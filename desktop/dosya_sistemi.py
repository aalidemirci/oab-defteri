"""Seçilen yerin dosya sistemi (plan F1b-3 "Uzun iş, çarpı, temiz kapanış").

Şifreli yedek kullanıcının seçtiği yere yazılır. FAT32 tek dosyada 4 GiB'ı aşamaz; okul
USB belleklerinin çoğu böyle biçimlenmiştir. Yazmaya başlamadan önce bilinirse kullanıcı uzun
bir yazımın sonunda değil, başında uyarılır.

Tür, işletim sisteminin kendi kaydından okunur: Windows'ta `GetVolumeInformationW`, Linux'ta
`/proc/self/mountinfo`. Okunamazsa `None` döner, HATA YÜKSELTMEZ: çağıran yazımı dener, sınır
aşılırsa işletim sisteminin hatasını Türkçe iletiye çevirir (`encrypted_backup`). Yol günlüğe
yazılmaz: Windows yolu hesap adını taşır.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Final

#: FAT'ın tek dosya sınırı (bayt): 2^32 - 1.
FAT_TEK_DOSYA_SINIRI: Final = 2**32 - 1
#: FAT ailesinin adları: Windows `FAT` ve `FAT32` der, Linux çekirdeği `vfat` ve `msdos`.
_FAT_TURLERI: Final = frozenset({"fat", "fat12", "fat16", "fat32", "vfat", "msdos"})
_MOUNTINFO: Final = Path("/proc/self/mountinfo")
#: `mountinfo`'daki sekizlik kaçış (boşluk `\040`).
_KACIS: Final = re.compile(r"\\([0-7]{3})")
#: `GetVolumePathNameW` ve `GetVolumeInformationW` tamponlarının karakter sayısı.
_TAMPON: Final = 1024


def fat_mi(tur: str | None) -> bool:
    """Tür FAT ailesinden mi? Bilinmeyen tür FAT sayılmaz: yazım denenir (modül başlığı)."""
    return tur is not None and tur.lower() in _FAT_TURLERI


def _kacisi_coz(ham: str) -> str:
    return _KACIS.sub(lambda eslesme: chr(int(eslesme[1], 8)), ham)


def _altinda_mi(yol: str, nokta: str) -> bool:
    return nokta == "/" or yol == nokta or yol.startswith(nokta.rstrip("/") + "/")


def _linux_turu(yol: Path, mountinfo: Path) -> str | None:
    """Yolu taşıyan en uzun bağlama noktasının türü; aynı noktaya sonra bağlanan kazanır."""
    gercek = os.path.realpath(yol)
    tur: str | None = None
    en_uzun = -1
    icerik = mountinfo.read_text(encoding="utf-8", errors="surrogateescape")
    for satir in icerik.splitlines():
        sol, ayrac, sag = satir.partition(" - ")
        alanlar = sol.split(" ")
        if not ayrac or len(alanlar) < 5 or not sag:
            continue
        nokta = _kacisi_coz(alanlar[4])
        if _altinda_mi(gercek, nokta) and len(nokta) >= en_uzun:
            tur, en_uzun = sag.split(" ")[0], len(nokta)
    return tur


def _windows_turu(yol: Path) -> str | None:
    import ctypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    kok = ctypes.create_unicode_buffer(_TAMPON)
    if not kernel32.GetVolumePathNameW(str(yol), kok, _TAMPON):
        return None
    tur = ctypes.create_unicode_buffer(_TAMPON)
    if not kernel32.GetVolumeInformationW(kok, None, 0, None, None, None, tur, _TAMPON):
        return None
    return tur.value or None


def dosya_sistemi_turu(yol: Path, *, mountinfo: Path = _MOUNTINFO) -> str | None:
    """Yolun bulunduğu birimin dosya sistemi; okunamazsa `None` (modül başlığı)."""
    try:
        if sys.platform == "win32":
            return _windows_turu(yol)
        return _linux_turu(yol, mountinfo)
    except (OSError, ValueError, AttributeError):
        return None
