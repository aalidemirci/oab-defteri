// Kabuk + yönlendirme testi (aile iskeletinin kalıbı).
// Pinlenen davranışlar: (1) kurulum kapısı — `setup_completed=false` iken her rota
// sihirbaza düşer, `true` iken Genel Bakış açılır, durum okunamazsa kapı FAIL-OPEN;
// (2) kabuk gezinmesi (Genel Bakış/Kişiler/Ayarlar/Kılavuz + Hakkında) ve
// kopyalanmayan modüllerin bağlantı ve rotalarının iskelete sızmaması;
// (3) açılışta güncelleme denetimi YOK — kabuk açılırken `/updates/` isteği
// çıkmaz (tasarım TK4); (4) M3 token bütünlüğü — kaynakta kullanılan
// şekil/opaklık sınıflarının Tailwind çıktısında gerçekten üretildiği (aile
// iskeletinin dersi); (5) oturum (tasarım §4.4.3, TK14) — açık oturumda üst çubukta
// oturum göstergesi (rol etiketi + tanıtıcı, Kilitle); Kilitle pencereyi yeniden
// yükler (D53); oturum okunamazsa FAIL-OPEN. Aile iskeletinin görevli kipi (görevli
// ekranı, gezinmesiz kabuk, gizli güncelleme bandı) yoktur.

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import postcss from "postcss";
import { MemoryRouter } from "react-router-dom";
import tailwindcss from "tailwindcss";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MockInstance } from "vitest";

import { ConfirmProvider } from "./ui/ConfirmProvider";
import { SnackbarProvider } from "./ui/SnackbarProvider";
import type { SetupStatus } from "./modules/okul/api";
import { KURULU_DURUM } from "./test/kurulumDurumu";

const okulApiMock = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getSchoolConfig: vi.fn(),
  updateSchoolConfig: vi.fn(),
  completeSetup: vi.fn(),
  getGradeLevels: vi.fn(),
  listSchoolYears: vi.fn(),
  listSchoolTerms: vi.fn(),
  listStudents: vi.fn(),
  listPersonnel: vi.fn(),
  listClassSections: vi.fn(),
  listHolidays: vi.fn(),
  markRoadmapItem: vi.fn(),
  setRoadmapHidden: vi.fn(),
  // Genel Bakış'taki "Ayrılış Havuzu" kartı yalnız sayıları okur.
  getLeavePoolSummary: vi.fn(),
}));

vi.mock("./modules/okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./modules/okul/api")>();
  return { ...actual, okulApi: okulApiMock };
});

const oturumApiMock = vi.hoisted(() => ({
  ozet: vi.fn(),
  hesaplar: vi.fn(),
  ac: vi.fn(),
  kilitle: vi.fn(),
  kurtar: vi.fn(),
  kurtarmaHesaplari: vi.fn(),
}));

vi.mock("./modules/oturum/api", () => ({ oturumApi: oturumApiMock }));

import App from "./App";
import { denetimSonucunuYayinla } from "./modules/guncelleme/denetimOlayi";
import { pencereIcerigi } from "./lib/kilit";
import type { OturumOzeti } from "./modules/oturum/api";

const ACIK_OTURUM: OturumOzeti = {
  durum: "acik",
  hesap: { id: "h-1", tanitici: "yonetici", rol: "yonetici", rol_etiketi: "Program yöneticisi" },
  bosta_dk: 10,
  bosta_kalan_sn: 600,
  kilit_bekliyor: false,
  kurulum_tamam: true,
};

const KURULU: SetupStatus = {
  ...KURULU_DURUM,
  student_count: 482,
  personnel_count: 37,
  class_section_count: 18,
};

// Parola kurulu ama okul ve takvim adımları eksik (kurulum tamamlanmamış).
const KURULMAMIS: SetupStatus = {
  ...KURULU,
  setup_completed: false,
  school_name: "",
  school_info_complete: false,
  has_active_school_year: false,
  active_school_year: null,
  missing_steps: ["school", "calendar"],
  student_count: 0,
  personnel_count: 0,
};

/** main.tsx ile aynı sağlayıcı zinciri — sayfalar react-query, snackbar ve confirm
 *  bekliyor. Her ekran taze önbellekle açılır; başarısız sorgu yeniden denenmez. */
function ekranaBas(yol = "/") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[yol]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <App />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/**
 * Kabuğun üst çubuğu. Testing Library her `<header>`i "banner" sayar (sayfa
 * içi `<header>` için ARIA istisnasını uygulamaz); kabuğunki DOM'da İLKİDİR.
 */
