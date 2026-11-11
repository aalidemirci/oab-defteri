// Kilit ekranı testi (tasarım §4.4.3; plan F1b-1 "Oturum", "Parola ve hatalı deneme"):
// hesap listesi rol etiketi + tanıtıcıyla, kişi adı olmadan; askıdaki ve kaydı okunamayan
// satır seçilemez; tek hesap İLK yüklemede seçili gelir, askıdan sonra tazelenen listede
// başka hesap kendiliğinden seçilmez; başka hesap seçilince hata silinir; ret kodları
// kullanıcı metnine çıkmaz ve her ileti kendi alanına (Parola, Hesap grubu, Yeni parola,
// Parola (tekrar)) bağlıdır; odak her retten ve geri dönüşten sonra forma döner; 409
// `parola_yenilenmeli`de aynı ekranda yeni parola istenir (gerekçe alana bağlı, ret
// dalları dâhil); güç göstergesi yazılan yeni parolayı izler; "Parolamı unuttum" yalnız
// SEÇİLİ hesap program yöneticisiyken; liste boşken kurtarma yolu doğrudan açılır; liste dolu
// ama seçilebilir satır kalmayınca yol gösterir ve "Kurtarma anahtarıyla aç"ı sunar (plan F1b-2
// "Kilit ekranı"; metin kullanıcı kararlarının: zarfın üçüncü durumu, çaresi, Denetleme Kurulu);
// sunucunun ret iletileri (hesap kaydı, denetim izi, parola kaydı) olduğu gibi yazılır; gönderim
// sürerken ve açılıştan sonra ikinci gönderim gitmez (aynı olay döngüsündeki iki gönderim de).
// Başarılı açılış pencereyi yeniden yükler (tasarım §13 D53).
// Oturum istemcisi vi.mock ile taklit edilir — ağ yok. Hesaplar ve parolalar uydurmadır.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  BOS_LISTE_METNI,
  KURTARMA_ILE_AC_ETIKETI,
  OKUNAMADI_ETIKETI,
  SECILEBILIR_HESAP_YOK_METNI,
  UNUTTUM_BASKA_ROL_METNI,
  UYELIK_ASKISI_METNI,
} from "./KilitEkrani";
import { KURTARILACAK_HESAP_YOK_METNI, UCUNCU_DURUM_YOL_METNI } from "./KurtarmaIleAcma";
import { UCUNCU_DURUMUN_CARESI, ZARFIN_UCUNCU_DURUMU } from "./metinler";

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

const YONETICI_ASKIDA: KilitEkraniHesabi = {
  ...YONETICI,
  secilebilir: false,
  askida_nedeni: "HATALI_DENEME",
};
const KURTARILACAK_YONETICI = {
  id: YONETICI.id,
  tanitici: "yonetici",
  rol_etiketi: "Program yöneticisi",
  sarmali_var: true,
};

const GECERLI_PAROLA = "Yeni-Parola-22";

/** Backend'in kilit ekranı iletileri (`app_password`: `_SEAL_MISMATCH_MESSAGE`,
 * `IZ_BOSLUGU_MESSAGE`, `UNBOUND_WRAP_MESSAGE` = `WRAP_DIGEST_MISMATCH_MESSAGE`; sözlük §1). */
const KAYIT_REDDI =
  "Hesap kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. Program " +
  "yöneticisine ve Denetleme Kuruluna bildirin.";
const IZ_BOSLUGU =
  "Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş " +
  "görünüyor; giriş açılmadı. Program yöneticisine ve Denetleme Kuruluna bildirin.";
const PAROLA_KAYDI =
  "Bu hesabın parola kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. " +
  "Denetleme Kuruluna bildirin. Program yöneticisinin hesabıysa “Parolamı unuttum” yolundan " +
  "kurtarma anahtarıyla açılır; öteki hesapların parolasını program yöneticisi sıfırlar.";

function radyo(ad: RegExp | string) {
  return screen.getByRole("radio", { name: ad });
}

