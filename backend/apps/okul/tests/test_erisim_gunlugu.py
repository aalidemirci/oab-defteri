"""Erişim günlüğü (tasarım §4.6.4, §4.6.2 kural 4, TK19; plan F1b-1 alt commit d).

Bölümler: model ve göç (kapalı tür kümesi, kısıtlar, değiştirilemezlik, toplu eklemenin reddi,
tetikleyici; kaynak taraması: tek yazar, tek silme yolu) · yazıcı (bağlam, tür, kimlik biçimi,
çıktı özeti) · `KVKK_SILME` satırının yazıcısı · saklama süresinin silmesi (sınır,
Europe/Istanbul gün sınırı, 29 Şubat, satırın içeriği, uydurma kişisel veri araması, kip
kilidi) · gün işi ve tetik (kilitliyken koşulsuz erteleme, kilit açılışının sinyali,
üretimdeki kayıtlar ve sırası, kapıyla uçtan uca). Kilitliyken gerçek silme işinin iş verisi
yazmadığı `test_kilitli_kip.py::test_kilitliyken_gun_isi_is_verisi_yazmaz`'dadır.

Kişi adları ve numaralar UYDURMADIR.
"""

from __future__ import annotations

import ast
import json
import re
import threading
import time
from collections.abc import Callable, Iterator
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import desktop
import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.okul import denetim_izi, erisim_gunlugu, masaustu_kanca
from apps.okul.erisim_gunlugu import ErisimGunluguYazilamadi
from apps.okul.models import (
    AccessKind,
    AccessLog,
    Account,
    AuditAction,
    AuditTrail,
    ImmutableRecord,
    Student,
    _AccessLogQuerySet,
)
from apps.okul.oturum import IZ_KIP_KILIDI, OTURUM, sistem_olarak, yazar_olarak
from apps.okul.services import app_password, persons
from apps.okul.tests.hesap_ortak import YENI_PAROLA
from conftest import TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA, TEST_TANITICI
from shared import crypto

pytestmark = pytest.mark.django_db

#: Göç 0010'un tetikleyici adı.
TETIKLEYICI = "okul_accesslog_no_update"
#: Uydurma kişi (gerçek kişi değildir).
UYDURMA_AD = "Nazlıcan"
UYDURMA_SOYAD = "Hayalpınaroğlu"
UYDURMA_OKUL_NO = "80080080088"
#: Uydurma belge özeti.
OZET = "ab" * 32


def yerel(
    yil: int, ay: int, gun: int, saat: int = 12, dakika: int = 0, saniye: int = 0
) -> datetime:
    """Europe/Istanbul'da verilen an (saat dilimli)."""
    return timezone.make_aware(datetime(yil, ay, gun, saat, dakika, saniye))


def satir(an: datetime, **alanlar: Any) -> AccessLog:
    """Verilen anlı satır (yazıcı anı kendisi koyar; geçmiş satır taklidi doğrudan yazılır)."""
    varsayilan: dict[str, Any] = {
        "account_id": TEST_HESAP_ID,
        "role": "yonetici",
        "kind": AccessKind.KISI_DOKUMU,
        "model": "okul.Student",
        "object_id": "7",
    }
    return AccessLog.objects.create(at=an, **{**varsayilan, **alanlar})


def son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else bas[0]


def satirlar(**suz: Any) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(**suz).order_by("seq"))


def kilitle() -> AuditTrail:
    """Zincir başlatılır ve oturum elle kilitlenir (`KILIT` satırı + çapa); `KILIT`'i verir."""
    with transaction.atomic():
        denetim_izi.olay(AuditAction.HESAP, model="okul.Account", object_id=TEST_HESAP_ID)
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    son: AuditTrail | None = AuditTrail.objects.order_by("-seq").first()
    assert son is not None and son.action == "KILIT"
    return son


def ac() -> None:
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


@pytest.fixture
def kanca_temiz() -> Iterator[None]:
    """Masaüstü kancaları süreç içidir: test önce ve sonra temizlenir."""
    masaustu_kanca._reset_for_tests()
    try:
        yield
    finally:
        masaustu_kanca._reset_for_tests()


# ============================================================ model ve göç


def test_tur_kumesi_anlik_goruntusu() -> None:
    """Tasarım §4.6.4: kapalı küme; yeni tür göçle eklenir (DB kısıtı da aynı kümedir)."""
    assert AccessKind.values == [
        "MASKESIZ_TCKN",
        "KISI_DOKUMU",
        "VELI_LISTESI_CIKTISI",
        "KISISEL_DISA_AKTARIM",
        "IHLAL_DOKUMU",
        "OZEL_NITELIKLI_EK",
        "OZEL_NITELIKLI_ALAN",
    ]


def test_satirin_sutunlari_deger_tasimaz() -> None:
    """Tasarım §4.6.4: kimlik, alan adı ve çıktı özeti; okunan değerin sütunu yoktur."""
    assert [alan.name for alan in AccessLog._meta.fields] == [
        "id",
        "at",
        "account",
        "role",
        "kind",
        "model",
        "object_id",
        "field",
        "document_sha256",
        "row_count",
    ]


@pytest.mark.parametrize(
    "alanlar",
    [
        pytest.param({"kind": "SIL"}, id="kume-disi-tur"),
        pytest.param({"role": ""}, id="bos-rol"),
        pytest.param({"role": "veli"}, id="kume-disi-rol"),
        pytest.param({"document_sha256": OZET}, id="ozet-sayisiz"),
        pytest.param({"row_count": 3}, id="sayi-ozetsiz"),
        pytest.param({"document_sha256": OZET[:63], "row_count": 3}, id="kisa-ozet"),
        pytest.param({"model": "", "object_id": "7"}, id="modelsiz-kimlik"),
        pytest.param({"object_id": "", "field": "first_name"}, id="kimliksiz-alan"),
    ],
)
def test_veritabani_kisitlari_reddeder(alanlar: dict[str, Any]) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        satir(timezone.now(), **alanlar)
    assert not AccessLog.objects.exists()


def test_hesapsiz_satir_reddedilir() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        satir(timezone.now(), account_id=None)


