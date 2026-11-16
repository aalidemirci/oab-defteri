// Katılım işaretleri penceresi (plan F2 §7 U33; R9, dipnot ¹⁰): yalnız `kisisel_veri_ciktisi`
// yeteneğinde açılır (program yöneticisi). Pencere VELİ ADINI gösterir: okuma erişim günlüğüne yazılır,
// yanıt önbelleğe alınmaz (`no-store`); ön yüz adları yalnız pencere açıkken bellekte tutar, hiçbir
// depoya yazmaz. İşaret sayısı katılan sayısına ÖNERİDİR; toplantının sayısı elle girilir (U33).
// Başka genel kurulda işaretli satır değiştirilemez; öteki toplantıda işaretli satır bu toplantıya
// taşınabilir (sunucunun kuralı). Toplantı değişince değişiklikler bırakılır, liste yeniden okunur.

import { useEffect, useMemo, useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { genelKurulApi } from "./api";
import type { KatilimIsaretleri, Toplanti } from "./api";
import {
  ADI_OKUNAMADI,
  ALAN_TOPLANTI,
  DUGME_ISARETLERI_KAYDET,
  DUGME_VAZGEC,
  ISARETLER_KAYDEDILDI,
  ISARETLER_KAYDEDILEMEDI,
  ISARETLER_OKUNAMADI,
  ISARET_BASKA_GENEL_KURUL,
  ISARET_LISTESI_BOS,
  ISARET_OTEKI_TOPLANTI,
  KATILIM_ISARETLERI_ACIKLAMASI,
  KATILIM_ISARETLERI_BASLIGI,
  KAYDEDILIYOR,
  TOPLANTI_TR,
  isaretOnerisi,
} from "./metinler";

export default function KatilimIsaretleriPenceresi({
  kurul,
  ilkToplanti,
  onKapat,
  onKaydedildi,
}: {
  kurul: number;
  ilkToplanti: Toplanti;
  onKapat: () => void;
  /** İşaret sayısı (öneri); ayrıntı yeniden okunur. */
  onKaydedildi: (sayi: number) => void;
}) {
  const snackbar = useSnackbar();
  const [toplanti, setToplanti] = useState<Toplanti>(ilkToplanti);
  const [liste, setListe] = useState<KatilimIsaretleri | null>(null);
  const [isaretli, setIsaretli] = useState<Set<number>>(new Set());
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let iptal = false;
    setListe(null);
    setHata(null);
    genelKurulApi
      .katilimIsaretleri(kurul, toplanti)
      .then((l) => {
        if (iptal) return;
        setListe(l);
        setIsaretli(
          new Set(l.siniflar.flatMap((s) => s.satirlar.filter((r) => r.isaretli).map((r) => r.id))),
        );
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, ISARETLER_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [kurul, toplanti]);

  const ilk = useMemo(
    () =>
      new Set(
        liste?.siniflar.flatMap((s) => s.satirlar.filter((r) => r.isaretli).map((r) => r.id)) ?? [],
      ),
    [liste],
  );

  const degistir = (id: number, secili: boolean) =>
    setIsaretli((s) => {
      const yeni = new Set(s);
      if (secili) yeni.add(id);
      else yeni.delete(id);
      return yeni;
    });

  const kaydet = async () => {
    const isaretle = [...isaretli].filter((id) => !ilk.has(id));
    const kaldir = [...ilk].filter((id) => !isaretli.has(id));
    if (isaretle.length === 0 && kaldir.length === 0) {
      onKapat();
      return;
    }
    setBusy(true);
    setHata(null);
    try {
      const sonuc = await genelKurulApi.isaretle(kurul, { toplanti, isaretle, kaldir });
      snackbar.success(ISARETLER_KAYDEDILDI);
      onKaydedildi(sonuc.isaret_sayisi);
    } catch (e) {
      setHata(hataOku(e, ISARETLER_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  const satirSayisi = liste?.siniflar.reduce((t, s) => t + s.satirlar.length, 0) ?? 0;

  return (
    <Dialog
      open
      onClose={onKapat}
      title={KATILIM_ISARETLERI_BASLIGI}
      wide
      actions={
        <>
          <Button variant="text" onClick={onKapat} disabled={busy}>
            {DUGME_VAZGEC}
          </Button>
          <Button icon="save" onClick={() => void kaydet()} disabled={busy || liste === null}>
            {busy ? KAYDEDILIYOR : DUGME_ISARETLERI_KAYDET}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-body-medium text-on-surface-variant">{KATILIM_ISARETLERI_ACIKLAMASI}</p>
        {hata && <ErrorBand hata={hata} />}
        <Select
          className="max-w-xs"
          label={ALAN_TOPLANTI}
          value={toplanti}
          onChange={(e) => setToplanti(e.target.value as Toplanti)}
          options={(["BIRINCI", "IKINCI"] as const).map((t) => ({
            value: t,
            label: TOPLANTI_TR[t],
          }))}
        />
        {liste === null ? (
          !hata && <SkeletonList rows={4} />
        ) : satirSayisi === 0 ? (
          <p className="text-body-medium text-on-surface-variant">{ISARET_LISTESI_BOS}</p>
        ) : (
          <>
            <p role="status" className="text-body-medium text-on-surface">
              {isaretOnerisi(isaretli.size)}
            </p>
            {liste.siniflar.map((sinif) => (
              <fieldset key={sinif.sinif} className="space-y-1">
                <legend className="text-label-large text-on-surface">{sinif.sinif}</legend>
                <ul className="grid gap-x-4 gap-y-1 sm:grid-cols-2">
                  {sinif.satirlar.map((r) => (
                    <li key={r.id}>
                      <label className="flex items-start gap-2 text-body-medium text-on-surface">
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 shrink-0"
                          checked={isaretli.has(r.id)}
                          disabled={r.baska_isaret}
                          onChange={(e) => degistir(r.id, e.target.checked)}
                        />
                        <span className="min-w-0 break-words">
                          {r.veli ?? ADI_OKUNAMADI}
                          {(r.oteki_toplanti || r.baska_isaret) && (
                            <span className="block text-body-small text-on-surface-variant">
                              {r.baska_isaret ? ISARET_BASKA_GENEL_KURUL : ISARET_OTEKI_TOPLANTI}
                            </span>
                          )}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              </fieldset>
            ))}
          </>
        )}
      </div>
    </Dialog>
  );
}
