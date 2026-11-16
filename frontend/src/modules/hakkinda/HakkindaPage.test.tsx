// Hakkında sayfası testleri: üst yazı, program tanımı ve konum notu (CLAUDE.md §1,
// tasarım §3.1 — program karar defterinin ve TEFBİS'in yerine geçmez, bunlara
// girilecek metni ve listeyi hazırlar), şifreleme yöntemi adlarının YALNIZ bu
// sayfada geçmesi (docs/sozluk.md §1 — ayar ekranları "güçlü şifrelemeyle korunur"
// der) ve dış isteğin yalnız elle güncelleme denetimi olduğu (tasarım TK4).

//
// Kişisel Veri kartı (plan F2 10. adım): kişisel veri aydınlatma metninin (E04) belge kartı — durum
// satırı, "Belgeyi oluştur" yalnız `aydinlatma_metni_uretme`'de ve veri sorumlusu girilmişken, basım her
// rolde, veri sorumlusu boşken uyarı ve Okul Bilgileri'ne bağlantı (basım düğmesi yok), sunucunun
// basım uyarıları kartta (belgeye basılmaz). Veriler UYDURMADIR.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { EvrakKaydi } from "../evrak/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { AydinlatmaDurumu } from "./api";

const aydinlatmaMock = vi.hoisted(() => ({ durum: vi.fn(), uret: vi.fn() }));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  aydinlatmaApi: aydinlatmaMock,
}));
const evrakMock = vi.hoisted(() => ({ liste: vi.fn(), uret: vi.fn(), dosya: vi.fn() }));
vi.mock("../evrak/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../evrak/api")>()),
  evrakApi: evrakMock,
}));
const indirmeMock = vi.hoisted(() => ({ saveBlob: vi.fn() }));
vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: indirmeMock.saveBlob,
}));

import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  E04_ADI,
  EVRAK_OKUNAMADI,
  EVRAK_YOK,
  PDF_KAYDEDILDI,
} from "../evrak/metinler";
import HakkindaPage from "./HakkindaPage";
import {
  E04_VERI_SORUMLUSU_GIRILMEDI,
  KISISEL_VERI_BASLIGI,
  OKUL_BILGILERI_BAGLANTISI,
  TEYIT_BASLIGI,
} from "./metinler";

const UYARILAR = [
  "Hukuki sebep öneridir; veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir.",
  "Özel nitelikli kişisel verinin işleme şartı (KVKK md. 6/3'ün bendi) okul müdürlüğünce belirlenir; 1. ve 3. bölümde yeri ……… basıldı.",
];
const KAYIT: EvrakKaydi = {
  id: 41,
  kod: "E04",
  ad: E04_ADI,
  surum: 1,
  durum: "GECERLI",
  uretim_zamani: "2026-11-16T10:15:00+03:00",
  bicimler: ["DOCX", "PDF"],
};

function durumu(alanlar: Partial<AydinlatmaDurumu> = {}): AydinlatmaDurumu {
  return { evrak: null, veri_sorumlusu_girildi: true, basim_uyarilari: UYARILAR, ...alanlar };
}

