# OAB Defteri — Arayüz Sözlüğü ve Yazım Kuralları

*31.10.2026 · F1b 0. adımda yazıldı. Kalıbı aile iskeletinin sözlüğüdür; kavramları OAB'nin
[genel tasarımına](tasarim/2026-10-31-genel-tasarim.md) ve [CLAUDE.md](../CLAUDE.md)'ye dayanır. **Bağlayıcıdır.**
Kullanıcıya görünen HER metin (etiket, düğme, başlık, snackbar, hata, boş durum, açılış iletisi, kılavuz, evrak,
site içeriği) bu sözlüğe uyar. Kod tanımlayıcıları (İngilizce) ve kod yorumları kapsam dışıdır; yorumlar ve testler
buradaki kurallara bölüm numarasıyla ya da satır adıyla ("Yedek" satırı) atıf yapar.*

Hedef okur, programı çoğunlukla kullanan ve okul-aile birliği işlerinden sorumlu müdür yardımcısı; ayda bir kendi işi
için giren başkan, muhasip ve sekreter (çoğu gönüllü veli); Denetleme Kurulu üyeleri ve okul müdürüdür (tasarım §1
"Kim kullanır"). Hiçbiri yazılımcı değildir. Metin onlarla onların diliyle konuşur: mevzuat terimleri mevzuattaki
anlamıyla kullanılır (CLAUDE.md §2 altın kural 6), programın iç kavramları (karar, faz, evrak ve kural kodları)
yüzeye çıkmaz (§2).

**Dayanak ve çelişki.** Terimin dayanağı [`docs/mevzuat/`](mevzuat/BENIOKU.md) kanonik metni, CLAUDE.md ve genel
tasarımdır. Sözlük onlara uyar; çelişirse onlar kazanır ve sözlük düzeltilir. Doğrulanamayan hüküm buraya da yazılmaz
(altın kural 1). Yalın "md." atıfları MEB Okul-Aile Birliği Yönetmeliğidir; "BSG Yön." MEB Bilgi ve Sistem Güvenliği
Yönergesi, "RYUE" Resmî Yazışmalarda Uygulanacak Usul ve Esaslar Hakkında Yönetmeliktir (tasarımdaki
kısaltmalar; §6.4, §9.5).

**Bugünkü durum.** Program F1b'dedir. Aile iskeletinden gelen bazı düzenler (tek yönetici parolası, görevli kipi,
öğrenci sicili) F1b adımlarında OAB'nin düzenine döner ([plan §2.2](plan/2026-10-31-f0-f1-plani.md)). Sözlük bugün
ekranda olanı yazar; değişeceği bilinen satır bunu yanında söyler. Ekrandaki metin değişince buradaki satır aynı
değişiklikte güncellenir.

## 1. Kavram sözlüğü

Sıra: program ve konumu; birlik ve organları; resmî kayıtlar; takvim ve okul; kişiler; güvenlik; yedek, sürüm,
kurulum. F1'den sonraki fazların kavramları (genel kurul akışı, gelir-gider ve banka eşleme, makbuz koçanı, harcama
zinciri, kantin, servis) ekranları geldiği fazda eklenir; o güne dek terim için tasarımın ilgili bölümü esastır.

