"""Birlik kişileri ve veli listesinin dönem bağı (F1c'nin 4. adımı; tasarım §5.2.2, §8.4, §13 D30).

Kod kapısının kişi kolları burada sınanır (plan §2.4, F1c-4 "Bitti"):

* **Kör indeks kolu:** kişinin ad indeksi veli listesinin indeksiyle aynı yoldan iner; ad değişince
  yenilenir, ilgisiz alan yazılınca hesaplanmaz; anahtar bellekte değilse yazılmaz (fail-closed).
* **İzsiz yazım ve kişisel veri:** her yazım `degisiklik` satırıdır; kişi KVKK silme kümesindedir,
  satır değer taşımaz, ad içerik MAC'ine girmez. (Uçların tablo karşılaştırması ve uydurma veri
  araması `apps/okul/tests/test_izsiz_yazim.py`'dedir.)
* **Parola kapısı (409) ve kilit:** kişi yazan dört uç `RequiresAdminPassword` taşır (listesi
  `apps/okul/tests/test_kisi_yazan_uclar.py`); burada ayrıca sürülür. Kilitliyken servis yazmaz.
* **Rol bağlantısı:** M2'de program yöneticisi ve yönetim kurulu rolleri yazar, Denetleme Kurulu ve
  müdür okur; veli listesinden kopya yalnız program yöneticisinindir.

Kişi adları ve okul adı UYDURMADIR.
"""

from __future__ import annotations

import ast
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.oab.hatalar import KisiPasif, OlasiAyniKisi
from apps.oab.models import (
    OabPerson,
    OabTerm,
    PersonKind,
    PersonStatus,
    TermStatus,
    kisi_adi_kor_indeksi,
)
from apps.oab.services import donemler, kisiler
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import (
    AccountRole,
    AuditTrail,
    MemberKind,
    ParentRoster,
    Personnel,
    SchoolYear,
    parent_name_blind_index,
)
from apps.okul.services import imports as import_service
from apps.okul.services import persons
from apps.okul.services import setup as setup_service
from apps.okul.services.templates import PARENT_TEMPLATE_HEADERS
from apps.okul.tests.hesap_ortak import rol_hesabi
from apps.okul.tests.okul_karti_ortak import okul_karti
from conftest import TEST_DEK, TEST_IA, oturumu_ac_test
from shared import crypto

#: `backend/` kökü.
KOK = Path(__file__).resolve().parents[3]
UC = "/api/v1/oab/persons/"
UC_PERSONEL = "/api/v1/oab/persons/from-personnel/"
UC_VELI = "/api/v1/oab/persons/from-parent/"
GUN = date(2026, 10, 10)


def _istemci() -> APIClient:
    return APIClient()


def _kisi(**alanlar: Any) -> OabPerson:
    varsayilan: dict[str, Any] = {
        "kind": PersonKind.VELI,
        "first_name": "Uydurnur",
        "last_name": "Örnekkaya",
    }
    return kisiler.create_person(**{**varsayilan, **alanlar})


def _yil() -> SchoolYear:
    yil: SchoolYear = SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    return yil


def _donem() -> OabTerm:
    return donemler.create_term(name="2026-2027 birlik dönemi", school_year=_yil(), start_date=GUN)


def _veli_xlsx(satirlar: list[tuple[str, str]]) -> bytes:
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.append(list(PARENT_TEMPLATE_HEADERS))
    for satir in satirlar:
        sayfa.append(list(satir))
    tampon = BytesIO()
    kitap.save(tampon)
    return tampon.getvalue()


def _veli_aktar(satirlar: list[tuple[str, str]], ad: str = "veli-listesi.xlsx") -> None:
    import_service.commit_parents_file(file_bytes=_veli_xlsx(satirlar), file_name=ad)


def _rol_oturumu(rol: AccountRole) -> None:
    hesap = rol_hesabi(rol)
    oturumu_ac_test(str(hesap.id), tanitici=hesap.login_name, rol=rol.value)


def _izler(kisi: OabPerson) -> list[AuditTrail]:
    return list(
        AuditTrail.objects.filter(model="oab.OabPerson", object_id=str(kisi.pk)).order_by("seq")
    )


# ============================================================ model ve kör indeks


def test_tur_ve_durum_tasarimin_lafzidir() -> None:
    """Tasarım §5.2.2: `IDARECI`'nin görünen adı "İdareci"dir; kişi silinmez, `PASIF` olur."""
    assert PersonKind.IDARECI.label == "İdareci"
    assert tuple(PersonStatus.values) == ("AKTIF", "PASIF")
    alanlar = {alan.name for alan in OabPerson._meta.get_fields()}
    # K9 ve tasarım §5.2.2: T.C. kimlik no, telefon ve kullanıcı bağı yoktur.
    assert not {"tckn", "tckn_hash", "phone", "phone_hash", "linked_user_id"} & alanlar
    assert {f.name for f in crypto.encrypted_fields_of(OabPerson)} == {"first_name", "last_name"}


