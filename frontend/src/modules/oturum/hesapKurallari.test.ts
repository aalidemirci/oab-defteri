// Hesap kurallarının ön yüz kopyası backend'le (`hesap_kurallari.py`) aynı sonucu verir:
// tanıtıcı biçimi ve Türkçe küçük harfe çevirme (`validate_login_name`), ad-soyad
// (`validate_display_name`) ve tanıtıcının ad-soyadı içerdiği uyarısı
// (`login_name_warning`; Türkçe harfler ASCII'ye katlanır). Tablodaki ilk yedi satır
// backend testi `TestTaniticiKurallari`nin satırlarıdır; adlar uydurmadır.

import { describe, expect, it } from "vitest";

import {
  AD_SOYAD_BOS_ILETISI,
  AD_SOYAD_UZUN_ILETISI,
  TANITICI_BOS_ILETISI,
  TANITICI_GECERSIZ_ILETISI,
  TANITICI_TCKN_UYARISI,
  TANITICI_UYARISI,
  TANITICI_VARSAYILAN,
  adSoyadNormallestir,
  adSoyadSorunu,
  asciiKatla,
  taniticiNormallestir,
  taniticiSorunu,
  taniticiUyarisi,
  trKucuk,
} from "./hesapKurallari";

describe("tanıtıcı uyarısı (ad-soyad içeriyor mu?)", () => {
  it.each([
    ["muhasip", "Ayşe Kaya", false],
    ["ayse.k", "Ayşe Kaya", true],
    ["ayse-1", "Ayşe Kaya", true], // dört harfli sözcük sınırın içinde
    ["sukru-2", "Şükrü Öztürk", true], // Türkçe harf katlanır
    ["ali-1", "Ali Can", false], // üç harfli sözcük aranmaz
    ["can.k", "Ali Can", false], // "can" da üç harfli
    ["ozturk", "Şükrü Öztürk", true],
    // Ön yüze özgü Türkçe durumlar (aynı kural):
    ["ismail", "İSMAİL Işıkdağ", true], // büyük İ ve noktasız I katlanır
    ["isikdag-2", "İsmail IŞIKDAĞ", true],
    ["ısıl", "Işıl Çınar", true], // tanıtıcıdaki ı da katlanır
    ["cagri.o", "Çağrı Önal", true],
    ["onal", "Çağrı Önal", true],
    ["yonetici", "Gökçe Ünlü", false],
    ["dk-1", "Ece Su", false],
    ["unlu", "Gökçe Ünlü", true],
  ])("%s + %s → uyarı: %s", (tanitici, ad, uyariVar) => {
    expect(taniticiUyarisi(tanitici, ad) !== null).toBe(uyariVar);
  });

  it("uyarı metni backend'inkiyle aynıdır ve boş girdide uyarı yoktur", () => {
    expect(taniticiUyarisi("ayse.k", "Ayşe Kaya")).toBe(TANITICI_UYARISI);
    expect(TANITICI_UYARISI).toMatch(/^Tanıtıcı hesap sahibinin adını içeriyor\./);
    expect(taniticiUyarisi("", "Ayşe Kaya")).toBeNull();
    expect(taniticiUyarisi("ayse", "")).toBeNull();
    expect(taniticiUyarisi("ayse", "   ")).toBeNull();
  });

  it("ASCII katlama başlık normalleştirmesiyle aynıdır", () => {
    expect(asciiKatla("Şükrü ÖZTÜRK")).toBe("sukru ozturk");
    expect(asciiKatla("sukru.k")).toBe("sukru k");
    expect(asciiKatla("  İĞNE-ılgın  ")).toBe("igne ilgin");
  });
});

