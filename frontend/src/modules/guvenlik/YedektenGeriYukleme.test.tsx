// Yedekten geri yükleme kartı testleri: liste, sır zorunluluğu (yedekler DAİMA
// şifrelidir — düz yedek dalı yok), onay akışı, FormData içeriği (kaynak ad YA
// DA dosya) ve başarıda "yeniden başlat" olayının yayınlanması. Backend hatası
// Türkçe mesajıyla kartta gösterilir. Seçilen yedeği hangi kurtarma anahtarının
// (no, tarih) açtığı sır sorulmadan önce yazılır (tasarım TK10); parola yolu
// oturumdaki hesabın kendi parolasıdır ("Parolanız"; gövdede `hesap` yok, backend
// oturumdaki hesabı kullanır). Güvenlik dosyası kayıp ekranındaki kullanımı
// (`kayipKipi`) giriş metnini değiştirir ve parola alanını göstermez. F1b-3: liste her yedeğin
// türünü ve kapsamını yazar, onay kapsamı söyler; 8 GiB üstü dosya gönderilmez; 409
// `ek_onayi_gerekli`de kart kişisiz listeyi ve ikinci düğmeyi açar, ikinci istek aynı kaynağı ve
// sırrı `ekler_olmadan_surdur` ile yollar, kaynak ya da sır değişirse onay sıfırlanır. Sahte
// rapor `geri_yukleme_ekleri.DosyaRaporu.yanit`, ret gövdesi `views.BackupRestoreView` ile aynıdır.
// Süren istek kart sökülüp takılsa da görünür, ikinci istek gitmez; istek sürerken kart söküldüyse
// ret kapatılana dek duran snackbar'la söylenir. Durulunca odak panele alınır, ikinci düğmeye değil.

import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { YENIDEN_BASLAT_OLAYI } from "../../lib/restart";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { EK_ONAYI_KART_DISINDA } from "./metinler";

