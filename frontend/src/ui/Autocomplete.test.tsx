// Autocomplete — ARIA 1.2 combobox sözleşmesi (aile iskeletinin 18.09.2026 değerlendirmesi):
// rol ve durum öznitelikleri SARMALAYICI div'de değil, odağı alan INPUT'tadır.
// Seçim/klavye davranışı da burada sabitlenir (bileşenin ilk birim testi).

import { useState } from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import Autocomplete from "./Autocomplete";
import Dialog from "./Dialog";

interface Kisi {
  id: number;
  ad: string;
  ayrildi?: boolean;
}

// KVKK: adlar uydurmadır.
const KISILER: Kisi[] = [
  { id: 1, ad: "Ayşe Yılmaz" },
  { id: 2, ad: "Ayhan Demir", ayrildi: true },
  { id: 3, ad: "Aylin Kaya" },
];

const search = (q: string) =>
  Promise.resolve(
    KISILER.filter((k) => k.ad.toLocaleLowerCase("tr").includes(q.toLocaleLowerCase("tr"))),
  );

/** Gerçek kullanımın aynası: seçim ebeveynde tutulur, seçilince alan chip'e döner. */
function Alan({
  label,
  ariaLabel,
  onSelect,
}: {
  label: string;
  ariaLabel?: string;
  onSelect: (k: Kisi) => void;
}) {
  const [secili, setSecili] = useState<Kisi | null>(null);
  return (
    <Autocomplete<Kisi>
      label={label}
      ariaLabel={ariaLabel}
      selected={secili}
      search={search}
      onSelect={(k) => {
        setSecili(k);
        onSelect(k);
      }}
      onClear={() => setSecili(null)}
      getKey={(k) => k.id}
      getLabel={(k) => k.ad}
      getDisabled={(k) => (k.ayrildi ? "ayrıldı" : undefined)}
      minChars={1}
      debounceMs={0}
    />
  );
}

function renderAlan(props: { label?: string; ariaLabel?: string } = {}) {
  const onSelect = vi.fn();
  render(
    <Alan label={props.label ?? "Öğretmen"} ariaLabel={props.ariaLabel} onSelect={onSelect} />,
  );
  return { onSelect };
}

