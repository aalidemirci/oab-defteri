"""Geri yüklemede dosya deposu (tasarım §4.4.7, §10.6; plan F1b-3 "Geri yükleme").

Kullanıcı kararları (04.11.2026 "Bozuk ekte geri yükleme durur, ikinci onayla sürer", "Eksik ve bozuk
ekler kişisiz bilgiyle listelenir"; 05.11.2026 "Yedek alınırken bozuk olan ek eksik sayılır"). Yazıcı
`tam_yedek_yaz`'dır, programdaki çağıranı `encrypted_backup`'tır. Çekirdek gibi bu testler ORM'e
dokunmaz; ilk testler gerçek şemada, gerçek depo servisiyle koşar. Ekler ve adlar uydurmadır
(`geri_yukleme_ortak`).

"eksik": manifestoda `eksik` işaretli ya da yerel yedekte hiçbir yerde bulunamayan ek; durdurmaz.
"bozuk": tam yedekte özeti tutmayan girdi, yerel yedekte depoda ya da yetimde duran ama tutmayan ek;
durdurur, ikinci onayla o ek olmadan sürer. Kap düzeyinde bozuk bölüm onayla da sürmez.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import shutil
import sqlite3
import stat
from collections.abc import Callable, Iterator
from contextlib import closing
from dataclasses import replace
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from desktop import backup_crypto
from desktop.backup import goruntu_ve_manifesto
from desktop.backup_crypto import (
    DOSYA_BOLUMU_SONU,
    KAPSAM_TAM,
    Manifesto,
    ManifestoGirdisi,
    decrypt_bytes,
    kap_basligini_oku,
    private_key_from_data_key,
    tam_yedek_yaz,
)
from desktop.paths import VERSION_STAMP_FILE_NAME
from desktop.tests.kap_ortak import bolum_girdisi, durum_basligi, kap_kur
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.utils import timezone

from apps.okul import iz_dogrulama
from apps.okul.models import Attachment, AttachmentSensitivity, SchoolYear
from apps.okul.services import (
    app_password,
    backup_restore,
    dosya_deposu,
    encrypted_backup,
    geri_yukleme_ekleri,
    ozet_onarimi,
)
from apps.okul.services import school_year as school_year_service
from apps.okul.tests.geri_yukleme_ortak import (
    OZGUN_AD,
    PDF,
    PNG,
    HesapSatiri,
    OrnekEk,
    depoya_koy,
    ek_tablosu_ekle,
    ekli_sqlite,
    ornek_ek,
    tam_yedek_kur,
    yerel_yedek_yaz,
    yetkili_sqlite,
)
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    varsayilan_yazar,
)
from shared import crypto
from shared import dosya_sifreleme as ds

YEDEK = "gunluk-2026-11-04.odbak"


@pytest.fixture
def depo() -> Path:
    """Programın dosya deposu (`guvenlik_ortami` testine özel, henüz kurulmamıştır)."""
    return Path(settings.DOSYA_DEPOSU_DIR)


@pytest.fixture
def canli_db(tmp_path: Path) -> Path:
    """Geri yüklemeden önceki güncel veritabanı."""
    yol = tmp_path / "canli" / "db.sqlite3"
    yol.parent.mkdir()
    # WAL kipinde değil: salt okunur okuma yanında boş `-wal` ve `-shm` bırakır (belgeli), karşılaştırmayı
    # gürültüye boğardı.
    yetkili_sqlite(yol, dek=TEST_DEK, hesaplar=[], isaret="onceki", wal=False)
    return yol


@pytest.fixture
def kaynak_depo(tmp_path: Path) -> Path:
    """Yedeğin alındığı andaki depo."""
    return ds.dizin_kur(tmp_path / "kaynak-depo")


def _goruntu(tmp_path: Path, *ekler: OrnekEk) -> bytes:
    return ekli_sqlite(tmp_path / "goruntu.sqlite3", ekler, isaret="yeni")


def _yedek(tmp_path: Path) -> Path:
    return tmp_path / YEDEK


def _tam_yedek(tmp_path: Path, kaynak_depo: Path, *ekler: OrnekEk) -> Path:
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _goruntu(tmp_path, *ekler), ekler, kaynak_depo)
    return yedek


def _yerel_yedek(tmp_path: Path, *ekler: OrnekEk) -> Path:
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(yedek, _goruntu(tmp_path, *ekler), ekler)
    return yedek


def _geri_yukle(yedek: Path, canli_db: Path, **secenekler: Any) -> backup_restore.RestoreResult:
    return backup_restore.restore_database(
        yedek, canli_db, recovery_key=TEST_KURTARMA_ANAHTARI, **secenekler
    )


def _bit_cevir(yol: Path) -> None:
    """Dosyanın gövdesinde bir bit: boy aynı kalır, GCM etiketi tutmaz."""
    baytlar = bytearray(yol.read_bytes())
    baytlar[-1] ^= 1
    yol.write_bytes(baytlar)


def _agac(kok: Path) -> dict[str, bytes]:
    """Dizinin altındaki düzenli dosyalar: göreli yol → içerik."""
    if not kok.is_dir():
        return {}
    return {
        yol.relative_to(kok).as_posix(): yol.read_bytes() for yol in kok.rglob("*") if yol.is_file()
    }


def _hazirlik_dizinleri(depo: Path) -> list[Path]:
    return list(depo.glob(f"{ds.HAZIRLIK_ONEKI}*")) if depo.is_dir() else []


def _durum(canli_db: Path, depo: Path) -> dict[str, Any]:
    """Geri yüklemenin dokunabileceği her şey: `canli_db`'nin dizini, güvenlik dizini, depo."""
    return {
        "veri": _agac(canli_db.parent),
        "guvenlik": _agac(app_password.state_path().parent),
        "depo": _agac(depo),
    }


def _not() -> dict[str, Any]:
    yol = app_password.state_path().parent / "geri-yukleme-notu.json"
    veri: dict[str, Any] = json.loads(yol.read_text(encoding="utf-8"))
    return veri


# ============================================================ tam yedekte eklerin dönüşü


@pytest.fixture
def sahip(monkeypatch: pytest.MonkeyPatch) -> Iterator[SchoolYear]:
    """Geçici sahip kümesi (`SchoolYear`; F1b'de küme boştur)."""
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", set())
    dosya_deposu.sahip_kaydet(SchoolYear)
    yield school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "sir",
    [
        {"recovery_key": TEST_KURTARMA_ANAHTARI},
        {"hesap": TEST_TANITICI, "password": TEST_PAROLA},
    ],
    ids=["kurtarma_anahtari", "parola"],
)
def test_tam_yedekte_ekli_kayit_geri_yuklemeden_sonra_acilir(
    sir: dict[str, Any], sahip: SchoolYear, tmp_path: Path, depo: Path
) -> None:
    """Tasarım §10.6 (F1b kapısı "şifreli yedek (ekler dâhil) geri yüklenir"): gerçek şema, gerçek
    depo servisi, gerçek yazıcı. Depo kaybolur; yedekten dönen ek programın yoluyla açılır."""
    ek = dosya_deposu.yaz(
        PDF,
        original_name=OZGUN_AD,
        sensitivity=AttachmentSensitivity.OZEL_NITELIKLI,
        owner=sahip,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )
    veritabani, manifesto = goruntu_ve_manifesto(Path(str(connection.settings_dict["NAME"])))
    yedek = tmp_path / "oab-defteri-yedek-2026-11-04-101530.odbak"
    tam_yedek_yaz(
        yedek,
        veritabani,
        manifesto.dosyalar,
        depo,
        private_key_from_data_key(TEST_DEK).public_key(),
        recovery_header=durum_basligi(app_password.read_state() or {}),
    )
    shutil.rmtree(depo)
    hedef = tmp_path / "canli" / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, hedef, **sir)

    assert sonuc.dosya_raporu.sayilar() == {
        "kapsam": "tam",
        "yerine_konan": 1,
        "yetimden_donen": 0,
        "eksik": 0,
        "bozuk": 0,
        "onayla_suruldu": 0,
    }
    with closing(sqlite3.connect(hedef)) as baglanti:
        ad, sarmal = baglanti.execute(
            "SELECT stored_name, key_wrap FROM okul_attachment"
        ).fetchone()
    assert ad == ek.stored_name
    acik = ds.depodan_ac(depo, ad, key_wrap=sarmal, sarmal_anahtari=crypto.file_wrap_key(TEST_DEK))
    assert acik == PDF
    assert dosya_deposu.oku(ek) == PDF  # programın kendi yolu: satırın özeti de tutar
    if os.name == "posix":
        assert stat.S_IMODE((depo / ad).stat().st_mode) == ds.DOSYA_KIPI
    assert not _hazirlik_dizinleri(depo)


