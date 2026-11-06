"""Yetim taraması ve açılıştaki artık temizliği (tasarım §4.4.7; plan F1b-3 "Geri yükleme").

Kanca `apps.okul.masaustu_kanca`'dadır, saf parçalar `shared.dosya_sifreleme`'dedir. Masaüstü
kabuğunun çağırdığı yer ve kipler `desktop/tests/test_main.py`'de, yetim silmesi
`desktop/tests/test_backup_saklama.py`'de sınanır.

Asıl tehlike korumasız taramadır: boş bir veritabanı bütün depoyu yetime gönderir, 14 gün sonra da
silinir. Bu yüzden ilk bölüm dosyanın KALDIĞINI sınar. Ekler ve adlar uydurmadır
(`geri_yukleme_ortak`).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from desktop import main as masaustu
from desktop.backup import GORUNTU_DIZINI_ONEKI
from desktop.paths import ENV_APP_HOME, resolve_app_paths
from django.conf import settings
from django.db import connection, transaction

from apps.okul import denetim_izi, iz_dogrulama, iz_durumu, masaustu_kanca
from apps.okul.models import (
    AttachmentSensitivity,
    AuditAction,
    AuditTrail,
    SchoolConfig,
    SchoolYear,
)
from apps.okul.oturum import OTURUM
from apps.okul.services import (
    app_password,
    backup_restore,
    dosya_deposu,
    geri_yukleme_notu,
    geri_yukleme_yetkisi,
    live_restore,
)
from apps.okul.services import school_year as school_year_service
from apps.okul.tests.geri_yukleme_ortak import (
    OZGUN_AD,
    PDF,
    PNG,
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
    varsayilan_yazar,
)
from shared import crypto
from shared import dosya_sifreleme as ds

GUN = date(2026, 3, 9)
#: Geçerli depo adı biçiminde uydurma ad (artıkların gövdesi).
HEX = "ab" * 16


@pytest.fixture
def depo() -> Path:
    """Programın dosya deposu (`guvenlik_ortami` testine özel)."""
    return ds.dizin_kur(Path(settings.DOSYA_DEPOSU_DIR))


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """Okul kartı ve parmak izi dolu, eki olmayan veritabanı."""
    return _veritabani(tmp_path)


def _veritabani(tmp_path: Path, *ekler: OrnekEk, **secenekler: Any) -> Path:
    yol = tmp_path / "canli" / "db.sqlite3"
    yol.parent.mkdir(exist_ok=True)
    yetkili_sqlite(yol, dek=TEST_DEK, hesaplar=[], wal=False, **secenekler)
    ek_tablosu_ekle(yol, ekler)
    return yol


def _agac(kok: Path) -> dict[str, bytes | None]:
    """Dizindeki her dosya ve dizin; dizinin değeri None."""
    return {
        str(yol.relative_to(kok)): yol.read_bytes() if yol.is_file() else None
        for yol in sorted(kok.rglob("*"))
    }


def _tara(db: Path, depo: Path) -> int:
    return masaustu_kanca.yetim_taramasi(db, depo, gun=GUN)


def _yetimde(depo: Path, ek: OrnekEk) -> Path:
    return ds.yetim_gun_dizini(depo, GUN) / ek.ad


# ============================================================ koruma: dosya taşınmaz


def _tablosuz(tmp_path: Path) -> Path:
    """Göç koşmamış veritabanı: tablolar yok."""
    yol = tmp_path / "bos.sqlite3"
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE kayit (deger TEXT)")
        baglanti.commit()
    return yol


def _ek_tablosu_yok(tmp_path: Path) -> Path:
    yol = tmp_path / "ek-yok.sqlite3"
    yetkili_sqlite(yol, dek=TEST_DEK, hesaplar=[], wal=False)
    return yol


def _kart_tablosu_yok(tmp_path: Path) -> Path:
    yol = _veritabani(tmp_path)
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("DROP TABLE okul_schoolconfig")
        baglanti.commit()
    return yol


def _bozuk_dosya(tmp_path: Path) -> Path:
    yol = tmp_path / "bozuk.sqlite3"
    yol.write_bytes(b"SQLite degil" * 512)
    return yol


@pytest.mark.parametrize(
    "kur",
    [
        pytest.param(_tablosuz, id="tablo_yok"),
        pytest.param(_ek_tablosu_yok, id="ek_tablosu_yok"),
        pytest.param(_kart_tablosu_yok, id="kart_tablosu_yok"),
        pytest.param(_bozuk_dosya, id="bozuk_dosya"),
        pytest.param(lambda t: t / "yok.sqlite3", id="dosya_yok"),
        pytest.param(lambda t: _veritabani(t, okul_karti=0), id="okul_karti_bos"),
        pytest.param(lambda t: _veritabani(t, okul_karti=2), id="okul_karti_iki_satir"),
        pytest.param(lambda t: _veritabani(t, parmak_izi=""), id="parmak_izi_bos"),
        pytest.param(lambda t: _veritabani(t, parmak_izi="   "), id="parmak_izi_yalniz_bosluk"),
    ],
)
def test_koruma_tutmayan_veritabaninda_depoya_dokunulmaz(
    kur: Callable[[Path], Path], tmp_path: Path, depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)
    once = _agac(depo)

    assert _tara(kur(tmp_path), depo) == 0

    assert _agac(depo) == once


def test_parmak_izi_null_ise_de_atlanir(tmp_path: Path, depo: Path) -> None:
    """Sütun boş olamaz; program dışından değiştirilmiş veritabanı yine atlanır."""
    yol = tmp_path / "null.sqlite3"
    with closing(sqlite3.connect(yol)) as baglanti:
        baglanti.execute("CREATE TABLE okul_schoolconfig (id integer, app_password_hash text)")
        baglanti.execute("INSERT INTO okul_schoolconfig VALUES (1, NULL)")
        baglanti.commit()
    ek_tablosu_ekle(yol, ())
    ek = ornek_ek()
    depoya_koy(depo, ek)

    assert _tara(yol, depo) == 0

    assert (depo / ek.ad).exists()


def test_takasta_oldurulen_geri_yuklemeden_sonraki_bos_veritabani_depoyu_yetime_gondermez(
    tmp_path: Path, depo: Path
) -> None:
    """Risk: eski veritabanı kenara alınmış, yenisi konmadan süreç ölmüş; göç boş bir veritabanı
    kurmuş. Şema tam, okul kartı yok ya da parmak izi boş. Depodaki dosyalar kaybolmamalı."""
    ek = ornek_ek()
    depoya_koy(depo, ek)
    db = _veritabani(tmp_path, okul_karti=0)
    (db.parent / "db-onceki-2026-11-06-101530.sqlite3").write_bytes(b"kenara alinan")

    assert _tara(db, depo) == 0

    assert (depo / ek.ad).read_bytes() == ek.hazir.kap
    assert not (depo / ds.YETIM_DIZINI).exists()


def test_veritabani_okunamazsa_gunluge_duser_acilisi_dusurmez(
    tmp_path: Path, depo: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="oab_defteri.okul"):
        assert _tara(_tablosuz(tmp_path), depo) == 0

    assert "OperationalError" in caplog.text
    assert str(tmp_path) not in caplog.text


def test_depo_dizini_okunamazsa_tarama_gunluge_duser(
    db: Path,
    depo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def patla(_depo: Path) -> list[str]:
        raise PermissionError(f"izin yok: {_depo}")

    monkeypatch.setattr(ds, "depodaki_dosyalar", patla)

    with caplog.at_level(logging.WARNING, logger="oab_defteri.okul"):
        assert _tara(db, depo) == 0

    assert "PermissionError" in caplog.text
    assert str(depo) not in caplog.text


def test_depo_dizini_yoksa_tarama_bos_doner(db: Path, tmp_path: Path) -> None:
    assert _tara(db, tmp_path / "yok") == 0


# ============================================================ taşıma


def test_satiri_olmayan_dosya_yetime_gider_satiri_olan_kalir(tmp_path: Path, depo: Path) -> None:
    kayitli, satirsiz = ornek_ek(), ornek_ek(PNG)
    depoya_koy(depo, kayitli, satirsiz)

    assert _tara(_veritabani(tmp_path, kayitli), depo) == 1

    assert (depo / kayitli.ad).read_bytes() == kayitli.hazir.kap
    assert not (depo / satirsiz.ad).exists()
    assert _yetimde(depo, satirsiz).read_bytes() == satirsiz.hazir.kap


def test_imhali_satirin_dosyasi_yerinde_kalir(tmp_path: Path, depo: Path) -> None:
    """`purged_at` dolu satır da satırdır: imhanın dosyası imhanın işidir, tarama ayrıca bakmaz."""
    imhali = ornek_ek(purged_at="2026-11-01 08:00:00")
    depoya_koy(depo, imhali)

    assert _tara(_veritabani(tmp_path, imhali), depo) == 0

    assert (depo / imhali.ad).exists()


def test_gun_verilmezse_yerel_gunun_dizini_kullanilir(db: Path, depo: Path) -> None:
    from django.utils import timezone

    ek = ornek_ek()
    depoya_koy(depo, ek)

    masaustu_kanca.yetim_taramasi(db, depo)

    assert (ds.yetim_gun_dizini(depo, timezone.localdate()) / ek.ad).exists()


def test_desene_uymayan_ada_ve_duzenli_olmayan_dosyaya_dokunulmaz(db: Path, depo: Path) -> None:
    """Yalnız `dosyalar/<32 hane>` düzenli dosyası; satırsız oldukları hâlde hepsi kalır."""
    for ad in (
        "notlar.txt",
        "AB" * 16,  # büyük harfli
        "ab" * 15,  # kısa
        "ab" * 17,  # uzun
        f"{HEX}.tmp",
        f"{HEX}-1",
        "Uydurgül Masalcıoğlu dilekçesi.pdf",
    ):
        (depo / ad).write_bytes(b"x")
    (depo / ("cd" * 16)).mkdir()  # desene uyan dizin
    (depo / f"{ds.HAZIRLIK_ONEKI}{HEX}").mkdir()
    gun = depo / ds.YETIM_DIZINI / "2026-11-01"
    gun.mkdir(parents=True)
    (gun / ("ef" * 16)).write_bytes(b"eski yetim")
    once = _agac(depo)

    assert _tara(db, depo) == 0

    assert _agac(depo) == once


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ testi POSIX'te koşar")
def test_desene_uyan_sembolik_baga_dokunulmaz(db: Path, depo: Path, tmp_path: Path) -> None:
    hedef = tmp_path / "hedef"
    hedef.write_bytes(b"x")
    bag = depo / HEX
    bag.symlink_to(hedef)

    assert _tara(db, depo) == 0

    assert bag.is_symlink() and hedef.exists()


def test_ayni_gun_ayni_ad_yetimdeyse_ezilmez(db: Path, depo: Path) -> None:
    ek = ornek_ek()
    onceki = _yetimde(depo, ek)
    onceki.parent.mkdir(parents=True)
    onceki.write_bytes(b"onceki kopya")
    depoya_koy(depo, ek)

    assert _tara(db, depo) == 1

    assert onceki.read_bytes() == b"onceki kopya"
    assert not (depo / ek.ad).exists()
    assert sorted(yol.read_bytes() for yol in onceki.parent.iterdir()) == sorted(
        [b"onceki kopya", ek.hazir.kap]
    )


def test_tasinamayan_dosya_taramayi_durdurmaz_sayisi_gunluge_duser(
    db: Path,
    depo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    kilitli, serbest = sorted([ornek_ek(), ornek_ek(PNG)], key=lambda ek: ek.ad)
    depoya_koy(depo, kilitli, serbest)
    asil = ds.yetime_tasi

    def tasi(depo_: Path, ad: str, gun: date) -> Path:
        if ad == kilitli.ad:
            raise PermissionError(f"kilitli: {depo_ / ad}")
        return asil(depo_, ad, gun)

    monkeypatch.setattr(ds, "yetime_tasi", tasi)
    yazilan: list[dict[str, int]] = []
    monkeypatch.setattr(
        masaustu_kanca, "_yetim_olayini_yaz", lambda **sayilar: yazilan.append(sayilar)
    )

    with caplog.at_level(logging.WARNING, logger="oab_defteri.okul"):
        assert _tara(db, depo) == 1

    assert (depo / kilitli.ad).exists() and _yetimde(depo, serbest).exists()
    assert yazilan == [{"tasinan": 1, "tasinamayan": 1}]
    assert kilitli.ad not in caplog.text and serbest.ad not in caplog.text
    assert str(depo) not in caplog.text


def test_hicbir_dosya_tasinamazsa_satir_yazilmaz(
    db: Path, depo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    depoya_koy(depo, ornek_ek())

    def tasi(_depo: Path, _ad: str, _gun: date) -> Path:
        raise PermissionError("kilitli")

    monkeypatch.setattr(ds, "yetime_tasi", tasi)
    yazilan: list[dict[str, int]] = []
    monkeypatch.setattr(
        masaustu_kanca, "_yetim_olayini_yaz", lambda **sayilar: yazilan.append(sayilar)
    )

    assert _tara(db, depo) == 0
    assert yazilan == []


# ============================================================ masaüstü kabuğu


@pytest.mark.django_db
@pytest.mark.parametrize("autotest", [False, True], ids=["olagan", "autotest"])
def test_masaustu_kabugu_gercek_kancalari_kendi_yollariyla_cagirir(
    autotest: bool, tmp_path: Path
) -> None:
    """Kabuğun testleri sahte kanca kullanır, hataları da yutulur: imza ve yollar burada sınanır."""
    paths = resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path / "kok")})
    paths.ensure()
    yetkili_sqlite(paths.db_path, dek=TEST_DEK, hesaplar=[], wal=False)
    ek_tablosu_ekle(paths.db_path, ())
    ek = ornek_ek()
    depoya_koy(paths.dosya_deposu, ek)
    artiklar = [
        _dosya(paths.db_path.with_name(paths.db_path.name + backup_restore.YENI_VERITABANI_EKI)),
        _dosya(paths.backups / f"{live_restore.YUKLEME_ONEKI}{HEX}{live_restore.YUKLEME_EKI}"),
        _dosya(paths.dosya_deposu / f"{HEX}.tmp"),
    ]

    masaustu._acilis_bakimi(paths, autotest=autotest)

    assert not any(yol.exists() for yol in artiklar)
    assert (paths.dosya_deposu / ek.ad).exists() is autotest


# ============================================================ gerçek şema


@pytest.fixture
def sahip(monkeypatch: pytest.MonkeyPatch) -> Iterator[SchoolYear]:
    """Geçici sahip kümesi (`SchoolYear`; F1b'de küme boştur)."""
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", set())
    dosya_deposu.sahip_kaydet(SchoolYear)
    yield school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )


