// Aç penceresiyle seçilen yedek (kullanıcı kararları 06.11.2026 "Yedek dosyası yüklenmez, programın
// Aç penceresiyle seçilir", "Elden seçilen yedeğin başlığını sunucu okur"). Köprü varsa kart dosya
// kutusu yerine düğme gösterir, köprü yoksa kutu kalır. Yol yalnız bileşenin durumunda ve istek
// gövdesinde durur: ekranda yalnız dosyanın adı görünür, yol konsola, hata iletisine ve tarayıcı
// deposuna girmez, kart sökülünce gider. İptalde önceki kaynak aynen kalır, pencere açıkken düğme
// kapalıdır. Seçilen yolun başlığı `POST backups/inspect/` ile okunur, satır, anahtar cümlesi ve onay
// listedekiyle aynıdır; eski yanıt yeni seçimi ezmez; istek düşerse kapsam yazılmaz, geri yükleme
// engellenmez, ad yoldan türetilir. İkinci onay aynı yolla ve aynı sırla gider. Sahteler uç
// sözleşmesiyle aynıdır (`views.BackupInspectView`, `live_restore._yedek_satiri`,
// `views.BackupRestoreView`). Boşta sayaçla ilişkisi `YedektenGeriYukleme.etkinlik.test.tsx`'tedir.

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { YENIDEN_BASLAT_OLAYI } from "../../lib/restart";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";

const guvenlik = vi.hoisted(() => ({
  yedekler: vi.fn(),
  yedekBasligi: vi.fn(),
  geriYukle: vi.fn(),
}));

vi.mock("./api", () => ({ guvenlikApi: guvenlik }));

import YedektenGeriYukleme from "./YedektenGeriYukleme";
import { yedekIsleriniSifirla } from "./yedekIsleri";

const LISTE = {
  backup_dir: "C:\\OABDefteri\\backups",
  backups: [
    {
      name: "gunluk-2026-09-01.odbak",
      size: 2 * 1024 * 1024,
      modified_at: "2026-09-01T08:00:00+03:00",
      kurtarma: { no: 2, tarih: "2026-08-31" },
      kapsam: "yerel",
    },
  ],
};

const WINDOWS_YOLU = "E:\\Okul Yedekleri\\Şubat ayı ğüşıöç.odbak";
const WINDOWS_ADI = "Şubat ayı ğüşıöç.odbak";
const PARDUS_YOLU = "/media/öğretmen/USB BELLEK/günlük yedek.odbak";
const PARDUS_ADI = "günlük yedek.odbak";
/** Yolun dosya adında olmayan parçası: ekrana düşerse testler bunu yakalar. */
const YOLUN_KLASORU = "Okul Yedekleri";

/** `POST backups/inspect/` yanıtı: listenin satırı. */
function satir(ad: string, degisim: Record<string, unknown> = {}) {
  return {
    name: ad,
    size: 45987,
    modified_at: "2026-11-06T17:55:12.643259+03:00",
    kurtarma: { no: 1, tarih: "2026-11-06" },
    kapsam: "tam",
    ...degisim,
  };
}

const DOSYA_RAPORU = {
  kapsam: "tam",
  yerine_konan: 2,
  yetimden_donen: 0,
  eksik: 0,
  bozuk: 0,
  onayla_suruldu: 0,
  ekler: [],
};

const SONUC = {
  old_db_name: "db-onceki-2026-11-06-101010.sqlite3",
  state_written: false,
  restart_required: true,
  dosya_raporu: DOSYA_RAPORU,
};

const DURMA_ILETISI =
  "1 ek yedek alınırkenki hâlini tutmuyor; geri yükleme yapılmadı. Onaylarsanız kayıtlar bu ekler " +
  "olmadan geri yüklenir.";
const YOL_ACILAMADI =
  "Seçilen yedek dosyası açılamadı; dosyanın yerinde ve okunabilir olduğundan emin olun.";

/** Bozuk ekte durma: 409 gövdesiyle aynı. */
function ekOnayiReddi() {
  const rapor = {
    ...DOSYA_RAPORU,
    bozuk: 1,
    ekler: [
      {
        durum: "bozuk",
        kayit_turu: "ders yılı",
        kayit_no: "7",
        yukleme_tarihi: "2026-10-01",
        boyut: 4096,
        yedekte_yoktu: false,
      },
    ],
  };
  const govde = { code: "ek_onayi_gerekli", message: DURMA_ILETISI, fields: {}, rapor };
  return new ApiError(409, govde.code, govde.message, govde.fields, govde);
}

