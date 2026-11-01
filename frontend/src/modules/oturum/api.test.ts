// Oturum API istemcisi — uç yolları, Türkçe gövde anahtarları ve etkinlik sözleşmesi
// backend `apps/okul/urls.py` (security/session, accounts, unlock, lock, recover,
// change-password, idle-lock) ve `views_oturum.py` ile birebir. Kip uçları
// (`security/mode/*`) yoktur.

import { beforeEach, describe, expect, it, vi } from "vitest";

const apiSahte = vi.hoisted(() => ({
  get: vi.fn().mockResolvedValue({}),
  post: vi.fn().mockResolvedValue({}),
  put: vi.fn().mockResolvedValue({}),
}));

vi.mock("../../lib/api", () => ({ api: apiSahte }));

import { oturumApi } from "./api";

describe("oturumApi", () => {
  beforeEach(() => vi.clearAllMocks());

  it("özet yoklaması varsayılan olarak etkinlik başlığı göndermez", async () => {
    await oturumApi.ozet();
    expect(apiSahte.get).toHaveBeenCalledWith("/security/session/", { etkinlik: false });
  });

  it("nabız sorgusu etkinlik kuralına bırakılır", async () => {
    await oturumApi.ozet(true);
    expect(apiSahte.get).toHaveBeenCalledWith("/security/session/", { etkinlik: true });
  });

  it("kilit ekranının ve kurtarmanın hesap listeleri etkinliksiz okunur", async () => {
    await oturumApi.hesaplar();
    await oturumApi.kurtarmaHesaplari();
    expect(apiSahte.get.mock.calls).toEqual([
      ["/security/accounts/", { etkinlik: false }],
      ["/security/recover/", { etkinlik: false }],
    ]);
  });

  it("açma, kurtarma, Kilitle ve parola değişimi Türkçe gövdeyle gider", async () => {
    await oturumApi.ac({ hesap: "h-1", parola: "Deneme-Parola-1" });
    await oturumApi.ac({ hesap: "h-1", parola: "Gecici-Parola-1", yeni_parola: "Yeni-Parola-22" });
    await oturumApi.kurtar({
      kurtarma_anahtari: "AAAA-BBBB",
      hesap: "yonetici",
      yeni_parola: "Yeni-Parola-22",
    });
    await oturumApi.kilitle();
    await oturumApi.parolaDegistir("Eski-Parola-1", "Yeni-Parola-22");
    expect(apiSahte.post.mock.calls).toEqual([
      ["/security/unlock/", { hesap: "h-1", parola: "Deneme-Parola-1" }],
      [
        "/security/unlock/",
        { hesap: "h-1", parola: "Gecici-Parola-1", yeni_parola: "Yeni-Parola-22" },
      ],
      [
        "/security/recover/",
        { kurtarma_anahtari: "AAAA-BBBB", hesap: "yonetici", yeni_parola: "Yeni-Parola-22" },
      ],
      ["/security/lock/"],
      ["/security/change-password/", { parola: "Eski-Parola-1", yeni_parola: "Yeni-Parola-22" }],
    ]);
  });

  it("boşta kilit süresi okunur ve yazılır", async () => {
    await oturumApi.bostaKilitSuresi();
    await oturumApi.bostaKilitSuresiniYaz(15);
    expect(apiSahte.get).toHaveBeenCalledWith("/security/idle-lock/");
    expect(apiSahte.put).toHaveBeenCalledWith("/security/idle-lock/", { dakika: 15 });
  });
});
