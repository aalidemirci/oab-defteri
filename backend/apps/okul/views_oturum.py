"""Oturum uçları (tasarım §4.4.3, TK14; plan F1b-1 "Oturum") — aile iskeletinin kip uçlarının yerine.

* `GET  security/session/`  → oturum özeti (`OTURUM.ozet()`): `durum`, `hesap` {id,
  tanitici, rol, rol_etiketi} (kişi adı yok), `bosta_dk`, `bosta_kalan_sn`,
  `kilit_bekliyor`, `kurulum_tamam`. Ön yüz bunu kısa aralıkla yoklar ve
  `X-OD-Etkinlik` GÖNDERMEZ (yoklama oturumu canlı tutmaz). Kilitliyken ve güvenlik
  dosyası kayıpken de yanıt verir (`lock_middleware`); yanıtı vermeden önce tembel
  kilit uygulanmıştır.
* `GET  security/accounts/` → kilit ekranının hesap listesi (`hesaplar.lock_screen_accounts`):
  `[{id, tanitici, rol, rol_etiketi, secilebilir, askida_nedeni}]`; ad-soyad ASLA dönmez.
* `POST security/unlock/` `{hesap, parola[, yeni_parola]}` → seçilen hesabın
  parolasıyla oturumu açar. Ret kodları (`app_password.UnlockRefused`; kod kullanıcı
  metnine çıkmaz): 400 `parola_yanlis`, 403 `hesap_askida`, 409 `hesap_muhru_tutmadi`,
  409 `iki_depo_tutarsiz`, 409 `parola_yenilenmeli` (geçici ya da süresi dolmuş
  parola: istek `yeni_parola` ile yinelenir, oturum yeni parolayla açılır).
* `POST security/lock/` → Kilitle (her rolde, parolasız; `OTURUM.kilitle`). Uçuştaki
  istekleri bekler; uzun iş sürerken ertelenir (`sonuc: "ertelendi"`, özetteki
  `kilit_bekliyor`). Kilitle'nin kısayolu ve "kullanıcı değiştir" (TK14) ön yüzdedir.
* `GET  security/recover/` → kurtarma anahtarıyla açılabilecek hesaplar
  (`hesaplar.recovery_accounts`): `[{id, tanitici, rol_etiketi, sarmali_var}]`; kişi
  adı yok. Kurtarma anahtarıyla geri yüklemeden sonra kilit ekranı listesi boştur
  (sarmal yoktur, TK10); "kurtarma anahtarıyla aç + program yöneticisi parolası"
  ekranı hesabı buradan seçer (tasarım §4.4.4).
* `POST security/recover/` `{kurtarma_anahtari, hesap, yeni_parola}` → kurtarma
  anahtarıyla açılış; yalnız var olan bir program yöneticisi hesabının parolasını
  yeniler (tasarım §4.4.3). `hesap` kimlik ya da tanıtıcıdır.
* `POST security/change-password/` `{parola, yeni_parola}` → oturumdaki hesabın
  kendi parolası. Yalnız açık oturumda (kilitliyken kilit kapısı 423 verir) ve o
  hesabın parolasıyla; başka hesabın parolası geçmez.
* `GET|PUT security/idle-lock/` `{dakika}` → boşta kilit süresi (3-30, varsayılan 10;
  `SchoolConfig.idle_lock_minutes`, tasarım TK14, §13 D11). Ayarlar → Güvenlik okur
  ve yazar. Yalnız açık oturumda: kilit ekranının açık listesinde DEĞİLDİR
  (`lock_middleware.KILITLI_IZINLI`; kilitliyken 423). Yazmayı yalnız program
  yöneticisine bırakan rol kuralı (tasarım §4.4.2) 2. adımdadır.

Parolalar ve kurtarma anahtarı YALNIZ istek gövdesinde taşınır; hiçbir yanıtta,
günlükte ya da hata iletisinde yankılanmaz. Gövde anahtarları Türkçedir (oturum
sözleşmesi); ilk hesabın kurulumu ve kurtarma anahtarı belgesi uçları `views.py`'dedir.
Rol denetimi (`RolMiddleware`) 2. adımdadır; boşta kilit süresinin yazımı dışındaki
bu uçların hepsi her role açık olacaktır (§4.4.2 "Kendi parolasını değiştirme, Kilitle,
Çık").
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.views.decorators.debug import sensitive_variables
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul.models import IDLE_LOCK_MINUTES_MAX, IDLE_LOCK_MINUTES_MIN
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, hesaplar
from apps.okul.services import setup as setup_service


class SecurityRefusedResponse(APIException):
    """Kilit açma reddi (`app_password.UnlockRefused`): kod ve HTTP durumu servisten gelir.

    Kodlar `parola_yanlis` (400), `hesap_askida` (403), `hesap_muhru_tutmadi` ve
    `iki_depo_tutarsiz` (409), `parola_yenilenmeli` (409); ileti Türkçedir, kod
    kullanıcı metnine çıkmaz (plan F1b-1).
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_code = "parola_yanlis"
    default_detail = "Parola hatalı."

    def __init__(self, exc: app_password.UnlockRefused) -> None:
        super().__init__(detail=str(exc))
        self.status_code = exc.status_code
        self.default_code = exc.code


@contextmanager
def guvenlik_hatalari() -> Iterator[None]:
    """Kilit açma retlerini kodlu yanıta, öteki servis hatalarını 400'e çevirir."""
    try:
        yield
    except app_password.UnlockRefused as exc:
        raise SecurityRefusedResponse(exc) from exc
    except ValueError as exc:
        raise serializers.ValidationError(str(exc)) from exc


