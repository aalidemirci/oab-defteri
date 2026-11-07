// Yedek listesinin ve dosya raporunun satırları (plan F1b-3 "Ekran adları", "Eksik ve bozuk ekler
// kişisiz bilgiyle listelenir"): tür yalnız programın ürettiği adda yazılır, F4'ün türleri adsızdır;
// ek satırı konsolun sırasını taşır; "Ekler" satırı sıfırı yazmaz, sorun yoksa bunu söyler.

import { describe, expect, it } from "vitest";

import type { EkSatiri } from "./api";
import {
  AZAMI_YEDEK_DOSYASI,
  ekSatiriMetni,
  eklerOzeti,
  eklerSatiri,
  eksikEkCumlesi,
  kapsamMetni,
  yedekAciklamasi,
  yedekBoyuSatiri,
  yedekTuru,
  yoldanDosyaAdi,
} from "./yedekBilgisi";

const EK: EkSatiri = {
  durum: "eksik",
  kayit_turu: "ders yılı",
  kayit_no: "7",
  yukleme_tarihi: "2026-10-01",
  boyut: 4096,
  yedekte_yoktu: false,
};

const SIFIR = {
  kapsam: "yerel",
  yerine_konan: 0,
  yetimden_donen: 0,
  eksik: 0,
  bozuk: 0,
  onayla_suruldu: 0,
} as const;

describe("yedekTuru", () => {
  it.each([
    ["gunluk-2026-09-01.odbak", "Günlük yedek"],
    ["pre-migrate-1.0.0-2026-09-01.odbak", "Güncelleme öncesi yedek"],
    ["pre-migrate-1.2.3-rc.1-2026-09-01.odbak", "Güncelleme öncesi yedek"],
    ["pre-parola-acilis-2026-09-01-101530.odbak", "Kurulum yedeği"],
  ])("programın ürettiği adın türünü yazar: %s", (ad, tur) => {
    expect(yedekTuru(ad)).toBe(tur);
  });

  it.each([
    "gunluk-Uydurgul-Masalcioglu.odbak",
    "gunluk-2026-09-01-kopya.odbak",
    "kopya-gunluk-2026-09-01.odbak",
    "pre-migrate-Uydurgul-Masalcioglu-2020-01-01.odbak",
    "pre-parola-2026-09-01.odbak",
    "okulun-yedegi.odbak",
    "oab-defteri-yedek-2026-11-06-101530.odbak",
    // F4'ün türleri: adları o fazdadır.
    "pre-kapanis-2026-09-01.odbak",
    "pre-dek-yenileme-2026-09-01.odbak",
    "pre-anonim-2026-09-01-101530.odbak",
  ])("elle adlandırılmış ya da F4'ün dosyasında tür yazılmaz: %s", (ad) => {
    expect(yedekTuru(ad)).toBeNull();
  });
});

describe("kapsamMetni", () => {
  it("iki kapsamın sözü kullanıcı kararındaki gibidir; okunamıyorsa yoktur", () => {
    expect(kapsamMetni("yerel")).toBe("yalnız kayıtlar; ekler bu bilgisayardan alınır");
    expect(kapsamMetni("tam")).toBe("kayıtlar, ekler ve üretilen evrak");
    expect(kapsamMetni(null)).toBeNull();
  });
});

describe("yedekAciklamasi", () => {
  it("tür ve kapsam yan yana; biri yoksa öteki kalır; ikisi de yoksa satır yoktur", () => {
    expect(yedekAciklamasi("gunluk-2026-09-01.odbak", "yerel")).toBe(
      "Günlük yedek · yalnız kayıtlar; ekler bu bilgisayardan alınır",
    );
    expect(yedekAciklamasi("gunluk-2026-09-01.odbak", null)).toBe("Günlük yedek");
    expect(yedekAciklamasi("okulun-yedegi.odbak", "tam")).toBe("kayıtlar, ekler ve üretilen evrak");
    expect(yedekAciklamasi("okulun-yedegi.odbak", null)).toBeNull();
  });
});

describe("yoldanDosyaAdi", () => {
  it.each([
    ["E:\\Okul Yedekleri\\Şubat ayı ğüşıöç.odbak", "Şubat ayı ğüşıöç.odbak"],
    ["/media/öğretmen/USB BELLEK/günlük yedek.odbak", "günlük yedek.odbak"],
    ["\\\\sunucu\\pay\\yedek.odbak", "yedek.odbak"],
    ["E:\\Okul/iç klasör\\son yedek.odbak", "son yedek.odbak"],
    ["E:/Okul\\iç klasör/son yedek.odbak", "son yedek.odbak"],
    ["ayracsiz.odbak", "ayracsiz.odbak"],
  ])("iki ayracı da tanır: %s", (yol, ad) => {
    expect(yoldanDosyaAdi(yol)).toBe(ad);
  });
});

