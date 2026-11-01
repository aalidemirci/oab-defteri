// Oturum göstergesi (tasarım §4.4.3, TK14; plan F1b-1 "Oturum"): açık oturumda rol
// etiketi + tanıtıcı (kişi adı yok), boşta kilide görsel geri sayım (yalnız kurulumdan
// sonra; mutlak süre yok), "Kilitle" + Ctrl+Shift+L. Kilitle pencereyi yeniden yükler
// (D53); uzun iş sürerken ertelenir ("İşlem bitince kilitlenecek"); doğrulanmamış
// kurtarma anahtarı beklerken önce sorar. Görevli kipi ve Ctrl+Shift+G yoktur.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, etkinlikSaatleriniSifirla } from "../../lib/api";
import { pencereIcerigi } from "../../lib/kilit";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { bekleyenKurtarmaAnahtariniYaz } from "../guvenlik/bekleyenAnahtar";
import type { OturumDurumAdi, OturumOzeti } from "./api";

const oturum = vi.hoisted(() => ({ ozet: vi.fn(), kilitle: vi.fn() }));

vi.mock("./api", () => ({ oturumApi: oturum }));

import OturumGostergesi from "./OturumGostergesi";
import { KILITLE_KISAYOLU } from "./useKilitle";

function ozetOlustur(durum: OturumDurumAdi, ek: Partial<OturumOzeti> = {}): OturumOzeti {
  const acik = durum === "acik";
  return {
    durum,
    hesap: acik
      ? { id: "h-1", tanitici: "dk-2", rol: "denetleme_kurulu", rol_etiketi: "Denetleme Kurulu 2" }
      : null,
    bosta_dk: 10,
    bosta_kalan_sn: acik ? 161 : null,
    kilit_bekliyor: false,
    kurulum_tamam: true,
    ...ek,
  };
}

function bas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <SnackbarProvider>
        <ConfirmProvider>
          <OturumGostergesi />
        </ConfirmProvider>
      </SnackbarProvider>
    </QueryClientProvider>,
  );
}

function grup(): HTMLElement {
  return screen.getByRole("group", { name: "Oturum" });
}

beforeEach(() => {
  vi.clearAllMocks();
  etkinlikSaatleriniSifirla();
});

describe("OturumGostergesi — açık oturum", () => {
  it("rol etiketi ve tanıtıcıyı, geri sayımı ve Kilitle'yi gösterir; görevli geçişi yoktur", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    bas();

    expect(await screen.findByText("Denetleme Kurulu 2")).toBeInTheDocument();
    expect(within(grup()).getByText("dk-2")).toBeInTheDocument();
    expect(screen.getByTestId("oturum-geri-sayim")).toHaveTextContent("2:41");
    const kilitle = within(grup()).getByRole("button", { name: "Kilitle" });
    expect(kilitle).toHaveAttribute("title", `Kilitle (${KILITLE_KISAYOLU})`);
    expect(kilitle).toHaveAttribute("aria-keyshortcuts", "Control+Shift+L");
    expect(grup().firstElementChild).toHaveAttribute(
      "title",
      expect.stringContaining("10 dakika işlem yapılmazsa kilitlenir"),
    );
    expect(screen.queryByText(/kip/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /Görevli|Yönetici kipine/ })).toBeNull();
  });

  it("kurulum tamamlanmadan geri sayım ve boşta kilit ipucu yoktur", async () => {
    oturum.ozet.mockResolvedValue(
      ozetOlustur("acik", { kurulum_tamam: false, bosta_kalan_sn: null }),
    );
    bas();
    await screen.findByText("Denetleme Kurulu 2");
    expect(screen.queryByTestId("oturum-geri-sayim")).toBeNull();
    expect(grup().firstElementChild).not.toHaveAttribute("title");
    expect(within(grup()).getByRole("button", { name: "Kilitle" })).toBeInTheDocument();
  });

  it("kilit beklerken “İşlem bitince kilitlenecek” yazar, sayaç durur", async () => {
    oturum.ozet.mockResolvedValue(
      ozetOlustur("acik", { kilit_bekliyor: true, bosta_kalan_sn: null }),
    );
    bas();
    expect(
      await within(await screen.findByRole("group", { name: "Oturum" })).findByRole("status"),
    ).toHaveTextContent("İşlem bitince kilitlenecek");
    expect(screen.queryByTestId("oturum-geri-sayim")).toBeNull();
  });

  it("geri sayım sıfırsa oturum sunucuya yeniden sorulur", async () => {
    oturum.ozet
      .mockResolvedValueOnce(ozetOlustur("acik", { bosta_kalan_sn: 0 }))
      .mockResolvedValue(ozetOlustur("kilitli"));
    bas();
    await waitFor(() => expect(oturum.ozet).toHaveBeenCalledTimes(2));
    expect(oturum.ozet).toHaveBeenLastCalledWith(false);
    // Açık sanılan oturum kilitli göründü: boşta kilit, pencere yeniden yüklenir.
    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
  });
});

