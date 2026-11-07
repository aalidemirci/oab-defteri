// Pencerenin dosya köprüleri (`desktop/window.py` `PencereKoprusu`): kaydetme penceresi (plan F1b-3
// "Şifreli yedeği program kaydeder") ve Aç penceresi (kullanıcı kararı 06.11.2026 "Yedek dosyası
// yüklenmez, programın Aç penceresiyle seçilir"). Köprü yoksa (geliştirme kipi, tarayıcı) "Şifreli
// yedeği kaydet" düğmesi kapalıdır, geri yükleme kartı dosya kutusunu gösterir. `window.pywebview`
// sayfa yüklendikten sonra gelir: ilk çizimde olmayabilir, `pywebviewready` olayıyla yeniden bakılır.

import { useEffect, useState } from "react";

type KopruIslevi = "kaydetme_yeri_sor" | "yedek_dosyasi_sor";

function kopruVar(islev: KopruIslevi): boolean {
  return typeof window.pywebview?.api?.[islev] === "function";
}

function useKopruIslevi(islev: KopruIslevi): boolean {
  const [hazir, setHazir] = useState(() => kopruVar(islev));

  useEffect(() => {
    const dinleyici = () => setHazir(kopruVar(islev));
    // Olay ilk çizimle bu efekt arasında gelmiş olabilir.
    dinleyici();
    window.addEventListener("pywebviewready", dinleyici);
    return () => window.removeEventListener("pywebviewready", dinleyici);
  }, [islev]);

  return hazir;
}

/** Kaydetme köprüsü hazır mı? */
export function useKaydetmeKoprusu(): boolean {
  return useKopruIslevi("kaydetme_yeri_sor");
}

/** Aç penceresinin köprüsü hazır mı? */
export function useAcmaKoprusu(): boolean {
  return useKopruIslevi("yedek_dosyasi_sor");
}
