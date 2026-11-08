// Kurulum sihirbazı testi (sihirbaz kapısı): program yöneticisi hesabı kurulmadan
// ilerlenmez; hesap formu (tanıtıcı + kuralı, ad-soyad, parola politikası ve güç
// göstergesi, tanıtıcı ad-soyadı içeriyorsa gönderimden ÖNCE ve sonra uyarı — engel
// değil) ve ilk hesabın pencereyi yeniden yüklememesi (tasarım §13 D53); kurtarma
// anahtarı (no'su ve üretim tarihiyle) iki grubu geri yazılarak doğrulanıp sunucuda
// damgalanmadan devam edilmez (genel tasarım §4.4.5); anahtar ekranda değilken kâğıttan
// doğrulama ve YENİ anahtar üretme yolları (kaybolan anahtar senaryosu uçtan uca); okul
// adımının (okul kartı: ortak alanlar `okul/OkulKartiAlanlari`) zorunlu alanları ve
// gövdesi (kurum kodu, kademeler, öğrenci mevcudu ve tarihi, yerleşim türü, kantin ve
// personel çalıştırma biçimi, demirbaş onayı); ders yılı
// kaydedilince iki takvim yılının tatilleri eklenir; `setup/complete/` reddi
// iletisiyle gösterilir; ve sihirbaz UÇTAN UCA çalışır.
//
// Backend, `okulApi`/`guvenlikApi` sınırında BELLEK İÇİ SAHTE SUNUCUYLA taklit
// edilir: `setup/status/` durumu backend `services/setup.py` ile aynı kuralla
// hesaplanır (eksik adımlar), böylece adım geçişleri gerçek sırayla sınanır.
// Yönlendirme gerçek router'dan geçer ("/" rotası işaret basar). Veriler uydurmadır.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { todayIso } from "../../lib/format";
import { pencereIcerigi } from "../../lib/kilit";
import { ILK_ACILIS_DURUMU } from "../../test/kurulumDurumu";
import { BOS_OKUL_KARTI, ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type {
  SchoolConfig,
  SchoolConfigBody,
  SchoolYear,
  SetupStatus,
  SetupStep,
} from "../okul/api";

const oapi = vi.hoisted(() => ({
  getSetupStatus: vi.fn(),
  getSchoolConfig: vi.fn(),
  updateSchoolConfig: vi.fn(),
  completeSetup: vi.fn(),
  listSchoolYears: vi.fn(),
  createSchoolYear: vi.fn(),
  configureSchoolTerms: vi.fn(),
  activateSchoolYear: vi.fn(),
  seedHolidays: vi.fn(),
}));
const gapi = vi.hoisted(() => ({
  kur: vi.fn(),
  kurtarmaAnahtariPdf: vi.fn(),
  kurtarmaAnahtariniDogrula: vi.fn(),
  kurtarmaAnahtariniYenile: vi.fn(),
}));
const indirme = vi.hoisted(() => ({ saveBlob: vi.fn() }));

vi.mock("../okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../okul/api")>();
  return { ...actual, okulApi: oapi };
});
vi.mock("../guvenlik/api", () => ({ guvenlikApi: gapi }));
vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: indirme.saveBlob,
}));
// Kapalı gün paneli kendi testinde; burada yalnız hangi yıllarla bağlandığı görünür.
vi.mock("../takvim/KapaliGunlerPaneli", () => ({
  default: ({ yil, yillar }: { yil: number; yillar: number[] }) => (
    <div>
      KAPALI GÜNLER PANELİ {yil} [{yillar.join(",")}]
    </div>
  ),
}));

import { bekleyenKurtarmaAnahtariniYaz } from "../guvenlik/bekleyenAnahtar";
import { kurtarmaAnahtariniNormallestir } from "../guvenlik/kurtarma";
import {
  DERS_YILI_ACIKLAMASI,
  KANTIN_ISLETME_BILGISI,
  OKUL_KARTI_ACIKLAMASI,
} from "../okul/metinler";
import KurulumPage from "./KurulumPage";

const ANAHTAR = "TEST-KURT-ARMA-ANAH-TARI-ABCD-EFGH-JKLM";
const YENI_ANAHTAR = "YENI-ANAH-TARD-EFGH-JKLM-NOPQ-RSTU-VWXY";
const PAROLA = "Deneme-Parola-1";
/** Uydurma ad-soyad; varsayılan tanıtıcıdaki ("yonetici") hiçbir sözcüğü içermez. */
const AD_SOYAD = "Ayşe Deneme";

// --- Bellek içi sahte sunucu -------------------------------------------------

interface Sunucu {
  parola: boolean;
  /** Sunucudaki "saklandı" damgası (`guvenlik.json` → `kurtarma.dogrulandi`). */
  dogrulandi: boolean;
  /** Güvenlik dosyasındaki kurtarma sarmalının anahtarı (yenilemede değişir). */
  anahtar: string;
  okul: SchoolConfig;
  yillar: SchoolYear[];
  donemli: Set<number>;
  tamam: boolean;
}

const BOS_OKUL: SchoolConfig = BOS_OKUL_KARTI;

let sunucu: Sunucu;

/** Backend `missing_school_fields` ile aynı küme (biri eksikse okul adımı eksiktir). */
function okulTamamMi(o: SchoolConfig): boolean {
  return Boolean(
    o.school_name.trim() &&
    o.province.trim() &&
    o.district.trim() &&
    /^\d{6}$/.test(o.institution_code) &&
    o.levels.length > 0 &&
    o.student_count !== null &&
    o.student_count_as_of &&
    o.settlement_type &&
    o.canteen_mode &&
    o.staffing_mode &&
    o.demirbas_onayi,
  );
}

