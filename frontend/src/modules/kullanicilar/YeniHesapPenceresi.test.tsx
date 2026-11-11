// "Yeni hesap" penceresi (plan F1b-2 "Kullanıcılar uçları", "Geçici parola", "Kendi hesabı ve ikinci
// program yöneticisi"): rol seçenekleri ve açılamama nedenleri sunucudan; tanıtıcının varsayılanı
// sunucudan; ön denetim sunucunun iletileriyle alanların altında; kişisel veri uyarısı gönderimden
// önce; geçici parola programın önerisiyle dolu (her açılışta yeni), kopyalama düğmesi yok, sonuçta
// gösterilmez; sonuçta sunucunun uyarısı, bilgisi ve hesap teslim pusulası, odak sonucun başlığında;
// hesap açıldığı hâlde parola kaydı yazılamadıysa (yarım açılış) form kapanır, yeniden açma
// önerilmez, çıkış "Parolayı sıfırla"; organ rolünde üyelik seçimi (plan F1c 7. adım; ekranı 11. adımda):
// seçilmeden gitmez, seçilen üyenin adı boş ad-soyada konur, gövde üyeliği ve kişisini taşır, açılabilecek
// üye yoksa sunucunun nedeni ve Organlar bağlantısı. Veriler uydurmadır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { KENDI_HESABI, ROL_SECENEKLERI, hesapSatiri } from "../../test/kullanicilar";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import {
  AD_SOYAD_BOS_ILETISI,
  TANITICI_GECERSIZ_ILETISI,
  TANITICI_TCKN_UYARISI,
  TANITICI_UYARISI,
} from "../oturum/hesapKurallari";
import { parolaSorunu } from "../oturum/parolaPolitikasi";
import { DUGME_PUSULA } from "./metinler";

