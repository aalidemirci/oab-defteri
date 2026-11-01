"""Bakım kapısı ve uzun iş sayacı (tasarım §4.1, §4.2, §4.4.3; §13 D3; TK5, TK14, TK19).

İki süreç içi nesne vardır: geri yükleme ile gün işlerini dışlaştıran **bakım kapısı**
(`KAPI`) ve boşta ya da elle kilidi erteleyen **uzun iş sayacı** (`UZUN_ISLER`).

BAKIM KAPISI

Yedekten geri yükleme veritabanı dosyasının yerine başkasını koyar. O sırada bir
gün işi (günlük yedek) dosyayı açık tutarsa (Windows'ta dosya değiştirilemez) ya
da yarım bir dosyayı okursa geri yükleme bozulur. Sıra:

1. `bakima_al()` — kapı kapanır: yeni iş başlamaz.
2. Aynı çağrı uçuştaki iş sayacı sıfıra inene dek bekler.
3. Gün değişimi kapısının işleri (`desktop/gunluk.py`) bu kapıdan geçer
   (`is_()` bağlam yöneticisi): kapı kapalıyken iş başlamaz, başlamış iş
   bitene dek bakım bekler. İş parçacığının bağlantıları iş bitince kapatılır.
4. Başarılı geri yüklemeden sonra kapı program yeniden açılana dek kapalı kalır
   (`bakimdan_cik` yalnız geri yükleme başarısız olduğunda ve testlerde
   kullanılır).

Aile iskeletinde kapı ağ kataloğu paketindeydi ve masaüstü kolu onu
bulamadığında sessizce "her zaman izinli"ye düşüyordu; OAB'de kapı burada durur
ve düşüş yolu yoktur. Bu modül YALNIZ standart kütüphaneyi kullanır: hem Django
tarafı (geri yükleme) hem masaüstü kabuğu (gün işleri) aynı nesneyi içe aktarır.
Süreç içi tektir (`KAPI`).

UZUN İŞ SAYACI (§4.2 "Uçuştaki iş", §4.4.3 "Boşta kilit"; denetim UY-1)

Uzun yazma işi (bugün yalnız canlı geri yükleme; tam yedek, banka özeti uygulama,
dönem kapanışı, DEK yenileme ve dosya eki yazımı geldikçe girer) sürerken oturum
kilitlenmez: kilit (elle ya da boşta) ertelenir, iş bitince ilk istekte uygulanır
(`apps/okul/oturum.py`). Böylece DEK işin ortasında bellekten silinmez. Çarpının
bir kez ertelenmesi ve temiz kapanış işaretinin "sayaç sıfırken" koşulu ilk yeni
uzun işle (tam yedek, plan F1b 3. adım) bu sayaca bağlanır.

Sayaç bakım kapısının uçuştaki iş sayacından AYRIDIR: canlı geri yükleme hem uzun
iştir hem de bakım kapısını kapatıp gün işlerinin bitmesini bekler; tek sayaç
olsaydı geri yükleme kendi kendini beklerdi. Sayaç kapı değildir, hiçbir işi
reddetmez; yalnız sayar (`with UZUN_ISLER.is_():`).
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final


class BakimKapisi:
    """Uçuştaki işleri sayan ve bakımda yeni işi reddeden kapı (iş parçacığı güvenli)."""

    def __init__(self) -> None:
        self._kosul = threading.Condition()
        self._bakimda = False
        self._ucusta = 0

    @property
    def bakimda(self) -> bool:
        with self._kosul:
            return self._bakimda

    @property
    def ucusta(self) -> int:
        """Şu an kapıdan geçmiş ve henüz bitmemiş iş sayısı."""
        with self._kosul:
            return self._ucusta

    def gir(self) -> bool:
        """İşe başlama izni: bakımdaysa `False` (iş başlamaz), değilse sayaç artar.

        `True` dönen her `gir()` için tam bir kez `cik()` çağrılmalıdır; bunu
        `is_()` bağlam yöneticisi garanti eder.
        """
        with self._kosul:
            if self._bakimda:
                return False
            self._ucusta += 1
            return True

    def cik(self) -> None:
        """İşin bittiğini bildirir; son iş bitince bekleyen bakımı uyandırır."""
        with self._kosul:
            if self._ucusta <= 0:
                raise RuntimeError("Bakım kapısı: girişi olmayan çıkış.")
            self._ucusta -= 1
            if self._ucusta == 0:
                self._kosul.notify_all()

    @contextmanager
    def is_(self) -> Iterator[bool]:
        """`with KAPI.is_() as izin:` — izin yoksa iş yapılmaz; varsa çıkış garantilidir."""
        izin = self.gir()
        try:
            yield izin
        finally:
            if izin:
                self.cik()

    def bakima_al(self, *, bekleme_sn: float = 10.0) -> bool:
        """Kapıyı kapatır ve uçuştaki işlerin bitmesini bekler.

        `True`: bütün işler bitti, veritabanı serbest. `False`: süre doldu, hâlâ
        iş var — kapı YİNE DE kapalı kalır (yeni iş başlamaz).
        """
        with self._kosul:
            self._bakimda = True
            return self._kosul.wait_for(lambda: self._ucusta == 0, timeout=bekleme_sn)

    def bakimdan_cik(self) -> None:
        """Kapıyı yeniden açar (geri yükleme başarısız olduysa; testler)."""
        with self._kosul:
            self._bakimda = False


#: Süreç içi tek bakım kapısı: gün değişimi işleri ve canlı geri yükleme paylaşır.
KAPI: Final = BakimKapisi()


class UzunIsSayaci:
    """Süren uzun yazma işlerini sayar (iş parçacığı güvenli; modül başlığı)."""

    def __init__(self) -> None:
        self._kilit = threading.Lock()
        self._sayi = 0

    @property
    def sayi(self) -> int:
        """Şu an süren uzun iş sayısı; sıfır değilken oturum kilidi ertelenir."""
        with self._kilit:
            return self._sayi

    @contextmanager
    def is_(self) -> Iterator[None]:
        """`with UZUN_ISLER.is_():` — iş süresince sayaç bir artar; çıkış garantilidir."""
        with self._kilit:
            self._sayi += 1
        try:
            yield
        finally:
            with self._kilit:
                self._sayi -= 1

    def _reset_for_tests(self) -> None:
        """Yalnız testler için: sayaç süreç içi olduğundan testler arasında sızar."""
        with self._kilit:
            self._sayi = 0


#: Süreç içi tek uzun iş sayacı: oturum (boşta ve elle kilit) okur, uzun işler artırır.
UZUN_ISLER: Final = UzunIsSayaci()