describe("Autocomplete — ARIA 1.2 combobox", () => {
  it("rol INPUT'tadır: etiketle bulunan alan combobox'tır, sarmalayıcı rol taşımaz", () => {
    renderAlan();

    const alan = screen.getByLabelText(/Öğretmen/);
    expect(alan.tagName).toBe("INPUT");
    expect(alan).toHaveAttribute("role", "combobox");
    expect(alan).toHaveAttribute("aria-haspopup", "listbox");
    expect(alan).toHaveAttribute("aria-autocomplete", "list");
    // Tek combobox vardır ve o da input'tur (eski desende rol div'deydi).
    expect(screen.getAllByRole("combobox")).toEqual([alan]);
    expect(alan.parentElement).not.toHaveAttribute("role");
  });

  it("kapalıyken aria-expanded=false ve aria-controls yok; açılınca listeye işaret eder", async () => {
    const user = userEvent.setup();
    renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    expect(alan).toHaveAttribute("aria-expanded", "false");
    expect(alan).not.toHaveAttribute("aria-controls");

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    expect(alan).toHaveAttribute("aria-expanded", "true");
    expect(alan).toHaveAttribute("aria-controls", liste.id);
    expect(within(liste).getAllByRole("option")).toHaveLength(3);
  });

  it("ok tuşlarıyla vurgu aria-activedescendant ile izlenir; Enter seçer ve liste kapanır", async () => {
    const user = userEvent.setup();
    const { onSelect } = renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    await user.type(alan, "ay");
    const secenekler = within(await screen.findByRole("listbox")).getAllByRole("option");
    expect(alan).toHaveAttribute("aria-activedescendant", secenekler[0].id);

    await user.keyboard("{ArrowDown}{ArrowDown}");
    expect(alan).toHaveAttribute("aria-activedescendant", secenekler[2].id);
    expect(secenekler[2]).toHaveAttribute("aria-selected", "true");

    await user.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledWith(KISILER[2]);
    // Seçimden sonra liste kapanır ve alan seçili chip'e döner.
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
    expect(screen.getByText("Aylin Kaya")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Seçimi temizle" })).toBeInTheDocument();
  });

  it("seçilemeyen öğe görünür ama ne tıkla ne Enter ile seçilir (neden etiketiyle)", async () => {
    const user = userEvent.setup();
    const { onSelect } = renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    await user.type(alan, "ayhan");
    const secenek = await screen.findByRole("option", { name: /Ayhan Demir/ });
    expect(secenek).toHaveAttribute("aria-disabled", "true");
    expect(within(secenek).getByText(/ayrıldı/)).toBeInTheDocument();

    await user.click(secenek);
    await user.keyboard("{Enter}");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("Escape listeyi kapatır", async () => {
    const user = userEvent.setup();
    renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    await user.type(alan, "ay");
    await screen.findByRole("listbox");
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(alan).toHaveAttribute("aria-expanded", "false");
  });

  it("görsel etiket yokken erişilebilir ad ariaLabel'dan gelir", () => {
    renderAlan({ label: "", ariaLabel: "Toplantıya katılacak öğretmeni seçin" });
    expect(
      screen.getByRole("combobox", { name: "Toplantıya katılacak öğretmeni seçin" }),
    ).toBeInTheDocument();
  });
});

// Öneri listesi kapsayıcının kaydırma alanında kırpılmasın diye bileşenin dışına çizilir
// (Windows sınaması 12.11.2026: tek alanlı "Personelden ekle" penceresinde liste pencere
// gövdesinin kaydırma alanında kalıyor, yalnız bir satırı görünüyordu).
describe("Autocomplete — liste kırpılmaz (kapsayıcının dışına çizilir)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  /** Alanın çerçevesinin (girişin sarmalayıcısı) ekrandaki yerini sabitler; ötekiler 0. */
  function alanKonumu(alan: HTMLElement, kutu: { top: number; left: number; width: number }) {
    const yukseklik = 56;
    let k = kutu;
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this !== alan.parentElement) return new DOMRect(0, 0, 0, 0);
      return new DOMRect(k.left, k.top, k.width, yukseklik);
    });
    return (yeni: typeof kutu) => {
      k = yeni;
    };
  }

  function PenceredeAlan({
    onClose,
    onSelect,
  }: {
    onClose: () => void;
    onSelect: (k: Kisi) => void;
  }) {
    return (
      <Dialog open onClose={onClose} title="Personelden ekle">
        <Alan label="Personel" onSelect={onSelect} />
      </Dialog>
    );
  }

  function renderPencere() {
    const onClose = vi.fn();
    const onSelect = vi.fn();
    render(<PenceredeAlan onClose={onClose} onSelect={onSelect} />);
    return { onClose, onSelect };
  }

  it("sayfa içinde liste gövdeye, alanın sarmalayıcısının dışına ve fixed konumla çizilir", async () => {
    const user = userEvent.setup();
    renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    expect(liste.parentElement).toBe(document.body);
    expect(alan.closest("div.relative")?.contains(liste)).toBe(false);
    expect(liste.style.position).toBe("fixed");
    // ARIA sözleşmesi taşınmada bozulmaz.
    expect(alan).toHaveAttribute("aria-controls", liste.id);
  });

  it("pencere içinde liste pencere gövdesinin (kaydırma alanı) dışında, pencere öğesinin içinde çizilir", async () => {
    const user = userEvent.setup();
    renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });
    const pencere = screen.getByRole("dialog", { name: "Personelden ekle" });
    const govde = alan.closest<HTMLElement>("[role=dialog] > div.overflow-y-auto");
    expect(govde).not.toBeNull();

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    expect(govde?.contains(liste)).toBe(false);
    // aria-modal pencerenin dışı yardımcı teknolojide görünmez: liste pencere öğesinde kalır.
    expect(pencere.contains(liste)).toBe(true);
    expect(liste.style.position).toBe("fixed");
    expect(within(pencere).getAllByRole("option")).toHaveLength(3);
  });

  it("pencere içinde seçeneğe tıklamak seçer, pencereyi kapatmaz", async () => {
    const user = userEvent.setup();
    const { onClose, onSelect } = renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });

    await user.type(alan, "ay");
    // Ad, vurgu (`mark`) yüzünden jsdom'da bölünür; seçenek sırasıyla alınır.
    const secenekler = within(await screen.findByRole("listbox")).getAllByRole("option");
    expect(secenekler[2]).toHaveTextContent("Aylin Kaya");
    await user.click(secenekler[2]);
    expect(onSelect).toHaveBeenCalledWith(KISILER[2]);
    expect(onClose).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
    expect(screen.getByRole("dialog", { name: "Personelden ekle" })).toBeInTheDocument();
  });

  it("pencere içinde klavye: ↓ ↑ vurguyu gezdirir, Enter seçer; pencere kapanmaz", async () => {
    const user = userEvent.setup();
    const { onClose, onSelect } = renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });

    await user.type(alan, "ay");
    const secenekler = within(await screen.findByRole("listbox")).getAllByRole("option");
    await user.keyboard("{ArrowDown}{ArrowDown}{ArrowUp}");
    expect(alan).toHaveAttribute("aria-activedescendant", secenekler[1].id);
    await user.keyboard("{ArrowDown}{Enter}");
    expect(onSelect).toHaveBeenCalledWith(KISILER[2]);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("listenin kendisine basmak dışarı tıklama sayılmaz; dışarı basınca liste kapanır, pencere kalır", async () => {
    const user = userEvent.setup();
    const { onClose } = renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    // Listenin boşluğu ya da kaydırma çubuğu: liste açık kalır.
    fireEvent.mouseDown(liste);
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    // Pencerenin başlığına basmak dışarıdır: liste kapanır, pencere açık kalır.
    fireEvent.mouseDown(screen.getByRole("heading", { name: "Personelden ekle" }));
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
    expect(onClose).not.toHaveBeenCalled();
  });

  it("sayfa içinde dışarı basınca liste kapanır", async () => {
    const user = userEvent.setup();
    renderAlan();
    const alan = screen.getByRole("combobox", { name: /Öğretmen/ });

    await user.type(alan, "ay");
    await screen.findByRole("listbox");
    fireEvent.mouseDown(document.body);
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
  });

  it("konum alanın altından ve alan genişliğinde hesaplanır; kaydırmada yeniden hesaplanır", async () => {
    const user = userEvent.setup();
    renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });
    const tasi = alanKonumu(alan, { top: 100, left: 40, width: 320 });

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    // 100 + 56 (alan) + 4 (aralık)
    expect(liste.style.top).toBe("160px");
    expect(liste.style.left).toBe("40px");
    expect(liste.style.width).toBe("320px");

    // Pencere gövdesi kaydırılınca liste alanla birlikte yer değiştirir.
    tasi({ top: 60, left: 40, width: 320 });
    const govde = alan.closest<HTMLElement>("[role=dialog] > div.overflow-y-auto");
    fireEvent.scroll(govde as HTMLElement);
    await waitFor(() => expect(liste.style.top).toBe("120px"));

    // Pencere boyutu değişince de.
    tasi({ top: 80, left: 10, width: 200 });
    fireEvent(window, new Event("resize"));
    await waitFor(() => expect(liste.style.top).toBe("140px"));
    expect(liste.style.left).toBe("10px");
    expect(liste.style.width).toBe("200px");
  });

  it("altta yer yetmiyorsa liste alanın üstüne açılır", async () => {
    const user = userEvent.setup();
    renderPencere();
    const alan = screen.getByRole("combobox", { name: /Personel/ });
    // Alan ekranın dibinde: altta ~40 px, üstte yüzlerce px yer var.
    alanKonumu(alan, { top: window.innerHeight - 100, left: 40, width: 320 });
    vi.spyOn(Element.prototype, "scrollHeight", "get").mockReturnValue(200);

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    expect(liste.style.top).toBe("");
    // Liste alanın üst kenarının 4 px üstünde biter.
    expect(liste.style.bottom).toBe("104px");
  });
});

