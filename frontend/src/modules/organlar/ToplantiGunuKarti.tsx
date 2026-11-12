// Yönetim kurulunun aylık toplantı günü (dönem ayarı `yk_meeting_day_rule`; E01'in D bölümünün ilk satırı,
// plan F1c 10. adım notları). Serbest metindir: md. 13/3 yalnız "ayda bir toplanır" der, günü kurul
// belirler; program ona bağlı kural koymaz (altın kural 1). Yazan E01'i üretenlerdir
// (`toplanti_gunu_yazma`: program yöneticisi ve sekreter); öteki rollerde değer salt okunur gösterilir.

import { useState } from "react";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { UyumHataBandi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { organlarApi } from "./api";
import {
  ALAN_TOPLANTI_GUNU,
  GIRILMEDI,
  TOPLANTI_GUNU_ACIKLAMASI,
  TOPLANTI_GUNU_BASLIGI,
  TOPLANTI_GUNU_KAYDEDILDI,
  TOPLANTI_GUNU_KAYDEDILEMEDI,
  TOPLANTI_GUNU_YARDIMI,
} from "./metinler";

/** Kuralın üst sınırı (backend `donemler.TOPLANTI_GUNU_UST`). */
const UST_SINIR = 64;

export default function ToplantiGunuKarti({
  donem,
  deger,
  yazabilir,
  onKaydedildi,
}: {
  donem: number;
  /** Kayıtlı değer (boşsa girilmedi). */
  deger: string;
  yazabilir: boolean;
  /** Kayıttan sonra sunucunun döndürdüğü dönem kaydı (dönem seçimi güncel kalsın; sekmeye dönüşte). */
  onKaydedildi?: (donem: BirlikDonemi) => void;
}) {
  const snackbar = useSnackbar();
  const [kayitli, setKayitli] = useState(deger);
  const [metin, setMetin] = useState(deger);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<UyumHatasi | SayfaHatasi | null>(null);
  const degisti = metin.trim() !== kayitli;

  const kaydet = async () => {
    setBusy(true);
    setHata(null);
    try {
      const donemKaydi = await organlarApi.toplantiGunu(donem, metin.trim());
      const yeni = donemKaydi.yk_meeting_day_rule ?? "";
      setKayitli(yeni);
      setMetin(yeni);
      onKaydedildi?.(donemKaydi);
      snackbar.success(TOPLANTI_GUNU_KAYDEDILDI);
    } catch (e) {
      setHata(uyumHatasiOku(e) ?? hataOku(e, TOPLANTI_GUNU_KAYDEDILEMEDI));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card elevation={0} className="space-y-3 p-[var(--od-panel-padding)]">
      <div className="space-y-1">
        <h2 className="text-title-small text-on-surface">{TOPLANTI_GUNU_BASLIGI}</h2>
        <p className="text-body-small text-on-surface-variant">{TOPLANTI_GUNU_ACIKLAMASI}</p>
      </div>
      {hata && ("tur" in hata ? <UyumHataBandi hata={hata} /> : <ErrorBand hata={hata} />)}
      {yazabilir ? (
        <div className="flex flex-wrap items-end gap-3">
          <TextField
            className="min-w-0 flex-1 basis-64"
            label={ALAN_TOPLANTI_GUNU}
            value={metin}
            maxLength={UST_SINIR}
            onChange={(e) => setMetin(e.target.value)}
            helperText={TOPLANTI_GUNU_YARDIMI}
          />
          <Button
            variant="tonal"
            icon="save"
            disabled={busy || !degisti}
            onClick={() => void kaydet()}
          >
            {busy ? "Kaydediliyor…" : "Kaydet"}
          </Button>
        </div>
      ) : (
        <p className="break-words text-body-medium text-on-surface">{kayitli || GIRILMEDI}</p>
      )}
    </Card>
  );
}
