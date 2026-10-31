// Kullanım Kılavuzu — kabuk (aile iskeletinden ayıklandı) ve programın konum bölümü.
// Aile iskeletinin kütüphane içeriği ve onu ekran metinleriyle eşleyen testler
// F1a-2'de silindi; OAB'nin bölümleri özellikleriyle birlikte yazılır.

import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Kod, Mevzuat, Tus } from "./KilavuzKabugu";
import KilavuzPage, { KILAVUZ_BOLUMLERI } from "./KilavuzPage";

function bas(yol = "/kilavuz") {
  return render(
    <MemoryRouter initialEntries={[yol]}>
      <KilavuzPage />
    </MemoryRouter>,
  );
}

describe("KilavuzPage", () => {
  it("başlık ve her bölüme çapalı bağlantı vardır", () => {
    bas();

    expect(screen.getByRole("heading", { level: 1, name: "Kullanım Kılavuzu" })).toBeVisible();
    const gezinme = screen.getByRole("navigation", { name: "Kılavuz bölümleri" });
    for (const bolum of KILAVUZ_BOLUMLERI) {
      expect(within(gezinme).getByRole("link", { name: bolum.baslik })).toHaveAttribute(
        "href",
        `#${bolum.id}`,
      );
      expect(screen.getByRole("region", { name: bolum.baslik })).toHaveAttribute("id", bolum.id);
    }
  });

  it("programın konumu: karar defterinin ve TEFBİS'in yerine geçmez", () => {
    bas();

    const bolum = screen.getByRole("region", { name: "Programın Konumu" });
    expect(bolum).toHaveTextContent("karar defterinin ve TEFBİS'in yerine geçmez");
    expect(within(bolum).getByRole("link", { name: "Kurulum Sihirbazı" })).toHaveAttribute(
      "href",
      "/kurulum",
    );
  });

  it("kütüphane içeriği silinmiştir", () => {
    const { container } = bas();

    expect(container.textContent).not.toMatch(/ödünç|nüsha|barkod|Ağ Kataloğu|kütüphane/i);
  });

  it("çapalı adresle açılınca bölüme kaydırır", () => {
    const kaydir = vi.fn();
    const asil = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = kaydir;
    try {
      bas("/kilavuz#programin-konumu");
    } finally {
      Element.prototype.scrollIntoView = asil;
    }

    expect(kaydir).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
  });
});

describe("KilavuzKabugu", () => {
  it("kabuk bileşenleri içeriklerini çizer", () => {
    render(
      <MemoryRouter>
        <KilavuzBolumu id="deneme" baslik="Deneme Bölümü" ikon="info">
          <AltBaslik>Alt başlık</AltBaslik>
          <Ipucu>İpucu metni</Ipucu>
          <Mevzuat kaynak="Yönetmelik md. 1">Alıntı metni</Mevzuat>
          <Ekran to="/ayarlar">Ayarlar</Ekran>
          <Tus>Ctrl</Tus>
          <Kod>oab-defteri --autotest</Kod>
        </KilavuzBolumu>
      </MemoryRouter>,
    );

    const bolum = screen.getByRole("region", { name: "Deneme Bölümü" });
    expect(within(bolum).getByRole("heading", { level: 3, name: "Alt başlık" })).toBeVisible();
    expect(within(bolum).getByText("İpucu metni")).toBeVisible();
    expect(within(bolum).getByText("Yönetmelik md. 1")).toBeVisible();
    expect(within(bolum).getByRole("link", { name: "Ayarlar" })).toHaveAttribute(
      "href",
      "/ayarlar",
    );
    expect(within(bolum).getByText("Ctrl").tagName).toBe("KBD");
    expect(within(bolum).getByText("oab-defteri --autotest").tagName).toBe("CODE");
  });
});