const guvenlik = vi.hoisted(() => ({
  yedekler: vi.fn(),
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
    {
      name: "gunluk-2026-08-31.odbak",
      size: 4096,
      modified_at: "2026-08-31T08:00:00+03:00",
      kurtarma: null,
      kapsam: "yerel",
    },
  ],
};

const DOSYA_RAPORU = {
  kapsam: "yerel",
  yerine_konan: 0,
  yetimden_donen: 0,
  eksik: 0,
  bozuk: 0,
  onayla_suruldu: 0,
  ekler: [],
};

const SONUC = {
  old_db_name: "db-onceki-2026-09-02-101010.sqlite3",
  state_written: false,
  restart_required: true,
  dosya_raporu: DOSYA_RAPORU,
};

const DURMA_ILETISI =
  "1 ek yedek alınırkenki hâlini tutmuyor; geri yükleme yapılmadı. Onaylarsanız kayıtlar bu ekler " +
  "olmadan geri yüklenir.";
const KART_DISI_ILETI = `${DURMA_ILETISI} ${EK_ONAYI_KART_DISINDA}`;

/** Bozuk ekte durma: 409 gövdesiyle aynı (`rapor` kişisiz sayıları ve listeyi taşır). */
function ekOnayiReddi(ekler = 1) {
  const rapor = {
    ...DOSYA_RAPORU,
    kapsam: "tam",
    yerine_konan: 2,
    eksik: 1,
    bozuk: ekler,
    ekler: [
      {
        durum: "bozuk",
        kayit_turu: "ders yılı",
        kayit_no: "7",
        yukleme_tarihi: "2026-10-01",
        boyut: 4096,
        yedekte_yoktu: false,
      },
      {
        durum: "eksik",
        kayit_turu: "Kaydı bulunamadı",
        kayit_no: "",
        yukleme_tarihi: null,
        boyut: 2048,
        yedekte_yoktu: true,
      },
    ],
  };
  const govde = { code: "ek_onayi_gerekli", message: DURMA_ILETISI, fields: {}, rapor };
  return new ApiError(409, govde.code, govde.message, govde.fields, govde);
}

/** Tarayıcının bildirdiği boyu verilen File (gerçek gövde taşımadan). */
function boyluDosya(ad: string, boy: number) {
  const dosya = new File([new Uint8Array([1])], ad);
  Object.defineProperty(dosya, "size", { value: boy });
  return dosya;
}

const SEKIZ_GIB = 8 * 1024 * 1024 * 1024;

function ekranaBas(kayipKipi = false) {
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

/** Yanıtı testin elinde duran `geriYukle` isteği (bir kez). */
function bekletilenIstek() {
  let coz: (sonuc: typeof SONUC) => void = () => undefined;
  let reddet: (hata: unknown) => void = () => undefined;
  guvenlik.geriYukle.mockImplementationOnce(
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

const PAROLA = "Deneme-Parola-1";

/** Onay diyaloğundaki "Geri yükle" düğmesine basar (karttaki eş adlıdan ayrışır). */
async function onayla(kullanici: ReturnType<typeof userEvent.setup>) {
  const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
  await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));
}

describe("YedektenGeriYukleme", () => {
  beforeEach(() => {
    yedekIsleriniSifirla();
    vi.resetAllMocks();
    guvenlik.yedekler.mockResolvedValue(LISTE);
  });

  it("yedekleri ve yedek klasörünü listeler; parola alanları hep görünür", async () => {
    ekranaBas();

    expect(await screen.findByText("gunluk-2026-09-01.odbak")).toBeInTheDocument();
    expect(screen.getByText("gunluk-2026-08-31.odbak")).toBeInTheDocument();
    // Düz yedek yoktur: "şifresiz" etiketi de yoktur.
    expect(screen.queryByText(/şifresiz/)).toBeNull();
    expect(screen.getByLabelText("Parolanız")).toBeInTheDocument();
    expect(screen.getByLabelText("Kurtarma anahtarı")).toBeInTheDocument();
    // Satır yedeği açan anahtarın kimliğini taşır (tasarım TK10).
    expect(screen.getByText(/Anahtar no 2 · üretim tarihi 31\.08\.2026/)).toBeInTheDocument();
    // Eski "yönetici parolası" dili kalmadı.
    expect(document.body.textContent).not.toMatch(/yönetici parolası/i);
    expect(screen.getByText("C:\\OABDefteri\\backups")).toBeInTheDocument();
    // Kaynak seçilmeden geri yükleme düğmesi kapalıdır.
    expect(screen.getByRole("button", { name: "Geri yükle" })).toBeDisabled();
  });

  it("program açılmıyorsa iki platformun da kurtarma yolunu söyler", async () => {
    ekranaBas();
    await screen.findByText("gunluk-2026-09-01.odbak");

    // Paketle aynı: Windows'ta Başlat menüsü kısayolu (packaging/windows/oab-defteri.iss),
    // Pardus/Linux'ta `--geri-yukle` komutu (desktop/main.py, desktop/restore.py).
    expect(screen.getByText(/“OAB Defteri — Yedekten Geri Yükle” kısayolunu/)).toBeInTheDocument();
    expect(screen.getByText("oab-defteri --geri-yukle")).toBeInTheDocument();
  });

  it("yedek yokken günlük yedeğin “her gün ilk açılışta” alındığını söyler", async () => {
    guvenlik.yedekler.mockResolvedValue({ ...LISTE, backups: [] });
    ekranaBas();

    expect(await screen.findByText(/her gün ilk açılışta günlük\s+yedek alır/)).toBeInTheDocument();
  });

  it("yedeği parola ve onayla geri yükler, yeniden başlat olayını yayınlar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    const dinleyici = vi.fn();
    window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    try {
      ekranaBas();

      await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-08-31/ }));
      await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      // Onay metni kenara alma davranışını açıkça söyler.
      const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
      expect(diyalog).toHaveTextContent("db-onceki-");
      // Gövde SONUCU söyler; başlıktaki soruyu yinelemez (docs/sozluk.md §3).
      expect(diyalog).toHaveTextContent("o yedekten sonra girdiğiniz kayıtlar ekrandan kalkar");
      expect(diyalog).not.toHaveTextContent("Devam edilsin mi?");
      await kullanici.click(within(diyalog).getByRole("button", { name: "Geri yükle" }));

      await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
      const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
      expect(form.get("name")).toBe("gunluk-2026-08-31.odbak");
      expect(form.get("file")).toBeNull();
      expect(form.get("password")).toBe(PAROLA);
      expect(form.get("recovery_key")).toBeNull();
      // Parola oturumdaki hesabındır: gövdede tanıtıcı gitmez (backend oturumdan alır).
      expect(form.get("hesap")).toBeNull();
      await waitFor(() => expect(dinleyici).toHaveBeenCalled());
      // Dosya raporu olayla yeniden başlat ekranına gider.
      expect((dinleyici.mock.calls[0][0] as CustomEvent).detail).toEqual(DOSYA_RAPORU);
      // İlk istek ikinci onayı taşımaz.
      expect(form.get("ekler_olmadan_surdur")).toBeNull();
    } finally {
      window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
    }
  });

  it("parola ya da kurtarma anahtarı girilmeden istek atmaz", async () => {
    const kullanici = userEvent.setup();
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Yedekler şifrelidir; parolanızı ya da kurtarma anahtarını girin.",
    );
    expect(guvenlik.geriYukle).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("kurtarma anahtarıyla gönderir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue({ ...SONUC, state_written: true });
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
    await kullanici.type(screen.getByLabelText("Kurtarma anahtarı"), "AAAA-BBBB");
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
    expect(form.get("name")).toBe("gunluk-2026-09-01.odbak");
    expect(form.get("recovery_key")).toBe("AAAA-BBBB");
    expect(form.get("password")).toBeNull();
  });

  it("elden dosya yüklemesini FormData'ya koyar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    ekranaBas();

    const dosya = new File([new Uint8Array([1, 2, 3])], "elden.odbak");
    await kullanici.upload(await screen.findByLabelText(/elinizdeki yedek dosyası/), dosya);
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
    expect(form.get("name")).toBeNull();
    expect((form.get("file") as File).name).toBe("elden.odbak");
  });

  it("dosya seçildikten sonra listeden yedek seçilirse gövdede dosya gitmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    ekranaBas();

    await kullanici.upload(
      await screen.findByLabelText(/elinizdeki yedek dosyası/),
      new File([new Uint8Array([1, 2, 3])], "elden.odbak"),
    );
    await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-08-31/ }));
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
    expect(form.get("name")).toBe("gunluk-2026-08-31.odbak");
    expect(form.get("file")).toBeNull();
  });

  it("listeden yedek seçildikten sonra dosya seçilirse radyo boşalır, gövdede ad gitmez", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    ekranaBas();

    const radyo = await screen.findByRole("radio", { name: /gunluk-2026-08-31/ });
    await kullanici.click(radyo);
    await kullanici.upload(
      screen.getByLabelText(/elinizdeki yedek dosyası/),
      new File([new Uint8Array([1, 2, 3])], "elden.odbak"),
    );
    expect(radyo).not.toBeChecked();
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
    expect(form.get("name")).toBeNull();
    expect((form.get("file") as File).name).toBe("elden.odbak");
  });

  it("onay reddedilirse istek atmaz", async () => {
    const kullanici = userEvent.setup();
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-08-31/ }));
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
    await kullanici.click(within(diyalog).getByRole("button", { name: "Vazgeç" }));

    expect(guvenlik.geriYukle).not.toHaveBeenCalled();
  });

  it("backend hatasını Türkçe mesajıyla gösterir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Yedek açılamadı: tanıtıcı, parola ya da kurtarma anahtarı hatalı veya yedek bu kuruluma ait değil.",
      ),
    );
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-08-31/ }));
    await kullanici.type(screen.getByLabelText("Parolanız"), "Yanlis-Parola-9");
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    expect(await screen.findByRole("alert")).toHaveTextContent("Yedek açılamadı");
  });

  it("yedek klasörü boşken dosya yükleme yolu açık kalır", async () => {
    guvenlik.yedekler.mockResolvedValue({ backup_dir: "C:\\x", backups: [] });
    ekranaBas();

    expect(await screen.findByText(/geri yüklenebilir dosya yok/)).toBeInTheDocument();
    expect(screen.getByLabelText(/elinizdeki yedek dosyası/)).toBeInTheDocument();
  });

  it("kayıp kipinde giriş metni en yeni yedeği önerir", async () => {
    ekranaBas(true);

    expect(await screen.findByText(/En yeni yedeği seçin/)).toBeInTheDocument();
    expect(screen.queryByText(/Yanlış veri girişinden sonra/)).toBeNull();
  });

  it.each([false, true])(
    "giriş metni kenara alınan veritabanının 14 gün sonra silindiğini söyler (kayıp kipi: %s)",
    async (kayipKipi) => {
      const { container } = ekranaBas(kayipKipi);
      await screen.findByText("gunluk-2026-09-01.odbak");

      expect(container.textContent).toContain(
        "Mevcut veritabanı veri klasöründe “db-onceki-…” adıyla kenara alınır; 14 gün saklanır, sonra silinir.",
      );
      expect(container.textContent).not.toMatch(/silinmez/);
    },
  );

  it("liste her yedeğin türünü ve kapsamını yazar; elle adlı dosyada tür yazılmaz", async () => {
    guvenlik.yedekler.mockResolvedValue({
      ...LISTE,
      backups: [
        { ...LISTE.backups[0] },
        { ...LISTE.backups[1], name: "pre-migrate-1.2.0-2026-08-30.odbak" },
        { ...LISTE.backups[1], name: "pre-parola-acilis-2026-08-29-101530.odbak" },
        { ...LISTE.backups[1], name: "okulun-yedegi.odbak", kapsam: "tam" },
        { ...LISTE.backups[1], name: "bozuk-baslik.odbak", kapsam: null },
      ],
    });
    ekranaBas();

    const satir = async (ad: RegExp) =>
      (await screen.findByRole("radio", { name: ad })).closest("label") as HTMLElement;
    const yerel = "yalnız kayıtlar; ekler bu bilgisayardan alınır";

    expect(await satir(/gunluk-2026-09-01/)).toHaveTextContent(`Günlük yedek · ${yerel}`);
    expect(await satir(/pre-migrate-1\.2\.0/)).toHaveTextContent(
      `Güncelleme öncesi yedek · ${yerel}`,
    );
    expect(await satir(/pre-parola-acilis/)).toHaveTextContent(`Kurulum yedeği · ${yerel}`);
    const elle = await satir(/okulun-yedegi/);
    expect(elle).toHaveTextContent("kayıtlar, ekler ve üretilen evrak");
    expect(elle).not.toHaveTextContent("yedeği ·");
    const okunamayan = await satir(/bozuk-baslik/);
    expect(okunamayan).not.toHaveTextContent("kayıtlar");
    // Liste artık yalnız günlük yedekleri taşımaz.
    expect(screen.getByText("Bu bilgisayardaki yedekler (en yeniden eskiye)")).toBeInTheDocument();
    expect(screen.queryByText(/Günlük yedekler/)).toBeNull();
  });

  it.each([
    ["yerel", "Yedeğin kapsamı: yalnız kayıtlar; ekler bu bilgisayardan alınır."],
    ["tam", "Yedeğin kapsamı: kayıtlar, ekler ve üretilen evrak."],
  ])("onay metni seçilen yedeğin kapsamını söyler (%s)", async (kapsam, cumle) => {
    const kullanici = userEvent.setup();
    guvenlik.yedekler.mockResolvedValue({
      ...LISTE,
      backups: [{ ...LISTE.backups[0], kapsam }],
    });
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));

    const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
    expect(diyalog).toHaveTextContent(cumle);
    expect(diyalog).toHaveTextContent(
      "Mevcut veritabanı veri klasöründe “db-onceki-…” adıyla kenara alınır; 14 gün saklanır, sonra silinir.",
    );
    expect(diyalog).not.toHaveTextContent("silinmez");
  });

  it("kapsamı bilinmeyen yedekte (elden dosya, okunamayan başlık) onay kapsam yazmaz", async () => {
    const kullanici = userEvent.setup();
    ekranaBas();

    const dosya = new File([new Uint8Array([1, 2, 3])], "elden.odbak");
    await kullanici.upload(await screen.findByLabelText(/elinizdeki yedek dosyası/), dosya);
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));

    const diyalog = await screen.findByRole("dialog", { name: "Yedekten geri yüklensin mi?" });
    expect(diyalog).not.toHaveTextContent("Yedeğin kapsamı");
  });

  it("8 GiB üstü dosya gönderilmez; ileti seçimde ve düğmede görünür", async () => {
    const kullanici = userEvent.setup();
    ekranaBas();

    await kullanici.upload(
      await screen.findByLabelText(/elinizdeki yedek dosyası/),
      boyluDosya("buyuk.odbak", SEKIZ_GIB + 1),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Dosya çok büyük; en çok 8 GB olabilir.",
    );

    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Dosya çok büyük");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(guvenlik.geriYukle).not.toHaveBeenCalled();
  });

  it("sınırdaki 8 GiB dosya gönderilir; küçük dosya seçilince ileti kalkar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue(SONUC);
    ekranaBas();

    const kutu = await screen.findByLabelText(/elinizdeki yedek dosyası/);
    await kullanici.upload(kutu, boyluDosya("buyuk.odbak", SEKIZ_GIB + 1));
    expect(await screen.findByRole("alert")).toHaveTextContent("Dosya çok büyük");

    await kullanici.upload(kutu, boyluDosya("sinirda.odbak", SEKIZ_GIB));
    expect(screen.queryByRole("alert")).toBeNull();
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
  });

  describe("bozuk ekte ikinci onay", () => {
    /** Listeden seçilen yedekle ilk denemeyi 409'a götürür. */
    async function ilkDenemeDursun(kullanici: ReturnType<typeof userEvent.setup>) {
      guvenlik.geriYukle.mockRejectedValueOnce(ekOnayiReddi());
      await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
      await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      await onayla(kullanici);
      return screen.findByRole("button", { name: "Ekler olmadan geri yükle" });
    }

    it("iletiyi, kişisiz listeyi ve ikinci düğmeyi gösterir; olay yayınlanmaz", async () => {
      const kullanici = userEvent.setup();
      const dinleyici = vi.fn();
      window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      try {
        ekranaBas();

        await ilkDenemeDursun(kullanici);

        const kutu = screen.getByRole("alert");
        expect(kutu).toHaveTextContent(DURMA_ILETISI);
        expect(kutu).toHaveTextContent("Eksik ya da bozuk ekler:");
        expect(
          within(kutu).getByText("Bozuk · ders yılı · no 7 · 01.10.2026 · 4 KB"),
        ).toBeInTheDocument();
        expect(
          within(kutu).getByText(
            "Eksik (yedek alınırken bulunamadı ya da bozuktu) · Kaydı bulunamadı · tarih yok · 2 KB",
          ),
        ).toBeInTheDocument();
        expect(dinleyici).not.toHaveBeenCalled();
        // Sır alanda kalır: ikinci istek onu yollar.
        expect(screen.getByLabelText("Parolanız")).toHaveValue(PAROLA);
        // İlk denemenin düğmesi kapalıdır: yol ikinci düğmedir ya da Vazgeç.
        expect(screen.getByRole("button", { name: "Geri yükle" })).toBeDisabled();
      } finally {
        window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      }
    });

    it("ikinci istek aynı adı ve aynı parolayı açık bayrakla yollar", async () => {
      const kullanici = userEvent.setup();
      guvenlik.geriYukle.mockResolvedValueOnce(SONUC);
      const dinleyici = vi.fn();
      window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      try {
        ekranaBas();
        guvenlik.geriYukle.mockReset();
        const ikinci = await ilkDenemeDursun(kullanici);
        guvenlik.geriYukle.mockResolvedValueOnce({
          ...SONUC,
          dosya_raporu: { ...DOSYA_RAPORU, bozuk: 1, onayla_suruldu: 1 },
        });

        await kullanici.click(ikinci);

        await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(2));
        const ilk = guvenlik.geriYukle.mock.calls[0][0] as FormData;
        const son = guvenlik.geriYukle.mock.calls[1][0] as FormData;
        expect(ilk.get("ekler_olmadan_surdur")).toBeNull();
        expect(son.get("ekler_olmadan_surdur")).toBe("true");
        expect(son.get("name")).toBe("gunluk-2026-09-01.odbak");
        expect(son.get("password")).toBe(PAROLA);
        await waitFor(() => expect(dinleyici).toHaveBeenCalledTimes(1));
        expect((dinleyici.mock.calls[0][0] as CustomEvent).detail).toMatchObject({
          onayla_suruldu: 1,
        });
      } finally {
        window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      }
    });

    it("ikinci istek aynı File nesnesini ve kurtarma anahtarını yollar", async () => {
      const kullanici = userEvent.setup();
      guvenlik.geriYukle.mockRejectedValueOnce(ekOnayiReddi());
      guvenlik.geriYukle.mockResolvedValueOnce(SONUC);
      ekranaBas();

      const dosya = new File([new Uint8Array([1, 2, 3])], "elden.odbak");
      await kullanici.upload(await screen.findByLabelText(/elinizdeki yedek dosyası/), dosya);
      await kullanici.type(screen.getByLabelText("Kurtarma anahtarı"), "AAAA-BBBB");
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      await onayla(kullanici);
      await kullanici.click(
        await screen.findByRole("button", { name: "Ekler olmadan geri yükle" }),
      );

      await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(2));
      const son = guvenlik.geriYukle.mock.calls[1][0] as FormData;
      const ilk = guvenlik.geriYukle.mock.calls[0][0] as FormData;
      expect(son.get("file")).toBe(ilk.get("file"));
      expect((son.get("file") as File).name).toBe("elden.odbak");
      expect(son.get("name")).toBeNull();
      expect(son.get("recovery_key")).toBe("AAAA-BBBB");
      expect(son.get("ekler_olmadan_surdur")).toBe("true");
    });

    it("başka yedek seçilince ikinci onay sıfırlanır", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      await ilkDenemeDursun(kullanici);

      await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-08-31/ }));

      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
      expect(screen.getByRole("button", { name: "Geri yükle" })).toBeEnabled();
    });

    it("başka dosya seçilince ikinci onay sıfırlanır", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      await ilkDenemeDursun(kullanici);

      await kullanici.upload(
        screen.getByLabelText(/elinizdeki yedek dosyası/),
        new File([new Uint8Array([1])], "baska.odbak"),
      );

      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
    });

    it.each(["Parolanız", "Kurtarma anahtarı"])(
      "%s değişince ikinci onay sıfırlanır",
      async (ad) => {
        const kullanici = userEvent.setup();
        ekranaBas();
        await ilkDenemeDursun(kullanici);

        await kullanici.type(screen.getByLabelText(ad), "x");

        expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
      },
    );

    it("ikinci istek sürerken ikinci düğme ve Vazgeç kapalıdır, ikinci tıklama istek yollamaz", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      const ikinci = await ilkDenemeDursun(kullanici);
      const istek = bekletilenIstek();

      await kullanici.click(ikinci);

      const bekleyen = await screen.findByRole("button", { name: "Geri yükleniyor…" });
      expect(bekleyen).toBeDisabled();
      expect(screen.getByRole("button", { name: "Vazgeç" })).toBeDisabled();
      await kullanici.click(bekleyen);
      expect(guvenlik.geriYukle).toHaveBeenCalledTimes(2);

      await istek.bitir(SONUC);
      await waitFor(() => expect(screen.getByLabelText("Parolanız")).toHaveValue(""));
    });

    it("durulunca odak panele alınır, ikinci düğmeye alınmaz; ilk Tab listeye gider", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      const istek = bekletilenIstek();
      await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
      await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      await onayla(kullanici);
      await screen.findByRole("button", { name: "Geri yükleniyor…" });

      await istek.dus(ekOnayiReddi());

      const panel = await screen.findByRole("alert");
      await waitFor(() => expect(panel).toHaveFocus());
      expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).not.toHaveFocus();

      await kullanici.tab();
      expect(screen.getByRole("list", { name: "Eksik ya da bozuk ekler:" })).toHaveFocus();
      await kullanici.tab();
      expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).toHaveFocus();
    });

    it("Vazgeç ikinci onayı kapatır, istek gitmez, seçim ve sır kalır", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      await ilkDenemeDursun(kullanici);

      await kullanici.click(screen.getByRole("button", { name: "Vazgeç" }));

      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
      expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1);
      expect(screen.getByRole("button", { name: "Geri yükle" })).toBeEnabled();
      expect(screen.getByLabelText("Parolanız")).toHaveValue(PAROLA);
    });

    it("ikinci istek de reddedilirse iletisi gösterilir, ikinci düğme kalır", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      const ikinci = await ilkDenemeDursun(kullanici);
      guvenlik.geriYukle.mockRejectedValueOnce(
        new ApiError(
          400,
          "validation_error",
          "Süren bir yedekleme ya da gün işi var; geri yükleme yapılmadı. Biraz sonra yeniden deneyin.",
        ),
      );

      await kullanici.click(ikinci);

      expect(await screen.findByText(/Süren bir yedekleme ya da gün işi var/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Ekler olmadan geri yükle" })).toBeEnabled();
    });

    it("raporsuz 409 ikinci düğme açmaz, iletisi gösterilir", async () => {
      const kullanici = userEvent.setup();
      guvenlik.geriYukle.mockRejectedValueOnce(
        new ApiError(409, "ek_onayi_gerekli", DURMA_ILETISI),
      );
      ekranaBas();

      await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
      await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      await onayla(kullanici);

      expect(await screen.findByRole("alert")).toHaveTextContent(DURMA_ILETISI);
      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
    });
  });

  describe("istek sürerken kart söküldüyse", () => {
    /** Listeden seçilen yedekle isteği başlatır; yanıt testin elindedir. */
    async function istekBaslasin(kullanici: ReturnType<typeof userEvent.setup>) {
      const istek = bekletilenIstek();
      await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
      await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
      await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
      await onayla(kullanici);
      await screen.findByRole("button", { name: "Geri yükleniyor…" });
      return istek;
    }

    it("takılan yeni kart süren isteği gösterir, alanlar kapalıdır, ikinci istek gitmez", async () => {
      const kullanici = userEvent.setup();
      const kart = sokulebilirBas();
      const istek = await istekBaslasin(kullanici);

      kart.sok();
      kart.tak();

      const bekleyen = await screen.findByRole("button", { name: "Geri yükleniyor…" });
      expect(bekleyen).toBeDisabled();
      expect(await screen.findByRole("radio", { name: /gunluk-2026-08-31/ })).toBeDisabled();
      expect(screen.getByLabelText(/elinizdeki yedek dosyası/)).toBeDisabled();
      expect(screen.getByLabelText("Parolanız")).toBeDisabled();
      // Sır belleğe girmez: yeni kartın alanı boştur.
      expect(screen.getByLabelText("Parolanız")).toHaveValue("");
      await kullanici.click(bekleyen);
      expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1);

      await istek.bitir(SONUC);
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "Geri yükle" })).toBeInTheDocument(),
      );
      expect(screen.getByLabelText("Parolanız")).toBeEnabled();
    });

    it("409 kalıcı snackbar'la söylenir; dönüşte ikinci düğme yoktur, akış baştan yürür", async () => {
      const kullanici = userEvent.setup();
      const kart = sokulebilirBas();
      const istek = await istekBaslasin(kullanici);

      kart.sok();
      await istek.dus(ekOnayiReddi());

      expect(await screen.findByText(KART_DISI_ILETI)).toBeInTheDocument();
      kart.tak();
      await screen.findByRole("radio", { name: /gunluk-2026-09-01/ });
      expect(screen.queryByRole("button", { name: "Ekler olmadan geri yükle" })).toBeNull();
      expect(screen.getByLabelText("Parolanız")).toBeEnabled();
      await kullanici.click(screen.getByRole("button", { name: "Kapat" }));
      expect(screen.queryByText(KART_DISI_ILETI)).toBeNull();
    });

    it("snackbar süresi dolmaz: kullanıcı kapatana dek durur", async () => {
      vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"], shouldAdvanceTime: true });
      try {
        const kullanici = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
        const kart = sokulebilirBas();
        const istek = await istekBaslasin(kullanici);

        kart.sok();
        await istek.dus(ekOnayiReddi());
        expect(await screen.findByText(KART_DISI_ILETI)).toBeInTheDocument();

        // Öntanımlı hata süresi 6 sn'dir.
        await act(() => vi.advanceTimersByTimeAsync(60_000));

        expect(screen.getByText(KART_DISI_ILETI)).toBeInTheDocument();
      } finally {
        vi.useRealTimers();
      }
    });

    it("öteki ret de snackbar'la söylenir", async () => {
      const kullanici = userEvent.setup();
      const kart = sokulebilirBas();
      const istek = await istekBaslasin(kullanici);

      kart.sok();
      await istek.dus(new ApiError(400, "validation_error", "Yedek açılamadı."));

      expect(await screen.findByText("Yedek açılamadı.")).toBeInTheDocument();
    });

    it("kart çiziliyken ret snackbar açmaz: tek duyuru kartın satırıdır", async () => {
      const kullanici = userEvent.setup();
      ekranaBas();
      const istek = await istekBaslasin(kullanici);

      await istek.dus(new ApiError(400, "validation_error", "Yedek açılamadı."));

      expect(await screen.findByRole("alert")).toHaveTextContent("Yedek açılamadı.");
      expect(screen.getAllByText("Yedek açılamadı.")).toHaveLength(1);
    });

    it("başarı kart yokken de yeniden başlat olayını yayınlar", async () => {
      const kullanici = userEvent.setup();
      const dinleyici = vi.fn();
      window.addEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      try {
        const kart = sokulebilirBas();
        const istek = await istekBaslasin(kullanici);

        kart.sok();
        await istek.bitir(SONUC);

        await waitFor(() => expect(dinleyici).toHaveBeenCalledTimes(1));
      } finally {
        window.removeEventListener(YENIDEN_BASLAT_OLAYI, dinleyici);
      }
    });
  });

  it("istek sürerken kaynak ve sır alanları kapalıdır", async () => {
    const kullanici = userEvent.setup();
    let bitir: (sonuc: typeof SONUC) => void = () => undefined;
    guvenlik.geriYukle.mockImplementation(
      () =>
        new Promise((coz) => {
          bitir = coz;
        }),
    );
    ekranaBas();

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
    await kullanici.type(screen.getByLabelText("Parolanız"), PAROLA);
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    expect(await screen.findByRole("button", { name: "Geri yükleniyor…" })).toBeDisabled();
    expect(screen.getByRole("radio", { name: /gunluk-2026-08-31/ })).toBeDisabled();
    expect(screen.getByLabelText(/elinizdeki yedek dosyası/)).toBeDisabled();
    expect(screen.getByLabelText("Parolanız")).toBeDisabled();
    expect(screen.getByLabelText("Kurtarma anahtarı")).toBeDisabled();
    bitir(SONUC);
    await waitFor(() => expect(screen.getByLabelText("Parolanız")).toHaveValue(""));
  });

  it("seçilen yedeği hangi kurtarma anahtarının açtığını sır sorulmadan önce söyler", async () => {
    const kullanici = userEvent.setup();
    ekranaBas();

    // Seçim yokken cümle yoktur.
    await screen.findByText("gunluk-2026-09-01.odbak");
    expect(screen.queryByText(/kurtarma anahtarıyla açılır\./)).toBeNull();

    await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-09-01/ }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Bu yedek 2 numaralı, 31.08.2026 tarihli kurtarma anahtarıyla açılır.",
    );

    // Başlığı okunamayan yedek bunu açıkça söyler.
    await kullanici.click(screen.getByRole("radio", { name: /gunluk-2026-08-31/ }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Bu yedeği hangi kurtarma anahtarının açtığı okunamadı.",
    );

    // Elden dosya seçilince listedeki yedeğin cümlesi kalkar (dosyanın başlığı istemcide okunmaz).
    const dosya = new File([new Uint8Array([1, 2, 3])], "elden.odbak");
    await kullanici.upload(screen.getByLabelText(/elinizdeki yedek dosyası/), dosya);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("kayıp kipinde parola alanı yoktur; yalnız kurtarma anahtarı sorulur", async () => {
    const kullanici = userEvent.setup();
    guvenlik.geriYukle.mockResolvedValue({ ...SONUC, state_written: true });
    ekranaBas(true);

    await kullanici.click(await screen.findByRole("radio", { name: /gunluk-2026-09-01/ }));
    // Oturum yok ve güncel güvenlik dosyası okunamıyor: parola yolu işlemez.
    expect(screen.queryByLabelText("Parolanız")).toBeNull();
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Yedekler şifrelidir; yedeğin kurtarma anahtarını girin.",
    );

    await kullanici.type(screen.getByLabelText("Kurtarma anahtarı"), "AAAA-BBBB");
    await kullanici.click(screen.getByRole("button", { name: "Geri yükle" }));
    await onayla(kullanici);

    await waitFor(() => expect(guvenlik.geriYukle).toHaveBeenCalledTimes(1));
    const form = guvenlik.geriYukle.mock.calls[0][0] as FormData;
    expect(form.get("recovery_key")).toBe("AAAA-BBBB");
    expect(form.get("password")).toBeNull();
  });

  it.each([false, true])(
    "kullanıcı metninde teknik dosya uzantısı geçmez (kayıp kipi: %s)",
    async (kayipKipi) => {
      // Sözlük (docs/sozluk.md §2): ".odbak" kullanıcı metninde kullanılmaz; teknik adlar yalnız
      // Hakkında sayfasında. Liste boşken ekrandaki her metin kartın kendisinindir
      // (dolu listede dosya adları sunucudan gelen veridir, metin değil).
      guvenlik.yedekler.mockResolvedValue({ backup_dir: "C:\\x", backups: [] });
      const { container } = ekranaBas(kayipKipi);

      await screen.findByText(/geri yüklenebilir dosya yok/);
      expect(container.textContent).not.toMatch(/odbak/i);
    },
  );
});
