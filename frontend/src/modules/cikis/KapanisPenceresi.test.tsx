// Kapanış bekleme penceresi (plan F1b-3 "Uzun iş, çarpı, temiz kapanış"): olay gelince açılır,
// kapatılamaz, iki olay tek pencere yapar, dinleyici temizlenir. Uygulama kökündeki yeri
// `App.test.tsx`'tedir.

import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import KapanisPenceresi, { KAPANIS_BEKLIYOR_OLAYI } from "./KapanisPenceresi";
import { KAPANIS_BEKLENIYOR_METNI, PROGRAM_KAPANIYOR_BASLIGI } from "./metinler";

function olayYolla() {
  act(() => {
    window.dispatchEvent(new CustomEvent(KAPANIS_BEKLIYOR_OLAYI));
  });
}

afterEach(() => vi.restoreAllMocks());

describe("KapanisPenceresi", () => {
  it("olay gelmeden hiçbir şey çizmez", () => {
    const { container } = render(<KapanisPenceresi />);
    expect(container).toBeEmptyDOMElement();
  });

  it("olay adı masaüstünün yolladığı addır", () => {
    expect(KAPANIS_BEKLIYOR_OLAYI).toBe("od:kapanis-bekliyor");
  });

  it("olay gelince Çık'ın kalıbıyla açılır; düğmesi yoktur", () => {
    render(<KapanisPenceresi />);

    olayYolla();

    expect(screen.getByRole("dialog", { name: PROGRAM_KAPANIYOR_BASLIGI })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(KAPANIS_BEKLENIYOR_METNI);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("Esc ve dış tıklama pencereyi kapatmaz", () => {
    render(<KapanisPenceresi />);
    olayYolla();
    const pencere = screen.getByRole("dialog");

    fireEvent.keyDown(document, { key: "Escape" });
    fireEvent.mouseDown(pencere.parentElement as HTMLElement);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("olay iki kez gelse tek pencere olur", () => {
    render(<KapanisPenceresi />);

    olayYolla();
    olayYolla();

    expect(screen.getAllByRole("dialog")).toHaveLength(1);
  });

  it("yeniden başlat ekranının (z-[60]) üstünde açılır", () => {
    render(<KapanisPenceresi />);

    olayYolla();

    expect(screen.getByRole("dialog").parentElement).toHaveClass("z-[70]");
  });

  it("bileşen kalkınca dinleyici de kalkar", () => {
    const ekle = vi.spyOn(window, "addEventListener");
    const kaldir = vi.spyOn(window, "removeEventListener");
    const { unmount } = render(<KapanisPenceresi />);
    const eklenen = ekle.mock.calls.find(([ad]) => ad === KAPANIS_BEKLIYOR_OLAYI);

    unmount();

    expect(eklenen).toBeDefined();
    expect(
      kaldir.mock.calls.some(
        ([ad, dinleyici]) => ad === KAPANIS_BEKLIYOR_OLAYI && dinleyici === eklenen?.[1],
      ),
    ).toBe(true);
  });
});
