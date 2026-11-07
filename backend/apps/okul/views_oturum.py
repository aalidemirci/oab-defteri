"""Oturum uçları (tasarım §4.4.3, TK14; plan F1b-1 "Oturum") — aile iskeletinin kip uçlarının yerine.

* `GET  security/session/`  → oturum özeti (`OTURUM.ozet()`): `durum`, `hesap` {id,
  tanitici, rol, rol_etiketi, yetenekler} (kişi adı yok; `yetenekler` rolün yetenek adları,
  `rol_izinleri.yetenekler` — ön yüz süzmesinin tek kaynağı), `bosta_dk`, `bosta_kalan_sn`,
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
  (`lock_middleware.KILITLI_IZINLI`; kilitliyken 423). Her rol okur; yazmayı yalnız program
  yöneticisi yapar (tasarım §4.4.2 Ayarlar satırı; rol kapısı ve servisin yetki kapısı).

BÜTÜNLÜK KARTLARI üç uçtadır (tasarım §4.4.2 "kısmi yetki ayrı uçla verilir"; plan F1b-2
"Bütünlük ucu bölünür"; `iz_dogrulama`). Her uç kendi `okunamayan` listesini döndürür (tek
kartın hatası öteki kartları düşürmez; ön yüz "Bütünlük Durumu Okunamadı" der):

* `GET  security/integrity/` → oturumdaki hesabın KENDİ kartları, her rol
  (`iz_dogrulama.kendi_kartlari`): `son_girisler` (yalnız bu hesabın), `parola_yenilenme`
  (sıfırlama ya da kurtarma bildirimi ve o tarihten sonraki girişler) ve `kagit_capasi`
  (`kayit_no`, `zincir`: "Kayıt no: N · Zincir: XXXX-XXXX").
* `GET  security/integrity/audit/` → denetim kartları, program yöneticisi ve Denetleme Kurulu
  (`iz_dogrulama.denetim_kartlari`; tasarım §4.6.3, §4.6.1 kural 1, §4.4.4): `butunluk`
  (oturumdaki hesabın bir önceki girişinden beri yazılmış `BUTUNLUK` satırları: kilit açılışı
  doğrulamasının bulgu kodları ve düzeyi ya da girişte tutmayan hesap mührü), `geri_yukleme`
  (son `GERI_YUKLEME` satırı: geri yüklemenin anı nottan, satırın anı ilk girişten; yedeği açan
  yol hesap ya da kurtarma anahtarı no'su; uygulama içinden yapıldıysa başlatan oturumun hesabı;
  Denetleme Kurulu "gördüm" diyene dek), `muhru_tutmayan` (kaydı program dışından
  değiştirilmiş görünen hesaplar, canlı) ve `eksik_ekler` (satırı olup dosyası olmayan ekler,
  canlı; özgün ad yalnız burada ve kaydın kendisinde görünür; `dosya_deposu.eksik_ekler`).
* `GET  security/integrity/two-store/` → iki depo kartı, yalnız program yöneticisi
  (`iz_dogrulama.iki_depo_karti`; §4.6.1 kural 4): `iki_depo` {`fark_var`,
  `sarmalsiz_hesaplar`, `silinebilir_sarmallar`} (canlı fark; fark hesaplanamazsa `null`).
* `POST security/integrity/orphan-wraps/` `{hesaplar: [kimlik]}` → program yöneticisinin
  onayıyla sahipsiz (satırı olmayan ya da `KAPALI`) hesap sarmallarının silinmesi (tasarım
  §4.6.1 kural 4; `hesaplar.remove_orphan_wraps`, `HESAP` satırı); yalnız program yöneticisi
  (rol kapısı ve servisin yetki kapısı). Yanıt `{silinen, …iki depo kartı}`'dır.
* `POST security/integrity/restore-seen/` `{seq}` → geri yükleme kartının "Gördüm"ü (plan
  F1b-2 "Gördüm."; tasarım §4.4.4, §4.4.2 M8 ⁵): yalnız Denetleme Kurulu (rol kapısı ve servisin
  yetki kapısı `Eylem.GERI_YUKLEME_GORDUM`; `hesaplar.acknowledge_restore`). `seq` kartın
  gösterdiği (doğrulanan son) `GERI_YUKLEME` satırıdır; `ISARET` satırı yazılır, kart herkes için
  kalkar (bir üye yeter; kimin gördüğü izde kalır). Aynı geri yüklemeye ikinci "Gördüm" satır
  yazmaz (200); eski ya da olmayan `seq` 409 `geri_yukleme_guncel_degil`; biçimsiz `seq` 400.
  Yanıt güncel denetim kartlarıdır.

Kişi adı ve bulgu metni DÖNMEZ: kodları ön yüz sözlükteki metne çevirir. Kartlardaki hesaplar
kişisizdir: `{id, tanitici, rol_etiketi}` (iki depo ve mührü tutmayan satırlarında ek olarak
`kapali`). Kartlar yalnız iz anahtarıyla mühürlü ve doğrulanan satırları okur
(`denetim_izi.acik_satir_dogrulayici`). Yalnız açık oturumda (kilitliyken 423).

* `GET|POST security/integrity/reset-notice/` → oturumdaki hesabın parola yenilenme
  bildirimi (tasarım §4.4.3, §4.3 tehdit 12): `{parola_yenilenme: {tur, zaman, girisler} |
  null, okunamayan: [ad]}` (`iz_dogrulama.bildirim_yaniti`; girişler YALNIZ bu hesabın;
  bildirim okunamazsa — program dışından bozulmuş sıfırlama anı — `parola_yenilenme` null,
  `okunamayan` `["parola_yenilenme"]`dir, uç 500 vermez). POST sahibinin "Gördüm"üdür: bayrak
  izli bir yazımla kalkar (`hesaplar.acknowledge_reset_notice`,
  `GUNCELLE` satırı); bildirim beklemiyorsa bir şey yazmaz. Başka hesabın bildirimi bu uçtan
  ne okunur ne kapatılır. Ön yüz bildirimi kilit ekranından açılıştan sonra pencerede
  gösterir. Yalnız açık oturumda (kilitliyken 423).

Parolalar ve kurtarma anahtarı YALNIZ istek gövdesinde taşınır; hiçbir yanıtta,
günlükte ya da hata iletisinde yankılanmaz. Gövde anahtarları Türkçedir (oturum
sözleşmesi); ilk hesabın kurulumu ve kurtarma anahtarı belgesi uçları `views.py`'dedir.

ROL TABLOSU (`rol_izinleri.KURALLAR`; rol kapısı `RolMiddleware`): oturum özeti, kilit
ekranının hesap listesi, kilit açma, kurtarma, Kilitle, kendi parolası, boşta süreyi okuma,
kendi kartları ve parola yenilenme bildirimi her role açıktır (§4.4.2 "Kendi parolasını
değiştirme, Kilitle, Çık"; kilitliyken açık olan her uç açık oturumda her role açıktır).
Boşta süre yazımı, iki depo kartı ve sahipsiz parola kayıtlarının silinmesi yalnız program
yöneticisine; denetim kartları program yöneticisi ve Denetleme Kuruluna, geri yükleme kartının
"Gördüm"ü yalnız Denetleme Kuruluna açıktır.
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

from apps.okul import iz_dogrulama
from apps.okul.models import IDLE_LOCK_MINUTES_MAX, IDLE_LOCK_MINUTES_MIN
from apps.okul.oturum import OTURUM, yazar
from apps.okul.services import app_password, hesaplar, satir_izi
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
    """Kilit açma retlerini kodlu yanıta, öteki servis hatalarını 400'e çevirir.

    Hesap servisinin güvenlik dosyası adımı yarıda kalırsa (`hesaplar.GuvenlikDosyasiYazilamadi`, bir
    `OSError`: hesap açma, kapama, parola sıfırlama, askıdan çıkarma ve sahipsiz parola kayıtlarının
    silinmesi) servis retlerinin kalıbıyla 400 `validation_error` olur, ileti servisin Türkçe
    iletisidir ve neyin yapılıp neyin yapılmadığını söyler (orkestratör maddeleri F-7 ve (d0)-1;
    eskiden 500). Öteki `OSError`'lar burada yakalanmaz.
    """
    try:
        yield
    except app_password.UnlockRefused as exc:
        raise SecurityRefusedResponse(exc) from exc
    except ValueError as exc:
        raise serializers.ValidationError(str(exc)) from exc
    except hesaplar.GuvenlikDosyasiYazilamadi as exc:
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
                hesap_id=_yazar_hesabi() or "",
                current_password=veri["parola"],
                new_password=veri["yeni_parola"],
            )
        return Response(OTURUM.ozet())


class SahipsizSarmalSerializer(serializers.Serializer[dict[str, Any]]):
    """Sahipsiz sarmalların onayla silinmesi: silinecek hesap kimlikleri (listeden)."""

    hesaplar = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)


def _yazar_hesabi() -> str | None:
    """İsteğin yazarı olan hesap (istek başındaki görüntü; `SISTEM` ya da bağlamsız: yok).

    Oturumdaki hesabı isteyen BÜTÜN uçlar buradan okur (kendi parolası, kendi kartları, kendi
    parola bildirimi, sahipsiz parola kayıtlarının silinmesi; orkestratör maddesi C-5): yetki
    kapısının ilkesiyle aynı (`rol_izinleri` modül başlığı) — istek ortasındaki kilit ya da hesap
    değişimi kararı değiştirmez, `OTURUM.hesap_id()` o anın oturumunu verirdi.
    """
    kim = yazar()
    return None if kim is None or kim.sistem_mi else kim.hesap_id


class ButunlukDurumuView(APIView):
    """`GET /api/v1/security/integrity/` — oturumdaki hesabın kendi kartları (modül başlığı)."""

    def get(self, request: Request) -> Response:
        return Response(iz_dogrulama.kendi_kartlari(_yazar_hesabi()))


class DenetimKartlariView(APIView):
    """`GET /api/v1/security/integrity/audit/` — denetim kartları (modül başlığı)."""

    def get(self, request: Request) -> Response:
        return Response(iz_dogrulama.denetim_kartlari(_yazar_hesabi()))


class IkiDepoKartiView(APIView):
    """`GET /api/v1/security/integrity/two-store/` — iki depo kartı (modül başlığı)."""

    def get(self, request: Request) -> Response:
        return Response(iz_dogrulama.iki_depo_karti())


class SahipsizSarmalView(APIView):
    """`POST /api/v1/security/integrity/orphan-wraps/` — sahipsiz sarmalları onayla siler."""

    def post(self, request: Request) -> Response:
        req = SahipsizSarmalSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        with guvenlik_hatalari():
            silinen = hesaplar.remove_orphan_wraps(
                by_hesap_id=_yazar_hesabi() or "",
                hesap_idler=[str(kimlik) for kimlik in req.validated_data["hesaplar"]],
            )
        return Response({"silinen": silinen, **iz_dogrulama.iki_depo_karti()})


#: "Gördüm"ün gövdesindeki sıranın iletileri (sözlük §1 "Geri yükleme kartının “Gördüm”ü (F1b)").
GORDUM_SIRASI_EKSIK = "Geri yükleme kaydı belirtilmedi."
GORDUM_SIRASI_GECERSIZ = "Geri yükleme kaydının numarası geçersiz."


class GeriYuklemeGordumSerializer(serializers.Serializer[dict[str, Any]]):
    """ "Gördüm": kartın gösterdiği geri yüklemenin denetim izindeki sırası (`seq`)."""

    seq = serializers.IntegerField(
        min_value=1,
        max_value=satir_izi.EN_BUYUK_SIRA,
        error_messages={
            "required": GORDUM_SIRASI_EKSIK,
            "null": GORDUM_SIRASI_EKSIK,
            "invalid": GORDUM_SIRASI_GECERSIZ,
            "max_string_length": GORDUM_SIRASI_GECERSIZ,
            "min_value": GORDUM_SIRASI_GECERSIZ,
            "max_value": GORDUM_SIRASI_GECERSIZ,
        },
    )


class GeriYuklemeKartiGuncelDegilResponse(APIException):
    """`hesaplar.RestoreCardStale`: 409 `geri_yukleme_guncel_degil` (eski ya da olmayan `seq`)."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "geri_yukleme_guncel_degil"
    default_detail = hesaplar.RESTORE_CARD_STALE_MESSAGE


