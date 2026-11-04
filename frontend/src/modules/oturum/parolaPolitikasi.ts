// Parola politikası — arayüzdeki ön denetim ve yerel güç göstergesi (tasarım TK15, §15
// M-4; plan F1b-1 "Parola ve hatalı deneme"). OTORİTE BACKEND'DİR
// (`apps/okul/services/hesap_kurallari.py::validate_password`): buradaki denetim yalnız
// gereksiz istek ve bekleme olmasın diye aynı kuralı ÖNCEDEN söyler; iletiler oradakiyle
// birebir aynıdır. Kural değişirse iki yer birlikte değişir.
//
// * En az 8, en çok 128 karakter (BSG Yön. md. 9/2-a).
// * Küçük harf, büyük harf, rakam ve simge zorunludur (BSG Yön. md. 9/2-b; v1'de ayarı yok).
//   Türkçe harfler harf sayılır (ç ğ ı ö ş ü küçük; Ç Ğ İ Ö Ş Ü büyük): denetim Unicode
//   özellikleriyledir, ASCII aralığıyla değil. Simge harf, rakam ve boşluk dışındaki
//   her karakterdir; parola cümlesindeki ara boşluk serbesttir ama simge sayılmaz.
// * Parola KIRPILMAZ; başında ya da sonunda boşluk olan parola kabul edilmez.
// * Yeni parola eskisiyle aynı olamaz (tasarım §4.4.5).
//
// Karakter türleri Python'un tanımıyla BİREBİRDİR (ön denetim backend'den ne katı ne
// gevşek olsun): küçük harf `str.islower` = Unicode "Lowercase" özelliği (ª da sayılır),
// büyük harf `str.isupper` = "Uppercase" (Ⅷ da sayılır), rakam `str.isdecimal` = onluk
// rakam `Nd` (², ① sayılmaz), boşluk `str.isspace` (aşağıdaki küme: U+001C-001F ve
// U+0085 dâhil, U+FEFF hariç; JS `trim` ve `\s` bundan farklı olduğu için kullanılmaz).
// Ortak vaka tablosu backend `test_hesaplar.py` ile `parolaPolitikasi.test.ts`'tedir.
//
// Güç göstergesi yerel kuraldır (uzunluk + karakter türleri; yeni bağımlılık yok) ve
// 12 karakterlik parola cümlesi önerilir. Gösterge sunucunun kararı değildir.

export const PAROLA_EN_AZ = 8;
export const PAROLA_EN_COK = 128;
/** Önerilen parola cümlesinin uzunluğu (organ hesabına önerilir; plan F1b-1). */
export const PAROLA_CUMLESI_EN_AZ = 12;

/** Alanın altındaki kısa kural metni (sözlük §1 "Parola"). */
export const PAROLA_KURALI_METNI =
  `En az ${PAROLA_EN_AZ} karakter; küçük harf, büyük harf, rakam ve simge içerir. ` +
  "Başında ve sonunda boşluk olamaz.";

/** Parola cümlesi önerisi (yerel öneri; zorunlu değildir). */
export const PAROLA_CUMLESI_ONERISI =
  `Akılda kalan bir parola cümlesi seçin: en az ${PAROLA_CUMLESI_EN_AZ} karakter, ` +
  "birkaç sözcük, araya bir rakam ve bir simge.";

// Backend iletileriyle BİREBİR (hesap_kurallari.py; app_password._SAME_PASSWORD_MESSAGE).
export const KENAR_BOSLUGU_ILETISI = "Parolanın başında ya da sonunda boşluk olamaz.";
export const KISA_ILETISI = `Parola en az ${PAROLA_EN_AZ} karakter olmalıdır.`;
export const UZUN_ILETISI = `Parola en çok ${PAROLA_EN_COK} karakter olabilir.`;
export const AYNI_PAROLA_ILETISI = "Yeni parola eskisiyle aynı olamaz.";
export const ESLESMEDI_ILETISI = "Parolalar eşleşmedi.";

const KUCUK = /\p{Lowercase}/u;
const BUYUK = /\p{Uppercase}/u;
const RAKAM = /\p{Nd}/u;
/** Python `str.isspace` kümesi (CPython 3.12, Unicode 15; dosya başı notu). */
const BOSLUK =
  "\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
