// Çık (tasarım §4.2, §4.5): üst çubuktaki düğme her durumda görünür ve HER oturum
// durumunda parolasız bir onaydır ("Programdan çıkılsın mı?"); aile iskeletinin görevli
// kipindeki parola dalı kalktı. Tepsi yoktur (T6): diyalog yalnız düğmeyle açılır.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";

const cikis = vi.hoisted(() => ({ cik: vi.fn() }));

vi.mock("./api", async (orijinal) => ({
  ...(await orijinal<typeof import("./api")>()),
  cikisApi: cikis,
}));

import CikisDugmesi, { CikisDiyalogu, DogrudanCikisDugmesi } from "./CikisDugmesi";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("CikisDugmesi", () => {
  it("parolasız onayla çıkar; diyalogda parola alanı yoktur", async () => {
    const kullanici = userEvent.setup();
    cikis.cik.mockResolvedValue({ durum: "kapaniyor" });
    render(<CikisDugmesi />);

    await kullanici.click(screen.getByRole("button", { name: "Çık" }));
    const diyalog = screen.getByRole("dialog", { name: "Programdan çıkılsın mı?" });
    // T6: çarpı programı kapatır; aile iskeletinin "yalnız gizler" ve Ağ Kataloğu
    // cümleleri yoktur.
    expect(diyalog).toHaveTextContent("Pencerenin çarpısı da programı aynı biçimde kapatır.");
    expect(diyalog).not.toHaveTextContent(/Ağ Kataloğu|gizler|görevli/i);
    expect(within(diyalog).queryByLabelText(/parola/i)).toBeNull();
    await kullanici.click(within(diyalog).getByRole("button", { name: "Çık" }));

    expect(cikis.cik).toHaveBeenCalledWith();
    expect(await screen.findByRole("status")).toHaveTextContent("kapanıyor");
  });

  it("çıkış reddedilirse iletiyi gösterir, diyalog açık kalır", async () => {
    const kullanici = userEvent.setup();
    cikis.cik.mockRejectedValue(
      new ApiError(503, "cikis_kullanilamiyor", "Program masaüstü penceresinde çalışmıyor."),
    );
    render(<CikisDugmesi />);

    await kullanici.click(screen.getByRole("button", { name: "Çık" }));
    const diyalog = screen.getByRole("dialog");
    await kullanici.click(within(diyalog).getByRole("button", { name: "Çık" }));

    expect(await within(diyalog).findByRole("alert")).toHaveTextContent("masaüstü penceresinde");
    expect(within(diyalog).queryByText(/cikis_kullanilamiyor/)).toBeNull();
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("ağ hatasında genel ileti gösterilir", async () => {
    const kullanici = userEvent.setup();
    cikis.cik.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<CikisDiyalogu open onClose={vi.fn()} />);

    await kullanici.click(screen.getByRole("button", { name: "Çık" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Programdan çıkılamadı.");
  });

  it("Vazgeç diyaloğu kapatır, istek gitmez", async () => {
    const kullanici = userEvent.setup();
    render(<CikisDugmesi />);

    await kullanici.click(screen.getByRole("button", { name: "Çık" }));
    await kullanici.click(screen.getByRole("button", { name: "Vazgeç" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(cikis.cik).not.toHaveBeenCalled();
  });
});

describe("DogrudanCikisDugmesi", () => {
  it("yeniden başlat ekranında parolasız çıkar", async () => {
    const kullanici = userEvent.setup();
    cikis.cik.mockResolvedValue({ durum: "kapaniyor" });
    render(<DogrudanCikisDugmesi />);

    await kullanici.click(screen.getByRole("button", { name: "Programdan çık" }));

    expect(cikis.cik).toHaveBeenCalledWith();
    expect(await screen.findByRole("status")).toHaveTextContent("kapanıyor");
  });

  it("masaüstü dışında (geliştirme) hatayı gösterir", async () => {
    const kullanici = userEvent.setup();
    cikis.cik.mockRejectedValue(
      new ApiError(503, "cikis_kullanilamiyor", "Program masaüstü penceresinde çalışmıyor."),
    );
    render(<DogrudanCikisDugmesi />);

    await kullanici.click(screen.getByRole("button", { name: "Programdan çık" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("masaüstü penceresinde");
  });
});