const apiMock = vi.hoisted(() => ({
  liste: vi.fn(),
  secenekler: vi.fn(),
  ac: vi.fn(),
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

import YeniHesapPenceresi from "./YeniHesapPenceresi";

const BASKAN = hesapSatiri({
  id: "3c2b1a0f-9e8d-4c7b-8a6f-5e4d3c2b1a0f",
  tanitici: "baskan",
  rol: "baskan",
  rol_etiketi: "Başkan",
  ad_soyad: "Deneme Başkan",
  durum: "PAROLA_YENILENMELI",
  durum_etiketi: "Parola yenilenmeli",
});

function bas() {
  const onClose = vi.fn();
  const onDegisti = vi.fn();
  const onSifirla = vi.fn();
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const { unmount } = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SnackbarProvider>
          <YeniHesapPenceresi onClose={onClose} onDegisti={onDegisti} onSifirla={onSifirla} />
        </SnackbarProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { onClose, onDegisti, onSifirla, unmount };
}

async function pencere(): Promise<HTMLElement> {
  const p = await screen.findByRole("dialog", { name: "Yeni hesap" });
  await within(p).findByLabelText(/^Rol/);
  return p;
}

const alan = (p: HTMLElement, ad: RegExp) => within(p).getByLabelText(ad) as HTMLInputElement;

beforeEach(() => {
  vi.clearAllMocks();
  // Gerçek `saveBlob` hep sonuç döndürür: sahte `undefined` dönseydi başarı dalı sınanmazdı.
  indirme.saveBlob.mockResolvedValue("kaydedildi");
  apiMock.secenekler.mockResolvedValue({ roller: ROL_SECENEKLERI });
  apiMock.liste.mockResolvedValue([KENDI_HESABI]);
});

describe("Yeni hesap — form", () => {
  it("rol seçenekleri sunucudan (sıra no'suz); seçilen rolün varsayılan tanıtıcısı gelir", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    const rol = alan(p, /^Rol/);
    expect(
      within(rol)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Seçin", "Program yöneticisi", "Başkan", "Muhasip", "Denetleme Kurulu"]);

    await user.selectOptions(rol, "denetleme_kurulu");
    expect(alan(p, /^Tanıtıcı/).value).toBe("dk-1");
    await user.selectOptions(rol, "baskan");
    expect(alan(p, /^Tanıtıcı/).value).toBe("baskan");

    // Elle değiştirilen tanıtıcıyı rol değişimi ezmez.
    await user.clear(alan(p, /^Tanıtıcı/));
    await user.type(alan(p, /^Tanıtıcı/), "uye.baskan");
    await user.selectOptions(rol, "denetleme_kurulu");
    expect(alan(p, /^Tanıtıcı/).value).toBe("uye.baskan");
  });

  it("açılamayan rolde sunucunun nedeni alanın altında, gönderim kapalı", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.selectOptions(alan(p, /^Rol/), "muhasip");
    expect(
      within(p).getByText("Bu rolde açık bir hesap zaten var; önce onu kapatın."),
    ).toBeVisible();
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeDisabled();
  });

  it("program yöneticisi rolünde sunucunun bilgisi (anahtar yenilemesi sonraki sürümde)", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.selectOptions(alan(p, /^Rol/), "yonetici");
    expect(within(p).getByText(/sonraki bir sürümünde gelecek/)).toBeVisible();
    expect(alan(p, /^Tanıtıcı/).value).toBe("yonetici-2");
  });

  it("geçici parola önerisi dolu, politikaya uyar; kopyalama düğmesi yok; zarf notu var", async () => {
    const guvenli = vi.spyOn(globalThis.crypto, "getRandomValues");
    bas();
    const p = await pencere();
    const parola = alan(p, /^Geçici parola/);
    expect(parola.type).toBe("text");
    expect(parolaSorunu(parola.value)).toBeNull();
    expect([...parola.value]).toHaveLength(12);
    // Öneri pencere açılırken güvenli kaynaktan kurulur (modül yüklenirken bir kez değil).
    expect(guvenli).toHaveBeenCalled();
    guvenli.mockRestore();
    // Pencerenin düğmeleri tam olarak bunlardır: adı ne olursa olsun kopyalama düğmesi yok.
    expect(within(p).getAllByRole("button")).toHaveLength(3);
    for (const ad of ["Yeni öneri", "Vazgeç", "Hesabı aç"]) {
      expect(within(p).getByRole("button", { name: ad })).toBeInTheDocument();
    }
    expect(within(p).getByRole("note")).toHaveTextContent(
      "Bilgi ve Sistem Güvenliği Yönergesi 10/1",
    );
  });

  it("her açılış yeni öneri verir; “Yeni öneri” alanın değerini değiştirir", async () => {
    const user = userEvent.setup();
    const { unmount } = bas();
    const birinci = alan(await pencere(), /^Geçici parola/).value;
    unmount();
    bas();
    const p = await pencere();
    const parola = alan(p, /^Geçici parola/);
    const ikinci = parola.value;
    expect(ikinci).not.toBe(birinci);

    await user.click(within(p).getByRole("button", { name: "Yeni öneri" }));
    const ucuncu = parola.value;
    expect(ucuncu).not.toBe(ikinci);
    expect(parolaSorunu(ucuncu)).toBeNull();
    expect([...ucuncu]).toHaveLength(12);
    // Her basış yeni bir öneridir (sabit bir değer yazılmaz).
    await user.click(within(p).getByRole("button", { name: "Yeni öneri" }));
    expect(parola.value).not.toBe(ucuncu);
  });

  it("ön denetim sunucunun iletileriyle her alanın altında; istek gitmez", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.clear(alan(p, /^Geçici parola/));
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));

    expect(within(p).getByText("Geçerli bir rol seçin.")).toBeVisible();
    expect(within(p).getByText("Tanıtıcı boş olamaz.")).toBeVisible();
    expect(within(p).getByText(AD_SOYAD_BOS_ILETISI)).toBeVisible();
    expect(within(p).getByText("Parola en az 8 karakter olmalıdır.")).toBeVisible();
    expect(apiMock.ac).not.toHaveBeenCalled();

    await user.selectOptions(alan(p, /^Rol/), "baskan");
    await user.clear(alan(p, /^Tanıtıcı/));
    await user.type(alan(p, /^Tanıtıcı/), "1abc");
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    expect(within(p).getByText(TANITICI_GECERSIZ_ILETISI)).toBeVisible();
    expect(alan(p, /^Tanıtıcı/)).toHaveFocus();
    expect(apiMock.ac).not.toHaveBeenCalled();
  });

  it("tanıtıcının kişisel veri uyarısı gönderimden önce görünür (11 rakam; ad-soyad)", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.type(alan(p, /^Tanıtıcı/), "kayit-12345678901");
    expect(within(p).getByText(TANITICI_TCKN_UYARISI)).toBeVisible();

    await user.clear(alan(p, /^Tanıtıcı/));
    await user.type(alan(p, /^Tanıtıcı/), "ayse.k");
    await user.type(alan(p, /^Ad-soyad/), "Ayşe Kaya");
    expect(within(p).getByText(TANITICI_UYARISI)).toBeVisible();
  });
});

