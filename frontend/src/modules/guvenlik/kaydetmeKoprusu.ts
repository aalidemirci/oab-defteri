// Pencerenin kaydetme köprüsü (plan F1b-3 "Şifreli yedeği program kaydeder"; `desktop/window.py`
// `PencereKoprusu`). Köprü yoksa (geliştirme kipi, tarayıcı) "Şifreli yedeği kaydet" düğmesi
// kapalıdır. `window.pywebview` sayfa yüklendikten sonra gelir: ilk çizimde olmayabilir,
// `pywebviewready` olayıyla yeniden bakılır.

import { useEffect, useState } from "react";

function kopruVar(): boolean {
  return typeof window.pywebview?.api?.kaydetme_yeri_sor === "function";
}

/** Kaydetme köprüsü hazır mı? */
export function useKaydetmeKoprusu(): boolean {
  const [hazir, setHazir] = useState(kopruVar);

  useEffect(() => {
    const dinleyici = () => setHazir(kopruVar());
    // Olay ilk çizimle bu efekt arasında gelmiş olabilir.
    dinleyici();
    window.addEventListener("pywebviewready", dinleyici);
    return () => window.removeEventListener("pywebviewready", dinleyici);
  }, []);

  return hazir;
}
