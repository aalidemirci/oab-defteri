// Güvenlik ayarları testi: dürüst KVKK metni ve "en zayıf hesap parolası" sınırı,
// "Hesap ve Parola" kartı (oturumdaki hesabın rol etiketi + tanıtıcısı, kişi adı yok),
// kendi parolasını değiştirme akışı (parola politikasının ön denetimi, eskisiyle aynı
// olamaz, güç göstergesi; hesap dilinde snackbar), "Parolayı kaldır" ve "hesabı kur"
// eylemlerinin OLMAMASI (tasarım §4.4.3 — hesap yalnız kurulum sihirbazının ilk adımında
// kurulur; burada sihirbaza bağlantı durur), boşta kilit süresi kartı (3-30, varsayılan
// 10), kurtarma anahtarı belgesini elindeki anahtarla yeniden alma kartı (katalog dışı
// program belgesi, tasarım §9.7; güncel anahtarın no'su ve tarihi) ve kurtarma
// anahtarının doğrulanması/yenilenmesi (aile iskeletinin doğrulama deseni; tasarım
// §4.4.4; yenileme §13 D14). Parola değişimi oturumdaki hesabın kendi parolasıdır
// (Türkçe gövdeli oturum ucu; pencere yeniden yüklenmez), Kilitle üst çubuktakiyle aynı
// yoldur (pencere yeniden yüklenir). Veriler uydurmadır.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { pencereIcerigi } from "../../lib/kilit";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";

const guvenlik = vi.hoisted(() => ({
  durum: vi.fn(),
  kur: vi.fn(),
  kurtarmaAnahtariPdf: vi.fn(),
  kurtarmaAnahtariniDogrula: vi.fn(),
  kurtarmaAnahtariniYenile: vi.fn(),
}));
const download = vi.hoisted(() => ({ saveBlob: vi.fn() }));

const oturum = vi.hoisted(() => ({
  ozet: vi.fn(),
  kilitle: vi.fn(),
  parolaDegistir: vi.fn(),
  bostaKilitSuresi: vi.fn(),
  bostaKilitSuresiniYaz: vi.fn(),
}));

vi.mock("./api", () => ({ guvenlikApi: guvenlik }));
vi.mock("../oturum/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../oturum/api")>()),
  oturumApi: oturum,
}));
// Yedek kartlarının kendi testleri var; burada yalnız görünüp görünmedikleri (rol süzmesi) sınanır.
vi.mock("./SifreliYedekleme", () => ({ default: () => <div>ŞİFRELİ YEDEK KARTI</div> }));
vi.mock("./YedektenGeriYukleme", () => ({ default: () => <div>GERİ YÜKLEME KARTI</div> }));
vi.mock("./YedekRaporuKarti", () => ({ default: () => <div>YEDEK RAPORU KARTI</div> }));
vi.mock("../../lib/download", async (importOriginal) => {
  const gercek = await importOriginal<typeof import("../../lib/download")>();
  return { ...gercek, saveBlob: download.saveBlob };
});

import { YETENEK_ADLARI } from "../oturum/api";
import { OTURUM_DEGISTI_OLAYI } from "../oturum/eylemler";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import { BOSTA_DK_TAM_SAYI_ILETISI, bostaDakikaSorunu } from "./BostaKilitSuresiKarti";
import GuvenlikAyarlari from "./GuvenlikAyarlari";
import { bekleyenKurtarmaAnahtariniYaz } from "./bekleyenAnahtar";

const PAROLASIZ = {
  password_set: false,
  locked: false,
  security_file_missing: false,
  reset_available: false,
  transition_pending: false,
  transition: "",
  recovery_key_confirmed: false,
  protected_fields: ["ad", "soyad"],
  account_count: 0,
  recovery_key_no: null,
  recovery_key_date: null,
  corrupt_field_count: 0,
};
const PAROLALI = {
  ...PAROLASIZ,
  password_set: true,
  recovery_key_confirmed: true,
  account_count: 1,
  recovery_key_no: 3,
  recovery_key_date: "2026-10-31",
};

/** Açık oturumun kişisiz özeti (kişi adı yok; tanıtıcı uydurma). */
const ACIK_OTURUM = {
  durum: "acik",
  hesap: {
    id: "h1",
    tanitici: "yonetici",
    rol: "yonetici",
    rol_etiketi: "Program yöneticisi",
    yetenekler: [],
  },
  bosta_dk: 10,
  bosta_kalan_sn: 600,
  kilit_bekliyor: false,
  kurulum_tamam: true,
  yukleme_siniri_mb: 20,
};
/** Anahtarı doğrulanmamış kurulum (yenilenmiş ve henüz doğrulanmamış anahtar). */
const DOGRULANMAMIS = { ...PAROLALI, recovery_key_confirmed: false };
const YENI_ANAHTAR = "YENI-ANAH-TARD-EFGH-JKLM-NOPQ-RSTU-VWXY";

