// Genel Bakış: gezinme kartları, son oturum kartı, ayrılış havuzu kartı ve
// "Başlangıç Yol Haritası" (kurulumdan sonra; işaretler backend'de saklanır,
// bütün maddeler tamamlanınca kart gizlenebilir). Aile iskeletinin kütüphane
// kartları F1a-2'de söküldü.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { KURULU_DURUM } from "../../test/kurulumDurumu";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { RoadmapState, SetupStatus } from "../okul/api";

const oapi = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  markRoadmapItem: vi.fn(),
  setRoadmapHidden: vi.fn(),
  getLeavePoolSummary: vi.fn(),
}));
const papi = vi.hoisted(() => ({ sonOturum: vi.fn(), kontrolEttim: vi.fn() }));

vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: oapi,
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  panelApi: papi,
}));

import PanelPage from "./PanelPage";

/** Bütün maddeler tamam: aktarımlar yapılmış, kapalı gün girilmiş, zarf işareti konmuş. */
const HEPSI_TAMAM: SetupStatus = {
  ...KURULU_DURUM,
  student_count: 480,
  personnel_count: 36,
  school_break_count: 2,
  roadmap: {
    marks: {
      kurtarma_zarfi: "2026-09-22",
    },
    hidden: false,
  },
};

function bas() {
  return render(
    <MemoryRouter>
      <SnackbarProvider>
        <PanelPage />
      </SnackbarProvider>
    </MemoryRouter>,
  );
}

function yolHaritasi(): HTMLElement {
  return screen.getByRole("region", { name: "Başlangıç Yol Haritası" });
}

beforeEach(() => {
  oapi.getSetupStatus.mockResolvedValue(KURULU_DURUM);
  oapi.getLeavePoolSummary.mockResolvedValue({ student_count: 0, personnel_count: 0 });
  papi.sonOturum.mockResolvedValue({
    unexpected_shutdown: false,
    process_started_at: "2026-10-31T09:00:00+03:00",
  });
});

afterEach(() => vi.clearAllMocks());

describe("Genel Bakış", () => {
  it("sayfanın tek adı Genel Bakış'tır; gezinme kartları sayfalarına gider", async () => {
    bas();
    await screen.findByRole("heading", { name: "Başlangıç Yol Haritası" });

    expect(screen.getByRole("heading", { level: 1, name: "Genel Bakış" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Öğretmen ve diğer personel sicili/ })).toHaveAttribute(
      "href",
      "/kisiler",
    );
    expect(
      screen.getByRole("link", { name: /Ders yılı, şubeler, okul bilgileri/ }),
    ).toHaveAttribute("href", "/ayarlar");
  });

  it("kütüphane kartları ve bağlantıları sökülmüştür", async () => {
    bas();
    await screen.findByRole("heading", { name: "Başlangıç Yol Haritası" });

    for (const baslik of ["Katalog Excel Şablonu", "Raporlar", "Sayım", "Gecikmiş Ödünçler"]) {
      expect(screen.queryByRole("heading", { name: baslik })).toBeNull();
    }
    const hedefler = screen.getAllByRole("link").map((a) => a.getAttribute("href"));
    for (const yol of ["/raporlar", "/ilisik-listesi", "/katalog"]) {
      expect(hedefler).not.toContain(yol);
    }
  });

  it("önceki oturum düzgün kapanmadıysa son oturum kartı görünür", async () => {
    papi.sonOturum.mockResolvedValue({
      unexpected_shutdown: true,
      process_started_at: "2026-10-31T09:00:00+03:00",
    });
    bas();

    expect(
      await screen.findByRole("heading", { name: "Son Oturumu Kontrol Edin" }),
    ).toBeInTheDocument();
  });

  it("ayrılış havuzu boş değilse “N kişi ayrılış kararı bekliyor” kartı havuza bağlanır", async () => {
    oapi.getLeavePoolSummary.mockResolvedValue({ student_count: 3, personnel_count: 1 });
    bas();

    const kart = await screen.findByRole("region", { name: "Ayrılış Havuzu" });
    expect(
      within(kart).getByText(
        "4 kişi ayrılış kararı bekliyor (3 öğrenci, 1 öğretmen ve diğer personel).",
      ),
    ).toBeInTheDocument();
    expect(within(kart).getByRole("link", { name: "Ayrılış Havuzu'nu aç" })).toHaveAttribute(
      "href",
      "/kisiler?tab=havuz",
    );
  });

  it("ayrılış havuzu boşsa ya da sayı okunamazsa kart görünmez", async () => {
    const { unmount } = bas();
    await waitFor(() => expect(oapi.getLeavePoolSummary).toHaveBeenCalled());
    expect(screen.queryByRole("region", { name: "Ayrılış Havuzu" })).toBeNull();
    unmount();

    oapi.getLeavePoolSummary.mockRejectedValueOnce(new Error("görevli kipi"));
    bas();
    await waitFor(() => expect(oapi.getLeavePoolSummary).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("region", { name: "Ayrılış Havuzu" })).toBeNull();
  });
});

