// Güvenlik arayüzünün DÜRÜST metinleri — tek kaynak (tasarım §4.3, §4.4.6).
// Kural: bu program "veritabanını şifreliyorum" DEMEZ. Şifrelenen şey belirli
// kişisel veri alanlarıdır; anahtar da aynı bilgisayarda durur. Kullanıcıya
// olduğundan güçlü bir koruma vadetmek, gerçek önlemi (tam disk şifreleme)
// almasını engellerdi. Sözlük (docs/sozluk.md §1): "hesap", "parola", "program
// yöneticisi", "kurtarma anahtarı"; parola anlamında "şifre", "uygulama parolası"
// kullanılmaz. F1b 1. adımdan beri herkes programı kendi hesabıyla ve kendi
// parolasıyla açar (tasarım TK9, TK14): metinler tek bir "yönetici parolası" anmaz.

/** Ayarlar ve kilit ekranında gösterilen kapsam açıklaması. */
export const KAPSAM_METNI =
  "Bu koruma, kayıtlardaki kişisel veri alanlarını (öğrenci, öğretmen ve diğer " +
  "personelin ad-soyadları, öğrencilerin okul numaraları, hesap sahiplerinin " +
  "ad-soyadları, eklerin özgün dosya adları) her hesabın kendi parolasıyla açılan bir " +
  "anahtarla şifreler. TAM DİSK " +
  "ŞİFRELEME DEĞİLDİR: bilgisayarın tamamını korumak için Windows'ta BitLocker, " +
  "Pardus/Linux'ta LUKS kullanın.";

/** Şifrelenmeyen alanlar açıkça söylenir — sürpriz olmasın. */
export const KAPSAM_DISI_METNI =
  "Sınıf/şube, üye türü ve tarihler şifrelenmez (süzgeçler bunlara dayanır). " +
  "Okul numarası şifrelidir; arama ve e-Okul eşleştirmesi numaranın tamamıyla " +
  "yapılır, numaranın bir parçasıyla arama yapılamaz.";

/**
 * Dürüst sınır (tasarım §4.4.6-5, TK15): her hesabın parolası kayıtların anahtarını tek
 * başına açar; şifreli alanlar en zayıf hesap parolası kadar korunur.
 */
export const EN_ZAYIF_PAROLA_METNI =
  "Şifreli alanlar en zayıf hesap parolası kadar korunur: güvenlik dosyası veritabanıyla " +
  "aynı diskte durur ve her hesabın parolası kayıtların anahtarını tek başına açar. Bu " +
  "yüzden her hesap güçlü bir parola seçer; parola paylaşılmaz.";

/**
 * Kurtarma anahtarı zarfının üçüncü durumu (kullanıcı kararı 02.11.2026) — sözler BİREBİR:
 * kurtarma anahtarı belgesi (backend `recovery_key_document.UCUNCU_DURUM`), anahtar panelinin
 * uyarısı (`KURTARMA_UYARISI`), kilit ekranının yol gösterme metni
 * (`KurtarmaIleAcma.UCUNCU_DURUM_YOL_METNI`) ve sözlük (§1 "Kurtarma anahtarı", "Kurtarma anahtarı
 * belgesi") aynı sözü taşır; backend `test_kurtarma_anahtari_pdf` dördünü ve bu sabiti sınar.
 * Program yöneticisinin hesap kaydı ya da parola kaydı bozulmuş ya da program dışından
 * değiştirilmişse kilit ekranında girilebilecek hesap kalmayabilir; çıkış bu durumdur.
 */
export const ZARFIN_UCUNCU_DURUMU =
  "bu bilgisayarın güvenlik dosyası ya da kayıtları kaybolduğunda, bozulduğunda ya da " +
  "program dışından değiştirildiğinde";

/**
 * Üçüncü durumun çaresi (kullanıcı kararı 03.11.2026): yedekten geri yükleme (güvenlik dosyası
 * kayıpken parola yolu işlemez; tasarım §4.4.4) ya da kurtarma anahtarıyla açılış ("Parolamı
 * unuttum"; program yöneticisinin parola kaydı program dışından değiştirildiğinde). Backend
 * `recovery_key_document.UCUNCU_DURUMUN_CARESI` ile birebir.
 */
