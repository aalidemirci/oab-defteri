"""Genel kurul evrakı: E04-E14 ve E64 — üretim, veli adlı çıktı ve basım (plan F2 §4, 8. adım).

`gorev_evraki`'nin kalıbıdır (`KODLAR`, `BELGE_ADLARI`, `URETEN_ROLLER`, kurucular, `uret`, `bas`).
Bu adımda (8.) yalnız İSKELET vardır: belgelerin içerik kurucuları 9. adımda (E05-E08, E64) ve 10.
adımda (E09-E14, E04) `KURUCULAR`'a ve `ADLI_KURUCULAR`'a girer. Kurucusu olmayan kod üretilmez
(`KOD_GECERSIZ`).

KONU VE DÖNEM (plan F2 §4.2). Genel kurul belgelerinin (E05-E13, E64) konusu genel kuruldur
(`GeneralAssembly`); dönemi `assembly.term`'dür, yeni okulun ilk genel kurulunda hazırlık dönemi
(`opens_term`; `genel_kurul.kural_donemi`). Bu belgeler hazırlık dönemine de yazılır
(`hazirlik_yazimi=True`; dönem kilidi `donem_kilidi.yazma_denetimi`). E04'ün konusu okul kartıdır
(dönemsiz), E14'ünkü birlik dönemidir; E14 genel kurul belgesi değildir, hazırlıktaki döneme
yazılmaz (`DonemYazilamaz`).

KİP VE TOPLANTI (plan F2 §7 U14, U34). E07 ve E08 iki kiplidir: kişisiz kip (`KISISIZ`: davet ve
sınıf başına adet; boş satırlı cetvel) `uret` ile üretilir ve saklanır; adlı kip (`ADLI`: teslim
çizelgesi; veli adlı cetvel) yalnız `adli_uret_ve_ver` ile, saklanmadan verilir. E05, E06 ve E64
toplantı başınadır (`BIRINCI`, `IKINCI`). Öteki belgeler kip ve toplantı almaz. Aynı konunun aynı
kodlu belgeleri kip ve toplantı başına ayrı geçerli satırdır (`evrak_servisi.kaydet`).

BİÇİMLER (tasarım §9.5; plan F2 §7 U18). Word ve PDF dosya deposunda saklanır (`dosya_ekle`); Excel
(E08, E14) ve web sayfası (E06) saklanmaz, kayıtlı içerikten (`content_json`) istendikçe çizilir.

ÜRETİM (`uret`). Sıra `gorev_evraki.uret`'inki: yazma kapısı → ilk hesap → rol (genel kurul
belgelerinde `Eylem.GENEL_KURUL_YAZMA` ve tasarım §9.6'nın "Üreten"i, `URETEN_ROLLER`; E05'in
çağırana göre kolları 9. adımda) → içerik → çizim (işlem dışında) → TEK işlemde evrak kaydı ve
saklanan dosyalar.

VELİ ADLI ÇIKTI (`adli_uret_ve_ver`; plan F2 §7 U15, R9; tasarım §5.2.8, §4.6.4). Hesap teslim
pusulasının (E63) kalıbıyla tek istekte üretilir ve verilir. Kapı `Eylem.KISISEL_VERI_CIKTISI`'dır
(dipnot ¹⁰: yalnız program yöneticisi). Belge bellekte çizilir; sonra AYNI işlemde (1) evrak kaydı
`kaydet(kisi_listesi=True, satir_sayisi=N, kip=ADLI)` — içerik JSON'u saklanmaz, yalnız özeti, satır
sayısı ve tarih kalır; kapanmış döneme yazılmaz (O2), (2) `BASIM` izi (kod ve dosyanın sha256'sı) ve
(3) erişim günlüğünün `VELI_LISTESI_CIKTISI` satırı (dosyanın sha256'sı ve satır sayısı; ad
yok) yazılır. Biri yazılamazsa dosya verilmez. `dosya_ekle` çağrılmaz: dosya hiçbir yerde saklanmaz;
arşiv paketine girmez (F4). Yanıtın `Cache-Control: no-store`'u ucundur (11. adım; `indirme_yaniti`
hazırdır). Günlüğe, hataya ve ize kişi adı yazılmaz: kayıt yalnız kodu ve satır sayısını söyler.

BASIM (`bas`). Kaydedilmiş belgeyi okur roller basar (tasarım §9.6; `OKUMA_SATIRLARI`): genel kurul
belgelerini M3'ü, E14'ü M9'u, E04'ü M1'i okuyan roller. Saklanan biçim dosya deposundan, saklanmayan
biçim kayıtlı içerikten çizilir (`evrak_servisi.yeniden_ciz`); sonra AYNI istekte `BASIM` satırı
yazılır, yazılamazsa dosya verilmez. Veli adlı belge yeniden basılmaz (dosyası ve içeriği yoktur:
404). `gorev_evraki.bas`'ın F1c davranışı değişmez.

Bütün sabit metinler sözlüğe girer (sözlük §1 "Genel kurul evrakı (F2)").
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Final

from django.db import models, transaction
from django.http import FileResponse, Http404
from django.utils import timezone

from apps.oab.kurallar import yazma_kapisi
from apps.oab.models import (
    AssemblyMeeting,
    DocumentFormat,
    DocumentStatus,
    DocumentVariant,
    GeneralAssembly,
    GeneratedDocument,
    OabTerm,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import genel_kurul
from apps.okul import denetim_izi, erisim_gunlugu, rol_izinleri
from apps.okul.models import AccessKind, AccountRole, SchoolConfig
from apps.okul.oturum import yazar
from apps.okul.services import app_password, dosya_deposu
from shared import evrak
from shared.exceptions import RolYetkisiz

logger = logging.getLogger(__name__)

E04: Final = "E04"
E05: Final = "E05"
E06: Final = "E06"
E07: Final = "E07"
E08: Final = "E08"
E09: Final = "E09"
E10: Final = "E10"
E11: Final = "E11"
E12: Final = "E12"
E13: Final = "E13"
E14: Final = "E14"
E64: Final = "E64"
KODLAR: Final = (E04, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E64)
#: Konusu genel kurul olan belgeler (modül başlığı "Konu ve dönem").
GENEL_KURUL_KODLARI: Final = frozenset({E05, E06, E07, E08, E09, E10, E11, E12, E13, E64})
#: İki kipli belgeler (U14) ve toplantı başına belgeler (U34).
KIPLI_KODLAR: Final = frozenset({E07, E08})
TOPLANTILI_KODLAR: Final = frozenset({E05, E06, E64})
#: Veli adlı kipin belgeleri (R9).
ADLI_KODLAR: Final = (E07, E08)

#: Belge adları (tasarım §9.5 kataloğu; kısaltmalar açık yazılır, sözlük §3 "Kısaltma").
BELGE_ADLARI: Final[dict[str, str]] = {
    E04: "Kişisel veri aydınlatma metni",
    E05: "Genel kurul toplantı çağrısı ve gündemi",
    E06: "Genel kurul duyurusu",
    E07: "Üyelere elden yazılı davet ve sınıf teslim çizelgesi",
    E08: "Genel kurul katılım cetveli",
    E09: "Yönetim kurulu ve Denetleme Kurulu (veli koltuğu) aday listeleri",
    E10: "Genel kurul toplantı tutanağı",
    E11: "İbra edilmeyen muhasebe evrakının teslim tutanağı",
    E12: "İbra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı",
    E13: "Genel kurul sonuç bildirimi",
    E14: "Yıllık iş takvimi",
    E64: "Genel kurul yeter sayı tespit tutanağı",
}
#: Kaydedilen dosyanın adının belge kısmı (sözlük §3 "Kaydedilen dosya adı"; ad + kapsam + tarih).
DOSYA_ADI_KOKLERI: Final[dict[str, str]] = {
    E04: "Kişisel-Veri-Aydınlatma-Metni",
    E05: "Genel-Kurul-Çağrısı-ve-Gündemi",
    E06: "Genel-Kurul-Duyurusu",
    E07: "Genel-Kurul-Daveti",
    E08: "Genel-Kurul-Katılım-Cetveli",
    E09: "Genel-Kurul-Aday-Listeleri",
    E10: "Genel-Kurul-Toplantı-Tutanağı",
    E11: "İbra-Edilmeyen-Evrak-Teslim-Tutanağı",
    E12: "İbra-Edilmediğine-Dair-Resmî-Yazı",
    E13: "Genel-Kurul-Sonuç-Bildirimi",
    E14: "Yıllık-İş-Takvimi",
    E64: "Genel-Kurul-Yeter-Sayı-Tespit-Tutanağı",
}
#: Veli adlı kipin dosya adı kökleri (kişisiz kipten ayırt edilsin).
ADLI_DOSYA_ADI_KOKLERI: Final[dict[str, str]] = {
    E07: "Genel-Kurul-Daveti-Sınıf-Teslim-Çizelgesi",
    E08: "Genel-Kurul-Katılım-Cetveli-Veli-Adlı",
}
#: Toplantının dosya adındaki kapsamı.
TOPLANTI_KAPSAMLARI: Final[dict[str, str]] = {
    AssemblyMeeting.BIRINCI: "Birinci-Toplantı",
    AssemblyMeeting.IKINCI: "İkinci-Toplantı",
}

_DOCX_PDF: Final = (DocumentFormat.PDF, DocumentFormat.DOCX)
#: Belgelerin biçimleri (tasarım §9.5 "Biçim").
BICIMLER: Final[dict[str, tuple[str, ...]]] = {
    E04: _DOCX_PDF,
    E05: _DOCX_PDF,
    E06: (DocumentFormat.PDF, DocumentFormat.HTML),
    E07: _DOCX_PDF,
    E08: (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX),
    E09: _DOCX_PDF,
    E10: _DOCX_PDF,
    E11: _DOCX_PDF,
    E12: _DOCX_PDF,
    E13: _DOCX_PDF,
    E14: (DocumentFormat.PDF, DocumentFormat.XLSX),
    E64: _DOCX_PDF,
}
#: Veli adlı kipin biçimleri (tasarım §9.5; plan F2 §4.1: adlı E08 docx+pdf ve xlsx).
ADLI_BICIMLER: Final[dict[str, tuple[str, ...]]] = {
    E07: _DOCX_PDF,
    E08: (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX),
}
#: Dosya deposunda saklanan biçimler; ötekiler kayıtlı içerikten çizilir (U18).
SAKLANAN_BICIMLER: Final = frozenset(_DOCX_PDF)
UZANTILAR: Final[dict[str, str]] = {
    DocumentFormat.PDF: "pdf",
    DocumentFormat.DOCX: "docx",
    DocumentFormat.XLSX: "xlsx",
    DocumentFormat.HTML: "html",
}
#: Verilen dosyanın türü (saklanan biçimlerde dosya deposunun türüyle aynı).
MIME_TURLERI: Final[dict[str, str]] = {
    **evrak_servisi.BICIM_TURLERI,
    DocumentFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    DocumentFormat.HTML: "text/html; charset=utf-8",
}

_YONETICI: Final = AccountRole.YONETICI.value
_SEKRETER: Final = AccountRole.SEKRETER.value
#: Üreten roller (tasarım §9.6 "Üreten"; plan F2 §4.1). E05'in çağırana göre kolları (başkan, müdür,
#: Denetleme Kurulu) 9. adımda; E07 ve E08'in adlı kipi `KISISEL_VERI_CIKTISI` ile yalnız program
#: yöneticisinindir (U14).
URETEN_ROLLER: Final[dict[str, frozenset[str]]] = {
    E04: frozenset({_YONETICI}),
    **{
        kod: frozenset({_YONETICI, _SEKRETER})
        for kod in (E05, E06, E07, E08, E09, E10, E11, E13, E64)
    },
    E12: frozenset({_YONETICI}),
    E14: frozenset({_YONETICI}),
}
#: Basımın okuma satırı (tasarım §4.4.2 "Okuma"; plan F2 §6.1): genel kurul M3, yıllık iş takvimi M9
#: (Genel Bakış), aydınlatma metni M1 (okul kartı; her rol okur).
OKUMA_SATIRLARI: Final[dict[str, rol_izinleri.Satir]] = {
    E04: rol_izinleri.Satir.M1,
    **{kod: rol_izinleri.Satir.M3 for kod in GENEL_KURUL_KODLARI},
    E14: rol_izinleri.Satir.M9,
}

KOD_GECERSIZ: Final = "Bu evrak bu yoldan üretilmez."
KONU_GECERSIZ: Final = "Bu evrak bu kayıt için üretilmez."
KIP_GECERSIZ: Final = "Bu evrakın kipi geçersiz."
TOPLANTI_GECERSIZ: Final = "Bu evrakın toplantısı geçersiz."
BICIM_GECERSIZ: Final = "Bu evrak bu biçimde verilmez."


# ---------------------------------------------------------------------------
# Kurucular (9. ve 10. adımlarda dolar)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Secim:
    """Üretimin kipi ve toplantısı (modül başlığı "Kip ve toplantı")."""

    kip: str = ""
    toplanti: str = ""


@dataclass(frozen=True)
class AdliIcerik:
    """Veli adlı belgenin içeriği: model, satır sayısı (veli satırı) ve basım uyarıları."""

    belge: evrak.Belge
    satir_sayisi: int
    uyarilar: tuple[str, ...] = ()


#: Kişisiz kurucu: konu ve seçim → (içerik modeli, basım uyarıları).
Kurucu = Callable[[models.Model, Secim], tuple[evrak.Belge, tuple[str, ...]]]
#: Veli adlı kurucu: genel kurul ve toplantı → içerik.
AdliKurucu = Callable[[GeneralAssembly, str], AdliIcerik]

#: Kodun kişisiz içerik kurucusu (E05-E08, E64 9. adımda; E04, E09-E14 10. adımda).
KURUCULAR: dict[str, Kurucu] = {}
#: Veli adlı kipin içerik kurucusu (E07 ve E08; 9. adımda).
ADLI_KURUCULAR: dict[str, AdliKurucu] = {}


# ---------------------------------------------------------------------------
# Ortak yardımcılar
# ---------------------------------------------------------------------------
def _konu_turu(kod: str) -> type[models.Model]:
    if kod in GENEL_KURUL_KODLARI:
        return GeneralAssembly
    if kod == E14:
        return OabTerm
    return SchoolConfig


def _konu_ve_donem(kod: str, konu: models.Model) -> tuple[models.Model, OabTerm | None]:
    """Konunun güncel kaydı ve evrakın dönemi (modül başlığı "Konu ve dönem")."""
    tur = _konu_turu(kod)
    if not isinstance(konu, tur) or konu.pk is None:
        raise ValueError(KONU_GECERSIZ)
    if tur is GeneralAssembly:
        kurul = GeneralAssembly.objects.select_related(
            "term__rule_package", "opens_term__rule_package"
        ).get(pk=konu.pk)
        return kurul, genel_kurul.kural_donemi(kurul)
    if tur is OabTerm:
        donem = OabTerm.objects.select_related("rule_package").get(pk=konu.pk)
        return donem, donem
    return SchoolConfig.load(), None


def _secim_denetimi(kod: str, secim: Secim, *, adli: bool = False) -> None:
    """Kip ve toplantı koda uymalı (modül başlığı "Kip ve toplantı")."""
    if kod in KIPLI_KODLAR:
        beklenen = DocumentVariant.ADLI if adli else DocumentVariant.KISISIZ
        if secim.kip != beklenen:
            raise ValueError(KIP_GECERSIZ)
    elif secim.kip:
        raise ValueError(KIP_GECERSIZ)
    if kod in TOPLANTILI_KODLAR:
        if secim.toplanti not in AssemblyMeeting.values:
            raise ValueError(TOPLANTI_GECERSIZ)
    elif secim.toplanti:
        raise ValueError(TOPLANTI_GECERSIZ)


def _cizim(belge: evrak.Belge, bicim: str) -> bytes:
    """Biçimin çizicisi (tek içerik, dört çizici)."""
    if bicim == DocumentFormat.PDF:
        return evrak.pdf_ciz(belge)
    if bicim == DocumentFormat.DOCX:
        return evrak.docx_ciz(belge)
    if bicim == DocumentFormat.XLSX:
        return evrak.xlsx_ciz(belge)
    if bicim == DocumentFormat.HTML:
        return evrak.web_html_ciz(belge).encode("utf-8")
    raise ValueError(BICIM_GECERSIZ)


def dosya_adi(kod: str, gun: date, bicim: str, *, toplanti: str = "", adli: bool = False) -> str:
    """Kaydedilen dosyanın adı: belge + kapsam (toplantı) + tarih (sözlük §3). Kişi adı, dönem adı ve
    sınıf taşımaz: 'Genel-Kurul-Duyurusu-İkinci-Toplantı_20.11.2026.pdf'."""
    kok = ADLI_DOSYA_ADI_KOKLERI[kod] if adli else DOSYA_ADI_KOKLERI[kod]
    if toplanti:
        kok = f"{kok}-{TOPLANTI_KAPSAMLARI[toplanti]}"
    return f"{kok}_{gun:%d.%m.%Y}.{UZANTILAR[bicim]}"


def indirme_yaniti(icerik: bytes, *, dosya_adi: str, mime: str) -> FileResponse:
    """Bellekteki dosyanın indirme yanıtı: ek olarak, önbelleğe alınmadan (`no-store`; R9). Türkçe
    harfli ad Content-Disposition'a Django'nun kodlamasıyla girer (E63'ün kalıbı)."""
    from io import BytesIO

    yanit = FileResponse(BytesIO(icerik), as_attachment=True, filename=dosya_adi, content_type=mime)
    yanit["Cache-Control"] = "no-store"
    return yanit


def _uretim_yetkisi(kod: str, roller: frozenset[str]) -> None:
    """Üreten rol (modül başlığı "Üretim"): genel kurul belgelerinde genel kurul yazma kapısı, sonra
    tasarım §9.6'nın "Üreten"i."""
    if kod in GENEL_KURUL_KODLARI:
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.GENEL_KURUL_YAZMA)
    kim = yazar()
    if kim is None or kim.sistem_mi or kim.rol not in roller:
        raise RolYetkisiz