class GeriYuklemeGordumView(APIView):
    """`POST /api/v1/security/integrity/restore-seen/` `{seq}` — geri yükleme kartının "Gördüm"ü.

    Yalnız Denetleme Kurulu (modül başlığı). Yanıt güncel denetim kartlarıdır
    (`iz_dogrulama.denetim_kartlari`; görülen kart `geri_yukleme: null`).
    """

    def post(self, request: Request) -> Response:
        req = GeriYuklemeGordumSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        try:
            with guvenlik_hatalari():
                hesaplar.acknowledge_restore(
                    by_hesap_id=_yazar_hesabi() or "", seq=req.validated_data["seq"]
                )
        except hesaplar.RestoreCardStale as exc:
            raise GeriYuklemeKartiGuncelDegilResponse from exc
        return Response(iz_dogrulama.denetim_kartlari(_yazar_hesabi()))


class ParolaBildirimiView(APIView):
    """`GET|POST /api/v1/security/integrity/reset-notice/` — parola yenilenme bildirimi.

    Yalnız oturumdaki hesabın bildirimi (modül başlığı). POST "Gördüm"dür; yanıt güncel
    bildirimdir (kapandıysa `null`). Bildirim okunamazsa (program dışından bozulmuş sıfırlama
    anı) uç 500 vermez: `parola_yenilenme` null, adı `okunamayan`'dadır
    (`iz_dogrulama.bildirim_yaniti`).
    """

    def get(self, request: Request) -> Response:
        return Response(iz_dogrulama.bildirim_yaniti(_yazar_hesabi()))

    def post(self, request: Request) -> Response:
        with guvenlik_hatalari():
            hesaplar.acknowledge_reset_notice(hesap_id=_yazar_hesabi() or "")
        return Response(iz_dogrulama.bildirim_yaniti(_yazar_hesabi()))


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
