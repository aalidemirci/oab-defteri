// Genel Bakış'ın pano kalemleri (tasarım §7.10; F1c 12. adım): görünüm ("Bu Hafta Yapılacaklar",
// veli rollerinde "Bu Ay Sizden Beklenenler" ve büyük yazı), pencere (son günü yedi gün içinde ya da
// geçmiş kalemler önde, pencerenin ötesindeki kalem yok), kalemin götürdüğü ekran, tamamlanacaklar,
// bilgi bantları, boş, yükleniyor ve hata durumları, gün değişiminde ve yeniden açılışta yeniden okuma,
// aynı önerilerin sayılı tek kalemi. F2 (12. adım): genel kurul süreleri, müdürün yazısı, ibra edilmedi
// bildirimi, TEFBİS girişleri, dönem onayı ve veri sorumlusunun tamamlanacağı — başlık, kişisiz cümle
// (süreler sunucunun kural paketinden okuduğu değerlerdir), götürdüğü ekran (`?kurul=`), veli rollerinin
// ay görünümü ve sözlüğün yasakları. İbra edilmedi bildirimi ve TEFBİS kalemleri süresizdir; yalnız
// `takvim_isareti` yeteneğinde kalemin yanında "Yapıldı" düğmesi çıkar, işin yapıldığı günü yazar ve
// panoyu yeniden okur. Veriler uydurmadır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { DUGME_BIRLIK_DONEMINE_GIT } from "../organlar/metinler";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { PanoKalemi, PanoYaniti } from "./api";
import {
  AY_BASLIGI,
  AY_BOS,
  DK_KADRO_BASLIGI,
  DK_YEDEK_BASLIGI,
  DONEM_IPTAL_BILGISI,
  DONEM_ONAYI_BASLIGI,
  DONEM_YOK_BILGISI,
  EKSIK_ROZETI,
  GK_IKINCI_TOPLANTI_BASLIGI,
  GK_ILAN_BASLIGI,
  GK_OLAGAN_BASLIGI,
  GK_YENI_OKUL_BASLIGI,
  HAFTA_BASLIGI,
  HAFTA_BOS,
  IBRA_BILDIRIMI_BASLIGI,
  KURAL_SURUMU_ACIKLAMASI,
  KURAL_SURUMU_BASLIGI,
  MUDUR_YAZISI_BASLIGI,
  PANO_OKUNAMADI,
  PANO_YUKLENIYOR,
  TAMAMLANACAKLAR_ACIKLAMASI,
  TAMAMLANACAKLAR_BASLIGI,
  TEFBIS_KONUMU,
  VERI_SORUMLUSU_TAMAMLANACAK,
  YAPILDIGI_GUN_GEREKLI,
  YAPILDI_DUGMESI,
  YAPILDI_KAYDET,
  YAPILDI_PENCERESI_BASLIGI,
  YK_KADRO_BASLIGI,
  YK_YEDEK_BASLIGI,
  hesapOnerisiCumlesi,
  kalemAciklamasi,
  kalemBasligi,
  taslakCumlesi,
  yedekCagrisiCumlesi,
} from "./metinler";

const papi = vi.hoisted(() => ({
  sonOturum: vi.fn(),
  kontrolEttim: vi.fn(),
  kalemler: vi.fn(),
  takvimYapildi: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  panelApi: papi,
}));

import PanoKalemleri, {
  GUN_YOKLAMA_MS,
  gorunenIsler,
  hedef,
  pencereSonu,
  takvimSatiri,
} from "./PanoKalemleri";

function kalem(ek: Partial<PanoKalemi>): PanoKalemi {
  return {
    kod: "KADRO",
    vade: null,
    gecikti: false,
    rota: "/organlar",
    sekme: "yk",
    metin: "",
    atif: "",
    ek: {},
    ...ek,
  };
}

const YK_SURE = kalem({
  kod: "YK_GOREV_BOLUMU",
  vade: "2026-11-14",
  atif: "md. 12/3",
});
const DK_SURE = kalem({
  kod: "DK_GOREV_BOLUMU",
  vade: "2026-11-05",
  gecikti: true,
  sekme: "dk",
  atif: "md. 14/1",
});
const UZAK = kalem({ kod: "YK_GOREV_BOLUMU", vade: "2026-12-20" });
const GECIS = kalem({
  kod: "GECIS_ADIMI",
  rota: "/birlik-donemi/gecis-kurulumu",
  sekme: "",
  ek: { adim: "kurul" },
});
const KADRO = kalem({
  metin: "Yönetim kurulunda 0 yedek üye var; 5 yedek üye olmalı.",
  atif: "md. 12/1",
  ek: { organ: "YK", durum: "uyari" },
});
const EKSIK = kalem({
  kod: "EKSIK",
  metin: "Programdan önceki seçilme sayısı bilinmiyor.",
  atif: "md. 12/4",
});

function yanit(ek: Partial<PanoYaniti> = {}): PanoYaniti {
  return {
    bugun: "2026-11-11",
    gorunum: "hafta",
    bilgiler: [],
    isler: [DK_SURE, YK_SURE, UZAK, GECIS, KADRO],
    tamamlanacaklar: [EKSIK],
    ...ek,
  };
}

function cizim(queryClient: QueryClient) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PanoKalemleri />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function bas() {
  return render(cizim(new QueryClient({ defaultOptions: { queries: { retry: false } } })));
}

