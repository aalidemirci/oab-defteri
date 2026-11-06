"""Şifreli yedeğin programca kaydedilmesi (tasarım §2.3.1, §4.4.7, §16 R6; plan F1b-3).

Kullanıcı kararı 04.11.2026 "Şifreli yedeği program kaydeder": düğme programın "Farklı kaydet"
penceresini açar, yeri kullanıcı seçer, adı program önerir (`onerilen_ad`). Yedek tamdır: veritabanı,
manifesto ve dosya deposunun şifreli baytları (`backup_crypto.tam_yedek_yaz`). Bellek içi indirme
yoktur. Program dosyanın USB bellekte olduğunu bilemez, yalnız seçilen yere sağlam yazıldığını bilir.

SIRA (`sifreli_yedegi_kaydet`):

1. Kilit ve yetki: yalnız program yöneticisi (tasarım §4.4.2 Güvenlik satırı "yedek indirme"). Rol
   kapısının ardından servis de isteğin yazarını sorar (`RolYetkisiz`, 403); ret görüntü alınmadan
   verilir. Denetim uzun iş sayacının İÇİNDEDİR: sayaçtan önce verilen bir kilit kararı burada
   görülür, sayaçtan sonraki kilit de işin sonuna ertelenir; arada DEK düşmez.
2. Hedef yolun denetimi (`_hedef_denetle`).
3. Boş yer ve FAT32'nin tek dosya sınırı (`_yer_denetle`). Tahmini boy görüntüden ve manifestodaki
   kapların boyundan gelir. Tür ya da boş yer okunamazsa yazım denenir, hata iletiye çevrilir.
4. Her ek yazmadan önce bir kez baştan sona okunur (`_ekleri_on_oku`; kullanıcı kararı 05.11.2026).
   Manifesto mühürlendikten sonra `eksik` yazılamaz; okunurken disk hatası veren dosya her denemede
   yedeği düşürürdü. Okunamayan ek `eksik` sayılır, yedek yine alınır. Elde DEK olduğu için ek açılıp
   manifestoyla da sınanır: 5. adımdaki denetim bozuk kopyayı her denemede reddederdi. İçi tutmayan
   ek de `eksik` sayılır (kullanıcı kararı 06.11.2026). Bellekte aynı anda tek ek durur: kap tek
   parçadır, GCM sonda doğrular (`shared.dosya_sifreleme`, üst sınır 64 MiB); depo bellekte toplanmaz.
5. Seçilen yerde geçici adla akışla yazım, sonra yazılan dosyanın diskte yeniden açılıp denetlenmesi
   (`_yazilani_denetle`): başlık, mühürlü bölüm, veritabanı, manifesto, dosya bölümünün yapısı ve her
   ekin içeriği. Denetim programın bellekteki kopyasından yapılmaz. POSIX'te dosyanın önbellek
   sayfaları okumadan önce bırakılır (`_onbellegi_birak`): okuma aygıttan gelir, denetim yerin okuma
   hızında koşar. Kalan risk: Windows'ta bu adım yoktur, denetim işletim sisteminin önbelleğinden
   okuyabilir; aygıtın kendi önbelleğini hiçbir platformda görmez. Düşerse geçici dosya silinir, satır
   yazılmaz.
6. `YEDEK` satırı (tasarım §4.6.3): oturumdaki hesabın satırı, açık kip, nesne `yedek.dosya`. Satır
   yazılamazsa geçici dosya silinir, yedek verilmez (izsiz yedek yoktur). Yedek görüntüsü satırdan
   önce alındığı için yedeğin içinde kendi satırı yoktur.
7. Dosyaya asıl adı verilir (`os.replace`), sonra dış yedek hatırlatması sıfırlanır (§16 R6). Asıl ad
   verilemezse satır kalır, geçici dosya silinir, hatırlatma sıfırlanmaz, kullanıcıya ileti gider.

İptalde (yol gelmezse) hiçbir şey yazılmaz. Kalan risk planda yazılıdır: denetimle satır arasında
süreç ölürse seçilen yerde geçici adlı, izsiz bir dosya kalır; program onu yedek saymaz.

YOL (tasarım §4.1; plan F1b-3): yol ön yüzden isteğin içinde gelir, masaüstü sunucuyu doğrudan
çağırmaz. Sunucu yola güvenmez: mutlak yol, var olan üst dizin, program uzantısı. Veri dizininin, yedek
dizininin ve dosya deposunun içine yazılmaz: bilgisayarda kalan kopya disk bozulunca onlarla birlikte
gider, rotasyon ve geri yükleme listesi de o dizinlere bakar. Bu denetim yolun metnine ve dosya
kimliğine bakar (`_icinde_mi`). Kimlik aynı dizinin başka yazımını da tanır: Windows'un uzun yol
öneki, Windows 11'de bilgisayarın kendi paylaşımından geçen yol. Ağ yolu reddedilmez, okulun ağ
paylaşımı meşru bir dış yerdir. Hedefte düzenli dosya varsa kullanıcı pencerede üzerine yazmayı
onaylamıştır, yeni dosya ancak denetimden geçince onun yerine geçer; düzenli olmayan hedefe (dizin,
sembolik bağ, aygıt) yazılmaz. Sembolik bağ izlenmez. Geçici ad programa özgüdür (`GECICI_EK`),
`O_EXCL` ve 0600 ile açılır (`yeni_yedek_dosyasi`).

SERBEST AD (R1): kullanıcı pencerede dosya adını değiştirebilir, ad serbest metindir, kişi adı
içerebilir. Satırın kimliği, günlük ve iletiler yalnız programın ad desenine birebir uyan adı taşır;
uymuyorsa kimlik programın yazım anında ürettiği addır (`_yedek_kimligi`). Yol hiçbir satıra, günlüğe,
iletiye ve yanıta yazılmaz: Windows yolu hesap adını taşır. Ham `OSError`'ın iletisi tam yolu taşıdığı
için buradan dışarı çıkmaz (`_yazim_iletisi`, `from None`); günlüğe yalnız türü yazılır.

UZUN İŞ (tasarım §4.2, §4.4.3; plan F1b-3 "Uzun iş, çarpı, temiz kapanış"): iş `UZUN_ISLER` ve bakım
kapısı içinde koşar: bakım sürerken başlamaz, sürerken kilit ertelenir. Aynı anda ikincisi 409 alır
(`_TEK_IS`). Sayaç ve kapı bağlam yöneticisidir: her çıkış yolunda düşer.

Başlık TK10 izdüşümüdür (`backup_crypto.usable_recovery_header`): yalnız kurtarma bölümü ve kurtarma
anahtarının kimliği; hesap sarmalları yedeğe girmez (tasarım §4.4.4). Başlıksız yedek üretilmez (plan
F1b-3 "Kap ve manifesto"): güvenlik dosyası kullanılamıyorsa yedek verilmez.
"""

