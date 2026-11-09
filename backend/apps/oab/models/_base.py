"""`oab` modellerinin soyut temeli ve ortak seçenek kümeleri (tasarım §5.2).

Temel alanlar tasarım §5 O4'tür: `created_at`, `created_by`, `updated_at`, `updated_by`. `shared`
`okul.Account`'a bağlanmasın diye (plan F1b-1 "created_by/updated_by") alanlar burada, `oab`
tarafındadır. Yazarı olmayan kayıt da olur: gün işi ve sistem işi `SISTEM` adına yazar, hesabı
yoktur (`apps.okul.oturum`); bu yüzden iki yazar alanı boş olabilir. Temelde `deleted_at` yoktur:
yanlış kayıt silinmez, `IPTAL` ya da `PASIF` olur (O1).

Seçeneklerin değerleri Türkçe büyük harf ASCII'dir, etiketleri Yönetmelik terimiyle yazılır (O8).
Değerlerin kaynağı tasarım §5.2.1 `OabTerm` ile §5.2.2 `OabPerson`, `OrganMembership` satırları ve
"Temsil türleri" listesidir. Kurul bileşimleri ve sayılar burada değil, kural paketindedir (altın
kural 2).
"""

from __future__ import annotations

from django.db import models


class OabBaseModel(models.Model):
    """`oab` modellerinin ortak alanları (tasarım §5 O4)."""

    created_at = models.DateTimeField("oluşturulma", auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="oluşturan hesap",
    )
    updated_at = models.DateTimeField("güncellenme", auto_now=True)
    updated_by = models.ForeignKey(
        "okul.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="güncelleyen hesap",
    )

    class Meta:
        abstract = True


class TermStatus(models.TextChoices):
    """Birlik döneminin durumu: `HAZIRLIK` → `ACIK` → `KAPANISTA` → `KAPANDI`; `HAZIRLIK` → `IPTAL`."""

    HAZIRLIK = "HAZIRLIK", "Hazırlık"
    ACIK = "ACIK", "Açık"
    KAPANISTA = "KAPANISTA", "Kapanışta"
    KAPANDI = "KAPANDI", "Kapandı"
    IPTAL = "IPTAL", "İptal"


class PersonKind(models.TextChoices):
    """Birlik kişisinin türü. `IDARECI` "Program yöneticisi" ile karışmasın (plan F1c kararları)."""

    VELI = "VELI", "Veli"
    OGRETMEN = "OGRETMEN", "Öğretmen"
    IDARECI = "IDARECI", "İdareci"
    HAYIRSEVER = "HAYIRSEVER", "Hayırsever"
    KURSIYER = "KURSIYER", "Kursiyer"
    DIGER = "DIGER", "Diğer"


class PersonStatus(models.TextChoices):
    """Birlik kişi kaydının durumu; kişi kaydı silinmez, `PASIF` olur (O1)."""

    AKTIF = "AKTIF", "Aktif"
    PASIF = "PASIF", "Pasif"


class OrganType(models.TextChoices):
    """Üyelik kaydının bağlı olduğu organ ya da görev kanalı."""

    YONETIM_KURULU = "YK", "Yönetim Kurulu"
    DENETLEME_KURULU = "DK", "Denetleme Kurulu"
    DIVAN = "DIVAN", "Divan"
    ALIM_KOMISYONU = "ALIM_KOMISYONU", "Alım komisyonu"
    TEMSILCI = "TEMSILCI", "Temsilci"


class MembershipRole(models.TextChoices):
    """Organ içi görev."""

    BASKAN = "BASKAN", "Başkan"
    BASKAN_YARDIMCISI = "BASKAN_YARDIMCISI", "Başkan yardımcısı"
    MUHASIP = "MUHASIP", "Muhasip"
    SEKRETER = "SEKRETER", "Sekreter"
    KATIP = "KATIP", "Kâtip"
    UYE = "UYE", "Üye"


class SeatType(models.TextChoices):
    """Seçildiği koltuk; değişmez, yedekten çağrıyı `promoted_on` gösterir (plan F1c kararları)."""

    ASIL = "ASIL", "Asıl"
    YEDEK = "YEDEK", "Yedek"


