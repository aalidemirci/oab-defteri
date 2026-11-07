"""Masaüstü kancaları — backend ile masaüstü kabuğu arasındaki TEK kanal (tasarım §4.1).

Program tek süreçtir: Django (yönetim API'si) ve masaüstü kabuğunun iş
parçacıkları (`od-gunluk`, `od-kanal`) aynı süreçte koşar. Backend masaüstüne
bir HTTP ucuyla değil, masaüstü kabuğunun açılışta buraya KAYDETTİĞİ nesnelerle
ulaşır (tasarım §4.1). Böylece ikinci bir durum kaynağı ya da tanımsız bir
kontrol kanalı doğmaz:

* **Çıkış** (`POST app/quit/`, `views_app.py`): düzenli kapanışı başlatan
  çağrılabilir; masaüstünde pencere denetçisinin `request_quit` yoludur
  (pencerenin çarpısı, tek kopya kanalı ve kurucunun kapatma olayıyla aynı yol).
* **Gün değişimi işleri** (T9): backend'deki bir işin masaüstünün `od-gunluk`
  kapısına girmesi için buraya kaydolması yeter; kapı açılışta bu listeyi okur.
  Masaüstü modüllerini backend'den içe aktarmak gerekmez. Kayıtlı iş yazar bağlamı
  `SISTEM` ile koşar (denetim izi; plan F1b-1: gün işi `SISTEM`'i açıkça verir). DEK
  isteyen iş kilitliyken `KeyMissingError` ile düşerse ERTELENMİŞ sayılır: `GUN_ISI` satırı
  iş başına günde en çok bir kez yazılır (kilitli kipte; `iz_durumu.gun_isi_ertelendi`),
  iş veritabanına hiçbir şey yazmamıştır (işlemi geri sarılır) ve yeniden denenir.
* **Ertelenenleri şimdi dene** (TK19: "ilk kilit açılışında koşar"; tasarım §4.4.3 kilit
  açılışı sırasının son adımı): masaüstü kabuğu `od-gunluk` kapısını başlatınca kapının
  sinyalini kaydeder (`kaydet(ertelenenleri_dene=…)`); kilit açılışı oturum açıldıktan ve
  kilitleri bıraktıktan SONRA çağırır (`ertelenen_gun_islerini_dene`;
  `app_password._start_session`). Kanca ENGELLEMEZ: yalnız kapıyı uyandırır, iş `od-gunluk`
  iş parçacığında, bakım kapısından geçerek koşar; isteğin iş parçacığında uzun iş
  koşmaz. Tetiklenen iş düşerse saatlik deneme sürer (kapının takvimi kaymaz).
* **Sistem olayları** (tasarım §4.2 adım 7-8, §4.6.3; plan F1b-1 "Açılıştaki YEDEK ve GOC
  olayları göçten sonra `masaustu_kanca` üzerinden yazılır"): açılıştaki günlük yedek ve
  göç öncesi yedek Django ve tablo hazır olmadan alınır, göç tabloyu kurar. Masaüstü kabuğu
  olguları tamponlar ve göçten SONRA buraya verir (`yedek_olaylarini_yaz`,
  `goc_olayini_yaz`); `od-gunluk`'un günlük yedeği de aynı kapıdan geçer. Satırı kip seçen
  yazıcı yazar (`iz_durumu.sistem_olayi`: oturum açıksa açık, değilse kilitli kip). Bu
  işlevler HATA YÜKSELTMEZ: denetim izinin yazılamaması açılışı ve yedeği durdurmaz, olay
  günlüğe düşer (kilitli kipte ilk hesaptan önce olay yazılmaz).
* **Yetim taraması** (`yetim_taramasi`; tasarım §4.4.7 "Yetim ve eksik dosya", plan F1b-3 "Geri
  yükleme"): masaüstü kabuğu her açılışta göçten sonra, sunucudan önce çağırır. Satırı olmayan
  dosyayı `dosyalar/yetim/<yyyy-aa-gg>/`'e taşır. Eski bir yedeğin geri yüklenmesinden, yarım kalmış
  bir geri yüklemeden ya da kaydı düşmüş bir ek yazımından kalır. KORUMA: tarama veritabanının bu
  deponun sahibi olduğunu kanıtlamadan dosyaya dokunmaz. Okul kartı tek satır değilse, parmak izi
  boşsa ya da tablolar okunamıyorsa atlanır: boş veritabanı bütün depoyu yetime gönderirdi, 14 gün
  sonra da silerdi (takasın ortasında öldürülen geri yüklemeden sonra göç böyle bir veritabanı
  kurar). Okuma ham SQL'ledir, salt okunurdur, DEK istemez; iki sorgu da yalnız açık sütun okur.
  Satırı olan her ad yerinde kalır: `purged_at` dolu satır da satırdır, imhanın dosyası imhanın
  işidir (F4-F6), tarama onu ayrıca ele almaz. Yalnız desene uyan düzenli dosyalara dokunulur
  (`dosya_sifreleme.depodaki_dosyalar`). Olay `BUTUNLUK` satırıdır (`DOSYA_DEPOSU`; sayılar, ad yok);
  bir dosya bile taşınmadıysa satır yazılmaz. Geri yükleme notu varken olay nota düşer
  (`iz_durumu`). Hata yükseltmez; tek dosyanın taşınamaması taramayı durdurmaz.
* **Artık temizliği** (`artiklari_temizle`; plan F1b-3 "Geri yükleme"): yarım kalmış işlerin geçici
  dosyaları açılışta silinir: `db.sqlite3.yeni.tmp` ve eşleri, `.geri-yukleme-denetimi-*`,
  `.yukleme-*.tmp`, `*.odbak.tmp`, `dosyalar/<stored_name>.tmp`, hazırlık dizinleri ve `serialize`
  olmayan SQLite'ın görüntü dizini (`.yedek-goruntusu-*`; içinde düz görüntü durur). Yalnız bu adlara
  ve beklenen türe (dosya ya da dizin) dokunulur, yol ve ad günlüğe yazılmaz (`*.odbak.tmp`'nin adı
  serbest olabilir; R1). Çağıran tek kopya kilidini tutar: başka bir kopya ya da geri yükleme
  sürerken bu adlar artık değildir. `--geri-yukle` de kendi kilidi altında çağırır: veritabanı
  bozukken program açılmaz, artık başka türlü silinmezdi. Hata yükseltmez.
* **Kapanış kilidi** (ters yön; tasarım §4.2 kapanış sırası, plan F1b-1 "Oturum"):
  backend `OkulConfig.ready` içinde oturumun kapanış kilidini KAYDEDER
  (`kapanis_kilidi_kaydet`), masaüstü kabuğu düzenli kapanışta `od-gunluk` durduktan
  sonra, yönetim sunucusu durmadan önce ÇAĞIRIR (`kapanista_kilitle`). Masaüstü
  oturum modülünü içe aktarmaz; kilit `KILIT` satırını ve çapayı (`iz-durumu.json`)
  yazar. Bu kayıt `kaldir()` ile düşmez: backend'in kendi kaydıdır. Kapanışın kaynağı bu
  kanaldan backend'e geçmez (`request_quit` tektir): satırın yazarını yalnız arayüzdeki
  Çık'ın isteği belirler (`views_app`, `apps.okul.oturum` "KİLİDİN İZİ").
* **Kilitli yazım düşerse** (tohum ilerledi, satır yazılmadı) sonraki sistem olayları ilk
  kilit açılışına dek bellekte bekler (`iz_durumu`): boşluk sonda kalır, kesinti sayılır.
  Bekleyen olay yazılan satır sayılmaz (0 ya da False); süreç kilit açılmadan biterse
  yalnız günlükte kalır.

Geri yükleme ile gün işlerinin dışlaşması bu kanaldan değil, ortak bakım
kapısından (`shared/bakim.py`) geçer.

Kanca yoksa (geliştirme sunucusu, testler, konsol) işlevler "yok" der; çağıran uç bunu
kullanıcıya Türkçe iletiyle bildirir (ör. 503), kilit açılışının sinyali etkisiz kalır.
Kayıt süreç içidir ve açılışta bir kez yapılır; `_reset_for_tests` yalnız testler içindir.
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import stat
import threading
from collections.abc import Callable, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

logger = logging.getLogger("oab_defteri.okul")

GunlukIs = Callable[[], bool | None]

#: Denetim izinin `object_id` sütununun sınırı (dosya adı daha uzunsa kırpılır).
_KIMLIK_SINIRI = 64
#: Yetim taramasının `BUTUNLUK` satırının kimliği (kişisiz sabit).
_YETIM_KIMLIGI: Final = "yetim"


@dataclass(frozen=True)
class GunlukIsKaydi:
    """Gün değişimi kapısına backend'den kaydolan iş (T9)."""

    ad: str
    calistir: GunlukIs


