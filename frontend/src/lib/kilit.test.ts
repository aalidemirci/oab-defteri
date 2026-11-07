// D53 sözleşmesi (tasarım §4.4.3 "Ön yüz belleği", §13 D53, §10.6 `kilit.test.ts`; plan
// F1b-1 "Oturum"): kilitlenmede ve kilit ekranından her açılışta pencere içeriği yeniden
// yüklenir — önceki hesabın sorgu önbelleği ve modül belleği sonraki hesaba kalmaz.
// Pinlenen anlar: elle Kilitle, oturum yoklamasının gördüğü boşta kilit, ön yüz oturumu
// açık sanırken gelen 423, kilit açma ve kurtarma anahtarıyla açılış. Pinlenen yüklemeyen
// anlar: ön yüz zaten kilitli bilirken gelen 423 (döngü koruması), kurulumdaki ilk hesap,
// parola değişimi, ertelenen Kilitle ve başarısız açılış.
//
// Ağ en alttan (`fetch`) taklit edilir: `lib/api.ts`, oturum istemcisi ve eylemler
// gerçektir. Yeniden yükleme `test/setup.ts`'te her test için taze bir taklittir.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement } from "react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "./api";
import {
  KILIT_KAPISI_OLAYI,
  kilitlendi,
  oturumAcikSan,
  oturumAcikSaniliyor,
  pencereIcerigi,
  yenidenYuklemeIstendi,
} from "./kilit";
import {
  ilkHesabiKur,
  kilidiAc,
  kurtarmaAnahtariylaAc,
  oturumuKilitle,
  parolayiDegistir,
} from "../modules/oturum/eylemler";
import type { OturumOzeti } from "../modules/oturum/api";
import { useOturum } from "../modules/oturum/useOturum";

const ACIK: OturumOzeti = {
  durum: "acik",
  hesap: {
    id: "h-1",
    tanitici: "yonetici",
    rol: "yonetici",
    rol_etiketi: "Program yöneticisi",
    yetenekler: [],
  },
  bosta_dk: 10,
  bosta_kalan_sn: 600,
  kilit_bekliyor: false,
  kurulum_tamam: true,
  yukleme_siniri_mb: 20,
};
const KILITLI: OturumOzeti = { ...ACIK, durum: "kilitli", hesap: null, bosta_kalan_sn: null };

function yanit(status: number, govde: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(govde),
    blob: () => Promise.resolve(new Blob()),
  };
}

/** Her isteğe aynı yanıtı veren `fetch` taklidi. */
function fetchHep(status: number, govde: unknown) {
  const sahte = vi.fn().mockResolvedValue(yanit(status, govde));
  vi.stubGlobal("fetch", sahte);
  return sahte;
}

const KILITLI_423 = {
  code: "locked",
  message:
    "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız program " +
    "yöneticisine başvurun).",
  fields: {},
};