describe("Yeni hesap — gönderim", () => {
  async function doldurVeGonder(user: ReturnType<typeof userEvent.setup>, p: HTMLElement) {
    await user.selectOptions(alan(p, /^Rol/), "baskan");
    await user.clear(alan(p, /^Tanıtıcı/));
    await user.type(alan(p, /^Tanıtıcı/), "  BASKAN ");
    await user.type(alan(p, /^Ad-soyad/), "  Deneme   Başkan ");
    const parola = alan(p, /^Geçici parola/).value;
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    return parola;
  }

  it("normalleştirilmiş gövde gider; sonuçta geçici parola yok, uyarı ve pusula var", async () => {
    const user = userEvent.setup();
    const uyari = "Tanıtıcı hesap sahibinin adını içeriyor. Tanıtıcı kilit ekranında …";
    apiMock.ac.mockResolvedValue({ hesap: BASKAN, uyari, bilgi: null });
    const pdf = new Blob(["%PDF"]);
    apiMock.pusula.mockResolvedValue({
      blob: pdf,
      ad: "Hesap-Teslim-Pusulası_Başkan_04.11.2026.pdf",
    });
    const { onClose, onDegisti } = bas();
    const p = await pencere();
    const parola = await doldurVeGonder(user, p);

    expect(apiMock.ac).toHaveBeenCalledWith({
      rol: "baskan",
      tanitici: "baskan",
      ad_soyad: "Deneme Başkan",
      gecici_parola: parola,
    });
    expect(await within(p).findByText("Hesap açıldı.")).toBeVisible();
    // Form sökülünce odak sonucun başlığındadır (<body>'ye düşmez; ekran okuyucu sonucu okur).
    expect(within(p).getByText("Hesap açıldı.")).toHaveFocus();
    expect(within(p).getByText("Başkan · tanıtıcı baskan")).toBeVisible();
    expect(within(p).getByText(uyari)).toBeVisible();
    expect(within(p).getByText(/kapalı zarfta hesap sahibine verin/)).toBeVisible();
    // Geçici parola sonuç görünümünde hiçbir biçimde yok.
    expect(p.textContent).not.toContain(parola);
    expect(screen.queryByDisplayValue(parola)).toBeNull();
    expect(onDegisti).toHaveBeenCalled();

    await user.click(within(p).getByRole("button", { name: "Hesap teslim pusulasını kaydet" }));
    expect(apiMock.pusula).toHaveBeenCalledWith(BASKAN.id);
    await waitFor(() =>
      expect(indirme.saveBlob).toHaveBeenCalledWith(
        pdf,
        "Hesap-Teslim-Pusulası_Başkan_04.11.2026.pdf",
      ),
    );
    expect(await screen.findByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeVisible();
    await user.click(within(p).getByRole("button", { name: "Kapat" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("sonuçta köprü yoksa dosya tarayıcıya verilir, bildirim yine çıkar", async () => {
    const user = userEvent.setup();
    apiMock.ac.mockResolvedValue({ hesap: BASKAN, uyari: null, bilgi: null });
    apiMock.pusula.mockResolvedValue({ blob: new Blob(["%PDF"]), ad: "pusula.pdf" });
    indirme.saveBlob.mockResolvedValueOnce("indirildi");
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    await within(p).findByText("Hesap açıldı.");

    await user.click(within(p).getByRole("button", { name: DUGME_PUSULA }));

    expect(await screen.findByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeVisible();
  });

  it("sonuçta pusula kaydında iptal sessizdir, yazılamazsa pencerede tek ileti çıkar", async () => {
    const user = userEvent.setup();
    apiMock.ac.mockResolvedValue({ hesap: BASKAN, uyari: null, bilgi: null });
    apiMock.pusula.mockResolvedValue({ blob: new Blob(["%PDF"]), ad: "pusula.pdf" });
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    await within(p).findByText("Hesap açıldı.");
    const dugme = within(p).getByRole("button", { name: DUGME_PUSULA });

    indirme.saveBlob.mockResolvedValueOnce("iptal");
    await user.click(dugme);
    await waitFor(() => expect(indirme.saveBlob).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(within(p).getByRole("button", { name: DUGME_PUSULA })).toBeEnabled(),
    );
    expect(screen.queryByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeNull();
    expect(within(p).queryByText(DOSYA_YAZILAMADI_ILETISI)).toBeNull();

    indirme.saveBlob.mockResolvedValueOnce("hata");
    await user.click(within(p).getByRole("button", { name: DUGME_PUSULA }));
    expect(await within(p).findByText(DOSYA_YAZILAMADI_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText("Hesap teslim pusulası PDF olarak kaydedildi.")).toBeNull();
  });

  it("sonuçta pusula basılamıyorsa sunucunun nedeni; ikinci program yöneticisinin bilgisi", async () => {
    const user = userEvent.setup();
    const neden = "Hesap kapalı; kapalı hesap yeniden açılmaz, yeni hesap açılır.";
    const bilgi = ROL_SECENEKLERI[0].bilgi;
    apiMock.ac.mockResolvedValue({
      hesap: hesapSatiri({
        ...BASKAN,
        eylemler: { ...BASKAN.eylemler, pusula: { yapilabilir: false, neden } },
      }),
      uyari: null,
      bilgi,
    });
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    const dugme = await within(p).findByRole("button", { name: "Hesap teslim pusulasını kaydet" });
    expect(dugme).toBeDisabled();
    expect(dugme).toHaveAccessibleDescription(neden);
    expect(within(p).getByText(bilgi as string)).toBeVisible();
  });

  it("pusulanın reddi sonuç görünümünde", async () => {
    const user = userEvent.setup();
    apiMock.ac.mockResolvedValue({ hesap: BASKAN, uyari: null, bilgi: null });
    apiMock.pusula.mockRejectedValue(new TypeError("ağ yok"));
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    await user.click(
      await within(p).findByRole("button", { name: "Hesap teslim pusulasını kaydet" }),
    );
    expect(await within(p).findByText("Hesap teslim pusulası hazırlanamadı.")).toBeVisible();
  });

  it("servis reddi pencerenin genel iletisi; form kalır, liste yine yeniden okunur", async () => {
    // Tanıtıcısı alınmış rol: o tanıtıcılı açık hesap listede ama gönderimden ÖNCE de vardı —
    // hesabı bu deneme açmadı (yarım açılış değil).
    const user = userEvent.setup();
    const ileti = "Bu tanıtıcı açık bir başka hesapta kullanılıyor.";
    apiMock.liste.mockResolvedValue([KENDI_HESABI, BASKAN]);
    apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", ileti));
    const { onDegisti } = bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    expect(await within(p).findByRole("alert")).toHaveTextContent(ileti);
    expect(onDegisti).toHaveBeenCalled();
    expect(within(p).queryByText("Hesap açıldı.")).toBeNull();
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeEnabled();
    expect(apiMock.liste).toHaveBeenCalledTimes(2);
  });

  it.each([
    [
      409,
      "iz_yazilamadi",
      "Denetim izine yazılamadığı için işlem yapılmadı. Denetim izi program dışından değiştirilmiş " +
        "olabilir; program yöneticisine ve Denetleme Kuruluna bildirin.",
    ],
    [
      409,
      "hesap_muhru_tutmadi",
      "Hesap kaydı program dışından değiştirilmiş görünüyor; kayda dokunulmadı. Denetleme " +
        "Kuruluna bildirin.",
    ],
    [403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."],
  ])("%i %s: sunucunun iletisi pencerede", async (status, kod, ileti) => {
    const user = userEvent.setup();
    apiMock.ac.mockRejectedValue(new ApiError(status, kod, ileti));
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    expect(await within(p).findByRole("alert")).toHaveTextContent(ileti);
  });

  it("sunucunun alan hatası alanının altında; genel ileti çıkmaz", async () => {
    const user = userEvent.setup();
    apiMock.ac.mockRejectedValue(
      new ApiError(400, "validation_error", "Gönderilen veride hatalar var.", {
        tanitici: ["Bu tanıtıcı açık bir başka hesapta kullanılıyor."],
      }),
    );
    bas();
    const p = await pencere();
    await doldurVeGonder(user, p);
    expect(
      await within(p).findByText("Bu tanıtıcı açık bir başka hesapta kullanılıyor."),
    ).toBeVisible();
    expect(alan(p, /^Tanıtıcı/)).toHaveAttribute("aria-invalid", "true");
    expect(within(p).queryByText("Gönderilen veride hatalar var.")).toBeNull();
  });

  it("seçenekler okunamazsa ileti ve Vazgeç", async () => {
    const user = userEvent.setup();
    apiMock.secenekler.mockRejectedValue(new TypeError("ağ yok"));
    const { onClose } = bas();
    const p = await screen.findByRole("dialog", { name: "Yeni hesap" });
    expect(await within(p).findByText("Rol seçenekleri okunamadı.")).toBeVisible();
    await user.click(within(p).getByRole("button", { name: "Vazgeç" }));
    expect(onClose).toHaveBeenCalled();
  });
});

describe("Yeni hesap — hesap açıldı, parola kaydı yazılamadı", () => {
  const OPEN_WRAP =
    "Hesap açıldı, ancak parola kaydı güvenlik dosyasına yazılamadı (ör. dosyayı başka bir " +
    "program tutuyor); hesabın parolasını sıfırlayın.";
  const SARMALSIZ = "Parola kaydı bu bilgisayarın güvenlik dosyasında yok; parolasını sıfırlayın.";

  /** Sunucunun açtığı, parola kaydı olmayan yeni hesap (kimlik gönderimden önce listede yok). */
  function yeniSatir(rol: string, rolEtiketi: string, tanitici: string) {
    return hesapSatiri({
      id: "8d7c6b5a-4f3e-4d2c-8b1a-0f9e8d7c6b5a",
      tanitici,
      rol,
      rol_etiketi: rolEtiketi,
      ad_soyad: "Deneme Üye",
      durum: "PAROLA_YENILENMELI",
      durum_etiketi: "Parola yenilenmeli",
      son_giris: null,
      giris: { yapabilir: false, neden: SARMALSIZ },
    });
  }

  async function gonder(user: ReturnType<typeof userEvent.setup>, p: HTMLElement, rol: string) {
    await user.selectOptions(alan(p, /^Rol/), rol);
    await user.type(alan(p, /^Ad-soyad/), "Deneme Üye");
    const parola = alan(p, /^Geçici parola/).value;
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    return parola;
  }

  it.each([
    ["denetleme_kurulu", "Denetleme Kurulu", "dk-1"],
    ["yonetici", "Program yöneticisi", "yonetici-2"],
  ])(
    "%s: form kapanır, ileti hesabın adıyla, geçici parola yok; çıkış “Parolayı sıfırla”",
    async (rol, rolEtiketi, tanitici) => {
      const user = userEvent.setup();
      const yeni = yeniSatir(rol, rolEtiketi, tanitici);
      apiMock.liste.mockResolvedValueOnce([KENDI_HESABI]).mockResolvedValue([KENDI_HESABI, yeni]);
      apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", OPEN_WRAP));
      const { onClose, onDegisti, onSifirla } = bas();
      const p = await pencere();
      const parola = await gonder(user, p, rol);

      const ileti = await within(p).findByText(OPEN_WRAP);
      // Odak iletidedir (form söküldü; odak <body>'ye düşmez).
      expect(ileti).toHaveFocus();
      expect(within(p).getByRole("alert")).toHaveTextContent(OPEN_WRAP);
      expect(within(p).getByText(`${rolEtiketi} · tanıtıcı ${tanitici}`)).toBeVisible();
      expect(within(p).getByText(/kâğıda yazdıysanız o kâğıdı vermeyin/)).toBeVisible();
      // Form yok: rol yeniden seçilip ikinci hesap açılamaz; geçici parola hiçbir yerde yok.
      expect(within(p).queryByRole("button", { name: "Hesabı aç" })).toBeNull();
      expect(within(p).queryByRole("combobox")).toBeNull();
      expect(within(p).queryByRole("textbox")).toBeNull();
      expect(p.textContent).not.toContain(parola);
      expect(screen.queryByDisplayValue(parola)).toBeNull();
      expect(within(p).queryByText(/Bilgi ve Sistem Güvenliği Yönergesi/)).toBeNull();
      expect(within(p).queryByRole("button", { name: DUGME_PUSULA })).toBeNull();
      expect(within(p).getAllByRole("button")).toHaveLength(2);
      expect(apiMock.ac).toHaveBeenCalledTimes(1);
      expect(onDegisti).toHaveBeenCalled();

      await user.click(within(p).getByRole("button", { name: "Parolayı sıfırla" }));
      expect(onSifirla).toHaveBeenCalledWith(yeni);
      await user.click(within(p).getByRole("button", { name: "Kapat" }));
      expect(onClose).toHaveBeenCalled();
    },
  );

  it("sıfırlama yapılamıyorsa sunucunun nedeni düğmenin yanında", async () => {
    const user = userEvent.setup();
    const neden = "Askıdaki hesabın parolası sıfırlanamaz; önce hesabı askıdan çıkarın.";
    const yeni = hesapSatiri({
      ...yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-1"),
      eylemler: {
        ...yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-1").eylemler,
        parola_sifirla: { yapilabilir: false, neden },
      },
    });
    apiMock.liste.mockResolvedValueOnce([KENDI_HESABI]).mockResolvedValue([KENDI_HESABI, yeni]);
    apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", OPEN_WRAP));
    bas();
    const p = await pencere();
    await gonder(user, p, "denetleme_kurulu");
    const dugme = await within(p).findByRole("button", { name: "Parolayı sıfırla" });
    expect(dugme).toBeDisabled();
    expect(dugme).toHaveAccessibleDescription(neden);
  });

  it.each([
    [
      "yeni hesap başka rol ve tanıtıcıda",
      () => [KENDI_HESABI, yeniSatir("baskan", "Başkan", "baskan")],
    ],
    // Yüklemin iki koşulu ayrı ayrı (son sınama): yalnız biri tutan satır da sayılmaz.
    [
      "yeni hesap aynı tanıtıcıda, başka rolde",
      () => [KENDI_HESABI, yeniSatir("baskan", "Başkan", "dk-1")],
    ],
    [
      "yeni hesap aynı rolde, başka tanıtıcıda",
      () => [KENDI_HESABI, yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-2")],
    ],
    [
      "yeni hesap kapalı",
      () => [
        KENDI_HESABI,
        hesapSatiri({
          ...yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-1"),
          durum: "KAPALI",
          durum_etiketi: "Kapalı",
        }),
      ],
    ],
  ])("%s: yarım açılış sayılmaz, ileti genel iletidir ve form kalır", async (_ad, sonraki) => {
    const user = userEvent.setup();
    apiMock.liste.mockResolvedValueOnce([KENDI_HESABI]).mockResolvedValue(sonraki());
    apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", OPEN_WRAP));
    bas();
    const p = await pencere();
    await gonder(user, p, "denetleme_kurulu");
    expect(await within(p).findByRole("alert")).toHaveTextContent(OPEN_WRAP);
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeInTheDocument();
    expect(within(p).queryByRole("button", { name: "Parolayı sıfırla" })).toBeNull();
  });

  it("gönderimden önceki liste okunamazsa yarım açılış sezilmez: ileti genel iletidir", async () => {
    const user = userEvent.setup();
    const yeni = yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-1");
    apiMock.liste
      .mockRejectedValueOnce(new TypeError("ağ yok"))
      .mockResolvedValue([KENDI_HESABI, yeni]);
    apiMock.ac.mockRejectedValue(new ApiError(400, "validation_error", OPEN_WRAP));
    bas();
    const p = await pencere();
    await gonder(user, p, "denetleme_kurulu");
    expect(await within(p).findByRole("alert")).toHaveTextContent(OPEN_WRAP);
    expect(within(p).queryByRole("button", { name: "Parolayı sıfırla" })).toBeNull();
    // Gönderim yine yapılır (liste okunamadı diye hesap açma engellenmez).
    expect(apiMock.ac).toHaveBeenCalledTimes(1);
  });

  it("409 retten sonra liste karşılaştırılmaz (hesap açılmamıştır)", async () => {
    const user = userEvent.setup();
    const ileti =
      "Denetim izine yazılamadığı için işlem yapılmadı. Denetim izi program dışından değiştirilmiş " +
      "olabilir; program yöneticisine ve Denetleme Kuruluna bildirin.";
    apiMock.liste
      .mockResolvedValueOnce([KENDI_HESABI])
      .mockResolvedValue([KENDI_HESABI, yeniSatir("denetleme_kurulu", "Denetleme Kurulu", "dk-1")]);
    apiMock.ac.mockRejectedValue(new ApiError(409, "iz_yazilamadi", ileti));
    bas();
    const p = await pencere();
    await gonder(user, p, "denetleme_kurulu");
    expect(await within(p).findByRole("alert")).toHaveTextContent(ileti);
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeInTheDocument();
  });
});

describe("Yeni hesap — organ rolünde üyelik", () => {
  const BAG_YOK =
    "Bu role hesap açılabilecek üye yok; açık birlik döneminde üyeliği, yönetim kurulu rollerinde " +
    "görev bölümünü de girin.";
  const TEK_HESAP = "Bu rolde açık bir hesap zaten var; önce onu kapatın.";

  beforeEach(() => {
    apiMock.secenekler.mockResolvedValue({
      roller: ROL_SECENEKLERI.map((r) =>
        r.rol === "baskan"
          ? {
              ...r,
              uyelik_gerekli: true,
              uyelikler: [
                {
                  uyelik: 11,
                  kisi: 7,
                  ad_soyad: "Uydurnur Örnekkaya",
                  organ: "YK",
                  gorev: "BASKAN",
                  gorev_etiketi: "Başkan",
                  donem: 3,
                },
                {
                  uyelik: 12,
                  kisi: 8,
                  ad_soyad: null,
                  organ: "YK",
                  gorev: "BASKAN",
                  gorev_etiketi: "Başkan",
                  donem: 3,
                },
              ],
            }
          : r.rol === "denetleme_kurulu"
            ? {
                ...r,
                acilabilir: false,
                neden: BAG_YOK,
                uyelik_gerekli: true,
                uyelikler: [],
                organlara_yonlendir: true,
              }
            : r.rol === "muhasip"
              ? {
                  ...r,
                  acilabilir: false,
                  neden: TEK_HESAP,
                  uyelik_gerekli: true,
                  uyelikler: [],
                  organlara_yonlendir: false,
                }
              : r,
      ),
    });
  });

  it("üyelik seçilmeden gitmez; seçilen üyenin adı boş ad-soyada konur; gövde üyeliği taşır", async () => {
    const user = userEvent.setup();
    apiMock.ac.mockResolvedValue({ hesap: BASKAN, uyari: null, bilgi: null });
    bas();
    const p = await pencere();
    await user.selectOptions(alan(p, /^Rol/), "baskan");
    const uyelik = alan(p, /^Üyelik/);
    expect(
      within(uyelik)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Seçin", "Uydurnur Örnekkaya · Başkan", "Adı okunamadı · Başkan"]);
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    expect(within(p).getByText("Üyeliği seçin.")).toBeVisible();
    expect(apiMock.ac).not.toHaveBeenCalled();
    await user.selectOptions(uyelik, "11");
    expect(alan(p, /^Ad-soyad/).value).toBe("Uydurnur Örnekkaya");
    const parola = alan(p, /^Geçici parola/).value;
    await user.click(within(p).getByRole("button", { name: "Hesabı aç" }));
    expect(apiMock.ac).toHaveBeenCalledWith({
      rol: "baskan",
      tanitici: "baskan",
      ad_soyad: "Uydurnur Örnekkaya",
      gecici_parola: parola,
      uyelik: 11,
      kisi: 7,
    });
  });

  it("açılabilecek üye yoksa neden ve Organlar bağlantısı; seçim yok", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.selectOptions(alan(p, /^Rol/), "denetleme_kurulu");
    expect(within(p).getByText(BAG_YOK)).toBeVisible();
    expect(within(p).getByRole("link", { name: "Organlar ekranını aç" })).toHaveAttribute(
      "href",
      "/organlar",
    );
    expect(within(p).queryByLabelText(/^Üyelik/)).toBeNull();
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeDisabled();
  });

  it("sınır engelinde neden görünür, Organlar bağlantısı çıkmaz", async () => {
    const user = userEvent.setup();
    bas();
    const p = await pencere();
    await user.selectOptions(alan(p, /^Rol/), "muhasip");
    expect(within(p).getByText(TEK_HESAP)).toBeVisible();
    expect(within(p).queryByRole("link", { name: "Organlar ekranını aç" })).toBeNull();
    expect(within(p).getByRole("button", { name: "Hesabı aç" })).toBeDisabled();
  });
});
