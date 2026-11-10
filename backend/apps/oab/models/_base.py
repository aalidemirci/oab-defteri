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
    """Birlik döneminin durumu: `HAZIRLIK` → `ACIK` → `KAPANISTA` → `KAPANDI`; `HAZIRLIK` → `IPTAL`.

    Geçiş kurulumunun dönemi (genel kurulsuz açılan ilk dönem) "Geçiş kurulumu tamamlandı" işaretinden
    önce `ACIK` → `IPTAL` olabilir: yanlış girilmiş geçiş kaydının iptal yolu (plan F1c 8. adımın kararı).
    """

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
    """Birlik temsilcisinin görev aldığı kurul ya da komisyon (tasarım "Temsil türleri").

    `PAY_DAGITIM_KOMISYONU` tasarımın temsil türleri listesinde yoktur; §6.4.4 (`temsilci.pay_dagitim_
    komisyonu`, md. 17/1-b-3: "başkan bu komisyona seçildiyse temsilci satırı") ve E03'ün "pay dağıtım
    komisyonu satırı yalnız başkan seçildiyse" hükmü kaydı ister (plan F1c 6. adım).
    """

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
    PAY_DAGITIM_KOMISYONU = "PAY_DAGITIM_KOMISYONU", "Pay dağıtım komisyonu"
    KAMPUS_YONETIMI = "KAMPUS_YONETIMI", "Kampüs yönetimi"
    KANTIN_DENETIM_KOMISYONU = "KANTIN_DENETIM_KOMISYONU", "Kantin denetim komisyonu"
    DIGER = "DIGER", "Diğer"


class AssemblyKind(models.TextChoices):
    """Genel kurulun türü."""

    OLAGAN = "OLAGAN", "Olağan"
    OLAGANUSTU = "OLAGANUSTU", "Olağanüstü"


class AssemblyStatus(models.TextChoices):
    """Genel kurulun durumu (tasarım §7.1)."""

    PLANLANDI = "PLANLANDI", "Planlandı"
    CAGRILDI = "CAGRILDI", "Çağrıldı"
    ILAN_EDILDI = "ILAN_EDILDI", "İlan edildi"
    YETER_SAYI_YOK = "YETER_SAYI_YOK", "Yeter sayı yok"
    YAPILDI = "YAPILDI", "Yapıldı"
    TUTANAK_TAMAM = "TUTANAK_TAMAM", "Tutanak tamam"
    IPTAL = "IPTAL", "İptal"


class ComplianceKind(models.TextChoices):
    """Uyum satırının türü (tasarım §5 O3)."""

    SAPMA = "SAPMA", "Sapma"
    EKSIK = "EKSIK", "Eksik"
    TAKVIM = "TAKVIM", "Takvim"


class ComplianceObligation(models.TextChoices):
    """Takvim satırının yükümlülüğü (tasarım §5.2.7)."""

    DEFTER_TASDIK = "DEFTER_TASDIK", "Defter tasdiki"
    DK_INCELEME = "DK_INCELEME", "Denetleme Kurulu incelemesi"
    MEM_DENETIMI = "MEM_DENETIMI", "İl/ilçe millî eğitim müdürlüğü denetimi"
    KANTIN_FAALIYET_BELGESI = "KANTIN_FAALIYET_BELGESI", "Kantin faaliyet belgesi"
    KANTIN_CALISAN_BELGE_YENILEME = (
        "KANTIN_CALISAN_BELGE_YENILEME",
        "Kantin çalışanı belge yenileme",
    )
    TUFE_BILDIRIMI = "TUFE_BILDIRIMI", "TÜFE bildirimi"
    MILLI_EMLAK_BILDIRIMI = "MILLI_EMLAK_BILDIRIMI", "Millî Emlak bildirimi"
    IBRA_EDILMEDI_BILDIRIMI = "IBRA_EDILMEDI_BILDIRIMI", "İbra edilmedi bildirimi"
    TEFBIS_YONETIM_BILGISI = "TEFBIS_YONETIM_BILGISI", "TEFBİS yönetim bilgisi"
    TEFBIS_BANKA_BILGISI = "TEFBIS_BANKA_BILGISI", "TEFBİS banka bilgisi"
    TEFBIS_BUTCE_GIRISI = "TEFBIS_BUTCE_GIRISI", "TEFBİS bütçe girişi"
    DIGER = "DIGER", "Diğer"


