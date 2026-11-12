// Karar defterinin geçiş kaydı (tasarım §7.9 adım 4; plan F1c 8. adım notları). Programdan önceki son
// karar sıra no'su ve sayfası zorunludur. Karar defteri noterce tasdik edilir (md. 23/2): tasdik bilgisi
// (makam ve gün) girilmezse ya da makam noter değilse uyarı + gerekçe (defter başına bir gerekçe; kural
// `yonetim_kurulu.karar_defteri_noter_tasdiki`). Program defteri tutmaz; defter ekranı F3'tedir.

import { useState } from "react";

import { useFormErrors } from "../../hooks/useFormErrors";
import Button from "../../ui/Button";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import type { TasdikMakami } from "../birlik-donemi/api";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { gecisApi } from "./api";
import {
  ALAN_DEFTER_ACILIS,
  ALAN_SAYFA_SAYISI,
  ALAN_SON_SAYFA,
  ALAN_SON_SIRA_NO,
  ALAN_TASDIK_GUNU,
  ALAN_TASDIK_MAKAMI,
  ALAN_TASDIK_NO,
  DEFTER_KAYDEDILDI,
  DEFTER_KAYDEDILEMEDI,
  DUGME_DEFTERI_KAYDET,
  SON_SAYFA_ZORUNLU,
  SON_SIRA_NO_ZORUNLU,
  TASDIK_MEM,
  TASDIK_NOTER,
} from "./metinler";

const MAKAMLAR = [
  { value: "NOTER", label: TASDIK_NOTER },
  { value: "IL_ILCE_MEM", label: TASDIK_MEM },
];

/** Boş alan null, dolu alan sayı. */
function sayi(metin: string): number | null {
  return metin.trim() === "" ? null : Number(metin);
}

export default function KararDefteriFormu({ onKaydedildi }: { onKaydedildi: () => void }) {
  const snackbar = useSnackbar();
  const [sonNo, setSonNo] = useState("");
  const [sonSayfa, setSonSayfa] = useState("");
  const [makam, setMakam] = useState<TasdikMakami | "">("");
  const [tasdikGunu, setTasdikGunu] = useState("");
  const [tasdikNo, setTasdikNo] = useState("");
  const [sayfaSayisi, setSayfaSayisi] = useState("");
  const [acilis, setAcilis] = useState("");
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors();
  const ug = useUyariGerekce("gecis.karar_defteri");

  const gonder = async () => {
    clearErrors();
    setHata(null);
    let eksik = false;
    if (!sonNo.trim()) {
      setFieldError("last_no_before_program", SON_SIRA_NO_ZORUNLU);
      eksik = true;
    }
    if (!sonSayfa.trim()) {
      setFieldError("last_page_before_program", SON_SAYFA_ZORUNLU);
      eksik = true;
    }
    if (eksik || !ug.hazir()) return;
    setBusy(true);
    try {
      await gecisApi.kararDefteriKaydet({
        last_no_before_program: sayi(sonNo),
        last_page_before_program: sayi(sonSayfa),
        certified_by: makam,
        certified_on: tasdikGunu || null,
        certification_no: tasdikNo.trim(),
        page_count: sayi(sayfaSayisi),
        opened_on: acilis || null,
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(DEFTER_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) {
        applyApiError(e);
        setHata(hataOku(e, DEFTER_KAYDEDILEMEDI));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      noValidate
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        void gonder();
      }}
    >
      {hata && <ErrorBand hata={hata} />}
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={ALAN_SON_SIRA_NO}
          type="number"
          min={0}
          required
          value={sonNo}
          onChange={(e) => setSonNo(e.target.value)}
          error={errors.last_no_before_program}
        />
        <TextField
          label={ALAN_SON_SAYFA}
          type="number"
          min={0}
          required
          value={sonSayfa}
          onChange={(e) => setSonSayfa(e.target.value)}
          error={errors.last_page_before_program}
        />
        <Select
          label={ALAN_TASDIK_MAKAMI}
          value={makam}
          onChange={(e) => setMakam(e.target.value as TasdikMakami | "")}
          options={MAKAMLAR}
          placeholder="— yok —"
          error={errors.certified_by}
        />
        <TextField
          label={ALAN_TASDIK_GUNU}
          type="date"
          value={tasdikGunu}
          onChange={(e) => setTasdikGunu(e.target.value)}
          error={errors.certified_on}
        />
        <TextField
          label={ALAN_TASDIK_NO}
          maxLength={64}
          value={tasdikNo}
          onChange={(e) => setTasdikNo(e.target.value)}
          error={errors.certification_no}
        />
        <TextField
          label={ALAN_SAYFA_SAYISI}
          type="number"
          min={1}
          value={sayfaSayisi}
          onChange={(e) => setSayfaSayisi(e.target.value)}
          error={errors.page_count}
        />
        <TextField
          label={ALAN_DEFTER_ACILIS}
          type="date"
          value={acilis}
          onChange={(e) => setAcilis(e.target.value)}
          error={errors.opened_on}
        />
      </div>
      <UyariGerekceAlani durum={ug} />
      <div className="flex justify-end">
        <Button type="submit" icon="menu_book" disabled={busy}>
          {busy ? "Kaydediliyor…" : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : DUGME_DEFTERI_KAYDET}
        </Button>
      </div>
    </form>
  );
}
