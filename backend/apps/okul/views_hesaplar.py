"""Kullanıcılar uçları (plan F1b-2 "Kullanıcılar uçları"; tasarım §4.4.2 Kullanıcılar satırı, §4.4.5).

Hepsi yalnız program yöneticisine açıktır: rol kapısı (`rol_izinleri.KURALLAR`, satır
`KULLANICILAR`) ve servisin yetki kapısı (`Eylem.HESAP_YONETIMI`) birlikte. Yalnız açık oturumda
(kilitliyken kilit kapısı 423 verir; kilit ekranının açık listesinde değildir).

* `GET  accounts/` → `{hesaplar: [satır]}`: BÜTÜN hesaplar, giriş yapamayanlar ve kapalılar dahil
  (`hesaplar.kullanici_listesi`). Satır kişisiz kodlar ve kullanıcı metinleri taşır: `{id,
  tanitici, rol, rol_etiketi (sıra no'suz), ad_soyad, durum, durum_etiketi, askida_nedeni,
  askida_nedeni_etiketi, kayit_tutuyor, oturumdaki, acilis, kapanis, son_giris, giris: {yapabilir,
  neden}, eylemler: {kapat, askidan_cikar, parola_sifirla: {yapilabilir, neden}}}`. Eylemleri
  sunucu hesaplar (servislerin kuralları ve iletileriyle), ön yüz yalnız eşler.
* `POST accounts/` `{rol, tanitici, ad_soyad, gecici_parola}` → hesap açma
  (`hesaplar.open_account`; `HESAP` satırı) → 201 `{hesap: satır, uyari, bilgi}`. `uyari` tanıtıcı
  ad-soyadı içeriyorsa sözlükteki uyarıdır (engel değil); `bilgi` program yöneticisi rolünde ikinci
  program yöneticisinin bilgisidir (`hesaplar.IKINCI_YONETICI_BILGISI`).
* `GET  accounts/options/` → `{roller: [{rol, rol_etiketi, acilabilir, neden, varsayilan_tanitici,
  bilgi}]}` (`hesaplar.kullanici_secenekleri`): açılamama nedeni hesap açmanınkiyle aynıdır;
  kaydı ya da izi (satır izi ya da iz boşluğu) tutmayan hesap için ayrı neden (orkestratör maddesi
  C-1).
* `GET  accounts/<id>/` → satır + `{acan, kapatan, parola_degisimi, sifirlama, son_girisler}`
  (`hesaplar.kullanici_ayrintisi`); hesap yoksa 404.
* `POST accounts/<id>/close/` (`HESAP`), `unsuspend/` (`HESAP`; dosyadaki hatalı deneme askısı
  `guvenlik.sarmal` satırıyla) ve `reset-password/` `{gecici_parola}` (`PAROLA` + iki aşamalı özetin
  `HESAP` satırı) → `{hesap: satır}`. Oturumdaki hesap kendi hesabını kapatamaz, kendi parolasını
  buradan sıfırlayamaz (plan F1b-2 "Kendi hesabı"; servis reddeder, satırın eylemi de söyler).
* `POST accounts/<id>/handover-slip/` → hesap teslim pusulası (E63; plan F1b-2 "E63 hesap teslim
  pusulası"): yalnız PDF, ek olarak indirilir (`Cache-Control: no-store`); dosya SAKLANMAZ, bellekten
  verilir; izi `BASIM` satırıdır (kod ve PDF'in sha256'sı; `hesaplar.teslim_pusulasi`), erişim
  günlüğüne girmez. Kendi hesabına, kapalı hesaba ve kaydı ya da izi tutmayan hesaba basılmaz
  (satırın `pusula` eylemi aynı nedenleri söyler). İz satırı yazacağı için yöntem POST'tur.

GEÇİCİ PAROLA (plan F1b-2 "Geçici parola"): istemci önerir; sunucu yalnız politikayı denetler
(`hesap_kurallari.validate_password`) ve parolayı sarmala koyar. Parola HİÇBİR yanıtta, günlükte,
iz satırında ya da iletide yoktur (`sensitive_variables`; doğrulama iletisi parolayı yankılamaz).

RET KODLARI: servis reddi 400 `validation_error` (Türkçe ileti); kaydı ya da izi tutmayan hesap 409
`hesap_muhru_tutmadi` (ileti mühür ya da iz boşluğu iletisi; satır izinde ve izdeki boşlukta
`BUTUNLUK` satırı kalır, yalnız mührü tutmayan hesapta satır yazılmaz — o hesap
`security/integrity/audit/`'in `muhru_tutmayan` listesinde canlı görünür; tasarım §4.4.5 olayı
denetim izine kilit açılışında yazdırır); rol 403 `rol_yetkisiz`; denetim izi yazılamazsa 409
`iz_yazilamadi`.

İŞLEM SINIRI (orkestratör maddesi C-2): uçlar istek boyu işlem (`atomic`) AÇMAZ ve ayarlarda
`ATOMIC_REQUESTS` yoktur. Servisler `BUTUNLUK` satırını ve yanlış alarm ayıklamasını KENDİ
işlemlerinde yürütür; istek boyu bir işlem reddin `BUTUNLUK` satırını yanıtla birlikte geri sarardı
(`test_kullanicilar_uclari.py` her yazma ucunda sınar).
"""

from __future__ import annotations

from io import BytesIO
from typing import Any
from uuid import UUID

