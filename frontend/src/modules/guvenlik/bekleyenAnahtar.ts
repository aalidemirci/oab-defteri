// Doğrulanmayı bekleyen kurtarma anahtarı — ROTA AĞACININ DIŞINDA, modül belleğinde.
//
// Neden bileşen durumunda değil: anahtar sunucuda saklanmaz ve bir daha
// gösterilemez; kurulum, anahtarın saklandığı doğrulanmadan bitmez (tasarım §4.4.3).
// Sihirbaz sayfası anahtar ekrandayken sökülebilir: üst menüden bir bağlantıya
// tıklamak KurulumKapisi üzerinden sihirbazı sıfırdan açar; Ayarlar → Güvenlik'te
// yenilenen anahtar da sekme değişince sökülür. Anahtar bileşen durumunda dursaydı bu
// yollar onu sessizce silerdi. Burada tutulan anahtar sihirbaz (ya da Ayarlar →
// Güvenlik) yeniden açılınca geri gelir; iki grup yeniden doğrulanmadan ilerlenemez.
//
// KİLİT ANAHTARI SİLER. Kilitlenme pencereyi yeniden yükler (tasarım §13 D53; plan
// F1b-1 "Oturum"): modül belleği, bu anahtar da, gider. Bu yüzden Kilitle anahtar
// beklerken ÖNCE sorar (`oturum/useKilitle`); kilitlenirse sonra kâğıttaki anahtar
// doğrulanır ya da yenisi üretilir. Kurulum sihirbazı bitene dek boşta kilit yoktur
// (tasarım §13 D15); kurulumdan sonra yenilenip ekranda bekleyen anahtar boşta kilitte
// de gider ve aynı yola düşülür.
//
// Anahtar YALNIZ bellektedir: tarayıcı deposuna (localStorage, sessionStorage)
// YAZILMAZ — o, anahtarı diske düz metin olarak bırakırdı. Pencere kapanırsa ya
// da program çökerse anahtar gider: sihirbaz ve Güvenlik ekranı bu durumda
// "kâğıttaki anahtarı doğrula" ya da "yenisini üret" yolunu sunar (sunucudaki
// "saklandı" damgası yoktur). Sunucu damgayı yazınca bırakılır.
//
// SİHİRBAZDAKİ ARA DURUM: Ayarlar → Güvenlik anahtarı damga yazılır yazılmaz bırakır;
// sihirbaz ise panelin "Doğrulandı" iletisini göstermeyi sürer ve anahtarı ancak "Devam"
// (ya da adım rayı) ile bırakır. Bu arada damga yazılmıştır: kilitlenip yüklense de
// sihirbaz damgayı görür, kâğıdı yeniden sormaz. Bu yüzden sihirbaz damgayı burada
// işaretler (`bekleyenKurtarmaAnahtariDogrulandi`) ve Kilitle YALNIZ damgasız anahtar
// beklerken sorar (`kilitlemedenOnceSorulmali`; sözlük §4.4 "anahtar henüz
// doğrulanmadıysa").

import { useSyncExternalStore } from "react";

import type { KurtarmaKimligi } from "./api";

let bekleyen: string | null = null;
// Anahtarın kimliği (no + üretim günü; sır değildir): panel anahtarın yanında gösterir,
// kâğıda hangi no'nun yazıldığı belli olsun. Anahtarla birlikte yazılır ve bırakılır.
let bekleyenKimlik: KurtarmaKimligi | null = null;
// Bekleyen anahtarın sunucu damgası yazıldı mı? (dosya başı "sihirbazdaki ara durum")
let sunucudaDogrulandi = false;
const dinleyiciler = new Set<() => void>();

/** Bellekte bekleyen anahtar (yoksa null); damgası yazılmış olabilir. */
export function bekleyenKurtarmaAnahtari(): string | null {
  return bekleyen;
}

/**
 * Bekleyen anahtarın sunucu damgası yazıldı: anahtar bellekte kalır (sihirbaz "Devam"a
 * dek gösterir) ama artık kaybı bir şey yitirtmez. Anahtar yoksa etkisizdir.
 */
export function bekleyenKurtarmaAnahtariDogrulandi(): void {
  if (bekleyen !== null) sunucudaDogrulandi = true;
}

/**
 * Kilitlemeden (pencere yeniden yüklenmeden) önce sorulmalı mı? Yalnız saklandığı henüz
 * doğrulanmamış (damgasız) anahtar bellekte bekliyorsa: yükleme onu ekrandan kaldırır.
 */
export function kilitlemedenOnceSorulmali(): boolean {
  return bekleyen !== null && !sunucudaDogrulandi;
}

/** Bekleyen anahtarın kimliği (no, üretim günü); bilinmiyorsa ya da anahtar yoksa null. */
export function bekleyenKurtarmaKimligi(): KurtarmaKimligi | null {
  return bekleyenKimlik;
}

/**
 * Anahtarı (ve biliniyorsa kimliğini) bekletir; `null` ikisini birden bırakır. Dinleyen
 * bileşenler yeniden çizilir.
 */
export function bekleyenKurtarmaAnahtariniYaz(
  anahtar: string | null,
  kimlik: KurtarmaKimligi | null = null,
): void {
  const yeniKimlik = anahtar === null ? null : kimlik;
  if (bekleyen === anahtar && bekleyenKimlik === yeniKimlik) return;
  // Yeni (ya da bırakılan) anahtarın damgası henüz yoktur.
  if (bekleyen !== anahtar) sunucudaDogrulandi = false;
  bekleyen = anahtar;
  bekleyenKimlik = yeniKimlik;
  for (const dinleyici of dinleyiciler) dinleyici();
}

function abone(dinleyici: () => void): () => void {
  dinleyiciler.add(dinleyici);
  return () => {
    dinleyiciler.delete(dinleyici);
  };
}

/** Bekleyen anahtarı okuyan kanca (değişince bileşen yeniden çizilir). */
export function useBekleyenKurtarmaAnahtari(): string | null {
  return useSyncExternalStore(abone, bekleyenKurtarmaAnahtari, bekleyenKurtarmaAnahtari);
}

/** Bekleyen anahtarın kimliğini okuyan kanca. */
export function useBekleyenKurtarmaKimligi(): KurtarmaKimligi | null {
  return useSyncExternalStore(abone, bekleyenKurtarmaKimligi, bekleyenKurtarmaKimligi);
}