export const UCUNCU_DURUMUN_CARESI = "yedekten geri yükleme ya da kurtarma anahtarıyla açılış";

/**
 * Kurtarma anahtarı panelinin uyarısı (kurulum sihirbazının ilk adımı ve yenileme).
 * Anahtarın üç kullanımı belgedekiyle aynıdır (tasarım §9.7, §4.4.4): unutulan parola,
 * yeni bilgisayar ve zarfın üçüncü durumu (`ZARFIN_UCUNCU_DURUMU`, çaresi
 * `UCUNCU_DURUMUN_CARESI`; sözler birebir, dize düz yazılır: backend testi kaynağı okur).
 */
export const KURTARMA_UYARISI =
  "Bu anahtar bir daha gösterilmez. Kayıtlara üç durumda bu anahtarla erişilir: program " +
  "yöneticisi parolasını unutursa; kayıtlar yeni bir bilgisayara taşınırken; bu bilgisayarın " +
  "güvenlik dosyası ya da kayıtları kaybolduğunda, bozulduğunda ya da program dışından " +
  "değiştirildiğinde (çaresi yedekten geri yükleme ya da kurtarma anahtarıyla açılış). Şimdi " +
  "saklayın: yazdırın, PDF olarak USB belleğe kaydedin ya da kâğıda elle yazın. Kâğıdı " +
  "müdürlükte kapalı zarfta saklayın; anahtarı bu bilgisayarda bırakmayın.";

/**
 * Pencere içi "Yazdır" kâğıdının saklama satırı. Zarfa giren kâğıt PDF belgesinin
 * saklama kurallarını kısaca taşır (tasarım §13 D50, §9.7; BSG Yön. md. 7/2, 9/2-e).
 */
export const YAZDIRMA_SAKLAMA_METNI =
  "Okul müdürlüğünde kapalı zarfta saklanır; veliye geçmez. Yalnız program yöneticisi " +
  "içindir; parola paylaşılmaz, herkes programı kendi hesabıyla açar.";

/** Elle yazma yönergesi — belgedeki ipucuyla aynı (anahtar alfabesinde 0/1/8/9 yok). */
export const ELLE_YAZ_METNI =
  "Elle yazacaksanız grupları sırasıyla, büyük harfle yazın; anahtar no'sunu ve üretim " +
  "tarihini de kâğıda ekleyin. Anahtarda 0, 1, 8 ve 9 rakamları yoktur: O ve I her zaman " +
  "harftir.";

/** Doğrulama adımının açıklaması (iki grup, istemci tarafında; anahtar sunucuda saklanmaz). */
export function dogrulamaMetni(birinci: number, ikinci: number): string {
  return (
    `Sakladığınız kopyaya bakarak anahtarın ${birinci}. ve ${ikinci}. grubunu yazın. ` +
    "Böylece kopyanın doğru ve okunaklı olduğundan emin olursunuz."
  );
}

/**
 * Kurulum sihirbazının ilk adımı: program yöneticisi hesabı (yalnız ilk kurulumda;
 * kaldırılamaz). Parola paylaşılmaz (MEB Bilgi ve Sistem Güvenliği Yönergesi md. 7/2,
 * programa kıyasen — tasarım TK9; kullanıcı kararı T1): herkes programı kendi hesabıyla
 * açar. Program yöneticisi parolasını unutursa yol kurtarma anahtarıdır; anahtar okul
 * müdürlüğünde kapalı zarfta durur (kullanıcı kararı D3; tasarım §4.4.3).
 */
export const KURMA_UYARISI =
  "Program yöneticisi hesabı zorunludur: hesap kurulmadan öğrenci, öğretmen ve diğer " +
  "personel kaydı yapılamaz. Kurulduktan sonra kaldırılamaz; parolası değiştirilebilir. " +
  "Parolayı kimseyle paylaşmayın; herkes programı kendi hesabıyla ve kendi parolasıyla " +
  "açar. Program yöneticisi parolasını unutursa kayıtlar kurtarma anahtarıyla açılır ve " +
  "yeni parola belirlenir; bu yüzden anahtar okul müdürlüğünde kapalı zarfta saklanır.";

