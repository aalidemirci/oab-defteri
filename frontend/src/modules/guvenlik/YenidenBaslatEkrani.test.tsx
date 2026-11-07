// Yeniden başlat örtüsü: olay gelene kadar HİÇBİR ŞEY çizmez; olay gelince tam
// ekran, kapatılamaz yönlendirme gösterir (kapatma düğmesi bilinçli olarak yok
// — bayat oturumda çalışmaya davet olurdu). Geri yükleme olayla birlikte dosya raporunu verir:
// kapsam, kişisiz sayılar ve eksik ya da bozuk eklerin listesi görünür (plan F1b-3); sahte rapor
// `geri_yukleme_ekleri.DosyaRaporu.yanit` ile aynı biçimdedir.

import { act, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { yenidenBaslatGerekliYayinla } from "../../lib/restart";
import YenidenBaslatEkrani from "./YenidenBaslatEkrani";

const RAPOR = {
  kapsam: "tam",
  yerine_konan: 4,
  yetimden_donen: 1,
  eksik: 1,
  bozuk: 1,
  onayla_suruldu: 1,
  ekler: [
    {
      durum: "eksik",
      kayit_turu: "ders yılı",
      kayit_no: "12",
      yukleme_tarihi: "2026-10-01",
      boyut: 2048,
      yedekte_yoktu: true,
    },
    {
      durum: "bozuk",
      kayit_turu: "Kaydı bulunamadı",
      kayit_no: "",
      yukleme_tarihi: null,
      boyut: 512,
      yedekte_yoktu: false,
    },
  ],
};

describe("YenidenBaslatEkrani", () => {
  it("olay gelmeden görünmez, olayla tam ekran yönlendirme gösterir", () => {
    const { container } = render(<YenidenBaslatEkrani />);
    expect(container.firstChild).toBeNull();

    act(() => yenidenBaslatGerekliYayinla());

    const ekran = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ekran).toHaveTextContent("Programı kapatıp yeniden açın");
    // Kenara alınan veritabanı 14 günlük rotasyondadır: "silinmedi" sözü verilmez.
    expect(ekran).toHaveTextContent(
      "Önceki veritabanı veri klasöründe “db-onceki-…” adıyla kenara alındı; 14 gün saklanır, sonra silinir.",
    );
    expect(ekran).not.toHaveTextContent("silinmedi");
    // Raporsuz olayda (ör. sayfa yenilendi) Ekler satırı çizilmez.
    expect(ekran).not.toHaveTextContent("Ekler:");
    // Örtüyü kapatan düğme yok: tek çıkış programı yeniden başlatmaktır. Tek düğme
    // programdan çıkıştır (tasarım §4.5: pencere süslemesi olmayan masaüstünün çıkış yolu).
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Programdan çık" })).toBeInTheDocument();
  });

  it("dosya raporunun kapsamını, sayılarını ve kişisiz listesini yazar", () => {
    render(<YenidenBaslatEkrani />);
    act(() => yenidenBaslatGerekliYayinla(RAPOR));

    const ekran = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ekran).toHaveTextContent("Yedeğin kapsamı: kayıtlar, ekler ve üretilen evrak");
    expect(ekran).toHaveTextContent(
      "Ekler: 4 ek yerine kondu · 1 ek geri alındı · 1 ek eksik · 1 bozuk ek onayla geride bırakıldı",
    );
    expect(ekran).toHaveTextContent("Eksik ya da bozuk ekler:");
    expect(
      screen.getByText(
        "Eksik (yedek alınırken bulunamadı ya da bozuktu) · ders yılı · no 12 · 01.10.2026 · 2 KB",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Bozuk · Kaydı bulunamadı · tarih yok · 1 KB")).toBeInTheDocument();
    // Örtü yine kapatılamaz.
    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("sorunsuz geri yüklemede liste çizilmez, satır eksik ya da bozuk ek olmadığını söyler", () => {
    render(<YenidenBaslatEkrani />);
    act(() =>
      yenidenBaslatGerekliYayinla({
        kapsam: "yerel",
        yerine_konan: 0,
        yetimden_donen: 0,
        eksik: 0,
        bozuk: 0,
        onayla_suruldu: 0,
        ekler: [],
      }),
    );

    const ekran = screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" });
    expect(ekran).toHaveTextContent("Ekler: eksik ya da bozuk ek yok");
    expect(ekran).toHaveTextContent(
      "Yedeğin kapsamı: yalnız kayıtlar; ekler bu bilgisayardan alınır",
    );
    expect(ekran).not.toHaveTextContent("Eksik ya da bozuk ekler:");
  });

  it("sonraki istekten gelen raporsuz olay raporu silmez", () => {
    render(<YenidenBaslatEkrani />);
    act(() => yenidenBaslatGerekliYayinla(RAPOR));
    act(() => yenidenBaslatGerekliYayinla());

    expect(
      screen.getByRole("alertdialog", { name: "Programı yeniden başlatın" }),
    ).toHaveTextContent("Ekler: 4 ek yerine kondu");
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
