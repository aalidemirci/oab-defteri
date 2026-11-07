// Eksik ve bozuk eklerin kişisiz listesi (kullanıcı kararı 04.11.2026 "Eksik ve bozuk ekler
// kişisiz bilgiyle listelenir"): geri yükleme durduğunda kartta, başarıda yeniden başlat ekranında.
// Liste uzun olabilir; kendi içinde kayar, klavyeyle de kaysın diye odak alır. Ek yoksa hiçbir şey
// çizilmez.

import type { EkSatiri } from "./api";
import { EK_LISTESI_BASLIGI } from "./metinler";
import { ekSatiriMetni } from "./yedekBilgisi";

export default function EkListesi({ ekler }: { ekler: EkSatiri[] }) {
  if (ekler.length === 0) return null;
  return (
    <div className="mt-2">
      <p className="text-label-large">{EK_LISTESI_BASLIGI}</p>
      <ul
        tabIndex={0}
        aria-label={EK_LISTESI_BASLIGI}
        className="mt-1 max-h-40 space-y-0.5 overflow-y-auto pr-1 text-body-small focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        {ekler.map((ek, sira) => (
          <li key={sira}>{ekSatiriMetni(ek)}</li>
        ))}
      </ul>
    </div>
  );
}