/** Kurtarma anahtarı belgesini yeniden alma kartı (Ayarlar → Güvenlik). */
export const BELGE_YENIDEN_METNI =
  "Kurtarma anahtarı programda saklanmaz; yalnız program yöneticisi hesabı kurulurken ya da " +
  "anahtar yenilenirken bir kez gösterilir. Elinizdeki anahtarı yazın: anahtar doğruysa " +
  "kurtarma anahtarı belgesi PDF olarak hazırlanır (ör. elle yazılmış kâğıdın temiz kopyası " +
  "için).";

/** Anahtarın saklandığı sunucuda doğrulanmadıysa (kurulum sihirbazı, Güvenlik, yol haritası). */
export const DOGRULANMADI_BASLIGI = "Kurtarma anahtarı doğrulanmadı";

export const DOGRULANMADI_METNI =
  "Kurtarma anahtarının saklandığı henüz doğrulanmadı. Program yöneticisi parolasını " +
  "unutursa kayıtlara yalnız bu anahtarla ulaşılır. Anahtarı sakladıysanız aşağıya yazıp " +
  "doğrulayın; kaydedemediyseniz yenisini üretin.";

/** "Kurtarma anahtarını doğrula" kartı: kâğıttaki anahtarın tamamı yazılır. */
export const DOGRULA_KARTI_METNI =
  "Sakladığınız kâğıttaki ya da PDF'teki anahtarı olduğu gibi yazın. Anahtar doğruysa " +
  "saklandığı kaydedilir; program anahtarı saklamaz.";

/** "Kurtarma anahtarını yenile" kartının açıklaması. */
export const YENILEME_METNI =
  "Anahtar kaybolduysa ya da kurulumda kaydedilemediyse yenisini üretin. Yeni anahtarın " +
  "no'su bir artar ve anahtar bir kez gösterilir; saklayıp doğrulamadan programı " +
  "kapatmayın. Hesapların parolaları değişmez, kayıtlar yeniden şifrelenmez.";

/** Yenileme onay diyaloğu: sonuç (başlık soru, gövde sonuç — docs/sozluk.md §3). */
export const YENILEME_SONUCU_METNI =
  "Yeni bir kurtarma anahtarı üretilir ve bir kez gösterilir. Bu bilgisayarın güvenlik " +
  "dosyasında kilidi bundan sonra yeni anahtar açar; zarftaki eski anahtar eski yedeklerle " +
  "ve arşivlenen güvenlik dosyasıyla açmayı sürdürür (aşağıya bakın).";

/**
 * Eski yedekler (backend `backup_restore`: yedek başlığı yalnız alındığı günün kurtarma
 * bölümünü taşır, hesap sarmalı taşımaz — tasarım TK10; bu bilgisayarda güncel güvenlik
 * dosyası da aday olduğu için yeni anahtar ve hesap parolası da açar). Testle kanıtlı:
 * `apps/okul/tests/test_kurtarma_yenileme.py::TestYedekler`.
 */
export const ESKI_YEDEK_METNI =
  "Her yedek, alındığı gün geçerli olan kurtarma anahtarının no'sunu taşır ve o anahtarla " +
  "açılır. Bugünden önce alınmış yedekler bu bilgisayarda yeni anahtarla da açılır; ama " +
  "başka bir bilgisayarda ya da güvenlik dosyası kaybolduğunda yalnız eski kurtarma " +
  "anahtarıyla açılır. O yedekler (USB bellektekiler dahil) duruyorsa eski kâğıdı atmayın: " +
  "“Eski anahtar — bugünden önceki yedekler için” diye işaretleyip ayrı saklayın.";