# ---------------------------------------------------------------------------
# Üretim (kişisiz)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Uretim:
    """Üretimin sonucu: evrak kaydı ve basım uyarıları (belgeye basılmaz)."""

    kayit: GeneratedDocument
    uyarilar: tuple[str, ...]


def uret(kod: str, konu: models.Model, *, kip: str = "", toplanti: str = "") -> Uretim:
    """Evrakı üretir ve kaydeder (modül başlığı "Üretim"); yeni sürümün kaydını döner."""
    if kod not in KURUCULAR:
        raise ValueError(KOD_GECERSIZ)
    secim = Secim(kip=kip, toplanti=toplanti)
    _secim_denetimi(kod, secim)
    yazma_kapisi()
    app_password.require_password_set()
    _uretim_yetkisi(kod, URETEN_ROLLER[kod])
    guncel, donem = _konu_ve_donem(kod, konu)
    belge, uyarilar = KURUCULAR[kod](guncel, secim)
    if belge.kod != kod:
        raise ValueError(KOD_GECERSIZ)
    saklananlar = [bicim for bicim in BICIMLER[kod] if bicim in SAKLANAN_BICIMLER]
    cizimler = {bicim: _cizim(belge, bicim) for bicim in saklananlar}
    gun = timezone.localdate()
    with transaction.atomic():
        kayit = evrak_servisi.kaydet(
            belge,
            konu=guncel,
            bicimler=BICIMLER[kod],
            donem=donem,
            hazirlik_yazimi=kod in GENEL_KURUL_KODLARI,
            kip=secim.kip,
            toplanti=secim.toplanti,
        )
        for bicim in saklananlar:
            evrak_servisi.dosya_ekle(
                kayit,
                cizimler[bicim],
                bicim=bicim,
                dosya_adi=dosya_adi(kod, gun, bicim, toplanti=secim.toplanti),
            )
    return Uretim(kayit=kayit, uyarilar=uyarilar)


