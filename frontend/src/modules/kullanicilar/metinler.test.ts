// Kullanıcılar metinleri: sözlüğe uyar (§1 "Kullanıcılar (F1b)", §3), iç kod ve "sarmal" yüzeye
// çıkmaz (§2), atıf korpustan doğrulanan maddedir (BSG Yön. md. 10/1), metin rol adı saymaz.

import { describe, expect, it } from "vitest";

import { KAPALI_HESAP, hesapSatiri } from "../../test/kullanicilar";
import * as metinler from "./metinler";
import {
  ZARF_METNI,
  anVeHesap,
  durumMetni,
  girisNedeniGorunur,
  hesapAdi,
  kapamaSonucu,
  kisaltmaAdi,
  satirEtiketi,
  sifirlamaSatiri,
  sifirlamaTuru,
} from "./metinler";

/** Modülün bütün metin sabitleri. */
const SABITLER = Object.values(metinler).filter((d): d is string => typeof d === "string");

describe("Kullanıcılar metinleri", () => {
  it("iç kod, “sarmal”, “mühür” ve rol kodu yüzeye çıkmaz", () => {
    expect(SABITLER.length).toBeGreaterThan(30);
    for (const metin of SABITLER) {
      expect(metin).not.toMatch(/sarmal|mühür|[a-z]+_[a-z]+|yonetici|denetleme_kurulu/i);
      expect(metin).not.toMatch(/şifre(?!l)/i);
    }
  });

  it("zarf metni yönergenin md. 10/1'ini anar ve kapalı zarfı söyler", () => {
    expect(ZARF_METNI).toContain("Bilgi ve Sistem Güvenliği Yönergesi 10/1");
    expect(ZARF_METNI).toContain("kapalı zarfta");
    expect(ZARF_METNI).toContain("bir daha göstermez");
  });

  it("hesabın kişisiz adı ve satırın erişilebilir adı", () => {
    const h = hesapSatiri();
    expect(hesapAdi(h)).toBe("Muhasip · tanıtıcı muhasip");
    expect(satirEtiketi(h)).toBe("Muhasip · tanıtıcı muhasip hesabının ayrıntısını aç");
    expect(kapamaSonucu(h)).toMatch(/^Muhasip · tanıtıcı muhasip hesabı kapanır: /);
    expect(kisaltmaAdi({ id: "x", tanitici: null, rol_etiketi: null })).toBe(
      "Kaydı okunamayan hesap",
    );
    expect(kisaltmaAdi({ id: "x", tanitici: "eski", rol_etiketi: null })).toBe("tanıtıcı eski");
  });

  it("durum metni askının nedenini ve kapanış gününü yazar", () => {
    expect(durumMetni(hesapSatiri())).toBe("Açık");
    expect(
      durumMetni(
        hesapSatiri({
          durum: "ASKIDA",
          durum_etiketi: "Askıda",
          askida_nedeni: "HATALI_DENEME",
          askida_nedeni_etiketi: "Hatalı parola denemesi",
        }),
      ),
    ).toBe("Askıda · Hatalı parola denemesi");
    expect(durumMetni(KAPALI_HESAP)).toBe("Kapalı · 03.11.2026");
    expect(durumMetni({ ...KAPALI_HESAP, kapanis: null })).toBe("Kapalı");
  });

  it("girişin nedeni kapalı ve kaydı tutan hesapta yinelenmez", () => {
    expect(girisNedeniGorunur(hesapSatiri())).toBe(false);
    expect(girisNedeniGorunur(KAPALI_HESAP)).toBe(false);
    expect(girisNedeniGorunur({ ...KAPALI_HESAP, kayit_tutuyor: false })).toBe(true);
    expect(
      girisNedeniGorunur(
        hesapSatiri({ giris: { yapabilir: false, neden: "Hesap askıda; askıdan çıkarılınca…" } }),
      ),
    ).toBe(true);
    expect(girisNedeniGorunur(hesapSatiri({ giris: { yapabilir: false, neden: null } }))).toBe(
      false,
    );
  });

  it("an ve ilgili hesap; sıfırlamanın türü kod değil etikettir", () => {
    const yonetici = { id: "a", tanitici: "yonetici", rol_etiketi: "Program yöneticisi" };
    expect(anVeHesap("2026-11-02T10:15:00+03:00", "açan", yonetici)).toBe(
      "02.11.2026 10:15 · açan: Program yöneticisi · tanıtıcı yonetici",
    );
    expect(anVeHesap(null, "kapatan", null)).toBe("—");
    expect(sifirlamaSatiri(null)).toBe("—");
    expect(
      sifirlamaSatiri({ tur: "SIFIRLAMA", zaman: "2026-11-03T09:00:00+03:00", yapan: yonetici }),
    ).toBe("Parola sıfırlandı · 03.11.2026 09:00 · yapan: Program yöneticisi · tanıtıcı yonetici");
    expect(sifirlamaTuru("KURTARMA")).toBe("Kurtarma anahtarıyla yenilendi");
    expect(sifirlamaTuru(null)).toBe("Parola yenilendi");
  });
});
