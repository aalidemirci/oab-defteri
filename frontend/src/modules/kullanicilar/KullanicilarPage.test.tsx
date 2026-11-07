// Kullanıcılar ekranı (plan F1b-2 "Kullanıcılar uçları"): liste bütün hesapları sunucunun sırasıyla
// gösterir; eylemler ve yapılamama nedenleri sunucunundur (ön yüz yalnız eşler, neden düğmenin
// yanında); her yazmadan sonra liste yeniden okunur (güvenlik dosyası yazılamasa da); kapama onay
// diyaloğundan geçer; geçici parola sonuçta görünmez; pusulanın adı sunucunun başlığındandır.
// Veriler uydurmadır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import {
  HESAP_KAPALI,
  KAPALI_HESAP,
  KENDI_HESABI,
  KENDI_KAPAT,
  KENDI_PUSULA,
  KENDI_SIFIRLA,
  KAYIT_DEGISMIS,
  ASKIDA_DEGIL,
  ayrinti,
  hesapSatiri,
} from "../../test/kullanicilar";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { parolaSorunu } from "../oturum/parolaPolitikasi";

const apiMock = vi.hoisted(() => ({
  liste: vi.fn(),
  secenekler: vi.fn(),
  ayrinti: vi.fn(),
  ac: vi.fn(),
  kapat: vi.fn(),
  askidanCikar: vi.fn(),
  parolaSifirla: vi.fn(),
  pusula: vi.fn(),
}));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  kullanicilarApi: apiMock,
}));

const indirme = vi.hoisted(() => ({ saveBlob: vi.fn() }));

vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: indirme.saveBlob,
}));

import KullanicilarPage from "./KullanicilarPage";
import { ZARF_METNI } from "./metinler";

const MUHASIP = hesapSatiri();
const ASKIDAKI = hesapSatiri({
  id: "5b4a3c2d-1e0f-4a9b-8c7d-6e5f4a3b2c1d",
  tanitici: "dk-1",
  rol: "denetleme_kurulu",
  rol_etiketi: "Denetleme Kurulu",
  ad_soyad: null,
  durum: "ASKIDA",
  durum_etiketi: "Askıda",
  askida_nedeni: "HATALI_DENEME",
  askida_nedeni_etiketi: "Hatalı parola denemesi",
  son_giris: null,
  giris: { yapabilir: false, neden: "Hesap askıda; askıdan çıkarılınca giriş açılır." },
  eylemler: {
    kapat: { yapilabilir: true, neden: null },
    askidan_cikar: { yapilabilir: true, neden: null },
    parola_sifirla: {
      yapilabilir: false,
      neden: "Askıdaki hesabın parolası sıfırlanamaz; önce hesabı askıdan çıkarın.",
    },
    pusula: { yapilabilir: true, neden: null },
  },
});
const BOZUK = hesapSatiri({
  id: "7c6b5a4f-3e2d-4c1b-8a0f-9e8d7c6b5a4f",
  tanitici: "baskan",
  rol: "baskan",
  rol_etiketi: "Başkan",
  ad_soyad: "Uydurma Başkan",
  kayit_tutuyor: false,
  giris: { yapabilir: false, neden: KAYIT_DEGISMIS },
});

const LISTE = [KENDI_HESABI, MUHASIP, ASKIDAKI, BOZUK, KAPALI_HESAP];

function bas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <KullanicilarPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function tablo(): Promise<HTMLElement> {
  return screen.findByRole("table", { name: "Hesaplar" });
}

/** Satırı (tıklanabilir) erişilebilir adıyla açar ve ayrıntı penceresini döndürür. */
async function ayrintiyiAc(
  user: ReturnType<typeof userEvent.setup>,
  rolTanitici: string,
): Promise<HTMLElement> {
  await user.click(
    within(await tablo()).getByRole("button", {
      name: `${rolTanitici} hesabının ayrıntısını aç`,
    }),
  );
  return screen.findByRole("dialog", { name: "Hesap ayrıntısı" });
}