/** Backend `setup_status` ile aynı kural (eksik adımlar sırasıyla). */
function durum(): SetupStatus {
  const aktif = sunucu.yillar.find((y) => y.is_active) ?? null;
  const donemli = aktif !== null && sunucu.donemli.has(aktif.id);
  const eksik: SetupStep[] = [];
  if (!sunucu.parola || !sunucu.dogrulandi) eksik.push("password");
  if (!okulTamamMi(sunucu.okul)) eksik.push("school");
  if (!donemli) eksik.push("calendar");
  return {
    ...ILK_ACILIS_DURUMU,
    setup_completed: sunucu.tamam,
    password_set: sunucu.parola,
    recovery_key_confirmed: sunucu.parola && sunucu.dogrulandi,
    school_name: sunucu.okul.school_name,
    school_info_complete: okulTamamMi(sunucu.okul),
    has_active_school_year: aktif !== null,
    active_school_year: aktif && {
      id: aktif.id,
      name: aktif.name,
      start_date: aktif.start_date,
      end_date: aktif.end_date,
      terms_ready: donemli,
    },
    missing_steps: eksik,
  };
}

function sunucuyuKur(baslangic: Partial<Sunucu> = {}) {
  sunucu = {
    parola: false,
    // Parolası önceden kurulu başlayan senaryolarda anahtar varsayılan olarak doğrulanmıştır.
    dogrulandi: baslangic.parola ?? false,
    anahtar: ANAHTAR,
    okul: { ...BOS_OKUL },
    yillar: [],
    donemli: new Set(),
    tamam: false,
    ...baslangic,
  };
  oapi.getSetupStatus.mockImplementation(async () => durum());
  oapi.getSchoolConfig.mockImplementation(async () => ({ ...sunucu.okul }));
  oapi.updateSchoolConfig.mockImplementation(async (govde: SchoolConfigBody) => {
    sunucu.okul = { ...sunucu.okul, ...govde };
    return { ...sunucu.okul };
  });
  oapi.listSchoolYears.mockImplementation(async () => [...sunucu.yillar]);
  oapi.createSchoolYear.mockImplementation(
    async (govde: { name: string; start_date: string; end_date: string }) => {
      const yil: SchoolYear = { id: sunucu.yillar.length + 5, is_active: false, ...govde };
      sunucu.yillar.push(yil);
      return yil;
    },
  );
  oapi.configureSchoolTerms.mockImplementation(async (id: number) => {
    sunucu.donemli.add(id);
    return [];
  });
  oapi.activateSchoolYear.mockImplementation(async (id: number) => {
    sunucu.yillar = sunucu.yillar.map((y) => ({ ...y, is_active: y.id === id }));
    return sunucu.yillar.find((y) => y.id === id);
  });
  oapi.seedHolidays.mockImplementation(async (year: number) => ({
    year,
    created: 10,
    skipped: 0,
    religious_available: true,
  }));
  oapi.completeSetup.mockImplementation(async () => {
    const eksik = durum().missing_steps;
    if (eksik.length > 0) {
      throw new ApiError(400, "kurulum_eksik", `Kurulum tamamlanamadı. Eksik: ${eksik.join(",")}`);
    }
    sunucu.tamam = true;
    return { setup_completed: true };
  });
  gapi.kur.mockImplementation(async () => {
    sunucu.parola = true;
    sunucu.dogrulandi = false;
    sunucu.anahtar = ANAHTAR;
    return {
      ...durum(),
      recovery_key: ANAHTAR,
      recovery_key_no: 1,
      recovery_key_date: "2026-11-01",
      login_name_warning: null,
      locked: false,
    };
  });
  // Backend `confirm_recovery_key`: anahtar sarmalı açıyorsa damga yazılır.
  gapi.kurtarmaAnahtariniDogrula.mockImplementation(async (anahtar: string) => {
    if (
      kurtarmaAnahtariniNormallestir(anahtar) !== kurtarmaAnahtariniNormallestir(sunucu.anahtar)
    ) {
      throw new ApiError(
        400,
        "validation_error",
        "Kurtarma anahtarı hatalı. Yazdırdığınız kâğıttaki anahtarı olduğu gibi girin.",
      );
    }
    sunucu.dogrulandi = true;
    return { password_set: true, recovery_key_confirmed: true };
  });
  // Backend `renew_recovery_key`: parola doğruysa YENİ anahtar, damga silinir.
  gapi.kurtarmaAnahtariniYenile.mockImplementation(async (parola: string) => {
    if (parola !== PAROLA) throw new ApiError(400, "validation_error", "Parola hatalı.");
    sunucu.anahtar = YENI_ANAHTAR;
    sunucu.dogrulandi = false;
    return {
      password_set: true,
      recovery_key_confirmed: false,
      recovery_key: YENI_ANAHTAR,
      recovery_key_no: 2,
      recovery_key_date: "2026-11-02",
    };
  });
}

const TAM_OKUL: SchoolConfig = {
  ...ORNEK_OKUL_KARTI,
  school_name: "Deneme Anadolu Lisesi",
  setup_completed: false,
};

const AKTIF_YIL: SchoolYear = {
  id: 3,
  name: "2026-2027",
  start_date: "2026-09-07",
  end_date: "2027-06-25",
  is_active: true,
};

/** `state` kapı yönlendirmesini taklit eder (KurulumKapisi'nin taşıdığı sebep). */
function renderPage(state?: unknown) {
  return render(
    <SnackbarProvider>
      <ConfirmProvider>
        <MemoryRouter initialEntries={[{ pathname: "/kurulum", state }]}>
          <Routes>
            <Route path="/kurulum" element={<KurulumPage />} />
            <Route path="/" element={<div>PANEL EKRANI</div>} />
          </Routes>
        </MemoryRouter>
      </ConfirmProvider>
    </SnackbarProvider>,
  );
}

