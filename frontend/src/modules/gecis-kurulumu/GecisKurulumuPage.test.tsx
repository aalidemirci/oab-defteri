// Geçiş Kurulumu ekranı (tasarım §7.9; plan F1c 8. adımın kararı ve notları; F1c-11): dönem yokken ilk
// birlik dönemi formu (ders yılı dönem başından önerilir, görev süresi uyarısı açılışı engellemez);
// görevdeki kurul (devralınan kayıt; gövde kurula göre kurulur; iptal gerekçeyle); seçilme sayısı beyanı
// (değişmeyen alan gitmez, "Bilinmiyor" tek gerekçeyle, verilmiş sayının düzeltmesi gerekçe ister); karar
// defteri (tasdik yoksa sunucu gerekçe ister, ikinci istek gerekçeyi taşır); "Geçiş kurulumu tamamlandı"
// onayla; işaretten sonra, salt okur rolde ve kural kopyası doğrulanamayan (D7) dönemde yazma denetimi
// yok, boş bölümler öğütsüz "girilmedi" cümlesi gösterir; "Bilinmiyor" beyanı uyum satırından okunur
// (yalnız kişinin satırı), iptal edilmiş ve programda kurulan üyelik ile temsilci sayaçta yok; değişiklik
// kalmayan beyan istek göndermez, yarım metni siler; birlik dönemi genel kurulla açıldıysa geçiş gerekmez.
// Veriler uydurmadır.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { BirlikDonemi, GecisOzeti } from "../birlik-donemi/api";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { YETENEK_ADLARI } from "../oturum/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { OrganUyeligi } from "./api";

const donemApiMock = vi.hoisted(() => ({
  donemler: vi.fn(),
  donem: vi.fn(),
  ilkDonemiAc: vi.fn(),
  donemiIptalEt: vi.fn(),
  gecis: vi.fn(),
}));
vi.mock("../birlik-donemi/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../birlik-donemi/api")>()),
  birlikDonemiApi: donemApiMock,
}));

const gecisApiMock = vi.hoisted(() => ({
  uyelikler: vi.fn(),
  devralinanEkle: vi.fn(),
  uyeligiIptalEt: vi.fn(),
  sayacBeyani: vi.fn(),
  kararDefteriKaydet: vi.fn(),
  kararDefteriniIptalEt: vi.fn(),
  tamamla: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  gecisApi: gecisApiMock,
}));

const kisiApiMock = vi.hoisted(() => ({ liste: vi.fn() }));
vi.mock("../kisiler/birlikKisileriApi", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../kisiler/birlikKisileriApi")>()),
  birlikKisileriApi: kisiApiMock,
}));

// Gerekçe kutusunun yarım metni (sunucu kaydı): ağ yok, taklit.
const yarimMetinMock = vi.hoisted(() => ({ oku: vi.fn(), kaydet: vi.fn(), temizle: vi.fn() }));
vi.mock("../uyum/api", () => ({ yarimMetinApi: yarimMetinMock }));

const okulApiMock = vi.hoisted(() => ({ listSchoolYears: vi.fn() }));
vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: okulApiMock,
}));