_kilit = threading.Lock()
_cikis: Callable[[], None] | None = None
_ertelenenleri_dene: Callable[[], None] | None = None
_gunluk_isler: dict[str, GunlukIsKaydi] = {}
_kapanis_kilidi: Callable[[], bool] | None = None


def kaydet(
    *,
    cikis: Callable[[], None] | None = None,
    ertelenenleri_dene: Callable[[], None] | None = None,
) -> None:
    """Masaüstü kabuğu açılışta kancalarını kaydeder (verilmeyen kanca değişmez).

    Kayıt iki çağrıdır: `serve` kapının sinyalini, ardından `run_window_session` çıkış
    kancasını kaydeder; ikincisi birincisini silmemelidir (sıranın taklitsiz testi
    `test_erisim_gunlugu.py`'de).
    """
    global _cikis, _ertelenenleri_dene
    with _kilit:
        if cikis is not None:
            _cikis = cikis
        if ertelenenleri_dene is not None:
            _ertelenenleri_dene = ertelenenleri_dene


def kaldir() -> None:
    """Kapanışta kancaları bırakır: kapanan sunucuya ve duran kapıya istek yönlendirilmez."""
    global _cikis, _ertelenenleri_dene
    with _kilit:
        _cikis = None
        _ertelenenleri_dene = None