beforeEach(() => papi.kalemler.mockResolvedValue(yanit()));
afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe("pencere", () => {
  it("haftada bugün + 7; ayda ayın son günü, en az bugün + 7", () => {
    expect(pencereSonu("2026-11-11", "hafta")).toBe("2026-11-18");
    expect(pencereSonu("2026-11-11", "ay")).toBe("2026-11-30");
    expect(pencereSonu("2026-11-28", "ay")).toBe("2026-12-05");
    expect(pencereSonu("2026-12-29", "hafta")).toBe("2027-01-05");
  });

  it("pencerenin ötesindeki kalem çıkmaz; süresiz ve geçmiş kalem kalır (sunucu sırası)", () => {
    expect(gorunenIsler(yanit())).toEqual([DK_SURE, YK_SURE, GECIS, KADRO]);
    expect(gorunenIsler(yanit({ bugun: "2026-12-14", gorunum: "ay" }))).toContain(UZAK);
  });

  it("son günü tam pencere sınırında (bugün + 7) olan kalem listede, ertesi günkü değil", () => {
    const SINIR = kalem({ kod: "YK_GOREV_BOLUMU", vade: "2026-11-18" });
    const OTESI = kalem({ kod: "DK_GOREV_BOLUMU", vade: "2026-11-19", sekme: "dk" });
    expect(gorunenIsler(yanit({ isler: [SINIR, OTESI] }))).toEqual([SINIR]);
  });
});

