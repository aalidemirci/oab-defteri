"""Dış yedek hatırlatması (tasarım §16 R6, §4.3 tehdit 18; aile iskeletinden).

**Sorun.** Program her gün şifreli bir yedek alır, ama o yedekler aynı diskte
durur: disk bozulur, bilgisayar çalınır ya da yeniden kurulursa otomatik
yedekler de gider. Okulun elinde kalan tek kopya, kullanıcının Ayarlar →
Güvenlik'ten seçtiği yere kaydettiği şifreli yedektir. Bu modül son kaydın
tarihini tutar ve belli bir süre geçince Genel Bakış'a kart düşürür.

**Karar — tarih VERİTABANINDA DEĞİL, veri dizinindeki bir dosyada tutulur**
(`dis-yedek.json`, `guvenlik.json` ile aynı yer). Gerekçe:

1. Dış yedek veritabanının değil **bu bilgisayarın** fiziksel bir olgusudur. Tarih
   veritabanında olsaydı, eski bir yedeği geri yüklemek son dış yedeğin tarihini
   de geri sarardı (ya da yeni bilgisayara taşınan veritabanı "dış yedek alındı"
   derdi, oysa yeni diskte hiç kopya yoktur).
2. Model alanı gerekmez: göç yoktur, `SchoolConfig` şişmez.
3. Dosya kişisel veri taşımaz: yalnız bir zaman damgası ve bir gün sayısı.

**Hangi olay "dış yedek" sayılır?** Kullanıcının istediği şifreli yedeğin seçilen yere
yazılıp denetlenmesi ve asıl adını alması (`encrypted_backup.sifreli_yedegi_kaydet`; kullanıcı
kararı 04.11.2026 "Şifreli yedeği program kaydeder"). Program dosyanın USB bellekte olduğunu
bilemez, yalnız seçilen yere sağlam yazıldığını bilir; kart bu yüzden son şifreli yedeği söyler
ve dosyanın USB belleğe alınmasını ister (dürüst dil).

**Hatırlatma ne zaman?**

* Hiç kayıt yoksa: ilk program yöneticisi hesabı kurulduktan `ILK_HATIRLATMA_GUN`
  gün sonra (başlangıç, `guvenlik.json`'un oluşturma damgasıdır — yeni bilgisayara
  kurtarma anahtarıyla geri yüklenen kurulumda o damga kurtarma anahtarının üretim
  günüdür, yani eski bir tarihtir (`backup_restore._creation_stamp`); kart hemen
  çıkar, doğrusu da budur: yeni diskte henüz dış kopya yoktur).
* Kayıt varsa: son kayıttan `hatirlatma_gun` gün sonra (varsayılan 30 —
  kılavuzun "ayda bir"i; ayarla 7-90).

Dosya okunamazsa ya da bozuksa hiç kayıt yokmuş gibi davranılır (hatırlatma
tarafında hata yapmak kayıptan iyidir); yazma hatası yedeği DURDURMAZ, yalnız
günlüğe olay düşer. Tarihler yerel gündür (`timezone.localdate`; saat dilimi
`Europe/Istanbul`).
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi
from apps.okul.models import AuditAction
from apps.okul.services import app_password

logger = logging.getLogger("oab_defteri.yedek")

#: Veri dizinindeki dosyanın adı (`guvenlik.json`, `yedekleme.json` ile yan yana).
DOSYA_ADI: Final = "dis-yedek.json"
DOSYA_SURUMU: Final = 1

#: Son kayıttan sonra hatırlatmanın varsayılan süresi (gün) — kılavuzun "ayda bir"i.
VARSAYILAN_HATIRLATMA_GUN: Final = 30
#: Ayarın sınırları (gün). Bir haftadan sık hatırlatma gürültüdür, üç aydan seyrek
#: hatırlatma bir dönemin kaydını tek diske bırakır.
EN_AZ_HATIRLATMA_GUN: Final = 7
EN_COK_HATIRLATMA_GUN: Final = 90
#: Hiç kayıt yokken ilk hatırlatma, ilk hesap kurulduktan bu kadar gün sonra.
ILK_HATIRLATMA_GUN: Final = 7

SURE_ARALIK_MESAJI: Final = (
    f"Hatırlatma süresi {EN_AZ_HATIRLATMA_GUN} ile {EN_COK_HATIRLATMA_GUN} gün arasında olmalıdır."
)

_kilit = threading.Lock()


@dataclass(frozen=True)
class DisYedekDurumu:
    """Kartın ve ayar ekranının okuduğu özet (kişisel veri yok)."""

    #: Son şifreli yedeğin kaydedildiği an (ISO, yerel dilim); hiç yoksa None.
    son_indirme: str | None
    hatirlatma_gun: int
    #: Son kayıttan (yoksa ilk hesabın kurulumundan) bu yana geçen gün; bilinmiyorsa None.
    gecen_gun: int | None
    #: Genel Bakış kartı gösterilsin mi?
    hatirlat: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "last_download": self.son_indirme,
            "reminder_days": self.hatirlatma_gun,
            "days_since": self.gecen_gun,
            "remind": self.hatirlat,
            "min_reminder_days": EN_AZ_HATIRLATMA_GUN,
            "max_reminder_days": EN_COK_HATIRLATMA_GUN,
        }


def dosya_yolu() -> Path:
    """`dis-yedek.json` — güvenlik dosyasının dizini (paketli kipte veri dizini)."""
    return app_password.state_path().parent / DOSYA_ADI


def _oku() -> dict[str, Any]:
    """Dosyayı okur; yoksa, okunamıyorsa ya da biçimsizse boş sözlük (hata yükseltmez)."""
    try:
        veri: Any = json.loads(dosya_yolu().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        logger.warning("Dış yedek kaydı okunamadı; hiç kayıt yokmuş gibi davranılıyor.")
        return {}
    return veri if isinstance(veri, dict) else {}


def _yaz(veri: dict[str, Any]) -> None:
    """Atomik yazım (.tmp → yerine koy): yarım dosya kalmaz."""
    yol = dosya_yolu()
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_name(yol.name + ".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    gecici.replace(yol)


def _hatirlatma_gun(veri: dict[str, Any]) -> int:
    deger = veri.get("hatirlatma_gun")
    if isinstance(deger, int) and EN_AZ_HATIRLATMA_GUN <= deger <= EN_COK_HATIRLATMA_GUN:
        return deger
    return VARSAYILAN_HATIRLATMA_GUN


def _an(deger: Any) -> datetime | None:
    if not isinstance(deger, str) or not deger:
        return None
    try:
        an = datetime.fromisoformat(deger)
    except ValueError:
        return None
    return an if timezone.is_aware(an) else timezone.make_aware(an)


def _parola_kurulum_gunu() -> date | None:
    """`guvenlik.json`'un oluşturma damgası (yerel gün); yoksa ya da okunamazsa None."""
    try:
        durum = app_password.read_state()
    except app_password.AppPasswordError:
        return None
    if not durum:
        return None
    an = _an(durum.get("olusturma"))
    return timezone.localtime(an).date() if an else None