/** Dürüst sınır: yenileme ele geçmiş anahtara karşı koruma değildir (DEK değişmez). */
export const ELE_GECMIS_ANAHTAR_METNI =
  "Yenileme, başkasının eline geçmiş bir anahtara karşı koruma değildir: kayıtların " +
  "anahtarı değişmez; eski yedekler ve veri klasöründe “guvenlik-arsiv” adıyla saklanan " +
  "önceki güvenlik dosyası eski anahtarla açılabilir.";

/**
 * Yarım kalan kurulum (backend `resolve_interrupted_setup`: güvenlik durumu her
 * okunduğunda yarım kalan ilk hesabı ya tamamlar ya da geri alıp sihirbazı baştan açar;
 * ikisi de olmuyorsa kilit açılışı reddeder).
 */
export const YARIM_GECIS_METNI =
  "Program yöneticisi hesabının kurulumu yarıda kalmış görünüyor. Program bunu kendiliğinden " +
  "çözer; uyarı kalkmazsa programı kapatıp yeniden açın.";

/** Güvenlik dosyası kayıp ekranının başlığı (dosya yok ya da bozuk — ikisi aynı ekran). */
export const DOSYA_KAYIP_BASLIGI = "Güvenlik dosyası bulunamadı ya da okunamıyor";

/** Güvenlik dosyası kayıp ekranı: ne oldu? */
export const DOSYA_KAYIP_METNI =
  "Bu bilgisayarda program yöneticisi hesabı kurulmuş, ancak hesapların ve kayıtların " +
  "anahtarını saklayan güvenlik dosyası (guvenlik.json) veri klasöründe bulunamadı ya da " +
  "okunamıyor (boş ya da bozuk). Dosya olmadan kayıtlar açılamaz. Yeni hesap da " +
  "kurulamaz; kurulsaydı eski kayıtlar hiç okunamaz hâle gelirdi.";

/** Güvenlik dosyası kayıp ekranı: birinci çıkış yolu. */
export const DOSYA_KAYIP_GERI_KOY =
  "Dosyanın sağlam bir kopyası varsa (ör. bilgisayar taşınırken alınan veri klasörü " +
  "ya da USB bellekteki kopya) guvenlik.json dosyasını veri klasörüne geri koyun " +
  "(bozuk dosya varsa onun yerine), ardından “Yeniden denetle” düğmesine basın.";

/** Güvenlik dosyası kayıp ekranı: ikinci çıkış yolu (yedek başlığı yalnız kurtarma bölümünü taşır). */
export const DOSYA_KAYIP_YEDEKTEN =
  "Kopya yoksa aşağıdan bir yedeği geri yükleyin: geri yükleme güvenlik dosyasını yedeğin " +
  "kurtarma anahtarıyla yeniden oluşturur. Yedeğin alındığı gün geçerli olan kurtarma " +
  "anahtarı gerekir (listede her yedeğin anahtar no'su ve tarihi yazar); o yedekten sonra " +
  "girilen kayıtlar ekrandan kalkar. Program yeniden açılınca kilit ekranında kurtarma " +
  "anahtarıyla açıp program yöneticisinin yeni parolasını belirlersiniz.";

/** Güvenlik dosyası kayıp ekranı: üçüncü çıkış yolu (yalnız korunan veri yokken görünür). */
export const DOSYA_KAYIP_SIFIRLA_METNI =
  "Bu veritabanında kişi kaydı yok, kayıtların anahtarı veritabanına işlenmemiş ve yedek " +
  "klasöründe yedek bulunmuyor: okunamayan dosya korunan bir veriyi açmıyor. Dosyayı " +
  "kenara alıp kurulum sihirbazına dönebilirsiniz. Dosya silinmez, veri klasöründe " +
  "“guvenlik-arsiv” adıyla " +
  "kalır; program yöneticisi hesabı yeniden kurulur ve yeni bir kurtarma anahtarı verilir.";

