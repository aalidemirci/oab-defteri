// Programdan önceki seçilme sayılarının toplu beyanı (tasarım §7.9 adım 3; md. 12/4, 14/3; plan F1c 8.
// adımın kararı). Her kişide sayı ("karar defterinden: n") ya da "Bilinmiyor"; değişmeyen alan gönderilmez.
// "Bilinmiyor" denen bütün kişiler için seçilme sınırı uyarısı TEK gerekçeyle kapanır (toplu gerekçe, kök
// nedeni sunucu koyar; O3): sunucu gerekçe isterse ortak kutu açılır. Verilmiş sayı değişirse ya da
// "Bilinmiyor"a dönerse düzeltme gerekçesi zorunludur; "Bilinmiyor"dan sayıya geçiş düzeltme değildir.
// "Girilmedi" yalnız değeri hiç girilmemiş alanda seçenektir (değeri olan alanda seçilse yok sayılırdı);
// gönderilecek değişiklik kalmamışsa Kaydet Vazgeç gibi davranır (yarım metin de silinir).

import { useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { gecisApi } from "./api";
import type { SayacBeyani } from "./api";
import {
  ALAN_DK_BASKANLIK_SAYISI,
  ALAN_DUZELTME_GEREKCESI,
  ALAN_YK_SAYISI,
  DUZELTME_GEREKCESI_YARDIMI,
  DUZELTME_GEREKCESI_YAZIN,
  SAYAC_ACIKLAMASI,
  SAYAC_BILINMIYOR,
  SAYAC_GIRILMEDI,
  SAYAC_KAYDEDILDI,
  SAYAC_KAYDEDILEMEDI,
  SAYAC_PENCERESI_BASLIGI,
} from "./metinler";

/** Seçicinin değeri: "" girilmedi, "?" bilinmiyor, "0"… sayı. */
export type SayacSecimi = string;

export const BILINMIYOR = "?";

/** Beyan satırı: kişi ve iki alanın bugünkü değeri. */
export interface SayacSatiri {
  kisi: number;
  ad: string;
  /** Yönetim kuruluna seçilme sayısı alanı gösterilsin mi? */
  yk: boolean;
  /** Denetleme Kurulu başkanlığı alanı gösterilsin mi? */
  dk: boolean;
  ykDegeri: SayacSecimi;
  dkDegeri: SayacSecimi;
}

/** Seçicinin seçenekleri: girilmedi, bilinmiyor, 0-10. */
const SECENEKLER = [
  { value: BILINMIYOR, label: SAYAC_BILINMIYOR },
  ...Array.from({ length: 11 }, (_, i) => ({ value: String(i), label: String(i) })),
];

function deger(secim: SayacSecimi): number | null {
  return secim === BILINMIYOR ? null : Number(secim);
}

/** Verilmiş bir sayının değişmesi ya da "Bilinmiyor"a dönmesi düzeltmedir. */
export function duzeltmeMi(once: SayacSecimi, sonra: SayacSecimi): boolean {
  return once !== "" && once !== BILINMIYOR && sonra !== "" && once !== sonra;
}

/** Değişen alanlardan beyan listesi (değişmeyen alan ve satır gönderilmez). */
export function beyanlar(
  satirlar: readonly SayacSatiri[],
  secimler: Record<number, { yk: SayacSecimi; dk: SayacSecimi }>,
): SayacBeyani[] {
  const sonuc: SayacBeyani[] = [];
  for (const s of satirlar) {
    const secim = secimler[s.kisi];
    const beyan: SayacBeyani = { person: s.kisi };
    if (s.yk && secim.yk !== s.ykDegeri && secim.yk !== "") beyan.yk = deger(secim.yk);
    if (s.dk && secim.dk !== s.dkDegeri && secim.dk !== "") beyan.dk_baskanlik = deger(secim.dk);
    if ("yk" in beyan || "dk_baskanlik" in beyan) sonuc.push(beyan);
  }
  return sonuc;
}

export default function SayacBeyaniPenceresi({
  satirlar,
  onKapat,
  onKaydedildi,
}: {
  satirlar: readonly SayacSatiri[];
  onKapat: () => void;
  onKaydedildi: () => void;
}) {
  const snackbar = useSnackbar();
  const [secimler, setSecimler] = useState<Record<number, { yk: SayacSecimi; dk: SayacSecimi }>>(
    () => Object.fromEntries(satirlar.map((s) => [s.kisi, { yk: s.ykDegeri, dk: s.dkDegeri }])),
  );
  const [duzeltme, setDuzeltme] = useState("");
  const [duzeltmeHatasi, setDuzeltmeHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const ug = useUyariGerekce("gecis.sayac_beyani");

  const duzeltmeVar = satirlar.some(
    (s) =>
      (s.yk && duzeltmeMi(s.ykDegeri, secimler[s.kisi].yk)) ||
      (s.dk && duzeltmeMi(s.dkDegeri, secimler[s.kisi].dk)),
  );

  // Vazgeçilince yarım metin silinir (kayıt yapılmadı).
  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const sec = (kisi: number, alan: "yk" | "dk", secim: SayacSecimi) =>
    setSecimler((onceki) => ({ ...onceki, [kisi]: { ...onceki[kisi], [alan]: secim } }));

  const gonder = async () => {
    setHata(null);
    const liste = beyanlar(satirlar, secimler);
    // Değişiklik kalmadı: kayıt yok, Vazgeç gibi (gerekçe sorulmaz; yarım metin silinir).
    if (liste.length === 0) {
      vazgec();
      return;
    }
    if (duzeltmeVar && !duzeltme.trim()) {
      setDuzeltmeHatasi(DUZELTME_GEREKCESI_YAZIN);
      return;
    }
    if (!ug.hazir()) return;
    setBusy(true);
    try {
      await gecisApi.sayacBeyani({
        beyanlar: liste,
        ...ug.ek(),
        ...(duzeltmeVar ? { duzeltme_gerekcesi: duzeltme.trim() } : {}),
      });
      ug.sifirla();
      snackbar.success(SAYAC_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, SAYAC_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={SAYAC_PENCERESI_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={vazgec} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="check" onClick={() => void gonder()} disabled={busy}>
            {busy ? "Kaydediliyor…" : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : "Kaydet"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        <p className="text-body-medium text-on-surface-variant">{SAYAC_ACIKLAMASI}</p>
        <UyariGerekceAlani durum={ug} toplu />
        <ul className="divide-y divide-outline-variant">
          {satirlar.map((s) => (
            <li key={s.kisi} className="grid gap-3 py-3 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
              <p className="min-w-0 break-words self-center text-body-medium text-on-surface">
                {s.ad}
              </p>
              {s.yk ? (
                <Select
                  label={ALAN_YK_SAYISI}
                  aria-label={`${s.ad}: ${ALAN_YK_SAYISI}`}
                  value={secimler[s.kisi].yk}
                  onChange={(e) => sec(s.kisi, "yk", e.target.value)}
                  options={SECENEKLER}
                  placeholder={s.ykDegeri === "" ? SAYAC_GIRILMEDI : undefined}
                />
              ) : (
                <span />
              )}
              {s.dk ? (
                <Select
                  label={ALAN_DK_BASKANLIK_SAYISI}
                  aria-label={`${s.ad}: ${ALAN_DK_BASKANLIK_SAYISI}`}
                  value={secimler[s.kisi].dk}
                  onChange={(e) => sec(s.kisi, "dk", e.target.value)}
                  options={SECENEKLER}
                  placeholder={s.dkDegeri === "" ? SAYAC_GIRILMEDI : undefined}
                />
              ) : (
                <span />
              )}
            </li>
          ))}
        </ul>
        {duzeltmeVar && (
          <div>
            <label
              htmlFor="duzeltme-gerekcesi"
              className="mb-1.5 block text-label-medium font-semibold text-on-surface-variant"
            >
              {ALAN_DUZELTME_GEREKCESI}
              <span className="text-error"> *</span>
            </label>
            <textarea
              id="duzeltme-gerekcesi"
              rows={2}
              maxLength={1000}
              value={duzeltme}
              onChange={(e) => {
                setDuzeltme(e.target.value);
                setDuzeltmeHatasi(undefined);
              }}
              aria-invalid={duzeltmeHatasi ? true : undefined}
              aria-describedby="duzeltme-gerekcesi-yardim"
              className="block w-full rounded-shape-xs border border-outline bg-surface px-3 py-2 text-body-medium text-on-surface outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
            />
            {duzeltmeHatasi && (
              <p role="alert" className="mt-1 text-body-small text-error">
                {duzeltmeHatasi}
              </p>
            )}
            <p
              id="duzeltme-gerekcesi-yardim"
              className="mt-1 text-body-small text-on-surface-variant"
            >
              {DUZELTME_GEREKCESI_YARDIMI}
            </p>
          </div>
        )}
      </div>
    </Dialog>
  );
}
