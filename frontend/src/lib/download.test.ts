// saveBlob: masaüstünde dosyayı program kaydeder (`dosya_kaydet`; kullanıcı kararı 07.11.2026
// "Program kaydetsin"), köprü yoksa DOM akışı: createObjectURL → <a download> → revoke.

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
    vi.unstubAllGlobals();
    delete window.pywebview;
  });

  function urlYakala() {
    const createObjectURL = vi.fn(() => "blob:test-url");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    return { createObjectURL, revokeObjectURL, click };
  }

  it("köprü yoksa blob için geçici URL açar, bağlantıyı tıklar, URL'yi gecikmeli bırakır", async () => {
    vi.useFakeTimers();
    const { createObjectURL, revokeObjectURL, click } = urlYakala();

    await expect(saveBlob(new Blob(["test"]), "dosya.xlsx")).resolves.toBe("indirildi");

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).not.toHaveBeenCalled();
    // Bağlantı DOM'da bırakılmadı.
    expect(document.querySelector("a[download]")).toBeNull();

    vi.advanceTimersByTime(1_000);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test-url");
  });

  it("pencere eskiyse (köprüde işlev yoksa) tarayıcının indirmesine düşer", async () => {
    const { click } = urlYakala();
    window.pywebview = { api: { set_titlebar_theme: vi.fn() } };

    await expect(saveBlob(new Blob(["test"]), "dosya.xlsx")).resolves.toBe("indirildi");

    expect(click).toHaveBeenCalledTimes(1);
  });

  it("köprü varsa içeriği base64 metin, adı önerilen ad olarak verir; bağlantı tıklanmaz", async () => {
    const { createObjectURL, click } = urlYakala();
    const dosya_kaydet = vi.fn().mockResolvedValue("kaydedildi");
    window.pywebview = { api: { dosya_kaydet } };

    await expect(
      saveBlob(new Blob(["çğ%PDF"], { type: "application/pdf" }), "Yedek-Raporu.pdf"),
    ).resolves.toBe("kaydedildi");

    expect(dosya_kaydet).toHaveBeenCalledTimes(1);
    const [icerik, ad] = dosya_kaydet.mock.calls[0] as [string, string];
    expect(ad).toBe("Yedek-Raporu.pdf");
    expect(new TextDecoder().decode(Uint8Array.from(atob(icerik), (c) => c.charCodeAt(0)))).toBe(
      "çğ%PDF",
    );
    expect(createObjectURL).not.toHaveBeenCalled();
    expect(click).not.toHaveBeenCalled();
  });

  it("ev klasörü işareti yalnız istenince köprüye true gider (kurtarma anahtarı belgesi)", async () => {
    const dosya_kaydet = vi.fn().mockResolvedValue("kaydedildi");
    window.pywebview = { api: { dosya_kaydet } };

    await saveBlob(new Blob(["a"]), "Yedek-Raporu.pdf");
    await saveBlob(new Blob(["a"]), "Kurtarma-Anahtarı-Belgesi.pdf", { evKlasorunde: true });

    expect(dosya_kaydet.mock.calls.map((cagri) => cagri[2])).toEqual([false, true]);
  });

  it.each([
    ["iptal", "iptal"],
    ["hata", "hata"],
    // Köprünün tanımadığı dönüşü başarı sayılmaz.
    ["belirsiz", "hata"],
  ])("köprünün %s dönüşü sonuç olarak yansır", async (donus, beklenen) => {
    window.pywebview = { api: { dosya_kaydet: vi.fn().mockResolvedValue(donus) } };

    await expect(saveBlob(new Blob(["test"]), "dosya.pdf")).resolves.toBe(beklenen);
  });

  it("blob okunamazsa sonuç hatadır; köprüye boş içerik gitmez", async () => {
    const dosya_kaydet = vi.fn().mockResolvedValue("kaydedildi");
    window.pywebview = { api: { dosya_kaydet } };
    class OkunamayanOkuyucu {
      error = new DOMException("okunamadı", "NotReadableError");
      onerror: (() => void) | null = null;
      readAsDataURL() {
        queueMicrotask(() => this.onerror?.());
      }
    }
    vi.stubGlobal("FileReader", OkunamayanOkuyucu);

    await expect(saveBlob(new Blob(["test"]), "dosya.pdf")).resolves.toBe("hata");

    expect(dosya_kaydet).not.toHaveBeenCalled();
  });

  it("köprü reddederse sonuç hatadır; ret çağırana yükselmez", async () => {
    window.pywebview = { api: { dosya_kaydet: vi.fn().mockRejectedValue(new Error("köprü")) } };

    await expect(saveBlob(new Blob(["test"]), "dosya.pdf")).resolves.toBe("hata");
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