/**
 * Hakkında'daki "Dürüst Sınırlar" kartı (tasarım §4.4.6; kılavuza da girer). Sade dille,
 * iç kod olmadan; yalnız bugün doğru olan söylenir (anahtar yenilemesinin eski zarfı
 * imha eden kolu ve ihlal dökümü sonraki fazlardadır, burada vaat edilmez).
 *
 * Denetim izi (F1b 1. adım, alt commit c): okul çekirdeğinin bütün yazmaları oturumdaki
 * hesabın adına denetim izine yazılır; tek istisna plan gereği 5. adımda yeniden yazılacak
 * katı silme ve birleştirmedir (öğrenci ve personelin sicilden silinmesi, iki kişi kaydının
 * birleştirilmesi — backend `test_izsiz_yazim.py` `MUAF_ISLEVLER`). Bu istisna metinde açıkça
 * yazar; istisna kalkınca cümle kısalır. Yedekten geri yükleme veritabanını değiştirdiği için
 * satırı ancak geri yüklemeden sonraki ilk girişte yazılır; uygulama içinden yapıldıysa satır
 * onu başlatan oturumun hesabını taşır (kurtarma anahtarı yolunda da; backend
 * `iz_dogrulama._geri_yukleme_satiri`), metin bunu da söyler. "Denetim izi değişikliği gösterir, önlemez" maddesi
 * tasarım §4.6.3 "Kalan risk"in sade dilidir: veritabanı kilit işaretiyle birlikte eski bir
 * kopyayla değiştirilirse program fark etmez, parolasını bilen biri zinciri program dışında
 * yeniden hesaplayabilir (tehdit 6); son katman kâğıda inen "Kayıt no · Zincir" satırıdır.
 * Kâğıt bugün kullanıcının elle not ettiğidir (Genel Bakış → Son Girişler); aylık bildirim
 * ve devir tutanağı gibi belgelere basılması sonraki fazlardadır, burada vaat edilmez.
 */
export const DURUST_SINIRLAR: readonly { baslik: string; metin: string }[] = [
  {
    baslik: "Rol bir şifreleme önlemi değildir.",
    metin:
      "Her hesap kendi parolasıyla kayıtların aynı anahtarını açar; roller arasındaki " +
      "ayrım programın içindedir. Hesapların asıl yararı, her işin kimin hesabıyla ve ne " +
      "zaman yapıldığını belli etmesidir.",
  },
  {
    baslik: "Şifreli alanlar en zayıf hesap parolası kadar korunur.",
    metin:
      "Güvenlik dosyası veritabanıyla aynı diskte durur ve her hesabın parolası kayıtların " +
      "anahtarını tek başına açar. Bilgisayarın tamamını korumak için disk şifrelemesi " +
      "gerekir: Windows'ta BitLocker, Pardus'ta LUKS.",
  },
  {
    baslik: "Açık oturum, sahibinin imzasıdır.",
    metin:
      "Oturum açıkken yapılan her iş o hesabın adına denetim izine yazılır (bugün tek " +
      "istisna: öğrenci ve personelin sicilden silinmesi ile iki kişi kaydının " +
      "birleştirilmesi). Yedekten geri yükleme, ardından yapılan ilk girişte, onu başlatan " +
      "hesapla birlikte yazılır. Bilgisayar başından kalkarken Kilitle'ye basın " +
      "(Ctrl+Shift+L); program boşta kalınca da kendiliğinden kilitlenir.",
  },
  {
    baslik: "Denetim izi değişikliği gösterir, önlemez.",
    metin:
      "Program her kaydı bir öncekine bağlayarak yazar ve kilit açılırken son kayıtları " +
      "denetler; program dışından yapılan değişikliği çoğu zaman fark edip Genel Bakış'ta " +
      "uyarır. Ama veritabanı, kilit işaretiyle birlikte eski bir kopyayla değiştirilirse " +
      "fark etmez; parolasını bilen biri de denetim izini programın dışında baştan " +
      "hesaplayabilir. Son katman kâğıttır: Genel Bakış'taki Son Girişler kartında yazan " +
      "“Kayıt no · Zincir” satırını zaman zaman tarihiyle birlikte kâğıda not edin.",
  },
  {
    baslik: "Kurtarma anahtarını yenilemek önceki yedekleri kapatmaz.",
    metin:
      "Yenilemeden önce alınmış yedekler eski anahtarla açılmayı sürdürür; eski kâğıt " +
      "“Eski anahtar” diye işaretlenip saklanır, atılmaz.",
  },
  {
    baslik: "Çıktı, programın dışına çıkınca korumadan da çıkar.",
    metin:
      "Kişisel veri içeren her Word, PDF ya da Excel dosyası programın dışına çıktığı anda " +
      "programın korumasından çıkar; onu saklamak ve silmek kullananın işidir.",
  },
  {
    baslik: "Kayıp ya da çalınmada bildirim programın işi değildir.",
    metin:
      "Bilgisayar, disk ya da USB bellekteki yedek kaybolur ya da çalınırsa kişisel " +
      "verilerin başkalarının eline geçmesini ilgililere ve Kişisel Verileri Koruma Kuruluna " +
      "en kısa sürede bildirmek veri sorumlusunun işidir (KVKK md. 12/5). Program bu " +
      "bildirimi yapmaz; durumu okul müdürlüğüne hemen iletin.",
  },
];

