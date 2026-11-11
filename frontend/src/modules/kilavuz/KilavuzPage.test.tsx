// Kullanım Kılavuzu — kabuk, bölüm dizilişi ve sözlük kilitleri (aile kalıbı). Aile iskeletinin
// kütüphane içeriği ve onu ekran metinleriyle eşleyen testler F1a-2'de silindi. F1c'nin bölümleri
// (13. adım) aynı kilitlere bağlandı: ekran, sekme, düğme ve belge adları ekran sabitlerinden okunur.
//
// Üç tür kilit var:
// 1. Ekran adları DEPODAN gelir: sekme, başlık ve düğme adları ekran sabitlerinden okunur;
//    ekrandaki ad değişirse kılavuz da değişmek zorunda kalır.
// 2. Sözlük (docs/sozluk.md, bağlayıcı): iç kodlar (§2) ve "Kullanılmaz" sütunu (§1) bütün
//    bölümlerde geçmez. Tarama çizilmiş metin üzerindedir ve İKİ uçta yapılır (bütün yetenekler
//    açık, hiçbiri açık değil): kaynak taransa yorumlar ve kod takılırdı, tek uç taransa
//    `yetki.acik(…)`in öteki kolu görülmezdi.
// 3. Mevzuat alıntıları docs/mevzuat'taki metinle BİREBİR yazılır. Ön yüz konteynerine yalnız
//    frontend/ bağlıdır, korpus buradan okunamaz: beklenen metinler `MEVZUAT_ALINTILARI`ye o
//    dosyalardan kopyalanır (aile kalıbı); sayfadaki her `Mevzuat` kutusu bu tabloyla eşleşmek
//    zorundadır, tabloda olmayan alıntı testi düşürür.
//
// Metin denetimleri `textContent` üzerinden yapılır: `getByText` yalnız tek elemanın metnine
// baktığından <strong>/<kbd> sınırını aşan ifade eşleşmezdi.

import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { TAB_ITEMS as AYAR_SEKMELERI } from "../ayarlar/AyarlarPage";
import {
  BIRLIK_DONEMI_BASLIGI,
  DUGME_DONEMI_IPTAL,
  KURAL_KOPYASI_BOZUK,
  KURAL_SURUMU_AYARLAR_BASLIGI,
} from "../birlik-donemi/metinler";
import {
  DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
  DENETIM_IZI_KARTI_BASLIGI,
  EKSIK_EKLER_KARTI_BASLIGI,
  GERI_YUKLEME_KARTI_BASLIGI,
} from "../butunluk/metinler";
import { ERISIM_GUNLUGU_BASLIGI } from "../erisim/metinler";
import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  E01_ADI,
  E02_ADI,
  E03_ADI,
  TASLAK_ACIKLAMASI,
  URETIM_UYARILARI_BASLIGI,
} from "../evrak/metinler";
import {
  DEFTER_BASLIGI,
  DUGME_TAMAMLA,
  DUGME_UYE_EKLE,
  GECIS_BASLIGI,
  ILK_DONEM_BASLIGI,
  KURUL_BASLIGI,
  SAYAC_BASLIGI,
  SIHIRBAZ_ADIM_ADI,
  TAMAMLA_BASLIGI,
} from "../gecis-kurulumu/metinler";
import {
  KILIT_EKRANI_BASLIGI,
  KURTARMA_ILE_AC_ETIKETI,
  UYELIK_ASKISI_METNI,
} from "../guvenlik/KilitEkrani";
import { KURTARMA_BELGESI_ADI } from "../guvenlik/kurtarma";
import {
  DOSYA_KAYIP_BASLIGI,
  DURUST_SINIRLAR,
  SIFRELI_YEDEK_DUGMESI,
  SIFRELI_YEDEK_KARTI_BASLIGI,
  YEDEK_RAPORU_ADI,
} from "../guvenlik/metinler";
import {
  BIRLIK_KISILERI_SEKMESI,
  DUGME_BIRLIK_KISISI_EKLE,
  DUGME_PASIF_YAP,
  DUGME_PERSONELDEN_EKLE,
  DUGME_VELI_LISTESINDEN_EKLE,
  VELI_LISTESI_SEKMESI,
} from "../kisiler/metinler";
import { TABS as KISI_SEKMELERI } from "../kisiler/KisilerPage";
import {
  ALAN_UYELIK,
  DUGME_ASKIDAN_CIKAR,
  DUGME_KAPAT,
  DUGME_SIFIRLA,
  KULLANICILAR_BASLIGI,
  ORGANLARA_GIT,
  YENI_HESAP_BASLIGI,
} from "../kullanicilar/metinler";
import { ADIMLAR as SIHIRBAZ_ADIMLARI } from "../kurulum/KurulumPage";
import {
  DUGME_DAYANAK,
  DUGME_DK_GOREV_BOLUMU,
  DUGME_DUSUR,
  DUGME_ENGEL,
  DUGME_GOREV_BOLUMU,
  DUGME_KAYDI_IPTAL,
  DUGME_YEDEK_CAGIR,
  ORGANLAR_BASLIGI,
  TOPLANTI_GUNU_BASLIGI,
} from "../organlar/metinler";
import { TAB_ITEMS as ORGAN_SEKMELERI } from "../organlar/OrganlarPage";
import { YETENEK_ADLARI } from "../oturum/api";
import type { YetenekAdi } from "../oturum/api";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { Yetki } from "../oturum/yetki";
import { YOL_HARITASI_MADDELERI } from "../pano/BaslangicYolHaritasi";
import {
  AY_BASLIGI,
  HAFTA_BASLIGI,
  HESAP_ONERISI_BASLIGI,
  TAMAMLANACAKLAR_BASLIGI,
  YARIM_TASLAK_BASLIGI,
  YK_GOREV_BOLUMU_BASLIGI,
} from "../pano/metinler";
import { CIZELGE_BASLIGI, DUGME_TEMSILCI_EKLE, TEMSILCILER_BASLIGI } from "../temsilciler/metinler";
import { KILAVUZ_SIHIRBAZ_KAPALI_METNI } from "./bolumler/PrograminKonumu";
import {
  AltBaslik,
  Ekran,
  Ipucu,
  KapiliEkran,
  KilavuzBolumu,
  Kod,
  Mevzuat,
  Tus,
} from "./KilavuzKabugu";
import KilavuzPage, { KILAVUZ_BOLUMLERI } from "./KilavuzPage";

