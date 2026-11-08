// Kişiler → Veli Listesi (T5; genel tasarım §8.4): özet yalnız sınıf başına sayıdır, aktarım
// önizle → aktar akışıyla yürür (Aktar önizlemeden önce kapalı), önizleme ve sonuç ad
// göstermez, aktarılamayan satırlar numarası ve nedeniyle görünür, aydınlatma metni dosya
// seçiminin üstündedir, "Veli listesini sil" onay ister. Hata dalları AktarimPaneli'ninkiyle
// aynı desendir: sunucunun Türkçe iletisi olduğu gibi, gövdesiz retde ekranın metni, 409
// `parola_gerekli`de kurulum yönlendirmesi; sınırı aşan dosya uca gitmez. Veriler uydurmadır (KVKK).

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";
import { saveBlob } from "../../lib/download";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { ParentImportReport, ParentRosterSummary } from "../okul/api";
import type { OturumOzeti } from "../oturum/api";
import { OTURUM_SORGU_ANAHTARI } from "../oturum/useOturum";
import {
  AKTARILAMAYAN_SATIR_YOK,
  AYDINLATMA_BASLIGI,
  KAYNAK_DOSYA_HATIRLATMASI,
  ONIZLEME_YAPILAMADI,
  SABLON_INDIRILEMEDI,
  VELI_AKTARILAMADI,
  VELI_AKTARILDI,
  VELI_AYDINLATMA_AMACI,
  VELI_DOSYA_ALANI_ETIKETI,
  VELI_LISTESI_BOS,
  VELI_LISTESI_OKUNAMADI,
  VELI_LISTESINI_SIL,
  VELI_SILINEMEDI,
  VELI_SILME_ONAY_BASLIGI,
} from "./metinler";

const okulApiMock = vi.hoisted(() => ({
  getSchoolConfig: vi.fn(),
  getParentRoster: vi.fn(),
  deleteParentRoster: vi.fn(),
  previewParentImport: vi.fn(),
  commitParentImport: vi.fn(),
  parentTemplate: vi.fn(),
}));

vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: okulApiMock,
}));

vi.mock("../../lib/download", () => ({ saveBlob: vi.fn() }));

import VeliListesi from "./VeliListesi";

const BOS: ParentRosterSummary = {
  total_rows: 0,
  class_count: 0,
  last_import_at: null,
  classes: [],
};

const DOLU: ParentRosterSummary = {
  total_rows: 3,
  class_count: 2,
  last_import_at: "2026-11-08T10:15:00+03:00",
  classes: [
    { student_class: "9-A", rows: 2 },
    { student_class: "10-B", rows: 1 },
  ],
};

const ONIZLEME: ParentImportReport = {
  file_hash: "abc",
  file_name: "veli.xlsx",
  total_rows: 4,
  imported_rows: 3,
  class_count: 2,
  replaced_rows: 2,
  kept_class_count: 1,
  kept_rows: 1,
  already_imported: false,
  dry_run: true,
  classes: [
    { student_class: "9-A", rows: 2, replaced_rows: 2 },
    { student_class: "11-C", rows: 1, replaced_rows: 0 },
  ],
  issues: [
    {
      row_number: 5,
      field: "student_class",
      issue: "Öğrencinin sınıfı boş; satır aktarılmadı.",
    },
  ],
};

