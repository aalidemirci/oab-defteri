// Kilit ekranı testi (tasarım §4.4.3; plan F1b-1 "Oturum", "Parola ve hatalı deneme"):
// hesap listesi rol etiketi + tanıtıcıyla, kişi adı olmadan; askıdaki ve kaydı okunamayan
// satır seçilemez; tek hesap İLK yüklemede seçili gelir, askıdan sonra tazelenen listede
// başka hesap kendiliğinden seçilmez; başka hesap seçilince hata silinir; ret kodları
// kullanıcı metnine çıkmaz ve her ileti kendi alanına (Parola, Hesap grubu, Yeni parola,
// Parola (tekrar)) bağlıdır; odak her retten ve geri dönüşten sonra forma döner; 409
// `parola_yenilenmeli`de aynı ekranda yeni parola istenir (gerekçe alana bağlı, ret
// dalları dâhil); güç göstergesi yazılan yeni parolayı izler; "Parolamı unuttum" yalnız
// SEÇİLİ hesap program yöneticisiyken; liste boşken kurtarma yolu doğrudan açılır.
// Başarılı açılış pencereyi yeniden yükler (tasarım §13 D53).
// Oturum istemcisi vi.mock ile taklit edilir — ağ yok.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const oturum = vi.hoisted(() => ({
  hesaplar: vi.fn(),
  ac: vi.fn(),
  kurtar: vi.fn(),
  kurtarmaHesaplari: vi.fn(),
}));

vi.mock("../oturum/api", () => ({ oturumApi: oturum }));

import { ApiError } from "../../lib/api";
import { pencereIcerigi } from "../../lib/kilit";
import type { KilitEkraniHesabi } from "../oturum/api";
import KilitEkrani, {
  ASKIDA_ETIKETI,
  OKUNAMADI_ETIKETI,
  UNUTTUM_BASKA_ROL_METNI,
} from "./KilitEkrani";

const YONETICI: KilitEkraniHesabi = {
  id: "aaaaaaaa-0000-4000-8000-000000000001",
  tanitici: "yonetici",
  rol: "yonetici",
  rol_etiketi: "Program yöneticisi",
  secilebilir: true,
  askida_nedeni: null,
};
const MUHASIP: KilitEkraniHesabi = {
  id: "aaaaaaaa-0000-4000-8000-000000000002",
  tanitici: "muhasip",
  rol: "muhasip",
  rol_etiketi: "Muhasip",
  secilebilir: true,
  askida_nedeni: null,
};
const DK_ASKIDA: KilitEkraniHesabi = {
  id: "aaaaaaaa-0000-4000-8000-000000000003",
  tanitici: "dk-1",
  rol: "denetleme_kurulu",
  rol_etiketi: "Denetleme Kurulu 1",
  secilebilir: false,
  askida_nedeni: "HATALI_DENEME",
};
const DK_UYELIK: KilitEkraniHesabi = {
  id: "aaaaaaaa-0000-4000-8000-000000000004",
  tanitici: "dk-2",
  rol: "denetleme_kurulu",
  rol_etiketi: "Denetleme Kurulu 2",
  secilebilir: false,
  askida_nedeni: "UYELIK_DUSTU",
};
const OKUNAMAYAN: KilitEkraniHesabi = {
  id: "aaaaaaaa-0000-4000-8000-000000000005",
  tanitici: "sekreter",
  rol: null,
  rol_etiketi: "Hesap kaydı okunamadı",
  secilebilir: false,
  askida_nedeni: null,
};

const GECERLI_PAROLA = "Yeni-Parola-22";

function radyo(ad: RegExp | string) {
  return screen.getByRole("radio", { name: ad });
}

async function hazir() {
  await screen.findByRole("group", { name: "Hesap" });
}

beforeEach(() => {
  vi.clearAllMocks();
  oturum.hesaplar.mockResolvedValue([YONETICI]);
});

