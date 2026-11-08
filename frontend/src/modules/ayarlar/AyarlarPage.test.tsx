// AyarlarPage testi: ders yılları + kapalı günler + şube kataloğu + okul bilgileri
// (okul kartı; alanların kendisi `okul/OkulKartiAlanlari.test`te) + güvenlik sekmesinin varlığı. Güvenlik ve kapalı gün
// panellerinin kendi davranışı modules/guvenlik ve modules/takvim testlerinde;
// burada yalnız sekme kablolaması doğrulanır.
// Kaldırılan sekmeler (ders saatleri, zümreler, şube kümeleri) ve okul türü/
// çizelge/ayrışma alanları geri gelmesin diye ayrıca sabitlenir.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { ClassSection, SchoolTerm, SchoolYear } from "../okul/api";
import { OKUL_KARTI_ACIKLAMASI } from "../okul/metinler";

const oapi = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getSchoolConfig: vi.fn(),
  updateSchoolConfig: vi.fn(),
  getGradeLevels: vi.fn(),
  listSchoolYears: vi.fn(),
  createSchoolYear: vi.fn(),
  activateSchoolYear: vi.fn(),
  listSchoolTerms: vi.fn(),
  configureSchoolTerms: vi.fn(),
  listClassSections: vi.fn(),
  createClassSection: vi.fn(),
  deleteClassSection: vi.fn(),
  seedHolidays: vi.fn(),
}));

vi.mock("../okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../okul/api")>();
  return { ...actual, okulApi: oapi };
});

// Güvenlik paneli kendi API'sine gider; bu testte içeriği önemsizdir.
vi.mock("../guvenlik/GuvenlikAyarlari", () => ({
  default: () => <div>GÜVENLİK PANELİ</div>,
}));

// Kapalı gün paneli kendi testinde; burada yalnız sekmeye bağlandığı doğrulanır.
vi.mock("../takvim/KapaliGunlerPaneli", () => ({
  default: ({ saltOkur }: { saltOkur: boolean }) => (
    <div>KAPALI GÜNLER PANELİ{saltOkur ? " (salt okur)" : ""}</div>
  ),
}));

// Güncelleme paneli kendi testinde; burada yalnız sekmenin rolle görünüp görünmediği sınanır.
vi.mock("../guncelleme/UpdatePanel", () => ({
  default: () => <div>GÜNCELLEME PANELİ</div>,
}));

import { YETENEK_ADLARI } from "../oturum/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import AyarlarPage from "./AyarlarPage";

const AKTIF_YIL: SchoolYear = {
  id: 3,
  name: "2026-2027",
  start_date: "2026-09-01",
  end_date: "2027-06-30",
  is_active: true,
};

const PASIF_YIL: SchoolYear = {
  id: 4,
  name: "2027-2028",
  start_date: "2027-09-01",
  end_date: "2028-06-30",
  is_active: false,
};

const SUBE: ClassSection = {
  id: 11,
  school_year: 3,
  school_year_name: "2026-2027",
  class_level: 10,
  class_section: "A",
  class_label: "10/A",
};

