// Hesap kuralları — tanıtıcı ve ad-soyad için arayüzdeki ön denetim (tasarım §4.4.4;
// plan F1b-1 "Parola ve hatalı deneme"). OTORİTE BACKEND'DİR
// (`apps/okul/services/hesap_kurallari.py`): buradaki denetim yalnız gereksiz istek
// olmasın ve uyarı gönderimden ÖNCE görünsün diye aynı kuralı önceden söyler; iletiler
// oradakiyle birebir aynıdır. Kural değişirse iki yer birlikte değişir. Parola kuralı
// ayrı dosyadadır (`parolaPolitikasi.ts`).
//
// TANITICI: kilit ekranında herkese görünen hesap adıdır, gerçek ad olmaz. Varsayılanı
// rolden türer (`yonetici`, `yonetici-2`, `muhasip`, `dk-1`). Baştaki ve sondaki boşluk
// atılır, Türkçe küçük harfe çevrilir ("I" → "ı", "İ" → "i"; backend `tr_lower`).
//
// UYARI, ENGEL DEĞİL (altın kural 3; backend `login_name_warning`), iki hâl, öncelik sırasıyla:
// 1. Tanıtıcıda T.C. kimlik numarasına benzeyen 11 ardışık rakam (orkestratör maddesi F-5; K9:
//    kimlik numarası kilit ekranında hiç görünmemeli). Sayının sağlaması aranmaz.
// 2. Tanıtıcı ad-soyaddaki üç harften uzun bir sözcüğü içeriyor. Karşılaştırma Türkçe harfleri
//    ASCII'ye katlayarak yapılır ("Şükrü" ≡ "sukru"; backend `excel_ogrenci.normalize_header`):
//    `sukru.k` de ŞÜKRÜ adını açık eder. Üç harfli sözcük ("Ali", "Can") aranmaz; yoksa rolden
//    türeyen tanıtıcılar da sık sık uyarı verirdi.
// İkisi birden varsa kimlik numarasının uyarısı gelir. Ortak vaka tablosu backend
// `test_hesaplar.py::TestTaniticiKurallari` ile `hesapKurallari.test.ts`'tedir.

/** İlk program yöneticisi hesabının varsayılan tanıtıcısı (tasarım §4.4.4). */
export const TANITICI_VARSAYILAN = "yonetici";
export const TANITICI_EN_COK = 32;
export const AD_SOYAD_EN_COK = 150;
/** Uyarıda aranan ad sözcüğünün en kısa boyu (üç harften uzun). */
const AD_SOZCUGU_EN_AZ = 4;

// Backend iletileriyle BİREBİR (hesap_kurallari.py).
export const TANITICI_BOS_ILETISI = "Tanıtıcı boş olamaz.";
export const TANITICI_GECERSIZ_ILETISI =
  `Tanıtıcı 2-${TANITICI_EN_COK} karakter olmalıdır; küçük harfle başlar, küçük ` +
  "harf, rakam, nokta, tire ya da alt çizgi içerir.";
export const AD_SOYAD_BOS_ILETISI = "Hesap sahibinin adı-soyadı boş olamaz.";
export const AD_SOYAD_UZUN_ILETISI = `Hesap sahibinin adı-soyadı en çok ${AD_SOYAD_EN_COK} karakter olabilir.`;
export const TANITICI_UYARISI =
  "Tanıtıcı hesap sahibinin adını içeriyor. Tanıtıcı kilit ekranında herkese görünür; " +
  "rolden türeyen bir tanıtıcı seçmeniz önerilir.";
/** Backend `LOGIN_NAME_TCKN_WARNING_MESSAGE` ile BİREBİR. */
export const TANITICI_TCKN_UYARISI =
  "Tanıtıcı T.C. kimlik numarasına benzeyen 11 haneli bir sayı içeriyor. Tanıtıcı kilit " +
  "ekranında herkese görünür; rolden türeyen bir tanıtıcı seçmeniz önerilir.";

