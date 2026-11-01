// "Okunamayan Kayıt Alanları" kartı (tasarım TK8 (3), §13 D48): güvenlik durumundaki
// çözülemeyen alan sayısı sıfırdan büyükse çıkar; kişisizdir (yalnız sayı); sıfırsa ya
// da durum okunamazsa hiçbir şey göstermez.

import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";

const guvenlik = vi.hoisted(() => ({ durum: vi.fn() }));
vi.mock("../guvenlik/api", () => ({ guvenlikApi: guvenlik }));

import OkunamayanAlanlarKarti, { OKUNAMAYAN_ALANLAR_BASLIGI } from "./OkunamayanAlanlarKarti";

afterEach(() => vi.clearAllMocks());

describe("OkunamayanAlanlarKarti", () => {
  it("çözülemeyen alan varsa sayıyı ve ne yapılacağını söyler; kişi adı yok", async () => {
    guvenlik.durum.mockResolvedValue({ corrupt_field_count: 3 });
    const { container } = render(<OkunamayanAlanlarKarti />);

    expect(
      await screen.findByRole("region", { name: OKUNAMAYAN_ALANLAR_BASLIGI }),
    ).toBeInTheDocument();
    expect(OKUNAMAYAN_ALANLAR_BASLIGI).toBe("Okunamayan Kayıt Alanları");
    expect(screen.getByText(/3 şifreli alan okunamadı/)).toBeInTheDocument();
    expect(screen.getByText(/ekranda “okunamadı” diye görünür/)).toBeInTheDocument();
    expect(
      screen.getByText(/program yöneticisine ve Denetleme Kuruluna bildirin/),
    ).toBeInTheDocument();
    // İç kodlar yüzeye çıkmaz (sözlük §2).
    expect(container.textContent).not.toMatch(/D48|CorruptField|bozuk_alanlar/);
  });

  it("sayı sıfırsa kart görünmez", async () => {
    guvenlik.durum.mockResolvedValue({ corrupt_field_count: 0 });
    const { container } = render(<OkunamayanAlanlarKarti />);

    await waitFor(() => expect(guvenlik.durum).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("alan yoksa (eski yanıt) ya da durum okunamazsa kart görünmez", async () => {
    guvenlik.durum.mockResolvedValueOnce({});
    const ilk = render(<OkunamayanAlanlarKarti />);
    await waitFor(() => expect(guvenlik.durum).toHaveBeenCalledTimes(1));
    expect(ilk.container).toBeEmptyDOMElement();
    ilk.unmount();

    guvenlik.durum.mockRejectedValueOnce(new ApiError(500, "error", "Sunucu hatası."));
    const ikinci = render(<OkunamayanAlanlarKarti />);
    await waitFor(() => expect(guvenlik.durum).toHaveBeenCalledTimes(2));
    expect(ikinci.container).toBeEmptyDOMElement();
  });
});
