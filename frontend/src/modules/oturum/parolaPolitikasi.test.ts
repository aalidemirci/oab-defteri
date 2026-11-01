// Parola politikasının ön yüz kopyası (tasarım TK15; plan F1b-1): kural ve iletiler
// backend `hesap_kurallari.validate_password` ile birebir; Türkçe harfler harf sayılır;
// parola kırpılmaz; eskisiyle aynı olamaz. Birebirliğin kanıtı ORTAK VAKA TABLOSUdur:
// aynı satırlar backend `test_hesaplar.py::ORTAK_PAROLA_VAKALARI`'nda da vardır (kenar
// karakterler: ², ①, ٣, ª, Ⅷ, U+00A0, U+001F, U+FEFF). Güç göstergesi yerel kuraldır.

import { describe, expect, it } from "vitest";

import {
  AYNI_PAROLA_ILETISI,
  ESLESMEDI_ILETISI,
  KENAR_BOSLUGU_ILETISI,
  KISA_ILETISI,
  UZUN_ILETISI,
  eksikTurler,
  parolaGucu,
  parolaSorunu,
  yeniParolaHatalari,
} from "./parolaPolitikasi";

/** Backend `ORTAK_PAROLA_VAKALARI` ile AYNI satırlar (değişirse iki dosya birlikte değişir). */
const EKSIK_RAKAM = "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: rakam.";
const ORTAK_PAROLA_VAKALARI: [string, string | null][] = [
  ["Okul-Aile\u00b2", EKSIK_RAKAM],
  ["Okul-Aile\u2460", EKSIK_RAKAM],
  ["Okul-Aile\u0663", null],
  ["OKUL-AILE1\u00aa", null],
  ["okul-aile1\u2167", null],
  ["\u00a0Okul-Aile1", KENAR_BOSLUGU_ILETISI],
  ["Okul-Aile1\u001f", KENAR_BOSLUGU_ILETISI],
  ["\ufeffOkulAile1", null],
];

describe("parolaSorunu", () => {
  it.each(["Deneme-Parola-1", "Çiğdem.2026", "ŞÜKRÜ-kaya-9", "sözcük Bir 2 üç!"])(
    "%s kurala uyar",
    (parola) => {
      expect(parolaSorunu(parola)).toBeNull();
    },
  );

  it("backend sırasıyla ve iletileriyle reddeder", () => {
    expect(parolaSorunu(" Deneme-Parola-1")).toBe(KENAR_BOSLUGU_ILETISI);
    expect(parolaSorunu("Deneme-Parola-1 ")).toBe(KENAR_BOSLUGU_ILETISI);
    expect(parolaSorunu("Kisa-1a")).toBe(KISA_ILETISI);
    expect(parolaSorunu(`Aa1!${"x".repeat(125)}`)).toBe(UZUN_ILETISI);
    expect(parolaSorunu("denemeparola")).toBe(
      "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: büyük harf, rakam, simge.",
    );
  });

  it("uzunluk kod noktasıyla sayılır (Python len gibi)", () => {
    // Sekiz kod noktası; UTF-16'da dokuz birim.
    expect(parolaSorunu("Aa1!😀bcd")).toBeNull();
    expect(parolaSorunu("Aa1!😀bc")).toBe(KISA_ILETISI);
  });

  it("Türkçe harfler harf sayılır; boşluk simge değildir", () => {
    expect(eksikTurler("ığüşöç")).toEqual(["büyük harf", "rakam", "simge"]);
    expect(eksikTurler("İĞÜŞÖÇ")).toEqual(["küçük harf", "rakam", "simge"]);
    expect(eksikTurler("Aa1 bcde")).toEqual(["simge"]);
    expect(eksikTurler("Aa1.")).toEqual([]);
  });

  it("yeni parola eskisiyle aynı olamaz", () => {
    expect(parolaSorunu("Deneme-Parola-1", "Deneme-Parola-1")).toBe(AYNI_PAROLA_ILETISI);
    expect(parolaSorunu("Deneme-Parola-2", "Deneme-Parola-1")).toBeNull();
  });

  it.each(ORTAK_PAROLA_VAKALARI)("ortak vaka tablosu: %j → %s", (parola, ileti) => {
    expect(parolaSorunu(parola)).toBe(ileti);
  });

  it("alan alan hatalar: politika ilk alana, eşleşmeme tekrar alanına", () => {
    expect(yeniParolaHatalari("zayif", "baska")).toEqual({
      yeni: KISA_ILETISI,
      tekrar: ESLESMEDI_ILETISI,
    });
    expect(yeniParolaHatalari("Deneme-Parola-1", "Deneme-Parola-2")).toEqual({
      yeni: null,
      tekrar: ESLESMEDI_ILETISI,
    });
    expect(yeniParolaHatalari("Deneme-Parola-1", "Deneme-Parola-1", "Deneme-Parola-1")).toEqual({
      yeni: AYNI_PAROLA_ILETISI,
      tekrar: null,
    });
    expect(yeniParolaHatalari("Deneme-Parola-2", "Deneme-Parola-2")).toEqual({
      yeni: null,
      tekrar: null,
    });
  });
});

describe("parolaGucu", () => {
  it.each([
    ["", 0, ""],
    ["zayif", 1, "Zayıf"],
    ["Deneme-1", 2, "Orta"],
    ["Deneme-Parola", 1, "Zayıf"],
    ["Deneme-Parola-1", 3, "İyi"],
    ["Okul aile birliği-2026", 4, "Güçlü"],
  ])("%s → %i (%s)", (parola, duzey, etiket) => {
    expect(parolaGucu(parola)).toEqual({ duzey, etiket });
  });
});
