"""Yedek Raporu (plan F1b-3 "Yedek raporu bu adımda, tam döküm"; tasarım §4.4.7, §9.7).

Program belgesidir: birlik evrakı değildir, E-kodu almaz, katalog sayımına girmez (§9.7). Aileden
gelmez, yeni yazılmıştır. Tek sayfa, kişisiz PDF'tir. Yalnız program yöneticisi basar (Ayarlar →
Güvenlik; `Eylem.YEDEK_INDIRME`, Güvenlik satırı). Dosyası saklanmaz, yanıt bellekten verilir; izi
E63'teki gibi `BASIM` satırıdır (kod ve PDF'in sha256'sı; `hesaplar.teslim_pusulasi` kalıbı). Satır
yazılamazsa PDF verilmez (409 `iz_yazilamadi`). Kod `KOD`'dur: E-kodu olmayan belge için
`denetim_izi.basim` bu sabiti kabul eder.

İÇERİK (planın lafzı):

* bu bilgisayardaki yedekler türlerine göre: adet, en eski ve en yeni tarih, saklama kuralı. Tür ve
  tarih dosyanın ADINDAN okunur (rotasyonun deseni ve kuralı; `desktop.backup.ROTASYON_KUMESI`): dosya
  zamanı yedeğin anını söylemez. Saklama rakamları rotasyon sabitlerinden gelir, metne elle yazılmaz.
  Adları F4'te yazılacak türlerin dosyası (`pre-anonim`, `pre-kapanis`, `pre-dek-yenileme`) "Öteki
  yedek" satırında sayılır; bugün üreticileri bağlı değildir (kullanıcı kararı 04.11.2026 "Ekran
  adları": F4'te gelen türlerin adları F4'tedir). Adı hiçbir desene uymayan `.odbak` (elle
  adlandırılmış dosya, yedek klasörüne kopyalanmış şifreli yedek) "Elle konmuş yedek" satırında yalnız
  sayılır: ad serbest metindir, rapora girmez (R1), rotasyon ona dokunmaz, tarihi de bilinmez;
* her yedeği açan kurtarma anahtarının no'su ve tarihi: dosyanın yalnız başı okunur, kurtarma anahtarı
  gerekmez (`live_restore.recovery_key_of`). Okunamayan dosya "Okunamadı" diye sayılır, rapor düşmez.
  Sayfa bütçesi için en yeni `ANAHTAR_SATIRI_SINIRI` anahtar ayrı satırdır, ötekiler tek satırda
  toplanır;
* kenara alınmış önceki veritabanları (`db-onceki`; `-wal`/`-shm` eşleri sayılmaz);
* son şifreli yedeğin tarihi, denetlendiği ve kaç ek taşıdığı. Tarih hatırlatmanın okuduğu kayıttır
  (`dis_yedek`): yalnız dosya denetimden geçip asıl adını aldıktan sonra yazılır, bu yüzden
  "denetlendi" onun varlığıdır. Ek sayıları o kaydın `YEDEK` satırındandır (`_son_tam_satir`): satır
  dosyaya ad vermeden önce yazıldığı için ad verilemeyen yedeğin satırı kaydın ilerisinde kalır ve
  atlanır. Eski bir veritabanı geri yüklenmişse satır yoktur, ek sayısı "bilinmiyor" basılır;
* hatırlatma süresi ve "USB bellekteki yedek programın dışındadır" cümlesi.

BASILMAYANLAR: kişi adı (antette okul müdürü de yoktur: `principal_name` verilmez), yol, elle
adlandırılmış dosyanın adı. Yedeğin içi okunmaz: rapor başlıkları kurtarma anahtarı olmadan okur.
"""

from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Final

from desktop.backup import (
    DAILY_PREFIX,
    DEFAULT_KEEP_DAYS,
    DEFAULT_KEEP_PRE_MIGRATE,
    OLD_DB_PREFIX,
    PRE_MIGRATE_PREFIX,
    PRE_PAROLA_PREFIX,
    ROTASYON_KUMESI,
    RotasyonKurali,
    adin_gunu,
    is_old_database_file,
)
from desktop.backup_crypto import BACKUP_SUFFIX, KAPSAM_TAM
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AuditAction, AuditTrail, SchoolConfig
from apps.okul.services import app_password, dis_yedek, live_restore
from apps.okul.services.geri_yukleme_ekleri import KAPSAM_KODLARI
from shared.letterhead import letterhead_context
from shared.pdf import html_to_pdf
from shared.text import tr_upper