/** Varsayılan: program yöneticisinin bütün yetenekleri (süzme `oturum/yetki`'den gelir). */
function renderPage(yol = "/ayarlar", yetenekler: readonly string[] = YETENEK_ADLARI) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter initialEntries={[yol]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <AyarlarPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  oapi.listSchoolYears.mockResolvedValue([AKTIF_YIL, PASIF_YIL]);
  oapi.seedHolidays.mockResolvedValue({
    year: 0,
    created: 0,
    skipped: 0,
    religious_available: true,
  });
  oapi.getSchoolConfig.mockResolvedValue(ORNEK_OKUL_KARTI);
  oapi.getGradeLevels.mockResolvedValue({
    levels: [
      { value: 9, label: "9" },
      { value: 10, label: "10" },
    ],
    prep_enabled: false,
  });
  oapi.listSchoolTerms.mockResolvedValue([]);
  oapi.listClassSections.mockResolvedValue([SUBE]);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("AyarlarPage — sekmeler", () => {
  it("altı sekme vardır (bu sırayla); kaldırılan sekmeler geri gelmez", async () => {
    renderPage();
    await screen.findByText("2026-2027");
    expect(screen.getAllByRole("tab").map((t) => t.textContent?.trim())).toEqual([
      expect.stringContaining("Ders Yılları"),
      expect.stringContaining("Kapalı Günler"),
      expect.stringContaining("Şubeler"),
      expect.stringContaining("Okul Bilgileri"),
      expect.stringContaining("Güvenlik"),
      expect.stringContaining("Güncelleme"),
    ]);
    for (const ad of [
      /Ders Saatleri/,
      /Zümreler/,
      /Şube Kümeleri/,
      /Tatiller/,
      // Aile iskeletinin kütüphane panelleri (F1a-2'de söküldü).
      /Kütüphane Politikası/,
      /Bölümler/,
      /Ağ Kataloğu/,
      /Saklama/,
    ]) {
      expect(screen.queryByRole("tab", { name: ad })).toBeNull();
    }
  });

  it.each(["ag-katalogu", "saklama", "politika", "bolumler"])(
    "sökülen %s sekmesinin adresi Ders Yılları sekmesine düşer",
    async (sekme) => {
      renderPage(`/ayarlar?tab=${sekme}`);
      expect(await screen.findByText("2026-2027")).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /Ders Yılları/ })).toHaveAttribute(
        "aria-selected",
        "true",
      );
    },
  );

  it("kaldırılmış bir sekmenin adresi sessizce Ders Yılları sekmesine düşer", async () => {
    renderPage("/ayarlar?tab=zumreler");
    expect(await screen.findByText("2026-2027")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Ders Yılları/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("“Diğer ayarlar”da yalnız kurulum sihirbazı bağlantısı kalır", async () => {
    renderPage();
    await screen.findByText("2026-2027");
    expect(screen.getByRole("link", { name: /Kurulum Sihirbazı/ })).toHaveAttribute(
      "href",
      "/kurulum",
    );
    expect(screen.queryByRole("link", { name: /Ders Havuzu/ })).toBeNull();
  });
});

describe("AyarlarPage — ders yılları", () => {
  it("yılları listeler, aktif olanı rozetler; pasif yıl aktifleştirilebilir", async () => {
    oapi.activateSchoolYear.mockResolvedValue(PASIF_YIL);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("2026-2027")).toBeInTheDocument();
    expect(screen.getByText("Aktif")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Aktifleştir/ }));
    const onay = await screen.findByRole("dialog", { name: "Ders yılı aktifleştirilsin mi?" });
    // Onay gövdesi sonucu söyler; kaldırılan modüllerden söz etmez.
    expect(within(onay).getByText(/e-Okul aktarımlarında görülen şubeler/)).toBeInTheDocument();
    expect(within(onay).queryByText(/sınav|ders havuzu/i)).toBeNull();
    await user.click(within(onay).getByRole("button", { name: "Aktifleştir" }));

    await waitFor(() => expect(oapi.activateSchoolYear).toHaveBeenCalledWith(4));
  });

  it("aktifleştirilen yılın iki takvim yılına tatiller eklenir; eksik dini bayram söylenir", async () => {
    // Yıl dönümü: tatilsiz kalan takvim yılında tatiller iş günü sayılır, iş günüyle
    // verilen süreler yanlış hesaplanır (aile iskeletinde görülen kusur).
    oapi.activateSchoolYear.mockResolvedValue(PASIF_YIL);
    oapi.seedHolidays.mockImplementation((yil: number) =>
      Promise.resolve({ year: yil, created: 7, skipped: 0, religious_available: yil !== 2028 }),
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /Aktifleştir/ }));
    const onay = await screen.findByRole("dialog", { name: "Ders yılı aktifleştirilsin mi?" });
    await user.click(within(onay).getByRole("button", { name: "Aktifleştir" }));

    await waitFor(() => expect(oapi.seedHolidays).toHaveBeenCalledTimes(2));
    expect(oapi.seedHolidays.mock.calls.map((c) => c[0])).toEqual([2027, 2028]);
    expect(await screen.findByText(/2028 yılının dini bayram tarihleri yok/)).toBeInTheDocument();
  });

  it("yeni ders yılı oluşturulur ve dönemleri kaydedilir", async () => {
    oapi.createSchoolYear.mockResolvedValue({ ...PASIF_YIL, id: 9, name: "2028-2029" });
    oapi.configureSchoolTerms.mockResolvedValue([]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("2026-2027");

    await user.type(screen.getByLabelText(/Ders yılı adı/), "2028-2029");
    // Tarih alanları klavyeyle değil doğrudan değerle doldurulur (jsdom tarih girdisi).
    const tarih = (etiket: RegExp, deger: string) =>
      fireEvent.change(screen.getByLabelText(etiket), { target: { value: deger } });
    tarih(/^Başlangıç/, "2028-09-01");
    tarih(/^Bitiş/, "2029-06-30");
    tarih(/^1\. dönem bitişi/, "2029-01-16");
    tarih(/^2\. dönem başlangıcı/, "2029-02-02");
    await user.click(screen.getByRole("button", { name: "Ders yılı oluştur" }));

    await waitFor(() =>
      expect(oapi.createSchoolYear).toHaveBeenCalledWith({
        name: "2028-2029",
        start_date: "2028-09-01",
        end_date: "2029-06-30",
      }),
    );
    await waitFor(() =>
      expect(oapi.configureSchoolTerms).toHaveBeenCalledWith(9, {
        first_term_end: "2029-01-16",
        second_term_start: "2029-02-02",
      }),
    );
  });

  it("boş formda istek atılmaz, eksik alanlar işaretlenir", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("2026-2027");

    await user.click(screen.getByRole("button", { name: "Ders yılı oluştur" }));

    expect(await screen.findByText("Ders yılı adı yazılmalıdır.")).toBeInTheDocument();
    expect(oapi.createSchoolYear).not.toHaveBeenCalled();
  });
});

