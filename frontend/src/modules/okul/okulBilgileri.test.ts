// Okul kartının form modeli: zorunlu alan iletileri (backend `SchoolConfigSerializer` ve
// `missing_school_fields` ile birebir), kayıttan forma ve formdan gövdeye dönüşüm (kırpma,
// sayı çevirme, kademe sırası), mevcudun tarihinin varsayılanı. Veriler uydurmadır.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BOS_OKUL_KARTI, ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import {
  bosOkulFormu,
  formdanGovdeye,
  kademeleriSirala,
  kayittanForma,
  mevcutSayisi,
  okulBilgileriHatalari,
} from "./okulBilgileri";
import type { OkulFormu } from "./okulBilgileri";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 7, 10, 0, 0));
});
afterEach(() => vi.useRealTimers());

/** Bütün zorunlu alanları geçerli form. */
function tamForm(): OkulFormu {
  return kayittanForma(ORNEK_OKUL_KARTI);
}

describe("okulBilgileriHatalari", () => {
  it("tam formda hata yoktur", () => {
    expect(okulBilgileriHatalari(tamForm())).toEqual({});
  });

  it("boş formda her zorunlu alan kendi iletisiyle döner (backend alan kodlarıyla)", () => {
    expect(okulBilgileriHatalari({ ...bosOkulFormu(), mevcutTarihi: "" })).toEqual({
      school_name: "Okul adı zorunludur.",
      province: "İl zorunludur.",
      district: "İlçe zorunludur.",
      institution_code: "Kurum kodu zorunludur.",
      levels: "En az bir kademe seçin.",
      student_count: "Öğrenci mevcudu zorunludur.",
      student_count_as_of: "Mevcudun tarihi zorunludur.",
      settlement_type: "Yerleşim türünü seçin.",
      canteen_mode: "Kantin işletme biçimini seçin.",
      staffing_mode: "Personel çalıştırma biçimini seçin.",
      demirbas_onayi: "Program yalnız okul demirbaşı bilgisayara kurulur; onay zorunludur.",
    });
  });

  it("yalnız boşluktan oluşan metin boş sayılır", () => {
    const h = okulBilgileriHatalari({ ...tamForm(), okulAdi: "   ", il: " ", ilce: "\t" });
    expect(h.school_name).toBe("Okul adı zorunludur.");
    expect(h.province).toBe("İl zorunludur.");
    expect(h.district).toBe("İlçe zorunludur.");
  });

  it.each(["12345", "1234567", "12345a", "12 456", "ABCDEF"])(
    "kurum kodu “%s” altı rakam değildir",
    (kod) => {
      expect(okulBilgileriHatalari({ ...tamForm(), kurumKodu: kod }).institution_code).toBe(
        "Kurum kodu altı haneli bir sayıdır.",
      );
    },
  );

  it("kurum kodu baştan ve sondan kırpılarak denetlenir", () => {
    expect(okulBilgileriHatalari({ ...tamForm(), kurumKodu: " 012345 " })).toEqual({});
  });

  it.each(["-1", "12,5", "1.5", "100000", "on iki", "1e3"])(
    "öğrenci mevcudu “%s” aralık iletisini verir",
    (mevcut) => {
      expect(okulBilgileriHatalari({ ...tamForm(), mevcut }).student_count).toBe(
        "Öğrenci mevcudu 0 ile 99999 arasında bir tam sayıdır.",
      );
    },
  );

  it.each(["0", "99999", "1.234", " 480 "])("öğrenci mevcudu “%s” geçerlidir", (mevcut) => {
    expect(okulBilgileriHatalari({ ...tamForm(), mevcut })).toEqual({});
  });

  it("mevcudun tarihi bugün olabilir, yarın olamaz", () => {
    expect(okulBilgileriHatalari({ ...tamForm(), mevcutTarihi: "2026-11-07" })).toEqual({});
    expect(
      okulBilgileriHatalari({ ...tamForm(), mevcutTarihi: "2026-11-08" }).student_count_as_of,
    ).toBe("Mevcudun tarihi bugünden sonra olamaz.");
  });

  it("isteğe bağlı alanlar (müdür, kampüs, açılış tarihi, demirbaş no) hata vermez", () => {
    expect(
      okulBilgileriHatalari({ ...tamForm(), mudur: "", kampus: false, acilis: "", demirbasNo: "" }),
    ).toEqual({});
  });
});