const PAROLA = "Deneme-Parola-1";
const koprudenSor = vi.fn<() => Promise<string>>();

function kopruyuKur() {
  window.pywebview = { api: { yedek_dosyasi_sor: koprudenSor } };
}

function bas(kayipKipi = false) {
  return render(
    <SnackbarProvider>
      <ConfirmProvider>
        <YedektenGeriYukleme kayipKipi={kayipKipi} />
      </ConfirmProvider>
    </SnackbarProvider>,
  );
}

/** Ayarlar sekmesi gibi: sağlayıcılar kökte kalır, kart sökülüp yeniden takılır. */
function sokulebilirBas() {
  const agac = (takili: boolean) => (
    <SnackbarProvider>
      <ConfirmProvider>{takili && <YedektenGeriYukleme />}</ConfirmProvider>
    </SnackbarProvider>
  );
  const { rerender } = render(agac(true));
  return { sok: () => rerender(agac(false)), tak: () => rerender(agac(true)) };
}

type Kullanici = ReturnType<typeof userEvent.setup>;

const secmeDugmesi = () => screen.findByRole("button", { name: "Yedek dosyası seç" });
const geriYukleDugmesi = () => screen.getByRole("button", { name: "Geri yükle" });

/** Aç penceresinde `yol` seçilir; yanıtı testte bekletilebilir. */
async function dosyaSec(kullanici: Kullanici, yol: string) {
  koprudenSor.mockResolvedValueOnce(yol);
  await kullanici.click(await secmeDugmesi());
}

/** Yanıtı testin elinde duran başlık isteği (bir kez). */
function bekletilenBaslik() {
  let coz: (ozet: unknown) => void = () => undefined;
  let reddet: (hata: unknown) => void = () => undefined;
  guvenlik.yedekBasligi.mockImplementationOnce(
    () =>
      new Promise((c, r) => {
        coz = c;
        reddet = r;
      }),
  );
  return {
    bitir: (ozet: unknown) =>
      act(async () => {
        coz(ozet);
        await Promise.resolve();
      }),
    dus: (hata: unknown) =>
      act(async () => {
        reddet(hata);
        await Promise.resolve();
      }),
  };
}

/** Parolayı yazar, "Geri yükle"ye basar; açılan onay diyaloğunu döndürür. */
async function onayaGel(kullanici: Kullanici) {
  await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
  await kullanici.click(geriYukleDugmesi());
  return screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
}

async function onayla(kullanici: Kullanici) {
  const diyalog = await onayaGel(kullanici);
  await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));
}

function gidenForm(sira = 0) {
  return guvenlik.geriYukle.mock.calls[sira][0] as FormData;
}

beforeEach(() => {
  yedekIsleriniSifirla();
  vi.resetAllMocks();
  guvenlik.yedekler.mockResolvedValue(LISTE);
  guvenlik.yedekBasligi.mockResolvedValue(satir(WINDOWS_ADI));
  kopruyuKur();
});
afterEach(() => {
  delete window.pywebview;
  vi.restoreAllMocks();
});