function formu(alan: HTMLElement): HTMLFormElement {
  const form = alan.closest("form");
  if (form === null) throw new Error("form bulunamadı");
  return form;
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
    // Üyelik askısındaki hesap listede: nedenin iletisi listenin altında (F1c 11. adım).
    expect(screen.getByText(UYELIK_ASKISI_METNI)).toBeInTheDocument();
    // Birden çok seçilebilir hesap: hiçbiri kendiliğinden seçili gelmez; odak (sayfa
    // gövdesine düşmesin) ilk seçilebilir satırdadır.
    expect(radyo("Program yöneticisi (yonetici)")).not.toBeChecked();
    expect(radyo("Muhasip (muhasip)")).not.toBeChecked();
    await waitFor(() => expect(radyo("Program yöneticisi (yonetici)")).toHaveFocus());
    // Seçilebilir satır varken yol gösterme yoktur; parola yolu yerindedir.
    expect(screen.queryByRole("button", { name: KURTARMA_ILE_AC_ETIKETI })).toBeNull();
    expect(screen.queryByText(SECILEBILIR_HESAP_YOK_METNI)).toBeNull();
    expect(screen.getByRole("button", { name: "Aç" })).toBeInTheDocument();
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

  it("tek hesaplı listede askıdan sonra seçilebilir hesap kalmaz; ileti ve yol gösterme görünür", async () => {
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
    // Askı iletisi kalır; parola yolu yerine yol gösterme gelir, odak kurtarma düğmesindedir.
    expect(screen.getByText(SECILEBILIR_HESAP_YOK_METNI)).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Parola/)).toBeNull();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI })).toHaveFocus(),
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

  it.each([
    ["hesap kaydı", 409, "hesap_muhru_tutmadi", KAYIT_REDDI],
    ["iz boşluğu", 409, "hesap_muhru_tutmadi", IZ_BOSLUGU],
    ["özeti tutmayan parola kaydı", 409, "hesap_muhru_tutmadi", PAROLA_KAYDI],
    ["bağsız parola kaydı", 409, "iki_depo_tutarsiz", PAROLA_KAYDI],
  ])(
    "program yöneticisinde sunucunun ret iletisi olduğu gibi yazılır (%s); altında zarfın üçüncü durumunun yol metni durur",
    async (_ad, status, kod, ileti) => {
      const kullanici = userEvent.setup();
      oturum.ac.mockRejectedValue(new ApiError(status, kod, ileti));
      render(<KilitEkrani />);
      await hazir();

      await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

      expect((await screen.findByRole("alert")).textContent).toBe(ileti);
      // Kullanıcı kararı 04.11.2026: satır seçilebilir göründüğü hâlde giriş reddedildi; çıkış
      // (yedekten geri yükleme) iletinin altında yazılır. Seçilebilir satırlar kaldığı için
      // yol gösterme kutusu ve "Kurtarma anahtarıyla aç" çıkmaz.
      expect(screen.getByText(UCUNCU_DURUM_YOL_METNI)).toBeInTheDocument();
      // Yol metni odağın döndüğü alana bağlıdır: ekran okuyucu çıkışı da okur.
      await waitFor(() => expect(screen.getByLabelText(/^Parola/)).toHaveFocus());
      expect(screen.getByLabelText(/^Parola/)).toHaveAccessibleDescription(
        /zarfının üçüncü durumudur/,
      );
      expect(screen.queryByText(SECILEBILIR_HESAP_YOK_METNI)).toBeNull();
      expect(screen.queryByRole("button", { name: KURTARMA_ILE_AC_ETIKETI })).toBeNull();
      // Program yöneticisinin "Parolamı unuttum"u (iletinin andığı yol) yerindedir.
      expect(screen.getByRole("button", { name: "Parolamı unuttum" })).toBeInTheDocument();
      expect(oturum.ac).toHaveBeenCalledTimes(1);
    },
  );

  it.each([
    ["hatalı parola", 400, "parola_yanlis", "Parola hatalı."],
    ["ağ", 0, "network_error", "Sunucuya ulaşılamadı."],
    ["beklenmeyen", 500, "server_error", "Beklenmeyen bir hata oluştu."],
  ])("kayıt reddi olmayan retten (%s) sonra yol metni çıkmaz", async (_ad, status, kod, ileti) => {
    const kullanici = userEvent.setup();
    oturum.ac.mockRejectedValue(new ApiError(status, kod, ileti));
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

    await screen.findByRole("alert");
    expect(screen.queryByText(UCUNCU_DURUM_YOL_METNI)).toBeNull();
    expect(screen.getByLabelText(/^Parola/)).not.toHaveAccessibleDescription(/üçüncü durumudur/);
  });

  it.each([
    ["özeti tutmayan parola kaydı", 409, "hesap_muhru_tutmadi", PAROLA_KAYDI],
    ["bağsız parola kaydı", 409, "iki_depo_tutarsiz", PAROLA_KAYDI],
    ["hesap kaydı", 409, "hesap_muhru_tutmadi", KAYIT_REDDI],
    ["iz boşluğu", 409, "hesap_muhru_tutmadi", IZ_BOSLUGU],
  ])(
    "öteki hesapta kayıt reddinde (%s) yol metni çıkmaz: sunucunun iletisi çareyi kendisi söyler",
    async (_ad, status, kod, ileti) => {
      const kullanici = userEvent.setup();
      oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
      oturum.ac.mockRejectedValue(new ApiError(status, kod, ileti));
      render(<KilitEkrani />);
      await hazir();

      await kullanici.click(radyo("Muhasip (muhasip)"));
      await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

      expect((await screen.findByRole("alert")).textContent).toBe(ileti);
      // Kullanıcı kararı program yöneticisinin hesabı içindir; muhasibin parola kaydında çare
      // program yöneticisinin sıfırlamasıdır, ekranda ikinci (ağır) bir çare önerilmez.
      expect(screen.queryByText(UCUNCU_DURUM_YOL_METNI)).toBeNull();
      expect(screen.getByText(UNUTTUM_BASKA_ROL_METNI)).toBeInTheDocument();
    },
  );

  it("kayıt reddinin yol metni sonraki denemede kalkar", async () => {
    const kullanici = userEvent.setup();
    oturum.ac
      .mockRejectedValueOnce(new ApiError(409, "hesap_muhru_tutmadi", KAYIT_REDDI))
      .mockRejectedValueOnce(new ApiError(400, "parola_yanlis", "Parola hatalı."));
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");
    expect(await screen.findByText(UCUNCU_DURUM_YOL_METNI)).toBeInTheDocument();

    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-2{Enter}");
    expect(await screen.findByText("Parola hatalı.")).toBeInTheDocument();
    expect(screen.queryByText(UCUNCU_DURUM_YOL_METNI)).toBeNull();
    expect(screen.queryByText(KAYIT_REDDI)).toBeNull();
  });
});