describe("mevcutSayisi", () => {
  it("boş → null, geçerli → sayı, geçersiz → NaN", () => {
    expect(mevcutSayisi("")).toBeNull();
    expect(mevcutSayisi("  ")).toBeNull();
    expect(mevcutSayisi("0")).toBe(0);
    expect(mevcutSayisi("1.234")).toBe(1234);
    expect(mevcutSayisi("12.345")).toBe(12345);
    expect(mevcutSayisi("1.23")).toBeNaN();
    expect(mevcutSayisi("100000")).toBeNaN();
  });
});

describe("kayıttan forma, formdan gövdeye", () => {
  it("boş formun mevcut tarihi bugündür", () => {
    expect(bosOkulFormu().mevcutTarihi).toBe("2026-11-07");
  });

  it("kayıtta mevcudun tarihi yoksa form bugünü önerir; varsa kayıttakini korur", () => {
    expect(kayittanForma(BOS_OKUL_KARTI).mevcutTarihi).toBe("2026-11-07");
    expect(kayittanForma(ORNEK_OKUL_KARTI).mevcutTarihi).toBe("2026-10-01");
  });

  it("kayıttaki sayı metne, boş tarih boş metne çevrilir", () => {
    const f = kayittanForma({ ...ORNEK_OKUL_KARTI, opened_on: null });
    expect(f.mevcut).toBe("1234");
    expect(f.acilis).toBe("");
    expect(kayittanForma(BOS_OKUL_KARTI).mevcut).toBe("");
  });

  it("gövdede metinler kırpılır, sayı tam sayıya çevrilir, kademeler backend sırasıyla gider", () => {
    const govde = formdanGovdeye({
      okulAdi: "  Örnek Ortaokulu ",
      il: " İstanbul",
      ilce: "Örnek İlçe  ",
      mudur: " ",
      kurumKodu: " 654321 ",
      kademeler: ["ORTAOKUL", "OKUL_ONCESI", "ILKOKUL", "ORTAOKUL"],
      mevcut: " 1.234 ",
      mevcutTarihi: "2026-10-01",
      yerlesim: "IL_MERKEZI_BUYUKSEHIR_DEGIL",
      kantin: "BIRLIKCE_ISLETILIYOR",
      personel: "DOGRUDAN_ISVEREN",
      kampus: true,
      acilis: "2025-09-08",
      demirbasOnayi: true,
      demirbasNo: " BLG-17 ",
    });
    expect(govde).toEqual({
      school_name: "Örnek Ortaokulu",
      province: "İstanbul",
      district: "Örnek İlçe",
      principal_name: "",
      institution_code: "654321",
      levels: ["OKUL_ONCESI", "ILKOKUL", "ORTAOKUL"],
      student_count: 1234,
      student_count_as_of: "2026-10-01",
      settlement_type: "IL_MERKEZI_BUYUKSEHIR_DEGIL",
      canteen_mode: "BIRLIKCE_ISLETILIYOR",
      staffing_mode: "DOGRUDAN_ISVEREN",
      in_campus: true,
      opened_on: "2025-09-08",
      demirbas_onayi: true,
      demirbas_no: "BLG-17",
    });
  });

  it("boşaltılan açılış tarihi ve girilmemiş mevcut gövdede null gider", () => {
    const govde = formdanGovdeye({ ...tamForm(), acilis: "", mevcut: "", mevcutTarihi: "" });
    expect(govde.opened_on).toBeNull();
    expect(govde.student_count).toBeNull();
    expect(govde.student_count_as_of).toBeNull();
  });

  it("kayıt → form → gövde gidiş-dönüşü kaydı değiştirmez", () => {
    const { setup_completed: _tamam, ...beklenen } = ORNEK_OKUL_KARTI;
    expect(formdanGovdeye(kayittanForma(ORNEK_OKUL_KARTI))).toEqual(beklenen);
  });

  it("kademeleriSirala tekrarı atar ve backend sırasına dizer", () => {
    expect(kademeleriSirala(["ORTAOGRETIM", "ILKOKUL", "ORTAOGRETIM"])).toEqual([
      "ILKOKUL",
      "ORTAOGRETIM",
    ]);
  });
});
