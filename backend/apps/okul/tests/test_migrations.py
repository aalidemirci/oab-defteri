"""`okul` göç ağacının genel koruma testleri.

Göç ağacı F0'da temizlenmiş modellerden `0001_initial` ile yeniden başladı (aile
iskeletinin atasındaki 0001-0013 göçleri zil/vardiya/küme/zümre/fotoğraf/cinsiyet/çizelge
alanlarını taşıyordu). Buradaki testler iki
şeyi sabitler:

- Modellerde yapılan ve göçe dökülmemiş değişiklik YOKTUR (masaüstü açılışı
  `migrate` koşar; eksik göç kurulu programda şemayı sessizce eskide bırakır).
- Ağaç tek yapraklıdır (iki dal aynı anda göç eklerse `migrate` çakışma verir).

Veri dönüştüren göçlerin testleri de buradadır (0013: `kademe` → `levels`). Bu testler
veritabanını eski göçe geri alıp yeniden ilerletir (`transaction=True`); sonunda en son göçe
döner.
"""

from __future__ import annotations

from collections.abc import Iterator
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.db import connection
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
