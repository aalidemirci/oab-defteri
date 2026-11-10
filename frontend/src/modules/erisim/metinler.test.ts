// Erişim Günlüğü metinlerinin kuralları (sözlük §1 "Erişim günlüğü (F1b)", "Erişim Günlüğü ekranı
// (F1b)", §2, §5): hesap rol etiketi, tanıtıcı ve açılış/kapanış günüyle anılır (kişi adı yok);
// model ve alan kodu yüzeye çıkmaz; çıktının satır sayısı Türkçe biçimlenir.

import { describe, expect, it } from "vitest";

import {
  ALAN_ADLARI,
  BILINMEYEN_ALAN,
  BILINMEYEN_KAYIT_TURU,
  BOS_ACIKLAMA,
  ERISIM_GUNLUGU_ACIKLAMASI,
  MODEL_ADLARI,
  ciktiMetni,
  erisimHesabi,
  okunanKayit,
} from "./metinler";

describe("okuyan hesabın anılışı", () => {
  it("rol etiketi, tanıtıcı ve günlerle anılır: aynı tanıtıcılı iki hesap ayrılır", () => {
    const eski = {
      id: "a",
      tanitici: "muhasip",
      rol_etiketi: "Muhasip",
      acilis: "2026-09-01",
      kapanis: "2026-10-31",
    };
    const yeni = { ...eski, id: "b", acilis: "2026-11-01", kapanis: null };
    expect(erisimHesabi(eski)).toBe(
      "Muhasip · tanıtıcı muhasip (açılış 01.09.2026, kapanış 31.10.2026)",
    );
    expect(erisimHesabi(yeni)).toBe("Muhasip · tanıtıcı muhasip (açılış 01.11.2026)");
    expect(erisimHesabi(eski)).not.toBe(erisimHesabi(yeni));
  });

  it("kaydın söylemediği açılış günü ve bulunamayan hesap kaydı söylenir", () => {
    expect(
      erisimHesabi({
        id: "a",
        tanitici: "dk-1",
        rol_etiketi: "Denetleme Kurulu",
        acilis: null,
        kapanis: null,
      }),
    ).toBe("Denetleme Kurulu · tanıtıcı dk-1 (açılış günü okunamadı)");
    expect(
      erisimHesabi({
        id: "a",
        tanitici: null,
        rol_etiketi: "Muhasip",
        acilis: null,
        kapanis: null,
      }),
    ).toBe("Muhasip · hesap kaydı bulunamadı");
  });
});

describe("okunan kayıt", () => {
  it("model ve alan kodu yazılmaz; adı olmayan kod “bilinmeyen” diye yazılır", () => {
    const metin = okunanKayit({ model: "okul.Student", kayit: "7", alan: "first_name" });
    expect(metin).toBe(`${BILINMEYEN_KAYIT_TURU} · kimlik 7 · ${BILINMEYEN_ALAN}`);
    expect(metin).not.toMatch(/okul\.|Student|first_name|[a-z]+_[a-z]+/);
    expect(okunanKayit({ model: null, kayit: null, alan: null })).toBe("—");
    expect(okunanKayit({ model: "okul.Student", kayit: null, alan: null })).toBe(
      BILINMEYEN_KAYIT_TURU,
    );
  });

  it("ad eşlemleri günlüğe yazan okumalarla gelir: organ üyeliğindeki engel dayanağı (F1c)", () => {
    expect(MODEL_ADLARI).toEqual({ "oab.OrganMembership": "Organ üyeliği" });
    expect(ALAN_ADLARI).toEqual({ eligibility_bar_basis: "görev alma engelinin dayanağı" });
    expect(
      okunanKayit({ model: "oab.OrganMembership", kayit: "7", alan: "eligibility_bar_basis" }),
    ).toBe("Organ üyeliği · kimlik 7 · görev alma engelinin dayanağı");
  });

  it("çıktının satır sayısı Türkçe biçimlenir; çıktı değilse “—”", () => {
    expect(ciktiMetni({ satir_sayisi: 1250 })).toBe("1.250 satır");
    expect(ciktiMetni({ satir_sayisi: 0 })).toBe("0 satır");
    expect(ciktiMetni({ satir_sayisi: null })).toBe("—");
  });
});

describe("ekranın metinleri", () => {
  it("“log”, iç kod ve kişi verisi değeri anılmaz; okumanın iz bırakmadığı söylenir", () => {
    for (const metin of [ERISIM_GUNLUGU_ACIKLAMASI, BOS_ACIKLAMA]) {
      expect(metin).not.toMatch(/\blog|[a-z]+_[a-z]+|hassas veri/i);
    }
    expect(ERISIM_GUNLUGU_ACIKLAMASI).toMatch(/iz bırakmaz/);
    expect(ERISIM_GUNLUGU_ACIKLAMASI).toMatch(/Okunan değer günlükte yoktur/);
  });
});
