// Hesap seçimi — kilit ekranının ve kurtarma anahtarıyla açılışın hesap listesi
// (tasarım §4.4.3; plan F1b-1 "Oturum"). Satır rol etiketini (büyük) ve altında
// tanıtıcıyı (küçük) gösterir; kişi adı ASLA gösterilmez (sözlük §5).
//
// Erişilebilirlik: yerel radyo düğmeleri bir `fieldset` içindedir (grup adı "Hesap"):
// Sekme tuşu gruba seçili satırdan girer, ok tuşları seçilebilir satırlar arasında
// dolaşır. Satırdayken Enter formu gönderir (parola yazıldıysa), yoksa parola alanına
// geçer (`onEnter`). Seçilemeyen satır (askıda, kaydı okunamayan) devre dışıdır ve
// nedeni `aria-describedby` ile okunur.
//
// Hesap seçiminin hatası ("Hesabınızı seçin.", askıya alınan hesabın iletisi) grubun
// altında `role="alert"` ile çıkar ve gruba `aria-describedby` ile bağlanır: parola
// alanının hatası gibi görünmez (hata hangi alanınsa orada).

import { useId } from "react";
import type { KeyboardEvent } from "react";

export interface HesapSecenegi {
  id: string;
  /** Büyük satır: rol etiketi ("Program yöneticisi", "Denetleme Kurulu 2"). */
  rolEtiketi: string;
  /** Küçük satır: tanıtıcı (`yonetici`, `dk-1`). */
  tanitici: string;
  secilebilir: boolean;
  /** Seçilemezlik nedeni ("askıda — program yöneticisine başvurun"); yoksa null. */
  not: string | null;
}

interface HesapSecimiProps {
  secenekler: readonly HesapSecenegi[];
  seciliId: string | null;
  onSec: (id: string) => void;
  /** Satırda Enter'a basıldı (dosya başı notu). */
  onEnter?: () => void;
  disabled?: boolean;
  /** Hesap seçiminin hatası (grubun altında; dosya başı notu). */
  hata?: string | null;
}

export default function HesapSecimi({
  secenekler,
  seciliId,
  onSec,
  onEnter,
  disabled = false,
  hata = null,
}: HesapSecimiProps) {
  const ad = useId();
  const hataId = `${ad}-hata`;

  function tus(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter" || !onEnter) return;
    e.preventDefault();
    onEnter();
  }

  return (
    <fieldset
      className="flex flex-col gap-2"
      disabled={disabled}
      aria-describedby={hata ? hataId : undefined}
    >
      <legend className="mb-2 text-label-large text-on-surface">Hesap</legend>
      {secenekler.map((h) => {
        const notId = `${ad}-${h.id}-not`;
        const secili = h.id === seciliId;
        return (
          <label
            key={h.id}
            className={`flex items-center gap-3 rounded-shape-md border px-3 py-2.5 transition-colors ${
              !h.secilebilir
                ? "cursor-not-allowed border-outline-variant/70 opacity-60"
                : secili
                  ? "cursor-pointer border-primary bg-primary-container text-on-primary-container"
                  : "cursor-pointer border-outline-variant hover:border-outline"
            }`}
          >
            <input
              type="radio"
              name={ad}
              value={h.id}
              checked={secili}
              disabled={!h.secilebilir}
              onChange={() => onSec(h.id)}
              onKeyDown={tus}
              aria-label={`${h.rolEtiketi} (${h.tanitici})`}
              aria-describedby={h.not ? notId : undefined}
              className="h-4 w-4 shrink-0 accent-primary"
            />
            <span className="flex min-w-0 flex-col">
              <span className="truncate text-title-small text-on-surface">{h.rolEtiketi}</span>
              <span className="truncate text-body-small text-on-surface-variant">{h.tanitici}</span>
              {h.not && (
                <span id={notId} className="text-body-small text-error">
                  {h.not}
                </span>
              )}
            </span>
          </label>
        );
      })}
      {hata && (
        <p id={hataId} role="alert" className="text-body-small text-error">
          {hata}
        </p>
      )}
    </fieldset>
  );
}
