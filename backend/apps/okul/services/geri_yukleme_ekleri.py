"""Geri yüklemede dosya deposu: eklerin denetimi, yerleşimi, kişisiz raporu (tasarım §4.4.7).

Plan F1b-3 "Geri yükleme" ve kullanıcı kararları (04.11.2026 "Bozuk ekte geri yükleme durur, ikinci
onayla sürer", "Eksik ve bozuk ekler kişisiz bilgiyle listelenir"; 05.11.2026 "Yedek alınırken bozuk
olan ek eksik sayılır"). Sırayı çekirdek kurar (`backup_restore`); bu modül onun dosya ayağıdır.
Çekirdek gibi ORM kullanmaz, veritabanı bozuk olabilir: ek satırları geri yüklenecek `.tmp`'den ham
SQL ile okunur, hiçbir alanın şifresi çözülmez. Dosya anahtarı DEK'ten türeyen sarmal anahtarıyla
açılır, DEK yedeği açarken elde edilmiştir. Doğrulama `ds.depodan_ac` ve `ds.acik_ozet`'le yapılır;
`dosya_deposu.oku` kullanılmaz: özel nitelikli ekte `SISTEM` okuması reddedilir, hesapla okuma
erişim günlüğüne satır yazardı.

DOĞRULANMAMIŞ HİÇBİR BAYT DEPOYA GİRMEZ. Bir kopya ancak iki koşulla tutar: satırındaki sarmalla
açılır ve açık içeriği hem satırın (`size`, `sha256`) hem manifesto girdisinin özetini verir.
`dosya_deposu.oku` satırın özetine bakar; manifesto tutup satır tutmasaydı dosya yerine konur, sonra
açılmazdı.

İKİ AŞAMA. `hazirla` hiçbir kalıcı dosyaya dokunmaz: tam yedekte dosya bölümü hazırlık dizinine akar,
girdi girdi denetlenir; depodaki ve `yetim/`'deki kopyalar yalnız okunur. Bozuk ek varsa çekirdek bu
noktada durur, hazırlık dizini silinince hiçbir şey değişmemiş olur. `yerine_koy` bütün değişikliği
yapar; her adım bir taşımadır, `geri_al` taşımaları ters sırayla geri çevirir. Takas olunca çekirdek
`kesinlestir`'i çağırır: artık geri alınacak bir şey yoktur. Geçiş günlüğü tutulmaz: süreç öldürülürse
takas yapılmamıştır, depoya konanlar yalnız satırsız dosya kalır.

KAPSAMA GÖRE KARAR.

* Tam yedek, `eksik` işaretli girdi: yedek alınırken bulunamamış ya da bozuk bulunmuştur; **eksik**
  sayılır, durdurmaz, depoya ve `yetim/`'e bakılmaz.
* Tam yedek, doğrulanan girdi: depoda yoksa yerine konur. Depoda aynı adla duran kopya tutuyorsa
  dokunulmaz, tutmuyorsa o kopya `yetim/`'e alınır, yerine doğrulanmış kopya konur (kopyanın içeriği
  satırındaki özetle tanımlıdır).
* Tam yedek, tutmayan girdi: **bozuk**. Depodaki kopyaya dokunulmaz.
* Yerel yedek: manifestodaki ek depoda aranır, yoksa `yetim/`'de (en yeni gün önce). Depodaki kopya
  tutmuyorsa dokunulmaz, **bozuk** sayılır. Yetimde tutan kopya geri alınır; yalnız tutmayan kopya
  varsa ona da dokunulmaz, **bozuk** sayılır. Hiçbir yerde yoksa **eksik**. Sıra ekli yetim kopyası
  (`<ad>-<n>`) da aranır: kabın adı yolun yanında şifrenin ve sarmalın bağıdır, kopya bu yüzden
  hazırlık dizinine asıl adıyla alınıp orada sınanır, depoya oradan girer; yetimdeki aslına dokunulmaz.

MANİFESTO VE SATIR AYRIŞIRSA. İkisi aynı mühürdedir, program ayrışmış yedek üretmez; ayrışma yazıcı
hatası ya da açık yedek anahtarıyla kurulmuş kaptır (`backup_crypto` kalan risk). Kural:

* Manifestoda olup canlı satırı olmayan ek doğrulanamaz: sarmalı yoktur. `eksik` işaretli değilse
  **bozuk** sayılır, depoya girmez. Listede satırın alanları boştur, boy manifestodandır.
* Manifesto ve satırın özeti ya da boyu ayrı ise kopya ikisini birden tutamaz: **bozuk**.
* Satırı olup manifestoda olmayan ek kapsamdan bağımsız yerel yedekteki gibi aranır; dosya bölümünde
  kopyası yoktur. Adı desene uymayan satır yol kurmaz, **eksik** sayılır.

KİŞİSİZ RAPOR (`DosyaRaporu`): sayılar ve her eksik ya da bozuk ek için kayıt türü ve numarası, yükleme
günü, boy. Özgün ad hiç okunmaz. Liste geri yükleme ekranına ve konsola gider; geri yükleme notuna ve
denetim izine yalnız sayılar geçer (`sayilar`). Asıl dosya adı yalnız program açıkken görünür.
Manifestoda `eksik` işaretli ek `yedekte_yoktu` taşır, satırı "yedek alınırken bulunamadı ya da
bozuktu" der (05.11.2026); iki hâl ayrı sayılmaz, yedek biçimine işaret gelmez.

Bu modül depo adını, özgün adı ve yolu günlüğe yazmaz.
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import IO, Any, Final

from desktop.backup import EK_TABLOSU
from desktop.backup_crypto import (
    KAPSAM_TAM,
    KAPSAM_YEREL,
    EkTutmuyorHatasi,
    Manifesto,
    ManifestoGirdisi,
    dosya_bolumunu_oku,
    ek_denetle,
)
from django.apps import apps
from django.utils import timezone

from shared import crypto, sqlite_adres
from shared import dosya_sifreleme as ds

logger = logging.getLogger("oab_defteri.restore")

EKSIK: Final = "eksik"
BOZUK: Final = "bozuk"
#: Kapsamın notta, iz satırında ve yanıtta görünen kodu.
KAPSAM_KODLARI: Final[dict[int, str]] = {KAPSAM_YEREL: "yerel", KAPSAM_TAM: "tam"}
#: Satırı bulunamayan ekin kayıt türü (modül başlığı "MANİFESTO VE SATIR AYRIŞIRSA").
KAYDI_BULUNAMADI: Final = "Kaydı bulunamadı"

_DURUM_ADLARI: Final[dict[str, str]] = {EKSIK: "Eksik", BOZUK: "Bozuk"}
#: Manifestoda `eksik` işaretli ekin durumuna eklenen açıklama (modül başlığı "KİŞİSİZ RAPOR").
_YEDEKTE_YOKTU: Final = "yedek alınırken bulunamadı ya da bozuktu"
#: Kaydı olmayan kayıt türü: ekin bağlı olduğu model artık tanınmıyor.
_BILINMEYEN_TUR: Final = "Kayıt"


class EkKayitlariOkunamadi(ValueError):
    """Yedek çözüldü ama eklerin kayıtları okunamadı: yedeğin kendisi bozuk, onayla sürmez."""

    def __init__(self) -> None:
        super().__init__("Yedek çözüldü ama eklerin kayıtları okunamadı; dosya bozulmuş olabilir.")


@dataclass(frozen=True)
class EkSatiri:
    """Eksik ya da bozuk bir ekin kişisiz satırı (modül başlığı "KİŞİSİZ RAPOR").

    `yukleme_tarihi` yerel günün ISO biçimidir; arayüz gg.aa.yyyy yazar. `yedekte_yoktu`: ek yedeğin
    kendisinde yoktu, yani bu geri yüklemede kaybolmadı.
    """

    durum: str
    kayit_turu: str
    kayit_no: str
    yukleme_tarihi: str | None
    boyut: int
    yedekte_yoktu: bool = False

    def metin(self) -> str:
        """Konsolun satırı: tarih kâğıttaki biçimiyle, boy en az 1 KB."""
        gun = (
            date.fromisoformat(self.yukleme_tarihi).strftime("%d.%m.%Y")
            if self.yukleme_tarihi is not None
            else "tarih yok"
        )
        durum = _DURUM_ADLARI[self.durum]
        if self.yedekte_yoktu:
            durum = f"{durum} ({_YEDEKTE_YOKTU})"
        parcalar = [durum, self.kayit_turu]
        if self.kayit_no:
            parcalar.append(f"no {self.kayit_no}")
        parcalar += [gun, f"{max(1, self.boyut // 1024)} KB"]
        return " · ".join(parcalar)


@dataclass(frozen=True)
class DosyaRaporu:
    """Bir geri yüklemenin dosya ayağının sonucu (modül başlığı "KİŞİSİZ RAPOR").

    `onayla_suruldu`: ikinci onayla geride bırakılan ek sayısı (plan: "onay ... sayı olarak").
    """

    kapsam: str
    yerine_konan: int = 0
    yetimden_donen: int = 0
    onayla_suruldu: int = 0
    ekler: tuple[EkSatiri, ...] = ()

    def _sayi(self, durum: str) -> int:
        return sum(satir.durum == durum for satir in self.ekler)

    @property
    def eksik(self) -> int:
        return self._sayi(EKSIK)

    @property
    def bozuk(self) -> int:
        return self._sayi(BOZUK)

    def sayilar(self) -> dict[str, Any]:
        """Geri yükleme notuna ve `GERI_YUKLEME` satırına geçen kişisiz sayılar."""
        return {
            "kapsam": self.kapsam,
            "yerine_konan": self.yerine_konan,
            "yetimden_donen": self.yetimden_donen,
            "eksik": self.eksik,
            "bozuk": self.bozuk,
            "onayla_suruldu": self.onayla_suruldu,
        }

    def yanit(self) -> dict[str, Any]:
        """Uygulama içi ucun yanıtı: sayılar ve kişisiz liste."""
        return {**self.sayilar(), "ekler": [asdict(satir) for satir in self.ekler]}

    def metin_satirlari(self) -> list[str]:
        """Konsolun listesi; ek yoksa boş."""
        return [satir.metin() for satir in self.ekler]


@dataclass(frozen=True)
class _EkKaydi:
    """Geri yüklenecek veritabanının bir ek satırı; alanlar okunduğu gibidir, güvenilmez."""

    stored_name: Any
    key_wrap: Any = field(repr=False)
    size: Any
    sha256: Any
    owner_type: Any
    owner_id: Any
    uploaded_at: Any


def _metin(ham: bytes) -> str:
    """Satır çözme hatası satır düzeyinde kalsın (`desktop.backup` manifesto okuyucusu gibi)."""
    return ham.decode("utf-8", "replace")


def _ek_kayitlari(db: Path, *, zorunlu: bool) -> dict[Any, _EkKaydi]:
    """Canlı ek satırları, depo adıyla; tablo yoksa boş.

    Salt okunur açılır, `.tmp`'nin baytları değişmez. Okuma düşerse manifesto boşken yine boştur
    (`zorunlu` yanlış); manifestoda ek varsa doğrulama yapılamaz, yedek bozuk sayılır.
    """
    adres = sqlite_adres.salt_okunur_adres(db)
    try:
        with closing(sqlite3.connect(adres, uri=True, timeout=5)) as baglanti:
            baglanti.text_factory = _metin
            tablo = baglanti.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (EK_TABLOSU,)
            ).fetchone()
            # İzni `test_dosya_deposu.EK_OKUMA_DIZELERI`'nde, tam metniyle.
            satirlar = (
                []
                if tablo is None
                else baglanti.execute(
                    "SELECT stored_name, key_wrap, size, sha256, owner_type, owner_id, uploaded_at "
                    "FROM okul_attachment WHERE purged_at IS NULL ORDER BY stored_name"
                ).fetchall()
            )
    except sqlite3.Error as exc:
        if zorunlu:
            raise EkKayitlariOkunamadi from exc
        logger.warning("Geri yüklenecek veritabanının ek kayıtları okunamadı.")
        return {}
    return {satir[0]: _EkKaydi(*satir) for satir in satirlar}


def _yerel_gun(ham: object) -> str | None:
    """`uploaded_at`'in ham metni (saat dilimsiz UTC) → yerel gün; biçimsizse None."""
    if not isinstance(ham, str):
        return None
    try:
        an = datetime.fromisoformat(ham)
    except ValueError:
        return None
    if an.tzinfo is None:
        an = an.replace(tzinfo=UTC)
    return timezone.localtime(an).date().isoformat()