def test_cikti_satiri_kisitlara_uyar() -> None:
    kayit = satir(timezone.now(), document_sha256=OZET, row_count=0, model="", object_id="")
    assert AccessLog.objects.get(pk=kayit.pk).row_count == 0


def test_orm_ile_guncelleme_ve_silme_reddedilir() -> None:
    kayit = satir(timezone.now())
    kayit.object_id = "8"
    with pytest.raises(ImmutableRecord):
        kayit.save()
    with pytest.raises(ImmutableRecord):
        kayit.delete()
    with pytest.raises(ImmutableRecord):
        AccessLog.objects.filter(pk=kayit.pk).update(object_id="8")
    with pytest.raises(ImmutableRecord):
        AccessLog.objects.all().delete()
    with pytest.raises(ImmutableRecord):
        AccessLog.objects.bulk_update([kayit], ["object_id"])
    assert AccessLog.objects.get(pk=kayit.pk).object_id == "7"


def test_orm_ile_toplu_ekleme_reddedilir() -> None:
    """Toplu ekleme `save()`'i ve yazıcının biçim denetimini atlardı; satırı yalnız yazıcı yazar."""
    ad_tasiyan = AccessLog(
        at=timezone.now(),
        account_id=TEST_HESAP_ID,
        role="yonetici",
        kind=AccessKind.KISI_DOKUMU,
        model="okul.Student",
        object_id=UYDURMA_AD,
    )
    with pytest.raises(ImmutableRecord, match="toplu"):
        AccessLog.objects.bulk_create([ad_tasiyan])
    assert not AccessLog.objects.exists()


def test_model_yontemlerini_atlayan_guncellemeyi_tetikleyici_keser() -> None:
    """`_base_manager` ve ham SQL model yöntemlerini atlar; `BEFORE UPDATE` tetikleyicisi keser."""
    kayit = satir(timezone.now())
    with pytest.raises(IntegrityError, match="değiştirilemez"), transaction.atomic():
        AccessLog._base_manager.filter(pk=kayit.pk).update(object_id="8")
    with pytest.raises(IntegrityError, match="değiştirilemez"), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE okul_accesslog SET at = %s WHERE id = %s", ["2000-01-01", kayit.pk]
            )
    assert AccessLog.objects.get(pk=kayit.pk).object_id == "7"


