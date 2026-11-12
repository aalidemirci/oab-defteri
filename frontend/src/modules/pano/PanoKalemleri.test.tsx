// Genel Bakış'ın pano kalemleri (tasarım §7.10; F1c 12. adım): görünüm ("Bu Hafta Yapılacaklar",
// veli rollerinde "Bu Ay Sizden Beklenenler" ve büyük yazı), pencere (son günü yedi gün içinde ya da
// geçmiş kalemler önde, pencerenin ötesindeki kalem yok), kalemin götürdüğü ekran, tamamlanacaklar,
// bilgi bantları, boş, yükleniyor ve hata durumları, gün değişiminde ve yeniden açılışta yeniden okuma,
// aynı önerilerin sayılı tek kalemi. Veriler uydurmadır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { DUGME_BIRLIK_DONEMINE_GIT } from "../organlar/metinler";
import type { PanoKalemi, PanoYaniti } from "./api";
import {
  AY_BASLIGI,
  AY_BOS,
  DK_KADRO_BASLIGI,
  DK_YEDEK_BASLIGI,
  DONEM_IPTAL_BILGISI,
  DONEM_YOK_BILGISI,
  EKSIK_ROZETI,
  HAFTA_BASLIGI,
  HAFTA_BOS,
  PANO_OKUNAMADI,
  PANO_YUKLENIYOR,
  TAMAMLANACAKLAR_ACIKLAMASI,
  TAMAMLANACAKLAR_BASLIGI,
  YK_KADRO_BASLIGI,
  YK_YEDEK_BASLIGI,
  hesapOnerisiCumlesi,
  kalemBasligi,
  taslakCumlesi,
  yedekCagrisiCumlesi,
} from "./metinler";

const papi = vi.hoisted(() => ({ sonOturum: vi.fn(), kontrolEttim: vi.fn(), kalemler: vi.fn() }));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  panelApi: papi,
}));

import PanoKalemleri, { GUN_YOKLAMA_MS, gorunenIsler, pencereSonu } from "./PanoKalemleri";

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