describe("KilitEkrani — hesap listesi", () => {
  it("satır rol etiketi ve tanıtıcıdır; tek hesap seçili gelir ve parola alanı odaktadır", async () => {
    render(<KilitEkrani />);
    await hazir();

    const satir = radyo("Program yöneticisi (yonetici)");
    expect(satir).toBeChecked();
    expect(screen.getByText("Program yöneticisi")).toBeInTheDocument();
    expect(screen.getByText("yonetici")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
    expect(oturum.hesaplar).toHaveBeenCalledTimes(1);
  });

  it("askıdaki (iki kaynak) ve kaydı okunamayan satır seçilemez, nedeni okunur", async () => {
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP, DK_ASKIDA, DK_UYELIK, OKUNAMAYAN]);
    render(<KilitEkrani />);
    await hazir();

    for (const ad of ["Denetleme Kurulu 1 (dk-1)", "Denetleme Kurulu 2 (dk-2)"]) {
      expect(radyo(ad)).toBeDisabled();
      expect(radyo(ad)).toHaveAccessibleDescription(ASKIDA_ETIKETI);
    }
    expect(radyo(`${OKUNAMADI_ETIKETI} (sekreter)`)).toBeDisabled();
    // İç askı nedenleri ekrana çıkmaz.
    expect(screen.queryByText(/HATALI_DENEME|UYELIK_DUSTU/)).toBeNull();
    // Birden çok seçilebilir hesap: hiçbiri kendiliğinden seçili gelmez; odak (sayfa
    // gövdesine düşmesin) ilk seçilebilir satırdadır.
    expect(radyo("Program yöneticisi (yonetici)")).not.toBeChecked();
    expect(radyo("Muhasip (muhasip)")).not.toBeChecked();
    await waitFor(() => expect(radyo("Program yöneticisi (yonetici)")).toHaveFocus());
  });

  it("hesap seçilmeden gönderilirse hesap grubunun altında sorar, istek atmaz", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1");
    await kullanici.click(screen.getByRole("button", { name: "Aç" }));

    expect(await screen.findByText("Hesabınızı seçin.")).toBeInTheDocument();
    // İleti Parola alanının değil hesap grubunun hatasıdır; odak ilk satıra döner.
    expect(screen.getByRole("group", { name: "Hesap" })).toHaveAccessibleDescription(
      "Hesabınızı seçin.",
    );
    expect(screen.getByLabelText(/^Parola/)).not.toHaveAttribute("aria-invalid");
    await waitFor(() => expect(radyo("Program yöneticisi (yonetici)")).toHaveFocus());
    expect(oturum.ac).not.toHaveBeenCalled();
  });

  it("seçilen hesabın parolasıyla açar ve pencereyi yeniden yükler", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    oturum.ac.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(radyo("Muhasip (muhasip)"));
    await kullanici.type(screen.getByLabelText(/^Parola/), "Muhasip-Parola-1{Enter}");

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.ac).toHaveBeenCalledWith({ hesap: MUHASIP.id, parola: "Muhasip-Parola-1" });
  });

  it("satırda Enter parola boşsa parola alanına geçer, doluysa gönderir", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    oturum.ac.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();

    radyo("Muhasip (muhasip)").focus();
    await kullanici.keyboard(" ");
    expect(radyo("Muhasip (muhasip)")).toBeChecked();
    await kullanici.keyboard("{Enter}");
    expect(screen.getByLabelText(/^Parola/)).toHaveFocus();
    expect(oturum.ac).not.toHaveBeenCalled();

    await kullanici.keyboard("Muhasip-Parola-1");
    radyo("Muhasip (muhasip)").focus();
    await kullanici.keyboard("{Enter}");
    await waitFor(() => expect(oturum.ac).toHaveBeenCalledTimes(1));
  });

  it("liste okunamazsa iletiyi ve Yeniden dene'yi gösterir", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<KilitEkrani />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Hesap listesi okunamadı.");
    await kullanici.click(screen.getByRole("button", { name: "Yeniden dene" }));
    await hazir();
    expect(oturum.hesaplar).toHaveBeenCalledTimes(2);
  });

  it("korumanın tam disk şifreleme OLMADIĞINI açıkça yazar", async () => {
    render(<KilitEkrani />);
    await hazir();
    expect(screen.getByText(/TAM DİSK ŞİFRELEME/)).toBeInTheDocument();
    expect(screen.getByText(/BitLocker/)).toBeInTheDocument();
    expect(screen.getByText(/kendi parolasıyla/)).toBeInTheDocument();
  });
});

