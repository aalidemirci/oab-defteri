// Oturum sorgusu — oturum göstergesi (AppShell üst çubuğu) ve oturumu okuyan öteki
// bileşenler aynı react-query önbelleğini paylaşır; tek istek, tek doğruluk kaynağı.
// Aile iskeletinin kip sorgusunun (`useKip`) yerini alır (tasarım §12.B "kip → oturum").
//
// Yoklama periyodiktir ve `X-OD-Etkinlik` TAŞIMAZ (tasarım §4.4.3): zamanlayıcıyla giden
// istek oturumu canlı tutmamalıdır. Oturum arayüzün haberi olmadan kilitlenebilir (boşta
// süre sunucuda tembel dolar); bunu iki yol yakalar: bu yoklama ve 423 (`lib/api.ts` →
// `lib/kilit.ts`). Yoklama oturumu açık gördükçe ön yüz "açık sanır"; açık sanırken
// kilitli (ya da kayıp dosya) görürse bu boşta kilittir ve pencere yeniden yüklenir
// (tasarım §13 D53; `lib/kilit.ts`). Görsel geri sayım sıfırlanınca yoklama hemen yinelenir.
//
// Sorgu hatası FAIL-OPEN'dır (`ozet: null`): gerçek kapı backend'dedir
// (`apps/okul/lock_middleware`); arayüzü burada kilitlemek bir uç hatasında kullanıcıyı
// ekrandan atmak olurdu. Hata "açık sanma" bayrağına dokunmaz.

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef } from "react";

import { sonEtkinlikGonderimiAni } from "../../lib/api";
import { KILIT_KAPISI_OLAYI, kilitlendi, oturumAcikSan } from "../../lib/kilit";
import { oturumApi } from "./api";
import type { OturumDurumAdi, OturumOzeti } from "./api";
import { OTURUM_DEGISTI_OLAYI } from "./eylemler";

export const OTURUM_SORGU_ANAHTARI = ["oturum"] as const;

/** Oturum yoklamasının aralığı (ms). */
export const OTURUM_YOKLAMA_MS = 15_000;

/**
 * Etkinlik nabzı en sık bu aralıkla gider (ms). Kullanıcı uzun bir formu doldururken
 * (API isteği olmadan tuşlama) boşta süre dolmasın diye, GERÇEK bir etkileşimin ardından
 * ve son başlıklı istekten bu kadar zaman geçmişse oturum sorgusu bir kez başlıkla
 * gönderilir. Zamanlayıcıyla gitmez.
 */
export const NABIZ_ARALIGI_MS = 30_000;

export interface OturumBilgisi {
  /** Son okunan özet; okunamadıysa ya da henüz gelmediyse null. */
  ozet: OturumOzeti | null;
  /** Özetin alındığı an (`Date.now()` ölçeği). */
  alindi: number;
  /** Sunucuya yeniden sorar (etkinlik başlığı olmadan). */
  yenile: () => void;
  /** Bir oturum ucunun döndürdüğü özeti önbelleğe yazar. */
  ozetiYaz: (ozet: OturumOzeti) => void;
}

