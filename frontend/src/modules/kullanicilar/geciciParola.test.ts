// Geçici parola önerisi (plan F1b-2 "Geçici parola"): politikaya uyar, 12 karakterdir, karışabilecek
// karakter içermez, güvenli rastgele kaynaktan gelir (Math.random kullanılmaz), seçim eğilimsizdir.

import { afterEach, describe, expect, it, vi } from "vitest";

import { eksikTurler, parolaSorunu } from "../oturum/parolaPolitikasi";
import {
  BUYUK_HARFLER,
  GECICI_PAROLA_UZUNLUGU,
  KARISABILECEKLER,
  KUCUK_HARFLER,
  ONERI_ALFABESI,
  RAKAMLAR,
  SIMGELER,
  geciciParolaOner,
  rastgeleSira,
} from "./geciciParola";
import type { RastgeleKaynak } from "./geciciParola";

/** Verilen sayıları sırayla döndüren kaynak (bitince başa döner). */
function siraliKaynak(sayilar: number[]): RastgeleKaynak {
  let i = 0;
  return (dizi) => {
    for (let j = 0; j < dizi.length; j += 1) {
      dizi[j] = sayilar[i % sayilar.length];
      i += 1;
    }
    return dizi;
  };
}

afterEach(() => vi.restoreAllMocks());

describe("geciciParolaOner", () => {
  it("her öneri 12 karakterdir, politikaya uyar ve dört türü de taşır", () => {
    for (let n = 0; n < 500; n += 1) {
      const oneri = geciciParolaOner();
      expect([...oneri]).toHaveLength(GECICI_PAROLA_UZUNLUGU);
      expect(GECICI_PAROLA_UZUNLUGU).toBeGreaterThanOrEqual(12);
      expect(parolaSorunu(oneri)).toBeNull();
      expect(eksikTurler(oneri)).toEqual([]);
      for (const tur of [KUCUK_HARFLER, BUYUK_HARFLER, RAKAMLAR, SIMGELER]) {
        expect([...oneri].some((k) => tur.includes(k))).toBe(true);
      }
    }
  });

  it("karışabilecek karakter (0/O, 1/l/I, ı/İ, büyük-küçük karışan harfler) içermez", () => {
    for (const k of KARISABILECEKLER) expect(ONERI_ALFABESI).not.toContain(k);
    for (let n = 0; n < 500; n += 1) {
      for (const k of geciciParolaOner()) {
        expect(ONERI_ALFABESI).toContain(k);
        expect(KARISABILECEKLER).not.toContain(k);
      }
    }
    // Elle yazılınca birbirine karışan çiftlerin en çok biri alfabededir (küçük t, + ile de f ile de
    // karışır; t çıkarıldı).
    for (const [a, b] of [
      ["t", "+"],
      ["t", "f"],
      ["1", "l"],
      ["0", "O"],
      ["2", "Z"],
      ["5", "S"],
      ["6", "G"],
      ["8", "B"],
      ["9", "g"],
    ]) {
      expect([a, b].filter((k) => ONERI_ALFABESI.includes(k)).length, `${a}/${b}`).toBeLessThan(2);
    }
    expect(KARISABILECEKLER).toContain("t");
    expect(ONERI_ALFABESI).toHaveLength(30);
    // Alfabe ASCII'dir, boşluk yoktur, her karakter bir kez geçer.
    expect(ONERI_ALFABESI).toMatch(/^[\x21-\x7e]+$/);
    expect(new Set(ONERI_ALFABESI).size).toBe(ONERI_ALFABESI.length);
  });

  it("güvenli rastgele kaynağı kullanır, Math.random'ı kullanmaz", () => {
    const guvenli = vi.spyOn(globalThis.crypto, "getRandomValues");
    const zayif = vi.spyOn(Math, "random");
    geciciParolaOner();
    expect(guvenli).toHaveBeenCalled();
    expect(zayif).not.toHaveBeenCalled();
  });

  it("türlerin yeri sabit değildir (öneri karıştırılır)", () => {
    // Karıştırılmasaydı ilk dört karakter hep küçük harf, büyük harf, rakam, simge olurdu.
    const turu = (k: string) =>
      [KUCUK_HARFLER, BUYUK_HARFLER, RAKAMLAR, SIMGELER].findIndex((t) => t.includes(k));
    const ilkler = new Set<number>();
    let dorduncuSimge = 0;
    for (let n = 0; n < 200; n += 1) {
      const oneri = geciciParolaOner();
      ilkler.add(turu(oneri[0]));
      if (turu(oneri[3]) === 3) dorduncuSimge += 1;
    }
    expect(ilkler.size).toBeGreaterThan(1);
    expect(dorduncuSimge).toBeLessThan(200);
  });

  it("aynı kaynak aynı öneriyi verir; öneriler birbirinden ayrılır", () => {
    const sabit = [7, 3, 1, 0, 9, 22, 4, 15, 8, 2, 30, 11, 5, 6, 13, 17, 19, 23, 29, 10];
    expect(geciciParolaOner(siraliKaynak(sabit))).toBe(geciciParolaOner(siraliKaynak(sabit)));
    const oneriler = new Set(Array.from({ length: 50 }, () => geciciParolaOner()));
    expect(oneriler.size).toBe(50);
  });
});

describe("rastgeleSira", () => {
  it("sınırın üstündeki değeri reddeder (modülo eğilimi yok)", () => {
    // n = 31: sınır 4 294 967 292; 0xFFFFFFFF reddedilir, sıradaki 5 alınır.
    expect(rastgeleSira(31, siraliKaynak([0xffffffff, 5]))).toBe(5);
    expect(rastgeleSira(31, siraliKaynak([4_294_967_291]))).toBe(4_294_967_291 % 31);
  });

  it("bozuk kaynak sonsuz döngüye sokmaz", () => {
    expect(() => rastgeleSira(31, siraliKaynak([0xffffffff]))).toThrow(
      "Rastgele sayı üretilemedi.",
    );
  });
});
