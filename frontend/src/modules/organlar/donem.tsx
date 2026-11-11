// Organlar ve Temsilciler ekranlarının birlik dönemi seçimi (plan F1c kararları: birlik dönemi yoksa organ
// ekranları boş durum gösterir). Varsayılan dönem Birlik Dönemi ekranınınkiyle aynıdır: açık olan; yoksa
// iptal edilmemiş en yenisi. Seçim yalnız birden çok (iptal edilmemiş) dönemde çizilir. Dönem yazılabilir
// değilse (kapanmış, iptal ya da kural kopyası doğrulanamayan, D7) ekranlar yazma denetimi çizmez ve
// bandını gösterir; kapı sunucudadır (409 `donem_kapali`, `donem_salt_okur`).

import { useCallback, useEffect, useMemo, useState } from "react";

import { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import Select from "../../ui/Select";
import { birlikDonemiApi } from "../birlik-donemi/api";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { DONEM_KAPANDI_NOTU, KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { ALAN_BIRLIK_DONEMI, DONEMLER_OKUNAMADI } from "./metinler";

/** Varsayılan dönem: açık olan; yoksa iptal edilmemiş en yenisi. */
export function varsayilanDonem(donemler: readonly BirlikDonemi[]): BirlikDonemi | undefined {
  return (
    donemler.find((d) => d.status === "ACIK") ??
    [...donemler].reverse().find((d) => d.status !== "IPTAL")
  );
}

/** Döneme yazılabilir mi? Açık ve kural kopyası doğrulanmış (D7). */
export function donemYazilir(donem: BirlikDonemi | undefined): boolean {
  return donem !== undefined && donem.status === "ACIK" && donem.kural_kopyasi_tutuyor;
}

/**
 * Geçiş kayıtları (devralınan kaydın iptali dâhil) bu döneme yazılabilir mi? Sunucunun
 * `donem_kilidi.gecis_acik_mi` koşulunun karşılığı: dönem genel kurulsuz açılmış, açık ve "Geçiş
 * kurulumu tamamlandı" işareti konmamış. İşaretten sonra sunucu 409 `gecis_kapali` verir; düğme çizilmez.
 */
export function gecisAcik(donem: BirlikDonemi): boolean {
  return (
    donem.opened_by_assembly === null &&
    donem.status === "ACIK" &&
    donem.transition_completed_on === null
  );
}

export interface DonemSecimi {
  donemler: BirlikDonemi[];
  secili: BirlikDonemi | undefined;
  sec: (id: number) => void;
  /** Sunucunun döndürdüğü güncel dönem kaydını listeye yerleştirir (ör. toplantı günü kaydından sonra). */
  guncelle: (donem: BirlikDonemi) => void;
  yukleniyor: boolean;
  hata: SayfaHatasi | null;
}

/** Birlik dönemlerini okur ve seçimi tutar (iptal edilmiş dönem seçilmez). */
export function useDonemSecimi(): DonemSecimi {
  const [donemler, setDonemler] = useState<BirlikDonemi[]>([]);
  const [seciliId, setSeciliId] = useState<number | null>(null);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  useEffect(() => {
    let iptal = false;
    birlikDonemiApi
      .donemler()
      .then((liste) => {
        if (iptal) return;
        setDonemler(liste.filter((d) => d.status !== "IPTAL"));
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, DONEMLER_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setYukleniyor(false);
      });
    return () => {
      iptal = true;
    };
  }, []);

  const secili = useMemo(
    () => donemler.find((d) => d.id === seciliId) ?? varsayilanDonem(donemler),
    [donemler, seciliId],
  );
  const guncelle = useCallback(
    (d: BirlikDonemi) => setDonemler((ds) => ds.map((x) => (x.id === d.id ? d : x))),
    [],
  );
  return { donemler, secili, sec: setSeciliId, guncelle, yukleniyor, hata };
}

/** Dönem seçimi (birden çok dönemde) ve dönemin kilit bantları. */
export function DonemBasligi({ secim }: { secim: DonemSecimi }) {
  const { donemler, secili } = secim;
  if (secili === undefined) return null;
  return (
    <div className="space-y-3">
      {donemler.length > 1 && (
        <Select
          className="max-w-md"
          label={ALAN_BIRLIK_DONEMI}
          value={String(secili.id)}
          onChange={(e) => secim.sec(Number(e.target.value))}
          options={donemler.map((d) => ({ value: String(d.id), label: d.name }))}
        />
      )}
      {!secili.kural_kopyasi_tutuyor && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-shape-sm bg-error-container px-4 py-3 text-body-medium text-on-error-container"
        >
          <Icon name="gpp_bad" size="lg" className="shrink-0" />
          <span>{KURAL_KOPYASI_BOZUK}</span>
        </div>
      )}
      {secili.status === "KAPANDI" && (
        <p role="note" className="text-body-medium text-on-surface-variant">
          {DONEM_KAPANDI_NOTU}
        </p>
      )}
    </div>
  );
}
