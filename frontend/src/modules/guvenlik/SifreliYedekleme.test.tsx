// Şifreli Yedek kartı testleri (plan F1b-3 kullanıcı kararı 04.11.2026 "Şifreli yedeği program
// kaydeder"): adı sunucu önerir, yeri köprü sorar, yol isteğin içinde gider; iptalde istek gitmez;
// köprü yoksa düğme kapalıdır (`pywebviewready` gelince açılır); iş sürerken düğme kapalıdır ve
// bekleme görünür; başarı seçilen yere yazıldığını söyler, "USB belleğe alındı" demez, yanıttaki adı
// dosyanın adı diye göstermez; eksik ek sayısı tek sayıdır. Süren iş ve son sonuç modül belleğindedir:
// kart sökülüp takılınca iş görünür, ikinci istek gitmez. Hata kartta kalıcı satırdır; kart yokken
// snackbar söyler. Sahte yanıtlar uç sözleşmesiyle aynıdır (`views.EncryptedBackupDownloadView`,
// `encrypted_backup.KayitSonucu.yanit`).

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  postBlob: vi.fn(),
}));

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  api: { get: mocks.get, post: mocks.post, put: mocks.put, postBlob: mocks.postBlob },
}));

import SifreliYedekleme from "./SifreliYedekleme";
import { yedekIsleriniSifirla } from "./yedekIsleri";

/** Dış yedek hatırlatmasının sunucu özeti — varsayılan: hiç kayıt yok. */
const HIC_KAYDEDILMEDI = {
  last_download: null,
  reminder_days: 30,
  days_since: 3,
  remind: false,
  min_reminder_days: 7,
  max_reminder_days: 90,
};

const ONERILEN_AD = "oab-defteri-yedek-2026-11-06-101530.odbak";
const BOS_YER_YOK = "Seçilen yerde yeterli boş yer yok; şifreli yedek alınmadı.";
const SECILEN_YOL = "E:\\okul-yedegi.odbak";
const SONUC = {
  ad: ONERILEN_AD,
  boyut: 3 * 1024 * 1024,
  ek_sayisi: 12,
  eksik: 0,
  denetlendi: true,
};

const koprudenSor = vi.fn<(onerilen_ad: string) => Promise<string>>();

function kopruyuKur() {
  window.pywebview = { api: { kaydetme_yeri_sor: koprudenSor } };
}

function bas(parolaKurulu = true) {
  return render(
    <SnackbarProvider>
      <SifreliYedekleme parolaKurulu={parolaKurulu} />
    </SnackbarProvider>,
  );
}

/** Ayarlar sekmesi gibi: sağlayıcı kökte kalır, kart sökülüp yeniden takılır. */
function sokulebilirBas() {
  const agac = (takili: boolean) => (
    <SnackbarProvider>{takili && <SifreliYedekleme parolaKurulu />}</SnackbarProvider>
  );
  const { rerender } = render(agac(true));
  return { sok: () => rerender(agac(false)), tak: () => rerender(agac(true)) };
}

/** Yanıtı testin elinde duran istek. */
function bekletilenPost() {
  let coz: (sonuc: typeof SONUC) => void = () => undefined;
  let reddet: (hata: unknown) => void = () => undefined;
  mocks.post.mockImplementation(
    () =>
      new Promise((c, r) => {
        coz = c;
        reddet = r;
      }),
  );
  return {
    bitir: (sonuc: typeof SONUC) =>
      act(async () => {
        coz(sonuc);
        await Promise.resolve();
      }),
    dus: (hata: unknown) =>
      act(async () => {
        reddet(hata);
        await Promise.resolve();
      }),
  };
}

const dugme = () => screen.getByRole("button", { name: /Şifreli yedeği kaydet/ });

/** Kartın sonuç kutusu (snackbar da `status`'tur, kutu kalıcıdır). */
async function sonucKutusu() {
  const satir = await screen.findByText(/^Boy: /);
  return satir.closest("[role=status]") as HTMLElement;
}

