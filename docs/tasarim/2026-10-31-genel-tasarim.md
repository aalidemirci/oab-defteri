# OAB Defteri — Genel Tasarım

*Tarih: 31.10.2026 · Durum: **TASLAK v2** — bağımsız tasarım denetiminden (F0-9) geçti; 129 bulgu işlendi ya da gerekçeyle
reddedildi ([denetim](../kesif/2026-10-31-tasarim-denetimi.md#işleniş)). Kararlar: ön değerlendirmede dokuz kullanıcı
kararı (K1-K9); F0'da on bir karar (§2.1) ve tasarımın altı açık sorusu (§15.1) kullanıcıya soruldu; denetimden sonra
beş karar daha alındı (D1-D5, §15.1b); kalanlar varsayılanla ilerler (§15.2-§15.5). Dayanaklar:
[ön değerlendirme](../kesif/2026-10-31-on-degerlendirme.md) · [F0-F1 planı](../plan/2026-10-31-f0-f1-plani.md) ·
[mevzuat korpusu](../mevzuat/BENIOKU.md) · [OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) ·
[iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md) · [saha notları](../kesif/saha.md)*

---

## 1. Altmış saniyede proje

OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten **çevrimdışı bir masaüstü programıdır**
(Windows 10/11 + Pardus 21/23/25). Kapsadığı işler:

- organlar ve toplantılar: yönetim ve Denetleme Kurulu, görev bölümü, temsilciler, aylık YK toplantıları ve karar
  defterine el ile yazılacak karar taslakları;
- genel kurul: çağrı, ilan, katılım cetveli, yeter sayı, ikinci toplantı, divan, ibra, seçim, devir-teslim;
- gelir-gider: işlem düzeyinde kayıt, banka hesap hareketiyle eşleme, makbuz koçanı takibi, şartlı bağış, elden
  bağışta 5 iş günü, harcama zinciri, tahmini bütçe, aylık bildirim ve dönemlik ilan;
- TEFBİS'e girilecek kayıtların listesi ve TEFBİS çıktısıyla banka-defter mutabakatı;
- Denetleme Kurulu'nun ara ve nihai raporu, faaliyet raporu ve kesin hesap;
- kantin (kiralama süreci evrakı, sözleşme, aylık kira, arz bedeli ve pay dağılımı, belge süreleri) ve servis
  (taşımacının tespiti, sözleşme, belge takibi);
- dönem kapanışı, devir-teslim ve yıl sonu arşiv paketi.

**Konum (bağlayıcı).** Program **karar defterinin ve TEFBİS'in yerine geçmez.** Kararlar noter tasdikli karar
defterine el ile yazılır ([md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13),
[23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); gelir ve giderleri TEFBİS'e okul idaresi girer
([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Program bunlara girilecek metni ve listeyi
hazırlar, tutarlılığı denetler, kurul değişse de kaybolmayan kurumsal hafızayı tutar (§3.1).

**Kim kullanır.** Okulda tek bilgisayar, kişisel hesaplar. Programı çoğunlukla OAB'den sorumlu müdür yardımcısı
kullanır; başkan, muhasip ve sekreter ayda bir kendi işleri için girer (mali kayıtları yalnız muhasip girer, D2); Denetleme Kurulu her şeyi okur ve yalnız
denetim modülüne yazar; okul müdürü her şeyi okur ve yalnız kendi yazılarını hazırlar (§4.4).

**Köken.**
- Masaüstü, paketleme, güvenlik çekirdeği ve ön yüz kiti: **Kütüphane Defteri** (ailenin en güncel iskeleti). Tepsi,
  ağ kataloğu, Ağ Doktoru, güvenlik duvarı, barkod ve ISBN alınmaz (§12.B).
- İş mantığı: OYS'nin `okul_aile_birligi` modülü (ADR-0028) — **mevzuat hataları düzeltilerek** uyarlanır (§12.A);
  mali çekirdeğin (banka, işlem, eşleme, harcama zinciri, makbuz yaprağı) OYS'de karşılığı yoktur, yeni yazılır.
- Mevzuat: bu deponun [`docs/mevzuat/`](../mevzuat/BENIOKU.md) korpusu (26 metin, 31.10.2026'da teyitli). Programın
  her kuralı buradaki bir çapaya bağlıdır (§6).
- Evrak: yazarın evrak çalışmasındaki genel OAB seti (`GNL-OAB-FR-001…023`, `GNL-OAB-RH-001`) ve OYS şablonları (§9).

**Neden.** Kurullar her yıl değişen gönüllü velilerden oluşuyor ve kayıtlar kişilerle birlikte dağılıyor; pilot okulda
devir tutanağı tutulmuyor ve genel kurul çoğu yıl ikinci toplantıya kalıyor ([saha](../kesif/saha.md)). TEFBİS, banka
ve defter denkliği isteniyor; Sayıştay birliklerin mali tablosu olmadığı için görüş verememiş. Piyasada OAB işlerini
kapsayan iki ürünün ikisi de bulutta ve TEFBİS, makbuz koçanı, karar defteri, genel kurul evrakı yok
([ön değerlendirme §0, §3](../kesif/2026-10-31-on-degerlendirme.md)).

---

## 2. Verilmiş kararlar

### 2.1 Kullanıcı kararları

Ön değerlendirme §9 (K1-K9) ve F0'da kullanıcıya tek tek sorulan sorular (31.10.2026; ayrıntı
[plan §1.8](../plan/2026-10-31-f0-f1-plani.md)). "Öneriden farklı" sütunu, kullanıcının önerilen seçeneği almadığı
kararları gösterir.

| # | Konu | Karar | Öneriden farklı |
|---|---|---|---|
| K1 | Gelir-gider ayrıntısı | **İşlem düzeyi**; her kayıt banka hareketiyle eşlenir | — |
| K2 | Kurulum ve kullanıcılar | Okulda **tek bilgisayar**, rol bazlı yerel hesaplar. **Mali kayıtları yalnız muhasip girer** (MY TEFBİS'i muhasibin girişinden sonra yapar; D2). Denetleme Kurulu her şeyi okur, **yalnız denetim modülüne** yazar; okul müdürü her şeyi okur, **yalnız kendi yazılarını** (harcama talebi md. 18/1, uyarı md. 27/3, yeni okulda genel kurul daveti md. 9/1, olağanüstü genel kurul çağrısı md. 9/6 — §15.1 M-5) yazar; DK'nin md. 14/5 çağrısı denetim modülündendir (§15.1 M-6) | — |
| K3 | Bordro ve personel | Bordro **yok**; personel için özlük, yıllık izin, kıdem karşılığı (sürüm 2). Çalıştırma biçimi **okula göre**: okul kartında doğrudan işveren · hizmet alımı · çalıştırmıyor; personel modülü yalnız doğrudan işverende açılır | — |
| K4 | Kantin ve servis | **İlk sürümde**; birliğin ve okulun evrakı ve takibi, komisyon kararının yerine geçmez | **evet** (öneri sürüm 2-3 idi) |
| K5 | Makbuz | **Basılmaz**; ciltli koçanın envanteri ve yaprak kaydı | — |
| K6 | TEFBİS | Giriş listesi + TEFBİS Excel çıktısıyla mutabakat; **otomatik giriş yok** (teyit 31.10.2026) | — |
| K7 | Lisans | **PolyForm Noncommercial 1.0.0**; kamuya "kaynağı açık" diye tanıtılır | — |
| K8 | Ad | **OAB Defteri**; site `okulapp.org/oab-defteri` | — |
| K9 | Bağışçının T.C. kimlik no'su | **Varsayılan kapalı**, ayardan açılır (yalnız bağışçı alanı, şifreli, maskeli) | — |
| T1 | Hesaplar ve şifreleme anahtarı | **Kişisel hesaplar** (Argon2id); veri anahtarı her hesap için ayrı sarılır; kurtarma anahtarı basılıp **okul müdürlüğünde kapalı zarfta** saklanır, veliye geçmez (D3) | — |
| T2 | Evrak hattı | **Tek içerik, iki çizici**: Word `python-docx`, PDF ailenin WeasyPrint hattı; LibreOffice/Word gerekmez | — |
| T3 | Birlik dönemi | **Genel kuruldan genel kurula**; ders yılı ve TEFBİS dönemiyle eşlem tablosu | — |
| T4 | Hesap modeli | **Basit hesap planı** (banka, kasa, şartlı bağış alt hesabı), TEFBİS işlem tipine eşlemli; çift taraflı muhasebe değil | — |
| T5 | e-Okul verisi | **Personel** (ad-soyad, görev) **+ veli listesi** — veliden yalnız ad-soyad ve öğrencinin sınıfı; telefon, adres, T.C. kimlik no, öğrenci no alınmaz; liste dönem kapanışında silinir | **evet** (öneri yalnız personeldi) |
| T6 | Pencere | Çarpı **programı kapatır**; tepsi ve otomatik başlatma yok | — |
| F0-a | Kantin arz bedeli vadesi | Sözleşmedeki **izleyen ayın 10'u** ([EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7)) esas, Yönetmelikteki **20'si** ([md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) üst sınır; iki tarih kural paketinde ayrı kural | — |
| F0-b | Sert engeller | Sert engel yalnız dört gerekçede (D1 ve D4 ile güncel hâli; §6.1): **hesap bütünlüğü** (toplamlar, numara tekilliği, kapanmış dönem, yeter sayı ve karar hesabı); **programın kendi hesapladığı değerde** yasal oran ve yöntem (D1: gerçekte olan tutar yine kaydedilir, fark uyarıdır; kullanıcının belgeden girdiği değer uyarıdır); **mevzuatın hukuken geçersiz saydığı işlem** (kantin isteklisinde suç ve hısımlık engeli; serviste mülki amir onayı (OLUR) olmadan kesinleştirme — kantinde uyarı, D4; organda mevzuatın saymadığı kişi türü: YK'ye veli olmayan, DK bileşimi); **kullanıcının sert dediği karar** (A-2, KE-15). Eksik belge, taksit sayısı, puan sınırı uyarı + gerekçe; liste genişlemez (CLAUDE.md altın kural 3) | — |
| F0-c | TEFBİS ve banka örnekleri | Sonra gelecek; tasarım varsayılan şemayla (§8), örnek gelince "F1 eki" | — |
| F0-d | Saha | Yalnız pilot okul; gönüllü okul aranmaz. Pilot okul görüşmesi yapıldı ([saha.md](../kesif/saha.md)) | **evet** (öneri 2-4 gönüllü okuldu) |
| F0-e | İl/ilçe MEM'e sorular | Sorulmaz; varsayılanlar: (a) program tasdikli deftere geçirilecek baskı üretir, (b) veri sorumlusu sorusu kılavuzda okul müdürlüğüne bırakılır, (c) internet bankacılığında üçüncü onay okul ayarıdır, (d) okul kendi TEFBİS işlem tipi listesini girer | — |
| D1 | Sert engel ve yasal parametreler | Programın **hesapladığı** değerde sert, kullanıcının **girdiği** değerde uyarı + gerekçe (§15.1b) | — |
| D2 | Mali kayıtları kim girer | **Yalnız muhasip**; MY mali kayıt yazamaz (§15.1b) | **evet** (öneri: MY girer, muhasip onaylar) |
| D3 | Kurtarma anahtarı | **Müdürlükte kapalı zarf**; veliye geçmez (§15.1b) | — |
| D4 | Mülki amir onayı olmadan kesinleştirme | Serviste sert, kantinde uyarı (§15.1b) | — |
| D5 | Taşımacı listesi duyurusu | Altın kural 5'e mevzuat istisnası, asgari bilgi (§15.1b) | — |

### 2.2 Teknik kararlar

*Bu tablo bu belgenin önerisidir; itiraz edilebilir. Kimlikler **TK-n**'dir (plan §1.3'teki T1-T6 kullanıcı
kararlarıyla karışmasın diye). "Durum" sütunu: **Kesin** = bağlayıcı bir kullanıcı ya da aile kararının teknik
karşılığı · **Öneri** = bu belgenin önerisi · **§15 (M-n)** = kullanıcıya açık karar, yazılı varsayılanla ilerlenir.*

| # | Konu | Karar | Gerekçe | Durum |
|---|---|---|---|---|
| TK1 | İskelet | Kaynak Kütüphane Defteri `origin/main` 9a3829d. Dosya düzeyi harita §12.B'dedir; değişen her dosya UYARLA sınıfındadır; haritada olmayan "iyileştirme" yapılmaz | Ailenin en güncel iskeleti: Linux zinciri PySide6 (PyQt5 + PolyForm NC aynı pakette dağıtılamıyordu), lisans dizini, saha kabul protokolü, Debian provası ([plan](../plan/2026-10-31-f0-f1-plani.md) F0-7) | Kesin |
| TK2 | Katmanlar | Django 5.1.15 + DRF 3.15.2, SQLite (WAL, `synchronous=FULL`, `secure_delete=ON`), Python 3.12 · React 18 + TS + Vite + Tailwind (aile kiti) · servis katmanı baştan alt modüllere bölünür · OpenAPI yok, tipler elle · tek yazar + `IMMEDIATE` işlem | Aile kararları (Kütüphane T12, T13, T15, B13). Ölçek küçük: yılda ~400-500 banka hareketi ([ön değerlendirme §6](../kesif/2026-10-31-on-degerlendirme.md)) | Kesin |
| TK3 | Süreç ve ağ | Tek süreç, tek dinleyici: waitress yalnız `127.0.0.1`'de, rastgele portta, oturum belirteciyle. **Ağ servisi yoktur**; ikinci dinleyici, güvenlik duvarı kuralı, Ağ Doktoru yoktur | K2 (tek bilgisayar) ağ erişimi gerektirmez. Okul ağına port açmak [BSG Yön. md. 11/7](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11) ("aktif ağ cihazı") ve 11/22 (port yönetimi Başkanlıkta) tartışmasını doğururdu; Kütüphane'nin bu bedeli ödeme gerekçesi (ağ kataloğu) burada yok | Kesin |
| TK4 | Dış istek | Tek kapı: kullanıcının başlattığı "Güncellemeyi denetle". İlk istek yalnız `api.github.com`'a, kurulum dosyası `github.com`'dan; GitHub'ın indirme yönlendirmesi izlenir, **güven çapası SHA-256'dır** (kurucu çalıştırılmadan hemen önce yeniden doğrulanır). Ulaşılamazsa dürüst ileti ve elle indirme alanı. Açılışta ağ yok, telemetri yok, dışarı kişisel veri çıkmaz. Evrak hattı (WeasyPrint) yalnız `data:` ve paket içi `file:` kaynağı açar (§4.1) | Aile T11 (ISBN künye kapısı ALMA). [BSG Yön. md. 11/23](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11) bulut depolamaya veri aktarılmaz. Koruma: `test_dis_istek_kapilari` (kaynak), `test_acilista_dis_istek` (gerçek açılış, ağ tuzağı), `http(s)` kaynaklı belgenin PDF'e çevrilmesi (ağ tuzağı; denetim GA-22) | Kesin |
| TK5 | Pencere | T6: çarpı programı kapatır, onay sorulmaz; tepsi, `--tepside`, otomatik başlatma, uyku engeli yoktur. Uzun yazma işi sürerken kapanış **bir kez ertelenir** ("İşlem bitiyor, program kendiliğinden kapanacak"; en çok 60 sn) — bu bekletmedir, soru değildir; temiz kapanış işareti yalnız iş sayacı sıfırken yazılır (§4.2). Tek kopya kanalı, WAL checkpoint, Linux SIGTERM köprüsü kalır; Linux Qt kurulumu `desktop/qt_kurulum.py`'ye taşınır (§4.5) | T6 kullanıcı kararı; Kelebek Sınav davranışı, Kütüphane'nin kazanımlarıyla ([iskelet envanteri §9.3](../kesif/2026-10-31-iskelet-envanteri.md)). Kütüphane'de çarpı programı gizlediği için uçuştaki işi kesen yol yoktu (denetim GA-13) | Kesin (T6); erteleme öneri |
| TK6 | Paketleme | Windows: PyInstaller onedir + Inno Setup · Linux: `.deb` + taşınabilir `.tar.gz`, Debian 11 (bullseye, glibc 2.31) kabında derleme · PySide6 6.8.3 tavanı · kurulum provası Debian 11/12/**13** | Pardus 21/23/25 (Pardus 25 Debian 13 tabanlı); TB27 tavanı; TB5 | Kesin + Debian 13 eki |
| TK7 | Kurulum yetkisi | `PrivilegesRequired=lowest` + `PrivilegesRequiredOverridesAllowed=dialog`: kurucu iki seçeneği sunar. **Kullanıcı başına kurulum** (`{autopf}` → `%LOCALAPPDATA%\Programs`) yalnız programı kendi Windows hesabında tek başına kullanan MY senaryosu içindir. **Ortak "OAB" Windows hesabı** (§15 M-8) kullanılacaksa kurulum **yönetici kipinde** (Program Files) yapılır. Kılavuz iki senaryoyu ayrı yazar | Kütüphane'de yönetici kurulumunun iki gerekçesi vardı: güvenlik duvarı kuralı ve "kurulum dizini standart kullanıcıya salt okunur" (`kutuphane-defteri.iss`). OAB'de ilki düşer, ikincisi ortak hesapta sürer: kullanıcı başına kurulumda program dosyaları o Windows hesabınca değiştirilebilir; ortak hesabı kullanan herkes programı değiştirip başkalarının parolasını toplayabilir (§4.3 tehdit 20). Bedel: yönetici kurulumunda her güncelleme yönetici (BTR) ister. Risk: AppLocker/SRP kullanıcı dizininden exe çalıştırmayı engelleyebilir (doğrulanmadı; F7 sahada) | §15 (M-1) |
| TK8 | Güvenlik çekirdeği | Aileden: Argon2id (RFC 9106 düşük bellek profili, ~0,2 sn), Fernet alan şifrelemesi, kör indeks, fail-closed yazma (`KeyMissingError` → 409 `parola_gerekli`), güvenlik dosyası kayıp kilidi, X25519 + AES-256-GCM şifreli yedek (`Connection.backup()`), kademeli gecikme. **Aileden ayrılan dört nokta:** (1) dosya deposu şifrelemesi yenidir (dosya başına anahtar, §4.4.4; TK22); (2) yedek kabı dosya bölümü taşır (`ODBAK\x03`, §4.4.7); (3) `from_db_value` **katı kipte** çalışır: kilit açıkken çözülemeyen ya da token olmayan dolu değer düz metin diye dönmez, `CorruptField` işaretiyle döner ve panoya bütünlük uyarısı düşer; hoşgörü yalnız `gecis` sürerken açıktır (§13 D48); (4) hatalı deneme sayacı hesap başınadır (TK15). Şifrelenecek alanların **listesi** §5'tedir | [KVKK md. 12/1](../mevzuat/6698-kvkk.md#madde-12) teknik tedbir; [BSG Yön. md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) taşınabilir ortamda şifreleme; Kütüphane'de kapalı denetim bulguları (TB26). Ailenin hoşgörüsü düz metin döneminden kalmadır; OAB'de düz metin dönemi hiç olmadı (§13 D29), hoşgörü SQLite'ta şifreli sütuna yazılan düz metni meşru veri gibi gösterirdi (denetim GA-9) | Kesin (aile) + öneri (dört ayrılış) |
| TK9 | Hesaplar | T1: kişisel hesaplar; veri anahtarı (DEK) her hesap için ayrı sarılır; rol ve organ bağı veritabanında, `Account` satırı mühürlü (§4.6.1); kurtarma anahtarını yalnız `yonetici` yeniler, anahtar okul müdürlüğünde mühürlü zarfta durur (D3; §4.4) | T1 kullanıcı kararı; [BSG Yön. md. 7/2, 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) ve [md. 9/2-e](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) (kullanıcı adı ve şifre paylaşılmaz, herkes kendi hesabıyla çalışır). Yönergenin 7. maddesi aktif dizin hesabı içindir; programa kıyasen uygulanır | Kesin (T1) |
| TK10 | Yedek başlığı | Şifreli yedeğin başlığı **yalnız kurtarma bölümünü** ve kurtarma anahtarının **kimliğini** (sıra no + üretim tarihi; anahtar kâğıdında da basılıdır) taşır; hesap sarmalları yedeğe girmez. Aynı bilgisayarda geri yükleme güncel `guvenlik.json` + bir `yonetici` hesabının parolasıyla, yeni bilgisayarda kurtarma anahtarıyla açılır; program "bu yedek <no> numaralı, <tarih> tarihli kurtarma anahtarıyla açılır" der | TB23 OAB'de ağırlaşır: dönemi biten veli üyenin eski parolası + eski yedek başlığı → DEK. Bedel: yeni bilgisayara taşıma kurtarma anahtarı ister — bu zaten yönetici işidir. Anahtar kimliği hangi zarfın hangi yedeği açtığını gösterir (denetim SU-12) | Öneri |
| TK11 | Kapanan hesap | Hesap kapanınca sarmalı `guvenlik.json`'dan **ve bütün `guvenlik-arsiv-*` kopyalarından** silinir; `Account` satırı (rol, tanıtıcı, kapanış tarihi) denetim izi için kalır. **İki depo kuralı:** giriş, sarmal açıldığında **ve** `Account` satırı var, açık ve mühürlüyse açılır; kapanışta önce veritabanı, sonra dosyalar yazılır; açılışta ve geri yüklemeden sonra iki depo karşılaştırılır (§4.6.1) | Arşiv kopyasında sarmal kalırsa kapatma anlamsızdır (TB17/TB23); satırın kalması altın kural 4. Dosya yazımı SQLite işlemine giremez; sıra ve yarıda kalma tanımlı olmalı (denetim GA-11) | Öneri |
| TK12 | DEK yenileme | **Hesap geçişinde** (yeni görev bölümünden sonra, eski organ hesapları kapanınca ve yeni organ hesapları açılmadan önce; §4.4.5) ve **MY değişiminde** DEK yenilenir; `yonetici` gerektiğinde elle de başlatır. Şifreli alanlar, kör indeksler, hareket parmak izleri, hesap mühürleri, dosya anahtarı sarmalları ve iz anahtarlarının şifreli kopyaları yeni DEK'le **tek SQLite işleminde** yazılır; yedek anahtar çifti yenilenir; yeni iz anahtarı üretilir, zincir **yeniden mühürlenmez**. Yeni kurtarma anahtarı basılır, okul müdürlüğünde mühürlü zarfta saklanır; eski zarf, yeni anahtarla alınan tam yedek açılıp doğrulandıktan sonra imha tutanağıyla yok edilir (D3). Sıra ve yarıda kalma §4.4.4 | Eski kurulun bildiği hiçbir şey (parola, eski başlık, arşiv kopyası, iz anahtarı) **yenilemeden sonraki** veriyi ve yedekleri açmaz; genel kurul ile hesap geçişi arasındaki pencere (görev bölümü en çok bir hafta, [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) kalan risktir. Kütüphane v1 dışı bırakmıştı (TB17, TB23); OAB'de veri küçük, dosya içerikleri yeniden şifrelenmez (yalnız sarmalları, TK22) | §15 (M-2) |
| TK13 | Rol izinleri | **İki katman.** (1) Uç katmanı: uç + yöntem (+ parametre) matrisi (`rol_izinleri.py`; ailenin `govdede_yok`/`yalniz_sorgu` denetçileri), kısmi yetki ayrı uçla verilir, yeni uç varsayılan kapalı, URL desenlerini dolaşan koruma testi; ret 403 `{"code":"rol_yetkisiz"}`. (2) Servis katmanı: kapanmış dönem, maskesiz okuma, kişisel veri içeren çıktı, rol-özel işaretler ve kayıt sahipliği tek kapıdan geçer (`yetki(rol, eylem, kayıt)`; §4.4.2). Rol kriptografik değildir: kaza önleyici + izlenebilirlik; `Account` satırı mühürlüdür (§4.6.1) | Kütüphane görevli kipinin deseni (`kip_izinleri` "uç + yöntem (+ parametre)", `test_kip_koruma`); [iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md) risk 1. URL dolaşan test yalnız uç düzeyini kanıtlar (denetim GA-18) | Öneri |
| TK14 | Oturum | Süreç içi tek oturum (`OturumDurumu`, tek nesne); kullanıcı değiştirmek = Kilitle + başka hesapla aç; **kilitlenme ve her kilit açılışı ön yüzde sorgu önbelleğini ve modül belleğini sıfırlar** (pencere içeriği yeniden yüklenir); boşta süre dolunca **kilit** (görevliye iniş yok), uzun yazma işi sürerken boşta kilit ertelenir; varsayılan 10 dk (ayar 3-30); mutlak süre yok | [BSG Yön. md. 10/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) kullanılmayan bilgisayarda parolalı kilit (süre vermez). Görevli kipi olmadığından Kütüphane'nin 30 dk mutlak süre gerekçesi düşer; 3 dk velinin yavaş yazdığı formda can sıkar. Önceki hesabın yüklediği maskesiz veri sonraki oturumda kalmamalı (denetim GA-23); iş ortasında DEK silinmemeli (denetim UY-1) | §15 (M-3) |
| TK15 | Parola politikası | En az 8 karakter (sert) · küçük harf, büyük harf, rakam ve simge (varsayılan sert) · 180 günü geçen parola girişte değiştirilir · ilk girişte geçici parola değiştirilir · organ hesaplarına **en az 12 karakterlik parola cümlesi önerilir**, sihirbazda güç göstergesi · kademeli gecikme hesap başına sayılır; ardışık hatalı denemede organ ve müdür hesabı askıya alınır, `yonetici` açar; `yonetici` hesabında askı yoktur (kurtarma anahtarı yolu kalır) | [BSG Yön. md. 9/2-a, b, ç](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9); geçici parolanın değişimi [md. 7/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7); askı [md. 7/3](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) ve 9/2-c'nin karşılığıdır (ailede "hesabı açacak yönetici yok" gerekçesi OAB'de geçmez; denetim GA-15). Her sarmal DEK'i tek başına verir: şifreli alanlar en zayıf hesap parolası kadar korunur (§4.3 tehdit 9). Argon2id profili (64 MiB, t=3) aynı kalır: hesap sayısı deneme başına maliyeti değiştirmez, zayıf parola olasılığını artırır; çare parolanın gücü ve kapanan hesabın sarmalının silinmesidir (TK11); profili yükseltmek 4 GB'lık makinede her girişi yavaşlatır (denetim GA-16). Yönergenin "kullanıcı" tanımı Bakanlık bilişim kaynağını kullanma yetkisi verilen konukları da kapsar ([md. 2/1, 4/1-j, k](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)) — veli kullanıcı için yorum | §15 (M-4, M-12) |
| TK16 | Denetim izi | Her yazma, veri satırıyla **aynı işlemde** `AuditTrail`'e hesap + rol + zaman (Europe/Istanbul) ile düşer; ekleme-yalnız. Satır **kişisel veri taşımaz** ("kaydın özeti"): kayıt kimliği, değişen alan adları, izinli kişisiz alanların (tutar, tarih, durum, numara, kod) önceki ve sonraki değeri ve kaydın **içerik MAC'i**. Zincir DEK'ten bağımsız **iz anahtarıyla** (İA) HMAC mühürlüdür; kilitliyken yazılan sistem olayları ileriye dönük güvenli **kilitli kip anahtarıyla** mühürlenir; zincirin başı her kilitlenmede **çapa** olarak yazılır, her ay kâğıda iner; kilit açılışında kendiliğinden, DK modülünde tam doğrulanır ("kayıt bütünlüğü denetimi"). Model ve kurallar §4.6 | Altın kural 4; Kütüphane'de `AuditLog` bilerek yoktu ([iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md)). Zincir program dışından SQLite'ta değişikliği görünür kılar (§4.3 tehdit 7). Değer kopyası tutulsaydı ekleme-yalnız iz KVKK silmesini boşa çıkarırdı (denetim KM-2, UY-2). İA DEK'ten türeseydi kilitliyken iz yazılamaz, DEK yenilemesi zinciri yeniden yazıp kâğıttaki çapaları geçersiz kılardı (denetim GA-8, UY-1) | Öneri; model §4.6 |
| TK17 | Evrak hattı | T2: tek içerik modeli, iki çizici. PDF: `shared/pdf.py` (aile tek kapısı, WeasyPrint, süreç kilidi). Word: `shared/docx.py` (python-docx tek kapısı). Cephe: `shared/evrak.py` (belge tanımı + bağlam → içerik → {pdf, docx}). LibreOffice/Word gerekmez. PDF ↔ Word içerik eşdeğerliği testi (pypdf metni ↔ python-docx metni); `w:caps` kullanılmaz, büyük harf `tr_upper`'dan; `--evrak-duman` (çıkış 12). İçerik modeli ve katalog §9'da | T2 kullanıcı kararı; [iskelet envanteri §7.2](../kesif/2026-10-31-iskelet-envanteri.md) ekleme noktası | Kesin (T2); yerleşim öneri |
| TK18 | İçe/dışa aktarım güvenliği | İçe alınan dosya (banka özeti, e-Okul listesi, TEFBİS Excel) güvenilmeyen girdidir: boyut tavanı (`OD_MAX_UPLOAD_SIZE_MB`), yalnız `.xlsx`/`.xls`/`.csv`, makrolu biçim reddi, türü imza baytından denetim, openpyxl `read_only` + `data_only`, önizleme + onay. Dışa yazılan xlsx'te dış kaynaklı metin hücreye **metin tipiyle** yazılır. `python-magic` eklenmez | openpyxl `=` ile başlayan dizeyi formül sayar; banka açıklaması dış kaynaklıdır (formül enjeksiyonu). libmagic Windows'ta ayrı DLL ister ([OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) S-26) | Öneri |
| TK19 | Periyodik işler | Celery yok. Gün değişimi kapısı (`od-gunluk`; açılışta + saatte bir): günlük yedek + bütün yerel yedek öneklerinin rotasyonu (§4.4.7); sonraki fazların işleri kayıt defterine eklenir. **DEK yokken veritabanına iş verisi yazılmaz:** DEK isteyen gün işi kilitliyken "ertelendi" döner ve ilk kilit açılışında koşar; kilitliyken yalnız yedek ve kişisiz sistem olayı yazılır (§4.6.3). Bakım kapısı `katalog/bakim.py`'den `shared/bakim.py`'ye taşınır ve uzun yazma işlerini sayar (§4.2) | Aile T9. Bakım kapısı bugün katalog paketindedir; katalog sökülünce sessizce devre dışı kalır (§13 D3). Ailede kilit DEK'i silmiyordu (görevli kipine iniş); OAB'de boşta kilit DEK'i siler (denetim UY-1) | Öneri |
| TK20 | `SECRET_KEY` | Sabit kalır; program imza, Django oturumu ve CSRF kullanmaz | Aile T17 | Kesin |
| TK21 | Kimlik | Kimlik sabitleri §2.3; kalıntı taraması F1a kapısıdır | Plan §1.4 | Kesin |
| TK22 | Dosya deposu ve yedek kapsamı | Ekler ve üretilmiş evrak veri dizinindeki `dosyalar/`'da, **dosya başına rastgele anahtarla** AES-256-GCM şifreli durur; anahtar DEK'ten türeyen sarmal anahtarıyla sarılıp `Attachment.key_wrap`'te tutulur (§4.4.4). **Yerel yedekler** (günlük, `pre-*`) veritabanı görüntüsü + dosya manifestosudur; **dışarı çıkan yedek** (indirme, USB, yeni bilgisayara taşıma) veritabanıyla birlikte dosya deposunun tamamını tek şifreli dosyada taşır. Bütün yerel yedek önekleri 14 günlük rotasyondadır (§4.4.7) | Aile yedeği yalnız SQLite görüntüsüdür; dosyalar yedeğe girmeseydi disk arızasında ve yeni bilgisayara taşımada ekler kaybolurdu (denetim GA-1). Dosya başına anahtar sayesinde DEK yenilemesi dosyaları yeniden yazmaz, yalnız sarmalları tek SQLite işleminde yeniler (yarıda kalan dosya yazımı olmaz; denetim GA-2, UY-3); dosyalar değişmediği için veritabanı yedeği dosya deposuyla tutarlı kalır ve 14 günlük tam yedek dizisinin disk bedeli doğmaz | Öneri |

### 2.3 Kimlik sabitleri

*Plan §1.4'teki taslak burada kesinleşir. Kural: program adını, kısa adını ya da önekini taşıyan **her** dize bu
tablodan gelir; program adı taşımayan genel adlar (§2.3.2) değişmez. GUID ve gizli değer belgeye yazılmaz.
Karşılıkların yeri ve sayımı: [iskelet envanteri §4.1-4.2](../kesif/2026-10-31-iskelet-envanteri.md).*

#### 2.3.1 Değerler

| Öğe | OAB Defteri | Kütüphane karşılığı | Not |
|---|---|---|---|
| **Ad ve önek** | | | |
| Program adı (arayüz, pencere başlığı, Inno `AppName` ve `AppPublisher`, `.desktop` `Name`) | `OAB Defteri` | Kütüphane Defteri | Yayıncı alanında kişi adı ve unvan yok |
| Kısa ad (exe, paket, dosya adları, argparse) | `oab-defteri` | `kutuphane-defteri` | |
| Python adı (spec, logger) | `oab_defteri` | `kutuphane_defteri` | |
| Bitişik ad (Windows nesneleri, veri dizini) | `OABDefteri` | `KutuphaneDefteri` | |
| Önek | `od` · `OD_` · `X-OD-` · `--od-` · `od:` | `kd` · `KD_` … | |
| **Ortam** | | | |
| Ortam değişkenleri | `OD_SESSION_TOKEN`, `OD_DEBUG`, `OD_APP_VERSION`, `OD_APP_HOME`, `OD_DATA_DIR`, `OD_SECURITY_DIR`, `OD_BACKUP_DIR`, `OD_BACKEND_DIR`, `OD_FRONTEND_DIR`, `OD_RTHOOK_UYARI`, `OD_ONCEKI_OTURUM`, `OD_SECRET_KEY`, `OD_MAX_UPLOAD_SIZE_MB`, `OD_UPDATE_REPOSITORY`, `OD_WITH_QT`, `OD_DLL_DIR`, `OD_SKIP_PIP`, `OD_BUILD_IMAGE`, `OD_AG_TUZAGI_KAYIT` | `KD_*` (24 ad) | ALMA: `KD_KATALOG_PORT`, `KD_KATALOG_HOST`, `KD_PROVA_ESER`, `KD_EKRAN_DERLE`, `KD_YAVAS`. `OD_UPDATE_REPOSITORY` yalnız geliştirme ve test içindir: paketli yapıda (`sys.frozen`) **okunmaz**, testle sabitlenir (ailede koşulsuz okunuyordu; §13 D51) |
| Veri dizini | Windows `%LOCALAPPDATA%\OABDefteri` · Linux veri `~/.local/share/oab-defteri`, günlük `~/.local/state/oab-defteri`, önbellek `~/.cache/oab-defteri` | `KutuphaneDefteri` / `kutuphane-defteri` | `%APPDATA%` (gezici profil) ve `ProgramData` seçilmez (§4.5). Linux'ta dizinler 0700, gizli dosyalar 0600 (§4.5) |
| **Oturum, ön yüz** | | | |
| Oturum çerezi / başlığı | `od_oturum` / `X-OD-Token` | `kd_oturum` / `X-KD-Token` | |
| Etkinlik başlığı | `X-OD-Etkinlik` | `X-KD-Etkinlik` | Boşta kilit (TK14) yalnız bu başlığı taşıyan istekle tazelenir |
| Ret kodları | 403 `rol_yetkisiz` · 423 `locked`, `guvenlik_dosyasi_kayip` · 409 `parola_gerekli` · 503 `restart_required` | 403 `kip_yetkisiz` | `rol_yetkisiz` yenidir (T1); ötekiler aynen |
| DOM olayları | `od:kilit-kapisi`, `od:rol-yetkisiz`, `od:yeniden-baslat-gerekli`, `od:guncelleme-denetlendi` | `kd:*` | `kd:cik-iste` ALMA (T6); `kd:kip-yetkisiz` → `od:rol-yetkisiz` |
| CSS | değişkenler `--od-*`; sınıflar `od-page-title`, `od-page-header`, `od-page-description` | `--kd-*`, `kd-page-*` | Sitedeki `od` paletiyle karıştırılmaz |
| Tarayıcı deposu anahtarları | `oab-defteri-density`, `oab-defteri-sidebar-collapsed`, `oab-defteri-dismissed-update`, `oab-defteri-theme` | `kutuphane-defteri-*`, `oys-theme` | `-okuma-sesi` ALMA (barkod); `oys-theme` OYS kalıntısıydı (§13 D13). Tarayıcı deposuna kişisel veri ve form taslağı yazılmaz (§4.2) |
| Ön yüz paket adı | `oab-defteri-frontend` | `kutuphane-defteri-frontend` | |
| Rol kodları | `yonetici`, `baskan`, `baskan_yardimcisi`, `muhasip`, `sekreter`, `denetleme_kurulu`, `mudur` | — (yeni) | Üç bölümün ortak adı (§4.4, §5, §7) |
| **Kripto ve yedek** | | | |
| Yedek uzantısı / MAGIC | `.odbak` / `ODBAK\x03` | `.kdbak` / `KDBAK\x02` | Kap aileden ayrılır: aile kabının ardına dosya bölümü eklenir (§4.4.7); başlık TK10 ile değişir |
| Dosya kabı MAGIC | `ODDOSYA\x01` | — (yeni) | Dosya deposundaki her dosyanın başı (§4.4.4) |
| Yedek HKDF bilgileri | `OABDefteri/backup/private/v1`, `OABDefteri/backup/envelope/v1` | `KutuphaneDefteri/backup/…` | İki dizge |
| Kör indeks HKDF | `od-kor-indeks` | `kd-kor-indeks` | |
| Anahtar parmak izi HMAC | `od-anahtar-parmak-izi` | `kd-anahtar-parmak-izi` | |
| Dosya sarmal anahtarı HKDF (DEK'ten) | `od-dosya-sarmal/v1` | — (yeni) | Dosya başına anahtarı saran anahtar (§4.4.4; TK22) |
| Hareket parmak izi HKDF (DEK'ten) | `od-hareket-parmak-izi/v1` | — (yeni) | `BankTransaction.fingerprint` anahtarlı HMAC'tir; şifreli açıklamadan türeyen özet anahtarsız olamaz (denetim KM-11) |
| Hesap mührü HKDF (DEK'ten) | `od-hesap-muhru/v1` | — (yeni) | §4.6.1 |
| İz anahtarı türevleri (HKDF, İA'dan) | `od-denetim-izi/v1` (zincir) · `od-kayit-ozeti/v1` (içerik MAC'i) · `od-iz-capa/v1` (çapa mührü) · `od-iz-kilitli/v1`, `od-iz-kilitli-mac/v1` (kilitli kip) | — (yeni) | §4.6.3. İA DEK'ten **türemez**; kurulumda ayrı üretilir |
| Yedek indirme adı | `oab-defteri-yedek-<damga>.odbak` | `kutuphane-defteri-yedek-<damga>.kdbak` | Tam yedek (dosyalar dâhil) |
| `guvenlik.json` şema sürümü | `"surum": 2` (hesaplı şema: `hesaplar[]` ile `hatali` sayacı ve `askida` işareti; `kurtarma.no`, `kurtarma.tarih`) | 1 | §4.4.4 |
| **Windows** | | | |
| Inno AppId | **yeni GUID üretilecek** | sabit GUID | Kütüphane'ninki asla kullanılmaz; bir kez üretilir, bir daha değişmez |
| Mutex | `OABDefteri`, `Global\OABDefteri` | `KutuphaneDefteri`, `Global\…` | Inno `AppMutex` kullanılmaz (§4.2) |
| Adlı olaylar | `OABDefteri.Goster`, `OABDefteri.Kapat` | `KutuphaneDefteri.*` | |
| AUMID | `OABDefteri.Desktop` | `KutuphaneDefteri.Desktop` | |
| exe / dağıtım dizini | `oab-defteri.exe` · spec `DIST_NAME = "oab-defteri"` | `kutuphane-defteri.exe` | |
| Kurulum dizini | `{autopf}\OAB Defteri` | `{autopf}\Kütüphane Defteri` | Yönetici kipinde `Program Files\OAB Defteri`, kullanıcı kipinde `%LOCALAPPDATA%\Programs\OAB Defteri` (TK7) |
| Kurulum dosyası | `oab-defteri-<sürüm>-win64-setup.exe`; `updates.INSTALLER_PATTERN` `^oab-defteri-.+-win64-setup\.exe$` | `kutuphane-defteri-…` | `build.ps1`, `.iss`, `updates.py` birlikte |
| Kurulu simge | `oab-defteri-<sürüm>.ico` | | |
| Inno katalog kimlikleri (kural adı, HKLM anahtarı, görev adı, `RunOnceId`) | — | var | ALMA |
| **Paket ve süreç** | | | |
| spec / rthook | `oab_defteri.spec`, `rthook_od.py` | `kutuphane_defteri.spec`, `rthook_kd.py` | |
| Logger | `oab_defteri` + alt adlar (`.server`, `.window`, `.kanal`, `.okul`, `.guvenlik`, `.restore` …) | `kutuphane_defteri.*` | |
| İş parçacıkları | `od-wsgi`, `od-kanal`, `od-gunluk`, `od-cikis` | `kd-*` | ALMA: `kd-katalog*`, `kd-tepsi` |
| Duman kipleri | `--autotest`, `--pdf-duman`, `--bagimlilik-duman`, `--geri-yukle`, **`--evrak-duman`** (yeni) | + `--dagitim-duman` | `--dagitim-duman` ALMA; çıkış kodları §4.2 |
| İstisna işleyicisi | `od_exception_handler` | `kd_exception_handler` | |
| Django `SECRET_KEY` varsayılanı, test veritabanı adı | `oab-defteri` önekli yeni sabitler | program adını taşır | Değer belgeye yazılmaz (gizli değildir, TK20) |
| **Linux** | | | |
| Debian paketi | `oab-defteri`, `Section: education` | `kutuphane-defteri` | |
| Yerleşim | `/opt/oab-defteri`, `/usr/bin/oab-defteri`, `/usr/share/applications/oab-defteri.desktop`, `/usr/share/doc/oab-defteri` | | Hepsi aynı anda |
| `.desktop` | `Name=OAB Defteri`, `StartupWMClass=oab-defteri`, hicolor simge adı `oab-defteri` | | `Keywords` OAB terimleriyle |
| Taşınabilir arşiv | `oab-defteri-<sürüm>-linux-x64.tar.gz` | | |
| Simge dosyaları | `oab-defteri-{16…512}.png`, `oab-defteri.ico`, `oab-defteri-logo.png` | `kutuphane-defteri-*` | Logo yeni (TB4); dosya adları da taranır |
| **Geliştirme ve dağıtım** | | | |
| Compose projesi | `oab-defteri` | `kutuphane-defteri` | |
| Kapı geçici dosyası | `.od-depo-listesi.tmp` | `.kd-depo-listesi.tmp` | `.gitignore` ile birlikte |
| Yasaklı adlar listesi (depo dışı) | `.od-yasakli-adlar.txt` | — (yeni) | `.gitignore`'da; sızıntı kapısı gerçek adları buradan okur, ad depoya girmez (§13 D42) |
| Test geçici dizinleri | `od-guvenlik`, `od-yedek` | `kd-guvenlik`, `kd-yedek` | `backend/conftest.py` |
| Güncelleme deposu | `<github-kullanıcısı>/oab-defteri` | `<…>/kutuphane-defteri` | Deponun açılışı yayın işidir (altın kural 8) |
| Site | sayfa `okulapp.org/oab-defteri` (`src/pages/oab-defteri/**`), palet `od`, `src/data/od-release.json`, gerekirse `src/layouts/ODLayout.astro`, varlıklar `public/oab-defteri/**` | `kd`, `kd-release.json`, `KDLayout.astro` | Ortak alan kuralları §17 |
| R2 öneki | `oab-defteri/` | `kutuphane-defteri/` | `packaging/r2-yukle.sh` `R2_ONEK` |

#### 2.3.2 Değişmeyen genel adlar

Program adı taşımadıkları ve veri dizinleri ayrı olduğu için kardeş programlarla çakışmazlar; çevrilmez:
`db.sqlite3`, `instance.lock`, `surum.json`, `guvenlik.json`, `guvenlik-arsiv-<damga>.json`, `yedekleme.json`,
`temiz-kapanis.json`, `gun-kapisi.json`, `kanal.sock`, `cokme.log`, yedek önekleri `gunluk-`, `pre-migrate-`,
`pre-parola-`, `db-onceki-<damga>.sqlite3`, kanal komutları `goster`/`kapat`, kapı nöbetçisi `KAPI_OK_<ad>`.

Yeni genel adlar: dosya deposu dizini `dosyalar/` (dosya adı `stored_name`, uzantısız), denetim izi durum dosyası
`iz-durumu.json` (çapa ve kilitli kip; §4.6.3), geri yükleme notu `geri-yukleme-notu.json` (§4.4.4). Yeni yedek
önekleri: `pre-kapanis-` (dönem kapanışı, §7.8) ve `pre-dek-yenileme-` (TK12). `pre-anonim-` F4'ten itibaren elle
KVKK silme tetiğinde kullanılır. Bütün yedek önekleri (`gunluk-`, `pre-migrate-`, `pre-parola-`, `pre-anonim-`,
`pre-kapanis-`, `pre-dek-yenileme-`) ve `db-onceki-` rotasyon kümesindedir; küme kapalıdır ve testle sabitlenir
(§4.4.7).

#### 2.3.3 Kalıntı taraması (F1a kapısı)

`packaging/tests/test_kimlik_kalintisi.py` (UYARLA) depo ağacını dolaşır, her dosyanın **yolunu** ve **satırlarını**
`katla()` uygulanmış metinde arar (İ/I/ı → i, ayrışık U+0307 silinir, `casefold`). `katla()` "ü"yü katlamaz; kalıp
bu yüzden "ü"yü karakter sınıfıyla yazar (plan §1.4'ün F0 ekiyle düzeltilmiş hâli). Kelime sınırı `(?<![^\W_])`:

| Kaynak | Kalıp | Yakaladığı örnek |
|---|---|---|
| Kütüphane Defteri | `k[uü]t[uü]phane[ _-]?defteri` | "Kütüphane Defteri", "KÜTÜPHANE DEFTERİ", `kutuphane-defteri`, `KutuphaneDefteri.Kapat` |
| | `(?<![^\W_])kd[_:-]` | `KD_DATA_DIR`, `kd-wsgi`, `kd:kilit-kapisi`, `--kd-renk` |
| | `x-kd-` | `X-KD-Token`, `X-KD-Etkinlik` |
| | `kdbak` | `.kdbak`, `KDBAK` |
| Kelebek Sınav (aynen) | `kelebek`, `(?<![^\W_])ks[_:-]`, `x-ks-`, `ksbak` | |
| Disiplin Defteri (aynen) | `disiplin[ _-]?defteri`, `x-dd-`, `ddbak` | |
| OYS | `(?<![^\W_])oys-` | `oys-theme` |

- **Taranmaz:** yalın "kütüphane", "disiplin", "sınav", "katalog" (meşru metin: "Python kütüphanesi", "evrak kataloğu").
- **Kapsam dışı yollar:** `.git`, `node_modules`, `__pycache__`, `*_cache`, `docs/`, `frontend/dist`, `backend/data`,
  `build`, `dist`, `.claude/settings.local.json`. **Muaf dosyalar:** `CLAUDE.md`, `AGENTS.md` (köken anlatır).
  `README.md` herkese açıktır ve kapsamda kalır: köken cümlesi yazılmaz (§15 M-9).
- `test_tarama_kapsami_bos_degil` beklenen yolları: `packaging/windows/oab-defteri.iss`,
  `packaging/pyinstaller/oab_defteri.spec` (ötekiler aynen). Kalıp örnekleri testine yukarıdaki sütundaki örnekler
  dosyanın kendi bölücüsüyle (`X-K|D-Token`, `yedek.k|dbak`, `o|ys-theme` biçiminde) eklenir.
- **Negatif örnek:** kalıp `(?<![^\W_])kd[_:-]` alt çizgiden sonra da yakalar; bu yüzden iş kodunda `konum_kd_metni` gibi
  bir ad olmaz. Evrak konum cümlelerinin kısa adları (KDT, TFB, DFT; §9.2) kodda tam adla yazılır
  (ör. `konum_karar_defteri_taslagi`); kalıp örnekleri testine bu ad negatif örnek olarak girer (denetim UY-20).
- **Kapı dışı, uyarı düzeyi:** "alan kalıntısı" listesi (ödünç, nüsha, barkod, ISBN, tepsi, görevli kipi, Ağ Kataloğu,
  künye, öğrenci, okul numarası, kütüphane masası) F1a-2'de bir kez elle koşulur; "katalog" gibi meşru kullanımlar
  yüzünden kapıya girmez. Aileden gelip kütüphaneye özgü kullanıcı metni taşıyan üç dosya bu elle taramada **adıyla**
  okunur: `backend/templates/documents/kurtarma_anahtari.html`, `backend/apps/okul/lock_middleware.py`,
  `backend/apps/okul/services/recovery_key_document.py` (§12.B UYARLA; denetim GA-19).

---

## 3. Hukuki konum ve mevzuat

### 3.1 Konum: resmî kayıt defterdir, program hazırlar

| Resmî kayıt | Dayanak | Programın yaptığı | Programın yapmadığı |
|---|---|---|---|
| Yönetim kurulu karar defteri (noter tasdikli, el yazısı) | [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/1-b, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Karar **taslağı** üretir; sekreter deftere yazınca "deftere işlendi" işareti, defter sıra no ve sayfası kaydedilir; deftere yazılmış ama yeter sayısı olmayan karar da "defterde sakat" diye iz olarak tutulur (§5.2.4) | Kararı resmîleştirmez; taslak "karar defterine el ile yazılır" ibaresini taşır |
| Gelir-gider defteri (il/ilçe MEM tasdikli) | [md. 23/1-ç, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Tasdikli deftere **geçirilecek** aylık baskı (tarih, sıra no, belge türü ve no, açıklama, gelir, gider, kalan, karar no, gelir-gider türü — saha 1b), defterin sayfa düzeninde; "bu baskı şu sayfalara geçirildi" toplu işareti (§7.3) | Defterin yerine geçmez; Yönetmelik defterin sütunlarını belirlemez, program asgari sütun setini önerir |
| TEFBİS kayıtları (okul idaresi girer) | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | TEFBİS ekran sırasıyla "girilecekler" listesi; "TEFBİS'e girildi" işareti; sürüm 2'de TEFBİS Excel çıktısıyla mutabakat | TEFBİS'e giriş yapmaz, TEFBİS şifresi saklamaz (K6) |
| Makbuz koçanı (ciltli, seri-cilt-sıra numaralı, mühürlü) | [md. 16/5-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/1-e, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1). Koçanın [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)'deki "diğer defter ve belgeler" tasdikine girip girmediği yorum sorusudur (§15 B-15) | Koçan envanteri, kullanılan ve iptal yaprak kaydı, numara tekilliği, isteğe bağlı tasdik kaydı | Makbuz basmaz (K5) |
| Genel kurul tutanak dosyası, gelen-giden evrak defteri, harcama dosyası | [md. 23/1-a, c, d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Tutanak ve yazı taslakları, evrak kaydı, harcama dosyasının dizini | İmzalı aslın yerine geçmez; veli adını taşıyan katılım cetvelinin aslı yalnız kâğıttadır (§5.4) |

**Her çıktıda konum ibaresi.** Karar taslağı, deftere geçirilecek baskı ve TEFBİS listesi, hangi resmî kayda
girileceğini ve programın yardımcı kayıt olduğunu söyleyen bir ibare taşır (biçimi §9). İbare kılavuzda, sitede ve
ilk açılış ekranında da yer alır (CLAUDE.md §1).

**Yardımcı kaydın değeri.** Program kayıtları resmî değildir ama denetimde kanıt sunar: kararın taslağı ile defterdeki
hâlinin tutarlılığı, banka-defter-TEFBİS denkliği (SGB 02.12.2019 yazısının istediği; ön değerlendirme §2.5), sürelerin
tutulup tutulmadığı. Bu yüzden program kayıtları da altın kural 4'e tabidir: silinmez, ters kayıtla düzeltilir,
kapanan dönem kilitlenir (yalnız defter ve TEFBİS işaretleri ile yeniden basım yazılabilir, §5 O2), her değişiklik
denetim izine yazılır.

### 3.2 Mevzuat korpusu ve kural paketi

- Programın koyduğu her oran, süre, çarpan ve sınır **kural paketinde** durur ve `madde` alanıyla
  `docs/mevzuat/` korpusundaki bir çapaya bağlanır (§6). Çapası olmayan kural paketi yüklenmez (atıf kilidi; §10).
- Korpus [BENIOKU](../mevzuat/BENIOKU.md)'daki protokolle tutulur: resmî kaynaktan birebir metin, şerhler aynen,
  `(Mülga:…)` hüküm yok, `(Değişik:…)` en güncel hâl; her dosyada `oab-teyit` tarihi. 31.10.2026'da 26 metnin 18'i
  mevzuat.gov.tr konsolide metniyle madde madde karşılaştırıldı.
- Mevzuat değişince: korpus güncellenir → değişen madde hangi kurallara dayanak, bakılır → yeni kural sürümü açılır;
  kapanmış dönemler eski sürümle hesaplanmaya devam eder (altın kural 2).
- Yönetmeliğin mülga metinlere iki atfı güncel karşılığıyla gösterilir: md. 18/3'teki eski Taşınır Mal Yönetmeliği →
  [TMY 2024](../mevzuat/tasinir-mal-yonetmeligi.md) (md. 41/2 atıf hükmü); [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)'deki
  1988 arşiv yönetmeliği atfı → [Devlet Arşiv Hizmetleri Hakkında Yönetmelik](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md)
  (1988 metnini md. 32 ile kaldırdı). [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)'daki atıf
  tarihsizdir, doğrudan yürürlükteki Yönetmeliğe gider.

### 3.3 Üç tür hüküm: kural, bilgi metni, okul ayarı ya da uygulaması

| Tür | Nerede durur | Örnek | Programda görünüşü |
|---|---|---|---|
| **Kural** (mevzuat hükmü) | Kural paketi, çapalı | Yeter sayı ×4/×2 ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); elden bağış 5 iş günü ([md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)); kantin kirasında KDV yok ([KDVK md. 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17)) | Uyarı + gerekçe ya da sert engel (altın kural 3; programın **hesapladığı** değerde sert, kullanıcının belgeden **girdiği** değerde uyarı — kullanıcı kararı D1); madde bağlantısıyla |
| **Bilgi metni** (özelge, sirküler, yorum) | `docs/mevzuat/bilgi/` (F5'ten önce kurulur) | Bağışçının vergi indirimi olmaması; kantini birlik işletirse kurumlar vergisi; tevkifat ([GVK md. 94](../mevzuat/193-gelir-vergisi-kanunu.md#madde-94)) | Bilgi kutusu; hüküm diye basılmaz, evraka girmez |
| **Okul ayarı ya da okul uygulaması** (mevzuatta yok ya da hükmün uygulama yöntemi okula bırakılmış; okulun kararı) | Okul kartı / dönem ayarları / üyelik kaydı | Küçük alım tutar sınırı ve sürekli ödemeler için genel karar (saha 6); internet bankacılığında üçüncü onay (F0-e (c)); YK, DK ve alım komisyonu üyesinden suç engeli ve tek birlik beyanı alınması (hüküm kuraldadır, beyan okulun yöntemidir; §6 giriş tablosu, §15 KE-22); taramaların saklama süresi | "Okul kararı" ya da "okul uygulaması" etiketiyle; mevzuat gereği diye sunulmaz |

### 3.4 KVKK

**Kapsam ve veri sorumlusu.**

- Birliğin tüzel kişiliği yoktur; veri sorumlusunun birlik mi okul/MEB mi olduğunu belirleyen Kurul kararı
  bulunamadı (ön değerlendirme §2.5). Kılavuz soruyu açıkça okul müdürlüğünün değerlendirmesine bırakır (F0-e b).
- KVKK, otomatik olmayan yollarla işlemeyi de veri kayıt sisteminin parçasıysa kapsar
  ([KVKK md. 2](../mevzuat/6698-kvkk.md#madde-2), [md. 3/1-e](../mevzuat/6698-kvkk.md#madde-3)); birliğin kâğıt
  kayıtları (karar defteri, katılım cetveli, koçan) zaten kapsamdadır. Program, kâğıt kayda dayanan Veri Sorumluları
  Sicili kayıt istisnasının okul için geçerliliğini değiştirebilir ([KVKK md. 16/2](../mevzuat/6698-kvkk.md#madde-16)):
  istisnayı getiren Kurul kararları korpusta yoktur (DOĞRULANMADI; BENIOKU §6'ya "bekliyor" diye girer). VERBİS sorusu
  veri sorumlusu sorusuyla birlikte kılavuzdaki açık sorulardadır.

**İşleme envanteri.** Her veri kategorisinin amacı, hukuki sebebi, saklama kuralı ve aktarımı tek tabloda durur;
aydınlatma metni (E04) bu tablodan dolar. Hukuki sebep sütunu **öneridir**: veri sorumlusunun belirlenmesine bağlıdır
(F0-e b) ve kılavuzda okul müdürlüğüne açık soru olarak durur. "Yön." OAB Yönetmeliğidir.

| Veri kategorisi | İlgili kişi | Amaç | Hukuki sebep (öneri) | Saklama | Aktarım |
|---|---|---|---|---|---|
| Ad-soyad, kişi türü, organ ve görev, seçilme sayıları, okulun beyan uygulamasının tarihi | Organ üyesi ve aday (veli, kursiyer, hayırsever, öğretmen) | Organların oluşturulması; karar, tutanak ve aday listesi taslakları; seçilme sınırı denetimi | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [12](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [14](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | Birlik kaydıyla (§5.4) | Yok; yeni yönetimi TEFBİS'e okul idaresi girer ([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| Ad-soyad, öğrencinin sınıfı, katılım işareti | Veli (e-Okul listesi, T5) | Genel kurul katılım cetveli ve sayımı; aday olan velinin kişi kaydı | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 9/2-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [10/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10). "Zorunlu" unsuru, boş satırlı cetvel seçeneği karşısında açık sorudur | Dönem kapanışında silinir; adlı çıktının dosyası saklanmaz | Yok |
| Ad-soyad, öğretmen/yönetici türü | Okul personeli (e-Okul) | DK öğretmen üyeleri, alım komisyonu, imza blokları | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | Ayrılan ve birlik kaydına bağı olmayan dönem kapanışında silinir | Yok |
| Ad-soyad (isteğe bağlı); K9 açıksa T.C. kimlik no | Bağışçı | Gelir kaydı, makbuz yaprağı, TEFBİS girişi | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 6/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [16](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Ad birlik kaydıyla; kimlik no dönem kapanışında boşaltılır | TEFBİS'e okul idaresi |
| Ad/unvan (gerçek kişide), fatura bilgisi | Tedarikçi | Harcama dosyası ve ödeme | [KVKK md. 5/2-c, ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 18/1-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Birlik kaydıyla | TEFBİS'e okul idaresi (gider kaydı) |
| Ad/unvan, adres, telefon, e-posta, teklif tutarı | Kantin ve servis isteklisi (gerçek kişi) | Kiralama ve taşımacının tespiti; sözleşme | [KVKK md. 5/2-c, ç](../mevzuat/6698-kvkk.md#madde-5); Yön. [md. 20](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [21](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [U-E md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6), [7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) | Ad birlik kaydıyla; iletişim bilgisi §5.4'teki dönem kapanışında boşaltılır | Yok |
| Katılım engeli (var/yok) ve dayanağı | Kantin isteklisi | Hukuken geçersiz katılımı önlemek ([md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) | Dayanak bendi **özel nitelikli** olabilir; [KVKK md. 6/3](../mevzuat/6698-kvkk.md#madde-6) şartı DOĞRULANMADI (§15 B-16) | Dayanak şifreli; arşiv paketine girmez | Yok |
| Ad, belge türü, görüldü ve geçerlilik tarihi (içerik yok) | Kiracı, kantin çalışanı, şoför, rehber personel | Belge takibi (Yön. [md. 20/6-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9)) | Adli sicil ve portör kaydı **özel nitelikli** olabilir; md. 6/3 şartı DOĞRULANMADI — işveren birlik değil kiracı ya da taşımacıdır (§15 B-16) | Birlik kaydıyla; tarama varsayılan alınmaz (§5.4) | Yok |
| Ad/unvan, plaka, güzergâh | Taşımacı | Mevzuatın istediği ilan ([U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10)) | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5) | Birlik kaydıyla | İlan panosu ve okul sitesi (D5) |
| Ad-soyad, rol, hesap olayları, hassas okumalar | Program kullanıcısı | Hesap, denetim izi, erişim günlüğü (§4.6) | [KVKK md. 5/2-ç](../mevzuat/6698-kvkk.md#madde-5) ([KVKK md. 12/1](../mevzuat/6698-kvkk.md#madde-12) güvenlik tedbiri) | §4.6; erişim günlüğü §15 B-9 | Yok |

**Aydınlatma.** Aydınlatma metni ilgili kişiye verinin elde edildiği anda verilir
([KVKK md. 10/1](../mevzuat/6698-kvkk.md#madde-10)). Kılavuz ve ilk kurulum ekranı yalnız program kullanıcısını
bilgilendirir. E04 dört alt metindir (veli ve üye · personel · istekli, kiracı ve çalışan · bağışçı ve tedarikçi) ve
okul kartındaki veri sorumlusu alanından (`data_controller_text`, §5.1) dolar; alan boşken basılmaz. Ulaştırma
noktaları:

- **Veli ve organ üyesi:** genel kurul davetinde (E07) kısa aydınlatma paragrafı ve tam metnin okunacağı yer (pano,
  okul sitesi); aday kaydında ve görev bölümünde veli-üye metni.
- **Personel:** e-Okul personel aktarımından önce personel metni okulda duyurulur.
- **İstekli:** birliğin istekli verisi aldığı yerlerde — servis çalıştırma işinin ilanı (E48), tip şartname teslim
  tutanağı (E50). Kantin ilanı il/ilçe MEM'indir (§7.6); birlik istekli verisini MEM'den gelen evrakla alır.
- **Kiracı, kantin çalışanı, şoför, rehber personel:** belge tesliminde (E46, E58).
- **Bağışçı ve tedarikçi:** ayni bağış teslim tutanağında (E21) kısa paragraf. Banka havalesiyle gelen bağışçıya
  ulaşma kanalı yoktur: okul sitesindeki genel metin (E04'ün web hâli) bu boşluğu kapatmaya aday; yeterliliği
  DOĞRULANMADI, kılavuzdaki açık sorulardadır.
- **Program kullanıcısı:** ilk kurulum ekranı ve hesap teslim pusulası (§9).

**Veri en aza.**

- Veliden yalnız ad-soyad ve öğrencinin sınıfı (T5); liste dönem kapanışında silinir. Veli adını taşıyan iki çıktıyı
  (E07 sınıf teslim çizelgesi, adlı E08 katılım cetveli) yalnız `yonetici` basar; program bu dosyaları saklamaz
  (§5.2.8, §5.4).
- T.C. kimlik numarası varsayılan kapalı (K9); açıksa yalnız bağışçı alanında durur, hiçbir dosyaya girmez (§5.3).
- Telefon tutulmaz: program SMS ya da e-posta göndermez, hiçbir evrakta telefon yoktur (OYS'deki alan çıkar).
- Suç engeli ([md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12),
  [14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14),
  [20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)): program adli sicil içeriği tutmaz. Organ
  üyeliğinde yalnız okulun beyan uygulamasının tarihi tutulur — beyan Yönetmeliğin değil okulun yöntemidir (§3.3,
  §6.4); OYS'deki şifreli not alanı çıkar (envanter S-20). Kantin isteklisinde açık alanda yalnız "katılım engeli
  var/yok" durur; engelin hangi bentten geldiği şifreli ve erişim günlüklüdür (§5.2.9).
- **Özel nitelikli veri** ([KVKK md. 6/1](../mevzuat/6698-kvkk.md#madde-6): ceza mahkûmiyeti, sağlık). Katılım
  engelinin dayanağı ile kiracı ve çalışan belgelerinin (adli sicil, portör) "görüldü" kaydı bu sınıfa girebilir.
  İşlemenin [md. 6/3](../mevzuat/6698-kvkk.md#madde-6)'teki hangi şarta dayandığı DOĞRULANMADI: 6/3-b "kanunlarda
  açıkça öngörülme" ister, dayanak hükümler ise yönetmeliktir; 6/3-f istihdamdaki yükümlülüğü sayar, ama çalışanların
  işvereni birlik değil kiracıdır. Kurulun [md. 6/4](../mevzuat/6698-kvkk.md#madde-6)'teki "yeterli önlemler" kararı
  korpusta yoktur (BENIOKU §6'ya "bekliyor"). Program bu yüzden içeriği hiç tutmaz, yalnız var/yok ve tarih; soru
  kılavuzda okul müdürlüğüne açık soru olarak durur (§15 B-16).

**Saklanması gereken kişisel belge.** Kantin işletmecisinin (kiracının) ve çalışanlarının belgeleri
([md. 20/6-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20),
[23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); kiracı kantini bizzat çalıştırır,
[EK-2 md. 9](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-9);
hijyen belgesi işletene de gerekir, [HEY md. 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5)), servis şoförü
ve rehber personel belgeleri ([U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9)) ve personel
belgeleri (sürüm 2; [5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86)):
asıl kâğıt birlik dosyasındadır. Program varsayılan olarak yalnız belge türünü, görüldü tarihini ve geçerlilik sonunu
tutar. Tarama eklenirse şifreli dosya olur (`OZEL_NITELIKLI`, erişim günlüklü); saklama süresi öneridir
(DOĞRULANMADI), kural paketine değil okul ayarına girer (§5.4, §15 B-5).

**Duyuru ve ilan çıktılarında kişi adı yok** (dönemlik gelir-gider ilanı, bütçe duyurusu, genel kurul ilanı); bağışçı
adı ilanda görünmez. **Tek istisna mevzuattandır:** sözleşme imzalanan taşımacıların ilanı
([U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10)) taşımacının ad/unvanını, plakayı ve
güzergâhı taşır; telefon, adres ve T.C. kimlik no basılmaz; ilan süresi bitince okul sitesindeki kopyanın
kaldırılması hatırlatılır (kullanıcı kararı D5, §15.1b).

**e-Okul kaynaklı veri.** Veli ve personel listesi e-Okul'dan alınır (T5). MEB Bilgi ve Sistem Güvenliği Yönergesi
yetkili kullanıcının öğretmen, öğrenci ve velilere ait kişisel bilgileri "3. şahıslar ile paylaşamaz" der
([BSG Yön. md. 5/8](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-5)); kişisel veriler yetkili
merciler dışında paylaşılmaz ([md. 6/7](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-6)). Birlik
okul bünyesinde kurulur ([Yön. md. 5/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-5)); birliğin bu
hükümler karşısında "3. şahıs" sayılıp sayılmadığı veri sorumlusu sorusuna bağlıdır (F0-e (b), §15 KE-20) ve
kılavuzda okul müdürlüğüne açık soru olarak durur. Program bu yüzden adlı listeyi en dar yolla kullanır: adlı E07
çizelgesini ve E08 cetvelini yalnız `yonetici` basar, dosyası saklanmaz, her basım erişim günlüğüne düşer (§4.4.2
dipnot ¹⁰, §4.6.4); uygulama biçimi §15 M-13'tedir.

**Depoya girmez:** gerçek veri, banka özeti, TEFBİS çıktısı, e-Okul listesi (`.gitignore`; F1'de sızıntı kapısı).

### 3.5 Okul türü kapsamı

Kapsam **resmî örgün okullardır**; eğitim kampüsünde yer alan okul da kapsamdadır
([md. 2/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-2),
[4/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4)). Kural paketi şu farkları okul kartından okur:

| Fark | Dayanak | Programda |
|---|---|---|
| Öğrenci mevcudu 100'ün altında | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | Yeter sayı çarpanı ×2 |
| Büyükşehir statüsünde olmayan il merkezi | [md. 17/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | Kantin payında il %20; okul kartında üç değerli yerleşim türü; kantin sözleşmesinin özel şartına pay notu (§7.6) |
| İlkokul/ortaokul (OÖEİKY) | [OÖEİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57) | Temsilciler çizelgesinde ortaöğretimdeki kurulların karşılıkları |
| Birden çok kademe (ör. ortaokul + lise) | [OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25), [185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185); [OÖEİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57) | Okul kartında çok değerli kademe (`levels`, §5.1); her kademenin kurulu çizelgeye girer |
| Eğitim kampüsünde | [md. 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | Okul kartında kampüs işareti (`in_campus`); temsilciler çizelgesinde kampüs yönetimi satırı |
| Kantin birlikçe işletiliyor | [md. 17/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | Arz %1; iktisadi işletme bilgi metni |

Kapsam dışı (sonra): özel okullar (md. 15 ve 17 "resmî okullarda" der); yaygın eğitim kurumları — üye tanımı farklıdır
([md. 4/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4): usta öğretici, kursiyer, çırak, kalfa, usta,
eğitsel kulüp üyesi ve gönüllü de üyedir), okul kartında yaygın kademe seçeneği yoktur. Pilot okul dışında saha
sınaması yapılmayacağından (F0-d) küçük okul, ilkokul/ortaokul, karma kademe ve kampüs farkları kural testleri ve
uydurma senaryolarla sınanır (§10, §16).

---

## 4. Mimari

### 4.1 Süreç modeli

```
oab-defteri.exe   (tek süreç · tek kopya kilidi · OturumDurumu tek nesne)
├── ana iş parçacığı: pywebview penceresi — çarpı = çık (T6; uzun yazma işi sürerken bekletir, §4.2)
│     Windows: WebView2 · Linux: qt_kurulum.hazirla() → PySide6 QtWebEngine + SIGTERM köprüsü
├── od-wsgi    waitress 127.0.0.1:<rastgele> → Django (API + SPA, whitenoise)
│                OturumBelirteci(403) · RestartRequired(503) · AppLock(423) · RolMiddleware(403 rol_yetkisiz)
├── od-kanal   tek kopya kanalı — Windows: OABDefteri.Goster / .Kapat · Linux: kanal.sock (yalnız sahibi)
├── od-gunluk  gün değişimi kapısı: açılışta + saatte bir; her iş bakım kapısından geçer; DEK isteyen iş kilitliyken ertelenir
└── od-cikis   arayüzdeki Çık: HTTP yanıtı gittikten sonra düzenli kapanışı başlatan zamanlayıcı
```

**Değişmezler** (testle kilitlenir):

- Yönetim sunucusu `127.0.0.1` dışında host kabul etmez; `main.py` host vermez. `0.0.0.0` hiçbir üretim kaynağında
  geçmez (tek muafiyet `window.py`'deki WebView2 sürüm damgası). Bu testler bugün `test_katalog_server.py`'dedir,
  `test_server.py`'ye taşınır (§13 D2).
- Paketli yapıda `ALLOWED_HOSTS` yalnız `127.0.0.1` ve `localhost`; `backend` adı yalnız `OD_SESSION_TOKEN` boşken
  (geliştirme, test) eklenir. **Yapılacak:** iskelette bu koşul yoktur, `backend` her zaman listededir ve kilitleyen
  test yoktur (Kütüphane tasarımında yazılı, kodda uygulanmamış; §13 D46); F1a-2'de yazılır ve testle kilitlenir.
  Oturum belirteci her açılışta rastgele; URL'deki `?t=` → `HttpOnly`, `SameSite=Strict` çerez; belirteçsiz istek 403.
- Dış bağlantı yalnız `apps/okul/services/updates.py`'den çıkar (TK4); `OD_UPDATE_REPOSITORY` paketli yapıda okunmaz.
  Evrak hattı (`shared/pdf.py`, `shared/evrak.py`) WeasyPrint'e yalnız `data:` ve paket içi `file:` kaynağını kabul
  eden bir `url_fetcher` verir, öteki şemalarda istisna yükselir (iskelette `url_fetcher` yok; §13 D47). Kaynak
  taraması (`test_dis_istek_kapilari`) kitaplığın kendi istemcisini görmediği için ayrıca test: `<img
  src="http://…">` içeren belge PDF'e çevrilirken ağ tuzağı tetiklenmez.
- `OturumDurumu` süreç içi tektir: kilit kapısı, `RolMiddleware`, denetim izi yazıcısı ve uzun iş sayacı aynı nesneyi
  okur. Masaüstü ile backend arasında tek kanal `masaustu_kanca`dır (çıkış kancası + gün işleri kaydı); katalog
  denetçisi yoktur.
- Veritabanının tek yazarı vardır: istekler ve `od-gunluk` aynı SQLite dosyasına `IMMEDIATE` işlemle yazar; geri
  yükleme bakım kapısını kapatır, uçuştaki işin bitmesini bekler, sonra dosyayı takas eder (TK19, §13 D3).
- **DEK yokken veritabanına iş verisi yazılmaz.** Kilitliyken yalnız kişisiz sistem olayları (yedek alındı, şema
  göçü uygulandı, gün işi ertelendi) denetim izine kilitli kip anahtarıyla düşer (§4.6.3); şifreli alan zaten yazılamaz
  (`KeyMissingError`). Göçler yalnız şema değiştirir; veri göçü gerekirse ilk kilit açılışında koşar.

**Katmanlar** ([ön değerlendirme §7.2](../kesif/2026-10-31-on-degerlendirme.md)): arayüz (React) → DRF uçları →
servis katmanı (iş akışı, kural motoru, uyarı + gerekçe kaydı, yetki kapısı) → modeller → evrak (§9) ve içe/dışa
aktarım (§8). **Her yazma servis katmanından geçer**; servis, `OturumDurumu`'ndaki hesabı "yazar" olarak veri satırıyla
aynı işlemde denetim izine verir (TK16, model §4.6). Yazar bağlamı olmayan yazma reddedilir; kullanıcı eylemi olmadan
yapılan iş `SISTEM` aktörüyle düşer. Veri değiştiren sistem işi (dönem kilidi denetimi gibi) DEK ister; kilitliyken
ertelenir, ilk kilit açılışında koşar.

### 4.2 Açılış ve kapanış

**Açılış** (Kütüphane `desktop/main.py` sırası; katalog, tepsi, uyku ve güvenlik duvarı adımları düşer):

| # | Adım | Başarısızlıkta | Not |
|---|---|---|---|
| 1 | Veri dizinleri (exe dışında) + günlük yapılandırması; Linux'ta `umask 077` ve dizin kipleri (§4.5) | 1 | |
| 2 | Tek kopya kilidi (iki mutex + `instance.lock`) | normal ikinci açılış: çalışan kopyanın penceresi öne gelir, ikinci süreç **0** · `--geri-yukle`, `--autotest`, `--pdf-duman`, `--evrak-duman` çalışan kopya bulursa **2** | İleti "OAB Defteri açık. Programı kapatıp yeniden deneyin." — tepsi anlatılmaz |
| 3 | Temiz kapanış işareti okunur ve silinir; geri yükleme notu (`geri-yukleme-notu.json`) varsa okunur; tek kopya kanalı kurulur | — | İşaret yoksa panoda "son oturumdaki kayıtları kontrol edin" kartı (T15; okuyucusu §13 D4) |
| 4 | Oturum belirteci (ayarlar okunmadan önce) | — | |
| 5 | Sürüm damgası; damga yoksa göç kaydı denetimi | 4 | Eski program yeni veriyi açmaz |
| 6 | Bütünlük denetimi | 3 | Yedekten **önce**: bozuk veritabanıyla rotasyon sağlam eski yedekleri silmesin |
| 7 | Günlük yedek (veritabanı + dosya manifestosu) + yerel yedeklerin rotasyonu (§4.4.7) | günlüğe | İlk hesap kurulmadan atlanır; olay denetim izine kilitli kip anahtarıyla düşer (§4.6.3) |
| 8 | Göç öncesi yedek (son 5; §4.4.7) + `migrate --no-input` (yalnız şema) | 5 | Veri göçü ilk kilit açılışında; olay denetim izine (§4.6.3) |
| 9 | waitress `127.0.0.1:<boş port>` + sağlık denetimi | 6 | |
| 10 | Çıkış kancası `masaustu_kanca`'ya kaydolur; `od-gunluk` başlar | — | |
| 11 | Linux: `qt_kurulum.hazirla()` (`QT_API=pyside6`, `QtWebEngineWidgets`'ın `QApplication`'dan önce yüklenmesi, pencere simgesi) + SIGTERM köprüsü | 1 | `tray.py`'den ayrılmış hâli (§13 D1) |
| 12 | Windows: WebView2 denetimi → pencere; ilk açılışta kurulum sihirbazı, sonra kilit ekranı | 7 | Kilit açılışındaki denetimler §4.4.3 |

`--autotest`: 1-10 + sağlık denetimi, pencere açılmaz; katalog adımı yoktur (§13 D5). Kurulum sihirbazının ilk adımı
(ilk yönetici hesabı) bitmeden kişi yazan uçlar 409 `parola_gerekli` döner (aile).

**Kapanış — tek yol.** Kaynaklar: çarpı · arayüzdeki **Çık** (`POST app/quit/`, her oturum durumunda parolasız) ·
kurucu ve kaldırıcının `OABDefteri.Kapat` olayı · kanal komutu `kapat` · Linux SIGTERM (oturum kapanışı). Sıra:
pencere kapanır (uzun yazma işi sürüyorsa önce biter, aşağıda), `webview.start` döner → kanal → kancalar bırakılır →
`od-gunluk` durur → oturum açıksa kilitlenir (çapa `iz-durumu.json`'a yazılır, §4.6.3) → yönetim sunucusu → **WAL
checkpoint** (TB14) → temiz kapanış işareti (yalnız uzun iş sayacı sıfırsa) → kilit (mutex'ler süreç bitene dek kalır).

- **Uçuştaki iş** (denetim GA-13). `shared/bakim.py`'deki kapı uzun yazma işlerini sayar: banka özeti uygulama, dönem
  kapanışı ve arşiv paketi, DEK yenileme, canlı geri yükleme, dosya eki yazımı, tam yedek. Çarpıda sayaç sıfır değilse
  pywebview `closing` işleyicisi kapanışı **bir kez** erteler ve "İşlem bitiyor, program kendiliğinden kapanacak"
  iletisini gösterir; iş bitince kapanış sürer, en çok 60 sn beklenir. Bu bekletmedir, onay sorusu değildir; T6
  korunur. Süreç yine de ölürse (zorla kapatma, elektrik) çok adımlı işler kendi `gecis` günlüğünden sürdürülür ya da
  geri alınır (DEK yenileme §4.4.4); temiz kapanış işareti yazılmaz, sonraki açılışta T15 kartı çıkar. Aynı sayaç
  boşta kilidi de erteler (§4.4.3). Testler: iş sürerken çarpı → iş tamamlanır, sonra çıkılır · iş öldürüldü →
  işaret yok.
- Çarpıda onay sorulmaz (T6, Kelebek davranışı). Kaydedilmemiş form kaybı kabul edilen risktir; azaltma: uzun
  akışlar (genel kurul sihirbazı, harcama zinciri) adım adım sunucuya kaydedilir; serbest metinli uzun alanlar (karar
  metni, DK bulgusu, gerekçe) açıkken kısa aralıklarla sunucuya **taslak** kaydedilir ve yeniden açılışta "yarım kalan
  taslak" panoda görünür (ayrıntı §7 girişi ve §7.10; denetim SU-16). Taslak tarayıcı deposuna yazılmaz: kişisel veri orada şifresiz
  kalırdı (TK8).
- **Kurucu ve kaldırıcı:** Inno `AppMutex` kullanılmaz (kaldırıcı olayı göndermeden "programı kapatın" iletisinde
  beklerdi). `[Code]` `InitializeSetup`/`InitializeUninstall` `.Kapat`'ı işaretler, iki mutex için en çok 30 sn
  bekler; program o sürede düzenli kapanır. Kapanmazsa ileti "OAB Defteri açık. Programı kapatıp Yeniden Dene'ye
  basın."; süreç zorla sonlandırılmaz.
- **Geri yükleme sonrası** tüm API 503 `restart_required` ile kesilir; ileti "Programı kapatıp yeniden açın"
  (Kütüphane'deki "tepsiden Çık" metni gider).

**Çıkış kodları** (`desktop/errors.py`):

| Kod | Anlam | Kod | Anlam |
|---|---|---|---|
| 0 | başarılı | 7 | WebView2 yok |
| 1 | beklenmedik | 8 | `--pdf-duman` başarısız |
| 2 | zaten çalışıyor | 9 | geri yükleme başarısız ya da yetkisiz (§4.4.4) |
| 3 | veritabanı bozuk | 10 | `--bagimlilik-duman` başarısız |
| 4 | şema bu sürümden yeni | 11 | **ayrılmış** (ailede `--dagitim-duman`; aile hizası için yeniden kullanılmaz) |
| 5 | göç başarısız | 12 | **`--evrak-duman` başarısız** (yeni; docx üret → python-docx ile geri oku → Türkçe örnek ve "İ"; paketli ikilide `Document()` ile boş belge de açılır) |
| 6 | sunucu kalkmadı | | |

### 4.3 Tehdit modeli

**Korunan varlıklar:** birliğin mali kayıtlarının bütünlüğü · kişisel veri (veli adı ve sınıfı, iletişim, K9 açıksa
bağışçı T.C. kimlik no) · evrakın doğruluğu. Birliğin kurumsal IBAN'ı kişisel veri değildir: açık alandır, maskesiz
gösterilir ve basılır, erişim günlüğüne düşmez (denetim EK-13). Ödeme alıcısının IBAN'ı modelde yoktur; eklenirse
şifreli, maskeli ve erişim günlüklü bir kişisel veri alanı olur (§5). **Saldırgan profili:** aynı odadaki kişi, ortak
Windows hesabını kullanan kurul üyesi, dönemi biten kurul üyesi, bilgisayara erişimi olan personel, yedeği bulan kişi;
uzak saldırganın tek yüzeyi güncelleme kanalıdır. **Sınır:** program bir izlenebilirlik ve kaza önleme aracıdır; **asıl
güvenlik sınırı Windows hesabı ve disk şifrelemesidir** (BitLocker; Pardus'ta LUKS). Bu cümle kılavuza ve Hakkında'ya
girer ([KVKK md. 12/1](../mevzuat/6698-kvkk.md#madde-12) idari tedbirler okulundur).

| # | Tehdit | Katman | Kalan risk |
|---|---|---|---|
| 1 | Aynı makinedeki başka süreç yönetim API'sine istek atar | Oturum belirteci (fail-closed 403), yalnız loopback, rastgele port | — |
| 2 | Kötü niyetli web sayfası DNS rebinding yapar | Belirteç çerezi `SameSite=Strict`, yalnız WebView2 profilinde; `ALLOWED_HOSTS` paketli yapıda yalnız loopback adları (§4.1, §13 D46) | — |
| 3 | Açık bırakılan oturumda başkası işlem yapar (MY masadan kalkar) | Boşta kilit (TK14), Kilitle düğmesi ve kısayolu, her yazma hesapla denetim izinde; kilitlenmede ön yüz belleği sıfırlanır (§4.4.3) | Boşta süre içindeki işlem oturum sahibinin adına düşer; [BSG Yön. md. 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) kilitleme yükümlülüğü kullanıcınındır |
| 4 | Kısıtlı rol (DK, müdür) yetki alanı dışına ya da yetkisiz rol yazmaya çalışır | Uç katmanı: rol matrisi, yeni uç kapalı, koruma testi; servis katmanı: tek yetki kapısı (TK13, §4.4.2) | Hatalı matris: URL desenlerini dolaşan test ve hücre başına anlık görüntü testi yakalar |
| 5 | Dönemi biten ya da görevden düşen üye eski parolasıyla girer ya da eski yedeği açar | Üyelik düşünce ve görev bölümünde hesap askıya alınır, hesap geçişinde kapanır; sarmal `guvenlik.json`'dan ve arşivden silinir (TK11); yedek başlığında hesap sarmalı yok (TK10); hesap geçişinde DEK yenilenir (TK12) | Görevdeyken kopyaladığı veri; genel kurul ile hesap geçişi arasında (en çok bir hafta) alınan yedekler eski DEK'le açılır. TK12 kapalı kalırsa: görevdeyken kopyaladığı `guvenlik.json`'la sonraki yedekler de açılır |
| 6 | Hesap parolasını bilen biri veri dizinini kopyalayıp DEK'i program dışında türetir | Rol kriptografik değildir; dönemlik hesap + izlenebilirlik | Tam okuma mümkündür; kılavuz açıkça yazar ([iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md) risk 1); BitLocker ve ayrı Windows hesabı önerisi (§4.5) |
| 7 | Program dışından SQLite dosyasında veri değiştirilir, son kayıtlar ve iz satırları birlikte silinir ya da dosya dünkü kopyayla değiştirilir — parola gerekmez | İçerik MAC'i + HMAC zinciri (İA; §4.6); kilit açılışında çapa, kilitli satırlar ve son 200 satır kendiliğinden doğrulanır; zincir başı her ay kâğıda iner (aylık bildirim, deftere geçirilecek baskı, devir tutanağı; §9); `from_db_value` katı kip (TK8); DK'nin "kayıt bütünlüğü denetimi" | Veritabanı ile `iz-durumu.json` birlikte eski kopyayla değiştirilirse program fark etmez, kâğıt çapası yakalar; parolayı bilen biri zinciri yeniden hesaplayabilir (tehdit 6) |
| 8 | Kilitliyken `guvenlik.json` silinir ya da bozulur | Kayıp kilidi (fail-closed): yalnız durum ve geri yükleme açık; "sıfırla ve kuruluma dön" yalnız korunacak veri yokken | Geri yükleme `guvenlik.json`'u yedek başlığından (yalnız kurtarma bölümü) yazar → kurtarma anahtarı gerekir |
| 9 | Disk, bilgisayar ya da USB yedeği çalınır | Fernet alan şifrelemesi (kapsam §5), dosya deposu şifreli (§4.4.4), X25519/AES-GCM yedek; yedek başlığında yalnız kurtarma sarmalı (TK10); şifreli alandan türeyen her özet anahtarlı (kör indeks, hareket parmak izi) | `guvenlik.json` aynı diskte durur: şifreli alanlar **en zayıf hesap parolası** kadar korunur (TK15). Düz alanlar (tutar, tarih, karar no, kategori, kurumsal IBAN) okunur; veli listesinin sınıf alanı dönem kapanışına dek açıktır, satır sırası tutulmaz (§5). Tam koruma BitLocker |
| 10 | Kurtarma anahtarı kâğıdı ele geçer | Anahtar okul müdürlüğünde, mühürlü zarfta durur; veliye geçmez; devir tutanağına yalnız zarfın durumu girer (D3). Yalnız `yonetici` yeniler; hesap geçişinde yeni anahtar, eski zarf imha tutanağıyla yok edilir (TK12). Anahtarla açılış ayrı türle denetim izine düşer, parolası yenilenen hesabın sahibine ilk girişinde bildirilir (§4.4.3) | Zarfı açan kişi (müdür dâhil) bir `yonetici` hesabını devralabilir; iz ve bildirim görünür kılar. Yenilemeden önceki yedekler eski zarf imha edilene dek eski anahtarla açılır (TB17) |
| 11 | Kilit ekranında parola denenir | Argon2id (~0,2 sn), kademeli gecikme 0/0/1/2/4 sn **hesap başına**; yalnız seçilen hesabın sarmalı denenir; organ ve müdür hesabı ardışık 10 hatalı denemede askıya alınır, `yonetici` açar ([BSG Yön. md. 7/3](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [md. 9/2-c](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9); §15 M-12) | `yonetici` hesabında askı yoktur (kendi kendine hizmet reddi olurdu; kurtarma anahtarı yolu kalır). Sayaç `guvenlik.json`'dadır, dosyaya erişen sıfırlayabilir; çevrimdışı denemeye karşı koruma parolanın gücüdür (tehdit 9) |
| 12 | `yonetici` başka bir hesabın parolasını sıfırlayıp o hesapla işlem yapar | Sıfırlama denetim izine düşer; geçici parola yalnız ilk girişte geçer ve hemen değiştirilir; hesap sahibine ilk girişte "parolanız … tarihinde sıfırlandı" bildirimi ve son girişleri gösterilir; kurtarma anahtarıyla yenilemede de aynı | Sıfırlama ile sahibinin ilk girişi arasındaki işlemler; bildirim ve denetim izi görünür kılar |
| 13 | İçe aktarılan dosya (banka özeti, e-Okul listesi, TEFBİS Excel) zararlı ya da bozuk | TK18: tür ve boyut denetimi, makrolu biçim reddi, `read_only`/`data_only`, önizleme + onay | openpyxl XML saldırılarına karşı `defusedxml` önerir (doğrulanmadı; §11 B15) |
| 14 | Dış kaynaklı metin Excel çıktısında formül olarak çalışır (banka açıklamasında `=HYPERLINK(…)`) | Tek xlsx yazım yardımcısı metin tipini zorlar (TK18); test | — |
| 15 | Programın ürettiği dosyalar (Word, PDF, Excel) ve içe aktarılan e-Okul listesi diskte kalır | Program kendi geçici dizinine açık kopya bırakmaz (§4.4.7); kalanını koruyamaz: içe aktarma ekranında "kaynak dosyayı silin" hatırlatması, kılavuz, ayrı Windows hesabı; evrak izi (sha256) neyin üretildiğini gösterir | Kullanıcının kaydettiği kopya kullanıcının idari tedbiridir |
| 16 | Sahte güncelleme | İlk istek yalnız `api.github.com`'a, kurulum dosyası `github.com`'dan; indirme yönlendirmesi izlenir; **güven çapası SHA-256** (kurucu çalıştırılmadan hemen önce yeniden doğrulanır); HTTPS; kurulumu kullanıcı başlatır; `OD_UPDATE_REPOSITORY` paketli yapıda okunmaz | İmzasız exe (TB6, SmartScreen); GitHub hesabı ele geçerse sahte sürüm |
| 17 | Kişisel veri depoya ya da pakete sızar | `.gitignore`; `depo_sizintisi` (TCKN sağlaması + **IBAN mod-97**), `veri_sizintisi` (paket ve arşiv üyeleri) | Sentetik örnekler adıyla muaf |
| 18 | Elektrik kesintisi, disk arızası (tek bilgisayar) | `synchronous=FULL`, temiz kapanış işareti, uzun işlerin `gecis` günlüğü (§4.2), günlük yedek, dış (USB) **tam** yedek hatırlatması — dışarı çıkan yedek ekleri ve üretilmiş evrakı da taşır (§4.4.7) | Bilgisayar ve USB birlikte kaybolursa son dış yedekten sonrası |
| 19 | Program dışından `Account` satırında rol ya da durum değiştirilir (parola gerekmez) | Her `Account` satırı DEK'ten türeyen anahtarla mühürlüdür; kilit açılışında seçilen hesabın mührü doğrulanır, tutmazsa oturum açılmaz ve olay denetim izine düşer (§4.6.1) | Parolasını bilen biri DEK'i dışarıda türetip mührü yeniden hesaplayabilir (tehdit 6); mühür bu yolu kod yazmayı gerektiren bir işe çevirir |
| 20 | Ortak Windows hesabını kullanan kişi program dosyalarını değiştirip başkalarının parolasını toplar | Ortak "OAB" Windows hesabında yönetici kurulumu: Program Files standart kullanıcıya salt okunur (TK7) | Kullanıcı başına kurulumla ortak hesap birlikte kullanılırsa program dosyalarının bütünlüğü korunmaz; kılavuz bu birleşimi önermez |
| 21 | Yönetici olmayan hesap sahibi konsoldan ("Yedekten Geri Yükle" kısayolu) veritabanını ve denetim izini geri sarar | Konsol geri yüklemesi yalnız kurtarma anahtarıyla ya da rolü `yonetici` olan hesabın parolasıyla; geri yükleme ilk kilit açılışında denetim izine ve DK panosuna düşer (§4.4.4) | Kurtarma anahtarını ele geçiren (tehdit 10) |
| 22 | Aynı bilgisayardaki başka yerel hesap veri dizinini okur (Linux) | Açılışta `umask 077`; veri, günlük, önbellek ve yedek dizinleri 0700, gizli dosyalar 0600 (§4.5). Windows'ta `%LOCALAPPDATA%` hesaba özeldir | Pardus'ta yeni kullanıcı ev dizininin varsayılan izni doğrulanmadı (F1a'da elle) |

### 4.4 Kullanıcılar, roller ve oturum (T1)

**Terim.** `yonetici` rolünün arayüz etiketi "Program yöneticisi (OAB'den sorumlu müdür yardımcısı)"dır;
[BSG Yön. md. 4/1-s](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)'deki "sistem yöneticisi"
(Başkanlık ve MEM bilişim personeli) ile karıştırılmaz.

#### 4.4.1 Roller

| Rol | Kim | Bağ | Yazma | Dayanak |
|---|---|---|---|---|
| `yonetici` | OAB işlerinden sorumlu müdür yardımcısı | Organ dışı; okul idaresince belirlenir; dönemler arası sürer | Birlik modülleri (mali kayıtlar hariç) + sistem işleri (hesaplar, güvenlik, ayarlar, yedek) | K2; saha 10 (programı çoğunlukla MY kullanır); TEFBİS'e okul idaresi girer ([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| `baskan` | YK başkanı (veli) | YK üyeliği, görev "başkan" ([md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) | Birlik modülleri (mali kayıtlar hariç) | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/2, 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) |
| `baskan_yardimcisi` | YK başkan yardımcısı | YK üyeliği, görev | Birlik modülleri (mali kayıtlar hariç) | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (başkana vekâlet) |
| `muhasip` | Muhasip üye | YK üyeliği, görev | Birlik modülleri; **mali kayıtları yalnız muhasip girer** (K2, D2) | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (gelir-gider işlemleri) |
| `sekreter` | Sekreter üye | YK üyeliği, görev | Birlik modülleri (mali kayıtlar hariç) | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (yazışmalar); saha 5 (kararları sekreter yazar) |
| `denetleme_kurulu` | DK asıl üyeleri (1 veli + 2 öğretmen) | DK asıl üyeliği ([md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) | **Yalnız denetim modülü** (DK görev bölümü, denetim planı, md. 14/5 çağrısı dâhil) | K2; [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) ara ve nihai rapor, [14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| `mudur` | Okul müdürü | Organ dışı; YK üyesi değildir, kurula başkanlık etmez (altın kural 6) | **Yalnız kendi yazıları** (harcama talebi, md. 27/3 uyarısı, yeni okulda genel kurul daveti, olağanüstü genel kurul çağrısı) | K2; [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25), [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) |

**Kurallar.**

- **Bir hesap = bir kişi + bir rol.** İzin hesabı basit kalır, denetim izinde rol açıktır. Aynı kişinin ikinci rolü
  gerekirse ikinci hesap açılır. Aynı kişi aynı dönemde YK'de ve DK'de olamaz (§15 A-2).
- **Organ rolleri organ üyeliğine bağlanır** (F1c): YK rollerinde üyelik `SECILDI` ve görev bölümü yapılmışsa hesap
  açılabilir. DK hesapları DK üyeliği `SECILDI` olunca açılır: DK kendi görev bölümünü (başkan seçimi,
  [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) ve E02'yi bu hesapla denetim modülünde yazar
  (M8; K2). Geçiş kurulumunda devralınan üyelik (`source = DEVRALINAN`, §7.9) de hesap açmaya yeter.
  Üyelik düştüğünde ([md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) ya da görev değiştiğinde
  hesap kayıtla **aynı işlemde askıya alınır** (giriş kapanır); kapanışı ve sarmalın silinmesini `yonetici` yapar
  (§4.4.5). F1b'de organ yoktur: hesap rolle açılır, bağ F1c'de zorunlu olur.
- **Hesaplar dönemliktir.** Eski dönemin organ hesapları yeni görev bölümünden sonraki **hesap geçişinde** kapanır;
  yeniden seçilen üyeye yeni dönemde yeni hesap açılır. Denetim izi dönemle hizalı kalır, TK12 ile uyumludur.
  `yonetici` ve `mudur` dönemler arası sürer. Hesap olaylarının tek kaynağı §4.4.5'tir.
- YK'nin görevsiz asıl üyeleri ve yedekler v1'de hesap almaz (§15 M-7).

#### 4.4.2 Rol-izin matrisi

**Y** yazar · **O** okur · **—** erişemez · üst simge dipnottur.

**Bağlayıcılık** (R2; denetim EK-4). Bu matris rol yetkisinin **tek bağlayıcı kaynağıdır**. §7'deki "Kim" ve §9.6'daki
"Üreten" sütunları matrisi **daraltır, genişletemez**: matriste Y olmayan rol akışta ya da katalogda yazar olamaz;
matriste Y olan bir rolün belli bir geçişi ya da belgeyi yapmaması §7/§9'daki satırla yazılır. `yonetici` başka rolün
işini "adına" ya da operatör olarak giremez: her yazma girenin hesabına ve rolüne düşer, `yonetici` yalnız Y olduğu
satırda yazar.

**Okuma** okunan verinin evrak çıktısını (PDF, Word) almayı da kapsar; çıktının evrak izi kaydı (sha256) okuma rolünde
de yazılır. Okur rolün bundan başka yazması yalnız dipnotla verilen rol-özel işarettir (² "TEFBİS'e girildi").
**İstisna:** kişisel veri içeren çıktı ve dışa aktarım
(matrisin ilgili satırı) okumanın kapsamında değildir. **Kapanmış dönem her rolde salt okurdur** (altın kural 4);
yalnız işaret alanları (deftere işlendi, TEFBİS'e girildi, deftere geçirildi) ve yeniden basım kaydı yazılır, ikisi de
denetim izindedir (R12); düzeltme yeni dönemde ters kayıtla (§5, §7). Hassas okumalar (K9 açıksa maskesiz bağışçı T.C.
kimlik no, kişi dökümü, kişisel veri içeren çıktı) erişim günlüğüne düşer (§4.6.4); OYS'nin "okuma ≠ yönetme ≠ hassas
detay" ayrımı korunur.

| Alan | `yonetici` | `baskan` | `baskan_yardimcisi` | `muhasip` | `sekreter` | `denetleme_kurulu` | `mudur` |
|---|---|---|---|---|---|---|---|
| Okul kartı, ders yılı, kapalı günler, birlik dönemi açma ve kapama (M1) | Y | O | O | O | O | O | O |
| Kişiler, organlar, temsilciler, YK görev bölümü, yedek üye çağrısı (YK ve DK; md. 13/6, 14/6) (M2) | Y | Y | Y | Y | Y | O | O |
| Genel kurul (M3) | Y | Y | Y | Y | Y | O | Y¹ |
| YK toplantı, katılım, karar taslağı (M4) | Y | Y | Y | Y | Y | O | O |
| Gelir-gider kaydı, banka eşleme, makbuz koçanı ve yaprağı, kasa (M5) | O² | O | O | Y | O | O | O |
| Harcama zinciri (M6) | Y³ | Y³ | Y³ | Y | Y³ | O | Y⁴ |
| Bütçe, ilan, aylık bildirim, faaliyet raporu (M7) | Y | Y | Y | Y | Y | O | O |
| Denetim: DK görev bölümü, denetim planı, kontrol listesi, bulgu, ara ve nihai rapor, md. 14/5 çağrısı, kayıt bütünlüğü denetimi (M8) | O | O | O | O | O | Y⁵ | O |
| Müdür yazısı: birlik başkanına yazılı uyarı ([md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27); E35) | O | O | O | O | O | O | Y⁶ |
| Takvim, pano ve uyum kaydı (M9; §7.10 — pano her role kendi kalemlerini gösterir) | Y | Y | Y | Y | Y | O | O |
| Gelen-giden evrak, belge dosyası (M10) | Y | Y | Y | Y | Y | O | O⁷ |
| Devir-teslim ve dönem kapanışı (M11) | Y⁸ | Y | Y | Y | Y | O | O |
| Kantin (M13), servis (M14) | Y | Y | Y | Y | Y | O | O⁹ |
| Personel (M15, sürüm 2) | Y | Y | Y | Y | Y | O | O |
| Denetim izi | O | O | O | O | O | O | O |
| Erişim günlüğü (§4.6.4) | O | — | — | — | — | O | — |
| Kullanıcılar: hesap açma (hesap teslim pusulası E63), kapama, askıdan çıkarma, parola sıfırlama, hesap geçişi | Y | — | — | — | — | — | — |
| Güvenlik: kurtarma anahtarı, geri yükleme (uygulama içi ve konsol), yedek indirme, DEK yenileme | Y | — | — | — | — | — | — |
| Ayarlar (K9, boşta süre, küçük alım sınırı, kural sürümü seçimi) | Y | O | O | O | O | O | O |
| Kişisel veri içeren çıktı ve dışa aktarım: veli listesi, adlı davet teslim çizelgesi (E07) ve katılım cetveli (E08), kişi dökümü, ihlal dökümü, maskesiz T.C. kimlik no | Y¹⁰ | — | — | — | — | — | — |
| Güncelleme denetimi (tek dış istek) | Y | — | — | — | — | — | — |
| Kendi parolasını değiştirme, Kilitle, Çık | Y | Y | Y | Y | Y | Y | Y |

¹ Yeni açılan okulda genel kurul daveti ([md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) ve
olağanüstü genel kurul çağrısı ([md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9),
[13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); §15 M-5). Genel kurulun öteki işlerinde müdür okurdur.
² Mali kayıtlar (gelir-gider kaydı, banka içe aktarımı ve geri alma, eşleme, makbuz koçanı ve yaprağı, kasa, emanet)
yalnız `muhasip`tir (K2, D2). **Rol-özel işaretlerin tek kaynağı bu dipnottur:** "deftere geçirildi"
(`MarkBatch(DEFTERE_GECIRME)`) `muhasip`; "TEFBİS'e girildi" (`MarkBatch(TEFBIS_GIRISI)`) `yonetici`, muhasibin
girişinden sonra; kararın "deftere işlendi" geçişi ve `DEFTERDE_SAKAT` kaydı `sekreter` (M4); harcama halkaları ³'tedir.
³ Mali halkalar (harcama belgesinin kaydı, ödeme talimatı, banka eşleme) yalnız `muhasip` (D2); talep halkası yalnız
`mudur` (⁴). YK rolleri ve `yonetici` karar, komisyon ve belge dosyası halkalarını yazar.
⁴ Okul yönetiminin yazılı harcama talebi ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) K2'deki
müdür yazısıdır; `yonetici` taslağını hazırlamaz (§15 M-11). Müdür hesabını kullanmıyorsa kâğıt talep gelen evrak
olarak kaydedilir (`DocumentRecord`, M10) ve harcama dosyasına bağlanır (§7.4).
⁵ DK kendi görev bölümünü (başkan seçimi, [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)),
denetim planını ve [md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) olağanüstü genel kurul çağrısını
bu modülde yazar (§15 M-6). DK üyeliğinin kendisi (genel kurul ve öğretmenler kurulu seçimi) M2'dedir. YK rolleri DK
modülüne yazamaz: DK, YK'nin faaliyetlerini inceler (md. 14/4).
⁶ Yalnız `mudur`; `yonetici` taslak hazırlamaz (K2 lafzı; §15 M-11). Uyarıya rağmen durum sürerse il/ilçe MEM'e
bildirim (md. 27/3 ikinci cümle) K2'deki dört müdür yazısından değildir: okul idaresinin öteki resmî yazıları gibi
taslağını `yonetici` hazırlar (M10), Okul Müdürü kâğıtta imzalar (E70; §15 KE-19; §7.12).
⁷ Müdürün kendi yazıları evrak defterine program tarafından işlenir.
⁸ Dönem kilidi (kapanış; başkan onayı aranmaz, R12), hesap geçişi ve DEK yenilemesi yalnız `yonetici`.
⁹ Müdür kantin ve servis akışlarında iş yapan rol değildir: okul idaresinin yazılarının taslağını `yonetici` hazırlar,
müdür kâğıtta imzalar (§15 KE-19). Kira, arz ve pay tahsilatının kaydı mali kayıttır (M5, `muhasip`).
¹⁰ Yalnız `yonetici` basar ve dışa aktarır (R9; [BSG Yön. md. 5/8](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-5)
veliye ait kişisel bilginin paylaşımını sınırlar, §15 M-13). Adlı E07 ve E08'in dosyası saklanmaz: yalnız tür, tarih,
satır sayısı ve sha256 kalır, arşiv paketine girmez. Her biri erişim günlüğüne düşer. Davetin kişisiz mektubu, boş
satırlı katılım cetveli ve sayılar M3'tedir.

**Uygulama — iki katman** (TK13; denetim GA-18).

1. **Uç katmanı** (`rol_izinleri.py`): her hücre uç + yöntem (+ parametre) kuralıdır; kısmi yetki ayrı uçla verilir
   (ör. harcama dosyasının talep ucu yalnız `mudur`; dönemi kapatma ucu yalnız `yonetici`; olağanüstü çağrı ucu
   `mudur` ve yetkili YK rolleri). Parametre denetçileri (`govdede_yok`, `yalniz_sorgu`) aileden alınır.
2. **Servis katmanı**: kapanmış dönem, maskesiz okuma, kişisel veri içeren çıktı, rol-özel işaretler ve kayıt
   sahipliği (müdür yalnız kendi yazısını düzenler, DK yalnız kendi raporunu) tek kapıdan geçer:
   `yetki(rol, eylem, kayıt)`; ret 403 `rol_yetkisiz`.

**Testler (F1b):** URL desenlerini dolaşan koruma testi · matristeki her (rol, satır, Y) hücresi için en az bir uç
bulunduğunu gösteren anlık görüntü testi · her dipnot için en az bir servis testi (F1b kapısındaki "müdür yalnız kendi
yazılarına yazar" maddesi bu testlerle sınanır).

#### 4.4.3 Oturum durumları

```
KURULUM ──(ilk yönetici hesabı + kurtarma anahtarı saklandı)──▶ KİLİTLİ
KİLİTLİ ──(hesap + parola, hesap mührü ve iki depo tutarlı  |  kurtarma anahtarı + yeni parola)──▶ AÇIK(hesap, rol)
AÇIK    ──(Kilitle  |  boşta süre doldu ve uzun iş yok  |  kullanıcı değiştir)──▶ KİLİTLİ
her durum ──(parmak izi dolu, guvenlik.json yok ya da kullanılamaz)──▶ GÜVENLİK_DOSYASI_KAYIP
her durum ──(geri yükleme uygulandı)──▶ YENİDEN_BAŞLAT_GEREK
```

- **Kilit ekranı** açık hesapların tanıtıcılarını rol etiketiyle listeler ("Muhasip", "Denetleme Kurulu 2"); kişi adı
  gösterilmez — `guvenlik.json` düz metindir ve kilitliyken şifreli adlar okunamaz. Askıdaki hesap "askıda — program
  yöneticisine başvurun" etiketiyle görünür, seçilemez. Kullanıcı hesabını seçer, parolasını yazar; yalnız o hesabın
  sarmalı denenir (Argon2id süresi hesap sayısıyla büyümez).
- **Kilit açılışında sıra:** sarmal açılır → `Account` satırı var, durumu uygun, mührü tutuyor mu (iki depo kuralı,
  §4.6.1) → çapa ve kilitli satırlar doğrulanır (§4.6.3) → geri yükleme notu varsa denetim izine yazılır → ertelenen gün
  işleri ve veri göçleri koşar. Mühür ya da iki depo tutmazsa oturum açılmaz.
- **Kurtarma anahtarıyla açılış** (denetim GA-17). Kullanıcı ya **var olan bir `yonetici` hesabının** parolasını
  yeniler ya da (MY değişimi) **yeni bir `yonetici` hesabı** açar; başka rolün hesabı bu yolla açılmaz. Olay denetim
  izine ayrı türle (`KURTARMA`: hangi hesap, yeni mi) düşer; parolası yenilenen hesabın sahibine ilk girişinde
  "parolanız … tarihinde kurtarma anahtarıyla yenilendi" bildirimi ve o tarihten sonraki girişler gösterilir (tehdit 12
  deseni). Anahtar müdürlükte durduğu için (D3) bu iz zarfın açıldığını görünür kılan kayıttır.
- **Ara katman sırası:** belirteç → güvenlik → whitenoise → common → `RestartRequired` (503) → `AppLock` (423) →
  `RolMiddleware` (403 `rol_yetkisiz`). `RolMiddleware` yalnız AÇIK durumda devreye girer; `HEALTH_PATH`,
  `setup/status/`, `security/status/` hiçbir durumda kesilmez (aile).
- **Boşta kilit** sunucuda tembel dolar: her istekte `son_etkinlik + N < şimdi` ise oturum kilitlenir, DEK bellekten
  silinir. `son_etkinlik` yalnız `X-OD-Etkinlik` başlıklı (kullanıcı eylemli) istekle tazelenir; durum ve pano
  sorguları tazelemez. Saat uykuyu sayar (`UykuyuSayanSaat`). Ön yüzdeki geri sayım yalnız görseldir. Kurulum
  sihirbazı bitene dek süre kilitlemez (kurtarma anahtarı ekrandayken; TB19 dersi); elle Kilitle çalışır. **Uzun
  yazma işi sürerken** (bakım kapısı sayacı sıfır değilken) kilit ertelenir, iş bitince ilk istekte uygulanır: DEK
  işin ortasında silinmez (denetim UY-1).
- **Ön yüz belleği** (denetim GA-23). Kilitlenme (elle, boşta ya da 423) ve her kilit açılışı ön yüzde sorgu
  önbelleğini ve modül belleğini sıfırlar; yol, pencere içeriğinin yeniden yüklenmesidir (oturum çerezi kalır). Önceki
  hesabın yüklediği maskesiz veri sonraki hesabın oturumunda kalmaz. Vitest testiyle sabitlenir.

#### 4.4.4 Anahtarlar ve `guvenlik.json` (şema 2)

- **DEK:** 32 bayt, kurulumda üretilir; hesap geçişinde ve MY değişiminde yenilenir (TK12). Kör indeks, hareket parmak
  izi, hesap mührü, dosya sarmal anahtarı ve yedek anahtar çifti DEK'ten HKDF ile türer (dizgeler §2.3.1). Denetim izinin
  **iz anahtarı (İA) DEK'ten türemez**; DEK'le şifreli olarak veritabanında durur (§4.6.3).
- **`guvenlik.json`:** `surum: 2`, `kdf` parametreleri, `hesaplar: [{id, tanitici, salt, sarmal, hatali, askida}]`,
  `kurtarma: {no, tarih, salt, sarmal, dogrulandi}`, `gecis`. **Rol, ad-soyad, organ bağı, durum ve tarihler
  veritabanındadır** (`Account`, §4.6.1). `tanitici` gerçek ad olmaz; varsayılan rolden türer (`muhasip`, `dk-1`,
  `yonetici-2`), yönetici değiştirebilir — kişinin adını içeriyorsa program uyarır (açılışta DEK eldedir). `hatali`
  ardışık hatalı deneme sayacı, `askida` hatalı deneme askısıdır (§15 M-12); ikisi DEK istemez, kilitliyken yazılır.
- **Parmak izi:** `HMAC(DEK, "od-anahtar-parmak-izi")` okul kartında; dosyanın ve veritabanının aynı DEK'i
  anlattığını gösterir. `enable()` → ilk yönetici hesabı; ön koşulları aile ile aynı (dosya yok, parmak izi boş,
  kişi tabloları boş).
- **Dosya anahtarı** (yeni; TK22; denetim GA-2, UY-3). Her dosya kendi rastgele 32 baytlık anahtarıyla AES-256-GCM
  şifrelenir (`ODDOSYA\x01` + nonce + şifreli metin; AAD = `stored_name`). Dosya anahtarı
  `HKDF(DEK, "od-dosya-sarmal/v1")` ile AES-GCM sarılır (AAD = `stored_name`) ve `Attachment.key_wrap`'te durur. DEK
  yenilemesi dosyaları yeniden yazmaz, yalnız sarmalları tek SQLite işleminde yeniler. Aile `shared/crypto.py`'si
  dosya şifrelemez; yeni modül `shared/dosya_sifreleme.py` (§12.B YENİ). Açık kopya kuralı §4.4.7.
- **Yedek başlığı (TK10):** `{surum, kdf, kurtarma: {no, tarih, salt, sarmal}}` — hesap yok. Geri yüklemede aday
  sırası: (1) güncel `guvenlik.json` + bir `yonetici` hesabının parolası; (2) yedek başlığı + kurtarma anahtarı. Program
  yedeğin hangi anahtarla açılacağını (no, tarih) gösterir. (2) ile açılırsa `guvenlik.json` yalnız kurtarma bölümüyle
  yazılır; program "kurtarma anahtarıyla aç + yönetici parolası" ekranına gelir, öteki hesaplar "parola yenilenmeli"
  durumuna düşer (geçici parolayı yönetici verir).
- **Geri yükleme yetkisi** (denetim GA-3). Uygulama içi geri yükleme `RolMiddleware`'den geçer (yalnız `yonetici`).
  Konsol yolu (`--geri-yukle`, Başlat menüsündeki "Yedekten Geri Yükle" kısayolu) Django ara katmanından geçmez; rol
  orada denetlenir: geri yükleme yalnız **kurtarma anahtarıyla** ya da rolü `yonetici` olan hesabın parolasıyla
  yapılır. Parola yolunda DEK açıldıktan sonra güncel `db.sqlite3` salt okunur bir `sqlite3` bağlantısıyla okunur (ORM
  yok; ailenin "geri yükleme veritabanına yazmaz" kuralı korunur) ve hesabın satırı, durumu ve mührü denetlenir;
  güncel veritabanı okunamıyorsa aynı denetim yedeğin içindeki görüntüde bellekte yapılır. `yonetici` doğrulanmazsa
  kenara alma yapılmadan durulur (çıkış 9). Başarılı geri yükleme `geri-yukleme-notu.json`'a yedeğin adını, kenara alınan
  `db-onceki-<damga>` dosyasının adını ve sha256'sını, kullanılan yolu (hesap tanıtıcısı ya da kurtarma anahtarı no'su)
  ve kenara alınan veritabanının zincir başını (son `seq` + MAC) yazar. İlk kilit açılışında not denetim izine
  `GERI_YUKLEME` satırı olarak geçer, çapa yenilenir ve `yonetici` ile DK panosunda kart çıkar; kart DK "gördüm" diyene
  dek kalır. `db-onceki-*` 14 günlük rotasyondadır (§4.4.7): bu sürede DK kenara alınan veritabanını isteyebilir;
  zincir başı izde kaldığı için sonra da kâğıt çapasıyla karşılaştırılabilir.
- **İki depo karşılaştırması** her açılışta ve geri yüklemeden sonraki ilk kilit açılışında yapılır (§4.6.1).
- **Arşiv:** her durum yazımından önce `guvenlik-arsiv-<damga>.json` (aile); hesap kapanınca sarmalı bütün arşiv
  kopyalarından da silinir (TK11).
- **DEK yenileme (TK12, F4).** Ön koşul: `yonetici` oturumu açık; hesap geçişinde eski dönemin organ hesapları kapanmış
  ve yeni dönemin organ hesabı henüz açılmamış (MY değişiminde ve elle başlatmada bu koşul aranmaz); uzun iş sayacı
  artar.
  1. Parola yeniden sorulur; `pre-dek-yenileme-<tarih>` yedeği (eski DEK).
  2. Zincir eski iz anahtarlarıyla **tam** doğrulanır; kırıksa yenileme durur, DK panosuna kart düşer.
  3. Yeni DEK, yeni İA ve yeni kurtarma anahtarı (no + 1) üretilir. Yeni DEK `yonetici` parolası ve yeni kurtarma
     anahtarıyla sarılır ve `guvenlik.json`'a **veritabanından önce** `gecis: {tur: "DEK_YENILEME", yeni: {sarmallar,
     kurtarma}, eski_parmak_izi, yeni_parmak_izi}` olarak atomik yazılır.
  4. Tek SQLite işleminde yeni DEK'le: şifreli alanlar, kör indeksler, hareket parmak izleri, hesap mühürleri, dosya
     anahtarı sarmalları, eski iz anahtarlarının şifreli kopyaları; yeni İA eklenir; parmak izi; `DEK_YENILEME` satırı
     (eski İA'yla mühürlü son satır; sonraki satırlar yeni İA'yla). Öteki açık hesaplar (`mudur`, öteki `yonetici`)
     `PAROLA_YENILENMELI` olur.
  5. `guvenlik.json`: `gecis`'teki sarmallar etkinleşir; öteki hesapların ve `guvenlik-arsiv-*` kopyalarının eski DEK
     sarmalları silinir; `gecis` kalkar. `yedekleme.json` yeni açık anahtarla yazılır.
  6. Yeni kurtarma anahtarı (no, tarih) basılır, saklandığı doğrulanır (aile `dogrulandi` deseni); okul müdürlüğünde
     mühürlü zarfa girer (D3).
  7. Yeni anahtarla **tam yedek** alınır, açılıp doğrulanır; sonra eski zarfın **imha tutanağı** basılır ve zarf
     yok edilir (D3; §9.7 program belgeleri). Devir tutanağına yalnız "kurtarma anahtarı zarfı müdürlükte, mührü sağlam; anahtar no, tarih"
     kaydı girer.

  **Yarıda kalma** (denetim GA-12): açılışta `gecis` görülürse veritabanındaki parmak izi `gecis`'teki iki değerden
  hangisine eşitse o DEK kullanılır (karşılaştırma DEK istemez). Eskiye eşitse (kesinti 1-3 arası) `gecis` silinir,
  yenileme olmamış sayılır ve `yonetici`ye bildirilir. Yeniye eşitse (kesinti 4'ten sonra) 5 tamamlanır; 6 tamamlanmadıysa
  ilk `yonetici` girişinde yeni bir kurtarma anahtarı üretilip basılır (değeri gösterilmeden kaybolan anahtar
  kullanılmaz). Ailenin `resume_pending` deseni yalnız tek anahtarlı şifreleme geçişini sürdürür, bu akışı karşılamaz.
  **Prova** (F4 kapısı): her adımdan sonra süreç öldürülür, program açılır, veri, dosyalar ve zincir doğrulanır.

#### 4.4.5 Hesap yaşam döngüsü

Hesap olaylarının **tek kaynağı** bu tablodur; §5 ve §7 buraya gönderir (denetim UY-8, SU-6; R12).

| Olay | Hesaba etkisi | Kim | Ne zaman |
|---|---|---|---|
| Kurulum (sihirbaz 1. adım) | İlk `yonetici` hesabı + parola + kurtarma anahtarı (no 1); anahtar basılıp saklandığı doğrulanmadan kurulum bitmez; ilk İA üretilir; `pre-parola` yedeği | Kuran kişi | İlk açılış |
| Hesap açma | Önce `Account` satırı (`PAROLA_YENILENMELI`, mühür), sonra DEK geçici parolayla sarılır; ilk girişte parola değişimi zorunlu, durum `ACIK`; organ rolünde üyelik bağı (F1c); hesap teslim pusulası (E63: tanıtıcı, rol, açılış tarihi; parola taşımaz — geçici parola ayrı kapalı zarfta verilir, okul uygulaması; [BSG Yön. md. 10/1](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) parolanın görünür yere yazılmasını yasaklar) | `yonetici` | Görevlendirmede ya da hesap geçişinde |
| Parola değiştirme | Kendi sarmalı yenilenir; eskisiyle aynı olamaz | Hesap sahibi | Her an; 180 gün dolunca girişte (TK15) |
| Parola unutuldu (organ, müdür, öteki yönetici) | DEK yeni geçici parolayla sarılır, `PAROLA_YENILENMELI`; sıfırlama denetim izine; sahibine ilk girişte bildirim (tehdit 12) | `yonetici` | İstek üzerine |
| Yönetici parolası unutuldu | Başka `yonetici` sıfırlar; yoksa kurtarma anahtarıyla o hesabın parolası yenilenir (ayrı iz türü, bildirim; §4.4.3) | Başka `yonetici` ya da zarfı açan | İstek üzerine |
| Ardışık hatalı deneme (organ, müdür) | 10. hatada `guvenlik.json`'da askı; giriş kapanır | Sistem; askıyı `yonetici` kaldırır | Anında (§15 M-12) |
| Üyelik düştü ([md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)), görev değişti ([md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) | Kayıtla **aynı işlemde** `ASKIDA` (giriş kapanır); `yonetici`nin "hesap önerileri" listesine düşer: kapanış, sarmalın silinmesi (TK11), yeni görevliye hesap | Askı: kaydı yazan (programın etkisi); kapanış ve açılış: `yonetici` | Askı anında; kapanış aynı gün hedeflenir, yapılmadıkça panoda kart |
| Yeni dönemin görev bölümü ([md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) | Eski dönemin organ hesapları `ASKIDA`; **hesap geçişi** önerilir ve tek akışta yürür: (1) eski organ hesapları kapanır, sarmallar silinir; (2) DEK yenilenir (TK12; öteki açık hesaplar `PAROLA_YENILENMELI`); (3) yeni organ hesapları yeni DEK'le, tek geçici parolayla açılır | Askı: görev bölümünü yazan; geçiş: `yonetici` | Görev bölümü kaydından sonra; yapılmadıkça panoda kart |
| Dönem kapanışı (`KAPANISTA → KAPANDI`) | Hesaplara etkisi yok (geçiş görev bölümünde yapıldı); kapanmış döneme yalnız işaret alanları ve yeniden basım kaydı yazılır (R12). Eski dönemin kalan işi yeni dönemin hesaplarıyla yürür; mali kayıtları muhasip girer (D2; §7.8) | `yonetici` (başkan onayı aranmaz) | §7.8 |
| Müdür değişti | `mudur` hesabı kapanır, yenisi açılır | `yonetici` | Görev değişiminde |
| MY değişti | Yeni `yonetici` hesabı açılır, eskisi kapanır, DEK yenilenir (TK12; dönem ön koşulu yok); devir notu (KütD-E18 kalıbı) F4'te | Giden MY ya da kurtarma anahtarıyla gelen | Görev değişiminde |
| Geri yükleme | İki depo karşılaştırılır (§4.6.1): sarmalı olmayan açık hesap `PAROLA_YENILENMELI`; açık satırı olmayan sarmal `yonetici` onayıyla silinir | `yonetici` | Geri yüklemeden sonraki ilk kilit açılışı |
| Hesap mührü tutmadı | Oturum açılmaz; satıra dokunulmaz; olay denetim izine, kart `yonetici` ve DK panosuna | Program; inceleyen `yonetici` ve DK | Kilit açılışında |

#### 4.4.6 Dürüst sınırlar (kılavuz ve Hakkında'ya girer)

1. **Rol kriptografik değildir.** Her hesap aynı veri anahtarını açar; rol kısıtı program içindedir.
   Hesapların değeri "kim, ne zaman, ne yaptı" sorusunun cevabıdır.
2. **Anahtar yenilemek önceki yedekleri kapatmaz;** yenilemeden önceki yedekler eski zarf imha edilene dek eski
   anahtarla açılır. Eski zarf imha edilince yenilemeden önceki bütün yedekler (USB'dekiler dâhil) açılmaz olur;
   kapanmış dönemin programsız okunan kaydı arşiv paketidir (§8.5). DEK yenilemesi (TK12) yalnız **sonraki** verinin
   ve yedeklerin korunmasını sağlar.
3. **Açık oturum, sahibinin imzasıdır.** Bilgisayar başından kalkarken Kilitle.
4. Kişisel veri içeren her çıktı (Word, PDF, Excel) programın dışına çıktığı anda programın korumasından çıkar.
5. **Şifreli alanlar en zayıf hesap parolası kadar korunur:** `guvenlik.json` veritabanıyla aynı diskte durur ve
   her hesap sarmalı veri anahtarını tek başına verir. Tam koruma disk şifrelemesidir (BitLocker; Pardus'ta LUKS).
6. **Kayıp ya da çalınmada bildirim okulundur.** Bilgisayar, disk, USB yedeği ya da arşiv paketi kaybolur ya da
   çalınırsa [KVKK md. 12/5](../mevzuat/6698-kvkk.md#madde-12) bildirimi (ilgilisine ve Kurula, en kısa sürede) veri
   sorumlusunun, yani okulun işidir. Program yalnız yardım eder: "ihlal dökümü" seçilen tarihte programda bulunan veri
   kategorilerini ve kişi sayılarını kişisiz verir (§8.6). Kılavuz kontrol listesini yazar (denetim KM-18).

#### 4.4.7 Dosya deposu ve yedekler

**Dosya deposu** (TK22). Ekler ve üretilmiş evrak veri dizinindeki `dosyalar/<stored_name>`'de, dosya anahtarıyla
şifreli durur (§4.4.4). Depo tek yazımlıdır: dosya bir kez yazılır, değişmez; yalnız KVKK imhasında silinir (`purged_at`
kalır). Veli adı taşıyan E07 çizelgesi ve adlı E08 depoya hiç yazılmaz (R9).

- **Açık kopya kuralı** (denetim GA-2, EK-15). İndirme ve yazdırma yanıtı bellekten akar, `Cache-Control: no-store`
  taşır; program kendi geçici dizinine açık kopya bırakmaz; açık dosya yalnız kullanıcının "kaydet" dediği yerde oluşur
  (tehdit 15). İçe aktarılan ham dosyalar da diske yazılmadan bellekte okunur (§5.4).
- **Yetim ve eksik dosya.** Açılışta satırı olmayan dosya (eski bir yedeğin geri yüklenmesinden sonra) `dosyalar/yetim/`'e
  taşınır, 14 gün sonra silinir; satırı olup dosyası olmayan kayıt "dosya yok" gösterir ve panoya bütünlük uyarısı düşer.

**Yedek türleri** (denetim GA-1, GA-5, KM-10; R10):

| Yedek | Ne zaman | Kapsam | Saklama |
|---|---|---|---|
| `gunluk-<tarih>.odbak` | Açılışta ve gün değişiminde, günde bir | Veritabanı + manifesto | 14 gün |
| `pre-migrate-<sürüm>-<tarih>.odbak` | Göçten önce | Veritabanı + manifesto | Son 5; ayrıca KVKK silme tetiğinden önce alınmış olanlar tetikten sonra silinir |
| `pre-parola-*` | Kurulumda (kişi verisi yokken) | Veritabanı | 14 gün |
| `pre-anonim-<tarih-saat>.odbak` | Elle KVKK silme tetiğinden önce (F4+) | Veritabanı + manifesto | 14 gün |
| `pre-kapanis-<tarih>.odbak` | Dönem kapanışından önce (§7.8) | Veritabanı + manifesto | 14 gün |
| `pre-dek-yenileme-<tarih>.odbak` | DEK yenilemesinden önce (eski DEK) | Veritabanı + manifesto | 14 gün; eski zarf imha edilince açılamaz |
| `db-onceki-<damga>.sqlite3` | Geri yüklemede kenara alınan veritabanı | Veritabanı (şifreli alanlar şifreli) | 14 gün |
| İndirilen yedek (`oab-defteri-yedek-<damga>.odbak`), dış (USB) yedek | Kullanıcı ister; program hatırlatır | **Tam:** veritabanı + dosya deposunun tamamı | Kullanıcının elindedir; imha kuralı kılavuzda |

- **Kap** (`ODBAK\x03`). Aile kabı (MAGIC, geçici X25519 açık anahtar, nonce, uzunluk, kurtarma başlığı, AES-256-GCM
  (veritabanı görüntüsü ‖ manifesto)) aynen kalır; tam yedekte ardına **dosya bölümü** eklenir: her dosya ad, boyut ve
  şifreli içerikle sırayla, ikinci kez şifrelenmeden (dosyalar zaten dosya anahtarıyla şifrelidir, sarmallar mühürlü
  veritabanının içindedir). Manifesto (ad, boyut, sha256) mühürlü bölümdedir: geri yükleme dosya bölümünü manifestoyla
  doğrulamadan takas yapmaz. Yerel yedek manifestoyu taşır, dosya bölümünü taşımaz; geri yüklemede manifestodaki
  dosyalar depoda aranır, eksikler adıyla listelenir. Dosyalar bellekte toplanmaz, akışla kopyalanır (4 GB'lık makine).
- **Neden yerel yedek dosyasız:** yerel yedekler aynı diskte durur; disk arızasında dosya deposuyla birlikte gider,
  bu riske karşılık dış (tam) yedektir. Dosya içeriği değişmediği ve DEK yenilemesi yalnız sarmalları yenilediği için
  veritabanı yedeği dosya deposuyla tutarlı kalır. Her günlük yedeğe dosyaları koymak, yıllar içinde büyüyen depoyu
  14 kez çoğaltırdı.

**Rotasyon ve KVKK sınırı** (denetim GA-5, KM-10).

1. Rotasyon tek işlevdir ve yukarıdaki önek kümesini kapsar; adı desene uymayan dosyaya dokunulmaz (aile kuralı).
   Küme testle sabitlenir: her önek için "15. günde silinir" testi.
2. Dönem kapanışı silmelerinden ve elle KVKK silme tetiğinden sonra: `PRAGMA wal_checkpoint(TRUNCATE)` (TB24); tetik
   anından eski `pre-migrate-*` yedekleri adıyla silinir, silinemeyen adıyla yeniden denenir (ailenin
   `pre_migrate_before` + `remove_pre_migrate_named` kalıbı).
3. Sonuç: silinen kişisel veri programın **yerel** yedeklerinde en çok 14 gün kalır. Rotasyon program açıkken koşar;
   program açılmadan geçen günlerde silme bekler.
4. Dışarı alınmış yedekler programın erişiminde değildir: kapanışta "bu tarihten önce dışarı aldığınız yedekler silinen
   veriyi taşır; imha kuralı kılavuzdadır" kartı gösterilir. Eski kurtarma zarfı imha edilince bu yedekler de açılmaz
   olur (§4.4.6-2).
5. Test (F4 kapısı): kapanıştan sonra veritabanında, `AuditTrail`'de, arşiv paketinde ve 15. günden sonra yedek
   dizininde (yedekler açılarak) uydurma veli adı, istekli telefonu ve e-postası, T.C. kimlik no bulunmaz.

### 4.5 Pencere (T6)

| Konu | Davranış | Not |
|---|---|---|
| Çarpı | Programı kapatır, onay sorulmaz. `closing` işleyicisi yalnız uzun yazma işi sürerken kapanışı bir kez erteler (§4.2); başka hâlde kapanmayı iptal etmez | T6; Windows oturum kapanışındaki iptal-geri-alma geçişi gereksizleşir, testle sabitlenip silinir |
| Tepsi | Yok: `tray.py`, pystray/six, `gorev-kur.ps1`, `.iss` `otobaslat`/`tepside` görevleri sökülür | Qt kurulumu önce ayrılır (§13 D1) |
| Otomatik başlatma, uyku engeli | Yok | Katalog olmadığı için uyku engeli gerekçesi düşer |
| İkinci açılış | Çalışan pencere öne gelir (`goster`), ikinci süreç 0 ile çıkar | `instance_channel.py` aynen |
| Arayüzdeki Çık | Kalır (`modules/cikis`), parola istemez | Linux'ta pencere süslemesi olmayan masaüstü (TB13 dersi); "yeniden başlat" ekranının çıkış yolu |
| Kurucu ve kaldırıcı | `.Kapat` olayı + 30 sn mutex bekleme; `AppMutex` yok | §4.2 |
| Linux | `qt_kurulum.hazirla()` pencereden önce; SIGTERM → düzenli kapanış (temiz kapanış işareti + checkpoint). `setQuitOnLastWindowClosed` değeri ve Pardus davranışı F1a'da elle doğrulanır. **Dosya izinleri** (denetim GA-20): açılışta `os.umask(0o077)`; veri, günlük, önbellek ve yedek dizinleri 0700 oluşturulur, var olanlar 0700'e çekilir; `guvenlik.json`, `yedekleme.json`, `iz-durumu.json`, `.odbak` ve dosya deposu 0600 yazılır; `.deb` `postinst` kullanıcı dizinine dokunmaz. Test: Linux'ta açılıştan sonra dizin ve dosya kipleri | `prerm` açık programı kapatmaz (TB40); çarpı = çık ile olasılık düşer. Aile dizinleri varsayılan umask'la açıyordu (§13 D52). Kılavuz: "Pardus'ta programı kendi kullanıcı hesabınızda çalıştırın" |
| Ekran | 1366×768'de yatay kaydırmasız kullanılabilir ([ön değerlendirme §5.2](../kesif/2026-10-31-on-degerlendirme.md)); pencere boyutu aile değeri | 4 GB RAM'li eski okul bilgisayarı |
| Başlık ve görev çubuğu | "OAB Defteri"; AUMID `OABDefteri.Desktop`; Linux `StartupWMClass=oab-defteri` | §2.3 |

**Kanıt.** Birim: `on_closing` iş yokken kapanmayı iptal etmez, iş sürerken bir kez erteler; `serve` sonrası WAL
checkpoint ve temiz kapanış işareti yazılır, iş öldürülmüşse yazılmaz. "Exe açılır, çarpıyla kapanır, çıkış kodu doğru"
F1a kapısında **elle** doğrulanır (CI pencereye tıklayamaz); `packaging/windows/NOTLAR.md`'ye madde olarak girer.

**Hesap ve bilgisayar.**

- Program **okul demirbaşı** bilgisayara kurulur; muhasibin evdeki bilgisayarına kurulum önerilmez: kişisel veri ve
  mali kayıt kurum dışına çıkar, devir zorlaşır ([ön değerlendirme §4.2](../kesif/2026-10-31-on-degerlendirme.md)).
- Veri, programı çalıştıran Windows hesabının `%LOCALAPPDATA%\OABDefteri` dizinindedir. `ProgramData`'ya taşınmaz
  (bütün hesaplara okuma hakkı verirdi), `%APPDATA%`'ya konmaz (gezici profil açık SQLite'ı bozar). Sonuç: **veri tek
  Windows hesabında durur**, program o hesapta çalışır.
- **Öneri (§15 M-8):** bilgisayarda yönetici yetkisi olmayan ayrı bir "OAB" Windows hesabı; MY'nin kişisel oturumu
  (e-Okul, MEBBİS, DYS, e-posta açık) velilere açılmaz. Bu hesapta program **yönetici kipinde** kurulur (TK7).
  [BSG Yön. md. 7/2, 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) ve
  [md. 9/2-e](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) her kullanıcının kendi Windows oturumunu
  ve şifrenin paylaşılmamasını öngörür; ortak hesabın parolası kurul üyelerince bilineceği için bu tam karşılanamaz —
  program içindeki kişisel hesaplar "kim" sorusunu cevaplar, sapma kılavuzda açıkça yazılır (denetim GA-15). Kılavuz
  maddesi: ortak hesabın parolası yalnız görevdeki kurul üyelerinde ve MY'de olur; kurul değiştiğinde (hesap geçişinde)
  MY değiştirir. Reddedilen seçenek: veriyi erişim listeli ortak dizine (`ProgramData` + yerel grup) almak — yönetici
  kurulumu ve BTR'nin grup bakımını ister, aile çizgisinden sapar.
- BitLocker önerilir (tehdit 6, 9). USB'ye alınan dış yedek şifrelidir
  ([BSG Yön. md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)).
- **Yeni bilgisayara taşıma:** kurulum → **tam** `.odbak` geri yükleme (kurtarma anahtarı: müdürlükteki zarf; TK10) →
  yönetici parolası → öteki hesaplara geçici parola → ekli bir kaydın açıldığı denetlenir. Kontrol listesi
  kılavuzdadır.

### 4.6 Hesap, denetim izi ve erişim günlüğü — modeller

Güvenlik çekirdeğinin dört modeli burada tanımlanır; §5 ve öteki bölümler buraya gönderir, tanımı tekrar etmez (R1;
denetim GA-7, KM-2, UY-2, EK-8). Hepsi `apps/okul`'dadır ve F1b'de gelir. Ortak kural: bu modellerin **silme ucu
yoktur**; `AccessLog` dışında satır da silinmez. Alan adları İngilizcedir (§5 O8).

#### 4.6.1 `Account`

| Alan | Tür ve değerler | Not |
|---|---|---|
| `id` | UUID | `guvenlik.json` `hesaplar[].id` ile aynı |
| `login_name` | kısa metin, açık | `guvenlik.json` `tanitici` ile aynı; gerçek ad olmaz (§4.4.4) |
| `role` | rol kodu (§2.3.1) | Hesap açıldıktan sonra değişmez; görev değişince yeni hesap |
| `display_name` | şifreli (Fernet); kör indeks yok | Ad-soyad; kilit ekranında gösterilmez |
| `person` | → `OabPerson`, boş olabilir | Organ rollerinde dolu; `yonetici` ve `mudur`'da boş |
| `membership` | → `OrganMembership`, boş olabilir | Organ rollerinde F1c'den itibaren zorunlu |
| `term` | → `OabTerm`, boş olabilir | Organ hesabının dönemi |
| `status` | `PAROLA_YENILENMELI` · `ACIK` · `ASKIDA` · `KAPALI` | `KAPALI` geri dönmez |
| `suspend_reason` | `UYELIK_DUSTU` · `GOREV_BOLUMU` · boş | Hatalı deneme askısı `guvenlik.json`'dadır (§4.4.4) |
| `opened_at`, `opened_by` | zaman, → `Account` | |
| `closed_at`, `closed_by` | zaman, → `Account` | |
| `password_changed_at` | zaman | 180 gün kuralı (TK15) |
| `reset_at`, `reset_by`, `reset_notice_pending` | zaman, → `Account`, evet/hayır | Sıfırlama ve kurtarma bildirimi (tehdit 12) |
| `last_login_at` | zaman | "Son girişler" kartı |
| `seal` | HMAC-SHA256, açık | `HMAC(HKDF(DEK, "od-hesap-muhru/v1"), kanonik(id, login_name, role, status, person, membership, term, opened_at, closed_at))` |

**Kısıtlar** (sert; sistem bütünlüğü): açık (`KAPALI` olmayan) hesaplar arasında `login_name` tekil · aynı üyeliğe
bağlı tek açık hesap · `baskan`, `baskan_yardimcisi`, `muhasip`, `sekreter` ve `mudur` için aynı anda tek açık hesap,
`denetleme_kurulu` için en çok üç · en az bir açık `yonetici` (son yönetici kapatılamaz) · satır silinmez (TK11; altın
kural 4).

**İki depo kuralı** (`guvenlik.json` ↔ `Account`; denetim GA-11, UY-8):

1. **Giriş** ikisi birden tutarlıysa açılır: sarmal parolayla açılır **ve** `Account` satırı var, durumu `ACIK` ya da
   `PAROLA_YENILENMELI`, mührü tutar. Biri eksikse giriş reddedilir. Mühür tutmazsa satıra dokunulmaz (yeniden
   mühürlemek değiştirilmiş rolü meşrulaştırırdı); olay denetim izine düşer, `yonetici` ve DK panosuna kart çıkar.
2. **Açma:** önce veritabanı (`PAROLA_YENILENMELI`, mühür), sonra `guvenlik.json` sarmalı. Arada kesilirse satır
   sarmalsız kalır; giriş zaten açılmaz, `yonetici` yeniden geçici parola verir.
3. **Kapama:** önce veritabanı (`KAPALI`, `closed_at`, mühür), sonra `guvenlik.json` ve bütün `guvenlik-arsiv-*`
   kopyalarından sarmal silinir. Dosya adımı yarıda kalırsa her açılışta koşan "kapalı hesabın sarmalı duruyor"
   denetimi sarmalı siler (fikirdeş).
4. **Geri yüklemeden sonra** ilk kilit açılışında iki depo karşılaştırılır, fark `yonetici`ye liste olarak gösterilir:
   veritabanında açık ama sarmalı olmayan hesap `PAROLA_YENILENMELI` olur; sarmalı olup satırı olmayan ya da satırı
   `KAPALI` olan sarmal `yonetici` onayıyla silinir.

F1b testleri bu dört hâli ve mühür bozulmasını kapsar.

#### 4.6.2 `AuditTrail`

| Alan | Tür ve değerler | Not |
|---|---|---|
| `seq` | tamsayı, birincil anahtar, artan | Zincir sırası |
| `at` | zaman damgası (Europe/Istanbul) | |
| `actor` | `HESAP` · `SISTEM` | `SISTEM`: kullanıcı eylemi olmadan programın yaptığı iş |
| `account` | → `Account`; `SISTEM`'de boş | |
| `role` | rol kodu; `SISTEM`'de boş | Yazma anındaki rol |
| `action` | kapalı küme: `OLUSTUR` · `GUNCELLE` · `DURUM` · `TERS_KAYIT` · `ISARET` · `BASIM` · `KVKK_SILME` · `GIRIS` · `KILIT` · `HESAP` · `PAROLA` · `KURTARMA` · `YEDEK` · `GOC` · `GERI_YUKLEME` · `DEK_YENILEME` · `BUTUNLUK` · `GUN_ISI` | Küme testle sabitlenir; yeni tür göçle eklenir |
| `model`, `object_id` | metin, kimlik | Kaydın kendisi |
| `term` | → `OabTerm`, boş olabilir | DK görünümü dönemle süzer |
| `changed_fields` | JSON liste | Değişen **alan adları**; değer yok |
| `values` | JSON `{alan: [önce, sonra]}` | Yalnız modelin **izinli kişisiz alanları** (tutar, tarih, durum, sayı, numara, kod); izin listesi modelde tanımlıdır; KVKK silme kümesindeki modellerde boştur |
| `record_mac` | HMAC-SHA256, boş olabilir | İçerik MAC'i (aşağıda) |
| `compliance_item` | → `ComplianceItem`, boş olabilir | Gerekçe bağı (§5 O3); gerekçenin metni orada şifreli |
| `label` | `GECIS` · `KISA_YOL` · `KAPALI_DONEM` · boş | `GECIS`: geçiş kurulumunun yazmaları (§7.9); `KISA_YOL`: genel karar kapsamındaki kısa yol harcaması (§7.4); `KAPALI_DONEM`: kapanmış döneme beyaz listedeki yazma — işaret ya da yeniden basım (§5 O2, R12) |
| `key_mode` | `ACIK` · `KILITLI` | Hangi anahtarla mühürlendiği (§4.6.3) |
| `key_ref` | `AuditKey` kimliği ya da (çapa `seq`, adım) | Doğrulayıcının anahtarı bulması için |
| `prev_mac`, `mac` | HMAC-SHA256 | Zincir |

**"Kaydın özeti" — bağlayıcı kural** (R1). Denetim izi satırı **kişisel veri taşımaz**: kayıt kimliği, değişen alan
adları, izinli kişisiz alanların değeri ve içerik MAC'i. Kişi adı, telefon, T.C. kimlik no, adres, serbest metin,
gerekçe metni ve veli listesinin (`ParentRoster`) hiçbir alanı ne açık ne şifreli olarak satıra girmez. Şifreli alanın
değiştiği yalnız alan adıyla görünür.

**İçerik MAC'i.** `record_mac = HMAC(HKDF(İA, "od-kayit-ozeti/v1"), kanonik(model, object_id, alanların çözülmüş
değerleri))`; yazmadan sonraki hâli özetler. Kayıt bütünlüğü denetimi kaydın bugünkü değerinden MAC'i yeniden hesaplar ve
o kaydın son iz satırıyla karşılaştırır: program dışından yapılan değişiklik, şifreli sütuna yazılmış düz metin ve bir
satırdan ötekine taşınmış Fernet token'ı burada görünür (denetim GA-9). **MAC dışı alanlar:** KVKK gereği boşaltılan
ya da silinen alanlar (§5.4: bağışçı T.C. kimlik no, istekli iletişim bilgisi, katılım ve görev alma engelinin dayanağı, imha edilen
dosya) ve veli listesi modelinin tamamı MAC'e girmez. Gerekçe: silinen değerin MAC'i kalsaydı anahtara erişen biri
olasılık uzayı dar değeri (telefon, T.C. kimlik no) deneyerek geri bulabilir, silme anlamsızlaşırdı.

**Yazma kuralları.**

1. Veri satırı ile iz satırı **aynı `IMMEDIATE` işlemde** yazılır; biri yazılamazsa ikisi de geri alınır. Yazar
   bağlamı olmayan yazma reddedilir.
2. Ekleme-yalnızdır: modelde güncelleme ve silme hata verir; ayrıca SQLite tetikleyicisi (`BEFORE UPDATE`,
   `BEFORE DELETE` → `RAISE`) program içi kazayı önler. Program dışındaki değişikliği zincir yakalar.
3. Her durum geçişi ayrı satırdır (§5 O4); evrak basımı `BASIM` satırıdır (tür, sha256; evrak izi §9).
4. KVKK silmesi `KVKK_SILME` satırıdır: model, alan adları, adet, tetik; değer yok (§5.4).
5. Satır silinmez, anonimleştirilmez (birlik kaydı; §5.4). Arşiv paketindeki "denetim izi dökümü" aynı sütunlardan
   üretilir, fazlasını taşımaz (§8.5).
6. **Test (F1b kapısı):** her model için uydurma ad, telefon ve T.C. kimlik no içeren kayıt yazılır, güncellenir,
   KVKK silmesi uygulanır; sonra `AuditTrail`'in bütün sütunlarında ve arşiv dökümünde bu değerler aranır — sonuç
   sıfır.

#### 4.6.3 Mühür, çapa ve kilitliyken yazım

*R11'in karşılığı: iz anahtarı DEK'ten bağımsızdır; kilitliyken de iz yazılır; zincir kuyruğunun kesilmesine karşı çapa
vardır (denetim GA-8, GA-9, UY-1).*

**İz anahtarı (İA).** Kurulumda üretilen 32 bayt; **DEK'ten türemez**. `AuditKey` tablosunda DEK'le şifreli
(Fernet) durur: veritabanıyla birlikte yedeğe girer, geri yükleme hangi yoldan yapılırsa yapılsın zincir doğrulanabilir.
`guvenlik.json`'a konmaz: kurtarma anahtarıyla geri yüklemede o dosya yalnız kurtarma bölümüyle yeniden yazılır, İA
orada olsaydı kaybolurdu.

| `AuditKey` alanı | Not |
|---|---|
| `id` | |
| `key` | şifreli (DEK) |
| `valid_from_seq` | Bu anahtarla mühürlenen ilk satır |
| `created_at`, `retired_at` | |

- Kilit açıkken her satır: `mac = HMAC(HKDF(İA, "od-denetim-izi/v1"), kanonik(satır) ‖ prev_mac)`.
- **DEK yenilemesinde** (TK12) yeni İA üretilir; eski İA'lar yeni DEK'le yeniden şifrelenir ve eski satırları
  doğrulamaya devam eder. Zincir **yeniden mühürlenmez**: kâğıda inmiş çapalar geçerli kalır. Eski İA'yı bilen eski
  üye yenilemeden sonraki satırları mühürleyemez; zincir bağlı olduğu için eski satırları da fark edilmeden
  değiştiremez.

**Kilitliyken yazım.** DEK yokken iş verisi yazılmaz (§4.1). Kilitliyken yalnız kapalı bir kümedeki kişisiz sistem
olayı yazılır: `YEDEK` (alındı, rotasyon), `GOC` (şema göçü uygulandı), `GUN_ISI` (DEK istediği için ertelendi),
`BUTUNLUK` (açılış bütünlük denetimi). Bunlar `record_mac` taşımaz, hiçbir veri değişikliğini meşrulaştıramaz.
Mühürleri **kilitli kip anahtarıyla**dır:

- Her kilitlenmede ve düzenli kapanışta `iz-durumu.json`'a (atomik yazım, Linux'ta 0600) **çapa** yazılır:
  `{seq, mac, muhur}`, `muhur = HMAC(HKDF(İA, "od-iz-capa/v1"), seq ‖ mac)`. Aynı anda kilitli kip tohumu yazılır:
  `tohum₀ = HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)`, `adim = 0`.
- Kilitliyken k'ıncı satır `HMAC(HKDF(tohumₖ, "od-iz-kilitli-mac/v1"), kanonik(satır) ‖ prev_mac)` ile mühürlenir
  (`key_mode = KILITLI`, `key_ref = (çapa seq, k)`); ardından `tohumₖ₊₁ = SHA-256("ileri" ‖ tohumₖ)` dosyaya yazılır,
  eski tohum silinir. Bu ileriye dönük güvenli bir mühürdür: dosyayı bir an okuyan kişi o andan **önce** yazılmış kilitli
  satırları ve kilit açıkken yazılmış hiçbir satırı değiştiremez.
- Geri yükleme notu varken kilitli satır yazılmaz; o açılışın sistem olayları ilk kilit açılışında yazılır.
- `iz-durumu.json` yoksa ya da bozuksa kilitli satır mühürsüz yazılır; ilk kilit açılışında "çapa yok" bütünlük
  uyarısı çıkar.

**Kilit açılışında kendiliğinden doğrulama.** DEK ve İA yüklenince: (1) çapanın mührü tutuyor mu ve veritabanında
çapanın `seq` satırının `mac`'i çapaya eşit mi — değilse "denetim izi kuyruğu kesilmiş ya da veritabanı geri sarılmış"
uyarısı (geri yükleme notu bunu açıklıyorsa uyarı yerine `GERI_YUKLEME` satırı); (2) çapadan sonraki kilitli satırlar
tohumdan yeniden türetilerek doğrulanır ve sayıları dosyadaki `adim`'e eşit mi; (3) son 200 satırın zinciri. Uyarı
`BUTUNLUK` satırı olarak denetim izine, kart olarak `yonetici` ve DK panosuna düşer; giriş engellenmez (altın kural 3:
sert engel hesap bütünlüğündedir). **Tam doğrulama** DK modülünde elle ve dönem kapanışında kendiliğinden koşar (§7.8).

**Kâğıt çapası.** Zincir başı ("Kayıt no: N · Zincir: XXXX-XXXX"; `mac`'in ilk 8 onaltılık hanesi) aylık bildirime,
deftere geçirilecek aylık baskıya ve devir-teslim tutanağına basılır (E31, E17, E37; §9); kilit açılışındaki "son girişler" kartında da
görünür. Zincir böylece her ay programın dışına, kâğıda iner.

**Uzun iş sayacı.** Kapanış, arşiv paketi, DEK yenileme, banka özeti uygulama, canlı geri yükleme ve tam yedek
`shared/bakim.py` sayacını artırır; sayaç sıfır değilken boşta kilit ertelenir (§4.4.3) ve çarpı kapanışı bekletir
(§4.2).

**Kalan risk** (dürüst sınır). Veritabanı ve `iz-durumu.json` birlikte eski kopyayla değiştirilirse program fark etmez;
aylık kâğıt çapası yakalar. Parolasını bilen biri DEK'i ve İA'yı dışarıda çözüp zinciri yeniden hesaplayabilir (tehdit
6); kâğıt çapası yine son katmandır. Kilitli kip tohumu dosyada açıktır: dosyayı okuyan kişi o andan sonraki kilitli
satırları taklit edebilir; bu satırlar veri değiştirmez.

#### 4.6.4 `AccessLog`

Hassas okumanın ve kişisel veri içeren çıktının kaydıdır ([KVKK md. 12](../mevzuat/6698-kvkk.md#madde-12) güvenlik
tedbiri; OYS'nin "okuma ≠ yönetme ≠ hassas detay" ayrımı). **Zincir dışıdır**, süresi dolunca silinir, okunan değeri
tutmaz.

| Alan | Not |
|---|---|
| `id`, `at` | |
| `account`, `role` | → `Account`; okuyan |
| `kind` | `MASKESIZ_TCKN` · `KISI_DOKUMU` · `VELI_LISTESI_CIKTISI` (adlı E07, E08) · `KISISEL_DISA_AKTARIM` · `IHLAL_DOKUMU` · `OZEL_NITELIKLI_EK` · `OZEL_NITELIKLI_ALAN` (kantin isteklisinin katılım engeli dayanağı `Bidder.participation_bar_basis`, organ üyesinin görev alma engeli dayanağı `OrganMembership.eligibility_bar_basis`; §5.2.2, §5.2.9) |
| `model`, `object_id`, `field` | Okunan kaydın kimliği ve alan adı; değer yok |
| `document_sha256`, `row_count` | Çıktıysa |

- Kişisel veri: yalnız okuyan hesabın bağı ve okunan kaydın kimliği (takma ad düzeyinde); şifrelenmez.
- **Saklama:** 2 yıl (§15 B-9; DOĞRULANMADI). Silme kilit açıkken gün işiyle yapılır; silinen satır sayısı ve en yeni
  tarih denetim izine `KVKK_SILME` satırı olarak düşer.
- Arşiv paketine girmez: saklama süresi arşivinkinden kısadır (§8.5).
- Okuyan: `yonetici` ve DK (§4.4.2).

#### 4.6.5 Özet: kişisel veri, koruma, saklama

| Model ya da dosya | Kişisel veri | Koruma | Saklama |
|---|---|---|---|
| `Account` | `display_name`; kişi ve üyelik bağı | `display_name` şifreli; satır mühürlü | Silinmez (altın kural 4; organ üyesinin adı birlik kaydıyla kalır, §5.4) |
| `AuditTrail` | Yok (yalnız hesap bağı) | HMAC zinciri (İA) | Silinmez (birlik kaydı) |
| `AuditKey` | Yok | Anahtar şifreli (DEK) | Silinmez |
| `AccessLog` | Okuyan hesap + okunan kaydın kimliği | Açık; değer tutmaz | 2 yıl (B-9) |
| `iz-durumu.json` | Yok | Çapa mühürlü; Linux'ta 0600 | Sürekli üzerine yazılır |
| `guvenlik.json` | Yok (tanıtıcı gerçek ad olmaz) | Sarmallar Argon2id | Kapanan hesabın sarmalı silinir (TK11) |

§5.3 şifreleme tablosu bu satırlara gönderir.

---

## 5. Veri modeli

Bu bölüm modelleri, alanları, kısıtları ve ilişkileri verir. Kuralların değerleri kural paketindedir (§6), evrakın adı,
kodu ve şablonu evrak kataloğunda (§9). `Account`, `AuditTrail`, `AuditKey` ve `AccessLog` modelleri §4.6'da,
şifreleme çekirdeği §4.4.4'tedir; bu bölüm onları tekrar etmez, yalnız atıf yapar. OYS'den gelen modellerde "Kaynak" sütunu
[OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) §2'deki modeli ve yapılan değişikliği yazar; **YENİ** OYS'de
karşılığı olmayan modeldir. Çıkarım sınıfının kesin hâli §12.A'dadır.

**Ortak ilkeler**

| # | İlke | Ayrıntı |
|---|---|---|
| O1 | Silme ucu yok | Hiçbir alan modelinin silme ucu yoktur (altın kural 4). OYS `BaseModel.deleted_at` yumuşak silmesi alınmaz (envanter S-22; §15 A-8). Kesinleşmemiş yanlış kayıt `IPTAL` durumuna geçer (gerekçe ve kim alanlarıyla); `IPTAL` durumu taşıyan modeller: `OabTerm` (hazırlıkta), `OrganMembership`, `BoardMeeting`, `BoardDecision`, `OabBudget`, `LedgerEntry`, `ExpenseFile`, `ExpenseInvoice`, `SocialEvent`, `ReceiptBookRegistry`, `ReceiptLeaf`, `Tender`, `OabContract`, `ContractInstallment`; durum alanı olmayan satır modellerinde iptal işareti vardır (`BudgetLine.is_cancelled`, `AgendaItem.removed_by_vote`). Kişi kaydı `PASIF` olur; kesinleşmiş mali kayıt ters kayıtla düzeltilir (§5.2.5). OYS'nin "canlı kayıt" koşullu tekil kısıtları "iptal olmayan" koşuluna döner. Tek istisna KVKK silmesi ve anonimleştirmesidir (§5.4): onaylı tetikle, iz bırakarak |
| O2 | Dönem kilidi | `term` taşıyan her kayıt, dönemi `KAPANDI` ise yazılamaz (sert — kapanmış dönem). **Beyaz liste** (kapanıştan sonra beklenen yazmalar; kullanıcı ve ana oturum kararı R12): (1) işaret alanları — gelir-gider kaydının "deftere geçirildi" (`posted_book`, `posted_page`, `posted_at`, `posting_batch`) ve "TEFBİS'e girildi" (`tefbis_entered_at`, `tefbis_entered_by`, `tefbis_batch`) alanları, kararın `KABUL_EDILDI → DEFTERE_ISLENDI` geçişi ve defter alanları (`book`, `decision_no`, `page_no`, `entered_by`, `entered_at`, `page_photo`), bu işaretleri toplayan `MarkBatch` satırı; (2) yeniden basım — `GeneratedDocument`'ın yeni sürüm satırı ve eskisinin `YERINI_ALDI` geçişi (veli adı taşıyan belge hariç, §5.2.8); (3) bu işaretlerin kapattığı `ComplianceItem(EKSIK)` satırının `resolved_at`'ı. Tutar, tarih, hesap, metin, oy ve öteki durumlar kilitli kalır; beyaz listedeki her yazma denetim izine ayrı satır yazar. "TEFBİS'te düzeltilecek" bilgisi asıl kayda yazılmaz, ters kayıttan hesaplanır (§5.2.5). `HAZIRLIK` dönemine yalnız genel kurul hazırlığı (aday ve seçim üyelikleri, tahmini bütçe, genel kurul evrakı) yazılır; mali kayıt yazılmaz (§5.2.1). Dönemsiz kayıtlar (kişi, koçan, defter, sözleşme, kiralanan yer) kendi durum kilidini taşır |
| O3 | Uygun · eksik · sapma | Kural denetimi kayıt anında yapılır (§6.1 `denetle`); sonuç üç durumdan biridir. **Uygun.** **Eksik:** kuralın istediği bilgi henüz girilmemiştir ve süreçte sonra dolacaktır (kural şemasında `eksik_veri: tamamlanacak` olan kurallar, §6.1; `eksik_veri: sapma` olan kuralda — aylık bildirim, dönemlik duyuru, YK aylık toplantısı — eksiklik baştan sapmadır); kayıt gerekçesiz yazılır, bir `ComplianceItem(EKSIK)` satırı açılır ve panonun "tamamlanacaklar" listesine düşer (§7.10); bilgi girilince satır `resolved_at` ile kapanır. Eksik, kaydı kapatan geçişte (`KESIN`, `DEFTERE_ISLENDI`, harcama `ODENDI` ve `KAPANDI`, genel kurul `TUTANAK_TAMAM`, sözleşme `IMZALANDI`, süreç `KESINLESTI`, dönem kapanışı) hâlâ duruyorsa sapmaya döner ve gerekçe ister. **Sapma:** kural bilerek uygulanmıyor ya da girilen değer kuraldan sapıyor; gerekçesiz geçmez (altın kural 3): `ComplianceItem(SAPMA)` satırı (gerekçe şifreli, kim-ne zaman). **Toplu gerekçe:** aynı kural ve aynı kök neden için tek gerekçe (`ComplianceJustification`) birden çok sapma satırına bağlanır — ör. bir karar defterinin tasdik kaydı girilmemişse defter başına bir kez; programdan önceki seçilme sayıları bilinmiyorsa geçiş kurulumunda bir kez (§7.9); küçük alımda eksik halka genel karar no'suna bağlı bir kez (§15 A-11); `toplu_gerekce: false` olan kuralda (`harcama.organ_uyesine_odeme`, `kantin.kiralama_onay_kaydi`) her kayıt kendi gerekçesini ister. Sık gerekçeler seçilebilir kalıptır. Kayıt güncel uyarı özetini `rule_warnings` (JSON: kural kimliği, madde, ileti, durum, paket ve revizyon) alanında tutar. OYS'nin model başına `compliance_warnings`/`compliance_justification` alanları ve `_persist_tender_warnings` deseni (AYNEN) bu tabloya taşınır; Denetleme Kurulu bütün sapmaları tek listede görür ve liste "eksik" satırlarla dolmaz. Sert ihlal hiç geçmez (altın kural 3; programın **hesapladığı** değerde sert, kullanıcının belgeden **girdiği** değerde uyarı — kullanıcı kararı D1) |
| O4 | Temel alanlar | `created_at`, `created_by`, `updated_at`, `updated_by` (→ `Account`, §4.6.1). Her durum geçişi denetim izine ayrı satır yazar: önceki ve sonraki durum, gerekçe varsa `ComplianceItem` bağı; kişisel ya da şifreli alanın değeri denetim izine girmez, yalnız alan adı (§4.6.2). Her model denetim izine **değeri** yazılabilen kişisiz alanlarını (tutar, tarih, durum, sayı, numara, kod) izin listesiyle tanımlar; KVKK silme kümesindeki alanlar (§5.4) değer listesine de içerik MAC'ine de girmez (§4.6.2) |
| O5 | Para ve tarih | `Decimal(14,2)`, kuruş, ROUND_HALF_UP (OYS `_q` AYNEN). Pay dağıtımında kuruş korunur: toplam = parçaların toplamı; artık birlik payına kalır (§6.4.11-4). Tarih alanı yerel gündür; zaman damgası Europe/Istanbul; görünüm gg.aa.yyyy |
| O6 | Tek kaynak | Bir bilgi tek modelde durur, evrak oradan okur (OYS'nin evrak ilkesi, AYNEN): seçilen üyeler `OrganMembership`'ten, tutarlar `LedgerEntry`'den, yeter sayı `GeneralAssembly`'den, yaprak–kayıt bağı `LeafUse`'tan, ödeme bağı `LedgerEntry.expense_invoice`'tan. Evrak üretimi veriyi kopyalamaz; `GeneratedDocument` yalnız içerik özetini ve dosyayı tutar |
| O7 | Anlık görüntü | Sonradan değişebilen okul kartı değerleri (öğrenci mevcudu, yerleşim türü) hesaba girdiği anda kayda kopyalanır; okul kartı değişse de geçmiş hesap değişmez (altın kural 2'nin veri karşılığı) |
| O8 | Adlandırma | Model ve alan adları İngilizce; OYS'den UYARLA'lananlar OYS adını korur. Enum değerleri OYS'deki gibi Türkçe büyük harf ASCII (`ASIL`, `YEDEK`, `KAPANDI`); etiketleri Türkçe ve Yönetmelik terimiyle ("Denetleme Kurulu", "muhasip", "tahmini bütçe") |

### 5.1 Okul çekirdeği (Kütüphane Defteri `apps/okul` — UYARLA)

Kaynak: [iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md) §2.8. Kütüphane'deki modeller korunur; OAB'ye
özgü alanlar `SchoolConfig`'e eklenir, öğrenci tarafı T5 gereği sökülür.

| Model | Sınıf | OAB Defteri'nde |
|---|---|---|
| `SchoolConfig` (pk=1) | UYARLA | Aşağıdaki OAB alanları eklenir; `kutuphane_saatleri` ve kütüphaneye özgü alanlar düşer; `app_password_hash` parmak izi §4.4.4'te. Alanlar sonradan boşaltılamaz (aile kuralı); her değişiklik denetim izine düşer |
| `SchoolYear` | AYNEN | Ders yılı. `OabTerm.school_year` buna bağlanır (T3 eşlemi) |
| `SchoolTerm` | AYNEN | Ders yılının iki dönemi. Dönemlik gelir-gider duyurusu ([md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) "her dönem") ve yarıyıl ayında yarım kira ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) bu kayıttan okunur |
| `Holiday` | AYNEN (Disiplin Defteri'nden UYARLA'lı hâli) | İş günü hesabı: elden bağış beş iş günü ([md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)), servis onay ve tebliği beşer iş günü ([Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)). `SCHOOL_BREAK` yarıyıl tatilini tanır |
| `Personnel` | UYARLA | e-Okul personel listesinden ad-soyad (şifreli) ve `member_kind` (öğretmen · yönetici · diğer); "Görevi" sütunu yalnız türü belirlemek için geçici okunur, saklanmaz. Ayrılış havuzu (Kütüphane F1 eki 7) alınır, ama Kütüphane'de silmeyi yapan saklama servisi alınmadığından silme kuralı burada yazılır: ayrıldı işaretlenen ve hiçbir birlik kaydına bağı olmayan personel, ayrılışı izleyen dönem kapanışında silinir (§5.4). `OabPerson.personnel` ile isteğe bağlı bağ |
| `Student`, `ClassSection` | ALMA | T5: öğrenci listesi alınmaz. Öğrenci mevcudu okul kartında elle; veli listesindeki sınıf düz metindir (`ParentRoster`, §5.2.2) |
| `ImportRun` | UYARLA | Türler: `PERSONEL`, `VELI` (§8.4). `payload_sha256`, satır sayısı, önizleme özeti; ham dosya saklanmaz. Banka ve TEFBİS partileri kendi modellerindedir (`BankStatement`, `TefbisStatement`) |
| `Account`, `AuditTrail`, `AuditKey`, `AccessLog` | YENİ (§4.6) | Alanlar, şifreleme, kısıtlar, saklama ve denetim izindeki "kaydın özeti"nin tanımı §4.6'dadır; tanım orada. Bu bölümdeki her `created_by`/`updated_by` `Account`'a bağlanır; her durum geçişi `AuditTrail`'e, her hassas okuma `AccessLog`'a yazar |

**`SchoolConfig`'e eklenen OAB alanları**

| Alan | Değerler | Kullanıldığı yer ve dayanak | Not |
|---|---|---|---|
| `institution_code`, `school_name`, `district`, `province` | metin | Antet (`letterhead.py`), arşiv paketi adı | Aile alanlarının OAB karşılığı |
| `levels` (kademeler) | çok değerli: `OKUL_ONCESI` · `ILKOKUL` · `ORTAOKUL` · `ORTAOGRETIM` | Kursiyer türünün görünürlüğü ([md. 4/1-ğ](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4), [md. 7/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7)); temsilci kurulları ([OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25), [OKY md. 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OÖİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57)) | Birden çok kademeli kurumda birden çok değer seçilir ("karma" ayrı değer değildir); kural paketinin `kosul` alanı kesişimle bakar (§6.1). Yaygın eğitim v1 kapsamı dışındadır, seçenek yoktur (§3.5) |
| `in_campus` | mantıksal | Kampüs yönetimine temsilci ([md. 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)); kampüsteki okul kapsamdadır ([md. 2/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-2)) | Temsilciler çizelgesinde `KAMPUS_YONETIMI` satırının koşulu |
| `student_count`, `student_count_as_of` | sayı, tarih | Genel kurul yeter sayısı çarpanı ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); kantin kirasında %25 değişim ([md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) | Genel kurul ilan edilirken ve sözleşme imzalanırken anlık görüntü alınır (O7) |
| `settlement_type` (yerleşim türü) | `BUYUKSEHIR` · `IL_MERKEZI_BUYUKSEHIR_DEGIL` · `DIGER` | Pay dağılımı: büyükşehir olmayan il merkezinde ilçe payı yok, il payı %20 ([md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) | OYS `is_metropolitan` yerine (envanter S-17) |
| `canteen_mode` | `KIRAYA_VERILIYOR` · `BIRLIKCE_ISLETILIYOR` · `KANTIN_YOK` | Arz bedeli %3 kiracıdan ya da %1 birlikten ([md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [md. 17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)); işletmede VUK ([md. 23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | İşletmede vergi bilgi metni (özelge, `bilgi/`) |
| `staffing_mode` | `DOGRUDAN_ISVEREN` · `HIZMET_ALIMI` · `CALISTIRMIYOR` | K3; kıdem karşılığı ([md. 6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)) | Personel modülü (sürüm 2) yalnız doğrudan işverende açılır; hizmet alımı harcama zincirinden (sürekli ödeme dosyası, §7.4) geçer |
| `opened_on` | tarih (çoğu okulda boş) | Yeni açılan okulda genel kurul iki ay içinde ([md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); serviste ilk kez EK-3 puanlaması ([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)) | — |
| `registration_periods` | tarih aralıkları listesi | Kayıt-kabul ve diploma döneminde bağış toplanmaz ([md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [Genelge 2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni)) → uyarı | Tarihleri mevzuat vermez; okul girer. Boşken uyarı çalışmaz, kurulum yol haritasında madde olur (§7.10) |
| `small_purchase_limit`, `standing_decision` | tutar, → `BoardDecision` | Küçük alımda talep ve komisyon halkasının gerekçesi ve kısa yolu ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); saha 6; §15 A-11; §7.4) | Kural paketine değil okul ayarına; genel karar her dönem YK'ce yenilenir |
| `donor_tckn_enabled` | mantıksal (varsayılan kapalı) | K9 | Açılması yönetici + gerekçe + denetim izi; kapatılması mevcut değerleri boşaltma önerir |
| `third_approval_enabled` | mantıksal | İnternet bankacılığında üçüncü onay (F0-e c) | Ödeme talimatında müdür onay satırı; "mevzuat gereği" diye sunulmaz |
| `data_controller_text` | metin | Aydınlatma metninde veri sorumlusu ve iletişim ([KVKK md. 10/1-a](../mevzuat/6698-kvkk.md#madde-10)); E04 | Boşken E04 basılmaz; kim olduğu okul müdürlüğünün değerlendirmesidir (F0-e b, §3.4, §15 KE-20) |
| `scan_retention_years` | sayı (öneri 2) | Kiracı, çalışan, şoför ve rehber belge taramalarının sözleşme sonundan sonraki saklama süresi (§5.4) | Okul ayarı; süre DOĞRULANMADI (§15 B-5); kural paketine girmez (altın kural 1) |

Kurulum sihirbazı (plan §2.2) bu modelleri şu sırayla doldurur: 1) yönetici hesabı ve kurtarma anahtarı (§4.4.4, §4.4.5) 2)
`SchoolConfig` 3) `SchoolYear`, `SchoolTerm`, `Holiday` — bu üç adım F1b'dedir; 4) ilk birlik dönemi ve görevdeki
kurul (F1c) 5) `BankAccount`, `LedgerAccount`, ilk `OpeningBalance`, defter ve koçan envanteri (F3). Dördüncü ve
beşinci adım, dönem ortasında başlayan okulun **geçiş kurulumudur** (§7.9): ilk `OabTerm` son olağan genel kurulun
tarihiyle açılır; görevdeki kurul "devralınan" üyelik olarak girilir; açılış bakiyesinin günü ve programdan önceki
aralık §7.9'dadır.

### 5.2 OAB modelleri

#### 5.2.1 Kural paketi ve birlik dönemi

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `RulePackage` | `package` (ör. `OAB-2023.12`) · `rev` · `schema_version` · `content` (dondurulmuş JSON kopyası) · `content_sha256` · `loaded_at` | (`package`, `rev`) tekil; içerik yazıldıktan sonra değişmez, yeni revizyon yeni satırdır (altın kural 2; §6.2-4). Açılışta dağıtılan dosyanın özetiyle karşılaştırılır (§6.3 D7) | YENİ |
| `OabTerm` | `name` (ör. "2026-2027 birlik dönemi") · `school_year` → `SchoolYear` · `start_date` (dönemi açan olağan genel kurulun yapıldığı gün — birinci ya da ikinci toplantı; `HAZIRLIK`'te boş) · `end_date` (sonraki olağan genel kurul gününden bir önceki gün; açıkken boş) · `opened_by_assembly` → `GeneralAssembly` (geçiş kurulumunda boş) · `rule_package` → `RulePackage` (PROTECT) · `status` (`HAZIRLIK` → `ACIK` → `KAPANISTA` → `KAPANDI`; `HAZIRLIK` → `IPTAL`) · `program_start_date` (geçiş kurulumunda programa başlama günü; boşsa `start_date`, §7.9) · `pre_program_income`, `pre_program_expense` (dönem başı ile programa başlama arasındaki gelir ve gider toplamı; defterden ya da TEFBİS'ten) · `pre_program_evidence` (şifreli; kanıtın yeri: defter sayfaları, TEFBİS dökümü) · `yk_meeting_day_rule` (dönem ayarı: YK aylık toplantı günü kuralı, ör. "her ayın ilk salısı"; takvim ve `yonetim_kurulu.toplanti_sikligi`) · `dk_audit_plan_dates` (dönem ayarı: DK'nin denetim planındaki inceleme tarihleri; E02, E14, `denetleme_kurulu.inceleme_yilda_en_az`) · `closed_at`, `closed_by` · `archive_document` → `GeneratedDocument` | Dönem aralıkları çakışmaz; en çok bir `HAZIRLIK` ve bir `ACIK` dönem; mali kaydın tarihi kaydın dönem aralığında olmalı (sert — hesap bütünlüğü). **Hazırlık (R12, UY-5):** olağan genel kurul `PLANLANDI` olunca yeni dönem `HAZIRLIK` durumunda açılır; tarih aralığı boştur, çakışma ve tarih–dönem kısıtları ona uygulanmaz; YK ve DK adayları ile seçilenler ve tahmini bütçe bu döneme yazılır, mali kayıt yazılmaz (O2). Genel kurul `TUTANAK_TAMAM` olunca `start_date` toplantı günü olur, dönem `ACIK`'a geçer; önceki `ACIK` dönem `KAPANISTA`'ya geçer ve `end_date`'i bir önceki gündür (§7.1, §7.8). Genel kurul `IPTAL` olursa `HAZIRLIK` dönemi de `IPTAL` olur. `KAPANISTA` dönem sayısı sınırlanmaz (tarih aralıkları çakışmadığı için kayıt dönemi tektir); kapanmayan dönem panoda durur (§7.8, §7.10). `rule_package` yalnız revizyon geçişi ekranından ve `KAPANDI` olmayan dönemde değişir (§6.2-5, 6). Görev süresi bir yıl ([md. 12/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) sonraki olağan genel kurula kadar sayılır. Olağanüstü genel kurul yeni dönem açmaz, aynı dönemde organ yeniler ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13): olağanüstü genel kurulca seçilen YK olağan toplantıya kadar görev yapar). `program_start_date` ve programdan önceki toplamlar yalnız geçiş kurulumunda yazılır, sonra değişmez | OYS `OabTerm` UYARLA: `core.SchoolYear` → okul `SchoolYear`; `is_active` → `status` (hazırlık durumu eklenir); kilit, kural bağı ve geçiş alanları eklenir |

**İki "dönem".** Birlik dönemi (`OabTerm`, T3: genel kuruldan genel kurula) ile ders yılının iki dönemi (`SchoolTerm`)
ayrı kavramlardır; [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)'daki "her dönem" ders dönemidir. Arayüz ikisini "birlik dönemi" ve "ders dönemi" diye
yazar. TEFBİS'in dönem esası (takvim yılı mı öğretim yılı mı) DOĞRULANMADI; program TEFBİS için dönem zorlamaz,
liste ve mutabakat tarih aralığıyla çalışır (§15'e öneri B-1).

#### 5.2.2 Kişiler, organlar, veli listesi

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `OabPerson` | `kind` (`VELI` · `OGRETMEN` · `IDARECI` · `HAYIRSEVER` · `KURSIYER` · `DIGER`) · `first_name`, `last_name` (şifreli) · `name_index` (kör indeks) · `is_parent` (velidir: okulda öğrencisi var; türü `OGRETMEN` ya da `IDARECI` olan kişi de veli olabilir — YK, DK veli koltuğu ve divan uygunluğu bu işarete bakar, §6.4.1-§6.4.3) · `adult_declared` (kursiyer için "18 yaşını doldurmuştur" beyanı; doğum tarihi tutulmaz) · `is_principal` (okul müdürü) · `personnel` → `Personnel` · `external_yk_terms`, `external_dk_chair_terms` (programdan önceki seçilme sayıları; eski karar defterinden beyan ya da "bilinmiyor"; geçiş kurulumunda toplu girilir, §7.9; sayım biçimi §15 B-12) · `status` (`AKTIF` · `PASIF`) | T.C. kimlik no ve telefon alanı yoktur (K9; telefonun programda amacı yok — SMS, e-posta ve evrakta kullanılmaz, §3.4). `name_index` tekil değildir (adaşlık); aynı indeksle ikinci kayıtta "olası aynı kişi" uyarısı. Hayırsever yalnız okul yaptırıp Bakanlığa bağışlayan kişidir ([md. 7/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7)); bağışçı kişi kaydı açmaz (bağışçı adı gelir kaydında, §5.2.5). Hiçbir birlik kaydına bağlanmamış kişi kaydı dönem kapanışında silinir (§5.4) | OYS `OabPerson` UYARLA: `tckn`, `tckn_hash`, TCKN tekil kısıtı ve doğrulaması, `phone`, `phone_hash`, `linked_user_id` çıkar; ad-soyad şifrelenir (aile kuralı); yaş beyanı ve geçmiş sayaçlar eklenir |
| `OrganMembership` | `term` · `person` · `organ` (`YK` · `DK` · `DIVAN` · `ALIM_KOMISYONU` · `TEMSILCI`) · `assembly` → `GeneralAssembly` (seçildiği genel kurul; divanda ve genel kurul seçiminde zorunlu, öteki kanallarda boş) · `role` (`BASKAN` · `BASKAN_YARDIMCISI` · `MUHASIP` · `SEKRETER` · `KATIP` · `UYE`) · `seat_type` (`ASIL` · `YEDEK`) · `seat_group` (DK'da `VELI` · `OGRETMEN`) · `votes` (aldığı oy) · `seat_order` (yedek sırası, oydan) · `elected_by` (`GENEL_KURUL` · `OGRETMENLER_KURULU` · `MEM_GOREVLENDIRME` · `YK_KARARI` · `OKUL_IDARESI` · `KENDILIGINDEN`) · `source` (`PROGRAM` · `DEVRALINAN` — geçiş kurulumunda programdan önce seçilmiş görevdeki üye, §7.9) · `evidence_note` (devralınanda: seçildiği genel kurulun tarihi, görev bölümü kararının defter sıra no'su) · `representation` (temsilcide, aşağıda) · `status` (`ADAY` → `SECILDI` → `DUSTU`; `ADAY` · `SECILDI` → `IPTAL`, yanlış kayıt, gerekçe ve kim) · `start_date`, `end_date` · `promoted_on`, `promoted_by_decision` → `BoardDecision` (yedekten asıla geçiş) · `drop_kind` (`OGRENCI_AYRILDI` · `DEVAMSIZLIK` · `ISTIFA` · `BASKA_KURUMDA_GOREV` · `OLAGANUSTU_GK_SECIMI` · `DIGER`) · `dropped_reason` (şifreli, isteğe bağlı) · `eligibility_declared_on` (okulun suç engeli beyanı uygulamasının tarihi — beyan Yönetmeliğin değil okulun yöntemidir; görev alamama hükmü [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), §6.4) · `single_birlik_declared_on` (aynı biçimde; hüküm [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) 2. cümle) · `expertise_required` (`ALIM_KOMISYONU`'nda YK üyesi olmayan üye için "uzmanlık gerektiren iş" işareti; [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) · `eligibility_bar` (`YOK` · `VAR`; hüküm alanı: görev alma engeli tespit edildi) · `eligibility_bar_basis` (şifreli, hassasiyet `OZEL_NITELIKLI`: `SUC_12_5_14_7` · `TEK_BIRLIK_12_4`; okuması erişim günlüğüne) · `eligibility_bar_found_on` (tespit tarihi; düşürme önerisinin günü) · `retained_until_assembly` ([md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) istisnası işareti) · `rule_warnings` | İki kısmi tekil kısıt, ikisi de `IPTAL` olmayanlarda: `assembly` doluyken (dönem, organ, kişi, genel kurul); `assembly` boşken (dönem, organ, kişi) — SQLite tekil dizinde NULL'ları ayrı saydığından tek kısıt genel kurul dışı seçimlerde etkisiz kalırdı (denetim UY-10). Koltuk uygunluğu aşağıdaki tabloda. Genel kurul seçiminde `SECILDI` yalnız aynı genel kurulun `ADAY` kaydından olur (tek kaynak — sert); bu kural `source = DEVRALINAN` üyelikte ve genel kurul dışı kanallarda (öğretmenler kurulu, YK kararı, MEM görevlendirmesi, okul idaresi) aranmaz. Olağan genel kurulun YK ve DK adayları ile seçilenleri yeni (`HAZIRLIK`) döneme, divan genel kurulun kendi dönemine yazılır (§5.2.1). Düşmede `drop_kind` zorunlu. `eligibility_bar = VAR` olan kişinin seçimi uyarı + gerekçe, görevdeki üyede düşürme önerisi (`uyelik.suc_engeli`, `yonetim_kurulu.tek_birlik`); düşme türü `DIGER` olur, engelin hangi hükümden geldiği yalnız şifreli dayanakta durur (suç engeli ceza mahkûmiyeti verisidir, [KVKK md. 6/1](../mevzuat/6698-kvkk.md#madde-6); §15 B-16) | OYS `OrganMembership` UYARLA: organ türleri genişler (plan §2.3); şifreli beyan notu yerine yalnız tarih (envanter S-20) — böylece `kvkk_special_category` bayrağı da kalkar; `NITELIK_KAYBI` düşme türü `DIGER`'e katılır (Yönetmelikte yalnız suç hükmüne işaret ederdi; gerekçe şifreli kalır); yedek çağırma, oy, temsil, devralınan üyelik ve iptal eklenir |
| `ParentRoster` | `import_run` → `ImportRun` · `term` · `full_name` (şifreli) · `name_index` (kör indeks) · `student_class` (düz metin, ör. "9-A") · `attended_assembly` → `GeneralAssembly` (boş olabilir) · `attended_meeting` (`BIRINCI` · `IKINCI`) | Bir satır bir öğrencidir; iki çocuklu veli iki satırdır ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1 "velisi katılan öğrenci sayısı" bunu ister). Öğrencinin adı, numarası, T.C. kimlik no, telefon, adres alınmaz (T5). Kaynak dosyadaki satır sırası tutulmaz: sınıf ve satır no ikilisi veliyi bulmaya yeterdi (denetim KM-11); sıralama sınıfa ve çözülmüş ada göre Python'da yapılır. Başka hiçbir model buna yabancı anahtar vermez (silinebilirlik); adaylığa geçen veli için ad `OabPerson`'a kopyalanır. Dönem kapanışında bütün satırlar silinir (§5.4, §7.8) | YENİ (T5 kararı) |

**Temsil türleri (`representation`).** `ODUL_DISIPLIN_KURULU` ([OKY md. 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OKY md. 186](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-186)) · `DAVRANIS_DEGERLENDIRME_KURULU`
([OÖİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57)) · `SOSYAL_ETKINLIKLER_KURULU` ([SEY md. 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6)) · `KONTENJAN_KOMISYONU` ([OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25)) · `RPD_YURUTME_KOMISYONU`
([RPD Yön. md. 16](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16)) · `TASIMACI_TESPIT_KOMISYONU` (birlik başkanı; [Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3), [Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3)) · `MUHAMMEN_BEDEL_KOMISYONU` (birlik
başkanı; [md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) · `KIRALAMA_IHALE_KOMISYONU` (birlik başkanı; [md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) · `KAMPUS_YONETIMI` ([md. 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); okul kartında `in_campus`) ·
`KANTIN_DENETIM_KOMISYONU` ([Genelge 2020/8](../mevzuat/okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md); korpusta çapasız, kural yok — yalnız kayıt) · `DIGER`. Kurul bileşimleri kural
paketindedir (§6.4.4).

**Koltuk uygunluğu**

| Koltuk | Kim oturabilir | Tür | Dayanak |
|---|---|---|---|
| YK asıl ve yedek | veli (`is_parent`; veli olan öğretmen ve idareci dâhil) · `KURSIYER` (`adult_declared`) · `HAYIRSEVER` (isterse) | sert (hukuken geçersiz seçim) | [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| YK, her koltuk | Okul müdürü (`is_principal`) olamaz | sert | Proje kuralı 6; [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) (§6.4.2 yorumu); kullanıcı kararı §15.1 KE-15 |
| DK veli koltuğu (1+1) | veli (`is_parent`) · `KURSIYER` (`adult_declared`); hayırsever **değil** | sert | [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [md. 11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) (OYS hayırseveri sayıyordu, envanter S-8) |
| DK öğretmen koltukları (2+2) | `OGRETMEN`; okulda yeterli öğretmen yoksa il/ilçe MEM onayıyla başka okulun öğretmeni | sert (tür) · uyarı (onay kaydı eksik) | [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Divan başkanı ve kâtip | veli (`is_parent`; veli olan öğretmen ve idareci dâhil) · `KURSIYER` (`adult_declared`) | uyarı | [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) |
| Alım komisyonu | YK üyeleri; uzmanlık gereken işte birlik üyeleri (`expertise_required` işaretiyle); en az üç kişi | uyarı | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) |
| Sayılar (YK 5+5, DK 3+3) | Eksik bileşim | uyarı; genel kurul yeter sayısının tabanını etkilemez (sabit 16, §5.2.3) | [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Aynı kişi aynı dönemde YK'de ve DK'de | — | **sert** — kullanıcı kararı (31.10.2026): denetleyen ile denetlenen ayrılığı | `denetleme_kurulu.yk_uyesi_olamaz`; §15 A-2 |

#### 5.2.3 Genel kurul

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `GeneralAssembly` | `term` (olağanda kapanacak dönem: çağrıyı o dönemin YK'si yapar, raporlar o döneme aittir) · `opens_term` → `OabTerm` (olağanda açılacak `HAZIRLIK` dönemi; olağanüstüde boş) · `kind` (`OLAGAN` · `OLAGANUSTU`) · `called_by` (`YONETIM_KURULU` · `OKUL_MUDURU` · `MUDUR_YENI_OKUL` · `DENETLEME_KURULU` · `UYE_BASVURUSU` · `BASKAN_VEYA_MUDUR_13_8` · `MUDUR_25_2`) · `call_reason` (şifreli; olağanüstüde zorunlu) · `call_decision` → `BoardDecision` · `call_document` → `DocumentRecord` (müdür ya da DK yazısı, üye başvurusu) · `call_audit_report` → `AuditReport` (DK çağrısında, md. 6'ya aykırılık işaretli rapor) · `member_application_count` (%10 başvurusunda başvuran sayısı; kişi listesi tutulmaz) · `announced_on` · `venue` · `first_meeting_at` · `second_meeting_at` · `second_announced_on` · `student_count_snapshot` · `quorum_base` (16) · `quorum_multiplier` (4 ya da 2) · `quorum_required` · `first_attendee_count` · `second_attendee_count` · `held_at_meeting` (`BIRINCI` · `IKINCI`) · `attendance_by_kind` (JSON sayılar: veli/kursiyer, öğretmen, yönetici, hayırsever, diğer) · `parent_students_count` (velisi katılan öğrenci sayısı) · `observer_count` ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) gözlemci öğrenci; oy yok) · `discharge_yk`, `discharge_dk` (`EDILDI` · `EDILMEDI` · `GORUSULMEDI`) · `budget` → `OabBudget` · `status` (§7.1) · `rule_warnings` | Yeter sayı = 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban organ bileşiminden gelir, üyelik kayıtlarından sayılmaz; olağanüstüde de aynı ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) — ilan anında hesaplanır, dondurulur, elle değiştirilemez (sert — yeter sayı hesabı). Birinci toplantı katılımı yeter sayının altındaysa "yapıldı" olamaz (sert). İkinci toplantı olağanda da olağanüstüde de açılır (kullanıcı kararı §15.1 A-1). Katılım sayıları `TUTANAK_TAMAM`'dan sonra yalnız gerekçeli düzeltme satırıyla (`AttendanceCorrection`) değişir. Olağanda `PLANLANDI` geçişi `opens_term`'ü açar (§5.2.1) | OYS `GeneralAssembly` UYARLA: taban sabitlenir (envanter S-1, S-2); `follows_failed_assembly` öz FK kalkar, iki toplantı aynı kayıtta; `attendee_count` ikiye ayrılır; ibra, katılım dağılımı, 30 gün ve Ekim sonu denetimleri ve açılacak dönem bağı eklenir; `venue` ve ikinci toplantı yazılabilir olur |
| `AgendaItem` | `assembly` · `order` · `kind` (`ACILIS` · `DIVAN_SECIMI` · `YK_FAALIYET_RAPORU` · `DK_RAPORU` · `IBRA` · `TAHMINI_BUTCE` · `YETKILENDIRME` · `SECIM_YK` · `SECIM_DK` · `ONERILER` · `DILEK` · `KAPANIS` · `DIGER`) · `title` · `notes` (şifreli) · `added_by_vote`, `removed_by_vote` + `change_votes_for`, `change_votes_against` ([md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9): ekleme ve çıkarma oy çokluğuyla; çıkarılan madde silinmez) · `result_text` (şifreli) · `votes_for`, `votes_against` · `result` (`KABUL` · `RET` · `GORUSULDU`) | (genel kurul, sıra) tekil; SQLite tekil kısıtı ertelemediği için sıra değişikliği servis katmanında geçici değerle iki adımda yapılır. Olağanüstüde çağrı gündemi dışında madde eklenirse **uyarı + gerekçe** ([md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) "gündeme bağlılık ilkesi geçerlidir"; `genel_kurul.olaganustu_gundeme_baglilik`; kullanıcı kararı §15.1 B-13). Tohum gündemi [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) yetkilendirme ve [md. 11/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) öneriler maddelerini de içerir | OYS `AgendaItem` **AYNEN → UYARLA** (envanterden sapma): tür, sonuç, oy ve çıkarma alanları eklenir |
| `AssemblyMinutes` | `assembly` (1:1) · divan `OrganMembership(DIVAN)` kayıtlarından · `yk_report_reader`, `dk_report_reader`, `budget_presenter` → `OabPerson` · `unaudited_documents_note` (şifreli; ibra edilmeyen muhasebe evrakı listesi, [md. 11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11)) · `handed_to_new_yk_on` ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10)) | Seçilen üyeler `OrganMembership`'ten okunur (tek kaynak, AYNEN) | OYS `AssemblyMinutes` UYARLA: serbest metin adlar kişi kaydına bağlanır |
| `AttendanceCorrection` | `assembly` · `meeting` (`BIRINCI` · `IKINCI`) · `field` (düzeltilen sayı alanı) · `old_value`, `new_value` · `justification` (şifreli) · `corrected_by`, `corrected_at` | Ekleme-yalnız; `GeneralAssembly`'deki sayı son düzeltme satırının değeridir. Düzeltme yeter sayının sağlanıp sağlanmadığını değiştiriyorsa uyarı + gerekçe; dondurulmuş yeter sayının kendisi düzeltilemez (sert) | YENİ |

Olağanüstü genel kurulda ikinci toplantı: [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) çoğunluk aranmayan ikinci toplantıyı tekrarlamaz (envanter S-3);
**kullanıcı kararı (31.10.2026):** md. 9/2'deki ikinci toplantı olağanüstü genel kurulda da uygulanır (§15.1 A-1).

#### 5.2.4 Kurul toplantıları, kararlar, denetim

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `BoardMeeting` | `term` · `organ` (`YK` · `DK`) · `meeting_no` (dönem içinde sıra) · `kind` (`AYLIK` · `OLAGANUSTU` · `GOREV_BOLUMU`) · `scheduled_at`, `held_at` · `place` · `agenda` (şifreli) · `status` (`PLANLANDI` → `YAPILDI` · `YETER_SAYI_YOK` · `IPTAL`) | YK'de `YAPILDI` için en az dört üye ([md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) — sert. `YAPILDI`/`YETER_SAYI_YOK`'a geçerken görevdeki her asıl üyenin katılım satırı zorunlu (sert; devamsızlık sayımının bütünlüğü, envanter S-19, §15 A-9). `YETER_SAYI_YOK` toplantısına yalnız `DEFTERDE_SAKAT` karar bağlanabilir | OYS `BoardMeeting` UYARLA: tür, durum, yeter sayı denetimi |
| `BoardMeetingAttendance` | `meeting` · `membership` · `present` · `excused` | (toplantı, üyelik) tekil. Özrün nedeni ve belgesi tutulmaz (sağlık verisi olabilir) | OYS AYNEN |
| `BoardDecision` | `meeting` · `kind` (`OLAGAN` · `GENEL_KARAR` · `HARCAMA` · `GOREV_BOLUMU` · `YEDEK_CAGIRMA` · `KOCAN_KAYIT` · `GK_CAGRISI` · `BUTCE` · `DIGER`) · `text` (şifreli) · `votes_for`, `votes_against` · `dissent` (şifreli, isteğe bağlı) · `status` (`TASLAK` → `KABUL_EDILDI` · `REDDEDILDI`; `KABUL_EDILDI` → `DEFTERE_ISLENDI`; `TASLAK` → `IPTAL`; `DEFTERDE_SAKAT`) · `book` → `OfficialBook` (karar defteri) · `decision_no` (defter sıra no) · `page_no` · `decision_date` · `entered_by`, `entered_at` (deftere işleyen) · `page_photo` → `Attachment` (isteğe bağlı) · `amends` → `BoardDecision` | Kabul oyu ≥ 3 ([md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) ve toplantı `YAPILDI` — sert: program bu koşulları sağlamayan kararı **geçerli saymaz**. Defterde fiilen yazılı olan böyle bir karar **`DEFTERDE_SAKAT`** olarak iz bırakır: yalnız defter sıra no'su, sayfa, gerçek katılım ve oylar ile şifreli açıklama taşır; açıklama `ComplianceItem(SAPMA)`'ya yazılır; hiçbir bağlı akışı (harcama, koçan kaydı, görev bölümü, genel kurul çağrısı, bütçe) beslemez; Denetleme Kurulunun sapma listesine ve kapanış denetimine kendiliğinden düşer (denetim SU-11; §15 B-17). (defter, sıra no) tekil — sert. Sıra no ve sayfa defterdeki son kayıttan öneri olarak dolar; geri giderse ya da atlarsa uyarı. `DEFTERE_ISLENDI` sonrası metin ve oylar değişmez; düzeltme yeni kararla (`amends`) — sert (altın kural 4). `DEFTERE_ISLENDI` geçişi kapanmış dönemde de yapılabilir (O2) | OYS `BoardDecision` UYARLA: `is_draft` → `status`; defter, sıra no, sayfa, oylar, sakat karar izi ve bağlar eklenir (envanter S-11) |
| `AuditReport` | `term` · `kind` (`ARA` · `NIHAI`) · `report_date` · `checklist` (JSON; liste sürümü evrak kataloğundan) · `findings` (şifreli) · `irregularity_found` (rapor bayrağı) · `md6_violation_found` (DK'nin açık işareti: YK'nin [md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)'da sayılan görev ve yetkilere aykırı faaliyeti tespit edildi) · `escalated_assembly` → `GeneralAssembly` ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) olağanüstü çağrı) · `submitted_to_yk_on` (ara) · `submitted_to_assembly` → `GeneralAssembly` (nihai) · `status` (`TASLAK` → `DK_IMZALADI` → `SUNULDU`) | Yazan rol `denetleme_kurulu` (plan §1.8). Yılda en az iki inceleme ([md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) — uyarı. Bir `UYGUNSUZ` madde → `irregularity_found` (OYS mantığı AYNEN); bu bayrak yalnız raporu "gereği için" sunulan rapora çevirir. Olağanüstü genel kurul çağrısı önerisi ve `escalated_assembly` bağı yalnız `md6_violation_found` doğruyken açılır: md. 14/5 DK'ye çağrıyı md. 6'ya aykırı faaliyette verir; "usulsüzlük veya uygunsuzluk" müdürün [md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) yoludur (denetim MB-10) | OYS `AuditReport` UYARLA: liste tazelenir, KVKK'lı "adli sicil kayıtları alınmış mı" maddesi çıkar (S-20); md. 6 aykırılık alanı eklenir |
| `InspectionRecord` | OYS alanları aynen (konu, plan ve gerçekleşme tarihi, sonuç, rapor no, bulgular, izleme tarihi) | `follow_up_due` yardım metni düzeltilir: Genelge 2020/8'deki süreler ilçe ekibinin müdahale süresidir, düzeltme termini değildir | OYS AYNEN |

#### 5.2.5 Mali çekirdek (K1, T4)

Hesap planı T4'e göredir: banka, kasa, şartlı bağış alt hesabı; çift taraflı muhasebe yoktur, her kayıt tek hesaba
yazılır. Mali kayıtları (gelir-gider kaydı, banka içe aktarımı ve eşleme, makbuz yaprağı) **yalnız `muhasip`** yazar;
`yonetici` yalnız "TEFBİS'e girildi" işaretini koyar (kullanıcı kararı D2; §7.3).

**T4'e bir ek önerilir (§15 B-6):** `EMANET` alt hesabı — kiracıdan nakit alınan kesin teminat
([EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8))
ve birliğe yanlışlıkla yatırılıp aktarılacak paylar. Emanet birliğin geliri değildir: girişi ve iadesi
`EMANET_GIRIS` / `EMANET_CIKIS` yönlü kayıttır, TEFBİS listesine gelir ya da gider diye girmez (TEFBİS'teki karşılığı
DOĞRULANMADI). Kesin teminatın çıkışı fesih ya da sona erme hâline göre üç yoldan biridir (§7.6):

- **(a) Gelir kaydı** — kiracının fesih talebi, faaliyetini durdurması, yeri amacı dışında kullanması, taahhüdünü
  yerine getirmemesi, izin ve ruhsatlarının iptali ([md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22);
  [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22)
  2. paragraf): teminat `EMANET` karşı hesaplı gelir kaydına döner (banka hareketi doğmaz); cari dönem kirası tazminat
  olarak tahsil edilir (`ShareStatement`, `CEZA_TAZMINAT`).
- **(b) Mahsup ve iade** — mücbir sebep dışında iki ay üst üste ödememe feshi
  ([EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7)
  4. paragraf): birliğin alacağı kadar `EMANET` karşı hesaplı gelir kaydı, kalanı kiracıya iade (`EMANET_CIKIS`,
  banka hareketiyle eşlenir).
- **(c) İade** — sözleşmenin olağan sona ermesinde birliğin alacağı kalmamışsa
  ([EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8))
  ve kiracı [md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)'deki hâlde taahhüdünden vazgeçerse
  ("teminat geri verilir"); alacak varsa önce (b) gibi mahsup edilir.

md. 22/4'teki "taahhüdünü … yerine getirmemesi" ile EK-2 md. 7'nin ödememe hükmünün örtüşmesi, mahsup edilecek
"birliğin alacakları"nın kapsamı (birlik payı mı, il/ilçe payları ve arz da mı) ve
[md. 22/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) ile
[EK-2 md. 15](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-15)
fesihlerinde teminatın akıbeti yorum sorusudur (§15 B-14). Varsayılan: ödememe feshinde özel hüküm olan EK-2 md. 7
uygulanır; öteki fesihlerde yol kullanıcıca seçilir ve uyarı + gerekçe istenir.

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `BankAccount` | `bank_name` · `branch` · `iban` · `label` · `opened_on` · `is_active` · `import_profile` (JSON: sütun eşlemesi, §8.2) | IBAN mod-97 ve tekil — sert. IBAN açık tutulur (kurumsal hesap). İmza yetkilileri `OrganMembership`'ten okunur ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)); ayrı alan yok | YENİ |
| `BankStatement` | `bank_account` · `file_sha256` · `file_name` · `period_start`, `period_end` · `opening_balance`, `closing_balance` (dosyada varsa) · `row_count` · `imported_at`, `imported_by` · `status` (`ONIZLEME` → `UYGULANDI` → `GERI_ALINDI`) | Ham dosya saklanmaz. `GERI_ALINDI` yalnız hiçbir hareketi eşlenmemişse | YENİ (içe aktarım partisi) |
| `BankTransaction` | `bank_account` · `statement` · `booking_date` · `value_date` · `amount` (işaretli: + giriş, − çıkış) · `balance_after` · `reference` (dekont/işlem no) · `description` (şifreli) · `counterparty` (şifreli) · `fingerprint` · `void` | `fingerprint` anahtarlı özettir (HMAC; girdisi hesap + tarih + tutar + bakiye + referans + normalize açıklama; anahtarın bilgi dizgesi §2.3.1, DEK yenilemesinde yeniden hesap §4.4.4): şifreli açıklamanın düz özeti olsaydı ad listesiyle denenebilirdi. `void` olmayan satırlar arasında tekil — sert (çift aktarım; kısmi kısıt `condition: void = False`). Geri alınan partinin `void` satırları yeniden aktarımı engellemez (denetim UY-6). İçe aktarıldıktan sonra değişmez (K1) — sert. Kapanmış döneme düşen satır alınmaz — sert | YENİ |
| `LedgerAccount` | `kind` (`BANKA` · `KASA` · `SARTLI_BAGIS` · `EMANET`) · `name` · `bank_account` (`BANKA`'da) · `parent` (`SARTLI_BAGIS` ve `EMANET` paranın fiilen durduğu `BANKA` ya da `KASA` hesabı) · `purpose` (şifreli; şartlı bağışın şartı ve amacı) · `source_entry` → `LedgerEntry` (şartlı bağışın gelir kaydı) · `opened_on`, `closed_on` | `KASA`, `SARTLI_BAGIS`, `EMANET` bakiyesi eksiye düşemez — sert. Şartlı alt hesaptan gider amaç beyanı olmadan kaydedilmez — sert ([md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) | YENİ; OYS `BudgetCategory` yalnız sınıflamadır, hesap değildir |
| `LedgerEntry` | `term` · `entry_no` (dönem içi sıra; defter baskısının sıra no'su) · `date` · `direction` (`GELIR` · `GIDER` · `VIRMAN` · `EMANET_GIRIS` · `EMANET_CIKIS`) · `ledger_account` · `counter_account` (virmanda; emanetten gelire dönüşmede `EMANET`) · `amount` (> 0) · `in_kind` (ayni bağış; bakiyeye girmez) · `budget_category` · `tefbis_type` → `TefbisTypeMapping` (işlem tipi ve alt kalem) · `tefbis_source_type` (kaynak tipi; gelirde) · `activity_code` (faaliyet kodu) · `description` (şifreli) · `document_kind` (`MAKBUZ` · `ALINDI_BELGESI` · `DEKONT` · `FATURA` · `GIDER_PUSULASI` · `SOZLESME` · `DIGER`) · `document_no`, `document_date` · `decision` → `BoardDecision` · `expense_invoice` → `ExpenseInvoice` · `installment` → `ContractInstallment` · `share_statement` → `ShareStatement` · `event` → `SocialEvent` (etkinlik ve kampanya geliri ve gideri, §7.11) · `donor_name` (şifreli, isteğe bağlı) · `donor_tckn` (şifreli; yalnız `donor_tckn_enabled`) · `asset_slip_no` (varlık işlem fişi no; [TMY md. 16](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16), [TMY md. 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41)) · `status` (`TASLAK` → `KESIN`; `TASLAK`/`KESIN` → `IPTAL`) · `reversal_of` → `LedgerEntry` · `posted_book` → `OfficialBook`, `posted_page`, `posted_at`, `posting_batch` → `MarkBatch` (deftere geçirildi) · `tefbis_entered_at`, `tefbis_entered_by`, `tefbis_batch` → `MarkBatch` · `rule_warnings` | Yazan rol yalnız `muhasip`; işaretlerden "TEFBİS'e girildi"yi `yonetici` koyar (D2). `KESIN` kayıt değişmez — sert; tek istisna O2'deki işaret alanlarıdır. Tarih dönem aralığında — sert. Makbuzlu gelirde etkin yaprak bağı (`LeafUse`, §5.2.6) zorunlu ve yaprak tutarı = kayıt tutarı — sert; ters kaydın kendisi yaprak istemez. Virmanda iki hesap, aynı tutar — sert. Emanet yönlü kayıt yalnız `EMANET` hesabında; emanetten gelire dönüşme kaydı banka hareketi doğurmaz, eşleme aranmaz. `IPTAL` yalnız deftere geçmemiş ve TEFBİS'e girilmemiş kayıtta; öbür hâlde ters kayıt (§7.3) — sert. "TEFBİS'te düzeltilecek" listesi, `reversal_of`'u TEFBİS'e girilmiş bir kayda bağlı ters kayıtlardan hesaplanır; asıl kayda alan yazılmaz (kapanmış dönemin kaydı da değişmez kalır). Giderde karar bağı yoksa ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) ve kayıt döneminde bağışta ([md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15)) — uyarı | YENİ (ön değerlendirme §7.3 GelirKaydı ve GiderKaydı tek modelde) |
| `LedgerEntryLine` | `entry` · `line_no` · `description` · `quantity` · `unit` · `unit_price` · `amount` · `tefbis_subitem` | Satırlar toplamı = kayıt tutarı — sert. Tek satırlı kayıtta satır açılmaz | YENİ (TEFBİS detay satırı: işlem türü, miktar, birim, birim fiyat — 2009 kılavuzu) |
| `TransactionMatch` | `bank_transaction` · `ledger_entry` · `amount` · `matched_by`, `matched_at` · `status` (`ETKIN` · `COZULDU`) | Çoka çok. Bir hareketin ve bir kaydın etkin eşleşmeleri toplamı kendi tutarını aşamaz; yönler tutarlı (giriş ↔ gelir, emanet girişi ya da virmanın banka ayağı; çıkış ↔ gider ya da emanet iadesi) — sert. Eşleşme silinmez, `COZULDU` olur. `KASA` kaydı bankayla eşlenmez, yalnız kasa → banka virmanının banka ayağı eşlenir | YENİ |
| `OpeningBalance` | `term` · `ledger_account` · `amount` · `source` (`ONCEKI_DONEM_KAPANISI` · `GECIS_KURULUMU`) · `evidence_date` (ekstre tarihi: dönem başı ya da programa başlama günü, §7.9) · `tefbis_carryover` (TEFBİS "Devreden" ekranındaki tutar) · `difference_note` | (dönem, hesap) tekil; `ONCEKI_DONEM_KAPANISI` kapanışta otomatik yazılır ve değişmez — sert; `GECIS_KURULUMU` yalnız ilk dönemde, geçiş kurulumunda `muhasip` girer (§7.9) | YENİ (OYS `OabBudget.opening_balance` alanının yerine) |
| `MarkBatch` | `kind` (`DEFTERE_GECIRME` · `TEFBIS_GIRISI`) · `source` (`AYLIK` · `GECIS`) · `book` → `OfficialBook` (deftere geçirmede) · `first_page`, `last_page` · `document` → `GeneratedDocument` (E17 ya da E18 baskısı) · `entry_count` · `marked_by`, `marked_at` · `reverts` → `MarkBatch` (yanlış toplu işaretin geri alınması yeni satırdır) | Toplu işaret: E17 tasdikli defterin sayfa düzeninde basılır (sayfa başına satır `OfficialBook.lines_per_page`); "bu baskı X defterinin a-b sayfalarına geçirildi" tek işlemi baskıdaki her kaydın `posted_page`'ini satır sırasından yazar. TEFBİS toplu işareti E18'in satır sırasıyla çalışır; yalnız `KESIN` kayıtlar girer. Deftere geçirmeyi `muhasip`, TEFBİS işaretini `yonetici` yapar. Kapanmış dönemde de yazılır (O2). Geçiş kurulumunda defterde ve TEFBİS'te zaten bulunan aylar `source = GECIS` ile topluca işaretlenir (§7.9) | YENİ (denetim SU-7) |
| `TefbisTypeMapping` | `kind` (`ISLEM_TIPI` · `KAYNAK_TIPI` · `FAALIYET_KODU`) · `direction` (`GELIR` · `GIDER` · boş) · `group_label` (ör. "Bağışlar, Yardımlar") · `type_label` · `subitem_label` · `source` (`EK_A_2009` · `OKUL_EKRANI`) · `is_active` · `valid_from` · `replaced_by` | Kullanılmış satır silinmez, pasifleşir. Okul kendi TEFBİS ekranındaki listeyi girer (K6; F0-e d). Tohum: [2009 kılavuzu EK-A](../kesif/kaynaklar/tefbis-2009-kilavuz-ek-a-islem-tipleri.txt) üç düzeyiyle; kaynak tipinin yedi üst sınıfı | YENİ (ön değerlendirme §7.3 TEFBİSEşleme; OYS'nin atıfsız kategori tohumunun yerine EK-A, envanter §4.1 satır 58) |
| `TefbisStatement`, `TefbisStatementLine` | Parti: `period_start`, `period_end`, `file_sha256`, `row_count`, `status`. Satır: `date` · `direction` · `type_label` · `description` (şifreli) · `document_no`, `document_date` · `amount` · `decision_no` · `matched_entry` → `LedgerEntry` | T.C. kimlik no ve ad-soyad sütunları okunmaz (§8.3). Sürüm 2 (M12, F8+); şema şimdi sabitlenir | YENİ (OYS `TefbisImport` ALMA) |

**Bakiye ve mutabakat değişmezleri.** (1) Banka hesabının son içe aktarılan bakiyesi = `BANKA` + o bankaya bağlı
`SARTLI_BAGIS` ve `EMANET` hesaplarının eşlenmiş kayıt bakiyesi; fark mutabakat listesine düşer. (2) `KASA`,
`SARTLI_BAGIS`, `EMANET` eksiye düşmez. (3) Ayni bağış (`in_kind`) hiçbir nakit bakiyesine girmez; yalnız TEFBİS
listesinde ve raporlarda görünür. (4) Dönem kapanış bakiyesi sonraki dönemin `OpeningBalance`'ıdır. (5) Emanetten
gelire dönüşme `BANKA`'yı artırır, `EMANET`'i azaltır; (1)'deki toplam değişmez.

#### 5.2.6 Makbuz koçanı (K5)

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `ReceiptBookRegistry` | `kind` (`BAGIS_ALINDI_BELGESI` ([EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1)) · `GELIR_GIDER_MAKBUZU` · `DIGER`) · `series` · `volume_no` (cilt) · `first_leaf`, `last_leaf` · `printed_by` (matbaa) · `received_on` · `sealed_on` (kurum mührü) · `registration_decision` → `BoardDecision` (koçan seri numaralarıyla karar defterine kayıt) · `certified_by` (`IL_ILCE_MEM` · boş), `certified_on`, `certification_no` (isteğe bağlı tasdik kaydı) · `holder_role` · `status` (`ENVANTERDE` → `KAYITLI` → `KULLANIMDA` → `BITTI` → `ARSIVDE`; `IPTAL`) · `finished_on` · `rule_warnings` | (tür, seri, cilt) tekil; aynı serideki yaprak aralıkları çakışmaz — sert (numara tekilliği). 50 asıl + 50 koçan değilse ([md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) ve mühür ya da karar kaydı olmadan kullanımda ([md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) — uyarı. Koçan [md. 23/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)'deki belgelerdendir, biten koçan okulda saklanır ([md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)'deki il/ilçe MEM tasdikine girip girmediği yorum sorusudur (§15 B-15): tasdik alanları boşken yalnız bilgi. **Dönem alanı yoktur:** koçan birlikle yaşar, dönemden döneme devredilir | OYS `ReceiptBookRegistry` UYARLA: `term` FK kalkar; seri-cilt-sıra, mühür, karar bağı, tasdik ve durumlar eklenir |
| `ReceiptLeaf` | `book` · `leaf_no` · `status` (`BOS` → `KULLANILDI` → `IPTAL`; `BOS` → `IPTAL` · `KAYIP`; `GECIS_ONCESI`) · `used_on` · `cancel_reason` (şifreli) | (koçan, yaprak no) tekil ve aralık içinde — sert. `IPTAL` ve `KAYIP` geri alınamaz — sert. `KULLANILDI → IPTAL`: kâğıtta sonradan iptal edilen kullanılmış yaprak; gerekçe zorunlu; bağlı kayıt `TASLAK` ise `IPTAL`, `KESIN` ise ters kayda zorlanır — sert (koçan envanteri ve TKB Tablo 4 doğru kalır). `GECIS_ONCESI`: geçiş kurulumunda programdan önce kullanılmış yapraklar; kayıt bağı aranmaz (§7.9). Kendinden önce `BOS` yaprak bırakarak kullanım — uyarı. Koçan envantere girince yaprakları topluca `BOS` açılır | YENİ |
| `LeafUse` | `leaf` → `ReceiptLeaf` · `ledger_entry` → `LedgerEntry` · `status` (`ETKIN` · `COZULDU`) · `created_by`, `created_at`, `resolved_at` | Bir yaprağın ve bir kaydın en çok bir `ETKIN` bağı — sert (bir yaprak bir kayda). Ters kayıt eski bağı `COZULDU` yapar; düzeltilmiş kayıt aynı yaprağa yeni bağla bağlanır; bağ silinmez (`TransactionMatch` deseni). Yaprak–kayıt bağının tek kaynağı budur (O6) | YENİ (denetim UY-7) |

Program makbuz basmaz (K5); elektronik ortamda basılan belge [md. 16/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)'ya göre ayrı bir güvenlik işidir, ilk sürümde
yoktur.

#### 5.2.7 Harcama, bütçe, duyuru, bildirim, uyum

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `ExpenseFile` | `term` · `file_no` · `title` (şifreli) · `kind` (`MAL` · `HIZMET` · `ONARIM` · `SUREKLI_ODEME` · `OGRENCI_YARDIMI` · `AKTARIM` · `DIGER`) · `path` (`TAM_ZINCIR` · `KISA_YOL` — sınırın altında ve genel karar kapsamındaki küçük alım, §7.4) · `request_kind` (`OKUL_YAZILI_TALEBI` · `YK_RESEN` · `GENEL_KARAR`) · `request_record` → `DocumentRecord` · `request_document` → `GeneratedDocument` (müdürün yazdığı talep) · `request_date` · `estimated_amount` · `decision` → `BoardDecision` · `standing_decision` → `BoardDecision` · `supplier_name` (şifreli) · `supplier_tax_no` (yalnız tüzel ve ticari VKN; gerçek kişide tutulmaz) · `request_reason` (şifreli; talep gerekçesi, E25) · `delivered_on`, `received_by` → `OabPerson` (çoğul), `delivery_note` (şifreli) (teslim ve muayene, E26) · `payee_is_member` (hesaplanır) · `status` (§7.4) · `rule_warnings` | `ODENDI` koşulu: dosyanın faturalarına bağlı `KESIN` gider kayıtlarının toplamı fatura tutarlarına eşit ve her kayıt ya bankayla tam eşli ya da `KASA` kaydı (kasa yolu [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) uyarı + gerekçe) — sert (denetim UY-9). Öteki halkalar (talep, karar, en az üç kişilik komisyon, VİF, müşterek imza, organ üyesine ödeme) uyarı + gerekçedir (§7.4). Alım komisyonu ayrı kişi listesi olarak tutulmaz: tek kaynak `OrganMembership(ALIM_KOMISYONU)`'dur (O6). Ödeme alıcısının IBAN'ı tutulmaz (veri en aza); ödeme talimatında (E27) elle yazılır. **Sürekli ödeme** (R6): dönem başı YK genel kararına bağlı tek dosya, çok ödeme (aylık hizmet alımı, bakım, lisans, banka masrafı); talep, karar ve komisyon bir kez girilir, her dönemde yalnız fatura ve ödeme; dosya dönem sonunda ya da sözleşme bitince `KAPANDI`, yeni dönemde yeni genel kararla yeni dosya açılır | YENİ (ön değerlendirme M6) |
| `ExpenseFileLine` | `expense_file` · `line_no` · `description` · `quantity` · `unit` · `estimated_amount` | Talep kalemleri (E25, E26); toplam `ExpenseFile.estimated_amount`'a eşit değilse uyarı | YENİ (denetim EK-12) |
| `ExpenseQuote` | `expense_file` · `supplier_name` (şifreli) · `supplier_tax_no` (yalnız tüzel) · `amount` · `quoted_on` · `selected` | Piyasa araştırması teklifleri (alım komisyonu tutanağı E26); en çok bir `selected` — sert (tek kaynak) | YENİ (denetim EK-12) |
| `ExpenseInvoice` | `expense_file` · `period` (sürekli ödemede yıl-ay) · `document_kind` (`FATURA` · `GIDER_PUSULASI` · `DIGER`) · `document_no`, `document_date`, `amount` · `withholding_amount` (bilgi) · `asset_slip_no` (VİF; [md. 18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) · `payment_order` → `GeneratedDocument` (banka ödeme talimatı ya da kasa çıkış tutanağı) · `status` (`BEKLIYOR` → `ODEME_TALIMATI` → `ODENDI`; `IPTAL`) | Bir dosyada 1—n. Avans ve kalan gibi iki ödemeli alım iki gider kaydıyla aynı faturaya bağlanır. Ödeme bağı tek yönlüdür: `LedgerEntry.expense_invoice` (O6); dosyada ödeme kaydı alanı yoktur | YENİ (denetim SU-2, UY-9) |
| `BudgetCategory` | `code` · `name` · `kind` (`GELIR` · `GIDER`) · `order` · `is_active` · `default_tefbis_type` → `TefbisTypeMapping` · `requires_expense_file` | Kod tekil. "Huzur hakkı" ya da benzeri kategori yoktur ([md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25)) — tanımlanamaz. Vergi, MEM payı aktarımı, arz bedeli gibi kategorilerde `requires_expense_file` kapalıdır; banka masrafı dönemin genel kararına bağlı sürekli ödeme dosyasına bağlanır (R6) | OYS UYARLA: tohum TEFBİS EK-A üst gruplarından (OYS'nin atıfsız 5+8 tohumu yerine) |
| `OabBudget` | `term` (bütçenin uygulanacağı dönem: olağan genel kurulda görüşülen bütçe yeni, `HAZIRLIK` dönemine yazılır) · `prepared_decision` → `BoardDecision` ([md. 13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · `discussed_at` → `GeneralAssembly` ([md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11)) · `announcement` → `Announcement` · `status` (`TASLAK` → `YK_HAZIRLADI` → `GK_GORUSULDU` → `DUYURULDU`; `TASLAK` · `YK_HAZIRLADI` → `IPTAL`) · `notes` | Dönem başına bir iptal olmayan bütçe. "Onaylandı" yerine "genel kurulda görüşüldü" | OYS UYARLA: `opening_balance` kalkar (→ `OpeningBalance`); `ONAYLANDI` adı değişir; iptal eklenir |
| `BudgetLine` | `budget` · `category` · `estimated_amount` · `notes` · `is_cancelled` (+ gerekçe, kim) | (bütçe, kategori) iptal olmayanlarda tekil; tutar ≥ 0. Gerçekleşen kayıtlardan hesaplanır, alan yoktur | OYS UYARLA: `realized_amount` (K1) ve `realized_from_payroll` (K3) kalkar |
| `Announcement` | `term` · `kind` (`GK_CAGRISI` · `OLAGANUSTU_GK_CAGRISI` · `BUTCE` · `GELIR_GIDER_DONEMLIK` · `SERVIS_ISI_ILANI` · `TASIMACI_LISTESI` · `DIGER`) · `subject_type`, `subject_id` (genel kurul, bütçe, ders dönemi, tespit süreci) · `school_term` → `SchoolTerm` · `distributed_written_on` (elden yazılı) · `posted_board_on`, `removed_board_on` · `published_web_on` · `evidence` → `Attachment` (çoğul) · `content` → `GeneratedDocument` · `status` (`TASLAK` → `YAYIMLANDI` → `KALDIRILDI`) | İçerikte kişi adı yoktur (altın kural 5); üretici kurgusu gereği ad koymaz. **Tek istisna `TASIMACI_LISTESI`:** [Servis U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) gereği taşımacının ad/unvanı, plaka ve güzergâh basılır; telefon, adres, T.C. kimlik no basılmaz; `removed_board_on` gelince okul sitesindeki kopyanın kaldırılması panoda hatırlatılır (kullanıcı kararı D5). Web metni HTML dosyasıdır; program yayımlamaz, okul sitesine kullanıcı taşır (çevrimdışı) | YENİ (OYS `ComplianceEntry` `PANO_WEB_ILAN` türünün yerine) |
| `MonthlyReport` | `term` · `year`, `month` · `cutoff_date` (kesim: bu tarihe kadar içe aktarılan hareketler ve girilen kayıtlar) · `snapshot` (JSON: gelirler, bağışlar, kararla yapılan harcamalar; "önceki aylara ait geç kayıtlar" bölümü; kayıtlardan) · `document` → `GeneratedDocument` · `signed_on` · `delivered_on` · `outgoing_record` → `DocumentRecord` · `status` (`TASLAK` → `TESLIM_EDILDI`) | (dönem, yıl, ay) tekil. Ay sonunda teslim ([md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) — uyarı. Teslim edilen bildirim değişmez: `TESLIM_EDILDI`'den sonra o aya tarihli yeni kayıt, sonraki ayın bildiriminde "önceki aylara ait geç kayıtlar" bölümüne girer (denetim SU-8). Bağışçı adları varsayılan olarak dökümde yoktur (toplamlar) | YENİ (OYS `MUDURE_BILDIRIM` türünün yerine) |
| `ComplianceItem` | `term` · `kind` (`SAPMA` · `EKSIK` · `TAKVIM`) · **sapma ve eksikte:** `subject_type`, `subject_id`, `rule_id`, `rule_package`, `rev`, `message`, `justification_group` → `ComplianceJustification` (sapmada zorunlu), `resolved_at` · **takvimde:** `obligation` (`DEFTER_TASDIK` · `DK_INCELEME` · `MEM_DENETIMI` · `KANTIN_FAALIYET_BELGESI` · `KANTIN_CALISAN_BELGE_YENILEME` · `TUFE_BILDIRIMI` · `MILLI_EMLAK_BILDIRIMI` · `IBRA_EDILMEDI_BILDIRIMI` · `TEFBIS_YONETIM_BILGISI` · `TEFBIS_BANKA_BILGISI` · `TEFBIS_BUTCE_GIRISI` · `DIGER`), `due_date`, `done_on`, `evidence` → `Attachment`, `responsible_role` | Satır silinmez. `EKSIK` bilgi girilince `resolved_at` ile kapanır; kapatıcı geçişte hâlâ açıksa `SAPMA`'ya döner ve gerekçe ister (O3). Sapma, kayıt düzeltilip uyarı kalkınca `resolved_at` alır. Genel kuruldan sonra okul idaresinin TEFBİS'e yeni yönetimi, banka hesap bilgilerini ve tahmini bütçeyi girmesi `TAKVIM` satırıdır (dayanak [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); süre yalnız rehberde — GNL-OAB-RH-001 "genel kuruldan hemen sonra" — kural paketine girmez, §7.1). Genel kurul son günü, YK aylık toplantısı, aylık bildirim, dönemlik duyuru, arz vadesi gibi süreler kendi modellerinden pano ve takvime hesaplanır, buraya kopyalanmaz (§7.10) | OYS `ComplianceEntry` UYARLA ve yeniden adlandırma: dört türü başka modellere dağılır (envanter §2.2); OYS'nin model başına uyarı alanları buraya toplanır (O3); serbest metin `responsible` → rol |
| `SocialEvent` | `term` · `kind` (`ETKINLIK` · `KAMPANYA`) · `name` · `organizer` (`BIRLIK` · `UCUNCU_KISI`; kural paketinin `etkinlik.duzenleyen` koşulu) · `starts_at`, `ends_at` · `responsible_member` → `OrganMembership` (sorumlu YK üyesi) · `decision` → `BoardDecision` · `sek_review_on`, `sek_review_no` (sosyal etkinlikler kurulu incelemesi) · `principal_opinion_on`, `principal_opinion_record` → `DocumentRecord` (müdürün uygunluk görüşü, kâğıtta) · `mem_approval_on`, `mem_approval_no` (il/ilçe MEM onayı) · `not_in_ministry_project` ("Bakanlık proje/protokolü kapsamında değil" beyanı) · `notes` (şifreli) · `status` (`TASLAK` → `ONAYDA` → `ONAYLANDI` → `YAPILDI` → `KAPANDI`; `YAPILDI` öncesinden `IPTAL`) · `rule_warnings` | Onay zincirinin boş aşaması uyarı (`etkinlik.onay_zinciri`); üçüncü kişi etkinliği ders saatinde uyarı (`etkinlik.ders_saatleri_disinda`); beyan yokken ücret geliri uyarı (`gelir.proje_protokol_ucret_yasak`). Gelir ve gider kayıtları `LedgerEntry.event` ile bağlanır; toplamlar hesaplanır, alan yoktur (§7.11) | YENİ (denetim EK-9; [md. 6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [15/1-c, 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15)) |
| `ComplianceJustification` | `rule_id` · `root_cause` (kök neden anahtarı: bir defterin tasdik kaydı, geçiş kurulumunun sayaç beyanı, bir genel kararın no'su gibi) · `text` (şifreli) · `template` (seçilebilir kalıbın kimliği) · `justified_by`, `justified_at` | Aynı kural ve aynı kök neden için tek gerekçe birden çok `SAPMA` satırına bağlanır (toplu gerekçe, R5); bağlanan her satır denetim izine yazılır | YENİ |

#### 5.2.8 Defterler, evrak, dosyalar, devir

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `OfficialBook` | `kind` (`KARAR_DEFTERI` · `GELIR_GIDER_DEFTERI` · `GELEN_GIDEN_EVRAK_DEFTERI` · `DIGER`) · `certified_by` (`NOTER` · `IL_ILCE_MEM`) · `certified_on` · `certification_no` · `page_count` · `lines_per_page` (gelir-gider defterinde sayfa başına satır; E17 baskısı ve toplu işaret) · `last_no_before_program`, `last_page_before_program` (geçiş kurulumunda defterdeki son sıra no ve sayfa, §7.9) · `opened_on`, `closed_on` · `status` (`KULLANIMDA` · `DOLDU` · `ARSIVDE`) | Karar defteri noterce, diğerleri il/ilçe MEM'ce tasdik edilir ([md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); tasdik kaydı yokken ya da yanlış makamla kullanım — uyarı (defter başına bir toplu gerekçe, O3). Dönemsizdir, devredilir | YENİ (ön değerlendirme §2.2 "Defterler", [md. 23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| `DocumentRecord` | `book` → `OfficialBook` (gelen-giden) · `direction` (`GELEN` · `GIDEN`) · `year` · `record_no` · `date` · `counterparty` (şifreli) · `subject` (şifreli) · `external_ref` (karşı tarafın ya da EBYS sayısı) · `generated_document` → `GeneratedDocument` (giden yazının programdaki karşılığı) · `attachments` → `Attachment` · `term` | (defter, yıl, kayıt no) tekil — sert. Sıra atlama uyarı | YENİ — ADR-0028'deki `OabDocumentRecord`'un karşılığı; OYS'de hiç yazılmamıştı (envanter §0-9) |
| `GeneratedDocument` | `doc_type` (evrak kataloğu kimliği, §9) · `subject_type`, `subject_id` · `term` · `version` · `formats` (`DOCX` · `PDF` · `XLSX` · `HTML`) · `content_sha256` (tek içerik modelinin kanonik JSON özeti, §9.1) · `content_json` (şifreli; içerik modelinin her üretimde saklanan kanonik JSON'u — yeniden basım bundan çizilir, §6.2-6) · `files` → `Attachment` · `personal_list` (katalogdan; veli adı taşıyan belge: E07 sınıf teslim çizelgesi, adlı E08 katılım cetveli) · `row_count` · `rule_package` · `generated_at`, `generated_by` · `wet_signed_on` (ıslak imzalandı işareti) · `status` (`GECERLI` · `YERINI_ALDI`) | Aynı nesne için yeniden üretim yeni sürüm satırıdır; eski satır silinmez; kapanmış dönemde de yazılabilir (O2) ve aynı `content_sha256`'yı vermelidir (§6.2-6). Dosya imha edilse de tür, tarih ve özet kalır (Kütüphane `BelgeIzi` kalıbı). **Veli adı taşıyan belge (R9):** yalnız `yonetici` üretir; program dosyasını ve `content_json`'unu saklamaz — `files` ve `content_json` boş kalır, satırda tür, tarih, satır sayısı ve sha256 durur; dosya kullanıcının kaydettiği yerde, basılı ve imzalı aslı genel kurul tutanak dosyasındadır ([md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Bu belgeler veli listesi silindikten sonra yeniden basılmaz, arşiv paketine girmez; "kapanmış dönemde aynı özet" vaadi bunlar için geçerli değildir. Hesap teslim pusulasının (E63) dosyası saklanmaz, yalnız `content_json`'u | YENİ |
| `Attachment` | `stored_name` (uuid) · `original_name` (şifreli) · `key_wrap` (dosya anahtarı sarmalı, §4.4.4) · `sha256` · `mime` · `size` · `sensitivity` (`NORMAL` · `OZEL_NITELIKLI`) · `retention_until` · `owner_type`, `owner_id` · `uploaded_by`, `uploaded_at` · `purged_at` | Dosya `dosyalar/<stored_name>`'de dosya başına anahtarla şifreli durur (§4.4.4). İçe aktarılan ham dosya diske yazılmadan bellekte okunur. Kabul: PDF, JPEG, PNG; tür imza baytından denetlenir (libmagic yok). İmha edilen dosyanın satırı `purged_at` ile kalır | OYS `file_storage.py` UYARLA (sha256, uuid adı, boyut sınırı AYNEN; libmagic ve yalnız-PDF kalkar) |
| `Handover` | `from_term`, `to_term` · `assembly` → `GeneralAssembly` · `date` · `handed_by`, `received_by` (→ `OabPerson`, çoğul) · `cash_count` (kasa sayımı) · `bank_balance`, `bank_balance_on` · `document` → `GeneratedDocument` · `status` (`TASLAK` → `BASILDI` → `IMZALANDI`) | Kasa sayımı ≠ `KASA` bakiyesi ise uyarı; düzeltme kaydını `muhasip` girer (D2). Banka bakiyesiyle defter bakiyesinin devir günündeki farkı bilgidir (aylık kayıt düzeninde her yıl çıkar; denklik kapanışta sert denetlenir, §7.8). Olağanüstü genel kurulda `from_term` = `to_term` (ara devir) | YENİ ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10); saha 9: devir tutanağı yok) |
| `HandoverItem` | `handover` · `kind` (`DEFTER` · `KOCAN` · `DOSYA` · `BANKA_YETKISI` · `PROGRAM_HESABI` · `KURTARMA_ZARFI` · `ACIK_IS` · `DIGER`) · `ref_type`, `ref_id` · `description` · `state` (`TESLIM_EDILDI` · `EKSIK` · `SONRA_TESLIM`) · `note` (şifreli) | Kalemler kayıtlardan otomatik önerilir (§7.8); elle eklenebilir. `KURTARMA_ZARFI` kalemi yalnız "kurtarma anahtarı zarfı okul müdürlüğünde, mührü sağlam" kaydıdır; zarf devredilmez, veliye geçmez (kullanıcı kararı D3) | YENİ |

#### 5.2.9 Kantin ve servis (K4)

Program bu iki süreçte birliğin ve okulun evrakını hazırlar ve takibini yapar; komisyon kararının yerine geçmez (K4,
ön değerlendirme §2.3). Servis tarafında model adları OYS'deki gibi kalır, arayüz ve evrak "taşımacının tespiti",
"başvuru", "değerlendirme" der (altın kural 6).

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `RentableAsset` | `name` · `asset_kind` (`KANTIN` · `SPOR_SALONU` · `KONFERANS_SALONU` · `OTOPARK` · `ACIK_ALAN` · `DIGER`) · `area_m2` · `full_year` (tam yıl işletilen yerde 12 ay, [md. 19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19); işletilmeyen yerde dokuz ay, [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) · `short_term_rates` (saatlik, günlük, haftalık; [md. 19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) + `rates_document` → `DocumentRecord` · `is_active` | Ad tekil | OYS UYARLA: `SERVIS_GUZERGAHI` çıkar; tam yıl ve kısa süreli kullandırma eklenir |
| `Tender` | `kind` (`KANTIN_KIRALAMA` · `SERVIS_TESPIT`) · `route` (kantinde `YENIDEN_KIRALAMA` ([Genelge 2024/35 I](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i)) · `IHALE` ([Genelge 2024/35 II](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii), [Genelge 2024/35 I-7](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-7))) · `evaluation_method` (kantinde `PAZARLIK` ([2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51)); serviste `KOMISYON_DEGERLENDIRMESI` ([Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), varsayılan) · `EK3_PUANLAMA` ([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8))) · `ek3_reason` (`ITIRAZ` · `YENI_OKUL`) · `asset` · `term` · `status` (§7.6, §7.7) · ilan, başvuru, değerlendirme, karar, onay, tebliğ tarihleri · `estimated_price` (yalnız kantin, [md. 19](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) · `incumbent_request_on`, `incumbent_reply_on`, `offer_to_incumbent_on`, `incumbent_accepted` (yeniden kiralama, [Genelge 2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2), [Genelge 2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3), [Genelge 2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5), [Genelge 2024/35 I-6](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-6)) · `rule_warnings` | `KESINLESTI` sonrası değişmez (OYS kilidi AYNEN, altın kural 4 ile genelleşir). Onay (`OLUR`) kaydı olmadan `KESINLESTI`: **serviste sert** ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); §7.7); **kantinde uyarı + gerekçe** — dayanak korpusta doğrulanamadı, onay makamı ve tarihi kaydedilir (kullanıcı kararı D4; §7.6). `winner` alanı yoktur: seçilenler `Bidder.selected` ile (serviste birden çok taşımacı, §15 A-6) | OYS `Tender` UYARLA: iki süreç ayrılır; `EN_DUSUK_TEKLIF` çıkar; serviste varsayılan yöntem ters çevrilir (S-7); servis etiketleri "ihale", "teklif toplama" demez |
| `TenderCommissionMember` | OYS alanları + `appointed_via` (belirlenme kanalı: `KENDILIGINDEN_MUDUR` · `KENDILIGINDEN_BIRLIK_BASKANI` · `OGRETMENLER_KURULU_AD_CEKME` · `OKUL_IDARESI_VELI` · `VAKIF_TEMSILCISI`; görevlendirme yazısı E73) · `vote` (`KABUL` · `RET`; çekimser yok) · `dissent` (şifreli; muhalif şerhi) · `seat_type` (yedekler) | Serviste çoğunluk, eşitlikte başkanın tarafı, çekimser yok — sonuç programca hesaplanır (sert); muhalif üye gerekçe yazar, şerh boşsa uyarı ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4); D1) | OYS UYARLA |
| `TenderApproval` | `tender` · `order` · `authority` · `decision` (`BEKLIYOR` · `UYGUN_GORUS` · `OLUR` · `RED`) · `requested_on` · `decided_on` · `document_no`, `document_date` | Serviste mülki amir ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8)). Kantinde onay makamı korpusta bulunamadı (2886'nın kısmi dosyasında onay hükmü yok) — DOĞRULANMADI; makam ve tarih kullanıcıca girilir, kayıt yoksa kesinleşme uyarı + gerekçedir (`kantin.kiralama_onay_kaydi`, `dayanak_turu: kullanici_karari`; D4) | OYS UYARLA |
| `Bidder` | `tender` · `bidder_type` (`GERCEK` · `TUZEL`) · `legal_name` (şifreli) · `tax_number` (yalnız tüzel) · `trade_registry_no` · `contact_address`, `contact_phone`, `contact_email` (şifreli) · `bid_amount` (yalnız kantin) · `incumbent` · `participation_bar` (`YOK` · `VAR`) · `participation_bar_basis` (şifreli, hassasiyet `OZEL_NITELIKLI`: `HISIMLIK_20_8` · `SUC_20_11`; okuması erişim günlüğüne) · `is_disqualified` · `disqualified_reason` (kapalı liste: `BELGE_EKSIK` · `KATILIM_ENGELI` · `YASAKLI_22_5` · `DIGER`) · `disqualified_note` (şifreli; ekranda "adli sicil içeriği yazılmaz" uyarısı) · `selected` · `rule_warnings` | Kantinde `participation_bar = VAR` olan istekli seçilemez — sert (hukuken geçersiz katılım; [md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)). Engelin hangi bentten geldiği açık alanda tutulmaz: suç engeli ceza mahkûmiyeti verisidir ([KVKK md. 6/1](../mevzuat/6698-kvkk.md#madde-6); §3.4, §15 B-16). Belge eksikliği ([md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) — uyarı + gerekçe (plan §1.8). İletişim bilgisi ve engel dayanağı §5.4'e göre boşaltılır | OYS UYARLA: `person` FK kalkar (istekli birlik üyesi değildir); gerçek kişide vergi no (= T.C. kimlik no) tutulmaz (K9 çizgisi); `crime_bar` ve `kinship_bar` tek açık alanda birleşir, dayanak şifrelenir |
| `BidderDocument` | `bidder` · `document_type` (OYS'nin 21 türü) · `subject` (`ISTEKLI` · `KIRACI` · `CALISAN` · `SOFOR` · `REHBER` · `ARAC`) · `subject_name` (şifreli) · `seen_on` · `valid_until` · `is_present` · `attachment` → `Attachment` (isteğe bağlı) · `sensitivity` | İhale aşamasında portör ve adli sicil istekli belgesi değildir ([md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); envanter S-8). Sözleşmeden sonra kiracının ve çalışanlarının portör, adli sicil ve hijyen belgeleri izlenir ([md. 20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); kiracı kantini bizzat çalıştırır, [EK-2 md. 9](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-9); [HEY md. 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5)). Yıllık yenileme ve servis belgeleri ([Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9)) `valid_until` ile izlenir. Varsayılan: tarama alınmaz (§5.4) | OYS UYARLA: kiracı öznesi eklenir |
| `ScoringCriterion`, `BidderScore` | OYS alanları aynen | Kademeler [Servis EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) ile birebir; tohum kural paketine taşınır. Kademe dışı puan uyarı + gerekçe (plan §1.8; D1: girilen değer; OYS'de sertti) | OYS AYNEN (model) |
| `OabContract` | `kind` (`KANTIN_KIRA` · `SERVIS`) · `tender` · `contractor` → `Bidder` · `asset` · `term` (imzalandığı dönem) · `renewal_of` · `twenty_year_base_date` ([Genelge 2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii)) · `frozen_days` ([EK-2 md. 21](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-21)) · `pandemic_days_applied` (540 gün, [Genelge 2024/35 III-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-4)) · `status` (`TASLAK` → `IMZALANDI` → `YURURLUKTE` → `SONA_ERDI` · `FESHEDILDI`; `TASLAK` → `IPTAL`) · `decision_notified_on` · `signed_on` · `start_date`, `end_date` · `site_handover_on` · `milli_emlak_sent_on` · `months_per_year` (9 · 12) · `monthly_rent`, `annual_rent`, `base_amount` · `annual_adjustments` (JSON: yıl, TÜFE, yeni bedel, bildirim tarihi) · serviste `route_description` (güzergâh) ve `vehicle_plates` (sözleşmedeki araç plakaları; taşımacı ilanı E56'nın kaynağı, D5) · `guarantee_kind` (`NAKIT` · `TEMINAT_MEKTUBU` · `YOK`) · `guarantee_amount` · `guarantee_disposition` (`IADE` · `MAHSUP_VE_IADE` · `GELIR`; fesihte ve sona ermede, §5.2.5) · `termination_ground` (fesihte dayanak hâli) · `special_terms` (şifreli; Özel Şartlar md. 2 metni, §7.6) · `student_count_at_signing` · `share_split_snapshot` (oranlar ve yerleşim türü) · serviste `academic_years` · `fee_installments_max` · `free_needy_students` (sayı) · `rule_warnings` | (süreç, yüklenici) `IPTAL` olmayanlarda tekil (OYS'nin "süreç başına tek sözleşme" kısıtı kalkar, S-16). Yer teslimi imzadan önce olamaz ([md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) — **uyarı + gerekçe**: teslim tarihi belgeden girilen değerdir (D1; `kira.yer_teslimi_gun`). Kesin teminat, ay sayısı ve TÜFE artışı programın önerisinden saparsa uyarı + gerekçe (D1). `IMZALANDI` sonrası tutarlar değişmez; TÜFE artışı `annual_adjustments`'a yeni satırdır | OYS UYARLA: kantin için [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) alanları, 20 yıl hesabı, teminat türü ve akıbeti, özel şart; durum geçişleri yazılır (S-11) |
| `ContractInstallment` | `contract` (yalnız kantin) · `period` (yıl-ay) · `due_from`, `due_to` (ayın 5-15'i, [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) · `rent_amount` · `arz_amount` · `il_amount`, `ilce_amount`, `birlik_amount` · `force_majeure_reduction` · `status` (`BEKLIYOR` → `BIRLIK_PAYI_ALINDI` → `DEKONTLAR_TAMAM`; `IPTAL`) · `birlik_entry` → `LedgerEntry` · `il_receipt_seen_on`, `ilce_receipt_seen_on` | (sözleşme, dönem) tekil. Pay hesabı kuruş korunumlu — sert. Serviste üretilmez: ücreti veli taşımacıya öder ([Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6); §15 A-5) | OYS UYARLA: anlamı kantin aylık kira takvimine döner; 1-9 taksit kısıtı kalkar |
| `ShareStatement` | `contract` ya da `asset` · `mode` (`KIRAYA_VERME` · `ISLETME` · `KISA_SURELI_KULLANIM` · `CEZA_TAZMINAT`) · `payer` (`KIRACI` · `BIRLIK`) · `year`, `period` (Q1-Q4) · `gross_amount` · `arz_rate`, `arz_amount` · `expenses` (işletmede) · `net_amount` · `il_amount`, `ilce_amount`, `birlik_amount` · `settlement_type_snapshot` · `due_contract` (izleyen ayın 10'u, [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7)) · `due_regulation` (izleyen ayın 20'si, [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) · `paid_on` · `evidence` → `Attachment` · `late_status` (`ZAMANINDA` · `SOZLESME_VADESI_GECTI` · `YONETMELIK_SURESI_GECTI`) | (sözleşme ya da yer, tür, yıl, dönem) tekil — OYS kısıtına yer eklendi (S-16). Çeyrek başlangıcı DOĞRULANMADI; varsayılan takvim çeyreği (§6.4.11-2). Gecikme zammı hesaplanmaz: [md. 17/1-b-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) 6183 md. 51'e gönderir, o metin korpusta yok; yalnız bilgi notu | OYS UYARLA: `is_metropolitan` → yerleşim türü; iki vade; kısa süreli kullanım ve ceza-tazminat türleri ([md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) |
| `IndexRate` | OYS alanları aynen | `value` = "TÜFE on iki aylık ortalamalara göre yüzde değişim" ([md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) diye sabitlenir | OYS AYNEN |

#### 5.2.10 İlişki özeti

- `OabTerm` 1—n `GeneralAssembly`, `BoardMeeting`, `OrganMembership`, `LedgerEntry`, `ExpenseFile`, `MonthlyReport`,
  `Announcement`, `ComplianceItem`, `AuditReport`; 1—1 `OabBudget`; n—1 `RulePackage`, `SchoolYear`.
- `GeneralAssembly` 1—n `AgendaItem`, `OrganMembership` (aday, seçilen, divan), `AttendanceCorrection`; 1—1
  `AssemblyMinutes`; açacağı dönem `GeneralAssembly.opens_term`, açtığı dönem `OabTerm.opened_by_assembly`.
- `BoardMeeting` 1—n `BoardMeetingAttendance`, `BoardDecision`; `BoardDecision` n—1 `OfficialBook`; kararı gösteren
  bağlar: `ExpenseFile.decision`, `ExpenseFile.standing_decision`, `ReceiptBookRegistry.registration_decision`,
  `OrganMembership.promoted_by_decision`, `GeneralAssembly.call_decision`, `OabBudget.prepared_decision`,
  `LedgerEntry.decision`. `DEFTERDE_SAKAT` karar bu bağların hiçbirine bağlanamaz.
- `BankAccount` 1—n `BankStatement` 1—n `BankTransaction` n—m `LedgerEntry` (`TransactionMatch` üzerinden);
  `LedgerEntry` n—1 `LedgerAccount`, `TefbisTypeMapping`, `MarkBatch` (iki ayrı bağ); 1—n `LedgerEntryLine`.
- `ReceiptBookRegistry` 1—n `ReceiptLeaf` n—m `LedgerEntry` (`LeafUse` üzerinden; etkin bağ birebir).
- `ExpenseFile` 1—n `ExpenseInvoice` 1—n `LedgerEntry` (ödeme kayıtları; bağ yalnız `LedgerEntry.expense_invoice`).
- `ComplianceItem` n—1 `ComplianceJustification` (toplu gerekçe).
- `ExpenseFile` 1—n `ExpenseFileLine`, `ExpenseQuote`; komisyon üyeleri `OrganMembership(ALIM_KOMISYONU)`'ten.
- `SocialEvent` 1—n `LedgerEntry` (`LedgerEntry.event`); n—1 `BoardDecision`.
- `Tender` 1—n `Bidder`, `TenderCommissionMember`, `TenderApproval`; `Bidder` 1—n `BidderDocument`, `BidderScore`;
  `OabContract` 1—n `ContractInstallment`, `ShareStatement`; `ContractInstallment` 1—1 birlik payı `LedgerEntry`.
- `GeneratedDocument`, `Attachment`, `ComplianceItem` genel bağla (`*_type`, `*_id`) her kayda bağlanır.
- `ParentRoster` yalnız `ImportRun`, `OabTerm`, `GeneralAssembly`'ye bağlanır; ona bağlanan yoktur.
- `Account`, `AuditTrail`, `AuditKey`, `AccessLog` (§4.6): her modelin `created_by`/`updated_by`'ı `Account`'a bağlanır.

#### 5.2.11 Sürüm 2'ye kalanlar

Personel (K3; yalnız `DOGRUDAN_ISVEREN`): istihdam kartı (yaş grubu `≤18` · `19-49` · `≥50` — doğum tarihi tutulmadan, yıllık izin alt sınırı için; sözleşme türü `BELIRSIZ_SURELI` · `BELIRLI_SURELI` — ihbar süresi için; §6.4.10), yıllık izin kaydı ([5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) saklama), kıdem karşılığı ·
TEFBİS mutabakatının ekranı (M12; modeller §5.2.5'te) · denetim dosyası tabloları (M12b; model gerekmez, kayıtlardan
hesaplanır).

### 5.3 Şifreleme kapsamı

Çekirdek kurallar ailedendir ve §4.4.4'te tanımlanır: alan şifrelemesi Fernet, anahtar yokken yazma hata verir
(fail-closed), parola kurulmadan kişi yazan uçlar 409 döner, kör indeks `HMAC-SHA256(HKDF(DEK, "od-kor-indeks"),
normalize(değer))`, `PRAGMA secure_delete=ON`. `Account`, `AuditTrail`, `AuditKey` ve `AccessLog`'un şifrelemesi ve denetim
izine kişisel değer yazılmaması kuralı §4.6'dadır. Bu bölüm OAB modellerinde hangi alanın hangi korumayı aldığını
sabitler.

**İlke.** Kişi adı ya da kişiye ait bilgi içerebilecek her alan ve **her serbest metin** şifrelidir; yapılandırılmış ve
kişisiz alanlar (tutar, tarih, tür, durum, sayı, TEFBİS kodu, kurum adı, kurumsal IBAN) açıktır. **Şifreli alandan
türeyen her özet anahtarlıdır** (kör indeks, banka hareketi parmak izi): düz özet, şifreli değeri sözlük denemesine
açardı. Şifreli alanda veritabanı araması yoktur; listeleme, arama ve ada göre sıralama Python'da çözülerek yapılır
(ölçek: yılda birkaç yüz kayıt, ön değerlendirme §6).

| Model | Şifreli (Fernet) | Kör indeks / anahtarlı özet | Açık |
|---|---|---|---|
| `OabPerson` | `first_name`, `last_name` | `name_index` (adaşlık uyarısı, personel eşleştirme) | tür, beyan tarihleri, sayaçlar, durum |
| `Personnel` (okul) | ad-soyad | — (eşleştirme ailenin `name_match.py` yoluyla) | `member_kind`, tarihler |
| `ParentRoster` | `full_name` | `name_index` (adaydan kişi kaydına, yeniden aktarımda çift satır) | `student_class`, katılım işareti |
| `OrganMembership` | `dropped_reason`, `evidence_note`, `eligibility_bar_basis` | — | organ, görev, koltuk, oy, durum, kaynak, tarihler, görev alma engeli var/yok |
| `OabTerm` | `pre_program_evidence` | — | tarihler, durum, programdan önceki toplamlar |
| `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes`, `AttendanceCorrection` | `call_reason`, `notes`, `result_text`, `unaudited_documents_note`, `justification` | — | tarihler, sayılar, yeter sayı, ibra sonucu, oylar |
| `BoardMeeting`, `BoardDecision` | `agenda`, `text`, `dissent` | — | no, tarih, defter sıra no ve sayfa, oy sayıları, durum |
| `AuditReport` | `findings`, kontrol listesi notları | — | tür, tarih, bayraklar |
| `BankTransaction` | `description`, `counterparty` | `fingerprint` (HMAC; §2.3.1) | tarih, tutar, bakiye, referans |
| `LedgerEntry`, `LedgerEntryLine` | `description`, `donor_name`, `donor_tckn` | — (T.C. kimlik no'ya kör indeks **yok**) | tutar, tarih, yön, TEFBİS kodları, belge no ve tarihi, bağlar, işaretler |
| `LedgerAccount` | `purpose` | — | tür, bağlar |
| `ExpenseFile`, `ExpenseInvoice`, `ExpenseQuote`, `ExpenseFileLine` | `title`, `supplier_name`, `request_reason`, `delivery_note` | — | tutarlar, tüzel VKN, belge ve VİF no, durum |
| `DocumentRecord` | `counterparty`, `subject` | — | no, tarih, yön, dış sayı |
| `Bidder` | `legal_name`, `contact_address`, `contact_phone`, `contact_email`, `participation_bar_basis`, `disqualified_note` | — | tür, tüzel VKN, teklif tutarı (kantin), katılım engeli var/yok, eleme nedeni (kapalı liste) |
| `BidderDocument` | `subject_name` | — | belge türü, özne, görüldü ve geçerlilik tarihi |
| `OabContract` | `special_terms` | — | tutarlar, tarihler, durum, teminat türü ve akıbeti |
| `ReceiptLeaf`, `HandoverItem`, `TenderCommissionMember` | `cancel_reason`, `note`, `dissent` | — | numaralar, durumlar |
| `ComplianceItem`, `ComplianceJustification` | `text` (gerekçe) | — | kural kimliği, paket, ileti, kök neden anahtarı, tarihler |
| `SocialEvent` | `notes` | — | tür, ad, düzenleyen, tarihler, onay alanları, durum |
| `Attachment`, `GeneratedDocument` | dosyanın kendisi (dosya düzeyinde), `original_name`, `content_json` | — | sha256, tür, boyut, tarih, satır sayısı |
| `Account`, `AuditTrail`, `AuditKey`, `AccessLog` | bkz. §4.6.5 | bkz. §4.6.5 | bkz. §4.6.5 |

**Dosyalar.** `Attachment` ve `GeneratedDocument` dosyaları dosya başına rastgele anahtarla diskte şifreli durur;
anahtar DEK'ten türeyen sarmal anahtarıyla sarılıp `Attachment.key_wrap`'te tutulur (§4.4.4; dizge §2.3.1). DEK
yenilemesi dosyaları yeniden yazmaz, yalnız sarmalları tek SQLite işleminde yeniler. Dışarı çıkan (tam) yedeğe
girmeleri §4.4.7'dedir (R10). Açık hâli yalnız kullanıcı kaydet ya da yazdır dediğinde oluşur; açık kopya kuralı
§4.4.7'dedir. Veli adı taşıyan belgenin dosyası hiç saklanmaz (§5.2.8).

**T.C. kimlik no (K9).** Yalnız `LedgerEntry.donor_tckn`; yalnız `donor_tckn_enabled` açıkken yazılır. Ekranda
maskeli; maskesiz gösterim yalnız `yonetici` rolünde ve erişim günlüğüyle (§4.6.4). **Hiçbir dosyaya girmez** — dışa aktarım,
evrak, liste: bağış izleme çizelgesinde (E20) yalnız "kimlik no kayıtlı: evet/hayır" sütunu, TEFBİS listesinde (E18)
yalnız "kimlik no kaynağı" sütunu bulunur (§8.3). Kör indeksi yoktur: gruplama gerekmez, kalıcı bir indeks de takma
kimlik olurdu. Kişi, organ, istekli ve sözleşme kayıtlarında alan hiç yoktur. Birliğin kurumsal IBAN'ı kişisel veri değildir: açık ve
maskesiz kalır (§4.3).

### 5.4 Saklama ve anonimleştirme

Birlik defter ve belgeleri [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) ve [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) gereği Devlet Arşiv Hizmetleri Hakkında Yönetmelikteki süreler kadar
okulda saklanır; o Yönetmelik süreyi kurumun saklama planına bırakır ([Arşiv Yön. md. 9/4](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-9), [Arşiv Yön. md. 24](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-24)) ve MEB saklama planı
korpusta yoktur (§6.4.11-9). Bu yüzden program birlik kaydını **hiç silmez**; imha kurumun Ayıklama ve İmha
Komisyonunun işidir ve birim arşivinde yapılmaz ([Arşiv Yön. md. 17/1](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-17); tereddütte saklanır, [Arşiv Yön. md. 20/2](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-20)). Program yalnız amacı
biten kişisel veriyi siler ya da boşaltır ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7)).

| Veri | Kural | Süre | Dayanak |
|---|---|---|---|
| Birlik kayıtları: organ ve toplantılar, kararlar, mali kayıtlar ve banka hareketleri, koçan ve yapraklar, harcama dosyaları, sözleşmeler, üretilen evrak (veli adı taşıyan belge hariç), sapma kayıtları, denetim izi (kişisel veri taşımaz, §4.6.2) | Silinmez, anonimleştirilmez | Saklama planına göre — OAB evrakı için süre **DOĞRULANMADI** | [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [Arşiv Yön. md. 17/1](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-17), [Arşiv Yön. md. 18](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-18), [Arşiv Yön. md. 20/2](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-20) |
| Veli listesi (`ParentRoster`) | Dönem kapanışında bütün satırlar silinir; kapanışın sert adımıdır. Genel kuruldan sonra elle de silinebilir | Dönem kapanışına kadar | T5; [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Veli adı taşıyan üretilmiş evrak (E07 sınıf teslim çizelgesi, adlı E08 katılım cetveli) | Program dosyayı hiç saklamaz; yalnız tür, tarih, satır sayısı ve sha256 izi kalır; yeniden basılmaz, arşiv paketine girmez. Basılı aslı genel kurul tutanak dosyasındadır | — (iz birlik kaydıyla) | T5; R9; [md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Genel kurul katılım kaydı | Kişi düzeyinde işaret listeyle silinir; sayılar kalır (aşağıdaki öneri) | Sayılar: birlik kaydıyla | [md. 10/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1 |
| Bağışçı T.C. kimlik no'su (K9 açıksa) | TEFBİS'e girildikten sonra dönem kapanışında alan boşaltılır, "silindi" izi kalır | En geç dönem kapanışı | K9; [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4) (§15'e öneri B-8) |
| Kişi adı ve türü | Organ üyesi olmuş ya da aday olmuş kişide kalır (karar defteri, tutanak, aday listesi ve dönem sayacı bağı) | Birlik kaydıyla | [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Bağsız kişi kaydı (`OabPerson`) | Hiçbir üyelik, aday, bağış, komisyon, imza bloğu, sözleşme ya da devir kaydına bağlanmamış kişi kaydı silinir | Dönem kapanışı | [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Okul personeli (`Personnel`) | Ayrıldı işaretlenen ve hiçbir birlik kaydına (`OabPerson.personnel`, organ, komisyon, imza bloğu) bağı olmayan personel silinir; bağı olanın adı `OabPerson`'da kalır | Ayrılışı izleyen dönem kapanışı | [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Üyelik düşme gerekçesi ve görev alma engelinin dayanağı (`dropped_reason`, `eligibility_bar_basis`) | Serbest metin ve dayanak boşaltılır; `drop_kind` ve `eligibility_bar` kalır | Üyeliğin bittiği dönemin kapanışı | [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4) |
| Kiracı, kantin çalışanı, servis şoförü ve rehber personel belgeleri (özel nitelikli olabilir) | **Varsayılan: tarama alınmaz**; yalnız belge türü, "görüldü" tarihi ve geçerlilik sonu tutulur (birlik kaydıyla kalır). Asıl kâğıt birlik dosyasında ([md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Tarama eklenirse şifreli, erişim günlüklü, `OZEL_NITELIKLI`; süre dolunca imha adayı (kopya; asıl arşivde) | Tarama: sözleşme sonu + okul ayarı `scan_retention_years` (öneri 2 yıl; DOĞRULANMADI) | [md. 20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9); [KVKK md. 6](../mevzuat/6698-kvkk.md#madde-6) (§15'e öneri B-5) |
| İstekli iletişim bilgisi (`Bidder.contact_*`) | Seçilmeyen isteklinin adres, telefon ve e-postası süreç sözleşmeyle ya da iptalle kapandıktan sonraki ilk dönem kapanışında boşaltılır; sözleşme tarafı isteklininki sözleşme sona erdikten sonraki ilk dönem kapanışında. Ad kalır (tutanaklarda geçer) | Dönem kapanışı | [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4) (B-5 ile birlikte) |
| Katılım engelinin dayanağı ve eleme notu (`participation_bar_basis`, `disqualified_note`) | Boşaltılır; `participation_bar` ve kapalı listedeki eleme nedeni kalır | Süreç kapandıktan sonraki ilk dönem kapanışı | [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 6](../mevzuat/6698-kvkk.md#madde-6) |
| İçe aktarılan ham dosyalar (banka, TEFBİS, e-Okul) | Hiç saklanmaz; yalnız sha256 ve parti özeti | — | [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4) |
| Personel ve SGK belgeleri (sürüm 2) | Silinmez (silme kilidi) | İlgili yılı izleyen yıl başından 10 yıl (§6.4.10 yorumu) | [5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) |
| Hassas okuma ve erişim günlüğü (§4.6.4) | Süre dolunca silinir | 2 yıl (öneri; DOĞRULANMADI) | [KVKK md. 12](../mevzuat/6698-kvkk.md#madde-12) güvenlik tedbiri (§15'e öneri B-9) |

**Tek sabit, iki iş (denetim KM-5).** Bu tablodaki süreli kişisel veri alanları kodda tek bir sabitte durur
(`SURELI_KISISEL_ALANLAR`): `ParentRoster` (bütün satır), `LedgerEntry.donor_tckn`, `OabPerson` (bağsız kayıt),
`Personnel` (bağsız ayrılan), `OrganMembership.dropped_reason`, `OrganMembership.eligibility_bar_basis`, `Bidder.contact_*`,
`Bidder.participation_bar_basis`, `Bidder.disqualified_note`, `OZEL_NITELIKLI` taramalar. Dönem kapanışındaki silme
ve boşaltma işi ile arşiv paketinin dışlama listesi (§8.5) bu sabitten üretilir ve testle kilitlenir. Kural: süreli
kişisel veri alanı ve veli adı taşıyan belge arşiv paketine **hiçbir zaman** girmez — silinmemiş olsa da. Süreli
alan bir belgenin `content_json`'una girdiyse dönem kapanışında içerikten de boşaltılır; belgenin yeni içerik özeti
yeni sürüm satırına yazılır, eski özet denetim izinde kalır (§5.2.8).

**Genel kurul katılım kaydı — öneri (T5'in açık noktası; §15'e öneri B-11).**

- **Saklanan (kalıcı, kişisiz):** genel kurul ve toplantı başına imzalayan üye sayısı; türe göre dağılım (veli ve
  kursiyer, öğretmen, yönetici, hayırsever, diğer); velisi katılan öğrenci sayısı ve o günkü öğrenci mevcudu ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2)
  Tablo 1'in iki sütunu; oran hesaplanır); dondurulmuş yeter sayı ve sağlanıp sağlanmadığı; gözlemci öğrenci sayısı
  ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)).
- **Basılan cetvelin izi:** katılım cetvelinin `GeneratedDocument` satırı (tür, tarih, satır sayısı, sha256); dosyası
  saklanmaz, adlı cetveli yalnız `yonetici` basar (R9). İmzalı asıl genel kurul tutanak dosyasındadır ([md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)), okulda saklanır ([md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) ve devir kalemidir ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10)) —
  programın asıl kaydı kâğıttır.
- **Saklanmayan:** kişi düzeyindeki "katıldı" işareti (yalnız sayımı kolaylaştırmak için `ParentRoster` satırında
  durur, listeyle silinir), adlı cetvelin dosyası ve imzalı cetvelin taraması (varsayılan alınmaz: asıl zaten
  saklanıyor, tarama aynı kişisel veriyi ikinci kez ve süresiz tutardı).
- **Neden:** katılım sayısı yeter sayının (sert kural) girdisidir; altın kural 4 gereği dondurulur ve yalnız gerekçeli
  düzeltme satırıyla (`AttendanceCorrection`) değişir. Kişi listesi programdaki işi (cetvel basımı ve sayım) bitince
  amacını yitirir ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7)). Bu düzen TKB E.4 Tablo 1'i ve yeter sayı denetimini tek başına karşılar.

**Çalışma biçimi** (Kütüphane Defteri §6.4 kalıbı): (1) aday tespiti açılışta ve gün değişiminde yapılır ve pano
kalemi olarak hesaplanır (§7.10); program kilitliyken veritabanına yazılmaz (§4.1); (2) yönetici onayıyla tetik çalışır;
(3) tetikten önce `pre-anonim-<tarih>.odbak` yedeği alınır (F4'ten itibaren); (4) her silme ve boşaltma denetim izine kişisiz satır
yazar (tür, adet, tetik; §4.6.2); (5) dönem kapanışındaki silmeler kapanış işleminin parçasıdır, kapanış onayı yeter ve
arşiv paketinden **önce** yapılır (§7.8); silmelerden sonra WAL `TRUNCATE` ve eski `pre-migrate` silmesi koşar
(§4.4.7). Silinen kişisel veri programın yerel yedeklerinde en çok 14 gün kalır; düzenek (bütün öneklerin rotasyonu,
KVKK tetiğinden eski `pre-migrate` silmesi, `wal_checkpoint(TRUNCATE)`, dışarı alınmış yedek kartı) §4.4.7'dedir.
Dışarı çıkan (tam) yedek ekleri ve üretilmiş evrakı da taşır; yerel yedekler veritabanı + manifestodur (R10). Kullanıcının dışarı aldığı şifreli yedekler
okulun elindedir, imha kuralı kılavuzda yazılır.

---

## 6. Kural paketi

Kural paketi, programın koyduğu her sayısal ve yapısal hükmün (oran, süre, çarpan, sınır, organ bileşimi, vade)
**tek kaynağıdır** (altın kural 2). Kodda bu değerler sabit olarak yazılmaz; servisler değeri `kural("<id>")` ile
okur. Paket mevzuat değildir, korpusa atıftır: her kural `docs/mevzuat/` içindeki bir çapaya ve fıkra/bent
düzeyinde bir hükme bağlanır (altın kural 1). Doğrulanamayan hüküm pakete girmez; §6.4.11 sonunda ayrı listelenir.

**Paket okul ayarı değildir.** Okuldan okula değişen ve mevzuatın okula bıraktığı değerler okul kartında ya da
ayarlarda durur; bir hükmü uygulamak için okulun seçtiği yöntem (beyan almak gibi) okul uygulamasıdır. İkisi de kural
paketine girmez ve arayüzde "Yönetmelik gereği" diye sunulmaz (§3.3):

| Okul ayarı ya da okul uygulaması (kural değil) | Nerede | Kuralla bağı |
|---|---|---|
| Öğrenci mevcudu | okul kartı (F1b) | `genel_kurul.kucuk_okul_esik` ile karşılaştırılır |
| Yerleşim türü (büyükşehir · büyükşehir olmayan il merkezi · diğer) | okul kartı (`settlement_type`) | `pay_dagitimi.*` kurallarının `kosul` alanı |
| Kademe (okul öncesi · ilkokul · ortaokul · ortaöğretim; karma okulda birden çok) | okul kartı (`levels`) | `temsilci.*` kurallarının `kosul` alanı |
| Kantin işletme modu (kiraya veriliyor · birlikçe işletiliyor · kantin yok) | okul kartı (`canteen_mode`) | `arz_bedeli.kira_oran` ya da `arz_bedeli.isletme_oran` |
| Personel çalıştırma biçimi | okul kartı (`staffing_mode`) | `personel.*` kuralları yalnız doğrudan işverende |
| Ders yılı, dönemler, tatiller, iş günü takvimi | kurulum sihirbazı | süre hesapları (iş günü, "eğitim-öğretim yılı içinde") |
| Kayıt-kabul ve diploma dönemi tarihleri | ayarlar (`registration_periods`) | `bagis.kayit_doneminde_toplanmaz` |
| Küçük alım tutar sınırı, sürekli ödemeler için dönem başı genel kararı | ayarlar (YK karar no'suyla) | `harcama.*` uyarılarının gerekçesi (saha.md soru 6; §15 A-11) |
| YK aylık toplantı günü, DK denetim planı tarihleri | dönem ayarı (`OabTerm`, §5) | takvim; `yonetim_kurulu.toplanti_sikligi`, `denetleme_kurulu.inceleme_yilda_en_az` |
| TEFBİS işlem tipi eşlemesi | `TefbisTypeMapping` | kural değil; okul kendi TEFBİS listesini girer (K6, F0-e (d)) |
| İnternet bankacılığında üçüncü onay | ayarlar | mevzuat gereği diye sunulmaz (F0-e (c)) |
| Bağışçı T.C. kimlik no'su | ayarlar (varsayılan kapalı) | K9 |
| **Okul uygulaması:** YK, DK ve alım komisyonu üyesinden suç engeli ve tek birlik beyanı alınması | üyelik kaydı (`eligibility_declared_on`, `single_birlik_declared_on`) | Hüküm `uyelik.suc_engeli` ve `yonetim_kurulu.tek_birlik`'tedir; Yönetmelik beyan istemez. Beyan tarihi boşsa "tamamlanacaklar"da "Okulunuzun uygulaması: beyan alındı mı?" görünür; mevzuat uyarısı değildir, gerekçe istemez (KE-22). E01'de sütun başlığı "Beyan (okul uygulaması)" |
| **Okul uygulaması:** kantin isteklisi ve çalışanında suç engelinin nasıl tespit edildiği (belge görüldü, beyan) | `Bidder.participation_bar` (açık: var/yok), `Bidder.participation_bar_basis` (şifreli), `BidderDocument` | Hüküm `kantin.istekli_suc_engeli`'dedir; yöntem okulun ve komisyonundur, içerik tutulmaz |

### 6.1 Şema

Paket dosyası `backend/apps/oab/kurallar/paketler/OAB-2023.12.r<n>.json`, şeması aynı dizinde
`kural-paketi.schema.json` (JSON Schema 2020-12). Dosyalar sürümle birlikte dağıtılır, salt okunurdur; kullanıcı
kural düzenleyemez.

**Üst düzey alanlar**

| Alan | Tip | Zorunlu | Anlamı |
|---|---|---|---|
| `paket` | dize, `^OAB-\d{4}\.\d{2}$` | evet | Paket kimliği: dayandığı OAB Yönetmeliği metninin son değişikliğinin RG yılı ve ayı (v1: `OAB-2023.12` = RG 01.12.2023/32386) |
| `rev` | tamsayı ≥ 1 | evet | Aynı kimlikte içerik revizyonu (§6.2-1) |
| `sema_surumu` | tamsayı | evet | Bu şemanın sürümü (v1: 1) |
| `baslik` | dize | evet | İnsan okur ad |
| `korpus_teyit` | tarih `gg.aa.yyyy` | evet | Atıfların korpusa karşı son denetlendiği gün |
| `degisiklik_notu` | dize | evet | Bu revizyonda ne değişti, insan diliyle |
| `degisiklikler` | dizi `{id, tur}`; `tur` = `ekleme` · `bitis` · `deger_degisikligi` · `duzeltme` | evet | Önceki revizyona göre kural kural farklar; açık dönemin geçiş ekranı (§6.2-5) ve D2 bundan kurulur |
| `kurallar` | dizi | evet | Aşağıdaki kural nesneleri |

**Kural nesnesi**

| Alan | Tip | Zorunlu | Anlamı |
|---|---|---|---|
| `id` | dize, `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` | evet | `alan.konu`, ASCII snake_case, tam bir nokta. Alanlar: `genel_kurul`, `yonetim_kurulu`, `denetleme_kurulu`, `uyelik`, `temsilci`, `bagis`, `gelir`, `etkinlik`, `makbuz`, `harcama`, `bildirim`, `duyuru`, `vergi`, `denetim`, `arz_bedeli`, `pay_dagitimi`, `kira`, `kantin`, `servis`, `personel`. Kimlik bir kez yayımlanınca değişmez, silinmez |
| `deger` | sayı · ondalık dize · mantıksal · liste · nesne | evet | Kuralın değeri. Para ve oran **ondalık dize** (`"0.03"`), kayan nokta yasak |
| `birim` | enum | evet | `gun` (takvim günü) · `is_gunu` · `hafta` · `ay` · `yil` · `takvim_ayi` · `ayin_gunu` · `kisi` · `ogrenci` · `oran` · `puan` · `adet` · `tarih` · `mantiksal` · `liste` · `tablo` |
| `karsilastirma` | enum | evet | `en_az` · `en_cok` · `kucuktur` · `esit` · `carpan` · `parametre` · `liste_icinde` · `tablo` |
| `tur` | `uyari` · `sert` | evet | Aşağıdaki anlamda |
| `sert_gerekcesi` | `hesap_butunlugu` · `hesaplanan_deger` · `hukuki_gecersizlik` · `kullanici_karari` | `sert`te evet | Sertliğin dört kapalı gerekçesinden hangisi (aşağıda) |
| `dayanak_turu` | `lafiz` (varsayılan) · `yorum` · `kullanici_karari` | evet | Değerin lafızdan mı, yorumdan mı, kullanıcı kararından mı geldiği (aşağıda) |
| `karar` | `{kimlik, tarih}` (ör. `{"kimlik": "A-2", "tarih": "31.10.2026"}`) | `kullanici_karari`nda evet | Kararın §15'teki kimliği ve günü |
| `madde` | nesne `{capa, fikra?, bent?, alt_bent?, fikra_bicimi?}` | evet | Asıl dayanak; `kullanici_karari`nda gerekçe ya da bağlam hükmü. `capa` = `<dosya>#<çapa>` (`docs/mevzuat/` köküne göre). `fikra` numaralı fıkra ya da paragraf sırası; `fikra_bicimi` = `numarali` (varsayılan) ya da `paragraf` (kanunlar, EK-2, genelgeler). Çok fıkralı ya da çok paragraflı maddede `fikra` boş bırakılamaz (D4) |
| `ek_madde` | `madde` dizisi | hayır | Ek dayanaklar (ör. md. 9/6 olağanüstü için) |
| `aciklama` | dize | evet | Hükmün bir cümlelik özeti (lafız değil) |
| `uyari_metni` | dize (yer tutuculu) | `uyari`da evet | Ekranda görünen metin; atıf `madde` ve `dayanak_turu`ndan otomatik eklenir |
| `kosul` | nesne (anahtarlar aşağıdaki sözlükte) | hayır | Kuralın uygulandığı okul kartı ya da kayıt durumu (ör. `{"okul.kademe": ["ORTAOGRETIM"]}`) |
| `olay_tarihi` | dize (aşağıdaki tablodaki adlardan) | hayır | Kuralın baktığı olayın günü; boşsa alanın varsayılanı |
| `yururluk` | `{baslangic, bitis}` (`gg.aa.yyyy`, `bitis` boş olabilir) | evet | Bu değerin geçerli olduğu aralık: **değerin bugünkü hâliyle yürürlüğe girdiği tarih** (değeri taşıyan cümle ya da ibarenin şerhindeki RG tarihi; şerh yoksa metnin yayımı). Aynı fıkradaki başka bir ibarenin şerhi tarihi değiştirmez. `kullanici_karari`nda: paketin dayandığı Yönetmelik metninin tarihi (v1: 01.12.2023), kararın günü değil |
| `giris` | `F1c`…`F8` | evet | Kuralın pakete girdiği faz; değer ve atıf testleri bu fazda (§6.2-2) |
| `davranis_fazi` | `F1c`…`F8`, ≥ `giris` | evet | Kuralı kullanan servisin ve davranış testinin geldiği faz (§6.2-2; D6) |
| `yorum` | dize | `yorum`da evet | Değerin lafzın ötesine geçtiği nokta açıkça yazılır (ör. "ilk hafta = 7 takvim günü"); arayüzde ve gerekçe kaydında "yorum" etiketiyle görünür |
| `eksik_veri` | `tamamlanacak` (varsayılan) · `sapma` | evet | Denetlenecek veri henüz girilmemişse ne olacağı (aşağıda) |
| `toplu_gerekce` | mantıksal (varsayılan `true`) | evet | Aynı kök nedenli sapmalara tek gerekçe verilebilir mi (aşağıda) |

**`tur` alanının anlamı.**

- `uyari`: program doğrusunu gösterir, **sapma gerekçeyle** kaydedilir; gerekçe, kural kimliği ve paket revizyonuyla
  birlikte denetim izine ve `ComplianceItem` kaydına düşer (altın kural 3). Eksik veri sapma değildir (aşağıda).
- `sert`: kural dışı değer ya da işlem kaydedilmez. Yalnız şu dört gerekçeyle kullanılır; gerekçe `sert_gerekcesi`
  alanında adıyla yazılır, liste kapalıdır ve genişletilmesi kullanıcı kararı ister (B-13'ün gerekçesi bu
  kapalılıktır). Bu liste CLAUDE.md altın kural 3 ve §2.1 F0-b ile aynı metin olur (EK-6):
  1. **`hesap_butunlugu`** — toplamlar, numara tekilliği, kapanmış dönem, yeter sayı ve karar hesabı (oylardan
     hesaplanan sonuç), alt hesabın eksiye düşmemesi.
  2. **`hesaplanan_deger`** — programın **kendi hesapladığı** tutar ve sürede kullandığı yasal oran, çarpan, taban ve
     sayım yöntemi (kullanıcı kararı D1, §15.1b). Hesap paketteki değerle yapılır; kullanıcı oranı ya da çarpanı
     değiştiremez. Bu sertlik gerçekte olanın kaydını **engellemez**: ödenen, tahsil edilen ya da belgede yazan tutar
     hesaplanandan farklıysa kayıt olduğu gibi yapılır (banka hareketi reddedilemez, K1) ve fark aynı kural kimliğiyle
     **uyarı + gerekçe** olur (KE-23). Kullanıcının belgeden **girdiği** değer (sözleşmedeki teminat, kira, TÜFE artışı, kira ay
     sayısı, kiralama usulü, EK-3 puanı, izin ve ihbar süresi) bu türe girmez; o kurallar `uyari`dır.
  3. **`hukuki_gecersizlik`** — mevzuatın hukuken geçersiz saydığı işlem: kantin isteklisinde suç ve hısımlık engeli
     ([md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), 20/11), serviste mülki amir onayı olmadan
     kesinleştirme (D4; kantinde uyarıdır), organda mevzuatın saymadığı kişi türü
     ([md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12),
     [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); plan §2.4 F1 kapısı "YK'ye veli olmayan
     eklenemez" ve "DK bileşimi").
  4. **`kullanici_karari`** — kullanıcının açıkça "sert" dediği kural (§15.1: A-2, KE-15).

**Dayanak türü.** `lafiz`: değer fıkranın sözündedir. `yorum`: değer lafzın ötesine geçer; `yorum` alanı zorunludur
ve arayüzde, gerekçe kaydında ve evrakta "yorum" etiketiyle görünür. `kullanici_karari`: hüküm mevzuatta açıkça
yoktur, kullanıcı kararıyla konur; `madde` gerekçe ya da bağlam hükmünü taşır, atıf "kullanıcı kararı A-2 (gerekçe md.
14/4)" biçiminde basılır ve hiçbir yerde "Yönetmelik gereği" denmez (altın kural 1). Kullanıcı kararı kuralının
yürürlüğü kararın günü değil paketin Yönetmelik metninin tarihidir: karar o metnin geçerli olduğu her olaya, kararın
verildiği ayın genel kuruluna da uygulanır (MA-1; KE-25).

**Eksik ve sapma** (R5). Eksik: kuralın denetleyeceği veri **henüz girilmemiştir** (ilan kanıtı, VİF no, beyan, belge
tarihi, kişi geçmişi). Eksik veri gerekçe istemez; "tamamlanacaklar" listesinde (pano, §7.10) kalır ve `ComplianceItem`
sapma satırı açmaz. Kuralın akışındaki kapanış geçişinde (genel kurul `TUTANAK_TAMAM`, harcama dosyası `KAPANDI`,
sözleşme `IMZALANDI`, dönem kapanışı) hâlâ eksikse sapmaya döner ve gerekçe istenir. `eksik_veri: sapma` olan
kuralda eksiklik baştan sapmadır (süresi kendiliğinden dolan yükümlülükler: aylık bildirim, dönemlik duyuru,
YK aylık toplantısı). Sapma: girilen değer kuraldan bilinçli olarak ayrılır; gerekçe ister. **Toplu gerekçe:** aynı
kural ve aynı kök neden için birden çok kayda tek gerekçe verilebilir (bir genel kurulun eksik kanıtları, bir koçanın
yaprakları, bir sözleşmenin ay ay kira farkları); gerekçe her kayda ayrı satır olarak bağlanır. `toplu_gerekce: false`
olan kuralda her kayıt kendi gerekçesini ister (`harcama.organ_uyesine_odeme`, `kantin.kiralama_onay_kaydi`).

**`kosul` sözlüğü** (UY-12). Anahtarlar Türkçe kısa ad, bağlandığı alan §5'teki adla; değerler enum değeriyle
birebir (büyük harf) yazılır ve JSON Schema'da `enum` ile kilitlenir. D1 sözlükte olmayan anahtarı ya da değeri
reddeder. Koşul sağlanmıyorsa kural o okulda ya da kayıtta uygulanmaz (uyarı da bilgi de üretmez).

| Anahtar | Bağlandığı alan | Değerler | Değerlendirme |
|---|---|---|---|
| `okul.kademe` | `SchoolConfig.levels` (çok değerli; karma okul birden çok kademe seçer) | §5.1 `levels` enum'u (`OKUL_ONCESI` · `ILKOKUL` · `ORTAOKUL` · `ORTAOGRETIM`) | kesişim boş değil |
| `okul.yerlesim_turu` | `SchoolConfig.settlement_type` | `BUYUKSEHIR` · `IL_MERKEZI_BUYUKSEHIR_DEGIL` · `DIGER` | içinde |
| `okul.kantin` | `SchoolConfig.canteen_mode` | `KIRAYA_VERILIYOR` · `BIRLIKCE_ISLETILIYOR` · `KANTIN_YOK` | içinde |
| `okul.personel` | `SchoolConfig.staffing_mode` | `DOGRUDAN_ISVEREN` · `HIZMET_ALIMI` · `CALISTIRMIYOR` | içinde |
| `etkinlik.duzenleyen` | `SocialEvent.organizer` (§5.2.7) | `BIRLIK` · `UCUNCU_KISI` | içinde |
| `personel.sozlesme_turu` | personel modeli (sürüm 2) | `BELIRSIZ_SURELI` · `BELIRLI_SURELI` | içinde |

**Olay tarihi** (MA-12). `kural(id, tarih)`'e geçirilen tarih kuralın denetlediği olayın günüdür; işlem anı değil.
Sözleşmeye bağlı kurallar sözleşmenin ilk tarihine değil, denetlenen olayın gününe bakar. Varsayılanlar:

| Alan | Olay tarihi (varsayılan) |
|---|---|
| `genel_kurul.*` | duyuru kurallarında duyuru günü, ötekilerde toplantı günü |
| `yonetim_kurulu.*`, `denetleme_kurulu.*`, `uyelik.*`, `temsilci.*` | seçim ya da görevlendirme günü; toplantı kurallarında toplantı günü |
| `bagis.*`, `gelir.*`, `etkinlik.*`, `makbuz.*`, `harcama.*`, `bildirim.*`, `duyuru.*`, `vergi.*`, `denetim.*` | işlemin (kabul, tahsilat, ödeme, cilt kaydı, etkinlik, bildirim) günü |
| `arz_bedeli.*`, `pay_dagitimi.*`, kira takvimi kuralları | ödeme döneminin (ay ya da çeyrek) son günü |
| `kira.*`, `kantin.*` (sözleşme ve kiralama) | denetlenen olay: imza (teminat, süre, ay sayısı, usul), teslim, artış, yenileme, fesih, belge tarihi |
| `servis.*` | denetlenen adım: ilan, karar, onay, tebliğ, imza, belge |
| `personel.*` | izin, ihbar ya da belge günü |

**Örnek (iki kural; `uyari` kuralında ayrıca `uyari_metni` vardır, ör. "Duyuru ile toplantı arasında {fark} gün var;
en az {deger} gün olmalı."):**

```json
{
  "paket": "OAB-2023.12",
  "rev": 1,
  "sema_surumu": 1,
  "baslik": "MEB Okul-Aile Birliği Yönetmeliği (son değişiklik RG 01.12.2023/32386) ve bağlı metinler",
  "korpus_teyit": "31.10.2026",
  "degisiklik_notu": "F1c: yeter sayı, organ bileşimleri, dönem sınırları, temsilciler, F1c listesindeki süre ve oranlar",
  "degisiklikler": [{"id": "pay_dagitimi.il_merkezi", "tur": "ekleme"}, {"id": "denetleme_kurulu.yk_uyesi_olamaz", "tur": "ekleme"}],
  "kurallar": [
    {
      "id": "pay_dagitimi.il_merkezi",
      "deger": {"birlik": "0.80", "ilce": "0.00", "il": "0.20"},
      "birim": "oran",
      "karsilastirma": "tablo",
      "tur": "sert",
      "sert_gerekcesi": "hesaplanan_deger",
      "dayanak_turu": "yorum",
      "madde": {"capa": "meb-okul-aile-birligi-yonetmeligi.md#madde-17", "fikra": "1", "bent": "a", "alt_bent": "2"},
      "ek_madde": [{"capa": "meb-okul-aile-birligi-yonetmeligi.md#madde-17", "fikra": "1", "bent": "b", "alt_bent": "2"}],
      "aciklama": "Büyükşehir statüsünde olmayan il merkezlerindeki birliklerde ilçe payı ayrılmaz, %20 il MEM hesabına yatırılır.",
      "kosul": {"okul.yerlesim_turu": ["IL_MERKEZI_BUYUKSEHIR_DEGIL"]},
      "yururluk": {"baslangic": "09.02.2012", "bitis": null},
      "giris": "F1c",
      "davranis_fazi": "F3",
      "yorum": "Yönetmelik 'gelirin %20'si' der; taban net tutar (arz düşülmüş) kabul edildi, birlik %80 ile toplam %100.",
      "eksik_veri": "tamamlanacak",
      "toplu_gerekce": true
    },
    {
      "id": "denetleme_kurulu.yk_uyesi_olamaz",
      "deger": true,
      "birim": "mantiksal",
      "karsilastirma": "esit",
      "tur": "sert",
      "sert_gerekcesi": "kullanici_karari",
      "dayanak_turu": "kullanici_karari",
      "karar": {"kimlik": "A-2", "tarih": "31.10.2026"},
      "madde": {"capa": "meb-okul-aile-birligi-yonetmeligi.md#madde-14", "fikra": "4"},
      "aciklama": "Aynı kişi aynı dönemde yönetim kurulunda ve denetleme kurulunda bulunamaz.",
      "yururluk": {"baslangic": "01.12.2023", "bitis": null},
      "giris": "F1c",
      "davranis_fazi": "F1c",
      "eksik_veri": "tamamlanacak",
      "toplu_gerekce": true
    }
  ]
}
```

**Erişim.** `kural(id, tarih=None, donem=None)` dönemin bağlı paketinden (§6.2), `tarih`i kapsayan yürürlük
aralığındaki değeri döndürür; `tarih` verilmezse olay tarihi (yukarıdaki tablo) kullanılır. `denetle(id, ...)` sonucu
`{durum: uygun|eksik|uyari|sert|denetlenmedi, mesaj, atif, dayanak_turu, paket, rev}` döner; `atif` ekranda ve gerekçe
kaydında "md. 9/3" ya da "kullanıcı kararı A-2 (gerekçe md. 14/4)" biçiminde görünür. İki durum ayrıdır:

- **Bilinmeyen kimlik** (koddaki kimlik pakette yok): programlama hatasıdır; testte yakalanır (§6.3 D6), çalışma
  anında yine de olursa ilgili yazma işlemi yapılmaz (fail-closed).
- **Olay tarihinde yürürlükte değer yok** (olay, değerin bugünkü hâlinden önce; ör. 01.12.2023'ten önce imzalanıp
  hâlâ süren kantin sözleşmesinin teminatı, [geçici md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#gecici-madde-4)):
  denetim yapılmaz (`denetlenmedi`), kayıt yapılır ve "olay tarihindeki metin korpusta yok; denetlenmedi" bilgi notu
  düşer. Hesaplanan değer gerekiyorsa tutar sözleşme ya da belge alanından okunur. Aynı sözleşmenin 2026'daki ödeme ve
  artış olayları bugünkü değerle denetlenir (MA-12).

### 6.2 Sürümleme ve dönem bağı

1. **Kimlik ve revizyon.** `paket` OAB Yönetmeliğinin metin durumunu izler (Yönetmelik değişince yeni kimlik:
   `OAB-<yyyy>.<aa>`). Aynı kimlik altında her içerik değişikliği `rev`'i bir artırır ve `degisiklikler`'de türüyle
   yazılır: **ekleme** (yeni kural), **bitiş** (mevzuat hükmü kaldırdı; `yururluk.bitis` dolar), **değer değişikliği**
   (bağlı bir metin — EK-2, Genelge 2024/35, Servis Usul ve Esasları, Okul Servis Araçları Yön. — değeri değiştirdi;
   madde 3), **düzeltme** (değer baştan yanlış yazılmıştı; madde 3a). Yayımlanan bir revizyon dosyası değiştirilmez;
   yeni dosya eklenir.
2. **Kurallar fazlarıyla birlikte girer** (UY-15). Bir kural pakete, onu ilk kullanan kodun geldiği fazda girer
   (`giris`) ve o fazda değer ve atıf testlerini taşır; davranış testi kuralın `davranis_fazi`nda gelir (§6.4 "Giriş"
   sütununda parantez içi; parantez yoksa aynı faz). F1c'de `r1` = plan §2.3'teki liste + organ, divan, alım
   komisyonu ve temsilci kuralları (**53 kural**; 18'inin davranışı sonraki fazlarda); F2…F8 her biri `rev`'i
   artırır. **Ekleme ve bitiş** revizyonları mevcut değerleri değiştirmez; açık dönemin bu revizyonlara geçişi hesap
   değiştirmez.
3. **Değer değişirse eski kayıt kalır.** Mevzuat bir değeri değiştirirse aynı `id` ile ikinci bir kayıt eklenir: eskinin
   `yururluk.bitis`'i değişiklikten önceki gün, yeninin `baslangic`'ı değişiklik günüdür. Aynı kimliğin aralıkları
   çakışamaz (D2). Böylece açık dönemde değişiklikten önce olmuş olaylar eski değerle hesaplanmaya devam eder.
   3a. **Düzeltme** (UY-16). Değer baştan yanlışsa aynı `id` ve aynı yürürlük aralığıyla düzeltme kaydı yayımlanır;
   `degisiklikler`'de `duzeltme` diye işaretlenir ve D2'de önceki revizyondaki aynı aralığın yerini alır (çakışma
   sayılmaz). Düzeltmenin kendi yürürlük tarihi yoktur: açık dönem geçtiğinde geçmiş olaylar da yeni değerle yeniden
   denetlenir ve hesaplanır. Bu yüzden geçiş ekranı hesabı ya da uyarısı değişecek kayıtları tek tek listeler ve
   onay ister. Kapanmış dönem düzeltmeden etkilenmez (madde 6); gerekirse fark açık dönemde "önceki dönem
   düzeltmesi" ters kaydıyla işlenir (§15 B-4).
4. **Dönem bağı.** Her birlik dönemi (`OabTerm`, T3: genel kuruldan genel kurula) açılışta programla gelen en yeni
   revizyona bağlanır. Bağ bir `RulePackage` kaydıdır: `paket`, `rev`, içeriğin **dondurulmuş kopyası** (JSON) ve
   SHA-256 özeti veritabanında tutulur. Dönemin bütün hesapları, uyarıları ve evrakı bu kopyadan okunur; program
   güncellemesi dosyayı değiştirse ya da kaldırsa bile bağlı dönem etkilenmez.
5. **Açık dönemin geçişi.** Yeni revizyon geldiğinde açık dönem kendiliğinden geçmez. Yönetici "kural paketi
   güncellemesi" ekranında farkı görür: eklenen, biten, değeri değişen ve düzeltilen kurallar ve **hesabı ya da
   uyarısı değişecek kayıtların listesi** (düzeltme ve değer değişikliği varsa zorunlu); onaylar. Geçiş denetim izine
   kim-ne-zaman ve eski/yeni revizyonla yazılır. Geçiş geri alınabilir (dönem kapanana kadar).
6. **Kapanmış dönem değişmez.** Dönem kapanışında (F4) bağ kilitlenir. Kapanmış dönemde revizyon geçişi **sert
   engeldir** (hesap bütünlüğü); yalnız işaret alanları ve yeniden basım kaydı yazılır (R12). **Yeniden basım**, kayıtlı
   belge sürümünün her üretimde saklanan içerik JSON'undan (`GeneratedDocument.content_json`, şifreli; §5) çizilir.
   İçerik özeti (§9.1-2) bu JSON'un özeti olduğu için program sürümü, şablon metni ya da ana veri (okul adı, kişi adı)
   sonradan değişse de aynı çıkar; çizicinin değişmesi yalnız dosya özetini değiştirir (UY-13). Kapanmış dönemde
   güncel kayıtlardan yeniden **üretim** yapılmaz. **İstisna (R9):** veli adı taşıyan E07 ve E08'in içerik JSON'u ve
   dosyası saklanmaz (yalnız sha256, satır sayısı, tarih); bu iki belge yeniden basılamaz ve bu vaadin dışındadır,
   basılı aslı genel kurul tutanak dosyasındadır. Yedekten geri yüklenen eski dönem de kendi kopyasıyla gelir; program
   o revizyonu artık taşımasa bile hesap yapılır.
7. **Değişiklik akışı.** Mevzuat değişikliği → korpus güncellenir ([BENIOKU §8](../mevzuat/BENIOKU.md)) → yeni kayıt
   ya da yeni kimlik → §10 testleri → sürüm notu → program güncellemesi. Kural paketi yalnız program sürümüyle
   değişir; kullanıcının kural ekleme, silme, değer değiştirme yolu yoktur.

### 6.3 Doğrulama ve atıf kilidi

| # | Denetim | Ne denetler | Ne zaman | Başarısızlıkta |
|---|---|---|---|---|
| D1 | Şema | JSON Schema'ya uygunluk; zorunlu alanlar; ondalıkların dize olması; tarih biçimi; `sert`te `sert_gerekcesi`, `kullanici_karari`nda `karar`, `yorum`da `yorum` dolu; `kosul` anahtar ve değerleri sözlükte (§6.1); `davranis_fazi` ≥ `giris` | açılış + test | Paket yüklenmez → kural kullanan yazma uçları kapalı (fail-closed), ana ekranda hata; okuma açık |
| D2 | Kimlik | `id` biçimi; aynı `id`'nin yürürlük aralıkları çakışmaz (düzeltme kaydı önceki revizyondaki aynı aralığın yerini alır); yayımlanmış `id` silinmemiş ve `degisiklikler` önceki revizyonla tutarlı (karşılaştırma) | açılış + test | D1 gibi |
| D3 | **Atıf kilidi — çapa** | `madde.capa` ve her `ek_madde.capa` için: dosya `docs/mevzuat/` altında var; adı `.draft-` ile başlamıyor; `bilgi/` altında değil (özelge ve sirküler kural dayanağı olamaz); frontmatter `belge-turu` "denetim rehberi" değil (TKB E.4 kabul ölçütüdür, mevzuat değil); dosyada `<a id="<çapa>"></a>` var; frontmatter `yururlukte: false` ise kuralın `yururluk.bitis`'i dolu. `kullanici_karari` kuralında `karar.kimlik` testteki karar listesinde (§15.1, §15.1b'den elle yazılır) var | test (Docker; F1 kapısı) | Test kırmızı → faz kapanmaz |
| D4 | **Atıf kilidi — fıkra ve bent** | Çapadan bir sonraki çapaya kadar olan madde gövdesinde: `numarali` biçimde `(<fıkra>)` geçer; `paragraf` biçimde o sırada paragraf var; `bent` için `<bent>)` geçer; madde birden çok fıkra ya da paragraf taşıyorsa `fikra` boş değil (MA-13). Atıf yapılan fıkra, bent ya da alt bent: (a) `(Mülga` ile başlamıyor; (b) "yürütmesi durdurulan" ibaresini taşımıyor; (c) "iptal bent" ya da "iptal ibare" geçiyorsa ardından "(Yeniden Düzenleme:" geliyor (MA-14) | test | D3 gibi |
| D5 | Tutarlılık | `genel_kurul.yeter_sayi_taban` = YK asıl + yedek + DK asıl + yedek (16); her pay tablosunun toplamı 1,00; `arz_bedeli.sozlesme_vade_gunu` < `arz_bedeli.yonetmelik_vade_gunu`; EK-3 kriter azamileri toplamı 25; `genel_kurul.yeter_sayi_carpan` > `genel_kurul.kucuk_okul_carpan` | açılış + test | D1 gibi |
| D6 | Kapsam | Koddaki her `kural("…")` çağrısının kimliği pakette var (statik tarama); paketteki her kuralın `@pytest.mark.kural_deger("<id>")` işaretli testi var; `davranis_fazi` geçerli faza eşit ya da küçük olan her kuralın `@pytest.mark.kural_davranis("<id>")` işaretli en az bir testi var (§10); iki işaret `pyproject.toml` `markers` listesinde kayıtlı (ailenin `--strict-markers` ayarı) | test | D3 gibi |
| D7 | Bütünlük | Dağıtılan dosyanın SHA-256'sı sürüm bildirimindeki değerle; dönemin dondurulmuş kopyasının özeti `RulePackage` kaydıyla aynı | açılış | Dönem salt okur açılır, yönetici uyarılır (yedekten geri yükleme önerisi) |
| D8 | Sabit taraması (sezgisel) | `apps/oab` iş kodu (testler ve `kurallar/` hariç) içinde paket değerlerinin çıplak yazımı: `Decimal("0.03")`, `"0.80"`, `timedelta(days=15)`, `* 4` gibi kalıplar; izin listesiyle | test (lint adımı) | Uyarı; gözden geçirmede kapanır |

Atıf kilidi (D3-D4) çalışma anında yapılmaz: korpus pakete girmez, dağıtılan programda `docs/` yoktur. Kilidin
güvencesi, korpusta çapası doğrulanmamış bir kuralın sürüme hiç girememesidir. Çapalar korpusta değişmez
([BENIOKU §2](../mevzuat/BENIOKU.md)); bir çapa adı değişirse D3 bütün bağlı kuralları kırmızıya çevirir. Çapa
**eklemek** yasak değildir; çapası olmayan bir hüküm (Genelge 2020/8, §6.4.11 DOĞRULANMADI-14) çapa eklenene kadar
pakete giremez.

### 6.4 v1 içeriği (`OAB-2023.12`)

Kısaltmalar: atıfta yalın madde numarası **MEB Okul-Aile Birliği Yönetmeliği**dir. EK-2 = aynı Yönetmeliğin Kantin
Kiralama Sözleşmesi (Genel Şartlar); "EK-2 md. 7/2. paragraf" maddenin ikinci paragrafıdır · G.2024/35, G.2011/40 =
MEB genelgeleri · U-E = Okul Servis Araçlarının Çalıştırılmasına İlişkin Usul ve Esaslar · OSAY = Okul Servis Araçları
Yönetmeliği · OKY = Ortaöğretim Kurumları Yön. · OÖİKY = Okul Öncesi Eğitim ve İlköğretim Kurumları Yön. · SEY =
Sosyal Etkinlikler Yön. · RPD = Rehberlik ve Psikolojik Danışma Hizmetleri Yön. · HEY = Hijyen Eğitimi Yön. · TMY =
Taşınır Mal Yön. · KDVK = 3065 · "Tür": **U** = uyarı; **S** = sert, parantezde `sert_gerekcesi`: **hb** hesap
bütünlüğü · **hd** hesaplanan değer · **hg** hukuken geçersiz işlem · **kk** kullanıcı kararı · "Giriş" = `giris`;
parantezde `davranis_fazi` (yoksa aynı) · Not sütunundaki **yorum** ve **kullanıcı kararı** etiketleri
`dayanak_turu` alanıdır · "Yürürlük" §6.1'deki tanımla (değerin bugünkü hâli).

#### 6.4.1 Genel kurul

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `genel_kurul.olagan_son_ay` | Ekim (ayın son günü dâhil) | U | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | Ders yılının başladığı takvim yılının 31.10'u |
| `genel_kurul.yeni_okul_ay` | 2 ay | U | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Okulun açıldığı tarihten (`opened_on`); çağrı okul müdürünün yazısıdır (E05, müdür hesabından; M-11) |
| `genel_kurul.ilan_en_az_gun` | 15 gün | U | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c (F2) | Duyuru günü ile toplantı günü arası ≥ 15 |
| `genel_kurul.ilan_kanallari` | elden yazılı · ilan panosu · internet sayfası | U | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F2 | Üçü birlikte; her biri için kanıt alanı (tarih, görev); kanıt E05'in duyuru kanıtı bölümünde, sınıf teslimi E07'de |
| `genel_kurul.yeter_sayi_taban` | 16 | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | YK 5+5 + DK 3+3. **Yorum:** "asıl ve yedek üye sayısı" kadrodur (16), dönemdeki fiilî üye sayısı değil; üyelik kayıtlarından sayılmaz (OYS S-1 düzeltmesi); D5 ile bileşim kurallarına bağlı |
| `genel_kurul.yeter_sayi_carpan` | ×4 | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c | 16 × 4 = 64; olağanüstü GK'de de (OYS S-2 düzeltmesi) |
| `genel_kurul.kucuk_okul_carpan` | ×2 | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c | 16 × 2 = 32 |
| `genel_kurul.kucuk_okul_esik` | mevcut < 100 | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c | "Yüzün altında": 99 → ×2, 100 → ×4; mevcut okul kartından, GK kaydına anlık değer olarak yazılır |
| `genel_kurul.ikinci_toplanti_en_gec_gun` | 30 gün | U | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | **Yorum:** süre birinci toplantı gününden başlar ("toplanamaması durumunda, en geç otuz gün içinde"); OYS'de yoktu |
| `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | evet | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | Yeter sayı hesabı: ikinci toplantıda yeter sayı denetlenmez, kararlar katılanların çoğunluğuyla. Olağanüstüde uygulanması kullanıcı kararı (§15 A-1). §7.1'de [S] |
| `genel_kurul.karar_cogunlugu` | katılanların çoğunluğu | S (hb) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F2 | Karar sonucu oylama alanından hesaplanır; oylarla çelişen "kabul" işareti konamaz |
| `genel_kurul.gundem_degisikligi` | ekleme ve çıkarma oylanır; oy çokluğu aranır | U | [9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Oylama satırı yoksa ya da oy çokluğu yoksa uyarı + gerekçe; tutanak olduğu gibi girilir. "Sıra değişikliği" lafızda olmadığı için kuraldan çıkarıldı (MA-16); 9/4 1. cümle ("sırası ile görüşür") bilgi notu |
| `genel_kurul.olaganustu_cagiranlar` | YK · okul müdürü · DK (14/5) · üyelerin %10'u · başkan ya da okul müdürü (13/8) · okul müdürü (25/2) | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); [14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) | 01.12.2023 | F2 | "Çağıran" alanı formda zorunlu; listede olmayan → uyarı. Çağrı yazısını çağıran üretir (E05; M-5, M-6). DK yolu yalnız `AuditReport.md6_violation_found` işaretliyken açılır: 14/5 DK'ye çağrıyı YK'nin md. 6'daki görev ve yetkilerine aykırı faaliyetinde verir (MB-10) |
| `genel_kurul.olaganustu_basvuru_oran` | %10 (0,10) | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Üye sayısı elle girilir; başvuru eki kanıt. Aynı cümledeki 2023 ek ibaresi (25/2) %10'u değiştirmedi (MA-17) |
| `genel_kurul.olaganustu_gundeme_baglilik` | evet | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Çağrıda olmayan gündem maddesi → uyarı (§15 B-13) |
| `genel_kurul.divan_uye_turleri` | veli · 18 yaşını doldurmuş kursiyer | U | [10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) | 01.12.2023 | F1c (F2) | Divan başkanı ve kâtip; açık oy. Uygunluk kişinin işine değil **veli olup olmadığına** bakar: veli olan öğretmen ve idareci uygundur (MA-11). `DIVAN` organı F1c'de açıldığı için `r1`'de (MA-7) |
| `genel_kurul.secim_bicimi` | asıl ve yedek liste hâlinde, açık oy | U | [10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10); [11/1-a, b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 09.02.2012 | F2 | Liste ve açık oy sınanır. DK öğretmen koltuklarının GK oylamasına girmemesi `denetleme_kurulu.koltuklar`'dadır (EK-5). Yürürlük: 10/1-d şerhsiz; 11/1'deki 2023 ibareleri kişi türüne ilişkin |

#### 6.4.2 Yönetim kurulu ve ortak üyelik

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `yonetim_kurulu.asil_uye` | 5 | U | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 09.02.2012 | F1c | Eksik bileşim uyarı; yeter sayı tabanını etkilemez. 12/1 2023'te bütünüyle değişti; "beş asıl" 11/1-a'nın değişmeyen kısmında 2012'den beri (MA-17) |
| `yonetim_kurulu.yedek_uye` | 5 | U | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 09.02.2012 | F1c | — |
| `yonetim_kurulu.uye_turleri` | veli · 18 yaşını doldurmuş kursiyer · okul yaptıran hayırsever (isterse) | S (hg) | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F1c | Plan §2.4 F1 kapısı "YK'ye veli olmayan eklenemez". Uygunluk kişinin **veli olup olmadığına** bakar (`OabPerson` veli işareti, §5): veli olmayan öğretmen ve idareci reddedilir; veli olan öğretmen ve idareci eklenebilir; okul müdürü veli olsa da reddedilir (KE-15) (MA-11) |
| `yonetim_kurulu.okul_muduru_uye_olamaz` | evet | S (kk) | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [27/2-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) (gerekçe) | 01.12.2023 | F1c | **Kullanıcı kararı KE-15** (31.10.2026): açık yasak yok; gerekçe 12/1 ve 27'deki denetim konumu (CLAUDE.md altın kural 6). Atıf "kullanıcı kararı KE-15 (gerekçe md. 12/1, 27/2-3)" diye basılır. Okul kartındaki müdür, veli olsa da eklenemez |
| `yonetim_kurulu.gorev_suresi_yil` | 1 yıl | U | [12/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Dönem bitişi takvimde |
| `yonetim_kurulu.gorev_bolumu_gun` | 7 gün | U | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Seçimden ve yedek çağrısından sonra; **yorum:** "ilk hafta" = izleyen 7 takvim günü (§15 KE-12) |
| `yonetim_kurulu.gorevler` | başkan · başkan yardımcısı · muhasip · sekreter, her biri tek asıl üyede | S (hb) | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Tekillik (müşterek imza buna bağlı) |
| `yonetim_kurulu.secilme_siniri` | en fazla 4 | U | [12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F1c | Başkan **ve üyeler** (OYS yalnız başkanı sayıyordu, S-4); kişi geçmişi eksikse "tamamlanacak" (R5), engel değil |
| `yonetim_kurulu.tek_birlik` | başkan ve YK üyeleri aynı anda başka bir birlik yönetiminde görev alamaz | U | [12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) (2. cümle) | 09.02.2012 | F1c | Hüküm (KM-8). Program başka birlikteki görevi bilemez: "başka birlikte görevli" işareti (`eligibility_bar = VAR`, dayanak `TEK_BIRLIK_12_4`) konursa seçimde uyarı + gerekçe, görevdeki üyede düşürme önerisi. Beyan almak okul uygulamasıdır (§6 giriş tablosu). 2. cümle şerhsiz (MA-17) |
| `uyelik.suc_engeli` | 12/5'teki suçlardan ceza alan ya da yargı kararıyla tespit edilen kişi YK'de ve harcama komisyonunda (12/5), DK'de (14/7) görev alamaz; sonradan anlaşılırsa görevi tespit tarihinde sona erer | U | [12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 01.12.2023 | F1c | Hüküm (KM-8). "Engel tespit edildi" işareti (`OrganMembership.eligibility_bar = VAR`, dayanağı şifreli `SUC_12_5_14_7`) ve tespit tarihi konursa seçimde uyarı + gerekçe, görevdeki üyede düşürme önerisi (tespit tarihiyle; düşme türü `DIGER` — tür suçu ele vermez, KVKK md. 6/1). Beyan okul uygulamasıdır; beyan içeriği ve adli sicil verisi tutulmaz (KVKK). v1 kimliği `uyelik.suc_engeli_beyani` idi (yayımlanmadan değişti) |
| `uyelik.ayrilan_veli_devam` | YK üye sayısı toplantı yeter sayısının (4) altına düşerse YK'deki velinin ve 18 yaşını doldurmuş kursiyerin üyeliği olağanüstü GK'ye kadar sürer | U | [7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) | 01.12.2023 | F1c | "Öğrencisi ayrıldı" ya da "eğitimini tamamladı" düşürme önerisinde denetlenir; kursiyer 2023 ek ibaresiyle (MA-16) |
| `yonetim_kurulu.yedek_cagirma` | oy sırasıyla | U | [13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c | Sıra dışı çağrı gerekçe ister (yedeğin çekilmesi vb.); çağrı yazısı E65 |
| `yonetim_kurulu.toplanti_yeter_sayi` | en az 4 asıl üye | S (hb) | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Altında toplantı "yapılamadı" kaydedilir, karar girilemez |
| `yonetim_kurulu.karar_yeter_sayi` | en az 3 kabul oyu | S (hb) | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Altında karar "alınmadı" |
| `yonetim_kurulu.toplanti_sikligi` | ayda bir (eğitim-öğretim yılı içinde) | U | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F3 | Ders yılı takviminden; toplantısız ders ayı → uyarı (`eksik_veri: sapma`); toplantı günü dönem ayarından |
| `yonetim_kurulu.devamsizlik_siniri` | üst üste 3 özürsüz | U | [13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Toplantılar üzerinden sayılır (kayıtlar değil, S-19); program öneri üretir, düşürme kullanıcı onayıyla; yalnız YK |
| `yonetim_kurulu.olaganustu_cagri_ay` | 1 ay | U | [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F3 | YK yedeklerle karar yeter sayısının (3) altına düşünce; çağrı başkan ya da okul müdürü (E05) |

#### 6.4.3 Denetleme Kurulu

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `denetleme_kurulu.asil_uye` | 3 | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 09.02.2012 | F1c | "Üç asıl" 2023 ek ibaresinin dışında, 2012'den (MA-17) |
| `denetleme_kurulu.yedek_uye` | 3 | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 09.02.2012 | F1c | — |
| `denetleme_kurulu.koltuklar` | veli/18+ kursiyer 1+1 (GK seçer, açık oy) · öğretmen 2+2 (öğretmenler kurulu seçer) | S (hg) | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 01.12.2023 | F1c | Plan §2.4 "DK bileşimi". Hayırsever veli koltuğuna giremez (OYS S-8); öğretmen koltukları GK oylamasına girmez (§7.1 [S]). Öğretmen yetmezse il/ilçe MEM onayıyla başka okulun öğretmeni (onay no alanı) |
| `denetleme_kurulu.gorev_bolumu_gun` | 7 gün | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | GK'den sonraki ilk hafta; **yorum** KE-12. "İlk hafta" 2012'den; 2023 ek ibaresi ve ek cümlesi başka konuda (MA-17) |
| `denetleme_kurulu.gorev_suresi_yil` | 1 yıl | U | [14/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | — |
| `denetleme_kurulu.baskan_secilme_siniri` | en fazla 3 | U | [14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | Yalnız DK başkanlığı sayılır; YK sayacından ayrı |
| `denetleme_kurulu.inceleme_yilda_en_az` | 2 | U | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F4 | Ara raporlar YK'ye, nihai rapor GK'ye; plan tarihleri dönem ayarından |
| `denetleme_kurulu.yk_uyesi_olamaz` | evet | S (kk) | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) (gerekçe) | 01.12.2023 | F1c | **Kullanıcı kararı A-2** (31.10.2026): aynı kişi aynı dönemde YK'de ve DK'de olamaz. Yönetmelikte açık yasak yok; 14/4 gerekçedir (denetleyen ile denetlenenin ayrılığı), dayanak değil. Atıf "kullanıcı kararı A-2 (gerekçe md. 14/4)". Yürürlük paket metninin tarihi: Ekim 2026 genel kurulu da kapsanır (MA-1) |
| `denetleme_kurulu.ogretmen_gorevlendirme_ay` | 4 aydan fazla → yedek | U | [14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | Başka kurumda görevlendirme süresi girilir |

#### 6.4.4 Birlik temsilcileri

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `temsilci.odul_disiplin_kurulu` | 1 veli + 1 yedek | U | [OKY 185/1-ç](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185); [OKY 186/1](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-186) | 07.09.2013 | F1c | `kosul`: `okul.kademe` ∋ `ORTAOGRETIM` |
| `temsilci.davranis_degerlendirme_kurulu` | 1 veli | U | [OÖİKY 57/2-c](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57) | 26.07.2014 | F1c | `kosul`: `okul.kademe` ∋ `ORTAOKUL` |
| `temsilci.sosyal_etkinlikler_kurulu` | 1 veli | U | [SEY 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6) | 08.06.2017 | F1c | Kurul birliğin etkinliklerini de inceler ([OAB Yön. md. 6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)) (MA-18) |
| `temsilci.kontenjan_komisyonu` | 1 veli | U | [OKY 25/1-a](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25) | 13.09.2014 | F1c | `kosul`: `okul.kademe` ∋ `ORTAOGRETIM` |
| `temsilci.rpd_yurutme_komisyonu` | 1 temsilci | U | [RPD 16/2-e](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16); RPD 16/5 | 14.08.2020 | F1c | Komisyonun diğer üyelerini her ders yılı başında öğretmenler kurulu belirler (16/5); **yorum:** YK kararı (E01, E03) bu satırda öneri ve bilgi niteliğindedir (MA-18). Hayat boyu öğrenme kurumlarında yok (16/3) |
| `temsilci.tasimaci_tespit_komisyonu` | birlik başkanı | U | [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3); [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) | 25.10.2017 | F1c | Doğrudan üyelik; seçim yok |
| `temsilci.muhammen_bedel_komisyonu` | birlik başkanı | U | [19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) | 01.12.2023 | F1c | Komisyonu valilik/kaymakamlık kurar (bilgi satırı) |
| `temsilci.kiralama_ihale_komisyonu` | birlik başkanı | U | [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F1c | Bilgi satırı; hısımlık yasağı `kantin.hisimlik_derecesi` |
| `temsilci.pay_dagitim_komisyonu` | il/ilçe MEM hesabındaki payları dağıtan komisyonda iki birlik başkanı (mülki amir onayıyla) | U | [17/1-b-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c | Yalnız kayıt: başkan bu komisyona seçildiyse temsilci satırı (E03). **Yorum:** bent (b) altında; il/ilçe hesabına yatan bütün paylar için uygulanır (KE-17 gibi) (MA-9) |

`temsilci.kampus_yonetimi` ([13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) v1'den çıkarıldı:
kampüsteki okul kapsamdadır (§3.5) ve okul kartında `in_campus` alanı vardır, ama hüküm ("ihtiyaç hâlinde … başkan veya
yönetim kurulu üyelerinden biri görevlendirilir") sayısal ya da süreli bir değer taşımaz; kural gerekmez (UY-12; KE-24).
Temsilciler çizelgesinde (E03) `KAMPUS_YONETIMI` kayıt satırı `in_campus` doğruyken görünür.

#### 6.4.5 Gelir, bağış, makbuz, etkinlik

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `bagis.elden_yatirma_is_gunu` | 5 iş günü | U | [16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F1c (F3) | **Yorum:** süre kabulü izleyen iş gününden başlar (MA-16); iş günü takvimi okul ayarından; kasa sayacı |
| `bagis.kayit_doneminde_toplanmaz` | kayıt-kabul ve diploma döneminde bağış yok | U | [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15); [G.2011/40 (1-2)](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) | 09.02.2012 | F3 | Dönem tarihleri okul ayarı; diploma dönemi G.2011/40'tan; bağış girişinde uyarı |
| `gelir.proje_protokol_ucret_yasak` | Bakanlık proje/protokol faaliyetinden ücret yok | U | [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) | 09.02.2012 | F4 | Etkinlik kaydındaki "Bakanlık proje/protokolü kapsamında değil" beyanından (`SocialEvent`, §5; EK-9); kapsamdaysa ücret geliri → uyarı |
| `bagis.sartli_amac` | amacı dışında kullanılamaz | S (hb) | [16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F3 | Şartlı bağış alt hesabı; alt hesaptan çıkan gider amaca bağlanmadan kaydedilmez, alt hesap eksiye düşmez |
| `bagis.ayni_teslim` | nakde çevrilemeyen → okul müdürlüğüne belge karşılığı; VİF | U | [16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [TMY 16/1](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) | 10.10.2024 | F3 | VİF no/tarih boşsa uyarı; VİF'i TKYS'de taşınır kayıt yetkilisi düzenler; "VİF" TMY 2024'ün terimi (MA-17) |
| `makbuz.cilt_yaprak` | 50 asıl + 50 koçan | U | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F1c (F3) | Cilt kaydında sıra aralığı 50'den farklıysa uyarı |
| `makbuz.seri_cilt_sira_tekil` | seri + cilt + sıra tekil | S (hb) | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F3 | Numara tekilliği; yaprak bir kez kullanılır ya da iptal edilir (E67) |
| `makbuz.muhur_ve_karar_kaydi` | kurum mührü + koçan seri no'ları karar defterine | U | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); 16/7 | 09.02.2012 | F3 | Mühür tarihi ya da karar no boşsa cilt kullanıma açılırken uyarı |
| `etkinlik.onay_zinciri` | SEK incelemesi → okul müdürü uygunluk görüşü → il/ilçe MEM onayı | U | [6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) | 01.12.2023 | F4 | Her aşamanın tarih/sayı alanı `SocialEvent`'te (§5; EK-9) |
| `etkinlik.ders_saatleri_disinda` | üçüncü kişilerin okulda düzenlediği gelir getirici etkinlik eğitim-öğretim saatleri dışında | U | [15/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) | 09.02.2012 | F4 | `kosul`: `etkinlik.duzenleyen` = `UCUNCU_KISI` (MA-8). Birliğin kendi etkinliğinde uyarı yok; bilgi notu: sosyal etkinlikler "öncelikle ders saatleri dışında", zorunlu hâllerde içinde ([SEY 5/3](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-5)) |

#### 6.4.6 Harcama, bildirim, duyuru, vergi, denetim

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `harcama.yk_karari` | her harcama YK kararıyla | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Dönem başı genel karar (okul ayarı) ve sürekli ödeme dosyasının bağlı kararı (R6) gerekçe sayılır |
| `harcama.okul_yazili_talep` | okul ihtiyacında okul yönetiminin yazılı talebi | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Talep müdürün yazısıdır (E25, müdür hesabından; M-11); kâğıtta gelen talebin gelen evrak kaydı (`DocumentRecord`) da yeter (SU-10) |
| `harcama.alim_komisyonu_en_az` | 3 kişi | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F1c | `ALIM_KOMISYONU` organı F1c'de açılır (plan §2.3); organ ekranında ve harcama dosyasında (F4) denetlenir; küçük alımda eksik halka gerekçeyle (§15 A-11) (MA-7) |
| `harcama.alim_komisyonu_uyeleri` | YK üyeleri; uzmanlık gerektiren işlerde birlik üyeleri | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F1c (F4) | YK üyesi olmayan üyede "uzmanlık gerektiren iş" işareti aranır. Suç engeli hükmü `uyelik.suc_engeli`'de, beyan okul uygulaması (KM-8). Komisyonun tek kaynağı `OrganMembership(ALIM_KOMISYONU)` (UY-20) |
| `harcama.musterek_imza` | başkan + muhasip (başkan yoksa başkan yardımcısı) | U | [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Ödeme kaydındaki imzacılar; ödeme talimatı iki imzalı |
| `harcama.tasinir_kaydi` | okul adına kayıt; VİF örneği harcama belgesine | U | [18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [TMY 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41) | 10.10.2024 | F4 | 18/3'teki mülga TMY atfı TMY 41/2 ile yeni TMY'ye; "taşınır işlem fişi" = VİF (TMY 2024; MA-17) |
| `harcama.organ_uyesine_odeme` | YK/DK üyesine huzur hakkı vb. ödeme yok | U | [25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) | 09.02.2012 | F4 | Alıcı organ üyesiyse uyarı + gerekçe; `toplu_gerekce: false`. 2022 tarihli değişik ibare aynı fıkranın SEY atfıdır (MA-17) |
| `bildirim.aylik_mudur` | her ayın sonu, yazılı | U | [18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Ay bitti, bildirim yok → uyarı (`eksik_veri: sapma`) |
| `duyuru.butce` | ilan panosu + internet sayfası | U | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F4 | GK'de görüşülen bütçe; kanıt alanları |
| `duyuru.gelir_gider_donemlik` | her dönem en az 1, pano + internet | U | [13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F4 | Dönem sınırları ders yılı takviminden (`eksik_veri: sapma`) |
| `vergi.damga_harc_muafiyeti` | md. 6 kapsamındaki işlemler ve kâğıtlar damga vergisi ve harçtan muaf | S (hd) | [24/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24) | 09.02.2012 | F4 | Program birlik kâğıdında damga vergisi hesaplamaz (D1). Kiracının sözleşme damga vergisi bilgi metnidir (§6.4.11) |
| `denetim.mem_yilda_en_az` | 1 | U | [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26) | 09.02.2012 | F4 | Pano hatırlatması; denetim kaydı `InspectionRecord` |

#### 6.4.7 Kantin: arz bedeli, pay dağılımı, aylık kira

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `arz_bedeli.kira_oran` | 0,03 (gayri safi) | S (hd) | [17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); [EK-2 md. 7/1. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 09.02.2012 | F1c (F3) | Kiracı öder; `kosul`: `okul.kantin` = `KIRAYA_VERILIYOR`. Fiilî ödeme hesaplanandan farklıysa kaydedilir, fark uyarı (D1) |
| `arz_bedeli.isletme_oran` | 0,01 (gayri safi hâsılat) | S (hd) | [17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F5) | Birlik öder; `kosul`: `BIRLIKCE_ISLETILIYOR` |
| `arz_bedeli.donem_ay` | 3 ay | S (hd) | [17/1-a-1, b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); EK-2 md. 7/1. paragraf | 09.02.2012 | F3 | Dönem başlangıcı DOĞRULANMADI-2 (varsayılan takvim çeyreği, KE-2); EK-2'deki peşin ödeme sözleşme seçeneğidir, sapma değil |
| `arz_bedeli.sozlesme_vade_gunu` | izleyen ayın 10'u (dâhil) | U | [EK-2 md. 7/1. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F1c (F3) | 11-20: "sözleşme vadesi geçti" (plan §1.8 kararı) |
| `arz_bedeli.yonetmelik_vade_gunu` | izleyen ayın 20'si (dâhil) | U | [17/1-a-1, b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F3) | 20'sinden sonra: "Yönetmelik süresi de geçti"; tatil kayması yok (KE-18) |
| `arz_bedeli.takip_sorumlulari` | okul müdürü + birlik başkanı | U | [17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F3 | İzleme çizelgesinde iki imza (E24). **Yorum:** bent (b) altında; kiraya vermede de uygulanır (KE-17 gibi) (MA-8). §7.6'da [U] |
| `arz_bedeli.diger_tahsilat_oran` | 0,03 | S (hd) | [17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F5 | Tahliye cezası, fesih tazminatı, kısa süreli kullanım bedeli; kalan 17/1'e göre dağıtılır. **Yorum:** bent (b) altında ama konusu kira (KE-17) |
| `pay_dagitimi.genel` | birlik 0,80 · ilçe 0,10 · il 0,10 | S (hd) | [17/1-a-2, b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); [EK-2 md. 7/2. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 09.02.2012 | F1c (F3) | Taban: gayri safi − arz bedeli; `kosul`: `BUYUKSEHIR` ya da `DIGER` |
| `pay_dagitimi.il_merkezi` | birlik 0,80 · ilçe 0 · il 0,20 | S (hd) | [17/1-a-2, b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F3) | `kosul`: `IL_MERKEZI_BUYUKSEHIR_DEGIL` (OYS `is_metropolitan` düzeltmesi, S-17); **yorum:** taban KE-13 |
| `pay_dagitimi.isletme_net_tabani` | gayri safi − arz − zorunlu işletme giderleri − kanuni giderler | S (hd) | [17/1-b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F5 | `kosul`: `BIRLIKCE_ISLETILIYOR` |
| `kira.odeme_gunleri` | her ayın 5-15'i | U | [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4); EK-2 md. 7/2. paragraf | 01.12.2023 | F3 | Kira ve payların yatırılması aynı pencerede; 4'ünde ve 16'sında uyarı |
| `kira.yariyil_ayi_carpani` | 0,5 | S (hd) | [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4) | 01.12.2023 | F3 | Yarıyıl tatilinin yapıldığı ayın beklenen kirası yarımdır (ders yılı takviminden); fiilî tam ödeme kaydedilir, fark uyarı |
| `kira.ay_sayisi` | 9 ya da 12 | U | [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4); [19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) | 01.12.2023 | F3 | Sözleşmeden girilen değer (D1): 9 ve 12 dışındaysa uyarı + gerekçe. "Dokuz ay; Haziran-Ağustos yok" yalnız EK-2 md. 4'te; 19/3 aylık bedelin açık günlerle belirlenmesidir (MA-8) |
| `kira.mucbir_sebep_indirimi` | ara verilen günlerin kirası düşülür | U | [EK-2 md. 7/3. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F5 | Hesap biçimi yazılı değil → indirim elle ve gerekçeyle |
| `kira.ust_uste_odememe_fesih` | 2 ödeme (iki defa üst üste ödenmeyen aylık kira) | U | [EK-2 md. 7/4. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F5 | Birim `adet` (ödeme), ay değil (MA-16); mücbir sebep dışında; fesih önerisi; fesih bildirimi E71 |
| `kantin.kdv_istisnasi` | kira tahsilatında KDV hesaplanmaz | S (hd) | [KDVK 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17) | 21.03.2018 | F3 | `kosul`: `KIRAYA_VERILIYOR` |

#### 6.4.8 Kantin: kiralama, sözleşme, belgeler

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `kantin.kiralama_usulu` | pazarlık (2886 md. 51/g) | U | [20/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51) | 09.02.2012 | F5 | Girilen usul (D1): pazarlık dışında bir usul kaydedilirse uyarı + gerekçe; v1'de sertti, "başka yöntem seçeneği" artık var |
| `kantin.kiralama_onay_kaydi` | ihale komisyonu kararının onay makamı, tarihi ve sayısı kaydedilir | U | [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) (bağlam) | 01.12.2023 | F5 | **Kullanıcı kararı D4** (31.10.2026): kantinde onay kaydı olmadan kesinleştirme uyarı + gerekçe; `toplu_gerekce: false`. Korpusta onayı açıkça isteyen hüküm yok (2886 md. 42 mülga; kiralama 51/g pazarlığıyla); 20/3 yalnız komisyonun valilik/kaymakamlıkça kurulduğunu söyler. Uyarı metni "Yönetmelik gereği" demez. Serviste karşılığı sert (`servis.olur_olmadan_kesinlesmez`) |
| `kantin.istekli_belge_sarti` | birinci kademe: kantin işletmeciliğinden ustalık ya da iş yeri açma belgesi · ikinci kademe (yalnız hiçbir istekli birinci kademe belge taşımıyorsa): 20/4 2. cümledeki alan/dal belgeleri, diploma, kalfalık, kurs bitirme | U | [20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 01.12.2023 | F5 | Uyarı iki hâlde: istekli hiç belge taşımıyor · birinci kademe belgeli istekli varken başka istekli ikinci kademe belgeyle katılıyor (MA-6). Uyarı + gerekçe (plan §1.8); OYS'de sertti ve kademeyi taşımıyordu |
| `kantin.esnaf_odasi_belgesi` | kayıtlı kantin yok + yasaklama yok belgesi | U | [20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F5 | OYS'de yoktu |
| `kantin.hisimlik_derecesi` | 2. dereceye kadar kan ve kayın | S (hg) | [20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F5 | Komisyon başkan ve üyeleri + YK + DK üyeleri; hukuken geçersiz katılım (plan §1.8). Engel `Bidder.participation_bar = VAR` ile kaydedilir, dayanak (`HISIMLIK_20_8`) şifreli |
| `kantin.istekli_suc_engeli` | 12/5 suçlarını işledikleri yargı kararıyla tespit edilenler ihaleye katılamaz, kiraya verilen yerde istihdam edilemez | S (hg) | [20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 01.12.2023 | F5 | `Bidder.participation_bar = VAR` olan istekli seçilemez. Engel var/yok açık alandadır; hangi bentten geldiği (`SUC_20_11` · `HISIMLIK_20_8`) şifreli `participation_bar_basis`'tedir, okuması erişim günlüğüne düşer ([KVKK md. 6/1](../mevzuat/6698-kvkk.md#madde-6); §5.2.9). Tespitin yöntemi okulun ve komisyonundur (§6 giriş tablosu; KM-8); içerik tutulmaz. Atıf 20/11 (OYS 12/5 diyordu, S-8) |
| `kantin.calisan_niteligi` | ustalık, iş yeri açma, kalfalık, diploma ya da kurs belgesinden biri | U | [20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [EK-2 md. 19](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-19) | 09.02.2012 | F5 | Belgesiz çalışan → uyarı. Portör ve adli sicil **çalışandan** istenir, istekliden değil (S-8) |
| `kantin.yillik_yenileme` | 12 ay: işletme faaliyet belgesi + çalışan adli sicil ve arşiv kaydı | U | [20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | 09.02.2012 | F5 | **Yorum:** "her yıl" = belge tarihinden 12 ay (MA-16); içerik tutulmaz |
| `kantin.calisan_hijyen_belgesi` | belgesiz çalıştırılamaz; belge hizmet süresince geçerli | U | [HEY 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5); [HEY 6/3](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-6) | 05.07.2013 | F5 | Süre sayacı yok |
| `kantin.kisa_sureli_bedel_birimi` | saat · gün · hafta | U | [19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) | 09.02.2012 | F5 | Bedeli muhammen bedel komisyonu belirler (kayıt) |
| `kantin.isletmede_vergi_uyarisi` | VUK hükümleri uygulanır | U | [23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | 09.02.2012 | F1c | `kosul`: `BIRLIKCE_ISLETILIYOR`; okul kartında (F1b) seçilince görünen uyarı F1c'de pakete bağlanır |
| `kira.sozlesme_en_fazla_yil` | 5 yıl | U | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 6/2. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) | 01.12.2023 | F5 | Takvimle hesap (5 × 365 değil, S-18); uyarı (KE-6). EK-2 md. 6/1. paragrafta süre boştur |
| `kira.toplam_en_fazla_yil` | 20 yıl | U | [21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii) | 01.12.2023 | F5 | Geçici md. 4 istisnası (20 yılı geçenler bitime kadar) bilgi notu |
| `kira.yirmi_yil_taban_tarihi` | 31.05.2005 | S (hd) | [G.2024/35 III-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-1) | 03.01.2024 | F5 | Daha önceki ilk sözleşmeler bu tarihten sayılır. Programın 20 yıl hesabının girdisi; sonucu yalnız `kira.toplam_en_fazla_yil` uyarısına girer, kayıt engellemez |
| `kira.yirmi_yil_yeniden_baslangic` | ilanlı ya da çok istekli pazarlık yeni başlangıç; teklif-kabul yenilemesi değil | S (hd) | [G.2024/35 III-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-2); [III-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-3) | 03.01.2024 | F5 | Sözleşme zinciri (`OabContract`) türüyle; 20 yıl hesabının girdisi |
| `kira.yirmi_yil_ilave` | dondurulan süre + 540 gün (16.03.2020-06.09.2021) | S (hd) | [G.2024/35 III-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-4); [EK-2 md. 21](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-21) | 03.01.2024 | F5 | 540 genelgede yazılı sabittir, iki ucu sayılmış; tarih farkından (539) hesaplanmaz (MA-15) |
| `kira.yer_teslimi_gun` | 15 gün (imzadan) | U | [21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) (2. cümle) | 01.12.2023 | F5 | Gecikmede kiracının 15 gün içinde 10 günlük noter ihtarı hakkı (bilgi) |
| `kira.imzadan_once_teslim_yok` | sözleşme taraflarca imzalanmadan yer teslimi yapılamaz | U | [21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) (1. cümle) | 01.12.2023 | F5 | Teslim tarihi imzadan önceyse uyarı + gerekçe; teslim tarihi tutanaktan girilen değerdir (D1). §5.2.9 ve §7.6'da [U] (EK-5) |
| `kira.tufe_artisi` | 2. yıldan; TÜFE on iki aylık ortalamalara göre % değişim | U | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 6/1. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) | 01.12.2023 | F5 | Program yasal artışı hesaplar, sözleşmede uygulanan artışı kaydeder; farklıysa uyarı + gerekçe (D1). `IndexRate.value` bu anlamda sabitlenir; ilk yıl ihale bedeli. TÜFE işlemi servis sözleşmesinde yoktur (yapısal) |
| `kira.ogrenci_degisim_esigi` | %25 azalış ya da artış | U | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | 01.12.2023 | F5 | Muhammen bedelin yeniden tespiti önerisi |
| `kira.kesin_teminat_oran` | 0,06 (yıllık kira) | U | [EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) | 01.12.2023 | F5 | Program yasal tutarı hesaplar; sözleşmedeki teminat farklıysa uyarı + gerekçe (D1); olay tarihi imza |
| `kira.tahliye_gunluk_ceza_oran` | 0,03 (aylık kira, her geçen gün) | S (hd) | [EK-2 md. 22/1. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) | 01.12.2023 | F5 | Program cezayı hesaplar; tahsil edilen farklıysa kaydedilir, fark uyarı. Arzı `arz_bedeli.diger_tahsilat_oran` |
| `kira.fesih_tazminati` | cari kiralama döneminin (9 ya da 12 aylık) kira bedeli tazminat; kesin teminat gelir kaydı; fesihten sonraki döneme alınmış kira tazminata mahsup | S (hd) | [22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22); [EK-2 md. 22/2. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) | 01.12.2023 | F5 | 22/4'te sayılan fesih hâllerinde. Program tutarı hesaplar; fiilî tahsilat farkı uyarı; arzı `arz_bedeli.diger_tahsilat_oran` (MA-9) |
| `kira.fesih_ihtar_gun` | 15 gün | U | [22/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) | 09.02.2012 | F5 | Yazılı bildirimden (E47); süre dolmadan fesih → uyarı |
| `kira.bakanlik_tahliye_gun` | 15 gün (tebligattan) | U | [EK-2 md. 18](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-18) | 01.12.2023 | F5 | Sözleşmeye aykırı işletmede Bakanlık ihtiyacı hâlinde; süre sayacı, bilgi düzeyinde (MA-9) |
| `kira.yeniden_kiralama_bildirim_ay` | bitişten en az 2 ay önce (işletmeci) | U | [G.2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2) | 03.01.2024 | F5 | — |
| `kira.yeniden_kiralama_cevap_gun` | 15 gün | U | [G.2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) | 03.01.2024 | F5 | Birliğin yazılı cevabı (E41) |
| `kira.muhammen_bedel_teklif_ay` | bitişten en az 1 ay önce | U | [G.2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5) | 03.01.2024 | F5 | Muhammen bedel komisyonunun tespiti |
| `kira.tufe_bildirimi` | yenilenen kira il/ilçe MEM'e bildirilir | U | [G.2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) | 03.01.2024 | F5 | E45 |
| `kira.milli_emlak_ornegi` | sözleşme örneği millî emlak birimine (okul müdürlüğü) | U | [21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | 01.12.2023 | F5 | Gönderim tarihi/sayısı alanı (E44) |
| `kira.ihaleden_yasaklama_yil` | 1 yıl | U | [22/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22); [2886 md. 84/1. paragraf](../mevzuat/2886-devlet-ihale-kanunu.md#madde-84) | 09.02.2012 | F5 | Yasaklama kararını Bakanlık verir; kayıtlı yasaklı istekli → uyarı |

#### 6.4.9 Servis

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `servis.ilan_en_az_gun` | 7 gün (dosya teslim gününden önce) | U | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | 30.05.2018 | F6 | OYS yalnız kesinleştirmede bakıyordu |
| `servis.ilan_kanallari` | ilan tahtası + okul web sitesi; tutanak | U | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | 30.05.2018 | F6 | E49 |
| `servis.komisyon_bilesimi` | müdür (başkan) + birlik başkanı + 1 öğretmen (+1 yedek) + 2 veli (+2 yedek) + varsa vakıf temsilcisi | U | [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3); [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) | 25.10.2017 | F6 | Yedekler sayılır (OYS saymıyordu); görevlendirme yazısı E73 |
| `servis.komisyon_karar_cogunlugu` | çoğunluk; oylar eşitse başkanın bulunduğu taraf | S (hb) | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) | 30.05.2018 | F6 | Karar sonucu oylardan hesaplanır; "oy birliği ile" sabit basılmaz (S-7). v1'deki `servis.komisyon_karari` ikiye bölündü (MA-4) |
| `servis.komisyon_cekimser_ve_serh` | çekimser kalınamaz; muhalif üye karşı oy gerekçesini kararın altına yazıp imzalar | U | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) | 30.05.2018 | F6 | Usul hükmü: çekimser oy ya da şerhsiz muhalif varsa uyarı + gerekçe; tutanak olduğu gibi girilir (MA-4). §7.7'de [U] |
| `servis.degerlendirme_yontemi` | komisyon değerlendirmesi (8/2); EK-3 puanlaması yalnız itiraz ya da yeni okulda ilk kez | U | [U-E 8/2-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | OYS varsayılanı ters çevrilir (S-7); "en düşük teklif" yok |
| `servis.ek3_puanlama` | 5 kriter, kademe tablosu | U | [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | 30.05.2018 | F6 | Kademe tablosu paketten gelir; girilen puan kademe dışındaysa uyarı + gerekçe (D1; MA-5). İkili kriter yalnız 4. kriterdir; 2. kriter 5 ya da 1, 3. kriter 5, 3 ya da 0. Kriter 4'ün basılı adı KE-8 |
| `servis.ek3_kriter_azami_puan` | 5 (toplam 25) | U | [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | 30.05.2018 | F6 | Puan sınırı uyarı (plan §1.8); OYS'de sertti |
| `servis.olur_olmadan_kesinlesmez` | mülki amir onayı | S (hg) | [OSAY 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4); [U-E 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 25.10.2017 | F6 | Hukuken geçersiz işlem (plan §1.8; D4: serviste sert). Onaya sunma yazısı E76 |
| `servis.mulki_amir_onay_is_gunu` | 5 iş günü | U | [U-E 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | Bekleme sayacı |
| `servis.teblig_is_gunu` | 5 iş günü (onaydan) | U | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | Tebliğ yazısı E77 (Tebligat Kanunu hükümlerince) |
| `servis.sozlesme_imza_gun` | 10 gün (tebliğden) | U | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | İmzalanmazsa `servis.yeniden_cikma` |
| `servis.sozlesme_en_fazla_yil` | 3 eğitim öğretim yılı | U | [OSAY 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); [U-E 8/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 25.10.2017 | F6 | U-E "dönem" der; Yönetmelik "yıl" der ve üst normdur; esas süre bir yıl |
| `servis.yeniden_cikma` | başvuru yok · belge uygun değil · sözleşme imzalanmadı → aynı usulle yeniden | U | [U-E 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | OYS "tek katılımcı" tutanağının yerine (S-8) |
| `servis.ucret_tarifesi` | ücret belediye fiyat tarifesine bağlı; birlik ve komisyon fiyat belirlemez | U | [OSAY 5/2-d](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-5); [U-E 10/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | 19.08.2025 | F6 | Servis sürecinde muhammen bedel ya da fiyat alanı yoktur (yapısal; uç bilinmeyen alanı reddeder). Sözleşmeye girilen ücretin tarife kaynağı (karar tarihi/sayısı) boşsa uyarı (D1; v1'de sertti). OSAY 5/2-d (yeniden düzenleme 19.08.2025) 5216/5393 tarifesine bağlar; U-E 10/2'deki 5362/62 atfı eski |
| `servis.taksit_en_fazla` | 9 | U | [U-E EK-2 md. 6/a](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) | 30.05.2018 | F6 | Taksit sayısı uyarı (plan §1.8); ücreti veli taşımacıya öder, birliğin alacağı değil (KE-14) |
| `servis.yariyil_ucret_yok` | yarıyılda ücret istenmez | U | [U-E EK-2 md. 6/c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) | 30.05.2018 | F6 | Sözleşme metni ve bilgi |
| `servis.muhtac_ogrenci` | araç başına 1 öğrenci ücretsiz | U | [U-E EK-2 md. 8/c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-8) | 30.05.2018 | F6 | Komisyon yazılı bildirir; ad evrakta (iç) |
| `servis.tasimaci_ilani` | sözleşmeden sonra pano + web | U | [U-E 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | 30.05.2018 | F6 | E56: ad/unvan, plaka, güzergâh; telefon, adres, T.C. kimlik no yok (D5) |
| `servis.arac_yasi_en_fazla` | 12 | U | [OSAY 4/1-f](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-4) | 29.11.2024 | F6 | Sözleşme içinde dolarsa o ders yılı sonuna kadar (2024 ek cümlesi) |
| `servis.arac_yasi_hesabi` | yaş, imal tarihinden sonra gelen ilk takvim yılı esas alınarak hesaplanır | S (hd) | [OSAY 4/1-f](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-4) (2. cümle) | 25.10.2017 | F6 | Program yaşı hesaplar; sonucu `servis.arac_yasi_en_fazla` uyarısına girer, kayıt engellemez (MA-10) |
| `servis.sofor_yasi` | 26 yaşından gün almış, 66 yaşından gün almamış | U | [OSAY 9/1-a](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.10.2017 | F6 | 31.12.2026'ya kadarki geçici "69" uygulaması korpusta yok → yalnız bilgi notu (DOĞRULANMADI-11) |
| `servis.sofor_belge_yili` | D ≥ 2 yıl · D1 ≥ 5 yıl | U | [OSAY 9/1-c](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 29.11.2024 | F6 | U-E 9/1-c'deki 5/7 yıl eski; Yönetmelik esas; B sınıfı süresi `servis.sofor_b_sinifi_sayilan_yil` |
| `servis.sofor_b_sinifi_sayilan_yil` | B sınıfında geçen süreden D için en fazla 1, D1 için en fazla 3 yıl sayılır | S (hd) | [OSAY 9/5](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 19.08.2025 | F6 | Program belge yılını hesaplarken sayar; sonucu `servis.sofor_belge_yili` uyarısına girer (MA-10) |
| `servis.sofor_psikoteknik_yil` | 5 yıl | U | [OSAY 9/1-ç](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.10.2017 | F6 | Belge tarihi + 5 yıl |
| `servis.saglik_raporu_ay` | 12 ay (şoför ve rehber personel) | U | [OSAY 9/1-c, 9/2-ç](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 29.11.2024 | F6 | **Yorum:** "her yıl" = rapor tarihinden 12 ay (MA-16); varlık + tarih; içerik tutulmaz |
| `servis.rehber_yasi` | 22 yaşını doldurmuş, 61 yaşından gün almamış | U | [OSAY 9/2-a](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.08.2021 | F6 | — |
| `servis.tuzel_kisi_tescil_orani` | tüzel kişide taşıtların en az 1/3'ü tüzel kişi adına tescilli | U | [OSAY 8/3](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); [U-E 6/1-ç](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6); [U-E EK-1 md. 7/f](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1-madde-7) | 19.08.2025 | F6 | Girilen araç tescillerinden oran; altındaysa uyarı (MA-10) |
| `servis.ozmal_en_fazla_okul` | tüzel kişi aracı en fazla 2 okulda öz mal gösterilir | U | [U-E EK-1 md. 6/ç](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1-madde-6) | 30.05.2018 | F6 | Beyan edilen öz mal okul sayısından (MA-10) |
| `servis.fesih_ihtar_gun` | 15 gün (yazılı bildirimden) | U | [U-E 11/1-ç](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-11); [U-E EK-2 md. 7/f](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-7) | 30.05.2018 | F6 | İhtar E78, fesih E79; süre dolmadan fesih → uyarı. Kantindeki karşılığı `kira.fesih_ihtar_gun` (MA-10) |
| `servis.oda_belgesi_ayni_yil` | gerçek kişide oda kayıt belgesi işin yapıldığı yıl, tüzel kişide ilanın yapıldığı yıl içinde alınmış | U | [U-E 6/1-b, c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6) | 30.05.2018 | F6 | Belge tarihinden (MA-10) |

#### 6.4.10 Personel (sürüm 2; yalnız doğrudan işveren okullar)

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `personel.sgk_saklama_yil` | 10 yıl (ilgili yılı izleyen yıl başından) | S (hd) | [5510 md. 86 (2. fıkra)](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86); [5510 md. 12](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-12) | 16.06.2006 | F1c (F8) | Saklama sonu programca hesaplanır; bu tarihten önce imha önerisi çıkmaz. **Yorum:** birlik tüzel kişiliği olmayan işverendir, "kamu idareleri otuz yıl" hükmüne girmez |
| `personel.karsilik_ayrilir` | kıdem, ihbar vb. için karşılık | U | [6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) | 01.12.2023 | F8 | Tutar hesabı DOĞRULANMADI-10 (1475 md. 14 korpusta yok) |
| `personel.yillik_izin_gun` | hizmet ≤ 5 yıl: 14 · 5 yıl < hizmet < 15 yıl: 20 · hizmet ≥ 15 yıl: 26 gün; işçi 18 yaşında ya da küçük, 50 yaşında ya da büyükse en az 20 gün | U (`en_az`) | [4857 md. 53/4. paragraf a-c, 5. ve 6. paragraf](../mevzuat/4857-is-kanunu.md#madde-53) | 10.06.2003 | F8 | Asgari süredir, sözleşmeyle artırılabilir (6. paragraf): verilen izin altındaysa uyarı + gerekçe, üstündeyse uyarı yok (D1; MA-3). Basamak sınırları lafızdaki gibi: "beş yıl dahil", "onbeş yıl (dahil)". 2014 ek cümlesi (yer altı işleri) değeri değiştirmez |
| `personel.izin_bolumu_en_az_gun` | 10 gün | U | [4857 md. 56/3. paragraf](../mevzuat/4857-is-kanunu.md#madde-56) | 14.04.2016 | F8 | Anlaşmayla bölünürse bir bölüm |
| `personel.ihbar_hafta` | < 6 ay: 2 · 6 ay-1,5 yıl: 4 · 1,5-3 yıl: 6 · 3 yıldan fazla: 8 hafta | U (`en_az`) | [4857 md. 17/2. paragraf a-d, 3. paragraf](../mevzuat/4857-is-kanunu.md#madde-17) | 10.06.2003 | F8 | `kosul`: `personel.sozlesme_turu` = `BELIRSIZ_SURELI`; asgari, sözleşmeyle artırılabilir (MA-3) |

#### 6.4.11 Özet ve dışarıda kalanlar

**Sayım.** `OAB-2023.12`'nin hedef içeriği **157 kuraldır**; F1c'deki ilk revizyon (`r1`) bunların **53**'ünü taşır,
kalanlar §6.2-2'ye göre fazlarıyla girer.

| Alan | Kural | Sert | Uyarı | F1c'de giren |
|---|---|---|---|---|
| Genel kurul | 17 | 6 | 11 | 9 |
| Yönetim kurulu ve ortak üyelik | 17 | 5 | 12 | 15 |
| Denetleme Kurulu | 9 | 2 | 7 | 8 |
| Temsilciler | 9 | 0 | 9 | 9 |
| Gelir, bağış, makbuz, etkinlik | 10 | 2 | 8 | 2 |
| Harcama, bildirim, duyuru, vergi, denetim | 12 | 1 | 11 | 2 |
| Kantin: arz, pay, kira | 16 | 9 | 7 | 6 |
| Kantin: kiralama, sözleşme, belgeler | 31 | 7 | 24 | 1 |
| Servis | 31 | 4 | 27 | 0 |
| Personel | 5 | 1 | 4 | 1 |
| **Toplam** | **157** | **37** | **120** | **53** |

**Sertlerin dağılımı (§6.1'in dört kapalı gerekçesi).**

- **Hesap bütünlüğü 12:** yeter sayı ve karar hesabı 9 (GK yeter sayısının dört kuralı, ikinci toplantıda çoğunluk
  aranmaması, GK karar çoğunluğu, YK toplantı ve karar yeter sayısı, servis komisyonunda karar çoğunluğu) · tekillik ve
  alt hesap 3 (YK görev tekilliği, makbuz tekilliği, şartlı bağış alt hesabı).
- **Programın hesapladığı değer (D1) 18:** arz bedeli 4 (kira ve işletme oranı, üç aylık dönem, diğer tahsilatların
  arzı) · pay dağılımı 3 · yarıyıl ayı çarpanı · kantin kirasında KDV yok · damga ve harç muafiyeti · tahliye cezası ·
  fesih tazminatı · 20 yıl hesabı 3 · araç yaşı hesabı · B sınıfı sürenin sayımı · SGK belgesi saklama sonu.
- **Hukuken geçersiz işlem 5:** YK kişi türü, DK koltukları, kantin isteklisinde hısımlık ve suç engeli, serviste
  OLUR'suz kesinleştirme.
- **Kullanıcı kararı 2:** aynı kişinin YK ve DK'de bulunamaması (A-2), müdürün YK'ye girememesi (KE-15).

**F0-9 işlenişindeki değişiklik (31.10.2026; 146 → 157).** v1'in "hesap parametresi" saydığı 23 sert kuraldan 15'i
programın hesapladığı değer olarak sert kaldı; 8'i kullanıcının belgeden girdiği değer olduğu için uyarı oldu
(`kira.ay_sayisi`, `kira.kesin_teminat_oran`, `kira.tufe_artisi`, `kantin.kiralama_usulu`, `servis.ek3_puanlama`,
`servis.ucret_tarifesi`, `personel.yillik_izin_gun`, `personel.ihbar_hafta`; D1). `genel_kurul.gundem_degisikligi`
uyarı oldu (MA-16, EK-5). `servis.komisyon_karari` ikiye bölündü (MA-4). Eklenen 11 kural: `kira.fesih_tazminati`,
`kira.bakanlik_tahliye_gun`, `temsilci.pay_dagitim_komisyonu` (MA-9) · `servis.arac_yasi_hesabi`,
`servis.sofor_b_sinifi_sayilan_yil`, `servis.tuzel_kisi_tescil_orani`, `servis.ozmal_en_fazla_okul`,
`servis.fesih_ihtar_gun`, `servis.oda_belgesi_ayni_yil` (MA-10) · `kira.imzadan_once_teslim_yok` (EK-5) ·
`kantin.kiralama_onay_kaydi` (D4). Çıkarılan 1: `temsilci.kampus_yonetimi` (UY-12). Kimliği değişen 1:
`uyelik.suc_engeli_beyani` → `uyelik.suc_engeli` (KM-8). `r1`'e alınan 3: `genel_kurul.divan_uye_turleri`,
`harcama.alim_komisyonu_en_az`, `harcama.alim_komisyonu_uyeleri` (MA-7).

**DOĞRULANMADI — kural değil.** Aşağıdakiler korpusta dayanağı bulunamadığı ya da hüküm ayrıntıyı vermediği için
pakete girmez; program bunlar için mevzuat uyarısı göstermez, varsayılan davranış §15'teki karara bağlanır.

| # | Konu | Neden | Program ne yapar (varsayılan) |
|---|---|---|---|
| 1 | Olağanüstü GK'de çoğunluk aranmayan ikinci toplantı | [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) yeter sayıyı tekrarlar, 9/2'deki "otuz gün içinde çoğunluk aranmaksızın" cümlesini tekrarlamaz (S-3) | **Kapandı:** kullanıcı kararıyla md. 9/2 uygulanır, kural `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` olağanüstüyü de kapsar (§15 A-1) |
| 2 | Arz bedeli üçer aylık dönemlerinin başlangıcı | md. 17/1 ve EK-2 md. 7 başlangıcı söylemez | Takvim çeyreği; sözleşmede peşin seçeneği (KE-2) |
| 3 | Gecikme zammı oranı ve hesap yöntemi | 6183 md. 51 korpusta yok | Hesaplanmaz; oran ve tutar elle, "6183 md. 51'e göre" bilgi notu (KE-4) |
| 4 | Pay hesabında kuruş artığı | Yönetmelik sessiz | Hesap bütünlüğü kuralı: il ve ilçe payı yuvarlanır, birlik payı = net − il − ilçe (KE-3) |
| 5 | Aynı kişinin YK ve DK'de bulunması | Açık yasak bulunamadı (S-28) | **Kapandı:** kullanıcı kararıyla sert kural `denetleme_kurulu.yk_uyesi_olamaz` (§15 A-2; `dayanak_turu: kullanici_karari`) |
| 6 | Serviste hısımlık engeli | U-E ve OSAY'de hüküm bulunamadı | Kural yok; OYS'nin "uygulanmaz" testi korunur |
| 7 | Serviste birden çok taşımacı | U-E 10/3 çoğul der, usul yazmaz (S-16) | Model birden çoğa izin verir; kural yok |
| 8 | Kantin çalışanının portör/sağlık muayenesi periyodu | md. 20/6 "ilgili mevzuatında belirtilen sürelerde" der; [Okul Kantinlerine Dair Özel Hijyen Kuralları Yön. md. 14/1-h](../mevzuat/okul-kantinlerine-dair-ozel-hijyen-kurallari-yonetmeligi.md#madde-14) "periyodik olarak" der, süre vermez | Belge tarihi kaydı; süre uyarısı yok |
| 9 | Defter, koçan ve evrakın saklama süresi | md. 16/7, 23/6 Devlet Arşiv Hizmetleri Yön.'e gönderir; o Yönetmelik süreyi saklama planına bırakır ([md. 4/1-r](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-4), [md. 18](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-18)), MEB saklama planı korpusta yok | Silme ve imha yok (altın kural 4); yıl sonu arşiv paketi |
| 10 | Kıdem tazminatı karşılığının tutarı | 1475 md. 14 korpusta yok (4857 md. 120 yürürlükte bırakır) | Personel modülünde (sürüm 2) elle tutar |
| 11 | Şoför üst yaşında 31.12.2026'ya kadarki "69" uygulaması | İçişleri yazısı korpusa alınmadı (BENIOKU §6) | Kural 66 kalır; bilgi notu frontmatter'dan |
| 12 | "Yeter sayı sağlanamadı" tutanağının imzacıları | Mevzuat imzacı saymaz | KE-10 (E64) |
| 13 | Üyelerin %10'u başvurusunda çağrıyı kimin imzalayacağı | md. 9/6 yazmaz | KE-11 |
| 14 | Kantin denetim komisyonu (her ay; birlik yönetiminden bir veli) | Genelge 2020/8 A-1/a ve A-1/b metni korpusta **var**, hüküm açık; ama dosyada hiç `<a id>` çapası yok, atıf kilidi (D3) geçmez. BENIOKU §6'da da satır yok (MA-7) | Kural yok. Korpusa A-1/a ve A-1/b çapaları eklenince (BENIOKU §2 çapa eklemeyi yasaklamaz) iki kural girer: `temsilci.kantin_denetim_komisyonu` (birlik yönetiminden 1 veli; `r1`, F1c) ve `kantin.denetim_aylik` (her ay; F5) |
| 15 | Kantin ihale kararının mülki amir onayı | Korpusta açık hüküm bulunamadı (2886 md. 42 mülga; kiralama md. 51/g pazarlıkla) | **Kapandı:** kullanıcı kararı D4 ile uyarı kuralı `kantin.kiralama_onay_kaydi` (`dayanak_turu: kullanici_karari`; "Yönetmelik gereği" denmez) |
| 16 | 01.12.2023'ten önce imzalanmış kantin sözleşmelerinin imza günündeki EK-2 metni | Korpusta yalnız bugünkü EK-2 var (MA-12) | İmza gününe bağlı denetim yapılmaz (`denetlenmedi` + bilgi notu, §6.1 Erişim); teminat, ay sayısı, ödeme günü sözleşme alanından okunur; sonraki ödeme ve artış olayları bugünkü değerle denetlenir |

**Kural olmayan hüküm.** Eğitim kampüsü yönetimine birlik temsilcisi
([13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)): kampüsteki okul kapsamdadır (§3.5); hüküm değer
taşımadığı için kural yok, temsilciler çizelgesinde kayıt satırı (`in_campus`).

**Bilgi metni — kural değil** (yalnız açıklama ve uyarı metninde, hüküm diye basılmaz): bağışın gelir vergisi
matrahından indirilememesi ([GVK md. 89](../mevzuat/193-gelir-vergisi-kanunu.md#madde-89); özelge değerlendirmesi
`bilgi/`'e girecek) · birliğin tevkifat sorumluluğu ([GVK md. 94](../mevzuat/193-gelir-vergisi-kanunu.md#madde-94)) ·
kantin kira sözleşmesinin damga vergisini kiracının ödemesi ve stopaj (GİB görüşü, KV Sirküleri No. 11 — `bilgi/`
bekliyor) · birlik kantini işletirse kurumlar vergisi mükellefiyeti (sirküler/özelge).

---

---

## 7. İş akışları

**Okuma kılavuzu.** Her akış önce konumunu ve durumlarını verir, sonra geçiş tablosunu. Sütunlar:

- **Kim:** işi asıl yürüten rol — `yonetici` (OAB'den sorumlu müdür yardımcısı), `baskan`, `baskan_yardimcisi` (başkan
  yokken başkanın yerine; [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)), `muhasip`, `sekreter`, `denetleme_kurulu`, `mudur`. **Rol yetkisinin bağlayıcı kaynağı §4.4.2
  rol-izin matrisidir** (R2): Kim sütunu matrisi daraltır, genişletemez; `yonetici` başka rolün işini adına ya da
  operatör olarak giremez. Mali kayıtları (gelir-gider kaydı, banka içe aktarımı ve eşleme, makbuz yaprağı, kasa,
  emanet) **yalnız `muhasip`** yazar; `yonetici` mali kayıt yazmaz, yalnız "TEFBİS'e girildi" işaretini koyar
  (kullanıcı kararı D2). `mudur` kantin ve servis akışlarında iş yapan rol değildir; programda yazdığı belgeler
  yalnız K2'deki **dört** müdür yazısıdır: harcama talebi (E25), md. 27/3 uyarısı (E35), yeni okulda genel kurul
  daveti (E05), olağanüstü genel kurul çağrısı (E05); bunların taslağını `yonetici` hazırlamaz (§15 M-11). Okul
  idaresinin öteki resmî yazılarının (E12, E40 üst yazısı, E44, E70, E72, E73, E76, E77) ve servis komisyonu
  yazılarının (E78, E79) taslağını `yonetici` hazırlar, Okul Müdürü ya da Komisyon Başkanı kâğıtta imzalar
  (§15 KE-19); bu sıfat Kim hücresinde "kâğıtta … imzalar" notuyla yazılır. Pilot okulda programın başında çoğunlukla
  müdür yardımcısı oturur (saha 10); veli rollerinin aylık işi §7.3'teki aylık iş sırasında ve §7.10'daki panodadır. Denetim
  izi her durumda girenin hesabını yazar. "Sistem" kullanıcı eylemi olmadan programın yaptığı geçiştir.
- **Kural:** madde ve kısa açıklama; **[S]** sert (program kaydetmez — hesap bütünlüğü, hukuken geçersiz işlem,
  programın **hesapladığı** değer (kullanıcı kararı D1) ve kullanıcının sert dediği karar (A-2, KE-15); §6.1),
  **[U]** uyarı: bilgi henüz girilmemişse kayıt gerekçesiz
  yazılır, `ComplianceItem(EKSIK)` açılır ve "tamamlanacaklar"a (§7.10) düşer — sapma satırı açmaz; değer kuraldan
  sapıyorsa ya da kaydı kapatan geçişte bilgi hâlâ eksikse sapmaya döner ve gerekçe istenir, aynı kural ve kök neden
  için toplu gerekçe verilebilir (O3; kural şemasında `eksik_veri: tamamlanacak | sapma` ve `toplu_gerekce`, §6.1),
  **[B]** bilgi (gösterilir, gerekçe istemez). Değerler ve kural kimlikleri §6.4'tedir; türü çelişirse §6.4 esastır.
- **Evrak:** katalog kodu ve adı (§9.5); ad katalogdakiyle aynıdır. Belge başka bir belgenin bölümüyse kod ve bölüm
  adı yazılır (ör. "E27 kasa çıkış bölümü"). Belge yoksa "—".

Durum adları §5'teki enum değerleridir. Hiçbir akışta geri alma silme değildir: `IPTAL` ya da ters kayıt (O1).

**Yarım kalan metin** (denetim SU-16). Serbest metinli alanlar (karar metni `BoardDecision.text`, DK bulgusu
`AuditReport.findings`, gerekçe kutusu) açıkken kısa aralıklarla (öneri 30 sn) sunucuya taslak olarak kaydedilir;
`TASLAK` durumu olmayan gerekçe kutusu için hesap başına tek, şifreli, kısa süreli "yarım metin" kaydı tutulur, metin
kaydedilince ya da vazgeçilince temizlenir. Yeniden açılışta panoda "yarım kalan taslak" kalemi görünür (§7.10).
Tarayıcı deposu kullanılmaz (§4.2).

### 7.1 Genel kurul (olağan: birinci ve ikinci toplantı; olağanüstü)

Olağan genel kurul kapanacak birlik döneminin kaydıdır: çağrıyı o dönemin YK'si yapar, raporlar o döneme aittir.
Planlandığı anda yeni dönem `HAZIRLIK` durumunda açılır; adaylar, seçilenler ve tahmini bütçe ona yazılır; tutanak
tamamlanınca yeni dönem açık olur (§5.2.1, §7.8). Pilot okulda genel kurul çoğu yıl ikinci toplantıya kalır
(saha 8); bu yüzden ikinci toplantı yan yol değil, ana akışın parçasıdır — olağanda da olağanüstüde de (kullanıcı
kararı §15.1 A-1).

**Durumlar:** `PLANLANDI → CAGRILDI → ILAN_EDILDI → YAPILDI → TUTANAK_TAMAM`; `ILAN_EDILDI → YETER_SAYI_YOK →
YAPILDI`; `PLANLANDI | CAGRILDI | ILAN_EDILDI | YETER_SAYI_YOK → IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `PLANLANDI` (oluşturma) | yonetici, sekreter | [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağan genel kurul en geç Ekim sonunda [U]; yeni açılan okulda açılıştan itibaren iki ay içinde [U] · Olağanda yeni birlik dönemi `HAZIRLIK` durumunda açılır (`opens_term`; R12) [S] · Önceki dönem hâlâ `KAPANISTA` ise "kapanış bekliyor" [B] (§7.8) · Okul kartındaki öğrenci mevcudu ve tarihi güncel mi [B] · Veli listesi aktarılmadıysa öneri (§8.4) [B] | — |
| `PLANLANDI → CAGRILDI` (olağan) | sekreter (YK kararı); yeni okulda mudur | [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — çağrı YK'nindir: `KABUL_EDILDI` çağrı kararı bağı yoksa [U]; yeni okulda çağrı okul müdürünün yazısıdır | E15 YK toplantı gündemi ve karar taslağı (çağrı kararı) · Yeni okulda: E05 Genel kurul toplantı çağrısı ve gündemi (müdür imzalı) |
| `PLANLANDI → CAGRILDI` (olağanüstü) | çağırana göre: sekreter (YK kararı) · baskan ya da mudur ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · mudur ([md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25); §15.1 M-5) · denetleme_kurulu ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); §15.1 M-6) · yonetici (üye başvurusunu kaydeder) | [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — çağıran ve çağrı nedeni zorunlu alandır (envanter S-2); listede olmayan çağıran [U]: YK kararı · okul müdürü · DK, yaptığı denetimde YK'nin [md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)'da sayılan görev ve yetkilere aykırı faaliyetini tespit ettiyse ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); `AuditReport.md6_violation_found` işaretli rapor bağı, §5.2.4) · üyelerin %10'unun yazılı başvurusu (başvuran sayısı girilir; üye sayısı programca bilinmediği için oran [U]) · başkan ya da müdür ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), YK yedeklerle karar yeter sayısının altına düşünce; bir ay içinde [U]) · müdür ([md. 25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25)) · Olağanüstü genel kurul yeni dönem açmaz ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) [B] | E05 Genel kurul toplantı çağrısı ve gündemi (çağırana göre imza: YK adına başkan ve sekreter · okul müdürü · DK asıl üyeleri) · YK çağırıyorsa E15 (çağrı kararı) |
| `CAGRILDI → ILAN_EDILDI` | yonetici, sekreter; adlı katılım cetvelini ve sınıf teslim çizelgesini yalnız yonetici basar (R9) | [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — yer, zaman ve gündem birinci toplantıdan en az 15 gün önce elden yazılı, ilan panosu ve internet sayfası kanallarının üçünden [U] (gün ya da kanal eksikse) · [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — yeter sayı bu geçişte hesaplanır ve dondurulur: 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban sabit, kayıt sayısından gelmez [S] · [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — ikinci toplantı tarihi birinciden en geç 30 gün sonra [U]; olağanda ve olağanüstüde (§15.1 A-1) · [md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — gündem sırası; tohumda [md. 11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) görevleri [B] · [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağanüstüde gündem çağrı nedenine bağlıdır [B] · Davette kısa aydınlatma paragrafı ve tam metnin yeri ([KVKK md. 10/1](../mevzuat/6698-kvkk.md#madde-10); §3.4) [B] | E05 Genel kurul toplantı çağrısı ve gündemi (dosya nüshası; birinci ve ikinci toplantı tarihi; duyuru kanıtı bölümü) · E06 Genel kurul duyurusu — ilan panosu ve internet sayfası (kişisiz) · E07 Üyelere elden yazılı davet ve sınıf teslim çizelgesi · E08 Genel kurul katılım cetveli (veli listesiyle doldurulmuş ya da boş satırlı) · Olağanda dosya eki: E34 YK yıllık faaliyet raporu ve kesin hesap cetveli (dönem gelir-gider çizelgesi), E28 Tahmini bütçe, E33 Denetleme Kurulu nihai (yıllık) raporu ([md. 11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); programdan üretimi F4, o güne dek dosya eki — §14) |
| `ILAN_EDILDI → YAPILDI` (birinci toplantı) | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — katılan üye sayısı dondurulmuş yeter sayıdan az değil [S]; gözlemci öğrenciler ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) sayıya girmez [S] · [md. 10/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — açılışı okul müdürü yapar [B] · [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — divan başkanı ve kâtip veliler ya da 18 yaşını doldurmuş kursiyerler arasından açık oyla [U] | E08 Genel kurul katılım cetveli · E64 Genel kurul yeter sayı tespit tutanağı (sağlandı) |
| `ILAN_EDILDI → YETER_SAYI_YOK` | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — katılım yeter sayının altında; katılım sayısı yine dondurulur · İkinci toplantı ilk ilanda yoksa yeni ilan: [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) en az 15 gün önce ve [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) birinci toplantıdan en geç 30 gün sonra [U]; ikisi birlikte sağlanamıyorsa iki uyarı da görünür · Olağanüstüde de ikinci toplantı ilanı (§15.1 A-1) | E64 Genel kurul yeter sayı tespit tutanağı (sağlanamadı; kişisiz, saklanır; imza §15 KE-10) · E05 ve E06 ikinci toplantı ilanı (gerekirse) |
| `YETER_SAYI_YOK → YAPILDI` (ikinci toplantı; olağan ve olağanüstü — §15.1 A-1) | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — ikinci toplantıda çoğunluk aranmaz (`genel_kurul.ikinci_toplanti_cogunluk_aranmaz`) [S]; kararlar katılanların çoğunluğuyla alınır, sonuç programca hesaplanır (`genel_kurul.karar_cogunlugu`) [S] · [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) divan [U] | E08 Genel kurul katılım cetveli · E64 (ikinci toplantı) |
| `YAPILDI → TUTANAK_TAMAM` | sekreter, yonetici | [md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — gündem değişikliği oy çokluğuyla [U]; çıkarılan madde silinmez (`removed_by_vote`) · [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağanüstüde çağrı gündemi dışında madde [U] (kullanıcı kararı §15.1 B-13) · [md. 11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — YK ve DK faaliyet raporları ayrı ayrı ibra: `EDILDI` · `EDILMEDI` · [md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) tahmini bütçe görüşüldü · [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) yetkilendirme · [md. 10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [md. 11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — seçim asıl ve yedek liste hâlinde açık oyla; seçilen yalnız aynı genel kurulun adayından [S]; koltuk uygunluğu (§5.2.2) [S]; YK 5+5, DK veli 1+1 eksikse [U]; seçilme sınırı ([md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) YK başkan ve üyeleri dört, [md. 14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) DK başkanı üç) [U] — programdan önceki sayı bilinmiyorsa geçiş kurulumundaki toplu gerekçe yeter (§7.9) · Suç engeli ve tek birlik ([md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)): hüküm `uyelik.suc_engeli`, `yonetim_kurulu.tek_birlik` [U] (engel kaydedilirse); okulun beyan uygulaması işaretlenmediyse yalnız "tamamlanacaklar"da hatırlatma — mevzuat uyarısı değildir, gerekçe istemez; beyan Yönetmeliğin değil okulun yöntemidir (§3.3, §6 giriş, §15 KE-22) · [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK öğretmen üyelerini öğretmenler kurulu seçer, genel kurul oylamasına girmez [S] · Katılım sayıları ve türe göre dağılım dondurulur; sonradan yalnız gerekçeli düzeltme satırıyla (§5.4) [S] | E10 Genel kurul toplantı tutanağı · E09 YK ve DK (veli koltuğu) aday listeleri · E29 Bütçe duyurusu ([md. 13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · E13 Genel kurul sonuç bildirimi (okul müdürlüğüne) — Yönetmelikte açık bildirim hükmü yoktur (DOĞRULANMADI); okul uygulamasıdır, dolaylı dayanak [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) koordinasyon ve [md. 27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27); belgede hüküm diye sunulmaz |
| İbra `EDILMEDI` (yan akış) | sekreter, yonetici (E11); E12'nin taslağı yonetici (§15 KE-19), kâğıtta Okul Müdürü ve yeni YK adına Birlik Başkanı imzalar | [md. 11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — diğer gündem maddeleri görüşülür; divan ibra edilmeyen muhasebe evrakını tutanağa bağlar ve yeni YK ile DK'ya teslim eder; yeni YK ve okul yönetimi il/ilçe MEM'e resmî yazıyla bildirir → `ComplianceItem(TAKVIM, IBRA_EDILMEDI_BILDIRIMI)` [U] | E11 İbra edilmeyen muhasebe evrakının teslim tutanağı (divan) · E12 İbra edilmediğine dair il/ilçe MEM'e resmî yazı |
| `TUTANAK_TAMAM` sonrası | sistem; yonetici onaylar | Olağanda: `HAZIRLIK` dönemi `ACIK` olur (başlangıç = genel kurulun yapıldığı gün — birinci ya da ikinci toplantı), önceki dönem `KAPANISTA` (§7.8) [S] · [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — YK ve DK görev bölümü bir hafta içinde (§7.2) [U] · [md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — tutanak ve belgeler yeni YK'ye teslim → devir-teslim (§7.8) · Okul idaresinin TEFBİS'e yeni yönetimi, banka hesap bilgilerini ve tahmini bütçeyi girmesi → `ComplianceItem(TAKVIM)` (`TEFBIS_YONETIM_BILGISI`, `TEFBIS_BANKA_BILGISI`, `TEFBIS_BUTCE_GIRISI`; [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); "genel kuruldan hemen sonra" yalnız rehberde, GNL-OAB-RH-001 — süre kural değildir) [B] · Olağanüstüde seçim yapıldıysa görevdeki eski YK üyelikleri `DUSTU` (`OLAGANUSTU_GK_SECIMI`); dönem değişmez ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) | (§7.2 ve §7.8'deki evrak) |
| `… → IPTAL` | yonetici | Gerekçe zorunlu [S]; ilan ve dondurulmuş yeter sayı iz olarak kalır · Olağanda `HAZIRLIK` dönemi de `IPTAL` olur [S] | — |

**Notlar.**
- Yeter sayının tabanı dönemin üyelik kayıtlarından sayılmaz; organ bileşiminden gelen sabit 16'dır (YK 5+5, DK 3+3) ve
  olağanüstüde de aynı çarpan uygulanır (envanter S-1, S-2). Öğrenci mevcudu `ILAN_EDILDI` geçişinde anlık görüntü
  olarak alınır (O7).
- Sihirbaz davetiyede ikinci toplantı tarihini birlikte önerir, olağanüstüde de. Yorum: iki tarihi birlikte duyuran
  ilan, en az 15 gün öncesinde yapıldıysa [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) şartını iki toplantı için de karşılar; ayrı ilan gerekmez.
- **Veli adlı çıktılar (R9).** Veli listesi varsa katılım cetveli (E08) adlarla ve sınıfla, sınıf teslim çizelgesi
  (E07) veli adıyla basılabilir; ikisini yalnız `yonetici` basar ve program dosyalarını saklamaz — yalnız tür, tarih,
  satır sayısı ve sha256 izi kalır (§5.2.8). Öteki roller boş satırlı cetveli ve sayıları görür. Kâğıt cetvel
  "kişisel veri içerir" dipnotuyla basılır, imzadan sonra genel kurul tutanak dosyasına konur. Toplantıda ya da sonra
  yalnız sayılar girilir (isteğe bağlı satır işareti sayımı kolaylaştırır); kişi düzeyindeki işaret listeyle silinir
  (§5.4). Yeter sayının kanıtı kişisiz E64'tür: saklanır ve yeniden basılır (§15 KE-21).
- Olağan genel kurulun YK ve DK adayları ile seçilenleri `HAZIRLIK` dönemine, divan genel kurulun kendi dönemine
  yazılır (§5.2.2); böylece görev bölümü, seçilme sayacı ve dönem devrindeki hesap kapanışı doğru döneme bakar.

### 7.2 Yönetim kurulu toplantısı ve karar

Pilot okulda YK her ay toplanır, kararları sekreter deftere yazar (saha 5). Karar defteri noter tasdikli ve el
yazısıdır ([md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); program karar **taslağı** üretir ve "deftere işlendi" işaretini, sıra no'yu, sayfayı
tutar. Organ değişiklikleri (devamsızlık, ayrılan veli, yedek çağırma) bu akışa bağlıdır; hesabın askıya alınması kayıtla
aynı işlemde olur, hesap kapama ve açma `yonetici`nin işidir (§4.4.5).

**Durumlar:** toplantı `PLANLANDI → YAPILDI | YETER_SAYI_YOK | IPTAL`; karar `TASLAK → KABUL_EDILDI | REDDEDILDI`,
`KABUL_EDILDI → DEFTERE_ISLENDI`, `TASLAK → IPTAL`, ayrıca `DEFTERDE_SAKAT` (deftere yazılmış ama yeter sayısı
olmayan karar); üyelik `SECILDI → DUSTU`, yedek `SECILDI` + `promoted_on`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Toplantı `PLANLANDI` | sekreter | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — eğitim-öğretim yılı içinde ayda bir; ay toplantısız geçiyorsa pano [U]; yaz tatili ayları dışarıda [B] | E15 YK toplantı gündemi ve karar taslağı |
| `PLANLANDI → YAPILDI` | sekreter | Görevdeki her asıl üyenin katılım satırı (katıldı · özürlü · özürsüz) girilmeden geçiş yok [S] (devamsızlık sayımı, §15 A-9) · [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — en az dört üye katıldı [S] | E16 YK toplantı ve katılım izleme çizelgesi |
| `PLANLANDI → YETER_SAYI_YOK` | sekreter | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — dörtten az katılım: geçerli karar girilemez [S]; katılım satırları yine zorunlu [S] | — |
| `PLANLANDI → IPTAL` | sekreter | Gerekçe [S] | — |
| Karar `TASLAK → KABUL_EDILDI / REDDEDILDI` | sekreter | Toplantı `YAPILDI` [S] · [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — kabul oyu en az üç; kabul + ret katılanı aşamaz [S] | E15 ("karar defterine el ile yazılarak imzalanır" konum cümlesiyle, [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) |
| `KABUL_EDILDI → DEFTERE_ISLENDI` | sekreter | [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — karar defteri noter tasdikli; `OfficialBook` tasdik kaydı yoksa [U] (defter başına bir toplu gerekçe) · Sıra no ve sayfa defterdeki son kayıttan öneri olarak dolar [B] · (defter, sıra no) tekil [S]; sıra geri gider ya da atlarsa [U] · İşlenen kararın metni ve oyları değişmez [S]; sayfa fotoğrafı eklenebilir [B] · Kapanmış dönemde de yapılabilir (O2) | E68 Karar defteri dizini (dönem sonunda; arşiv paketinin `02-defterler/` dökümüne de girer, §8.5) |
| Defterde sakat karar | sekreter | Defterde fiilen yazılı ama toplantı yeter sayısı ([md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), dört üye) ya da üç kabul oyu olmayan karar: `DEFTERDE_SAKAT` olarak girilir — defter sıra no'su, sayfa, gerçek katılım ve oylar, şifreli açıklama; açıklama zorunludur ve `ComplianceItem(SAPMA)`'ya yazılır [U]; program kararı geçerli saymaz, hiçbir bağlı akışı beslemez [S]; Denetleme Kurulunun listesine ve kapanış denetimine düşer (§15 B-17) | — |
| Düzeltme | sekreter | Deftere işlenmiş karar değişmez; yeni kararla düzeltilir (`amends`) [S] | E15 (düzeltme kararı) |
| YK görev bölümü | sekreter (kayıt ve karar taslağı); yonetici (hesap işlemi) | [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — seçimden ya da yedek çağrısından sonra bir hafta içinde [U]; asıl üyeler arasından birer başkan, başkan yardımcısı, muhasip, sekreter — bir görev iki kişide olamaz [S]; okul müdürü görev alamaz [S] · Yeni dönemin görev bölümü kaydı eski dönemin organ hesaplarını askıya alır ve hesap geçişini önerir; dönem içi görev değişiminde önceki görev sahibinin hesabı kayıtla aynı işlemde askıya alınır. Eski hesapların kapanışı, DEK yenilemesi ve yeni hesapların açılışı `yonetici`nindir (olay tablosu §4.4.5) | E01 YK görev bölümü, imza yetkisi ve temsilci karar taslağı ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) müşterek imza) · E03 Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi · E66 Bankaya imza yetkisi bildirim yazısı (bankanın kendi formu DOĞRULANMADI) |
| DK görev bölümü | denetleme_kurulu (başkan seçimini, E02'yi ve denetim planını denetim modülünde yazar, M8) | [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK asıl üyeleri genel kuruldan sonraki ilk hafta toplanıp başkan seçer [U] · DK hesapları DK üyeliği `SECILDI` olunca açılır; görev bölümü hesabın ön koşulu değildir (§4.4.5) · YK rolleri ve `yonetici` DK'nin görev bölümünü yazmaz: denetleyen ile denetlenen ayrıdır (§15.1 A-2'nin ilkesi; §4.4.2 dipnot ⁵) | E02 Denetleme Kurulu görev bölümü tutanağı ve denetim planı |
| Devamsızlıkla görevin sona ermesi | sistem önerir; sekreter onaylar | [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — son üç YK toplantısında üst üste özürsüz katılmama → görev sona erer; öneri toplantının `YAPILDI` geçişinde görünür, onayla `DUSTU` (tarih: üçüncü toplantı, `DEVAMSIZLIK`); hesap aynı işlemde askıya alınır, kapanışı `yonetici` yapar (§4.4.5) · DK'de bu kural yoktur (OYS testi AYNEN) | — |
| Öğrencisi ayrılan veli | yonetici, sekreter | [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7), [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — elle `DUSTU` (`OGRENCI_AYRILDI`); hesap aynı işlemde askıya alınır, kapanışı `yonetici` yapar (§4.4.5) · [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) 2. cümle — YK üye sayısı toplantı yeter sayısının altına düştüyse veli üyeliği olağanüstü genel kurula kadar sürer: düşürme ertelenir, `retained_until_assembly` işaretlenir [U] | — |
| YK yedeğinin çağrılması | sekreter (YK kararıyla) | [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — yedekler aldıkları oy sırasıyla asıl üyeliğe çağrılır; sıradakinin atlanması [U] (ör. yedeğin çekilmesi) · [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — yeni kurul bir hafta içinde görev dağılımı yapar [U] | E15 (yedek çağırma kararı) · E65 Yedek üyenin asıl üyeliğe çağrı yazısı |
| DK yedeğinin çağrılması | yonetici (üyelik kaydı, M2) | [md. 14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK öğretmeni başka kurumda dört aydan uzun görevlendirilirse yerine yedeği çağrılır [U]; hüküm çağırma yetkisini YK'ye vermez, YK kararı gerekmez | E65 Yedek üyenin asıl üyeliğe çağrı yazısı (YK kararı bağı olmadan) |
| Karar yeter sayısının altı | sistem | [md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — görevdeki asıl ve çağrılabilir yedek sayısı üçün altına düşerse başkan ya da okul müdürü bir ay içinde olağanüstü genel kurula çağırır [U] → §7.1 olağanüstü akışı önerilir | E05 (çağıran başkan ya da müdür) |

**Notlar.** Harcama, koçan kaydı, genel kurul çağrısı, bütçe ve görev bölümü kararları ilgili kayda yabancı anahtarla
bağlanır (§5.2.10). Bağlanan karar `KABUL_EDILDI` olmalıdır (`TASLAK` ve `DEFTERDE_SAKAT` bağlanamaz); karar bağı
hiç yoksa bağlı akış uyarı + gerekçeyle ilerler (§7.1, §7.4). `DEFTERE_ISLENDI` olmaması kapatıcı geçişe (harcama
`KAPANDI`, dönem kapanışı) kadar "tamamlanacaklar"dadır (O3, §7.8). Toplantıların "yeter sayı yok" kaydı da
devamsızlık sayımına girer (§15'e öneri B-2). Karar metni yazılırken pencere kapanırsa metin "yarım kalan taslak"
olarak korunur (§7 giriş, §4.2).

### 7.3 Gelir-gider ve banka eşleme

Muhasip ayda bir, banka dekontuna ve makbuza bakarak defter tutar; müdür yardımcısı ayda bir TEFBİS'e girer (saha 1a,
2). Program banka hareketinden başlar (K1): hareket içe aktarılır, kayıt hareketten doğar ya da hareketle eşlenir.
**Mali kayıtları yalnız muhasip girer** (kullanıcı kararı D2): banka dosyası, gelir ve gider kaydı, eşleme, makbuz
yaprağı, kasa, emanet, `KESIN` ve "deftere geçirildi" işareti muhasibindir; `yonetici` mali kayıt yazmaz, TEFBİS listesini
muhasibin girişinden sonra alır ve "TEFBİS'e girildi" işaretini koyar. Muhasip görevi boşsa (görev bölümü
yapılmamışsa) kayıt bekler; pano YK'ye görev bölümünü hatırlatır (§7.10).

**Durumlar:** `BankStatement`: `ONIZLEME → UYGULANDI → GERI_ALINDI`. `BankTransaction` (hesaplanır): `ESLESMEDI →
KISMI → TAM`. `LedgerEntry`: `TASLAK → KESIN`; `TASLAK | KESIN → IPTAL`; işaretler: deftere geçirildi, TEFBİS'e girildi;
düzeltme ters kayıtla.

**Aylık iş sırası.** Adımların varsayılan sahibi ve sırası şudur; her adım bir öncekini bekler, pano bekleyeni ilgili
role gösterir (§7.10). Takvim önerisi GNL-OAB-RH-001'dendir ("her ayın son iş günü" bildirim; "ilk hafta" YK
toplantısı) — rehberdir, kural değildir.

| # | Ne zaman (öneri) | Kim | Adım | Bekler | Evrak |
|---|---|---|---|---|---|
| 1 | Ayın son haftası, muhasibin aylık oturumu | muhasip | Banka dökümünü o güne kadar içe aktarır, hareketlerden kayıt açar ya da eşler, makbuz yapraklarını bağlar, kasayı denetler | — | — |
| 2 | Aynı oturum | muhasip | Kayıtları `KESIN` yapar; eksik bilgiler "tamamlanacaklar"da kalır (O3); banka mutabakatına bakar | 1 | E19 Banka mutabakat dökümü |
| 3 | Aynı oturum | muhasip | Deftere geçirilecek kayıtları defterin sayfa düzeninde basar, tasdikli deftere el ile geçirir, "bu baskı şu sayfalara geçirildi" toplu işaretini koyar | 2 | E17 Gelir-gider defterine geçirilecek kayıtlar |
| 4 | Ayın son iş günü | muhasip (hazırlar), baskan (imzalar, teslim eder) | Başkanın müdüre aylık bildirimi, kesim tarihi o ana kadar girilen kayıtlar | 2 | E31 Birlik başkanının okul müdürüne aylık bildirimi |
| 5 | Muhasibin girişinden sonra | yonetici | TEFBİS'e girilecekler listesini alır (yalnız `KESIN`), TEFBİS'e girer, toplu "TEFBİS'e girildi" işaretini listenin sırasıyla koyar | 2 | E18 TEFBİS'e girilecekler listesi |
| 6 | Sonraki ayın ilk haftası | sekreter | YK toplantısı; harcama ve diğer kararlar, deftere işleme | — | E15, E16 |

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Banka dosyası `ONIZLEME` | muhasip | Dosyadaki hesap no ya da IBAN `BankAccount` ile aynı [S] · Kapanmış döneme düşen satır alınmaz [S] · `void` olmayan satırlarla aynı parmak izli satır elenir [S]; geri alınmış partinin satırları yeniden alınır, sayısı önizlemede görünür [B] · Aynı dosya ikinci kez [U] · Bakiye zinciri kopuk [U] · İlk bakiye ↔ `OpeningBalance` farkı [U] (§8.2) | — (ekranda içe aktarım özeti) |
| `ONIZLEME → UYGULANDI` | muhasip | Parti tek işlemde uygulanır; hareketler bundan sonra değişmez (K1) [S] | — |
| `UYGULANDI → GERI_ALINDI` | muhasip | Yalnız hiçbir hareketi eşlenmemişse [S]; satırlar `void` olur, silinmez; düzeltilmiş dosya yeniden aktarılabilir | — |
| Hareketten gelir kaydı | muhasip | Program öneri verir (kiracının birlik payı, kasa yatırması, tekrarlayan açıklama), onay kullanıcıdadır [B] · TEFBİS işlem tipi, kaynak tipi, evrak no ve tarihi eksik [U] ("TEFBİS'e girilemez"; eksik — `KESIN`'de gerekçe) · [md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [Genelge 2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) — kayıt-kabul ve diploma döneminde bağış [U] · [md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) — Bakanlık proje ve protokol faaliyetinden ücret [U] · [md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — şartlı bağış işaretlenirse amaç zorunlu, `SARTLI_BAGIS` alt hesabı açılır [S] | — |
| Hareketten gider kaydı | muhasip | Gider harcama dosyasının faturasına bağlanır (§7.4); `requires_expense_file` kapalı kategoriler dışında dosyasız gider [U] · [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — karar bağı yok [U] · [md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) — huzur hakkı ve benzeri kategori yoktur [S] | — |
| Eşleme | muhasip | Hareket ile kayıt çoka çok; etkin eşleşmeler toplamı hareket ve kayıt tutarını aşamaz, yönler tutarlı [S]; eşleşme silinmez, `COZULDU` olur [S] | — |
| Elden bağış | muhasip | [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — banka hesabına yatırılması mümkün değilse makbuzla kabul: yaprak `KULLANILDI` ve etkin yaprak bağı (§7.5) + `KASA` gelir kaydı; tutarlar eşit [S] · [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — en geç beş iş günü içinde bankaya; iş günü takvimi `Holiday`'den, kasa sayacı panoda [U] · Yatırma `KASA → BANKA` virmanıdır; banka ayağı hareketle eşlenir [S] · [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — gelirler bankada toplanır: kasadan doğrudan gider [U] | — (makbuz ciltli koçandan elle kesilir, K5) |
| Ayni bağış | muhasip | [md. 16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — nakde çevrilebilen çevrilip bağış hesabına yatırılır; çevrilemeyen belge karşılığı okul müdürlüğüne teslim edilir · `in_kind` kayıt bakiyeye girmez [S] · [TMY md. 16](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) — varlık işlem fişi no ve tarihi boş [U] (eksik: taşınır kayıt yetkilisi fişi sonra düzenler) | E21 Ayni bağış teslim tutanağı (okul müdürlüğüne; kısa aydınlatma paragrafıyla, §3.4) |
| Emanet (kesin teminat) | muhasip | Nakit kesin teminat `EMANET_GIRIS` kaydıdır, gelir değildir; TEFBİS listesine gelir diye girmez [S] · Çıkışı fesih ya da sona erme hâline göre gelir kaydı, mahsup ve iade ya da iadedir (§5.2.5, §7.6) | — |
| `TASLAK → KESIN` | muhasip | Zorunlu alanlar [S] · `KASA`, `SARTLI_BAGIS`, `EMANET` eksiye düşmez [S] · [md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — şartlı alt hesaptan giderde amaca uygunluk beyanı boş geçilemez [S] · Hâlâ açık "eksik" kalemler bu geçişte gerekçe ister (O3) | — |
| Deftere geçirildi | muhasip (aylık; aylık iş sırası adım 3) | [md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — il/ilçe MEM tasdikli gelir-gider defteri; yalnız `KESIN` kayıt [S] · Toplu işaret: baskı defterin sayfa düzenindedir (`lines_per_page`); "bu baskı X defterinin a-b sayfalarına geçirildi" her kaydın sayfasını satır sırasından yazar (`MarkBatch`) [B] · Kapanmış dönemde de yapılabilir (O2) | E17 (asgari sütunlar §15 A-12: sıra no, tarih, belge türü-no-tarih, açıklama, gelir/gider türü, karar no, gelir, gider, kalan) |
| TEFBİS'e girildi | yonetici (aylık; adım 5) | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — kaydı okul idaresi girer; yalnız `KESIN` [S]; TEFBİS alanı eksik kayıt listede uyarılı [U] · Toplu işaret E18'in satır sırasıyla [B] · Kapanmış dönemde de yapılabilir (O2) | E18 TEFBİS'e girilecekler listesi (§8.3) |
| Düzeltme | muhasip | Deftere geçmemiş ve TEFBİS'e girilmemiş kayıt `IPTAL` (gerekçe; eşleşmeleri ve yaprak bağı çözülür) · Geçmiş ya da girilmiş kayıt ters kayıtla (`reversal_of`) [S]; makbuzlu kayıtta eski yaprak bağı `COZULDU` olur, düzeltilmiş kayıt aynı yaprağa bağlanır, ters kaydın kendisi yaprak istemez (§5.2.6) · TEFBİS'e girilmiş kaydın ters kaydı "TEFBİS'te düzeltilecek" listesine düşer (ters kayıttan hesaplanır; asıl kayda yazılmaz) [U] · Kapanmış dönemin kaydı açık dönemde "önceki dönem düzeltmesi" olarak [S] | E17'de düzeltme satırı |
| Ay sonu | muhasip; baskan | Banka bakiyesi = `BANKA` + bağlı alt hesapların eşlenmiş bakiyesi; fark mutabakat listesinde [U] · [md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — başkan her ay sonunda gelirleri, bağışları ve kararla yapılan harcamaları müdüre yazılı bildirir [U] · Bildirim kesim tarihini basar; teslimden sonra o aya düşen kayıt sonraki bildirimin "önceki aylara ait geç kayıtlar" bölümüne girer (§5.2.7) [B] | E19 · E31 |
| Ders dönemi sonu | muhasip (hazırlar); yonetici (pano ve web kanıtını kaydeder) | [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — gelir-gider kayıtları her ders döneminde en az bir kez pano ve internet sayfasında [U]; duyuruda kişi adı yok (altın kural 5) | E30 Dönemlik gelir-gider duyurusu (A4 + web HTML) |

**Kantin kirası** bu akışa §7.6'dan girer: kiracının birlik payını yatırdığı hareket, takvimdeki aylık satırla
(`ContractInstallment`) eşleşen bir gelir kaydı doğurur. **Faiz ve banka masrafı** açıklama kalıbından önerilir
(TEFBİS "Faiz Gelirleri" ve ilgili gider tipi); banka masrafı dönemin sürekli ödeme dosyasına bağlanır (§7.4).

### 7.4 Harcama zinciri

[md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) her harcamada YK kararını, okul ihtiyacında okul yönetiminin yazılı talebini ve mal-hizmet alımında en az üç
kişilik komisyonu öngörür; para başkan ve muhasibin müşterek imzasıyla çekilir ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)). Pilot okulda büyük alımda
zincir tam işler, küçük alımda YK kararı yeterli sayılır (saha 6): eksik halka uyarı + gerekçe olarak kaydedilir;
dönem başı genel kararla (okul ayarı `standing_decision`, `small_purchase_limit`) gerekçe kendiliğinden o karara
toplu bağlanır (§15 A-11, O3). Her dönemde tekrarlayan ödemeler (hizmet alımı personeli, bakım, lisans, banka masrafı)
tek **sürekli ödeme dosyasında** toplanır (R6); küçük alımın **kısa yolu** tek ekrandır.

**Durumlar:** tam zincir `TALEP → KARAR → ALIM → BELGE → ODEME_TALIMATI → ODENDI → KAPANDI`; sürekli ödeme `TALEP →
KARAR → ALIM → SUREKLI → KAPANDI`, faturaları ayrı ayrı `BEKLIYOR → ODEME_TALIMATI → ODENDI`; `ODENDI` (sürekli
ödemede `SUREKLI`) öncesinden `IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `TALEP` (açılış) | mudur (E25'i yalnız müdür yazar; `yonetici` taslağını hazırlamaz — §15 M-11). Müdür programı kullanmıyorsa `yonetici` kâğıt talebi gelen evrak olarak kaydeder (`DocumentRecord`, M10); E27 kontrol listesi oradan dolar | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — okul ihtiyacında okul yönetiminin yazılı talebi; talepsiz (`YK_RESEN`) dosya [U]; genel karar kapsamındaki sürekli ödeme ya da küçük alımda gerekçe genel karara toplu bağlanır | E25 Okul yönetimi ihtiyaç ve harcama talep yazısı · E27 Harcama belgesi kontrol ve ödeme onay formu (kontrol listesi bölümü dosya açılınca başlar) |
| `TALEP → KARAR` | sekreter | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — YK harcama kararı `KABUL_EDILDI` [U] (yoksa gerekçe) · Tahmini bütçedeki kalemi aşıyor [B] · Şartlı bağıştan harcanacaksa amaç uygunluğu (§7.3) | E15 (harcama kararı) |
| `KARAR → ALIM` | yonetici, sekreter | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — mal ve hizmet alımında YK üyelerinden, uzmanlık işinde birlik üyelerinden en az üç kişilik komisyon [U] · [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — suç engeli olan harcama komisyonunda görev alamaz: hüküm `uyelik.suc_engeli` [U] (engel kaydedilirse); okulun beyan uygulaması işaretlenmediyse yalnız "tamamlanacaklar"da hatırlatma, gerekçe istemez (beyan okul uygulamasıdır, §6 giriş, §15 KE-22) | E26 Mal ve hizmet alım komisyonu piyasa araştırması ve karar tutanağı |
| `ALIM → BELGE` | muhasip | Fatura ya da gider pusulası dosyanın fatura satırına (`ExpenseInvoice`) girilir: satıcı, tutar · Fatura tutarı karar tutarını aşıyor [U] (ya da ek karar) · [md. 18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [TMY md. 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41) — alınan taşınır okul adına kaydedilir, varlık işlem fişinin bir örneği harcama belgesine eklenir: fiş no boş [U] (eksik; `KAPANDI`'da gerekçe) · Tevkifat yalnız bilgi metni (özelge; `bilgi/`) [B] | — (harcama belgesi dışarıdan gelir) |
| `BELGE → ODEME_TALIMATI` | baskan (yoksa baskan_yardimcisi) ve muhasip | [md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — talimat iki imzalı: başkan ya da yokluğunda başkan yardımcısı + muhasip; imzacı eksik [U] · [md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) — alıcı YK ya da DK üyesi [U] · Şartlı alt hesap bakiyesi yetmiyor [S] · Üçüncü onay ayarı açıksa müdür satırı [B] | E27 Harcama belgesi kontrol ve ödeme onay formu; banka ödeme talimatı · Kasadan ödenecekse E27'nin kasa çıkış bölümü (banka talimatı yerine; ayrı tutanak yok) |
| `ODEME_TALIMATI → ODENDI` | muhasip | Dosyanın faturalarına bağlı `KESIN` gider kayıtlarının toplamı fatura tutarlarına eşit ve her kayıt ya bankayla tam eşli ya da `KASA` kaydı [S] (§5.2.7) · Kasa yolu: [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — gelirler bankada toplanır, kasadan ödeme [U] · Avans ve kalan gibi birden çok ödeme olağandır [B] | — |
| `ODENDI → KAPANDI` | yonetici | Gider kaydı TEFBİS'e girildi; karar deftere işlendi; kontrol listesi tam — bu geçişte hâlâ eksikse gerekçe [U] (O3) | E27 (kontrol listesinin son hâli) |
| Sürekli ödeme `ALIM → SUREKLI` | yonetici | Dönem başı YK genel kararı (`standing_decision`) ve varsa sözleşme ve komisyon bir kez girilir; dosya dönemle sınırlıdır (R6) · Talep, karar ve komisyon halkaları dosya düzeyinde bir kez denetlenir | — |
| Sürekli ödemede fatura `BEKLIYOR → ODEME_TALIMATI → ODENDI` | muhasip; talimatı baskan ve muhasip | Her dönem (ay) yalnız fatura girilir ve ödeme hareketi eşlenir; kurallar yukarıdaki `ALIM → BELGE`, `BELGE → ODEME_TALIMATI` ve `ODEME_TALIMATI → ODENDI` satırlarıyla aynıdır | E27 (her ödeme için) |
| Sürekli ödeme `SUREKLI → KAPANDI` | yonetici | Sözleşme bitince ya da dönem sonunda; yeni dönemde yeni genel kararla yeni dosya açılır · Açık faturası kalan dosya kapanmaz [S] | E27 (dönem özeti) |
| Küçük alım kısa yolu | muhasip | `small_purchase_limit` altında ve `standing_decision` kapsamında: fatura, ödeme hareketi ve genel karar bağı tek ekranda girilir; `TALEP`, `KARAR`, `ALIM` kendiliğinden işlenir, denetim izine "genel karar kapsamında kısa yol" düşer · Eksik halkalar (yazılı talep, komisyon) [U] — gerekçe genel karara toplu bağlıdır (O3, §15 A-11) · Sınırın üstünde kısa yol açılmaz [S] | E27 |
| `… → IPTAL` | yonetici | `ODENDI` öncesi; gerekçe [S]; bağlı karar ve belgeler iz olarak kalır | — |

**Dosyasız giderler.** Vergi ödemesi, MEM payı ve arz bedeli aktarımı gibi kategorilerde (`requires_expense_file`
kapalı) gider kaydı harcama dosyası açmadan doğar; karar bağı yine uyarıyla istenir. Banka masrafı ise dönemin genel
kararına bağlı sürekli ödeme dosyasına bağlanır (R6); eşleme önerisi açıklama kalıbından gelir.

### 7.5 Makbuz koçanı

Koçanlar matbaada bastırılır, mühürlenir ve karar defterine kaydedilir (saha 4). Program koçan basmaz (K5); koçanın
envanterini ve her yaprağın kaderini tutar. Koçan dönemden bağımsızdır, devredilir. Koçan ve yaprak kayıtları mali
kayıttır: muhasip girer (D2); koçanın karar defterine kaydı kararını sekreter yazar (§7.2).

**Durumlar:** koçan `ENVANTERDE → KAYITLI → KULLANIMDA → BITTI → ARSIVDE`, her aşamadan `IPTAL`; yaprak `BOS →
KULLANILDI → IPTAL`, `BOS → IPTAL | KAYIP`, geçiş kurulumunda `GECIS_ONCESI`; yaprak–kayıt bağı `LeafUse` (`ETKIN →
COZULDU`).

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Koçan `ENVANTERDE` | muhasip | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — müteselsil seri, cilt ve sıra numarası; tür, seri, cilt tekil ve aralıklar çakışmaz [S] · 50 asıl + 50 koçan yaprağı değilse [U] · Yapraklar topluca `BOS` açılır | E22 Defter, makbuz ve belge tasdik-kayıt çizelgesi; koçan yaprak dökümü ve biten koçanların teslimi |
| `ENVANTERDE → KAYITLI` | muhasip (karar bağı ve mühür tarihi); karar taslağı sekreter | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — kurum mührüyle mühürlenir; koçan seri numaraları karar defterine yazılır; belgelerin sayısı ve türü YK'ce tespit edilir: mühür tarihi ya da karar bağı eksik [U] · [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — il/ilçe MEM tasdik kaydı isteğe bağlı; koçanın tasdike tabi olup olmadığı yorum sorusu (§15 B-15) [B] | E15 (koçan kayıt kararı, seri ve sıra numaralarıyla) · E22 |
| `KAYITLI → KULLANIMDA` | sistem (ilk yaprak kullanılınca) | Kayıtsız koçandan yaprak kullanımı [U] (ENVANTERDE'den doğrudan) | — |
| Yaprak `BOS → KULLANILDI` | muhasip | Bir yaprak bir gelir kaydına: etkin yaprak bağı (`LeafUse`) tekil, tutar eşit [S] · Önceki `BOS` yaprağı atlama [U] · [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1) — bağış alındı belgesinin bağışçı alanları kâğıttadır; programda T.C. kimlik no yok (K9) [B] | — |
| Yaprak `KULLANILDI → IPTAL` | muhasip | Kâğıtta sonradan iptal edilen kullanılmış yaprak: gerekçe zorunlu; bağlı kayıt `TASLAK` ise `IPTAL`, `KESIN` ise ters kayda zorlanır [S]; iptal edilen yaprağın aslı koçanda kalır [B] | E67 Makbuz yaprağı ve koçan iptal/kayıp tutanağı |
| Yaprak `BOS → IPTAL` / `KAYIP` | muhasip | Gerekçe zorunlu; geri alınamaz [S]. İptal edilen yaprağın aslı koçanda kalır [B] | E67 Makbuz yaprağı ve koçan iptal/kayıp tutanağı |
| Ters kayıtta yaprak | muhasip (ters kayıtla birlikte, §7.3) | Eski bağ `COZULDU`; düzeltilmiş kayıt aynı yaprağa yeni bağla [S]; yaprak `KULLANILDI` kalır | — |
| `KULLANIMDA → BITTI` | sistem | Son yaprak `KULLANILDI`/`IPTAL`/`KAYIP` | — |
| `BITTI → ARSIVDE` | muhasip | [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — biten koçanlar arşiv mevzuatındaki süreler kadar okulda saklanır; devirde liste kalemi (§7.8) | E22 (biten koçanların teslimi bölümü) · E37 Devir-teslim tutanağı (kasa sayımı bölümüyle; koçan kalemi) |
| `… → IPTAL` (koçan) | muhasip | Basım hatası, kayıp cilt; gerekçe [S]; kullanılmış yaprağı olan koçan iptal edilemez [S] | E67 Makbuz yaprağı ve koçan iptal/kayıp tutanağı (koçan iptali) |

Denetim dosyası için [TKB E.4 §4.1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4-1) Tablo 4'ün makbuz satırları (ciltli, müteselsil, mühürlü, karar defterine kayıtlı)
koçan kayıtlarından evet/hayır olarak doldurulur.

### 7.6 Kantin kiralaması ve kira-pay

Kiraya veren **birliktir** ([md. 20/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20),
[md. 20/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); sözleşme işletmeci ile birlik arasında
imzalanır, [Genelge 2024/35 II-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-5)).
Muhammen bedeli valilik ya da kaymakamlığın görevlendirdiği komisyon belirler
([md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19); il/ilçe MEM eliyle,
[Genelge 2024/35 II-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-2)); ilanı
il/ilçe MEM yapar ([Genelge 2024/35 II-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-3));
pazarlığı md. 20/3'teki ihale komisyonu yürütür ([md. 20/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20),
[md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20),
[2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51)); birlik başkanı iki komisyonda da üyedir. Birliğin
işi sözleşmenin tarafı olmak, tahsilat, pay takibi ve belge takibidir. Program birliğin ve okulun evrakını üretir,
MEM'in ve komisyonların evrakını yalnız gelen evrak olarak kaydeder. Müdür bu akışta iş yapan rol değildir; okul
yönetiminin yazılarını kâğıtta imzalar (R2, §15 KE-19).

**Durumlar.** Süreç (`Tender`, `KANTIN_KIRALAMA`) — yeniden kiralama yolu: `TALEP_ALINDI → TALEP_CEVAPLANDI →
MUHAMMEN_BEDEL → TEKLIF_EDILDI → KABUL | RET`; ihale yolu: `BILDIRILDI → MUHAMMEN_BEDEL → ILAN → IHALE → KARAR → ONAYDA →
KESINLESTI`; her aşamadan `IPTAL`. Sözleşme: `TASLAK → IMZALANDI → YURURLUKTE → SONA_ERDI | FESHEDILDI`; `TASLAK →
IPTAL`. Aylık satır: `BEKLIYOR → BIRLIK_PAYI_ALINDI → DEKONTLAR_TAMAM`; `IPTAL`. Çeyreklik arz: `late_status`
hesaplanır.

**Kiralama ve sözleşme**

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `TALEP_ALINDI` (yeniden kiralama) | yonetici | [Genelge 2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2) — mevcut işletmeci bitişten en az iki ay önce yazılı bildirir [U] · [md. 21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — toplam süre ilk sözleşmeden 20 yılı geçemez; hesap [Genelge 2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii) (31.05.2005 tabanı, rekabetçi ihale yeni başlangıç, dondurulan süre ve 540 gün) [U] | — (gelen evrak) |
| `TALEP_ALINDI → TALEP_CEVAPLANDI` | sekreter (YK kararı), baskan | [Genelge 2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) — birlik on beş gün içinde yazılı cevaplar [U] · [Genelge 2024/35 I-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-4) — yükümlülük değerlendirmesi somut belgeye dayanır, belge yoksa talebin kabulü esastır: belgesiz ret [U] | E41 Yeniden kiralama talebine yazılı cevap · E15 (YK kararı) |
| `→ MUHAMMEN_BEDEL` | yonetici, baskan | [md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) — komisyon tespiti gelen evrak olarak kaydedilir; birlik başkanı üyedir [B] · [Genelge 2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5) — tespit edilen bedel bitişten en az bir ay önce teklif edilir [U] | — |
| `TEKLIF_EDILDI → KABUL` | yonetici | [Genelge 2024/35 I-6](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-6) — kabulde muhammen bedel üzerinden yeni sözleşme; süre beş yılı, toplam 20 yılı aşamaz [U] | (sözleşme aşağıda) |
| `TEKLIF_EDILDI → RET` → ihale yolu | yonetici | [Genelge 2024/35 I-7](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-7) — muhammen bedel üzerinden pazarlık; ilanı MEM yapar | — |
| `BILDIRILDI` (ihale yolu) | sekreter (YK kararı), yonetici (üst yazı taslağı; kâğıtta Okul Müdürü imzalar) | [Genelge 2024/35 II-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-1) — kiralanacağı okul müdürlüğü vasıtasıyla il/ilçe MEM'e bildirilir | E15 (kiralama kararı; konum cümleli taslak) · E40 Kantinin kiralanacağına dair bildirim (okul müdürlüğü vasıtasıyla il/ilçe MEM'e; RYUE; konum cümlesi §9.2'ye göre) |
| `IHALE → KARAR` | yonetici (kayıt), baskan (komisyon üyesi) | [md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — istekli belgeleri eksik [U] · [md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — katılım engeli `VAR` olan istekli seçilemez [S] (hısımlık ya da suç; dayanak şifreli, §5.2.9) · [md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — komisyon bileşimi [U] · [md. 22/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — ihalelerden yasaklı kayıtlı istekli [U] | — (komisyon evrakı MEM'indir) |
| `KARAR → ONAYDA → KESINLESTI` | yonetici | Onay kaydı (makam, tarih, sayı) olmadan kesinleşme **[U]** (`kantin.kiralama_onay_kaydi`) — kullanıcı kararı D4: kantinde onay makamı ve dayanağı korpusta doğrulanamadı (2886'nın kısmi dosyasında onay hükmü yok; DOĞRULANMADI); makam elle girilir | — |
| Sözleşme `TASLAK → IMZALANDI` | baskan (imza), yonetici | [md. 21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) örneğine uygun: 25 genel şart + özel şartlar; yürütmesi durdurulan ibare basılmaz · [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2 md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) — süre en çok beş yıl [U]; ilk yıl ihale bedeli · [EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) — kesin teminat yıllık kiranın %6'sı: program önerir, girilen tutar saparsa [U] (D1); nakit alınırsa `EMANET_GIRIS` (muhasip) [B] · Ay sayısı 9 ya da 12: girilen değer yerin işletilme biçimine uymuyorsa [U] (D1) · [KDVK md. 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17) — kirada KDV hesaplanmaz [S] · [md. 24](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24) — birlik kâğıtları damga vergisi ve harçtan muaf [B] · **Pay notu:** yerleşim türü büyükşehir olmayan il merkeziyse genel şart 7'nin ikinci paragrafındaki %10-%10-%80 dağılımı [md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) ile çelişir: [Özel Şartlar md. 2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ozel-sartlar-madde-2)'ye "dağılım Yönetmeliğin 17/1-a-2 hükmü gereği %80 birlik, %20 il millî eğitim müdürlüğü olarak uygulanır; ilçe payı ayrılmaz" metni basılır, genel şartın boşluklarında ilçe "—" olur; genel şart metni değişmez (lafız kilidi) [B] · Öğrenci mevcudu ve pay oranları anlık görüntü (O7) | E42 Kantin ve benzeri yerleri kiralama sözleşmesi |
| `IMZALANDI → YURURLUKTE` | yonetici (kayıt; kâğıtta yeri okul yönetimi yetkilisi teslim eder, millî emlak üst yazısını Okul Müdürü imzalar) | [md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — imzadan önce yer teslimi yapılamaz: teslim tarihi imzadan önceyse [U] (D1: girilen tarih; `kira.imzadan_once_teslim_yok`); imzadan itibaren 15 gün içinde [U] (`kira.yer_teslimi_gun`) · [EK-2 md. 12](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-12) — teslim tutanağı · [md. 21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — sözleşme örneği okul müdürlüğünce millî emlak birimine [U] · Kira takvimi üretilir: tam yıl işletilen yerde 12 ay ([md. 19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)), işletilmeyen yerde dokuz ay ve yarıyıl ayında yarım kira ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) | E43 Kantin yer teslim ve tahliye tutanağı · E44 Sözleşme örneğinin millî emlak birimine gönderilmesi · E24 Kantin kira tahsilat, arz bedeli ve pay dağıtım izleme çizelgesi |
| Yıllık artış | sekreter (bildirim yazısı), yonetici (artış kaydı) | [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2 md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) — ikinci yıldan TÜFE on iki aylık ortalamalara göre yüzde değişim: program yeni bedeli `IndexRate`'ten önerir, girilen bedel saparsa [U] (D1) · [Genelge 2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) — yenilenen kira il/ilçe MEM'e bildirilir [U] · [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — öğrenci mevcudunda en az %25 değişim: muhammen bedelin yeniden tespiti önerisi [U] | E45 Yenilenen kira bedelinin (TÜFE) il/ilçe MEM'e bildirimi |
| Belge yenileme | yonetici | [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — her yıl işletme faaliyet belgesi ve çalışanların adli sicil ve arşiv kaydı yenilenir; [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — işletmecinin (kiracının) ve çalıştırdıklarının portör, adli sicil ve arşiv kaydı belgeleri birlikçe saklanır; kiracı kantini bizzat çalıştırdığından ([EK-2 md. 9](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-9)) hijyen belgesi kiracıdan da istenir ([HEY md. 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5)); `valid_until` geçti [U] · İhale aşamasında portör ve adli sicil istekli belgesi değildir ([md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) [B] · Belge tesliminde kısa aydınlatma ([KVKK md. 10/1](../mevzuat/6698-kvkk.md#madde-10); §3.4) [B] | E46 Kantin işletmeci ve çalışan belge izleme çizelgesi |
| Fesih (`YURURLUKTE → FESHEDILDI`) | sekreter (YK fesih kararı, E47 ve E71), baskan (imza), yonetici (sözleşme kaydı); teminat, tazminat ve mahsup kaydı muhasip | [md. 22/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — fesih hâlleri; (e) bendinde yazılı bildirime rağmen 15 gün içinde yükümlülük yerine getirilmezse [U — süre] · [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — mücbir sebep dışında iki ay üst üste ödememe: fesih önerisi [U] · **Kesin teminatın akıbeti fesih hâline göre** (§5.2.5): (a) [md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22), [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) hâllerinde gelir kaydı + cari dönem kirası tazminat; tazminat tutarı programca hesaplanır (`kira.fesih_tazminati`) [S — hesap], fiilen tahsil edilen olduğu gibi kaydedilir, fark uyarıdır (§15 KE-23); (b) EK-2 md. 7'deki ödememe feshinde birliğin alacağı kadar mahsup, kalanın iadesi; (c) olağan sona ermede ([EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8)) alacak yoksa iade · md. 22/1 ve [EK-2 md. 15](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-15) fesihlerinde yol seçilir [U] (yorum sorusu §15 B-14) · [md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — ceza, tazminat ve kısa süreli kullanım bedellerinde de %3 arz, kalan dağıtılır (`ShareStatement`, `CEZA_TAZMINAT`) [S — hesap] · [md. 22/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — yeniden ihale | E47 Kantin kiracısına yükümlülük ihtarı (15 gün) · E15 (fesih kararı) · E71 Kantin kira sözleşmesinin fesih bildirimi (fesih nedeni, teminatın akıbeti, tahliye ve teslim çağrısı) |
| Tahliye ve ihtilaf (`SONA_ERDI` ya da `FESHEDILDI` sonrası) | yonetici (tahliye kaydı ve E72 taslağı, §15 KE-19; kâğıtta Okul Müdürü imzalar); ceza tahsilatının kaydı muhasip | [EK-2 md. 13](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-13) — yer tutanakla teslim alınır · Tahliye edilmezse her geçen gün için aylık kiranın %3'ü ceza ([md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22), [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22)); tutar programca hesaplanır (`kira.tahliye_gunluk_ceza_oran`) [S — hesap] · [md. 22/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — tahliye edilmeyen yer 2886 sayılı Kanunun [md. 75](../mevzuat/2886-devlet-ihale-kanunu.md#madde-75)'i uyarınca tahliye edilir; okul yönetimi mülkiyet durumuna göre İl Muhakemat Müdürlüğü / İl Özel İdaresine bildirir ([EK-2 md. 24](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-24)) [B] · [md. 28/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-28) — sözleşmenin uygulanmasından doğan hukuki ihtilafta okul yönetimi kanuni yollara başvurulmak üzere mülki idare amirine durumu bildirir [B] | E43 Kantin yer teslim ve tahliye tutanağı (tahliye nüshası) · E72 Kiralanan yerin tahliyesi ve sözleşme ihtilafı için bildirim (okul yönetiminden) |

**Tahsilat, arz ve pay**

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Aylık satır `BEKLIYOR → BIRLIK_PAYI_ALINDI` | muhasip | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — kiracı arz düşüldükten sonra kalanın %80'ini birliğin, %10'unu il, %10'unu ilçe MEM'in hesabına ayın 5-15'i arasında yatırır ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)); vade geçti [U] · [md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — büyükşehir olmayan il merkezinde il %20, ilçe payı yok (yerleşim türü anlık görüntüsü; sözleşmenin özel şartı, yukarıda) [S — hesap] · Pay tutarları kuruş korunumlu [S] · Birlik payının banka hareketi gelir kaydıyla eşlenir (TEFBİS "Kira Gelirleri › Kantin kira geliri") | — |
| `BIRLIK_PAYI_ALINDI → DEKONTLAR_TAMAM` | muhasip (dekont kaydı; dekontu birlik ya da okul müdürlüğü teslim alır) | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — il ve ilçe paylarının dekontları birliğe ya da okul müdürlüğüne teslim edilir; eksik [U] | E24 |
| Mücbir sebep indirimi | muhasip | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — eğitime ara verilen günlerin kirası düşülür; hesap biçimi yazılı değil: indirim elle ve gerekçeyle [U] | — |
| Çeyreklik arz (kiraya vermede) | muhasip (dekont kaydı), baskan (takip); müdür kâğıtta E24'ü imzalar | [md. 17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — takipten okul müdürü ve birlik başkanı sorumludur (`arz_bedeli.takip_sorumlulari`) [U] · [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — kiracı gayri safi kiranın %3'ünü peşin ya da üçer aylık dönemlerle defterdarlık hesabına öder, dekont aslını teslim eder · Vade: [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) izleyen ayın 10'u — 11-20 arası "sözleşme vadesi geçti" [U]; [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) izleyen ayın 20'si — sonrası "Yönetmelik süresi de geçti" [U] (plan §1.8) · [md. 17/1-b-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — gecikme zammı 6183 md. 51'e göre; metin korpusta yok, program hesaplamaz [B] | E24 (arz bedeli bölümü) |
| Birlikçe işletmede (`canteen_mode`) | muhasip | [md. 17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — birlik gayri safi hasılatın %1'ini üçer aylık dönemlerle izleyen ayın 20'sine kadar öder (gider) · [md. 17/1-b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — arz, zorunlu işletme ve kanuni giderler düşüldükten sonra net 80/10/10 aktarılır (gider: kurumlara aktarım) [S — hesap] · [md. 23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — VUK hükümleri; vergi bilgi metni [B] | E24 (işletme hâli) |
| Kısa süreli kullandırma | yonetici (bedel kaydı), muhasip (gelir) | [md. 19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) — saatlik, günlük, haftalık bedel muhammen bedel komisyonunca belirlenir (kayıt) · [md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — bedelin %3'ü arz, kalan dağıtılır (`KISA_SURELI_KULLANIM`) [S — hesap] | — |

### 7.7 Servis: taşımacının tespiti

Taşımacıyı okul müdürünün başkanlığındaki taşımacıyı tespit komisyonu belirler; birlik başkanı üyedir ([Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3),
[Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3); [md. 6/1-h](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)). Komisyon kararları mülki amirin onayıyla yürürlüğe girer ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8)). Seçim fiyatla
değil, [Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'deki ölçütlerle yapılır; EK-3 puanlaması yalnız itirazda ya da yeni açılan okulda ilk kez zorunludur
([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)). Söz dağarcığı: "taşımacının tespiti", "başvuru", "değerlendirme"; "ihale", "teklif", "eksiltme" kullanıcı
metnine ve evraka girmez (altın kural 6); EK-3 kriter metninde mevzuat lafzının alıntısı §15 A-4'e bağlıdır. Ücreti
veli taşımacıya öder ([Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6)); birliğin defterine girmez, taksit takibi yoktur (§15 A-5). Komisyonun
kayıtlarını programda `yonetici` tutar; müdür komisyonun başkanıdır ama programda bu akışın rolü değildir, komisyon
evrakını kâğıtta Komisyon Başkanı sıfatıyla imzalar (R2, §15 KE-19).

**Durumlar** (`Tender`, `SERVIS_TESPIT`): `HAZIRLIK → ILAN → BASVURU → INCELEME → DEGERLENDIRME → KOMISYON_KARARI →
ONAYDA → KESINLESTI → TEBLIG_EDILDI → SOZLESME → YAYIMLANDI`; `YENIDEN` ([Servis U-E md. 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)); `IPTAL`. Sözleşme: `TASLAK →
IMZALANDI → YURURLUKTE → SONA_ERDI | FESHEDILDI`; `TASLAK → IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `HAZIRLIK` | yonetici (komisyonu kaydeder; görevlendirme yazısını kâğıtta Okul Müdürü imzalar) | [Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3), [Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3) — her yıl: müdür başkan, birlik başkanı, öğretmenler kurulunda ad çekmeyle bir asıl bir yedek öğretmen, servisle taşınan veliler arasından iki asıl iki yedek veli, varsa okul eğitim vakfı temsilcisi; bileşim eksik [U] · [Servis U-E md. 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — şartname EK-1'e göre komisyonca hazırlanır · [Servis U-E md. 5/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — işlem dosyası | E73 Taşımacıyı tespit komisyonu üyelerinin görevlendirme yazısı · E74 Servis işlem dosyası kapağı ve içerik listesi · E75 Servis tip şartnamesi ([Servis U-E EK-1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1); lafız kilidiyle) |
| `HAZIRLIK → ILAN` | yonetici | [Servis U-E md. 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — dosya teslim tarihinden en az 7 gün önce ilan tahtası ve okul web sitesi; tutanakla [U] · [Servis U-E md. 5/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — ilanın zorunlu hususları [U] · İlanda istekli için kısa aydınlatma ([KVKK md. 10/1](../mevzuat/6698-kvkk.md#madde-10); §3.4) [B] | E48 Servis çalıştırma işinin ilanı · E49 İlan asma ve indirme tutanağı |
| `ILAN → BASVURU` | yonetici | [Servis U-E md. 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) — evrak ilandaki saate kadar tutanakla teslim [U] · [Servis U-E md. 7/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) — verilen dosyalar geri alınamaz: başvuru kaydı silinmez (altın kural 4); programda "geri verildi" durumu yoktur; istekli dosyasını geri isterse talep gelen evrak olarak kaydedilir ve bu hüküm bilgi notu olarak gösterilir [B] · [Servis U-E md. 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — şartname isteyene bedelsiz verilir | E50 Tip şartname (EK-1) teslim tutanağı · E51 Başvuru dosyası teslim tutanağı · E49 (ilan indirme) |
| `BASVURU → INCELEME` | yonetici (komisyon adına kayıt) | [Servis U-E md. 8/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — eksik belgeli istekli değerlendirmeye alınmaz; istekliler önünde tutanakla · Belge eksikliği işareti [U] (plan §1.8) | E52 Belge kontrol ve tespit tutanağı |
| `INCELEME → DEGERLENDIRME` | yonetici (komisyon adına kayıt; kâğıtta komisyon imzalar) | [Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — araç yaşı, özmal durumu, il/ilçede ikamet ya da şube, aynı okulda önceki hizmet ve başlama tarihi ölçütleri (varsayılan yöntem) · [Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — EK-3 puanlaması yalnız itiraz ya da yeni okulda ilk kez; başka hâlde EK-3 seçimi [U] · [Servis EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) — puanlar kademe listesinden; kademe dışı puan [U] (plan §1.8; D1) | E54 Taşımacının tespiti değerlendirme tutanağı ve komisyon kararı (değerlendirme bölümü; md. 8/2 ölçütleriyle) · E53 EK-3 puanlama cetveli (yalnız [Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) hâlinde) |
| `DEGERLENDIRME → KOMISYON_KARARI` | yonetici (kayıt), baskan (komisyon üyesi); kâğıtta Komisyon Başkanı (Okul Müdürü) ve üyeler imzalar | [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) — çoğunluk; eşitlikte başkanın bulunduğu taraf: sonuç programca hesaplanır (`servis.komisyon_karar_cogunlugu`) [S] · çekimser kalınamaz, muhalif üye karşı oy gerekçesini kararın altına yazıp imzalar: çekimser oy girilirse ya da muhalif oyda şerh boşsa [U] (`servis.komisyon_cekimser_ve_serh`; D1) · Birden çok taşımacı seçilebilir ([Servis U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) çoğul; [Servis Araçları Yön. md. 8/3](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); §15 A-6) · [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) — komisyon gerekçesiyle işi yapmamakta serbesttir → `IPTAL` | E54 Taşımacının tespiti değerlendirme tutanağı ve komisyon kararı (karar bölümü) |
| `KOMISYON_KARARI → ONAYDA → KESINLESTI` | yonetici (onay kaydı ve E76 taslağı, §15 KE-19; kâğıtta Komisyon Başkanı (Okul Müdürü) imzalar) | [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) — mülki amir onayı (`OLUR`) olmadan kesinleşmez **[S]** (`servis.olur_olmadan_kesinlesmez`; kullanıcı kararı D4; plan §1.8) · [Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — onay ya da iptal beş iş günü içinde [U]; `RED` → `IPTAL` ya da `YENIDEN` | E76 Komisyon kararının mülki idare amirinin onayına sunulması yazısı |
| `KESINLESTI → TEBLIG_EDILDI` | yonetici (tebliğ kaydı ve E77 taslağı, §15 KE-19; kâğıtta Komisyon Başkanı (Okul Müdürü) imzalar) | [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — onaydan itibaren en geç beş iş günü içinde Tebligat Kanunu hükümlerince bildirilir [U]; sözleşmenin 10 günlük süresi bu tebliğden başlar | E77 Kesinleşen komisyon kararının taşımacıya tebliği yazısı |
| `TEBLIG_EDILDI → SOZLESME` | yonetici; kâğıtta Komisyon Başkanı (Okul Müdürü) ve taşımacı imzalar | [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — tebliğden 10 gün içinde imza [U]; imzalanmazsa `YENIDEN` · [Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9) — sözleşmede istenen belgeler (şoför ve rehber sabıka kaydı, sağlık raporu, psikoteknik, sertifika, sürücü belgesi, sigorta, ruhsat ve muayene): "görüldü" ve geçerlilik tarihi; tarama alınmaz (§5.4) [U — eksik belge]; belge tesliminde kısa aydınlatma (§3.4) [B] · [Servis Araçları Yön. md. 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) — bir eğitim öğretim yılı esas, en çok üç; [Servis U-E md. 8/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'teki "dönem" ifadesi karşısında Yönetmelik esas [U] · [Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) — ücret en çok dokuz taksit (bilgi alanı) [U] · [Servis U-E md. 10/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) — sözleşmeyi komisyon başkanı ve istekli imzalar, noter şart değil [B] | E55 Okul servis araçları sözleşmesi · E58 Servis belge izleme çizelgesi |
| `SOZLESME → YAYIMLANDI` | yonetici | [Servis U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) — sözleşme imzalanan taşımacıların bilgileri okul ilan panosu ve web sitesinde [U] · Altın kural 5'in mevzuat istisnası: taşımacının ad/unvanı, plaka ve güzergâh basılır; telefon, adres, T.C. kimlik no basılmaz; ilan kaldırılınca (`removed_board_on`) okul sitesindeki kopyanın kaldırılması panoda hatırlatılır (kullanıcı kararı D5) [B] | E56 Sözleşme imzalanan taşımacıların ilanı |
| `→ YENIDEN` | yonetici | [Servis U-E md. 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — başvuru olmaması, belgelerin uygun görülmemesi ya da sözleşmenin imzalanmaması hâlinde aynı usulle yeniden [B] | E57 Yeniden çıkma tutanağı (OYS'nin "tek katılımcı tutanağı" yerine) |
| Sözleşme dönemi | yonetici (belge ve denetim kaydı; E78, E79 taslağı, §15 KE-19; kâğıtta Komisyon Başkanı imzalar) | [Servis Araçları Yön. md. 9](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) — şoför ve rehber belge süreleri (`valid_until`) [U] · [Servis EK-2 md. 8](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-8) — her araç komisyonca bildirilen bir muhtaç öğrenciyi ücretsiz taşır: yalnız sayı tutulur [B] · Denetim kaydı (`InspectionRecord`, servis) · [Servis U-E md. 11](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-11), [Servis EK-2 md. 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-7) — fesih hâlleri; yazılı bildirime rağmen 15 gün içinde yerine getirilmeyen yükümlülük [U — süre] | E58 Servis belge izleme çizelgesi · E78 Taşımacıya yükümlülük ihtarı (15 gün) · E79 Servis sözleşmesinin fesih bildirimi |

### 7.8 Dönem kapanışı ve devir-teslim

Birlik dönemi genel kuruldan genel kurula sürer (T3). Olağan genel kurul planlanınca yeni dönem `HAZIRLIK`
durumunda açılır; `TUTANAK_TAMAM` olunca yeni dönem açık olur, eski dönem kapanışa girer. İki dönem bir süre birlikte
yazılabilir: genel kurul gününden önceki tarihli kayıtlar eski, o gün ve sonrası yeni döneme yazılır (tarih–dönem
kısıtı sert). Pilot okulda devir tutanağı yoktur (saha 9); tutanak programdan üretilir. Eski dönemi kapatan
`yonetici`dir; yeni başkan yürütmediği dönemi onaylamaz (R12).

**Durumlar:** dönem `HAZIRLIK → ACIK → KAPANISTA → KAPANDI`; devir `TASLAK → BASILDI → IMZALANDI`.

**Sıra.** Genel kurul günü: tutanak → yeni dönem açık, eski dönem kapanışta → devir-teslim (toplantı sonunda). İlk
hafta: YK ve DK görev bölümü → hesap geçişi: eski organ hesapları kapanır → DEK yenilenir → yeni hesaplar tek geçici
parolayla açılır (§4.4.5; DEK yenilemesi §4.4.4). Sonraki haftalar: eski dönemin kalan mali işi → kapanış denetimi → `yonetici` dönemi kapatır →
arşiv paketi.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Yeni dönem `ACIK`, eski `KAPANISTA` | sistem (`TUTANAK_TAMAM`, §7.1); yonetici onaylar | `HAZIRLIK` dönemi açılır: başlangıç = genel kurulun yapıldığı gün (birinci ya da ikinci toplantı); eski dönemin bitişi = bir önceki gün [S] · Yeni dönem o günün en yeni kural paketi revizyonuna bağlanır (§6.2-4) · Ders yılı eşlemi (`SchoolYear`) [B] | — |
| Devir `TASLAK → BASILDI → IMZALANDI` | yonetici (hazırlar); kâğıtta eski başkan ve muhasip teslim eder, yeni YK adına teslim alır | [md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — toplantı sonunda bütün tutanak ve belgeler yeni YK'ye teslim edilir · Kalemler kayıtlardan önerilir: defterler (karar defterinin son sıra no ve sayfası, gelir-gider defterinin son sayfası, gelen-giden evrak defteri), koçanlar (envanter, boş yapraklar, biten koçanlar), dosyalar (genel kurul tutanak dosyası, harcama dosyaları, kantin ve servis dosyaları; [md. 23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)), banka bakiyesi ve imza yetkisi değişikliği ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)), kasa sayımı, açık işler (açık harcama dosyaları, bekleyen kira ve arz, TEFBİS'e girilmemiş ve deftere işlenmemiş kayıtlar), program hesapları (hesap geçişi tamam mı, §4.4.5) · Kasa sayımı ([md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) ≠ `KASA` bakiyesi [U] — düzeltme kaydını muhasip girer (D2) · Devir günündeki banka bakiyesi ile defter bakiyesi farkı [B] (aylık kayıt düzeninde her yıl çıkar; denklik kapanışta sert denetlenir) · `EKSIK` kalem [U] · **Kurtarma anahtarı zarfı** okul müdürlüğünde kalır, devredilmez, veliye geçmez; tutanağa yalnız "zarf müdürlükte, mührü sağlam" kaydı ile anahtar no ve tarihi girer, anahtarın kendisi devre girmez (kullanıcı kararı D3; `HandoverItem.KURTARMA_ZARFI`) · Islak imza kâğıttadır; program "imzalandı" işaretini ve tarihini tutar | E37 Devir-teslim tutanağı (kasa sayımı bölümüyle) · E22 Defter, makbuz ve belge tasdik-kayıt çizelgesi; koçan yaprak dökümü ve biten koçanların teslimi (koçan envanteri) · E66 Bankaya imza yetkisi bildirim yazısı (görev bölümünden sonra; bankanın kendi formu DOĞRULANMADI) |
| Görev bölümü ve hesaplar | sekreter (YK görev bölümü), denetleme_kurulu (DK görev bölümü, §7.2); hesap geçişi yonetici | [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — bir hafta içinde (§7.2) [U] · Yeni görev bölümü kaydı eski organ hesaplarını askıya alır; §4.4.5 hesap geçişi: eski organ hesapları kapanır → DEK yenilenir (TK12, §4.4.4) → yeni hesaplar tek geçici parolayla açılır (R12) · Yapılmadıkça `yonetici` panosunda kart (§7.10) | E01, E02, E03 · E63 Hesap teslim pusulası (her yeni hesap için; parola taşımaz) |
| Eski dönemin kalan mali işi | muhasip (görev bölümüne dek eski muhasip; hesap geçişinden sonra yeni dönemin muhasibi, §4.4.5) | `KAPANISTA` dönemine yalnız o dönemin tarihli kayıtları yazılır; bitişe kadarki banka hareketleri içe aktarılır, eşlenir ve `KESIN` yapılır (D2; aylık iş sırası §7.3) | E17, E18, E19 |
| `KAPANISTA → KAPANDI` | yonetici (yeni başkana bilgi gider; başkan onayı aranmaz — R12) | Sıra (denetim KM-5): (1) `pre-kapanis-<tarih>.odbak` yedeği (§4.4.7; rotasyon §2.3.2) · (2) aşağıdaki kapanış denetimi — denetim izi zinciri bu adımda **tam** doğrulanır (§4.6.3); sert maddelerin hepsi geçmeden kapanmaz; açık "eksik" kalemler bu geçişte gerekçe ister, toplu gerekçe verilebilir (O3) · (3) tek işlemde: kapanış bakiyeleri yeni dönemin `OpeningBalance`'ı olur [S]; süreli kişisel veri silinir ve boşaltılır (§5.4: veli listesi, bağışçı T.C. kimlik no'ları, süresi dolan istekli iletişimi ve engel dayanağı, düşme gerekçeleri, bağsız kişi ve personel); dönem kilitlenir, kural bağı donar (§6.2-6); silmelerden sonra `wal_checkpoint(TRUNCATE)`, KVKK tetiğinden eski `pre-migrate-*` yedeklerinin silinmesi ve "bu tarihten önce dışarı aldığınız yedekler" kartı (§4.4.7) · (4) arşiv paketi kapanmış dönemden, **silmelerden sonra** üretilir (§8.5); yarıda kalırsa yeniden üretilir (yeniden basım, O2) · Geri alınamaz; düzeltme açık dönemde "önceki dönem düzeltmesi" ters kaydıyla [S] (§15'e öneri B-4) · Kapanmış dönemde yalnız işaretler ve yeniden basım yazılır (O2) | E69 Dönem kapanış denetim listesi · E34 YK yıllık faaliyet raporu ve kesin hesap cetveli (dönem gelir-gider çizelgesi) · E68 Karar defteri dizini (arşiv paketinin `02-defterler/` dökümüne de girer) · E39 Yıl sonu arşiv paketi içerik listesi ([Arşiv Yön. md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) "Dosya/Klasör İçerik Listesi" kalıbında) |
| Kapanmayan dönem | sistem (pano) | `KAPANISTA` dönem her açılışta `yonetici`nin pano kalemidir (§7.10) [B] · Sonraki olağan genel kurul planlanırken önceki dönem hâlâ kapanmamışsa "kapanış bekliyor" [B]; `yonetici` için son tarih o genel kurulun çağrısıdır · Kapanmamış dönem yeni dönemin açılmasını engellemez (dönem aralıkları çakışmaz, §5.2.1) | — |

**Kapanış denetimi**

| Denetim | Tür | Dayanak |
|---|---|---|
| Bitiş tarihine kadar banka hareketleri içe aktarılmış (son ekstre tarihi ≥ bitiş) ve hepsi tam eşli; geçiş kurulumu yapılmış ilk dönemde programa başlama gününden sonrası (§7.9) | sert (§15'e öneri B-3) | K1; [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| `TASLAK` mali kayıt yok | sert | Hesap bütünlüğü |
| `BANKA` + bağlı alt hesapların bakiyesi = bitiş günündeki banka bakiyesi; `KASA`, `SARTLI_BAGIS`, `EMANET` ≥ 0 | sert | Hesap bütünlüğü |
| Genel kurul katılım sayıları dondurulmuş | sert | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) |
| Veli listesi silinecek (kapanış adımı); veli adı taşıyan belgenin dosyası yok | sert | T5; R9 |
| Açık "eksik" kalemler sapmaya döner, gerekçe ister (toplu gerekçe verilebilir) | uyarı | O3 |
| Kasada bekleyen tutar | uyarı | [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| TEFBİS'e girilmemiş ya da "TEFBİS'te düzeltilecek" kayıt | uyarı (işaret kapanıştan sonra da konabilir, O2) | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Deftere geçirilmemiş gelir-gider kaydı; deftere işlenmemiş karar | uyarı (işaret kapanıştan sonra da konabilir, O2) | [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Defterde sakat karar var | uyarı (Denetleme Kuruluna bilgi) | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) |
| Açık harcama dosyası; kapanmamış sürekli ödeme dosyası | uyarı | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) |
| DK nihai raporu yok; yılda iki inceleme yapılmamış | uyarı | [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Eksik aylık bildirim; ders dönemi duyurusu eksik | uyarı | [md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) |
| Koçanda sıra atlanmış boş yaprak | uyarı | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| Defterlerin tasdik kaydı yok | uyarı | [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Koçanların tasdik kaydı yok | bilgi (yorum sorusu §15 B-15) | [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Kantinde bekleyen kira, pay dekontu ya da arz | uyarı | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7), [md. 17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) |
| Denetim izi zinciri tam doğrulandı | uyarı (kırıksa gerekçe + DK kartı) | Altın kural 4 (§4.6.3) |

Olağanüstü genel kurulla YK değişirse dönem kapanmaz; aynı dönem içinde ara devir-teslim yapılır (`Handover`,
`from_term` = `to_term`).

### 7.9 Geçiş kurulumu

Program bir okula çoğu zaman dönemin ortasında girer; pilot okulda da beta 2026-2027 dönemine paralel yürüyecek
(§14 F7). Geçiş kurulumu, programdan önce başlamış dönemi ve görevdeki kurulu, kuralları delmeden programa alır. Yalnız
ilk dönemde ve kurulum sihirbazında açılır; girilen her şey denetim izinde "geçiş" etiketiyle durur ve sonradan
değişmez (kanıt). Organ kısmı F1c'de, mali kısmı F3'te, kantin ve servisin süren sözleşmeleri F5 ve F6'da gelir (§14).

| Adım | Kim | Ne girilir | Kural | Faz |
|---|---|---|---|---|
| 1. İlk birlik dönemi | yonetici | Son olağan genel kurulun tarihi (dönem başı) ve programa başlama günü (`program_start_date`) | İlk `OabTerm` doğrudan `ACIK` açılır, `opened_by_assembly` boştur [B] · Programa başlama günü dönem başından önce olamaz [S] | F1c |
| 2. Görevdeki kurul | yonetici | YK 5+5, DK 3+3 ve temsilciler; her biri `source = DEVRALINAN` üyelik: koltuk, görev (başkan, muhasip…), seçim kanalı (genel kurul, öğretmenler kurulu), kanıt (seçildiği genel kurulun tarihi, görev bölümü kararının defter sıra no'su) | Aynı genel kurulun aday kaydı şartı aranmaz (devralınan üyelik, §5.2.2) [B] · Koltuk uygunluğu (kişi türü, müdür yasağı, aynı kişi YK ve DK'de) yine uygulanır [S] · Görev girilince hesap açılabilir; hesabı yonetici açar, E63 Hesap teslim pusulası basılır (§4.4.5) | F1c |
| 3. Programdan önceki seçilme sayıları | yonetici | Görevdeki ve aday olacak kişiler için toplu beyan: her kişide "karar defterinden: n" ya da "bilinmiyor" (`external_yk_terms`, `external_dk_chair_terms`) | "Bilinmiyor" seçilen bütün kişiler için seçilme sınırı uyarısı ([md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) bir kez, toplu gerekçeyle kapanır; aday başına yeniden sorulmaz (O3) [U] · Sayım biçimi §15 B-12 | F1c |
| 4. Defterler | yonetici (kayıt), sekreter (karar defteri bilgisi) | `OfficialBook` kayıtları; karar defterinin programdan önceki son sıra no'su ve sayfası, gelir-gider defterinin son sayfası ve sayfa başına satırı, tasdik bilgileri | Programdaki ilk karar ve ilk defter baskısı bu değerlerden sonra öneri olarak dolar [B]; tasdik kaydı yoksa defter başına bir toplu gerekçe [U] | F1c (karar defteri), F3 (gelir-gider defteri) |
| 5. Açılış bakiyesinin günü | muhasip | Okul iki yoldan birini seçer (§15 B-18): **(a) dönem başı** — açılış bakiyesi genel kurul günündeki ekstre bakiyesidir; dönem başından bugüne banka hareketleri içe aktarılır ve kayıtlar girilir (öneri: kesin hesap, faaliyet raporu ve dönemlik duyuru tam çıkar). **(b) programa başlama günü** — açılış bakiyesi o günün ekstre bakiyesidir; dönem başı ile başlama günü arası "programdan önce" sayılır, o aralığın gelir ve gider toplamı defterden ya da TEFBİS'ten elle girilir, kanıtının yeri yazılır (`pre_program_*`) | `OpeningBalance(source = GECIS_KURULUMU)`, `evidence_date` seçilen gün [S] · TEFBİS "Devreden" tutarıyla fark [U] (`tefbis_carryover`) · (b) yolunda kesin hesap (E34), dönemlik duyuru (E30) ve kapanış raporları bu aralık için kanıtlı tek toplam satırı basar; kapanış denetimi hareketleri yalnız başlama gününden sonrası için arar (§7.8) [B] | F3 |
| 6. Geriye dönük kayıtlara toplu işaret | muhasip (deftere geçirildi), yonetici (TEFBİS'e girildi) | (a) yolunda dönem başından bugüne girilen ve defterde ya da TEFBİS'te zaten bulunan aylar | Kayıtları yine muhasip girer (D2); defterde zaten olan aylar defter ve sayfa aralığıyla, TEFBİS'te zaten olan aylar tarih aralığıyla topluca işaretlenir (`MarkBatch`, `source = GECIS`) [B] | F3 |
| 7. Koçanlar | muhasip | Kullanımdaki ve boş koçanların envanteri; programdan önce kullanılmış yaprak aralıkları | Programdan önce kullanılmış yapraklar `GECIS_ONCESI` durumunu alır, kayıt bağı aranmaz [B]; koçan kayıt kararı ve mühür bilgisi girilir (§7.5) | F3 |
| 8. Süren işler | yonetici; mali kalemleri muhasip | Yürürlükteki kantin sözleşmesi (kira takvimi başlama ayından), servis sözleşmeleri, açık harcama dosyaları, sürekli ödemeler ve dönemin genel kararı | Süren sözleşme `YURURLUKTE` olarak girilir; tespit ya da kiralama süreci geriye dönük işletilmez [B] · Kesin teminat nakit alınmışsa `EMANET` açılış bakiyesine girer | F3 (ödemeler), F5 (kantin), F6 (servis) |

**Ne olmaz.** Geçmiş genel kurul geriye dönük işletilmez; geçmiş kararlar karar defterinden tek tek girilmez (yalnız
son sıra no ve sayfa); programdan önceki gelir-gider kayıtları (b) yolunda kayıt kayıt girilmez. Geçiş bilgisi
(başlama günü, devralınan kurul, açılış bakiyesinin kanıtı) dönem raporlarının dipnotuna ve arşiv paketinin
`00-BENIOKU.txt`'sine girer (§8.5).

### 7.10 Pano ve takvim

Ön değerlendirme programı "kurumsal hafıza, evrak motoru ve mevzuat takvimi" diye tanımlar; panonun işi takvim
tarafıdır: açılış ekranında "bu hafta yapılacaklar" (M9). Süreye bağlı her uyarının teslim yolu panodur: program
SMS ya da e-posta göndermez, ağa çıkmaz; veli ayda bir gelir. Pano kişisizdir — kalem metinlerinde kişi adı geçmez
(OYS'nin "bildirimde kişi adı yok" ilkesi, §12.A); kişi ancak kalemin götürdüğü ekranda, rolün okuma yetkisi
içinde görünür.

**Kaynaklar.** Pano kalemleri saklanmaz; her açılışta, gün değişiminde ve ilgili kayıt yazılınca kaynaklardan
hesaplanır (tek kaynak, O6). Hesap okuma işidir, kilitliyken veritabanına yazmaz (§4.6.3).

| Kaynak | Örnek kalemler |
|---|---|
| Kural paketindeki süre kuralları (§6.4) ile modellerdeki tarihler | Olağan genel kurul Ekim sonu, 15 gün ilan, 30 gün ikinci toplantı, görev bölümü bir hafta, YK aylık toplantısı, kasada 5 iş günü, aylık bildirim, dönemlik duyuru, kira 5-15'i, arz 10'u ve 20'si, TÜFE yıl dönümü, yer teslimi 15 gün, servis onayı ve tebliği beşer iş günü, sözleşme imzası 10 gün, yeniden kiralamada iki ay ve 15 gün, belge `valid_until` |
| `ComplianceItem(TAKVIM)` — modelde karşılığı olmayan yükümlülükler | Defter tasdiki, DK incelemesi, MEM denetimi, kantin faaliyet belgesi, TÜFE bildirimi, millî emlak bildirimi, ibra edilmedi bildirimi, genel kuruldan sonra TEFBİS'e yönetim, banka ve bütçe girişi |
| `ComplianceItem(EKSIK)` — "tamamlanacaklar" (O3) | VİF bekleyen gider, TEFBİS alanı eksik kayıt, beyan uygulaması işaretlenmemiş üye, tasdik kaydı girilmemiş defter |
| İş kuyrukları (sayımlar) | İçe aktarılmamış gün sayısı (son ekstre tarihinden bugüne), eşlenmemiş hareket, `TASLAK` kayıt, makbuz yaprağı bağlanmamış gelir, deftere geçirilmemiş `KESIN` kayıt, TEFBİS'e girilmemiş `KESIN` kayıt, "TEFBİS'te düzeltilecek", deftere işlenmemiş karar, açık harcama dosyası ve bekleyen fatura, bekleyen kira ve pay dekontu, onay zinciri bekleyen etkinlik (§7.11), kapanış bekleyen dönem, hesap önerileri ve hesap geçişi (§4.4.5), yarım kalan taslak (serbest metin ya da gerekçe kutusu; §7 giriş, §4.2) |
| Yıllık iş takvimi (GNL-OAB-RH-001 Bölüm 6) | Sene başı öğretmenler kurulunda DK öğretmen seçimi, eylülde temsilci görevlendirmeleri ve kantin belge yenilemesi, ara denetim ayları (öneri: Ocak, Nisan, Temmuz), ders dönemi sonu duyuruları; "öneri" ve "okul planı" satırları kuraldan ayrı biçimde gösterilir. E14 yıllık iş takvimi aynı kaynaktan basılır |
| Kurulum yol haritası (plan §2.2) | Okul kartının eksik alanları (`registration_periods`, `data_controller_text`), kural sürümü seçimi, yedek hatırlatması, geçiş kurulumunun açık adımları (§7.9) |

**Rol başına görünüm.** Her rol yalnız kendi kalemlerini ve okuma yetkisindeki bilgiyi görür (§4.4.2); her kalem tek
tıkla ilgili ekrana götürür.

| Rol | Pano |
|---|---|
| muhasip | "Bu ay sizden beklenenler": içe aktarılacak dönem, eşlenmemiş hareket, `TASLAK` kayıt, yaprağı bağlanmamış gelir, kasada bekleyen tutar ve 5 iş günü sayacı, deftere geçirilecek kayıt, aylık bildirimin hazırlığı, bekleyen fatura ve kira; ayın son haftasında aylık iş sırasının hatırlatması (§7.3) |
| sekreter | Gelecek YK toplantısı ve gündem, deftere işlenmemiş karar, görev bölümü süresi, yedek çağrısı önerisi, gelen-giden evrak sırası, genel kurul süreleri |
| baskan, baskan_yardimcisi | İmzalanacak aylık bildirim ve ödeme talimatı, arz takibi ([md. 17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)), genel kurul ve görev bölümü süreleri; başkan yardımcısı başkanın kalemlerini görür, başkan yokken iş onundur |
| denetleme_kurulu | Görev bölümü süresi, inceleme takvimi (yılda en az iki; öneri ayları), ara ve nihai rapor tarihleri, sapma listesi ve defterde sakat kararlar, bütünlük kartları (hesap mührü, denetim izi zinciri; §4.4.5, §4.6.3) |
| mudur | Kendi yazıları (E25 harcama talebi, E35 md. 27/3 uyarısı; yeni okulda ve olağanüstüde E05), aylık bildirimin teslimi ([md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)), genel kurulun zamanında yapılması ([md. 27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)), uygunluk görüşü bekleyen etkinlik (§7.11), okul idaresi, kantin ve servis yazılarından kâğıtta imzalayacakları (E70 dâhil; §7.12) |
| yonetici | Bütün liste; ayrıca TEFBİS'e girilecek `KESIN` kayıt sayısı (muhasibin girişinden sonra), hesap önerileri ve hesap geçişi (§4.4.5), kapanış bekleyen dönem, sistem işleri (yedek, güncelleme), geçiş kurulumunun açık adımları, ilanı kaldırılan taşımacı listesinin sitedeki kopyası (D5) |

**Teslim yolu.**

- **Giriş:** rolün "bu hafta yapılacaklar" listesi — vadesi yedi gün içinde ya da geçmiş kalemler. Veli rollerinde
  (başkan, başkan yardımcısı, muhasip, sekreter) varsayılan açılış görünümü "bu ay sizden beklenenler"dir ve büyük
  yazıyla açılır (ailenin yoğunluk ayarı; R5 riskinin karşılığı, §16).
- **Takvim görünümü:** ay ve yıl; basılı hâli E14'tür.
- **Gerekçe istemez:** pano bilgidir. Vadesi geçen bir kuralın gerekçesi kendi akışındaki kapatıcı geçişte istenir
  (O3); pano kalemi kayıt kapanınca kendiliğinden düşer.
- **Kalemin kapanması:** kaynak kayıt düzelince (eşlendi, işaretlendi, teslim edildi) ya da `ComplianceItem` satırı
  `done_on` / `resolved_at` alınca.

**Fazlar.** Pano kabuğu (açılış ekranı, rol başına liste, kurulum yol haritası, organ kalemleri: görev bölümü süresi,
DK görev bölümü, geçiş kurulumunun açık adımları) F1c'dedir. Her faz kendi kalemlerini ekler ve kapısında o fazın pano
kalemleri sınanır: F2 genel kurul süreleri; F3 mali kuyruklar, kasa sayacı, YK aylık toplantısı, kira ve arz
vadeleri; F4 harcama, bildirim, duyuru, etkinlik onay zinciri, DK ve kapanış kalemleri; F5 kantin belgeleri, TÜFE ve yeniden kiralama
süreleri; F6 servis belge, onay ve tebliğ süreleri (§14).

### 7.11 Sosyal-kültürel etkinlik ve kampanya

Birlik sosyal ve kültürel etkinlik ve kampanya düzenler ([md. 6/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6));
faaliyet sosyal etkinlikler kurulunca incelenir, okul müdürünün uygunluk görüşü ve il/ilçe MEM onayıyla yapılır
([md. 6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)). Etkinliğin gelir-gider işleri birliğindir
([SEY md. 5/8](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-5)). Program onay zincirinin
tarih ve sayılarını tutar, gelir ve gider kayıtlarını etkinliğe bağlar (`LedgerEntry.event`) ve E36'yı üretir; onay
vermez, müdürün görüşünü ve MEM onayını gelen evrak olarak kaydeder. Mali kayıtları muhasip girer (D2). Faz F4 (§14).

**Durumlar** (`SocialEvent`, §5.2.7): `TASLAK → ONAYDA → ONAYLANDI → YAPILDI → KAPANDI`; `YAPILDI` öncesinden `IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `TASLAK` (oluşturma) | sekreter, yonetici | Tür (etkinlik · kampanya), ad, düzenleyen (`BIRLIK` · `UCUNCU_KISI`), tarih-saat, sorumlu YK üyesi, YK kararı bağı (§7.2) · [md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) — Bakanlık proje ve protokolü kapsamındaki faaliyetten ücret talep edilemez: "kapsamında değil" beyanı yoksa ücret gelirinde [U] (`gelir.proje_protokol_ucret_yasak`) · [md. 15/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) — üçüncü kişinin okulda düzenlediği gelir getirici etkinlik eğitim-öğretim saatleri dışında [U] (`etkinlik.ders_saatleri_disinda`; yalnız `UCUNCU_KISI`) | E15 (etkinlik kararı) |
| `TASLAK → ONAYDA` | sekreter, yonetici | [md. 6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) — sosyal etkinlikler kurulunun incelemesine sunulur; inceleme tarihi ve sayısı girilir | — |
| `ONAYDA → ONAYLANDI` | yonetici (kayıt; uygunluk görüşünü kâğıtta Okul Müdürü verir, onay il/ilçe MEM'indir) | [md. 6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) — kurul incelemesi → okul müdürünün uygunluk görüşü → il/ilçe MEM onayı; her aşamanın tarihi ve sayısı; aşaması boş onay [U] (`etkinlik.onay_zinciri`; bilgi sonra gelecekse "tamamlanacaklar"da, `KAPANDI`'da gerekçe) | E36 (onay zinciri bölümü) |
| `ONAYLANDI → YAPILDI` | sekreter, yonetici; gelir-gider kayıtları muhasip | Gelir ve gider kayıtları etkinliğe bağlanır (`LedgerEntry.event`); bağış ve makbuzda §7.3 ve §7.5, giderde harcama zinciri (§7.4) kuralları geçerlidir | — |
| `YAPILDI → KAPANDI` | muhasip, sekreter | Gelir ve gider toplamları etkinliğe bağlı `KESIN` kayıtlardan programca hesaplanır; net gelir defterle aynıdır · Bağlı `TASLAK` kayıt ve açık "eksik" kalemler bu geçişte gerekçe ister (O3) | E36 Sosyal-kültürel etkinlik / kampanya gelir-gider kayıt ve onay formu |
| `… → IPTAL` | sekreter, yonetici | `YAPILDI` öncesi; gerekçe [S]; bağlı karar ve evrak iz olarak kalır | — |

### 7.12 Okul müdürünün yazılı uyarısı ve il/ilçe MEM'e bildirim (md. 27/3)

Okul müdürü birliğin iş ve işlemleri ile harcamalarda usulsüzlük veya uygunsuzluk görürse önce birlik başkanını yazılı
olarak uyarır; durum devam ederse il/ilçe MEM'e bildirip denetlenmesini talep eder
([md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)). Program iki yazıyı üretir, birlik kayıtlarına
yazmaz; yazılar ilgili kayda (harcama dosyası, karar, sözleşme) gelen-giden evrak bağıyla bağlanır. Uyarı K2'deki
dört müdür yazısından biridir; MEM'e bildirim değildir: okul idaresinin öteki resmî yazısıdır (§15 KE-19). Faz F4 (§14).

| Adım | Kim | Kural | Evrak |
|---|---|---|---|
| Yazılı uyarı | mudur (müdür hesabından; `yonetici` taslağını hazırlamaz, §15 M-11). Müdür programı kullanmıyorsa kâğıt uyarı birliğe gelen evrak olarak kaydedilir (`DocumentRecord`, M10) | [md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) 1. cümle — önce birlik başkanı yazılı uyarılır [B] | E35 Okul müdürünün birlik başkanına yazılı uyarısı |
| Durum sürerse: bildirim ve denetim talebi | yonetici (taslak; §15 KE-19); kâğıtta Okul Müdürü imzalar | [md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) 2. cümle — durum devam ederse il/ilçe MEM'e bildirilir, denetlenmesi talep edilir [B] · Yazı önceki uyarının (E35 ya da kâğıt uyarının evrak kaydı) tarihini ve sayısını taşır (§9.6) | E70 Okul müdürünün il/ilçe MEM'e bildirimi ve denetim talebi |

---

## 8. İçe ve dışa aktarım

Program ağa çıkmaz; dosyalar kullanıcının getirdiği ve götürdüğü dosyalardır. Banka özeti, TEFBİS çıktısı ve e-Okul
listesi gerçek kişi verisi taşır: depoya girmez (altın kural 5), test verisi uydurmadır.

### 8.1 Ortak kurallar

| # | Kural | Ayrıntı |
|---|---|---|
| A1 | Önizleme → uygula | Önizleme, uygulamayla aynı kodu geri alınan bir işlem noktası içinde çalıştırır (Kütüphane Defteri ADR-0034 deseni); kullanıcı sayıları ve uyarıları görür, sonra uygular. Parti tek işlemdir: ya hepsi ya hiçbiri |
| A2 | Ham dosya saklanmaz | Yalnız `payload_sha256`, dosya adı, satır sayısı ve parti özeti tutulur ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4)). Aynı özetli dosyanın ikinci kez uygulanması uyarı |
| A3 | Sütun beyaz listesi | Ayrıştırıcı yalnız tanımlı alanları okur; diğer sütunların değeri hiçbir modele, günlüğe, hata iletisine yazılmaz. Test: içe aktarımdan sonra veritabanında beyaz liste dışı değer yok |
| A4 | Biçimler | `.xlsx` (openpyxl), `.xls` (ailenin okuyucusu), `.csv` (UTF-8, UTF-8 BOM, Windows-1254, ISO-8859-9 sezgisi; `;`, `,`, sekme ayırıcı) |
| A5 | Başlık bulma | İlk 30 satırda Türkçe katlamalı eş anlamlı eşleme (`normalize.py`, AYNEN); bulunamazsa kullanıcı sütunları eşler ve eşleme profili saklanır |
| A6 | Tarih ve tutar | Tarih: gg.aa.yyyy, gg/aa/yyyy, gg-aa-yyyy, yyyy-aa-gg, Excel seri sayısı; saat atılır. Tutar: `1.234,56`, `1234,56`, `1,234.56` (ayraç sütun bazında sezilir), parantezli ya da eksi işaretli negatif, "B"/"A" ya da "Borç"/"Alacak" ekleri |
| A7 | Yetki | Banka: yalnız muhasip (mali kayıtları yalnız muhasip girer — kullanıcı kararı D2) · TEFBİS listesi ve "girildi" işareti: yonetici · e-Okul: yonetici. Bağlayıcı kaynak §4.4.2 rol-izin matrisidir. Her parti denetim izine kim-ne zaman ve özetle yazılır (kişisiz, §4.6) |

### 8.2 Banka özeti (xlsx öncelikli)

Pilot okul internet bankacılığından Excel döküm alabiliyor (saha 3; plan F0-3). Bankanın sütun düzeni örnek gelene
kadar aşağıdaki varsayılan şema geçerlidir; örnek gelince "F1 eki" ile kesinleşir. Her `BankAccount` kendi eşleme
profilini (`import_profile`) taşır: ilk aktarımda kullanıcı onaylar, sonra hatırlanır. İçe aktarımı muhasip yapar,
çoğunlukla aylık oturumunda (aylık iş sırası, §7.3).

| Alan | Zorunlu | Başlık eş anlamlıları (TR katlamalı) | Modeldeki yeri |
|---|---|---|---|
| İşlem tarihi | evet | Tarih · İşlem Tarihi | `booking_date` |
| Valör | hayır | Valör · Valör Tarihi | `value_date` |
| Açıklama | evet | Açıklama · İşlem Açıklaması · Detay | `description` (şifreli) |
| Tutar | Tutar **ya da** Borç + Alacak | Tutar · İşlem Tutarı | `amount` (işaretli) |
| Borç / Alacak | yukarıdaki gibi | Borç · Alacak · Çıkan · Giren | `amount` (borç −, alacak +) |
| Bakiye | hayır (önerilir) | Bakiye · Kalan · Hesap Bakiyesi | `balance_after` |
| Dekont / referans no | hayır | Dekont No · Referans · İşlem No · Fiş No | `reference` |
| Karşı taraf | hayır | Gönderen · Alıcı · Karşı Taraf | `counterparty` (şifreli); karşı IBAN okunmaz |
| Hesap no / IBAN (başlık alanı) | hayır | Hesap No · IBAN | Yalnız `BankAccount` ile eşleşme denetimi; saklanmaz |
| Kanal, şube, işlem kodu | — | — | Okunmaz |

**Denetimler.** Dosyadaki hesap `BankAccount` ile uyuşmuyorsa parti reddedilir [S]. Kapanmış döneme ya da bugünden
sonraya düşen satır reddedilir [S]. Parmak izi (`fingerprint`, anahtarlı özet — §5.2.5) `void` olmayan bir satırla
çakışan satır elenir, sayısı önizlemede görünür [S]: böylece kesişen tarih aralıklı iki döküm güvenle aktarılır.
Geri alınmış (`GERI_ALINDI`) partinin `void` satırları eleme dışıdır: yanlış hesap ya da yanlış sütun profiliyle
yapılmış aktarım geri alınıp düzeltilmiş dosyayla yeniden yapılabilir; önizleme "daha önce geri alınmış partiden N
satır yeniden alınacak" der. Bakiye sütunu varsa zincir denetlenir (önceki bakiye + tutar = bakiye); kopukluk eksik
hareket demektir [U]. İlk satırın bakiyesi `OpeningBalance` ya da önceki partinin son bakiyesiyle karşılaştırılır [U].

**Eşleme önerileri** (onay kullanıcıdadır, §7.3): kantin aylık satırı (tutar + ayın 5-15'i + sözleşme), kasa yatırması
(kasada bekleyen tutar), ödeme talimatı (tutar + tarih yakınlığı), sürekli ödeme dosyasının bekleyen faturası,
tekrarlayan açıklama kalıbı (önceki eşleşmeden öğrenilen kategori), faiz ve banka masrafı.

### 8.3 TEFBİS

TEFBİS'e kaydı okul idaresi girer ([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); program otomatik giriş yapmaz (K6). İki yön vardır: programdan TEFBİS'e
girilecekler listesi (dışa), TEFBİS'in "Excel Aktar" çıktısının programa alınması (içe; mutabakat). Varsayılan şema
2009 kılavuzuna ve onun [EK-A işlem tipi listesine](../kesif/kaynaklar/tefbis-2009-kilavuz-ek-a-islem-tipleri.txt)
dayanır; güncel ekran ve çıktı örneği gelince (plan F0-2) "F1 eki" ile kesinleşir.

**(a) TEFBİS'e girilecekler listesi (E18) — dışa, aylık, yonetici.** Muhasibin aylık girişinden sonra alınır
(kullanıcı kararı D2; aylık iş sırası §7.3): TEFBİS'e girilmemiş `KESIN` kayıtlar, TEFBİS ekranının sırasıyla
(gelirler, sonra giderler; tarih sırası). Biçim PDF + xlsx.

| Sütun | Kaynak | Not |
|---|---|---|
| Gelir / Gider | `direction` | Virman ve emanet hareketleri listeye girmez (§5.2.5) |
| İşlem tarihi | `date` | — |
| Kaynak tipi | `tefbis_source_type` | Yalnız gelirde; yedi üst sınıf |
| İşlem tipi: üst grup › tip › alt kalem | `tefbis_type` | `TefbisTypeMapping`; okulun güncel listesi |
| Açıklama | `description` | Şifre çözülerek basılır; kişi adı içerebilir — çıktı kişisel veri taşır, saklama ve imhası kılavuzda |
| Evrak no, evrak tarihi | `document_no`, `document_date` | Makbuzlu kayıtta etkin yaprak bağından seri-cilt-sıra (`LeafUse`) |
| Faaliyet kodu | `activity_code` | — |
| Karar no | `decision` | Yalnız giderde |
| Detay: işlem türü, miktar, birim, birim fiyat, tutar | `LedgerEntryLine` | Tek satırlı kayıtta kayıt tutarı |
| Kesinti | — | Bilgi; tevkifat hesaplanmaz |
| Kişiden gelen kayıtta ad-soyad | `donor_name` | — |
| Kimlik no kaynağı (kişiden gelen kayıtta) | Hesaplanır: etkin yaprak bağı varsa "makbuz seri-cilt-sıra …"; eşlenmiş banka hareketi varsa "dekont referansı …"; ikisi de yoksa "kâğıt kaynak yok — bağışçıdan alınmalı" | T.C. kimlik no **hiçbir dosyaya girmez** (§5.3). K9 kapalıyken yonetici numarayı bu sütunun gösterdiği kâğıttan TEFBİS'e girer; K9 açıksa numara yalnız ekranda, `yonetici` rolüne maskesiz ve erişim günlüğüyle görünür. Banka dekontunda T.C. kimlik no bulunup bulunmadığı DOĞRULANMADI |

"TEFBİS'e girildi" işareti satır satır ya da toplu konur; toplu işaret listenin satır sırasıyla çalışır ve tek
`MarkBatch` satırına bağlanır (§5.2.5); kapanmış dönemin kayıtlarına da konabilir (§5 O2). Ters kayıtla düzeltilen ve
önceden girilmiş kayıtlar ayrı bölümde ("TEFBİS'te düzeltilecek") listelenir; bu bölüm ters kayıtlardan hesaplanır.

**(b) TEFBİS Excel çıktısını içe alma — sürüm 2 (M12, F8+), şema şimdi.** Varsayılan sütunlar (DOĞRULANMADI):

| Alan | Okunur mu | Modeldeki yeri |
|---|---|---|
| Tarih · Gelir/Gider · İşlem tipi · Açıklama · Evrak no · Evrak tarihi · Tutar · Karar no · Kaynak tipi | evet | `TefbisStatementLine` (açıklama şifreli) |
| T.C. kimlik no · Adı soyadı | **hayır** | — (A3; mutabakat için gerekmez) |

Mutabakat satırı `LedgerEntry` ile evrak no + tutar + tarih (± birkaç gün) üzerinden eşler ve üç liste verir: TEFBİS'te
olup defterde olmayan, defterde olup TEFBİS'te olmayan, tutar ya da işlem tipi farklı olan. İşlem tipi bazında banka ↔
defter ↔ TEFBİS üç yönlü özet ve "Devreden" karşılaştırması (`OpeningBalance.tefbis_carryover`) aynı ekrandadır. Eşleşen
satır için "TEFBİS'e girildi" işareti önerilir. Önceki öğretim yılı kayıtlarının banka hesabı ve işletme defteriyle denk
girilmesi (ön değerlendirme §2.5, SGB 02.12.2019 yazısı — korpusta değil) bu ekranın amacıdır.

**(c) İşlem tipi listesinin bakımı.** Tohum EK-A'nın üç düzeyidir; okul kendi TEFBİS ekranındaki listeyi elle ya da
xlsx'ten girer (`TefbisTypeMapping`, `source = OKUL_EKRANI`). Kullanılmış satır silinmez, pasifleşir; yerine geçen
satır `replaced_by` ile bağlanır.

### 8.4 e-Okul personel ve veli listesi (T5)

| Liste | Okunan | Okunmayan | Hedef | Ömür |
|---|---|---|---|---|
| Personel (Kütüphane Defteri'nde OOK01001R1; OAB'de rapor adı örnekle teyit edilir) | Ad, soyad (ya da "Adı Soyadı"); "Görevi" yalnız tür için geçici (öğretmen · yönetici · diğer) | T.C. kimlik no, telefon, branş, unvan, adres, doğum tarihi | `Personnel` (ad şifreli, `member_kind`); `OabPerson` bağı isteğe bağlı (DK öğretmen adayları, alım komisyonu) | Personel kaydı; ayrılış havuzu (Kütüphane F1 eki 7). Ayrıldı işaretlenen ve hiçbir birlik kaydına bağı olmayan personel, ayrılışı izleyen dönem kapanışında silinir (§5.4) |
| Veli (öğrenci listesi türünde, veli sütunlu e-Okul raporu; rapor kodu DOĞRULANMADI, örnek gelince "F1 eki") | Veli adı-soyadı (tek sütun ya da ad + soyad); öğrencinin sınıfı ve şubesi | Öğrencinin adı ve numarası, T.C. kimlik no, telefon, adres, yakınlık, e-posta — bütün diğer sütunlar; kaynak dosyadaki satır sırası da tutulmaz | `ParentRoster` (ad şifreli + kör indeks, sınıf düz metin); bir satır bir öğrenci | Dönem kapanışında silinir (§5.4, §7.8); genel kuruldan sonra elle de silinebilir |

**Aydınlatma.** Personel aktarımından önce E04'ün personel metni, veli listesinin kullanıldığı genel kurul davetinde
(E07) kısa aydınlatma paragrafı yer alır (§3.4). Aktarım ekranı E04'ün ilgili metnini gösterir ve okul kartında veri
sorumlusu alanı boşken uyarır.

**Veli listesi kuralları.** (1) Dosyadaki sınıflar dönem içindeki önceki partide aynı sınıfların satırlarının yerini
alır; dosyada olmayan sınıflara dokunulmaz (Kütüphane EK-21 deseni). (2) Önizleme yalnız sayıları gösterir (sınıf başına
satır sayısı); adlar ekranda listelenmez. (3) Liste yalnız iki iş içindir: genel kurul katılım cetvelinin basımı ve
sayımı; aday olacak velinin adının `OabPerson`'a kopyalanması. (4) Veli adı taşıyan çıktıları (E07 sınıf teslim
çizelgesi, adlı E08 katılım cetveli) yalnız `yonetici` basar; program dosyalarını saklamaz, yalnız iz satırı kalır
(§5.2.8; R9). Listeyi aktarmak ve veli adı taşıyan çıktıyı almak "kişisel veri içeren dışa aktarım" yetkisidir
(§4.4.2). (5) Telefon ve iletişim yoktur: genel kurul daveti elden yazılı dağıtılır ([md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)), program SMS ya da e-posta göndermez. (6) İskelet envanteri §2.8'de ALMA yazılan öğrenci
ayrıştırıcısının (`excel_ogrenci.py`) başlık bulma ve Türkçe katlama kısmı veli listesi için UYARLA'ya döner (F1b).

### 8.5 Yıl sonu arşiv paketi (PDF + xlsx + JSON)

Dönem `KAPANDI` olduktan sonra, kapanışın kişisel veri silmelerinden **sonra** üretilir (§7.8; denetim KM-5); yarıda
kalırsa kapanmış dönemden yeniden üretilir (yeniden basım, §5 O2). Amaç: defter ve belgelerin okulda saklandığı süre
boyunca ([md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) dönemin programdan bağımsız okunabilmesi. Yedek (`.odbak`) programa geri yüklemek
içindir ve veritabanıyla birlikte ekleri ve üretilmiş evrakı da içerir (§4, R10); arşiv paketi programsız okumak
içindir.

| Yol | İçerik | Biçim |
|---|---|---|
| `00-BENIOKU.txt` | Paketin nasıl açılıp okunacağı; okul, dönem, oluşturma tarihi, program sürümü, kural paketi ve revizyonu, şema sürümü; ilk dönemse geçiş kurulumu bilgisi (programa başlama günü, devralınan kurul, açılış bakiyesinin kanıtı — §7.9) | düz metin (UTF-8) |
| `01-evrak/` | Dönemin `GeneratedDocument` dosyaları, evrak türü klasörleriyle; yerini alan eski sürümler `eski/` altında. Veli adı taşıyan belgeler (E07 çizelgesi, adlı E08) **girmez**: program dosyalarını hiç saklamaz; yerlerine `01-evrak/kisi-listesi-izleri.txt`'de tür, tarih, satır sayısı ve sha256 satırı durur | PDF (Word isteğe bağlı) |
| `02-defterler/` | Gelir-gider kayıtları (defter düzeninde, düzeltme satırlarıyla); banka hareketleri ve eşleşmeler; karar dizini (defterde sakat kararlar ayrı bölümde); gelen-giden evrak; koçan envanteri ve yapraklar; harcama dosyaları dizini; organ üyelikleri; genel kurul özetleri (katılım sayılarıyla); kira, arz ve pay çizelgeleri; TEFBİS girildi listesi; sapma kayıtları (`ComplianceItem`); denetim izi dökümü (§4.6.2 kuralıyla; kişisel veri taşımaz) | xlsx |
| `03-veri/` | Her model için kayıt listesi; şifreli alanlar çözülmüş — **süreli kişisel veri alanları hariç** (§5.4 `SURELI_KISISEL_ALANLAR`); şema `docs/arsiv-paketi.md`'de tek sürümlü | JSON |
| `04-ekler/` | Saklama süresi içindeki `Attachment` dosyaları; `OZEL_NITELIKLI` olanlar varsayılan hariç | özgün biçim |
| `05-icerik-listesi.pdf` | [Arşiv Yön. md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) "Dosya/Klasör İçerik Listesi" kalıbında içerik listesi (E39) | PDF |
| `SHA256SUMS.txt` | Her dosyanın özeti | düz metin |

**Dışarıda kalanlar.** Alan düzeyinde dışlama listesi §5.4'teki tek sabitten üretilir ve testle kilitlenir: veli
listesi ve veli adı taşıyan belgeler; bağışçı T.C. kimlik no'su; istekli iletişim bilgisi (`Bidder.contact_*`),
katılım engelinin dayanağı ve eleme notu; üyelik düşme gerekçesi ve görev alma engelinin dayanağı; özel nitelikli ekler
(varsayılan; açık seçimle girer); şifreleme anahtarları ve hesap bilgileri; erişim günlüğü (§4.6.4; saklama süresi
arşivinkinden kısadır); adlı E07 ve E08 (R9). `docs/arsiv-paketi.md` şemasının bağlayıcı kuralı: **süreli kişisel
veri alanı pakete girmez** — kapanışta henüz boşaltılmamış olsa da (ör. süreci yeni kapanan isteklinin iletişimi).

**Koruma.** Paket kişisel veri taşır ve çoğunlukla USB'ye kopyalanır; MEB Bilgi ve Sistem Güvenliği Yönergesi
taşınabilir ortamdaki önemli veriyi şifreli ister ([BSG Yönergesi md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)). Öneri: AES-256 şifreli ZIP (7-Zip ve Pardus arşiv
yöneticisi açar; Windows Gezgini açamaz, BENIOKU bunu yazar); parolayı kapanışta yönetici belirler, kurtarma anahtarı
gibi paketten ayrı saklanır. Yeni bağımlılık `pyzipper` §11 B20'dir (ADAY, F4; §15 B-10).
PDF'lerin uzun süre okunabilirliği için PDF/A çıktısı (WeasyPrint) §9.1'de karara bağlanır.

### 8.6 Diğer çıktılar

| Çıktı | Kim | Not |
|---|---|---|
| Deftere geçirilecek kayıtlar (aylık, E17) | muhasip | §7.3; PDF + xlsx; asgari sütunlar §15 A-12; tasdikli defterin sayfa düzeninde (`OfficialBook.lines_per_page`), "şu sayfalara geçirildi" toplu işaretiyle |
| Banka mutabakat çizelgesi (aylık, E19) | muhasip | §7.3 |
| Kişi dökümü ([KVKK md. 11](../mevzuat/6698-kvkk.md#madde-11) başvurusu) | yonetici | Bir kişinin üyelik, aday, bağış (ad), ödeme ve katılım kayıtları; erişim günlüğüne yazılır (`KISI_DOKUMU`, §4.6.4) |
| İhlal dökümü ([KVKK md. 12/5](../mevzuat/6698-kvkk.md#madde-12)) | yonetici | Seçilen tarihte programda bulunan veri kategorileri ve kişi sayıları, kişisiz; erişim günlüğüne yazılır (`IHLAL_DOKUMU`); bildirim okulun işidir (§4.4.6-6) |
| Denetim tabloları ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1, [TKB E.4 §3.3](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-3) Tablo 2, [TKB E.4 §4](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4) Tablo 3, [TKB E.4 §4.1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4-1) Tablo 4) | yonetici | Kişisiz sayılar; M12b sürüm 2, veri bugünden hazır |
| Duyuru web metni | yonetici | Tek HTML dosyası, dış bağlantısız; program yayımlamaz, okul sitesine kullanıcı taşır. Taşımacı listesi (E56) ilan süresi bitince sitedeki kopyanın kaldırılması panoda hatırlatılır (D5) |

---

## 9. Evrak kataloğu

Program birliğin ve okulun evrakını **hazırlar**; karar defterinin, tasdikli defterlerin, makbuz koçanının ve TEFBİS
kaydının yerine geçmez (konum, §9.2). Kaynaklar: genel OAB seti (`GNL-OAB-FR-001…023`, `GNL-OAB-RH-001`; CC BY 4.0),
OYS'nin 19 belge şablonu (envanter §5) ve Yönetmeliğin ve Servis Usul ve Esaslarının resmî ekleri. Program kodu
**`E01`…`E79`**; §7'de adı geçen her belge bu kodlardan birine bağlıdır ya da §9.7'de "program üretmez" ya da "program
belgesi (katalog dışı)" diye yazılıdır.
Belge altlığında yalnız "OAB Defteri · E07 · Sayfa n/m" yazar; kural paketi revizyonu basılmaz (evrak izinde tutulur).
Kütüphane Defteri'nin evrak kodları bu belgede "KütD-E13" biçiminde önekle anılır (OAB'nin E13'ü ayrı belgedir).

### 9.1 İlkeler

1. **Tek içerik, iki çizici** (T2). Belgenin cümleleri, tabloları ve imza blokları bir kez Python'da içerik modeli
   olarak kurulur; Word (python-docx) ve PDF (WeasyPrint) yalnız düzeni çizer. Listeler ayrıca xlsx (openpyxl) verir;
   duyurular ayrıca tek dosyalık, dış kaynaksız HTML verir (okul web sitesine elle konur; ağ servisi yok).
2. **Evrak izi.** Her üretim bir `GeneratedDocument` kaydıdır: kod, dönem, kural paketi (kimlik + rev), üreten
   kullanıcı, zaman, **içerik JSON'u** (`content_json`, şifreli), **içerik özeti** (bu JSON'un kanonik biçiminin
   SHA-256'sı; docx zip baytı değil) ve dosya özetleri. Yeniden basım kayıtlı JSON'dan çizilir; bu yüzden kapanmış
   dönemin belgesi program, şablon ya da ana veri değişse de aynı içerik özetini verir (§6.2-6; UY-13). **İstisna
   (R9):** veli adı taşıyan E07 ve E08'i yalnız `yonetici` basar; program bu iki belgenin dosyasını ve içerik JSON'unu
   saklamaz (yalnız sha256, satır sayısı, tarih), arşiv paketine girmezler, yeniden basılamazlar; basılı aslı genel
   kurul tutanak dosyasındadır. Hesap teslim pusulasının (E63) dosyası da saklanmaz; hesap açıkken yeniden üretilir.
3. **Tek kaynak** (OYS ilkesi, AYNEN). Aday listesi, tutanak, sonuç bildirimi, faaliyet raporu ve devir-teslim aynı
   kayıtlardan dolar; birbiriyle çelişemez. Alım komisyonu yalnız `OrganMembership(ALIM_KOMISYONU)`'ndan okunur;
   harcama dosyası bu üyeliklere bağ verir, kişi listesini ayrıca tutmaz (UY-20).
4. **Türkçe ve biçim.** Büyük harf yalnız `tr_upper` ile; `text-transform`, `w:caps` ve çıplak `.upper()` yasak.
   Dışa giden resmî yazılar (E12, E25, E35, E40, E44, E65, E66, E70, E72, E73, E76, E77, E78, E79)
   [RYUE md. 7](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-7) (biçim),
   [md. 11](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-11) (sayı),
   [md. 12](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-12) (tarih,
   `gg.aa.yyyy`), [md. 13](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-13)
   (konu), [md. 14](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-14)
   (muhatap) ve [md. 17](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-17)
   (imza bloğunda ad + SOYAD + unvan) biçimindedir. Sayfa bütçesi gerçek uzunlukta uydurma veriyle sınanır.
5. **KVKK.** İlan panosu ve internet çıktılarında (E06, E29, E30, E56) kişi adı yoktur, başkanınki de: imza
   "Okul-Aile Birliği Yönetim Kurulu" ya da "Taşımacıyı Tespit Komisyonu" olur. **Tek istisna E56'dır** (kullanıcı
   kararı D5, mevzuat istisnası): [U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10)
   sözleşme imzalanan taşımacıların bilgisinin panoda ve web sitesinde yayımlanmasını ister; yalnız taşımacının
   ad/unvanı, araç plakası ve güzergâh basılır; telefon, adres, T.C. kimlik no, şoför ve veli verisi basılmaz; ilan
   süresi bitince sitedeki kopyanın kaldırılması hatırlatılır (`Announcement.removed_board_on`). Kişi adı taşıyan iç
   belgeler "Kişisel veri içerir — asılmaz, okul dışına verilmez" dipnotu taşır. T.C. kimlik no hiçbir belgeye ve
   dosyaya girmez, K9 açıkken de: bağış izleme çizelgesinde (E20) yalnız "kimlik no kayıtlı: evet/hayır", TEFBİS
   listesinde (E18) yalnız "kimlik no kaynağı" sütunu vardır (KM-14; §5.3). Kişisel verinin toplandığı yerde verilen
   belgeler (E07 daveti, E21, E46 ve E58'de belge teslimi, E48, E50) kısa aydınlatma paragrafı taşır; tam metin E04'tür
   ve paragraf onun yerini söyler (KM-6). Adli sicil ve sağlık belgelerinin içeriği basılmaz, yalnız "teslim
   alındı" + tarih. Parola hiçbir belgede yoktur (E63).
6. **Uyarı kutusu resmî evraka basılmaz.** OYS'nin `_compliance_warnings.html` parçası alınmaz: kural sapmasının
   gerekçesi `ComplianceItem` ve denetim izinde kalır, istenirse ayrı iç belge olarak dökülür (KE-16).
7. **Mevzuat lafzı kilidi.** Resmî ekin metnini taşıyan belgeler (E42 EK-2 kira sözleşmesi, E55 servis sözleşmesi,
   E75 servis tip şartnamesi) metni `docs/mevzuat/` korpusundan alır ve testte karakter karakter karşılaştırılır;
   yalnız boşluk (`……`) alanları dolar. Servis tip şartnamesi sözleşmenin eki ve ayrılmaz parçasıdır
   ([U-E EK-1 md. 2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1-madde-2)).
8. **Biçim kararları** (varsayılanla ilerler; kesinleşmesi kullanıcının):
   - **Yazı tipi.** [RYUE md. 7](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-7)
     "Times New Roman" 12 ya da "Arial" 11 punto ister. Varsayılan: Word çıktısında yazı tipi adı "Times New Roman",
     12 punto yazılır, yazı tipi gömülmez (dosya açıldığı sistemin yazı tipini kullanır); PDF'te Windows'ta sistemin
     Times New Roman'ı, bulunmayan sistemde (Pardus) ölçüleri onunla aynı, açık lisanslı Liberation Serif kullanılır
     (pakete girer, §11); DejaVu yalnız eksik glif yedeğidir. Pardus'ta Word dosyası açan programın yerine koyduğu
     yazı tipiyle görünür, bu kılavuzda yazılır. Sayfa bütçesi (§10.5) Liberation Serif ile sınanır (iskelet envanteri
     §11-5; §11.3).
   - **PDF/A.** Mevzuat istemez (korpusta hüküm yok). Varsayılan: yalnız arşiv paketine (E39) giren PDF'ler PDF/A
     olarak üretilir (uzun süreli okunabilirlik, §8.5); günlük baskı olağan PDF'tir. WeasyPrint'in PDF/A kipinin
     paketlenen sürümde bulunduğu ve çıktının bir doğrulayıcıdan geçtiği F4'te sınanır (DOĞRULANMADI).
   - **Birlik antedi.** [RYUE md. 10](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-10)
     başlığı gönderen idarenin adıyla kurar; birlik okul bünyesinde kurulur ve okulun adını alır
     ([md. 5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-5)). Varsayılan: okul idaresinin yazıları (§9.3
     "Kendi yazıları" ve "Okul idaresinin resmî yazıları") okul antedini (`letterhead.py`) aynen kullanır; birliğin
     kendi belgeleri aynı antedin altına "Okul-Aile Birliği" satırını ekler (md. 10/2'deki birim satırı gibi); ayrı
     logo yoktur. E01-E03 F1c'de basıldığı için bu karar F1c'nin ön koşuludur (iskelet envanteri §11-6; §12.B).

### 9.2 Konum cümlesi

Üç kalıp vardır; **gövdenin sonunda, imza bloklarının hemen üstünde** 9 punto yazılır (altlıkta değil; altlıkta
yalnız "OAB Defteri · Exx · Sayfa n/m" durur) ve ekrandaki önizlemede de görünür. Kısa adlar kodda tam adla yazılır;
"KD" kısaltması aile kalıntı kalıbıyla çakıştığı için kullanılmaz (UY-20).

| Kısa ad | Metin | Dayanak | Belgeler |
|---|---|---|---|
| **KDT** | "Bu metin yönetim kurulu karar taslağıdır. Kararlar noterce tasdikli yönetim kurulu karar defterine el ile yazılarak imzalanır; bu belge karar defterinin yerine geçmez." | [13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E01, E03, E15, E22 (koçan seri no'ları), E36, E68 |
| **TFB** | "Birliğin gelir ve gider kayıtları ile diğer mali işlemleri TEFBİS'e okul idaresince kaydedilir; bu belge TEFBİS kaydının yerine geçmez." | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E13, E18, E20, E27, E28, E31, E34, E60 |
| **DFT** | "Bu döküm il/ilçe millî eğitim müdürlüğünce tasdikli deftere geçirilmek üzere hazırlanmıştır; defterin yerine geçmez." | [23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E17, E23 |

KDT taşıyan belgelerin başlığında "TASLAK — karar defterine geçirilecek metin" ibaresi vardır (E68 dizininde "Karar
defteri dizini — defterin yerine geçmez"); "deftere işlendi" işareti (defter sıra no ve sayfa) konduktan sonra da
taslak ibaresi kalkmaz. YK kararına dayanan yazılar (E40 bildirimi, E41 cevabı, E65, E66, E71) karar taslağı değildir,
KDT taşımaz; kararın kendisi E15'tedir (EK-17). Kantin ve servis ekranlarında ayrıca "Program komisyon kararının yerine geçmez" cümlesi
görünür; bu cümle komisyonun kendi evrakına (E54) basılmaz.

### 9.3 İmza blokları

Belgeyi hazırlayan organ imzalar: YK belgelerini YK (başkan; görevine göre muhasip ve sekreter), DK belgelerini DK
asıl üyeleri, genel kurul belgelerini divan. **Okul müdürü yönetim kurulu üyesi değildir**; YK belgelerinde yazar ya
da imzacı olarak yer almaz. Müdür yalnız mevzuatın ona rol verdiği yerde ve şu bloklarla görünür (MB-3, MB-15):

| Müdürün bloğu | Belgeler | Dayanak |
|---|---|---|
| **Çağıran ve imzacı** | E05 — yeni okulda genel kurul daveti; müdürün olağanüstü genel kurul çağrısı | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25); M-5 |
| **Görüldü** (müdür çağırmadıysa) | Genel kurul belgeleri: E05, E10, E64 (yeter sayı sağlanamadıysa, KE-10); genel kurul sonunda başlayan devir-teslim E37 | [10/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) |
| **Teslim alan** | E03 (temsilcilerin gireceği kurullar okulundur), E13 (sonuç bildirimi), E21 (ayni bağış), E31 (aylık bildirim) | [27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27); [16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) |
| **Mühürleyen** (okul müdürlüğü) | E22 (koçan ve belgeler kurum mührüyle mühürlenir) | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), 16/7 |
| **Kontrol eden** | E38 (işlem dosyası) | [27/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) |
| **Uygunluk görüşü** | E36 (etkinlik) | [6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) |
| **Sorumlu** | E24 (arz bedeli takibi) | [17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) |
| **Kendi yazıları** (müdür hesabından; taslağı `yonetici` hazırlamaz, M-11) | E25, E35; ayrıca çağıran olduğunda E05 (yukarıda). K2'deki müdür yazıları bu **dördüdür**: harcama talebi, md. 27/3 uyarısı, yeni okulda genel kurul daveti, olağanüstü genel kurul çağrısı | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) (1. cümle); K2 |
| **Okul idaresinin resmî yazıları** (taslak `yonetici`, KE-19) | E12, E40 üst yazısı, E44, E70, E72, E73, E76, E77 | [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) (2. cümle), [28/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-28); [U-E 8/5-6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [OSAY 6/1-b](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-6) |
| **Servis komisyonunun başkanı** | E48-E57, E74, E75, E78, E79 | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [U-E 10/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) |

Bunların dışında müdür bloğu basılmaz: DK belgeleri (E02, E32, E33) denetleyenin bağımsızlığı gereği, YK'nin mali
belgeleri (E28, E34) ve personel dosyası (E61) müdür bloğu taşımaz. Bloklar organ üyeliğinden dolar; görev boşsa
basımda uyarı verilir, blok "………" kalır.

OYS'den gelen hataların düzeltilmesi:

| Belge | OYS'de | OAB Defteri'nde | Dayanak |
|---|---|---|---|
| GK davetiyesi (E05) | Okul Müdürü | Çağırana göre: olağanda ve YK çağrısında Birlik Başkanı (YK adına) + Sekreter, müdür "Görüldü"; yeni okulda ve müdürün olağanüstü çağrısında Okul Müdürü; DK çağrısında DK asıl üyeleri; %10 başvurusunda KE-11 | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Tahmini bütçe (E28) | Okul Müdürü; "onaylandı" | YK adına Birlik Başkanı + Muhasip (+ asıl üyeler); "genel kurulda görüşüldü" | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| Gelir-gider çizelgesi (E34'e katıldı) | Okul Müdürü | Muhasip + Birlik Başkanı; kesin hesap YK asıl üyeleriyle | [13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| Yeter sayı yok tutanağı (E64) | Birlik Başkanı + Okul Müdürü | Birlik Başkanı + Sekreter; "Görüldü — Okul Müdürü" (mevzuat imzacı saymaz, KE-10) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) |
| Aday listeleri (E09) | DK öğretmen koltukları listede | Yalnız GK'nin seçtiği koltuklar; öğretmenler bilgi satırı | [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Servis komisyon kararı (E54) | "Oy birliği ile" sabit | Oylama sonucu; muhalif üyenin gerekçesi ve imzası | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) |
| Kira sözleşmesi (E42) | Servis maddeleri, "Taşımacı" tarafı | EK-2 tam metni; Birlik Başkanı + Kiracı + varsa esnaf odası temsilcisi | [21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) |

### 9.4 Servis söz dağarcığı ve EK-3'ün lafzı

Servis evrakında (E48-E58 ve E73-E79) "ihale", "teklif", "eksiltme" yazılmaz: 30.05.2018 metni eksiltmeyi ve teminatı
kaldırdı, seçim [U-E 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'deki ölçütlerle yapılır.
Kantin evrakında "ihale" serbesttir (md. 20 "kantin kiralama ihaleleri" der).

| OYS'de / eski metinde | Servis evrakında | Dayanak |
|---|---|---|
| ihale, servis ihalesi | servis çalıştırma işi · taşımacının tespiti | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5), [OSAY 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) |
| ihale ilanı | servis çalıştırma işinin ilanı | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) |
| teklif, teklif toplama | başvuru · başvuru dosyası · dosyaların teslimi | [U-E 7/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) |
| ihale tarihi / saati | dosyaların açılma tarihi / saati | [U-E 8/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) |
| ihale komisyonu | Taşımacıyı Tespit Komisyonu | [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) |
| en düşük teklif | — (yürürlükte değil; kaldırılır) | U-E korpus notu ([md. 8](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) sonrası) |
| istekli | istekli (değişmez) | [U-E 3/1-c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) |

Lafız sorunları ve öneri:

- **EK-3 4. kriter** ("İsteklinin taşıma işini yaptığı aynı okula **teklif** vermesi halinde"). Seçenekler: (a) lafzı
  tırnak içinde aynen basmak, (b) "teklif"i "başvuru" ile değiştirmek — mevzuat metni değiştirilemeyeceği için
  reddedilir, (c) puanlama cetvelinde kriteri kısa adla basmak: "4) Aynı okulda hâlen taşıma işini yapan istekli
  (EK-3, kriter 4)". **Öneri (c)** (KE-8): cetvel mevzuat metni değil, komisyonun değerlendirme aracıdır; kriter
  numarası ve atıf kaynağı gösterir, lafız evrakta alıntılanmaz.
- **Suç adı "ihaleye fesat karıştırma".** Servis sözleşmesinin (U-E EK-2 md. 4, 7) ve tip şartnamenin (EK-1 md. 6;
  E75) lafzında TCK suç adı olarak geçer; metin değiştirilemez. **Öneri** (KE-9): söz dağarcığı testinin tek
  istisnası bu tam ibaredir.

### 9.5 Katalog — kimlik, dayanak, kaynak, biçim, faz

Biçim: "docx+pdf" iki çizici · "xlsx" ek döküm · "html" web duyurusu. Dayanak atıflarında yalın numara OAB
Yönetmeliğidir; kısaltmalar §6.4'teki gibidir (BSG = MEB Bilgi ve Sistem Güvenliği Yönergesi); TKB E.4 rehberdir,
mevzuat değildir (kabul ölçütü). Faz sütunu planın §3'üne uyar (R3).

| Kod | Belge | Dayanak | Kaynak şablon | Biçim | Faz |
|---|---|---|---|---|---|
| E01 | YK görev bölümü, imza yetkisi ve temsilci karar taslağı | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [13/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | GNL-OAB-FR-006 | docx+pdf | F1c |
| E02 | Denetleme Kurulu görev bölümü tutanağı ve denetim planı | [14/1-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | GNL-OAB-FR-011 | docx+pdf | F1c |
| E03 | Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi | [13/4-5, 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [17/1-b-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); [OKY 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OKY 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25); [OÖİKY 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57); [SEY 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6); [RPD 16](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16); [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3) | GNL-OAB-FR-022 | docx+pdf | F1c |
| E04 | Kişisel veri aydınlatma metni (veli ve üye · personel · istekli, kiracı ve çalışan · bağışçı ve tedarikçi) | [KVKK md. 10](../mevzuat/6698-kvkk.md#madde-10) | yeni (KütD-E13 kalıbı) | docx+pdf | F2 (metni F1b içe aktarma ekranında) |
| E05 | Genel kurul toplantı çağrısı ve gündemi (dosya nüshası; duyuru kanıtıyla) | [9/1-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [10/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) | GNL-OAB-FR-002 A-B, D; OYS `davetiye.html`, `gundem.html` | docx+pdf | F2 |
| E06 | Genel kurul duyurusu — ilan panosu ve internet sayfası (kişisiz) | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | GNL-OAB-FR-002 C | pdf, html | F2 |
| E07 | Üyelere elden yazılı davet ve sınıf teslim çizelgesi | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [7/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) | GNL-OAB-FR-002 D (elden bildirim satırı) | docx+pdf | F2 |
| E08 | Genel kurul katılım cetveli | [10/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | GNL-OAB-FR-003 B-C; OYS `build_imza_surkusu_xlsx` | docx+pdf, xlsx | F2 |
| E09 | YK ve DK (veli koltuğu) aday listeleri | [10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1-a, b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [12/1, 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-004 D; OYS `aday_listeleri.html` | docx+pdf | F2 |
| E10 | Genel kurul toplantı tutanağı | [9/2-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [10/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-004; OYS `tutanak.html` | docx+pdf | F2 |
| E11 | İbra edilmeyen muhasebe evrakının teslim tutanağı (divan) | [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-005 B (satır 9) | docx+pdf | F2 |
| E12 | İbra edilmediğine dair il/ilçe MEM'e resmî yazı | [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | yeni (RYUE biçimi) | docx+pdf | F2 |
| E13 | Genel kurul sonuç bildirimi (okul müdürlüğüne) | Açık bildirim hükmü yok (DOĞRULANMADI); okul uygulaması — dolaylı: [13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (okul müdürüyle koordinasyon), [27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-005 A, C | docx+pdf | F2 |
| E14 | Yıllık iş takvimi | kural paketinin süre kuralları (§6.4) | GNL-OAB-RH-001 Bölüm 6 | pdf, xlsx | F2 |
| E15 | YK toplantı gündemi ve karar taslağı | [13/3, 13/5, 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | GNL-OAB-FR-007 | docx+pdf | F3 |
| E16 | YK toplantı ve katılım izleme çizelgesi | [13/3, 13/6, 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7), [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-008 | docx+pdf, xlsx | F3 |
| E17 | Gelir-gider defterine geçirilecek kayıtlar (aylık) | [23/1-ç, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (saha.md 1b sütunları) | pdf, xlsx | F3 |
| E18 | TEFBİS'e girilecekler listesi | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (K6; 2009 kılavuzu alanları) | pdf, xlsx | F3 |
| E19 | Banka mutabakat dökümü (banka ↔ defter) | [16/1, 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | yeni (K1) | pdf, xlsx | F3 |
| E20 | Bağış kabul ve kayıt izleme çizelgesi | [6/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [16/1-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [24](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24); [G.2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) | GNL-OAB-FR-014 A, C | docx+pdf, xlsx | F3 |
| E21 | Ayni bağış teslim tutanağı (okul müdürlüğüne) | [16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [TMY 16/1](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) | GNL-OAB-FR-014 B | docx+pdf | F3 |
| E22 | Defter, makbuz ve belge tasdik-kayıt çizelgesi; koçan yaprak dökümü ve biten koçanların teslimi | [16/5-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/1-2, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1) | GNL-OAB-FR-015 | docx+pdf, xlsx | F3 |
| E23 | Gelen-giden evrak defterine geçirilecek kayıtlar | [23/1-c, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni | pdf, xlsx | F3 |
| E24 | Kantin kira tahsilat, arz bedeli ve pay dağıtım izleme çizelgesi | [17/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4), [md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7), [md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) | GNL-OAB-FR-021 | docx+pdf, xlsx | F3 |
| E25 | Okul yönetimi ihtiyaç ve harcama talep yazısı | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [OKY 78/4-e](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-78) | GNL-OAB-FR-016 | docx+pdf | F4 |
| E26 | Mal ve hizmet alım komisyonu piyasa araştırması ve karar tutanağı | [18/1, 18/3-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-017 | docx+pdf | F4 |
| E27 | Harcama belgesi kontrol ve ödeme onay formu; banka ödeme talimatı (kasa çıkış bölümüyle) | [18/1-3, 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | GNL-OAB-FR-018 | docx+pdf | F4 |
| E28 | Tahmini bütçe | [11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 A; OYS `tahmini_butce.html` | docx+pdf, xlsx | F4 |
| E29 | Bütçe duyurusu (pano + internet; kişisiz) | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 A, C | pdf, html | F4 |
| E30 | Dönemlik gelir-gider duyurusu (kişisiz) | [13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 B, C | pdf, html | F4 |
| E31 | Birlik başkanının okul müdürüne aylık bildirimi | [18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [27/2-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-009 | docx+pdf | F4 |
| E32 | Denetleme Kurulu ara denetim raporu | [14/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [TKB E.4 §3-4](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3) (rehber) | GNL-OAB-FR-012; OYS `dk_faaliyet_raporu.html` | docx+pdf | F4 |
| E33 | Denetleme Kurulu nihai (yıllık) raporu | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-013; OYS `dk_faaliyet_raporu.html` | docx+pdf | F4 |
| E34 | YK yıllık faaliyet raporu ve kesin hesap cetveli (dönem gelir-gider çizelgesi) | [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [13/1, 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-023; OYS `yk_faaliyet_raporu.html`, `gelir_gider_cizelgesi.html` | docx+pdf, xlsx | F4 |
| E35 | Okul müdürünün birlik başkanına yazılı uyarısı | [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) (1. cümle) | yeni (RYUE biçimi) | docx+pdf | F4 |
| E36 | Sosyal-kültürel etkinlik / kampanya gelir-gider kayıt ve onay formu | [6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [15/1-c, 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25); [SEY 5/8](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-5) | GNL-OAB-FR-020 | docx+pdf | F4 |
| E37 | Devir-teslim tutanağı (kasa sayımı bölümüyle) | [10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | GNL-OAB-FR-005 B, C | docx+pdf | F4 |
| E38 | OAB işlem dosyası kapak ve kontrol listesi | [23/1, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26), [27/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-001 | docx+pdf | F4 |
| E39 | Yıl sonu arşiv paketi içerik listesi | [23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [DAHY md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) (kıyasen) | yeni | pdf, xlsx, JSON | F4 |
| E40 | Kantinin kiralanacağına dair bildirim (okul müdürlüğü vasıtasıyla il/ilçe MEM'e) | [G.2024/35 II-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-1) | yeni | docx+pdf | F5 |
| E41 | Yeniden kiralama talebine yazılı cevap | [21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 I-3, I-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) | yeni | docx+pdf | F5 |
| E42 | Kantin ve benzeri yerleri kiralama sözleşmesi | [21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) | Yön. EK-2 (korpus metni) | docx+pdf | F5 |
| E43 | Kantin yer teslim ve tahliye tutanağı | [21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 12](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-12), [md. 13](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-13) | yeni | docx+pdf | F5 |
| E44 | Sözleşme örneğinin millî emlak birimine gönderilmesi | [21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | yeni (RYUE biçimi) | docx+pdf | F5 |
| E45 | Yenilenen kira bedelinin (TÜFE) il/ilçe MEM'e bildirimi | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) | yeni | docx+pdf | F5 |
| E46 | Kantin işletmeci ve çalışan belge izleme çizelgesi | [20/6-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [HEY 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5) | yeni | pdf, xlsx | F5 |
| E47 | Kantin kiracısına yükümlülük ihtarı (15 gün) | [22/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) | yeni | docx+pdf | F5 |
| E48 | Servis çalıştırma işinin ilanı | [U-E 5/3-4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5), [U-E 6/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6) | OYS `ihale_ilani.html` | docx+pdf | F6 |
| E49 | İlan asma ve indirme tutanağı | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | OYS `ilan_asma_tutanagi.html`, `ilan_indirme_tutanagi.html` | docx+pdf | F6 |
| E50 | Tip şartname (EK-1) teslim tutanağı | [U-E 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5); [U-E EK-1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1) | OYS `sartname_teslim_tutanagi.html` | docx+pdf | F6 |
| E51 | Başvuru dosyası teslim tutanağı | [U-E 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) | OYS `evrak_teslim_tutanagi.html` | docx+pdf | F6 |
| E52 | Belge kontrol ve tespit tutanağı | [U-E 8/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [U-E 6/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6) | OYS `evrak_kontrol_cetveli.html` | docx+pdf | F6 |
| E53 | EK-3 puanlama cetveli (yalnız itiraz / yeni okul) | [U-E 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | OYS `puanlama_cetveli.html` | docx+pdf | F6 |
| E54 | Taşımacının tespiti değerlendirme tutanağı ve komisyon kararı | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [U-E 8/2, 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [OSAY 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) | OYS `komisyon_karari.html` | docx+pdf | F6 |
| E55 | Okul servis araçları sözleşmesi | [U-E 10/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10); [U-E EK-2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2) | OYS `sozlesme_taslagi.html` (servis kısmı) + korpus metni | docx+pdf | F6 |
| E56 | Sözleşme imzalanan taşımacıların ilanı | [U-E 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | yeni | pdf, html | F6 |
| E57 | Yeniden çıkma tutanağı | [U-E 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | OYS `tek_katilimci_tutanagi.html` (yeniden adlandırılır) | docx+pdf | F6 |
| E58 | Servis belge izleme çizelgesi | [U-E 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9); [OSAY 4/1-f](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-4), [OSAY 9](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | yeni | pdf, xlsx | F6 |
| E59 | Denetim dosyası: TKB E.4 Tablo 1-4 | [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26); [TKB E.4 §3.2-4.1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) (rehber) | yeni | xlsx, pdf | F8+ |
| E60 | TEFBİS Excel mutabakat raporu (banka ↔ defter ↔ TEFBİS) | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (K6) | xlsx, pdf | F8+ |
| E61 | Birlik personeli istihdam dosyası ve özlük takip formu | [6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6); [5510 md. 11](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-11), [md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) | GNL-OAB-FR-019 | docx+pdf | F8+ |
| E62 | Yıllık ücretli izin kayıt belgesi | [4857 md. 53](../mevzuat/4857-is-kanunu.md#madde-53), [md. 56](../mevzuat/4857-is-kanunu.md#madde-56) | yeni | docx+pdf, xlsx | F8+ |
| E63 | Hesap teslim pusulası | [BSG Yön. md. 9/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9), [md. 10/1-2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) | yeni | pdf | F1b |
| E64 | Genel kurul yeter sayı tespit tutanağı (sağlandı / sağlanamadı) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/5, 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | GNL-OAB-FR-003 A, D; OYS `yeter_sayi_yok.html` | docx+pdf | F2 |
| E65 | Yedek üyenin asıl üyeliğe çağrı yazısı | [13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); DK yedeğinde [14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | yeni (RYUE biçimi) | docx+pdf | F3 |
| E66 | Bankaya imza yetkisi bildirim yazısı | [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | GNL-OAB-FR-006 C (bildirim alanı); yeni (RYUE biçimi) | docx+pdf | F3 |
| E67 | Makbuz yaprağı ve koçan iptal/kayıp tutanağı | [16/5, 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | GNL-OAB-FR-015 B (notu) | docx+pdf | F3 |
| E68 | Karar defteri dizini | [13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni | pdf, xlsx | F4 |
| E69 | Dönem kapanış denetim listesi | [23/1, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); §7.8 kapanış denetimi | yeni | pdf | F4 |
| E70 | Okul müdürünün il/ilçe MEM'e bildirimi ve denetim talebi | [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) (2. cümle) | yeni (RYUE biçimi) | docx+pdf | F4 |
| E71 | Kantin kira sözleşmesinin fesih bildirimi | [22/1, 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22); [EK-2 md. 7/4. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7), [md. 15](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-15), [md. 22/2. paragraf](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) | yeni | docx+pdf | F5 |
| E72 | Kiralanan yerin tahliyesi ve sözleşme ihtilafı için bildirim (okul yönetiminden) | [22/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22), [28/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-28); [EK-2 md. 24](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-24); [2886 md. 75](../mevzuat/2886-devlet-ihale-kanunu.md#madde-75) | yeni (RYUE biçimi) | docx+pdf | F5 |
| E73 | Taşımacıyı tespit komisyonu üyelerinin görevlendirme yazısı | [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3); [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3), [OSAY 6/1-b](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-6) | yeni (RYUE biçimi) | docx+pdf | F6 |
| E74 | Servis işlem dosyası kapağı ve içerik listesi | [U-E 5/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | yeni | docx+pdf | F6 |
| E75 | Servis tip şartnamesi (U-E EK-1) | [U-E 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5); [U-E EK-1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1) | U-E EK-1 (korpus metni) | docx+pdf | F6 |
| E76 | Komisyon kararının mülki idare amirinin onayına sunulması yazısı | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [U-E 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [OSAY 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) | yeni (RYUE biçimi) | docx+pdf | F6 |
| E77 | Kesinleşen komisyon kararının taşımacıya tebliği yazısı | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | yeni (RYUE biçimi) | docx+pdf | F6 |
| E78 | Taşımacıya yükümlülük ihtarı (15 gün) | [U-E 11/1-ç](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-11); [U-E EK-2 md. 7/f](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-7) | yeni | docx+pdf | F6 |
| E79 | Servis sözleşmesinin fesih bildirimi | [U-E 11/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-11); [U-E EK-2 md. 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-7) | yeni | docx+pdf | F6 |

**Faz dağılımı:** F1b 1 · F1c 3 · F2 12 · F3 13 · F4 18 · F5 10 · F6 18 · F8+ 4 = **79** (F2'ye E04 aydınlatma
metni dâhil; E63-E79 F0-9 işlenişinde eklendi: §7'de adı geçip katalogda olmayan belgeler, E08'den ayrılan yeter sayı
tespit tutanağı ve hesap teslim pusulası). Aynı işin parçası olan tutanaklar kendi kodunu almaz, belgeye bölüm
olarak bağlanır (kasa sayımı E37'de, kasa çıkışı E27'de, değerlendirme E54'te, biten koçanlar E22'de; KE-26); program
belgeleri (kurtarma anahtarı belgesi, zarf imha tutanağı) katalog dışıdır (§9.7). Servis evrakı (E48-E58, E73-E79) söz dağarcığı testinin kapsamındadır.
**Kaynak kapsaması:** GNL setinin 23 formu ve RH-001 en az bir koda karşılık gelir. OYS'nin 19 belge şablonunun
hepsi UYARLA ile bir koda girer (`yeter_sayi_yok.html` → E64); iki parçadan `_commission_signatures.html` ilke olarak
alınır (yalnız ad + görev), `_compliance_warnings.html` alınmaz (§9.1-6); `build_imza_surkusu_xlsx` E08'e girer.

### 9.6 Katalog — veri, roller, imza, kabul

"Üreten": belgeyi programda oluşturup düzenleyebilen rol. Bağlayıcı kaynak §4.4.2 rol-izin matrisidir (R2); bu sütun
matrisi **daraltır, genişletemez**, çelişirse matris kazanır. Kaydedilmiş belgeyi her okur rol basabilir; kişisel veri
içeren çıktılar hariç (adlı E07 teslim çizelgesi, adlı E08): bunları yalnız `yonetici` basar, dosyası saklanmaz,
basım erişim günlüğüne düşer (§4.4.2 dipnot ¹⁰; R9).

- **Müdür.** `mudur` K2'deki **dört** müdür yazısını üretir: harcama talebi (E25), md. 27/3 uyarısı (E35), yeni okulda
  genel kurul daveti ve olağanüstü genel kurul çağrısı (E05; md. 9/1, 9/6, 13/8, 25/2; M-5). Bu yazıların taslağını
  `yonetici` hazırlamaz (M-11); müdür programı kullanmıyorsa yazı kâğıtta gelir ve gelen evrak olarak kaydedilir.
- **Okul idaresinin öteki resmî yazıları** (E12, E40 üst yazısı, E44, E70, E72, E73, E76, E77) ve servis komisyonu
  evrakı: taslağı `yonetici` (OAB'den sorumlu müdür yardımcısı) hazırlar, kâğıdı müdür imzalar (KE-19). E70 (md. 27/3
  ikinci cümle) bu gruptadır, müdür yazısı değildir. Müdür kantin ve servis akışlarında iş yapan rol değildir; müdür
  rolüne yeni yazma yetkisi eklenmez.
- **Denetleme Kurulu.** `denetleme_kurulu` kendi görev bölümünü (başkan seçimi, md. 14/1) ve denetim planını (E02),
  E32, E33'ü ve md. 14/5 hâlinde E05'i DK hesabıyla denetim modülünden (M8) üretir (M-6). DK hesapları DK üyeliği
  `SECILDI` olunca açılır; görev bölümü hesabın ön koşulu değildir.
- **Mali kayıtlar** yalnız `muhasip`tir (D2): mali dökümler muhasibin girişinden dolar; `yonetici` TEFBİS listesini
  (E18) muhasibin girişinden sonra alır ve "TEFBİS'e girildi" işaretini koyar.

Matriste `yonetici`nin Y olduğu modülün bir belgesinde Üreten'de `yonetici` yoksa nedeni şu dördünden biridir:
(a) **mali kayıt dökümü** (E17, E19-E22, E24, E27, E67): mali kayıt yalnız `muhasip`in (D2); (b) **YK'nin karar ve
yazışma belgeleri** (E15, E16, E41, E47, E65'te YK yedeği, E66, E68, E71): karar taslağını ve birliğin yazışmasını
sekreter yürütür ([md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); §7.2, §7.6 Kim);
(c) **birlik başkanının müdüre aylık bildirimi** (E31, [md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)):
alıcı okul idaresidir, `yonetici` hazırlamaz; (d) **organa ya da makama ait belge**: DK belgeleri
`denetleme_kurulu`nun (M8), müdür yazıları `mudur`un (M-11). Öteki belgelerde `yonetici` Üreten'de yazılıdır. YK
rolleri arasında Üreten Yönetmeliğin görev dağılımını izler (md. 13/4: gelir-gider işlemleri muhasibin, yazışma
sekreterin); `baskan` ve `baskan_yardimcisi` Y oldukları modüllerin (M2-M4, M7, M13, M14) belgelerini okur, basar ve
imzalar, oluşturmaz — istisna md. 13/8 çağrısında E05 ve aylık bildirim E31'dir. "Konum" §9.2.

| Kod | Veri kaynağı | Üreten | İmza bloğu | Konum | Kabul örneği (uydurma veriyle) |
|---|---|---|---|---|---|
| E01 | `OabTerm`, `OrganMembership` (görev, asıl/yedek, oy sırası, dönem sayacı, beyan tarihleri), `OabPerson`, `BankAccount` (kurumsal IBAN açık, maskelenmez), görev bölümü toplantısı ve karar no (`BoardMeeting`/`BoardDecision`) | sekreter, yonetici | YK asıl 5 üye, görev unvanlarıyla | KDT | 5+5 kadro: dört görev dolu ve tekil; "kaçıncı dönem" sayaçtan; sütun başlığı "Beyan (okul uygulaması)", Yönetmelik maddesine bağlanmaz (KM-8); imza yetkisi başkan + muhasip (yokluğunda başkan yardımcısı); bankaya bildirim tarihi ve belgesi (E66) alanı; temsilci satırları E03 ile aynı kişiler; FR-006 A-D bölümleri var |
| E02 | `OrganMembership` (DK; seçim kanalı), `OabPerson`, `OabTerm` (denetim planı tarihleri) | denetleme_kurulu (görev bölümü ve denetim planı DK hesabıyla, M8) | DK asıl 3 üye; "Bilgi: Birlik Başkanı" | — | Veli koltuğu GK seçimi, iki öğretmen öğretmenler kurulu seçimi ayrı satırda; hayırsever yok; başkanlık sayacı ≤ 3; planda ≥ 2 ara denetim; müdür bloğu yok (MB-15) |
| E03 | `OrganMembership` (temsilci türleri, YK karar no/tarih), `OabPerson`, okul kartı (`levels`, `in_campus`) | sekreter, yonetici | Sekreter + Birlik Başkanı; "Teslim alan: Okul Müdürü" | KDT | Kademe satırları `okul.kademe` kesişimiyle (karma okulda iki kademenin satırları birlikte); `in_campus` doğruysa kampüs yönetimi satırı (`KAMPUS_YONETIMI`, md. 13/7; kayıt satırıdır, kuralı yoktur); ortaöğretimde ödül-disiplin ve kontenjan, ortaokulda davranış kurulu satırı; RPD satırında "öğretmenler kurulu belirler" notu (RPD 16/5); servis, muhammen bedel ve ihale komisyonu satırlarında başkanın adı kendiliğinden; pay dağıtım komisyonu satırı yalnız başkan seçildiyse |
| E04 | `SchoolConfig.data_controller_text` (veri sorumlusu ve iletişim, KE-20; §5.1), işleme envanteri (§3.4: veri kategorileri, amaç, aktarım, yöntem ve hukuki sebep) | yonetici | imzasız bilgi metni | — | Dört alt metin: veli ve üye · personel · istekli, kiracı ve çalışan · bağışçı ve tedarikçi; her birinde KVKK 10/1 (a)-(d) unsurları ayrı başlıkta, (ç) "yöntem ve hukuki sebep" başlığı envanterden dolar; `data_controller_text` boşken basılmaz (uyarı, "tamamlanacaklar"da); "T.C. kimlik no tutulmaz" (K9 kapalıyken); veli listesinin dönem kapanışında silindiği yazılı |
| E05 | `GeneralAssembly` (tür, çağıran, çağrı nedeni, 1./2. toplantı, yer, yeter sayı anlık değeri), `AgendaItem`, davet kararı (`BoardDecision`), `Announcement` (duyuru kanıtı) | çağırana göre (MB-3): olağanda ve YK çağrısında sekreter, yonetici; başkan çağrısında (13/8) baskan; yeni okulda ve müdürün olağanüstü çağrısında (9/1, 9/6, 13/8, 25/2) mudur; DK çağrısında (14/5) denetleme_kurulu | Çağırana göre: Birlik Başkanı (YK adına) + Sekreter, "Görüldü — Okul Müdürü (md. 27/1)" · Birlik Başkanı (13/8) · Okul Müdürü (9/1, 9/6, 13/8, 25/2; "Görüldü" bloğu yok) · DK asıl üyeleri (14/5) · %10 başvurusunda KE-11 | — | Yeter sayı 64/32 paketten; 2. toplantı ≤ 30 gün, tarihi olağanüstüde de basılır (A-1); olağan gündemde 11/1-e ve f maddeleri var (OYS tohumunda yoktu); olağanüstüde çağıran ve neden basılı, gündem nedene bağlı; duyuru kanıtı bölümü: elden bildirim (E07'ye atıf), pano asma ve internet yayım tarihleri, görev unvanıyla (ad yok); 14 gün kala basımda uyarı |
| E06 | `GeneralAssembly`, `AgendaItem`, `Announcement` (kanıt) | sekreter, yonetici | "Okul-Aile Birliği Yönetim Kurulu" | — | Çıktıda hiçbir `OabPerson` adı yok (test); html tek dosya, dış bağlantısız; ikinci toplantı ilanı aynı kodla |
| E07 | `GeneralAssembly`, `ParentRoster` (sınıf/şube sayıları; teslim çizelgesinde veli adı) | yonetici (R9) | Davet: "Yönetim Kurulu adına Birlik Başkanı"; çizelge: sınıf rehber öğretmeni (teslim eden) | — | Davet mektubu kişisiz ("Sayın Veli"), sınıf başına adet, kısa aydınlatma paragrafı ve tam metnin (E04) yeri; çizelge kişisel veri dipnotlu; dosya ve içerik JSON'u saklanmaz, yalnız sha256 + satır sayısı + tarih; arşiv paketine girmez (R9) |
| E08 | `GeneralAssembly`, `ParentRoster` (veli adı + öğrencinin sınıfı), öğretmen ve yönetici listesi (`Personnel`); gözlemci bölümü boş satırlı (ad alınmaz, T5; sayı `GeneralAssembly.observer_count`) | yonetici (R9) | Sayfa parafı: toplantı yapıldıysa Divan Başkanı + Kâtip, yapılamadıysa Birlik Başkanı + Sekreter | — | Boş satırlı seçenek; xlsx ile PDF aynı sırada; T.C. kimlik no ve telefon sütunu yok; dosya ve içerik JSON'u saklanmaz (R9); yeter sayı tespiti E64'tedir |
| E09 | `OrganMembership` (`ADAY`), `OabPerson` (tür, veli işareti), kişi geçmişi (dönem sayacı) | sekreter, yonetici | Divan Başkanı + Kâtip | — | DK öğretmen koltukları oylamaya girmez (bilgi satırı); YK adayı veli/kursiyer/hayırsever; aday listesi ile E10 seçim sonucu aynı kişiler |
| E10 | `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes` (divan, ibra, oylamalar), `OrganMembership` (`SECILDI`), `OabBudget` | sekreter, yonetici | Divan Başkanı + Kâtip; "Görüldü — Okul Müdürü (md. 27/1)" | — | YK ve DK ibrası ayrı oylama satırı; "ibra edilmedi" E11-E12'yi açar; bütçe "görüşüldü" yazar; gündem değişikliğinin oylaması satır olarak |
| E11 | `AssemblyMinutes` (ibra), `DocumentRecord` (teslim edilen evrak) | sekreter, yonetici | Divan Başkanı + Kâtip; teslim alan yeni YK ve DK adına birer üye | — | Evrak tek tek listeli; tarih GK günü |
| E12 | `AssemblyMinutes`, `GeneralAssembly`, okul kartı (antet) | yonetici (taslak; KE-19) | Okul Müdürü + Birlik Başkanı (yeni YK adına) | — | RYUE: sayı, `gg.aa.yyyy`, konu, muhatap "… Millî Eğitim Müdürlüğüne"; ek E11 |
| E13 | `GeneralAssembly`, `OrganMembership`, `OabBudget`, `AssemblyMinutes` | sekreter, yonetici | Birlik Başkanı (yeni) + Sekreter; "Teslim alan: Okul Müdürü" | TFB | Seçilenler E10 ile aynı; sonraki adımlar tarihli (görev bölümü ≤ 7 gün, banka imza yetkisi E66, TEFBİS girişi); bildirim okul uygulamasıdır, belgede "Yönetmelik gereği" denmez (MB-11) |
| E14 | kural paketi (süreler), ders yılı takvimi, `OabTerm` (YK toplantı günü, DK denetim planı — dönem ayarı, §5) | yonetici | — | — | Her satır kural kimliği ve atıf taşır; "okul planı / öneri" satırları ayrı biçimde; Ekim sonu, 15, 30, 7 gün ve arz 10/20 tarihleri doğru |
| E15 | `BoardMeeting`, `BoardMeetingAttendance`, `BoardDecision` (sıra no, oylar, bağlı işlemler) | sekreter | Katılan YK üyeleri | KDT | < 4 katılımda karar bölümü yerine "toplantı yapılamadı"; kabul < 3 karar "alınmadı"; harcama kararında konu, üst sınır, bütçe kalemi, komisyon üyeleri dolu; GK çağrı, yedek çağırma ve koçan kayıt kararları bu kodla |
| E16 | `BoardMeeting`, `BoardMeetingAttendance`, `OrganMembership` | sekreter | Birlik Başkanı + Sekreter | — | Üst üste 3 özürsüz (toplantılar üzerinden) işaretli; yedek çağrısı (E65) ve görev bölümü satırı; aylık bildirim tarihleri E31'den |
| E17 | `LedgerEntry`, `LedgerAccount`, `BankTransaction`, `TransactionMatch`, `ReceiptLeaf`, `BoardDecision`, `OfficialBook` (`lines_per_page`), `MarkBatch` (`DEFTERE_GECIRME`) | muhasip | Muhasip + Birlik Başkanı | DFT | Sütunlar: tarih · sıra no · belge/evrak no · açıklama · gelir · gider · kalan · karar no · gelir-gider türü; kalan = banka + kasa; ters kayıt ayrı satır; tasdikli defterin sayfa düzeninde (sayfa başına `lines_per_page` satır); "bu baskı a-b sayfalarına geçirildi" toplu işareti (`MarkBatch`); kâğıt çapası satırı "Kayıt no: N · Zincir: XXXX-XXXX" (§4.6.3) |
| E18 | `LedgerEntry`, `TefbisTypeMapping`, `ReceiptLeaf`, `MarkBatch` (`TEFBIS_GIRISI`) | yonetici (muhasibin girişinden sonra alır, D2) | — (iş listesi); "TEFBİS'e girildi" işaretini yonetici koyar | TFB | Muhasibin girişinden sonra alınır (D2); her satırda TEFBİS işlem tipi dolu (eşleme yoksa basılmaz, uyarı); T.C. kimlik no sütunu yok; "kimlik no kaynağı" sütunu: makbuz seri-cilt-sıra · dekont referansı · "kâğıt kaynak yok — bağışçıdan alınmalı" (KM-14, SU-14) |
| E19 | `BankAccount`, `BankTransaction`, `LedgerEntry`, `TransactionMatch` | muhasip | Muhasip | — | Eşleşmeyen hareketler ve 5 iş gününü aşan kasa ayrı bölümde |
| E20 | `LedgerEntry` (bağış; `donor_name`; K9 açıkken `donor_tckn`'den yalnız "kayıtlı mı"), `LedgerAccount` (şartlı alt hesap), `ReceiptLeaf` | muhasip | Muhasip + Birlik Başkanı | TFB | Şartlı bağış kalanı alt hesap bakiyesiyle aynı; kayıt dönemi uyarısı ekranda, çıktıda değil; T.C. kimlik no sütunu yok, K9 açıkken yalnız "kimlik no kayıtlı: evet/hayır" (KM-14); bağışçı kişi kaydı açmaz (UY-20) |
| E21 | `LedgerEntry` (ayni; `donor_name`), VİF no/tarih alanı | muhasip | Teslim eden: Birlik Başkanı ya da Muhasip; Teslim alan: Okul Müdürü; taşınır kayıt yetkilisi (VİF) | — | Cins, miktar, takdir değeri; VİF no boşsa basımda uyarı; VİF'in bir nüshasının bağışçıya verileceği notu; bağışçıya kısa aydınlatma paragrafı (KM-6) |
| E22 | `OfficialBook` (defterler, tasdik), `ReceiptBookRegistry`, `ReceiptLeaf`, `BoardDecision` (koçan kaydı) | muhasip (koçan ve yaprak), sekreter (defter tasdik satırları) | Muhasip + Sekreter + Birlik Başkanı; "Mühürleyen — Okul Müdürlüğü" | KDT | Her cilt 50 yaprak; kullanılan + iptal + kayıp + boş = 50; aynı seri-cilt-sıra iki kez yok; karar defteri noter, diğerleri MEM tasdik satırında; koçan tasdik sütunu isteğe bağlı, boşken yalnız bilgi (varsayılan; MB-13); `IPTAL` ve `KAYIP` yapraklar dökümde görünür, tutanağı E67'dir; biten koçanların teslim-devir bölümü (FR-015 B; 23/6) ve dönem sonu koçan envanteri bu belgededir (KE-26) |
| E23 | `DocumentRecord` (gelen/giden, sayı, tarih, konu), `GeneratedDocument` | sekreter, yonetici | Sekreter | DFT | Sıra no kesintisiz; programın ürettiği yazılar giden olarak önerilir |
| E24 | `OabContract`, `ContractInstallment` (aylık kira takvimi), `ShareStatement`, `BankTransaction`, okul kartı (yerleşim türü) | muhasip | Muhasip + Birlik Başkanı + Okul Müdürü (md. 17/1-b-5) | — | 9 aylık sözleşme: Ocak yarım, Haziran-Ağustos boş; il merkezi okulunda ilçe sütunu 0, il %20; arz son ödeme 10'u ve 20'si ayrı sütunda, iki ayrı uyarı; fiilî ödeme ile hesaplanan arasındaki fark ayrı sütunda (D1); birlikçe işletme hâlinde (17/1-b) kira bölümü yerine hâsılat, %1 arz ve net pay tabanı bölümü (F5'te) |
| E25 | `ExpenseFile` (talep: tarih, gerekçe, kalemler — §5) | mudur (taslağı `yonetici` hazırlamaz, M-11) | Talep eden + Okul Müdürü; "Birlik işlemi": Sekreter + Birlik Başkanı | — | Kalem toplamı tutar; YK karar no ayrı bölümde; müdür hesabının yazısı (denetim izi). Müdür programı kullanmıyorsa talep kâğıtta gelir, `yonetici` gelen evrak olarak kaydeder (`DocumentRecord` + `ExpenseFile.request_record`); E25 basılmaz, zincir bu kayıttan yürür (SU-10) |
| E26 | `ExpenseFile` (teklifler, teslim — §5), `ExpenseFile.commission_members` → `OrganMembership(ALIM_KOMISYONU)`, `BoardDecision` | muhasip, sekreter, yonetici | Komisyon üyeleri (≥ 3) + Birlik Başkanı; teslim bölümünde taşınır kayıt yetkilisi | — | < 3 üyede gerekçe satırı; YK dışı üyede "uzmanlık gerektiren iş" satırı; "en az üç teklif" okul uygulaması diye yazılır, Yönetmelik hükmü diye değil; komisyon kişileri tek kaynaktan (UY-20) |
| E27 | `ExpenseFile`, `ExpenseInvoice` (fatura başına; `payment_order`), `LedgerEntry`, `BankAccount`, `BankTransaction` | muhasip | Birlik Başkanı (yokluğunda Başkan Yardımcısı) + Muhasip | TFB | Form fatura (`ExpenseInvoice`) başınadır; sürekli ödeme dosyasında her dönemin faturası için ayrı form (R6). "Harcama dosyası kontrol listesi" formun kontrol bölümüdür: talep (E25 ya da gelen evrak kaydı), E26 ve VİF alanlarından dolar. Banka yolunda ödeme talimatı: birliğin IBAN'ı tam (kurumsal), alıcı IBAN'ı modelde tutulmaz, kâğıtta elle yazılacak boş alan (EK-13); kasa yolunda talimat yerine kasa çıkış bölümü (ayrı kod almaz; md. 16/1 sapmasının gerekçesi bu bölüme basılır); iki imza |
| E28 | `OabBudget`, `BudgetLine`, `BudgetCategory`, `OpeningBalance` | muhasip, yonetici | YK adına Birlik Başkanı + Muhasip (+ asıl üyeler) | TFB | "Okul Müdürü" imzası yok; durum "genel kurulda görüşüldü"; satır toplamları tutar |
| E29 | `OabBudget`, `BudgetLine`, `Announcement` | muhasip, sekreter, yonetici (pano ve web yayım kaydı) | "Okul-Aile Birliği Yönetim Kurulu" | — | Kişisiz; yalnız kalem toplamları |
| E30 | `LedgerEntry` (dönem toplamları), `Announcement` | muhasip (hazırlar); yonetici (pano ve web yayım kaydı, §7.3) | "Okul-Aile Birliği Yönetim Kurulu" | — | Bağışçı, öğrenci, personel adı yok; dönem sonu bakiye E17'nin kalanıyla aynı |
| E31 | `MonthlyReport`, `LedgerEntry`, `BoardDecision`, `ReceiptLeaf`, `BankTransaction` | muhasip (hazırlar), baskan | Hazırlayan Muhasip; Birlik Başkanı; "Teslim alan: Okul Müdürü" (gelen evrak no) | TFB | Kesim satırı ("… tarihine kadar içe aktarılan hareketler"); ay toplamları kesim tarihine kadar E17 ile aynı; "önceki aylara ait geç kayıtlar" ayrı bölümde (SU-8); şartlı bağış ve arz/pay vadeleri D bölümünde; kâğıt çapası satırı "Kayıt no: N · Zincir: XXXX-XXXX" (§4.6.3) |
| E32 | `AuditReport` (ARA, kontrol listesi), `ComplianceItem`, `LedgerEntry`, `BankTransaction` | denetleme_kurulu | DK asıl 3 üye; "Teslim alan: Birlik Başkanı" (14/4: YK'ye sunulur) | — | FR-012'nin 22 kalemi; "adli sicil kayıtları alınmış mı" kalemi yok (S-20); defter = banka = TEFBİS sütunları; uygunsuz kalem yalnız rapor bayrağını (`irregularity_found`) kaldırır; "md. 6'ya aykırı faaliyet tespit edildi" ayrı kutudur ve md. 14/5 seçeneği (E05'i DK açar) yalnız bu kutu (`md6_violation_found`) işaretliyken basılır (MB-10); müdür bloğu yok (MB-15) |
| E33 | `AuditReport` (NIHAI), ara raporlar | denetleme_kurulu | DK asıl 3 üye | — | Ara rapor sayısı < 2 ise uyarı; mali özet E34 ile aynı rakamlar |
| E34 | `OabBudget`, `BudgetLine`, `LedgerEntry`, `BoardMeeting`, `MonthlyReport` | muhasip, sekreter, yonetici | YK asıl 5 üye | TFB | Gerçekleşen işlem kayıtlarından (K1); "Okul Müdürü" imzası yok; öğrenci/veli adı yok |
| E35 | `DocumentRecord`, `GeneratedDocument` | mudur (taslağı `yonetici` hazırlamaz, M-11) | Okul Müdürü | — | RYUE; muhatap Birlik Başkanı; birlik kayıtlarına yazmaz; 27/3 sırasının ilk adımı: uyarıya rağmen durum sürerse il/ilçe MEM'e bildirim E70'tir (okul idaresinin resmî yazısı; taslağı `yonetici`, KE-19) |
| E36 | `SocialEvent` (tür, düzenleyen, tarih-saat, sorumlu YK üyesi, YK kararı, SEK incelemesi, müdür görüşü ve MEM onayı tarih/sayıları, "proje/protokol kapsamında değil" beyanı; §5, EK-9), `LedgerEntry.event` (gelir ve gider kalemleri), `BoardDecision` | muhasip, sekreter, yonetici | Etkinlik sorumlusu YK üyesi + Muhasip + Birlik Başkanı; "Uygunluk görüşü — Okul Müdürü" | KDT | Onay zincirinin üç aşaması tarih/sayılı; gelir ve gider kalemleri etkinliğe bağlı kayıtlardan; net gelir defterle aynı |
| E37 | `Handover` (kasa sayımı, banka bakiyesi), `HandoverItem`, `ReceiptBookRegistry`, `BankAccount`, `DocumentRecord`, `OpeningBalance` | yonetici, sekreter | Devreden: önceki Birlik Başkanı + önceki Muhasip; Devralan: yeni Birlik Başkanı + yeni Muhasip; "Görüldü — Okul Müdürü (md. 10/1-ç, 27/1)" | — | Koçanlar seri-cilt-sıra aralığıyla (E22); banka bakiyesi tarihli; kasa sayımı bu belgenin bölümüdür (KE-26; sayım ≠ `KASA` bakiyesi ise uyarı ve düzeltme kaydı); banka imza yetkisi satırı (E66); hesap geçişi satırı (eski organ hesapları kapandı, yenileri açıldı; §4.4.5); yanında kurtarma anahtarı satırı: "Kurtarma anahtarı zarfı müdürlükte, mührü sağlam; anahtar no ve tarihi" — anahtarın kendisi basılmaz (D3); kâğıt çapası satırı "Kayıt no: N · Zincir: XXXX-XXXX" (§4.6.3) |
| E38 | `ComplianceItem`, `GeneratedDocument`, `DocumentRecord` | sekreter, yonetici | Sekreter + Birlik Başkanı; "Kontrol eden — Okul Müdürü" | — | 17 kalemin her biri bir belgeye bağlı; eksik kalem "yok" yazar |
| E39 | `GeneratedDocument` (`content_json`, özetler), `OabTerm` | yonetici | — | — | Her belgenin PDF'i + xlsx dökümler + JSON; içerik listesi DAHY EK-2 sütunlarıyla; kapanmış dönemde içerik özeti aynı; E07, E08 ve E63 pakete girmez (R9), yerlerinde yalnız iz satırı (tarih, sha256) |
| E40 | `RentableAsset`, `BoardDecision`, okul kartı | sekreter, yonetici | Birlik Başkanı; üst yazı Okul Müdürü (taslak yonetici, KE-19) | — | RYUE bildirim yazısı; muhatap okul müdürlüğü; MEM'e iletim üst yazısı ekte; kiralama kararı E15'tedir, bu yazı konum cümlesi taşımaz (EK-17) |
| E41 | `OabContract` (mevcut), `BoardDecision`, talep (`DocumentRecord`) | sekreter | Birlik Başkanı | — | Talepten ≤ 15 gün; ret somut bilgi ve belgeye dayanır (G.2024/35 I-4); karar E15'tedir, cevap yazısı konum cümlesi taşımaz (EK-17) |
| E42 | `OabContract`, `Bidder` (kiracı), `RentableAsset`, okul kartı | yonetici, sekreter | Birlik Başkanı + Kiracı + varsa İlgili Esnaf Odası Temsilcisi | — | 25 genel şart korpustaki EK-2 ile karakter karakter aynı (lafız kilidi); boşluklar dolu; YD'li ibare KE-7'ye göre; "Taşımacı" kelimesi yok. Büyükşehir statüsünde olmayan il merkezinde (varsayılan; MB-9): genel şart md. 7'nin lafzı değişmez, ilçe payının tutar boşluğuna "—" yazılır, Özel Şartlar md. 2'ye md. 17/1-a-2'nin pay notu (il %20, ilçe yok) girer |
| E43 | `OabContract` (yer teslimi), `RentableAsset` (levazım) | yonetici | Birlik/okul yönetimi yetkilisi + Kiracı | — | İmzadan ≤ 15 gün; imzadan önceki teslim tarihi uyarı + gerekçe (`kira.imzadan_once_teslim_yok`); levazım çeşit ve değer sütunları; tahliye nüshası E71/E72 sonrası |
| E44 | `OabContract`, okul kartı | yonetici (taslak; KE-19) | Okul Müdürü | — | RYUE; muhatap millî emlak birimi; ek sözleşme örneği |
| E45 | `OabContract`, `IndexRate` | sekreter (yazı), yonetici (artış kaydı; §7.6) | Birlik Başkanı | — | Oran "TÜFE on iki aylık ortalamalara göre % değişim"; ilk yıl artış yok; uygulanan artış hesaplanandan farklıysa ekranda uyarı, çıktıda uygulanan artış |
| E46 | `BidderDocument` (`document_type`, `subject` — `KIRACI` ve `CALISAN` dâhil —, `seen_on`, `valid_until`), `DocumentRecord`; `ComplianceItem` değil | yonetici | Birlik Başkanı | — | Adli sicil ve sağlık belgesinde yalnız "teslim alındı" + tarih; 12 aylık yenileme sütunu (UY-20); belge teslim alınırken kiracıya ve çalışana kısa aydınlatma paragrafı (KM-6) |
| E47 | `OabContract`, `ComplianceItem` | sekreter | Birlik Başkanı | — | Süre 15 gün; tebliğ tarihi alanı; süre dolunca fesih bildirimi E71 önerilir |
| E48 | `Tender` (servis tespiti kaydı), komisyon üyeleri | yonetici | Komisyon Başkanı (Okul Müdürü) | — | "ihale/teklif/eksiltme" yok (§9.4); md. 5/4'ün dört unsuru; ilan ile dosya teslimi arası ≥ 7 gün; istekliye kısa aydınlatma paragrafı (KM-6) |
| E49 | `Tender`, komisyon | yonetici | Komisyon başkan ve üyeleri | — | Asma ve indirme tarihi; pano + web satırları |
| E50 | `Tender`, `Bidder` | yonetici | Komisyon üyesi + İstekli | — | Bedelsiz teslim (md. 5/1); teslim edilen şartname E75'in tasdikli örneği; istekliye kısa aydınlatma paragrafı (KM-6) |
| E51 | `Tender`, `Bidder` | yonetici | Komisyon üyeleri + İstekli | — | Teslim saati ilandaki saatten önce; "dosyalar geri alınamaz" (md. 7/2) |
| E52 | `Bidder`, `BidderDocument` | yonetici | Komisyon başkan ve üyeleri | — | md. 6/1'in belgeleri satır satır; eksik belge uyarı, engel değil |
| E53 | `Bidder`, EK-3 puan kayıtları | yonetici | Komisyon başkan ve üyeleri | — | Yalnız itiraz ya da yeni okulda basılır; kademeler EK-3 ile aynı; kademe dışı puan gerekçesiyle basılır (D1); kriter 4 kısa adla (KE-8) |
| E54 | `Tender` (değerlendirme, oylama, karar), `TenderCommissionMember` (oy, şerh), `Bidder`, mülki amir onay kaydı | yonetici | Komisyon başkan ve üyeleri; muhalif şerhi; "Mülki idare amiri onayı" alanı | — | Değerlendirme tutanağı bu belgenin bölümüdür (KE-26); değerlendirme bölümü 8/2 ölçütlerini (araç yaşı, özmal, ikamet/şube, aynı okulda önceki iş ve başlangıç tarihi) istekli başına yazar; EK-3 hâlinde E53'e atıf; oylama sonucu ve muhalif gerekçesi basılır; çekimser ya da şerhsiz muhalif varsa ekranda uyarı, tutanak olduğu gibi; karar no "OAB-İhale-…" değil |
| E55 | `OabContract` (servis), `Bidder` (taşımacı), komisyon | yonetici | Komisyon Başkanı (Okul Müdürü) + Taşımacı | — | U-E EK-2 lafzı korpusla aynı (SIC bent harfleri dâhil); "ihaleye fesat karıştırma" dışında yasak kelime yok (KE-9); eki E75 |
| E56 | `OabContract` (servis; güzergâh), `Bidder` (ad/unvan), araç plakası (`BidderDocument`, `subject=ARAC`), `Announcement` | yonetici | "Taşımacıyı Tespit Komisyonu" (kişi adı yok; U-E 10/3 ilanı komisyona verir) | — | Yalnız taşımacının ad/unvanı, araç plakası ve güzergâh (D5); telefon, adres, T.C. kimlik no, şoför ve veli verisi yok; html tek dosya; ilan süresi bitince sitedeki kopyanın kaldırılması hatırlatması |
| E57 | `Tender`, `Bidder` | yonetici | Komisyon başkan ve üyeleri | — | Üç nedenden hangisi olduğu işaretli; atıf md. 8/7 |
| E58 | `BidderDocument` (`document_type`, `subject` — `SOFOR`, `REHBER`, `ARAC` dâhil —, `seen_on`, `valid_until`), `InspectionRecord`, `OabContract`; `ComplianceItem` değil | yonetici | — (iç izleme) | — | Araç yaşı (imal yılından sonraki ilk takvim yılından), şoför ve rehber yaşı, belge süreleri (B sınıfı sayımıyla) kural paketinden; içerik yok, tarih var (UY-20); belge teslim alınırken şoföre ve rehbere kısa aydınlatma paragrafı (KM-6) |
| E59 | `GeneralAssembly`, `LedgerEntry`, `OpeningBalance`, `ReceiptBookRegistry`, `BankAccount`, okul kartı | yonetici | — | — | Tablo 3 üç yıl: devreden + gelir = toplam; Tablo 4 göstergeleri kayıtlardan evet/hayır |
| E60 | `LedgerEntry`, `TefbisTypeMapping`, `BankTransaction`, TEFBİS Excel içe aktarımı (§8) | yonetici, muhasip | Muhasip + yönetici (iç) | TFB | Fark satırları türüne göre: TEFBİS'te yok · defterde yok · tutar farkı |
| E61 | personel modeli (sürüm 2), `LedgerEntry` (ücret, prim) | muhasip, yonetici (özlük bölümü; ücret ve prim satırları muhasibin kaydından) | Muhasip + Birlik Başkanı | — | Yalnız "doğrudan işveren" okulda açılır; izin ve ihbar süreleri kural paketinden; müdür bloğu yok (MB-15) |
| E62 | personel modeli (sürüm 2) | muhasip, yonetici | İşveren adına Birlik Başkanı + işçi | — | Hak edilen, kullanılan, kalan; bölüm ≥ 10 gün; sözleşmeyle verilen fazla izin uyarısız |
| E63 | `Account` (giriş adı, rol, açılış tarihi; §4.6), rol-izin matrisi (§4.4.2), parola politikası (TK15), boşta kilit süresi (TK14) | yonetici | Teslim eden: yönetici; Teslim alan: hesap sahibi (ad, imza, tarih) | — | Tanıtıcı (giriş adı), rol ve "bu programda sizin işiniz" özeti matristen; ilk giriş adımları (geçici parolayla giriş → parolayı değiştirme); parola kuralları: en az 8 karakter, küçük-büyük harf, rakam ve simgeli karışık yapı, en geç altı ayda bir değişim (BSG 9/2-a, b, ç); kilitleme: boşta kalınca oturum kilitlenir, "Kilitle" düğmesi, yanlış denemede artan bekleme (BSG 10/2; kalıcı kilit yok); **parola alanı yok** (ne değer ne boş satır); "İlk parolanız ayrı kapalı zarftadır; parolanızı kimseyle paylaşmayın, görünür yere yazmayın" cümlesi (BSG 9/2-e, 10/1; kapalı zarf okul uygulaması); kişisel veri dipnotu; dosya saklanmaz |
| E64 | `GeneralAssembly` (dondurulmuş yeter sayı, mevcut anlık değeri, katılan sayısı ve türe göre dağılımı, gözlemci sayısı, toplantı: birinci/ikinci) | sekreter, yonetici | Sağlandıysa Divan Başkanı + Kâtip; sağlanamadıysa Birlik Başkanı + Sekreter + "Görüldü — Okul Müdürü" (KE-10) | — | Kişisizdir, yalnız sayılar (E08'den ayrıldı, KE-21; R9 kapsamı dışında); 99 öğrenci → 32, 100 → 64; ikinci toplantıda "çoğunluk aranmaz" satırı; gözlemciler sayıya girmez (9/5); kapanmış dönemde içerik özeti aynı |
| E65 | `OrganMembership` (yedek, oy sırası, `promoted_on`, `promoted_by_decision`), `BoardDecision` (`YEDEK_CAGIRMA`; yalnız YK yedeğinde) | YK yedeğinde sekreter (YK kararıyla, 13/6); DK yedeğinde yonetici (14/6; üyelik kaydıdır, YK kararı gerekmez — M2) | Birlik Başkanı + Sekreter | — | Çağrılan oy sırasındaki ilk yedek (sıra dışıysa gerekçe satırı); boşalan koltuk ve düşme nedeni (kişisel ayrıntı yok); YK yedeğinde görev bölümü için 7 günlük süre ve karar no yazılı, DK yedeğinde karar satırı yok, neden "dört aydan uzun görevlendirme" (14/6); kişisel veri dipnotu |
| E66 | `BankAccount` (banka, şube, IBAN), `OrganMembership` (başkan, başkan yardımcısı, muhasip), `BoardDecision` (`GOREV_BOLUMU`) | sekreter | Birlik Başkanı + Sekreter | — | Üst yazı; ek E01 karar örneği; müşterek yetkililer başkan + muhasip (başkan yokken başkan yardımcısı); değişiklikte eski yetkililerin yetkisinin kaldırılması satırı; bankanın kendi formu ve imza sirküleri program dışı (§9.7); gönderim tarihi E01'deki alana döner |
| E67 | `ReceiptLeaf` (`IPTAL` · `KAYIP`, `cancel_reason`), `ReceiptBookRegistry` | muhasip | Muhasip + Birlik Başkanı | — | Yaprak no ya da koçanın seri-cilt-sıra aralığı; neden; iptal yaprağın koçanda kaldığı ve karar defterine not düşüleceği (E15) satırı; kayıp yaprak E22'de `KAYIP` görünür; yaprak yeniden kullanılamaz |
| E68 | `BoardDecision` (karar no, tarih, konu, defter sıra no ve sayfa, durum), `OfficialBook` (karar defteri) | sekreter | Sekreter | KDT | Dönem kararları defter sıra no'suyla; deftere işlenmemiş karar ayrı bölümde; sıra atlaması işaretli; konu özeti kişisel veri taşımaz |
| E69 | Kapanış denetimi sonuçları (§7.8): eşlenmemiş banka hareketi, deftere işlenmemiş karar, açık harcama dosyası, TEFBİS işaretsiz kayıt, koçan durumu, açık `ComplianceItem` | yonetici | Hazırlayan: yönetici | — | Sert maddeler "geçti/kaldı", uyarılar gerekçeleriyle, eksikler ayrı; kapanış tarihi; yeniden basımda içerik özeti aynı |
| E70 | `DocumentRecord` (E35'in tarih ve sayısı, sonucu), `GeneratedDocument` | yonetici (taslak; KE-19) | Okul Müdürü | — | RYUE; muhatap "… İl/İlçe Millî Eğitim Müdürlüğüne"; önceki yazılı uyarının (E35) tarih ve sayısı zorunlu (27/3 sırası); denetim talebi açık yazılı; okul idaresinin resmî yazısıdır, K2'deki müdür yazılarından değildir (taslağı `yonetici`, kâğıdı müdür imzalar); birlik kayıtlarına yazmaz |
| E71 | `OabContract` (fesih tarihi ve nedeni), `BoardDecision` (fesih kararı), E47 kaydı, `kira.fesih_tazminati` hesabı | sekreter | Birlik Başkanı (YK kararıyla) | — | Fesih nedeni 22/1 bendi ya da EK-2 maddesiyle; ihtar gereken hâlde E47'nin tebliği ve 15 günün dolduğu; tazminat, kesin teminatın gelir kaydı ve mahsup satırları; tahliye ve teslim çağrısı (E43) |
| E72 | `OabContract`, `RentableAsset`, `DocumentRecord` | yonetici (taslak; KE-19) | Okul Müdürü | — | RYUE; muhatap seçeneği: mülkiyet durumuna göre İl Muhakemat Müdürlüğü ya da İl Özel İdaresi (EK-2 md. 24) · mülki idare amiri (22/2 → 2886 md. 75 tahliye talebi; 28/3 ihtilaf); sözleşme bitiş ya da fesih tarihi, tahliye cezası (EK-2 md. 22) satırları |
| E73 | `Tender` (`SERVIS_TESPIT`), `TenderCommissionMember` (asıl/yedek, belirlenme kanalı) | yonetici (taslak; KE-19) | Okul Müdürü | — | Bileşim `servis.komisyon_bilesimi` ile; öğretmenin öğretmenler kurulunda ad çekmeyle belirlendiği tarih; veliler çocuğu servisle taşınanlardan okul idaresince; birlik başkanı kendiliğinden üye (E03 ile aynı kişi); "ihale" kelimesi yok |
| E74 | `Tender`, `GeneratedDocument` (E48-E57, E73-E79), `DocumentRecord` | yonetici | Komisyon Başkanı (Okul Müdürü) | — | Şartname (E75), sözleşme tasarısı (E55) ve sürecin bütün belgeleri tarih sırasıyla; eksik belge "yok" yazar |
| E75 | `Tender` (öğretim yılı, okul adı ve boşluklar), okul kartı | yonetici | Komisyon başkan ve üyeleri (tasdik) | — | EK-1 lafzı korpusla karakter karakter aynı (§9.1-7); yalnız boşluklar dolar; "ihaleye fesat karıştırma" dışında yasak kelime yok (KE-9) |
| E76 | `Tender` (karar tarihi), `TenderApproval` (`BEKLIYOR`, `requested_on`), E54 | yonetici (taslak; KE-19) | Okul Müdürü (Komisyon Başkanı) | — | RYUE; muhatap "… Kaymakamlığına / Valiliğine"; ek E54; 5 iş günlük onay süresi bilgi satırı; sunuş tarihi `requested_on`'a döner |
| E77 | `Tender`, `TenderApproval` (onay tarihi), `Bidder` (tebligat adresi), `OabContract` (taslak) | yonetici (taslak; KE-19) | Okul Müdürü (Komisyon Başkanı) | — | Onaydan ≤ 5 iş günü; 10 günlük imza süresi ve imzalanmazsa yeniden çıkılacağı (8/7) yazılı; tebliğ Tebligat Kanunu hükümlerince, tebliğ tarihi alanı; adres yalnız bu yazıda (iç) |
| E78 | `OabContract` (servis), `Bidder`, `ComplianceItem` | yonetici (taslak; KE-19) | Komisyon Başkanı (Okul Müdürü) | — | Yerine getirilmeyen yükümlülük sözleşme maddesiyle; süre 15 gün; tebliğ tarihi alanı; süre dolunca E79 önerilir |
| E79 | `OabContract` (servis; fesih tarihi ve nedeni), `Tender`, E78 kaydı | yonetici (taslak; KE-19) | Komisyon Başkanı (Okul Müdürü) | — | Fesih nedeni 11/1 bendiyle; (ç) bendinde E78'in tebliği ve 15 günün dolduğu; yeniden tespit sürecinin açılacağı bilgi satırı |

### 9.7 Programın üretmediği belgeler

| Belge | Neden | Program ne yapar |
|---|---|---|
| Yönetim kurulu karar defteri | El ile yazılır, noter tasdiklidir ([13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | Karar taslağı (E01, E15), "deftere işlendi" işareti, defter sıra no ve sayfa; dizin (E68) |
| Gelir-gider ve gelen-giden evrak defteri | İl/ilçe MEM tasdiklidir ([23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | Geçirilecek kayıt dökümü (E17, E23) |
| EK-1 bağış alındı belgesi, gelir/gider makbuzu | Ciltli, seri-cilt-sıra numaralı, mühürlü koçan ([16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); K5) | Koçan envanteri ve yaprak kaydı (E22), iptal/kayıp tutanağı (E67) |
| TEFBİS kaydı | Okul idaresi girer ([23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); K6) | Liste (E18) ve mutabakat (E60) |
| Kantin muhammen bedel ve ihale komisyonu kararları, ihale ilanı | Valilik/kaymakamlık komisyonlarının ve il/ilçe MEM'in evrakı ([19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [G.2024/35 II-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-3)) | Karar tarih/sayısı ve sonucu kaydedilir; onay kaydı (`kantin.kiralama_onay_kaydi`); başkan temsilci (E03) |
| Mülki amir onayı (OLUR) | Mülki idare amirinin işlemi | Tarih/sayı kaydı; servis kararının onaya sunulması yazısı (E76); onaysız kesinleştirme serviste sert, kantinde uyarı + gerekçe (D4) |
| Servis kararının tebligatı | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8): Tebligat Kanunu hükümlerince yapılır | Tebliğ yazısı (E77) ve tebliğ tarihi alanı |
| Öğretmenler kurulu tutanağı (DK öğretmen üyeleri, servis komisyonu öğretmeni) | Okulun kurul evrakı | Seçim sonucu üyelik kaydına girer |
| Varlık İşlem Fişi | TKYS'de taşınır kayıt yetkilisi düzenler ([TMY 16/1](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16), [TMY 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41)) | Fiş no ve tarih alanı |
| Banka talimatının elektronik onayı; bankanın imza yetkisi formları ve imza sirküleri | Bankanın sistemi ve formu (biçimi DOĞRULANMADI) | Kâğıt talimat (E27); imza yetkisi üst yazısı (E66); üçüncü onay ayarı |
| Kurtarma anahtarı belgesi, zarf imha tutanağı, yedek raporu | Programın kendi güvenlik belgeleridir, birlik evrakı değildir | Aşağıdaki "program belgeleri"; devir-teslim tutanağına (E37) yalnız "zarf müdürlükte, mührü sağlam; anahtar no ve tarihi" satırı girer |

**Program belgeleri (katalog dışı).** E-kodu almazlar ve katalog sayımına (79) girmezler; kurtarma anahtarı
belgesinin PDF'i bilgisayarda bırakılmaz (§12.B). Kurtarma anahtarı belgesi ve yedek raporu aile iskeletinden gelir, metni OAB'ye
göre yeniden yazılır (§12.B); zarf imha tutanağı yenidir (D3):

| Belge | Dayanak | Faz · üreten · imza | İçerik |
|---|---|---|---|
| Kurtarma anahtarı belgesi (`recovery_key_document.py`) | D3; §4.4.4 adım 6 | F1b · yonetici · — | Anahtarın no'su ve üretim tarihi; saklama yeri okul müdürlüğünde mühürlü zarf, veliye geçmez; "parola paylaşılmaz, herkes kendi hesabıyla" ([BSG Yön. md. 7/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [9/2-e](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9)); dönemlik yenileme ve eski zarfın imha tutanağıyla yok edileceği |
| Kurtarma anahtarı zarfı imha tutanağı | D3; §4.4.4 DEK yenilemesinin 7. adımı | F4 · yonetici · Okul Müdürü + Müdür Yardımcısı (program yöneticisi) | Eski anahtarın no ve tarihi; yeni anahtarla alınan tam yedeğin açılıp doğrulandığı tarih; zarfın mührü sağlam bulunarak yok edildiği; anahtarın kendisi basılmaz; yenilemeden önceki yedeklerin artık açılmayacağı bilgi satırı (§4.4.6) |
| Yedek raporu | §4.4.7 | F1b · yonetici · — | İçeriği §4.4.7'deki yedek türlerine göre F1b'de yazılır |

---

---

## 10. Kural testleri

Kural testleri mevzuat hükmü ile programın davranışı arasındaki bağı sabitler. Yalnız Docker'da koşar (altın kural
7); faz, o fazın kapısındaki kural testleri yeşil olmadan kapanmaz. Veri uydurmadır; OYS testlerindeki gerçek firma
adı ve gerçek evrak örneği taşınmaz (S-21), sızıntı denetimi bu adları da arar.

### 10.1 Düzen

| Kısaltma | Dosya (`backend/apps/oab/tests/kurallar/`) | Kapsam |
|---|---|---|
| `kp` | `test_kural_paketi.py` | Şema, atıf kilidi, tutarlılık, sürüm ve dönem bağı, eksik/sapma (§6.1-6.3) |
| `gk` | `test_genel_kurul_kurallari.py` | §6.4.1 |
| `yk` | `test_yonetim_kurulu_kurallari.py` | §6.4.2; alım komisyonunun organ ekranı |
| `dk` | `test_denetleme_kurulu_kurallari.py` | §6.4.3 |
| `tm` | `test_temsilci_kurallari.py` | §6.4.4 |
| `ml` | `test_mali_kurallar.py` | §6.4.5-6.4.6 |
| `pd` | `test_kantin_pay_kurallari.py` | §6.4.7 |
| `kn` | `test_kantin_kurallari.py` | §6.4.8 |
| `sv` | `test_servis_kurallari.py` | §6.4.9 |
| `pr` | `test_personel_kurallari.py` | §6.4.10 |
| `ev` | `test_evrak_kurallari.py` | §9 konum, imza, söz dağarcığı, lafız kilidi, katalog kabulü |
| `ak` | `test_akis_kararlari.py` | Kural paketine bağlı olmayan akış, model ve KVKK kararları (F0-9 ekleri; §10.7) |

Aile güvenlik ve rol testleri bu dizinde değildir; iskeletin test dosyalarındadır (§4, §12.B) ve F0-9 ekleri §10.6'da
adıyla listelidir.

- **İşaret** (UY-15). İki işaret vardır, ikisi de `pyproject.toml` `markers` listesinde kayıtlıdır (ailenin
  `--strict-markers` ayarı): `@pytest.mark.kural_deger("<id>")` değer ve atıf testlerini,
  `@pytest.mark.kural_davranis("<id>")` davranış testlerini işaretler; parametreli testte her parametre kendi işaretini
  alır. D6 meta testleri değer işareti olmayan kuralı, `davranis_fazi` geçerli faza eşit ya da küçük olup davranış
  işareti olmayan kuralı ve pakette olmayan işareti kırmızıya çevirir. `kp::test_atif_kilidi[<id>]` ve
  `kp::test_deger_tablosu[<id>]` yalnız `kural_deger` taşır; davranış eksikliğini örtemez.
- **İki katman.** (1) **Değer ve atıf**: paketteki her kural, giriş fazında `kp::test_atif_kilidi[<id>]` ve
  `kp::test_deger_tablosu[<id>]` parametreli testlerine girer. Değer tablosu test dosyasında korpustan **ayrıca elle**
  yazılır; paket ile karşılaştırılır (çift kayıt). (2) **Davranış**: kuralın `davranis_fazi`nda; kuralı kullanan
  servisin sonucu (`uygun`, `eksik`, `uyari`, `sert`, `denetlenmedi`) ve gerekçe kaydı. Eşikli kurallarda **sınırın
  iki yanı** sınanır: uyarısız ve uyarılı taraf aynı testte ya da yan yana iki testte (14/15 gün, 99/100 öğrenci, 3/4
  katılım, 2/3 kabul oyu, ayın 4/5 ve 15/16'sı, 10/11 ve 20/21. gün, 15/16 gün, 9/10 taksit, 9/10 gün izin bölümü,
  4 ay/4 ay 1 gün, 25/26 ve 65/66 yaş) (MA-15).
- **Uyarı kuralı** gerektiğinde dört testle sınanır: sapma yokken uyarısız · eksik veri gerekçe istemez ve
  "tamamlanacaklar"da kalır (R5) · sapma gerekçesiz reddedilir · gerekçeyle kaydedilir ve denetim izine kural kimliği
  + paket revizyonuyla düşer. **Sert kural**: sapan kayıt hiçbir yoldan kaydedilmez (servis ve uç). **Hesaplanan
  değer** sert kuralında ayrıca gerçek tutarın hesaplanandan farklı olduğu kaydın yapıldığı ve farkın uyarı olduğu
  sınanır (D1). **Kullanıcı kararı** kuralında atfın "kullanıcı kararı …" diye basıldığı sınanır.
- **Köken sütunu.** OYS AYNEN = mantık ve beklenen değer aynen; OYS UYARLA = mantık alınır, değişiklik yazılı; yeni;
  yapısal = kural değil, modelde alanın ya da işlemin olmaması (ör. servis kaydında bedel alanı yok).

### 10.2 Paket testleri (§6.1-6.3)

| Test | Denetim | Kapı |
|---|---|---|
| `kp::test_sema_gecerli` · `kp::test_ondalik_dize_kayan_nokta_yok` · `kp::test_sert_kuralda_gerekce_zorunlu` · `kp::test_kullanici_karari_kuralinda_karar_zorunlu` · `kp::test_yorum_kuralinda_yorum_zorunlu` · `kp::test_davranis_fazi_giristen_once_olamaz` | D1 | F1c |
| `kp::test_kosul_anahtar_ve_degerleri_sozlukte` · `kp::test_kosul_degerleri_okul_karti_enumlariyla_ayni` (`SchoolConfig` alanlarıyla karşılaştırma) | D1 (UY-12) | F1c |
| `kp::test_kimlik_bicimi_ve_tekillik` · `kp::test_yururluk_araliklari_cakismaz` · `kp::test_yayimlanmis_kimlik_silinmemis` · `kp::test_duzeltme_kaydi_ayni_araligin_yerini_alir` · `kp::test_degisiklikler_onceki_revizyonla_tutarli` | D2 (UY-16) | F1c |
| `kp::test_atif_kilidi[<id>]` (her kural) · `kp::test_bozuk_capa_yakalanir` (sahte `madde-99`) · `kp::test_bilgi_dizini_atfi_reddedilir` · `kp::test_draft_dosya_atfi_reddedilir` · `kp::test_kullanici_karari_kimligi_listede` | D3 | F1c |
| `kp::test_fikra_bent_kilidi[<id>]` · `kp::test_cok_fikrali_maddede_fikra_zorunlu` (MA-13) · `kp::test_paragraf_bicimli_fikra` (EK-2 md. 7, 4857 md. 17, 53) · `kp::test_mulga_fikraya_atif_yakalanir` (md. 20/10) · `kp::test_mulga_bende_atif_yakalanir` (sentetik korpus dosyası) · `kp::test_yd_bende_atif_yakalanir` (OSAY 5/2-b) · `kp::test_yd_ibareye_atif_yakalanir` (EK-2 Özel Şartlar md. 1) · `kp::test_yeniden_duzenlenen_iptal_bent_gecer` (OSAY 5/2-d) | D4 (MA-14) | F1c |
| `kp::test_yeter_sayi_tabani_bilesimle_tutarli` · `kp::test_pay_tablolari_toplami_bir` · `kp::test_arz_vadeleri_sirali` · `kp::test_ek3_azami_toplami_25` | D5 | F1c (EK-3 F6) |
| `kp::test_koddaki_kural_cagrilari_pakette` · `kp::test_her_kuralin_deger_testi_var` · `kp::test_davranis_fazi_gelen_kuralin_davranis_testi_var` · `kp::test_isaretler_pyproject_markers_listesinde` | D6 (UY-15) | her faz |
| `kp::test_dagitilan_paket_ozeti` · `kp::test_donem_kopyasi_ozeti` | D7 | F1c |
| `kp::test_sabit_taramasi` | D8 (sezgisel) | her faz |
| `kp::test_deger_tablosu[<id>]` | çift kayıt | giriş fazı |
| `kp::test_kapanmis_donem_yeni_revizyonla_ayni_sonuc` · `kp::test_kapanmis_donemde_revizyon_gecisi_sert` · `kp::test_acik_donem_gecisi_fark_listesi_ve_denetim_izi` · `kp::test_eski_degerli_olay_eski_degerle_hesaplanir` · `kp::test_ekleme_revizyonu_hesap_degistirmez` · `kp::test_duzeltme_revizyonunda_hesabi_degisecek_kayitlar_listelenir` | §6.2 dönem bağı (sentetik `r2` ve `r3` test paketleriyle; UY-16) | F1c |
| `kp::test_paket_yuklenemezse_yazma_kapali_okuma_acik` · `kp::test_bilinmeyen_kimlikte_yazma_kapali` · `kp::test_yururluk_disi_olayda_denetim_yok_bilgi_notu` | §6.1 Erişim (fail-closed; MA-12) | F1c |
| `kp::test_hesaplanan_degerde_fiili_fark_kaydedilir_uyari` · `kp::test_kullanici_karari_atfi_yonetmelik_geregi_demez` · `kp::test_eksik_veri_gerekce_istemez` · `kp::test_kapanis_gecisinde_eksik_sapmaya_doner` · `kp::test_toplu_gerekce_bir_gerekce_cok_kayit` · `kp::test_toplu_gerekce_kapali_kuralda_tek_tek` | §6.1 tür, dayanak türü, eksik ve sapma (D1, R5) | F1c |

### 10.3 Hüküm → test eşlemesi

Kapı: davranış testinin yeşil olması gereken faz = kuralın `davranis_fazi`'dır (§6.4 "Giriş" sütununda parantez
içi). Değer ve atıf testleri giriş fazındadır.

**Genel kurul**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `genel_kurul.olagan_son_ay` | `gk::test_olagan_gk_31_ekim_uyarisiz_1_kasim_uyari` | yeni | F2 |
| `genel_kurul.yeni_okul_ay` | `gk::test_yeni_okul_gk_acilistan_2_ay` · `gk::test_yeni_okul_cagrisi_mudur_hesabindan` | yeni | F2 |
| `genel_kurul.ilan_en_az_gun` | `gk::test_ilan_15_gun_uyarisiz` · `gk::test_ilan_13_gun_gerekcesiz_reddedilir` · `gk::test_ilan_13_gun_gerekceyle_gecer` · `gk::test_ilan_sinir_14_uyari_15_uyarisiz` | OYS AYNEN (3) + yeni | F2 |
| `genel_kurul.ilan_kanallari` | `gk::test_uc_kanal_kaniti_eksikse_tamamlanacak` · `gk::test_tutanak_tamamda_eksik_kanit_gerekce_ister` | yeni (R5) | F2 |
| `genel_kurul.yeter_sayi_taban` | `gk::test_taban_uyelik_kayitlarindan_bagimsiz_16` (eksik kadroyla da 64/32) | yeni (S-1) | F1c |
| `genel_kurul.yeter_sayi_carpan` | `gk::test_yeter_sayi_mevcut_100_ve_ustu_64` · `gk::test_olaganustu_gk_yeter_sayi_64` | OYS UYARLA + yeni (S-2) | F1c |
| `genel_kurul.kucuk_okul_carpan` | `gk::test_yeter_sayi_mevcut_99_32` | OYS UYARLA | F1c |
| `genel_kurul.kucuk_okul_esik` | `gk::test_esik_99_ve_100` · `gk::test_mevcut_gk_kaydina_anlik_yazilir` | yeni | F1c |
| `genel_kurul.ikinci_toplanti_en_gec_gun` | `gk::test_ikinci_toplanti_baglantisi` · `gk::test_ikinci_toplanti_30_gun_uyarisiz_31_uyari` (birinci toplantı gününden) | OYS UYARLA + yeni | F2 |
| `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | `gk::test_ikinci_toplanti_cogunluksuz` · `gk::test_olaganustu_ikinci_toplanti_cogunluksuz` (A-1) | OYS AYNEN + yeni | F2 |
| `genel_kurul.karar_cogunlugu` | `gk::test_karar_katilanlarin_cogunluguyla` · `gk::test_oy_esitliginde_karar_alinmadi` · `gk::test_oylarla_celisen_kabul_isareti_konamaz` | yeni | F2 |
| `genel_kurul.gundem_degisikligi` | `gk::test_oylanmadan_gundem_eklemesi_gerekceyle_kaydedilir` · `gk::test_oy_coklugu_ile_ekleme_uyarisiz` · `gk::test_sira_degisikligi_uyari_uretmez` | yeni (S → U; MA-16, EK-5) | F2 |
| `genel_kurul.olaganustu_cagiranlar` | `gk::test_olaganustu_cagiran_listede` · `gk::test_baskanin_13_8_cagrisi_listede` · `gk::test_dk_14_5_cagrisi_yalniz_md6_aykirilik_isaretiyle` (`md6_violation_found` yokken DK çağrı seçeneği açılmaz; `irregularity_found` tek başına açmaz) | yeni (MB-10) | F2 |
| `genel_kurul.olaganustu_basvuru_oran` | `gk::test_yuzde_10_alti_basvuru_uyari` · `gk::test_yuzde_10_basvuru_uyarisiz` | yeni | F2 |
| `genel_kurul.olaganustu_gundeme_baglilik` | `gk::test_olaganustu_gundem_disi_madde_uyari` · `gk::test_olaganustu_gundem_disi_madde_gerekceyle_kaydedilir` (B-13: sert değil) | yeni | F2 |
| `genel_kurul.divan_uye_turleri` | `gk::test_divana_veli_olmayan_ogretmen_secilirse_uyari` · `gk::test_divana_veli_olan_ogretmen_uyarisiz` | yeni (MA-11) | F2 |
| `genel_kurul.secim_bicimi` | `gk::test_secim_liste_ve_acik_oy` (liste dışı ya da gizli oy kaydı → uyarı) | yeni (MA-15) | F2 |

**Yönetim kurulu ve ortak üyelik**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `yonetim_kurulu.asil_uye` | `yk::test_yk_eksik_kadro_uyari` · `yk::test_yk_tam_kadro_uyarisiz` · `yk::test_dusen_koltuk_sayima_girmez` | OYS AYNEN (3) | F1c |
| `yonetim_kurulu.yedek_uye` | `yk::test_yk_eksik_kadro_uyari[yedek]` | OYS AYNEN (parametre) | F1c |
| `yonetim_kurulu.uye_turleri` | `yk::test_yk_ye_veli_olmayan_ogretmen_ve_idareci_eklenemez` · `yk::test_veli_olan_ogretmen_yk_ye_eklenebilir` · `yk::test_yk_ye_kursiyer_ve_hayirsever_eklenebilir` | yeni (F1 kapısı; MA-11) | F1c |
| `yonetim_kurulu.okul_muduru_uye_olamaz` | `yk::test_veli_olan_okul_muduru_yk_ye_eklenemez` · `yk::test_atif_kullanici_karari_ke15_diye_basilir` | yeni (F1 kapısı) | F1c |
| `yonetim_kurulu.gorev_suresi_yil` | `yk::test_gorev_suresi_bitiminde_uyari` | yeni | F1c |
| `yonetim_kurulu.gorev_bolumu_gun` | `yk::test_gorev_bolumu_7_gun_uyarisiz_8_gun_uyari` · `yk::test_yedek_cagrisindan_sonra_7_gun` | yeni | F1c |
| `yonetim_kurulu.gorevler` | `yk::test_ikinci_baskan_kaydedilemez` | yeni | F1c |
| `yonetim_kurulu.secilme_siniri` | `yk::test_baskan_besinci_secim_gerekcesiz_reddedilir` · `yk::test_baskan_besinci_secim_gerekceyle_gecer` · `yk::test_uye_dorduncu_secimde_uyarisiz_besincide_uyari` · `yk::test_gecmis_eksikse_tamamlanacak_engel_yok` · `yk::test_donem_siniri_ucu_gerekce` | OYS UYARLA (3) + yeni (S-4) | F1c |
| `yonetim_kurulu.tek_birlik` | `yk::test_baska_birlikte_gorevli_isaretiyle_uyari` · `yk::test_tek_birlik_beyani_yoksa_mevzuat_uyarisi_yok` (okul uygulaması hatırlatması) | yeni (KM-8) | F1c |
| `uyelik.suc_engeli` | `yk::test_engel_tespitinde_dusurme_onerisi_tespit_tarihiyle` · `yk::test_beyansiz_uye_okul_uygulamasi_hatirlatmasi` · `yk::test_beyan_yalniz_tarih` | OYS UYARLA (not alanı kalkar) + yeni (KM-8, MA-15) | F1c |
| `uyelik.ayrilan_veli_devam` | `yk::test_yk_4_altina_duserse_ayrilan_uye_devam_onerisi[veli, kursiyer]` · `yk::test_dusurme_gerekcesiz_reddedilir` · `yk::test_dusme_gerekcesi_kaydi` | yeni (MA-16) + OYS AYNEN (2) | F1c |
| `yonetim_kurulu.yedek_cagirma` | `yk::test_yedek_oy_sirasi_alani` · `yk::test_yedek_oy_sirasiyla_cagrilir` · `yk::test_sira_disi_cagri_gerekce_ister` | OYS AYNEN + yeni (F1 kapısı) | F1c |
| `yonetim_kurulu.toplanti_yeter_sayi` | `yk::test_3_katilimla_karar_girilemez` · `yk::test_4_katilimla_toplanti_gecerli` | yeni (MA-15) | F3 |
| `yonetim_kurulu.karar_yeter_sayi` | `yk::test_2_kabul_oyuyla_karar_alinmadi` · `yk::test_3_kabul_oyuyla_karar_alindi` | yeni (MA-15) | F3 |
| `yonetim_kurulu.toplanti_sikligi` | `yk::test_toplantisiz_ders_ayi_uyari_yaz_ayi_uyarisiz` | yeni | F3 |
| `yonetim_kurulu.devamsizlik_siniri` | `yk::test_ust_uste_3_ozursuz_dusme_onerisi` · `yk::test_ozurlu_devamsizlik_saymaz` · `yk::test_araya_katilim_seriyi_bozar` · `yk::test_katilim_ucu_ucuncu_ozursuzde_oneri` · `yk::test_kayitsiz_toplanti_eksik_veri_uyarisi` · `yk::test_dk_de_dusme_yok` | OYS UYARLA (4) + yeni (S-19) + OYS AYNEN | F3 |
| `yonetim_kurulu.olaganustu_cagri_ay` | `yk::test_yedeklerle_3_altina_dusunce_1_ay_uyarisi` | yeni | F3 |

**Denetleme Kurulu ve temsilciler**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `denetleme_kurulu.asil_uye` | `dk::test_dk_eksik_kadro_uyari[asil]` | yeni | F1c |
| `denetleme_kurulu.yedek_uye` | `dk::test_dk_eksik_kadro_uyari[yedek]` | yeni | F1c |
| `denetleme_kurulu.koltuklar` | `dk::test_veli_ogretmen_ayrimi` · `dk::test_veli_koltuguna_hayirsever_giremez` · `dk::test_baska_okul_ogretmeni_onay_no_ister` · `gk::test_dk_ogretmen_koltugu_gk_oylamasina_girmez` | OYS UYARLA + yeni (F1 kapısı; EK-5) | F1c |
| `denetleme_kurulu.gorev_bolumu_gun` | `dk::test_dk_gorev_bolumu_7_gun` | yeni | F1c |
| `denetleme_kurulu.gorev_suresi_yil` | `dk::test_dk_gorev_suresi_bitiminde_uyari` | yeni | F1c |
| `denetleme_kurulu.baskan_secilme_siniri` | `dk::test_dk_baskan_siniri_farkli_organi_etkilemez` · `dk::test_dk_baskani_ucuncu_secimde_uyarisiz_dorduncude_uyari` | OYS AYNEN + yeni | F1c |
| `denetleme_kurulu.inceleme_yilda_en_az` | `dk::test_tek_ara_raporla_donem_sonu_uyari` | yeni | F4 |
| `denetleme_kurulu.yk_uyesi_olamaz` | `dk::test_yk_uyesi_dk_ye_eklenemez` · `dk::test_dk_uyesi_yk_ye_eklenemez` · `dk::test_ekim_2026_genel_kurulunda_da_gecerli` (GK 15.10.2026 → sert) · `dk::test_atif_kullanici_karari_a2_diye_basilir` | OYS UYARLA (sonuç tersine) + yeni (MA-1) | F1c |
| `denetleme_kurulu.ogretmen_gorevlendirme_ay` | `dk::test_4_ay_uyarisiz_4_ay_1_gun_yedek_onerisi` · `dk::test_dk_yedegi_cagrisi_yk_karari_istemez` (yazan `yonetici`, M2) | yeni (MA-15) | F1c |
| — (kural değil: DK rapor bayrağı `AuditReport.irregularity_found`, §5) | `dk::test_uygunsuz_madde_rapor_bayragini_kaldirir` · `dk::test_tumu_uygun_rapor_bayragi_yok` · `dk::test_rapor_bayragi_olaganustu_cagri_onermez` | OYS AYNEN (2) + yeni (MB-10) | F4 |
| `temsilci.odul_disiplin_kurulu`, `temsilci.davranis_degerlendirme_kurulu`, `temsilci.sosyal_etkinlikler_kurulu`, `temsilci.kontenjan_komisyonu`, `temsilci.rpd_yurutme_komisyonu`, `temsilci.tasimaci_tespit_komisyonu`, `temsilci.muhammen_bedel_komisyonu`, `temsilci.kiralama_ihale_komisyonu`, `temsilci.pay_dagitim_komisyonu` (9 kural) | `tm::test_kademeye_gore_temsilci_satirlari[<id>]` (her kural bir parametre: kademe koşulu, sayı, yedek) · `tm::test_karma_okulda_iki_kademenin_satirlari` (UY-12) · `tm::test_baskan_kendiliginden_uye[tasimaci_tespit, muhammen_bedel, kiralama_ihale]` · `tm::test_pay_dagitim_komisyonu_yalniz_secildiyse` · `tm::test_rpd_satirinda_ogretmenler_kurulu_notu` | yeni | F1c |

**Gelir, bağış, makbuz, etkinlik, harcama, bildirim**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `bagis.elden_yatirma_is_gunu` | `ml::test_cuma_kabul_sonraki_cuma_besinci_is_gunu` (kabulü izleyen iş gününden) · `ml::test_resmi_tatil_is_gunu_sayilmaz` | yeni | F3 |
| `bagis.kayit_doneminde_toplanmaz` | `ml::test_kayit_doneminde_bagis_uyari` · `ml::test_diploma_doneminde_bagis_uyari` · `ml::test_donem_disinda_bagis_uyarisiz` | yeni (MA-15) | F3 |
| `gelir.proje_protokol_ucret_yasak` | `ml::test_proje_kapsamindaki_etkinlikte_ucret_uyari` | yeni | F4 |
| `bagis.sartli_amac` | `ml::test_sartli_alt_hesap_eksiye_dusemez` · `ml::test_amaca_baglanmayan_gider_kaydedilmez` | yeni | F3 |
| `bagis.ayni_teslim` | `ml::test_ayni_bagista_vif_eksigi_tamamlanacaklarda` · `ml::test_donem_kapanisinda_vif_eksigi_gerekce_ister` | yeni (R5) | F3 |
| `makbuz.cilt_yaprak` | `ml::test_cilt_50_disi_yaprak_uyari` · `ml::test_cilt_50_yaprak_uyarisiz` | yeni | F3 |
| `makbuz.seri_cilt_sira_tekil` | `ml::test_ayni_yaprak_iki_kez_kullanilamaz` · `ml::test_iptal_yaprak_yeniden_kullanilamaz` · `ml::test_kayip_yaprak_yeniden_kullanilamaz` | yeni | F3 |
| `makbuz.muhur_ve_karar_kaydi` | `ml::test_muhursuz_cilt_kullanima_acilirken_uyari` | yeni | F3 |
| `etkinlik.onay_zinciri` | `ml::test_mem_onayi_yoksa_etkinlik_geliri_uyari` | yeni | F4 |
| `etkinlik.ders_saatleri_disinda` | `ml::test_ucuncu_kisi_etkinligi_ders_saatinde_uyari` · `ml::test_birlik_etkinligi_ders_saatinde_uyarisiz` | yeni (MA-8) | F4 |
| `harcama.yk_karari` | `ml::test_kararsiz_harcama_uyari` · `ml::test_genel_karar_gerekce_sayilir` | yeni (saha.md 6) | F4 |
| `harcama.okul_yazili_talep` | `ml::test_talepsiz_harcama_uyari` · `ml::test_gelen_evrak_talebi_yeter` | yeni (SU-10) | F4 |
| `harcama.alim_komisyonu_en_az` | `yk::test_alim_komisyonu_ucten_az_uyari` · `yk::test_uc_kisilik_alim_komisyonu_uyarisiz` (organ ekranı; dosyadaki karşılığı `ml::test_dosyada_iki_kisilik_komisyon_uyari`, F4) | yeni (MA-7, MA-15) | F1c |
| `harcama.alim_komisyonu_uyeleri` | `ml::test_yk_disi_uyede_uzmanlik_isareti_yoksa_uyari` · `ml::test_komisyon_kisileri_tek_kaynaktan` | yeni (KM-8, UY-20) | F4 |
| `harcama.musterek_imza` | `ml::test_tek_imzali_odeme_uyari` · `ml::test_baskan_yokken_baskan_yardimcisi` | yeni | F4 |
| `harcama.tasinir_kaydi` | `ml::test_tasinir_aliminda_vif_yoksa_uyari` | yeni | F4 |
| `harcama.organ_uyesine_odeme` | `ml::test_yk_uyesine_odeme_uyari` · `ml::test_organ_uyesine_odemede_toplu_gerekce_yok` | yeni | F4 |
| `bildirim.aylik_mudur` | `ml::test_ay_bitti_bildirim_yok_uyari` | yeni | F4 |
| `duyuru.butce` | `ml::test_butce_duyuru_kaniti_yoksa_uyari` | yeni | F4 |
| `duyuru.gelir_gider_donemlik` | `ml::test_donemde_duyuru_yoksa_uyari` | yeni | F4 |
| `vergi.damga_harc_muafiyeti` | `ml::test_birlik_kagidinda_damga_hesaplanmaz` | yeni | F4 |
| `denetim.mem_yilda_en_az` | `ml::test_yil_icinde_mem_denetimi_yoksa_pano_uyarisi` | yeni | F4 |

**Kantin: arz, pay, kira**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `arz_bedeli.kira_oran` | `pd::test_kiraya_verme_yuzde_3_ve_dagitim` · `pd::test_fiili_arz_odemesi_farkliysa_kaydedilir_fark_uyari` | OYS AYNEN + yeni (D1) | F3 |
| `arz_bedeli.isletme_oran` | `pd::test_isletme_yuzde_1_ve_gider_dususu` | OYS AYNEN | F5 |
| `arz_bedeli.donem_ay` | `pd::test_ceyrekler_takvim_ceyregi` · `pd::test_pesin_odeme_secenegi` | OYS UYARLA (KE-2) | F3 |
| `arz_bedeli.sozlesme_vade_gunu` | `pd::test_vade_10_uyarisiz_11_sozlesme_vadesi_gecti` | OYS UYARLA | F3 |
| `arz_bedeli.yonetmelik_vade_gunu` | `pd::test_vade_20_tek_uyari_21_iki_uyari` · `pd::test_vade_tatilde_kaymaz` (KE-18) | OYS UYARLA + yeni | F3 |
| `arz_bedeli.takip_sorumlulari` | `ev::test_e24_mudur_ve_baskan_imzasi` | yeni | F3 |
| `arz_bedeli.diger_tahsilat_oran` | `pd::test_tahliye_cezasinda_yuzde_3_arz` · `pd::test_fesih_tazminatinda_yuzde_3_arz` | yeni | F5 |
| `pay_dagitimi.genel` | `pd::test_dagitim_80_10_10` · `pd::test_kurus_artigi_toplam_korunur` (KE-3) | OYS AYNEN + yeni | F3 |
| `pay_dagitimi.il_merkezi` | `pd::test_buyuksehir_olmayan_il_merkezi_ilce_0_il_20` · `pd::test_buyuksehir_olmayan_ilin_ilcesi_80_10_10` | OYS UYARLA (S-17) + yeni | F3 |
| `pay_dagitimi.isletme_net_tabani` | `pd::test_isletmede_giderler_dusulur` | OYS AYNEN (aynı test) | F5 |
| `kira.odeme_gunleri` | `pd::test_kira_4unde_uyari_5inde_uyarisiz` · `pd::test_kira_15inde_uyarisiz_16sinda_uyari` | yeni (MA-15) | F3 |
| `kira.yariyil_ayi_carpani` | `pd::test_yariyil_ayi_yarim_kira` · `pd::test_yariyil_ayinda_tam_odeme_kaydedilir_fark_uyari` | yeni (D1) | F3 |
| `kira.ay_sayisi` | `pd::test_9_aylik_sozlesmede_yaz_kirasi_yok` · `pd::test_12_aylik_tam_yil` · `pd::test_9_ve_12_disi_ay_sayisi_gerekceyle_kaydedilir` | yeni (D1) | F3 |
| `kira.mucbir_sebep_indirimi` | `pd::test_mucbir_indirim_gerekceyle` | yeni | F5 |
| `kira.ust_uste_odememe_fesih` | `pd::test_iki_odeme_ust_uste_odenmezse_fesih_onerisi` · `pd::test_arali_iki_odenmeyen_ay_fesih_onerisi_degil` | yeni (MA-16) | F5 |
| `kantin.kdv_istisnasi` | `pd::test_kira_tahsilatinda_kdv_yok` | yeni | F3 |

**Kantin: kiralama, sözleşme, belgeler**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `kantin.kiralama_usulu` | `kn::test_kiralama_pazarlik_ve_alan_uyarisi` · `kn::test_pazarlikta_en_yuksek_bedel` · `kn::test_pazarlik_disi_usul_gerekceyle_kaydedilir` | OYS AYNEN (2) + yeni (D1) | F5 |
| `kantin.kiralama_onay_kaydi` | `kn::test_onay_kaydi_yoksa_kesinlestirme_gerekceyle_gecer` · `kn::test_onay_uyarisi_yonetmelik_geregi_demez` | yeni (D4) | F5 |
| `kantin.istekli_belge_sarti` | `kn::test_belgesi_eksik_istekli_gerekceyle_gecer` · `kn::test_birinci_kademe_varken_diploma_uyari` · `kn::test_hicbirinde_birinci_kademe_yoksa_diploma_uyarisiz` | OYS UYARLA (sert → uyarı) + yeni (MA-6) | F5 |
| `kantin.esnaf_odasi_belgesi` | `kn::test_esnaf_odasi_belgesi_yoksa_uyari` | yeni | F5 |
| `kantin.hisimlik_derecesi` | `kn::test_kiralama_hisimlik_engeli` · `kn::test_ucuncu_derece_hisim_katilabilir` · `kn::test_kayin_hisim_ikinci_derece_engel` · `kn::test_serviste_hisimlik_kurali_yok` | OYS AYNEN + UYARLA + yeni (MA-15) | F5 |
| `kantin.istekli_suc_engeli` | `kn::test_suc_engeli_sert_atif_20_11` · `kn::test_tespit_yontemi_mevzuat_geregi_diye_sunulmaz` | OYS UYARLA (atıf) + yeni (KM-8) | F5 |
| `kantin.calisan_niteligi` | `kn::test_portor_ve_adli_sicil_istekliden_istenmez` · `kn::test_belgesiz_calisan_uyari` | yeni (S-8, MA-15) | F5 |
| `kantin.yillik_yenileme` | `kn::test_faaliyet_belgesi_12_ayda_uyarisiz_12_ayi_asinca_uyari` | yeni | F5 |
| `kantin.calisan_hijyen_belgesi` | `kn::test_hijyen_belgesiz_calisan_uyari` | yeni | F5 |
| `kantin.kisa_sureli_bedel_birimi` | `kn::test_kisa_sureli_bedel_birimleri` | yeni | F5 |
| `kantin.isletmede_vergi_uyarisi` | `kn::test_birlikce_isletme_secilince_vuk_uyarisi` | yeni | F1c |
| `kira.sozlesme_en_fazla_yil` | `kn::test_5_yil_artik_yilda_dogru` · `kn::test_5_yil_1_gun_uyari` | yeni (S-18) | F5 |
| `kira.toplam_en_fazla_yil` | `kn::test_20_yil_sozlesme_zincirinden` | yeni | F5 |
| `kira.yirmi_yil_taban_tarihi` | `kn::test_2005_oncesi_ilk_sozlesme_31_05_2005ten` | yeni | F5 |
| `kira.yirmi_yil_yeniden_baslangic` | `kn::test_ilanli_pazarlik_yeni_baslangic` · `kn::test_teklif_kabul_yenilemesi_baslatmaz` | yeni | F5 |
| `kira.yirmi_yil_ilave` | `kn::test_540_gun_ve_dondurulan_sure_eklenir` · `kn::test_540_sabit_tarih_farkindan_hesaplanmaz` | yeni (MA-15) | F5 |
| `kira.yer_teslimi_gun` | `kn::test_yer_teslimi_15_gunde_uyarisiz_16_gunde_uyari` | yeni (MA-15) | F5 |
| `kira.imzadan_once_teslim_yok` | `kn::test_imzasiz_sozlesmede_teslim_gerekceyle_kaydedilir` | yeni (EK-5) | F5 |
| `kira.tufe_artisi` | `kn::test_ilk_yil_artis_yok` · `kn::test_ikinci_yil_tufe_uygular` · `kn::test_tufeden_farkli_artis_gerekceyle_kaydedilir` · `kn::test_tufe_servis_sozlesmesine_uygulanmaz` (yapısal) | OYS UYARLA (2) + AYNEN + yeni (D1) | F5 |
| `kira.ogrenci_degisim_esigi` | `kn::test_mevcut_yuzde_25_degisince_oneri` · `kn::test_yuzde_24_degisimde_oneri_yok` | yeni (MA-15) | F5 |
| `kira.kesin_teminat_oran` | `kn::test_teminat_yillik_kiranin_yuzde_6_uyarisiz` · `kn::test_farkli_teminat_gerekceyle_kaydedilir` · `kn::test_2023_oncesi_sozlesme_kaydedilir_bilgi_notu` | yeni (D1, MA-12) | F5 |
| `kira.tahliye_gunluk_ceza_oran` | `kn::test_tahliye_cezasi_gunluk_yuzde_3` · `kn::test_tahsil_edilen_ceza_farkliysa_fark_uyari` | yeni (D1) | F5 |
| `kira.fesih_tazminati` | `kn::test_fesihte_cari_donem_kirasi_teminat_ve_mahsup[9_ay, 12_ay]` | yeni (MA-9) | F5 |
| `kira.fesih_ihtar_gun` | `kn::test_ihtardan_15_gun_dolmadan_fesih_uyari_16_gunde_uyarisiz` | yeni (MA-15) | F5 |
| `kira.bakanlik_tahliye_gun` | `kn::test_bakanlik_tebligatindan_15_gun_sayaci` | yeni (MA-9) | F5 |
| `kira.yeniden_kiralama_bildirim_ay`, `yeniden_kiralama_cevap_gun`, `muhammen_bedel_teklif_ay`, `tufe_bildirimi`, `milli_emlak_ornegi` | `kn::test_kiralama_takvim_uyarilari[<id>]` (bitişe 2 ay / cevap 15 gün / bitişe 1 ay / artıştan sonra MEM bildirimi / millî emlak gönderimi; süre dolmadan uyarısız, dolunca uyarı) | yeni | F5 |
| `kira.ihaleden_yasaklama_yil` | `kn::test_yasakli_istekli_uyari` | yeni | F5 |

**Servis**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `servis.ilan_en_az_gun` | `sv::test_ilan_7_gun_uyarisiz_6_gun_uyari` | yeni | F6 |
| `servis.ilan_kanallari` | `sv::test_ilan_tutanaginda_iki_kanal` | yeni | F6 |
| `servis.komisyon_bilesimi` | `sv::test_komisyon_uygun_gerekce_istemez` · `sv::test_komisyon_baskan_sapmasi_gerekce_ister` · `sv::test_yedekler_sayilir` | OYS AYNEN (2) + yeni | F6 |
| `servis.komisyon_karar_cogunlugu` | `sv::test_esitlikte_baskanin_tarafi` · `sv::test_cogunluk_yoksa_karar_alinmadi` | yeni (S-7, MA-4) | F6 |
| `servis.komisyon_cekimser_ve_serh` | `sv::test_cekimser_oy_gerekceyle_kaydedilir` · `sv::test_serhsiz_muhalif_uyari` | yeni (MA-4) | F6 |
| `servis.degerlendirme_yontemi` | `sv::test_varsayilan_komisyon_degerlendirmesi` · `sv::test_itirazda_ek3_en_yuksek_puan` · `sv::test_ek3_esitlikte_gerekce` | OYS UYARLA (3) | F6 |
| `servis.ek3_puanlama` | `sv::test_ek3_tohumu_ve_25_tavan` · `sv::test_tam_puan_25` · `sv::test_kademe_disi_puan_uyari[kriter_4]` · `sv::test_ara_kademe_puanlari_uyarisiz[kriter_2_1, kriter_3_3]` · `sv::test_ornek_istekli_23_puan` (uydurma) | OYS AYNEN (2) + UYARLA (2) + yeni (D1, MA-5) | F6 |
| `servis.ek3_kriter_azami_puan` | `sv::test_azamiyi_asan_puan_uyari` | OYS UYARLA (sert → uyarı) | F6 |
| `servis.olur_olmadan_kesinlesmez` | `sv::test_olursuz_kesinlestirme_sert` · `sv::test_onay_kesinlestirme_akisi` · `sv::test_ret_tespiti_iptal_eder` · `sv::test_kesinlestirme_ucu_olursuz_400` | OYS AYNEN (2) + UYARLA (2) | F6 |
| `servis.mulki_amir_onay_is_gunu` | `sv::test_onay_5_is_gunu_bekleme_sayaci` | yeni | F6 |
| `servis.teblig_is_gunu` | `sv::test_teblig_5_is_gunu` | yeni | F6 |
| `servis.sozlesme_imza_gun` | `sv::test_tebligden_10_gunde_imza_uyarisiz_11_gunde_uyari` | yeni | F6 |
| `servis.sozlesme_en_fazla_yil` | `sv::test_servis_suresi_3_yil_ustu_uyari` · `sv::test_sure_disi_ucu_gerekce_ister` | OYS UYARLA (2) | F6 |
| `servis.yeniden_cikma` | `sv::test_basvuru_yoksa_yeniden_cikma` | yeni | F6 |
| `servis.ucret_tarifesi` | `sv::test_servis_kaydinda_muhammen_bedel_alani_yok` (yapısal) · `sv::test_kiralama_muhammen_bedel_yazilir` · `sv::test_servis_bedel_ucu_400` (yapısal) · `sv::test_tarife_kaynagi_bossa_uyari` | OYS AYNEN (2) + UYARLA + yeni (D1) | F6 |
| `servis.taksit_en_fazla` | `sv::test_9_taksit_uyarisiz_10_taksit_uyari` · `sv::test_taksit_ucu_uyari_doner` | OYS UYARLA (2) | F6 |
| `servis.yariyil_ucret_yok` | `sv::test_sozlesme_metninde_yariyil_ucreti_yok` | OYS UYARLA (KE-14) | F6 |
| `servis.muhtac_ogrenci` | `sv::test_muhtac_ogrenci_sozlesmede` | yeni | F6 |
| `servis.tasimaci_ilani` | `sv::test_tasimaci_ilani_unvan_plaka_guzergah` | yeni (D5) | F6 |
| `servis.arac_yasi_en_fazla`, `arac_yasi_hesabi`, `sofor_yasi`, `sofor_belge_yili`, `sofor_b_sinifi_sayilan_yil`, `sofor_psikoteknik_yil`, `saglik_raporu_ay`, `rehber_yasi` | `sv::test_belge_ve_yas_sinirlari[<id>]` (her kural bir parametre; sınırın iki yanı: araç 12/13 yaş, yaş imal yılından sonraki ilk takvim yılından; şoför 26. ve 66. yaş günü; D sınıfı 2 yıl, B sınıfından en çok 1 yıl sayılır; D1 5 yıl, B'den en çok 3 yıl; psikoteknik 5 yıl; rapor 12 ay; rehber 22 ve 61 yaş) | yeni (MA-10, MA-15) | F6 |
| `servis.tuzel_kisi_tescil_orani` | `sv::test_tuzel_kiside_ucte_bir_uyarisiz_altinda_uyari` | yeni (MA-10) | F6 |
| `servis.ozmal_en_fazla_okul` | `sv::test_ozmal_ikinci_okulda_uyarisiz_ucuncude_uyari` | yeni (MA-10) | F6 |
| `servis.fesih_ihtar_gun` | `sv::test_ihtardan_15_gun_dolmadan_fesih_uyari` | yeni (MA-10) | F6 |
| `servis.oda_belgesi_ayni_yil` | `sv::test_oda_belgesi_onceki_yildan_uyari` | yeni (MA-10) | F6 |

**Personel (sürüm 2)**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `personel.sgk_saklama_yil` | `pr::test_sgk_belgesi_10_yil_dolmadan_imha_onerisi_yok` · `pr::test_sure_izleyen_yil_basindan` | yeni | F8 |
| `personel.karsilik_ayrilir` | `pr::test_karsilik_yoksa_uyari` | yeni | F8 |
| `personel.yillik_izin_gun` | `pr::test_izin_14_20_26_basamaklari` (5. yıl 14, 6. yıl 20, 15. yıl 26) · `pr::test_50_yasinda_2_yillik_isciye_en_az_20_gun` · `pr::test_sozlesmeyle_24_gun_uyarisiz` · `pr::test_asgari_altinda_izin_gerekceyle_kaydedilir` | yeni (MA-3) | F8 |
| `personel.izin_bolumu_en_az_gun` | `pr::test_9_gunluk_bolum_uyari_10_gunluk_uyarisiz` | yeni (MA-15) | F8 |
| `personel.ihbar_hafta` | `pr::test_ihbar_suresi_basamaklari` · `pr::test_belirli_sureli_sozlesmede_ihbar_kurali_uygulanmaz` · `pr::test_sozlesmeyle_uzun_ihbar_uyarisiz` | yeni (MA-3) | F8 |

**Kural olmayan, test edilen kararlar** (DOĞRULANMADI listesi, okul uygulamaları ve kural açılmayan hükümler): `pd::test_gecikme_zammi_hesaplanmaz_bilgi_notu` (3) ·
`pd::test_kurus_artigi_toplam_korunur` (4) · `kn::test_serviste_hisimlik_kurali_yok` (6) · `ml::test_saklama_suresi_yok_silme_yok` (9) ·
`kn::test_2023_oncesi_sozlesme_kaydedilir_bilgi_notu` (16) · `yk::test_beyansiz_uye_okul_uygulamasi_hatirlatmasi` ve
`yk::test_tek_birlik_beyani_yoksa_mevzuat_uyarisi_yok` (okul uygulaması, KM-8) · `tm::test_kampus_satiri_yalniz_in_campus`
(md. 13/7 sayı ve süre taşımaz, kural yoktur; `KAMPUS_YONETIMI` kayıt satırı yalnız `in_campus` doğruyken görünür,
E03) · `sv::test_dosya_iade_talebi_gelen_evrak_ve_bilgi_notu` ([U-E md. 7/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7)
ayrı kural değildir: başvuru kaydı silinmez, "geri verildi" durumu yoktur; iade talebi gelen evrak olarak kaydedilir ve
bilgi notu gösterilir; MB-6).

### 10.4 OYS'nin 71 kural testi

Sınıf, envanter §6.1-6.2'deki sınıflamanın plan §1.8 ve F0-9 kararlarıyla güncellenmiş hâlidir: **AYNEN 30 · UYARLA
39 · ALMA 2**. Envanterden sapan **16 test** (liste ve 373 testin sayımı §12.A'da):

- **AYNEN → UYARLA 14:** `ikinci_toplanti_baglantisi` (30 gün denetimi) · `servis_hisimlik_engeli_uygulanmaz`
  (gerekçe "pakette kural yok") · `kiralama_belge_eksik_engeli` (sert → uyarı, iki kademe) · üç devamsızlık testi
  (S-19: otomatik düşme yerine öneri) · `create_contract_servis_sure_uyarisi` ("dönem" → "yıl") ·
  `add_installments_9_gecer_10_engel` ve `puan_azamiyi_asamaz_sert_engel` (plan §1.8: sert → uyarı) ·
  `ikili_kriter_yalniz_0_veya_max` (D1, MA-5: kademe dışı puan uyarı; envanterde `test_scoring`'in dört AYNEN testinden) ·
  `add_installments_yariyil_atlar` (taksit kaydı yok; sözleşme metninde, KE-14) ·
  `membership_ayni_kisi_farkli_organda_serbesttir` (sonuç tersine, A-2) · `red_ihaleyi_iptal_eder` (adında "ihale" →
  "tespit") · `ilk_yil_artis_yok` (`IndexRate.value` anlamı; farklı artış gerekçeyle, D1).
- **UYARLA → AYNEN 1:** `record_board_decision_taslak_varsayilan`.
- **UYARLA → ALMA 1:** `gecikme_zammi` (6183 korpusta yok; yerine "hesaplanmaz" testi).

İki puanlama testi (`puanlama_*`) envanterde zaten UYARLA'dır (S-7), sapma değildir. Kesin sayım F2-F6'da test
taşınırken test başına sınıf yazılan listeyle doğrulanır; yeni sapma çıkarsa bu listeye ve §12.A sayımına girer.
D1 ile türü uyarıya dönen TÜFE, kiralama usulü ve servis ücreti kurallarının öteki OYS testleri yapısal davranışı
sınadığı için sınıfları değişmedi: servis kaydında bedel alanı, servis sözleşmesinde TÜFE işlemi yoktur.

| OYS testi (dosya :: ad) | Adet | Sınıf | OAB Defteri'nde | Değişiklik |
|---|---|---|---|---|
| `test_assembly` :: `quorum_100_ustu_ogrenci`, `quorum_100_alti_ogrenci` | 2 | UYARLA | `genel_kurul.yeter_sayi_*` | Kurulum tam kadrosuz; taban sabit 16 |
| `test_assembly` :: `quorum_ikinci_toplanti_cogunluksuz` | 1 | AYNEN | `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | — |
| `test_assembly` :: `yeterli_ilan_suresi_uyarisiz`, `13_gun_gerekcesiz_reddedilir`, `13_gun_gerekceyle_gecer` | 3 | AYNEN | `genel_kurul.ilan_en_az_gun` | Sınır testi (14/15) ayrıca yeni |
| `test_assembly` :: `ikinci_toplanti_baglantisi` | 1 | UYARLA | `genel_kurul.ikinci_toplanti_en_gec_gun` | 30 gün denetimi eklenir |
| `test_assembly_write` :: `13_gun_gerekcesiz_400`, `13_gun_gerekceyle_201` | 2 | UYARLA | `genel_kurul.ilan_en_az_gun` (uç) | K2 rolleri, aile uç katmanı |
| `test_audit` :: `uygunsuz_madde_usulsuzluk_bayragi_kaldirir`, `tumu_uygun_usulsuzluk_yok` | 2 | AYNEN | DK rapor bayrağı `AuditReport.irregularity_found` (kural değil): `dk::test_uygunsuz_madde_rapor_bayragini_kaldirir`, `dk::test_tumu_uygun_rapor_bayragi_yok` | Bayrak md. 14/5 yoluna bağlanmaz; o yol `md6_violation_found`'dadır (`gk::test_dk_14_5_cagrisi_yalniz_md6_aykirilik_isaretiyle`; MB-10) |
| `test_audit_write` :: `update_uygunsuz_bulgu_irregularity_true`, `update_hepsi_uygun_irregularity_false` | 2 | UYARLA | aynı bayrak (uç) | DK hesabından yazma (K2) |
| `test_bidder` :: `suc_engeli_sert` | 1 | UYARLA | `kantin.istekli_suc_engeli` | Atıf 12/5 → 20/11 |
| `test_bidder` :: `kiralama_hisimlik_engeli` | 1 | AYNEN | `kantin.hisimlik_derecesi` | — |
| `test_bidder` :: `servis_hisimlik_engeli_uygulanmaz` | 1 | UYARLA | kural yok (DOĞRULANMADI-6) | Gerekçe "pakette servis hısımlık kuralı yok" |
| `test_bidder` :: `kiralama_belge_eksik_engeli` | 1 | UYARLA | `kantin.istekli_belge_sarti` | Sert → uyarı; iki kademe (MA-6); md. 20/5 ayrı kural |
| `test_bidder` :: `puanlama_kazanan_en_yuksek`, `puanlama_esitlik_gerekce_ister` | 2 | UYARLA | `servis.degerlendirme_yontemi` | Yalnız itiraz/yeni okul kipinde |
| `test_bidder` :: `pazarlik_kazanan_en_yuksek_teklif` | 1 | AYNEN | `kantin.kiralama_usulu` | — |
| `test_bidder` :: `en_dusuk_teklif_kazanan` | 1 | ALMA | — | Yürürlükten kalkan 10.01.2018 metni |
| `test_board` :: `ust_uste_3_mazeretsiz_devamsizlik_dusurur`, `mazeretli_devamsizlik_dusurmez`, `araya_bir_katilim_girerse_seri_bozulur` | 3 | UYARLA | `yonetim_kurulu.devamsizlik_siniri` | Öneri üretir; sayım toplantılar üzerinden |
| `test_board` :: `dk_toplantisinda_otomatik_dusme_yok` | 1 | AYNEN | `yonetim_kurulu.devamsizlik_siniri` | — |
| `test_board` :: `record_board_decision_taslak_varsayilan` | 1 | AYNEN | konum KDT (`ev`) | — |
| `test_board_write` :: `attendance_ucuncu_mazeretsiz_devamsizlik_dusurur` | 1 | UYARLA | `yonetim_kurulu.devamsizlik_siniri` (uç) | Öneri döner |
| `test_contract` :: `create_contract_servis_sure_uyarisi` | 1 | UYARLA | `servis.sozlesme_en_fazla_yil` | "Dönem" → "yıl" (OSAY 8/1) |
| `test_contract` :: `add_installments_9_gecer_10_engel` | 1 | UYARLA | `servis.taksit_en_fazla` | Sert → uyarı |
| `test_contract` :: `add_installments_yariyil_atlar` | 1 | UYARLA | `servis.yariyil_ucret_yok` | Taksit kaydı yok; sözleşme metninde sınanır (KE-14) |
| `test_contract` :: `create_contract_kiralama_alan_uyarisi` | 1 | AYNEN | değişmez: kira sözleşmesi bir alana bağlı | — |
| `test_contract_write` :: `servis_sure_disi_gerekce_ister_400`, `add_installments_ondan_fazla_400` | 2 | UYARLA | `servis.sozlesme_en_fazla_yil`, `servis.taksit_en_fazla` (uç) | Uç; taksitte uyarı döner |
| `test_membership_lifecycle` :: `yk_eksik_uyari_uretir`, `yk_tam_uyarisiz` | 2 | AYNEN | `yonetim_kurulu.asil_uye`, `yedek_uye` | Kişi türü ayrı (yeni) |
| `test_membership_lifecycle` :: `dk_veli_ogretmen_ayrimi` | 1 | UYARLA | `denetleme_kurulu.koltuklar` | Hayırsever veli koltuğundan çıkar |
| `test_membership_lifecycle` :: `dustu_koltuk_kompozisyon_sayimina_girmez` | 1 | AYNEN | `yonetim_kurulu.asil_uye` | — |
| `test_membership_lifecycle` :: `baskan_5_kez_gerekcesiz_reddedilir`, `baskan_5_kez_gerekceyle_gecer` | 2 | UYARLA | `yonetim_kurulu.secilme_siniri` | Üyeler de sayılır |
| `test_membership_lifecycle` :: `dk_baskan_3_sinir_farkli_organda_etkilemez` | 1 | AYNEN | `denetleme_kurulu.baskan_secilme_siniri` | — |
| `test_membership_lifecycle` :: `drop_membership_gerekcesiz_reddedilir` | 1 | AYNEN | `uyelik.ayrilan_veli_devam` (düşürme akışı) | — |
| `test_membership_write` :: `promote_baskan_donem_siniri_gerekce` | 1 | UYARLA | `yonetim_kurulu.secilme_siniri` (uç) | — |
| `test_models` :: `membership_dustu_gerekcesi`, `membership_yedek_sirasi` | 2 | AYNEN | `uyelik.ayrilan_veli_devam`, `yonetim_kurulu.yedek_cagirma` | — |
| `test_models` :: `membership_uygunluk_beyani_alanlari` | 1 | UYARLA | `uyelik.suc_engeli` (okul uygulaması alanı) | Şifreli not alanı kalkar (KVKK); beyan tarihi okul uygulamasıdır (KM-8) |
| `test_models` :: `membership_ayni_kisi_farkli_organda_serbesttir` | 1 | UYARLA | `denetleme_kurulu.yk_uyesi_olamaz` | Beklenen sonuç tersine döner (kullanıcı kararı, §15 A-2) |
| `test_scoring` :: `ek3_seed_idempotent_ve_maks_25`, `tam_puan_25` | 2 | AYNEN | `servis.ek3_puanlama` | Tohum paketten |
| `test_scoring` :: `ikili_kriter_yalniz_0_veya_max` | 1 | UYARLA | `servis.ek3_puanlama` | Kademe dışı puan uyarı + gerekçe (D1, MA-5): `sv::test_kademe_disi_puan_uyari[kriter_4]`; ikili olan yalnız 4. kriter |
| `test_scoring` :: `puan_azamiyi_asamaz_sert_engel` | 1 | UYARLA | `servis.ek3_kriter_azami_puan` | Sert → uyarı |
| `test_scoring` :: gerçek evrak örneği (23 puan) | 1 | UYARLA | `servis.ek3_puanlama` | Gerçek firma adı ve veri → uydurma (S-21) |
| `test_share` :: `kiraya_verme_yuzde_3_ve_dagitim` | 1 | AYNEN | `arz_bedeli.kira_oran`, `pay_dagitimi.genel` | — |
| `test_share` :: `isletme_yuzde_1_ve_gider_dususu` | 1 | AYNEN | `arz_bedeli.isletme_oran`, `pay_dagitimi.isletme_net_tabani` | — |
| `test_share` :: `non_metropolitan_ilce_yok_il_yirmi` | 1 | UYARLA | `pay_dagitimi.il_merkezi` | Okul kartının üçlü yerleşim türü |
| `test_share` :: `due_date_ceyrekten_turer` | 1 | UYARLA | `arz_bedeli.sozlesme_vade_gunu`, `yonetmelik_vade_gunu` | İki vade, iki uyarı |
| `test_share` :: `gecikme_zammi` | 1 | ALMA | — | 6183 korpusta yok; yerine "hesaplanmaz" testi |
| `test_tender` :: `create_tender_servis_varsayilan_puanlama` | 1 | UYARLA | `servis.degerlendirme_yontemi` | Varsayılan komisyon değerlendirmesi |
| `test_tender` :: `create_tender_kiralama_pazarlik_ve_alan_uyarisi` | 1 | AYNEN | `kantin.kiralama_usulu` | — |
| `test_tender` :: `servis_muhammen_bedel_sert_engel`, `kiralama_muhammen_bedel_yazilir` | 2 | AYNEN | `servis.ucret_tarifesi` (yapısal: servis kaydında bedel alanı yok) | — |
| `test_tender` :: `servis_komisyon_uygun_gerekce_gerektirmez`, `servis_komisyon_baskan_sapmasi_uyari_gerekce` | 2 | AYNEN | `servis.komisyon_bilesimi` | — |
| `test_tender` :: `finalize_onaysiz_sert_engel`, `onay_kesinlestirme_akisi` | 2 | AYNEN | `servis.olur_olmadan_kesinlesmez` | — |
| `test_tender` :: `red_ihaleyi_iptal_eder` | 1 | UYARLA | `servis.olur_olmadan_kesinlesmez` | Test adında "ihale" → "tespit" |
| `test_tender_decision_write` :: `finalize_olursuz_sert_engel_400` | 1 | UYARLA | aynı (uç) | Uç katmanı |
| `test_tender_write` :: `estimated_price_servis_400`, `create_tender_kiralama_alansiz_gerekce_ister_400` | 2 | UYARLA | `servis.ucret_tarifesi` (yapısal); değişmez (alan) | Uç katmanı |
| `test_tufe` :: `ilk_yil_artis_yok`, `ikinci_yil_tufe_uygular` | 2 | UYARLA | `kira.tufe_artisi` | `IndexRate.value` anlamı sabitlenir; farklı artış gerekçeyle kaydedilir (D1) |
| `test_tufe` :: `tufe_servis_sert_engel` | 1 | AYNEN | `kira.tufe_artisi` (yapısal: TÜFE işlemi yalnız kantin sözleşmesinde) | — |

### 10.5 Evrak kuralı testleri (§9)

| Test | Neyi sabitler | Kapı |
|---|---|---|
| `ev::test_konum_kdt[<kod>]` · `ev::test_konum_tfb[<kod>]` · `ev::test_konum_dft[<kod>]` | §9.2 tablosundaki her belgede doğru konum cümlesi gövdede, imza bloğunun hemen üstünde; başka belgede ve altlıkta yok | belgenin fazı |
| `ev::test_karar_taslagi_varsayilan` | Karar "taslak" doğar, "deftere işlendi" işareti defter sıra no ve sayfa ister (OYS AYNEN) | F1c |
| `ev::test_yk_ve_gk_belgelerinde_mudur_yazar_degil` | E05 (yeni okul ve müdürün olağanüstü çağrısı hariç), E10, E28, E34'te "Okul Müdürü" yalnız "Görüldü" blokunda; E28 ve E34'te hiç yok (MB-3) | F2, F4 |
| `ev::test_mudur_bloklari_yalniz_93_tablosunda[<kod>]` | Müdür bloğu yalnız §9.3 tablosundaki belgelerde ve oradaki türüyle; E02, E32, E33, E61'de yok (MB-15) | belgenin fazı |
| `ev::test_e05_imza_cagirana_gore[yk, baskan_13_8, mudur_9_1, mudur_9_6, mudur_13_8, mudur_25_2, dk_14_5, yuzde_10]` | E05'in üreteni ve imza bloğu çağırana göre (MB-3; M-5, M-6) | F2 |
| `ev::test_mudur_yazilari_yalniz_mudur_hesabindan[E05_yeni_okul, E05_olaganustu, E25, E35]` | K2'deki dört müdür yazısı: `yonetici` bu belgeleri oluşturamaz ve taslağını yazamaz (M-11); denetim izinde müdür hesabı | F2, F4 |
| `ev::test_okul_idaresi_yazilarinin_taslagi_yonetici[E12, E44, E70, E72, E73, E76, E77]` | Taslağı `yonetici` oluşturur, imza bloğu Okul Müdürü; müdür hesabı gerekmez, müdür rolü bu belgelere yazamaz (KE-19); E70 müdür yazısı sayılmaz | F2, F4, F5, F6 |
| `ev::test_imza_ad_soyad_bicimi` | Ad ilk harf büyük, SOYAD `tr_upper` (RYUE md. 17/2), "İ/ı" doğru | F1c |
| `ev::test_resmi_yazi_ryue_unsurlari[<kod>]` | §9.1-4 listesindeki her yazıda sayı, tarih, konu, muhatap ve imza bloğu (RYUE md. 11-14, 17) | belgenin fazı |
| `ev::test_servis_evraki_soz_dagarcigi` | E48-E58 ve E73-E79'da `ihale`, `teklif`, `eksiltme` kökü yok (TR katlamalı); tek istisna "ihaleye fesat karıştırma" (KE-9) | F6 |
| `ev::test_duyurularda_kisi_adi_yok` | E06, E29, E30 çıktısında hiçbir `OabPerson` ve `ParentRoster` adı yok | F2, F4 |
| `ev::test_e56_yalniz_unvan_plaka_guzergah` | E56'da taşımacının ad/unvanı, plaka ve güzergâh var; telefon, adres, 11 haneli kimlik deseni, şoför ve veli adı yok; imza "Taşımacıyı Tespit Komisyonu"; ilan süresi bitince kaldırma hatırlatması (D5, KM-13) | F6 |
| `ev::test_tckn_hicbir_belgede_yok[k9_kapali, k9_acik]` | K9 açık ya da kapalı, hiçbir belgede ve dışa aktarımda 11 haneli kimlik deseni yok; K9 açıkken E20'de yalnız "kimlik no kayıtlı: evet/hayır", E18'de "kimlik no kaynağı" sütunu (KM-14) | her faz |
| `ev::test_kisa_aydinlatma_paragrafi[E07, E21, E46, E48, E50, E58]` | Kişisel verinin toplandığı belgede kısa aydınlatma paragrafı ve tam metnin (E04) yeri var (KM-6) | belgenin fazı |
| `ev::test_e04_dort_alt_metin_veri_sorumlusu_bossa_basilmaz` | E04'te dört alt metin ve her birinde KVKK 10/1 (a)-(d) başlıkları; `data_controller_text` boşken basım reddedilir, kalem "tamamlanacaklar"da (KM-6, KM-7, EK-12) | F2 |
| `ev::test_kagit_capasi[E17, E31, E37]` | "Kayıt no: N · Zincir: XXXX-XXXX" satırı basılır; değer basım anındaki zincir başıyla aynı (§4.6.3; GA-9) | F3, F4 |
| `ev::test_e42_il_merkezi_ozel_sart_pay_notu` | Büyükşehir statüsünde olmayan il merkezinde genel şart md. 7 lafzı değişmez, ilçe tutarı "—", Özel Şartlar md. 2'de md. 17/1-a-2 notu (varsayılan; MB-9) | F5 |
| `ev::test_e63_pusulada_parola_alani_yok` | E63'ün içerik modelinde ve çıktısında parola alanı, parola değeri ya da parola için boş satır yok; giriş adı, rol, iş özeti, BSG 9/2 kuralları, kilitleme ve "kapalı zarf" cümlesi var; dosyası saklanmaz | F1b |
| `ev::test_veli_adli_belge_saklanmaz[E07, E08]` | Üretimden sonra dosya ve `content_json` yok, iz yalnız sha256 + satır sayısı + tarih; yalnız `yonetici` üretir; arşiv paketinde yok (R9) | F2, F4 |
| `ev::test_ek2_lafiz_kilidi` · `ev::test_servis_ek2_lafiz_kilidi` · `ev::test_servis_ek1_lafiz_kilidi` | E42, E55 ve E75 metni korpus dosyasıyla karakter karakter aynı (boşluk alanları hariç) | F5, F6 |
| `ev::test_docx_pdf_icerik_esdegerligi[<kod>]` | İki çıktıdan aynı **kanonik metin akışı** çıkarılır ve karşılaştırılır: gövde blokları belge sırasıyla, tablo hücreleri satır satır (Word'de gövde öğeleri sırayla, tablolar dâhil; `Document.paragraphs` yetmez); PDF'te altlık bölgesi ve sayfa numarası ayıklanır; boşluk ve satır sonu normalleştirilir; altlık karşılaştırmaya girmez; `w:caps` yok (UY-18) | belgenin fazı |
| `ev::test_sayfa_butcesi[<kod>]` | Gerçek uzunlukta uydurma veriyle sayfa sayısı sınırı | belgenin fazı |
| `ev::test_yeniden_basim_icerik_ozeti_ayni` · `ev::test_kapanmis_donem_yeniden_basim_ozeti_ayni` | Kayıtlı `content_json`'dan çizilen yeniden basım aynı içerik özetini verir; okul adı, kişi adı ya da şablon sürümü sonradan değişse de (UY-13); kapanmış dönemde yeniden üretim yapılmaz | F1c, F4 |
| `ev::test_ilk_uc_evrak_pilot_esdegerligi` | E01-E03, pilot okulun aynı belgeleriyle (uydurma adlarla) bölüm ve alan eşdeğerliği | F1c |
| `ev::test_katalog_kabul[<kod>]` | §9.6 "Kabul örneği" sütunu; her kod bir parametre | belgenin fazı |
| `ev::test_katalogdaki_her_kodun_testi_var` | E01-E79'un her birinin `ev::test_katalog_kabul` parametresi var; §9.5 ile §9.6 aynı 79 kodu taşır; §7'nin evrak adları katalogdaki adlarla aynı (ad → kod listesi testte); program belgeleri (§9.7) kod almaz | her faz |

### 10.6 F1 kapısı

Plan §2.4'ün kural, organ ve evrak maddeleri bu testlerle karşılanır (aile güvenlik ve rol testleri §4'te):

| Plan §2.4 maddesi | Test(ler) | Kural |
|---|---|---|
| Her kuralın `madde`'si korpusta çapa olarak var (atıf kilidi) | `kp::test_atif_kilidi[*]` · `kp::test_fikra_bent_kilidi[*]` · `kp::test_cok_fikrali_maddede_fikra_zorunlu` · `kp::test_bozuk_capa_yakalanir` · `kp::test_mulga_fikraya_atif_yakalanir` · `kp::test_yd_bende_atif_yakalanir` · `kp::test_yeniden_duzenlenen_iptal_bent_gecer` · `kp::test_her_kuralin_deger_testi_var` · `kp::test_davranis_fazi_gelen_kuralin_davranis_testi_var` | `r1`'deki 53 kural |
| Yeter sayı: mevcut ≥ 100 → 64, < 100 → 32 (5+5+3+3 için) | `gk::test_yeter_sayi_mevcut_100_ve_ustu_64` · `gk::test_yeter_sayi_mevcut_99_32` · `gk::test_esik_99_ve_100` · `gk::test_taban_uyelik_kayitlarindan_bagimsiz_16` · `kp::test_yeter_sayi_tabani_bilesimle_tutarli` | `genel_kurul.yeter_sayi_*`, `kucuk_okul_*` |
| Dönem sınırı sayacı | `yk::test_baskan_besinci_secim_gerekcesiz_reddedilir` · `yk::test_uye_dorduncu_secimde_uyarisiz_besincide_uyari` · `yk::test_gecmis_eksikse_tamamlanacak_engel_yok` · `dk::test_dk_baskani_ucuncu_secimde_uyarisiz_dorduncude_uyari` · `dk::test_dk_baskan_siniri_farkli_organi_etkilemez` | `yonetim_kurulu.secilme_siniri`, `denetleme_kurulu.baskan_secilme_siniri` |
| Kural sürümü değişince kapanmış dönemin hesabı değişmez | `kp::test_kapanmis_donem_yeni_revizyonla_ayni_sonuc` · `kp::test_kapanmis_donemde_revizyon_gecisi_sert` · `kp::test_eski_degerli_olay_eski_degerle_hesaplanir` · `kp::test_duzeltme_revizyonunda_hesabi_degisecek_kayitlar_listelenir` | §6.2 |
| YK'ye veli olmayan eklenemez | `yk::test_yk_ye_veli_olmayan_ogretmen_ve_idareci_eklenemez` · `yk::test_veli_olan_ogretmen_yk_ye_eklenebilir` · `yk::test_veli_olan_okul_muduru_yk_ye_eklenemez` | `yonetim_kurulu.uye_turleri`, `okul_muduru_uye_olamaz` |
| DK bileşimi | `dk::test_veli_ogretmen_ayrimi` · `dk::test_veli_koltuguna_hayirsever_giremez` · `dk::test_dk_eksik_kadro_uyari[*]` · `dk::test_yk_uyesi_dk_ye_eklenemez` | `denetleme_kurulu.koltuklar`, `asil_uye`, `yedek_uye`, `yk_uyesi_olamaz` |
| Yedek oy sırasıyla çağrılır | `yk::test_yedek_oy_sirasiyla_cagrilir` · `yk::test_sira_disi_cagri_gerekce_ister` | `yonetim_kurulu.yedek_cagirma` |
| Aday listesi ve seçim sonucu aynı kişiler | `yk::test_aday_ve_secilen_ayni_kayit` (tek kaynak değişmezi; OYS ilkesi AYNEN) | — |
| Üç belge docx + PDF; Türkçe büyük harf, sayfa sayısı, alanların dolu olduğu; pilot okulla eşdeğerlik | `ev::test_docx_pdf_icerik_esdegerligi[E01, E02, E03]` · `ev::test_imza_ad_soyad_bicimi` · `ev::test_sayfa_butcesi[E01, E02, E03]` · `ev::test_konum_kdt[E01, E03]` · `ev::test_ilk_uc_evrak_pilot_esdegerligi` · `ev::test_katalog_kabul[E01, E02, E03]` | — |
| (F0-9 eki; F1b) Hesap teslim pusulası parolasız | `ev::test_e63_pusulada_parola_alani_yok` · `ev::test_katalog_kabul[E63]` | — |
| (F0-9 eki; F1c) Organ üyeliği kısıtları ve dönem ortasında kurulum (§7.9) | `ak::test_genel_kurulsuz_ayni_uyelik_iki_kez_reddedilir` · `ak::test_iptal_uyelik_tekil_kisita_girmez` · `ak::test_devralinan_uyelik_aday_sarti_olmadan_secildi` · `ak::test_gecis_toplu_sayac_beyani_tek_gerekce` (§10.7) | `yonetim_kurulu.secilme_siniri` (geçiş beyanı) |

**Aile güvenlik testleri — F0-9 ekleri.** Tanımları §4 ve §13'tedir (D46-D53); kapıları §14'tedir. Dosyaları
iskeletin test dosyalarıdır (§12.B):

| Test | Neyi sabitler | Bulgu | Kapı |
|---|---|---|---|
| `test_yonetici_olmayan_hesapla_geri_yukle_reddedilir[uygulama_ici, konsol]` | `--geri-yukle` ve uygulama içi geri yükleme yalnız `yonetici` (§4.4.4) | GA-3 | F1b |
| `test_iki_depo_dort_hali[giris, acma_yarida, kapama_yarida, geri_yukleme_sonrasi]` · `test_hesap_muhru_bozulunca_giris_reddedilir_satir_degismez` | `guvenlik.json` ↔ `Account` tutarlılığı ve mühür (§4.6.1) | GA-10, GA-11 | F1b |
| `test_denetim_izinde_uydurma_kisisel_veri_yok` · `test_arsiv_dokumunde_uydurma_kisisel_veri_yok` | Uydurma veli adı, telefon ve T.C. kimlik no iz satırlarında ve `02-defterler/` dökümünde geçmez (§4.6.2) | KM-2 | F1b, F4 |
| `test_kilitliyken_gun_isi_is_verisi_yazmaz` · `test_sema_gocu_olayi_kilitli_kipte_muhurlu` · `test_uzun_is_surerken_bosta_kilit_yok` | Kilitliyken yazım kümesi ve uzun iş sayacı (§4.6.3, §4.4.3) | UY-1 | F1b |
| `test_capa_ve_kuyruk_kesme_uyarisi` · `test_from_db_value_kati_kip` | Çapa, kuyruk kesmenin görünmesi, çözülemeyen şifreli alanın `CorruptField` olması (§4.6.3; D48) | GA-9 | F1b |
| `test_is_surerken_carpi_kapanisi_bekler` · `test_is_oldurulunce_temiz_kapanis_isareti_yok` | Uçuştaki iş kapısı (§4.2) | GA-13 | F1b |
| `test_url_fetcher_ag_tuzagi` | WeasyPrint yalnız `data:` ve paket içi `file:` okur; `http(s)` isteği tuzağa düşer (D47) | GA-22 | F1a-2 |
| `test_allowed_hosts_kosulu` | `backend` adı yalnız belirteç boşken eklenir (D46) | GA-21 | F1a-2 |
| `test_od_update_repository_paketli_yapida_okunmaz` | Güncelleme deposu ortam değişkeni `sys.frozen` iken okunmaz (D51) | GA-14 | F1a-2 |
| `test_linux_dizin_ve_dosya_kipleri` | Dizinler 0700, gizli dosyalar 0600, `umask 077` (D52) | GA-20 | F1a-2 |
| `kilit.test.ts` (Vitest): kilitlenmede ve kilit açılışında sorgu önbelleği ve modül belleği sıfırlanır | Önceki hesabın verisi sonrakine kalmaz (§4.4.3; D53) | GA-23 | F1b |
| `test_rol_matrisi_hucre_anlik_goruntusu` · `test_rol_matrisi_dipnot_servis_testi[1-10]` | Matristeki her (rol, satır, Y) hücresinin ucu ve her dipnotun servis kapısı (§4.4.2) | GA-18 | F1b |
| `test_rotasyon_onek_kumesi` · `test_her_onekte_15_gun_silme[gunluk, pre_parola, pre_anonim, pre_kapanis, pre_dek_yenileme, db_onceki]` · `test_kvkk_tetiginden_eski_pre_migrate_silinir` | Rotasyon bütün yerel önekleri kapsar; `pre-migrate` son 5'le tutulur, KVKK tetiğinden eskisi silinir (§4.4.7; D49) | GA-5 | F1b, F4 |
| `test_tam_yedekte_ekli_kayit_geri_yuklemeden_sonra_acilir` | Dışarı çıkan tam yedek ekleri ve üretilmiş evrakı taşır (§4.4.7; D49) | GA-1 | F1b |
| `--evrak-duman` paketli ikilide `Document()` | Paketli ikilide python-docx belge açar (§11) | UY-17 | F1a |
| `test_dek_yenileme_yarida_kesme_provasi` · `test_zarf_imha_tutanagi_yeni_yedek_dogrulanmadan_basilmaz` | DEK yenilemesinin her adımından sonra süreç öldürülür, veri, dosyalar ve zincir doğrulanır; imha tutanağı (§9.7) 7. adımdan önce basılmaz (§4.4.4; D3) | GA-12, GA-4 | F4 |

### 10.7 Akış, model ve KVKK kararları (F0-9 ekleri)

Kural paketinde kimliği olmayan ama F0-9 kararlarını sabitleyen testler (`ak`); kapı §14'teki fazdır. Kural testine
bağlı olanların adı §10.3'tedir, burada yalnız gönderme vardır.

| Kapı | Test | Neyi sabitler | Bulgu / karar |
|---|---|---|---|
| F1c | `ak::test_genel_kurulsuz_ayni_uyelik_iki_kez_reddedilir` · `ak::test_iptal_uyelik_tekil_kisita_girmez` | `OrganMembership`'in iki kısmi tekil kısıtı: genel kurul bağı boş iki aynı üyelik reddedilir; `IPTAL` olanlar kısıta girmez | UY-10 |
| F1c | `ak::test_devralinan_uyelik_aday_sarti_olmadan_secildi` · `ak::test_gecis_toplu_sayac_beyani_tek_gerekce` | Geçiş kurulumunda görevdeki kurul `DEVRALINAN` üyelikle `SECILDI` olur; geçmiş seçilme sayaçlarının toplu beyanı tek gerekçe üretir (§7.9) | SU-4, SU-3, R5 |
| F2 | `ev::test_veli_adli_belge_saklanmaz[E07, E08]` (§10.5) | Veli adı taşıyan belgenin dosyası ve içerik JSON'u yok; arşiv paketinde yok | KM-1, R9 |
| F2 | `ak::test_hazirlik_donemi_gk_planlaninca_acilir` · `ak::test_ikinci_toplantida_secilen_kurulla_donem_acik` · `ak::test_gk_iptalinde_hazirlik_donemi_iptal` | Yeni `OabTerm` genel kurul planlanınca `HAZIRLIK`; tutanak tamamlanınca (ikinci toplantıda da) `ACIK`; genel kurul `IPTAL` olursa hazırlık dönemi de `IPTAL` | UY-5, R12 |
| F2 | `gk::test_olaganustu_gundem_disi_madde_gerekceyle_kaydedilir` (§10.3) | Olağanüstü genel kurulda gündem dışı madde uyarı + gerekçe, engel değil | B-13 |
| F3 | `ak::test_banka_ozeti_geri_al_yeniden_aktar_ayni_satir_sayisi` | İçe aktar → geri al → yeniden aktar aynı hareketleri verir, parmak izi çift kayıt üretmez | UY-6 |
| F3 | `ak::test_makbuzlu_kesin_gelirin_ters_kaydi_ayni_yapraga_yeniden_baglanir` · `ak::test_yaprak_kullanildidan_iptale_bagli_kaydi_zorlar` | Makbuzlu `KESIN` gelirin ters kaydında eski bağ `COZULDU` olur, düzeltilmiş kayıt aynı yaprağa yeni bağla bağlanır; yaprak `KULLANILDI → IPTAL` olunca bağlı kayıt `TASLAK` ise `IPTAL`, `KESIN` ise ters kayda zorlanır | UY-7 |
| F3 | `ak::test_toplu_deftere_gecirme_sayfa_numaralari` | `MarkBatch(DEFTERE_GECIRME)` E17 baskısının ilk ve son sayfa no'sunu `lines_per_page`'e göre doğru yazar | SU-7 |
| F3 | `ak::test_defterde_sakat_karar_hicbir_akisa_baglanamaz` | `DEFTERDE_SAKAT` karar harcama, kiralama ya da üyelik akışına bağlanamaz; DK listesinde ve kapanış denetiminde görünür | SU-11 |
| F3 | `ak::test_uyarili_taslak_kayit_gerekcesiz_kesin_gerekce_ister` | Uyarılı kayıt taslakta gerekçesiz yazılır, `KESIN`'e geçişte gerekçe ister (eksik ≠ sapma) | SU-3, R5 |
| F3 | `ak::test_mali_kaydi_yalniz_muhasip_yazar[gelir_gider, banka_eslesme, makbuz_yapragi, kasa, emanet]` · `ak::test_yonetici_yalniz_tefbis_isareti_koyar` | Mali kayıt yalnız `muhasip`; `yonetici` mali kayıt yazamaz, yalnız "TEFBİS'e girildi" işaretini koyar | D2 |
| F3 | `ak::test_baslama_gunu_acilisli_donemde_bakiye_tutar` | Programa başlama günü açılışlı dönemde açılış + hareketler = banka ve kasa bakiyesi; geriye dönük kayıtlarda toplu işaret (§7.9) | SU-4 |
| F4 | `ak::test_kapanista_kvkk_silmeleri[veli_adi, istekli_iletisim, tckn, bagsiz_kisi, personel]` · `ak::test_arsiv_paketinde_sureli_kisisel_alan_yok` · `ak::test_arsiv_paketi_silmelerden_sonra_uretilir` | Kapanıştan sonra veritabanında ve arşiv paketinde süreli kişisel veri yok; paket silmelerden sonra üretilir (yedek tarafı §10.6 GA-5) | KM-5, KM-12 |
| F4 | `ak::test_on_iki_aylik_hizmet_alimi_tek_surekli_odeme_dosyasi` · `ak::test_iki_taksitli_ve_kasadan_odeme_odendi` | Sürekli ödeme tek dosyada çok fatura; iki ödemeli ve kasa yolundaki fatura `ODENDI` olur (E27 kasa çıkış bölümüyle) | SU-2, UY-9, R6 |
| F4 | `ak::test_teslimden_sonraki_kayit_sonraki_bildirimin_gec_kayitlarinda` | E31 teslim edildikten sonra girilen eski tarihli kayıt bir sonraki E31'in "geç kayıtlar" bölümünde | SU-8 |
| F4 | `ak::test_kapanmis_donemde_isaret_konur_tutar_degismez_yeniden_basim_olur` | Kapanmış dönemde yalnız işaret alanları ve yeniden basım kaydı yazılır, denetim izine düşer | UY-4, R12 |
| F5 | `kn::test_imzasiz_sozlesmede_teslim_gerekceyle_kaydedilir` · `kn::test_onay_kaydi_yoksa_kesinlestirme_gerekceyle_gecer` (§10.3) | Yer teslimi imzadan önceyse uyarı; kantinde onaysız kesinleşme uyarı + gerekçe | MB-6, D4 |
| F5 | `ev::test_e42_il_merkezi_ozel_sart_pay_notu` (§10.5) | İl merkezi sözleşmesinde özel şart pay notu | MB-9 |
| F5 | `ak::test_kesin_teminat_akibeti[gelir_kaydi_22_4, mahsup_ve_iade_odememe, iade_olagan_sona_erme]` · `ak::test_teminat_akibeti_belirsiz_fesihte_gerekce_ister` | Kesin teminatın üç yolu (§5.2.5): md. 22/4 feshinde `EMANET` karşı hesaplı gelir kaydı; ödememe feshinde birlik alacağı kadar mahsup, kalan iade; olağan sona ermede iade. md. 22/1 ve EK-2 md. 15 fesihlerinde yol kullanıcıca seçilir, uyarı + gerekçe (varsayılan) | MB-7 |
| F6 | `sv::test_olursuz_kesinlestirme_sert` · `sv::test_tasimaci_ilani_unvan_plaka_guzergah` (§10.3) · `ev::test_e56_yalniz_unvan_plaka_guzergah` (§10.5) | Serviste onaysız kesinleşme sert; taşımacı ilanında yalnız ad/unvan, plaka, güzergâh | D4, D5 |
| F6 | `sv::test_dosya_iade_talebi_gelen_evrak_ve_bilgi_notu` (§10.3, kural olmayan karar) | İstekli dosyasını geri isterse talep gelen evrak olarak kaydedilir, U-E md. 7/2 bilgi notu; "geri verildi" durumu yok | MB-6 |

---

## 11. Bağımlılık kesim listesi

*Her Python bağımlılığı değişikliği **dört halkaya ve lisans kümesine birlikte** işlenir; plan §2.1-2'deki "üç yer"
ifadesi bununla düzeltilir (§13 D28). Halkaların ayrıntısı: [iskelet envanteri §5.2](../kesif/2026-10-31-iskelet-envanteri.md).
OYS kodunun çekirdek bağları (`linked_user`, `shared.roles`, `core`, `denetim`, `bildirim`, `bordro`, Celery) bu
bölümde değil §12.A'da kesilir.*

| Halka | Yer | Denetleyen |
|---|---|---|
| 1 | `backend/requirements.txt` (pin) | — |
| 2 | `packaging/tests/test_spec_kapsami.py::DAGITIM_IMPORT_ESLEME` | Eşlemesiz pin testi kırar |
| 3 | spec `hiddenimports` (`collect_submodules`) | Aynı test, statik |
| 4 | `packaging/pyinstaller/giris.py::RUNTIME_MODULES` | Küme eşitliği testi; paketli ikilide `--bagimlilik-duman` |
| Lisans | `bash packaging/lisanslar/uret.sh` → `THIRD_PARTY_LICENSES/` + `test_lisans_kapisi.BEKLENEN_PYTHON_KUMELERI` (Windows, Linux) + `lisanslar.py kisitlar` + derlemede `lisanslar.py paket` | Kapı testi; GPL'li bileşende derleme durur |
| Masaüstü | `requirements-paketleme.txt` (win32) ↔ `PAKETLEME_IMPORT_ESLEME` ↔ spec Windows bloğu ↔ `DESKTOP_RUNTIME_MODULES` | `test_masaustu_modulleri_*` |
| Linux Qt | `QtPy` + `PySide6` (linux) ↔ spec `WITH_QT` bloğu ↔ `LINUX_DUMAN_DISI` ↔ `build.sh` 4b | Test + derleme |
| npm | `package.json` ↔ `on_yuz_paketleri.mjs` ↔ `lisanslar.py npm-denetle` | `gates.sh` |

### 11.1 Python çalışma zamanı

| # | Paket | Aile pini | Karar | Kullanım | Faz |
|---|---|---|---|---|---|
| B1 | Django · djangorestframework | 5.1.15 · 3.15.2 | KALIR | Çekirdek | — |
| B2 | argon2-cffi · cryptography | 23.1.0 · 48.0.1 | KALIR | Parola türetme, Fernet, HKDF, X25519, AES-GCM; dosya deposu şifrelemesi de (`AESGCM`, §4.4.4) — yeni paket gerekmez | — |
| B3 | openpyxl | 3.1.5 | KALIR | Banka özeti, TEFBİS Excel, çıktılar (TK18) | — |
| B4 | xlrd | 2.0.1 | KALIR | e-Okul `.xls` — personel ve veli listesi (T5) | — |
| B5 | Pillow | 12.3.0 | KALIR | WeasyPrint bağımlılığı, ikon üreteçleri | — |
| B6 | weasyprint | 68.0 | KALIR | PDF çizicisi (T2); yalnız `data:` ve paket içi `file:` kaynağı açan `url_fetcher`'la çağrılır (§4.1) | — |
| B7 | pypdf | 6.14.2 | KALIR | `--pdf-duman`; PDF ↔ Word içerik eşdeğerliği testi | — |
| B8 | whitenoise · waitress | 6.12.0 · 3.0.2 | KALIR | SPA servisi, WSGI | — |
| B9 | segno | 1.6.1 | **ÇIKAR** | Etiket ve Ağ Doktoru QR'ı. Dört halka + lisans + `test_bagimlilik_duman_gercek_listeyle…` (segno'yu adıyla sınar, §13 D8) | F1a-2 |
| B10 | python-docx | — | **EKLENİR** (sürüm F1a-3 ilk kanıtında pinlenir; yerelde denetlenen 1.2.0) | Word çizicisi (T2). Spec `collect_submodules("docx")` + **`collect_data_files("docx")` zorunlu**: `Document()` varsayılan şablonu paket dizininden dosya yoluyla okur (`docx/api.py`, `templates/default.docx`); eksik kalırsa `--evrak-duman` paketli ikilide düşer. `--evrak-duman` paketli ikilide `Document()` ile boş belge açmayı da sınar. Eşleme `"python-docx": "docx"` | F1a-3 |
| B11 | lxml | — | **EKLENİR** (doğrudan pin) | python-docx'in geçişlisi; pin, kısıt dosyası ve lisans kümesinin sürümü bağlasın; eşleme `"lxml": "lxml"` | F1a-3 |
| B12 | typing_extensions | aile kümesinde var (pywebview zinciri) | **Doğrudan pinlenir** | python-docx modül düzeyinde içe aktarır (`docx/blkcntnr.py`; `Requires-Dist: typing_extensions>=4.9.0`); "gelebilir" değil kesin gelir. Yeni olan backend çalışma zamanının ona doğrudan bağlanmasıdır: `requirements.txt` pini, eşleme ve `RUNTIME_MODULES`. python-docx'in öteki geçişlileri F1a-3'te çözülmüş kurulumdan çıkarılır | F1a-3 |
| B13 | python-magic (libmagic) | — | **EKLENMEZ** | OYS `file_storage`'ın MIME denetimi; Windows'ta ayrı DLL ister (S-26). İmza baytı denetimi yeter (TK18) | — |
| B14 | Celery, drf-spectacular, JWT altyapısı | — | **EKLENMEZ** | OYS bağları; karşılıkları gün değişimi kapısı ve oturum belirteci (§12.A) | — |
| B15 | defusedxml | — | **ADAY** | openpyxl belgesinin XML saldırıları için önerdiği paket (doğrulanmadı); içe aktarım tasarımıyla karar | F1b |
| B20 | pyzipper | — | **ADAY** | Yıl sonu arşiv paketinin AES-256 şifreli ZIP'i (§8.5, §15 B-10). Geçişli bağımlılığı (pycryptodomex olduğu biliniyor; tam liste ve lisansları doğrulanmadı) F4 başında çözülmüş kurulumdan çıkarılıp pinlenir; dört halka ve lisans kapısı aynı değişiklikte. Uygun lisans çıkmazsa seçenek F4 planında yeniden tartılır | F4 |

*B20 numarası, B16-B19'un §11.2'de kullanıldığı için verildi.*

### 11.2 Paketleme

| # | Paket | Pin | Karar | Not | Faz |
|---|---|---|---|---|---|
| B16 | pyinstaller | 6.11.1 | KALIR | | — |
| B17 | pywebview · pythonnet (win32) | 5.3.2 · 3.0.5 | KALIR | `clr`, `DESKTOP_RUNTIME_MODULES`'ta kalır | — |
| B18 | pystray · six (win32) | 0.19.5 · 1.17.0 | **ÇIKAR** | Tepsi. `PAKETLEME_IMPORT_ESLEME`, spec Windows bloğu + `module_collection_mode`, `DESKTOP_RUNTIME_MODULES`, lisans kümesi ve pystray/six platform sınamaları, `lisanslar.py` (pystray kaynağı ve LGPL yazılı teklifi), NOTLAR W13/W20/W22. Yalnız tepsi simgesi için toplanan `PIL.ImageDraw`, `PIL.IcoImagePlugin` başka kullanıcısı yoksa çıkar (doğrulanmadı) | F1a-2 |
| B19 | QtPy · PySide6 (linux) | 2.4.3 · 6.8.3 | KALIR | 6.9.1+ Pardus 21'de açılmaz (TB27); yükseltmeden önce `gbm_bo_get_fd_for_plane` sembol denetimi | — |

### 11.3 Ön yüz, sistem, kap

- **npm:** F1a'da paket eklenmez, çıkarılmaz. ALMA modülleri (159 dosya) sökülünce yalnız onların kullandığı
  paketler Vite çıktısından kendiliğinden düşer; `on_yuz_paketleri.mjs` + `npm-denetle` bunu gösterir (hangi
  paketin düşeceği doğrulanmadı). Kullanılmayan paket `package.json`'dan F1a-2'de temizlenir.
- **`.deb` `Depends`:** değişmez; Debian 13'te 64 bit zaman geçişiyle değişen adlar (`libasound2t64`,
  `libglib2.0-0t64` gibi) `apt-get -f install` ile çözülüyor mu, prova gösterir (doğrulanmadı; §13 D17).
- **Docker imajı:** Python 3.12-slim + WeasyPrint sistem kitaplıkları + DejaVu; **LibreOffice girmez** (T2). Son
  satırdaki `runserver 0.0.0.0:8000` silinir (§13 D12).
- **Windows:** WebView2 önyükleyicisi ve MSYS2 DLL kapanışı aynen; yeni DLL yok (B13).
- **Font:** DejaVu paket içindedir (`--pdf-duman` arar). Word çıktısında yazı tipi adı verilir, gömülmez; Windows ve
  Pardus eşlemesi ve gömülüp gömülmeyeceği §9.1'deki evrak kararıdır ([iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md)
  §11-5 açık sorusu; F1a-3'ün ilk kanıtından önce).

### 11.4 Lisans kümesi

| Yön | Bileşen | Lisans | Not |
|---|---|---|---|
| Çıkan | segno | BSD | |
| Çıkan | pystray · six | LGPLv3 · MIT | pystray'in kaynak kodu ve yazılı teklif yükümlülüğü de kalkar |
| Giren | python-docx | MIT | |
| Giren | lxml | BSD-3 | Windows tekerleği libxml2/libxslt'yi gömülü taşır; bildirimlerini `uret.sh` toplar mı — doğrulanmadı |
| Kalan | typing_extensions | PSF | Aile kümesinde pywebview zinciriyle zaten var; artık backend çalışma zamanında da (B12) |
| Giren (aday) | pyzipper + geçişlileri | doğrulanmadı | B20; F4'te kesinleşir |
| Kalan denetim | Qt (PySide6) | LGPLv3 | Yalnız GPL'li Qt modülleri pakete girmez; `lisanslar.py paket` GPL'de durur — PolyForm NC (K7) ile uyumun dayanağı |

`THIRD_PARTY_LICENSES/` elle düzenlenmez: F1a-2 sonunda `uret.sh` ile yeniden üretilir (Docker + ağ ister; F1a
kapısının ağa bağlı tek adımı). TB28'in iki işi (MSYS2 kaynak arşivi, Qt bildirim metni) F7 paketlemesinden önce kapanır.

---

## 12. Çıkarım haritası

Ne alınır, ne uyarlanır, ne bırakılır: iş mantığı OYS'den (§12.A), iskelet Kütüphane Defteri'nden (§12.B). Haritaya uymayan "iyileştirme" yapılmaz (CLAUDE.md §1).

### 12.A OYS okul_aile_birligi modülü

Kaynak: [OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) (OYS `origin/main` 8e1687c5). Bu bölüm envanterin
sınıflamasını model ve servis düzeyinde **kesinleştirir**; envanterden ayrılan satırlar "Sapma" sütununda yazılıdır.
Yerine gelen yeni modeller §5.2'dedir. Sınıfların anlamı envanterdeki gibidir (AYNEN: yalnız mekanik değişiklik ·
UYARLA: mantık alınır, değişiklik yazılır · ALMA).

**Ortak mekanik değişiklikler** (her AYNEN ve UYARLA satırında): `core.*` ve `shared.*` bağları ailenin karşılığına
(`okul.*`, ailenin şifreli alanı, ailenin denetim izi — §4.6); `BaseModel.deleted_at` yerine `IPTAL`/`PASIF` durumu
(O1); `created_by` → `Account` (§4.6); göç ağacı `0001`'den; fabrikalar `SchoolYearFactory` yerine yerel fabrikadan;
gerçek firma adı geçen test ve yorumlar uydurma adla yeniden yazılır (envanter S-21).

**Modeller (29)**

| OYS modeli | Kesin sınıf | OAB Defteri'nde | Sapma |
|---|---|---|---|
| `OabPerson` | UYARLA | `OabPerson` — K9, telefon kalkar, ad şifreli, yaş beyanı, geçmiş sayaçlar (geçişte toplu beyan) | — |
| `OabTerm` | UYARLA | `OabTerm` — hazırlık durumu (genel kurul planlanınca açılır), kilit, kural bağı, geçiş kurulumu alanları | — |
| `OrganMembership` | UYARLA | `OrganMembership` — organ ve temsil türleri, oy, yedek çağırma, devralınan üyelik, iptal; `NITELIK_KAYBI` → `DIGER`; boş genel kurullu iki kısmi tekil kısıt | — |
| `GeneralAssembly` | UYARLA | `GeneralAssembly` — sabit taban, iki toplantı tek kayıtta (olağanüstüde de), ibra, katılım dağılımı, açılacak dönem bağı; `AttendanceCorrection` (YENİ) | `follows_failed_assembly` kalkar |
| `AgendaItem` | **UYARLA** | `AgendaItem` — tür, sonuç, oylar, oyla çıkarma | Envanterde AYNEN |
| `AssemblyMinutes` | UYARLA | `AssemblyMinutes` — kişi bağları | — |
| `BoardMeeting` | UYARLA | `BoardMeeting` — durum, yeter sayı, katılım tamlığı | — |
| `BoardMeetingAttendance` | AYNEN | `BoardMeetingAttendance` | — |
| `BoardDecision` | UYARLA | `BoardDecision` — defter, sıra no, sayfa, oylar, durum, defterde sakat karar izi | — |
| `AuditReport` | UYARLA | `AuditReport` — liste tazelenir, DK yazar, md. 6 aykırılık alanı (md. 14/5 önerisi buna bağlı) | — |
| `BudgetCategory` | UYARLA | `BudgetCategory` — TEFBİS tohumu, dosya bayrağı | — |
| `OabBudget` | UYARLA | `OabBudget` — devir `OpeningBalance`'a, "görüşüldü", iptal, hazırlık dönemine yazılır | — |
| `BudgetLine` | UYARLA | `BudgetLine` — gerçekleşen hesaplanır, iptal işareti | — |
| `ComplianceEntry` | UYARLA | `ComplianceItem` (yeniden adlandırma; sapma, eksik ve takvim türleri) + `ComplianceJustification` (toplu gerekçe), `Announcement`, `MonthlyReport`, `ShareStatement`, TEFBİS mutabakatı | Ad değişti; sapma ve eksik kayıtları da buraya (O3) |
| `ReceiptBookRegistry` | UYARLA | `ReceiptBookRegistry` (tasdik alanları) + `ReceiptLeaf` + `LeafUse` (YENİ) | — |
| `IndexRate` | AYNEN | `IndexRate` (değer anlamı sabitlenir) | — |
| `TefbisImport` | ALMA | `TefbisStatement`, `TefbisStatementLine` (YENİ) | — |
| `RentableAsset` | UYARLA | `RentableAsset` | — |
| `Tender` | UYARLA | `Tender` — iki süreç, `winner` yerine `Bidder.selected`; onaysız kesinleşme serviste sert, kantinde uyarı (D4) | — |
| `TenderCommissionMember` | UYARLA | oy ve muhalif şerhi | — |
| `TenderApproval` | UYARLA | servis mülki amir; kantin makamı elle | — |
| `Bidder` | UYARLA | tek açık katılım engeli alanı, dayanağı şifreli; kapalı listeli eleme nedeni; `person` FK kalkar | — |
| `BidderDocument` | UYARLA | özne (kiracı dâhil), geçerlilik, dosya `Attachment`'a | — |
| `ScoringCriterion` | AYNEN | tohum kural paketine | — |
| `BidderScore` | AYNEN | — | — |
| `OabContract` | UYARLA | EK-2 alanları, 20 yıl hesabı, çoklu sözleşme, iptal, teminatın akıbeti, özel şart | — |
| `ContractInstallment` | UYARLA | Kantin aylık kira ve pay takvimi; serviste üretilmez | Servis kullanımı ALMA |
| `ShareStatement` | UYARLA | yerleşim türü, iki vade, yer alanlı tekil kısıt | — |
| `InspectionRecord` | AYNEN | yardım metni düzeltilir | — |

Sayım: **AYNEN 5** (`BoardMeetingAttendance`, `IndexRate`, `ScoringCriterion`, `BidderScore`, `InspectionRecord`) ·
**UYARLA 23** · **ALMA 1** (`TefbisImport`). Enum değişiklikleri envanter §2.3'teki gibidir; ek olarak `OrganType`'a
`DIVAN`, `ALIM_KOMISYONU`, `TEMSILCI` girer, `ComplianceKind` `ComplianceItem.obligation`'a dönüşür. OYS'de karşılığı
olmayan yeni modeller (`LedgerEntry`, `ExpenseFile`, `ExpenseInvoice`, `MarkBatch`, `LeafUse`,
`ComplianceJustification`, `AttendanceCorrection` ve ötekiler) §5.2'dedir.

**Servisler (`services.py`)**

| Fonksiyon | Kesin sınıf | Not | Sapma |
|---|---|---|---|
| `_q` | AYNEN | Kuruş yuvarlama | — |
| `create_term`, `update_term` | UYARLA | Ders yılı `okul`'dan; hazırlık durumu; kilit; kural bağı; geçiş kurulumu (§7.9) | — |
| `create_person`, `update_person` | UYARLA | K9; telefon yok; ad şifreli; `linked_user` yok | — |
| `compute_assembly_quorum` | UYARLA | Taban kural paketinden 16; olağanüstüde de çarpan | — |
| `schedule_general_assembly` | UYARLA | 15 gün, 30 gün (olağanüstüde de), Ekim sonu, çağıran ve neden, anlık mevcut, hazırlık döneminin açılması | — |
| `create_default_agenda` | AYNEN | Mantık aynı; tohum içeriği [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) maddeleriyle tazelenir (veri) | — |
| `record_assembly_outcome` | UYARLA | İki toplantı, ibra, katılım dağılımı, hazırlık döneminin açık olması | — |
| `set_assembly_minutes` | UYARLA | Kişi bağı; divan uyarısı | — |
| `validate_membership_composition` | UYARLA | Koltuk uygunluğu sert, sayılar uyarı; müdür yasağı; DK'de hayırsever yok | — |
| `count_prior_baskan_terms`, `promote_membership` | UYARLA | [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) başkan ve üyeler; geçmiş sayaçlar | — |
| `drop_membership` | UYARLA | `drop_kind` (`NITELIK_KAYBI` yok); [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) istisnası; yedek çağırma önerisi; hesap kapanışı öneri | — |
| `assign_membership` | UYARLA | Beyan yalnız tarih (okul uygulaması); devralınan üyelik | — |
| `record_board_meeting` | UYARLA | Yeter sayı 4, katılım tamlığı | — |
| `record_attendance`, `_maybe_auto_drop_for_absences` | **UYARLA** | Sayım toplantı üzerinden (kayıt değil, S-19); düşme öneri + onay | Envanterde AYNEN; üç devamsızlık testi UYARLA'ya geçer (§10.4) |
| `record_board_decision` | UYARLA | Durumlar, defter alanları, oy yeter sayısı, defterde sakat karar | — |
| `create_audit_report` / `update_audit_report` | UYARLA / **UYARLA** | Liste tazelenir / bayrak mantığı aynen, md. 6 aykırılık alanı eklenir; md. 14/5 önerisi yalnız o alana bağlı (denetim MB-10) | `update_audit_report` envanterde AYNEN |
| `ensure_default_budget_categories`, `create_budget`, `set_budget_line` | UYARLA | K1; TEFBİS tohumu; iptal | — |
| `_iter_year_months`, `suggest_personnel_realized_for_term`, `apply_personnel_realized` | ALMA | K3 | — |
| `BudgetFinancialSummary`, `budget_financial_summary` | UYARLA | Kayıtlardan; `OpeningBalance` | — |
| `record_compliance`, `mark_compliance_done` | UYARLA | `ComplianceItem` takvim türü; kanıt | — |
| `create_index_rate` | AYNEN | — | — |
| `create_receipt_book` | UYARLA | Seri-cilt-sıra, yapraklar, karar bağı, tasdik alanları | — |
| `_persist_tender_warnings`, `set_commission` | AYNEN (desen) | Uyarı + gerekçe deseni; yazdığı yer `ComplianceItem` (sapma ya da eksik, O3) | Hedef tablo değişir (mekanik) |
| `ensure_ek3_scoring_criteria` | UYARLA | Tohum kural paketinden | — |
| `create_rentable_asset`, `set_estimated_price` | AYNEN | — | — |
| `create_tender` | UYARLA | İki süreç; servis varsayılanı komisyon değerlendirmesi | — |
| `validate_commission` | UYARLA | Bileşimler kural paketinden; servis yedekleri | — |
| `register_bidder` | UYARLA | Gerçek kişide vergi no yok | — |
| `check_bidder_eligibility` | UYARLA | Katılım engeli (suç [md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), hısımlık [md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) tek açık alanda sert, dayanak şifreli; belge uyarı | — |
| `score_bidder`, `compute_bidder_total` | **UYARLA** / AYNEN | Kademe dışı puan sert değil uyarı (plan §1.8) / toplam aynen | Envanterde ikisi de AYNEN |
| `determine_winner` | UYARLA | En düşük teklif çıkar; çoklu seçim | — |
| `record_approval`, `finalize_tender` | UYARLA | OLUR serviste sert, kantinde uyarı + gerekçe (D4); 5 iş günü; 7 gün ilan ilan anında | — |
| `add_bidder_document` | UYARLA | `Attachment`; varsayılan tarama yok; kiracı öznesi | — |
| `create_contract` | UYARLA | EK-2, 20 yıl hesabı, takvimle yıl, durumlar, teminatın akıbeti, il merkezi pay notu (özel şart) | — |
| `add_installments` | UYARLA | Kantin aylık kira takvimi (taksit sınırı yok); serviste taksit kaydı üretilmez, yalnız `OabContract.fee_installments_max` bilgisi (> 9 uyarı, `servis.taksit_en_fazla`; KE-14) | — |
| `_share_due_date`, `record_share_statement`, `mark_share_paid` | UYARLA | İki vade; yerleşim türü; gecikme zammı hesaplanmaz | — |
| `apply_tufe_increase` | UYARLA | Yıl dönümü; on iki aylık ortalama; öneri ve sapma uyarısı (D1); bildirim | — |
| `record_inspection` | AYNEN | — | — |
| `oab_reminder_recipients`, `_emit_membership_dropped` | ALMA | Pano ve takvim (§7.10) | — |
| `get_disbursement_signatories` | UYARLA | Ödeme talimatının imza bloğu ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) | — |

**Diğer bileşenler**

| Bileşen | Kesin sınıf | Not |
|---|---|---|
| `selectors.py` tek kaynak listeleri (`organ_members`, `elected_roster`, `candidate_roster`, `agenda_items`, `list_memberships`) | AYNEN | Evrakın tutarlılık dayanağı |
| `selectors.py` getiriciler, liste uçları, vade taramaları | UYARLA | Model değişikliklerine göre; vade taramaları panonun kaynağıdır (§7.10); PII'siz liste deseni korunur |
| `selectors.latest_index_rate` | AYNEN | — |
| `permissions.py` | ALMA | K2 rol matrisi (§4.4.2); "okuma ≠ yönetme ≠ hassas detay" ayrımı ve hassas okuma günlüğü deseni korunur |
| `signals.py`, `events.md`, `tasks.py` | ALMA | Pano ve takvim (§7.10); "bildirimde kişi adı yok" ilkesi pano metinlerinde AYNEN |
| `documents.py` (`render_*`, `build_imza_surkusu_xlsx`) | UYARLA | Tek içerik, iki çizici (T2); imza blokları Yönetmeliğe göre (S-9); ayrıntı §9 |
| `documents._ihale_commission` | AYNEN | Başkan başta sıralama |
| `file_storage.py` | UYARLA | `Attachment`; sha256, uuid adı, boyut sınırı AYNEN; libmagic ve yalnız-PDF kalkar, dosya şifrelenir |
| `views.py`, `serializers.py`, `urls.py` | UYARLA | İnce görünüm deseni; liste/detay ayrımı; rol katmanı ve günlük ailenin |
| `admin.py`, `migrations/`, `apps.py` | ALMA | Masaüstünde admin yok; şema sıfırdan |
| `templates/.../documents/` (21) | UYARLA | §9 evrak kataloğunda dosya dosya |
| Ön yüz `modules/okul-aile-birligi/` (envanter S-27) | ALMA | Envanterlenmedi (OYS bu cihazda arka uç olarak alındı). Ekranlar ailenin ön yüz kitiyle (Kütüphane Defteri `frontend/`, §12.B) yeniden yazılır; F1c ekranları (birlik dönemi, organlar, temsilciler, geçiş kurulumu adımları, pano kabuğu) yenidir, akış ve alan sözlüğü §5 ve §7'dendir. Bir fazda OYS'nin ekran akışına bakmak gerekirse okuma o fazın başında `okulapp` `origin/main`'den yapılır |
| Testler (373) | Envanter §6.1: AYNEN 69 · UYARLA 277 · ALMA 27 (başlangıç). **71 kural testinin kesin sınıfı §10.4'tedir; tek kaynak odur** | Envanterden §10.4'e geçişte sınıfı değişen 16 test (envanterin dosya sayılarından ve gerekçe sütunundan test başına çıkarımla): **AYNEN → UYARLA 14** — `test_assembly` :: `…_ikinci_toplanti_baglantisi`; `test_bidder` :: `servis_hisimlik_engeli_uygulanmaz`, `kiralama_belge_eksik_engeli`; `test_board` :: `ust_uste_3_mazeretsiz_devamsizlik_dusurur`, `mazeretli_devamsizlik_dusurmez`, `araya_bir_katilim_girerse_seri_bozulur`; `test_contract` :: `create_contract_servis_sure_uyarisi`, `add_installments_9_gecer_10_engel`, `add_installments_yariyil_atlar`; `test_models` :: `membership_ayni_kisi_farkli_organda_serbesttir`; `test_scoring` :: `puan_azamiyi_asamaz_sert_engel`, `ikili_kriter_yalniz_0_veya_max` (D1, MA-5: kademe dışı puan uyarı); `test_tender` :: `red_ihaleyi_iptal_eder`; `test_tufe` :: `ilk_yil_artis_yok` · **UYARLA → AYNEN 1** — `test_board` :: `record_board_decision_taslak_varsayilan` · **UYARLA → ALMA 1** — `test_share` :: `gecikme_zammi` (6183 korpusta yok; yerine "hesaplanmaz" testi). İki puanlama testi (`test_bidder` :: `puanlama_*`) envanterde zaten UYARLA'dır. Sonuç: **AYNEN 56 · UYARLA 289 · ALMA 28 = 373**. Kesin sayım F2-F6'da test taşınırken test başına sınıf yazılan listeyle doğrulanır; envanterden sapan her test §10.4'ün sapma listesine girer |

### 12.B İskelet (Kütüphane Defteri)

*Kaynak 9a3829d. Dosya dosya gözlem [iskelet envanteri §2-§3](../kesif/2026-10-31-iskelet-envanteri.md)'tedir; burada
karar biçimi. Zaman: **F1a-1** ham kopya + kimlik çevirisi · **F1a-2** arındırma · **F1a-3** evrak hattının ilk kanıtı · **F1b**
güvenlik çekirdeği ve roller · **F1c** organ bağı · **sonra** ilgili faz.*

**F1a-1 ara commit'i kapısızdır** (karar): `config/settings.py` (`INSTALLED_APPS`), `config/urls.py`, `desktop/main.py`
(katalog) ve ön yüz rotaları ALMA modüllerini içe aktarır; ham kopya tek başına çalışmaz. Commit iletisi bunu yazar;
kapı F1a-2 sonunda koşar. Gerekçe: kimlik çevirisini arındırmadan ayrı görmek gözden geçirmeyi kolaylaştırır;
dört bağı F1a-1'de kesmek iki işi karıştırırdı.

#### AYNEN (yalnız kimlik sabitleri çevrilir)

*Kullanıcıya görünen metni kütüphaneye özgü olan ya da davranışı OAB'de değişen dosya AYNEN sınıfına girmez; kalıntı
taraması bu metinleri yakalamaz (denetim GA-19). Bu yüzden `lock_middleware.py`, `recovery_key_document.py`,
`kurtarma_anahtari.html`, `shared/pdf.py`, `shared/crypto.py`, `desktop/paths.py` ve `encrypted_backup.py` UYARLA'ya
alındı.*

| Dizin | Dosyalar |
|---|---|
| `desktop/` | `dialogs.py`, `integrity.py`, `version.py`, `django_bootstrap.py` (WAL checkpoint, bilinmeyen göç denetimi), `logging_setup.py`, `session_guard.py`, `win32_objects.py`, `instance_channel.py`; ALMA ve UYARLA dışındaki testler |
| `packaging/` | `fontlar/`, `pyinstaller/fonts.conf.tmpl`, `fonts.paket.conf`, `linux/apt_dene.sh`, `docker-build.sh`, `postinst`, `prerm`, `windows/build.ps1`, `dll_kapanisi.py`, `paket_kapanisi.py`, `lisanslar/on_yuz_paketleri.mjs`, `uret.sh`; testler `test_apt_dene`, `test_betik_kodlamasi`, `test_paket_kapanisi`, `test_paketleme_tetigi` |
| `backend/` kök ve `shared/` | `conftest.py`, `manage.py`, `requirements-dev.txt`, `apps/__init__.py`, `config/wsgi.py`; `shared/models.py`, `text.py`, `working_days.py` |
| `backend/apps/okul/` | `name_match.py`, `normalize.py`, `views_calendar.py`, `views_yedek.py`, `services/calendar.py`, `dis_yedek.py`, `school_year.py`, `terms.py`; testlerin kütüphaneye bağlı olmayanları |
| `backend/templates/` | `BENIOKU.md`, `print/_design.css`, `documents/base.html` |
| `frontend/` | `src/ui/` (50; `BarcodeInput` hariç), `src/hooks/` (11; depo anahtarları §2.3), `src/test/setup.ts`, `kurulumDurumu.ts`, `modules/takvim`, `modules/guncelleme` ("iki kapı" yorumu tek kapıya) |
| kök | `.gitattributes` (OAB'deki bayt bayt aynı), `LICENSE` (OAB'de var, K7) |

#### UYARLA

| Yol | Değişiklik | Zaman |
|---|---|---|
| `VERSION` | Kopyalanmaz; OAB'nin ilk sürümü aile CalVer biçimiyle yazılır | F1a-1 |
| `SECURITY.md` | `.odbak`; "ağ kataloğu yüzeyi" çıkar; "ağ servisi sunmaz" cümlesi; iletişim satırı kalır | F1a-1 |
| `docker-compose.yml` | Proje adı; "yerel ağa katalog" yorumu → ağ servisi yok | F1a-1 |
| `.gitignore` | Birleştirme: sentetik e-Okul personel ve veli örneklerinin **adıyla** istisnası, `.od-depo-listesi.tmp`, `.od-yasakli-adlar.txt` (§13 D42), `.claude/settings.local.json`, evrak denemesi dizini; `*.docx`, `*.ods` (şablonlar adıyla istisna) | F1a-1 |
| `.github/ISSUE_TEMPLATE/`, `workflows/` | Depo adresi; `kapilar.yml` gecelik `KD_YAVAS` dalı çıkar; `paketleme.yml` Debian 13 matrisi, adlar; `r2-yukle.yml` önek | F1a-1, F1a-2 |
| `THIRD_PARTY_LICENSES/` | Elle değil, `uret.sh` ile yeniden üretilir (§11.4) | F1a-2 |
| `scripts/gates.sh` | 3. adım (yavaş testler + ağ provası) sökülür; geçici dosya adı | F1a-2 |
| `docker/backend.Dockerfile` | Son `runserver 0.0.0.0:8000` satırı silinir | F1a-1 |
| `desktop/__init__.py`, `server.py` | Belge dizeleri: katalog paragrafı → "ağ servisi sunmaz" | F1a-2 |
| `desktop/paths.py` | Linux'ta dizinler 0700 oluşturulur, var olanlar 0700'e çekilir; açılışta `umask 077`; test (§4.5, §13 D52) | F1a-2 |
| `desktop/backup.py` | `.odbak`; `encrypt_legacy_backups` ve düz `*.sqlite3` yedek kalıpları sökülür (OAB'de düz yedek hiç olmadı, §13 D29); yerel yedek = veritabanı + dosya manifestosu, tam yedek = + dosya bölümü (§4.4.7); önekler `pre-kapanis`, `pre-dek-yenileme`; `pre-anonim` F4'te; **`rotate_backups` önek kümesi genişler**: bütün yerel önekler ve `db-onceki-` 14 gün, `pre-migrate` son 5 + KVKK tetiğinden eskiler silinir; küme testle sabitlenir (§13 D49) | F1a-1, F1a-2, F1b, F4 |
| `desktop/backup_crypto.py` | Kimlik (F1a-1); kap `ODBAK\x03` (dosya bölümü, manifesto mühürlü bölümde); başlıkta kurtarma anahtarının no ve tarihi (TK10); `is_usable_security_state` şema 2'ye, `recovery_metadata` yalnız kurtarma bölümüne | F1a-1, F1b |
| `desktop/clean_shutdown.py` | İleti "son oturumdaki kayıtları kontrol edin"; `OD_ONCEKI_OTURUM`; işaret yalnız uzun iş sayacı sıfırken yazılır (§4.2) | F1a-1, F1b |
| `desktop/errors.py` | Başlıklar "OAB Defteri …"; 11 ayrılmış; 12 `--evrak-duman`; 9 "geri yükleme başarısız ya da yetkisiz" | F1a-2, F1a-3, F1b |
| `desktop/gunluk.py` | Uyku engelleme, IP işi, saatlik katalog denetimi sökülür; bakım kapısı `shared/bakim.py`'den, `ImportError` düşüşü kalkar (§13 D3); DEK isteyen iş kilitliyken "ertelendi" döner ve iz satırı kilitli kip anahtarıyla düşer (§4.6.3) | F1a-2, F1b |
| `desktop/lock.py`, `restore.py` | Mutex adları; "tepside" iletileri; `restore.py` `--hesap` + parola ya da kurtarma anahtarı; **rol denetimi**: parola yolunda güncel veritabanı salt okunur `sqlite3` ile (ORM yok), okunamazsa yedeğin görüntüsü bellekte okunur, `yonetici` doğrulanmazsa kenara alma yapılmadan çıkış 9; `geri-yukleme-notu.json` yazılır (§4.4.4) | F1a-2, F1b |
| `desktop/main.py` | Tepsi, katalog, `--tepside`, uyku, güvenlik duvarı yardımcı kipi, `encrypt_legacy_backups`, `--autotest` katalog adımı sökülür; Linux'ta `umask 077` ve `qt_kurulum.hazirla()`; `--evrak-duman`; kapanışta kilitleme ve çapa (§4.2) | F1a-2, F1a-3, F1b |
| `desktop/window.py` | T6 (§4.5): `tray_available`, `ask_quit_in_spa`, `kd:cik-iste`, gizleme sökülür; `show()` ve `request_quit()` kalır; `closing` işleyicisi yalnız uzun yazma işi sürerken kapanışı bir kez erteler (§4.2) | F1a-2, F1b |
| `desktop/tests/` | `test_main`, `test_window_controller`, `test_window_f5`, `test_restore`, `test_gunluk`, `test_acilista_dis_istek`, `test_geri_yukleme_provasi` + `prova_betigi.py`, `alt_surec.py`, `conftest.py`. **Taşınacak parçalar:** `test_katalog_server.py`'deki "yalnız 127.0.0.1" testleri → `test_server.py`; `test_main_f5.py`'deki WAL checkpoint ve kapanış sırası testleri → `test_main.py`; `test_tray.py`'deki Qt kurulum testleri → `test_qt_kurulum.py`. **Yeni testler:** Linux dizin ve dosya kipleri; iş sürerken çarpı; yönetici olmayan hesapla `--geri-yukle` reddi | F1a-2, F1b |
| `packaging/README.md`, `requirements-paketleme.txt`, `r2-yukle.sh` | pystray, segno, katalog paragrafları; `R2_ONEK` | F1a-2 |
| `packaging/ikonlar/` | Üreteçler (`logo_uret.py`, `ikon_uret.py`; elle çizilmiş 16/24/32, yedi kareli `.ico`) kalır, çizim ve adlar yeni | F1a-2 |
| `packaging/linux/` | `build.sh` (ufw/firewalld, katalog öz sınaması), `debian-control.tmpl` (`Description`), `kutuphane-defteri.desktop` → `oab-defteri.desktop`, `kur.sh`, `kaldir.sh`, `BENIOKU.txt`, `kap-ici-test.sh` ve `test-kurulum.sh` (`--dagitim-duman` çıkar, Debian 13, `--evrak-duman` girer) | F1a-2 |
| `packaging/lisanslar/lisanslar.py` | pystray kaynağı, segno, yazılı teklif kapsamı; `OD_WITH_QT`, `OD_DLL_DIR` | F1a-2 |
| `packaging/pyinstaller/` | `giris.py` (`RUNTIME_MODULES` — `docx`, `lxml`, `typing_extensions` girer —, `DESKTOP_RUNTIME_MODULES`, `--dagitim-duman` çıkar, `--evrak-duman` girer) · `kutuphane_defteri.spec` → `oab_defteri.spec` (`Tree(backend/katalog)`, segno, pystray çıkar; docx girer: `collect_submodules` + `collect_data_files`, §11 B10; Qt GPL ayıklaması, UCRT süzgeci, fontconfig kalır) · `rthook_kd.py` → `rthook_od.py` (UAC yardımcı kipi dalı sökülür) | F1a-1, F1a-2, F1a-3 |
| `packaging/windows/` | `kutuphane-defteri.iss` → `oab-defteri.iss` (T6, TK7: `lowest` + `dialog`, ortak hesapta yönetici kipi kılavuzda; katalog, güvenlik duvarı, otomatik başlatma, tepsi iletileri) · `NOTLAR.md` (W13-W20 düşer ya da değişir; "çarpıyla kapanır" elle doğrulama maddesi) | F1a-2 |
| `packaging/` sızıntı kapıları | `depo_sizintisi.py` (`.odbak`; `.docx`, `.ods`; **IBAN mod-97**; sınıf listesi muafiyeti → sentetik veli örneği; depo dışındaki yasaklı adlar listesi, §13 D42) · `veri_sizintisi.py` (uzantı kümesi eşitliği) | F1a-2, F6 |
| `packaging/tests/` | `test_kimlik_kalintisi` (§2.3.3), `test_lisans_kapisi`, `test_spec_kapsami`, `test_rthook`, `test_ikonlar` (`docs/site-icerigi.md` bağı koparılır ya da OAB'nin belgesi o güne yazılır), `test_depo_sizintisi`, `test_veri_sizintisi`, `test_surum_yolu` | F1a-1, F1a-2 |
| `backend/pyproject.toml` | `testpaths` ve `--cov=katalog` çıkar; ruff, mypy strict, kapsam eşiği 75 kalır | F1a-2 |
| `backend/config/settings.py`, `urls.py` | `INSTALLED_APPS`, `include("apps.kutuphane.urls")`, belge dizesi, `SECRET_KEY` ve test VT adı, `RolMiddleware`, `od_exception_handler`; **`ALLOWED_HOSTS` koşullu** (`OD_SESSION_TOKEN` doluysa `backend` yok) + test (§4.1, §13 D46) | F1a-2, F1b |
| `backend/shared/crypto.py` | Kimlik dizgeleri; `from_db_value` **katı kip**: kilit açıkken çözülemeyen ya da token olmayan dolu değer `CorruptField` işaretiyle döner, panoya bütünlük uyarısı; hoşgörü yalnız `gecis` sürerken (TK8, §13 D48). Öteki ilkel işlevler aynen | F1a-1, F1b |
| `backend/shared/pdf.py` | WeasyPrint `url_fetcher`: yalnız `data:` ve paket içi `file:`; öteki şemada istisna; ağ tuzaklı test (§4.1, §13 D47) | F1a-2 |
| `backend/shared/exceptions.py`, `letterhead.py` | İşleyici adı; okul antedi aynen, birlik antedi kararı §9.1 ([iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md) §11-6; E01-E03 F1c'de basılacağından F1c'nin ön koşulu) | F1a-1, F1c |
| `apps/okul/models.py`, `migrations/` | `SchoolConfig.kutuphane_saatleri` çıkar; OAB alanları §5'te; `Account`, `AuditTrail`, `AuditKey`, `AccessLog` §4.6'da; `AuditTrail` için ekleme-yalnız SQLite tetikleyicileri; `Student` ALMA; `ClassSection` §5 (T5); göçler tek `0001_initial` | F1b |
| `apps/okul/excel_personel.py`, sentetik personel örneği, `uret_eokul_ornekleri.py` | "Görevi" yalnız üye türünü belirlemek için okunur (öğretmen/yönetici) | F1b |
| `apps/okul/eokul.py`, `excel_ogrenci.py` | **Veli listesi ayrıştırıcısına** dönüşür (T5): blok düzleştirici ve sınıf/şube çıkarımı korunur; yalnız veli ad-soyadı ve öğrencinin sınıfı okunur, öğrenci adı, numarası, T.C. kimlik no okunmaz ve tutulmaz. Hangi e-Okul raporunun veli adını taşıdığı **doğrulanmadı** (sınıf listesi OOG01001R020 taşımaz) — §15 M-10 | F1b |
| `apps/okul/kip.py`, `kip_izinleri.py`, `kip_middleware.py`, `views_mode.py` | → `oturum.py` (`OturumDurumu`), `rol_izinleri.py` (uç + yöntem + parametre; parametre denetçileri aynen), `rol_middleware.py`, `views_oturum.py`; görevli/yönetici kipi → oturum + rol (§4.4); servis katmanı yetki kapısı yeni (§4.4.2). Yeniden adlandırma bilinçli: "kip" kavramı kalkar | F1b |
| `apps/okul/lock_middleware.py` | 423 iletisi: "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız program yöneticisine başvurun)." — ailedeki "yönetici parolası" dili OAB'de her kullanıcının kendi hesabıyla açtığı düzene uymaz (§13 D50) | F1b |
| `apps/okul/services/recovery_key_document.py`, `templates/documents/kurtarma_anahtari.html` | Metin OAB'ye göre yeniden yazılır (§13 D50): amacı; anahtarın no'su ve üretim tarihi; saklama yeri **okul müdürlüğünde mühürlü zarf**, veliye geçmez, devir tutanağına yalnız zarfın durumu girer (D3); "parola paylaşılmaz, herkes kendi hesabıyla" (BSG md. 7/2, 9/2-e); dönemlik yenileme ve eski zarfın imha tutanağıyla yok edilmesi; PDF dosyası bilgisayarda bırakılmaz. Ailedeki "yönetici parolası en az iki kişide bulunsun", "öğrenci … okul numaraları", "kütüphane masası" ifadeleri çıkar. Aynı modül F4'te **kurtarma anahtarı zarfı imha tutanağını** da üretir (katalog dışı program belgesi, §9.7; DEK yenilemesinin 7. adımı, §4.4.4) | F1b, F4 |
| `apps/okul/permissions.py`, `views_app.py`, `restart_gate.py` | `RequiresAdminPassword` → rol izinleri; `app/quit/`'te görevli parola dalı sökülür; "tepsiden Çık" iletisi | F1a-2, F1b |
| `apps/okul/masaustu_kanca.py` | `KatalogKontrolu` protokolü ve katalog bakım çağrıları sökülür; çıkış kancası ve gün işleri kaydı kalır | F1a-2 |
| `apps/okul/services/app_password.py` | Şema 2: `enable` → ilk yönetici hesabı ve ilk İA; `unlock(hesap, parola)` + hesap mührü ve iki depo kuralı (§4.6.1); hesap aç, kapat (TK11), sıfırla, askı (hesap başına hatalı deneme sayacı, §15 M-12); kurtarma anahtarıyla açılış yalnız `yonetici` hesabına (§4.4.3); `start_handover` yerine hesap geçişi; DEK yenileme `gecis: DEK_YENILEME` (TK12, F4). Dosya adı korunur: "parolayla DEK açma" kavramı sürer | F1b, F4 |
| `apps/okul/services/backup_restore.py`, `live_restore.py` | Bakım kapısı `shared/bakim.py`'den; aday durumlar şema 2 ve TK10 (anahtar no'su gösterilir); hesap seçimi; tam yedekte dosya deposunun manifestoyla doğrulanıp takası; `geri-yukleme-notu.json` | F1a-2, F1b |
| `apps/okul/services/encrypted_backup.py` | İndirme yedeği **tam yedektir** (veritabanı + dosya deposu; §4.4.7) | F1b |
| `apps/okul/services/imports.py`, `persons.py`, `sections.py`, `templates.py`, `setup.py` | Öğrenci mutabakatı ve şablonu çıkar; kayıt defteri kancaları OAB modelleriyle (F1c); sihirbaz adımları plan §2.2, yol haritası maddeleri | F1a-1, F1b, F1c |
| `apps/okul/services/updates.py` | Varsayılan depo ve `INSTALLER_PATTERN`; `OD_UPDATE_REPOSITORY` paketli yapıda (`sys.frozen`) okunmaz, test (§13 D51); kurucu çalıştırılmadan hemen önce SHA-256 yeniden doğrulanır (ailede bu adım var mı doğrulanmadı) | F1a-1, F1a-2 |
| `apps/okul/views_pool.py`, `selectors.py`, `serializers.py`, `views.py`, `urls.py` | Öğrenci dalları sökülür; personel ayrılış havuzu kalır | F1b |
| `apps/okul/management/commands/` | `app_password`, `restore_backup`: `--parola` → `--hesap` + parola; rol denetimi `restore.py` ile aynı | F1b |
| `apps/okul/tests/` | `test_cikis_ucu`, `test_dis_istek_kapilari` (izinli listeden katalog ve künye satırları çıkar), `test_imports`, `test_kip_koruma` → `test_rol_koruma` (+ hücre başına anlık görüntü testi), `test_kisi_yazan_uclar` | F1a-2, F1b |
| `templates/documents/aydinlatma_metni.html` | KVKK md. 10 asgari unsur kalıbı; içerik §3.4 | sonra |
| `frontend/` yapılandırma, `public/app-logo.png` | `package.json` adı; `tailwind.config.js` `--od-*`; `vitest.config.ts` eşiği (82/82/78/55) aynen; logo | F1a-1 |
| `frontend/src/` kökü | `App.tsx` rotaları (≈20 ALMA sayfası), `AppShell` gezinmesi, `index.css` `--od-*`, `KurulumKapisi` | F1a-2 |
| `frontend/src/lib/` | `api.ts` (`X-OD-Etkinlik`), `kilit.ts` (kilitlenmede ve kilit açılışında sorgu önbelleği ve modül belleği sıfırlanır: pencere içeriği yeniden yüklenir; Vitest; §4.4.3, §13 D53), `kip.ts` → `oturum.ts`, `restart.ts` (olaylar), `mevzuat.ts` (Yönetmelik adı), `format.ts` (`formatAccessionNo` çıkar), `gradeLevels.ts` (T5) | F1a-1, F1a-2, F1b |
| `frontend/src/modules/` | `kurulum` (1. adım ilk yönetici hesabı) · `guvenlik` (kilit ekranında hesap seçimi, askıdaki hesap etiketi; `GorevDevri` sökülür) · `ayarlar` (dört kütüphane paneli çıkar) · `hakkinda` (tek dış istek kapısı, ağ servisi yok, dürüst sınırlar §4.4.6) · `kilavuz` (5.080 satırlık dosyadan kabuk bileşenleri ayıklanır, içerik silinir) · `panel` (kütüphane kartları çıkar; son oturum kartı §13 D4; bütünlük ve geri yükleme kartları §4.6.3) · `cikis` (görevli dalı) · `kip` → `oturum` · `okul`, `kisiler` (kütüphane içe aktarımları) | F1a-2, F1b |

#### ALMA

| Yol | Neden | Bağın kesildiği yer |
|---|---|---|
| `backend/apps/kutuphane/` (256 dosya) | Kütüphane iş mantığı | `INSTALLED_APPS`, `config/urls.py`; `ready()` kayıtları — kip süre kaynağı (§13 D11), gün işleri, son oturum kartı ve `mark_process_start` (§13 D4) |
| `backend/katalog/` (34) | Ağ kataloğu | Spec `Tree`, `pyproject`; `bakim.py` önce `shared/bakim.py`'ye taşınır (§13 D3) |
| `desktop/tray.py` | Tepsi (T6) | Qt kurulumu ve SIGTERM köprüsü önce `qt_kurulum.py`'ye (§13 D1) |
| `desktop/katalog_server.py`, `katalog_kontrol.py`, `ag.py`, `powershell.py`, `guvenlik_duvari.py`, `dagitim.py` | Katalog, Ağ Doktoru, güvenlik duvarı, dağıtım türü kapısı | "Yalnız 127.0.0.1" testleri önce `test_server.py`'ye (§13 D2); `--autotest` katalog adımı (§13 D5) |
| `desktop/tests/` `test_ag`, `test_dagitim`, `test_guvenlik_duvari`, `test_katalog_kontrol`, `test_katalog_yuk`, `test_sozluk_metinleri`, `test_tray`, `test_katalog_server` | Söküleni sınar | Taşınacak parçalar önce taşınır |
| `backend/shared/barcode128.py` (+test) | Barkod | segno zinciriyle birlikte (§11 B9) |
| `apps/okul/tests/veri/eokul_sinif_listesi.xls`, `tests/test_geri_yukleme_katalog.py`, `migrations/0001-0006` | Öğrenci listesi (T5), katalog, Kütüphane şeması | `.gitignore` istisnası sentetik veli örneğine geçer |
| `templates/documents/` — `gorev_devri_notu.html` (KütD-E18) ve 19 kütüphane şablonu | Kütüphane evrakı | KütD-E18 kalıbı F4 devir-teslimde (MY devir notu) yeniden yazılır |
| `packaging/linux/ufw-*`, `firewalld-*.xml`, `windows/gorev-kur.ps1`, `tests/test_ag_katalogu_paketi.py` | Güvenlik duvarı, otomatik başlatma, katalog paketi | `.iss` görevleri, `build.sh` kurulum satırları |
| `scripts/ag_katalogu_provasi.py`/`.sh`, `deneme_verisi.py`, `ekran_goruntuleri/` | Ağ provası; kütüphane deneme verisi; site görüntüleri | F7'de OAB'nin uydurma veri üreticisi aynı kalıpla (stdlib + openpyxl, çıktı depoya girmez); site adımında görüntü kalıbı |
| `frontend/src/ui/BarcodeInput.tsx` (+test); 12 modül (agkatalogu, ayiklama, dokumler, dolasim, kayip, kutuphane, raporlar, saklama, sayim, teslim, uyelik, yil — 159 dosya); `src/test/` dört kütüphane verisi | Kütüphane ekranları | `App.tsx`, `AppShell`, `panel`, `ayarlar`, `kip`, `kisiler`, `kilavuz` |
| Kök `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/` | OAB'nin kendileri var | — |

#### YENİ (aileden gelmeyen)

| Yol | Ne | Zaman |
|---|---|---|
| `desktop/qt_kurulum.py` (+ `test_qt_kurulum.py`) | `tray.py`'den taşınan `load_qt`, `prepare_qt_application`, SIGTERM köprüsü | F1a-2 |
| `backend/shared/bakim.py` | `katalog/bakim.py`'deki `BakimKapisi` (yalnız stdlib); geri yükleme ↔ gün işleri dışlaşması; **uzun yazma işi sayacı** (boşta kilit ve çarpı ertelemesi, §4.2) | F1a-2, F1b |
| `backend/shared/docx.py`, `shared/evrak.py` | T2 çizici ve cephe (TK17); `--evrak-duman`; `evrak.py` WeasyPrint'i `shared/pdf.py`'nin `url_fetcher`'ıyla çağırır | F1a-3 |
| `backend/shared/dosya_sifreleme.py` (+ testleri) | Dosya deposu: dosya başına anahtar, `ODDOSYA\x01` kabı, sarmal (`od-dosya-sarmal/v1`), bellekten akan açma, yetim taraması (§4.4.4, §4.4.7; TK22) | F1b |
| `Account`, `AuditTrail`, `AuditKey`, `AccessLog` modelleri ve servisleri | T1, TK16 (§4.6): hesap mührü ve iki depo kuralı, denetim izi yazıcısı (aynı işlem, izinli alan listesi, içerik MAC'i), İA, çapa ve kilitli kip (`iz-durumu.json`), kendiliğinden doğrulama, erişim günlüğü ve 2 yıllık silmesi | F1b |
| `frontend/src/modules/kullanicilar` | Hesap aç, kapat, askıdan çıkar, parola sıfırla; hesap teslim pusulası (E63); hesap önerileri ve hesap geçişi (F4); son girişler | F1b, F4 |
| `frontend/src/modules/` F1c ekranları: `birlik-donemi`, `organlar`, `temsilciler`, `gecis-kurulumu`, `pano` | Birlik dönemi (hazırlık ve açılış), organ üyelikleri ve görev bölümü, temsilciler çizelgesi, geçiş kurulumunun organ adımları (§7.9), pano kabuğu (§7.10); aile kitiyle yeni yazılır, OYS ön yüzü alınmaz (§12.A) | F1c |

**Kalıp olarak sonra bakılacaklar** (kopyalanmaz): `apps/kutuphane/services/saklama.py` + `pre-anonim` (saklama ve
anonimleştirme; `wal_bosalt`, `pre_migrate_before` kalıbı dönem kapanışı silmelerinde de kullanılır, F4) ·
`modules/dokumler` (KVKK md. 11 kişi dökümü) · `gorev_devri.py` + KütD-E18 (MY devir notu, F4) · `BelgeIzi` (tür,
tarih/sayı, sha256 — evrak izi, §9) · `docs/saha-kabulu.md` + eşleme testi + `deneme_verisi.py` (F7) ·
`scripts/ekran_goruntuleri/` (site, F7).

---

## 13. Devralınan kusurlar

### 13.A İskeletten (Kütüphane Defteri)

*Kaynak sütunu: "TB" = Kütüphane `docs/teknik-borc.md` maddesi; "env." = [iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md)
bölümü; "bu belge" = bu yazımda kaynak kodda görülen; "denetim" = [tasarım denetimi](../kesif/2026-10-31-tasarim-denetimi.md)
bulgusu. Kütüphane'de ALMA'lık bölümde kalanlar (TB2, TB10-12, TB15-16, TB20-22, TB29-35, TB37-38, TB41-42) OAB'ye
geçmez; TB26 bilgi içindir (OAB kapalı hâli devralır). D32-D45 §13.B'dedir; F0-9'da eklenen iskelet kusurları D46'dan
devam eder.*

| # | Kusur | Kaynak | Düzeltme | Öncelik | Faz |
|---|---|---|---|---|---|
| D1 | Linux Qt kurulumu (`load_qt`, `prepare_qt_application`) ve SIGTERM köprüsü `tray.py`'dedir; tepsiyle silinirse Pardus penceresi bozulur, oturum kapanışında temiz kapanış işareti yazılmaz | env. §3.1, §10.1-3 | `desktop/qt_kurulum.py`'ye taşı, testlerini taşı, sonra `tray.py`'yi sil | yüksek | F1a-2 |
| D2 | "Yalnız 127.0.0.1" değişmez testleri `test_katalog_server.py`'dedir; katalogla silinirse kanıt kaybolur | env. §10.1-2 | `test_server.py`'ye taşı; `0.0.0.0` taraması daralır (tek muafiyet WebView2 damgası) | yüksek | F1a-2 |
| D3 | Bakım kapısı `katalog/bakim.py`'dedir; `gunluk.varsayilan_bakim_girisi` `ImportError`'da sessizce "her zaman izinli"ye düşer. Katalog sökülünce canlı geri yükleme ile gün işleri (günlük yedek) dışlaşmaz; Windows'ta açık bağlantı dosya takasını bozabilir | **bu belge** (`desktop/gunluk.py:246-252`, `masaustu_kanca.katalog_bakima_al`, `live_restore.py:111`) | `BakimKapisi`'ni `shared/bakim.py`'ye taşı; düşüş yolunu kaldır; `live_restore` kapıyı doğrudan kapatır; "geri yükleme sürerken gün işi başlamaz" testi | yüksek | F1a-2 |
| D4 | Temiz kapanış "son oturum" kartını ve `mark_process_start` kaydını yalnız `apps/kutuphane` yapar; uygulama sökülünce T15 uyarısı sessizce kaybolur | env. §3.7 + bu belge | Kartı ve kaydı `apps/okul` + `modules/panel`'e al; "işaret yoksa kart görünür" testi | orta | F1a-2 |
| D5 | `--autotest` katalogu kaldırır, kalkmazsa 6 döner; katalog sökülünce paket duman testi düşer | env. §10.1-4 | Katalog adımını çıkar | yüksek | F1a-2 |
| D6 | Kalıntı kalıbı "Kütüphane Defteri"yi kaçırır (`katla()` "ü"yü katlamaz); `kd[_:-]` kelime sınırsız | env. §4.2, plan §1.4 F0 eki | §2.3.3 kalıpları + örnek testi | yüksek | F1a-1 |
| D7 | `gates.sh` yavaş dalı ve `kapilar.yml` gecelik girdisi yavaş test kalmayınca kırmızı (doğrulanmadı); `pyproject` `katalog` test yolu ve kapsamı | env. §8.1, §10.1-5, 6 | Dalları ve yolu çıkar | orta | F1a-2 |
| D8 | `test_bagimlilik_duman_gercek…` segno'yu adıyla sınar | env. §10.1-7 | §11 B9 ile birlikte | orta | F1a-2 |
| D9 | Depo kapısında IBAN taraması yok; OAB `.gitignore`'u sentetik e-Okul örneğinin istisnasını taşımıyor (CI'da test düşer) | env. §10.1-8, TB25 | IBAN (TR + 24 hane, mod-97) taraması; `.gitignore` birleştirmesi; `.docx`/`.ods` adıyla istisna | yüksek | F1a-2 |
| D10 | Görev devri ekranı `apps/kutuphane` uçlarına (`library/handover/…`) bağlı | env. §3.7, §10.1-9 | Kartı ve bağı sök; OAB devir-teslimi F4'te | orta | F1a-2 |
| D11 | Kip süreleri `LibraryPolicy`'den beslenir; uygulama yoksa sessizce varsayılan 3/30 dk | env. §10.1-10 | `OturumDurumu` boşta süresi ayardan (TK14) | orta | F1b |
| D12 | `backend.Dockerfile` son satırı `0.0.0.0` dinleyen geliştirme komutu | env. §10.1-11 | Sil | düşük | F1a-1 |
| D13 | `oys-theme` saklama anahtarı (OYS kalıntısı) | env. §10.1-12 | `oab-defteri-theme`; kalıp `oys-` | düşük | F1a-1 |
| D14 | Kurtarma anahtarı yenileme ele geçmiş anahtarı geçersiz kılmaz; yedekler eski parolayla açılır — dönemlik veli hesaplarıyla **ağırlaşır** | TB17, TB23; env. §6.3-2 | TK10 + TK11 (F1b); TK12 + eski zarfın imha tutanağıyla yok edilmesi (D3; §4.4.4) (F4) | yüksek | F1b, F4 |
| D15 | Kurulum bitmeden kip süreyle kapanmıyordu (anahtar ekrandayken atmasın) | TB19 | Aynı kural oturum kilidinde: sihirbaz bitene dek boşta kilit yok; elle Kilitle çalışır | orta | F1b |
| D16 | Her güncelleme yönetici ister | TB7, env. §11-1 | TK7 (§15 M-1): tek kullanıcılı senaryoda kullanıcı başına kurulum; ortak Windows hesabında yönetici kurulumu sürer | orta | F1a-2 |
| D17 | Debian 11 ana deposu arşive taşınınca derleme 404; Debian 13 provası yok; t64 adları | TB5, env. §8.5 | `test-kurulum.sh` ve `paketleme.yml` `11 12 13`; `apt_dene` arşiv sabitlemesi aynen; `Depends` davranışını prova gösterir | orta | F1a-2 |
| D18 | Lisans dizini kararlı öncesi iki iş (MSYS2 kaynak arşivi, Qt bildirimi) | TB28 | python-docx/lxml ile `uret.sh` yeniden üretim; iki iş F7 paketlemesinden önce | orta | F1a-2, F7 |
| D19 | PySide6 6.8.3 tavanı; `.deb` ~180 MB | TB27 | Tavan korunur; yükseltmeden önce sembol denetimi | orta | sürekli |
| D20 | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hâle Getirilmesi Hakkında Yönetmelik korpusta yok | TB9 | `docs/mevzuat/`'e resmî kaynaktan; saklama ve anonimleştirme tasarımından (§5) önce | orta | F4'ten önce |
| D21 | Şifreleme kapsamı Kütüphane modeline göreydi (düz kalan alanlar) | TB1 | OAB modeline göre §5'te yeniden yazılır | yüksek | F0-8 (§5) |
| D22 | Anonimleştirilen bağlar yedeklerde ve arşivdeki asılla eşleşebilir | TB8, TB39 | OAB saklama tasarımında aynı sınır; §5 | düşük | F4+ |
| D23 | Şifreleme öncesi düz metin penceresi | TB24 | `enable()` boş tablo şartıyla kuramsal; aynen. Kapanış silmelerinden sonra `wal_checkpoint(TRUNCATE)` (§4.4.7) | düşük | — |
| D24 | İmzasız exe (SmartScreen) | TB6 | Port kısmı düşer; kılavuz; imzalama ileride | düşük | F7 |
| D25 | Büyük dökümlerde PDF süresi (tek PDF kilidi) | TB36 | Uzun gelir-gider dökümünde Excel asıl çalışma biçimi; gerçek uzunlukta veriyle sayfa bütçesi testi | düşük | F3 |
| D26 | Pardus paketi açık programı kapatmaz | TB40 | Çarpı = çık ile olasılık düşer; `prerm` iletisi | düşük | F1a-2 |
| D27 | `synchronous=FULL` maliyeti | TB3 | Kalır; HDD ölçümü saha | düşük | F7 |
| D28 | Plan §2.1-2 bağımlılık zincirini "üç yer" sayar | env. §2.12-5 | Dört halka + lisans (§11); plana "F0 eki" | düşük | F0-8 |
| D29 | `backup.encrypt_legacy_backups` ve düz `*.sqlite3` yedek kalıpları ailenin düz yedek döneminden kalma geçiş yoludur | **bu belge** (`desktop/backup.py`) | Sök (OAB'de düz yedek hiç olmadı) | düşük | F1a-2 |
| D30 | "Olası aynı kişi" ad benzerliğiyle | TB18 | Personel ve veli aktarımında birleştirme önerisi onaylı | düşük | F1b |
| D31 | Logo geçiciydi; dosya adları taramaya girer | TB4 (kapandı) | Yeni logo, elle çizilmiş 16/24/32; adlar `oab-defteri-*` | düşük | F1a-2 |
| D46 | `ALLOWED_HOSTS` koşulsuz `["127.0.0.1", "localhost", "backend"]`; Kütüphane tasarımı `backend`i yalnız belirteç boşken eklemeyi yazmış (kendi denetiminin GA-13'ü), kodda uygulanmamış, kilitleyen test yok | denetim GA-21; `backend/config/settings.py:58` | Koşul + test (§4.1; §12.B `settings.py`) | orta | F1a-2 |
| D47 | WeasyPrint `url_fetcher`'sız çağrılır; belgedeki ya da CSS'teki `http(s)` adresini kitaplığın kendi istemcisi indirir, kaynak taraması bunu görmez | denetim GA-22; `backend/shared/pdf.py:51` | Yalnız `data:` ve paket içi `file:` kabul eden `url_fetcher` + ağ tuzaklı test (§4.1) | orta | F1a-2 |
| D48 | `EncryptedTextField.from_db_value` kilit açıkken çözülemeyen değeri hata vermeden düz metin döndürür; SQLite'ta şifreli sütuna yazılan düz metin meşru veri gibi görünür | denetim GA-9; `backend/shared/crypto.py:340-354` | Katı kip: `CorruptField` işareti + pano bütünlük uyarısı; hoşgörü yalnız `gecis` sürerken (TK8) | orta | F1b |
| D49 | Yedek yalnız SQLite görüntüsüdür, ek dosyası taşımaz; rotasyon yalnız `gunluk-` ve `pre-anonim-` öneklerini günle siler, tanımadığı öneke dokunmaz, `pre-migrate-` adetle tutulur | denetim GA-1, GA-5; `desktop/backup.py:3-7, 366-391` | Kap `ODBAK\x03` (dışarı çıkan yedekte dosya bölümü); rotasyon kümesi bütün yerel önekleri kapsar, KVKK tetiğinden eski `pre-migrate` silinir (§4.4.7) | yüksek | F1b, F4 |
| D50 | Kurtarma anahtarı belgesi "yönetici parolası en az iki görevlendirilmiş kişide bulunsun" diye öğütler (T1 ve [BSG Yön. md. 7/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7), [9/2-e](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) ile çelişir), öğrenci ve kütüphane masası anar; kilit iletisi "yönetici parolası" ister | denetim GA-19; `backend/templates/documents/kurtarma_anahtari.html:40, 61-78`, `backend/apps/okul/lock_middleware.py:113` | Üç dosya UYARLA'ya; metin OAB'ye göre (§12.B); F1a-2'deki elle "alan kalıntısı" taramasına adıyla girer (§2.3.3) | orta | F1b |
| D51 | `KD_UPDATE_REPOSITORY` paketli yapıda da koşulsuz okunur; kullanıcı ortam değişkeni güncelleme denetimini başka depoya yönlendirebilir, SHA-256 o deponun özetiyle doğrulanır | denetim GA-14; `apps/okul/services/updates.py:38` | Paketli yapıda (`sys.frozen`) okunmaz + test | orta | F1a-2 |
| D52 | Veri, günlük ve önbellek dizinleri Linux'ta varsayılan umask'la açılır (`desktop/paths.py:81`); tek `chmod` kanal soketindedir | denetim GA-20 | `umask 077`, dizinler 0700, gizli dosyalar 0600 + test (§4.5) | orta | F1a-2 |
| D53 | Ön yüz kilitlenince sorgu önbelleğini ve modül belleğini temizlemez; ailede kilit tek kişiye aitti, OAB'de önceki hesabın verisi sonrakine kalır | denetim GA-23; `frontend/src/lib/kilit.ts` | Kilitlenme ve kilit açılışında pencere içeriği yeniden yüklenir + Vitest (§4.4.3) | düşük | F1b |

**F1a arındırma sırası** (önce ayır ve taşı, sonra sök — §16 R14): (1) D6 kalıntı kalıpları ve kimlik çevirisi (F1a-1,
kapısız ara commit) → (2) D1 `qt_kurulum.py`, D2 `test_server.py`, D3 `shared/bakim.py`, D4 son oturum kartı —
taşı ve yeşile getir → (3) tepsi, katalog, Ağ Doktoru, güvenlik duvarı, barkod, `apps/kutuphane`, ön yüz modüllerini
sök; D5, D7, D10, D29 → (4) bağımlılık zinciri (B9, B18) ve D8 → (5) D9 sızıntı kapıları, D12, D13 → (6) "ağ servisi
sunmaz" cümlesi bütün kopyalara ([iskelet envanteri §3.9](../kesif/2026-10-31-iskelet-envanteri.md)); D46, D47, D51,
D52 → (7) D17 Debian 13 provası, `uret.sh` (D18) → (8) F1a-3 evrak hattının ilk kanıtı (B10-B12). Kapı (8)'den sonra
koşar. D48, D49, D50, D53 F1b'nin güvenlik çekirdeğiyle birlikte kapanır.

### 13.B OYS'den (iş mantığı — düzeltmenin yeri ilgili bölümdedir)

*Ayrıntı ve dayanak: [OYS envanteri §0, §8](../kesif/2026-10-31-oys-oab-envanteri.md). Bu tablo yalnız izler; düzeltme
kararı yerinde verilir.*

| # | Kusur | Kaynak | Düzeltmenin yeri | Faz |
|---|---|---|---|---|
| D32 | Genel kurul yeter sayısı kayıtlardan sayılıyor; taban sabit 16 koltuk ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); olağanüstüde 0 çıkıyor | S-1, S-2 | §6 kural paketi, §7 genel kurul | F1c, F2 |
| D33 | YK dönem sınırı yalnız başkanlığı sayıyor ([md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) | S-4 | §6 | F1c |
| D34 | Servis taşımacı seçiminde EK-3 puanlama varsayılan; yürürlükten kalkmış `EN_DUSUK_TEKLIF` | S-7, ana bulgu 5 | §7 servis | F6 |
| D35 | İmza blokları Yönetmelikle çelişiyor (davetiye, tahmini bütçe, gelir-gider çizelgesi müdür imzalı) | S-9 | §9 | F2-F4 |
| D36 | `is_metropolitan` yanlış ölçütü modelliyor | S-17 | §5 okul kartı (yerleşim türü üçlü) | F1b |
| D37 | Tarih hesapları (5 × 365 gün, ay = ⌈gün/30⌉, takvim çeyreği) | S-18 | §6, §7 (§15 A-10) | F3-F5 |
| D38 | Devamsızlık katılım kaydını sayıyor, toplantıyı değil | S-19 | §7 YK (§15 A-9) | F3 |
| D39 | Tekil kısıtlar: pay beyanı yer içermiyor, sözleşme ihale başına tek | S-16 | §5 (§15 A-6) | F5, F6 |
| D40 | Atıf hataları (istekli suç engeli md. 20/11; tek katılımcı tutanağı; portör belgesi istekliden) | S-8 | §6, §9 | ilgili faz |
| D41 | KVKK: üyelikteki serbest metin beyan notu, DK listesindeki adli sicil maddesi | S-20, ana bulgu 15 | §5, §7 | F1c, F4 |
| D42 | Kodda ve testte gerçek bir taşımacı firma adı | S-21 | Taşırken uydurma ad kullanılır. **Ad depoda hiçbir biçimde (kod, test, betik, belge, kalıp listesi) düz metin bulunmaz** (değer bu belgeye de yazılmaz). Sızıntı kapısı (`depo_sizintisi.py`) yasaklı adları depo dışındaki, `.gitignore`'lu yerel `.od-yasakli-adlar.txt` dosyasından okur ve katlanmış metinde arar; dosya yoksa kapı "yasaklı ad taraması atlandı" yazar (geçer ama uyarır). CI'da liste depo sırrı olarak verilir ve iş başında bu dosyaya yazılır; sırrın tanımı yayın işidir (altın kural 8). Firma bir şahıs işletmesiyse ad kişisel veridir (denetim KM-17) | F6 (kapı F1a-2'de hazırlanır) |
| D43 | Servis evrakında "ihale" söz dağarcığı (7 şablonda 13 kez) | S-25 | §9 (altın kural 6; §15 A-4) | F6 |
| D44 | OYS sert engelleri altın kural 3 ile gerilimde | S-23 | Kullanıcı kararı F0-b → §7 | F5, F6 |
| D45 | Arz bedeli vadesi yalnız 20'si; aylık kira takvimi yok | S-5, S-14 | Kullanıcı kararı F0-a → §6, §7 kantin | F5 |

---

## 14. Faz planı ve kod kapıları

Ailenin faz kuralları geçerlidir: faz **kod kapısı** geçilmeden kapanmaz; tasarımdan sapmalar "F<n> ekleri (tarih)"
satırıyla bu belgeye işlenir; okulun denetiminde olmayan saha kanıtı fazı kilitlemez, sonraki faza ertelenir; yayın
işleri kullanıcı onaylıdır. F0 ve F1'in iş kalemleri [F0-F1 planında](../plan/2026-10-31-f0-f1-plani.md)dır; F2-F8
ayrıntısı her fazın başında aynı biçimde bir plan belgesiyle açılır. Kural paketi `OAB-2023.12` (157 kural: 37 sert,
120 uyarı) F1c'de ilk revizyonuyla (`r1`: 53 kural; 18'inin davranışı sonraki fazlarda) girer; kalan kurallar, onları
kullanan kod hangi fazda yazılırsa o fazda paket revizyonu artırılarak eklenir (§6.2, §6.4). Evrak kataloğunun 79
belgesi (E01-E79) fazlara şöyle dağılır: F1b 1 · F1c 3 · F2 12 · F3 13 · F4 18 · F5 10 · F6 18 · F8+ 4 (§9.5).

**Faz ataması** [planın §3](../plan/2026-10-31-f0-f1-plani.md)'üne bağlıdır (denetim EK-7): genel kurulun kendi
evrakı F2'de; YK, gelir-gider, banka, makbuz ve **kantin aylık kira ile arz/pay hesabı** F3'te; harcama zinciri, bütçe,
bildirim, ilan, Denetleme Kurulu, faaliyet raporu, kapanış ve **devir-teslim** F4'te; kantinin kiralama süreci ve
sözleşmesi F5'te; servis F6'da. Bir fazın ihtiyaç duyduğu ama sonraki fazda üretilecek belge (ör. F2'de faaliyet
raporu ve tahmini bütçe) o fazda **dosya eki** olarak alınır. Geçiş kurulumunun (§7.9) organ kısmı F1c'de, mali kısmı
F3'tedir; panonun kabuğu F1c'de, kalemleri her fazda gelir (§7.10).

**Genel ilkeler.** Göçler yalnız şema değiştirir; veri göçü ilk kilit açılışında koşar (§4.1). Süreli silmeler
modelleriyle gelir: erişim günlüğünün 2 yıllık silmesi F1b'de, dönem kapanışı silmeleri F4'te; kiracı, çalışan ve şoför
belge taramalarının süreli silmesi (§15 B-5) F5 ve F6'da kalemleşir.

**Her kapıda üç ortak madde** (denetim SU-5, SU-13, SU-15): (1) **kılavuzun bu faza ait bölümü yazıldı**; (2) fazın
yeni ekranları **1366×768'de yatay kaydırmasız** açılır (elle denetim; F1a'da `NOTLAR.md` listesine girer); (3) fazın
**pano kalemleri** (süre sayaçları, "tamamlanacaklar", iş kuyrukları; §7.10 "Fazlar") sınanır.

| Faz | İçerik | Kod kapısı |
|---|---|---|
| **F0** | Mevzuat korpusu, envanterler, kullanıcı kararları, bu belge, bağımsız tasarım denetimi (F0-9) ve bulguların işlenişi | Plan §1.6 — denetim bulguları işlendi ya da gerekçeyle reddedildi, kullanıcı "F0 tamam" dedi |
| **F1a** | Aile iskeleti: ham kopya + kimlik çevirisi, arındırma (sıra §13), evrak hattının ilk kanıtı (T2), Debian 13 provası | Windows'ta exe açılır, çarpıyla kapanır · `.deb` Debian 11/12/13'te kurulur ve açılır · `--pdf-duman`, `--evrak-duman` (paketli ikilide `Document()` dâhil), `--bagimlilik-duman` geçer · kimlik kalıntısı sıfır · sızıntı denetimleri ve `gates.sh` yeşil · `url_fetcher` ağ tuzağı, `ALLOWED_HOSTS` koşulu, `OD_UPDATE_REPOSITORY`'nin paketli yapıda okunmaması, Linux dizin ve dosya kipleri (§10.6) · ana ekranlar 1366×768 |
| **F1b** | Güvenlik çekirdeği (kişisel hesaplar, T1; §4.4, §4.6), kurulum sihirbazının **ilk üç adımı** (yönetici hesabı ve kurtarma anahtarı — anahtar basılıp müdürlükte kapalı zarfta saklanır, D3; okul kartı; ders yılı, dönemler, kapalı günler), kullanıcılar ve roller, hesap teslim pusulası (E63), e-Okul personel ve veli aktarımı | Aile güvenlik testleri adıyla (§10.6): parola kurulmadan kişi yazan uç 409 · kilitliyken yazma hata verir; kilitliyken gün işi iş verisi yazmaz, şema göçü olayı kilitli kipte mühürlü · güvenlik dosyası silinince fail-closed · kör indeks eşleşmesi · şifreli yedek (ekler dâhil) geri yüklenir · **yönetici olmayan hesapla `--geri-yukle` reddedilir** · iki deponun dört hâli ve hesap mührü bozulması (§4.6.1) · **denetim izinde ve arşiv dökümünde uydurma kişisel veri sıfır** (§4.6.2) · rol testleri (rol matrisi §4.4.2; hücre başına anlık görüntü ve dipnot başına servis testi; DK yalnız denetim modülüne, müdür yalnız kendi yazılarına, mali kayıtlara yalnız muhasip yazar; her yazma denetim izinde) · **kapanmış hesap giremez** (elle kapanış ve üyelik düşmesi; dönem devrindeki hesap geçişi F4'te) · veli listesi yalnız iki alan taşır · `ev::test_e63_pusulada_parola_alani_yok` |
| **F1c** | Sihirbaza **ilk birlik dönemi** adımı (geçiş kurulumunun organ kısmı: görevdeki kurul "devralınan" üyelik olarak girilir, §7.9), kişiler, organlar, kural paketi `r1` (`OAB-2023.12`, 53 kural), ilk üç evrak (E01-E03; FR-006, FR-011, FR-022), **pano kabuğu** ("bu hafta yapılacaklar", yol haritası; §7.10) | Plan §2.4 — atıf kilidi; yeter sayı 64/32 (sabit taban); dönem sınırı başkan ve üyeler için; organ bileşimleri (YK ve DK'de aynı kişi olamaz; müdür YK'ye giremez); `OrganMembership`'in iki kısmi tekil kısıtı (genel kurullu ve genel kurulsuz; `IPTAL` kısıta girmez); **dönem ortasında kurulum senaryosu**: devralınan kurul aday şartı olmadan `SECILDI`, geçmiş seçilme sayaçları toplu beyanla tek gerekçe, karar defterinin son sıra no'su ve sayfası; pano kabuğunun kalemleri; üç evrak docx + PDF eşdeğer; temiz Windows 11 ve Pardus 25'te uçtan uca zincir (kurulum → sihirbaz → okul kartı → dönem → kişiler → organlar → üç evrak → şifreli yedek → geri yükleme) · kılavuzun F1 bölümleri (kurulum, okul kartı, kullanıcılar, organlar) |
| **F2** | Genel kurul sihirbazı ve **genel kurulun kendi evrakı**: çağrı kararı, davet, ilan ve duyuru tutanağı, katılım cetveli, yeter sayı tespit tutanağı (E64), **ikinci toplantı ana yol** (saha 8; olağanüstüde de, §15.1 A-1), divan, ibra ("ibra edilmedi" akışı dâhil), seçim, aday listeleri, sonuç bildirimi, görev bölümü; olağanüstü genel kurul (müdür ve DK çağrısı dâhil). Faaliyet raporu, DK raporu ve tahmini bütçe bu fazda **dosya eki** | Pilot okulun 2026-2027 genel kurul akışı (birinci toplantıda yeter sayı yok → ikinci toplantı) uydurma adlarla programdan baştan sona üretilir; evrak genel setle içerik eşdeğer; 15 gün, 30 gün, bir hafta süre testleri · veli adı taşıyan belgenin (E07 çizelgesi, adlı E08) dosyası saklanmaz, arşiv paketine girmez · hazırlık dönemi: genel kurul planlanınca `HAZIRLIK` açılır, ikinci toplantıda yapılan genel kurulda seçilen kurulla dönem `ACIK` olur, genel kurul `IPTAL` olursa `HAZIRLIK` dönemi de `IPTAL` · olağanüstüde gündem dışı madde uyarı + gerekçeyle kaydedilir (B-13) · DK'nin 14/5 çağrısı yalnız md. 6 aykırılık işaretiyle. **Canlı kullanım** bir sonraki olağan genel kurulda (Ekim) F7 betası içinde |
| **F3** | YK toplantı ve karar taslağı ("deftere işlendi"; defterde sakat karar), devamsızlık ve yedek çağırma; işlem düzeyinde gelir-gider, hesap planı ve sihirbazın **banka-devreden bakiye adımı** (geçiş kurulumunun mali kısmı, §7.9), banka özeti içe aktarma ve eşleme, makbuz koçanı, şartlı bağış, kasada 5 iş günü, "TEFBİS'e girilecekler" listesi, deftere geçirilecek aylık baskı; **kantin aylık kira takvimi, arz bedeli (10'u / 20'si) ve pay dağılımı** (`OabContract`'ın kira alanları, `ContractInstallment`, `ShareStatement`). **Fazdan önce** pilot okulun muhasibiyle görüşülür (saha notuna eklenir) | Uydurma bir yıllık banka dökümü (~410 hareket) eşlenir, TEFBİS listesi ve defter baskısı üretilir; ters kayıt ve dönem kilidi testleri · **yalnız muhasip mali kayıt yazar**, `yonetici` yalnız "TEFBİS'e girildi" işaretini koyar (D2) · içe aktar → geri al → yeniden aktar aynı satır sayısını verir · makbuzlu kesin gelirin ters kaydı ve aynı yaprağa yeniden bağlanması · toplu deftere geçirmenin sayfa no'ları · defterde sakat karar hiçbir akışa bağlanamaz · uyarılı taslak kayıt gerekçesiz yazılır, `KESIN` gerekçe ister · "programa başlama günü" açılışlı dönem senaryosu ve geçişte toplu defter/TEFBİS işareti (§7.9) · kantin kira-pay hesabı kurallarının davranış testleri · mali ekranlar ~35 hareketli bir ayla 1366×768'de. **Saha kanıtı (kapıyı kilitlemez):** pilot okulun 2025-2026 hareketleri yerelde, depoya girmeden mutabık |
| **F4** | Harcama zinciri (talep → karar → komisyon → belge → ödeme → banka → TEFBİS; sürekli ödeme dosyası, kısa yol), tahmini bütçe ve gerçekleşme, aylık bildirim, dönemlik ilan, Denetleme Kurulu modülü (kontrol listesi, ara ve nihai rapor), sosyal-kültürel etkinlik (E36, §7.11), müdürün md. 27/3 yazıları (E35, E70; §7.12), faaliyet raporu ve kesin hesap, dönem kapanışı, **devir-teslim** (eski organ hesaplarının kapanışı, veri anahtarının yenilenmesi, eski kurtarma zarfının imha tutanağı), yıl sonu arşiv paketi | Uydurma bir dönemin tamamı programdan kapanır: kesin hesap = banka; devir tutanağı ve arşiv paketi (PDF + xlsx + JSON) programsız okunabilir · **DEK yenilemesinin yarıda kesme provası** (her adımdan sonra süreç öldürülür; veri, dosyalar ve zincir doğrulanır; §4.4.4) ve eski zarfın imha tutanağı yeni yedek doğrulanmadan basılmaz · dönem kapanışında denetim izi zinciri **tam** doğrulanır · **KVKK silmeleri:** kapanıştan sonra veritabanında, arşiv paketinde ve 15. günden sonra yedek dizininde (yedekler açılarak) uydurma veli adı, istekli telefonu ve e-postası, T.C. kimlik no kalmaz; bağsız kişi ve personel silinir; arşiv paketinde süreli kişisel veri alanı yoktur, paket silmelerden sonra üretilir (§4.4.7, §5.4) · 12 aylık hizmet alımı tek sürekli ödeme dosyasında; iki taksitli ve kasadan ödeme `ODENDI` · teslimden sonra girilen kayıt sonraki bildirimin geç kayıtlar bölümünde · kapanmış dönemde "TEFBİS'e girildi" konur, tutar değişmez, yeniden basım aynı özeti verir · E36 ve E70 örnekleri üretilir |
| **F5** | Kantin: kiracı kartı, kiralama süreci evrakı, EK-2 sözleşmesi, TÜFE artışı, Genelge 2024/35 yirmi yıl hesabı, kesin teminat (fesihte mahsup ve iade), fesih ve tahliye bildirimleri (E71, E72), kiracı ve çalışan belge süreleri; `bilgi/` dizini (KV Sirküleri No. 11 ve özelgeler) | 2026-2027 kantin sözleşmesi programdan birebir (pilot okul, uydurma adlarla) · yer teslimi imzadan önceyse uyarı · onay kaydı olmadan kesinleşme uyarı + gerekçe (D4) · il merkezi sözleşmesinde Özel Şartlar md. 2 pay notu · kesin teminatın üç akıbeti (gelir kaydı, mahsup ve iade, iade) |
| **F6** | Servis: taşımacının tespiti (komisyon değerlendirmesi esas, EK-3 yalnız md. 8/3 hâllerinde; mülki amir onayı olmadan kesinleşmez), sözleşme, araç-şoför belge takibi, denetim kaydı, taşımacı listesi duyurusu (asgari bilgi, D5) | Pilot okulun servis tespiti evrakı programdan birebir; servis evrakında "ihale/teklif/eksiltme" taraması sıfır (tek istisna KE-9) · onay olmadan kesinleşme sert (D4) · dosya iade talebi gelen evrak ve bilgi notu (U-E md. 7/2) · taşımacı ilanında yalnız ad/unvan, plaka, güzergâh (D5) |
| **F7** | Paketleme ve saha kabulü: pilot okulda 2026-2027 dönemine **paralel** beta (başlangıç tarihi ve devralma adımları §7.9'a göre saha planında yazılır); site sayfası (§17); kılavuzun "yeni kurulun ilk ayı" bölümü (her rol için bir sayfa) | Saha kabulü protokolü (ailenin `saha-kabulu.md`'si uyarlanır) ve **ölçülebilir ölçütler** (denetim SU-9): (1) muhasip ve sekreter aylık işini MY yardımı olmadan yapar, gözlem notu `saha.md`'ye girer; (2) MY'nin aylık TEFBİS ve defter işinin süresi, programla ve programsız iki ay karşılaştırılır; (3) beta boyunca defter deftere geçirilecek baskıdan, TEFBİS girilecekler listesinden yazılır — paralel yürütme ek elle kayıt doğurmaz; (4) bir sonraki olağan genel kurul sihirbazla canlı yürütülür, beta takvimi Ekim'i kapsar; (5) 4 GB'lık makinede açılış süresi ve bir evrakın PDF üretim süresi not edilir. Gönüllü okul aranmadığından (F0-d) kabul yalnız pilot okul |
| **F8+** | TEFBİS Excel mutabakatı (M12), denetim dosyası (TKB E.4 Tablo 1-4, Sayıştay icmali), personel modülü (doğrudan işveren okullar; K3), ilkokul/ortaokul ve küçük okul sınamaları | Fazın kendi planında |

Beta F4'ten sonra başlayabilir; F5 ve F6 beta sürerken eklenebilir (kantin kiralaması en çok beş yılda, servis tespiti
bir-üç yılda bir yaşanır).

---

## 15. Açık kararlar (varsayılanla ilerlenir)

Kullanıcı itiraz etmedikçe varsayılan uygulanır; itiraz gelirse "F<n> eki" ile değişir. Kimlikler: A-n bu bölümün,
M-n mimari (§4, §11, §13), B-n veri modeli ve akışlar (§5, §7, §8), KE-n kural paketi ve evrak (§6, §9, §10)
bölümlerinin önerisidir; S-n atıfları OYS envanterindeki sorulardır. §15.1'deki altı soru ve denetim sonrası beş soru (§15.1b, D1-D5)
kullanıcıya soruldu ve karara bağlandı; kalanlar varsayılanla ilerler (§15.2-§15.5). Denetim işlenişinde (F0-9) eklenen
yeni varsayılanlar: M-12, M-13, B-14…B-18, KE-21…KE-26.

### 15.1 Kullanıcı kararları (31.10.2026'da tek tek soruldu)

Bu altı soru K2'yi ya da altın kuralları etkilediği için kullanıcıya soruldu; cevaplar bağlayıcıdır.

| # | Soru | **Karar** | Dayanak / not |
|---|---|---|---|
| A-1 = KE-1 | Olağanüstü genel kurulda yeter sayı sağlanamazsa çoğunluk aranmaksızın ikinci toplantı yapılabilir mi? (S-3) | **Evet** — [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)'deki ikinci toplantı (otuz gün içinde, çoğunluk aranmaksızın) olağanüstüde de uygulanır | Öneriden farklı (öneri: her toplantıda yeter sayı). [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) hükmü tekrarlamaz; kullanıcı md. 9/2'yi genel hüküm saydı |
| M-5 | Müdür, olağanüstü genel kurul çağrısını da yazabilsin mi? | **Evet** — K2'deki müdür yazılarına eklendi | [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) |
| M-6 | Denetleme Kurulu, olağanüstü genel kurul çağrısını denetim modülünden yazabilsin mi? | **Evet** | [md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| B-13 | Olağanüstü genel kurulda çağrı gündemi dışında madde görüşülürse | **Uyarı + gerekçe** | md. 9/6 "gündeme bağlılık ilkesi geçerlidir"; altın kural 3'ün sert listesi genişlemez |
| A-2 = KE-5 | Aynı kişi aynı dönemde YK'de ve DK'de olabilir mi? (S-28) | **Hayır, sert** (`denetleme_kurulu.yk_uyesi_olamaz`) | Öneriden farklı (öneri: kural yok). Kullanıcı: "doğası gereği olmaz", dayanak aranmaz — denetleyen ile denetlenenin ayrılığı ([md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)). Kural notunda dayanağın kullanıcı kararı olduğu yazılır |
| KE-15 | Okul müdürü (veli olsa da) YK'ye eklenebilir mi? | **Hayır, sert** (`yonetim_kurulu.okul_muduru_uye_olamaz`) | Açık yasak yok; [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) ve [md. 27](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)'nin yorumu, CLAUDE.md altın kural 6 ve kullanıcı kararı |

### 15.1b Denetim sonrası kullanıcı kararları (31.10.2026)

Tasarım denetiminin (F0-9) beş bulgusu kullanıcı kararı gerektirdi; cevaplar bağlayıcıdır.

| # | Bulgu | **Karar** | Not |
|---|---|---|---|
| D1 | MA-2 · sert engelin "hesapta kullanılan yasal parametre" gerekçesi | **Programın hesapladığı değerde sert, kullanıcının belgeden girdiği değerde uyarı** | Arz oranı, pay dağılımı, KDV yok gibi hesaplanan tutarlarda oran değiştirilemez; sözleşmedeki teminat, kira, artış, ay sayısı, usul, EK-3 puanı, izin/ihbar süresi saparsa uyarı + gerekçe. CLAUDE.md altın kural 3'e işlendi |
| D2 | SU-1 · mali kayıtları kim girer | **Yalnız muhasip** | Öneriden farklı (öneri: MY girer, muhasip onaylar). MY mali kayıt yazamaz; TEFBİS listesini muhasibin girişinden sonra alır (§7.3) |
| D3 | GA-4 · kurtarma anahtarının yeri | **Okul müdürlüğünde kapalı zarf** | Veliye geçmez; devir tutanağına yalnız zarf kaydı; anahtar yenilenince eski zarf imha tutanağıyla yok edilir |
| D4 | MB-5 · mülki amir onayı olmadan kesinleştirme | **Serviste sert, kantinde uyarı + gerekçe** | Servis: [U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4). Kantin: dayanak doğrulanamadı (2886 md. 42 mülga, kiralama md. 51/g pazarlıkla); onay makamı ve tarihi kaydedilir |
| D5 | KM-13 · taşımacı listesi duyurusu | **Altın kural 5'e mevzuat istisnası**, asgari bilgi | [U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10): ad/unvan, plaka, güzergâh; telefon, adres, T.C. kimlik no basılmaz |

### 15.2 Genel kurul, organlar, evrak

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| A-3 = KE-16 | Resmî evraka "mevzuat uyarıları" kutusu basılsın mı? (S-24) | **Basılmaz**; uyarı ve gerekçe programın iç kaydında ve denetim izinde kalır, istenirse ayrı "uyum notu" çıktısı | Resmî dosyaya girecek evrak sade kalmalı; gerekçe kaybolmaz |
| A-4 = KE-8 | EK-3 puanlama cetvelinde 4. kriterin mevzuat lafzındaki "teklif vermesi" ibaresi (S-25) | Cetvel kriteri **kısa adıyla** basar, lafız alıntılanmaz (lafız korpusta durur) | Cetvel mevzuat metni değil komisyonun değerlendirme aracıdır; altın kural 6 |
| KE-9 | Servis sözleşmesi ve tip şartnamedeki TCK suç adı "ihaleye fesat karıştırma" | Söz dağarcığı denetiminin **tek istisnası** (suç adı değiştirilemez) | Servis Usul ve Esasları EK-1 md. 6, EK-2 md. 4 ve 7 |
| KE-10 | "Yeter sayı sağlanamadı" tutanağını kim imzalar? | YK Başkanı ve Sekreter; müdür "Görüldü" bloğunda | Dayanak bulunamadı (DOĞRULANMADI); md. 10/1-b açılışı müdüre verir |
| KE-11 | Üyelerin %10'u başvurduğunda çağrıyı kim yapar? | YK başkanı; YK çağırmazsa okul müdürü | md. 9/6; imza sırası DOĞRULANMADI |
| KE-12 | "İlk hafta" (görev bölümü) | 7 takvim günü | [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); yorum |
| B-12 | md. 12/4 seçilme sayımında yedek olarak seçilmek sayılır mı? | Asıl ve yedek her seçilme sayılır, dökümde ayrı gösterilir; yalnız uyarı | [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) "seçilebilir" der |
| B-2 | YK devamsızlığında "yeter sayı yok" toplantısı sayılır mı? | Sayılır | [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) "toplantıya katılmayan" |
| A-9 | YK devamsızlığı sayımı (S-19) | Son üç **toplantıya** bakılır; toplantı kaydı katılım girilmeden kapanamaz; düşme otomatik değil, öneri | md. 13/6 |
| A-6 | Birden çok taşımacı ve iki kantinli okul (S-16) | Desteklenir: bir tespit sürecinde birden çok taşımacı ve sözleşme (`Bidder.selected`); pay beyanı kiralanan yer başına | [Servis Usul ve Esasları md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) "sözleşme imzalanan taşımacıların" der (sahada DOĞRULANMADI) |
| A-7 | Servis komisyonu kararında oylama (S-7) | Oy birliği / oy çokluğu alanı ve muhalif şerhi; şablon "oy birliği ile" sabit basmaz | [Servis Usul ve Esasları md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4): çoğunluk, çekimser kalınamaz, muhalif üye gerekçe yazar |
| KE-19 | Okul idaresinin diğer resmî yazıları (kantin bildirimleri, servis komisyonu evrakı) | Taslağı `yonetici` hazırlar, müdür kâğıtta imzalar; müdür rolüne K2'de yazılanlardan başka yetki eklenmez | K2 |
| M-11 | K2'deki dört müdür yazısının (harcama talebi E25, md. 27/3 uyarısı E35, yeni okulda genel kurul daveti E05, olağanüstü genel kurul çağrısı E05) taslağını `yonetici` hazırlayabilsin mi? | **Hayır**; müdür programı kullanmıyorsa kâğıt talep gelen evrak (`DocumentRecord`) olarak kaydedilir, harcama zinciri o kayıttan yürür. md. 27/3'ün ikinci cümlesindeki MEM bildirimi (E70) bu dördünden değildir, KE-19 kapsamındadır | K2 lafzı: bu yazılar müdür hesabından. **Kullanıcıya sorulması önerilen (denetim SU-10):** harcama talep yazısı yılda 20-40 kez yazılıyor ve müdür programı fiilen kullanmıyor; "E25'in taslağını MY hazırlayıp müdür kâğıtta imzalayabilsin mi?" sorusu açık; cevap gelene dek M-11 uygulanır |
| KE-20 | Aydınlatma metnindeki veri sorumlusu | `SchoolConfig.data_controller_text`'ten dolar (§5.1); alan boşken E04 basılmaz; kim olduğu kılavuzda okul müdürlüğüne açık soru | F0-e (b); [KVKK md. 10/1-a](../mevzuat/6698-kvkk.md#madde-10) |
| KE-21 | Genel kurul katılım cetveli ile yeter sayı tespit tutanağı aynı belge mi? | **Ayrılır:** E08 katılım cetveli (veli adı; R9, saklanmaz), E64 yeter sayı tespit tutanağı (kişisiz sayılar; saklanır, yeniden basılır) | R9; [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); yeter sayının kanıtı kaybolmasın |
| KE-22 | YK, DK ve alım komisyonu üyesinden suç engeli ve tek birlik beyanı | **Okul uygulamasıdır**, kural paketinde değil; boşsa "tamamlanacaklar"da hatırlatma, mevzuat uyarısı değil, gerekçe istemez; hüküm kuralı ayrıdır (`uyelik.suc_engeli`, `yonetim_kurulu.tek_birlik`) | KM-8; [md. 12/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) beyan istemez |
| KE-24 | Eğitim kampüsü yönetimine temsilci ([md. 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) | Kampüsteki okul kapsamdadır (§3.5); okul kartında `in_campus`; hüküm sayısal ya da süreli değer taşımadığı için kural yok, temsilciler çizelgesinde (E03) kayıt satırı | UY-12; kural sayımı 157 değişmez |
| KE-25 | Kullanıcı kararına dayanan kuralın yürürlüğü | Paketin dayandığı Yönetmelik metninin tarihi (v1: 01.12.2023), kararın günü değil | MA-1; Ekim 2026 genel kurulu da kapsanır |
| KE-26 | Değerlendirme tutanağı, kasa sayımı, biten koçan teslimi ayrı belge mi? | **Bölüm:** değerlendirme E54'te, kasa sayımı E37'de, biten koçan teslimi ve koçan envanteri E22'de, kasa çıkışı E27'de; banka imza yetkisi yazısı (E66) ve iptal/kayıp yaprak tutanağı (E67) ayrı kod | MB-12; GNL-OAB-FR-015 B "Teslim-devir" sütunu, FR-005 B kasa satırı |
| B-17 | Toplantı yeter sayısı ya da üç kabul oyu olmadan alınmış ama karar defterine yazılmış karar programda nasıl tutulur? | `DEFTERDE_SAKAT`: defter sıra no'su, sayfa, gerçek katılım ve oylar ve açıklama ile iz olarak girilir; program geçerli saymaz, hiçbir bağlı akışı beslemez, Denetleme Kurulunun listesine ve kapanış denetimine düşer. Sert kuralın anlamı "kaydedilemez"den "geçerli sayılmaz"a döner (§5.2.4, §7.2) | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); ön değerlendirme §0-4 "defterin dijital izi" (SU-11) |

### 15.3 Para, kantin, servis

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| A-5 = KE-14 | Servis taksitlerinin takibi (S-6) | Birliğin defterine **girmez** (ücreti veli taşımacıya öder); yalnız bilgi. Taksit yapısı kantin aylık kira takvimine dönüşür | Ücreti veli öder, en fazla 9 taksit: [Servis Usul ve Esasları EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) |
| KE-2 | Arz bedelinin "üçer aylık dönemleri" nereden başlar? | Takvim çeyreği; sözleşmede peşin ödeme seçeneği | [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) başlangıcı söylemez (DOĞRULANMADI) |
| KE-17 | md. 17/1-b-4'teki %3 hangi hâlde? | Kiraya verme hâlinde uygulanır | [md. 17/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); yorum |
| KE-18 | Arz vadesi tatil gününe gelirse | Kaymaz; 10'u ve 20'si dâhildir | EK-2 md. 7 "onuncu günü sonuna kadar", md. 17/1 "yirmisine kadar" |
| KE-3 | Pay hesabında kuruş artığı | İl ve ilçe payı kuruşa yuvarlanır; birlik payı net tutardan ikisi çıkarılarak bulunur (OYS artığı il payına yazıyordu) | Dağıtım kuralı mevzuatta yok (DOĞRULANMADI); birliğin payı toplamı tutturur |
| KE-13 | Büyükşehir olmayan il merkezindeki %20'nin tabanı | Arz bedeli düşüldükten sonraki net tutar | [md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) "gelirin %20'si" der; yorum |
| KE-4 | Gecikme zammı | Hesaplanmaz; oran ve tutar elle girilir, bilgi notu | 6183 md. 51 korpusta yok |
| KE-6 | Kantinde 5 yıllık sözleşme ve 20 yıllık toplam süre sınırı | Uyarı + gerekçe, sert değil | [md. 21](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), Genelge 2024/35; altın kural 3 |
| KE-7 | Danıştay'ın yürütmesini durdurduğu EK-2 ibaresi | Basılan sözleşmeye girmez; yerine kararın künyesiyle dipnot | EK-2 korpus notu (Danıştay 8. D., 24.02.2026, E.2024/369) |
| B-6 | `EMANET` alt hesabı (nakit kesin teminat, aktarılacak il/ilçe payları) | Eklenir (T4'teki banka, kasa, şartlı bağışa ek). Giriş ve çıkış ayrı yönlü kayıttır (`EMANET_GIRIS`/`EMANET_CIKIS`), TEFBİS listesine gelir ya da gider diye girmez (TEFBİS'teki karşılığı DOĞRULANMADI); çıkış yolları B-14'te | Birliğin olmayan parayı ayrı izlemek denkliği korur (MB-7) |
| B-14 | Kantinde fesihte kesin teminatın akıbeti: md. 22/4'teki "taahhüdünü yerine getirmeme" ile EK-2 md. 7'deki ödememe feshi örtüşüyor; mahsup edilecek "birliğin alacakları" neyi kapsar; md. 22/1 ve EK-2 md. 15 fesihlerinde teminat ne olur? | Ödememe feshinde özel hüküm EK-2 md. 7 uygulanır: birliğin alacağı kadar mahsup (gelir), kalan iade. "Birliğin alacakları" = birliğin ödenmemiş aylık payları ve sözleşmeden doğan öteki birlik alacakları; il/ilçe payları ve arz kiracının doğrudan yükümlülüğüdür, mahsuba girmez (yorum, DOĞRULANMADI). md. 22/4 ve EK-2 md. 22/2 hâllerinde gelir kaydı + cari dönem kira tazminatı. md. 22/1 ve EK-2 md. 15 fesihlerinde yol kullanıcıca seçilir, uyarı + gerekçe (§5.2.5, §7.6) | [md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22); [EK-2 md. 7, 8, 15, 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7); [md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) (MB-7) |
| B-15 | Makbuz koçanları md. 23/2'deki "diğer defter ve belgeler" il/ilçe MEM tasdikine tabi mi? | Tasdik alanları isteğe bağlı; boşken yalnız bilgi; kapanış denetiminde bilgi satırı; E22'de isteğe bağlı tasdik sütunu (§5.2.6, §7.5, §7.8) | [md. 23/1-e, 23/2, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); TKB E.4 §3.1; GNL-OAB-FR-015'te sütun yok (MB-13) |
| B-18 | Geçiş kurulumunda açılış bakiyesi hangi güne ait? | Okul seçer. Öneri: **dönem başı** (son olağan genel kurul günü) — banka hareketleri o günden içe aktarılır, kesin hesap ve dönemlik duyuru tam çıkar; banka dökümü dönem başından alınamıyorsa **programa başlama günü** — aradaki gelir-gider toplamı defterden ya da TEFBİS'ten kanıtıyla tek satır girilir (§7.9) | Saha: pilot okulda beta 2026-2027 dönemine paralel (§14 F7) (SU-4) |
| KE-23 | Programın hesapladığı değerde sertlik (D1) gerçek kaydı engeller mi? | **Engellemez:** hesap paketteki değerle yapılır, fiilî ödeme ya da tahsilat olduğu gibi kaydedilir, fark aynı kural kimliğiyle uyarı + gerekçe | D1'in uygulaması; K1 (banka hareketi reddedilemez) |
| B-1 | TEFBİS'in dönem esası (takvim yılı mı öğretim yılı mı) | Program dönem zorlamaz; liste ve mutabakat tarih aralığıyla çalışır | DOĞRULANMADI (ön değerlendirme §2.5) |
| B-3 | Kapanışta eşlenmemiş banka hareketi | **Sert:** dönem kapanmaz. Geçiş kurulumu yapılmış ilk dönemde kapanış denetimi hareketleri programa başlama gününden sonrası için arar (§7.8, §7.9) | Hesap bütünlüğü (altın kural 3) |
| B-4 | Kapanışın geri alınması | Geri alınamaz; düzeltme açık dönemde "önceki dönem düzeltmesi" ters kaydıyla | Altın kural 4 |
| A-10 | Süre hesapları (S-18) | Takvim günü/iş günü ayrımı kural paketinde; yıl hesabı tarih aritmetiğiyle (5 × 365 değil); iş günü için ailenin tatil takvimi; gecikme zammı hesabı yapılmaz, yalnız bilgi (6183 korpusta yok) | Altın kural 1-2 |
| A-11 | Küçük alım tutar sınırı (saha 6) | **Okul ayarı**: dönem başı YK genel kararıyla girilir; sınırın altında talep/komisyon halkası eksikse uyarı + gerekçe (genel karar no'suna bağlı toplu gerekçe), sınırın üstünde zincir tam beklenir. Sınırın altında genel karar kapsamındaki alım için tek ekranlık kısa yol (§7.4); sürekli ödemeler tek dosyada (R6) | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) her harcamada karar, talep ve komisyon öngörür; sınır mevzuatta yok (§3.3) |
| A-12 | Gelir-gider defteri baskısının sütunları | Tarih, sıra no, belge türü ve no, açıklama, gelir, gider, kalan, karar no, gelir-gider türü | Saha 1b; Yönetmelik biçim koymaz ([md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| A-13 | Gelir-gider defterinin bilgisayar çıktısı sayfalarla önceden tasdiki (F0-5a) | Program yalnız deftere **geçirilecek** baskı üretir; çıktı sayfaların tasdiki okulun il/ilçe MEM'le çözeceği konu | F0-e |

### 15.4 Kayıt, KVKK, saklama

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| A-8 | Organ ve kişi kayıtlarında yumuşak silme (S-22) | Mali kayıtlar **yalnız ters kayıtla** düzeltilir; organ ve kişi kayıtlarında "pasif" durumu (silme yok), denetim izinde | Altın kural 4 |
| B-11 | Genel kurul katılım kaydının ne kadarı saklanır? (T5 ile birlikte) | Kalıcı ve kişisiz: imzalayan üye sayısı ve türe göre dağılımı, velisi katılan öğrenci sayısı, o günkü mevcut, dondurulmuş yeter sayı ve sonucu. Basılan cetvelin `GeneratedDocument` izi (sha256). Adlı cetveli ve sınıf teslim çizelgesini yalnız `yonetici` basar; program dosyalarını saklamaz, yalnız iz satırı (R9). Kişi düzeyindeki "katıldı" işareti veli listesiyle silinir; imzalı cetvel taranmaz, aslı genel kurul tutanak dosyasında | [md. 23/1-a, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); katılım sayısı yeter sayının girdisidir, gerekçeli düzeltme satırı dışında değişmez (§5.4) |
| B-5 | Kiracı, kantin çalışanı, servis şoförü ve rehber personel belgeleri; istekli iletişim bilgisi | Tarama alınmaz; "görüldü" tarihi ve geçerlilik sonu tutulur. Tarama eklenirse sözleşme sonu + okul ayarı `scan_retention_years` (öneri 2 yıl; DOĞRULANMADI; kural paketine girmez) sonra imha adayı. İstekli iletişimi **ayrı kuraldır**: seçilmeyeninki süreç sözleşmeyle ya da iptalle kapandıktan sonraki ilk dönem kapanışında, sözleşme tarafınınki sözleşme bitiminden sonraki ilk dönem kapanışında boşaltılır (§5.4) | [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) belgeleri birliğe saklatır; saklama süresi DOĞRULANMADI |
| B-7 | Kişinin telefonu | **Alan yoktur:** `OabPerson.phone` kaldırıldı — programda amacı yok (SMS ve e-posta gönderilmez, hiçbir evrakta telefon yok). İsteklinin iletişim bilgisi B-5'tedir | Veri en aza ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4)); KM-7 |
| B-8 | Bağışçı T.C. kimlik no'su (K9 açıksa) | Dönem kapanışında boşaltılır; kör indeksi yok; hiçbir dışa aktarım dosyasına girmez. E20'de yalnız "kimlik no kayıtlı: evet/hayır", E18'de "kimlik no kaynağı" sütunu | K9; KM-14 |
| B-9 | Erişim günlüğünün saklama süresi | 2 yıl; model §4.6.4; silme kilit açıkken gün işiyle | DOĞRULANMADI |
| B-16 | Kantin isteklisinin katılım engeli dayanağı ile kiracı ve çalışan belgelerinin (adli sicil, portör) "görüldü" kaydı KVKK md. 6/3'ün hangi şartına dayanır? | İçerik hiç tutulmaz; açık alanda yalnız "engel var/yok" ve belge türü-tarih; dayanak şifreli, erişim günlüklü, arşiv paketine girmez, süreç kapanınca boşaltılır; soru kılavuzda okul müdürlüğüne açık soru; md. 6/4 Kurul kararı korpusta yok (§3.4, §5.2.9, §5.4) | [KVKK md. 6/1, 6/3, 6/4](../mevzuat/6698-kvkk.md#madde-6); dayanak hükümler yönetmelik ([md. 20/7, 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); işveren kiracıdır (KM-3, KM-7) |
| M-13 | e-Okul'dan alınan veli adlı katılım cetveli [BSG Yön. md. 5/8](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-5) ("velilere ait kişisel bilgileri … 3. şahıslar ile paylaşamaz") karşısında nasıl uygulansın? | **(a)** R9 sınırlarıyla: adlı E07/E08'i yalnız `yonetici` basar, dosyası saklanmaz; cetvel sınıf başına ayrı sayfa, imza masasında görevli elinde, "Kişisel veri içerir" dipnotlu, imzadan sonra genel kurul tutanak dosyasına; birliğin "3. şahıs" sayılıp sayılmadığı veri sorumlusu sorusuyla (F0-e (b), KE-20) kılavuzda okul müdürlüğüne açık soru. Öteki seçenekler: (b) adlı cetvel yalnız MY'nin elinde, genel kurulda boş satırlı cetvel; (c) md. 5/8'in son cümlesine göre il/ilçe yoluyla görüş | T5; [BSG Yön. md. 5/8](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-5), [6/7](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-6); birlik okul bünyesinde kurulur ([Yön. md. 5/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-5)) — yoruma açık (KM-4; §3.4) |
| B-10 | Yıl sonu arşiv paketinin korunması | AES-256 şifreli ZIP (`pyzipper`, §11 B20 — ADAY, F4); parolayı kapanışta yönetici belirler | Arşiv kişisel veri taşır; programsız açılabilmeli |

### 15.5 Mimari ve güvenlik

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| M-1 | Kurulum yetkisi | Kurucu iki seçeneği sunar (`lowest` + `dialog`). Tek kullanıcılı senaryoda (MY kendi Windows hesabında) kullanıcı başına kurulum; ortak "OAB" Windows hesabında (M-8) yönetici kurulumu — Program Files standart kullanıcıya salt okunur | Kullanıcı başına kurulumda program dosyaları o Windows hesabınca değiştirilebilir (§4.3 tehdit 20; TK7) |
| M-2 | Dönem devrinde veri anahtarını (DEK) yenileme | **Yapılır** (F4): hesap geçişinde (eski organ hesapları kapanınca, yenileri açılmadan önce) ve MY değişiminde; yeni kurtarma anahtarı okul müdürlüğünde mühürlü zarfta (D3); eski zarf, yeni anahtarla alınan tam yedek açılıp doğrulandıktan sonra imha tutanağıyla yok edilir (§9.7 program belgesi); yenilemeden önceki yedekler (USB'dekiler ve `pre-dek-yenileme` dâhil) böylece açılmaz olur — kapanmış dönemin okunabilir kaydı arşiv paketidir. Daha uzun bir bekleme (ör. yerel eski yedekler rotasyondan çıkana dek 14 gün) istenirse bu satır değişir | Kapanan hesapların ve eski kurulun bildiği her şeyin sonraki veriye erişimini keser (§4.4.4, §4.4.6-2) |
| M-3 | Boşta kilit süresi | 10 dk (ayar 3-30); mutlak oturum süresi yok | Ortak bilgisayar; Kütüphane'nin görevli/yönetici kipi yerine tek oturum |
| M-4 | Parola politikası | En az 8 karakter (sert); karışık yapı ve en geç altı ayda bir değişim zorunlu | [BSG Yönergesi md. 9/2-a, b, ç](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9); velilerin Yönergedeki kapsamı yorumdur |
| M-7 | Görevsiz YK asıl üyeleri ve yedekler hesap alsın mı? | Hayır (v1) | Saha 10: programı çoğunlukla MY kullanır |
| M-8 | Ayrı, yönetici yetkisi olmayan "OAB" Windows hesabı | Kılavuzda öneri, zorunlu değil; [BSG Yön. md. 7/2, 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) ve [9/2-e](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9)'den sapma kılavuzda açık yazılır. Kılavuz maddesi: ortak hesabın parolası yalnız görevdeki kurul üyelerinde ve MY'de olur, hesap geçişinde MY değiştirir; bu hesapta program yönetici kipinde kurulur (TK7) | Okul bilgisayarının yönetimi okulun işidir (§4.5) |
| M-12 | Organ ve müdür hesabında ardışık hatalı parola denemesi hesabı askıya alsın mı? | **Evet:** 10 ardışık hatada askı, `yonetici` açar; `yonetici` hesabında askı yok (kurtarma anahtarı yolu kalır); kademeli gecikme hesap başına | [BSG Yön. md. 7/3](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) (üst üste hatalı girişte hesabın geçersiz kılınması, üst yetkilinin yeniden etkinleştirmesi) ve [9/2-c](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) kıyasen; sayı Yönergede Başkanlığa bırakılmış, 10 öneridir (GA-15) |
| M-9 | Herkese açık README'de köken cümlesi | Yazılmaz | Kamuya açık metinde kurum ve kişi bilgisi yok (§17) |
| M-10 | e-Okul'da veli adını taşıyan rapor | DOĞRULANMADI (sınıf listesi raporu veli adı taşımıyor); sentetik örnekle ilerlenir, gerçek rapor gelince "F1 eki" | T5 |

---

## 16. Riskler

| # | Risk | Karşı önlem |
|---|---|---|
| R1 | **Çift iş algısı:** defter + TEFBİS + program üçüncü kayıt gibi görünürse kullanılmaz | Program defter baskısını ve TEFBİS listesini **üretir**, iş azalır; banka dökümünden başlayan kayıt (saha 3); F7'de ölçülür: MY'nin aylık işi programla ve programsız karşılaştırılır, beta paralel yürütmesi ek elle kayıt doğurmaz (§14) |
| R2 | **Konumun yanlış anlaşılması:** "program resmî defterdir" sanılması | Her çıktıda konum ibaresi; kılavuzda md. 13/5, 23/2, 23/5 (§3.1) |
| R3 | **Mevzuat değişikliği:** Yönetmelik 2012'den beri beş kez değişti; TEFBİS işlem tipleri değişiyor | Kural paketi + korpus + atıf kilidi; TEFBİS eşleme tablosu okulca güncellenir |
| R4 | **Okul türü çeşitliliği ve tek saha:** gönüllü okul aranmayacağı için ilkokul/ortaokul, küçük okul ve il merkezi farkları sahada sınanmaz (F0-d) | Bu farklar okul kartından okunan kurallardır; kural testleri ve uydurma senaryolarla sınanır (§10); kapsam resmî örgün okullar |
| R5 | **Gönüllü velilerin bilgisayar yetkinliği** | Arayüz MY odaklı (saha 10); velilere sihirbaz, büyük yazı, az ekran; hesap teslim pusulası (E63) ve kılavuzun "yeni kurulun ilk ayı" bölümü (F7); her faz kapısında kılavuz bölümü (§14); panonun açılış görünümü "bu ay sizden beklenenler" ve büyük yazı (§7.10); F7'de veli rollerinin işini yardımsız yapması ölçülür |
| R6 | **Veri kaybı:** tek bilgisayar = tek nokta | Zorunlu yedek hatırlatması, USB'ye şifreli **tam** yedek (ekler ve üretilmiş evrak dâhil, §4.4.7), yıl sonu açık biçimli arşiv |
| R7 | **Bakım yükü:** ailede bir program daha | Ortak iskelet, kural paketi veri, testler OYS'den |
| R8 | **KVKK konumu belirsiz** ve veli listesi (T5) | Veri en aza (iki alan), dönem sonunda silme, erişim günlüğü, kılavuzda açık soru (§3.4) |
| R9 | **Rejim değişebilir** ("mali yetkiler kaldırılsın" tartışması) | Tam ve açık biçimli dışa aktarım; TEFBİS'i besleyen konum değişiklikte değer kazanır |
| R10 | **Vergi tarafı özelgeye dayanıyor** | Bilgi metni olarak `bilgi/`'de; hüküm diye basılmaz (§3.3) |
| R11 | **Geniş ilk sürüm (K4):** kantin ve servis seyrek yaşanır, geç sınanır | Kabul ölçütü pilot okulun gerçek evrakının birebir üretilmesi; beta F4'ten sonra |
| R12 | **OYS kodundaki mevzuat hataları** taşınırken korunabilir (yeter sayı tabanı, dönem sınırı, servis varsayılanı, imza blokları) | Kural testleri koddan önce yazılır (§10); OYS testleri AYNEN alınmadan önce mevzuatla karşılaştırılır |
| R13 | **TEFBİS ve banka şeması örneksiz** (F0-c) | Varsayılan şema; F3 başlamadan pilot okul örneği istenir, gelmezse içe aktarıcı sütun eşleme ekranıyla esnek kurulur |
| R14 | **İskelet sökümü:** Linux Qt kurulumu tepsi dosyasında, "yalnız 127.0.0.1" testleri katalog testlerinde | F1a'da söküm sırası (§13): önce ayır/taşı, sonra sök |
| R15 | **Muhasibin ayda bir gelmesi mali kaydı geciktirir** (mali kayıtları yalnız muhasip girer — D2; saha 1a) | Aylık iş sırası (§7.3): muhasibin ay sonu oturumundaki kayıt girişi → MY'nin TEFBİS ve defter işi; pano, ay sonu yaklaşırken bekleyen dekont sayısını ve muhasip girişini hatırlatır (§7.10); F3'ten önce muhasiple görüşülür |

---

## 17. okulapp.org yayını (ortak alan — bağlayıcı kurallar)

`okulapp.org` birden çok projenin yazdığı **ortak yayın alanıdır**; bağlayıcı kurallar o deponun `CLAUDE.md`'sindeki
"Ortak çalışma düzeni" bölümündedir (29.08.2026 vakası: eski tabandan açılan bir dal canlıyı geri sardı). OAB Defteri
için:

- **Alan sahipliği.** OAB Defteri'nin tek yazarı olduğu alan: `src/data/od-release.json` + `src/pages/oab-defteri/**`
  + `public/oab-defteri/**` (gerekirse `src/layouts/ODLayout.astro`). Bu satır, site sayfası ilk açılmadan önce
  `okulapp.org/CLAUDE.md`'deki alan tablosuna **o deponun oturumunda ve kullanıcı onayıyla** eklenir. Belge arşivindeki
  genel OAB seti (`public/evrak/**`) evrakmotorunun alanıdır; OAB Defteri oraya yazmaz.
- **Taze taban.** Siteye dokunan her oturum `git fetch` + güncel `origin/main` üzerinden başlar, push'tan hemen önce
  yeniden çeker; eski tabandan açılmış dal güncellenmeden birleştirilmez.
- **Yayın kapısı.** Production yalnız `main` push'uyla değişir; Cloudflare Workers Builds "Version command" alanı
  `npx wrangler versions upload` kalır, `deploy` yapılmaz.
- **Commit dili.** Başlık "OAB Defteri: …" ile başlar. Yayın sonrası 1-2 dakika içinde canlı sayfa doğrulanır.
- **İçerik.** Metnin kaynağı uygulama deposundaki `docs/site-icerigi.md` (Kütüphane Defteri deseni). Ekran görüntüleri
  ve örnek evrak "Örnek Anadolu Lisesi" ile, uydurma kişi adlarıyla, uygulama deposundaki bir betikle üretilir. Kamuya
  açık metinde yazarın unvanı ve kurum adı geçmez; program "kaynağı açık" diye tanıtılır (K7).
- **Dağıtım.** İndirme `indir.okulapp.org`, R2 öneki `oab-defteri/`, sürüm kaydı `src/data/od-release.json`; sayfa ilk
  kez F7'de (beta) açılır. Her adım kullanıcı onaylıdır (altın kural 8).
