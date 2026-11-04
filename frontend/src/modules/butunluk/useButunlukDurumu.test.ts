// Bütünlük durumunun düzenlenmesi: eksik alanlı ya da beklenmeyen yanıt kartları düşürmez
// (eksik liste boş, eksik nesne null); nesne olmayan yanıt "okunamadı"dır (kartlar görünmez).
// Kanca yetki yüklenirken hiçbir ucu çağırmaz, yetki değişmedikçe yeniden okumaz (plan F1b-2);
// yetki (oturum özeti) okunamazsa "okunamadı" der ve yalnız her role açık kendi kartlarını okur.

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { butunlukApi } from "./api";
import type { ButunlukDurumu, ButunlukYetkisi, GeriYuklemeOzeti } from "./api";
import useButunlukDurumu, { duzenle, okunamadiSayilir } from "./useButunlukDurumu";

const DURUM: ButunlukDurumu = {
  butunluk: [],
  geri_yukleme: null,
  iki_depo: {
    fark_var: true,
    sarmalsiz_hesaplar: [],
    silinebilir_sarmallar: [
      { id: "s-1", tanitici: "eski-hesap", rol_etiketi: null, kapali: false },
    ],
    muhru_tutmayan: [
      { id: "h-4", tanitici: "dk-1", rol_etiketi: "Denetleme Kurulu", kapali: false },
    ],
  },
  kagit_capasi: { kayit_no: 3, zincir: "AAAA-BBBB" },
  son_girisler: [],
  parola_yenilenme: null,
  okunamayan: [],
};

afterEach(() => vi.restoreAllMocks());

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

describe("useButunlukDurumu", () => {
  it("yetki bilinmeden hiçbir uç çağrılmaz; bilinince rolün yetkisiyle bir kez okunur", async () => {
    const durum = vi.spyOn(butunlukApi, "durum").mockResolvedValue(DURUM);
    const { result, rerender } = renderHook(
      ({ yetki }: { yetki: { denetim: boolean; ikiDepo: boolean } | null }) =>
        useButunlukDurumu(yetki),
      { initialProps: { yetki: null } as { yetki: { denetim: boolean; ikiDepo: boolean } | null } },
    );
    expect(durum).not.toHaveBeenCalled();
    expect(result.current.durum).toBeNull();

    rerender({ yetki: { denetim: true, ikiDepo: false } });
    await waitFor(() => expect(result.current.durum).toEqual(DURUM));
    expect(durum).toHaveBeenCalledTimes(1);
    expect(durum).toHaveBeenCalledWith({ denetim: true, ikiDepo: false });

    // Oturum özetinin yeni yoklaması aynı yetkiyi verirse yeniden okunmaz.
    rerender({ yetki: { denetim: true, ikiDepo: false } });
    expect(durum).toHaveBeenCalledTimes(1);
  });

  it("silmeden dönen iki depo kartı yazılır, mührü tutmayan hesaplar kalır", async () => {
    vi.spyOn(butunlukApi, "durum").mockResolvedValue(DURUM);
    const { result } = renderHook(() => useButunlukDurumu({ denetim: true, ikiDepo: true }));
    await waitFor(() => expect(result.current.durum).not.toBeNull());

    act(() =>
      result.current.ikiDepoyuYaz({
        iki_depo: { fark_var: false, sarmalsiz_hesaplar: [], silinebilir_sarmallar: [] },
        okunamayan: [],
      }),
    );

    expect(result.current.durum?.iki_depo?.silinebilir_sarmallar).toEqual([]);
    expect(result.current.durum?.iki_depo?.muhru_tutmayan).toEqual(DURUM.iki_depo?.muhru_tutmayan);
  });

  it("okuma düşerse “okunamadı”; kilitliyken değil", async () => {
    vi.spyOn(butunlukApi, "durum").mockRejectedValue(new ApiError(500, "500", "Hata."));
    const { result } = renderHook(() => useButunlukDurumu({ denetim: false, ikiDepo: false }));
    await waitFor(() => expect(result.current.okunamadi).toBe(true));
  });

  it("yetki okunamazsa “okunamadı”; yalnız kendi kartları okunur, özet gelince rolün uçları", async () => {
    // Bağımsız denetim bulgusu: oturum özeti düşünce hiçbir uç çağrılmıyor, uyarı kartı da
    // çıkmıyordu (fail-closed kuralına aykırı).
    const durum = vi.spyOn(butunlukApi, "durum").mockResolvedValue(DURUM);
    const { result, rerender } = renderHook(
      ({ yetki, hata }: { yetki: ButunlukYetkisi | null; hata: unknown }) =>
        useButunlukDurumu(yetki, hata),
      {
        initialProps: {
          yetki: null,
          hata: new ApiError(500, "500", "Sunucu hatası."),
        } as { yetki: ButunlukYetkisi | null; hata: unknown },
      },
    );
    expect(result.current.okunamadi).toBe(true);
    await waitFor(() => expect(result.current.durum).toEqual(DURUM));
    expect(durum).toHaveBeenCalledTimes(1);
    expect(durum).toHaveBeenCalledWith({ denetim: false, ikiDepo: false });
    // Kendi kartları okunsa da uyarı kalır: denetim kartlarının bu role açıklığı bilinmiyor.
    expect(result.current.okunamadi).toBe(true);

    rerender({ yetki: { denetim: true, ikiDepo: true }, hata: null });
    expect(result.current.okunamadi).toBe(false);
    await waitFor(() => expect(durum).toHaveBeenCalledTimes(2));
    expect(durum).toHaveBeenLastCalledWith({ denetim: true, ikiDepo: true });
  });

  it("yetki kilit (423) ya da düşen anahtar (409) yüzünden okunamazsa uyarı yok, uç çağrılmaz", () => {
    const durum = vi.spyOn(butunlukApi, "durum").mockResolvedValue(DURUM);
    for (const hata of [
      new ApiError(423, "locked", "Kayıtlar kilitli."),
      new ApiError(409, "parola_gerekli", "Kilitli."),
    ]) {
      const { result, unmount } = renderHook(() => useButunlukDurumu(null, hata));
      expect(result.current.okunamadi).toBe(false);
      unmount();
    }
    expect(durum).not.toHaveBeenCalled();
  });
});