def test_silme_tetikleyicisi_bilerek_yoktur() -> None:
    """Koşulsuz bir `BEFORE DELETE` saklama süresinin meşru silmesini de keserdi (`AccessLog`
    belge dizesi); program içi silmeyi model yöntemleri, aşağıdaki kaynak taraması (tek silme
    yolu) ve uçların tablo karşılaştırması (`test_izsiz_yazim.py`) tutar."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_accesslog' ORDER BY name"
        )
        bulunan = cursor.fetchall()
    assert [ad for ad, _ in bulunan] == [TETIKLEYICI]
    assert "BEFORE UPDATE" in bulunan[0][1] and "RAISE(ABORT" in bulunan[0][1]


def _program_kaynaklari() -> dict[str, str]:
    """Programın kaynağı (testler ve göçler hariç): `backend/`'e göreli yol → metin.

    Kökler izsiz yazım taramasınınkilerdir: `apps/`, `shared` ve masaüstü kabuğu.
    """
    kok = Path(__file__).resolve().parents[3]
    masaustu = Path(desktop.__file__).resolve().parent
    kaynaklar: dict[str, str] = {}
    for dizin, taban in ((kok / "apps", kok), (kok / "shared", kok), (masaustu, masaustu.parent)):
        for yol in sorted(dizin.rglob("*.py")):
            if "tests" in yol.parts or "migrations" in yol.parts:
                continue
            kaynaklar[yol.relative_to(taban).as_posix()] = yol.read_text(encoding="utf-8")
    return kaynaklar


def _cagri_yerleri(ad: str) -> tuple[int, set[tuple[str, str]]]:
    """Programın kaynağında (testler ve göçler hariç) `.ad(…)` çağrıları.

    (toplam çağrı sayısı, {(dosya, çağıran işlev)}).
    """
    toplam = 0
    yerler: set[tuple[str, str]] = set()

    def cagri_mi(dugum: ast.AST) -> bool:
        return (
            isinstance(dugum, ast.Call)
            and isinstance(dugum.func, ast.Attribute)
            and dugum.func.attr == ad
        )

    for yol, kaynak in _program_kaynaklari().items():
        agac = ast.parse(kaynak)
        toplam += sum(1 for dugum in ast.walk(agac) if cagri_mi(dugum))
        for islev in ast.walk(agac):
            if isinstance(islev, ast.FunctionDef | ast.AsyncFunctionDef) and any(
                cagri_mi(dugum) for dugum in ast.walk(islev)
            ):
                yerler.add((yol, islev.name))
    return toplam, yerler


def test_silme_ilkesinin_tek_cagirani_silme_servisidir() -> None:
    """Tek silme yolunu (`_saklama_disini_sil`) yalnız süreyi hesaplayan silme servisi çağırır."""
    toplam, yerler = _cagri_yerleri("_saklama_disini_sil")
    assert toplam == 1
    assert yerler == {("apps/okul/erisim_gunlugu.py", "suresi_dolanlari_sil")}


#: Kökü taranan model olan zincirde geçince zinciri YAZIM (ya da silme) yapan adlar: yönetici ve
#: queryset yazımları, örnek yazımı, Django'nun iç yazıcıları, ham sorgu, model yöntemlerini
#: atlayan yöneticiler ve tek silme ilkesi. Kurucu çağrısı (`AccessLog(…)`) da yazımdır.
_GUNLUK_YAZIM_ADLARI = frozenset(
    {
        "create",
        "get_or_create",
        "update_or_create",
        "bulk_create",
        "bulk_update",
        "update",
        "delete",
        "save",
        "_saklama_disini_sil",
        "_insert",
        "_batched_insert",
        "_update",
        "_raw_delete",
        "raw",
        "_base_manager",
        "_default_manager",
    }
)
#: Zincirin kurucu çağrısı, takma adla ve dizeyle başvuru (yazım listesindeki işaretler).
_KURUCU = "()"
_TAKMA_AD = "<takma ad>"
_DIZE = "<dize>"
#: Dizede modelin (`AccessLog`, `okul.AccessLog`) ya da tablonun (`okul_accesslog`) adı; DB
#: nesnelerinin adları (`ck_accesslog_kind`, `okul_accesslog_at_idx`) erişim yolu değildir.
_GUNLUK_ADI = re.compile(r"\b(?:okul_)?accesslog\b", re.IGNORECASE)

#: Erişim günlüğüne yazan ya da ondan silen zincirlerin İZİNLİ yerleri: (dosya, birim, zincirin
#: adları). Tek yazar `erisim_gunlugu.yaz`, tek silme yolu `suresi_dolanlari_sil` (tasarım
#: §4.6.4; `AccessLog` belge dizesi). Başka her yer — izli bir servis de — testi düşürür;
#: izsiz yazım taraması izli işlevin bütün yazımlarını izli saydığı için bunu göremez.
GUNLUK_YAZIM_YERLERI = {
    ("apps/okul/erisim_gunlugu.py", "yaz", ("objects", "create")),
    (
        "apps/okul/erisim_gunlugu.py",
        "suresi_dolanlari_sil",
        ("objects", "all", "_saklama_disini_sil"),
    ),
}


def _birim_adi(dugum: ast.AST, ust: dict[ast.AST, ast.AST]) -> str:
    """Düğümü içeren tanımların noktalı adı (`Sınıf.yöntem`, `f.ic`); modül düzeyinde `<modül>`."""
    adlar: list[str] = []
    while dugum in ust:
        dugum = ust[dugum]
        if isinstance(dugum, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            adlar.append(dugum.name)
    return ".".join(reversed(adlar)) or "<modül>"


def _kok_yazimlari(
    kaynaklar: dict[str, str],
    *,
    kok: str,
    ad_deseni: re.Pattern[str],
    okuma_dizeleri: tuple[tuple[str, str], ...] = (),
) -> set[tuple[str, str, tuple[str, ...]]]:
    """Kökü `kok` modeli olan yazım zincirleri ve kökü gizleyen başvurular: (dosya, birim, adlar).

    Örneklerdeki model `AccessLog`'dur; `Attachment` taraması `test_dosya_deposu.py`'dedir.
    Kök modelin adı ya da `x.AccessLog` özniteliğidir; zincir kökten yukarı öznitelik,
    çağrı ve indisle uzar (`AccessLog.objects.all()._saklama_disini_sil(…)` →
    `("objects", "all", "_saklama_disini_sil")`). Zincirde `_GUNLUK_YAZIM_ADLARI`'ndan biri
    geçerse ya da kök çağrılırsa (kurucu) yazımdır; okuma (`filter`, `aggregate`) ve kökün
    argüman olarak verilmesi (`kvkk_silme(AccessLog, …)`) yazım değildir. Kökü gizleyen
    başvurular adlarıyla raporlanır: `import … AccessLog as X` ve `X = AccessLog` (`_TAKMA_AD`),
    belge olmayan bir dizede tablonun ya da modelin adı (`get_model("okul", "AccessLog")`, ham
    SQL; `_DIZE`; adı `ad_deseni` tanır). Birim modül düzeyinde `<modül>`, değilse iç içe
    tanımların noktalı adıdır. `okuma_dizeleri` ham SQL okumasına verilen izindir: (dosya, dizenin
    tam metni) çiftleri sayılmaz, aynı dosyadaki başka dize yine yakalanır.
    Kalan sınır veri akışıdır (queryset'i değişkende tutup sonra yazmak, modeli genel bir
    yardımcıya vermek): uçlar için onu izsiz yazım taramasının tablo karşılaştırması yakalar.
    """
    bulunan: set[tuple[str, str, tuple[str, ...]]] = set()
    for yol, kaynak in kaynaklar.items():
        agac = ast.parse(kaynak)
        ust = {cocuk: dugum for dugum in ast.walk(agac) for cocuk in ast.iter_child_nodes(dugum)}
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.ImportFrom):
                for ad in dugum.names:
                    if ad.name == kok and ad.asname not in (None, kok):
                        bulunan.add((yol, _birim_adi(dugum, ust), (_TAKMA_AD,)))
                continue
            if (
                isinstance(dugum, ast.Constant)
                and isinstance(dugum.value, str)
                and ad_deseni.search(dugum.value)
                and not isinstance(ust.get(dugum), ast.Expr)  # belge dizesi
            ):
                if (yol, dugum.value) not in okuma_dizeleri:
                    bulunan.add((yol, _birim_adi(dugum, ust), (_DIZE,)))
                continue
            kok_mu = (isinstance(dugum, ast.Name) and dugum.id == kok) or (
                isinstance(dugum, ast.Attribute) and dugum.attr == kok
            )
            if not kok_mu:
                continue
            if isinstance(ust.get(dugum), ast.Assign | ast.AnnAssign | ast.NamedExpr) and (
                getattr(ust[dugum], "value", None) is dugum
            ):
                bulunan.add((yol, _birim_adi(dugum, ust), (_TAKMA_AD,)))
                continue
            zincir: list[str] = []
            uc = dugum
            while True:
                sonraki = ust.get(uc)
                if isinstance(sonraki, ast.Attribute) and sonraki.value is uc:
                    zincir.append(sonraki.attr)
                elif isinstance(sonraki, ast.Call) and sonraki.func is uc:
                    if uc is dugum:
                        zincir.append(_KURUCU)
                elif not (isinstance(sonraki, ast.Subscript) and sonraki.value is uc):
                    break
                assert sonraki is not None
                uc = sonraki
            if _KURUCU in zincir or _GUNLUK_YAZIM_ADLARI & set(zincir):
                bulunan.add((yol, _birim_adi(dugum, ust), tuple(zincir)))
    return bulunan


def _gunluk_yazimlari(kaynaklar: dict[str, str]) -> set[tuple[str, str, tuple[str, ...]]]:
    """Kökü `AccessLog` olan yazım zincirleri (`_kok_yazimlari`)."""
    return _kok_yazimlari(kaynaklar, kok="AccessLog", ad_deseni=_GUNLUK_ADI)


def test_erisim_gunlugune_yalniz_yazici_yazar_yalniz_silme_servisi_siler() -> None:
    """`AccessLog`'un tek yazarı `erisim_gunlugu.yaz`, tek silme yolu `suresi_dolanlari_sil`'dir
    (inceleme bulgusu: izsiz yazım taraması izli bir işlevdeki doğrudan yazımı izli sayıyordu).
    Eşitlik iki yönlüdür: başka yazım yoktur, izinli iki zincir hâlâ vardır."""
    assert _gunluk_yazimlari(_program_kaynaklari()) == GUNLUK_YAZIM_YERLERI


#: Programa eklenen erişim günlüğü yazımları ve atlatmaları: her biri yakalanmalıdır.
_GUNLUK_SONDASI = '''
"""`AccessLog.objects.create(...)` belge metnidir; `okul_accesslog` da."""
from apps.okul import denetim_izi, models
from apps.okul.models import AccessLog
from apps.okul.models import AccessLog as Gunluk
from django.apps import apps as django_apps


def izli_serviste_dogrudan_yazim(ogrenci):
    denetim_izi.olay("BASIM", model="okul.Student", object_id=str(ogrenci.pk))
    AccessLog.objects.create(object_id="Uydurma Ad")


def toplu_ekleme():
    models.AccessLog.objects.bulk_create([AccessLog(object_id="1")])


def kurucuyla_yazim():
    AccessLog(object_id="1").save()


def yoneticiyi_atlayan_silme(ogrenci):
    denetim_izi.degisiklik(ogrenci, onceki=None)
    AccessLog._base_manager.filter(object_id=str(ogrenci.pk)).delete()


def ilkelle_izli_silme(sinir, gun):
    adet = AccessLog.objects.all()._saklama_disini_sil(sinir)
    denetim_izi.kvkk_silme(AccessLog, adet=adet, en_yeni=gun, tetik="GUN_ISI")


def takma_adla():
    tablo = AccessLog
    tablo.objects.get_or_create(object_id="1")


def model_adi_dizeyle():
    return django_apps.get_model("okul", "AccessLog")


def tablo_adi_dizeyle(cursor):
    cursor.execute("DELETE FROM okul_accesslog")


class Servis:
    def guncelle(self, pk):
        AccessLog.objects.filter(pk=pk)[0].delete()


def okuma():
    """Okuma yazım değildir; DB nesnesinin adı erişim yolu değildir."""
    en_yeni = AccessLog.objects.filter(kind="KISI_DOKUMU").aggregate(an=None)["an"]
    return denetim_izi.model_etiketi(AccessLog), en_yeni, "ck_accesslog_kind"
'''


def test_gunluk_taramasi_izli_islevdeki_yazimi_ve_atlatmalari_yakalar() -> None:
    """Taramanın kendisi: izli işlevdeki (`olay`, `degisiklik`, `kvkk_silme` çağıran) doğrudan
    yazım ve silme, toplu ekleme, kurucu, model yöntemlerini atlayan yönetici, takma ad ve
    dizeyle başvuru yakalanır; belge metni, okuma ve argüman olarak verilen model sayılmaz."""
    bulunan = {
        (birim, adlar)
        for _, birim, adlar in _gunluk_yazimlari({"apps/okul/services/sonda.py": _GUNLUK_SONDASI})
    }
    assert bulunan == {
        ("izli_serviste_dogrudan_yazim", ("objects", "create")),
        ("toplu_ekleme", ("objects", "bulk_create")),
        ("toplu_ekleme", (_KURUCU,)),
        ("kurucuyla_yazim", (_KURUCU, "save")),
        ("yoneticiyi_atlayan_silme", ("_base_manager", "filter", "delete")),
        ("ilkelle_izli_silme", ("objects", "all", "_saklama_disini_sil")),
        ("<modül>", (_TAKMA_AD,)),
        ("takma_adla", (_TAKMA_AD,)),
        ("model_adi_dizeyle", (_DIZE,)),
        ("tablo_adi_dizeyle", (_DIZE,)),
        ("Servis.guncelle", ("objects", "filter", "delete")),
    }


# ============================================================ yazıcı


def test_yazici_okuyan_hesabi_ve_rolu_baglamdan_yazar() -> None:
    once = timezone.now()
    kayit = erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU, model=Student, object_id=12)

    kayit = AccessLog.objects.get(pk=kayit.pk)
    assert (str(kayit.account_id), kayit.role, kayit.kind) == (
        TEST_HESAP_ID,
        "yonetici",
        "KISI_DOKUMU",
    )
    assert (kayit.model, kayit.object_id, kayit.field) == ("okul.Student", "12", "")
    assert (kayit.document_sha256, kayit.row_count) == ("", None)
    assert once <= kayit.at <= timezone.now()


def test_yazici_kimligi_tek_metne_indirir_ve_alan_adini_yazar() -> None:
    hesap = erisim_gunlugu.yaz(
        AccessKind.OZEL_NITELIKLI_ALAN,
        model=Account,
        object_id=TEST_HESAP_ID.replace("-", "").upper(),
        field="display_name",
    )
    sayi = erisim_gunlugu.yaz(AccessKind.MASKESIZ_TCKN, model=Student, object_id="15", field="id")
    assert (hesap.model, hesap.object_id, hesap.field) == (
        "okul.Account",
        TEST_HESAP_ID,
        "display_name",
    )
    assert (sayi.object_id, sayi.field) == ("15", "id")


def test_yazici_cikti_ozetini_ve_satir_sayisini_yazar() -> None:
    kayit = erisim_gunlugu.yaz(AccessKind.VELI_LISTESI_CIKTISI, document_sha256=OZET, row_count=42)
    assert (kayit.model, kayit.object_id, kayit.document_sha256, kayit.row_count) == (
        "",
        "",
        OZET,
        42,
    )


def test_yazici_baglamsiz_ve_sistem_yazarini_reddeder() -> None:
    with yazar_olarak(None), pytest.raises(ErisimGunluguYazilamadi, match="Yazar bağlamı"):
        erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU)
    with sistem_olarak(), pytest.raises(ErisimGunluguYazilamadi, match="program adına"):
        erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU)
    assert not AccessLog.objects.exists()


@pytest.mark.parametrize(
    ("tur", "secenekler"),
    [
        pytest.param("SIL", {}, id="kume-disi-tur"),
        pytest.param("kisi_dokumu", {}, id="kucuk-harfli-tur"),
        pytest.param("KISI_DOKUMU", {"model": "okul.Student"}, id="model-metin"),
        pytest.param("KISI_DOKUMU", {"model": dict}, id="model-degil"),
        pytest.param(
            "KISI_DOKUMU", {"model": Student, "object_id": f"{UYDURMA_AD}"}, id="kimlikte-ad"
        ),
        pytest.param("KISI_DOKUMU", {"model": Student, "object_id": "12; 13"}, id="kimlikte-metin"),
        pytest.param("KISI_DOKUMU", {"model": Student, "object_id": True}, id="kimlik-bool"),
        pytest.param("KISI_DOKUMU", {"model": Student, "object_id": ""}, id="bos-kimlik"),
        pytest.param(
            "KISI_DOKUMU", {"model": Account, "object_id": UYDURMA_SOYAD}, id="uuid-yerine-ad"
        ),
        pytest.param(
            "OZEL_NITELIKLI_ALAN",
            {"model": Student, "object_id": 3, "field": f"{UYDURMA_AD} {UYDURMA_SOYAD}"},
            id="alanda-deger",
        ),
        pytest.param(
            "OZEL_NITELIKLI_ALAN",
            {"model": Student, "object_id": 3, "field": "classsection"},
            id="alan-degil",
        ),
        pytest.param("OZEL_NITELIKLI_ALAN", {"model": Student, "field": "id"}, id="kimliksiz-alan"),
        pytest.param("KISI_DOKUMU", {"object_id": 3}, id="modelsiz-kimlik"),
        pytest.param("KISI_DOKUMU", {"field": "id"}, id="modelsiz-alan"),
        pytest.param(
            "KISISEL_DISA_AKTARIM",
            {"document_sha256": OZET.upper(), "row_count": 1},
            id="buyuk-ozet",
        ),
        pytest.param(
            "KISISEL_DISA_AKTARIM", {"document_sha256": OZET[:62], "row_count": 1}, id="kisa-ozet"
        ),
        pytest.param("KISISEL_DISA_AKTARIM", {"document_sha256": OZET}, id="sayisiz-ozet"),
        pytest.param("KISISEL_DISA_AKTARIM", {"row_count": 1}, id="ozetsiz-sayi"),
        pytest.param(
            "KISISEL_DISA_AKTARIM", {"document_sha256": OZET, "row_count": -1}, id="eksi-sayi"
        ),
        pytest.param(
            "KISISEL_DISA_AKTARIM", {"document_sha256": OZET, "row_count": True}, id="bool-sayi"
        ),
        pytest.param("KISISEL_DISA_AKTARIM", {}, id="ciktisiz-disa-aktarim"),
        pytest.param("VELI_LISTESI_CIKTISI", {}, id="ciktisiz-veli-listesi"),
        pytest.param("MASKESIZ_TCKN", {"model": Student, "object_id": 3}, id="alansiz-tckn"),
        pytest.param(
            "MASKESIZ_TCKN",
            {
                "model": Student,
                "object_id": 3,
                "field": "id",
                "document_sha256": OZET,
                "row_count": 1,
            },
            id="dosyada-tckn",
        ),
    ],
)
def test_yazici_kume_disi_turu_serbest_metni_ve_degeri_reddeder(
    tur: str, secenekler: dict[str, Any]
) -> None:
    with pytest.raises(ErisimGunluguYazilamadi):
        erisim_gunlugu.yaz(tur, **secenekler)
    assert not AccessLog.objects.exists()


def test_yazici_iz_satiri_yazmaz() -> None:
    """Zincir dışıdır (tasarım §4.6.4): okumanın kaydı denetim izinde satır doğurmaz."""
    bas = son_seq()
    erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU, model=Student, object_id=1)
    assert son_seq() == bas


# ============================================================ KVKK_SILME satırının yazıcısı


def _kvkk_silme(**secenekler: Any) -> AuditTrail:
    varsayilan: dict[str, Any] = {"adet": 1, "en_yeni": date(2024, 1, 1), "tetik": "GUN_ISI"}
    with sistem_olarak(), transaction.atomic():
        return denetim_izi.kvkk_silme(AccessLog, **{**varsayilan, **secenekler})


@pytest.mark.parametrize(
    "secenekler",
    [
        pytest.param({"adet": 0}, id="sifir-adet"),
        pytest.param({"adet": True}, id="bool-adet"),
        pytest.param({"adet": "3"}, id="metin-adet"),
        pytest.param({"en_yeni": yerel(2024, 1, 1)}, id="an-tarih-degil"),
        pytest.param({"en_yeni": "2024-01-01"}, id="metin-tarih"),
        pytest.param({"tetik": "ELLE"}, id="kume-disi-tetik"),
        pytest.param({"alanlar": []}, id="bos-alanlar"),
        pytest.param({"alanlar": ["at", "at"]}, id="yinelenen-alan"),
        pytest.param({"alanlar": [UYDURMA_AD]}, id="alanda-deger"),
        pytest.param({"alanlar": ["id"]}, id="kimlik-alani"),
    ],
)
def test_kvkk_silme_satiri_bicimsiz_degeri_reddeder(secenekler: dict[str, Any]) -> None:
    bas = son_seq()
    with pytest.raises(denetim_izi.IzYazilamadi):
        _kvkk_silme(**secenekler)
    assert son_seq() == bas


def test_kvkk_silme_satiri_kilitliyken_yazilmaz() -> None:
    app_password.lock()
    with pytest.raises(denetim_izi.IzAnahtariBellekteDegil):
        _kvkk_silme()


# ============================================================ saklama süresinin silmesi


@pytest.mark.parametrize(
    ("bugun", "sinir"),
    [
        (date(2026, 11, 2), date(2024, 11, 2)),
        (date(2026, 2, 28), date(2024, 2, 28)),
        (date(2026, 3, 1), date(2024, 3, 1)),
        (date(2028, 2, 29), date(2026, 3, 1)),  # iki yıl önce 29 Şubat yok
        (date(2024, 2, 29), date(2022, 3, 1)),
    ],
)
def test_saklama_siniri_takvim_yilidir(bugun: date, sinir: date) -> None:
    assert erisim_gunlugu.SAKLAMA_SURESI_YIL == 2
    assert erisim_gunlugu.saklama_siniri(bugun) == sinir


@pytest.mark.parametrize(
    ("bugun", "kalir"),
    [
        pytest.param(date(2025, 6, 14), True, id="bir-gun-once"),
        pytest.param(date(2025, 6, 15), True, id="tam-iki-yil"),
        pytest.param(date(2025, 6, 16), False, id="bir-gun-sonra"),
    ],
)
def test_silme_siniri_tam_iki_yildir(bugun: date, kalir: bool) -> None:
    """Satır yıl dönümü günü durur, ertesi gün silinir: süre hiçbir satırda kısalmaz."""
    kayit = satir(yerel(2023, 6, 15, 23, 59))
    erisim_gunlugu.suresi_dolanlari_sil(bugun=bugun)
    assert AccessLog.objects.filter(pk=kayit.pk).exists() is kalir


def test_silme_gun_siniri_europe_istanbuldur() -> None:
    """İki satır UTC'de aynı gündedir (20:59Z, 21:00Z), yerel günleri ayrıdır."""
    aksam = satir(yerel(2023, 6, 15, 23, 59, 59))
    gece = satir(yerel(2023, 6, 16, 0, 0, 30))
    assert aksam.at.astimezone(timezone.get_current_timezone()).date() == date(2023, 6, 15)

    assert erisim_gunlugu.suresi_dolanlari_sil(bugun=date(2025, 6, 16)) == 1

    assert list(AccessLog.objects.values_list("pk", flat=True)) == [gece.pk]