beforeEach(() => {
  yedekIsleriniSifirla();
  vi.clearAllMocks();
  koprudenSor.mockReset();
  mocks.get.mockImplementation((yol: string) =>
    Promise.resolve(
      yol === "/backups/encrypted/" ? { onerilen_ad: ONERILEN_AD } : HIC_KAYDEDILMEDI,
    ),
  );
  kopruyuKur();
});
afterEach(() => {
  delete window.pywebview;
});

it("adı sunucudan alır, köprüye verir; seçilen yol isteğin içinde gider", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValue(SONUC);
  bas();

  await userEvent.click(dugme());

  await waitFor(() =>
    expect(mocks.post).toHaveBeenCalledWith("/backups/encrypted/", { hedef: SECILEN_YOL }),
  );
  expect(mocks.get).toHaveBeenCalledWith("/backups/encrypted/");
  expect(koprudenSor).toHaveBeenCalledWith(ONERILEN_AD);
  // Bellek içi indirme yolu kalktı (plan: "bellek içi indirme yolu kalkar").
  expect(mocks.postBlob).not.toHaveBeenCalled();
});

it("kaydetme penceresinde iptalde istek gönderilmez, hiçbir şey değişmez", async () => {
  koprudenSor.mockResolvedValue("");
  bas();
  await screen.findByLabelText("Hatırlatma süresi");
  mocks.get.mockClear();

  await userEvent.click(dugme());

  await waitFor(() => expect(koprudenSor).toHaveBeenCalled());
  await waitFor(() => expect(dugme()).toBeEnabled());
  expect(mocks.post).not.toHaveBeenCalled();
  expect(screen.queryByText(/seçilen yere yazıldı/)).not.toBeInTheDocument();
  // Hatırlatma yeniden okunmaz: yalnız adın isteği gitti.
  expect(mocks.get.mock.calls).toEqual([["/backups/encrypted/"]]);
});

it("köprü yoksa düğme kapalıdır ve nedenini söyler; ad istenmez", async () => {
  delete window.pywebview;
  bas();
  await screen.findByLabelText("Hatırlatma süresi");

  expect(dugme()).toBeDisabled();
  expect(
    screen.getByText("Şifreli yedek yalnız programın kendi penceresinden kaydedilir."),
  ).toBeInTheDocument();
  expect(mocks.get).not.toHaveBeenCalledWith("/backups/encrypted/");
});

it("köprü sayfa yüklendikten sonra gelince düğme pywebviewready ile açılır", async () => {
  delete window.pywebview;
  bas();
  await screen.findByLabelText("Hatırlatma süresi");
  expect(dugme()).toBeDisabled();

  kopruyuKur();
  act(() => {
    window.dispatchEvent(new Event("pywebviewready"));
  });

  expect(dugme()).toBeEnabled();
  expect(screen.queryByText(/programın kendi penceresinden/)).not.toBeInTheDocument();
});

it("köprüde kaydetme işlevi yoksa (eski pencere) düğme kapalı kalır", async () => {
  window.pywebview = { api: { set_titlebar_theme: vi.fn() } };
  bas();
  await screen.findByLabelText("Hatırlatma süresi");

  expect(dugme()).toBeDisabled();
});

it("iş sürerken düğme kapalıdır, bekleme görünür, ikinci istek gitmez", async () => {
  let bitir: (sonuc: typeof SONUC) => void = () => undefined;
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockImplementation(
    () =>
      new Promise((coz) => {
        bitir = coz;
      }),
  );
  bas();

  await userEvent.click(dugme());

  const bekleyen = await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });
  expect(bekleyen).toBeDisabled();
  expect(screen.getByRole("status")).toHaveTextContent(
    "Şifreli yedek yazılıyor ve denetleniyor; bu iş birkaç dakika sürebilir.",
  );
  await userEvent.click(bekleyen);
  expect(mocks.post).toHaveBeenCalledTimes(1);

  await act(async () => {
    bitir(SONUC);
    await Promise.resolve();
  });

  await waitFor(() => expect(dugme()).toBeEnabled());
  expect(screen.queryByText(/bu iş birkaç dakika/)).not.toBeInTheDocument();
});

