// Açık dosya penceresinin bildirimi (bağımsız denetim 13.11.2026): olay gelince geçici bildirim
// çıkar, dinleyici sökülünce temizlenir. Uygulama kökündeki yeri `App.test.tsx`'tedir.

import { act, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DosyaPenceresiBildirimi, {
  DOSYA_PENCERESI_ACIK_METNI,
  DOSYA_PENCERESI_ACIK_OLAYI,
} from "./DosyaPenceresiBildirimi";
import { SnackbarProvider } from "./ui/SnackbarProvider";

function olayYolla() {
  act(() => {
    window.dispatchEvent(new CustomEvent(DOSYA_PENCERESI_ACIK_OLAYI));
  });
}

function cizim() {
  return render(
    <SnackbarProvider>
      <DosyaPenceresiBildirimi />
    </SnackbarProvider>,
  );
}

describe("DosyaPenceresiBildirimi", () => {
  it("olay adı masaüstünün yolladığı addır", () => {
    expect(DOSYA_PENCERESI_ACIK_OLAYI).toBe("od:dosya-penceresi-acik");
  });

  it("olay gelmeden bildirim yoktur", () => {
    cizim();
    expect(screen.queryByText(DOSYA_PENCERESI_ACIK_METNI)).toBeNull();
  });

  it("olay gelince geçici bildirim çıkar", () => {
    cizim();

    olayYolla();

    expect(screen.getByText(DOSYA_PENCERESI_ACIK_METNI)).toBeInTheDocument();
  });

  it("söküldükten sonra olay bildirim çıkarmaz", () => {
    const { unmount } = cizim();
    unmount();

    olayYolla();

    expect(screen.queryByText(DOSYA_PENCERESI_ACIK_METNI)).toBeNull();
  });
});