describe("kaynak seçimi", () => {
  it("köprü varsa kutu yerine düğme gösterir; metin dosya yükletmez", async () => {
    const { container } = bas();

    expect(await secmeDugmesi()).toBeEnabled();
    expect(screen.getByText("Ya da elinizdeki yedek dosyası")).toBeInTheDocument();
    expect(container.querySelector('input[type="file"]')).toBeNull();
    expect(container.textContent).toContain("elinizdeki yedek dosyasını seçin");
    expect(container.textContent).not.toMatch(/yükleyin\.|yükleyebilirsiniz/);
  });

  it("yedek klasörü boşken de metin dosyanın seçileceğini söyler", async () => {
    guvenlik.yedekler.mockResolvedValue({ backup_dir: "C:\\x", backups: [] });
    const { container } = bas();

    await screen.findByText(/geri yüklenebilir dosya yok/);
    expect(container.textContent).toContain("varsa aşağıdan seçebilirsiniz");
    expect(await secmeDugmesi()).toBeEnabled();
  });

  it.each([
    ["köprü yoksa", () => delete window.pywebview],
    ["pencere eskiyse", () => (window.pywebview = { api: { set_titlebar_theme: vi.fn() } })],
  ])("%s dosya kutusu kalır, düğme çizilmez", async (_ad, kur) => {
    kur();
    bas();

    expect(await screen.findByLabelText(/elinizdeki yedek dosyası/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Yedek dosyası seç" })).toBeNull();
  });

  it("köprü sayfa yüklendikten sonra gelince kutu düğmeye döner", async () => {
    delete window.pywebview;
    bas();
    await screen.findByLabelText(/elinizdeki yedek dosyası/);

    kopruyuKur();
    act(() => {
      window.dispatchEvent(new Event("pywebviewready"));
    });

    expect(await secmeDugmesi()).toBeEnabled();
    expect(screen.queryByLabelText(/elinizdeki yedek dosyası/)).toBeNull();
  });

  it("seçilen dosyanın başlığı sunucudan okunur; satır ve anahtar cümlesi listedeki gibidir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.yedekBasligi.mockResolvedValue(satir("gunluk-2026-11-01.odbak"));
    bas();

    await dosyaSec(kullanici, "E:\\gunluk-2026-11-01.odbak");

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Bu yedek 1 numaralı, 06.11.2026 tarihli kurtarma anahtarıyla açılır.",
    );
    expect(guvenlik.yedekBasligi).toHaveBeenCalledTimes(1);
    expect(guvenlik.yedekBasligi).toHaveBeenCalledWith("E:\\gunluk-2026-11-01.odbak");
    expect(screen.getByText("gunluk-2026-11-01.odbak")).toBeInTheDocument();
    expect(
      screen.getByText("Günlük yedek · kayıtlar, ekler ve üretilen evrak"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("06.11.2026 17:55 · 45 KB · Anahtar no 1 · üretim tarihi 06.11.2026"),
    ).toBeInTheDocument();
  });

  it.each([
    ["yerel", "Yedeğin kapsamı: yalnız kayıtlar; ekler bu bilgisayardan alınır."],
    ["tam", "Yedeğin kapsamı: kayıtlar, ekler ve üretilen evrak."],
  ])(
    "onay metni dosyanın adını ve kapsamını söyler, yolunu söylemez (%s)",
    async (kapsam, cumle) => {
      const kullanici = userEvent.setup();
      guvenlik.yedekBasligi.mockResolvedValue(satir(WINDOWS_ADI, { kapsam }));
      bas();
      await dosyaSec(kullanici, WINDOWS_YOLU);
      await screen.findByRole("status");

      const diyalog = await onayaGel(kullanici);

      expect(diyalog).toHaveTextContent(
        `“${WINDOWS_ADI}” yedeği mevcut veritabanının yerine konur`,
      );
      expect(diyalog).toHaveTextContent(cumle);
      expect(diyalog).not.toHaveTextContent(YOLUN_KLASORU);
    },
  );

  it("yol ekrana, konsola ve tarayıcı deposuna girmez", async () => {
    const kullanici = userEvent.setup();
    const konsol = (["log", "info", "warn", "error", "debug"] as const).map((ad) =>
      vi.spyOn(console, ad),
    );
    guvenlik.geriYukle.mockRejectedValue(new ApiError(400, "validation_error", YOL_ACILAMADI));
    bas();

    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");
    await onayla(kullanici);

    expect(await screen.findByRole("alert")).toHaveTextContent(YOL_ACILAMADI);
    expect(document.documentElement.outerHTML).not.toContain(YOLUN_KLASORU);
    for (const casus of konsol) {
      expect(JSON.stringify(casus.mock.calls)).not.toContain(YOLUN_KLASORU);
    }
    expect(JSON.stringify(Object.entries(window.localStorage))).not.toContain(YOLUN_KLASORU);
    expect(JSON.stringify(Object.entries(window.sessionStorage))).not.toContain(YOLUN_KLASORU);
  });

  it("kart sökülünce yol gider: yeni kartta kaynak seçili değildir", async () => {
    const kullanici = userEvent.setup();
    const kart = sokulebilirBas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    kart.sok();
    kart.tak();

    await screen.findByText("gunluk-2026-09-01.odbak");
    expect(screen.queryByText(WINDOWS_ADI)).toBeNull();
    expect(geriYukleDugmesi()).toBeDisabled();
  });

  it("pencere açıkken kart söküldüyse dönen yol başlık isteği göndermez", async () => {
    const kullanici = userEvent.setup();
    let sec: (yol: string) => void = () => undefined;
    koprudenSor.mockImplementationOnce(
      () =>
        new Promise((coz) => {
          sec = coz;
        }),
    );
    const kart = sokulebilirBas();
    await kullanici.click(await secmeDugmesi());
    await screen.findByRole("button", { name: "Dosya seçiliyor…" });

    kart.sok();
    await act(async () => {
      sec(WINDOWS_YOLU);
      await Promise.resolve();
    });

    expect(guvenlik.yedekBasligi).not.toHaveBeenCalled();
  });

  it("listeden seçilince seçilen dosyanın satırı kalkar, gövdede yol gitmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByText(WINDOWS_ADI);

    await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-09-01/ }));

    expect(screen.queryByText(WINDOWS_ADI)).toBeNull();
    await onayla(kullanici);
    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    expect(gidenForm().get("name")).toBe("gunluk-2026-09-01.odbak");
    expect(gidenForm().get("yol")).toBeNull();
  });

  it("dosya seçilince listedeki seçim boşalır, gövdede ad gitmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    bas();
    const radyo = await screen.findByRole("radio", { name: /gunluk-2026-09-01/ });
    await kullanici.click(radyo);

    await dosyaSec(kullanici, WINDOWS_YOLU);

    expect(radyo).not.toBeChecked();
    await screen.findByText(WINDOWS_ADI);
    await waitFor(() => expect(geriYukleDugmesi()).toBeEnabled());
    await onayla(kullanici);
    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    expect(gidenForm().get("name")).toBeNull();
    expect(gidenForm().get("yol")).toBe(WINDOWS_YOLU);
  });
});

