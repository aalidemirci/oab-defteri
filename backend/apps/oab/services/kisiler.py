"""Birlik kişileri (tasarım §5.2.2 `OabPerson`, §13 D30; §12.A `create_person`, `update_person`
UYARLA; plan F1c-4).

Üç yoldan kişi kaydı açılır, üçü de `create_person`'dan geçer:

* **Elle** (Kişiler → Birlik Kişileri; ekran F1c'nin 11. adımında).
* **Personelden kopya** (`copy_from_personnel`): okul personelinin adı ve görev türü kopyalanır,
  personel bağı (`personnel`) kurulur; görev türü `YONETICI` birlik kişisinde `IDARECI`'dir
  (görünen adı "İdareci", plan F1c kararları). Bir personelin tek birlik kişi kaydı olur.
* **Veli listesinden kopya** (`copy_from_parent`, tasarım §8.4 (3): liste "aday olacak velinin adının
  `OabPerson`'a kopyalanması" için de kullanılır): ad kör indeksle aranır (liste ekranda dökülmez),
  satırın adı kopyalanır — son sözcük soyad, kalanı ad (yanlışsa ekranda düzeltilir) — kişi veli
  işaretiyle açılır. Arama aktarımın dönem kapsamındadır (`imports.roster_term_rows`).

"OLASI AYNI KİŞİ" (tasarım §13 D30): ad kör indeksi tekil değildir (adaşlık). Aynı indeksle başka
kişi varsa kayıt yazılmaz, 409 `olasi_ayni_kisi` döner; kullanıcı aynı kişi olmadığını onaylarsa
(`ayni_kisi_degil`) yazılır. Ad değişikliği de aynı soruyu sorar. Engel değil, sorudur (emsal
`hatalar.RevizyonOnayiGerekli`).

OKUL MÜDÜRÜ İŞARETİ (`is_principal`; plan F1c kararları): kayıt açılırken okul kartındaki müdür adıyla
`name_key` eşleşirse kendiliğinden konur; yanlışsa güncellemeyle (izli) kaldırılır; eşleşme yoksa elle
işaretlenir. Okul kartı sonradan değişirse var olan kayıtlar değişmez.

DURUM KİLİDİ (tasarım §5 O1, O2): kişi kaydı silinmez, `PASIF` olur. Kişi dönemsiz kayıttır, kilidi
kendi durumudur: `PASIF` kişinin alanları değişmez, yalnız yeniden etkinleştirilir (409 `kisi_pasif`).

Kural kullanmazlar: kişi kaydında kural paketi değeri ya da denetimi yoktur (koltuk uygunluğu ve seçilme
sayacı organ üyeliğindedir, F1c 5. adım); bu yüzden `yazma_kapisi()` çağrılmaz. Rol kapısı uç
katmanındadır (`rol_izinleri.KURALLAR` M2). Her yazım veriyle aynı işlemde iz satırı yazar
(`denetim_izi.degisiklik`); kişi KVKK silme kümesindedir, satır değer taşımaz (`models.kisi`).

Personel kancaları (`AppConfig.ready`): `personnel_linked` personelin silinmesini keser (bağı olan
personel silinmez, ayrılış yoluna yönlendirilir; tasarım §5.4), `personnel_merged` "olası aynı kişi"
birleştirmesinde bağı hedef personele taşır.
"""

from __future__ import annotations

from typing import Any, Final

from django.db import transaction
from django.db.models import QuerySet

from apps.oab.hatalar import KisiPasif, OlasiAyniKisi
from apps.oab.models import (
    OabPerson,
    PersonKind,
    PersonStatus,
    kisi_adi_kor_indeksi,
)
from apps.oab.models.kisi import KISI_ADI_MAX
from apps.oab.services import iz
from apps.okul import denetim_izi, name_match
from apps.okul.models import (
    MemberKind,
    ParentRoster,
    Personnel,
    SchoolConfig,
    parent_name_blind_index,
)
from apps.okul.services import app_password, imports
from shared.crypto import has_corrupt

#: Personelin görev türü → birlik kişisinin türü (plan F1c kararları: `YONETICI` → `IDARECI`).
PERSONEL_TURU: Final[dict[str, str]] = {
    MemberKind.OGRETMEN.value: PersonKind.OGRETMEN.value,
    MemberKind.YONETICI.value: PersonKind.IDARECI.value,
    MemberKind.DIGER.value: PersonKind.DIGER.value,
}