class EligibilityBar(models.TextChoices):
    """Görev alma engeli tespit edildi mi (hüküm alanı; md. 12/4-5, 14/7)."""

    YOK = "YOK", "Yok"
    VAR = "VAR", "Var"


class EligibilityBarBasis(models.TextChoices):
    """Görev alma engelinin dayanağı (şifreli alanın değerleri; özel nitelikli, KVKK md. 6/1)."""

    SUC_12_5_14_7 = "SUC_12_5_14_7", "Suç engeli (md. 12/5, 14/7)"
    TEK_BIRLIK_12_4 = "TEK_BIRLIK_12_4", "Başka birlik yönetiminde görev (md. 12/4)"


class BookKind(models.TextChoices):
    """Resmî defterin türü (tasarım §5.2.8; F1c'de yalnız karar defteri kullanılır)."""

    KARAR_DEFTERI = "KARAR_DEFTERI", "Karar defteri"
    GELIR_GIDER_DEFTERI = "GELIR_GIDER_DEFTERI", "Gelir-gider defteri"
    GELEN_GIDEN_EVRAK_DEFTERI = "GELEN_GIDEN_EVRAK_DEFTERI", "Gelen-giden evrak defteri"
    DIGER = "DIGER", "Diğer"


class BookCertifier(models.TextChoices):
    """Defteri tasdik eden makam (md. 23/2)."""

    NOTER = "NOTER", "Noter"
    IL_ILCE_MEM = "IL_ILCE_MEM", "İl/ilçe millî eğitim müdürlüğü"


class BookStatus(models.TextChoices):
    """Defterin durumu. `IPTAL`: yanlış girilmiş geçiş kaydı; yalnız `KULLANIMDA` → `IPTAL`, geçiş
    kurulumu tamamlanmadan (plan F1c 8. adımın kararı). Öteki geçişler F3'ün defter ekranındadır."""

    KULLANIMDA = "KULLANIMDA", "Kullanımda"
    DOLDU = "DOLDU", "Doldu"
    ARSIVDE = "ARSIVDE", "Arşivde"
    IPTAL = "IPTAL", "İptal"


class MeetingKind(models.TextChoices):
    """Kurul toplantısının türü (tasarım §5.2.4)."""

    AYLIK = "AYLIK", "Aylık"
    OLAGANUSTU = "OLAGANUSTU", "Olağanüstü"
    GOREV_BOLUMU = "GOREV_BOLUMU", "Görev bölümü"


class MeetingStatus(models.TextChoices):
    """Kurul toplantısının durumu: `PLANLANDI` → `YAPILDI` · `YETER_SAYI_YOK` · `IPTAL`."""

    PLANLANDI = "PLANLANDI", "Planlandı"
    YAPILDI = "YAPILDI", "Yapıldı"
    YETER_SAYI_YOK = "YETER_SAYI_YOK", "Yeter sayı yok"
    IPTAL = "IPTAL", "İptal"


class DecisionKind(models.TextChoices):
    """Kurul kararının türü (tasarım §5.2.4)."""

    OLAGAN = "OLAGAN", "Olağan"
    GENEL_KARAR = "GENEL_KARAR", "Genel karar"
    HARCAMA = "HARCAMA", "Harcama"
    GOREV_BOLUMU = "GOREV_BOLUMU", "Görev bölümü"
    YEDEK_CAGIRMA = "YEDEK_CAGIRMA", "Yedek çağırma"
    KOCAN_KAYIT = "KOCAN_KAYIT", "Koçan kaydı"
    GK_CAGRISI = "GK_CAGRISI", "Genel kurul çağrısı"
    BUTCE = "BUTCE", "Bütçe"
    DIGER = "DIGER", "Diğer"


class DecisionStatus(models.TextChoices):
    """Kararın durumu: `TASLAK` → `KABUL_EDILDI` · `REDDEDILDI`; `KABUL_EDILDI` → `DEFTERE_ISLENDI`;
    `TASLAK` → `IPTAL`; defterde fiilen yazılı geçersiz karar `DEFTERDE_SAKAT`."""

    TASLAK = "TASLAK", "Taslak"
    KABUL_EDILDI = "KABUL_EDILDI", "Kabul edildi"
    REDDEDILDI = "REDDEDILDI", "Reddedildi"
    DEFTERE_ISLENDI = "DEFTERE_ISLENDI", "Deftere işlendi"
    IPTAL = "IPTAL", "İptal"
    DEFTERDE_SAKAT = "DEFTERDE_SAKAT", "Defterde sakat"