describe("AyarlarPage — şubeler", () => {
  it("şube kataloğunu listeler ve yeni şube ekler", async () => {
    oapi.createClassSection.mockResolvedValue({ ...SUBE, id: 12, class_section: "B" });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Şubeler/ }));
    expect(await screen.findByText("10/A")).toBeInTheDocument();
    // Katalog tarifi kaldırılan salon/sınav özelliklerinden söz etmez.
    expect(screen.getByText(/aktarımında görülen şubeler buraya/)).toBeInTheDocument();
    expect(screen.queryByText(/[Ss]alon|sınav duyurusu/)).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Şube"), "B");
    await user.click(screen.getByRole("button", { name: "Şube ekle" }));

    await waitFor(() =>
      expect(oapi.createClassSection).toHaveBeenCalledWith({
        school_year: 3,
        class_level: 9,
        class_section: "B",
      }),
    );
  });

  it("şube kaldırma onaydan geçer", async () => {
    oapi.deleteClassSection.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Şubeler/ }));
    await screen.findByText("10/A");

    await user.click(screen.getByRole("button", { name: "10/A şubesini kaldır" }));
    const onay = await screen.findByRole("dialog", { name: "Şube katalogdan kaldırılsın mı?" });
    await user.click(within(onay).getByRole("button", { name: "Kaldır" }));

    await waitFor(() => expect(oapi.deleteClassSection).toHaveBeenCalledWith(11));
  });
});

