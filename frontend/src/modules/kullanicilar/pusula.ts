// Hesap teslim pusulasının (E63) kaydedilmesi (plan F1b-2 "E63 hesap teslim pusulası"): yalnız PDF,
// `POST accounts/<id>/handover-slip/` (iz satırı yazıldığı için POST). Dosya adı SUNUCUNUNDUR
// (`Content-Disposition`; `lib/download.basliktanDosyaAdi`): rol etiketini taşır, tanıtıcıyı ve adı
// taşımaz (`Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf`). Başlık okunamazsa ön yüz aynı kalıbı
// kurar (`pusulaYedekDosyaAdi`; backend `hesap_teslim_pusulasi.dosya_adi` ile birebir, günü bu
// bilgisayarın günüdür). Dosya programda saklanmaz: kullanıcının seçtiği yere yazılır. `BASIM` satırı
// PDF üretilince yazılır; kaydetme penceresinde iptal satırı geri almaz.

import { dosyaAdi, saveBlob } from "../../lib/download";
import type { KaydetmeSonucu } from "../../lib/download";
import { formatDate, todayIso } from "../../lib/format";
import { kullanicilarApi } from "./api";
import type { KullaniciSatiri } from "./api";

/**
 * Dosya adının kökü: belge adı "Hesap teslim pusulası"nın her sözcüğü büyük harfle başlar
 * (backend `dosya_adi`: `tr_upper(sozcuk[:1]) + sozcuk[1:]`; sözlük §3 "Kaydedilen dosya adı").
 */
export const PUSULA_DOSYA_KOKU = "Hesap Teslim Pusulası";

/** Sunucunun adı okunamazsa yedek ad: kök + sıra no'suz rol etiketi + bugünün tarihi. */
export function pusulaYedekDosyaAdi(rolEtiketi: string): string {
  return dosyaAdi([PUSULA_DOSYA_KOKU, rolEtiketi, formatDate(todayIso())], "pdf");
}

/** Pusulayı ister ve kaydeder; ret `ApiError` olarak yükselir (çağıran iletiyi gösterir). */
export async function pusulayiKaydet(
  hesap: Pick<KullaniciSatiri, "id" | "rol_etiketi">,
): Promise<KaydetmeSonucu> {
  const { blob, ad } = await kullanicilarApi.pusula(hesap.id);
  return saveBlob(blob, ad ?? pusulaYedekDosyaAdi(hesap.rol_etiketi));
}
