// Kabuk + yönlendirme testi (aile iskeletinin kalıbı).
// Pinlenen davranışlar: (1) kurulum kapısı — `setup_completed=false` iken her rota
// sihirbaza düşer, `true` iken Genel Bakış açılır, durum okunamazsa kapı FAIL-OPEN;
// (2) kabuk gezinmesi (Genel Bakış/Birlik Dönemi/Kişiler/Organlar/Temsilciler/Kullanıcılar/Erişim
// Günlüğü/Ayarlar/Kılavuz + Hakkında;
// Kullanıcılar yalnız `kullanicilar`, Erişim Günlüğü yalnız `erisim_gunlugu` yeteneğinde) ve
// kopyalanmayan modüllerin bağlantı ve rotalarının iskelete sızmaması;
// (3) açılışta güncelleme denetimi YOK — kabuk açılırken `/updates/` isteği
// çıkmaz (tasarım TK4); (4) M3 token bütünlüğü — kaynakta kullanılan
// şekil/opaklık sınıflarının Tailwind çıktısında gerçekten üretildiği (aile
// iskeletinin dersi); (5) oturum (tasarım §4.4.3, TK14) — açık oturumda üst çubukta
// oturum göstergesi (rol etiketi + tanıtıcı, Kilitle); Kilitle pencereyi yeniden
// yükler (D53); oturum okunamazsa FAIL-OPEN. Aile iskeletinin görevli kipi (görevli
// ekranı, gezinmesiz kabuk, gizli güncelleme bandı) yoktur; (6) parola yenilenme
// bildirimi (tasarım §4.4.3, tehdit 12) Genel Bakış dışındaki sayfada da pencere olarak çıkar;
// (7) kapanış bekleme penceresi (plan F1b-3 "Uzun iş, çarpı, temiz kapanış") kapıların dışındadır.

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

import { yenidenBaslatGerekliYayinla } from "./lib/restart";
import { ConfirmProvider } from "./ui/ConfirmProvider";
import { SnackbarProvider } from "./ui/SnackbarProvider";
import { guvenlikApi } from "./modules/guvenlik/api";
import { OKUNAMADI as GUVENLIK_OKUNAMADI } from "./modules/guvenlik/GuvenlikKapisi";
import type { SetupStatus } from "./modules/okul/api";
import { gorunenMetin } from "./test/gorunenMetin";
import { KURULU_DURUM } from "./test/kurulumDurumu";
import { ORNEK_OKUL_KARTI } from "./test/okulKarti";

const okulApiMock = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getSchoolConfig: vi.fn(),
  updateSchoolConfig: vi.fn(),
  completeSetup: vi.fn(),
  listSchoolYears: vi.fn(),
  listSchoolTerms: vi.fn(),
  listPersonnel: vi.fn(),
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

vi.mock("./modules/oturum/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./modules/oturum/api")>()),
  oturumApi: oturumApiMock,
}));

// Kullanıcılar ekranı (yalnız `kullanicilar` yeteneği): liste tek hesaptır.
const kullanicilarApiMock = vi.hoisted(() => ({
  liste: vi.fn(),
  secenekler: vi.fn(),
  ayrinti: vi.fn(),
}));

vi.mock("./modules/kullanicilar/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./modules/kullanicilar/api")>()),
  kullanicilarApi: kullanicilarApiMock,
}));

// Erişim Günlüğü (yalnız `erisim_gunlugu` yeteneği): günlük boştur.
const erisimApiMock = vi.hoisted(() => ({ sayfa: vi.fn() }));

vi.mock("./modules/erisim/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./modules/erisim/api")>()),
  erisimGunluguApi: erisimApiMock,
}));

// Denetim izi (Genel Bakış kartları, parola yenilenme bildirimi): varsayılan "okunamadı",
// yani kartlar ve bildirim görünmez; bildirimin kendi testi aşağıda.
const butunlukApiMock = vi.hoisted(() => ({
  durum: vi.fn(),
  sahipsizSarmallariSil: vi.fn(),
  parolaBildirimi: vi.fn(),
  parolaBildiriminiGordum: vi.fn(),
}));

