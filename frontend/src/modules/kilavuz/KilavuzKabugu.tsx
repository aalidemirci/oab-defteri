// Kullanım Kılavuzu'nun kabuk bileşenleri — aile iskeletinin kılavuzundan ayıklandı
// (tasarım §12.B `kilavuz`: 5.080 satırlık dosyadan kabuk ayrıldı, kütüphane içeriği
// silindi). Kalıp HakkindaPage'den: bölüm başına Card + 44px ikon rozeti. Ekranlara
// `Link` ile atlanır; sayfa içi bağlantılar yalnız "Bu kılavuzda" listesindeki bölüm
// çapalarıdır. OAB'nin bölümleri özellikleriyle birlikte yazılır.

import { useEffect } from "react";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import Card from "../../ui/Card";
import Icon from "../../ui/Icon";

/**
 * Kılavuz bölümü — ikon rozeti + başlık + içerik. `scroll-mt-24`: "Bu kılavuzda"
 * bağlantısıyla gelindiğinde başlık yapışkan üst çubuğun altında kalmasın.
 */
export function KilavuzBolumu({
  id,
  baslik,
  ikon,
  children,
}: {
  id: string;
  baslik: string;
  ikon: string;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-baslik`} className="scroll-mt-24">
      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-primary-container text-on-primary-container">
            <Icon name={ikon} size="xl" />
          </span>
          <div className="min-w-0 flex-1 space-y-3 text-body-medium text-on-surface-variant">
            <h2 id={`${id}-baslik`} className="text-title-large font-semibold text-on-surface">
              {baslik}
            </h2>
            {children}
          </div>
        </div>
      </Card>
    </section>
  );
}

/** Bölüm içi alt başlık. */
export function AltBaslik({ children }: { children: ReactNode }) {
  return <h3 className="pt-1 text-title-small font-semibold text-on-surface">{children}</h3>;
}

/** Vurgulu ipucu kutusu (tertiary yüzey — gövde metninden ayrışır). */
export function Ipucu({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-shape-md bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
      <Icon name="lightbulb" size="lg" className="mt-0.5 shrink-0" />
      <div className="min-w-0">{children}</div>
    </div>
  );
}

/** Mevzuat alıntısı — birebir metin + kaynak adı ve madde (docs/mevzuat'tan). */
export function Mevzuat({ kaynak, children }: { kaynak: string; children: ReactNode }) {
  return (
    <figure className="rounded-shape-md border-l-4 border-outline bg-surface-container px-4 py-3">
      <blockquote className="text-body-medium text-on-surface">{children}</blockquote>
      <figcaption className="mt-1 text-body-small text-on-surface-variant">{kaynak}</figcaption>
    </figure>
  );
}

/** Ekran bağlantısı — kılavuzdan doğrudan ilgili sayfaya (ya da sekmeye) atlar. */
export function Ekran({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      {children}
    </Link>
  );
}

/** Klavye kısayolu. */
export function Tus({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded-shape-xs border border-outline-variant bg-surface-container px-1.5 py-0.5 font-mono text-label-medium text-on-surface">
      {children}
    </kbd>
  );
}

/** Dosya yolu, komut ya da dosya adı. */
export function Kod({ children }: { children: ReactNode }) {
  return <code className="break-all font-mono text-body-small text-on-surface">{children}</code>;
}

/**
 * Başka bir ekrandan çapalı adresle gelindiğinde (`/kilavuz#bolum`) ilgili bölüme
 * kaydırır. Tarayıcı çapayı YALNIZ gerçek gezinmede kendisi uygular; SPA'da rota
 * değiştiğinde adresteki `#` yok sayılır, sayfa tepede açılırdı.
 */
export function useCapayaKaydir(): void {
  const { hash } = useLocation();
  useEffect(() => {
    if (!hash) return;
    const hedef = document.getElementById(decodeURIComponent(hash.slice(1)));
    // jsdom ve eski gömülü motorlarda yok olabilir; kaydırma kritik değildir.
    hedef?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }, [hash]);
}