def cikis_iste() -> bool:
    """Düzenli kapanışı başlatır; kanca yoksa `False` (masaüstü dışında çalışıyor).

    Kanca ENGELLEMEZ: kapanış ayrı bir iş parçacığında sürer, bu çağrıyı yapan
    HTTP isteği yanıtını gönderebilir.
    """
    with _kilit:
        cikis = _cikis
    if cikis is None:
        return False
    cikis()
    return True


def ertelenen_gun_islerini_dene() -> bool:
    """Kilit açılışı çağırır: `od-gunluk` günü eskiyen işleri hemen denesin; kanca yoksa False.

    ENGELLEMEZ ve HATA YÜKSELTMEZ (modül başlığı "Ertelenenleri şimdi dene"): kanca yalnız
    kapıya sinyal verir; sinyal verilemese de kilit açılışı düşmez, iş saatlik denemede koşar.
    Kilit açılışı bunu kilitlerini (`_state_lock`, `IZ_KIP_KILIDI`) bıraktıktan sonra
    çağırır: iş o kilitleri kendi iş parçacığında alır.
    """
    with _kilit:
        dene = _ertelenenleri_dene
    if dene is None:
        return False
    try:
        dene()
    except Exception:  # noqa: BLE001 — sinyal düşse de iş saatlik denemede koşar
        logger.warning("Ertelenen gün işleri için kapıya sinyal verilemedi.", exc_info=True)
        return False
    return True


def _sistem_adina(ad: str, calistir: GunlukIs) -> GunlukIs:
    """İşi yazar bağlamı `SISTEM` olarak koşturur; DEK yoksa ertelenmiş sayar (modül başlığı).

    Gün işi kullanıcı eylemi değildir: yazdığı iz satırının yazarı `SISTEM`'dir ve bu
    açıkça verilir. `od-gunluk` iş parçacığının bağlam değişkeni boş başlar; sarmalayıcı
    olmasaydı yazıcı yazarsız yazmayı reddederdi. İş `KeyMissingError` ile düşerse (kilitli:
    DEK ya da İA bellekte değil) `GUN_ISI` satırı günde bir kez yazılır ve False döner (kilit
    açılışının sinyalinde ya da bir saat sonra yeniden). Oturum ve kripto modülleri çağrı
    anında içe aktarılır: bu modül masaüstünden Django kurulmadan da içe aktarılabilir kalır.
    """

    def kos() -> bool | None:
        from apps.okul.oturum import sistem_olarak
        from shared.crypto import KeyMissingError

        with sistem_olarak():
            try:
                return calistir()
            except KeyMissingError:
                logger.info("Gün işi kilitli olduğu için ertelendi: %s", ad)
                _gun_isi_ertelendi(ad)
                return False

    return kos


def _gun_isi_ertelendi(ad: str) -> None:
    """Ertelenen gün işinin `GUN_ISI` satırı (iş başına günde bir); hata yükseltmez."""
    try:
        from apps.okul import iz_durumu

        iz_durumu.gun_isi_ertelendi(ad)
    except Exception:  # noqa: BLE001 — iz yazılamasa da iş bir saat sonra yeniden denenir
        logger.warning("Gün işinin ertelenmesi denetim izine yazılamadı (%s).", ad, exc_info=True)


