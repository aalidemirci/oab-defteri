// Genel Bakış → Yıllık İş Takvimi (plan F2 §6.1 M9): sekme adresi (`?tab=takvim`), yıl görünümü ay ay,
// ay görünümü, günü göreli satırlar ayrı listede, madde atfı (kural kimliği yüzeye çıkmaz), basım
// uyarıları, birlik dönemi yokken boş durum ve E14'ün kartı (üretim yalnız `yillik_is_takvimi_uretme`'de
// ve açık dönemde; basım her rolde). Veriler UYDURMADIR.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { DUGME_OLUSTUR } from "../evrak/metinler";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { YillikTakvim } from "./api";

const panelMock = vi.hoisted(() => ({ yillikTakvim: vi.fn() }));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  panelApi: panelMock,
}));
const donemMock = vi.hoisted(() => ({ donemler: vi.fn() }));
vi.mock("../birlik-donemi/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../birlik-donemi/api")>()),
  birlikDonemiApi: donemMock,
}));
const evrakMock = vi.hoisted(() => ({ liste: vi.fn(), uret: vi.fn(), dosya: vi.fn() }));
vi.mock("../evrak/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../evrak/api")>()),
  evrakApi: evrakMock,
}));

import YillikIsTakvimi, { ilkGun } from "./YillikIsTakvimi";
import {
  ALAN_TAKVIM_DONEMI,
  TAKVIM_AY_BOS,
  TAKVIM_DONEM_YOK,
  TAKVIM_OKUNAMADI,
  TAKVIM_UYARILARI,
  TARIHSIZ_ISLER,
} from "./metinler";

const DONEM: BirlikDonemi = {
  id: 3,
  name: "2026-2027 birlik dönemi",
  school_year: 1,
  start_date: "2026-10-20",
  end_date: null,
  status: "ACIK",
  program_start_date: "2026-10-20",
  opened_by_assembly: 5,
  transition_completed_on: null,
  kural_paketi: { paket: "OAB-2023.12", rev: 2 },
  kural_kopyasi_tutuyor: true,
};

const TAKVIM: YillikTakvim = {
  donem: 3,
  bolumler: ["A. Süre kuralları", "B. Okul planı"],
  kural_satirlari: [
    {
      tarih: "27.10.2026",
      is: "Yönetim kurulunun görev bölümü",
      kural: "yonetim_kurulu.gorev_bolumu_gun",
      atif: "md. 12/3",
    },
    {
      tarih: "toplantı gününden en az 15 gün önce",
      is: "Olağan genel kurulun yeri, zamanı ve gündeminin bildirilmesi ve duyurulması",
      kural: "genel_kurul.ilan_en_az_gun",
      atif: "md. 9/3",
    },
  ],
  plan_satirlari: [
    { tarih: "07.09.2026", is: "Ders yılının başlangıcı", kaynak: "Ders yılı (Ayarlar)" },
    {
      tarih: "………",
      is: "Yönetim kurulunun aylık toplantısı (md. 13/3)",
      kaynak: "Birlik döneminin ayarı",
    },
  ],
  uyarilar: ["Yönetim kurulunun aylık toplantı günü girilmedi; satır ……… basıldı."],
};

