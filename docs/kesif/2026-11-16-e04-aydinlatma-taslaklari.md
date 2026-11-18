# E04 kişisel veri aydınlatma metni — dört alt metnin taslağı (onaylı)

*16.11.2026 · F2 planı [§9 S8 (i)](../plan/2026-11-15-f2-plani.md)*

**Onaylandı (16.11.2026): kullanıcı dört alt metni ve 20 sorunun varsayılanlarını onayladı** (kendi sözüyle
"Varsayılanlarla onayla"). Basılacak tam metin F2 planının 10. adımının son işinde koda harfi harfine kuruldu
(`backend/apps/oab/services/aydinlatma_metni.py`; ‹…› işaretlerinin varsayılanlarla çözülüşü modülün başlığında,
birebirlik `test_e04_metni_onayli_taslakla_harfi_harfine` testinde). Tek istisna: soru 11'in açık biçimdeki hukuki sebep satırı (4. bölüm) "KVKK md. 5/2-ç" yerine "………" ve basım uyarısıyla basılır; bu, varsayılanın uygulamadaki yorumudur, kullanıcı kararı değildir ve kullanıcıya sorulacaktır (F2 planı 10. adımın E04 notu). Ayar alanı F3'te gelir; o güne dek açık biçim basılmaz. Soru 7'nin varsayılanıyla Aydınlatma Tebliği OAB
korpusuna kopyalandı; aşağıdaki "Tb" atıfları ona çevrildi. "T:n", "P:n" ve `dosya:satır` atıfları taslağın yazıldığı
günün (commit `1f02508`) satır numaralarıdır; sonraki değişikliklerle kayabilir.

