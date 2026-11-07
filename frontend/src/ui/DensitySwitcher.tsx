// Yoğunluk düğmesi. RENK: `className` verilirse varsayılan rengin YERİNE geçer. İki `text-*` sınıfı
// yan yana durursa kazananı sınıf sırası değil Tailwind çıktısının sırası belirler: kenar çubuğunda
// `text-on-surface-variant` kazanıyor, açık temada koyu gri yazı koyu zemine düşüyordu (gerçek
// pencere sınaması 07.11.2026).

import { useDensity } from "../hooks/useDensity";
import Icon from "./Icon";

interface DensitySwitcherProps {
  collapsed?: boolean;
  /** Renk sınıfları; varsayılan rengin yerine geçer (dosya başı notu). */
  className?: string;
}

const VARSAYILAN_RENK = "text-on-surface-variant hover:bg-on-surface/8 hover:text-on-surface";

export default function DensitySwitcher({
  collapsed = false,
  className = VARSAYILAN_RENK,
}: DensitySwitcherProps) {
  const { isComfortable, toggle } = useDensity();
  const label = isComfortable ? "Kompakt görünüme geç" : "Rahat görünüme geç";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      aria-pressed={isComfortable}
      className={`group relative flex min-h-[var(--od-control-height)] items-center overflow-hidden rounded-shape-md text-label-large transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
        collapsed ? "w-full justify-center px-2" : "w-full gap-3 px-3"
      } ${className}`}
    >
      <Icon name={isComfortable ? "density_small" : "density_medium"} size="lg" />
      {!collapsed && <span>{isComfortable ? "Rahat görünüm" : "Kompakt görünüm"}</span>}
    </button>
  );
}
