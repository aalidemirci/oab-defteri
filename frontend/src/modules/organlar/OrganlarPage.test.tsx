// Organlar ekranı (plan F1c 11. adımın ikinci parçası): sekmeler, kadro (asıllar, yedekler, öteki kayıtlar,
// kadro uyarıları, öneriler adla), üyeliğin penceresi (seçilme sayacı, görev alma engelinin hükmü, rolün
// görünümüyle uyum satırı, dayanağın yalnız düğmeyle okunması), eylemler yeteneğe göre (görev bölümü yalnız
// sekreter, Denetleme Kurulunun görev bölümü yalnız Denetleme Kurulu, düşme, yedek çağrısı, engel, iptal),
// uyarı + gerekçe akışı, aylık toplantı günü, birlik dönemi yokken ve kapanmışken salt okur. Veriler
// uydurmadır.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { E01_ADI } from "../evrak/metinler";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { YETENEK_ADLARI } from "../oturum/api";
import type { YetenekAdi } from "../oturum/api";
import { SALT_OKUR_ILETISI } from "../oturum/RolKapisi";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { Kadro, Uyelik } from "./api";

const organlarApiMock = vi.hoisted(() => ({
  kadro: vi.fn(),
  uyelikler: vi.fn(),
  ogretmenUyeEkle: vi.fn(),
  guncelle: vi.fn(),
  iptalEt: vi.fn(),
  dusur: vi.fn(),
  ykYedekCagir: vi.fn(),
  dkYedekCagir: vi.fn(),
  engelYaz: vi.fn(),
  engelDayanagi: vi.fn(),
  ykGorevBolumu: vi.fn(),
  dkGorevBolumu: vi.fn(),
  alimKomisyonuEkle: vi.fn(),
  toplantiGunu: vi.fn(),
  baglanabilirKararlar: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
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

import { katilimSatirlari } from "./GorevBolumuPenceresi";
import OrganlarPage from "./OrganlarPage";
import { ogretmenGovdesi } from "./UyeEklePenceresi";
import { bilgiGovdesi } from "./UyelikEylemleri";
import {
  ASIL_UYE_YOK_GOREV_BOLUMU,
  DAYANAK_OKUMA_NOTU,
  DK_GOREV_BOLUMU_BASLIGI,
  DONEM_YOK_ORGAN_ACIKLAMASI,
  DUGME_DAYANAK,
  DUGME_DK_GOREV_BOLUMU,
  DUGME_DUSUR,
  DUGME_ENGEL,
  DUGME_GOREV_BOLUMU,
  DUGME_KAYDI_IPTAL,
  DUGME_KOMISYON_UYESI_EKLE,
  DUGME_OGRETMEN_EKLE,
  DUGME_YEDEK_CAGIR,
  DUSME_PENCERESI_BASLIGI,
  DUSME_TURU_SECIN,
  ENGEL_DAYANAK_ZORUNLU,
  ENGEL_PENCERESI_BASLIGI,
  GOREV_SECIN,
  KADRO_OKUNAMADI,
  KARAR_YOK,
  KOMISYON_PENCERESI_BASLIGI,
  OGRETMEN_PENCERESI_BASLIGI,
  TEK_GOREV,
  TOPLANTI_GUNU_BASLIGI,
  TOPLANTI_ZAMANI_ZORUNLU,
  UYELIK_IPTAL_BASLIGI,
  YEDEK_PENCERESI_BASLIGI,
  YK_GOREV_BOLUMU_BASLIGI,
  acikUyariMetni,
  kadroOzeti,
  kaldirEtiketi,
  komisyonOzeti,
  satirEtiketi,
  sayacMetni,
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
  yk_meeting_day_rule: "",
  kural_paketi: { paket: "OAB-2023.12", rev: 1 },
  kural_kopyasi_tutuyor: true,
};

function uye(id: number, ad: string, ek: Partial<Uyelik> = {}): Uyelik {
  return {
    id,
    term: 3,
    person: id + 100,
    person_name: ad,
    organ: "YK",
    role: "UYE",
    seat_type: "ASIL",
    seat_group: "",
    seat_order: null,
    elected_by: "GENEL_KURUL",
    source: "DEVRALINAN",
    evidence_note: "",
    representation: "",
    mem_approval_no: "",
    status: "SECILDI",
    start_date: "2026-10-10",
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

const BASKAN = uye(11, "Uydurnur Örnekkaya", { role: "BASKAN" });
const UYE = uye(12, "Uydurgül Denemeoğlu", {
  eligibility_bar: "VAR",
  eligibility_bar_found_on: "2026-10-14",
});
const YEDEK = uye(13, "Uydurhan Sınamacı", { seat_type: "YEDEK", seat_order: 1 });
const DUSEN = uye(14, "Uydurcan Eskikaya", {
  status: "DUSTU",
  drop_kind: "ISTIFA",
  end_date: "2026-11-01",
});

const YK_KADRO: Kadro = {
  organ: "YK",
  gorevdeki_asillar: [BASKAN, UYE],
  bekleyen_yedekler: [YEDEK],
  kadro: { asil: 2, yedek: 1 },
  kadro_uyarilari: [
    {
      metin: "Yönetim kurulunun asıl üye sayısı 5 olmalıdır; kayıtlı 2 (md. 12/1).",
      atif: "md. 12/1",
      durum: "uyari",
    },
  ],
  oneriler: [
    {
      uyelik: 12,
      tur: "HATIRLATMA",
      metin: "Okulun tek birlik yönetimi beyanı uygulaması bu üyelikte işaretlenmedi.",
      gun: null,
      drop_kind: "",
    },
  ],
  uyum_satirlari: [
    {
      id: 41,
      uyelik: 12,
      tur: "SAPMA",
      metin: "Bu kişi için görev almaya engel durum işaretlendi.",
      atif: "",
      gerekceli: true,
    },
  ],
  secilme_sayaclari: [
    { uyelik: 11, program: 1, beyan: 2 },
    { uyelik: 12, program: 0, beyan: null },
  ],
};

const DK_KADRO: Kadro = {
  organ: "DK",
  gorevdeki_asillar: [
    uye(21, "Uydurnaz Velioğlu", { organ: "DK", seat_group: "VELI", role: "BASKAN" }),
    uye(22, "Uydurkan Öğretmen", {
      organ: "DK",
      seat_group: "OGRETMEN",
      elected_by: "MEM_GOREVLENDIRME",
      mem_approval_no: "Uydurma-12",
    }),
  ],
  bekleyen_yedekler: [],
  kadro: { asil: 2, yedek: 0 },
  kadro_uyarilari: [],
  oneriler: [],
  uyum_satirlari: [],
  secilme_sayaclari: [{ uyelik: 21, program: 1, beyan: 1 }],
};

const ALIM_KADRO: Kadro = {
  organ: "ALIM_KOMISYONU",
  gorevdeki_asillar: [
    uye(31, "Uydurnur Alımcı", {
      organ: "ALIM_KOMISYONU",
      source: "PROGRAM",
      elected_by: "YK_KARARI",
      expertise_required: true,
    }),
  ],
  bekleyen_yedekler: [],
  kadro: { asil: 1, yedek: 0 },
  kadro_uyarilari: [
    {
      metin: "Alım komisyonu en az üç kişidir; kayıtlı 1 (md. 18/1).",
      atif: "md. 18/1",
      durum: "uyari",
    },
  ],
  oneriler: [],
  uyum_satirlari: [],
  secilme_sayaclari: [],
};

const KISI: BirlikKisisi = {
  id: 7,
  kind: "OGRETMEN",
  first_name: "Uydurnur",
  last_name: "Yenikaya",
  full_name: "Uydurnur Yenikaya",
  is_parent: false,
  adult_declared: false,
  is_principal: false,
  personnel: null,
  external_yk_terms: null,
  external_dk_chair_terms: null,
  status: "AKTIF",
};

/** Program yöneticisinin yetenekleri (sekreterin ve Denetleme Kurulunun yetenekleri hariç). */
const YONETICI: YetenekAdi[] = YETENEK_ADLARI.filter(
  (ad) => !["gorev_bolumu_yazma", "dk_gorev_bolumu_yazma", "geri_yukleme_gordum"].includes(ad),
);
const SEKRETER: YetenekAdi[] = [
  "birlik_kisi_yazma",
  "gorev_alma_engeli",
  "gorev_bolumu_yazma",
  "karar_taslagi_uretme",
  "organ_yazma",
  "temsilci_yazma",
  "toplanti_gunu_yazma",
  "uyelik_dusurme",
];
const DENETLEME: YetenekAdi[] = ["dk_gorev_bolumu_yazma", "erisim_gunlugu"];
/** Başkanın (ve başkan yardımcısı ile muhasibin) yetenekleri: backend `rol_izinleri` yk_ortak listesi. */
const BASKAN_ROLU: YetenekAdi[] = [
  "birlik_kisi_yazma",
  "gorev_alma_engeli",
  "organ_yazma",
  "son_oturum_onay",
  "temsilci_yazma",
];

function bas(yetenekler: readonly string[] = YONETICI, yol = "/organlar") {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter initialEntries={[yol]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <OrganlarPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  donemApiMock.donemler.mockResolvedValue([DONEM]);
  organlarApiMock.kadro.mockImplementation(async (_d: number, organ: string) =>
    organ === "YK" ? YK_KADRO : organ === "DK" ? DK_KADRO : ALIM_KADRO,
  );
  organlarApiMock.uyelikler.mockImplementation(async (_d: number, organ: string) =>
    organ === "YK" ? [BASKAN, UYE, YEDEK, DUSEN] : [],
  );
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

describe("gövdeler", () => {
  it("katılım: katıldı, özürlü, özürsüz", () => {
    expect(katilimSatirlari([BASKAN, UYE, YEDEK], { 12: "OZURLU", 13: "OZURSUZ" })).toEqual([
      { membership: 11, present: true, excused: false },
      { membership: 12, present: false, excused: true },
      { membership: 13, present: false, excused: false },
    ]);
  });

  it("öğretmen üye: sıra yalnız yedekte, onay sayısı yalnız görevlendirmede", () => {
    const temel = {
      donem: 3,
      kisi: 7,
      koltuk: "ASIL" as const,
      kanal: "OGRETMENLER_KURULU" as const,
      sira: "2",
      gun: "",
      kanit: " Uydurma kanıt ",
      memNo: " 99 ",
    };
    expect(ogretmenGovdesi(temel)).toEqual({
      term: 3,
      person: 7,
      organ: "DK",
      seat_type: "ASIL",
      seat_group: "OGRETMEN",
      elected_by: "OGRETMENLER_KURULU",
      start_date: null,
      seat_order: null,
      evidence_note: "Uydurma kanıt",
      mem_approval_no: "",
    });
    expect(
      ogretmenGovdesi({ ...temel, koltuk: "YEDEK", kanal: "MEM_GOREVLENDIRME", gun: "2026-11-02" }),
    ).toMatchObject({ seat_order: 2, mem_approval_no: "99", start_date: "2026-11-02" });
  });

  it("bilgiler: yalnız değişen alanlar gider, boş gün null", () => {
    const form = {
      eligibility_declared_on: "2026-10-20",
      single_birlik_declared_on: "",
      external_assignment_start: "",
      external_assignment_end: "",
      mem_approval_no: "",
      seat_order: "",
    };
    expect(bilgiGovdesi(BASKAN, form)).toEqual({ eligibility_declared_on: "2026-10-20" });
    expect(bilgiGovdesi(YEDEK, { ...form, eligibility_declared_on: "", seat_order: "3" })).toEqual({
      seat_order: 3,
    });
  });
});

describe("Organlar — yönetim kurulu", () => {
  it("kadro, uyarılar, öneriler adla, öteki kayıtlar ve belge kartı", async () => {
    bas();
    expect(await screen.findByText(kadroOzeti(2, 1))).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Organlar" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Yönetim Kurulu/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText(/asıl üye sayısı 5 olmalıdır/)).toBeInTheDocument();
    expect(screen.getByText(/Uydurgül Denemeoğlu: Okulun tek birlik/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Uydurgül Denemeoğlu/ })).toHaveTextContent(
      acikUyariMetni(1),
    );
    expect(screen.getByRole("button", { name: /Uydurhan Sınamacı/ })).toHaveTextContent(
      "Yedek (1. sıra)",
    );
    expect(screen.getByRole("button", { name: /Uydurcan Eskikaya/ })).toHaveTextContent("Düştü");
    // Program yöneticisi görev bölümünü yazmaz (yalnız sekreter); belgeyi üretir.
    expect(screen.queryByRole("button", { name: DUGME_GOREV_BOLUMU })).toBeNull();
    expect(await screen.findByRole("button", { name: "Belgeyi oluştur" })).toBeInTheDocument();
    expect(screen.getByLabelText("Toplantı günü")).toBeInTheDocument();
  });

  it("üyelik penceresi: sayaç, engel hükmü, uyum satırı; dayanak yalnız düğmeyle okunur", async () => {
    const user = userEvent.setup();
    organlarApiMock.engelDayanagi.mockResolvedValue({
      eligibility_bar: "VAR",
      eligibility_bar_basis: "SUC_12_5_14_7",
      eligibility_bar_found_on: "2026-10-14",
    });
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurgül Denemeoğlu/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurgül Denemeoğlu" });
    expect(within(pencere).getByText(sayacMetni(0, null))).toBeInTheDocument();
    expect(within(pencere).getByText("Var · tespit günü 14.10.2026")).toBeInTheDocument();
    expect(within(pencere).getByText(/görev almaya engel durum/)).toBeInTheDocument();
    expect(organlarApiMock.engelDayanagi).not.toHaveBeenCalled();
    await user.click(within(pencere).getByRole("button", { name: DUGME_DAYANAK }));
    expect(await within(pencere).findByText("Suç engeli (md. 12/5, 14/7)")).toBeInTheDocument();
    expect(within(pencere).getByText(DAYANAK_OKUMA_NOTU)).toBeInTheDocument();
    expect(organlarApiMock.engelDayanagi).toHaveBeenCalledWith(12);
    // Devralınan kaydın iptali program yöneticisinindir (geçiş kaydı).
    expect(within(pencere).getByRole("button", { name: DUGME_KAYDI_IPTAL })).toBeInTheDocument();
  });

  it("başkanın sayacı programla beyan toplanır", async () => {
    const user = userEvent.setup();
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    expect(screen.getByText(sayacMetni(1, 2))).toBeInTheDocument();
  });

  it("düşme: tür zorunlu; uyarı gerekçe ister, ikinci istek gerekçeyi taşır", async () => {
    const user = userEvent.setup();
    organlarApiMock.dusur
      .mockRejectedValueOnce(
        new ApiError(
          400,
          "gerekce_gerekli",
          "Bu kayıt için gerekçe yazılmalıdır. Öğrencisi ayrılan velinin üyeliği sürer (md. 7/2).",
        ),
      )
      .mockResolvedValueOnce(BASKAN);
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    await user.click(screen.getByRole("button", { name: DUGME_DUSUR }));
    const pencere = screen.getByRole("dialog", { name: DUSME_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: DUGME_DUSUR }));
    expect(within(pencere).getByText(DUSME_TURU_SECIN)).toBeInTheDocument();
    // "Olağanüstü genel kurul seçimi" elle seçilmez.
    expect(
      within(pencere).queryByRole("option", { name: "Olağanüstü genel kurul seçimi" }),
    ).toBeNull();
    await user.selectOptions(within(pencere).getByLabelText(/Düşme türü/), "OGRENCI_AYRILDI");
    await user.click(within(pencere).getByLabelText(/Olağanüstü genel kurula kadar sürsün/));
    await user.click(within(pencere).getByRole("button", { name: DUGME_DUSUR }));
    expect(await within(pencere).findByText("Bu kayıt gerekçe istiyor")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText(/^Gerekçe/), "Uydurma gerekçe.");
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(organlarApiMock.dusur).toHaveBeenLastCalledWith(11, {
      drop_kind: "OGRENCI_AYRILDI",
      end_date: null,
      dropped_reason: "",
      ertele: true,
      gerekce: "Uydurma gerekçe.",
    });
    expect(
      await screen.findByText("Üyelik olağanüstü genel kurula kadar devam edecek."),
    ).toBeInTheDocument();
    expect(yarimMetinMock.temizle).toHaveBeenCalledWith("organlar.dusme.yk");
  });

  it("görev alma engeli: var seçilince dayanak ve gün zorunlu", async () => {
    const user = userEvent.setup();
    organlarApiMock.engelYaz.mockResolvedValue({});
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    await user.click(screen.getByRole("button", { name: DUGME_ENGEL }));
    const pencere = screen.getByRole("dialog", { name: ENGEL_PENCERESI_BASLIGI });
    await user.selectOptions(within(pencere).getByLabelText("Engel"), "VAR");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText(ENGEL_DAYANAK_ZORUNLU)).toBeInTheDocument();
    await user.selectOptions(within(pencere).getByLabelText(/Dayanak/), "TEK_BIRLIK_12_4");
    await user.type(within(pencere).getByLabelText(/Tespit günü/), "2026-11-03");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.engelYaz).toHaveBeenCalledWith(11, {
      eligibility_bar: "VAR",
      eligibility_bar_basis: "TEK_BIRLIK_12_4",
      eligibility_bar_found_on: "2026-11-03",
    });
  });

  it("bilgiler penceresi değişen alanı yazar", async () => {
    const user = userEvent.setup();
    organlarApiMock.guncelle.mockResolvedValue(BASKAN);
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    await user.click(screen.getByRole("button", { name: "Bilgileri düzenle" }));
    const pencere = screen.getByRole("dialog", { name: "Üyeliğin bilgileri" });
    await user.type(
      within(pencere).getByLabelText("Görev alma engeli beyanı (okul uygulaması)"),
      "2026-10-20",
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.guncelle).toHaveBeenCalledWith(11, {
      eligibility_declared_on: "2026-10-20",
    });
  });

  it("iptal: gerekçeyle genel iptal ucu", async () => {
    const user = userEvent.setup();
    organlarApiMock.iptalEt.mockResolvedValue(BASKAN);
    bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    await user.click(screen.getByRole("button", { name: DUGME_KAYDI_IPTAL }));
    const pencere = screen.getByRole("dialog", { name: UYELIK_IPTAL_BASLIGI });
    await user.type(within(pencere).getByLabelText(/İptal gerekçesi/), "Uydurma yanlış kayıt.");
    await user.click(within(pencere).getByRole("button", { name: "İptal et" }));
    expect(organlarApiMock.iptalEt).toHaveBeenCalledWith(11, "Uydurma yanlış kayıt.");
    expect(await screen.findByText("Kayıt iptal edildi.")).toBeInTheDocument();
  });

  it("sekreter: görev bölümü (doğrulama, gövde) ve yedek çağrısı; karar yoksa bağ verilmez", async () => {
    const user = userEvent.setup();
    organlarApiMock.ykGorevBolumu.mockResolvedValue({
      toplanti: 1,
      karar: 2,
      karar_durumu: "TASLAK",
      uyelikler: [],
    });
    organlarApiMock.ykYedekCagir.mockResolvedValue(YEDEK);
    bas(SEKRETER);
    await user.click(await screen.findByRole("button", { name: DUGME_GOREV_BOLUMU }));
    const pencere = screen.getByRole("dialog", { name: YK_GOREV_BOLUMU_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText(TOPLANTI_ZAMANI_ZORUNLU)).toBeInTheDocument();
    expect(within(pencere).getByText(GOREV_SECIN)).toBeInTheDocument();
    await user.type(
      within(pencere).getByLabelText(/Toplantının günü ve saati/),
      "2026-10-16T15:00",
    );
    await user.selectOptions(within(pencere).getByLabelText("Başkan"), "11");
    await user.selectOptions(within(pencere).getByLabelText("Sekreter"), "11");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText(TEK_GOREV)).toBeInTheDocument();
    await user.selectOptions(within(pencere).getByLabelText("Sekreter"), "12");
    await user.selectOptions(
      within(pencere).getByLabelText("Uydurgül Denemeoğlu · Katılım"),
      "OZURLU",
    );
    await user.type(within(pencere).getByLabelText("Yer"), "Uydurma salon");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.ykGorevBolumu).toHaveBeenCalledWith(3, {
      held_at: "2026-10-16T15:00",
      place: "Uydurma salon",
      katilim: [
        { membership: 11, present: true, excused: false },
        { membership: 12, present: false, excused: true },
      ],
      baskan: 11,
      sekreter: 12,
    });
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    await user.click(screen.getByRole("button", { name: /Uydurhan Sınamacı/ }));
    await user.click(screen.getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    const yedek = screen.getByRole("dialog", { name: YEDEK_PENCERESI_BASLIGI });
    expect(await within(yedek).findByText(KARAR_YOK)).toBeInTheDocument();
    await user.click(within(yedek).getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    expect(organlarApiMock.ykYedekCagir).toHaveBeenCalledWith(13, {
      promoted_on: null,
      promoted_by_decision: null,
    });
  });

  it("yedek çağrısında kabul edilmiş karar bağlanabilir", async () => {
    const user = userEvent.setup();
    organlarApiMock.baglanabilirKararlar.mockResolvedValue([
      {
        id: 9,
        kind: "YEDEK_CAGIRMA",
        status: "DEFTERE_ISLENDI",
        decision_no: 12,
        page_no: 4,
        decision_date: "2026-11-02",
        toplanti_gunu: "2026-11-02",
      },
    ]);
    organlarApiMock.ykYedekCagir.mockResolvedValue(YEDEK);
    bas(SEKRETER);
    await user.click(await screen.findByRole("button", { name: /Uydurhan Sınamacı/ }));
    await user.click(screen.getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    const yedek = screen.getByRole("dialog", { name: YEDEK_PENCERESI_BASLIGI });
    await user.selectOptions(await within(yedek).findByLabelText("Yedek çağırma kararı"), "9");
    expect(
      within(yedek).getByRole("option", { name: "Sıra no 12 · 02.11.2026" }),
    ).toBeInTheDocument();
    await user.click(within(yedek).getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    expect(organlarApiMock.ykYedekCagir).toHaveBeenCalledWith(13, {
      promoted_on: null,
      promoted_by_decision: 9,
    });
  });

  it("aylık toplantı günü kaydedilir", async () => {
    const user = userEvent.setup();
    organlarApiMock.toplantiGunu.mockResolvedValue({
      ...DONEM,
      yk_meeting_day_rule: "Her ayın ilk salısı",
    });
    bas();
    const alan = await screen.findByLabelText("Toplantı günü");
    await user.type(alan, "Her ayın ilk salısı ");
    await user.click(screen.getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.toplantiGunu).toHaveBeenCalledWith(3, "Her ayın ilk salısı");
    expect(await screen.findByText("Toplantı günü kaydedildi.")).toBeInTheDocument();
  });

  it("toplantı gününün dönem kilidi bantla gösterilir", async () => {
    const user = userEvent.setup();
    organlarApiMock.toplantiGunu.mockRejectedValue(
      new ApiError(409, "donem_kapali", "Bu birlik dönemi kapandı; kayıt yazılamaz."),
    );
    bas();
    await user.type(await screen.findByLabelText("Toplantı günü"), "Salı");
    await user.click(screen.getByRole("button", { name: "Kaydet" }));
    expect(await screen.findByText("Bu kayıt yazılamaz")).toBeInTheDocument();
  });

  it("okul müdürü: yazma denetimi yok; toplantı günü salt okunur", async () => {
    const user = userEvent.setup();
    bas([]);
    expect(await screen.findByText(kadroOzeti(2, 1))).toBeInTheDocument();
    expect(screen.getByText("Girilmedi.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Toplantı günü")).toBeNull();
    expect(screen.queryByRole("button", { name: "Belgeyi oluştur" })).toBeNull();
    await user.click(screen.getByRole("button", { name: /Uydurgül Denemeoğlu/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurgül Denemeoğlu" });
    expect(within(pencere).queryByRole("button", { name: DUGME_DAYANAK })).toBeNull();
    expect(within(pencere).queryByRole("button", { name: DUGME_DUSUR })).toBeNull();
  });

  it("kadro okunamazsa hata bandı", async () => {
    organlarApiMock.kadro.mockRejectedValue(new Error("ağ yok"));
    bas();
    expect(await screen.findByText(KADRO_OKUNAMADI)).toBeInTheDocument();
  });

  it("kapanmış dönemde yazma denetimi çizilmez", async () => {
    donemApiMock.donemler.mockResolvedValue([
      { ...DONEM, status: "KAPANDI", end_date: "2027-10-01" },
    ]);
    bas();
    expect(await screen.findByText(/Bu birlik dönemi kapandı/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Toplantı günü")).toBeNull();
  });

  it("birlik dönemi yoksa boş durum (program yöneticisinde yol gösterir)", async () => {
    donemApiMock.donemler.mockResolvedValue([]);
    bas();
    expect(await screen.findByText("Birlik dönemi açılmadı")).toBeInTheDocument();
    expect(screen.getByText(DONEM_YOK_ORGAN_ACIKLAMASI)).toBeInTheDocument();
    expect(organlarApiMock.kadro).not.toHaveBeenCalled();
  });

  it("birden çok dönemde seçim yapılır", async () => {
    const user = userEvent.setup();
    donemApiMock.donemler.mockResolvedValue([
      {
        ...DONEM,
        id: 2,
        name: "2025-2026 birlik dönemi",
        status: "KAPANDI",
        end_date: "2026-10-09",
      },
      DONEM,
    ]);
    bas([]);
    const secim = await screen.findByLabelText("Birlik dönemi");
    expect(secim).toHaveValue("3");
    await user.selectOptions(secim, "2");
    await waitFor(() => expect(organlarApiMock.kadro).toHaveBeenLastCalledWith(2, "YK"));
  });
});

describe("Organlar — Denetleme Kurulu", () => {
  it("Denetleme Kurulu rolü: görev bölümü ve denetim planı; engel dayanağı yok", async () => {
    const user = userEvent.setup();
    organlarApiMock.dkGorevBolumu.mockResolvedValue({
      toplanti: 1,
      karar: 2,
      karar_durumu: "TASLAK",
      uyelikler: [],
    });
    bas(DENETLEME, "/organlar?tab=dk");
    expect(await screen.findByText(kadroOzeti(2, 0))).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_OGRETMEN_EKLE })).toBeNull();
    expect(await screen.findByRole("button", { name: "Belgeyi oluştur" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_DK_GOREV_BOLUMU }));
    const pencere = screen.getByRole("dialog", { name: DK_GOREV_BOLUMU_BASLIGI });
    await user.type(
      within(pencere).getByLabelText(/Toplantının günü ve saati/),
      "2026-10-17T14:00",
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Başkanı seçin.")).toBeInTheDocument();
    await user.selectOptions(within(pencere).getByLabelText(/Başkan/), "22");
    await user.click(within(pencere).getByRole("button", { name: "İnceleme günü ekle" }));
    await user.click(within(pencere).getByRole("button", { name: "İnceleme günü ekle" }));
    await user.type(within(pencere).getByLabelText("1. inceleme günü"), "2027-01-15");
    await user.click(within(pencere).getByRole("button", { name: kaldirEtiketi(2) }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.dkGorevBolumu).toHaveBeenCalledWith(3, {
      held_at: "2026-10-17T14:00",
      place: "",
      baskan: 22,
      katilim: [
        { membership: 21, present: true, excused: false },
        { membership: 22, present: true, excused: false },
      ],
      denetim_plani: ["2027-01-15"],
    });
  });

  it("program yöneticisi öğretmen üye ekler (onay sayısıyla)", async () => {
    const user = userEvent.setup();
    organlarApiMock.ogretmenUyeEkle.mockResolvedValue(DK_KADRO.gorevdeki_asillar[1]);
    bas(YONETICI, "/organlar?tab=dk");
    await user.click(await screen.findByRole("button", { name: DUGME_OGRETMEN_EKLE }));
    const pencere = screen.getByRole("dialog", { name: OGRETMEN_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Kişiyi seçin.")).toBeInTheDocument();
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    await user.selectOptions(within(pencere).getByLabelText("Seçildiği yer"), "MEM_GOREVLENDIRME");
    await user.type(
      within(pencere).getByLabelText("Millî eğitim müdürlüğü onay sayısı"),
      "Uydurma-7",
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.ogretmenUyeEkle).toHaveBeenCalledWith(
      expect.objectContaining({
        term: 3,
        person: 7,
        elected_by: "MEM_GOREVLENDIRME",
        mem_approval_no: "Uydurma-7",
      }),
    );
  });

  it("sert engel bantla gösterilir", async () => {
    const user = userEvent.setup();
    organlarApiMock.ogretmenUyeEkle.mockRejectedValue(
      new ApiError(400, "kural_sert", "Öğretmen koltuğuna öğretmen girer (md. 14/1)."),
    );
    bas(YONETICI, "/organlar?tab=dk");
    await user.click(await screen.findByRole("button", { name: DUGME_OGRETMEN_EKLE }));
    const pencere = screen.getByRole("dialog", { name: OGRETMEN_PENCERESI_BASLIGI });
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    const bant = await within(pencere).findByRole("alert");
    expect(bant).toHaveTextContent("Kayıt yapılmadı");
    expect(bant).toHaveTextContent("Dayanak: md. 14/1");
  });

  it("asıl üye yokken görev bölümü yapılamaz", async () => {
    const user = userEvent.setup();
    organlarApiMock.kadro.mockResolvedValue({ ...DK_KADRO, gorevdeki_asillar: [] });
    bas(DENETLEME, "/organlar?tab=dk");
    await user.click(await screen.findByRole("button", { name: DUGME_DK_GOREV_BOLUMU }));
    expect(screen.getByText(ASIL_UYE_YOK_GOREV_BOLUMU)).toBeInTheDocument();
  });
});

describe("Organlar — alım komisyonu", () => {
  it("üye ekleme (uzmanlık işaretiyle) ve uyarı", async () => {
    const user = userEvent.setup();
    organlarApiMock.alimKomisyonuEkle.mockResolvedValue(ALIM_KADRO.gorevdeki_asillar[0]);
    bas(YONETICI, "/organlar?tab=alim");
    expect(await screen.findByText(komisyonOzeti(1))).toBeInTheDocument();
    expect(screen.getByText(/en az üç kişidir/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Uydurnur Alımcı/ })).toHaveTextContent(
      "Uzmanlık gerektiren iş",
    );
    await user.click(screen.getByRole("button", { name: DUGME_KOMISYON_UYESI_EKLE }));
    const pencere = screen.getByRole("dialog", { name: KOMISYON_PENCERESI_BASLIGI });
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Yenikaya/ }));
    await user.click(within(pencere).getByLabelText(/Uzmanlık gerektiren iş için/));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(organlarApiMock.alimKomisyonuEkle).toHaveBeenCalledWith({
      term: 3,
      person: 7,
      expertise_required: true,
      start_date: null,
    });
  });

  it("komisyon üyesinin penceresi iptal yolunu açar", async () => {
    const user = userEvent.setup();
    organlarApiMock.iptalEt.mockResolvedValue(ALIM_KADRO.gorevdeki_asillar[0]);
    bas(YONETICI, "/organlar?tab=alim");
    await user.click(await screen.findByRole("button", { name: /Uydurnur Alımcı/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurnur Alımcı" });
    expect(within(pencere).getByText("Evet")).toBeInTheDocument();
    await user.click(within(pencere).getByRole("button", { name: DUGME_KAYDI_IPTAL }));
    const iptal = screen.getByRole("dialog", { name: UYELIK_IPTAL_BASLIGI });
    await user.type(within(iptal).getByLabelText(/İptal gerekçesi/), "Uydurma.");
    await user.click(within(iptal).getByRole("button", { name: "İptal et" }));
    expect(organlarApiMock.iptalEt).toHaveBeenCalledWith(31, "Uydurma.");
  });
});

describe("Organlar — rol dalları, tazeleme ve erişilebilirlik", () => {
  it("toplantı günü kaydı sekme değişince de görünür (dönem seçimi güncellenir)", async () => {
    const user = userEvent.setup();
    organlarApiMock.toplantiGunu.mockResolvedValue({
      ...DONEM,
      yk_meeting_day_rule: "Her ayın ilk salısı",
    });
    bas();
    await user.type(await screen.findByLabelText("Toplantı günü"), "Her ayın ilk salısı");
    await user.click(screen.getByRole("button", { name: "Kaydet" }));
    expect(await screen.findByText("Toplantı günü kaydedildi.")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: /Denetleme Kurulu/ }));
    expect(await screen.findByText(kadroOzeti(2, 0))).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: /Yönetim Kurulu/ }));
    const alan = await screen.findByLabelText("Toplantı günü");
    expect(alan).toHaveValue("Her ayın ilk salısı");
    expect(screen.getByRole("button", { name: "Kaydet" })).toBeDisabled();
  });

  it.each([
    ["yk", true],
    ["alim", true],
    ["dk", false],
  ])("Denetleme Kurulu rolünde salt okur notu sekmeye göre (%s)", async (sekme, gorunur) => {
    bas(DENETLEME, `/organlar?tab=${sekme}`);
    await waitFor(() => expect(organlarApiMock.kadro).toHaveBeenCalled());
    await screen.findByRole("tab", { name: /Yönetim Kurulu/ });
    expect(screen.queryByText(SALT_OKUR_ILETISI) !== null).toBe(gorunur);
  });

  it("toplantı günü ve belge kartlarının başlığı sekme düzeyindedir (h2)", async () => {
    bas();
    expect(
      await screen.findByRole("heading", { level: 2, name: TOPLANTI_GUNU_BASLIGI }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: E01_ADI })).toBeInTheDocument();
  });

  it("kadro satırının adı kaydı açar; görev ve işaretler açıklamadır", async () => {
    bas();
    const satir = await screen.findByRole("button", { name: satirEtiketi("Uydurgül Denemeoğlu") });
    expect(satir).toHaveAccessibleDescription(expect.stringContaining(acikUyariMetni(1)));
  });

  it("geçiş kurulumu tamamlanınca devralınan kaydın iptali çizilmez; program kaydınınki kalır", async () => {
    const user = userEvent.setup();
    donemApiMock.donemler.mockResolvedValue([{ ...DONEM, transition_completed_on: "2026-11-05" }]);
    const { unmount } = bas();
    await user.click(await screen.findByRole("button", { name: /Uydurnur Örnekkaya/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurnur Örnekkaya" });
    expect(within(pencere).getByRole("button", { name: DUGME_DUSUR })).toBeInTheDocument();
    expect(within(pencere).queryByRole("button", { name: DUGME_KAYDI_IPTAL })).toBeNull();
    unmount();
    bas(YONETICI, "/organlar?tab=alim");
    await user.click(await screen.findByRole("button", { name: /Uydurnur Alımcı/ }));
    const komisyon = screen.getByRole("dialog", { name: "Uydurnur Alımcı" });
    expect(within(komisyon).getByRole("button", { name: DUGME_KAYDI_IPTAL })).toBeInTheDocument();
  });

  it("başkan: düşme, yedek çağrısı, devralınan kaydın iptali ve toplantı günü yazımı yok", async () => {
    const user = userEvent.setup();
    bas(BASKAN_ROLU);
    expect(await screen.findByText("Girilmedi.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Toplantı günü")).toBeNull();
    expect(screen.queryByText(SALT_OKUR_ILETISI)).toBeNull();
    await user.click(screen.getByRole("button", { name: /Uydurgül Denemeoğlu/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurgül Denemeoğlu" });
    expect(within(pencere).getByRole("button", { name: DUGME_ENGEL })).toBeInTheDocument();
    expect(within(pencere).queryByRole("button", { name: DUGME_DUSUR })).toBeNull();
    expect(within(pencere).queryByRole("button", { name: DUGME_KAYDI_IPTAL })).toBeNull();
    await user.click(within(pencere).getByRole("button", { name: "Kapat" }));
    await user.click(screen.getByRole("button", { name: /Uydurhan Sınamacı/ }));
    const yedek = screen.getByRole("dialog", { name: "Uydurhan Sınamacı" });
    expect(within(yedek).queryByRole("button", { name: DUGME_YEDEK_CAGIR })).toBeNull();
    expect(screen.queryByRole("button", { name: "Belgeyi oluştur" })).toBeNull();
  });

  it("sekreter: devralınan kaydın iptali yok (geçiş kaydı program yöneticisinindir)", async () => {
    const user = userEvent.setup();
    bas(SEKRETER);
    await user.click(await screen.findByRole("button", { name: /Uydurgül Denemeoğlu/ }));
    const pencere = screen.getByRole("dialog", { name: "Uydurgül Denemeoğlu" });
    expect(within(pencere).getByRole("button", { name: DUGME_DUSUR })).toBeInTheDocument();
    expect(within(pencere).queryByRole("button", { name: DUGME_KAYDI_IPTAL })).toBeNull();
  });

  it("program yöneticisi Denetleme Kurulunun yedeğini çağırır (karar bağı yok)", async () => {
    const user = userEvent.setup();
    const dkYedek = uye(23, "Uydurcan Yedekoğlu", {
      organ: "DK",
      seat_group: "VELI",
      seat_type: "YEDEK",
      seat_order: 1,
    });
    organlarApiMock.kadro.mockImplementation(async (_d: number, organ: string) =>
      organ === "DK" ? { ...DK_KADRO, bekleyen_yedekler: [dkYedek] } : YK_KADRO,
    );
    organlarApiMock.dkYedekCagir.mockResolvedValue(dkYedek);
    bas(YONETICI, "/organlar?tab=dk");
    await user.click(await screen.findByRole("button", { name: /Uydurcan Yedekoğlu/ }));
    await user.click(screen.getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    const pencere = screen.getByRole("dialog", { name: YEDEK_PENCERESI_BASLIGI });
    expect(within(pencere).queryByText(KARAR_YOK)).toBeNull();
    await user.click(within(pencere).getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    expect(organlarApiMock.dkYedekCagir).toHaveBeenCalledWith(23, null);
    expect(organlarApiMock.ykYedekCagir).not.toHaveBeenCalled();
  });

  it("Denetleme Kurulu üyesinin düşmesinde md. 7/2 ertelemesi sorulmaz", async () => {
    const user = userEvent.setup();
    bas(YONETICI, "/organlar?tab=dk");
    await user.click(await screen.findByRole("button", { name: /Uydurnaz Velioğlu/ }));
    await user.click(screen.getByRole("button", { name: DUGME_DUSUR }));
    const pencere = screen.getByRole("dialog", { name: DUSME_PENCERESI_BASLIGI });
    await user.selectOptions(within(pencere).getByLabelText(/Düşme türü/), "OGRENCI_AYRILDI");
    expect(within(pencere).queryByLabelText(/Olağanüstü genel kurula kadar sürsün/)).toBeNull();
  });

  it("Denetleme Kurulunda düşme ve yedek çağrısının yarım metni kurullu bağlamdadır", async () => {
    // Genel Bakış'ın "yarım kalan taslak" kalemi bağlamdan sekmeyi okur (backend pano.TASLAK_EKRANLARI).
    const user = userEvent.setup();
    const gerekceIster = () =>
      new ApiError(400, "gerekce_gerekli", "Bu kayıt için gerekçe yazılmalıdır. Uydurma ileti.");
    const dkYedek = uye(23, "Uydurcan Yedekoğlu", {
      organ: "DK",
      seat_group: "VELI",
      seat_type: "YEDEK",
      seat_order: 1,
    });
    organlarApiMock.kadro.mockImplementation(async (_d: number, organ: string) =>
      organ === "DK" ? { ...DK_KADRO, bekleyen_yedekler: [dkYedek] } : YK_KADRO,
    );
    organlarApiMock.dusur.mockRejectedValueOnce(gerekceIster()).mockResolvedValueOnce(BASKAN);
    organlarApiMock.dkYedekCagir
      .mockRejectedValueOnce(gerekceIster())
      .mockResolvedValueOnce(dkYedek);
    bas(YONETICI, "/organlar?tab=dk");

    await user.click(await screen.findByRole("button", { name: /Uydurnaz Velioğlu/ }));
    await user.click(screen.getByRole("button", { name: DUGME_DUSUR }));
    const dusme = screen.getByRole("dialog", { name: DUSME_PENCERESI_BASLIGI });
    await user.selectOptions(within(dusme).getByLabelText(/Düşme türü/), "OGRENCI_AYRILDI");
    await user.click(within(dusme).getByRole("button", { name: DUGME_DUSUR }));
    await user.type(await within(dusme).findByLabelText(/^Gerekçe/), "Uydurma gerekçe.");
    await user.click(within(dusme).getByRole("button", { name: "Gerekçeyle kaydet" }));
    await waitFor(() => expect(yarimMetinMock.temizle).toHaveBeenCalledWith("organlar.dusme.dk"));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    await user.click(screen.getByRole("button", { name: /Uydurcan Yedekoğlu/ }));
    await user.click(screen.getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    const yedek = screen.getByRole("dialog", { name: YEDEK_PENCERESI_BASLIGI });
    await user.click(within(yedek).getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    await user.type(await within(yedek).findByLabelText(/^Gerekçe/), "Uydurma gerekçe.");
    await user.click(within(yedek).getByRole("button", { name: "Gerekçeyle kaydet" }));
    await waitFor(() =>
      expect(yarimMetinMock.temizle).toHaveBeenCalledWith("organlar.yedek_cagrisi.dk"),
    );
    expect(yarimMetinMock.temizle).not.toHaveBeenCalledWith("organlar.dusme.yk");
    expect(yarimMetinMock.temizle).not.toHaveBeenCalledWith("organlar.yedek_cagrisi.yk");
  });

  it("yönetim kurulunda yedek çağrısının yarım metni kurullu bağlamdadır", async () => {
    // Genel Bakış'ın "yarım kalan taslak" kalemi bağlamdan sekmeyi okur (backend pano.TASLAK_EKRANLARI).
    const user = userEvent.setup();
    organlarApiMock.ykYedekCagir
      .mockRejectedValueOnce(
        new ApiError(400, "gerekce_gerekli", "Bu kayıt için gerekçe yazılmalıdır. Uydurma ileti."),
      )
      .mockResolvedValueOnce(YEDEK);
    bas(SEKRETER);

    await user.click(await screen.findByRole("button", { name: /Uydurhan Sınamacı/ }));
    await user.click(screen.getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    const yedek = screen.getByRole("dialog", { name: YEDEK_PENCERESI_BASLIGI });
    await user.click(within(yedek).getByRole("button", { name: DUGME_YEDEK_CAGIR }));
    await user.type(await within(yedek).findByLabelText(/^Gerekçe/), "Uydurma gerekçe.");
    await user.click(within(yedek).getByRole("button", { name: "Gerekçeyle kaydet" }));
    await waitFor(() =>
      expect(yarimMetinMock.temizle).toHaveBeenCalledWith("organlar.yedek_cagrisi.yk"),
    );
    expect(yarimMetinMock.temizle).not.toHaveBeenCalledWith("organlar.yedek_cagrisi.dk");
  });
});
