// Ortak "uyarı + gerekçe" bileşeni (altın kural 3): hata gövdelerinin okunması (gerekçe, sert engel,
// kural paketi D1, dönem ve geçiş kilidi), madde atfının ayrılması, uyum satırının türleri (eksik gerekçe
// istemez), gerekçe kutusunun akışı (sunucu isteyince açılır, odak alana geçer ve uyarı alanın açıklaması
// olur, boşken istek gitmez, ikinci istek gerekçeyi taşır, toplu notu), yarım metnin yalnız kendi kutusunda
// silinmesi. Veriler uydurmadır.

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";

const yarimMetinMock = vi.hoisted(() => ({ oku: vi.fn(), kaydet: vi.fn(), temizle: vi.fn() }));
vi.mock("./api", () => ({ yarimMetinApi: yarimMetinMock }));
import { UyariGerekceAlani, UyumSatirlari, useUyariGerekce } from "./UyariGerekce";
import { atifAyir, uyumHatasiOku } from "./hatalar";
import {
  DONEM_KILIDI_BASLIGI,
  EKSIK_ACIKLAMASI,
  GEREKCE_BASLIGI,
  GEREKCE_ZORUNLU,
  KURAL_PAKETI_BASLIGI,
  KURAL_SERT_BASLIGI,
  SAPMA_ACIKLAMASI,
  SAPMA_GEREKCESIZ_ACIKLAMASI,
  TAKVIM_ACIKLAMASI,
  TOPLU_GEREKCE_NOTU,
} from "./metinler";

const UYARI =
  "Bu kişi yönetim kuruluna 5 defa seçilmiş görünüyor; en fazla 4 defa seçilebilir (md. 12/4).";

describe("atfın ayrılması", () => {
  it("sondaki madde atfı gövdeden ayrılır", () => {
    expect(atifAyir(UYARI)).toEqual({
      govde: "Bu kişi yönetim kuruluna 5 defa seçilmiş görünüyor; en fazla 4 defa seçilebilir.",
      atif: "md. 12/4",
    });
    expect(atifAyir("Kira ödenir (EK-2 md. 7).").atif).toBe("EK-2 md. 7");
    expect(atifAyir("Karar verilir (kullanıcı kararı A-2 (gerekçe md. 14/4)).").atif).toBe(
      "kullanıcı kararı A-2 (gerekçe md. 14/4)",
    );
  });

  it("atıf olmayan parantez ayrılmaz", () => {
    expect(atifAyir("Ad (okunamadı) yazılmadı.")).toEqual({
      govde: "Ad (okunamadı) yazılmadı.",
      atif: null,
    });
    expect(atifAyir("Atıfsız ileti.").atif).toBeNull();
  });
});

describe("hata gövdelerinin okunması", () => {
  it("400 gerekce_gerekli: önek atılır, uyarı ve atıf kalır", () => {
    const e = new ApiError(400, "gerekce_gerekli", `Bu kayıt için gerekçe yazılmalıdır. ${UYARI}`);
    expect(uyumHatasiOku(e)).toEqual({
      tur: "gerekce",
      metin: "Bu kişi yönetim kuruluna 5 defa seçilmiş görünüyor; en fazla 4 defa seçilebilir.",
      atif: "md. 12/4",
    });
    // Gövdesiz gerekçe isteğinde ileti olduğu gibi kalır.
    const bos = new ApiError(400, "gerekce_gerekli", "Bu kayıt için gerekçe yazılmalıdır.");
    expect(uyumHatasiOku(bos)?.metin).toBe("Bu kayıt için gerekçe yazılmalıdır.");
  });

  it("sert engel: kural_sert ya da atıflı 400; atıfsız 400 uyum hatası değildir", () => {
    expect(uyumHatasiOku(new ApiError(400, "kural_sert", "Kayıt yapılmadı."))?.tur).toBe("sert");
    expect(
      uyumHatasiOku(
        new ApiError(400, "invalid", "Okul müdürü yönetim kuruluna giremez (md. 12/1)."),
      ),
    ).toEqual({ tur: "sert", metin: "Okul müdürü yönetim kuruluna giremez.", atif: "md. 12/1" });
    expect(uyumHatasiOku(new ApiError(400, "invalid", "Bu alan zorunludur."))).toBeNull();
  });

  it("kural paketi (D1, D7), dönem ve geçiş kilidi; öteki hatalar null", () => {
    expect(uyumHatasiOku(new ApiError(503, "kural_paketi_yok", "x"))?.tur).toBe("paket");
    expect(uyumHatasiOku(new ApiError(503, "donem_kopyasi_dogrulanamadi", "x"))?.tur).toBe("paket");
    for (const kod of ["donem_kapali", "donem_salt_okur", "donem_yazilamaz", "gecis_kapali"]) {
      expect(uyumHatasiOku(new ApiError(409, kod, "x"))?.tur).toBe("donem");
    }
    expect(uyumHatasiOku(new ApiError(409, "parola_gerekli", "x"))).toBeNull();
    expect(uyumHatasiOku(new Error("ağ"))).toBeNull();
  });
});

