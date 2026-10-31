// Hakkında sayfası testleri: üst yazı, program tanımı ve konum notu (CLAUDE.md §1,
// tasarım §3.1 — program karar defterinin ve TEFBİS'in yerine geçmez, bunlara
// girilecek metni ve listeyi hazırlar), şifreleme yöntemi adlarının YALNIZ bu
// sayfada geçmesi (docs/sozluk.md §1 — ayar ekranları "güçlü şifrelemeyle korunur"
// der) ve dış isteğin yalnız elle güncelleme denetimi olduğu (tasarım TK4).

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HakkindaPage from "./HakkindaPage";

describe("HakkindaPage", () => {
  it("üst yazı konumu, geliştiriciyi, iletişim bilgilerini ve kullanım koşullarını sayar", () => {
    render(<HakkindaPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Hakkında ve Lisans" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Programın konumu, geliştiricisi, iletişim bilgileri ve kullanım koşulları.",
      ),
    ).toBeInTheDocument();
  });

  it("geliştirici kartı: kardeş programlarla aynı biçimde ad ve e-posta (unvan ve kurum yok)", () => {
    // Kullanıcı kuralı: iletişim, aile programlarının Hakkında sayfasındaki biçimde
    // verilir — ad + e-posta; unvan ve kurum adı herkese açık tanıtımda geçmez.
    render(<HakkindaPage />);

    expect(screen.getByRole("heading", { level: 2, name: "Geliştirici" })).toBeInTheDocument();
    expect(screen.getByText("Ahmet Ali DEMİRCİ")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /aalidemirci@gmail\.com/ })).toHaveAttribute(
      "href",
      "mailto:aalidemirci@gmail.com",
    );
    expect(
      screen.getByText(/talep, öneri, hata bildirimi ve şikâyetlerinizi bu e-posta adresine/),
    ).toBeInTheDocument();
    // KVKK: destek iletisine kişi verisi girmez; okulun kayıtları için başvuru okula yapılır.
    expect(screen.getByText(/İletinize öğrenci, veli ya da personel bilgisi/)).toHaveTextContent(
      "başvurular okul müdürlüğüne yapılır",
    );
    const kart = screen.getByRole("heading", { level: 2, name: "Geliştirici" }).parentElement;
    const kartMetni = kart?.textContent ?? "";
    expect(kartMetni).toContain("Ahmet Ali DEMİRCİ");
    for (const unvanYaDaKurum of [/öğretmen/i, /müdür yardımcısı/i, /lisesi/i, /ortaokulu/i]) {
      expect(kartMetni).not.toMatch(unvanYaDaKurum);
    }
  });

  it("program kartı: tanım ve konum notu — karar defterinin ve TEFBİS'in yerine geçmez", () => {
    const { container } = render(<HakkindaPage />);

    const baslik = screen.getByRole("heading", { level: 2, name: "Program" });
    expect(
      screen.getByText(
        "OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten çevrimdışı bir masaüstü programıdır.",
      ),
    ).toBeInTheDocument();
    // Konum notu CLAUDE.md §1 ve Kullanım Kılavuzu'ndaki "Programın Konumu" ile aynıdır.
    expect(
      screen.getByText(
        "Program karar defterinin ve TEFBİS'in yerine geçmez. Karar defterine kararlar el ile yazılır ve defter noter tasdiklidir; birliğin gelir-gider kayıtlarını TEFBİS'e okul idaresi girer. Program bunlara girilecek metni ve listeyi hazırlar, tutarlılığı denetler.",
      ),
    ).toBeInTheDocument();
    // Simge logonun motifidir (okul çatısı altında aile); aile iskeletinin kitap simgesi kalmadı.
    const kart = baslik.parentElement?.parentElement;
    expect(kart?.querySelector(".material-symbols-outlined")).toHaveTextContent("family_restroom");
    // Program kendine "otomasyon sistemi" adını vermez (docs/sozluk.md §1); aile
    // iskeletinin kütüphane tanımı sayfada kalmaz.
    expect(container.textContent).not.toMatch(/otomasyon sistemi/i);
    expect(container.textContent).not.toMatch(/kütüphane|local_library/i);
  });

  it("teknik bilgiler kartı şifreleme yöntemlerini adıyla verir; fotoğraf şifrelemesi anlatılmaz", () => {
    render(<HakkindaPage />);

    expect(screen.getByRole("heading", { level: 2, name: "Teknik Bilgiler" })).toBeInTheDocument();
    expect(screen.getByText(/X25519 ve AES-256-GCM/)).toBeInTheDocument();
    expect(screen.getByText(/Argon2id/)).toBeInTheDocument();
    expect(screen.queryByText(/fotoğraf/i)).not.toBeInTheDocument();
  });

  it("ağ servisi sunmadığını ve dış isteğin tek kapıdan çıktığını söyler (tasarım §4.1)", () => {
    render(<HakkindaPage />);

    expect(
      screen.getByText(/Program ağ\s+servisi sunmaz: yönetim sunucusu yalnız 127\.0\.0\.1'de/),
    ).toBeInTheDocument();
    expect(screen.getByText(/hiçbir port okul ağına açılmaz/)).toBeInTheDocument();
    expect(screen.getByText(/Program açılışta internete çıkmaz;/)).toBeInTheDocument();
    expect(screen.getByText(/“Şimdi\s+denetle” düğmesine bastığınızda/)).toBeInTheDocument();
    // Denetimin hedefi GitHub'dır (tasarım TK4).
    expect(screen.getByText(/son sürümü GitHub'dan soran anonim\s+denetim/)).toBeInTheDocument();
    expect(screen.getByText(/kişisel veri dışarı\s+çıkmaz/)).toBeInTheDocument();
    // Aile iskeletinin ikinci kapısı (ISBN künye sorgusu) ve Ağ Kataloğu yoktur.
    expect(screen.queryByText(/ISBN/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Ağ Kataloğu/)).not.toBeInTheDocument();
  });

  it("üçüncü taraf kartı LGPL kitaplıkların telif bildirimini ve lisans dosyalarını verir", () => {
    // LGPL-3.0 §4(c) (lisans kümesi: tasarım §11.4): çalışırken telif bildirimi gösteren program,
    // LGPL kitaplığın bildirimini de gösterir ve GPL/LGPL metinlerine yönlendirir.
    render(<HakkindaPage />);

    expect(
      screen.getByRole("heading", { level: 2, name: "Üçüncü Taraf Bileşenler" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/GNU Kısıtlı Genel Kamu Lisansı\s+\(LGPL-3\.0\)/)).toBeInTheDocument();
    // Aile iskeletinin Windows tepsisi (pystray, LGPL-3.0) OAB'de yoktur (tasarım §11 B18).
    expect(screen.queryByText(/pystray/)).not.toBeInTheDocument();
    expect(screen.getByText(/Qt 6 ve PySide6 — Copyright © The Qt/)).toBeInTheDocument();
    for (const dosya of [
      "THIRD_PARTY_LICENSES",
      "BENIOKU.txt",
      "LGPL-3.0-metni.txt",
      "GPL-3.0-metni.txt",
    ]) {
      expect(screen.getByText(dosya)).toBeInTheDocument();
    }
    // Sözlük (docs/sozluk.md §1): "kurucu" / "yükleyici" kullanıcı metninde geçmez.
    expect(screen.queryByText(/kurucu|yükleyici/i)).not.toBeInTheDocument();
  });
});
