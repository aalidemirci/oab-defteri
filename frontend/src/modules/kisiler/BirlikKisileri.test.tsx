// Kişiler → Birlik Kişileri (`?tab=birlik`; tasarım §5.2.2; plan F1c kararları "Kişiler ekranı"; F1c-11):
// her rol okur, `birlik_kisi_yazma` yazar; tür görünen adı "İdareci"; T.C. kimlik no ve telefon yok;
// "olası aynı kişi" (D30) onayla `ayni_kisi_degil` ile yinelenir; pasif kişide alanlar kilitli, yalnız
// "Etkinleştir"; veli listesinden ekleme yalnız `veli_listesi` ile; programdan önceki seçilme sayıları
// salt okunur; aramaya uyan kayıt yoksa "kişi yok" denmez, aramaya yönlendirilir. Veriler uydurmadır (KVKK).

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { BirlikKisisi } from "./birlikKisileriApi";

const kisiApiMock = vi.hoisted(() => ({
  liste: vi.fn(),
  ekle: vi.fn(),
  guncelle: vi.fn(),
  personeldenEkle: vi.fn(),
  veliListesindenEkle: vi.fn(),
}));
vi.mock("./birlikKisileriApi", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./birlikKisileriApi")>()),
  birlikKisileriApi: kisiApiMock,
}));

const okulApiMock = vi.hoisted(() => ({ listPersonnel: vi.fn() }));
vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: okulApiMock,
}));

import { YETENEK_ADLARI } from "../oturum/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import KisilerPage from "./KisilerPage";
import {
  ARAMAYI_DEGISTIRIN,
  BIRLIK_KISILERI_SEKMESI,
  BIRLIK_KISISI_ARAMAYA_UYAN_YOK,
  BIRLIK_KISISI_ARAMAYA_UYAN_YOK_ACIKLAMASI,
  BIRLIK_KISISI_YOK,
  BIRLIK_KISISI_YOK_ACIKLAMASI,
  DUGME_BIRLIK_KISISI_EKLE,
  DUGME_ETKINLESTIR,
  DUGME_PERSONELDEN_EKLE,
  DUGME_VELI_LISTESINDEN_EKLE,
  OLASI_AYNI_KISI_BASLIGI,
  PASIF_KISI_NOTU,
  VELI_LISTESINDEN_EKLE_BASLIGI,
} from "./metinler";

const KISI: BirlikKisisi = {
  id: 7,
  kind: "IDARECI",
  first_name: "Uydurnur",
  last_name: "Örnekkaya",
  full_name: "Uydurnur Örnekkaya",
  is_parent: false,
  adult_declared: false,
  is_principal: false,
  personnel: 3,
  external_yk_terms: 2,
  external_dk_chair_terms: null,
  status: "AKTIF",
};