describe("AyarlarPage — okul bilgileri", () => {
  it("okul kartını yükler ve kaydedince bütün alanları gövdeyle gönderir", async () => {
    oapi.updateSchoolConfig.mockResolvedValue({});
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    expect(await screen.findByLabelText(/Okul adı/)).toHaveValue("Örnek Anadolu Lisesi");
    // Kaldırılan alanlar formda yoktur (API sözleşmesi, F0 temizliği, F1b 4. adım).
    for (const etiket of [/Okul türü/, /ders saati/i, /ayrışma/i, /Kısa ad/, /Hazırlık/]) {
      expect(screen.queryByLabelText(etiket)).toBeNull();
    }
    expect(screen.queryByText(/çizelge|Hazırlık/i)).toBeNull();

    await user.click(screen.getByRole("checkbox", { name: "Ortaokul" }));
    await user.click(screen.getByRole("radio", { name: "Hizmet alımıyla" }));
    await user.click(screen.getByRole("button", { name: "Kaydet" }));

    await waitFor(() =>
      expect(oapi.updateSchoolConfig).toHaveBeenCalledWith({
        school_name: "Örnek Anadolu Lisesi",
        province: "İstanbul",
        district: "Örnek İlçe",
        principal_name: "",
        institution_code: "123456",
        levels: ["ORTAOKUL", "ORTAOGRETIM"],
        student_count: 1234,
        student_count_as_of: "2026-10-01",
        settlement_type: "BUYUKSEHIR",
        canteen_mode: "KIRAYA_VERILIYOR",
        staffing_mode: "HIZMET_ALIMI",
        in_campus: false,
        opened_on: null,
        demirbas_onayi: true,
        demirbas_no: "",
      }),
    );
    expect(await screen.findByText("Okul bilgileri kaydedildi.")).toBeInTheDocument();
  });

  it("mevcut, kurum kodu ve bilgisayarın demirbaş no'su düzenlenir", async () => {
    oapi.updateSchoolConfig.mockResolvedValue({});
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    expect(await screen.findByLabelText(/^Öğrenci mevcudu/)).toHaveValue("1234");
    expect(screen.getByRole("checkbox", { name: "Ortaöğretim (lise)" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Bu bilgisayar okul demirbaşıdır/ })).toBeChecked();

    await user.clear(screen.getByLabelText(/^Öğrenci mevcudu/));
    await user.type(screen.getByLabelText(/^Öğrenci mevcudu/), " 1.250 ");
    await user.clear(screen.getByLabelText(/^Kurum kodu/));
    await user.type(screen.getByLabelText(/^Kurum kodu/), "654321");
    await user.type(screen.getByLabelText("Bilgisayarın demirbaş no'su"), "BLG-17");
    await user.click(screen.getByRole("button", { name: "Kaydet" }));

    await waitFor(() =>
      expect(oapi.updateSchoolConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          institution_code: "654321",
          student_count: 1250,
          demirbas_onayi: true,
          demirbas_no: "BLG-17",
        }),
      ),
    );
  });

  it("açıklama okul kartının kullanıldığı yerleri söyler; etiket ve üye kartı yoktur", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    await screen.findByLabelText(/^Kurum kodu/);
    expect(screen.getByText(OKUL_KARTI_ACIKLAMASI)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/etiket|üye kart/i);
  });

  it("kurulumdan sonra zorunlu alanlar boşaltılamaz (sihirbazla aynı kural)", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    await user.clear(await screen.findByLabelText(/^Kurum kodu/));
    await user.click(screen.getByRole("checkbox", { name: "Ortaöğretim (lise)" }));
    await user.clear(screen.getByLabelText(/^Öğrenci mevcudu/));
    await user.click(screen.getByRole("checkbox", { name: /Bu bilgisayar okul demirbaşıdır/ }));
    await user.click(screen.getByRole("button", { name: "Kaydet" }));

    expect(await screen.findByText("Zorunlu alanları doldurun.")).toBeInTheDocument();
    expect(screen.getByText("Kurum kodu zorunludur.")).toBeInTheDocument();
    expect(screen.getByText("En az bir kademe seçin.")).toBeInTheDocument();
    expect(screen.getByText("Öğrenci mevcudu zorunludur.")).toBeInTheDocument();
    expect(
      screen.getByText("Program yalnız okul demirbaşı bilgisayara kurulur; onay zorunludur."),
    ).toBeInTheDocument();
    expect(oapi.updateSchoolConfig).not.toHaveBeenCalled();
  });

  it("F1b 4. adımdan önce kurulmuş programda yeni alanlar boş gelir; seçilmeden kaydedilmez", async () => {
    oapi.getSchoolConfig.mockResolvedValue({
      ...ORNEK_OKUL_KARTI,
      institution_code: "",
      levels: [],
      student_count: null,
      student_count_as_of: null,
      settlement_type: "",
      canteen_mode: "",
      staffing_mode: "",
    });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    const yerlesim = await screen.findByRole("group", { name: /^Yerleşim türü/ });
    for (const radyo of within(yerlesim).getAllByRole("radio")) expect(radyo).not.toBeChecked();
    // Mevcudun tarihi kayıtta yoksa form bugünü önerir.
    expect(screen.getByLabelText(/^Mevcudun tarihi/)).not.toHaveValue("");
    await user.click(screen.getByRole("button", { name: "Kaydet" }));
    expect(await screen.findByText("Yerleşim türünü seçin.")).toBeInTheDocument();
    expect(screen.getByText("Kantin işletme biçimini seçin.")).toBeInTheDocument();
    expect(screen.getByText("Personel çalıştırma biçimini seçin.")).toBeInTheDocument();
    expect(oapi.updateSchoolConfig).not.toHaveBeenCalled();
  });

  it("kaydetme hatası bantta gösterilir", async () => {
    oapi.updateSchoolConfig.mockRejectedValue(
      new ApiError(500, "server_error", "Kayıt yazılamadı."),
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    await screen.findByLabelText(/Okul adı/);
    await user.click(screen.getByRole("button", { name: "Kaydet" }));

    expect(await screen.findByText("Kayıt yazılamadı.")).toBeInTheDocument();
  });

  it("sunucunun alan hatası ilgili alanın altına yazılır", async () => {
    oapi.updateSchoolConfig.mockRejectedValue(
      new ApiError(400, "validation_error", "Girdiğiniz bilgileri kontrol edin.", {
        institution_code: ["Kurum kodu altı haneli bir sayıdır."],
      }),
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("tab", { name: /Okul Bilgileri/ }));
    await screen.findByLabelText(/Okul adı/);
    await user.click(screen.getByRole("button", { name: "Kaydet" }));

    expect(await screen.findByText("Kurum kodu altı haneli bir sayıdır.")).toBeInTheDocument();
    expect(screen.getByLabelText(/^Kurum kodu/)).toHaveAccessibleDescription(
      "Kurum kodu altı haneli bir sayıdır.",
    );
  });
});

