// `butunlukApi` sözleşmesi: yollar backend `urls.py`'deki "security/integrity/*" ile birebir;
// okumalar kullanıcı eylemi değildir (`X-OD-Etkinlik` gitmez, tasarım §4.4.3); yazmalar POST.
// Kartlar role göre üç uçtan okunur (tasarım §4.4.2 "kısmi yetki ayrı uçla"; plan F1b-2): rolün
// açamadığı uç ÇAĞRILMAZ; üç yanıt tek bileşik durumda birleşir ve bugünkü kartları besler.

import { afterEach, describe, expect, it, vi } from "vitest";

import { ETKINLIK_BASLIGI, etkinlikSaatleriniSifirla } from "../../lib/api";
import {
  birlestir,
  butunlukApi,
  butunlukYetkisi,
  denetimiBirlestir,
  ikiDepoFarki,
  ikiDepoyuBirlestir,
} from "./api";
import type { ButunlukDurumu, EksikEk, GeriYuklemeOzeti, IkiDepoHesabi } from "./api";

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
/** `dosya_deposu.eksik_ekler`'in satırı; ad uydurmadır. */
const EKSIK_EK: EksikEk = {
  kayit_turu: "ders yılı",
  kayit_no: "7",
  yukleme_tarihi: "2026-10-01",
  boyut: 4096,
  ozgun_ad: "toplanti-tutanagi.pdf",
};
const DENETIM = {
  butunluk: [],
  geri_yukleme: null,
  muhru_tutmayan: [DK_1],
  eksik_ekler: [EKSIK_EK],
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
      eksik_ekler: [],
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
      ozeti_tutmayan_hesaplar: [],
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
        ozeti_tutmayan_hesaplar: [],
        muhru_tutmayan: [DK_1],
      },
      eksik_ekler: [EKSIK_EK],
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
      "eksik_ekler",
    ]);
  });

  it("eksik ekler denetim ucundan gelir; uç okunamadıysa “eksik yok” sayılmaz", () => {
    expect(birlestir(KENDI, DENETIM, null)?.eksik_ekler).toEqual([EKSIK_EK]);
    expect(birlestir(KENDI, null, null)?.eksik_ekler).toEqual([]);
    expect(birlestir(KENDI, null, null)?.okunamayan).toEqual([]);
    expect(
      birlestir(KENDI, { ...DENETIM, eksik_ekler: [], okunamayan: ["eksik_ekler"] }, null)
        ?.okunamayan,
    ).toEqual(["eksik_ekler"]);
  });

  it("kendi kartları okunamazsa durum okunamamıştır (uyarı kartı); eksik alan boştur", () => {
    expect(birlestir(null, DENETIM, IKI_DEPO)).toBeNull();
    expect(birlestir({}, {}, {})).toEqual({
      butunluk: [],
      geri_yukleme: null,
      iki_depo: null,
      eksik_ekler: [],
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
      ozeti_tutmayan_hesaplar: [],
      muhru_tutmayan: [],
    });
  });

  it("parola kaydı özeti tutmayan hesaplar iki depo kaydından geçer, eksikse boş sayılır", () => {
    const yanit = {
      fark_var: true,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      ozeti_tutmayan_hesaplar: [MUHASIP],
    };
    expect(ikiDepoFarki(yanit, [])?.ozeti_tutmayan_hesaplar).toEqual([MUHASIP]);
    expect(
      ikiDepoFarki({ fark_var: true, sarmalsiz_hesaplar: [MUHASIP], silinebilir_sarmallar: [] }, [])
        ?.ozeti_tutmayan_hesaplar,
    ).toEqual([]);
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
      ozeti_tutmayan_hesaplar: [],
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

describe("butunlukApi — geri yükleme kartının “Gördüm”ü", () => {
  it("kartın sırasını POST eder (kullanıcı eylemi; etkinlik başlığı gider)", async () => {
    const fetchSahte = vi.fn().mockResolvedValue(yanit(DENETIM));
    vi.stubGlobal("fetch", fetchSahte);
    window.dispatchEvent(new Event("pointerdown"));

    await expect(butunlukApi.geriYuklemeyiGordum(40)).resolves.toEqual(DENETIM);

    const [yol, istek] = cagri(fetchSahte, 0);
    expect(yol).toMatch(/\/security\/integrity\/restore-seen\/$/);
    expect(istek.method).toBe("POST");
    expect(JSON.parse(String(istek.body))).toEqual({ seq: 40 });
    expect((istek.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBe("1");
  });
});

describe("denetimiBirlestir", () => {
  const GERI = { seq: 40, onceki_geri_yuklemeler: [] } as unknown as GeriYuklemeOzeti;
  const IKI_DEPO_OZETLI = {
    iki_depo: {
      fark_var: true,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      ozeti_tutmayan_hesaplar: [MUHASIP],
    },
    okunamayan: [],
  };

  it("“Gördüm”den dönen kartlar yazılır; iki depo kaydı (program yöneticisi) korunur", () => {
    const once = birlestir(KENDI, { ...DENETIM, geri_yukleme: GERI }, IKI_DEPO_OZETLI);
    expect(once?.geri_yukleme).toEqual(GERI);

    const sonra = denetimiBirlestir(once as ButunlukDurumu, {
      butunluk: [],
      geri_yukleme: null,
      muhru_tutmayan: [],
      eksik_ekler: [],
      okunamayan: [],
    });

    expect(sonra.geri_yukleme).toBeNull();
    expect(sonra.eksik_ekler).toEqual([]);
    expect(sonra.iki_depo).toEqual({
      fark_var: true,
      sarmalsiz_hesaplar: [],
      silinebilir_sarmallar: [],
      ozeti_tutmayan_hesaplar: [MUHASIP],
      muhru_tutmayan: [],
    });
    expect(sonra.son_girisler).toEqual(KENDI.son_girisler);
    expect(sonra.kagit_capasi).toEqual(KENDI.kagit_capasi);
  });

  it("iki depo ucu çağrılmayan rolde (Denetleme Kurulu) mührü tutmayanlar yenilenir", () => {
    const once = birlestir(KENDI, { ...DENETIM, geri_yukleme: GERI }, null) as ButunlukDurumu;
    expect(once.iki_depo?.muhru_tutmayan).toEqual([DK_1]);

    const bos = denetimiBirlestir(once, { ...DENETIM, muhru_tutmayan: [] });
    expect(bos.iki_depo?.fark_var).toBe(false);

    const ayni = denetimiBirlestir(
      { ...once, iki_depo: null },
      { ...DENETIM, muhru_tutmayan: [MUHASIP] },
    );
    expect(ayni.iki_depo?.muhru_tutmayan).toEqual([MUHASIP]);
    expect(ayni.iki_depo?.fark_var).toBe(true);
  });

  it("okunamayan adlar yenilenir; yanıt nesne değilse denetim kartları okunamamış sayılır", () => {
    const once = {
      ...(birlestir(KENDI, DENETIM, IKI_DEPO) as ButunlukDurumu),
      okunamayan: ["geri_yukleme", "iki_depo"],
    };
    expect(denetimiBirlestir(once, { ...DENETIM, okunamayan: ["butunluk"] }).okunamayan).toEqual([
      "iki_depo",
      "butunluk",
    ]);
    const bozuk = denetimiBirlestir(once, "beklenmeyen");
    expect(bozuk.okunamayan).toEqual([
      "iki_depo",
      "butunluk",
      "geri_yukleme",
      "muhru_tutmayan",
      "eksik_ekler",
    ]);
    expect(bozuk.butunluk).toEqual([]);
    expect(bozuk.eksik_ekler).toEqual([]);
    expect(bozuk.geri_yukleme).toBeNull();
  });
});