@pytest.mark.parametrize(
    ("satir_gunu", "bugun", "kalir"),
    [
        pytest.param(date(2024, 2, 29), date(2026, 2, 28), True, id="29-subat-yil-donumu"),
        pytest.param(date(2024, 2, 29), date(2026, 3, 1), False, id="29-subat-ertesi"),
        pytest.param(date(2022, 2, 28), date(2024, 2, 28), True, id="28-subat-yil-donumu"),
        pytest.param(date(2022, 2, 28), date(2024, 2, 29), False, id="ertesi-gun-29-subat"),
        pytest.param(date(2022, 3, 1), date(2024, 2, 29), True, id="1-mart-29-subatta"),
    ],
)
def test_silme_29_subat_siniri(satir_gunu: date, bugun: date, kalir: bool) -> None:
    kayit = satir(yerel(satir_gunu.year, satir_gunu.month, satir_gunu.day))
    erisim_gunlugu.suresi_dolanlari_sil(bugun=bugun)
    assert AccessLog.objects.filter(pk=kayit.pk).exists() is kalir


def test_bugunden_sonraki_gun_verilemez() -> None:
    kayit = satir(yerel(2020, 1, 1))
    with pytest.raises(ValueError, match="bugünden sonra"):
        erisim_gunlugu.suresi_dolanlari_sil(bugun=timezone.localdate() + timedelta(days=1))
    assert AccessLog.objects.filter(pk=kayit.pk).exists()


