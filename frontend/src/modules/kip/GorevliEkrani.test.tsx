// Görevli ekranı — aile iskeletinin kütüphane masa işleri F1a-2'de söküldü.
// Sabitlenen davranışlar:
//
//   1) Sayfanın h1'i "Görevli Kipi"dir (üst çubukla aynı); ekran ne yapılacağını söyler.
//   2) Yönetici kipine geçiş açıktır (parola diyaloğu).
//   3) Bekleyen kurtarma anahtarı uyarısı görünür.
//   4) Masa işlerinin düğmeleri (dolaşım, doğrulama, katalog, geri alma, sayım) yoktur.

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import GorevliEkrani, {
  BEKLEYEN_ANAHTAR_METNI,
  GOREVLI_EKRANI_BASLIGI,
  GOREVLI_EKRANI_METNI,
} from "./GorevliEkrani";

describe("GorevliEkrani", () => {
  it("başlık ve açıklama görünür; masa işleri sökülmüştür", () => {
    render(<GorevliEkrani onGecti={vi.fn()} />);

    expect(screen.getByRole("heading", { level: 1, name: GOREVLI_EKRANI_BASLIGI })).toBeVisible();
    expect(screen.getByText(GOREVLI_EKRANI_METNI)).toBeInTheDocument();
    for (const ad of [
      /Doğrulama okutmasını aç/,
      /Katalogda ara/,
      /Teslimden geri al/,
      /Sayım okutmasını aç/,
    ]) {
      expect(screen.queryByRole("button", { name: ad })).toBeNull();
    }
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("Yönetici kipine geç düğmesi parola diyaloğunu açar", async () => {
    const user = userEvent.setup();
    render(<GorevliEkrani onGecti={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Yönetici kipine geç" }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("bekleyen kurtarma anahtarı uyarısı görünür", () => {
    render(<GorevliEkrani onGecti={vi.fn()} anahtarBekliyor />);

    expect(screen.getByText(BEKLEYEN_ANAHTAR_METNI)).toBeInTheDocument();
  });

  it("anahtar beklemiyorsa uyarı görünmez", () => {
    render(<GorevliEkrani onGecti={vi.fn()} />);

    expect(screen.queryByText(BEKLEYEN_ANAHTAR_METNI)).toBeNull();
  });
});