def gunluk_is_kaydet(ad: str, calistir: GunlukIs) -> None:
    """Gün değişimi kapısına iş kaydeder (T9). Aynı adla ikinci kayıt öncekinin yerine geçer.

    İş günde bir kez, kapının `od-gunluk` iş parçacığında koşar. `True` ya da
    `None` dönerse o günün işi yapılmış sayılır; `False` dönerse ya da istisna
    yükseltirse bir saat sonra yeniden denenir. İş kendi veritabanı
    bağlantısını `finally` içinde kapatmakla yükümlü değildir: kapı her işten
    sonra iş parçacığının bağlantılarını kapatır. İş yazar bağlamı `SISTEM` ile koşar
    (`_sistem_adina`): yazdığı her şey denetim izine programın işi olarak düşer.
    """
    if not ad or not ad.isascii():
        raise ValueError("Gün değişimi işinin adı ASCII ve boş olmayan bir dize olmalı.")
    with _kilit:
        _gunluk_isler[ad] = GunlukIsKaydi(ad=ad, calistir=_sistem_adina(ad, calistir))


def gunluk_isler() -> tuple[GunlukIsKaydi, ...]:
    """Kayıtlı gün değişimi işleri (kayıt sırasıyla)."""
    with _kilit:
        return tuple(_gunluk_isler.values())


def yedek_olaylarini_yaz(*, alinan: Sequence[str] = (), silinen: Sequence[str] = ()) -> int:
    """Yedek olguları → `YEDEK` satırları (alındı; rotasyonla silindi). Hata yükseltmez.

    Kimlik yedeğin dosya adıdır — YALNIZ programın ürettiği, zaman damgalı adsa; rotasyonun
    sildiği elle konmuş ya da yeniden adlandırılmış dosyanın adı satıra girmez, olay boş
    kimlikle yazılır (`denetim_izi.yedek_kimligi`, kapıda: `iz_durumu._olay_kaydi`). Silinen
    yedeğin satırı `changed_fields = ["silindi"]` taşır. Denetim izine yazılan satır sayısını
    döndürür (ilk hesaptan önce yazılmayan ya da geri yükleme notuna bırakılan olay sayılmaz).
    Masaüstü kabuğu açılışta göçten sonra ve `od-gunluk`'un günlük yedeğinden sonra çağırır
    (modül başlığı "Sistem olayları").
    """
    olaylar = [(ad, ()) for ad in alinan] + [(ad, ("silindi",)) for ad in silinen]
    yazilan = 0
    for ad, alanlar in olaylar:
        try:
            from apps.okul import denetim_izi, iz_durumu
            from apps.okul.models import AuditAction

            satir = iz_durumu.sistem_olayi(
                AuditAction.YEDEK,
                model=denetim_izi.YEDEK_DOSYASI,
                object_id=denetim_izi.yedek_kimligi(ad),
                changed_fields=alanlar,
            )
            if satir is not None:
                yazilan += 1
        except Exception:  # noqa: BLE001 — yedek ve açılış iz yüzünden durmaz
            # Dosyanın adı günlüğe de yazılmaz: elle konmuş dosyanın adı serbest metindir (R1).
            logger.warning("Yedek olayı denetim izine yazılamadı.", exc_info=True)
    return yazilan


def goc_olayini_yaz(*, surum: str, gocler: Sequence[str]) -> bool:
    """Uygulanan şema göçleri → TEK `GOC` satırı (tasarım §4.2 adım 8). Hata yükseltmez.

    Kimlik programın sürümüdür, değer uygulanan göçlerin adlarıdır (`uygulama.ad`; kişisiz
    kod). Göç yoksa satır yoktur. Satır yazıldıysa True (ilk hesaptan önce ya da geri yükleme
    notu varken False: olay yazılmadı ya da nota bırakıldı).
    """
    if not gocler:
        return False
    try:
        from apps.okul import denetim_izi, iz_durumu
        from apps.okul.models import AuditAction

        satir = iz_durumu.sistem_olayi(
            AuditAction.GOC,
            model=denetim_izi.SEMA_GOCU,
            object_id=str(surum)[:_KIMLIK_SINIRI],
            changed_fields=("gocler",),
            values={"gocler": (None, [str(goc) for goc in gocler])},
        )
    except Exception:  # noqa: BLE001 — açılış iz yüzünden durmaz
        logger.warning("Şema göçü denetim izine yazılamadı.", exc_info=True)
        return False
    return satir is not None


