"""Birlik kişisi (tasarım §5.2.2 `OabPerson`; §12.A `OabPerson` UYARLA; plan F1c-4).

Kaynak modülden (tasarım §12.A) çıkanlar: T.C. kimlik no ve kör indeksi, TCKN tekil kısıtı, telefon
ve kör indeksi, `linked_user_id`, ada göre `Meta.ordering` (ad şifrelidir, veritabanında
sıralanamaz; sıra seçicide Python'dadır). Eklenenler: şifreli ad ve soyad, adın kör indeksi
(`name_index`), veli, yaş ve müdür işaretleri, personel bağı, programdan önceki seçilme sayıları ve
durum (`AKTIF` · `PASIF`).

KÖR İNDEKS (`name_index`) YALNIZ `save()` İLE YAZILIR (emsal `okul.ParentRoster`): ad ve soyad
`name_match.name_key` ile katlanıp `crypto.blind_index`'ten geçer; veli listesinin indeksiyle aynı
yoldur, böylece adaylığa geçen velinin kaydı listedeki satırla eşleşir. `QuerySet.update(first_name=…)`
ve toplu yazım indeksi atlar; kişi adı toplu yazılmaz (bekçisi `apps/oab/tests/test_kisiler.py`).
İndeks tekil DEĞİLDİR (adaşlık): aynı indeksle ikinci kayıt "olası aynı kişi" sorusunu doğurur
(`services.kisiler`; tasarım §13 D30).

DENETİM İZİ (tasarım §4.6.2, §5 O4): kişi kaydı KVKK silme kümesindedir (§5.4: hiçbir birlik kaydına
bağlanmamış kişi dönem kapanışında silinir; tasarımın `SURELI_KISISEL_ALANLAR` sabiti F4'te). Bu
yüzden `values` BOŞTUR ve ad, soyad ile kör indeks içerik MAC'ine GİRMEZ (`okul.Personnel` emsali):
silinen kişinin adı izden aday sözlüğüyle geri bulunamaz. Durum (`AKTIF` · `PASIF`) ayrı `DURUM` satırıdır.

Kişi kaydı silinmez, `PASIF` olur (O1). Dönemsiz kayıttır; kilidi kendi durumudur (O2): `PASIF`
kişinin alanları değişmez, yalnız yeniden etkinleştirilir (`services.kisiler`).
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models
from django.db.models import Q

from apps.oab.models._base import OabBaseModel, PersonKind, PersonStatus
from apps.okul.models import parent_name_blind_index
from shared.crypto import EncryptedCharField, is_corrupt

#: Ad ve soyadın üst sınırı (karakter; şifreli sütunun düz metni; `okul.Personnel` ile aynı).
KISI_ADI_MAX = 100


def kisi_adi_kor_indeksi(first_name: object, last_name: object) -> str:
    """Ad-soyadın kör indeksi; veli listesinin (`okul.parent_name_blind_index`) yoluyla aynıdır.

    Metin olmayan değer (çözülemeyen alan işareti) boş anahtar verir. Anahtar bellekte değilse
    `KeyMissingError` (fail-closed).
    """
    if not isinstance(first_name, str) or not isinstance(last_name, str):
        return ""
    return parent_name_blind_index(f"{first_name} {last_name}")


class OabPerson(OabBaseModel):
    """Birlik kişisi: organ üyeliği, aday, komisyon ve imza bloklarının tek kaynağı (O6)."""

    #: Denetim izinde değeri yazılabilen alan YOK (KVKK silme kümesi; tasarım §4.6.2, §5 O4).
    IZ_DEGER_ALANLARI: ClassVar[tuple[str, ...]] = ()
    #: İçerik MAC'ine giren alanlar: kimlik ve KVKK silme kümesindeki kişi alanları hariç.
    IZ_OZET_ALANLARI: ClassVar[tuple[str, ...]] = (
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "kind",
        "is_parent",
        "adult_declared",
        "is_principal",
        "personnel",
        "external_yk_terms",
        "external_dk_chair_terms",
        "status",
    )
    #: İçerik MAC'inin DIŞINDAKİ alanlar: silinecek kişi verisi ve adın kör indeksi.
    IZ_MAC_DISI_ALANLARI: ClassVar[tuple[str, ...]] = ("first_name", "last_name", "name_index")
    IZ_DURUM_ALANLARI: ClassVar[tuple[str, ...]] = ("status",)

    kind = models.CharField("tür", max_length=16, choices=PersonKind.choices)
    first_name = EncryptedCharField("ad", max_length=KISI_ADI_MAX)
    last_name = EncryptedCharField("soyad", max_length=KISI_ADI_MAX)
    name_index = models.CharField(
        "ad kör indeksi", max_length=64, blank=True, default="", editable=False
    )
    #: Velidir: okulda öğrencisi var. Türü öğretmen ya da idareci olan kişi de veli olabilir; YK, DK
    #: veli koltuğu ve divan uygunluğu bu işarete bakar (tasarım §5.2.2, §6.4.1-§6.4.3).
    is_parent = models.BooleanField("veli", default=False)
    #: Kursiyer için "18 yaşını doldurmuştur" beyanı; doğum tarihi tutulmaz.
    adult_declared = models.BooleanField("18 yaşını doldurmuştur", default=False)
    #: Okul müdürü: okul kartındaki müdür adıyla eşleşirse kendiliğinden konur, yanlışsa izle
    #: kaldırılır, eşleşme yoksa elle işaretlenir (plan F1c kararları); YK'ye girme engeli buna bakar.
    is_principal = models.BooleanField("okul müdürü", default=False)
    personnel = models.ForeignKey(
        "okul.Personnel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="personel kaydı",
    )
    #: Programdan önceki seçilme sayıları (eski karar defterinden beyan); boş "bilinmiyor"dur.
    #: Beyan görevdeki seçimi içerir; `DEVRALINAN` üyelik sayaca ayrıca girmez (plan F1c kararları).
    external_yk_terms = models.PositiveSmallIntegerField(
        "programdan önceki yönetim kurulu seçilme sayısı", null=True, blank=True
    )
    external_dk_chair_terms = models.PositiveSmallIntegerField(
        "programdan önceki Denetleme Kurulu başkanlığı sayısı", null=True, blank=True
    )
    status = models.CharField(
        "durum", max_length=8, choices=PersonStatus.choices, default=PersonStatus.AKTIF
    )

    class Meta:
        verbose_name = "birlik kişisi"
        verbose_name_plural = "birlik kişileri"
        # Şifreli adda veritabanı sıralaması anlamsızdır; kullanıcıya gösterilen sıra seçicidedir.
        ordering = ["pk"]
        indexes = [
            models.Index(fields=["name_index"], name="oab_oabperson_name_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=PersonKind.values), name="ck_oabperson_kind"
            ),
            models.CheckConstraint(
                condition=Q(status__in=PersonStatus.values), name="ck_oabperson_status"
            ),
        ]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Adın kör indeksini günceller, sonra kaydeder (emsal `okul.ParentRoster.save`).

        `update_fields` verilmişse ve ad ya da soyad içinde yoksa indeks yeniden hesaplanmaz.
        Ad ya da soyad çözülemiyorsa (`CorruptField`, tasarım §13 D48) indeks BOŞALTILIR: işaretin
        indeksi anlamsızdır ve ad iki alanda durduğu için öteki alan değişmiş olabilir; eski indeks
        artık taşınmayan adla "olası aynı kişi" eşleşmesi üretirdi (`okul.ParentRoster`'ın tek alanlı
        emsalinde ad değişmemiştir, orada indeks kalır). Boş indeks hiçbir D30 eşleşmesi üretmez.
        """
        update_fields = kwargs.get("update_fields")
        adi_yazildi = update_fields is None or bool(
            {"first_name", "last_name"} & set(update_fields)
        )
        if adi_yazildi:
            if is_corrupt(self.first_name) or is_corrupt(self.last_name):
                self.name_index = ""
            else:
                self.name_index = kisi_adi_kor_indeksi(self.first_name, self.last_name)
            if update_fields is not None and "name_index" not in update_fields:
                kwargs["update_fields"] = [*update_fields, "name_index"]
        super().save(*args, **kwargs)