beforeEach(() => {
  vi.clearAllMocks();
  // Gerçek `saveBlob` hep sonuç döndürür: sahte `undefined` dönseydi başarı dalı sınanmazdı.
  indirme.saveBlob.mockResolvedValue("kaydedildi");
  apiMock.liste.mockResolvedValue(LISTE);
  apiMock.ayrinti.mockImplementation((id: string) =>
    Promise.resolve(ayrinti(LISTE.find((h) => h.id === id) ?? MUHASIP)),
  );
});

describe("Kullanıcılar — liste", () => {
  it("bütün hesaplar sunucunun sırasıyla; kapalı ve giriş yapamayanlar dahil", async () => {
    bas();
    const t = await tablo();
    expect(screen.getByRole("heading", { level: 1, name: "Kullanıcılar" })).toBeInTheDocument();
    expect(
      within(t)
        .getAllByRole("columnheader")
        .map((h) => h.textContent),
    ).toEqual(["Tanıtıcı", "Rol", "Hesap sahibi", "Durum", "Son giriş"]);
    const satirlar = within(t).getAllByRole("button");
    expect(satirlar.map((s) => s.getAttribute("aria-label"))).toEqual([
      "Program yöneticisi · tanıtıcı yonetici hesabının ayrıntısını aç",
      "Muhasip · tanıtıcı muhasip hesabının ayrıntısını aç",
      "Denetleme Kurulu · tanıtıcı dk-1 hesabının ayrıntısını aç",
      "Başkan · tanıtıcı baskan hesabının ayrıntısını aç",
      "Sekreter · tanıtıcı sekreter hesabının ayrıntısını aç",
    ]);
    // Oturumdaki hesap işaretli; rol etiketi sıra no'suz; çözülemeyen ad "okunamadı".
    expect(within(satirlar[0]).getByText(/bu oturum/)).toBeInTheDocument();
    expect(within(satirlar[2]).getByText("okunamadı")).toBeInTheDocument();
    expect(within(satirlar[1]).getByText("03.11.2026 08:05")).toBeInTheDocument();
    // Durum: askının nedeni ve girişin nedeni (sunucunun metni).
    expect(within(satirlar[2]).getByText("Askıda · Hatalı parola denemesi")).toBeInTheDocument();
    expect(
      within(satirlar[2]).getByText("Hesap askıda; askıdan çıkarılınca giriş açılır."),
    ).toBeInTheDocument();
    expect(within(satirlar[3]).getByText(KAYIT_DEGISMIS)).toBeInTheDocument();
    // Kapalı hesapta kapanış günü; "Hesap kapalı." durumla aynı şeyi söylediği için yinelenmez.
    expect(within(satirlar[4]).getByText("Kapalı · 03.11.2026")).toBeInTheDocument();
    expect(within(satirlar[4]).queryByText("Hesap kapalı.")).toBeNull();
    expect(apiMock.liste).toHaveBeenCalledTimes(1);
  });

  it("liste okunamazsa sunucunun iletisi (rol reddi dahil) görünür", async () => {
    apiMock.liste.mockRejectedValue(
      new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."),
    );
    bas();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Bu işlem hesabınızın rolüne açık değil.",
    );
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("ağ hatasında yedek ileti; boş listede boş durum", async () => {
    apiMock.liste.mockRejectedValueOnce(new TypeError("ağ yok"));
    const { unmount } = bas();
    expect(await screen.findByRole("alert")).toHaveTextContent("Hesap listesi okunamadı.");
    unmount();
    apiMock.liste.mockResolvedValue([]);
    bas();
    expect(await screen.findByText("Gösterilecek hesap yok")).toBeInTheDocument();
  });
});

describe("Kullanıcılar — ayrıntı", () => {
  it("satır klavyeyle de açılır; ayrıntı açan, sıfırlama ve son girişleri yazar", async () => {
    const user = userEvent.setup();
    apiMock.ayrinti.mockResolvedValue(
      ayrinti(MUHASIP, {
        parola_degisimi: "2026-11-02T11:00:00+03:00",
        sifirlama: {
          tur: "SIFIRLAMA",
          zaman: "2026-11-03T09:00:00+03:00",
          yapan: { id: KENDI_HESABI.id, tanitici: "yonetici", rol_etiketi: "Program yöneticisi" },
        },
        son_girisler: ["2026-11-03T08:05:00+03:00", "2026-11-02T12:30:00+03:00"],
      }),
    );
    bas();
    const satir = within(await tablo()).getByRole("button", {
      name: "Muhasip · tanıtıcı muhasip hesabının ayrıntısını aç",
    });
    satir.focus();
    await user.keyboard("{Enter}");
    const pencere = await screen.findByRole("dialog", { name: "Hesap ayrıntısı" });

    expect(apiMock.ayrinti).toHaveBeenCalledWith(MUHASIP.id);
    expect(
      await within(pencere).findByText(
        "02.11.2026 10:15 · açan: Program yöneticisi · tanıtıcı yonetici",
      ),
    ).toBeInTheDocument();
    expect(within(pencere).getByText("02.11.2026 11:00")).toBeInTheDocument();
    expect(
      within(pencere).getByText(
        "Parola sıfırlandı · 03.11.2026 09:00 · yapan: Program yöneticisi · tanıtıcı yonetici",
      ),
    ).toBeInTheDocument();
    const girisler = within(pencere).getByRole("region", {
      name: "Kilit ekranından son girişler",
    });
    expect(
      within(girisler)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["03.11.2026 08:05", "02.11.2026 12:30"]);
    expect(within(pencere).getByText("Kilit ekranından girebilir.")).toBeInTheDocument();
    expect(within(pencere).getByText("Deneme Muhasipoğlu")).toBeInTheDocument();
  });

  it("giriş kaydı yoksa söyler; ayrıntı okunamazsa yalnız o bölüm okunamadı der", async () => {
    const user = userEvent.setup();
    bas();
    let pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    expect(
      await within(pencere).findByText("Bu hesapla henüz kilit ekranından giriş yapılmadı."),
    ).toBeInTheDocument();
    await user.click(within(pencere).getByRole("button", { name: "Kapat" }));

    apiMock.ayrinti.mockRejectedValue(new TypeError("ağ yok"));
    pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    expect(await within(pencere).findByText("Hesabın ayrıntısı okunamadı.")).toBeInTheDocument();
    // Satırın bilgisi ve eylemleri yine durur.
    expect(within(pencere).getByRole("button", { name: "Parolayı sıfırla" })).toBeEnabled();
  });

  it("eylemler sunucunundur: yapılamayan düğme kapalı, sunucunun nedeni yanında", async () => {
    const user = userEvent.setup();
    bas();
    const pencere = await ayrintiyiAc(user, "Program yöneticisi · tanıtıcı yonetici");
    const beklenen: Array<[string, string]> = [
      ["Parolayı sıfırla", KENDI_SIFIRLA],
      ["Askıdan çıkar", ASKIDA_DEGIL],
      ["Hesap teslim pusulasını kaydet", KENDI_PUSULA],
      ["Hesabı kapat", KENDI_KAPAT],
    ];
    for (const [ad, neden] of beklenen) {
      const dugme = within(pencere).getByRole("button", { name: ad });
      expect(dugme).toBeDisabled();
      expect(dugme).toHaveAccessibleDescription(neden);
      expect(within(pencere).getByText(neden)).toBeVisible();
    }
  });

  it("dört eylemin nedeni aynıysa (kapalı hesap) neden bir kez yazılır", async () => {
    const user = userEvent.setup();
    bas();
    const pencere = await ayrintiyiAc(user, "Sekreter · tanıtıcı sekreter");
    expect(within(pencere).getAllByText(HESAP_KAPALI)).toHaveLength(1);
    for (const ad of ["Parolayı sıfırla", "Askıdan çıkar", "Hesabı kapat"]) {
      const dugme = within(pencere).getByRole("button", { name: ad });
      expect(dugme).toBeDisabled();
      expect(dugme).toHaveAccessibleDescription(HESAP_KAPALI);
    }
    expect(within(pencere).getByText("Kapalı · 03.11.2026")).toBeInTheDocument();
  });

  it("askıdan çıkarma pencerede yürür; liste yeniden okunur", async () => {
    const user = userEvent.setup();
    apiMock.askidanCikar.mockResolvedValue({ hesap: ASKIDAKI });
    bas();
    const pencere = await ayrintiyiAc(user, "Denetleme Kurulu · tanıtıcı dk-1");
    // Askıdaki hesabın parolası sıfırlanmaz (sunucunun nedeni).
    expect(within(pencere).getByRole("button", { name: "Parolayı sıfırla" })).toBeDisabled();

    await user.click(within(pencere).getByRole("button", { name: "Askıdan çıkar" }));

    expect(apiMock.askidanCikar).toHaveBeenCalledWith(ASKIDAKI.id);
    expect(await screen.findByText("Hesap askıdan çıkarıldı.")).toBeInTheDocument();
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
  });

  it("askıdan çıkarmanın reddi pencerede; liste yine yeniden okunur", async () => {
    const user = userEvent.setup();
    const ileti =
      "Hesabın askısı kaldırıldı, ancak hatalı parola denemelerinin kaydı güvenlik dosyasından " +
      "silinemedi (ör. dosyayı başka bir program tutuyor). Hesap hâlâ askıda görünürse askıdan " +
      "çıkarmayı yeniden deneyin.";
    apiMock.askidanCikar.mockRejectedValue(new ApiError(400, "validation_error", ileti));
    bas();
    const pencere = await ayrintiyiAc(user, "Denetleme Kurulu · tanıtıcı dk-1");
    await user.click(within(pencere).getByRole("button", { name: "Askıdan çıkar" }));

    expect(await within(pencere).findByText(ileti)).toBeInTheDocument();
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
  });

  it("pusula sunucunun adıyla kaydedilir; ad gelmezse aynı kalıp kurulur", async () => {
    const user = userEvent.setup();
    const pdf = new Blob(["%PDF"]);
    apiMock.pusula.mockResolvedValueOnce({
      blob: pdf,
      ad: "Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf",
    });
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(
      within(pencere).getByRole("button", { name: "Hesap teslim pusulasını kaydet" }),
    );

    expect(apiMock.pusula).toHaveBeenCalledWith(MUHASIP.id);
    await waitFor(() =>
      expect(indirme.saveBlob).toHaveBeenCalledWith(
        pdf,
        "Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf",
      ),
    );
    expect(await screen.findByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeVisible();

    apiMock.pusula.mockResolvedValueOnce({ blob: pdf, ad: null });
    await user.click(
      within(pencere).getByRole("button", { name: "Hesap teslim pusulasını kaydet" }),
    );
    await waitFor(() => expect(indirme.saveBlob).toHaveBeenCalledTimes(2));
    expect(indirme.saveBlob.mock.calls[1][1]).toMatch(
      /^Hesap-Teslim-Pusulası_Muhasip_\d{2}\.\d{2}\.\d{4}\.pdf$/,
    );
  });

  it("köprü yoksa dosya tarayıcıya verilir, bildirim yine çıkar", async () => {
    const user = userEvent.setup();
    apiMock.pusula.mockResolvedValue({ blob: new Blob(["%PDF-"]), ad: "pusula.pdf" });
    indirme.saveBlob.mockResolvedValueOnce("indirildi");
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");

    await user.click(
      within(pencere).getByRole("button", { name: "Hesap teslim pusulasını kaydet" }),
    );

    expect(await screen.findByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeVisible();
  });

  it("kaydetme penceresinde iptal sessizdir, yazılamazsa pencerede tek ileti çıkar", async () => {
    const user = userEvent.setup();
    apiMock.pusula.mockResolvedValue({ blob: new Blob(["%PDF-"]), ad: "pusula.pdf" });
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    const dugme = within(pencere).getByRole("button", { name: "Hesap teslim pusulasını kaydet" });

    indirme.saveBlob.mockResolvedValueOnce("iptal");
    await user.click(dugme);
    await waitFor(() => expect(indirme.saveBlob).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(dugme).toBeEnabled());
    expect(screen.queryByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeNull();
    expect(within(pencere).queryByText(DOSYA_YAZILAMADI_ILETISI)).toBeNull();

    indirme.saveBlob.mockResolvedValueOnce("hata");
    await user.click(dugme);
    expect(await within(pencere).findByText(DOSYA_YAZILAMADI_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeNull();
  });

  it("pusulanın reddi (kaydı tutmayan hesap) pencerede sunucunun iletisiyle", async () => {
    const user = userEvent.setup();
    const ileti =
      "Hesap kaydı program dışından değiştirilmiş görünüyor; kayda dokunulmadı. Denetleme " +
      "Kuruluna bildirin.";
    apiMock.pusula.mockRejectedValue(new ApiError(409, "hesap_muhru_tutmadi", ileti));
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(
      within(pencere).getByRole("button", { name: "Hesap teslim pusulasını kaydet" }),
    );
    expect(await within(pencere).findByText(ileti)).toBeInTheDocument();
    expect(indirme.saveBlob).not.toHaveBeenCalled();
  });
});

describe("Kullanıcılar — kapama", () => {
  it("onay diyaloğundan geçer: başlık soru, gövde sonuç; onayla kapanır", async () => {
    const user = userEvent.setup();
    apiMock.kapat.mockResolvedValue({ hesap: MUHASIP });
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Hesabı kapat" }));

    // Ayrıntı penceresi kapanır, onay açılır (üst üste iki pencere yok).
    const onay = await screen.findByRole("dialog", { name: "Hesap kapatılsın mı?" });
    expect(screen.queryByRole("dialog", { name: "Hesap ayrıntısı" })).toBeNull();
    expect(onay).toHaveTextContent(
      "Muhasip · tanıtıcı muhasip hesabı kapanır: kilit ekranından kalkar, parola kaydı bu " +
        "bilgisayarın güvenlik dosyasından silinir.",
    );
    await user.click(within(onay).getByRole("button", { name: "Hesabı kapat" }));

    expect(apiMock.kapat).toHaveBeenCalledWith(MUHASIP.id);
    expect(await screen.findByText("Hesap kapatıldı.")).toBeInTheDocument();
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
  });

  it("vazgeçilirse istek gitmez", async () => {
    const user = userEvent.setup();
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Hesabı kapat" }));
    const onay = await screen.findByRole("dialog", { name: "Hesap kapatılsın mı?" });
    await user.click(within(onay).getByRole("button", { name: "Vazgeç" }));
    expect(apiMock.kapat).not.toHaveBeenCalled();
  });

  it("parola kaydı silinemezse (400) hesap kapanmıştır: ileti sayfada, liste yenilenir", async () => {
    const user = userEvent.setup();
    const ileti =
      "Hesap kapatıldı, ancak parola kaydının güvenlik dosyasından silinmesi tamamlanamadı (ör. " +
      "dosyayı başka bir program tutuyor); program bir sonraki kilit açılışında yineler.";
    apiMock.kapat.mockRejectedValue(new ApiError(400, "validation_error", ileti));
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Hesabı kapat" }));
    const onay = await screen.findByRole("dialog", { name: "Hesap kapatılsın mı?" });
    await user.click(within(onay).getByRole("button", { name: "Hesabı kapat" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(ileti);
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Hesap kapatıldı.")).toBeNull();
  });
});

describe("Kullanıcılar — parola sıfırlama", () => {
  it("alan önerilen geçici parolayla dolu; gönderilir, sonuçta gösterilmez", async () => {
    const user = userEvent.setup();
    apiMock.parolaSifirla.mockResolvedValue({ hesap: MUHASIP });
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));

    const form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    expect(screen.queryByRole("dialog", { name: "Hesap ayrıntısı" })).toBeNull();
    expect(form).toHaveTextContent("Hesap: Muhasip · tanıtıcı muhasip");
    const alan = within(form).getByLabelText(/^Geçici parola/);
    const oneri = (alan as HTMLInputElement).value;
    expect([...oneri]).toHaveLength(12);
    expect(parolaSorunu(oneri)).toBeNull();
    // Açılışta odak alandadır; zarf notu alana bağlıdır; kopyalama düğmesi yoktur: pencerenin
    // düğmeleri tam olarak bunlardır (adı ne olursa olsun başka düğme yok).
    expect(alan).toHaveFocus();
    expect(alan).toHaveAccessibleDescription(expect.stringContaining(ZARF_METNI));
    expect(within(form).getAllByRole("button")).toHaveLength(3);
    for (const ad of ["Yeni öneri", "Vazgeç", "Sıfırla"]) {
      expect(within(form).getByRole("button", { name: ad })).toBeInTheDocument();
    }

    await user.click(within(form).getByRole("button", { name: "Sıfırla" }));

    expect(apiMock.parolaSifirla).toHaveBeenCalledWith(MUHASIP.id, oneri);
    expect(
      await screen.findByText(
        "Parola sıfırlandı. Geçici parolayı kapalı zarfta hesap sahibine verin.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Parolayı sıfırla" })).toBeNull();
    expect(document.body.textContent).not.toContain(oneri);
    expect(screen.queryByDisplayValue(oneri)).toBeNull();
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
  });

  it("parola kuralına uymayan değer alanın altında reddedilir, istek gitmez", async () => {
    const user = userEvent.setup();
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));
    const form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    const alan = within(form).getByLabelText(/^Geçici parola/);
    await user.clear(alan);
    await user.type(alan, "kisa");
    await user.click(within(form).getByRole("button", { name: "Sıfırla" }));

    expect(await within(form).findByText("Parola en az 8 karakter olmalıdır.")).toBeVisible();
    expect(alan).toHaveAttribute("aria-invalid", "true");
    expect(apiMock.parolaSifirla).not.toHaveBeenCalled();
  });

  it("“Yeni öneri” alanı yeni bir öneriyle doldurur", async () => {
    const user = userEvent.setup();
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));
    const form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    const alan = within(form).getByLabelText(/^Geçici parola/) as HTMLInputElement;
    const once = alan.value;
    await user.click(within(form).getByRole("button", { name: "Yeni öneri" }));
    const yeni = alan.value;
    expect(yeni).not.toBe(once);
    expect(parolaSorunu(yeni)).toBeNull();
    expect([...yeni]).toHaveLength(12);
    // Her basış yeni bir öneridir (sabit bir değer yazılmaz).
    await user.click(within(form).getByRole("button", { name: "Yeni öneri" }));
    expect(alan.value).not.toBe(yeni);
  });

  it("her açılış güvenli kaynaktan yeni öneri kurar (iki zarfa aynı parola girmez)", async () => {
    const user = userEvent.setup();
    bas();
    let pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    const guvenli = vi.spyOn(globalThis.crypto, "getRandomValues");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));
    let form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    expect(guvenli).toHaveBeenCalled();
    guvenli.mockRestore();
    const birinci = (within(form).getByLabelText(/^Geçici parola/) as HTMLInputElement).value;
    await user.click(within(form).getByRole("button", { name: "Vazgeç" }));

    pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));
    form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    const ikinci = (within(form).getByLabelText(/^Geçici parola/) as HTMLInputElement).value;
    expect(ikinci).not.toBe(birinci);
    expect(parolaSorunu(ikinci)).toBeNull();
  });

  it("sunucunun reddi pencerede; liste yine yeniden okunur", async () => {
    const user = userEvent.setup();
    const ileti =
      "Parola kaydı güvenlik dosyasına yazılamadı (ör. dosyayı başka bir program tutuyor); " +
      "geçici parola geçerli değil. Hesabın durumu “Parola yenilenmeli”; parolayı yeniden sıfırlayın.";
    apiMock.parolaSifirla.mockRejectedValue(new ApiError(400, "validation_error", ileti));
    bas();
    const pencere = await ayrintiyiAc(user, "Muhasip · tanıtıcı muhasip");
    await user.click(within(pencere).getByRole("button", { name: "Parolayı sıfırla" }));
    const form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    await user.click(within(form).getByRole("button", { name: "Sıfırla" }));

    expect(await within(form).findByRole("alert")).toHaveTextContent(ileti);
    await waitFor(() => expect(apiMock.liste).toHaveBeenCalledTimes(2));
    await user.click(within(form).getByRole("button", { name: "Vazgeç" }));
    expect(screen.queryByRole("dialog", { name: "Parolayı sıfırla" })).toBeNull();
  });
});

