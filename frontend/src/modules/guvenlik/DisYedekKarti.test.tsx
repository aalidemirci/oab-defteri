// Genel Bakış "Şifreli Yedeği USB Belleğe Alın" kartı (tasarım §4.3 tehdit 18, §16 R6):
// yalnız süre dolunca görünür, son kaydı ya da hiç kayıt olmadığını söyler, gövdesi eklerin ve
// üretilen evrakın da şifreli yedekle korunduğunu anar, Güvenlik sekmesine bağlanır; pano okuması
// kullanıcı etkinliği sayılmaz. Program dosyanın USB bellekte olduğunu bilemez: kart "alındı" demez.

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock("../../lib/api", () => ({ api: { get: mocks.get } }));

import DisYedekKarti, { DIS_YEDEK_KARTI_BASLIGI, GUVENLIK_ADRESI } from "./DisYedekKarti";

const TEMEL = {
  last_download: null,
  reminder_days: 30,
  days_since: 10,
  remind: true,
  min_reminder_days: 7,
  max_reminder_days: 90,
};

function bas() {
  return render(
    <MemoryRouter>
      <DisYedekKarti />
    </MemoryRouter>,
  );
}

beforeEach(() => vi.clearAllMocks());

it("hiç kayıt yoksa bunu söyler ve Güvenlik sekmesine bağlanır", async () => {
  mocks.get.mockResolvedValue(TEMEL);
  bas();

  expect(await screen.findByRole("heading", { name: DIS_YEDEK_KARTI_BASLIGI })).toBeInTheDocument();
  expect(
    screen.getByText("Bu bilgisayardan henüz şifreli yedek kaydedilmedi."),
  ).toBeInTheDocument();
  expect(screen.getByText(/USB belleğe kaydedin/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Güvenlik/ })).toHaveAttribute("href", GUVENLIK_ADRESI);
  // Pano okuması boşta süreyi tazelemez (tasarım §4.4.3).
  expect(mocks.get).toHaveBeenCalledWith("/backups/external/", { etkinlik: false });
});

it("son kaydın tarihini gg.aa.yyyy ve gün sayısıyla yazar", async () => {
  mocks.get.mockResolvedValue({
    ...TEMEL,
    last_download: "2026-08-20T09:05:00+03:00",
    days_since: 38,
  });
  bas();

  expect(
    await screen.findByText("Son şifreli yedek 20.08.2026 tarihinde kaydedildi (38 gün önce)."),
  ).toBeInTheDocument();
});

it("gövde ekleri ve üretilen evrakı anar; indirme ve USB'ye alındı sözü yoktur", async () => {
  mocks.get.mockResolvedValue(TEMEL);
  const { container } = bas();

  await screen.findByRole("heading", { name: DIS_YEDEK_KARTI_BASLIGI });
  expect(container.textContent).toMatch(/kayıtları, ekleri ve\s+üretilen evrakı birlikte taşır/);
  expect(container.textContent).toMatch(/ekleri taşımaz/);
  expect(container.textContent).not.toMatch(/indir/i);
  expect(container.textContent).not.toMatch(/USB belleğe alındı/);
});

it("süre dolmadıysa kart görünmez", async () => {
  mocks.get.mockResolvedValue({ ...TEMEL, remind: false });
  const { container } = bas();

  await waitFor(() => expect(mocks.get).toHaveBeenCalled());
  expect(container).toBeEmptyDOMElement();
});

it("özet okunamazsa kart görünmez", async () => {
  mocks.get.mockRejectedValue(new Error("423"));
  const { container } = bas();

  await waitFor(() => expect(mocks.get).toHaveBeenCalled());
  expect(container).toBeEmptyDOMElement();
});
