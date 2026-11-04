// Geçici parola önerisi (plan F1b-2 "Geçici parola"): "Yeni hesap" ve "Parolayı sıfırla"
// pencerelerinde alan programın önerisiyle dolu gelir; program yöneticisi öneriyi değiştirebilir.
// Öneri bu bilgisayarda kurulur, sunucuya yalnız gönderilen değer gider (sunucu politikayı denetler).
//
// KURALLAR:
// * Politikaya uyar (`oturum/parolaPolitikasi.parolaSorunu`): küçük harf, büyük harf, rakam ve
//   simge her öneride en az birer tanedir; boşluk yoktur.
// * Uzunluk 12 karakterdir (`PAROLA_CUMLESI_EN_AZ`; plan: "en az 12 karakter").
// * Karışabilecek karakter yoktur: parola kâğıda elle yazılıp kapalı zarfta verilir, hesap
//   sahibi onu okuyup yazar. Çıkarılanlar: 0 ve 1 (O, o, Q; l, I, i ile karışır) ve onlarla
//   karışan harfler; 2, 5, 6, 8, 9 kalır, onlarla karışan Z, S, G, b, B, g, q çıkar; ! ve /
//   (1 ve l ile karışır); küçük t (elle yazılınca + ile, f ile de karışır); el yazısında büyüğü
//   ile küçüğü ayırt edilmeyen harfler (c j k m o p s u v w x y z, iki hâlde de); Türkçe ı, İ ve
//   ASCII dışı her harf. Simgeler Türkçe Q ve F klavyede AltGr'siz yazılır (+ % = * ? -).
// * Rastgelelik güvenli kaynaktandır (`crypto.getRandomValues`); `Math.random` kullanılmaz.
//   Sıra seçimi reddetmeli örneklemedir (modülo eğilimi yok); karıştırma Fisher-Yates.

import { PAROLA_CUMLESI_EN_AZ } from "../oturum/parolaPolitikasi";

/** Önerinin uzunluğu. */
export const GECICI_PAROLA_UZUNLUGU = PAROLA_CUMLESI_EN_AZ;

/** Önerinin karakter türleri (dosya başı "Karışabilecek karakter yoktur"). */
export const KUCUK_HARFLER = "adefhnr";
export const BUYUK_HARFLER = "ADEFHLNRT";
export const RAKAMLAR = "23456789";
export const SIMGELER = "+%=*?-";

/** Bütün öneri alfabesi (30 karakter; 12 karakterlik öneri ≈ 58,9 bit). */
export const ONERI_ALFABESI = KUCUK_HARFLER + BUYUK_HARFLER + RAKAMLAR + SIMGELER;

/** Öneride HİÇ bulunmayan, karışabilecek karakterler (test bu kümeyle sınar). */
export const KARISABILECEKLER = "0OoQ1lIiıİ!/tZSGbBgqCcJjKkMmPpsUuVvWwXxYyz";

/** Rastgele kaynak: diziyi rastgele 32 bitlik sayılarla doldurur (testte sabitlenir). */
export type RastgeleKaynak = (dizi: Uint32Array) => Uint32Array;

const guvenliKaynak: RastgeleKaynak = (dizi) => globalThis.crypto.getRandomValues(dizi);

/** Reddetmeli örneklemede ardışık ret sınırı (bozuk kaynak sonsuz döngüye sokmasın). */
const EN_COK_DENEME = 1_000;

/** `[0, n)` aralığında eğilimsiz rastgele sıra. */
export function rastgeleSira(n: number, kaynak: RastgeleKaynak = guvenliKaynak): number {
  const sinir = Math.floor(0x1_0000_0000 / n) * n;
  const kutu = new Uint32Array(1);
  for (let deneme = 0; deneme < EN_COK_DENEME; deneme += 1) {
    kaynak(kutu);
    if (kutu[0] < sinir) return kutu[0] % n;
  }
  throw new Error("Rastgele sayı üretilemedi.");
}

/** Politikaya uyan, karışabilecek karakter içermeyen 12 karakterlik geçici parola önerisi. */
export function geciciParolaOner(kaynak: RastgeleKaynak = guvenliKaynak): string {
  const turler = [KUCUK_HARFLER, BUYUK_HARFLER, RAKAMLAR, SIMGELER];
  const karakterler = turler.map((tur) => tur[rastgeleSira(tur.length, kaynak)]);
  while (karakterler.length < GECICI_PAROLA_UZUNLUGU) {
    karakterler.push(ONERI_ALFABESI[rastgeleSira(ONERI_ALFABESI.length, kaynak)]);
  }
  for (let i = karakterler.length - 1; i > 0; i -= 1) {
    const j = rastgeleSira(i + 1, kaynak);
    [karakterler[i], karakterler[j]] = [karakterler[j], karakterler[i]];
  }
  return karakterler.join("");
}
