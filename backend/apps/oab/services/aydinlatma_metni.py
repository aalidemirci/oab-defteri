"""Kişisel veri aydınlatma metni (E04): dört alt metnin basılacak tam metni (plan F2 §4.1, §9 S8 (i)).

Metin `docs/kesif/2026-11-16-e04-aydinlatma-taslaklari.md`'nin "Basılacak tam metin" bölümleridir;
kullanıcı dört alt metni ve belgenin sonundaki 20 sorunun varsayılanlarını 16.11.2026'da onayladı
("Varsayılanlarla onayla"). Metin HARFİ HARFİNE kurulur: tek harf değiştirilmez; tek istisna K9 açıkken
basılan hukuki sebep satırıdır (aşağıda, soru 11; kullanıcı kararı bekleniyor). Kullanıcının
08.11.2026'da onayladığı cümleler (veli ve personel aktarım ekranlarının aydınlatma metni) ön yüzdeki
`frontend/src/modules/kisiler/metinler.ts` ile BİREBİRDİR; birebirlik testte kaynaktan okunarak
sınanır (`test_evrak_kurallari.py::test_e04_onayli_cumleler_on_yuzle_birebir`).

Taslaktaki işaretlerin koda çevrilişi (onaylı varsayılanlar):

- `{data_controller_text}` → Okul Bilgileri'ndeki `SchoolConfig.data_controller_text` (boşlukları tek
  boşluğa indirilmiş); alan boşken belge üretilmez ve basılmaz (kurucunun işi; plan F2 §9 S6 (iv),
  tasarım KE-20).
- 3. ve 4. bölümün başındaki ‹…› koşul cümlesi (soru 1) olduğu gibi basılır: bölüm, programın o işleri
  kullanılmaya başlandığında geçerlidir.
- KVKK md. 6/3'ün bendi (soru 4) "………" ile basılır; basım uyarısı `UYARI_OZEL_NITELIKLI_BENT`.
- Yeni yönetim kurulunun TEFBİS'e girilmesi cümlesi (soru 6) ‹…› işaretsiz, md. 23/5 çapası olmadan
  ("uygulamada") basılır.
- Yedek cümlesinin ‹…› parçası (soru 8) işaretsiz basılır; sayılar programın yedek ayarlarıdır
  (`desktop/backup.py` `DEFAULT_KEEP_DAYS`, `DEFAULT_KEEP_PRE_MIGRATE`; birebirliği testte).
- Bağışçının T.C. kimlik no'su (K9; soru 11): ayar kapalıyken yalnız "T.C. kimlik no tutulmaz." satırı;
  ayar açıkken amaç, veri, aktarım ve saklama satırları ‹Okulun ayarı açıkken:› öneki düşürülerek
  basılır, hukuki sebep satırı teyit gelene kadar "………" ve basım uyarısıdır
  (`UYARI_TCKN_HUKUKI_SEBEP`). Bu, taslaktan sapmadır: taslağın satırı ‹okulun ayarı açıkken, T.C.
  kimlik no'da: … (KVKK md. 5/2-ç)›'dir; sorunun varsayılanı "‹…› içinde kalır" der, doğrulanamayan
  hukuki sebep basılmaz (altın kural 1). Yorum kullanıcı kararı değildir; satırın taslaktaki gibi mi
  basılacağı kullanıcıya sorulacak (plan F2 §8 10. adımın E04 notu). Ayar alanı F3'te gelir, o güne
  dek açık biçim basılmaz.
- Aylık bildirimde bağışçı adının yer almadığı cümle (soru 12) ‹…› işaretsiz basılır.
- Ekran notu (soru 5) belgeye basılmaz; üretimin ve kartın basım uyarısıdır (`UYARI_HUKUKI_SEBEP_ONERI`,
  onaylı ekran notunun birebir metni).

Madde imleri: liste maddesi "•", alt madde "–" ile başlayan paragraftır (evrak hattında liste bloğu
yoktur; dört çizici aynı paragrafı çizer). Taslaktaki kalın etiketler ("A. Veli listesi") bölüm başlığı,
"Yedekler:" etiketli paragraftır.

Belge kişisizdir (yalnız veri sorumlusunun kurum bilgisi basılır), imzasızdır, konum cümlesi ve müdür
bloğu yoktur (plan F2 §4.1 E04; tasarım §9.6 E04).
"""

from __future__ import annotations

from typing import Final

from shared import evrak
from shared.text import tr_upper

# ---------------------------------------------------------------------------
# 08.11.2026'da onaylanan cümleler (ön yüzdeki `kisiler/metinler.ts` ile BİREBİR)
# ---------------------------------------------------------------------------
VELI_AYDINLATMA_AMACI: Final = (
    "Amaç: Genel kurul toplantısının daveti, katılım cetveli ve toplantı yeter sayısının sayımı "
    "(OAB Yönetmeliği md. 9/2, 9/3, 10/1-a); birlik organlarına aday olan velinin kaydı. Yalnız "
    "veli adı-soyadı ve öğrencinin sınıfı tutulur; telefon, adres, T.C. kimlik no ve öğrencinin "
    "adı tutulmaz."
)
VELI_AYDINLATMA_TOPLAMA: Final = (
    "Toplama yöntemi ve hukuki sebep: Okul idaresinin hazırladığı listeden elektronik ortamda "
    "aktarılır. Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi "
    "(KVKK md. 5/2-ç)."
)
VELI_AYDINLATMA_SAKLAMA: Final = (
    "Saklama: Liste birlik döneminin kapanışında silinir; genel kuruldan sonra daha önce de "
    "silinebilir."
)
PERSONEL_AYDINLATMA_AMACI: Final = (
    "Amaç: Okul-aile birliğinin işlerinde öğretmen ve yöneticilerin adının kullanılması: "
    "Denetleme Kuruluna öğretmen üyelerin seçimi (OAB Yönetmeliği md. 14/1), mal ve hizmet alım "
    "komisyonu (md. 18/1) ve birlik evrakının imza blokları. Yalnız ad-soyad ve görev türü "
    "(öğretmen, yönetici, diğer personel) tutulur."
)
PERSONEL_AYDINLATMA_TOPLAMA: Final = (
    "Toplama yöntemi ve hukuki sebep: e-Okul personel listesinden okul idaresince elektronik "
    "ortamda aktarılır. Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi "
    "(KVKK md. 5/2-ç)."
)
PERSONEL_AYDINLATMA_SAKLAMA: Final = (
    "Saklama: Okuldan ayrılan ve birlik kaydına bağı olmayan personelin kaydı, ayrılışı izleyen "
    "dönem kapanışında silinir."
)
AYDINLATMA_VERI_SORUMLUSU_ETIKETI: Final = "Veri sorumlusu:"
AYDINLATMA_HAKLARINIZ: Final = (
    "Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi "
    "isteme, düzeltilmesini ya da silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak "
    "kullanabilirsiniz."
)
#: Aktarım ekranlarının ekran notu (onaylı); E04'e basılmaz, basım uyarısıdır (soru 5).
AYDINLATMA_EKRAN_NOTU: Final = (
    "Hukuki sebep öneridir; veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir."
)
#: "Saklama: " etiketi (personel metninin saklama cümlesi E04'te "Saklama:" listesinin ilk maddesidir).
SAKLAMA_ETIKETI: Final = "Saklama: "