/** Sihirbazı açabilen hesap (program yöneticisinin yeteneği). */
const SIHIRBAZ_ACIK = hazirYetki(["kurulum_tamamlama"]);
const BUTUN_YETENEKLER = hazirYetki(YETENEK_ADLARI);
const HICBIR_YETENEK = hazirYetki([]);

/** Bölüm dosyalarının kaynağı (`./bolumler/Ad.tsx` → metin). */
const BOLUM_KAYNAKLARI = import.meta.glob<string>("./bolumler/*.tsx", {
  query: "?raw",
  import: "default",
  eager: true,
});
const SAYFA_KAYNAGI = import.meta.glob<string>("./KilavuzPage.tsx", {
  query: "?raw",
  import: "default",
  eager: true,
})["./KilavuzPage.tsx"];
const KILIT_EKRANI_KAYNAGI = import.meta.glob<string>("../guvenlik/KilitEkrani.tsx", {
  query: "?raw",
  import: "default",
  eager: true,
})["../guvenlik/KilitEkrani.tsx"];

function sekmeAdi(sekmeler: ReadonlyArray<{ key: string; label: string }>, key: string): string {
  const sekme = sekmeler.find((s) => s.key === key);
  if (!sekme) throw new Error(`Sekme yok: ${key}`);
  return sekme.label;
}

/** Sıra kullanıcının iş sırasıdır; adı sabiti olanlar ekranın sabitinden gelir. */
const BEKLENEN_BOLUMLER: ReadonlyArray<readonly [id: string, baslik: string]> = [
  ["programin-konumu", "Programın Konumu"],
  ["programi-kurmak", "Programı Kurmak"],
  ["ilk-kurulum", "İlk Kurulum"],
  ["genel-bakis", "Genel Bakış"],
  ["hesaplar-ve-oturum", "Hesaplar ve Oturum"],
  ["kullanicilar", KULLANICILAR_BASLIGI],
  ["okul-karti", sekmeAdi(AYAR_SEKMELERI, "okul")],
  ["ders-yili-kapali-gunler", "Ders Yılları ve Kapalı Günler"],
  ["kisiler", "Kişiler"],
  ["veli-listesi", VELI_LISTESI_SEKMESI],
  // F1c (13. adım): birlik kişileri, birlik dönemi, geçiş kurulumu, organlar, temsilciler.
  ["birlik-kisileri", sekmeAdi(KISI_SEKMELERI, "birlik")],
  ["birlik-donemi", BIRLIK_DONEMI_BASLIGI],
  ["gecis-kurulumu", GECIS_BASLIGI],
  ["organlar", ORGANLAR_BASLIGI],
  ["temsilciler", TEMSILCILER_BASLIGI],
  ["yedek-ve-geri-yukleme", "Yedek ve Geri Yükleme"],
  ["guvenlik-ve-kvkk", "Güvenlik ve Kişisel Veriler"],
  ["guncelleme", sekmeAdi(AYAR_SEKMELERI, "guncelleme")],
  ["cikis-ve-kapanis", "Çıkış ve Kapanış"],
];