describe("iptal ve pencere", () => {
  it("iptalde listeden seçilen kaynak aynen kalır, başlık istenmez", async () => {
    const kullanici = userEvent.setup();
    bas();
    const radyo = await screen.findByRole("radio", { name: /gunluk-2026-09-01/ });
    await kullanici.click(radyo);

    await dosyaSec(kullanici, "");

    await waitFor(async () => expect(await secmeDugmesi()).toBeEnabled());
    expect(radyo).toBeChecked();
    expect(geriYukleDugmesi()).toBeEnabled();
    expect(guvenlik.yedekBasligi).not.toHaveBeenCalled();
  });

  it("iptalde daha önce seçilen dosya aynen kalır", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await dosyaSec(kullanici, "");

    await waitFor(async () => expect(await secmeDugmesi()).toBeEnabled());
    expect(screen.getByText(WINDOWS_ADI)).toBeInTheDocument();
    expect(guvenlik.yedekBasligi).toHaveBeenCalledTimes(1);
    await onayla(kullanici);
    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    expect(gidenForm().get("yol")).toBe(WINDOWS_YOLU);
  });

  it("pencere açıkken düğme süren işi söyler; kaynak ve gönderme denetimleri kapalıdır", async () => {
    const kullanici = userEvent.setup();
    let sec: (yol: string) => void = () => undefined;
    koprudenSor.mockImplementationOnce(
      () =>
        new Promise((coz) => {
          sec = coz;
        }),
    );
    bas();
    const radyo = await screen.findByRole("radio", { name: /gunluk-2026-09-01/ });
    await kullanici.click(radyo);

    await kullanici.click(await secmeDugmesi());

    const bekleyen = await screen.findByRole("button", { name: "Dosya seçiliyor…" });
    expect(bekleyen).toBeDisabled();
    expect(radyo).toBeDisabled();
    expect(geriYukleDugmesi()).toBeDisabled();
    // Sır alanları yalnız istek sürerken kapalıdır: pencere modaldır, kullanıcı oraya varamaz.
    expect(screen.getByLabelText("Parolanız")).toBeEnabled();
    expect(screen.getByLabelText("Kurtarma anahtarı")).toBeEnabled();
    await kullanici.click(bekleyen);
    expect(koprudenSor).toHaveBeenCalledTimes(1);

    await act(async () => {
      sec("");
      await Promise.resolve();
    });

    expect(await secmeDugmesi()).toBeEnabled();
    expect(radyo).toBeEnabled();
    expect(geriYukleDugmesi()).toBeEnabled();
  });

  it("köprünün reddi iptal sayılır: ileti çıkmaz, düğme yeniden açılır", async () => {
    const kullanici = userEvent.setup();
    koprudenSor.mockRejectedValueOnce(new Error("window is closed"));
    bas();

    await kullanici.click(await secmeDugmesi());

    await waitFor(async () => expect(await secmeDugmesi()).toBeEnabled());
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain("window is closed");
    expect(guvenlik.yedekBasligi).not.toHaveBeenCalled();
  });

  it("geri yükleme sürerken düğme kapalıdır", async () => {
    const kullanici = userEvent.setup();
    let bitir: (sonuc: typeof SONUC) => void = () => undefined;
    guvenlik.geriYukle.mockImplementation(
      () =>
        new Promise((coz) => {
          bitir = coz;
        }),
    );
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await onayla(kullanici);

    await screen.findByRole("button", { name: "Geri yükleniyor…" });
    expect(await secmeDugmesi()).toBeDisabled();
    bitir(SONUC);
    await waitFor(() => expect(screen.getByLabelText("Parolanız")).toHaveValue(""));
  });
});