describe("AyarlarPage — kapalı günler", () => {
  it("“Kapalı Günler” sekmesi paneli gösterir", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("tab", { name: /Kapalı Günler/ }));
    expect(await screen.findByText("KAPALI GÜNLER PANELİ")).toBeInTheDocument();
  });

  it("?tab=kapali-gunler adresi sekmeyi seçili açar", async () => {
    renderPage("/ayarlar?tab=kapali-gunler");
    expect(await screen.findByText("KAPALI GÜNLER PANELİ")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Kapalı Günler/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("dönem düzenleyicisi yarıyılın kapalı gün olarak girilmesini söyler", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("2026-2027");
    await user.click(screen.getAllByRole("button", { name: /Dönemler/ })[0]);
    const metin = await screen.findByText(
      /Kapalı Günler sekmesinde öğrenciye kapalı gün olarak da ekleyin/,
    );
    // Gerekçe OAB'nin yarıyıla bağlı hesaplarıdır; ödünç iadesinden söz edilmez.
    expect(metin).toHaveTextContent(/yarıyıla bağlı hesaplar/);
    expect(metin.textContent).not.toMatch(/iade/i);
  });
});

describe("AyarlarPage — güvenlik", () => {
  it("güvenlik sekmesi paneli gösterir", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("tab", { name: /Güvenlik/ }));
    expect(await screen.findByText("GÜVENLİK PANELİ")).toBeInTheDocument();
  });
});

