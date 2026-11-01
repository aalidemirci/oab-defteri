// Oturum hata eşlemi (plan F1b-1; sözlük §2): ret kodları kullanıcı metnine çıkmaz;
// backend'in sözlüğe uyan iletisi varsa o, yoksa ya da kod biçimindeyse eşlemin metni,
// bilinmeyen kodda çağıranın varsayılanı yazılır. Davranış seçimi için kod ayrıca döner.

import { describe, expect, it } from "vitest";

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";
import { OTURUM_HATA_METINLERI, dogrulamaReddiMi, oturumHataMetni, oturumHatasi } from "./hatalar";

describe("oturumHatasi", () => {
  it("backend iletisi varsa onu yazar, kodu davranış için döndürür", () => {
    const hata = new ApiError(403, "hesap_askida", "Parola hatalı. Hesap askıya alındı.");
    expect(oturumHatasi(hata, "Kilit açılamadı.")).toEqual({
      kod: "hesap_askida",
      metin: "Parola hatalı. Hesap askıya alındı.",
    });
  });

  it.each(Object.keys(OTURUM_HATA_METINLERI))(
    "%s iletisiz, kod biçiminde ya da genel iletiyle gelirse eşlemin metni yazılır",
    (kod) => {
      for (const ileti of ["", kod, BEKLENMEYEN_HATA_ILETISI, "  "]) {
        const { metin } = oturumHatasi(new ApiError(400, kod, ileti), "Varsayılan.");
        expect(metin).toBe(OTURUM_HATA_METINLERI[kod as keyof typeof OTURUM_HATA_METINLERI]);
      }
    },
  );

  it("eşlemin hiçbir metni iç kod ya da kısaltma taşımaz", () => {
    for (const metin of Object.values(OTURUM_HATA_METINLERI)) {
      expect(metin).not.toMatch(/[a-z]+_[a-z]+/);
      expect(metin).not.toMatch(/\b(YK|DK|MY)\b/);
      expect(metin).not.toMatch(/şifre/i);
      expect(metin.endsWith(".") || metin.endsWith(")")).toBe(true);
    }
  });

  it("bilinmeyen kodda ve iletisiz yanıtta varsayılan yazılır", () => {
    expect(oturumHatasi(new ApiError(500, "500", ""), "Kilit açılamadı.")).toEqual({
      kod: null,
      metin: "Kilit açılamadı.",
    });
    expect(oturumHataMetni(new ApiError(500, "500", "sunucu_hatasi"), "Kilit açılamadı.")).toBe(
      "Kilit açılamadı.",
    );
  });

  it("bilinmeyen koddaki anlamlı ileti yazılır (doğrulama hataları)", () => {
    const hata = new ApiError(400, "validation_error", "Yeni parola eskisiyle aynı olamaz.");
    expect(oturumHatasi(hata, "x")).toEqual({
      kod: null,
      metin: "Yeni parola eskisiyle aynı olamaz.",
    });
  });

  it("ApiError olmayan hata (ağ) varsayılana düşer, İngilizce ileti ekrana çıkmaz", () => {
    expect(oturumHataMetni(new TypeError("Failed to fetch"), "Kilitlenemedi.")).toBe(
      "Kilitlenemedi.",
    );
  });
});

describe("dogrulamaReddiMi", () => {
  it("yalnız 400 validation_error alan doğrulaması reddidir", () => {
    expect(dogrulamaReddiMi(new ApiError(400, "validation_error", "Parola kısa."))).toBe(true);
    expect(dogrulamaReddiMi(new ApiError(400, "parola_yanlis", "Parola hatalı."))).toBe(false);
    expect(dogrulamaReddiMi(new TypeError("Failed to fetch"))).toBe(false);
  });
});