describe("KilitEkrani — çift gönderim", () => {
  it("aynı anda gelen iki gönderimden yalnız biri gider", async () => {
    oturum.ac.mockReturnValue(new Promise(() => undefined));
    render(<KilitEkrani />);
    await hazir();
    const alan = screen.getByLabelText(/^Parola/);
    fireEvent.change(alan, { target: { value: "Deneme-Parola-1" } });

    // İki gönderim yeniden çizimden önce: `calisiyor` ikisinde de henüz false'tur.
    act(() => {
      formu(alan).requestSubmit();
      formu(alan).requestSubmit();
    });

    expect(await screen.findByRole("status")).toHaveTextContent("Denetleniyor…");
    expect(oturum.ac).toHaveBeenCalledTimes(1);
  });

  it("satırda yinelenen Enter (requestSubmit yolu) ikinci gönderim yapmaz", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI, MUHASIP]);
    oturum.ac.mockReturnValue(new Promise(() => undefined));
    render(<KilitEkrani />);
    await hazir();
    await kullanici.click(radyo("Muhasip (muhasip)"));
    await kullanici.type(screen.getByLabelText(/^Parola/), "Muhasip-Parola-1");
    const satir = radyo("Muhasip (muhasip)");

    act(() => {
      fireEvent.keyDown(satir, { key: "Enter" });
      fireEvent.keyDown(satir, { key: "Enter" });
    });

    await screen.findByRole("status");
    expect(oturum.ac).toHaveBeenCalledTimes(1);
    expect(oturum.ac).toHaveBeenCalledWith({ hesap: MUHASIP.id, parola: "Muhasip-Parola-1" });
  });

  it("açılıştan sonra (pencere yüklenirken) ikinci açılış gitmez", async () => {
    const kullanici = userEvent.setup();
    oturum.ac.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();
    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");
    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));

    act(() => {
      formu(screen.getByLabelText(/^Parola/)).requestSubmit();
    });

    expect(oturum.ac).toHaveBeenCalledTimes(1);
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("ret geldikten sonra yeniden gönderilebilir", async () => {
    const kullanici = userEvent.setup();
    oturum.ac
      .mockRejectedValueOnce(new ApiError(400, "parola_yanlis", "Parola hatalı."))
      .mockResolvedValueOnce({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();

    await kullanici.type(screen.getByLabelText(/^Parola/), "yanlis{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent("Parola hatalı.");
    await kullanici.type(screen.getByLabelText(/^Parola/), "Deneme-Parola-1{Enter}");

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.ac).toHaveBeenCalledTimes(2);
  });

  it("kurtarma yolunda da aynı anda gelen iki gönderimden yalnız biri gider", async () => {
    const kullanici = userEvent.setup();
    oturum.kurtar.mockReturnValue(new Promise(() => undefined));
    render(<KilitEkrani />);
    await hazir();
    await kullanici.click(screen.getByRole("button", { name: "Parolamı unuttum" }));
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    const form = screen.getByRole("form", { name: "Kurtarma yolu" });

    act(() => {
      (form as HTMLFormElement).requestSubmit();
      (form as HTMLFormElement).requestSubmit();
    });

    expect(await screen.findByRole("status")).toHaveTextContent("Denetleniyor…");
    expect(oturum.kurtar).toHaveBeenCalledTimes(1);
  });
});