/** Her `Mevzuat` kutusunun beklenen metni (kaynak satırı → docs/mevzuat'tan birebir kopya). */
const MEVZUAT_ALINTILARI: Readonly<Record<string, string>> = {
  "Yönetmelik md. 12/3":
    "Yönetim kurulu, seçimden sonraki ilk hafta içinde okulda toplanarak üyeleri arasından bir başkan, bir başkan yardımcısı, bir muhasip ve bir sekreter seçerek görev ve iş bölümü yapar. Yönetim kurulu üyelerinden üyeliği sona erenlerin yerine yedeklerin çağrılmasıyla oluşan yeni yönetim kurulu bir hafta içinde toplanarak aralarında görev dağılımı yaparlar.",
  "Yönetmelik md. 13/5": "Yönetim kurulu kararları, karar defterine el ile yazılarak imzalanır.",
  "Yönetmelik md. 13/6":
    "Özürsüz olarak üst üste üç toplantıya katılmayan yönetim kurulu üyesinin görevi sona erer. Bu şekilde görevi sona erenler ile öğrencisinin okuldan ayrılması veya öğrenciliğin sona ermesi nedenleriyle yönetim kurulu üyeliği sona eren velinin yerine yedek üyeler, aldıkları oy sırasına göre asıl üye olarak göreve çağırılır.",
  "Yönetmelik md. 23/2":
    "Yönetim kurulunca, yönetim kurulu karar defterinin noterce tasdik edilmesi zorunlu olup diğer defter ve belgeler ise birliğin bağlı bulunduğu il/ilçe millî eğitim müdürlüğünce tasdik edilir.",
  "Yönetmelik md. 23/5":
    "Okul idaresi, okul-aile birliklerinin gelir ve gider kayıtları ile diğer mali işlemlerini Bakanlıkça kurulan merkezî bilgi sistemine (TEFBİS) kaydeder.",
};

/** Yalnız bazı rollere açık ekranlar: adresin kapısı (`App.tsx` rotaları, sekme yetenekleri). */
const KAPILI_ADRESLER: ReadonlyArray<readonly [adres: string, yetenek: YetenekAdi]> = [
  ["/kullanicilar", "kullanicilar"],
  ["/erisim-gunlugu", "erisim_gunlugu"],
  ["/kurulum", "kurulum_tamamlama"],
  ["/kisiler?tab=veli", "veli_listesi"],
  ["/kisiler?tab=havuz", "ayrilis_havuzu"],
  ["/ayarlar?tab=guncelleme", "guncelleme"],
];

/** Sayfaların adresleri (`App.tsx`); sekmeler ekranların sekme listelerinden. */
const SAYFA_ADRESLERI = [
  "/",
  "/birlik-donemi",
  "/birlik-donemi/gecis-kurulumu",
  "/kisiler",
  "/organlar",
  "/temsilciler",
  "/kullanicilar",
  "/erisim-gunlugu",
  "/ayarlar",
  "/kilavuz",
  "/hakkinda",
  "/kurulum",
];

/** Türkçe harfte `\b` çalışmaz: sözcük sınırı harf sınıfıyla bakılır. */
function sozcuk(kalip: string): RegExp {
  return new RegExp(`(?<!\\p{L})${kalip}(?!\\p{L})`, "iu");
}

/** Sözlük §2 "İç kodlar yüzeye çıkmaz". Büyük/küçük harfe duyarlıdır. */
const IC_KODLAR: readonly RegExp[] = [
  /\b[KTDU]\d{1,2}\b/, // kullanıcı kararları, aile kodları, devralınan kusurlar
  /\bT[KB]\d+\b/, // teknik kararlar
  /\bR\d{1,2}\b/, // riskler ve denetim önerileri
  /\bF\d[a-z]?\b/, // fazlar ve adımlar
  /\bE\d{2}\b/, // evrak kodları
  /\b(?:M|A|B|KE|GA|UY|KM|SU|MA)-\d/, // açık kararlar ve denetim bulguları
  /OAB-\d{4}/, // kural paketinin kimliği
  /\bpk\b/,
  /\bid=/,
  /\b(?:SchoolConfig|Account)\b/, // model adları
  /\/api\b/, // uç yolları
  /\b[a-z]+_[a-z_]+\b/, // hata kodları, alan ve yetenek adları
  /\b[A-Z]+_[A-Z_]+\b/, // tür kodları
  /\.odbak/i, // yedek uzantısı (sözlük §1 "Yedek")
  /§/, // tasarım ve plan atıfları
];