class KilitAcmaSerializer(serializers.Serializer[dict[str, Any]]):
    """Kilit açma: seçilen hesabın kimliği + parolası; parola yenilenmeliyse yeni parola."""

    hesap = serializers.CharField()
    parola = serializers.CharField(trim_whitespace=False)
    yeni_parola = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )


class KurtarmaSerializer(serializers.Serializer[dict[str, Any]]):
    """Kurtarma anahtarıyla açılış: program yöneticisi hesabı (kimlik ya da tanıtıcı) + yeni parolası."""

    kurtarma_anahtari = serializers.CharField(trim_whitespace=False)
    hesap = serializers.CharField()
    yeni_parola = serializers.CharField(trim_whitespace=False)


class ParolaDegistirmeSerializer(serializers.Serializer[dict[str, Any]]):
    """Kendi parolasını değiştirme: oturumdaki hesabın şimdiki ve yeni parolası."""

    parola = serializers.CharField(trim_whitespace=False)
    yeni_parola = serializers.CharField(trim_whitespace=False)


class BostaKilitSuresiSerializer(serializers.Serializer[dict[str, Any]]):
    """Boşta kilit süresi: dakika, 3-30 tam sayı (iletiler sözlüğe uyar; iç kod yok)."""

    dakika = serializers.IntegerField(
        min_value=IDLE_LOCK_MINUTES_MIN,
        max_value=IDLE_LOCK_MINUTES_MAX,
        error_messages={
            "required": "Boşta kilit süresini dakika olarak girin.",
            "null": "Boşta kilit süresini dakika olarak girin.",
            "invalid": "Boşta kilit süresi tam sayı (dakika) olmalıdır.",
            "max_string_length": "Boşta kilit süresi tam sayı (dakika) olmalıdır.",
            "min_value": setup_service.IDLE_LOCK_RANGE_MESSAGE,
            "max_value": setup_service.IDLE_LOCK_RANGE_MESSAGE,
        },
    )


class OturumOzetiView(APIView):
    """`GET /api/v1/security/session/` — oturum özeti (modül başlığı)."""

    def get(self, request: Request) -> Response:
        return Response(OTURUM.ozet())


class KilitEkraniHesaplariView(APIView):
    """`GET /api/v1/security/accounts/` — kilit ekranının hesap listesi (kişi adı yok)."""

    def get(self, request: Request) -> Response:
        return Response(hesaplar.lock_screen_accounts())


class SecurityUnlockView(APIView):
    """`POST /api/v1/security/unlock/` `{hesap, parola[, yeni_parola]}` — oturumu açar."""

    @sensitive_variables("req", "veri")
    def post(self, request: Request) -> Response:
        req = KilitAcmaSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            app_password.unlock(
                hesap_id=veri["hesap"],
                password=veri["parola"],
                new_password=veri["yeni_parola"] or None,
            )
        return Response(OTURUM.ozet())


class SecurityLockView(APIView):
    """`POST /api/v1/security/lock/` — Kilitle; uzun iş sürerken ertelenir (`sonuc`)."""

    def post(self, request: Request) -> Response:
        sonuc = OTURUM.kilitle(neden="elle")
        return Response({"sonuc": sonuc, **OTURUM.ozet()})


class SecurityRecoverView(APIView):
    """`/api/v1/security/recover/` — kurtarma listesi (GET) ve kurtarma anahtarıyla açılış (POST)."""

    def get(self, request: Request) -> Response:
        return Response(hesaplar.recovery_accounts())

    @sensitive_variables("req", "veri")
    def post(self, request: Request) -> Response:
        req = KurtarmaSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            app_password.unlock_with_recovery(
                recovery_key=veri["kurtarma_anahtari"],
                hesap_id=veri["hesap"],
                new_password=veri["yeni_parola"],
            )
        return Response(OTURUM.ozet())


class SecurityChangePasswordView(APIView):
    """`POST /api/v1/security/change-password/` `{parola, yeni_parola}` — oturumdaki hesabın parolası.

    Veri yeniden şifrelenmez, yalnız o hesabın sarmalı yenilenir; oturum ve DEK
    değişmez. Kilitliyken kilit kapısı keser (423); servis de açık oturum ister.
    """

    @sensitive_variables("req", "veri")
    def post(self, request: Request) -> Response:
        req = ParolaDegistirmeSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            app_password.change_password(
                hesap_id=OTURUM.hesap_id() or "",
                current_password=veri["parola"],
                new_password=veri["yeni_parola"],
            )
        return Response(OTURUM.ozet())


class BostaKilitSuresiView(APIView):
    """`GET|PUT /api/v1/security/idle-lock/` `{dakika}` — boşta kilit süresi (modül başlığı).

    GET oturumun uyguladığı süreyi verir (`setup.idle_lock_minutes`); PUT yazar ve
    yeni değeri döndürür. Yeni süre bir sonraki istekte geçerlidir (oturumun önbelleği
    kayıtla boşalır). Kişi yazmaz.
    """

    def get(self, request: Request) -> Response:
        return Response({"dakika": setup_service.idle_lock_minutes()})

    def put(self, request: Request) -> Response:
        req = BostaKilitSuresiSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        with guvenlik_hatalari():
            dakika = setup_service.set_idle_lock_minutes(dakika=req.validated_data["dakika"])
        return Response({"dakika": dakika})
