// Son oturum kartı (T15; tasarım §13 D4): temiz kapanış işareti yoksa kart görünür,
// "Kontrol ettim" kartı bu oturum için kapatır; durum okunamazsa kart görünmez.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, ETKINLIK_BASLIGI } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { panelApi } from "./api";
import SonOturumKarti, { SON_OTURUM_KARTI_BASLIGI } from "./SonOturumKarti";

const BASLANGIC = "2026-10-31T09:00:00+03:00";

function bas() {
  return render(
    <SnackbarProvider>
      <SonOturumKarti />
    </SnackbarProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Son oturum kartı", () => {
  it("işaret yoksa (beklenmedik kapanış) kart görünür", async () => {
    vi.spyOn(panelApi, "sonOturum").mockResolvedValue({
      unexpected_shutdown: true,
      process_started_at: BASLANGIC,
    });

    bas();

    expect(
      await screen.findByRole("heading", { name: SON_OTURUM_KARTI_BASLIGI }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Son oturumdaki kayıtları kontrol edin/)).toBeInTheDocument();
  });

  it("önceki oturum düzgün kapandıysa kart görünmez", async () => {
    const sorgu = vi.spyOn(panelApi, "sonOturum").mockResolvedValue({
      unexpected_shutdown: false,
      process_started_at: BASLANGIC,
    });

    const { container } = bas();

    await waitFor(() => expect(sorgu).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("durum okunamazsa kart görünmez", async () => {
    const sorgu = vi
      .spyOn(panelApi, "sonOturum")
      .mockRejectedValue(new ApiError(500, "sunucu_hatasi", "Sunucu hatası"));

    const { container } = bas();

    await waitFor(() => expect(sorgu).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("Kontrol ettim kartı kapatır", async () => {
    vi.spyOn(panelApi, "sonOturum").mockResolvedValue({
      unexpected_shutdown: true,
      process_started_at: BASLANGIC,
    });
    const onay = vi
      .spyOn(panelApi, "kontrolEttim")
      .mockResolvedValue({ unexpected_shutdown: false, process_started_at: BASLANGIC });

    bas();
    await userEvent.click(await screen.findByRole("button", { name: /Kontrol ettim/ }));

    expect(onay).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: SON_OTURUM_KARTI_BASLIGI }),
      ).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("Son oturumun kontrolü tamamlandı.")).toBeInTheDocument();
  });

  it("onay kaydedilemezse kart kalır ve hata gösterilir", async () => {
    vi.spyOn(panelApi, "sonOturum").mockResolvedValue({
      unexpected_shutdown: true,
      process_started_at: BASLANGIC,
    });
    vi.spyOn(panelApi, "kontrolEttim").mockRejectedValue(new ApiError(500, "sunucu_hatasi", "Sunucu hatası"));

    bas();
    await userEvent.click(await screen.findByRole("button", { name: /Kontrol ettim/ }));

    expect(await screen.findByText(/Sunucu hatası/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: SON_OTURUM_KARTI_BASLIGI })).toBeInTheDocument();
  });
});

describe("panelApi", () => {
  function yanit(govde: unknown): Response {
    return new Response(JSON.stringify(govde), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }

  it("durum sorgusu etkinlik başlığı göndermez; onay POST eder", async () => {
    const fetchSahte = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(yanit({ unexpected_shutdown: false, process_started_at: BASLANGIC })),
      );
    vi.stubGlobal("fetch", fetchSahte);

    await panelApi.sonOturum();
    await panelApi.kontrolEttim();

    const [url, secenek] = fetchSahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/dashboard/last-session/");
    expect((secenek.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBeUndefined();
    const [, onay] = fetchSahte.mock.calls[1] as [string, RequestInit];
    expect(onay.method).toBe("POST");
  });
});