describe("OturumGostergesi — Kilitle", () => {
  it("Kilitle kilit ucunu çağırır ve pencereyi yeniden yükler", async () => {
    const kullanici = userEvent.setup();
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    oturum.kilitle.mockResolvedValue({ sonuc: "kilitlendi", ...ozetOlustur("kilitli") });
    bas();

    await kullanici.click(await screen.findByRole("button", { name: "Kilitle" }));

    expect(oturum.kilitle).toHaveBeenCalledTimes(1);
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("Ctrl+Shift+L kısayolu kilitler; eksik biçimleri kilitlemez", async () => {
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    oturum.kilitle.mockResolvedValue({ sonuc: "kilitlendi", ...ozetOlustur("kilitli") });
    bas();
    await screen.findByText("Denetleme Kurulu 2");

    fireEvent.keyDown(window, { key: "l", ctrlKey: true });
    fireEvent.keyDown(window, { key: "L", shiftKey: true });
    fireEvent.keyDown(window, { key: "L", ctrlKey: true, shiftKey: true, altKey: true });
    fireEvent.keyDown(window, { key: "L", ctrlKey: true, shiftKey: true, repeat: true });
    fireEvent.keyDown(window, { key: "G", ctrlKey: true, shiftKey: true });
    expect(oturum.kilitle).not.toHaveBeenCalled();

    fireEvent.keyDown(window, { key: "L", ctrlKey: true, shiftKey: true });
    await waitFor(() => expect(oturum.kilitle).toHaveBeenCalledTimes(1));
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("uzun iş sürerken ertelenen kilit yüklemez, “İşlem bitince kilitlenecek” der", async () => {
    const kullanici = userEvent.setup();
    const bekliyor = ozetOlustur("acik", { kilit_bekliyor: true, bosta_kalan_sn: null });
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    oturum.kilitle.mockResolvedValue({ sonuc: "ertelendi", ...bekliyor });
    bas();
    const dugme = await screen.findByRole("button", { name: "Kilitle" });
    oturum.ozet.mockResolvedValue(bekliyor);

    await kullanici.click(dugme);

    expect(await within(grup()).findByRole("status")).toHaveTextContent(
      "İşlem bitince kilitlenecek",
    );
    expect(await screen.findByText("İşlem bitince kilitlenecek.")).toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("doğrulanmamış kurtarma anahtarı beklerken önce sorar; Vazgeç'te kilitlemez", async () => {
    const kullanici = userEvent.setup();
    oturum.ozet.mockResolvedValue(ozetOlustur("acik", { kurulum_tamam: false }));
    oturum.kilitle.mockResolvedValue({ sonuc: "kilitlendi", ...ozetOlustur("kilitli") });
    bekleyenKurtarmaAnahtariniYaz("TEST-KURT-ARMA-ANAH");
    bas();

    await kullanici.click(await screen.findByRole("button", { name: "Kilitle" }));
    const diyalog = await screen.findByRole("dialog", { name: "Program kilitlensin mi?" });
    expect(diyalog).toHaveTextContent(/anahtar ekrandan kalkar/);
    await kullanici.click(within(diyalog).getByRole("button", { name: "Vazgeç" }));

    expect(oturum.kilitle).not.toHaveBeenCalled();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();

    await kullanici.click(screen.getByRole("button", { name: "Kilitle" }));
    await kullanici.click(
      within(await screen.findByRole("dialog", { name: "Program kilitlensin mi?" })).getByRole(
        "button",
        { name: "Kilitle" },
      ),
    );
    await waitFor(() => expect(oturum.kilitle).toHaveBeenCalledTimes(1));
    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
  });

  it("kilitleme başarısızsa hata gösterilir, kod gösterilmez", async () => {
    const kullanici = userEvent.setup();
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    oturum.kilitle.mockRejectedValue(new ApiError(500, "500", ""));
    bas();

    await kullanici.click(await screen.findByRole("button", { name: "Kilitle" }));

    expect(await screen.findByText("Kilitlenemedi.")).toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("oturum bu arada kilitlenmişse (423) hata göstermeden yine yükler", async () => {
    const kullanici = userEvent.setup();
    oturum.ozet.mockResolvedValue(ozetOlustur("acik"));
    oturum.kilitle.mockRejectedValue(new ApiError(423, "locked", "Kayıtlar kilitli."));
    bas();

    await kullanici.click(await screen.findByRole("button", { name: "Kilitle" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(screen.queryByText("Kilitlenemedi.")).toBeNull();
  });
});

describe("OturumGostergesi — açık oturum yokken", () => {
  it.each<OturumDurumAdi>(["kilitli", "kurulum", "guvenlik_dosyasi_kayip"])(
    "%s durumunda gösterge boştur ve kısayol etkisizdir",
    async (durum) => {
      oturum.ozet.mockResolvedValue(ozetOlustur(durum));
      bas();
      await waitFor(() => expect(oturum.ozet).toHaveBeenCalled());
      await act(async () => {});
      expect(screen.queryByRole("group", { name: "Oturum" })).toBeNull();
      fireEvent.keyDown(window, { key: "L", ctrlKey: true, shiftKey: true });
      expect(oturum.kilitle).not.toHaveBeenCalled();
    },
  );

  it("oturum okunamazsa gösterge boştur", async () => {
    oturum.ozet.mockRejectedValue(new Error("ağ yok"));
    bas();
    await waitFor(() => expect(oturum.ozet).toHaveBeenCalled());
    expect(screen.queryByRole("group", { name: "Oturum" })).toBeNull();
  });
});
