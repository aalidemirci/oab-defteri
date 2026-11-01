// Yeni parola + tekrarı + güç göstergesi — parola belirlenen HER yer aynı alanları
// kullanır (tasarım TK15; plan F1b-1): kilit ekranındaki zorunlu parola yenileme,
// kurtarma anahtarıyla açılış, kurulum sihirbazının program yöneticisi hesabı ve
// Ayarlar → Güvenlik'teki "Parolayı değiştir". Kural ve gösterge `parolaPolitikasi.ts`'tedir;
// ön denetimi çağıran form yapar (`yeniParolaHatalari`), otorite backend'dir.
// İlk alanın etiketi varsayılan "Yeni parola"dır; hesabın ilk parolası (sihirbaz) "Parola"
// der (sözlük §1 "Parola").
//
// Tekrar alanının etiketi "Yeni parola (tekrar)" DEĞİL, "Parola (tekrar)"dır: iki alanın
// adı aynı ön ekle başladığında hem ekran okuyucuda hem testte ayrışmıyor (Ayarlar →
// Güvenlik'teki "Parolayı değiştir" penceresiyle aynı ad).
//
// Hata hangi alanın sorunuysa o alanın altında çıkar ve o alan işaretlenir: politika
// (kısa, eksik tür, kenar boşluğu, eskisiyle aynı) "Yeni parola"nın, eşleşmeme "Parola
// (tekrar)"ın hatasıdır. İlk alan kural metniyle (güç göstergesindeki) ve varsa ekranın
// gerekçe kutusuyla (`aciklamaId`; ör. zorunlu yenilemenin nedeni) açıklanır.

import { forwardRef, useId } from "react";
import type { Ref } from "react";

import TextField from "../../ui/TextField";
import ParolaGucGostergesi from "./ParolaGucGostergesi";

interface YeniParolaAlanlariProps {
  yeniParola: string;
  onYeniParola: (deger: string) => void;
  tekrar: string;
  onTekrar: (deger: string) => void;
  /** "Yeni parola" alanının hatası (politika; sunucunun yeni parola reddi). */
  yeniHata?: string | null;
  /** "Parola (tekrar)" alanının hatası (eşleşmeme). */
  tekrarHata?: string | null;
  /** İlk alanı ayrıca açıklayan öğenin kimliği (ör. zorunlu yenilemenin gerekçesi). */
  aciklamaId?: string;
  disabled?: boolean;
  /** İlk alanın etiketi (varsayılan "Yeni parola"). */
  etiket?: string;
  /** Tekrar alanının ref'i (eşleşmeme reddinden sonra odak oraya döner). */
  tekrarRef?: Ref<HTMLInputElement>;
}

const YeniParolaAlanlari = forwardRef<HTMLInputElement, YeniParolaAlanlariProps>(
  function YeniParolaAlanlari(
    {
      yeniParola,
      onYeniParola,
      tekrar,
      onTekrar,
      yeniHata,
      tekrarHata,
      aciklamaId,
      disabled = false,
      etiket = "Yeni parola",
      tekrarRef,
    },
    ref,
  ) {
    const kuralId = useId();
    return (
      <>
        <TextField
          ref={ref}
          label={etiket}
          type="password"
          value={yeniParola}
          onChange={(e) => onYeniParola(e.target.value)}
          autoComplete="new-password"
          error={yeniHata ?? undefined}
          describedBy={aciklamaId ? `${aciklamaId} ${kuralId}` : kuralId}
          disabled={disabled}
          required
        />
        <ParolaGucGostergesi parola={yeniParola} kuralId={kuralId} />
        <TextField
          ref={tekrarRef}
          label="Parola (tekrar)"
          type="password"
          value={tekrar}
          onChange={(e) => onTekrar(e.target.value)}
          autoComplete="new-password"
          error={tekrarHata ?? undefined}
          disabled={disabled}
          required
        />
      </>
    );
  },
);

export default YeniParolaAlanlari;
