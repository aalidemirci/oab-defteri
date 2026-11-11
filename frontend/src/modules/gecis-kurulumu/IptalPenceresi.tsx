// Geçiş kaydının iptal penceresi (plan F1c 8. adımın kararı; altın kural 4): kayıt silinmez, değişmez;
// iptal gerekçesi zorunludur ve şifreli saklanır, "kim" denetim izindedir. Başlık soru, gövde sonuçtur
// (sözlük §3 "Onay diyaloğu"); geri dönüşü olmayan işlem değer istediği için başlık yine sorudur.

import { useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { UyumHataBandi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { DUGME_KAYDI_IPTAL, IPTAL_GEREKCESI, IPTAL_GEREKCESI_YAZIN } from "./metinler";

export default function IptalPenceresi({
  baslik,
  metin,
  yedekHata,
  onIptal,
  onKapat,
}: {
  /** Soru ("Birlik dönemi iptal edilsin mi?"). */
  baslik: string;
  /** Sonuç cümlesi. */
  metin: string;
  /** Sunucu iletisi yoksa gösterilecek hata. */
  yedekHata: string;
  /** İptali gönderir; başarılıysa pencere çağıranca kapatılır. */
  onIptal: (gerekce: string) => Promise<void>;
  onKapat: () => void;
}) {
  const [gerekce, setGerekce] = useState("");
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [uyum, setUyum] = useState<UyumHatasi | null>(null);

  const gonder = async () => {
    if (!gerekce.trim()) {
      setAlanHatasi(IPTAL_GEREKCESI_YAZIN);
      return;
    }
    setBusy(true);
    setHata(null);
    setUyum(null);
    try {
      await onIptal(gerekce.trim());
    } catch (e) {
      const okunan = uyumHatasiOku(e);
      if (okunan) setUyum(okunan);
      else setHata(hataOku(e, yedekHata));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={baslik}
      actions={
        <>
          <Button variant="text" onClick={onKapat} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="block" onClick={() => void gonder()} disabled={busy}>
            {busy ? "Kaydediliyor…" : DUGME_KAYDI_IPTAL}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        {uyum && <UyumHataBandi hata={uyum} />}
        <p className="text-body-medium text-on-surface">{metin}</p>
        <div>
          <label
            htmlFor="iptal-gerekcesi"
            className="mb-1.5 block text-label-medium font-semibold text-on-surface-variant"
          >
            {IPTAL_GEREKCESI}
            <span className="text-error"> *</span>
          </label>
          <textarea
            id="iptal-gerekcesi"
            rows={3}
            maxLength={1000}
            value={gerekce}
            onChange={(e) => {
              setGerekce(e.target.value);
              setAlanHatasi(undefined);
            }}
            aria-invalid={alanHatasi ? true : undefined}
            aria-describedby={alanHatasi ? "iptal-gerekcesi-hata" : undefined}
            className="block w-full rounded-shape-xs border border-outline bg-surface px-3 py-2 text-body-medium text-on-surface outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
          />
          {alanHatasi && (
            <p id="iptal-gerekcesi-hata" role="alert" className="mt-1 text-body-small text-error">
              {alanHatasi}
            </p>
          )}
        </div>
      </div>
    </Dialog>
  );
}