logger = logging.getLogger("oab_defteri.yedek")

#: Belgenin görünen adı (plan F1b-3): başlık `tr_upper` ile büyür, dosya adı buradan kurulur.
BELGE_ADI: Final = "Yedek Raporu"
#: `BASIM` satırının kodu ve kaydın kimliği (modül başlığı).
KOD: Final = denetim_izi.YEDEK_RAPORU_KODU
KIMLIK: Final = "yedek-raporu"
TEMPLATE_NAME: Final = "documents/yedek_raporu.html"

#: Rotasyon önekinin görünen adı (sözlük §1 "Yedek"; kullanıcı kararı 04.11.2026 "Ekran adları").
TUR_ADLARI: Final[Mapping[str, str]] = {
    DAILY_PREFIX: "Günlük yedek",
    PRE_MIGRATE_PREFIX: "Güncelleme öncesi yedek",
    PRE_PAROLA_PREFIX: "Kurulum yedeği",
}
OTEKI_YEDEK: Final = "Öteki yedek"
ELLE_KONMUS_YEDEK: Final = "Elle konmuş yedek"
ONCEKI_VERITABANI: Final = "Kenara alınan önceki veritabanı"
#: Rotasyonun dokunmadığı dosyanın saklama kuralı.
PROGRAM_SILMEZ: Final = "Program silmez"
OKUNAMADI: Final = "Okunamadı"
OTEKI_ANAHTARLAR: Final = "Öteki anahtarlar"
#: Anahtarın no'su ya da tarihi başlıkta yoksa.
BILINMIYOR: Final = "Bilinmiyor"
DENETLENDI: Final = "Dosya yazıldıktan sonra yeniden açılıp denetlendi."
HIC_ALINMADI: Final = "Bu bilgisayardan henüz şifreli yedek kaydedilmedi."
EK_SAYISI_BILINMIYOR: Final = "Bilinmiyor; bu yedeğin kaydı şimdiki kayıtlarda yok."
PROGRAMIN_DISINDA: Final = "USB bellekteki yedek programın dışındadır."

#: Sayfa bütçesi: en çok bu kadar anahtar ayrı satır olur (modül başlığı).
ANAHTAR_SATIRI_SINIRI: Final = 6
#: Tarih saniyeye kırpılı yazılır, satır ondan az önce yazılmış olabilir.
_KIRPMA_PAYI: Final = timedelta(seconds=1)
#: Satır ile kayıt arasında yalnız dosyanın asıl adını alması vardır.
_ESLESME_PAYI: Final = timedelta(minutes=5)


def _binlikli(sayi: int | None) -> str:
    """Evrakın sayı biçimi: üçlü gruplar nokta ile ayrılır (sözlük §3; RYUE md. 16/7)."""
    return "" if sayi is None else f"{sayi:,}".replace(",", ".")


@dataclass(frozen=True)
class TurSatiri:
    """Yedek türlerinin bir satırı; tarihler gg.aa.yyyy, bilinmiyorsa boş."""

    ad: str
    adet: int
    en_eski: str
    en_yeni: str
    saklama: str

    @property
    def adet_metni(self) -> str:
        return _binlikli(self.adet)


@dataclass(frozen=True)
class AnahtarSatiri:
    """Bir kurtarma anahtarının açtığı yedek sayısı (`no` anahtar no'su ya da satırın adıdır)."""

    no: str
    tarih: str
    adet: int

    @property
    def adet_metni(self) -> str:
        return _binlikli(self.adet)


@dataclass(frozen=True)
class SonSifreliYedek:
    tarih: str
    #: Taşıdığı ek ve giremeyen ek; `YEDEK` satırı yoksa None (modül başlığı).
    ek_sayisi: int | None
    eksik: int | None

    @property
    def ek_sayisi_metni(self) -> str:
        return _binlikli(self.ek_sayisi)

    @property
    def eksik_metni(self) -> str:
        return _binlikli(self.eksik)


@dataclass(frozen=True)
class BasilanRapor:
    """Bellekteki PDF ve indirme adı (dosya saklanmaz)."""

    pdf: bytes
    dosya_adi: str


