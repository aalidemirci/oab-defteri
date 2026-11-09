// Okul kartının kural paketi bilgisi: uç adresi, başarılı yanıt, başarısız istek (bilgi çıkmaz).

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ORNEK_KANTIN_BILGISI } from "../../test/okulKarti";

const apiMock = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock("../../lib/api", () => ({ api: apiMock }));

import { useKantinIsletmeBilgisi } from "./kuralBilgileri";

afterEach(() => vi.clearAllMocks());

describe("useKantinIsletmeBilgisi", () => {
  it("bilgiyi paketin ucundan alır", async () => {
    apiMock.get.mockResolvedValue({ kantin_isletme_bilgisi: ORNEK_KANTIN_BILGISI });
    const { result } = renderHook(() => useKantinIsletmeBilgisi());
    expect(result.current).toBeNull();
    await waitFor(() => expect(result.current).toEqual(ORNEK_KANTIN_BILGISI));
    expect(apiMock.get).toHaveBeenCalledWith("/oab/okul-karti-bilgileri/");
  });

  it("paket okunamadıysa ya da istek başarısızsa null kalır", async () => {
    apiMock.get.mockRejectedValue(new Error("ağ"));
    const { result } = renderHook(() => useKantinIsletmeBilgisi());
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled());
    await Promise.resolve();
    expect(result.current).toBeNull();
  });
});