from __future__ import annotations

import errno
import logging
import os
import re
import secrets
import shutil
import sqlite3
import stat
import threading
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import IO, Any, Final

from desktop.backup import goruntu_ve_manifesto
from desktop.backup_crypto import (
    BACKUP_SUFFIX,
    KAPSAM_TAM,
    BackupCryptoError,
    EkTutmuyorHatasi,
    Manifesto,
    ManifestoGirdisi,
    baslik_oku,
    dosya_bolumunu_oku,
    ek_denetle,
    load_public_key,
    muhurlu_bolumu_ac,
    tam_yedek_yaz,
    usable_recovery_header,
)
from desktop.dosya_sistemi import FAT_TEK_DOSYA_SINIRI, dosya_sistemi_turu, fat_mi
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import Attachment, AuditAction
from apps.okul.services import app_password, dis_yedek, dosya_deposu
from apps.okul.services.geri_yukleme_ekleri import KAPSAM_KODLARI
from shared import bakim, crypto
from shared import dosya_sifreleme as ds

logger = logging.getLogger("oab_defteri.yedek")

#: Programın ürettiği adın öneki ve deseni (tasarım §2.3.1; `fullmatch`, yalnız ASCII rakam).
AD_ONEKI: Final = "oab-defteri-yedek"
_PROGRAM_ADI: Final = re.compile(
    rf"{AD_ONEKI}-[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-[0-9]{{6}}{re.escape(BACKUP_SUFFIX)}"
)
#: Geçici dosyanın eki: rotasyon, liste ve geri yükleme yalnız asıl uzantıya bakar, yarım dosya
#: yedek sanılmaz. Adın kalanı rastgeledir, kullanıcının yazdığı addan türemez (R1).
GECICI_EK: Final = f"{BACKUP_SUFFIX}.tmp"
#: Boy tahmininin payı: kurtarma başlığı en çok 1 MB'tır, kalanı kabın sabit alanlarıdır.
_KAP_PAYI: Final = 2 * 1024 * 1024
#: Her ekin dosya bölümündeki başlığı ve manifestodaki satırı için pay.
_GIRDI_PAYI: Final = 256
#: Windows'un disk dolu ve dosya çok büyük kodları (`errno`'ya her zaman çevrilmez).
_WIN_YER_YOK: Final = frozenset({39, 112})
_WIN_COK_BUYUK: Final = 223