// Liste kırpılmadığı için alan kaydırma alanının görünen yerinden çıkınca liste başlığın, eylem
// şeridinin ya da pencerenin dışında asılı kalıyordu (bağımsız denetim 12.11.2026). Alan görünen
// yerin tamamen dışına çıkınca liste kapanır; kısmen görünürken görünen kenarına bağlanır.
describe("Autocomplete — alan kaydırma alanından çıkınca liste asılı kalmaz", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  const ALAN_YUKSEKLIGI = 56;
  // Pencere gövdesinin (kaydırma alanı) ekrandaki yeri: 80 ile 380 arası.
  const GOVDE = new DOMRect(0, 80, 600, 300);

  /** Alanın ve pencere gövdesinin yerini sabitler. jsdom CSS yüklemez: gövdenin kaydırma
   *  özelliği satır içi biçemle verilir (gerçekte `overflow-y-auto` sınıfı). */
  function yerlesim(alan: HTMLElement, govde: HTMLElement, ilkTop: number) {
    govde.style.overflowY = "auto";
    let top = ilkTop;
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      if (this === alan.parentElement) return new DOMRect(40, top, 320, ALAN_YUKSEKLIGI);
      if (this === govde) return GOVDE;
      return new DOMRect(0, 0, 0, 0);
    });
    return (yeniTop: number) => {
      top = yeniTop;
      fireEvent.scroll(govde);
    };
  }

  function renderPencere() {
    const onClose = vi.fn();
    render(
      <Dialog open onClose={onClose} title="Görevdeki üyeyi ekle">
        <Alan label="Üye" onSelect={vi.fn()} />
      </Dialog>,
    );
    const alan = screen.getByRole("combobox", { name: /Üye/ });
    const govde = alan.closest<HTMLElement>("[role=dialog] > div.overflow-y-auto");
    expect(govde).not.toBeNull();
    return { onClose, alan, govde: govde as HTMLElement };
  }

  it("alan gövdenin üstünden çıkınca (başlığın arkasına geçince) liste kapanır, pencere kalır", async () => {
    const user = userEvent.setup();
    const { onClose, alan, govde } = renderPencere();
    const kaydir = yerlesim(alan, govde, 100);

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");
    expect(liste.style.top).toBe("160px");

    // Alanın alt kenarı gövdenin üst kenarının (80) üstünde: alan görünmez.
    kaydir(10);
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
    expect(alan).toHaveAttribute("aria-expanded", "false");
    expect(alan).not.toHaveAttribute("aria-activedescendant");
    expect(onClose).not.toHaveBeenCalled();

    // Geri kaydırılınca ↓ listeyi aynı sonuçlarla yeniden açar.
    kaydir(100);
    await user.keyboard("{ArrowDown}");
    expect(await screen.findByRole("listbox")).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(3);
  });

  it("alan gövdenin altından çıkınca (eylem şeridinin arkasına geçince) liste kapanır", async () => {
    const user = userEvent.setup();
    const { alan, govde } = renderPencere();
    const kaydir = yerlesim(alan, govde, 100);

    await user.type(alan, "ay");
    await screen.findByRole("listbox");

    // Alanın üst kenarı gövdenin alt kenarının (380) altında.
    kaydir(390);
    await waitFor(() => expect(screen.queryByRole("listbox")).not.toBeInTheDocument());
  });

  it("alan kısmen görünürken liste alanın görünen kenarına bağlanır", async () => {
    const user = userEvent.setup();
    const { alan, govde } = renderPencere();
    const kaydir = yerlesim(alan, govde, 100);

    await user.type(alan, "ay");
    const liste = await screen.findByRole("listbox");

    // Alan 350-406 arasında, gövde 380'de bitiyor: liste 380 + 4'ten başlar, gizli kısmın
    // altından (410) değil.
    kaydir(350);
    await waitFor(() => expect(liste.style.top).toBe("384px"));
    expect(screen.getByRole("listbox")).toBe(liste);

    // Üstten kısmen görünür (40-96, gövde 80'de başlıyor): görünen alt kenar 96, liste 100'de.
    kaydir(40);
    await waitFor(() => expect(liste.style.top).toBe("100px"));
  });
});