# ---------------------------------------------------------------------------
# Veli adlı çıktı (R9; U15)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AdliCikti:
    """Veli adlı çıktının sonucu: verilecek bayt, dosya adı ve türü; kayıt ve basım uyarıları. Bayt
    hiçbir yerde saklanmaz (modül başlığı "Veli adlı çıktı")."""

    icerik: bytes
    dosya_adi: str
    mime: str
    kayit: GeneratedDocument
    uyarilar: tuple[str, ...]


def adli_uret_ve_ver(
    kod: str, kurul: GeneralAssembly, *, bicim: str, toplanti: str = ""
) -> AdliCikti:
    """Veli adlı belgeyi tek istekte üretir ve verir (modül başlığı "Veli adlı çıktı")."""
    if kod not in ADLI_KURUCULAR:
        raise ValueError(KOD_GECERSIZ)
    if bicim not in ADLI_BICIMLER[kod]:
        raise ValueError(BICIM_GECERSIZ)
    secim = Secim(kip=DocumentVariant.ADLI, toplanti=toplanti)
    _secim_denetimi(kod, secim, adli=True)
    yazma_kapisi()
    app_password.require_password_set()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KISISEL_VERI_CIKTISI)
    guncel, donem = _konu_ve_donem(kod, kurul)
    if not isinstance(guncel, GeneralAssembly):  # adlı kipin kodları genel kurul belgesidir
        raise ValueError(KONU_GECERSIZ)
    icerik = ADLI_KURUCULAR[kod](guncel, secim.toplanti)
    if icerik.belge.kod != kod or icerik.satir_sayisi < 0:
        raise ValueError(KOD_GECERSIZ)
    dosya = _cizim(icerik.belge, bicim)
    ozet = hashlib.sha256(dosya).hexdigest()
    with transaction.atomic():
        kayit = evrak_servisi.kaydet(
            icerik.belge,
            konu=guncel,
            bicimler=(bicim,),
            donem=donem,
            kisi_listesi=True,
            satir_sayisi=icerik.satir_sayisi,
            hazirlik_yazimi=True,
            kip=secim.kip,
            toplanti=secim.toplanti,
        )
        denetim_izi.basim(
            model=str(kayit.subject_type), object_id=str(kayit.subject_id), kod=kod, sha256=ozet
        )
        erisim_gunlugu.yaz(
            AccessKind.VELI_LISTESI_CIKTISI,
            model=GeneralAssembly,
            object_id=guncel.pk,
            document_sha256=ozet,
            row_count=icerik.satir_sayisi,
        )
    # Kişi adı yazılmaz: kod ve satır sayısı yeter (modül başlığı).
    logger.info("Veli adlı evrak verildi (%s, %s satır).", kod, icerik.satir_sayisi)
    return AdliCikti(
        icerik=dosya,
        dosya_adi=dosya_adi(kod, timezone.localdate(), bicim, toplanti=secim.toplanti, adli=True),
        mime=MIME_TURLERI[bicim],
        kayit=kayit,
        uyarilar=icerik.uyarilar,
    )


