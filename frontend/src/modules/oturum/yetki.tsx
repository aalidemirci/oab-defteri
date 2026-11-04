// Rol süzmesi (tasarım §4.4.2; plan F1b-2 "Ön yüz"). Süzmenin TEK kaynağı oturum özetindeki
// `hesap.yetenekler`'dir (`api.YETENEK_ADLARI`; değeri sunucu kurallardan türetir): ön yüz rol
// matrisini kopyalamaz, rol adıyla dallanmaz. Ekran, kart ve düğme "şu yetenek açık mı?" diye
// sorar (`useYetki().acik(ad)`); hangi rolün o yeteneği taşıdığını bilmez.
//
// SÜZME KULLANIM İÇİNDİR, GÜVENLİK DEĞİL: kapı sunucudadır (`RolMiddleware`, yetki kapısı; 403
// `rol_yetkisiz`). Gizlenen bir düğmeye yine de basılırsa (ör. özet bayatken) sunucunun iletisi
// "Bu işlem hesabınızın rolüne açık değil." çağıran ekranda görünür; `lib/api` aynı anda
// `od:rol-yetkisiz` olayını yayınlar, sağlayıcı da özeti yeniden okur ki süzme yetişsin.
//
// Durumlar:
// * `yukleniyor` — özet henüz okunmadı: hiçbir yetenek açık sayılmaz; rol kapısı (RolKapisi) ve
//   sekmesi yeteneğe bağlı sayfalar iskelet gösterir (ekran sıçramasın, yanlış sekme açılmasın).
// * `hazir` — özet okundu. Açık oturumda yalnız özetteki adlar açıktır; kilitliyken ve güvenlik
//   dosyası kayıpken hesap yoktur, hiçbiri açık değildir (ekranı zaten kilit kapısı örter).
//   KURULUM durumunda (hesap yok) SÜZME YAPILMAZ: her yetenek açık sayılır (`kurulum`); rol kapısı
//   o durumda devrede değildir ve sihirbaz ilk program yöneticisi hesabını kurar.
// * `okunamadi` — özet HİÇ okunamadı: fail-closed, hiçbir yetenek açık sayılmaz; rol kapısı
//   "rolünüze açık değil" demez, okunamadığını söyler. Özet bir kez okunduysa sonraki yoklama
//   hatası son bilinen yetenekleri düşürmez (`useOturum` ile aynı önbellek).
//
// Sağlayıcı (`YetkiSaglayici`) `App`'tedir ve oturum göstergesinin sorgusuyla AYNI önbelleği
// okur (yoklama aralığı içinde ikinci istek gitmez). Sağlayıcı yoksa değer `YUKLENIYOR`dur:
// hiçbir yazma denetimi açılmaz (fail-closed), testler sağlayıcıyı açıkça kurar.

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useMemo } from "react";
import type { ReactNode } from "react";

import { ROL_YETKISIZ_OLAYI } from "../../lib/api";
import { oturumApi } from "./api";
import type { OturumOzeti, YetenekAdi } from "./api";
import { OTURUM_SORGU_ANAHTARI, OTURUM_YOKLAMA_MS, yeteneklerOku } from "./useOturum";

export type YetkiDurumu = "yukleniyor" | "hazir" | "okunamadi";

export interface Yetki {
  durum: YetkiDurumu;
  /** Kurulum durumu (hesap yok): süzme yapılmaz, her yetenek açık sayılır. */
  kurulum: boolean;
  /** Yetenek açık mı? Yüklenirken ve okunamadıysa hayır (fail-closed); kurulumda evet. */
  acik: (ad: YetenekAdi) => boolean;
}

const hicbiri = () => false;

/** Özet henüz okunmadı (ve sağlayıcısız değer). */
export const YUKLENIYOR: Yetki = { durum: "yukleniyor", kurulum: false, acik: hicbiri };
/** Özet hiç okunamadı. */
export const OKUNAMADI: Yetki = { durum: "okunamadi", kurulum: false, acik: hicbiri };
/** Kurulum durumu: süzme yok. */
export const KURULUM: Yetki = { durum: "hazir", kurulum: true, acik: () => true };

/** Okunmuş bir özetin yetenekleri (açık oturum dışında boş liste verilir). */
export function hazirYetki(yetenekler: readonly string[]): Yetki {
  const kume = new Set(yetenekler);
  return { durum: "hazir", kurulum: false, acik: (ad) => kume.has(ad) };
}

/** Oturum özetinden yetki (dosya başı "Durumlar"). `okunamadi`: özet hiç okunamadı. */
export function yetkiKur(ozet: OturumOzeti | null | undefined, okunamadi: boolean): Yetki {
  if (ozet === null || ozet === undefined) return okunamadi ? OKUNAMADI : YUKLENIYOR;
  if (ozet.durum === "kurulum") return KURULUM;
  return hazirYetki(yeteneklerOku(ozet) ?? []);
}

const YetkiBaglami = createContext<Yetki>(YUKLENIYOR);

/** Testlerin ve sağlayıcının kullandığı ham bağlam sağlayıcısı (değer dışarıdan verilir). */
export const YetkiDegeri = YetkiBaglami.Provider;

/**
 * Uygulamanın yetki sağlayıcısı: oturum özetini (aynı önbellekten) okur ve süzmeyi bütün
 * ağaca verir. 403 `rol_yetkisiz` görülünce (`od:rol-yetkisiz`) özeti yeniden okutur; hatayı
 * çağıran ekran gösterir, sağlayıcı ileti çizmez.
 */
export function YetkiSaglayici({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const sorgu = useQuery({
    queryKey: OTURUM_SORGU_ANAHTARI,
    queryFn: () => oturumApi.ozet(false),
    staleTime: OTURUM_YOKLAMA_MS,
    retry: false,
  });
  const okunamadi = sorgu.data === undefined && sorgu.isError;
  const deger = useMemo(() => yetkiKur(sorgu.data, okunamadi), [sorgu.data, okunamadi]);

  useEffect(() => {
    const yenile = () => void queryClient.invalidateQueries({ queryKey: OTURUM_SORGU_ANAHTARI });
    window.addEventListener(ROL_YETKISIZ_OLAYI, yenile);
    return () => window.removeEventListener(ROL_YETKISIZ_OLAYI, yenile);
  }, [queryClient]);

  return <YetkiBaglami.Provider value={deger}>{children}</YetkiBaglami.Provider>;
}

/** Oturumdaki hesabın süzmesi (dosya başı). */
export function useYetki(): Yetki {
  return useContext(YetkiBaglami);
}
