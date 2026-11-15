// Pardus'ta açık dosya penceresinin bildirimi (saha bulgusu K-P3; bağımsız denetim 13.11.2026).
// Linux'ta kaydetme ve Aç pencereleri masaüstünün penceresidir, dış süreçte açılır ve ana pencereye
// bağlı değildir (`desktop/yerel_pencere.py`): ana pencere tıklanabilir kalır. Pencere açıkken gelen
// ikinci çağrı (başka bir düğme, sayfanın dosya kutusu) beklemeden iptal döner, ikinci pencere açılmaz
// (`desktop/window.py` `_tek_pencere`). İptal sessiz kalmasın diye masaüstü `od:dosya-penceresi-acik`
// olayını yollar (ayrıntı taşımaz); bu bileşen geçici bildirim gösterir: dış pencere ana pencerenin
// arkasında kalmış olabilir. Windows'ta pencere işletim sisteminindir, olay hiç gelmez.
//
// YERİ: uygulama köküne yakın, kapıların dışında (`App`): kaydetme penceresi kilit ekranında da açık
// kalmış olabilir. Hiçbir şey çizmez.

import { useEffect } from "react";

import { useSnackbar } from "./ui/SnackbarProvider";

/** Masaüstünün yolladığı DOM olayı (`desktop/window.py` `DOSYA_PENCERESI_ACIK_OLAYI`). */
export const DOSYA_PENCERESI_ACIK_OLAYI = "od:dosya-penceresi-acik";
/** Bildirimin metni (docs/sozluk.md §3 "Dosyayı program kaydeder"). */
export const DOSYA_PENCERESI_ACIK_METNI = "Açık bir dosya penceresi var; önce onu kapatın.";

export default function DosyaPenceresiBildirimi() {
  const { show } = useSnackbar();

  useEffect(() => {
    const dinleyici = () => show(DOSYA_PENCERESI_ACIK_METNI);
    window.addEventListener(DOSYA_PENCERESI_ACIK_OLAYI, dinleyici);
    return () => window.removeEventListener(DOSYA_PENCERESI_ACIK_OLAYI, dinleyici);
  }, [show]);

  return null;
}