# ---------------------------------------------------------------------------
# Madde imleri ve satır türleri
# ---------------------------------------------------------------------------
MADDE_IMI: Final = "•"
ALT_MADDE_IMI: Final = "–"
BAS = "baslik"
PAR = "paragraf"
MAD = "madde"
ALT = "alt_madde"
#: (tür, metin)
Satir = tuple[str, str]
#: Veri sorumlusunun yerini tutan işaret (`satirlar` doldurur).
VERI_SORUMLUSU_YERI: Final = "{veri_sorumlusu}"
#: KVKK md. 6/3'ün bendinin ve teyit bekleyen hukuki sebebin yeri (gorev_evraki.BOS ile aynı).
BOS: Final = "………"

# ---------------------------------------------------------------------------
# 0. Belgenin başı (dört bölüme ortak)
# ---------------------------------------------------------------------------
BELGE_ADI: Final = "Kişisel veri aydınlatma metni"
ALT_BASLIK: Final = (
    "Okul-aile birliğinin işlerinde işlenen kişisel veriler · 6698 sayılı Kişisel Verileri Koruma "
    "Kanunu (KVKK) md. 10"
)
GIRIS: Final = (
    "Okul-aile birliğinin işleri, okulun bilgisayarında çalışan OAB Defteri programıyla yürütülür. "
    "Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez. Bu metin, birliğin "
    "işlerinde kişisel verisi işlenen kişileri KVKK md. 10/1 gereği bilgilendirir."
)
BOLUMLER_GIRISI: Final = "Metin dört bölümdür ve her bölüm kendi başına okunur:"
BOLUM_ADLARI: Final = (
    "Veli ve üye",
    "Personel",
    "İstekli, kiracı ve çalışan",
    "Bağışçı ve tedarikçi",
)
ADLANDIRMA: Final = (
    'Metinde "OAB Yönetmeliği", Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliğidir; başında '
    'başka bir mevzuatın adı yazılmayan "md." atıfları bu Yönetmeliğindir. "Usul ve Esaslar", Okul '
    "Servis Araçlarının Çalıştırılmasına İlişkin Usul ve Esaslardır."
)


def bolum_basligi(no: int) -> str:
    """Bölümün başlığı: "1. VELİ VE ÜYE" (Türkçe büyük harf)."""
    return f"{no}. {tr_upper(BOLUM_ADLARI[no - 1])}"


# ---------------------------------------------------------------------------
# Bölümlerin ortak parçaları
# ---------------------------------------------------------------------------
#: KVKK md. 10/1 unsurlarının etiketleri: (a) veri sorumlusu, (b) amaç, (c) aktarım, (ç) toplama
#: yöntemi ve hukuki sebep, (d) haklar (her bölümde bulunur; testte sınanır).
ETIKET_AMAC: Final = "Amaç:"
ETIKET_ISLENEN: Final = "İşlenen veriler:"
ETIKET_TOPLAMA: Final = "Toplama yöntemi ve hukuki sebep:"
ETIKET_AKTARIM: Final = "Aktarım:"
ETIKET_SAKLAMA: Final = "Saklama:"
ETIKET_HAKLAR: Final = "Haklarınız:"
ETIKET_BASVURU: Final = "Başvuru:"
UNSUR_ETIKETLERI: Final = {
    "a": AYDINLATMA_VERI_SORUMLUSU_ETIKETI,
    "b": ETIKET_AMAC,
    "c": ETIKET_AKTARIM,
    "ç": ETIKET_TOPLAMA,
    "d": ETIKET_HAKLAR,
}
VERI_SORUMLUSU_SATIRI: Final = f"{AYDINLATMA_VERI_SORUMLUSU_ETIKETI} {VERI_SORUMLUSU_YERI}"
GONDERMEZ: Final = "Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez."
DENETIME_ACIK: Final = (
    "Birliğin kayıtları, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü "
    "denetim elemanlarına açıktır (md. 26/1)."
)
ARSIV_SURESI: Final = (
    "Birliğin defter ve belgeleri Devlet Arşiv Hizmetleri Hakkında Yönetmelikte öngörülen süreler "
    "kadar okulda saklanır (md. 16/7, 23/6)."
)
#: Gelen-giden evrak kaydı (md. 23/1-c): ilk cümle 3. ve 4. bölümde "İşlenen veriler" maddesidir.
YAZI_KAYDI: Final = (
    "Birliğe yazdığınız ya da birliğin size yazdığı yazı, gelen-giden evrak defterinin tutulması için "
    "(md. 23/1-c) programın gelen-giden evrak kaydına girer: karşı taraf olarak adınız, yazının "
    "konusu ve varsa taranmış örneği şifreli tutulur."
)
YAZI_KAYDI_TAMAMI: Final = (
    f"{YAZI_KAYDI} Kayıt programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası "
    "olarak girilir. Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. "
    "5/2-ç). Kayıt birlik kaydıdır, silinmez; birliğin denetimi için md. 26/1'deki denetim "
    "elemanlarına açıktır."
)
YEDEKLER_ETIKETI: Final = "Yedekler:"
#: Yedek cümlesi (soru 8): `{yonetici}` "Program yöneticisinin" ya da bölümde ilk geçişte açılımıyla.
_YEDEK_KALIBI: Final = (
    "Silinen ya da boşaltılan veri, programın bilgisayardaki şifreli yedeklerinde günlük yedeklerde "
    "en çok 14 gün, güncelleme öncesi yedeklerde son beş güncelleme boyunca kalır. {yonetici} "
    "kaydettiği şifreli dış yedeklerde (ör. USB bellek) veri, yedeğin okulca saklandığı süre boyunca "
    "kalır."
)
YEDEK_CUMLESI: Final = _YEDEK_KALIBI.format(yonetici="Program yöneticisinin")
YEDEK_CUMLESI_ACILIMLI: Final = _YEDEK_KALIBI.format(
    yonetici="Program yöneticisinin (OAB'den sorumlu müdür yardımcısı)"
)
HAKLARINIZ_GIRISI: Final = f"{AYDINLATMA_HAKLARINIZ} Haklarınızın tamamı şunlardır:"
#: KVKK md. 11/1 (a)-(ğ), sırasıyla.
HAKLAR: Final = (
    "kişisel verinizin işlenip işlenmediğini öğrenme;",
    "işlenmişse buna ilişkin bilgi isteme;",
    "işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme;",
    "yurt içinde ya da yurt dışında aktarıldığı üçüncü kişileri bilme;",
    "eksik ya da yanlış işlenmişse düzeltilmesini isteme;",
    "KVKK md. 7'deki şartlarla silinmesini ya da yok edilmesini isteme;",
    "düzeltme ve silmenin, verinin aktarıldığı üçüncü kişilere bildirilmesini isteme;",
    "yalnız otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz "
    "etme;",
    "kanuna aykırı işleme yüzünden zarara uğrarsanız zararın giderilmesini isteme.",
)
BASVURU: Final = (
    "Başvuru: Başvurunuzu yukarıda adı geçen veri sorumlusuna yazıyla ya da Kişisel Verileri Koruma "
    "Kurulunun belirlediği öteki yöntemlerle iletebilirsiniz (KVKK md. 13/1). Başvuru, niteliğine göre "
    "en kısa sürede ve en geç otuz gün içinde ücretsiz sonuçlandırılır; işlem ayrıca bir maliyet "
    "gerektirirse Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki ücret alınabilir (KVKK md. "
    "13/2). Başvurunuz reddedilir, verilen cevap yetersiz bulunur ya da süresinde cevap verilmezse, "
    "cevabı öğrendiğiniz günden başlayarak otuz gün içinde, her durumda başvuru gününden başlayarak "
    "altmış gün içinde Kişisel Verileri Koruma Kuruluna şikâyette bulunabilirsiniz (KVKK md. 14/1)."
)
OZEL_NITELIKLI_SARTI: Final = f"işleme şartı: KVKK md. 6/3'ün {BOS} bendi."


