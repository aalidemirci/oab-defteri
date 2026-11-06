// Kaydetme penceresi ve boşta sayaç (tasarım §4.4.3): yerel "Farklı kaydet" penceresindeki tıklamalar
// DOM olayı üretmez. Yer seçimi 5 sn'den uzun sürse de seçilen yerle giden POST kullanıcı eylemidir,
// `X-OD-Etkinlik` taşır; iptal etkileşim kaydetmez. Bu test gerçek `lib/api`'yle ve sahte fetch'le
// koşar: başlığı `lib/api` koyar, kartın öteki davranışları `SifreliYedekleme.test.tsx`'tedir.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import {
  ETKINLIK_BASLIGI,
  ETKINLIK_PENCERESI_MS,
  etkinlikSaatleriniSifirla,
  sonEtkilesimAni,
} from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import SifreliYedekleme from "./SifreliYedekleme";
import { yedekIsleriniSifirla } from "./yedekIsleri";

const ONERILEN_AD = "oab-defteri-yedek-2026-11-06-101530.odbak";
const SONUC = { ad: ONERILEN_AD, boyut: 1024, ek_sayisi: 0, eksik: 0, denetlendi: true };
const DIS_YEDEK = {
  last_download: null,
  reminder_days: 30,
  days_since: 3,
  remind: false,
  min_reminder_days: 7,
  max_reminder_days: 90,
};

function yanit(govde: unknown) {
  return { ok: true, status: 200, json: () => Promise.resolve(govde) };
}

const fetchSahte = vi.fn((yol: string, init: RequestInit) => {
  if (!yol.endsWith("/backups/encrypted/")) return Promise.resolve(yanit(DIS_YEDEK));
  return Promise.resolve(yanit(init.method === "POST" ? SONUC : { onerilen_ad: ONERILEN_AD }));
});

/** Pencere açıkken süre geçer, DOM olayı olmaz; kullanıcı `donus`le döner. */
function kopruyuKur(donus: string) {
  window.pywebview = {
    api: {
      kaydetme_yeri_sor: () => {
        vi.setSystemTime(Date.now() + ETKINLIK_PENCERESI_MS + 300);
        return Promise.resolve(donus);
      },
    },
  };
}

function bas() {
  return render(
    <SnackbarProvider>
      <SifreliYedekleme parolaKurulu />
    </SnackbarProvider>,
  );
}

function kayitIstegi() {
  const cagri = fetchSahte.mock.calls.find(([, init]) => init.method === "POST");
  return cagri?.[1].headers as Record<string, string> | undefined;
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

it("pencere 5 sn'den uzun sürse de seçilen yerle giden POST başlık taşır", async () => {
  kopruyuKur("E:\\okul-yedegi.odbak");
  bas();

  await userEvent.click(screen.getByRole("button", { name: "Şifreli yedeği kaydet" }));

  await waitFor(() => expect(kayitIstegi()).toBeDefined());
  expect(kayitIstegi()?.[ETKINLIK_BASLIGI]).toBe("1");
});

it("iptal etkileşim kaydetmez: pencerede geçen süre kullanıcı eylemi sayılmaz", async () => {
  kopruyuKur("");
  bas();
  const dugme = screen.getByRole("button", { name: "Şifreli yedeği kaydet" });
  const tiklama = Date.now();

  await userEvent.click(dugme);

  await waitFor(() => expect(Date.now()).toBeGreaterThan(tiklama));
  await waitFor(() => expect(dugme).toBeEnabled());
  expect(kayitIstegi()).toBeUndefined();
  // Son etkileşim düğmeye basılan andır; pencerenin kapandığı an değildir.
  expect(sonEtkilesimAni()).toBe(tiklama);
});