function bas(yetenekler: string[] = []) {
  return render(
    <YetkiDegeri value={hazirYetki(yetenekler)}>
      <MemoryRouter>
        <SnackbarProvider>
          <HakkindaPage />
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

function kart() {
  return within(screen.getByRole("region", { name: E04_ADI }));
}

beforeEach(() => {
  aydinlatmaMock.durum.mockResolvedValue(durumu());
  indirmeMock.saveBlob.mockResolvedValue("kaydedildi");
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("HakkindaPage — Kişisel Veri kartı", () => {
  it("program yöneticisi metni oluşturur; uyarılar kartta durur, belgeye basılmaz", async () => {
    const user = userEvent.setup();
    aydinlatmaMock.uret.mockResolvedValue({ evrak: KAYIT, uyarilar: UYARILAR });
    bas(["aydinlatma_metni_uretme"]);
    expect(
      screen.getByRole("heading", { level: 2, name: KISISEL_VERI_BASLIGI }),
    ).toBeInTheDocument();
    expect(await kart().findByText(EVRAK_YOK)).toBeInTheDocument();
    expect(kart().getByText(TEYIT_BASLIGI)).toBeInTheDocument();
    expect(kart().getByText(UYARILAR[1])).toBeInTheDocument();
    expect(kart().queryByRole("button", { name: DUGME_PDF })).toBeNull();
    await user.click(kart().getByRole("button", { name: DUGME_OLUSTUR }));
    expect(aydinlatmaMock.uret).toHaveBeenCalledTimes(1);
    expect(await kart().findByText(/1\. sürüm/)).toBeInTheDocument();
    expect(kart().getByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeInTheDocument();
    expect(kart().getByRole("button", { name: DUGME_PDF })).toBeInTheDocument();
    expect(kart().getByRole("button", { name: DUGME_WORD })).toBeInTheDocument();
  });

  it("öteki roller basar, oluşturamaz; ad sunucunundur, yoksa yedek ad", async () => {
    const user = userEvent.setup();
    aydinlatmaMock.durum.mockResolvedValue(durumu({ evrak: KAYIT }));
    const blob = new Blob(["%PDF"]);
    evrakMock.dosya
      .mockResolvedValueOnce({ blob, ad: "Kişisel-Veri-Aydınlatma-Metni_16.11.2026.pdf" })
      .mockResolvedValueOnce({ blob, ad: null });
    bas([]);
    await user.click(await kart().findByRole("button", { name: DUGME_PDF }));
    expect(evrakMock.dosya).toHaveBeenCalledWith(41, "pdf");
    expect(indirmeMock.saveBlob).toHaveBeenCalledWith(
      blob,
      "Kişisel-Veri-Aydınlatma-Metni_16.11.2026.pdf",
    );
    expect(await screen.findByText(PDF_KAYDEDILDI)).toBeInTheDocument();
    expect(kart().queryByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeNull();
    await user.click(kart().getByRole("button", { name: DUGME_WORD }));
    expect(indirmeMock.saveBlob).toHaveBeenLastCalledWith(
      blob,
      "Kişisel-Veri-Aydınlatma-Metni_16.11.2026.docx",
    );
  });

  it("veri sorumlusu boşken uyarı ve Okul Bilgileri bağlantısı; oluşturma ve basım yok", async () => {
    aydinlatmaMock.durum.mockResolvedValue(durumu({ evrak: KAYIT, veri_sorumlusu_girildi: false }));
    bas(["aydinlatma_metni_uretme"]);
    expect(await kart().findByText(E04_VERI_SORUMLUSU_GIRILMEDI)).toBeInTheDocument();
    expect(kart().getByRole("link", { name: OKUL_BILGILERI_BAGLANTISI })).toHaveAttribute(
      "href",
      "/ayarlar?tab=okul",
    );
    expect(kart().queryByRole("button", { name: DUGME_YENIDEN_OLUSTUR })).toBeNull();
    expect(kart().queryByRole("button", { name: DUGME_PDF })).toBeNull();
    expect(kart().queryByRole("button", { name: DUGME_WORD })).toBeNull();
  });

  it("sunucunun ret iletisi kartta; durum okunamazsa 'Belgeyi oluştur' çizilmez", async () => {
    const user = userEvent.setup();
    aydinlatmaMock.uret.mockRejectedValue(
      new ApiError(400, "invalid", "Okul Bilgileri'nde veri sorumlusu girilmemiş."),
    );
    const { unmount } = bas(["aydinlatma_metni_uretme"]);
    await user.click(await kart().findByRole("button", { name: DUGME_OLUSTUR }));
    expect(
      await kart().findByText("Okul Bilgileri'nde veri sorumlusu girilmemiş."),
    ).toBeInTheDocument();
    unmount();
    aydinlatmaMock.durum.mockRejectedValue(new Error("ağ yok"));
    bas(["aydinlatma_metni_uretme"]);
    expect(await kart().findByText(EVRAK_OKUNAMADI)).toBeInTheDocument();
    expect(kart().queryByRole("button", { name: DUGME_OLUSTUR })).toBeNull();
  });
});

describe("HakkindaPage", () => {
  // Öteki kartların testleri: Kişisel Veri kartının durumu hiç gelmez (kart durum satırını boş bırakır).
  beforeEach(() => {
    aydinlatmaMock.durum.mockReturnValue(new Promise<AydinlatmaDurumu>(() => undefined));
  });

  it("Teknik Bilgiler eklerin şifrelenmesini ve yedeğin dosya bölümünü anlatır", () => {
    bas();

    const kart = screen.getByRole("heading", { level: 2, name: "Teknik Bilgiler" }).parentElement;
    const metin = kart?.textContent?.replace(/\s+/g, " ") ?? "";
    expect(metin).toContain("eklerin özgün dosya adları Fernet");
    expect(metin).toContain("her dosya kendi rastgele anahtarıyla AES-256-GCM ile şifreli durur");
    expect(metin).toContain("Bu bilgisayardaki yedekler veritabanını ve eklerin listesini");
    expect(metin).toContain("taşır, dosyaların kendisini taşımaz");
    expect(metin).toContain("Kaydedilen şifreli yedekte bunların ardına dosya bölümü gelir");
    expect(metin).toContain("geri yükleme her dosyayı onunla denetler");
  });

  it("üst yazı konumu, geliştiriciyi, iletişim bilgilerini ve kullanım koşullarını sayar", () => {
    bas();

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
    bas();

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
    const { container } = bas();

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
    bas();

    expect(screen.getByRole("heading", { level: 2, name: "Teknik Bilgiler" })).toBeInTheDocument();
    expect(screen.getByText(/X25519 ve AES-256-GCM/)).toBeInTheDocument();
    expect(screen.getByText(/Argon2id/)).toBeInTheDocument();
    expect(screen.queryByText(/fotoğraf/i)).not.toBeInTheDocument();
  });

  it("teknik bilgiler kişisel hesapları anlatır: tek bir yönetici parolası yoktur", () => {
    const { container } = bas();

    // Veri anahtarı her hesap için ayrı şifrelenir, hesabın parola kaydında durur (tasarım
    // TK9); yedek başlığı hesapların parola kayıtlarını taşımaz, başka bilgisayarda yalnız
    // kurtarma anahtarı açar (TK10).
    expect(
      screen.getByText(/Şifreleme anahtarı her hesap için ayrı şifrelenir ve güvenlik dosyasında/),
    ).toBeInTheDocument();
    expect(screen.getByText(/hesapların parola kayıtlarını taşımaz/)).toBeInTheDocument();
    // Denetim izinin yöntemi de yalnız bu kartta adıyla geçer (sözlük §1 "Denetim izi").
    expect(
      screen.getByText(/Denetim izinin her kaydı, bir önceki kaydın mührüyle birlikte HMAC-SHA256/),
    ).toBeInTheDocument();
    expect(screen.getByText(/mührünün ilk sekiz onaltılık hanesidir/)).toBeInTheDocument();
    expect(
      screen.getByText(/başka bir bilgisayarda yalnız kurtarma\s+anahtarıyla açılır/),
    ).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/yönetici parolası|görevli kipi/i);
  });

  it("Teknik Bilgiler de “sarmal” demez: adı parola kaydıdır (sözlüğün istisnası yalnız “mühür”)", () => {
    const { container } = bas();
    // Sözlük §1 "Denetim izi": "sarmal" kullanıcı metninde yoktur; Teknik Bilgiler'in istisnası
    // yalnız "mühür"ü (yöntem adlarıyla) kapsar, genişlemez (plan F1b-2 "Ön yüz").
    expect(container.textContent).not.toMatch(/sarmal|sarıl/i);
    const teknik = screen.getByRole("heading", { level: 2, name: "Teknik Bilgiler" }).parentElement;
    expect(teknik?.textContent).toMatch(/parola kaydında durur/);
  });

  it("dürüst sınırlar kartı (tasarım §4.4.6) sade dille ve iç kod olmadan", () => {
    const { container } = bas();

    const baslik = screen.getByRole("heading", { level: 2, name: "Dürüst Sınırlar" });
    const kart = baslik.parentElement;
    const metin = kart?.textContent ?? "";
    // Tasarımın sayılı sınırları: rol şifreleme değildir, en zayıf hesap parolası, açık
    // oturum sahibinin imzasıdır, anahtar yenilemek eski yedekleri kapatmaz, çıktı
    // programın dışına çıkınca korumadan çıkar, kayıp ya da çalınmada bildirim.
    expect(metin).toContain("Rol bir şifreleme önlemi değildir.");
    expect(metin).toContain("Şifreli alanlar en zayıf hesap parolası kadar korunur.");
    expect(metin).toContain("Açık oturum, sahibinin imzasıdır.");
    expect(metin).toMatch(/her iş o hesabın adına denetim izine yazılır/);
    expect(metin).toContain("Denetim izi değişikliği gösterir, önlemez.");
    expect(metin).toContain("Kurtarma anahtarını yenilemek önceki yedekleri kapatmaz.");
    expect(metin).toMatch(/Word, PDF ya da Excel/);
    expect(metin).toContain("KVKK md. 12/5");
    expect(metin).toMatch(/BitLocker.*LUKS/);
    expect(metin).toContain(
      "Parola değişimi eski parolayı program içinde geçersiz kılar, program dışında kılmaz.",
    );
    // İç kodlar ve teknik adlar yüzeye çıkmaz (sözlük §2).
    expect(metin).not.toMatch(/\bDEK\b|TK\d|§|Argon2id|Fernet/);
    expect(container.querySelectorAll("li").length).toBeGreaterThanOrEqual(6);
  });

  it("ağ servisi sunmadığını ve dış isteğin tek kapıdan çıktığını söyler (tasarım §4.1)", () => {
    bas();

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
    bas();

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