#: Kurtarma başlığı kullanılamıyor (başlıksız yedek üretilmez; modül başlığı).
GUVENLIK_DOSYASI_OKUNAMIYOR = "Güvenlik dosyası okunamıyor; şifreli yedek alınmadı."
KILITLI: Final = "Şifreli yedek oluşturmak için önce hesabınızla kilidi açın."
VERITABANI_YOK: Final = "Yedeklenecek veritabanı bulunamadı."
OLUSTURULAMADI: Final = "Şifreli yedek oluşturulamadı."
YER_SECILMEDI: Final = "Şifreli yedeğin kaydedileceği yer seçilmedi."
YER_KULLANILAMIYOR: Final = "Seçilen yer kullanılamıyor; başka bir yer seçin."
UZANTI_DEGISMIS: Final = "Dosyanın uzantısını değiştirmeyin; programın önerdiği adı kullanın."
PROGRAM_KLASORU: Final = (
    "Yedeği programın kendi klasörüne kaydetmeyin: bilgisayar bozulursa onunla birlikte gider. "
    "USB bellek gibi başka bir yer seçin."
)
DOSYA_DEGIL: Final = "Seçilen adda bir klasör ya da kısayol var; başka bir ad seçin."
YER_YOK: Final = "Seçilen yerde yeterli boş yer yok; şifreli yedek alınmadı."
FAT_SINIRI: Final = (
    "Yedek 4 GB'tan büyük; seçilen yer bu boyda tek dosya almıyor (FAT32 biçimli bellek). "
    "Başka bir yer seçin."
)
YAZILAMADI: Final = (
    "Şifreli yedek seçilen yere yazılamadı; yerin takılı ve yazılabilir olduğundan emin olun."
)
DENETIM_DUSTU: Final = (
    "Yazılan şifreli yedek denetimden geçmedi; dosya silindi. Yeniden deneyin, sorun sürerse "
    "başka bir yer seçin."
)
ASIL_AD_VERILEMEDI: Final = (
    "Şifreli yedek yazıldı ama dosyaya adı verilemedi; yedek alınmış sayılmadı. Aynı adlı dosya "
    "açıksa kapatıp yeniden deneyin."
)
YEDEK_ALINIYOR: Final = "Şifreli yedek zaten alınıyor; bitmesini bekleyin."
BAKIM_SURUYOR: Final = "Geri yükleme sürüyor; şifreli yedek alınmadı. Biraz sonra yeniden deneyin."