it("kaydetme penceresi açıkken düğme kapalıdır ve yer seçimini söyler", async () => {
  let sec: (yol: string) => void = () => undefined;
  koprudenSor.mockImplementation(
    () =>
      new Promise((coz) => {
        sec = coz;
      }),
  );
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByRole("button", { name: "Yer seçiliyor…" })).toBeDisabled();
  await act(async () => {
    sec("");
    await Promise.resolve();
  });
  await waitFor(() => expect(dugme()).toBeEnabled());
});

it("başarıda seçilen yere yazıldığını ve denetlendiğini söyler; USB belleğe alındı demez", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValue(SONUC);
  bas();

  await userEvent.click(dugme());

  const sonuc = await sonucKutusu();
  expect(sonuc).toHaveTextContent("Şifreli yedek seçilen yere yazıldı ve denetlendi.");
  expect(sonuc).toHaveTextContent("Boy: 3 MB · Taşıdığı ek: 12");
  expect(sonuc).not.toHaveTextContent(/bulunamadı ya da bozuktu/);
  expect(document.body.textContent).not.toMatch(/USB belleğe alındı/);
  // Yanıttaki ad serbest ad seçildiyse diskteki ad değildir; yol da ekrana düşmez.
  expect(document.body.textContent).not.toContain(ONERILEN_AD);
  expect(document.body.textContent).not.toContain(SECILEN_YOL);
});

it("eksik ek varsa sayıyı söyler; eksik ile bozuğu ayrı saymaz", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValue({ ...SONUC, ek_sayisi: 9, eksik: 3 });
  bas();

  await userEvent.click(dugme());

  const sonuc = await sonucKutusu();
  expect(within(sonuc).getByText("3 ek yedek alınırken bulunamadı ya da bozuktu.")).toBeVisible();
  // Bekleyen kullanıcı başka ekrana geçmiş olabilir: sayı snackbar'da da yazar.
  expect(
    await screen.findByText(
      "Şifreli yedek seçilen yere yazıldı ve denetlendi. 3 ek yedek alınırken bulunamadı ya da bozuktu.",
    ),
  ).toBeInTheDocument();
});

it("son kayıt tarihi kayıttan sonra yeniden okunur", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValue(SONUC);
  bas();
  expect(
    await screen.findByText("Bu bilgisayardan henüz şifreli yedek kaydedilmedi."),
  ).toBeInTheDocument();
  expect(mocks.get).toHaveBeenCalledWith("/backups/external/", { etkinlik: false });

  mocks.get.mockImplementation((yol: string) =>
    Promise.resolve(
      yol === "/backups/encrypted/"
        ? { onerilen_ad: ONERILEN_AD }
        : { ...HIC_KAYDEDILMEDI, last_download: "2026-09-27T10:15:00+03:00", days_since: 0 },
    ),
  );
  await userEvent.click(dugme());

  expect(
    await screen.findByText("Son şifreli yedek 27.09.2026 tarihinde kaydedildi (0 gün önce)."),
  ).toBeInTheDocument();
});

it("sunucunun hata iletisini gösterir, düğme yeniden açılır, tarih yeniden okunmaz", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockRejectedValue(new ApiError(400, "validation_error", BOS_YER_YOK));
  bas();
  await screen.findByLabelText("Hatırlatma süresi");
  mocks.get.mockClear();

  await userEvent.click(dugme());

  expect(await screen.findByRole("alert")).toHaveTextContent(BOS_YER_YOK);
  expect(dugme()).toBeEnabled();
  expect(screen.queryByText(/seçilen yere yazıldı/)).not.toBeInTheDocument();
  expect(mocks.get).not.toHaveBeenCalledWith("/backups/external/", { etkinlik: false });
});

it("hata kartın kalıcı satırıdır; kart çiziliyken snackbar çıkmaz (tek duyuru)", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockRejectedValue(new ApiError(400, "validation_error", BOS_YER_YOK));
  bas();

  await userEvent.click(dugme());

  const satir = await screen.findByRole("alert");
  expect(satir.tagName).toBe("P");
  expect(satir).toHaveTextContent(BOS_YER_YOK);
  expect(screen.getAllByText(BOS_YER_YOK)).toHaveLength(1);
});

