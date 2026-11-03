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

**Bugünkü durum.** Program F1b'dedir. Aile iskeletinin tek yönetici parolası ve görevli kipi F1b 1. adımda
kalktı: herkes programı kendi hesabıyla ve kendi parolasıyla açar. Öteki aile düzenleri (öğrenci sicili) F1b
adımlarında OAB'nin düzenine döner ([plan §2.2](plan/2026-10-31-f0-f1-plani.md)). Sözlük bugün ekranda olanı
yazar; değişeceği bilinen satır bunu yanında söyler. Ekrandaki metin değişince buradaki satır aynı değişiklikte
güncellenir.

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
| Parola | **parola**; her hesabın kendi **parolası** (kilit ekranında alanın adı **"Parola"**); ilk girişte değiştirilen **geçici parola** ve 180 günü dolan parola kilit ekranında yenilenir: **"Yeni parola"** + **"Parola (tekrar)"**, düğme **"Parolayı yenile ve aç"** (tasarım §4.4.5, TK15). Kural metni **"En az 8 karakter; küçük harf, büyük harf, rakam ve simge içerir. Başında ve sonunda boşluk olamaz."**; yeni parolanın altında **parola gücü** (**Zayıf** · **Orta** · **İyi** · **Güçlü**) ve parola cümlesi önerisi (en az 12 karakter). Kurulum sihirbazının ilk adımında hesabın ilk parolası **"Parola"** + **"Parola (tekrar)"**; Ayarlar → Güvenlik'te her hesap kendi parolasını **"Parolayı değiştir"** penceresinde değiştirir (**"Mevcut parola"** · **"Yeni parola"** · **"Parola (tekrar)"**, düğme **"Uygula"**, beklerken **"Denetleniyor…"**; snackbar **"Parolanız değiştirildi."**); oturumdaki hesabın parolasını isteyen alanların adı (kurtarma anahtarını yenileme, yedekten geri yükleme) **"Parolanız"**dır. Zorunlu yenilemenin iletisi: "Parolanızı yenilemeniz gerekiyor (geçici parola ya da süresi dolan parola). Yeni parolanızı belirleyin." | parola anlamında **"şifre"**; "uygulama parolası"; "PIN"; tek bir program parolası anlamında **"yönetici parolası"** | Program yöneticisi hesabı ve parolası kurulum sihirbazının ilk adımıdır; kurulmadan kişi kaydı yapılamaz (ileti: "Önce program yöneticisi hesabını kurun"). Kural ve iletiler sunucununkiyle birebirdir ("Parola en az 8 karakter olmalıdır.", "Parola en çok 128 karakter olabilir.", "Parolanın başında ya da sonunda boşluk olamaz.", "… eksik: büyük harf, simge.", "Yeni parola eskisiyle aynı olamaz.", "Parolalar eşleşmedi."); güç göstergesi programın yerel önerisidir, sunucu kararı değildir. Her ileti sorunlu alanın altında çıkar: "Parola hatalı." (mevcut parola yanlış) **Mevcut parola** ya da **Parola** alanının, politika iletisi **Yeni parola**nın, "Parolalar eşleşmedi." **Parola (tekrar)**ın altında; kural metni yeni parola alanına bağlıdır, ekran okuyucu alana gelince okur. **Parola paylaşılmaz, herkes kendi hesabıyla çalışır** (T1; [BSG Yön. md. 7/2](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [9/2-e](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) — programa kıyasen, tasarım TK9): metin parolanın başkasıyla paylaşılmasını ya da birden çok kişide bulunmasını öğütlemez. Parola hiçbir belgede yoktur (tasarım §9.1-5). "Şifre" yalnız şifreleme anlamında kalır ("şifreli yedek", "şifrelenen alanlar"); mevzuattan alıntıda mevzuatın sözcüğü korunur. Programın parolası işletim sisteminin yetkisiyle karışmaz: Windows'un ve Pardus'un (`sudo`) yetkisi için **"yönetici yetkisi"** denir |
| Program yöneticisi ve roller (F1b) | `yonetici` rolünün etiketi **"Program yöneticisi (OAB'den sorumlu müdür yardımcısı)"**; öteki roller **başkan** · **başkan yardımcısı** · **muhasip** · **sekreter** · **Denetleme Kurulu** · **okul müdürü** | programın yöneticisi için "sistem yöneticisi", "admin" | Tasarım §4.4. "Sistem yöneticisi" BSG Yön. [md. 4/1-s](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)'de Bakanlığın ve il/ilçe millî eğitim müdürlüklerinin bilişim personelidir; programın yöneticisiyle karıştırılmaz. Rolün açık olmadığı bir işlem denenirse ileti tek ve sabittir: **"Bu işlem hesabınızın rolüne açık değil."** (rol etiketi, uç ve kod yazmaz; program yöneticisine de düşebilir — rol-izin matrisi tasarım §4.4.2). Yedekten geri yüklemenin rol iletileri §1 "Yedek" satırındadır (Başlat menüsündeki kısayol ve komut rol kapısından geçmediği için iletileri ayrıdır). Kullanıcılar ekranı ve rol süzmesinin ekranları F1b 2. adımda gelir |
| Hesap (F1b) | **hesap** (bir hesap = bir kişi + bir rol); hesabın kilit ekranında görünen adı **tanıtıcı** (`yonetici`, `muhasip`, `dk-1`; gerçek ad değildir); kilit ekranının satırı **rol etiketi** (büyük; program yöneticisi için kısa **"Program yöneticisi"**, aynı rolde birden çok hesapta sıra no'lu: "Denetleme Kurulu 2") + altında **tanıtıcı** (küçük); grubun adı **"Hesap"**; askıdaki hesap (hatalı deneme ya da üyelik/görev askısı) **"askıda — program yöneticisine başvurun"**, kaydı okunamayan **"Hesap kaydı okunamadı"** — ikisi de seçilemez (açık olmayan başka bir satır olursa **"giriş kapalı — program yöneticisine başvurun"**); hesap sahibinin **ad-soyadı** (kurulumda alan **"Ad-soyad"**; şifreli saklanır, kilit ekranında görünmez); kurulumda tanıtıcının alanı **"Tanıtıcı"** (varsayılan `yonetici`; kural metni **"Kilit ekranında herkese görünen hesap adıdır; gerçek ad yazılmaz. Küçük harfle başlar; küçük harf, rakam, nokta, tire ya da alt çizgi içerir."**); tanıtıcı ad-soyaddaki üç harften uzun bir sözcüğü içeriyorsa uyarı (engel değil) **"Tanıtıcı hesap sahibinin adını içeriyor. Tanıtıcı kilit ekranında herkese görünür; rolden türeyen bir tanıtıcı seçmeniz önerilir."**; tanıtıcının ve ad-soyadın iletileri (kurulum ve Kullanıcılar'ın **"Yeni hesap"** penceresi) **"Tanıtıcı boş olamaz."** · **"Tanıtıcı 2-32 karakter olmalıdır; küçük harfle başlar, küçük harf, rakam, nokta, tire ya da alt çizgi içerir."** · **"Hesap sahibinin adı-soyadı boş olamaz."** · **"Hesap sahibinin adı-soyadı en çok 150 karakter olabilir."**; belge **Hesap teslim pusulası** | — | Kilit ekranında ve üst çubukta kişi adı gösterilmez (tasarım §4.4.3; §5). Ayarlar → Güvenlik'teki **Hesap ve Parola** kartı oturumu rol etiketi ve tanıtıcıyla yazar (**"Bu oturum: Program yöneticisi · tanıtıcı yonetici"**). Tanıtıcı uyarısı gönderimden önce de ekrandadır; karşılaştırma Türkçe harfleri katlar ("Şükrü" ≡ "sukru"). Tek seçilebilir hesap seçili gelir. Hesaplar dönemliktir (tasarım §4.4.1). Hesap açma ve Kullanıcılar ekranı F1b 2. adımda gelir. Hesabın güvenlik dosyasındaki **parola kaydı** (§1 "Denetim izi") hesabın kimliğine bağlıdır: başka hesabın kaydına çevrilen kayıt parolayla açılmaz, ileti yanlış parolanınkidir ("Parola hatalı."). Kimliğe bağlı biçimin işaretini taşımayan kayıt parolayla hiç açılmaz. Hesap kaydı, güvenlik dosyasındaki GÜNCEL parola kaydının özetini taşır: eski bir parola kaydı (güvenlik dosyasının arşiv kopyasından ya da önceden alınmış bir kopyadan) geri konursa eski parolayla da açılmaz. Program böyle kayıt yazmaz; sahada yalnız program dışı değişiklikle doğar (F1b 1. ve 2. adımın deneme kurulumları silinip yeniden kurulur). Kilit ekranı hatalı deneme saymadan, mühür iletisinin kalıbıyla **"Bu hesabın parola kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. Denetleme Kuruluna bildirin. Program yöneticisinin hesabıysa “Parolamı unuttum” yolundan kurtarma anahtarıyla açılır; öteki hesapların parolasını program yöneticisi sıfırlar."** der (iki hâlde de aynı ileti; eski kayıtta olay Denetleme Kurulunun panosuna da düşer). Çıkış kurtarma anahtarı zarfının üçüncü durumudur (güvenlik dosyası ya da kayıtlar program dışından değiştirildiğinde): program yöneticisinin hesabı kurtarma anahtarıyla açılır ya da başka bir program yöneticisi parolasını sıfırlar; öteki hesapların parolasını program yöneticisi sıfırlar (sıfırlama kaydı yeniden yazar). Genel Bakış'ın **Hesaplar ve Güvenlik Dosyası** kartı bu hesapları ayrı listede gösterir (ekranı F1b 2. adımın (d) alt commit'inde) |
| Kullanıcılar (F1b) | ekran **Kullanıcılar** (yalnız program yöneticisi); hesap açma penceresi **"Yeni hesap"**, parola sıfırlama penceresi **"Parolayı sıfırla"**; eylemler **kapama**, **askıdan çıkarma**, **parola sıfırlama**, **hesap teslim pusulası** (aşağıda "Hesap teslim pusulası (F1b)"); satırın durumu **"Açık"** · **"Parola yenilenmeli"** · **"Askıda"** · **"Kapalı"**, askının nedeni **"Hatalı parola denemesi"** · **"Üyelik düştü"** · **"Görev bölümü"** · **"Nedeni kayıtlı değil"**; girişi kapalı hesabın nedeni **"Hesap kapalı."** · **"Hesap askıda; askıdan çıkarılınca giriş açılır."** · **"Parola kaydı bu bilgisayarın güvenlik dosyasında yok; parolasını sıfırlayın."** · **"Parola kaydı hesap kaydındakiyle uyuşmuyor; parolasını sıfırlayın."**; yapılamayan eylemin nedeni **"Kendi hesabınızı kapatamazsınız."** · **"Kendi parolanızı buradan sıfırlayamazsınız; Ayarlar → Güvenlik'teki “Parolayı değiştir” penceresini kullanın."** · **"Kendi hesabınızın teslim pusulasını basamazsınız."** · **"Hesap kapalı; kapalı hesap yeniden açılmaz, yeni hesap açılır."** · **"Son program yöneticisi hesabı kapatılamaz."** · **"Askıdaki hesabın parolası sıfırlanamaz; önce hesabı askıdan çıkarın."** · **"Hesap askıda değil."** · kaydı ya da izi tutmayan hesapta **"Hesap kaydı program dışından değiştirilmiş görünüyor; program bu kayda dokunmaz. Denetleme Kuruluna bildirin."** ya da (izde boşluk) **"Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş görünüyor; program bu kayda dokunmaz. Denetleme Kuruluna bildirin."**; role yeni hesap açılamıyorsa **"Bu rolde açık bir hesap zaten var; önce onu kapatın."** · **"Denetleme Kurulu için en çok 3 hesap açık olabilir."** · yeri tutan hesabın kaydı ya da izi tutmuyorsa **"Bu roldeki hesabın kaydı ya da denetim izi program dışından değiştirilmiş görünüyor; o hesap kapatılamadığı için bu role yeni hesap açılamaz. Denetleme Kuruluna bildirin; kayıtlar sağlam bir yedekten geri yüklenebilir."**; program yöneticisi rolünde bilgi **"Program yöneticisi değiştiğinde kayıtların anahtarının yenilenmesi programın sonraki bir sürümünde gelecek; bu hesap ikinci bir program yöneticisi hesabı olarak açılır."**; öteki iletiler **"Hesap bulunamadı."** · **"Bu tanıtıcı açık bir başka hesapta kullanılıyor."** · **"Geçerli bir rol seçin."** | "kullanıcı yönetimi", "admin paneli"; rol etiketinde sıra no ("Denetleme Kurulu 2" yalnız kilit ekranındadır) | Plan F1b-2 "Kullanıcılar uçları"; tasarım §4.4.2 Kullanıcılar satırı, §4.4.5. Liste bütün hesapları gösterir: giriş yapamayanlar ve kapalılar dahil. Eylemleri ve nedenlerini program hesaplar; ekran yalnız gösterir. **Geçici parola** ekranda gösterilmez, kopyalanmaz, hiçbir yanıtta, günlükte, denetim izinde ya da iletide yer almaz; hesap sahibine kapalı zarfta verilir (okul uygulaması; [BSG Yön. md. 10/1](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) parolanın görünür yere yazılmasını yasaklar, [9/2-e](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) paylaşılmasını). Sunucu yalnız parola kuralını denetler (§1 "Parola"); öneriyi ve pencere metinlerini ekran (F1b 2. adımın (d) alt commit'i) yazar. Hesap teslim pusulası kapalı hesaba, kaydı ya da izi tutmayan hesaba ve oturumdaki hesabın kendisine basılmaz (nedenleri yukarıdaki iletilerdir); askıdaki hesaba basılır |
| Hesap teslim pusulası (F1b) | belge **Hesap teslim pusulası** (başlığı **"HESAP TESLİM PUSULASI"**; yalnız PDF, indirilen dosya `Hesap-Teslim-Pusulası_gg.aa.yyyy.pdf`); künye tablosu **"Tanıtıcı"** · **"Rol"** (sıra no'suz rol etiketi) · **"Açılış tarihi"**; tablo **"Bu programda sizin işiniz"**, satırları rol-izin matrisinin satır adlarıdır (yalnız rolün bugün yazabildiği satırlar): **"Okul bilgileri, ders yılı, kapalı günler, birlik döneminin açılması ve kapanması"** · **"Kişiler, organlar, temsilciler, yönetim kurulu görev bölümü, yedek üye çağrısı"** · **"Genel kurul"** · **"Yönetim kurulu toplantısı, katılım, karar taslağı"** · **"Gelir-gider kaydı, banka eşleme, makbuz koçanı ve yaprağı, kasa"** · **"Harcama zinciri"** · **"Tahmini bütçe, ilan, aylık bildirim, faaliyet raporu"** · **"Denetim: Denetleme Kurulu görev bölümü, denetim planı, kontrol listesi, bulgu, ara ve nihai rapor, olağanüstü genel kurul çağrısı, kayıt bütünlüğü denetimi"** · **"Müdür yazısı: birlik başkanına yazılı uyarı"** · **"Takvim, pano ve uyum kaydı"** · **"Gelen-giden evrak, belge dosyası"** · **"Devir-teslim ve dönem kapanışı"** · **"Kantin ve servis"** · **"Personel"** · **"Denetim izi"** · **"Erişim günlüğü"** · **"Kullanıcılar: hesap açma, kapama, askıdan çıkarma, parola sıfırlama, hesap geçişi"** · **"Güvenlik: kurtarma anahtarı, yedek indirme, geri yükleme, kayıtların anahtarının yenilenmesi"** · **"Ayarlar: boşta kilit süresi, küçük alım sınırı, kural sürümü, bağışçı kimlik numarası"** · **"Kişisel veri içeren çıktı ve dışa aktarım"** · **"Güncelleme denetimi"** · **"Kendi parolanızı değiştirme, Kilitle, Çık"**; bölüm paragrafları başlık + iki nokta + cümlelerdir: **"İlk girişte"**: **"(1) OAB Defteri'ni açın; kilit ekranında tanıtıcısı “<tanıtıcı>” olan hesabı seçin."** **"(2) Kapalı zarftaki geçici parolayı “Parola” alanına yazıp “Aç” düğmesine basın."** **"(3) Program yeni parola ister: kendi belirlediğiniz parolayı “Yeni parola” ve “Parola (tekrar)” alanlarına yazıp “Parolayı yenile ve aç” düğmesine basın."** **"(4) Bundan sonra programı yalnız kendi parolanızla açarsınız; geçici parola artık geçmez."**; **"Parola kuralları"**: **"Parolanız en az 8 karakterdir; küçük harf, büyük harf, rakam ve simge içerir; başında ve sonunda boşluk olamaz."** **"İlk iki kural Millî Eğitim Bakanlığı Bilgi ve Sistem Güvenliği Yönergesinin (BSG Yön.) md. 9/2-a ve 9/2-b bentlerindedir."** **"Parolanızı en geç altı ayda bir değiştirirsiniz (BSG Yön. md. 9/2-ç); 180 gün dolunca program yeni parolanızı ister."**; **"Kilitleme"**: **"Program N dakika işlem yapılmazsa kendiliğinden kilitlenir; yeniden açmak için parolanız sorulur (BSG Yön. md. 10/2; programa kıyasen)."** **"Bilgisayarın başından ayrılırken “Kilitle” düğmesine basın (BSG Yön. md. 7/4; programa kıyasen)."** **"Parola üst üste yanlış girildikçe bekleme süresi artar."** ve program yöneticisi dışındaki hesaplarda **"Üst üste 10. yanlış denemede hesap askıya alınır; askıyı program yöneticisi kaldırır (BSG Yön. md. 7/3, 9/2-c; programa kıyasen)."**, program yöneticisinin pusulasında **"Program yöneticisi hesabı yanlış denemede askıya alınmaz."**; imzanın üstünde **"İlk parolanız ayrı kapalı zarftadır; parolanızı kimseyle paylaşmayın, görünür yere yazmayın (BSG Yön. md. 9/2-e, 10/1)."**; imza blokları **"Teslim eden"** / **"Program yöneticisi (ad-soyad, imza, tarih)"** ve **"Teslim alan"** / **"Hesap sahibi (ad-soyad, imza, tarih)"**; dipnot **"Kişisel veri içerir — asılmaz, okul dışına verilmez."** | pusulada **parola alanı** (ne değer ne boş satır), **ad-soyad** (hesap sahibinin de basanın da); kodlar (`E63` yalnız altlıkta, §2 istisna 1); RYUE unsurları (sayı, konu, muhatap) ve konum cümlesi; açılımı dipnotta bırakılan kısaltma (§3 "Kısaltma") | Plan F1b-2 "E63 hesap teslim pusulası"; tasarım §4.4.5, §9.1-5, §9.5-§9.6. Yalnız program yöneticisi basar (Kullanıcılar); antet okulundur. `<tanıtıcı>` hesabın tanıtıcısı, `N` okulun boşta kilit süresidir (Ayarlar → Güvenlik). Rolün işleri satır düzeyindedir: satırın bir bölümünün ekranı sonraki bir fazdaysa da satırın adı basılır; program yöneticisinin satırları tek sayfaya sığsın diye kısaltılmıştır ("hesap teslim pusulası" Kullanıcılar satırının hesap açma bölümündedir). Atıflar korpusla doğrulanmıştır ([BSG Yön. md. 7](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [9](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9), [10](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)): md. 9/2-a, b, ç ve e uygulamalara doğrudan bağlanır (md. 9/1 "her türlü uygulama"), md. 10/1 de ("sistemlerde kullanılan şifreler"); md. 7 Bakanlığın kullanıcı hesaplarını, md. 10/2 personelin bilgisayarını, md. 9/2-c Başkanlığın kilitleme politikasını düzenlediği için "programa kıyasen" anılır. Yönergenin adı ilk atıfta ("Parola kuralları") açık yazılır, kısaltma ardından parantez içindedir (§3 "Kısaltma"; açılımı dipnota bırakılmaz). Artan bekleme, 180 günlük yenileme isteği ve baştaki-sondaki boşluk yasağı programın kurallarıdır, atıf almaz. Kapalı zarf okul uygulamasıdır. Dosya saklanmaz: PDF bellekten verilir; basım denetim izine düşer (belge kodu ve dosyanın özeti), erişim günlüğüne düşmez (pusula kişisel veri basmaz). Teslim alanın elle yazdığı ad ve imza kişisel veridir: kâğıt kişisel veri dipnotunu taşır |
| Hesap kaydının ve denetim izinin tutmaması (F1b) | kilit ekranında kaydı program dışından değiştirilmiş görünen hesap (mührü tutmayan ya da eski bir kopyadan geri konmuş: denetim izindeki son kaydını tutmayan) **"Hesap kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. Program yöneticisine ve Denetleme Kuruluna bildirin."**; denetim izinde hesabın son kaydından sonra silinmiş ya da sırası değiştirilmiş kayıt varsa **"Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş görünüyor; giriş açılmadı. Program yöneticisine ve Denetleme Kuruluna bildirin."**; hesap işlemlerinde (Kullanıcılar) aynı iki hâl **"Hesap kaydı program dışından değiştirilmiş görünüyor; kayda dokunulmadı. Denetleme Kuruluna bildirin."** ve **"Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş görünüyor; kayda dokunulmadı. Denetleme Kuruluna bildirin."**; geri yüklemedeki karşılıkları §1 "Yedek" satırındadır; denetim izine yazılamayan işlemde **"Denetim izine yazılamadığı için işlem yapılmadı. Denetim izi program dışından değiştirilmiş olabilir; program yöneticisine ve Denetleme Kuruluna bildirin."** | kullanıcı metninde "mühür", "zincir", "sıra no", "iz boşluğu", "kayma", ret kodları | İki ileti ayrılır: hesap kaydı değişmişse ilki, değişen denetim iziyse (izden ilgisiz bir satır silinmiş olsa da son kaydı ondan eski BÜTÜN hesaplar reddedilir) ikincisi; ikisinde de hatalı deneme sayılmaz, kayda dokunulmaz ve olay denetim izine düşer (program yöneticisi ve Denetleme Kurulu panosundaki **Değiştirilmiş Hesap Kaydı** kartı; ikinci hâlin kart metni F1b 2. adımın (d) alt commit'indedir). Hesap işleminde yalnız mührü tutmayan hesabın reddi denetim izine yazılmaz (tasarım §4.4.5 olayı kilit açılışında yazdırır); o hesap aynı panoda "Kaydı değiştirilmiş görünen hesaplar" listesinde görünür. Hesabın kendi son kaydı denetim izinin ortasından silinmişse (ondan sonra kayıt kalmışsa) de ikinci ileti çıkar (değişen denetim izidir). En yeni kayıtlarla birlikte silinmişse (kuyruk kesme) ya da hesabın denetim izindeki bütün kayıtları silinmişse, programın boşluğu arayacağı kayıt kalmaz ve ilk ileti çıkar. Kuyruk kesmeyi kilit açılışının çapa denetimi gösterir. Çıkış, değişiklikten önceki bir yedeğin kurtarma anahtarıyla geri yüklenmesidir (zarfın üçüncü durumu; §1 "Kurtarma anahtarı"). Denetim izine yazılamayan işlem hiçbir şey yazmaz (tasarım §4.6.2: iz yazılamazsa yazma yapılmaz) |
| Oturum (F1b) | kilidi açan hesabın **oturumu**; üst çubuktaki **oturum göstergesi** rol etiketini ve tanıtıcıyı gösterir; başka hesaba geçmek **Kilitle** + kendi hesabıyla açmaktır | kullanıcı metninde **"yönetici kipi"**, **"görevli kipi"**, "kip"; "kullanıcı değiştir" diye ayrı düğme; "öğrenci modu", "admin modu", "kiosk"; "kütüphane görevlisi", "öğrenci görevli", "masa" | Aile iskeletinin görevli/yönetici kipi F1b 1. adımda kalktı (tasarım TK14): herkes kendi hesabıyla açar, boşta süre dolunca program kilitlenir. Kilitlenmede ve kilit ekranından açılışta pencere içeriği yeniden yüklenir; açık form kaybolur (tasarım §13 D53) |
| Kilit ve çıkış | **"Kilitle"** (programı açık bırakır, kayıtları kilitler; kısayol **Ctrl+Shift+L**; ekran **"Kayıtlar kilitli"**, §4.2); uzun iş sürerken istenen kilit ertelenir, ekranda **"İşlem bitince kilitlenecek"**; **"Çık"** (programı kapatır; her durumda parolasız); kullanılmayan programın kendiliğinden kilitlendiği süre **boşta kilit süresi** (dakika) | — | Pencerenin çarpısı da programı kapatır; tepsi yoktur (T6). Çıkış diyalogları §4.2'dedir. Doğrulanmamış kurtarma anahtarı ekrandayken Kilitle önce sorar (**"Program kilitlensin mi?"**): kilitlenme anahtarı ekrandan kaldırır. Üst çubuktaki geri sayım ve ipucu (**"Program N dakika işlem yapılmazsa kilitlenir."**) yalnız kurulum tamamlandıktan sonra görünür. Boşta kilit süresi 3 ile 30 dakika arasındadır, varsayılanı 10'dur; Ayarlar → Güvenlik'in **Boşta Kilit Süresi** kartında (alan **"Boşta kilit süresi (dakika)"**, düğme **"Kaydet"**, snackbar **"Boşta kilit süresi N dakika olarak kaydedildi."**) yalnız açık oturumda değiştirilir (tasarım TK14). Süreyi her rol okur, yalnız program yöneticisi yazar; öteki rollerde sunucu "Bu işlem hesabınızın rolüne açık değil." der, alanın öteki rollerde salt okur gösterilmesi F1b 2. adımın ön yüz işindedir (§4.6). Mutlak oturum süresi yoktur |
| Kurtarma anahtarı | **kurtarma anahtarı**; kimliği **anahtar no** ve **üretim tarihi**; kilit ekranındaki yolu **"Parolamı unuttum"** → **"Kurtar ve aç"** (geri dönüş **"Parolayla açmaya dön"**) | "kurtarma kodu", "yedek parola", "ana anahtar" | Yalnız program yöneticisi içindir (kilit ekranında "Parolamı unuttum" yalnız program yöneticisi hesabı seçiliyken görünür; öteki hesaplarda **"Parolanızı unuttuysanız program yöneticisine başvurun."** yazar) ve **üç durumda** kullanılır: parolası unutulduğunda, kayıtlar yeni bilgisayara taşınırken ve bu bilgisayarın güvenlik dosyası kaybolduğunda ya da bozulduğunda yedekten geri yüklemede (o durumda parola yolu işlemez; tasarım §4.4.4). Anahtar panelinin uyarısı ve kurtarma anahtarı belgesi bu üçünü sayar; zarf "yalnız bu üç durumda" açılır; herkes programı kendi hesabıyla açar, öteki hesaplarda parolasını unutan program yöneticisine başvurur (tasarım §4.4.3). No her yeni anahtarda bir artar; belge ve yedek listesi hangi anahtarın hangi yedeği açtığını no ve tarihle gösterir (tasarım TK10). Ekranda kimlik **"Anahtar no 3 · üretim tarihi 01.11.2026"** biçimindedir (yeni anahtarın üstünde, Kurtarma anahtarı belgesi kartında ve yedek satırında); seçilen yedek için **"Bu yedek 3 numaralı, 01.11.2026 tarihli kurtarma anahtarıyla açılır."** yazar, bilinmiyorsa **"Bu yedeği hangi kurtarma anahtarının açtığı okunamadı."** Basılıp **okul müdürlüğünde kapalı zarfta** saklanır, veliye geçmez (T1, D3); PDF dosyası bilgisayarda bırakılmaz (tasarım §9.7). Panelden **Yazdır**'la basılan kâğıt da anahtarın altında **"Okul müdürlüğünde kapalı zarfta saklanır; veliye geçmez. Yalnız program yöneticisi içindir; parola paylaşılmaz, herkes programı kendi hesabıyla açar."** satırını taşır (tasarım §13 D50). Anahtar programda saklanmaz; hiçbir günlüğe, iletiye ya da dosya adına yazılmaz |
| Kurtarma anahtarı işlemleri | kart adları **Kurtarma Anahtarını Doğrula** ve **Kurtarma Anahtarını Yenile**; eylem **"yenileme"** (onay diyaloğu oturumu açan hesabın parolasını sorar: alan **"Parolanız"**); uyarı **"Kurtarma anahtarı doğrulanmadı"** | "anahtarı sıfırla", "anahtarı değiştir" | Bugünkü yenileme kayıtların anahtarını değiştirmez, kayıtlar yeniden şifrelenmez; yenilemeden önce alınmış yedekler başka bilgisayarda eski anahtarla açılır ve metin bunu söyler (tasarım §4.4.6). F1b'den sonra anahtarı yalnız program yöneticisi yeniler (tasarım TK9) |
| Şifreleme | **şifreli**, **şifrelenen alanlar**; "güçlü şifrelemeyle korunur"; dürüst sınır **"Şifreli alanlar en zayıf hesap parolası kadar korunur"**; çözülemeyen şifreli alanın ekrandaki karşılığı **"okunamadı"** (kişinin adı okunamazsa metinde **"Adı okunamayan kayıt"**, eylem adında **"Adı okunamayan kaydı düzenle"**; "kayıt kaydını" ikilemesi kurulmaz) | ayar ekranında ve iletide yöntem adları (Fernet, AES, X25519, Argon2id, HMAC); "veritabanı şifreli"; okunamayan alan için boş hücre | Şifrelenen şey belirli kişisel veri alanlarıdır; bu **tam disk şifrelemesi değildir** ve metin bunu açıkça söyler; tam koruma BitLocker ya da LUKS'tur (tasarım §4.4.6). Her hesabın parolası kayıtların anahtarını tek başına açar; Ayarlar → Güvenlik'in **Şifreleme** kartı ve Hakkında'nın **Dürüst Sınırlar** kartı bunu söyler. Okunamayan alan program dışından değiştirilmiş ya da bozulmuş kaydı gösterir (tasarım §13 D48); ekran onu "veri yok"la karıştırmaz, Genel Bakış'ta **Okunamayan Kayıt Alanları** kartı kişisiz sayıyı verir. Yöntem adları yalnız Hakkında'nın **Teknik Bilgiler** kartında geçer |
| Denetim izi (F1b) | **denetim izi** (her kaydın kimin hesabıyla, ne zaman ve ne türde yazıldığını gösteren, silinmeyen ve kayıtları birbirine bağlayarak yazılan kayıt); program her kilitlenmede ve düzenli kapanışta denetim izinin son kaydını işaretler: **kilit işareti**; kâğıda inen satır **"Kayıt no: N · Zincir: XXXX-XXXX"** (N son kaydın sırası, binlik ayırıcısız — kâğıda aynen geçirilen kimliktir; Zincir son kaydın mührünün ilk sekiz onaltılık hanesi, büyük harf, dörder dörder; Son Girişler kartında başlığı **"Denetim izinin son kaydı"**); kilit açılışındaki denetimin bulguları sade cümleyle: **"Denetim izinin son kayıtları silinmiş ya da veritabanı daha eski bir kopyayla değiştirilmiş (geri sarılmış) görünüyor."** · **"Program kilitliyken yazılan olaylardan bazıları denetim izinde yok; silinmiş olabilir."** · **"Denetim izinin zinciri kırık: kayıtlar arasındaki bağ tutmuyor."** · **"Kilit işareti bulunamadı; denetim izinin sonu denetlenemedi. …"** · yalnız bilgi olan **"Program kilitliyken bir sistem olayının (ör. günlük yedek) denetim izine yazımı yarıda kalmış: program kapanmış ya da kayıt yazılamamış (elektrik kesintisi, zorla kapatma ya da dolu disk olabilir). …"** · sırrı olmayan birinin eklediği kayıt **"Denetim izinde, türüne ya da yazılış biçimine uymayan bir kayıt var; program dışından eklenmiş olabilir."** · **"Kilit işareti son kilitlenmede yenilenememiş ya da eski bir kopyayla değiştirilmiş; denetim izinin sonu tam denetlenemedi."** (bütün bulgu cümleleri `modules/butunluk/metinler.ts`'te; tanınmayan bulguda **"Denetim izinde tanınmayan bir bulgu var."**); hesabın güvenlik dosyasındaki parolalı kaydı **parola kaydı** (düğme **"Güvenlik dosyasından sil"** — erişilebilir adı hangi hesabın kaydı olduğunu söyler: **"“eski-hesap” tanıtıcılı hesabın parola kaydını güvenlik dosyasından sil"**, tanıtıcı okunamazsa "Bu hesabın …"; sürerken **"Siliniyor…"**, snackbar **"Parola kaydı güvenlik dosyasından silindi."**); parola yenilenme bildirimi **"Parolanız gg.aa.yyyy tarihinde sıfırlandı."** / **"Parolanız gg.aa.yyyy tarihinde kurtarma anahtarıyla yenilendi."**, altında **"O tarihten bu yana hesabınızla yapılan girişler:"**, düğme **"Gördüm"**; giriş listelerinde oturumun kendi girişi **"· bu oturum"** | kullanıcı metninde "çapa", "tohum", "sarmal", "kip", "zincir başı", "log", "audit"; bulgu kodları (`kuyruk_kesik`, `capa_yok`, `seal`…); "mühür" (yalnız Hakkında'nın **Teknik Bilgiler** kartında, yöntem adlarıyla birlikte) | Tasarım §4.6.2-4.6.3, §4.4.3. Okul çekirdeğinin bütün yazmaları oturumdaki hesabın adına denetim izine yazılır; **bugünkü tek istisna** öğrenci ve personelin sicilden silinmesi ile iki kişi kaydının birleştirilmesidir (F1b 5. adımda yeniden yazılır; plan §2.2 "Denetim izi") — Hakkında'nın **Dürüst Sınırlar** kartı bunu açıkça söyler. Yedekten geri yükleme veritabanını değiştirdiği için satırı geri yüklemeden sonraki ilk girişte yazılır; uygulama içinden yapıldıysa satır onu başlatan oturumun hesabını taşır (kurtarma anahtarı yolunda da) — Dürüst Sınırlar: **"Yedekten geri yükleme, ardından yapılan ilk girişte, onu başlatan hesapla birlikte yazılır."** Kartlar ve bildirim yalnız programın kendi anahtarıyla yazdığı ve doğrulanan kayıtları okur: program dışından eklenen bir giriş "Son Girişler"de görünmez, bulgu olur. Bugün denetim izinin kullanıcıya görünen yüzü Genel Bakış kartları (§4.5) ve parola yenilenme bildirimidir; denetim izini okuma ekranı Denetleme Kurulu modülüyle gelir. Kişisizdir: hesap **rol etiketi** ve **tanıtıcı**yla anılır ("Muhasip · tanıtıcı muhasip"; mührü tutmayan hesapta "Tanıtıcısı “muhasip” olan hesap (kayıtta yazan rol: Sekreter)"), ad-soyad hiçbir kartta ve bildirimde yoktur (§5). Kâğıda inen satırı bugün kullanıcı elle not eder; aylık bildirime, deftere geçirilecek baskıya ve devir-teslim tutanağına basılması o belgelerle gelir (tasarım §4.6.3). Dürüst sınır **"Denetim izi değişikliği gösterir, önlemez."**: veritabanı kilit işaretiyle birlikte eski bir kopyayla değiştirilirse program fark etmez, kâğıttaki satır fark ettirir (tasarım §4.6.3 "Kalan risk") |
| Erişim günlüğü (F1b) | ekran **Erişim Günlüğü** (program yöneticisi ve Denetleme Kurulu); kayıt **erişim günlüğü** (hassas okumanın ve kişisel veri içeren çıktının kaydı); türlerin görünen adları **"Maskesiz T.C. kimlik numarası"** · **"Kişi dökümü"** · **"Veli listesi çıktısı"** · **"Kişisel veri içeren dışa aktarım"** · **"İhlal dökümü"** · **"Özel nitelikli kişisel veri içeren ek"** · **"Özel nitelikli kişisel veri alanı"**, kapalı kümede olmayan tür **"Bilinmeyen tür"**; süzgeçlerin iletileri **"Tarih geçersiz."** · **"Bitiş tarihi başlangıç tarihinden önce olamaz."** · **"Geçerli bir tür seçin."** · **"Geçerli bir hesap seçin."** · **"Sayfa numarası geçersiz."** | kullanıcı metninde "log", "erişim logu"; tür kodları (`MASKESIZ_TCKN`…), model ve alan kodları (`okul.Student`, `first_name`); özel nitelikli türlerde "hassas veri" | Tasarım §4.6.4, §4.4.2 ("Erişim günlüğü" satırı: program yöneticisi ve Denetleme Kurulu okur, öteki roller göremez); plan F1b-2 "Erişim günlüğü okuma ucu". Özel nitelikli türlerin adı [KVKK md. 6/1](mevzuat/6698-kvkk.md#madde-6)'in sözüdür ("özel nitelikli kişisel veri"); kişi dökümü [KVKK md. 11](mevzuat/6698-kvkk.md#madde-11) başvurusunun, ihlal dökümü [KVKK md. 12/5](mevzuat/6698-kvkk.md#madde-12) bildiriminin yardımıdır (tasarım §8.6); veli listesi çıktısı adlı davet teslim çizelgesi ve katılım cetvelidir (tasarım §4.6.4). Kişisizdir: okuyan hesap **rol etiketi** (sıra no'suz, okuma anındaki rol) ve **tanıtıcı**yla anılır ("Muhasip · tanıtıcı muhasip"), ad-soyad yoktur; okunan değer günlükte hiç yoktur, yalnız okunan kaydın kimliği durur. Süzgeçler tarih aralığı (iki uç dahil; gün Europe/Istanbul'a göredir), tür ve hesaptır; en yeni kayıt üstte, sayfa başına 50 kayıt. Günlüğü okumak iz bırakmaz: ne denetim izine ne erişim günlüğüne yazılır. Saklama 2 yıldır (programın varsayılanı; tasarım §15 B-9 doğrulanmadı); süresi dolan kayıt silinir, silme denetim izine düşer. Bugün günlüğe yazan bir okuma yoktur: kayıtlar o okumaları getiren fazlarla gelir (F1c-F5), ekran o güne dek boştur. Model ve alan kodlarının ekrandaki adları o okumaları getiren fazda bu satıra eklenir. Ekranı F1b 2. adımın (d) alt commit'indedir |
| Geri yükleme kartının “Gördüm”ü (F1b) | **Yedekten Geri Yükleme Yapıldı** kartında düğme **"Gördüm"** (yalnız Denetleme Kurulu); kartın gösterdiği geri yükleme artık son geri yükleme değilse ya da kayıt bulunamazsa **"Bu geri yükleme kartı artık güncel değil; Genel Bakış'ı yenileyip yeniden deneyin."**; biçimsiz istekte **"Geri yükleme kaydı belirtilmedi."** · **"Geri yükleme kaydının numarası geçersiz."** | düğmede "Onayla", "Kapat", "Tamam"; kullanıcı metninde kayıt türü kodları (`ISARET`, `GERI_YUKLEME`) ve "seq" | Tasarım §4.4.4 (kart Denetleme Kurulu "gördüm" diyene dek kalır), §4.4.2 ⁵ (kayıt bütünlüğü denetimi Denetleme Kurulunun işidir; yönetim kurulu rolleri ve program yöneticisi yazamaz); plan F1b-2 "Gördüm." ve kullanıcı kararı 02.11.2026: Denetleme Kurulunun bir üyesinin "Gördüm"ü kartı herkes için kaldırır (program yöneticisinde ve öteki üyelerde de); kimin gördüğü denetim izinde kalır. Aynı geri yüklemeye ikinci "Gördüm" bir şey yazmaz. Program yöneticisi kartı görür, kaldıramaz: açık Denetleme Kurulu hesabı yoksa kart kalır. Yeni bir geri yükleme kartı yeniden açar. Kart yalnız programın kendi anahtarıyla yazılmış ve doğrulanan bir "Gördüm" kaydıyla kalkar (§1 "Denetim izi"). Düğme F1b 2. adımın (d) alt commit'indedir |
| Yedek | **yedek**, **şifreli yedek**; bugün türleri **günlük yedek** (program günde bir kez kendiliğinden alır: açılışta ya da açıkken gün değişince) ve indirilen şifreli yedek; indirileni **"USB bellekteki yedek"** (ya da okulun ağ diskindeki); hatırlatma kartı **Şifreli Yedeği USB Belleğe Alın**; geri yüklemede kenara alınan **önceki veritabanı** (`db-onceki-…`) | kullanıcı metninde dosya uzantısı (`.odbak`), "kapsayıcı", yöntem adları; "dış yedek" (ekranda ve kılavuzda; kod yorumunda serbest); "harici yedek", "bulut yedeği" | Teknik adlar yalnız Hakkında sayfasında geçer. Yedek bulut depolama hizmetine yüklenmez ([BSG Yön. md. 11/23](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11)); taşınabilir ortamdaki veri şifreli saklanır ([BSG Yön. md. 10/5](mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)), programın yedeği zaten şifrelidir ve şifresiz kopya üretilmez. **USB bellekteki yedek programın dışındadır:** program ona ulaşamaz, onu silemez; saklanması okulun sorumluluğundadır. Yedek bu bilgisayarda program yöneticisinin parolasıyla (geri yüklemede alan **"Parolanız"**), başka bir bilgisayarda ya da güvenlik dosyası kayıpken yalnız yedeğin alındığı gün geçerli olan kurtarma anahtarıyla açılır (yedek başlığı hesap taşımaz; tasarım TK10). Program açılmıyorsa geri yükleme Windows'ta Başlat menüsündeki **"OAB Defteri — Yedekten Geri Yükle"** kısayoluyla, Pardus'ta `oab-defteri --geri-yukle` komutuyla yapılır. Parolayla geri yüklemeyi (kısayolda ve komutta da) yalnız program yöneticisi hesabı yapar; kurtarma anahtarıyla geri yüklemede hesap sorulmaz. Ret iletileri (tasarım §4.4.4 "Geri yükleme yetkisi"): başka rolde ya da hesabın kaydı bulunamazsa **"Yedekten geri yüklemeyi yalnız program yöneticisi hesabıyla ya da kurtarma anahtarıyla yapabilirsiniz."**; askıdaki ya da kapalı hesapta **"Bu hesap açık değil; geri yükleme yapılmadı. Kurtarma anahtarıyla deneyin."**; kaydı program dışından değiştirilmiş görünen hesapta (mührü tutmayan ya da eski bir kopyadan geri konmuş: denetim izindeki son kaydını tutmayan hesap kaydı — iki hâl tek iletidir) **"Hesap kaydı program dışından değiştirilmiş görünüyor; geri yükleme yapılmadı. Program yöneticisine ve Denetleme Kuruluna bildirin."**; denetim izinde hesabın son kaydından sonra silinmiş ya da sırası değiştirilmiş kayıt varsa (değişen hesap kaydı değil denetim izidir; izden ilgisiz bir satır silinince son kaydı ondan eski bütün hesaplar bu iletiyi alır) **"Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş görünüyor; geri yükleme yapılmadı. Yedeği kurtarma anahtarıyla geri yükleyin ve Denetleme Kuruluna bildirin."**; parola kaydı hesap kaydındakiyle uyuşmayan program yöneticisi hesabında (eski ya da program dışından konmuş parola kaydı; güncel veritabanı okunamayıp yedeğin içindeki kayda bakıldığında yedekten sonra değiştirilmiş parola da) **"Bu hesabın parola kaydı kayıtlardakiyle uyuşmuyor; geri yükleme yapılmadı. Güvenlik dosyası ya da kayıtlar bozulduysa ya da program dışından değiştirildiyse yedeği kurtarma anahtarıyla geri yükleyin ve Denetleme Kuruluna bildirin."** Dördünde de hiçbir dosya değişmez; konsol penceresi iletiyi gösterir, uygulama içinde ileti geri yükleme kartında çıkar. F1b 3. adımda dışarı çıkan yedek dosya deposunu da taşır (tasarım §4.4.7); yeni türlerin adları o adımda işlenir |
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
| — (program belgesi) | **Kurtarma anahtarı belgesi** (tasarım §9.7; belgenin başlığı "KURTARMA ANAHTARI BELGESİ"); indirilen dosya `Kurtarma-Anahtarı-Belgesi_gg.aa.yyyy.pdf` | aileden; metni F1b 1. adımda OAB'ye göre yazıldı (tasarım §13 D50): anahtar no'su ve üretim tarihi, "herkes kendi hesabıyla", anahtar yalnız program yöneticisine ve üç durumda (unutulan parola, yeni bilgisayar, güvenlik dosyasının kaybı ya da bozulması) |
| — (program belgesi) | Yedek raporu (adı F1b'de kesinleşir) | F1b |
| — (program belgesi) | Kurtarma anahtarı zarfı imha tutanağı | F4 |
| E63 | Hesap teslim pusulası (belgenin başlığı "HESAP TESLİM PUSULASI"); indirilen dosya `Hesap-Teslim-Pusulası_gg.aa.yyyy.pdf`; metinleri §1 "Hesap teslim pusulası (F1b)" | F1b 2. adım |
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
  yazılır ("Kurtarma anahtarı belgesi"); program durumu ekranlarının başlıkları §4.2'deki cümlenin kendisidir
  ("Kayıtlar kilitli"); onay diyaloğunun başlığı sorudur.
- **Başlık sabit addır.** Kartın ya da bölümün başlığı duruma göre değişmez; durum başlığın altındaki cümlede
  söylenir ("Hesap ve Parola" başlığının altında "Bu oturum: Program yöneticisi · tanıtıcı yonetici" ya da "Program
  yöneticisi hesabı kurulmadı."). Böylece yol tarifi hep aynı adı kullanır.
- **Onay diyaloğu:** geri dönüşü olmayan ya da kayıt düşüren her işlem onay diyaloğundan geçer. **Başlık soru, gövde
  sonuçtur** ("Yedekten geri yüklensin mi?" başlığının gövdesi ne olacağını söyler); gövde başlıktaki soruyu yinelemez,
  ikisi aynı cümle olmaz. Parola ya da başka bir değer isteyen diyalog bir formdur: başlığı eylemin adıdır
  ("Parolayı değiştir"). Geri dönüşü olmayan işlemi onaylatırken parolayı da soran diyaloğun
  başlığı yine sorudur ("Kurtarma anahtarı yenilensin mi?").
- **Devam düğmesi** tek biçim: "Kaydet ve devam et" (kayıt yoksa "Devam"). Vazgeçme: "Vazgeç"; salt bilgi
  diyaloğunda "Kapat".
- **Seçici yer tutucusu** tek biçim: "Seçin". Boş seçenek: "— yok —".
- **Snackbar** tam cümledir ve noktayla biter ("Parolanız değiştirildi.").
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
  `Kurtarma-Anahtarı-Belgesi_31.10.2026.pdf`. Kimlik numaralı ad (`belge_3.pdf`) masaüstünde neye ait olduğunu
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
| Hakkında ve Lisans | Hakkında ve Lisans | `/hakkinda` | Kenar çubuğunun altında, ana gezinmenin dışında. Kartları: **Program** (tanım ve konum) · **Geliştirici** (iletişim) · **Ücretsiz ve Ticari Olmayan Kullanım** · **Üçüncü Taraf Bileşenler** · **Dürüst Sınırlar** (tasarım §4.4.6, sade dille: rol bir şifreleme önlemi değildir · şifreli alanlar en zayıf hesap parolası kadar korunur · açık oturum, sahibinin imzasıdır — her iş o hesabın adına denetim izine yazılır, bugünkü istisnasıyla; yedekten geri yükleme ilk girişte, başlatan hesapla birlikte yazılır (§1 "Denetim izi") · denetim izi değişikliği gösterir, önlemez — tasarım §4.6.3 "Kalan risk", "Kayıt no · Zincir" satırını kâğıda not etme öğüdüyle · kurtarma anahtarını yenilemek önceki yedekleri kapatmaz · çıktı, programın dışına çıkınca korumadan da çıkar · kayıp ya da çalınmada bildirim programın işi değildir, KVKK md. 12/5) · **Teknik Bilgiler** (yöntem adları; denetim izinin zinciri dahil) |
| — | Kurulum Sihirbazı | `/kurulum` | Menüde yoktur. İlk açılışta kurulum kapısı buraya getirir; kurulumdan sonra Ayarlar'ın altındaki **Kurulum Sihirbazı** kartıyla açılır |

Ana gezinmenin sırası: Genel Bakış · Kişiler · Ayarlar · Kılavuz. Role göre gezinme F1b 2. adımda gelir (tasarım
§4.4.2). Planlanan ekranlar: Kullanıcılar F1b 2. adımda (plan §2.2; tasarım §14); Okul Bilgileri bugün Ayarlar'ın sekmesidir, OAB alanları F1b 4. adımda gelir; Birlik Dönemi,
Kişiler (OAB'nin kişi türleriyle), Organlar, Temsilciler ve Pano (yol haritası) F1c'dedir (plan §2.3). Adları ekran
gelince buraya işlenir.

### 4.2 Program durumu ekranları

Bunlar adres değildir; program durumuna göre sayfanın yerine gelir. **Üst çubuk başlığı ekranın h1'idir:** ekran
açıkken kendi h1'ini üst çubuğa yazar (`ui/DurumBasligi.tsx`; `UstCubukBasligi.test.tsx`).

| Durum | Başlık |
|---|---|
| Kilitli | **Kayıtlar kilitli** |
| Güvenlik dosyası yok ya da bozuk | **Güvenlik dosyası bulunamadı ya da okunamıyor** |
| Yedekten geri yüklendi | **Programı kapatıp yeniden açın** |

Pencere açılmadan çıkan açılış iletilerinin başlıkları (masaüstü ileti kutusu; `desktop/errors.py`): **Program sürümü
eski** (eski program, yeni veri — çıkış kodu 4) · **Veritabanı bozuk** · **Veritabanı güncellenemedi** · **OAB
Defteri zaten çalışıyor** · **Pencere açılamadı** · **Program başlatılamadı** · **OAB Defteri açılamadı** (genel).
İletinin gövdesi sonucu, ikinci paragrafı yapılacak işi söyler.

Kilit ekranının adları: grup **Hesap** (satır rol etiketi + tanıtıcı; §1 "Hesap"), alan **Parola**, düğme **Aç**
(sürerken **"Açılıyor…"**, beklerken **"Denetleniyor…"**); zorunlu yenilemede **Yeni parola** · **Parola (tekrar)** ·
**Parolayı yenile ve aç** · **Vazgeç**; kurtarma yolu **Parolamı unuttum** → **Kurtarma anahtarı** · **Yeni parola** ·
**Parola (tekrar)** · **Kurtar ve aç** · **Parolayla açmaya dön**. Liste boşsa (kayıtlar kurtarma anahtarıyla geri
yüklendi) kurtarma yolu doğrudan açılır ve gerekçesini söyler. Hesap seçilmeden gönderilince Hesap grubunun altında
**"Hesabınızı seçin."** (kurtarma yolunda **"Program yöneticisi hesabını seçin."**) yazar; onuncu hatalı denemedeki
askı iletisi de orada kalır ve seçim bırakılır (başka hesap kendiliğinden seçilmez).

Üst çubuktaki **oturum göstergesi** (yalnız açık oturumda): rol etiketi ve tanıtıcı, boşta kilide geri sayım (kurulumdan
sonra), **"İşlem bitince kilitlenecek"** (kilit ertelenmişse), düğme **Kilitle** (ipucu "Kilitle (Ctrl+Shift+L)").
Her durumda görünen **Çık** düğmesinin pencereleri: **Programdan çıkılsın mı?** (onay; her durumda parolasız) ·
**Program kapanıyor**. Kapanış başladıktan sonra gelen kilit açılışı hiçbir şey yazmadan reddedilir: **"Program
kapanıyor; kilit açılmadı."** (kapanış, süren kilidin ve kilit açılışının bitmesini bekler; oturum kilitlenip işaret
yazılmadan program kapanmaz).

### 4.3 Sekmeler

İlk sekme varsayılandır.

| Sayfa | Sekmeler, sırasıyla (`?tab=` değeri) |
|---|---|
| Kişiler | **Öğrenciler** (`ogrenciler`) · **Öğretmenler ve Diğer Personel** (`personel`) · **Ayrılış Havuzu** (`havuz`) |
| Ayarlar | **Ders Yılları** (`ders-yillari`) · **Kapalı Günler** (`kapali-gunler`) · **Şubeler** (`subeler`) · **Okul Bilgileri** (`okul`) · **Güvenlik** (`guvenlik`) · **Güncelleme** (`guncelleme`) |

Kişiler'in Öğrenciler sekmesi F1b 5. adımda sökülür (plan §2.2).

Pencere başlıkları (Dialog): **Yeni öğrenci** / **Öğrenciyi düzenle** · **Yeni kişi** / **Kişiyi düzenle** ·
**Parolayı değiştir** · **Parola yenilenme bildirimi** (kilit ekranından açılıştan sonra hangi sayfada olunursa
olsun kendiliğinden açılır; düğme **"Gördüm"**; §1 "Denetim izi"). Onay diyaloglarının başlıkları (soru, §3):
**Program kilitlensin mi?** · **Ders yılı aktifleştirilsin mi?** · **Şube katalogdan kaldırılsın mı?** · **Kapalı
gün silinsin mi?** · **Öğrenci ayrıldı olarak işaretlensin mi?** · **Öğrenci sicilden silinsin mi?** · **Kişi ayrıldı
olarak işaretlensin mi?** · **Kişi sicilden silinsin mi?** · **Bu iki kayıt aynı kişi mi?** · **Kurtarma anahtarı
yenilensin mi?** · **Yedekten geri yüklensin mi?** · **Güvenlik dosyası sıfırlansın mı?** · **Parola kaydı güvenlik
dosyasından silinsin mi?** (onay düğmesi **"Sil"**). Kişiler'deki içe aktarma panelleri: **e-Okul Raporundan veya Şablondan
Öğrenci Aktar** · **e-Okul Raporundan veya Şablondan Öğretmen ve Diğer Personeli Aktar**.

### 4.4 Kurulum Sihirbazı adımları

Adım rayındaki adlar, sırasıyla: **Program Yöneticisi Hesabı** · **Okul Bilgileri** · **Ders Yılı ve Kapalı
Günler**. İlk adım atlanamaz. Adımlar arası düğmeler: **Geri**, **Devam** (1. adım), **Kaydet ve devam et** (2. adım),
**Kurulumu tamamla** (son adım).

1. adımın alanları **Tanıtıcı** · **Ad-soyad** · **Parola** · **Parola (tekrar)**, düğme **"Hesabı kur"** (sürerken
**"Kuruluyor…"**), snackbar **"Program yöneticisi hesabı kuruldu."**; hesap kurulmadan ilerleme ipucu **"Devam etmek
için program yöneticisi hesabını kurun."** Hesap kurulunca **Kurtarma Anahtarınız** paneli anahtarı no'su ve üretim
tarihiyle gösterir. Bu adımda Kilitle'ye basılırsa ve anahtar henüz doğrulanmadıysa önce **"Program kilitlensin
mi?"** sorulur (§1 "Kilit ve çıkış").

F1b'de sihirbazın öteki adımları da OAB'nin düzenine döner: okul kartı (OAB alanları 4. adımda) · ders yılı,
dönemler, kapalı günler (plan §2.2; tasarım §5.1, §14). Geçiş kurulumunun adımları sonra gelir: ilk birlik dönemi ve
görevdeki kurul F1c'de, birliğin banka hesabı ve açılış (devreden) bakiyesi F3'te. Adların yeni hâli adım gelince
buraya işlenir.

### 4.5 Genel Bakış kartları

Sırasıyla: **Başlangıç Yol Haritası** (kurulumdan sonra; bütün maddeler bitince gizlenebilir; kurtarma anahtarı
doğrulanmamışsa uyarı kartın başındadır. Maddeler bugün: e-Okul aktarımları, öğrenciye kapalı günler ve kurtarma
anahtarının müdürlükte kapalı zarfta saklanması; parolanın paylaşılmasını öğütleyen madde yoktur — §1 "Parola") ·
**Son Oturumu Kontrol Edin** (yalnız önceki oturum düzgün kapanmadıysa; düğme **"Kontrol ettim"**) · denetim izinin
uyarı kartları (§1 "Denetim izi"; yalnız söyleyecekleri varken): **Bütünlük Durumu Okunamadı** (kartlardan biri ya
da hepsi — Son Girişler ve denetim izinin son kaydı da — okunamadıysa; bir uyarı ya da giriş sessizce kaybolmaz;
kilitliyken çıkmaz: "Denetim izinin kartları tam okunamadı; bir uyarı ya da giriş gösterilemiyor olabilir. Program
yöneticisine ve Denetleme Kuruluna bildirin.") · **Denetim İzi Bütünlüğü**
(oturumdaki hesabın bir önceki girişinden beri kilit açılışındaki denetimin bulguları, her biri sade cümlesi ve
gg.aa.yyyy SS:dd anıyla; "Bulgu denetim izinde kayıtlıdır; bu kart bir sonraki girişinizde kalkar."). Giriş cümlesi
bulgunun türüne göredir: yalnız bilgi varsa bilgi tonunda "Kilit açılırken yapılan denetim bir bilgi verdi:";
bulgulardan biri değişiklik gösteriyorsa (kayıtların silinmesi, zincirin kırılması, değiştirilmiş kayıt ya da kilit
işareti, eksik ya da fazla olay, kuralına uymayan kayıt, yenilenmemiş kilit işareti, denetlemek için gereken anahtarı
bulunamayan kayıt — "Denetim izinde, denetlemek için gereken anahtarı bulunamayan kayıt var; kayıt ya da anahtarı
program dışından değiştirilmiş olabilir."; tanınmayan bulgu da) "Kilit
açılırken yapılan denetim, denetim izinde program dışından yapılmış olabilecek bir değişiklik buldu:" ve dipte "Kayıtlar
program dışından değiştirilmiş ya da veritabanı eski bir kopyayla değiştirilmiş olabilir. Program yöneticisine ve
Denetleme Kuruluna bildirin; gerekirse sağlam bir yedekten geri yüklenir."; yalnız denetleyemeyen bulgular varsa
(kilit işareti yok ya da okunamadı, denetimin kendisi düştü, kilit işareti yokken yazılmış olaylar) uyarı tonunda
"Kilit açılırken yapılan denetim, denetim izinin bir bölümünü denetleyemedi:" ve dipte "Denetlenemeyen bölümde
değişiklik olup olmadığı bilinmiyor; orada yapılmış bir değişiklik görünmez. Durum sonraki girişlerde de sürerse
program yöneticisine bildirin." — değişiklik iddia edilmez, geri yükleme öğütlenmez; "değişiklik yok" da denmez
(denetimi program dışından düşürülmüş bir iz de bu kartı verir) ·
**Değiştirilmiş Hesap Kaydı** (girişte hesap kaydının program dışından değiştirildiği görüldü: "Kaydı program dışından değiştirilmiş görünen hesapla
giriş denendi; giriş açılmadı ve program kayda dokunmadı:") · **Yedekten Geri Yükleme Yapıldı** (son geri yükleme:
**Geri yükleme anı** (geri yükleme notundan) · **Denetim izine yazıldığı an** (geri yüklemeden sonraki ilk giriş) ·
**Yedek** — programın ürettiği yedeğin adı, yoksa "Elden getirilen dosya (adı kayda geçmez)" · **Yedeği açan** —
"Program yöneticisi · tanıtıcı yonetici hesabının parolası" ya da "Kurtarma anahtarı (anahtar no 3)" · **Başlatan
oturum** — uygulama içinden yapıldıysa onu başlatan oturumun hesabı, "Program yöneticisi · tanıtıcı yonetici"
(konsoldan yapılan geri yüklemede oturum yoktur, satır çizilmez) · **Kenara
alınan önceki veritabanı** · **Önceki veritabanının son kaydı** "Kayıt no: N · Zincir: XXXX-XXXX". Aralarında
giriş yapılmadan birden çok geri yükleme olduysa hepsi sırasıyla yazılır ("Kayıtlar, aralarında giriş yapılmadan N kez
yedekten geri yüklendi; …", alt başlıklar **"1. geri yükleme"** … **"N. geri yükleme (son)"**); ayrıntıları
okunamayan geri yükleme "Geri yüklemenin ayrıntıları okunamadı; olgu denetim izinde kayıtlıdır." der. Dip cümlesi:
"Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; kenara alınan önceki veritabanında durur."
(birden çok geri yüklemede "… ilk geri yüklemede kenara alınan veritabanında durur."); ilk geri yüklemede kenara
alınacak veritabanı yoktuysa ya da izi boştuysa (yeni bilgisayara taşıma) yerine **"Geri yüklemeden önce bu
bilgisayarda kayıt yoktu."**; ardından "Geri yüklemeyi kimin ve neden yaptığını Denetleme Kuruluna bildirin." Kart
kalır — Denetleme Kurulunun "gördüm" düğmesi F1b 2. adımın (d) alt commit'inde gelir (§1 "Geri yükleme kartının “Gördüm”ü
(F1b)"), metin bugün "Kart, son geri yüklemeyi göstermeyi
sürdürür." der) · **Hesaplar ve Güvenlik Dosyası** (iki depo farkı; alt başlıklar **"Giriş yapamayan hesaplar"** ·
**"Güvenlik dosyasında kalan eski parola kayıtları"** — her satırda neden "hesap kapalı" ya da "veritabanında kaydı
yok" ve **"Güvenlik dosyasından sil"** (erişilebilir adı hesabı anar; §1 "Denetim izi"); açıklama listedeki nedenlere
göredir: "Kapalı hesapların parola kaydını program her kilit açılışında kendisi siler; burada görünen kaydın silinmesi
tamamlanamadı (ör. dosyayı başka bir program tutuyordu), bir sonraki kilit açılışında yinelenir." · "Veritabanında
kaydı olmayan hesapların parola kaydını program kendiliğinden silmez." · "Program yöneticisi onaylarsa hemen
silinir." · **"Kaydı değiştirilmiş görünen hesaplar"**) · **Okunamayan
Kayıt Alanları** (yalnız çözülemeyen şifreli alan varken; kişisiz, yalnız sayı: "Program açıldığından beri N şifreli
alan okunamadı; bu alanlar ekranda “okunamadı” diye görünür." — §1 "Şifreleme") · **Ayrılış
Havuzu** (yalnız havuz boş değilken, yalnız sayı: "N kişi ayrılış kararı bekliyor" → Kişiler → Ayrılış Havuzu) ·
**Şifreli Yedeği USB Belleğe Alın** (yalnız son şifreli yedek indirmesinden hatırlatma süresi — varsayılan 30 gün,
ayarla 7-90 — geçince; hiç indirme yoksa program yöneticisi hesabı kurulduktan 7 gün sonra: "Son şifreli yedek gg.aa.yyyy
tarihinde indirildi (N gün önce)." / "Bu bilgisayarda henüz şifreli yedek indirilmedi."; bağlantı **"Ayarlar →
Güvenlik'i aç"**; program dosyanın USB belleğe kopyalandığını bilemez, kart "son indirme" der) · **Son Girişler**
(her zaman; oturumdaki hesabın kilit ekranından yaptığı son girişler, ilki "· bu oturum"; hiç yoksa "Bu hesapla
henüz kilit ekranından giriş yapılmadı."; okunamadıysa — "hiç yok" demez — "Son girişler okunamadı; tanımadığınız bir
giriş burada gösterilemiyor olabilir."; altında **"Denetim izinin son kaydı"** ve "Kayıt no: N · Zincir:
XXXX-XXXX" satırı, kâğıda not etme öğüdüyle; son kayıt okunamadıysa "Denetim izinin son kaydı okunamadı.") · **Kişiler** · **Ayarlar** (gezinme kartları).

Denetim izi kartlarının kime göründüğü (tasarım §4.4.2, §4.6.1, §4.6.3): **Denetim İzi Bütünlüğü**, **Değiştirilmiş
Hesap Kaydı**, **Yedekten Geri Yükleme Yapıldı** ve "Kaydı değiştirilmiş görünen hesaplar" listesi program yöneticisine
ve Denetleme Kuruluna; **Hesaplar ve Güvenlik Dosyası** kartının "Giriş yapamayan hesaplar" ve "Güvenlik dosyasında
kalan eski parola kayıtları" listeleri ve **"Güvenlik dosyasından sil"** yalnız program yöneticisine; **Son Girişler**
ve **Bütünlük Durumu Okunamadı** her hesaba görünür. Öteki kartların rol süzmesi F1b 2. adımın ön yüz işindedir. OAB'nin
pano kartları F1c'de gelir (tasarım §7.10).

### 4.6 Ayarlar → Güvenlik kartları

Sırasıyla: **Hesap ve Parola** (oturumdaki hesabın rol etiketi ve tanıtıcısı, kişi adı yok; **"Parolayı
değiştir"** ve **"Kilitle"** düğmeleri; hesap kurulmamışsa "Program yöneticisi hesabı kurulmadı." ve **"Kurulum
Sihirbazı'nı aç"**) · **Boşta Kilit Süresi** (yalnız hesap kurulduktan sonra; §1 "Kilit ve çıkış") · **Şifreleme**
(durumu, şifrelenen ve şifrelenmeyen alanlar, "en zayıf hesap parolası" sınırı) · **Kurtarma Anahtarınız** (yalnız
yeni üretilmiş anahtar beklerken) · **Kurtarma Anahtarını Doğrula** (yalnız anahtar doğrulanmamışken; üstünde
"Kurtarma anahtarı doğrulanmadı" uyarısı) · **Kurtarma Anahtarını Yenile** · **Kurtarma anahtarı belgesi** (belge adı,
§2; güncel anahtarın no'su ve üretim tarihi; düğme **"PDF olarak kaydet"**) · **Şifreli Veritabanı Yedeği** (düğme
**"Şifreli yedeği indir"**, son indirme cümlesi, hatırlatmanın durumu ve **"Hatırlatma süresi"** seçimi) · **Yedekten
Geri Yükleme** (seçilen yedeği açan anahtarın cümlesi; alanlar **"Parolanız"** ve **"Kurtarma anahtarı"**; güvenlik
dosyası kayıp ekranında yalnız **"Kurtarma anahtarı"**). Parolayla geri yükleme yalnız oturumdaki program yöneticisi
hesabının parolasıyladır; başka hesabın parolası verilirse **"Parola yalnız oturumdaki hesap için doğrulanır."**,
oturum yokken **"Parolayla geri yükleme yalnız açık oturumda, program yöneticisi hesabıyla yapılır; yedeği kurtarma
anahtarıyla açın."** (tasarım §4.4.4 "Geri yükleme yetkisi").

Kart başlıkları durumla DEĞİŞMEZ (§3 "Başlık sabit addır"): kullanıcıya "Ayarlar → Güvenlik → Hesap ve Parola"
diye yol tarif edilebilsin. Kurtarma, yedek ve geri yükleme işlemleri ile boşta süre yazımı yalnız program yöneticisine
açıktır (öteki rollerde sunucu "Bu işlem hesabınızın rolüne açık değil." der); kartların öteki rollerde gizlenmesi F1b
2. adımın ön yüz işindedir.

### 4.7 Güncelleme ekranının adları

Ekran **Ayarlar → Güncelleme** (`?tab=guncelleme`); kart **Uygulama Güncellemesi**. Düğmeler **"Şimdi denetle"**
(sürerken **"Denetleniyor…"**) · **"Doğrula ve indir"** (sürerken **"İndiriliyor…"**; yalnız Windows'ta); kutular
**Kurulu sürüm** · **Yayımlanan son sürüm**; iletiler **"Uygulama güncel."** · **"Yeni sürüm hazır: …"** · snackbar
**"Kurulum dosyası doğrulanarak indirildi."**. GitHub'a ulaşılamazsa ileti **"GitHub'a ulaşılamadı; okul ağında
engellenmiş olabilir. Yeni sürümü indir.okulapp.org'dan elle denetleyebilirsiniz."** (sunucudaki
`updates.ULASILAMADI_MESAJI` ile ön yüzdeki `ULASILAMADI_METNI` birebir aynıdır). Altında elle denetleme bağlantısı
**okulapp.org/oab-defteri** (dış tarayıcıda açılır). Pardus'ta indirme düğmesi yoktur; ekran güncellemenin paketle
yapıldığını söyler.

Elle denetim yeni sürüm bulursa kabukta **güncelleme bandı** durur (Ayarlar'da gizli;
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
- **Kilit ekranı ve üst çubuk kişi adı göstermez;** hesaplar rol etiketi ve tanıtıcıyla listelenir (tasarım §4.4.3).
  Hesap sahibinin ad-soyadı şifreli saklanır; Ayarlar → Güvenlik de oturumu rol etiketi ve tanıtıcıyla yazar.
  Genel Bakış'ın denetim izi kartları ve parola yenilenme bildirimi de hesabı yalnız rol etiketi ve tanıtıcıyla anar;
  "Son Girişler" ve bildirim yalnız oturumdaki hesabın girişlerini gösterir (§1 "Denetim izi").
- **Okunamayan ad tahmin edilmez:** çözülemeyen şifreli alan "okunamadı" diye görünür; onay diyaloğu "Adı okunamayan
  bu kayıt", erişilebilir ad "Adı okunamayan kayıt" der (eylemde belirtme hâliyle: "Adı okunamayan kaydı düzenle"). Genel Bakış kartı yalnız sayıyı verir (§1 "Şifreleme").
- **Şifreleme dürüst anlatılır:** metin olduğundan güçlü bir koruma vadetmez; şifrelenen alanları ve şifrelenmeyenleri
  ayrı ayrı söyler, tam disk şifrelemesi olmadığını yazar (§1 "Şifreleme"; tasarım §4.4.6).
- **Destek ve hata bildirimi:** iletiye öğrenci, veli ya da personel bilgisi, gerçek veri içeren ekran görüntüsü,
  yedek ya da veritabanı dosyası eklenmez; Hakkında sayfası bunu söyler.
- Bugünkü Kişiler ekranındaki öğrenci sicili (ad-soyad, okul numarası, sınıf) aile iskeletinden kalır ve F1b 5.
  adımda sökülür (plan §2.2); o güne dek okul numarası şifreli saklanır ve yalnız numaranın tamamıyla aranır.