describe("useButunlukDurumu — geri yükleme kartının “Gördüm”ü", () => {
  const YETKI: ButunlukYetkisi = { denetim: true, ikiDepo: false };
  const GERI = { seq: 40, onceki_geri_yuklemeler: [] } as unknown as GeriYuklemeOzeti;

  it("“Gördüm”den dönen denetim kartları duruma yazılır (yeniden okuma yok)", async () => {
    const durum = vi
      .spyOn(butunlukApi, "durum")
      .mockResolvedValue({ ...DURUM, geri_yukleme: GERI });
    const { result } = renderHook(() => useButunlukDurumu(YETKI));
    await waitFor(() => expect(result.current.durum?.geri_yukleme).toEqual(GERI));

    act(() =>
      result.current.denetimiYaz({
        butunluk: [],
        geri_yukleme: null,
        muhru_tutmayan: [],
        okunamayan: [],
      }),
    );

    expect(result.current.durum?.geri_yukleme).toBeNull();
    // İki depo kaydı korunur; mührü tutmayanlar yanıttan.
    expect(result.current.durum?.iki_depo?.silinebilir_sarmallar).toHaveLength(1);
    expect(result.current.durum?.iki_depo?.muhru_tutmayan).toEqual([]);
    expect(durum).toHaveBeenCalledTimes(1);
  });

  it("yenile uçları aynı yetkiyle bir kez daha okutur", async () => {
    const durum = vi.spyOn(butunlukApi, "durum").mockResolvedValue(DURUM);
    const { result } = renderHook(() => useButunlukDurumu(YETKI));
    await waitFor(() => expect(durum).toHaveBeenCalledTimes(1));

    act(() => result.current.yenile());

    await waitFor(() => expect(durum).toHaveBeenCalledTimes(2));
    expect(durum).toHaveBeenLastCalledWith(YETKI);
  });

  it("durum henüz yoksa denetim yanıtı yazılmaz", () => {
    vi.spyOn(butunlukApi, "durum").mockReturnValue(new Promise(() => undefined));
    const { result } = renderHook(() => useButunlukDurumu(YETKI));

    act(() =>
      result.current.denetimiYaz({
        butunluk: [],
        geri_yukleme: null,
        muhru_tutmayan: [],
        okunamayan: [],
      }),
    );

    expect(result.current.durum).toBeNull();
  });
});