function yuklemeSayisi(): number {
  return vi.mocked(pencereIcerigi.yenidenYukle).mock.calls.length;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("kilitlenme pencereyi yeniden yükler", () => {
  it("elle Kilitle (kurulumda bayrak kalkmamış olsa da)", async () => {
    fetchHep(200, { sonuc: "kilitlendi", ...KILITLI });
    expect(oturumAcikSaniliyor()).toBe(false);

    await oturumuKilitle();

    expect(yuklemeSayisi()).toBe(1);
    // Yeni pencerede kapı durumu sunucudan okur; bayrak inmiş başlar.
    expect(oturumAcikSaniliyor()).toBe(false);
  });

  it("Kilitle 423 alırsa (oturum bu arada kilitlendi) hata vermeden yine yükler", async () => {
    fetchHep(423, KILITLI_423);
    await expect(oturumuKilitle()).resolves.toBeNull();
    expect(yuklemeSayisi()).toBe(1);
  });

  it("uzun iş sürerken ertelenen Kilitle yüklemez", async () => {
    fetchHep(200, { sonuc: "ertelendi", ...ACIK, bosta_kalan_sn: null, kilit_bekliyor: true });
    const sonuc = await oturumuKilitle();
    expect(sonuc?.sonuc).toBe("ertelendi");
    expect(yuklemeSayisi()).toBe(0);
  });

  it("oturum yoklaması açık sanılan oturumu kilitli görünce yükler (boşta kilit)", async () => {
    const sahte = fetchHep(200, ACIK);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const sarmal = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);
    const { result } = renderHook(() => useOturum(), { wrapper: sarmal });

    await waitFor(() => expect(result.current.ozet?.durum).toBe("acik"));
    expect(oturumAcikSaniliyor()).toBe(true);
    expect(yuklemeSayisi()).toBe(0);
    // Yoklama başlıksız gider (oturumu canlı tutmaz).
    const [, init] = sahte.mock.calls[0] as [string, RequestInit];
    expect(init.headers).not.toHaveProperty("X-OD-Etkinlik");

    sahte.mockResolvedValue(yanit(200, KILITLI));
    result.current.yenile();

    await waitFor(() => expect(yuklemeSayisi()).toBe(1));
  });

  it("ön yüz oturumu açık sanırken gelen 423 yükler, olay yayınlamaz", async () => {
    oturumAcikSan(true);
    fetchHep(423, KILITLI_423);
    const dinleyici = vi.fn();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    try {
      await expect(api.get("/students/")).rejects.toMatchObject({ status: 423 });
    } finally {
      window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    }
    expect(yuklemeSayisi()).toBe(1);
    expect(dinleyici).not.toHaveBeenCalled();
  });

  it("güvenlik dosyası açık oturumda kaybolursa (423 guvenlik_dosyasi_kayip) da yükler", async () => {
    oturumAcikSan(true);
    fetchHep(423, { code: "guvenlik_dosyasi_kayip", message: "Güvenlik dosyası…", fields: {} });
    await api.getBlob("/templates/students/").catch(() => undefined);
    expect(yuklemeSayisi()).toBe(1);
  });
});

describe("kilit ekranından açılış pencereyi yeniden yükler", () => {
  it("kilit açma başarıda yükler", async () => {
    const sahte = fetchHep(200, ACIK);
    await kilidiAc({ hesap: "h-1", parola: "Deneme-Parola-1" });
    expect(yuklemeSayisi()).toBe(1);
    const [url, init] = sahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/security/unlock/");
    expect(JSON.parse(String(init.body))).toEqual({ hesap: "h-1", parola: "Deneme-Parola-1" });
  });

  it("zorunlu parola yenilemesiyle açılış da yükler", async () => {
    fetchHep(200, ACIK);
    await kilidiAc({ hesap: "h-1", parola: "Gecici-Parola-1", yeni_parola: "Yeni-Parola-22" });
    expect(yuklemeSayisi()).toBe(1);
  });

  it("kurtarma anahtarıyla açılış başarıda yükler", async () => {
    const sahte = fetchHep(200, ACIK);
    await kurtarmaAnahtariylaAc({
      kurtarma_anahtari: "AAAA-BBBB",
      hesap: "h-1",
      yeni_parola: "Yeni-Parola-22",
    });
    expect(yuklemeSayisi()).toBe(1);
    expect(String(sahte.mock.calls[0][0])).toBe("/api/v1/security/recover/");
  });

  it.each([
    [400, { code: "parola_yanlis", message: "Parola hatalı.", fields: {} }],
    [409, { code: "parola_yenilenmeli", message: "Parolanızı yenilemeniz gerekiyor.", fields: {} }],
    [403, { code: "hesap_askida", message: "Hesap askıda.", fields: {} }],
  ])("başarısız açılış (%i) yüklemez", async (status, govde) => {
    fetchHep(status, govde);
    await expect(kilidiAc({ hesap: "h-1", parola: "yanlis" })).rejects.toBeTruthy();
    expect(yuklemeSayisi()).toBe(0);
  });
});

