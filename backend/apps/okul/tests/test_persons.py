"""Personel ELLE kayıt işlemleri, ayrılış yolu ve unutma kancası — servis + uç.

İçe aktarma yolu `test_imports.py` ve mutabakat testlerinde sınanır; burada
sicil ekranının elle ekleme/düzeltme/ayrılış/silme yolu sabitlenir:

- Güncelleme YALNIZ değişen alanı yazar ve `updated_at`'i elle damgalar
  (`save(update_fields=…)` `auto_now` alanını kendiliğinden yazmaz).
- AYRILIŞ KAYDI SİLMEZ (aile iskeletinden; tasarım §5.1): ayrılış
  `is_active=False` + `left_at` yazar, havuzdan çıkarır, kancaları koşar;
  kayıt bağdan ve yükümlülükten bağımsız olarak KALIR (ailenin eski "bağsız ve
  yükümlülüksüz → katı sil" dalı aile iskeletinde kalkmıştı; bu testler o davranışı
  tersine sabitler).
- Kullanıcı silmesi ("Sil" düğmesi) kuralı korunur: açık yükümlülükte gerekçeyle
  reddedilir, birlik kayıtlarına bağlı kişide ayrılış yoluna yönlendirir, aksi
  hâlde katı siler. Bugün kayıtlı denetim yoktur (OAB modelleri F1c'den itibaren
  kaydeder): yollar SAHTE kayıtlı denetimlerle sınanır.

Öğrenci sicili F1b 5. adımda söküldü (tasarım §5.1 ALMA); öğrenciyle sınanan ayrılış, kanca ve
silme yolları personele taşındı, öğrenci uçlarının yokluğu ayrıca sınanır.

Tüm adlar uydurmadır (KVKK).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul.models import MemberKind, Personnel
from apps.okul.services import persons

pytestmark = pytest.mark.django_db

PERSONEL_URL = "/api/v1/personnel/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def bos_kayit_defterleri(monkeypatch: pytest.MonkeyPatch) -> None:
    """Her test boş kayıt defterleriyle başlar (uygulamaların kayıtları testleri etkilemesin)."""
    for ad in (
        "_obligation_checks",
        "_membership_checks",
        "_leave_hooks",
        "_merge_hooks",
        "_deletion_blocks",
    ):
        monkeypatch.setattr(persons, ad, [])


@pytest.fixture
def uye_olmus(monkeypatch: pytest.MonkeyPatch) -> Iterator[set[tuple[str, int]]]:
    """Sahte bağ denetimi: kümeye eklenen (model, pk) birlik kayıtlarına bağlı sayılır."""
    uyeler: set[tuple[str, int]] = set()
    persons.register_membership_check(lambda kisi: (type(kisi).__name__, kisi.pk) in uyeler)
    yield uyeler


@pytest.fixture
def acik_yukumluluk(monkeypatch: pytest.MonkeyPatch) -> Iterator[set[tuple[str, int]]]:
    """Sahte yükümlülük denetimi: kümedekilerin açık yükümlülüğü vardır (gerekçe adsız)."""
    borclular: set[tuple[str, int]] = set()

    def _denetim(kisi: persons.Person) -> list[str]:
        return ["Kapanmamış kayıt var."] if (type(kisi).__name__, kisi.pk) in borclular else []

    persons.register_obligation_check(_denetim)
    yield borclular


def _personel(**alanlar: Any) -> Personnel:
    varsayilan: dict[str, Any] = {"first_name": "DENEME", "last_name": "ÖĞRETMEN"}
    varsayilan.update(alanlar)
    return persons.create_personnel(**varsayilan)


def _anahtar(kisi: persons.Person) -> tuple[str, int]:
    return (type(kisi).__name__, kisi.pk)


def _eskit(kayit: Personnel) -> Any:
    """`updated_at`'i geçmişe çeker → sonraki yazmanın damgayı yenilediği ölçülebilir."""
    eski = timezone.now() - timedelta(days=3)
    type(kayit).objects.filter(pk=kayit.pk).update(updated_at=eski)
    kayit.refresh_from_db()
    return eski


def _sonuclar(yanit: Any) -> list[dict[str, Any]]:
    veri = yanit.json()
    return list(veri["results"]) if isinstance(veri, dict) else list(veri)