def _programin_yedegi(tmp_path: Path) -> Path:
    usb = tmp_path / "usb"
    usb.mkdir()
    return usb / "oab-defteri-yedek-2026-11-06-101530.odbak"


@pytest.mark.django_db(transaction=True)
def test_programin_kaydettigi_tam_yedek_geri_yuklenir_ek_cozulur(
    sahip: SchoolYear, tmp_path: Path, depo: Path
) -> None:
    """Uçtan uca (plan F1b-3 "Ötekiler"): şifreli yedeği program kaydeder, çekirdek açar, ek çözülür."""
    ek = dosya_deposu.yaz(
        PDF,
        original_name=OZGUN_AD,
        sensitivity=AttachmentSensitivity.OZEL_NITELIKLI,
        owner=sahip,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )
    yedek = _programin_yedegi(tmp_path)

    kayit = encrypted_backup.sifreli_yedegi_kaydet(str(yedek))

    assert (kayit.ek_sayisi, kayit.eksik, kayit.denetlendi) == (1, 0, True)
    assert kap_basligini_oku(yedek).kapsam == KAPSAM_TAM
    shutil.rmtree(depo)
    hedef = tmp_path / "canli" / "db.sqlite3"

    sonuc = backup_restore.restore_database(yedek, hedef, recovery_key=TEST_KURTARMA_ANAHTARI)

    assert sonuc.dosya_raporu.sayilar()["kapsam"] == "tam"
    assert sonuc.dosya_raporu.sayilar()["yerine_konan"] == 1
    assert (sonuc.dosya_raporu.eksik, sonuc.dosya_raporu.bozuk) == (0, 0)
    assert dosya_deposu.oku(ek) == PDF
    assert not _hazirlik_dizinleri(depo)


@pytest.mark.django_db(transaction=True)
def test_programin_yedeginde_eksik_ek_durdurmaz_saglam_ek_doner(
    sahip: SchoolYear, tmp_path: Path, depo: Path
) -> None:
    """Boyu tutan bozuk ek yedeğe girmez, geri yüklemede listelenir, durdurmaz.

    Uygulama okuması (`encrypted_backup` başlığı, 4. adım): 05.11.2026 kararı boy farkını sayar.
    """

    def yaz(acik: bytes) -> Attachment:
        return dosya_deposu.yaz(
            acik,
            original_name=OZGUN_AD,
            sensitivity=AttachmentSensitivity.NORMAL,
            owner=sahip,
            yazar=varsayilan_yazar(),
            kisi_listesi=False,
        )

    saglam, bozuk = yaz(PDF), yaz(PNG)
    _bit_cevir(depo / bozuk.stored_name)
    yedek = _programin_yedegi(tmp_path)

    kayit = encrypted_backup.sifreli_yedegi_kaydet(str(yedek))

    assert (kayit.ek_sayisi, kayit.eksik) == (1, 1)
    shutil.rmtree(depo)

    sonuc = backup_restore.restore_database(
        yedek, tmp_path / "canli" / "db.sqlite3", recovery_key=TEST_KURTARMA_ANAHTARI
    )

    assert (sonuc.dosya_raporu.eksik, sonuc.dosya_raporu.bozuk) == (1, 0)
    assert dosya_deposu.oku(saglam) == PDF
    assert not (depo / bozuk.stored_name).exists()


def test_ek_sorgusu_modelin_sutunlarini_okur() -> None:
    """Masaüstü ve çekirdek ORM'siz okur: sütun adı değişirse sorgu sessizce düşmesin."""
    sutunlar = {alan.column for alan in Attachment._meta.fields}
    assert {
        "stored_name",
        "key_wrap",
        "size",
        "sha256",
        "owner_type",
        "owner_id",
        "uploaded_at",
        "purged_at",
    } <= sutunlar
    assert "original_name" not in inspect.getsource(geri_yukleme_ekleri._ek_kayitlari)


def test_tam_yedek_ekleri_yerine_koyar_eski_veritabani_kenara_alinir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    birinci, ikinci = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, birinci, ikinci)
    yedek = _tam_yedek(tmp_path, kaynak_depo, birinci, ikinci)

    sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.dosya_raporu.yerine_konan == 2
    assert _agac(depo) == {birinci.ad: birinci.hazir.kap, ikinci.ad: ikinci.hazir.kap}
    assert sonuc.old_db_path is not None and sonuc.old_db_path.is_file()


def test_depoda_tutan_kopyaya_dokunulmaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    depoya_koy(depo, ek)
    oncesi = (depo / ek.ad).stat().st_mtime_ns

    sonuc = _geri_yukle(_tam_yedek(tmp_path, kaynak_depo, ek), canli_db)

    assert (sonuc.dosya_raporu.yerine_konan, sonuc.dosya_raporu.bozuk) == (0, 0)
    assert (depo / ek.ad).stat().st_mtime_ns == oncesi
    assert not (depo / ds.YETIM_DIZINI).exists()


def test_dosya_bolumu_bellekte_toplanmaz_yedek_tek_seferde_okunmaz(
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§4.4.7 "Dosyalar bellekte toplanmaz": bölüm parça parça yazılır; `read_bytes` kalktı."""
    ek = ornek_ek(PDF * 40)
    depoya_koy(kaynak_depo, ek)
    yedek = _tam_yedek(tmp_path, kaynak_depo, ek)
    monkeypatch.setattr(backup_crypto, "KOPYA_PARCASI", 64)
    parcalar: list[int] = []
    asil_yaz = ds.akisla_yaz

    def izleyen(hedef: Path, gelen: Any) -> None:
        def sayan() -> Iterator[bytes]:
            for parca in gelen:
                parcalar.append(len(parca))
                yield parca

        asil_yaz(hedef, sayan())

    monkeypatch.setattr(ds, "akisla_yaz", izleyen)
    asil_oku = Path.read_bytes

    def yedegi_okumaz(yol: Path) -> bytes:
        assert yol != yedek, "yedek dosyası bütünüyle okunmamalı"
        return asil_oku(yol)

    monkeypatch.setattr(Path, "read_bytes", yedegi_okumaz)

    _geri_yukle(yedek, canli_db)

    assert max(parcalar) == 64 and len(parcalar) > 1
    assert sum(parcalar) == ek.girdi.sifreli_boy
    monkeypatch.undo()
    assert _agac(depo) == {ek.ad: ek.hazir.kap}


# ============================================================ bozuk ek: durur, ikinci onayla sürer


def _bozuk_tam_yedek(tmp_path: Path, kaynak_depo: Path) -> tuple[OrnekEk, OrnekEk, Path]:
    """Biri sağlam, biri boyu tutan ama içeriği bozuk iki ek taşıyan tam yedek."""
    saglam = ornek_ek(PDF, owner_id="3")
    bozuk = ornek_ek(PNG, owner_id="9")
    depoya_koy(kaynak_depo, saglam, bozuk)
    _bit_cevir(kaynak_depo / bozuk.ad)
    return saglam, bozuk, _tam_yedek(tmp_path, kaynak_depo, saglam, bozuk)


def test_bozuk_girdi_durur_ve_hicbir_sey_degismez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _saglam, bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    ilgisiz = ornek_ek()
    depoya_koy(depo, ilgisiz)
    oncesi = _durum(canli_db, depo)
    # Durmak geri almak değildir: yerleşim hiç başlamaz.
    monkeypatch.setattr(ds, "yerine_tasi", lambda *a: pytest.fail("taşıma yapılmamalı"))

    with pytest.raises(backup_restore.EkOnayiGerekli) as durma:
        _geri_yukle(yedek, canli_db)

    assert _durum(canli_db, depo) == oncesi
    assert not _hazirlik_dizinleri(depo)
    assert "1 ek" in str(durma.value)
    rapor = durma.value.rapor
    assert (rapor.kapsam, rapor.bozuk, rapor.eksik, rapor.onayla_suruldu) == ("tam", 1, 0, 0)
    assert rapor.yanit()["ekler"] == [
        {
            "durum": "bozuk",
            "kayit_turu": "ders yılı",
            "kayit_no": "9",
            "yukleme_tarihi": "2026-11-04",  # 21:30 UTC yerelde ertesi gün
            "boyut": len(PNG),
            "yedekte_yoktu": False,
        }
    ]
    assert bozuk.ad not in json.dumps(rapor.yanit())


def test_ikinci_onayla_kayitlar_bozuk_ek_olmadan_geri_yuklenir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    saglam, bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)

    sonuc = _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert _agac(depo) == {saglam.ad: saglam.hazir.kap}
    assert (depo / bozuk.ad).exists() is False
    with closing(sqlite3.connect(canli_db)) as baglanti:
        assert baglanti.execute("SELECT deger FROM kayit").fetchone() == ("yeni",)
    assert sonuc.dosya_raporu.sayilar() == {
        "kapsam": "tam",
        "yerine_konan": 1,
        "yetimden_donen": 0,
        "eksik": 0,
        "bozuk": 1,
        "onayla_suruldu": 1,
    }


def test_bayrak_varken_bozuk_ek_yoksa_onay_sayilmaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)

    sonuc = _geri_yukle(_tam_yedek(tmp_path, kaynak_depo, ek), canli_db, ekler_olmadan_surdur=True)

    assert sonuc.dosya_raporu.onayla_suruldu == 0


def test_ikinci_onay_durumsuzdur_dogrulama_bastan_kosar(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan F1b-3 "(c) ekleri": ikinci onay durumsuzdur; sunucu ilk denemenin dosyasını saklamaz,
    bölüm yeniden okunur."""
    _saglam, _bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    okuma = 0
    asil = backup_crypto.dosya_bolumunu_oku

    def sayan(*args: Any) -> Any:
        nonlocal okuma
        okuma += 1
        return asil(*args)

    monkeypatch.setattr(geri_yukleme_ekleri, "dosya_bolumunu_oku", sayan)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)
    _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert okuma == 2


