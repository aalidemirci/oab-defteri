// Tam ekran "programı kapatıp yeniden açın" yönlendirmesi — backend
// `restart_gate` kapısının arayüz ayağı. Geri yükleme uygulandıktan sonra
// süreç içi durum (bellekteki anahtar, bekleyen şema göçleri) diskteki veriyi
// artık tarif etmez; backend tüm API'yi 503 `restart_required` ile keser ve
// `lib/api.ts` olayı yayınlar. Ekran BİLEREK kapatılamaz: kapatma düğmesi
// koymak kullanıcıyı bayat oturumda çalışmaya davet ederdi — tek çıkış
// programı gerçekten kapatıp yeniden açmaktır.
//
// Program bu ekrandaki "Programdan çık" düğmesiyle (`POST app/quit/`, "yeniden
// başlat" kapısının geçirdiği tek uç) ya da pencerenin çarpısıyla kapanır; ikisi
// aynı düzenli kapanış yoludur (T6, tasarım §4.5 — tepsi yoktur).
//
// Dosya raporu (plan F1b-3 "Eksik ve bozuk ekler kişisiz bilgiyle listelenir"): geri yükleme
// olayla birlikte raporu verir; ekran kapsamı, kişisiz sayıları ("Ekler" satırı) ve eksik ya da
// bozuk eklerin listesini yazar. Bu ekran kartın üstünü örttüğü için liste burada görünmezse hiç
// görünmez. Sayfa yenilenince gelen olay rapor taşımaz, satır çizilmez; önceki rapor da silinmez.

import { useEffect, useState } from "react";

import { YENIDEN_BASLAT_OLAYI } from "../../lib/restart";
import { DogrudanCikisDugmesi } from "../cikis/CikisDugmesi";
import { useDurumBasligi } from "../../ui/DurumBasligi";
import Icon from "../../ui/Icon";
import type { DosyaRaporu } from "./api";
import EkListesi from "./EkListesi";
import { ONCEKI_VERITABANI_KENARA_ALINDI } from "./metinler";
import { eklerSatiri, kapsamMetni } from "./yedekBilgisi";

/** Ekranın başlığı — üst çubukta da bu yazar (docs/sozluk.md §4.2). */
export const YENIDEN_BASLAT_BASLIGI = "Programı kapatıp yeniden açın";

export default function YenidenBaslatEkrani() {
  const [aktif, setAktif] = useState(false);
  const [rapor, setRapor] = useState<DosyaRaporu | null>(null);
  useDurumBasligi(aktif ? YENIDEN_BASLAT_BASLIGI : null);

  useEffect(() => {
    const dinleyici = (olay: Event) => {
      setAktif(true);
      const ayrinti = (olay as CustomEvent<DosyaRaporu | null>).detail;
      if (ayrinti) setRapor(ayrinti);
    };
    window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    return () => window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
  }, []);

  if (!aktif) return null;

  return (
    <div
      // z-[60]: ui/Dialog z-50 kullanır; bu ekran diyalogların üstünde kalmalı. Tek istisna
      // kapanış penceresidir (`enUstte`): program bu ekrandayken de kapanabilir.
      className="fixed inset-0 z-[60] flex items-center justify-center bg-scrim/[0.6] p-4"
      role="alertdialog"
      aria-modal="true"
      aria-label="Programı yeniden başlatın"
    >
      <div className="max-h-full w-full max-w-lg overflow-y-auto rounded-shape-lg border border-outline-variant bg-surface-container-lowest p-8 text-center shadow-elevation-3">
        <Icon name="restart_alt" size="5xl" className="text-primary" />
        <h2 className="mt-3 text-headline-small text-on-surface">{YENIDEN_BASLAT_BASLIGI}</h2>
        <p className="mt-3 text-body-medium text-on-surface-variant">
          Yedekten geri yükleme uygulandı. Geri yüklenen kayıtlarla çalışmaya devam edebilmek için
          programın yeniden başlatılması gerekir.
        </p>
        <p className="mt-3 text-body-medium text-on-surface-variant">
          Programı kapatıp yeniden açın: aşağıdaki düğmeyle ya da pencerenin çarpı düğmesiyle
          programdan çıkın, sonra programı yeniden açın.
        </p>
        {rapor && (
          <div className="mt-3 rounded-shape-sm bg-surface-container p-3 text-left text-body-small text-on-surface">
            <p>Yedeğin kapsamı: {kapsamMetni(rapor.kapsam)}</p>
            <p>{eklerSatiri(rapor)}</p>
            <EkListesi ekler={rapor.ekler} />
          </div>
        )}
        {/* Çık (tasarım §4.5): pencere süslemesi olmayan masaüstünde çıkış yolu; parolasızdır. */}
        <DogrudanCikisDugmesi />
        <p className="mt-3 text-body-small text-on-surface-variant">
          {ONCEKI_VERITABANI_KENARA_ALINDI}
        </p>
      </div>
    </div>
  );
}