/** 11 ardışık ASCII rakamı (backend `_TCKN_BENZERI = [0-9]{11}`; tanıtıcının rakamı yalnız ASCII'dir). */
const TCKN_BENZERI = /[0-9]{11}/;

/** Tanıtıcı alanının altındaki kural metni (sözlük §1 "Hesap"). */
export const TANITICI_KURALI_METNI =
  "Kilit ekranında herkese görünen hesap adıdır; gerçek ad yazılmaz. Küçük harfle başlar; " +
  "küçük harf, rakam, nokta, tire ya da alt çizgi içerir.";

const TANITICI_DESENI = /^[a-zçğıöşü][a-zçğıöşü0-9._-]{1,31}$/;

/** Türkçe-duyarlı küçük harf (backend `shared.text.tr_lower`: I → ı, İ → i). */
export function trKucuk(deger: string): string {
  return deger.replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase();
}

/** Tanıtıcının saklanacağı biçim: kenar boşluğu atılmış, Türkçe küçük harf. */
export function taniticiNormallestir(deger: string): string {
  return trKucuk(deger.trim());
}

/** Tanıtıcı kurala uymuyorsa iletisi, uyuyorsa null (backend `validate_login_name`). */
export function taniticiSorunu(deger: string): string | null {
  const tanitici = taniticiNormallestir(deger);
  if (tanitici === "") return TANITICI_BOS_ILETISI;
  return TANITICI_DESENI.test(tanitici) ? null : TANITICI_GECERSIZ_ILETISI;
}

/** Ad-soyadın saklanacağı biçim: ara boşluklar teke iner, kenarlar atılır. */
export function adSoyadNormallestir(deger: string): string {
  return deger.split(/\s+/).filter(Boolean).join(" ");
}

/** Ad-soyad kurala uymuyorsa iletisi, uyuyorsa null (backend `validate_display_name`). */
export function adSoyadSorunu(deger: string): string | null {
  const ad = adSoyadNormallestir(deger);
  if (ad === "") return AD_SOYAD_BOS_ILETISI;
  // Karakter sayısı kod noktasıyla (Python `len` gibi).
  return [...ad].length > AD_SOYAD_EN_COK ? AD_SOYAD_UZUN_ILETISI : null;
}

// Backend `excel_ogrenci._TR_MAP`: Türkçe harf → ASCII (büyük ve küçük aynı harfe).
const TR_ASCII: Record<string, string> = {
  ş: "s",
  Ş: "s",
  ı: "i",
  I: "i",
  İ: "i",
  ğ: "g",
  Ğ: "g",
  ü: "u",
  Ü: "u",
  ö: "o",
  Ö: "o",
  ç: "c",
  Ç: "c",
};

/**
 * Karşılaştırma biçimi (backend `normalize_header`): Türkçe harfler ASCII'ye katlanır,
 * küçük harfe çevrilir, harf ve rakam dışındaki her dizi tek boşluk olur.
 * "Şükrü ÖZTÜRK" → "sukru ozturk"; "sukru.k" → "sukru k".
 */
export function asciiKatla(deger: string): string {
  return deger
    .replace(/[şŞıIİğĞüÜöÖçÇ]/g, (harf) => TR_ASCII[harf])
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/**
 * Tanıtıcının kişisel veri uyarısı, yoksa null (backend `login_name_warning`; dosya başı notu):
 * önce 11 ardışık rakam (ad-soyad boş olsa da), sonra ad-soyaddaki üç harften uzun bir sözcük.
 * Engel değildir.
 */
export function taniticiUyarisi(tanitici: string, adSoyad: string): string | null {
  if (TCKN_BENZERI.test(tanitici)) return TANITICI_TCKN_UYARISI;
  const katli = asciiKatla(tanitici).replace(/ /g, "");
  if (katli === "") return null;
  for (const sozcuk of asciiKatla(adSoyad).split(" ")) {
    if (sozcuk.length >= AD_SOZCUGU_EN_AZ && katli.includes(sozcuk)) return TANITICI_UYARISI;
  }
  return null;
}