/** Şifreli Yedek kartının adı ve düğmesi (kullanıcı kararı 04.11.2026 "Ekran adları"). */
export const SIFRELI_YEDEK_KARTI_BASLIGI = "Şifreli Yedek";
export const SIFRELI_YEDEK_DUGMESI = "Şifreli yedeği kaydet";
/** Kaydetme penceresi açıkken ve yazım sürerken düğmenin etiketi (sözlük §3 "Süren iş"). */
export const SIFRELI_YEDEK_YER_SECILIYOR = "Yer seçiliyor…";
export const SIFRELI_YEDEK_KAYDEDILIYOR = "Şifreli yedek kaydediliyor…";

/** Kartın gövdesi: ne taşıdığı ve programın ne yaptığı (plan F1b-3; metin "indirilir" demez). */
export const SIFRELI_YEDEK_METNI =
  "Kayıtlar, ekler ve üretilen evrak tek dosyada toplanır ve güçlü şifrelemeyle korunur. Program " +
  "dosyayı sizin seçtiğiniz yere kaydeder, ardından yeniden açıp denetler. Şifresiz kopya " +
  "üretilmez; dosya hiçbir yere kendiliğinden gönderilmez.";

/** Yerin seçimi ve yedeğin açılışı (BSG Yön. md. 11/23; tasarım TK10). */
export const SIFRELI_YEDEK_YER_METNI =
  "Yer olarak USB belleği ya da okulun ağ diskini seçin; bulut depolama hizmetine yüklemeyin " +
  "(Bilgi ve Sistem Güvenliği Yönergesi 11/23). Yedek bu bilgisayarda program yöneticisinin " +
  "parolasıyla, başka bir bilgisayarda yalnız kurtarma anahtarıyla açılır; kurtarma anahtarı " +
  "belgesini okul müdürlüğünde kapalı zarfta saklayın.";

/** Hesap kurulmadan düğme kapalıdır. */
export const SIFRELI_YEDEK_HESAP_YOK =
  "Şifreli yedek oluşturabilmek için önce program yöneticisi hesabını kurmalısınız.";

/** Köprü yoksa (geliştirme kipi) düğme kapalıdır; bellek içi indirme yolu yoktur (plan F1b-3). */
export const SIFRELI_YEDEK_PENCERE_YOK =
  "Şifreli yedek yalnız programın kendi penceresinden kaydedilir.";

/** Yazım ve denetim sürerken (iş dakikalar sürebilir; denetim yerin okuma hızında koşar). */
export const SIFRELI_YEDEK_SURUYOR =
  "Şifreli yedek yazılıyor ve denetleniyor; bu iş birkaç dakika sürebilir.";

/**
 * Başarı: program dosyanın USB bellekte olduğunu bilemez, yalnız seçilen yere sağlam yazıldığını
 * bilir; metin "USB belleğe alındı" demez (kullanıcı kararı 04.11.2026).
 */
export const SIFRELI_YEDEK_YAZILDI = "Şifreli yedek seçilen yere yazıldı ve denetlendi.";

/** Sunucunun iletisi okunamayan hatanın metni. */
export const SIFRELI_YEDEK_KAYDEDILEMEDI = "Şifreli yedek kaydedilemedi.";

