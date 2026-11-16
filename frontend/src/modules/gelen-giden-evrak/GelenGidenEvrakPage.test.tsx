// Gelen-Giden Evrak ekranı (plan F2 §6.1 M10): defter yokken boş durum ve (yalnız `evrak_kaydi`'nde)
// defterin kaydı; defter seçimi ve süzgeçler; kayıtlar ve kaydın penceresi (ekler); yeni kayıt ve sıra
// atlamanın uyarı + gerekçe akışı; müdür ve Denetleme Kurulu okur (salt okur notu, yazma denetimi yok;
// kaydın penceresinde ek eklenmez). Defter varken de yeni defter kaydedilir ve seçili olur; okuma
// hataları bantla gösterilir. Veriler UYDURMADIR.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { SALT_OKUR_ILETISI } from "../oturum/RolKapisi";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { EvrakDefteri, EvrakKaydi } from "./api";

const apiMock = vi.hoisted(() => ({
  defterler: vi.fn(),
  defterKaydet: vi.fn(),
  kayitlar: vi.fn(),
  kaydet: vi.fn(),
  ekEkle: vi.fn(),
  gidenOnerisi: vi.fn(),
  gidenKaydet: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  gelenGidenApi: apiMock,
}));

const yarimMetinMock = vi.hoisted(() => ({ oku: vi.fn(), kaydet: vi.fn(), temizle: vi.fn() }));
vi.mock("../uyum/api", () => ({ yarimMetinApi: yarimMetinMock }));

import GelenGidenEvrakPage from "./GelenGidenEvrakPage";
import {
  DEFTERLER_OKUNAMADI,
  DEFTER_YOK,
  DEFTER_YOK_ACIKLAMASI,
  DUGME_DEFTER,
  DUGME_YENI_KAYIT,
  KAYIT_EKLENDI,
  KAYITLAR_OKUNAMADI,
  KAYIT_YOK,
} from "./metinler";

const DEFTER: EvrakDefteri = {
  id: 2,
  status: "KULLANIMDA",
  certified_by: "IL_ILCE_MEM",
  certified_on: "2026-09-01",
  certification_no: "12",
  page_count: 100,
  opened_on: "2026-09-02",
  last_no_before_program: 13,
  siradaki_no: 15,
};

const KAYIT: EvrakKaydi = {
  id: 9,
  book: 2,
  direction: "GELEN",
  year: new Date().getFullYear(),
  record_no: 14,
  date: "2026-10-03",
  counterparty: "Uydurma İlçe Millî Eğitim Müdürlüğü",
  subject: "Genel kurul hakkında",
  external_ref: "E-123",
  generated_document: null,
  term: 3,
  ekler: [],
};

function bas(yetenekler: string[] = ["evrak_kaydi"]) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <GelenGidenEvrakPage />
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