function ustCubuk(): HTMLElement {
  return screen.getAllByRole("banner")[0];
}

beforeEach(() => {
  vi.clearAllMocks();
  okulApiMock.getSetupStatus.mockResolvedValue(KURULU);
  okulApiMock.getSchoolConfig.mockResolvedValue({
    school_name: "Örnek Anadolu Lisesi",
    province: "İstanbul",
    district: "Örnek",
    principal_name: "",
    has_prep_class: false,
    kademe: "ORTAOGRETIM",
    kisa_ad: "Örnek AL",
    demirbas_onayi: true,
    demirbas_no: "",
    setup_completed: true,
  });
  okulApiMock.getGradeLevels.mockResolvedValue({
    levels: [
      { value: 9, label: "9" },
      { value: 10, label: "10" },
    ],
    prep_enabled: false,
  });
  okulApiMock.listSchoolYears.mockResolvedValue([]);
  okulApiMock.listSchoolTerms.mockResolvedValue([]);
  okulApiMock.listClassSections.mockResolvedValue([]);
  okulApiMock.listHolidays.mockResolvedValue([]);
  const bosSayfa = { count: 0, next: null, previous: null, results: [] };
  okulApiMock.listStudents.mockResolvedValue(bosSayfa);
  okulApiMock.listPersonnel.mockResolvedValue(bosSayfa);
  okulApiMock.getLeavePoolSummary.mockResolvedValue({ student_count: 0, personnel_count: 0 });
  oturumApiMock.ozet.mockResolvedValue(ACIK_OTURUM);
});

describe("App — oturum", () => {
  it("açık oturumda üst çubukta rol etiketi, tanıtıcı ve Kilitle durur; sayfalar açılır", async () => {
    ekranaBas("/");
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
    const cubuk = ustCubuk();
    const gosterge = await within(cubuk).findByRole("group", { name: "Oturum" });
    expect(within(gosterge).getByText("Program yöneticisi")).toBeInTheDocument();
    expect(within(gosterge).getByText("yonetici")).toBeInTheDocument();
    expect(within(gosterge).getByRole("button", { name: "Kilitle" })).toBeInTheDocument();
    // Yoklama oturumu canlı tutmaz (etkinlik başlığı yok).
    expect(oturumApiMock.ozet).toHaveBeenCalledWith(false);
    // Görevli kipinin izi kalmadı.
    expect(within(cubuk).queryByText(/kipi/)).not.toBeInTheDocument();
    expect(within(cubuk).queryByRole("button", { name: /kipine geç/ })).not.toBeInTheDocument();
    expect(within(cubuk).getByRole("button", { name: "Çık" })).toBeInTheDocument();
  });

  it("Kilitle pencereyi yeniden yükler (sorgu önbelleği ve modül belleği gider)", async () => {
    const user = userEvent.setup();
    oturumApiMock.kilitle.mockResolvedValue({
      ...ACIK_OTURUM,
      sonuc: "kilitlendi",
      durum: "kilitli",
      hesap: null,
    });
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });

    await user.click(await within(ustCubuk()).findByRole("button", { name: "Kilitle" }));

    expect(oturumApiMock.kilitle).toHaveBeenCalledTimes(1);
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("güncelleme bandı açık oturumda görünür (görevli kipindeki gizleme kalktı)", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });

    // Ayarlar → Güncelleme'de elle denetlendi ve yeni sürüm bulundu.
    act(() =>
      denetimSonucunuYayinla({
        current_version: "2026.9.0",
        latest_version: "2026.10.0",
        update_available: true,
        release_name: "",
        published_at: "",
        release_url: "",
        platform: "windows",
        can_download: true,
        installer_name: "kurulum.exe",
        installer_size: 1,
      }),
    );
    expect(await screen.findByText(/OAB Defteri 2026\.10\.0 hazır\./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Güncellemeyi indir" })).toBeInTheDocument();
  });

  it("oturum okunamazsa sayfalar açılır, gösterge görünmez (fail-open)", async () => {
    oturumApiMock.ozet.mockRejectedValue(new Error("ağ yok"));
    ekranaBas("/");
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
    await waitFor(() => expect(oturumApiMock.ozet).toHaveBeenCalled());
    expect(screen.queryByRole("group", { name: "Oturum" })).not.toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });
});