const ileri = (ad: string | RegExp) => screen.getByRole("button", { name: ad });

/** Paneldeki anahtarın sorulan iki grubunu (sabit rastgele: 1. ve 2.) yazar ve devam eder. */
async function anahtariDogrulaVeDevamEt(user: ReturnType<typeof userEvent.setup>, anahtar: string) {
  const gruplar = anahtar.split("-");
  await user.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
  await user.type(screen.getByLabelText("1. grup"), gruplar[0]);
  await user.type(screen.getByLabelText("2. grup"), gruplar[1]);
  // İki grup tutunca TAM anahtar sunucuda doğrulanır; İleri ondan sonra açılır.
  await waitFor(() => expect(ileri("Devam")).toBeEnabled());
  expect(gapi.kurtarmaAnahtariniDogrula).toHaveBeenLastCalledWith(anahtar);
  await user.click(ileri("Devam"));
}

/** "Parola" alanı (tekrarı ve "Parola gücü" göstergesinden ayrışsın diye tam etiket). */
const PAROLA_ALANI = /^Parola \*$/;

/** Hesap formunu doldurur (tanıtıcı varsayılan kalır) ve "Hesabı kur"a basar. */
async function hesapFormunuDoldurVeKur(
  user: ReturnType<typeof userEvent.setup>,
  parola = PAROLA,
  tekrar = parola,
) {
  await user.type(await screen.findByLabelText(/^Ad-soyad/), AD_SOYAD);
  await user.type(screen.getByLabelText(PAROLA_ALANI), parola);
  await user.type(screen.getByLabelText(/^Parola \(tekrar\)/), tekrar);
  await user.click(screen.getByRole("button", { name: "Hesabı kur" }));
}

/** Hesabı kurar ve anahtarın sorulan iki grubunu (sabit rastgele: 1. ve 2.) doğrular. */
async function parolaAdiminiGec(user: ReturnType<typeof userEvent.setup>) {
  await hesapFormunuDoldurVeKur(user);
  expect(await screen.findByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
  await anahtariDogrulaVeDevamEt(user, ANAHTAR);
}

/** Okul adımının bütün zorunlu alanlarını doldurur (mevcudun tarihi varsayılan: bugün). */
async function okulAdiminiDoldur(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/^Okul adı/), "Deneme Anadolu Lisesi");
  await user.type(screen.getByLabelText(/^Kurum kodu/), "123456");
  await user.type(screen.getByLabelText(/^İl \*$/), "Ankara");
  await user.type(screen.getByLabelText(/^İlçe/), "Örnek İlçe");
  await user.click(screen.getByRole("checkbox", { name: "Ortaöğretim (lise)" }));
  await user.type(screen.getByLabelText(/^Öğrenci mevcudu/), "1.234");
  await user.click(screen.getByRole("radio", { name: "Büyükşehir statüsündeki il" }));
  await user.click(screen.getByRole("radio", { name: "Kiraya veriliyor" }));
  await user.click(screen.getByRole("radio", { name: "Personel çalıştırmıyor" }));
  await user.click(screen.getByRole("checkbox", { name: /Bu bilgisayar okul demirbaşıdır/ }));
}