@pytest.mark.django_db
def test_kor_indeks_veli_listesinin_yoluyla_ayni_iner() -> None:
    """Adaydan kişi kaydına geçiş: aynı adın iki indeksi eşleşir (büyük-küçük, Türkçe harf, boşluk)."""
    kisi = _kisi(first_name="Işıl  Ayşe", last_name="ÇAĞLAR")
    assert kisi.name_index == parent_name_blind_index("IŞIL AYŞE çağlar")
    assert kisi.name_index == kisi_adi_kor_indeksi("ışıl ayşe", "Çağlar")
    assert "isil" not in kisi.name_index and len(kisi.name_index) == 64


@pytest.mark.django_db
def test_kor_indeks_ad_degisince_yenilenir_ilgisiz_alanda_hesaplanmaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kisi = _kisi()
    eski = kisi.name_index
    kisiler.update_person(kisi, last_name="Yenisoyad", ayni_kisi_degil=True)
    kisi.refresh_from_db()
    assert kisi.name_index == kisi_adi_kor_indeksi("Uydurnur", "Yenisoyad") != eski
    # İlgisiz alan yazılırken anahtar istenmez: indeks hesaplanmaz.
    cagri: list[tuple[object, ...]] = []

    def _sayan(*argumanlar: object) -> str:
        cagri.append(argumanlar)
        return "z"

    monkeypatch.setattr("apps.oab.models.kisi.kisi_adi_kor_indeksi", _sayan)
    kisiler.update_person(kisi, is_parent=False)
    assert cagri == []
    kisi.refresh_from_db()
    assert kisi.name_index == kisi_adi_kor_indeksi("Uydurnur", "Yenisoyad")


#: Soyadı bozulacak tablolar (sabit sorgular; tablo adı dışarıdan gelmez).
_SOYAD_BOZ: dict[str, str] = {
    "oab_oabperson": "UPDATE oab_oabperson SET last_name = %s WHERE id = %s",
    "okul_personnel": "UPDATE okul_personnel SET last_name = %s WHERE id = %s",
}


def _soyadi_boz(tablo: str, kimlik: int, ham: str = "UYDURMA HAM") -> None:
    """Program DIŞINDAN yazım taklidi: şifreli sütuna token olmayan değer (tasarım §13 D48)."""
    with connection.cursor() as cursor:
        cursor.execute(_SOYAD_BOZ[tablo], [ham, kimlik])


@pytest.mark.django_db
def test_bozuk_soyadli_kiside_ad_degisince_kor_indeks_bosalir() -> None:
    """D48 + D30: soyadı çözülemeyen kişide yalnız ad değişirse eski ad-soyadın indeksi KALMAZ.

    Kalsaydı kişi artık taşımadığı adla "olası aynı kişi" eşleşmesi üretirdi. Boş indeks hiçbir
    eşleşme üretmez; soyadın ham değeri aynen geri yazılır (bozukluk kayıtta görünür kalır).
    """
    kisi = _kisi(first_name="Uydurnur", last_name="Örnekkaya")
    _soyadi_boz("oab_oabperson", kisi.pk)
    okunan = OabPerson.objects.get(pk=kisi.pk)
    assert crypto.is_corrupt(okunan.last_name)
    kisiler.update_person(okunan, first_name="Yeniad")
    okunan.refresh_from_db()
    assert okunan.name_index == ""
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_name FROM oab_oabperson WHERE id = %s", [kisi.pk])
        assert cursor.fetchone() == ("UYDURMA HAM",)
    # Eski adla yeni kayıt "olası aynı kişi" sorusuna takılmaz.
    assert _kisi(first_name="Uydurnur", last_name="Örnekkaya").name_index != ""


@pytest.mark.django_db
def test_kilitliyken_kisi_yazilmaz() -> None:
    """Fail-closed (tasarım §5.3): anahtar bellekte değilse şifreli ad ve kör indeks yazılmaz."""
    crypto.unload_key()
    try:
        with pytest.raises(crypto.KeyMissingError):
            _kisi()
    finally:
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
    assert not OabPerson.objects.exists()