def test_silinecek_satir_yoksa_iz_satiri_yazilmaz() -> None:
    satir(timezone.now())
    bas = son_seq()
    assert erisim_gunlugu.suresi_dolanlari_sil() == 0
    assert son_seq() == bas
    assert AccessLog.objects.count() == 1


def _iz_metni() -> str:
    """`okul_audittrail`'in BÜTÜN sütunları, ham SQL ile (ORM dönüşümü yok)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail ORDER BY seq")
        return json.dumps([list(map(str, s)) for s in cursor.fetchall()], ensure_ascii=False)


def test_kvkk_silme_satiri_kisisizdir_ve_tek_islemdedir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tasarım §4.6.2 kural 4 ve 6: uydurma ad ve numaralı kişinin okuma kayıtları silinir; tek
    `KVKK_SILME` satırı (model, alan adları, adet, en yeni gün, tetik; SISTEM) yazılır ve denetim
    izinin HİÇBİR sütununda uydurma kişisel veri yoktur."""
    ogrenci = persons.create_student(
        first_name=UYDURMA_AD,
        last_name=UYDURMA_SOYAD,
        student_number=UYDURMA_OKUL_NO,
        class_level=9,
        class_section="A",
    )
    eski = timezone.now() - timedelta(days=3 * 366)
    with monkeypatch.context() as yama:  # okuma iki yıldan eskiymiş gibi: yazıcının kendi yolu
        yama.setattr(timezone, "now", lambda: eski)
        erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU, model=Student, object_id=ogrenci.pk)
        erisim_gunlugu.yaz(
            AccessKind.KISISEL_DISA_AKTARIM,
            model=Student,
            object_id=ogrenci.pk,
            document_sha256=OZET,
            row_count=1,
        )
    yeni = erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU, model=Student, object_id=ogrenci.pk)
    bas = son_seq()

    assert erisim_gunlugu.suresi_dolanlari_sil() == 2

    assert list(AccessLog.objects.values_list("pk", flat=True)) == [yeni.pk]
    (silme,) = satirlar(seq__gt=bas)
    assert (silme.action, silme.actor, silme.account_id, silme.role) == (
        "KVKK_SILME",
        "SISTEM",
        None,
        "",
    )
    assert (silme.model, silme.object_id, silme.record_mac, silme.key_mode) == (
        "okul.AccessLog",
        "",
        "",
        "ACIK",
    )
    assert silme.changed_fields == [
        "at",
        "account",
        "role",
        "kind",
        "model",
        "object_id",
        "field",
        "document_sha256",
        "row_count",
    ]
    assert silme.values == {
        "adet": [None, 2],
        "en_yeni": [None, timezone.localdate(eski).isoformat()],
        "tetik": [None, "GUN_ISI"],
    }
    assert denetim_izi.zinciri_dogrula() == []

    metin = _iz_metni()
    for deger in (UYDURMA_AD, UYDURMA_SOYAD, UYDURMA_OKUL_NO):
        assert deger not in metin
    silme_metni = json.dumps(denetim_izi.satir_alanlari(silme), default=str)
    assert TEST_HESAP_ID not in silme_metni and OZET not in silme_metni