describe("KilitEkrani — retler", () => {
  it("yanlış parolada iletiyi gösterir, kodu göstermez, alanı boşaltır ve yüklemez", async () => {
    const kullanici = userEvent.setup();
    oturum.ac.mockRejectedValue(new ApiError(400, "parola_yanlis", "Parola hatalı."));
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis-parola{Enter}");

    expect(await screen.findByRole("alert")).toHaveTextContent("Parola hatalı.");
    expect(screen.queryByText(/parola_yanlis/)).toBeNull();
    expect(screen.getByLabelText(/^Parola/)).toHaveValue("");
    expect(screen.getByLabelText(/^Parola/)).toHaveAttribute("aria-invalid", "true");
    await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("başka hesap seçilince önceki hata silinir", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    oturum.ac.mockRejectedValue(new ApiError(400, "parola_yanlis", "Parola hatalı."));
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(radyo("Muhasip (muhasip)"));
    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis{Enter}");
    expect(await screen.findByText("Parola hatalı.")).toBeInTheDocument();

    await kullanici.click(radyo("Program yöneticisi (yonetici)"));
    expect(screen.queryByText("Parola hatalı.")).toBeNull();
  });

  it("onuncu hatada hesap askıya alınır: ileti gösterilir, liste tazelenir, satır seçilemez, başka hesap kendiliğinden seçilmez", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar
      .mockResolvedValueOnce([YONETICI, MUHASIP])
      .mockResolvedValueOnce([
        YONETICI,
        { ...MUHASIP, secilebilir: false, askida_nedeni: "HATALI_DENEME" },
      ]);
    oturum.ac.mockRejectedValue(
      new ApiError(
        403,
        "hesap_askida",
        "Parola hatalı. Art arda yanlış parola girildiği için hesap askıya alındı — program " +
          "yöneticisine başvurun.",
      ),
    );
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(radyo("Muhasip (muhasip)"));
    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis{Enter}");

    expect(await screen.findByText(/hesap askıya alındı/)).toBeInTheDocument();
    await waitFor(() => expect(radyo("Muhasip (muhasip)")).toBeDisabled());
    expect(oturum.hesaplar).toHaveBeenCalledTimes(2);
    expect(radyo("Muhasip (muhasip)")).toHaveAccessibleDescription(ASKIDA_ETIKETI);
    // Geriye tek seçilebilir hesap kaldı ama o SEÇİLMEZ: seçilseydi askıya alınan kişinin
    // yazacağı parola program yöneticisi hesabına hatalı deneme diye sayılırdı.
    expect(radyo("Program yöneticisi (yonetici)")).not.toBeChecked();
    expect(screen.queryByRole("button", { name: "Parolamı unuttum" })).toBeNull();
    expect(screen.queryByText(UNUTTUM_BASKA_ROL_METNI)).toBeNull();
    // Askı iletisi Parola alanının değil hesap grubunun altındadır; odak ilk seçilebilir satırda.
    expect(screen.getByRole("group", { name: "Hesap" })).toHaveAccessibleDescription(
      /hesap askıya alındı/,
    );
    expect(screen.getByLabelText(/^Parola/)).not.toHaveAttribute("aria-invalid");
    await waitFor(() => expect(radyo("Program yöneticisi (yonetici)")).toHaveFocus());

    // Gönderilirse istek gitmez, hesap sorulur (askıya alınan hesabın parolası başka hesaba gitmez).
    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis{Enter}");
    expect(await screen.findByText("Hesabınızı seçin.")).toBeInTheDocument();
    expect(oturum.ac).toHaveBeenCalledTimes(1);
  });

  it("tek hesaplı listede askıdan sonra seçilebilir hesap kalmaz; ileti görünür", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar
      .mockResolvedValueOnce([MUHASIP])
      .mockResolvedValueOnce([{ ...MUHASIP, secilebilir: false, askida_nedeni: "HATALI_DENEME" }]);
    oturum.ac.mockRejectedValue(new ApiError(403, "hesap_askida", ""));
    render(<KilitEkrani />);
    await hazir();
    expect(radyo("Muhasip (muhasip)")).toBeChecked();

    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis{Enter}");

    await waitFor(() => expect(radyo("Muhasip (muhasip)")).toBeDisabled());
    expect(radyo("Muhasip (muhasip)")).not.toBeChecked();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Hesap askıda — program yöneticisine başvurun.",
    );
  });

  it.each([
    [409, "hesap_muhru_tutmadi", /program dışından değiştirilmiş/],
    [409, "iki_depo_tutarsiz", /güvenlik dosyasıyla uyuşmuyor/],
  ])(
    "iletisiz %i %s eşlemdeki metinle gösterilir, kod ekrana çıkmaz",
    async (status, kod, metin) => {
      const kullanici = userEvent.setup();
      oturum.ac.mockRejectedValue(new ApiError(status, kod, ""));
      render(<KilitEkrani />);
      await hazir();

      await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

      expect(await screen.findByRole("alert")).toHaveTextContent(metin);
      expect(screen.queryByText(new RegExp(kod))).toBeNull();
      // Alana bağlı olmayan ret formun genel uyarısıdır: Parola alanı işaretlenmez.
      expect(screen.getByLabelText(/^Parola/)).not.toHaveAttribute("aria-invalid");
      await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
    },
  );

  it("backend gecikmesi sürerken bekleme durumu görünür ve form kapalıdır", async () => {
    const kullanici = userEvent.setup();
    let bitir: (deger: unknown) => void = () => undefined;
    oturum.ac.mockReturnValue(
      new Promise((resolve) => {
        bitir = resolve;
      }),
    );
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

    expect(await screen.findByRole("status")).toHaveTextContent("Denetleniyor…");
    expect(screen.getByRole("button", { name: "Açılıyor…" })).toBeDisabled();
    expect(screen.getByLabelText(/^Parola/)).toBeDisabled();
    bitir({ durum: "acik" });
    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
  });
});

