// Oturum sorgusu ve görsel geri sayım (tasarım §4.4.3, TK14). Pinlenen davranışlar:
// yoklama `X-OD-Etkinlik` TAŞIMAZ (etkinlik:false); açık özet ön yüzü "açık sanır"a
// geçirir, açık sanılırken kilitli özet pencereyi yeniden yükler (D53; ayrıntı
// `lib/kilit.test.ts`); 423 olayı sorguyu yeniler; geri sayım yalnız boşta süredir
// (mutlak süre yok) ve özetten sonra giden başlıklı istek sayacı tazeler; etkinlik nabzı
// yalnız açık oturumda, gerçek etkileşimle ve seyrek gider; sorgu hatası fail-open'dır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, etkinlikSaatleriniSifirla } from "../../lib/api";
import {
  KILIT_KAPISI_OLAYI,
  oturumAcikSan,
  oturumAcikSaniliyor,
  pencereIcerigi,
} from "../../lib/kilit";
import type { OturumDurumAdi, OturumOzeti } from "./api";

const oturum = vi.hoisted(() => ({ ozet: vi.fn() }));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  oturumApi: oturum,
}));

import { YETENEK_ADLARI } from "./api";
import { OTURUM_DEGISTI_OLAYI } from "./eylemler";
import {
  kalanSaniye,
  sureBicimle,
  useEtkinlikNabzi,
  useOturum,
  useYetenekler,
  useYuklemeSiniri,
  yeteneklerOku,
} from "./useOturum";

function ozetOlustur(durum: OturumDurumAdi, ek: Partial<OturumOzeti> = {}): OturumOzeti {
  const acik = durum === "acik";
  return {
    durum,
    hesap: acik
      ? {
          id: "h-1",
          tanitici: "yonetici",
          rol: "yonetici",
          rol_etiketi: "Program yöneticisi",
          yetenekler: [],
        }
      : null,
    bosta_dk: 10,
    bosta_kalan_sn: acik ? 600 : null,
    kilit_bekliyor: false,
    kurulum_tamam: true,
    yukleme_siniri_mb: 20,
    ...ek,
  };
}

function OturumYazici() {
  const { ozet } = useOturum();
  useEtkinlikNabzi(ozet?.durum, () => {});
  return <p>oturum: {ozet?.durum ?? "yok"}</p>;
}

function bas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <OturumYazici />
    </QueryClientProvider>,
  );
}

describe("kalanSaniye", () => {
  const T0 = 1_000_000;

  it("boşta kalan süreyi geçen süreyi düşerek verir; mutlak süre yoktur", () => {
    const ozet = ozetOlustur("acik", { bosta_kalan_sn: 161 });
    expect(kalanSaniye(ozet, T0, T0, -Infinity)).toBe(161);
    expect(kalanSaniye(ozet, T0, T0 + 60_000, -Infinity)).toBe(101);
    expect(kalanSaniye(ozet, T0, T0 + 500_000, -Infinity)).toBe(0);
  });

  it("özetten sonra giden başlıklı istek boşta sayacını tazeler", () => {
    const ozet = ozetOlustur("acik", { bosta_kalan_sn: 100, bosta_dk: 3 });
    // 90 sn sonra bir kullanıcı eylemi gitti; 10 sn daha geçti.
    expect(kalanSaniye(ozet, T0, T0 + 100_000, T0 + 90_000)).toBe(170);
    // Eylem özetten ÖNCE gittiyse sunucu onu zaten saymıştır.
    expect(kalanSaniye(ozet, T0, T0 + 10_000, T0 - 5_000)).toBe(90);
  });

  it("kurulumda, kilit beklerken (sunucu süre vermez) ve açık oturum dışında boştur", () => {
    expect(kalanSaniye(ozetOlustur("acik", { bosta_kalan_sn: null }), T0, T0, -Infinity)).toBe(
      null,
    );
    expect(kalanSaniye(ozetOlustur("kilitli"), T0, T0, -Infinity)).toBeNull();
    expect(kalanSaniye(ozetOlustur("kurulum"), T0, T0, -Infinity)).toBeNull();
  });
});

describe("sureBicimle", () => {
  it.each([
    [0, "0:00"],
    [9, "0:09"],
    [161, "2:41"],
    [1800, "30:00"],
  ])("%i sn → %s", (saniye, beklenen) => {
    expect(sureBicimle(saniye)).toBe(beklenen);
  });
});