it("iptal eski hatayı silmez; yer seçilip yazım başlayınca satır kalkar, başarıda dönmez", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockRejectedValueOnce(new ApiError(400, "validation_error", BOS_YER_YOK));
  bas();
  await userEvent.click(dugme());
  await screen.findByRole("alert");

  koprudenSor.mockResolvedValueOnce("");
  await userEvent.click(dugme());
  await waitFor(() => expect(dugme()).toBeEnabled());
  expect(screen.getByRole("alert")).toHaveTextContent(BOS_YER_YOK);

  const post = bekletilenPost();
  await userEvent.click(dugme());
  await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();

  await post.bitir(SONUC);
  await sonucKutusu();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("ikinci kayıt başlayınca ve düşünce eski sonuç kutusu kalkar", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValueOnce(SONUC);
  bas();
  await userEvent.click(dugme());
  await sonucKutusu();

  const post = bekletilenPost();
  await userEvent.click(dugme());
  await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });
  expect(screen.queryByText(/^Boy: /)).not.toBeInTheDocument();

  await post.dus(new ApiError(400, "validation_error", BOS_YER_YOK));

  expect(await screen.findByRole("alert")).toHaveTextContent(BOS_YER_YOK);
  expect(screen.queryByText(/^Boy: /)).not.toBeInTheDocument();
});

it("önerilen ad alınamayan denemede eski sonuç kutusu kalmaz", async () => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockResolvedValueOnce(SONUC);
  bas();
  await userEvent.click(dugme());
  await sonucKutusu();

  mocks.get.mockImplementation((yol: string) =>
    yol === "/backups/encrypted/"
      ? Promise.reject(new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."))
      : Promise.resolve(HIC_KAYDEDILMEDI),
  );
  await userEvent.click(dugme());

  expect(await screen.findByRole("alert")).toHaveTextContent("hesabınızın rolüne");
  expect(screen.queryByText(/^Boy: /)).not.toBeInTheDocument();
});

it.each([
  ["gövdesiz ret", new ApiError(500, "500", BEKLENMEYEN_HATA_ILETISI)],
  ["kopan bağlantı", new TypeError("Failed to fetch")],
])("%s sözlükteki metinle gösterilir, ham ileti çıkmaz", async (_ad, hata) => {
  koprudenSor.mockResolvedValue(SECILEN_YOL);
  mocks.post.mockRejectedValue(hata);
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByRole("alert")).toHaveTextContent("Şifreli yedek kaydedilemedi.");
  expect(document.body.textContent).not.toContain("Failed to fetch");
});

it("köprünün reddi de sözlükteki metinle gösterilir", async () => {
  koprudenSor.mockRejectedValue(new Error("window is closed"));
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByRole("alert")).toHaveTextContent("Şifreli yedek kaydedilemedi.");
  expect(mocks.post).not.toHaveBeenCalled();
});

it("hatırlatma süresi yazılamazsa ham ileti çıkmaz", async () => {
  mocks.put.mockRejectedValue(new TypeError("Failed to fetch"));
  bas();

  await userEvent.selectOptions(await screen.findByLabelText("Hatırlatma süresi"), "60");

  expect(await screen.findByText("Hatırlatma süresi kaydedilemedi.")).toBeInTheDocument();
  expect(document.body.textContent).not.toContain("Failed to fetch");
});