def _kayitli_ek_adlari(db_path: Path) -> frozenset[str] | None:
    """Depoyu tanıyan veritabanının bütün ek adları; koruma tutmuyorsa None (modül başlığı).

    Veritabanı yoksa, kilitliyse ya da tablolardan biri okunamıyorsa da None: taranamayan depoya
    dokunulmaz. Metin hoşgörüyle okunur: bozuk bir satır okumayı düşürmez, adı desene uymaz.
    """
    from shared import sqlite_adres

    adres = sqlite_adres.salt_okunur_adres(db_path)
    try:
        with closing(sqlite3.connect(adres, uri=True, timeout=5)) as baglanti:
            baglanti.text_factory = lambda ham: ham.decode("utf-8", "replace")
            kartlar = baglanti.execute(
                "SELECT app_password_hash FROM okul_schoolconfig LIMIT 2"
            ).fetchall()
            if len(kartlar) != 1 or not str(kartlar[0][0] or "").strip():
                logger.info("Dosya deposu taranmadı: okul kartı ya da parmak izi yok.")
                return None
            # İzni `test_dosya_deposu.EK_OKUMA_DIZELERI`'nde, tam metniyle.
            satirlar = baglanti.execute("SELECT stored_name FROM okul_attachment").fetchall()
    except sqlite3.Error as hata:
        logger.warning("Dosya deposu taranmadı: veritabanı okunamadı (%s).", type(hata).__name__)
        return None
    return frozenset(satir[0] for satir in satirlar)


def _yetim_olayini_yaz(*, tasinan: int, tasinamayan: int) -> None:
    """Taramanın `BUTUNLUK` satırı (sayılar); not varken olay nota düşer. Hata yükseltmez."""
    try:
        from apps.okul import denetim_izi, iz_durumu
        from apps.okul.models import AuditAction

        degerler = {"tasinan": (None, tasinan), "tasinamayan": (None, tasinamayan)}
        iz_durumu.sistem_olayi(
            AuditAction.BUTUNLUK,
            model=denetim_izi.DOSYA_DEPOSU,
            object_id=_YETIM_KIMLIGI,
            changed_fields=sorted(degerler),
            values=degerler,
        )
    except Exception:  # noqa: BLE001 — açılış iz yüzünden durmaz
        logger.warning("Yetim taraması denetim izine yazılamadı.", exc_info=True)


def yetim_taramasi(db_path: Path, depo: Path, *, gun: date | None = None) -> int:
    """Satırı olmayan dosyaları yetime taşır; taşınan sayıyı döndürür (modül başlığı "Yetim taraması").

    Hata yükseltmez. Bir dosya bile taşınmadıysa denetim izine satır yazılmaz: taşınamayan dosya her
    açılışta yeniden denenir, satırı çoğaltmaz, günlüğe düşer.
    """
    from django.utils import timezone

    from shared import dosya_sifreleme as ds

    kayitli = _kayitli_ek_adlari(db_path)
    if kayitli is None:
        return 0
    try:
        yetimler = [ad for ad in ds.depodaki_dosyalar(depo) if ad not in kayitli]
    except OSError as hata:
        logger.warning("Dosya deposu taranmadı: dizin okunamadı (%s).", type(hata).__name__)
        return 0
    gunu = gun if gun is not None else timezone.localdate()
    tasinan = tasinamayan = 0
    for ad in yetimler:
        try:
            ds.yetime_tasi(depo, ad, gunu)
        except OSError:
            tasinamayan += 1
        else:
            tasinan += 1
    if tasinamayan:
        logger.warning("Satırı olmayan %d dosya yetime taşınamadı.", tasinamayan)
    if tasinan:
        logger.warning("Satırı olmayan %d dosya yetime taşındı.", tasinan)
        _yetim_olayini_yaz(tasinan=tasinan, tasinamayan=tasinamayan)
    return tasinan


def _artigi_sil(yol: Path, mod: int) -> None:
    if stat.S_ISDIR(mod):
        shutil.rmtree(yol)
    else:
        yol.unlink()