#: Güncellemeyle değişebilen alanlar. Personel bağı yalnız kopyayla kurulur, birleştirmeyle taşınır.
GUNCELLENEBILIR: Final = frozenset(
    {
        "kind",
        "first_name",
        "last_name",
        "is_parent",
        "adult_declared",
        "is_principal",
        "external_yk_terms",
        "external_dk_chair_terms",
        "status",
    }
)

PERSONEL_ZATEN_BAGLI = "Bu personelin birlik kişi kaydı zaten var."
PERSONEL_ADI_OKUNAMADI = "Personel kaydının adı okunamadı (kayıt bozuk); kişiyi elle ekleyin."
VELI_LISTESINDE_YOK = "Veli listesinde bu adla satır bulunamadı."
VELI_ADI_OKUNAMADI = "Veli listesindeki ad okunamadı (kayıt bozuk); kişiyi elle ekleyin."
VELI_ADI_AYRISTIRILAMADI = (
    "Veli listesindeki ad tek sözcük; ad ve soyad ayrıştırılamadı. Kişiyi elle ekleyin."
)
VELI_ADI_UZUN = "Veli listesindeki ad ad ya da soyad alanına sığmıyor; kişiyi elle ekleyin."


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _olasi_ayni_kisiler(indeks: str, *, haric: int | None) -> QuerySet[OabPerson]:
    """Aynı ad kör indeksli öteki kişiler (durumu ne olursa olsun)."""
    if not indeks:
        return OabPerson.objects.none()
    kisiler = OabPerson.objects.filter(name_index=indeks)
    return kisiler if haric is None else kisiler.exclude(pk=haric)


def olasi_ayni_kisi_sorusu(
    first_name: object, last_name: object, *, haric: int | None, ayni_kisi_degil: bool
) -> None:
    """Aynı adla başka kişi varsa ve kullanıcı onaylamadıysa 409 `olasi_ayni_kisi` (D30)."""
    if ayni_kisi_degil:
        return
    if _olasi_ayni_kisiler(kisi_adi_kor_indeksi(first_name, last_name), haric=haric).exists():
        raise OlasiAyniKisi


def okul_muduru_mu(first_name: object, last_name: object) -> bool:
    """Ad-soyad okul kartındaki müdür adıyla `name_key` eşleşmesi veriyor mu? (plan F1c kararları)"""
    kart = SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).first()
    if kart is None or not isinstance(first_name, str) or not isinstance(last_name, str):
        return False
    mudur = name_match.name_key(kart.principal_name)
    return bool(mudur) and mudur == name_match.name_key(f"{first_name} {last_name}")


# ---------------------------------------------------------------------------
# Yazma yolları
# ---------------------------------------------------------------------------
@transaction.atomic
def create_person(
    *,
    kind: str,
    first_name: str,
    last_name: str,
    is_parent: bool | None = None,
    adult_declared: bool = False,
    external_yk_terms: int | None = None,
    external_dk_chair_terms: int | None = None,
    personnel: Personnel | None = None,
    ayni_kisi_degil: bool = False,
) -> OabPerson:
    """Birlik kişisi kaydı açar (`OLUSTUR`). `is_parent` verilmezse türü veli olan kişi velidir."""
    app_password.require_password_set()
    olasi_ayni_kisi_sorusu(first_name, last_name, haric=None, ayni_kisi_degil=ayni_kisi_degil)
    hesap = iz.yazar_hesabi()
    kisi = OabPerson.objects.create(
        kind=kind,
        first_name=first_name,
        last_name=last_name,
        is_parent=(kind == PersonKind.VELI) if is_parent is None else is_parent,
        adult_declared=adult_declared,
        is_principal=okul_muduru_mu(first_name, last_name),
        personnel=personnel,
        external_yk_terms=external_yk_terms,
        external_dk_chair_terms=external_dk_chair_terms,
        status=PersonStatus.AKTIF,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kisi, onceki=None)
    return kisi


