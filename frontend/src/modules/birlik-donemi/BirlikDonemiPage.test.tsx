// Birlik Dönemi ekranı (plan F1c-11): dönem yokken boş durum ve (program yöneticisinde) geçiş
// kurulumuna bağlantı; dönemin bilgileri ve SALT OKUNUR kural sürümü; D7 bandı (kural kopyası
// doğrulanamadı) ve kapanmış dönem notu; görev süresi uyarıları atfıyla; geçiş döneminin iptali yalnız
// `birlik_donemi_yazma`'da, gerekçe zorunlu, D7 dönemde yok; salt okur rolde not ve düğme yok, boş durumda
// öğüt cümlesi yok. F2 11b: yeni açılan okulda boş durum genel kurula götürür; hazırlık döneminin açılış
// satırı ve genel kurul bağlantısı (U3); kural sürümü güncellemesi (tasarım §6.2-5) yalnız
// `kural_surumu_guncelleme`'de, fark listeleri, etkilenen kayıtların onayı, geri alma. Veriler uydurmadır.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { YETENEK_ADLARI } from "../oturum/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { BirlikDonemi, GecisOzeti } from "./api";

const apiMock = vi.hoisted(() => ({
  donemler: vi.fn(),
  donem: vi.fn(),
  ilkDonemiAc: vi.fn(),
  donemiIptalEt: vi.fn(),
  gecis: vi.fn(),
  kuralSurumu: vi.fn(),
  kuralSurumunuGecir: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  birlikDonemiApi: apiMock,
}));

const okulApiMock = vi.hoisted(() => ({ listSchoolYears: vi.fn(), getSchoolConfig: vi.fn() }));
vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: okulApiMock,
}));

import BirlikDonemiPage from "./BirlikDonemiPage";
import {
  ACILIS_HAZIRLIK,
  DONEM_YOK_YENI_OKUL_ACIKLAMASI,
  DUGME_GENEL_KURULU_AC,
  DUGME_GENEL_KURULU_PLANLA,
  DUGME_GERI_AL,
  DUGME_SURUMU_GUNCELLE,
  ETKILENEN_ONAYI,
  ETKILENEN_ONAYI_GEREKLI,
  FARK_DEGER,
  FARK_EKLENEN,
  KURAL_GUNCEL,
  KURAL_GUNCELLEME_BASLIGI,
  KURAL_GUNCELLEME_OKUNAMADI,
  SURUM_GUNCELLENDI,
  DONEM_IPTAL_BASLIGI,
  DONEM_KAPANDI_NOTU,
  DONEM_YOK_ACIKLAMASI,
  DONEM_YOK_BASLIGI,
  DUGME_DONEMI_IPTAL,
  DUGME_GECISI_AC,
  KURAL_KOPYASI_BOZUK,
} from "./metinler";

const DONEM: BirlikDonemi = {
  id: 3,
  name: "2026-2027 birlik dönemi",
  school_year: 1,
  start_date: "2026-10-10",
  end_date: null,
  status: "ACIK",
  program_start_date: "2026-11-11",
  opened_by_assembly: null,
  transition_completed_on: null,
  kural_paketi: { paket: "OAB-2023.12", rev: 1 },
  kural_kopyasi_tutuyor: true,
};

const GECIS: GecisOzeti = {
  state: "SURUYOR",
  open_steps: ["kurul", "karar_defteri", "tamamla"],
  donem: DONEM,
  karar_defteri: null,
  gorev_suresi_uyarilari: [],
  uyum_satirlari: [],
};

const R1 = { paket: "OAB-2023.12", rev: 1 };
const R2 = { paket: "OAB-2023.12", rev: 2 };
const GUNCEL_SURUM = {
  donem: 3,
  bagli: R1,
  en_yeni: R1,
  hedefler: [],
  gecilebilir: true,
  hedef: R1,
  fark: null,
};
const FARK = {
  eski: R1,
  yeni: R2,
  eklenen: [
    {
      id: "genel_kurul.ilan_en_az_gun",
      aciklama: "Genel kurulun ilanı en az on beş gün önce yapılır.",
      atif: "md. 9/3",
    },
  ],
  cikarilan: [],
  biten: [],
  deger_degisen: [
    { id: "genel_kurul.olagan_son_ay", aciklama: "Olağan genel kurulun son ayı.", atif: "md. 9/1" },
  ],
  duzeltilen: [],
  kayitlar: [
    { model: "oab.GeneralAssembly", kayit_id: "7", kural_id: "genel_kurul.olagan_son_ay" },
  ],
  onay_gerekli: true,
};