describe("yüklemeyen anlar ve döngü koruması", () => {
  it("ön yüz zaten kilitli bilirken gelen 423 yüklemez, yalnız olay yayınlar", async () => {
    // Kilit ekranı gösteriliyor: bayrak inik (GuvenlikKapisi yazar).
    oturumAcikSan(false);
    fetchHep(423, KILITLI_423);
    const dinleyici = vi.fn();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    try {
      await api.get("/students/").catch(() => undefined);
      await api.get("/students/").catch(() => undefined);
    } finally {
      window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    }
    expect(yuklemeSayisi()).toBe(0);
    expect(dinleyici).toHaveBeenCalledTimes(2);
  });

  it("yükleme istendikten sonra uçuştaki öteki 423'ler ne ikinci yükleme ne olay doğurur", async () => {
    oturumAcikSan(true);
    fetchHep(423, KILITLI_423);
    // Olay da yayınlanmaz: yayınlansaydı güvenlik kapısı durumu yeniden okur ve sayfa
    // boşalmadan kilit ekranını çizebilirdi (`kilitKapisiYaniti`, "|| yukleniyor").
    const dinleyici = vi.fn();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    try {
      await Promise.all([
        api.get("/students/").catch(() => undefined),
        api.get("/personnel/").catch(() => undefined),
        api.get("/class-sections/").catch(() => undefined),
      ]);
    } finally {
      window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    }
    expect(dinleyici).not.toHaveBeenCalled();
    expect(yuklemeSayisi()).toBe(1);
    expect(yenidenYuklemeIstendi()).toBe(true);
    // Elle Kilitle de ikinci kez yüklemez.
    expect(kilitlendi("elle")).toBe(false);
    expect(yuklemeSayisi()).toBe(1);
  });

  it("yoklama kilitli görse de ön yüz zaten kilitli biliyorsa yüklemez", async () => {
    fetchHep(200, KILITLI);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const sarmal = ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);
    const { result } = renderHook(() => useOturum(), { wrapper: sarmal });
    await waitFor(() => expect(result.current.ozet?.durum).toBe("kilitli"));
    expect(yuklemeSayisi()).toBe(0);
  });

  it("kurulumdaki ilk hesap yüklemez, Türkçe gövde gönderir ve ön yüz oturumu artık açık sanar", async () => {
    const sahte = fetchHep(201, {
      recovery_key: "AAAA-BBBB",
      login_name_warning: null,
      password_set: true,
    });
    const sonuc = await ilkHesabiKur({
      tanitici: "yonetici",
      ad_soyad: "Deneme Yönetici",
      parola: "Deneme-Parola-1",
    });
    expect(sonuc.recovery_key).toBe("AAAA-BBBB");
    expect(yuklemeSayisi()).toBe(0);
    // Uç ve gövde backend sözleşmesidir (`SecurityEnableView`): eski `{password}` değil.
    const [url, init] = sahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/security/enable/");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({
      tanitici: "yonetici",
      ad_soyad: "Deneme Yönetici",
      parola: "Deneme-Parola-1",
    });
    expect(oturumAcikSaniliyor()).toBe(true);
  });

  it("parola değişimi yüklemez ve Türkçe gövde gönderir", async () => {
    oturumAcikSan(true);
    const sahte = fetchHep(200, ACIK);
    await parolayiDegistir("Eski-Parola-1", "Yeni-Parola-22");
    expect(yuklemeSayisi()).toBe(0);
    const [url, init] = sahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/security/change-password/");
    expect(JSON.parse(String(init.body))).toEqual({
      parola: "Eski-Parola-1",
      yeni_parola: "Yeni-Parola-22",
    });
    expect(oturumAcikSaniliyor()).toBe(true);
  });

  it("başka kodlu 423 ve 423 dışındaki kilit kodu ne yükler ne olay yayınlar", async () => {
    oturumAcikSan(true);
    const dinleyici = vi.fn();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    try {
      fetchHep(423, { code: "baska" });
      await api.get("/students/").catch(() => undefined);
      fetchHep(400, { code: "locked", message: "x" });
      await api.get("/students/").catch(() => undefined);
    } finally {
      window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    }
    expect(yuklemeSayisi()).toBe(0);
    expect(dinleyici).not.toHaveBeenCalled();
  });
});