@pytest.mark.django_db(transaction=True)
def test_gercek_semada_sorgular_okul_kartini_ve_ek_satirini_okur(
    sahip: SchoolYear, depo: Path
) -> None:
    """Okuma ORM'siz: sütun ya da tablo adı değişirse tarama sessizce atlanmasın, düşmesin."""
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults={"app_password_hash": "uydurma-parmak-izi"}
    )
    ek = dosya_deposu.yaz(
        PDF,
        original_name=OZGUN_AD,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=sahip,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )
    satirsiz = ornek_ek(PNG)
    depoya_koy(depo, satirsiz)
    gercek = Path(str(connection.settings_dict["NAME"]))

    assert masaustu_kanca.yetim_taramasi(gercek, depo, gun=GUN) == 1

    assert (depo / ek.stored_name).exists()
    assert _yetimde(depo, satirsiz).exists()


@pytest.mark.django_db(transaction=True)
def test_gercek_semada_parmak_izi_bos_kart_depoya_dokunmaz(depo: Path) -> None:
    SchoolConfig.objects.update_or_create(
        pk=SchoolConfig.SINGLETON_PK, defaults={"app_password_hash": ""}
    )
    ek = ornek_ek()
    depoya_koy(depo, ek)
    gercek = Path(str(connection.settings_dict["NAME"]))

    assert masaustu_kanca.yetim_taramasi(gercek, depo, gun=GUN) == 0

    assert (depo / ek.ad).exists()


