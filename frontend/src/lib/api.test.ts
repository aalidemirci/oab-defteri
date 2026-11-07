// lib/api "yeniden başlat" sözleşmesi: backend restart_gate kapısındayken HANGİ
// uç çağrılırsa çağrılsın 503 `restart_required` döner; istemci ApiError fırlatır
// VE yeniden başlat olayını yayınlar (YenidenBaslatEkrani bunu dinler). Sıradan
// hatalar olayı yayınlamaz.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  ETKINLIK_BASLIGI,
  ETKINLIK_PENCERESI_MS,
  ROL_YETKISIZ_KODU,
  ROL_YETKISIZ_OLAYI,
  BEKLENMEYEN_HATA_ILETISI,
  api,
  etkilesimKaydet,
  etkinlikSaatleriniSifirla,
  sonEtkilesimAni,
  sonEtkinlikGonderimiAni,
} from "./api";
import { KILIT_KAPISI_OLAYI, oturumAcikSan, pencereIcerigi } from "./kilit";
import { YENIDEN_BASLAT_OLAYI } from "./restart";

function sahteYanit(status: number, govde: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(govde),
    blob: () => Promise.resolve(new Blob()),
  };
}

describe("api — restart_required sözleşmesi", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("503 restart_required hem ApiError fırlatır hem olayı yayınlar", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sahteYanit(503, {
          code: "restart_required",
          message: "Yedekten geri yükleme uygulandı.",
          fields: {},
        }),
      ),
    );
    const dinleyici = vi.fn();
    window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    try {
      await expect(api.get("/security/status/")).rejects.toMatchObject({
        code: "restart_required",
        status: 503,
      });
      expect(dinleyici).toHaveBeenCalledTimes(1);
    } finally {
      window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    }
  });

  it("hata gövdesinin sözleşme dışı alanı ApiError.govde'de kalır (409 ek_onayi_gerekli)", async () => {
    const rapor = { kapsam: "tam", bozuk: 1 };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sahteYanit(409, {
          code: "ek_onayi_gerekli",
          message: "1 ek yedek alınırkenki hâlini tutmuyor; geri yükleme yapılmadı.",
          fields: {},
          rapor,
        }),
      ),
    );

    const hata = await api.postForm("/backups/restore/", new FormData()).catch((e: unknown) => e);

    expect(hata).toBeInstanceOf(ApiError);
    expect((hata as ApiError).govde.rapor).toEqual(rapor);
  });

  it("gövdesiz dosya yanıtının iletisi JSON yolundakiyle aynıdır (ekranlar kendi metnine düşer)", async () => {
    const bozuk = {
      ok: false,
      status: 500,
      json: () => Promise.reject(new SyntaxError("Unexpected token <")),
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(bozuk));

    const hata = await api.postDosya("/backups/report/").catch((e: unknown) => e);

    expect(hata).toBeInstanceOf(ApiError);
    expect((hata as ApiError).message).toBe(BEKLENMEYEN_HATA_ILETISI);
    expect((hata as ApiError).code).toBe("500");
  });

  it("sıradan hata olayı yayınlamaz", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          sahteYanit(400, { code: "validation_error", message: "Hata.", fields: {} }),
        ),
    );
    const dinleyici = vi.fn();
    window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    try {
      await expect(api.get("/students/")).rejects.toBeInstanceOf(ApiError);
      expect(dinleyici).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    }
  });
});

// Oturum sözleşmesi (tasarım §4.4.3): kullanıcı etkileşiminden hemen sonra giden istek
// `X-OD-Etkinlik: 1` taşır; zamanlayıcıyla giden istek (çağıran `etkinlik: false` verir)
// ve etkileşimsiz istek taşımaz. Aile iskeletinin 403 `kip_yetkisiz` dalı görevli kipiyle
// kalktı: hiçbir 403 kilit ya da kip tepkisi doğurmaz (403 `rol_yetkisiz`in olayı aşağıda).

function gonderilenBasliklar(fetchSahte: ReturnType<typeof vi.fn>): Record<string, string> {
  const [, init] = fetchSahte.mock.calls[0] as [string, RequestInit];
  return init.headers as Record<string, string>;
}