def test_iz_satiri_yazilamazsa_silme_geri_alinir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Yazma kuralı 1: silme ve `KVKK_SILME` satırı aynı işlemdedir; biri düşerse ikisi de."""
    kayit = satir(yerel(2020, 1, 1))
    bas = son_seq()

    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    monkeypatch.setattr(denetim_izi, "kvkk_silme", yazilamadi)
    with pytest.raises(denetim_izi.IzYazilamadi):
        erisim_gunlugu.suresi_dolanlari_sil()

    assert AccessLog.objects.filter(pk=kayit.pk).exists()
    assert son_seq() == bas


def test_silme_kilitliyken_hicbir_sey_yazmaz() -> None:
    kayit = satir(yerel(2020, 1, 1))
    bas = son_seq()
    app_password.lock()

    with pytest.raises(denetim_izi.IzAnahtariBellekteDegil):
        erisim_gunlugu.suresi_dolanlari_sil()

    assert AccessLog.objects.filter(pk=kayit.pk).exists()
    assert son_seq() == bas


def test_anahtar_denetimi_silme_ve_iz_satiri_kip_kilidi_altindadir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Modül başlığı "SİLME": anahtarların bellekte olup olmadığı, silme ve `KVKK_SILME` satırı
    `IZ_KIP_KILIDI` bu iş parçacığındayken yapılır. Başka bir iş parçacığı (boşta kilit) bu
    arada kilidi alamaz: `KILIT` satırı, çapa ve anahtarların düşmesi işin ortasına girmez,
    açık kip `KVKK_SILME` satırı çapadan sonraya düşmez (inceleme bulgusu: kilitsiz mutant
    bütün testlerden geçiyordu)."""
    satir(yerel(2020, 1, 1))
    gorulen: list[tuple[str, bool]] = []

    def kilit_altinda(ad: str, asil: Callable[..., Any]) -> Callable[..., Any]:
        def sarmal(*args: Any, **kwargs: Any) -> Any:
            tutuluyor = not _baska_is_parcacigi_alabilir(IZ_KIP_KILIDI, sure=0.05)
            gorulen.append((ad, tutuluyor))
            return asil(*args, **kwargs)

        return sarmal

    monkeypatch.setattr(crypto, "is_unlocked", kilit_altinda("anahtar", crypto.is_unlocked))
    monkeypatch.setattr(
        _AccessLogQuerySet,
        "_saklama_disini_sil",
        kilit_altinda("silme", _AccessLogQuerySet._saklama_disini_sil),
    )
    monkeypatch.setattr(denetim_izi, "kvkk_silme", kilit_altinda("iz", denetim_izi.kvkk_silme))

    assert erisim_gunlugu.suresi_dolanlari_sil() == 1

    assert {ad for ad, _ in gorulen} == {"anahtar", "silme", "iz"}
    assert all(tutuluyor for _, tutuluyor in gorulen), gorulen
    assert _baska_is_parcacigi_alabilir(IZ_KIP_KILIDI)  # iş bitince bırakılır


