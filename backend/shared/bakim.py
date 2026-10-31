"""Bakım kapısı — geri yükleme ile gün işlerinin dışlaşması (tasarım §4.1, §4.2; §13 D3).

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

Uzun yazma işi sayacı (boşta kilit ve çarpı ertelemesi, §4.2) F1b'de buraya
eklenir.
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
