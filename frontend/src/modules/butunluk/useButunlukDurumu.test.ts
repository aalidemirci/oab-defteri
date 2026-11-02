// Bütünlük durumunun düzenlenmesi: eksik alanlı ya da beklenmeyen yanıt kartları düşürmez
// (eksik liste boş, eksik nesne null); nesne olmayan yanıt "okunamadı"dır (kartlar görünmez).

import { describe, expect, it } from "vitest";

import { ApiError } from "../../lib/api";
import { duzenle, okunamadiSayilir } from "./useButunlukDurumu";

describe("bütünlük durumunun düzenlenmesi", () => {
  it("eksik alanlar boş sayılır", () => {
    expect(duzenle({})).toEqual({
      butunluk: [],
      geri_yukleme: null,
      iki_depo: null,
      kagit_capasi: null,
      son_girisler: [],
      parola_yenilenme: null,
      okunamayan: [],
    });
  });

  it("eski yanıtın geri yükleme kartında öncekiler listesi boş sayılır; okunamayanlar korunur", () => {
    const d = duzenle({ geri_yukleme: { seq: 4 }, okunamayan: ["geri_yukleme"] });
    expect(d?.geri_yukleme?.onceki_geri_yuklemeler).toEqual([]);
    expect(d?.okunamayan).toEqual(["geri_yukleme"]);
  });

  it("dolu yanıt olduğu gibi kalır", () => {
    const capa = { kayit_no: 3, zincir: "AAAA-BBBB" };
    expect(duzenle({ kagit_capasi: capa, son_girisler: ["2026-11-01T10:00:00+03:00"] })).toEqual(
      expect.objectContaining({ kagit_capasi: capa, son_girisler: ["2026-11-01T10:00:00+03:00"] }),
    );
  });

  it("okuma hatası kilit ve düşen anahtar dışında uyarı kartıyla söylenir (fail-closed)", () => {
    expect(okunamadiSayilir(new ApiError(500, "500", "Sunucu hatası."))).toBe(true);
    expect(okunamadiSayilir(new TypeError("ağ yok"))).toBe(true);
    expect(okunamadiSayilir(new ApiError(423, "locked", "Kayıtlar kilitli."))).toBe(false);
    expect(okunamadiSayilir(new ApiError(409, "parola_gerekli", "Kilitli."))).toBe(false);
  });

  it("nesne olmayan yanıt okunamadı sayılır", () => {
    expect(duzenle(null)).toBeNull();
    expect(duzenle("beklenmeyen")).toBeNull();
  });
});
