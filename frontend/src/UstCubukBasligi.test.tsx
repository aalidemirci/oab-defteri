// Üst çubuk başlığı = ekranın h1'i (docs/sozluk.md §4). Adrese bağlı sayfalar
// için bu `App.test.tsx`'te sabitlenmiştir; burada PROGRAM DURUMU ekranları
// (sözlük §4.2) sınanır: kilitli, güvenlik dosyası kayıp ve yedekten geri
// yükleme sonrası "yeniden başlatın" örtüsü. Bu ekranlar bir rotaya bağlı
// olmadığı için başlığı `ui/DurumBasligi` üzerinden kabuğa kendileri bildirir.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GuvenlikDurumu } from "./modules/guvenlik/api";
import { ConfirmProvider } from "./ui/ConfirmProvider";
import { SnackbarProvider } from "./ui/SnackbarProvider";
import { KURULU_DURUM } from "./test/kurulumDurumu";

const guvenlikApiMock = vi.hoisted(() => ({
  durum: vi.fn(),
  yedekler: vi.fn(),
}));

vi.mock("./modules/guvenlik/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./modules/guvenlik/api")>();
  return { ...actual, guvenlikApi: { ...actual.guvenlikApi, ...guvenlikApiMock } };
});

const okulApiMock = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getLeavePoolSummary: vi.fn(),
  markRoadmapItem: vi.fn(),
  setRoadmapHidden: vi.fn(),
}));

vi.mock("./modules/okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./modules/okul/api")>();
  return { ...actual, okulApi: { ...actual.okulApi, ...okulApiMock } };
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

import App from "./App";
import { KILIT_EKRANI_BASLIGI } from "./modules/guvenlik/KilitEkrani";
import { YENIDEN_BASLAT_BASLIGI } from "./modules/guvenlik/YenidenBaslatEkrani";
import { DOSYA_KAYIP_BASLIGI } from "./modules/guvenlik/metinler";
import { yenidenBaslatGerekliYayinla } from "./lib/restart";

const ACIK: GuvenlikDurumu = {
  password_set: true,
  locked: false,
  security_file_missing: false,
  reset_available: false,
  transition_pending: false,
  transition: "",
  recovery_key_confirmed: true,
  protected_fields: [],
  account_count: 1,
  recovery_key_no: 1,
  recovery_key_date: "2026-11-01",
  corrupt_field_count: 0,
};

function ekranaBas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/"]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <App />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/** Kabuğun üst çubuğu — DOM'daki ilk `banner` (App.test.tsx ile aynı kalıp). */
function ustCubuk(): HTMLElement {
  return screen.getAllByRole("banner")[0];
}

beforeEach(() => {
  vi.clearAllMocks();
  guvenlikApiMock.durum.mockResolvedValue(ACIK);
  guvenlikApiMock.yedekler.mockResolvedValue({ backup_dir: "", backups: [] });
  okulApiMock.getSetupStatus.mockResolvedValue(KURULU_DURUM);
  okulApiMock.getLeavePoolSummary.mockResolvedValue({ student_count: 0, personnel_count: 0 });
  oturumApiMock.ozet.mockResolvedValue({
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
  });
  oturumApiMock.hesaplar.mockResolvedValue([
    {
      id: "h-1",
      tanitici: "yonetici",
      rol: "yonetici",
      rol_etiketi: "Program yöneticisi",
      secilebilir: true,
      askida_nedeni: null,
    },
  ]);
});

describe("Üst çubuk başlığı — program durumu ekranları", () => {
  it("kilitliyken ekranın h1'i ve üst çubuk aynı başlığı gösterir", async () => {
    guvenlikApiMock.durum.mockResolvedValue({ ...ACIK, locked: true });
    oturumApiMock.ozet.mockResolvedValue({
      durum: "kilitli",
      hesap: null,
      bosta_dk: 10,
      bosta_kalan_sn: null,
      kilit_bekliyor: false,
      kurulum_tamam: true,
      yukleme_siniri_mb: 20,
    });
    ekranaBas();

    expect(
      await screen.findByRole("heading", { level: 1, name: KILIT_EKRANI_BASLIGI }),
    ).toBeInTheDocument();
    // Başlığı ekran MOUNT sonrası bildirir (etki); üst çubuk bir sonraki
    // çizimde yetişir — bu yüzden `findByText`.
    expect(await within(ustCubuk()).findByText(KILIT_EKRANI_BASLIGI)).toBeInTheDocument();
    expect(within(ustCubuk()).queryByText("Genel Bakış")).not.toBeInTheDocument();
    // Kilitliyken oturum göstergesi yoktur (kimse açık değil); Çık vardır ve parolasızdır.
    expect(within(ustCubuk()).queryByRole("group", { name: "Oturum" })).not.toBeInTheDocument();
    await userEvent.setup().click(within(ustCubuk()).getByRole("button", { name: "Çık" }));
    const diyalog = screen.getByRole("dialog", { name: "Programdan çıkılsın mı?" });
    expect(within(diyalog).queryByLabelText(/parola/i)).toBeNull();
  });

  it("güvenlik dosyası kayıpken ekranın h1'i ve üst çubuk aynı başlığı gösterir", async () => {
    guvenlikApiMock.durum.mockResolvedValue({ ...ACIK, security_file_missing: true });
    ekranaBas();

    expect(
      await screen.findByRole("heading", { level: 1, name: DOSYA_KAYIP_BASLIGI }),
    ).toBeInTheDocument();
    expect(await within(ustCubuk()).findByText(DOSYA_KAYIP_BASLIGI)).toBeInTheDocument();
  });

  it("yeniden başlat örtüsü açılınca üst çubuk onun başlığını gösterir", async () => {
    ekranaBas();
    expect(
      await screen.findByRole("heading", { level: 1, name: "Genel Bakış" }),
    ).toBeInTheDocument();
    expect(within(ustCubuk()).getByText("Genel Bakış")).toBeInTheDocument();

    act(() => yenidenBaslatGerekliYayinla());

    const ortu = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ortu).toHaveTextContent(YENIDEN_BASLAT_BASLIGI);
    expect(within(ustCubuk()).getByText(YENIDEN_BASLAT_BASLIGI)).toBeInTheDocument();
    expect(within(ustCubuk()).queryByText("Genel Bakış")).not.toBeInTheDocument();
  });

  // Gerçek pencere sınaması (07.11.2026): en uzun başlık "Programı kapatıp yenid…" diye kesiliyordu;
  // geniş pencerede de, çünkü başlığın kutusu `lg:w-48` ile 12rem'e sabitti. Kutu kalan yeri alır,
  // yer gerçekten yetmezse `truncate` kısaltır.
  it("başlık kutusu sabit genişlikte değildir, üst çubukta kalan yerin tamamını alır", async () => {
    ekranaBas();
    await screen.findByRole("heading", { level: 1, name: "Genel Bakış" });

    act(() => yenidenBaslatGerekliYayinla());

    const baslik = within(ustCubuk()).getByText(YENIDEN_BASLAT_BASLIGI);
    expect(baslik).toHaveClass("truncate");
    const kutu = baslik.parentElement as HTMLElement;
    expect(kutu).toHaveClass("min-w-0", "flex-1");
    expect(kutu.className).not.toMatch(/(^|[\s:])w-\d/);
  });
});