beforeEach(() => {
  sunucuyuKur();
  // Gerçek `saveBlob` hep sonuç döndürür; sahte de öyle olsun.
  indirme.saveBlob.mockResolvedValue("kaydedildi");
  // Bekleyen anahtar modül belleğindedir: testler arasında sızmasın.
  bekleyenKurtarmaAnahtariniYaz(null);
  // Doğrulanacak gruplar sabit: 1. ve 2. grup (rastgeleIkiGrup(8, () => 0.125)).
  vi.spyOn(Math, "random").mockReturnValue(0.125);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

describe("KurulumPage — 1. adım: program yöneticisi hesabı (atlanamaz)", () => {
  it("ilk açılışta hesap adımından başlar; hesap kurulmadan ilerlenemez", async () => {
    renderPage();

    expect(await screen.findByText("1. Program Yöneticisi Hesabı")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Kurulum Sihirbazı" }),
    ).toBeInTheDocument();
    expect(ileri("Devam")).toBeDisabled();
    expect(
      screen.getByText("Devam etmek için program yöneticisi hesabını kurun."),
    ).toBeInTheDocument();
    // Adım rayının adı sözlük §4.4'tekidir; ray tıklanmaz (hesap kapısı kapalı).
    const ray = screen.getByRole("list", { name: "Kurulum adımları" });
    expect(within(ray).getByText("Program Yöneticisi Hesabı")).toBeInTheDocument();
    expect(within(ray).queryAllByRole("button")).toHaveLength(0);
    // Eski "isteğe bağlı parola" ve tek "yönetici parolası" dili yoktur.
    expect(screen.queryByText(/isteğe bağlı/i)).toBeNull();
    expect(document.body.textContent).not.toMatch(/yönetici parolası/i);
    expect(screen.queryByText("2. Okul Bilgileri")).toBeNull();
  });

  it("form: tanıtıcı varsayılan “yonetici”, kural metni, ad-soyad, parola gücü göstergesi", async () => {
    renderPage();

    expect(await screen.findByLabelText(/^Tanıtıcı/)).toHaveValue("yonetici");
    expect(screen.getByText(/Kilit ekranında herkese görünen hesap adıdır/)).toBeInTheDocument();
    expect(screen.getByText(/şifreli saklanır, kilit ekranında görünmez/)).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "Parola gücü" })).toBeInTheDocument();
    // Parola cümlesi önerisi (yerel öneri; tasarım TK15).
    expect(screen.getByText(/en az 12 karakter/)).toBeInTheDocument();
  });

  it("okul bilgileri önceden tamam olsa bile hesap yokken adım rayı atlatmaz", async () => {
    sunucuyuKur({ okul: { ...TAM_OKUL } });
    renderPage();
    expect(await screen.findByText("1. Program Yöneticisi Hesabı")).toBeInTheDocument();
    const ray = screen.getByRole("list", { name: "Kurulum adımları" });
    expect(within(ray).queryAllByRole("button")).toHaveLength(0);
  });

  it("ad-soyad girilmeden hesap kurulamaz", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.type(await screen.findByLabelText(PAROLA_ALANI), PAROLA);
    await user.type(screen.getByLabelText(/^Parola \(tekrar\)/), PAROLA);
    expect(screen.getByRole("button", { name: "Hesabı kur" })).toBeDisabled();
    expect(gapi.kur).not.toHaveBeenCalled();
  });

  it("eşleşmeyen parola tekrarında istek atmaz", async () => {
    const user = userEvent.setup();
    renderPage();
    await hesapFormunuDoldurVeKur(user, PAROLA, "baska");
    expect(await screen.findByText("Parolalar eşleşmedi.")).toBeInTheDocument();
    // Eşleşmeme tekrar alanının hatasıdır; ilk alan işaretlenmez.
    expect(screen.getByLabelText(/^Parola \(tekrar\)/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText(PAROLA_ALANI)).not.toHaveAttribute("aria-invalid");
    expect(gapi.kur).not.toHaveBeenCalled();
  });

  it("parola politikası gönderimden önce denetlenir (sunucunun iletileriyle)", async () => {
    const user = userEvent.setup();
    renderPage();
    await hesapFormunuDoldurVeKur(user, "kisa");
    expect(await screen.findByText("Parola en az 8 karakter olmalıdır.")).toBeInTheDocument();
    // Politika iletisi Parola alanının altındadır (tekrar alanının değil); kural metni de
    // o alana bağlıdır.
    expect(screen.getByLabelText(PAROLA_ALANI)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText(PAROLA_ALANI)).toHaveAccessibleDescription(
      /^Parola en az 8 karakter olmalıdır\. En az 8 karakter; küçük harf/,
    );
    expect(screen.getByLabelText(/^Parola \(tekrar\)/)).not.toHaveAttribute("aria-invalid");
    expect(gapi.kur).not.toHaveBeenCalled();

    await user.clear(screen.getByLabelText(PAROLA_ALANI));
    await user.clear(screen.getByLabelText(/^Parola \(tekrar\)/));
    await user.type(screen.getByLabelText(PAROLA_ALANI), "uzunamaduz1");
    await user.type(screen.getByLabelText(/^Parola \(tekrar\)/), "uzunamaduz1");
    await user.click(screen.getByRole("button", { name: "Hesabı kur" }));
    expect(
      await screen.findByText(
        "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: büyük harf, simge.",
      ),
    ).toBeInTheDocument();
    expect(gapi.kur).not.toHaveBeenCalled();
  });

  it("kurala uymayan tanıtıcı alanın altında söylenir, istek atılmaz", async () => {
    const user = userEvent.setup();
    renderPage();
    const tanitici = await screen.findByLabelText(/^Tanıtıcı/);
    await user.clear(tanitici);
    await user.type(tanitici, "iki sözcük");
    await hesapFormunuDoldurVeKur(user);
    expect(await screen.findByText(/Tanıtıcı 2-32 karakter olmalıdır/)).toBeInTheDocument();
    expect(gapi.kur).not.toHaveBeenCalled();
  });

  it("tanıtıcı ad-soyadı içeriyorsa gönderimden ÖNCE uyarır ama engellemez", async () => {
    const user = userEvent.setup();
    renderPage();
    const tanitici = await screen.findByLabelText(/^Tanıtıcı/);
    await user.clear(tanitici);
    await user.type(tanitici, "Ayse.D");
    // Ad-soyad yazılmadan uyarı yoktur.
    expect(screen.queryByText(/Tanıtıcı hesap sahibinin adını içeriyor/)).toBeNull();
    await user.type(screen.getByLabelText(/^Ad-soyad/), "Ayşe Deneme");
    // Türkçe harf katlanır ("Ayşe" ≡ "ayse"); uyarı canlı bölgede, engel değil.
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Tanıtıcı hesap sahibinin adını içeriyor.",
    );
    await user.type(screen.getByLabelText(PAROLA_ALANI), PAROLA);
    await user.type(screen.getByLabelText(/^Parola \(tekrar\)/), PAROLA);
    await user.click(screen.getByRole("button", { name: "Hesabı kur" }));

    // Tanıtıcı Türkçe küçük harfe çevrilip gönderilir; ad-soyadın ara boşlukları tekleşir.
    await waitFor(() =>
      expect(gapi.kur).toHaveBeenCalledWith({
        tanitici: "ayse.d",
        ad_soyad: "Ayşe Deneme",
        parola: PAROLA,
      }),
    );
  });

  it("kimlik numarasına benzeyen 11 rakamın uyarısı ad-soyad yazılmadan da çıkar, engel değildir", async () => {
    const user = userEvent.setup();
    renderPage();
    const tanitici = await screen.findByLabelText(/^Tanıtıcı/);
    await user.clear(tanitici);
    // Uydurma sayı (sağlaması aranmaz; orkestratör maddesi F-5).
    await user.type(tanitici, "yonetici-12345678901");
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Tanıtıcı T.C. kimlik numarasına benzeyen 11 haneli bir sayı içeriyor.",
    );
    await user.type(screen.getByLabelText(/^Ad-soyad/), "Ayşe Deneme");
    await user.type(screen.getByLabelText(PAROLA_ALANI), PAROLA);
    await user.type(screen.getByLabelText(/^Parola \(tekrar\)/), PAROLA);
    await user.click(screen.getByRole("button", { name: "Hesabı kur" }));
    await waitFor(() =>
      expect(gapi.kur).toHaveBeenCalledWith(
        expect.objectContaining({ tanitici: "yonetici-12345678901" }),
      ),
    );
  });

  it("sunucunun döndürdüğü tanıtıcı uyarısı hesap kurulduktan sonra anahtarın üstünde kalır", async () => {
    const user = userEvent.setup();
    const uyari =
      "Tanıtıcı hesap sahibinin adını içeriyor. Tanıtıcı kilit ekranında herkese görünür; " +
      "rolden türeyen bir tanıtıcı seçmeniz önerilir.";
    gapi.kur.mockImplementationOnce(async () => {
      sunucu.parola = true;
      return {
        ...durum(),
        recovery_key: ANAHTAR,
        recovery_key_no: 1,
        recovery_key_date: "2026-11-01",
        login_name_warning: uyari,
      };
    });
    renderPage();
    await hesapFormunuDoldurVeKur(user);

    expect(await screen.findByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
    expect(screen.getByText(uyari)).toBeInTheDocument();
  });

  it("backend reddi iletisiyle bantta gösterilir", async () => {
    const user = userEvent.setup();
    gapi.kur.mockRejectedValue(
      new ApiError(400, "validation_error", "Hesap sahibinin adı-soyadı boş olamaz.", {}),
    );
    renderPage();
    await hesapFormunuDoldurVeKur(user);
    expect(await screen.findByText("Hesap sahibinin adı-soyadı boş olamaz.")).toBeInTheDocument();
    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
  });

  it("anahtar no'su ve tarihiyle gösterilir; iki grup doğrulanmadan devam edilemez, doğrulanınca okul adımına geçer", async () => {
    const user = userEvent.setup();
    renderPage();
    await hesapFormunuDoldurVeKur(user);

    expect(await screen.findByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
    expect(screen.getByTestId("kurtarma-kimligi")).toHaveTextContent(
      "Anahtar no 1 · üretim tarihi 01.11.2026",
    );
    // İlk program yöneticisi hesabı: Türkçe gövde, varsayılan tanıtıcı (tasarım §4.4.4).
    expect(gapi.kur).toHaveBeenCalledWith({
      tanitici: "yonetici",
      ad_soyad: AD_SOYAD,
      parola: PAROLA,
    });
    // İlk hesap pencereyi yeniden YÜKLEMEZ (tasarım §13 D53): anahtar ekranda kalır.
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    expect(await screen.findByText("Program yöneticisi hesabı kuruldu.")).toBeInTheDocument();
    expect(ileri("Devam")).toBeDisabled();
    expect(
      screen.getByText("Devam etmek için kurtarma anahtarını sakladığınızı doğrulayın."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
    await user.type(screen.getByLabelText("1. grup"), "TEST");
    await user.type(screen.getByLabelText("2. grup"), "YANL");
    expect(ileri("Devam")).toBeDisabled();

    await user.clear(screen.getByLabelText("2. grup"));
    await user.type(screen.getByLabelText("2. grup"), "kurt");
    await waitFor(() => expect(ileri("Devam")).toBeEnabled());
    await user.click(ileri("Devam"));

    expect(await screen.findByText("2. Okul Bilgileri")).toBeInTheDocument();
    // Geri dönülünce anahtar bir daha gösterilmez (bellekte tutulmaz).
    await user.click(screen.getByRole("button", { name: "Geri" }));
    expect(
      await screen.findByText(/Hesap kurulu, kurtarma anahtarının saklandığı doğrulandı/),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
    expect(screen.getByRole("heading", { name: "Kurtarma anahtarı belgesi" })).toBeInTheDocument();
  });

  it("anahtar sihirbazdan PDF olarak kaydedilir (backend'in Content-Disposition adıyla)", async () => {
    const user = userEvent.setup();
    const pdf = new Blob(["%PDF-"]);
    gapi.kurtarmaAnahtariPdf.mockResolvedValue(pdf);
    renderPage();
    await hesapFormunuDoldurVeKur(user);

    await user.click(await screen.findByRole("button", { name: "PDF olarak kaydet" }));

    await waitFor(() => expect(gapi.kurtarmaAnahtariPdf).toHaveBeenCalledWith(ANAHTAR));
    expect(indirme.saveBlob).toHaveBeenCalledWith(
      pdf,
      expect.stringMatching(/^Kurtarma-Anahtarı-Belgesi_\d{2}\.\d{2}\.\d{4}\.pdf$/),
      { evKlasorunde: true },
    );
  });
});

describe("KurulumPage — 1. adım: anahtar ekranda değilken", () => {
  it("parola kurulu ama anahtar doğrulanmamış: uyarı, ray kilitli, kâğıttaki anahtarla doğrulanır", async () => {
    const user = userEvent.setup();
    sunucuyuKur({ parola: true, dogrulandi: false, okul: { ...TAM_OKUL } });
    renderPage();

    expect(await screen.findByText(/Kurtarma anahtarı doğrulanmadı/)).toBeInTheDocument();
    expect(ileri("Devam")).toBeDisabled();
    expect(
      screen.getByText("Devam etmek için kurtarma anahtarını doğrulayın ya da yenisini üretin."),
    ).toBeInTheDocument();
    const ray = screen.getByRole("list", { name: "Kurulum adımları" });
    expect(within(ray).queryAllByRole("button")).toHaveLength(0);

    // Yanlış anahtar: backend iletisi, damga yok.
    await user.type(screen.getByLabelText(/^Kurtarma anahtarı/), "YANLIS-ANAHTAR");
    await user.click(screen.getByRole("button", { name: "Doğrula" }));
    expect(await screen.findByText(/Kurtarma anahtarı hatalı/)).toBeInTheDocument();
    expect(sunucu.dogrulandi).toBe(false);

    await user.clear(screen.getByLabelText(/^Kurtarma anahtarı/));
    await user.type(screen.getByLabelText(/^Kurtarma anahtarı/), ANAHTAR.toLowerCase());
    await user.click(screen.getByRole("button", { name: "Doğrula" }));

    expect(
      await screen.findByText(/Hesap kurulu, kurtarma anahtarının saklandığı doğrulandı/),
    ).toBeInTheDocument();
    expect(sunucu.dogrulandi).toBe(true);
    await waitFor(() => expect(ileri("Devam")).toBeEnabled());
  });

  it("kaybolan anahtar: yenile → yeni anahtar → doğrula → tamamla", async () => {
    const user = userEvent.setup();
    // Parola kuruldu, anahtar gösterildi ama pencere kapandı: anahtar bellekte yok.
    sunucuyuKur({ parola: true, dogrulandi: false, okul: { ...TAM_OKUL } });
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    renderPage();

    // Tamamlamak mümkün değil: sunucu 1. adımı eksik sayar.
    expect(await screen.findByText(/Kurtarma anahtarı doğrulanmadı/)).toBeInTheDocument();
    expect(durum().missing_steps).toEqual(["password"]);

    await user.click(screen.getByRole("button", { name: "Kurtarma anahtarını yenile" }));
    const diyalog = await screen.findByRole("dialog", { name: "Kurtarma anahtarı yenilensin mi?" });
    // Dürüst metin: eski yedekler eski anahtarla açılır.
    expect(within(diyalog).getByText(/Bugünden önce alınmış yedekler/)).toBeInTheDocument();
    await user.type(within(diyalog).getByLabelText(/^Parolanız/), PAROLA);
    await user.click(within(diyalog).getByRole("button", { name: "Yeni anahtar üret" }));

    await waitFor(() => expect(gapi.kurtarmaAnahtariniYenile).toHaveBeenCalledWith(PAROLA));
    expect(await screen.findByTestId("kurtarma-anahtari")).toHaveTextContent(YENI_ANAHTAR);
    // Yeni anahtarın no'su bir artmıştır; kâğıda yazılacak kimlik anahtarın üstünde.
    expect(screen.getByTestId("kurtarma-kimligi")).toHaveTextContent(
      "Anahtar no 2 · üretim tarihi 02.11.2026",
    );
    expect(ileri("Devam")).toBeDisabled();

    await anahtariDogrulaVeDevamEt(user, YENI_ANAHTAR);
    expect(sunucu.dogrulandi).toBe(true);

    expect(await screen.findByText("2. Okul Bilgileri")).toBeInTheDocument();
    await user.click(ileri("Kaydet ve devam et"));
    await waitFor(() => expect(ileri("Kurulumu tamamla")).toBeEnabled());
    await user.click(ileri("Kurulumu tamamla"));

    expect(await screen.findByText("PANEL EKRANI")).toBeInTheDocument();
    expect(sunucu.tamam).toBe(true);
    expect(sunucu.anahtar).toBe(YENI_ANAHTAR);
  });

  it("yenilemede yanlış parola: ileti gösterilir, yeni anahtar üretilmez", async () => {
    const user = userEvent.setup();
    sunucuyuKur({ parola: true, dogrulandi: false });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Kurtarma anahtarını yenile" }));
    const diyalog = await screen.findByRole("dialog");
    await user.type(within(diyalog).getByLabelText(/^Parolanız/), "yanlis-parola");
    await user.click(within(diyalog).getByRole("button", { name: "Yeni anahtar üret" }));

    expect(await within(diyalog).findByText("Parola hatalı.")).toBeInTheDocument();
    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
    expect(sunucu.anahtar).toBe(ANAHTAR);
  });

  it("kurulumu önceden tamamlanmış damgasız programda ray kilitlenmez, yalnız uyarı çıkar", async () => {
    sunucuyuKur({ parola: true, dogrulandi: false, okul: { ...TAM_OKUL }, tamam: true });
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    renderPage();

    expect(await screen.findByText(/Kurtarma anahtarı doğrulanmadı/)).toBeInTheDocument();
    expect(screen.getByText(/Kurulum daha önce tamamlanmıştı/)).toBeInTheDocument();
    const ray = screen.getByRole("list", { name: "Kurulum adımları" });
    expect(within(ray).getAllByRole("button").length).toBeGreaterThan(0);
    expect(ileri("Devam")).toBeEnabled();
  });
});

describe("KurulumPage — 2. adım: okul bilgileri", () => {
  beforeEach(() => sunucuyuKur({ parola: true }));

  it("zorunlu alanlar olmadan kaydetmez; her alanın iletisi altında yazılır", async () => {
    const user = userEvent.setup();
    renderPage();
    expect(await screen.findByText("2. Okul Bilgileri")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/Okul adı/), "Deneme Anadolu Lisesi");
    await user.type(screen.getByLabelText(/^Kurum kodu/), "12345");
    await user.type(screen.getByLabelText(/^Öğrenci mevcudu/), "12,5");
    await user.click(ileri("Kaydet ve devam et"));

    expect(await screen.findByText("Zorunlu alanları doldurun.")).toBeInTheDocument();
    for (const ileti of [
      "İl zorunludur.",
      "İlçe zorunludur.",
      "Kurum kodu altı haneli bir sayıdır.",
      "En az bir kademe seçin.",
      "Öğrenci mevcudu 0 ile 99999 arasında bir tam sayıdır.",
      "Yerleşim türünü seçin.",
      "Kantin işletme biçimini seçin.",
      "Personel çalıştırma biçimini seçin.",
    ]) {
      expect(screen.getByText(ileti)).toBeInTheDocument();
    }
    expect(screen.getByText(/onay zorunludur/)).toBeInTheDocument();
    // Mevcudun tarihi varsayılan olarak bugündür: iletisi çıkmaz.
    expect(screen.queryByText("Mevcudun tarihi zorunludur.")).toBeNull();
    expect(oapi.updateSchoolConfig).not.toHaveBeenCalled();
    expect(screen.getByText("2. Okul Bilgileri")).toBeInTheDocument();
  });

  it("açıklama okul kartının kullanıldığı yerleri söyler; kısa ad ve hazırlık sınıfı yoktur", async () => {
    renderPage();
    expect(await screen.findByText("2. Okul Bilgileri")).toBeInTheDocument();
    expect(screen.getByText(OKUL_KARTI_ACIKLAMASI)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Kısa ad/)).toBeNull();
    expect(document.body.textContent).not.toMatch(/Hazırlık|En çok 24 karakter/);
    expect(document.body.textContent).not.toMatch(/etiket|üye kart|kayıp ve hasar|son sınıf/i);
  });

  it("yeni alanlarla tam gövdeyi gönderir ve 3. adıma geçer", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("2. Okul Bilgileri");
    await okulAdiminiDoldur(user);
    await user.click(screen.getByRole("checkbox", { name: "Ortaokul" }));
    await user.click(screen.getByRole("radio", { name: "Birlikçe işletiliyor" }));
    expect(screen.getByText(KANTIN_ISLETME_BILGISI)).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: /eğitim kampüsündedir/ }));
    await user.type(screen.getByLabelText(/^Okulun açılış tarihi/), "2025-09-08");
    await user.type(screen.getByLabelText("Bilgisayarın demirbaş no'su"), "BLG-17");
    await user.click(ileri("Kaydet ve devam et"));

    await waitFor(() =>
      expect(oapi.updateSchoolConfig).toHaveBeenCalledWith({
        school_name: "Deneme Anadolu Lisesi",
        province: "Ankara",
        district: "Örnek İlçe",
        principal_name: "",
        institution_code: "123456",
        levels: ["ORTAOKUL", "ORTAOGRETIM"],
        student_count: 1234,
        student_count_as_of: todayIso(),
        settlement_type: "BUYUKSEHIR",
        canteen_mode: "BIRLIKCE_ISLETILIYOR",
        staffing_mode: "CALISTIRMIYOR",
        in_campus: true,
        opened_on: "2025-09-08",
        demirbas_onayi: true,
        demirbas_no: "BLG-17",
      }),
    );
    expect(await screen.findByText("3. Ders Yılı")).toBeInTheDocument();
    expect(sunucu.okul.levels).toEqual(["ORTAOKUL", "ORTAOGRETIM"]);
  });

  it("kayıtlı okul kartı forma dolar; mevcudun tarihi kayıttakidir", async () => {
    const user = userEvent.setup();
    sunucuyuKur({ parola: true, okul: { ...TAM_OKUL } });
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    renderPage();
    const ray = await screen.findByRole("list", { name: "Kurulum adımları" });
    await user.click(within(ray).getByRole("button", { name: /Okul Bilgileri/ }));

    expect(screen.getByLabelText(/^Kurum kodu/)).toHaveValue("123456");
    expect(screen.getByRole("checkbox", { name: "Ortaöğretim (lise)" })).toBeChecked();
    expect(screen.getByLabelText(/^Öğrenci mevcudu/)).toHaveValue("1234");
    expect(screen.getByLabelText(/^Mevcudun tarihi/)).toHaveValue("2026-10-01");
    expect(screen.getByRole("radio", { name: "Kiraya veriliyor" })).toBeChecked();
  });

  it("kayıt hatasında Türkçe hata bandı + alan hatası gösterilir, adım değişmez", async () => {
    const user = userEvent.setup();
    sunucuyuKur({ parola: true, okul: { ...TAM_OKUL } });
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    oapi.updateSchoolConfig.mockRejectedValue(
      new ApiError(400, "validation_error", "Mevcudun tarihi bugünden sonra olamaz.", {
        student_count_as_of: ["Mevcudun tarihi bugünden sonra olamaz."],
      }),
    );
    renderPage();
    // Hepsi tamamken sihirbaz son adımdan açılır; okul adımına raydan dönülür.
    const ray = await screen.findByRole("list", { name: "Kurulum adımları" });
    await user.click(within(ray).getByRole("button", { name: /Okul Bilgileri/ }));
    await user.click(ileri("Kaydet ve devam et"));

    expect(await screen.findAllByText("Mevcudun tarihi bugünden sonra olamaz.")).not.toHaveLength(
      0,
    );
    expect(screen.getByText("2. Okul Bilgileri")).toBeInTheDocument();
  });
});