function bas(yetenekler: readonly string[] = YETENEK_ADLARI) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <YetkiDegeri value={hazirYetki(yetenekler)}>
        <MemoryRouter initialEntries={["/kisiler?tab=birlik"]}>
          <SnackbarProvider>
            <ConfirmProvider>
              <KisilerPage />
            </ConfirmProvider>
          </SnackbarProvider>
        </MemoryRouter>
      </YetkiDegeri>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  kisiApiMock.liste.mockResolvedValue([KISI]);
  okulApiMock.listPersonnel.mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Birlik Kişileri", () => {
  it("sekme her role açıktır; liste ad, tür (İdareci) ve durumu gösterir, T.C. no ve telefon yok", async () => {
    bas(["son_oturum_onay"]);
    expect(await screen.findByRole("tab", { name: BIRLIK_KISILERI_SEKMESI })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(await screen.findByText("Uydurnur Örnekkaya")).toBeInTheDocument();
    expect(screen.getByText("İdareci")).toBeInTheDocument();
    expect(screen.getByText("Etkin")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /T\.C\.|Telefon/ })).toBeNull();
    expect(kisiApiMock.liste).toHaveBeenCalledWith({ search: "", onlyActive: true });
    // Salt okur: ekleme düğmeleri yok, satır ayrıntıyı salt okunur açar.
    expect(screen.queryByRole("button", { name: DUGME_BIRLIK_KISISI_EKLE })).toBeNull();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Uydurnur Örnekkaya kaydını aç" }));
    const pencere = screen.getByRole("dialog", { name: "Birlik kişisi" });
    expect(within(pencere).getByLabelText(/^Ad/)).toBeDisabled();
    expect(within(pencere).getByText("2")).toBeInTheDocument();
    expect(within(pencere).getByText("Girilmedi ya da bilinmiyor")).toBeInTheDocument();
    expect(within(pencere).queryByRole("button", { name: "Kaydet" })).toBeNull();
  });

  it("pasifler süzgeci listeyi yeniden okur", async () => {
    const user = userEvent.setup();
    bas();
    await screen.findByText("Uydurnur Örnekkaya");
    await user.click(screen.getByLabelText("Pasif kişileri de göster"));
    await waitFor(() =>
      expect(kisiApiMock.liste).toHaveBeenLastCalledWith({ search: "", onlyActive: false }),
    );
  });

  it("aramaya uyan kayıt yoksa ayrı boş durum: yeni kayda değil aramaya yönlendirir", async () => {
    const user = userEvent.setup();
    bas();
    await screen.findByText("Uydurnur Örnekkaya");
    kisiApiMock.liste.mockResolvedValue([]);
    await user.type(screen.getByLabelText("Ara"), "Uydurmaz");
    expect(await screen.findByText(BIRLIK_KISISI_ARAMAYA_UYAN_YOK)).toBeInTheDocument();
    expect(screen.getByText(BIRLIK_KISISI_ARAMAYA_UYAN_YOK_ACIKLAMASI)).toBeInTheDocument();
    expect(screen.queryByText(BIRLIK_KISISI_YOK)).toBeNull();
    expect(screen.queryByText(BIRLIK_KISISI_YOK_ACIKLAMASI)).toBeNull();
    // Pasifler zaten gösteriliyorsa yalnız aramayı değiştirmek önerilir.
    await user.click(screen.getByLabelText("Pasif kişileri de göster"));
    expect(await screen.findByText(ARAMAYI_DEGISTIRIN)).toBeInTheDocument();
    // Arama boşalınca hiç kayıt yok demektir: yazabilen role ekleme öğüdü.
    await user.clear(screen.getByLabelText("Ara"));
    expect(await screen.findByText(BIRLIK_KISISI_YOK)).toBeInTheDocument();
    expect(screen.getByText(BIRLIK_KISISI_YOK_ACIKLAMASI)).toBeInTheDocument();
  });

  it("yeni kişi: olası aynı kişi onaylanınca `ayni_kisi_degil` ile yinelenir", async () => {
    const user = userEvent.setup();
    kisiApiMock.ekle
      .mockRejectedValueOnce(
        new ApiError(
          409,
          "olasi_ayni_kisi",
          "Bu adla kayıtlı bir birlik kişisi var; aynı kişi olabilir.",
        ),
      )
      .mockResolvedValueOnce(KISI);
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_BIRLIK_KISISI_EKLE }));
    const pencere = screen.getByRole("dialog", { name: "Yeni birlik kişisi" });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText("Ad zorunludur.")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText(/^Ad/), "Uydurnur");
    await user.type(within(pencere).getByLabelText(/^Soyad/), "Örnekkaya");
    expect(within(pencere).getByLabelText("Velidir", { exact: false })).toBeChecked();
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    const soru = await screen.findByRole("dialog", { name: OLASI_AYNI_KISI_BASLIGI });
    expect(soru).toHaveTextContent("aynı kişi olabilir");
    await user.click(within(soru).getByRole("button", { name: "Aynı kişi değil, kaydet" }));
    await waitFor(() => expect(kisiApiMock.ekle).toHaveBeenCalledTimes(2));
    expect(kisiApiMock.ekle).toHaveBeenLastCalledWith({
      kind: "VELI",
      first_name: "Uydurnur",
      last_name: "Örnekkaya",
      is_parent: true,
      adult_declared: false,
      ayni_kisi_degil: true,
    });
    expect(await screen.findByText("Birlik kişisi kaydedildi.")).toBeInTheDocument();
  });

  it("olası aynı kişi sorusunda vazgeçilirse kayıt yazılmaz", async () => {
    const user = userEvent.setup();
    kisiApiMock.ekle.mockRejectedValue(new ApiError(409, "olasi_ayni_kisi", "Aynı kişi olabilir."));
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_BIRLIK_KISISI_EKLE }));
    const pencere = screen.getByRole("dialog", { name: "Yeni birlik kişisi" });
    await user.type(within(pencere).getByLabelText(/^Ad/), "Uydurnur");
    await user.type(within(pencere).getByLabelText(/^Soyad/), "Örnekkaya");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    const soru = await screen.findByRole("dialog", { name: OLASI_AYNI_KISI_BASLIGI });
    await user.click(within(soru).getByRole("button", { name: "Vazgeç" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog", { name: OLASI_AYNI_KISI_BASLIGI })).toBeNull(),
    );
    expect(kisiApiMock.ekle).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("dialog", { name: "Yeni birlik kişisi" })).toBeInTheDocument();
  });

  it("düzenleme: okul müdürü işareti gönderilir; pasif yapma ve pasif kişinin kilidi", async () => {
    const user = userEvent.setup();
    kisiApiMock.guncelle.mockResolvedValue(KISI);
    bas();
    await user.click(await screen.findByRole("button", { name: "Uydurnur Örnekkaya kaydını aç" }));
    const pencere = screen.getByRole("dialog", { name: "Birlik kişisini düzenle" });
    await user.click(within(pencere).getByLabelText("Okul müdürüdür", { exact: false }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(kisiApiMock.guncelle).toHaveBeenCalledWith(
      7,
      expect.objectContaining({ is_principal: true, kind: "IDARECI", ayni_kisi_degil: false }),
    );
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    await user.click(screen.getByRole("button", { name: "Uydurnur Örnekkaya kaydını aç" }));
    await user.click(screen.getByRole("button", { name: "Pasif yap" }));
    expect(kisiApiMock.guncelle).toHaveBeenLastCalledWith(7, { status: "PASIF" });

    kisiApiMock.liste.mockResolvedValue([{ ...KISI, status: "PASIF" }]);
    await user.click(screen.getByLabelText("Pasif kişileri de göster"));
    await user.click(await screen.findByRole("button", { name: "Uydurnur Örnekkaya kaydını aç" }));
    const pasif = screen.getByRole("dialog", { name: "Birlik kişisini düzenle" });
    expect(within(pasif).getByText(PASIF_KISI_NOTU)).toBeInTheDocument();
    expect(within(pasif).getByLabelText(/^Ad/)).toBeDisabled();
    expect(within(pasif).queryByRole("button", { name: "Kaydet" })).toBeNull();
    await user.click(within(pasif).getByRole("button", { name: DUGME_ETKINLESTIR }));
    expect(kisiApiMock.guncelle).toHaveBeenLastCalledWith(7, { status: "AKTIF" });
  });

  it("veli listesinden ekleme yalnız veli listesi yeteneğiyle", async () => {
    bas(["birlik_kisi_yazma"]);
    await screen.findByText("Uydurnur Örnekkaya");
    expect(screen.queryByRole("button", { name: DUGME_VELI_LISTESINDEN_EKLE })).toBeNull();
    expect(screen.getByRole("button", { name: DUGME_PERSONELDEN_EKLE })).toBeInTheDocument();
  });

  it("veli listesinden ekleme: yazılan ad gönderilir", async () => {
    const user = userEvent.setup();
    kisiApiMock.veliListesindenEkle.mockResolvedValue(KISI);
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_VELI_LISTESINDEN_EKLE }));
    const pencere = screen.getByRole("dialog", { name: VELI_LISTESINDEN_EKLE_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Ekle" }));
    expect(within(pencere).getByText("Velinin adı-soyadını yazın.")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText(/Velinin adı-soyadı/), " Ayşe Örnek ");
    await user.click(within(pencere).getByRole("button", { name: "Ekle" }));
    expect(kisiApiMock.veliListesindenEkle).toHaveBeenCalledWith("Ayşe Örnek", false);
  });

  it("personelden ekleme: sicilden seçilen kişi gönderilir", async () => {
    const user = userEvent.setup();
    okulApiMock.listPersonnel.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 3,
          first_name: "Uydurnur",
          last_name: "Örnekkaya",
          full_name: "Uydurnur Örnekkaya",
          member_kind: "YONETICI",
          is_active: true,
          left_at: null,
          leave_candidate_since: null,
        },
      ],
    });
    kisiApiMock.personeldenEkle.mockResolvedValue(KISI);
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_PERSONELDEN_EKLE }));
    const pencere = screen.getByRole("dialog", { name: "Personelden birlik kişisi ekle" });
    await user.click(within(pencere).getByRole("button", { name: "Ekle" }));
    expect(within(pencere).getByText("Personeli seçin.")).toBeInTheDocument();
    await user.type(within(pencere).getByRole("combobox"), "Uydurnur");
    await user.click(await within(pencere).findByRole("option", { name: /Uydurnur Örnekkaya/ }));
    await user.click(within(pencere).getByRole("button", { name: "Ekle" }));
    expect(kisiApiMock.personeldenEkle).toHaveBeenCalledWith(3, false);
  });

  it("okunamazsa hata bandı, boşsa boş durum", async () => {
    kisiApiMock.liste.mockRejectedValueOnce(new Error("ağ"));
    const { unmount } = bas();
    expect(await screen.findByRole("alert")).toHaveTextContent("Birlik kişileri okunamadı.");
    unmount();
    kisiApiMock.liste.mockResolvedValue([]);
    bas();
    expect(await screen.findByText("Birlik kişisi yok")).toBeInTheDocument();
  });
});
