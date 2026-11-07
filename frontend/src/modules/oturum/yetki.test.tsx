// Rol süzmesi (plan F1b-2 "Ön yüz"; `yetki.tsx`). Pinlenen davranışlar: kaynak oturum özetinin
// `hesap.yetenekler`'idir (ön yüz matrisi kopyalamaz); yüklenirken ve özet hiç okunamadıysa
// hiçbir yetenek açık değildir (fail-closed) ama iki durum ayrıdır; kurulum durumunda süzme
// yoktur; kilitliyken hesap yoktur, yetenek de yoktur; sağlayıcısız değer "yükleniyor"dur;
// 403 `rol_yetkisiz` olayı (`lib/api`) özeti yeniden okutur, ileti çizmez. Rol kapısı ekranı:
// yüklenirken iskelet, açık yetenekte içerik, kapalıda h1 + tek ileti, okunamayınca ayrı ileti.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, ROL_YETKISIZ_OLAYI } from "../../lib/api";
import type { OturumDurumAdi, OturumOzeti, YetenekAdi } from "./api";

const oturum = vi.hoisted(() => ({ ozet: vi.fn() }));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  oturumApi: oturum,
}));

import { YETENEK_ADLARI } from "./api";
import RolKapisi, {
  EKRAN_ROLE_KAPALI_ILETISI,
  KURULUM_SIHIRBAZI_KAPALI_ILETISI,
  SALT_OKUR_ILETISI,
  SaltOkurNotu,
  YETKI_OKUNAMADI_ILETISI,
} from "./RolKapisi";
import {
  KURULUM,
  OKUNAMADI,
  YUKLENIYOR,
  YetkiDegeri,
  YetkiSaglayici,
  hazirYetki,
  useYetki,
  yetkiKur,
} from "./yetki";
import type { Yetki } from "./yetki";

function ozet(durum: OturumDurumAdi, yetenekler: string[] = []): OturumOzeti {
  return {
    durum,
    hesap:
      durum === "acik"
        ? {
            id: "h-1",
            tanitici: "muhasip",
            rol: "muhasip",
            rol_etiketi: "Muhasip",
            yetenekler,
          }
        : null,
    bosta_dk: 10,
    bosta_kalan_sn: durum === "acik" ? 600 : null,
    kilit_bekliyor: false,
    kurulum_tamam: durum !== "kurulum",
    yukleme_siniri_mb: 20,
  };
}

/** Yetkinin bütün adlar üzerindeki açık kümesi. */
function acikAdlar(yetki: Yetki): string[] {
  return YETENEK_ADLARI.filter((ad) => yetki.acik(ad));
}

describe("yetkiKur", () => {
  it("özet yokken yükleniyor; hiç okunamadıysa okunamadı — ikisinde de hiçbir yetenek açık değil", () => {
    expect(yetkiKur(undefined, false)).toBe(YUKLENIYOR);
    expect(yetkiKur(null, false)).toBe(YUKLENIYOR);
    expect(yetkiKur(undefined, true)).toBe(OKUNAMADI);
    expect(acikAdlar(YUKLENIYOR)).toEqual([]);
    expect(acikAdlar(OKUNAMADI)).toEqual([]);
    expect(YUKLENIYOR.durum).toBe("yukleniyor");
    expect(OKUNAMADI.durum).toBe("okunamadi");
  });

  it("açık oturumda yalnız özetteki yetenekler açıktır (ön yüz matrisi kopyalamaz)", () => {
    const yetki = yetkiKur(ozet("acik", ["son_oturum_onay", "iki_depo"]), false);
    expect(yetki.durum).toBe("hazir");
    expect(yetki.kurulum).toBe(false);
    expect(acikAdlar(yetki)).toEqual(["iki_depo", "son_oturum_onay"]);
  });

  it("bilinmeyen ad yok sayılır; alanı olmayan eski özet hiçbir yeteneği açmaz", () => {
    expect(acikAdlar(yetkiKur(ozet("acik", ["eski_bir_ad"]), false))).toEqual([]);
    const eski = { ...ozet("acik"), hesap: { ...ozet("acik").hesap } } as unknown as OturumOzeti;
    delete (eski.hesap as unknown as Record<string, unknown>).yetenekler;
    expect(acikAdlar(yetkiKur(eski, false))).toEqual([]);
  });

  it("kurulum durumunda süzme yoktur: her yetenek açık", () => {
    const yetki = yetkiKur(ozet("kurulum"), false);
    expect(yetki).toBe(KURULUM);
    expect(yetki.kurulum).toBe(true);
    expect(acikAdlar(yetki)).toEqual([...YETENEK_ADLARI]);
  });

  it.each<OturumDurumAdi>(["kilitli", "guvenlik_dosyasi_kayip"])(
    "%s durumunda hesap yoktur, hiçbir yetenek açık değildir",
    (durum) => {
      const yetki = yetkiKur(ozet(durum), false);
      expect(yetki.durum).toBe("hazir");
      expect(acikAdlar(yetki)).toEqual([]);
    },
  );

  it("hazirYetki verilen adları açar", () => {
    expect(acikAdlar(hazirYetki(["guncelleme"]))).toEqual(["guncelleme"]);
  });
});

