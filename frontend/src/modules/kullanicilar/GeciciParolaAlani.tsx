// Geçici parola alanı — "Yeni hesap" ve "Parolayı sıfırla" pencerelerinin ortak parçası (plan
// F1b-2 "Geçici parola"). Alan programın önerisiyle dolu gelir (`geciciParolaOner`); program
// yöneticisi değiştirebilir ya da "Yeni öneri"yle yenisini alabilir. Parola kâğıda yazılıp kapalı
// zarfta verileceği için alan GÖRÜNÜR metindir (yalnız bu pencerede; sonuç ekranında ve
// iletilerde yoktur). KOPYALAMA DÜĞMESİ YOKTUR: parola panoya ve başka bir dosyaya gitmesin.
// Alanın altında kural metni, önerinin açıklaması ve kapalı zarf notu durur; üçü de alana
// `aria-describedby` ile bağlıdır (ekran okuyucu alana gelince okur).

import { forwardRef, useId } from "react";

import Button from "../../ui/Button";
import Icon from "../../ui/Icon";
import TextField from "../../ui/TextField";
import { PAROLA_KURALI_METNI } from "../oturum/parolaPolitikasi";
import { geciciParolaOner } from "./geciciParola";
import { ALAN_GECICI_PAROLA, DUGME_YENI_ONERI, ONERI_YARDIMI, ZARF_METNI } from "./metinler";

interface GeciciParolaAlaniProps {
  deger: string;
  onDeger: (deger: string) => void;
  hata?: string;
  disabled?: boolean;
}

const GeciciParolaAlani = forwardRef<HTMLInputElement, GeciciParolaAlaniProps>(
  function GeciciParolaAlani({ deger, onDeger, hata, disabled = false }, ref) {
    const kok = useId();
    const oneriId = `${kok}-oneri`;
    const zarfId = `${kok}-zarf`;
    return (
      <div className="flex flex-col gap-2">
        <TextField
          ref={ref}
          className="font-mono"
          label={ALAN_GECICI_PAROLA}
          type="text"
          value={deger}
          onChange={(e) => onDeger(e.target.value)}
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          error={hata}
          helperText={PAROLA_KURALI_METNI}
          describedBy={`${oneriId} ${zarfId}`}
          disabled={disabled}
          required
        />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p id={oneriId} className="min-w-0 flex-1 text-body-small text-on-surface-variant">
            {ONERI_YARDIMI}
          </p>
          <Button
            type="button"
            variant="text"
            icon="refresh"
            onClick={() => onDeger(geciciParolaOner())}
            disabled={disabled}
          >
            {DUGME_YENI_ONERI}
          </Button>
        </div>
        <p
          id={zarfId}
          role="note"
          className="flex items-start gap-2 rounded-shape-sm bg-secondary-container px-4 py-3 text-body-small text-on-secondary-container"
        >
          <Icon name="mail_lock" size="lg" className="shrink-0" />
          <span>{ZARF_METNI}</span>
        </p>
      </div>
    );
  },
);

export default GeciciParolaAlani;