/** Sözlük §1 "Kullanılmaz" sütunu, §3 yazım kuralları ve vaat yasağı. */
const YASAK_SOZLER: readonly RegExp[] = [
  // Program ve konum
  /otomasyon sistemi/i,
  /resmî sistem/i,
  /elektronik karar defteri/i,
  /dijital defter/i,
  /TEFBİS yerine/i,
  /karar belgesi/i,
  /TEFBİS'e (?:aktar|gönder)/i,
  /TEFBİS ile eşitle/i,
  /entegrasyon/i,
  // Birlik, organlar ve terimler
  sozcuk("dernek"),
  sozcuk("vakıf"),
  /Denetim Kurulu/i,
  /(?<!\p{L})(?:YK|DK|MY)(?!\p{L})/u,
  sozcuk("sayman"),
  sozcuk("muhasebeci"),
  /bütçe planı/i,
  /kural ihlali/i,
  sozcuk("override"),
  sozcuk("bypass"),
  /mali yıl/i,
  // Okul bilgileri, aktarım, personel
  /okul kartı/i,
  sozcuk("kısa ad(?:ı)?"),
  /(?<!\p{L})(?:e-okul|E-Okul|eOkul|eokul)(?!\p{L})/u,
  sozcuk("import"),
  /senkronizasyon/i,
  /eşitle/i,
  /üye türü/i,
  // Parola, roller, hesap
  /(?<!\p{L})şifre(?!\p{L})/iu,
  /uygulama parolası/i,
  /(?<!\p{L})PIN(?!\p{L})/u,
  /yönetici parolası/i,
  /sistem yöneticisi/i,
  sozcuk("admin"),
  /yetki matrisi/i,
  /denetleme_kurulu/,
  /kullanıcı yönetimi/i,
  /(?<!\p{L})(?:mühür|zincir)/iu,
  /iz boşluğu/i,
  /yönetici kipi/i,
  /görevli kipi/i,
  sozcuk("kip\\p{L}*"),
  /kullanıcı değiştir/i,
  /öğrenci modu/i,
  /admin modu/i,
  sozcuk("kiosk"),
  // Kurtarma anahtarı ve şifreleme
  /kurtarma kodu/i,
  /yedek parola/i,
  /ana anahtar/i,
  /anahtarı (?:sıfırla|değiştir)/i,
  /(?<!\p{L})(?:Fernet|AES|X25519|Argon2id|HMAC)(?!\p{L})/u,
  /veritabanı şifreli/i,
  // Denetim izi ve erişim günlüğü
  sozcuk("çapa"),
  sozcuk("tohum"),
  sozcuk("sarmal"),
  sozcuk("log"),
  sozcuk("audit"),
  /erişim logu/i,
  /hassas veri/i,
  // Yedek ve ekler
  /dış yedek/i,
  /harici yedek/i,
  /bulut yedeği/i,
  sozcuk("kapsayıcı"),
  /USB belleğe alındı/i,
  /db-onceki/i,
  /şifreli yede\p{L}* indir/iu,
  /yedek dosya\p{L}* yükle/iu,
  /dosya deposu/i,
  sozcuk("yetim"),
  // Sürüm, kurulum, eski program
  sozcuk("şema\\p{L}*"),
  sozcuk("migration"),
  sozcuk("göç\\p{L}*"),
  /sürüm uyuşmazlığı/i,
  /GitHub sürümü/i,
  /(?<!\p{L})Release(?!\p{L})/u,
  /kurucu/i,
  /yükleyici/i,
  /installer/i,
  sozcuk("setup"),
  /SHA-?\d/i,
  // Yazım (§3): düzeltme işareti
  /(?<!\p{L})(?:resmi|milli)(?!\p{L})/iu,
  // Olmayan özellik vaat edilmez
  /(?:ilerideki|ilerleyen|sonraki|gelecek) (?:bir )?sürüm/i,
  sozcuk("yakında"),
  // Kardeş programların işi
  /ödünç|nüsha|barkod|Ağ Kataloğu|kütüphane/i,
];