#: Aynı anda tek şifreli yedek: ikincisi beklemez, 409 alır (modül başlığı "UZUN İŞ").
_TEK_IS: Final = threading.Lock()


class EncryptedBackupError(ValueError):
    """Kullanıcıya gösterilebilen yedek oluşturma hatası."""


class YedekSuruyor(EncryptedBackupError):
    """Aynı anda ikinci şifreli yedek (409 `yedek_suruyor`)."""

    def __init__(self) -> None:
        super().__init__(YEDEK_ALINIYOR)


class BakimSuruyor(EncryptedBackupError):
    """Bakım kapısı kapalı: geri yükleme sürüyor (409 `bakim_suruyor`)."""

    def __init__(self) -> None:
        super().__init__(BAKIM_SURUYOR)


@dataclass(frozen=True)
class KayitSonucu:
    """Kaydedilen yedeğin kişisiz özeti (ucun yanıtı)."""

    #: Programın adı (R1): kullanıcının yazdığı serbest ad burada görünmez.
    ad: str
    boyut: int
    #: Yedeğin taşıdığı ek sayısı.
    ek_sayisi: int
    #: Yedeğe giremeyen ek sayısı (bulunamadı ya da bozuk; ikisi ayrı sayılmaz).
    eksik: int
    #: Yazılan dosya yeniden açılıp denetlendi. Denetimden geçmeyen yedek sonuç üretmez.
    denetlendi: bool = True

    def yanit(self) -> dict[str, Any]:
        return {
            "ad": self.ad,
            "boyut": self.boyut,
            "ek_sayisi": self.ek_sayisi,
            "eksik": self.eksik,
            "denetlendi": self.denetlendi,
        }


def _yeni_ad() -> str:
    """Programın saatli adı (tasarım §2.3.1; yerel saat, `Europe/Istanbul`)."""
    return f"{AD_ONEKI}-{timezone.localtime():%Y-%m-%d-%H%M%S}{BACKUP_SUFFIX}"


def _yedek_kimligi(hedef: Path) -> str:
    """Satırın kimliği: dosyanın adı programın desenine birebir uyuyorsa o, değilse yeni ad (R1)."""
    return hedef.name if _PROGRAM_ADI.fullmatch(hedef.name) else _yeni_ad()


def _kilit_ve_yetki() -> None:
    if app_password.is_locked():
        raise EncryptedBackupError(KILITLI)
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.YEDEK_INDIRME)


def onerilen_ad() -> str:
    """Kaydetme penceresinin önereceği ad (kullanıcı kararı 04.11.2026; adı program önerir)."""
    _kilit_ve_yetki()
    return _yeni_ad()


def _ayni_dizin_mi(aday: Path, kok: Path) -> bool:
    try:
        return os.path.samefile(aday, kok)
    except OSError:  # kök henüz yoksa ya da okunamıyorsa bu aday o dizin değildir
        return False


def _icinde_mi(yol: Path, kok: Path) -> bool:
    r"""`yol` `kok`'un kendisi ya da altı mı? Windows'ta büyük-küçük harf ayrılmaz.

    Metin karşılaştırması aynı dizinin başka yazımını görmez: `resolve` `\\?\C:\...` önekini korur.
    Dosya kimliği onu tanır (modül başlığı "YOL").
    """
    if Path(os.path.normcase(yol)).is_relative_to(os.path.normcase(kok)):
        return True
    return any(_ayni_dizin_mi(aday, kok) for aday in (yol, *yol.parents))


def _program_dizinleri() -> tuple[Path, ...]:
    return (app_password.state_path().parent, app_password.backup_dir(), dosya_deposu.depo_dizini())