def _haklar_ve_basvuru() -> tuple[Satir, ...]:
    return (
        (PAR, HAKLARINIZ_GIRISI),
        *((MAD, hak) for hak in HAKLAR),
        (PAR, BASVURU),
    )


# ---------------------------------------------------------------------------
# 1. Veli ve üye
# ---------------------------------------------------------------------------
BOLUM_1_KAPSAM: Final = (
    "Kapsam: veliler; yönetim kuruluna ve Denetleme Kuruluna aday olan ve seçilen kişiler; genel "
    "kurul divanında, alım komisyonunda ve birlik temsilcisi olarak görev alan kişiler. A kısmı veli "
    "listesini, B kısmı aday olan ve görev alan kişinin kaydını, C kısmı birliğe yazılan yazıları "
    "anlatır."
)
BOLUM_1_KISIMLARI: Final = (
    "A. Veli listesi",
    "B. Aday olan ve görev alan kişi",
    "C. Birliğe yazılan yazılar",
)
_B1_A_ISLENEN: Final = (
    "İşlenen veriler: Veli adı-soyadı şifreli tutulur. Genel kurulda velinin katıldığı toplantı, "
    "sayıma yardım için listedeki satırına işaretlenebilir."
)
_B1_A_TOPLAMA: Final = (
    f"{VELI_AYDINLATMA_TOPLAMA} Liste dosyadan kısmen otomatik yolla aktarılır. Katılım işareti genel "
    "kurulda programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak "
    "konur; hukuki sebebi de veri sorumlusunun hukuki yükümlülüğünü yerine getirmesidir (KVKK md. "
    "5/2-ç)."
)
_B1_A_AKTARIM: Final = (
    "Aktarım: Veli listesindeki veriler programdan kimseye aktarılmaz. İmzalı katılım cetveli genel "
    "kurul tutanak dosyasında durur (md. 23/1-a); bu dosya, birliğin denetimi için Bakanlık, valilik "
    "ve il/ilçe millî eğitim müdürlüğü denetim elemanlarına açıktır (md. 26/1)."
)
_B1_A_SAKLAMA: Final = (
    f"{VELI_AYDINLATMA_SAKLAMA} Velinin adını taşıyan sınıf teslim çizelgesini ve katılım cetvelini "
    "yalnız program yöneticisi (OAB'den sorumlu müdür yardımcısı) basar; program bu belgelerin "
    "dosyasını saklamaz, basım ise ad ve değer taşımadan erişim günlüğüne yazılır. İmzalı katılım "
    "cetveli genel kurul tutanak dosyasında saklanır (md. 23/1-a). Katılım işareti veli listesiyle "
    "birlikte silinir; ondan sonra programda genel kurula katılanların yalnız sayısı kalır."
)
_B1_B_AMAC: Final = (
    "divanın, yönetim kurulunun ve Denetleme Kurulunun oluşturulması (md. 10/1-c, 10/1-d, 11/1-a, "
    "11/1-b, 14/1);",
    "aday listesinin, genel kurul tutanağının ve yönetim kurulu kararı taslaklarının hazırlanması;",
    "görev ve iş bölümü, kurul toplantılarına katılım ve yedek üyenin göreve çağrılması (md. 12/3, "
    "13/3, 13/6);",
    "seçilme sınırının ve görev alma şartlarının izlenmesi (md. 12/4, 12/5, 14/3, 14/7);",
    "alım komisyonu üyelerinin kaydı (md. 18/1);",
    "birlik temsilcisinin kaydı: eğitim kampüsü yönetimi (md. 13/7), muhammen bedel tespit komisyonu "
    "(md. 19/1), kiralama ihale komisyonu (md. 20/3), il/ilçe millî eğitim müdürlüğü hesabındaki "
    "payları dağıtan komisyon (md. 17/1-b-3), Taşımacıyı Tespit Komisyonu (Usul ve Esaslar md. "
    "3/1-e); okulun öğrenci ödül ve disiplin kurulu, öğrenci davranışlarını değerlendirme kurulu, "
    "sosyal etkinlikler kurulu, kontenjan belirleme komisyonu, rehberlik ve psikolojik danışma "
    "hizmetleri yürütme komisyonu ve kantin denetim komisyonundaki birlik temsilcisi; yönetim kurulu "
    "kararıyla görevlendirilen öteki temsilciler;",
    "genel kurulda yönetim kurulu faaliyet raporunu ya da Denetleme Kurulu raporunu okuyan ve tahmini "
    "bütçeyi sunan kişinin tutanağa yazılması (md. 11/1-c, 11/1-d).",
)
_B1_B_ISLENEN_GIRISI: Final = "İşlenen veriler: Aday olan ve görev alan kişi için şunlar tutulur:"
_B1_B_ISLENEN: Final = (
    "ad-soyad;",
    "kişinin türü (veli, öğretmen, idareci, kursiyer, hayırsever ya da diğer) ve okuldaki bir "
    "öğrencinin velisi olup olmadığı;",
    "kursiyerde on sekiz yaşını doldurduğu beyanı (doğum tarihi tutulmaz);",
    "okul müdürü olup olmadığı;",
    "organ, görev, asıl ya da yedek koltuk, aldığı oy ve yedek sırası; temsilcide temsil edilen kurul "
    "ya da komisyon;",
    "göreve geliş yolu, görevin başlangıç ve bitiş günü, yedekten göreve çağrıldığı gün;",
    "yönetim kuruluna ve Denetleme Kurulu başkanlığına seçilme sayıları (programdan öncekiler kişinin "
    "beyanıyla);",
    "kurul toplantılarına katılıp katılmadığı; katılmadıysa bunun özürlü sayılıp sayılmadığı (özrün "
    "nedeni tutulmaz);",
    "başka okuldan görevlendirilen öğretmen üyede il/ilçe millî eğitim müdürlüğü onayının sayısı; "
    "başka kurumda görevlendirilen öğretmen üyenin görevlendirme günleri;",
    "görevin sona erme türü ve gerekçesi; öğrencisi okuldan ayrılan velinin olağanüstü genel kurula "
    "kadar görevde kaldığı (md. 7/2);",
    "görev almaya engel bir hâlin (md. 12/5, 14/7) bulunmadığına ve başka bir birliğin yönetiminde "
    "görev almadığına (md. 12/4) ilişkin beyanların okulca alındığı gün (beyanın içeriği tutulmaz);",
    "programdan önce başlamış görevin dayanak notu (seçildiği genel kurulun günü ve görev bölümü "
    "kararının defter sıra no'su) ve yanlış girilen kaydın iptal gerekçesi;",
    "genel kurulda raporu okuyan ya da tahmini bütçeyi sunan kişi olduğu.",
)
_B1_B_ENGEL: Final = (
    "Görev alma engeli tespit edilirse engelin bulunduğu ve tespit günü tutulur; engelin dayanağı "
    "(suç engeli ya da başka birlik yönetiminde görev) şifreli tutulur, adli sicil içeriği tutulmaz. "
    "Ad-soyad, dayanak notu, sona erme gerekçesi ve iptal gerekçesi şifreli tutulur. Telefon, adres "
    "ve T.C. kimlik no tutulmaz."
)
_B1_B_TOPLAMA: Final = (
    "Toplama yöntemi ve hukuki sebep: Bilgiler birliğin yetkili kullanıcılarınca programa elle, "
    "otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak girilir. Kaynakları: kişinin "
    "adaylık bildirimi, genel kurul tutanağı, yönetim kurulu kararları ve okulun aldığı beyanlar. Kişi "
    "kaydı veli listesinden ya da personel listesinden de açılabilir. Hukuki sebep: veri sorumlusunun "
    "hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç); yükümlülüğün kaynağı OAB Yönetmeliği md. "
    "7/2, 10/1, 11/1-a, 11/1-b, 12/3-5, 13/6, 13/7, 14/1-7, 17/1-b-3, 18/1, 19/1, 20/3 ve Usul ve "
    "Esaslar md. 3/1-e ile temsil edilen kurulun kendi mevzuatıdır. Görev alma engelinin dayanağı "
    "ceza mahkûmiyetine ilişkin olabileceği için özel nitelikli kişisel veridir (KVKK md. 6/1); "
    f"{OZEL_NITELIKLI_SARTI}"
)
#: Yeni yönetim kurulunun TEFBİS'e girilmesi: md. 23/5 çapasız, uygulama olarak (soru 6).
TEFBIS_YONETIM_CUMLESI: Final = (
    "Yeni yönetim kurulunun bilgileri, uygulamada, genel kuruldan sonra okul idaresince Bakanlığın "
    "merkezî bilgi sistemine (TEFBİS) girilir."
)
_B1_B_AKTARIM: Final = (
    GONDERMEZ,
    "Adınız, birliğin kayıtlarının tutulması için birliğin kâğıt evrakında yer alır: aday listesi ve "
    "genel kurul tutanağı (md. 23/1-a), yönetim kurulu karar defteri (md. 13/5, 23/1-b).",
    "Genel kurulun sonucunun okul müdürlüğünce bilinmesi için genel kurul sonuç bildirimi okul "
    "müdürlüğüne verilir.",
    TEFBIS_YONETIM_CUMLESI,
    "Hesaplar ibra edilmezse bu durum, yeni yönetim kurulu ve okul yönetimince il/ilçe millî eğitim "
    "müdürlüğüne resmî yazıyla bildirilir (md. 11/1-ç).",
    DENETIME_ACIK,
)
_B1_B_SAKLAMA: Final = (
    "Aday olan ve görev alan kişinin adı ve görev kaydı birlik kaydıdır, silinmez; dayanak notu ve "
    "iptal gerekçesi de kayıtla kalır. Birliğin defter ve belgeleri, Devlet Arşiv Hizmetleri Hakkında "
    "Yönetmelikte öngörülen süreler kadar okulda saklanır (md. 16/7, 23/6).",
    "Programın ürettiği birlik evrakı (adınızın geçtiği aday listesi, tutanak ve kurul evrakı) "
    "programda şifreli olarak saklanır ve silinmez.",
    "Görevin sona erme gerekçesi ve görev alma engelinin dayanağı, üyeliğin bittiği birlik döneminin "
    "kapanışında boşaltılır; sona erme türü, engelin bulunduğu bilgisi ve tespit günü kalır.",
    "Hiçbir birlik kaydına bağlanmamış kişi kaydı birlik döneminin kapanışında silinir.",
    "Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine "
    "yazılır; izde ad yer almaz, engelin bulunduğu bilgisi gibi kişisiz değerler kalır. Görev alma "
    "engelinin dayanağının görüntülenmesi erişim günlüğüne yazılır; günlükte ad ve okunan değer yer "
    "almaz, günlük iki yıl sonra silinir.",
)