def dosya_adi(gun: date | None = None) -> str:
    """İndirme adı: `Yedek-Raporu_gg.aa.yyyy.pdf` (kurtarma anahtarı belgesinin kalıbı)."""
    return f"{BELGE_ADI.replace(' ', '-')}_{gun or timezone.localdate():%d.%m.%Y}.pdf"


def _gun(deger: date | None) -> str:
    return "" if deger is None else f"{deger:%d.%m.%Y}"


def _dosya_adlari(dizin: Path) -> list[str]:
    """Dizindeki düzenli dosyalar; dizin yoksa ya da okunamıyorsa boş (rapor düşmez)."""
    try:
        with os.scandir(dizin) as girdiler:
            return sorted(girdi.name for girdi in girdiler if girdi.is_file(follow_symlinks=False))
    except OSError as hata:
        logger.warning("Yedek raporu için dizin okunamadı (%s).", type(hata).__name__)
        return []


def _yedek_kurali(ad: str) -> tuple[RotasyonKurali, date] | None:
    """Adı rotasyonun yedek dizinindeki bir desenine uyuyorsa kuralı ve yedeğin günü."""
    for kural in ROTASYON_KUMESI:
        if not kural.veri_dizininde and (gun := adin_gunu(kural.desen, ad)) is not None:
            return kural, gun
    return None


def _saklama(kural: RotasyonKurali) -> str:
    return f"Son {DEFAULT_KEEP_PRE_MIGRATE} yedek" if kural.adetle else f"{DEFAULT_KEEP_DAYS} gün"


def _satir(ad: str, gunler: list[date], saklama: str) -> TurSatiri:
    return TurSatiri(
        ad=ad,
        adet=len(gunler),
        en_eski=_gun(min(gunler, default=None)),
        en_yeni=_gun(max(gunler, default=None)),
        saklama=saklama,
    )


def _tur_satirlari(adlar: Iterable[str], veri_adlari: Iterable[str]) -> list[TurSatiri]:
    """Adı olan türler her zaman, adsız türler ve elle adlı dosyalar varsa basılır."""
    turler: dict[str, list[date]] = {ad: [] for ad in TUR_ADLARI.values()}
    saklamalar: dict[str, str] = {}
    elle_adli = 0
    for kural in ROTASYON_KUMESI:
        if not kural.veri_dizininde:
            saklamalar[TUR_ADLARI.get(kural.onek, OTEKI_YEDEK)] = _saklama(kural)
    for ad in adlar:
        bulunan = _yedek_kurali(ad)
        if bulunan is None:
            elle_adli += 1
            continue
        kural, gun = bulunan
        turler.setdefault(TUR_ADLARI.get(kural.onek, OTEKI_YEDEK), []).append(gun)
    satirlar = [_satir(ad, gunler, saklamalar[ad]) for ad, gunler in turler.items()]
    if elle_adli:
        satirlar.append(TurSatiri(ELLE_KONMUS_YEDEK, elle_adli, "", "", PROGRAM_SILMEZ))
    onceki = next(kural for kural in ROTASYON_KUMESI if kural.onek == OLD_DB_PREFIX)
    gunler = [
        gun
        for ad in veri_adlari
        if is_old_database_file(ad) and (gun := adin_gunu(onceki.desen, ad)) is not None
    ]
    satirlar.append(_satir(ONCEKI_VERITABANI, gunler, _saklama(onceki)))
    return satirlar


def _anahtar_satirlari(yedekler: Path, adlar: Iterable[str]) -> list[AnahtarSatiri]:
    """Her yedeği açan kurtarma anahtarı, en yeniden eskiye; okunamayanlar son satırdadır."""
    sayilar: dict[tuple[int, str], int] = {}
    okunamayan = 0
    for ad in adlar:
        kimlik = live_restore.recovery_key_of(yedekler / ad)
        if kimlik is None:
            okunamayan += 1
            continue
        anahtar = (kimlik["no"] or 0, kimlik["tarih"] or "")
        sayilar[anahtar] = sayilar.get(anahtar, 0) + 1
    sirali = sorted(sayilar.items(), reverse=True)
    satirlar = [
        AnahtarSatiri(
            no=str(no) if no else BILINMIYOR,
            tarih=_gun(date.fromisoformat(tarih)) if tarih else "",
            adet=adet,
        )
        for (no, tarih), adet in sirali[:ANAHTAR_SATIRI_SINIRI]
    ]
    kalan = sum(adet for _, adet in sirali[ANAHTAR_SATIRI_SINIRI:])
    if kalan:
        satirlar.append(AnahtarSatiri(OTEKI_ANAHTARLAR, "", kalan))
    if okunamayan:
        satirlar.append(AnahtarSatiri(OKUNAMADI, "", okunamayan))
    return satirlar


