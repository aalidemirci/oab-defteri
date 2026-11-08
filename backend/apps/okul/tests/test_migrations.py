"""`okul` göç ağacının genel koruma testleri.

Göç ağacı F0'da temizlenmiş modellerden `0001_initial` ile yeniden başladı (aile
iskeletinin atasındaki 0001-0013 göçleri zil/vardiya/küme/zümre/fotoğraf/cinsiyet/çizelge
alanlarını taşıyordu). Buradaki testler iki
şeyi sabitler:

- Modellerde yapılan ve göçe dökülmemiş değişiklik YOKTUR (masaüstü açılışı
  `migrate` koşar; eksik göç kurulu programda şemayı sessizce eskide bırakır).
- Ağaç tek yapraklıdır (iki dal aynı anda göç eklerse `migrate` çakışma verir).

Veri dönüştüren ve tablo düşüren göçlerin testleri de buradadır (0013: `kademe` → `levels`;
0014: öğrenci sicili, şube kataloğu ve hazırlık bayrağı düşer; 0015: görev ve aktarım türlerinin
değerleri çevrilir; 0016: veli listesi ve veri sorumlusu alanı kurulur). Bu testler
veritabanını eski göçe geri alıp yeniden ilerletir (`transaction=True`); sonunda en son göçe
döner.
"""

from __future__ import annotations

from collections.abc import Iterator
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader


@pytest.mark.django_db
def test_modellerde_goce_dokulmemis_degisiklik_yoktur() -> None:
    cikti = StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=cikti, stderr=cikti)
    except SystemExit as exc:  # `--check` eksik göçte 1 koduyla çıkar
        pytest.fail(f"Eksik göç var — `makemigrations` çalıştırın:\n{cikti.getvalue()} ({exc})")


@pytest.mark.django_db
def test_okul_goc_agaci_tek_yaprakli_ve_0001den_baslar() -> None:
    loader = MigrationLoader(connection)
    yapraklar = loader.graph.leaf_nodes("okul")
    assert len(yapraklar) == 1, f"Birden çok yaprak göç: {yapraklar}"
    kokler = [ad for app, ad in loader.graph.root_nodes("okul") if app == "okul"]
    assert kokler == ["0001_initial"]


# ---------------------------------------------------------------------------
# 0013 — okul kartının OAB alanları: tek değerli `kademe` → `levels` listesi
# ---------------------------------------------------------------------------
_ONCE = [("okul", "0012_attachment")]
_SONRA = [("okul", "0013_okul_karti_oab_alanlari")]


def _goc(hedef: list[tuple[str, str]]) -> Any:
    """`okul`'u `hedef`e göçürür; o durumun model sınıflarını (`apps`) döndürür."""
    yurutucu = MigrationExecutor(connection)
    yurutucu.migrate(hedef)
    yurutucu.loader.build_graph()
    return yurutucu.loader.project_state(hedef).apps