@transaction.atomic
def update_person(kisi: OabPerson, *, ayni_kisi_degil: bool = False, **alanlar: Any) -> OabPerson:
    """Yalnız DEĞİŞEN alanı yazar (`GUNCELLE`; durum `DURUM`). Pasif kişide yalnız durum değişir."""
    app_password.require_password_set()
    bilinmeyen = set(alanlar) - GUNCELLENEBILIR
    if bilinmeyen:
        raise ValueError(f"Güncellenemeyen alan: {', '.join(sorted(bilinmeyen))}")
    guncel = OabPerson.objects.get(pk=kisi.pk)
    degisen = [ad for ad, deger in alanlar.items() if getattr(guncel, ad) != deger]
    if not degisen:
        return guncel
    if guncel.status == PersonStatus.PASIF and set(degisen) - {"status"}:
        raise KisiPasif
    if {"first_name", "last_name"} & set(degisen):
        olasi_ayni_kisi_sorusu(
            alanlar.get("first_name", guncel.first_name),
            alanlar.get("last_name", guncel.last_name),
            haric=guncel.pk,
            ayni_kisi_degil=ayni_kisi_degil,
        )
    onceki = denetim_izi.anlik(guncel)
    for ad in degisen:
        setattr(guncel, ad, alanlar[ad])
    guncel.updated_by_id = iz.yazar_hesabi()
    guncel.save(update_fields=[*degisen, "updated_at", "updated_by"])
    denetim_izi.degisiklik(guncel, onceki=onceki)
    return guncel


@transaction.atomic
def copy_from_personnel(personel: Personnel, *, ayni_kisi_degil: bool = False) -> OabPerson:
    """Personelden birlik kişisi: ad, soyad ve görev türü (`YONETICI` → `IDARECI`), personel bağı."""
    app_password.require_password_set()
    if OabPerson.objects.filter(personnel=personel).exists():
        raise ValueError(PERSONEL_ZATEN_BAGLI)
    if has_corrupt(personel):
        raise ValueError(PERSONEL_ADI_OKUNAMADI)
    return create_person(
        kind=PERSONEL_TURU[str(personel.member_kind)],
        first_name=str(personel.first_name),
        last_name=str(personel.last_name),
        personnel=personel,
        ayni_kisi_degil=ayni_kisi_degil,
    )


def _veli_satiri(full_name: str) -> ParentRoster | None:
    """Aktarımın dönem kapsamında adı kör indeksle eşleşen ilk veli satırı (liste dökülmez)."""
    indeks = parent_name_blind_index(full_name)
    if not indeks:
        return None
    satirlar = imports.roster_term_rows(imports.current_roster_term_id())
    return satirlar.filter(name_index=indeks).order_by("pk").first()


def veli_adini_ayristir(full_name: object) -> tuple[str, str]:
    """Veli listesindeki tek alanlık ad → (ad, soyad): son sözcük soyad, kalanı ad (plan F1c-4)."""
    if not isinstance(full_name, str):
        raise ValueError(VELI_ADI_OKUNAMADI)
    sozcukler = full_name.split()
    if len(sozcukler) < 2:
        raise ValueError(VELI_ADI_AYRISTIRILAMADI)
    ad, soyad = " ".join(sozcukler[:-1]), sozcukler[-1]
    if len(ad) > KISI_ADI_MAX or len(soyad) > KISI_ADI_MAX:
        raise ValueError(VELI_ADI_UZUN)
    return ad, soyad


@transaction.atomic
def copy_from_parent(full_name: str, *, ayni_kisi_degil: bool = False) -> OabPerson:
    """Veli listesinden birlik kişisi (tasarım §8.4 (3)): satırın adı kopyalanır, kişi velidir."""
    app_password.require_password_set()
    satir = _veli_satiri(full_name)
    if satir is None:
        raise ValueError(VELI_LISTESINDE_YOK)
    ad, soyad = veli_adini_ayristir(satir.full_name)
    return create_person(
        kind=PersonKind.VELI,
        first_name=ad,
        last_name=soyad,
        is_parent=True,
        ayni_kisi_degil=ayni_kisi_degil,
    )


# ---------------------------------------------------------------------------
# Personel kancaları (`apps.okul.services.persons` kayıt defterleri; `AppConfig.ready`)
# ---------------------------------------------------------------------------
def personnel_linked(personel: Personnel) -> bool:
    """Personel bir birlik kişisine bağlı mı? Bağlıysa kullanıcı silemez (tasarım §5.4)."""
    return OabPerson.objects.filter(personnel=personel).exists()


def personnel_merged(kaynak: Personnel, hedef: Personnel) -> None:
    """Birleştirmede kaynağa bağlı birlik kişileri hedefe bağlanır (her biri `GUNCELLE` satırı)."""
    for kisi in OabPerson.objects.filter(personnel=kaynak).order_by("pk"):
        onceki = denetim_izi.anlik(kisi)
        kisi.personnel = hedef
        kisi.updated_by_id = iz.yazar_hesabi()
        kisi.save(update_fields=["personnel", "updated_at", "updated_by"])
        denetim_izi.degisiklik(kisi, onceki=onceki)