# ============================================================ gün işi ve tetik


def test_uretimde_acilista_gun_kapisina_kaydedilir(kanca_temiz: None, tmp_path: Path) -> None:
    """Üretim yolu: `OkulConfig.ready` → `masaustu_kanca` → masaüstünün `gun_kapisi_kur`'u."""
    from desktop.main import gun_kapisi_kur
    from desktop.paths import ENV_APP_HOME, resolve_app_paths

    django_apps.get_app_config("okul").ready()
    kapi = gun_kapisi_kur(resolve_app_paths(environ={ENV_APP_HOME: str(tmp_path)}))

    assert kapi.is_adlari == ("gunluk-yedek", erisim_gunlugu.SILME_ISI)


def _silme_isi() -> masaustu_kanca.GunlukIsKaydi:
    django_apps.get_app_config("okul").ready()
    (kayit,) = [is_ for is_ in masaustu_kanca.gunluk_isler() if is_.ad == erisim_gunlugu.SILME_ISI]
    return kayit


def test_gun_isi_sistem_adina_siler(kanca_temiz: None) -> None:
    """Kapının işi yazar bağlamı olmadan da (`od-gunluk`) `SISTEM` adına yazar."""
    satir(yerel(2020, 1, 1))
    with yazar_olarak(None):
        assert _silme_isi().calistir() is True
    (silme,) = satirlar(action="KVKK_SILME")
    assert silme.actor == "SISTEM"
    assert not AccessLog.objects.exists()


def test_kilitliyken_silinecek_satir_yoksa_da_ertelenir_ve_gunluk_okunmaz(
    kanca_temiz: None,
) -> None:
    """Karar (plan F1b-1 "Silme gün işidir; kilitliyken ertelenir", koşulsuz; modül başlığı
    "hiçbir şey okunmaz"): kilitliyken silme, silinecek satır olup olmadığına BAKMADAN
    ertelenir. Erişim günlüğü tablosuna tek sorgu gitmez, iş False döner (gün damgalanmaz),
    `GUN_ISI` satırı yazılır (inceleme bulgusu: önce okuyup boşsa dönen mutant geçiyordu)."""
    taze = satir(timezone.now())
    kayit = _silme_isi()
    capa = kilitle()

    with CaptureQueriesContext(connection) as sorgular:
        assert kayit.calistir() is False

    okumalar = [s["sql"] for s in sorgular.captured_queries if "okul_accesslog" in s["sql"]]
    assert okumalar == []
    (ertele,) = satirlar(seq__gt=capa.seq)
    assert (ertele.action, ertele.object_id, ertele.key_mode) == (
        "GUN_ISI",
        erisim_gunlugu.SILME_ISI,
        "KILITLI",
    )
    assert list(AccessLog.objects.values_list("pk", flat=True)) == [taze.pk]