# ---------------------------------------------------------------------------
# Servis — personel
# ---------------------------------------------------------------------------


def test_personel_olusturulur_varsayilan_aktif_ve_ogretmendir() -> None:
    kisi = _personel()

    kisi.refresh_from_db()
    assert kisi.full_name == "DENEME ÖĞRETMEN"
    assert kisi.is_active is True
    assert kisi.member_kind == MemberKind.TEACHER
    assert kisi.left_at is None


def test_personel_guncelleme_degisen_alani_yazar_ve_damgayi_yeniler() -> None:
    kisi = _personel()
    eski = _eskit(kisi)

    persons.update_personnel(kisi, member_kind=MemberKind.STAFF)

    kisi.refresh_from_db()
    assert kisi.member_kind == MemberKind.STAFF
    assert kisi.updated_at > eski


def test_personel_guncelleme_degisiklik_yoksa_yazmaz() -> None:
    kisi = _personel()
    eski = _eskit(kisi)

    persons.update_personnel(kisi, member_kind=MemberKind.TEACHER, first_name="DENEME")

    kisi.refresh_from_db()
    assert kisi.updated_at == eski


def test_personel_guncelleme_dokunulmayan_alani_ezmez() -> None:
    """Bayat kopya üzerinden üye türü düzeltmek, ayrılışı geri almaz."""
    kisi = _personel()
    Personnel.objects.filter(pk=kisi.pk).update(is_active=False)

    persons.update_personnel(kisi, member_kind=MemberKind.STAFF)  # `kisi` bellekte hâlâ aktif

    kisi.refresh_from_db()
    assert (kisi.member_kind, kisi.is_active) == (MemberKind.STAFF, False)


# ---------------------------------------------------------------------------
# Ayrılış yolu (tasarım §5.1) — kayıt SİLİNMEZ
# ---------------------------------------------------------------------------


def test_ayrilis_hic_uye_olmamis_ve_yukumluluksuz_personeli_silmez() -> None:
    kisi = _personel()

    persons.leave_personnel(kisi)

    kisi.refresh_from_db()
    assert (kisi.is_active, kisi.left_at, kisi.deleted_at) == (False, timezone.localdate(), None)
    assert Personnel.all_objects.count() == 1


def test_ayrilis_uye_olmus_personelde_de_kaydi_saklar(
    uye_olmus: set[tuple[str, int]],
) -> None:
    kisi = _personel()
    uye_olmus.add(_anahtar(kisi))

    persons.leave_personnel(kisi)

    kisi.refresh_from_db()
    assert kisi.is_active is False
    assert kisi.left_at == timezone.localdate()
    assert kisi.deleted_at is None


def test_ayrilis_acik_yukumlulugu_olan_personelde_de_kaydi_saklar(
    acik_yukumluluk: set[tuple[str, int]],
) -> None:
    kisi = _personel()
    acik_yukumluluk.add(_anahtar(kisi))

    persons.leave_personnel(kisi)
    kisi.refresh_from_db()
    assert (kisi.is_active, kisi.left_at) == (False, timezone.localdate())


def test_ayrilis_havuzdaki_kisiyi_havuzdan_cikarir() -> None:
    """Havuzdaki kişi elle "Ayrıldı olarak işaretle"nince havuz alanları aynı kayıtta temizlenir."""
    kisi = _personel()
    persons.add_to_leave_pool(kisi, run=None)

    persons.leave_personnel(kisi)

    kisi.refresh_from_db()
    assert (kisi.leave_candidate_since, kisi.leave_candidate_run_id) == (None, None)


def test_ayrilis_kancasi_kisiyle_ve_left_olarak_cagrilir(
    uye_olmus: set[tuple[str, int]],
) -> None:
    """Kanca kişiyi alır; kayıt o anda ayrılmıştır."""
    gorulen: list[tuple[str, int, bool]] = []

    def _kanca(kisi: persons.Person) -> None:
        assert isinstance(kisi, Personnel)
        gorulen.append((type(kisi).__name__, kisi.pk, kisi.is_active))

    persons.register_leave_hook(_kanca)
    persons.register_leave_hook(_kanca)  # idempotent kayıt
    kisi = _personel()
    pk = kisi.pk

    persons.leave_personnel(kisi)

    assert gorulen == [("Personnel", pk, False)]