def tur_adi(etiket: object) -> str:
    """`owner_type`'ın ekrandaki adı: modelin `verbose_name`'i. Veritabanına gidilmez."""
    try:
        return str(apps.get_model(str(etiket))._meta.verbose_name)
    except (LookupError, ValueError):
        return _BILINMEYEN_TUR


def _ek_satiri(
    durum: str,
    kayit: _EkKaydi | None,
    girdi: ManifestoGirdisi | None,
    *,
    yedekte_yoktu: bool = False,
) -> EkSatiri:
    if kayit is None:
        boyut = girdi.boyut if girdi is not None else 0
        return EkSatiri(durum, KAYDI_BULUNAMADI, "", None, boyut, yedekte_yoktu)
    return EkSatiri(
        durum,
        tur_adi(kayit.owner_type),
        str(kayit.owner_id),
        _yerel_gun(kayit.uploaded_at),
        kayit.size if isinstance(kayit.size, int) else 0,
        yedekte_yoktu,
    )


class EkYerlesimi:
    """Bir geri yüklemenin dosya ayağı: `hazirla` → (`yerine_koy`) → (`geri_al`) → `temizle`.

    `akis` tam yedekte dosya bölümünün başındadır; yerel yedekte okunmaz. `gun` yetim dizininin
    günüdür. Sıra ve kurallar modül başlığındadır.
    """

    def __init__(
        self,
        *,
        depo: Path,
        dek: bytes,
        kapsam: int,
        manifesto: Manifesto,
        akis: IO[bytes],
        gun: date,
    ) -> None:
        self._depo = depo
        self._sarmal_anahtari = crypto.file_wrap_key(dek)
        self._kapsam = kapsam
        self._manifesto = manifesto
        self._akis = akis
        self._gun = gun
        self._hazirlik: Path | None = None
        self._satirlar: list[EkSatiri] = []
        #: Depoda olmayan, yerine konacak doğrulanmış kopyalar (hazırlık dizinindeki yolları).
        self._konacak: list[Path] = []
        #: Depodaki kopyası tutmadığı için onun yerine konacak doğrulanmış kopyalar.
        self._degisecek: list[Path] = []
        #: Yetimden geri alınacak doğrulanmış kopyalar.
        self._donecek: list[Path] = []
        #: Yapılan taşımalar, sırayla: (kaynak, hedef).
        self._tasimalar: list[tuple[Path, Path]] = []
        self._yerine_konan = 0
        self._yetimden_donen = 0

    @property
    def bozuk_var(self) -> bool:
        return any(satir.durum == BOZUK for satir in self._satirlar)

    def rapor(self, *, onaylandi: bool = False) -> DosyaRaporu:
        """Şu anki durumun raporu; `onaylandi`: bozuk ekler ikinci onayla geride bırakıldı."""
        satirlar = tuple(
            sorted(
                self._satirlar,
                key=lambda s: (s.durum, s.kayit_turu, s.kayit_no, s.yukleme_tarihi or "", s.boyut),
            )
        )
        return DosyaRaporu(
            kapsam=KAPSAM_KODLARI[self._kapsam],
            yerine_konan=self._yerine_konan,
            yetimden_donen=self._yetimden_donen,
            onayla_suruldu=sum(s.durum == BOZUK for s in satirlar) if onaylandi else 0,
            ekler=satirlar,
        )

    # ------------------------------------------------------------------ denetim
    def hazirla(self, gecici_db: Path) -> None:
        """Bütün eklerin kararını verir; yalnız hazırlık dizinine yazar (modül başlığı)."""
        kayitlar = _ek_kayitlari(gecici_db, zorunlu=bool(self._manifesto.dosyalar))
        dogrulanan = self._dosya_bolumunu_al(kayitlar) if self._kapsam == KAPSAM_TAM else {}
        for girdi in self._manifesto.dosyalar:
            kayit = kayitlar.get(girdi.ad)
            if self._kapsam == KAPSAM_TAM:
                self._tam_yedekteki(girdi, kayit, dogrulanan)
            elif kayit is None:
                self._satirlar.append(_ek_satiri(BOZUK, None, girdi))
            else:
                self._yerelde_ara(girdi.ad, kayit, girdi)
        manifestodakiler = {girdi.ad for girdi in self._manifesto.dosyalar}
        for ad, kayit in kayitlar.items():
            if ad in manifestodakiler:
                continue
            if not isinstance(ad, str) or ds.DEPO_ADI_DESENI.fullmatch(ad) is None:
                self._satirlar.append(_ek_satiri(EKSIK, kayit, None))
            else:
                self._yerelde_ara(ad, kayit, None)

    def _dosya_bolumunu_al(self, kayitlar: dict[Any, _EkKaydi]) -> dict[str, Path]:
        """Dosya bölümünü hazırlık dizinine akıtır; doğrulanan kopyaları adlarıyla döndürür.

        Bölümün sonuna dek okunur: kesik ya da sırası bozuk bölüm `DosyaBolumuHatasi` verir ve
        bozuk girdilerden önce gelir. Tutmayan kopya dizinle birlikte silinir.
        """
        dogrulanan: dict[str, Path] = {}
        for bolum in dosya_bolumunu_oku(self._akis, self._manifesto):
            girdi = bolum.girdi
            kayit = kayitlar.get(girdi.ad)
            if kayit is None:
                continue  # sarmal yok: doğrulanamaz, gövdeyi okuyucu atlar
            if self._hazirlik is None:
                self._hazirlik = ds.hazirlik_dizini_kur(self._depo)
            yol = self._hazirlik / girdi.ad
            ds.akisla_yaz(yol, bolum.parcalar())
            if self._tutuyor_mu(self._hazirlik, girdi.ad, kayit, girdi):
                dogrulanan[girdi.ad] = yol
        return dogrulanan

    def _tam_yedekteki(
        self, girdi: ManifestoGirdisi, kayit: _EkKaydi | None, dogrulanan: dict[str, Path]
    ) -> None:
        kopya = dogrulanan.get(girdi.ad)
        if girdi.eksik:
            self._satirlar.append(_ek_satiri(EKSIK, kayit, girdi, yedekte_yoktu=True))
        elif kayit is None or kopya is None:
            self._satirlar.append(_ek_satiri(BOZUK, kayit, girdi))
        elif not os.path.lexists(self._depo / girdi.ad):
            self._konacak.append(kopya)
        elif not self._tutuyor_mu(self._depo, girdi.ad, kayit, girdi):
            self._degisecek.append(kopya)

    def _yerelde_ara(self, ad: str, kayit: _EkKaydi, girdi: ManifestoGirdisi | None) -> None:
        if os.path.lexists(self._depo / ad):
            if not self._tutuyor_mu(self._depo, ad, kayit, girdi):
                self._satirlar.append(_ek_satiri(BOZUK, kayit, girdi))
            return
        kopyalar = ds.yetimdeki_kopyalar(self._depo, ad)
        for kopya in kopyalar:
            donecek = self._yetimdeki_tutan(kopya, ad, kayit, girdi)
            if donecek is not None:
                self._donecek.append(donecek)
                return
        self._satirlar.append(_ek_satiri(BOZUK if kopyalar else EKSIK, kayit, girdi))

    def _yetimdeki_tutan(
        self, kopya: Path, ad: str, kayit: _EkKaydi, girdi: ManifestoGirdisi | None
    ) -> Path | None:
        """Kopya tutuyorsa depoya taşınacak yolu; sıra ekli kopya hazırlıktan sınanır (modül başlığı).

        Açılamayan sıra ekli kopya tutmuyordur; hazırlığa yazılamazsa `OSError` çağırana gider.
        """
        if kopya.name == ad:
            return kopya if self._tutuyor_mu(kopya.parent, ad, kayit, girdi) else None
        try:
            kap = ds.kabi_oku(kopya)
        except (ds.DosyaSifrelemeHatasi, OSError):
            return None
        if self._hazirlik is None:
            self._hazirlik = ds.hazirlik_dizini_kur(self._depo)
        yol = self._hazirlik / ad
        yol.unlink(missing_ok=True)  # aynı adın önceki sıra ekli adayı tutmamıştır
        ds.akisla_yaz(yol, (kap,))
        return yol if self._tutuyor_mu(self._hazirlik, ad, kayit, girdi) else None

    def _tutuyor_mu(
        self, dizin: Path, ad: str, kayit: _EkKaydi, girdi: ManifestoGirdisi | None
    ) -> bool:
        """Kopya satırın sarmalıyla açılıyor, satırın ve manifestonun özetini veriyor mu?

        Açılamayan kopya (düzenli dosya değil, okunamıyor, bozuk kap ya da sarmal) tutmuyordur.
        """
        try:
            acik = ds.depodan_ac(
                dizin, ad, key_wrap=kayit.key_wrap, sarmal_anahtari=self._sarmal_anahtari
            )
            if girdi is not None:
                ek_denetle(girdi, acik)
        except (ds.DosyaSifrelemeHatasi, EkTutmuyorHatasi, OSError):
            return False
        return bool(len(acik) == kayit.size and ds.acik_ozet(acik) == kayit.sha256)

    # ------------------------------------------------------------------ yerleşim
    def _depoya_tasi(self, kopya: Path) -> None:
        hedef = self._depo / kopya.name
        ds.yerine_tasi(kopya, hedef)
        self._tasimalar.append((kopya, hedef))

    def yerine_koy(self) -> None:
        """Kararları uygular; düşerse yapılanları çağıran `geri_al` ile çevirir (modül başlığı)."""
        if self._konacak or self._degisecek or self._donecek:
            ds.dizin_kur(self._depo)
        for kopya in self._degisecek:
            yetimde = ds.yetime_tasi(self._depo, kopya.name, self._gun)
            self._tasimalar.append((self._depo / kopya.name, yetimde))
        for kopya in (*self._degisecek, *self._konacak):
            self._depoya_tasi(kopya)
        for kopya in self._donecek:
            self._depoya_tasi(kopya)
        self._yerine_konan = len(self._degisecek) + len(self._konacak)
        self._yetimden_donen = len(self._donecek)

    def kesinlestir(self) -> None:
        """Takas oldu: yerleşim kesindir, `geri_al` artık hiçbir dosyayı çevirmez."""
        self._tasimalar.clear()

    def geri_al(self) -> None:
        """Bu geri yüklemenin taşımalarını ters sırayla çevirir. Hata yükseltmez.

        Çevrilemeyen dosya yalnız satırsız kalır, açılış taraması toplar (modül başlığı "İKİ AŞAMA").
        """
        while self._tasimalar:
            kaynak, hedef = self._tasimalar.pop()
            try:
                os.replace(hedef, kaynak)
            except OSError:
                logger.warning("Geri yüklemenin yerleştirdiği bir ek geri alınamadı.")

    def temizle(self) -> None:
        """Hazırlık dizinini siler; silinemezse açılış temizliği toplar. Hata yükseltmez."""
        if self._hazirlik is not None:
            shutil.rmtree(self._hazirlik, ignore_errors=True)
            self._hazirlik = None