# ============================================================ olay


def _kilitle() -> None:
    with transaction.atomic():
        denetim_izi.olay(AuditAction.HESAP, model="okul.Account", object_id=TEST_HESAP_ID)
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"


def _ac() -> None:
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def _olaylar() -> list[AuditTrail]:
    return list(
        AuditTrail.objects.filter(
            action=AuditAction.BUTUNLUK, model=denetim_izi.DOSYA_DEPOSU
        ).order_by("seq")
    )


def _not_kaydi() -> dict[str, Any]:
    return geri_yukleme_notu.geri_yukleme_kaydi(
        yedek="gunluk-2026-11-01.odbak",
        onceki_dosya=None,
        onceki_sha256=None,
        onceki_zincir_basi=None,
        yol_bilgisi={"tur": geri_yukleme_notu.YOL_KURTARMA, "no": 1},
    )


@pytest.mark.django_db
def test_olay_kilitli_kipte_butunluk_satiridir_sayilar_tasir_ad_tasimaz(
    db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)
    _kilitle()

    assert _tara(db, depo) == 1

    (satir,) = _olaylar()
    assert (satir.actor, satir.key_mode, satir.object_id) == ("SISTEM", "KILITLI", "yetim")
    assert satir.changed_fields == ["tasinamayan", "tasinan"]
    assert satir.values == {"tasinan": [None, 1], "tasinamayan": [None, 0]}
    assert ek.ad not in json.dumps(satir.values) and ek.ad not in satir.object_id