@pytest.fixture
def goc_sonda_biter() -> Iterator[None]:
    """Test nerede biterse bitsin veritabanı en son göçe döner (öteki testler onu bekler)."""
    yield
    yurutucu = MigrationExecutor(connection)
    yurutucu.loader.build_graph()
    yurutucu.migrate(yurutucu.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz  # göç satırı yalnız okul kartını taşır; hesap ve iz anahtarı gerekmez
@pytest.mark.usefixtures("goc_sonda_biter")
@pytest.mark.parametrize(
    ("kademe", "beklenen"),
    [("ORTAOKUL", ["ORTAOKUL"]), ("", [])],
    ids=["dolu_kademe_listeye", "bos_kademe_bos_liste"],
)
def test_0013_kademeyi_listeye_cevirir_ve_eski_alanlari_dusurur(
    kademe: str, beklenen: list[str]
) -> None:
    eski = _goc(_ONCE).get_model("okul", "SchoolConfig")
    eski.objects.update_or_create(
        pk=1,
        defaults={
            "school_name": "Örnek Ortaokulu",
            "kademe": kademe,
            "kisa_ad": "Örnek OO",
            "kutuphane_saatleri": "Örnek saatler",
            "setup_completed": True,
        },
    )

    yeni = _goc(_SONRA).get_model("okul", "SchoolConfig")
    satir = yeni.objects.get(pk=1)

    assert satir.levels == beklenen
    assert satir.school_name == "Örnek Ortaokulu"
    assert satir.setup_completed is True  # kurulum kapısı yeniden kapanmaz
    assert satir.institution_code == ""
    assert (satir.student_count, satir.student_count_as_of) == (None, None)
    assert (satir.settlement_type, satir.canteen_mode, satir.staffing_mode) == ("", "", "")
    assert satir.in_campus is False and satir.opened_on is None
    with connection.cursor() as cursor:
        sutunlar = {
            s.name
            for s in connection.introspection.get_table_description(cursor, "okul_schoolconfig")
        }
    assert not {"kademe", "kisa_ad", "kutuphane_saatleri"} & sutunlar


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0013_geri_alininca_listenin_ilk_kademesi_kademe_olur() -> None:
    yeni = _goc(_SONRA).get_model("okul", "SchoolConfig")
    yeni.objects.update_or_create(
        pk=1, defaults={"levels": ["OKUL_ONCESI", "ORTAOKUL", "ORTAOGRETIM"]}
    )

    eski = _goc(_ONCE).get_model("okul", "SchoolConfig")

    # Eski alanın kümesinde okul öncesi yoktu: tanıdığı ilk kademe yazılır.
    assert eski.objects.get(pk=1).kademe == "ORTAOKUL"


# ---------------------------------------------------------------------------
# 0014 — öğrenci sicili, şube kataloğu ve hazırlık sınıfı bayrağı düşer (F1b 5. adım; düz göç)
# ---------------------------------------------------------------------------
_ONCE_0014 = [("okul", "0013_okul_karti_oab_alanlari")]
_SONRA_0014 = [("okul", "0014_ogrenci_ve_sube_sokumu")]


def _tablolar() -> set[str]:
    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _okul_karti_sutunlari() -> set[str]:
    with connection.cursor() as cursor:
        return {
            s.name
            for s in connection.introspection.get_table_description(cursor, "okul_schoolconfig")
        }


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0014_ogrenci_ve_sube_tablolarini_ve_hazirlik_bayragini_dusurur() -> None:
    eski = _goc(_ONCE_0014)
    eski.get_model("okul", "SchoolConfig").objects.update_or_create(
        pk=1, defaults={"school_name": "Örnek Ortaokulu", "has_prep_class": True}
    )
    yil = eski.get_model("okul", "SchoolYear").objects.create(
        name="2026-2027", start_date="2026-09-07", end_date="2027-06-25"
    )
    eski.get_model("okul", "ClassSection").objects.create(
        school_year=yil, class_level=9, class_section="A"
    )
    # Ad ve okul no boş: şifreli alan boş dizeyi şifrelemez (uydurma bile kişi verisi yazılmaz).
    eski.get_model("okul", "Student").objects.create(class_level=9, class_section="A")
    assert {"okul_student", "okul_classsection"} <= _tablolar()

    yeni = _goc(_SONRA_0014)

    assert not {"okul_student", "okul_classsection"} & _tablolar()
    assert "has_prep_class" not in _okul_karti_sutunlari()
    # Okul kartı ve ders yılı kalır; yalnız öğrenci tarafı düşer.
    assert yeni.get_model("okul", "SchoolConfig").objects.get(pk=1).school_name == (
        "Örnek Ortaokulu"
    )
    assert yeni.get_model("okul", "SchoolYear").objects.filter(name="2026-2027").exists()
    for ad in ("Student", "ClassSection"):
        with pytest.raises(LookupError):
            yeni.get_model("okul", ad)


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0014_geri_alininca_tablolar_bos_kurulur() -> None:
    """Ters yön tabloları verisiz kurar: düşen satırlar geri gelmez (düz göç, kullanıcı kararı)."""
    _goc(_SONRA_0014)

    eski = _goc(_ONCE_0014)

    assert {"okul_student", "okul_classsection"} <= _tablolar()
    assert "has_prep_class" in _okul_karti_sutunlari()
    assert not eski.get_model("okul", "Student").objects.exists()
    assert not eski.get_model("okul", "ClassSection").objects.exists()


# ---------------------------------------------------------------------------
# 0015 — görev türü üçlü (OGRETMEN · YONETICI · DIGER), aktarım türü PERSONEL · VELI (F1b 5. adım)
# ---------------------------------------------------------------------------
_ONCE_0015 = [("okul", "0014_ogrenci_ve_sube_sokumu")]
_SONRA_0015 = [("okul", "0015_gorev_turu_ve_aktarim_turu")]


def _kosu(apps: Any, tur: str, ozet: str) -> Any:
    return apps.get_model("okul", "ImportRun").objects.create(
        source_type=tur, file_hash=ozet * 64, status="COMPLETED"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0015_gorev_ve_aktarim_turlerini_cevirir_eski_ogrenci_kosusuna_dokunmaz() -> None:
    eski = _goc(_ONCE_0015)
    # Ad ve soyad boş: şifreli alan boş dizeyi şifrelemez (uydurma bile kişi verisi yazılmaz).
    personel = eski.get_model("okul", "Personnel")
    ogretmen = personel.objects.create(member_kind="TEACHER")
    diger = personel.objects.create(member_kind="STAFF")
    personel_kosusu = _kosu(eski, "PERSONNEL", "a")
    ogrenci_kosusu = _kosu(eski, "STUDENTS", "b")

    yeni = _goc(_SONRA_0015)

    turler = dict(yeni.get_model("okul", "Personnel").objects.values_list("pk", "member_kind"))
    assert turler == {ogretmen.pk: "OGRETMEN", diger.pk: "DIGER"}
    kosular = dict(yeni.get_model("okul", "ImportRun").objects.values_list("pk", "source_type"))
    # Eski öğrenci koşusu çevrilmez: içerik MAC'i değişmesin (models.ImportSourceType).
    assert kosular == {personel_kosusu.pk: "PERSONEL", ogrenci_kosusu.pk: "STUDENTS"}
    with pytest.raises(IntegrityError), transaction.atomic():
        yeni.get_model("okul", "Personnel").objects.create(member_kind="TEACHER")


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0015_geri_alininca_yonetici_ogretmen_olur() -> None:
    yeni = _goc(_SONRA_0015)
    personel = yeni.get_model("okul", "Personnel")
    kayitlar = {
        tur: personel.objects.create(member_kind=tur).pk
        for tur in ("OGRETMEN", "YONETICI", "DIGER")
    }
    personel_kosusu = _kosu(yeni, "PERSONEL", "c")
    veli_kosusu = _kosu(yeni, "VELI", "d")

    eski = _goc(_ONCE_0015)

    turler = dict(eski.get_model("okul", "Personnel").objects.values_list("pk", "member_kind"))
    assert turler == {
        kayitlar["OGRETMEN"]: "TEACHER",
        kayitlar["YONETICI"]: "TEACHER",  # eski kümede yönetici yoktu
        kayitlar["DIGER"]: "STAFF",
    }
    kosular = dict(eski.get_model("okul", "ImportRun").objects.values_list("pk", "source_type"))
    assert kosular == {personel_kosusu.pk: "PERSONNEL", veli_kosusu.pk: "VELI"}


# ---------------------------------------------------------------------------
# 0016 — veli listesi (`ParentRoster`) ve okul kartının veri sorumlusu alanı (F1b 5. adım)
# ---------------------------------------------------------------------------
_ONCE_0016 = [("okul", "0015_gorev_turu_ve_aktarim_turu")]
_SONRA_0016 = [("okul", "0016_veli_listesi_ve_veri_sorumlusu")]


def _veli_sutunlari() -> set[str]:
    with connection.cursor() as cursor:
        return {
            s.name
            for s in connection.introspection.get_table_description(cursor, "okul_parentroster")
        }


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0016_veli_listesini_iki_veri_alaniyla_kurar_ve_veri_sorumlusu_bos_baslar() -> None:
    eski = _goc(_ONCE_0016)
    eski.get_model("okul", "SchoolConfig").objects.update_or_create(
        pk=1, defaults={"school_name": "Örnek Ortaokulu"}
    )
    assert "okul_parentroster" not in _tablolar()

    yeni = _goc(_SONRA_0016)

    assert "okul_parentroster" in _tablolar()
    # Tasarım §14 F1b kapısı "veli listesi yalnız iki alan taşır": ad (ve kör indeksi) ile sınıf;
    # birlik dönemi ve katılım işaretleri F1c ve F2'de gelir.
    assert _veli_sutunlari() == {
        "id",
        "import_run_id",
        "full_name",
        "name_index",
        "student_class",
        "created_at",
    }
    assert "data_controller_text" in _okul_karti_sutunlari()
    assert yeni.get_model("okul", "SchoolConfig").objects.get(pk=1).data_controller_text == ""
    kosu = _kosu(yeni, "VELI", "e")
    with pytest.raises(IntegrityError), transaction.atomic():
        yeni.get_model("okul", "ParentRoster").objects.create(import_run=kosu, student_class="")


@pytest.mark.django_db(transaction=True)
@pytest.mark.hesapsiz
@pytest.mark.usefixtures("goc_sonda_biter")
def test_0016_geri_alininca_tablo_ve_sutun_duser() -> None:
    _goc(_SONRA_0016)

    _goc(_ONCE_0016)

    assert "okul_parentroster" not in _tablolar()
    assert "data_controller_text" not in _okul_karti_sutunlari()