describe("KilitEkrani — seçilebilir satır kalmayınca yol gösterme", () => {
  it("liste dolu ama hiçbir satır seçilemiyorsa yol gösterir; parola yolu kalkar, odak kurtarma düğmesindedir", async () => {
    oturum.hesaplar.mockResolvedValue([YONETICI_ASKIDA, DK_UYELIK, OKUNAMAYAN]);
    render(<KilitEkrani />);
    await hazir();

    // Satırlar nedenleriyle yerinde kalır.
    expect(radyo("Program yöneticisi (yonetici)")).toBeDisabled();
    expect(radyo("Program yöneticisi (yonetici)")).toHaveAccessibleDescription(ASKIDA_ETIKETI);
    expect(radyo(`${OKUNAMADI_ETIKETI} (sekreter)`)).toBeDisabled();
    // Yol gösterme: kim ne yapar ve zarfın üçüncü durumu.
    expect(screen.getByText(SECILEBILIR_HESAP_YOK_METNI)).toBeInTheDocument();
    expect(screen.getByText(UCUNCU_DURUM_YOL_METNI)).toBeInTheDocument();
    // Gönderilecek bir şey yok: Parola alanı, "Aç" ve "Parolamı unuttum" çizilmez.
    expect(screen.queryByLabelText(/^Parola/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Aç" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Parolamı unuttum" })).toBeNull();
    // Düğme yol gösterme metnine bağlıdır: ekran okuyucu nedenini de okur.
    const dugme = screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI });
    expect(dugme).toHaveAccessibleDescription(
      /seçilebilecek hesap kalmadı.*Denetleme Kuruluna bildirin/,
    );
    await waitFor(() => expect(dugme).toHaveFocus());
    // Uyarı değil bilgidir: tek uyarı yoktur (askı iletisi gibi uyarılarla karışmaz).
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("yol gösterme kullanıcı kararlarının sözlerini taşır", () => {
    // Zarfın üçüncü durumu (02.11.2026) ve çaresi (03.11.2026) belgeyle ve panelle birebir.
    expect(UCUNCU_DURUM_YOL_METNI).toContain(ZARFIN_UCUNCU_DURUMU);
    expect(UCUNCU_DURUM_YOL_METNI).toContain(UCUNCU_DURUMUN_CARESI);
    expect(UCUNCU_DURUM_YOL_METNI).toContain("kurtarma anahtarı zarfının üçüncü durumudur");
    expect(UCUNCU_DURUM_YOL_METNI).toContain("Denetleme Kuruluna bildirin");
    // Kilitliyken geri yüklemenin yolu kısayol ve komuttur (sözlük §1 "Yedek").
    expect(UCUNCU_DURUM_YOL_METNI).toContain(
      "Başlat menüsündeki “OAB Defteri — Yedekten Geri Yükle” kısayolunu",
    );
    expect(UCUNCU_DURUM_YOL_METNI).toContain("oab-defteri --geri-yukle");
    // Program yöneticisi için "Parolamı unuttum", öteki hesaplar için program yöneticisi.
    expect(SECILEBILIR_HESAP_YOK_METNI).toContain("(“Parolamı unuttum” yolu)");
    expect(SECILEBILIR_HESAP_YOK_METNI).toContain(`“${KURTARMA_ILE_AC_ETIKETI}” düğmesiyle`);
    expect(SECILEBILIR_HESAP_YOK_METNI).toContain(
      "Öteki hesaplar program yöneticisine başvurur: askıyı o kaldırır, parolayı o sıfırlar.",
    );
    // Boş liste de Denetleme Kurulunu anar (geri yükleme yoksa dosya değiştirilmiştir).
    expect(BOS_LISTE_METNI).toContain("Denetleme Kuruluna bildirin");
    expect(KURTARILACAK_HESAP_YOK_METNI).toContain("Denetleme Kuruluna bildirin");
    // Sözlük: iç terimler ve kısaltmalar kullanıcı metnine çıkmaz.
    for (const metin of [
      SECILEBILIR_HESAP_YOK_METNI,
      UCUNCU_DURUM_YOL_METNI,
      BOS_LISTE_METNI,
      KURTARILACAK_HESAP_YOK_METNI,
    ]) {
      expect(metin).not.toMatch(/sarmal|mühür|zincir|\bDK\b|\bYK\b|şifre(?!l)/i);
    }
  });

  it("“Kurtarma anahtarıyla aç” kurtarma yolunu açar: hesap kurtarma listesinden gelir, dönülebilir, kurtarınca pencere yüklenir", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI_ASKIDA]);
    oturum.kurtarmaHesaplari.mockResolvedValue([KURTARILACAK_YONETICI]);
    oturum.kurtar.mockResolvedValue({ durum: "acik" });
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI }));
    const form = screen.getByRole("form", { name: "Kurtarma yolu" });
    expect(
      await within(form).findByRole("radio", { name: "Program yöneticisi (yonetici)" }),
    ).toBeChecked();
    expect(oturum.kurtarmaHesaplari).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(SECILEBILIR_HESAP_YOK_METNI)).toBeNull();

    // Geri dönüş yol göstermeye döner; odak sayfa gövdesine düşmez.
    await kullanici.click(screen.getByRole("button", { name: "Parolayla açmaya dön" }));
    expect(screen.getByText(SECILEBILIR_HESAP_YOK_METNI)).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI })).toHaveFocus(),
    );

    await kullanici.click(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI }));
    await screen.findByRole("radio", { name: "Program yöneticisi (yonetici)", checked: true });
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
    expect(oturum.ac).not.toHaveBeenCalled();
  });

  it("kurtarmanın reddi (sunucunun iletisi) olduğu gibi yazılır", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI_ASKIDA]);
    oturum.kurtarmaHesaplari.mockResolvedValue([KURTARILACAK_YONETICI]);
    oturum.kurtar.mockRejectedValue(new ApiError(409, "hesap_muhru_tutmadi", KAYIT_REDDI));
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI }));
    await screen.findByRole("radio", { name: "Program yöneticisi (yonetici)", checked: true });
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    expect((await screen.findByRole("alert")).textContent).toBe(KAYIT_REDDI);
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
    // Kayıt reddi: yol metni iletinin altında durur (kullanıcı kararı 04.11.2026) ve odağın
    // döndüğü Kurtarma anahtarı alanını açıklar.
    expect(screen.getByText(UCUNCU_DURUM_YOL_METNI)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText(/^Kurtarma anahtarı/)).toHaveFocus());
    expect(screen.getByLabelText(/^Kurtarma anahtarı/)).toHaveAccessibleDescription(
      /zarfının üçüncü durumudur/,
    );
  });

  it("kurtarmanın kayıt reddi olmayan reddinde (yanlış anahtar) yol metni çıkmaz", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([YONETICI]);
    oturum.kurtar.mockRejectedValue(
      new ApiError(400, "validation_error", "Kurtarma anahtarı hatalı."),
    );
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: "Parolamı unuttum" }));
    await kullanici.type(screen.getByLabelText(/^Kurtarma anahtarı/), "AAAA-BBBB");
    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Kurtar ve aç" }));

    expect((await screen.findByRole("alert")).textContent).toBe("Kurtarma anahtarı hatalı.");
    expect(screen.queryByText(UCUNCU_DURUM_YOL_METNI)).toBeNull();
    expect(screen.getByLabelText(/^Kurtarma anahtarı/)).not.toHaveAccessibleDescription(
      /üçüncü durumudur/,
    );
  });

  it("kurtarma listesi de boşsa yolun sonunu söyler: Denetleme Kurulu ve yedekten geri yükleme", async () => {
    const kullanici = userEvent.setup();
    oturum.hesaplar.mockResolvedValue([OKUNAMAYAN]);
    oturum.kurtarmaHesaplari.mockResolvedValue([]);
    render(<KilitEkrani />);
    await hazir();

    await kullanici.click(screen.getByRole("button", { name: KURTARMA_ILE_AC_ETIKETI }));

    expect(await screen.findByText(KURTARILACAK_HESAP_YOK_METNI)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kurtar ve aç" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Parolayla açmaya dön" })).toBeEnabled();
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

  it("yenilemede kayıt reddi: yol metni Yeni parola alanını gerekçeyle birlikte açıklar", async () => {
    const kullanici = userEvent.setup();
    await yenilemeyeGec(kullanici);
    oturum.ac.mockRejectedValueOnce(new ApiError(409, "hesap_muhru_tutmadi", KAYIT_REDDI));

    await kullanici.type(screen.getByLabelText(/^Yeni parola/), GECERLI_PAROLA);
    await kullanici.type(screen.getByLabelText(/^Parola \(tekrar\)/), GECERLI_PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Parolayı yenile ve aç" }));

    expect((await screen.findByRole("alert")).textContent).toBe(KAYIT_REDDI);
    expect(screen.getByText(UCUNCU_DURUM_YOL_METNI)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText(/^Yeni parola/)).toHaveFocus());
    expect(screen.getByLabelText(/^Yeni parola/)).toHaveAccessibleDescription(
      /Parolanızı yenilemeniz gerekiyor.*zarfının üçüncü durumudur.*En az 8 karakter/,
    );
  });

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

describe("KilitEkrani — üyelik askısının iletisi", () => {
  it("yalnız hatalı deneme askısı varsa ileti çıkmaz; görev bölümü askısında çıkar", async () => {
    oturum.hesaplar.mockResolvedValue([YONETICI, DK_ASKIDA]);
    const { unmount } = render(<KilitEkrani />);
    await hazir();
    expect(screen.queryByText(UYELIK_ASKISI_METNI)).toBeNull();
    unmount();
    oturum.hesaplar.mockResolvedValue([
      YONETICI,
      { ...MUHASIP, secilebilir: false, askida_nedeni: "GOREV_BOLUMU" },
    ]);
    render(<KilitEkrani />);
    await hazir();
    expect(screen.getByText(UYELIK_ASKISI_METNI)).toBeInTheDocument();
    expect(radyo("Muhasip (muhasip)")).toHaveAccessibleDescription(ASKIDA_ETIKETI);
  });
});
