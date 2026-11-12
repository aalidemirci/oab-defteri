// Organlar ve Temsilciler pencerelerinin ortak parçaları: etkin birlik kişilerinin seçimi (Autocomplete),
// bağlanabilir kararların okuması, pencere formunun hata bandı ve işlerin ortak gönderim kalıbı.

import { useCallback, useEffect, useState } from "react";

import Autocomplete from "../../ui/Autocomplete";
import ErrorBand from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { KISI_ARA_YER_TUTUCU, KISI_BULUNAMADI, ALAN_KISI } from "../gecis-kurulumu/metinler";
import { BIRLIK_KISI_TURU_TR, birlikKisileriApi } from "../kisiler/birlikKisileriApi";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { formatDate } from "../../lib/format";
import { organlarApi } from "./api";
import type { BaglanabilirKarar } from "./api";
import { kararSecenegi } from "./metinler";

/** Etkin birlik kişileri (pencere açılınca bir kez okunur; okunamazsa liste boş kalır). */
export function useEtkinKisiler(): BirlikKisisi[] {
  const [kisiler, setKisiler] = useState<BirlikKisisi[]>([]);
  useEffect(() => {
    let iptal = false;
    birlikKisileriApi
      .liste()
      .then((liste) => {
        if (!iptal) setKisiler(liste.filter((k) => k.status === "AKTIF"));
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);
  return kisiler;
}

/** Kişi seçimi: etkin birlik kişileri arasında adla arama (geçiş kurulumunun deseni). */
export function KisiSecimi({
  kisiler,
  secili,
  onSecim,
  hata,
}: {
  kisiler: readonly BirlikKisisi[];
  secili: BirlikKisisi | null;
  onSecim: (kisi: BirlikKisisi | null) => void;
  hata?: string;
}) {
  // Arama işlevi kararlı olmalı: `Autocomplete` onu etkinin bağımlılığında tutar.
  const ara = useCallback(
    async (sorgu: string) => {
      const aranan = sorgu.toLocaleLowerCase("tr");
      return kisiler.filter((k) => (k.full_name ?? "").toLocaleLowerCase("tr").includes(aranan));
    },
    [kisiler],
  );
  return (
    <Autocomplete<BirlikKisisi>
      label={ALAN_KISI}
      required
      placeholder={KISI_ARA_YER_TUTUCU}
      selected={secili}
      minChars={1}
      search={ara}
      onSelect={onSecim}
      onClear={() => onSecim(null)}
      getLabel={(k) => k.full_name ?? ""}
      getSublabel={(k) => BIRLIK_KISI_TURU_TR[k.kind]}
      getKey={(k) => k.id}
      emptyText={KISI_BULUNAMADI}
      error={hata}
    />
  );
}

/** Dönemin bağlanabilir kararları (okunamazsa boş: karar bağı verilmez, kayıt yine yapılabilir). */
export function useBaglanabilirKararlar(donem: number, tur?: string): BaglanabilirKarar[] {
  const [kararlar, setKararlar] = useState<BaglanabilirKarar[]>([]);
  useEffect(() => {
    let iptal = false;
    organlarApi
      .baglanabilirKararlar(donem)
      .then((liste) => {
        if (!iptal) setKararlar(tur === undefined ? liste : liste.filter((k) => k.kind === tur));
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, [donem, tur]);
  return kararlar;
}

/** Kararın seçenekleri (sıra no ve toplantı günü; karar metni yoktur). */
export function kararSecenekleri(kararlar: readonly BaglanabilirKarar[]) {
  return kararlar.map((k) => ({
    value: String(k.id),
    label: kararSecenegi(k.decision_no, formatDate(k.decision_date ?? k.toplanti_gunu)),
  }));
}

/** Pencerenin genel hata bandı (yoksa hiçbir şey). */
export function PencereHatasi({ hata }: { hata: SayfaHatasi | null }) {
  return hata ? <ErrorBand hata={hata} /> : null;
}