describe("KurulumPage — 3. adım: ders yılı ve kapalı günler", () => {
  beforeEach(() => sunucuyuKur({ parola: true, okul: { ...TAM_OKUL } }));

  it("ders yılı kaydedilince dönemler kurulur, yıl aktifleşir ve iki takvim yılı tohumlanır", async () => {
    const user = userEvent.setup();
    renderPage();
    expect(await screen.findByText("3. Ders Yılı")).toBeInTheDocument();
    expect(screen.getByText(DERS_YILI_ACIKLAMASI, { exact: false })).toBeInTheDocument();
    expect(screen.queryByText(/Şube kataloğu/)).toBeNull();
    expect(ileri("Kurulumu tamamla")).toBeDisabled();
    // Aktif yıl yokken kapalı gün paneli görünmez.
    expect(screen.queryByText(/KAPALI GÜNLER PANELİ/)).toBeNull();

    await user.clear(screen.getByLabelText(/^Ad/));
    await user.type(screen.getByLabelText(/^Ad/), "2026-2027");
    await user.click(screen.getByRole("button", { name: "Ders yılını kaydet ve aktifleştir" }));

    await waitFor(() => expect(oapi.activateSchoolYear).toHaveBeenCalled());
    expect(oapi.configureSchoolTerms).toHaveBeenCalled();
    await waitFor(() => expect(oapi.seedHolidays).toHaveBeenCalledTimes(2));
    const tohumlanan = oapi.seedHolidays.mock.calls.map(([y]) => y as number);
    expect(tohumlanan[1] - tohumlanan[0]).toBe(1);
    expect(
      await screen.findByText(`KAPALI GÜNLER PANELİ ${tohumlanan[0]} [${tohumlanan.join(",")}]`),
    ).toBeInTheDocument();
    // Kapalı günlerin gerekçesi iş günü hesabıdır; ödünç iadesinden söz edilmez.
    expect(screen.getByText(/iş günüyle verilen süreler/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/iade tarihi/i);
    await waitFor(() => expect(ileri("Kurulumu tamamla")).toBeEnabled());
  });

  it("dini bayram tarihleri programda yoksa uyarı gösterilir", async () => {
    const user = userEvent.setup();
    oapi.seedHolidays.mockImplementation(async (year: number) => ({
      year,
      created: 5,
      skipped: 0,
      religious_available: year < 2027,
    }));
    renderPage();
    await screen.findByText("3. Ders Yılı");
    await user.click(screen.getByRole("button", { name: "Ders yılını kaydet ve aktifleştir" }));
    expect(await screen.findByText(/dini bayram tarihleri yok/)).toBeInTheDocument();
  });

  it("aktif yılın dönemleri yoksa dönem formu çıkar; kaydedilince tamamlanabilir", async () => {
    const user = userEvent.setup();
    sunucu.yillar = [AKTIF_YIL];
    renderPage();

    expect(await screen.findByText("2026-2027 Dönemleri")).toBeInTheDocument();
    expect(ileri("Kurulumu tamamla")).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Dönemleri kaydet" }));

    await waitFor(() =>
      expect(oapi.configureSchoolTerms).toHaveBeenCalledWith(AKTIF_YIL.id, {
        first_term_end: "2027-01-16",
        second_term_start: "2027-02-02",
      }),
    );
    await waitFor(() => expect(ileri("Kurulumu tamamla")).toBeEnabled());
  });

  it("backend eksik adım reddi (kurulum_eksik) iletisiyle bantta gösterilir", async () => {
    const user = userEvent.setup();
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    oapi.completeSetup.mockRejectedValue(
      new ApiError(
        400,
        "kurulum_eksik",
        "Kurulum tamamlanamadı. 1. adım (program yöneticisi hesabı): hesap kurulmadı.",
      ),
    );
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Kurulumu tamamla" }));
    expect(await screen.findByText(/1\. adım \(program yöneticisi hesabı\)/)).toBeInTheDocument();
    expect(screen.queryByText("PANEL EKRANI")).toBeNull();
  });
});

describe("KurulumPage — uçtan uca", () => {
  it("parola → kurtarma anahtarı → okul bilgileri → ders yılı → Kurulumu tamamla → Genel Bakış", async () => {
    const user = userEvent.setup();
    renderPage();

    // 1. adım
    await parolaAdiminiGec(user);

    // 2. adım
    expect(await screen.findByText("2. Okul Bilgileri")).toBeInTheDocument();
    await okulAdiminiDoldur(user);
    await user.click(ileri("Kaydet ve devam et"));

    // 3. adım
    expect(await screen.findByText("3. Ders Yılı")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ders yılını kaydet ve aktifleştir" }));
    await waitFor(() => expect(ileri("Kurulumu tamamla")).toBeEnabled());

    // Adım rayında üç adım da tamam.
    const ray = screen.getByRole("list", { name: "Kurulum adımları" });
    expect(within(ray).getAllByRole("button")).toHaveLength(2); // tamam + tıklanabilir: 1 ve 2

    await user.click(ileri("Kurulumu tamamla"));
    expect(await screen.findByText("PANEL EKRANI")).toBeInTheDocument();
    expect(sunucu.tamam).toBe(true);
    expect(sunucu.parola).toBe(true);
  });
});

describe("KurulumPage — bilgilendirme", () => {
  it("kapı yönlendirmesiyle gelindiyse sebebi söyler", async () => {
    renderPage({ kapiYonlendirdi: "/kisiler" });
    expect(await screen.findByText(/bu yüzden buraya getirildiniz/)).toBeInTheDocument();
  });

  it("kurulum daha önce tamamlandıysa bunu söyler ve son adımdan açılır", async () => {
    sunucuyuKur({ parola: true, okul: { ...TAM_OKUL }, tamam: true });
    sunucu.yillar = [AKTIF_YIL];
    sunucu.donemli.add(AKTIF_YIL.id);
    renderPage();
    expect(await screen.findByText(/Kurulum daha önce tamamlanmıştı/)).toBeInTheDocument();
    expect(await screen.findByText("3. Ders Yılı")).toBeInTheDocument();
  });

  it("durum okunamazsa Türkçe hata bandı gösterilir", async () => {
    oapi.getSetupStatus.mockRejectedValue(new ApiError(500, "error", "Sunucuya ulaşılamadı."));
    renderPage();
    expect(await screen.findByText("Sunucuya ulaşılamadı.")).toBeInTheDocument();
  });
});