def _bolum_1() -> tuple[Satir, ...]:
    return (
        (BAS, bolum_basligi(1)),
        (PAR, BOLUM_1_KAPSAM),
        (PAR, VERI_SORUMLUSU_SATIRI),
        (BAS, BOLUM_1_KISIMLARI[0]),
        (PAR, VELI_AYDINLATMA_AMACI),
        (PAR, _B1_A_ISLENEN),
        (PAR, _B1_A_TOPLAMA),
        (PAR, _B1_A_AKTARIM),
        (PAR, _B1_A_SAKLAMA),
        (BAS, BOLUM_1_KISIMLARI[1]),
        (PAR, ETIKET_AMAC),
        *((MAD, m) for m in _B1_B_AMAC),
        (PAR, _B1_B_ISLENEN_GIRISI),
        *((MAD, m) for m in _B1_B_ISLENEN),
        (PAR, _B1_B_ENGEL),
        (PAR, _B1_B_TOPLAMA),
        (PAR, ETIKET_AKTARIM),
        *((MAD, m) for m in _B1_B_AKTARIM),
        (PAR, ETIKET_SAKLAMA),
        *((MAD, m) for m in _B1_B_SAKLAMA),
        (BAS, BOLUM_1_KISIMLARI[2]),
        (PAR, YAZI_KAYDI_TAMAMI),
        (PAR, f"{YEDEKLER_ETIKETI} {YEDEK_CUMLESI}"),
        *_haklar_ve_basvuru(),
    )


