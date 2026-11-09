"""`oab` uygulamasının iskeleti (plan "F1c adımları" 1. adım).

Üç şeyi sabitler: uygulama kurulu ve göçü temiz; soyut temel model tasarım §5 O4'teki alanları taşır;
seçenek kümelerinin değerleri tasarım §5.2'nin lafzıdır. Değerler kaynakla karşılaştırılmak için
burada ELLE ayrıca yazılıdır.

Ayrıca bağımlılık yönünü bekler: `okul` ve `shared` `oab`'yi içe aktarmaz (plan "F1c adımları");
`okul`'dan `oab`'ye giden yabancı anahtar dizeyle verilir. Taramanın kırmızıya dönebildiğini sondalar
gösterir.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.db import models
from django.db.models.fields.related import ForeignKey
from django.test.utils import isolate_apps
from django.urls import get_resolver

from apps.oab.models import (
    DropKind,
    ElectedBy,
    MembershipRole,
    MembershipSource,
    MembershipStatus,
    OabBaseModel,
    OrganType,
    PersonKind,
    PersonStatus,
    Representation,
    SeatGroup,
    SeatType,
    TermStatus,
)

#: `backend/` kökü.
KOK = Path(__file__).resolve().parents[3]

#: Tasarım §5.2'nin lafzı: seçenek kümesi → değerleri, tasarımdaki sırayla.
BEKLENEN_DEGERLER: list[tuple[type[models.TextChoices], tuple[str, ...]]] = [
    (TermStatus, ("HAZIRLIK", "ACIK", "KAPANISTA", "KAPANDI", "IPTAL")),
    (PersonKind, ("VELI", "OGRETMEN", "IDARECI", "HAYIRSEVER", "KURSIYER", "DIGER")),
    (PersonStatus, ("AKTIF", "PASIF")),
    (OrganType, ("YK", "DK", "DIVAN", "ALIM_KOMISYONU", "TEMSILCI")),
    (MembershipRole, ("BASKAN", "BASKAN_YARDIMCISI", "MUHASIP", "SEKRETER", "KATIP", "UYE")),
    (SeatType, ("ASIL", "YEDEK")),
    (SeatGroup, ("VELI", "OGRETMEN")),
    (
        ElectedBy,
        (
            "GENEL_KURUL",
            "OGRETMENLER_KURULU",
            "MEM_GOREVLENDIRME",
            "YK_KARARI",
            "OKUL_IDARESI",
            "KENDILIGINDEN",
        ),
    ),
    (MembershipSource, ("PROGRAM", "DEVRALINAN")),
    (MembershipStatus, ("ADAY", "SECILDI", "DUSTU", "IPTAL")),
    (
        DropKind,
        (
            "OGRENCI_AYRILDI",
            "DEVAMSIZLIK",
            "ISTIFA",
            "BASKA_KURUMDA_GOREV",
            "OLAGANUSTU_GK_SECIMI",
            "DIGER",
        ),
    ),
    (
        Representation,
        (
            "ODUL_DISIPLIN_KURULU",
            "DAVRANIS_DEGERLENDIRME_KURULU",
            "SOSYAL_ETKINLIKLER_KURULU",
            "KONTENJAN_KOMISYONU",
            "RPD_YURUTME_KOMISYONU",
            "TASIMACI_TESPIT_KOMISYONU",
            "MUHAMMEN_BEDEL_KOMISYONU",
            "KIRALAMA_IHALE_KOMISYONU",
            "KAMPUS_YONETIMI",
            "KANTIN_DENETIM_KOMISYONU",
            "DIGER",
        ),
    ),
]


def test_uygulama_kurulu() -> None:
    assert django_apps.get_app_config("oab").name == "apps.oab"


def test_oab_uclari_kendi_on_ekinin_altindadir() -> None:
    """`oab` uçları `/api/v1/oab/` altında toplanır; SPA kuyruğunun önünde durur."""
    desenler = [str(desen.pattern) for desen in get_resolver().url_patterns]
    assert "api/v1/oab/" in desenler
    assert desenler.index("api/v1/oab/") < len(desenler) - 1


@pytest.mark.parametrize(
    ("kume", "beklenen"), BEKLENEN_DEGERLER, ids=[k.__name__ for k, _ in BEKLENEN_DEGERLER]
)
def test_secenek_degerleri_tasarimin_lafzidir(
    kume: type[models.TextChoices], beklenen: tuple[str, ...]
) -> None:
    assert tuple(kume.values) == beklenen


@pytest.mark.parametrize("kume", [k for k, _ in BEKLENEN_DEGERLER], ids=lambda k: k.__name__)
def test_secenek_degerleri_turkce_buyuk_harf_ascii_etiketleri_dolu(
    kume: type[models.TextChoices],
) -> None:
    """Tasarım §5 O8."""
    for deger, etiket in kume.choices:
        assert deger.isascii() and deger == deger.upper(), deger
        assert str(etiket).strip(), deger


def test_idareci_gorunen_adi_program_yoneticisiyle_karismaz() -> None:
    """Plan F1c kararları "Kişiler ekranı"."""
    assert PersonKind.IDARECI.label == "İdareci"


def test_temel_model_soyuttur_ve_yumusak_silme_tasimaz() -> None:
    """Tasarım §5 O1 ve O4: dört temel alan; `deleted_at` yok."""
    assert OabBaseModel._meta.abstract is True
    adlar = {alan.name for alan in OabBaseModel._meta.get_fields()}
    assert adlar == {"created_at", "created_by", "updated_at", "updated_by"}


@isolate_apps("apps.oab")
def test_temel_alanlar_hesaba_baglanir_ve_ters_erisim_acmaz() -> None:
    """Tasarım §5 O4; `SISTEM` yazarının hesabı yoktur, yazar alanı boş olabilir."""

    class Ornek(OabBaseModel):
        class Meta:
            app_label = "oab"

    for ad in ("created_by", "updated_by"):
        alan = Ornek._meta.get_field(ad)
        assert isinstance(alan, ForeignKey)
        assert alan.remote_field.on_delete is models.PROTECT
        assert alan.remote_field.related_name == "+"
        assert alan.null is True


def _mutlak_ad(dosya: str, duzey: int, modul: str | None) -> str:
    """Göreli içe aktarmanın mutlak modül adı (`dosya` `backend/`'e göreli yoldur)."""
    if not duzey:
        return modul or ""
    paket = Path(dosya).parent.parts
    taban = paket[: len(paket) - (duzey - 1)]
    return ".".join([*taban, *([modul] if modul else [])])


def _oab_mi(ad: str) -> bool:
    return ad == "apps.oab" or ad.startswith("apps.oab.")


def _oab_aktarimi_mi(dosya: str, dugum: ast.Import | ast.ImportFrom | ast.Call) -> bool:
    if isinstance(dugum, ast.Import):
        return any(_oab_mi(ad.name) for ad in dugum.names)
    if isinstance(dugum, ast.ImportFrom):
        modul = _mutlak_ad(dosya, dugum.level, dugum.module)
        return _oab_mi(modul) or any(_oab_mi(f"{modul}.{ad.name}") for ad in dugum.names)
    cagrilan = getattr(dugum.func, "attr", getattr(dugum.func, "id", ""))
    return (
        cagrilan in ("import_module", "__import__")
        and bool(dugum.args)
        and isinstance(dugum.args[0], ast.Constant)
        and _oab_mi(str(dugum.args[0].value))
    )


def _oab_importlari(dosya: str, kaynak: str) -> list[int]:
    """Kaynakta `apps.oab`'yi içe aktaran satırlar (işlev içi ve dinamik içe aktarma dahil)."""
    return [
        dugum.lineno
        for dugum in ast.walk(ast.parse(kaynak))
        if isinstance(dugum, ast.Import | ast.ImportFrom | ast.Call)
        and _oab_aktarimi_mi(dosya, dugum)
    ]


@pytest.mark.parametrize(
    "kaynak",
    [
        "import apps.oab.models\n",
        "from apps.oab import models\n",
        "from apps.oab.models import TermStatus\n",
        "from apps import oab\n",
        "from ...oab import models\n",
        "from ... import oab\n",
        "def f():\n    from apps.oab.models import TermStatus\n",
        "import importlib\nimportlib.import_module('apps.oab.models')\n",
        "__import__('apps.oab.models')\n",
    ],
)
def test_bagimlilik_taramasi_ters_importu_yakalar(kaynak: str) -> None:
    """Sonda: tarama kırmızıya dönebiliyor. Sahte dosya `apps/okul/services/` altındadır."""
    assert _oab_importlari("apps/okul/services/ornek.py", kaynak)


@pytest.mark.parametrize(
    "kaynak",
    [
        'term = models.ForeignKey("oab.OabTerm", on_delete=models.PROTECT)\n',
        "from apps.okul.models import Account\n",
        "from apps.oabx import models\n",
        "from .oab import models\n",
        "yol = 'apps.oab.models'\n",
    ],
)
def test_bagimlilik_taramasi_mesru_kaynagi_gecirir(kaynak: str) -> None:
    """Dizeyle yabancı anahtar ve benzer adlı modül ihlal değildir."""
    assert _oab_importlari("apps/okul/ornek.py", kaynak) == []


def test_okul_ve_shared_oab_yi_ice_aktarmaz() -> None:
    """Plan "F1c adımları": göç grafiği çift yönlüdür, Python bağımlılığı tek yönlüdür."""
    ihlaller: list[str] = []
    taranan = 0
    for kok in (KOK / "apps" / "okul", KOK / "shared"):
        for yol in sorted(kok.rglob("*.py")):
            if "tests" in yol.parts:
                continue
            goreli = yol.relative_to(KOK).as_posix()
            taranan += 1
            ihlaller += [
                f"{goreli}:{satir}"
                for satir in _oab_importlari(goreli, yol.read_text(encoding="utf-8"))
            ]
    assert taranan > 50, "tarama kök dizinleri boş kaldı"
    assert ihlaller == []
