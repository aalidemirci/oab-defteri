// KORUMA TESTİ (tasarım §4.4.5: anahtar basılıp saklandığı doğrulanmadan kurulum
// bitmez): kurtarma anahtarı ekrandayken sihirbaz sayfası sökülürse anahtar
// kaybolmamalı ve doğrulama atlanmamalıdır. Tam App ağacı (kilit ve kurulum kapıları,
// oturum göstergesi gerçek); yalnız API sınırı sahtedir.
//
// İki yol sınanır:
// * Üst menüden başka bir sayfaya gidilmesi (kurulum kapısı sihirbazı sıfırdan açar):
//   sihirbaz yeniden 1. adımda anahtarı gösterir, iki grup yeniden doğrulanmadan
//   "Devam" kapalı kalır.
// * "Kilitle": kilitlenme pencereyi yeniden yükler ve anahtarı ekrandan kaldırır
//   (tasarım §13 D53; plan F1b-1 "Oturum"). Bu yüzden anahtar beklerken Kilitle ÖNCE
//   sorar; "Vazgeç"te anahtar ekranda kalır, onaylanırsa kilitlenir ve pencere yüklenir
//   (sonra kâğıttaki anahtar doğrulanır ya da yenisi üretilir). İki grup tutup sunucu
//   damgayı yazdıysa ("Devam"a basılmamış olsa da) Kilitle sormaz. Kurulum sürerken boşta
//   kilit yoktur (D15). Aile iskeletinin görevli kipi senaryosu görevli kipiyle kalktı.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SetupStatus } from "./modules/okul/api";
import { YETENEK_ADLARI } from "./modules/oturum/api";
import type { OturumOzeti } from "./modules/oturum/api";
import { ILK_ACILIS_DURUMU } from "./test/kurulumDurumu";
import { BOS_OKUL_KARTI } from "./test/okulKarti";
import { ConfirmProvider } from "./ui/ConfirmProvider";
import { SnackbarProvider } from "./ui/SnackbarProvider";

const okulApiMock = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getSchoolConfig: vi.fn(),
  updateSchoolConfig: vi.fn(),
  completeSetup: vi.fn(),
  listSchoolYears: vi.fn(),
  listSchoolTerms: vi.fn(),
  listPersonnel: vi.fn(),
  listHolidays: vi.fn(),
  markRoadmapItem: vi.fn(),
  setRoadmapHidden: vi.fn(),
}));
vi.mock("./modules/okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./modules/okul/api")>();
  return { ...actual, okulApi: okulApiMock };
});
const oturumApiMock = vi.hoisted(() => ({
  ozet: vi.fn(),
  hesaplar: vi.fn(),
  ac: vi.fn(),
  kilitle: vi.fn(),
  kurtar: vi.fn(),
  kurtarmaHesaplari: vi.fn(),
}));
vi.mock("./modules/oturum/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./modules/oturum/api")>()),
  oturumApi: oturumApiMock,
}));
const gapi = vi.hoisted(() => ({
  durum: vi.fn(),
  kur: vi.fn(),
  kurtarmaAnahtariPdf: vi.fn(),
  kurtarmaAnahtariniDogrula: vi.fn(),
  kurtarmaAnahtariniYenile: vi.fn(),
}));
vi.mock("./modules/guvenlik/api", () => ({ guvenlikApi: gapi }));

import App from "./App";
import { pencereIcerigi } from "./lib/kilit";
import { bekleyenKurtarmaAnahtari } from "./modules/guvenlik/bekleyenAnahtar";

const ANAHTAR = "TEST-KURT-ARMA-ANAH-TARI-ABCD-EFGH-JKLM";
const GRUPLAR = ANAHTAR.split("-");
const PAROLA = "Gizli-Parola-42";
let hesapKurulu = false;
/** Sunucudaki "saklandı" damgası (`kurtarma.dogrulandi`, tasarım §4.4.4): doğrulama ucu yazar. */
let anahtarDogrulandi = false;

function oturumOzeti(): OturumOzeti {
  return {
    durum: hesapKurulu ? "acik" : "kurulum",
    hesap: hesapKurulu
      ? {
          id: "h-1",
          tanitici: "yonetici",
          rol: "yonetici",
          rol_etiketi: "Program yöneticisi",
          yetenekler: [...YETENEK_ADLARI],
        }
      : null,
    bosta_dk: 10,
    // Kurulum sihirbazı bitene dek süre işlemez (D15).
    bosta_kalan_sn: null,
    kilit_bekliyor: false,
    kurulum_tamam: false,
    yukleme_siniri_mb: 20,
  };
}

