"""Seçilen yerin dosya sistemi (plan F1b-3 "Uzun iş, çarpı, temiz kapanış")."""

from __future__ import annotations

from pathlib import Path

import pytest

from desktop.dosya_sistemi import FAT_TEK_DOSYA_SINIRI, dosya_sistemi_turu, fat_mi

_MOUNTINFO = """\
22 1 8:1 / / rw,relatime shared:1 - ext4 /dev/sda1 rw
36 22 0:30 / /proc rw,nosuid shared:2 - proc proc rw
40 22 8:17 / /media/ogretmen/USB\\040BELLEK rw,nosuid shared:7 - vfat /dev/sdb1 rw,fmask=0022
41 22 8:18 / /media/ogretmen/ntfs rw shared:8 master:3 - fuseblk /dev/sdb2 rw,user_id=0
42 22 8:19 / /mnt/ust rw shared:9 - ext4 /dev/sdc1 rw
43 42 8:20 / /mnt/ust/alt rw shared:10 - exfat /dev/sdc2 rw
bozuk satir
44 22 8:21 / /mnt/cift rw shared:11 - ext4 /dev/sdd1 rw
45 22 8:22 / /mnt/cift rw shared:12 - vfat /dev/sdd2 rw
46 22 0:40 / /media rw,nosuid shared:13 - tmpfs tmpfs rw
"""


@pytest.fixture
def mountinfo(tmp_path: Path) -> Path:
    yol = tmp_path / "mountinfo"
    yol.write_text(_MOUNTINFO, encoding="utf-8")
    return yol


@pytest.mark.parametrize(
    ("yol", "tur"),
    [
        ("/home/ogretmen", "ext4"),
        ("/media/ogretmen/USB BELLEK/yedekler", "vfat"),
        ("/media/ogretmen/USB BELLEK", "vfat"),
        ("/media/ogretmen/ntfs", "fuseblk"),
        ("/media/ogretmen/USB BELLEK2", "tmpfs"),  # önek benzerliği bağlama noktası sayılmaz
        ("/mnt/ust/alt/dizin", "exfat"),  # en uzun bağlama noktası kazanır
        ("/mnt/ust/dizin", "ext4"),
        ("/mnt/cift", "vfat"),  # aynı noktaya sonra bağlanan kazanır
    ],
)
def test_linuxta_tur_en_uzun_baglama_noktasindan_okunur(
    yol: str, tur: str, mountinfo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("desktop.dosya_sistemi.sys.platform", "linux")
    monkeypatch.setattr("desktop.dosya_sistemi.os.path.realpath", lambda hedef: str(hedef))

    assert dosya_sistemi_turu(Path(yol), mountinfo=mountinfo) == tur


def test_kayit_okunamazsa_tur_yoktur_hata_yukselmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("desktop.dosya_sistemi.sys.platform", "linux")

    assert dosya_sistemi_turu(tmp_path, mountinfo=tmp_path / "yok") is None


def test_windows_arayuzu_yoksa_tur_yoktur(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ctypes.windll` Windows dışında yoktur: işlev hata yükseltmez, yazım denenir."""
    monkeypatch.setattr("desktop.dosya_sistemi.sys.platform", "win32")

    assert dosya_sistemi_turu(Path("/")) is None


@pytest.mark.parametrize("tur", ["FAT", "FAT32", "fat32", "vfat", "msdos"])
def test_fat_ailesi_taninir(tur: str) -> None:
    assert fat_mi(tur)


@pytest.mark.parametrize("tur", ["NTFS", "exFAT", "exfat", "ext4", "fuseblk", "", None])
def test_oteki_turler_fat_sayilmaz(tur: str | None) -> None:
    assert not fat_mi(tur)


def test_fat_siniri_dort_gibden_bir_bayt_eksiktir() -> None:
    assert FAT_TEK_DOSYA_SINIRI == 4 * 1024**3 - 1
