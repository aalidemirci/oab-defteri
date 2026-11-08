// Okul kartının ekran metinleri — tek kaynak (F1b 4. adım; genel tasarım §5.1 "`SchoolConfig`'e
// eklenen OAB alanları"). Kurulum sihirbazının 2. ve 3. adımı, Ayarlar → Okul Bilgileri ve
// Genel Bakış'taki başlangıç yol haritası buradan okur. Sözlük testi (`docs/sozluk.md`) bu
// sabitleri kaynaktan okur: dizeler düz yazılır (tek satır ya da `"…" + "…"`; şablon dizesi yok).
//
// Altın kural 2: oranlar ve eşikler (öğrenci mevcudunun eşiği, arz bedeli ve pay oranları) okul
// kartında yazılmaz; yardım metni yalnız alanın hangi hesaba girdiğini ve maddesini söyler (kural
// paketi F1c'de). Madde numaraları OAB Yönetmeliğinindir (`docs/mevzuat/`).

/** Okul adımının (sihirbaz 2. adım) ve Okul Bilgileri sekmesinin açıklaması. */
export const OKUL_KARTI_ACIKLAMASI =
  "Bu bilgiler programın bastığı evrakın antedinde ve birliğin hesaplarında (genel kurul yeter " +
  "sayısı, kantin arz bedeli ve pay dağılımı) kullanılır.";

/** Antette okul adı birim satırındadır ("<Okul Adı> Müdürlüğü"; `shared/letterhead.py`, RYUE md. 10/3). */
export const OKUL_ADI_YARDIMI = "Evrak antedinde “… Müdürlüğü” satırında görünür.";

export const KURUM_KODU_YARDIMI = "MEB kurum kodu; altı haneli.";

export const KADEME_YARDIMI = "Birden çok kademesi olan kurumda hepsini seçin.";

/** md. 9/2: genel kurulun toplantı yeter sayısı öğrenci mevcuduna göre hesaplanır. */
export const MEVCUT_YARDIMI = "Genel kurulun toplantı yeter sayısının hesabına girer (md. 9/2).";

export const MEVCUT_TARIHI_YARDIMI = "Sayının alındığı gün.";

/** md. 17/1-a-2: kantin gelirinin pay dağılımı yerleşim türüne göre. */
export const YERLESIM_YARDIMI = "Kantin gelirinin pay dağılımı buna göre yapılır (md. 17/1).";

/** md. 17/1-a-1, 17/1-b-1: arz bedeli işletme biçimine göre. */
export const KANTIN_YARDIMI =
  "Kantin ve benzeri yerlerin arz bedeli buna göre hesaplanır (md. 17/1).";

/**
 * Kantin birlikçe işletiliyorsa seçimin altında görünen bilgi (md. 23/3; tasarım §6.4.8
 * `kantin.isletmede_vergi_uyarisi`). Uyarıdır, engel değildir.
 */
export const KANTIN_ISLETME_BILGISI =
  "Kantin ve benzeri yerler birlikçe işletilir ve vergi mükellefiyeti doğarsa birlik hakkında " +
  "213 sayılı Vergi Usul Kanunu hükümleri uygulanır (md. 23/3).";

/** K3 ve md. 6/1-d: personel modülü yalnız doğrudan işverende açılır. */
export const PERSONEL_YARDIMI =
  "Birliğin istihdam ettiği personel için kıdem tazminatı karşılığı ayrılır (md. 6/1-d).";

export const KAMPUS_ETIKETI = "Okul bir eğitim kampüsündedir.";

/** md. 2/1 (tanım) ve 13/7. */
export const KAMPUS_YARDIMI =
  "Kampüsteki okulda, ihtiyaç hâlinde kampüs yönetimine birliği temsilen başkan ya da yönetim " +
  "kurulu üyelerinden biri görevlendirilir (md. 13/7).";

/**
 * Veri sorumlusu alanı (F1b 5. adım; KVKK md. 10/1-a, E04). Örnek uydurmadır; aydınlatma metni
 * personel ve veli listesi aktarım ekranlarındadır (`kisiler/metinler.ts`).
 */
export const VERI_SORUMLUSU_ETIKETI = "Veri sorumlusu";
export const VERI_SORUMLUSU_YARDIMI =
  "Okul müdürlüğünce belirlenir; personel ve veli listesi aktarım ekranlarındaki aydınlatma " +
  "metninde görünür. Örnek: Örnek Anadolu Lisesi Müdürlüğü, Örnek Mah. Örnek Sok. No: 1, " +
  "Örnek İlçe.";

/** md. 9/1: yeni açılan okulda ilk genel kurulun süresi açılış tarihinden sayılır. */
export const ACILIS_YARDIMI =
  "Yalnız yeni açılan okulda doldurun; ilk genel kurulun süresi bu tarihten sayılır (md. 9/1).";

/** Başlangıç yol haritasının `okul_karti` maddesi (tasarım §7.10 "okul kartının eksik alanları"). */
export const OKUL_KARTI_YOL_HARITASI_BASLIGI = "Okul bilgilerini tamamlayın";
export const OKUL_KARTI_YOL_HARITASI_ACIKLAMASI =
  "Okul Bilgileri'nin zorunlu alanları (il, ilçe, kurum kodu, kademe, öğrenci mevcudu, yerleşim " +
  "türü, kantin ve personel çalıştırma biçimi) evrakın antedinde ve birliğin hesaplarında " +
  "kullanılır.";

/**
 * Sihirbazın 3. adımındaki ders yılı kartının ilk cümlesi: dönemler md. 13/10'un dönemlik
 * gelir-gider duyurusunun ve kantin sözleşmesinin (EK-2 md. 4) yarıyıl ayının takvimidir.
 */
export const DERS_YILI_ACIKLAMASI =
  "Dönemlik gelir-gider duyurusu (md. 13/10) ve kantinde yarıyıl ayının yarım kirası (EK-2 md. 4) " +
  "aktif ders yılının dönemlerinden okunur.";