function kurulumDurumu(): SetupStatus {
  if (!hesapKurulu) return ILK_ACILIS_DURUMU;
  return {
    ...ILK_ACILIS_DURUMU,
    password_set: true,
    recovery_key_confirmed: anahtarDogrulandi,
    missing_steps: anahtarDogrulandi ? ["school", "calendar"] : ["password", "school", "calendar"],
  };
}

function guvenlikDurumu() {
  return {
    password_set: hesapKurulu,
    locked: false,
    security_file_missing: false,
    reset_available: false,
    transition_pending: false,
    transition: "",
    recovery_key_confirmed: anahtarDogrulandi,
    protected_fields: [],
    account_count: hesapKurulu ? 1 : 0,
    recovery_key_no: hesapKurulu ? 1 : null,
    recovery_key_date: hesapKurulu ? "2026-11-01" : null,
    corrupt_field_count: 0,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  hesapKurulu = false;
  anahtarDogrulandi = false;
  okulApiMock.getSetupStatus.mockImplementation(async () => kurulumDurumu());
  okulApiMock.getSchoolConfig.mockResolvedValue(BOS_OKUL_KARTI);
  okulApiMock.listSchoolYears.mockResolvedValue([]);
  oturumApiMock.ozet.mockImplementation(async () => oturumOzeti());
  oturumApiMock.kilitle.mockImplementation(async () => ({
    sonuc: "kilitlendi",
    ...oturumOzeti(),
    durum: "kilitli",
    hesap: null,
  }));
  gapi.durum.mockImplementation(async () => guvenlikDurumu());
  gapi.kur.mockImplementation(async () => {
    hesapKurulu = true;
    anahtarDogrulandi = false;
    return { ...guvenlikDurumu(), recovery_key: ANAHTAR, login_name_warning: null };
  });
  gapi.kurtarmaAnahtariniDogrula.mockImplementation(async () => {
    anahtarDogrulandi = true;
    return guvenlikDurumu();
  });
});

function bas() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/kurulum"]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <App />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function hesabiKur() {
  const kullanici = userEvent.setup();
  await kullanici.type(await screen.findByLabelText(/^Ad-soyad/), "Ayşe Deneme");
  await kullanici.type(screen.getByLabelText(/^Parola \*$/), PAROLA);
  await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), PAROLA);
  await kullanici.click(screen.getByRole("button", { name: "Hesabı kur" }));
  await screen.findByText("Kurtarma Anahtarınız");
  return kullanici;
}

/** Kabuğun üst çubuğu — DOM'daki ilk `banner` (App.test.tsx ile aynı kalıp). */
function ustCubuk(): HTMLElement {
  return screen.getAllByRole("banner")[0];
}

