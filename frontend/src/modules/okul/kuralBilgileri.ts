// Okul kartında kural paketinden gelen bilgi (md. 23/3; tasarım §6.4.8
// `kantin.isletmede_vergi_uyarisi`). Metin ve hangi kantin biçiminde görüneceği paketten gelir, ön
// yüzde kopyası yoktur (altın kural 2). Form kaydedilmeden seçim değişebildiği için biçimlerin
// listesi tek seferde okunur.

import { useEffect, useState } from "react";

import { api } from "../../lib/api";
import type { CanteenMode } from "./api";

export interface KantinBilgisi {
  /** Bilginin göründüğü kantin işletme biçimleri. */
  modlar: CanteenMode[];
  /** Atfıyla birlikte hazır cümle. */
  metin: string;
  paket: string;
  rev: number;
}

interface OkulKartiBilgileri {
  kantin_isletme_bilgisi: KantinBilgisi | null;
}

export const getOkulKartiBilgileri = (): Promise<OkulKartiBilgileri> =>
  api.get<OkulKartiBilgileri>("/oab/okul-karti-bilgileri/");

/** Kural paketi okunamazsa ya da istek başarısızsa `null`: bilgi çıkmaz, form çalışmayı sürdürür. */
export function useKantinIsletmeBilgisi(): KantinBilgisi | null {
  const [bilgi, setBilgi] = useState<KantinBilgisi | null>(null);
  useEffect(() => {
    let canli = true;
    getOkulKartiBilgileri()
      .then((yanit) => {
        if (canli) setBilgi(yanit.kantin_isletme_bilgisi);
      })
      .catch(() => {
        if (canli) setBilgi(null);
      });
    return () => {
      canli = false;
    };
  }, []);
  return bilgi;
}
