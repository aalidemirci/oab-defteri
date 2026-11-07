// Uzun iş sürerken gelen kapanışın ön yüz ayağı (tasarım §4.5 "Çarpı", §4.2; plan F1b-3 "Uzun iş,
// çarpı, temiz kapanış"). Masaüstü kapanışı bir kez, en çok 60 sn erteler ve `od:kapanis-bekliyor`
// olayını yollar (`desktop/window.py`; bekleme başına bir kez, ayrıntı taşımaz). Kapanış olayı
// yoktur: pencere kendiliğinden kapanır, bu yüzden ileti açılır ve açık kalır.
//
// KAPATILAMAZ: Çık'ın "Program kapanıyor" kalıbıdır (`onClose` boş, düğme yok). Kapatılabilseydi
// kullanıcı işin sürdüğünü sanıp bir şey başlatırdı; pencere o sırada kapanır.
//
// YERİ: uygulama köküne yakın, kapıların dışında (`App`): çarpı kilit ekranında, kurulumda ve
// "Programı kapatıp yeniden açın" ekranında da basılabilir. O ekran her diyaloğun üstünde durduğu
// için pencere `enUstte` açılır.

import { useEffect, useState } from "react";

import Dialog from "../../ui/Dialog";
import { KAPANIS_BEKLENIYOR_METNI, PROGRAM_KAPANIYOR_BASLIGI } from "./metinler";

/** Masaüstünün yolladığı DOM olayı (`desktop/window.py` `KAPANIS_BEKLIYOR_OLAYI`; backend testi). */
export const KAPANIS_BEKLIYOR_OLAYI = "od:kapanis-bekliyor";

export default function KapanisPenceresi() {
  const [acik, setAcik] = useState(false);

  useEffect(() => {
    const dinleyici = () => setAcik(true);
    window.addEventListener(KAPANIS_BEKLIYOR_OLAYI, dinleyici);
    return () => window.removeEventListener(KAPANIS_BEKLIYOR_OLAYI, dinleyici);
  }, []);

  return (
    <Dialog open={acik} onClose={() => undefined} title={PROGRAM_KAPANIYOR_BASLIGI} enUstte>
      <p role="status">{KAPANIS_BEKLENIYOR_METNI}</p>
    </Dialog>
  );
}
