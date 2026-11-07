// Yoğunluk düğmesi: renk sözleşmesi. `className` verilirse varsayılan rengin YERİNE geçer; iki
// `text-*` sınıfı yan yana durursa kazananı Tailwind çıktısının sırası belirler (gerçek pencere
// sınaması 07.11.2026: kenar çubuğunda açık temada yazı okunmuyordu).

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import DensitySwitcher from "./DensitySwitcher";

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-density");
});

describe("DensitySwitcher", () => {
  it("varsayılan rengi yüzey rengidir", () => {
    render(<DensitySwitcher />);
    expect(screen.getByRole("button")).toHaveClass(
      "text-on-surface-variant",
      "hover:bg-on-surface/8",
      "hover:text-on-surface",
    );
  });

  it("className varsayılan rengin yerine geçer, yanına eklenmez", () => {
    render(<DensitySwitcher className="text-on-sidebar-muted hover:text-on-sidebar" />);
    const dugme = screen.getByRole("button");

    expect(dugme).toHaveClass("text-on-sidebar-muted", "hover:text-on-sidebar");
    expect(dugme).not.toHaveClass("text-on-surface-variant");
    expect(dugme).not.toHaveClass("hover:text-on-surface");
    expect(dugme).not.toHaveClass("hover:bg-on-surface/8");
  });

  it("daralmış kenar çubuğunda yazı yoktur", () => {
    render(<DensitySwitcher collapsed />);
    expect(screen.queryByText("Kompakt görünüm")).toBeNull();
    expect(screen.getByRole("button", { name: "Rahat görünüme geç" })).toBeInTheDocument();
  });
});
