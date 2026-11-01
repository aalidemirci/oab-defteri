// Kurtarma anahtarı paneli: anahtar gruplarıyla GÖRÜNÜR; yazdır, PDF
// olarak kaydet ve elle yaz yolları sunulur; devam, sakladığı kopyadan rastgele
// İKİ grubun geri yazdırılmasıyla doğrulanır (doğrulama kipinde anahtar ekrandan
// kalkar); iki grup tutunca TAM anahtar sunucuda doğrulanıp "saklandı" damgası
// yazılır (`kurtarma.dogrulandi`, tasarım §4.4.4) ve `onDogrulama(true)` ancak o zaman
// gelir. Anahtar
// ve okul adı uydurmadır.

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, etkinlikSaatleriniSifirla } from "../../lib/api";
import { SnackbarProvider } from "../../ui/SnackbarProvider";

const guvenlik = vi.hoisted(() => ({
  kurtarmaAnahtariPdf: vi.fn(),
  kurtarmaAnahtariniDogrula: vi.fn(),
}));
const indirme = vi.hoisted(() => ({ saveBlob: vi.fn() }));

vi.mock("./api", () => ({ guvenlikApi: guvenlik }));
vi.mock("../../lib/download", async (importOriginal) => {
  const gercek = await importOriginal<typeof import("../../lib/download")>();
  return { ...gercek, saveBlob: indirme.saveBlob };
});

import KurtarmaAnahtariPaneli, { BOSTA_GIZLEME_MS } from "./KurtarmaAnahtariPaneli";
import {
  KURTARMA_BELGESI_DOSYA_KOKU,
  guncelKurtarmaKimligi,
  kurtarmaAnahtariniNormallestir,
  kurtarmaBelgesiDosyaAdi,
  kurtarmaGruplari,
  kurtarmaKimligiMetni,
  rastgeleIkiGrup,
  yedekAnahtarCumlesi,
} from "./kurtarma";
import type { GuvenlikDurumu } from "./api";

const ANAHTAR = "TEST-KURT-ARMA-ANAH-TARI-ABCD-EFGH-JKLM";

/** `rastgele` sırayla bu değerleri döndürür → 2. ve 6. grup sorulur (0,1 → 1 ve 5). */
function sabitRastgele(...degerler: number[]): () => number {
  let i = 0;
  return () => degerler[i++ % degerler.length];
}

function bas(onDogrulama = vi.fn(), rastgele = sabitRastgele(0.125, 0.6)) {
  render(
    <SnackbarProvider>
      <KurtarmaAnahtariPaneli
        anahtar={ANAHTAR}
        okulAdi="Deneme Anadolu Lisesi"
        onDogrulama={onDogrulama}
        rastgele={rastgele}
      />
    </SnackbarProvider>,
  );
  return onDogrulama;
}

