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
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass

logger = logging.getLogger("oab_defteri.okul")

GunlukIs = Callable[[], bool | None]

#: Denetim izinin `object_id` sütununun sınırı (dosya adı daha uzunsa kırpılır).
_KIMLIK_SINIRI = 64


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