@pytest.mark.django_db
def test_kilitliyken_kisi_ucu_423(kilitli: Path) -> None:
    yanit = _istemci().post(
        UC, {"kind": "VELI", "first_name": "A", "last_name": "B"}, format="json"
    )
    assert yanit.status_code == 423
    assert yanit.json()["code"] == "locked"
    assert not OabPerson.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("yontem", "yol", "govde"),
    [
        ("post", UC, {"kind": "VELI", "first_name": "A", "last_name": "B"}),
        ("patch", f"{UC}1/", {"is_parent": True}),
        ("post", UC_PERSONEL, {"personnel": 1}),
        ("post", UC_VELI, {"full_name": "A B"}),
    ],
)
def test_parolasizken_kisi_yazan_oab_uclari_409(
    parolasiz: Path, yontem: str, yol: str, govde: dict[str, Any]
) -> None:
    """Plan §2.4: parola kurulmadan kişi yazan uç 409 `parola_gerekli`."""
    yanit = getattr(_istemci(), yontem)(yol, govde, format="json")
    assert yanit.status_code == 409
    assert yanit.json()["code"] == "parola_gerekli"


# ============================================================ izsiz yazım ve kişisel veri


@pytest.mark.django_db
def test_her_yazim_degersiz_iz_satiri_yazar_ad_mac_disindadir() -> None:
    """Tasarım §4.6.2, §5 O4: kişi KVKK silme kümesinde — satır değer taşımaz; ad, soyad ve kör
    indeks içerik MAC'ine girmez (program dışından ad değişse MAC değişmez); durum ayrı satırdır."""
    kisi = _kisi()
    kisiler.update_person(kisi, kind=PersonKind.OGRETMEN, is_parent=True)
    kisiler.update_person(kisi, status=PersonStatus.PASIF)
    izler = _izler(kisi)
    assert [satir.action for satir in izler] == ["OLUSTUR", "GUNCELLE", "DURUM"]
    assert all(satir.values == {} for satir in izler)
    assert izler[2].changed_fields == ["updated_at", "status"]
    assert denetim_izi.kaydi_dogrula(OabPerson, kisi.pk) is True
    once = denetim_izi.kayit_mac_hesapla(OabPerson, kisi.pk)
    OabPerson.objects.filter(pk=kisi.pk).update(first_name="Uydurgül", name_index="0" * 64)
    assert denetim_izi.kayit_mac_hesapla(OabPerson, kisi.pk) == once
    OabPerson.objects.filter(pk=kisi.pk).update(is_parent=False)
    assert denetim_izi.kayit_mac_hesapla(OabPerson, kisi.pk) != once


def _toplu_kisi_adi_yazimlari(kaynak: str) -> list[int]:
    """Kişi adını `save()`'i atlayarak yazan çağrılar: `update(first_name=…|last_name=…)`, adları
    anan `bulk_update` ve `OabPerson…bulk_create` (kör indeks dolmaz ya da eskir)."""
    satirlar: list[int] = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.Call) or not isinstance(dugum.func, ast.Attribute):
            continue
        adlar = {k.arg for k in dugum.keywords}
        metin = ast.unparse(dugum)
        if dugum.func.attr == "update" and adlar & {"first_name", "last_name"}:
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_update" and ("first_name" in metin or "last_name" in metin):
            satirlar.append(dugum.lineno)
        elif dugum.func.attr == "bulk_create" and "OabPerson" in ast.unparse(dugum.func.value):
            satirlar.append(dugum.lineno)
    return satirlar


def test_kisi_adi_toplu_yazilmaz() -> None:
    """Koruma (emsal `test_veli_listesi.test_veli_adi_toplu_yazilmaz`): uygulama kodunda (testler ve
    göçler hariç) kişi adını toplu yazan çağrı yoktur."""
    ihlaller = [
        f"{yol.relative_to(KOK)}:{satir}"
        for yol in KOK.rglob("*.py")
        if "tests" not in yol.parts and "migrations" not in yol.parts
        for satir in _toplu_kisi_adi_yazimlari(yol.read_text(encoding="utf-8"))
    ]
    assert ihlaller == []


def test_toplu_ad_denetcisi_ihlali_yakalar() -> None:
    kaynak = (
        '"""`update(first_name=…)` belge metnidir."""\n'
        "OabPerson.objects.filter(pk=1).update(first_name='X')\n"
        "OabPerson.objects.bulk_update(rows, ['last_name'])\n"
        "OabPerson.objects.filter(pk=1).update(status='PASIF')\n"
        "OabPerson.objects.bulk_create(rows)\n"
    )
    assert _toplu_kisi_adi_yazimlari(kaynak) == [2, 3, 5]


# ============================================================ elle kayıt, olası aynı kişi, durum


