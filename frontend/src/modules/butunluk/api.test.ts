// `butunlukApi` sözleşmesi: yollar backend `urls.py`'deki "security/integrity/*" ile birebir;
// okumalar kullanıcı eylemi değildir (`X-OD-Etkinlik` gitmez, tasarım §4.4.3); yazmalar POST.
// Kartlar role göre üç uçtan okunur (tasarım §4.4.2 "kısmi yetki ayrı uçla"; plan F1b-2): rolün
// açamadığı uç ÇAĞRILMAZ; üç yanıt tek bileşik durumda birleşir ve bugünkü kartları besler.

import { afterEach, describe, expect, it, vi } from "vitest";

import { ETKINLIK_BASLIGI, etkinlikSaatleriniSifirla } from "../../lib/api";
import { birlestir, butunlukApi, butunlukYetkisi, ikiDepoFarki, ikiDepoyuBirlestir } from "./api";
import type { ButunlukDurumu, IkiDepoHesabi } from "./api";

function yanit(govde: unknown): Response {
  return new Response(JSON.stringify(govde), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function cagri(fetchSahte: ReturnType<typeof vi.fn>, sira: number): [string, RequestInit] {
  return fetchSahte.mock.calls[sira] as [string, RequestInit];
}

function yollar(fetchSahte: ReturnType<typeof vi.fn>): string[] {
  return fetchSahte.mock.calls.map((c) => String(c[0])).sort();
}

const KENDI = {
  kagit_capasi: { kayit_no: 57, zincir: "A1B2-C3D4" },
  son_girisler: ["2026-11-01T08:00:00+03:00"],
  parola_yenilenme: null,
  okunamayan: [],
};
const DK_1: IkiDepoHesabi = {
  id: "h-4",
  tanitici: "dk-1",
  rol_etiketi: "Denetleme Kurulu",
  kapali: false,
};
const MUHASIP: IkiDepoHesabi = {
  id: "h-2",
  tanitici: "muhasip",
  rol_etiketi: "Muhasip",
  kapali: false,
};
const DENETIM = {
  butunluk: [],
  geri_yukleme: null,
  muhru_tutmayan: [DK_1],
  okunamayan: [],
};
const IKI_DEPO = {
  iki_depo: { fark_var: true, sarmalsiz_hesaplar: [MUHASIP], silinebilir_sarmallar: [] },
  okunamayan: [],
};

/** Yola göre yanıt veren sahte `fetch`. */
function sahteSunucu(): ReturnType<typeof vi.fn> {
  return vi.fn().mockImplementation((yol: string) => {
    if (yol.endsWith("/security/integrity/audit/")) return Promise.resolve(yanit(DENETIM));
    if (yol.endsWith("/security/integrity/two-store/")) return Promise.resolve(yanit(IKI_DEPO));
    return Promise.resolve(yanit(KENDI));
  });
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

    await butunlukApi.kendiKartlari();
    await butunlukApi.denetimKartlari();
    await butunlukApi.ikiDepo();
    await butunlukApi.parolaBildirimi();

    const beklenen = [
      "/api/v1/security/integrity/",
      "/api/v1/security/integrity/audit/",
      "/api/v1/security/integrity/two-store/",
      "/api/v1/security/integrity/reset-notice/",
    ];
    beklenen.forEach((yol, sira) => {
      const [gercek, secenek] = cagri(fetchSahte, sira);
      expect(gercek).toBe(yol);
      expect(secenek.method).toBe("GET");
      expect((secenek.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBeUndefined();
    });
  });

  it("yetkisi olmayan rol yalnız kendi kartlarını çağırır (denetim ve iki depo ucu hiç gitmez)", async () => {
    const fetchSahte = sahteSunucu();
    vi.stubGlobal("fetch", fetchSahte);

    const durum = await butunlukApi.durum(butunlukYetkisi(["son_oturum_onay"]));

    expect(yollar(fetchSahte)).toEqual(["/api/v1/security/integrity/"]);
    expect(durum).toEqual({
      butunluk: [],
      geri_yukleme: null,
      iki_depo: null,
      kagit_capasi: KENDI.kagit_capasi,
      son_girisler: KENDI.son_girisler,
      parola_yenilenme: null,
      okunamayan: [],
    } satisfies ButunlukDurumu);
  });

  it("Denetleme Kurulu denetim kartlarını da çağırır, iki depo ucunu çağırmaz", async () => {
    const fetchSahte = sahteSunucu();
    vi.stubGlobal("fetch", fetchSahte);

    const durum = await butunlukApi.durum(butunlukYetkisi(["butunluk_denetim"]));

    expect(yollar(fetchSahte)).toEqual([
      "/api/v1/security/integrity/",
      "/api/v1/security/integrity/audit/",
    ]);
    // Mührü tutmayan hesap "Hesaplar ve Güvenlik Dosyası" kartında görünür; silinecek kayıt yok.
    expect(durum?.iki_depo).toEqual({
      fark_var: true,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      muhru_tutmayan: [DK_1],
    });
  });

  it("program yöneticisi üç ucu çağırır; durum bugünkü tek yanıtın biçimidir", async () => {
    const fetchSahte = sahteSunucu();
    vi.stubGlobal("fetch", fetchSahte);

    const durum = await butunlukApi.durum(butunlukYetkisi(["butunluk_denetim", "iki_depo"]));

    expect(yollar(fetchSahte)).toEqual([
      "/api/v1/security/integrity/",
      "/api/v1/security/integrity/audit/",
      "/api/v1/security/integrity/two-store/",
    ]);
    expect(durum).toEqual({
      butunluk: [],
      geri_yukleme: null,
      iki_depo: {
        fark_var: true,
        sarmalsiz_hesaplar: [MUHASIP],
        silinebilir_sarmallar: [],
        muhru_tutmayan: [DK_1],
      },
      kagit_capasi: KENDI.kagit_capasi,
      son_girisler: KENDI.son_girisler,
      parola_yenilenme: null,
      okunamayan: [],
    } satisfies ButunlukDurumu);
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

describe("bütünlük yanıtlarının birleşmesi", () => {
  it("yetki oturum özetinin yeteneklerinden okunur; ön yüz matrisi kopyalamaz", () => {
    expect(butunlukYetkisi([])).toEqual({ denetim: false, ikiDepo: false });
    expect(butunlukYetkisi(["butunluk_denetim"])).toEqual({ denetim: true, ikiDepo: false });
    expect(butunlukYetkisi(["iki_depo", "butunluk_denetim"])).toEqual({
      denetim: true,
      ikiDepo: true,
    });
  });

  it("her ucun okunamayan kartları birleşir; okunamayan çağrılmış uç uyarıya düşer", () => {
    const d = birlestir(
      { ...KENDI, okunamayan: ["kagit_capasi"] },
      { ...DENETIM, okunamayan: ["geri_yukleme"] },
      "beklenmeyen",
    );
    expect(d?.okunamayan).toEqual(["kagit_capasi", "geri_yukleme", "iki_depo"]);
    expect(birlestir(KENDI, 42, null)?.okunamayan).toEqual([
      "butunluk",
      "geri_yukleme",
      "muhru_tutmayan",
    ]);
  });

  it("kendi kartları okunamazsa durum okunamamıştır (uyarı kartı); eksik alan boştur", () => {
    expect(birlestir(null, DENETIM, IKI_DEPO)).toBeNull();
    expect(birlestir({}, {}, {})).toEqual({
      butunluk: [],
      geri_yukleme: null,
      iki_depo: null,
      kagit_capasi: null,
      son_girisler: [],
      parola_yenilenme: null,
      okunamayan: [],
    } satisfies ButunlukDurumu);
  });

  it("iki depo kaydı yoksa ve mührü tutmayan hesap da yoksa kart durumu null'dır", () => {
    expect(ikiDepoFarki(null, [])).toBeNull();
    expect(
      ikiDepoFarki({ fark_var: false, sarmalsiz_hesaplar: [], silinebilir_sarmallar: [] }, []),
    ).toEqual({
      fark_var: false,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      muhru_tutmayan: [],
    });
  });

  it("silmeden dönen iki depo kartı mührü tutmayan hesapları korur", () => {
    const once = birlestir(KENDI, DENETIM, IKI_DEPO);
    expect(once).not.toBeNull();

    const sonra = ikiDepoyuBirlestir(once as ButunlukDurumu, {
      silinen: ["x"],
      iki_depo: { fark_var: false, sarmalsiz_hesaplar: [], silinebilir_sarmallar: [] },
      okunamayan: [],
    });

    expect(sonra.iki_depo).toEqual({
      fark_var: true,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      muhru_tutmayan: [DK_1],
    });
    expect(sonra.son_girisler).toEqual(KENDI.son_girisler);
    // Okunamayan iki depo kartı yanıtta bildirilir; önceki ad yenilenir.
    expect(
      ikiDepoyuBirlestir({ ...(once as ButunlukDurumu), okunamayan: ["iki_depo"] }, IKI_DEPO)
        .okunamayan,
    ).toEqual([]);
  });
});