describe("useOturum", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    etkinlikSaatleriniSifirla();
  });

  it("yoklama etkinlik başlığı olmadan gider ve açık oturum ön yüzü “açık sanır”a geçirir", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    bas();
    expect(await screen.findByText("oturum: acik")).toBeInTheDocument();
    expect(oturum.ozet).toHaveBeenCalledWith(false);
    expect(oturumAcikSaniliyor()).toBe(true);
  });

  it("423 olayı (ön yüz kilitli bilirken) sorguyu yeniler", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("kilitli"));
    bas();
    await screen.findByText("oturum: kilitli");
    oturum.ozet.mockResolvedValue(ozetOlustur("guvenlik_dosyasi_kayip"));
    act(() => {
      window.dispatchEvent(new CustomEvent(KILIT_KAPISI_OLAYI));
    });
    expect(await screen.findByText("oturum: guvenlik_dosyasi_kayip")).toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("pencere yüklenmeden açılan oturum (ilk hesap) olayla hemen okunur", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("kurulum"));
    bas();
    await screen.findByText("oturum: kurulum");
    oturum.ozet.mockResolvedValue(ozetOlustur("acik", { kurulum_tamam: false }));
    act(() => {
      window.dispatchEvent(new CustomEvent(OTURUM_DEGISTI_OLAYI));
    });
    expect(await screen.findByText("oturum: acik")).toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("açık sanılan oturum kilitli görünürse pencere yeniden yüklenir", async () => {
    oturumAcikSan(true);
    oturum.ozet.mockResolvedValue(ozetOlustur("kilitli"));
    bas();
    await screen.findByText("oturum: kilitli");
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("sorgu hatasında özet boştur (fail-open), bayrağa dokunulmaz", async () => {
    oturum.ozet.mockRejectedValue(new Error("ağ yok"));
    bas();
    await waitFor(() => expect(oturum.ozet).toHaveBeenCalled());
    expect(screen.getByText("oturum: yok")).toBeInTheDocument();
    expect(oturumAcikSaniliyor()).toBe(false);
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });
});

describe("useEtkinlikNabzi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    etkinlikSaatleriniSifirla();
  });

  it("açık oturumda etkileşim nabız gönderir, hemen ikincisi gönderilmez", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    bas();
    await screen.findByText("oturum: acik");
    oturum.ozet.mockClear();

    act(() => {
      window.dispatchEvent(new Event("pointerdown"));
      window.dispatchEvent(new Event("keydown"));
    });

    await waitFor(() => expect(oturum.ozet).toHaveBeenCalledTimes(1));
    expect(oturum.ozet).toHaveBeenCalledWith(true);
  });

  it("nabız hatası sessizdir", async () => {
    oturum.ozet.mockResolvedValueOnce(ozetOlustur("acik")).mockRejectedValue(new Error("x"));
    bas();
    await screen.findByText("oturum: acik");

    act(() => window.dispatchEvent(new Event("pointerdown")));

    await waitFor(() => expect(oturum.ozet).toHaveBeenLastCalledWith(true));
    expect(screen.getByText("oturum: acik")).toBeInTheDocument();
  });

  it.each<OturumDurumAdi>(["kilitli", "kurulum"])(
    "%s durumunda nabız gönderilmez",
    async (durum) => {
      oturum.ozet.mockResolvedValue(ozetOlustur(durum));
      bas();
      await screen.findByText(`oturum: ${durum}`);
      oturum.ozet.mockClear();

      act(() => window.dispatchEvent(new Event("pointerdown")));

      expect(oturum.ozet).not.toHaveBeenCalled();
    },
  );
});

describe("yetenekler (ön yüz süzmesinin tek kaynağı; plan F1b-2)", () => {
  it("özet okunmadıysa bilinmez (null); açık oturumda hesabın listesi, yoksa boş", () => {
    expect(yeteneklerOku(null)).toBeNull();
    expect(yeteneklerOku(undefined)).toBeNull();
    expect(yeteneklerOku(ozetOlustur("kilitli"))).toEqual([]);
    const hesap = {
      id: "h-1",
      tanitici: "yonetici",
      rol: "yonetici" as const,
      rol_etiketi: "Program yöneticisi",
      yetenekler: ["iki_depo"],
    };
    const acik = ozetOlustur("acik");
    expect(yeteneklerOku({ ...acik, hesap })).toEqual(["iki_depo"]);
    // Eski sunucu alanı göndermezse hiçbir yetenek yoktur (fail-closed).
    const eski = JSON.parse(
      JSON.stringify({ ...acik, hesap: { ...hesap, yetenekler: undefined } }),
    );
    expect(yeteneklerOku(eski as OturumOzeti)).toEqual([]);
  });

  it("ön yüzün yetenek adı listesi (anlık görüntü; arka yüzle eşitliğini backend `test_yetenek_adlari_on_yuzle_birebir` sınar)", () => {
    expect([...YETENEK_ADLARI]).toEqual([
      "ayrilis_havuzu",
      "birlik_donemi_yazma",
      "birlik_kisi_yazma",
      "bosta_sure_yazma",
      "butunluk_denetim",
      "ders_yili_yazma",
      "dk_gorev_bolumu_yazma",
      "dk_yedek_cagirma",
      "eokul_aktarimi",
      "erisim_gunlugu",
      "geri_yukleme_gordum",
      "gorev_alma_engeli",
      "gorev_bolumu_yazma",
      "guncelleme",
      "guvenlik",
      "iki_depo",
      "kapali_gun_yazma",
      "karar_taslagi_uretme",
      "kisi_yazma",
      "kullanicilar",
      "kurulum_tamamlama",
      "okul_karti_yazma",
      "organ_yazma",
      "son_oturum_onay",
      "temsilci_yazma",
      "toplanti_gunu_yazma",
      "uyelik_dusurme",
      "veli_listesi",
      "yol_haritasi",
    ]);
  });
});

