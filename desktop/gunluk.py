"""Gün değişimi kapısı — `od-gunluk` iş parçacığı (tasarım T9, §4.1, §4.2).

Program günlerce açık kalabilir; "her gün yeniden açılır" varsayımı geçersizdir.
Günde bir kez yapılması gereken işler bu yüzden açılışa değil KAPIYA bağlanır:
kapı açılışta ve süreç içinde saatte bir koşar, her işin son çalıştığı günü
damga dosyasında tutar ve günü eskiyen işi çalıştırır.

* **Kayıt defteri.** İşler adla kaydolur (`kaydet`); sonraki fazlar kendi
  işlerini ekler. Backend'deki bir iş masaüstünü içe aktarmadan
  `apps.okul.masaustu_kanca.gunluk_is_kaydet` ile kaydolur; kapı o listeyi
  açılışta okur (`backend_islerini_ekle`).
* **Damga** (`gun-kapisi.json`, veri dizininde): iş başına son başarılı gün.
  Bir iş `False` döner ya da istisna yükseltirse damgası yazılmaz ve bir saat
  sonra yeniden denenir (ör. yönetici parolası kurulmadan yedek alınamaz).
  Tarih YEREL gündür (`date.today()`, `Europe/Istanbul`); saat taklit edilebilir.
* **Bakım kapısı** (§13 D3): her iş ortak bakım kapısından geçer
  (`shared.bakim.KAPI.is_()`); geri yükleme sürerken iş başlamaz, başlamış iş
  bitene dek geri yükleme bekler. İş bitince bu iş parçacığının Django
  bağlantıları kapatılır: açık kalan bir bağlantı Windows'ta geri yüklemedeki
  dosya takasını bozardı.
* **Yerleşik iş** (`desktop/main.py` kaydeder): günlük yedek + 14 gün rotasyonu
  (yedek alınmadıysa rotasyon koşmaz).
* **Saatlik işler** (`saatlik_kaydet`): damgasız, HER tikte koşar. Günde bir
  yetmeyen denetimler içindir; bakım kapısından aynı biçimde geçer.

Aile iskeletindeki uyku engelleme ve IP denetimi yalnız ağ kataloğu içindi;
katalogla birlikte söküldü (program ağ servisi sunmaz).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

logger = logging.getLogger("oab_defteri.gunluk")

THREAD_NAME: Final = "od-gunluk"
DAMGA_DOSYASI: Final = "gun-kapisi.json"
SAATLIK_SN: Final = 3600.0

GunlukIs = Callable[[], bool | None]
BakimKapisiGirisi = Callable[[], AbstractContextManager[bool]]


@dataclass(frozen=True)
class IsKaydi:
    ad: str
    calistir: GunlukIs


# ------------------------------------------------------ açık kalma saati


def acik_kalma_saati(platform: str = sys.platform) -> float:
    """Sistemin açılıştan beri geçen süresi (sn), UYKU DAHİL; duvar saatinden bağımsız.

    Duvar saati elle ya da NTP'yle sıçrayabilir; bu saat sıçramaz ve bilgisayar
    uykudayken de ilerler. Windows'ta `GetTickCount64` (uyku ve hazırda bekletme
    dahil), Linux'ta `CLOCK_BOOTTIME` (askıya alma dahil; `CLOCK_MONOTONIC`
    dahil etmez). İkisi de yoksa `time.monotonic`.
    """
    if platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.GetTickCount64.restype = ctypes.c_ulonglong
            return float(kernel32.GetTickCount64()) / 1000.0
        except (AttributeError, OSError):
            return time.monotonic()
    saat = getattr(time, "CLOCK_BOOTTIME", None)
    if saat is not None:
        try:
            return time.clock_gettime(saat)
        except OSError:
            pass
    return time.monotonic()


# ----------------------------------------------------------- bakım kapısı


def varsayilan_bakim_girisi() -> BakimKapisiGirisi:
    """Ortak bakım kapısı (`shared.bakim.KAPI.is_`; tasarım §13 D3).

    Düşüş yolu YOKTUR: kapı bulunamazsa iş "her zaman izinli" sayılmaz, hata
    yükselir ve iş bir saat sonra yeniden denenir (geri yükleme ile gün işleri
    dışlaşmadan iş koşmaz). İçe aktarma çağrı anındadır: backend dizini
    `sys.path`'e `prepare_django` ile girer.
    """
    from shared.bakim import KAPI

    return KAPI.is_


def _baglantilari_kapat() -> None:
    """Bu iş parçacığının Django bağlantıları (Django kurulu değilse etkisiz)."""
    try:
        from django.db import connections

        connections.close_all()
    except Exception:  # noqa: BLE001 — Django yok ya da kurulmamış
        logger.debug("Django bağlantıları kapatılamadı (Django kurulmamış olabilir).")


# --------------------------------------------------------------- kapı


class GunDegisimiKapisi:
    """Günde bir kez yapılacak işlerin kapısı; `od-gunluk` iş parçacığını yönetir."""

    def __init__(
        self,
        *,
        damga_yolu: Path,
        bugun: Callable[[], date] = date.today,
        bakim_girisi: BakimKapisiGirisi | None = None,
        aralik_sn: float = SAATLIK_SN,
        baglanti_kapatici: Callable[[], None] = _baglantilari_kapat,
        monoton: Callable[[], float] = time.monotonic,
    ) -> None:
        self._monoton = monoton
        self._damga_yolu = damga_yolu
        self._bugun = bugun
        self._bakim_girisi = bakim_girisi
        self._aralik = aralik_sn
        self._baglanti_kapat = baglanti_kapatici
        self._isler: dict[str, IsKaydi] = {}
        self._saatlik: dict[str, IsKaydi] = {}
        self._ilk_is: Callable[[], None] | None = None
        self._kilit = threading.Lock()
        self._uyandir = threading.Event()
        self._dur = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------ kayıt

    def kaydet(self, ad: str, calistir: GunlukIs) -> None:
        """İşi kayda alır (aynı ad yeniden kaydedilirse öncekinin yerine geçer)."""
        if not ad or not ad.isascii():
            raise ValueError("Gün değişimi işinin adı ASCII ve boş olmayan bir dize olmalı.")
        with self._kilit:
            self._isler[ad] = IsKaydi(ad, calistir)

    def saatlik_kaydet(self, ad: str, calistir: GunlukIs) -> None:
        """DAMGASIZ iş: her tikte (açılışta ve saatte bir) koşar (modül belgesi)."""
        if not ad or not ad.isascii():
            raise ValueError("Saatlik işin adı ASCII ve boş olmayan bir dize olmalı.")
        with self._kilit:
            self._saatlik[ad] = IsKaydi(ad, calistir)

    def backend_islerini_ekle(self) -> int:
        """`masaustu_kanca.gunluk_isler()` listesini kayda alır (Django kurulduktan sonra)."""
        try:
            from apps.okul.masaustu_kanca import gunluk_isler
        except ImportError:
            return 0
        sayi = 0
        for kayit in gunluk_isler():
            self.kaydet(kayit.ad, kayit.calistir)
            sayi += 1
        return sayi

    @property
    def is_adlari(self) -> tuple[str, ...]:
        with self._kilit:
            return tuple(self._isler)

    # ------------------------------------------------------------ damga

    def damgalar(self) -> dict[str, str]:
        try:
            veri = json.loads(self._damga_yolu.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        isler = veri.get("isler") if isinstance(veri, dict) else None
        if not isinstance(isler, dict):
            return {}
        return {str(ad): str(gun) for ad, gun in isler.items() if isinstance(gun, str)}

    def _damga_yaz(self, damgalar: dict[str, str]) -> None:
        gecici = self._damga_yolu.with_name(self._damga_yolu.name + ".tmp")
        try:
            self._damga_yolu.parent.mkdir(parents=True, exist_ok=True)
            gecici.write_text(
                json.dumps({"surum": 1, "isler": damgalar}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(gecici, self._damga_yolu)
        except OSError:
            logger.warning("Gün değişimi damgası yazılamadı.", exc_info=True)

    # ------------------------------------------------------------ tek geçiş

    def tik(self) -> list[str]:
        """Günü eskiyen işleri çalıştırır; bu geçişte BAŞARIYLA biten işlerin adları."""
        bugun = self._bugun().isoformat()
        damgalar = self.damgalar()
        with self._kilit:
            isler = list(self._isler.values())
        biten: list[str] = []
        for is_ in isler:
            if damgalar.get(is_.ad) == bugun:
                continue
            if self._calistir(is_):
                damgalar[is_.ad] = bugun
                biten.append(is_.ad)
        if biten:
            self._damga_yaz(damgalar)
            logger.info("Gün değişimi kapısı: %s tamamlandı.", ", ".join(biten))
        with self._kilit:
            saatlik = list(self._saatlik.values())
        for is_ in saatlik:
            self._calistir(is_)  # damga yok; sonuç bir sonraki tikte yeniden sorulur
        return biten

    def _calistir(self, is_: IsKaydi) -> bool:
        try:
            # Kapı bulunamazsa (ImportError) iş koşmaz; bir saat sonra yeniden denenir.
            giris = self._bakim_girisi or varsayilan_bakim_girisi()
            with giris() as izin:
                if not izin:
                    logger.info("Gün değişimi işi bakım nedeniyle ertelendi: %s", is_.ad)
                    return False
                try:
                    sonuc = is_.calistir()
                finally:
                    self._baglanti_kapat()
        except Exception:  # noqa: BLE001 — bir iş ötekileri durdurmaz
            logger.exception(
                "Gün değişimi işi başarısız: %s (bir saat sonra yeniden denenecek)", is_.ad
            )
            return False
        return sonuc is not False

    # ------------------------------------------------------------ iş parçacığı

    def baslat(self, *, ilk_is: Callable[[], None] | None = None) -> None:
        """`od-gunluk`'u başlatır. `ilk_is` döngüden önce bir kez koşar."""
        if self._thread is not None:
            raise RuntimeError("Gün değişimi kapısı zaten çalışıyor.")
        self._dur.clear()
        self._ilk_is = ilk_is
        self._thread = threading.Thread(target=self._dongu, name=THREAD_NAME, daemon=True)
        self._thread.start()

    def uyandir(self) -> None:
        """Döngüyü uyandırır (saatlik takvim kaymaz; vakti gelmişse tik koşar)."""
        self._uyandir.set()

    def durdur(self, *, zaman_asimi: float = 10.0) -> None:
        """Döngüyü bitirir."""
        thread, self._thread = self._thread, None
        self._dur.set()
        self._uyandir.set()
        if thread is not None and thread.is_alive():
            thread.join(timeout=zaman_asimi)

    def _dongu(self) -> None:
        try:
            ilk_is, self._ilk_is = self._ilk_is, None
            if ilk_is is not None:
                try:
                    ilk_is()
                except Exception:  # noqa: BLE001 — açılış işi kapıyı düşürmesin
                    logger.exception("Gün değişimi kapısının açılış işi başarısız.")
                finally:
                    self._baglanti_kapat()
            self.tik()
            sonraki = self._monoton() + self._aralik
            while not self._dur.is_set():
                # Uyandırma saatlik takvimi kaydırmaz.
                self._uyandir.wait(timeout=max(0.0, sonraki - self._monoton()))
                self._uyandir.clear()
                if self._dur.is_set():
                    break
                if self._monoton() >= sonraki:
                    self.tik()
                    sonraki = self._monoton() + self._aralik
        except Exception:  # noqa: BLE001 — iş parçacığı sessizce ölmesin
            logger.exception("Gün değişimi kapısı beklenmedik biçimde durdu.")


@contextmanager
def calisan_kapi(kapi: GunDegisimiKapisi) -> Iterator[GunDegisimiKapisi]:
    """`with calisan_kapi(k):` — başlatır, çıkışta her durumda durdurur."""
    kapi.baslat()
    try:
        yield kapi
    finally:
        kapi.durdur()
