"""`okul` göç ağacının genel koruma testleri.

Göç ağacı F1b sonunda temizlenmiş modellerden tek `0001_initial` ile yeniden başladı (`replaces`
yok; plan "F1b-6 uygulama kararları"). Buradaki testler iki şeyi sabitler:

- Modellerde yapılan ve göçe dökülmemiş değişiklik YOKTUR (masaüstü açılışı
  `migrate` koşar; eksik göç kurulu programda şemayı sessizce eskide bırakır).
- Ağaç tek yapraklıdır (iki dal aynı anda göç eklerse `migrate` çakışma verir).

Göçle kurulan tetikleyicilerin testleri `test_denetim_izi.py` ve `test_erisim_gunlugu.py`'dedir.
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
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