Bu belge E04 "Kişisel veri aydınlatma metni"nin dört alt metnini (veli ve üye · personel · istekli, kiracı ve çalışan ·
bağışçı ve tedarikçi) basılacak biçimiyle onaya sunar: F2 planı §9 S8 (i) bu onayı 10. adımdan (E04'ün kurucusu) önce
ister. Taslak bağımsız bir denetimden geçti; 31 bulgu kaynağıyla tek tek sınandı, işlendi ya da gerekçesiyle kısmen
reddedildi (belgenin sonunda). Metindeki işaretler: **`{data_controller_text}`** Okul Bilgileri'ndeki veri sorumlusu
alanının değeridir; "Veri sorumlusu:" etiketinin yanına basılır, alan boşken E04 basılmaz (plan §9 S6 (iv), tasarım
KE-20). **‹…›** koşullu ya da karar bekleyen parçadır; koşulu yanında yazar ve "Kullanıcıya sorulacak" listesinde
karşılığı vardır. **"………"** cevabı okul müdürlüğünden beklenen satırdır; o hâliyle basılırsa basım uyarısı verilir.
08.11.2026'da onaylanan cümleler (`frontend/src/modules/kisiler/metinler.ts:39-91`) tek harf değişmeden korundu; her
bölümün "Dayanaklar" kısmı hangilerinin onaylı olduğunu söyler. Metin, programın bugün (F2) gerçekten tuttuğu alanlara
(`backend/apps/okul/models.py`, `backend/apps/oab/models/`) dayanır; kodda henüz olmayan kantin, servis, bağış ve harcama
verisi için genel tasarımın veri modeline (§5) ve işleme envanterine (§3.4) dayanır. Her veri cümlesi modeldeki bir
alana bağlıdır; metin fazlasını ya da eksiğini söylemez. Konum cümlesi ve müdür bloğu yoktur (plan §2
`ev::test_konum_tfb` satırı; tasarım §9.6 E04'ü imzasız tanımlar).

Atıf kısaltmaları (yalnız bu belgede; basılan metne girmez): **K** = [6698 KVKK](../mevzuat/6698-kvkk.md) ·
**Y** = [OAB Yönetmeliği](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md) · **UE** =
[Servis Usul ve Esaslar](../mevzuat/okul-servisi-calistirma-usul-esaslari.md) · **Tb** = [Aydınlatma Tebliği](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md)
(soru 7: Kütüphane korpusundaki teyitli metin 16.11.2026'da değiştirilmeden kopyalandı) · **T:n** = [genel tasarım](../tasarim/2026-10-31-genel-tasarim.md) satır n · **P:n** =
[F2 planı](../plan/2026-11-15-f2-plani.md) satır n. Kod atıfları depo köküne göre `dosya:satır` biçimindedir.

---

## 0. Belgenin başı (dört bölüme ortak)

### Basılacak tam metin

KİŞİSEL VERİ AYDINLATMA METNİ

Okul-aile birliğinin işlerinde işlenen kişisel veriler · 6698 sayılı Kişisel Verileri Koruma Kanunu (KVKK) md. 10

Okul-aile birliğinin işleri, okulun bilgisayarında çalışan OAB Defteri programıyla yürütülür. Program kişisel veriyi
internete, buluta ya da başka bir kuruma göndermez. Bu metin, birliğin işlerinde kişisel verisi işlenen kişileri KVKK
md. 10/1 gereği bilgilendirir.

Metin dört bölümdür ve her bölüm kendi başına okunur:

1. Veli ve üye
2. Personel
3. İstekli, kiracı ve çalışan
4. Bağışçı ve tedarikçi

Metinde "OAB Yönetmeliği", Millî Eğitim Bakanlığı Okul-Aile Birliği Yönetmeliğidir; başında başka bir mevzuatın adı
yazılmayan "md." atıfları bu Yönetmeliğindir. "Usul ve Esaslar", Okul Servis Araçlarının Çalıştırılmasına İlişkin Usul
ve Esaslardır.

### Dayanaklar

| Cümle | Dayanak |
|---|---|
| Başlık, alt başlık, giriş | [K md. 10/1](../mevzuat/6698-kvkk.md#madde-10) (`6698-kvkk.md:82`); T:3169, T:3291 (dört alt metin); P:214 |
| "Program kişisel veriyi … göndermez" | Onaylı aktarım cümlesinin "dışarıya veri göndermez" sözünden daraltıldı: güncelleme denetimi kullanıcının düğmesiyle `api.github.com`'a, kurucu indirmesi `github.com`'a istek atar, kişisel veri taşımaz (`backend/apps/okul/services/updates.py:1-18`, `:57`) |
| "OAB Yönetmeliği" ve yalın "md." | `docs/sozluk.md` giriş paragrafı ("Yalın 'md.' atıfları … Okul-Aile Birliği Yönetmeliğidir"); öteki mevzuatın atfı her yerde adıyla başlar (KVKK md. …, Usul ve Esaslar md. …) |
| "Usul ve Esaslar" açılımı | UE başlığı ve [UE md. 1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-1) |
| Veri sorumlusu satırı (her bölümde) | [K md. 10/1-a](../mevzuat/6698-kvkk.md#madde-10); `backend/apps/okul/models.py:162-166, 281`; T:1447; P:642 (S6-iv: boşken basılmaz). Veri sorumlusu temsilcisi yalnız Türkiye'de yerleşik olmayan veri sorumlusu için doğar ([Tb md. 3/1-ğ](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-3), `:49`); okul ve birlik için ayrı yer tutucu gerekmez |
| Usul denetimi (bütün bölümler) | [Tb md. 4](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-4), [Tb md. 5/1-g, h, ı, i, j](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) (`:89-99`) |

---

## 1. Veli ve üye

### Basılacak tam metin

1. VELİ VE ÜYE

Kapsam: veliler; yönetim kuruluna ve Denetleme Kuruluna aday olan ve seçilen kişiler; genel kurul divanında, alım
komisyonunda ve birlik temsilcisi olarak görev alan kişiler. A kısmı veli listesini, B kısmı aday olan ve görev alan
kişinin kaydını, C kısmı birliğe yazılan yazıları anlatır.

Veri sorumlusu: {data_controller_text}

**A. Veli listesi**

Amaç: Genel kurul toplantısının daveti, katılım cetveli ve toplantı yeter sayısının sayımı (OAB Yönetmeliği md. 9/2,
9/3, 10/1-a); birlik organlarına aday olan velinin kaydı. Yalnız veli adı-soyadı ve öğrencinin sınıfı tutulur; telefon,
adres, T.C. kimlik no ve öğrencinin adı tutulmaz.

İşlenen veriler: Veli adı-soyadı şifreli tutulur. Genel kurulda velinin katıldığı toplantı, sayıma yardım için listedeki
satırına işaretlenebilir.

Toplama yöntemi ve hukuki sebep: Okul idaresinin hazırladığı listeden elektronik ortamda aktarılır. Hukuki sebep: veri
sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç). Liste dosyadan kısmen otomatik yolla aktarılır.
Katılım işareti genel kurulda programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak konur;
hukuki sebebi de veri sorumlusunun hukuki yükümlülüğünü yerine getirmesidir (KVKK md. 5/2-ç).

Aktarım: Veli listesindeki veriler programdan kimseye aktarılmaz. İmzalı katılım cetveli genel kurul tutanak dosyasında
durur (md. 23/1-a); bu dosya, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim
elemanlarına açıktır (md. 26/1).

Saklama: Liste birlik döneminin kapanışında silinir; genel kuruldan sonra daha önce de silinebilir. Velinin adını
taşıyan sınıf teslim çizelgesini ve katılım cetvelini yalnız program yöneticisi (OAB'den sorumlu müdür yardımcısı)
basar; program bu belgelerin dosyasını saklamaz, basım ise ad ve değer taşımadan erişim günlüğüne yazılır. İmzalı
katılım cetveli genel kurul tutanak dosyasında saklanır (md. 23/1-a). Katılım işareti veli listesiyle birlikte silinir;
ondan sonra programda genel kurula katılanların yalnız sayısı kalır.

**B. Aday olan ve görev alan kişi**

Amaç:

- divanın, yönetim kurulunun ve Denetleme Kurulunun oluşturulması (md. 10/1-c, 10/1-d, 11/1-a, 11/1-b, 14/1);
- aday listesinin, genel kurul tutanağının ve yönetim kurulu kararı taslaklarının hazırlanması;
- görev ve iş bölümü, kurul toplantılarına katılım ve yedek üyenin göreve çağrılması (md. 12/3, 13/3, 13/6);
- seçilme sınırının ve görev alma şartlarının izlenmesi (md. 12/4, 12/5, 14/3, 14/7);
- alım komisyonu üyelerinin kaydı (md. 18/1);
- birlik temsilcisinin kaydı: eğitim kampüsü yönetimi (md. 13/7), muhammen bedel tespit komisyonu (md. 19/1), kiralama
  ihale komisyonu (md. 20/3), il/ilçe millî eğitim müdürlüğü hesabındaki payları dağıtan komisyon (md. 17/1-b-3),
  Taşımacıyı Tespit Komisyonu (Usul ve Esaslar md. 3/1-e); okulun öğrenci ödül ve disiplin kurulu, öğrenci davranışlarını
  değerlendirme kurulu, sosyal etkinlikler kurulu, kontenjan belirleme komisyonu, rehberlik ve psikolojik danışma
  hizmetleri yürütme komisyonu ve kantin denetim komisyonundaki birlik temsilcisi; yönetim kurulu kararıyla
  görevlendirilen öteki temsilciler;
- genel kurulda yönetim kurulu faaliyet raporunu ya da Denetleme Kurulu raporunu okuyan ve tahmini bütçeyi sunan kişinin
  tutanağa yazılması (md. 11/1-c, 11/1-d).

İşlenen veriler: Aday olan ve görev alan kişi için şunlar tutulur:

- ad-soyad;
- kişinin türü (veli, öğretmen, idareci, kursiyer, hayırsever ya da diğer) ve okuldaki bir öğrencinin velisi olup
  olmadığı;
- kursiyerde on sekiz yaşını doldurduğu beyanı (doğum tarihi tutulmaz);
- okul müdürü olup olmadığı;
- organ, görev, asıl ya da yedek koltuk, aldığı oy ve yedek sırası; temsilcide temsil edilen kurul ya da komisyon;
- göreve geliş yolu, görevin başlangıç ve bitiş günü, yedekten göreve çağrıldığı gün;
- yönetim kuruluna ve Denetleme Kurulu başkanlığına seçilme sayıları (programdan öncekiler kişinin beyanıyla);
- kurul toplantılarına katılıp katılmadığı; katılmadıysa bunun özürlü sayılıp sayılmadığı (özrün nedeni tutulmaz);
- başka okuldan görevlendirilen öğretmen üyede il/ilçe millî eğitim müdürlüğü onayının sayısı; başka kurumda
  görevlendirilen öğretmen üyenin görevlendirme günleri;
- görevin sona erme türü ve gerekçesi; öğrencisi okuldan ayrılan velinin olağanüstü genel kurula kadar görevde kaldığı
  (md. 7/2);
- görev almaya engel bir hâlin (md. 12/5, 14/7) bulunmadığına ve başka bir birliğin yönetiminde görev almadığına
  (md. 12/4) ilişkin beyanların okulca alındığı gün (beyanın içeriği tutulmaz);
- programdan önce başlamış görevin dayanak notu (seçildiği genel kurulun günü ve görev bölümü kararının defter sıra
  no'su) ve yanlış girilen kaydın iptal gerekçesi;
- genel kurulda raporu okuyan ya da tahmini bütçeyi sunan kişi olduğu.

Görev alma engeli tespit edilirse engelin bulunduğu ve tespit günü tutulur; engelin dayanağı (suç engeli ya da başka
birlik yönetiminde görev) şifreli tutulur, adli sicil içeriği tutulmaz. Ad-soyad, dayanak notu, sona erme gerekçesi ve
iptal gerekçesi şifreli tutulur. Telefon, adres ve T.C. kimlik no tutulmaz.

Toplama yöntemi ve hukuki sebep: Bilgiler birliğin yetkili kullanıcılarınca programa elle, otomatik olmayan yolla ve
programın kayıt sisteminin parçası olarak girilir. Kaynakları: kişinin adaylık bildirimi, genel kurul tutanağı, yönetim
kurulu kararları ve okulun aldığı beyanlar. Kişi kaydı veli listesinden ya da personel listesinden de açılabilir.
Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç); yükümlülüğün kaynağı OAB
Yönetmeliği md. 7/2, 10/1, 11/1-a, 11/1-b, 12/3-5, 13/6, 13/7, 14/1-7, 17/1-b-3, 18/1, 19/1, 20/3 ve Usul ve Esaslar
md. 3/1-e ile temsil edilen kurulun kendi mevzuatıdır. Görev alma engelinin dayanağı ceza mahkûmiyetine ilişkin
olabileceği için özel nitelikli kişisel veridir (KVKK md. 6/1); işleme şartı: KVKK md. 6/3'ün ……… bendi.

Aktarım:

- Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez.
- Adınız, birliğin kayıtlarının tutulması için birliğin kâğıt evrakında yer alır: aday listesi ve genel kurul tutanağı
  (md. 23/1-a), yönetim kurulu karar defteri (md. 13/5, 23/1-b).
- Genel kurulun sonucunun okul müdürlüğünce bilinmesi için genel kurul sonuç bildirimi okul müdürlüğüne verilir.
- ‹Yeni yönetim kurulunun bilgileri, uygulamada, genel kuruldan sonra okul idaresince Bakanlığın merkezî bilgi
  sistemine (TEFBİS) girilir.›
- Hesaplar ibra edilmezse bu durum, yeni yönetim kurulu ve okul yönetimince il/ilçe millî eğitim müdürlüğüne resmî
  yazıyla bildirilir (md. 11/1-ç).
- Birliğin kayıtları, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim elemanlarına
  açıktır (md. 26/1).

Saklama:

- Aday olan ve görev alan kişinin adı ve görev kaydı birlik kaydıdır, silinmez; dayanak notu ve iptal gerekçesi de
  kayıtla kalır. Birliğin defter ve belgeleri, Devlet Arşiv Hizmetleri Hakkında Yönetmelikte öngörülen süreler kadar
  okulda saklanır (md. 16/7, 23/6).
- Programın ürettiği birlik evrakı (adınızın geçtiği aday listesi, tutanak ve kurul evrakı) programda şifreli olarak
  saklanır ve silinmez.
- Görevin sona erme gerekçesi ve görev alma engelinin dayanağı, üyeliğin bittiği birlik döneminin kapanışında
  boşaltılır; sona erme türü, engelin bulunduğu bilgisi ve tespit günü kalır.
- Hiçbir birlik kaydına bağlanmamış kişi kaydı birlik döneminin kapanışında silinir.
- Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine yazılır; izde ad yer
  almaz, engelin bulunduğu bilgisi gibi kişisiz değerler kalır. Görev alma engelinin dayanağının görüntülenmesi erişim
  günlüğüne yazılır; günlükte ad ve okunan değer yer almaz, günlük iki yıl sonra silinir.

**C. Birliğe yazılan yazılar**

Birliğe yazdığınız ya da birliğin size yazdığı yazı, gelen-giden evrak defterinin tutulması için (md. 23/1-c) programın
gelen-giden evrak kaydına girer: karşı taraf olarak adınız, yazının konusu ve varsa taranmış örneği şifreli tutulur.
Kayıt programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak girilir. Hukuki sebep: veri
sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç). Kayıt birlik kaydıdır, silinmez; birliğin denetimi
için md. 26/1'deki denetim elemanlarına açıktır.

**Yedekler:** Silinen ya da boşaltılan veri, programın bilgisayardaki şifreli yedeklerinde ‹günlük yedeklerde en çok
14 gün, güncelleme öncesi yedeklerde son beş güncelleme boyunca› kalır. Program yöneticisinin kaydettiği şifreli dış
yedeklerde (ör. USB bellek) veri, yedeğin okulca saklandığı süre boyunca kalır.

Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi isteme, düzeltilmesini ya da
silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak kullanabilirsiniz. Haklarınızın tamamı şunlardır:

- kişisel verinizin işlenip işlenmediğini öğrenme;
- işlenmişse buna ilişkin bilgi isteme;
- işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme;
- yurt içinde ya da yurt dışında aktarıldığı üçüncü kişileri bilme;
- eksik ya da yanlış işlenmişse düzeltilmesini isteme;
- KVKK md. 7'deki şartlarla silinmesini ya da yok edilmesini isteme;
- düzeltme ve silmenin, verinin aktarıldığı üçüncü kişilere bildirilmesini isteme;
- yalnız otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz etme;
- kanuna aykırı işleme yüzünden zarara uğrarsanız zararın giderilmesini isteme.

Başvuru: Başvurunuzu yukarıda adı geçen veri sorumlusuna yazıyla ya da Kişisel Verileri Koruma Kurulunun belirlediği
öteki yöntemlerle iletebilirsiniz (KVKK md. 13/1). Başvuru, niteliğine göre en kısa sürede ve en geç otuz gün içinde
ücretsiz sonuçlandırılır; işlem ayrıca bir maliyet gerektirirse Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki
ücret alınabilir (KVKK md. 13/2). Başvurunuz reddedilir, verilen cevap yetersiz bulunur ya da süresinde cevap verilmezse,
cevabı öğrendiğiniz günden başlayarak otuz gün içinde, her durumda başvuru gününden başlayarak altmış gün içinde
Kişisel Verileri Koruma Kuruluna şikâyette bulunabilirsiniz (KVKK md. 14/1).

### Dayanaklar

**Onaylı cümleler (08.11.2026, birebir):** A'nın "Amaç", "Toplama yöntemi ve hukuki sebep" ve "Saklama" satırlarının
ilk cümleleri ile "Haklarınız"ın ilk cümlesi: `frontend/src/modules/kisiler/metinler.ts:62-76, 84-87`; E07'deki
karşılıkları `backend/apps/oab/services/genel_kurul_evraki.py:452-463`.

| Cümle | Dayanak |
|---|---|
| Kapsam | [Y md. 8/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-8) (organlar yalnız genel kurul, yönetim kurulu, Denetleme Kurulu; `:127`); [Y md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) (divan); [Y md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); `backend/apps/oab/models/_base.py:85-92` (organ ve görev kanalları) |
| A — işlenen veriler | `backend/apps/okul/models.py:869` (veli adı şifreli), `:833-838, 882-895` (katılım işareti, isteğe bağlı sayım yardımı); T:312 |
| A — toplama, katılım işareti | `backend/apps/oab/services/genel_kurul.py:2677-2700`; [Tb md. 5/1-i](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) (yöntem sınıfı) |
| A — aktarım | [Y md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [Y md. 26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26) (`:427`); [Tb md. 5/1-ı](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| A — saklama | T:1726-1727 (R9; dosya saklanmaz, katılım işareti listeyle silinir, sayılar kalır); `backend/apps/oab/models/evrak.py:25-28` (veli adlı belgede içerik ve dosya yok); `backend/apps/okul/models.py:1561` (`VELI_LISTESI_CIKTISI` erişim günlüğü türü); "program yöneticisi" etiketi `docs/sozluk.md` "Program yöneticisi ve roller" satırı |
| B — amaç | [Y md. 10/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [12](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [13/3, 13/6, 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (`:210, 212`), [14](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [17/1-b-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [UE md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) (`:77`); öteki kurulların çapaları tasarımdadır ve korpusta vardır: [OKY md. 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OÖİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57), [SEY md. 6](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6), [OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25), [RPD Yön. md. 16](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16), [Genelge 2020/8 A-1/a](../mevzuat/okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md#bolum-a-1-a) (T:1479-1483); `backend/apps/oab/models/_base.py:158-183` (temsil türleri, `DIGER` dâhil); `backend/apps/oab/models/genel_kurul.py:814-836` (raporu okuyan, bütçeyi sunan) |
| B — işlenen veriler | `backend/apps/oab/models/kisi.py:75-104` (tür, ad şifreli, veli, 18 yaş beyanı, müdür, önceki seçilme sayıları); `backend/apps/oab/models/uyelik.py:169-269` (koltuk, oy, yedek sırası, kanal, `evidence_note` :198 şifreli, `mem_approval_no` :212, görevlendirme günleri, `promoted_on` :226, sona erme türü ve gerekçesi, beyan günleri :240-241, engel ve dayanağı :245-257, `retained_until_assembly` :259, `chair_elections`, `cancel_reason` :267 şifreli); `backend/apps/oab/models/kurul.py:227-259` ("Özrün nedeni tutulmaz"; `excused`); `backend/apps/oab/models/_base.py:233-244` (engel ve dayanağın iki değeri); [Y md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7), [Y md. 14/1, 14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| B — toplama ve hukuki sebep | `backend/apps/oab/services/kisiler.py:161, 227, 266` (elle, personelden, veli listesinden); [K md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5) (`:50`); T:311 (envanter önerisi); [Tb md. 5/1-h, i](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| B — özel nitelikli | [K md. 6/1, 6/3](../mevzuat/6698-kvkk.md#madde-6) (`:56`); T:350-358, T:4409 (B-16, DOĞRULANMADI); `backend/apps/oab/models/uyelik.py:249-256` |
| B — aktarım | [Y md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [Y md. 23/1-a, b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); E13 sonuç bildirimi: T:3178 (açık hüküm yok, okul uygulaması); TEFBİS yönetim bilgisi: `backend/apps/oab/services/genel_kurul.py:3455-3461`, T:1599, T:2423 (süresi yalnız GNL-OAB-RH-001'de; [Y md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) lafzı yalnız mali kayıtları anar, `:402` — bu yüzden çapasız, soru 6); [Y md. 11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11); [Y md. 26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26) |
| B — saklama | T:1724, T:1729-1732; [Y md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); `backend/apps/oab/models/evrak.py:1-9, 150, 286-288` (içerik şifreli, kayıt silinmez); `backend/apps/oab/models/uyelik.py:84-112, 153` (izdeki değer alanları; yalnız gerekçe ve dayanak boşaltılır); `backend/apps/okul/models.py:1418-1446` (denetim izi ekleme-yalnız), `:1566, 1605` (erişim günlüğü, değer tutmaz); `backend/apps/okul/erisim_gunlugu.py:120` (`SAKLAMA_SURESI_YIL = 2`; T:1738 B-9 DOĞRULANMADI) |
| C | [Y md. 23/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) (`:386`); `backend/apps/oab/models/evrak.py:292-298, 343-344` (karşı taraf ve konu şifreli, kayıt silinmez); `backend/apps/oab/services/gelen_giden_evrak.py:245, 343` (kayıt ve taranmış ek); md. 9/6 üye başvurusu bu kayda girer, başvuranların listesi tutulmaz (`backend/apps/oab/models/genel_kurul.py:365, 383-385`) |
| Yedekler | `desktop/backup.py:42-47, 118-119` (`DEFAULT_KEEP_DAYS = 14`, `DEFAULT_KEEP_PRE_MIGRATE = 5`); `backend/apps/okul/services/encrypted_backup.py:1-6` (tam şifreli dış yedek, yeri kullanıcı seçer); T:1770 |
| Haklarınız | [K md. 11/1 a-ğ](../mevzuat/6698-kvkk.md#madde-11) (`:88`), [K md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Başvuru | [K md. 13/1-2](../mevzuat/6698-kvkk.md#madde-13) (`:102`), [K md. 14/1](../mevzuat/6698-kvkk.md#madde-14) (`:108`) |

### Onayınıza sunulan seçimler

- Bölüm iki (C ile üç) kısma ayrıldı: onaylı "Yalnız veli adı-soyadı ve öğrencinin sınıfı tutulur" cümlesi yalnız veli
  listesine bağlanır; aday ve görevli verisi B'de ayrı sayılır.
- Onaylı "Haklarınız" cümlesi korundu, ardından hakların tamamı "Haklarınızın tamamı şunlardır:" girişiyle sayıldı
  (tekrar bilinçlidir; soru 17).
- Özel nitelikli verinin işleme şartı "………" ile basılır ve basım uyarısı verilir (soru 4).
- TEFBİS yönetim bilgisi satırı md. 23/5 çapası olmadan, uygulama olarak ‹…› içinde (soru 6).

---

## 2. Personel

### Basılacak tam metin

2. PERSONEL

Kapsam: okulun öğretmen, yönetici ve diğer personeli.

Veri sorumlusu: {data_controller_text}

Amaç: Okul-aile birliğinin işlerinde öğretmen ve yöneticilerin adının kullanılması: Denetleme Kuruluna öğretmen üyelerin
seçimi (OAB Yönetmeliği md. 14/1), mal ve hizmet alım komisyonu (md. 18/1) ve birlik evrakının imza blokları. Yalnız
ad-soyad ve görev türü (öğretmen, yönetici, diğer personel) tutulur.

İşlenen veriler:

- Personel listesindeki ad-soyad şifreli tutulur.
- Kaydı güncel tutmak için ayrıca personelin görevde ya da ayrılmış olduğu, ayrılış günü ve yeni personel listesinde
  bulunmadığı için ayrılış havuzuna girdiği gün tutulur.
- T.C. kimlik no, unvan, branş, telefon ve adres tutulmaz.
- Okul müdürünün adı, girilmişse, okul bilgilerinde şifresiz tutulur; birlik evrakının imza bloklarında, kurtarma
  anahtarı belgesinde ve birlik kişisinin okul müdürü olup olmadığının belirlenmesinde kullanılır.
- Birlik organında, alım komisyonunda ya da birlik temsilciliğinde görev alan personelin o göreve ilişkin verileri için
  "1. Veli ve üye" bölümünün B kısmı geçerlidir.

Toplama yöntemi ve hukuki sebep: e-Okul personel listesinden okul idaresince elektronik ortamda aktarılır. Hukuki sebep:
veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç). Liste dosyadan kısmen otomatik yolla
aktarılır. Listede bulunmayan personel program yöneticisince (OAB'den sorumlu müdür yardımcısı) programa elle, otomatik
olmayan yolla ve programın kayıt sisteminin parçası olarak da girilir; ayrılış elle işaretlenir. Elle girilen kayıtta da
hukuki sebep veri sorumlusunun hukuki yükümlülüğünü yerine getirmesidir (KVKK md. 5/2-ç).

Aktarım:

- Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez; personel listesi kimseye aktarılmaz.
- Adınızın geçtiği birlik evrakı (komisyon ve kurul evrakı, imza blokları) birlik dosyasında durur; bu evrak, birliğin
  denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim elemanlarına açıktır (md. 26/1).

Saklama:

- Okuldan ayrılan ve birlik kaydına bağı olmayan personelin kaydı, ayrılışı izleyen dönem kapanışında silinir.
- Birlik kaydına bağı olmayan personel kaydı program yöneticisince daha önce de silinebilir; aynı kişiye ait iki kayıt
  birleştirilirse fazla kayıt silinir.
- Birlik kaydına bağlı personelin (organ, komisyon, imza bloğu) adı birlik kişi kaydında kalır ("1. Veli ve üye",
  B kısmı).
- Programın ürettiği ve adınızın geçtiği birlik evrakı programda şifreli olarak saklanır ve silinmez.
- Aktarılan personel listesi dosyasının kendisi programda saklanmaz.
- Kaydınızdaki değişiklikler denetim izine yalnız değişen alanın adıyla yazılır; izde adınız ve değer yer almaz.

Birliğe yazılan yazılar: Birliğe yazdığınız ya da birliğin size yazdığı yazı, gelen-giden evrak defterinin tutulması
için (md. 23/1-c) programın gelen-giden evrak kaydına girer: karşı taraf olarak adınız, yazının konusu ve varsa taranmış
örneği şifreli tutulur. Kayıt programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak girilir.
Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç). Kayıt birlik kaydıdır,
silinmez; birliğin denetimi için md. 26/1'deki denetim elemanlarına açıktır.

Yedekler: Silinen ya da boşaltılan veri, programın bilgisayardaki şifreli yedeklerinde ‹günlük yedeklerde en çok 14 gün,
güncelleme öncesi yedeklerde son beş güncelleme boyunca› kalır. Program yöneticisinin kaydettiği şifreli dış yedeklerde
(ör. USB bellek) veri, yedeğin okulca saklandığı süre boyunca kalır.

Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi isteme, düzeltilmesini ya da
silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak kullanabilirsiniz. Haklarınızın tamamı şunlardır:

- kişisel verinizin işlenip işlenmediğini öğrenme;
- işlenmişse buna ilişkin bilgi isteme;
- işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme;
- yurt içinde ya da yurt dışında aktarıldığı üçüncü kişileri bilme;
- eksik ya da yanlış işlenmişse düzeltilmesini isteme;
- KVKK md. 7'deki şartlarla silinmesini ya da yok edilmesini isteme;
- düzeltme ve silmenin, verinin aktarıldığı üçüncü kişilere bildirilmesini isteme;
- yalnız otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz etme;
- kanuna aykırı işleme yüzünden zarara uğrarsanız zararın giderilmesini isteme.

Başvuru: Başvurunuzu yukarıda adı geçen veri sorumlusuna yazıyla ya da Kişisel Verileri Koruma Kurulunun belirlediği
öteki yöntemlerle iletebilirsiniz (KVKK md. 13/1). Başvuru, niteliğine göre en kısa sürede ve en geç otuz gün içinde
ücretsiz sonuçlandırılır; işlem ayrıca bir maliyet gerektirirse Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki
ücret alınabilir (KVKK md. 13/2). Başvurunuz reddedilir, verilen cevap yetersiz bulunur ya da süresinde cevap verilmezse,
cevabı öğrendiğiniz günden başlayarak otuz gün içinde, her durumda başvuru gününden başlayarak altmış gün içinde
Kişisel Verileri Koruma Kuruluna şikâyette bulunabilirsiniz (KVKK md. 14/1).

### Dayanaklar

**Onaylı cümleler (08.11.2026, birebir):** "Amaç", "Toplama yöntemi ve hukuki sebep" satırının ilk iki cümlesi,
"Saklama"nın ilk maddesi ve "Haklarınız"ın ilk cümlesi: `frontend/src/modules/kisiler/metinler.ts:42-55, 84-87`.

| Cümle | Dayanak |
|---|---|
| İşlenen veriler (liste) | `backend/apps/okul/models.py:594-656` (ad şifreli; unvan ve branş yok; `is_active`, `left_at` :647, `leave_candidate_since` :648); T:313 |
| Okul müdürünün adı | `backend/apps/okul/models.py:143-146, 246` (okul kartı alanı, şifrelenmez, isteğe bağlı); `backend/apps/oab/services/gorev_evraki.py:778`; `backend/apps/okul/services/recovery_key_document.py:118`; `backend/apps/oab/services/kisiler.py:150-154` (müdür eşleşmesi) |
| Birlik görevine gönderme | `backend/apps/oab/models/kisi.py:89-96` (personel bağı); T:311 |
| Toplama (elle giriş, ayrılış) | `backend/apps/okul/views.py:202-237` (yalnız program yöneticisi, `RequiresAdminPassword`); [Tb md. 5/1-i](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Aktarım | [Y md. 26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26) |
| Saklama — erken silme ve birleştirme | `backend/apps/okul/views.py:217-231`; `backend/apps/okul/services/persons.py:390-416` (`delete_personnel` yalnız bağsız kayıtta, `merge_personnel` kaynağı siler); T:1731 |
| Saklama — evrak, liste dosyası, iz | `backend/apps/oab/models/evrak.py:1-9, 286-288`; `backend/apps/okul/models.py:707-760` (aktarım koşusu yalnız SHA256 tutar), `:604-616` (personelde izde değer yok, ad MAC dışı); T:1736 |
| Birliğe yazılan yazılar, Yedekler, Haklarınız, Başvuru | 1. bölümün C, Yedekler, Haklarınız ve Başvuru satırları |

### Onayınıza sunulan seçimler

- Onaylı "Yalnız ad-soyad ve görev türü … tutulur" cümlesi korundu; kaydın durum alanları ve okul müdürünün adı
  "İşlenen veriler"de ayrıca sayıldı (soru 2).
- Okul müdürünün adı bu bölümde anıldı (müdür okul personelidir); ayrı bir alt metin açılmadı.

---

## 3. İstekli, kiracı ve çalışan

### Basılacak tam metin

3. İSTEKLİ, KİRACI VE ÇALIŞAN

‹Bu bölüm, programın kantin ve servis işleri kullanılmaya başlandığında geçerlidir.›

Kapsam: kantin kiralamasına katılan istekliler ve kiracı (işletmeci); okul servis taşıma işine başvuran istekliler ve
sözleşme imzalanan taşımacı; kiracının çalıştırdığı kişiler, servis şoförleri ve rehber personel. Bölüm gerçek kişiler
içindir.

Veri sorumlusu: {data_controller_text}

Amaç:

- Kantin ve benzeri yerlerin kiralanmasında birliğe düşen işlerin yürütülmesi (OAB Yönetmeliği md. 19, 20, 21):
  - kiralamaya katılamayacak kişinin seçilmesinin önlenmesi (md. 20/8, 20/11);
  - kira sözleşmesinin, kira bedelinin, yıllık artışın ve teminatın izlenmesi (md. 21; EK-2 Kiralama Sözleşmesi);
  - işletmecinin ve çalıştırdığı kişilerin belgelerinin birlikçe saklanması ve her yıl yenilenmesinin izlenmesi
    (md. 20/6, 20/7, 23/4).
- Okul servis araçlarında:
  - taşımacının tespiti ve sözleşme (Usul ve Esaslar md. 6-8, 10/1);
  - şoför ve rehber personel belgelerinin izlenmesi (Usul ve Esaslar md. 9);
  - sözleşme imzalanan taşımacıların ilanı (Usul ve Esaslar md. 10/3).

İşlenen veriler:

- İstekli için: ad-soyad ya da unvan, varsa ticaret sicil numarası; tebligat adresi, telefon ve e-posta adresi;
  sunduğu belgelerin türü ve görüldüğü gün; elenmişse eleme nedeni ve açıklaması; seçilip seçilmediği; kantinde
  teklif ettiği bedel ve katılım engelinin bulunup bulunmadığı (engelin dayanağı — hısımlık ya da suç engeli — şifreli
  tutulur); serviste puanlama yapılırsa puanları.
- Kiracı ve taşımacı için ayrıca: sözleşmenin tarihleri, bedeli, yıllık artışları, teminatı ve ödemeleri; serviste
  güzergâh ve araç plakaları. Birliğin banka hesap özetinden aktarılan ödeme hareketlerinde karşı tarafın adı ve
  açıklama şifreli tutulur.
- Kiracının çalıştırdığı kişiler, şoför ve rehber personel için: ad-soyad ile teslim edilen belgenin türü (ör. adli
  sicil kaydı, sağlık raporu, hijyen eğitimi belgesi, sürücü belgesi), görüldüğü gün ve geçerlilik sonu.
- Belgelerin içeriği tutulmaz; belgenin taraması varsayılan olarak alınmaz.
- Gerçek kişinin vergi numarası ve T.C. kimlik no tutulmaz. Ad, iletişim bilgisi ve açıklamalar şifreli tutulur.
- Birliğe yazdığınız ya da birliğin size yazdığı yazı, gelen-giden evrak defterinin tutulması için (md. 23/1-c)
  programın gelen-giden evrak kaydına girer: karşı taraf olarak adınız, yazının konusu ve varsa taranmış örneği şifreli
  tutulur.

Toplama yöntemi ve hukuki sebep:

- Bilgiler programa elle, otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak girilir. Kaynakları:
  - kantin isteklisinde, il/ilçe millî eğitim müdürlüğünün yürüttüğü kiralama sürecinin evrakı (md. 20/3);
  - servis isteklisinde, Taşımacıyı Tespit Komisyonuna teslim ettiği dosya (Usul ve Esaslar md. 7/1);
  - kiracı ve taşımacıda, imzalanan sözleşme;
  - çalışan, şoför ve rehber personelde, kiracının ya da taşımacının teslim ettiği belgeler;
  - yazışmada, gelen ya da giden yazı.
- Ödemeler birliğin banka hesap özeti dosyasından kısmen otomatik yolla aktarılır.
- Hukuki sebep:
  - istekli, kiracı ve taşımacıda: sözleşmenin kurulması ve ifası (KVKK md. 5/2-c) ve veri sorumlusunun hukuki
    yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç);
  - kiracının çalıştırdığı kişiler, şoför ve rehber personelde: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi
    (KVKK md. 5/2-ç; OAB Yönetmeliği md. 20/6, 20/7, 23/4 ve Usul ve Esaslar md. 9/1);
  - yazışmada: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç).
- Katılım engelinin dayanağı ile adli sicil kaydının ve sağlık raporunun görüldüğüne ilişkin kayıt özel nitelikli
  kişisel veri olabilir (KVKK md. 6/1); işleme şartı: KVKK md. 6/3'ün ……… bendi.

Aktarım:

- Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez.
- Sözleşme imzalanan taşımacının bilgileri (adı ya da unvanı, araç plakası ve güzergâhı), Usul ve Esaslar md. 10/3'ün
  gereği olarak okul ilan panosunda ve okulun internet sayfasında yayımlanır. Telefon, adres ve T.C. kimlik no
  yayımlanmaz.
- Taşımacıyı Tespit Komisyonunun kararı, yürürlüğe girmesi için mahallî mülki idare amirinin onayına sunulur (Usul ve
  Esaslar md. 4/1, 8/5).
- Kira sözleşmesinin bir örneği, md. 21/5'in gereği olarak okul müdürlüğünce millî emlak birimine gönderilir.
- Kira gelirinin kaydı, birliğin mali kayıtlarının Bakanlığın merkezî bilgi sistemine işlenmesi için okul idaresince
  TEFBİS'e girilir (md. 23/5).
- Birliğin kayıtları, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim elemanlarına
  açıktır (md. 26/1).

Saklama:

- İletişim bilgileri (adres, telefon, e-posta) birlik döneminin kapanışında boşaltılır: seçilmeyen isteklininki süreç
  sözleşmeyle ya da iptalle kapandıktan sonraki ilk kapanışta; kiracınınki ve taşımacınınki sözleşme sona erdikten
  sonraki ilk kapanışta. Ad ya da unvan tutanaklarda geçtiği için kalır.
- Katılım engelinin dayanağı ve eleme açıklaması, süreç kapandıktan sonraki ilk birlik dönemi kapanışında boşaltılır.
- Sözleşme, ödeme ve belge kayıtları (tür ve tarihler) ile gelen-giden evrak kaydı birlik kaydıdır, silinmez. Birliğin
  defter ve belgeleri Devlet Arşiv Hizmetleri Hakkında Yönetmelikte öngörülen süreler kadar okulda saklanır (md. 16/7,
  23/6).
- Belgelerin asıl kâğıdı birlik dosyasında saklanır (md. 23/4). Okul taramayı programa almayı seçerse tarama şifreli
  tutulur ve okulun belirlediği süre dolunca silinir.
- Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine yazılır; izde ad yer
  almaz. Katılım engelinin dayanağının görüntülenmesi erişim günlüğüne yazılır; günlükte ad ve okunan değer yer almaz,
  günlük iki yıl sonra silinir.
- Silinen ya da boşaltılan veri, programın bilgisayardaki şifreli yedeklerinde ‹günlük yedeklerde en çok 14 gün,
  güncelleme öncesi yedeklerde son beş güncelleme boyunca› kalır. Program yöneticisinin (OAB'den sorumlu müdür
  yardımcısı) kaydettiği şifreli dış yedeklerde (ör. USB bellek) veri, yedeğin okulca saklandığı süre boyunca kalır.

Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi isteme, düzeltilmesini ya da
silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak kullanabilirsiniz. Haklarınızın tamamı şunlardır:

- kişisel verinizin işlenip işlenmediğini öğrenme;
- işlenmişse buna ilişkin bilgi isteme;
- işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme;
- yurt içinde ya da yurt dışında aktarıldığı üçüncü kişileri bilme;
- eksik ya da yanlış işlenmişse düzeltilmesini isteme;
- KVKK md. 7'deki şartlarla silinmesini ya da yok edilmesini isteme;
- düzeltme ve silmenin, verinin aktarıldığı üçüncü kişilere bildirilmesini isteme;
- yalnız otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz etme;
- kanuna aykırı işleme yüzünden zarara uğrarsanız zararın giderilmesini isteme.

Başvuru: Başvurunuzu yukarıda adı geçen veri sorumlusuna yazıyla ya da Kişisel Verileri Koruma Kurulunun belirlediği
öteki yöntemlerle iletebilirsiniz (KVKK md. 13/1). Başvuru, niteliğine göre en kısa sürede ve en geç otuz gün içinde
ücretsiz sonuçlandırılır; işlem ayrıca bir maliyet gerektirirse Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki
ücret alınabilir (KVKK md. 13/2). Başvurunuz reddedilir, verilen cevap yetersiz bulunur ya da süresinde cevap verilmezse,
cevabı öğrendiğiniz günden başlayarak otuz gün içinde, her durumda başvuru gününden başlayarak altmış gün içinde
Kişisel Verileri Koruma Kuruluna şikâyette bulunabilirsiniz (KVKK md. 14/1).

### Dayanaklar

Bu bölümün modelleri F2 kodunda yoktur (kantin F5, servis F6; T:4305-4306); veri cümleleri tasarımın veri modeline
dayanır. Onaylı cümle: yalnız "Haklarınız"ın ilk cümlesi (`frontend/src/modules/kisiler/metinler.ts:84-87`).

| Cümle | Dayanak |
|---|---|
| Amaç — kantin | [Y md. 19](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [20/3, 20/6-8, 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) (`:311-334`), [21](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) (`:400`); [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md) |
| Amaç — servis | [UE md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6), [7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7), [8](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9) (`:168`), [10](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) (`:195`) |
| İşlenen veriler | T:1626 (`Bidder`: iletişim şifreli, gerçek kişide vergi no tutulmaz, engel dayanağı `HISIMLIK_20_8` · `SUC_20_11`), T:3963 (`BidderScore`), T:1627 (`BidderDocument`: tür, görüldü, geçerlilik, tarama isteğe bağlı), T:1629 (`OabContract`), T:1559 (banka hareketinin karşı tarafı), T:1692-1693 (şifreli alanlar); T:316-318 |
| Gelen-giden evrak | [Y md. 23/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); `backend/apps/oab/models/evrak.py:292-298, 343-344` |
| Toplama | T:333; [UE md. 7/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7); T:1558-1559; [Tb md. 5/1-i](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Hukuki sebep | [K md. 5/2-c, ç](../mevzuat/6698-kvkk.md#madde-5) (5/2-c yalnız sözleşmenin taraflarına ait veri içindir; çalışan, şoför ve rehber sözleşmenin tarafı değildir); [Y md. 20/6-7, 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) (`:325, 400`); [UE md. 9/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9); T:316; [Tb md. 5/1-h](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Özel nitelikli | [K md. 6](../mevzuat/6698-kvkk.md#madde-6); T:317-318, T:4409 (B-16) |
| Aktarım | [UE md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) ("taşımacıların bilgileri … ilan panolarında ve web sitesinde yayınlanır"; içerik T:371-375 D5, T:3343); [UE md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) (`:91`), [UE md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [Y md. 21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) (`:348`); [Y md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) (`:402`); [Y md. 26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26); [Tb md. 5/1-ı](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Saklama | T:1724, T:1733-1735; [Y md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/4, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); `backend/apps/okul/models.py:1566` (`OZEL_NITELIKLI_ALAN`: kantin isteklisinin katılım engeli dayanağı) |
| Yedekler, Haklarınız, Başvuru | 1. bölümdeki satırlar |

### Onayınıza sunulan seçimler

- Bölüm, kantin ve servis işleri kullanılmaya başlandığında geçerlidir koşuluyla basılır (soru 1).
- Hukuki sebep üç gruba ayrıldı; çalışan, şoför ve rehber personel için yalnız KVKK md. 5/2-ç gösterildi.
- Şoför ve rehber personelin doğum tarihi sayılmadı (soru 9).

---

## 4. Bağışçı ve tedarikçi

### Basılacak tam metin

4. BAĞIŞÇI VE TEDARİKÇİ

‹Bu bölüm, programın bağış, gelir-gider ve harcama işleri kullanılmaya başlandığında geçerlidir.›

Kapsam: birliğe ayni ya da nakdî bağış yapan ve birliğe mal ya da hizmet satan gerçek kişiler.

Veri sorumlusu: {data_controller_text}

Amaç:

- Bağış işleri:
  - bağışların kabulü ve kaydı (OAB Yönetmeliği md. 6/1-f, 16);
  - makbuz koçanı yapraklarının kaydı (md. 16/3, 16/5);
  - şartlı bağışın amacına uygun kullanılmasının izlenmesi (md. 16/4);
  - nakde çevrilemeyen ayni bağışın belge karşılığında okul müdürlüğüne teslimi (md. 16/2).
- ‹Okulun ayarı açıkken:› bağışçının T.C. kimlik no'su, bağış kaydının TEFBİS'e girilmesi için işlenir.
- Mal ve hizmet alımlarında harcama dosyasının hazırlanması: okul yönetiminin yazılı talebi, yönetim kurulu kararı ve en
  az üç kişilik komisyon (md. 18/1); birlik başkanı ve muhasibin müşterek imzasıyla ödeme (md. 18/2); alınan taşınırın
  okul adına kaydı (md. 18/3); harcama belgelerinin yer aldığı dosya (md. 23/1-d, 23/1-e). Programın harcama dosyası
  ayrıca alım komisyonunun topladığı teklifleri ve malın ya da hizmetin teslim kaydını tutar.
- Gelir-gider kayıtlarının, gelir-gider defterine geçirilecek ve TEFBİS'e girilecek listelerinin hazırlanması (md. 23/1-ç,
  23/5).

İşlenen veriler:

- Bağışçı için: ad-soyad (biliniyorsa; boş bırakılabilir), bağışın günü ve tutarı, ayni bağışta cinsi, miktarı ve takdir
  değeri, makbuz yaprağının ya da banka dekontunun numarası.
- ‹Okulun ayarı kapalıyken:› T.C. kimlik no tutulmaz.
- ‹Okulun ayarı açıkken:› T.C. kimlik no yalnız bağış kaydında, şifreli tutulur; ekranda numaranın bir kısmı gizlenir,
  tamamını yalnız program yöneticisi (OAB'den sorumlu müdür yardımcısı) görür ve her görüntüleme erişim günlüğüne
  yazılır. Numara hiçbir çıktıya ve dışa aktarım dosyasına girmez.
- Tedarikçi için: ad-soyad ya da unvan, alım komisyonuna verdiği teklifin tutarı, fatura ya da gider pusulasının
  numarası, günü ve tutarı, ödemenin kaydı.
- Gerçek kişi tedarikçinin vergi numarası ve banka hesap numarası (IBAN) tutulmaz.
- Birliğin banka hesap özetinden aktarılan hareketlerde karşı tarafın adı ve açıklama şifreli tutulur.
- Birliğe yazdığınız ya da birliğin size yazdığı yazı, gelen-giden evrak defterinin tutulması için (md. 23/1-c)
  programın gelen-giden evrak kaydına girer: karşı taraf olarak adınız, yazının konusu ve varsa taranmış örneği şifreli
  tutulur.

Toplama yöntemi ve hukuki sebep:

- Mali kayıtlar muhasipçe, öteki bilgiler birliğin yetkili kullanıcılarınca programa elle, otomatik olmayan yolla ve
  programın kayıt sisteminin parçası olarak girilir. Kaynakları: makbuz koçanı, bağış alındı belgesi, ayni bağış teslim
  tutanağı, fatura, gider pusulası, alım komisyonuna verilen teklifler ve gelen ya da giden yazı.
- Banka hareketleri birliğin banka hesap özeti dosyasından kısmen otomatik yolla aktarılır.
- Hukuki sebep:
  - bağışta ve yazışmada: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç);
  - ‹okulun ayarı açıkken, T.C. kimlik no'da: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç)›;
  - tedarikçide: sözleşmenin kurulması ve ifası (KVKK md. 5/2-c) ve veri sorumlusunun hukuki yükümlülüğünü yerine
    getirmesi (KVKK md. 5/2-ç).

Aktarım:

- Program kişisel veriyi internete, buluta ya da başka bir kuruma göndermez.
- Birliğin gelir ve gider kayıtları, birliğin mali kayıtlarının Bakanlığın merkezî bilgi sistemine işlenmesi için okul
  idaresince TEFBİS'e girilir (md. 23/5).
- ‹Okulun ayarı açıkken:› T.C. kimlik no, bağış kaydının aynı sisteme işlenmesi için okul idaresince TEFBİS'e girilir;
  başka bir çıktıya ve dosyaya girmez.
- Tedarikçiye ödeme, ödemenin yapılması için birlik başkanı ve muhasibin müşterek imzasıyla birliğin bankasına verilen
  talimatla yapılır (md. 18/2).
- Nakde çevrilemeyen ayni bağışın teslim tutanağı, bağışın okula tesliminin belgelenmesi için okul müdürlüğüne verilir
  (md. 16/2).
- ‹Birlik başkanının okul müdürüne aylık bildiriminde (md. 18/5) bağışçının adı yer almaz.›
- Okul ilan panosunda ve internet sayfasında yapılan gelir-gider ve tahmini bütçe duyurularında (md. 13/9, 13/10) kişi
  adı yer almaz.
- Birliğin kayıtları, birliğin denetimi için Bakanlık, valilik ve il/ilçe millî eğitim müdürlüğü denetim elemanlarına
  açıktır (md. 26/1).

Saklama:

- Gelir-gider kayıtları, makbuz koçanları, harcama dosyaları ve gelen-giden evrak kaydı birlik kaydıdır, silinmez.
  Birliğin defter ve belgeleri Devlet Arşiv Hizmetleri Hakkında Yönetmelikte öngörülen süreler kadar okulda saklanır
  (md. 16/7, 23/6).
- ‹Okulun ayarı açıkken:› T.C. kimlik no, TEFBİS'e girildikten sonra en geç birlik döneminin kapanışında silinir.
- Banka hesap özeti dosyasının kendisi programda saklanmaz.
- Kayıtlardaki değişiklikler, değişikliği yapan hesapla birlikte silinmeyen bir denetim izine yazılır; izde ad yer
  almaz.
- Silinen ya da boşaltılan veri, programın bilgisayardaki şifreli yedeklerinde ‹günlük yedeklerde en çok 14 gün,
  güncelleme öncesi yedeklerde son beş güncelleme boyunca› kalır. Program yöneticisinin kaydettiği şifreli dış
  yedeklerde (ör. USB bellek) veri, yedeğin okulca saklandığı süre boyunca kalır.

Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi isteme, düzeltilmesini ya da
silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak kullanabilirsiniz. Haklarınızın tamamı şunlardır:

- kişisel verinizin işlenip işlenmediğini öğrenme;
- işlenmişse buna ilişkin bilgi isteme;
- işlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme;
- yurt içinde ya da yurt dışında aktarıldığı üçüncü kişileri bilme;
- eksik ya da yanlış işlenmişse düzeltilmesini isteme;
- KVKK md. 7'deki şartlarla silinmesini ya da yok edilmesini isteme;
- düzeltme ve silmenin, verinin aktarıldığı üçüncü kişilere bildirilmesini isteme;
- yalnız otomatik sistemlerle analiz edilmesi sonucunda aleyhinize bir sonuç çıkmasına itiraz etme;
- kanuna aykırı işleme yüzünden zarara uğrarsanız zararın giderilmesini isteme.

Başvuru: Başvurunuzu yukarıda adı geçen veri sorumlusuna yazıyla ya da Kişisel Verileri Koruma Kurulunun belirlediği
öteki yöntemlerle iletebilirsiniz (KVKK md. 13/1). Başvuru, niteliğine göre en kısa sürede ve en geç otuz gün içinde
ücretsiz sonuçlandırılır; işlem ayrıca bir maliyet gerektirirse Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki
ücret alınabilir (KVKK md. 13/2). Başvurunuz reddedilir, verilen cevap yetersiz bulunur ya da süresinde cevap verilmezse,
cevabı öğrendiğiniz günden başlayarak otuz gün içinde, her durumda başvuru gününden başlayarak altmış gün içinde
Kişisel Verileri Koruma Kuruluna şikâyette bulunabilirsiniz (KVKK md. 14/1).

### Dayanaklar

Bu bölümün modelleri F2 kodunda yoktur (bağış ve gelir-gider F3, harcama F4; T:4303-4304). Onaylı cümle: yalnız
"Haklarınız"ın ilk cümlesi (`frontend/src/modules/kisiler/metinler.ts:84-87`).

| Cümle | Dayanak |
|---|---|
| Amaç — bağış | [Y md. 6/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [Y md. 16/2-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) (`:263`) |
| Amaç — T.C. kimlik no (ayar açık) | T:74 (K9), T:314 (envanter: "TEFBİS girişi"), T:2901 (numarayı yonetici TEFBİS'e girer; ayar açıkken yalnız ekranda, maskesiz yalnız yonetici rolüne ve erişim günlüğüyle). TEFBİS'in numarayı istediği korpusta DOĞRULANMADI (soru 11) |
| Amaç — harcama | [Y md. 18/1-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) (`:287`), [Y md. 23/1-d, e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23). "Teklif" ve "teslim kaydı" mevzuat hükmü değil, programın uygulamasıdır: T:1590 (`ExpenseFile` teslim, E26), T:1592 (`ExpenseQuote`, denetim EK-12); "piyasa araştırması" sözü korpusta yoktur, metne girmedi |
| Amaç — gelir-gider | [Y md. 23/1-ç, 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); T:3183 |
| İşlenen veriler | T:1561 (`LedgerEntry`: bağışçı adı şifreli ve isteğe bağlı, ayni bağış), T:3308 (E21); T:1590, T:1592 (tedarikçi: vergi no yalnız tüzelde, IBAN tutulmaz); T:1559, T:1687 (banka hareketinin karşı tarafı); T:1708 (maskeli, maskesiz gösterim yalnız yonetici rolünde ve erişim günlüğüyle; maskenin biçimi tasarımda tanımlı değil) |
| Gelen-giden evrak | [Y md. 23/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); `backend/apps/oab/models/evrak.py:292-298, 343-344` |
| Toplama | CLAUDE.md K2 (mali kaydı yalnız muhasip girer); T:1558; [Tb md. 5/1-i](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Hukuki sebep | [K md. 5/2-c, ç](../mevzuat/6698-kvkk.md#madde-5); T:314-315 |
| Aktarım | [Y md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) (`:402`); T:2901 (T.C. kimlik no'nun TEFBİS'e girilmesi); [Y md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [Y md. 16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [Y md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) (`:295`) ve T:1598 ("Bağışçı adları varsayılan olarak dökümde yoktur"); [Y md. 13/9-10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), T:371-372 (duyuruda kişi adı yok; CLAUDE.md altın kural 5); [Y md. 26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26); [Tb md. 5/1-ı](../mevzuat/kvkk-aydinlatma-yukumlulugu-tebligi.md#madde-5) |
| Saklama | T:1724, T:1728, T:1736; [Y md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Yedekler, Haklarınız, Başvuru | 1. bölümdeki satırlar |

### Onayınıza sunulan seçimler

- Bölüm, bağış, gelir-gider ve harcama işleri kullanılmaya başlandığında geçerlidir koşuluyla basılır (soru 1).
- T.C. kimlik no'nun iki biçimi: ayar kapalıyken yalnız "tutulmaz" satırı, ayar açıkken amaç, veri, hukuki sebep,
  aktarım ve saklama satırları birlikte basılır; hangisinin basılacağı okulun ayarından okunur (soru 11).
- Harcama dosyasının teklif ve teslim kaydı mevzuat çapası olmadan programın uygulaması olarak yazıldı (soru 19).

---

## Kullanıcıya sorulacak

Her satırın sonundaki "varsayılan", cevap gelene kadar uygulanacak en dar seçimdir.

1. 3. ve 4. bölümün verisi F2 kodunda yok (kantin F5, servis F6, bağış F3, harcama F4); varsayılan: dördü bugün onaylanır ve 3 ile 4 "kullanılmaya başlandığında geçerlidir" koşuluyla basılır (plan §4.1 ve `ev::test_e04_dort_alt_metin_veri_sorumlusu_bossa_basilmaz` korunur), seçenek F2'de yalnız 1 ve 2'nin basılmasıdır.
2. Onaylı "Yalnız veli adı-soyadı ve öğrencinin sınıfı tutulur" ve "Yalnız ad-soyad ve görev türü … tutulur" cümleleri katılım işaretini ve personelin ayrılış alanlarını saymıyor; varsayılan: cümleler değişmez, E04'te alt başlık ve ek cümleyle kapsam daraltılır, seçenek iki cümleye "veli listesinde" ve "personel listesinde" sözünün eklenmesidir (E07 ve aktarım ekranları da değişir).
3. Onaylı ortak "Kişisel veriler kimseye aktarılmaz" cümlesi E04'te her bölümün alıcılarıyla yeniden yazıldı; varsayılan: aktarım ekranlarının ve hesap teslim pusulasının onaylı cümlesi olduğu gibi kalır.
4. Görev alma engelinin dayanağı, kantin isteklisinin katılım engelinin dayanağı ve adli sicil ile sağlık belgesinin "görüldü" kaydı için KVKK md. 6/3'ün hangi bendine dayanıldığını okul müdürlüğü belirler; varsayılan: satır "………" ile basılır ve basım uyarısı verilir, seçenek dayanak alanının hiç tutulmaması (yalnız "engel var/yok"; tasarım değişikliği) olur.
5. Ekran notu ("Hukuki sebep öneridir; …") E04'e basılsın mı; varsayılan: basılmaz, E04'ün basım ekranında uyarı olarak kalır.
6. Yeni yönetim kurulunun TEFBİS'e girilmesi md. 23/5'in lafzında yok (yalnız mali kayıtlar); varsayılan: cümle md. 23/5 çapası olmadan uygulama olarak ‹…› içinde kalır, seçenek cümlenin düşmesidir.
7. Aydınlatma Tebliği OAB korpusunda yok; varsayılan: Kütüphane korpusundaki teyitli metin (23.08.2026) `docs/mevzuat/`'a kopyalanıp BENIOKU'ya satırı eklenir ve bu belgenin "Tb" atıfları ona çevrilir.
8. Yedek cümlesi için varsayılan: "günlük yedeklerde en çok 14 gün, güncelleme öncesi yedeklerde son beş güncelleme boyunca" ve "dış yedeklerde yedeğin okulca saklandığı süre boyunca" yazılır; dış yedeğin saklama ve imha süresini okul müdürlüğü belirler (dönem kapanışındaki silmeler F4'te gelir).
9. Şoför ve rehber yaşı kural paketinde var (T:3633), doğum tarihi alanı veri modelinde yok; varsayılan: doğum tarihi tutulmaz ve metne girmez, F6 tasarımında karara bağlanır.
10. Banka hareketinin karşı tarafı (T:1559) §3.4 işleme envanterinde yok; varsayılan: envantere satır eklenir, havaleyle gelen bağışçıya ulaşma kanalı olarak E04'ün okul sitesinde yayımlanmasının yeterliliğini okul müdürlüğü değerlendirir.
11. Ayar açıkken bağışçının T.C. kimlik no'sunun hukuki sebebi (TEFBİS'in numarayı istemesi) korpusta doğrulanamadı; varsayılan: teyit gelene kadar açık biçim onaylanmış sayılmaz ve hukuki sebep satırı ‹…› içinde kalır.
12. T:1598'deki "varsayılan olarak dökümde yoktur" sözü bir ayarı ima ediyor olabilir; varsayılan: aylık bildirimde bağışçı adı yer almaz cümlesi ‹…› içinde kalır, F3'te ayar çıkarsa değişir.
13. Veri sorumlusu temsilcisi okul için doğmaz (Tb md. 3/1-ğ); varsayılan: başvuru adresi (posta ya da e-posta) Okul Bilgileri'ndeki veri sorumlusu alanına yazılır, ayrı alan açılmaz.
14. K3'teki birlik personeli (sürüm 2) ve program kullanıcısı E04'ün dışında; varsayılan: program kullanıcısının metni hesap teslim pusulasında kalır, birlik personeline sürüm 2'de beşinci bölüm yazılır.
15. E07'deki "Aydınlatma metninin tamamı … okul ilan panosunda ve okulun internet sayfasındadır" cümlesi onay bekliyor; varsayılan: cümle kalır ve E04 katalogdaki gibi docx ve PDF basılır, okul sitesine PDF konur (ayrı HTML biçimi üretilmez).
16. 1. bölümün adı "Veli ve üye" plan §4.1'deki katalog adıdır; varsayılan: ad kalır, kim kastedildiğini Kapsam satırı söyler, seçenek "Veli, aday ve görevli"dir.
17. Onaylı "Haklarınız" cümlesi hakların bir kısmını sayıyor, ardından tam liste geliyor; varsayılan: ikisi de basılır ve liste "Haklarınızın tamamı şunlardır:" ile açılır, seçenek E04'te onaylı cümlenin yerine yalnız tam listenin basılmasıdır.
18. Veli listesindeki katılım işareti isteğe bağlı sayım yardımıdır ve KVKK md. 5/2-ç'nin "zorunlu" unsuru tasarımda açık sorudur (T:312); varsayılan: hukuki sebep 5/2-ç basılır, okul müdürlüğü teyit eder.
19. Harcama dosyasındaki teklif ve teslim kaydı korpusta dayanaksız; varsayılan: mevzuat çapası olmadan "programın harcama dosyası ayrıca … tutar" diye yazılır, seçenek bu cümlenin çıkarılmasıdır.
20. Toplama yönteminin Tebliğ md. 5/1-i'ye göre sınıfı için varsayılan: dosyadan aktarım "kısmen otomatik yolla", elle giriş "otomatik olmayan yolla ve programın kayıt sisteminin parçası olarak" yazılır.

## Denetim bulgularının işlenişi

31 bulgunun 28'i olduğu gibi, 3'ü kısmen işlendi; tamamen reddedilen bulgu yok.

| Bulgu | Nerede |
|---|---|
| 1, 21 | Başvuru: "(KVKK md. 13/2)", "(KVKK md. 14/1)", süreler açıkça (dört bölüm) |
| 2, 26 | 1-B Toplama: ayrı hukuki sebep cümlesi ve yükümlülük kaynakları; 1-A'da "aynıdır" kalktı |
| 3 | 3. bölüm Hukuki sebep üç gruba ayrıldı |
| 4 | 4. bölüm: ayar açıkken amaç, aktarım, hukuki sebep ‹…›; basmama kısmı soru 11'e çevrildi (aşağıda) |
| 5, 25 | 1. bölüm A (veli listesi) ve B (aday ve görevli) kısımlarına ayrıldı; V5 tekrarı B'de "ad şifreli" cümlesine indirildi |
| 6 | 4. bölüm Amaç: md. 18/1-3 lafzı; teklif ve teslim kaydı çapasız program uygulaması; soru 19 |
| 7, 23 | Kapsam satırı ve 1-B Amaç'ın temsil türleri; bölüm adı soru 16 (aşağıda) |
| 8 | 1-B Aktarım: md. 23/5 çapası düştü, "uygulamada"; soru 6 |
| 9 | Aktarım satırlarına amaç sözü (dört bölüm) |
| 10 | Toplama satırlarına Tebliğ md. 5/1-i sınıfı; soru 20 |
| 11 | Soru 13 temsilci yönünden kapandı; 0. bölüm Dayanaklar |
| 12 | Yedekler satırına dış yedek cümlesi; soru 8 |
| 13 | 1-B İşlenen veriler: MEM onay sayısı, dayanak notu, iptal gerekçesi, yedekten çağrı günü, görevde kalma işareti, raporu okuyan/bütçeyi sunan; Saklama'da notların kalışı |
| 14 | 1-B ve 2. bölüm Saklama: üretilen evrakın şifreli saklanması |
| 15 | 1-B, 2., 3., 4. bölüm Saklama: denetim izi ve erişim günlüğü |
| 16 | 1-C ve öteki bölümlerde gelen-giden evrak kaydı (md. 23/1-c, korpusta teyitli) |
| 17 | 2. bölüm: okul müdürünün adı şifresiz; ad şifreli cümlesi personel listesine daraltıldı |
| 18 | 2. bölüm Saklama: erken silme ve birleştirme |
| 19 | 1-A Saklama: katılım işaretinin listeyle silinmesi koşulu |
| 20 | 0. bölüm: "kişisel veriyi … göndermez" |
| 22 | 3. bölüm Amaç: "Usul ve Esaslar md. …" önekleri |
| 24 | 1-B: "katılmadıysa bunun özürlü sayılıp sayılmadığı" |
| 27 | 1-B: kişi türü ve beyan günleri yeniden yazıldı |
| 28 | Haklarınız: "Haklarınızın tamamı şunlardır:"; soru 17 |
| 29 | Başvuru: "Kişisel Verileri Koruma Kurulunun belirlediği tarifedeki", "yukarıda adı geçen … yazıyla" |
| 30 | "program yöneticisi (OAB'den sorumlu müdür yardımcısı)" her bölümde ilk geçişte |
| 31 | 4. bölüm: iç not çıktı, ayar ‹…› ile iki biçim; maske biçimi kısmı reddedildi (aşağıda) |

## Denetimde reddedilen bulgular

- **Bulgu 4, "ayar açık varyantı basılmasın" kısmı:** ayar açıkken E04'ün numarayı hiç anmaması KVKK md. 10/1-b ve Tebliğ
  md. 5/1-j'ye göre daha ağır bir eksik bilgilendirme olur; açık biçim metne kondu, hukuki sebebin teyidi soru 11'e
  bırakıldı.
- **Bulgu 23, "üye Yönetmelikteki anlamıyla kullanılmamış" kısmı:** Yönetmelik "üye"yi organ üyesi için de kullanır
  ("yönetim kurulu başkan ve üyeleri", md. 12/4; "yönetim kurulu üyesi", md. 13/6) ve sözlük "organlarda asıl üye ·
  yedek üye" der; bölüm adı plan §4.1'in katalog adı ve test adı olduğu için değiştirilmedi (soru 16). Kapsam ve "organ"
  düzeltmesi işlendi.
- **Bulgu 31, "ekranda ilk hanelerden başkası gizlenir" kısmı:** maskenin biçimi tasarımda tanımlı değil (T:74, T:1708
  yalnız "maskeli" der); doğrulanamayan biçim yerine "numaranın bir kısmı gizlenir" yazıldı.
