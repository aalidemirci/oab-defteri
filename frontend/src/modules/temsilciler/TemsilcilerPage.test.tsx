// Temsilciler ekranı (plan F1c 11. adımın ikinci parçası): çizelge (satırın atıflı uyarısı ve eksikliği,
// rehberlik komisyonunun notu, başkan sıfatıyla satır, karar bağı işareti), temsilci kaydı (satırdan açılınca
// temsil türü seçili; karar bağı yalnız kabul edilmiş karar; uyarı gerekçe ister), iptal, belge kartı
// (E03), salt okur rol ve birlik dönemi yokken boş durum. Veriler uydurmadır.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { BirlikDonemi } from "../birlik-donemi/api";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import type { Uyelik } from "../organlar/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { CizelgeSatiri } from "./api";

const temsilcilerApiMock = vi.hoisted(() => ({ cizelge: vi.fn(), ekle: vi.fn() }));
vi.mock("./api", () => ({ temsilcilerApi: temsilcilerApiMock }));

const organlarApiMock = vi.hoisted(() => ({ iptalEt: vi.fn(), baglanabilirKararlar: vi.fn() }));
vi.mock("../organlar/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../organlar/api")>()),
  organlarApi: organlarApiMock,
}));

const donemApiMock = vi.hoisted(() => ({ donemler: vi.fn() }));
vi.mock("../birlik-donemi/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../birlik-donemi/api")>()),
  birlikDonemiApi: donemApiMock,
}));

const evrakApiMock = vi.hoisted(() => ({ liste: vi.fn(), uret: vi.fn(), dosya: vi.fn() }));
vi.mock("../evrak/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../evrak/api")>()),
  evrakApi: evrakApiMock,
}));

const kisiApiMock = vi.hoisted(() => ({ liste: vi.fn() }));
vi.mock("../kisiler/birlikKisileriApi", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../kisiler/birlikKisileriApi")>()),
  birlikKisileriApi: kisiApiMock,
}));

const yarimMetinMock = vi.hoisted(() => ({ oku: vi.fn(), kaydet: vi.fn(), temizle: vi.fn() }));
vi.mock("../uyum/api", () => ({ yarimMetinApi: yarimMetinMock }));

