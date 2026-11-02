// Genel Bakış: gezinme kartları, son oturum kartı, ayrılış havuzu kartı, denetim izi
// kartları (tasarım §4.6.3: bütünlük uyarıları ve "Son Girişler") ve "Başlangıç Yol
// Haritası" (kurulumdan sonra; işaretler backend'de saklanır, bütün maddeler
// tamamlanınca kart gizlenebilir). Aile iskeletinin kütüphane kartları F1a-2'de söküldü.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { KURULU_DURUM } from "../../test/kurulumDurumu";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { ButunlukDurumu } from "../butunluk/api";
import type { RoadmapState, SetupStatus } from "../okul/api";

const oapi = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  markRoadmapItem: vi.fn(),
  setRoadmapHidden: vi.fn(),
  getLeavePoolSummary: vi.fn(),
}));
const papi = vi.hoisted(() => ({ sonOturum: vi.fn(), kontrolEttim: vi.fn() }));
// Güvenlik durumu (okunamayan alan kartı) ve dış yedek hatırlatması kendi uçlarından okur.
const gapi = vi.hoisted(() => ({ durum: vi.fn(), disYedek: vi.fn() }));
// Denetim izi kartları tek `GET security/integrity/` okumasından beslenir.
const bapi = vi.hoisted(() => ({ durum: vi.fn(), sahipsizSarmallariSil: vi.fn() }));

vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: oapi,
}));
vi.mock("../guvenlik/api", () => ({ guvenlikApi: gapi }));
vi.mock("../butunluk/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../butunluk/api")>()),
  butunlukApi: bapi,
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

