// Tur 57 — M3 Dialog davranış testi: açık/kapalı render, ESC + scrim kapatma,
// rol=dialog + aria-modal, başlık + eylem alanı. React Testing Library + Vitest.

import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRef, useState } from "react";
import { describe, expect, it, vi } from "vitest";

import Button from "./Button";
import Dialog from "./Dialog";
import TextField from "./TextField";

/** Gerçek kullanım kalıbı: bir buton dialogu açar, dialog kendini kapatır. */
function AcKapa() {
  const [acik, setAcik] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setAcik(true)}>
        Aç
      </button>
      <Dialog open={acik} onClose={() => setAcik(false)} title="Onay">
        İçerik
      </Dialog>
    </>
  );
}

describe("Dialog", () => {
  it("kapalıyken hiçbir şey basmaz", () => {
    render(
      <Dialog open={false} onClose={() => {}} title="Onay">
        İçerik
      </Dialog>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("açıkken başlık + içeriği rol=dialog + aria-modal ile basar", () => {
    render(
      <Dialog open onClose={() => {}} title="Sınıf Atlatma">
        Emin misiniz?
      </Dialog>,
    );
    const dlg = screen.getByRole("dialog");
    expect(dlg).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("heading", { name: "Sınıf Atlatma" })).toBeInTheDocument();
    expect(screen.getByText("Emin misiniz?")).toBeInTheDocument();
  });

  it("ESC tuşu onClose çağırır", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Dialog open onClose={onClose} title="Onay">
        İçerik
      </Dialog>,
    );
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("scrim'e tıklama onClose çağırır, panele tıklama çağırmaz", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Dialog open onClose={onClose} title="Onay">
        İçerik
      </Dialog>,
    );
    await user.click(screen.getByRole("heading", { name: "Onay" }));
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.mouseDown(screen.getByRole("dialog").parentElement as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // WCAG 2.4.3 (odak sırası): modal kapanınca odak, onu AÇAN öğeye döner.
  // Aksi halde odak <body>'ye düşer ve klavye kullanıcısı sekmeye sayfanın
  // en başından başlar — bulunduğu yeri kaybeder (B6).
  it("kapanışta odağı dialogu açan öğeye geri verir", async () => {
    const user = userEvent.setup();
    render(<AcKapa />);
    const acici = screen.getByRole("button", { name: "Aç" });

    await user.click(acici);
    expect(screen.getByRole("dialog")).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(acici).toHaveFocus();
  });

  it("açan öğe DOM'dan kalktıysa odak geri verilmeye çalışılmaz (çökmez)", async () => {
    const user = userEvent.setup();
    const { unmount } = render(<AcKapa />);
    await user.click(screen.getByRole("button", { name: "Aç" }));
    expect(screen.getByRole("dialog")).toHaveFocus();
    expect(() => unmount()).not.toThrow();
  });

  it("actions alanı verilen butonları basar", () => {
    render(
      <Dialog open onClose={() => {}} title="Onay" actions={<Button>Uygula</Button>}>
        İçerik
      </Dialog>,
    );
    expect(screen.getByRole("button", { name: "Uygula" })).toBeInTheDocument();
  });
});

// Gerçek pencere sınaması (07.11.2026): `fixed`, atasında `backdrop-filter` varsa ekrana değil o
// ataya göre konumlanır. Üst çubuktan açılan pencere çubuğa göre ortalanıp başı kesiliyordu; pencere
// bu yüzden nereden açılırsa açılsın gövdeye çizilir.
describe("Dialog — gövdeye çizim", () => {
  it("üst çubuğun içinden açılsa da document.body'ye çizilir", () => {
    const { container } = render(
      <header className="backdrop-blur-md">
        <Dialog open onClose={() => undefined} title="Onay">
          İçerik
        </Dialog>
      </header>,
    );

    const pencere = screen.getByRole("dialog");
    expect(pencere.parentElement?.parentElement).toBe(document.body);
    expect(container).not.toContainElement(pencere);
    expect(pencere.closest("header")).toBeNull();
  });

  it("kapanınca gövdede iz bırakmaz", async () => {
    const user = userEvent.setup();
    render(<AcKapa />);
    const oncekiCocuklar = document.body.childElementCount;

    await user.click(screen.getByRole("button", { name: "Aç" }));
    expect(document.body.childElementCount).toBe(oncekiCocuklar + 1);

    await user.keyboard("{Escape}");
    expect(document.body.childElementCount).toBe(oncekiCocuklar);
  });

  it("katman sırası korunur: olağan pencere z-50, kapanış penceresi z-[70]", () => {
    const { rerender } = render(
      <Dialog open onClose={() => undefined} title="Onay">
        İçerik
      </Dialog>,
    );
    expect(screen.getByRole("dialog").parentElement).toHaveClass("fixed", "inset-0", "z-50");

    rerender(
      <Dialog open onClose={() => undefined} title="Onay" enUstte>
        İçerik
      </Dialog>,
    );
    expect(screen.getByRole("dialog").parentElement).toHaveClass("z-[70]");
  });

  it("pencere gövdedeyken odak tuzağı içerideki öğelerde döner", async () => {
    const user = userEvent.setup();
    render(
      <header className="backdrop-blur-md">
        <button type="button">Dışarıdaki</button>
        <Dialog open onClose={() => undefined} title="Tuzak">
          <button type="button">Tek</button>
        </Dialog>
      </header>,
    );

    await user.keyboard("{Tab}");
    expect(screen.getByRole("button", { name: "Tek" })).toHaveFocus();
    await user.keyboard("{Tab}");
    expect(screen.getByRole("button", { name: "Tek" })).toHaveFocus();
  });
});

it("Tab odak tuzağı: son öğeden ilkine, Shift+Tab ilkinden sonuncuya sarar (F29)", async () => {
  const user = userEvent.setup();
  render(
    <Dialog open onClose={() => undefined} title="Tuzak">
      <button type="button">İlk</button>
      <button type="button">Orta</button>
      <button type="button">Son</button>
    </Dialog>,
  );
  const ilk = screen.getByRole("button", { name: "İlk" });
  const son = screen.getByRole("button", { name: "Son" });

  // Panel odaklıyken Shift+Tab → son öğeye sarar (dışarı çıkmaz).
  await user.keyboard("{Shift>}{Tab}{/Shift}");
  expect(son).toHaveFocus();

  // Son öğedeyken Tab → ilk öğeye sarar.
  await user.keyboard("{Tab}");
  expect(ilk).toHaveFocus();

  // İlk öğedeyken Shift+Tab → tekrar sona sarar.
  await user.keyboard("{Shift>}{Tab}{/Shift}");
  expect(son).toHaveFocus();
});

/** Parola penceresi kalıbı: açılışta parola alanı odakta olmalı (`initialFocusRef`). */
function ParolaPenceresi({ alanliMi = true }: { alanliMi?: boolean }) {
  const [acik, setAcik] = useState(false);
  const [parola, setParola] = useState("");
  const alan = useRef<HTMLInputElement>(null);
  return (
    <>
      <button type="button" onClick={() => setAcik(true)}>
        Aç
      </button>
      {/* onClose her render'da YENİ işlevdir: yazı yazarken efekt yeniden koşmamalı. */}
      <Dialog open={acik} onClose={() => setAcik(false)} title="Parola" initialFocusRef={alan}>
        {alanliMi && (
          <TextField
            ref={alan}
            label="Parolanız"
            type="password"
            value={parola}
            onChange={(e) => setParola(e.target.value)}
          />
        )}
        <button type="button">Başka</button>
      </Dialog>
    </>
  );
}

describe("Dialog — ilk odak (initialFocusRef)", () => {
  it("açılışta verilen alan odaktadır, kapanışta odak açan öğeye döner", async () => {
    const user = userEvent.setup();
    render(<ParolaPenceresi />);
    const acici = screen.getByRole("button", { name: "Aç" });

    await user.click(acici);
    expect(screen.getByLabelText("Parolanız")).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(acici).toHaveFocus();
  });

  it("yazı yazarken odak alanda kalır (efekt yalnız açılışta koşar)", async () => {
    const user = userEvent.setup();
    render(<ParolaPenceresi />);
    await user.click(screen.getByRole("button", { name: "Aç" }));

    await user.keyboard("Gizli-Parola-1");

    const alan = screen.getByLabelText("Parolanız");
    expect(alan).toHaveValue("Gizli-Parola-1");
    expect(alan).toHaveFocus();
  });

  it("ref boşsa (alan basılmadı) odak panele alınır", async () => {
    const user = userEvent.setup();
    render(<ParolaPenceresi alanliMi={false} />);
    await user.click(screen.getByRole("button", { name: "Aç" }));
    expect(screen.getByRole("dialog")).toHaveFocus();
  });

  // Kaynak taraması: `autoFocus` Dialog içinde etkisizdir (açılış efekti odağı panele
  // alır) ve açan öğenin kaydını bozar (kapanışta odak geri verilemez). İlk odak
  // `initialFocusRef` ile verilir. Tarama bütün kaynak ağacını okur; süre açıkça
  // verilir (format.test.ts'teki tarih taramasıyla aynı kalıp).
  it("ui/Dialog kullanan dosyalarda autoFocus yok", async () => {
    const { readdirSync, readFileSync } = await import("node:fs");
    const { join } = await import("node:path");

    const suclular: string[] = [];
    const tara = (dizin: string): void => {
      for (const girdi of readdirSync(dizin, { withFileTypes: true })) {
        const yol = join(dizin, girdi.name);
        if (girdi.isDirectory()) {
          tara(yol);
        } else if (/\.tsx$/.test(girdi.name) && !girdi.name.includes(".test.")) {
          const metin = readFileSync(yol, "utf8");
          const dialogKullanir = /from "(\.\.\/)*(ui\/|\.\/)Dialog"/.test(metin);
          if (dialogKullanir && /\sautoFocus(\s*=|\s*\/?>|\s*$)/m.test(metin)) {
            suclular.push(yol);
          }
        }
      }
    };
    tara(join(__dirname, ".."));

    expect(suclular).toEqual([]);
  }, 60_000);
});