def _artik_kurallari(
    db_path: Path, yedekler: Path, depo: Path
) -> tuple[tuple[Path, Callable[[str], bool], Callable[[int], bool]], ...]:
    """(dizin, ad tanıyıcı, beklenen tür) üçlüleri: tanınan artıkların tek listesi (modül başlığı)."""
    from desktop.backup import GORUNTU_DIZINI_ONEKI, SQLITE_EKLERI
    from desktop.backup_crypto import BACKUP_SUFFIX

    from apps.okul.services import backup_restore, geri_yukleme_yetkisi, live_restore
    from shared import dosya_sifreleme as ds

    yeni = db_path.name + backup_restore.YENI_VERITABANI_EKI
    yeni_adlar = {yeni, *(yeni + ek for ek in SQLITE_EKLERI)}
    yarim_yedek = BACKUP_SUFFIX + ds.GECICI_EK

    def yedek_artigi_mi(ad: str) -> bool:
        return ad.endswith(yarim_yedek) or (
            ad.startswith(live_restore.YUKLEME_ONEKI) and ad.endswith(live_restore.YUKLEME_EKI)
        )

    return (
        (db_path.parent, yeni_adlar.__contains__, stat.S_ISREG),
        (
            db_path.parent,
            lambda ad: ad.startswith(geri_yukleme_yetkisi.GECICI_DIZIN_ONEKI),
            stat.S_ISDIR,
        ),
        (db_path.parent, lambda ad: ad.startswith(GORUNTU_DIZINI_ONEKI), stat.S_ISDIR),
        (yedekler, yedek_artigi_mi, stat.S_ISREG),
        (depo, ds.gecici_artik_mi, stat.S_ISREG),
        (depo, ds.hazirlik_artigi_mi, stat.S_ISDIR),
    )


def artiklari_temizle(db_path: Path, yedekler: Path, depo: Path) -> int:
    """Yarım işlerin artıklarını siler; silinen sayıyı döndürür (modül başlığı "Artık temizliği").

    Hata yükseltmez; silinemeyen artık sonraki açılışta yeniden denenir.
    """
    silinen = kalan = 0
    for dizin, artik_mi, tur_tutar_mi in _artik_kurallari(db_path, yedekler, depo):
        try:
            adlar = sorted(ad for ad in os.listdir(dizin) if artik_mi(ad))
        except OSError:
            continue  # dizin yoksa artığı da yoktur; okunamıyorsa sonraki açılış dener
        for ad in adlar:
            yol = dizin / ad
            try:
                mod = yol.lstat().st_mode
                if tur_tutar_mi(mod):
                    _artigi_sil(yol, mod)
                    silinen += 1
            except OSError:
                kalan += 1
    if kalan:
        logger.warning("Yarım işlerden kalan %d artık silinemedi.", kalan)
    if silinen:
        logger.info("Yarım işlerden kalan %d artık silindi.", silinen)
    return silinen


def kapanis_kilidi_kaydet(kilitle: Callable[[], bool] | None) -> None:
    """Backend düzenli kapanışın oturum kilidini kaydeder (`None` kaydı kaldırır).

    `kilitle` oturum açıksa kilitler ve True döndürür; oturum yoksa False.
    """
    global _kapanis_kilidi
    with _kilit:
        _kapanis_kilidi = kilitle


def kapanista_kilitle() -> bool:
    """Masaüstü düzenli kapanışta çağırır: oturum açıksa kilitler; kilitlediyse True.

    Kayıt yoksa (backend yüklenmemiş, testler) False. Kanca ENGELLER: uçuştaki
    isteklerin, süren bir kilidin ve süren bir kilit açılışının bitmesini sınırlı süre bekler
    (`apps.okul.oturum.UCUSTA_BEKLEME_SN`; "DÜZENLİ KAPANIŞ"): dönüşte oturumun `KILIT` satırı
    ve çapası yazılmıştır, masaüstü ancak sonra yönetim sunucusunu durdurur.
    """
    with _kilit:
        kilitle = _kapanis_kilidi
    if kilitle is None:
        return False
    return kilitle()


def _reset_for_tests() -> None:
    """Yalnız testler için: kayıt süreç içi olduğundan testler arasında sızar.

    Masaüstünün kaydettikleri (çıkış, ertelenenleri deneme) ve gün işleri temizlenir —
    `OkulConfig.ready`'nin kaydettiği gün işi de (erişim günlüğünün silmesi; onu sınayan test
    `ready`'yi yeniden çağırır). Backend'in açılışta kaydettiği kapanış kilidi YERİNDE kalır
    (süreç boyunca tek kayıttır).
    """
    global _cikis, _ertelenenleri_dene
    with _kilit:
        _cikis = None
        _ertelenenleri_dene = None
        _gunluk_isler.clear()
