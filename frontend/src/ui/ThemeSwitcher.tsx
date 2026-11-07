// M3 tema değiştirici — Top App Bar'a yerleştirilir. Açık/karanlık ikon arasında
// geçiş yapar; tercih localStorage'a yazılır.
//
// Erişilebilirlik: yoğunluğa duyarlı hedef, aria-label, görünür focus halkası.
//
// SATIR KİPİ (`satir`): kenar çubuğunda "Tema" yazısı düğmenin içindedir, satırın tamamı basılır
// (gerçek pencere sınaması 07.11.2026: yazı düğme gibi duruyor, yalnız simge basılıyordu).
// Erişilebilir ad iki kipte de eylemdir ("Karanlık temaya geç"); yazı onu değiştirmez.
//
// RENK: `className` verilirse varsayılan rengin YERİNE geçer. İki `text-*` sınıfı yan yana durursa
// kazananı sınıf sırası değil Tailwind çıktısının sırası belirler (DensitySwitcher ile aynı kalıp).

import { useTheme } from "../hooks/useTheme";
import Icon from "./Icon";

interface Props {
  /** Renk sınıfları; varsayılan rengin yerine geçer (dosya başı notu). */
  className?: string;
  /** Yazılı, tam genişlikte satır (dosya başı notu). */
  satir?: boolean;
  /** Daralmış kenar çubuğu: satırda yazı yoktur, simge ortalanır. */
  collapsed?: boolean;
}

const VARSAYILAN_RENK = "text-on-surface-variant hover:bg-on-surface/8 hover:text-on-surface";

export default function ThemeSwitcher({
  className = VARSAYILAN_RENK,
  satir = false,
  collapsed = false,
}: Props) {
  const { isDark, toggle } = useTheme();
  const label = isDark ? "Açık temaya geç" : "Karanlık temaya geç";
  const bicim = !satir
    ? "inline-flex h-[var(--od-control-height)] w-[var(--od-control-height)] items-center justify-center rounded-shape-sm"
    : `flex min-h-[var(--od-control-height)] w-full items-center rounded-shape-md text-label-large ${
        collapsed ? "justify-center px-2" : "gap-3 px-3"
      }`;
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      aria-pressed={isDark}
      className={`group relative overflow-hidden transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${bicim} ${className}`}
    >
      {/* M3 state layer — parent overflow-hidden + rounded-full örtüyü kırpar. */}
      <span aria-hidden="true" className="state-layer" />
      <Icon name={isDark ? "light_mode" : "dark_mode"} size={satir ? "lg" : undefined} />
      {satir && !collapsed && <span>Tema</span>}
    </button>
  );
}