/** Başta ya da sonda boşluk (Python: `parola != parola.strip()`). */
const KENAR_BOSLUGU = new RegExp(`^[${BOSLUK}]|[${BOSLUK}]$`, "u");
/** Harf, rakam ve boşluk dışındaki karakter (Python: `not isalnum() and not isspace()`). */
const SIMGE = new RegExp(`[^\\p{L}\\p{N}${BOSLUK}]`, "u");

/** Karakter sayısı kod noktasıyla (Python `len` gibi; vekil çiftler tek sayılır). */
function uzunluk(parola: string): number {
  return [...parola].length;
}

/** Eksik karakter türleri, iletideki sırayla. */
export function eksikTurler(parola: string): string[] {
  const eksik: string[] = [];
  if (!KUCUK.test(parola)) eksik.push("küçük harf");
  if (!BUYUK.test(parola)) eksik.push("büyük harf");
  if (!RAKAM.test(parola)) eksik.push("rakam");
  if (!SIMGE.test(parola)) eksik.push("simge");
  return eksik;
}

/**
 * Parolanın politikaya uymayan İLK yönü (backend'in sırasıyla) ya da null. `eski`
 * verilirse yeni parolanın eskisiyle aynı olmaması da denetlenir.
 */
export function parolaSorunu(parola: string, eski?: string): string | null {
  if (KENAR_BOSLUGU.test(parola)) return KENAR_BOSLUGU_ILETISI;
  const boy = uzunluk(parola);
  if (boy < PAROLA_EN_AZ) return KISA_ILETISI;
  if (boy > PAROLA_EN_COK) return UZUN_ILETISI;
  const eksik = eksikTurler(parola);
  if (eksik.length > 0) {
    return `Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: ${eksik.join(", ")}.`;
  }
  if (eski !== undefined && eski !== "" && parola === eski) return AYNI_PAROLA_ILETISI;
  return null;
}

/** Yeni parola alanlarının ayrı ayrı hataları (her ileti kendi alanının altında çıkar). */
export interface YeniParolaHatalari {
  /** Politika (ve eskisiyle aynılık) — "Yeni parola" alanının sorunu. */
  yeni: string | null;
  /** Eşleşme — "Parola (tekrar)" alanının sorunu. */
  tekrar: string | null;
}

/**
 * Ön denetimin alan alan sonucu: politika sorunu ilk alana, eşleşmeme tekrar alanına
 * yazılır (hata hangi alandaysa o alan işaretlensin; ikisi birden olabilir).
 */
export function yeniParolaHatalari(
  yeni: string,
  tekrar: string,
  eski?: string,
): YeniParolaHatalari {
  return {
    yeni: parolaSorunu(yeni, eski),
    tekrar: yeni === tekrar ? null : ESLESMEDI_ILETISI,
  };
}

export type ParolaGucuDuzeyi = 0 | 1 | 2 | 3 | 4;

export interface ParolaGucu {
  /** 0: boş · 1: kurala uymuyor · 2: kurala uyuyor · 3: parola cümlesi boyu · 4: uzun cümle. */
  duzey: ParolaGucuDuzeyi;
  /** Ekrandaki ad ("Zayıf", "Orta", "İyi", "Güçlü"); boşta "". */
  etiket: string;
}

const GUC_ETIKETLERI: Record<ParolaGucuDuzeyi, string> = {
  0: "",
  1: "Zayıf",
  2: "Orta",
  3: "İyi",
  4: "Güçlü",
};

/** Yerel güç kuralı: uzunluk + karakter türleri (dosya başı notu). */
export function parolaGucu(parola: string): ParolaGucu {
  let duzey: ParolaGucuDuzeyi;
  if (parola === "") duzey = 0;
  else if (parolaSorunu(parola) !== null) duzey = 1;
  else if (uzunluk(parola) < PAROLA_CUMLESI_EN_AZ) duzey = 2;
  else if (uzunluk(parola) < PAROLA_CUMLESI_EN_AZ + 4) duzey = 3;
  else duzey = 4;
  return { duzey, etiket: GUC_ETIKETLERI[duzey] };
}