@pytest.mark.django_db
def test_elle_kayit_ucu_ve_veli_isareti_turden_gelir() -> None:
    yanit = _istemci().post(
        UC, {"kind": "VELI", "first_name": " Uydurnur ", "last_name": "Örnekkaya"}, format="json"
    )
    assert yanit.status_code == 201, yanit.json()
    veri = yanit.json()
    assert (veri["first_name"], veri["full_name"], veri["is_parent"]) == (
        "Uydurnur",
        "Uydurnur Örnekkaya",
        True,
    )
    assert veri["status"] == "AKTIF" and veri["bozuk_alanlar"] == []
    assert "name_index" not in veri and "tckn" not in veri and "phone" not in veri
    ogretmen = _kisi(kind=PersonKind.OGRETMEN, first_name="Deneme", last_name="Öğretmen")
    assert ogretmen.is_parent is False
    veli_ogretmen = _kisi(
        kind=PersonKind.OGRETMEN, first_name="Deneme", last_name="Veliöğretmen", is_parent=True
    )
    assert veli_ogretmen.is_parent is True


@pytest.mark.django_db
def test_liste_ucu_python_da_turk_alfabesiyle_siralar_ve_arar() -> None:
    for ad in ("ZEHRA", "ÇAĞLA", "CEM", "İLKAY", "IŞIK"):
        _kisi(first_name=ad, last_name="ÖRNEK")
    adlar = [k["first_name"] for k in _istemci().get(UC).json()]
    assert adlar == ["CEM", "ÇAĞLA", "IŞIK", "İLKAY", "ZEHRA"]
    assert [k["first_name"] for k in _istemci().get(UC, {"search": "cagla"}).json()] == ["ÇAĞLA"]
    kisiler.update_person(OabPerson.objects.order_by("pk")[0], status=PersonStatus.PASIF)
    assert len(_istemci().get(UC, {"only_active": "true"}).json()) == 4


@pytest.mark.django_db
def test_olasi_ayni_kisi_sorulur_onayla_yazilir() -> None:
    """Tasarım §13 D30: aynı kör indeksle ikinci kayıt "olası aynı kişi" sorusudur, engel değil."""
    ilk = _kisi(first_name="Ayşe", last_name="Yılmaz")
    with pytest.raises(OlasiAyniKisi):
        _kisi(first_name="AYŞE", last_name="YILMAZ")
    yanit = _istemci().post(
        UC, {"kind": "VELI", "first_name": "ayşe", "last_name": "yılmaz"}, format="json"
    )
    assert yanit.status_code == 409
    assert yanit.json()["code"] == "olasi_ayni_kisi"
    assert "Ayşe" not in yanit.json()["message"]
    yanit = _istemci().post(
        UC,
        {"kind": "VELI", "first_name": "ayşe", "last_name": "yılmaz", "ayni_kisi_degil": True},
        format="json",
    )
    assert yanit.status_code == 201
    assert OabPerson.objects.filter(name_index=ilk.name_index).count() == 2
    # Ad değişikliği de sorar; kaydın kendisiyle çakışmaz.
    baska = _kisi(first_name="Fatma", last_name="Kaya")
    with pytest.raises(OlasiAyniKisi):
        kisiler.update_person(baska, first_name="Ayşe", last_name="Yılmaz")
    kisiler.update_person(baska, first_name="FATMA", last_name="KAYA")
    baska.refresh_from_db()
    assert baska.first_name == "FATMA"


@pytest.mark.django_db
def test_tek_ad_alani_degisince_de_olasi_ayni_kisi_sorulur() -> None:
    """D30'un asıl işi soyadı değişimidir: değişmeyen alan kaydın kendi değeriyle karşılaştırılır."""
    _kisi(first_name="Ayşe", last_name="Yılmaz")
    fatma = _kisi(first_name="Fatma", last_name="Kaya")
    kisiler.update_person(fatma, first_name="Ayşe")  # Ayşe Kaya: çakışma yok.
    with pytest.raises(OlasiAyniKisi):
        kisiler.update_person(fatma, last_name="Yılmaz")
    zeynep = _kisi(first_name="Zeynep", last_name="Yılmaz")
    with pytest.raises(OlasiAyniKisi):
        kisiler.update_person(zeynep, first_name="Ayşe")
    yanit = _istemci().patch(f"{UC}{zeynep.pk}/", {"first_name": "Ayşe"}, format="json")
    assert yanit.status_code == 409 and yanit.json()["code"] == "olasi_ayni_kisi"


