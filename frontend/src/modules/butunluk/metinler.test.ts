// Denetim izi metinlerinin kuralları (docs/sozluk.md §1 "Denetim izi", §2, §5): backend'in
// her bulgu kodunun sade bir cümlesi vardır ve hiçbir cümle iç kod ya da teknik terim
// ("çapa", "tohum", "sarmal", "kip") taşımaz; tanınmayan kod yazılmaz. Kâğıt çapası
// satırı tasarım §4.6.3'ün biçimindedir. Hesap rol etiketi ve tanıtıcıyla anılır.

import { describe, expect, it } from "vitest";

import {
  BILINMEYEN_BULGU_METNI,
  BULGU_METINLERI,
  DENETLENEMEDI_KODLARI,
  bulguMetinleri,
  bulguMetni,
  degisiklikGosterir,
  hesapEtiketi,
  kagitCapasiSatiri,
  parolaYenilenmeCumlesi,
  parolaYenilenmeOgudu,
} from "./metinler";

/**
 * Backend'in bulgu kodları (`apps/okul/iz_dogrulama.py` ve `denetim_izi.py` sabitleri). Yeni
 * bir kod eklenince buraya ve `metinler.BULGU_METINLERI`'ne cümlesiyle eklenir.
 */
const BACKEND_KODLARI = [
  "capa_yok",
  "capa_bozuk",
  "capa_muhru_tutmadi",
  "capa_bayat",
  "kuyruk_kesik",
  "kesinti",
  "kilitli_satir_eksik",
  "kilitli_satir_fazla",
  "kilitli_sira",
  "kilitli_mac_tutmadi",
  "muhursuz_satir",
  "tohum_tutmadi",
  "dogrulama_yapilamadi",
  "sira_boslugu",
  "zincir_kopuk",
  "mac_tutmadi",
  "anahtar_yok",
  "muhursuz",
  "satir_kurali",
];

describe("bulgu metinleri", () => {
  it("backend'in her bulgu kodunun cümlesi vardır", () => {
    for (const kod of BACKEND_KODLARI) {
      expect(bulguMetni(kod), kod).not.toBe(BILINMEYEN_BULGU_METNI);
    }
    expect(Object.keys(BULGU_METINLERI).sort()).toEqual([...BACKEND_KODLARI].sort());
  });

  it("cümleler iç kod ve teknik terim taşımaz, noktayla biter", () => {
    for (const metin of Object.values(BULGU_METINLERI)) {
      expect(metin).not.toMatch(/[a-z]+_[a-z]+/);
      expect(metin).not.toMatch(/çapa|tohum|sarmal|\bkip\b|mühür|HMAC|seal/i);
      expect(metin.endsWith(".")).toBe(true);
    }
  });

  it("tasarımın saydığı dört durum sade dille söylenir", () => {
    expect(bulguMetni("kuyruk_kesik")).toMatch(/son kayıtları silinmiş.*geri sarılmış/);
    expect(bulguMetni("kilitli_satir_eksik")).toMatch(/kilitliyken yazılan olaylardan bazıları/);
    expect(bulguMetni("zincir_kopuk")).toMatch(/zinciri kırık/);
    expect(bulguMetni("capa_yok")).toMatch(/Kilit işareti bulunamadı/);
    expect(bulguMetni("kesinti")).toMatch(/Bu bir bilgidir/);
  });

  it("sırrı olmayanın eklediği kayıt ve yenilenmemiş kilit işareti de söylenir", () => {
    expect(bulguMetni("satir_kurali")).toMatch(/program dışından eklenmiş olabilir/);
    expect(bulguMetni("capa_bayat")).toMatch(/son kilitlenmede yenilenememiş/);
  });

  it("kesinti cümlesi iki nedeni de söyler: program kapandı ya da kayıt yazılamadı", () => {
    // Bağımsız denetim bulgusu: kilitli yazım tohum ilerledikten sonra düşerse (disk dolu)
    // program açık kalır, bulgu yine kesintidir; cümle yalnız "kapanmış" diyordu.
    expect(bulguMetni("kesinti")).toMatch(/program kapanmış ya da kayıt yazılamamış/);
    expect(bulguMetni("kesinti")).toMatch(/dolu disk/);
  });

  it("bulgular değişiklik gösteren ve denetleyemeyen diye ikiye ayrılır", () => {
    for (const kod of ["capa_yok", "capa_bozuk", "dogrulama_yapilamadi"]) {
      expect(degisiklikGosterir(kod), kod).toBe(false);
    }
    expect(degisiklikGosterir("muhursuz_satir")).toBe(false);
    expect(degisiklikGosterir("kesinti")).toBe(false);
    for (const kod of [
      "kuyruk_kesik",
      "capa_muhru_tutmadi",
      "capa_bayat",
      "zincir_kopuk",
      "sira_boslugu",
      "mac_tutmadi",
      "kilitli_satir_eksik",
      "kilitli_satir_fazla",
      "kilitli_sira",
      "kilitli_mac_tutmadi",
      "tohum_tutmadi",
      "satir_kurali",
      "anahtar_yok", // bugün meşru nedeni yok: program dışından yazılmış kayıt ya da başvuru
      "yeni_bir_kod", // tanınmayan kod değişiklik sayılır (fail-closed)
    ]) {
      expect(degisiklikGosterir(kod), kod).toBe(true);
    }
    for (const kod of DENETLENEMEDI_KODLARI) expect(BACKEND_KODLARI).toContain(kod);
  });

  it("anahtarı bulunamayan kayıt değişiklik olabileceğini söyler, denetlenemedi demez", () => {
    // Bağımsız denetim bulgusu: sırrı olmayan biri bir kaydın içeriğini değiştirip aynı
    // yazımda anahtar başvurusunu bozunca bulgu `anahtar_yok` oluyor, kart "Bu bir değişiklik
    // bulgusu değildir" diyordu.
    expect(bulguMetni("anahtar_yok")).toMatch(/program dışından değiştirilmiş olabilir/);
    expect(bulguMetni("anahtar_yok")).not.toMatch(/denetlenemedi/);
    expect(DENETLENEMEDI_KODLARI.has("anahtar_yok")).toBe(false);
  });

  it("tanınmayan kod yazılmaz; aynı cümle bir kez yazılır", () => {
    expect(bulguMetni("yeni_bir_kod")).toBe(BILINMEYEN_BULGU_METNI);
    expect(bulguMetni("toString")).toBe(BILINMEYEN_BULGU_METNI);
    expect(bulguMetinleri(["yeni_kod", "baska_kod", "muhursuz", "muhursuz_satir"])).toEqual([
      BILINMEYEN_BULGU_METNI,
      BULGU_METINLERI.muhursuz,
    ]);
  });
});