class SeatGroup(models.TextChoices):
    """Denetleme Kurulunda koltuk grubu."""

    VELI = "VELI", "Veli"
    OGRETMEN = "OGRETMEN", "Öğretmen"


class ElectedBy(models.TextChoices):
    """Üyenin göreve geldiği kanal."""

    GENEL_KURUL = "GENEL_KURUL", "Genel kurul"
    OGRETMENLER_KURULU = "OGRETMENLER_KURULU", "Öğretmenler kurulu"
    MEM_GOREVLENDIRME = "MEM_GOREVLENDIRME", "İl/ilçe millî eğitim müdürlüğü görevlendirmesi"
    YK_KARARI = "YK_KARARI", "Yönetim kurulu kararı"
    OKUL_IDARESI = "OKUL_IDARESI", "Okul idaresi"
    KENDILIGINDEN = "KENDILIGINDEN", "Kendiliğinden"


class MembershipSource(models.TextChoices):
    """`DEVRALINAN`: geçiş kurulumunda girilen, programdan önce seçilmiş görevdeki üye (§7.9)."""

    PROGRAM = "PROGRAM", "Program"
    DEVRALINAN = "DEVRALINAN", "Devralınan"


class MembershipStatus(models.TextChoices):
    """Üyelik durumu: `ADAY` → `SECILDI` → `DUSTU`; `ADAY` · `SECILDI` → `IPTAL` (yanlış kayıt)."""

    ADAY = "ADAY", "Aday"
    SECILDI = "SECILDI", "Seçildi"
    DUSTU = "DUSTU", "Düştü"
    IPTAL = "IPTAL", "İptal"


class DropKind(models.TextChoices):
    """Üyeliğin düşme türü; düşmede zorunludur."""

    OGRENCI_AYRILDI = "OGRENCI_AYRILDI", "Öğrencisi okuldan ayrıldı"
    DEVAMSIZLIK = "DEVAMSIZLIK", "Devamsızlık"
    ISTIFA = "ISTIFA", "İstifa"
    BASKA_KURUMDA_GOREV = "BASKA_KURUMDA_GOREV", "Başka kurumda görev"
    OLAGANUSTU_GK_SECIMI = "OLAGANUSTU_GK_SECIMI", "Olağanüstü genel kurul seçimi"
    DIGER = "DIGER", "Diğer"


class Representation(models.TextChoices):
    """Birlik temsilcisinin görev aldığı kurul ya da komisyon (tasarım "Temsil türleri")."""

    ODUL_DISIPLIN_KURULU = "ODUL_DISIPLIN_KURULU", "Okul öğrenci ödül ve disiplin kurulu"
    DAVRANIS_DEGERLENDIRME_KURULU = (
        "DAVRANIS_DEGERLENDIRME_KURULU",
        "Öğrenci davranışlarını değerlendirme kurulu",
    )
    SOSYAL_ETKINLIKLER_KURULU = "SOSYAL_ETKINLIKLER_KURULU", "Okul sosyal etkinlikler kurulu"
    KONTENJAN_KOMISYONU = "KONTENJAN_KOMISYONU", "Kontenjan belirleme komisyonu"
    RPD_YURUTME_KOMISYONU = (
        "RPD_YURUTME_KOMISYONU",
        "Rehberlik ve psikolojik danışma hizmetleri yürütme komisyonu",
    )
    TASIMACI_TESPIT_KOMISYONU = "TASIMACI_TESPIT_KOMISYONU", "Taşımacıyı tespit komisyonu"
    MUHAMMEN_BEDEL_KOMISYONU = "MUHAMMEN_BEDEL_KOMISYONU", "Muhammen bedel tespit komisyonu"
    KIRALAMA_IHALE_KOMISYONU = "KIRALAMA_IHALE_KOMISYONU", "Kiralama ihale komisyonu"
    KAMPUS_YONETIMI = "KAMPUS_YONETIMI", "Kampüs yönetimi"
    KANTIN_DENETIM_KOMISYONU = "KANTIN_DENETIM_KOMISYONU", "Kantin denetim komisyonu"
    DIGER = "DIGER", "Diğer"