@pytest.mark.django_db
def test_adi_degismeyen_guncellemede_olasi_ayni_kisi_sorulmaz() -> None:
    """Onaylanmış adaş çiftinde ad dışındaki alanın güncellemesi soru doğurmaz (D30 yalnız ad)."""
    ilk = _kisi(first_name="Ayşe", last_name="Yılmaz")
    _kisi(first_name="Ayşe", last_name="Yılmaz", ayni_kisi_degil=True)
    for govde in (
        {"is_principal": True},
        {"external_yk_terms": 1},
        {"first_name": "Ayşe", "kind": "OGRETMEN"},
        {"status": "PASIF"},
    ):
        yanit = _istemci().patch(f"{UC}{ilk.pk}/", govde, format="json")
        assert yanit.status_code == 200, (govde, yanit.json())


@pytest.mark.django_db
def test_pasif_kisi_de_olasi_ayni_kisi_karsilastirmasina_girer() -> None:
    """Kişi silinmez, `PASIF` olur (O1): aynı kişinin yeniden kaydı da sorulur (D30)."""
    kisi = _kisi(first_name="Ayşe", last_name="Yılmaz")
    kisiler.update_person(kisi, status=PersonStatus.PASIF)
    with pytest.raises(OlasiAyniKisi):
        _kisi(first_name="Ayşe", last_name="Yılmaz")
    yanit = _istemci().post(
        UC, {"kind": "VELI", "first_name": "Ayşe", "last_name": "Yılmaz"}, format="json"
    )
    assert yanit.status_code == 409 and yanit.json()["code"] == "olasi_ayni_kisi"


@pytest.mark.django_db
def test_sapkali_harf_katlanir_olasi_ayni_kisi_sorulur() -> None:
    """Düzeltme işareti (â, î, û) adı ayırmaz: "Hâle" ile "Hale" aynı kör indeksi verir (D30)."""
    hale = _kisi(first_name="Hâle", last_name="Yılmaz")
    assert hale.name_index == kisi_adi_kor_indeksi("Hale", "Yılmaz")
    with pytest.raises(OlasiAyniKisi):
        _kisi(first_name="Hale", last_name="Yılmaz")
    # Ayrışık yazılmış şapka (a + U+0302) da aynı anahtarı verir.
    with pytest.raises(OlasiAyniKisi):
        _kisi(first_name="Hâle", last_name="YILMAZ")


@pytest.mark.django_db
def test_okul_muduru_isareti_kendiliginden_konur_izle_kaldirilir() -> None:
    """Plan F1c kararları: okul kartındaki müdür adıyla `name_key` eşleşirse kendiliğinden; yanlışsa
    güncellemeyle (izli) kaldırılır; eşleşmeyen kişi elle işaretlenir."""
    setup_service.update_school_config(fields=okul_karti(principal_name="Uydurma Müdüroğlu"))
    mudur = _kisi(kind=PersonKind.IDARECI, first_name="UYDURMA", last_name="MÜDÜROĞLU")
    assert mudur.is_principal is True
    baska = _kisi(kind=PersonKind.IDARECI, first_name="Deneme", last_name="İdareci")
    assert baska.is_principal is False
    yanit = _istemci().patch(f"{UC}{mudur.pk}/", {"is_principal": False}, format="json")
    assert yanit.status_code == 200 and yanit.json()["is_principal"] is False
    assert [s.action for s in _izler(mudur)] == ["OLUSTUR", "GUNCELLE"]
    assert _izler(mudur)[1].changed_fields == ["updated_at", "is_principal"]
    kisiler.update_person(baska, is_principal=True)
    baska.refresh_from_db()
    assert baska.is_principal is True


@pytest.mark.django_db
def test_okul_muduru_isareti_sapkali_harfte_de_konur() -> None:
    """Kart ile kayıt arasındaki şapka farkı (Kâzım/Kazım) eşleşmeyi bozmaz."""
    setup_service.update_school_config(fields=okul_karti(principal_name="Kâzım Uydurmaoğlu"))
    assert _kisi(kind=PersonKind.IDARECI, first_name="Kazım", last_name="Uydurmaoğlu").is_principal


