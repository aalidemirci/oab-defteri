// Yedek Raporu kartı (tasarım §9.7; kullanıcı kararı 04.11.2026 "Yedek raporu"): PDF sunucudan gelir,
// önerilen ad sunucunun verdiği addır, ekranın kurduğu ad yalnız o ad okunamazsa kullanılır (sözlük §3);
// iş sürerken düğme kapalıdır; ret sunucunun iletisiyle gösterilir, iletisiz ret ve kopan bağlantı
// sözlükteki metinle (İngilizce ham ileti ekrana çıkmaz). Uç gövdesizdir.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { SnackbarProvider } from "../../ui/SnackbarProvider";

const mocks = vi.hoisted(() => ({ postDosya: vi.fn(), saveBlob: vi.fn() }));

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  api: { postDosya: mocks.postDosya },
}));
vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: mocks.saveBlob,
}));

import YedekRaporuKarti from "./YedekRaporuKarti";

const PDF = new Blob(["%PDF-1.7"], { type: "application/pdf" });

function bas() {
  return render(
    <SnackbarProvider>
      <YedekRaporuKarti />
    </SnackbarProvider>,
  );
}

const dugme = () => screen.getByRole("button", { name: "PDF olarak kaydet" });

// Gerçek `saveBlob` hep sonuç döndürür: sahte `undefined` dönseydi başarı dalı sınanmazdı.
beforeEach(() => {
  vi.clearAllMocks();
  mocks.saveBlob.mockResolvedValue("kaydedildi");
});
afterEach(() => vi.useRealTimers());

it("kart adı belge adıdır; raporu gövdesiz ister, sunucunun adıyla kaydeder", async () => {
  mocks.postDosya.mockResolvedValue({ blob: PDF, ad: "Yedek-Raporu_06.11.2026.pdf" });
  bas();

  expect(screen.getByRole("heading", { name: "Yedek Raporu" })).toBeInTheDocument();
  await userEvent.click(dugme());

  await waitFor(() =>
    expect(mocks.saveBlob).toHaveBeenCalledWith(PDF, "Yedek-Raporu_06.11.2026.pdf"),
  );
  expect(mocks.postDosya).toHaveBeenCalledWith("/backups/report/");
  expect(await screen.findByText("Yedek Raporu PDF olarak kaydedildi.")).toBeInTheDocument();
});

it("köprü yoksa dosya tarayıcıya verilir, bildirim yine çıkar", async () => {
  mocks.postDosya.mockResolvedValue({ blob: PDF, ad: "Yedek-Raporu_06.11.2026.pdf" });
  mocks.saveBlob.mockResolvedValueOnce("indirildi");
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByText("Yedek Raporu PDF olarak kaydedildi.")).toBeInTheDocument();
});

it("kaydetme penceresinde iptal sessizdir: bildirim çıkmaz, düğme geri gelir", async () => {
  mocks.postDosya.mockResolvedValue({ blob: PDF, ad: "Yedek-Raporu_06.11.2026.pdf" });
  mocks.saveBlob.mockResolvedValueOnce("iptal");
  bas();

  await userEvent.click(dugme());

  await waitFor(() => expect(mocks.saveBlob).toHaveBeenCalledTimes(1));
  await waitFor(() => expect(dugme()).toBeEnabled());
  expect(screen.queryByText("Yedek Raporu PDF olarak kaydedildi.")).not.toBeInTheDocument();
  expect(screen.queryByText(DOSYA_YAZILAMADI_ILETISI)).not.toBeInTheDocument();
});

it("dosya yazılamazsa tek ileti çıkar, kaydedildi denmez", async () => {
  mocks.postDosya.mockResolvedValue({ blob: PDF, ad: "Yedek-Raporu_06.11.2026.pdf" });
  mocks.saveBlob.mockResolvedValueOnce("hata");
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByText(DOSYA_YAZILAMADI_ILETISI)).toBeInTheDocument();
  expect(screen.queryByText("Yedek Raporu PDF olarak kaydedildi.")).not.toBeInTheDocument();
});

it("sunucunun adı okunamazsa aynı kalıpla ve yerel tarihle kurar", async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 6, 0, 30, 0));
  mocks.postDosya.mockResolvedValue({ blob: PDF, ad: null });
  bas();

  await userEvent.click(dugme());

  await waitFor(() =>
    expect(mocks.saveBlob).toHaveBeenCalledWith(PDF, "Yedek-Raporu_06.11.2026.pdf"),
  );
});

it("iş sürerken düğme kapalıdır ve hazırlandığını söyler", async () => {
  let bitir: (dosya: { blob: Blob; ad: string }) => void = () => undefined;
  mocks.postDosya.mockImplementation(
    () =>
      new Promise((coz) => {
        bitir = coz;
      }),
  );
  bas();

  await userEvent.click(dugme());

  expect(screen.getByRole("button", { name: "Hazırlanıyor…" })).toBeDisabled();
  bitir({ blob: PDF, ad: "Yedek-Raporu_06.11.2026.pdf" });
  await waitFor(() => expect(dugme()).toBeEnabled());
});

it("ret sunucunun iletisiyle gösterilir, dosya kaydedilmez", async () => {
  mocks.postDosya.mockRejectedValue(
    new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."),
  );
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByText("Bu işlem hesabınızın rolüne açık değil.")).toBeInTheDocument();
  expect(mocks.saveBlob).not.toHaveBeenCalled();
  expect(dugme()).toBeEnabled();
});

it.each([
  ["gövdesiz ret", new ApiError(500, "500", BEKLENMEYEN_HATA_ILETISI)],
  ["kopan bağlantı", new TypeError("Failed to fetch")],
])("%s sözlükteki metinle gösterilir, ham ileti çıkmaz", async (_ad, hata) => {
  mocks.postDosya.mockRejectedValue(hata);
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByText("Yedek Raporu hazırlanamadı.")).toBeInTheDocument();
  expect(document.body.textContent).not.toContain("Failed to fetch");
  expect(document.body.textContent).not.toContain(BEKLENMEYEN_HATA_ILETISI);
});