function YetenekYazici() {
  const { yetenekler, hata } = useYetenekler();
  const liste = yetenekler === null ? "bilinmiyor" : yetenekler.join(",") || "boş";
  return <p>{`yetenekler: ${liste} · hata: ${hata === null ? "yok" : hata.message}`}</p>;
}

function yetenekliOzet(yetenekler: string[]): OturumOzeti {
  return {
    ...ozetOlustur("acik"),
    hesap: {
      id: "h-1",
      tanitici: "yonetici",
      rol: "yonetici",
      rol_etiketi: "Program yöneticisi",
      yetenekler,
    },
  };
}

function yetenekleriBas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <YetenekYazici />
    </QueryClientProvider>,
  );
  return queryClient;
}

function SinirYazici() {
  return <p>{`sınır: ${useYuklemeSiniri() ?? "bilinmiyor"}`}</p>;
}

function sinirBas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <SinirYazici />
    </QueryClientProvider>,
  );
}

describe("useYuklemeSiniri", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sınır özetten okunur", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("acik", { yukleme_siniri_mb: 7 }));
    sinirBas();
    expect(await screen.findByText("sınır: 7")).toBeInTheDocument();
    expect(oturum.ozet).toHaveBeenCalledWith(false);
  });

  it("özet beklenirken sınır bilinmez", async () => {
    oturum.ozet.mockReturnValue(new Promise(() => {}));
    sinirBas();
    expect(await screen.findByText("sınır: bilinmiyor")).toBeInTheDocument();
  });

  it("özet okunamazsa sınır bilinmez", async () => {
    oturum.ozet.mockRejectedValue(new TypeError("çevrimdışı"));
    sinirBas();
    await waitFor(() => expect(oturum.ozet).toHaveBeenCalled());
    expect(await screen.findByText("sınır: bilinmiyor")).toBeInTheDocument();
  });
});

describe("useYetenekler (yükleniyor, okundu, okunamadı ayrıdır)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("özet beklenirken yetenekler bilinmez ve hata yoktur", async () => {
    oturum.ozet.mockReturnValue(new Promise(() => {}));
    yetenekleriBas();
    expect(await screen.findByText("yetenekler: bilinmiyor · hata: yok")).toBeInTheDocument();
  });

  it("özet okununca hesabın yetenekleri gelir", async () => {
    oturum.ozet.mockResolvedValue(yetenekliOzet(["butunluk_denetim", "iki_depo"]));
    yetenekleriBas();
    expect(
      await screen.findByText("yetenekler: butunluk_denetim,iki_depo · hata: yok"),
    ).toBeInTheDocument();
  });

  it("özet hiç okunamazsa hata verilir (çağıran “okunamadı” kartını seçer)", async () => {
    oturum.ozet.mockRejectedValue(new ApiError(500, "500", "Sunucu hatası."));
    yetenekleriBas();
    expect(
      await screen.findByText("yetenekler: bilinmiyor · hata: Sunucu hatası."),
    ).toBeInTheDocument();
  });

  it("özet bir kez okunduysa sonraki yoklamanın hatası son bilinen yetenekleri düşürmez", async () => {
    oturum.ozet.mockResolvedValue(yetenekliOzet(["iki_depo"]));
    const queryClient = yetenekleriBas();
    await screen.findByText("yetenekler: iki_depo · hata: yok");

    oturum.ozet.mockRejectedValue(new ApiError(500, "500", "Sunucu hatası."));
    await act(() => queryClient.refetchQueries({ queryKey: ["oturum"] }));

    await waitFor(() => expect(oturum.ozet).toHaveBeenCalledTimes(2));
    expect(screen.getByText("yetenekler: iki_depo · hata: yok")).toBeInTheDocument();
  });
});
