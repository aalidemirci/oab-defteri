// Çık ucu istemcisi: her oturum durumunda parolasız, boş gövde; etkinlik başlığı
// gönderilmez (tasarım §4.2, §4.5; aile iskeletinin görevli kipi parola dalı kalktı).

import { afterEach, describe, expect, it, vi } from "vitest";

import { ETKINLIK_BASLIGI } from "../../lib/api";
import { cikisApi } from "./api";

function yanit(): Response {
  return new Response(JSON.stringify({ durum: "kapaniyor" }), {
    status: 202,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("cikisApi", () => {
  it("parolasız, boş gövdeyle ve etkinlik başlığı olmadan POST eder", async () => {
    const fetchSahte = vi.fn().mockResolvedValue(yanit());
    vi.stubGlobal("fetch", fetchSahte);
    // Kullanıcı az önce tıkladı: başlık yine gitmez (çıkış oturumu canlı tutmaz).
    window.dispatchEvent(new Event("pointerdown"));

    await cikisApi.cik();

    const [url, secenek] = fetchSahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/app/quit/");
    expect(secenek.method).toBe("POST");
    expect(secenek.body).toBe("{}");
    expect((secenek.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBeUndefined();
  });
});
