// Geçiş kurulumunun 1. adımı: ilk birlik dönemi (tasarım §7.9 adım 1; plan F1c 8. adım). Form hem Geçiş
// Kurulumu ekranında hem kurulum sihirbazının atlanabilir Birlik Dönemi adımında kullanılır. Ders yılı
// dönem başını (son olağan genel kurulun günü) kapsamalıdır; kapsayan yıl yoksa sunucu reddeder ve
// iletisi Ayarlar → Ders Yılları'nı gösterir. Programa başlama günü boşsa bugündür. Görev süresi uyarısı
// (son genel kuruldan bu yana bir yıl geçmiş: md. 12/2, 14/2) açılışı engellemez, gerekçe istemez:
// çağıran yanıttaki uyarıları gösterir.

import { useEffect, useState } from "react";

import { useFormErrors } from "../../hooks/useFormErrors";
import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { birlikDonemiApi } from "../birlik-donemi/api";
import type { IlkDonemYaniti } from "../birlik-donemi/api";
import { okulApi } from "../okul/api";
import type { SchoolYear } from "../okul/api";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import {
  ALAN_DONEM_ADI,
  ALAN_DONEM_BASI,
  ALAN_GECIS_DERS_YILI,
  ALAN_PROGRAMA_BASLAMA,
  DERS_YILI_SECIN,
  DONEM_ACILAMADI,
  DONEM_ACILDI,
  DONEM_ADI_YARDIMI,
  DONEM_ADI_ZORUNLU,
  DONEM_BASI_YARDIMI,
  DONEM_BASI_ZORUNLU,
  DUGME_DONEMI_AC,
  GECIS_DERS_YILI_YARDIMI,
  PROGRAMA_BASLAMA_YARDIMI,
} from "./metinler";

/** Ad alanının sınırı (backend `OabTermAcilisSerializer.name`). */
const AD_SINIRI = 40;

/** Ders yılının seçenek etiketi: "2026-2027 (07.09.2026 – 25.06.2027)". */
function yilEtiketi(yil: SchoolYear): string {
  return `${yil.name} (${formatDate(yil.start_date)} – ${formatDate(yil.end_date)})`;
}

/** Günü kapsayan ders yılı (yoksa undefined). */
function kapsayanYil(yillar: readonly SchoolYear[], gun: string): SchoolYear | undefined {
  return yillar.find((y) => y.start_date <= gun && gun <= y.end_date);
}

export default function IlkDonemFormu({
  onAcildi,
}: {
  /** Dönem açıldı (yanıt görev süresi uyarılarını taşır). */
  onAcildi: (yanit: IlkDonemYaniti) => void;
}) {
  const snackbar = useSnackbar();
  const [yillar, setYillar] = useState<SchoolYear[]>([]);
  const [ad, setAd] = useState("");
  const [yil, setYil] = useState("");
  const [donemBasi, setDonemBasi] = useState("");
  const [baslama, setBaslama] = useState("");
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors();
  const ug = useUyariGerekce();

  useEffect(() => {
    let iptal = false;
    okulApi
      .listSchoolYears()
      .then((liste) => {
        if (!iptal) setYillar(liste);
      })
      .catch(() => {
        /* liste okunamazsa seçici boş kalır; gönderimde sunucu söyler */
      });
    return () => {
      iptal = true;
    };
  }, []);

  // Dönem başı girilince kapsayan yıl ve ad önerilir (kullanıcı değiştirmediyse).
  const donemBasiDegisti = (gun: string) => {
    setDonemBasi(gun);
    const kapsayan = gun ? kapsayanYil(yillar, gun) : undefined;
    if (kapsayan && !yil) setYil(String(kapsayan.id));
    if (kapsayan && !ad.trim()) setAd(`${kapsayan.name} birlik dönemi`);
  };

  const gonder = async () => {
    clearErrors();
    setHata(null);
    let eksik = false;
    if (!ad.trim()) {
      setFieldError("name", DONEM_ADI_ZORUNLU);
      eksik = true;
    }
    if (!yil) {
      setFieldError("school_year", DERS_YILI_SECIN);
      eksik = true;
    }
    if (!donemBasi) {
      setFieldError("start_date", DONEM_BASI_ZORUNLU);
      eksik = true;
    }
    if (eksik || !ug.hazir()) return;
    setBusy(true);
    try {
      const yanit = await birlikDonemiApi.ilkDonemiAc({
        name: ad.trim(),
        school_year: Number(yil),
        start_date: donemBasi,
        program_start_date: baslama || null,
      });
      ug.sifirla();
      snackbar.success(DONEM_ACILDI);
      onAcildi(yanit);
    } catch (e) {
      if (!ug.yakala(e)) {
        applyApiError(e);
        setHata(hataOku(e, DONEM_ACILAMADI));
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
      <UyariGerekceAlani durum={ug} />
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={ALAN_DONEM_BASI}
          type="date"
          required
          value={donemBasi}
          onChange={(e) => donemBasiDegisti(e.target.value)}
          error={errors.start_date}
          helperText={DONEM_BASI_YARDIMI}
        />
        <TextField
          label={ALAN_PROGRAMA_BASLAMA}
          type="date"
          value={baslama}
          onChange={(e) => setBaslama(e.target.value)}
          error={errors.program_start_date}
          helperText={PROGRAMA_BASLAMA_YARDIMI}
        />
        <Select
          label={ALAN_GECIS_DERS_YILI}
          required
          value={yil}
          onChange={(e) => setYil(e.target.value)}
          options={yillar.map((y) => ({ value: String(y.id), label: yilEtiketi(y) }))}
          placeholder="Seçin"
          error={errors.school_year}
          helperText={GECIS_DERS_YILI_YARDIMI}
        />
        <TextField
          label={ALAN_DONEM_ADI}
          required
          maxLength={AD_SINIRI}
          value={ad}
          onChange={(e) => setAd(e.target.value)}
          error={errors.name}
          helperText={DONEM_ADI_YARDIMI}
        />
      </div>
      <div className="flex justify-end">
        <Button type="submit" icon="event_available" disabled={busy}>
          {busy ? "Kaydediliyor…" : DUGME_DONEMI_AC}
        </Button>
      </div>
    </form>
  );
}