import { devralinanGovdesi } from "./DevralinanPenceresi";
import GecisKurulumuPage from "./GecisKurulumuPage";
import { beyanlar, duzeltmeMi } from "./SayacBeyaniPenceresi";
import {
  DEFTER_BOS,
  DEFTER_IPTAL_BASLIGI,
  DEVRALINAN_IPTAL_BASLIGI,
  DUGME_DEFTERI_KAYDET,
  DUGME_DONEMI_AC,
  DUGME_SAYAC_BEYANI,
  DUGME_TAMAMLA,
  DUGME_UYE_EKLE,
  GEREKMIYOR_NOTU,
  ILK_DONEM_BOS,
  KURUL_BOS,
  SAYAC_ACIKLAMASI,
  SAYAC_ACIKLAMASI_BILGI,
  SAYAC_KISI_YOK,
  SAYAC_PENCERESI_BASLIGI,
  TAMAMLA_ONAY_BASLIGI,
  UYE_PENCERESI_BASLIGI,
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

const OZET: GecisOzeti = {
  state: "SURUYOR",
  open_steps: ["sayac_beyani", "karar_defteri", "tamamla"],
  donem: DONEM,
  karar_defteri: null,
  gorev_suresi_uyarilari: [],
  uyum_satirlari: [],
};

const KISI: BirlikKisisi = {
  id: 7,
  kind: "VELI",
  first_name: "Uydurnur",
  last_name: "Örnekkaya",
  full_name: "Uydurnur Örnekkaya",
  is_parent: true,
  adult_declared: false,
  is_principal: false,
  personnel: null,
  external_yk_terms: 2,
  external_dk_chair_terms: null,
  status: "AKTIF",
};

const UYE: OrganUyeligi = {
  id: 11,
  term: 3,
  person: 7,
  person_name: "Uydurnur Örnekkaya",
  organ: "YK",
  role: "MUHASIP",
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
};

function bas(yetenekler: readonly string[] = YETENEK_ADLARI) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <GecisKurulumuPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  yarimMetinMock.oku.mockResolvedValue(null);
  yarimMetinMock.kaydet.mockResolvedValue(undefined);
  yarimMetinMock.temizle.mockResolvedValue(undefined);
  donemApiMock.gecis.mockResolvedValue(OZET);
  gecisApiMock.uyelikler.mockImplementation(async (_donem: number, organ: string) =>
    organ === "YK" ? [UYE] : [],
  );
  kisiApiMock.liste.mockResolvedValue([KISI]);
  okulApiMock.listSchoolYears.mockResolvedValue([
    { id: 1, name: "2026-2027", start_date: "2026-09-07", end_date: "2027-06-25", is_active: true },
  ]);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("gövdeler", () => {
  const temel = {
    kisi: 7,
    kurul: "YK" as const,
    koltuk: "ASIL" as const,
    grup: "VELI" as const,
    gorev: "SEKRETER" as const,
    kanal: "OGRETMENLER_KURULU" as const,
    temsil: "" as const,
    sira: "",
    gun: "",
    kanit: " Uydurma kanıt ",
    memNo: "",
  };

  it("devralınan kaydın gövdesi kurula ve koltuğa göredir", () => {
    expect(devralinanGovdesi(temel)).toEqual({
      organ: "YK",
      person: 7,
      seat_type: "ASIL",
      start_date: null,
      evidence_note: "Uydurma kanıt",
      role: "SEKRETER",
      seat_order: null,
      elected_by: "GENEL_KURUL",
    });
    // Yedeğe görev verilmez, sırası gider.
    expect(devralinanGovdesi({ ...temel, koltuk: "YEDEK", sira: "2" })).toMatchObject({
      role: "UYE",
      seat_order: 2,
    });
    // Denetleme Kurulunun öğretmen koltuğu: kanal ve MEM onay sayısı.
    expect(
      devralinanGovdesi({
        ...temel,
        kurul: "DK",
        grup: "OGRETMEN",
        kanal: "MEM_GOREVLENDIRME",
        memNo: " 123 ",
        gorev: "BASKAN",
      }),
    ).toMatchObject({
      organ: "DK",
      seat_group: "OGRETMEN",
      elected_by: "MEM_GOREVLENDIRME",
      mem_approval_no: "123",
      role: "BASKAN",
    });
    // Temsilci: yalnız temsil türü; görev ve kanal yok.
    const temsilci = devralinanGovdesi({ ...temel, kurul: "TEMSILCI", temsil: "KAMPUS_YONETIMI" });
    expect(temsilci).toEqual({
      organ: "TEMSILCI",
      person: 7,
      seat_type: "ASIL",
      start_date: null,
      evidence_note: "Uydurma kanıt",
      representation: "KAMPUS_YONETIMI",
    });
  });

  it("beyan listesi yalnız değişen alanları taşır; düzeltme yalnız verilmiş sayının değişmesidir", () => {
    const satirlar = [
      { kisi: 1, ad: "A", yk: true, dk: false, ykDegeri: "2", dkDegeri: "" },
      { kisi: 2, ad: "B", yk: true, dk: true, ykDegeri: "", dkDegeri: "?" },
    ];
    expect(beyanlar(satirlar, { 1: { yk: "2", dk: "" }, 2: { yk: "", dk: "?" } })).toEqual([]);
    expect(beyanlar(satirlar, { 1: { yk: "?", dk: "1" }, 2: { yk: "0", dk: "1" } })).toEqual([
      { person: 1, yk: null },
      { person: 2, yk: 0, dk_baskanlik: 1 },
    ]);
    expect(duzeltmeMi("2", "?")).toBe(true);
    expect(duzeltmeMi("2", "3")).toBe(true);
    expect(duzeltmeMi("?", "3")).toBe(false);
    expect(duzeltmeMi("", "3")).toBe(false);
    expect(duzeltmeMi("2", "")).toBe(false);
  });
});

describe("GecisKurulumuPage", () => {
  it("dönem yokken ilk birlik dönemi açılır: ders yılı ve ad dönem başından önerilir", async () => {
    const user = userEvent.setup();
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      state: "BASLAMADI",
      open_steps: ["donem"],
      donem: null,
    });
    donemApiMock.ilkDonemiAc.mockResolvedValue({ ...DONEM, uyarilar: [] });
    bas();
    const dugme = await screen.findByRole("button", { name: DUGME_DONEMI_AC });
    // Zorunlu alanlar boşken istek gitmez.
    await user.click(dugme);
    expect(screen.getByText("Son olağan genel kurulun günü zorunludur.")).toBeInTheDocument();
    expect(donemApiMock.ilkDonemiAc).not.toHaveBeenCalled();
    await waitFor(() => expect(okulApiMock.listSchoolYears).toHaveBeenCalled());
    await user.type(screen.getByLabelText(/Son olağan genel kurulun günü/), "2026-10-10");
    expect(screen.getByLabelText(/Birlik döneminin adı/)).toHaveValue("2026-2027 birlik dönemi");
    await user.click(dugme);
    expect(donemApiMock.ilkDonemiAc).toHaveBeenCalledWith({
      name: "2026-2027 birlik dönemi",
      school_year: 1,
      start_date: "2026-10-10",
      program_start_date: null,
    });
    await waitFor(() => expect(donemApiMock.gecis).toHaveBeenCalledTimes(2));
  });

  it("görevdeki kurul listelenir; üye eklenir ve kayıt gerekçeyle iptal edilir", async () => {
    const user = userEvent.setup();
    gecisApiMock.devralinanEkle.mockResolvedValue(UYE);
    gecisApiMock.uyeligiIptalEt.mockResolvedValue({ ...UYE, status: "IPTAL" });
    bas();
    const tablo = await screen.findByRole("table", { name: "Görevdeki Kurul" });
    expect(within(tablo).getByText("Muhasip")).toBeInTheDocument();
    expect(within(tablo).getByText("Yönetim kurulu")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: DUGME_UYE_EKLE }));
    const pencere = screen.getByRole("dialog", { name: UYE_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Kişiyi seçin.")).toBeInTheDocument();
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Örnekkaya/ }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gecisApiMock.devralinanEkle).toHaveBeenCalledWith(
      expect.objectContaining({ organ: "YK", person: 7, role: "UYE", seat_type: "ASIL" }),
    );
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    await user.click(await screen.findByRole("button", { name: "Uydurnur Örnekkaya İptal et" }));
    const iptal = screen.getByRole("dialog", { name: DEVRALINAN_IPTAL_BASLIGI });
    await user.type(within(iptal).getByLabelText(/İptal gerekçesi/), "Uydurma yanlış kayıt.");
    await user.click(within(iptal).getByRole("button", { name: "İptal et" }));
    expect(gecisApiMock.uyeligiIptalEt).toHaveBeenCalledWith(11, "Uydurma yanlış kayıt.");
  });

  it("devralınan kayıt sert engelde atfıyla reddedilir", async () => {
    const user = userEvent.setup();
    gecisApiMock.devralinanEkle.mockRejectedValue(
      new ApiError(400, "invalid", "Okul müdürü yönetim kuruluna giremez (md. 12/1)."),
    );
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_UYE_EKLE }));
    const pencere = screen.getByRole("dialog", { name: UYE_PENCERESI_BASLIGI });
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur/ }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    const bant = await within(pencere).findByRole("alert");
    expect(bant).toHaveTextContent("Kayıt yapılmadı");
    expect(bant).toHaveTextContent("Dayanak: md. 12/1");
  });

  it("seçilme sayısı: düzeltme gerekçesi ister, bilinmiyor tek gerekçeyle yazılır", async () => {
    const user = userEvent.setup();
    gecisApiMock.sayacBeyani
      .mockRejectedValueOnce(
        new ApiError(
          400,
          "gerekce_gerekli",
          "Bu kayıt için gerekçe yazılmalıdır. Programdan önceki yönetim kurulu seçilme sayısı bilinmiyor (md. 12/4).",
        ),
      )
      .mockResolvedValueOnce({ kisiler: [KISI], bilinmeyen_sayisi: 1 });
    bas();
    expect(await screen.findByText("Yönetim kurulu: 2")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_SAYAC_BEYANI }));
    const pencere = screen.getByRole("dialog", { name: SAYAC_PENCERESI_BASLIGI });
    const secici = within(pencere).getByRole("combobox", {
      name: /Yönetim kuruluna seçilme sayısı/,
    });
    // Değeri olan alanda etkisiz "Girilmedi" seçeneği yoktur.
    expect(within(secici).queryByRole("option", { name: "Girilmedi" })).toBeNull();
    await user.selectOptions(secici, "?");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Düzeltme gerekçesi yazın.")).toBeInTheDocument();
    expect(gecisApiMock.sayacBeyani).not.toHaveBeenCalled();
    await user.type(
      within(pencere).getByLabelText(/Düzeltme gerekçesi/),
      "Uydurma: yeniden sayıldı.",
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gecisApiMock.sayacBeyani).toHaveBeenLastCalledWith({
      beyanlar: [{ person: 7, yk: null }],
      duzeltme_gerekcesi: "Uydurma: yeniden sayıldı.",
    });
    expect(await within(pencere).findByText("Bu kayıt gerekçe istiyor")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText(/^Gerekçe/), "Uydurma: defter kayıp.");
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(gecisApiMock.sayacBeyani).toHaveBeenLastCalledWith({
      beyanlar: [{ person: 7, yk: null }],
      gerekce: "Uydurma: defter kayıp.",
      duzeltme_gerekcesi: "Uydurma: yeniden sayıldı.",
    });
    expect(await screen.findByText("Seçilme sayıları kaydedildi.")).toBeInTheDocument();
    // Kayıt yapıldı: gerekçenin yarım metni (yalnız bu kutunun bağlamıyla) silinir.
    expect(yarimMetinMock.temizle).toHaveBeenCalledWith("gecis.sayac_beyani");
  });

  it("seçilme sayısı: değişiklik kalmayınca istek gitmez, yarım metin silinir, pencere kapanır", async () => {
    const user = userEvent.setup();
    kisiApiMock.liste.mockResolvedValue([{ ...KISI, external_yk_terms: null }]);
    gecisApiMock.sayacBeyani.mockRejectedValueOnce(
      new ApiError(
        400,
        "gerekce_gerekli",
        "Bu kayıt için gerekçe yazılmalıdır. Programdan önceki yönetim kurulu seçilme sayısı bilinmiyor (md. 12/4).",
      ),
    );
    bas();
    expect(await screen.findByText("Yönetim kurulu: Girilmedi")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_SAYAC_BEYANI }));
    const pencere = screen.getByRole("dialog", { name: SAYAC_PENCERESI_BASLIGI });
    const secici = within(pencere).getByRole("combobox", {
      name: /Yönetim kuruluna seçilme sayısı/,
    });
    // Değeri girilmemiş alanda "Girilmedi" başlangıç değeridir.
    expect(secici).toHaveValue("");
    await user.selectOptions(secici, "?");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    await user.type(await within(pencere).findByLabelText(/^Gerekçe/), "Uydurma yarım gerekçe");
    // Seçim geri alınır: gönderilecek değişiklik yok.
    await user.selectOptions(secici, "");
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(gecisApiMock.sayacBeyani).toHaveBeenCalledTimes(1);
    expect(yarimMetinMock.temizle).toHaveBeenCalledWith("gecis.sayac_beyani");
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("seçilme sayısı: Bilinmiyor uyum satırından okunur; iptal, program ve temsilci kaydı sayaçta yok", async () => {
    const user = userEvent.setup();
    const kisi = (id: number, ad: string): BirlikKisisi => ({
      ...KISI,
      id,
      first_name: ad,
      full_name: `${ad} Örnekkaya`,
      external_yk_terms: null,
    });
    kisiApiMock.liste.mockResolvedValue([
      { ...KISI, external_yk_terms: null },
      kisi(9, "Uydurhan"),
      kisi(10, "Uydurcan"),
      kisi(11, "Uydurgül"),
      kisi(12, "Uydurnaz"),
    ]);
    const uye = (
      id: number,
      person: number,
      ad: string,
      ek: Partial<OrganUyeligi> = {},
    ): OrganUyeligi => ({
      ...UYE,
      id,
      person,
      person_name: `${ad} Örnekkaya`,
      role: "UYE",
      ...ek,
    });
    gecisApiMock.uyelikler.mockImplementation(async (_donem: number, organ: string) => {
      if (organ === "YK") {
        return [
          UYE,
          uye(13, 9, "Uydurhan"),
          uye(14, 10, "Uydurcan", { status: "IPTAL" }),
          uye(15, 11, "Uydurgül", { source: "PROGRAM" }),
        ];
      }
      if (organ === "TEMSILCI") {
        return [
          uye(16, 12, "Uydurnaz", { organ: "TEMSILCI", representation: "KONTENJAN_KOMISYONU" }),
        ];
      }
      return [];
    });
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      uyum_satirlari: [
        {
          id: 2,
          tur: "SAPMA",
          konu_turu: "oab.OabPerson",
          konu: "7",
          metin: "Programdan önceki yönetim kurulu seçilme sayısı bilinmiyor.",
          atif: "md. 12/4",
          gerekceli: true,
          sayac_alani: "yk",
        },
        // Tuzak: aynı alan ve 9 numaralı konu, ama kişinin değil defterin satırı.
        {
          id: 3,
          tur: "SAPMA",
          konu_turu: "oab.OfficialBook",
          konu: "9",
          metin: "Uydurma defter satırı.",
          atif: "md. 23/2",
          gerekceli: true,
          sayac_alani: "yk",
        },
      ],
    });
    bas();
    expect(await screen.findByText("Yönetim kurulu: Bilinmiyor")).toBeInTheDocument();
    expect(screen.getByText("Yönetim kurulu: Girilmedi")).toBeInTheDocument();
    const tablo = screen.getByRole("table", { name: "Görevdeki Kurul" });
    expect(within(tablo).queryByText("Uydurcan Örnekkaya")).toBeNull();
    expect(within(tablo).queryByText("Uydurgül Örnekkaya")).toBeNull();
    expect(within(tablo).getByText("Uydurnaz Örnekkaya")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Uydurcan Örnekkaya İptal et" })).toBeNull();
    // Temsilci görevdeki kurul tablosunda var, seçilme sayıları listesinde yok.
    expect(screen.getAllByText("Uydurnaz Örnekkaya")).toHaveLength(1);
    expect(screen.queryByText("Uydurcan Örnekkaya")).toBeNull();
    expect(screen.queryByText("Uydurgül Örnekkaya")).toBeNull();

    gecisApiMock.sayacBeyani.mockResolvedValue({ kisiler: [KISI], bilinmeyen_sayisi: 0 });
    await user.click(screen.getByRole("button", { name: DUGME_SAYAC_BEYANI }));
    const pencere = screen.getByRole("dialog", { name: SAYAC_PENCERESI_BASLIGI });
    expect(
      within(pencere).getAllByRole("combobox", { name: /Yönetim kuruluna seçilme sayısı/ }),
    ).toHaveLength(2);
    const bilinmeyen = within(pencere).getByRole("combobox", {
      name: "Uydurnur Örnekkaya: Yönetim kuruluna seçilme sayısı",
    });
    expect(bilinmeyen).toHaveValue("?");
    // "Bilinmiyor"dan sayıya geçiş düzeltme değildir: düzeltme gerekçesi sorulmaz.
    await user.selectOptions(bilinmeyen, "3");
    expect(within(pencere).queryByLabelText(/Düzeltme gerekçesi/)).toBeNull();
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gecisApiMock.sayacBeyani).toHaveBeenCalledWith({ beyanlar: [{ person: 7, yk: 3 }] });
    expect(await screen.findByText("Seçilme sayıları kaydedildi.")).toBeInTheDocument();
  });

  it("karar defteri: tasdik yoksa gerekçe istenir; kayıt sonrası bilgiler ve tasdik uyarısı görünür", async () => {
    const user = userEvent.setup();
    gecisApiMock.kararDefteriKaydet
      .mockRejectedValueOnce(
        new ApiError(
          400,
          "gerekce_gerekli",
          "Bu kayıt için gerekçe yazılmalıdır. Yönetim kurulu karar defterinin noterce tasdik edilmesi zorunludur (md. 23/2).",
        ),
      )
      .mockResolvedValueOnce({});
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_DEFTERI_KAYDET }));
    expect(screen.getByText("Son karar sıra no'su zorunludur.")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/Programdan önceki son karar sıra no'su/), "37");
    await user.type(screen.getByLabelText(/Programdan önceki son sayfa/), "12");
    await user.click(screen.getByRole("button", { name: DUGME_DEFTERI_KAYDET }));
    expect(gecisApiMock.kararDefteriKaydet).toHaveBeenLastCalledWith(
      expect.objectContaining({ last_no_before_program: 37, last_page_before_program: 12 }),
    );
    expect(await screen.findByText("Dayanak: md. 23/2")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/^Gerekçe/), "Uydurma: tasdik bilgisi elde değil.");
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      karar_defteri: {
        id: 4,
        status: "KULLANIMDA",
        certified_by: "",
        certified_on: null,
        certification_no: "",
        page_count: null,
        opened_on: null,
        last_no_before_program: 37,
        last_page_before_program: 12,
      },
      uyum_satirlari: [
        {
          id: 1,
          tur: "SAPMA",
          konu_turu: "oab.OfficialBook",
          konu: "4",
          metin: "Yönetim kurulu karar defterinin noterce tasdik edilmesi zorunludur.",
          atif: "md. 23/2",
          gerekceli: true,
          sayac_alani: "",
        },
      ],
    });
    await user.click(screen.getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(gecisApiMock.kararDefteriKaydet).toHaveBeenLastCalledWith(
      expect.objectContaining({ gerekce: "Uydurma: tasdik bilgisi elde değil." }),
    );
    const liste = await screen.findByRole("list", { name: "Karar defterinin tasdik uyarısı" });
    expect(liste).toHaveTextContent("Sapma");
    expect(screen.getByText("37")).toBeInTheDocument();

    gecisApiMock.kararDefteriniIptalEt.mockResolvedValue({});
    await user.click(screen.getAllByRole("button", { name: "İptal et" }).at(-1)!);
    const iptal = screen.getByRole("dialog", { name: DEFTER_IPTAL_BASLIGI });
    await user.type(within(iptal).getByLabelText(/İptal gerekçesi/), "Uydurma: sayfa yanlış.");
    await user.click(within(iptal).getByRole("button", { name: "İptal et" }));
    expect(gecisApiMock.kararDefteriniIptalEt).toHaveBeenCalledWith(4, "Uydurma: sayfa yanlış.");
  });

  it("tamamlama onay ister, eksik adımları söyler; işaretten sonra ekran salt okunurdur", async () => {
    const user = userEvent.setup();
    gecisApiMock.tamamla.mockResolvedValue({ ...DONEM, transition_completed_on: "2026-11-11" });
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_TAMAMLA }));
    const onay = screen.getByRole("dialog", { name: TAMAMLA_ONAY_BASLIGI });
    expect(onay).toHaveTextContent(
      "Eksik adımlar: programdan önceki seçilme sayıları, karar defteri.",
    );
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      state: "TAMAMLANDI",
      open_steps: [],
      donem: { ...DONEM, transition_completed_on: "2026-11-11" },
    });
    await user.click(within(onay).getByRole("button", { name: "Tamamlandı olarak işaretle" }));
    expect(gecisApiMock.tamamla).toHaveBeenCalled();
    expect(await screen.findByText(/11\.11\.2026 günü tamamlandı/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_UYE_EKLE })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_TAMAMLA })).toBeNull();
    expect(screen.queryByRole("button", { name: /İptal et/ })).toBeNull();
    // Defter girilmeden işaretlendi: bölüm boş kalmaz; öğüt cümlesi düşer.
    expect(screen.getByText(DEFTER_BOS)).toBeInTheDocument();
    expect(screen.queryByText(SAYAC_ACIKLAMASI)).toBeNull();
    expect(screen.getByText(SAYAC_ACIKLAMASI_BILGI)).toBeInTheDocument();
  });

  it("D7: kural kopyası doğrulanamayan açık geçiş döneminde bant var, yazma denetimi yok", async () => {
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      donem: { ...DONEM, kural_kopyasi_tutuyor: false },
    });
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(KURAL_KOPYASI_BOZUK);
    expect(await screen.findByRole("table", { name: "Görevdeki Kurul" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_UYE_EKLE })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_SAYAC_BEYANI })).toBeNull();
    expect(screen.queryByRole("button", { name: /İptal et/ })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_DEFTERI_KAYDET })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_TAMAMLA })).toBeNull();
    expect(screen.getByText(DEFTER_BOS)).toBeInTheDocument();
  });

  it("tamamlama reddedilirse kilit bandı görünür", async () => {
    const user = userEvent.setup();
    gecisApiMock.tamamla.mockRejectedValue(
      new ApiError(
        409,
        "gecis_kapali",
        "Geçiş kurulumu tamamlandı; geçiş kayıtları artık eklenemez.",
      ),
    );
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_TAMAMLA }));
    await user.click(screen.getByRole("button", { name: "Tamamlandı olarak işaretle" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Bu kayıt yazılamaz");
  });

  it("salt okur rolde yazma denetimi yok", async () => {
    bas(["son_oturum_onay"]);
    expect(await screen.findByRole("table", { name: "Görevdeki Kurul" })).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("yalnız okuma");
    expect(screen.queryByRole("button", { name: DUGME_UYE_EKLE })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_SAYAC_BEYANI })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_DEFTERI_KAYDET })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_TAMAMLA })).toBeNull();
    // Yazmayı öğütleyen cümleler düşer; boş bölümde öğütsüz cümle.
    expect(screen.queryByText(SAYAC_ACIKLAMASI)).toBeNull();
    expect(screen.getByText(SAYAC_ACIKLAMASI_BILGI)).toBeInTheDocument();
    expect(screen.getByText(DEFTER_BOS)).toBeInTheDocument();
  });

  it("salt okur rolde boş kurulda seçilme sayıları da öğütsüz cümle gösterir", async () => {
    gecisApiMock.uyelikler.mockResolvedValue([]);
    bas(["son_oturum_onay"]);
    // Görevdeki Kurul ve Seçilme Sayıları bölümleri aynı öğütsüz cümleyi gösterir.
    await waitFor(() => expect(screen.getAllByText(KURUL_BOS)).toHaveLength(2));
    expect(screen.queryByText(SAYAC_KISI_YOK)).toBeNull();
  });

  it("salt okur rolde dönem yokken form yok, öğütsüz cümle var", async () => {
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      state: "BASLAMADI",
      open_steps: ["donem"],
      donem: null,
    });
    bas(["son_oturum_onay"]);
    expect(await screen.findByText(ILK_DONEM_BOS)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_DONEMI_AC })).toBeNull();
  });

  it("birlik dönemi genel kurulla açıldıysa geçiş gerekmez", async () => {
    donemApiMock.gecis.mockResolvedValue({
      ...OZET,
      state: "GEREKMIYOR",
      open_steps: [],
      donem: null,
    });
    bas();
    expect(await screen.findByText(GEREKMIYOR_NOTU)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_DONEMI_AC })).toBeNull();
  });

  it("okunamazsa hata bandı", async () => {
    donemApiMock.gecis.mockRejectedValue(new Error("ağ"));
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Geçiş kurulumunun durumu okunamadı.",
    );
  });
});