describe("gövde", () => {
  it.each([
    ["Windows", WINDOWS_YOLU, WINDOWS_ADI],
    ["Pardus", PARDUS_YOLU, PARDUS_ADI],
  ])(
    "yalnız yol ve sır gider; Türkçe ve boşluklu yol olduğu gibidir (%s)",
    async (_ad, yol, dosyaAdi) => {
      const kullanici = userEvent.setup();
      guvenlik.yedekBasligi.mockResolvedValue(satir(dosyaAdi));
      guvenlik.geriYukle.mockResolvedValue(SONUC);
      const dinleyici = vi.fn();
      window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      try {
        bas();
        await dosyaSec(kullanici, yol);
        await screen.findByRole("status");

        await onayla(kullanici);

        await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
        const form = gidenForm();
        expect(form.get("yol")).toBe(yol);
        expect(form.get("name")).toBeNull();
        expect(form.get("file")).toBeNull();
        expect(form.get("password")).toBe(PAROLA);
        expect(form.get("ekler_olmadan_surdur")).toBeNull();
        await waitFor(() => expect(dinleyici).toHaveBeenCalledTimes(1));
      } finally {
        window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      }
    },
  );

  it("kayıp kipinde kurtarma anahtarıyla yol gider", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue({ ...SONUC, state_written: true });
    bas(true);
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await kullanici.type(screen.getByLabelText("Kurtarma anahtarı"), "AAAA-BBBB");
    await kullanici.click(geriYukleDugmesi());
    const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
    await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    expect(gidenForm().get("yol")).toBe(WINDOWS_YOLU);
    expect(gidenForm().get("recovery_key")).toBe("AAAA-BBBB");
    expect(gidenForm().get("password")).toBeNull();
  });

  it("boy sınırı yalnız yükleme kutusundadır: büyük dosya seçilir ve gider", async () => {
    const kullanici = userEvent.setup();
    guvenlik.yedekBasligi.mockResolvedValue(satir(WINDOWS_ADI, { size: 9 * 1024 * 1024 * 1024 }));
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain("Dosya çok büyük");
  });

  it("sunucunun reddi gösterilir; kaynak kalır, aynı dosya yeniden denenebilir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockRejectedValueOnce(
      new ApiError(400, "validation_error", "Yedek dosyası okunamadı."),
    );
    guvenlik.geriYukle.mockResolvedValueOnce(SONUC);
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");
    await onayla(kullanici);
    expect(await screen.findByRole("alert")).toHaveTextContent("Yedek dosyası okunamadı.");

    await kullanici.click(geriYukleDugmesi());
    const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
    await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(2));
    expect(gidenForm(1).get("yol")).toBe(WINDOWS_YOLU);
    expect(guvenlik.yedekBasligi).toHaveBeenCalledTimes(1);
  });
});