def test_masaustu_yokken_sinyal_etkisizdir(kanca_temiz: None) -> None:
    assert masaustu_kanca.ertelenen_gun_islerini_dene() is False


def test_uretim_sirasinda_cikis_kaydi_sinyali_silmez_kapanis_dusurur(
    kanca_temiz: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Üretimdeki iki kayıt taklitsiz (`desktop.main`, `masaustu_kanca`): `serve` önce kapının
    sinyalini kaydeder, sonra `run_window_session` çıkış kancasını; ikinci kayıt birincisini
    SİLMEZ (verilmeyen kanca değişmez), pencere açıkken kilit açılışının sinyali kapıya ulaşır
    (TK19 "ilk kilit açılışında koşar"). Kapanışta `_kancalari_birak` ikisini de düşürür
    (inceleme bulgusu: kayıt sırası yalnız taklitle sınanıyordu)."""
    from desktop import main as main_mod

    sinyaller: list[str] = []
    pencerede: list[bool] = []

    def pencere(url: str, *, storage_path: Path, controller: Any, **_: Any) -> None:
        # Pencere açıkken bir kilit açılışı (`app_password._start_session`'ın son adımı).
        pencerede.append(masaustu_kanca.ertelenen_gun_islerini_dene())

    monkeypatch.setattr(main_mod, "open_window", pencere)
    main_mod._kancalari_kaydet(ertelenenleri_dene=lambda: sinyaller.append("dene"))  # `serve`
    main_mod.run_window_session("http://127.0.0.1:1/", tmp_path, None, platform="win32")

    assert pencerede == [True]
    assert sinyaller == ["dene"]

    main_mod._kancalari_birak()  # `serve`'ün kapanışı

    assert masaustu_kanca.ertelenen_gun_islerini_dene() is False
    assert masaustu_kanca.cikis_iste() is False
    assert sinyaller == ["dene"]


def test_sinyal_hatasi_kilit_acilisini_dusurmez(kanca_temiz: None) -> None:
    def patla() -> None:
        raise RuntimeError("kapı yok")

    masaustu_kanca.kaydet(ertelenenleri_dene=patla)
    app_password.lock()

    ac()

    assert OTURUM.acik_mi() is True


def _baska_is_parcacigi_alabilir(kilit: Any, sure: float = 0.5) -> bool:
    """Kilit başka bir iş parçacığınca `sure` içinde alınabiliyor mu? (bu iş parçacığı tutmuyor)"""
    sonuc: list[bool] = []

    def dene() -> None:
        alindi = kilit.acquire(timeout=sure)
        if alindi:
            kilit.release()
        sonuc.append(alindi)

    deneyen = threading.Thread(target=dene)
    deneyen.start()
    deneyen.join()
    return sonuc == [True]


@pytest.mark.parametrize("yol", ["parola", "kurtarma"])
def test_kilit_acilisi_kilitlerini_biraktiktan_sonra_sinyal_verir(
    kanca_temiz: None, yol: str
) -> None:
    """TK19 ve tasarım §4.4.3 sırasının son adımı: oturum açılır, kilitler bırakılır, SONRA
    kapıya "ertelenenleri şimdi dene" sinyali gider. Düşen açılış sinyal vermez."""
    gorulen: list[tuple[bool, bool, bool]] = []

    def sinyal() -> None:
        gorulen.append(
            (
                OTURUM.acik_mi(),
                _baska_is_parcacigi_alabilir(IZ_KIP_KILIDI),
                _baska_is_parcacigi_alabilir(app_password._state_lock),
            )
        )

    masaustu_kanca.kaydet(ertelenenleri_dene=sinyal)
    app_password.lock()

    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password="Yanlis-Parola-9!")
    assert gorulen == []

    if yol == "parola":
        ac()
    else:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_TANITICI, new_password=YENI_PAROLA
        )
    assert gorulen == [(True, True, True)]


def _bekle(kosul: Callable[[], bool], sure: float = 10.0) -> None:
    son = time.monotonic() + sure
    while not kosul() and time.monotonic() < son:
        time.sleep(0.02)
    assert kosul()


@pytest.mark.django_db(transaction=True)
def test_ilk_kilit_acilisinda_ertelenen_silme_kapida_kosar(
    kanca_temiz: None, tmp_path: Path
) -> None:
    """Uçtan uca (TK19): kilitliyken `od-gunluk`'un ilk geçişi silmeyi erteler (`GUN_ISI`);
    kilit açılışının sinyaliyle kapı işi saatlik takvimi beklemeden kendi iş parçacığında koşar,
    süresi dolan satır silinir, `KVKK_SILME` yazılır, gün damgalanır."""
    from desktop.gunluk import GunDegisimiKapisi

    eski = satir(yerel(2020, 1, 1))
    capa = kilitle()
    django_apps.get_app_config("okul").ready()
    kapi = GunDegisimiKapisi(damga_yolu=tmp_path / "gun-kapisi.json", monoton=lambda: 0.0)
    assert kapi.backend_islerini_ekle() == 1
    kapi.baslat()
    try:
        _bekle(lambda: AuditTrail.objects.filter(seq__gt=capa.seq, action="GUN_ISI").exists())
        assert AccessLog.objects.filter(pk=eski.pk).exists()
        assert erisim_gunlugu.SILME_ISI not in kapi.damgalar()

        masaustu_kanca.kaydet(ertelenenleri_dene=kapi.ertelenenleri_dene)
        ac()

        _bekle(lambda: AuditTrail.objects.filter(action="KVKK_SILME").exists())
        _bekle(lambda: erisim_gunlugu.SILME_ISI in kapi.damgalar())
    finally:
        kapi.durdur()
    assert not AccessLog.objects.filter(pk=eski.pk).exists()
    (silme,) = satirlar(action="KVKK_SILME")
    assert (silme.actor, silme.key_mode) == ("SISTEM", "ACIK")
    assert kapi.damgalar() == {erisim_gunlugu.SILME_ISI: timezone.localdate().isoformat()}