@pytest.mark.django_db
def test_pasif_kisinin_alanlari_degismez_yeniden_etkinlesir() -> None:
    """Tasarım §5 O1, O2: kişi silinmez, `PASIF` olur; dönemsiz kaydın kilidi kendi durumudur."""
    kisi = _kisi()
    yanit = _istemci().patch(f"{UC}{kisi.pk}/", {"status": "PASIF"}, format="json")
    assert yanit.status_code == 200 and yanit.json()["status"] == "PASIF"
    with pytest.raises(KisiPasif):
        kisiler.update_person(kisi, first_name="Başka")
    yanit = _istemci().patch(f"{UC}{kisi.pk}/", {"last_name": "Başka"}, format="json")
    assert yanit.status_code == 409 and yanit.json()["code"] == "kisi_pasif"
    # Değişmeyen alan gönderilse de olur; yalnız durum değişir.
    kisiler.update_person(kisi, status=PersonStatus.AKTIF, first_name="Uydurnur")
    kisiler.update_person(kisi, last_name="Başka")
    # Silme ucu yoktur (O1): kuralsız yöntem rol kapısında kesilir.
    assert _istemci().delete(f"{UC}{kisi.pk}/").status_code == 403
    assert OabPerson.objects.filter(pk=kisi.pk).exists()


@pytest.mark.django_db
def test_sayac_beyani_bos_bilinmiyordur_eksi_olamaz() -> None:
    """Programdan önceki seçilme sayıları: beyan ya da "bilinmiyor" (boş; tasarım §5.2.2)."""
    kisi = _kisi()
    assert (kisi.external_yk_terms, kisi.external_dk_chair_terms) == (None, None)
    yanit = _istemci().patch(
        f"{UC}{kisi.pk}/", {"external_yk_terms": 2, "external_dk_chair_terms": 0}, format="json"
    )
    assert yanit.status_code == 200
    assert (yanit.json()["external_yk_terms"], yanit.json()["external_dk_chair_terms"]) == (2, 0)
    yanit = _istemci().patch(f"{UC}{kisi.pk}/", {"external_yk_terms": -1}, format="json")
    assert yanit.status_code == 400
    yanit = _istemci().patch(f"{UC}{kisi.pk}/", {"external_yk_terms": None}, format="json")
    assert yanit.status_code == 200 and yanit.json()["external_yk_terms"] is None


# ============================================================ personelden kopya


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("gorev", "tur"),
    [
        (MemberKind.OGRETMEN, PersonKind.OGRETMEN),
        (MemberKind.YONETICI, PersonKind.IDARECI),
        (MemberKind.DIGER, PersonKind.DIGER),
    ],
)
def test_personelden_kopya_gorev_turunu_eslar(gorev: str, tur: str) -> None:
    personel = persons.create_personnel(
        first_name="Uydurnur", last_name="Örnekkaya", member_kind=gorev
    )
    yanit = _istemci().post(UC_PERSONEL, {"personnel": personel.pk}, format="json")
    assert yanit.status_code == 201, yanit.json()
    kisi = OabPerson.objects.get(pk=yanit.json()["id"])
    assert (kisi.kind, kisi.personnel_id, kisi.is_parent) == (tur, personel.pk, False)
    assert (kisi.first_name, kisi.last_name) == ("Uydurnur", "Örnekkaya")
    # Bir personelin tek birlik kişi kaydı olur.
    yanit = _istemci().post(UC_PERSONEL, {"personnel": personel.pk}, format="json")
    assert yanit.status_code == 400
    assert yanit.json()["message"] == kisiler.PERSONEL_ZATEN_BAGLI


@pytest.mark.django_db
def test_birlik_kisisine_bagli_personel_silinmez_birlestirmede_bag_tasinir() -> None:
    """Tasarım §5.4: bağı olan personel silinmez (adı birlik kişisinde kalır); "olası aynı kişi"
    birleştirmesinde bağ hedefe taşınır (izli), kaynak silinir."""
    eski = persons.create_personnel(first_name="Uydurnur", last_name="Eskisoyad")
    kisi = kisiler.copy_from_personnel(eski)
    with pytest.raises(ValidationError) as hata:
        persons.delete_personnel(eski)
    assert hata.value.messages == [persons.MEMBER_DELETE_MESSAGE]
    yeni = persons.create_personnel(first_name="Uydurnur", last_name="Yenisoyad")
    persons.merge_personnel(eski, yeni)
    kisi.refresh_from_db()
    assert kisi.personnel_id == yeni.pk
    assert [s.action for s in _izler(kisi)] == ["OLUSTUR", "GUNCELLE"]
    assert _izler(kisi)[1].changed_fields == ["updated_at", "personnel"]
    assert denetim_izi.kaydi_dogrula(OabPerson, kisi.pk) is True


@pytest.mark.django_db
def test_bozuk_adli_personelden_kopya_yapilmaz() -> None:
    """D48: çözülemeyen ad boş metin gibi kopyalanmaz (`CorruptField`'ın `str()`'i boş dizedir)."""
    personel = persons.create_personnel(first_name="Uydurnur", last_name="Örnekkaya")
    _soyadi_boz("okul_personnel", personel.pk)
    okunan = Personnel.objects.get(pk=personel.pk)
    assert crypto.is_corrupt(okunan.last_name)
    with pytest.raises(ValueError, match="okunamadı") as hata:
        kisiler.copy_from_personnel(okunan)
    assert str(hata.value) == kisiler.PERSONEL_ADI_OKUNAMADI
    assert not OabPerson.objects.exists()