export function useOturum(): OturumBilgisi {
  const queryClient = useQueryClient();
  const sorgu = useQuery({
    queryKey: OTURUM_SORGU_ANAHTARI,
    queryFn: () => oturumApi.ozet(false),
    refetchInterval: OTURUM_YOKLAMA_MS,
    staleTime: 0,
    retry: false,
  });

  const yenile = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: OTURUM_SORGU_ANAHTARI });
  }, [queryClient]);

  const ozetiYaz = useCallback(
    (ozet: OturumOzeti) => queryClient.setQueryData(OTURUM_SORGU_ANAHTARI, ozet),
    [queryClient],
  );

  // Ön yüz oturumu kilitli bilirken gelen 423 (güvenlik kapısıyla birlikte) ve pencere
  // yüklenmeden açılan oturum (kurulumdaki ilk hesap): oturum hemen tazelenir.
  useEffect(() => {
    window.addEventListener(KILIT_KAPISI_OLAYI, yenile);
    window.addEventListener(OTURUM_DEGISTI_OLAYI, yenile);
    return () => {
      window.removeEventListener(KILIT_KAPISI_OLAYI, yenile);
      window.removeEventListener(OTURUM_DEGISTI_OLAYI, yenile);
    };
  }, [yenile]);

  // Boşta kilidin ön yüz ayağı (dosya başı notu). Her yeni özet bir kez değerlendirilir.
  const durum = sorgu.data?.durum;
  useEffect(() => {
    if (durum === undefined) return;
    if (durum === "acik") oturumAcikSan(true);
    else kilitlendi("yoklama");
  }, [durum, sorgu.dataUpdatedAt]);

  return {
    // Yoklama arada bir düşerse son bilinen durum korunur (ekran sıçramaz).
    ozet: sorgu.data ?? null,
    alindi: sorgu.dataUpdatedAt,
    yenile,
    ozetiYaz,
  };
}

/**
 * Açık oturumda gerçek etkileşimin ardından (en sık `NABIZ_ARALIGI_MS`'de bir) oturum
 * sorgusunu `X-OD-Etkinlik` ile gönderir. Başlığı `lib/api` ekler: etkileşim yakalama
 * evresinde kaydedildiği için bu istek "kullanıcı eylemi" sayılır. Yalnız bir yerde
 * (oturum göstergesi) takılır.
 */
export function useEtkinlikNabzi(
  durum: OturumDurumAdi | undefined,
  ozetiYaz: (o: OturumOzeti) => void,
) {
  const sonNabiz = useRef(Number.NEGATIVE_INFINITY);

  useEffect(() => {
    if (durum !== "acik") return;
    const nabiz = () => {
      const simdi = Date.now();
      const son = Math.max(sonNabiz.current, sonEtkinlikGonderimiAni());
      if (simdi - son < NABIZ_ARALIGI_MS) return;
      sonNabiz.current = simdi;
      oturumApi
        .ozet(true)
        .then(ozetiYaz)
        .catch(() => {
          /* nabız sessizdir; yoklama durumu zaten yeniler */
        });
    };
    window.addEventListener("pointerdown", nabiz);
    window.addEventListener("keydown", nabiz);
    return () => {
      window.removeEventListener("pointerdown", nabiz);
      window.removeEventListener("keydown", nabiz);
    };
  }, [durum, ozetiYaz]);
}

/**
 * Görsel geri sayım: boşta kilide kalan saniye. Yalnız GÖRSELDİR; karar her istekte
 * sunucuda verilir. Mutlak süre yoktur (TK14). Özetten sonra başlıklı bir istek
 * gittiyse sunucu boşta sayacını tazelemiştir. Açık oturum dışında, kilit beklerken ve
 * kurulum sürerken (sunucu `bosta_kalan_sn: null` verir; tasarım §13 D15) boştur.
 */
export function kalanSaniye(
  ozet: OturumOzeti,
  alindi: number,
  simdi: number,
  sonGonderim: number,
): number | null {
  if (ozet.durum !== "acik" || ozet.bosta_kalan_sn === null) return null;
  const gecen = (simdi - alindi) / 1000;
  let bosta = ozet.bosta_kalan_sn - gecen;
  if (sonGonderim > alindi) {
    bosta = Math.max(bosta, ozet.bosta_dk * 60 - (simdi - sonGonderim) / 1000);
  }
  return Math.max(0, Math.ceil(bosta));
}

/** Saniye → "d:ss" (ör. 161 → "2:41"). */
export function sureBicimle(saniye: number): string {
  const dk = Math.floor(saniye / 60);
  const sn = saniye % 60;
  return `${dk}:${String(sn).padStart(2, "0")}`;
}