# ---------------------------------------------------------------------------
# 2. Personel
# ---------------------------------------------------------------------------
BOLUM_2_KAPSAM: Final = "Kapsam: okulun öğretmen, yönetici ve diğer personeli."
_B2_ISLENEN: Final = (
    "Personel listesindeki ad-soyad şifreli tutulur.",
    "Kaydı güncel tutmak için ayrıca personelin görevde ya da ayrılmış olduğu, ayrılış günü ve yeni "
    "personel listesinde bulunmadığı için ayrılış havuzuna girdiği gün tutulur.",
    "T.C. kimlik no, unvan, branş, telefon ve adres tutulmaz.",
    "Okul müdürünün adı, girilmişse, okul bilgilerinde şifresiz tutulur; birlik evrakının imza "
    "bloklarında, kurtarma anahtarı belgesinde ve birlik kişisinin okul müdürü olup olmadığının "
    "belirlenmesinde kullanılır.",
    "Birlik organında, alım komisyonunda ya da birlik temsilciliğinde görev alan personelin o göreve "
    'ilişkin verileri için "1. Veli ve üye" bölümünün B kısmı geçerlidir.',
)
_B2_TOPLAMA: Final = (
    f"{PERSONEL_AYDINLATMA_TOPLAMA} Liste dosyadan kısmen otomatik yolla aktarılır. Listede "
    "bulunmayan personel program yöneticisince (OAB'den sorumlu müdür yardımcısı) programa elle, "
    "otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak da girilir; ayrılış elle "
    "işaretlenir. Elle girilen kayıtta da hukuki sebep veri sorumlusunun hukuki yükümlülüğünü yerine "
    "getirmesidir (KVKK md. 5/2-ç)."
)
_B2_AKTARIM: Final = (
    f"{GONDERMEZ[:-1]}; personel listesi kimseye aktarılmaz.",
    "Adınızın geçtiği birlik evrakı (komisyon ve kurul evrakı, imza blokları) birlik dosyasında durur; "
    "bu evrak, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim "
    "elemanlarına açıktır (md. 26/1).",
)
_B2_SAKLAMA: Final = (
    PERSONEL_AYDINLATMA_SAKLAMA.removeprefix(SAKLAMA_ETIKETI),
    "Birlik kaydına bağı olmayan personel kaydı program yöneticisince daha önce de silinebilir; aynı "
    "kişiye ait iki kayıt birleştirilirse fazla kayıt silinir.",
    "Birlik kaydına bağlı personelin (organ, komisyon, imza bloğu) adı birlik kişi kaydında kalır "
    '("1. Veli ve üye", B kısmı).',
    "Programın ürettiği ve adınızın geçtiği birlik evrakı programda şifreli olarak saklanır ve "
    "silinmez.",
    "Aktarılan personel listesi dosyasının kendisi programda saklanmaz.",
    "Kaydınızdaki değişiklikler denetim izine yalnız değişen alanın adıyla yazılır; izde adınız ve "
    "değer yer almaz.",
)
YAZILAR_ETIKETI: Final = "Birliğe yazılan yazılar:"


def _bolum_2() -> tuple[Satir, ...]:
    return (
        (BAS, bolum_basligi(2)),
        (PAR, BOLUM_2_KAPSAM),
        (PAR, VERI_SORUMLUSU_SATIRI),
        (PAR, PERSONEL_AYDINLATMA_AMACI),
        (PAR, ETIKET_ISLENEN),
        *((MAD, m) for m in _B2_ISLENEN),
        (PAR, _B2_TOPLAMA),
        (PAR, ETIKET_AKTARIM),
        *((MAD, m) for m in _B2_AKTARIM),
        (PAR, ETIKET_SAKLAMA),
        *((MAD, m) for m in _B2_SAKLAMA),
        (PAR, f"{YAZILAR_ETIKETI} {YAZI_KAYDI_TAMAMI}"),
        (PAR, f"{YEDEKLER_ETIKETI} {YEDEK_CUMLESI}"),
        *_haklar_ve_basvuru(),
    )


