// `butunlukApi` sözleşmesi: yollar backend `urls.py`'deki "security/integrity/*" ile birebir;
// okumalar kullanıcı eylemi değildir (`X-OD-Etkinlik` gitmez, tasarım §4.4.3); yazmalar POST.

import { afterEach, describe, expect, it, vi } from "vitest";

import { ETKINLIK_BASLIGI, etkinlikSaatleriniSifirla } from "../../lib/api";
import { butunlukApi } from "./api";

function yanit(govde: unknown): Response {
  return new Response(JSON.stringify(govde), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function cagri(fetchSahte: ReturnType<typeof vi.fn>, sira: number): [string, RequestInit] {
  return fetchSahte.mock.calls[sira] as [string, RequestInit];
}

afterEach(() => {
  vi.unstubAllGlobals();
  etkinlikSaatleriniSifirla();
});

describe("butunlukApi", () => {
  it("okumalar GET'tir ve etkinlik başlığı göndermez (kullanıcı az önce etkileşmiş olsa da)", async () => {
    const fetchSahte = vi.fn().mockImplementation(() => Promise.resolve(yanit({})));
    vi.stubGlobal("fetch", fetchSahte);
    // Gerçek bir etkileşim (yakalama evresinde `lib/api` kaydeder).
    window.dispatchEvent(new Event("pointerdown"));

    await butunlukApi.durum();
    await butunlukApi.parolaBildirimi();

    const [durumYolu, durum] = cagri(fetchSahte, 0);
    expect(durumYolu).toBe("/api/v1/security/integrity/");
    expect(durum.method).toBe("GET");
    expect((durum.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBeUndefined();
    const [bildirimYolu, bildirim] = cagri(fetchSahte, 1);
    expect(bildirimYolu).toBe("/api/v1/security/integrity/reset-notice/");
    expect((bildirim.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBeUndefined();
  });

  it("sahipsiz parola kaydının silinmesi kimlik listesini POST eder", async () => {
    const fetchSahte = vi.fn().mockImplementation(() => Promise.resolve(yanit({ silinen: [] })));
    vi.stubGlobal("fetch", fetchSahte);

    await butunlukApi.sahipsizSarmallariSil(["0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f"]);

    const [yol, secenek] = cagri(fetchSahte, 0);
    expect(yol).toBe("/api/v1/security/integrity/orphan-wraps/");
    expect(secenek.method).toBe("POST");
    expect(JSON.parse(String(secenek.body))).toEqual({
      hesaplar: ["0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f"],
    });
  });

  it("“Gördüm” bildirimin ucuna POST eder ve kullanıcı eylemi sayılır", async () => {
    const fetchSahte = vi
      .fn()
      .mockImplementation(() => Promise.resolve(yanit({ parola_yenilenme: null })));
    vi.stubGlobal("fetch", fetchSahte);
    window.dispatchEvent(new Event("pointerdown"));

    await expect(butunlukApi.parolaBildiriminiGordum()).resolves.toEqual({
      parola_yenilenme: null,
    });

    const [yol, secenek] = cagri(fetchSahte, 0);
    expect(yol).toBe("/api/v1/security/integrity/reset-notice/");
    expect(secenek.method).toBe("POST");
    expect((secenek.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBe("1");
  });
});