def _hedef_denetle(ham: str) -> Path:
    """Gelen yolu denetler (modül başlığı "YOL"); iletiler yolu taşımaz."""
    if not ham:
        raise EncryptedBackupError(YER_SECILMEDI)
    hedef = Path(ham)
    if "\0" in ham or not hedef.is_absolute() or ".." in hedef.parts:
        raise EncryptedBackupError(YER_KULLANILAMIYOR)
    if hedef.suffix != BACKUP_SUFFIX:
        raise EncryptedBackupError(UZANTI_DEGISMIS)
    try:
        if not hedef.parent.is_dir():
            raise EncryptedBackupError(YER_KULLANILAMIYOR)
        ust = hedef.parent.resolve()
        program_klasorunde = any(_icinde_mi(ust, kok.resolve()) for kok in _program_dizinleri())
    except (OSError, RuntimeError):
        raise EncryptedBackupError(YER_KULLANILAMIYOR) from None
    if program_klasorunde:
        raise EncryptedBackupError(PROGRAM_KLASORU)
    try:
        duzenli = stat.S_ISREG(os.lstat(hedef).st_mode)
    except FileNotFoundError:
        return hedef
    except OSError:
        raise EncryptedBackupError(YER_KULLANILAMIYOR) from None
    if not duzenli:
        raise EncryptedBackupError(DOSYA_DEGIL)
    return hedef


def _tahmini_boy(veritabani: bytes, girdiler: Iterable[ManifestoGirdisi]) -> int:
    """Yedeğin boyuna üstten tahmin: görüntü, kaplar, kabın sabit alanları."""
    kaplar: int = sum(girdi.sifreli_boy + _GIRDI_PAYI for girdi in girdiler)
    return len(veritabani) + kaplar + _KAP_PAYI


def _yer_denetle(dizin: Path, boy: int) -> None:
    """FAT32 sınırı ve boş yer; okunamayan bilgi engel değildir, yazım denenir (modül başlığı)."""
    if boy > FAT_TEK_DOSYA_SINIRI and fat_mi(dosya_sistemi_turu(dizin)):
        raise EncryptedBackupError(FAT_SINIRI)
    try:
        bos = shutil.disk_usage(dizin).free
    except OSError:
        return
    if bos < boy:
        raise EncryptedBackupError(YER_YOK)


def _ek_saglam_mi(
    girdi: ManifestoGirdisi, depo: Path, key_wrap: str, sarmal_anahtari: bytes
) -> bool:
    """Ek baştan sona okunuyor, sarmalıyla açılıyor ve manifestoyu tutuyor mu?

    `dosya_deposu.oku` kullanılmaz (`geri_yukleme_ekleri` başlığı): bu bir hesabın ek okuması
    değildir, açık içerik burada kalır.
    """
    try:
        ek_denetle(
            girdi, ds.depodan_ac(depo, girdi.ad, key_wrap=key_wrap, sarmal_anahtari=sarmal_anahtari)
        )
    except (ds.DosyaSifrelemeHatasi, EkTutmuyorHatasi, OSError):
        return False
    return True


def _ekleri_on_oku(
    girdiler: Iterable[ManifestoGirdisi],
    depo: Path,
    sarmallar: Mapping[str, str],
    sarmal_anahtari: bytes,
) -> tuple[ManifestoGirdisi, ...]:
    """Her ek bir kez okunur; okunamayan ya da tutmayan ek `eksik` işaretlenir (modül başlığı)."""
    return tuple(
        girdi
        if _ek_saglam_mi(girdi, depo, sarmallar.get(girdi.ad, ""), sarmal_anahtari)
        else replace(girdi, eksik=True)
        for girdi in girdiler
    )


def _yazim_iletisi(hata: OSError) -> str:
    """Ham hatanın kullanıcı iletisi; günlüğe yalnız türü gider (ileti tam yolu taşır; R1)."""
    logger.warning("Şifreli yedek yazılamadı (%s).", type(hata).__name__)
    winerror = getattr(hata, "winerror", None)
    if hata.errno in (errno.ENOSPC, errno.EDQUOT) or winerror in _WIN_YER_YOK:
        return YER_YOK
    if hata.errno == errno.EFBIG or winerror == _WIN_COK_BUYUK:
        return FAT_SINIRI
    return YAZILAMADI