describe("yedekBoyuSatiri", () => {
  it("boyu ve ek sayısını yan yana yazar; bilinmeyen parça yazılmaz, ikisi yoksa satır yoktur", () => {
    expect(yedekBoyuSatiri(3 * 1024 * 1024, 1200)).toBe("Boy: 3 MB · Taşıdığı ek: 1.200");
    expect(yedekBoyuSatiri(3 * 1024 * 1024, null)).toBe("Boy: 3 MB");
    expect(yedekBoyuSatiri(null, 0)).toBe("Taşıdığı ek: 0");
    expect(yedekBoyuSatiri(null, null)).toBeNull();
  });
});

describe("ekSatiriMetni", () => {
  it("durum, kayıt türü, kayıt no, tarih ve boy sırasıyla yazar", () => {
    expect(ekSatiriMetni(EK)).toBe("Eksik · ders yılı · no 7 · 01.10.2026 · 4 KB");
    expect(ekSatiriMetni({ ...EK, durum: "bozuk" })).toBe(
      "Bozuk · ders yılı · no 7 · 01.10.2026 · 4 KB",
    );
  });

  it("yedek alınırken eksik işaretlenmiş ek bunu söyler", () => {
    expect(ekSatiriMetni({ ...EK, yedekte_yoktu: true })).toBe(
      "Eksik (yedek alınırken bulunamadı ya da bozuktu) · ders yılı · no 7 · 01.10.2026 · 4 KB",
    );
  });

  it("kaydı bulunamayan ekte no yazılmaz, tarih yerine tarih yok der", () => {
    expect(
      ekSatiriMetni({
        ...EK,
        durum: "bozuk",
        kayit_turu: "Kaydı bulunamadı",
        kayit_no: "",
        yukleme_tarihi: null,
      }),
    ).toBe("Bozuk · Kaydı bulunamadı · tarih yok · 4 KB");
  });
});

describe("eksikEkCumlesi", () => {
  it("eksik ile bozuğu tek sayıda söyler", () => {
    expect(eksikEkCumlesi(1234)).toBe("1.234 ek yedek alınırken bulunamadı ya da bozuktu.");
  });
});

describe("eklerSatiri", () => {
  it("sıfır olan sayıyı yazmaz", () => {
    expect(eklerSatiri({ ...SIFIR, yerine_konan: 3 })).toBe("Ekler: 3 ek yerine kondu");
    expect(eklerSatiri({ ...SIFIR, yetimden_donen: 2, eksik: 1 })).toBe(
      "Ekler: 2 ek geri alındı · 1 ek eksik",
    );
  });

  it("onayla geride bırakılan bozuk ek iki kez sayılmaz: sunucunun iki sayısı aynı eklerdir", () => {
    expect(eklerSatiri({ ...SIFIR, bozuk: 2, onayla_suruldu: 2 })).toBe(
      "Ekler: 2 bozuk ek onayla geride bırakıldı",
    );
  });

  it("onaysız kalan bozuk ek kendi parçasında kalır", () => {
    expect(eklerSatiri({ ...SIFIR, bozuk: 3, onayla_suruldu: 1 })).toBe(
      "Ekler: 2 ek bozuk · 1 bozuk ek onayla geride bırakıldı",
    );
    expect(eklerSatiri({ ...SIFIR, bozuk: 1 })).toBe("Ekler: 1 ek bozuk");
  });

  it("hiç sayı yoksa eksik ya da bozuk ek olmadığını söyler", () => {
    expect(eklerSatiri(SIFIR)).toBe("Ekler: eksik ya da bozuk ek yok");
  });
});

describe("eklerOzeti", () => {
  it("geri yükleme kartının satırı aynı sayıları önek olmadan yazar", () => {
    expect(eklerOzeti({ ...SIFIR, yerine_konan: 3, bozuk: 1 })).toBe(
      "3 ek yerine kondu · 1 ek bozuk",
    );
    expect(eklerOzeti(SIFIR)).toBe("eksik ya da bozuk ek yok");
  });

  it.each(["yerine_konan", "yetimden_donen", "eksik", "bozuk", "onayla_suruldu"] as const)(
    "%s yoksa satır yoktur: olmayan sayı sıfır sayılmaz",
    (alan) => {
      const { [alan]: _atilan, ...kalan } = SIFIR;
      expect(eklerOzeti(kalan)).toBeNull();
    },
  );

  it("eski satırın boş nesnesinde satır yoktur", () => {
    expect(eklerOzeti({})).toBeNull();
  });
});

describe("AZAMI_YEDEK_DOSYASI", () => {
  it("sunucunun gövde sınırıyla aynı değerdir (8 GiB; desktop/server.py)", () => {
    expect(AZAMI_YEDEK_DOSYASI).toBe(8 * 1024 * 1024 * 1024);
  });
});
