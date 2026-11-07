// Tur 46 — ThemeSwitcher davranış testi.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ThemeSwitcher from "./ThemeSwitcher";

describe("ThemeSwitcher", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    delete window.pywebview;
  });
  afterEach(() => {
    document.documentElement.removeAttribute("data-theme");
    delete window.pywebview;
  });

  it("varsayılan açık tema; tıklanınca karanlığa geçer", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);

    const btn = screen.getByRole("button", { name: /karanlık temaya geç/i });
    expect(btn).toHaveAttribute("aria-pressed", "false");
    expect(document.documentElement.getAttribute("data-theme")).toBeNull();

    await user.click(btn);

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(window.localStorage.getItem("oab-defteri-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: /açık temaya geç/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("yoğunluğa duyarlı kare hedef kullanır", () => {
    render(<ThemeSwitcher />);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("h-[var(--od-control-height)]");
    expect(btn.className).toContain("w-[var(--od-control-height)]");
  });

  it("satır kipinde yazı düğmenin içindedir, erişilebilir ad değişmez", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher satir />);

    const btn = screen.getByRole("button", { name: "Karanlık temaya geç" });
    expect(btn).toContainElement(screen.getByText("Tema"));
    expect(btn).toHaveClass("w-full", "min-h-[var(--od-control-height)]");
    expect(btn).not.toHaveClass("w-[var(--od-control-height)]");

    await user.click(screen.getByText("Tema"));

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: "Açık temaya geç" })).toBeInTheDocument();
  });

  it("satır kipinde simge kenar çubuğunun simge boyundadır", () => {
    render(<ThemeSwitcher satir />);
    expect(screen.getByText("dark_mode")).toHaveClass("text-lg");
  });

  it("daralmış satırda yazı yoktur, simge ortalanır", () => {
    render(<ThemeSwitcher satir collapsed />);
    expect(screen.queryByText("Tema")).toBeNull();
    expect(screen.getByRole("button", { name: "Karanlık temaya geç" })).toHaveClass(
      "justify-center",
    );
  });

  it("className varsayılan rengin yerine geçer, yanına eklenmez", () => {
    const { rerender } = render(<ThemeSwitcher />);
    expect(screen.getByRole("button")).toHaveClass("text-on-surface-variant");

    rerender(<ThemeSwitcher className="text-on-sidebar-muted" />);
    expect(screen.getByRole("button")).toHaveClass("text-on-sidebar-muted");
    expect(screen.getByRole("button")).not.toHaveClass("text-on-surface-variant");
  });

  it("merkezî .state-layer örtü span'ı içerir (M3 state layer)", () => {
    const { container } = render(<ThemeSwitcher />);
    const layer = container.querySelector('[aria-hidden="true"]');
    expect(layer).not.toBeNull();
    expect(layer?.className).toMatch(/state-layer/);
  });

  it("tema değişimini Windows başlık çubuğuna iletir", async () => {
    const user = userEvent.setup();
    const setTitlebarTheme = vi.fn().mockResolvedValue(true);
    window.pywebview = { api: { set_titlebar_theme: setTitlebarTheme } };

    render(<ThemeSwitcher />);
    expect(setTitlebarTheme).toHaveBeenCalledWith(false);

    await user.click(screen.getByRole("button", { name: /karanlık temaya geç/i }));
    expect(setTitlebarTheme).toHaveBeenLastCalledWith(true);
  });
});