describe("Pano kalemleri", () => {
  it("“Bu Hafta Yapılacaklar”: kalemler ekrana götürür, son gün ve dayanak görünür", async () => {
    bas();
    const bolum = await screen.findByRole("region", { name: HAFTA_BASLIGI });
    const baglantilar = within(bolum).getAllByRole("link");
    const yk = baglantilar.find((b) => b.textContent?.includes("Yönetim kurulunun görev bölümü"));
    expect(yk).toHaveAttribute("href", "/organlar?tab=yk");
    expect(yk).toHaveTextContent("Son gün 14.11.2026");
    expect(yk).toHaveTextContent("Dayanak: md. 12/3");
    expect(yk).toHaveTextContent("Organlar → Yönetim Kurulu");
    const dk = baglantilar.find((b) => b.textContent?.includes("Denetleme Kurulunun görev bölümü"));
    expect(dk).toHaveAttribute("href", "/organlar?tab=dk");
    expect(dk).toHaveTextContent("Süresi doldu · 05.11.2026");
    const gecis = baglantilar.find((b) => b.textContent?.includes("Görevdeki kurul girilmedi."));
    expect(gecis).toHaveAttribute("href", "/birlik-donemi/gecis-kurulumu");
    expect(gecis).toHaveTextContent("Geçiş Kurulumu");
    expect(within(bolum).getByText(KADRO.metin)).toBeInTheDocument();
    // Pencerenin ötesindeki kalem (20.12.2026) listede yok; sıra sunucununki (geçmiş önde).
    expect(bolum).not.toHaveTextContent("20.12.2026");
    expect(baglantilar[0]).toHaveTextContent("Denetleme Kurulunun görev bölümü");
    expect(screen.queryByText(AY_BASLIGI)).not.toBeInTheDocument();
  });

  it("veli rollerinde “Bu Ay Sizden Beklenenler” büyük yazıyla açılır", async () => {
    const bilgi = kalem({ kod: "DONEM_YOK", rota: "/birlik-donemi", sekme: "", ek: {} });
    papi.kalemler.mockResolvedValue(yanit({ gorunum: "ay", isler: [YK_SURE], bilgiler: [bilgi] }));
    bas();
    const baslik = await screen.findByRole("heading", { level: 2, name: AY_BASLIGI });
    expect(baslik).toHaveClass("text-headline-small");
    expect(screen.getByText("Yönetim kurulunun görev bölümü")).toHaveClass("text-title-large");
    expect(screen.queryByText(HAFTA_BASLIGI)).not.toBeInTheDocument();
    // Satırın ikincil yazısı da büyür: dayanak, götürdüğü ekran, rozet, açıklama ve bilgi bandı.
    const ekran = screen.getAllByText("Organlar → Yönetim Kurulu");
    for (const e of ekran) expect(e.parentElement).toHaveClass("text-body-medium");
    expect(screen.getByText("Dayanak: md. 12/3")).toHaveClass("text-body-medium");
    expect(screen.getByText("Dayanak: md. 12/4")).toHaveClass("text-body-medium");
    expect(screen.getByText(EKSIK_ROZETI)).toHaveClass("text-label-large");
    expect(screen.getByText(TAMAMLANACAKLAR_ACIKLAMASI)).toHaveClass("text-body-medium");
    expect(screen.getByRole("status")).toHaveClass("text-body-large");
  });

  it("hafta görünümünde ikincil yazı küçük kalır", async () => {
    const bilgi = kalem({ kod: "DONEM_YOK", rota: "/birlik-donemi", sekme: "", ek: {} });
    papi.kalemler.mockResolvedValue(yanit({ isler: [YK_SURE], bilgiler: [bilgi] }));
    bas();
    await screen.findByRole("heading", { level: 2, name: HAFTA_BASLIGI });
    for (const e of screen.getAllByText("Organlar → Yönetim Kurulu")) {
      expect(e.parentElement).toHaveClass("text-body-small");
    }
    expect(screen.getByText("Dayanak: md. 12/3")).toHaveClass("text-body-small");
    expect(screen.getByText(EKSIK_ROZETI)).toHaveClass("text-label-medium");
    expect(screen.getByText(TAMAMLANACAKLAR_ACIKLAMASI)).toHaveClass("text-body-small");
    expect(screen.getByRole("status")).toHaveClass("text-body-medium");
  });

  it("kural sürümü güncellemesi: başlık, durum cümlesi, Birlik Dönemi'ne götürür", async () => {
    const SURUM = kalem({
      kod: "KURAL_SURUMU",
      rota: "/birlik-donemi",
      sekme: "",
      ek: { bagli_paket: "OAB-2023.12", bagli_rev: 1, yeni_paket: "OAB-2023.12", yeni_rev: 2 },
    });
    papi.kalemler.mockResolvedValue(yanit({ isler: [SURUM] }));
    bas();
    const bolum = await screen.findByRole("region", { name: HAFTA_BASLIGI });
    const satir = within(bolum)
      .getAllByRole("link")
      .find((b) => b.textContent?.includes(KURAL_SURUMU_BASLIGI));
    expect(satir).toHaveAttribute("href", "/birlik-donemi");
    expect(satir).toHaveTextContent(KURAL_SURUMU_ACIKLAMASI);
    expect(satir).toHaveTextContent("Birlik Dönemi");
    // Paket kodu ve revizyon numarası kullanıcı metnine çıkmaz (sözlük §2).
    expect(satir).not.toHaveTextContent("OAB-2023.12");
    expect(KURAL_SURUMU_BASLIGI).toBe("Kural sürümü güncellemesi");
  });

  it("yedek çağrısı ve kadro başlığı kurula göre", () => {
    const yk = { ek: { organ: "YK" } };
    const dk = { ek: { organ: "DK" } };
    expect(kalemBasligi(kalem({ kod: "KADRO", ...yk }))).toBe(YK_KADRO_BASLIGI);
    expect(kalemBasligi(kalem({ kod: "KADRO", ...dk }))).toBe(DK_KADRO_BASLIGI);
    expect(kalemBasligi(kalem({ kod: "YEDEK_CAGRISI", ...yk }))).toBe(YK_YEDEK_BASLIGI);
    expect(kalemBasligi(kalem({ kod: "YEDEK_CAGRISI", ...dk }))).toBe(DK_YEDEK_BASLIGI);
    expect(YK_KADRO_BASLIGI).toBe("Yönetim kurulunun kadrosu");
    expect(DK_KADRO_BASLIGI).toBe("Denetleme Kurulunun kadrosu");
    expect(YK_YEDEK_BASLIGI).toBe("Yönetim kurulunda yedek çağrısı");
    expect(DK_YEDEK_BASLIGI).toBe("Denetleme Kurulunda yedek çağrısı");
  });

  it("tamamlanacaklar ayrı bölümdür, eksik rozeti ve dayanağıyla; boşsa çizilmez", async () => {
    const { unmount } = bas();
    const bolum = await screen.findByRole("region", { name: TAMAMLANACAKLAR_BASLIGI });
    const satir = within(bolum).getByRole("link");
    expect(satir).toHaveAttribute("href", "/organlar?tab=yk");
    expect(satir).toHaveTextContent("Eksik");
    expect(satir).toHaveTextContent(EKSIK.metin);
    expect(satir).toHaveTextContent("Dayanak: md. 12/4");
    unmount();
    papi.kalemler.mockResolvedValue(yanit({ tamamlanacaklar: [] }));
    bas();
    await screen.findByRole("region", { name: HAFTA_BASLIGI });
    expect(screen.queryByText(TAMAMLANACAKLAR_BASLIGI)).not.toBeInTheDocument();
  });

  it("boş liste: haftada ve ayda kendi cümlesi; salt okurda yazmayı öğütleyen cümle yok", async () => {
    papi.kalemler.mockResolvedValue(yanit({ isler: [], tamamlanacaklar: [] }));
    const { unmount } = bas();
    expect(await screen.findByText(HAFTA_BOS)).toBeInTheDocument();
    unmount();
    papi.kalemler.mockResolvedValue(yanit({ gorunum: "ay", isler: [], tamamlanacaklar: [] }));
    bas();
    expect(await screen.findByText(AY_BOS)).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/girin|ekleyin|açın|yapın/i);
  });

  it("bilgi bantları: kural kopyası, açık dönem yok ve iptal; Birlik Dönemi'ne götürür", async () => {
    const bilgi = (ek: Partial<PanoKalemi>) => kalem({ rota: "/birlik-donemi", sekme: "", ...ek });
    papi.kalemler.mockResolvedValue(
      yanit({ bilgiler: [bilgi({ kod: "KURAL_KOPYASI_DOGRULANAMADI" })] }),
    );
    const { unmount } = bas();
    expect(await screen.findByText(KURAL_KOPYASI_BOZUK)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: DUGME_BIRLIK_DONEMINE_GIT })).toHaveAttribute(
      "href",
      "/birlik-donemi",
    );
    expect(DUGME_BIRLIK_DONEMINE_GIT).toBe("Birlik Dönemi ekranını aç");
    unmount();
    papi.kalemler.mockResolvedValue(
      yanit({ bilgiler: [bilgi({ kod: "DONEM_YOK", ek: { son_durum: "" } })], isler: [] }),
    );
    const ikinci = bas();
    expect(await screen.findByText(DONEM_YOK_BILGISI)).toBeInTheDocument();
    ikinci.unmount();
    papi.kalemler.mockResolvedValue(
      yanit({ bilgiler: [bilgi({ kod: "DONEM_YOK", ek: { son_durum: "IPTAL" } })] }),
    );
    bas();
    expect(await screen.findByText(DONEM_IPTAL_BILGISI)).toBeInTheDocument();
  });

  it("hesap önerisi ve yarım taslak kişisiz cümleyle; taslak kutusunun ekranına götürür", async () => {
    papi.kalemler.mockResolvedValue(
      yanit({
        isler: [
          kalem({
            kod: "HESAP_ONERISI",
            rota: "/kullanicilar",
            sekme: "",
            ek: { tur: "HESAP_KAPAT", rol: "muhasip", neden: "UYELIK_DUSTU" },
          }),
          kalem({ kod: "YARIM_TASLAK", ek: { baglam: "organlar.yk_gorev_bolumu" } }),
        ],
      }),
    );
    bas();
    const hesap = await screen.findByRole("link", { name: /Hesap önerisi/ });
    expect(hesap).toHaveAttribute("href", "/kullanicilar");
    expect(hesap).toHaveTextContent(
      "Muhasip hesabı askıda: bağlı üyelik düştü ya da iptal edildi. Hesabın kapatılması önerilir.",
    );
    const taslak = screen.getByRole("link", { name: /Yarım kalan taslak/ });
    expect(taslak).toHaveAttribute("href", "/organlar?tab=yk");
    expect(taslak).toHaveTextContent(taslakCumlesi("organlar.yk_gorev_bolumu"));
  });

  it("hesap önerisinin üç türü ve iki nedeni", () => {
    expect(
      hesapOnerisiCumlesi({ tur: "HESAP_KAPAT", rol: "sekreter", neden: "GOREV_BOLUMU" }),
    ).toBe("Sekreter hesabı askıda: görev bölümünde görevi değişti. Hesabın kapatılması önerilir.");
    expect(hesapOnerisiCumlesi({ tur: "HESAP_ASKIDAN_CIKAR", rol: "baskan" })).toBe(
      "Başkan hesabı askıda, üyelik bağı yeniden geçerli. Hesabın askıdan çıkarılması önerilir.",
    );
    expect(hesapOnerisiCumlesi({ tur: "HESAP_AC", rol: "denetleme_kurulu" })).toBe(
      "Görevdeki üyeye hesap açılmadı (Denetleme Kurulu). Hesap açılması önerilir.",
    );
  });

  it("aynı öneriler tek kalemdir: sayı cümlede, bağlantı tek", async () => {
    expect(hesapOnerisiCumlesi({ tur: "HESAP_AC", rol: "denetleme_kurulu", sayi: 3 })).toBe(
      "Görevdeki 3 üyeye hesap açılmadı (Denetleme Kurulu). Hesap açılması önerilir.",
    );
    expect(
      hesapOnerisiCumlesi({ tur: "HESAP_KAPAT", rol: "muhasip", neden: "UYELIK_DUSTU", sayi: 2 }),
    ).toBe(
      "Muhasip hesabı askıda (2 hesap): bağlı üyelik düştü ya da iptal edildi. Hesapların kapatılması önerilir.",
    );
    expect(hesapOnerisiCumlesi({ tur: "HESAP_ASKIDAN_CIKAR", rol: "baskan", sayi: 2 })).toBe(
      "Başkan hesabı askıda (2 hesap), üyelik bağı yeniden geçerli. Hesapların askıdan çıkarılması önerilir.",
    );
    expect(hesapOnerisiCumlesi({ tur: "HESAP_AC", rol: "sekreter", sayi: 1 })).toBe(
      "Görevdeki üyeye hesap açılmadı (Sekreter). Hesap açılması önerilir.",
    );
    const ileti = "Başka kurumdaki görevlendirme 4 aydan uzun; yerine yedeği çağrılır.";
    expect(yedekCagrisiCumlesi({ metin: ileti, ek: { organ: "DK", sayi: 2 } })).toBe(
      `${ileti} (2 üye)`,
    );
    expect(yedekCagrisiCumlesi({ metin: ileti, ek: { organ: "DK", sayi: 1 } })).toBe(ileti);

    papi.kalemler.mockResolvedValue(
      yanit({
        isler: [
          kalem({
            kod: "HESAP_ONERISI",
            rota: "/kullanicilar",
            sekme: "",
            ek: { tur: "HESAP_AC", rol: "denetleme_kurulu", neden: "", sayi: 3 },
          }),
          kalem({
            kod: "YEDEK_CAGRISI",
            sekme: "dk",
            metin: ileti,
            atif: "md. 14/6",
            ek: { organ: "DK", sayi: 2 },
          }),
        ],
        tamamlanacaklar: [],
      }),
    );
    bas();
    const hesap = await screen.findAllByRole("link", { name: /Hesap önerisi/ });
    expect(hesap).toHaveLength(1);
    expect(hesap[0]).toHaveTextContent("Görevdeki 3 üyeye hesap açılmadı (Denetleme Kurulu).");
    const yedek = screen.getAllByRole("link", { name: new RegExp(DK_YEDEK_BASLIGI) });
    expect(yedek).toHaveLength(1);
    expect(yedek[0]).toHaveTextContent(`${ileti} (2 üye)`);
    expect(yedek[0]).toHaveAttribute("href", "/organlar?tab=dk");
  });

  it("yüklenirken iskelet ve duyuru; okunamazsa hata ve yeniden deneme", async () => {
    let coz: (y: PanoYaniti) => void = () => undefined;
    papi.kalemler.mockReturnValueOnce(new Promise<PanoYaniti>((r) => (coz = r)));
    const { unmount } = bas();
    expect(screen.getByRole("status")).toHaveTextContent(PANO_YUKLENIYOR);
    await act(async () => coz(yanit()));
    expect(await screen.findByRole("region", { name: HAFTA_BASLIGI })).toBeInTheDocument();
    unmount();

    papi.kalemler.mockRejectedValueOnce(new ApiError(500, "hata", "Sunucu hatası."));
    bas();
    const hata = await screen.findByRole("alert");
    expect(hata).toHaveTextContent(PANO_OKUNAMADI);
    await userEvent.click(within(hata).getByRole("button", { name: "Yeniden dene" }));
    expect(await screen.findByRole("region", { name: HAFTA_BASLIGI })).toBeInTheDocument();
  });

  it("kilitliyken (423) hata söylenmez", async () => {
    papi.kalemler.mockRejectedValueOnce(new ApiError(423, "locked", "Kayıtlar kilitli."));
    const { container } = bas();
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("yeniden açılış yeni okumadır (ailenin 30 sn'lik tazeliği panoda geçerli değil)", async () => {
    // Uygulamanın istemcisiyle aynı varsayılan: staleTime 30 sn, odakta yeniden okuma yok.
    const istemci = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 30_000, refetchOnWindowFocus: false } },
    });
    const ilk = render(cizim(istemci));
    await screen.findByRole("region", { name: HAFTA_BASLIGI });
    await waitFor(() => expect(istemci.isFetching()).toBe(0));
    const once = papi.kalemler.mock.calls.length;
    expect(once).toBeGreaterThan(0);
    ilk.unmount();
    render(cizim(istemci));
    await screen.findByRole("region", { name: HAFTA_BASLIGI });
    await waitFor(() => expect(papi.kalemler.mock.calls.length).toBeGreaterThan(once));
  });

  it("gün değişince kalemler yeniden okunur", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] });
    vi.setSystemTime(new Date(2026, 10, 11, 10, 0, 0));
    bas();
    await screen.findByRole("region", { name: HAFTA_BASLIGI });
    const ilk = papi.kalemler.mock.calls.length;
    // Aynı gün içinde yoklama yeniden okumaz.
    await act(async () => {
      vi.advanceTimersByTime(GUN_YOKLAMA_MS);
    });
    expect(papi.kalemler).toHaveBeenCalledTimes(ilk);
    // Saat ilerletilince gün değişir (sahte saat Date'i de ilerletir).
    vi.setSystemTime(new Date(2026, 10, 11, 23, 59, 30));
    await act(async () => {
      vi.advanceTimersByTime(GUN_YOKLAMA_MS);
    });
    await waitFor(() => expect(papi.kalemler).toHaveBeenCalledTimes(ilk + 1));
  });
});