def test_ayrilis_kancasi_hata_verirse_ayrilis_geri_sarilir() -> None:
    """Kanca AYNI işlemde koşar: kanca başarısızsa kişi ayrılmış sayılmaz."""

    def _patla(_kisi: persons.Person) -> None:
        raise RuntimeError("kanca başarısız")

    persons.register_leave_hook(_patla)
    kisi = _personel()

    with pytest.raises(RuntimeError):
        persons.leave_personnel(kisi)

    kisi.refresh_from_db()
    assert (kisi.is_active, kisi.left_at) == (True, None)


def test_zaten_ayrilmis_kisi_yeniden_ayrilamaz() -> None:
    kisi = _personel()
    persons.leave_personnel(kisi)

    with pytest.raises(ValidationError, match="zaten ayrıldı"):
        persons.leave_personnel(kisi)


# ---------------------------------------------------------------------------
# Kullanıcı silmesi ("Sil" düğmesi — bilinçli eylem; ayrılış havuzu bunu değiştirmez)
# ---------------------------------------------------------------------------


def test_silme_hic_uye_olmamis_kisiyi_kati_siler() -> None:
    kisi = _personel()
    pk = kisi.pk

    persons.delete_personnel(kisi)

    assert not Personnel.all_objects.filter(pk=pk).exists()
    assert Personnel.all_objects.count() == 0


def test_ayrilmis_ve_hic_uye_olmamis_kisi_elle_silinebilir() -> None:
    """Ayrılış kaydı saklar; yanlış girilmiş kaydı kullanıcı yine "Sil" ile katı siler."""
    kisi = _personel()
    persons.leave_personnel(kisi)

    persons.delete_personnel(kisi)

    assert not Personnel.all_objects.filter(pk=kisi.pk).exists()


def test_silme_acik_yukumlulukte_gerekceyle_reddedilir(
    acik_yukumluluk: set[tuple[str, int]],
) -> None:
    kisi = _personel()
    acik_yukumluluk.add(_anahtar(kisi))

    with pytest.raises(ValidationError) as hata:
        persons.delete_personnel(kisi)

    assert hata.value.messages == ["Kayıt silinemez: Kapanmamış kayıt var."]
    assert Personnel.objects.filter(pk=kisi.pk).exists()


def test_silme_uye_olmus_kisiyi_ayrilis_yoluna_yonlendirir(
    uye_olmus: set[tuple[str, int]],
) -> None:
    kisi = _personel()
    uye_olmus.add(_anahtar(kisi))

    with pytest.raises(ValidationError) as hata:
        persons.delete_personnel(kisi)

    assert hata.value.messages == [persons.MEMBER_DELETE_MESSAGE]
    assert persons.MEMBER_DELETE_MESSAGE.startswith("Bu kişi birlik kayıtlarına bağlı;")
    assert "Ayrıldı olarak işaretle" in persons.MEMBER_DELETE_MESSAGE
    assert Personnel.objects.filter(pk=kisi.pk).exists()


# ---------------------------------------------------------------------------
# Birleştirme (olası aynı kişi)
# ---------------------------------------------------------------------------


def test_birlestirme_kancalari_kaynak_hedef_sirasiyla_cagrilir_kaynak_silinir() -> None:
    tasinan: list[tuple[int, int]] = []
    persons.register_merge_hook(lambda kaynak, hedef: tasinan.append((kaynak.pk, hedef.pk)))
    eski = _personel(first_name="AYŞE", last_name="ESKİSOYAD")
    yeni = _personel(first_name="AYŞE", last_name="YENİSOYAD")

    eski_pk = eski.pk

    sonuc = persons.merge_personnel(eski, yeni)

    assert sonuc.pk == yeni.pk
    assert tasinan == [(eski_pk, yeni.pk)]
    assert eski_pk is not None
    assert not Personnel.all_objects.filter(pk=eski_pk).exists()
    assert Personnel.objects.filter(pk=yeni.pk).exists()


def test_kisi_kendisiyle_birlestirilemez() -> None:
    kisi = _personel()

    with pytest.raises(ValidationError, match="kendisiyle"):
        persons.merge_personnel(kisi, kisi)