function YetkiYazici({ ad = "guncelleme" }: { ad?: YetenekAdi }) {
  const yetki = useYetki();
  return <p>{`durum: ${yetki.durum} · ${ad}: ${yetki.acik(ad) ? "açık" : "kapalı"}`}</p>;
}

function saglayiciylaBas(cocuk = <YetkiYazici />) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <YetkiSaglayici>{cocuk}</YetkiSaglayici>
    </QueryClientProvider>,
  );
  return queryClient;
}

describe("YetkiSaglayici ve useYetki", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sağlayıcı yoksa değer yükleniyordur (hiçbir yazma denetimi açılmaz)", () => {
    render(<YetkiYazici />);
    expect(screen.getByText("durum: yukleniyor · guncelleme: kapalı")).toBeInTheDocument();
  });

  it("özet etkinliksiz okunur; yetenekler ağaca verilir", async () => {
    oturum.ozet.mockResolvedValue(ozet("acik", ["guncelleme"]));
    saglayiciylaBas();
    expect(await screen.findByText("durum: hazir · guncelleme: açık")).toBeInTheDocument();
    // Yoklama gibi: ekranı açmak kullanıcı eylemi sayılmaz (tasarım §4.4.3).
    expect(oturum.ozet).toHaveBeenCalledWith(false);
  });

  it("özet hiç okunamazsa okunamadı; bir kez okunduysa sonraki hata son yetenekleri düşürmez", async () => {
    oturum.ozet.mockRejectedValue(new ApiError(500, "500", "Sunucu hatası."));
    const ilk = saglayiciylaBas();
    expect(await screen.findByText("durum: okunamadi · guncelleme: kapalı")).toBeInTheDocument();

    oturum.ozet.mockResolvedValue(ozet("acik", ["guncelleme"]));
    await act(() => ilk.refetchQueries({ queryKey: ["oturum"] }));
    expect(await screen.findByText("durum: hazir · guncelleme: açık")).toBeInTheDocument();

    oturum.ozet.mockRejectedValue(new ApiError(500, "500", "Sunucu hatası."));
    await act(() => ilk.refetchQueries({ queryKey: ["oturum"] }));
    expect(screen.getByText("durum: hazir · guncelleme: açık")).toBeInTheDocument();
  });

  it("403 rol_yetkisiz olayı özeti yeniden okutur; süzme yeni yeteneklere uyar", async () => {
    oturum.ozet.mockResolvedValue(ozet("acik", ["guncelleme"]));
    saglayiciylaBas();
    await screen.findByText("durum: hazir · guncelleme: açık");
    expect(oturum.ozet).toHaveBeenCalledTimes(1);

    oturum.ozet.mockResolvedValue(ozet("acik", []));
    act(() => {
      window.dispatchEvent(new CustomEvent(ROL_YETKISIZ_OLAYI));
    });

    await waitFor(() => expect(oturum.ozet).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("durum: hazir · guncelleme: kapalı")).toBeInTheDocument();
  });

  it("sağlayıcı sökülünce olay dinlenmez", async () => {
    oturum.ozet.mockResolvedValue(ozet("acik", []));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <YetkiSaglayici>
          <YetkiYazici />
        </YetkiSaglayici>
      </QueryClientProvider>,
    );
    await screen.findByText("durum: hazir · guncelleme: kapalı");
    unmount();
    const sayi = oturum.ozet.mock.calls.length;
    window.dispatchEvent(new CustomEvent(ROL_YETKISIZ_OLAYI));
    await new Promise((r) => setTimeout(r, 0));
    expect(oturum.ozet.mock.calls.length).toBe(sayi);
  });
});

function kapiylaBas(yetki: Yetki) {
  return render(
    <YetkiDegeri value={yetki}>
      <RolKapisi yetenek="kullanicilar" baslik="Kullanıcılar">
        <p>EKRANIN İÇERİĞİ</p>
      </RolKapisi>
    </YetkiDegeri>,
  );
}