/** "Kurtarma Anahtarını Doğrula" kartının formu (PDF kartıyla aynı etiketi taşır). */
function dogrulamaFormu(): HTMLElement {
  const dugme = screen.getByRole("button", { name: "Doğrula" });
  const form = dugme.closest("form");
  if (form === null) throw new Error("Doğrulama formu bulunamadı.");
  return form;
}

/** Varsayılan: program yöneticisinin bütün yetenekleri (süzme `oturum/yetki`'den gelir). */
function ekranaBas(yetenekler: readonly string[] = YETENEK_ADLARI) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <GuvenlikAyarlari />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

describe("GuvenlikAyarlari", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Gerçek `saveBlob` hep sonuç döndürür: sahte `undefined` dönseydi başarı dalı sınanmazdı.
    download.saveBlob.mockResolvedValue("kaydedildi");
    guvenlik.durum.mockResolvedValue(PAROLASIZ);
    oturum.ozet.mockResolvedValue(ACIK_OTURUM);
    oturum.bostaKilitSuresi.mockResolvedValue({ dakika: 10 });
    // Bekleyen anahtar modül belleğindedir: testler arasında sızmasın.
    bekleyenKurtarmaAnahtariniYaz(null);
    vi.spyOn(Math, "random").mockReturnValue(0.125); // sorulan gruplar: 1. ve 2.
  });

  it("hesapsız durumda dürüst kapsam metnini ve korunan alanları gösterir", async () => {
    ekranaBas();
    expect(await screen.findByText("Program yöneticisi hesabı kurulmadı.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hesap ve Parola" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Şifreleme" })).toBeInTheDocument();
    // Eski tek parola dili yoktur (tasarım TK9: herkes kendi hesabıyla).
    expect(document.body.textContent).not.toMatch(/yönetici parolası/i);
    expect(screen.getByText(/TAM DİSK ŞİFRELEME/)).toBeInTheDocument();
    expect(screen.getByText(/LUKS/)).toBeInTheDocument();
    expect(screen.getByText(/ad, soyad/)).toBeInTheDocument();
    // Okul numarası artık şifrelidir; şifrelenmeyen alanlar da açıkça söylenir.
    expect(screen.getByText(/öğrencilerin okul numaraları/)).toBeInTheDocument();
    expect(screen.getByText(/Sınıf\/şube, üye türü ve tarihler şifrelenmez/)).toBeInTheDocument();
    expect(screen.queryByText(/Okul numarası ve sınıf\/şube bilgisi şifrelenmez/)).toBeNull();
    // Fotoğraf ve sınav belgeleri bu programda yoktur; metin onlardan söz etmez.
    expect(screen.queryByText(/fotoğraf|oturma düzeni|Soru belgesi/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Öğrenci fotoğrafları" })).toBeNull();
  });

  it("hesap burada kurulmaz: yalnız kurulum sihirbazına bağlantı durur", async () => {
    ekranaBas();
    expect(await screen.findByText("Program yöneticisi hesabı kurulmadı.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /parolasını kur|hesabı kur/i })).toBeNull();
    expect(screen.getByRole("link", { name: /Kurulum Sihirbazı'nı aç/ })).toHaveAttribute(
      "href",
      "/kurulum",
    );
    // Hesapsızken belge kartı da, boşta kilit kartı da yoktur.
    expect(screen.queryByRole("heading", { name: "Kurtarma anahtarı belgesi" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Boşta Kilit Süresi" })).toBeNull();
    expect(oturum.bostaKilitSuresi).not.toHaveBeenCalled();
  });

  it("hesap kuruluyken değiştirme ve kilitleme sunar; kurma ve kaldırma YOKTUR", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    expect(await screen.findByText("Kişisel veri alanları şifreli.")).toBeInTheDocument();
    // Kart başlığı durumla DEĞİŞMEZ (docs/sozluk.md §4.6): yol tarifi hep aynı addır.
    expect(screen.getByRole("heading", { name: "Hesap ve Parola" })).toBeInTheDocument();
    // Oturumdaki hesap rol etiketi ve tanıtıcıyla yazılır; kişi adı yok (sözlük §5).
    expect(await screen.findByText("Program yöneticisi")).toBeInTheDocument();
    expect(screen.getByText("yonetici")).toBeInTheDocument();
    expect(oturum.ozet).toHaveBeenCalledWith(false);
    // Dürüst sınır: şifreli alanlar en zayıf hesap parolası kadar korunur (tasarım §4.4.6).
    expect(screen.getByText(/en zayıf hesap parolası kadar korunur/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Parolayı değiştir" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kilitle" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /kaldır/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /parolasını kur/i })).toBeNull();
  });

  it("kurtarma anahtarı belgesini elindeki anahtarla PDF olarak yeniden alır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    const pdf = new Blob(["%PDF-"], { type: "application/pdf" });
    guvenlik.kurtarmaAnahtariPdf.mockResolvedValue(pdf);
    ekranaBas();

    expect(
      await screen.findByRole("heading", { name: "Kurtarma anahtarı belgesi" }),
    ).toBeInTheDocument();
    // Güncel anahtarın kimliği kartta yazar (tasarım TK10).
    expect(screen.getByText(/Anahtar no 3 · üretim tarihi 31\.10\.2026/)).toBeInTheDocument();
    const alan = screen.getByLabelText(/^Kurtarma anahtarı/);
    await kullanici.type(alan, "AAAA-BBBB-CCCC-DDDD");
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    await waitFor(() =>
      expect(guvenlik.kurtarmaAnahtariPdf).toHaveBeenCalledWith("AAAA-BBBB-CCCC-DDDD"),
    );
    expect(download.saveBlob).toHaveBeenCalledWith(
      pdf,
      expect.stringMatching(/^Kurtarma-Anahtarı-Belgesi_\d{2}\.\d{2}\.\d{4}\.pdf$/),
      { evKlasorunde: true },
    );
    // Anahtar işi bitince alanda bekletilmez.
    await waitFor(() => expect(alan).toHaveValue(""));
    expect(
      await screen.findByText("Kurtarma anahtarı belgesi PDF olarak kaydedildi."),
    ).toBeInTheDocument();
  });

  it("köprü yoksa dosya tarayıcıya verilir: anahtar alanı boşalır, bildirim çıkar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariPdf.mockResolvedValue(new Blob(["%PDF-"]));
    download.saveBlob.mockResolvedValueOnce("indirildi");
    ekranaBas();

    const alan = await screen.findByLabelText(/^Kurtarma anahtarı/);
    await kullanici.type(alan, "AAAA-BBBB-CCCC-DDDD");
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    await waitFor(() => expect(alan).toHaveValue(""));
    expect(
      await screen.findByText("Kurtarma anahtarı belgesi PDF olarak kaydedildi."),
    ).toBeInTheDocument();
  });

  it("kaydetme penceresinde iptal sessizdir: anahtar alanı boşalmaz, bildirim çıkmaz", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariPdf.mockResolvedValue(new Blob(["%PDF-"]));
    download.saveBlob.mockResolvedValueOnce("iptal");
    ekranaBas();

    const alan = await screen.findByLabelText(/^Kurtarma anahtarı/);
    await kullanici.type(alan, "AAAA-BBBB-CCCC-DDDD");
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    await waitFor(() => expect(download.saveBlob).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "PDF olarak kaydet" })).toBeEnabled(),
    );
    expect(alan).toHaveValue("AAAA-BBBB-CCCC-DDDD");
    expect(
      screen.queryByText("Kurtarma anahtarı belgesi PDF olarak kaydedildi."),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(DOSYA_YAZILAMADI_ILETISI)).not.toBeInTheDocument();
  });

  it("dosya yazılamazsa tek ileti çıkar, anahtar alanı boşalmaz", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariPdf.mockResolvedValue(new Blob(["%PDF-"]));
    download.saveBlob.mockResolvedValueOnce("hata");
    ekranaBas();

    const alan = await screen.findByLabelText(/^Kurtarma anahtarı/);
    await kullanici.type(alan, "AAAA-BBBB-CCCC-DDDD");
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    expect(await screen.findByText(DOSYA_YAZILAMADI_ILETISI)).toBeInTheDocument();
    expect(alan).toHaveValue("AAAA-BBBB-CCCC-DDDD");
    expect(
      screen.queryByText("Kurtarma anahtarı belgesi PDF olarak kaydedildi."),
    ).not.toBeInTheDocument();
  });

  it("yanlış anahtarda backend iletisini gösterir, dosya inmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariPdf.mockRejectedValue(
      new ApiError(400, "validation_error", "Kurtarma anahtarı hatalı.", {}),
    );
    ekranaBas();

    await kullanici.type(await screen.findByLabelText(/^Kurtarma anahtarı/), "YANLIS");
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    expect(await screen.findByText("Kurtarma anahtarı hatalı.")).toBeInTheDocument();
    expect(download.saveBlob).not.toHaveBeenCalled();
  });

  it("anahtar doğrulanmamışsa uyarı ve doğrulama kartı çıkar; doğrulanınca kalkar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(DOGRULANMAMIS);
    guvenlik.kurtarmaAnahtariniDogrula.mockResolvedValue(PAROLALI);
    ekranaBas();

    expect(await screen.findByText(/Kurtarma anahtarı doğrulanmadı/)).toBeInTheDocument();
    const form = dogrulamaFormu();
    await kullanici.type(within(form).getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.click(within(form).getByRole("button", { name: "Doğrula" }));

    await waitFor(() =>
      expect(guvenlik.kurtarmaAnahtariniDogrula).toHaveBeenCalledWith("AAAA-BBBB"),
    );
    expect(
      await screen.findByText("Kurtarma anahtarının saklandığı doğrulandı."),
    ).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText(/Kurtarma anahtarı doğrulanmadı/)).toBeNull());
  });

  it("yanlış anahtarda doğrulama kartı backend iletisini gösterir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(DOGRULANMAMIS);
    guvenlik.kurtarmaAnahtariniDogrula.mockRejectedValue(
      new ApiError(400, "validation_error", "Kurtarma anahtarı hatalı.", {}),
    );
    ekranaBas();

    await screen.findByRole("heading", { name: "Kurtarma Anahtarını Doğrula" });
    const form = dogrulamaFormu();
    await kullanici.type(within(form).getByLabelText(/^Kurtarma anahtarı/), "YANLIS");
    await kullanici.click(within(form).getByRole("button", { name: "Doğrula" }));

    expect(await screen.findByText("Kurtarma anahtarı hatalı.")).toBeInTheDocument();
    expect(screen.getByText(/Kurtarma anahtarı doğrulanmadı/)).toBeInTheDocument();
  });

  it("kurtarma anahtarını yeniler: parola ister, yeni anahtarı bir kez gösterir, doğrulatır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariniYenile.mockResolvedValue({
      ...DOGRULANMAMIS,
      recovery_key: YENI_ANAHTAR,
      recovery_key_no: 4,
      recovery_key_date: "2026-11-01",
    });
    guvenlik.kurtarmaAnahtariniDogrula.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(
      await screen.findByRole("button", { name: "Kurtarma anahtarını yenile" }),
    );
    const diyalog = await screen.findByRole("dialog", { name: "Kurtarma anahtarı yenilensin mi?" });
    // Dürüst metinler: eski yedekler ve ele geçmiş anahtar.
    expect(within(diyalog).getByText(/Bugünden önce alınmış yedekler/)).toBeInTheDocument();
    expect(
      within(diyalog).getByText(/eline geçmiş bir anahtara karşı koruma değildir/),
    ).toBeInTheDocument();
    // Oturumdaki hesabın KENDİ parolası (plan F1b-1; başka hesabın parolası geçmez).
    await kullanici.type(within(diyalog).getByLabelText(/^Parolanız/), "Deneme-Parola-1");
    await kullanici.click(within(diyalog).getByRole("button", { name: "Yeni anahtar üret" }));

    await waitFor(() =>
      expect(guvenlik.kurtarmaAnahtariniYenile).toHaveBeenCalledWith("Deneme-Parola-1"),
    );
    expect(await screen.findByTestId("kurtarma-anahtari")).toHaveTextContent(YENI_ANAHTAR);
    // Yeni anahtarın no'su ve üretim tarihi anahtarın üstündedir.
    expect(screen.getByTestId("kurtarma-kimligi")).toHaveTextContent(
      "Anahtar no 4 · üretim tarihi 01.11.2026",
    );
    expect(
      await screen.findByText("Yeni kurtarma anahtarı üretildi. Saklayıp doğrulayın."),
    ).toBeInTheDocument();

    // Yeni anahtar da saklanıp doğrulanır (iki grup → sunucu damgası).
    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
    const gruplar = YENI_ANAHTAR.split("-");
    await kullanici.type(screen.getByLabelText("1. grup"), gruplar[0]);
    await kullanici.type(screen.getByLabelText("2. grup"), gruplar[1]);

    await waitFor(() =>
      expect(guvenlik.kurtarmaAnahtariniDogrula).toHaveBeenCalledWith(YENI_ANAHTAR),
    );
    // Doğrulanınca anahtar bellekten bırakılır (panel kalkar) ve durum yeniden okunur.
    await waitFor(() => expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull());
    expect(guvenlik.durum.mock.calls.length).toBeGreaterThan(1);
  });

  it("yenilemede yanlış parola: ileti gösterilir, yeni anahtar gösterilmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    guvenlik.kurtarmaAnahtariniYenile.mockRejectedValue(
      new ApiError(400, "validation_error", "Parola hatalı.", {}),
    );
    ekranaBas();

    await kullanici.click(
      await screen.findByRole("button", { name: "Kurtarma anahtarını yenile" }),
    );
    const diyalog = await screen.findByRole("dialog");
    await kullanici.type(within(diyalog).getByLabelText(/^Parolanız/), "yanlis");
    await kullanici.click(within(diyalog).getByRole("button", { name: "Yeni anahtar üret" }));

    expect(await within(diyalog).findByText("Parola hatalı.")).toBeInTheDocument();
    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
  });

  it("Kilitle oturumu kilitler ve pencereyi yeniden yükler", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.kilitle.mockResolvedValue({ sonuc: "kilitlendi", durum: "kilitli" });
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Kilitle" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.kilitle).toHaveBeenCalledTimes(1);
  });

  it("hesapsızken yenileme ve doğrulama kartları yoktur", async () => {
    ekranaBas();
    expect(await screen.findByText("Program yöneticisi hesabı kurulmadı.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kurtarma Anahtarını Yenile" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Kurtarma Anahtarını Doğrula" })).toBeNull();
  });

  it("parolayı değiştirir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.parolaDegistir.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Yeni-Parola-22");
    await kullanici.type(screen.getByLabelText(/tekrar/), "Yeni-Parola-22");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    await waitFor(() =>
      expect(oturum.parolaDegistir).toHaveBeenCalledWith("Deneme-Parola-1", "Yeni-Parola-22"),
    );
    // Hesap dilinde snackbar (sözlük §3): tek bir "yönetici parolası" yoktur.
    expect(await screen.findByText("Parolanız değiştirildi.")).toBeInTheDocument();
    // Parola değişimi pencereyi yeniden yüklemez (tasarım §13 D53; oturum ve veri aynı).
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  // Parola pencereleri açılınca parola alanı odaktadır (`ui/Dialog` `initialFocusRef`).
  it("parola değiştirme penceresi açılınca “Mevcut parola” alanı odaktadır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));

    expect(screen.getByLabelText(/Mevcut parola/)).toHaveFocus();
  });

  it("kurtarma anahtarı yenileme penceresi açılınca parola alanı odaktadır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(
      await screen.findByRole("button", { name: "Kurtarma anahtarını yenile" }),
    );
    const diyalog = await screen.findByRole("dialog", { name: "Kurtarma anahtarı yenilensin mi?" });

    expect(within(diyalog).getByLabelText(/^Parolanız/)).toHaveFocus();
  });

  it("eşleşmeyen yeni parola tekrarında istek atmaz", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Yeni-Parola-22");
    await kullanici.type(screen.getByLabelText(/tekrar/), "baska-bir-sey");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    expect(await screen.findByText("Parolalar eşleşmedi.")).toBeInTheDocument();
    expect(oturum.parolaDegistir).not.toHaveBeenCalled();
  });

  it("yanlış mevcut parola: ileti Mevcut parola alanının altında, alan boşalır ve odaklanır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    let reddet: (hata: unknown) => void = () => undefined;
    oturum.parolaDegistir.mockReturnValue(
      new Promise((_, ret) => {
        reddet = ret;
      }),
    );
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "yanlis");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Yeni-Parola-22");
    await kullanici.type(screen.getByLabelText(/tekrar/), "Yeni-Parola-22");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    // Backend gecikmesi sürerken bütün alanlar kapalı, pencere bekleme durumunu söyler.
    const diyalog = screen.getByRole("dialog", { name: "Parolayı değiştir" });
    expect(await within(diyalog).findByRole("status")).toHaveTextContent("Denetleniyor…");
    expect(screen.getByLabelText(/Mevcut parola/)).toBeDisabled();
    reddet(new ApiError(400, "parola_yanlis", "Parola hatalı."));

    const mevcut = screen.getByLabelText(/Mevcut parola/);
    await waitFor(() => expect(mevcut).toHaveAccessibleDescription("Parola hatalı."));
    expect(mevcut).toHaveAttribute("aria-invalid", "true");
    expect(mevcut).toHaveValue("");
    await waitFor(() => expect(mevcut).toHaveFocus());
    // Yeni parola alanları işaretlenmez, yazılanlar korunur.
    expect(screen.getByLabelText(/tekrar/)).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText(/^Yeni parola/)).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveValue("Yeni-Parola-22");
  });

  it("sunucu yeni parolayı reddederse ileti Yeni parola alanının altındadır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.parolaDegistir.mockRejectedValue(
      new ApiError(400, "validation_error", "Yeni parola eskisiyle aynı olamaz."),
    );
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Yeni-Parola-22");
    await kullanici.type(screen.getByLabelText(/tekrar/), "Yeni-Parola-22");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    const yeni = screen.getByLabelText(/^Yeni parola/);
    await waitFor(() => expect(yeni).toHaveAttribute("aria-invalid", "true"));
    expect(yeni).toHaveAccessibleDescription(/^Yeni parola eskisiyle aynı olamaz\./);
    expect(screen.getByLabelText(/Mevcut parola/)).not.toHaveAttribute("aria-invalid");
    await waitFor(() => expect(yeni).toHaveFocus());
  });

  it("alana bağlı olmayan ret pencerenin genel uyarısıdır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.parolaDegistir.mockRejectedValue(new TypeError("Failed to fetch"));
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Yeni-Parola-22");
    await kullanici.type(screen.getByLabelText(/tekrar/), "Yeni-Parola-22");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    const diyalog = screen.getByRole("dialog", { name: "Parolayı değiştir" });
    expect(await within(diyalog).findByRole("alert")).toHaveTextContent("Parola değiştirilemedi.");
    expect(screen.getByLabelText(/Mevcut parola/)).not.toHaveAttribute("aria-invalid");
    expect(screen.getByLabelText(/^Yeni parola/)).not.toHaveAttribute("aria-invalid");
  });

  // --- Kendi parolası: politika ön denetimi (tasarım TK15; plan F1b-1) -------------

  it("yeni parola politikaya uymazsa istek atmaz; eksik türleri sunucunun diliyle söyler", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    const diyalog = await screen.findByRole("dialog", { name: "Parolayı değiştir" });
    // Paylaşılan alanlar: güç göstergesi ve kural metni (kilit ekranındakiyle aynı).
    expect(within(diyalog).getByRole("meter", { name: "Parola gücü" })).toBeInTheDocument();
    expect(within(diyalog).getByText(/küçük harf, büyük harf, rakam ve simge/)).toBeInTheDocument();

    await kullanici.type(within(diyalog).getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(within(diyalog).getByLabelText(/^Yeni parola/), "kucukharf1");
    await kullanici.type(within(diyalog).getByLabelText(/tekrar/), "kucukharf1");
    await kullanici.click(within(diyalog).getByRole("button", { name: "Uygula" }));

    expect(
      await within(diyalog).findByText(
        "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: büyük harf, simge.",
      ),
    ).toBeInTheDocument();
    // Politika iletisi Yeni parola alanının hatasıdır (tekrar alanının değil); kural metni
    // de o alana bağlıdır.
    const yeni = within(diyalog).getByLabelText(/^Yeni parola/);
    expect(yeni).toHaveAttribute("aria-invalid", "true");
    expect(yeni).toHaveAccessibleDescription(/eksik: büyük harf, simge\..*En az 8 karakter/);
    expect(within(diyalog).getByLabelText(/tekrar/)).not.toHaveAttribute("aria-invalid");
    await waitFor(() => expect(yeni).toHaveFocus());
    expect(oturum.parolaDegistir).not.toHaveBeenCalled();
  });

  it("yeni parola eskisiyle aynı olamaz (istek atılmaz)", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Deneme-Parola-1");
    await kullanici.type(screen.getByLabelText(/tekrar/), "Deneme-Parola-1");
    await kullanici.click(screen.getByRole("button", { name: "Uygula" }));

    expect(await screen.findByText("Yeni parola eskisiyle aynı olamaz.")).toBeInTheDocument();
    expect(oturum.parolaDegistir).not.toHaveBeenCalled();
  });

  it("alanlar dolmadan Uygula kapalıdır; Vazgeç pencereyi kapatır ve alanları boşaltır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await kullanici.click(await screen.findByRole("button", { name: "Parolayı değiştir" }));
    expect(screen.getByRole("button", { name: "Uygula" })).toBeDisabled();
    await kullanici.type(screen.getByLabelText(/Mevcut parola/), "Deneme-Parola-1");
    await kullanici.click(screen.getByRole("button", { name: "Vazgeç" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    await kullanici.click(screen.getByRole("button", { name: "Parolayı değiştir" }));
    expect(screen.getByLabelText(/Mevcut parola/)).toHaveValue("");
  });

  it("oturum özeti okunamazsa hesap satırı yazılmaz, kart yine çalışır", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.ozet.mockRejectedValue(new ApiError(500, "error", "Sunucu hatası."));
    ekranaBas();

    expect(await screen.findByRole("button", { name: "Parolayı değiştir" })).toBeInTheDocument();
    expect(screen.queryByText(/Bu oturum:/)).toBeNull();
  });

  it("kilitli özet gelirse (yarış) hesap satırı yazılmaz", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.ozet.mockResolvedValue({ ...ACIK_OTURUM, durum: "kilitli", hesap: null });
    ekranaBas();

    expect(await screen.findByRole("button", { name: "Parolayı değiştir" })).toBeInTheDocument();
    await waitFor(() => expect(oturum.ozet).toHaveBeenCalled());
    expect(screen.queryByText(/Bu oturum:/)).toBeNull();
  });

  // --- Boşta kilit süresi (tasarım TK14, D11; uç security/idle-lock/) ----------------

  it("boşta kilit süresini okur ve kaydeder; oturum göstergesi hemen tazelenir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.bostaKilitSuresiniYaz.mockResolvedValue({ dakika: 15 });
    const dinleyici = vi.fn();
    window.addEventListener(OTURUM_DEGISTI_OLAYI, dinleyici);
    try {
      ekranaBas();

      expect(
        await screen.findByRole("heading", { name: "Boşta Kilit Süresi" }),
      ).toBeInTheDocument();
      const alan = await screen.findByLabelText(/^Boşta kilit süresi \(dakika\)/);
      expect(alan).toHaveValue(10);
      // Değişiklik yokken Kaydet kapalıdır.
      expect(screen.getByRole("button", { name: "Kaydet" })).toBeDisabled();
      expect(screen.getByText(/varsayılanı 10 dakikadır/)).toBeInTheDocument();

      await kullanici.clear(alan);
      await kullanici.type(alan, "15");
      await kullanici.click(screen.getByRole("button", { name: "Kaydet" }));

      await waitFor(() => expect(oturum.bostaKilitSuresiniYaz).toHaveBeenCalledWith(15));
      expect(
        await screen.findByText("Boşta kilit süresi 15 dakika olarak kaydedildi."),
      ).toBeInTheDocument();
      expect(dinleyici).toHaveBeenCalledTimes(1);
      // Süre değişimi pencereyi yeniden yüklemez (tasarım §13 D53).
      expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener(OTURUM_DEGISTI_OLAYI, dinleyici);
    }
  });

  it.each([
    ["2", "Boşta kilit süresi 3 ile 30 dakika arasında olmalıdır."],
    ["31", "Boşta kilit süresi 3 ile 30 dakika arasında olmalıdır."],
    ["", "Boşta kilit süresini dakika olarak girin."],
    ["7.5", "Boşta kilit süresi tam sayı (dakika) olmalıdır."],
  ])("aralık dışı, kesirli ya da boş süre (%s) istek atmadan reddedilir", async (deger, ileti) => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    const alan = await screen.findByLabelText(/^Boşta kilit süresi \(dakika\)/);
    await kullanici.clear(alan);
    if (deger) await kullanici.type(alan, deger);
    await kullanici.click(screen.getByRole("button", { name: "Kaydet" }));

    expect(await screen.findByText(ileti)).toBeInTheDocument();
    expect(oturum.bostaKilitSuresiniYaz).not.toHaveBeenCalled();
  });

  it("tam sayı ön denetimi backend'in (DRF IntegerField) kuralıyla aynıdır", () => {
    // Sondaki ".0" backend'de 15 olarak kabul edilir; ön yüz ondan katı olmaz.
    expect(bostaDakikaSorunu("15.0")).toBeNull();
    expect(bostaDakikaSorunu("15.")).toBeNull();
    expect(bostaDakikaSorunu(" 15 ")).toBeNull();
    for (const deger of ["7.5", "on", "1e1", "15.01"]) {
      expect(bostaDakikaSorunu(deger)).toBe(BOSTA_DK_TAM_SAYI_ILETISI);
    }
  });

  it("sunucu reddi iletisiyle gösterilir; süre okunamazsa kart bunu söyler", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(PAROLALI);
    oturum.bostaKilitSuresiniYaz.mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Boşta kilit süresi yalnız açık oturumda değiştirilir.",
      ),
    );
    const { unmount } = ekranaBas();

    const alan = await screen.findByLabelText(/^Boşta kilit süresi \(dakika\)/);
    await kullanici.clear(alan);
    await kullanici.type(alan, "20");
    await kullanici.click(screen.getByRole("button", { name: "Kaydet" }));
    expect(
      await screen.findByText("Boşta kilit süresi yalnız açık oturumda değiştirilir."),
    ).toBeInTheDocument();
    unmount();

    oturum.bostaKilitSuresi.mockRejectedValue(new ApiError(423, "locked", "Kayıtlar kilitli."));
    ekranaBas();
    expect(await screen.findByText("Boşta kilit süresi okunamadı.")).toBeInTheDocument();
  });
});