function bas(yetenekler: readonly string[] = YETENEK_ADLARI) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <BirlikDonemiPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  apiMock.donemler.mockResolvedValue([DONEM]);
  apiMock.gecis.mockResolvedValue(GECIS);
  okulApiMock.getSchoolConfig.mockResolvedValue({ opened_on: null });
  apiMock.kuralSurumu.mockResolvedValue(GUNCEL_SURUM);
  okulApiMock.listSchoolYears.mockResolvedValue([
    { id: 1, name: "2026-2027", start_date: "2026-09-07", end_date: "2027-06-25", is_active: true },
  ]);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("BirlikDonemiPage", () => {
  it("dönem yokken boş durum ve geçiş kurulumuna bağlantı (program yöneticisi)", async () => {
    apiMock.donemler.mockResolvedValue([]);
    apiMock.gecis.mockResolvedValue({
      ...GECIS,
      state: "BASLAMADI",
      donem: null,
      open_steps: ["donem"],
    });
    bas();
    expect(await screen.findByText(DONEM_YOK_BASLIGI)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: DUGME_GECISI_AC })[0]).toHaveAttribute(
      "href",
      "/birlik-donemi/gecis-kurulumu",
    );
    expect(screen.getByText(DONEM_YOK_ACIKLAMASI)).toBeInTheDocument();
  });

  it("salt okur rolde dönem yokken yalnız başlık: yazmayı öğütleyen cümle ve bağlantı yok", async () => {
    apiMock.donemler.mockResolvedValue([]);
    apiMock.gecis.mockResolvedValue({
      ...GECIS,
      state: "BASLAMADI",
      donem: null,
      open_steps: ["donem"],
    });
    bas(["son_oturum_onay"]);
    expect(await screen.findByText(DONEM_YOK_BASLIGI)).toBeInTheDocument();
    expect(screen.queryByText(DONEM_YOK_ACIKLAMASI)).toBeNull();
    expect(screen.queryByRole("link", { name: DUGME_GECISI_AC })).toBeNull();
  });

  it("D7: kural kopyası doğrulanamayan açık geçiş döneminde bant var, iptal düğmesi yok", async () => {
    const bozuk = { ...DONEM, kural_kopyasi_tutuyor: false };
    apiMock.donemler.mockResolvedValue([bozuk]);
    apiMock.gecis.mockResolvedValue({ ...GECIS, donem: bozuk });
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(KURAL_KOPYASI_BOZUK);
    expect(screen.queryByRole("button", { name: DUGME_DONEMI_IPTAL })).toBeNull();
  });

  it("dönemin bilgileri, salt okunur kural sürümü ve ders yılının adı", async () => {
    bas();
    expect(await screen.findByText("2026-2027 birlik dönemi · Açık")).toBeInTheDocument();
    expect(await screen.findByText("2026-2027")).toBeInTheDocument();
    // Bilgilerdeki satır ve kural sürümü güncellemesinin bağlı ve en yeni sürüm satırları.
    expect(screen.getAllByText("OAB-2023.12 · 1. revizyon")).toHaveLength(3);
    expect(screen.getByText("Geçiş kurulumuyla açıldı")).toBeInTheDocument();
    expect(screen.getByText("Sonraki olağan genel kurul")).toBeInTheDocument();
    expect(screen.getByText("Durum: Sürüyor")).toBeInTheDocument();
    // Kural sürümünü değiştiren bir denetim yoktur.
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByText(KURAL_KOPYASI_BOZUK)).toBeNull();
  });

  it("D7: kural kopyası doğrulanamazsa bant; kapanmış dönemde not; görev süresi uyarısı atfıyla", async () => {
    apiMock.donemler.mockResolvedValue([
      { ...DONEM, id: 2, name: "Eski dönem", status: "KAPANDI", kural_kopyasi_tutuyor: false },
    ]);
    apiMock.gecis.mockResolvedValue({ ...GECIS, donem: null, state: "GEREKMIYOR" });
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(KURAL_KOPYASI_BOZUK);
    expect(screen.getByText(DONEM_KAPANDI_NOTU)).toBeInTheDocument();
    // Geçiş dönemi değil: iptal yok.
    expect(screen.queryByRole("button", { name: DUGME_DONEMI_IPTAL })).toBeNull();
  });

  it("görev süresi uyarıları gerekçe istemez, atfıyla görünür", async () => {
    apiMock.gecis.mockResolvedValue({
      ...GECIS,
      gorev_suresi_uyarilari: [
        {
          metin:
            "Yönetim kurulunun görev süresi 1 yıldır; son genel kuruldan bu yana bu süre geçti (md. 12/2).",
          atif: "md. 12/2",
          durum: "uyari",
        },
      ],
    });
    bas();
    const liste = await screen.findByRole("list", { name: "Görev süresi uyarıları" });
    expect(liste).toHaveTextContent("bu süre geçti.");
    expect(liste).toHaveTextContent("Dayanak: md. 12/2");
    expect(screen.queryByLabelText(/Gerekçe/)).toBeNull();
  });

  it("geçiş dönemi gerekçeyle iptal edilir", async () => {
    const user = userEvent.setup();
    apiMock.donemiIptalEt.mockResolvedValue({ ...DONEM, status: "IPTAL" });
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_DONEMI_IPTAL }));
    const pencere = screen.getByRole("dialog", { name: DONEM_IPTAL_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "İptal et" }));
    expect(within(pencere).getByRole("alert")).toHaveTextContent("İptal gerekçesi yazın.");
    expect(apiMock.donemiIptalEt).not.toHaveBeenCalled();
    await user.type(within(pencere).getByLabelText(/İptal gerekçesi/), "Uydurma: gün yanlış.");
    await user.click(within(pencere).getByRole("button", { name: "İptal et" }));
    expect(apiMock.donemiIptalEt).toHaveBeenCalledWith(3, "Uydurma: gün yanlış.");
    expect(await screen.findByText("Birlik dönemi iptal edildi.")).toBeInTheDocument();
    expect(apiMock.donemler).toHaveBeenCalledTimes(2);
  });

  it("salt okur rolde not var, iptal düğmesi yok; birden çok dönemde liste", async () => {
    const user = userEvent.setup();
    apiMock.donemler.mockResolvedValue([
      { ...DONEM, id: 1, name: "İptal edilen dönem", status: "IPTAL" },
      DONEM,
    ]);
    bas(["son_oturum_onay"]);
    expect(await screen.findByRole("note")).toHaveTextContent("yalnız okuma");
    expect(screen.queryByRole("button", { name: DUGME_DONEMI_IPTAL })).toBeNull();
    const tablo = screen.getByRole("table", { name: "Birlik Dönemleri" });
    expect(within(tablo).getByText("İptal edildi")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "İptal edilen dönem bilgilerini göster" }));
    expect(screen.getByText("İptal edilen dönem · İptal edildi")).toBeInTheDocument();
  });

  it("okunamazsa hata bandı", async () => {
    apiMock.donemler.mockRejectedValue(new Error("ağ"));
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent("Birlik dönemleri okunamadı.");
  });

  it("yeni açılan okulda boş durum genel kurulu planlamaya götürür; geçiş kurulumu önerilmez", async () => {
    apiMock.donemler.mockResolvedValue([]);
    apiMock.gecis.mockResolvedValue({ ...GECIS, state: "GEREKMIYOR", donem: null, open_steps: [] });
    okulApiMock.getSchoolConfig.mockResolvedValue({ opened_on: "2026-09-07" });
    bas();
    const baglanti = await screen.findByRole("link", { name: DUGME_GENEL_KURULU_PLANLA });
    expect(baglanti).toHaveAttribute("href", "/genel-kurul");
    expect(screen.getByText(DONEM_YOK_YENI_OKUL_ACIKLAMASI)).toBeInTheDocument();
    expect(screen.queryByText(DONEM_YOK_ACIKLAMASI)).toBeNull();
    expect(screen.queryByRole("link", { name: DUGME_GECISI_AC })).toBeNull();
  });

  it("hazırlık dönemi geçişle açılmış sayılmaz: açılış satırı ve genel kurul bağlantısı (U3)", async () => {
    const hazirlik = {
      ...DONEM,
      id: 4,
      name: "2027-2028 birlik dönemi",
      status: "HAZIRLIK" as const,
      opened_by_assembly: 9,
    };
    apiMock.donemler.mockResolvedValue([hazirlik]);
    apiMock.gecis.mockResolvedValue({ ...GECIS, state: "GEREKMIYOR", donem: null });
    bas();
    expect(await screen.findByText(ACILIS_HAZIRLIK)).toBeInTheDocument();
    expect(screen.queryByText("Geçiş kurulumuyla açıldı")).toBeNull();
    expect(screen.getByRole("link", { name: DUGME_GENEL_KURULU_AC })).toHaveAttribute(
      "href",
      "/genel-kurul?kurul=9",
    );
  });

  it("kural sürümü güncellemesi yalnız program yöneticisinde; güncel sürümde fark yok", async () => {
    const { unmount } = bas();
    expect(await screen.findByText(KURAL_GUNCELLEME_BASLIGI)).toBeInTheDocument();
    expect(await screen.findByText(KURAL_GUNCEL)).toBeInTheDocument();
    expect(apiMock.kuralSurumu).toHaveBeenCalledWith(3, undefined);
    unmount();
    apiMock.kuralSurumu.mockClear();
    bas(["son_oturum_onay", "birlik_donemi_yazma"]);
    // Dönem yüklenmeden bakılmaz: bölüm yalnız seçili dönem gelince çizilir.
    expect(await screen.findByText("2026-2027 birlik dönemi · Açık")).toBeInTheDocument();
    expect(screen.queryByText(KURAL_GUNCELLEME_BASLIGI)).toBeNull();
    expect(apiMock.kuralSurumu).not.toHaveBeenCalled();
  });

  it("kural sürümü okunamazsa bölümde hata bandı", async () => {
    apiMock.kuralSurumu.mockRejectedValue(new Error("ağ"));
    bas();
    expect(await screen.findByText(KURAL_GUNCELLEME_OKUNAMADI)).toBeInTheDocument();
  });

  it("kapanmış dönemde geçiş sert engeldir: dönem kilidi bantla gösterilir", async () => {
    const user = userEvent.setup();
    apiMock.kuralSurumu.mockResolvedValue({
      ...GUNCEL_SURUM,
      en_yeni: R2,
      hedefler: [R2],
      hedef: R2,
      fark: { ...FARK, kayitlar: [], onay_gerekli: false },
    });
    apiMock.kuralSurumunuGecir.mockRejectedValue(
      new ApiError(409, "donem_kapali", "Bu birlik dönemi kapandı; kayıt yazılamaz."),
    );
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_SURUMU_GUNCELLE }));
    expect(await screen.findByText("Bu kayıt yazılamaz")).toBeInTheDocument();
    expect(screen.queryByText(SURUM_GUNCELLENDI)).toBeNull();
  });

  it("fark listeleri; etkilenen kayıt onaylanmadan geçiş gitmez, onayla gider", async () => {
    const user = userEvent.setup();
    apiMock.kuralSurumu.mockResolvedValue({
      ...GUNCEL_SURUM,
      en_yeni: R2,
      hedefler: [R2],
      hedef: R2,
      fark: FARK,
    });
    apiMock.kuralSurumunuGecir.mockResolvedValue({ ...DONEM, kural_paketi: R2, fark: FARK });
    bas();
    const eklenen = await screen.findByRole("list", { name: FARK_EKLENEN });
    expect(eklenen).toHaveTextContent("en az on beş gün önce");
    expect(eklenen).toHaveTextContent("Dayanak: md. 9/3");
    // Kural kimliği yüzeye çıkmaz (sözlük §2).
    expect(screen.queryByText(/genel_kurul\./)).toBeNull();
    expect(screen.getByRole("list", { name: FARK_DEGER })).toBeInTheDocument();
    expect(screen.getByText("Genel kurul · kayıt 7")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_SURUMU_GUNCELLE }));
    expect(await screen.findByText(ETKILENEN_ONAYI_GEREKLI)).toBeInTheDocument();
    expect(apiMock.kuralSurumunuGecir).not.toHaveBeenCalled();
    await user.click(screen.getByRole("checkbox", { name: ETKILENEN_ONAYI }));
    await user.click(screen.getByRole("button", { name: DUGME_SURUMU_GUNCELLE }));
    expect(apiMock.kuralSurumunuGecir).toHaveBeenCalledWith(3, R2, true);
    expect(await screen.findByText(SURUM_GUNCELLENDI)).toBeInTheDocument();
  });

  it("dönemin önceki bağına dönüş geri almadır", async () => {
    const user = userEvent.setup();
    const bagliR2 = { ...GUNCEL_SURUM, bagli: R2, en_yeni: R2, hedef: R2, hedefler: [R1] };
    apiMock.kuralSurumu.mockImplementation((_id: number, hedef?: { rev: number }) =>
      Promise.resolve(
        hedef?.rev === 1
          ? {
              ...bagliR2,
              hedef: R1,
              fark: { ...FARK, eski: R2, yeni: R1, kayitlar: [], onay_gerekli: false },
            }
          : bagliR2,
      ),
    );
    apiMock.kuralSurumunuGecir.mockResolvedValue({ ...DONEM, fark: FARK });
    bas();
    await user.selectOptions(
      await screen.findByRole("combobox", { name: "Geçilecek sürüm" }),
      "OAB-2023.12#1",
    );
    await user.click(await screen.findByRole("button", { name: DUGME_GERI_AL }));
    expect(apiMock.kuralSurumunuGecir).toHaveBeenCalledWith(3, R1, false);
  });
});