def indirme_kaydet(an: datetime | None = None) -> None:
    """Şifreli yedeğin kaydedildiği anı yazar. HATA YÜKSELTMEZ (yedek zaten yerindedir)."""
    zaman = timezone.localtime(an or timezone.now())
    with _kilit:
        veri = _oku()
        veri["surum"] = DOSYA_SURUMU
        veri["son_indirme"] = zaman.isoformat(timespec="seconds")
        veri["hatirlatma_gun"] = _hatirlatma_gun(veri)
        try:
            _yaz(veri)
        except OSError:
            logger.warning("Dış yedek tarihi yazılamadı; yedek yine de kaydedildi.")


def hatirlatma_suresini_ayarla(gun: int) -> DisYedekDurumu:
    """Hatırlatma süresini değiştirir; aralık dışıysa `ValueError` (400).

    Ayar değişikliği oturumdaki hesabın `GUNCELLE` satırıdır (tasarım §4.6.2; nesne
    `dis_yedek.ayar`, gün sayısı `[önce, sonra]` değeriyle). Sıra `guvenlik.json`
    yazımlarındakiyle aynıdır: önce dosya kilidi, sonra veritabanı işlemi; satır dosyadan
    ÖNCE eklenir, dosya yazılamazsa işlem geri sarılır (iz yapılmamış işi anlatmaz).
    """
    if isinstance(gun, bool) or not EN_AZ_HATIRLATMA_GUN <= gun <= EN_COK_HATIRLATMA_GUN:
        raise ValueError(SURE_ARALIK_MESAJI)
    with _kilit, transaction.atomic():
        veri = _oku()
        onceki = _hatirlatma_gun(veri)
        denetim_izi.olay(
            AuditAction.GUNCELLE,
            model=denetim_izi.DIS_YEDEK_AYARI,
            object_id="hatirlatma_gun",
            changed_fields=["hatirlatma_gun"],
            values={"hatirlatma_gun": [onceki, gun]},
        )
        veri["surum"] = DOSYA_SURUMU
        veri["hatirlatma_gun"] = gun
        _yaz(veri)
    return durum()


def durum(bugun: date | None = None) -> DisYedekDurumu:
    """Kartın özeti. Hesap kurulmamışsa (yedek alınamaz) hatırlatma yoktur."""
    gun = bugun or timezone.localdate()
    with _kilit:
        veri = _oku()
    sure = _hatirlatma_gun(veri)
    son = _an(veri.get("son_indirme"))
    if son is not None:
        gecen = max(0, (gun - timezone.localtime(son).date()).days)
        return DisYedekDurumu(
            son_indirme=timezone.localtime(son).isoformat(timespec="seconds"),
            hatirlatma_gun=sure,
            gecen_gun=gecen,
            hatirlat=gecen >= sure,
        )
    kurulum = _parola_kurulum_gunu()
    if kurulum is None:
        return DisYedekDurumu(son_indirme=None, hatirlatma_gun=sure, gecen_gun=None, hatirlat=False)
    gecen = max(0, (gun - kurulum).days)
    return DisYedekDurumu(
        son_indirme=None,
        hatirlatma_gun=sure,
        gecen_gun=gecen,
        hatirlat=gecen >= min(ILK_HATIRLATMA_GUN, sure),
    )