/** Bulgusuz denetim izi: yalnız "Son Girişler" kartı görünür. */
const TEMIZ_IZ: ButunlukDurumu = {
  butunluk: [],
  geri_yukleme: null,
  iki_depo: {
    fark_var: false,
    sarmalsiz_hesaplar: [],
    silinebilir_sarmallar: [],
    muhru_tutmayan: [],
  },
  kagit_capasi: { kayit_no: 57, zincir: "A1B2-C3D4" },
  son_girisler: ["2026-11-01T08:00:00+03:00"],
  parola_yenilenme: null,
  okunamayan: [],
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
  gapi.durum.mockResolvedValue({ corrupt_field_count: 0 });
  gapi.disYedek.mockResolvedValue({ remind: false });
  bapi.durum.mockResolvedValue(TEMIZ_IZ);
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

  it("çözülemeyen şifreli alan varsa “Okunamayan Kayıt Alanları” kartı çıkar (yalnız sayı)", async () => {
    gapi.durum.mockResolvedValue({ corrupt_field_count: 2 });
    bas();

    expect(
      await screen.findByRole("heading", { name: "Okunamayan Kayıt Alanları" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 şifreli alan okunamadı/)).toBeInTheDocument();
  });

  it("“Son Girişler” kartı oturumdaki hesabın girişini ve denetim izinin son kaydını verir", async () => {
    bas();

    const kart = await screen.findByRole("region", { name: "Son Girişler" });
    expect(within(kart).getByText("01.11.2026 08:00 · bu oturum")).toBeInTheDocument();
    expect(within(kart).getByText("Kayıt no: 57 · Zincir: A1B2-C3D4")).toBeInTheDocument();
    // Bulgu yoksa uyarı kartları çizilmez.
    expect(screen.queryByRole("region", { name: "Denetim İzi Bütünlüğü" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Yedekten Geri Yükleme Yapıldı" })).toBeNull();
    expect(bapi.durum).toHaveBeenCalledTimes(1);
  });

  it("kilit açılışındaki denetimin bulgusu ve geri yükleme kartı Son Girişler'den önce gelir", async () => {
    bapi.durum.mockResolvedValue({
      ...TEMIZ_IZ,
      butunluk: [
        {
          seq: 50,
          zaman: "2026-11-01T08:00:00+03:00",
          tur: "dogrulama",
          duzey: "uyari",
          bulgular: ["kuyruk_kesik"],
          hesap: null,
        },
      ],
      geri_yukleme: {
        seq: 40,
        zaman: "2026-10-31T09:00:00+03:00",
        geri_yukleme_ani: null,
        hesap: null,
        yol: "kurtarma",
        yol_hesap: null,
        oturum_hesap: null,
        kurtarma_no: 2,
        yedek: null,
        onceki_dosya: null,
        onceki_sha256: null,
        onceki_kayit_no: null,
        onceki_zincir: null,
        ayrintisiz: false,
        onceki_geri_yuklemeler: [],
      },
    } satisfies ButunlukDurumu);
    bas();

    const uyari = await screen.findByRole("region", { name: "Denetim İzi Bütünlüğü" });
    expect(within(uyari).getByText(/geri sarılmış/)).toBeInTheDocument();
    const basliklar = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(basliklar.indexOf("Denetim İzi Bütünlüğü")).toBeLessThan(
      basliklar.indexOf("Son Girişler"),
    );
    expect(basliklar).toContain("Yedekten Geri Yükleme Yapıldı");
  });

  it("denetim izi okunamazsa kartları görünmez, sayfanın geri kalanı çalışır", async () => {
    bapi.durum.mockRejectedValue(new ApiError(423, "locked", "Kayıtlar kilitli."));
    bas();

    await screen.findByRole("heading", { name: "Başlangıç Yol Haritası" });
    await waitFor(() => expect(bapi.durum).toHaveBeenCalled());
    expect(screen.queryByRole("region", { name: "Son Girişler" })).toBeNull();
    // Kilitliyken uyarı kartı da çizilmez: kilit ekranı gelir.
    expect(screen.queryByRole("region", { name: "Bütünlük Durumu Okunamadı" })).toBeNull();
  });

  it("denetim izi beklenmedik biçimde okunamazsa uyarı kartı çıkar (kartlar sessizce kaybolmaz)", async () => {
    // Bağımsız denetim bulgusu: program dışından eklenen biçimsiz bir satır ucu 500'e
    // düşürüyordu; ön yüz hatayı yutuyor, bütün uyarı kartları sessizce kayboluyordu.
    bapi.durum.mockRejectedValue(new ApiError(500, "500", "Beklenmeyen bir hata oluştu."));
    bas();

    const kart = await screen.findByRole("region", { name: "Bütünlük Durumu Okunamadı" });
    expect(within(kart).getByText(/kartları tam okunamadı/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Genel Bakış" })).toBeInTheDocument();
  });

  it("Son Girişler okunamadıysa kart “henüz giriş yapılmadı” demez, okunamadı der", async () => {
    // Bağımsız denetim bulgusu: backend okunamayan kartı boş listeyle doldurup adını
    // `okunamayan`'a yazar; Genel Bakış bunu "Bu hesapla henüz kilit ekranından giriş
    // yapılmadı." diye yazıyordu (gerçek girişler ve tanımadığınız giriş öğüdü kayboluyordu).
    bapi.durum.mockResolvedValue({
      ...TEMIZ_IZ,
      son_girisler: [],
      kagit_capasi: null,
      okunamayan: ["son_girisler", "kagit_capasi"],
    } satisfies ButunlukDurumu);
    bas();

    const kart = await screen.findByRole("region", { name: "Son Girişler" });
    expect(within(kart).getByText(/Son girişler okunamadı/)).toBeInTheDocument();
    expect(within(kart).queryByText(/henüz kilit ekranından giriş/)).toBeNull();
    expect(within(kart).getByText("Denetim izinin son kaydı okunamadı.")).toBeInTheDocument();
    const uyari = screen.getByRole("region", { name: "Bütünlük Durumu Okunamadı" });
    expect(within(uyari).getByText(/bir uyarı ya da giriş gösterilemiyor/)).toBeInTheDocument();
  });

  it("çözülemeyen alan yoksa kart görünmez", async () => {
    bas();
    await screen.findByRole("heading", { name: "Başlangıç Yol Haritası" });
    await waitFor(() => expect(gapi.durum).toHaveBeenCalled());
    expect(screen.queryByRole("heading", { name: "Okunamayan Kayıt Alanları" })).toBeNull();
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

    oapi.getLeavePoolSummary.mockRejectedValueOnce(new Error("bağlantı koptu"));
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
      new ApiError(500, "error", "İşaret kaydedilemedi; yeniden deneyin.", {}),
    );
    bas();

    const kutu = await screen.findByRole("checkbox", {
      name: /Kurtarma anahtarını müdürlükte kapalı zarfta saklayın — yapıldı/,
    });
    await user.click(kutu);

    expect(await screen.findByText("İşaret kaydedilemedi; yeniden deneyin.")).toBeInTheDocument();
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