// ---------------------------------------------------------------------------
// F2: genel kurul süreleri (plan F2 §6.3, 12. adım)
// ---------------------------------------------------------------------------
function gkKalemi(ek: Partial<PanoKalemi>): PanoKalemi {
  return kalem({ rota: "/genel-kurul", sekme: "", ...ek });
}

const OLAGAN = gkKalemi({
  kod: "GK_OLAGAN",
  vade: "2026-10-16",
  atif: "md. 9/1, 9/3",
  ek: { durum: "PLANLANMADI", son_gun: "2026-10-31", ilan_gun: 15, ilan_atif: "md. 9/3" },
});
const ILAN = gkKalemi({
  kod: "GK_ILAN",
  vade: "2026-10-05",
  gecikti: true,
  atif: "md. 9/3",
  ek: {
    durum: "KANIT_EKSIK",
    toplanti: "BIRINCI",
    eksik: "ILAN_PANOSU,INTERNET_SAYFASI",
    kurul: 5,
  },
});
const IKINCI = gkKalemi({
  kod: "GK_IKINCI_TOPLANTI",
  vade: "2026-11-19",
  atif: "md. 9/2",
  ek: { kurul: 5, sure_gun: 30, ilan_gun: 15, ilan_atif: "md. 9/3", tarihli: 0, olaganustu: 0 },
});
// Takvim kalemleri süresizdir (mevzuatta süre yok): `vade` null.
const TEFBIS = gkKalemi({
  kod: "TEFBIS_GIRISI",
  metin:
    "Okul idaresi birliğin kayıtlarını TEFBİS'e girer (md. 23/5): genel kuruldan sonra banka hesap bilgileri girilir.",
  ek: { yukumluluk: "TEFBIS_BANKA_BILGISI", satir: 41, salt_okur: false, kurul: 5 },
});
const IBRA = gkKalemi({
  kod: "IBRA_BILDIRIMI",
  metin:
    "Hesaplar ibra edilmedi: yeni yönetim kurulu ve okul yönetimi il/ilçe millî eğitim müdürlüğüne resmî yazıyla bildirir (md. 11/1-ç).",
  ek: { yukumluluk: "IBRA_EDILMEDI_BILDIRIMI", satir: 42, salt_okur: false, kurul: 5 },
});
const ONAY = gkKalemi({ kod: "DONEM_ONAYI", ek: { kurul: 5, baslangic: "2026-11-05" } });
// Son gün birinci toplantı − ilan süresi: atıf iki kuralı birlikte taşır (md. 9/1 ya da 9/6, 9/3).
const MUDUR = gkKalemi({
  kod: "MUDUR_YAZISI",
  vade: "2026-10-31",
  atif: "md. 9/1, 9/3",
  ek: { tur: "YENI_OKUL_DAVETI", kurul: 7, ilan_gun: 15, ilan_atif: "md. 9/3" },
});
const VERI_SORUMLUSU = kalem({ kod: "VERI_SORUMLUSU", rota: "/ayarlar", sekme: "okul" });