describe("AyarlarPage — rol süzmesi (okul sekmeleri öteki rollerde salt okurdur)", () => {
  /** Başkanın yetenekleri (sunucudan gelir gibi): Ayarlar'da yazma yok. */
  const BASKAN = ["son_oturum_onay"];
  const SALT_OKUR = "Bu bölüm hesabınızın rolüne yalnız okuma için açık.";

  it("Güncelleme sekmesi ve Kurulum Sihirbazı kartı yalnız yeteneği olan rolde", async () => {
    renderPage("/ayarlar", BASKAN);
    await screen.findByText("2026-2027");

    expect(screen.getAllByRole("tab").map((t) => t.textContent?.trim())).toEqual([
      expect.stringContaining("Ders Yılları"),
      expect.stringContaining("Kapalı Günler"),
      expect.stringContaining("Şubeler"),
      expect.stringContaining("Okul Bilgileri"),
      expect.stringContaining("Güvenlik"),
    ]);
    expect(screen.queryByRole("link", { name: /Kurulum Sihirbazı/ })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Diğer Ayarlar" })).toBeNull();
    expect(
      screen.getByText(/burada görüntülenir; parolanızı Güvenlik sekmesinden/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/güncelleme burada yönetilir/)).toBeNull();
  });

  it("?tab=guncelleme adresi yeteneksiz rolde varsayılan sekmeye düşer, panel çizilmez", async () => {
    renderPage("/ayarlar?tab=guncelleme", BASKAN);
    expect(await screen.findByText("2026-2027")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Ders Yılları/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.queryByText("GÜNCELLEME PANELİ")).toBeNull();
  });

  it("program yöneticisinde Güncelleme sekmesi açılır", async () => {
    renderPage("/ayarlar?tab=guncelleme");
    expect(await screen.findByText("GÜNCELLEME PANELİ")).toBeInTheDocument();
  });

  it("ders yılları salt okur: oluşturma ve aktifleştirme yok, dönemler aralık olarak yazılır", async () => {
    const user = userEvent.setup();
    oapi.listSchoolTerms.mockResolvedValue([
      {
        id: 1,
        school_year: 3,
        sequence: 1,
        name: "1. dönem",
        start_date: "2026-09-01",
        end_date: "2027-01-22",
      },
      {
        id: 2,
        school_year: 3,
        sequence: 2,
        name: "2. dönem",
        start_date: "2027-02-08",
        end_date: "2027-06-30",
      },
    ] satisfies SchoolTerm[]);
    renderPage("/ayarlar", BASKAN);

    expect(await screen.findByText("2026-2027")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(SALT_OKUR);
    expect(screen.queryByRole("button", { name: /Aktifleştir/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Ders yılı oluştur/ })).toBeNull();
    expect(screen.queryByText("Yeni Ders Yılı")).toBeNull();

    await user.click(screen.getAllByRole("button", { name: /Dönemler/ })[0]);
    expect(
      await screen.findByText(
        "1. dönem: 01.09.2026 – 22.01.2027 · 2. dönem: 08.02.2027 – 30.06.2027",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("1. dönem bitişi")).toBeNull();
    expect(screen.queryByRole("button", { name: /Dönemleri kaydet/ })).toBeNull();
  });

  it("dönemleri girilmemiş yıl salt okurda bunu söyler; ders yılı yoksa eklemeyi öğütlemez", async () => {
    const user = userEvent.setup();
    const { unmount } = renderPage("/ayarlar", BASKAN);
    await screen.findByText("2026-2027");
    await user.click(screen.getAllByRole("button", { name: /Dönemler/ })[0]);
    expect(
      await screen.findByText("Bu ders yılının dönemleri henüz girilmedi."),
    ).toBeInTheDocument();
    unmount();

    oapi.listSchoolYears.mockResolvedValue([]);
    renderPage("/ayarlar", BASKAN);
    expect(await screen.findByText("Henüz ders yılı tanımlanmadı.")).toBeInTheDocument();
  });

  it("kapalı günler paneli salt okur kipte açılır", async () => {
    renderPage("/ayarlar?tab=kapali-gunler", BASKAN);
    expect(await screen.findByText("KAPALI GÜNLER PANELİ (salt okur)")).toBeInTheDocument();
  });

  it("şubeler salt okur: liste kalır, ekleme ve kaldırma yok", async () => {
    renderPage("/ayarlar?tab=subeler", BASKAN);

    expect(await screen.findByText("10/A")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(SALT_OKUR);
    expect(screen.queryByRole("button", { name: /şubesini kaldır/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Şube ekle" })).toBeNull();
    expect(screen.queryByLabelText("Şube")).toBeNull();
    expect(
      screen.getByText("Öğrenci aktarımında görülen şubeler buraya kendiliğinden eklenir."),
    ).toBeInTheDocument();
  });

  it("okul bilgileri salt okur: form yerine değerler listelenir", async () => {
    renderPage("/ayarlar?tab=okul", BASKAN);

    expect(await screen.findByText("Örnek Anadolu Lisesi")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(SALT_OKUR);
    expect(screen.getByText("Ortaöğretim (lise)")).toBeInTheDocument();
    expect(screen.getByText("123456")).toBeInTheDocument();
    expect(screen.getByText("1.234 · 01.10.2026 itibarıyla")).toBeInTheDocument();
    expect(screen.getByText("Kiraya veriliyor")).toBeInTheDocument();
    expect(screen.queryByText("Örnek AL")).toBeNull();
    expect(screen.getByText("Bu bilgisayar okul demirbaşıdır.")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByRole("radio")).toBeNull();
    expect(screen.queryByRole("button", { name: "Kaydet" })).toBeNull();
    expect(oapi.updateSchoolConfig).not.toHaveBeenCalled();
  });

  it("özet yüklenirken sekmeler çizilmez", () => {
    render(
      <MemoryRouter initialEntries={["/ayarlar"]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <AyarlarPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Ayarlar" })).toBeInTheDocument();
    expect(screen.queryByRole("tab")).toBeNull();
    expect(screen.queryByRole("link", { name: /Kurulum Sihirbazı/ })).toBeNull();
  });
});