describe("Başlangıç Yol Haritası", () => {
  it("yeni kurulumda dört madde yapılacak olarak görünür, ilerleme 0/4", async () => {
    bas();

    expect(
      await screen.findByRole("heading", { name: "Başlangıç Yol Haritası" }),
    ).toBeInTheDocument();
    const kart = yolHaritasi();
    expect(within(kart).getAllByRole("listitem")).toHaveLength(4);
    expect(within(kart).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
    expect(within(kart).getByText(/4 maddeden 0 tanesi tamamlandı/)).toBeInTheDocument();
    expect(within(kart).queryByRole("button", { name: "Kartı gizle" })).toBeNull();
  });

  it("gizlenmiş kart görünmez; durum okunamazsa da sayfa çalışır", async () => {
    oapi.getSetupStatus.mockResolvedValueOnce({
      ...KURULU_DURUM,
      roadmap: { marks: {}, hidden: true },
    });
    const { unmount } = bas();
    await waitFor(() => expect(oapi.getSetupStatus).toHaveBeenCalled());
    expect(screen.queryByRole("heading", { name: "Başlangıç Yol Haritası" })).toBeNull();
    unmount();

    oapi.getSetupStatus.mockRejectedValueOnce(new Error("ağ yok"));
    bas();
    await waitFor(() => expect(oapi.getSetupStatus).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("heading", { name: "Başlangıç Yol Haritası" })).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: "Genel Bakış" })).toBeInTheDocument();
  });

  it("elle işaretlenen madde backend'e yazılır ve tarihiyle görünür", async () => {
    const user = userEvent.setup();
    const yeni: RoadmapState = { marks: { kurtarma_zarfi: "2026-09-22" }, hidden: false };
    oapi.markRoadmapItem.mockResolvedValue(yeni);
    bas();

    const kutu = await screen.findByRole("checkbox", {
      name: /Kurtarma anahtarını müdürlükte kapalı zarfta saklayın — yapıldı/,
    });
    await user.click(kutu);

    expect(oapi.markRoadmapItem).toHaveBeenCalledWith("kurtarma_zarfi", true);
    await waitFor(() => expect(kutu).toBeChecked());
    expect(within(yolHaritasi()).getByText("· 22.09.2026")).toBeInTheDocument();
    expect(within(yolHaritasi()).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "1");
  });

  it("işaret kaydedilemezse hata bildirilir, kutu işaretlenmez", async () => {
    const user = userEvent.setup();
    oapi.markRoadmapItem.mockRejectedValue(
      new ApiError(403, "kip_yetkisiz", "Bu işlem görevli kipinde yapılamaz.", {}),
    );
    bas();

    const kutu = await screen.findByRole("checkbox", {
      name: /Kurtarma anahtarını müdürlükte kapalı zarfta saklayın — yapıldı/,
    });
    await user.click(kutu);

    expect(await screen.findByText("Bu işlem görevli kipinde yapılamaz.")).toBeInTheDocument();
    expect(kutu).not.toBeChecked();
  });

  it("bütün maddeler tamamsa kart gizlenebilir", async () => {
    const user = userEvent.setup();
    oapi.getSetupStatus.mockResolvedValue(HEPSI_TAMAM);
    oapi.setRoadmapHidden.mockResolvedValue({ ...HEPSI_TAMAM.roadmap, hidden: true });
    bas();

    expect(await screen.findByText("Bütün maddeler tamamlandı.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Kartı gizle" }));

    expect(oapi.setRoadmapHidden).toHaveBeenCalledWith(true);
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Başlangıç Yol Haritası" })).toBeNull(),
    );
  });
});
