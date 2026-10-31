// Yeniden başlat örtüsü: olay gelene kadar HİÇBİR ŞEY çizmez; olay gelince tam
// ekran, kapatılamaz yönlendirme gösterir (kapatma düğmesi bilinçli olarak yok
// — bayat oturumda çalışmaya davet olurdu).

import { act, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { yenidenBaslatGerekliYayinla } from "../../lib/restart";
import YenidenBaslatEkrani from "./YenidenBaslatEkrani";

describe("YenidenBaslatEkrani", () => {
  it("olay gelmeden görünmez, olayla tam ekran yönlendirme gösterir", () => {
    const { container } = render(<YenidenBaslatEkrani />);
    expect(container.firstChild).toBeNull();

    act(() => yenidenBaslatGerekliYayinla());

    const ekran = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ekran).toHaveTextContent("Programı kapatıp yeniden açın");
    expect(ekran).toHaveTextContent("db-onceki-");
    // Örtüyü kapatan düğme yok: tek çıkış programı yeniden başlatmaktır. Tek düğme
    // programdan çıkıştır (TB13: pencere süslemesi olmayan masaüstünün çıkış yolu).
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Programdan çık" })).toBeInTheDocument();
  });

  // T6: çarpı programı kapatır (desktop/window.py::on_closing); tepsi yoktur.
  it("çarpıyı ya da Çık düğmesini tarif eder, tepsiyi anlatmaz", () => {
    render(<YenidenBaslatEkrani />);
    act(() => yenidenBaslatGerekliYayinla());

    const ekran = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ekran).toHaveTextContent("pencerenin çarpı düğmesiyle");
    expect(ekran).not.toHaveTextContent("tepside");
  });
});