vi.mock("./modules/butunluk/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./modules/butunluk/api")>()),
  butunlukApi: butunlukApiMock,
}));

import App from "./App";
import { denetimSonucunuYayinla } from "./modules/guncelleme/denetimOlayi";
import { pencereIcerigi } from "./lib/kilit";
import { YETENEK_ADLARI } from "./modules/oturum/api";
import type { OturumOzeti } from "./modules/oturum/api";
import { KENDI_HESABI } from "./test/kullanicilar";
import { ROL_YETKISIZ_OLAYI } from "./lib/api";
import { gezinmeGirdileri } from "./AppShell";
import type { NavItem } from "./AppShell";
import { KURULUM, OKUNAMADI, YUKLENIYOR, hazirYetki } from "./modules/oturum/yetki";

const ACIK_OTURUM: OturumOzeti = {
  durum: "acik",
  hesap: {
    id: "h-1",
    tanitici: "yonetici",
    rol: "yonetici",
    rol_etiketi: "Program yöneticisi",
    // Program yöneticisinin yetenekleri (sunucu türetir; süzme `oturum/yetki`).
    yetenekler: [...YETENEK_ADLARI],
  },
  bosta_dk: 10,
  bosta_kalan_sn: 600,
  kilit_bekliyor: false,
  kurulum_tamam: true,
  yukleme_siniri_mb: 20,
};