describe("uyum satırları", () => {
  it("türün rozeti, açıklaması ve dayanağı; eksik gerekçe istemez", () => {
    render(
      <UyumSatirlari
        baslik="Uyarılar"
        satirlar={[
          { tur: "EKSIK", metin: "Bilgi girilmedi.", atif: "md. 12/4" },
          { tur: "SAPMA", metin: "Sapma var.", atif: "md. 23/2", gerekceli: true },
          { tur: "SAPMA", metin: "Açık sapma.", atif: null, gerekceli: false },
          { tur: "TAKVIM", metin: "Defter tasdiki.", atif: "md. 23/2" },
        ]}
      />,
    );
    const liste = screen.getByRole("list", { name: "Uyarılar" });
    expect(liste).toHaveTextContent("Eksik");
    expect(liste).toHaveTextContent(EKSIK_ACIKLAMASI);
    expect(liste).toHaveTextContent(SAPMA_ACIKLAMASI);
    expect(liste).toHaveTextContent(SAPMA_GEREKCESIZ_ACIKLAMASI);
    expect(liste).toHaveTextContent(TAKVIM_ACIKLAMASI);
    expect(screen.getAllByText("Dayanak: md. 23/2")).toHaveLength(2);
  });

  it("boş listede hiçbir şey çizilmez", () => {
    const { container } = render(<UyumSatirlari baslik="Uyarılar" satirlar={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

/** Akışı sürmek için küçük form: her gönderim `gonder`i ek alanla çağırır. */
function Form({
  gonder,
  toplu = false,
  baglam,
}: {
  gonder: (ek: object) => Promise<void>;
  toplu?: boolean;
  baglam?: string;
}) {
  const ug = useUyariGerekce(baglam);
  const [tamam, setTamam] = useState(false);
  return (
    <div>
      <UyariGerekceAlani durum={ug} toplu={toplu} />
      {tamam && <p>Kaydedildi</p>}
      <button
        type="button"
        onClick={async () => {
          if (!ug.hazir()) return;
          try {
            await gonder(ug.ek());
            ug.sifirla();
            setTamam(true);
          } catch (e) {
            if (!ug.yakala(e)) throw e;
          }
        }}
      >
        Gönder
      </button>
      <button type="button" onClick={() => ug.sifirla()}>
        Vazgeç
      </button>
    </div>
  );
}

describe("gerekçe akışı", () => {
  it("sunucu gerekçe isteyince kutu açılır; boşken istek gitmez; ikinci istek gerekçeyi taşır", async () => {
    const user = userEvent.setup();
    const gonder = vi
      .fn()
      .mockRejectedValueOnce(
        new ApiError(400, "gerekce_gerekli", `Bu kayıt için gerekçe yazılmalıdır. ${UYARI}`),
      )
      .mockResolvedValueOnce(undefined);
    render(<Form gonder={gonder} toplu />);

    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(gonder).toHaveBeenLastCalledWith({});
    const kutu = await screen.findByRole("group", { name: GEREKCE_BASLIGI });
    expect(kutu).toHaveTextContent("en fazla 4 defa seçilebilir.");
    expect(kutu).toHaveTextContent("Dayanak: md. 12/4");
    expect(kutu).toHaveTextContent(TOPLU_GEREKCE_NOTU);

    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(screen.getByRole("alert")).toHaveTextContent(GEREKCE_ZORUNLU);
    expect(gonder).toHaveBeenCalledTimes(1);

    await user.type(screen.getByLabelText(/Gerekçe/), "  Uydurma gerekçe  ");
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(gonder).toHaveBeenLastCalledWith({ gerekce: "Uydurma gerekçe" });
    expect(await screen.findByText("Kaydedildi")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: GEREKCE_BASLIGI })).toBeNull();
  });

  it("kutu açılınca odak gerekçe alanına geçer; alanın açıklaması uyarı ve dayanakla başlar", async () => {
    const user = userEvent.setup();
    const gonder = vi
      .fn()
      .mockRejectedValue(
        new ApiError(400, "gerekce_gerekli", `Bu kayıt için gerekçe yazılmalıdır. ${UYARI}`),
      );
    render(<Form gonder={gonder} />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    const alan = await screen.findByLabelText(/Gerekçe/);
    expect(alan).toHaveFocus();
    expect(alan).toHaveAccessibleDescription(/en fazla 4 defa seçilebilir\..*Dayanak: md\. 12\/4/);
    // Boş gönderimde alan hatası da açıklamaya girer.
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(screen.getByLabelText(/Gerekçe/)).toHaveAccessibleDescription(
      expect.stringContaining(GEREKCE_ZORUNLU),
    );
  });

  it.each([
    [new ApiError(400, "kural_sert", "Kural dışı (md. 12/1)."), KURAL_SERT_BASLIGI, "md. 12/1"],
    [new ApiError(503, "kural_paketi_yok", "Kural paketi okunamadı."), KURAL_PAKETI_BASLIGI, null],
    [new ApiError(409, "gecis_kapali", "Geçiş kurulumu tamamlandı."), DONEM_KILIDI_BASLIGI, null],
  ])(
    "öteki uyum hataları bant olarak görünür, gerekçe sorulmaz: %s",
    async (hata, baslik, atif) => {
      const user = userEvent.setup();
      render(<Form gonder={vi.fn().mockRejectedValue(hata)} />);
      await user.click(screen.getByRole("button", { name: "Gönder" }));
      const bant = await screen.findByRole("alert");
      expect(bant).toHaveTextContent(baslik);
      if (atif) expect(bant).toHaveTextContent(`Dayanak: ${atif}`);
      expect(screen.queryByRole("group", { name: GEREKCE_BASLIGI })).toBeNull();
    },
  );
});

describe("yarım metin", () => {
  const hata = () =>
    new ApiError(400, "gerekce_gerekli", `Bu kayıt için gerekçe yazılmalıdır. ${UYARI}`);

  beforeEach(() => {
    vi.clearAllMocks();
    yarimMetinMock.oku.mockResolvedValue(null);
    yarimMetinMock.kaydet.mockResolvedValue(undefined);
    yarimMetinMock.temizle.mockResolvedValue(undefined);
  });

  it("bağlamlı kutuda yazılan gerekçe sunucuya yazılır, kayıt yapılınca silinir", async () => {
    const user = userEvent.setup();
    const gonder = vi.fn().mockRejectedValueOnce(hata()).mockResolvedValueOnce(undefined);
    render(<Form gonder={gonder} baglam="deneme.baglam" />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    await user.type(await screen.findByLabelText(/Gerekçe/), "Uydurma");
    await waitFor(
      () => expect(yarimMetinMock.kaydet).toHaveBeenCalledWith("Uydurma", "deneme.baglam"),
      { timeout: 3000 },
    );
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(await screen.findByText("Kaydedildi")).toBeInTheDocument();
    // Silme yalnız bu kutunun bağlamıyla gider.
    expect(yarimMetinMock.temizle).toHaveBeenCalledTimes(1);
    expect(yarimMetinMock.temizle).toHaveBeenCalledWith("deneme.baglam");
  });

  it("yazmamış kutunun vazgeçişi ve kaydı başka kutunun yarım metnini silmez", async () => {
    const user = userEvent.setup();
    yarimMetinMock.oku.mockResolvedValue({
      metin: "Başka kutunun uydurma metni",
      baglam: "gecis.karar_defteri",
      guncelleme: "",
    });
    // Kutu hiç açılmadan başarılı kayıt ve vazgeç.
    render(<Form gonder={vi.fn().mockResolvedValue(undefined)} baglam="gecis.devralinan" />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(await screen.findByText("Kaydedildi")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Vazgeç" }));
    expect(yarimMetinMock.temizle).not.toHaveBeenCalled();
  });

  it("açılıp yazılmamış kutunun vazgeçişi de silmez; metnini geri getiren kutununki siler", async () => {
    const user = userEvent.setup();
    yarimMetinMock.oku.mockResolvedValue({
      metin: "Başka kutunun uydurma metni",
      baglam: "gecis.karar_defteri",
      guncelleme: "",
    });
    const { unmount } = render(
      <Form gonder={vi.fn().mockRejectedValue(hata())} baglam="gecis.devralinan" />,
    );
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    await screen.findByRole("group", { name: GEREKCE_BASLIGI });
    await waitFor(() => expect(yarimMetinMock.oku).toHaveBeenCalledTimes(1));
    await user.click(screen.getByRole("button", { name: "Vazgeç" }));
    expect(yarimMetinMock.temizle).not.toHaveBeenCalled();
    unmount();
    // Aynı bağlamın kutusu metni geri getirir; vazgeçince yalnız kendi bağlamıyla siler.
    render(<Form gonder={vi.fn().mockRejectedValue(hata())} baglam="gecis.karar_defteri" />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(await screen.findByDisplayValue("Başka kutunun uydurma metni")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Vazgeç" }));
    expect(yarimMetinMock.temizle).toHaveBeenCalledWith("gecis.karar_defteri");
  });

  it("aynı bağlamın yarım metni kutu açılınca geri gelir; başka bağlamınki gelmez", async () => {
    const user = userEvent.setup();
    yarimMetinMock.oku.mockResolvedValue({
      metin: "Yarım kalan uydurma",
      baglam: "deneme.baglam",
      guncelleme: "",
    });
    const { unmount } = render(
      <Form gonder={vi.fn().mockRejectedValue(hata())} baglam="deneme.baglam" />,
    );
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    expect(await screen.findByDisplayValue("Yarım kalan uydurma")).toBeInTheDocument();
    unmount();
    render(<Form gonder={vi.fn().mockRejectedValue(hata())} baglam="baska.baglam" />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    await screen.findByRole("group", { name: GEREKCE_BASLIGI });
    await waitFor(() => expect(yarimMetinMock.oku).toHaveBeenCalledTimes(2));
    expect(screen.queryByDisplayValue("Yarım kalan uydurma")).toBeNull();
  });

  it("bağlamsız kutu sunucuya yazmaz", async () => {
    const user = userEvent.setup();
    render(<Form gonder={vi.fn().mockRejectedValue(hata())} />);
    await user.click(screen.getByRole("button", { name: "Gönder" }));
    await user.type(await screen.findByLabelText(/Gerekçe/), "Uydurma");
    expect(yarimMetinMock.oku).not.toHaveBeenCalled();
    expect(yarimMetinMock.kaydet).not.toHaveBeenCalled();
  });
});