beforeEach(() => {
  apiMock.defterler.mockResolvedValue({ defterler: [DEFTER], varsayilan: 2 });
  apiMock.kayitlar.mockResolvedValue([KAYIT]);
  yarimMetinMock.oku.mockResolvedValue(null);
  yarimMetinMock.kaydet.mockResolvedValue(undefined);
  yarimMetinMock.temizle.mockResolvedValue(undefined);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Gelen-Giden Evrak", () => {
  it("defter yokken yazan role defter kaydı; okuyan rolde yalnız başlık ve salt okur notu", async () => {
    const user = userEvent.setup();
    apiMock.defterler.mockResolvedValue({ defterler: [], varsayilan: null });
    apiMock.defterKaydet.mockResolvedValue(DEFTER);
    const { unmount } = bas(["son_oturum_onay"]);
    expect(await screen.findByText(DEFTER_YOK)).toBeInTheDocument();
    expect(screen.getByText(SALT_OKUR_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText(DEFTER_YOK_ACIKLAMASI)).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_DEFTER })).toBeNull();
    unmount();
    bas();
    expect(await screen.findByText(DEFTER_YOK_ACIKLAMASI)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_DEFTER }));
    const pencere = screen.getByRole("dialog");
    await user.type(within(pencere).getByLabelText(/Programdan önceki son sıra no/), "13");
    await user.click(within(pencere).getByRole("button", { name: DUGME_DEFTER }));
    expect(apiMock.defterKaydet).toHaveBeenCalledWith({
      certified_by: "IL_ILCE_MEM",
      certified_on: null,
      certification_no: "",
      page_count: null,
      last_no_before_program: 13,
      opened_on: null,
    });
  });

  it("kayıtlar defter, yıl ve yönle süzülür; satır kaydın penceresini açar", async () => {
    const user = userEvent.setup();
    bas(["son_oturum_onay"]);
    const yil = new Date().getFullYear();
    expect(await screen.findByText(`${yil}/14`)).toBeInTheDocument();
    expect(apiMock.kayitlar).toHaveBeenCalledWith({ book: 2, year: yil, direction: "" });
    expect(screen.queryByRole("button", { name: DUGME_YENI_KAYIT })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_DEFTER })).toBeNull();
    await user.selectOptions(screen.getByLabelText("Yön"), "GIDEN");
    expect(apiMock.kayitlar).toHaveBeenLastCalledWith({ book: 2, year: yil, direction: "GIDEN" });
    apiMock.kayitlar.mockResolvedValue([]);
    await user.selectOptions(screen.getByLabelText("Yıl"), String(yil - 1));
    expect(await screen.findByText(KAYIT_YOK)).toBeInTheDocument();
  });

  it("kaydın penceresi: ayrıntı ve ek yalnız yazan rolde eklenir; okuyan rol eki görür", async () => {
    const user = userEvent.setup();
    apiMock.kayitlar.mockResolvedValue([
      {
        ...KAYIT,
        ekler: [
          {
            id: 4,
            ad: "Uydurma başvuru.pdf",
            tur: "application/pdf",
            boyut: 1000,
            yukleme_zamani: "2026-10-03T10:00:00+03:00",
          },
        ],
      },
    ]);
    const satir = `${new Date().getFullYear()}/14 kaydını aç`;
    const { unmount } = bas();
    await user.click(await screen.findByRole("button", { name: satir }));
    const pencere = screen.getByRole("dialog");
    expect(within(pencere).getByText("Uydurma İlçe Millî Eğitim Müdürlüğü")).toBeInTheDocument();
    expect(within(pencere).getByLabelText(/Ekler: Dosya ekle/)).toBeInTheDocument();
    unmount();
    bas(["son_oturum_onay"]);
    await user.click(await screen.findByRole("button", { name: satir }));
    const okunan = screen.getByRole("dialog");
    expect(within(okunan).getByText("Uydurma başvuru.pdf")).toBeInTheDocument();
    expect(within(okunan).queryByLabelText(/Ekler: Dosya ekle/)).toBeNull();
  });

  it("defter varken yeni defter kaydedilir ve seçili olur", async () => {
    const user = userEvent.setup();
    const yeni: EvrakDefteri = { ...DEFTER, id: 3, last_no_before_program: null, siradaki_no: 1 };
    apiMock.defterKaydet.mockResolvedValue(yeni);
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_DEFTER }));
    apiMock.defterler.mockResolvedValue({ defterler: [DEFTER, yeni], varsayilan: 3 });
    const pencere = screen.getByRole("dialog");
    await user.click(within(pencere).getByRole("button", { name: DUGME_DEFTER }));
    expect(apiMock.defterKaydet).toHaveBeenCalledTimes(1);
    const yil = new Date().getFullYear();
    await waitFor(() =>
      expect(apiMock.kayitlar).toHaveBeenLastCalledWith({ book: 3, year: yil, direction: "" }),
    );
    // İki defterde seçici çizilir.
    expect(await screen.findByLabelText("Defter")).toHaveValue("3");
  });

  it("defterler okunamazsa hata bandı; kayıtlar okunamazsa kendi bandı", async () => {
    apiMock.defterler.mockRejectedValue(new Error("ağ"));
    const { unmount } = bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(DEFTERLER_OKUNAMADI);
    unmount();
    apiMock.defterler.mockResolvedValue({ defterler: [DEFTER], varsayilan: 2 });
    apiMock.kayitlar.mockRejectedValue(new Error("ağ"));
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(KAYITLAR_OKUNAMADI);
  });

  it("yeni kayıt: tarih zorunlu; sıra atlamada gerekçe istenir ve gerekçeyle gider", async () => {
    const user = userEvent.setup();
    apiMock.kaydet
      .mockRejectedValueOnce(
        new ApiError(
          400,
          "gerekce_gerekli",
          "Bu kayıt için gerekçe yazılmalıdır. Kayıt numarası sıradaki numara değil.",
        ),
      )
      .mockResolvedValueOnce({ kayit: { ...KAYIT, id: 10, record_no: 20 }, uyarilar: [] });
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_YENI_KAYIT }));
    const pencere = screen.getByRole("dialog");
    await user.click(within(pencere).getByRole("button", { name: DUGME_YENI_KAYIT }));
    expect(within(pencere).getByText("Tarihi girin.")).toBeInTheDocument();
    fireEvent.change(within(pencere).getByLabelText(/^Tarih/), { target: { value: "2026-10-04" } });
    await user.type(within(pencere).getByLabelText("Kayıt no"), "20");
    await user.type(within(pencere).getByLabelText("Konu"), "Uydurma başvuru");
    await user.click(within(pencere).getByRole("button", { name: DUGME_YENI_KAYIT }));
    expect(apiMock.kaydet).toHaveBeenNthCalledWith(1, {
      direction: "GELEN",
      tarih: "2026-10-04",
      counterparty: "",
      subject: "Uydurma başvuru",
      external_ref: "",
      record_no: 20,
      defter: 2,
    });
    await user.type(
      await within(pencere).findByLabelText(/^Gerekçe/),
      "Uydurma: iki numara boş kaldı.",
    );
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(apiMock.kaydet).toHaveBeenLastCalledWith(
      expect.objectContaining({ record_no: 20, gerekce: "Uydurma: iki numara boş kaldı." }),
    );
    expect(await screen.findByText(KAYIT_EKLENDI)).toBeInTheDocument();
  });
});