const KURULU: SetupStatus = {
  ...KURULU_DURUM,
  personnel_count: 37,
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
  okulApiMock.getSchoolConfig.mockResolvedValue(ORNEK_OKUL_KARTI);
  okulApiMock.listSchoolYears.mockResolvedValue([]);
  okulApiMock.listSchoolTerms.mockResolvedValue([]);
  okulApiMock.listHolidays.mockResolvedValue([]);
  const bosSayfa = { count: 0, next: null, previous: null, results: [] };
  okulApiMock.listPersonnel.mockResolvedValue(bosSayfa);
  okulApiMock.getLeavePoolSummary.mockResolvedValue({ personnel_count: 0 });
  oturumApiMock.ozet.mockResolvedValue(ACIK_OTURUM);
  butunlukApiMock.durum.mockRejectedValue(new TypeError("çevrimdışı"));
  butunlukApiMock.parolaBildirimi.mockResolvedValue({ parola_yenilenme: null });
  kullanicilarApiMock.liste.mockResolvedValue([KENDI_HESABI]);
  erisimApiMock.sayfa.mockResolvedValue({
    satirlar: [],
    toplam: 0,
    sayfa: 1,
    sayfa_sayisi: 1,
    sayfa_boyutu: 50,
    turler: [],
    hesaplar: [],
  });
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
    // Bant güncelleme yeteneğinde takılır: önce oturum özeti okunmuş olmalı.
    await within(ustCubuk()).findByText("Program yöneticisi");

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
    expect(screen.getByRole("button", { name: "Doğrula ve indir" })).toBeInTheDocument();
  });

  it("parola yenilenme bildirimi Genel Bakış dışındaki sayfada da pencere olarak çıkar", async () => {
    // Kilit ekranından açılış pencereyi önceki adreste yeniden yükler (tasarım §13 D53):
    // bildirim pano kartı olsaydı sahibi onu göremeyebilirdi (tasarım §4.4.3, tehdit 12).
    butunlukApiMock.parolaBildirimi.mockResolvedValue({
      parola_yenilenme: {
        tur: "SIFIRLAMA",
        zaman: "2026-10-30T16:00:00+03:00",
        girisler: ["2026-11-01T09:05:00+03:00"],
      },
    });
    ekranaBas("/kilavuz");

    const pencere = await screen.findByRole("dialog", { name: "Parola yenilenme bildirimi" });
    expect(
      within(pencere).getByText("Parolanız 30.10.2026 tarihinde sıfırlandı."),
    ).toBeInTheDocument();
    expect(within(pencere).getByText("01.11.2026 09:05 · bu oturum")).toBeInTheDocument();
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

describe("App — kapanış penceresi", () => {
  function kapanisBekliyor() {
    act(() => {
      window.dispatchEvent(new CustomEvent("od:kapanis-bekliyor"));
    });
  }

  it("açık oturumda açılır", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });

    kapanisBekliyor();

    expect(screen.getByRole("dialog", { name: "Program kapanıyor" })).toBeInTheDocument();
  });

  it("kilit ekranında da açılır", async () => {
    const durum = vi.spyOn(guvenlikApi, "durum").mockResolvedValue({
      ...GUVENLIK_OKUNAMADI,
      password_set: true,
      locked: true,
      account_count: 1,
    });
    oturumApiMock.ozet.mockResolvedValue({ ...ACIK_OTURUM, durum: "kilitli", hesap: null });
    oturumApiMock.hesaplar.mockResolvedValue([]);
    oturumApiMock.kurtarmaHesaplari.mockResolvedValue([]);
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Kayıtlar kilitli" });

    kapanisBekliyor();

    expect(screen.getByRole("dialog", { name: "Program kapanıyor" })).toBeInTheDocument();
    durum.mockRestore();
  });

  it("kurulumda da açılır", async () => {
    okulApiMock.getSetupStatus.mockResolvedValue(KURULMAMIS);
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Kurulum Sihirbazı" });

    kapanisBekliyor();

    expect(screen.getByRole("dialog", { name: "Program kapanıyor" })).toBeInTheDocument();
  });

  it("yeniden başlat ekranında da açılır", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    act(() => {
      yenidenBaslatGerekliYayinla();
    });
    expect(screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" })).toBeTruthy();

    kapanisBekliyor();

    expect(screen.getByRole("dialog", { name: "Program kapanıyor" })).toBeInTheDocument();
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
  it("program yöneticisinin gezinmesi Genel Bakış, Birlik Dönemi, Kişiler, Organlar, Temsilciler, Kullanıcılar, Erişim Günlüğü, Ayarlar ve Kılavuz'dur (bu sırayla)", async () => {
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    // Kullanıcılar yeteneğe bağlıdır: özet okunduktan sonra bakılır.
    await within(ustCubuk()).findByText("Program yöneticisi");
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    const baglantilar = within(gezinme).getAllByRole("link");
    const beklenen: Array<[ad: string, yol: string]> = [
      ["Genel Bakış", "/"],
      ["Birlik Dönemi", "/birlik-donemi"],
      ["Kişiler", "/kisiler"],
      ["Organlar", "/organlar"],
      ["Temsilciler", "/temsilciler"],
      ["Kullanıcılar", "/kullanicilar"],
      ["Erişim Günlüğü", "/erisim-gunlugu"],
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
    ["/birlik-donemi", "Birlik Dönemi"],
    ["/birlik-donemi/gecis-kurulumu", "Geçiş Kurulumu"],
    ["/kisiler", "Kişiler"],
    ["/organlar", "Organlar"],
    ["/temsilciler", "Temsilciler"],
    ["/kullanicilar", "Kullanıcılar"],
    ["/erisim-gunlugu", "Erişim Günlüğü"],
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

// Rol süzmesi (plan F1b-2 "Ön yüz"): kaynak oturum özetinin yetenekleridir; ön yüz rol
// matrisini kopyalamaz. Kurulum durumunda süzme yoktur.
describe("App — rol süzmesi", () => {
  /** Başkanın özeti (yetenekler sunucudan gelir gibi: yalnız son oturum onayı). */
  const BASKAN_OTURUMU: OturumOzeti = {
    ...ACIK_OTURUM,
    hesap: {
      id: "h-2",
      tanitici: "baskan",
      rol: "baskan",
      rol_etiketi: "Başkan",
      yetenekler: ["son_oturum_onay"],
    },
  };
  const GUNCELLEME_VAR = {
    current_version: "2026.9.0",
    latest_version: "2026.10.0",
    update_available: true,
    release_name: "",
    published_at: "",
    release_url: "",
    platform: "windows" as const,
    can_download: true,
    installer_name: "kurulum.exe",
    installer_size: 1,
  };

  it("bugünkü yedi ekran her rolün gezinmesinde durur", async () => {
    oturumApiMock.ozet.mockResolvedValue(BASKAN_OTURUMU);
    ekranaBas("/");
    await screen.findByRole("heading", { name: "Genel Bakış" });
    // Özet okunduktan sonra (süzme hazır) bakılır.
    await within(ustCubuk()).findByText("Başkan");
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    expect(
      within(gezinme)
        .getAllByRole("link")
        .map((a) => gorunenMetin(a)),
    ).toEqual([
      "Genel Bakış",
      "Birlik Dönemi",
      "Kişiler",
      "Organlar",
      "Temsilciler",
      "Ayarlar",
      "Kılavuz",
    ]);
  });

  it("Kullanıcılar yeteneği olmayan rolde gezinmede yoktur, adresi “rolünüze açık değil” der", async () => {
    oturumApiMock.ozet.mockResolvedValue(BASKAN_OTURUMU);
    ekranaBas("/kullanicilar");

    expect(await screen.findByText("Bu ekran hesabınızın rolüne açık değil.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Kullanıcılar" })).toBeInTheDocument();
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    expect(within(gezinme).queryByRole("link", { name: "Kullanıcılar" })).toBeNull();
    // Rolün açamadığı uç çağrılmaz; "Yeni hesap" çizilmez.
    expect(kullanicilarApiMock.liste).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Yeni hesap" })).toBeNull();
  });

  it("Erişim Günlüğü Denetleme Kurulunun gezinmesindedir ve açılır; Kullanıcılar yoktur", async () => {
    oturumApiMock.ozet.mockResolvedValue({
      ...ACIK_OTURUM,
      hesap: {
        id: "h-4",
        tanitici: "dk-1",
        rol: "denetleme_kurulu",
        rol_etiketi: "Denetleme Kurulu",
        // Sunucunun türettiği gibi (süzme yalnız yeteneklere bakar).
        yetenekler: ["butunluk_denetim", "erisim_gunlugu", "geri_yukleme_gordum"],
      },
    } satisfies OturumOzeti);
    ekranaBas("/erisim-gunlugu");

    expect(await screen.findByText("Erişim günlüğünde kayıt yok")).toBeInTheDocument();
    expect(erisimApiMock.sayfa).toHaveBeenCalled();
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    expect(
      within(gezinme)
        .getAllByRole("link")
        .map((a) => gorunenMetin(a)),
    ).toEqual([
      "Genel Bakış",
      "Birlik Dönemi",
      "Kişiler",
      "Organlar",
      "Temsilciler",
      "Erişim Günlüğü",
      "Ayarlar",
      "Kılavuz",
    ]);
  });

  it("Erişim Günlüğü yeteneği olmayan rolde gezinmede yoktur, adresi “rolünüze açık değil” der", async () => {
    oturumApiMock.ozet.mockResolvedValue(BASKAN_OTURUMU);
    ekranaBas("/erisim-gunlugu");

    expect(await screen.findByText("Bu ekran hesabınızın rolüne açık değil.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Erişim Günlüğü" })).toBeInTheDocument();
    const gezinme = screen.getByRole("navigation", { name: "Ana gezinme" });
    expect(within(gezinme).queryByRole("link", { name: "Erişim Günlüğü" })).toBeNull();
    // Rolün açamadığı uç çağrılmaz.
    expect(erisimApiMock.sayfa).not.toHaveBeenCalled();
  });

  it("Kullanıcılar program yöneticisinde açılır: liste sunucudan okunur", async () => {
    ekranaBas("/kullanicilar");

    expect(await screen.findByRole("table", { name: "Hesaplar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yeni hesap" })).toBeInTheDocument();
    expect(kullanicilarApiMock.liste).toHaveBeenCalledTimes(1);
  });

  it("güncelleme bandı yalnız güncelleme yeteneğinde çizilir", async () => {
    oturumApiMock.ozet.mockResolvedValue(BASKAN_OTURUMU);
    ekranaBas("/");
    await within(ustCubuk()).findByText("Başkan");

    act(() => denetimSonucunuYayinla(GUNCELLEME_VAR));
    expect(screen.queryByText(/OAB Defteri 2026\.10\.0 hazır\./)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Doğrula ve indir" })).not.toBeInTheDocument();
  });

  it("Kurulum Sihirbazı'nın rotası yeteneği olmayan rolde kendi iletisini verir", async () => {
    oturumApiMock.ozet.mockResolvedValue(BASKAN_OTURUMU);
    ekranaBas("/kurulum");

    // Kullanıcı kararı 04.11.2026: matristeki "O"ya istisna; bilgiler Ayarlar'da salt okur.
    expect(
      await screen.findByText(
        "Kurulum Sihirbazı yalnız kurulumu tamamlayabilen hesaba açıktır; bu bilgiler Ayarlar'da görünür.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Bu ekran hesabınızın rolüne açık değil.")).toBeNull();
    // Sayfanın h1'i üst çubukla aynı kalır (sözlük §4); sihirbazın hiçbir denetimi çizilmez.
    expect(
      screen.getByRole("heading", { level: 1, name: "Kurulum Sihirbazı" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Devam|Hesabı kur|Kurulumu tamamla/ })).toBeNull();
    expect(okulApiMock.getSchoolConfig).not.toHaveBeenCalled();
  });

  it("kurulum durumunda süzme yoktur: sihirbaz hesap yokken açılır", async () => {
    oturumApiMock.ozet.mockResolvedValue({
      ...ACIK_OTURUM,
      durum: "kurulum",
      hesap: null,
      bosta_kalan_sn: null,
      kurulum_tamam: false,
      yukleme_siniri_mb: 20,
    } satisfies OturumOzeti);
    okulApiMock.getSetupStatus.mockResolvedValue({
      ...KURULMAMIS,
      password_set: false,
      missing_steps: ["password", "school", "calendar"],
    });
    ekranaBas("/");

    expect(await screen.findByRole("heading", { name: "Kurulum Sihirbazı" })).toBeInTheDocument();
    expect(screen.queryByText("Bu ekran hesabınızın rolüne açık değil.")).not.toBeInTheDocument();
  });

  it("403 rol_yetkisiz olayı oturum özetini (yetenekleri) yeniden okutur", async () => {
    ekranaBas("/");
    await within(ustCubuk()).findByText("Program yöneticisi");
    const once = oturumApiMock.ozet.mock.calls.length;

    act(() => {
      window.dispatchEvent(new CustomEvent(ROL_YETKISIZ_OLAYI));
    });

    await waitFor(() => expect(oturumApiMock.ozet.mock.calls.length).toBeGreaterThan(once));
    // Olay ileti çizmez: hatayı çağıran ekran gösterir.
    expect(screen.queryByText("Bu işlem hesabınızın rolüne açık değil.")).not.toBeInTheDocument();
  });
});

describe("gezinmeGirdileri", () => {
  const GIRDILER: NavItem[] = [
    { to: "/", label: "Genel Bakış", icon: "space_dashboard" },
    // Yeteneğe bağlı girdi (Kullanıcılar gibi).
    {
      to: "/kullanicilar",
      label: "Kullanıcılar",
      icon: "manage_accounts",
      yetenek: "kullanicilar",
    },
  ];
  const yollar = (y: Parameters<typeof gezinmeGirdileri>[1]) =>
    gezinmeGirdileri(GIRDILER, y).map((g) => g.to);

  it("yeteneğe bağlı girdi yalnız yetenek açıkken görünür; yeteneksiz girdi her zaman", () => {
    expect(yollar(hazirYetki(["kullanicilar"]))).toEqual(["/", "/kullanicilar"]);
    expect(yollar(hazirYetki(["erisim_gunlugu"]))).toEqual(["/"]);
  });

  it("özet yüklenirken ve okunamadıysa görünmez; kurulumda süzme yok", () => {
    expect(yollar(YUKLENIYOR)).toEqual(["/"]);
    expect(yollar(OKUNAMADI)).toEqual(["/"]);
    expect(yollar(KURULUM)).toEqual(["/", "/kullanicilar"]);
  });
});