# ---------------------------------------------------------------------------
# Liste ve basım
# ---------------------------------------------------------------------------
def evrak_listesi(konu: models.Model) -> list[GeneratedDocument]:
    """Konunun geçerli genel kurul evrakı kayıtları (kod, kip ve toplantı sırasıyla); veli adlı
    kayıtlar dahil (yalnız tür, tarih ve satır sayısıyla; dosyaları yoktur)."""
    return list(
        GeneratedDocument.objects.filter(
            subject_type=denetim_izi.model_etiketi(type(konu)),
            subject_id=denetim_izi.kimlik_metni(type(konu), konu.pk),
            doc_type__in=KODLAR,
            status=DocumentStatus.GECERLI,
        ).order_by("doc_type", "variant", "meeting", "-version")
    )


def _okuma_yetkisi(kod: str) -> None:
    """Basan rol belgenin satırını okuyabilmeli (tasarım §4.4.2 "Okuma"); yoksa 403."""
    kim = yazar()
    if (
        kim is None
        or kim.sistem_mi
        or kim.rol not in rol_izinleri.okuyabilen_roller(OKUMA_SATIRLARI[kod])
    ):
        raise RolYetkisiz


def bas(kayit: GeneratedDocument, bicim: str) -> FileResponse:
    """Kaydın dosyasını verir ve `BASIM` satırını yazar (modül başlığı "Basım").

    Kod bu belgelerden biri değilse, biçim kayıtta yoksa, kayıt veli adı taşıyorsa ya da saklanan
    dosya eklenmemişse 404. Kayıtlı içerik tutmuyorsa (`EvrakIcerigiTutmuyor`) ya da dosya
    okunamazsa bayt verilmez, iz yazılmaz.
    """
    kod = str(kayit.doc_type)
    if kod not in KODLAR or bicim not in kayit.formats or kayit.personal_list:
        raise Http404
    _okuma_yetkisi(kod)
    ad = dosya_adi(kod, timezone.localdate(kayit.generated_at), bicim, toplanti=str(kayit.meeting))
    if bicim in SAKLANAN_BICIMLER:
        ek = kayit.ekler().filter(mime=evrak_servisi.BICIM_TURLERI[bicim]).last()
        if ek is None:
            raise Http404
        yanit = dosya_deposu.indirme_yaniti(ek, dosya_adi=ad)
        ozet = str(ek.sha256)
    else:
        icerik = _cizim(evrak_servisi.yeniden_ciz(kayit), bicim)
        yanit = indirme_yaniti(icerik, dosya_adi=ad, mime=MIME_TURLERI[bicim])
        ozet = hashlib.sha256(icerik).hexdigest()
    with transaction.atomic():
        denetim_izi.basim(
            model=str(kayit.subject_type), object_id=str(kayit.subject_id), kod=kod, sha256=ozet
        )
    return yanit


def bicim_coz(metin: str, bicimler: Mapping[str, str] = UZANTILAR) -> str:
    """Yoldaki biçim ('pdf', 'docx', 'xlsx', 'html') → kaydın biçimi; tanınmazsa 404."""
    for bicim, uzanti in bicimler.items():
        if metin == uzanti:
            return bicim
    raise Http404
