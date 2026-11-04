// Kullanıcılar istemcisi backend `views_hesaplar.py` uçlarıyla birebir: yollar, yöntemler, Türkçe
// gövde anahtarları; geçici parola yalnız gövdede gider. Pusulanın adı sunucunun başlığındandır.

import { afterEach, describe, expect, it, vi } from "vitest";

import { kullanicilarApi } from "./api";

function jsonYanit(govde: unknown, status = 200) {
  return { ok: true, status, json: () => Promise.resolve(govde) };
}

function cagri(fetchSahte: ReturnType<typeof vi.fn>, i = 0) {
  const [url, istek] = fetchSahte.mock.calls[i] as [string, RequestInit];
  return {
    url,
    method: istek.method,
    govde: istek.body === undefined ? undefined : JSON.parse(String(istek.body)),
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("kullanicilarApi", () => {
  it("liste `hesaplar` dizisini döndürür; seçenekler ve ayrıntı GET'tir", async () => {
    const fetchSahte = vi
      .fn()
      .mockResolvedValueOnce(jsonYanit({ hesaplar: [{ id: "h-1" }] }))
      .mockResolvedValueOnce(jsonYanit({ roller: [] }))
      .mockResolvedValueOnce(jsonYanit({ id: "h-1" }));
    vi.stubGlobal("fetch", fetchSahte);

    expect(await kullanicilarApi.liste()).toEqual([{ id: "h-1" }]);
    expect(await kullanicilarApi.secenekler()).toEqual({ roller: [] });
    expect(await kullanicilarApi.ayrinti("h-1")).toEqual({ id: "h-1" });
    expect([0, 1, 2].map((i) => [cagri(fetchSahte, i).method, cagri(fetchSahte, i).url])).toEqual([
      ["GET", "/api/v1/accounts/"],
      ["GET", "/api/v1/accounts/options/"],
      ["GET", "/api/v1/accounts/h-1/"],
    ]);
  });

  it("hesap açma ve parola sıfırlama Türkçe anahtarlarla POST'tur", async () => {
    const fetchSahte = vi.fn().mockResolvedValue(jsonYanit({ hesap: {} }, 201));
    vi.stubGlobal("fetch", fetchSahte);

    await kullanicilarApi.ac({
      rol: "muhasip",
      tanitici: "muhasip",
      ad_soyad: "Deneme Kişi",
      gecici_parola: "Ad3+fHn7=rT2",
    });
    await kullanicilarApi.parolaSifirla("h-2", "Te4%dR9*aN5h");

    expect(cagri(fetchSahte, 0)).toEqual({
      url: "/api/v1/accounts/",
      method: "POST",
      govde: {
        rol: "muhasip",
        tanitici: "muhasip",
        ad_soyad: "Deneme Kişi",
        gecici_parola: "Ad3+fHn7=rT2",
      },
    });
    expect(cagri(fetchSahte, 1)).toEqual({
      url: "/api/v1/accounts/h-2/reset-password/",
      method: "POST",
      govde: { gecici_parola: "Te4%dR9*aN5h" },
    });
  });

  it("kapama ve askıdan çıkarma gövdesiz POST'tur", async () => {
    const fetchSahte = vi.fn().mockResolvedValue(jsonYanit({ hesap: {} }));
    vi.stubGlobal("fetch", fetchSahte);

    await kullanicilarApi.kapat("h-3");
    await kullanicilarApi.askidanCikar("h-3");

    expect(cagri(fetchSahte, 0)).toEqual({
      url: "/api/v1/accounts/h-3/close/",
      method: "POST",
      govde: undefined,
    });
    expect(cagri(fetchSahte, 1)).toEqual({
      url: "/api/v1/accounts/h-3/unsuspend/",
      method: "POST",
      govde: undefined,
    });
  });

  it("pusula POST'tur; dosya adı sunucunun Content-Disposition'ından", async () => {
    const ad = "Hesap-Teslim-Pusulası_Denetleme-Kurulu_03.11.2026.pdf";
    const fetchSahte = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        "Content-Disposition": `attachment; filename*=utf-8''${encodeURIComponent(ad)}`,
      }),
      blob: () => Promise.resolve(new Blob(["%PDF"])),
    });
    vi.stubGlobal("fetch", fetchSahte);

    const dosya = await kullanicilarApi.pusula("h-4");

    expect(dosya.ad).toBe(ad);
    expect(cagri(fetchSahte).url).toBe("/api/v1/accounts/h-4/handover-slip/");
    expect(cagri(fetchSahte).method).toBe("POST");
  });
});