def _kesik(yedek: Path, _a: OrnekEk, _b: OrnekEk, _goruntu: bytes) -> None:
    yedek.write_bytes(yedek.read_bytes()[:-20])


def _sirasi_bozuk(yedek: Path, a: OrnekEk, b: OrnekEk, goruntu: bytes) -> None:
    yedek.write_bytes(
        kap_kur(
            goruntu,
            TEST_DEK,
            baslik=durum_basligi(app_password.read_state() or {}),
            manifesto=Manifesto(KAPSAM_TAM, (a.girdi, b.girdi)),
            dosya_bolumu=bolum_girdisi(b.ad.encode("ascii"), b.hazir.kap)
            + bolum_girdisi(a.ad.encode("ascii"), a.hazir.kap)
            + DOSYA_BOLUMU_SONU,
        )
    )


def _manifestoda_olmayan_girdi(yedek: Path, a: OrnekEk, _b: OrnekEk, goruntu: bytes) -> None:
    yabanci = ornek_ek(PNG)
    yedek.write_bytes(
        kap_kur(
            goruntu,
            TEST_DEK,
            baslik=durum_basligi(app_password.read_state() or {}),
            manifesto=Manifesto(KAPSAM_TAM, (a.girdi,)),
            dosya_bolumu=bolum_girdisi(a.ad.encode("ascii"), a.hazir.kap)
            + bolum_girdisi(yabanci.ad.encode("ascii"), yabanci.hazir.kap)
            + DOSYA_BOLUMU_SONU,
        )
    )


@pytest.mark.parametrize(
    "boz",
    [_kesik, _sirasi_bozuk, _manifestoda_olmayan_girdi],
    ids=["kesik", "sirasi_bozuk", "manifestoda_olmayan_girdi"],
)
@pytest.mark.parametrize("onay", [False, True], ids=["onaysiz", "onayli"])
def test_kap_duzeyinde_bozuk_bolum_ikinci_onayla_da_surmez(
    boz: Callable[[Path, OrnekEk, OrnekEk, bytes], None],
    onay: bool,
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
) -> None:
    """Kullanıcı kararı: kesik, sırası bozuk ya da manifestoda olmayan girdi yedeği reddeder."""
    a, b = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, a, b)
    goruntu = _goruntu(tmp_path, a, b)
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, goruntu, (a, b), kaynak_depo)
    boz(yedek, a, b, goruntu)
    oncesi = _durum(canli_db, depo)

    with pytest.raises(backup_restore.BackupRestoreError, match="bölümü bozuk") as hata:
        _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=onay)

    assert not isinstance(hata.value, backup_restore.EkOnayiGerekli)
    assert _durum(canli_db, depo) == oncesi
    assert not _hazirlik_dizinleri(depo)


def test_bozuk_girdi_ve_kesik_bolum_birlikteyse_kap_duzeyi_kazanir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Bölüm sonuna dek okunmadan sağlam sayılmaz: bozuk girdi onayla sürdürülecek gibi durmaz."""
    _saglam, _bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    yedek.write_bytes(yedek.read_bytes()[:-1])

    with pytest.raises(backup_restore.BackupRestoreError, match="bölümü bozuk") as hata:
        _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert not isinstance(hata.value, backup_restore.EkOnayiGerekli)


# ============================================================ eksik ek: durdurmaz


def _dosyasi_yok(yol: Path) -> None:
    yol.unlink()


def _boyu_tutmuyor(yol: Path) -> None:
    yol.write_bytes(yol.read_bytes()[:-1])


@pytest.mark.parametrize("boz", [_dosyasi_yok, _boyu_tutmuyor], ids=["bulunamadi", "boyu_tutmuyor"])
def test_manifestoda_eksik_isaretli_ek_durdurmaz(
    boz: Callable[[Path], None], tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Kullanıcı kararı 05.11.2026: yedek alınırken bulunamayan ya da bozuk olan ek listelenir,
    durdurmaz: bozuk bayt taşınsa da kurtarılamaz, ikinci onayın kazancı yoktur."""
    saglam, eksik = ornek_ek(PDF), ornek_ek(PNG, owner_id="12")
    depoya_koy(kaynak_depo, saglam, eksik)
    boz(kaynak_depo / eksik.ad)

    sonuc = _geri_yukle(_tam_yedek(tmp_path, kaynak_depo, saglam, eksik), canli_db)

    assert (sonuc.dosya_raporu.eksik, sonuc.dosya_raporu.bozuk) == (1, 0)
    assert sonuc.dosya_raporu.yerine_konan == 1
    (satir,) = sonuc.dosya_raporu.ekler
    assert (satir.durum, satir.kayit_no, satir.boyut) == ("eksik", "12", len(PNG))
    assert satir.yedekte_yoktu is True
    # Plan: "yedek alınırken bulunamadı ya da bozuktu" diye listelenir; ikisi ayrı sayılmaz.
    assert sonuc.dosya_raporu.metin_satirlari() == [
        "Eksik (yedek alınırken bulunamadı ya da bozuktu) · ders yılı · no 12 · 04.11.2026 · 1 KB"
    ]
    assert sonuc.dosya_raporu.yanit()["ekler"][0]["yedekte_yoktu"] is True
    assert "yedekte_yoktu" not in sonuc.dosya_raporu.sayilar()
    assert _agac(depo) == {saglam.ad: saglam.hazir.kap}