describe("kart sökülüp takılınca", () => {
  it("süren iş görünür, düğme kapalıdır, ikinci istek gitmez", async () => {
    koprudenSor.mockResolvedValue(SECILEN_YOL);
    const post = bekletilenPost();
    const kart = sokulebilirBas();
    await userEvent.click(dugme());
    await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });

    kart.sok();
    kart.tak();

    const bekleyen = screen.getByRole("button", { name: "Şifreli yedek kaydediliyor…" });
    expect(bekleyen).toBeDisabled();
    expect(screen.getByText(/bu iş birkaç dakika/)).toBeInTheDocument();
    await userEvent.click(bekleyen);
    expect(mocks.post).toHaveBeenCalledTimes(1);

    await post.bitir(SONUC);
    await waitFor(() => expect(dugme()).toBeEnabled());
  });

  it("iş bitince sonuç yeni kartta görünür, son kayıt tarihi yeniden okunur", async () => {
    koprudenSor.mockResolvedValue(SECILEN_YOL);
    const post = bekletilenPost();
    const kart = sokulebilirBas();
    await userEvent.click(dugme());
    await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });
    kart.sok();
    kart.tak();
    mocks.get.mockClear();

    await post.bitir({ ...SONUC, ek_sayisi: 9, eksik: 3 });

    const sonuc = await sonucKutusu();
    expect(sonuc).toHaveTextContent("Taşıdığı ek: 9");
    expect(sonuc).toHaveTextContent("3 ek yedek alınırken bulunamadı ya da bozuktu.");
    await waitFor(() =>
      expect(mocks.get).toHaveBeenCalledWith("/backups/external/", { etkinlik: false }),
    );
  });

  it("kart yokken biten işin sonucu dönüşte görünür", async () => {
    koprudenSor.mockResolvedValue(SECILEN_YOL);
    const post = bekletilenPost();
    const kart = sokulebilirBas();
    await userEvent.click(dugme());
    await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });

    kart.sok();
    await post.bitir(SONUC);
    expect(
      await screen.findByText("Şifreli yedek seçilen yere yazıldı ve denetlendi."),
    ).toBeInTheDocument();
    kart.tak();

    expect(await sonucKutusu()).toHaveTextContent("Boy: 3 MB");
    expect(dugme()).toBeEnabled();
  });

  it("kart yokken düşen işin iletisini snackbar söyler, dönüşte kartta kalır", async () => {
    koprudenSor.mockResolvedValue(SECILEN_YOL);
    const post = bekletilenPost();
    const kart = sokulebilirBas();
    await userEvent.click(dugme());
    await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });

    kart.sok();
    await post.dus(new ApiError(400, "validation_error", BOS_YER_YOK));
    expect(await screen.findByText(BOS_YER_YOK)).toBeInTheDocument();
    kart.tak();

    await waitFor(() => expect(screen.getAllByText(BOS_YER_YOK)).toHaveLength(2));
    expect(
      screen
        .getAllByRole("alert")
        .some((kutu) => kutu.tagName === "P" && kutu.textContent === BOS_YER_YOK),
    ).toBe(true);
  });

  it("yeni kart takılıyken düşen iş snackbar açmaz: tek duyuru kartın satırıdır", async () => {
    koprudenSor.mockResolvedValue(SECILEN_YOL);
    const post = bekletilenPost();
    const kart = sokulebilirBas();
    await userEvent.click(dugme());
    await screen.findByRole("button", { name: "Şifreli yedek kaydediliyor…" });
    kart.sok();
    kart.tak();

    await post.dus(new ApiError(400, "validation_error", BOS_YER_YOK));

    expect(await screen.findByRole("alert")).toHaveTextContent(BOS_YER_YOK);
    expect(screen.getAllByText(BOS_YER_YOK)).toHaveLength(1);
  });
});

it("kart sökülünce pywebviewready dinleyicisi kalkar", () => {
  const kaldir = vi.spyOn(window, "removeEventListener");
  const { unmount } = bas(false);

  unmount();

  expect(kaldir).toHaveBeenCalledWith("pywebviewready", expect.any(Function));
  kaldir.mockRestore();
});

