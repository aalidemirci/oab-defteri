// Genel Bakış'ın bütünlük kartlarının durumu: rolün açabildiği uçlar (`yetki`; oturum
// özetinin yeteneklerinden, `butunlukYetkisi`) sayfa açılınca TEK kez okunur (kullanıcı eylemi
// değil) ve tek bileşik durumda birleşir (`butunlukApi.durum`, `birlestir`). Yetki henüz
// bilinmiyorsa (oturum özeti yükleniyor) hiçbir uç çağrılmaz; rolün açamadığı uç hiç çağrılmaz.
// Kartlar aynı durumdan beslenir; sahipsiz parola kaydının silinmesi güncel iki depo kartını
// döndürür, çağıran `ikiDepoyuYaz` ile yerine koyar (mührü tutmayan hesaplar korunur). Geri
// yükleme kartının "Gördüm"ü güncel denetim kartlarını döndürür (`denetimiYaz`; iki depo kaydı
// korunur); kartın gösterdiği geri yükleme artık güncel değilse uçlar yeniden okunur (`yenile`).
//
// OKUNAMAZSA GİZLENMEZ (fail-closed): uyarı kartları denetim izinin bulgusunu taşır; okuma
// beklenmedik biçimde düşerse (sunucu hatası, ağ) `okunamadi` doğru olur ve Genel Bakış
// "Bütünlük Durumu Okunamadı" kartını gösterir — bir uyarı sessizce kaybolmaz. Oturum
// kilitliyken (423) ya da anahtar düşmüşken (409) kart yoktur: kilit ekranı gelir. Backend tek
// kartın hatasını öteki kartlara yaymaz, adını o ucun `okunamayan`'ına yazar (aynı uyarı
// kartı). Eksik alanlı yanıt (eski sürüm, beklenmeyen gövde) kartları düşürmez: eksik liste
// boş, eksik nesne null sayılır (`duzenle`).
//
// YETKİ OKUNAMAZSA (oturum özeti düştü, `yetkiHatasi`; aynı 423/409 kuralı): `okunamadi` yine
// doğrudur — denetim kartlarının bu role açık olup olmadığı bilinmez, bir uyarı sessizce
// kaybolmamalıdır. Yalnız her role açık kendi kartları okunur ("Son Girişler"); denetim ve iki
// depo uçları yetenek bilinmeden çağrılmaz (süzmenin kaynağı yeteneklerdir, plan F1b-2).
// Özet sonradan okununca kart kalkar ve rolün uçları okunur.

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../lib/api";
import { butunlukApi, denetimiBirlestir, ikiDepoyuBirlestir } from "./api";
import type {
  ButunlukDurumu,
  ButunlukYetkisi,
  DenetimKartlari,
  GeriYuklemeOzeti,
  IkiDepoYaniti,
} from "./api";

export interface ButunlukDurumuKancasi {
  durum: ButunlukDurumu | null;
  /** Durum okunamadı (kilit ve anahtar dışındaki bir hata): uyarı kartı gösterilir. */
  okunamadi: boolean;
  /** Sahipsiz kaydın silinmesinden dönen iki depo kartını duruma yazar. */
  ikiDepoyuYaz: (yanit: IkiDepoYaniti) => void;
  /** Geri yükleme kartının "Gördüm"ünden dönen denetim kartlarını duruma yazar. */
  denetimiYaz: (yanit: DenetimKartlari) => void;
  /** Rolün uçlarını yeniden okur (kartın gösterdiği geri yükleme artık güncel değilse). */
  yenile: () => void;
}

/** Geri yükleme kartı; eski yanıtta öncekiler listesi yoksa boş. */
function geriYukleme(geri: GeriYuklemeOzeti | null | undefined): GeriYuklemeOzeti | null {
  if (geri === null || geri === undefined || typeof geri !== "object") return null;
  return {
    ...geri,
    onceki_geri_yuklemeler: Array.isArray(geri.onceki_geri_yuklemeler)
      ? geri.onceki_geri_yuklemeler
      : [],
  };
}

/** Bileşik durumu kartların beklediği biçime getirir; nesne değilse null. */
export function duzenle(yanit: unknown): ButunlukDurumu | null {
  if (yanit === null || typeof yanit !== "object") return null;
  const d = yanit as Partial<ButunlukDurumu>;
  return {
    butunluk: Array.isArray(d.butunluk) ? d.butunluk : [],
    geri_yukleme: geriYukleme(d.geri_yukleme),
    iki_depo: d.iki_depo ?? null,
    kagit_capasi: d.kagit_capasi ?? null,
    son_girisler: Array.isArray(d.son_girisler) ? d.son_girisler : [],
    parola_yenilenme: d.parola_yenilenme ?? null,
    okunamayan: Array.isArray(d.okunamayan) ? d.okunamayan : [],
  };
}

/** Okuma hatası kartla söylenir mi? Kilit (423) ve düşen anahtar (409) söylenmez. */
export function okunamadiSayilir(hata: unknown): boolean {
  return !(hata instanceof ApiError && (hata.status === 423 || hata.status === 409));
}

/**
 * `yetki`: rolün açabildiği bütünlük uçları; `null` → oturum özeti okunmadı. `yetkiHatasi`:
 * özet okunamadıysa okuma hatası (yükleniyorsa null; `useYetenekler().hata`). Yetki yükleniyorsa
 * hiçbir uç çağrılmaz; okunamadıysa yalnız kendi kartları okunur ve `okunamadi` doğrudur
 * (dosya başı). Yetki yalnız değeri değişince yeniden okunur (özetin her yoklaması değil).
 */
export default function useButunlukDurumu(
  yetki: ButunlukYetkisi | null,
  yetkiHatasi: unknown = null,
): ButunlukDurumuKancasi {
  const [durum, setDurum] = useState<ButunlukDurumu | null>(null);
  const [okunamadi, setOkunamadi] = useState(false);
  // Yeniden okuma isteği (`yenile`): her artış uçları bir kez daha okutur.
  const [okuma, setOkuma] = useState(0);
  const yetkiOkunamadi =
    yetki === null &&
    yetkiHatasi !== null &&
    yetkiHatasi !== undefined &&
    okunamadiSayilir(yetkiHatasi);
  const hazir = yetki !== null || yetkiOkunamadi;
  const denetim = yetki?.denetim ?? false;
  const ikiDepo = yetki?.ikiDepo ?? false;

  useEffect(() => {
    if (!hazir) return;
    let iptal = false;
    butunlukApi
      .durum({ denetim, ikiDepo })
      .then((d) => {
        if (iptal) return;
        const duzenli = duzenle(d);
        setDurum(duzenli);
        setOkunamadi(duzenli === null);
      })
      .catch((e: unknown) => {
        if (!iptal) setOkunamadi(okunamadiSayilir(e));
      });
    return () => {
      iptal = true;
    };
  }, [hazir, denetim, ikiDepo, okuma]);

  const ikiDepoyuYaz = useCallback((yanit: IkiDepoYaniti) => {
    setDurum((d) => (d === null ? d : ikiDepoyuBirlestir(d, yanit)));
  }, []);

  const denetimiYaz = useCallback((yanit: DenetimKartlari) => {
    setDurum((d) => (d === null ? d : denetimiBirlestir(d, yanit)));
  }, []);

  const yenile = useCallback(() => setOkuma((n) => n + 1), []);

  return { durum, okunamadi: okunamadi || yetkiOkunamadi, ikiDepoyuYaz, denetimiYaz, yenile };
}
