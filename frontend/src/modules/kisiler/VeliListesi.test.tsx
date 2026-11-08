// Kişiler → Veli Listesi (T5; genel tasarım §8.4): özet yalnız sınıf başına sayıdır, aktarım
// önizle → aktar akışıyla yürür (Aktar önizlemeden önce kapalı), önizleme ve sonuç ad
// göstermez, aktarılamayan satırlar numarası ve nedeniyle görünür, aydınlatma metni dosya
// seçiminin üstündedir, "Veli listesini sil" onay ister. Veriler uydurmadır (KVKK).

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { saveBlob } from "../../lib/download";
import { ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { ParentImportReport, ParentRosterSummary } from "../okul/api";
import type { OturumOzeti } from "../oturum/api";
import { OTURUM_SORGU_ANAHTARI } from "../oturum/useOturum";
import {
  AYDINLATMA_BASLIGI,
  VELI_AYDINLATMA_AMACI,
  VELI_DOSYA_ALANI_ETIKETI,
  VELI_LISTESI_BOS,
  VELI_LISTESINI_SIL,
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

function dosya(): File {
  return new File(["uydurma"], "veli.xlsx", {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}

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

    await user.click(screen.getByRole("button", { name: "Aktar" }));
    expect(await screen.findByText("Aktarım sonucu")).toBeInTheDocument();
    expect(okulApiMock.commitParentImport).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("Veli listesi aktarıldı.")).toBeInTheDocument();
    // Özet yeniden okunur.
    await waitFor(() => expect(okulApiMock.getParentRoster).toHaveBeenCalledTimes(2));
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