describe("F2 kalemleri", () => {
  it("adres: sekme ve genel kurulun ayrıntısı", () => {
    expect(hedef(ILAN)).toBe("/genel-kurul?kurul=5");
    expect(hedef(OLAGAN)).toBe("/genel-kurul");
    expect(hedef(VERI_SORUMLUSU)).toBe("/ayarlar?tab=okul");
    expect(hedef(YK_SURE)).toBe("/organlar?tab=yk");
  });

  it("başlık ve kişisiz cümle: süreler sunucunun değerlerinden", () => {
    expect(kalemBasligi(OLAGAN)).toBe(GK_OLAGAN_BASLIGI);
    expect(kalemAciklamasi(OLAGAN)).toBe(
      "Olağan genel kurul henüz planlanmadı. Toplantının son günü: 31.10.2026. Toplantı en az 15 gün önce ilan edilir (md. 9/3); kalemin son günü ilanın son günüdür.",
    );
    expect(
      kalemAciklamasi({
        ...OLAGAN,
        ek: { durum: "SINIRI_ASIYOR", son_gun: "2026-10-31", kurul: 5 },
      }),
    ).toBe("Birinci toplantının günü olağan genel kurulun son gününü (31.10.2026) aşıyor.");
    const yeniOkul: PanoKalemi = { ...OLAGAN, kod: "GK_YENI_OKUL" };
    expect(kalemBasligi(yeniOkul)).toBe(GK_YENI_OKUL_BASLIGI);
    expect(kalemAciklamasi(yeniOkul)).toContain(
      "Okulun açılışından sayılan son toplantı günü: 31.10.2026.",
    );
    expect(
      kalemAciklamasi({ ...yeniOkul, ek: { durum: "SINIRI_ASIYOR", son_gun: "2026-11-15" } }),
    ).toBe("Birinci toplantının günü, okulun açılışından sayılan son günü (15.11.2026) aşıyor.");
    expect(kalemBasligi(ILAN)).toBe(GK_ILAN_BASLIGI);
    expect(kalemAciklamasi(ILAN)).toBe(
      "Birinci toplantının ilanında kanıt günü girilmemiş kanal: ilan panosu, internet sayfası.",
    );
    expect(
      kalemAciklamasi({
        ...ILAN,
        ek: { durum: "ILAN_BEKLIYOR", toplanti: "BIRINCI", ilan_gun: 15 },
      }),
    ).toBe("Birinci toplantı henüz ilan edilmedi; ilan toplantıdan en az 15 gün önce yapılır.");
    expect(
      kalemAciklamasi({
        ...ILAN,
        ek: { durum: "KANIT_EKSIK", toplanti: "IKINCI", eksik: "ELDEN_YAZILI" },
      }),
    ).toBe("İkinci toplantının ilanında kanıt günü girilmemiş kanal: elden yazılı bildirim.");
    expect(kalemBasligi(IKINCI)).toBe(GK_IKINCI_TOPLANTI_BASLIGI);
    expect(kalemAciklamasi(IKINCI)).toBe(
      "Birinci toplantıda yeter sayı sağlanamadı. İkinci toplantı birinci toplantıdan en geç 30 gün içinde yapılır; tarihi ilk ilanda yoksa en az 15 gün önce ilan edilir (md. 9/3).",
    );
    expect(kalemAciklamasi({ ...IKINCI, ek: { ...IKINCI.ek, tarihli: 1 } })).toBe(
      "Birinci toplantıda yeter sayı sağlanamadı. İkinci toplantı birinci toplantıdan en geç 30 gün içinde yapılır.",
    );
    // Olağanüstü genel kurul (U10): süre kullanıcı kararı A-1 ile uygulanır; atıf sunucudan.
    expect(kalemAciklamasi({ ...IKINCI, ek: { ...IKINCI.ek, tarihli: 1, olaganustu: 1 } })).toBe(
      "Birinci toplantıda yeter sayı sağlanamadı. İkinci toplantı birinci toplantıdan en geç 30 gün içinde yapılır. md. 9/2 olağan genel kurulu düzenler; süre olağanüstü genel kurulda kullanıcı kararı A-1 ile uygulanır.",
    );
    expect(kalemBasligi(MUDUR)).toBe(MUDUR_YAZISI_BASLIGI);
    expect(kalemAciklamasi(MUDUR)).toBe(
      "Yeni açılan okulda genel kurulu okul müdürü davet eder; çağrı henüz kaydedilmedi. Toplantı en az 15 gün önce ilan edilir (md. 9/3); kalemin son günü ilanın son günüdür.",
    );
    expect(kalemAciklamasi({ ...MUDUR, ek: { ...MUDUR.ek, tur: "CAGRI_YAZISI" } })).toBe(
      "Çağrı kaydedildi; “Genel kurul toplantı çağrısı ve gündemi” belgesi henüz oluşturulmadı. Toplantı en az 15 gün önce ilan edilir (md. 9/3); kalemin son günü ilanın son günüdür.",
    );
    // Süre gelmediyse yalnız ilk cümle.
    expect(kalemAciklamasi({ ...MUDUR, ek: { tur: "CAGRI_YAZISI", kurul: 7 } })).toBe(
      "Çağrı kaydedildi; “Genel kurul toplantı çağrısı ve gündemi” belgesi henüz oluşturulmadı.",
    );
    expect(kalemBasligi(IBRA)).toBe(IBRA_BILDIRIMI_BASLIGI);
    expect(kalemAciklamasi(IBRA)).toBe(IBRA.metin);
    expect(kalemBasligi(TEFBIS)).toBe("TEFBİS: banka hesap bilgileri");
    expect(kalemAciklamasi(TEFBIS)).toBe(`${TEFBIS.metin} ${TEFBIS_KONUMU}`);
    expect(TEFBIS_KONUMU).toBe("Program TEFBİS'in yerine geçmez.");
    expect(kalemBasligi(ONAY)).toBe(DONEM_ONAYI_BASLIGI);
    expect(kalemAciklamasi(ONAY)).toBe(
      "Genel kurulun tutanağı tamamlandı; yeni birlik döneminin açılması onay bekliyor. Dönemin başlangıcı genel kurulun yapıldığı gün: 05.11.2026.",
    );
  });

  it("“Bu Hafta Yapılacaklar”: genel kurul kalemleri genel kurulun ayrıntısına götürür", async () => {
    papi.kalemler.mockResolvedValue(
      yanit({ bugun: "2026-11-11", isler: [ILAN, TEFBIS, IBRA, ONAY], tamamlanacaklar: [] }),
    );
    bas();
    const bolum = await screen.findByRole("region", { name: HAFTA_BASLIGI });
    const satir = (metin: string) =>
      within(bolum)
        .getAllByRole("link")
        .find((b) => b.textContent?.includes(metin));
    const ilan = satir(GK_ILAN_BASLIGI);
    expect(ilan).toHaveAttribute("href", "/genel-kurul?kurul=5");
    expect(ilan).toHaveTextContent("Süresi doldu · 05.10.2026");
    expect(ilan).toHaveTextContent("Dayanak: md. 9/3");
    expect(ilan).toHaveTextContent("Genel Kurul");
    expect(satir("TEFBİS: banka hesap bilgileri")).toHaveTextContent(TEFBIS_KONUMU);
    expect(satir(IBRA_BILDIRIMI_BASLIGI)).toHaveAttribute("href", "/genel-kurul?kurul=5");
    // Takvim kalemleri süresizdir: son gün ve "Süresi doldu" yazılmaz.
    for (const baslik of ["TEFBİS: banka hesap bilgileri", IBRA_BILDIRIMI_BASLIGI]) {
      expect(satir(baslik)).not.toHaveTextContent("Son gün");
      expect(satir(baslik)).not.toHaveTextContent("Süresi doldu");
    }
    // Yeteneksiz (yükleniyor) oturumda "Yapıldı" düğmesi yoktur.
    expect(within(bolum).queryByRole("button", { name: /yapıldı olarak işaretle/ })).toBeNull();
    const onay = satir(DONEM_ONAYI_BASLIGI);
    expect(onay).toHaveAttribute("href", "/genel-kurul?kurul=5");
    expect(onay).not.toHaveTextContent("Son gün");
  });

  it("veli rollerinin ay görünümünde ayın sonuna dek, haftada yedi gün içindeki kalem", async () => {
    // Sekreter (ay): ikinci toplantının son günü 19.11.2026, bugün 11.11 → ay penceresinde (30.11).
    expect(gorunenIsler(yanit({ gorunum: "ay", isler: [IKINCI, OLAGAN] }))).toEqual([
      IKINCI,
      OLAGAN,
    ]);
    // Program yöneticisi (hafta): 19.11 pencerenin (18.11) ötesinde.
    expect(gorunenIsler(yanit({ gorunum: "hafta", isler: [IKINCI] }))).toEqual([]);
    papi.kalemler.mockResolvedValue(yanit({ gorunum: "ay", isler: [IKINCI], tamamlanacaklar: [] }));
    bas();
    const satir = await screen.findByRole("link", {
      name: new RegExp(GK_IKINCI_TOPLANTI_BASLIGI),
    });
    expect(satir).toHaveAttribute("href", "/genel-kurul?kurul=5");
    expect(screen.getByText(GK_IKINCI_TOPLANTI_BASLIGI)).toHaveClass("text-title-large");
  });

  it("veri sorumlusunun tamamlanacağı Ayarlar → Okul Bilgileri'ne götürür", async () => {
    papi.kalemler.mockResolvedValue(yanit({ isler: [], tamamlanacaklar: [VERI_SORUMLUSU] }));
    bas();
    const bolum = await screen.findByRole("region", { name: TAMAMLANACAKLAR_BASLIGI });
    const satir = within(bolum).getByRole("link");
    expect(satir).toHaveAttribute("href", "/ayarlar?tab=okul");
    expect(satir).toHaveTextContent(VERI_SORUMLUSU_TAMAMLANACAK);
    expect(satir).toHaveTextContent("Ayarlar → Okul Bilgileri");
  });

  it("sözlük: kısaltma, evrak kodu, kural kimliği, “Pano” ve bayat faz cümlesi çıkmaz", () => {
    const metinler = [OLAGAN, ILAN, IKINCI, TEFBIS, IBRA, ONAY, MUDUR].flatMap((k) => [
      kalemBasligi(k),
      kalemAciklamasi(k),
    ]);
    metinler.push(VERI_SORUMLUSU_TAMAMLANACAK);
    for (const m of metinler) {
      expect(m).not.toMatch(/\b(YK|DK|E0\d|E1\d|E64)\b/);
      expect(m).not.toMatch(/genel_kurul\.|_gun\b|Pano/);
      expect(m).not.toMatch(/sonraki faz|yapılmaz/i);
    }
  });
});