describe("kâğıt çapası satırı", () => {
  it("“Kayıt no: N · Zincir: XXXX-XXXX” biçimindedir; no ayrımsız yazılır", () => {
    expect(kagitCapasiSatiri({ kayit_no: 128, zincir: "C3ED-8364" })).toBe(
      "Kayıt no: 128 · Zincir: C3ED-8364",
    );
    expect(kagitCapasiSatiri({ kayit_no: 12345, zincir: "0A1B-2C3D" })).toBe(
      "Kayıt no: 12345 · Zincir: 0A1B-2C3D",
    );
  });
});

describe("hesap etiketi", () => {
  it("rol etiketi ve tanıtıcıyla anılır (kişi adı yok)", () => {
    expect(hesapEtiketi({ id: "1", tanitici: "muhasip", rol_etiketi: "Muhasip" })).toBe(
      "Muhasip · tanıtıcı muhasip",
    );
    expect(hesapEtiketi({ id: "2", tanitici: "eski-hesap", rol_etiketi: null })).toBe(
      "tanıtıcı eski-hesap",
    );
    expect(hesapEtiketi({ id: "3", tanitici: null, rol_etiketi: null })).toBe(
      "Kaydı okunamayan hesap",
    );
  });
});

describe("parola yenilenme bildirimi", () => {
  const ZAMAN = "2026-11-01T00:30:00+03:00"; // UTC'de 31.10.2026: gün yerel saatten okunur

  it("sıfırlama ve kurtarma cümleleri sözlükteki biçimdedir (gg.aa.yyyy)", () => {
    expect(parolaYenilenmeCumlesi("SIFIRLAMA", ZAMAN)).toBe(
      "Parolanız 01.11.2026 tarihinde sıfırlandı.",
    );
    expect(parolaYenilenmeCumlesi("KURTARMA", ZAMAN)).toBe(
      "Parolanız 01.11.2026 tarihinde kurtarma anahtarıyla yenilendi.",
    );
    expect(parolaYenilenmeCumlesi("", ZAMAN)).toBe("Parolanız 01.11.2026 tarihinde yenilendi.");
  });

  it("öğüt türe göredir; kurtarmada zarfın açıldığını söyler", () => {
    expect(parolaYenilenmeOgudu("KURTARMA")).toMatch(/okul müdürlüğüne ve Denetleme Kuruluna/);
    expect(parolaYenilenmeOgudu("KURTARMA")).toMatch(/zarf açılmış/);
    expect(parolaYenilenmeOgudu("SIFIRLAMA")).toMatch(/sıfırlanmasını siz istemediyseniz/);
  });
});