| Kavram (kod) | Kullanılır | Kullanılmaz | Not |
|---|---|---|---|
| Program kendisi | **OAB Defteri**; tanım: "okul-aile birliğinin işlerini okulun bilgisayarında yürüten çevrimdışı bir masaüstü programı"; Genel Bakış'ta kısaca "yerel araç" | "otomasyon sistemi", "resmî sistem", "elektronik karar defteri", "TEFBİS yerine" | Konum (CLAUDE.md §1, bağlayıcı): program **karar defterinin ve TEFBİS'in yerine geçmez**; bunlara girilecek metni ve listeyi hazırlar, tutarlılığı denetler. Konum dili bugün kılavuzun "Programın Konumu" bölümünde ve Hakkında'dadır, ikisinde aynı dille yazılır; tasarıma göre ilk açılış ekranında ve sitede de yer alır (tasarım §3.1), evrakta belgeye göre üç kalıptan biriyle yazılır (tasarım §9.2) |
| Birlik | **birlik**; ilk geçişte ve tanıtımda **okul-aile birliği** | "dernek", "vakıf" | Yönetmeliğin kısa adı ([md. 4/1-b](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4)). Birlik okul bünyesinde kurulan, tüzel kişiliği olmayan bir yapıdır ([md. 5/1](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-5)); dernek ya da vakıf diye anılmaz |
| Birlik üyesi | **üye**; organlarda **asıl üye** · **yedek üye** | — | Yönetmeliğin anlamıyla: okul yöneticileri, öğretmenler, veliler ile on sekiz yaşını doldurmuş kursiyerler ve çıraklık, kalfalık, ustalık eğitimine devam edenler birliğin tabii üyesidir ([md. 4/1-e](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4), [7/1](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7)). Bugün Kişiler ekranındaki "üye türü" birlik üyeliği değildir (aşağıda "Personelin türü") |
| Organlar | **genel kurul** · **yönetim kurulu** · **Denetleme Kurulu** | "Denetim Kurulu"; kullanıcı metninde "YK", "DK" | [md. 8](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-8). Yazım CLAUDE.md §2 altın kural 6 ve tasarımdaki gibidir: cümle içinde "genel kurul", "yönetim kurulu", "Denetleme Kurulu"; başlıkta Başlık Düzeni (§3). Kilit ekranındaki rol etiketi de açık yazılır ("Denetleme Kurulu 2"; tasarım §4.4.3). Organ ekranları F1c'de gelir (plan §2.3) |
| Yönetim kurulunun görevleri | **başkan** (Yönetmeliğin "birlik başkanı", md. 4/1-g) · **başkan yardımcısı** · **muhasip** · **sekreter**; kurulun işi **görev ve iş bölümü** | "sayman", "muhasebeci" (muhasip için) | [md. 12/3](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [13/4](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13): muhasip birliğin gelir-gider işlemlerini, sekreter yazışmalarını yürütür. **Mali kayıtları yalnız muhasip girer** (K2, D2) |
| Okul müdürü | **okul müdürü** | müdür için "yönetim kurulu başkanı", "yönetim kurulu üyesi" | Okul müdürü yönetim kurulu üyesi değildir, kurula başkanlık etmez (altın kural 6). Her şeyi okur, yalnız kendi yazılarını yazar (K2) |
| Karar defteri | **karar defteri** (tam adı "yönetim kurulu karar defteri", [md. 23/1-b](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | "elektronik karar defteri", "dijital defter" | Noterce tasdiklidir; kararlar deftere el ile yazılarak imzalanır ([md. 13/5](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/2](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Program defteri tutmaz: karar taslağını hazırlar; sekreter deftere yazınca **"deftere işlendi"** işaretini, defter sıra no'sunu ve sayfasını kaydeder (tasarım §3.1) |
| Karar taslağı | **karar taslağı**; belgenin başında **"TASLAK — karar defterine geçirilecek metin"** | taslak anlamında tek başına "karar"; "karar belgesi" | Konum cümlesi taslağın sonunda, imza bloklarının üstündedir; "deftere işlendi" işaretinden sonra da taslak ibaresi kalkmaz (tasarım §9.2). İlk karar taslağı F1c'dedir (plan §2.3) |
| Tasdikli öteki defterler | **gelir-gider defteri**, **gelen-giden evrak defteri** | — | İl/ilçe millî eğitim müdürlüğünce tasdiklidir ([md. 23/1-2](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Program yerlerine geçmez; deftere **geçirilecek** dökümü hazırlar (tasarım §9.2). F3'te gelir |
| TEFBİS | **TEFBİS**; kılavuzun TEFBİS bölümünde (F3) ilk geçişte "Bakanlıkça kurulan merkezî bilgi sistemi (TEFBİS)" (md. 23/5'in sözü); konum cümlesi CLAUDE.md §1'deki gibi yalın "TEFBİS" der | "TEFBİS'e aktar", "TEFBİS'e gönder", "TEFBİS ile eşitle", "entegrasyon" | Birliğin gelir ve gider kayıtlarını TEFBİS'e okul idaresi girer ([md. 23/5](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Program TEFBİS'e bağlanmaz, giriş yapmaz, TEFBİS'in giriş bilgisini saklamaz (K6; tasarım §3.1): **TEFBİS'e girilecekler listesi**ni hazırlar, **"TEFBİS'e girildi"** işaretini kaydeder. F3'te gelir |
| Tahmini bütçe | **tahmini bütçe** ("birlik tahmini bütçesi") | "bütçe planı" | Yönetim kurulu hazırlar, genel kurulda görüşülür ([md. 13/9](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)). Ekranı F4'te gelir |
| Uyarı, gerekçe, engel (kural paketi) | **uyarı**; bilinçli sapmada kullanıcının yazdığı **gerekçe**; madde atfı **"md. 9/3"** biçiminde | "kural ihlali", "override", "bypass"; uyarı için "hata" | Altın kural 3: program doğrusunu gösterir, sapma gerekçesiyle kayda geçer; sert engel yalnız CLAUDE.md'de sayılan hâllerdedir. Henüz girilmemiş veri **eksik**tir, gerekçe istemez. Okulun kendi ayarı ya da uygulaması **"okul kararı"** / **"okul uygulaması"** etiketiyle gösterilir, mevzuat gereği diye sunulmaz; özelge ve sirküler **bilgi metni**dir, hüküm diye basılmaz (tasarım §3.3). Kural paketi F1c'de gelir |
| Birlik dönemi | **birlik dönemi** (genel kuruldan genel kurula) | tek başına "dönem" (ders dönemiyle karışacak yerde), "mali yıl" | T3. Ders yılının iki dönemi (**ders dönemi**) ayrı kavramdır (Ayarlar → Ders Yılları; tasarım §5.1 `SchoolTerm`, §5.2.1); birlik dönemi ders yılı ve TEFBİS dönemiyle eşlenir. Ekranı F1c'de gelir |
| Ders yılı | **ders yılı**; ders yılının iki dönemi **ders dönemi** (birlik dönemiyle karışabilecek her yerde; tasarım §5.2.1); Ders Yılları ekranında bağlam açıkken **1. dönem** · **2. dönem** | — | Ayarlar → Ders Yılları ve sihirbazın üçüncü adımı. Kantinde yarıyıl ayının yarım kirası (EK-2 md. 4) dönem tarihlerinden okunur (tasarım §5.1 `SchoolTerm`). Mevzuattan alıntıda mevzuatın sözü ("eğitim ve öğretim yılı") korunur |
| Kapalı gün (`Holiday`) | üst adı **kapalı gün** (sekme **Kapalı Günler**); türleri **Resmî tatil** · **Dini bayram** · **Öğrenciye kapalı gün** (ara tatil, yarıyıl) · **İdari izin / diğer**; hesapla bulunmuş bayram tarihinde **"tahmini"** | genel anlamda tek başına "tatil" | Türler aile iskeletinden gelir (tasarım §5.1 `Holiday`). Ara tatil ve yarıyıl resmî tatil türünden ayrı tutulur ve tek başına "tatil" denmez. İş günüyle verilen süreler (ör. elden bağışın beş iş günü içinde bankaya yatırılması, [md. 16/3](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) bu takvimle hesaplanır |
| Okul bilgileri | ekranda **Okul Bilgileri** (Ayarlar sekmesi ve sihirbazın ikinci adımı); künye evrakın antedinde kullanılır | — | Tasarım ve plan aynı yeri "okul kartı" diye anar. OAB'ye özgü alanlar (öğrenci mevcudu, yerleşim türü, kantin işletme modu, personel çalıştırma biçimi) F1b 4. adımda gelir (plan §2.2; tasarım §5.1); birliğin banka hesabı F3'te sihirbazın banka adımıyla gelir (tasarım §14) |
| Bilgisayar ve demirbaş | onay **"Bu bilgisayar okul demirbaşıdır."**; alan **"Bilgisayarın demirbaş no'su"** | — | Program okul demirbaşı bilgisayara kurulur (tasarım §4.5 "Hesap ve bilgisayar"). Bugün "demirbaş" yalnız bilgisayar için geçer; birliğin satın aldığı malların adı harcama ekranlarıyla (F4) eklenir |
| e-Okul | **e-Okul**; e-Okul'daki rapor adları olduğu gibi ("Personel Listesi") | "e-okul", "eOkul" | Program e-Okul'a bağlanmaz; okulun e-Okul'dan aldığı dosya içe aktarılır (tasarım §8.4) |
| İçe aktarma | **içe aktarma** (dosyadan toplu alma), tek çalıştırma **aktarım**; önce **önizleme**, kayıt yalnız onayla yazılır | "import", "senkronizasyon", "eşitle" | İçe alınan dosya güvenilmeyen girdidir (tasarım TK18). Aktarım kimseyi ayırmaz: listede bulunmayan kişi **Ayrılış Havuzu**'nda karar bekler (bugünkü Kişiler ekranı) |
| Kişiler (bugün) | **öğrenci**, **öğretmen**, **diğer personel**; **sicil**; **Ayrılış Havuzu**; eylem **"Ayrıldı olarak işaretle"**, rozet **"Ayrıldı · gg.aa.yyyy"**; olası aynı kişi sorusu **"Bu iki kayıt aynı kişi mi?"** | — | Aile iskeletinden gelir. Öğrenci sicili, içe aktarımı ve Öğrenciler sekmesi F1b 5. adımda sökülür; e-Okul'dan personel ve **veli listesi** alınır (T5; plan §2.2). OAB'nin kişi türleri (veli, öğretmen, yönetici, hayırsever, kursiyer) F1c'de gelir (tasarım §5.2.2) |
| Personelin türü (`MemberKind`) | ekranda bugün **"üye türü"**: **öğretmen** · **diğer personel**; sekme **"Öğretmenler ve Diğer Personel"** | öğretmen anlamında tek başına "personel" | "Personel" genel anlamda (okulun bütün çalışanları) ve e-Okul raporunun adında ("Personel Listesi") serbesttir. e-Okul'daki görev metni yalnız bu türü seçmek için okunur, saklanmaz (T5). OAB'de "üye" Yönetmeliğin birlik üyesidir (md. 4/1-e); değerler F1b 5. adımda tasarıma göre (öğretmen · yönetici · diğer; tasarım §5.1, §8.4) düzelir, "üye" sözcüğünün birlik üyeliğiyle karışması o adımda gözden geçirilir |
| Veli | **veli**; **veli listesi** | — | Veli, öğrencinin annesi, babası ya da kanuni sorumluluğunu üstlenen kişidir ([md. 4/1-f](mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4)). e-Okul'dan yalnız veli adı-soyadı ve öğrencinin sınıfı alınır (T5; §5). F1b 5. adımda gelir |
| Parola | **parola**; bugün programın tek parolası **yönetici parolası**; F1b'den sonra her hesabın kendi **parolası**, ilk girişte değiştirilen **geçici parola** (tasarım §4.4.5, TK15) | parola anlamında **"şifre"**; "uygulama parolası"; "PIN" | Parola kurulum sihirbazının ilk adımıdır; kurulmadan kişi kaydı yapılamaz. **Parola paylaşılmaz, herkes kendi hesabıyla çalışır** (T1; [BSG Yön. md. 7/2](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [9/2-e](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) — programa kıyasen, tasarım TK9): metin parolanın başkasıyla paylaşılmasını ya da birden çok kişide bulunmasını öğütlemez. Parola hiçbir belgede yoktur (tasarım §9.1-5). "Şifre" yalnız şifreleme anlamında kalır ("şifreli yedek", "şifrelenen alanlar"); mevzuattan alıntıda mevzuatın sözcüğü korunur. Programın parolası işletim sisteminin yetkisiyle karışmaz: Windows'un ve Pardus'un (`sudo`) yetkisi için **"yönetici yetkisi"** denir |
| Program yöneticisi ve roller (F1b) | `yonetici` rolünün etiketi **"Program yöneticisi (OAB'den sorumlu müdür yardımcısı)"**; öteki roller **başkan** · **başkan yardımcısı** · **muhasip** · **sekreter** · **Denetleme Kurulu** · **okul müdürü** | programın yöneticisi için "sistem yöneticisi", "admin" | Tasarım §4.4. "Sistem yöneticisi" BSG Yön. [md. 4/1-s](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)'de Bakanlığın ve il/ilçe millî eğitim müdürlüklerinin bilişim personelidir; programın yöneticisiyle karıştırılmaz. Roller F1b 2. adımda gelir (rol-izin matrisi tasarım §4.4.2) |
| Hesap (F1b) | **hesap** (bir hesap = bir kişi + bir rol); kilit ekranında hesaplar **rol etiketiyle** ("Muhasip", "Denetleme Kurulu 2"); askıdaki hesap **"askıda — program yöneticisine başvurun"**; belge **Hesap teslim pusulası** | — | Kilit ekranında kişi adı gösterilmez (tasarım §4.4.3). Hesaplar dönemliktir (tasarım §4.4.1). F1b 1. ve 2. adımlarda gelir |
| Kip (aile iskeleti) | **yönetici kipi**, **görevli kipi**, **kilitli**; eylemler **"Görevli kipine geç"** (Ctrl+Shift+G), **"Yönetici kipine geç"**, **"Kilitle"** | "öğrenci modu", "admin modu", "kiosk"; "kütüphane görevlisi", "öğrenci görevli", "masa" | Aile iskeletinden gelir. OAB tasarımında görevli kipi yoktur: boşta süre dolunca program kilitlenir (tasarım TK14); kip F1b 1. adımda hesap ve oturum düzenine döner (plan §2.2). O güne dek metin görevli kipini kütüphanenin ya da öğrencinin işi gibi anlatmaz |
| Kilit ve çıkış | **"Kilitle"** (programı açık bırakır, kayıtları kilitler; ekran **"Kayıtlar kilitli"**, §4.2); **"Çık"** (programı kapatır) | — | Pencerenin çarpısı da programı kapatır; tepsi yoktur (T6). Çıkış diyalogları §4.2'dedir |
| Kurtarma anahtarı | **kurtarma anahtarı** | "kurtarma kodu", "yedek parola", "ana anahtar" | Parola unutulursa kayıtlara erişmenin tek yoludur. Basılıp **okul müdürlüğünde kapalı zarfta** saklanır, veliye geçmez (T1, D3); PDF dosyası bilgisayarda bırakılmaz (tasarım §9.7). Anahtar programda saklanmaz; hiçbir günlüğe, iletiye ya da dosya adına yazılmaz |
| Kurtarma anahtarı işlemleri | kart adları **Kurtarma Anahtarını Doğrula** ve **Kurtarma Anahtarını Yenile**; eylem **"yenileme"**; uyarı **"Kurtarma anahtarı doğrulanmadı"** | "anahtarı sıfırla", "anahtarı değiştir" | Bugünkü yenileme kayıtların anahtarını değiştirmez, kayıtlar yeniden şifrelenmez; yenilemeden önce alınmış yedekler başka bilgisayarda eski anahtarla açılır ve metin bunu söyler (tasarım §4.4.6). F1b'den sonra anahtarı yalnız program yöneticisi yeniler (tasarım TK9) |
| Şifreleme | **şifreli**, **şifrelenen alanlar**; "güçlü şifrelemeyle korunur" | ayar ekranında ve iletide yöntem adları (Fernet, AES, X25519, Argon2id, HMAC); "veritabanı şifreli" | Şifrelenen şey belirli kişisel veri alanlarıdır; bu **tam disk şifrelemesi değildir** ve metin bunu açıkça söyler; tam koruma BitLocker ya da LUKS'tur (tasarım §4.4.6). Yöntem adları yalnız Hakkında'nın **Teknik Bilgiler** kartında geçer |
| Yedek | **yedek**, **şifreli yedek**; bugün türleri **günlük yedek** (program günde bir kez kendiliğinden alır: açılışta ya da açıkken gün değişince) ve indirilen şifreli yedek; indirileni **"USB bellekteki yedek"** (ya da okulun ağ diskindeki); hatırlatma kartı **Şifreli Yedeği USB Belleğe Alın**; geri yüklemede kenara alınan **önceki veritabanı** (`db-onceki-…`) | kullanıcı metninde dosya uzantısı (`.odbak`), "kapsayıcı", yöntem adları; "dış yedek" (ekranda ve kılavuzda; kod yorumunda serbest); "harici yedek", "bulut yedeği" | Teknik adlar yalnız Hakkında sayfasında geçer. Yedek bulut depolama hizmetine yüklenmez ([BSG Yön. md. 11/23](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11)); taşınabilir ortamdaki veri şifreli saklanır ([BSG Yön. md. 10/5](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)), programın yedeği zaten şifrelidir ve şifresiz kopya üretilmez. **USB bellekteki yedek programın dışındadır:** program ona ulaşamaz, onu silemez; saklanması okulun sorumluluğundadır. Program açılmıyorsa geri yükleme Windows'ta Başlat menüsündeki **"OAB Defteri — Yedekten Geri Yükle"** kısayoluyla, Pardus'ta `oab-defteri --geri-yukle` komutuyla yapılır. F1b 3. adımda dışarı çıkan yedek dosya deposunu da taşır (tasarım §4.4.7); yeni türlerin adları o adımda işlenir |
| Eski program, yeni veri (`SchemaTooNewError`, çıkış kodu 4) | açılış iletisinin başlığı **"Program sürümü eski"**; çözüm "programı güncel sürüme yükseltip yeniden açın" | kullanıcı metninde "şema", "migration", "göç", "sürüm uyuşmazlığı" | İki durumda çıkar: daha yeni sürümün yazdığı veriyi eski program açmaya çalışınca ve daha yeni sürümle alınmış yedek eski programa geri yüklenince. Program veriyi korumak için açılmaz. İleti "tanımadığı **değişiklikler**" der; tanınmayan değişikliklerin adları iletide GEÇMEZ (§2), yalnız günlüğe (`logs/uygulama.log`) yazılır ve ipucu günlük dosyasını anar |
| Sürüm | **"yayımlanan son sürüm"**, **"kurulu sürüm"**, **"kurulum dosyası"**; düğmeler **"Şimdi denetle"** · **"Doğrula ve indir"**; elle denetlemenin bağlantısı **okulapp.org/oab-defteri** (programın sayfası; dosyalar indir.okulapp.org'dan iner) | "GitHub sürümü", "Release", "kurucu"; özet algoritmasının adı; düğme adı olarak tek başına "Denetle" | Güncelleme denetimi yalnız düğmeyle yapılır, program açılışta internete çıkmaz (tasarım TK4). Hizmetin adı (GitHub) Güncelleme ekranının açıklama metninde geçmez. **Bugünkü sapma:** sunucunun denetim hata iletileri (ulaşılamama, güvenli bağlantı, sınırlama, HTTP hatası, beklenmeyen yanıt; `services/updates.py`) GitHub adını, doğrulama hata iletileri "SHA-256" ve "SHA256SUMS.txt" adlarını anar; iletiler F1b 6. adımda bu satıra uydurulur ve satır güncellenir. Program indir.okulapp.org'a ve programın sayfasına istek atmaz: bağlantıyı dış tarayıcı açar. Ekran adları §4.7 |
| Kurulum ve kaldırma | **kurulum dosyası** (Windows'ta indirilen ve çalıştırılan dosya); işler **kurulum** · **güncelleme** · **kaldırma**; kurulumsuz paket **taşınabilir sürüm** (Windows'ta `…-win64-portable.zip`, Pardus'ta `…-linux-x64.tar.gz`); karşıtı **kurulu program** | kullanıcı metninde **"kurucu"**, **"yükleyici"**, "installer", "setup"; kurulum dosyasının penceresi için "sihirbaz" | **Kurulum Sihirbazı** programın ilk açılış ekranıdır (§4.4). Kod yorumlarında ve geliştiriciye dönük paketleme belgelerinde (`packaging/`) "kurucu" serbesttir. Kurulum yetkisinin iki seçeneği tasarım TK7'dedir |
| Lisans | **PolyForm Noncommercial 1.0.0**; program kamuya "kaynağı açık" diye tanıtılır | programın kendisi için "açık kaynak" | K7. Üçüncü taraf bileşenler kendi lisanslarıyla anılır ("açık kaynaklı üçüncü taraf bileşenler" doğrudur). Lisans adı teknik ad sayılmaz: bildirim yükümlülüğü gereği açıkça yazılır (Hakkında ve Lisans; `THIRD_PARTY_LICENSES`) |

## 2. İç kodlar yüzeye çıkmaz

Tasarımın, planın ve denetimin kodları kullanıcı metninde (ekran, ileti, hata, açılış iletisi, kılavuz, site) ve
evrakın başlığında ve gövdesinde GEÇMEZ:

- kullanıcı kararları (`K1`-`K9`, `T1`-`T6`, `D1`-`D5`, `F0-a`…`F0-e`), teknik kararlar (`TK1`-`TK22`), açık
  kararlar (`M-`, `A-`, `B-`, `KE-` ile başlayanlar), riskler ve denetim önerileri (`R2`, `R9` gibi);
- fazlar ve adımlar (`F0`-`F8`, `F1a`, `F1b`…), devralınan kusurlar (tasarım §13'teki `D3`, `D48` gibi; kullanıcı
  kararı `D1`-`D5` ile karışmasın) ve denetim bulguları (`GA-`, `UY-`, `KM-`, `SU-`, `MA-`…);
- evrak kodları `E01`-`E79`;
- kural paketinin kimliği ve revizyonu (`OAB-2023.12`, `rev`) ile kural kimlikleri (`alan.konu` biçimi, ör.
  `bagis.elden_yatirma_is_gunu`);
- aile iskeletinden yorumlarda kalmış kodlar (`U5`, `T15`, `TB…` ve ailenin evrak kodları);
- iç kimlikler (`id=…`, `pk`), model ve alan adları (`SchoolConfig`, `Account`), uç yolları, hata kodları
  (`parola_gerekli`, `rol_yetkisiz`), göç adları ve dosya uzantıları (`.odbak`; §1 "Yedek").

Kodun yerine **adı** yazılır: belge kodunun yerine belgenin adı, kararın yerine sonucu, kural kimliğinin yerine madde
atfı. Kod yorumlarında ve testlerde kodlar serbesttir.

**Tasarımın açtığı istisnalar.** Başkası yoktur; her biri kendi fazında bu sözlükle birlikte gözden geçirilir:

1. Evrak altlığı: "OAB Defteri · E07 · Sayfa n/m" (tasarım §9, §9.2). Kod yalnız altlıkta durur; başlıkta ve
   gövdede belgenin adı yazılır. Kural paketinin revizyonu belgeye basılmaz, evrak izinde tutulur (tasarım §9).
2. Kural uyarısının ve gerekçe kaydının atfı: "md. 9/3" ya da "kullanıcı kararı A-2 (gerekçe md. 14/4)" biçimi
   (tasarım §6.1 "Erişim"; F1c).
3. Yıllık iş takviminin satırları kural kimliği ve atıf taşır (tasarım §9.6, E14 satırı; F2).

**Belge adları.** Programın kendi güvenlik belgeleri katalog dışıdır ve E-kodu almaz (tasarım §9.7). Programın belgeleri
ve F1'de ele alınan evrak, fazlarıyla:

| Kod | Belgenin adı | Faz |
|---|---|---|
| — (program belgesi) | **Kurtarma anahtarı çıktısı** — tasarımdaki adı "kurtarma anahtarı belgesi" (§9.7); indirilen dosya `Kurtarma-Anahtarı-Çıktısı_gg.aa.yyyy.pdf` | aileden; metni F1b'de OAB'ye göre yazılır (tasarım §13 D50) |
| — (program belgesi) | Yedek raporu (adı F1b'de kesinleşir) | F1b |
| — (program belgesi) | Kurtarma anahtarı zarfı imha tutanağı | F4 |
| E63 | Hesap teslim pusulası | F1b |
| E04 | Kişisel veri aydınlatma metni | metni F1b'de içe aktarma ekranında, belgesi F2'de |
| E01 | Yönetim kurulu görev bölümü, imza yetkisi ve temsilci karar taslağı | F1c |
| E02 | Denetleme Kurulu görev bölümü tutanağı ve denetim planı | F1c |
| E03 | Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi | F1c |

Öteki belgelerin adları tasarım §9.5 kataloğundadır; belge ekrana geldiği fazda buraya işlenir. Katalogdaki
kısaltmalar (YK, DK, MEM) belge adında açık yazılır (§3). **Aile kodlarına dikkat:** aile iskeletinden gelen kodda ve
yorumlarda geçen evrak kodları ailenin kataloğudur; OAB'de aynı numara başka belgedir (ailede kurtarma anahtarı
çıktısı "E14" idi, OAB'nin E14'ü yıllık iş takvimidir). Tasarım aile kodlarını "KütD-" önekiyle anar ("KütD-E13"
biçiminde; §9).

## 2.1 Belgelerde örnek ve yer tutucu yazımı

Depo herkese açıktır; belgelerde, testlerde ve ekran görüntülerinde **gerçek kurum, kişi, banka ve ağ bilgisi
kullanılmaz** (altın kural 5):

- **Örnek veri** uydurmadır ve `Örnek` ön ekiyle kurulur: "Örnek Anadolu Lisesi", "Örnek İlçe", kısa ad "Örnek AL".
  Uzun ad gereken testte ad uzatılır, gerçek kurum adı kullanılmaz. Örnek kişi adları da uydurmadır; görev ve rol
  birleşimi gerçek bir kişiyi düşündürmeyecek biçimde seçilir.
- **Sağlaması tutan T.C. kimlik numarası ve IBAN** depoya düz metin olarak yazılmaz; test gerekirse değeri çalışırken
  üretir. Gerçek veri, banka özeti, TEFBİS çıktısı ve e-Okul listesi depoya girmez: `.gitignore` önler,
  `packaging/depo_sizintisi.py` (TCKN, IBAN, yasaklı ad) ve `packaging/veri_sizintisi.py` (paket) denetler.
- **Yollar:** kardeş depolara atıf `../<depo>/…` biçimindedir; mutlak yerel yol (`C:\Users\…`) hiçbir belgeye
  yazılmaz. Bilgisayar adı gerekirse `<bilgisayar-adı>` yer tutucusu kullanılır.
- Herkese açık tanıtım metninde (README, site) kişinin unvanı ve kurumun adı geçmez.

## 3. Yazım kuralları

- **Düğmeler cümle düzenindedir:** "Kilitle", "Parolayı değiştir", "Şimdi denetle", "Kaydet ve devam et". Sayfa,
  sekme ve bölüm **başlıkları** Başlık Düzenindedir: "Genel Bakış", "Kapalı Günler".
- **Başlık Düzeni nereye uygulanır:** kullanıcıya yol tarif edilirken adı geçebilen her başlık — sayfa başlığı (h1),
  sekme, sayfa içi bölüm ve kart başlıkları — Başlık Düzenindedir ("Ayarlar → Güvenlik", "Kişiler → Ayrılış Havuzu",
  "Şifreli Veritabanı Yedeği"); bir bölümün ya da kartın içinde metni parçalayan **alt başlıklar** cümle düzeninde
  kalır ("Sakladığınızı doğrulayın"). Üç istisna: §2'deki **belge adları** başlık yerinde de oradaki yazımıyla
  yazılır ("Kurtarma anahtarı çıktısı"); program durumu ekranlarının başlıkları §4.2'deki cümlenin kendisidir
  ("Kayıtlar kilitli"); onay diyaloğunun başlığı sorudur.
- **Başlık sabit addır.** Kartın ya da bölümün başlığı duruma göre değişmez; durum başlığın altındaki cümlede
  söylenir ("Yönetici Parolası ve Şifreleme" başlığının altında "Kişisel veri alanları şifreli." ya da "Yönetici
  parolası kurulmadı."). Böylece yol tarifi hep aynı adı kullanır.
- **Onay diyaloğu:** geri dönüşü olmayan ya da kayıt düşüren her işlem onay diyaloğundan geçer. **Başlık soru, gövde
  sonuçtur** ("Yedekten geri yüklensin mi?" başlığının gövdesi ne olacağını söyler); gövde başlıktaki soruyu yinelemez,
  ikisi aynı cümle olmaz. Parola ya da başka bir değer isteyen diyalog bir formdur: başlığı eylemin adıdır
  ("Programdan çık", "Parolayı değiştir"). Geri dönüşü olmayan işlemi onaylatırken parolayı da soran diyaloğun
  başlığı yine sorudur ("Kurtarma anahtarı yenilensin mi?").
- **Devam düğmesi** tek biçim: "Kaydet ve devam et" (kayıt yoksa "Devam"). Vazgeçme: "Vazgeç"; salt bilgi
  diyaloğunda "Kapat".
- **Seçici yer tutucusu** tek biçim: "Seçin". Boş seçenek: "— yok —".
- **Snackbar** tam cümledir ve noktayla biter ("Yönetici parolası değiştirildi.").
- **Süren iş** üç nokta karakteriyle söylenir: "Kaydediliyor…", "Denetleniyor…".
- **Yol tarifi** ok işaretiyle yazılır ("Ayarlar → Güvenlik"); bağlantı metni gittiği yeri adıyla söyler
  ("Ayarlar → Güvenlik'i aç", "Ayrılış Havuzu'nu aç").
- **Tırnak:** JSX metninde “ ” (kıvrık). Kesme işareti düz `'` (JSX'te `&apos;`).
- **"resmî"** ve **"millî"** düzeltme işaretiyle yazılır ("resmi", "milli" değil).
- **Kısaltma:** açıklanmamış kısaltma kullanılmaz. Evrakta kısaltma ilk geçtiği yerde açık biçimiyle, ardından parantez
  içinde yazılır ([RYUE md. 16/11](mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-16)).
  Arayüzde organ ve görev adları açık yazılır ("yönetim kurulu", "Denetleme Kurulu", "müdür yardımcısı"); "YK", "DK",
  "MY" kullanıcı metninde geçmez. TEFBİS ve e-Okul sistemlerin adıdır; TEFBİS kılavuzun TEFBİS bölümünde açılır (§1).
- **Terimler Yönetmeliğinkidir** (altın kural 6; §1). Servis evrakında "ihale", "teklif", "eksiltme" yazılmaz;
  "taşımacının tespiti", "başvuru", "Taşımacıyı Tespit Komisyonu" yazılır (tasarım §9.4). Kantin evrakında "ihale"
  serbesttir.
- **Tarih ve saat:** gg.aa.yyyy ve SS:dd, saat dilimi Europe/Istanbul. Ekranda yalnız `lib/format.ts` yardımcılarıyla
  (`formatDate`, `formatDateTime`) yazılır; `toLocaleString`/`toISOString` ile yerel kopya yazılmaz (`toISOString`
  UTC verir, gece yarısına yakın kayda bir önceki günü yazar). Evrakta tarih RYUE biçimindedir: gün ve ay iki, yıl
  dört hane, aralarında nokta ([RYUE md. 12/1](mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-12)).
- **Sayı ve para:** ekranda `formatNumber` ve `formatPrice` (tr-TR) kullanılır. Evrakta dört ve daha çok haneli
  sayılar sondan üçlü gruplara nokta ile ayrılır, kesir virgülle yazılır (RYUE md. 16/7: 1.452; 10.545,72).
- **Büyük harf:** evrakta `text-transform: uppercase`, Word'de `w:caps` ve çıplak `.upper()` kullanılmaz; büyük
  harfli metin `tr_upper` ile üretilir ("i/İ", "ı/I" ayrımı — tasarım §9.1-4).
- **Simgeler** `Icon` bileşeniyle verilir; metne ham "✓" / "⚠" yazılmaz.
- **İndirilen dosya adı** belge adı + kapsam + tarih taşır (`lib/download.ts` `dosyaAdi`):
  `Kurtarma-Anahtarı-Çıktısı_31.10.2026.pdf`. Kimlik numaralı ad (`belge_3.pdf`) masaüstünde neye ait olduğunu
  söylemez. İstisna şifreli yedektir: `oab-defteri-yedek-yyyy-aa-gg` (adlar sıralanınca tarih sırası çıksın diye).

## 4. Sayfa ve gezinme adları

Kural: gezinme etiketi kısa, sayfa başlığı (h1) tam addır ve üst çubuktaki başlıkla AYNIDIR (`AppShell.tsx`
`PAGE_TITLES`; eşlik `App.test.tsx`'te sınanır). Adresi tanınmayan sayfada üst çubukta "OAB Defteri" yazar. Gezinme
kartının (Genel Bakış) başlığı gittiği sayfanın h1'idir. Adrese bağlı olmayan program durumu ekranları üst çubuğa
kendi h1'lerini yazar (§4.2). Sekme adları Başlık Düzenindedir; sekme adreste `?tab=` ile tutulur, böylece başka
ekranlar ve kılavuz doğrudan sekmeye bağlanır. Kılavuzda ekran, sekme ve düğme adları buradaki ve ekrandaki metinle
birebir yazılır ("Ayarlar → Güvenlik"). Ekranlar fazlarla geldikçe buraya işlenir.

*Aşağıdaki tablolar F1b 0. adımdaki durumdur (31.10.2026); kaynak `AppShell.tsx` (`NAV_ITEMS`, `PAGE_TITLES`),
sayfaların h1'leri ve sekme tanımlarıdır.*

### 4.1 Sayfalar

| Gezinme etiketi | Sayfa başlığı (h1 = üst çubuk) | Adres | Not |
|---|---|---|---|
| Genel Bakış | Genel Bakış | `/` | Ana sayfanın tek adı. Altındaki açıklama: "Okul-aile birliğinin işlerini yürüttüğü yerel araç." |
| Kişiler | Kişiler | `/kisiler` | Bugün öğrenci, öğretmen ve diğer personel sicili ile e-Okul aktarımı (aile iskeleti; F1b 5. adımda personel ve veli listesine döner) |
| Ayarlar | Ayarlar | `/ayarlar` | Altında "Diğer Ayarlar" bölümü ve **Kurulum Sihirbazı** kartı |
| Kılavuz | Kullanım Kılavuzu | `/kilavuz` | Bugün tek bölüm: **Programın Konumu**. Bölümler her fazın özellikleriyle yazılır |
| Hakkında ve Lisans | Hakkında ve Lisans | `/hakkinda` | Kenar çubuğunun altında, ana gezinmenin dışında. Kartları: **Program** (tanım ve konum) · **Geliştirici** (iletişim) · **Ücretsiz ve Ticari Olmayan Kullanım** · **Üçüncü Taraf Bileşenler** · **Teknik Bilgiler** |
| — | Kurulum Sihirbazı | `/kurulum` | Menüde yoktur. İlk açılışta kurulum kapısı buraya getirir; kurulumdan sonra Ayarlar'ın altındaki **Kurulum Sihirbazı** kartıyla açılır |

Ana gezinmenin sırası: Genel Bakış · Kişiler · Ayarlar · Kılavuz. Görevli kipinde gezinme bağlantıları gösterilmez,
her adreste görevli ekranı durur (aile iskeleti; F1b 1. adıma dek). Planlanan ekranlar: Kullanıcılar F1b 2. adımda
(plan §2.2; tasarım §14); Okul Bilgileri bugün Ayarlar'ın sekmesidir, OAB alanları F1b 4. adımda gelir; Birlik Dönemi,
Kişiler (OAB'nin kişi türleriyle), Organlar, Temsilciler ve Pano (yol haritası) F1c'dedir (plan §2.3). Adları ekran
gelince buraya işlenir.

### 4.2 Program durumu ekranları

Bunlar adres değildir; program durumuna göre sayfanın yerine gelir. **Üst çubuk başlığı ekranın h1'idir:** ekran
açıkken kendi h1'ini üst çubuğa yazar (`ui/DurumBasligi.tsx`; `UstCubukBasligi.test.tsx`).

| Durum | Başlık |
|---|---|
| Kilitli | **Kayıtlar kilitli** |
| Görevli kipi | **Görevli Kipi** (aile iskeleti; F1b 1. adımda kalkar) |
| Güvenlik dosyası yok ya da bozuk | **Güvenlik dosyası bulunamadı ya da okunamıyor** |
| Yedekten geri yüklendi | **Programı kapatıp yeniden açın** |

Pencere açılmadan çıkan açılış iletilerinin başlıkları (masaüstü ileti kutusu; `desktop/errors.py`): **Program sürümü
eski** (eski program, yeni veri — çıkış kodu 4) · **Veritabanı bozuk** · **Veritabanı güncellenemedi** · **OAB
Defteri zaten çalışıyor** · **Pencere açılamadı** · **Program başlatılamadı** · **OAB Defteri açılamadı** (genel).
İletinin gövdesi sonucu, ikinci paragrafı yapılacak işi söyler.

Üst çubuktaki kip göstergesinin adları (aile iskeleti; F1b 1. adıma dek): kip adı **Yönetici kipi** / **Görevli
kipi**; düğmeler **Görevli kipine geç** (kısayol Ctrl+Shift+G), **Yönetici kipine geç**, **Kilitle**. Her durumda
görünen **Çık** düğmesinin pencereleri: **Programdan çıkılsın mı?** (onay) / **Programdan çık** (görevli kipinde,
yönetici parolasıyla) · **Program kapanıyor**.

### 4.3 Sekmeler

İlk sekme varsayılandır.

| Sayfa | Sekmeler, sırasıyla (`?tab=` değeri) |
|---|---|
| Kişiler | **Öğrenciler** (`ogrenciler`) · **Öğretmenler ve Diğer Personel** (`personel`) · **Ayrılış Havuzu** (`havuz`) |
| Ayarlar | **Ders Yılları** (`ders-yillari`) · **Kapalı Günler** (`kapali-gunler`) · **Şubeler** (`subeler`) · **Okul Bilgileri** (`okul`) · **Güvenlik** (`guvenlik`) · **Güncelleme** (`guncelleme`) |

Kişiler'in Öğrenciler sekmesi F1b 5. adımda sökülür (plan §2.2).

Pencere başlıkları (Dialog): **Yeni öğrenci** / **Öğrenciyi düzenle** · **Yeni kişi** / **Kişiyi düzenle** ·
**Parolayı değiştir** · **Yönetici kipine geç**. Onay diyaloglarının başlıkları (soru, §3): **Ders yılı
aktifleştirilsin mi?** · **Şube katalogdan kaldırılsın mı?** · **Kapalı gün silinsin mi?** · **Öğrenci ayrıldı olarak
işaretlensin mi?** · **Öğrenci sicilden silinsin mi?** · **Kişi ayrıldı olarak işaretlensin mi?** · **Kişi sicilden
silinsin mi?** · **Bu iki kayıt aynı kişi mi?** · **Kurtarma anahtarı yenilensin mi?** · **Yedekten geri yüklensin
mi?** · **Güvenlik dosyası sıfırlansın mı?**. Kişiler'deki içe aktarma panelleri: **e-Okul Raporundan veya Şablondan
Öğrenci Aktar** · **e-Okul Raporundan veya Şablondan Öğretmen ve Diğer Personeli Aktar**.

### 4.4 Kurulum Sihirbazı adımları

Adım rayındaki adlar, sırasıyla: **Yönetici Parolası** · **Okul Bilgileri** · **Ders Yılı ve Kapalı Günler**. İlk
adım atlanamaz. Adımlar arası düğmeler: **Geri**, **Devam** (1. adım), **Kaydet ve devam et** (2. adım), **Kurulumu
tamamla** (son adım).

F1b'de sihirbazın ilk üç adımı OAB'nin düzenine döner: yönetici hesabı ve parolası + kurtarma anahtarı · okul kartı ·
ders yılı, dönemler, kapalı günler (plan §2.2; tasarım §5.1, §14). Geçiş kurulumunun adımları sonra gelir: ilk birlik
dönemi ve görevdeki kurul F1c'de, birliğin banka hesabı ve açılış (devreden) bakiyesi F3'te. Adların yeni hâli adım
gelince buraya işlenir.

### 4.5 Genel Bakış kartları

Sırasıyla: **Başlangıç Yol Haritası** (kurulumdan sonra; bütün maddeler bitince gizlenebilir; kurtarma anahtarı
doğrulanmamışsa uyarı kartın başındadır. Maddeler bugün: e-Okul aktarımları, öğrenciye kapalı günler ve kurtarma
anahtarının müdürlükte kapalı zarfta saklanması; parolanın paylaşılmasını öğütleyen madde yoktur — §1 "Parola") ·
**Son Oturumu Kontrol Edin** (yalnız önceki oturum düzgün kapanmadıysa; düğme **"Kontrol ettim"**) · **Ayrılış
Havuzu** (yalnız havuz boş değilken, yalnız sayı: "N kişi ayrılış kararı bekliyor" → Kişiler → Ayrılış Havuzu) ·
**Şifreli Yedeği USB Belleğe Alın** (yalnız son şifreli yedek indirmesinden hatırlatma süresi — varsayılan 30 gün,
ayarla 7-90 — geçince; hiç indirme yoksa yönetici parolası kurulduktan 7 gün sonra: "Son şifreli yedek gg.aa.yyyy
tarihinde indirildi (N gün önce)." / "Bu bilgisayarda henüz şifreli yedek indirilmedi."; bağlantı **"Ayarlar →
Güvenlik'i aç"**; program dosyanın USB belleğe kopyalandığını bilemez, kart "son indirme" der) · **Kişiler** ·
**Ayarlar** (gezinme kartları).

OAB'nin pano kartları F1c'de gelir (tasarım §7.10).

### 4.6 Ayarlar → Güvenlik kartları

Sırasıyla: **Yönetici Parolası ve Şifreleme** (durumu, şifrelenen alanları, **"Parolayı değiştir"** ve
**"Kilitle"** düğmelerini taşır) · **Kurtarma Anahtarınız** (yalnız yeni üretilmiş anahtar beklerken) · **Kurtarma
Anahtarını Doğrula** (yalnız anahtar doğrulanmamışken; üstünde "Kurtarma anahtarı doğrulanmadı" uyarısı) ·
**Kurtarma Anahtarını Yenile** · **Kurtarma anahtarı çıktısı** (belge adı, §2; düğme **"PDF olarak kaydet"**) ·
**Şifreli Veritabanı Yedeği** (düğme **"Şifreli yedeği indir"**, son indirme cümlesi, hatırlatmanın durumu ve
**"Hatırlatma süresi"** seçimi) · **Yedekten Geri Yükleme**.

Kart başlıkları durumla DEĞİŞMEZ (§3 "Başlık sabit addır"): kullanıcıya "Ayarlar → Güvenlik → Yönetici Parolası ve
Şifreleme" diye yol tarif edilebilsin.

### 4.7 Güncelleme ekranının adları

Ekran **Ayarlar → Güncelleme** (`?tab=guncelleme`); kart **Uygulama Güncellemesi**. Düğmeler **"Şimdi denetle"**
(sürerken **"Denetleniyor…"**) · **"Doğrula ve indir"** (sürerken **"İndiriliyor…"**; yalnız Windows'ta); kutular
**Kurulu sürüm** · **Yayımlanan son sürüm**; iletiler **"Uygulama güncel."** · **"Yeni sürüm hazır: …"** · snackbar
**"Kurulum dosyası doğrulanarak indirildi."**. GitHub'a ulaşılamazsa ileti **"GitHub'a ulaşılamadı; okul ağında
engellenmiş olabilir. Yeni sürümü indir.okulapp.org'dan elle denetleyebilirsiniz."** (sunucudaki
`updates.ULASILAMADI_MESAJI` ile ön yüzdeki `ULASILAMADI_METNI` birebir aynıdır). Altında elle denetleme bağlantısı
**okulapp.org/oab-defteri** (dış tarayıcıda açılır). Pardus'ta indirme düğmesi yoktur; ekran güncellemenin paketle
yapıldığını söyler.

Elle denetim yeni sürüm bulursa kabukta **güncelleme bandı** durur (Ayarlar'da ve görevli kipinde gizli;
`UpdateBanner.tsx`). **Bugünkü sapma:** bant aynı kavramlar için aileden kalan adları kullanır: "OAB Defteri … hazır.
Çalışan sürüm: …", düğme **"Güncellemeyi indir"** (sürerken "İndiriliyor…") · **"Daha sonra"**. Bu adlar F1b 6. adımda
§1 "Sürüm" satırındaki **"kurulu sürüm"** ve **"Doğrula ve indir"** adlarına uydurulur.

## 5. Kişisel veri ve metin

Dayanak CLAUDE.md §2 altın kural 5 ve tasarım §3.4, §9.1-5'tir.

- **Hata ve uyarı metnine, günlüğe, uç yoluna ve dosya adına kişi adı, okul numarası ya da T.C. kimlik numarası
  yazılmaz.** Günlüğe yalnız sayılar yazılır ("N yeni, M güncellenen"). Kurtarma anahtarı ve parola da hiçbir
  günlüğe, iletiye ya da dosya adına girmez.
- **T.C. kimlik numarası** varsayılan kapalıdır (K9); açılırsa yalnız bağışçı alanında, şifreli ve maskeli tutulur
  ve hiçbir belgeye ve dosyaya girmez (tasarım §9.1-5).
- **Veli verisi en azdır:** e-Okul'dan yalnız veli adı-soyadı ve öğrencinin sınıfı alınır; telefon, adres, T.C.
  kimlik no ve öğrenci no alınmaz; liste dönem kapanışında silinir (T5). Veli adı taşıyan katılım cetvelini ve teslim
  çizelgesini yalnız program yöneticisi basar, program dosyasını saklamaz (tasarım §9.1-2).
- **Duyuru ve ilan çıktılarında** (ilan panosu, internet sayfası) kişi adı yoktur, başkanınki de; imza "Okul-Aile
  Birliği Yönetim Kurulu" (servis ilanında "Taşımacıyı Tespit Komisyonu") olur. Tek istisna mevzuat gereği taşımacı
  listesidir: yalnız taşımacının ad/unvanı, araç plakası ve güzergâh
  ([Servis U-E md. 10/3](mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10); D5).
- **Kişi adı taşıyan iç belgeler** "Kişisel veri içerir — asılmaz, okul dışına verilmez" dipnotunu taşır. Adli sicil
  ve sağlık belgelerinin içeriği basılmaz, yalnız "teslim alındı" ve tarih basılır (tasarım §9.1-5).
- **Aydınlatma:** kişisel verinin toplandığı yerde kısa aydınlatma paragrafı bulunur, tam metin Kişisel veri
  aydınlatma metnidir (E04). Metin e-Okul aktarımından **önce** gösterilir
  ([KVKK md. 10/1](mevzuat/6698-kvkk.md#madde-10) "elde edilmesi sırasında"): F1b 5. adımda içe aktarma ekranında,
  belgesi F2'de (plan §2.2).
- **Kilit ekranı kişi adı göstermez;** hesaplar rol etiketiyle listelenir (tasarım §4.4.3, F1b).
- **Şifreleme dürüst anlatılır:** metin olduğundan güçlü bir koruma vadetmez; şifrelenen alanları ve şifrelenmeyenleri
  ayrı ayrı söyler, tam disk şifrelemesi olmadığını yazar (§1 "Şifreleme"; tasarım §4.4.6).
- **Destek ve hata bildirimi:** iletiye öğrenci, veli ya da personel bilgisi, gerçek veri içeren ekran görüntüsü,
  yedek ya da veritabanı dosyası eklenmez; Hakkında sayfası bunu söyler.
- Bugünkü Kişiler ekranındaki öğrenci sicili (ad-soyad, okul numarası, sınıf) aile iskeletinden kalır ve F1b 5.
  adımda sökülür (plan §2.2); o güne dek okul numarası şifreli saklanır ve yalnız numaranın tamamıyla aranır.