describe("GuvenlikAyarlari — rol süzmesi (plan F1b-2 'Ayarlar ve bant')", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    oturum.ozet.mockResolvedValue(ACIK_OTURUM);
    oturum.bostaKilitSuresi.mockResolvedValue({ dakika: 12 });
    bekleyenKurtarmaAnahtariniYaz(null);
  });

  /** Sayfadaki h2 başlıkları (kart adları; sözlük §4.6). */
  function kartlar(): string[] {
    return screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent ?? "");
  }

  it("program yöneticisi olmayan rolde kurtarma ve yedek kartları çizilmez", async () => {
    guvenlik.durum.mockResolvedValue(DOGRULANMAMIS);
    // Başkanın yetenekleri: Güvenlik ve boşta süre yazımı yok.
    ekranaBas(["son_oturum_onay"]);

    expect(await screen.findByRole("heading", { name: "Hesap ve Parola" })).toBeInTheDocument();
    expect(await screen.findByText("Boşta kilit süresi 12 dakika.")).toBeInTheDocument();
    expect(kartlar()).toEqual(["Hesap ve Parola", "Boşta Kilit Süresi", "Şifreleme"]);
    // Doğrulanmamış anahtar uyarısı da kurtarma kartlarındandır.
    expect(screen.queryByText(/Kurtarma anahtarı doğrulanmadı/)).toBeNull();
    expect(screen.queryByText("ŞİFRELİ YEDEK KARTI")).toBeNull();
    expect(screen.queryByText("GERİ YÜKLEME KARTI")).toBeNull();
    expect(screen.queryByText("YEDEK RAPORU KARTI")).toBeNull();
    // Kendi parolası ve Kilitle her rolde (KENDI satırı).
    expect(screen.getByRole("button", { name: "Parolayı değiştir" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kilitle" })).toBeInTheDocument();
  });

  it("bekleyen yeni anahtar yeteneksiz rolde gösterilmez", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    bekleyenKurtarmaAnahtariniYaz(YENI_ANAHTAR);
    ekranaBas([]);

    await screen.findByRole("heading", { name: "Hesap ve Parola" });
    expect(screen.queryByRole("heading", { name: "Kurtarma Anahtarınız" })).toBeNull();
    expect(document.body.textContent).not.toContain("YENI-ANAH");
  });

  it("boşta kilit süresini her rol okur; alan ve Kaydet yalnız yazabilen rolde", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    const { unmount } = ekranaBas([]);

    expect(await screen.findByText("Boşta kilit süresi 12 dakika.")).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Boşta kilit süresi \(dakika\)/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Kaydet" })).toBeNull();
    unmount();

    ekranaBas(["bosta_sure_yazma"]);
    expect(await screen.findByLabelText(/^Boşta kilit süresi \(dakika\)/)).toHaveValue(12);
    expect(screen.getByRole("button", { name: "Kaydet" })).toBeInTheDocument();
  });

  it("hesap kurulmadan Yedek Raporu kartı çizilmez; öteki yedek kartları durur", async () => {
    guvenlik.durum.mockResolvedValue(PAROLASIZ);
    ekranaBas();

    expect(await screen.findByText("ŞİFRELİ YEDEK KARTI")).toBeInTheDocument();
    expect(screen.getByText("GERİ YÜKLEME KARTI")).toBeInTheDocument();
    expect(screen.queryByText("YEDEK RAPORU KARTI")).toBeNull();
  });

  it("program yöneticisinde kurtarma ve yedek kartlarının hepsi durur", async () => {
    guvenlik.durum.mockResolvedValue(PAROLALI);
    ekranaBas();

    await screen.findByRole("heading", { name: "Kurtarma Anahtarını Yenile" });
    expect(kartlar()).toEqual(
      expect.arrayContaining(["Kurtarma Anahtarını Yenile", "Kurtarma anahtarı belgesi"]),
    );
    expect(screen.getByText("ŞİFRELİ YEDEK KARTI")).toBeInTheDocument();
    expect(screen.getByText("GERİ YÜKLEME KARTI")).toBeInTheDocument();
    expect(screen.getByText("YEDEK RAPORU KARTI")).toBeInTheDocument();
  });
});