describe("başlık okuması", () => {
  it("yanıt gelene dek ad görünür, Geri yükle kapalıdır, anahtar cümlesi çizilmez", async () => {
    const kullanici = userEvent.setup();
    const baslik = bekletilenBaslik();
    bas();

    await dosyaSec(kullanici, WINDOWS_YOLU);

    expect(await screen.findByText(WINDOWS_ADI)).toBeInTheDocument();
    expect(geriYukleDugmesi()).toBeDisabled();
    expect(screen.queryByRole("status")).toBeNull();

    await baslik.bitir(satir(WINDOWS_ADI));

    expect(await screen.findByRole("status")).toHaveTextContent("1 numaralı");
    expect(geriYukleDugmesi()).toBeEnabled();
  });

  it("eski yanıt yeni seçimi ezmez", async () => {
    const kullanici = userEvent.setup();
    const eski = bekletilenBaslik();
    bas();
    await dosyaSec(kullanici, PARDUS_YOLU);
    guvenlik.yedekBasligi.mockResolvedValueOnce(satir(WINDOWS_ADI, { kapsam: "yerel" }));
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await eski.bitir(
      satir(PARDUS_ADI, { kapsam: "tam", kurtarma: { no: 9, tarih: "2026-01-01" } }),
    );

    expect(screen.getByRole("status")).toHaveTextContent("1 numaralı");
    expect(screen.getByText(WINDOWS_ADI)).toBeInTheDocument();
    expect(screen.queryByText(PARDUS_ADI)).toBeNull();
    expect(screen.getByText("yalnız kayıtlar; ekler bu bilgisayardan alınır")).toBeInTheDocument();
  });

  it("aynı dosya yeniden seçilince de yalnız son yanıt yazılır", async () => {
    const kullanici = userEvent.setup();
    const eski = bekletilenBaslik();
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    guvenlik.yedekBasligi.mockResolvedValueOnce(satir(WINDOWS_ADI, { kapsam: "yerel" }));
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");

    await eski.bitir(satir(WINDOWS_ADI, { kapsam: "tam" }));

    expect(screen.getByText("yalnız kayıtlar; ekler bu bilgisayardan alınır")).toBeInTheDocument();
  });

  it("eski yanıt sonradan seçilen listedeki yedeği de ezmez", async () => {
    const kullanici = userEvent.setup();
    const baslik = bekletilenBaslik();
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByText(WINDOWS_ADI);
    const radyo = await screen.findByRole("radio", { name: /gunluk-2026-09-01/ });
    await kullanici.click(radyo);

    await baslik.bitir(satir(WINDOWS_ADI));

    expect(radyo).toBeChecked();
    expect(screen.getByRole("status")).toHaveTextContent("2 numaralı");
    expect(screen.queryByText(WINDOWS_ADI)).toBeNull();
  });

  it.each([
    ["Windows", WINDOWS_YOLU, WINDOWS_ADI],
    ["Pardus", PARDUS_YOLU, PARDUS_ADI],
    ["karışık ayraç", "E:\\Okul Yedekleri/iç klasör\\son yedek.odbak", "son yedek.odbak"],
  ])(
    "istek düşerse kapsam yazılmaz, ad yoldan türetilir, geri yükleme engellenmez (%s)",
    async (_ad, yol, dosyaAdi) => {
      const kullanici = userEvent.setup();
      guvenlik.yedekBasligi.mockRejectedValue(new ApiError(400, "validation_error", YOL_ACILAMADI));
      guvenlik.geriYukle.mockResolvedValue(SONUC);
      bas();

      await dosyaSec(kullanici, yol);

      expect(await screen.findByRole("status")).toHaveTextContent(
        "Bu yedeği hangi kurtarma anahtarının açtığı okunamadı.",
      );
      expect(screen.getByText(dosyaAdi)).toBeInTheDocument();
      expect(screen.queryByRole("alert")).toBeNull();
      const diyalog = await onayaGel(kullanici);
      expect(diyalog).toHaveTextContent(`“${dosyaAdi}” yedeği`);
      expect(diyalog).not.toHaveTextContent("Yedeğin kapsamı");
      await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));
      await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
      expect(gidenForm().get("yol")).toBe(yol);
    },
  );

  it("başlığı okunamayan dosyada kapsam yazılmaz, istek yine gider", async () => {
    const kullanici = userEvent.setup();
    guvenlik.yedekBasligi.mockResolvedValue(satir(WINDOWS_ADI, { kurtarma: null, kapsam: null }));
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    bas();
    await dosyaSec(kullanici, WINDOWS_YOLU);

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Bu yedeği hangi kurtarma anahtarının açtığı okunamadı.",
    );
    const diyalog = await onayaGel(kullanici);
    expect(diyalog).not.toHaveTextContent("Yedeğin kapsamı");
    await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));
    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
  });

  it("değişme anı tutulamayan dosyanın satırı tarih yazmaz", async () => {
    const kullanici = userEvent.setup();
    guvenlik.yedekBasligi.mockResolvedValue(
      satir(WINDOWS_ADI, { modified_at: null, kurtarma: null }),
    );
    bas();

    await dosyaSec(kullanici, WINDOWS_YOLU);

    expect(await screen.findByText("45 KB")).toBeInTheDocument();
  });

  it("yanıttaki ad yoldan türetilen adın yerine geçer; tür de ondan okunur", async () => {
    const kullanici = userEvent.setup();
    guvenlik.yedekBasligi.mockResolvedValue(satir("gunluk-2026-11-01.odbak"));
    bas();

    await dosyaSec(kullanici, "/media/öğretmen/a\\gunluk-2026-11-01.odbak");
    expect(
      await screen.findByText("Günlük yedek · kayıtlar, ekler ve üretilen evrak"),
    ).toBeInTheDocument();

    guvenlik.yedekBasligi.mockResolvedValue(satir("ters\\bölü.odbak"));
    await dosyaSec(kullanici, "/media/öğretmen/ters\\bölü.odbak");

    expect(await screen.findByText("ters\\bölü.odbak")).toBeInTheDocument();
    const diyalog = await onayaGel(kullanici);
    expect(diyalog).toHaveTextContent("“ters\\bölü.odbak” yedeği");
  });
});

