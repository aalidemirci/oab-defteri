// Parola güç göstergesi — yeni parola alanının altında (tasarım TK15; plan F1b-1).
// Yerel kuraldır (`parolaPolitikasi.parolaGucu`: uzunluk + karakter türleri), sunucunun
// kararı değildir; kural metnini ve parola cümlesi önerisini de söyler. Erişilebilir
// adı "Parola gücü"dür; düzey metinle de yazılır (renk tek başına anlam taşımaz).
//
// Erişilebilirlik: kural + öneri metni `kuralId` kimliğini taşır ve yeni parola alanına
// `aria-describedby` ile bağlanır (`YeniParolaAlanlari`): ekran okuyucu kuralı alana
// gelince duyar, ilk kez ret iletisinden öğrenmez. Düzey ("Parola gücü: İyi.") kibar bir
// canlı bölgededir: yazarken düzey değişince duyurulur. Canlı bölge boşken de DOM'dadır
// (içeriği sonradan dolan bölge ancak böyle duyurulur).

import { PAROLA_CUMLESI_ONERISI, PAROLA_KURALI_METNI, parolaGucu } from "./parolaPolitikasi";

const DOLGU: Record<number, string> = {
  0: "bg-outline-variant",
  1: "bg-error",
  2: "bg-tertiary",
  3: "bg-primary",
  4: "bg-success",
};

interface ParolaGucGostergesiProps {
  parola: string;
  /** Kural + öneri metninin kimliği (yeni parola alanı bu kimlikle açıklanır). */
  kuralId?: string;
}

export default function ParolaGucGostergesi({ parola, kuralId }: ParolaGucGostergesiProps) {
  const { duzey, etiket } = parolaGucu(parola);
  return (
    <div className="flex flex-col gap-1.5">
      <div
        role="meter"
        aria-label="Parola gücü"
        aria-valuemin={0}
        aria-valuemax={4}
        aria-valuenow={duzey}
        aria-valuetext={etiket || "Boş"}
        className="flex gap-1"
      >
        {[1, 2, 3, 4].map((dilim) => (
          <span
            key={dilim}
            aria-hidden="true"
            className={`h-1.5 flex-1 rounded-full ${dilim <= duzey ? DOLGU[duzey] : DOLGU[0]}`}
          />
        ))}
      </div>
      <p className="text-body-small text-on-surface-variant">
        <span aria-live="polite" className="font-semibold text-on-surface">
          {etiket && `Parola gücü: ${etiket}. `}
        </span>
        <span id={kuralId}>
          {PAROLA_KURALI_METNI} {PAROLA_CUMLESI_ONERISI}
        </span>
      </p>
    </div>
  );
}
