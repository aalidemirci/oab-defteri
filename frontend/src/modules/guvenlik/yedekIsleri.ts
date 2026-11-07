// Süren yedek işleri — ROTA AĞACININ DIŞINDA, modül belleğinde (`bekleyenAnahtar` kalıbı).
//
// Neden bileşen durumunda değil: şifreli yedek dakikalar sürer, büyük yedeğin geri yüklemesi de
// öyle. Ayarlar sekmeleri koşullu çizilir; başka sekmeye ya da sayfaya geçmek kartı söker, istek
// sürer. Durum bileşende dursaydı dönüşte kart boşta görünür, düğme açılır, ikinci istek giderdi.
// Kartlar her çizimde buradan okur; isteği başlatan kart sökülmüş olsa da sonuç buraya yazılır.
//
// ŞİFRELİ YEDEK: aşama, son sonuç ve son hata tutulur; dönüşte kart üçünü de gösterir.
//
// GERİ YÜKLEME: yalnız "sürüyor" bayrağı tutulur. Parola, kurtarma anahtarı, seçilen dosyanın yolu
// ve File bu belleğe GİRMEZ: bileşenin durumundan çıkmazlar, kart sökülünce giderler; kart yeniden
// açılınca akış baştan yürür (sunucu da ikinci onay için bir şey saklamaz).
//
// KİLİT SİLER. Kilitlenme pencereyi yeniden yükler (tasarım §13 D53): bu bellek de gider, eski
// sonuç sonraki hesaba taşınmaz. Bu yüzden tarayıcı deposuna yazılmaz. Şifreli Yedek kartı kilitten
// sonra son denemeyi sunucudan okur (`SifreliYedekleme` "SON DENEME").

import { useSyncExternalStore } from "react";

import type { SifreliYedekSonucu } from "./api";

/** Düğmenin üç hâli: boşta, kaydetme penceresi açık, yedek yazılıyor. */
export type SifreliYedekAsamasi = "bos" | "yer" | "yazim";

export interface SifreliYedekIsi {
  asama: SifreliYedekAsamasi;
  /** Son başarılı kaydın sonucu; yeni yazım başlayınca ya da deneme düşünce silinir. */
  sonuc: SifreliYedekSonucu | null;
  /** Son denemenin hatası; yeni yazım başlayınca silinir, iptal silmez. */
  hata: string | null;
}

const BOSTA: SifreliYedekIsi = { asama: "bos", sonuc: null, hata: null };

/** Tek değerlik abone olunabilir bellek. */
function depoKur<T>(ilk: T) {
  let deger = ilk;
  const dinleyiciler = new Set<() => void>();
  return {
    oku: () => deger,
    yaz(yeni: T) {
      deger = yeni;
      for (const dinleyici of dinleyiciler) dinleyici();
    },
    abone(dinleyici: () => void) {
      dinleyiciler.add(dinleyici);
      return () => {
        dinleyiciler.delete(dinleyici);
      };
    },
    dinleniyor: () => dinleyiciler.size > 0,
  };
}

const sifreliYedek = depoKur(BOSTA);
const geriYukleme = depoKur(false);

/** Şifreli yedek işinin alanlarını değiştirir; verilmeyen alan kalır. */
export function sifreliYedekIsiniYaz(degisim: Partial<SifreliYedekIsi>): void {
  sifreliYedek.yaz({ ...sifreliYedek.oku(), ...degisim });
}

/**
 * Şifreli Yedek kartı şu an çizili mi? Çizili kart hatayı kalıcı satırda gösterir; çizili kart
 * yokken hatayı bildirim söyler (iki duyuru olmasın diye). Kancanın aboneliğine bakar: isteği
 * başlatan kart sökülüp yenisi takıldıysa da doğrudur.
 */
export function sifreliYedekKartiCizili(): boolean {
  return sifreliYedek.dinleniyor();
}

/** Şifreli yedek işini okuyan kanca. */
export function useSifreliYedekIsi(): SifreliYedekIsi {
  return useSyncExternalStore(sifreliYedek.abone, sifreliYedek.oku, sifreliYedek.oku);
}

/** Geri yükleme isteğinin sürüp sürmediğini yazar. */
export function geriYuklemeSuruyorYaz(suruyor: boolean): void {
  geriYukleme.yaz(suruyor);
}

/** Geri yükleme isteği sürüyor mu? */
export function useGeriYuklemeSuruyor(): boolean {
  return useSyncExternalStore(geriYukleme.abone, geriYukleme.oku, geriYukleme.oku);
}

/** Yalnız testler için: belleği ilk hâline döndürür. */
export function yedekIsleriniSifirla(): void {
  sifreliYedek.yaz(BOSTA);
  geriYukleme.yaz(false);
}
