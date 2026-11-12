// Görev bölümü ve temsilci evrakının kartı (plan F1c 10-11. adım): kaydın durumu, üretim (yeni sürüm;
// basım uyarıları kartta, belgeye basılmaz), PDF ve Word basımı (GET; adı sunucunun, okunamazsa belge +
// üretim günü), dönem kilidi bandı, dosya deposu iletisi, kaydetme sonuçları. Veriler uydurmadır.

import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { EvrakKaydi } from "./api";

const evrakApiMock = vi.hoisted(() => ({ liste: vi.fn(), uret: vi.fn(), dosya: vi.fn() }));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  evrakApi: evrakApiMock,
}));

const indirmeMock = vi.hoisted(() => ({ saveBlob: vi.fn() }));
vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: indirmeMock.saveBlob,
}));

import { evrakYedekDosyaAdi } from "./api";
import EvrakKarti from "./EvrakKarti";
import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  E01_ADI,
  EVRAK_OKUNAMADI,
  EVRAK_YOK,
  PDF_KAYDEDILDI,
  URETIM_UYARILARI_BASLIGI,
} from "./metinler";

const KAYIT: EvrakKaydi = {
  id: 5,
  kod: "E01",
  ad: E01_ADI,
  surum: 2,
  durum: "GECERLI",
  uretim_zamani: "2026-11-11T09:30:00+03:00",
  bicimler: ["PDF", "DOCX"],
};

function bas(uretebilir = true) {
  return render(
    <MemoryRouter>
      <SnackbarProvider>
        <EvrakKarti donem={3} kod="E01" baslik={E01_ADI} uretebilir={uretebilir} />
      </SnackbarProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  evrakApiMock.liste.mockResolvedValue([]);
  indirmeMock.saveBlob.mockResolvedValue("kaydedildi");
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("EvrakKarti", () => {
  it("yedek dosya adı belge ve üretim günüyle kurulur", () => {
    expect(evrakYedekDosyaAdi(KAYIT, "pdf")).toBe(
      "Yönetim-Kurulu-Görev-Bölümü-Karar-Taslağı_11.11.2026.pdf",
    );
    expect(evrakYedekDosyaAdi({ ...KAYIT, kod: "E03" }, "docx")).toBe(
      "Temsilci-Görevlendirme-Çizelgesi_11.11.2026.docx",
    );
  });

  it("kayıt yokken üretilir; basım uyarıları kartta durur", async () => {
    const user = userEvent.setup();
    evrakApiMock.uret.mockResolvedValue({
      evrak: KAYIT,
      uyarilar: ["Sekreter görevi boş.", "Kurulda boş koltuk var; satırı ……… basıldı."],
    });
    bas();
    expect(await screen.findByText(EVRAK_YOK)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_PDF })).toBeNull();
    await user.click(screen.getByRole("button", { name: DUGME_OLUSTUR }));
    expect(evrakApiMock.uret).toHaveBeenCalledWith(3, "E01");
    expect(await screen.findByText(URETIM_UYARILARI_BASLIGI)).toBeInTheDocument();
    expect(screen.getByText("Sekreter görevi boş.")).toBeInTheDocument();
    expect(screen.getByText(/2\. sürüm/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeInTheDocument();
  });

  it("PDF ve Word kaydedilir; ad sunucunundur, yoksa yedek ad", async () => {
    const user = userEvent.setup();
    evrakApiMock.liste.mockResolvedValue([KAYIT]);
    const blob = new Blob(["%PDF"]);
    evrakApiMock.dosya
      .mockResolvedValueOnce({ blob, ad: "Sunucunun-Adı_11.11.2026.pdf" })
      .mockResolvedValueOnce({ blob, ad: null });
    bas(false);
    await user.click(await screen.findByRole("button", { name: DUGME_PDF }));
    expect(evrakApiMock.dosya).toHaveBeenCalledWith(5, "pdf");
    expect(indirmeMock.saveBlob).toHaveBeenCalledWith(blob, "Sunucunun-Adı_11.11.2026.pdf");
    expect(await screen.findByText(PDF_KAYDEDILDI)).toBeInTheDocument();
    // Üretemeyen rolde "Belgeyi oluştur" yoktur, basım vardır.
    expect(screen.queryByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeNull();
    await user.click(screen.getByRole("button", { name: DUGME_WORD }));
    expect(indirmeMock.saveBlob).toHaveBeenLastCalledWith(
      blob,
      "Yönetim-Kurulu-Görev-Bölümü-Karar-Taslağı_11.11.2026.docx",
    );
    // Bildirimler sırayla gösterilir: ikincisi birincinin ardından gelir (kuyruk).
  });

  it("kaydetme yazılamazsa ileti; iptalde ileti yok", async () => {
    const user = userEvent.setup();
    evrakApiMock.liste.mockResolvedValue([KAYIT]);
    evrakApiMock.dosya.mockResolvedValue({ blob: new Blob(["x"]), ad: null });
    indirmeMock.saveBlob.mockResolvedValueOnce("hata").mockResolvedValueOnce("iptal");
    bas(false);
    await user.click(await screen.findByRole("button", { name: DUGME_PDF }));
    expect(await screen.findByText(DOSYA_YAZILAMADI_ILETISI)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_PDF }));
    expect(screen.queryByText(PDF_KAYDEDILDI)).toBeNull();
    expect(screen.queryByText(DOSYA_YAZILAMADI_ILETISI)).toBeNull();
  });

  it("dönem kilidi bantla, dosya deposu iletisi hata bandıyla", async () => {
    const user = userEvent.setup();
    evrakApiMock.liste.mockResolvedValue([KAYIT]);
    evrakApiMock.uret.mockRejectedValue(
      new ApiError(409, "donem_kapali", "Bu birlik dönemi kapandı; kayıt yazılamaz."),
    );
    evrakApiMock.dosya.mockRejectedValue(
      new ApiError(409, "evrak_dosyasi_acilamadi", "Evrakın dosyası açılamadı."),
    );
    bas();
    await user.click(await screen.findByRole("button", { name: DUGME_YENIDEN_OLUSTUR }));
    expect(await screen.findByText("Bu kayıt yazılamaz")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_PDF }));
    expect(await screen.findByText("Evrakın dosyası açılamadı.")).toBeInTheDocument();
  });

  it("liste okunamazsa durum satırı söyler", async () => {
    evrakApiMock.liste.mockRejectedValue(new Error("ağ yok"));
    bas();
    expect(await screen.findByText(EVRAK_OKUNAMADI)).toBeInTheDocument();
    // Kaydın varlığı bilinmez: "Belgeyi oluştur" çizilmez.
    expect(screen.queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
  });

  it("liste okunana dek 'belge yok' ve 'Belgeyi oluştur' gösterilmez", async () => {
    let coz: (liste: EvrakKaydi[]) => void = () => undefined;
    evrakApiMock.liste.mockReturnValue(
      new Promise<EvrakKaydi[]>((r) => {
        coz = r;
      }),
    );
    bas();
    expect(screen.getByRole("heading", { level: 2, name: E01_ADI })).toBeInTheDocument();
    expect(screen.queryByText(EVRAK_YOK)).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeNull();
    await act(async () => {
      coz([KAYIT]);
    });
    expect(await screen.findByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
    expect(screen.queryByText(EVRAK_YOK)).toBeNull();
  });
});