# ---------------------------------------------------------------------------
# 3. İstekli, kiracı ve çalışan
# ---------------------------------------------------------------------------
#: Bölümün geçerlilik koşulu (soru 1): kantin F5, servis F6.
BOLUM_3_KOSULU: Final = (
    "Bu bölüm, programın kantin ve servis işleri kullanılmaya başlandığında geçerlidir."
)
BOLUM_3_KAPSAM: Final = (
    "Kapsam: kantin kiralamasına katılan istekliler ve kiracı (işletmeci); okul servis taşıma işine "
    "başvuran istekliler ve sözleşme imzalanan taşımacı; kiracının çalıştırdığı kişiler, servis "
    "şoförleri ve rehber personel. Bölüm gerçek kişiler içindir."
)
_B3_AMAC: Final[tuple[Satir, ...]] = (
    (
        MAD,
        "Kantin ve benzeri yerlerin kiralanmasında birliğe düşen işlerin yürütülmesi (OAB Yönetmeliği "
        "md. 19, 20, 21):",
    ),
    (ALT, "kiralamaya katılamayacak kişinin seçilmesinin önlenmesi (md. 20/8, 20/11);"),
    (
        ALT,
        "kira sözleşmesinin, kira bedelinin, yıllık artışın ve teminatın izlenmesi (md. 21; EK-2 "
        "Kiralama Sözleşmesi);",
    ),
    (
        ALT,
        "işletmecinin ve çalıştırdığı kişilerin belgelerinin birlikçe saklanması ve her yıl "
        "yenilenmesinin izlenmesi (md. 20/6, 20/7, 23/4).",
    ),
    (MAD, "Okul servis araçlarında:"),
    (ALT, "taşımacının tespiti ve sözleşme (Usul ve Esaslar md. 6-8, 10/1);"),
    (ALT, "şoför ve rehber personel belgelerinin izlenmesi (Usul ve Esaslar md. 9);"),
    (ALT, "sözleşme imzalanan taşımacıların ilanı (Usul ve Esaslar md. 10/3)."),
)
#: Banka hesap özetinden aktarılan hareketin karşı tarafı (tasarım §3.4 işleme envanteri; soru 10).
_B3_ISLENEN: Final = (
    "İstekli için: ad-soyad ya da unvan, varsa ticaret sicil numarası; tebligat adresi, telefon ve "
    "e-posta adresi; sunduğu belgelerin türü ve görüldüğü gün; elenmişse eleme nedeni ve açıklaması; "
    "seçilip seçilmediği; kantinde teklif ettiği bedel ve katılım engelinin bulunup bulunmadığı "
    "(engelin dayanağı — hısımlık ya da suç engeli — şifreli tutulur); serviste puanlama yapılırsa "
    "puanları.",
    "Kiracı ve taşımacı için ayrıca: sözleşmenin tarihleri, bedeli, yıllık artışları, teminatı ve "
    "ödemeleri; serviste güzergâh ve araç plakaları. Birliğin banka hesap özetinden aktarılan ödeme "
    "hareketlerinde karşı tarafın adı ve açıklama şifreli tutulur.",
    "Kiracının çalıştırdığı kişiler, şoför ve rehber personel için: ad-soyad ile teslim edilen "
    "belgenin türü (ör. adli sicil kaydı, sağlık raporu, hijyen eğitimi belgesi, sürücü belgesi), "
    "görüldüğü gün ve geçerlilik sonu.",
    "Belgelerin içeriği tutulmaz; belgenin taraması varsayılan olarak alınmaz.",
    "Gerçek kişinin vergi numarası ve T.C. kimlik no tutulmaz. Ad, iletişim bilgisi ve açıklamalar "
    "şifreli tutulur.",
    YAZI_KAYDI,
)
_B3_TOPLAMA: Final[tuple[Satir, ...]] = (
    (
        MAD,
        "Bilgiler programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak "
        "girilir. Kaynakları:",
    ),
    (
        ALT,
        "kantin isteklisinde, il/ilçe millî eğitim müdürlüğünün yürüttüğü kiralama sürecinin evrakı "
        "(md. 20/3);",
    ),
    (
        ALT,
        "servis isteklisinde, Taşımacıyı Tespit Komisyonuna teslim ettiği dosya (Usul ve Esaslar md. "
        "7/1);",
    ),
    (ALT, "kiracı ve taşımacıda, imzalanan sözleşme;"),
    (
        ALT,
        "çalışan, şoför ve rehber personelde, kiracının ya da taşımacının teslim ettiği belgeler;",
    ),
    (ALT, "yazışmada, gelen ya da giden yazı."),
    (MAD, "Ödemeler birliğin banka hesap özeti dosyasından kısmen otomatik yolla aktarılır."),
    (MAD, "Hukuki sebep:"),
    (
        ALT,
        "istekli, kiracı ve taşımacıda: sözleşmenin kurulması ve ifası (KVKK md. 5/2-c) ve veri "
        "sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç);",
    ),
    (
        ALT,
        "kiracının çalıştırdığı kişiler, şoför ve rehber personelde: veri sorumlusunun hukuki "
        "yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç; OAB Yönetmeliği md. 20/6, 20/7, 23/4 ve Usul "
        "ve Esaslar md. 9/1);",
    ),
    (
        ALT,
        "yazışmada: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç).",
    ),
    (
        MAD,
        "Katılım engelinin dayanağı ile adli sicil kaydının ve sağlık raporunun görüldüğüne ilişkin "
        "kayıt özel nitelikli kişisel veri olabilir (KVKK md. 6/1); " + OZEL_NITELIKLI_SARTI,
    ),
)
_B3_AKTARIM: Final = (
    GONDERMEZ,
    "Sözleşme imzalanan taşımacının bilgileri (adı ya da unvanı, araç plakası ve güzergâhı), Usul ve "
    "Esaslar md. 10/3'ün gereği olarak okul ilan panosunda ve okulun internet sayfasında yayımlanır. "
    "Telefon, adres ve T.C. kimlik no yayımlanmaz.",
    "Taşımacıyı Tespit Komisyonunun kararı, yürürlüğe girmesi için mahallî mülki idare amirinin "
    "onayına sunulur (Usul ve Esaslar md. 4/1, 8/5).",
    "Kira sözleşmesinin bir örneği, md. 21/5'in gereği olarak okul müdürlüğünce millî emlak birimine "
    "gönderilir.",
    "Kira gelirinin kaydı, birliğin mali kayıtlarının Bakanlığın merkezî bilgi sistemine işlenmesi "
    "için okul idaresince TEFBİS'e girilir (md. 23/5).",
    DENETIME_ACIK,
)
_B3_SAKLAMA: Final = (
    "İletişim bilgileri (adres, telefon, e-posta) birlik döneminin kapanışında boşaltılır: seçilmeyen "
    "isteklininki süreç sözleşmeyle ya da iptalle kapandıktan sonraki ilk kapanışta; kiracınınki ve "
    "taşımacınınki sözleşme sona erdikten sonraki ilk kapanışta. Ad ya da unvan tutanaklarda geçtiği "
    "için kalır.",
    "Katılım engelinin dayanağı ve eleme açıklaması, süreç kapandıktan sonraki ilk birlik dönemi "
    "kapanışında boşaltılır.",
    "Sözleşme, ödeme ve belge kayıtları (tür ve tarihler) ile gelen-giden evrak kaydı birlik "
    f"kaydıdır, silinmez. {ARSIV_SURESI}",
    "Belgelerin asıl kâğıdı birlik dosyasında saklanır (md. 23/4). Okul taramayı programa almayı "
    "seçerse tarama şifreli tutulur ve okulun belirlediği süre dolunca silinir.",
    "Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine "
    "yazılır; izde ad yer almaz. Katılım engelinin dayanağının görüntülenmesi erişim günlüğüne "
    "yazılır; günlükte ad ve okunan değer yer almaz, günlük iki yıl sonra silinir.",
    YEDEK_CUMLESI_ACILIMLI,
)


