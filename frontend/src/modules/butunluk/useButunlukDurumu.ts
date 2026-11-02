// Genel Bakış'ın bütünlük kartlarının durumu: `GET security/integrity/` sayfa açılınca TEK
// kez okunur (kullanıcı eylemi değil). Kartlar aynı durumdan beslenir; sahipsiz parola
// kaydının silinmesi güncel durumu döndürür, çağıran `yaz` ile yerine koyar.
//
// OKUNAMAZSA GİZLENMEZ (fail-closed): uyarı kartları denetim izinin bulgusunu taşır; okuma
// beklenmedik biçimde düşerse (sunucu hatası, ağ) `okunamadi` doğru olur ve Genel Bakış
// "Bütünlük Durumu Okunamadı" kartını gösterir — bir uyarı sessizce kaybolmaz. Oturum
// kilitliyken (423) ya da anahtar düşmüşken (409) kart yoktur: kilit ekranı gelir. Backend tek
// kartın hatasını öteki kartlara yaymaz, adını `okunamayan`'a yazar (aynı uyarı kartı).
// Eksik alanlı yanıt (eski sürüm, beklenmeyen gövde) kartları düşürmez: eksik liste boş,
// eksik nesne null sayılır (`duzenle`).

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../lib/api";
import { butunlukApi } from "./api";
import type { ButunlukDurumu, GeriYuklemeOzeti } from "./api";

export interface ButunlukDurumuKancasi {
  durum: ButunlukDurumu | null;
  /** Durum okunamadı (kilit ve anahtar dışındaki bir hata): uyarı kartı gösterilir. */
  okunamadi: boolean;
  yaz: (durum: ButunlukDurumu) => void;
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

/** Yanıtı kartların beklediği biçime getirir; nesne değilse null. */
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

export default function useButunlukDurumu(): ButunlukDurumuKancasi {
  const [durum, setDurum] = useState<ButunlukDurumu | null>(null);
  const [okunamadi, setOkunamadi] = useState(false);

  useEffect(() => {
    let iptal = false;
    butunlukApi
      .durum()
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
  }, []);

  const yaz = useCallback((d: ButunlukDurumu) => {
    setDurum(duzenle(d));
    setOkunamadi(false);
  }, []);

  return { durum, okunamadi, yaz };
}