describe("api — etkinlik başlığı", () => {
  let fetchSahte: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    etkinlikSaatleriniSifirla();
    fetchSahte = vi.fn().mockResolvedValue(sahteYanit(200, {}));
    vi.stubGlobal("fetch", fetchSahte);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("etkileşim yoksa başlık gönderilmez", async () => {
    await api.get("/students/");
    expect(gonderilenBasliklar(fetchSahte)).not.toHaveProperty(ETKINLIK_BASLIGI);
    expect(sonEtkinlikGonderimiAni()).toBe(Number.NEGATIVE_INFINITY);
  });

  it.each(["pointerdown", "keydown"])(
    "%s sonrasındaki istek başlığı taşır ve gönderim anını kaydeder",
    async (olay) => {
      window.dispatchEvent(new Event(olay));
      expect(sonEtkilesimAni()).toBeGreaterThan(0);
      await api.post("/students/", { ad: "x" });
      expect(gonderilenBasliklar(fetchSahte)[ETKINLIK_BASLIGI]).toBe("1");
      expect(sonEtkinlikGonderimiAni()).toBeGreaterThan(0);
    },
  );

  it("yerel pencereden dönen seçim etkileşim sayılır: sonraki istek başlığı taşır", async () => {
    etkilesimKaydet();

    await api.post("/backups/encrypted/", { hedef: "E:\\yedek.odbak" });

    expect(gonderilenBasliklar(fetchSahte)[ETKINLIK_BASLIGI]).toBe("1");
  });

  it("pencere dolduktan sonraki istek başlık taşımaz", async () => {
    const simdi = Date.now();
    const saat = vi.spyOn(Date, "now").mockReturnValue(simdi);
    window.dispatchEvent(new Event("pointerdown"));
    saat.mockReturnValue(simdi + ETKINLIK_PENCERESI_MS + 1);
    await api.get("/students/");
    expect(gonderilenBasliklar(fetchSahte)).not.toHaveProperty(ETKINLIK_BASLIGI);
  });

  it("etkinlik:false verilen istek etkileşimden hemen sonra da başlık taşımaz", async () => {
    window.dispatchEvent(new Event("keydown"));
    await api.get("/security/session/", { etkinlik: false });
    expect(gonderilenBasliklar(fetchSahte)).not.toHaveProperty(ETKINLIK_BASLIGI);
    expect(sonEtkinlikGonderimiAni()).toBe(Number.NEGATIVE_INFINITY);
  });

  it("dosya indirmeleri de aynı kuralla başlık taşır", async () => {
    window.dispatchEvent(new Event("pointerdown"));
    await api.getBlob("/templates/students/");
    expect(gonderilenBasliklar(fetchSahte)[ETKINLIK_BASLIGI]).toBe("1");
  });

  it("dosya indirmesinde etkinlik:false başlığı keser", async () => {
    window.dispatchEvent(new Event("pointerdown"));
    await api.postBlob("/backups/report/", undefined, { etkinlik: false });
    expect(gonderilenBasliklar(fetchSahte)).not.toHaveProperty(ETKINLIK_BASLIGI);
  });
});

describe("api — 403 kilit ya da kip tepkisi doğurmaz", () => {
  afterEach(() => vi.unstubAllGlobals());

  it.each([{ code: "kip_yetkisiz", message: "Eski kip kodu.", fields: {} }, { detail: "Yasak" }])(
    "403 (%o) olay yayınlamaz, pencereyi yüklemez",
    async (govde) => {
      oturumAcikSan(true);
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sahteYanit(403, govde)));
      const dinleyici = vi.fn();
      window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
      try {
        await expect(api.get("/students/")).rejects.toMatchObject({ status: 403 });
      } finally {
        window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
      }
      expect(dinleyici).not.toHaveBeenCalled();
      expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    },
  );
});

// Kilit kapısı (tasarım §4.4.3, §13 D53): 423 `locked` ya da `guvenlik_dosyasi_kayip`
// `lib/kilit.ts`'e verilir. Ön yüz kilitli olduğunu bilirken (bayrak inik) güvenlik kapısı
// durumu yeniden okusun diye olay yayınlanır; açık sanırken pencere yeniden yüklenir
// (ayrıntı `kilit.test.ts`). Başka kodlu 423 ikisini de yapmaz.
describe("api — kilit kapısı sözleşmesi", () => {
  afterEach(() => vi.unstubAllGlobals());

  async function olaySayisi(istek: () => Promise<unknown>): Promise<number> {
    const dinleyici = vi.fn();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    try {
      await istek().catch(() => undefined);
    } finally {
      window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    }
    return dinleyici.mock.calls.length;
  }

  it.each(["locked", "guvenlik_dosyasi_kayip"])(
    "kilitliyken 423 %s hem ApiError fırlatır hem kilit olayını yayınlar",
    async (code) => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(sahteYanit(423, { code, message: "Kilitli.", fields: {} })),
      );
      await expect(api.get("/students/")).rejects.toMatchObject({ status: 423, code });
      expect(await olaySayisi(() => api.get("/students/"))).toBe(1);
      expect(await olaySayisi(() => api.getBlob("/templates/students/"))).toBe(1);
      expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    },
  );

  it("açık sanılan oturumda 423 olay yerine pencereyi yeniden yükler", async () => {
    oturumAcikSan(true);
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(sahteYanit(423, { code: "locked", message: "Kilitli.", fields: {} })),
    );
    expect(await olaySayisi(() => api.get("/students/"))).toBe(0);
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("başka kodlu 423 ve 423 dışı kilit kodu olayı yayınlamaz", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sahteYanit(423, { code: "baska" })));
    expect(await olaySayisi(() => api.get("/students/"))).toBe(0);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sahteYanit(400, { code: "locked" })));
    expect(await olaySayisi(() => api.get("/students/"))).toBe(0);
  });
});