def _bolum_3() -> tuple[Satir, ...]:
    return (
        (BAS, bolum_basligi(3)),
        (PAR, BOLUM_3_KOSULU),
        (PAR, BOLUM_3_KAPSAM),
        (PAR, VERI_SORUMLUSU_SATIRI),
        (PAR, ETIKET_AMAC),
        *_B3_AMAC,
        (PAR, ETIKET_ISLENEN),
        *((MAD, m) for m in _B3_ISLENEN),
        (PAR, ETIKET_TOPLAMA),
        *_B3_TOPLAMA,
        (PAR, ETIKET_AKTARIM),
        *((MAD, m) for m in _B3_AKTARIM),
        (PAR, ETIKET_SAKLAMA),
        *((MAD, m) for m in _B3_SAKLAMA),
        *_haklar_ve_basvuru(),
    )


# ---------------------------------------------------------------------------
# 4. Bağışçı ve tedarikçi
# ---------------------------------------------------------------------------
#: Bölümün geçerlilik koşulu (soru 1): bağış ve gelir-gider F3, harcama F4.
BOLUM_4_KOSULU: Final = "Bu bölüm, programın bağış, gelir-gider ve harcama işleri kullanılmaya başlandığında geçerlidir."
BOLUM_4_KAPSAM: Final = (
    "Kapsam: birliğe ayni ya da nakdî bağış yapan ve birliğe mal ya da hizmet satan gerçek kişiler."
)
#: K9 açıkken basılan satırlar (‹Okulun ayarı açıkken:› öneki düşer; soru 11).
TCKN_AMAC: Final = "Bağışçının T.C. kimlik no'su, bağış kaydının TEFBİS'e girilmesi için işlenir."
TCKN_TUTULMAZ: Final = "T.C. kimlik no tutulmaz."
TCKN_VERI: Final = (
    "T.C. kimlik no yalnız bağış kaydında, şifreli tutulur; ekranda numaranın bir kısmı gizlenir, "
    "tamamını yalnız program yöneticisi (OAB'den sorumlu müdür yardımcısı) görür ve her görüntüleme "
    "erişim günlüğüne yazılır. Numara hiçbir çıktıya ve dışa aktarım dosyasına girmez."
)
#: Hukuki sebep teyit gelene kadar "………" (soru 11; basım uyarısı `UYARI_TCKN_HUKUKI_SEBEP`). Taslaktan
#: tek sapma (taslakta KVKK md. 5/2-ç); kullanıcı kararı bekleniyor (modül başlığı).
TCKN_HUKUKI_SEBEP: Final = f"T.C. kimlik no'da: {BOS};"
TCKN_AKTARIM: Final = (
    "T.C. kimlik no, bağış kaydının aynı sisteme işlenmesi için okul idaresince TEFBİS'e girilir; "
    "başka bir çıktıya ve dosyaya girmez."
)
TCKN_SAKLAMA: Final = (
    "T.C. kimlik no, TEFBİS'e girildikten sonra en geç birlik döneminin kapanışında silinir."
)
_B4_BAGIS: Final = (
    "bağışların kabulü ve kaydı (OAB Yönetmeliği md. 6/1-f, 16);",
    "makbuz koçanı yapraklarının kaydı (md. 16/3, 16/5);",
    "şartlı bağışın amacına uygun kullanılmasının izlenmesi (md. 16/4);",
    "nakde çevrilemeyen ayni bağışın belge karşılığında okul müdürlüğüne teslimi (md. 16/2).",
)
_B4_HARCAMA: Final = (
    "Mal ve hizmet alımlarında harcama dosyasının hazırlanması: okul yönetiminin yazılı talebi, "
    "yönetim kurulu kararı ve en az üç kişilik komisyon (md. 18/1); birlik başkanı ve muhasibin "
    "müşterek imzasıyla ödeme (md. 18/2); alınan taşınırın okul adına kaydı (md. 18/3); harcama "
    "belgelerinin yer aldığı dosya (md. 23/1-d, 23/1-e). Programın harcama dosyası ayrıca alım "
    "komisyonunun topladığı teklifleri ve malın ya da hizmetin teslim kaydını tutar."
)
_B4_GELIR_GIDER: Final = (
    "Gelir-gider kayıtlarının, gelir-gider defterine geçirilecek ve TEFBİS'e girilecek listelerinin "
    "hazırlanması (md. 23/1-ç, 23/5)."
)
_B4_BAGISCI: Final = (
    "Bağışçı için: ad-soyad (biliniyorsa; boş bırakılabilir), bağışın günü ve tutarı, ayni bağışta "
    "cinsi, miktarı ve takdir değeri, makbuz yaprağının ya da banka dekontunun numarası."
)
_B4_TEDARIKCI: Final = (
    "Tedarikçi için: ad-soyad ya da unvan, alım komisyonuna verdiği teklifin tutarı, fatura ya da "
    "gider pusulasının numarası, günü ve tutarı, ödemenin kaydı.",
    "Gerçek kişi tedarikçinin vergi numarası ve banka hesap numarası (IBAN) tutulmaz.",
    "Birliğin banka hesap özetinden aktarılan hareketlerde karşı tarafın adı ve açıklama şifreli "
    "tutulur.",
    YAZI_KAYDI,
)
_B4_TOPLAMA: Final = (
    "Mali kayıtlar muhasipçe, öteki bilgiler birliğin yetkili kullanıcılarınca programa elle, otomatik "
    "olmayan yolla ve programın kayıt sisteminin parçası olarak girilir. Kaynakları: makbuz koçanı, "
    "bağış alındı belgesi, ayni bağış teslim tutanağı, fatura, gider pusulası, alım komisyonuna "
    "verilen teklifler ve gelen ya da giden yazı.",
    "Banka hareketleri birliğin banka hesap özeti dosyasından kısmen otomatik yolla aktarılır.",
)
_B4_HUKUKI_BAGIS: Final = "bağışta ve yazışmada: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç);"
_B4_HUKUKI_TEDARIKCI: Final = (
    "tedarikçide: sözleşmenin kurulması ve ifası (KVKK md. 5/2-c) ve veri sorumlusunun hukuki "
    "yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç)."
)
_B4_TEFBIS: Final = (
    "Birliğin gelir ve gider kayıtları, birliğin mali kayıtlarının Bakanlığın merkezî bilgi sistemine "
    "işlenmesi için okul idaresince TEFBİS'e girilir (md. 23/5)."
)
#: Aylık bildirimde bağışçı adı yer almaz (soru 12; ‹…› işaretsiz basılır).
AYLIK_BILDIRIM_CUMLESI: Final = (
    "Birlik başkanının okul müdürüne aylık bildiriminde (md. 18/5) bağışçının adı yer almaz."
)
_B4_AKTARIM_SONU: Final = (
    "Tedarikçiye ödeme, ödemenin yapılması için birlik başkanı ve muhasibin müşterek imzasıyla "
    "birliğin bankasına verilen talimatla yapılır (md. 18/2).",
    "Nakde çevrilemeyen ayni bağışın teslim tutanağı, bağışın okula tesliminin belgelenmesi için okul "
    "müdürlüğüne verilir (md. 16/2).",
    AYLIK_BILDIRIM_CUMLESI,
    "Okul ilan panosunda ve internet sayfasında yapılan gelir-gider ve tahmini bütçe duyurularında "
    "(md. 13/9, 13/10) kişi adı yer almaz.",
    DENETIME_ACIK,
)
_B4_SAKLAMA_BASI: Final = (
    "Gelir-gider kayıtları, makbuz koçanları, harcama dosyaları ve gelen-giden evrak kaydı birlik "
    f"kaydıdır, silinmez. {ARSIV_SURESI}"
)
_B4_SAKLAMA_SONU: Final = (
    "Banka hesap özeti dosyasının kendisi programda saklanmaz.",
    "Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine "
    "yazılır; izde ad yer almaz.",
    YEDEK_CUMLESI,
)