function bas(yol = "/kilavuz", yetki: Yetki = SIHIRBAZ_ACIK) {
  return render(
    <YetkiDegeri value={yetki}>
      <MemoryRouter initialEntries={[yol]}>
        <KilavuzPage />
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

/**
 * Elemanın okunan metni. Mevzuat alıntıları kendi diliyledir, sözlüğe tabi değildir; ikonların
 * adı (`aria-hidden`, `power_settings_new` gibi) metin düğümü olsa da okunmaz.
 */
function alintisizMetin(oge: Element): string {
  const kopya = oge.cloneNode(true) as Element;
  kopya.querySelectorAll('blockquote, [aria-hidden="true"]').forEach((gizli) => gizli.remove());
  return kopya.textContent ?? "";
}

/** Sayfa başı ve her bölümün metni, verilen yetkiyle. */
function metinler(yetki: Yetki): Array<{ yer: string; metin: string }> {
  const { container, unmount } = bas("/kilavuz", yetki);
  const sonuc = [
    { yer: "sayfa başı", metin: alintisizMetin(container.querySelector("header") as Element) },
    ...KILAVUZ_BOLUMLERI.map(({ id }) => ({
      yer: id,
      metin: alintisizMetin(container.querySelector(`[id="${id}"]`) as Element),
    })),
  ];
  unmount();
  return sonuc;
}

/** Bütün dalları görmek için iki uç: her yetenek açık ve hiçbiri açık değil. */
function ikiUcMetinleri(): Array<{ yer: string; metin: string }> {
  return [...metinler(BUTUN_YETENEKLER), ...metinler(HICBIR_YETENEK)];
}

function bolumBaglantilari(yetki: Yetki): string[] {
  const { container, unmount } = bas("/kilavuz", yetki);
  const adresler = Array.from(container.querySelectorAll("section a[href]")).map(
    (a) => a.getAttribute("href") ?? "",
  );
  unmount();
  return adresler;
}

describe("KilavuzPage — kabuk ve bölümler", () => {
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

  it("bölümler iş sırasıyla gelir, adı sabiti olan başlık ekranın sabitindedir", () => {
    expect(KILAVUZ_BOLUMLERI.map((b) => [b.id, b.baslik])).toEqual(BEKLENEN_BOLUMLER);

    const { container } = bas();
    expect(Array.from(container.querySelectorAll("section")).map((s) => s.id)).toEqual(
      BEKLENEN_BOLUMLER.map(([id]) => id),
    );
  });

  it("her bölüm dosyası sayfaya bağlıdır; bölüm sayısı dosya sayısıdır", () => {
    const dosyalar = Object.keys(BOLUM_KAYNAKLARI);

    expect(dosyalar).toHaveLength(KILAVUZ_BOLUMLERI.length);
    for (const dosya of dosyalar) {
      expect(SAYFA_KAYNAGI).toContain(`"${dosya.replace(/\.tsx$/, "")}"`);
    }
  });

  it("bölüm dosyaları çapa ve başlığı kendisi yazmaz, kabuğu kullanır", () => {
    for (const [dosya, kaynak] of Object.entries(BOLUM_KAYNAKLARI)) {
      expect(kaynak, dosya).toContain("<KilavuzBolumu {...bolum}>");
      expect(kaynak, dosya).not.toMatch(/TODO|FIXME/);
    }
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

describe("KilavuzPage — programın konumu", () => {
  it("karar defterinin ve TEFBİS'in yerine geçmez", () => {
    bas();

    const bolum = screen.getByRole("region", { name: "Programın Konumu" });
    expect(bolum).toHaveTextContent("karar defterinin ve TEFBİS'in yerine geçmez");
    expect(within(bolum).getByRole("link", { name: "Kurulum Sihirbazı" })).toHaveAttribute(
      "href",
      "/kurulum",
    );
    expect(bolum).not.toHaveTextContent(KILAVUZ_SIHIRBAZ_KAPALI_METNI);
  });

  it("sihirbazı açamayan rolde sihirbazın adı bağlantı değildir (kullanıcı kararı 04.11.2026)", () => {
    // Başkanın yetenekleri: kurulum_tamamlama yok.
    bas("/kilavuz", hazirYetki(["son_oturum_onay"]));

    const bolum = screen.getByRole("region", { name: "Programın Konumu" });
    expect(within(bolum).queryByRole("link")).toBeNull();
    expect(bolum).toHaveTextContent(KILAVUZ_SIHIRBAZ_KAPALI_METNI);
    expect(bolum).not.toHaveTextContent("Kurulum Sihirbazı'nı açın");
  });
});

describe("KilavuzPage — sözlük ve kalıntı denetimi", () => {
  it("iç kodlar geçmez", () => {
    for (const { yer, metin } of ikiUcMetinleri()) {
      for (const kalip of IC_KODLAR) expect(metin, yer).not.toMatch(kalip);
      for (const yetenek of YETENEK_ADLARI) expect(metin, yer).not.toContain(yetenek);
    }
  });

  it("sözlüğün kullanmadığı sözler ve olmayan özelliğin vaadi geçmez", () => {
    for (const { yer, metin } of ikiUcMetinleri()) {
      for (const kalip of YASAK_SOZLER) expect(metin, yer).not.toMatch(kalip);
    }
  });

  it("tırnak kıvrık, kesme işareti düzdür (sözlük §3)", () => {
    for (const { yer, metin } of ikiUcMetinleri()) {
      expect(metin, yer).not.toContain('"');
      expect(metin, yer).not.toContain("’");
    }
  });

  it("rol tablosu yazılmaz: yönlendirme cümlesi yeter", () => {
    const { container } = bas("/kilavuz", BUTUN_YETENEKLER);

    for (const baslik of Array.from(container.querySelectorAll("th"))) {
      expect(baslik.textContent ?? "").not.toMatch(sozcuk("rol(?:ler)?"));
    }
  });

  it("mevzuat alıntıları korpustan kopyalanan tabloyla birebirdir", () => {
    const { container } = bas("/kilavuz", BUTUN_YETENEKLER);

    for (const kutu of Array.from(container.querySelectorAll("figure"))) {
      const kaynak = kutu.querySelector("figcaption")?.textContent ?? "";
      const alinti = kutu.querySelector("blockquote")?.textContent ?? "";
      expect(MEVZUAT_ALINTILARI[kaynak], kaynak).toBe(alinti.replace(/\s+/g, " ").trim());
    }
  });
});

describe("KilavuzPage — ekran bağlantıları", () => {
  it.each(KAPILI_ADRESLER)("%s yalnız kendi yeteneğiyle bağlantı olur", (adres, yetenek) => {
    const yeteneksiz = hazirYetki(YETENEK_ADLARI.filter((ad) => ad !== yetenek));

    expect(bolumBaglantilari(yeteneksiz).filter((a) => a.startsWith(adres))).toEqual([]);
  });

  it("kurtarma anahtarı görevleri yalnız kartları görebilen hesaba anlatılır", () => {
    const yeteneksiz = hazirYetki(YETENEK_ADLARI.filter((ad) => ad !== "guvenlik"));
    const { container } = bas("/kilavuz", yeteneksiz);
    const metin = container.querySelector('[id="yedek-ve-geri-yukleme"]')?.textContent ?? "";

    expect(metin).not.toContain("Kurtarma anahtarını yenilemek için");
    expect(metin).not.toContain("Kurtarma anahtarı belgesini yeniden almak için");
    expect(metin).toContain("program yöneticisine başvurun");
  });

  it("bağlantılar var olan sayfaya, sekmeye ve bölüme gider", () => {
    const sekmeler: Record<string, readonly string[]> = {
      "/ayarlar": AYAR_SEKMELERI.map((s) => s.key),
      "/kisiler": KISI_SEKMELERI.map((s) => s.key),
      "/organlar": ORGAN_SEKMELERI.map((s) => s.key),
    };
    const capalar = KILAVUZ_BOLUMLERI.map((b) => `#${b.id}`);

    for (const adres of bolumBaglantilari(BUTUN_YETENEKLER)) {
      const url = new URL(adres, "http://kilavuz.test");
      expect(SAYFA_ADRESLERI, adres).toContain(url.pathname);
      const sekme = url.searchParams.get("tab");
      if (sekme !== null) expect(sekmeler[url.pathname] ?? [], adres).toContain(sekme);
      if (url.hash) expect(capalar, adres).toContain(url.hash);
    }
  });

  it("kilit ekranından kılavuza bağlantı yoktur (kılavuz kilitliyken açılmaz)", () => {
    expect(KILIT_EKRANI_KAYNAGI).not.toContain("/kilavuz");
  });
});

describe("KilavuzPage — bölüm içerikleri", () => {
  /** Bölüm → ekranda sabiti olan ve bölümde adıyla geçmesi gereken adlar. */
  const EKRAN_ADLARI: Readonly<Record<string, readonly string[]>> = {
    "ilk-kurulum": [
      "Kurulum Sihirbazı",
      KURTARMA_BELGESI_ADI,
      ...SIHIRBAZ_ADIMLARI.map((a) => a.label),
      SIHIRBAZ_ADIM_ADI,
    ],
    "genel-bakis": [
      AY_BASLIGI,
      HAFTA_BASLIGI,
      TAMAMLANACAKLAR_BASLIGI,
      YK_GOREV_BOLUMU_BASLIGI,
      HESAP_ONERISI_BASLIGI,
      YARIM_TASLAK_BASLIGI,
      ...YOL_HARITASI_MADDELERI.map((m) => m.baslik),
      DENETIM_IZI_KARTI_BASLIGI,
      DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
      GERI_YUKLEME_KARTI_BASLIGI,
      EKSIK_EKLER_KARTI_BASLIGI,
    ],
    "hesaplar-ve-oturum": [
      KILIT_EKRANI_BASLIGI,
      KURTARMA_ILE_AC_ETIKETI,
      "Kilitle",
      UYELIK_ASKISI_METNI,
    ],
    kullanicilar: [
      YENI_HESAP_BASLIGI,
      DUGME_SIFIRLA,
      DUGME_ASKIDAN_CIKAR,
      DUGME_KAPAT,
      ALAN_UYELIK,
      ORGANLARA_GIT,
    ],
    "okul-karti": [sekmeAdi(AYAR_SEKMELERI, "okul")],
    "ders-yili-kapali-gunler": [
      sekmeAdi(AYAR_SEKMELERI, "ders-yillari"),
      sekmeAdi(AYAR_SEKMELERI, "kapali-gunler"),
    ],
    kisiler: [sekmeAdi(KISI_SEKMELERI, "personel"), sekmeAdi(KISI_SEKMELERI, "havuz")],
    "veli-listesi": [VELI_LISTESI_SEKMESI],
    "birlik-kisileri": [
      BIRLIK_KISILERI_SEKMESI,
      DUGME_BIRLIK_KISISI_EKLE,
      DUGME_PERSONELDEN_EKLE,
      DUGME_VELI_LISTESINDEN_EKLE,
      DUGME_PASIF_YAP,
    ],
    "birlik-donemi": [
      BIRLIK_DONEMI_BASLIGI,
      DUGME_DONEMI_IPTAL,
      KURAL_SURUMU_AYARLAR_BASLIGI,
      KURAL_KOPYASI_BOZUK,
    ],
    "gecis-kurulumu": [
      GECIS_BASLIGI,
      ILK_DONEM_BASLIGI,
      KURUL_BASLIGI,
      SAYAC_BASLIGI,
      DEFTER_BASLIGI,
      TAMAMLA_BASLIGI,
      DUGME_TAMAMLA,
      DUGME_UYE_EKLE,
    ],
    organlar: [
      ORGANLAR_BASLIGI,
      ...ORGAN_SEKMELERI.map((s) => s.label),
      DUGME_GOREV_BOLUMU,
      DUGME_DK_GOREV_BOLUMU,
      DUGME_YEDEK_CAGIR,
      DUGME_DUSUR,
      DUGME_ENGEL,
      DUGME_KAYDI_IPTAL,
      TOPLANTI_GUNU_BASLIGI,
      E01_ADI,
      E02_ADI,
      DUGME_OLUSTUR,
      DUGME_PDF,
      DUGME_WORD,
      URETIM_UYARILARI_BASLIGI,
    ],
    temsilciler: [TEMSILCILER_BASLIGI, CIZELGE_BASLIGI, DUGME_TEMSILCI_EKLE, E03_ADI],
    "yedek-ve-geri-yukleme": [
      SIFRELI_YEDEK_KARTI_BASLIGI,
      SIFRELI_YEDEK_DUGMESI,
      YEDEK_RAPORU_ADI,
      DOSYA_KAYIP_BASLIGI,
      KURTARMA_BELGESI_ADI,
      "Kurtarma Anahtarını Yenile",
    ],
    "guvenlik-ve-kvkk": [ERISIM_GUNLUGU_BASLIGI, ...DURUST_SINIRLAR.map((s) => s.baslik)],
    guncelleme: [sekmeAdi(AYAR_SEKMELERI, "guncelleme")],
  };

  /** Bölüm → metinde madde numarasıyla geçmesi gereken dayanaklar (tasarım ve plan istekleri). */
  const MADDE_ATIFLARI: Readonly<Record<string, readonly string[]>> = {
    "programin-konumu": ["13/5", "23/2", "23/5"],
    "okul-karti": ["9/2", "17/1", "23/3"],
    "genel-bakis": ["12/3", "14/1"],
    "birlik-kisileri": ["12/1", "14/1"],
    "birlik-donemi": ["12/2", "14/2"],
    "gecis-kurulumu": ["12/4", "14/3", "23/2"],
    organlar: [
      "7/2",
      "12/1",
      "12/3",
      "12/4",
      "12/5",
      "13/3",
      "13/5",
      "13/6",
      "14/1",
      "14/4",
      "14/6",
      "14/7",
      "18/1",
    ],
  };

  function bolumMetni(id: string): string {
    const { container } = bas("/kilavuz", BUTUN_YETENEKLER);
    return container.querySelector(`[id="${id}"]`)?.textContent ?? "";
  }

  it("yer tutucu kalmamıştır", () => {
    for (const [dosya, kaynak] of Object.entries(BOLUM_KAYNAKLARI)) {
      expect(kaynak, dosya).not.toContain("Bu bölüm yazılacak.");
    }
  });

  it.each(Object.entries(EKRAN_ADLARI))("%s: ekran adları sabitlerle birebirdir", (id, adlar) => {
    const metin = bolumMetni(id);
    for (const ad of adlar) expect(metin, ad).toContain(ad);
  });

  it.each(Object.entries(MADDE_ATIFLARI))("%s: dayanak maddeleri yazılıdır", (id, maddeler) => {
    const metin = bolumMetni(id);
    for (const madde of maddeler) expect(metin, madde).toContain(madde);
  });

  it("F1 kod kapısının kılavuz bölümleri yazılıdır: kurulum, okul bilgileri, kullanıcılar, organlar", () => {
    // Plan §2.4 "Kılavuzda F1 bölümleri"; tasarım §14 F1c satırı.
    for (const id of ["programi-kurmak", "ilk-kurulum", "okul-karti", "kullanicilar", "organlar"]) {
      expect(
        KILAVUZ_BOLUMLERI.map((b) => b.id),
        id,
      ).toContain(id);
      expect(bolumMetni(id).length, id).toBeGreaterThan(400);
    }
    expect(bolumMetni("programi-kurmak")).toMatch(/kurulum dosyası/);
    expect(bolumMetni("programi-kurmak")).toContain(".deb");
  });

  it("evrakın konumu: karar taslağı karar defterine el ile yazılır (CLAUDE.md §1)", () => {
    expect(bolumMetni("programin-konumu")).toContain("karar defterine el ile yazılır ve imzalanır");
    expect(bolumMetni("organlar")).toContain(TASLAK_ACIKLAMASI);
    expect(bolumMetni("temsilciler")).toContain(TASLAK_ACIKLAMASI);
    for (const id of ["organlar", "gecis-kurulumu"]) {
      expect(bolumMetni(id), id).toContain("karar defterinin yerine geçmez");
    }
  });

  it("sihirbazın adımları ekrandaki sırayla sayılır; birlik dönemi adımı atlanabilir", () => {
    const { container } = bas("/kilavuz", BUTUN_YETENEKLER);
    const liste = container.querySelector('[id="ilk-kurulum"] ol');
    const maddeler = Array.from(liste?.querySelectorAll("li") ?? []).map((li) => li.textContent);
    expect(maddeler).toHaveLength(SIHIRBAZ_ADIMLARI.length);
    SIHIRBAZ_ADIMLARI.forEach((adim, i) => expect(maddeler[i]).toContain(adim.label));
    expect(maddeler.at(-1)).toContain("atlanabilir");
  });

  it("F1c bölümlerinin yazma adımları yalnız o yeteneği olan hesaba anlatılır", () => {
    const yazmayan = ["birlik_donemi_yazma", "birlik_kisi_yazma", "temsilci_yazma"];
    const { container } = bas(
      "/kilavuz",
      hazirYetki(YETENEK_ADLARI.filter((ad) => !yazmayan.includes(ad))),
    );
    const metin = (id: string) => container.querySelector(`[id="${id}"]`)?.textContent ?? "";
    expect(metin("birlik-donemi")).not.toContain(DUGME_DONEMI_IPTAL);
    expect(metin("birlik-kisileri")).not.toContain(DUGME_BIRLIK_KISISI_EKLE);
    expect(metin("temsilciler")).not.toContain(DUGME_TEMSILCI_EKLE);
    expect(metin("gecis-kurulumu")).not.toContain(DUGME_UYE_EKLE);
    for (const id of ["birlik-donemi", "birlik-kisileri", "temsilciler", "gecis-kurulumu"]) {
      expect(metin(id), id).toMatch(/program yöneticisine (?:başvurun|bildirin)/);
    }
  });

  it("görev alma engelinin dayanağı yalnız onu okuyabilen hesaba anlatılır", () => {
    const engelsiz = hazirYetki(YETENEK_ADLARI.filter((ad) => ad !== "gorev_alma_engeli"));
    const { container, unmount } = bas("/kilavuz", engelsiz);
    expect(container.querySelector('[id="organlar"]')?.textContent).toContain(
      "yalnız engelin var olduğu görünür",
    );
    unmount();
    expect(bolumMetni("organlar")).toContain(DUGME_DAYANAK);
  });

  it("öğretmen üyenin yedek çağrısı görevlendirmenin süresine bağlanır, geçen zamana değil (md. 14/6)", () => {
    const metin = bolumMetni("genel-bakis");
    expect(metin).toContain("dört aydan fazla süreli görevlendirildi (md. 13/6, 14/6)");
    expect(metin).not.toContain("dört ayı aştı");
  });

  it("parolayı unutunca ne olacağı kilit ekranından önce öğretilir", () => {
    expect(bolumMetni("hesaplar-ve-oturum")).toContain("Parolamı unuttum");
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

  it("KapiliEkran: yetenek açıksa bağlantı, değilse düz addır", () => {
    const { rerender } = render(
      <YetkiDegeri value={hazirYetki(["kullanicilar"])}>
        <MemoryRouter>
          <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
            Kullanıcılar
          </KapiliEkran>
        </MemoryRouter>
      </YetkiDegeri>,
    );
    expect(screen.getByRole("link", { name: "Kullanıcılar" })).toHaveAttribute(
      "href",
      "/kullanicilar",
    );

    rerender(
      <YetkiDegeri value={hazirYetki([])}>
        <MemoryRouter>
          <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
            Kullanıcılar
          </KapiliEkran>
        </MemoryRouter>
      </YetkiDegeri>,
    );
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByText("Kullanıcılar")).toBeVisible();
  });
});