// Rol reddi (plan F1b-2 "Ön yüz"): `od:rol-yetkisiz` YALNIZ 403 `rol_yetkisiz`'de yayınlanır;
// kilit açmanın 403 `hesap_askida`'sı, belirteç kapısının 403'ü (`forbidden`) ve başka durumdaki
// aynı kod yayınlamaz. Hata her durumda çağırana ApiError olarak (sunucunun iletisiyle) döner.
describe("api — rol reddi olayı", () => {
  afterEach(() => vi.unstubAllGlobals());

  async function olaySayisi(istek: () => Promise<unknown>, status: number, code: string) {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(sahteYanit(status, { code, message: "İleti.", fields: {} })),
    );
    const dinleyici = vi.fn();
    window.addEventListener(ROL_YETKISIZ_OLAYI, dinleyici);
    try {
      await expect(istek()).rejects.toMatchObject({ status, code, message: "İleti." });
    } finally {
      window.removeEventListener(ROL_YETKISIZ_OLAYI, dinleyici);
    }
    return dinleyici.mock.calls.length;
  }

  it("403 rol_yetkisiz olayı bir kez yayınlar; ileti çağırana gider", async () => {
    expect(await olaySayisi(() => api.post("/accounts/", {}), 403, ROL_YETKISIZ_KODU)).toBe(1);
  });

  it("dosya indirmede de (getBlob/postBlob) 403 rol_yetkisiz olayı yayınlar", async () => {
    expect(
      await olaySayisi(() => api.postBlob("/backups/download/", {}), 403, "rol_yetkisiz"),
    ).toBe(1);
    expect(await olaySayisi(() => api.getBlob("/templates/personnel/"), 403, "rol_yetkisiz")).toBe(
      1,
    );
  });

  it.each([
    [403, "hesap_askida"],
    [403, "forbidden"],
    [403, "403"],
    [400, "rol_yetkisiz"],
    [409, "rol_yetkisiz"],
  ])("%i %s olayı yayınlamaz", async (status, code) => {
    expect(await olaySayisi(() => api.get("/security/session/"), status, code)).toBe(0);
  });
});

// `postDosya` (hesap teslim pusulası): dosya + sunucunun `Content-Disposition`'daki adı. Ad yoksa
// null (çağıran yedek adı kurar); hata yolu öteki dosya indirmeleriyle aynıdır.
describe("api — postDosya", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("dosyayı ve sunucunun Türkçe harfli adını verir; gövdesiz POST'tur", async () => {
    const ad = "Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf";
    const pdf = new Blob(["%PDF"]);
    const fetchSahte = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        "Content-Disposition": `attachment; filename*=utf-8''${encodeURIComponent(ad)}`,
      }),
      blob: () => Promise.resolve(pdf),
    });
    vi.stubGlobal("fetch", fetchSahte);

    const sonuc = await api.postDosya("/accounts/h-1/handover-slip/");

    expect(sonuc).toEqual({ blob: pdf, ad });
    const [url, istek] = fetchSahte.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/accounts/h-1/handover-slip/");
    expect(istek.method).toBe("POST");
    expect(istek.body).toBeUndefined();
  });

  it("başlık yoksa ad null'dır", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers(),
        blob: () => Promise.resolve(new Blob()),
      }),
    );
    expect((await api.postDosya("/x/")).ad).toBeNull();
  });

  it("ret JSON gövdesinden ApiError olur ve rol reddi olayı yayınlanır", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          sahteYanit(403, { code: ROL_YETKISIZ_KODU, message: "İleti.", fields: {} }),
        ),
    );
    const dinleyici = vi.fn();
    window.addEventListener(ROL_YETKISIZ_OLAYI, dinleyici);
    try {
      await expect(api.postDosya("/accounts/h-1/handover-slip/")).rejects.toMatchObject({
        status: 403,
      });
    } finally {
      window.removeEventListener(ROL_YETKISIZ_OLAYI, dinleyici);
    }
    expect(dinleyici).toHaveBeenCalledTimes(1);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sahteYanit(400, {
          code: "validation_error",
          message: "Kendi hesabınızın teslim pusulasını basamazsınız.",
          fields: {},
        }),
      ),
    );
    await expect(api.postDosya("/accounts/h-1/handover-slip/")).rejects.toMatchObject({
      status: 400,
      code: "validation_error",
      message: "Kendi hesabınızın teslim pusulasını basamazsınız.",
    });
  });
});