describe("ikinci onay", () => {
  /** Seçilen dosyayla ilk denemeyi 409'a götürür. */
  async function ilkDenemeDursun(kullanici: Kullanici) {
    guvenlik.geriYukle.mockRejectedValueOnce(ekOnayiReddi());
    await dosyaSec(kullanici, WINDOWS_YOLU);
    await screen.findByRole("status");
    await onayla(kullanici);
    return screen.findByRole("button", { name: "Ekler olmadan geri yükle" });
  }

  it("ikinci istek aynı yolu ve aynı sırrı açık bayrakla yollar; başlık yeniden okunmaz", async () => {
    const kullanici = userEvent.setup();
    bas();
    const ikinci = await ilkDenemeDursun(kullanici);
    guvenlik.geriYukle.mockResolvedValueOnce(SONUC);

    await kullanici.click(ikinci);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(2));
    expect(gidenForm(0).get("ekler_olmadan_surdur")).toBeNull();
    const son = gidenForm(1);
    expect(son.get("ekler_olmadan_surdur")).toBe("true");
    expect(son.get("yol")).toBe(WINDOWS_YOLU);
    expect(son.get("file")).toBeNull();
    expect(son.get("password")).toBe(PAROLA);
    expect(guvenlik.yedekBasligi).toHaveBeenCalledTimes(1);
  });

  it("başka dosya seçilince sıfırlanır", async () => {
    const kullanici = userEvent.setup();
    bas();
    await ilkDenemeDursun(kullanici);

    await dosyaSec(kullanici, PARDUS_YOLU);

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull(),
    );
  });

  it("aynı dosya yeniden seçilince de sıfırlanır", async () => {
    const kullanici = userEvent.setup();
    bas();
    await ilkDenemeDursun(kullanici);

    await dosyaSec(kullanici, WINDOWS_YOLU);

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull(),
    );
  });

  it("listeden yedek seçilince sıfırlanır", async () => {
    const kullanici = userEvent.setup();
    bas();
    await ilkDenemeDursun(kullanici);

    await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-09-01/ }));

    expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
  });

  it("sır değişince sıfırlanır", async () => {
    const kullanici = userEvent.setup();
    bas();
    await ilkDenemeDursun(kullanici);

    await kullanici.type(screen.getByLabelText("Parolanız"), "x");

    expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
  });

  it("Aç penceresinde iptal ikinci onayı sıfırlamaz", async () => {
    const kullanici = userEvent.setup();
    bas();
    await ilkDenemeDursun(kullanici);

    await dosyaSec(kullanici, "");

    await waitFor(async () => expect(await secmeDugmesi()).toBeEnabled());
    expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).toBeEnabled();
  });

  it("pencere açıkken ikinci düğme kapalıdır", async () => {
    const kullanici = userEvent.setup();
    let sec: (yol: string) => void = () => undefined;
    bas();
    await ilkDenemeDursun(kullanici);
    koprudenSor.mockImplementationOnce(
      () =>
        new Promise((coz) => {
          sec = coz;
        }),
    );

    await kullanici.click(await secmeDugmesi());

    await screen.findByRole("button", { name: "Dosya seçiliyor…" });
    expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).toBeDisabled();
    await act(async () => {
      sec("");
      await Promise.resolve();
    });
    expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).toBeEnabled();
  });
});