def _onbellegi_birak(akis: IO[bytes]) -> None:
    """POSIX'te dosyanın önbellek sayfalarını bırakır: okuma aygıttan gelir (modül başlığı, 5. adım).

    `tam_yedek_yaz` fsync ettiği için sayfalar temizdir, atılabilir. Bırakılamazsa denetim yine
    koşar; önbellekten okumak denetimsiz kalmaktan iyidir.
    """
    if not hasattr(os, "posix_fadvise"):
        return
    try:
        os.posix_fadvise(akis.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
    except OSError as hata:
        logger.warning("Yedeğin önbellek sayfaları bırakılamadı (%s).", type(hata).__name__)


def _yazilani_denetle(
    gecici: Path,
    veritabani: bytes,
    manifesto: Manifesto,
    dek: bytes,
    sarmallar: Mapping[str, str],
    sarmal_anahtari: bytes,
) -> None:
    """Yazılan dosyayı diskte yeniden açar; tutmazsa `EncryptedBackupError` (modül başlığı)."""
    try:
        with gecici.open("rb") as akis:
            _onbellegi_birak(akis)
            baslik = baslik_oku(akis, os.fstat(akis.fileno()).st_size)
            icerik = muhurlu_bolumu_ac(akis, baslik, dek)
            # Manifesto kapsamıyla karşılaştırılır: yerel kap burada düşer.
            if icerik.manifesto != manifesto or icerik.veritabani != veritabani:
                raise BackupCryptoError(DENETIM_DUSTU)
            for bolum in dosya_bolumunu_oku(akis, icerik.manifesto):
                ad = bolum.girdi.ad
                anahtar = ds.anahtari_ac(
                    sarmallar.get(ad, ""), sarmal_anahtari=sarmal_anahtari, stored_name=ad
                )
                kap = b"".join(bolum.parcalar())
                ek_denetle(bolum.girdi, ds.coz(kap, dosya_anahtari=anahtar, stored_name=ad))
    except (BackupCryptoError, ds.DosyaSifrelemeHatasi, OSError) as hata:
        logger.warning("Yazılan şifreli yedek denetimden geçmedi (%s).", type(hata).__name__)
        raise EncryptedBackupError(DENETIM_DUSTU) from None


def _satiri_yaz(kimlik: str, boyut: int, manifesto: Manifesto, eksik: int) -> None:
    """`YEDEK` satırı (tasarım §4.6.3): kendi işleminde, kişisiz değerlerle."""
    degerler = {
        "kapsam": (None, KAPSAM_KODLARI[KAPSAM_TAM]),
        "dosya_sayisi": (None, len(manifesto.tasinanlar)),
        "boyut": (None, boyut),
        "eksik": (None, eksik),
    }
    with transaction.atomic():
        denetim_izi.olay(
            AuditAction.YEDEK,
            model=denetim_izi.YEDEK_DOSYASI,
            object_id=kimlik,
            changed_fields=sorted(degerler),
            values=degerler,
        )


def _asil_adi_ver(gecici: Path, hedef: Path) -> None:
    try:
        os.replace(gecici, hedef)
    except OSError as hata:
        logger.warning("Şifreli yedeğe asıl adı verilemedi (%s).", type(hata).__name__)
        raise EncryptedBackupError(ASIL_AD_VERILEMEDI) from None
    try:
        ds.dizini_esitle(hedef.parent)
    except OSError as hata:  # dosya asıl adındadır; yedek bu yüzden düşmez
        logger.warning("Yedeğin dizini eşitlenemedi (%s).", type(hata).__name__)


def _gecici_sil(gecici: Path) -> None:
    try:
        gecici.unlink(missing_ok=True)
    except OSError as hata:
        logger.warning("Şifreli yedeğin geçici dosyası silinemedi (%s).", type(hata).__name__)


def _kaydet(hedef: Path) -> KayitSonucu:
    """Modül başlığındaki 3-7. adımlar; kilit, yetki, hedef ve kapılar çağıranındır."""
    data_dir = app_password.state_path().parent
    database_path = Path(str(settings.DATABASES["default"]["NAME"]))
    if not database_path.is_file():
        raise EncryptedBackupError(VERITABANI_YOK)
    baslik = usable_recovery_header(data_dir)
    if baslik is None:
        raise EncryptedBackupError(GUVENLIK_DOSYASI_OKUNAMIYOR)
    dek = crypto.active_key()
    if dek is None:
        raise crypto.KeyMissingError("Şifreli yedek için veri anahtarı bellekte değil.")

    try:
        public_key = load_public_key(data_dir)
        veritabani, goruntu_manifestosu = goruntu_ve_manifesto(database_path)
    except BackupCryptoError as hata:
        raise EncryptedBackupError(str(hata)) from None
    except (OSError, sqlite3.Error) as hata:
        logger.warning("Veritabanı görüntüsü alınamadı (%s).", type(hata).__name__)
        raise EncryptedBackupError(OLUSTURULAMADI) from None

    _yer_denetle(hedef.parent, _tahmini_boy(veritabani, goruntu_manifestosu.dosyalar))

    depo = dosya_deposu.depo_dizini()
    sarmal_anahtari = crypto.file_wrap_key(dek)
    sarmallar = dict(
        Attachment.objects.filter(purged_at__isnull=True).values_list("stored_name", "key_wrap")
    )
    girdiler = _ekleri_on_oku(goruntu_manifestosu.dosyalar, depo, sarmallar, sarmal_anahtari)

    gecici = hedef.parent / f"{AD_ONEKI}-{secrets.token_hex(8)}{GECICI_EK}"
    try:
        try:
            manifesto = tam_yedek_yaz(
                gecici, veritabani, girdiler, depo, public_key, recovery_header=baslik
            )
            boyut = gecici.stat().st_size
        except OSError as hata:
            raise EncryptedBackupError(_yazim_iletisi(hata)) from None
        except BackupCryptoError as hata:
            raise EncryptedBackupError(str(hata)) from None
        _yazilani_denetle(gecici, veritabani, manifesto, dek, sarmallar, sarmal_anahtari)
        eksik = len(manifesto.dosyalar) - len(manifesto.tasinanlar)
        kimlik = _yedek_kimligi(hedef)
        _satiri_yaz(kimlik, boyut, manifesto, eksik)
        _asil_adi_ver(gecici, hedef)
    finally:
        _gecici_sil(gecici)

    # Tasarım §16 R6: hatırlatmanın saati ancak dosya asıl adını aldıktan sonra sıfırlanır.
    # Kayıt veri dizinindeki dosyadadır ve hata yükseltmez (`dis_yedek` modül başlığı).
    dis_yedek.indirme_kaydet()
    if eksik:
        logger.warning("Şifreli yedeğe %d ek giremedi; yedek onlarsız alındı.", eksik)
    logger.info("Şifreli yedek kaydedildi: %d ek.", len(manifesto.tasinanlar))
    return KayitSonucu(ad=kimlik, boyut=boyut, ek_sayisi=len(manifesto.tasinanlar), eksik=eksik)


def sifreli_yedegi_kaydet(hedef: str) -> KayitSonucu:
    """Tam yedeği seçilen yola kaydeder (modül başlığı "SIRA"); yanıtın özetini döndürür."""
    with bakim.UZUN_ISLER.is_():
        _kilit_ve_yetki()
        yol = _hedef_denetle(hedef)
        if not _TEK_IS.acquire(blocking=False):
            raise YedekSuruyor
        try:
            with bakim.KAPI.is_() as izin:
                if not izin:
                    raise BakimSuruyor
                return _kaydet(yol)
        finally:
            _TEK_IS.release()