def _bolum_4(*, k9_acik: bool) -> tuple[Satir, ...]:
    """K9 (soru 11): kapalıyken yalnız "T.C. kimlik no tutulmaz." satırı; açıkken amaç, veri, hukuki
    sebep ("………"), aktarım ve saklama satırları."""
    return (
        (BAS, bolum_basligi(4)),
        (PAR, BOLUM_4_KOSULU),
        (PAR, BOLUM_4_KAPSAM),
        (PAR, VERI_SORUMLUSU_SATIRI),
        (PAR, ETIKET_AMAC),
        (MAD, "Bağış işleri:"),
        *((ALT, m) for m in _B4_BAGIS),
        *(((MAD, TCKN_AMAC),) if k9_acik else ()),
        (MAD, _B4_HARCAMA),
        (MAD, _B4_GELIR_GIDER),
        (PAR, ETIKET_ISLENEN),
        (MAD, _B4_BAGISCI),
        (MAD, TCKN_VERI if k9_acik else TCKN_TUTULMAZ),
        *((MAD, m) for m in _B4_TEDARIKCI),
        (PAR, ETIKET_TOPLAMA),
        *((MAD, m) for m in _B4_TOPLAMA),
        (MAD, "Hukuki sebep:"),
        (ALT, _B4_HUKUKI_BAGIS),
        *(((ALT, TCKN_HUKUKI_SEBEP),) if k9_acik else ()),
        (ALT, _B4_HUKUKI_TEDARIKCI),
        (PAR, ETIKET_AKTARIM),
        (MAD, GONDERMEZ),
        (MAD, _B4_TEFBIS),
        *(((MAD, TCKN_AKTARIM),) if k9_acik else ()),
        *((MAD, m) for m in _B4_AKTARIM_SONU),
        (PAR, ETIKET_SAKLAMA),
        (MAD, _B4_SAKLAMA_BASI),
        *(((MAD, TCKN_SAKLAMA),) if k9_acik else ()),
        *((MAD, m) for m in _B4_SAKLAMA_SONU),
        *_haklar_ve_basvuru(),
    )


# ---------------------------------------------------------------------------
# Basım uyarıları (belgeye basılmaz; üretimin yanıtında ve kartta)
# ---------------------------------------------------------------------------
#: Onaylı ekran notu (soru 5): E04'e basılmaz, basım ekranında uyarıdır.
UYARI_HUKUKI_SEBEP_ONERI: Final = AYDINLATMA_EKRAN_NOTU
UYARI_OZEL_NITELIKLI_BENT: Final = (
    "Özel nitelikli kişisel verinin işleme şartı (KVKK md. 6/3'ün bendi) okul müdürlüğünce "
    "belirlenir; 1. ve 3. bölümde yeri ……… basıldı."
)
UYARI_TCKN_HUKUKI_SEBEP: Final = (
    "Bağışçının T.C. kimlik no'sunun hukuki sebebi okul müdürlüğünce teyit edilmedi; 4. bölümde "
    "yeri ……… basıldı."
)


def basim_uyarilari(*, k9_acik: bool) -> tuple[str, ...]:
    """Belgenin her basımında geçerli uyarılar (belgeye basılmaz)."""
    uyarilar = [UYARI_HUKUKI_SEBEP_ONERI, UYARI_OZEL_NITELIKLI_BENT]
    if k9_acik:
        uyarilar.append(UYARI_TCKN_HUKUKI_SEBEP)
    return tuple(uyarilar)


# ---------------------------------------------------------------------------
# Satırlar ve bloklar
# ---------------------------------------------------------------------------
def bolum_satirlari(no: int, *, k9_acik: bool) -> tuple[Satir, ...]:
    """Bölümün satırları (veri sorumlusu yer tutucusuyla)."""
    if no == 1:
        return _bolum_1()
    if no == 2:
        return _bolum_2()
    if no == 3:
        return _bolum_3()
    if no == 4:
        return _bolum_4(k9_acik=k9_acik)
    raise ValueError(no)


def bas_satirlari() -> tuple[Satir, ...]:
    """Belgenin başı (başlıktan sonra): giriş, bölümlerin listesi ve adlandırma."""
    return (
        (PAR, GIRIS),
        (PAR, BOLUMLER_GIRISI),
        *((PAR, f"{no}. {ad}") for no, ad in enumerate(BOLUM_ADLARI, start=1)),
        (PAR, ADLANDIRMA),
    )


def _blok(satir: Satir, veri_sorumlusu: str) -> evrak.Blok:
    tur, metin = satir
    metin = metin.replace(VERI_SORUMLUSU_YERI, veri_sorumlusu)
    if tur == BAS:
        return evrak.AltBaslik(metin)
    if tur == MAD:
        return evrak.Paragraf(f"{MADDE_IMI} {metin}")
    if tur == ALT:
        return evrak.Paragraf(f"{ALT_MADDE_IMI} {metin}")
    return evrak.Paragraf(metin)


def govde(veri_sorumlusu: str, *, k9_acik: bool) -> tuple[evrak.Blok, ...]:
    """Belgenin gövdesi (başlıktan sonra): baş, sonra dört bölüm; her bölüm yeni sayfada başlar (her
    bölüm kendi başına okunur, ayrı asılabilir). `veri_sorumlusu` boş olamaz (kurucu denetler)."""
    if not veri_sorumlusu.strip():
        raise ValueError(veri_sorumlusu)
    bloklar: list[evrak.Blok] = [_blok(s, veri_sorumlusu) for s in bas_satirlari()]
    for no in range(1, len(BOLUM_ADLARI) + 1):
        bloklar.append(evrak.SayfaSonu())
        bloklar.extend(_blok(s, veri_sorumlusu) for s in bolum_satirlari(no, k9_acik=k9_acik))
    return tuple(bloklar)