beforeEach(() => {
  guvenlik.kurtarmaAnahtariniDogrula.mockResolvedValue({ recovery_key_confirmed: true });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("kurtarma yardımcıları", () => {
  it("normalleştirme örnek tablosu backend ile aynı (Türkçe İ/ı dahil)", () => {
    // AYNI tablo backend'de sınanır: apps/okul/tests/test_app_password.py
    // NORMALLESTIRME_ORNEKLERI. Biri değişirse öteki de değişmeli.
    const ornekler: Array<[string, string]> = [
      [" test-kurt ", "TESTKURT"],
      ["o0i1b8", "OOIIBB"],
      ["abci-ABCI-ABCİ-ABCı", "ABCIABCIABCIABCI"],
      ["TARİ tarı Tari", "TARITARITARI"],
      ["ŞAKA-12", "AKAI2"],
    ];
    for (const [yazim, beklenen] of ornekler) {
      expect(kurtarmaAnahtariniNormallestir(yazim)).toBe(beklenen);
    }
  });

  it("Türkçe klavyede büyük harfle yazılan grup doğrulamayı geçer", () => {
    expect(kurtarmaGruplari(ANAHTAR.replace(/I/g, "İ"))).toEqual(ANAHTAR.split("-"));
  });

  it("anahtar dörtlü gruplara ayrılır", () => {
    expect(kurtarmaGruplari(ANAHTAR)).toEqual(ANAHTAR.split("-"));
  });

  it("iki farklı grup seçilir, sıralı döner", () => {
    for (const [a, b] of [
      [0, 0],
      [0.99, 0.99],
      [0.5, 0.1],
      [0.2, 0.9],
    ]) {
      const [x, y] = rastgeleIkiGrup(8, sabitRastgele(a, b));
      expect(x).toBeLessThan(y);
      expect(x).toBeGreaterThanOrEqual(0);
      expect(y).toBeLessThan(8);
    }
  });

  it("PDF dosya adı belge adı + yerel tarih taşır, anahtar taşımaz", () => {
    // Backend `recovery_key_document.DOCUMENT_NAME` + `recovery_key_pdf_filename` ile aynı:
    // Content-Disposition'daki adla ön yüzün kaydettiği ad birebir.
    expect(KURTARMA_BELGESI_DOSYA_KOKU).toBe("Kurtarma Anahtarı Belgesi");
    expect(kurtarmaBelgesiDosyaAdi()).toMatch(
      /^Kurtarma-Anahtarı-Belgesi_\d{2}\.\d{2}\.\d{4}\.pdf$/,
    );
  });

  it("anahtar kimliği no ve üretim tarihiyle yazılır; eksik parça atlanır", () => {
    expect(kurtarmaKimligiMetni({ no: 3, tarih: "2026-11-01" })).toBe(
      "Anahtar no 3 · üretim tarihi 01.11.2026",
    );
    expect(kurtarmaKimligiMetni({ no: 2, tarih: null })).toBe("Anahtar no 2");
    expect(kurtarmaKimligiMetni({ no: null, tarih: "2026-09-15" })).toBe(
      "Üretim tarihi 15.09.2026",
    );
    expect(kurtarmaKimligiMetni({ no: null, tarih: null })).toBeNull();
    expect(kurtarmaKimligiMetni(null)).toBeNull();
  });

  it("yedeği açan anahtar cümlesi (tasarım TK10) ve bilinmeyen kimlik", () => {
    expect(yedekAnahtarCumlesi({ no: 3, tarih: "2026-11-01" })).toBe(
      "Bu yedek 3 numaralı, 01.11.2026 tarihli kurtarma anahtarıyla açılır.",
    );
    expect(yedekAnahtarCumlesi({ no: 4, tarih: null })).toBe(
      "Bu yedek 4 numaralı kurtarma anahtarıyla açılır.",
    );
    expect(yedekAnahtarCumlesi({ no: null, tarih: "2026-11-01" })).toBe(
      "Bu yedek 01.11.2026 tarihli kurtarma anahtarıyla açılır.",
    );
    expect(yedekAnahtarCumlesi(null)).toBe(
      "Bu yedeği hangi kurtarma anahtarının açtığı okunamadı.",
    );
  });

  it("güvenlik durumundan güncel kimlik; alan yoksa null", () => {
    const durum = { recovery_key_no: 5, recovery_key_date: "2026-10-31" } as GuvenlikDurumu;
    expect(guncelKurtarmaKimligi(durum)).toEqual({ no: 5, tarih: "2026-10-31" });
    expect(guncelKurtarmaKimligi({} as GuvenlikDurumu)).toEqual({ no: null, tarih: null });
  });
});

describe("KurtarmaAnahtariPaneli", () => {
  it("anahtarı numaralı gruplarla ve tek satırda gösterir, üç saklama yolunu sunar", () => {
    bas();
    expect(screen.getByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
    expect(screen.getByText("1. grup")).toBeInTheDocument();
    expect(screen.getByText("8. grup")).toBeInTheDocument();
    expect(screen.getByText(/Deneme Anadolu Lisesi/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yazdır" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "PDF olarak kaydet" })).toBeInTheDocument();
    expect(screen.getByText(/elle yazacaksanız/i)).toBeInTheDocument();
    // Metin dosyası yolu kaldırıldı (PDF aynı işi resmî çıktı biçiminde görür).
    expect(screen.queryByRole("button", { name: /metin dosyası/i })).toBeNull();
  });

  it("anahtarın no'su ve üretim tarihi biliniyorsa anahtarın üstünde (yazdırma alanında) yazar", () => {
    render(
      <SnackbarProvider>
        <KurtarmaAnahtariPaneli
          anahtar={ANAHTAR}
          kimlik={{ no: 2, tarih: "2026-11-01" }}
          onDogrulama={vi.fn()}
        />
      </SnackbarProvider>,
    );
    expect(screen.getByTestId("kurtarma-kimligi")).toHaveTextContent(
      "Anahtar no 2 · üretim tarihi 01.11.2026",
    );
    // Kimlik yazdırılan alandadır: kâğıt hangi no'yu taşıdığını söyler.
    expect(document.getElementById("kurtarma-anahtari-yazdirma-alani")?.textContent).toContain(
      "Anahtar no 2",
    );
  });

  it("yazdırılan kâğıt saklama satırını taşır (zarf, veli, herkes kendi hesabıyla)", () => {
    bas();
    const alan = document.getElementById("kurtarma-anahtari-yazdirma-alani")?.textContent ?? "";
    expect(alan).toContain("Okul müdürlüğünde kapalı zarfta saklanır; veliye geçmez.");
    expect(alan).toContain("herkes programı kendi hesabıyla açar");
  });

  it("kimlik bilinmiyorsa satır gösterilmez", () => {
    bas();
    expect(screen.queryByTestId("kurtarma-kimligi")).toBeNull();
  });

  it("Yazdır pencere yazdırmasını çağırır", async () => {
    const kullanici = userEvent.setup();
    const yazdir = vi.fn();
    vi.stubGlobal("print", yazdir);
    bas();
    await kullanici.click(screen.getByRole("button", { name: "Yazdır" }));
    expect(yazdir).toHaveBeenCalledTimes(1);
    vi.unstubAllGlobals();
  });

  it("PDF olarak kaydet: anahtarı backend'e gönderir ve dosyayı belge adıyla indirir", async () => {
    const kullanici = userEvent.setup();
    const pdf = new Blob(["%PDF-"], { type: "application/pdf" });
    guvenlik.kurtarmaAnahtariPdf.mockResolvedValue(pdf);
    bas();

    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));

    await waitFor(() => expect(guvenlik.kurtarmaAnahtariPdf).toHaveBeenCalledWith(ANAHTAR));
    expect(indirme.saveBlob).toHaveBeenCalledWith(pdf, kurtarmaBelgesiDosyaAdi());
    expect(
      await screen.findByText("Kurtarma anahtarı belgesi PDF olarak kaydedildi."),
    ).toBeInTheDocument();
  });

  it("PDF hatasında backend iletisi görünür", async () => {
    const kullanici = userEvent.setup();
    guvenlik.kurtarmaAnahtariPdf.mockRejectedValue(
      new ApiError(423, "locked", "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın.", {}),
    );
    bas();
    await kullanici.click(screen.getByRole("button", { name: "PDF olarak kaydet" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın.",
    );
    expect(indirme.saveBlob).not.toHaveBeenCalled();
  });

  it("doğrulama kipinde anahtar ekrandan kalkar; iki grup doğru yazılınca sunucuda damgalanır", async () => {
    const kullanici = userEvent.setup();
    const onDogrulama = bas();
    expect(onDogrulama).toHaveBeenLastCalledWith(false);

    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));

    expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
    expect(screen.getByText(/anahtarın 2\. ve 6\. grubunu yazın/)).toBeInTheDocument();
    // Küçük harf ve boşluk serbest (backend normalleştirmesiyle aynı).
    await kullanici.type(screen.getByLabelText("2. grup"), "kurt");
    expect(guvenlik.kurtarmaAnahtariniDogrula).not.toHaveBeenCalled();
    await kullanici.type(screen.getByLabelText("6. grup"), "ab cd");

    expect(await screen.findByRole("status")).toHaveTextContent("Doğrulandı.");
    // Sunucuya bellekteki TAM anahtar gider (kullanıcının yazdığı iki grup değil).
    expect(guvenlik.kurtarmaAnahtariniDogrula).toHaveBeenCalledTimes(1);
    expect(guvenlik.kurtarmaAnahtariniDogrula).toHaveBeenCalledWith(ANAHTAR);
    expect(onDogrulama).toHaveBeenLastCalledWith(true);
  });

  it("sunucu damgayı yazamazsa doğrulanmaz; ileti ve yeniden deneme çıkar", async () => {
    const kullanici = userEvent.setup();
    guvenlik.kurtarmaAnahtariniDogrula.mockRejectedValueOnce(
      new ApiError(423, "locked", "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın.", {}),
    );
    const onDogrulama = bas();
    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
    await kullanici.type(screen.getByLabelText("2. grup"), "KURT");
    await kullanici.type(screen.getByLabelText("6. grup"), "ABCD");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın.",
    );
    expect(screen.queryByRole("status")).toBeNull();
    expect(onDogrulama).not.toHaveBeenCalledWith(true);

    await kullanici.click(screen.getByRole("button", { name: "Yeniden dene" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Doğrulandı.");
    expect(onDogrulama).toHaveBeenLastCalledWith(true);
  });

  it("yanlış grup doğrulanmaz, sunucuya gidilmez ve alan hatası gösterir", async () => {
    const kullanici = userEvent.setup();
    const onDogrulama = bas();
    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));

    await kullanici.type(screen.getByLabelText("2. grup"), "KURT");
    await kullanici.type(screen.getByLabelText("6. grup"), "ABCE");

    expect(screen.getByText("Bu grup anahtarla eşleşmiyor.")).toBeInTheDocument();
    expect(screen.queryByRole("status")).toBeNull();
    expect(guvenlik.kurtarmaAnahtariniDogrula).not.toHaveBeenCalled();
    expect(onDogrulama).not.toHaveBeenCalledWith(true);
  });

  it("grup sonradan bozulursa doğrulama düşer", async () => {
    const kullanici = userEvent.setup();
    const onDogrulama = bas();
    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
    await kullanici.type(screen.getByLabelText("2. grup"), "KURT");
    await kullanici.type(screen.getByLabelText("6. grup"), "ABCD");
    await waitFor(() => expect(onDogrulama).toHaveBeenLastCalledWith(true));

    await kullanici.type(screen.getByLabelText("6. grup"), "X");

    expect(onDogrulama).toHaveBeenLastCalledWith(false);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("gözetimsiz ekranda (5 dk) anahtar gizlenir, “Anahtarı göster” geri getirir", () => {
    // Tasarım §13 D15: kurulum bitene kadar kip süreyle düşmez; anahtar ekranda süresiz durmasın.
    // Sahte zamanlayıcı kullanıldığı için tıklama `fireEvent` ile yapılır (userEvent'in
    // kendi gecikme zamanlayıcısı sahte saatle kilitleniyor).
    etkinlikSaatleriniSifirla();
    vi.useFakeTimers();
    try {
      bas();
      expect(screen.getByTestId("kurtarma-anahtari")).toBeInTheDocument();

      act(() => vi.advanceTimersByTime(BOSTA_GIZLEME_MS));

      expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
      // Gruplar da (yazdırma alanının tamamı) DOM'dan kalkar.
      expect(screen.queryByLabelText("Kurtarma anahtarının grupları")).toBeNull();
      expect(screen.getByText(/Anahtar güvenlik için gizlendi/)).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Anahtarı göster" }));
      expect(screen.getByTestId("kurtarma-anahtari")).toHaveTextContent(ANAHTAR);
      expect(screen.getByRole("button", { name: "PDF olarak kaydet" })).toBeInTheDocument();

      // Sayaç sıfırlandı: dört dakika yetmez, beş dakika yeniden gizler.
      act(() => vi.advanceTimersByTime(4 * 60_000));
      expect(screen.getByTestId("kurtarma-anahtari")).toBeInTheDocument();
      act(() => vi.advanceTimersByTime(BOSTA_GIZLEME_MS));
      expect(screen.queryByTestId("kurtarma-anahtari")).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("etkileşim sürdükçe anahtar gizlenmez", () => {
    etkinlikSaatleriniSifirla();
    vi.useFakeTimers();
    try {
      bas();
      act(() => vi.advanceTimersByTime(4 * 60_000));
      // Etkileşim saati lib/api.ts'in küresel dinleyicisinde tutulur (panelin kendi
      // dinleyicisi yok): tuşa basmak sayacı tazeler.
      act(() => {
        window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
      });
      act(() => vi.advanceTimersByTime(4 * 60_000));

      expect(screen.getByTestId("kurtarma-anahtari")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("anahtar yeniden gösterilince doğrulama düşer", async () => {
    const kullanici = userEvent.setup();
    const onDogrulama = bas();
    await kullanici.click(screen.getByRole("button", { name: "Sakladım, doğrula" }));
    await kullanici.type(screen.getByLabelText("2. grup"), "KURT");
    await kullanici.type(screen.getByLabelText("6. grup"), "ABCD");
    await waitFor(() => expect(onDogrulama).toHaveBeenLastCalledWith(true));

    await kullanici.click(screen.getByRole("button", { name: "Anahtarı yeniden göster" }));

    expect(screen.getByTestId("kurtarma-anahtari")).toBeInTheDocument();
    expect(onDogrulama).toHaveBeenLastCalledWith(false);
  });
});
