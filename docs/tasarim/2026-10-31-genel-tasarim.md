# OAB Defteri — Genel Tasarım

*Tarih: 31.10.2026 · Durum: **TASLAK v1** — bağımsız tasarım denetimini (F0-9) bekliyor. Kararlar: ön değerlendirmede
dokuz kullanıcı kararı (K1-K9); F0'da on bir karar (§2.1) ve tasarımın altı açık sorusu (§15.1) kullanıcıya soruldu;
kalanlar varsayılanla ilerler (§15.2-§15.5). Dayanaklar:
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
kullanır; başkan, muhasip ve sekreter ayda bir kendi işleri için girer; Denetleme Kurulu her şeyi okur ve yalnız
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
| K2 | Kurulum ve kullanıcılar | Okulda **tek bilgisayar**, rol bazlı yerel hesaplar. Denetleme Kurulu her şeyi okur, **yalnız denetim modülüne** yazar; okul müdürü her şeyi okur, **yalnız kendi yazılarını** (harcama talebi md. 18/1, uyarı md. 27/3, yeni okulda genel kurul daveti md. 9/1, olağanüstü genel kurul çağrısı md. 9/6 — §15.1 M-5) yazar; DK'nin md. 14/5 çağrısı denetim modülündendir (§15.1 M-6) | — |
| K3 | Bordro ve personel | Bordro **yok**; personel için özlük, yıllık izin, kıdem karşılığı (sürüm 2). Çalıştırma biçimi **okula göre**: okul kartında doğrudan işveren · hizmet alımı · çalıştırmıyor; personel modülü yalnız doğrudan işverende açılır | — |
| K4 | Kantin ve servis | **İlk sürümde**; birliğin ve okulun evrakı ve takibi, komisyon kararının yerine geçmez | **evet** (öneri sürüm 2-3 idi) |
| K5 | Makbuz | **Basılmaz**; ciltli koçanın envanteri ve yaprak kaydı | — |
| K6 | TEFBİS | Giriş listesi + TEFBİS Excel çıktısıyla mutabakat; **otomatik giriş yok** (teyit 31.10.2026) | — |
| K7 | Lisans | **PolyForm Noncommercial 1.0.0**; kamuya "kaynağı açık" diye tanıtılır | — |
| K8 | Ad | **OAB Defteri**; site `okulapp.org/oab-defteri` | — |
| K9 | Bağışçının T.C. kimlik no'su | **Varsayılan kapalı**, ayardan açılır (yalnız bağışçı alanı, şifreli, maskeli) | — |
| T1 | Hesaplar ve şifreleme anahtarı | **Kişisel hesaplar** (Argon2id); veri anahtarı her hesap için ayrı sarılır, kurtarma anahtarı yönetici kipinde | — |
| T2 | Evrak hattı | **Tek içerik, iki çizici**: Word `python-docx`, PDF ailenin WeasyPrint hattı; LibreOffice/Word gerekmez | — |
| T3 | Birlik dönemi | **Genel kuruldan genel kurula**; ders yılı ve TEFBİS dönemiyle eşlem tablosu | — |
| T4 | Hesap modeli | **Basit hesap planı** (banka, kasa, şartlı bağış alt hesabı), TEFBİS işlem tipine eşlemli; çift taraflı muhasebe değil | — |
| T5 | e-Okul verisi | **Personel** (ad-soyad, görev) **+ veli listesi** — veliden yalnız ad-soyad ve öğrencinin sınıfı; telefon, adres, T.C. kimlik no, öğrenci no alınmaz; liste dönem kapanışında silinir | **evet** (öneri yalnız personeldi) |
| T6 | Pencere | Çarpı **programı kapatır**; tepsi ve otomatik başlatma yok | — |
| F0-a | Kantin arz bedeli vadesi | Sözleşmedeki **izleyen ayın 10'u** ([EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7)) esas, Yönetmelikteki **20'si** ([md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) üst sınır; iki tarih kural paketinde ayrı kural | — |
| F0-b | Sert engeller | Sert engel yalnız hesap bütünlüğünde ve **hukuken geçersiz işlemde**: kantin isteklisinde suç ve hısımlık engeli, mülki amir onayı (OLUR) olmadan kesinleştirme. Eksik belge, taksit sayısı, puan sınırı uyarı + gerekçe (CLAUDE.md altın kural 3) | — |
| F0-c | TEFBİS ve banka örnekleri | Sonra gelecek; tasarım varsayılan şemayla (§8), örnek gelince "F1 eki" | — |
| F0-d | Saha | Yalnız pilot okul; gönüllü okul aranmaz. Pilot okul görüşmesi yapıldı ([saha.md](../kesif/saha.md)) | **evet** (öneri 2-4 gönüllü okuldu) |
| F0-e | İl/ilçe MEM'e sorular | Sorulmaz; varsayılanlar: (a) program tasdikli deftere geçirilecek baskı üretir, (b) veri sorumlusu sorusu kılavuzda okul müdürlüğüne bırakılır, (c) internet bankacılığında üçüncü onay okul ayarıdır, (d) okul kendi TEFBİS işlem tipi listesini girer | — |

### 2.2 Teknik kararlar

*Bu tablo bu belgenin önerisidir; itiraz edilebilir. Kimlikler **TK-n**'dir (plan §1.3'teki T1-T6 kullanıcı
kararlarıyla karışmasın diye). "Durum" sütunu: **Kesin** = bağlayıcı bir kullanıcı ya da aile kararının teknik
karşılığı · **Öneri** = bu belgenin önerisi · **§15 (M-n)** = kullanıcıya açık karar, yazılı varsayılanla ilerlenir.*

| # | Konu | Karar | Gerekçe | Durum |
|---|---|---|---|---|
| TK1 | İskelet | Kaynak Kütüphane Defteri `origin/main` 9a3829d. Dosya düzeyi harita §12.B'dedir; değişen her dosya UYARLA sınıfındadır; haritada olmayan "iyileştirme" yapılmaz | Ailenin en güncel iskeleti: Linux zinciri PySide6 (PyQt5 + PolyForm NC aynı pakette dağıtılamıyordu), lisans dizini, saha kabul protokolü, Debian provası ([plan](../plan/2026-10-31-f0-f1-plani.md) F0-7) | Kesin |
| TK2 | Katmanlar | Django 5.1.15 + DRF 3.15.2, SQLite (WAL, `synchronous=FULL`, `secure_delete=ON`), Python 3.12 · React 18 + TS + Vite + Tailwind (aile kiti) · servis katmanı baştan alt modüllere bölünür · OpenAPI yok, tipler elle · tek yazar + `IMMEDIATE` işlem | Aile kararları (Kütüphane T12, T13, T15, B13). Ölçek küçük: yılda ~400-500 banka hareketi ([ön değerlendirme §6](../kesif/2026-10-31-on-degerlendirme.md)) | Kesin |
| TK3 | Süreç ve ağ | Tek süreç, tek dinleyici: waitress yalnız `127.0.0.1`'de, rastgele portta, oturum belirteciyle. **Ağ servisi yoktur**; ikinci dinleyici, güvenlik duvarı kuralı, Ağ Doktoru yoktur | K2 (tek bilgisayar) ağ erişimi gerektirmez. Okul ağına port açmak [BSG Yön. md. 11/7](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11) ("aktif ağ cihazı") ve 11/22 (port yönetimi Başkanlıkta) tartışmasını doğururdu; Kütüphane'nin bu bedeli ödeme gerekçesi (ağ kataloğu) burada yok | Kesin |
| TK4 | Dış istek | Tek kapı: kullanıcının başlattığı "Güncellemeyi denetle" — GitHub Release (`api.github.com`), kurulum dosyası `github.com`'dan, SHA-256 doğrulamalı; ulaşılamazsa dürüst ileti ve elle indirme alanı. Açılışta ağ yok, telemetri yok, dışarı kişisel veri çıkmaz | Aile T11 (ISBN künye kapısı ALMA). [BSG Yön. md. 11/23](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-11) bulut depolamaya veri aktarılmaz. Koruma: `test_dis_istek_kapilari` (kaynak), `test_acilista_dis_istek` (gerçek açılış, ağ tuzağı) | Kesin |
| TK5 | Pencere | T6: çarpı programı kapatır; tepsi, `--tepside`, otomatik başlatma, uyku engeli yoktur. Tek kopya kanalı, temiz kapanış işareti, WAL checkpoint, Linux SIGTERM köprüsü kalır; Linux Qt kurulumu `desktop/qt_kurulum.py`'ye taşınır (§4.5) | T6 kullanıcı kararı; Kelebek Sınav davranışı, Kütüphane'nin kazanımlarıyla ([iskelet envanteri §9.3](../kesif/2026-10-31-iskelet-envanteri.md)) | Kesin (T6) |
| TK6 | Paketleme | Windows: PyInstaller onedir + Inno Setup · Linux: `.deb` + taşınabilir `.tar.gz`, Debian 11 (bullseye, glibc 2.31) kabında derleme · PySide6 6.8.3 tavanı · kurulum provası Debian 11/12/**13** | Pardus 21/23/25 (Pardus 25 Debian 13 tabanlı); TB27 tavanı; TB5 | Kesin + Debian 13 eki |
| TK7 | Kurulum yetkisi | `PrivilegesRequired=lowest` + `PrivilegesRequiredOverridesAllowed=dialog`: varsayılan kullanıcı başına kurulum (`{autopf}` → `%LOCALAPPDATA%\Programs`), BTR isterse aynı kurucuyla yönetici kurulumu (Program Files) | Kütüphane'de her kurulum ve güncellemenin yönetici istemesinin (U4, TB7) ana gerekçesi güvenlik duvarı kuralıydı; OAB'de kural yok. MY güncellemeyi BTR'siz kurabilir. Risk: AppLocker/SRP kullanıcı dizininden exe çalıştırmayı engelleyebilir (doğrulanmadı; F7 sahada) | §15 (M-1) |
| TK8 | Güvenlik çekirdeği | Aileden aynen: Argon2id (RFC 9106 düşük bellek profili, ~0,2 sn), Fernet alan şifrelemesi, kör indeks, fail-closed yazma (`KeyMissingError` → 409 `parola_gerekli`), güvenlik dosyası kayıp kilidi, X25519 + AES-256-GCM şifreli yedek (`Connection.backup()`), kademeli gecikme (kalıcı kilit yok). Şifrelenecek alanların **listesi** §5'tedir | [KVKK md. 12/1](../mevzuat/6698-kvkk.md#madde-12) teknik tedbir; [BSG Yön. md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) taşınabilir ortamda şifreleme; Kütüphane'de kapalı denetim bulguları (TB26) | Kesin |
| TK9 | Hesaplar | T1: kişisel hesaplar; veri anahtarı (DEK) her hesap için ayrı sarılır; rol ve organ bağı veritabanında; kurtarma anahtarını yalnız `yonetici` yeniler (§4.4) | T1 kullanıcı kararı; [BSG Yön. md. 7/2, 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) (kullanıcı adı ve şifre paylaşılmaz, herkes kendi hesabıyla çalışır) | Kesin (T1) |
| TK10 | Yedek başlığı | Şifreli yedeğin başlığı **yalnız kurtarma bölümünü** taşır; hesap sarmalları yedeğe girmez. Aynı bilgisayarda geri yükleme güncel `guvenlik.json` + hesap parolasıyla, yeni bilgisayarda kurtarma anahtarıyla açılır | TB23 OAB'de ağırlaşır: dönemi biten veli üyenin eski parolası + eski yedek başlığı → DEK. Bedel: yeni bilgisayara taşıma kurtarma anahtarı ister — bu zaten yönetici işidir | Öneri |
| TK11 | Kapanan hesap | Hesap kapanınca sarmalı `guvenlik.json`'dan **ve bütün `guvenlik-arsiv-*` kopyalarından** silinir; `Hesap` satırı (rol, tanıtıcı, kapanış tarihi) denetim izi için kalır | Arşiv kopyasında sarmal kalırsa kapatma anlamsızdır (TB17/TB23); satırın kalması altın kural 4 | Öneri |
| TK12 | DEK yenileme | Dönem devrinde (devir-teslim akışının bir adımı, F4) DEK yenilenir: şifreli alanlar, kör indeksler, parmak izi, yedek anahtar çifti ve denetim izi mührü yeni DEK'le; yeni kurtarma anahtarı basılır, devir dosyasına girer | Eski kurulun bildiği hiçbir şey (parola, eski başlık, arşiv) yeni dönemin verisini ve yedeğini açmaz. Kütüphane v1 dışı bırakmıştı (TB17, TB23); OAB'de veri hacmi küçük ve dönem devri zaten bir iş akışıdır | §15 (M-2) |
| TK13 | Rol izinleri | Sunucu tarafında uç + yöntem matrisi (`rol_izinleri.py`), yeni uç varsayılan kapalı, URL desenlerini dolaşan koruma testi; ret 403 `{"code":"rol_yetkisiz"}`. Rol kriptografik değildir: kaza önleyici + izlenebilirlik | Kütüphane görevli kipinin deseni (`kip_izinleri`, `test_kip_koruma`); [iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md) risk 1 | Öneri |
| TK14 | Oturum | Süreç içi tek oturum (`OturumDurumu`, tek nesne); kullanıcı değiştirmek = Kilitle + başka hesapla aç; boşta süre dolunca **kilit** (görevliye iniş yok); varsayılan 10 dk (ayar 3-30); mutlak süre yok | [BSG Yön. md. 10/2](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10) kullanılmayan bilgisayarda parolalı kilit (süre vermez). Görevli kipi olmadığından Kütüphane'nin 30 dk mutlak süre gerekçesi düşer; 3 dk velinin yavaş yazdığı formda can sıkar | §15 (M-3) |
| TK15 | Parola politikası | En az 8 karakter (sert) · küçük harf, büyük harf, rakam ve simge (varsayılan sert) · 180 günü geçen parola girişte değiştirilir · ilk girişte geçici parola değiştirilir | [BSG Yön. md. 9/2-a, b, ç](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9). Yönergenin "kullanıcı" tanımı Bakanlık bilişim kaynağını kullanma yetkisi verilen konukları da kapsar ([md. 2/1, 4/1-j, k](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)) — veli kullanıcı için yorum | §15 (M-4) |
| TK16 | Denetim izi | Her yazma `DenetimIzi`'ne hesap + rol + zaman (Europe/Istanbul) ile düşer; ekleme-yalnız. Satırlar kaydın özetini taşır ve HMAC zinciriyle mühürlenir (anahtar `HKDF(DEK, "od-denetim-izi")`); DK modülünde "kayıt bütünlüğü denetimi" | Altın kural 4; Kütüphane'de `AuditLog` bilerek yoktu ([iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md)). Zincir, program dışından SQLite'ta düz alan değiştirilmesini görünür kılar (§4.3 tehdit 7) | Öneri; model §5 |
| TK17 | Evrak hattı | T2: tek içerik modeli, iki çizici. PDF: `shared/pdf.py` (aile tek kapısı, WeasyPrint, süreç kilidi). Word: `shared/docx.py` (python-docx tek kapısı). Cephe: `shared/evrak.py` (belge tanımı + bağlam → içerik → {pdf, docx}). LibreOffice/Word gerekmez. PDF ↔ Word içerik eşdeğerliği testi (pypdf metni ↔ python-docx metni); `w:caps` kullanılmaz, büyük harf `tr_upper`'dan; `--evrak-duman` (çıkış 12). İçerik modeli ve katalog §9'da | T2 kullanıcı kararı; [iskelet envanteri §7.2](../kesif/2026-10-31-iskelet-envanteri.md) ekleme noktası | Kesin (T2); yerleşim öneri |
| TK18 | İçe/dışa aktarım güvenliği | İçe alınan dosya (banka özeti, e-Okul listesi, TEFBİS Excel) güvenilmeyen girdidir: boyut tavanı (`OD_MAX_UPLOAD_SIZE_MB`), yalnız `.xlsx`/`.xls`/`.csv`, makrolu biçim reddi, türü imza baytından denetim, openpyxl `read_only` + `data_only`, önizleme + onay. Dışa yazılan xlsx'te dış kaynaklı metin hücreye **metin tipiyle** yazılır. `python-magic` eklenmez | openpyxl `=` ile başlayan dizeyi formül sayar; banka açıklaması dış kaynaklıdır (formül enjeksiyonu). libmagic Windows'ta ayrı DLL ister ([OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) S-26) | Öneri |
| TK19 | Periyodik işler | Celery yok. Gün değişimi kapısı (`od-gunluk`; açılışta + saatte bir): günlük yedek + 14 gün rotasyonu; sonraki fazların işleri kayıt defterine eklenir. Bakım kapısı `katalog/bakim.py`'den `shared/bakim.py`'ye taşınır | Aile T9. Bakım kapısı bugün katalog paketindedir; katalog sökülünce sessizce devre dışı kalır (§13 D3) | Öneri |
| TK20 | `SECRET_KEY` | Sabit kalır; program imza, Django oturumu ve CSRF kullanmaz | Aile T17 | Kesin |
| TK21 | Kimlik | Kimlik sabitleri §2.3; kalıntı taraması F1a kapısıdır | Plan §1.4 | Kesin |

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
| Ortam değişkenleri | `OD_SESSION_TOKEN`, `OD_DEBUG`, `OD_APP_VERSION`, `OD_APP_HOME`, `OD_DATA_DIR`, `OD_SECURITY_DIR`, `OD_BACKUP_DIR`, `OD_BACKEND_DIR`, `OD_FRONTEND_DIR`, `OD_RTHOOK_UYARI`, `OD_ONCEKI_OTURUM`, `OD_SECRET_KEY`, `OD_MAX_UPLOAD_SIZE_MB`, `OD_UPDATE_REPOSITORY`, `OD_WITH_QT`, `OD_DLL_DIR`, `OD_SKIP_PIP`, `OD_BUILD_IMAGE`, `OD_AG_TUZAGI_KAYIT` | `KD_*` (25 ad) | ALMA: `KD_KATALOG_PORT`, `KD_KATALOG_HOST`, `KD_PROVA_ESER`, `KD_EKRAN_DERLE`, `KD_YAVAS`. `OD_UPDATE_REPOSITORY` yalnız geliştirme ve test içindir |
| Veri dizini | Windows `%LOCALAPPDATA%\OABDefteri` · Linux veri `~/.local/share/oab-defteri`, günlük `~/.local/state/oab-defteri`, önbellek `~/.cache/oab-defteri` | `KutuphaneDefteri` / `kutuphane-defteri` | `%APPDATA%` (gezici profil) ve `ProgramData` seçilmez (§4.5) |
| **Oturum, ön yüz** | | | |
| Oturum çerezi / başlığı | `od_oturum` / `X-OD-Token` | `kd_oturum` / `X-KD-Token` | |
| Etkinlik başlığı | `X-OD-Etkinlik` | `X-KD-Etkinlik` | Boşta kilit (TK14) yalnız bu başlığı taşıyan istekle tazelenir |
| Ret kodları | 403 `rol_yetkisiz` · 423 `locked`, `guvenlik_dosyasi_kayip` · 409 `parola_gerekli` · 503 `restart_required` | 403 `kip_yetkisiz` | `rol_yetkisiz` yenidir (T1); ötekiler aynen |
| DOM olayları | `od:kilit-kapisi`, `od:rol-yetkisiz`, `od:yeniden-baslat-gerekli`, `od:guncelleme-denetlendi` | `kd:*` | `kd:cik-iste` ALMA (T6); `kd:kip-yetkisiz` → `od:rol-yetkisiz` |
| CSS | değişkenler `--od-*`; sınıflar `od-page-title`, `od-page-header`, `od-page-description` | `--kd-*`, `kd-page-*` | Sitedeki `od` paletiyle karıştırılmaz |
| Tarayıcı deposu anahtarları | `oab-defteri-density`, `oab-defteri-sidebar-collapsed`, `oab-defteri-dismissed-update`, `oab-defteri-theme` | `kutuphane-defteri-*`, `oys-theme` | `-okuma-sesi` ALMA (barkod); `oys-theme` OYS kalıntısıydı (§13 D13) |
| Ön yüz paket adı | `oab-defteri-frontend` | `kutuphane-defteri-frontend` | |
| Rol kodları | `yonetici`, `baskan`, `baskan_yardimcisi`, `muhasip`, `sekreter`, `denetleme_kurulu`, `mudur` | — (yeni) | Üç bölümün ortak adı (§4.4, §5, §7) |
| **Kripto ve yedek** | | | |
| Yedek uzantısı / MAGIC | `.odbak` / `ODBAK\x02` | `.kdbak` / `KDBAK\x02` | Kap biçimi aileyle aynı; başlık içeriği TK10 ile değişir |
| Yedek HKDF bilgileri | `OABDefteri/backup/private/v1`, `OABDefteri/backup/envelope/v1` | `KutuphaneDefteri/backup/…` | İki dizge |
| Kör indeks HKDF | `od-kor-indeks` | `kd-kor-indeks` | |
| Anahtar parmak izi HMAC | `od-anahtar-parmak-izi` | `kd-anahtar-parmak-izi` | |
| Denetim izi mührü HKDF | `od-denetim-izi` | — (yeni) | TK16; §5 modeli kabul ederse |
| Yedek indirme adı | `oab-defteri-yedek-<damga>.odbak` | `kutuphane-defteri-yedek-<damga>.kdbak` | |
| `guvenlik.json` şema sürümü | `"surum": 2` (hesaplı şema) | 1 | §4.4.4 |
| **Windows** | | | |
| Inno AppId | **yeni GUID üretilecek** | sabit GUID | Kütüphane'ninki asla kullanılmaz; bir kez üretilir, bir daha değişmez |
| Mutex | `OABDefteri`, `Global\OABDefteri` | `KutuphaneDefteri`, `Global\…` | Inno `AppMutex` kullanılmaz (§4.2) |
| Adlı olaylar | `OABDefteri.Goster`, `OABDefteri.Kapat` | `KutuphaneDefteri.*` | |
| AUMID | `OABDefteri.Desktop` | `KutuphaneDefteri.Desktop` | |
| exe / dağıtım dizini | `oab-defteri.exe` · spec `DIST_NAME = "oab-defteri"` | `kutuphane-defteri.exe` | |
| Kurulum dizini | `{autopf}\OAB Defteri` | `{autopf}\Kütüphane Defteri` | TK7 kullanıcı kipinde `%LOCALAPPDATA%\Programs\OAB Defteri` |
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
| Test geçici dizinleri | `od-guvenlik`, `od-yedek` | `kd-guvenlik`, `kd-yedek` | `backend/conftest.py` |
| Güncelleme deposu | `<github-kullanıcısı>/oab-defteri` | `<…>/kutuphane-defteri` | Deponun açılışı yayın işidir (altın kural 8) |
| Site | sayfa `okulapp.org/oab-defteri` (`src/pages/oab-defteri/**`), palet `od`, `src/data/od-release.json`, gerekirse `src/layouts/ODLayout.astro`, varlıklar `public/oab-defteri/**` | `kd`, `kd-release.json`, `KDLayout.astro` | Ortak alan kuralları §17 |
| R2 öneki | `oab-defteri/` | `kutuphane-defteri/` | `packaging/r2-yukle.sh` `R2_ONEK` |

#### 2.3.2 Değişmeyen genel adlar

Program adı taşımadıkları ve veri dizinleri ayrı olduğu için kardeş programlarla çakışmazlar; çevrilmez:
`db.sqlite3`, `instance.lock`, `surum.json`, `guvenlik.json`, `guvenlik-arsiv-<damga>.json`, `yedekleme.json`,
`temiz-kapanis.json`, `gun-kapisi.json`, `kanal.sock`, `cokme.log`, yedek önekleri `gunluk-`, `pre-migrate-`,
`pre-parola-`, `db-onceki-<damga>.sqlite3`, kanal komutları `goster`/`kapat`, kapı nöbetçisi `KAPI_OK_<ad>`.
Yeni yedek öneki: `pre-dek-yenileme-` (TK12). `pre-anonim-` saklama fazına kadar kullanılmaz (§12.B).

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
- **Kapı dışı, uyarı düzeyi:** "alan kalıntısı" listesi (ödünç, nüsha, barkod, ISBN, tepsi, görevli kipi, Ağ Kataloğu,
  künye) F1a-2'de bir kez elle koşulur; "katalog" gibi meşru kullanımlar yüzünden kapıya girmez.

---

## 3. Hukuki konum ve mevzuat

### 3.1 Konum: resmî kayıt defterdir, program hazırlar

| Resmî kayıt | Dayanak | Programın yaptığı | Programın yapmadığı |
|---|---|---|---|
| Yönetim kurulu karar defteri (noter tasdikli, el yazısı) | [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/1-b, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Karar **taslağı** üretir; sekreter deftere yazınca "deftere işlendi" işareti, defter sıra no ve sayfası kaydedilir | Kararı resmîleştirmez; taslak "karar defterine el ile yazılır" ibaresini taşır |
| Gelir-gider defteri (il/ilçe MEM tasdikli) | [md. 23/1-ç, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Tasdikli deftere **geçirilecek** aylık baskı (tarih, sıra no, belge türü ve no, açıklama, gelir, gider, kalan, karar no, gelir-gider türü — saha 1b) | Defterin yerine geçmez; Yönetmelik defterin sütunlarını belirlemez, program asgari sütun setini önerir |
| TEFBİS kayıtları (okul idaresi girer) | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | TEFBİS ekran sırasıyla "girilecekler" listesi; "TEFBİS'e girildi" işareti; sürüm 2'de TEFBİS Excel çıktısıyla mutabakat | TEFBİS'e giriş yapmaz, TEFBİS şifresi saklamaz (K6) |
| Makbuz koçanı (ciltli, seri-cilt-sıra numaralı, mühürlü) | [md. 16/5-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1) | Koçan envanteri, kullanılan ve iptal yaprak kaydı, numara tekilliği | Makbuz basmaz (K5) |
| Genel kurul tutanak dosyası, gelen-giden evrak defteri, harcama dosyası | [md. 23/1-a, c, d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | Tutanak ve yazı taslakları, evrak kaydı, harcama dosyasının dizini | İmzalı aslın yerine geçmez |

**Her çıktıda konum ibaresi.** Karar taslağı, deftere geçirilecek baskı ve TEFBİS listesi, hangi resmî kayda
girileceğini ve programın yardımcı kayıt olduğunu söyleyen bir ibare taşır (biçimi §9). İbare kılavuzda, sitede ve
ilk açılış ekranında da yer alır (CLAUDE.md §1).

**Yardımcı kaydın değeri.** Program kayıtları resmî değildir ama denetimde kanıt sunar: kararın taslağı ile defterdeki
hâlinin tutarlılığı, banka-defter-TEFBİS denkliği (SGB 02.12.2019 yazısının istediği; ön değerlendirme §2.5), sürelerin
tutulup tutulmadığı. Bu yüzden program kayıtları da altın kural 4'e tabidir: silinmez, ters kayıtla düzeltilir,
kapanan dönem kilitlenir, her değişiklik denetim izine yazılır.

### 3.2 Mevzuat korpusu ve kural paketi

- Programın koyduğu her oran, süre, çarpan ve sınır **kural paketinde** durur ve `madde` alanıyla
  `docs/mevzuat/` korpusundaki bir çapaya bağlanır (§6). Çapası olmayan kural paketi yüklenmez (atıf kilidi; §10).
- Korpus [BENIOKU](../mevzuat/BENIOKU.md)'daki protokolle tutulur: resmî kaynaktan birebir metin, şerhler aynen,
  `(Mülga:…)` hüküm yok, `(Değişik:…)` en güncel hâl; her dosyada `oab-teyit` tarihi. 31.10.2026'da 26 metnin 18'i
  mevzuat.gov.tr konsolide metniyle madde madde karşılaştırıldı.
- Mevzuat değişince: korpus güncellenir → değişen madde hangi kurallara dayanak, bakılır → yeni kural sürümü açılır;
  kapanmış dönemler eski sürümle hesaplanmaya devam eder (altın kural 2).
- Yönetmeliğin mülga metinlere iki atfı güncel karşılığıyla gösterilir: md. 18/3'teki eski Taşınır Mal Yönetmeliği →
  [TMY 2024](../mevzuat/tasinir-mal-yonetmeligi.md) (md. 41/2 atıf hükmü); md. 16/7 ve 23/6'daki 1988 arşiv
  yönetmeliği → [Devlet Arşiv Hizmetleri Hakkında Yönetmelik](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md)
  (1988 metnini md. 32 ile kaldırdı).

### 3.3 Üç tür hüküm: kural, bilgi metni, okul ayarı

| Tür | Nerede durur | Örnek | Programda görünüşü |
|---|---|---|---|
| **Kural** (mevzuat hükmü) | Kural paketi, çapalı | Yeter sayı ×4/×2 ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); elden bağış 5 iş günü ([md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)); kantin kirasında KDV yok ([KDVK md. 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17)) | Uyarı + gerekçe ya da sert engel (altın kural 3); madde bağlantısıyla |
| **Bilgi metni** (özelge, sirküler, yorum) | `docs/mevzuat/bilgi/` (F5'ten önce kurulur) | Bağışçının vergi indirimi olmaması; kantini birlik işletirse kurumlar vergisi; tevkifat ([GVK md. 94](../mevzuat/193-gelir-vergisi-kanunu.md#madde-94)) | Bilgi kutusu; hüküm diye basılmaz, evraka girmez |
| **Okul ayarı** (mevzuatta yok, okulun kararı) | Okul kartı / dönem ayarları | Küçük alım tutar sınırı ve sürekli ödemeler için genel karar (saha 6); internet bankacılığında üçüncü onay (F0-e) | "Okul kararı" etiketiyle; mevzuat gereği diye sunulmaz |

### 3.4 KVKK

- **Veri sorumlusu açık soru.** Birliğin tüzel kişiliği yoktur; veri sorumlusunun birlik mi okul/MEB mi olduğunu
  belirleyen Kurul kararı bulunamadı (ön değerlendirme §2.5). Kılavuz soruyu açıkça okul müdürlüğünün
  değerlendirmesine bırakır (F0-e). Masaüstü program, kâğıt kaydın "yalnız otomatik olmayan yollarla işleme"
  istisnasını ortadan kaldırır ([KVKK](../mevzuat/6698-kvkk.md)); aydınlatma metni kılavuzda ve ilk kurulumda.
- **Veri en aza.** Veliden yalnız ad-soyad ve öğrencinin sınıfı (T5), liste dönem kapanışında silinir. T.C. kimlik
  numarası varsayılan kapalı (K9). Suç engeli için ([md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12),
  [14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) yalnız **"beyan alındı"** işareti tutulur; adli
  sicil verisi ve serbest metin beyan notu tutulmaz (OYS'deki alan çıkar — envanter S-20).
- **Saklanması gereken kişisel belge.** Kantin çalışanlarının belgeleri
  ([md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23))
  ve personel belgeleri (sürüm 2; [5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86))
  şifreli dosya olarak, erişim günlüğüyle, saklama süresi kural paketinde (§5.4).
- **Duyuru ve ilan çıktılarında kişi adı yok** (dönemlik gelir-gider ilanı, bütçe duyurusu); bağışçı adı ilanda
  görünmez.
- **Depoya girmez:** gerçek veri, banka özeti, TEFBİS çıktısı, e-Okul listesi (`.gitignore`; F1'de sızıntı kapısı).

### 3.5 Okul türü kapsamı

Kapsam **resmî örgün okullardır**. Kural paketi şu farkları okul kartından okur:

| Fark | Dayanak | Programda |
|---|---|---|
| Öğrenci mevcudu 100'ün altında | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | Yeter sayı çarpanı ×2 |
| Büyükşehir statüsünde olmayan il merkezi | [md. 17/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | Kantin payında il %20; okul kartında üç değerli yerleşim türü |
| İlkokul/ortaokul (OÖEİKY) | [OÖEİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57) | Temsilciler çizelgesinde ortaöğretimdeki kurulların karşılıkları |
| Kantin birlikçe işletiliyor | [md. 17/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | Arz %1; iktisadi işletme bilgi metni |

Kapsam dışı (sonra): özel okullar (md. 15 ve 17 "resmî okullarda" der), yaygın eğitim kurumları (üye tanımı farklı),
kampüs okulları. Pilot okul dışında saha sınaması yapılmayacağından (F0-d) küçük okul ve ilkokul/ortaokul farkları
kural testleri ve uydurma senaryolarla sınanır (§10, §16).

---

## 4. Mimari

### 4.1 Süreç modeli

```
oab-defteri.exe   (tek süreç · tek kopya kilidi · OturumDurumu tek nesne)
├── ana iş parçacığı: pywebview penceresi — çarpı = çık (T6)
│     Windows: WebView2 · Linux: qt_kurulum.hazirla() → PySide6 QtWebEngine + SIGTERM köprüsü
├── od-wsgi    waitress 127.0.0.1:<rastgele> → Django (API + SPA, whitenoise)
│                OturumBelirteci(403) · RestartRequired(503) · AppLock(423) · RolMiddleware(403 rol_yetkisiz)
├── od-kanal   tek kopya kanalı — Windows: OABDefteri.Goster / .Kapat · Linux: kanal.sock (yalnız sahibi)
├── od-gunluk  gün değişimi kapısı: açılışta + saatte bir; her iş bakım kapısından geçer
└── od-cikis   arayüzdeki Çık: HTTP yanıtı gittikten sonra düzenli kapanışı başlatan zamanlayıcı
```

**Değişmezler** (testle kilitlenir):

- Yönetim sunucusu `127.0.0.1` dışında host kabul etmez; `main.py` host vermez. `0.0.0.0` hiçbir üretim kaynağında
  geçmez (tek muafiyet `window.py`'deki WebView2 sürüm damgası). Bu testler bugün `test_katalog_server.py`'dedir,
  `test_server.py`'ye taşınır (§13 D2).
- Paketli yapıda `ALLOWED_HOSTS` yalnız `127.0.0.1` ve `localhost`; `backend` adı yalnız `OD_SESSION_TOKEN` boşken
  (geliştirme, test) eklenir. Oturum belirteci her açılışta rastgele; URL'deki `?t=` → `HttpOnly`, `SameSite=Strict`
  çerez; belirteçsiz istek 403.
- Dış bağlantı yalnız `apps/okul/services/updates.py`'den çıkar (TK4).
- `OturumDurumu` süreç içi tektir: kilit kapısı, `RolMiddleware` ve denetim izi yazıcısı aynı nesneyi okur. Masaüstü
  ile backend arasında tek kanal `masaustu_kanca`dır (çıkış kancası + gün işleri kaydı); katalog denetçisi yoktur.
- Veritabanının tek yazarı vardır: istekler ve `od-gunluk` aynı SQLite dosyasına `IMMEDIATE` işlemle yazar; geri
  yükleme bakım kapısını kapatır, uçuştaki işin bitmesini bekler, sonra dosyayı takas eder (TK19, §13 D3).

**Katmanlar** ([ön değerlendirme §7.2](../kesif/2026-10-31-on-degerlendirme.md)): arayüz (React) → DRF uçları →
servis katmanı (iş akışı, kural motoru, uyarı + gerekçe kaydı) → modeller → evrak (§9) ve içe/dışa aktarım (§8).
**Her yazma servis katmanından geçer**; servis, `OturumDurumu`'ndaki hesabı "yazar" olarak denetim izine verir
(TK16, model §5). Yazar bağlamı olmayan yazma reddedilir; sistem işleri (günlük yedek, göç, dönem kilidi
denetimi) `sistem` yazarıyla düşer.

### 4.2 Açılış ve kapanış

**Açılış** (Kütüphane `desktop/main.py` sırası; katalog, tepsi, uyku ve güvenlik duvarı adımları düşer):

| # | Adım | Başarısızlıkta | Not |
|---|---|---|---|
| 1 | Veri dizinleri (exe dışında) + günlük yapılandırması | 1 | |
| 2 | Tek kopya kilidi (iki mutex + `instance.lock`) | normal ikinci açılış: çalışan kopyanın penceresi öne gelir, ikinci süreç **0** · `--geri-yukle`, `--autotest`, `--pdf-duman`, `--evrak-duman` çalışan kopya bulursa **2** | İleti "OAB Defteri açık. Programı kapatıp yeniden deneyin." — tepsi anlatılmaz |
| 3 | Temiz kapanış işareti okunur ve silinir; tek kopya kanalı kurulur | — | İşaret yoksa panoda "son oturumdaki kayıtları kontrol edin" kartı (T15; okuyucusu §13 D4) |
| 4 | Oturum belirteci (ayarlar okunmadan önce) | — | |
| 5 | Sürüm damgası; damga yoksa göç kaydı denetimi | 4 | Eski program yeni veriyi açmaz |
| 6 | Bütünlük denetimi | 3 | Yedekten **önce**: bozuk veritabanıyla rotasyon sağlam eski yedekleri silmesin |
| 7 | Günlük yedek + 14 gün rotasyonu (yalnız `.odbak`) | günlüğe | İlk hesap kurulmadan atlanır |
| 8 | Göç öncesi yedek (son 5) + `migrate --no-input` | 5 | |
| 9 | waitress `127.0.0.1:<boş port>` + sağlık denetimi | 6 | |
| 10 | Çıkış kancası `masaustu_kanca`'ya kaydolur; `od-gunluk` başlar | — | |
| 11 | Linux: `qt_kurulum.hazirla()` (`QT_API=pyside6`, `QtWebEngineWidgets`'ın `QApplication`'dan önce yüklenmesi, pencere simgesi) + SIGTERM köprüsü | 1 | `tray.py`'den ayrılmış hâli (§13 D1) |
| 12 | Windows: WebView2 denetimi → pencere; ilk açılışta kurulum sihirbazı, sonra kilit ekranı | 7 | |

`--autotest`: 1-10 + sağlık denetimi, pencere açılmaz; katalog adımı yoktur (§13 D5). Kurulum sihirbazının ilk adımı
(ilk yönetici hesabı) bitmeden kişi yazan uçlar 409 `parola_gerekli` döner (aile).

**Kapanış — tek yol.** Kaynaklar: çarpı · arayüzdeki **Çık** (`POST app/quit/`, her oturum durumunda parolasız) ·
kurucu ve kaldırıcının `OABDefteri.Kapat` olayı · kanal komutu `kapat` · Linux SIGTERM (oturum kapanışı). Sıra:
pencere kapanır, `webview.start` döner → kanal → kancalar bırakılır → `od-gunluk` durur → yönetim sunucusu →
**WAL checkpoint** (TB14) → temiz kapanış işareti → kilit (mutex'ler süreç bitene dek kalır).

- Çarpıda onay sorulmaz (T6, Kelebek davranışı). Kaydedilmemiş form kaybı kabul edilen risktir; uzun akışlar
  (genel kurul sihirbazı, harcama zinciri) adım adım sunucuya kaydedilir (§7).
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
| 2 | zaten çalışıyor | 9 | geri yükleme başarısız |
| 3 | veritabanı bozuk | 10 | `--bagimlilik-duman` başarısız |
| 4 | şema bu sürümden yeni | 11 | **ayrılmış** (ailede `--dagitim-duman`; aile hizası için yeniden kullanılmaz) |
| 5 | göç başarısız | 12 | **`--evrak-duman` başarısız** (yeni; docx üret → python-docx ile geri oku → Türkçe örnek ve "İ") |
| 6 | sunucu kalkmadı | | |

### 4.3 Tehdit modeli

**Korunan varlıklar:** birliğin mali kayıtlarının bütünlüğü · kişisel veri (veli adı ve sınıfı, iletişim, IBAN, K9
açıksa bağışçı T.C. kimlik no) · evrakın doğruluğu. **Saldırgan profili:** aynı odadaki kişi, dönemi biten kurul
üyesi, bilgisayara erişimi olan personel, yedeği bulan kişi; uzak saldırganın tek yüzeyi güncelleme kanalıdır.
**Sınır:** program bir izlenebilirlik ve kaza önleme aracıdır; **asıl güvenlik sınırı Windows hesabı ve disk
şifrelemesidir** (BitLocker). Bu cümle kılavuza ve Hakkında'ya girer ([KVKK md. 12/1](../mevzuat/6698-kvkk.md#madde-12)
idari tedbirler okulundur).

| # | Tehdit | Katman | Kalan risk |
|---|---|---|---|
| 1 | Aynı makinedeki başka süreç yönetim API'sine istek atar | Oturum belirteci (fail-closed 403), yalnız loopback, rastgele port | — |
| 2 | Kötü niyetli web sayfası DNS rebinding yapar | Belirteç çerezi `SameSite=Strict`, yalnız WebView2 profilinde; `ALLOWED_HOSTS` | — |
| 3 | Açık bırakılan oturumda başkası işlem yapar (MY masadan kalkar) | Boşta kilit (TK14), Kilitle düğmesi ve kısayolu, her yazma hesapla denetim izinde | Boşta süre içindeki işlem oturum sahibinin adına düşer; [BSG Yön. md. 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7) kilitleme yükümlülüğü kullanıcınındır |
| 4 | Kısıtlı rol (DK, müdür) yetki alanı dışına ya da yetkisiz rol yazmaya çalışır | Sunucu tarafı rol matrisi, yeni uç kapalı, koruma testi (TK13) | Hatalı matris: URL desenlerini dolaşan test yakalar |
| 5 | Dönemi biten ya da görevden düşen üye eski parolasıyla girer ya da eski yedeği açar | Hesap kapanır, sarmal `guvenlik.json`'dan ve arşivden silinir (TK11); yedek başlığında hesap sarmalı yok (TK10); dönem devrinde DEK yenilenir (TK12) | Görevdeyken kopyaladığı veri. TK12 kapalı kalırsa: görevdeyken kopyaladığı `guvenlik.json`'la sonraki yedekler de açılır |
| 6 | Hesap parolasını bilen biri veri dizinini kopyalayıp DEK'i program dışında türetir | Rol kriptografik değildir; dönemlik hesap + izlenebilirlik | Tam okuma mümkündür; kılavuz açıkça yazar ([iskelet envanteri §6.3](../kesif/2026-10-31-iskelet-envanteri.md) risk 1); BitLocker ve ayrı Windows hesabı önerisi (§4.5) |
| 7 | Program dışından SQLite dosyasında düz alan (tutar, tarih, karar no) değiştirilir — parola gerekmez | Denetim izi kayıt özeti + HMAC zinciri (TK16); DK'nin "kayıt bütünlüğü denetimi"; kapanmış dönemin özet değerinin devir-teslim tutanağına basılması (öneri; §7, §9) | Parolayı bilen biri zinciri yeniden hesaplayabilir; kâğıttaki özet son katmandır |
| 8 | Kilitliyken `guvenlik.json` silinir ya da bozulur | Kayıp kilidi (fail-closed): yalnız durum ve geri yükleme açık; "sıfırla ve kuruluma dön" yalnız korunacak veri yokken | Geri yükleme `guvenlik.json`'u yedek başlığından (yalnız kurtarma bölümü) yazar → kurtarma anahtarı gerekir |
| 9 | Disk, bilgisayar ya da USB yedeği çalınır | Fernet alan şifrelemesi (kapsam §5) + X25519/AES-GCM yedek; yedek başlığında yalnız kurtarma sarmalı (TK10) | Düz alanlar (tutar, tarih, karar no, kategori) okunur; kişi adı olmadan kişiye bağlanmaz (§5). Tam koruma BitLocker |
| 10 | Kurtarma anahtarı kâğıdı ele geçer | Yalnız `yonetici` yeniler; müdürlükte kapalı zarf; dönem devrinde yeni anahtar (TK12) | Yenileme, eski başlıkla açılan eski yedekleri kapatmaz (TB17) |
| 11 | Kilit ekranında parola denenir | Argon2id (~0,2 sn), kademeli gecikme 0/0/1/2/4 sn; yalnız seçilen hesabın sarmalı denenir | Kalıcı kilit yok (kendi kendine hizmet reddi olurdu); [BSG Yön. md. 9/2-c](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9) kilidi "kilitlenebilir" diye bırakır |
| 12 | `yonetici` başka bir hesabın parolasını sıfırlayıp o hesapla işlem yapar | Sıfırlama denetim izine düşer; geçici parola yalnız ilk girişte geçer ve hemen değiştirilir; hesap sahibine ilk girişte "parolanız … tarihinde sıfırlandı" bildirimi ve son girişleri gösterilir | Sıfırlama ile sahibinin ilk girişi arasındaki işlemler; bildirim ve denetim izi görünür kılar |
| 13 | İçe aktarılan dosya (banka özeti, e-Okul listesi, TEFBİS Excel) zararlı ya da bozuk | TK18: tür ve boyut denetimi, makrolu biçim reddi, `read_only`/`data_only`, önizleme + onay | openpyxl XML saldırılarına karşı `defusedxml` önerir (doğrulanmadı; §11 B15) |
| 14 | Dış kaynaklı metin Excel çıktısında formül olarak çalışır (banka açıklamasında `=HYPERLINK(…)`) | Tek xlsx yazım yardımcısı metin tipini zorlar (TK18); test | — |
| 15 | Programın ürettiği dosyalar (Word, PDF, Excel) ve içe aktarılan e-Okul listesi diskte kalır | Program koruyamaz: içe aktarma ekranında "kaynak dosyayı silin" hatırlatması, kılavuz, ayrı Windows hesabı; evrak izi (sha256) neyin üretildiğini gösterir | Kullanıcının idari tedbiri |
| 16 | Sahte güncelleme | Yalnız `github.com`/`api.github.com`, HTTPS, SHA-256; kurulumu kullanıcı başlatır | İmzasız exe (TB6, SmartScreen); GitHub hesabı ele geçerse sahte sürüm |
| 17 | Kişisel veri depoya ya da pakete sızar | `.gitignore`; `depo_sizintisi` (TCKN sağlaması + **IBAN mod-97**), `veri_sizintisi` (paket ve arşiv üyeleri) | Sentetik örnekler adıyla muaf |
| 18 | Elektrik kesintisi, disk arızası (tek bilgisayar) | `synchronous=FULL`, temiz kapanış işareti, günlük yedek, dış (USB) yedek hatırlatması | Bilgisayar ve USB birlikte kaybolursa son dış yedekten sonrası |

### 4.4 Kullanıcılar, roller ve oturum (T1)

**Terim.** `yonetici` rolünün arayüz etiketi "Program yöneticisi (OAB'den sorumlu müdür yardımcısı)"dır;
[BSG Yön. md. 4/1-s](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-4)'deki "sistem yöneticisi"
(Başkanlık ve MEM bilişim personeli) ile karıştırılmaz.

#### 4.4.1 Roller

| Rol | Kim | Bağ | Yazma | Dayanak |
|---|---|---|---|---|
| `yonetici` | OAB işlerinden sorumlu müdür yardımcısı | Organ dışı; okul idaresince belirlenir; dönemler arası sürer | Bütün birlik modülleri + sistem işleri (hesaplar, güvenlik, ayarlar, yedek) | K2; saha 10 (programı çoğunlukla MY kullanır); TEFBİS'e okul idaresi girer ([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| `baskan` | YK başkanı (veli) | YK üyeliği, görev "başkan" ([md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) | Birlik modülleri | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/2, 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) |
| `baskan_yardimcisi` | YK başkan yardımcısı | YK üyeliği, görev | Birlik modülleri | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (başkana vekâlet) |
| `muhasip` | Muhasip üye | YK üyeliği, görev | Birlik modülleri | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (gelir-gider işlemleri) |
| `sekreter` | Sekreter üye | YK üyeliği, görev | Birlik modülleri | [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) (yazışmalar); saha 5 (kararları sekreter yazar) |
| `denetleme_kurulu` | DK asıl üyeleri (1 veli + 2 öğretmen) | DK asıl üyeliği ([md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) | **Yalnız denetim modülü** | K2 (plan §1.8); [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) ara ve nihai rapor |
| `mudur` | Okul müdürü | Organ dışı; YK üyesi değildir, kurula başkanlık etmez (altın kural 6) | **Yalnız kendi yazıları** | K2; [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) |

**Kurallar.**

- **Bir hesap = bir kişi + bir rol.** İzin hesabı basit kalır, denetim izinde rol açıktır. Aynı kişinin ikinci rolü
  gerekirse ikinci hesap açılır. Aynı kişi aynı dönemde YK'de ve DK'de olamaz (§15 A-2).
- **Organ rolleri organ üyeliğine bağlanır** (F1c): üyelik "seçildi" ve görev bölümü yapılmışsa hesap açılabilir.
  Üyelik düştüğünde ([md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) hesap **aynı işlemde**
  kapanır. F1b'de organ yoktur: hesap rolle açılır, bağ F1c'de zorunlu olur.
- **Hesaplar dönemliktir.** Dönem devrinde bütün organ hesapları kapanır; yeniden seçilen üyeye yeni dönemde yeni
  hesap açılır. Denetim izi dönemle hizalı kalır, TK12 ile uyumludur. `yonetici` ve `mudur` dönemler arası sürer.
- YK'nin görevsiz asıl üyeleri ve yedekler v1'de hesap almaz (§15 M-7).

#### 4.4.2 Rol-izin matrisi

**Y** yazar · **O** okur · **—** erişemez · üst simge dipnottur. Okuma, okunan verinin evrak çıktısını (PDF, Word)
almayı da kapsar; çıktının evrak izi kaydı (sha256) okuma rolünde de yazılır — matrisin tek "açıkça izinli"
yazmasıdır. **Kapanmış dönem her rolde salt okurdur** (altın kural 4; düzeltme yeni dönemde ters kayıtla, §5, §7).
Rol-özel işaretler (karar "deftere işlendi", "TEFBİS'e girildi", harcama zincirinin halkaları) §7'dedir; bu matris
modül düzeyindedir. Hassas okumalar (K9 açıksa maskesiz bağışçı T.C. kimlik no, tam IBAN) erişim günlüğüne düşer;
hangi rolün maskesiz gördüğü §5'tedir (OYS'nin "okuma ≠ yönetme ≠ hassas detay" ayrımı korunur).

| Alan | `yonetici` | `baskan` | `baskan_yardimcisi` | `muhasip` | `sekreter` | `denetleme_kurulu` | `mudur` |
|---|---|---|---|---|---|---|---|
| Okul kartı, ders yılı, kapalı günler, birlik dönemi açma ve kapama (M1) | Y | O | O | O | O | O | O |
| Kişiler, organlar, temsilciler (M2) | Y | Y | Y | Y | Y | O | O |
| Genel kurul (M3) | Y | Y | Y | Y | Y | O | Y¹ |
| YK toplantı, katılım, karar taslağı (M4) | Y | Y | Y | Y | Y | O | O |
| Gelir-gider, banka eşleme, makbuz koçanı, kasa (M5) | Y | Y | Y | Y | Y | O | O |
| Harcama zinciri (M6) | Y | Y | Y | Y | Y | O | Y² |
| Bütçe, ilan, aylık bildirim, faaliyet raporu (M7) | Y | Y | Y | Y | Y | O | O |
| Denetim: kontrol listesi, bulgu, ara ve nihai rapor, bütünlük denetimi (M8) | O | O | O | O | O | Y³ | O |
| Müdür yazıları: birlik başkanına uyarı ve MEM'e bildirim ([md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)) | O | O | O | O | O | O | Y⁴ |
| Takvim ve uyum kaydı (M9) | Y | Y | Y | Y | Y | O | O |
| Gelen-giden evrak, belge dosyası (M10) | Y | Y | Y | Y | Y | O | O⁵ |
| Devir-teslim ve dönem kapanışı (M11) | Y⁶ | Y | Y | Y | Y | O | O |
| Kantin (M13), servis (M14) | Y | Y | Y | Y | Y | O | O |
| Personel (M15, sürüm 2) | Y | Y | Y | Y | Y | O | O |
| Denetim izi | O | O | O | O | O | O | O |
| Kullanıcılar: hesap açma, kapama, parola sıfırlama | Y | — | — | — | — | — | — |
| Güvenlik: kurtarma anahtarı, geri yükleme, yedek indirme, DEK yenileme | Y | — | — | — | — | — | — |
| Ayarlar (K9, boşta süre, küçük alım sınırı, kural sürümü seçimi) | Y | O | O | O | O | O | O |
| Kişisel veri içeren dışa aktarım (veli listesi, kişi dökümü) | Y | — | — | — | — | — | — |
| Güncelleme denetimi (tek dış istek) | Y | — | — | — | — | — | — |
| Kendi parolasını değiştirme, Kilitle, Çık | Y | Y | Y | Y | Y | Y | Y |

¹ Yeni açılan okulda genel kurul daveti ([md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)).
Yönetmelik müdüre olağanüstü genel kurul çağrısını da verir ([md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9),
[13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)); K2 listesine kullanıcı kararıyla eklendi (31.10.2026, §15 M-5).
² Okul yönetiminin yazılı harcama talebi ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)).
Yönetmelik "okul yönetimi" der; `yonetici` (müdür yardımcısı) zaten yazar.
³ DK'nin olağanüstü genel kurul çağrısı ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) denetim
modülünün çıktısı sayılır (kullanıcı kararı 31.10.2026, §15 M-6). YK rolleri DK modülüne yazamaz: DK, YK'nin faaliyetlerini inceler (md. 14/4).
⁴ Yalnız `mudur`; `yonetici` taslak hazırlayamaz (K2 lafzı; §15 M-11).
⁵ Müdürün kendi yazıları evrak defterine program tarafından işlenir.
⁶ Dönem kilidi, hesap kapanışları ve DEK yenilemesi yalnız `yonetici`.

#### 4.4.3 Oturum durumları

```
KURULUM ──(ilk yönetici hesabı + kurtarma anahtarı saklandı)──▶ KİLİTLİ
KİLİTLİ ──(hesap + parola  |  kurtarma anahtarı + yeni yönetici parolası)──▶ AÇIK(hesap, rol)
AÇIK    ──(Kilitle  |  boşta süre doldu  |  kullanıcı değiştir)──▶ KİLİTLİ
her durum ──(parmak izi dolu, guvenlik.json yok ya da kullanılamaz)──▶ GÜVENLİK_DOSYASI_KAYIP
her durum ──(geri yükleme uygulandı)──▶ YENİDEN_BAŞLAT_GEREK
```

- **Kilit ekranı** açık hesapların tanıtıcılarını rol etiketiyle listeler ("Muhasip", "Denetleme Kurulu 2"); kişi adı
  gösterilmez — `guvenlik.json` düz metindir ve kilitliyken şifreli adlar okunamaz. Kullanıcı hesabını seçer,
  parolasını yazar; yalnız o hesabın sarmalı denenir (Argon2id süresi hesap sayısıyla büyümez).
- **Ara katman sırası:** belirteç → güvenlik → whitenoise → common → `RestartRequired` (503) → `AppLock` (423) →
  `RolMiddleware` (403 `rol_yetkisiz`). `RolMiddleware` yalnız AÇIK durumda devreye girer; `HEALTH_PATH`,
  `setup/status/`, `security/status/` hiçbir durumda kesilmez (aile).
- **Boşta kilit** sunucuda tembel dolar: her istekte `son_etkinlik + N < şimdi` ise oturum kilitlenir, DEK bellekten
  silinir. `son_etkinlik` yalnız `X-OD-Etkinlik` başlıklı (kullanıcı eylemli) istekle tazelenir; durum ve pano
  sorguları tazelemez. Saat uykuyu sayar (`UykuyuSayanSaat`). Ön yüzdeki geri sayım yalnız görseldir. Kurulum
  sihirbazı bitene dek süre kilitlemez (kurtarma anahtarı ekrandayken; TB19 dersi); elle Kilitle çalışır.

#### 4.4.4 Anahtarlar ve `guvenlik.json` (şema 2)

- **DEK:** 32 bayt, kurulumda üretilir; TK12 kabul edilirse dönem devrinde yenilenir. Kör indeks, yedek anahtar çifti
  ve denetim izi mührü DEK'ten HKDF ile türer.
- **`guvenlik.json`:** `surum: 2`, `kdf` parametreleri, `hesaplar: [{id, tanitici, salt, sarmal}]`,
  `kurtarma: {salt, sarmal, dogrulandi}`, `gecis`. **Rol, ad-soyad, organ bağı ve açılış/kapanış tarihi
  veritabanındadır** (`Hesap`, alanları §5). `tanitici` gerçek ad olmaz; varsayılan rolden türer (`muhasip`,
  `dk-1`, `yonetici-2`), yönetici değiştirebilir — kişinin adını içeriyorsa program uyarır (açılışta DEK eldedir).
- **Parmak izi:** `HMAC(DEK, "od-anahtar-parmak-izi")` okul kartında; dosyanın ve veritabanının aynı DEK'i
  anlattığını gösterir. `enable()` → ilk yönetici hesabı; ön koşulları aile ile aynı (dosya yok, parmak izi boş,
  kişi tabloları boş).
- **Yedek başlığı (TK10):** `{surum, kdf, kurtarma}` — hesap yok. Geri yüklemede aday sırası: (1) güncel
  `guvenlik.json` + seçilen hesabın parolası; (2) yedek başlığı + kurtarma anahtarı. (2) ile açılırsa
  `guvenlik.json` yalnız kurtarma bölümüyle yazılır; program "kurtarma anahtarıyla aç + yönetici parolası" ekranına
  gelir, öteki hesaplar "parola yenilenmeli" durumuna düşer (geçici parolayı yönetici verir).
- **Arşiv:** her durum yazımından önce `guvenlik-arsiv-<damga>.json` (aile); hesap kapanınca sarmalı bütün arşiv
  kopyalarından da silinir (TK11).
- **DEK yenileme (TK12, F4):** ön koşul dönem kapanışı tamam ve `yonetici` oturumu açık; parola yeniden sorulur →
  `pre-dek-yenileme` yedeği (eski DEK'le) → `gecis` işareti (yarıda kalırsa açılışta tamamlanır ya da geri alınır,
  ailenin `resume_pending` deseni) → denetim izi zinciri önce eski anahtarla doğrulanır (başarısızsa yenileme durur) →
  tek SQLite işleminde şifreli alanlar, kör indeksler, parmak izi ve zincir mührü yeni DEK'le → `yonetici` sarmalı
  ve yeni kurtarma sarmalı; açık kalan öteki hesaplar (`mudur`, ikinci yönetici) geçici parolaya düşer →
  `yedekleme.json` yeni açık anahtar → yeni kurtarma anahtarı basılır, saklandığı doğrulanır, devir dosyasına girer →
  eski DEK'in arşiv kopyaları silinir. Eski kurtarma anahtarı, eski yedeklerin saklandığı süre boyunca devir dosyasında
  kapalı zarfta kalır (eski yedekleri yalnız o açar).

#### 4.4.5 Hesap yaşam döngüsü

| Olay | Ne olur | Kim |
|---|---|---|
| Kurulum (sihirbaz 1. adım) | İlk `yonetici` hesabı + parola + kurtarma anahtarı; anahtar basılıp saklandığı doğrulanmadan kurulum bitmez; `pre-parola` yedeği | Kuran kişi |
| Hesap açma | DEK geçici parolayla sarılır; ilk girişte parola değişimi zorunlu; organ rolünde üyelik bağı (F1c) | `yonetici` |
| Parola değiştirme | Kendi sarmalı yenilenir; eskisiyle aynı olamaz | Hesap sahibi |
| Parola unutuldu | DEK yeni geçici parolayla sarılır; sıfırlama denetim izine; sahibine ilk girişte bildirim (tehdit 12) | `yonetici` |
| Yönetici parolası unutuldu | İkinci yönetici hesabı sıfırlar ya da kurtarma anahtarı + yeni parola | — |
| Üyelik düştü ([md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)), görev değişti ([md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) | Hesap aynı işlemde kapanır, sarmal silinir (TK11); yeni görevliye yeni hesap | Düşmeyi kaydeden yazar |
| Dönem devri (F4) | Bütün organ hesapları kapanır; TK12 açıksa DEK yenilenir | `yonetici` |
| Müdür değişti | `mudur` hesabı kapanır, yenisi açılır | `yonetici` |
| MY değişti | Yeni `yonetici` hesabı açılır, eskisi kapanır, kurtarma anahtarı yenilenir; devir notu (Kütüphane E18 kalıbı) F4'te | Giden ya da kurtarma anahtarıyla gelen |

#### 4.4.6 Dürüst sınırlar (kılavuz ve Hakkında'ya girer)

1. **Rol kriptografik değildir.** Her hesap aynı veri anahtarını açar; rol kısıtı program içindedir.
   Hesapların değeri "kim, ne zaman, ne yaptı" sorusunun cevabıdır.
2. **Kurtarma anahtarını yenilemek eski yedekleri kapatmaz;** eski anahtar eski yedeği açmaya devam eder. Dönem
   devrindeki anahtar yenileme (TK12) yalnız **sonraki** verinin ve yedeklerin korunmasını sağlar.
3. **Açık oturum, sahibinin imzasıdır.** Bilgisayar başından kalkarken Kilitle.
4. Kişisel veri içeren her çıktı (Word, PDF, Excel) programın dışına çıktığı anda programın korumasından çıkar.

### 4.5 Pencere (T6)

| Konu | Davranış | Not |
|---|---|---|
| Çarpı | Programı kapatır: `on_closing` kapanmayı iptal etmez (işleyici bağlanmaz); onay sorulmaz | T6; Windows oturum kapanışındaki iptal-geri-alma geçişi gereksizleşir, testle sabitlenip silinir |
| Tepsi | Yok: `tray.py`, pystray/six, `gorev-kur.ps1`, `.iss` `otobaslat`/`tepside` görevleri sökülür | Qt kurulumu önce ayrılır (§13 D1) |
| Otomatik başlatma, uyku engeli | Yok | Katalog olmadığı için uyku engeli gerekçesi düşer |
| İkinci açılış | Çalışan pencere öne gelir (`goster`), ikinci süreç 0 ile çıkar | `instance_channel.py` aynen |
| Arayüzdeki Çık | Kalır (`modules/cikis`), parola istemez | Linux'ta pencere süslemesi olmayan masaüstü (TB13 dersi); "yeniden başlat" ekranının çıkış yolu |
| Kurucu ve kaldırıcı | `.Kapat` olayı + 30 sn mutex bekleme; `AppMutex` yok | §4.2 |
| Linux | `qt_kurulum.hazirla()` pencereden önce; SIGTERM → düzenli kapanış (temiz kapanış işareti + checkpoint). `setQuitOnLastWindowClosed` değeri ve Pardus davranışı F1a'da elle doğrulanır | `prerm` açık programı kapatmaz (TB40); çarpı = çık ile olasılık düşer |
| Ekran | 1366×768'de yatay kaydırmasız kullanılabilir ([ön değerlendirme §5.2](../kesif/2026-10-31-on-degerlendirme.md)); pencere boyutu aile değeri | 4 GB RAM'li eski okul bilgisayarı |
| Başlık ve görev çubuğu | "OAB Defteri"; AUMID `OABDefteri.Desktop`; Linux `StartupWMClass=oab-defteri` | §2.3 |

**Kanıt.** Birim: `on_closing` kapanmayı iptal etmez; `serve` sonrası WAL checkpoint ve temiz kapanış işareti yazılır.
"Exe açılır, çarpıyla kapanır, çıkış kodu doğru" F1a kapısında **elle** doğrulanır (CI pencereye tıklayamaz);
`packaging/windows/NOTLAR.md`'ye madde olarak girer.

**Hesap ve bilgisayar.**

- Program **okul demirbaşı** bilgisayara kurulur; muhasibin evdeki bilgisayarına kurulum önerilmez: kişisel veri ve
  mali kayıt kurum dışına çıkar, devir zorlaşır ([ön değerlendirme §4.2](../kesif/2026-10-31-on-degerlendirme.md)).
- Veri, programı çalıştıran Windows hesabının `%LOCALAPPDATA%\OABDefteri` dizinindedir. `ProgramData`'ya taşınmaz
  (bütün hesaplara okuma hakkı verirdi), `%APPDATA%`'ya konmaz (gezici profil açık SQLite'ı bozar). Sonuç: **veri tek
  Windows hesabında durur**, program o hesapta çalışır.
- **Öneri (§15 M-8):** bilgisayarda yönetici yetkisi olmayan ayrı bir "OAB" Windows hesabı; MY'nin kişisel oturumu
  (e-Okul, MEBBİS, DYS, e-posta açık) velilere açılmaz. [BSG Yön. md. 7/4](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-7)
  her kullanıcının kendi Windows oturumunu öngörür; veri tek Windows hesabında durduğu için bu tam karşılanamaz —
  program içindeki kişisel hesaplar "kim" sorusunu cevaplar, sapma kılavuzda açıkça yazılır. Reddedilen seçenek:
  veriyi erişim listeli ortak dizine (`ProgramData` + yerel grup) almak — yönetici kurulumu ve BTR'nin grup bakımını
  ister, aile çizgisinden sapar.
- BitLocker önerilir (tehdit 6, 9). USB'ye alınan dış yedek şifrelidir
  ([BSG Yön. md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)).
- **Yeni bilgisayara taşıma:** kurulum → `.odbak` geri yükleme (kurtarma anahtarı, TK10) → yönetici parolası →
  öteki hesaplara geçici parola. Kontrol listesi kılavuzdadır.

---

## 5. Veri modeli

Bu bölüm modelleri, alanları, kısıtları ve ilişkileri verir. Kuralların değerleri kural paketindedir (§6), evrakın adı,
kodu ve şablonu evrak kataloğunda (§9), hesap ve denetim izi modelleri ile şifreleme çekirdeği mimaride (§4). OYS'den
gelen modellerde "Kaynak" sütunu [OYS envanteri](../kesif/2026-10-31-oys-oab-envanteri.md) §2'deki modeli ve yapılan
değişikliği yazar; **YENİ** OYS'de karşılığı olmayan modeldir. Çıkarım sınıfının kesin hâli §12.A'dadır.

**Ortak ilkeler**

| # | İlke | Ayrıntı |
|---|---|---|
| O1 | Silme ucu yok | Hiçbir alan modelinin silme ucu yoktur (altın kural 4). OYS `BaseModel.deleted_at` yumuşak silmesi alınmaz (envanter S-22; §15 A-8). Kesinleşmemiş yanlış kayıt `IPTAL` durumuna geçer; kişi kaydı `PASIF` olur; kesinleşmiş mali kayıt ters kayıtla düzeltilir (§5.2.5). OYS'nin "canlı kayıt" koşullu tekil kısıtları "iptal olmayan" koşuluna döner. Tek istisna KVKK silmesi ve anonimleştirmesidir (§5.4): onaylı tetikle, iz bırakarak |
| O2 | Dönem kilidi | `term` taşıyan her kayıt, dönemi `KAPANDI` ise yazılamaz (sert — kapanmış dönem). Dönemsiz kayıtlar (kişi, koçan, defter, sözleşme, kiralanan yer) kendi durum kilidini taşır |
| O3 | Uyarı + gerekçe | Kural denetimi kayıt anında yapılır (§6.1 `denetle`). Kayıt güncel uyarı özetini `rule_warnings` (JSON: kural kimliği, madde, ileti, paket ve revizyon) alanında tutar; **gerekçe** kayda değil merkezî uyum kaydına yazılır: her (kayıt, kural) sapması bir `ComplianceItem(kind=SAPMA)` satırıdır (gerekçe şifreli, kim-ne zaman). OYS'nin model başına `compliance_warnings`/`compliance_justification` alanları ve `_persist_tender_warnings` deseni (AYNEN) bu tabloya taşınır; Denetleme Kurulu bütün sapmaları tek listede görür. Uyarılı yazma gerekçesiz geçmez, sert ihlal hiç geçmez (altın kural 3) |
| O4 | Temel alanlar | `created_at`, `created_by`, `updated_at`, `updated_by` (hesap, §4). Her durum geçişi denetim izine ayrı satır yazar: önceki ve sonraki durum, gerekçe varsa `ComplianceItem` bağı |
| O5 | Para ve tarih | `Decimal(14,2)`, kuruş, ROUND_HALF_UP (OYS `_q` AYNEN). Pay dağıtımında kuruş korunur: toplam = parçaların toplamı; artık birlik payına kalır (§6.4.11-4). Tarih alanı yerel gündür; zaman damgası Europe/Istanbul; görünüm gg.aa.yyyy |
| O6 | Tek kaynak | Bir bilgi tek modelde durur, evrak oradan okur (OYS'nin evrak ilkesi, AYNEN): seçilen üyeler `OrganMembership`'ten, tutarlar `LedgerEntry`'den, yeter sayı `GeneralAssembly`'den. Evrak üretimi veriyi kopyalamaz; `GeneratedDocument` yalnız içerik özetini ve dosyayı tutar |
| O7 | Anlık görüntü | Sonradan değişebilen okul kartı değerleri (öğrenci mevcudu, yerleşim türü) hesaba girdiği anda kayda kopyalanır; okul kartı değişse de geçmiş hesap değişmez (altın kural 2'nin veri karşılığı) |
| O8 | Adlandırma | Model ve alan adları İngilizce; OYS'den UYARLA'lananlar OYS adını korur. Enum değerleri OYS'deki gibi Türkçe büyük harf ASCII (`ASIL`, `YEDEK`, `KAPANDI`); etiketleri Türkçe ve Yönetmelik terimiyle ("Denetleme Kurulu", "muhasip", "tahmini bütçe") |

### 5.1 Okul çekirdeği (Kütüphane Defteri `apps/okul` — UYARLA)

Kaynak: [iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md) §2.8. Kütüphane'deki modeller korunur; OAB'ye
özgü alanlar `SchoolConfig`'e eklenir, öğrenci tarafı T5 gereği sökülür.

| Model | Sınıf | OAB Defteri'nde |
|---|---|---|
| `SchoolConfig` (pk=1) | UYARLA | Aşağıdaki OAB alanları eklenir; `kutuphane_saatleri` ve kütüphaneye özgü alanlar düşer; `app_password_hash` parmak izi §4'te. Alanlar sonradan boşaltılamaz (aile kuralı); her değişiklik denetim izine düşer |
| `SchoolYear` | AYNEN | Ders yılı. `OabTerm.school_year` buna bağlanır (T3 eşlemi) |
| `SchoolTerm` | AYNEN | Ders yılının iki dönemi. Dönemlik gelir-gider duyurusu ([md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) "her dönem") ve yarıyıl ayında yarım kira ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) bu kayıttan okunur |
| `Holiday` | AYNEN (Disiplin Defteri'nden UYARLA'lı hâli) | İş günü hesabı: elden bağış beş iş günü ([md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)), servis onay ve tebliği beşer iş günü ([Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)). `SCHOOL_BREAK` yarıyıl tatilini tanır |
| `Personnel` | UYARLA | e-Okul personel listesinden ad-soyad (şifreli) ve `member_kind` (öğretmen · yönetici · diğer); "Görevi" sütunu yalnız türü belirlemek için geçici okunur, saklanmaz. Ayrılış havuzu (Kütüphane F1 eki 7) aynen. `OabPerson.personnel` ile isteğe bağlı bağ |
| `Student`, `ClassSection` | ALMA | T5: öğrenci listesi alınmaz. Öğrenci mevcudu okul kartında elle; veli listesindeki sınıf düz metindir (`ParentRoster`, §5.2.2) |
| `ImportRun` | UYARLA | Türler: `PERSONEL`, `VELI` (§8.4). `payload_sha256`, satır sayısı, önizleme özeti; ham dosya saklanmaz. Banka ve TEFBİS partileri kendi modellerindedir (`BankStatement`, `TefbisStatement`) |
| Hesap ve denetim izi | YENİ (§4) | Hesap modeli (rol, `OrganMembership` bağı, açılış-kapanış) ve ekleme-yalnız denetim izi §4'te tanımlanır; bu bölümdeki her `created_by`/`updated_by` ve her durum geçişi oraya yazar |

**`SchoolConfig`'e eklenen OAB alanları**

| Alan | Değerler | Kullanıldığı yer ve dayanak | Not |
|---|---|---|---|
| `institution_code`, `school_name`, `district`, `province` | metin | Antet (`letterhead.py`), arşiv paketi adı | Aile alanlarının OAB karşılığı |
| `level` (kademe) | `OKUL_ONCESI` · `ILKOKUL` · `ORTAOKUL` · `ORTAOGRETIM` · `YAYGIN` · `KARMA` | Kursiyer türünün görünürlüğü ([md. 4/1-ğ](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-4), [md. 7/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7)); temsilci kurulları ([OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25), [OKY md. 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OÖİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57)) | Kural paketinin `kosul` alanı buna bakar (§6) |
| `student_count`, `student_count_as_of` | sayı, tarih | Genel kurul yeter sayısı çarpanı ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); kantin kirasında %25 değişim ([md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) | Genel kurul ilan edilirken ve sözleşme imzalanırken anlık görüntü alınır (O7) |
| `settlement_type` (yerleşim türü) | `BUYUKSEHIR` · `IL_MERKEZI_BUYUKSEHIR_DEGIL` · `DIGER` | Pay dağılımı: büyükşehir olmayan il merkezinde ilçe payı yok, il payı %20 ([md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) | OYS `is_metropolitan` yerine (envanter S-17) |
| `canteen_mode` | `KIRAYA_VERILIYOR` · `BIRLIKCE_ISLETILIYOR` · `KANTIN_YOK` | Arz bedeli %3 kiracıdan ya da %1 birlikten ([md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [md. 17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)); işletmede VUK ([md. 23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | İşletmede vergi bilgi metni (özelge, `bilgi/`) |
| `staffing_mode` | `DOGRUDAN_ISVEREN` · `HIZMET_ALIMI` · `CALISTIRMIYOR` | K3; kıdem karşılığı ([md. 6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)) | Personel modülü (sürüm 2) yalnız doğrudan işverende açılır; hizmet alımı harcama zincirinden geçer |
| `opened_on` | tarih (çoğu okulda boş) | Yeni açılan okulda genel kurul iki ay içinde ([md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)); serviste ilk kez EK-3 puanlaması ([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)) | — |
| `registration_periods` | tarih aralıkları listesi | Kayıt-kabul ve diploma döneminde bağış toplanmaz ([md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [Genelge 2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni)) → uyarı | Tarihleri mevzuat vermez; okul girer. Boşken uyarı çalışmaz, kurulum yol haritasında madde olur |
| `small_purchase_limit`, `standing_decision` | tutar, → `BoardDecision` | Küçük alımda talep ve komisyon halkasının gerekçesi ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); saha 6; §15 A-11) | Kural paketine değil okul ayarına |
| `donor_tckn_enabled` | mantıksal (varsayılan kapalı) | K9 | Açılması yönetici + gerekçe + denetim izi; kapatılması mevcut değerleri boşaltma önerir |
| `third_approval_enabled` | mantıksal | İnternet bankacılığında üçüncü onay (F0-5 c) | Ödeme talimatında müdür onay satırı; "mevzuat gereği" diye sunulmaz |

Kurulum sihirbazı (plan §2.2) bu modelleri şu sırayla doldurur: 1) yönetici hesabı (§4) 2) `SchoolConfig` 3)
`SchoolYear`, `SchoolTerm`, `Holiday` 4) `BankAccount`, `LedgerAccount` ve ilk `OpeningBalance` (§5.2.5). İlk birlik
dönemi (`OabTerm`) son olağan genel kurulun tarihiyle açılır, devreden bakiye elle girilir.

### 5.2 OAB modelleri

#### 5.2.1 Kural paketi ve birlik dönemi

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `RulePackage` | `package` (ör. `OAB-2023.12`) · `rev` · `schema_version` · `content` (dondurulmuş JSON kopyası) · `content_sha256` · `loaded_at` | (`package`, `rev`) tekil; içerik yazıldıktan sonra değişmez, yeni revizyon yeni satırdır (altın kural 2; §6.2-4). Açılışta dağıtılan dosyanın özetiyle karşılaştırılır (§6.3 D7) | YENİ |
| `OabTerm` | `name` (ör. "2026-2027 birlik dönemi") · `school_year` → `SchoolYear` · `start_date` (dönemi açan olağan genel kurulun yapıldığı gün) · `end_date` (sonraki olağan genel kurul gününden bir önceki gün; açıkken boş) · `opened_by_assembly` → `GeneralAssembly` · `rule_package` → `RulePackage` (PROTECT) · `status` (`ACIK` → `KAPANISTA` → `KAPANDI`) · `closed_at`, `closed_by` · `archive_document` → `GeneratedDocument` | Dönem aralıkları çakışmaz; en çok bir `ACIK` ve bir `KAPANISTA` dönem; mali kaydın tarihi kaydın dönem aralığında olmalı (üçü sert — hesap bütünlüğü). `rule_package` yalnız revizyon geçişi ekranından ve `KAPANDI` olmayan dönemde değişir (§6.2-5, 6). Görev süresi bir yıl ([md. 12/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) sonraki olağan genel kurula kadar sayılır. Olağanüstü genel kurul yeni dönem açmaz, aynı dönemde organ yeniler ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13): olağanüstü genel kurulca seçilen YK olağan toplantıya kadar görev yapar) | OYS `OabTerm` UYARLA: `core.SchoolYear` → okul `SchoolYear`; `is_active` → `status`; kilit ve kural bağı eklenir |

**İki "dönem".** Birlik dönemi (`OabTerm`, T3: genel kuruldan genel kurula) ile ders yılının iki dönemi (`SchoolTerm`)
ayrı kavramlardır; [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)'daki "her dönem" ders dönemidir. Arayüz ikisini "birlik dönemi" ve "ders dönemi" diye
yazar. TEFBİS'in dönem esası (takvim yılı mı öğretim yılı mı) DOĞRULANMADI; program TEFBİS için dönem zorlamaz,
liste ve mutabakat tarih aralığıyla çalışır (§15'e öneri B-1).

#### 5.2.2 Kişiler, organlar, veli listesi

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `OabPerson` | `kind` (`VELI` · `OGRETMEN` · `IDARECI` · `HAYIRSEVER` · `KURSIYER` · `DIGER`) · `first_name`, `last_name` (şifreli) · `name_index` (kör indeks) · `phone` (şifreli, isteğe bağlı) · `adult_declared` (kursiyer için "18 yaşını doldurmuştur" beyanı; doğum tarihi tutulmaz) · `is_principal` (okul müdürü) · `personnel` → `Personnel` · `external_yk_terms`, `external_dk_chair_terms` (programdan önceki seçilme sayıları; eski karar defterinden beyan; sayım biçimi §15'e öneri B-12) · `status` (`AKTIF` · `PASIF`) | T.C. kimlik no alanı yok (K9). `name_index` tekil değildir (adaşlık); aynı indeksle ikinci kayıtta "olası aynı kişi" uyarısı. Hayırsever yalnız okul yaptırıp Bakanlığa bağışlayan kişidir ([md. 7/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7)); bağışçı kişi kaydı açmaz (bağışçı adı gelir kaydında, §5.2.5) | OYS `OabPerson` UYARLA: `tckn`, `tckn_hash`, TCKN tekil kısıtı ve doğrulaması, `phone_hash`, `linked_user_id` çıkar; ad-soyad şifrelenir (aile kuralı); yaş beyanı ve geçmiş sayaçlar eklenir |
| `OrganMembership` | `term` · `person` · `organ` (`YK` · `DK` · `DIVAN` · `ALIM_KOMISYONU` · `TEMSILCI`) · `assembly` → `GeneralAssembly` (seçildiği genel kurul; divanda zorunlu) · `role` (`BASKAN` · `BASKAN_YARDIMCISI` · `MUHASIP` · `SEKRETER` · `KATIP` · `UYE`) · `seat_type` (`ASIL` · `YEDEK`) · `seat_group` (DK'da `VELI` · `OGRETMEN`) · `votes` (aldığı oy) · `seat_order` (yedek sırası, oydan) · `elected_by` (`GENEL_KURUL` · `OGRETMENLER_KURULU` · `MEM_GOREVLENDIRME` · `YK_KARARI` · `OKUL_IDARESI` · `KENDILIGINDEN`) · `representation` (temsilcide, aşağıda) · `status` (`ADAY` → `SECILDI` → `DUSTU`) · `start_date`, `end_date` · `promoted_on`, `promoted_by_decision` → `BoardDecision` (yedekten asıla geçiş) · `drop_kind` (`OGRENCI_AYRILDI` · `DEVAMSIZLIK` · `ISTIFA` · `NITELIK_KAYBI` · `BASKA_KURUMDA_GOREV` · `OLAGANUSTU_GK_SECIMI` · `DIGER`) · `dropped_reason` (şifreli, isteğe bağlı) · `eligibility_declared_on` (suç engeli beyanı alındı; [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) · `single_birlik_declared_on` ([md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) 2. cümle) · `retained_until_assembly` ([md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) istisnası işareti) · `rule_warnings` | (dönem, organ, kişi, genel kurul) iptal olmayanlarda tekil. Koltuk uygunluğu aşağıdaki tabloda. `SECILDI` yalnız aynı genel kurulun `ADAY` kaydından olur (tek kaynak — sert). Düşmede `drop_kind` zorunlu | OYS `OrganMembership` UYARLA: organ türleri genişler (plan §2.3); şifreli beyan notu yerine yalnız tarih (envanter S-20) — böylece `kvkk_special_category` bayrağı da kalkar; yedek çağırma, oy ve temsil alanları eklenir |
| `ParentRoster` | `import_run` → `ImportRun` · `term` · `full_name` (şifreli) · `name_index` (kör indeks) · `student_class` (düz metin, ör. "9-A") · `row_no` · `attended_assembly` → `GeneralAssembly` (boş olabilir) · `attended_meeting` (`BIRINCI` · `IKINCI`) | Bir satır bir öğrencidir; iki çocuklu veli iki satırdır ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1 "velisi katılan öğrenci sayısı" bunu ister). Öğrencinin adı, numarası, T.C. kimlik no, telefon, adres alınmaz (T5). Başka hiçbir model buna yabancı anahtar vermez (silinebilirlik); adaylığa geçen veli için ad `OabPerson`'a kopyalanır. Dönem kapanışında bütün satırlar silinir (§5.4, §7.8) | YENİ (T5 kararı) |

**Temsil türleri (`representation`).** `ODUL_DISIPLIN_KURULU` ([OKY md. 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OKY md. 186](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-186)) · `DAVRANIS_DEGERLENDIRME_KURULU`
([OÖİKY md. 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57)) · `SOSYAL_ETKINLIKLER_KURULU` ([SEY md. 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6)) · `KONTENJAN_KOMISYONU` ([OKY md. 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25)) · `RPD_YURUTME_KOMISYONU`
([RPD Yön. md. 16](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16)) · `TASIMACI_TESPIT_KOMISYONU` (birlik başkanı; [Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3), [Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3)) · `MUHAMMEN_BEDEL_KOMISYONU` (birlik
başkanı; [md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) · `KIRALAMA_IHALE_KOMISYONU` (birlik başkanı; [md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) · `KAMPUS_YONETIMI` ([md. 13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) ·
`KANTIN_DENETIM_KOMISYONU` ([Genelge 2020/8](../mevzuat/okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md); korpusta çapasız, kural yok — yalnız kayıt) · `DIGER`. Kurul bileşimleri kural
paketindedir (§6.4.4).

**Koltuk uygunluğu**

| Koltuk | Kim oturabilir | Tür | Dayanak |
|---|---|---|---|
| YK asıl ve yedek | `VELI` · `KURSIYER` (`adult_declared`) · `HAYIRSEVER` (isterse) | sert (hukuken geçersiz seçim) | [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| YK, her koltuk | Okul müdürü (`is_principal`) olamaz | sert | Proje kuralı 6; [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) (§6.4.2 yorumu) |
| DK veli koltuğu (1+1) | `VELI` · `KURSIYER` (`adult_declared`); hayırsever **değil** | sert | [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [md. 11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) (OYS hayırseveri sayıyordu, envanter S-8) |
| DK öğretmen koltukları (2+2) | `OGRETMEN`; okulda yeterli öğretmen yoksa il/ilçe MEM onayıyla başka okulun öğretmeni | sert (tür) · uyarı (onay kaydı eksik) | [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Divan başkanı ve kâtip | `VELI` · `KURSIYER` (`adult_declared`) | uyarı | [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) |
| Alım komisyonu | YK üyeleri; uzmanlık gereken işte birlik üyeleri; en az üç kişi | uyarı | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) |
| Sayılar (YK 5+5, DK 3+3) | Eksik bileşim | uyarı; genel kurul yeter sayısının tabanını etkilemez (sabit 16, §5.2.3) | [md. 12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Aynı kişi aynı dönemde YK'de ve DK'de | — | **sert** — kullanıcı kararı (31.10.2026): denetleyen ile denetlenen ayrılığı | `denetleme_kurulu.yk_uyesi_olamaz`; §15 A-2 |

#### 5.2.3 Genel kurul

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `GeneralAssembly` | `term` (olağanda kapanacak dönem: çağrıyı o dönemin YK'si yapar, raporlar o döneme aittir) · `kind` (`OLAGAN` · `OLAGANUSTU`) · `called_by` (`YONETIM_KURULU` · `OKUL_MUDURU` · `MUDUR_YENI_OKUL` · `DENETLEME_KURULU` · `UYE_BASVURUSU` · `BASKAN_VEYA_MUDUR_13_8` · `MUDUR_25_2`) · `call_reason` (şifreli; olağanüstüde zorunlu) · `call_decision` → `BoardDecision` · `call_document` → `DocumentRecord` (müdür ya da DK yazısı, üye başvurusu) · `member_application_count` (%10 başvurusunda başvuran sayısı; kişi listesi tutulmaz) · `announced_on` · `venue` · `first_meeting_at` · `second_meeting_at` · `second_announced_on` · `student_count_snapshot` · `quorum_base` (16) · `quorum_multiplier` (4 ya da 2) · `quorum_required` · `first_attendee_count` · `second_attendee_count` · `held_at_meeting` (`BIRINCI` · `IKINCI`) · `attendance_by_kind` (JSON sayılar: veli/kursiyer, öğretmen, yönetici, hayırsever, diğer) · `parent_students_count` (velisi katılan öğrenci sayısı) · `observer_count` ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) gözlemci öğrenci; oy yok) · `discharge_yk`, `discharge_dk` (`EDILDI` · `EDILMEDI` · `GORUSULMEDI`) · `budget` → `OabBudget` · `status` (§7.1) · `rule_warnings` | Yeter sayı = 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban organ bileşiminden gelir, üyelik kayıtlarından sayılmaz; olağanüstüde de aynı ([md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) — ilan anında hesaplanır, dondurulur, elle değiştirilemez (sert — yeter sayı hesabı). Birinci toplantı katılımı yeter sayının altındaysa "yapıldı" olamaz (sert). Katılım sayıları `TUTANAK_TAMAM`'dan sonra yalnız gerekçeli düzeltme satırıyla değişir | OYS `GeneralAssembly` UYARLA: taban sabitlenir (envanter S-1, S-2); `follows_failed_assembly` öz FK kalkar, iki toplantı aynı kayıtta; `attendee_count` ikiye ayrılır; ibra, katılım dağılımı, 30 gün ve Ekim sonu denetimleri eklenir; `venue` ve ikinci toplantı yazılabilir olur |
| `AgendaItem` | `assembly` · `order` · `kind` (`ACILIS` · `DIVAN_SECIMI` · `YK_FAALIYET_RAPORU` · `DK_RAPORU` · `IBRA` · `TAHMINI_BUTCE` · `YETKILENDIRME` · `SECIM_YK` · `SECIM_DK` · `ONERILER` · `DILEK` · `KAPANIS` · `DIGER`) · `title` · `notes` (şifreli) · `added_by_vote` + `change_votes_for`, `change_votes_against` ([md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) · `result_text` (şifreli) · `votes_for`, `votes_against` · `result` (`KABUL` · `RET` · `GORUSULDU`) | (genel kurul, sıra) tekil. Olağanüstüde çağrı gündemi dışında madde eklenemez ([md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) gündeme bağlılık — sert, hukuken geçersiz karar; kural paketi bunu uyarı sayıyor: §6.4.1 ile birleştirmede eşitlenmeli; §15'e öneri B-13). Tohum gündemi [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) yetkilendirme ve [md. 11/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) öneriler maddelerini de içerir | OYS `AgendaItem` **AYNEN → UYARLA** (envanterden sapma): tür, sonuç ve oy alanları eklenir |
| `AssemblyMinutes` | `assembly` (1:1) · divan `OrganMembership(DIVAN)` kayıtlarından · `yk_report_reader`, `dk_report_reader`, `budget_presenter` → `OabPerson` · `unaudited_documents_note` (şifreli; ibra edilmeyen muhasebe evrakı listesi, [md. 11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11)) · `handed_to_new_yk_on` ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10)) | Seçilen üyeler `OrganMembership`'ten okunur (tek kaynak, AYNEN) | OYS `AssemblyMinutes` UYARLA: serbest metin adlar kişi kaydına bağlanır |

Olağanüstü genel kurulda ikinci toplantı: [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) çoğunluk aranmayan ikinci toplantıyı tekrarlamaz (envanter S-3);
**kullanıcı kararı (31.10.2026):** md. 9/2'deki ikinci toplantı olağanüstü genel kurulda da uygulanır (§15 A-1).

#### 5.2.4 Kurul toplantıları, kararlar, denetim

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `BoardMeeting` | `term` · `organ` (`YK` · `DK`) · `meeting_no` (dönem içinde sıra) · `kind` (`AYLIK` · `OLAGANUSTU` · `GOREV_BOLUMU`) · `scheduled_at`, `held_at` · `place` · `agenda` (şifreli) · `status` (`PLANLANDI` → `YAPILDI` · `YETER_SAYI_YOK` · `IPTAL`) | YK'de `YAPILDI` için en az dört üye ([md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) — sert. `YAPILDI`/`YETER_SAYI_YOK`'a geçerken görevdeki her asıl üyenin katılım satırı zorunlu (sert; devamsızlık sayımının bütünlüğü, envanter S-19, §15 A-9) | OYS `BoardMeeting` UYARLA: tür, durum, yeter sayı denetimi |
| `BoardMeetingAttendance` | `meeting` · `membership` · `present` · `excused` | (toplantı, üyelik) tekil. Özrün nedeni ve belgesi tutulmaz (sağlık verisi olabilir) | OYS AYNEN |
| `BoardDecision` | `meeting` · `kind` (`OLAGAN` · `GENEL_KARAR` · `HARCAMA` · `GOREV_BOLUMU` · `YEDEK_CAGIRMA` · `KOCAN_KAYIT` · `GK_CAGRISI` · `BUTCE` · `DIGER`) · `text` (şifreli) · `votes_for`, `votes_against` · `dissent` (şifreli, isteğe bağlı) · `status` (`TASLAK` → `KABUL_EDILDI` · `REDDEDILDI`; `KABUL_EDILDI` → `DEFTERE_ISLENDI`; `TASLAK` → `IPTAL`) · `book` → `OfficialBook` (karar defteri) · `decision_no` (defter sıra no) · `page_no` · `decision_date` · `entered_by`, `entered_at` (deftere işleyen) · `page_photo` → `Attachment` (isteğe bağlı) · `amends` → `BoardDecision` | Kabul oyu ≥ 3 ([md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) ve toplantı `YAPILDI` — sert. (defter, sıra no) tekil — sert. `DEFTERE_ISLENDI` sonrası metin ve oylar değişmez; düzeltme yeni kararla (`amends`) — sert (altın kural 4). Sıra no geri giderse ya da atlarsa uyarı | OYS `BoardDecision` UYARLA: `is_draft` → `status`; defter, sıra no, sayfa, oylar ve bağlar eklenir (envanter S-11) |
| `AuditReport` | `term` · `kind` (`ARA` · `NIHAI`) · `report_date` · `checklist` (JSON; liste sürümü evrak kataloğundan) · `findings` (şifreli) · `irregularity_found` · `escalated_assembly` → `GeneralAssembly` ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) olağanüstü çağrı) · `submitted_to_yk_on` (ara) · `submitted_to_assembly` → `GeneralAssembly` (nihai) · `status` (`TASLAK` → `DK_IMZALADI` → `SUNULDU`) | Yazan rol `denetleme_kurulu` (plan §1.8). Yılda en az iki inceleme ([md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) — uyarı. Bir `UYGUNSUZ` madde → `irregularity_found` (OYS mantığı AYNEN) | OYS `AuditReport` UYARLA: liste tazelenir, KVKK'lı "adli sicil kayıtları alınmış mı" maddesi çıkar (S-20) |
| `InspectionRecord` | OYS alanları aynen (konu, plan ve gerçekleşme tarihi, sonuç, rapor no, bulgular, izleme tarihi) | `follow_up_due` yardım metni düzeltilir: Genelge 2020/8'deki süreler ilçe ekibinin müdahale süresidir, düzeltme termini değildir | OYS AYNEN |

#### 5.2.5 Mali çekirdek (K1, T4)

Hesap planı T4'e göredir: banka, kasa, şartlı bağış alt hesabı; çift taraflı muhasebe yoktur, her kayıt tek hesaba
yazılır. **T4'e bir ek önerilir:** `EMANET` alt hesabı — kiracıdan nakit alınan kesin teminat ([EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8); fesihte
"gelir kaydedilir" [md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22), yani o güne kadar gelir değildir) ve birliğe yanlışlıkla yatırılıp aktarılacak paylar
için (§15'e öneri B-6).

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `BankAccount` | `bank_name` · `branch` · `iban` · `label` · `opened_on` · `is_active` · `import_profile` (JSON: sütun eşlemesi, §8.2) | IBAN mod-97 ve tekil — sert. IBAN açık tutulur (kurumsal hesap). İmza yetkilileri `OrganMembership`'ten okunur ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)); ayrı alan yok | YENİ |
| `BankStatement` | `bank_account` · `file_sha256` · `file_name` · `period_start`, `period_end` · `opening_balance`, `closing_balance` (dosyada varsa) · `row_count` · `imported_at`, `imported_by` · `status` (`ONIZLEME` → `UYGULANDI` → `GERI_ALINDI`) | Ham dosya saklanmaz. `GERI_ALINDI` yalnız hiçbir hareketi eşlenmemişse | YENİ (içe aktarım partisi) |
| `BankTransaction` | `bank_account` · `statement` · `booking_date` · `value_date` · `amount` (işaretli: + giriş, − çıkış) · `balance_after` · `reference` (dekont/işlem no) · `description` (şifreli) · `counterparty` (şifreli) · `fingerprint` · `void` | `fingerprint` (hesap + tarih + tutar + bakiye + referans + açıklamanın normalize özeti) tekil — sert (çift aktarım). İçe aktarıldıktan sonra değişmez (K1) — sert. Kapanmış döneme düşen satır alınmaz — sert | YENİ |
| `LedgerAccount` | `kind` (`BANKA` · `KASA` · `SARTLI_BAGIS` · `EMANET`) · `name` · `bank_account` (`BANKA`'da) · `parent` (`SARTLI_BAGIS` ve `EMANET` paranın fiilen durduğu `BANKA` ya da `KASA` hesabı) · `purpose` (şifreli; şartlı bağışın şartı ve amacı) · `source_entry` → `LedgerEntry` (şartlı bağışın gelir kaydı) · `opened_on`, `closed_on` | `KASA`, `SARTLI_BAGIS`, `EMANET` bakiyesi eksiye düşemez — sert. Şartlı alt hesaptan gider amaç beyanı olmadan kaydedilmez — sert ([md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) | YENİ; OYS `BudgetCategory` yalnız sınıflamadır, hesap değildir |
| `LedgerEntry` | `term` · `entry_no` (dönem içi sıra; defter baskısının sıra no'su) · `date` · `direction` (`GELIR` · `GIDER` · `VIRMAN`) · `ledger_account` · `counter_account` (virmanda) · `amount` (> 0) · `in_kind` (ayni bağış; bakiyeye girmez) · `budget_category` · `tefbis_type` → `TefbisTypeMapping` (işlem tipi ve alt kalem) · `tefbis_source_type` (kaynak tipi; gelirde) · `activity_code` (faaliyet kodu) · `description` (şifreli) · `document_kind` (`MAKBUZ` · `ALINDI_BELGESI` · `DEKONT` · `FATURA` · `GIDER_PUSULASI` · `SOZLESME` · `DIGER`) · `document_no`, `document_date` · `receipt_leaf` → `ReceiptLeaf` · `decision` → `BoardDecision` · `expense_file` → `ExpenseFile` · `installment` → `ContractInstallment` · `share_statement` → `ShareStatement` · `donor_name` (şifreli, isteğe bağlı) · `donor_tckn` (şifreli; yalnız `donor_tckn_enabled`) · `asset_slip_no` (varlık işlem fişi no; [TMY md. 16](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16), [TMY md. 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41)) · `status` (`TASLAK` → `KESIN`; `TASLAK`/`KESIN` → `IPTAL`) · `reversal_of` → `LedgerEntry` · `posted_book` → `OfficialBook`, `posted_page`, `posted_at` (deftere geçirildi) · `tefbis_entered_at`, `tefbis_entered_by` · `tefbis_fix_needed` · `rule_warnings` | `KESIN` kayıt değişmez — sert. Tarih dönem aralığında — sert. Makbuzlu gelirde yaprak zorunlu ve yaprak tutarı = kayıt tutarı — sert. Virmanda iki hesap, aynı tutar — sert. `IPTAL` yalnız deftere geçmemiş ve TEFBİS'e girilmemiş kayıtta; öbür hâlde ters kayıt (§7.3) — sert. Giderde karar bağı yoksa ([md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) ve kayıt döneminde bağışta ([md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15)) — uyarı | YENİ (ön değerlendirme §7.3 GelirKaydı ve GiderKaydı tek modelde) |
| `LedgerEntryLine` | `entry` · `line_no` · `description` · `quantity` · `unit` · `unit_price` · `amount` · `tefbis_subitem` | Satırlar toplamı = kayıt tutarı — sert. Tek satırlı kayıtta satır açılmaz | YENİ (TEFBİS detay satırı: işlem türü, miktar, birim, birim fiyat — 2009 kılavuzu) |
| `TransactionMatch` | `bank_transaction` · `ledger_entry` · `amount` · `matched_by`, `matched_at` · `status` (`ETKIN` · `COZULDU`) | Çoka çok. Bir hareketin ve bir kaydın etkin eşleşmeleri toplamı kendi tutarını aşamaz; yönler tutarlı (giriş ↔ gelir ya da virmanın banka ayağı, çıkış ↔ gider) — sert. Eşleşme silinmez, `COZULDU` olur. `KASA` kaydı bankayla eşlenmez, yalnız kasa → banka virmanının banka ayağı eşlenir | YENİ |
| `OpeningBalance` | `term` · `ledger_account` · `amount` · `source` (`ONCEKI_DONEM_KAPANISI` · `ILK_KURULUM_ELLE`) · `evidence_date` (ekstre tarihi) · `tefbis_carryover` (TEFBİS "Devreden" ekranındaki tutar) · `difference_note` | (dönem, hesap) tekil; `ONCEKI_DONEM_KAPANISI` kapanışta otomatik yazılır ve değişmez — sert; elle giriş yalnız ilk dönemde | YENİ (OYS `OabBudget.opening_balance` alanının yerine) |
| `TefbisTypeMapping` | `kind` (`ISLEM_TIPI` · `KAYNAK_TIPI` · `FAALIYET_KODU`) · `direction` (`GELIR` · `GIDER` · boş) · `group_label` (ör. "Bağışlar, Yardımlar") · `type_label` · `subitem_label` · `source` (`EK_A_2009` · `OKUL_EKRANI`) · `is_active` · `valid_from` · `replaced_by` | Kullanılmış satır silinmez, pasifleşir. Okul kendi TEFBİS ekranındaki listeyi girer (K6; F0-5 d). Tohum: [2009 kılavuzu EK-A](../kesif/kaynaklar/tefbis-2009-kilavuz-ek-a-islem-tipleri.txt) üç düzeyiyle; kaynak tipinin yedi üst sınıfı | YENİ (ön değerlendirme §7.3 TEFBİSEşleme; OYS'nin atıfsız kategori tohumunun yerine EK-A, envanter §4.1 satır 58) |
| `TefbisStatement`, `TefbisStatementLine` | Parti: `period_start`, `period_end`, `file_sha256`, `row_count`, `status`. Satır: `date` · `direction` · `type_label` · `description` (şifreli) · `document_no`, `document_date` · `amount` · `decision_no` · `matched_entry` → `LedgerEntry` | T.C. kimlik no ve ad-soyad sütunları okunmaz (§8.3). Sürüm 2 (M12, F8+); şema şimdi sabitlenir | YENİ (OYS `TefbisImport` ALMA) |

**Bakiye ve mutabakat değişmezleri.** (1) Banka hesabının son içe aktarılan bakiyesi = `BANKA` + o bankaya bağlı
`SARTLI_BAGIS` ve `EMANET` hesaplarının eşlenmiş kayıt bakiyesi; fark mutabakat listesine düşer. (2) `KASA`,
`SARTLI_BAGIS`, `EMANET` eksiye düşmez. (3) Ayni bağış (`in_kind`) hiçbir nakit bakiyesine girmez; yalnız TEFBİS
listesinde ve raporlarda görünür. (4) Dönem kapanış bakiyesi sonraki dönemin `OpeningBalance`'ıdır.

#### 5.2.6 Makbuz koçanı (K5)

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `ReceiptBookRegistry` | `kind` (`BAGIS_ALINDI_BELGESI` ([EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1)) · `GELIR_GIDER_MAKBUZU` · `DIGER`) · `series` · `volume_no` (cilt) · `first_leaf`, `last_leaf` · `printed_by` (matbaa) · `received_on` · `sealed_on` (kurum mührü) · `registration_decision` → `BoardDecision` (koçan seri numaralarıyla karar defterine kayıt) · `holder_role` · `status` (`ENVANTERDE` → `KAYITLI` → `KULLANIMDA` → `BITTI` → `ARSIVDE`; `IPTAL`) · `finished_on` · `rule_warnings` | (tür, seri, cilt) tekil; aynı serideki yaprak aralıkları çakışmaz — sert (numara tekilliği). 50 asıl + 50 koçan değilse ([md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) ve mühür ya da karar kaydı olmadan kullanımda ([md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) — uyarı. **Dönem alanı yoktur:** koçan birlikle yaşar, dönemden döneme devredilir | OYS `ReceiptBookRegistry` UYARLA: `term` FK kalkar; seri-cilt-sıra, mühür, karar bağı ve durumlar eklenir |
| `ReceiptLeaf` | `book` · `leaf_no` · `status` (`BOS` → `KULLANILDI` · `IPTAL` · `KAYIP`) · `used_on` · `ledger_entry` → `LedgerEntry` (1:1) · `cancel_reason` (şifreli) | (koçan, yaprak no) tekil ve aralık içinde; bir yaprak bir kayda — sert. `IPTAL` ve `KAYIP` geri alınamaz — sert. Kendinden önce `BOS` yaprak bırakarak kullanım — uyarı. Koçan envantere girince yaprakları topluca `BOS` açılır | YENİ |

Program makbuz basmaz (K5); elektronik ortamda basılan belge [md. 16/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)'ya göre ayrı bir güvenlik işidir, ilk sürümde
yoktur.

#### 5.2.7 Harcama, bütçe, duyuru, bildirim, uyum

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `ExpenseFile` | `term` · `file_no` · `title` (şifreli) · `kind` (`MAL` · `HIZMET` · `ONARIM` · `SUREKLI_ODEME` · `OGRENCI_YARDIMI` · `AKTARIM` · `DIGER`) · `request_kind` (`OKUL_YAZILI_TALEBI` · `YK_RESEN` · `GENEL_KARAR`) · `request_record` → `DocumentRecord` · `request_document` → `GeneratedDocument` (müdürün yazdığı talep) · `request_date` · `estimated_amount` · `decision` → `BoardDecision` · `standing_decision` → `BoardDecision` · `commission_members` (çoka çok → `OabPerson`) · `supplier_name` (şifreli) · `supplier_tax_no` (yalnız tüzel ve ticari VKN; gerçek kişide tutulmaz) · `invoice_no`, `invoice_date`, `invoice_amount` · `withholding_amount` (bilgi) · `asset_slip_no` (VİF; [md. 18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) · `payment_order` → `GeneratedDocument` · `payment_entry` → `LedgerEntry` · `payee_is_member` (hesaplanır) · `status` (§7.4) · `rule_warnings` | Gider kaydı dosyaya bağlanmadan dosya `ODENDI` olmaz — sert. Diğer halkalar (talep, karar, en az üç kişilik komisyon, VİF, müşterek imza, organ üyesine ödeme) uyarı + gerekçedir (§7.4) | YENİ (ön değerlendirme M6) |
| `BudgetCategory` | `code` · `name` · `kind` (`GELIR` · `GIDER`) · `order` · `is_active` · `default_tefbis_type` → `TefbisTypeMapping` · `requires_expense_file` | Kod tekil. "Huzur hakkı" ya da benzeri kategori yoktur ([md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25)) — tanımlanamaz. Banka masrafı, vergi, MEM payı aktarımı gibi kategorilerde `requires_expense_file` kapalı | OYS UYARLA: tohum TEFBİS EK-A üst gruplarından (OYS'nin atıfsız 5+8 tohumu yerine) |
| `OabBudget` | `term` (bütçenin uygulanacağı dönem) · `prepared_decision` → `BoardDecision` ([md. 13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · `discussed_at` → `GeneralAssembly` ([md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11)) · `announcement` → `Announcement` · `status` (`TASLAK` → `YK_HAZIRLADI` → `GK_GORUSULDU` → `DUYURULDU`) · `notes` | Dönem başına bir iptal olmayan bütçe. "Onaylandı" yerine "genel kurulda görüşüldü" | OYS UYARLA: `opening_balance` kalkar (→ `OpeningBalance`); `ONAYLANDI` adı değişir |
| `BudgetLine` | `budget` · `category` · `estimated_amount` · `notes` | (bütçe, kategori) tekil; tutar ≥ 0. Gerçekleşen kayıtlardan hesaplanır, alan yoktur | OYS UYARLA: `realized_amount` (K1) ve `realized_from_payroll` (K3) kalkar |
| `Announcement` | `term` · `kind` (`GK_CAGRISI` · `OLAGANUSTU_GK_CAGRISI` · `BUTCE` · `GELIR_GIDER_DONEMLIK` · `SERVIS_ISI_ILANI` · `TASIMACI_LISTESI` · `DIGER`) · `subject_type`, `subject_id` (genel kurul, bütçe, ders dönemi, tespit süreci) · `school_term` → `SchoolTerm` · `distributed_written_on` (elden yazılı) · `posted_board_on`, `removed_board_on` · `published_web_on` · `evidence` → `Attachment` (çoğul) · `content` → `GeneratedDocument` · `status` (`TASLAK` → `YAYIMLANDI` → `KALDIRILDI`) | İçerikte kişi adı yoktur (altın kural 5); üretici kurgusu gereği ad koymaz. Web metni HTML dosyasıdır; program yayımlamaz, okul sitesine kullanıcı taşır (çevrimdışı) | YENİ (OYS `ComplianceEntry` `PANO_WEB_ILAN` türünün yerine) |
| `MonthlyReport` | `term` · `year`, `month` · `snapshot` (JSON: gelirler, bağışlar, kararla yapılan harcamalar; kayıtlardan) · `document` → `GeneratedDocument` · `signed_on` · `delivered_on` · `outgoing_record` → `DocumentRecord` · `status` (`TASLAK` → `TESLIM_EDILDI`) | (dönem, yıl, ay) tekil. Ay sonunda teslim ([md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) — uyarı. Bağışçı adları varsayılan olarak dökümde yoktur (toplamlar) | YENİ (OYS `MUDURE_BILDIRIM` türünün yerine) |
| `ComplianceItem` | `term` · `kind` (`SAPMA` · `TAKVIM`) · **sapmada:** `subject_type`, `subject_id`, `rule_id`, `rule_package`, `rev`, `message`, `justification` (şifreli), `justified_by`, `justified_at` · **takvimde:** `obligation` (`DEFTER_TASDIK` · `DK_INCELEME` · `MEM_DENETIMI` · `KANTIN_FAALIYET_BELGESI` · `KANTIN_CALISAN_BELGE_YENILEME` · `TUFE_BILDIRIMI` · `MILLI_EMLAK_BILDIRIMI` · `IBRA_EDILMEDI_BILDIRIMI` · `DIGER`), `due_date`, `done_on`, `evidence` → `Attachment`, `responsible_role` | Sapma satırı silinmez; kayıt düzeltilip uyarı kalkınca `resolved_at` yazılır. Genel kurul son günü, YK aylık toplantısı, aylık bildirim, dönemlik duyuru, arz vadesi kendi modellerinden panoya düşer, buraya kopyalanmaz | OYS `ComplianceEntry` UYARLA ve yeniden adlandırma: dört türü başka modellere dağılır (envanter §2.2); OYS'nin model başına uyarı alanları buraya toplanır (O3); serbest metin `responsible` → rol |

#### 5.2.8 Defterler, evrak, dosyalar, devir

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `OfficialBook` | `kind` (`KARAR_DEFTERI` · `GELIR_GIDER_DEFTERI` · `GELEN_GIDEN_EVRAK_DEFTERI` · `DIGER`) · `certified_by` (`NOTER` · `IL_ILCE_MEM`) · `certified_on` · `certification_no` · `page_count` · `opened_on`, `closed_on` · `status` (`KULLANIMDA` · `DOLDU` · `ARSIVDE`) | Karar defteri noterce, diğerleri il/ilçe MEM'ce tasdik edilir ([md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); tasdik kaydı yokken ya da yanlış makamla kullanım — uyarı. Dönemsizdir, devredilir | YENİ (ön değerlendirme §2.2 "Defterler", [md. 23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| `DocumentRecord` | `book` → `OfficialBook` (gelen-giden) · `direction` (`GELEN` · `GIDEN`) · `year` · `record_no` · `date` · `counterparty` (şifreli) · `subject` (şifreli) · `external_ref` (karşı tarafın ya da EBYS sayısı) · `generated_document` → `GeneratedDocument` (giden yazının programdaki karşılığı) · `attachments` → `Attachment` · `term` | (defter, yıl, kayıt no) tekil — sert. Sıra atlama uyarı | YENİ — ADR-0028'deki `OabDocumentRecord`'un karşılığı; OYS'de hiç yazılmamıştı (envanter §0-9) |
| `GeneratedDocument` | `doc_type` (evrak kataloğu kimliği, §9) · `subject_type`, `subject_id` · `term` · `version` · `formats` (`DOCX` · `PDF` · `XLSX` · `HTML`) · `content_sha256` (tek içerik modelinin kanonik JSON özeti, §9.1) · `files` → `Attachment` · `rule_package` · `generated_at`, `generated_by` · `wet_signed_on` (ıslak imzalandı işareti) · `status` (`GECERLI` · `YERINI_ALDI`) | Aynı nesne için yeniden üretim yeni sürüm satırıdır; eski satır silinmez. Kapanmış dönemde yeniden basım aynı `content_sha256`'yı vermelidir (§6.2-6). Dosya imha edilse de tür, tarih ve özet kalır (Kütüphane `BelgeIzi` kalıbı) | YENİ |
| `Attachment` | `stored_name` (uuid) · `original_name` (şifreli) · `sha256` · `mime` · `size` · `sensitivity` (`NORMAL` · `OZEL_NITELIKLI`) · `retention_until` · `owner_type`, `owner_id` · `uploaded_by`, `uploaded_at` · `purged_at` | Dosya diskte şifreli durur (§5.3). Kabul: PDF, JPEG, PNG; tür imza baytından denetlenir (libmagic yok). İmha edilen dosyanın satırı `purged_at` ile kalır | OYS `file_storage.py` UYARLA (sha256, uuid adı, boyut sınırı AYNEN; libmagic ve yalnız-PDF kalkar) |
| `Handover` | `from_term`, `to_term` · `assembly` → `GeneralAssembly` · `date` · `handed_by`, `received_by` (→ `OabPerson`, çoğul: başkan, muhasip) · `cash_count` (kasa sayımı) · `bank_balance`, `bank_balance_on` · `document` → `GeneratedDocument` · `status` (`TASLAK` → `BASILDI` → `IMZALANDI`) | Kasa sayımı ≠ `KASA` bakiyesi ise uyarı + düzeltme kaydı. Olağanüstü genel kurulda `from_term` = `to_term` (ara devir) | YENİ ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10); saha 9: devir tutanağı yok) |
| `HandoverItem` | `handover` · `kind` (`DEFTER` · `KOCAN` · `DOSYA` · `BANKA_YETKISI` · `PROGRAM_HESABI` · `ACIK_IS` · `DIGER`) · `ref_type`, `ref_id` · `description` · `state` (`TESLIM_EDILDI` · `EKSIK` · `SONRA_TESLIM`) · `note` (şifreli) | Kalemler kayıtlardan otomatik önerilir (§7.8); elle eklenebilir | YENİ |

#### 5.2.9 Kantin ve servis (K4)

Program bu iki süreçte birliğin ve okulun evrakını hazırlar ve takibini yapar; komisyon kararının yerine geçmez (K4,
ön değerlendirme §2.3). Servis tarafında model adları OYS'deki gibi kalır, arayüz ve evrak "taşımacının tespiti",
"başvuru", "değerlendirme" der (altın kural 6).

| Model | Alanlar | Kısıt ve kural | Kaynak |
|---|---|---|---|
| `RentableAsset` | `name` · `asset_kind` (`KANTIN` · `SPOR_SALONU` · `KONFERANS_SALONU` · `OTOPARK` · `ACIK_ALAN` · `DIGER`) · `area_m2` · `full_year` (12 ay; aksi 9 ay, [md. 19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) · `short_term_rates` (saatlik, günlük, haftalık; [md. 19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) + `rates_document` → `DocumentRecord` · `is_active` | Ad tekil | OYS UYARLA: `SERVIS_GUZERGAHI` çıkar; tam yıl ve kısa süreli kullandırma eklenir |
| `Tender` | `kind` (`KANTIN_KIRALAMA` · `SERVIS_TESPIT`) · `route` (kantinde `YENIDEN_KIRALAMA` ([Genelge 2024/35 I](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i)) · `IHALE` ([Genelge 2024/35 II](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii), [Genelge 2024/35 I-7](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-7))) · `evaluation_method` (kantinde `PAZARLIK` ([2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51)); serviste `KOMISYON_DEGERLENDIRMESI` ([Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), varsayılan) · `EK3_PUANLAMA` ([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8))) · `ek3_reason` (`ITIRAZ` · `YENI_OKUL`) · `asset` · `term` · `status` (§7.6, §7.7) · ilan, başvuru, değerlendirme, karar, onay, tebliğ tarihleri · `estimated_price` (yalnız kantin, [md. 19](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)) · `incumbent_request_on`, `incumbent_reply_on`, `offer_to_incumbent_on`, `incumbent_accepted` (yeniden kiralama, [Genelge 2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2), [Genelge 2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3), [Genelge 2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5), [Genelge 2024/35 I-6](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-6)) · `rule_warnings` | `KESINLESTI` sonrası değişmez (OYS kilidi AYNEN, altın kural 4 ile genelleşir). Onay `OLUR` olmadan `KESINLESTI` olmaz — sert (§7.6, §7.7). `winner` alanı yoktur: seçilenler `Bidder.selected` ile (serviste birden çok taşımacı, §15 A-6) | OYS `Tender` UYARLA: iki süreç ayrılır; `EN_DUSUK_TEKLIF` çıkar; serviste varsayılan yöntem ters çevrilir (S-7); servis etiketleri "ihale", "teklif toplama" demez |
| `TenderCommissionMember` | OYS alanları + `vote` (`KABUL` · `RET`; çekimser yok) · `dissent` (şifreli; muhalif şerhi) · `seat_type` (yedekler) | Serviste çoğunluk, eşitlikte başkanın tarafı, çekimser yok, muhalif üye gerekçe yazar ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4)) | OYS UYARLA |
| `TenderApproval` | `tender` · `order` · `authority` · `decision` (`BEKLIYOR` · `UYGUN_GORUS` · `OLUR` · `RED`) · `requested_on` · `decided_on` · `document_no`, `document_date` | Serviste mülki amir ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8)). Kantinde onay makamı korpusta bulunamadı — DOĞRULANMADI; makam kullanıcıca girilir, onay kaydı yine zorunludur (plan §1.8) | OYS UYARLA |
| `Bidder` | `tender` · `bidder_type` (`GERCEK` · `TUZEL`) · `legal_name` (şifreli) · `tax_number` (yalnız tüzel) · `trade_registry_no` · `contact_address`, `contact_phone`, `contact_email` (şifreli) · `bid_amount` (yalnız kantin) · `incumbent` · `crime_bar` (`BEYAN_YOK_DEDI` · `ENGEL_VAR`) · `kinship_bar` (aynı) · `is_disqualified`, `disqualified_reason` · `selected` · `rule_warnings` | Kantinde `crime_bar` ([md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) ya da `kinship_bar` ([md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) `ENGEL_VAR` ise seçilemez — sert (hukuken geçersiz katılım). Belge eksikliği ([md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) — uyarı + gerekçe (plan §1.8) | OYS UYARLA: `person` FK kalkar (istekli birlik üyesi değildir); gerçek kişide vergi no (= T.C. kimlik no) tutulmaz (K9 çizgisi) |
| `BidderDocument` | `bidder` · `document_type` (OYS'nin 21 türü; kantinde portör ve adli sicil "çalışan belgesi") · `subject` (`ISTEKLI` · `CALISAN` · `SOFOR` · `REHBER` · `ARAC`) · `subject_name` (şifreli) · `seen_on` · `valid_until` · `is_present` · `attachment` → `Attachment` (isteğe bağlı) · `sensitivity` | Portör ve adli sicil **çalışandan** istenir, istekliden değil ([md. 20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); envanter S-8). Yıllık yenileme ([md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) ve servis belgeleri ([Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9)) `valid_until` ile izlenir. Varsayılan: tarama alınmaz (§5.4) | OYS UYARLA |
| `ScoringCriterion`, `BidderScore` | OYS alanları aynen | Kademeler [Servis EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) ile birebir; tohum kural paketine taşınır. Kademe dışı puan uyarı + gerekçe (plan §1.8; OYS'de sertti) | OYS AYNEN (model) |
| `OabContract` | `kind` (`KANTIN_KIRA` · `SERVIS`) · `tender` · `contractor` → `Bidder` · `asset` · `term` (imzalandığı dönem) · `renewal_of` · `twenty_year_base_date` ([Genelge 2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii)) · `frozen_days` ([EK-2 md. 21](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-21)) · `pandemic_days_applied` (540 gün, [Genelge 2024/35 III-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-4)) · `status` (`TASLAK` → `IMZALANDI` → `YURURLUKTE` → `SONA_ERDI` · `FESHEDILDI`) · `decision_notified_on` · `signed_on` · `start_date`, `end_date` · `site_handover_on` · `milli_emlak_sent_on` · `months_per_year` (9 · 12) · `monthly_rent`, `annual_rent`, `base_amount` · `annual_adjustments` (JSON: yıl, TÜFE, yeni bedel, bildirim tarihi) · `guarantee_kind` (`NAKIT` · `TEMINAT_MEKTUBU` · `YOK`) · `guarantee_amount` · `student_count_at_signing` · `share_split_snapshot` (oranlar ve yerleşim türü) · serviste `academic_years` · `fee_installments_max` · `free_needy_students` (sayı) · `rule_warnings` | (süreç, yüklenici) iptal olmayanlarda tekil (OYS'nin "süreç başına tek sözleşme" kısıtı kalkar, S-16). Yer teslimi imzadan önce olamaz ([md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) — sert. `IMZALANDI` sonrası tutarlar değişmez; TÜFE artışı `annual_adjustments`'a yeni satırdır | OYS UYARLA: kantin için [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) alanları, 20 yıl hesabı, teminat türü; durum geçişleri yazılır (S-11) |
| `ContractInstallment` | `contract` (yalnız kantin) · `period` (yıl-ay) · `due_from`, `due_to` (ayın 5-15'i, [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) · `rent_amount` · `arz_amount` · `il_amount`, `ilce_amount`, `birlik_amount` · `force_majeure_reduction` · `status` (`BEKLIYOR` → `BIRLIK_PAYI_ALINDI` → `DEKONTLAR_TAMAM`; `IPTAL`) · `birlik_entry` → `LedgerEntry` · `il_receipt_seen_on`, `ilce_receipt_seen_on` | (sözleşme, dönem) tekil. Pay hesabı kuruş korunumlu — sert. Serviste üretilmez: ücreti veli taşımacıya öder ([Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6); §15 A-5) | OYS UYARLA: anlamı kantin aylık kira takvimine döner; 1-9 taksit kısıtı kalkar |
| `ShareStatement` | `contract` ya da `asset` · `mode` (`KIRAYA_VERME` · `ISLETME` · `KISA_SURELI_KULLANIM` · `CEZA_TAZMINAT`) · `payer` (`KIRACI` · `BIRLIK`) · `year`, `period` (Q1-Q4) · `gross_amount` · `arz_rate`, `arz_amount` · `expenses` (işletmede) · `net_amount` · `il_amount`, `ilce_amount`, `birlik_amount` · `settlement_type_snapshot` · `due_contract` (izleyen ayın 10'u, [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7)) · `due_regulation` (izleyen ayın 20'si, [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) · `paid_on` · `evidence` → `Attachment` · `late_status` (`ZAMANINDA` · `SOZLESME_VADESI_GECTI` · `YONETMELIK_SURESI_GECTI`) | (sözleşme ya da yer, tür, yıl, dönem) tekil — OYS kısıtına yer eklendi (S-16). Çeyrek başlangıcı DOĞRULANMADI; varsayılan takvim çeyreği (§6.4.11-2). Gecikme zammı hesaplanmaz: [md. 17/1-b-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) 6183 md. 51'e gönderir, o metin korpusta yok; yalnız bilgi notu | OYS UYARLA: `is_metropolitan` → yerleşim türü; iki vade; kısa süreli kullanım ve ceza-tazminat türleri ([md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) |
| `IndexRate` | OYS alanları aynen | `value` = "TÜFE on iki aylık ortalamalara göre yüzde değişim" ([md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21)) diye sabitlenir | OYS AYNEN |

#### 5.2.10 İlişki özeti

- `OabTerm` 1—n `GeneralAssembly`, `BoardMeeting`, `OrganMembership`, `LedgerEntry`, `ExpenseFile`, `MonthlyReport`,
  `Announcement`, `ComplianceItem`, `AuditReport`; 1—1 `OabBudget`; n—1 `RulePackage`, `SchoolYear`.
- `GeneralAssembly` 1—n `AgendaItem`, `OrganMembership` (aday, seçilen, divan); 1—1 `AssemblyMinutes`; açtığı dönem
  `OabTerm.opened_by_assembly`.
- `BoardMeeting` 1—n `BoardMeetingAttendance`, `BoardDecision`; `BoardDecision` n—1 `OfficialBook`; kararı gösteren
  bağlar: `ExpenseFile.decision`, `ReceiptBookRegistry.registration_decision`, `OrganMembership.promoted_by_decision`,
  `GeneralAssembly.call_decision`, `OabBudget.prepared_decision`, `LedgerEntry.decision`.
- `BankAccount` 1—n `BankStatement` 1—n `BankTransaction` n—m `LedgerEntry` (`TransactionMatch` üzerinden);
  `LedgerEntry` n—1 `LedgerAccount`, `TefbisTypeMapping`; 1—n `LedgerEntryLine`; 1—1 `ReceiptLeaf`.
- `ReceiptBookRegistry` 1—n `ReceiptLeaf`; `ExpenseFile` 1—1 ödeme `LedgerEntry`.
- `Tender` 1—n `Bidder`, `TenderCommissionMember`, `TenderApproval`; `Bidder` 1—n `BidderDocument`, `BidderScore`;
  `OabContract` 1—n `ContractInstallment`, `ShareStatement`; `ContractInstallment` 1—1 birlik payı `LedgerEntry`.
- `GeneratedDocument`, `Attachment`, `ComplianceItem` genel bağla (`*_type`, `*_id`) her kayda bağlanır.
- `ParentRoster` yalnız `ImportRun`, `OabTerm`, `GeneralAssembly`'ye bağlanır; ona bağlanan yoktur.

#### 5.2.11 Sürüm 2'ye kalanlar

Personel (K3; yalnız `DOGRUDAN_ISVEREN`): istihdam kartı, yıllık izin kaydı ([5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) saklama), kıdem karşılığı ·
TEFBİS mutabakatının ekranı (M12; modeller §5.2.5'te) · denetim dosyası tabloları (M12b; model gerekmez, kayıtlardan
hesaplanır).

### 5.3 Şifreleme kapsamı

Çekirdek kurallar ailedendir ve §4'te tanımlanır: alan şifrelemesi Fernet, anahtar yokken yazma hata verir
(fail-closed), parola kurulmadan kişi yazan uçlar 409 döner, kör indeks `HMAC-SHA256(HKDF(DEK, "od-kor-indeks"),
normalize(değer))`, `PRAGMA secure_delete=ON`. Bu bölüm hangi alanın hangi korumayı aldığını sabitler.

**İlke.** Kişi adı ya da kişiye ait bilgi içerebilecek her alan ve **her serbest metin** şifrelidir; yapılandırılmış ve
kişisiz alanlar (tutar, tarih, tür, durum, sayı, TEFBİS kodu, kurum adı, kurumsal IBAN) açıktır. Şifreli alanda
veritabanı araması yoktur; listeleme, arama ve ada göre sıralama Python'da çözülerek yapılır (ölçek: yılda birkaç yüz
kayıt, ön değerlendirme §6).

| Model | Şifreli (Fernet) | Kör indeks | Açık |
|---|---|---|---|
| `OabPerson` | `first_name`, `last_name`, `phone` | `name_index` (adaşlık uyarısı, personel eşleştirme) | tür, beyanlar, sayaçlar, durum |
| `Personnel` (okul) | ad-soyad | — (eşleştirme ailenin `name_match.py` yoluyla) | `member_kind`, tarihler |
| `ParentRoster` | `full_name` | `name_index` (adaydan kişi kaydına, yeniden aktarımda çift satır) | `student_class`, katılım işareti |
| `OrganMembership` | `dropped_reason` | — | organ, görev, koltuk, oy, durum, tarihler |
| `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes` | `call_reason`, `notes`, `result_text`, `unaudited_documents_note` | — | tarihler, sayılar, yeter sayı, ibra sonucu, oylar |
| `BoardMeeting`, `BoardDecision` | `agenda`, `text`, `dissent` | — | no, tarih, defter sıra no ve sayfa, oy sayıları |
| `AuditReport` | `findings`, kontrol listesi notları | — | tür, tarih, bayrak |
| `BankTransaction` | `description`, `counterparty` | — | tarih, tutar, bakiye, referans, parmak izi |
| `LedgerEntry`, `LedgerEntryLine` | `description`, `donor_name`, `donor_tckn` | — (T.C. kimlik no'ya kör indeks **yok**) | tutar, tarih, yön, TEFBİS kodları, belge no ve tarihi, bağlar |
| `LedgerAccount` | `purpose` | — | tür, bağlar |
| `ExpenseFile` | `title`, `supplier_name` | — | tutarlar, tüzel VKN, VİF no, durum |
| `DocumentRecord` | `counterparty`, `subject` | — | no, tarih, yön, dış sayı |
| `Bidder` | `legal_name`, `contact_address`, `contact_phone`, `contact_email` | — | tür, tüzel VKN, teklif tutarı (kantin), engel işaretleri |
| `BidderDocument` | `subject_name` | — | belge türü, görüldü ve geçerlilik tarihi |
| `ReceiptLeaf`, `HandoverItem`, `TenderCommissionMember` | `cancel_reason`, `note`, `dissent` | — | numaralar, durumlar |
| `ComplianceItem` | `justification` | — | kural kimliği, paket, ileti, tarihler |
| `Attachment`, `GeneratedDocument` | dosyanın kendisi (dosya düzeyinde), `original_name` | — | sha256, tür, boyut, tarih |

**Dosyalar.** `Attachment` ve `GeneratedDocument` dosyaları DEK'ten HKDF ile türeyen dosya anahtarıyla diskte şifreli
durur (bilgi dizgesi §4 kimlik sabitlerinde). Açık hâli yalnız kullanıcı kaydet ya da yazdır dediğinde oluşur;
geçici kopyanın temizlenmesi §4'tedir.

**T.C. kimlik no (K9).** Yalnız `LedgerEntry.donor_tckn`; yalnız `donor_tckn_enabled` açıkken yazılır. Ekranda
maskeli; maskesiz gösterim yalnız `yonetici` rolünde ve erişim günlüğüyle; hiçbir dışa aktarım dosyasına girmez (§8.3).
Kör indeksi yoktur: gruplama gerekmez, kalıcı bir indeks de takma kimlik olurdu. Kişi, organ, istekli ve sözleşme
kayıtlarında alan hiç yoktur.

### 5.4 Saklama ve anonimleştirme

Birlik defter ve belgeleri [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) ve [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) gereği Devlet Arşiv Hizmetleri Hakkında Yönetmelikteki süreler kadar
okulda saklanır; o Yönetmelik süreyi kurumun saklama planına bırakır ([Arşiv Yön. md. 9/4](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-9), [Arşiv Yön. md. 24](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-24)) ve MEB saklama planı
korpusta yoktur (§6.4.11-9). Bu yüzden program birlik kaydını **hiç silmez**; imha kurumun Ayıklama ve İmha
Komisyonunun işidir ve birim arşivinde yapılmaz ([Arşiv Yön. md. 17/1](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-17); tereddütte saklanır, [Arşiv Yön. md. 20/2](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-20)). Program yalnız amacı
biten kişisel veriyi siler ya da boşaltır ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7)).

| Veri | Kural | Süre | Dayanak |
|---|---|---|---|
| Birlik kayıtları: organ ve toplantılar, kararlar, mali kayıtlar ve banka hareketleri, koçan ve yapraklar, harcama dosyaları, sözleşmeler, üretilen evrak, sapma kayıtları, denetim izi | Silinmez, anonimleştirilmez | Saklama planına göre — OAB evrakı için süre **DOĞRULANMADI** | [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [Arşiv Yön. md. 17/1](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-17), [Arşiv Yön. md. 18](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-18), [Arşiv Yön. md. 20/2](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-20) |
| Veli listesi (`ParentRoster`) | Dönem kapanışında bütün satırlar silinir; kapanışın sert adımıdır. Genel kuruldan sonra elle de silinebilir | Dönem kapanışına kadar | T5; [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7) |
| Genel kurul katılım kaydı | Kişi düzeyinde işaret listeyle silinir; sayılar kalır (aşağıdaki öneri) | Sayılar: birlik kaydıyla | [md. 10/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1 |
| Bağışçı T.C. kimlik no'su (K9 açıksa) | TEFBİS'e girildikten sonra dönem kapanışında alan boşaltılır, "silindi" izi kalır | En geç dönem kapanışı | K9; [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4) (§15'e öneri B-8) |
| Kişi telefonu | Son üyeliğinin bittiği dönemin kapanışında boşaltılır; seçilmeyen adayınki de | Dönem kapanışı | [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4) (§15'e öneri B-7) |
| Kişi adı ve türü | Organ üyesi olmuş ya da aday olmuş kişide kalır (karar defteri, tutanak, aday listesi ve dönem sayacı bağı) | Birlik kaydıyla | [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Kantin çalışanı, servis şoförü ve rehber personel belgeleri (özel nitelikli) | **Varsayılan: tarama alınmaz**; yalnız "görüldü" tarihi ve geçerlilik sonu. Asıl kâğıt birlik dosyasında ([md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)). Tarama eklenirse şifreli, erişim günlüklü, `OZEL_NITELIKLI`; sözleşme sona erdikten sonra imha adayı (kopya; asıl arşivde) | Sözleşme sonu + 2 yıl (öneri) | [md. 20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9); [KVKK md. 6](../mevzuat/6698-kvkk.md#madde-6) (§15'e öneri B-5) |
| Seçilmeyen isteklinin iletişim bilgisi | Süreç kesinleştikten sonra adres, telefon, e-posta boşaltılır; ad kalır (tutanaklarda geçer) | Kesinleşme + 2 yıl (öneri) | [KVKK md. 4/2-d](../mevzuat/6698-kvkk.md#madde-4) (B-5 ile birlikte) |
| İçe aktarılan ham dosyalar (banka, TEFBİS, e-Okul) | Hiç saklanmaz; yalnız sha256 ve parti özeti | — | [KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4) |
| Personel ve SGK belgeleri (sürüm 2) | Silinmez (silme kilidi) | İlgili yılı izleyen yıl başından 10 yıl (§6.4.10 yorumu) | [5510 md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) |
| Hassas okuma ve erişim günlüğü | Süre dolunca silinir | 2 yıl (öneri; DOĞRULANMADI) | [KVKK md. 12](../mevzuat/6698-kvkk.md#madde-12) güvenlik tedbiri (§15'e öneri B-9) |

**Genel kurul katılım kaydı — öneri (T5'in açık noktası; §15'e öneri B-11).**

- **Saklanan (kalıcı, kişisiz):** genel kurul ve toplantı başına imzalayan üye sayısı; türe göre dağılım (veli ve
  kursiyer, öğretmen, yönetici, hayırsever, diğer); velisi katılan öğrenci sayısı ve o günkü öğrenci mevcudu ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2)
  Tablo 1'in iki sütunu; oran hesaplanır); dondurulmuş yeter sayı ve sağlanıp sağlanmadığı; gözlemci öğrenci sayısı
  ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)).
- **Basılan cetvelin izi:** katılım cetvelinin `GeneratedDocument` kaydı (tür, tarih, satır sayısı, sha256). İmzalı
  asıl genel kurul tutanak dosyasındadır ([md. 23/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)), okulda saklanır ([md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) ve devir kalemidir ([md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10)) —
  programın asıl kaydı kâğıttır.
- **Saklanmayan:** kişi düzeyindeki "katıldı" işareti (yalnız sayımı kolaylaştırmak için `ParentRoster` satırında
  durur, listeyle silinir) ve imzalı cetvelin taraması (varsayılan alınmaz: asıl zaten saklanıyor, tarama aynı kişisel
  veriyi ikinci kez ve süresiz tutardı).
- **Neden:** katılım sayısı yeter sayının (sert kural) girdisidir; altın kural 4 gereği dondurulur ve yalnız gerekçeli
  düzeltme satırıyla değişir. Kişi listesi programdaki işi (cetvel basımı ve sayım) bitince amacını yitirir
  ([KVKK md. 4/2-ç](../mevzuat/6698-kvkk.md#madde-4), [KVKK md. 7](../mevzuat/6698-kvkk.md#madde-7)). Bu düzen TKB E.4 Tablo 1'i ve yeter sayı denetimini tek başına karşılar.

**Çalışma biçimi** (Kütüphane Defteri §6.4 kalıbı): (1) aday tespiti açılışta ve gün değişiminde yapılır, pano kartı
düşer; (2) yönetici onayıyla tetik çalışır; (3) tetikten önce `pre-anonim-<tarih>.odbak` yedeği alınır ve 14 günlük
rotasyona girer; (4) her silme ve boşaltma denetim izine kişisiz satır yazar (tür, adet, tetik); (5) dönem kapanışındaki
silmeler (veli listesi, T.C. kimlik no, telefon) kapanış işleminin parçasıdır, kapanış onayı yeter. Silinen veri günlük
yedeklerde ve `pre-kapanis` yedeğinde en çok 14 gün kalır; kullanıcının dışarı aldığı şifreli yedekler okulun
elindedir, imha kuralı kılavuzda yazılır.

---

## 6. Kural paketi

Kural paketi, programın koyduğu her sayısal ve yapısal hükmün (oran, süre, çarpan, sınır, organ bileşimi, vade)
**tek kaynağıdır** (altın kural 2). Kodda bu değerler sabit olarak yazılmaz; servisler değeri `kural("<id>")` ile
okur. Paket mevzuat değildir, korpusa atıftır: her kural `docs/mevzuat/` içindeki bir çapaya ve fıkra/bent
düzeyinde bir hükme bağlanır (altın kural 1). Doğrulanamayan hüküm pakete girmez; §6.4 sonunda ayrı listelenir.

**Paket okul ayarı değildir.** Okuldan okula değişen ve mevzuatın okula bıraktığı değerler okul kartında ya da
ayarlarda durur, kural paketine girmez ve arayüzde "Yönetmelik gereği" diye sunulmaz:

| Okul ayarı (kural değil) | Nerede | Kuralla bağı |
|---|---|---|
| Öğrenci mevcudu | okul kartı (F1b) | `genel_kurul.kucuk_okul_esik` ile karşılaştırılır |
| Yerleşim türü (büyükşehir · büyükşehir olmayan il merkezi · diğer) | okul kartı | `pay_dagitimi.*` kuralının `kosul` alanı |
| Kademe (ilkokul · ortaokul · ortaöğretim · okul öncesi · yaygın) | okul kartı | `temsilci.*` kurallarının `kosul` alanı |
| Kantin işletme modu (kiraya veriliyor · birlikçe işletiliyor · kantin yok) | okul kartı | `arz_bedeli.kira_oran` ya da `arz_bedeli.isletme_oran` |
| Personel çalıştırma biçimi | okul kartı | `personel.*` kuralları yalnız doğrudan işverende |
| Ders yılı, dönemler, tatiller, iş günü takvimi | kurulum sihirbazı | süre hesapları (iş günü, "eğitim-öğretim yılı içinde") |
| Kayıt-kabul ve diploma dönemi tarihleri | ayarlar | `bagis.kayit_doneminde_toplanmaz` |
| Küçük alım tutar sınırı, sürekli ödemeler için dönem başı genel kararı | ayarlar (YK karar no'suyla) | `harcama.*` uyarılarının gerekçesi (saha.md soru 6) |
| YK aylık toplantı günü, DK denetim planı tarihleri | ayarlar / organ ekranı | takvim; `yonetim_kurulu.toplanti_sikligi`, `denetleme_kurulu.inceleme_yilda_en_az` |
| TEFBİS işlem tipi eşlemesi | `TefbisTypeMapping` | kural değil; okul kendi TEFBİS listesini girer (K6, F0-5 d) |
| İnternet bankacılığında üçüncü onay | ayarlar | mevzuat gereği diye sunulmaz (F0-5 c) |
| Bağışçı T.C. kimlik no'su | ayarlar (varsayılan kapalı) | K9 |

### 6.1 Şema

Paket dosyası `backend/apps/oab/kurallar/paketler/OAB-2023.12.r<n>.json`, şeması aynı dizinde
`kural-paketi.schema.json` (JSON Schema 2020-12). Dosyalar sürümle birlikte dağıtılır, salt okunurdur; kullanıcı
kural düzenleyemez.

**Üst düzey alanlar**

| Alan | Tip | Zorunlu | Anlamı |
|---|---|---|---|
| `paket` | dize, `^OAB-\d{4}\.\d{2}$` | evet | Paket kimliği: dayandığı OAB Yönetmeliği metninin son değişikliğinin RG yılı ve ayı (v1: `OAB-2023.12` = RG 01.12.2023/32386) |
| `rev` | tamsayı ≥ 1 | evet | Aynı kimlikte içerik revizyonu (kural ekleme, başka metindeki değişiklik, düzeltme) |
| `sema_surumu` | tamsayı | evet | Bu şemanın sürümü (v1: 1) |
| `baslik` | dize | evet | İnsan okur ad |
| `korpus_teyit` | tarih `gg.aa.yyyy` | evet | Atıfların korpusa karşı son denetlendiği gün |
| `degisiklik_notu` | dize | evet | Bu revizyonda ne değişti (§6.2) |
| `kurallar` | dizi | evet | Aşağıdaki kural nesneleri |

**Kural nesnesi**

| Alan | Tip | Zorunlu | Anlamı |
|---|---|---|---|
| `id` | dize, `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` | evet | `alan.konu`, ASCII snake_case, tam bir nokta. Alanlar: `genel_kurul`, `yonetim_kurulu`, `denetleme_kurulu`, `uyelik`, `temsilci`, `bagis`, `gelir`, `etkinlik`, `makbuz`, `harcama`, `bildirim`, `duyuru`, `vergi`, `denetim`, `arz_bedeli`, `pay_dagitimi`, `kira`, `kantin`, `servis`, `personel`. Kimlik bir kez yayımlanınca değişmez, silinmez |
| `deger` | sayı · ondalık dize · mantıksal · liste · nesne | evet | Kuralın değeri. Para ve oran **ondalık dize** (`"0.03"`), kayan nokta yasak |
| `birim` | enum | evet | `gun` (takvim günü) · `is_gunu` · `hafta` · `ay` · `yil` · `takvim_ayi` · `ayin_gunu` · `kisi` · `ogrenci` · `oran` · `puan` · `adet` · `tarih` · `mantiksal` · `liste` · `tablo` |
| `karsilastirma` | enum | evet | `en_az` · `en_cok` · `kucuktur` · `esit` · `carpan` · `parametre` · `liste_icinde` · `tablo` |
| `tur` | `uyari` · `sert` | evet | Aşağıdaki anlamda |
| `madde` | nesne `{capa, fikra?, bent?, alt_bent?, fikra_bicimi?}` | evet | Asıl dayanak. `capa` = `<dosya>#<çapa>` (`docs/mevzuat/` köküne göre). `fikra` numaralı fıkra ya da paragraf sırası; `fikra_bicimi` = `numarali` (varsayılan) ya da `paragraf` (kanunlar, EK-2, genelgeler) |
| `ek_madde` | `madde` dizisi | hayır | Ek dayanaklar (ör. md. 9/6 olağanüstü için) |
| `aciklama` | dize | evet | Hükmün bir cümlelik özeti (lafız değil) |
| `uyari_metni` | dize (yer tutuculu) | `uyari`da evet | Ekranda görünen metin; atıf `madde`den otomatik eklenir |
| `kosul` | nesne | hayır | Kuralın uygulandığı okul kartı durumu (ör. `{"okul.kademe": ["ortaogretim"]}`) |
| `yururluk` | `{baslangic, bitis}` (`gg.aa.yyyy`, `bitis` boş olabilir) | evet | Bu değerin geçerli olduğu aralık: dayanak fıkranın bugünkü lafzının yürürlüğe girdiği tarih (şerhteki RG tarihi; şerh yoksa metnin yayımı) |
| `giris` | `F1c`…`F8` | evet | Kuralın pakete girdiği faz (§6.2-4) |
| `yorum` | dize | hayır | Değer bir yorum içeriyorsa açıkça yazılır (ör. "ilk hafta = 7 takvim günü"); arayüzde "yorum" etiketiyle görünür |

**`tur` alanının anlamı.** `sert`: program kuraldan sapan kaydı kaydetmez; hesap parametresiyse değer kullanıcıca
değiştirilemez (yalnız yeni paket revizyonuyla). `uyari`: program doğrusunu gösterir, sapma **gerekçeyle** kaydedilir;
gerekçe, kural kimliği ve paket revizyonuyla birlikte denetim izine ve `ComplianceItem` kaydına düşer (altın kural 3).
Sert yalnız şu üç durumda kullanılır: hesap bütünlüğü (toplamlar, oranlar, numara tekilliği, kapanmış dönem, yeter
sayı hesabı) · hukuken geçersiz işlem (kantin isteklisinde suç ve hısımlık engeli, mülki amir onayı olmadan
kesinleştirme; F1 kapısındaki organ bileşimi kişi türleri) · değeri hesapta kullanılan parametre.

**Örnek (bir kural; `uyari` kuralında ayrıca `uyari_metni` vardır, ör. "Duyuru ile toplantı arasında {fark} gün var; en az {deger} gün olmalı."):**

```json
{
  "paket": "OAB-2023.12",
  "rev": 1,
  "sema_surumu": 1,
  "baslik": "MEB Okul-Aile Birliği Yönetmeliği (son değişiklik RG 01.12.2023/32386) ve bağlı metinler",
  "korpus_teyit": "31.10.2026",
  "degisiklik_notu": "F1c: yeter sayı, organ bileşimleri, dönem sınırları, temsilciler, F1c listesindeki süre ve oranlar",
  "kurallar": [
    {
      "id": "pay_dagitimi.il_merkezi",
      "deger": {"birlik": "0.80", "ilce": "0.00", "il": "0.20"},
      "birim": "oran",
      "karsilastirma": "tablo",
      "tur": "sert",
      "madde": {"capa": "meb-okul-aile-birligi-yonetmeligi.md#madde-17", "fikra": "1", "bent": "a", "alt_bent": "2"},
      "ek_madde": [{"capa": "meb-okul-aile-birligi-yonetmeligi.md#madde-17", "fikra": "1", "bent": "b", "alt_bent": "2"}],
      "aciklama": "Büyükşehir statüsünde olmayan il merkezlerindeki birliklerde ilçe payı ayrılmaz, %20 il MEM hesabına yatırılır.",
      "kosul": {"okul.yerlesim_turu": ["il_merkezi_buyuksehir_degil"]},
      "yururluk": {"baslangic": "09.02.2012", "bitis": null},
      "giris": "F1c",
      "yorum": "Yönetmelik 'gelirin %20'si' der; taban net tutar (arz düşülmüş) kabul edildi, birlik %80 ile toplam %100."
    }
  ]
}
```

**Erişim.** `kural(id, tarih=None, donem=None)` dönemin bağlı paketinden (§6.2), `tarih`i kapsayan yürürlük
aralığındaki değeri döndürür; `tarih` verilmezse olayın tarihi (duyuru, toplantı, tahsilat) kullanılır, işlem anı
değil. `denetle(id, ...)` sonucu `{durum: uygun|uyari|sert, mesaj, atif, paket, rev}` döner; `atif` ekranda ve
gerekçe kaydında "md. 9/3" biçiminde görünür. Koddaki bilinmeyen kimlik testte yakalanır (§6.3 D6); çalışma anında
yine de olursa ilgili yazma işlemi yapılmaz (fail-closed).

### 6.2 Sürümleme ve dönem bağı

1. **Kimlik ve revizyon.** `paket` OAB Yönetmeliğinin metin durumunu izler (Yönetmelik değişince yeni kimlik:
   `OAB-<yyyy>.<aa>`). Aynı kimlik altında her içerik değişikliği `rev`'i bir artırır: yeni kural eklemek, bağlı
   başka bir metnin (EK-2, Genelge 2024/35, Servis Usul ve Esasları, Okul Servis Araçları Yön.) değişmesi, bir hatanın
   düzeltilmesi. Yayımlanan bir revizyon dosyası değiştirilmez; yeni dosya eklenir.
2. **Kurallar fazlarıyla birlikte girer.** Pakete bir kural, onu kullanan kodun ve davranış testinin geldiği fazda girer
   (§6.4 "Giriş" sütunu). F1c'de `r1` = plan §2.3'teki liste + organ ve temsilci kuralları; F2…F8 her biri `rev`'i
   artırır. Ekleme mevcut değerleri değiştirmez; bu yüzden açık dönemin yeni revizyona geçişi hesap değiştirmez.
3. **Değer değişirse eski kayıt kalır.** Mevzuat bir değeri değiştirirse aynı `id` ile ikinci bir kayıt eklenir: eskinin
   `yururluk.bitis`'i değişiklikten önceki gün, yeninin `baslangic`'ı değişiklik günüdür. Aynı kimliğin aralıkları
   çakışamaz (D2). Böylece açık dönemde değişiklikten önce olmuş olaylar eski değerle hesaplanmaya devam eder.
4. **Dönem bağı.** Her birlik dönemi (`OabTerm`, T3: genel kuruldan genel kurula) açılışta programla gelen en yeni
   revizyona bağlanır. Bağ bir `RulePackage` kaydıdır: `paket`, `rev`, içeriğin **dondurulmuş kopyası** (JSON) ve
   SHA-256 özeti veritabanında tutulur. Dönemin bütün hesapları, uyarıları ve evrakı bu kopyadan okunur; program
   güncellemesi dosyayı değiştirse ya da kaldırsa bile bağlı dönem etkilenmez.
5. **Açık dönemin geçişi.** Yeni revizyon geldiğinde açık dönem kendiliğinden geçmez. Yönetici "kural paketi
   güncellemesi" ekranında farkı görür (eklenen, biten, değişen kurallar; uyarısı değişecek kayıtların listesi) ve
   onaylar; geçiş denetim izine kim-ne-zaman ve eski/yeni revizyonla yazılır. Geçiş geri alınabilir (dönem kapanana
   kadar).
6. **Kapanmış dönem değişmez.** Dönem kapanışında (F4) bağ kilitlenir. Kapanmış dönemde revizyon geçişi **sert
   engeldir** (hesap bütünlüğü). Kapanmış dönemin raporu ve evrakı yeniden basıldığında içerik özeti (evrak içerik
   modelinin kanonik JSON'unun SHA-256'sı, §9.1) aynı çıkar. Yedekten geri yüklenen eski dönem de kendi kopyasıyla
   gelir; program o revizyonu artık taşımasa bile hesap yapılır.
7. **Değişiklik akışı.** Mevzuat değişikliği → korpus güncellenir ([BENIOKU §8](../mevzuat/BENIOKU.md)) → yeni kayıt
   ya da yeni kimlik → §10 testleri → sürüm notu → program güncellemesi. Kural paketi yalnız program sürümüyle
   değişir; kullanıcının kural ekleme, silme, değer değiştirme yolu yoktur.

### 6.3 Doğrulama ve atıf kilidi

| # | Denetim | Ne denetler | Ne zaman | Başarısızlıkta |
|---|---|---|---|---|
| D1 | Şema | JSON Schema'ya uygunluk; zorunlu alanlar; ondalıkların dize olması; tarih biçimi | açılış + test | Paket yüklenmez → kural kullanan yazma uçları kapalı (fail-closed), ana ekranda hata; okuma açık |
| D2 | Kimlik | `id` biçimi; aynı `id`'nin yürürlük aralıkları çakışmaz; yayımlanmış `id` silinmemiş (önceki revizyonla karşılaştırma) | açılış + test | D1 gibi |
| D3 | **Atıf kilidi — çapa** | `madde.capa` ve her `ek_madde.capa` için: dosya `docs/mevzuat/` altında var; adı `.draft-` ile başlamıyor; `bilgi/` altında değil (özelge ve sirküler kural dayanağı olamaz); frontmatter `belge-turu` "denetim rehberi" değil (TKB E.4 kabul ölçütüdür, mevzuat değil); dosyada `<a id="<çapa>"></a>` var; frontmatter `yururlukte: false` ise kuralın `yururluk.bitis`'i dolu | test (Docker; F1 kapısı) | Test kırmızı → faz kapanmaz |
| D4 | **Atıf kilidi — fıkra ve bent** | Çapadan bir sonraki çapaya kadar olan madde gövdesinde: `numarali` biçimde `(<fıkra>)` geçer; `paragraf` biçimde o sırada paragraf var; `bent` için `<bent>)` geçer; atıf yapılan fıkra `(Mülga:` ile başlamıyor | test | D3 gibi |
| D5 | Tutarlılık | `genel_kurul.yeter_sayi_taban` = YK asıl + yedek + DK asıl + yedek (16); her pay tablosunun toplamı 1,00; `arz_bedeli.sozlesme_vade_gunu` < `arz_bedeli.yonetmelik_vade_gunu`; EK-3 kriter azamileri toplamı 25; `genel_kurul.yeter_sayi_carpan` > `genel_kurul.kucuk_okul_carpan` | açılış + test | D1 gibi |
| D6 | Kapsam | Koddaki her `kural("…")` çağrısının kimliği pakette var (statik tarama); paketteki her kuralın `@pytest.mark.kural("<id>")` işaretli en az bir testi var (§10) | test | D3 gibi |
| D7 | Bütünlük | Dağıtılan dosyanın SHA-256'sı sürüm bildirimindeki değerle; dönemin dondurulmuş kopyasının özeti `RulePackage` kaydıyla aynı | açılış | Dönem salt okur açılır, yönetici uyarılır (yedekten geri yükleme önerisi) |
| D8 | Sabit taraması (sezgisel) | `apps/oab` iş kodu (testler ve `kurallar/` hariç) içinde paket değerlerinin çıplak yazımı: `Decimal("0.03")`, `"0.80"`, `timedelta(days=15)`, `* 4` gibi kalıplar; izin listesiyle | test (lint adımı) | Uyarı; gözden geçirmede kapanır |

Atıf kilidi (D3-D4) çalışma anında yapılmaz: korpus pakete girmez, dağıtılan programda `docs/` yoktur. Kilidin
güvencesi, korpusta çapası doğrulanmamış bir kuralın sürüme hiç girememesidir. Çapalar korpusta değişmez
([BENIOKU §2](../mevzuat/BENIOKU.md)); bir çapa adı değişirse D3 bütün bağlı kuralları kırmızıya çevirir.

### 6.4 v1 içeriği (`OAB-2023.12`)

Kısaltmalar: atıfta yalın madde numarası **MEB Okul-Aile Birliği Yönetmeliği**dir. EK-2 = aynı Yönetmeliğin Kantin
Kiralama Sözleşmesi (Genel Şartlar) · G.2024/35, G.2011/40 = MEB genelgeleri · U-E = Okul Servis Araçlarının
Çalıştırılmasına İlişkin Usul ve Esaslar · OSAY = Okul Servis Araçları Yönetmeliği · OKY = Ortaöğretim Kurumları
Yön. · OÖİKY = Okul Öncesi Eğitim ve İlköğretim Kurumları Yön. · SEY = Sosyal Etkinlikler Yön. · RPD = Rehberlik ve
Psikolojik Danışma Hizmetleri Yön. · HEY = Hijyen Eğitimi Yön. · TMY = Taşınır Mal Yön. · KDVK = 3065 · "Tür" S = sert,
U = uyarı · "Giriş" = pakete girdiği faz; parantezde davranış testinin geldiği faz.

#### 6.4.1 Genel kurul

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `genel_kurul.olagan_son_ay` | Ekim (ayın son günü dâhil) | U | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | Ders yılının başladığı takvim yılının 31.10'u |
| `genel_kurul.yeni_okul_ay` | 2 ay | U | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Okulun açıldığı tarihten; çağrıyı okul müdürü yapar (müdür rolünün yazısı) |
| `genel_kurul.ilan_en_az_gun` | 15 gün | U | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c (F2) | Duyuru günü ile toplantı günü arası ≥ 15 |
| `genel_kurul.ilan_kanallari` | elden yazılı · ilan panosu · internet sayfası | U | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F2 | Üçü birlikte; her biri için kanıt alanı (tarih, kim) |
| `genel_kurul.yeter_sayi_taban` | 16 | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | YK 5+5 + DK 3+3; üyelik kayıtlarından sayılmaz (OYS S-1 düzeltmesi); D5 ile bileşim kurallarına bağlı |
| `genel_kurul.yeter_sayi_carpan` | ×4 | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c | 16 × 4 = 64; olağanüstü GK'de de (OYS S-2 düzeltmesi) |
| `genel_kurul.kucuk_okul_carpan` | ×2 | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F1c | 16 × 2 = 32 |
| `genel_kurul.kucuk_okul_esik` | mevcut < 100 | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c | "Yüzün altında": 99 → ×2, 100 → ×4; mevcut okul kartından, GK kaydına anlık değer olarak yazılır |
| `genel_kurul.ikinci_toplanti_en_gec_gun` | 30 gün | U | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | Birinci toplantı gününden; OYS'de yoktu |
| `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | evet | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F1c (F2) | Olağan ve olağanüstü GK; olağanüstüde uygulanması kullanıcı kararı (31.10.2026, §15 A-1) |
| `genel_kurul.karar_cogunlugu` | katılanların çoğunluğu | S | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); 9/6 | 09.02.2012 | F2 | Oylama sonucu alanından hesaplanır |
| `genel_kurul.gundem_degisikligi` | oy çokluğu | S | [9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Ekleme, çıkarma, sıra değişikliği oylanır |
| `genel_kurul.olaganustu_cagiranlar` | YK · okul müdürü · DK (14/5) · üyelerin %10'u · okul müdürü (25/2) | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9); [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); [14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) | 01.12.2023 | F2 | "Çağıran" alanı formda zorunlu; listede olmayan → uyarı |
| `genel_kurul.olaganustu_basvuru_oran` | %10 (0,10) | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Üye sayısı elle girilir; başvuru eki kanıt |
| `genel_kurul.olaganustu_gundeme_baglilik` | evet | U | [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | 09.02.2012 | F2 | Çağrıda olmayan gündem maddesi → uyarı |
| `genel_kurul.divan_uye_turleri` | veli · 18 yaşını doldurmuş kursiyer | U | [10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) | 01.12.2023 | F2 | Divan başkanı ve kâtip; açık oy |
| `genel_kurul.secim_bicimi` | asıl ve yedek liste hâlinde açık oy | U | [10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10); [11/1-a, b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 01.12.2023 | F2 | DK öğretmen koltukları GK'da oylanmaz (öğretmenler kurulu seçer) |

#### 6.4.2 Yönetim kurulu ve ortak üyelik

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `yonetim_kurulu.asil_uye` | 5 | U | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 01.12.2023 | F1c | Eksik bileşim uyarı; yeter sayı tabanını etkilemez |
| `yonetim_kurulu.yedek_uye` | 5 | U | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); 11/1-a | 01.12.2023 | F1c | — |
| `yonetim_kurulu.uye_turleri` | veli · 18 yaşını doldurmuş kursiyer · okul yaptıran hayırsever (isterse) | S | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F1c | F1 kapısı: "YK'ye veli olmayan eklenemez"; öğretmen ve yönetici türü reddedilir |
| `yonetim_kurulu.okul_muduru_uye_olamaz` | evet | S | [12/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [27/2-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | 01.12.2023 | F1c | Okul kartındaki müdür, veli olsa da eklenemez. **Yorum + proje kararı** (CLAUDE.md §2-6): açık yasak yok, engel md. 27'deki denetim konumundan |
| `yonetim_kurulu.gorev_suresi_yil` | 1 yıl | U | [12/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Dönem bitişi takvimde |
| `yonetim_kurulu.gorev_bolumu_gun` | 7 gün | U | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Seçimden ve yedek çağrısından sonra; **yorum:** "ilk hafta" = izleyen 7 takvim günü (§15 KE-12) |
| `yonetim_kurulu.gorevler` | başkan · başkan yardımcısı · muhasip · sekreter, her biri tek asıl üyede | S | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 09.02.2012 | F1c | Tekillik (müşterek imza buna bağlı) |
| `yonetim_kurulu.secilme_siniri` | en fazla 4 | U | [12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F1c | Başkan **ve üyeler** (OYS yalnız başkanı sayıyordu, S-4); kişi geçmişi eksikse uyarı, engel değil |
| `yonetim_kurulu.tek_birlik` | başka birlik yönetiminde görev yok (beyan) | U | [12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F1c | Beyan alındı işareti + tarih |
| `uyelik.suc_engeli_beyani` | beyan alındı + tarih | U | [12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12); [14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 01.12.2023 | F1c | YK, DK, harcama komisyonu; beyan içeriği ve adli sicil verisi tutulmaz (KVKK) |
| `uyelik.ayrilan_veli_devam` | YK sayısı toplantı yeter sayısının (4) altına düşerse velinin üyeliği olağanüstü GK'ye kadar sürer | U | [7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) | 01.12.2023 | F1c | "Öğrencisi ayrıldı" düşürme önerisinde denetlenir |
| `yonetim_kurulu.yedek_cagirma` | oy sırasıyla | U | [13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c | Sıra dışı çağrı gerekçe ister (yedeğin çekilmesi vb.) |
| `yonetim_kurulu.toplanti_yeter_sayi` | en az 4 asıl üye | S | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Altında toplantı "yapılamadı" kaydedilir, karar girilemez |
| `yonetim_kurulu.karar_yeter_sayi` | en az 3 kabul oyu | S | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Altında karar "alınmadı" |
| `yonetim_kurulu.toplanti_sikligi` | ayda bir (eğitim-öğretim yılı içinde) | U | [13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F3 | Ders yılı takviminden; toplantısız ay → uyarı |
| `yonetim_kurulu.devamsizlik_siniri` | üst üste 3 özürsüz | U | [13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c (F3) | Toplantılar üzerinden sayılır (kayıtlar değil, S-19); program öneri üretir, düşürme kullanıcı onayıyla; yalnız YK |
| `yonetim_kurulu.olaganustu_cagri_ay` | 1 ay | U | [13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F3 | YK yedeklerle karar yeter sayısının (3) altına düşünce; çağrı başkan ya da okul müdürü |

#### 6.4.3 Denetleme Kurulu

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `denetleme_kurulu.asil_uye` | 3 | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 01.12.2023 | F1c | — |
| `denetleme_kurulu.yedek_uye` | 3 | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 01.12.2023 | F1c | — |
| `denetleme_kurulu.koltuklar` | veli/18+ kursiyer 1+1 (GK seçer) · öğretmen 2+2 (öğretmenler kurulu seçer) | S | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | 01.12.2023 | F1c | Hayırsever veli koltuğuna giremez (OYS S-8). Öğretmen yetmezse il/ilçe MEM onayıyla başka okulun öğretmeni (onay no alanı) |
| `denetleme_kurulu.gorev_bolumu_gun` | 7 gün | U | [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 01.12.2023 | F1c | GK'den sonraki ilk hafta; yorum KE-12 |
| `denetleme_kurulu.gorev_suresi_yil` | 1 yıl | U | [14/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | — |
| `denetleme_kurulu.baskan_secilme_siniri` | en fazla 3 | U | [14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | Yalnız DK başkanlığı sayılır; YK sayacından ayrı |
| `denetleme_kurulu.inceleme_yilda_en_az` | 2 | U | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F4 | Ara raporlar YK'ye, nihai rapor GK'ye |
| `denetleme_kurulu.yk_uyesi_olamaz` | evet | S | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 31.10.2026 | F1c | Aynı kişi aynı dönemde YK'de ve DK'de olamaz; dayanak lafız değil, **kullanıcı kararı** (31.10.2026): DK, YK'nin işlemlerini denetler |
| `denetleme_kurulu.ogretmen_gorevlendirme_ay` | 4 aydan fazla → yedek | U | [14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | 09.02.2012 | F1c | Başka kurumda görevlendirme süresi girilir |

#### 6.4.4 Birlik temsilcileri

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `temsilci.odul_disiplin_kurulu` | 1 veli + 1 yedek | U | [OKY 185/1-ç](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185); [OKY 186/1](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-186) | 07.09.2013 | F1c | `kosul`: ortaöğretim |
| `temsilci.davranis_degerlendirme_kurulu` | 1 veli | U | [OÖİKY 57/2-c](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57) | 26.07.2014 | F1c | `kosul`: ortaokul |
| `temsilci.sosyal_etkinlikler_kurulu` | 1 veli | U | [SEY 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6) | 08.06.2017 | F1c | Birlik etkinliklerini de inceler (md. 6/2) |
| `temsilci.kontenjan_komisyonu` | 1 veli | U | [OKY 25/1-a](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25) | 13.09.2014 | F1c | `kosul`: ortaöğretim |
| `temsilci.rpd_yurutme_komisyonu` | 1 temsilci | U | [RPD 16/2-e](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16) | 14.08.2020 | F1c | Hayat boyu öğrenme kurumlarında yok (16/3) |
| `temsilci.tasimaci_tespit_komisyonu` | birlik başkanı | U | [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3); [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) | 25.10.2017 | F1c | Doğrudan üyelik; seçim yok |
| `temsilci.muhammen_bedel_komisyonu` | birlik başkanı | U | [19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) | 01.12.2023 | F1c | Komisyonu valilik/kaymakamlık kurar (bilgi satırı) |
| `temsilci.kiralama_ihale_komisyonu` | birlik başkanı | U | [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F1c | Bilgi satırı; hısımlık yasağı `kantin.hisimlik_derecesi` |
| `temsilci.kampus_yonetimi` | başkan ya da 1 YK üyesi (ihtiyaç hâlinde) | U | [13/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F1c | `kosul`: eğitim kampüsünde |

#### 6.4.5 Gelir, bağış, makbuz, etkinlik

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `bagis.elden_yatirma_is_gunu` | 5 iş günü | U | [16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F1c (F3) | Kabulü izleyen iş gününden sayılır; iş günü takvimi okul ayarından; kasa sayacı |
| `bagis.kayit_doneminde_toplanmaz` | kayıt-kabul ve diploma döneminde bağış yok | U | [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15); [G.2011/40 (1-2)](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) | 09.02.2012 | F3 | Dönem tarihleri okul ayarı; bağış girişinde uyarı |
| `gelir.proje_protokol_ucret_yasak` | Bakanlık proje/protokol faaliyetinden ücret yok | U | [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) | 09.02.2012 | F3 | Etkinlik gelirinde onay kutusu |
| `bagis.sartli_amac` | amacı dışında kullanılamaz | S | [16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F3 | Şartlı bağış alt hesabı; gider amaca bağlanmadan kaydedilmez, alt hesap eksiye düşmez (hesap bütünlüğü) |
| `bagis.ayni_teslim` | nakde çevrilemeyen → okul müdürlüğüne belge karşılığı; VİF | U | [16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [TMY 16/1](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) | 09.02.2012 | F3 | VİF no/tarih boşsa uyarı; VİF'i TKYS'de taşınır kayıt yetkilisi düzenler |
| `makbuz.cilt_yaprak` | 50 asıl + 50 koçan | U | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F1c (F3) | Cilt kaydında sıra aralığı 50'den farklıysa uyarı |
| `makbuz.seri_cilt_sira_tekil` | seri + cilt + sıra tekil | S | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | 09.02.2012 | F3 | Numara tekilliği; yaprak bir kez kullanılır ya da iptal edilir |
| `makbuz.muhur_ve_karar_kaydi` | kurum mührü + koçan seri no'ları karar defterine | U | [16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); 16/7 | 09.02.2012 | F3 | Mühür tarihi ya da karar no boşsa cilt kullanıma açılırken uyarı |
| `etkinlik.onay_zinciri` | SEK incelemesi → okul müdürü uygunluk görüşü → il/ilçe MEM onayı | U | [6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) | 01.12.2023 | F4 | Her aşamanın tarih/sayı alanı |
| `etkinlik.ders_saatleri_disinda` | gelir getirici etkinlik ders saatleri dışında | U | [15/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) | 09.02.2012 | F4 | — |

#### 6.4.6 Harcama, bildirim, duyuru, vergi, denetim

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `harcama.yk_karari` | her harcama YK kararıyla | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Dönem başı genel karar (okul ayarı) gerekçe sayılır |
| `harcama.okul_yazili_talep` | okul ihtiyacında okul yönetiminin yazılı talebi | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Talep yazısı müdür rolünün yazısı |
| `harcama.alim_komisyonu_en_az` | 3 kişi | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Küçük alımda eksik halka gerekçeyle (saha.md 6) |
| `harcama.alim_komisyonu_uyeleri` | YK üyeleri; uzmanlık işinde birlik üyeleri; 12/5 beyanı | U | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | 01.12.2023 | F4 | — |
| `harcama.musterek_imza` | başkan + muhasip (başkan yoksa başkan yardımcısı) | U | [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Ödeme kaydındaki imzacılar; ödeme talimatı iki imzalı |
| `harcama.tasinir_kaydi` | okul adına kayıt; VİF örneği harcama belgesine | U | [18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [TMY 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41) | 09.02.2012 | F4 | 18/3'teki mülga TMY atfı TMY 41/2 ile yeni TMY'ye; "taşınır işlem fişi" = VİF |
| `harcama.organ_uyesine_odeme` | YK/DK üyesine huzur hakkı vb. ödeme yok | U | [25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) | 09.02.2012 | F4 | Alıcı organ üyesiyse uyarı + gerekçe |
| `bildirim.aylik_mudur` | her ayın sonu, yazılı | U | [18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | 09.02.2012 | F4 | Ay bitti, bildirim yok → uyarı |
| `duyuru.butce` | ilan panosu + internet sayfası | U | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F4 | GK'de görüşülen bütçe; kanıt alanları |
| `duyuru.gelir_gider_donemlik` | her dönem en az 1, pano + internet | U | [13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | 09.02.2012 | F4 | Dönem sınırları ders yılı takviminden |
| `vergi.damga_harc_muafiyeti` | md. 6 işlemleri ve kâğıtları muaf | S | [24](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24) | 09.02.2012 | F4 | Program birlik kâğıdında damga vergisi hesaplamaz |
| `denetim.mem_yilda_en_az` | 1 | U | [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26) | 09.02.2012 | F4 | Pano hatırlatması; denetim kaydı `InspectionRecord` |

#### 6.4.7 Kantin: arz bedeli, pay dağılımı, aylık kira

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `arz_bedeli.kira_oran` | 0,03 (gayri safi) | S | [17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 09.02.2012 | F1c (F3) | Kiracı öder; `kosul`: kiraya veriliyor |
| `arz_bedeli.isletme_oran` | 0,01 (gayri safi hâsılat) | S | [17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F5) | Birlik öder; `kosul`: birlikçe işletiliyor |
| `arz_bedeli.donem_ay` | 3 ay | S | [17/1-a-1, b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); EK-2 md. 7 | 09.02.2012 | F3 | Dönem başlangıcı DOĞRULANMADI-2 (varsayılan takvim çeyreği, KE-2); EK-2'de peşin ödeme seçeneği |
| `arz_bedeli.sozlesme_vade_gunu` | izleyen ayın 10'u (dâhil) | U | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F1c (F3) | 11-20: "sözleşme vadesi geçti" (plan §1.8 kararı) |
| `arz_bedeli.yonetmelik_vade_gunu` | izleyen ayın 20'si (dâhil) | U | [17/1-a-1, b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F3) | 20'sinden sonra: "Yönetmelik süresi de geçti"; tatil kayması yok (KE-18) |
| `arz_bedeli.takip_sorumlulari` | okul müdürü + birlik başkanı | U | [17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F3 | İzleme çizelgesinde iki imza (E24) |
| `arz_bedeli.diger_tahsilat_oran` | 0,03 | S | [17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F5 | Tahliye cezası, fesih tazminatı, kısa süreli kullanım bedeli; kalan 17/1'e göre dağıtılır. Bent (b) altında ama konusu kira (KE-17) |
| `pay_dagitimi.genel` | birlik 0,80 · ilçe 0,10 · il 0,10 | S | [17/1-a-2, b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17); EK-2 md. 7 | 09.02.2012 | F1c (F3) | Taban: gayri safi − arz bedeli; `kosul`: büyükşehir ya da diğer |
| `pay_dagitimi.il_merkezi` | birlik 0,80 · ilçe 0 · il 0,20 | S | [17/1-a-2, b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F1c (F3) | `kosul`: büyükşehir olmayan il merkezi (OYS `is_metropolitan` düzeltmesi, S-17); taban yorumu KE-13 |
| `pay_dagitimi.isletme_net_tabani` | gayri safi − arz − zorunlu işletme giderleri − kanuni giderler | S | [17/1-b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) | 09.02.2012 | F5 | `kosul`: birlikçe işletiliyor |
| `kira.odeme_gunleri` | her ayın 5-15'i | U | [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4); EK-2 md. 7 | 01.12.2023 | F3 | Kira ve payların yatırılması aynı pencerede |
| `kira.yariyil_ayi_carpani` | 0,5 | S | [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4) | 01.12.2023 | F3 | Yarıyıl tatilinin yapıldığı ay (ders yılı takviminden) |
| `kira.ay_sayisi` | 9 ya da 12 | S | [19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19); EK-2 md. 4 | 09.02.2012 | F3 | Sözleşmede seçilir; 9'da Haziran-Temmuz-Ağustos kirası yok |
| `kira.mucbir_sebep_indirimi` | ara verilen günlerin kirası düşülür | U | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F5 | Hesap biçimi yazılı değil → indirim elle ve gerekçeyle |
| `kira.ust_uste_odememe_fesih` | 2 ay | U | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) | 01.12.2023 | F5 | Mücbir sebep dışında; fesih önerisi |
| `kantin.kdv_istisnasi` | kira tahsilatında KDV hesaplanmaz | S | [KDVK 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17) | 21.03.2018 | F3 | `kosul`: kiraya veriliyor |

#### 6.4.8 Kantin: kiralama, sözleşme, belgeler

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `kantin.kiralama_usulu` | pazarlık (2886 md. 51/g) | S | [20/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51) | 09.02.2012 | F5 | Başka yöntem seçeneği yok |
| `kantin.istekli_belge_sarti` | 20/4 belgelerinden biri | U | [20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 01.12.2023 | F5 | Eksik belge uyarı + gerekçe (plan §1.8); OYS'de sertti |
| `kantin.esnaf_odasi_belgesi` | kayıtlı kantin yok + yasaklama yok belgesi | U | [20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F5 | OYS'de yoktu |
| `kantin.hisimlik_derecesi` | 2. dereceye kadar kan ve kayın | S | [20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 09.02.2012 | F5 | Komisyon başkan ve üyeleri + YK + DK üyeleri; hukuken geçersiz katılım (plan §1.8) |
| `kantin.istekli_suc_engeli` | 12/5 suçları (yargı kararıyla tespit) | S | [20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) | 01.12.2023 | F5 | Atıf 20/11 (OYS 12/5 diyordu, S-8); beyan işareti, içerik tutulmaz |
| `kantin.calisan_niteligi` | ustalık, iş yeri açma, kalfalık, diploma ya da kurs belgesinden biri | U | [20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [EK-2 md. 19](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-19) | 09.02.2012 | F5 | Portör ve adli sicil **çalışandan** istenir, istekliden değil (S-8) |
| `kantin.yillik_yenileme` | 12 ay: işletme faaliyet belgesi + çalışan adli sicil ve arşiv kaydı | U | [20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | 09.02.2012 | F5 | Belge tarihi + 12 ay; içerik tutulmaz |
| `kantin.calisan_hijyen_belgesi` | belgesiz çalıştırılamaz; belge hizmet süresince geçerli | U | [HEY 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5); [HEY 6/3](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-6) | 05.07.2013 | F5 | Süre sayacı yok |
| `kantin.kisa_sureli_bedel_birimi` | saat · gün · hafta | U | [19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) | 09.02.2012 | F5 | Bedeli muhammen bedel komisyonu belirler (kayıt) |
| `kantin.isletmede_vergi_uyarisi` | VUK hükümleri uygulanır | U | [23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | 09.02.2012 | F1c | `kosul`: birlikçe işletiliyor; okul kartında (F1b) seçilince görünen uyarı F1c'de pakete bağlanır |
| `kira.sozlesme_en_fazla_yil` | 5 yıl | U | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) | 01.12.2023 | F5 | Takvimle hesap (5 × 365 değil, S-18); sert mi KE-6 |
| `kira.toplam_en_fazla_yil` | 20 yıl | U | [21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii) | 01.12.2023 | F5 | Geçici md. 4 istisnası (20 yılı geçenler bitime kadar) bilgi notu |
| `kira.yirmi_yil_taban_tarihi` | 31.05.2005 | S | [G.2024/35 III-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-1) | 03.01.2024 | F5 | Daha önceki ilk sözleşmeler bu tarihten sayılır |
| `kira.yirmi_yil_yeniden_baslangic` | ilanlı ya da çok istekli pazarlık yeni başlangıç; teklif-kabul yenilemesi değil | S | [G.2024/35 III-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-2); [III-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-3) | 03.01.2024 | F5 | Sözleşme zinciri (`OabContract`) türüyle |
| `kira.yirmi_yil_ilave` | dondurulan süre + 540 gün (16.03.2020-06.09.2021) | S | [G.2024/35 III-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii-4); [EK-2 md. 21](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-21) | 03.01.2024 | F5 | — |
| `kira.yer_teslimi_gun` | 15 gün (imzadan) | U | [21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | 01.12.2023 | F5 | Gecikmede kiracının 15 gün içinde 10 günlük noter ihtarı hakkı (bilgi); imzasız teslim yok |
| `kira.tufe_artisi` | 2. yıldan; TÜFE on iki aylık ortalamalara göre % değişim | S | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); EK-2 md. 6 | 01.12.2023 | F5 | `IndexRate.value` bu anlamda sabitlenir; ilk yıl ihale bedeli |
| `kira.ogrenci_degisim_esigi` | %25 azalış ya da artış | U | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | 01.12.2023 | F5 | Muhammen bedelin yeniden tespiti önerisi |
| `kira.kesin_teminat_oran` | 0,06 (yıllık kira) | S | [EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) | 01.12.2023 | F5 | — |
| `kira.tahliye_gunluk_ceza_oran` | 0,03 (aylık kira, her geçen gün) | S | [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) | 01.12.2023 | F5 | Tahsilatında arz `arz_bedeli.diger_tahsilat_oran` |
| `kira.fesih_ihtar_gun` | 15 gün | U | [22/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) | 09.02.2012 | F5 | Yazılı bildirimden |
| `kira.yeniden_kiralama_bildirim_ay` | bitişten en az 2 ay önce (işletmeci) | U | [G.2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2) | 03.01.2024 | F5 | — |
| `kira.yeniden_kiralama_cevap_gun` | 15 gün | U | [G.2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) | 03.01.2024 | F5 | Birliğin yazılı cevabı (E41) |
| `kira.muhammen_bedel_teklif_ay` | bitişten en az 1 ay önce | U | [G.2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5) | 03.01.2024 | F5 | Muhammen bedel komisyonunun tespiti |
| `kira.tufe_bildirimi` | yenilenen kira il/ilçe MEM'e bildirilir | U | [G.2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) | 03.01.2024 | F5 | E45 |
| `kira.milli_emlak_ornegi` | sözleşme örneği millî emlak birimine (okul müdürlüğü) | U | [21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | 01.12.2023 | F5 | Gönderim tarihi/sayısı alanı |
| `kira.ihaleden_yasaklama_yil` | 1 yıl | U | [22/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22); [2886 md. 84](../mevzuat/2886-devlet-ihale-kanunu.md#madde-84) | 09.02.2012 | F5 | Yasaklama kararını Bakanlık verir; kayıtlı yasaklı istekli → uyarı |

#### 6.4.9 Servis

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `servis.ilan_en_az_gun` | 7 gün (dosya teslim gününden önce) | U | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | 30.05.2018 | F6 | OYS yalnız kesinleştirmede bakıyordu |
| `servis.ilan_kanallari` | ilan tahtası + okul web sitesi; tutanak | U | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | 30.05.2018 | F6 | E49 |
| `servis.komisyon_bilesimi` | müdür (başkan) + birlik başkanı + 1 öğretmen (+1 yedek) + 2 veli (+2 yedek) + varsa vakıf temsilcisi | U | [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3); [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) | 25.10.2017 | F6 | Yedekler sayılır (OYS saymıyordu) |
| `servis.komisyon_karari` | çoğunluk; eşitlikte başkanın tarafı; çekimser yok; muhalif şerhi zorunlu | S | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) | 30.05.2018 | F6 | "Oy birliği ile" sabit basılmaz (S-7) |
| `servis.degerlendirme_yontemi` | komisyon değerlendirmesi (8/2); EK-3 puanlaması yalnız itiraz ya da yeni okulda ilk kez | U | [U-E 8/2-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | OYS varsayılanı ters çevrilir (S-7); "en düşük teklif" yok |
| `servis.ek3_puanlama` | 5 kriter, kademe tablosu | S | [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | 30.05.2018 | F6 | Kademe değerleri değiştirilemez; kriter 4'ün basılı adı KE-8 |
| `servis.ek3_kriter_azami_puan` | 5 (toplam 25) | U | [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | 30.05.2018 | F6 | Puan sınırı uyarı (plan §1.8); OYS'de sertti |
| `servis.olur_olmadan_kesinlesmez` | mülki amir onayı | S | [OSAY 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); [U-E 4/1, 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 25.10.2017 | F6 | Hukuken geçersiz işlem (plan §1.8) |
| `servis.mulki_amir_onay_is_gunu` | 5 iş günü | U | [U-E 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | Bekleme sayacı |
| `servis.teblig_is_gunu` | 5 iş günü (onaydan) | U | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | — |
| `servis.sozlesme_imza_gun` | 10 gün (tebliğden) | U | [U-E 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | İmzalanmazsa `servis.yeniden_cikma` |
| `servis.sozlesme_en_fazla_yil` | 3 eğitim öğretim yılı | U | [OSAY 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); [U-E 8/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 25.10.2017 | F6 | U-E "dönem" der; Yönetmelik "yıl" der ve üst normdur; esas süre bir yıl |
| `servis.yeniden_cikma` | başvuru yok · belge uygun değil · sözleşme imzalanmadı → aynı usulle yeniden | U | [U-E 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | 30.05.2018 | F6 | OYS "tek katılımcı" tutanağının yerine (S-8) |
| `servis.ucret_tarifesi` | ücret belediye tarifesine bağlı; birlik ve komisyon fiyat belirlemez | S | [OSAY 5/2-d](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-5); [U-E 10/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | 19.08.2025 | F6 | Servis kaydında muhammen bedel alanı yok. OSAY 5/2-d (yeniden düzenleme 19.08.2025) 5216/5393 tarifesine bağlar; U-E 10/2'deki 5362/62 atfı eski |
| `servis.taksit_en_fazla` | 9 | U | [U-E EK-2 md. 6/a](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) | 30.05.2018 | F6 | Taksit sayısı uyarı (plan §1.8); ücreti veli taşımacıya öder, birliğin alacağı değil (KE-14) |
| `servis.yariyil_ucret_yok` | yarıyılda ücret istenmez | U | [U-E EK-2 md. 6/c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) | 30.05.2018 | F6 | Sözleşme metni ve bilgi |
| `servis.muhtac_ogrenci` | araç başına 1 öğrenci ücretsiz | U | [U-E EK-2 md. 8/c](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-8) | 30.05.2018 | F6 | Komisyon yazılı bildirir; ad evrakta (iç) |
| `servis.tasimaci_ilani` | sözleşmeden sonra pano + web | U | [U-E 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | 30.05.2018 | F6 | E56 |
| `servis.arac_yasi_en_fazla` | 12 | U | [OSAY 4/1-f](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-4) | 29.11.2024 | F6 | Sözleşme içinde dolarsa o ders yılı sonuna kadar |
| `servis.sofor_yasi` | 26 yaşından gün almış, 66 yaşından gün almamış | U | [OSAY 9/1-a](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.10.2017 | F6 | 31.12.2026'ya kadarki geçici "69" uygulaması korpusta yok → yalnız bilgi notu (DOĞRULANMADI-11) |
| `servis.sofor_belge_yili` | D ≥ 2 yıl · D1 ≥ 5 yıl | U | [OSAY 9/1-c](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 29.11.2024 | F6 | U-E 9/1-c'deki 5/7 yıl eski; Yönetmelik esas; B sınıfı süresi sayımı 9/5 |
| `servis.sofor_psikoteknik_yil` | 5 yıl | U | [OSAY 9/1-ç](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.10.2017 | F6 | Belge tarihi + 5 yıl |
| `servis.saglik_raporu_ay` | 12 ay (şoför ve rehber personel) | U | [OSAY 9/1-c, 9/2-ç](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 29.11.2024 | F6 | Varlık + tarih; içerik tutulmaz |
| `servis.rehber_yasi` | 22 yaşını doldurmuş, 61 yaşından gün almamış | U | [OSAY 9/2-a](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | 25.08.2021 | F6 | — |

#### 6.4.10 Personel (sürüm 2; yalnız doğrudan işveren okullar)

| Kimlik | Değer | Tür | Madde | Yürürlük | Giriş | Not |
|---|---|---|---|---|---|---|
| `personel.sgk_saklama_yil` | 10 yıl (ilgili yılı izleyen yıl başından) | S | [5510 md. 86 (2. fıkra)](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86); [5510 md. 12](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-12) | 16.06.2006 | F1c (F8) | Silme kilidi. **Yorum:** birlik tüzel kişiliği olmayan işverendir, "kamu idareleri otuz yıl" hükmüne girmez |
| `personel.karsilik_ayrilir` | kıdem, ihbar vb. için karşılık | U | [6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6) | 01.12.2023 | F8 | Tutar hesabı DOĞRULANMADI-10 (1475 md. 14 korpusta yok) |
| `personel.yillik_izin_gun` | 1-5 yıl 14 · 5-15 yıl 20 · 15+ yıl 26 gün | S | [4857 md. 53](../mevzuat/4857-is-kanunu.md#madde-53) | 10.06.2003 | F8 | Hesap parametresi |
| `personel.izin_bolumu_en_az_gun` | 10 gün | U | [4857 md. 56](../mevzuat/4857-is-kanunu.md#madde-56) | 14.04.2016 | F8 | Anlaşmayla bölünürse bir bölüm |
| `personel.ihbar_hafta` | < 6 ay 2 · 6 ay-1,5 yıl 4 · 1,5-3 yıl 6 · 3+ yıl 8 hafta | S | [4857 md. 17](../mevzuat/4857-is-kanunu.md#madde-17) | 10.06.2003 | F8 | Karşılık hesabında |

#### 6.4.11 Özet ve dışarıda kalanlar

**Sayım.** `OAB-2023.12`'nin hedef içeriği 146 kuraldır; F1c'deki ilk revizyon (`r1`) bunların 50'sini taşır, kalanlar
§6.2-2'ye göre fazlarıyla girer.

| Alan | Kural | Sert | Uyarı | F1c'de giren |
|---|---|---|---|---|
| Genel kurul | 17 | 7 | 10 | 8 |
| Yönetim kurulu ve ortak üyelik | 17 | 5 | 12 | 15 |
| Denetleme Kurulu | 9 | 2 | 7 | 8 |
| Temsilciler | 9 | 0 | 9 | 9 |
| Gelir, bağış, makbuz, etkinlik | 10 | 2 | 8 | 2 |
| Harcama, bildirim, duyuru, vergi, denetim | 12 | 1 | 11 | 0 |
| Kantin: arz, pay, kira | 16 | 10 | 6 | 6 |
| Kantin: kiralama, sözleşme, belgeler | 27 | 9 | 18 | 1 |
| Servis | 24 | 4 | 20 | 0 |
| Personel | 5 | 3 | 2 | 1 |
| **Toplam** | **146** | **43** | **103** | **50** |

Sertlerin dağılımı (altın kural 3'ün üç gerekçesi): **hesap bütünlüğü ve yeter sayı 13** (GK yeter sayısının dört
kuralı, ikinci toplantı, GK karar ve gündem çoğunluğu, YK görev tekilliği, YK toplantı ve karar yeter sayısı, şartlı
bağış, makbuz tekilliği, servis komisyon kararı) · **hesap parametresi 23** (arz ve pay oranları, kira çarpanları,
teminat ve ceza, 20 yıl hesabı, TÜFE, KDV ve damga, kiralama usulü, EK-3 kademeleri, servis ücret tarifesi, izin ve
ihbar süreleri, SGK saklama kilidi) · **hukuken geçersiz işlem 6** (YK kişi türü, müdürün YK'ye girememesi, DK
koltukları, kantin hısımlık ve suç engeli, OLUR'suz kesinleştirme) · **kullanıcı kararı 1** (YK ve DK'de aynı kişi).

**DOĞRULANMADI — kural değil.** Aşağıdakiler korpusta dayanağı bulunamadığı ya da hüküm ayrıntıyı vermediği için
pakete girmez; program bunlar için mevzuat uyarısı göstermez, varsayılan davranış §15'teki karara bağlanır.

| # | Konu | Neden | Program ne yapar (varsayılan) |
|---|---|---|---|
| 1 | Olağanüstü GK'de çoğunluk aranmayan ikinci toplantı | [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) yeter sayıyı tekrarlar, 9/2'deki "otuz gün içinde çoğunluk aranmaksızın" cümlesini tekrarlamaz (S-3) | **Kapandı:** kullanıcı kararıyla md. 9/2 uygulanır, kural `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` olağanüstüyü de kapsar (§15 A-1) |
| 2 | Arz bedeli üçer aylık dönemlerinin başlangıcı | md. 17/1 ve EK-2 md. 7 başlangıcı söylemez | Takvim çeyreği; sözleşmede peşin seçeneği (KE-2) |
| 3 | Gecikme zammı oranı ve hesap yöntemi | 6183 md. 51 korpusta yok | Hesaplanmaz; oran ve tutar elle, "6183 md. 51'e göre" bilgi notu (KE-4) |
| 4 | Pay hesabında kuruş artığı | Yönetmelik sessiz | Hesap bütünlüğü kuralı: il ve ilçe payı yuvarlanır, birlik payı = net − il − ilçe (KE-3) |
| 5 | Aynı kişinin YK ve DK'de bulunması | Açık yasak bulunamadı (S-28) | **Kapandı:** kullanıcı kararıyla sert kural `denetleme_kurulu.yk_uyesi_olamaz` (§15 A-2) |
| 6 | Serviste hısımlık engeli | U-E ve OSAY'de hüküm bulunamadı | Kural yok; OYS'nin "uygulanmaz" testi korunur |
| 7 | Serviste birden çok taşımacı | U-E 10/3 çoğul der, usul yazmaz (S-16) | Model birden çoğa izin verir; kural yok |
| 8 | Kantin çalışanının portör/sağlık muayenesi periyodu | md. 20/6 "ilgili mevzuatında belirtilen sürelerde" der; [Okul Kantinlerine Dair Özel Hijyen Kuralları Yön. md. 14/1-h](../mevzuat/okul-kantinlerine-dair-ozel-hijyen-kurallari-yonetmeligi.md#madde-14) "periyodik olarak" der, süre vermez | Belge tarihi kaydı; süre uyarısı yok |
| 9 | Defter, koçan ve evrakın saklama süresi | md. 16/7, 23/6 Devlet Arşiv Hizmetleri Yön.'e gönderir; o Yönetmelik süreyi saklama planına bırakır ([md. 4/1-r](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-4), [md. 18](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-18)), MEB saklama planı korpusta yok | Silme ve imha yok (altın kural 4); yıl sonu arşiv paketi |
| 10 | Kıdem tazminatı karşılığının tutarı | 1475 md. 14 korpusta yok (4857 md. 120 yürürlükte bırakır) | Personel modülünde (sürüm 2) elle tutar |
| 11 | Şoför üst yaşında 31.12.2026'ya kadarki "69" uygulaması | İçişleri yazısı korpusa alınmadı (BENIOKU §6) | Kural 66 kalır; bilgi notu frontmatter'dan |
| 12 | "Yeter sayı sağlanamadı" tutanağının imzacıları | Mevzuat imzacı saymaz | KE-10 |
| 13 | Üyelerin %10'u başvurusunda çağrıyı kimin imzalayacağı | md. 9/6 yazmaz | KE-11 |
| 14 | Kantin denetim komisyonu (her ay; OAB yönetiminden bir veli) | Genelge 2020/8 A-1/a-b metni korpusta **var ama çapasız**; atıf kilidi geçmez | Çapa eklenince `temsilci.kantin_denetim_komisyonu` ve `kantin.denetim_aylik` girer; korpus eksiği olarak BENIOKU §6'ya işlenir |

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
  yokken başkanın yerine; [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)), `muhasip`, `sekreter`, `denetleme_kurulu`, `mudur`. Pilot okulda programın
  başında çoğunlukla müdür yardımcısı oturur (saha 10); `yonetici`nin başka rolün işini operatör olarak girip
  giremeyeceği §4 rol matrisindedir. Denetim izi her durumda girenin hesabını yazar. "Sistem" kullanıcı eylemi olmadan
  programın yaptığı geçiştir.
- **Kural:** madde ve kısa açıklama; **[S]** sert (program kaydetmez), **[U]** uyarı + gerekçe (sapma
  `ComplianceItem`'a yazılır, O3), **[B]** bilgi (gösterilir, gerekçe istemez). Değerler ve kural kimlikleri §6.4'tedir.
- **Evrak:** üretilen belgenin adı; kodu, şablonu ve biçimi evrak kataloğundadır (§9). Ad yoksa "—".

Durum adları §5'teki enum değerleridir. Hiçbir akışta geri alma silme değildir: `IPTAL` ya da ters kayıt (O1).

### 7.1 Genel kurul (olağan: birinci ve ikinci toplantı; olağanüstü)

Olağan genel kurul kapanacak birlik döneminin kaydıdır: çağrıyı o dönemin YK'si yapar, raporlar o döneme aittir;
toplantı yapılınca yeni dönem açılır (§7.8). Pilot okulda genel kurul çoğu yıl ikinci toplantıya kalır (saha 8); bu
yüzden ikinci toplantı yan yol değil, ana akışın parçasıdır.

**Durumlar:** `PLANLANDI → CAGRILDI → ILAN_EDILDI → YAPILDI → TUTANAK_TAMAM`; `ILAN_EDILDI → YETER_SAYI_YOK →
YAPILDI`; `PLANLANDI | CAGRILDI | ILAN_EDILDI | YETER_SAYI_YOK → IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `PLANLANDI` (oluşturma) | yonetici, sekreter | [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağan genel kurul en geç Ekim sonunda [U]; yeni açılan okulda açılıştan itibaren iki ay içinde [U] · Okul kartındaki öğrenci mevcudu ve tarihi güncel mi [B] · Veli listesi aktarılmadıysa öneri (§8.4) [B] | — |
| `PLANLANDI → CAGRILDI` (olağan) | sekreter (YK kararı); yeni okulda mudur | [md. 9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — çağrı YK'nindir: `KABUL_EDILDI` çağrı kararı bağı yoksa [U]; yeni okulda çağrı okul müdürünün yazısıdır | Genel kurul çağrı kararı taslağı (YK) · Yeni okulda genel kurul daveti (müdür) |
| `PLANLANDI → CAGRILDI` (olağanüstü) | çağırana göre: sekreter (YK kararı) · mudur · denetleme_kurulu · yonetici (üye başvurusunu kaydeder) | [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — çağıran ve çağrı nedeni zorunlu alandır (envanter S-2); listede olmayan çağıran [U]: YK kararı · okul müdürü · DK ([md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), usulsüzlük tespiti) · üyelerin %10'unun yazılı başvurusu (başvuran sayısı girilir; üye sayısı programca bilinmediği için oran [U]) · başkan ya da müdür ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), YK yedeklerle karar yeter sayısının altına düşünce; bir ay içinde [U]) · müdür ([md. 25/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25)) | Olağanüstü genel kurul çağrı yazısı (müdür ya da DK) · Olağanüstü genel kurul çağrı kararı taslağı (YK) |
| `CAGRILDI → ILAN_EDILDI` | yonetici, sekreter | [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — yer, zaman ve gündem birinci toplantıdan en az 15 gün önce elden yazılı, ilan panosu ve internet sayfası kanallarının üçünden [U] (gün ya da kanal eksikse) · [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — yeter sayı bu geçişte hesaplanır ve dondurulur: 16 × 4 (mevcut ≥ 100) ya da 16 × 2 (mevcut < 100); taban sabit, kayıt sayısından gelmez [S] · [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağanda ikinci toplantı tarihi birinciden en geç 30 gün sonra [U]; olağanüstüde ikinci toplantı alanı açılmaz (§15 A-1) · [md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — gündem sırası; tohumda [md. 11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) görevleri [B] · [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağanüstüde gündem çağrı nedenine bağlıdır [B] | Genel kurul toplantı davetiyesi · Genel kurul gündemi · Genel kurul ilanı (pano ve internet metni) · Davetiye dağıtım ve ilan tutanağı · Genel kurul katılım cetveli (veli listesiyle doldurulmuş ya da boş satırlı) · Olağanda ayrıca: YK faaliyet raporu, gelir-gider çizelgesi, tahmini bütçe, DK nihai raporu ([md. 11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14)) |
| `ILAN_EDILDI → YAPILDI` (birinci toplantı) | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — katılan üye sayısı dondurulmuş yeter sayıdan az değil [S]; gözlemci öğrenciler ([md. 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)) sayıya girmez [S] · [md. 10/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — açılışı okul müdürü yapar [B] · [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — divan başkanı ve kâtip veliler ya da 18 yaşını doldurmuş kursiyerler arasından açık oyla [U] | — |
| `ILAN_EDILDI → YETER_SAYI_YOK` | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — katılım yeter sayının altında; katılım sayısı yine dondurulur · İkinci toplantı ilk ilanda yoksa yeni ilan: [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) en az 15 gün önce ve [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) birinci toplantıdan en geç 30 gün sonra [U]; ikisi birlikte sağlanamıyorsa iki uyarı da görünür · Olağanüstüde: yeni çağrı önerilir (§15 A-1) | Yeter sayı bulunamadığına dair tutanak · İkinci toplantı ilanı (gerekirse) |
| `YETER_SAYI_YOK → YAPILDI` (ikinci toplantı; olağan ve olağanüstü — §15 A-1) | yonetici, sekreter | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — çoğunluk aranmaz, kararlar katılanların çoğunluğuyla [B] · [md. 10/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) divan [U] | — |
| `YAPILDI → TUTANAK_TAMAM` | sekreter, yonetici | [md. 9/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — gündem değişikliği oy çokluğuyla [U]; [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) — olağanüstüde çağrı gündemi dışında madde eklenmez [U] (§15 B-13; altın kural 3'ün sert listesinde yok) · [md. 11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — YK ve DK faaliyet raporları ayrı ayrı ibra: `EDILDI` · `EDILMEDI` · [md. 11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) tahmini bütçe görüşüldü · [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) yetkilendirme · [md. 10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [md. 11/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — seçim asıl ve yedek liste hâlinde açık oyla; seçilen yalnız aynı genel kurulun adayından [S]; koltuk uygunluğu (§5.2.2) [S]; YK 5+5, DK veli 1+1 eksikse [U]; seçilme sınırı ([md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) YK başkan ve üyeleri dört, [md. 14/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) DK başkanı üç) [U]; suç engeli ve tek birlik beyanları alındı mı ([md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12)) [U] · [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK öğretmen üyelerini öğretmenler kurulu seçer, genel kurul oylamasına girmez [S] · Katılım sayıları ve türe göre dağılım dondurulur (§5.4) [S] | Genel kurul toplantı tutanağı · YK ve DK aday listeleri (DK'da yalnız veli koltuğu) · Bütçe duyurusu ([md. 13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · Genel kurul sonuç bildirimi (dayanağı korpusta bulunamadı — saha belgesi, DOĞRULANMADI) |
| İbra `EDILMEDI` (yan akış) | sekreter, yonetici; yazıyı yeni YK ve mudur imzalar | [md. 11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) — diğer gündem maddeleri görüşülür; divan ibra edilmeyen muhasebe evrakını tutanağa bağlar ve yeni YK ile DK'ya teslim eder; yeni YK ve okul yönetimi il/ilçe MEM'e resmî yazıyla bildirir → `ComplianceItem(TAKVIM, IBRA_EDILMEDI_BILDIRIMI)` [U] | İbra edilmeyen hesaplara ilişkin divan tutanağı · İl/ilçe MEM'e ibra edilmediğine dair yazı |
| `TUTANAK_TAMAM` sonrası | sistem; yonetici onaylar | Olağanda: yeni `OabTerm` açılır (başlangıç = genel kurul günü), önceki dönem `KAPANISTA` olur (§7.8) · [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — YK ve DK görev bölümü bir hafta içinde (§7.2) [U] · [md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — tutanak ve belgeler yeni YK'ye teslim → devir-teslim (§7.8) · Olağanüstüde seçim yapıldıysa görevdeki eski YK üyelikleri `DUSTU` (`OLAGANUSTU_GK_SECIMI`); dönem değişmez ([md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) | (§7.2 ve §7.8'deki evrak) |
| `… → IPTAL` | yonetici | Gerekçe zorunlu [S]; ilan ve dondurulmuş yeter sayı iz olarak kalır | — |

**Notlar.**
- Yeter sayının tabanı dönemin üyelik kayıtlarından sayılmaz; organ bileşiminden gelen sabit 16'dır (YK 5+5, DK 3+3) ve
  olağanüstüde de aynı çarpan uygulanır (envanter S-1, S-2). Öğrenci mevcudu `ILAN_EDILDI` geçişinde anlık görüntü
  olarak alınır (O7).
- Sihirbaz davetiyede ikinci toplantı tarihini birlikte önerir. Yorum: iki tarihi birlikte duyuran ilan, en az 15 gün
  öncesinde yapıldıysa [md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) şartını iki toplantı için de karşılar; ayrı ilan gerekmez.
- Veli listesi varsa katılım cetveli adlarla ve sınıfla basılır; toplantıda ya da sonra yalnız sayılar girilir
  (isteğe bağlı satır işareti sayımı kolaylaştırır). Kişi düzeyindeki işaret listeyle silinir (§5.4).

### 7.2 Yönetim kurulu toplantısı ve karar

Pilot okulda YK her ay toplanır, kararları sekreter deftere yazar (saha 5). Karar defteri noter tasdikli ve el
yazısıdır ([md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); program karar **taslağı** üretir ve "deftere işlendi" işaretini, sıra no'yu, sayfayı
tutar. Organ değişiklikleri (devamsızlık, ayrılan veli, yedek çağırma) bu akışa bağlıdır.

**Durumlar:** toplantı `PLANLANDI → YAPILDI | YETER_SAYI_YOK | IPTAL`; karar `TASLAK → KABUL_EDILDI | REDDEDILDI`,
`KABUL_EDILDI → DEFTERE_ISLENDI`, `TASLAK → IPTAL`; üyelik `SECILDI → DUSTU`, yedek `SECILDI` + `promoted_on`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Toplantı `PLANLANDI` | sekreter | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — eğitim-öğretim yılı içinde ayda bir; ay toplantısız geçiyorsa pano [U]; yaz tatili ayları dışarıda [B] | YK toplantı çağrısı ve gündemi |
| `PLANLANDI → YAPILDI` | sekreter | Görevdeki her asıl üyenin katılım satırı (katıldı · özürlü · özürsüz) girilmeden geçiş yok [S] (devamsızlık sayımı, §15 A-9) · [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — en az dört üye katıldı [S] | YK toplantı katılım çizelgesi |
| `PLANLANDI → YETER_SAYI_YOK` | sekreter | [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — dörtten az katılım: karar girilemez [S]; katılım satırları yine zorunlu [S] | — |
| `PLANLANDI → IPTAL` | sekreter | Gerekçe [S] | — |
| Karar `TASLAK → KABUL_EDILDI / REDDEDILDI` | sekreter | Toplantı `YAPILDI` [S] · [md. 13/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — kabul oyu en az üç; kabul + ret katılanı aşamaz [S] | YK karar taslağı ("karar defterine el ile yazılarak imzalanır" konum cümlesiyle, [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13)) · YK toplantı ve karar tutanağı |
| `KABUL_EDILDI → DEFTERE_ISLENDI` | sekreter | [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — karar defteri noter tasdikli; `OfficialBook` tasdik kaydı yoksa [U] · (defter, sıra no) tekil [S]; sıra geri gider ya da atlarsa [U] · İşlenen kararın metni ve oyları değişmez [S]; sayfa fotoğrafı eklenebilir [B] | Karar defteri dizini (dönem sonunda) |
| Düzeltme | sekreter | Deftere işlenmiş karar değişmez; yeni kararla düzeltilir (`amends`) [S] | YK karar taslağı (düzeltme) |
| Görev bölümü | sekreter | [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — seçimden ya da yedek çağrısından sonra bir hafta içinde [U]; asıl üyeler arasından birer başkan, başkan yardımcısı, muhasip, sekreter — bir görev iki kişide olamaz [S]; okul müdürü görev alamaz [S] · [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK asıl üyeleri ilk hafta başkan seçer [U] · Görev bölümü rol hesaplarını açar, önceki görev sahibinin hesabını kapatır (§4) | YK görev bölümü ve imza yetkisi kararı taslağı ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) müşterek imza) · DK görev bölümü tutanağı · Temsilciler görevlendirme çizelgesi · Bankaya imza yetkisi bildirimi (biçimi DOĞRULANMADI) |
| Devamsızlıkla görevin sona ermesi | sistem önerir; sekreter onaylar | [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — son üç YK toplantısında üst üste özürsüz katılmama → görev sona erer; öneri toplantının `YAPILDI` geçişinde görünür, onayla `DUSTU` (tarih: üçüncü toplantı, `DEVAMSIZLIK`) · DK'de bu kural yoktur (OYS testi AYNEN) | — |
| Öğrencisi ayrılan veli | yonetici, sekreter | [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7), [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — elle `DUSTU` (`OGRENCI_AYRILDI`) · [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) 2. cümle — YK üye sayısı toplantı yeter sayısının altına düştüyse veli üyeliği olağanüstü genel kurula kadar sürer: düşürme ertelenir, `retained_until_assembly` işaretlenir [U] | — |
| Yedek çağırma | sekreter (YK kararıyla) | [md. 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — yedekler aldıkları oy sırasıyla asıl üyeliğe çağrılır; sıradakinin atlanması [U] (ör. yedeğin çekilmesi) · [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — yeni kurul bir hafta içinde görev dağılımı yapar [U] · [md. 14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — DK öğretmeni başka kurumda dört aydan uzun görevlendirilirse yedeği çağrılır [U] | Yedek üye çağrı yazısı · Yedek çağırma kararı taslağı |
| Karar yeter sayısının altı | sistem | [md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — görevdeki asıl ve çağrılabilir yedek sayısı üçün altına düşerse başkan ya da okul müdürü bir ay içinde olağanüstü genel kurula çağırır [U] → §7.1 olağanüstü akışı önerilir | Olağanüstü genel kurul çağrı yazısı |

**Notlar.** Harcama, koçan kaydı, genel kurul çağrısı, bütçe ve görev bölümü kararları ilgili kayda yabancı anahtarla
bağlanır (§5.2.10). Bağlı akış karar `KABUL_EDILDI` olmadan ilerlemez; `DEFTERE_ISLENDI` olmaması yalnız kapanışta
uyarıdır (§7.8). Toplantıların "yeter sayı yok" kaydı da devamsızlık sayımına girer (§15'e öneri B-2).

### 7.3 Gelir-gider ve banka eşleme

Muhasip ayda bir, banka dekontuna ve makbuza bakarak defter tutar; müdür yardımcısı ayda bir TEFBİS'e girer (saha 1a,
2). Program banka hareketinden başlar (K1): hareket içe aktarılır, kayıt hareketten doğar ya da hareketle eşlenir.
Deftere geçirme ve TEFBİS'e girme iki ayrı, sırası serbest işarettir.

**Durumlar:** `BankStatement`: `ONIZLEME → UYGULANDI → GERI_ALINDI`. `BankTransaction` (hesaplanır): `ESLESMEDI →
KISMI → TAM`. `LedgerEntry`: `TASLAK → KESIN`; `TASLAK | KESIN → IPTAL`; işaretler: deftere geçirildi, TEFBİS'e girildi;
düzeltme ters kayıtla.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Banka dosyası `ONIZLEME` | muhasip, yonetici | Dosyadaki hesap no ya da IBAN `BankAccount` ile aynı [S] · Kapanmış döneme düşen satır alınmaz [S] · Aynı parmak izli satır elenir [S]; aynı dosya ikinci kez [U] · Bakiye zinciri kopuk [U] · İlk bakiye ↔ `OpeningBalance` farkı [U] (§8.2) | — (ekranda içe aktarım özeti) |
| `ONIZLEME → UYGULANDI` | muhasip, yonetici | Parti tek işlemde uygulanır; hareketler bundan sonra değişmez (K1) [S] | — |
| `UYGULANDI → GERI_ALINDI` | yonetici | Yalnız hiçbir hareketi eşlenmemişse [S]; satırlar `void` olur, silinmez | — |
| Hareketten gelir kaydı | muhasip | Program öneri verir (kiracının birlik payı, kasa yatırması, tekrarlayan açıklama), onay kullanıcıdadır [B] · TEFBİS işlem tipi, kaynak tipi, evrak no ve tarihi eksik [U] ("TEFBİS'e girilemez") · [md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [Genelge 2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) — kayıt-kabul ve diploma döneminde bağış [U] · [md. 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15) — Bakanlık proje ve protokol faaliyetinden ücret [U] · [md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — şartlı bağış işaretlenirse amaç zorunlu, `SARTLI_BAGIS` alt hesabı açılır [S] | — |
| Hareketten gider kaydı | muhasip | Gider harcama dosyasına bağlanır (§7.4); `requires_expense_file` kapalı kategoriler dışında dosyasız gider [U] · [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — karar bağı yok [U] · [md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) — huzur hakkı ve benzeri kategori yoktur [S] | — |
| Eşleme | muhasip | Hareket ile kayıt çoka çok; etkin eşleşmeler toplamı hareket ve kayıt tutarını aşamaz, yönler tutarlı [S]; eşleşme silinmez, `COZULDU` olur [S] | — |
| Elden bağış | muhasip | [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — banka hesabına yatırılması mümkün değilse makbuzla kabul: yaprak `KULLANILDI` (§7.5) + `KASA` gelir kaydı; tutarlar eşit [S] · [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — en geç beş iş günü içinde bankaya; iş günü takvimi `Holiday`'den, kasa sayacı panoda [U] · Yatırma `KASA → BANKA` virmanıdır; banka ayağı hareketle eşlenir [S] · [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — gelirler bankada toplanır: kasadan doğrudan gider [U] | — (makbuz ciltli koçandan elle kesilir, K5) |
| Ayni bağış | muhasip, yonetici | [md. 16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — nakde çevrilebilen çevrilip bağış hesabına yatırılır; çevrilemeyen belge karşılığı okul müdürlüğüne teslim edilir · `in_kind` kayıt bakiyeye girmez [S] · [TMY md. 16](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) — varlık işlem fişi no ve tarihi boş [U] | Ayni bağış teslim tutanağı (okul müdürlüğüne) |
| `TASLAK → KESIN` | muhasip | Zorunlu alanlar [S] · `KASA`, `SARTLI_BAGIS`, `EMANET` eksiye düşmez [S] · [md. 16/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — şartlı alt hesaptan giderde amaca uygunluk beyanı boş geçilemez [S] | — |
| Deftere geçirildi | muhasip (aylık) | [md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — il/ilçe MEM tasdikli gelir-gider defteri ve sayfası girilir; yalnız `KESIN` kayıt [S] | Deftere geçirilecek kayıtlar (aylık; asgari sütunlar §15 A-12: sıra no, tarih, belge türü-no-tarih, açıklama, gelir/gider türü, karar no, gelir, gider, kalan) |
| TEFBİS'e girildi | yonetici (aylık) | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — kaydı okul idaresi girer; yalnız `KESIN` [S]; TEFBİS alanı eksik kayıt listede uyarılı [U] | TEFBİS'e girilecekler listesi (§8.3) |
| Düzeltme | muhasip | Deftere geçmemiş ve TEFBİS'e girilmemiş kayıt `IPTAL` (gerekçe; eşleşmeleri çözülür) · Geçmiş ya da girilmiş kayıt ters kayıtla (`reversal_of`) [S]; TEFBİS'e girilmişse "TEFBİS'te düzeltilecek" listesine [U] · Kapanmış dönemin kaydı açık dönemde "önceki dönem düzeltmesi" olarak [S] | Deftere geçirilecek kayıtlarda düzeltme satırı |
| Ay sonu | muhasip; baskan | Banka bakiyesi = `BANKA` + bağlı alt hesapların eşlenmiş bakiyesi; fark mutabakat listesinde [U] · [md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — başkan her ay sonunda gelirleri, bağışları ve kararla yapılan harcamaları müdüre yazılı bildirir [U] | Banka mutabakat çizelgesi (aylık) · Müdüre aylık bildirim |
| Ders dönemi sonu | yonetici | [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) — gelir-gider kayıtları her ders döneminde en az bir kez pano ve internet sayfasında [U]; duyuruda kişi adı yok (altın kural 5) | Dönemlik gelir-gider duyurusu (A4 + web HTML) |

**Kantin kirası** bu akışa §7.6'dan girer: kiracının birlik payını yatırdığı hareket, takvimdeki aylık satırla
(`ContractInstallment`) eşleşen bir gelir kaydı doğurur. **Faiz ve banka masrafı** açıklama kalıbından önerilir
(TEFBİS "Faiz Gelirleri" ve ilgili gider tipi).

### 7.4 Harcama zinciri

[md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) her harcamada YK kararını, okul ihtiyacında okul yönetiminin yazılı talebini ve mal-hizmet alımında en az üç
kişilik komisyonu öngörür; para başkan ve muhasibin müşterek imzasıyla çekilir ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)). Pilot okulda büyük alımda
zincir tam işler, küçük alımda YK kararı yeterli sayılır (saha 6): eksik halka uyarı + gerekçe olarak kaydedilir;
dönem başı genel kararla (okul ayarı `standing_decision`, `small_purchase_limit`) gerekçe kendiliğinden o karara
bağlanır (§15 A-11).

**Durumlar:** `TALEP → KARAR → ALIM → BELGE → ODEME_TALIMATI → ODENDI → KAPANDI`; `ODENDI` öncesinden `IPTAL`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `TALEP` (açılış) | mudur (talep yazısını yazar) ya da yonetici (gelen talebi `DocumentRecord`'a kaydeder) | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — okul ihtiyacında okul yönetiminin yazılı talebi; talepsiz (`YK_RESEN`) dosya [U]; genel karar kapsamındaki sürekli ödeme ya da küçük alımda gerekçe genel karara bağlanır | Harcama talep yazısı (okul müdürlüğünden birliğe) · Harcama dosyası kapak ve kontrol listesi |
| `TALEP → KARAR` | sekreter | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — YK harcama kararı `KABUL_EDILDI` [U] (yoksa gerekçe) · Tahmini bütçedeki kalemi aşıyor [B] · Şartlı bağıştan harcanacaksa amaç uygunluğu (§7.3) | Harcama kararı taslağı |
| `KARAR → ALIM` | yonetici, sekreter | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — mal ve hizmet alımında YK üyelerinden, uzmanlık işinde birlik üyelerinden en az üç kişilik komisyon [U] · [md. 12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) — komisyon üyelerinin suç engeli beyanı [U] | Alım komisyonu tutanağı |
| `ALIM → BELGE` | muhasip | Fatura ya da gider pusulası, satıcı, tutar · Fatura tutarı karar tutarını aşıyor [U] (ya da ek karar) · [md. 18/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [TMY md. 41/2](../mevzuat/tasinir-mal-yonetmeligi.md#madde-41) — alınan taşınır okul adına kaydedilir, varlık işlem fişinin bir örneği harcama belgesine eklenir: fiş no boş [U] · Tevkifat yalnız bilgi metni (özelge; `bilgi/`) [B] | — (harcama belgesi dışarıdan gelir) |
| `BELGE → ODEME_TALIMATI` | baskan (yoksa baskan_yardimcisi) ve muhasip | [md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) — talimat iki imzalı: başkan ya da yokluğunda başkan yardımcısı + muhasip; imzacı eksik [U] · [md. 25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25) — alıcı YK ya da DK üyesi [U] · Şartlı alt hesap bakiyesi yetmiyor [S] · Üçüncü onay ayarı açıksa müdür satırı [B] | Ödeme talimatı (bankaya) |
| `ODEME_TALIMATI → ODENDI` | muhasip | Ödeme hareketi içe aktarılıp dosyanın gider kaydıyla eşlenmeden geçiş yok [S] (§7.3) | — |
| `ODENDI → KAPANDI` | yonetici | Gider kaydı TEFBİS'e girildi; karar deftere işlendi; kontrol listesi tam — eksik [U] | Harcama dosyası kontrol listesi (son hâli) |
| `… → IPTAL` | yonetici | `ODENDI` öncesi; gerekçe [S]; bağlı karar ve belgeler iz olarak kalır | — |

**Dosyasız giderler.** Banka masrafı, vergi ödemesi, MEM payı ve arz bedeli aktarımı gibi kategorilerde
(`requires_expense_file` kapalı) gider kaydı harcama dosyası açmadan doğar; karar bağı yine uyarıyla istenir.

### 7.5 Makbuz koçanı

Koçanlar matbaada bastırılır, mühürlenir ve karar defterine kaydedilir (saha 4). Program koçan basmaz (K5); koçanın
envanterini ve her yaprağın kaderini tutar. Koçan dönemden bağımsızdır, devredilir.

**Durumlar:** koçan `ENVANTERDE → KAYITLI → KULLANIMDA → BITTI → ARSIVDE`, her aşamadan `IPTAL`; yaprak `BOS →
KULLANILDI | IPTAL | KAYIP`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Koçan `ENVANTERDE` | muhasip | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — müteselsil seri, cilt ve sıra numarası; tür, seri, cilt tekil ve aralıklar çakışmaz [S] · 50 asıl + 50 koçan yaprağı değilse [U] · Yapraklar topluca `BOS` açılır | — |
| `ENVANTERDE → KAYITLI` | sekreter (YK kararı), muhasip (mühür tarihi) | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [md. 16/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) — kurum mührüyle mühürlenir; koçan seri numaraları karar defterine yazılır; belgelerin sayısı ve türü YK'ce tespit edilir: mühür tarihi ya da karar bağı eksik [U] | Koçan kayıt kararı taslağı (seri ve sıra numaralarıyla) |
| `KAYITLI → KULLANIMDA` | sistem (ilk yaprak kullanılınca) | Kayıtsız koçandan yaprak kullanımı [U] (ENVANTERDE'den doğrudan) | — |
| Yaprak `BOS → KULLANILDI` | muhasip | Bir yaprak bir gelir kaydına; tutar eşit [S] · Önceki `BOS` yaprağı atlama [U] · [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1) — bağış alındı belgesinin bağışçı alanları kâğıttadır; programda T.C. kimlik no yok (K9) [B] | — |
| Yaprak `BOS → IPTAL` / `KAYIP` | muhasip | Gerekçe zorunlu; geri alınamaz [S]. İptal edilen yaprağın aslı koçanda kalır [B] | İptal ve kayıp yaprak tutanağı |
| `KULLANIMDA → BITTI` | sistem | Son yaprak `KULLANILDI`/`IPTAL`/`KAYIP` | — |
| `BITTI → ARSIVDE` | yonetici | [md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — biten koçanlar arşiv mevzuatındaki süreler kadar okulda saklanır; devirde liste kalemi (§7.8) | Biten koçanlar teslim listesi |
| `… → IPTAL` | yonetici | Basım hatası, kayıp cilt; gerekçe [S]; kullanılmış yaprağı olan koçan iptal edilemez [S] | Koçan iptal tutanağı |

Denetim dosyası için [TKB E.4 §4](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4) Tablo 4'ün makbuz satırları (ciltli, müteselsil, mühürlü, karar defterine kayıtlı)
koçan kayıtlarından evet/hayır olarak doldurulur.

### 7.6 Kantin kiralaması ve kira-pay

Kiralamayı il/ilçe MEM yürütür: muhammen bedeli valilik veya kaymakamlığın görevlendirdiği komisyon belirler
([md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19)), ihaleyi MEM yöneticisi başkanlığındaki komisyon pazarlıkla yapar ([md. 20/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [2886 md. 51/g](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51)); birlik
başkanı iki komisyonda da üyedir. Birliğin işi sözleşmenin tarafı olmak, tahsilat, pay takibi ve belge takibidir.
Program birliğin ve okulun evrakını üretir, MEM'in evrakını yalnız gelen evrak olarak kaydeder.

**Durumlar.** Süreç (`Tender`, `KANTIN_KIRALAMA`) — yeniden kiralama yolu: `TALEP_ALINDI → TALEP_CEVAPLANDI →
MUHAMMEN_BEDEL → TEKLIF_EDILDI → KABUL | RET`; ihale yolu: `BILDIRILDI → MUHAMMEN_BEDEL → ILAN → IHALE → KARAR → ONAYDA →
KESINLESTI`; her aşamadan `IPTAL`. Sözleşme: `TASLAK → IMZALANDI → YURURLUKTE → SONA_ERDI | FESHEDILDI`. Aylık satır:
`BEKLIYOR → BIRLIK_PAYI_ALINDI → DEKONTLAR_TAMAM`; `IPTAL`. Çeyreklik arz: `late_status` hesaplanır.

**Kiralama ve sözleşme**

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `TALEP_ALINDI` (yeniden kiralama) | yonetici | [Genelge 2024/35 I-2](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-2) — mevcut işletmeci bitişten en az iki ay önce yazılı bildirir [U] · [md. 21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — toplam süre ilk sözleşmeden 20 yılı geçemez; hesap [Genelge 2024/35 III](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-iii) (31.05.2005 tabanı, rekabetçi ihale yeni başlangıç, dondurulan süre ve 540 gün) [U] | — (gelen evrak) |
| `TALEP_ALINDI → TALEP_CEVAPLANDI` | sekreter (YK kararı), baskan | [Genelge 2024/35 I-3](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) — birlik on beş gün içinde yazılı cevaplar [U] · [Genelge 2024/35 I-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-4) — yükümlülük değerlendirmesi somut belgeye dayanır, belge yoksa talebin kabulü esastır: belgesiz ret [U] | Yeniden kiralama talebine cevap yazısı · YK kararı taslağı |
| `→ MUHAMMEN_BEDEL` | yonetici, baskan | [md. 19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) — komisyon tespiti gelen evrak olarak kaydedilir; birlik başkanı üyedir [B] · [Genelge 2024/35 I-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-5) — tespit edilen bedel bitişten en az bir ay önce teklif edilir [U] | — |
| `TEKLIF_EDILDI → KABUL` | yonetici | [Genelge 2024/35 I-6](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-6) — kabulde muhammen bedel üzerinden yeni sözleşme; süre beş yılı, toplam 20 yılı aşamaz [U] | (sözleşme aşağıda) |
| `TEKLIF_EDILDI → RET` → ihale yolu | yonetici | [Genelge 2024/35 I-7](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-7) — muhammen bedel üzerinden pazarlık; ilanı MEM yapar | — |
| `BILDIRILDI` (ihale yolu) | mudur, yonetici | [Genelge 2024/35 II-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-1) — kiralanacağı okul müdürlüğü vasıtasıyla il/ilçe MEM'e bildirilir | Kantin kiralanacağına dair bildirim yazısı |
| `IHALE → KARAR` | yonetici (kayıt), baskan (komisyon üyesi) | [md. 20/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 20/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — istekli belgeleri eksik [U] · [md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — suç engeli `ENGEL_VAR` olan seçilemez [S] · [md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — komisyon, YK ve DK üyelerinin ikinci dereceye kadar kan ve kayın hısımları katılamaz [S] · [md. 20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — komisyon bileşimi [U] · [md. 22/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — ihalelerden yasaklı kayıtlı istekli [U] | — (komisyon evrakı MEM'indir) |
| `KARAR → ONAYDA → KESINLESTI` | yonetici | Onay `OLUR` kaydı olmadan `KESINLESTI` olmaz [S] (plan §1.8); kantinde onay makamı korpusta bulunamadı — DOĞRULANMADI, makam elle girilir | — |
| Sözleşme `TASLAK → IMZALANDI` | baskan (imza), yonetici | [md. 21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) örneğine uygun: 25 genel şart + özel şartlar; yürütmesi durdurulan ibare basılmaz · [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2 md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) — süre en çok beş yıl [U]; ilk yıl ihale bedeli · [EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) — kesin teminat yıllık kiranın %6'sı [S — hesap]; nakit alınırsa `EMANET` [B] · [KDVK md. 17/4-d](../mevzuat/3065-katma-deger-vergisi-kanunu.md#madde-17) — kirada KDV hesaplanmaz [S] · [md. 24](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24) — birlik kâğıtları damga vergisi ve harçtan muaf [B] · Öğrenci mevcudu ve pay oranları anlık görüntü (O7) | Kantin kira sözleşmesi ([EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2)) |
| `IMZALANDI → YURURLUKTE` | yonetici, mudur | [md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — imzadan önce yer teslimi yok [S]; imzadan itibaren 15 gün içinde [U] · [EK-2 md. 12](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-12) — teslim tutanağı · [md. 21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — sözleşme örneği okul müdürlüğünce millî emlak birimine [U] · Kira takvimi üretilir: 9 ya da 12 ay ([md. 19/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)), yarıyıl ayında yarım kira ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)) | Yer teslim tutanağı · Millî emlak birimine sözleşme örneği üst yazısı · Aylık kira ve pay izleme çizelgesi |
| Yıllık artış | yonetici | [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2 md. 6](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6) — ikinci yıldan TÜFE on iki aylık ortalamalara göre yüzde değişim (`IndexRate`) [S — hesap] · [Genelge 2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) — yenilenen kira il/ilçe MEM'e bildirilir [U] · [md. 21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) — öğrenci mevcudunda en az %25 değişim: muhammen bedelin yeniden tespiti önerisi [U] | TÜFE artışı bildirim yazısı |
| Belge yenileme | yonetici | [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — her yıl işletme faaliyet belgesi ve çalışanların adli sicil ve arşiv kaydı yenilenir; `valid_until` geçti [U] · [md. 20/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20) — portör ve adli sicil çalışandan istenir [B] | Kantin belge takip listesi |
| Fesih ve tahliye | baskan, yonetici | [md. 22/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — fesih halleri; (e) bendinde yazılı bildirime rağmen 15 gün içinde yükümlülük yerine getirilmezse [U — süre] · [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — mücbir sebep dışında iki ay üst üste ödememe: fesih önerisi [U] · [md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22), [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) — kesin teminat gelir kaydedilir (`EMANET` → gelir), cari dönem kirası tazminat; tahliye edilmezse günlük ceza · [md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — ceza, tazminat ve kısa süreli kullanım bedellerinde de %3 arz, kalan dağıtılır (`ShareStatement`, `CEZA_TAZMINAT`) [S — hesap] · [md. 22/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) — yeniden ihale | Yükümlülüklerin yerine getirilmesi için yazılı bildirim · Fesih bildirimi · Kiralanan yerin teslim tutanağı ([EK-2 md. 13](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-13)) |

**Tahsilat, arz ve pay**

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Aylık satır `BEKLIYOR → BIRLIK_PAYI_ALINDI` | muhasip | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — kiracı arz düşüldükten sonra kalanın %80'ini birliğin, %10'unu il, %10'unu ilçe MEM'in hesabına ayın 5-15'i arasında yatırır ([EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4)); vade geçti [U] · [md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — büyükşehir olmayan il merkezinde il %20, ilçe payı yok (yerleşim türü anlık görüntüsü) · Pay tutarları kuruş korunumlu [S] · Birlik payının banka hareketi gelir kaydıyla eşlenir (TEFBİS "Kira Gelirleri › Kantin kira geliri") | — |
| `BIRLIK_PAYI_ALINDI → DEKONTLAR_TAMAM` | yonetici | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — il ve ilçe paylarının dekontları birliğe ya da okul müdürlüğüne teslim edilir; eksik [U] | Aylık kira ve pay izleme çizelgesi |
| Mücbir sebep indirimi | yonetici | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — eğitime ara verilen günlerin kirası düşülür; hesap biçimi yazılı değil: indirim elle ve gerekçeyle [U] | — |
| Çeyreklik arz (kiraya vermede) | yonetici, baskan | [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) — kiracı gayri safi kiranın %3'ünü peşin ya da üçer aylık dönemlerle defterdarlık hesabına öder, dekont aslını teslim eder · Vade: [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) izleyen ayın 10'u — 11-20 arası "sözleşme vadesi geçti" [U]; [md. 17/1-a-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) izleyen ayın 20'si — sonrası "Yönetmelik süresi de geçti" [U] (plan §1.8) · [md. 17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — takipten okul müdürü ve birlik başkanı sorumludur [B] · [md. 17/1-b-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — gecikme zammı 6183 md. 51'e göre; metin korpusta yok, program hesaplamaz [B] | Arz bedeli takip çizelgesi |
| Birlikçe işletmede (`canteen_mode`) | muhasip, yonetici | [md. 17/1-b-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — birlik gayri safi hasılatın %1'ini üçer aylık dönemlerle izleyen ayın 20'sine kadar öder (gider) · [md. 17/1-b-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — arz, zorunlu işletme ve kanuni giderler düşüldükten sonra net 80/10/10 aktarılır (gider: kurumlara aktarım) [S — hesap] · [md. 23/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) — VUK hükümleri; vergi bilgi metni [U] | Arz bedeli ve pay aktarım çizelgesi |
| Kısa süreli kullandırma | yonetici, muhasip | [md. 19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19) — saatlik, günlük, haftalık bedel muhammen bedel komisyonunca belirlenir (kayıt) · [md. 17/1-b-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) — bedelin %3'ü arz, kalan dağıtılır (`KISA_SURELI_KULLANIM`) [S — hesap] | — |

### 7.7 Servis: taşımacının tespiti

Taşımacıyı okul müdürünün başkanlığındaki taşımacıyı tespit komisyonu belirler; birlik başkanı üyedir ([Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3),
[Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3); [md. 6/1-h](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)). Komisyon kararları mülki amirin onayıyla yürürlüğe girer ([Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8)). Seçim fiyatla
değil, [Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'deki ölçütlerle yapılır; EK-3 puanlaması yalnız itirazda ya da yeni açılan okulda ilk kez zorunludur
([Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)). Söz dağarcığı: "taşımacının tespiti", "başvuru", "değerlendirme"; "ihale", "teklif", "eksiltme" kullanıcı
metnine ve evraka girmez (altın kural 6); EK-3 kriter metninde mevzuat lafzının alıntısı §15 A-4'e bağlıdır. Ücreti
veli taşımacıya öder ([Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6)); birliğin defterine girmez, taksit takibi yoktur (§15 A-5).

**Durumlar** (`Tender`, `SERVIS_TESPIT`): `HAZIRLIK → ILAN → BASVURU → INCELEME → DEGERLENDIRME → KOMISYON_KARARI →
ONAYDA → KESINLESTI → TEBLIG_EDILDI → SOZLESME → YAYIMLANDI`; `YENIDEN` ([Servis U-E md. 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)); `IPTAL`. Sözleşme: `TASLAK →
IMZALANDI → YURURLUKTE → SONA_ERDI | FESHEDILDI`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| `HAZIRLIK` | mudur (komisyonu oluşturur), yonetici | [Servis U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3), [Servis Araçları Yön. md. 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3) — her yıl: müdür başkan, birlik başkanı, öğretmenler kurulunda ad çekmeyle bir asıl bir yedek öğretmen, servisle taşınan veliler arasından iki asıl iki yedek veli, varsa okul eğitim vakfı temsilcisi; bileşim eksik [U] · [Servis U-E md. 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — şartname EK-1'e göre komisyonca hazırlanır · [Servis U-E md. 5/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — işlem dosyası | Taşımacıyı tespit komisyonu görevlendirme yazısı · Servis işlem dosyası kapağı · Tip şartname ([Servis U-E EK-1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1)) |
| `HAZIRLIK → ILAN` | yonetici | [Servis U-E md. 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — dosya teslim tarihinden en az 7 gün önce ilan tahtası ve okul web sitesi; tutanakla [U] · [Servis U-E md. 5/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — ilanın zorunlu hususları [U] | Servis çalıştırma işi ilanı · İlan asma tutanağı |
| `ILAN → BASVURU` | yonetici | [Servis U-E md. 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) — evrak ilandaki saate kadar tutanakla teslim; verilen dosya geri alınamaz [S — kayıt kilidi] · [Servis U-E md. 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) — şartname isteyene bedelsiz verilir | Tip şartname teslim tutanağı · Başvuru evrakı teslim tutanağı · İlan indirme tutanağı |
| `BASVURU → INCELEME` | yonetici (komisyon adına) | [Servis U-E md. 8/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — eksik belgeli istekli değerlendirmeye alınmaz; istekliler önünde tutanakla · Belge eksikliği işareti [U] (plan §1.8) | Evrak kontrol ve tespit tutanağı |
| `INCELEME → DEGERLENDIRME` | yonetici, mudur | [Servis U-E md. 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — araç yaşı, özmal durumu, il/ilçede ikamet ya da şube, aynı okulda önceki hizmet ve başlama tarihi ölçütleri (varsayılan yöntem) · [Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — EK-3 puanlaması yalnız itiraz ya da yeni okulda ilk kez; başka hâlde EK-3 seçimi [U] · [Servis EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) — puanlar kademe listesinden; kademe dışı puan [U] (plan §1.8) | Değerlendirme tutanağı · EK-3 puanlama cetveli (yalnız [Servis U-E md. 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) hâlinde) |
| `DEGERLENDIRME → KOMISYON_KARARI` | mudur (başkan), baskan (üye), yonetici (kayıt) | [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) — çoğunluk; eşitlikte başkanın tarafı; çekimser yok (seçenek yok) [S]; muhalif üye karşı oy gerekçesini yazar: muhalif oyda şerh boş [U] · Birden çok taşımacı seçilebilir ([Servis U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) çoğul; [Servis Araçları Yön. md. 8/3](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8); §15 A-6) · [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) — komisyon gerekçesiyle işi yapmamakta serbesttir → `IPTAL` | Taşımacıyı tespit komisyonu kararı |
| `KOMISYON_KARARI → ONAYDA → KESINLESTI` | yonetici, mudur | [Servis U-E md. 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [Servis Araçları Yön. md. 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) — mülki amir onayı (`OLUR`) olmadan kesinleşmez [S] (plan §1.8) · [Servis U-E md. 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — onay ya da iptal beş iş günü içinde [U]; `RED` → `IPTAL` ya da `YENIDEN` | Komisyon kararının onaya sunulması yazısı |
| `KESINLESTI → TEBLIG_EDILDI` | yonetici, mudur | [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — onaydan itibaren en geç beş iş günü içinde Tebligat Kanunu hükümlerince bildirilir [U] | Komisyon kararının tebliği yazısı |
| `TEBLIG_EDILDI → SOZLESME` | mudur (komisyon başkanı imzalar), yonetici | [Servis U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — tebliğden 10 gün içinde imza [U]; imzalanmazsa `YENIDEN` · [Servis U-E md. 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9) — sözleşmede istenen belgeler (şoför ve rehber sabıka kaydı, sağlık raporu, psikoteknik, sertifika, sürücü belgesi, sigorta, ruhsat ve muayene): "görüldü" ve geçerlilik tarihi; tarama alınmaz (§5.4) [U — eksik belge] · [Servis Araçları Yön. md. 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) — bir eğitim öğretim yılı esas, en çok üç; [Servis U-E md. 8/4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'teki "dönem" ifadesi karşısında Yönetmelik esas [U] · [Servis EK-2 md. 6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-6) — ücret en çok dokuz taksit (bilgi alanı) [U] · [Servis U-E md. 10/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) — sözleşmeyi komisyon başkanı ve istekli imzalar, noter şart değil [B] | Servis sözleşmesi ([Servis EK-2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2)) |
| `SOZLESME → YAYIMLANDI` | yonetici | [Servis U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) — sözleşme imzalanan taşımacıların bilgileri okul ilan panosu ve web sitesinde [U] | Taşımacı listesi duyurusu |
| `→ YENIDEN` | yonetici | [Servis U-E md. 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) — başvuru olmaması, belgelerin uygun görülmemesi ya da sözleşmenin imzalanmaması hâlinde aynı usulle yeniden [B] | Başvuru olmadığına ya da uygun görülmediğine dair tutanak (OYS'nin "tek katılımcı tutanağı" yerine) |
| Sözleşme dönemi | yonetici | [Servis Araçları Yön. md. 9](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) — şoför ve rehber belge süreleri (`valid_until`) [U] · [Servis EK-2 md. 8](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-8) — her araç komisyonca bildirilen bir muhtaç öğrenciyi ücretsiz taşır: yalnız sayı tutulur [B] · Denetim kaydı (`InspectionRecord`, servis) · [Servis U-E md. 11](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-11), [Servis EK-2 md. 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2-madde-7) — fesih halleri; yazılı bildirime rağmen 15 gün içinde yerine getirilmeyen yükümlülük [U — süre] | Yükümlülüklerin yerine getirilmesi için yazılı bildirim · Fesih bildirimi |

### 7.8 Dönem kapanışı ve devir-teslim

Birlik dönemi genel kuruldan genel kurula sürer (T3). Olağan genel kurul `TUTANAK_TAMAM` olunca yeni dönem açılır,
eski dönem kapanışa girer; iki dönem bir süre birlikte açıktır: genel kurul gününden önceki tarihli kayıtlar eski,
o gün ve sonrası yeni döneme yazılır (tarih–dönem kısıtı sert). Pilot okulda devir tutanağı yoktur (saha 9); tutanak
programdan üretilir.

**Durumlar:** dönem `ACIK → KAPANISTA → KAPANDI`; devir `TASLAK → BASILDI → IMZALANDI`.

| Geçiş | Kim | Kural | Evrak |
|---|---|---|---|
| Yeni dönem `ACIK`, eski `KAPANISTA` | sistem (§7.1); yonetici onaylar | Yeni dönemin başlangıcı = genel kurul günü; eski dönemin bitişi = bir önceki gün [S] · Yeni dönem o günün en yeni kural paketi revizyonuna bağlanır (§6.2-4) · Ders yılı eşlemi (`SchoolYear`) [B] | — |
| Görev bölümü ve hesaplar | sekreter, yonetici | [md. 12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [md. 14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) — bir hafta içinde (§7.2) [U] · Yeni rol hesapları açılır, devir imzalanınca eski YK ve DK hesapları kapanır (§4) | (§7.2'deki görev bölümü evrakı) |
| Devir `TASLAK` | yonetici | [md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10) — toplantı sonunda bütün tutanak ve belgeler yeni YK'ye teslim edilir · Kalemler kayıtlardan önerilir: defterler (karar defterinin son sıra no ve sayfası, gelir-gider defterinin son sayfası, gelen-giden evrak defteri), koçanlar (envanter ve boş yapraklar), dosyalar (genel kurul tutanak dosyası, harcama dosyaları, kantin ve servis dosyaları; [md. 23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)), banka bakiyesi ve imza yetkisi değişikliği ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)), kasa sayımı, açık işler (açık harcama dosyaları, bekleyen kira ve arz, TEFBİS'e girilmemiş ve deftere işlenmemiş kayıtlar), program hesapları | — |
| `TASLAK → BASILDI → IMZALANDI` | yonetici; eski baskan ve muhasip teslim eder, yeni baskan ve muhasip teslim alır | Kasa sayımı ≠ `KASA` bakiyesi → düzeltme kaydı ve gerekçe [U] · Banka bakiyesi = mutabık defter bakiyesi [U] · `EKSIK` kalem [U] · Islak imza kâğıttadır; program "imzalandı" işaretini ve tarihini tutar | Devir-teslim tutanağı · Kasa sayım tutanağı · Makbuz koçanı envanter listesi · Bankaya imza yetkisi değişikliği bildirimi (biçimi DOĞRULANMADI) |
| `KAPANISTA → KAPANDI` | yonetici; baskan onaylar | Aşağıdaki kapanış denetimi; sert maddelerin hepsi geçmeden kapanmaz · `pre-kapanis-<tarih>.odbak` yedeği (§4) · Kapanış bakiyeleri yeni dönemin `OpeningBalance`'ı olur [S] · Arşiv paketi üretilir (§8.5) · Veli listesi, T.C. kimlik no'lar ve süresi dolan telefonlar silinir (§5.4) · Dönem kilitlenir, kural bağı donar (§6.2-6) · Geri alınamaz; düzeltme açık dönemde "önceki dönem düzeltmesi" ters kaydıyla [S] (§15'e öneri B-4) | Dönem kapanış kontrol listesi · Dönem gelir-gider çizelgesi · Karar defteri dizini · Arşiv paketi içerik listesi ([Arşiv Yön. md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) "Dosya/Klasör İçerik Listesi" kalıbında) |

**Kapanış denetimi**

| Denetim | Tür | Dayanak |
|---|---|---|
| Bitiş tarihine kadar banka hareketleri içe aktarılmış (son ekstre tarihi ≥ bitiş) ve hepsi tam eşli | sert (§15'e öneri B-3) | K1; [md. 16/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| `TASLAK` mali kayıt yok | sert | Hesap bütünlüğü |
| `BANKA` + bağlı alt hesapların bakiyesi = bitiş günündeki banka bakiyesi; `KASA`, `SARTLI_BAGIS`, `EMANET` ≥ 0 | sert | Hesap bütünlüğü |
| Genel kurul katılım sayıları dondurulmuş | sert | [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) |
| Veli listesi silinecek (kapanış adımı) | sert | T5 |
| Kasada bekleyen tutar | uyarı | [md. 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| TEFBİS'e girilmemiş ya da "TEFBİS'te düzeltilecek" kayıt | uyarı | [md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Deftere geçirilmemiş gelir-gider kaydı; deftere işlenmemiş karar | uyarı | [md. 13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Açık harcama dosyası | uyarı | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) |
| DK nihai raporu yok; yılda iki inceleme yapılmamış | uyarı | [md. 14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Eksik aylık bildirim; ders dönemi duyurusu eksik | uyarı | [md. 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [md. 13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) |
| Koçanda sıra atlanmış boş yaprak | uyarı | [md. 16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) |
| Defterlerin tasdik kaydı yok | uyarı | [md. 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) |
| Kantinde bekleyen kira, pay dekontu ya da arz | uyarı | [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7), [md. 17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17) |

Olağanüstü genel kurulla YK değişirse dönem kapanmaz; aynı dönem içinde ara devir-teslim yapılır (`Handover`,
`from_term` = `to_term`).

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
| A7 | Yetki | Banka: muhasip, yonetici · TEFBİS: yonetici · e-Okul: yonetici. Her parti denetim izine kim-ne zaman ve özetle yazılır |

### 8.2 Banka özeti (xlsx öncelikli)

Pilot okul internet bankacılığından Excel döküm alabiliyor (saha 3; plan F0-3). Bankanın sütun düzeni örnek gelene
kadar aşağıdaki varsayılan şema geçerlidir; örnek gelince "F1 eki" ile kesinleşir. Her `BankAccount` kendi eşleme
profilini (`import_profile`) taşır: ilk aktarımda kullanıcı onaylar, sonra hatırlanır.

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
sonraya düşen satır reddedilir [S]. Parmak izi (`fingerprint`) çakışan satır elenir, sayısı önizlemede görünür [S]:
böylece kesişen tarih aralıklı iki döküm güvenle aktarılır. Bakiye sütunu varsa zincir denetlenir (önceki bakiye +
tutar = bakiye); kopukluk eksik hareket demektir [U]. İlk satırın bakiyesi `OpeningBalance` ya da önceki partinin son
bakiyesiyle karşılaştırılır [U].

**Eşleme önerileri** (onay kullanıcıdadır, §7.3): kantin aylık satırı (tutar + ayın 5-15'i + sözleşme), kasa yatırması
(kasada bekleyen tutar), ödeme talimatı (tutar + tarih yakınlığı), tekrarlayan açıklama kalıbı (önceki eşleşmeden
öğrenilen kategori), faiz ve banka masrafı.

### 8.3 TEFBİS

TEFBİS'e kaydı okul idaresi girer ([md. 23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)); program otomatik giriş yapmaz (K6). İki yön vardır: programdan TEFBİS'e
girilecekler listesi (dışa), TEFBİS'in "Excel Aktar" çıktısının programa alınması (içe; mutabakat). Varsayılan şema
2009 kılavuzuna ve onun [EK-A işlem tipi listesine](../kesif/kaynaklar/tefbis-2009-kilavuz-ek-a-islem-tipleri.txt)
dayanır; güncel ekran ve çıktı örneği gelince (plan F0-2) "F1 eki" ile kesinleşir.

**(a) TEFBİS'e girilecekler listesi — dışa, aylık, yonetici.** TEFBİS'e girilmemiş `KESIN` kayıtlar, TEFBİS ekranının
sırasıyla (gelirler, sonra giderler; tarih sırası). Biçim PDF + xlsx.

| Sütun | Kaynak | Not |
|---|---|---|
| Gelir / Gider | `direction` | Virman listeye girmez |
| İşlem tarihi | `date` | — |
| Kaynak tipi | `tefbis_source_type` | Yalnız gelirde; yedi üst sınıf |
| İşlem tipi: üst grup › tip › alt kalem | `tefbis_type` | `TefbisTypeMapping`; okulun güncel listesi |
| Açıklama | `description` | Şifre çözülerek basılır; kişi adı içerebilir — çıktı kişisel veri taşır, saklama ve imhası kılavuzda |
| Evrak no, evrak tarihi | `document_no`, `document_date` | Makbuz yaprağında seri-cilt-sıra |
| Faaliyet kodu | `activity_code` | — |
| Karar no | `decision` | Yalnız giderde |
| Detay: işlem türü, miktar, birim, birim fiyat, tutar | `LedgerEntryLine` | Tek satırlı kayıtta kayıt tutarı |
| Kesinti | — | Bilgi; tevkifat hesaplanmaz |
| Kişiden gelen kayıtta ad-soyad | `donor_name` | T.C. kimlik no **dosyaya hiç girmez**; K9 açıksa yalnız ekranda, `yonetici` rolüne maskesiz ve erişim günlüğüyle; kapalıysa "makbuzdan ya da dekonttan girilecek" notu |

"TEFBİS'e girildi" işareti satır satır ya da seçili satırlara topluca konur; ters kayıtla düzeltilen ve önceden girilmiş
kayıtlar ayrı bölümde ("TEFBİS'te düzeltilecek") listelenir.

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
| Personel (Kütüphane Defteri'nde OOK01001R1; OAB'de rapor adı örnekle teyit edilir) | Ad, soyad (ya da "Adı Soyadı"); "Görevi" yalnız tür için geçici (öğretmen · yönetici · diğer) | T.C. kimlik no, telefon, branş, unvan, adres, doğum tarihi | `Personnel` (ad şifreli, `member_kind`); `OabPerson` bağı isteğe bağlı (DK öğretmen adayları, alım komisyonu) | Personel kaydı; ayrılış havuzu (Kütüphane F1 eki 7) aynen |
| Veli (öğrenci listesi türünde, veli sütunlu e-Okul raporu; rapor kodu DOĞRULANMADI, örnek gelince "F1 eki") | Veli adı-soyadı (tek sütun ya da ad + soyad); öğrencinin sınıfı ve şubesi | Öğrencinin adı ve numarası, T.C. kimlik no, telefon, adres, yakınlık, e-posta — bütün diğer sütunlar | `ParentRoster` (ad şifreli + kör indeks, sınıf düz metin); bir satır bir öğrenci | Dönem kapanışında silinir (§5.4, §7.8); genel kuruldan sonra elle de silinebilir |

**Veli listesi kuralları.** (1) Dosyadaki sınıflar dönem içindeki önceki partide aynı sınıfların satırlarının yerini
alır; dosyada olmayan sınıflara dokunulmaz (Kütüphane EK-21 deseni). (2) Önizleme yalnız sayıları gösterir (sınıf başına
satır sayısı); adlar ekranda listelenmez. (3) Liste yalnız iki iş içindir: genel kurul katılım cetvelinin basımı ve
sayımı; aday olacak velinin adının `OabPerson`'a kopyalanması. (4) Telefon ve iletişim yoktur: genel kurul daveti elden
yazılı dağıtılır ([md. 9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)), program SMS ya da e-posta göndermez. (5) İskelet envanteri §2.8'de ALMA yazılan öğrenci
ayrıştırıcısının (`excel_ogrenci.py`) başlık bulma ve Türkçe katlama kısmı veli listesi için UYARLA'ya döner (F1b).

### 8.5 Yıl sonu arşiv paketi (PDF + xlsx + JSON)

Dönem `KAPANDI` olurken üretilir (§7.8). Amaç: defter ve belgelerin okulda saklandığı süre boyunca ([md. 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) dönemin
programdan bağımsız okunabilmesi. Yedek (`.odbak`) programa geri yüklemek içindir; arşiv paketi programsız okumak içindir.

| Yol | İçerik | Biçim |
|---|---|---|
| `00-BENIOKU.txt` | Paketin nasıl açılıp okunacağı; okul, dönem, oluşturma tarihi, program sürümü, kural paketi ve revizyonu, şema sürümü | düz metin (UTF-8) |
| `01-evrak/` | Dönemin bütün `GeneratedDocument` dosyaları, evrak türü klasörleriyle; yerini alan eski sürümler `eski/` altında | PDF (Word isteğe bağlı) |
| `02-defterler/` | Gelir-gider kayıtları (defter düzeninde, düzeltme satırlarıyla); banka hareketleri ve eşleşmeler; karar dizini; gelen-giden evrak; koçan envanteri ve yapraklar; harcama dosyaları dizini; organ üyelikleri; genel kurul özetleri (katılım sayılarıyla); kira, arz ve pay çizelgeleri; TEFBİS girildi listesi; sapma kayıtları (`ComplianceItem`); denetim izi dökümü | xlsx |
| `03-veri/` | Her model için kayıt listesi; şifreli alanlar çözülmüş; şema `docs/arsiv-paketi.md`'de tek sürümlü | JSON |
| `04-ekler/` | Saklama süresi içindeki `Attachment` dosyaları; `OZEL_NITELIKLI` olanlar varsayılan hariç | özgün biçim |
| `05-icerik-listesi.pdf` | [Arşiv Yön. md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) "Dosya/Klasör İçerik Listesi" kalıbında içerik listesi | PDF |
| `SHA256SUMS.txt` | Her dosyanın özeti | düz metin |

**Dışarıda kalanlar:** veli listesi (kapanışta silinir), T.C. kimlik no, özel nitelikli ekler (varsayılan; açık seçimle
girer), şifreleme anahtarları ve hesap bilgileri.

**Koruma.** Paket kişisel veri taşır ve çoğunlukla USB'ye kopyalanır; MEB Bilgi ve Sistem Güvenliği Yönergesi
taşınabilir ortamdaki önemli veriyi şifreli ister ([BSG Yönergesi md. 10/5](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10)). Öneri: AES-256 şifreli ZIP (7-Zip ve Pardus arşiv
yöneticisi açar; Windows Gezgini açamaz, BENIOKU bunu yazar); parolayı kapanışta yönetici belirler, kurtarma anahtarı
gibi paketten ayrı saklanır. Yeni bağımlılık (ör. `pyzipper`) §11 bağımlılık kesim listesine girer (§15'e öneri B-10).
PDF'lerin uzun süre okunabilirliği için PDF/A çıktısı (WeasyPrint) §9'da değerlendirilir.

### 8.6 Diğer çıktılar

| Çıktı | Kim | Not |
|---|---|---|
| Deftere geçirilecek kayıtlar (aylık) | muhasip | §7.3; PDF + xlsx; asgari sütunlar §15 A-12 |
| Banka mutabakat çizelgesi (aylık) | muhasip | §7.3 |
| Kişi dökümü ([KVKK md. 11](../mevzuat/6698-kvkk.md#madde-11) başvurusu) | yonetici | Bir kişinin üyelik, aday, bağış (ad), ödeme ve katılım kayıtları; erişim günlüğüne yazılır |
| Denetim tabloları ([TKB E.4 §3.2](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) Tablo 1, [TKB E.4 §3.3](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-3) Tablo 2, [TKB E.4 §4](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4) Tablo 3-4) | yonetici | Kişisiz sayılar; M12b sürüm 2, veri bugünden hazır |
| Duyuru web metni | yonetici | Tek HTML dosyası, dış bağlantısız; program yayımlamaz, okul sitesine kullanıcı taşır |

---

## 9. Evrak kataloğu

Program birliğin ve okulun evrakını **hazırlar**; karar defterinin, tasdikli defterlerin, makbuz koçanının ve TEFBİS
kaydının yerine geçmez (konum, §9.2). Kaynaklar: genel OAB seti (`GNL-OAB-FR-001…023`, `GNL-OAB-RH-001`; CC BY 4.0),
OYS'nin 19 belge şablonu (envanter §5) ve Yönetmeliğin resmî ekleri. Program kodu **`E01`…`E62`**; belge altlığında
"OAB Defteri · E07 · Sayfa n/m" yazar, kural paketi revizyonu basılmaz (evrak izinde tutulur).

### 9.1 İlkeler

1. **Tek içerik, iki çizici** (T2). Belgenin cümleleri, tabloları ve imza blokları bir kez Python'da içerik modeli
   olarak kurulur; Word (python-docx) ve PDF (WeasyPrint) yalnız düzeni çizer. Listeler ayrıca xlsx (openpyxl) verir;
   duyurular ayrıca tek dosyalık, dış kaynaksız HTML verir (okul web sitesine elle konur; ağ servisi yok).
2. **Evrak izi.** Her üretim bir `GeneratedDocument` kaydıdır: kod, dönem, kural paketi (kimlik + rev), üreten
   kullanıcı, zaman, **içerik özeti** (içerik modelinin kanonik JSON'unun SHA-256'sı; docx zip baytı değil) ve dosya
   özetleri. Kapanmış dönemin belgesi yeniden basıldığında içerik özeti aynı çıkar (§6.2-6).
3. **Tek kaynak** (OYS ilkesi, AYNEN). Aday listesi, tutanak, sonuç bildirimi, faaliyet raporu ve devir-teslim aynı
   kayıtlardan dolar; birbiriyle çelişemez.
4. **Türkçe ve biçim.** Büyük harf yalnız `tr_upper` ile; `text-transform`, `w:caps` ve çıplak `.upper()` yasak.
   Resmî yazılar (E12, E25, E35, E40, E44) [RYUE md. 7](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-7),
   [md. 12](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-12) ve
   [md. 17](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-17) biçimindedir
   (yazı tipi, `gg.aa.yyyy`, imza bloğunda ad + SOYAD + unvan). Sayfa bütçesi gerçek uzunlukta uydurma veriyle sınanır.
5. **KVKK.** İlan panosu ve internet çıktılarında (E06, E29, E30) hiçbir kişi adı yoktur, başkanınki de: imza
   "Okul-Aile Birliği Yönetim Kurulu" olur. Kişi adı taşıyan iç belgeler "Kişisel veri içerir — asılmaz, okul dışına
   verilmez" dipnotu taşır. T.C. kimlik no hiçbir belgede yoktur; K9 açıksa yalnız bağış çizelgesinde maskeli.
   Adli sicil ve sağlık belgelerinin içeriği basılmaz, yalnız "teslim alındı" + tarih.
6. **Uyarı kutusu resmî evraka basılmaz.** OYS'nin `_compliance_warnings.html` parçası alınmaz: kural sapmasının
   gerekçesi `ComplianceItem` ve denetim izinde kalır, istenirse ayrı iç belge olarak dökülür (KE-16).
7. **Mevzuat lafzı kilidi.** Resmî ekin metnini taşıyan belgeler (E42 EK-2 sözleşmesi, E55 servis sözleşmesi) metni
   `docs/mevzuat/` korpusundan alır ve testte karakter karakter karşılaştırılır; yalnız boşluk (`……`) alanları dolar.

### 9.2 Konum cümlesi

Üç kalıp vardır; belge altlığında, imza bloklarının üstünde 9 punto yazılır ve ekrandaki önizlemede de görünür.

| Kısa ad | Metin | Dayanak | Belgeler |
|---|---|---|---|
| **KD** | "Bu metin yönetim kurulu karar taslağıdır. Kararlar noterce tasdikli yönetim kurulu karar defterine el ile yazılarak imzalanır; bu belge karar defterinin yerine geçmez." | [13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E01, E03, E15, E22 (koçan seri no'ları), E36, E40, E41 |
| **TF** | "Birliğin gelir ve gider kayıtları ile diğer mali işlemleri TEFBİS'e okul idaresince kaydedilir; bu belge TEFBİS kaydının yerine geçmez." | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E13, E18, E20, E27, E28, E31, E34, E60 |
| **DF** | "Bu döküm il/ilçe millî eğitim müdürlüğünce tasdikli deftere geçirilmek üzere hazırlanmıştır; defterin yerine geçmez." | [23/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | E17, E23 |

KD taşıyan belgelerin başlığında "TASLAK — karar defterine geçirilecek metin" ibaresi vardır; "deftere işlendi"
işareti (defter sıra no ve sayfa) konduktan sonra da taslak ibaresi kalkmaz. Kantin ve servis ekranlarında ayrıca
"Program komisyon kararının yerine geçmez" cümlesi görünür; bu cümle komisyonun kendi evrakına (E54) basılmaz.

### 9.3 İmza blokları

Belgeyi hazırlayan organ imzalar: YK belgelerini YK (başkan; görevine göre muhasip ve sekreter), DK belgelerini DK
asıl üyeleri, genel kurul belgelerini divan. **Okul müdürü yönetim kurulu üyesi değildir**; YK ve genel kurul
belgelerinde yazar ya da imzacı olarak yer almaz. Müdür yalnız mevzuatın ona rol verdiği yerde görünür: genel kurul
belgelerinde "Görüldü" ([10/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10),
[27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)) · aylık bildirimde ve ayni bağışta "Teslim alan"
([18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18),
[16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16)) · işlem dosyasında "Kontrol eden"
([27/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27)) · etkinlikte "Uygunluk görüşü"
([6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6)) · arz bedeli takibinde sorumlu
([17/1-b-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17)) · kendi yazıları (E25 harcama talebi, E35
uyarı, yeni okulda E05 çağrı) · okul idaresinin resmî yazıları (E12, E40 üst yazısı, E44) · servis komisyonunun
başkanı olarak (E48-E57). Bloklar organ üyeliğinden dolar; görev boşsa basımda uyarı verilir, blok "………" kalır.

OYS'den gelen hataların düzeltilmesi:

| Belge | OYS'de | OAB Defteri'nde | Dayanak |
|---|---|---|---|
| GK davetiyesi (E05) | Okul Müdürü | Birlik Başkanı (YK adına) + Sekreter; yeni okulda Okul Müdürü; olağanüstüde çağırana göre (KE-11); müdür yalnız "Görüldü" | [9/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) |
| Tahmini bütçe (E28) | Okul Müdürü; "onaylandı" | YK adına Birlik Başkanı + Muhasip (+ asıl üyeler); "genel kurulda görüşüldü" | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| Gelir-gider çizelgesi (E34'e katıldı) | Okul Müdürü | Muhasip + Birlik Başkanı; kesin hesap YK asıl üyeleriyle | [13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) |
| Yeter sayı yok tutanağı (E08) | Birlik Başkanı + Okul Müdürü | Birlik Başkanı + Sekreter; "Görüldü — Okul Müdürü" (mevzuat imzacı saymaz, KE-10) | [9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), 27/1 |
| Aday listeleri (E09) | DK öğretmen koltukları listede | Yalnız GK'nin seçtiği koltuklar; öğretmenler bilgi satırı | [11/1-b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [14/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) |
| Servis komisyon kararı (E54) | "Oy birliği ile" sabit | Oylama sonucu; muhalif üyenin gerekçesi ve imzası | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4) |
| Kira sözleşmesi (E42) | Servis maddeleri, "Taşımacı" tarafı | EK-2 tam metni; Birlik Başkanı + Kiracı + varsa esnaf odası temsilcisi | [21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21), [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) |

### 9.4 Servis söz dağarcığı ve EK-3'ün lafzı

Servis evrakında (E48-E58) "ihale", "teklif", "eksiltme" yazılmaz: 30.05.2018 metni eksiltmeyi ve teminatı kaldırdı,
seçim [U-E 8/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)'deki ölçütlerle yapılır. Kantin evrakında
"ihale" serbesttir (md. 20 "kantin kiralama ihaleleri" der).

| OYS'de / eski metinde | Servis evrakında | Dayanak |
|---|---|---|
| ihale, servis ihalesi | servis çalıştırma işi · taşımacının tespiti | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5), [OSAY 8/1](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) |
| ihale ilanı | servis çalıştırma işinin ilanı | U-E 5/3 |
| teklif, teklif toplama | başvuru · başvuru dosyası · dosyaların teslimi | [U-E 7/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) |
| ihale tarihi / saati | dosyaların açılma tarihi / saati | U-E 8/1 |
| ihale komisyonu | Taşımacıyı Tespit Komisyonu | [U-E 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) |
| en düşük teklif | — (yürürlükte değil; kaldırılır) | U-E korpus notu |
| istekli | istekli (değişmez) | U-E 3/1-c |

Lafız sorunları ve öneri:

- **EK-3 4. kriter** ("İsteklinin taşıma işini yaptığı aynı okula **teklif** vermesi halinde"). Seçenekler: (a) lafzı
  tırnak içinde aynen basmak, (b) "teklif"i "başvuru" ile değiştirmek — mevzuat metni değiştirilemeyeceği için
  reddedilir, (c) puanlama cetvelinde kriteri kısa adla basmak: "4) Aynı okulda hâlen taşıma işini yapan istekli
  (EK-3, kriter 4)". **Öneri (c)** (KE-8): cetvel mevzuat metni değil, komisyonun değerlendirme aracıdır; kriter
  numarası ve atıf kaynağı gösterir, lafız evrakta alıntılanmaz.
- **Suç adı "ihaleye fesat karıştırma".** Servis sözleşmesinin (U-E EK-2 md. 4, 7) ve tip şartnamenin (EK-1 md. 6)
  lafzında TCK suç adı olarak geçer; sözleşme metni değiştirilemez. **Öneri** (KE-9): söz dağarcığı testinin tek
  istisnası bu tam ibaredir.

### 9.5 Katalog — kimlik, dayanak, kaynak, biçim, faz

Biçim: "docx+pdf" iki çizici · "xlsx" ek döküm · "html" web duyurusu. Dayanak atıflarında yalın numara OAB
Yönetmeliğidir; kısaltmalar §6.4'teki gibidir; TKB E.4 rehberdir, mevzuat değildir (kabul ölçütü).

| Kod | Belge | Dayanak | Kaynak şablon | Biçim | Faz |
|---|---|---|---|---|---|
| E01 | YK görev bölümü, imza yetkisi ve temsilci karar taslağı | [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12), [13/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | GNL-OAB-FR-006 | docx+pdf | F1c |
| E02 | Denetleme Kurulu görev bölümü tutanağı ve denetim planı | [14/1-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) | GNL-OAB-FR-011 | docx+pdf | F1c |
| E03 | Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi | [13/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13); [OKY 185](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-185), [OKY 25](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-25); [OÖİKY 57](../mevzuat/meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md#madde-57); [SEY 6/1](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-6); [RPD 16](../mevzuat/meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md#madde-16); [OSAY 3/1-m](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-3) | GNL-OAB-FR-022 | docx+pdf | F1c |
| E04 | Kişisel veri aydınlatma metni (veli, bağışçı, organ üyesi) | [KVKK md. 10](../mevzuat/6698-kvkk.md#madde-10) | yeni (Kütüphane Defteri E13 kalıbı) | docx+pdf | F2 (metni F1b içe aktarma ekranında) |
| E05 | Genel kurul toplantı çağrısı ve gündemi (dosya nüshası) | [9/1-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [10/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-002 A-B; OYS `davetiye.html`, `gundem.html` | docx+pdf | F2 |
| E06 | Genel kurul duyurusu — ilan panosu ve internet sayfası (kişisiz) | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), 9/6 | GNL-OAB-FR-002 C | pdf, html | F2 |
| E07 | Üyelere elden yazılı davet ve sınıf teslim çizelgesi | [9/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [7/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) | GNL-OAB-FR-002 D | docx+pdf | F2 |
| E08 | Katılım cetveli ve yeter sayı tespit tutanağı | [10/1-a](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [9/2, 9/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) | GNL-OAB-FR-003; OYS `yeter_sayi_yok.html`, `build_imza_surkusu_xlsx` | docx+pdf, xlsx | F2 |
| E09 | YK ve DK (veli koltuğu) aday listeleri | [10/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1-a, b](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [12/1, 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-004 D; OYS `aday_listeleri.html` | docx+pdf | F2 |
| E10 | Genel kurul toplantı tutanağı | [9/2-6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9), [10/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-004; OYS `tutanak.html` | docx+pdf | F2 |
| E11 | İbra edilmeyen muhasebe evrakının teslim tutanağı (divan) | [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-005 B (satır 9) | docx+pdf | F2 |
| E12 | İbra edilmediğine dair il/ilçe MEM'e resmî yazı | [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | yeni (RYUE biçimi) | docx+pdf | F2 |
| E13 | Genel kurul sonuç bildirimi (okul müdürlüğüne) | [10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-005 A, C | docx+pdf | F2 |
| E14 | Yıllık iş takvimi | kural paketinin süre kuralları (§6.4) | GNL-OAB-RH-001 Bölüm 6 | pdf, xlsx | F2 |
| E15 | YK toplantı gündemi ve karar taslağı | [13/3, 13/5, 13/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | GNL-OAB-FR-007 | docx+pdf | F3 |
| E16 | YK toplantı ve katılım izleme çizelgesi | [13/3, 13/6, 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7), [12/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-008 | docx+pdf, xlsx | F3 |
| E17 | Gelir-gider defterine geçirilecek kayıtlar (aylık) | [23/1-ç, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (saha.md 1b sütunları) | pdf, xlsx | F3 |
| E18 | TEFBİS'e girilecekler listesi | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (K6; 2009 kılavuzu alanları) | pdf, xlsx | F3 |
| E19 | Banka mutabakat dökümü (banka ↔ defter) | [16/1, 16/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16) | yeni (K1) | pdf, xlsx | F3 |
| E20 | Bağış kabul ve kayıt izleme çizelgesi | [6/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [16/1-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [24](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-24); [G.2011/40](../mevzuat/ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md#genelge-metni) | GNL-OAB-FR-014 A, C | docx+pdf, xlsx | F3 |
| E21 | Ayni bağış teslim tutanağı (okul müdürlüğüne) | [16/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); [TMY 16/1](../mevzuat/tasinir-mal-yonetmeligi.md#madde-16) | GNL-OAB-FR-014 B | docx+pdf | F3 |
| E22 | Defter, makbuz ve belge tasdik-kayıt çizelgesi; koçan yaprak dökümü | [16/5-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16), [23/1-2, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [EK-1](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md#ek-1) | GNL-OAB-FR-015 | docx+pdf, xlsx | F3 |
| E23 | Gelen-giden evrak defterine geçirilecek kayıtlar | [23/1-c, 23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni | pdf, xlsx | F3 |
| E24 | Kantin kira tahsilat, arz bedeli ve pay dağıtım izleme çizelgesi | [17/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17), [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 4](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-4), [md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7), [md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8) | GNL-OAB-FR-021 | docx+pdf, xlsx | F3 |
| E25 | Okul yönetimi ihtiyaç ve harcama talep yazısı | [18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18); [OKY 78/4-e](../mevzuat/ortaogretim-kurumlari-yonetmeligi.md#madde-78) | GNL-OAB-FR-016 | docx+pdf | F4 |
| E26 | Mal ve hizmet alım komisyonu piyasa araştırması ve karar tutanağı | [18/1, 18/3-4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [12/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) | GNL-OAB-FR-017 | docx+pdf | F4 |
| E27 | Harcama belgesi kontrol ve ödeme onay formu; banka ödeme talimatı | [18/1-3, 18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | GNL-OAB-FR-018 | docx+pdf | F4 |
| E28 | Tahmini bütçe | [11/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 A; OYS `tahmini_butce.html` | docx+pdf, xlsx | F4 |
| E29 | Bütçe duyurusu (pano + internet; kişisiz) | [13/9](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 A, C | pdf, html | F4 |
| E30 | Dönemlik gelir-gider duyurusu (kişisiz) | [13/10](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-010 B, C | pdf, html | F4 |
| E31 | Birlik başkanının okul müdürüne aylık bildirimi | [18/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18), [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [27/2-3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-009 | docx+pdf | F4 |
| E32 | Denetleme Kurulu ara denetim raporu | [14/4-5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14); [TKB E.4 §3-4](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3) (rehber) | GNL-OAB-FR-012; OYS `dk_faaliyet_raporu.html` | docx+pdf | F4 |
| E33 | Denetleme Kurulu nihai (yıllık) raporu | [14/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14), [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) | GNL-OAB-FR-013; OYS `dk_faaliyet_raporu.html` | docx+pdf | F4 |
| E34 | YK yıllık faaliyet raporu ve kesin hesap cetveli | [11/1-c](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [13/1, 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) | GNL-OAB-FR-023; OYS `yk_faaliyet_raporu.html`, `gelir_gider_cizelgesi.html` | docx+pdf, xlsx | F4 |
| E35 | Okul müdürünün birlik başkanına yazılı uyarısı | [27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | yeni (RYUE biçimi) | docx+pdf | F4 |
| E36 | Sosyal-kültürel etkinlik / kampanya gelir-gider kayıt ve onay formu | [6/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6), [15/1-c, 15/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-15), [19/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [25/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-25); [SEY 5/8](../mevzuat/meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-5) | GNL-OAB-FR-020 | docx+pdf | F4 |
| E37 | Devir-teslim tutanağı | [10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10), [11/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) | GNL-OAB-FR-005 B, C | docx+pdf | F4 |
| E38 | OAB işlem dosyası kapak ve kontrol listesi | [23/1, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23), [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26), [27/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) | GNL-OAB-FR-001 | docx+pdf | F4 |
| E39 | Yıl sonu arşiv paketi içerik listesi | [23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [DAHY md. 11/5](../mevzuat/devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md#madde-11) (kıyasen) | yeni | pdf, xlsx, JSON | F4 |
| E40 | Kantinin kiralanacağına dair bildirim (okul müdürlüğü vasıtasıyla il/ilçe MEM'e) | [G.2024/35 II-1](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-1) | yeni | docx+pdf | F5 |
| E41 | Yeniden kiralama talebine yazılı cevap | [21/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 I-3, I-4](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-3) | yeni | docx+pdf | F5 |
| E42 | Kantin ve benzeri yerleri kiralama sözleşmesi | [21/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#ek-2) | Yön. EK-2 (korpus metni) | docx+pdf | F5 |
| E43 | Kantin yer teslim ve tahliye tutanağı | [21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [EK-2 md. 12](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-12), [md. 13](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-13) | yeni | docx+pdf | F5 |
| E44 | Sözleşme örneğinin millî emlak birimine gönderilmesi | [21/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21) | yeni (RYUE biçimi) | docx+pdf | F5 |
| E45 | Yenilenen kira bedelinin (TÜFE) il/ilçe MEM'e bildirimi | [21/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21); [G.2024/35 I-9](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-9) | yeni | docx+pdf | F5 |
| E46 | Kantin işletmeci ve çalışan belge izleme çizelgesi | [20/6-7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); [HEY 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5) | yeni | pdf, xlsx | F5 |
| E47 | Yükümlülük ihtarı (15 gün) | [22/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) | yeni | docx+pdf | F5 |
| E48 | Servis çalıştırma işinin ilanı | [U-E 5/3-4](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5), [U-E 6/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6) | OYS `ihale_ilani.html` | docx+pdf | F6 |
| E49 | İlan asma ve indirme tutanağı | [U-E 5/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5) | OYS `ilan_asma_tutanagi.html`, `ilan_indirme_tutanagi.html` | docx+pdf | F6 |
| E50 | Tip şartname (EK-1) teslim tutanağı | [U-E 5/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-5); [U-E EK-1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1) | OYS `sartname_teslim_tutanagi.html` | docx+pdf | F6 |
| E51 | Başvuru dosyası teslim tutanağı | [U-E 7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7) | OYS `evrak_teslim_tutanagi.html` | docx+pdf | F6 |
| E52 | Belge kontrol ve tespit tutanağı | [U-E 8/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8), [U-E 6/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-6) | OYS `evrak_kontrol_cetveli.html` | docx+pdf | F6 |
| E53 | EK-3 puanlama cetveli (yalnız itiraz / yeni okul) | [U-E 8/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [U-E EK-3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-3) | OYS `puanlama_cetveli.html` | docx+pdf | F6 |
| E54 | Taşımacının tespiti komisyon kararı | [U-E 4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4), [U-E 8/2, 8/5](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8); [OSAY 8/2](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-8) | OYS `komisyon_karari.html` | docx+pdf | F6 |
| E55 | Okul servis araçları sözleşmesi | [U-E 10/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10); [U-E EK-2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-2) | OYS `sozlesme_taslagi.html` (servis kısmı) + korpus metni | docx+pdf | F6 |
| E56 | Sözleşme imzalanan taşımacıların ilanı | [U-E 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10) | yeni | pdf, html | F6 |
| E57 | Yeniden çıkma tutanağı | [U-E 8/7](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8) | OYS `tek_katilimci_tutanagi.html` (yeniden adlandırılır) | docx+pdf | F6 |
| E58 | Servis belge izleme çizelgesi | [U-E 9](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-9); [OSAY 4/1-f](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-4), [OSAY 9](../mevzuat/okul-servis-araclari-yonetmeligi.md#madde-9) | yeni | pdf, xlsx | F6 |
| E59 | Denetim dosyası: TKB E.4 Tablo 1-4 | [26/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-26); [TKB E.4 §3.2-4.1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-2) (rehber) | yeni | xlsx, pdf | F8+ |
| E60 | TEFBİS Excel mutabakat raporu (banka ↔ defter ↔ TEFBİS) | [23/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) | yeni (K6) | xlsx, pdf | F8+ |
| E61 | Birlik personeli istihdam dosyası ve özlük takip formu | [6/1-d](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-6); [5510 md. 11](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-11), [md. 86](../mevzuat/5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md#madde-86) | GNL-OAB-FR-019 | docx+pdf | F8+ |
| E62 | Yıllık ücretli izin kayıt belgesi | [4857 md. 53](../mevzuat/4857-is-kanunu.md#madde-53), [md. 56](../mevzuat/4857-is-kanunu.md#madde-56) | yeni | docx+pdf, xlsx | F8+ |

**Faz dağılımı:** F1c 3 · F2 11 · F3 10 · F4 15 · F5 8 · F6 11 · F8+ 4 = **62** (F2'ye E04 aydınlatma metni dâhil).
**Kaynak kapsaması:** GNL setinin 23 formu ve RH-001 en az bir koda karşılık gelir. OYS'nin 19 belge şablonunun
hepsi UYARLA ile bir koda girer; iki parçadan `_commission_signatures.html` ilke olarak alınır (yalnız ad + görev),
`_compliance_warnings.html` alınmaz (§9.1-6); `build_imza_surkusu_xlsx` E08'e girer.

### 9.6 Katalog — veri, roller, imza, kabul

"Üreten": belgeyi programda oluşturup düzenleyebilen rol (K2; kaydedilmiş belgeyi her okur rol basabilir).
`denetleme_kurulu` yalnız E02, E32, E33'ü; `mudur` yalnız kendi yazılarını (E25, E35, yeni okulda E05) üretir. Okul
idaresinin resmî yazılarının (E12, E40 üst yazısı, E44) ve servis komisyonu evrakının taslağını `yonetici` (OAB'den
sorumlu müdür yardımcısı) hazırlar, kâğıdı müdür imzalar; müdür rolüne yeni yazma yetkisi eklenmez. "Konum" §9.2.

| Kod | Veri kaynağı | Üreten | İmza bloğu | Konum | Kabul örneği (uydurma veriyle) |
|---|---|---|---|---|---|
| E01 | `OabTerm`, `OrganMembership` (görev, asıl/yedek, oy sırası, dönem sayacı, beyan), `OabPerson`, `BankAccount` (IBAN maskeli), görev bölümü toplantısı ve karar no (§5'te asgari `BoardMeeting`/`BoardDecision`) | sekreter, yonetici | YK asıl 5 üye, görev unvanlarıyla | KD | 5+5 kadro: dört görev dolu ve tekil; "kaçıncı dönem" sayaçtan; beyan sütunu işaretli; imza yetkisi başkan + muhasip (yokluğunda başkan yardımcısı); temsilci satırları E03 ile aynı kişiler; FR-006 A-D bölümleri var |
| E02 | `OrganMembership` (DK; seçim kanalı), `OabPerson`, `OabTerm`, denetim planı (ayar) | denetleme_kurulu (üyelik kaydı yonetici) | DK asıl 3 üye; "Bilgi: Birlik Başkanı"; "Görüldü: Okul Müdürü" | — | Veli koltuğu GK seçimi, iki öğretmen öğretmenler kurulu seçimi ayrı satırda; hayırsever yok; başkanlık sayacı ≤ 3; planda ≥ 2 ara denetim |
| E03 | `OrganMembership` (temsilci türleri, YK karar no/tarih), `OabPerson`, okul kartı (kademe) | sekreter, yonetici | Sekreter + Birlik Başkanı; "Teslim alan: Okul Müdürü" | KD | Ortaöğretimde ödül-disiplin ve kontenjan satırı, ortaokulda davranış kurulu satırı; servis, muhammen bedel ve ihale komisyonu satırlarında başkanın adı kendiliğinden |
| E04 | okul kartı (veri sorumlusu alanı, KE-20), sabit veri kategorileri | yonetici | imzasız bilgi metni | — | KVKK 10/1 a-d unsurlarının her biri ayrı başlıkta; "T.C. kimlik no tutulmaz" (K9 kapalıyken); veli listesinin dönem kapanışında silindiği yazılı |
| E05 | `GeneralAssembly` (tür, çağıran, 1./2. toplantı, yer, yeter sayı anlık değeri), `AgendaItem`, davet kararı (`BoardDecision`) | sekreter, yonetici; yeni okulda mudur | Birlik Başkanı (YK adına) + Sekreter; "Görüldü — Okul Müdürü (md. 27/1)" | — | Yeter sayı 64/32 paketten; 2. toplantı ≤ 30 gün; olağan gündemde 11/1-e ve f maddeleri var (OYS tohumunda yoktu); 14 gün kala basımda uyarı |
| E06 | `GeneralAssembly`, `AgendaItem`, `Announcement` (kanıt) | sekreter, yonetici | "Okul-Aile Birliği Yönetim Kurulu" | — | Çıktıda hiçbir `OabPerson` adı yok (test); html tek dosya, dış bağlantısız |
| E07 | `GeneralAssembly`, `ParentRoster` (sınıf/şube sayıları; teslim çizelgesinde veli adı) | sekreter, yonetici | Davet: "Yönetim Kurulu adına Birlik Başkanı"; çizelge: sınıf rehber öğretmeni (teslim eden) | — | Davet mektubu kişisiz ("Sayın Veli"), sınıf başına adet; çizelge kişisel veri dipnotlu |
| E08 | `GeneralAssembly` (katılan, yeter sayı), `ParentRoster` (veli adı + öğrencinin sınıfı), öğretmen ve yönetici listesi, gözlemci öğrenciler (ayrı liste) | yonetici, sekreter | Sağlandıysa Divan Başkanı + Kâtip (sayfa parafı); sağlanamadıysa Birlik Başkanı + Sekreter + "Görüldü — Okul Müdürü" (KE-10) | — | 99 öğrenci → 32, 100 → 64; boş satırlı seçenek; xlsx ile PDF aynı sırada; T.C. kimlik no ve telefon sütunu yok |
| E09 | `OrganMembership` (ADAY), `OabPerson` (tür), kişi geçmişi (dönem sayacı) | sekreter, yonetici | Divan Başkanı + Kâtip | — | DK öğretmen koltukları oylamaya girmez (bilgi satırı); YK adayı veli/kursiyer/hayırsever; aday listesi ile E10 seçim sonucu aynı kişiler |
| E10 | `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes` (divan, ibra, oylamalar), `OrganMembership` (SEÇİLDİ), `OabBudget` | sekreter, yonetici | Divan Başkanı + Kâtip; "Görüldü — Okul Müdürü (md. 27/1)" | — | YK ve DK ibrası ayrı oylama satırı; "ibra edilmedi" E11-E12'yi açar; bütçe "görüşüldü" yazar |
| E11 | `AssemblyMinutes` (ibra), `DocumentRecord` (teslim edilen evrak) | sekreter, yonetici | Divan Başkanı + Kâtip; teslim alan yeni YK ve DK adına birer üye | — | Evrak tek tek listeli; tarih GK günü |
| E12 | `AssemblyMinutes`, `GeneralAssembly`, okul kartı (antet) | yonetici (taslak) | Okul Müdürü + Birlik Başkanı (yeni YK adına) | — | RYUE: sayı, `gg.aa.yyyy`, konu, muhatap "… Millî Eğitim Müdürlüğüne"; ek E11 |
| E13 | `GeneralAssembly`, `OrganMembership`, `OabBudget`, `AssemblyMinutes` | sekreter, yonetici | Birlik Başkanı (yeni) + Sekreter; "Teslim alan: Okul Müdürü" | TF | Seçilenler E10 ile aynı; sonraki adımlar tarihli (görev bölümü ≤ 7 gün, banka imza yetkisi, TEFBİS girişi) |
| E14 | kural paketi (süreler), ders yılı takvimi, ayarlar (YK günü, DK planı), `OabTerm` | yonetici | — | — | Her satır kural kimliği ve atıf taşır; "okul planı / öneri" satırları ayrı biçimde; Ekim sonu, 15, 30, 7 gün ve arz 10/20 tarihleri doğru |
| E15 | `BoardMeeting`, `BoardMeetingAttendance`, `BoardDecision` (sıra no, oylar, bağlı işlemler) | sekreter | Katılan YK üyeleri | KD | < 4 katılımda karar bölümü yerine "toplantı yapılamadı"; kabul < 3 karar "alınmadı"; harcama kararında konu, üst sınır, bütçe kalemi, komisyon üyeleri dolu |
| E16 | `BoardMeeting`, `BoardMeetingAttendance`, `OrganMembership` | sekreter | Birlik Başkanı + Sekreter | — | Üst üste 3 özürsüz (toplantılar üzerinden) işaretli; yedek çağrısı ve görev bölümü satırı; aylık bildirim tarihleri E31'den |
| E17 | `LedgerEntry`, `LedgerAccount`, `BankTransaction`, `TransactionMatch`, `ReceiptLeaf`, `BoardDecision` | muhasip | Muhasip + Birlik Başkanı | DF | Sütunlar: tarih · sıra no · belge/evrak no · açıklama · gelir · gider · kalan · karar no · gelir-gider türü; kalan = banka + kasa; ters kayıt ayrı satır |
| E18 | `LedgerEntry`, `TefbisTypeMapping`, `ReceiptLeaf` | muhasip, yonetici | — (iş listesi); "girildi" işaretini yonetici koyar | TF | Her satırda TEFBİS işlem tipi dolu (eşleme yoksa basılmaz, uyarı); kişi kaydında T.C. kimlik no sütunu yok, "kâğıt koçandan girilir" notu |
| E19 | `BankAccount`, `BankTransaction`, `LedgerEntry`, `TransactionMatch` | muhasip | Muhasip | — | Eşleşmeyen hareketler ve 5 iş gününü aşan kasa ayrı bölümde |
| E20 | `LedgerEntry` (bağış), `LedgerAccount` (şartlı alt hesap), `ReceiptLeaf`, `OabPerson` (bağışçı) | muhasip | Muhasip + Birlik Başkanı | TF | Şartlı bağış kalanı alt hesap bakiyesiyle aynı; kayıt dönemi uyarısı ekranda, çıktıda değil; T.C. kimlik no yalnız K9 açıkken maskeli |
| E21 | `LedgerEntry` (ayni), `OabPerson`, VİF no/tarih alanı | muhasip | Teslim eden: Birlik Başkanı ya da Muhasip; Teslim alan: Okul Müdürü; taşınır kayıt yetkilisi (VİF) | — | Cins, miktar, takdir değeri; VİF no boşsa basımda uyarı; VİF'in bir nüshasının bağışçıya verileceği notu |
| E22 | `ReceiptBookRegistry`, `ReceiptLeaf`, `DocumentRecord` (defterler, tasdik), `BoardDecision` (koçan kaydı) | muhasip, sekreter | Muhasip + Sekreter + Birlik Başkanı; "Mühürleyen — Okul Müdürlüğü" | KD | Her cilt 50 yaprak; kullanılan + iptal + boş = 50; aynı seri-cilt-sıra iki kez yok; karar defteri noter, diğerleri MEM tasdik satırında |
| E23 | `DocumentRecord` (gelen/giden, sayı, tarih, konu), `GeneratedDocument` | sekreter | Sekreter | DF | Sıra no kesintisiz; programın ürettiği yazılar giden olarak önerilir |
| E24 | `OabContract`, `ContractInstallment` (aylık kira takvimi), `ShareStatement`, `BankTransaction`, okul kartı (yerleşim türü) | muhasip | Muhasip + Birlik Başkanı + Okul Müdürü (md. 17/1-b-5) | — | 9 aylık sözleşme: Ocak yarım, Haziran-Ağustos boş; il merkezi okulunda ilçe sütunu 0, il %20; arz son ödeme 10'u ve 20'si ayrı sütunda, iki ayrı uyarı |
| E25 | `ExpenseFile` (talep, gerekçe, kalemler) | mudur (yonetici taslak hazırlayabilir) | Talep eden + Okul Müdürü; "Birlik işlemi": Sekreter + Birlik Başkanı | — | Kalem toplamı tutar; YK karar no ayrı bölümde; müdür hesabının yazısı (denetim izi) |
| E26 | `ExpenseFile` (teklifler, komisyon, teslim), `OrganMembership` (alım komisyonu), `BoardDecision` | muhasip, sekreter | Komisyon üyeleri (≥ 3) + Birlik Başkanı; teslim bölümünde taşınır kayıt yetkilisi | — | < 3 üyede gerekçe satırı; "en az üç teklif" okul uygulaması diye yazılır, Yönetmelik hükmü diye değil |
| E27 | `ExpenseFile`, `LedgerEntry`, `BankAccount`, `BankTransaction` | muhasip | Birlik Başkanı (yokluğunda Başkan Yardımcısı) + Muhasip | TF | Kontrol listesi E25, E26 ve VİF alanlarından dolar; talimatta IBAN tam, iki imza |
| E28 | `OabBudget`, `BudgetLine`, `BudgetCategory`, `OpeningBalance` | muhasip | YK adına Birlik Başkanı + Muhasip (+ asıl üyeler) | TF | "Okul Müdürü" imzası yok; durum "genel kurulda görüşüldü"; satır toplamları tutar |
| E29 | `OabBudget`, `BudgetLine`, `Announcement` | muhasip, sekreter | "Okul-Aile Birliği Yönetim Kurulu" | — | Kişisiz; yalnız kalem toplamları |
| E30 | `LedgerEntry` (dönem toplamları), `Announcement` | muhasip | "Okul-Aile Birliği Yönetim Kurulu" | — | Bağışçı, öğrenci, personel adı yok; dönem sonu bakiye E17'nin kalanıyla aynı |
| E31 | `MonthlyReport`, `LedgerEntry`, `BoardDecision`, `ReceiptLeaf`, `BankTransaction` | muhasip (hazırlar), baskan | Hazırlayan Muhasip; Birlik Başkanı; "Teslim alan: Okul Müdürü" (gelen evrak no) | TF | Ay toplamları E17 ile aynı; şartlı bağış ve arz/pay vadeleri D bölümünde |
| E32 | `AuditReport` (ARA, kontrol listesi), `ComplianceItem`, `LedgerEntry`, `BankTransaction` | denetleme_kurulu | DK asıl 3 üye; "Teslim alan: Birlik Başkanı"; "Görüldü — Okul Müdürü" | — | FR-012'nin 22 kalemi; "adli sicil kayıtları alınmış mı" kalemi yok (S-20); defter = banka = TEFBİS sütunları; aykırılıkta md. 14/5 seçeneği |
| E33 | `AuditReport` (NIHAI), ara raporlar | denetleme_kurulu | DK asıl 3 üye | — | Ara rapor sayısı < 2 ise uyarı; mali özet E34 ile aynı rakamlar |
| E34 | `OabBudget`, `BudgetLine`, `LedgerEntry`, `BoardMeeting`, `MonthlyReport` | muhasip, sekreter | YK asıl 5 üye | TF | Gerçekleşen işlem kayıtlarından (K1); "Okul Müdürü" imzası yok; öğrenci/veli adı yok |
| E35 | `DocumentRecord`, `GeneratedDocument` | mudur | Okul Müdürü | — | RYUE; muhatap Birlik Başkanı; birlik kayıtlarına yazmaz |
| E36 | `LedgerEntry` (etkinlik), `BoardDecision`, `DocumentRecord` (SEK, müdür görüşü, MEM onayı) | muhasip, sekreter | Etkinlik sorumlusu YK üyesi + Muhasip + Birlik Başkanı; "Uygunluk görüşü — Okul Müdürü" | KD | Onay zincirinin üç aşaması tarih/sayılı; net gelir defterle aynı |
| E37 | `Handover`, `ReceiptBookRegistry`, `BankAccount`, `DocumentRecord`, `OpeningBalance` | yonetici, sekreter | Devreden önceki Başkan + önceki Muhasip; Devralan yeni YK adına üye; Divan Başkanı; "Görüldü — Okul Müdürü" | — | Koçanlar seri-cilt-sıra aralığıyla; banka bakiyesi tarihli; program hesaplarının kapanışı satırı |
| E38 | `ComplianceItem`, `GeneratedDocument`, `DocumentRecord` | sekreter, yonetici | Sekreter + Birlik Başkanı; "Kontrol eden — Okul Müdürü" | — | 17 kalemin her biri bir belgeye bağlı; eksik kalem "yok" yazar |
| E39 | `GeneratedDocument`, `OabTerm` | yonetici | — | — | Her belgenin PDF'i + xlsx dökümler + JSON; içerik listesi DAHY EK-2 sütunlarıyla; kapanmış dönemde içerik özeti aynı |
| E40 | `RentableAsset`, `BoardDecision`, okul kartı | sekreter, yonetici | Birlik Başkanı; üst yazı taslağı Okul Müdürü | KD | Muhatap okul müdürlüğü; MEM'e iletim üst yazısı ekte |
| E41 | `OabContract` (mevcut), `BoardDecision`, talep (`DocumentRecord`) | sekreter | Birlik Başkanı | KD | Talepten ≤ 15 gün; ret somut bilgi ve belgeye dayanır (G.2024/35 I-4) |
| E42 | `OabContract`, `Bidder` (kiracı), `RentableAsset`, okul kartı | yonetici, sekreter | Birlik Başkanı + Kiracı + varsa İlgili Esnaf Odası Temsilcisi | — | 25 genel şart korpustaki EK-2 ile karakter karakter aynı (lafız kilidi); boşluklar dolu; YD'li ibare KE-7'ye göre; "Taşımacı" kelimesi yok |
| E43 | `OabContract` (yer teslimi), `RentableAsset` (levazım) | yonetici | Birlik/okul yönetimi yetkilisi + Kiracı | — | İmzadan ≤ 15 gün; levazım çeşit ve değer sütunları |
| E44 | `OabContract`, okul kartı | yonetici (taslak) | Okul Müdürü | — | RYUE; muhatap millî emlak birimi; ek sözleşme örneği |
| E45 | `OabContract`, `IndexRate` | muhasip, sekreter | Birlik Başkanı | — | Oran "TÜFE on iki aylık ortalamalara göre % değişim"; ilk yıl artış yok |
| E46 | `ComplianceItem` (belge türü, tarih, geçerlilik), `DocumentRecord` | yonetici | Birlik Başkanı | — | Adli sicil ve sağlık belgesinde yalnız "teslim alındı" + tarih; 12 aylık yenileme sütunu |
| E47 | `OabContract`, `ComplianceItem` | sekreter | Birlik Başkanı | — | Süre 15 gün; tebliğ tarihi alanı |
| E48 | `Tender` (servis tespiti kaydı), komisyon üyeleri | yonetici | Komisyon Başkanı (Okul Müdürü) | — | "ihale/teklif/eksiltme" yok (§9.4); md. 5/4'ün dört unsuru; ilan ile dosya teslimi arası ≥ 7 gün |
| E49 | `Tender`, komisyon | yonetici | Komisyon başkan ve üyeleri | — | Asma ve indirme tarihi; pano + web satırları |
| E50 | `Tender`, `Bidder` | yonetici | Komisyon üyesi + İstekli | — | Bedelsiz teslim (md. 5/1) |
| E51 | `Tender`, `Bidder` | yonetici | Komisyon üyeleri + İstekli | — | Teslim saati ilandaki saatten önce; "dosyalar geri alınamaz" (md. 7/2) |
| E52 | `Bidder`, belge kontrol alanları | yonetici | Komisyon başkan ve üyeleri | — | md. 6/1'in belgeleri satır satır; eksik belge uyarı, engel değil |
| E53 | `Bidder`, EK-3 puan kayıtları | yonetici | Komisyon başkan ve üyeleri | — | Yalnız itiraz ya da yeni okulda basılır; kademeler EK-3 ile aynı; kriter 4 kısa adla (KE-8) |
| E54 | `Tender` (oylama, karar), `Bidder`, mülki amir onay kaydı | yonetici | Komisyon başkan ve üyeleri; muhalif şerhi; "Mülki idare amiri onayı" alanı | — | Oylama sonucu ve muhalif gerekçesi basılır; karar no "OAB-İhale-…" değil |
| E55 | `OabContract` (servis), `Bidder` (taşımacı), komisyon | yonetici | Komisyon Başkanı (Okul Müdürü) + Taşımacı | — | U-E EK-2 lafzı korpusla aynı (SIC bent harfleri dâhil); "ihaleye fesat karıştırma" dışında yasak kelime yok (KE-9) |
| E56 | `OabContract`, `Bidder` | yonetici | "… Okulu Müdürlüğü" | — | Yalnız taşımacının ad/unvanı ve iş iletişimi; şoför ve veli verisi yok |
| E57 | `Tender`, `Bidder` | yonetici | Komisyon başkan ve üyeleri | — | Üç nedenden hangisi olduğu işaretli; atıf md. 8/7 |
| E58 | `ComplianceItem`, `InspectionRecord`, `OabContract` | yonetici | — (iç izleme) | — | Araç yaşı, şoför ve rehber yaşı, belge süreleri kural paketinden; içerik yok, tarih var |
| E59 | `GeneralAssembly`, `LedgerEntry`, `OpeningBalance`, `ReceiptBookRegistry`, `BankAccount`, okul kartı | yonetici | — | — | Tablo 3 üç yıl: devreden + gelir = toplam; Tablo 4 göstergeleri kayıtlardan evet/hayır |
| E60 | `LedgerEntry`, `TefbisTypeMapping`, `BankTransaction`, TEFBİS Excel içe aktarımı (§8) | yonetici, muhasip | Muhasip + yönetici (iç) | TF | Fark satırları türüne göre: TEFBİS'te yok · defterde yok · tutar farkı |
| E61 | personel modeli (sürüm 2), `LedgerEntry` (ücret, prim) | muhasip | Muhasip + Birlik Başkanı; "Görüldü — Okul Müdürü" (md. 13/4) | — | Yalnız "doğrudan işveren" okulda açılır; izin ve ihbar süreleri kural paketinden |
| E62 | personel modeli (sürüm 2) | muhasip | İşveren adına Birlik Başkanı + işçi | — | Hak edilen, kullanılan, kalan; bölüm ≥ 10 gün |

### 9.7 Programın üretmediği belgeler

| Belge | Neden | Program ne yapar |
|---|---|---|
| Yönetim kurulu karar defteri | El ile yazılır, noter tasdiklidir ([13/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13), [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) | Karar taslağı (E01, E15), "deftere işlendi" işareti, defter sıra no ve sayfa |
| Gelir-gider ve gelen-giden evrak defteri | İl/ilçe MEM tasdiklidir (23/2) | Geçirilecek kayıt dökümü (E17, E23) |
| EK-1 bağış alındı belgesi, gelir/gider makbuzu | Ciltli, seri-cilt-sıra numaralı, mühürlü koçan ([16/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-16); K5) | Koçan envanteri ve yaprak kaydı (E22) |
| TEFBİS kaydı | Okul idaresi girer (23/5; K6) | Liste (E18) ve mutabakat (E60) |
| Kantin muhammen bedel ve ihale komisyonu kararları, ihale ilanı | Valilik/kaymakamlık komisyonlarının ve il/ilçe MEM'in evrakı ([19/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-19), [20/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20); G.2024/35 II-3) | Karar tarih/sayısı ve sonucu kaydedilir; başkan temsilci (E03) |
| Mülki amir onayı (OLUR) | Mülki idare amirinin işlemi | Tarih/sayı kaydı; olmadan kesinleştirme sert engel |
| Öğretmenler kurulu tutanağı (DK öğretmen üyeleri) | Okulun kurul evrakı | Seçim sonucu üyelik kaydına girer |
| Varlık İşlem Fişi | TKYS'de taşınır kayıt yetkilisi düzenler (TMY 16/1, 41/2) | Fiş no ve tarih alanı |
| Banka talimatının elektronik onayı | Bankanın sistemi | Kâğıt talimat (E27); üçüncü onay ayarı |
| Kurtarma anahtarı çıktısı, yedek raporu | Aile iskeletinin evrakı (§4) | Bu katalogda değil |

---

---

## 10. Kural testleri

Kural testleri mevzuat hükmü ile programın davranışı arasındaki bağı sabitler. Yalnız Docker'da koşar (altın kural
7); faz, o fazın kapısındaki kural testleri yeşil olmadan kapanmaz. Veri uydurmadır; OYS testlerindeki gerçek firma
adı ve gerçek evrak örneği taşınmaz (S-21), sızıntı denetimi bu adları da arar.

### 10.1 Düzen

| Kısaltma | Dosya (`backend/apps/oab/tests/kurallar/`) | Kapsam |
|---|---|---|
| `kp` | `test_kural_paketi.py` | Şema, atıf kilidi, tutarlılık, sürüm ve dönem bağı (§6.2-6.3) |
| `gk` | `test_genel_kurul_kurallari.py` | §6.4.1 |
| `yk` | `test_yonetim_kurulu_kurallari.py` | §6.4.2 |
| `dk` | `test_denetleme_kurulu_kurallari.py` | §6.4.3 |
| `tm` | `test_temsilci_kurallari.py` | §6.4.4 |
| `ml` | `test_mali_kurallar.py` | §6.4.5-6.4.6 |
| `pd` | `test_kantin_pay_kurallari.py` | §6.4.7 |
| `kn` | `test_kantin_kurallari.py` | §6.4.8 |
| `sv` | `test_servis_kurallari.py` | §6.4.9 |
| `pr` | `test_personel_kurallari.py` | §6.4.10 |
| `ev` | `test_evrak_kurallari.py` | §9 konum, imza, söz dağarcığı, lafız kilidi |

- **İşaret.** Her kural testi `@pytest.mark.kural("<id>")` taşır; parametreli testte her parametre kendi işaretini
  alır. D6 meta testi (`kp::test_her_kuralin_testi_var`) işaretsiz kuralı ve pakette olmayan işareti kırmızıya çevirir.
- **İki katman.** (1) **Değer ve atıf**: paketteki her kural, giriş fazında `kp::test_atif_kilidi[<id>]` ve
  `kp::test_deger_tablosu[<id>]` parametreli testlerine girer. Değer tablosu test dosyasında korpustan **ayrıca elle**
  yazılır; paket ile karşılaştırılır (çift kayıt). (2) **Davranış**: kuralı kullanan servisin sonucu (`uygun`,
  `uyari`, `sert`) ve gerekçe kaydı; eşikli kurallarda sınırın iki yanı (14/15 gün, 99/100 öğrenci, 10/11/20/21. gün).
- **Uyarı kuralı üç testle sınanır** gerektiğinde: sapma yokken uyarısız · sapma gerekçesiz reddedilir · gerekçeyle
  kaydedilir ve denetim izine kural kimliği + paket revizyonuyla düşer. Sert kural: sapan kayıt hiçbir yoldan
  kaydedilmez (servis ve uç).
- **Köken sütunu.** OYS AYNEN = mantık ve beklenen değer aynen; OYS UYARLA = mantık alınır, değişiklik yazılı; yeni.

### 10.2 Paket testleri (§6.3)

| Test | Denetim | Kapı |
|---|---|---|
| `kp::test_sema_gecerli` · `kp::test_ondalik_dize_kayan_nokta_yok` | D1 | F1c |
| `kp::test_kimlik_bicimi_ve_tekillik` · `kp::test_yururluk_araliklari_cakismaz` · `kp::test_yayimlanmis_kimlik_silinmemis` | D2 | F1c |
| `kp::test_atif_kilidi[<id>]` (her kural) · `kp::test_bozuk_capa_yakalanir` (sahte `madde-99`) · `kp::test_bilgi_dizini_atfi_reddedilir` · `kp::test_draft_dosya_atfi_reddedilir` | D3 | F1c |
| `kp::test_fikra_bent_kilidi[<id>]` · `kp::test_mulga_fikraya_atif_yakalanir` (md. 20/10) · `kp::test_paragraf_bicimli_fikra` (EK-2 md. 7, 4857 md. 17) | D4 | F1c |
| `kp::test_yeter_sayi_tabani_bilesimle_tutarli` · `kp::test_pay_tablolari_toplami_bir` · `kp::test_arz_vadeleri_sirali` · `kp::test_ek3_azami_toplami_25` | D5 | F1c (EK-3 F6) |
| `kp::test_koddaki_kural_cagrilari_pakette` · `kp::test_her_kuralin_testi_var` | D6 | her faz |
| `kp::test_dagitilan_paket_ozeti` · `kp::test_donem_kopyasi_ozeti` | D7 | F1c |
| `kp::test_sabit_taramasi` | D8 (sezgisel) | her faz |
| `kp::test_deger_tablosu[<id>]` | çift kayıt | giriş fazı |
| `kp::test_kapanmis_donem_yeni_revizyonla_ayni_sonuc` · `kp::test_kapanmis_donemde_revizyon_gecisi_sert` · `kp::test_acik_donem_gecisi_fark_listesi_ve_denetim_izi` · `kp::test_eski_degerli_olay_eski_degerle_hesaplanir` | §6.2 dönem bağı (sentetik `r2` test paketiyle) | F1c |
| `kp::test_paket_yuklenemezse_yazma_kapali_okuma_acik` | D1 başarısızlığı (fail-closed) | F1c |

### 10.3 Hüküm → test eşlemesi

Kapı: davranış testinin yeşil olması gereken faz (değer ve atıf testleri giriş fazındadır, §6.4).

**Genel kurul**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `genel_kurul.olagan_son_ay` | `gk::test_olagan_gk_31_ekim_uyarisiz_1_kasim_uyari` | yeni | F2 |
| `genel_kurul.yeni_okul_ay` | `gk::test_yeni_okul_gk_acilistan_2_ay` · `gk::test_yeni_okul_cagrisi_mudur_rolunde` | yeni | F2 |
| `genel_kurul.ilan_en_az_gun` | `gk::test_ilan_15_gun_uyarisiz` · `gk::test_ilan_13_gun_gerekcesiz_reddedilir` · `gk::test_ilan_13_gun_gerekceyle_gecer` · `gk::test_ilan_sinir_14_uyari_15_uyarisiz` | OYS AYNEN (3) + yeni | F2 |
| `genel_kurul.ilan_kanallari` | `gk::test_uc_kanal_kaniti_eksikse_uyari` | yeni | F2 |
| `genel_kurul.yeter_sayi_taban` | `gk::test_taban_uyelik_kayitlarindan_bagimsiz_16` (eksik kadroyla da 64/32) | yeni (S-1) | F1c |
| `genel_kurul.yeter_sayi_carpan` | `gk::test_yeter_sayi_mevcut_100_ve_ustu_64` · `gk::test_olaganustu_gk_yeter_sayi_64` | OYS UYARLA + yeni (S-2) | F1c |
| `genel_kurul.kucuk_okul_carpan` | `gk::test_yeter_sayi_mevcut_99_32` | OYS UYARLA | F1c |
| `genel_kurul.kucuk_okul_esik` | `gk::test_esik_99_ve_100` · `gk::test_mevcut_gk_kaydina_anlik_yazilir` | yeni | F1c |
| `genel_kurul.ikinci_toplanti_en_gec_gun` | `gk::test_ikinci_toplanti_baglantisi` · `gk::test_ikinci_toplanti_30_gun_uyarisiz_31_uyari` | OYS UYARLA + yeni | F2 |
| `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | `gk::test_ikinci_toplanti_cogunluksuz` · `gk::test_olaganustu_ikinci_toplanti_cogunluksuz` (A-1) | OYS AYNEN + yeni | F2 |
| `genel_kurul.karar_cogunlugu` | `gk::test_karar_katilanlarin_cogunluguyla` | yeni | F2 |
| `genel_kurul.gundem_degisikligi` | `gk::test_gundem_degisikligi_oy_coklugu` | yeni | F2 |
| `genel_kurul.olaganustu_cagiranlar` | `gk::test_olaganustu_cagiran_listede` · `gk::test_dk_uygunsuz_bulgu_usulsuzluk_isareti` · `gk::test_dk_tumu_uygun_usulsuzluk_yok` | OYS AYNEN (2) + yeni | F2 |
| `genel_kurul.olaganustu_basvuru_oran` | `gk::test_yuzde_10_alti_basvuru_uyari` | yeni | F2 |
| `genel_kurul.olaganustu_gundeme_baglilik` | `gk::test_olaganustu_gundem_disi_madde_uyari` | yeni | F2 |
| `genel_kurul.divan_uye_turleri` | `gk::test_divana_ogretmen_secilirse_uyari` | yeni | F2 |
| `genel_kurul.secim_bicimi` | `gk::test_dk_ogretmen_koltugu_gk_oylamasina_girmez` | yeni (S-9) | F2 |

**Yönetim kurulu ve ortak üyelik**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `yonetim_kurulu.asil_uye` | `yk::test_yk_eksik_kadro_uyari` · `yk::test_yk_tam_kadro_uyarisiz` · `yk::test_dusen_koltuk_sayima_girmez` | OYS AYNEN (3) | F1c |
| `yonetim_kurulu.yedek_uye` | `yk::test_yk_eksik_kadro_uyari[yedek]` | OYS AYNEN (parametre) | F1c |
| `yonetim_kurulu.uye_turleri` | `yk::test_yk_ye_ogretmen_ve_yonetici_eklenemez` · `yk::test_yk_ye_kursiyer_ve_hayirsever_eklenebilir` | yeni (F1 kapısı) | F1c |
| `yonetim_kurulu.okul_muduru_uye_olamaz` | `yk::test_veli_olan_okul_muduru_yk_ye_eklenemez` | yeni (F1 kapısı) | F1c |
| `yonetim_kurulu.gorev_suresi_yil` | `yk::test_gorev_suresi_bitiminde_uyari` | yeni | F1c |
| `yonetim_kurulu.gorev_bolumu_gun` | `yk::test_gorev_bolumu_7_gun_uyarisiz_8_gun_uyari` · `yk::test_yedek_cagrisindan_sonra_7_gun` | yeni | F1c |
| `yonetim_kurulu.gorevler` | `yk::test_ikinci_baskan_kaydedilemez` | yeni | F1c |
| `yonetim_kurulu.secilme_siniri` | `yk::test_baskan_besinci_secim_gerekcesiz_reddedilir` · `yk::test_baskan_besinci_secim_gerekceyle_gecer` · `yk::test_uye_besinci_secimde_uyari` · `yk::test_gecmis_eksikse_engel_yok` · `yk::test_donem_siniri_ucu_gerekce` | OYS UYARLA (3) + yeni (S-4) | F1c |
| `yonetim_kurulu.tek_birlik` | `yk::test_tek_birlik_beyani_yoksa_uyari` | yeni | F1c |
| `uyelik.suc_engeli_beyani` | `yk::test_beyan_yalniz_isaret_ve_tarih` | OYS UYARLA (not alanı kalkar) | F1c |
| `uyelik.ayrilan_veli_devam` | `yk::test_yk_4_altina_duserse_ayrilan_veli_devam_onerisi` · `yk::test_dusurme_gerekcesiz_reddedilir` · `yk::test_dusme_gerekcesi_kaydi` | yeni + OYS AYNEN (2) | F1c |
| `yonetim_kurulu.yedek_cagirma` | `yk::test_yedek_oy_sirasi_alani` · `yk::test_yedek_oy_sirasiyla_cagrilir` · `yk::test_sira_disi_cagri_gerekce_ister` | OYS AYNEN + yeni (F1 kapısı) | F1c |
| `yonetim_kurulu.toplanti_yeter_sayi` | `yk::test_3_katilimla_karar_girilemez` | yeni | F3 |
| `yonetim_kurulu.karar_yeter_sayi` | `yk::test_2_kabul_oyuyla_karar_alinmadi` | yeni | F3 |
| `yonetim_kurulu.toplanti_sikligi` | `yk::test_toplantisiz_ders_ayi_uyari_yaz_ayi_uyarisiz` | yeni | F3 |
| `yonetim_kurulu.devamsizlik_siniri` | `yk::test_ust_uste_3_ozursuz_dusme_onerisi` · `yk::test_ozurlu_devamsizlik_saymaz` · `yk::test_araya_katilim_seriyi_bozar` · `yk::test_katilim_ucu_ucuncu_ozursuzde_oneri` · `yk::test_kayitsiz_toplanti_eksik_veri_uyarisi` · `yk::test_dk_de_dusme_yok` | OYS UYARLA (4) + yeni (S-19) + OYS AYNEN | F3 |
| `yonetim_kurulu.olaganustu_cagri_ay` | `yk::test_yedeklerle_3_altina_dusunce_1_ay_uyarisi` | yeni | F3 |

**Denetleme Kurulu ve temsilciler**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `denetleme_kurulu.asil_uye` | `dk::test_dk_eksik_kadro_uyari[asil]` | yeni | F1c |
| `denetleme_kurulu.yedek_uye` | `dk::test_dk_eksik_kadro_uyari[yedek]` | yeni | F1c |
| `denetleme_kurulu.koltuklar` | `dk::test_veli_ogretmen_ayrimi` · `dk::test_veli_koltuguna_hayirsever_giremez` · `dk::test_baska_okul_ogretmeni_onay_no_ister` | OYS UYARLA + yeni (F1 kapısı) | F1c |
| `denetleme_kurulu.gorev_bolumu_gun` | `dk::test_dk_gorev_bolumu_7_gun` | yeni | F1c |
| `denetleme_kurulu.gorev_suresi_yil` | `dk::test_dk_gorev_suresi_bitiminde_uyari` | yeni | F1c |
| `denetleme_kurulu.baskan_secilme_siniri` | `dk::test_dk_baskan_siniri_farkli_organi_etkilemez` · `dk::test_dk_baskani_dorduncu_secimde_uyari` | OYS AYNEN + yeni | F1c |
| `denetleme_kurulu.inceleme_yilda_en_az` | `dk::test_tek_ara_raporla_donem_sonu_uyari` | yeni | F4 |
| `denetleme_kurulu.yk_uyesi_olamaz` | `dk::test_yk_uyesi_dk_ye_eklenemez` · `dk::test_dk_uyesi_yk_ye_eklenemez` | OYS UYARLA (sonuç tersine) | F1c |
| `denetleme_kurulu.ogretmen_gorevlendirme_ay` | `dk::test_4_aydan_uzun_gorevlendirmede_yedek_onerisi` | yeni | F1c |
| `temsilci.*` (9 kural) | `tm::test_kademeye_gore_temsilci_satirlari[<id>]` (her kural bir parametre: kademe koşulu, sayı, yedek) · `tm::test_baskan_kendiliginden_uye[tasimaci_tespit, muhammen_bedel, kiralama_ihale]` · `tm::test_kampus_kosulu_yoksa_satir_yok` | yeni | F1c |

**Gelir, bağış, makbuz, etkinlik, harcama, bildirim**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `bagis.elden_yatirma_is_gunu` | `ml::test_cuma_kabul_sonraki_cuma_besinci_is_gunu` · `ml::test_resmi_tatil_is_gunu_sayilmaz` | yeni | F3 |
| `bagis.kayit_doneminde_toplanmaz` | `ml::test_kayit_doneminde_bagis_uyari` | yeni | F3 |
| `gelir.proje_protokol_ucret_yasak` | `ml::test_proje_kapsaminda_ucret_uyari` | yeni | F3 |
| `bagis.sartli_amac` | `ml::test_sartli_alt_hesap_eksiye_dusemez` · `ml::test_amaca_baglanmayan_gider_kaydedilmez` | yeni | F3 |
| `bagis.ayni_teslim` | `ml::test_ayni_bagista_vif_yoksa_uyari` | yeni | F3 |
| `makbuz.cilt_yaprak` | `ml::test_cilt_50_disi_yaprak_uyari` | yeni | F3 |
| `makbuz.seri_cilt_sira_tekil` | `ml::test_ayni_yaprak_iki_kez_kullanilamaz` · `ml::test_iptal_yaprak_yeniden_kullanilamaz` | yeni | F3 |
| `makbuz.muhur_ve_karar_kaydi` | `ml::test_muhursuz_cilt_kullanima_acilirken_uyari` | yeni | F3 |
| `etkinlik.onay_zinciri` | `ml::test_mem_onayi_yoksa_etkinlik_geliri_uyari` | yeni | F4 |
| `etkinlik.ders_saatleri_disinda` | `ml::test_ders_saatinde_etkinlik_uyari` | yeni | F4 |
| `harcama.yk_karari` | `ml::test_kararsiz_harcama_uyari` · `ml::test_genel_karar_gerekce_sayilir` | yeni (saha.md 6) | F4 |
| `harcama.okul_yazili_talep` | `ml::test_talepsiz_harcama_uyari` | yeni | F4 |
| `harcama.alim_komisyonu_en_az` | `ml::test_iki_kisilik_komisyon_uyari` | yeni | F4 |
| `harcama.alim_komisyonu_uyeleri` | `ml::test_komisyonda_beyansiz_uye_uyari` | yeni | F4 |
| `harcama.musterek_imza` | `ml::test_tek_imzali_odeme_uyari` · `ml::test_baskan_yokken_baskan_yardimcisi` | yeni | F4 |
| `harcama.tasinir_kaydi` | `ml::test_tasinir_aliminda_vif_yoksa_uyari` | yeni | F4 |
| `harcama.organ_uyesine_odeme` | `ml::test_yk_uyesine_odeme_uyari` | yeni | F4 |
| `bildirim.aylik_mudur` | `ml::test_ay_bitti_bildirim_yok_uyari` | yeni | F4 |
| `duyuru.butce` | `ml::test_butce_duyuru_kaniti_yoksa_uyari` | yeni | F4 |
| `duyuru.gelir_gider_donemlik` | `ml::test_donemde_duyuru_yoksa_uyari` | yeni | F4 |
| `vergi.damga_harc_muafiyeti` | `ml::test_birlik_kagidinda_damga_hesaplanmaz` | yeni | F4 |
| `denetim.mem_yilda_en_az` | `ml::test_yil_icinde_mem_denetimi_yoksa_pano_uyarisi` | yeni | F4 |

**Kantin: arz, pay, kira**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `arz_bedeli.kira_oran` | `pd::test_kiraya_verme_yuzde_3_ve_dagitim` | OYS AYNEN | F3 |
| `arz_bedeli.isletme_oran` | `pd::test_isletme_yuzde_1_ve_gider_dususu` | OYS AYNEN | F5 |
| `arz_bedeli.donem_ay` | `pd::test_ceyrekler_takvim_ceyregi` · `pd::test_pesin_odeme_secenegi` | OYS UYARLA (KE-2) | F3 |
| `arz_bedeli.sozlesme_vade_gunu` | `pd::test_vade_10_uyarisiz_11_sozlesme_vadesi_gecti` | OYS UYARLA | F3 |
| `arz_bedeli.yonetmelik_vade_gunu` | `pd::test_vade_20_tek_uyari_21_iki_uyari` · `pd::test_vade_tatilde_kaymaz` (KE-18) | OYS UYARLA + yeni | F3 |
| `arz_bedeli.takip_sorumlulari` | `ev::test_e24_mudur_ve_baskan_imzasi` | yeni | F3 |
| `arz_bedeli.diger_tahsilat_oran` | `pd::test_tahliye_cezasinda_yuzde_3_arz` | yeni | F5 |
| `pay_dagitimi.genel` | `pd::test_dagitim_80_10_10` · `pd::test_kurus_artigi_toplam_korunur` (KE-3) | OYS AYNEN + yeni | F3 |
| `pay_dagitimi.il_merkezi` | `pd::test_buyuksehir_olmayan_il_merkezi_ilce_0_il_20` · `pd::test_buyuksehir_olmayan_ilin_ilcesi_80_10_10` | OYS UYARLA (S-17) + yeni | F3 |
| `pay_dagitimi.isletme_net_tabani` | `pd::test_isletmede_giderler_dusulur` | OYS AYNEN (aynı test) | F5 |
| `kira.odeme_gunleri` | `pd::test_kira_16sinda_uyari` | yeni | F3 |
| `kira.yariyil_ayi_carpani` | `pd::test_yariyil_ayi_yarim_kira` | yeni | F3 |
| `kira.ay_sayisi` | `pd::test_9_aylik_sozlesmede_yaz_kirasi_yok` · `pd::test_12_aylik_tam_yil` | yeni | F3 |
| `kira.mucbir_sebep_indirimi` | `pd::test_mucbir_indirim_gerekceyle` | yeni | F5 |
| `kira.ust_uste_odememe_fesih` | `pd::test_iki_ay_odenmezse_fesih_onerisi` | yeni | F5 |
| `kantin.kdv_istisnasi` | `pd::test_kira_tahsilatinda_kdv_yok` | yeni | F3 |

**Kantin: kiralama, sözleşme, belgeler**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `kantin.kiralama_usulu` | `kn::test_kiralama_pazarlik_ve_alan_uyarisi` · `kn::test_pazarlikta_en_yuksek_bedel` | OYS AYNEN (2) | F5 |
| `kantin.istekli_belge_sarti` | `kn::test_belgesi_eksik_istekli_gerekceyle_gecer` | OYS UYARLA (sert → uyarı) | F5 |
| `kantin.esnaf_odasi_belgesi` | `kn::test_esnaf_odasi_belgesi_yoksa_uyari` | yeni | F5 |
| `kantin.hisimlik_derecesi` | `kn::test_kiralama_hisimlik_engeli` · `kn::test_serviste_hisimlik_kurali_yok` | OYS AYNEN + UYARLA | F5 |
| `kantin.istekli_suc_engeli` | `kn::test_suc_engeli_sert_atif_20_11` | OYS UYARLA (atıf) | F5 |
| `kantin.calisan_niteligi` | `kn::test_portor_ve_adli_sicil_istekliden_istenmez` | yeni (S-8) | F5 |
| `kantin.yillik_yenileme` | `kn::test_faaliyet_belgesi_12_ayi_asinca_uyari` | yeni | F5 |
| `kantin.calisan_hijyen_belgesi` | `kn::test_hijyen_belgesiz_calisan_uyari` | yeni | F5 |
| `kantin.kisa_sureli_bedel_birimi` | `kn::test_kisa_sureli_bedel_birimleri` | yeni | F5 |
| `kantin.isletmede_vergi_uyarisi` | `kn::test_birlikce_isletme_secilince_vuk_uyarisi` | yeni | F1c |
| `kira.sozlesme_en_fazla_yil` | `kn::test_5_yil_artik_yilda_dogru` · `kn::test_5_yil_1_gun_uyari` | yeni (S-18) | F5 |
| `kira.toplam_en_fazla_yil` | `kn::test_20_yil_sozlesme_zincirinden` | yeni | F5 |
| `kira.yirmi_yil_taban_tarihi` | `kn::test_2005_oncesi_ilk_sozlesme_31_05_2005ten` | yeni | F5 |
| `kira.yirmi_yil_yeniden_baslangic` | `kn::test_ilanli_pazarlik_yeni_baslangic` · `kn::test_teklif_kabul_yenilemesi_baslatmaz` | yeni | F5 |
| `kira.yirmi_yil_ilave` | `kn::test_540_gun_ve_dondurulan_sure_eklenir` | yeni | F5 |
| `kira.yer_teslimi_gun` | `kn::test_yer_teslimi_16_gunde_uyari` · `kn::test_imzasiz_sozlesmede_teslim_uyari` | yeni | F5 |
| `kira.tufe_artisi` | `kn::test_ilk_yil_artis_yok` · `kn::test_ikinci_yil_tufe_uygular` · `kn::test_tufe_servis_icin_yok` | OYS UYARLA (2) + AYNEN | F5 |
| `kira.ogrenci_degisim_esigi` | `kn::test_mevcut_yuzde_25_degisince_oneri` | yeni | F5 |
| `kira.kesin_teminat_oran` | `kn::test_teminat_yillik_kiranin_yuzde_6` | yeni | F5 |
| `kira.tahliye_gunluk_ceza_oran` | `kn::test_tahliye_cezasi_gunluk_yuzde_3` | yeni | F5 |
| `kira.fesih_ihtar_gun` | `kn::test_ihtar_suresi_15_gun` | yeni | F5 |
| `kira.yeniden_kiralama_bildirim_ay`, `yeniden_kiralama_cevap_gun`, `muhammen_bedel_teklif_ay`, `tufe_bildirimi`, `milli_emlak_ornegi` | `kn::test_kiralama_takvim_uyarilari[<id>]` (bitişe 2 ay / cevap 15 gün / bitişe 1 ay / artıştan sonra MEM bildirimi / millî emlak gönderimi; süre dolunca uyarı) | yeni | F5 |
| `kira.ihaleden_yasaklama_yil` | `kn::test_yasakli_istekli_uyari` | yeni | F5 |

**Servis**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `servis.ilan_en_az_gun` | `sv::test_ilan_7_gun_uyarisiz_6_gun_uyari` | yeni | F6 |
| `servis.ilan_kanallari` | `sv::test_ilan_tutanaginda_iki_kanal` | yeni | F6 |
| `servis.komisyon_bilesimi` | `sv::test_komisyon_uygun_gerekce_istemez` · `sv::test_komisyon_baskan_sapmasi_gerekce_ister` · `sv::test_yedekler_sayilir` | OYS AYNEN (2) + yeni | F6 |
| `servis.komisyon_karari` | `sv::test_cekimser_oy_kaydedilemez` · `sv::test_esitlikte_baskanin_tarafi` · `sv::test_muhalif_serhi_zorunlu` | yeni (S-7) | F6 |
| `servis.degerlendirme_yontemi` | `sv::test_varsayilan_komisyon_degerlendirmesi` · `sv::test_itirazda_ek3_en_yuksek_puan` · `sv::test_ek3_esitlikte_gerekce` | OYS UYARLA (3) | F6 |
| `servis.ek3_puanlama` | `sv::test_ek3_tohumu_ve_25_tavan` · `sv::test_tam_puan_25` · `sv::test_ikili_kriter_yalniz_0_ya_da_azami` · `sv::test_ornek_istekli_23_puan` (uydurma) | OYS AYNEN (3) + UYARLA | F6 |
| `servis.ek3_kriter_azami_puan` | `sv::test_azamiyi_asan_puan_uyari` | OYS UYARLA (sert → uyarı) | F6 |
| `servis.olur_olmadan_kesinlesmez` | `sv::test_olursuz_kesinlestirme_sert` · `sv::test_onay_kesinlestirme_akisi` · `sv::test_ret_tespiti_iptal_eder` · `sv::test_kesinlestirme_ucu_olursuz_400` | OYS AYNEN (2) + UYARLA (2) | F6 |
| `servis.mulki_amir_onay_is_gunu` | `sv::test_onay_5_is_gunu_bekleme_sayaci` | yeni | F6 |
| `servis.teblig_is_gunu` | `sv::test_teblig_5_is_gunu` | yeni | F6 |
| `servis.sozlesme_imza_gun` | `sv::test_tebligden_10_gun_icinde_imza` | yeni | F6 |
| `servis.sozlesme_en_fazla_yil` | `sv::test_servis_suresi_3_yil_ustu_uyari` · `sv::test_sure_disi_ucu_gerekce_ister` | OYS UYARLA (2) | F6 |
| `servis.yeniden_cikma` | `sv::test_basvuru_yoksa_yeniden_cikma` | yeni | F6 |
| `servis.ucret_tarifesi` | `sv::test_servis_muhammen_bedel_sert` · `sv::test_kiralama_muhammen_bedel_yazilir` · `sv::test_servis_bedel_ucu_400` | OYS AYNEN (2) + UYARLA | F6 |
| `servis.taksit_en_fazla` | `sv::test_10_taksit_uyari` · `sv::test_taksit_ucu_uyari_doner` | OYS UYARLA (2) | F6 |
| `servis.yariyil_ucret_yok` | `sv::test_sozlesme_metninde_yariyil_ucreti_yok` | OYS UYARLA (KE-14) | F6 |
| `servis.muhtac_ogrenci` | `sv::test_muhtac_ogrenci_sozlesmede` | yeni | F6 |
| `servis.tasimaci_ilani` | `sv::test_tasimaci_ilani_yalniz_unvan_ve_is_iletisimi` | yeni | F6 |
| `servis.arac_yasi_en_fazla`, `sofor_yasi`, `sofor_belge_yili`, `sofor_psikoteknik_yil`, `saglik_raporu_ay`, `rehber_yasi` | `sv::test_belge_ve_yas_sinirlari[<id>]` (her kural bir parametre; sınırın iki yanı: araç 12/13, şoför 66. yaş günü, D sınıfı 2 yıl, psikoteknik 5 yıl, rapor 12 ay, rehber 21/22 yaş) | yeni | F6 |

**Personel (sürüm 2)**

| Kural | Davranış testi | Köken | Kapı |
|---|---|---|---|
| `personel.sgk_saklama_yil` | `pr::test_sgk_belgesi_10_yil_silinemez` · `pr::test_sure_izleyen_yil_basindan` | yeni | F8 |
| `personel.karsilik_ayrilir` | `pr::test_karsilik_yoksa_uyari` | yeni | F8 |
| `personel.yillik_izin_gun` | `pr::test_izin_14_20_26_basamaklari` | yeni | F8 |
| `personel.izin_bolumu_en_az_gun` | `pr::test_9_gunluk_bolum_uyari` | yeni | F8 |
| `personel.ihbar_hafta` | `pr::test_ihbar_suresi_basamaklari` | yeni | F8 |

**Kural olmayan, test edilen kararlar** (DOĞRULANMADI listesinin davranışı): `pd::test_gecikme_zammi_hesaplanmaz_bilgi_notu` (3) · `pd::test_kurus_artigi_toplam_korunur` (4) ·
`kn::test_serviste_hisimlik_kurali_yok` (6) ·
`ml::test_saklama_suresi_yok_silme_yok` (9).

### 10.4 OYS'nin 71 kural testi

Sınıf, envanter §6.1-6.2'deki sınıflamanın plan §1.8 kararlarıyla güncellenmiş hâlidir: **AYNEN 31 · UYARLA 38 · ALMA 2**.
Envanterden sapmalar: üç devamsızlık testi (S-19, otomatik düşme yerine öneri), belge eksikliği, taksit ve puan
sınırı testleri (plan §1.8: sert → uyarı) ve iki puanlama testi (S-7: yalnız itiraz/yeni okul kipi) UYARLA'ya geçti.

| OYS testi (dosya :: ad) | Adet | Sınıf | OAB Defteri'nde | Değişiklik |
|---|---|---|---|---|
| `test_assembly` :: `quorum_100_ustu_ogrenci`, `quorum_100_alti_ogrenci` | 2 | UYARLA | `genel_kurul.yeter_sayi_*` | Kurulum tam kadrosuz; taban sabit 16 |
| `test_assembly` :: `quorum_ikinci_toplanti_cogunluksuz` | 1 | AYNEN | `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` | — |
| `test_assembly` :: `yeterli_ilan_suresi_uyarisiz`, `13_gun_gerekcesiz_reddedilir`, `13_gun_gerekceyle_gecer` | 3 | AYNEN | `genel_kurul.ilan_en_az_gun` | Sınır testi (14/15) ayrıca yeni |
| `test_assembly` :: `ikinci_toplanti_baglantisi` | 1 | UYARLA | `genel_kurul.ikinci_toplanti_en_gec_gun` | 30 gün denetimi eklenir |
| `test_assembly_write` :: `13_gun_gerekcesiz_400`, `13_gun_gerekceyle_201` | 2 | UYARLA | `genel_kurul.ilan_en_az_gun` (uç) | K2 rolleri, aile uç katmanı |
| `test_audit` :: `uygunsuz_madde_usulsuzluk_bayragi_kaldirir`, `tumu_uygun_usulsuzluk_yok` | 2 | AYNEN | `genel_kurul.olaganustu_cagiranlar` (14/5 yolu) | — |
| `test_audit_write` :: `update_uygunsuz_bulgu_irregularity_true`, `update_hepsi_uygun_irregularity_false` | 2 | UYARLA | aynı (uç) | DK hesabından yazma (K2) |
| `test_bidder` :: `suc_engeli_sert` | 1 | UYARLA | `kantin.istekli_suc_engeli` | Atıf 12/5 → 20/11 |
| `test_bidder` :: `kiralama_hisimlik_engeli` | 1 | AYNEN | `kantin.hisimlik_derecesi` | — |
| `test_bidder` :: `servis_hisimlik_engeli_uygulanmaz` | 1 | UYARLA | kural yok (DOĞRULANMADI-6) | Gerekçe "pakette servis hısımlık kuralı yok" |
| `test_bidder` :: `kiralama_belge_eksik_engeli` | 1 | UYARLA | `kantin.istekli_belge_sarti` | Sert → uyarı; md. 20/5 ayrı kural |
| `test_bidder` :: `puanlama_kazanan_en_yuksek`, `puanlama_esitlik_gerekce_ister` | 2 | UYARLA | `servis.degerlendirme_yontemi` | Yalnız itiraz/yeni okul kipinde |
| `test_bidder` :: `pazarlik_kazanan_en_yuksek_teklif` | 1 | AYNEN | `kantin.kiralama_usulu` | — |
| `test_bidder` :: `en_dusuk_teklif_kazanan` | 1 | ALMA | — | Yürürlükten kalkan 10.01.2018 metni |
| `test_board` :: `ust_uste_3_mazeretsiz_devamsizlik_dusurur`, `mazeretli_devamsizlik_dusurmez`, `araya_bir_katilim_girerse_seri_bozulur` | 3 | UYARLA | `yonetim_kurulu.devamsizlik_siniri` | Öneri üretir; sayım toplantılar üzerinden |
| `test_board` :: `dk_toplantisinda_otomatik_dusme_yok` | 1 | AYNEN | `yonetim_kurulu.devamsizlik_siniri` | — |
| `test_board` :: `record_board_decision_taslak_varsayilan` | 1 | AYNEN | konum KD (`ev`) | — |
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
| `test_models` :: `membership_uygunluk_beyani_alanlari` | 1 | UYARLA | `uyelik.suc_engeli_beyani` | Şifreli not alanı kalkar (KVKK) |
| `test_models` :: `membership_ayni_kisi_farkli_organda_serbesttir` | 1 | UYARLA | `denetleme_kurulu.yk_uyesi_olamaz` | Beklenen sonuç tersine döner (kullanıcı kararı, §15 A-2) |
| `test_scoring` :: `ek3_seed_idempotent_ve_maks_25`, `tam_puan_25`, `ikili_kriter_yalniz_0_veya_max` | 3 | AYNEN | `servis.ek3_puanlama` | Tohum paketten |
| `test_scoring` :: `puan_azamiyi_asamaz_sert_engel` | 1 | UYARLA | `servis.ek3_kriter_azami_puan` | Sert → uyarı |
| `test_scoring` :: gerçek evrak örneği (23 puan) | 1 | UYARLA | `servis.ek3_puanlama` | Gerçek firma adı ve veri → uydurma (S-21) |
| `test_share` :: `kiraya_verme_yuzde_3_ve_dagitim` | 1 | AYNEN | `arz_bedeli.kira_oran`, `pay_dagitimi.genel` | — |
| `test_share` :: `isletme_yuzde_1_ve_gider_dususu` | 1 | AYNEN | `arz_bedeli.isletme_oran`, `pay_dagitimi.isletme_net_tabani` | — |
| `test_share` :: `non_metropolitan_ilce_yok_il_yirmi` | 1 | UYARLA | `pay_dagitimi.il_merkezi` | Okul kartının üçlü yerleşim türü |
| `test_share` :: `due_date_ceyrekten_turer` | 1 | UYARLA | `arz_bedeli.sozlesme_vade_gunu`, `yonetmelik_vade_gunu` | İki vade, iki uyarı |
| `test_share` :: `gecikme_zammi` | 1 | ALMA | — | 6183 korpusta yok; yerine "hesaplanmaz" testi |
| `test_tender` :: `create_tender_servis_varsayilan_puanlama` | 1 | UYARLA | `servis.degerlendirme_yontemi` | Varsayılan komisyon değerlendirmesi |
| `test_tender` :: `create_tender_kiralama_pazarlik_ve_alan_uyarisi` | 1 | AYNEN | `kantin.kiralama_usulu` | — |
| `test_tender` :: `servis_muhammen_bedel_sert_engel`, `kiralama_muhammen_bedel_yazilir` | 2 | AYNEN | `servis.ucret_tarifesi` | — |
| `test_tender` :: `servis_komisyon_uygun_gerekce_gerektirmez`, `servis_komisyon_baskan_sapmasi_uyari_gerekce` | 2 | AYNEN | `servis.komisyon_bilesimi` | — |
| `test_tender` :: `finalize_onaysiz_sert_engel`, `onay_kesinlestirme_akisi` | 2 | AYNEN | `servis.olur_olmadan_kesinlesmez` | — |
| `test_tender` :: `red_ihaleyi_iptal_eder` | 1 | UYARLA | `servis.olur_olmadan_kesinlesmez` | Test adında "ihale" → "tespit" |
| `test_tender_decision_write` :: `finalize_olursuz_sert_engel_400` | 1 | UYARLA | aynı (uç) | Uç katmanı |
| `test_tender_write` :: `estimated_price_servis_400`, `create_tender_kiralama_alansiz_gerekce_ister_400` | 2 | UYARLA | `servis.ucret_tarifesi`; değişmez (alan) | Uç katmanı |
| `test_tufe` :: `ilk_yil_artis_yok`, `ikinci_yil_tufe_uygular` | 2 | UYARLA | `kira.tufe_artisi` | `IndexRate.value` anlamı sabitlenir |
| `test_tufe` :: `tufe_servis_sert_engel` | 1 | AYNEN | `kira.tufe_artisi` | — |

### 10.5 Evrak kuralı testleri (§9)

| Test | Neyi sabitler | Kapı |
|---|---|---|
| `ev::test_konum_kd[<kod>]` · `ev::test_konum_tf[<kod>]` · `ev::test_konum_df[<kod>]` | §9.2 tablosundaki her belgede doğru konum cümlesi; başka belgede yok | belgenin fazı |
| `ev::test_karar_taslagi_varsayilan` | Karar "taslak" doğar, "deftere işlendi" işareti defter sıra no ve sayfa ister (OYS AYNEN) | F1c |
| `ev::test_yk_ve_gk_belgelerinde_mudur_yazar_degil` | E05 (yeni okul hariç), E10, E28, E34'te "Okul Müdürü" yalnız "Görüldü" blokunda; E28 ve E34'te hiç yok | F2, F4 |
| `ev::test_imza_ad_soyad_bicimi` | Ad ilk harf büyük, SOYAD `tr_upper` (RYUE md. 17/2), "İ/ı" doğru | F1c |
| `ev::test_servis_evraki_soz_dagarcigi` | E48-E58'de `ihale`, `teklif`, `eksiltme` kökü yok (TR katlamalı); tek istisna "ihaleye fesat karıştırma" (KE-9) | F6 |
| `ev::test_duyurularda_kisi_adi_yok` | E06, E29, E30 çıktısında hiçbir `OabPerson` ve `ParentRoster` adı yok; E56'da yalnız taşımacı unvanı | F2, F4, F6 |
| `ev::test_tckn_hicbir_belgede_yok` | K9 kapalıyken bütün belgelerde 11 haneli kimlik deseni yok; açıkken yalnız E20'de maskeli | her faz |
| `ev::test_ek2_lafiz_kilidi` · `ev::test_servis_ek2_lafiz_kilidi` | E42 ve E55 metni korpus dosyasıyla karakter karakter aynı (boşluk alanları hariç) | F5, F6 |
| `ev::test_docx_pdf_icerik_esdegerligi[<kod>]` | python-docx metni ↔ pypdf metni aynı; `w:caps` yok | belgenin fazı |
| `ev::test_sayfa_butcesi[<kod>]` | Gerçek uzunlukta uydurma veriyle sayfa sayısı sınırı | belgenin fazı |
| `ev::test_kapanmis_donem_yeniden_basim_ozeti_ayni` | `GeneratedDocument` içerik özeti yeniden basımda aynı | F4 |
| `ev::test_ilk_uc_evrak_pilot_esdegerligi` | E01-E03, pilot okulun aynı belgeleriyle (uydurma adlarla) bölüm ve alan eşdeğerliği | F1c |

### 10.6 F1 kapısı

Plan §2.4'ün kural, organ ve evrak maddeleri bu testlerle karşılanır (aile güvenlik ve rol testleri §4'te):

| Plan §2.4 maddesi | Test(ler) | Kural |
|---|---|---|
| Her kuralın `madde`'si korpusta çapa olarak var (atıf kilidi) | `kp::test_atif_kilidi[*]` · `kp::test_fikra_bent_kilidi[*]` · `kp::test_bozuk_capa_yakalanir` · `kp::test_mulga_fikraya_atif_yakalanir` · `kp::test_her_kuralin_testi_var` | `r1`'deki 49 kural |
| Yeter sayı: mevcut ≥ 100 → 64, < 100 → 32 (5+5+3+3 için) | `gk::test_yeter_sayi_mevcut_100_ve_ustu_64` · `gk::test_yeter_sayi_mevcut_99_32` · `gk::test_esik_99_ve_100` · `gk::test_taban_uyelik_kayitlarindan_bagimsiz_16` · `kp::test_yeter_sayi_tabani_bilesimle_tutarli` | `genel_kurul.yeter_sayi_*`, `kucuk_okul_*` |
| Dönem sınırı sayacı | `yk::test_baskan_besinci_secim_gerekcesiz_reddedilir` · `yk::test_uye_besinci_secimde_uyari` · `yk::test_gecmis_eksikse_engel_yok` · `dk::test_dk_baskani_dorduncu_secimde_uyari` · `dk::test_dk_baskan_siniri_farkli_organi_etkilemez` | `yonetim_kurulu.secilme_siniri`, `denetleme_kurulu.baskan_secilme_siniri` |
| Kural sürümü değişince kapanmış dönemin hesabı değişmez | `kp::test_kapanmis_donem_yeni_revizyonla_ayni_sonuc` · `kp::test_kapanmis_donemde_revizyon_gecisi_sert` · `kp::test_eski_degerli_olay_eski_degerle_hesaplanir` | §6.2 |
| YK'ye veli olmayan eklenemez | `yk::test_yk_ye_ogretmen_ve_yonetici_eklenemez` · `yk::test_veli_olan_okul_muduru_yk_ye_eklenemez` | `yonetim_kurulu.uye_turleri`, `okul_muduru_uye_olamaz` |
| DK bileşimi | `dk::test_veli_ogretmen_ayrimi` · `dk::test_veli_koltuguna_hayirsever_giremez` · `dk::test_dk_eksik_kadro_uyari[*]` | `denetleme_kurulu.koltuklar`, `asil_uye`, `yedek_uye` |
| Yedek oy sırasıyla çağrılır | `yk::test_yedek_oy_sirasiyla_cagrilir` · `yk::test_sira_disi_cagri_gerekce_ister` | `yonetim_kurulu.yedek_cagirma` |
| Aday listesi ve seçim sonucu aynı kişiler | `yk::test_aday_ve_secilen_ayni_kayit` (tek kaynak değişmezi; OYS ilkesi AYNEN) | — |
| Üç belge docx + PDF; Türkçe büyük harf, sayfa sayısı, alanların dolu olduğu; pilot okulla eşdeğerlik | `ev::test_docx_pdf_icerik_esdegerligi[E01, E02, E03]` · `ev::test_imza_ad_soyad_bicimi` · `ev::test_sayfa_butcesi[E01, E02, E03]` · `ev::test_konum_kd[E01, E03]` · `ev::test_ilk_uc_evrak_pilot_esdegerligi` | — |

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
| B2 | argon2-cffi · cryptography | 23.1.0 · 48.0.1 | KALIR | Parola türetme, Fernet, HKDF, X25519, AES-GCM | — |
| B3 | openpyxl | 3.1.5 | KALIR | Banka özeti, TEFBİS Excel, çıktılar (TK18) | — |
| B4 | xlrd | 2.0.1 | KALIR | e-Okul `.xls` — personel ve veli listesi (T5) | — |
| B5 | Pillow | 12.3.0 | KALIR | WeasyPrint bağımlılığı, ikon üreteçleri | — |
| B6 | weasyprint | 68.0 | KALIR | PDF çizicisi (T2) | — |
| B7 | pypdf | 6.14.2 | KALIR | `--pdf-duman`; PDF ↔ Word içerik eşdeğerliği testi | — |
| B8 | whitenoise · waitress | 6.12.0 · 3.0.2 | KALIR | SPA servisi, WSGI | — |
| B9 | segno | 1.6.1 | **ÇIKAR** | Etiket ve Ağ Doktoru QR'ı. Dört halka + lisans + `test_bagimlilik_duman_gercek_listeyle…` (segno'yu adıyla sınar, §13 D8) | F1a-2 |
| B10 | python-docx | — | **EKLENİR** (sürüm F1a-3 ilk kanıtında pinlenir) | Word çizicisi (T2). Spec `collect_submodules("docx")`; iç şablon dosyaları için `collect_data_files("docx")` gerekip gerekmediği spike'ta (doğrulanmadı); eşleme `"python-docx": "docx"` | F1a-3 |
| B11 | lxml | — | **EKLENİR** (doğrudan pin) | python-docx'in geçişlisi; pin, kısıt dosyası ve lisans kümesinin sürümü bağlasın; eşleme `"lxml": "lxml"` | F1a-3 |
| B12 | python-docx'in öteki geçişlileri | — | Gelirse pinlenir | Sürüme göre `typing_extensions` gelebilir (doğrulanmadı); kesin liste F1a-3'te çözülmüş kurulumdan çıkar | F1a-3 |
| B13 | python-magic (libmagic) | — | **EKLENMEZ** | OYS `file_storage`'ın MIME denetimi; Windows'ta ayrı DLL ister (S-26). İmza baytı denetimi yeter (TK18) | — |
| B14 | Celery, drf-spectacular, JWT altyapısı | — | **EKLENMEZ** | OYS bağları; karşılıkları gün değişimi kapısı ve oturum belirteci (§12.A) | — |
| B15 | defusedxml | — | **ADAY** | openpyxl belgesinin XML saldırıları için önerdiği paket (doğrulanmadı); içe aktarım tasarımıyla karar | F1b |

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
- **Font:** DejaVu paket içindedir (`--pdf-duman` arar). Word çıktısında yazı tipi adı verilir, gömülmez; Pardus'taki
  karşılığı §9'da.

### 11.4 Lisans kümesi

| Yön | Bileşen | Lisans | Not |
|---|---|---|---|
| Çıkan | segno | BSD | |
| Çıkan | pystray · six | LGPLv3 · MIT | pystray'in kaynak kodu ve yazılı teklif yükümlülüğü de kalkar |
| Giren | python-docx | MIT | |
| Giren | lxml | BSD-3 | Windows tekerleği libxml2/libxslt'yi gömülü taşır; bildirimlerini `uret.sh` toplar mı — doğrulanmadı |
| Giren (gelirse) | typing_extensions | PSF | B12 |
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
(`okul.*`, ailenin şifreli alanı, ailenin denetim izi); `BaseModel.deleted_at` yerine `IPTAL`/`PASIF` durumu (O1);
`created_by` → hesap (§4); göç ağacı `0001`'den; fabrikalar `SchoolYearFactory` yerine yerel fabrikadan; gerçek firma
adı geçen test ve yorumlar uydurma adla yeniden yazılır (envanter S-21).

**Modeller (29)**

| OYS modeli | Kesin sınıf | OAB Defteri'nde | Sapma |
|---|---|---|---|
| `OabPerson` | UYARLA | `OabPerson` — K9, ad şifreli, yaş beyanı, geçmiş sayaçlar | — |
| `OabTerm` | UYARLA | `OabTerm` — durum, kilit, kural bağı | — |
| `OrganMembership` | UYARLA | `OrganMembership` — organ ve temsil türleri, oy, yedek çağırma | — |
| `GeneralAssembly` | UYARLA | `GeneralAssembly` — sabit taban, iki toplantı tek kayıtta, ibra, katılım dağılımı | `follows_failed_assembly` kalkar |
| `AgendaItem` | **UYARLA** | `AgendaItem` — tür, sonuç, oylar | Envanterde AYNEN |
| `AssemblyMinutes` | UYARLA | `AssemblyMinutes` — kişi bağları | — |
| `BoardMeeting` | UYARLA | `BoardMeeting` — durum, yeter sayı, katılım tamlığı | — |
| `BoardMeetingAttendance` | AYNEN | `BoardMeetingAttendance` | — |
| `BoardDecision` | UYARLA | `BoardDecision` — defter, sıra no, sayfa, oylar, durum | — |
| `AuditReport` | UYARLA | `AuditReport` — liste tazelenir, DK yazar | — |
| `BudgetCategory` | UYARLA | `BudgetCategory` — TEFBİS tohumu, dosya bayrağı | — |
| `OabBudget` | UYARLA | `OabBudget` — devir `OpeningBalance`'a, "görüşüldü" | — |
| `BudgetLine` | UYARLA | `BudgetLine` — gerçekleşen hesaplanır | — |
| `ComplianceEntry` | UYARLA | `ComplianceItem` (yeniden adlandırma) + `Announcement`, `MonthlyReport`, `ShareStatement`, TEFBİS mutabakatı | Ad değişti; sapma kayıtları da buraya (O3) |
| `ReceiptBookRegistry` | UYARLA | `ReceiptBookRegistry` + `ReceiptLeaf` | — |
| `IndexRate` | AYNEN | `IndexRate` (değer anlamı sabitlenir) | — |
| `TefbisImport` | ALMA | `TefbisStatement`, `TefbisStatementLine` (YENİ) | — |
| `RentableAsset` | UYARLA | `RentableAsset` | — |
| `Tender` | UYARLA | `Tender` — iki süreç, `winner` yerine `Bidder.selected` | — |
| `TenderCommissionMember` | UYARLA | oy ve muhalif şerhi | — |
| `TenderApproval` | UYARLA | servis mülki amir; kantin makamı elle | — |
| `Bidder` | UYARLA | engel işaretleri, `person` FK kalkar | — |
| `BidderDocument` | UYARLA | özne, geçerlilik, dosya `Attachment`'a | — |
| `ScoringCriterion` | AYNEN | tohum kural paketine | — |
| `BidderScore` | AYNEN | — | — |
| `OabContract` | UYARLA | EK-2 alanları, 20 yıl hesabı, çoklu sözleşme | — |
| `ContractInstallment` | UYARLA | Kantin aylık kira ve pay takvimi; serviste üretilmez | Servis kullanımı ALMA |
| `ShareStatement` | UYARLA | yerleşim türü, iki vade, yer alanlı tekil kısıt | — |
| `InspectionRecord` | AYNEN | yardım metni düzeltilir | — |

Sayım: **AYNEN 5** (`BoardMeetingAttendance`, `IndexRate`, `ScoringCriterion`, `BidderScore`, `InspectionRecord`) ·
**UYARLA 23** · **ALMA 1** (`TefbisImport`). Enum değişiklikleri envanter §2.3'teki gibidir; ek olarak `OrganType`'a
`DIVAN`, `ALIM_KOMISYONU`, `TEMSILCI` girer, `ComplianceKind` `ComplianceItem.obligation`'a dönüşür.

**Servisler (`services.py`)**

| Fonksiyon | Kesin sınıf | Not | Sapma |
|---|---|---|---|
| `_q` | AYNEN | Kuruş yuvarlama | — |
| `create_term`, `update_term` | UYARLA | Ders yılı `okul`'dan; kilit; kural bağı | — |
| `create_person`, `update_person` | UYARLA | K9; ad şifreli; `linked_user` yok | — |
| `compute_assembly_quorum` | UYARLA | Taban kural paketinden 16; olağanüstüde de çarpan | — |
| `schedule_general_assembly` | UYARLA | 15 gün, 30 gün, Ekim sonu, çağıran ve neden, anlık mevcut | — |
| `create_default_agenda` | AYNEN | Mantık aynı; tohum içeriği [md. 11/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11), [md. 11/1-f](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-11) maddeleriyle tazelenir (veri) | — |
| `record_assembly_outcome` | UYARLA | İki toplantı, ibra, katılım dağılımı, yeni dönem açılışı | — |
| `set_assembly_minutes` | UYARLA | Kişi bağı; divan uyarısı | — |
| `validate_membership_composition` | UYARLA | Koltuk uygunluğu sert, sayılar uyarı; müdür yasağı; DK'de hayırsever yok | — |
| `count_prior_baskan_terms`, `promote_membership` | UYARLA | [md. 12/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-12) başkan ve üyeler; geçmiş sayaçlar | — |
| `drop_membership` | UYARLA | `drop_kind`; [md. 7/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-7) istisnası; yedek çağırma önerisi | — |
| `assign_membership` | UYARLA | Beyan yalnız tarih | — |
| `record_board_meeting` | UYARLA | Yeter sayı 4, katılım tamlığı | — |
| `record_attendance`, `_maybe_auto_drop_for_absences` | **UYARLA** | Sayım toplantı üzerinden (kayıt değil, S-19); düşme öneri + onay | Envanterde AYNEN; bir testi UYARLA'ya geçer |
| `record_board_decision` | UYARLA | Durumlar, defter alanları, oy yeter sayısı | — |
| `create_audit_report` / `update_audit_report` | UYARLA / AYNEN | Liste tazelenir / bayrak mantığı aynen | — |
| `ensure_default_budget_categories`, `create_budget`, `set_budget_line` | UYARLA | K1; TEFBİS tohumu | — |
| `_iter_year_months`, `suggest_personnel_realized_for_term`, `apply_personnel_realized` | ALMA | K3 | — |
| `BudgetFinancialSummary`, `budget_financial_summary` | UYARLA | Kayıtlardan; `OpeningBalance` | — |
| `record_compliance`, `mark_compliance_done` | UYARLA | `ComplianceItem` takvim türü; kanıt | — |
| `create_index_rate` | AYNEN | — | — |
| `create_receipt_book` | UYARLA | Seri-cilt-sıra, yapraklar, karar bağı | — |
| `_persist_tender_warnings`, `set_commission` | AYNEN (desen) | Uyarı + gerekçe deseni; yazdığı yer `ComplianceItem(SAPMA)` | Hedef tablo değişir (mekanik) |
| `ensure_ek3_scoring_criteria` | UYARLA | Tohum kural paketinden | — |
| `create_rentable_asset`, `set_estimated_price` | AYNEN | — | — |
| `create_tender` | UYARLA | İki süreç; servis varsayılanı komisyon değerlendirmesi | — |
| `validate_commission` | UYARLA | Bileşimler kural paketinden; servis yedekleri | — |
| `register_bidder` | UYARLA | Gerçek kişide vergi no yok | — |
| `check_bidder_eligibility` | UYARLA | Suç ([md. 20/11](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) ve hısımlık ([md. 20/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20)) sert; belge uyarı | — |
| `score_bidder`, `compute_bidder_total` | **UYARLA** / AYNEN | Kademe dışı puan sert değil uyarı (plan §1.8) / toplam aynen | Envanterde ikisi de AYNEN |
| `determine_winner` | UYARLA | En düşük teklif çıkar; çoklu seçim | — |
| `record_approval`, `finalize_tender` | UYARLA | OLUR sert; 5 iş günü; 7 gün ilan ilan anında | — |
| `add_bidder_document` | UYARLA | `Attachment`; varsayılan tarama yok | — |
| `create_contract` | UYARLA | EK-2, 20 yıl hesabı, takvimle yıl, durumlar | — |
| `add_installments` | UYARLA | Kantin aylık kira takvimi; servis taksidi yok; > 9 uyarı | — |
| `_share_due_date`, `record_share_statement`, `mark_share_paid` | UYARLA | İki vade; yerleşim türü; gecikme zammı hesaplanmaz | — |
| `apply_tufe_increase` | UYARLA | Yıl dönümü; on iki aylık ortalama; bildirim | — |
| `record_inspection` | AYNEN | — | — |
| `oab_reminder_recipients`, `_emit_membership_dropped` | ALMA | Pano | — |
| `get_disbursement_signatories` | UYARLA | Ödeme talimatının imza bloğu ([md. 18/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18)) | — |

**Diğer bileşenler**

| Bileşen | Kesin sınıf | Not |
|---|---|---|
| `selectors.py` tek kaynak listeleri (`organ_members`, `elected_roster`, `candidate_roster`, `agenda_items`, `list_memberships`) | AYNEN | Evrakın tutarlılık dayanağı |
| `selectors.py` getiriciler, liste uçları, vade taramaları | UYARLA | Model değişikliklerine göre; vade taramaları pano "yaklaşan işler"e; PII'siz liste deseni korunur |
| `selectors.latest_index_rate` | AYNEN | — |
| `permissions.py` | ALMA | K2 rol matrisi (§4); "okuma ≠ yönetme ≠ hassas detay" ayrımı ve hassas okuma günlüğü deseni korunur |
| `signals.py`, `events.md`, `tasks.py` | ALMA | Pano ve takvim; "bildirimde kişi adı yok" ilkesi pano metinlerinde AYNEN |
| `documents.py` (`render_*`, `build_imza_surkusu_xlsx`) | UYARLA | Tek içerik, iki çizici (T2); imza blokları Yönetmeliğe göre (S-9); ayrıntı §9 |
| `documents._ihale_commission` | AYNEN | Başkan başta sıralama |
| `file_storage.py` | UYARLA | `Attachment`; sha256, uuid adı, boyut sınırı AYNEN; libmagic ve yalnız-PDF kalkar, dosya şifrelenir |
| `views.py`, `serializers.py`, `urls.py` | UYARLA | İnce görünüm deseni; liste/detay ayrımı; rol katmanı ve günlük ailenin |
| `admin.py`, `migrations/`, `apps.py` | ALMA | Masaüstünde admin yok; şema sıfırdan |
| `templates/.../documents/` (21) | UYARLA | §9 evrak kataloğunda dosya dosya |
| Testler (373) | Envanter §6: AYNEN 69 · UYARLA 277 · ALMA 27 | Üç test AYNEN'den UYARLA'ya geçer: `test_ust_uste_3_mazeretsiz_devamsizlik_dusurur` (düşme artık öneri + onay) ile `test_puan_azamiyi_asamaz_sert_engel` ve `test_ikili_kriter_yalniz_0_veya_max` (kademe dışı puan uyarı): **66 · 280 · 27**; seri bozulması, mazeretli devamsızlık ve DK testleri AYNEN kalır. Kesin sayım F2-F6'da test taşınırken yapılır |

### 12.B İskelet (Kütüphane Defteri)

*Kaynak 9a3829d. Dosya dosya gözlem [iskelet envanteri §2-§3](../kesif/2026-10-31-iskelet-envanteri.md)'tedir; burada
karar biçimi. Zaman: **F1a-1** ham kopya + kimlik çevirisi · **F1a-2** arındırma · **F1a-3** evrak hattının ilk kanıtı · **F1b**
güvenlik çekirdeği ve roller · **F1c** organ bağı · **sonra** ilgili faz.*

**F1a-1 ara commit'i kapısızdır** (karar): `config/settings.py` (`INSTALLED_APPS`), `config/urls.py`, `desktop/main.py`
(katalog) ve ön yüz rotaları ALMA modüllerini içe aktarır; ham kopya tek başına çalışmaz. Commit iletisi bunu yazar;
kapı F1a-2 sonunda koşar. Gerekçe: kimlik çevirisini arındırmadan ayrı görmek gözden geçirmeyi kolaylaştırır;
dört bağı F1a-1'de kesmek iki işi karıştırırdı.

#### AYNEN (yalnız kimlik sabitleri çevrilir)

| Dizin | Dosyalar |
|---|---|
| `desktop/` | `dialogs.py`, `integrity.py`, `version.py`, `django_bootstrap.py` (WAL checkpoint, bilinmeyen göç denetimi), `logging_setup.py`, `paths.py`, `session_guard.py`, `win32_objects.py`, `instance_channel.py`; ALMA ve UYARLA dışındaki testler |
| `packaging/` | `fontlar/`, `pyinstaller/fonts.conf.tmpl`, `fonts.paket.conf`, `linux/apt_dene.sh`, `docker-build.sh`, `postinst`, `prerm`, `windows/build.ps1`, `dll_kapanisi.py`, `paket_kapanisi.py`, `lisanslar/on_yuz_paketleri.mjs`, `uret.sh`; testler `test_apt_dene`, `test_betik_kodlamasi`, `test_paket_kapanisi`, `test_paketleme_tetigi` |
| `backend/` kök ve `shared/` | `conftest.py`, `manage.py`, `requirements-dev.txt`, `apps/__init__.py`, `config/wsgi.py`; `shared/models.py`, `pdf.py`, `text.py`, `working_days.py`, `crypto.py` (yalnız kimlik dizgeleri; ilkel işlevler aynen) |
| `backend/apps/okul/` | `name_match.py`, `normalize.py`, `lock_middleware.py`, `views_calendar.py`, `views_yedek.py`, `services/calendar.py`, `dis_yedek.py`, `recovery_key_document.py`, `school_year.py`, `terms.py`, `encrypted_backup.py`; testlerin kütüphaneye bağlı olmayanları |
| `backend/templates/` | `BENIOKU.md`, `print/_design.css`, `documents/base.html`, `documents/kurtarma_anahtari.html` |
| `frontend/` | `src/ui/` (50; `BarcodeInput` hariç), `src/hooks/` (11; depo anahtarları §2.3), `src/test/setup.ts`, `kurulumDurumu.ts`, `modules/takvim`, `modules/guncelleme` ("iki kapı" yorumu tek kapıya) |
| kök | `.gitattributes` (OAB'deki bayt bayt aynı), `LICENSE` (OAB'de var, K7) |

#### UYARLA

| Yol | Değişiklik | Zaman |
|---|---|---|
| `VERSION` | Kopyalanmaz; OAB'nin ilk sürümü aile CalVer biçimiyle yazılır | F1a-1 |
| `SECURITY.md` | `.odbak`; "ağ kataloğu yüzeyi" çıkar; "ağ servisi sunmaz" cümlesi; iletişim satırı kalır | F1a-1 |
| `docker-compose.yml` | Proje adı; "yerel ağa katalog" yorumu → ağ servisi yok | F1a-1 |
| `.gitignore` | Birleştirme: sentetik e-Okul personel ve veli örneklerinin **adıyla** istisnası, `.od-depo-listesi.tmp`, `.claude/settings.local.json`, evrak denemesi dizini; `*.docx`, `*.ods` (şablonlar adıyla istisna) | F1a-1 |
| `.github/ISSUE_TEMPLATE/`, `workflows/` | Depo adresi; `kapilar.yml` gecelik `KD_YAVAS` dalı çıkar; `paketleme.yml` Debian 13 matrisi, adlar; `r2-yukle.yml` önek | F1a-1, F1a-2 |
| `THIRD_PARTY_LICENSES/` | Elle değil, `uret.sh` ile yeniden üretilir (§11.4) | F1a-2 |
| `scripts/gates.sh` | 3. adım (yavaş testler + ağ provası) sökülür; geçici dosya adı | F1a-2 |
| `docker/backend.Dockerfile` | Son `runserver 0.0.0.0:8000` satırı silinir | F1a-1 |
| `desktop/__init__.py`, `server.py` | Belge dizeleri: katalog paragrafı → "ağ servisi sunmaz" | F1a-2 |
| `desktop/backup.py` | `.odbak`; `encrypt_legacy_backups` ve düz `*.sqlite3` yedek kalıpları sökülür (OAB'de düz yedek hiç olmadı, §13 D29); `pre-anonim` saklama fazına kadar boşta; `pre-dek-yenileme` (TK12) | F1a-1, F1a-2, F4 |
| `desktop/backup_crypto.py` | Kimlik (F1a-1); `is_usable_security_state` şema 2'ye, `recovery_metadata` yalnız kurtarma bölümüne (TK10) | F1a-1, F1b |
| `desktop/clean_shutdown.py` | İleti "son oturumdaki kayıtları kontrol edin"; `OD_ONCEKI_OTURUM` | F1a-1 |
| `desktop/errors.py` | Başlıklar "OAB Defteri …"; 11 ayrılmış; 12 `--evrak-duman` | F1a-2, F1a-3 |
| `desktop/gunluk.py` | Uyku engelleme, IP işi, saatlik katalog denetimi sökülür; bakım kapısı `shared/bakim.py`'den, `ImportError` düşüşü kalkar (§13 D3) | F1a-2 |
| `desktop/lock.py`, `restore.py` | Mutex adları; "tepside" iletileri; `restore.py` `--hesap` + parola ya da kurtarma anahtarı | F1a-2, F1b |
| `desktop/main.py` | Tepsi, katalog, `--tepside`, uyku, güvenlik duvarı yardımcı kipi, `encrypt_legacy_backups`, `--autotest` katalog adımı sökülür; Linux'ta `qt_kurulum.hazirla()`; `--evrak-duman` | F1a-2, F1a-3 |
| `desktop/window.py` | T6 (§4.5): `tray_available`, `ask_quit_in_spa`, `kd:cik-iste`, gizleme sökülür; `show()` ve `request_quit()` kalır | F1a-2 |
| `desktop/tests/` | `test_main`, `test_window_controller`, `test_window_f5`, `test_restore`, `test_gunluk`, `test_acilista_dis_istek`, `test_geri_yukleme_provasi` + `prova_betigi.py`, `alt_surec.py`, `conftest.py`. **Taşınacak parçalar:** `test_katalog_server.py`'deki "yalnız 127.0.0.1" testleri → `test_server.py`; `test_main_f5.py`'deki WAL checkpoint ve kapanış sırası testleri → `test_main.py`; `test_tray.py`'deki Qt kurulum testleri → `test_qt_kurulum.py` | F1a-2 |
| `packaging/README.md`, `requirements-paketleme.txt`, `r2-yukle.sh` | pystray, segno, katalog paragrafları; `R2_ONEK` | F1a-2 |
| `packaging/ikonlar/` | Üreteçler (`logo_uret.py`, `ikon_uret.py`; elle çizilmiş 16/24/32, yedi kareli `.ico`) kalır, çizim ve adlar yeni | F1a-2 |
| `packaging/linux/` | `build.sh` (ufw/firewalld, katalog öz sınaması), `debian-control.tmpl` (`Description`), `kutuphane-defteri.desktop` → `oab-defteri.desktop`, `kur.sh`, `kaldir.sh`, `BENIOKU.txt`, `kap-ici-test.sh` ve `test-kurulum.sh` (`--dagitim-duman` çıkar, Debian 13, `--evrak-duman` girer) | F1a-2 |
| `packaging/lisanslar/lisanslar.py` | pystray kaynağı, segno, yazılı teklif kapsamı; `OD_WITH_QT`, `OD_DLL_DIR` | F1a-2 |
| `packaging/pyinstaller/` | `giris.py` (`RUNTIME_MODULES`, `DESKTOP_RUNTIME_MODULES`, `--dagitim-duman` çıkar, `--evrak-duman` girer) · `kutuphane_defteri.spec` → `oab_defteri.spec` (`Tree(backend/katalog)`, segno, pystray çıkar; docx girer; Qt GPL ayıklaması, UCRT süzgeci, fontconfig kalır) · `rthook_kd.py` → `rthook_od.py` (UAC yardımcı kipi dalı sökülür) | F1a-1, F1a-2, F1a-3 |
| `packaging/windows/` | `kutuphane-defteri.iss` → `oab-defteri.iss` (T6, TK7; katalog, güvenlik duvarı, otomatik başlatma, tepsi iletileri) · `NOTLAR.md` (W13-W20 düşer ya da değişir; "çarpıyla kapanır" elle doğrulama maddesi) | F1a-2 |
| `packaging/` sızıntı kapıları | `depo_sizintisi.py` (`.odbak`; `.docx`, `.ods`; **IBAN mod-97**; sınıf listesi muafiyeti → sentetik veli örneği) · `veri_sizintisi.py` (uzantı kümesi eşitliği) | F1a-2 |
| `packaging/tests/` | `test_kimlik_kalintisi` (§2.3.3), `test_lisans_kapisi`, `test_spec_kapsami`, `test_rthook`, `test_ikonlar` (`docs/site-icerigi.md` bağı koparılır ya da OAB'nin belgesi o güne yazılır), `test_depo_sizintisi`, `test_veri_sizintisi`, `test_surum_yolu` | F1a-1, F1a-2 |
| `backend/pyproject.toml` | `testpaths` ve `--cov=katalog` çıkar; ruff, mypy strict, kapsam eşiği 75 kalır | F1a-2 |
| `backend/config/settings.py`, `urls.py` | `INSTALLED_APPS`, `include("apps.kutuphane.urls")`, belge dizesi, `SECRET_KEY` ve test VT adı, `RolMiddleware`, `od_exception_handler` | F1a-2, F1b |
| `backend/shared/exceptions.py`, `letterhead.py` | İşleyici adı; okul antedi aynen, birlik antedi kararı §9 | F1a-1 |
| `apps/okul/models.py`, `migrations/` | `SchoolConfig.kutuphane_saatleri` çıkar; OAB alanları ve `Hesap`, `DenetimIzi` §5'te; `Student` ALMA; `ClassSection` §5 (T5); göçler tek `0001_initial` | F1b |
| `apps/okul/excel_personel.py`, sentetik personel örneği, `uret_eokul_ornekleri.py` | "Görevi" yalnız üye türünü belirlemek için okunur (öğretmen/yönetici) | F1b |
| `apps/okul/eokul.py`, `excel_ogrenci.py` | **Veli listesi ayrıştırıcısına** dönüşür (T5): blok düzleştirici ve sınıf/şube çıkarımı korunur; yalnız veli ad-soyadı ve öğrencinin sınıfı okunur, öğrenci adı, numarası, T.C. kimlik no okunmaz ve tutulmaz. Hangi e-Okul raporunun veli adını taşıdığı **doğrulanmadı** (sınıf listesi OOG01001R020 taşımaz) — §15 M-10 | F1b |
| `apps/okul/kip.py`, `kip_izinleri.py`, `kip_middleware.py`, `views_mode.py` | → `oturum.py` (`OturumDurumu`), `rol_izinleri.py`, `rol_middleware.py`, `views_oturum.py`; görevli/yönetici kipi → oturum + rol (§4.4). Yeniden adlandırma bilinçli: "kip" kavramı kalkar | F1b |
| `apps/okul/permissions.py`, `views_app.py`, `restart_gate.py` | `RequiresAdminPassword` → rol izinleri; `app/quit/`'te görevli parola dalı sökülür; "tepsiden Çık" iletisi | F1a-2, F1b |
| `apps/okul/masaustu_kanca.py` | `KatalogKontrolu` protokolü ve katalog bakım çağrıları sökülür; çıkış kancası ve gün işleri kaydı kalır | F1a-2 |
| `apps/okul/services/app_password.py` | Şema 2: `enable` → ilk yönetici hesabı; `unlock(hesap, parola)`; hesap aç, kapat (TK11), sıfırla; `start_handover` yerine dönem sonu hesap kapanışı; DEK yenileme (TK12, F4). Dosya adı korunur: "parolayla DEK açma" kavramı sürer | F1b, F4 |
| `apps/okul/services/backup_restore.py`, `live_restore.py` | Bakım kapısı `shared/bakim.py`'den; aday durumlar şema 2 ve TK10; hesap seçimi | F1a-2, F1b |
| `apps/okul/services/imports.py`, `persons.py`, `sections.py`, `templates.py`, `setup.py`, `updates.py` | Öğrenci mutabakatı ve şablonu çıkar; kayıt defteri kancaları OAB modelleriyle (F1c); sihirbaz adımları plan §2.2, yol haritası maddeleri; varsayılan depo ve `INSTALLER_PATTERN` | F1a-1, F1b, F1c |
| `apps/okul/views_pool.py`, `selectors.py`, `serializers.py`, `views.py`, `urls.py` | Öğrenci dalları sökülür; personel ayrılış havuzu kalır | F1b |
| `apps/okul/management/commands/` | `app_password`, `restore_backup`: `--parola` → `--hesap` + parola | F1b |
| `apps/okul/tests/` | `test_cikis_ucu`, `test_dis_istek_kapilari` (izinli listeden katalog ve künye satırları çıkar), `test_imports`, `test_kip_koruma` → `test_rol_koruma`, `test_kisi_yazan_uclar` | F1a-2, F1b |
| `templates/documents/aydinlatma_metni.html` | KVKK md. 10 asgari unsur kalıbı; içerik §3.4 | sonra |
| `frontend/` yapılandırma, `public/app-logo.png` | `package.json` adı; `tailwind.config.js` `--od-*`; `vitest.config.ts` eşiği (82/82/78/55) aynen; logo | F1a-1 |
| `frontend/src/` kökü | `App.tsx` rotaları (≈20 ALMA sayfası), `AppShell` gezinmesi, `index.css` `--od-*`, `KurulumKapisi` | F1a-2 |
| `frontend/src/lib/` | `api.ts` (`X-OD-Etkinlik`), `kilit.ts`, `kip.ts` → `oturum.ts`, `restart.ts` (olaylar), `mevzuat.ts` (Yönetmelik adı), `format.ts` (`formatAccessionNo` çıkar), `gradeLevels.ts` (T5) | F1a-1, F1a-2, F1b |
| `frontend/src/modules/` | `kurulum` (1. adım ilk yönetici hesabı) · `guvenlik` (kilit ekranında hesap seçimi; `GorevDevri` sökülür) · `ayarlar` (dört kütüphane paneli çıkar) · `hakkinda` (tek dış istek kapısı, ağ servisi yok, dürüst sınırlar §4.4.6) · `kilavuz` (5.080 satırlık dosyadan kabuk bileşenleri ayıklanır, içerik silinir) · `panel` (kütüphane kartları çıkar; son oturum kartı §13 D4) · `cikis` (görevli dalı) · `kip` → `oturum` · `okul`, `kisiler` (kütüphane içe aktarımları) | F1a-2, F1b |

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
| `templates/documents/` — `gorev_devri_notu.html` (E18) ve 19 kütüphane şablonu | Kütüphane evrakı | E18 kalıbı F4 devir-teslimde yeniden yazılır |
| `packaging/linux/ufw-*`, `firewalld-*.xml`, `windows/gorev-kur.ps1`, `tests/test_ag_katalogu_paketi.py` | Güvenlik duvarı, otomatik başlatma, katalog paketi | `.iss` görevleri, `build.sh` kurulum satırları |
| `scripts/ag_katalogu_provasi.py`/`.sh`, `deneme_verisi.py`, `ekran_goruntuleri/` | Ağ provası; kütüphane deneme verisi; site görüntüleri | F7'de OAB'nin uydurma veri üreticisi aynı kalıpla (stdlib + openpyxl, çıktı depoya girmez); site adımında görüntü kalıbı |
| `frontend/src/ui/BarcodeInput.tsx` (+test); 12 modül (agkatalogu, ayiklama, dokumler, dolasim, kayip, kutuphane, raporlar, saklama, sayim, teslim, uyelik, yil — 159 dosya); `src/test/` dört kütüphane verisi | Kütüphane ekranları | `App.tsx`, `AppShell`, `panel`, `ayarlar`, `kip`, `kisiler`, `kilavuz` |
| Kök `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/` | OAB'nin kendileri var | — |

#### YENİ (aileden gelmeyen)

| Yol | Ne | Zaman |
|---|---|---|
| `desktop/qt_kurulum.py` (+ `test_qt_kurulum.py`) | `tray.py`'den taşınan `load_qt`, `prepare_qt_application`, SIGTERM köprüsü | F1a-2 |
| `backend/shared/bakim.py` | `katalog/bakim.py`'deki `BakimKapisi` (yalnız stdlib); geri yükleme ↔ gün işleri dışlaşması | F1a-2 |
| `backend/shared/docx.py`, `shared/evrak.py` | T2 çizici ve cephe (TK17); `--evrak-duman` | F1a-3 |
| `Hesap`, `DenetimIzi` modelleri ve servisleri | T1, TK16 (alanlar §5) | F1b |
| `frontend/src/modules/kullanicilar` | Hesap aç, kapat, parola sıfırla; son girişler | F1b |

**Kalıp olarak sonra bakılacaklar** (kopyalanmaz): `apps/kutuphane/services/saklama.py` + `pre-anonim` (saklama ve
anonimleştirme, F4+) · `modules/dokumler` (KVKK md. 11 kişi dökümü) · `gorev_devri.py` + E18 (devir-teslim, F4) ·
`BelgeIzi` (tür, tarih/sayı, sha256 — evrak izi, §9) · `docs/saha-kabulu.md` + eşleme testi + `deneme_verisi.py` (F7) ·
`scripts/ekran_goruntuleri/` (site, F7).

---

## 13. Devralınan kusurlar

### 13.A İskeletten (Kütüphane Defteri)

*Kaynak sütunu: "TB" = Kütüphane `docs/teknik-borc.md` maddesi; "env." = [iskelet envanteri](../kesif/2026-10-31-iskelet-envanteri.md)
bölümü; "bu belge" = bu yazımda kaynak kodda görülen. Kütüphane'de ALMA'lık bölümde kalanlar (TB2, TB10-12, TB15-16,
TB20-22, TB29-35, TB37-38, TB41-42) OAB'ye geçmez; TB26 bilgi içindir (OAB kapalı hâli devralır).*

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
| D14 | Kurtarma anahtarı yenileme ele geçmiş anahtarı geçersiz kılmaz; yedekler eski parolayla açılır — dönemlik veli hesaplarıyla **ağırlaşır** | TB17, TB23; env. §6.3-2 | TK10 + TK11 (F1b); TK12 (F4) | yüksek | F1b, F4 |
| D15 | Kurulum bitmeden kip süreyle kapanmıyordu (anahtar ekrandayken atmasın) | TB19 | Aynı kural oturum kilidinde: sihirbaz bitene dek boşta kilit yok; elle Kilitle çalışır | orta | F1b |
| D16 | Her güncelleme yönetici ister | TB7, env. §11-1 | TK7 (§15 M-1) | orta | F1a-2 |
| D17 | Debian 11 ana deposu arşive taşınınca derleme 404; Debian 13 provası yok; t64 adları | TB5, env. §8.5 | `test-kurulum.sh` ve `paketleme.yml` `11 12 13`; `apt_dene` arşiv sabitlemesi aynen; `Depends` davranışını prova gösterir | orta | F1a-2 |
| D18 | Lisans dizini kararlı öncesi iki iş (MSYS2 kaynak arşivi, Qt bildirimi) | TB28 | python-docx/lxml ile `uret.sh` yeniden üretim; iki iş F7 paketlemesinden önce | orta | F1a-2, F7 |
| D19 | PySide6 6.8.3 tavanı; `.deb` ~180 MB | TB27 | Tavan korunur; yükseltmeden önce sembol denetimi | orta | sürekli |
| D20 | Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hâle Getirilmesi Hakkında Yönetmelik korpusta yok | TB9 | `docs/mevzuat/`'e resmî kaynaktan; saklama ve anonimleştirme tasarımından (§5) önce | orta | F4'ten önce |
| D21 | Şifreleme kapsamı Kütüphane modeline göreydi (düz kalan alanlar) | TB1 | OAB modeline göre §5'te yeniden yazılır | yüksek | F0-8 (§5) |
| D22 | Anonimleştirilen bağlar yedeklerde ve arşivdeki asılla eşleşebilir | TB8, TB39 | OAB saklama tasarımında aynı sınır; §5 | düşük | F4+ |
| D23 | Şifreleme öncesi düz metin penceresi | TB24 | `enable()` boş tablo şartıyla kuramsal; aynen | düşük | — |
| D24 | İmzasız exe (SmartScreen) | TB6 | Port kısmı düşer; kılavuz; imzalama ileride | düşük | F7 |
| D25 | Büyük dökümlerde PDF süresi (tek PDF kilidi) | TB36 | Uzun gelir-gider dökümünde Excel asıl çalışma biçimi; gerçek uzunlukta veriyle sayfa bütçesi testi | düşük | F3 |
| D26 | Pardus paketi açık programı kapatmaz | TB40 | Çarpı = çık ile olasılık düşer; `prerm` iletisi | düşük | F1a-2 |
| D27 | `synchronous=FULL` maliyeti | TB3 | Kalır; HDD ölçümü saha | düşük | F7 |
| D28 | Plan §2.1-2 bağımlılık zincirini "üç yer" sayar | env. §2.12-5 | Dört halka + lisans (§11); plana "F0 eki" | düşük | F0-8 |
| D29 | `backup.encrypt_legacy_backups` ve düz `*.sqlite3` yedek kalıpları ailenin düz yedek döneminden kalma geçiş yoludur | **bu belge** (`desktop/backup.py`) | Sök (OAB'de düz yedek hiç olmadı) | düşük | F1a-2 |
| D30 | "Olası aynı kişi" ad benzerliğiyle | TB18 | Personel ve veli aktarımında birleştirme önerisi onaylı | düşük | F1b |
| D31 | Logo geçiciydi; dosya adları taramaya girer | TB4 (kapandı) | Yeni logo, elle çizilmiş 16/24/32; adlar `oab-defteri-*` | düşük | F1a-2 |

**F1a arındırma sırası** (önce ayır ve taşı, sonra sök — §16 R14): (1) D6 kalıntı kalıpları ve kimlik çevirisi (F1a-1,
kapısız ara commit) → (2) D1 `qt_kurulum.py`, D2 `test_server.py`, D3 `shared/bakim.py`, D4 son oturum kartı —
taşı ve yeşile getir → (3) tepsi, katalog, Ağ Doktoru, güvenlik duvarı, barkod, `apps/kutuphane`, ön yüz modüllerini
sök; D5, D7, D10, D29 → (4) bağımlılık zinciri (B9, B18) ve D8 → (5) D9 sızıntı kapıları, D12, D13 → (6) "ağ servisi
sunmaz" cümlesi bütün kopyalara ([iskelet envanteri §3.9](../kesif/2026-10-31-iskelet-envanteri.md)) → (7) D17
Debian 13 provası, `uret.sh` (D18) → (8) F1a-3 evrak hattının ilk kanıtı (B10-B12). Kapı (8)'den sonra koşar.

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
| D42 | Kodda ve testte gerçek bir taşımacı firma adı | S-21 | Taşırken uydurma ad; sızıntı denetimi bu adları da arar (değer belgeye yazılmaz) | F6 |
| D43 | Servis evrakında "ihale" söz dağarcığı (7 şablonda 13 kez) | S-25 | §9 (altın kural 6; §15 A-4) | F6 |
| D44 | OYS sert engelleri altın kural 3 ile gerilimde | S-23 | Kullanıcı kararı F0-b → §7 | F5, F6 |
| D45 | Arz bedeli vadesi yalnız 20'si; aylık kira takvimi yok | S-5, S-14 | Kullanıcı kararı F0-a → §6, §7 kantin | F5 |

---

## 14. Faz planı ve kod kapıları

Ailenin faz kuralları geçerlidir: faz **kod kapısı** geçilmeden kapanmaz; tasarımdan sapmalar "F<n> ekleri (tarih)"
satırıyla bu belgeye işlenir; okulun denetiminde olmayan saha kanıtı fazı kilitlemez, sonraki faza ertelenir; yayın
işleri kullanıcı onaylıdır. F0 ve F1'in iş kalemleri [F0-F1 planında](../plan/2026-10-31-f0-f1-plani.md)dır; F2-F8
ayrıntısı her fazın başında aynı biçimde bir plan belgesiyle açılır. Kural paketi `OAB-2023.12` F1c'de ilk
revizyonuyla (50 kural) girer; kalan kurallar, onları kullanan kod hangi fazda yazılırsa o fazda paket revizyonu
artırılarak eklenir (§6.2, §6.4).

| Faz | İçerik | Kod kapısı |
|---|---|---|
| **F0** | Mevzuat korpusu, envanterler, kullanıcı kararları, bu belge, bağımsız tasarım denetimi (F0-9) | Plan §1.6 — denetim bulguları işlendi, kullanıcı "F0 tamam" dedi |
| **F1a** | Aile iskeleti: ham kopya + kimlik çevirisi, arındırma (sıra §13), evrak hattının ilk kanıtı (T2), Debian 13 provası | Windows'ta exe açılır, çarpıyla kapanır · `.deb` Debian 11/12/13'te kurulur ve açılır · `--pdf-duman`, `--evrak-duman`, `--bagimlilik-duman` geçer · kimlik kalıntısı sıfır · sızıntı denetimleri ve `gates.sh` yeşil |
| **F1b** | Güvenlik çekirdeği (kişisel hesaplar, T1), kurulum sihirbazı, okul kartı, kullanıcılar ve roller, e-Okul personel ve veli aktarımı | Aile güvenlik testleri · rol testleri (salt okur rol yazamaz; DK yalnız denetim modülüne, müdür yalnız kendi yazılarına yazar; her yazma denetim izinde) · veli listesi yalnız iki alan taşır |
| **F1c** | Birlik dönemi, kişiler, organlar, kural paketi v1 (`OAB-2023.12`), ilk üç evrak (FR-006, FR-011, FR-022) | Plan §2.4 — atıf kilidi; yeter sayı 64/32 (sabit taban); dönem sınırı başkan ve üyeler için; organ bileşimleri; üç evrak docx + PDF eşdeğer; temiz Windows 11 ve Pardus 25'te uçtan uca zincir |
| **F2** | Genel kurul sihirbazı ve evrak seti: çağrı kararı, davet, ilan ve duyuru tutanağı, katılım cetveli, yeter sayı tespiti, **ikinci toplantı ana yol** (saha 8), divan, raporlar, ibra ("ibra edilmedi" akışı dâhil), bütçe, seçim, sonuç yazısı, görev bölümü, devir-teslim; olağanüstü genel kurul | Pilot okulun 2026-2027 genel kurul akışı (birinci toplantıda yeter sayı yok → ikinci toplantı) uydurma adlarla programdan baştan sona üretilir; evrak genel setle içerik eşdeğer; 15 gün, 30 gün, bir hafta süre testleri |
| **F3** | YK toplantı ve karar taslağı ("deftere işlendi"), devamsızlık ve yedek çağırma; işlem düzeyinde gelir-gider, hesap planı, banka özeti içe aktarma ve eşleme, makbuz koçanı, şartlı bağış, kasada 5 iş günü, devreden bakiye, "TEFBİS'e girilecekler" listesi, deftere geçirilecek aylık baskı | Uydurma bir yıllık banka dökümü (~410 hareket) eşlenir, TEFBİS listesi ve defter baskısı üretilir; ters kayıt ve dönem kilidi testleri. **Saha kanıtı (kapıyı kilitlemez):** pilot okulun 2025-2026 hareketleri yerelde, depoya girmeden mutabık |
| **F4** | Harcama zinciri (talep → karar → komisyon → belge → ödeme → banka → TEFBİS), tahmini bütçe ve gerçekleşme, aylık bildirim, dönemlik ilan, Denetleme Kurulu modülü (kontrol listesi, ara ve nihai rapor), faaliyet raporu ve kesin hesap, dönem kapanışı, devir-teslim, yıl sonu arşiv paketi | Uydurma bir dönemin tamamı programdan kapanır: kesin hesap = banka; devir tutanağı ve arşiv paketi (PDF + xlsx + JSON) programsız okunabilir |
| **F5** | Kantin: kiracı kartı, kiralama süreci evrakı, EK-2 sözleşmesi (25 madde), aylık kira takvimi, arz bedeli (10'u / 20'si) ve pay dağılımı, TÜFE artışı, Genelge 2024/35 yirmi yıl hesabı, kesin teminat, belge süreleri; `bilgi/` dizini (KV Sirküleri No. 11 ve özelgeler) | 2026-2027 kantin sözleşmesi ve kira-pay tablosu programdan birebir (pilot okul, uydurma adlarla) |
| **F6** | Servis: taşımacının tespiti (komisyon değerlendirmesi esas, EK-3 yalnız md. 8/3 hâllerinde), sözleşme, araç-şoför belge takibi, denetim kaydı | Pilot okulun servis tespiti evrakı programdan birebir; servis evrakında "ihale/teklif/eksiltme" taraması sıfır |
| **F7** | Paketleme ve saha kabulü: pilot okulda 2026-2027 dönemine **paralel** beta (defter ve TEFBİS esas kalır); site sayfası (§17) | Saha kabulü protokolü (ailenin `saha-kabulu.md`'si uyarlanır); gönüllü okul aranmayacağından (F0-d) kabul yalnız pilot okul |
| **F8+** | TEFBİS Excel mutabakatı (M12), denetim dosyası (TKB E.4 Tablo 1-4, Sayıştay icmali), personel modülü (doğrudan işveren okullar; K3), ilkokul/ortaokul ve küçük okul sınamaları | Fazın kendi planında |

Beta F4'ten sonra başlayabilir; F5 ve F6 beta sürerken eklenebilir (kantin kiralaması en çok beş yılda, servis tespiti
bir-üç yılda bir yaşanır).

---

## 15. Açık kararlar (varsayılanla ilerlenir)

Kullanıcı itiraz etmedikçe varsayılan uygulanır; itiraz gelirse "F<n> eki" ile değişir. Kimlikler: A-n bu bölümün,
M-n mimari (§4, §11, §13), B-n veri modeli ve akışlar (§5, §7, §8), KE-n kural paketi ve evrak (§6, §9, §10)
bölümlerinin önerisidir; S-n atıfları OYS envanterindeki sorulardır. §15.1'deki altı soru kullanıcıya soruldu ve
karara bağlandı; kalanlar varsayılanla ilerler (§15.2-§15.5).

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
| M-11 | K2'deki üç müdür yazısının taslağını `yonetici` hazırlayabilsin mi? | **Hayır** | K2 lafzı: bu yazılar müdür hesabından |
| KE-20 | Aydınlatma metnindeki veri sorumlusu | Okul kartındaki alandan dolar; kılavuzda açık soru | F0-e (b) |

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
| B-6 | `EMANET` alt hesabı (nakit kesin teminat, aktarılacak il/ilçe payları) | Eklenir (T4'teki banka, kasa, şartlı bağışa ek) | Birliğin olmayan parayı ayrı izlemek denkliği korur |
| B-1 | TEFBİS'in dönem esası (takvim yılı mı öğretim yılı mı) | Program dönem zorlamaz; liste ve mutabakat tarih aralığıyla çalışır | DOĞRULANMADI (ön değerlendirme §2.5) |
| B-3 | Kapanışta eşlenmemiş banka hareketi | **Sert:** dönem kapanmaz | Hesap bütünlüğü (altın kural 3) |
| B-4 | Kapanışın geri alınması | Geri alınamaz; düzeltme açık dönemde "önceki dönem düzeltmesi" ters kaydıyla | Altın kural 4 |
| A-10 | Süre hesapları (S-18) | Takvim günü/iş günü ayrımı kural paketinde; yıl hesabı tarih aritmetiğiyle (5 × 365 değil); iş günü için ailenin tatil takvimi; gecikme zammı hesabı yapılmaz, yalnız bilgi (6183 korpusta yok) | Altın kural 1-2 |
| A-11 | Küçük alım tutar sınırı (saha 6) | **Okul ayarı**: dönem başı YK genel kararıyla girilir; sınırın altında talep/komisyon halkası eksikse uyarı + gerekçe, sınırın üstünde zincir tam beklenir | [md. 18/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-18) her harcamada karar, talep ve komisyon öngörür; sınır mevzuatta yok (§3.3) |
| A-12 | Gelir-gider defteri baskısının sütunları | Tarih, sıra no, belge türü ve no, açıklama, gelir, gider, kalan, karar no, gelir-gider türü | Saha 1b; Yönetmelik biçim koymaz ([md. 23/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23)) |
| A-13 | Gelir-gider defterinin bilgisayar çıktısı sayfalarla önceden tasdiki (F0-5a) | Program yalnız deftere **geçirilecek** baskı üretir; çıktı sayfaların tasdiki okulun il/ilçe MEM'le çözeceği konu | F0-e |

### 15.4 Kayıt, KVKK, saklama

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| A-8 | Organ ve kişi kayıtlarında yumuşak silme (S-22) | Mali kayıtlar **yalnız ters kayıtla** düzeltilir; organ ve kişi kayıtlarında "pasif" durumu (silme yok), denetim izinde | Altın kural 4 |
| B-11 | Genel kurul katılım kaydının ne kadarı saklanır? (T5 ile birlikte) | Kalıcı ve kişisiz: imzalayan üye sayısı ve türe göre dağılımı, velisi katılan öğrenci sayısı, o günkü mevcut, dondurulmuş yeter sayı ve sonucu. Basılan cetvelin `GeneratedDocument` izi (sha256). Kişi düzeyindeki "katıldı" işareti veli listesiyle silinir; imzalı cetvel taranmaz, aslı genel kurul tutanak dosyasında | [md. 23/1-a, 23/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23); katılım sayısı yeter sayının girdisidir, gerekçeli düzeltme satırı dışında değişmez (§5.4) |
| B-5 | Kantin çalışanı, servis şoförü ve rehber personel belgeleri | Tarama alınmaz; "görüldü" tarihi ve geçerlilik sonu tutulur. Tarama eklenirse sözleşme sonu + 2 yıl sonra imha adayı; seçilmeyen isteklinin iletişim bilgisi aynı sürede boşaltılır | [md. 20/7](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-20), [23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) belgeleri birliğe saklatır; saklama süresi DOĞRULANMADI |
| B-7 | Kişinin telefonu | Son üyeliğin bittiği dönemin kapanışında boşaltılır | Veri en aza (KVKK) |
| B-8 | Bağışçı T.C. kimlik no'su (K9 açıksa) | Dönem kapanışında boşaltılır; kör indeksi yok; hiçbir dışa aktarım dosyasına girmez | K9 |
| B-9 | Erişim günlüğünün saklama süresi | 2 yıl | DOĞRULANMADI |
| B-10 | Yıl sonu arşiv paketinin korunması | AES-256 şifreli ZIP (`pyzipper`, §11'e yeni bağımlılık); parolayı kapanışta yönetici belirler | Arşiv kişisel veri taşır; programsız açılabilmeli |

### 15.5 Mimari ve güvenlik

| # | Soru | Varsayılan | Dayanak / gerekçe |
|---|---|---|---|
| M-1 | Kurulum yetkisi | Kullanıcı başına kurulum (`PrivilegesRequired=lowest`); BT sorumlusu isterse aynı kurucuyla yönetici kurulumu (`dialog`) | Güvenlik duvarı kuralı kalkınca yönetici kurulumunun gerekçesi düşer (§13) |
| M-2 | Dönem devrinde veri anahtarını (DEK) yenileme | **Yapılır** (F4): her dönem yeni kurtarma anahtarı devir dosyasına girer; eski anahtar eski yedekler için kapalı zarfta kalır | Kapanan hesapların eski sarmallarıyla erişimi keser (§4.4) |
| M-3 | Boşta kilit süresi | 10 dk (ayar 3-30); mutlak oturum süresi yok | Ortak bilgisayar; Kütüphane'nin görevli/yönetici kipi yerine tek oturum |
| M-4 | Parola politikası | En az 8 karakter (sert); karışık yapı ve en geç altı ayda bir değişim zorunlu | [BSG Yönergesi md. 9/2-a, b, ç](../mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-9); velilerin Yönergedeki kapsamı yorumdur |
| M-7 | Görevsiz YK asıl üyeleri ve yedekler hesap alsın mı? | Hayır (v1) | Saha 10: programı çoğunlukla MY kullanır |
| M-8 | Ayrı, yönetici yetkisi olmayan "OAB" Windows hesabı | Kılavuzda öneri, zorunlu değil; BSG md. 7/4'ten sapma kılavuzda açık yazılır | Okul bilgisayarının yönetimi okulun işidir |
| M-9 | Herkese açık README'de köken cümlesi | Yazılmaz | Kamuya açık metinde kurum ve kişi bilgisi yok (§17) |
| M-10 | e-Okul'da veli adını taşıyan rapor | DOĞRULANMADI (sınıf listesi raporu veli adı taşımıyor); sentetik örnekle ilerlenir, gerçek rapor gelince "F1 eki" | T5 |

---

## 16. Riskler

| # | Risk | Karşı önlem |
|---|---|---|
| R1 | **Çift iş algısı:** defter + TEFBİS + program üçüncü kayıt gibi görünürse kullanılmaz | Program defter baskısını ve TEFBİS listesini **üretir**, iş azalır; banka dökümünden başlayan kayıt (saha 3) |
| R2 | **Konumun yanlış anlaşılması:** "program resmî defterdir" sanılması | Her çıktıda konum ibaresi; kılavuzda md. 13/5, 23/2, 23/5 (§3.1) |
| R3 | **Mevzuat değişikliği:** Yönetmelik 2012'den beri beş kez değişti; TEFBİS işlem tipleri değişiyor | Kural paketi + korpus + atıf kilidi; TEFBİS eşleme tablosu okulca güncellenir |
| R4 | **Okul türü çeşitliliği ve tek saha:** gönüllü okul aranmayacağı için ilkokul/ortaokul, küçük okul ve il merkezi farkları sahada sınanmaz (F0-d) | Bu farklar okul kartından okunan kurallardır; kural testleri ve uydurma senaryolarla sınanır (§10); kapsam resmî örgün okullar |
| R5 | **Gönüllü velilerin bilgisayar yetkinliği** | Arayüz MY odaklı (saha 10); velilere sihirbaz, büyük yazı, az ekran |
| R6 | **Veri kaybı:** tek bilgisayar = tek nokta | Zorunlu yedek hatırlatması, USB'ye şifreli yedek, yıl sonu açık biçimli arşiv |
| R7 | **Bakım yükü:** ailede bir program daha | Ortak iskelet, kural paketi veri, testler OYS'den |
| R8 | **KVKK konumu belirsiz** ve veli listesi (T5) | Veri en aza (iki alan), dönem sonunda silme, erişim günlüğü, kılavuzda açık soru (§3.4) |
| R9 | **Rejim değişebilir** ("mali yetkiler kaldırılsın" tartışması) | Tam ve açık biçimli dışa aktarım; TEFBİS'i besleyen konum değişiklikte değer kazanır |
| R10 | **Vergi tarafı özelgeye dayanıyor** | Bilgi metni olarak `bilgi/`'de; hüküm diye basılmaz (§3.3) |
| R11 | **Geniş ilk sürüm (K4):** kantin ve servis seyrek yaşanır, geç sınanır | Kabul ölçütü pilot okulun gerçek evrakının birebir üretilmesi; beta F4'ten sonra |
| R12 | **OYS kodundaki mevzuat hataları** taşınırken korunabilir (yeter sayı tabanı, dönem sınırı, servis varsayılanı, imza blokları) | Kural testleri koddan önce yazılır (§10); OYS testleri AYNEN alınmadan önce mevzuatla karşılaştırılır |
| R13 | **TEFBİS ve banka şeması örneksiz** (F0-c) | Varsayılan şema; F3 başlamadan pilot okul örneği istenir, gelmezse içe aktarıcı sütun eşleme ekranıyla esnek kurulur |
| R14 | **İskelet sökümü:** Linux Qt kurulumu tepsi dosyasında, "yalnız 127.0.0.1" testleri katalog testlerinde | F1a'da söküm sırası (§13): önce ayır/taşı, sonra sök |

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