function bas(yetenekler: string[] = ["yillik_is_takvimi_uretme"]) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <YillikIsTakvimi />
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  donemMock.donemler.mockResolvedValue([DONEM]);
  panelMock.yillikTakvim.mockResolvedValue(TAKVIM);
  evrakMock.liste.mockResolvedValue([]);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Yıllık İş Takvimi", () => {
  it("tarih metninin ilk günü; göreli ve boş tarih gün değildir", () => {
    expect(ilkGun("20.10.2026")).toEqual({ yil: 2026, ay: 9, gun: 20 });
    expect(ilkGun("01.09.2026 – 30.01.2027")).toEqual({ yil: 2026, ay: 8, gun: 1 });
    expect(ilkGun("toplantı gününden en az 15 gün önce")).toBeNull();
    expect(ilkGun("………")).toBeNull();
  });

  it("yıl görünümü ay ay; göreli satırlar ayrı; atıf görünür, kural kimliği görünmez", async () => {
    bas();
    const eylul = await screen.findByRole("list", { name: "Eylül 2026" });
    expect(eylul).toHaveTextContent("Ders yılının başlangıcı");
    const ekim = screen.getByRole("list", { name: "Ekim 2026" });
    expect(ekim).toHaveTextContent("Yönetim kurulunun görev bölümü");
    expect(ekim).toHaveTextContent("Dayanak: md. 12/3");
    const goreli = screen.getByRole("list", { name: TARIHSIZ_ISLER });
    expect(goreli).toHaveTextContent("en az 15 gün önce");
    expect(goreli).toHaveTextContent("Kaynak: Birlik döneminin ayarı");
    expect(screen.queryByText(/gorev_bolumu_gun/)).toBeNull();
    expect(screen.getByText(TAKVIM_UYARILARI)).toBeInTheDocument();
    expect(panelMock.yillikTakvim).toHaveBeenCalledWith(3);
  });

  it("ay görünümü seçilen ayın işlerini gösterir", async () => {
    const user = userEvent.setup();
    bas();
    await screen.findByRole("list", { name: "Eylül 2026" });
    await user.selectOptions(screen.getByLabelText("Görünüm"), "AY");
    await user.selectOptions(screen.getByLabelText("Ay"), "2026-10");
    const liste = screen.getByRole("list", { name: "Ekim 2026" });
    expect(within(liste).getByText("Yönetim kurulunun görev bölümü")).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Eylül 2026" })).toBeNull();
  });

  it("E14'ü yalnız üretebilen rol açık dönemde oluşturur; okuyan rolde düğme yok", async () => {
    const { unmount } = bas();
    expect(await screen.findByRole("button", { name: DUGME_OLUSTUR })).toBeInTheDocument();
    expect(evrakMock.liste).toHaveBeenCalledWith(3);
    unmount();
    bas(["son_oturum_onay"]);
    expect(await screen.findByText("Yıllık iş takvimi")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
  });

  it("hazırlıktaki dönemde takvim okunur ama E14 yazılmaz", async () => {
    donemMock.donemler.mockResolvedValue([{ ...DONEM, status: "HAZIRLIK" }]);
    bas();
    expect(await screen.findByRole("list", { name: "Ekim 2026" })).toBeInTheDocument();
    expect(await screen.findByText("Yıllık iş takvimi")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
  });

  it("ay görünümünde dönem değişince seçilen ay yeni dönemin ilk ayına düşer", async () => {
    const user = userEvent.setup();
    const eski: BirlikDonemi = {
      ...DONEM,
      id: 2,
      name: "2025-2026 birlik dönemi",
      start_date: "2025-10-21",
      end_date: "2026-10-19",
      status: "KAPANDI",
    };
    donemMock.donemler.mockResolvedValue([eski, DONEM]);
    panelMock.yillikTakvim.mockImplementation((id: number) =>
      Promise.resolve(
        id === 2
          ? {
              ...TAKVIM,
              donem: 2,
              kural_satirlari: [],
              plan_satirlari: [
                { tarih: "17.11.2025", is: "Eski dönemin işi", kaynak: "Ders yılı (Ayarlar)" },
              ],
              uyarilar: [],
            }
          : TAKVIM,
      ),
    );
    bas();
    await screen.findByRole("list", { name: "Eylül 2026" });
    await user.selectOptions(screen.getByLabelText("Görünüm"), "AY");
    await user.selectOptions(screen.getByLabelText("Ay"), "2026-10");
    await user.selectOptions(screen.getByLabelText(ALAN_TAKVIM_DONEMI), "2");
    const liste = await screen.findByRole("list", { name: "Kasım 2025" });
    expect(within(liste).getByText("Eski dönemin işi")).toBeInTheDocument();
    expect(screen.queryByText(TAKVIM_AY_BOS)).toBeNull();
    expect(screen.getByLabelText("Ay")).toHaveValue("2025-11");
  });

  it("takvim okunamazsa hata bandı", async () => {
    panelMock.yillikTakvim.mockRejectedValue(new Error("ağ"));
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(TAKVIM_OKUNAMADI);
  });

  it("birlik dönemi yoksa boş durum", async () => {
    donemMock.donemler.mockResolvedValue([]);
    bas();
    expect(await screen.findByText(TAKVIM_DONEM_YOK)).toBeInTheDocument();
    expect(panelMock.yillikTakvim).not.toHaveBeenCalled();
  });
});