describe("Kullanıcılar — yeni hesap", () => {
  it("“Yeni hesap” penceresi açılır ve kapanır", async () => {
    const user = userEvent.setup();
    apiMock.secenekler.mockResolvedValue({ roller: [] });
    bas();
    await tablo();
    await user.click(screen.getByRole("button", { name: "Yeni hesap" }));
    const pencere = await screen.findByRole("dialog", { name: "Yeni hesap" });
    await user.click(within(pencere).getByRole("button", { name: "Vazgeç" }));
    expect(screen.queryByRole("dialog", { name: "Yeni hesap" })).toBeNull();
  });

  it("hesap açıldı ama parola kaydı yazılamadı: “Parolayı sıfırla” o hesabın penceresini açar", async () => {
    const user = userEvent.setup();
    const ileti =
      "Hesap açıldı, ancak parola kaydı güvenlik dosyasına yazılamadı (ör. dosyayı başka bir " +
      "program tutuyor); hesabın parolasını sıfırlayın.";
    const yeni = hesapSatiri({
      id: "2e1d0c9b-8a7f-4e6d-9c5b-4a3f2e1d0c9b",
      tanitici: "dk-2",
      rol: "denetleme_kurulu",
      rol_etiketi: "Denetleme Kurulu",
      ad_soyad: "Deneme Üye",
      durum: "PAROLA_YENILENMELI",
      durum_etiketi: "Parola yenilenmeli",
    });
    apiMock.secenekler.mockResolvedValue({
      roller: [
        {
          rol: "denetleme_kurulu",
          rol_etiketi: "Denetleme Kurulu",
          acilabilir: true,
          neden: null,
          varsayilan_tanitici: "dk-2",
          bilgi: null,
        },
      ],
    });
    apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", ileti));
    bas();
    await tablo();
    // Liste: ilk okuma ve gönderimden önceki kimlikler LISTE; retten sonra yeni hesapla.
    apiMock.liste.mockResolvedValueOnce(LISTE).mockResolvedValue([...LISTE, yeni]);
    await user.click(screen.getByRole("button", { name: "Yeni hesap" }));
    const p = await screen.findByRole("dialog", { name: "Yeni hesap" });
    await user.selectOptions(await within(p).findByLabelText(/^Rol/), "denetleme_kurulu");
    await user.type(within(p).getByLabelText(/^Ad-soyad/), "Deneme Üye");
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    expect(await within(p).findByText(ileti)).toHaveFocus();

    await user.click(within(p).getByRole("button", { name: "Parolayı sıfırla" }));
    const form = await screen.findByRole("dialog", { name: "Parolayı sıfırla" });
    expect(screen.queryByRole("dialog", { name: "Yeni hesap" })).toBeNull();
    expect(form).toHaveTextContent("Hesap: Denetleme Kurulu · tanıtıcı dk-2");
  });
});

describe("Kullanıcılar — geçici parola panoya gitmez", () => {
  it("modülün kaynağında pano kullanımı yok (adı ne olursa olsun kopyalama düğmesi yok)", () => {
    // Plan F1b-2 "Geçici parola": kopyalama düğmesi yoktur. Düğme testleri yalnız çizilen
    // düğmeleri sayar; pano kaynakta hiç geçmemelidir (tıklanmayan ya da kendiliğinden kopyalama).
    const kaynaklar = import.meta.glob<string>("./*.{ts,tsx}", {
      query: "?raw",
      import: "default",
      eager: true,
    });
    const ekran = Object.entries(kaynaklar).filter(([yol]) => !yol.includes(".test."));
    expect(ekran.map(([yol]) => yol)).toEqual(
      expect.arrayContaining(["./GeciciParolaAlani.tsx", "./YeniHesapPenceresi.tsx"]),
    );
    for (const [yol, kaynak] of ekran) {
      expect(kaynak, yol).not.toMatch(/clipboard|execCommand\s*\(\s*["']copy/i);
    }
  });
});