@pytest.mark.django_db
def test_kilitli_satir_ilk_kilit_acilisinda_bulgu_uretmez(db: Path, depo: Path) -> None:
    """Satır kilitli zincire uyar: açılışın doğrulaması onu tanır, `BUTUNLUK` bulgusu yazmaz."""
    depoya_koy(depo, ornek_ek())
    _kilitle()
    _tara(db, depo)

    _ac()

    assert not AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).exists()


@pytest.mark.django_db
def test_tasinan_yoksa_satir_yazilmaz(db: Path, depo: Path) -> None:
    _kilitle()

    assert _tara(db, depo) == 0

    assert not _olaylar()


@pytest.mark.django_db
def test_not_varken_olay_nota_duser_ilk_kilit_acilisinda_satir_olur(db: Path, depo: Path) -> None:
    """Geri yüklemeden sonraki açılış: çapa eski veritabanınındır, kilitli satır yazılmaz."""
    ek = ornek_ek()
    depoya_koy(depo, ek)
    _kilitle()
    dizin = iz_durumu.dizin()
    geri_yukleme_notu.geri_yukleme_ekle(dizin, _not_kaydi())

    assert _tara(db, depo) == 1

    assert not _olaylar()
    notu = geri_yukleme_notu.oku(dizin)
    assert notu is not None
    (bekleyen,) = notu["bekleyen_olaylar"]
    assert (bekleyen["eylem"], bekleyen["model"]) == ("BUTUNLUK", denetim_izi.DOSYA_DEPOSU)
    assert ek.ad not in json.dumps(notu)

    _ac()

    (satir,) = _olaylar()
    assert (satir.actor, satir.key_mode, satir.object_id) == ("SISTEM", "ACIK", "yetim")
    degerler = dict(satir.values)
    assert degerler.pop("zaman")[1].endswith("Z")  # olayın kendi anı
    assert degerler == {"tasinan": [None, 1], "tasinamayan": [None, 0]}
    assert not geri_yukleme_notu.var_mi(dizin)