def _deger(satir: AuditTrail, alan: str) -> Any:
    """`YEDEK` satırının kişisiz değeri (`[None, değer]`); yoksa None."""
    cift = satir.values.get(alan)
    return cift[1] if isinstance(cift, list) and len(cift) == 2 else None


def _son_tam_satir(kayit: datetime) -> AuditTrail | None:
    """Kaydın `YEDEK` satırı: kayıttan önceki son tam yedek, yeterince yakınsa (modül başlığı)."""
    try:
        sinir = kayit + _KIRPMA_PAYI
    except OverflowError:
        # Tarih aralığının son saniyesi: bu damga ancak bozuk dosyadan gelir, satırı yoktur.
        return None
    sorgu = AuditTrail.objects.filter(
        action=AuditAction.YEDEK, model=denetim_izi.YEDEK_DOSYASI, at__lte=sinir
    )
    for satir in sorgu.order_by("-seq").iterator():
        if _deger(satir, "kapsam") == KAPSAM_KODLARI[KAPSAM_TAM]:
            return satir if kayit - satir.at <= _ESLESME_PAYI else None
    return None


def _son_sifreli_yedek(son_indirme: str | None) -> SonSifreliYedek | None:
    if son_indirme is None:
        return None
    kayit = datetime.fromisoformat(son_indirme)
    tarih = _gun(timezone.localtime(kayit).date())
    satir = _son_tam_satir(kayit)
    if satir is None:
        return SonSifreliYedek(tarih=tarih, ek_sayisi=None, eksik=None)
    return SonSifreliYedek(
        tarih=tarih, ek_sayisi=_deger(satir, "dosya_sayisi"), eksik=_deger(satir, "eksik")
    )


def _baglam() -> dict[str, Any]:
    yedekler = app_password.backup_dir()
    yedek_adlari = [ad for ad in _dosya_adlari(yedekler) if ad.endswith(BACKUP_SUFFIX)]
    veri_adlari = _dosya_adlari(app_password.state_path().parent)
    durum = dis_yedek.durum()
    okul = SchoolConfig.load()
    return {
        # Müdürün adı verilmez: belge kişisizdir.
        **letterhead_context(school_name=okul.school_name, district=okul.district),
        "document_title": tr_upper(BELGE_ADI),
        "basim_gunu": _gun(timezone.localdate()),
        "turler": _tur_satirlari(yedek_adlari, veri_adlari),
        "anahtarlar": _anahtar_satirlari(yedekler, yedek_adlari),
        "son_yedek": _son_sifreli_yedek(durum.son_indirme),
        "hatirlatma_gun": durum.hatirlatma_gun,
        "denetlendi": DENETLENDI,
        "hic_alinmadi": HIC_ALINMADI,
        "ek_sayisi_bilinmiyor": EK_SAYISI_BILINMIYOR,
        "programin_disinda": PROGRAMIN_DISINDA,
    }


def yedek_raporu() -> BasilanRapor:
    """Raporun PDF'i; dosya saklanmaz (modül başlığı).

    Sıra teslim pusulasınınkidir: yetki → PDF bellekte çizilir → `BASIM` satırı. Satır
    yazılamazsa `IzYazilamadi` yükselir, PDF verilmez. Kişisiz günlük satırı yazılır.
    """
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.YEDEK_INDIRME)
    pdf = html_to_pdf(render_to_string(TEMPLATE_NAME, _baglam()))
    with transaction.atomic():
        denetim_izi.basim(
            model=denetim_izi.YEDEK_RAPORU,
            object_id=KIMLIK,
            kod=KOD,
            sha256=hashlib.sha256(pdf).hexdigest(),
        )
    logger.info("Yedek raporu basıldı.")
    return BasilanRapor(pdf=pdf, dosya_adi=dosya_adi())