describe("KilitEkrani — zorunlu parola yenileme (409 parola_yenilenmeli)", () => {
  async function yenilemeyeGec(kullanici: ReturnType<typeof userEvent.setup>) {
    oturum.ac.mockRejectedValueOnce(
      new ApiError(
        409,
        "parola_yenilenmeli",
        "Parolanızı yenilemeniz gerekiyor (geçici parola ya da süresi dolan parola). Yeni " +
          "parolanızı belirleyin.",
      ),
    );
    render(<KilitEkrani />);
    await hazir();
    await kullanici.type(screen.getByLabelText(/^Parola/), "Gecici-Parola-1{Enter}");
    await screen.findByLabelText(/^Yeni parola/);
  }

  it("oturum açılmadan aynı ekranda yeni parola + tekrar ister ve yeni parolayla açar", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);

    expect(screen.getByText(/Parolanızı yenilemeniz gerekiyor/)).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "Parola gücü" })).toBeInTheDocument();
    expect(screen.queryByText(/parola_yenilenmeli/)).toBeNull();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByLabelText(/^Yeni parola/)).toHaveFocus());
    // Gerekçe ve kural odaklanan alana bağlıdır: ekran okuyucu nedenini de okur.
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveAccessibleDescription(
      /Parolanızı yenilemeniz gerekiyor.*En az 8 karakter; küçük harf, büyük harf/,
    );

    oturum.ac.mockResolvedValueOnce({ durum: "acik" });
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.ac).toHaveBeenLastCalledWith({
      hesap: YONETICI.id,
      parola: "Gecici-Parola-1",
      yeni_parola: GECERLI_PAROLA,
    });
  });

  it.each([
    ["kisa1A!", "kisa1A!", "Parola en az 8 karakter olmalıdır."],
    ["yenisifre1", "yenisifre1", "eksik: büyük harf, simge."],
    [" Bosluk-1a", " Bosluk-1a", "Parolanın başında ya da sonunda boşluk olamaz."],
    ["Gecici-Parola-1", "Gecici-Parola-1", "Yeni parola eskisiyle aynı olamaz."],
    [GECERLI_PAROLA, "Baska-Parola-22", "Parolalar eşleşmedi."],
  ])("yeni parola “%s” önceden denetlenir, istek gitmez", async (yeni, tekrar, ileti) => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), yeni);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), tekrar);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(ileti);
    expect(oturum.ac).toHaveBeenCalledTimes(1);
  });

  it("politika iletisi Yeni parola'nın, eşleşmeme Parola (tekrar)'ın altındadır; odak hatalı alana gider", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "kisa1A!");
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), "kisa1A!");
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));
    expect(await screen.findByLabelText(/^Yeni parola/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText(/^Parola \(tekrar\)/)).not.toHaveAttribute("aria-invalid");
    await waitFor(() => expect(screen.getByLabelText(/^Yeni parola/)).toHaveFocus());

    await kullanici.clear(screen.getByLabelText(/^Yeni parola/));
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));
    await waitFor(() =>
      expect(screen.getByLabelText(/^Parola \(tekrar\)/)).toHaveAttribute("aria-invalid", "true"),
    );
    expect(screen.getByLabelText(/^Yeni parola/)).not.toHaveAttribute("aria-invalid");
    expect(screen.getByRole("alert")).toHaveTextContent("Parolalar eşleşmedi.");
    await waitFor(() => expect(screen.getByLabelText(/^Parola \(tekrar\)/)).toHaveFocus());
    expect(oturum.ac).toHaveBeenCalledTimes(1);
  });

  it("yenilemede “parola hatalı” (geçici parola bu arada değişti): parola adımına döner, alan boş ve odakta", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);
    oturum.ac.mockRejectedValueOnce(new ApiError(400, "parola_yanlis", "Parola hatalı."));

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Parola hatalı.");
    expect(screen.queryByLabelText(/^Yeni parola/)).toBeNull();
    expect(screen.getByLabelText(/^Parola/)).toHaveValue("");
    await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("sunucu yeni parolayı reddederse yenileme adımında kalınır, yazılanlar korunur", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);
    oturum.ac.mockRejectedValueOnce(
      new ApiError(400, "validation_error", "Yeni parola eskisiyle aynı olamaz."),
    );

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Yeni parola eskisiyle aynı olamaz.",
    );
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveValue(GECERLI_PAROLA);
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText(/^Parola \(tekrar\)/)).toHaveValue(GECERLI_PAROLA);
    await waitFor(() => expect(screen.getByLabelText(/^Yeni parola/)).toHaveFocus());
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    expect(oturum.ac).toHaveBeenCalledTimes(2);
  });

  it("güç göstergesi yazılan yeni parolayı izler ve düzeyini metinle söyler", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);
    const gosterge = screen.getByRole("meter", { name: "Parola gücü" });
    expect(gosterge).toHaveAttribute("aria-valuetext", "Boş");

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "zayif");
    expect(gosterge).toHaveAttribute("aria-valuetext", "Zayıf");
    expect(screen.getByText("Parola gücü: Zayıf.")).toBeInTheDocument();

    await kullanici.clear(screen.getByLabelText(/^Yeni parola/));
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "Deneme-Parola-1");
    expect(gosterge).toHaveAttribute("aria-valuetext", "İyi");
    expect(gosterge).toHaveAttribute("aria-valuenow", "3");
    expect(screen.getByText("Parola gücü: İyi.")).toBeInTheDocument();
    // Tekrar alanına yazılan göstergeyi değiştirmez.
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), "x");
    expect(gosterge).toHaveAttribute("aria-valuetext", "İyi");
  });

  it("Vazgeç parola adımına döner ve odak Parola alanına gelir", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);

    await kullanici.click(screen.getByRole("button", { name: "Vazgeç" }));

    expect(screen.getByLabelText(/^Parola/)).toHaveValue("");
    expect(screen.queryByLabelText(/^Yeni parola/)).toBeNull();
    await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
  });
});

