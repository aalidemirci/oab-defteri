// Denetim izi kartlarının ortak kabuğu: Genel Bakış'ın öteki kartlarıyla (`OkunamayanAlanlarKarti`,
// `SonOturumKarti`, `DisYedekKarti`) aynı yerleşim — solda tonlu simge, sağda başlık ve gövde.
// Bölge, başlığıyla adlanır (`aria-labelledby`): testler ve ekran okuyucu kartı adıyla bulur.
//
// Ton: `hata` program dışı değişiklik (error-container; okunamayan alan kartıyla aynı),
// `uyari` dikkat isteyen olay (tertiary-container; projede uyarının tonu), `bilgi` salt
// bilgi (secondary-container). Ham renk yok; token sınıfları.

import type { ReactNode } from "react";

import Card from "../../ui/Card";
import Icon from "../../ui/Icon";

export type KartTonu = "hata" | "uyari" | "bilgi";

const TON: Record<KartTonu, string> = {
  hata: "bg-error-container text-on-error-container",
  uyari: "bg-tertiary-container text-on-tertiary-container",
  bilgi: "bg-secondary-container text-on-secondary-container",
};

interface KartKabuguProps {
  /** Başlığın kimliği (bölgenin erişilebilir adı). */
  id: string;
  baslik: string;
  ikon: string;
  ton: KartTonu;
  children: ReactNode;
}

export default function KartKabugu({ id, baslik, ikon, ton, children }: KartKabuguProps) {
  return (
    <section aria-labelledby={id}>
      <Card elevation={0} className="p-5">
        <div className="flex items-start gap-4">
          <span
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg ${TON[ton]}`}
          >
            <Icon name={ikon} />
          </span>
          <div className="min-w-0 flex-1 space-y-2">
            <h2 id={id} className="text-title-medium font-semibold text-on-surface">
              {baslik}
            </h2>
            {children}
          </div>
        </div>
      </Card>
    </section>
  );
}