// Orkestratör maddesi F-5: T.C. kimlik numarasına benzeyen 11 ardışık rakam uyarıdır (engel değil).
// Tablo backend `TestTaniticiKurallari.test_kimlik_numarasina_benzer_sayi_uyarilir_engellenmez`
// satırlarıdır (sayılar uydurmadır; sağlama aranmaz).
describe("tanıtıcı uyarısı (kimlik numarasına benzeyen sayı)", () => {
  const ILETILER = { tckn: TANITICI_TCKN_UYARISI, ad: TANITICI_UYARISI, yok: null } as const;

  it.each([
    ["kayit-12345678901", "Örnek Kişi", "tckn"],
    ["x123456789012", "Örnek Kişi", "tckn"], // 12'lik dizi bir 11'liyi içerir
    ["a1234567890", "Örnek Kişi", "yok"], // 10 rakam: kimlik numarası değil
    ["a12345-678901", "Örnek Kişi", "yok"], // araya giren tire diziyi böler
    ["ornek-12345678901", "Örnek Kişi", "tckn"], // iki uyarı birden: kimlik önce gelir
    ["ornek-1", "Örnek Kişi", "ad"],
    // Ön yüze özgü: ad-soyad girilmeden de çıkar (kurulum ve "Yeni hesap" alanları).
    ["k12345678901", "", "tckn"],
  ] as const)("%s + %s → %s", (tanitici, ad, beklenen) => {
    expect(taniticiUyarisi(tanitici, ad)).toBe(ILETILER[beklenen]);
    // Uyarı engel değildir: tanıtıcı kurala uyar.
    expect(taniticiSorunu(tanitici)).toBeNull();
  });

  it('ileti sunucununkiyle birebirdir (sözlük §1 "Hesap")', () => {
    expect(TANITICI_TCKN_UYARISI).toBe(
      "Tanıtıcı T.C. kimlik numarasına benzeyen 11 haneli bir sayı içeriyor. Tanıtıcı kilit " +
        "ekranında herkese görünür; rolden türeyen bir tanıtıcı seçmeniz önerilir.",
    );
  });
});

describe("tanıtıcı kuralı", () => {
  it("varsayılan tanıtıcı kurala uyar", () => {
    expect(TANITICI_VARSAYILAN).toBe("yonetici");
    expect(taniticiSorunu(TANITICI_VARSAYILAN)).toBeNull();
  });

  it("baştaki ve sondaki boşluk atılır, Türkçe küçük harfe çevrilir", () => {
    expect(taniticiNormallestir("  MUHASİP ")).toBe("muhasip");
    expect(taniticiNormallestir("Iğdır")).toBe("ığdır");
    expect(trKucuk("İI")).toBe("iı");
    expect(taniticiSorunu("  MUHASİP ")).toBeNull();
  });

  it.each(["a", "1abc", "iki sözcük", "x".repeat(33), "tire/yok"])(
    "kurala uymayan tanıtıcı reddedilir: %s",
    (deger) => {
      expect(taniticiSorunu(deger)).toBe(TANITICI_GECERSIZ_ILETISI);
    },
  );

  it("boş tanıtıcı kendi iletisini alır", () => {
    expect(taniticiSorunu("   ")).toBe(TANITICI_BOS_ILETISI);
  });

  it.each(["dk-1", "yonetici-2", "baskan.yrd", "ö_1", "ab"])("geçerli tanıtıcı: %s", (deger) => {
    expect(taniticiSorunu(deger)).toBeNull();
  });
});

describe("ad-soyad kuralı", () => {
  it("ara boşluklar teke iner; boş ad reddedilir", () => {
    expect(adSoyadNormallestir("  Ayşe   Kaya ")).toBe("Ayşe Kaya");
    expect(adSoyadSorunu("Ayşe Kaya")).toBeNull();
    expect(adSoyadSorunu("   ")).toBe(AD_SOYAD_BOS_ILETISI);
  });

  it("150 karakterden uzun ad reddedilir (kod noktasıyla sayılır)", () => {
    expect(adSoyadSorunu("ş".repeat(150))).toBeNull();
    expect(adSoyadSorunu("ş".repeat(151))).toBe(AD_SOYAD_UZUN_ILETISI);
  });
});
