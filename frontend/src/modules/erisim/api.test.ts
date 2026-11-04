// `erisimGunluguApi` sözleşmesi: yol backend `urls.py`'deki `access-log/` ile birebir; süzgeçler
// sorgu metnidir (boş değer ve ilk sayfa gönderilmez; tarih ISO yyyy-aa-gg); okuma GET'tir.

import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { erisimGunluguApi, sorguMetni } from "./api";

function yanit(govde: unknown, status = 200): Response {
  return new Response(JSON.stringify(govde), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("sorguMetni", () => {
  it("boş süzgeç ve ilk sayfa sorgu metni üretmez", () => {
    expect(sorguMetni({})).toBe("");
    expect(sorguMetni({ baslangic: "", bitis: "", tur: "", hesap: "", sayfa: 1 })).toBe("");
  });

  it("dolu süzgeçler sunucunun adlarıyla yazılır", () => {
    const metin = sorguMetni({
      baslangic: "2026-11-01",
      bitis: "2026-11-03",
      tur: "KISI_DOKUMU",
      hesap: "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f",
      sayfa: 2,
    });
    expect(Object.fromEntries(new URLSearchParams(metin.slice(1)))).toEqual({
      baslangic: "2026-11-01",
      bitis: "2026-11-03",
      tur: "KISI_DOKUMU",
      hesap: "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f",
      sayfa: "2",
    });
    expect(metin.startsWith("?")).toBe(true);
  });
});

describe("erisimGunluguApi", () => {
  it("sayfa GET access-log/'tur; yanıt olduğu gibi döner", async () => {
    const govde = { satirlar: [], toplam: 0, sayfa: 1, sayfa_sayisi: 1, sayfa_boyutu: 50 };
    const fetchSahte = vi.fn().mockResolvedValue(yanit(govde));
    vi.stubGlobal("fetch", fetchSahte);

    await expect(erisimGunluguApi.sayfa({ tur: "KISI_DOKUMU" })).resolves.toEqual(govde);

    const [yol, istek] = fetchSahte.mock.calls[0] as [string, RequestInit];
    expect(yol).toMatch(/\/access-log\/\?tur=KISI_DOKUMU$/);
    expect(istek.method).toBe("GET");
  });

  it("biçimsiz süzgecin reddi alanıyla gelir", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        yanit(
          {
            code: "validation_error",
            message: "Tarih geçersiz.",
            fields: { bitis: ["Tarih geçersiz."] },
          },
          400,
        ),
      ),
    );

    const hata = await erisimGunluguApi.sayfa({ bitis: "9999-12-31" }).catch((e: unknown) => e);
    expect(hata).toBeInstanceOf(ApiError);
    expect((hata as ApiError).fields).toEqual({ bitis: ["Tarih geçersiz."] });
  });
});