import TemsilcilerPage from "./TemsilcilerPage";
import { DONEM_YOK_ORGAN_ACIKLAMASI, DUGME_BIRLIK_DONEMINE_GIT } from "../organlar/metinler";
import {
  CIP_KARAR_BAGLI,
  CIZELGE_BOS,
  DUGME_TEMSILCI_EKLE,
  TEMSILCI_GIRILMEDI,
  TEMSILCI_IPTAL_BASLIGI,
  TEMSILCI_PENCERESI_BASLIGI,
  temsilciIptalEtiketi,
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

function temsilci(id: number, ad: string, ek: Partial<Uyelik> = {}): Uyelik {
  return {
    id,
    term: 3,
    person: id + 100,
    person_name: ad,
    organ: "TEMSILCI",
    role: "UYE",
    seat_type: "ASIL",
    seat_group: "",
    seat_order: null,
    elected_by: "YK_KARARI",
    source: "PROGRAM",
    evidence_note: "",
    representation: "SOSYAL_ETKINLIKLER_KURULU",
    mem_approval_no: "",
    status: "SECILDI",
    start_date: "2026-10-20",
    end_date: null,
    votes: null,
    promoted_on: null,
    promoted_by_decision: null,
    representative_decision: null,
    drop_kind: "",
    eligibility_declared_on: null,
    single_birlik_declared_on: null,
    expertise_required: false,
    eligibility_bar: "YOK",
    eligibility_bar_found_on: null,
    retained_until_assembly: false,
    external_assignment_start: null,
    external_assignment_end: null,
    ...ek,
  };
}

const CIZELGE: CizelgeSatiri[] = [
  {
    representation: "SOSYAL_ETKINLIKLER_KURULU",
    ad: "Okul sosyal etkinlikler kurulu",
    kural: "temsilci.sosyal_etkinlikler_kurulu",
    durum: "uygun",
    metin: "",
    notlar: [],
    uyeler: [temsilci(51, "Uydurnur Sosyalkaya", { representative_decision: 8 })],
  },
  {
    representation: "RPD_YURUTME_KOMISYONU",
    ad: "Rehberlik ve psikolojik danışma hizmetleri yürütme komisyonu",
    kural: "temsilci.rpd_yurutme_komisyonu",
    durum: "eksik",
    metin: "Rehberlik komisyonunda birlik temsilcisi girilmedi (RPD Yön. md. 16/5).",
    notlar: ["Komisyonun diğer üyeleri öğretmenler kurulunda belirlenir."],
    uyeler: [],
  },
  {
    representation: "TASIMACI_TESPIT_KOMISYONU",
    ad: "Taşımacıyı tespit komisyonu",
    kural: "temsilci.tasimaci_tespit_komisyonu",
    durum: "uyari",
    metin: "Temsilci görevdeki yönetim kurulu başkanı olmalıdır (md. 17/1).",
    notlar: [],
    uyeler: [
      temsilci(52, "Uydurgül Başkanoğlu", {
        representation: "TASIMACI_TESPIT_KOMISYONU",
        elected_by: "KENDILIGINDEN",
      }),
    ],
  },
];

const KISI: BirlikKisisi = {
  id: 7,
  kind: "VELI",
  first_name: "Uydurnur",
  last_name: "Yenikaya",
  full_name: "Uydurnur Yenikaya",
  is_parent: true,
  adult_declared: false,
  is_principal: false,
  personnel: null,
  external_yk_terms: null,
  external_dk_chair_terms: null,
  status: "AKTIF",
};

const YAZAN = ["temsilci_yazma", "organ_yazma", "karar_taslagi_uretme", "birlik_donemi_yazma"];

function bas(yetenekler: readonly string[] = YAZAN) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <TemsilcilerPage />
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  donemApiMock.donemler.mockResolvedValue([DONEM]);
  temsilcilerApiMock.cizelge.mockResolvedValue(CIZELGE);
  organlarApiMock.baglanabilirKararlar.mockResolvedValue([]);
  evrakApiMock.liste.mockResolvedValue([]);
  kisiApiMock.liste.mockResolvedValue([KISI]);
  yarimMetinMock.oku.mockResolvedValue(null);
  yarimMetinMock.kaydet.mockResolvedValue(undefined);
  yarimMetinMock.temizle.mockResolvedValue(undefined);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Temsilciler", () => {
  it("çizelge: atıflı satır durumu, not, başkan sıfatı ve karar bağı", async () => {
    bas();
    expect(await screen.findByText("Uydurnur Sosyalkaya · Asıl")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Temsilciler" })).toBeInTheDocument();
    expect(screen.getByText(CIP_KARAR_BAGLI)).toBeInTheDocument();
    expect(screen.getByText("Birlik başkanı sıfatıyla")).toBeInTheDocument();
    expect(screen.getByText(TEMSILCI_GIRILMEDI)).toBeInTheDocument();
    expect(screen.getByText(/Komisyonun diğer üyeleri/)).toBeInTheDocument();
    expect(screen.getByText("Dayanak: md. 17/1")).toBeInTheDocument();
    expect(screen.getByText("Eksik")).toBeInTheDocument();
    expect(screen.getByText("Uyarı")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Belgeyi oluştur" })).toBeInTheDocument();
  });

  it("satırdan temsilci kaydı: temsil türü seçili, uyarı gerekçe ister", async () => {
    const user = userEvent.setup();
    temsilcilerApiMock.ekle
      .mockRejectedValueOnce(
        new ApiError(
          400,
          "gerekce_gerekli",
          "Bu kayıt için gerekçe yazılmalıdır. Kurulda fazla temsilci var (md. 6/1).",
        ),
      )
      .mockResolvedValueOnce(temsilci(53, "Uydurnur Yenikaya"));
    bas();
    await user.click(
      await screen.findByRole("button", {
        name: `Okul sosyal etkinlikler kurulu: ${DUGME_TEMSILCI_EKLE}`,
      }),
    );
    const pencere = screen.getByRole("dialog", { name: TEMSILCI_PENCERESI_BASLIGI });
    expect(within(pencere).getByLabelText(/Temsil edilen kurul ya da komisyon/)).toHaveValue(
      "SOSYAL_ETKINLIKLER_KURULU",
    );
    // Kabul edilmiş karar yoksa karar bağı seçilemez.
    expect(within(pencere).getByLabelText("Yönetim kurulu kararı")).toBeDisabled();
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(await within(pencere).findByText("Bu kayıt gerekçe istiyor")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText(/^Gerekçe/), "Uydurma gerekçe.");
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(temsilcilerApiMock.ekle).toHaveBeenLastCalledWith({
      term: 3,
      person: 7,
      representation: "SOSYAL_ETKINLIKLER_KURULU",
      seat_type: "ASIL",
      start_date: null,
      representative_decision: null,
      gerekce: "Uydurma gerekçe.",
    });
    expect(await screen.findByText("Temsilci eklendi.")).toBeInTheDocument();
  });

  it("genel düğme: temsil türü ve kişi zorunlu; kabul edilmiş karar bağlanır", async () => {
    const user = userEvent.setup();
    organlarApiMock.baglanabilirKararlar.mockResolvedValue([
      {
        id: 4,
        kind: "OLAGAN",
        status: "KABUL_EDILDI",
        decision_no: null,
        page_no: null,
        decision_date: null,
        toplanti_gunu: "2026-10-20",
      },
    ]);
    temsilcilerApiMock.ekle.mockResolvedValue(temsilci(53, "Uydurnur Yenikaya"));
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_TEMSILCI_EKLE }));
    const pencere = screen.getByRole("dialog", { name: TEMSILCI_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Kişiyi seçin.")).toBeInTheDocument();
    expect(
      within(pencere).getByText("Temsil edilen kurul ya da komisyonu seçin."),
    ).toBeInTheDocument();
    await user.selectOptions(
      within(pencere).getByLabelText(/Temsil edilen kurul ya da komisyon/),
      "KANTIN_DENETIM_KOMISYONU",
    );
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    await user.selectOptions(within(pencere).getByLabelText("Koltuk"), "YEDEK");
    await user.selectOptions(within(pencere).getByLabelText("Yönetim kurulu kararı"), "4");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(temsilcilerApiMock.ekle).toHaveBeenCalledWith({
      term: 3,
      person: 7,
      representation: "KANTIN_DENETIM_KOMISYONU",
      seat_type: "YEDEK",
      start_date: null,
      representative_decision: 4,
    });
  });

  it("temsilci kaydının iptali gerekçeyle", async () => {
    const user = userEvent.setup();
    organlarApiMock.iptalEt.mockResolvedValue(temsilci(51, "Uydurnur Sosyalkaya"));
    bas();
    await user.click(
      await screen.findByRole("button", {
        name: "Okul sosyal etkinlikler kurulu: Uydurnur Sosyalkaya Kaydı iptal et",
      }),
    );
    const pencere = screen.getByRole("dialog", { name: TEMSILCI_IPTAL_BASLIGI });
    await user.type(within(pencere).getByLabelText(/İptal gerekçesi/), "Uydurma.");
    await user.click(within(pencere).getByRole("button", { name: "İptal et" }));
    expect(organlarApiMock.iptalEt).toHaveBeenCalledWith(51, "Uydurma.");
  });

  it("salt okur rol: düğme yok, çizelge görünür", async () => {
    bas([]);
    expect(await screen.findByText("Uydurnur Sosyalkaya · Asıl")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_TEMSILCI_EKLE })).toBeNull();
    expect(screen.queryByRole("button", { name: /Kaydı iptal et/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Belgeyi oluştur" })).toBeNull();
  });

  it("çizelge boşsa ve birlik dönemi yoksa", async () => {
    temsilcilerApiMock.cizelge.mockResolvedValue([]);
    const { unmount } = bas();
    expect(await screen.findByText(CIZELGE_BOS)).toBeInTheDocument();
    unmount();
    donemApiMock.donemler.mockResolvedValue([]);
    bas();
    expect(await screen.findByText("Birlik dönemi açılmadı")).toBeInTheDocument();
  });

  it("çizelge okunamazsa hata bandı", async () => {
    temsilcilerApiMock.cizelge.mockRejectedValue(new Error("ağ yok"));
    bas();
    expect(await screen.findByText("Temsilciler çizelgesi okunamadı.")).toBeInTheDocument();
  });
});

describe("Temsilciler — geçiş, alan hataları, boş durum", () => {
  const DEVRALINAN = temsilci(54, "Uydurgül Devralkaya", { source: "DEVRALINAN" });
  const ILK_KART = "Okul sosyal etkinlikler kurulu";

  beforeEach(() => {
    temsilcilerApiMock.cizelge.mockResolvedValue([
      { ...CIZELGE[0], uyeler: [...CIZELGE[0].uyeler, DEVRALINAN] },
      ...CIZELGE.slice(1),
    ]);
  });

  it("devralınan temsilcinin iptali yalnız program yöneticisinde ve geçiş açıkken", async () => {
    const devralinanIptal = temsilciIptalEtiketi(ILK_KART, "Uydurgül Devralkaya");
    const programIptal = temsilciIptalEtiketi(ILK_KART, "Uydurnur Sosyalkaya");
    const ilk = bas();
    expect(await screen.findByRole("button", { name: devralinanIptal })).toBeInTheDocument();
    ilk.unmount();
    // Sekreter: temsilci yazar, kaydı iptal eder; devralınanı (geçiş kaydı) iptal etmez.
    const ikinci = bas(["temsilci_yazma", "organ_yazma"]);
    expect(await screen.findByRole("button", { name: programIptal })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: devralinanIptal })).toBeNull();
    ikinci.unmount();
    // "Geçiş kurulumu tamamlandı" işaretinden sonra sunucu 409 `gecis_kapali` verir.
    donemApiMock.donemler.mockResolvedValue([{ ...DONEM, transition_completed_on: "2026-11-05" }]);
    bas();
    expect(await screen.findByRole("button", { name: programIptal })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: devralinanIptal })).toBeNull();
  });

  it("alan hataları seçim yapılınca kalkar", async () => {
    const user = userEvent.setup();
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_TEMSILCI_EKLE }));
    const pencere = screen.getByRole("dialog", { name: TEMSILCI_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Kişiyi seçin.")).toBeInTheDocument();
    expect(
      within(pencere).getByText("Temsil edilen kurul ya da komisyonu seçin."),
    ).toBeInTheDocument();
    await user.selectOptions(
      within(pencere).getByLabelText(/Temsil edilen kurul ya da komisyon/),
      "KANTIN_DENETIM_KOMISYONU",
    );
    expect(within(pencere).queryByText("Temsil edilen kurul ya da komisyonu seçin.")).toBeNull();
    expect(within(pencere).getByText("Kişiyi seçin.")).toBeInTheDocument();
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    expect(within(pencere).queryByText("Kişiyi seçin.")).toBeNull();
  });

  it("birlik dönemi yoksa program yöneticisine açıklama ve bağlantı; salt okurda yok", async () => {
    donemApiMock.donemler.mockResolvedValue([]);
    const ilk = bas();
    expect(await screen.findByText("Birlik dönemi açılmadı")).toBeInTheDocument();
    expect(screen.getByText(DONEM_YOK_ORGAN_ACIKLAMASI)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: DUGME_BIRLIK_DONEMINE_GIT })).toHaveAttribute(
      "href",
      "/birlik-donemi",
    );
    ilk.unmount();
    bas([]);
    expect(await screen.findByText("Birlik dönemi açılmadı")).toBeInTheDocument();
    expect(screen.queryByText(DONEM_YOK_ORGAN_ACIKLAMASI)).toBeNull();
    expect(screen.queryByRole("link", { name: DUGME_BIRLIK_DONEMINE_GIT })).toBeNull();
  });
});