def test_eksik_isaretli_ekin_depodaki_kopyasi_durdurmaz_dokunulmaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Plan: manifestoda `eksik` işaretli ek "yalnız listelenir": depoya bakılmaz."""
    eksik = ornek_ek()
    yedek = _tam_yedek(tmp_path, kaynak_depo, eksik)  # kaynakta dosya yok: `eksik` işaretlenir
    depoya_koy(depo, eksik)
    _bit_cevir(depo / eksik.ad)
    oncesi = _agac(depo)

    sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.dosya_raporu.eksik == 1
    assert _agac(depo) == oncesi


def test_yerel_yedekte_bulunamayan_ek_eksik_listelenir(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek(owner_id="4", uploaded_at="2026-10-30 08:00:00.123456")

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert sonuc.dosya_raporu.sayilar() == {
        "kapsam": "yerel",
        "yerine_konan": 0,
        "yetimden_donen": 0,
        "eksik": 1,
        "bozuk": 0,
        "onayla_suruldu": 0,
    }
    assert sonuc.dosya_raporu.yanit()["ekler"] == [
        {
            "durum": "eksik",
            "kayit_turu": "ders yılı",
            "kayit_no": "4",
            "yukleme_tarihi": "2026-10-30",
            "boyut": len(PDF),
            "yedekte_yoktu": False,
        }
    ]
    assert sonuc.dosya_raporu.metin_satirlari() == [
        f"Eksik · ders yılı · no 4 · 30.10.2026 · {max(1, len(PDF) // 1024)} KB"
    ]


def test_yerel_yedekte_depodaki_ek_tutuyorsa_listelenmez(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert sonuc.dosya_raporu.ekler == ()
    assert _agac(depo) == {ek.ad: ek.hazir.kap}


# ============================================================ depodaki bozuk dosya


def test_yerel_yedekte_depodaki_bozuk_dosya_durur_dokunulmaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)
    _bit_cevir(depo / ek.ad)
    yedek = _yerel_yedek(tmp_path, ek)
    oncesi = _durum(canli_db, depo)

    with pytest.raises(backup_restore.EkOnayiGerekli) as durma:
        _geri_yukle(yedek, canli_db)

    assert _durum(canli_db, depo) == oncesi
    assert durma.value.rapor.bozuk == 1

    depo_oncesi = _agac(depo)
    sonuc = _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert _agac(depo) == depo_oncesi
    assert not (depo / ds.YETIM_DIZINI).exists()
    assert (sonuc.dosya_raporu.bozuk, sonuc.dosya_raporu.onayla_suruldu) == (1, 1)


def test_tam_yedekte_depodaki_bozuk_dosya_yetime_alinir_yerine_dogrulanmis_kopya_konur(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    depoya_koy(depo, ek)
    _bit_cevir(depo / ek.ad)
    bozuk_bayt = (depo / ek.ad).read_bytes()

    sonuc = _geri_yukle(_tam_yedek(tmp_path, kaynak_depo, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    yetimde = ds.yetim_gun_dizini(depo, timezone.localdate()) / ek.ad
    assert yetimde.read_bytes() == bozuk_bayt
    assert (sonuc.dosya_raporu.yerine_konan, sonuc.dosya_raporu.bozuk) == (1, 0)


def test_depoda_dosya_yerine_dizin_duruyorsa_bozuk_sayilir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Depoda düzenli olmayan şey açılamaz, "tutmuyor" demektir; okuma süreci düşürmez."""
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    ds.dizin_kur(depo / ek.ad)

    sonuc = _geri_yukle(_tam_yedek(tmp_path, kaynak_depo, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert (ds.yetim_gun_dizini(depo, timezone.localdate()) / ek.ad).is_dir()
    assert sonuc.dosya_raporu.yerine_konan == 1


# ============================================================ yetimden dönüş


def _yetime_koy(depo: Path, gun: str, ek: OrnekEk, *, boz: bool = False) -> Path:
    dizin = ds.dizin_kur(depo / ds.YETIM_DIZINI / gun)
    ds.depoya_yaz(dizin, ek.ad, ek.hazir.kap)
    if boz:
        _bit_cevir(dizin / ek.ad)
    return dizin / ek.ad


def test_yerel_yedekte_yetimdeki_ek_geri_alinir(tmp_path: Path, canli_db: Path, depo: Path) -> None:
    ek = ornek_ek()
    kopya = _yetime_koy(depo, "2026-11-01", ek)

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert not kopya.exists()
    assert (sonuc.dosya_raporu.yetimden_donen, sonuc.dosya_raporu.eksik) == (1, 0)


def test_yetimde_en_yeni_tutan_kopya_doner_tutmayana_dokunulmaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    eski = _yetime_koy(depo, "2026-10-20", ek)
    yeni_bozuk = _yetime_koy(depo, "2026-11-01", ek, boz=True)
    bozuk_bayt = yeni_bozuk.read_bytes()

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert not eski.exists()
    assert yeni_bozuk.read_bytes() == bozuk_bayt
    assert sonuc.dosya_raporu.yetimden_donen == 1


def test_yetimde_yalniz_tutmayan_kopya_varsa_geri_alinmaz_bozuk_sayilir(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Doğrulanmamış hiçbir bayt depoya girmez. Bulunan ama tutmayan kopya bozuktur (modül başlığı)."""
    ek = ornek_ek()
    kopya = _yetime_koy(depo, "2026-11-01", ek, boz=True)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert kopya.exists()
    assert not (depo / ek.ad).exists()


def _sirali_yetime_koy(depo: Path, gun: str, ek: OrnekEk, sira: int, *, boz: bool = False) -> Path:
    """Aynı gün aynı adla yetime düşen kopya: `ds.yetime_tasi`'nın sıra ekli adı."""
    dizin = ds.dizin_kur(depo / ds.YETIM_DIZINI / gun)
    yol = dizin / f"{ek.ad}-{sira}"
    yol.write_bytes(ek.hazir.kap)
    if boz:
        _bit_cevir(yol)
    return yol


def test_sira_ekli_yetim_kopyasi_tutuyorsa_ek_doner(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Plan: "yetim/'de aranır". İlk kopya bozuk, sağlam kopya sıra ekliyse ek bozuk sayılmaz."""
    ek = ornek_ek()
    bozuk = _yetime_koy(depo, "2026-11-01", ek, boz=True)
    bozuk_bayt = bozuk.read_bytes()
    sirali = _sirali_yetime_koy(depo, "2026-11-01", ek, 1)

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert (sonuc.dosya_raporu.yetimden_donen, sonuc.dosya_raporu.bozuk) == (1, 0)
    assert bozuk.read_bytes() == bozuk_bayt
    assert sirali.read_bytes() == ek.hazir.kap  # aslına dokunulmaz, gün dizini silinirken gider
    assert not _hazirlik_dizinleri(depo)


def test_sira_ekli_kopyalarin_ilki_tutmazsa_sonraki_denenir(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    _sirali_yetime_koy(depo, "2026-11-01", ek, 1, boz=True)
    _sirali_yetime_koy(depo, "2026-11-01", ek, 2)

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert sonuc.dosya_raporu.yetimden_donen == 1


def test_yalniz_tutmayan_sira_ekli_kopya_varsa_bozuk_sayilir_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    kopya = _sirali_yetime_koy(depo, "2026-11-01", ek, 1, boz=True)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert kopya.exists()
    assert not (depo / ek.ad).exists()
    assert not _hazirlik_dizinleri(depo)


def test_baska_adin_kabi_sira_ekiyle_konmussa_tutmaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Kabın adı şifrenin bağıdır: ad değiştirilmiş kap asıl adıyla sınanınca açılmaz."""
    ek, baska = ornek_ek(PDF), ornek_ek(PNG)
    dizin = ds.dizin_kur(depo / ds.YETIM_DIZINI / "2026-11-01")
    (dizin / f"{ek.ad}-1").write_bytes(baska.hazir.kap)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert not (depo / ek.ad).exists()


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ sınaması POSIX'tedir")
def test_sira_ekli_kopya_duzenli_dosya_degilse_tutmaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    dizin = ds.dizin_kur(depo / ds.YETIM_DIZINI / "2026-11-01")
    hedef = tmp_path / "disarida"
    hedef.write_bytes(ek.hazir.kap)
    (dizin / f"{ek.ad}-1").symlink_to(hedef)
    (dizin / f"{ek.ad}-2").mkdir()

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    assert not (depo / ek.ad).exists()


# ============================================================ manifesto ve satır ayrışırsa


def test_tam_yedekte_satiri_olmayan_girdi_bozuk_sayilir_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Sarmalı olmayan kopya doğrulanamaz. Liste satırdan okunamaz, boy manifestodandır."""
    satirli, satirsiz = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, satirli, satirsiz)
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _goruntu(tmp_path, satirli), (satirli, satirsiz), kaynak_depo)

    with pytest.raises(backup_restore.EkOnayiGerekli) as durma:
        _geri_yukle(yedek, canli_db)
    assert durma.value.rapor.yanit()["ekler"] == [
        {
            "durum": "bozuk",
            "kayit_turu": geri_yukleme_ekleri.KAYDI_BULUNAMADI,
            "kayit_no": "",
            "yukleme_tarihi": None,
            "boyut": len(PNG),
            "yedekte_yoktu": False,
        }
    ]

    _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert _agac(depo) == {satirli.ad: satirli.hazir.kap}


def test_imhali_satirin_girdisi_de_dogrulanamaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    imhali = OrnekEk(ek.hazir, purged_at="2026-11-02 09:00:00")
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _goruntu(tmp_path, imhali), (ek,), kaynak_depo)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)


def test_yerel_yedekte_satiri_olmayan_girdi_bozuk_sayilir_depoya_dokunulmaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(yedek, _goruntu(tmp_path), (ek,))

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert _agac(depo) == {ek.ad: ek.hazir.kap}


def test_manifesto_ve_satirin_ozeti_ayrisirsa_kopya_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Kopya manifestoyu tutsa da satırı tutmuyorsa program onu açamazdı (`EkOzetiTutmuyor`)."""
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    goruntu = tmp_path / "goruntu.sqlite3"
    ekli_sqlite(goruntu, (ek,), isaret="yeni")
    with closing(sqlite3.connect(goruntu)) as baglanti:
        baglanti.execute("UPDATE okul_attachment SET sha256 = ?", ("0" * 64,))
        baglanti.commit()
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, goruntu.read_bytes(), (ek,), kaynak_depo)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert not (depo / ek.ad).exists()


def _boyu_sapmis_goruntu(tmp_path: Path, ek: OrnekEk) -> bytes:
    """Satırın `size`'ı sapmış görüntü; özet ve manifesto doğrudur, yalnız boy denetimi yakalar.

    `replace(hazir, size=...)` olmaz: `OrnekEk.girdi` boyu ondan alır, manifesto da saparsa
    `ek_denetle` yakalar, satırın denetimi sınanmaz.
    """
    goruntu = tmp_path / "goruntu.sqlite3"
    ekli_sqlite(goruntu, (ek,), isaret="yeni")
    with closing(sqlite3.connect(goruntu)) as baglanti:
        baglanti.execute("UPDATE okul_attachment SET size = size + 1")
        baglanti.commit()
    return goruntu.read_bytes()


def test_tam_yedekte_satirin_boyu_tutmuyorsa_kopya_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _boyu_sapmis_goruntu(tmp_path, ek), (ek,), kaynak_depo)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert not (depo / ek.ad).exists()


def test_yerel_yedekte_satirin_boyu_tutmuyorsa_yetimdeki_kopya_donmez(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    kopya = _yetime_koy(depo, "2026-11-01", ek)
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(yedek, _boyu_sapmis_goruntu(tmp_path, ek), (ek,))

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert kopya.exists()
    assert not (depo / ek.ad).exists()


def test_kopya_satiri_tutsa_da_manifestoyu_tutmuyorsa_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Ayrışmanın öteki yönü: manifesto bölümün bütünlük kaynağıdır, satır tek başına yetmez."""
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    baska_ozetli = OrnekEk(replace(ek.hazir, sha256="0" * 64))
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _goruntu(tmp_path, ek), (baska_ozetli,), kaynak_depo)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert not (depo / ek.ad).exists()


def test_satiri_olup_manifestoda_olmayan_ek_yerel_yedekteki_gibi_aranir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Tam yedekte de: dosya bölümünde kopyası yoktur, depoda ve yetimde aranır."""
    yerinde, yetimde, kayip = ornek_ek(PDF), ornek_ek(PNG), ornek_ek(PDF, owner_id="21")
    depoya_koy(depo, yerinde)
    _yetime_koy(depo, "2026-11-01", yetimde)
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, _goruntu(tmp_path, yerinde, yetimde, kayip), (), kaynak_depo)

    sonuc = _geri_yukle(yedek, canli_db)

    assert (sonuc.dosya_raporu.yetimden_donen, sonuc.dosya_raporu.eksik) == (1, 1)
    assert sonuc.dosya_raporu.ekler[0].kayit_no == "21"
    assert (depo / yerinde.ad).is_file() and (depo / yetimde.ad).is_file()


def test_adi_desene_uymayan_satir_yol_kurmaz_eksik_sayilir(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Program dışından değiştirilmiş veritabanı: `../guvenlik.json` gibi bir ad yol kuramaz."""
    goruntu = tmp_path / "goruntu.sqlite3"
    ekli_sqlite(goruntu, (ornek_ek(),), isaret="yeni")
    with closing(sqlite3.connect(goruntu)) as baglanti:
        baglanti.execute("UPDATE okul_attachment SET stored_name = ?", ("../guvenlik.json",))
        baglanti.commit()
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(yedek, goruntu.read_bytes(), ())

    sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.dosya_raporu.eksik == 1


def test_ek_tablosu_olmayan_goruntude_manifesto_bossa_rapor_bostur(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(
        yedek, yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[]), ()
    )

    sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.dosya_raporu.ekler == ()
    assert not depo.exists()


def test_ek_tablosu_olmayan_goruntude_manifestodaki_ek_dogrulanamaz(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Tablo yoksa satır da yoktur; manifesto okuyucusuyla aynı kural (`desktop.backup`)."""
    yedek = _yedek(tmp_path)
    goruntu = yetkili_sqlite(tmp_path / "goruntu.sqlite3", dek=TEST_DEK, hesaplar=[])
    yerel_yedek_yaz(yedek, goruntu, (ornek_ek(),))

    with pytest.raises(backup_restore.EkOnayiGerekli) as durma:
        _geri_yukle(yedek, canli_db)

    assert durma.value.rapor.bozuk == 1


def test_ek_kayitlari_okunamayan_goruntu_manifesto_doluysa_reddedilir(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    """Sütunu olmayan tablo: doğrulama yapılamaz; yedek bozuk sayılır, onay istenmez."""
    goruntu = tmp_path / "goruntu.sqlite3"
    yetkili_sqlite(goruntu, dek=TEST_DEK, hesaplar=[], isaret="yeni")
    with closing(sqlite3.connect(goruntu)) as baglanti:
        baglanti.execute("CREATE TABLE okul_attachment (stored_name text)")
        baglanti.commit()
    yedek = _yedek(tmp_path)
    yerel_yedek_yaz(yedek, goruntu.read_bytes(), (ornek_ek(),))
    oncesi = _durum(canli_db, depo)

    with pytest.raises(backup_restore.BackupRestoreError, match="kayıtları okunamadı") as hata:
        _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert not isinstance(hata.value, backup_restore.EkOnayiGerekli)
    assert _durum(canli_db, depo) == oncesi


def test_tanimadigi_sahip_turu_kayit_yazar_yerel_gunu_bicimsizse_tarih_yok(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    ek = ornek_ek(owner_type="baska.Model", uploaded_at="bicimsiz")

    sonuc = _geri_yukle(_yerel_yedek(tmp_path, ek), canli_db)

    (satir,) = sonuc.dosya_raporu.ekler
    assert (satir.kayit_turu, satir.yukleme_tarihi) == ("Kayıt", None)
    assert "tarih yok" in satir.metin()


# ============================================================ yetki ve sıra


def _muhasipli(tmp_path: Path, ad: str) -> Path:
    yol = tmp_path / ad
    yetkili_sqlite(
        yol, dek=TEST_DEK, hesaplar=[HesapSatiri(TEST_HESAP_ID, TEST_TANITICI, role="muhasip")]
    )
    return yol


@pytest.mark.parametrize("guncel_okunur", [True, False], ids=["guncel", "goruntu"])
def test_yetkiden_once_dosya_yazilmaz(
    guncel_okunur: bool, tmp_path: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Plan: yetki yalnız veritabanı baytlarıyla verilir. Ret, güncel veritabanında da görüntüde de
    `dosyalar/`'a, `.tmp`'ye ve hazırlık dizinine dokunmaz."""
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    goruntu = _muhasipli(tmp_path, "goruntu.sqlite3")
    ek_tablosu_ekle(goruntu, (ek,))
    yedek = _yedek(tmp_path)
    tam_yedek_kur(yedek, goruntu.read_bytes(), (ek,), kaynak_depo)
    canli = tmp_path / "canli"
    canli.mkdir()
    canli_db = canli / "db.sqlite3"
    canli_db.write_bytes(
        _muhasipli(tmp_path, "guncel.sqlite3").read_bytes() if guncel_okunur else b"xx"
    )
    oncesi = _agac(canli)

    with pytest.raises(backup_restore.GeriYuklemeYetkisiz):
        backup_restore.restore_database(
            yedek, canli_db, hesap=TEST_TANITICI, password=TEST_PAROLA, ekler_olmadan_surdur=True
        )

    assert not depo.exists()
    assert {ad: bayt for ad, bayt in _agac(canli).items() if ad == "db.sqlite3"} == {
        "db.sqlite3": oncesi["db.sqlite3"]
    }
    assert not [ad for ad in _agac(canli) if ".tmp" in ad or "db-onceki" in ad]


def test_ozet_onarimi_dosya_bolumunden_once_kosar_yerlesim_takastan_once(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan "Sıra": `.tmp` ve özet onarımı → dosya bölümü → yerleşim → takas."""
    sira: list[str] = []
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    yedek = _tam_yedek(tmp_path, kaynak_depo, ek)
    asil_onarim = ozet_onarimi.ozetleri_onar
    asil_hazirla = geri_yukleme_ekleri.EkYerlesimi.hazirla
    asil_koy = geri_yukleme_ekleri.EkYerlesimi.yerine_koy

    def onarim(**kw: Any) -> Any:
        sira.append("onarim")
        assert kw["yeni_db"].is_file()
        return asil_onarim(**kw)

    def hazirla(self: Any, gecici: Path) -> None:
        sira.append("hazirla")
        asil_hazirla(self, gecici)

    def yerine_koy(self: Any) -> None:
        sira.append("yerlesim")
        assert b"yeni" not in canli_db.read_bytes()  # takas henüz yapılmadı
        asil_koy(self)

    monkeypatch.setattr(ozet_onarimi, "ozetleri_onar", onarim)
    monkeypatch.setattr(geri_yukleme_ekleri.EkYerlesimi, "hazirla", hazirla)
    monkeypatch.setattr(geri_yukleme_ekleri.EkYerlesimi, "yerine_koy", yerine_koy)

    _geri_yukle(yedek, canli_db)

    assert sira == ["onarim", "hazirla", "yerlesim"]


# ============================================================ takas düşerse, kesinti


def _takas_duser(monkeypatch: pytest.MonkeyPatch) -> None:
    """`.tmp` yerine konamaz (Windows'ta başka bir iş parçacığının açık bağlantısı)."""
    asil = Path.replace

    def replace(self: Path, hedef: Any) -> Path:
        if self.name.endswith(".yeni.tmp"):
            raise PermissionError("erişim reddedildi")
        return asil(self, hedef)

    monkeypatch.setattr(Path, "replace", replace)


def test_takas_duserse_yerine_konanlar_geri_alinir_veritabani_yerine_doner(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    konan, degisen = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, konan, degisen)
    depoya_koy(depo, degisen)
    _bit_cevir(depo / degisen.ad)
    wal = canli_db.with_name(canli_db.name + "-wal")
    wal.write_bytes(b"wal-kalintisi")
    yedek = _tam_yedek(tmp_path, kaynak_depo, konan, degisen)
    db_bayt, depo_oncesi = canli_db.read_bytes(), _agac(depo)
    _takas_duser(monkeypatch)

    with pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"):
        _geri_yukle(yedek, canli_db)

    assert canli_db.read_bytes() == db_bayt
    assert wal.read_bytes() == b"wal-kalintisi"
    assert _agac(depo) == depo_oncesi
    assert not _hazirlik_dizinleri(depo)
    assert not list(canli_db.parent.glob("db-onceki-*"))


def test_takas_duserse_yetimden_donen_yerine_doner(
    tmp_path: Path, canli_db: Path, depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ek = ornek_ek()
    kopya = _yetime_koy(depo, "2026-11-01", ek)
    yedek = _yerel_yedek(tmp_path, ek)
    _takas_duser(monkeypatch)

    with pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"):
        _geri_yukle(yedek, canli_db)

    assert kopya.read_bytes() == ek.hazir.kap
    assert not (depo / ek.ad).exists()


def test_takas_duserse_sira_ekli_kopya_yetimde_kalir_depoya_girmez(
    tmp_path: Path, canli_db: Path, depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ek = ornek_ek()
    kopya = _sirali_yetime_koy(depo, "2026-11-01", ek, 1)
    yedek = _yerel_yedek(tmp_path, ek)
    _takas_duser(monkeypatch)

    with pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"):
        _geri_yukle(yedek, canli_db)

    assert kopya.read_bytes() == ek.hazir.kap
    assert not (depo / ek.ad).exists()
    assert not _hazirlik_dizinleri(depo)


def test_yerlesim_yarida_duserse_yapilanlar_geri_alinir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, a, b)
    yedek = _tam_yedek(tmp_path, kaynak_depo, a, b)
    oncesi = _durum(canli_db, depo)
    asil = ds.yerine_tasi
    cagri = 0

    def ikincide_duser(kaynak: Path, hedef: Path) -> None:
        nonlocal cagri
        cagri += 1
        if cagri == 2:
            raise OSError("disk dolu")
        asil(kaynak, hedef)

    monkeypatch.setattr(ds, "yerine_tasi", ikincide_duser)

    with pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"):
        _geri_yukle(yedek, canli_db)

    assert _durum(canli_db, depo) == oncesi


def test_geri_alinamayan_ek_hatayi_ortmez_kalanlar_cevrilir(
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    a, b = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, a, b)
    yedek = _tam_yedek(tmp_path, kaynak_depo, a, b)
    _takas_duser(monkeypatch)
    asil = os.replace
    ilk_geri_alma = True

    def duser(kaynak: Any, hedef: Any) -> None:
        nonlocal ilk_geri_alma
        if ds.HAZIRLIK_ONEKI in str(hedef) and ilk_geri_alma:
            ilk_geri_alma = False
            raise PermissionError("kilitli")
        asil(kaynak, hedef)

    monkeypatch.setattr(os, "replace", duser)

    with (
        caplog.at_level(logging.WARNING, logger="oab_defteri.restore"),
        pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"),
    ):
        _geri_yukle(yedek, canli_db)

    assert len(_agac(depo)) == 1  # biri satırsız kaldı; açılış taraması toplar
    assert "geri alınamadı" in caplog.text
    assert a.ad not in caplog.text and b.ad not in caplog.text


# ============================================================ kesinleşme (modül başlığı)


def _takastan_sonra_yan_dosya_silinemez(
    monkeypatch: pytest.MonkeyPatch, canli_db: Path, hata: BaseException
) -> None:
    """`.yeni.tmp-shm` takastan sonra silinemez (Windows'ta virüs tarayıcısı tutuyor).

    Yalnız kenara alınan dosya oluştuktan sonra: takastan önceki aynı silme (özet onarımı) ayrı koldur.
    """
    asil = Path.unlink

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.endswith(".yeni.tmp-shm") and list(canli_db.parent.glob("db-onceki-*")):
            raise hata
        asil(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)


def _ekli_tam_yedek(tmp_path: Path, kaynak_depo: Path, depo: Path) -> tuple[OrnekEk, OrnekEk, Path]:
    """Biri yerine konacak, biri depodaki bozuk kopyanın yerine geçecek iki ekli tam yedek."""
    konan, degisen = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, konan, degisen)
    depoya_koy(depo, degisen)
    _bit_cevir(depo / degisen.ad)
    return konan, degisen, _tam_yedek(tmp_path, kaynak_depo, konan, degisen)


def _geri_yuklenen_isaret(canli_db: Path) -> str:
    with closing(sqlite3.connect(canli_db)) as baglanti:
        return str(baglanti.execute("SELECT deger FROM kayit").fetchone()[0])


def test_takastan_sonra_yan_dosya_silinemezse_ekler_yerinde_kalir_not_yazilir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plan: takas tek kesinleşme noktasıdır. Kesinleşmiş takas başarısızlık gibi işlenmez."""
    konan, degisen, yedek = _ekli_tam_yedek(tmp_path, kaynak_depo, depo)
    _takastan_sonra_yan_dosya_silinemez(monkeypatch, canli_db, PermissionError("tutuluyor"))

    sonuc = _geri_yukle(yedek, canli_db)

    assert _geri_yuklenen_isaret(canli_db) == "yeni"
    assert (depo / konan.ad).read_bytes() == konan.hazir.kap
    assert (depo / degisen.ad).read_bytes() == degisen.hazir.kap
    assert sonuc.dosya_raporu.yerine_konan == 2
    assert sonuc.old_db_path is not None and sonuc.old_db_path.is_file()
    assert _not()["geri_yuklemeler"][0]["dosyalar"]["yerine_konan"] == 2
    assert canli_db.with_name(canli_db.name + ".yeni.tmp-shm").exists()  # artığı açılış toplar


def test_takastan_once_yan_dosya_silinemezse_asil_ileti_kalir(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Artığın silinememesi durma kararını sunucu hatasına çevirmez (ikinci onay yolu kapanırdı)."""
    _saglam, _bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    asil_hazirla = geri_yukleme_ekleri.EkYerlesimi.hazirla
    asil_unlink = Path.unlink
    hazir = False

    def hazirla(self: Any, gecici: Path) -> None:
        nonlocal hazir
        asil_hazirla(self, gecici)
        hazir = True

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if hazir and ".yeni.tmp" in self.name:
            raise PermissionError("tutuluyor")
        asil_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(geri_yukleme_ekleri.EkYerlesimi, "hazirla", hazirla)
    monkeypatch.setattr(Path, "unlink", unlink)

    with pytest.raises(backup_restore.EkOnayiGerekli):
        _geri_yukle(yedek, canli_db)

    assert _geri_yuklenen_isaret(canli_db) == "onceki"


def test_onceki_denemeden_kalan_yan_dosya_silinemezse_deneme_turkce_iletiyle_duser(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Artık kaldığı sürece ikinci onay ham hataya düşmez; veritabanına dokunulmaz."""
    _saglam, _bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    artik = canli_db.with_name(canli_db.name + ".yeni.tmp")
    artik.write_bytes(b"artik")
    asil_unlink = Path.unlink

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if self == artik:
            raise PermissionError(13, "tutuluyor", str(self))
        asil_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)

    with pytest.raises(backup_restore.BackupRestoreError, match="Geri yükleme yazılamadı") as hata:
        _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    assert str(artik) not in str(hata.value)
    assert _geri_yuklenen_isaret(canli_db) == "onceki"


def test_takas_olduktan_sonra_kesilirse_yerlesim_geri_alinmaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yeni veritabanı eklerin satırlarını taşır: dosyalar geri çevrilirse kayıtlar "dosya yok" derdi."""
    konan, degisen, yedek = _ekli_tam_yedek(tmp_path, kaynak_depo, depo)
    _takastan_sonra_yan_dosya_silinemez(monkeypatch, canli_db, _Olduruldu())

    with pytest.raises(_Olduruldu):
        _geri_yukle(yedek, canli_db)

    assert _geri_yuklenen_isaret(canli_db) == "yeni"
    assert (depo / konan.ad).read_bytes() == konan.hazir.kap
    assert (depo / degisen.ad).read_bytes() == degisen.hazir.kap


def _damga_silinemez(monkeypatch: pytest.MonkeyPatch, gizli: str) -> None:
    asil = Path.unlink

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name == VERSION_STAMP_FILE_NAME:
            raise OSError(gizli)
        asil(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)


def _guvenlik_dosyasi_yazilamaz(monkeypatch: pytest.MonkeyPatch, gizli: str) -> None:
    monkeypatch.setattr(backup_restore, "_ensure_state_file", _duser(gizli))


def _yedekleme_dosyasi_yazilamaz(monkeypatch: pytest.MonkeyPatch, gizli: str) -> None:
    monkeypatch.setattr(backup_restore, "ensure_public_config", _duser(gizli))


def _duser(gizli: str) -> Callable[..., Any]:
    def duser(*_a: Any, **_k: Any) -> Any:
        raise OSError(gizli)

    return duser


@pytest.mark.parametrize(
    "boz",
    [_guvenlik_dosyasi_yazilamaz, _yedekleme_dosyasi_yazilamaz, _damga_silinemez],
    ids=["guvenlik_json", "yedekleme_json", "surum_damgasi"],
)
def test_takastan_sonraki_adim_duserse_geri_yukleme_basarilidir_oteki_adimlar_kosar(
    boz: Callable[[pytest.MonkeyPatch, str], None],
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    konan, _degisen, yedek = _ekli_tam_yedek(tmp_path, kaynak_depo, depo)
    damga = canli_db.parent / VERSION_STAMP_FILE_NAME
    damga.write_text("{}", encoding="utf-8")
    yedekleme = tmp_path / "yazilan-yedekleme"
    asil = backup_crypto.ensure_public_config

    def izleyen(*args: Any, **kwargs: Any) -> Any:
        yedekleme.write_text("yazildi", encoding="utf-8")
        return asil(*args, **kwargs)

    monkeypatch.setattr(backup_restore, "ensure_public_config", izleyen)
    gizli = f"erişilemedi: {canli_db}"
    boz(monkeypatch, gizli)

    with caplog.at_level(logging.WARNING, logger="oab_defteri.restore"):
        sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.dosya_raporu.yerine_konan == 2
    assert _geri_yuklenen_isaret(canli_db) == "yeni"
    assert (depo / konan.ad).is_file()
    assert _not()["geri_yuklemeler"]
    assert "yazılamadı" in caplog.text or "silinemedi" in caplog.text
    assert gizli not in caplog.text
    if boz is not _damga_silinemez:
        assert not damga.exists()
    if boz is _guvenlik_dosyasi_yazilamaz:
        assert yedekleme.exists()


def test_yeni_veritabani_kenara_almadan_once_diske_iner_dizin_takastan_sonra_esitlenir(
    tmp_path: Path, canli_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tasarım §4.3 tehdit 18: takas kesinleşme noktasıdır, ek dosyaları gibi diske inmelidir. Süreç
    ölümü bundan etkilenmez, elektrik kesintisi etkilenir."""
    sira: list[str] = []
    temp = canli_db.with_name(canli_db.name + backup_restore.YENI_VERITABANI_EKI)
    asil_fsync, asil_replace, asil_esitle = os.fsync, Path.replace, ds.dizini_esitle

    def fsync(tanitici: int) -> None:
        if temp.exists() and os.path.samestat(os.fstat(tanitici), temp.stat()):
            sira.append("fsync")
        asil_fsync(tanitici)

    def replace(self: Path, hedef: Any) -> Path:
        if self == canli_db:
            sira.append("kenara")
        elif self == temp:
            sira.append("takas")
        return asil_replace(self, hedef)

    def esitle(dizin: Path) -> None:
        if dizin == canli_db.parent:
            sira.append("dizin")
        asil_esitle(dizin)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr(ds, "dizini_esitle", esitle)

    _geri_yukle(_yerel_yedek(tmp_path), canli_db)

    assert sira == ["fsync", "kenara", "takas", "dizin"]


def test_yeni_veritabani_diske_indirilemezse_hicbir_sey_degismez(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _konan, _degisen, yedek = _ekli_tam_yedek(tmp_path, kaynak_depo, depo)
    oncesi = _durum(canli_db, depo)
    monkeypatch.setattr(ds, "dosyayi_esitle", _duser("disk hatası"))

    with pytest.raises(backup_restore.BackupRestoreError, match="yazılamadı"):
        _geri_yukle(yedek, canli_db)

    assert _durum(canli_db, depo) == oncesi
    assert not list(canli_db.parent.glob("db-onceki-*"))


def test_takastan_sonra_dizin_esitlenemezse_takas_basarisiz_sayilmaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    konan, _degisen, yedek = _ekli_tam_yedek(tmp_path, kaynak_depo, depo)
    asil = ds.dizini_esitle

    def esitle(dizin: Path) -> None:
        if dizin == canli_db.parent:
            raise OSError("dizin eşitlenemedi")
        asil(dizin)

    monkeypatch.setattr(ds, "dizini_esitle", esitle)

    sonuc = _geri_yukle(yedek, canli_db)

    assert sonuc.old_db_path is not None
    assert _geri_yuklenen_isaret(canli_db) == "yeni"
    assert (depo / konan.ad).is_file()
    assert _not()["geri_yuklemeler"]


class _Olduruldu(BaseException):
    """Süreç öldürüldü: temizlik çalışmaz (bkz. `_olu_surec`)."""


def _olu_surec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(geri_yukleme_ekleri.EkYerlesimi, "geri_al", lambda self: None)
    monkeypatch.setattr(geri_yukleme_ekleri.EkYerlesimi, "temizle", lambda self: None)


def _n_inci_cagrida_oldur(monkeypatch: pytest.MonkeyPatch, sahip_: Any, ad: str, n: int) -> None:
    asil = getattr(sahip_, ad)
    cagri = 0

    def oldurur(*args: Any, **kwargs: Any) -> Any:
        nonlocal cagri
        cagri += 1
        if cagri == n:
            raise _Olduruldu
        return asil(*args, **kwargs)

    monkeypatch.setattr(sahip_, ad, oldurur)


@pytest.mark.parametrize(
    ("ad", "n"),
    [
        ("akisla_yaz", 1),
        ("akisla_yaz", 2),
        ("yerine_tasi", 1),
        ("yerine_tasi", 2),
        ("yerine_tasi", 3),
    ],
    ids=["ilk_girdi", "ikinci_girdi", "yetim_tasimasi", "ilk_yerlesim", "ikinci_yerlesim"],
)
def test_kesinti_kayip_uretmez_yeniden_deneme_sonuclanir(
    ad: str,
    n: int,
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan: geçiş günlüğü tutulmaz, kesinti yalnız satırsız dosya üretir, kayıp üretmez. Süreç
    takastan önce öldürülürse eski veritabanı yerindedir, kapları aynı adla açılır; hazırlık dizini
    artıktır, yeniden deneme onu görmez ve sonuçlanır."""
    konan, degisen = ornek_ek(PDF), ornek_ek(PNG)
    depoya_koy(kaynak_depo, konan, degisen)
    depoya_koy(depo, degisen)
    _bit_cevir(depo / degisen.ad)
    bozuk_bayt = (depo / degisen.ad).read_bytes()
    yedek = _tam_yedek(tmp_path, kaynak_depo, konan, degisen)
    db_bayt = canli_db.read_bytes()

    with monkeypatch.context() as yama:
        _olu_surec(yama)
        _n_inci_cagrida_oldur(yama, ds, ad, n)
        with pytest.raises(_Olduruldu):
            _geri_yukle(yedek, canli_db)

    assert canli_db.read_bytes() == db_bayt
    assert not list(canli_db.parent.glob("db-onceki-*"))
    baytlar = [
        yol.read_bytes()
        for yol in depo.rglob(degisen.ad)
        if yol.is_file() and ds.HAZIRLIK_ONEKI not in str(yol)
    ]
    assert bozuk_bayt in baytlar or degisen.hazir.kap in baytlar  # dosyası bir yerde durur

    _geri_yukle(yedek, canli_db)

    assert (depo / konan.ad).read_bytes() == konan.hazir.kap
    assert (depo / degisen.ad).read_bytes() == degisen.hazir.kap


# ============================================================ not, iz satırı, günlük


def test_geri_yukleme_notu_kisisiz_sayilari_tasir_liste_ve_ad_tasimaz(
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    kaynak_depo: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _saglam, bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)

    with caplog.at_level(logging.INFO, logger="oab_defteri.restore"):
        _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)

    (kayit,) = _not()["geri_yuklemeler"]
    assert kayit["dosyalar"] == {
        "kapsam": "tam",
        "yerine_konan": 1,
        "yetimden_donen": 0,
        "eksik": 0,
        "bozuk": 1,
        "onayla_suruldu": 1,
    }
    metin = json.dumps(_not(), ensure_ascii=False)
    assert "Masalcıoğlu" not in metin and "ders yılı" not in metin and bozuk.ad not in metin
    assert "Masalcıoğlu" not in caplog.text and bozuk.ad not in caplog.text


def test_notun_sayilari_iz_satirina_gecer_satir_ad_ve_liste_tasimaz(
    tmp_path: Path, canli_db: Path, depo: Path, kaynak_depo: Path
) -> None:
    """Gerçek geri yüklemenin notu izin kapısından geçer (`denetim_izi.izinli_degerler`)."""
    _saglam, bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    _geri_yukle(yedek, canli_db, ekler_olmadan_surdur=True)
    (kayit,) = _not()["geri_yuklemeler"]

    _kimlik, alanlar, degerler = iz_dogrulama._geri_yukleme_satiri(kayit)

    assert {ad: cift[1] for ad, cift in degerler.items() if ad in kayit["dosyalar"]} == {
        "kapsam": "tam",
        "yerine_konan": 1,
        "yetimden_donen": 0,
        "eksik": 0,
        "bozuk": 1,
        "onayla_suruldu": 1,
    }
    assert set(kayit["dosyalar"]) <= set(alanlar)
    metin = json.dumps(degerler, ensure_ascii=False)
    assert "Masalcıoğlu" not in metin and bozuk.ad not in metin


@pytest.mark.parametrize(
    ("ad", "beklenen"),
    [
        ("gunluk-2026-11-04.odbak", "gunluk-2026-11-04.odbak"),
        ("oab-defteri-yedek-2026-11-04-101530.odbak", "oab-defteri-yedek-2026-11-04-101530.odbak"),
        ("Uydurgül Masalcıoğlu yedeği.odbak", None),
        ("gunluk-2026-11-04-Masalcıoğlu.odbak", None),
    ],
    ids=["gunluk", "indirilen", "serbest", "onekli_serbest"],
)
def test_yedegin_adi_nota_ve_gunluge_yalniz_programin_adiysa_gecer(
    ad: str,
    beklenen: str | None,
    tmp_path: Path,
    canli_db: Path,
    depo: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R1: seçilen dosyanın adı serbest metindir; `.tmp`'ye değil özgün ada bakılır."""
    yedek = tmp_path / ad
    yerel_yedek_yaz(yedek, _goruntu(tmp_path), ())

    with caplog.at_level(logging.INFO, logger="oab_defteri.restore"):
        _geri_yukle(yedek, canli_db)

    assert _not()["geri_yuklemeler"][0]["yedek"] == beklenen
    assert "Masalcıoğlu" not in caplog.text
    assert (ad in caplog.text) is (beklenen is not None)


def test_yuklenen_dosyanin_ozgun_adi_gecici_adin_yerine_gecer(
    tmp_path: Path, canli_db: Path, depo: Path
) -> None:
    gecici = tmp_path / ".yukleme-0123.tmp"
    yerel_yedek_yaz(gecici, _goruntu(tmp_path), ())

    _geri_yukle(gecici, canli_db, yedek_adi="gunluk-2026-11-04.odbak")
    assert _not()["geri_yuklemeler"][-1]["yedek"] == "gunluk-2026-11-04.odbak"

    _geri_yukle(gecici, canli_db, yedek_adi="Uydurgül.odbak")
    assert _not()["geri_yuklemeler"][-1]["yedek"] is None
    assert ".yukleme" not in json.dumps(_not())


def test_yedek_acilamazsa_ileti_yol_tasimaz(tmp_path: Path, canli_db: Path) -> None:
    """İleti konsolda günlüğe düşer: kullanıcının verdiği yol serbest metindir (R1)."""
    with pytest.raises(backup_restore.BackupRestoreError) as hata:
        _geri_yukle(tmp_path / "Uydurgül.odbak", canli_db)

    assert "okunamadı" in str(hata.value)
    assert "Uydurgül" not in str(hata.value)


def test_kapsam_baslikten_okunur_muhurlu_bolume_inilmez(
    tmp_path: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    tam = _tam_yedek(tmp_path, kaynak_depo, ek)
    monkeypatch.setattr(
        backup_restore, "muhurlu_bolumu_ac", lambda *a: pytest.fail("mühür açılmamalı")
    )

    assert backup_restore.inspect_backup(tam).kapsam == KAPSAM_TAM


def test_yazici_ve_okuyucunun_manifestosu_ayni_ekleri_soyler(
    tmp_path: Path, kaynak_depo: Path
) -> None:
    """Test yardımcısı gerçek yazıcıdır: kurduğu kap `decrypt_bytes`'tan da geçer."""
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    yedek = _tam_yedek(tmp_path, kaynak_depo, ek)

    icerik = decrypt_bytes(yedek.read_bytes(), TEST_DEK)

    assert icerik.manifesto.dosyalar == (ManifestoGirdisi(ek.ad, ek.hazir.size, ek.hazir.sha256),)


# ============================================================ restore_backup komutu


@pytest.fixture
def komut_ortami(canli_db: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setitem(settings.DATABASES["default"], "NAME", str(canli_db))
    return canli_db


def _komut(yedek: Path, *bayraklar: str) -> str:
    cikti = StringIO()
    call_command(
        "restore_backup",
        str(yedek),
        "--yes",
        "--recovery-key",
        TEST_KURTARMA_ANAHTARI,
        *bayraklar,
        stdout=cikti,
    )
    return cikti.getvalue()


def test_komut_yalniz_basligi_okur_onayda_kapsami_soyler(
    tmp_path: Path, komut_ortami: Path, kaynak_depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ek = ornek_ek()
    depoya_koy(kaynak_depo, ek)
    tam = _tam_yedek(tmp_path, kaynak_depo, ek)
    asil = Path.read_bytes

    def yedegi_okumaz(yol: Path) -> bytes:
        assert yol != tam, "komut yedeği bütünüyle okumamalı"
        return asil(yol)

    monkeypatch.setattr(Path, "read_bytes", yedegi_okumaz)

    cikti = _komut(tam)

    assert "Kapsam: kayıtlar, ekler ve üretilen evrak" in cikti


def test_komut_yerel_yedegin_kapsamini_soyler(tmp_path: Path, komut_ortami: Path) -> None:
    assert "Kapsam: yalnız kayıtlar; ekler bu bilgisayardan alınır" in _komut(
        _yerel_yedek(tmp_path)
    )


def test_komut_bozuk_ekte_liste_yazar_durur_yes_onay_sayilmaz(
    tmp_path: Path, komut_ortami: Path, depo: Path, kaynak_depo: Path
) -> None:
    _saglam, _bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)
    oncesi = _durum(komut_ortami, depo)
    cikti = StringIO()

    with pytest.raises(CommandError, match="--ekler-olmadan-surdur"):
        call_command(
            "restore_backup",
            str(yedek),
            "--yes",
            "--recovery-key",
            TEST_KURTARMA_ANAHTARI,
            stdout=cikti,
        )

    assert "Bozuk · ders yılı · no 9 · 04.11.2026" in cikti.getvalue()
    assert _durum(komut_ortami, depo) == oncesi


def test_komut_acik_bayrakla_ekler_olmadan_surer_listeyi_yazar(
    tmp_path: Path, komut_ortami: Path, depo: Path, kaynak_depo: Path
) -> None:
    saglam, bozuk, yedek = _bozuk_tam_yedek(tmp_path, kaynak_depo)

    cikti = _komut(yedek, "--ekler-olmadan-surdur")

    assert "Geri yükleme tamamlandı." in cikti
    assert "Bozuk · ders yılı · no 9" in cikti
    assert (depo / saglam.ad).is_file() and not (depo / bozuk.ad).exists()