def test_kancalar_kayitli() -> None:
    """`AppConfig.ready`: bağ denetimi, birleştirme kancası ve veli listesinin dönem sağlayıcısı."""
    assert kisiler.personnel_linked in persons._membership_checks
    assert kisiler.personnel_merged in persons._merge_hooks
    assert donemler.acik_donem_kimligi in import_service._roster_term_providers


# ============================================================ veli listesinden kopya


@pytest.mark.django_db
def test_veli_listesinden_kopya_adi_ayristirir_ve_velidir() -> None:
    _veli_aktar([("AYŞE NUR YILMAZ", "9-A"), ("TEKAD", "9-B")])
    yanit = _istemci().post(UC_VELI, {"full_name": "ayşe nur yılmaz"}, format="json")
    assert yanit.status_code == 201, yanit.json()
    veri = yanit.json()
    assert (veri["first_name"], veri["last_name"], veri["kind"], veri["is_parent"]) == (
        "AYŞE NUR",
        "YILMAZ",
        "VELI",
        True,
    )
    # İkinci kopya olası aynı kişidir.
    assert (
        _istemci().post(UC_VELI, {"full_name": "AYŞE NUR YILMAZ"}, format="json").json()["code"]
        == "olasi_ayni_kisi"
    )
    yok = _istemci().post(UC_VELI, {"full_name": "Olmayan Veli"}, format="json")
    assert yok.status_code == 400 and yok.json()["message"] == kisiler.VELI_LISTESINDE_YOK
    tek = _istemci().post(UC_VELI, {"full_name": "tekad"}, format="json")
    assert tek.status_code == 400 and tek.json()["message"] == kisiler.VELI_ADI_AYRISTIRILAMADI


@pytest.mark.django_db
def test_veli_listesinden_kopya_sapkasiz_yazimla_bulunur() -> None:
    """Listede "HÂLE" yazan veli, kullanıcı "Hale" yazınca da bulunur; satırın adı kopyalanır."""
    _veli_aktar([("HÂLE UYDURMAOĞLU", "9-A")])
    kisi = kisiler.copy_from_parent("Hale Uydurmaoğlu")
    assert (kisi.first_name, kisi.last_name) == ("HÂLE", "UYDURMAOĞLU")


def test_veli_adi_ayristirma() -> None:
    assert kisiler.veli_adini_ayristir("  Ali   Can  Demir ") == ("Ali Can", "Demir")
    for bozuk in ("Tek", "", None):
        with pytest.raises(ValueError):
            kisiler.veli_adini_ayristir(bozuk)
    with pytest.raises(ValueError, match="sığmıyor"):
        kisiler.veli_adini_ayristir("A" * 101 + " Soyad")


# ============================================================ rol bağlantısı (M2)


@pytest.mark.django_db
@pytest.mark.parametrize("rol", sorted(rol_izinleri.YK_ROLLERI))
def test_yonetim_kurulu_rolleri_kisi_yazar_veli_listesinden_kopyalayamaz(rol: str) -> None:
    _veli_aktar([("UYDURMA VELİ", "9-A")])
    _rol_oturumu(AccountRole(rol))
    yanit = _istemci().post(
        UC, {"kind": "KURSIYER", "first_name": "A", "last_name": "B"}, format="json"
    )
    assert yanit.status_code == 201, yanit.json()
    yanit = _istemci().patch(f"{UC}{yanit.json()['id']}/", {"adult_declared": True}, format="json")
    assert yanit.status_code == 200
    yanit = _istemci().post(UC_VELI, {"full_name": "Uydurma Veli"}, format="json")
    assert yanit.status_code == 403 and yanit.json()["code"] == "rol_yetkisiz"


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [AccountRole.DENETLEME_KURULU, AccountRole.MUDUR])
def test_denetleme_kurulu_ve_mudur_kisileri_okur_yazamaz(rol: AccountRole) -> None:
    kisi = _kisi()
    _rol_oturumu(rol)
    assert _istemci().get(UC).status_code == 200
    assert _istemci().get(f"{UC}{kisi.pk}/").status_code == 200
    yanit = _istemci().post(
        UC, {"kind": "VELI", "first_name": "A", "last_name": "B"}, format="json"
    )
    assert yanit.status_code == 403
    assert (
        _istemci().patch(f"{UC}{kisi.pk}/", {"is_parent": False}, format="json").status_code == 403
    )