/** Yedek Raporu kartı (tasarım §9.7; kullanıcı kararı 04.11.2026 "Yedek raporu"). */
export const YEDEK_RAPORU_ADI = "Yedek Raporu";
export const YEDEK_RAPORU_METNI =
  "Bu bilgisayardaki yedeklerin tek sayfalık dökümü: türleri, tarihleri, yedekleri açan kurtarma " +
  "anahtarları ve son şifreli yedek. Kişi adı taşımaz; dosyası programda saklanmaz.";
export const YEDEK_RAPORU_KAYDEDILDI = "Yedek Raporu PDF olarak kaydedildi.";
export const YEDEK_RAPORU_HAZIRLANAMADI = "Yedek Raporu hazırlanamadı.";

/** Geri yükleme listesindeki türler (kullanıcı kararı 04.11.2026 "Ekran adları"). */
export const YEDEK_TURU_GUNLUK = "Günlük yedek";
export const YEDEK_TURU_GUNCELLEME = "Güncelleme öncesi yedek";
export const YEDEK_TURU_KURULUM = "Kurulum yedeği";

/** Yedeğin kapsamı; `desktop/backup.py` `KAPSAM_METINLERI` ile birebir (backend testi sınar). */
export const KAPSAM_YEREL_METNI = "yalnız kayıtlar; ekler bu bilgisayardan alınır";
export const KAPSAM_TAM_METNI = "kayıtlar, ekler ve üretilen evrak";

/** Listenin başlığı: bütün türler listededir, yalnız günlük yedek değil. */
export const YEDEK_LISTESI_BASLIGI = "Bu bilgisayardaki yedekler (en yeniden eskiye)";

/** Kenara alınan veritabanı 14 günlük rotasyondadır (tasarım §4.4.7): "silinmez" denmez. */
export const ONCEKI_VERITABANI_KENARA_ALINIR =
  "Mevcut veritabanı veri klasöründe “db-onceki-…” adıyla kenara alınır; 14 gün saklanır, sonra " +
  "silinir.";
export const ONCEKI_VERITABANI_KENARA_ALINDI =
  "Önceki veritabanı veri klasöründe “db-onceki-…” adıyla kenara alındı; 14 gün saklanır, sonra " +
  "silinir.";

/** Sunucunun gövde sınırını aşan yedek gönderilmez (kullanıcı kararı 06.11.2026). */
export const YEDEK_DOSYASI_COK_BUYUK = "Dosya çok büyük; en çok 8 GB olabilir.";

/** İstek sürerken kart söküldüyse ikinci düğme yoktur: durma iletisinin ardına bu cümle eklenir. */
export const EK_ONAYI_KART_DISINDA =
  "Onay için geri yüklemeyi Ayarlar → Güvenlik'teki Yedekten Geri Yükleme kartından yeniden başlatın.";

/**
 * Eksik ve bozuk ekler kişisiz listelenir (kullanıcı kararı 04.11.2026): kayıt türü ve numarası,
 * yükleme tarihi, boy. Satır konsoldakiyle aynı sıradadır (`geri_yukleme_ekleri.EkSatiri.metin`);
 * boy `formatBoyut` ile yazılır.
 */
export const EK_LISTESI_BASLIGI = "Eksik ya da bozuk ekler:";
export const EK_DURUMU_EKSIK = "Eksik";
export const EK_DURUMU_BOZUK = "Bozuk";
export const EK_YEDEKTE_YOKTU = "yedek alınırken bulunamadı ya da bozuktu";
export const EK_TARIHI_YOK = "tarih yok";

/** İkinci onayın düğmesi: kayıtlar bozuk ekler olmadan geri yüklenir (kullanıcı kararı 04.11.2026). */
export const EKLER_OLMADAN_GERI_YUKLE = "Ekler olmadan geri yükle";

/** "Ekler" satırı: yerine konan, geri alınan, eksik ya da bozuk ek yoksa. */
export const EK_SORUNU_YOK = "eksik ya da bozuk ek yok";