it("önerilen ad alınamazsa pencere açılmaz, iletisi gösterilir", async () => {
  mocks.get.mockImplementation((yol: string) =>
    yol === "/backups/encrypted/"
      ? Promise.reject(new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."))
      : Promise.resolve(HIC_KAYDEDILMEDI),
  );
  bas();

  await userEvent.click(dugme());

  expect(await screen.findByText("Bu işlem hesabınızın rolüne açık değil.")).toBeInTheDocument();
  expect(koprudenSor).not.toHaveBeenCalled();
  expect(mocks.post).not.toHaveBeenCalled();
});

it("hatırlatma süresi seçilince sunucuya yazılır", async () => {
  mocks.put.mockResolvedValue({ ...HIC_KAYDEDILMEDI, reminder_days: 60 });
  bas();

  const secim = await screen.findByLabelText("Hatırlatma süresi");
  await userEvent.selectOptions(secim, "60");

  await waitFor(() =>
    expect(mocks.put).toHaveBeenCalledWith("/backups/external/", { reminder_days: 60 }),
  );
  expect(await screen.findByText("Hatırlatma süresi kaydedildi.")).toBeInTheDocument();
});

it("hatırlatma süresi dolunca kartta ne yapılacağı yazar; dolmadıysa kalan gün", async () => {
  mocks.get.mockResolvedValue({
    ...HIC_KAYDEDILMEDI,
    last_download: "2026-08-01T10:00:00+03:00",
    days_since: 57,
    remind: true,
  });
  const { unmount } = bas();
  expect(await screen.findByRole("status")).toHaveTextContent(
    "Hatırlatma süresi doldu: şifreli yedeği USB belleğe kaydedin.",
  );
  unmount();

  mocks.get.mockResolvedValue({
    ...HIC_KAYDEDILMEDI,
    last_download: "2026-09-20T10:00:00+03:00",
    days_since: 7,
  });
  bas();
  expect(
    await screen.findByText("Genel Bakış 23 gün sonra yeniden hatırlatır."),
  ).toBeInTheDocument();
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});

it("hiç kayıt yokken ve süre dolmamışken hatırlatma cümlesi çizilmez", async () => {
  bas();
  expect(
    await screen.findByText("Bu bilgisayardan henüz şifreli yedek kaydedilmedi."),
  ).toBeInTheDocument();
  expect(screen.queryByText(/yeniden hatırlatır/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Hatırlatma süresi doldu/)).not.toBeInTheDocument();
});

it("parola kurulmadan dış yedek özeti istenmez", () => {
  bas(false);

  expect(mocks.get).not.toHaveBeenCalled();
  expect(screen.queryByLabelText("Hatırlatma süresi")).not.toBeInTheDocument();
});

it("parola yokken düğme kapalıdır ve nedenini söyler", () => {
  bas(false);

  expect(dugme()).toBeDisabled();
  expect(screen.getByText(/önce program yöneticisi hesabını kurmalısınız/)).toBeInTheDocument();
});

it("kart adı ve metin kullanıcı kararındaki sözlerdir", async () => {
  bas();
  await screen.findByLabelText("Hatırlatma süresi");

  expect(screen.getByRole("heading", { name: "Şifreli Yedek" })).toBeInTheDocument();
  expect(screen.getByText(/Kayıtlar, ekler ve üretilen evrak/)).toBeInTheDocument();
  expect(document.body.textContent).not.toMatch(/Veritabanı Yedeği|indir/i);
});

it("metin kripto jargonu kullanmaz (teknik adlar yalnız Hakkında sayfasında)", async () => {
  bas();
  // Dış yedek özeti gelsin (durum güncellemesi testin içinde kalsın).
  await screen.findByLabelText("Hatırlatma süresi");

  expect(screen.getByText(/güçlü şifrelemeyle\s+korunur/)).toBeInTheDocument();
  expect(screen.getByText(/ağ diskini/)).toBeInTheDocument();
  expect(screen.queryByText(/X25519|AES-256|NAS/)).not.toBeInTheDocument();
});

it("buluta kopyalamayı önermez (Yönerge 11/23: bulut depolama sistemine veri aktarılmaz)", async () => {
  bas();
  await screen.findByLabelText("Hatırlatma süresi");

  expect(screen.getByText(/bulut\s+depolama hizmetine yüklemeyin/)).toBeInTheDocument();
  expect(screen.queryByText(/bulut klasörüne/)).not.toBeInTheDocument();
});