describe("RolKapisi", () => {
  it("yetenek açıksa içerik çizilir", () => {
    kapiylaBas(hazirYetki(["kullanicilar"]));
    expect(screen.getByText("EKRANIN İÇERİĞİ")).toBeInTheDocument();
    expect(screen.queryByText(EKRAN_ROLE_KAPALI_ILETISI)).not.toBeInTheDocument();
  });

  it("yetenek yoksa sayfanın h1'i ve tek ileti çizilir, içerik çizilmez", () => {
    kapiylaBas(hazirYetki(["erisim_gunlugu"]));
    expect(screen.getByRole("heading", { level: 1, name: "Kullanıcılar" })).toBeInTheDocument();
    expect(screen.getByText("Bu ekran hesabınızın rolüne açık değil.")).toBeInTheDocument();
    expect(screen.queryByText("EKRANIN İÇERİĞİ")).not.toBeInTheDocument();
  });

  it("özet yüklenirken ne içerik ne ileti çizilir", () => {
    kapiylaBas(YUKLENIYOR);
    expect(screen.queryByText("EKRANIN İÇERİĞİ")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
    expect(screen.queryByText(EKRAN_ROLE_KAPALI_ILETISI)).not.toBeInTheDocument();
    expect(screen.queryByText(YETKI_OKUNAMADI_ILETISI)).not.toBeInTheDocument();
    // İskelet ekran okuyucuya yüklendiğini söyler (`ui/Skeleton`).
    expect(screen.getByRole("status")).toHaveTextContent("Yükleniyor…");
  });

  it("özet okunamadıysa “rolünüze açık değil” demez, okunamadığını söyler", () => {
    kapiylaBas(OKUNAMADI);
    expect(screen.getByText(YETKI_OKUNAMADI_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText(EKRAN_ROLE_KAPALI_ILETISI)).not.toBeInTheDocument();
    expect(screen.queryByText("EKRANIN İÇERİĞİ")).not.toBeInTheDocument();
  });

  it("kurulum durumunda kapı içeriği gösterir (süzme yok)", () => {
    kapiylaBas(KURULUM);
    expect(screen.getByText("EKRANIN İÇERİĞİ")).toBeInTheDocument();
  });

  it("ekranın kendi iletisi yalnız rol kapalıyken çizilir; okunamayan özet yine okunamadığını söyler", () => {
    const ozelBas = (yetki: Yetki) =>
      render(
        <YetkiDegeri value={yetki}>
          <RolKapisi
            yetenek="kurulum_tamamlama"
            baslik="Kurulum Sihirbazı"
            kapaliIletisi={KURULUM_SIHIRBAZI_KAPALI_ILETISI}
          >
            <p>EKRANIN İÇERİĞİ</p>
          </RolKapisi>
        </YetkiDegeri>,
      );

    const kapali = ozelBas(hazirYetki(["son_oturum_onay"]));
    expect(screen.getByText(KURULUM_SIHIRBAZI_KAPALI_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText(EKRAN_ROLE_KAPALI_ILETISI)).not.toBeInTheDocument();
    kapali.unmount();

    const okunamadi = ozelBas(OKUNAMADI);
    expect(screen.getByText(YETKI_OKUNAMADI_ILETISI)).toBeInTheDocument();
    expect(screen.queryByText(KURULUM_SIHIRBAZI_KAPALI_ILETISI)).not.toBeInTheDocument();
    okunamadi.unmount();

    ozelBas(hazirYetki(["kurulum_tamamlama"]));
    expect(screen.getByText("EKRANIN İÇERİĞİ")).toBeInTheDocument();
    expect(screen.queryByText(KURULUM_SIHIRBAZI_KAPALI_ILETISI)).not.toBeInTheDocument();
  });

  it("iletiler iç kod, rol adı ya da kısaltma taşımaz", () => {
    for (const ileti of [
      EKRAN_ROLE_KAPALI_ILETISI,
      YETKI_OKUNAMADI_ILETISI,
      SALT_OKUR_ILETISI,
      KURULUM_SIHIRBAZI_KAPALI_ILETISI,
    ]) {
      expect(ileti).not.toMatch(/[a-z]+_[a-z]+/);
      expect(ileti).not.toMatch(/\b(YK|DK|MY)\b|yönetici|başkan|muhasip/i);
      expect(ileti.endsWith(".")).toBe(true);
    }
  });
});

describe("SaltOkurNotu", () => {
  it("not rolüyle salt okur iletisini verir", () => {
    render(<SaltOkurNotu />);
    expect(screen.getByRole("note")).toHaveTextContent(
      "Bu bölüm hesabınızın rolüne yalnız okuma için açık.",
    );
  });
});