def test_birlestirme_kancasi_hata_verirse_kaynak_silinmez() -> None:
    def _patla(_kaynak: Personnel, _hedef: Personnel) -> None:
        raise RuntimeError("taşıma başarısız")

    persons.register_merge_hook(_patla)
    eski, yeni = _personel(), _personel(first_name="BAŞKA")

    with pytest.raises(RuntimeError):
        persons.merge_personnel(eski, yeni)

    assert Personnel.objects.filter(pk=eski.pk).exists()


# ---------------------------------------------------------------------------
# Uç — personel
# ---------------------------------------------------------------------------


def test_api_silme_acik_yukumlulukte_400_ve_gerekce(
    client: APIClient, acik_yukumluluk: set[tuple[str, int]]
) -> None:
    kisi = _personel()
    acik_yukumluluk.add(_anahtar(kisi))

    yanit = client.delete(f"{PERSONEL_URL}{kisi.pk}/")

    assert yanit.status_code == 400
    assert yanit.json()["message"] == "Kayıt silinemez: Kapanmamış kayıt var."
    assert Personnel.objects.filter(pk=kisi.pk).exists()


def test_api_ayrilis_ucu_kaydi_saklar_ve_doner(client: APIClient) -> None:
    """Ayrılış ucu hiçbir durumda silmez (üye olmamış kişide de); ayrılmış kaydı döner."""
    kisi = _personel()
    persons.add_to_leave_pool(kisi, run=None)

    ayril = client.post(f"{PERSONEL_URL}{kisi.pk}/leave/")
    assert ayril.status_code == 200
    assert ayril.json()["id"] == kisi.pk
    assert ayril.json()["is_active"] is False
    assert ayril.json()["left_at"] == timezone.localdate().isoformat()
    assert "deleted" not in ayril.json()
    kisi.refresh_from_db()
    assert kisi.leave_candidate_since is None
    assert Personnel.all_objects.filter(pk=kisi.pk, deleted_at__isnull=True).exists()

    tekrar = client.post(f"{PERSONEL_URL}{kisi.pk}/leave/")
    assert tekrar.status_code == 400
    assert tekrar.json()["message"] == persons.ALREADY_LEFT_MESSAGE


def test_api_ogrenci_uclari_yoktur(client: APIClient) -> None:
    """Öğrenci sicili ve şube kataloğu F1b 5. adımda söküldü (tasarım §5.1 ALMA, T5).

    Ad tablosunda yoklar; yolları açık oturumda rol kapısında kesilir (adsız uç her role kapalı).
    """
    for ad in (
        "student-list",
        "student-detail",
        "student-leave",
        "class-section-list",
        "class-section-detail",
        "grade-levels",
    ):
        with pytest.raises(NoReverseMatch):
            reverse(ad, kwargs={"pk": 1} if ad.endswith(("detail", "leave")) else None)
    for yol in ("/api/v1/students/", "/api/v1/class-sections/", "/api/v1/grade-levels/"):
        assert client.get(yol).status_code == 403, yol


def test_api_personel_ekleme_duzeltme_ayrilis_ve_silme(
    client: APIClient, uye_olmus: set[tuple[str, int]]
) -> None:
    ekle = client.post(
        PERSONEL_URL,
        {"first_name": "DENEME", "last_name": "ÖĞRETMEN", "member_kind": "STAFF"},
        format="json",
    )
    assert ekle.status_code == 201
    assert ekle.json()["full_name"] == "DENEME ÖĞRETMEN"
    assert ekle.json()["is_active"] is True
    assert ekle.json()["member_kind"] == "STAFF"
    kisi_id = ekle.json()["id"]
    uye_olmus.add(("Personnel", kisi_id))

    # `is_active` gövdeyle değişmez (salt okunur); ayrılış `leave/` ucundan.
    yok_sayilan = client.patch(f"{PERSONEL_URL}{kisi_id}/", {"is_active": False}, format="json")
    assert yok_sayilan.status_code == 200 and yok_sayilan.json()["is_active"] is True

    ayril = client.post(f"{PERSONEL_URL}{kisi_id}/leave/")
    assert ayril.status_code == 200
    assert ayril.json()["id"] == kisi_id
    assert ayril.json()["is_active"] is False
    assert ayril.json()["left_at"] == timezone.localdate().isoformat()
    # Sicil ekranı ayrılanı gösterir, seçiciler (only_active) göstermez.
    assert [p["id"] for p in _sonuclar(client.get(PERSONEL_URL))] == [kisi_id]
    assert _sonuclar(client.get(PERSONEL_URL, {"only_active": "true"})) == []

    # Birlik kayıtlarına bağlı kişi silinemez: ayrılış yoluna yönlendirilir.
    sil = client.delete(f"{PERSONEL_URL}{kisi_id}/")
    assert sil.status_code == 400
    assert sil.json()["message"] == persons.MEMBER_DELETE_MESSAGE