function kur() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData<OturumOzeti>(OTURUM_SORGU_ANAHTARI, {
    durum: "acik",
    hesap: null,
    bosta_dk: 10,
    bosta_kalan_sn: 600,
    kilit_bekliyor: false,
    kurulum_tamam: true,
    yukleme_siniri_mb: 20,
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <VeliListesi />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function dosya(boy?: number): File {
  const sahte = new File(["uydurma"], "veli.xlsx", {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  if (boy !== undefined) Object.defineProperty(sahte, "size", { value: boy });
  return sahte;
}

const MB = 1024 * 1024;

/** Gövdesiz ret: istemci genel iletiyi koyar, ekran kendi metnini gösterir (`hataOku`). */
const GOVDESIZ_RET = new ApiError(500, "500", BEKLENMEYEN_HATA_ILETISI);

beforeEach(() => {
  vi.mocked(saveBlob).mockResolvedValue("kaydedildi");
  okulApiMock.getSchoolConfig.mockResolvedValue({
    ...ORNEK_OKUL_KARTI,
    data_controller_text: "Örnek Anadolu Lisesi Müdürlüğü",
  });
  okulApiMock.getParentRoster.mockResolvedValue(BOS);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("VeliListesi — özet", () => {
  it("boş listede boş durum; silme düğmesi yok", async () => {
    kur();
    expect(await screen.findByText(VELI_LISTESI_BOS)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: VELI_LISTESINI_SIL })).toBeNull();
  });

  it("sınıf başına sayı tablosu; ad listesi yoktur", async () => {
    okulApiMock.getParentRoster.mockResolvedValue(DOLU);
    kur();

    const tablo = await screen.findByRole("table", { name: /sınıf başına satır sayısı/ });
    const satirlar = within(tablo).getAllByRole("row");
    expect(satirlar.map((s) => s.textContent)).toEqual(["SınıfSatır (öğrenci)", "9-A2", "10-B1"]);
    expect(screen.getByText(/3 satır · 2 sınıf · son aktarım 08\.11\.2026/)).toBeInTheDocument();
  });

  it("Veli listesini sil: onaydan sonra silinir ve özet yenilenir", async () => {
    okulApiMock.getParentRoster.mockResolvedValueOnce(DOLU).mockResolvedValue(BOS);
    okulApiMock.deleteParentRoster.mockResolvedValue({ deleted_rows: 3 });
    const user = userEvent.setup();
    kur();

    await user.click(await screen.findByRole("button", { name: VELI_LISTESINI_SIL }));
    const onay = await screen.findByRole("dialog", { name: VELI_SILME_ONAY_BASLIGI });
    expect(onay).toHaveTextContent("geri alınamaz");
    await user.click(within(onay).getByRole("button", { name: VELI_LISTESINI_SIL }));

    await waitFor(() => expect(okulApiMock.deleteParentRoster).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Veli listesi silindi (3 satır).")).toBeInTheDocument();
    expect(await screen.findByText(VELI_LISTESI_BOS)).toBeInTheDocument();
  });

  it("özet okunamazsa sunucunun iletisi, gövdesiz retde ekranın metni çıkar", async () => {
    okulApiMock.getParentRoster.mockRejectedValueOnce(
      new ApiError(403, "yetki_yok", "Bu işlem için yetkiniz yok.", {}),
    );
    const { unmount } = kur();
    expect(await screen.findByRole("alert")).toHaveTextContent("Bu işlem için yetkiniz yok.");
    expect(screen.queryByText(VELI_LISTESI_BOS)).toBeNull();
    unmount();

    okulApiMock.getParentRoster.mockRejectedValueOnce(GOVDESIZ_RET);
    kur();
    expect(await screen.findByRole("alert")).toHaveTextContent(VELI_LISTESI_OKUNAMADI);
    expect(screen.queryByText(BEKLENMEYEN_HATA_ILETISI)).toBeNull();
  });

  it("silinemezse ileti görünür, başarı bildirimi çıkmaz ve özet kalır", async () => {
    okulApiMock.getParentRoster.mockResolvedValue(DOLU);
    okulApiMock.deleteParentRoster.mockRejectedValue(GOVDESIZ_RET);
    const user = userEvent.setup();
    kur();

    await user.click(await screen.findByRole("button", { name: VELI_LISTESINI_SIL }));
    const onay = await screen.findByRole("dialog", { name: VELI_SILME_ONAY_BASLIGI });
    await user.click(within(onay).getByRole("button", { name: VELI_LISTESINI_SIL }));

    expect(await screen.findByRole("alert")).toHaveTextContent(VELI_SILINEMEDI);
    expect(screen.queryByText(/Veli listesi silindi/)).toBeNull();
    expect(okulApiMock.getParentRoster).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("table", { name: /sınıf başına satır sayısı/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: VELI_LISTESINI_SIL })).toBeEnabled();
  });

  it("silme onayından vazgeçilirse uç çağrılmaz", async () => {
    okulApiMock.getParentRoster.mockResolvedValue(DOLU);
    const user = userEvent.setup();
    kur();

    await user.click(await screen.findByRole("button", { name: VELI_LISTESINI_SIL }));
    await user.click(await screen.findByRole("button", { name: "Vazgeç" }));
    expect(okulApiMock.deleteParentRoster).not.toHaveBeenCalled();
  });
});

describe("VeliListesi — aktarım", () => {
  it("aydınlatma metni dosya seçiminin üstündedir", async () => {
    kur();
    const metin = await screen.findByRole("region", { name: AYDINLATMA_BASLIGI });
    const dosyaAlani = screen.getByLabelText(VELI_DOSYA_ALANI_ETIKETI);
    expect(metin).toHaveTextContent(VELI_AYDINLATMA_AMACI.slice(0, 40));
    expect(
      metin.compareDocumentPosition(dosyaAlani) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    // Veli listesinde pano yolu yoktur.
    expect(screen.queryByLabelText(/yapıştırın/)).toBeNull();
  });

  it("önizle → aktar: yalnız sayılar ve satır sorunları; Aktar önizlemeden önce kapalı", async () => {
    okulApiMock.previewParentImport.mockResolvedValue(ONIZLEME);
    okulApiMock.commitParentImport.mockResolvedValue({ ...ONIZLEME, dry_run: false });
    const user = userEvent.setup();
    kur();

    expect(await screen.findByRole("button", { name: "Aktar" })).toBeDisabled();
    await user.upload(screen.getByLabelText(VELI_DOSYA_ALANI_ETIKETI), dosya());
    await user.click(screen.getByRole("button", { name: "Önizle" }));

    expect(await screen.findByText("Önizleme — hiçbir kayıt yazılmadı")).toBeInTheDocument();
    expect(okulApiMock.previewParentImport).toHaveBeenCalledWith(expect.any(File));
    const sinifTablosu = screen.getByRole("table", { name: "Dosyadaki sınıflar" });
    expect(
      within(sinifTablosu)
        .getAllByRole("row")
        .map((s) => s.textContent),
    ).toEqual(["SınıfDosyadaki satırSilinecek eski satır", "9-A22", "11-C10"]);
    expect(screen.getByText("Öğrencinin sınıfı boş; satır aktarılmadı.")).toBeInTheDocument();
    expect(screen.getByText("Öğrencinin sınıfı")).toBeInTheDocument();
    expect(screen.queryByText(KAYNAK_DOSYA_HATIRLATMASI)).toBeNull();

    await user.click(screen.getByRole("button", { name: "Aktar" }));
    expect(await screen.findByText("Aktarım sonucu")).toBeInTheDocument();
    expect(okulApiMock.commitParentImport).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("Veli listesi aktarıldı.")).toBeInTheDocument();
    // Dosyayla aktarım bitti: kaynak dosyanın silinmesi hatırlatılır (tasarım §4.3 tehdit 15).
    expect(screen.getByRole("note")).toHaveTextContent(KAYNAK_DOSYA_HATIRLATMASI);
    // Özet yeniden okunur.
    await waitFor(() => expect(okulApiMock.getParentRoster).toHaveBeenCalledTimes(2));
  });

  it("aktarılamayan satır sayısı kutuyla aynıdır; başlık uyarıları ayrı tablodadır", async () => {
    okulApiMock.previewParentImport.mockResolvedValue({
      ...ONIZLEME,
      total_rows: 4,
      imported_rows: 2,
      issues: [
        {
          row_number: 1,
          field: "header",
          issue:
            "“Sınıf” sütunu da “Öğrencinin sınıfı” alanına uyuyor; ilk uyan sütun kullanıldı, " +
            "bu sütun okunmadı.",
        },
        { row_number: 3, field: "full_name", issue: "Velinin adı-soyadı boş; satır aktarılmadı." },
        {
          row_number: 3,
          field: "student_class",
          issue: "Öğrencinin sınıfı boş; satır aktarılmadı.",
        },
        {
          row_number: 5,
          field: "student_class",
          issue: "Öğrencinin sınıfı boş; satır aktarılmadı.",
        },
      ],
    });
    const user = userEvent.setup();
    kur();
    await user.upload(await screen.findByLabelText(VELI_DOSYA_ALANI_ETIKETI), dosya());
    await user.click(screen.getByRole("button", { name: "Önizle" }));

    const kutu = (await screen.findByText("Aktarılamayan")).parentElement as HTMLElement;
    expect(within(kutu).getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Aktarılamayan satırlar (2)")).toBeInTheDocument();
    expect(screen.getByText("Başlık uyarıları (1)")).toBeInTheDocument();
    expect(screen.getByText("Başlık")).toBeInTheDocument();
    expect(screen.queryByText(/student_class|full_name/)).toBeNull();
  });

  it("aktarılamayan satır yoksa boş durum; başlık uyarısı yoksa tablosu çizilmez", async () => {
    okulApiMock.previewParentImport.mockResolvedValue({
      ...ONIZLEME,
      total_rows: 3,
      imported_rows: 3,
      issues: [],
    });
    const user = userEvent.setup();
    kur();
    await user.upload(await screen.findByLabelText(VELI_DOSYA_ALANI_ETIKETI), dosya());
    await user.click(screen.getByRole("button", { name: "Önizle" }));

    expect(await screen.findByText("Aktarılamayan satırlar (0)")).toBeInTheDocument();
    expect(screen.getByText(AKTARILAMAYAN_SATIR_YOK)).toBeInTheDocument();
    expect(screen.queryByText(/Başlık uyarıları/)).toBeNull();
  });

  it("dosya seçilmeden önizleme istenirse uyarır, uca gitmez", async () => {
    const user = userEvent.setup();
    kur();
    await user.click(await screen.findByRole("button", { name: "Önizle" }));
    expect(await screen.findByText("Önce bir dosya seçin.")).toBeInTheDocument();
    expect(okulApiMock.previewParentImport).not.toHaveBeenCalled();
  });

  it("şablon indirilir", async () => {
    okulApiMock.parentTemplate.mockResolvedValue(new Blob(["x"]));
    const user = userEvent.setup();
    kur();
    await user.click(await screen.findByRole("button", { name: "Şablon indir" }));
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(expect.any(Blob), "sablon-veli-listesi.xlsx"),
    );
  });
});

describe("VeliListesi — aktarım hataları", () => {
  async function dosyaSecVeOnizle(user: ReturnType<typeof userEvent.setup>, secilen = dosya()) {
    await user.upload(await screen.findByLabelText(VELI_DOSYA_ALANI_ETIKETI), secilen);
    await user.click(screen.getByRole("button", { name: "Önizle" }));
  }

  it("önizlemenin 400'ü sunucunun Türkçe iletisiyle gösterilir; Aktar kapalı kalır", async () => {
    const ileti =
      "Makro içeren dosya kabul edilmez. Dosyayı Excel'de “Excel Çalışma Kitabı (*.xlsx)” " +
      "olarak kaydedip yeniden yükleyin.";
    okulApiMock.previewParentImport.mockRejectedValue(new ApiError(400, "invalid", ileti, {}));
    const user = userEvent.setup();
    kur();
    await dosyaSecVeOnizle(user);

    expect(await screen.findByRole("alert")).toHaveTextContent(ileti);
    expect(screen.queryByText("Önizleme — hiçbir kayıt yazılmadı")).toBeNull();
    expect(screen.getByRole("button", { name: "Aktar" })).toBeDisabled();
  });

  it("önizlemenin gövdesiz reddinde ekranın metni çıkar", async () => {
    okulApiMock.previewParentImport.mockRejectedValue(GOVDESIZ_RET);
    const user = userEvent.setup();
    kur();
    await dosyaSecVeOnizle(user);

    expect(await screen.findByRole("alert")).toHaveTextContent(ONIZLEME_YAPILAMADI);
  });

  it("409 parola_gerekli önizlemede kurulum sihirbazına yönlendirir", async () => {
    okulApiMock.previewParentImport.mockRejectedValue(
      new ApiError(
        409,
        "parola_gerekli",
        "Kişi kaydı için önce program yöneticisi hesabını kurun.",
      ),
    );
    const user = userEvent.setup();
    kur();
    await dosyaSecVeOnizle(user);

    expect(await screen.findByText("Önce program yöneticisi hesabını kurun")).toBeInTheDocument();
    expect(
      screen.getByText("Kişi kaydı için önce program yöneticisi hesabını kurun."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Kurulum sihirbazını aç" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aktar" })).toBeDisabled();
  });

  it("aktarım reddedilirse öntanımlı ileti; başarı bildirimi ve hatırlatma çıkmaz", async () => {
    okulApiMock.previewParentImport.mockResolvedValue(ONIZLEME);
    okulApiMock.commitParentImport.mockRejectedValue(GOVDESIZ_RET);
    const user = userEvent.setup();
    kur();
    await dosyaSecVeOnizle(user);
    await user.click(await screen.findByRole("button", { name: "Aktar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(VELI_AKTARILAMADI);
    expect(okulApiMock.commitParentImport).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(VELI_AKTARILDI)).toBeNull();
    expect(screen.queryByText(KAYNAK_DOSYA_HATIRLATMASI)).toBeNull();
    expect(screen.queryByText("Aktarım sonucu")).toBeNull();
    // Özet yeniden okunmaz: liste değişmedi.
    expect(okulApiMock.getParentRoster).toHaveBeenCalledTimes(1);
  });

  it("sınırı aşan dosya seçilince boy iletisi çıkar; Önizle uca gitmez", async () => {
    const user = userEvent.setup();
    kur();
    await dosyaSecVeOnizle(user, dosya(20 * MB + 1));

    expect(await screen.findByText("Dosya çok büyük; en çok 20 MB olabilir.")).toBeInTheDocument();
    expect(okulApiMock.previewParentImport).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Aktar" })).toBeDisabled();
  });

  it("şablon indirilemezse hata bandı; gövdesiz retde ekranın metni", async () => {
    okulApiMock.parentTemplate.mockRejectedValue(GOVDESIZ_RET);
    const user = userEvent.setup();
    kur();
    await user.click(await screen.findByRole("button", { name: "Şablon indir" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(SABLON_INDIRILEMEDI);
    expect(saveBlob).not.toHaveBeenCalled();
  });

  it("şablon kaydedilemezse dosya yazılamadı iletisi çıkar", async () => {
    okulApiMock.parentTemplate.mockResolvedValue(new Blob(["x"]));
    vi.mocked(saveBlob).mockResolvedValue("hata");
    const user = userEvent.setup();
    kur();
    await user.click(await screen.findByRole("button", { name: "Şablon indir" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(DOSYA_YAZILAMADI_ILETISI);
  });
});