def test_m2_yonetim_kurulu_hucresi_bekleyende_degil() -> None:
    """Plan F1c-4: `BEKLEYEN_HUCRELER`'in M2 satırı çıktı; F1c adlı bekleyen hücre kalmadı."""
    assert not any(satir is rol_izinleri.Satir.M2 for satir, _ in rol_izinleri.BEKLEYEN_HUCRELER)
    assert "F1c" not in set(rol_izinleri.BEKLEYEN_HUCRELER.values())
    for rol in rol_izinleri.YK_ROLLERI:
        assert rol_izinleri.Satir.M2 in rol_izinleri.etkin_hucreler(rol)


# ============================================================ veli listesinin dönem bağı


@pytest.mark.django_db
def test_donemsiz_veli_satirlari_ilk_donem_acilinca_baglanir() -> None:
    """Plan F1c-4: açık dönem yokken aktarılan satırlar boş dönemlidir; ilk dönem açılınca o döneme
    bağlanır, izi kişisiz tek `DURUM` olayıdır (ad, sınıf, kimlik ve sayı yok)."""
    _veli_aktar([("UYDURMA VELİ", "9-A"), ("DENEME VELİ", "10-B")])
    assert set(ParentRoster.objects.values_list("term", flat=True)) == {None}
    donem = _donem()
    assert set(ParentRoster.objects.values_list("term", flat=True)) == {donem.pk}
    olay = AuditTrail.objects.get(model="okul.ParentRoster")
    assert (olay.action, olay.object_id, olay.changed_fields, olay.values) == (
        "DURUM",
        "",
        ["term"],
        {},
    )
    assert olay.term_id == donem.pk and olay.record_mac == ""
    # Bağlanacak satır yoksa olay yazılmaz.
    assert donemler._veli_listesini_bagla(donem) == 0
    assert AuditTrail.objects.filter(model="okul.ParentRoster").count() == 1


@pytest.mark.django_db
def test_onceki_parti_donem_bazindadir() -> None:
    """Tasarım §8.4 (1): dosyadaki sınıflar DÖNEM İÇİNDEKİ önceki partinin aynı sınıflarının yerini
    alır; başka dönemin satırlarına dokunulmaz, "dokunulmayan" sayıları da dönem içidir. Veli
    listesinden kopya yalnız açık dönemin satırlarında arar."""
    ilk = _donem()
    _veli_aktar([("ESKİ VELİ", "9-A"), ("ESKİ İKİ", "10-B")])
    assert set(ParentRoster.objects.values_list("term", flat=True)) == {ilk.pk}
    # Sentetik dönem geçişi (gerçek kapanış F4, ikinci dönem F2'nin yolu).
    OabTerm.objects.filter(pk=ilk.pk).update(status=TermStatus.KAPANDI, end_date=date(2027, 10, 1))
    ikinci = OabTerm.objects.create(
        name="2027-2028 birlik dönemi",
        school_year=ilk.school_year,
        start_date=date(2027, 10, 2),
        rule_package=ilk.rule_package,
        status=TermStatus.ACIK,
    )
    # Açık dönemden SONRA açılmış, açık olmayan dönem (en yüksek kimlik) aktarımın dönemi değildir.
    OabTerm.objects.create(
        name="İptal edilen uydurma dönem",
        school_year=ilk.school_year,
        rule_package=ilk.rule_package,
        status=TermStatus.IPTAL,
    )
    assert donemler.acik_donem_kimligi() == ikinci.pk
    rapor = import_service.commit_parents_file(
        file_bytes=_veli_xlsx([("YENİ VELİ", "9-A")]), file_name="ikinci.xlsx"
    )
    assert (rapor.replaced_rows, rapor.kept_rows, rapor.kept_class_count) == (0, 0, 0)
    assert ParentRoster.objects.filter(term=ilk).count() == 2
    assert ParentRoster.objects.filter(term=ikinci).count() == 1
    rapor = import_service.commit_parents_file(
        file_bytes=_veli_xlsx([("SON VELİ", "9-A")]), file_name="ucuncu.xlsx"
    )
    assert rapor.replaced_rows == 1
    assert ParentRoster.objects.filter(term=ilk).count() == 2
    # Kopya yalnız açık dönemin satırlarında arar.
    with pytest.raises(ValueError, match="bulunamadı"):
        kisiler.copy_from_parent("Eski Veli")
    assert kisiler.copy_from_parent("Son Veli").last_name == "VELİ"