describe("App — kurulum kapısı", () => {
  it("kurulum tamamlanmadıysa kök rotadan sihirbaza yönlendirir", async () => {
    okulApiMock.getSetupStatus.mockResolvedValue(KURULMAMIS);
    ekranaBas("/");
    expect(await screen.findByRole("heading", { name: "Kurulum Sihirbazı" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Genel Bakış" })).not.toBeInTheDocument();
  });

  it("kurulum tamamlanmadıysa iç rotalardan da sihirbaza yönlendirir", async () => {
    okulApiMock.getSetupStatus.mockResolvedValue(KURULMAMIS);
    ekranaBas("/kisiler");
    expect(await screen.findByRole("heading", { name: "Kurulum Sihirbazı" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kişiler" })).not.toBeInTheDocument();
  });

  it("kurulum tamamlandıysa kök rotada Genel Bakış açılır", async () => {
    ekranaBas("/");
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
  });

  it("kurulum tamamlandıktan sonra sihirbaz elle açılabilir kalır", async () => {
    ekranaBas("/kurulum");
    expect(await screen.findByRole("heading", { name: "Kurulum Sihirbazı" })).toBeInTheDocument();
  });

  it("durum okunamazsa kapı açılır (fail-open) — program kilitlenmez", async () => {
    okulApiMock.getSetupStatus.mockRejectedValue(new Error("ağ yok"));
    ekranaBas("/");
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
  });
});

describe("App — kabuk gezinmesi", () => {
  it("gezinme tam olarak Genel Bakış, Kişiler, Ayarlar ve Kılavuz'dur (bu sırayla)", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    const baglantilar = within(gezinme).getAllByRole("link");
    const beklenen: Array<[ad: string, yol: string]> = [
      ["Genel Bakış", "/"],
      ["Kişiler", "/kisiler"],
      ["Ayarlar", "/ayarlar"],
      ["Kılavuz", "/kilavuz"],
    ];
    expect(baglantilar).toHaveLength(beklenen.length);
    beklenen.forEach(([ad, yol], i) => {
      expect(baglantilar[i]).toHaveAccessibleName(ad);
      expect(baglantilar[i]).toHaveAttribute("href", yol);
    });
    expect(screen.getByRole("link", { name: "Hakkında ve Lisans" })).toHaveAttribute(
      "href",
      "/hakkinda",
    );
  });

  it("Kişiler bağlantısına tıklayınca sicil sayfası açılır", async () => {
    const user = userEvent.setup();
    ekranaBas("/");
    const gezinme = await screen.findByRole("navigation", { name: "Ana gezinme" });
    await user.click(within(gezinme).getByRole("link", { name: "Kişiler" }));
    expect(await screen.findByRole("heading", { name: "Kişiler" })).toBeInTheDocument();
  });

  it("Ayarlar bağlantısına tıklayınca ayarlar sayfası açılır", async () => {
    const user = userEvent.setup();
    ekranaBas("/");
    const gezinme = await screen.findByRole("navigation", { name: "Ana gezinme" });
    await user.click(within(gezinme).getByRole("link", { name: "Ayarlar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Ayarlar" })).toBeInTheDocument();
  });

  it("Hakkında ve Lisans bağlantısı geliştirici ve kullanım koşullarını gösterir", async () => {
    const user = userEvent.setup();
    ekranaBas("/");
    await user.click(await screen.findByRole("link", { name: "Hakkında ve Lisans" }));
    expect(await screen.findByRole("heading", { name: "Hakkında ve Lisans" })).toBeInTheDocument();
    expect(screen.getByText("Ahmet Ali DEMİRCİ")).toBeInTheDocument();
    expect(screen.getByText(/PolyForm Noncommercial License 1.0.0/)).toBeInTheDocument();
  });

  it("Kılavuz bağlantısı kullanım kılavuzunu açar", async () => {
    const user = userEvent.setup();
    ekranaBas("/");
    await user.click(await screen.findByRole("link", { name: "Kılavuz" }));
    expect(
      await screen.findByRole("heading", { level: 1, name: "Kullanım Kılavuzu" }),
    ).toBeInTheDocument();
  });

  // docs/sozluk.md §4: üst çubuktaki başlık sayfanın h1'iyle AYNIDIR. Eskiden
  // üst çubuk "Genel bakış", sayfa "Panel", gezinme "Panel" diyordu.
  it.each([
    ["/", "Genel Bakış"],
    ["/kisiler", "Kişiler"],
    ["/ayarlar", "Ayarlar"],
    ["/kilavuz", "Kullanım Kılavuzu"],
    ["/hakkinda", "Hakkında ve Lisans"],
    ["/kurulum", "Kurulum Sihirbazı"],
  ])("üst çubuk başlığı sayfanın h1'iyle aynıdır: %s", async (yol, baslik) => {
    ekranaBas(yol);
    expect(await screen.findByRole("heading", { level: 1, name: baslik })).toBeInTheDocument();
    expect(within(ustCubuk()).getByText(baslik)).toBeInTheDocument();
  });

  it("tema anahtarı tek yerdedir (kenar çubuğu) — üst çubukta ikinci kopya yok", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    expect(screen.getAllByRole("button", { name: /temaya geç/ })).toHaveLength(1);
    expect(
      within(ustCubuk()).queryByRole("button", { name: /temaya geç/ }),
    ).not.toBeInTheDocument();
  });

  it("kopyalanmayan modüllerin bağlantıları iskelete sızmadı (gezinme ve Genel Bakış)", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    // Kaynak programların gezinme etiketleri — tam ad. Aile iskeletinin kütüphane
    // ekranları da (F1a-2'de söküldü) burada denetlenir.
    for (const ad of [
      "Dolaşım Masası",
      "Katalog",
      "Raporlar",
      "Takvimler",
      "Oturumlar",
      "Mazeret Takibi",
      "Salonlar",
      "Ders Havuzu",
      "BEP",
      "Disiplin",
      "Onur / Ödül",
      "Bilgi Notları",
    ]) {
      expect(screen.queryByRole("link", { name: ad })).not.toBeInTheDocument();
    }
    const hedefler = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    for (const yol of [
      "/takvimler",
      "/oturumlar",
      "/mazeret",
      "/salonlar",
      "/dersler",
      "/dolasim",
      "/katalog",
      "/raporlar",
      "/ag-doktoru",
    ]) {
      expect(hedefler).not.toContain(yol);
    }
  });

  it.each([
    "/takvimler",
    "/oturumlar",
    "/mazeret",
    "/salonlar",
    "/dersler",
    // Aile iskeletinin kütüphane rotaları (F1a-2'de söküldü).
    "/dolasim",
    "/katalog",
    "/katalog/sayim",
    "/raporlar",
    "/ag-doktoru",
    "/gecikmis-oduncler",
    "/yil-sonu",
  ])("kaldırılan rota %s hiçbir sayfa açmaz; üst çubuk program adını gösterir", async (yol) => {
    // Yönlendiricinin "eşleşen rota yok" uyarısı beklenen sonuçtur: yakalanır
    // ve kanıt olarak denetlenir (test çıktısını da kirletmez).
    const uyari = vi.spyOn(console, "warn").mockImplementation(() => {});
    try {
      ekranaBas(yol);
      // Kabuk yüklenir (gezinme durur); kilit ve kurulum kapıları geçilince
      // iskelet kalkar ama rota eşleşmediği için sayfa başlığı yoktur.
      await screen.findByRole("navigation", { name: "Ana gezinme" });
      await waitFor(() => expect(okulApiMock.getSetupStatus).toHaveBeenCalled());
      await waitFor(() => expect(screen.queryByText("Yükleniyor…")).not.toBeInTheDocument());
      expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
      expect(within(ustCubuk()).getAllByText("OAB Defteri").length).toBeGreaterThan(0);
      expect(uyari).toHaveBeenCalledWith(
        expect.stringContaining(`No routes matched location "${yol}"`),
      );
    } finally {
      uyari.mockRestore();
    }
  });
});

describe("App — açılışta dış istek yok", () => {
  let fetchCasusu: MockInstance<typeof fetch>;

  beforeEach(() => {
    // Ağ katmanı en alttan dinlenir: okulApi dışındaki her istek (güvenlik
    // durumu, güncelleme…) buradan geçer. Çevrimdışı gibi davranır.
    fetchCasusu = vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("çevrimdışı"));
  });

  afterEach(() => {
    fetchCasusu.mockRestore();
  });

  it("kabuk açılırken /updates/ isteği çıkmaz (güncelleme yalnız elle denetlenir)", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });

    const yollar = fetchCasusu.mock.calls.map(([girdi]) => String(girdi));
    // Casus gerçekten ağ katmanını görüyor: kilit kapısı güvenlik durumunu sordu.
    expect(yollar.some((y) => y.includes("/security/status/"))).toBe(true);
    expect(yollar.filter((y) => y.includes("/updates/"))).toEqual([]);
    // Dış istek yalnız kullanıcının başlattığı güncelleme denetiminden çıkar
    // (tasarım §4.1). Açılışta olmaz: kabuk hiçbir mutlak adrese istek atmaz,
    // bütün istekler yerel sunucuya göreli yollardır.
    expect(yollar.filter((y) => /^[a-z]+:\/\//i.test(y))).toEqual([]);
  });

  it("gezinme boyunca da /updates/ isteği çıkmaz", async () => {
    const user = userEvent.setup();
    ekranaBas("/");
    const gezinme = await screen.findByRole("navigation", { name: "Ana gezinme" });
    for (const ad of ["Kişiler", "Kılavuz", "Genel Bakış"]) {
      await user.click(within(gezinme).getByRole("link", { name: ad }));
    }
    await screen.findByRole("heading", { level: 1, name: "Genel Bakış" });

    const yollar = fetchCasusu.mock.calls.map(([girdi]) => String(girdi));
    expect(yollar.filter((y) => y.includes("/updates/"))).toEqual([]);
  });
});

// --- M3 token bütünlüğü ------------------------------------------------------
// Tailwind JIT, ölçekte KARŞILIĞI OLMAYAN bir token için sessizce hiç kural
// üretmez: `rounded-shape-full` ya da `bg-on-surface/8` yazılınca derleme
// patlamaz, sınıf yok sayılır ve kusur ancak gözle fark edilir (aile iskeletinde
// görüldü: köşeli gezinme sekmeleri, hiç oluşmayan hover geri bildirimi).
// Bu test gerçek Tailwind çıktısını üretip kaynakta kullanılan her şekil ve
// opaklık token'ının CSS'te GERÇEKTEN yer aldığını doğrular.

// Vitest'in çalışma dizini proje kökü (`frontend/`) — `import.meta.url` burada
// dosya URL'i değil (vite-node sanal yolu), o yüzden cwd tabanlı çözülür.
const KOK = process.cwd();
const SRC_DIR = path.join(KOK, "src");

/** `src/` altındaki tüm ürün kaynağı (test dosyaları hariç). */
function kaynakDosyalari(dizin: string): string[] {
  const cikti: string[] = [];
  for (const girdi of readdirSync(dizin, { withFileTypes: true })) {
    const yol = path.join(dizin, girdi.name);
    if (girdi.isDirectory()) cikti.push(...kaynakDosyalari(yol));
    else if (/\.tsx?$/.test(girdi.name) && !/\.test\.tsx?$/.test(girdi.name)) cikti.push(yol);
  }
  return cikti;
}

// Şekil ölçeği: `rounded-shape-*`. Opaklık modifiyesi: yalnız SAYISAL olanlar —
// `bg-scrim/[0.32]` gibi keyfi değerler ölçeğe bakmadan üretildiği için kapsam dışı.
const SEKIL_DESENI = /\brounded-shape-[a-z0-9]+/g;
const OPAKLIK_DESENI =
  /\b(?:bg|text|border|ring|outline|fill|stroke|divide|from|via|to)-[a-z][a-z0-9-]*\/\d+\b/g;

/** Sınıf adının CSS'te üretilmiş bir seçici olarak var olup olmadığı.
 *
 * CSS çıktısında `/` kaçışlıdır (`.bg-primary\/8`). Sınıf bir varyantın ardından
 * da gelebilir (`hover:`, `placeholder:` → `.hover\:bg-primary\/8`), o yüzden
 * önünde `.` ya da kaçışlı `:` aranır.
 */
function uretildiMi(css: string, sinif: string): boolean {
  const desen = sinif
    .replace(/\//g, "\\/") // CSS kaçışı
    .replace(/[.\\/]/g, "\\$&"); // regex kaçışı
  return new RegExp(`(?:\\.|\\\\:)${desen}(?![\\w-])`).test(css);
}

describe("M3 token bütünlüğü", () => {
  it("kaynakta kullanılan şekil ve opaklık token'ları Tailwind çıktısında üretilir", async () => {
    const kullanilan = new Map<string, string>(); // sınıf → ilk görüldüğü dosya
    for (const dosya of kaynakDosyalari(SRC_DIR)) {
      const metin = readFileSync(dosya, "utf8");
      for (const desen of [SEKIL_DESENI, OPAKLIK_DESENI]) {
        for (const eslesme of metin.matchAll(desen)) {
          if (!kullanilan.has(eslesme[0]))
            kullanilan.set(eslesme[0], path.relative(SRC_DIR, dosya));
        }
      }
    }
    expect(kullanilan.size).toBeGreaterThan(0); // tarama gerçekten bir şey buldu

    const { css } = await postcss([
      tailwindcss({ config: path.join(KOK, "tailwind.config.js") }),
    ]).process("@tailwind utilities;", { from: undefined });

    const tanimsiz = [...kullanilan].filter(([sinif]) => !uretildiMi(css, sinif));
    expect(tanimsiz.map(([sinif, dosya]) => `${sinif} (${dosya})`)).toEqual([]);
  }, 60_000);
});
