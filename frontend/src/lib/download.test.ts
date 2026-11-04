// saveBlob DOM akışı testi (Tur 535): createObjectURL → <a download> → revoke.

import { afterEach, describe, expect, it, vi } from "vitest";

import { basliktanDosyaAdi, dosyaAdi, saveBlob } from "./download";

describe("dosyaAdi", () => {
  it("belge + kapsam + tarihten okunur dosya adı kurar (Türkçe harf korunur)", () => {
    expect(dosyaAdi(["Genel Kurul Toplantı Tutanağı", "2026-2027", "16.11.2026"], "pdf")).toBe(
      "Genel-Kurul-Toplantı-Tutanağı_2026-2027_16.11.2026.pdf",
    );
  });

  it("dosya sisteminin yasakladığı karakterleri atar, boş parçayı düşürür", () => {
    expect(dosyaAdi(['9/A: "Deneme" <1>', "", null, "Liste?"], ".zip")).toBe(
      "9A-Deneme-1_Liste.zip",
    );
    expect(dosyaAdi([], "pdf")).toBe("belge.pdf");
    // Ters bölü Windows'ta yol ayracıdır; bölüm adında geçerse dosya adını böler.
    expect(dosyaAdi(["Teslim Listesi", "B\\Blok 101"], "pdf")).toBe("Teslim-Listesi_BBlok-101.pdf");
  });
});

describe("saveBlob", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("blob için geçici URL açar, bağlantıyı tıklar ve URL'yi gecikmeli bırakır", () => {
    vi.useFakeTimers();
    const createObjectURL = vi.fn(() => "blob:test-url");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    saveBlob(new Blob(["test"]), "dosya.xlsx");

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).not.toHaveBeenCalled();
    // Bağlantı DOM'da bırakılmadı.
    expect(document.querySelector("a[download]")).toBeNull();

    vi.advanceTimersByTime(1_000);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test-url");
  });
});

describe("basliktanDosyaAdi", () => {
  it("Django'nun Türkçe harfli adını (filename*=utf-8''…, RFC 5987) çözer", () => {
    // Backend `test_evrak_kurallari`'nın beklediği başlık: `attachment; filename*=utf-8''{quote(ad)}`.
    const ad = "Hesap-Teslim-Pusulası_Başkan_03.11.2026.pdf";
    expect(basliktanDosyaAdi(`attachment; filename*=utf-8''${encodeURIComponent(ad)}`)).toBe(ad);
    expect(basliktanDosyaAdi("attachment; filename*=UTF-8'tr'Program-y%C3%B6neticisi.pdf")).toBe(
      "Program-yöneticisi.pdf",
    );
  });

  it("ASCII yedeği: tırnaklı ve tırnaksız filename, ters bölü kaçışı", () => {
    expect(basliktanDosyaAdi('attachment; filename="Kurtarma.pdf"')).toBe("Kurtarma.pdf");
    expect(basliktanDosyaAdi("attachment; filename=rapor.pdf")).toBe("rapor.pdf");
    expect(basliktanDosyaAdi('attachment; filename="a\\"b.pdf"')).toBe('a"b.pdf');
  });

  it("ikisi birden varsa filename* önce gelir; biçimsiz filename* yedeğe düşer", () => {
    expect(
      basliktanDosyaAdi("attachment; filename=\"yedek.pdf\"; filename*=utf-8''%C3%A7.pdf"),
    ).toBe("ç.pdf");
    // Geçersiz UTF-8 baytı, eksik yüzde kodu ve bilinmeyen karakter kümesi.
    for (const bozuk of ["utf-8''%E0%A4.pdf", "utf-8''%G1.pdf", "utf-16''%00a"]) {
      expect(basliktanDosyaAdi(`attachment; filename*=${bozuk}; filename="duz.pdf"`)).toBe(
        "duz.pdf",
      );
      expect(basliktanDosyaAdi(`attachment; filename*=${bozuk}`)).toBeNull();
    }
    // Kodlanmamış ASCII dışı karakter biçimsizdir.
    expect(basliktanDosyaAdi("attachment; filename*=utf-8''ç.pdf")).toBeNull();
  });

  it("ISO-8859-1 karakter kümesini çözer", () => {
    expect(basliktanDosyaAdi("attachment; filename*=iso-8859-1'en'%E7a.pdf")).toBe("ça.pdf");
  });

  it("ad yol taşımaz, denetim karakteri taşımaz", () => {
    expect(basliktanDosyaAdi('attachment; filename="../../gizli/x.pdf"')).toBe("x.pdf");
    expect(basliktanDosyaAdi("attachment; filename*=utf-8''..%5C..%5Cx.pdf")).toBe("x.pdf");
    expect(basliktanDosyaAdi("attachment; filename*=utf-8''a%0Ab.pdf")).toBe("ab.pdf");
    expect(basliktanDosyaAdi('attachment; filename=".."')).toBeNull();
  });

  it("başlık yoksa ya da ad taşımıyorsa null", () => {
    expect(basliktanDosyaAdi(null)).toBeNull();
    expect(basliktanDosyaAdi(undefined)).toBeNull();
    expect(basliktanDosyaAdi("")).toBeNull();
    expect(basliktanDosyaAdi("inline")).toBeNull();
    expect(basliktanDosyaAdi('attachment; filename=""')).toBeNull();
  });
});
