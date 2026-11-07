// Kabuğun görünüm sözleşmesi (gerçek pencere sınaması 07.11.2026). jsdom yerleşim ölçmez ve
// Tailwind çıktısını uygulamaz: bu dosya görünümü doğuran SINIF ve YAPIYI sınar, gözle doğrulama
// pakette yapılır. Yerleşimin kendisi (konum, taşma, renk) burada ölçülemez.
//
// (1) Üst çubuktan açılan pencere üst çubuğun dışına çizilir. (2) Kenar çubuğu kısa pencerede kendi
// içinde kayar, çekmece açıkken arka sayfa kaymaz. (3) "Tema" satırının tamamı basılır.
// (4) Kenar çubuğu düğmelerinde renk sınıfı çakışmaz. (5) Sayfa değişince kaydırma başa döner,
// sekme değişiminde dokunulmaz.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Oturum göstergesi ve güncelleme bandı sunucu ister; bu dosyanın konusu değildir.
vi.mock("./modules/oturum/OturumGostergesi", () => ({ default: () => null }));
vi.mock("./modules/guncelleme/UpdateBanner", () => ({ default: () => null }));

import AppShell from "./AppShell";
import { useCapayaKaydir } from "./modules/kilavuz/KilavuzKabugu";

function Gezinti() {
  const git = useNavigate();
  return (
    <>
      <button type="button" onClick={() => git("/kisiler")}>
        başka sayfa
      </button>
      <button type="button" onClick={() => git("/")}>
        ana sayfa
      </button>
      <button type="button" onClick={() => git("/?tab=ikinci")}>
        aynı sayfada sekme
      </button>
      <button type="button" onClick={() => git("/#bolum")}>
        aynı sayfada çapa
      </button>
      <button type="button" onClick={() => git("/kilavuz#bolum")}>
        kılavuzun bölümü
      </button>
    </>
  );
}

/** Kılavuz sayfasının kaydırma kancasını taşıyan en küçük sayfa. */
function KilavuzBolumu() {
  useCapayaKaydir();
  return <h2 id="bolum">Bölüm</h2>;
}

function kabuk() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <AppShell>
        <Gezinti />
        <Routes>
          <Route path="/kilavuz" element={<KilavuzBolumu />} />
          <Route path="*" element={null} />
        </Routes>
      </AppShell>
    </MemoryRouter>,
  );
}

/** Masaüstü kenar çubuğu: DOM'daki ilk `aside` (çekmece kabuğun sonunda çizilir). */
function kenarCubugu(): HTMLElement {
  return screen.getAllByRole("complementary")[0];
}

function cekmeceyiAc(kullanici: ReturnType<typeof userEvent.setup>) {
  return kullanici.click(screen.getByRole("button", { name: "Gezinme menüsünü aç" }));
}

/** Bir öğenin `text-on-*` renk sınıfları. */
function metinRenkleri(oge: HTMLElement): string[] {
  return [...oge.classList].filter((s) => s.startsWith("text-on-"));
}

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  vi.mocked(window.scrollTo).mockClear();
});

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

describe("Üst çubuktan açılan pencere", () => {
  // `backdrop-blur` taşıyan üst çubuk `fixed` konumu kendine bağlar: pencere içinde kalsaydı
  // 64 piksellik çubuğa göre ortalanır, başı ekranın üstünden taşardı.
  it("Çık penceresi üst çubuğun dışında, gövdede çizilir", async () => {
    const kullanici = userEvent.setup();
    kabuk();

    const ustCubuk = screen.getByRole("banner");
    await kullanici.click(within(ustCubuk).getByRole("button", { name: "Çık" }));

    const pencere = screen.getByRole("dialog", { name: "Programdan çıkılsın mı?" });
    expect(ustCubuk).not.toContainElement(pencere);
    expect(pencere.parentElement?.parentElement).toBe(document.body);
  });
});

describe("Kenar çubuğunun kaydırılması", () => {
  /** Öğeyi saran kaydırma kabı. */
  function kaydirmaKabi(oge: HTMLElement): HTMLElement {
    const kap = oge.closest<HTMLElement>(".overflow-y-auto");
    if (kap === null) throw new Error("kaydırma kabı yok");
    return kap;
  }

  it("masaüstü kenar çubuğu kendi içinde kayar; daraltma düğmesi kabın dışındadır", () => {
    kabuk();
    const kenar = kenarCubugu();
    const kap = kaydirmaKabi(within(kenar).getByRole("navigation", { name: "Ana gezinme" }));

    // `od-sidebar-scroll` kaydırma çubuğunun rengini kenar çubuğuna uydurur (`index.css`).
    expect(kap).toHaveClass("od-sidebar-scroll", "overscroll-contain", "min-h-0", "flex-1");
    expect(kap).toContainElement(within(kenar).getByText("Hakkında ve Lisans"));
    expect(kap).toContainElement(within(kenar).getByText("Tema"));
    // Aside'ın kendisi kaydırılsaydı kenardan taşan daraltma düğmesi kırpılırdı.
    expect(kenar).not.toHaveClass("overflow-y-auto");
    expect(kap).not.toContainElement(
      within(kenar).getByRole("button", { name: "Kenar çubuğunu daralt" }),
    );
  });

  it("açılan yan menü kendi içinde kayar ve Tema satırı kabın içindedir", async () => {
    const kullanici = userEvent.setup();
    kabuk();
    await cekmeceyiAc(kullanici);

    const cekmece = screen.getAllByRole("complementary")[1];
    const kap = kaydirmaKabi(within(cekmece).getByRole("navigation", { name: "Ana gezinme" }));
    expect(kap).toHaveClass("overscroll-contain");
    expect(kap).toContainElement(within(cekmece).getByText("Tema"));
  });

  it("yan menü açıkken arka sayfa kaymaz, kapanınca kilit kalkar", async () => {
    const kullanici = userEvent.setup();
    kabuk();
    const kok = document.documentElement;
    expect(kok).not.toHaveClass("max-lg:overflow-hidden");

    await cekmeceyiAc(kullanici);
    // Kilit yalnız çekmecenin göründüğü genişlikte geçerlidir: açıkken pencere büyütülürse
    // çekmece gizlenir, sayfa kilitli kalmaz.
    expect(kok).toHaveClass("max-lg:overflow-hidden");

    await kullanici.click(screen.getByRole("button", { name: "Gezinme menüsünü kapat" }));
    expect(kok).not.toHaveClass("max-lg:overflow-hidden");
  });

  it("kabuk kalkarsa kilit de kalkar", async () => {
    const kullanici = userEvent.setup();
    const { unmount } = kabuk();
    await cekmeceyiAc(kullanici);

    unmount();

    expect(document.documentElement).not.toHaveClass("max-lg:overflow-hidden");
  });
});