/** Sihirbaz anahtarı yeniden gösteriyor ve doğrulanmadan ilerlemiyor mu? */
async function anahtarYenidenGosterilir() {
  await screen.findByText("Kurtarma Anahtarınız");
  expect(screen.getByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
  expect(screen.queryByText("2. Okul Bilgileri")).toBeNull();
  expect(screen.getByRole("button", { name: "Devam" })).toBeDisabled();
}

/** İki grubu yazar; sunucu damgayı yazana dek bekler (grup sırası ekrandan okunur). */
async function ikiGrubuDogrula(kullanici: ReturnType<typeof userEvent.setup>) {
  await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
  const alanlar = screen.getAllByLabelText(/^\d+\. grup/) as HTMLInputElement[];
  expect(alanlar).toHaveLength(2);
  for (const alan of alanlar) {
    const grupNo = Number(/^(\d+)\. grup/.exec(alan.labels?.[0]?.textContent ?? "")?.[1]);
    await kullanici.type(alan, GRUPLAR[grupNo - 1]);
  }
  // İki grup tuttuktan sonra sunucu damgayı yazar; İleri ondan sonra açılır.
  await waitFor(() => expect(screen.getByRole("button", { name: "Devam" })).toBeEnabled());
  expect(gapi.kurtarmaAnahtariniDogrula).toHaveBeenLastCalledWith(ANAHTAR);
}

/** Anahtarı doğrular ve 2. adıma geçer. */
async function dogrulaVeDevamEt(kullanici: ReturnType<typeof userEvent.setup>) {
  await ikiGrubuDogrula(kullanici);
  await kullanici.click(screen.getByRole("button", { name: "Devam" }));
  await screen.findByText("2. Okul Bilgileri");
}

describe("kurtarma anahtarı doğrulanmadan sihirbaz sökülürse anahtar kaybolmaz", () => {
  it("ilk hesap pencereyi yeniden yüklemez; oturum göstergesi hemen gelir, geri sayım yoktur", async () => {
    bas();
    await hesabiKur();

    expect(gapi.kur).toHaveBeenCalledWith({
      tanitici: "yonetici",
      ad_soyad: "Ayşe Deneme",
      parola: PAROLA,
    });
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    const gosterge = await within(ustCubuk()).findByRole("group", { name: "Oturum" });
    expect(within(gosterge).getByText("Program yöneticisi")).toBeInTheDocument();
    // Kurulum sürerken boşta kilit ve geri sayım yoktur (D15).
    expect(screen.queryByTestId("oturum-geri-sayim")).toBeNull();
  });

  it("Kilitle anahtar beklerken önce sorar; Vazgeç'te anahtar ekranda kalır", async () => {
    bas();
    const kullanici = await hesabiKur();

    await kullanici.click(await within(ustCubuk()).findByRole("button", { name: "Kilitle" }));
    const diyalog = await screen.findByRole("dialog", { name: "Program kilitlensin mi?" });
    expect(diyalog).toHaveTextContent(/anahtar ekrandan kalkar/);
    await kullanici.click(within(diyalog).getByRole("button", { name: "Vazgeç" }));

    expect(oturumApiMock.kilitle).not.toHaveBeenCalled();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    await anahtarYenidenGosterilir();
    await dogrulaVeDevamEt(kullanici);
    // Doğrulanıp ilerlenince anahtar bellekten bırakılır: geri dönülünce gösterilmez.
    await kullanici.click(screen.getByRole("button", { name: "Geri" }));
    await screen.findByText(/Hesap kurulu, kurtarma anahtarının saklandığı doğrulandı/);
    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
  });

  it("Kilitle onaylanırsa kilitlenir ve pencere yeniden yüklenir (anahtar ekrandan gider)", async () => {
    bas();
    const kullanici = await hesabiKur();
    expect(bekleyenKurtarmaAnahtari()).toBe(ANAHTAR);

    await kullanici.click(await within(ustCubuk()).findByRole("button", { name: "Kilitle" }));
    const diyalog = await screen.findByRole("dialog", { name: "Program kilitlensin mi?" });
    await kullanici.click(within(diyalog).getByRole("button", { name: "Kilitle" }));

    await waitFor(() => expect(oturumApiMock.kilitle).toHaveBeenCalledTimes(1));
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("anahtar doğrulandıktan sonra Kilitle sormadan kilitler", async () => {
    bas();
    const kullanici = await hesabiKur();
    await dogrulaVeDevamEt(kullanici);

    await kullanici.click(within(ustCubuk()).getByRole("button", { name: "Kilitle" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("dialog", { name: "Program kilitlensin mi?" })).toBeNull();
  });

  it("iki grup doğrulanıp damga yazıldıysa Devam'a basılmadan da Kilitle sormadan kilitler", async () => {
    bas();
    const kullanici = await hesabiKur();
    await ikiGrubuDogrula(kullanici);
    // Anahtar hâlâ bellekte ve panelde ("Devam"a basılmadı) ama damgası yazıldı.
    expect(bekleyenKurtarmaAnahtari()).toBe(ANAHTAR);
    expect(anahtarDogrulandi).toBe(true);

    await kullanici.click(within(ustCubuk()).getByRole("button", { name: "Kilitle" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturumApiMock.kilitle).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("dialog", { name: "Program kilitlensin mi?" })).toBeNull();
  });

  it("menüden başka sayfaya gidilince sihirbaz anahtarı yeniden gösterir", async () => {
    bas();
    const kullanici = await hesabiKur();

    const menu = screen.getAllByRole("link", { name: /Genel Bakış/ })[0];
    await kullanici.click(menu);

    await anahtarYenidenGosterilir();
    expect(
      within(document.body).getByText(/Kurulum tamamlanmadan diğer ekranlar açılmaz/),
    ).toBeInTheDocument();
  });
});