@pytest.mark.django_db
def test_notta_serbest_metin_tasiyan_olay_satira_girmez(db: Path, depo: Path) -> None:
    """Not dosyası program dışından değişmiş: kimlik yeniden denetlenir, kişi adı satıra girmez."""
    _kilitle()
    dizin = iz_durumu.dizin()
    geri_yukleme_notu.geri_yukleme_ekle(dizin, _not_kaydi())
    geri_yukleme_notu.bekleyen_olay_ekle(
        dizin,
        {
            "eylem": "BUTUNLUK",
            "model": denetim_izi.DOSYA_DEPOSU,
            "object_id": "Uydurgül Masalcıoğlu",
            "changed_fields": ["tasinan"],
            "values": {"tasinan": [None, 1]},
        },
    )

    _ac()

    assert not _olaylar()


@pytest.mark.django_db
def test_acik_kipteki_olay_butunluk_kartina_cikmaz_dogrulama_bulgusu_sanilmaz(
    db: Path, depo: Path
) -> None:
    """Kart "dogrulama" dalına düşseydi boş bir uyarı gösterirdi: satır bulgu değildir."""
    depoya_koy(depo, ornek_ek())

    assert _tara(db, depo) == 1  # oturum açık: açık kip

    (satir,) = _olaylar()
    assert satir.key_mode == "ACIK"
    assert iz_dogrulama.denetim_kartlari(TEST_HESAP_ID)["butunluk"] == []


@pytest.mark.django_db
def test_izinli_liste_ad_ya_da_yol_tasiyan_alani_satira_koymaz() -> None:
    izinli = denetim_izi.izinli_degerler(
        denetim_izi.DOSYA_DEPOSU, {"tasinan": (None, 1), "tasinamayan": (None, 0)}
    )
    assert izinli == {"tasinan": [None, 1], "tasinamayan": [None, 0]}
    with pytest.raises(denetim_izi.IzYazilamadi):
        denetim_izi.izinli_degerler(denetim_izi.DOSYA_DEPOSU, {"ad": (None, HEX)})