def test_api_personel_ad_soyad_zorunludur(client: APIClient) -> None:
    yanit = client.post(PERSONEL_URL, {"member_kind": "TEACHER"}, format="json")

    assert yanit.status_code == 400
    assert yanit.json()["code"] == "validation_error"
    assert set(yanit.json()["fields"]) == {"first_name", "last_name"}


def test_api_personel_uye_turu_dogrulanir_unvan_brans_yok_sayilir(client: APIClient) -> None:
    """Unvan/branş gövdede gelse bile hiçbir yere yazılmaz (alan yok); tür iki değerlidir."""
    gecersiz = client.post(
        PERSONEL_URL,
        {"first_name": "A", "last_name": "B", "member_kind": "MUDUR"},
        format="json",
    )
    assert gecersiz.status_code == 400
    assert "üye türü" in str(gecersiz.json()["fields"]["member_kind"])

    yanit = client.post(
        PERSONEL_URL,
        {"first_name": "A", "last_name": "B", "title": "Müdür", "branch": "Matematik"},
        format="json",
    )
    assert yanit.status_code == 201
    assert "title" not in yanit.json() and "branch" not in yanit.json()
    assert yanit.json()["member_kind"] == "TEACHER"


def test_api_personel_aramasi_yalniz_adda_turkce_katlar(client: APIClient) -> None:
    _personel(first_name="ÇAĞLA", last_name="ÖRNEK")
    _personel(first_name="DENEME", last_name="ÖĞRETMEN")

    def adlar(aranan: str) -> list[str]:
        return [p["first_name"] for p in _sonuclar(client.get(PERSONEL_URL, {"search": aranan}))]

    assert adlar("cagla") == ["ÇAĞLA"]
    assert adlar("ogretmen") == ["DENEME"]
    assert adlar("olmayan") == []


def test_api_personel_birlestirme_ucu(client: APIClient) -> None:
    eski = _personel(first_name="AYŞE", last_name="ESKİSOYAD")
    yeni = _personel(first_name="AYŞE", last_name="YENİSOYAD")

    yanit = client.post(f"{PERSONEL_URL}{eski.pk}/merge/", {"into_id": yeni.pk}, format="json")

    assert yanit.status_code == 200
    assert yanit.json()["id"] == yeni.pk
    assert not Personnel.all_objects.filter(pk=eski.pk).exists()


def test_api_personel_birlestirme_hatalari(client: APIClient) -> None:
    kisi = _personel()

    kendisi = client.post(f"{PERSONEL_URL}{kisi.pk}/merge/", {"into_id": kisi.pk}, format="json")
    assert kendisi.status_code == 400
    assert kendisi.json()["message"] == persons.SELF_MERGE_MESSAGE

    olmayan = client.post(f"{PERSONEL_URL}{kisi.pk}/merge/", {"into_id": 99999}, format="json")
    assert olmayan.status_code == 404

    govdesiz = client.post(f"{PERSONEL_URL}{kisi.pk}/merge/", {}, format="json")
    assert govdesiz.status_code == 400
    assert "hedef" in str(govdesiz.json()["fields"]["into_id"])
    assert Personnel.objects.filter(pk=kisi.pk).exists()


def test_api_personel_listesi_ad_sirasiyla(client: APIClient) -> None:
    for ad in ("ZEHRA", "ÇAĞLA", "CEM"):
        _personel(first_name=ad)

    assert [p["first_name"] for p in _sonuclar(client.get(PERSONEL_URL))] == [
        "CEM",
        "ÇAĞLA",
        "ZEHRA",
    ]