describe("Tema satırı", () => {
  it("yazısı düğmenin içindedir: satırın tamamı basılır", async () => {
    const kullanici = userEvent.setup();
    kabuk();
    const kenar = kenarCubugu();

    const dugme = within(kenar).getByRole("button", { name: "Karanlık temaya geç" });
    expect(dugme).toContainElement(within(kenar).getByText("Tema"));
    expect(dugme).toHaveClass("w-full");

    await kullanici.click(within(kenar).getByText("Tema"));

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(within(kenar).getByRole("button", { name: "Açık temaya geç" })).toBeInTheDocument();
  });

  it("daralmış kenar çubuğunda yazı yoktur, erişilebilir ad kalır", async () => {
    const kullanici = userEvent.setup();
    kabuk();
    const kenar = kenarCubugu();

    await kullanici.click(within(kenar).getByRole("button", { name: "Kenar çubuğunu daralt" }));

    expect(within(kenar).queryByText("Tema")).toBeNull();
    expect(within(kenar).getByRole("button", { name: "Karanlık temaya geç" })).toBeInTheDocument();
  });
});

describe("Kenar çubuğu düğmelerinin rengi", () => {
  // Kenar çubuğu iki temada da koyudur. Bileşenin kendi `text-on-surface-variant`i kenar çubuğu
  // rengiyle yan yana durursa kazananı sınıf sırası değil Tailwind çıktısının sırası belirler:
  // açık temada koyu gri yazı koyu zemine düşüyordu.
  it("yoğunluk ve tema düğmesi Hakkında bağlantısıyla aynı renktedir, başka renk taşımaz", () => {
    kabuk();
    const kenar = kenarCubugu();
    const hakkinda = within(kenar).getByRole("link", { name: "Hakkında ve Lisans" });
    const yogunluk = within(kenar).getByRole("button", { name: "Rahat görünüme geç" });
    const tema = within(kenar).getByRole("button", { name: "Karanlık temaya geç" });

    expect(metinRenkleri(hakkinda)).toEqual(["text-on-sidebar-muted"]);
    for (const dugme of [yogunluk, tema]) {
      expect(metinRenkleri(dugme)).toEqual(["text-on-sidebar-muted"]);
      expect(dugme).toHaveClass("hover:text-on-sidebar", "hover:bg-on-sidebar/8");
      expect(dugme).not.toHaveClass("hover:text-on-surface");
      expect(dugme).not.toHaveClass("hover:bg-on-surface/8");
    }
  });
});

describe("Sayfa değişince kaydırma", () => {
  it("ilk açılışta kaydırmaya dokunulmaz", () => {
    kabuk();
    expect(window.scrollTo).not.toHaveBeenCalled();
  });

  it("adres yolu değişince sayfa başa döner", async () => {
    const kullanici = userEvent.setup();
    kabuk();

    await kullanici.click(screen.getByRole("button", { name: "başka sayfa" }));

    expect(screen.getByRole("banner")).toHaveTextContent("Kişiler");
    expect(window.scrollTo).toHaveBeenCalledTimes(1);
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it("geri dönüşte de başa döner (A → B → A)", async () => {
    const kullanici = userEvent.setup();
    kabuk();

    await kullanici.click(screen.getByRole("button", { name: "başka sayfa" }));
    await kullanici.click(screen.getByRole("button", { name: "ana sayfa" }));

    expect(window.scrollTo).toHaveBeenCalledTimes(2);
  });

  it("çapalı gelişte önce başa döner, sonra bölüme gider", async () => {
    const olaylar: string[] = [];
    vi.mocked(window.scrollTo).mockImplementationOnce(() => {
      olaylar.push("baş");
    });
    const asil = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = () => {
      olaylar.push("bölüm");
    };
    const kullanici = userEvent.setup();
    kabuk();

    await kullanici.click(screen.getByRole("button", { name: "kılavuzun bölümü" }));

    Element.prototype.scrollIntoView = asil;
    expect(olaylar).toEqual(["baş", "bölüm"]);
  });

  it("aynı sayfadaki sekme ve çapa değişiminde kaydırmaya dokunulmaz", async () => {
    const kullanici = userEvent.setup();
    kabuk();

    await kullanici.click(screen.getByRole("button", { name: "aynı sayfada sekme" }));
    await kullanici.click(screen.getByRole("button", { name: "aynı sayfada çapa" }));

    expect(window.scrollTo).not.toHaveBeenCalled();
  });
});