def test_olay_yazilamazsa_tarama_dusmez_dosya_yetimde_kalir(
    db: Path,
    depo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ek = ornek_ek()
    depoya_koy(depo, ek)

    def patla(*_a: Any, **_k: Any) -> None:
        raise denetim_izi.IzYazilamadi("yazılamadı")

    monkeypatch.setattr(iz_durumu, "sistem_olayi", patla)

    with caplog.at_level(logging.WARNING, logger="oab_defteri.okul"):
        assert _tara(db, depo) == 1

    assert _yetimde(depo, ek).exists()
    assert "denetim izine yazılamadı" in caplog.text


# ============================================================ uçtan uca


def _geri_yukle(yedek: Path, db: Path) -> backup_restore.RestoreResult:
    return backup_restore.restore_database(yedek, db, recovery_key=TEST_KURTARMA_ANAHTARI)


def _ac_dosyayi(depo: Path, ek: OrnekEk) -> bytes:
    return ds.depodan_ac(
        depo,
        ek.ad,
        key_wrap=ek.hazir.key_wrap,
        sarmal_anahtari=crypto.file_wrap_key(TEST_DEK),
    )


@pytest.mark.django_db
def test_eski_yedek_yetime_gonderir_yeni_yedek_yetimden_geri_alir(
    tmp_path: Path, db: Path, depo: Path
) -> None:
    """Tasarım §4.4.7: eski yedek geri yüklenir → satırı olmayan dosya yetime gider → yeni yedek
    geri yüklenir → dosya yetimden döner, açılır, sonraki tarama ona dokunmaz."""
    ilk, sonraki = ornek_ek(), ornek_ek(PNG)
    depoya_koy(depo, ilk, sonraki)
    eski = tmp_path / "gunluk-2026-11-01.odbak"
    yeni = tmp_path / "gunluk-2026-11-04.odbak"
    yerel_yedek_yaz(eski, ekli_sqlite(tmp_path / "eski.sqlite3", [ilk], isaret="eski"), [ilk])
    yerel_yedek_yaz(
        yeni,
        ekli_sqlite(tmp_path / "yeni.sqlite3", [ilk, sonraki], isaret="yeni"),
        [ilk, sonraki],
    )

    assert _geri_yukle(eski, db).dosya_raporu.eksik == 0
    assert _tara(db, depo) == 1
    assert not (depo / sonraki.ad).exists()
    assert (depo / ilk.ad).exists()
    assert _yetimde(depo, sonraki).read_bytes() == sonraki.hazir.kap

    rapor = _geri_yukle(yeni, db).dosya_raporu

    assert (rapor.yetimden_donen, rapor.eksik, rapor.bozuk) == (1, 0, 0)
    assert not _yetimde(depo, sonraki).exists()
    assert _ac_dosyayi(depo, sonraki) == PNG
    assert _tara(db, depo) == 0
    assert (depo / sonraki.ad).exists()


@pytest.mark.django_db
def test_tam_yedek_geri_yuklemesi_sonrasi_tarama_yerine_konanlara_dokunmaz(
    tmp_path: Path, db: Path, depo: Path
) -> None:
    ek = ornek_ek()
    kaynak = ds.dizin_kur(tmp_path / "kaynak-depo")
    depoya_koy(kaynak, ek)
    yedek = tmp_path / "gunluk-2026-11-04.odbak"
    tam_yedek_kur(yedek, ekli_sqlite(tmp_path / "goruntu.sqlite3", [ek]), [ek], kaynak)

    assert _geri_yukle(yedek, db).dosya_raporu.yerine_konan == 1

    assert _tara(db, depo) == 0
    assert _ac_dosyayi(depo, ek) == PDF


def test_yarim_kalan_geri_yuklemenin_yerlestirdigi_dosya_taramayla_toplanir(
    db: Path, depo: Path
) -> None:
    """Plan: kesinti yalnız yetim üretir, kayıp üretmez. Takas yapılmamış, dosya satırsız kalmış."""
    ek = ornek_ek()
    depoya_koy(depo, ek)
    hazirlik = ds.hazirlik_dizini_kur(depo)
    (hazirlik / HEX).write_bytes(b"yarim")

    assert _tara(db, depo) == 1
    assert masaustu_kanca.artiklari_temizle(db, depo.parent / "yedekler", depo) == 1

    assert _yetimde(depo, ek).exists()
    assert not hazirlik.exists()


# ============================================================ artık temizliği


@pytest.fixture
def dizinler(tmp_path: Path) -> tuple[Path, Path, Path]:
    """(veritabanı, yedek dizini, depo)."""
    veri, yedekler = tmp_path / "data", tmp_path / "backups"
    depo = veri / "dosyalar"
    for dizin in (veri, yedekler, depo):
        dizin.mkdir(parents=True)
    return veri / "db.sqlite3", yedekler, depo


def _dosya(yol: Path, icerik: bytes = b"x") -> Path:
    yol.write_bytes(icerik)
    return yol


def _dizin(yol: Path) -> Path:
    yol.mkdir()
    (yol / "goruntu.sqlite3").write_bytes(b"artik")
    return yol


def test_tanimlanan_artiklar_silinir(dizinler: tuple[Path, Path, Path]) -> None:
    db, yedekler, depo = dizinler
    veri = db.parent
    artiklar = [
        _dosya(veri / "db.sqlite3.yeni.tmp"),
        _dosya(veri / "db.sqlite3.yeni.tmp-wal"),
        _dosya(veri / "db.sqlite3.yeni.tmp-shm"),
        _dizin(veri / ".geri-yukleme-denetimi-a1b2c3_d"),
        _dizin(veri / f"{GORUNTU_DIZINI_ONEKI}a1b2c3_d"),
        _dosya(yedekler / f".yukleme-{HEX}.tmp"),
        _dosya(yedekler / "gunluk-2026-11-06.odbak.tmp"),
        _dosya(yedekler / "elle verilmis ad.odbak.tmp"),
        _dosya(depo / f"{HEX}.tmp"),
        _dizin(depo / f"{ds.HAZIRLIK_ONEKI}{HEX}"),
    ]

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == len(artiklar)

    assert not any(os.path.lexists(yol) for yol in artiklar)


def test_tanimadigi_ada_ve_baska_dizindeki_benzerine_dokunmaz(
    dizinler: tuple[Path, Path, Path],
) -> None:
    db, yedekler, depo = dizinler
    veri = db.parent
    (depo / ds.YETIM_DIZINI).mkdir()
    for yol in (
        # Veri dizini: canlı dosyalar ve ada yalnız benzeyenler.
        veri / "db.sqlite3",
        veri / "db.sqlite3-wal",
        veri / "db-onceki-2026-11-06-101530.sqlite3",
        veri / "guvenlik.json",
        veri / "guvenlik.json.tmp",  # kendi temizliği var
        veri / "baska.sqlite3.yeni.tmp",
        veri / "db.sqlite3.yeni",
        veri / "db.sqlite3.yeni.tmp.bak",
        veri / f"{HEX}.tmp",  # depo artığı veri dizininde değildir
        veri / f".yukleme-{HEX}.tmp",
        veri / "gunluk-2026-11-06.odbak.tmp",
        # Yedek dizini.
        yedekler / "gunluk-2026-11-06.odbak",
        yedekler / "gunluk-2026-11-06.odbak.tmp.bak",
        yedekler / f"yukleme-{HEX}.tmp",
        yedekler / f".yukleme-{HEX}",
        yedekler / "db.sqlite3.yeni.tmp",
        yedekler / f"{HEX}.tmp",
        yedekler / "notlar.tmp",
        # Depo.
        depo / HEX,
        depo / f"{HEX}.tmp.bak",
        depo / f"{'ab' * 15}.tmp",
        depo / f"{'AB' * 16}.tmp",
        depo / "notlar.tmp",
        depo / f".yukleme-{HEX}.tmp",
        depo / "gunluk-2026-11-06.odbak.tmp",
        depo / ds.YETIM_DIZINI / f"{HEX}.tmp",
    ):
        _dosya(yol)
    for yol in (
        depo / f"{ds.HAZIRLIK_ONEKI}kisa",
        depo / f"{ds.HAZIRLIK_ONEKI}{HEX}-kopya",
        depo / f"{ds.HAZIRLIK_ONEKI}{'AB' * 16}",
        depo / ".geri-yukleme-denetimi-a1",
        veri / f"{ds.HAZIRLIK_ONEKI}{HEX}",
        yedekler / ".geri-yukleme-denetimi-a1",
    ):
        _dizin(yol)
    once = _agac(db.parent.parent)

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 0

    assert _agac(db.parent.parent) == once


def test_ad_tutsa_da_tur_tutmayana_dokunulmaz(dizinler: tuple[Path, Path, Path]) -> None:
    """Dosya beklenen yerde dizin, dizin beklenen yerde dosya: program yazmamıştır."""
    db, yedekler, depo = dizinler
    veri = db.parent
    _dizin(veri / "db.sqlite3.yeni.tmp")
    _dosya(veri / ".geri-yukleme-denetimi-a1")
    _dizin(yedekler / "gunluk-2026-11-06.odbak.tmp")
    _dizin(yedekler / f".yukleme-{HEX}.tmp")
    _dizin(depo / f"{HEX}.tmp")
    _dosya(depo / f"{ds.HAZIRLIK_ONEKI}{HEX}")
    once = _agac(db.parent.parent)

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 0

    assert _agac(db.parent.parent) == once


@pytest.mark.skipif(os.name != "posix", reason="sembolik bağ testi POSIX'te koşar")
def test_sembolik_bag_izlenmez(dizinler: tuple[Path, Path, Path], tmp_path: Path) -> None:
    db, yedekler, depo = dizinler
    hedef = _dizin(tmp_path / "hedef-dizin")
    bag = db.parent / ".geri-yukleme-denetimi-bag"
    bag.symlink_to(hedef, target_is_directory=True)
    hedef_dosya = _dosya(tmp_path / "hedef-dosya")
    dosya_bagi = yedekler / "bag.odbak.tmp"
    dosya_bagi.symlink_to(hedef_dosya)

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 0

    assert bag.is_symlink() and (hedef / "goruntu.sqlite3").exists()
    assert dosya_bagi.is_symlink() and hedef_dosya.exists()


def test_uretenlerin_adlari_taninir(dizinler: tuple[Path, Path, Path]) -> None:
    """Ad üreticisi değişirse tanıma onunla değişmeli: artıklar üreticilerin sabitlerinden kurulur."""
    db, yedekler, depo = dizinler
    hazirlik = ds.hazirlik_dizini_kur(depo)
    yeni_vt = _dosya(db.with_name(db.name + backup_restore.YENI_VERITABANI_EKI))
    denetim = _dizin(db.parent / f"{geri_yukleme_yetkisi.GECICI_DIZIN_ONEKI}a1")
    yukleme = _dosya(yedekler / f"{live_restore.YUKLEME_ONEKI}{HEX}{live_restore.YUKLEME_EKI}")

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 4

    assert not any(yol.exists() for yol in (hazirlik, yeni_vt, denetim, yukleme))


def test_kesilen_yazimin_artigi_silinince_ayni_adla_yazim_acilir(
    dizinler: tuple[Path, Path, Path],
) -> None:
    """`atomik_yaz` önceki kesintinin `.tmp`'sini görünce reddeder; temizlik bu kilidi açar."""
    db, yedekler, depo = dizinler
    _dosya(depo / f"{HEX}.tmp")
    with pytest.raises(ds.GeciciDosyaVarHatasi):
        ds.depoya_yaz(depo, HEX, b"kap")

    masaustu_kanca.artiklari_temizle(db, yedekler, depo)

    ds.depoya_yaz(depo, HEX, b"kap")
    assert (depo / HEX).read_bytes() == b"kap"


def test_silinemeyen_artik_otekileri_durdurmaz_ad_gunluge_yazilmaz(
    dizinler: tuple[Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    db, yedekler, depo = dizinler
    kilitli = _dosya(yedekler / "Uydurgül Masalcıoğlu.odbak.tmp")
    serbest = _dosya(yedekler / "gunluk-2026-11-06.odbak.tmp")
    asil = Path.unlink

    def sil(yol: Path, missing_ok: bool = False) -> None:
        if yol == kilitli:
            raise PermissionError(f"kilitli: {yol}")
        asil(yol, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", sil)

    with caplog.at_level(logging.INFO, logger="oab_defteri.okul"):
        assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 1

    assert kilitli.exists() and not serbest.exists()
    assert "Masalcıoğlu" not in caplog.text
    assert "1 artık silinemedi" in caplog.text and "1 artık silindi" in caplog.text


def test_silinemeyen_dizin_de_durdurmaz(
    dizinler: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    db, yedekler, depo = dizinler
    _dizin(depo / f"{ds.HAZIRLIK_ONEKI}{HEX}")
    serbest = _dosya(depo / f"{HEX}.tmp")

    def sil(yol: Path, *_a: Any, **_k: Any) -> None:
        raise PermissionError(f"kilitli: {yol}")

    monkeypatch.setattr(shutil, "rmtree", sil)

    assert masaustu_kanca.artiklari_temizle(db, yedekler, depo) == 1

    assert not serbest.exists()


def test_dizinler_yoksa_temizlik_sessizce_biter(tmp_path: Path) -> None:
    assert (
        masaustu_kanca.artiklari_temizle(
            tmp_path / "veri" / "db.sqlite3", tmp_path / "yedek", tmp_path / "depo"
        )
        == 0
    )
