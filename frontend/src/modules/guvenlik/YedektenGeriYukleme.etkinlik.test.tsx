// Aç penceresi ve boşta sayaç (tasarım §4.4.3; kullanıcı kararı 06.11.2026 "Yedek dosyası yüklenmez,
// programın Aç penceresiyle seçilir"): yerel pencerede yapılan seçim DOM olayı üretmez. Seçim 5 sn'den
// uzun sürse de seçilen yolla giden başlık isteği kullanıcı eylemidir, `X-OD-Etkinlik` taşır; iptal
// etkileşim kaydetmez. Yol yalnız gövdede gider, adrese girmez. Bu test gerçek `lib/api`'yle ve sahte
// fetch'le koşar: başlığı `lib/api` koyar, kartın öteki davranışları `YedektenGeriYukleme.kopru.test.tsx`'tedir.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import {
  ETKINLIK_BASLIGI,
  ETKINLIK_PENCERESI_MS,
  etkinlikSaatleriniSifirla,
  sonEtkilesimAni,
} from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import YedektenGeriYukleme from "./YedektenGeriYukleme";
import { yedekIsleriniSifirla } from "./yedekIsleri";

const YOL = "E:\\Okul Yedekleri\\Şubat ayı.odbak";
const OZET = {
  name: "Şubat ayı.odbak",
  size: 45987,
  modified_at: "2026-11-06T17:55:12.643259+03:00",
  kurtarma: { no: 1, tarih: "2026-11-06" },
  kapsam: "tam",
};

function yanit(govde: unknown) {
  return { ok: true, status: 200, json: () => Promise.resolve(govde) };
}

const fetchSahte = vi.fn((yol: string, _init: RequestInit) =>
  Promise.resolve(
    yanit(yol.endsWith("/backups/inspect/") ? OZET : { backup_dir: "C:\\x", backups: [] }),
  ),
);

/** Pencere açıkken süre geçer, DOM olayı olmaz; kullanıcı `donus`le döner. */
function kopruyuKur(donus: string) {
  window.pywebview = {
    api: {
      yedek_dosyasi_sor: () => {
        vi.setSystemTime(Date.now() + ETKINLIK_PENCERESI_MS + 300);
        return Promise.resolve(donus);
      },
    },
  };
}

function bas() {
  return render(
    <SnackbarProvider>
      <ConfirmProvider>
        <YedektenGeriYukleme />
      </ConfirmProvider>
    </SnackbarProvider>,
  );
}

function baslikIstegi() {
  return fetchSahte.mock.calls.find(([, init]) => init.method === "POST");
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 6, 10, 0, 0));
  etkinlikSaatleriniSifirla();
  yedekIsleriniSifirla();
  fetchSahte.mockClear();
  vi.stubGlobal("fetch", fetchSahte);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  delete window.pywebview;
});

it("pencere 5 sn'den uzun sürse de seçilen yolla giden istek başlık taşır; yol adrese girmez", async () => {
  kopruyuKur(YOL);
  bas();

  await userEvent.click(await screen.findByRole("button", { name: "Yedek dosyası seç" }));

  await waitFor(() => expect(baslikIstegi()).toBeDefined());
  const [adres, ayar] = baslikIstegi() as [string, RequestInit];
  expect((ayar.headers as Record<string, string>)[ETKINLIK_BASLIGI]).toBe("1");
  expect(adres.endsWith("/backups/inspect/")).toBe(true);
  expect(JSON.parse(ayar.body as string)).toEqual({ yol: YOL });
});

it("iptal etkileşim kaydetmez: pencerede geçen süre kullanıcı eylemi sayılmaz", async () => {
  kopruyuKur("");
  bas();
  const dugme = await screen.findByRole("button", { name: "Yedek dosyası seç" });
  const tiklama = Date.now();

  await userEvent.click(dugme);

  await waitFor(() => expect(Date.now()).toBeGreaterThan(tiklama));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: /Yedek dosyası seç/ })).toBeEnabled(),
  );
  expect(baslikIstegi()).toBeUndefined();
  // Son etkileşim düğmeye basılan andır; pencerenin kapandığı an değildir.
  expect(sonEtkilesimAni()).toBe(tiklama);
});