from django.http import FileResponse
from django.views.decorators.debug import sensitive_variables
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul.models import AccountRole
from apps.okul.services import hesap_kurallari, hesap_teslim_pusulasi, hesaplar
from apps.okul.views_oturum import _yazar_hesabi, guvenlik_hatalari

#: Hesabı bulunamayan ayrıntı ve eylem yanıtı (404; sözlük §1 "Kullanıcılar").
_BULUNAMADI = "Hesap bulunamadı."


class HesapAcmaSerializer(serializers.Serializer[dict[str, Any]]):
    """Hesap açma: rol, tanıtıcı, ad-soyad ve geçici parola (parola kırpılmaz)."""

    rol = serializers.CharField()
    tanitici = serializers.CharField(trim_whitespace=False)
    ad_soyad = serializers.CharField(trim_whitespace=False)
    gecici_parola = serializers.CharField(trim_whitespace=False, write_only=True)


class ParolaSifirlamaSerializer(serializers.Serializer[dict[str, Any]]):
    """Parola sıfırlama: geçici parola (parola kırpılmaz)."""

    gecici_parola = serializers.CharField(trim_whitespace=False, write_only=True)


def _satir(hesap_id: object) -> dict[str, Any]:
    satir = hesaplar.kullanici_satiri(hesap_id)
    if satir is None:
        raise NotFound(_BULUNAMADI)
    return satir


class KullanicilarView(APIView):
    """`GET|POST /api/v1/accounts/` — liste ve hesap açma (modül başlığı)."""

    def get(self, request: Request) -> Response:
        with guvenlik_hatalari():
            liste = hesaplar.kullanici_listesi()
        return Response({"hesaplar": liste})

    @sensitive_variables("req", "veri")
    def post(self, request: Request) -> Response:
        req = HesapAcmaSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            hesap = hesaplar.open_account(
                by_hesap_id=_yazar_hesabi() or "",
                role=veri["rol"],
                tanitici=veri["tanitici"],
                display_name=veri["ad_soyad"],
                temp_password=veri["gecici_parola"],
            )
            satir = _satir(hesap.id)
        return Response(
            {
                "hesap": satir,
                "uyari": hesap_kurallari.login_name_warning(hesap.login_name, veri["ad_soyad"]),
                "bilgi": (
                    hesaplar.IKINCI_YONETICI_BILGISI if hesap.role == AccountRole.YONETICI else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class KullaniciSecenekleriView(APIView):
    """`GET /api/v1/accounts/options/` — "Yeni hesap" penceresinin rol seçenekleri."""

    def get(self, request: Request) -> Response:
        with guvenlik_hatalari():
            return Response(hesaplar.kullanici_secenekleri())


class KullaniciAyrintisiView(APIView):
    """`GET /api/v1/accounts/<id>/` — hesabın ayrıntısı ve son girişleri."""

    def get(self, request: Request, hesap_id: UUID) -> Response:
        with guvenlik_hatalari():
            ayrinti = hesaplar.kullanici_ayrintisi(hesap_id)
        if ayrinti is None:
            raise NotFound(_BULUNAMADI)
        return Response(ayrinti)


class KullaniciKapatView(APIView):
    """`POST /api/v1/accounts/<id>/close/` — hesabı kapatır (sarmal güvenlik dosyasından silinir)."""

    def post(self, request: Request, hesap_id: UUID) -> Response:
        with guvenlik_hatalari():
            hesaplar.close_account(by_hesap_id=_yazar_hesabi() or "", hesap_id=hesap_id)
            return Response({"hesap": _satir(hesap_id)})


class KullaniciAskidanCikarView(APIView):
    """`POST /api/v1/accounts/<id>/unsuspend/` — askıdan çıkarır (iki kaynak birlikte)."""

    def post(self, request: Request, hesap_id: UUID) -> Response:
        with guvenlik_hatalari():
            hesaplar.unsuspend(by_hesap_id=_yazar_hesabi() or "", hesap_id=hesap_id)
            return Response({"hesap": _satir(hesap_id)})


class KullaniciParolaSifirlaView(APIView):
    """`POST /api/v1/accounts/<id>/reset-password/` `{gecici_parola}` — geçici parolayla sıfırlar."""

    @sensitive_variables("req", "veri")
    def post(self, request: Request, hesap_id: UUID) -> Response:
        req = ParolaSifirlamaSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            hesaplar.reset_password(
                by_hesap_id=_yazar_hesabi() or "",
                hesap_id=hesap_id,
                temp_password=veri["gecici_parola"],
            )
            return Response({"hesap": _satir(hesap_id)})


class KullaniciTeslimPusulasiView(APIView):
    """`POST /api/v1/accounts/<id>/handover-slip/` — hesap teslim pusulası (E63; modül başlığı).

    Gövde yoktur. PDF bellekten, ek olarak verilir; önbelleğe alınmaz ve saklanmaz.
    """

    def post(self, request: Request, hesap_id: UUID) -> FileResponse:
        with guvenlik_hatalari():
            pdf = hesaplar.teslim_pusulasi(by_hesap_id=_yazar_hesabi() or "", hesap_id=hesap_id)
        yanit = FileResponse(
            BytesIO(pdf),
            as_attachment=True,
            filename=hesap_teslim_pusulasi.dosya_adi(),
            content_type="application/pdf",
        )
        yanit["Cache-Control"] = "no-store"
        return yanit