describe("takvim kaleminin “Yapıldı” işareti", () => {
  function basYetkili(yetenekler: string[]) {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <YetkiDegeri value={hazirYetki(yetenekler)}>
        <SnackbarProvider>
          <QueryClientProvider client={queryClient}>
            <MemoryRouter>
              <PanoKalemleri />
            </MemoryRouter>
          </QueryClientProvider>
        </SnackbarProvider>
      </YetkiDegeri>,
    );
  }

  it("takvim satırı yalnız takvim kaleminde okunur", () => {
    expect(takvimSatiri(TEFBIS)).toBe(41);
    expect(takvimSatiri(IBRA)).toBe(42);
    expect(takvimSatiri(ILAN)).toBeNull();
    expect(takvimSatiri({ ...IBRA, ek: { yukumluluk: "IBRA_EDILMEDI_BILDIRIMI" } })).toBeNull();
    expect(takvimSatiri({ ...IBRA, ek: { ...IBRA.ek, salt_okur: true } })).toBeNull();
  });

  it("yetenek yoksa düğme çıkmaz", async () => {
    papi.kalemler.mockResolvedValue(yanit({ isler: [TEFBIS, IBRA], tamamlanacaklar: [] }));
    basYetkili([]);
    await screen.findByText(IBRA_BILDIRIMI_BASLIGI);
    expect(screen.queryByRole("button", { name: /yapıldı olarak işaretle/ })).toBeNull();
  });

  // Karar bandın değil kalemin (`ek.salt_okur`, satırın kendi dönemi): takvim kalemi kapanıştaki
  // dönemden de gelir, bant yalnız açık dönemi söyler.
  it("açık dönem D7 (bant var), satırın dönemi geçerli: düğme çıkar", async () => {
    const bilgi = kalem({ kod: "KURAL_KOPYASI_DOGRULANAMADI", rota: "/birlik-donemi", sekme: "" });
    papi.kalemler.mockResolvedValue(
      yanit({ bilgiler: [bilgi], isler: [TEFBIS, IBRA], tamamlanacaklar: [] }),
    );
    basYetkili(["takvim_isareti"]);
    expect(await screen.findByText(KURAL_KOPYASI_BOZUK)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: `${IBRA_BILDIRIMI_BASLIGI} — yapıldı olarak işaretle` }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /yapıldı olarak işaretle/ })).toHaveLength(2);
  });

  it("satırın dönemi D7 (`salt_okur`), bant yok: o kalemde düğme çıkmaz, kalem görünür", async () => {
    const saltOkurIbra = { ...IBRA, ek: { ...IBRA.ek, salt_okur: true } };
    papi.kalemler.mockResolvedValue(yanit({ isler: [TEFBIS, saltOkurIbra], tamamlanacaklar: [] }));
    basYetkili(["takvim_isareti"]);
    expect(await screen.findByText(IBRA_BILDIRIMI_BASLIGI)).toBeInTheDocument();
    expect(screen.queryByText(KURAL_KOPYASI_BOZUK)).toBeNull();
    expect(
      screen.queryByRole("button", { name: `${IBRA_BILDIRIMI_BASLIGI} — yapıldı olarak işaretle` }),
    ).toBeNull();
    expect(screen.getAllByRole("button", { name: /yapıldı olarak işaretle/ })).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: /TEFBİS: banka hesap bilgileri — yapıldı/ }),
    ).toBeInTheDocument();
  });

  it("yapıldığı gün yazılır, pano yeniden okunur; boş gün gönderilmez", async () => {
    const kullanici = userEvent.setup();
    papi.kalemler.mockResolvedValue(yanit({ isler: [ILAN, TEFBIS, IBRA], tamamlanacaklar: [] }));
    papi.takvimYapildi.mockResolvedValue({ id: 42, done_on: "2026-11-10" });
    basYetkili(["takvim_isareti"]);
    const dugme = await screen.findByRole("button", {
      name: `${IBRA_BILDIRIMI_BASLIGI} — yapıldı olarak işaretle`,
    });
    expect(dugme).toHaveTextContent(YAPILDI_DUGMESI);
    // Takvim kalemi olmayan ilanda düğme yoktur: iki takvim kalemi, iki düğme.
    expect(screen.getAllByRole("button", { name: /yapıldı olarak işaretle/ })).toHaveLength(2);
    await kullanici.click(dugme);
    const pencere = await screen.findByRole("dialog", { name: YAPILDI_PENCERESI_BASLIGI });
    const alan = within(pencere).getByLabelText(/Yapıldığı gün/);
    await kullanici.clear(alan);
    await kullanici.click(within(pencere).getByRole("button", { name: YAPILDI_KAYDET }));
    expect(await within(pencere).findByText(YAPILDIGI_GUN_GEREKLI)).toBeInTheDocument();
    expect(papi.takvimYapildi).not.toHaveBeenCalled();
    await kullanici.type(alan, "2026-11-10");
    const okumaSayisi = papi.kalemler.mock.calls.length;
    await kullanici.click(within(pencere).getByRole("button", { name: YAPILDI_KAYDET }));
    await waitFor(() => expect(papi.takvimYapildi).toHaveBeenCalledWith(42, "2026-11-10"));
    await waitFor(() => expect(papi.kalemler.mock.calls.length).toBeGreaterThan(okumaSayisi));
    await waitFor(() =>
      expect(screen.queryByRole("dialog", { name: YAPILDI_PENCERESI_BASLIGI })).toBeNull(),
    );
  });

  it("sunucunun reddi pencerede gösterilir", async () => {
    const kullanici = userEvent.setup();
    papi.kalemler.mockResolvedValue(yanit({ isler: [TEFBIS], tamamlanacaklar: [] }));
    papi.takvimYapildi.mockRejectedValue(
      new ApiError(400, "validation_error", "Yapıldığı gün bugünden sonra olamaz."),
    );
    basYetkili(["takvim_isareti"]);
    await kullanici.click(
      await screen.findByRole("button", { name: /TEFBİS: banka hesap bilgileri — yapıldı/ }),
    );
    const pencere = await screen.findByRole("dialog", { name: YAPILDI_PENCERESI_BASLIGI });
    await kullanici.click(within(pencere).getByRole("button", { name: YAPILDI_KAYDET }));
    expect(
      await within(pencere).findByText("Yapıldığı gün bugünden sonra olamaz."),
    ).toBeInTheDocument();
    expect(papi.takvimYapildi).toHaveBeenCalledWith(41, expect.any(String));
  });
});