describe("KilitEkrani — kurtarma anahtarı (yalnız program yöneticisi)", () => {
  it("program yöneticisi olmayan hesapta “Parolamı unuttum” yoktur, program yöneticisine yönlendirir", async () => {
    oturum.hesaplar.mockResolvedValue([MUHASIP]);
    render(<KilitEkrani />);
    await hazir();

    expect(screen.queryByRole("button", { name: "Parolamı unuttum" })).toBeNull();
    expect(
      screen.getByText("Parolanızı unuttuysanız program yöneticisine başvurun."),
    ).toBeInTheDocument();
  });

  it("“Parolamı unuttum” listeye değil SEÇİLİ hesaba bağlıdır", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    render(<KilitEkrani />);
    await hazir();

    // Seçim yokken ne düğme ne yönlendirme metni (listede program yöneticisi olsa da).
    expect(screen.queryByRole("button", { name: "Parolamı unuttum" })).toBeNull();
    expect(screen.queryByText(UNUTTUM_BASKA_ROL_METNI)).toBeNull();

    await kullanici.click(radyo("Muhasip (muhasip)"));
    expect(screen.queryByRole("button", { name: "Parolamı unuttum" })).toBeNull();
    expect(screen.getByText(UNUTTUM_BASKA_ROL_METNI)).toBeInTheDocument();

    await kullanici.click(radyo("Program yöneticisi (yonetici)"));
    expect(screen.getByRole("button", { name: "Parolamı unuttum" })).toBeInTheDocument();
    expect(screen.queryByText(UNUTTUM_BASKA_ROL_METNI)).toBeNull();
  });

  it("program yöneticisi kurtarma anahtarı + yeni parolayla açar ve pencere yeniden yüklenir", async () => {
    const kullanici = userEvent.setup();
    oturum.kurtar.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: "Parolamı unuttum" }));
    expect(screen.getByText(/okul müdürlüğünde kapalı zarfta/)).toBeInTheDocument();
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.kurtar).toHaveBeenCalledWith({
      kurtarma_anahtari: "AAAA-BBBB",
      hesap: YONETICI.id,
      yeni_parola: GECERLI_PAROLA,
    });
    expect(oturum.kurtarmaHesaplari).not.toHaveBeenCalled();
  });

  it("yanlış kurtarma anahtarında iletiyi gösterir; parolayla açmaya dönülebilir", async () => {
    const kullanici = userEvent.setup();
    oturum.kurtar.mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Kurtarma anahtarı hatalı. Yazdırdığınız kâğıttaki anahtarı olduğu gibi girin.",
      ),
    );
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: "Parolamı unuttum" }));
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "YANL-IS00");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Kurtarma anahtarı hatalı.");
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    // Alanlar istek sürerken kapalıydı: odak anahtar alanına geri verilir.
    await waitFor(() => expect(screen.getByLabelText(/^Kurtarma anahtarı/)).toHaveFocus());

    await kullanici.click(screen.getByRole("button", { name: "Parolayla açmaya dön" }));
    expect(screen.getByLabelText(/^Parola/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Kurtarma anahtarı/)).toBeNull();
    // Odak sayfa gövdesine düşmez: seçili hesabın Parola alanına gelir.
    await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
  });

  it("kurtarmada yeni parola politikaya uymazsa istek gitmez", async () => {
    const kullanici = userEvent.setup();
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: "Parolamı unuttum" }));
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), "zayif");
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), "zayif");
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Parola en az 8 karakter olmalıdır.",
    );
    // Politika iletisi Yeni parola alanının hatasıdır; odak oraya döner.
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveAttribute("aria-invalid", "true");
    await waitFor(() => expect(screen.getByLabelText(/^Yeni parola/)).toHaveFocus());
    expect(oturum.kurtar).not.toHaveBeenCalled();
  });

  it("liste boşken (kurtarmayla geri yükleme) kurtarma yolu doğrudan açılır, hesap kurtarma listesinden gelir", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([]);
    oturum.kurtarmaHesaplari.mockResolvedValue([
      {
        id: YONETICI.id,
        tanitici: "yonetici",
        rol_etiketi: "Program yöneticisi",
        sarmali_var: false,
      },
    ]);
    oturum.kurtar.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);

    expect(await screen.findByText(/güvenlik dosyasında hesap parolası yok/)).toBeInTheDocument();
    const form = screen.getByRole("form", { name: "Kurtarma yolu" });
    expect(
      await within(form).findByRole("radio", { name: "Program yöneticisi (yonetici)" }),
    ).toBeChecked();
    // Dönülecek parola yolu yoktur.
    expect(screen.queryByRole("button", { name: "Parolayla açmaya dön" })).toBeNull();

    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.kurtar).toHaveBeenCalledWith({
      kurtarma_anahtari: "AAAA-BBBB",
      hesap: YONETICI.id,
      yeni_parola: GECERLI_PAROLA,
    });
  });

  it("birden çok program yöneticisi varsa seçilmeden gönderilemez", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([]);
    oturum.kurtarmaHesaplari.mockResolvedValue([
      { id: "y-1", tanitici: "yonetici", rol_etiketi: "Program yöneticisi", sarmali_var: false },
      { id: "y-2", tanitici: "yonetici-2", rol_etiketi: "Program yöneticisi", sarmali_var: false },
    ]);
    render(<KilitEkrani />);
    await screen.findByRole("radio", { name: "Program yöneticisi (yonetici-2)" });

    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Program yöneticisi hesabını seçin.",
    );
    // İleti hesap grubuna bağlıdır; odak ilk satıra gider.
    const form = screen.getByRole("form", { name: "Kurtarma yolu" });
    expect(within(form).getByRole("group", { name: "Hesap" })).toHaveAccessibleDescription(
      "Program yöneticisi hesabını seçin.",
    );
    await waitFor(() =>
      expect(
        within(form).getByRole("radio", { name: "Program yöneticisi (yonetici)" }),
      ).toHaveFocus(),
    );
    expect(oturum.kurtar).not.toHaveBeenCalled();
  });

  it("kurtarma listesi de boşsa bunu söyler ve gönderilemez", async () => {
    oturum.hesaplar.mockResolvedValue([]);
    oturum.kurtarmaHesaplari.mockResolvedValue([]);
    render(<KilitEkrani />);

    expect(
      await screen.findByText(/kurtarma anahtarıyla açılabilecek bir program yöneticisi/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kurtar ve aç" })).toBeDisabled();
  });

  it("kurtarma listesi okunamazsa iletiyi gösterir", async () => {
    oturum.hesaplar.mockResolvedValue([]);
    oturum.kurtarmaHesaplari.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<KilitEkrani />);

    expect(await screen.findByText("Hesap listesi okunamadı.")).toBeInTheDocument();
  });
});
