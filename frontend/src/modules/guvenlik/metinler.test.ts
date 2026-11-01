// Güvenlik metinlerinin içerik kuralları (`metinler.ts` tek kaynaktır): parola
// paylaşımı öğütlenmez (MEB Bilgi ve Sistem Güvenliği Yönergesi md. 7/2, programa
// kıyasen — tasarım TK9; kullanıcı kararı T1), parolayı bilen ayrılır ya da unutursa
// yol kurtarma anahtarıdır ve anahtar okul müdürlüğünde kapalı zarfta durur (kullanıcı
// kararı D3); aile iskeletinin kütüphane terimleri metinlerde kalmaz.

import { describe, expect, it } from "vitest";

import * as metinler from "./metinler";

describe("güvenlik metinleri", () => {
  it("kurma uyarısı parolanın paylaşılmamasını ve kurtarma anahtarı yolunu söyler", () => {
    expect(metinler.KURMA_UYARISI).toContain("Parolayı kimseyle paylaşmayın");
    expect(metinler.KURMA_UYARISI).toMatch(/ayrılırsa ya da parolayı unutursa/);
    expect(metinler.KURMA_UYARISI).toMatch(/kurtarma\s+anahtarıyla açılır/);
    expect(metinler.KURMA_UYARISI).toContain("okul müdürlüğünde kapalı zarfta");
    // Aile iskeletinin "parolayı en az iki kişi bilsin" öğüdü kalmadı.
    expect(metinler.KURMA_UYARISI).not.toMatch(/en az iki|bilsin|paylaşın/i);
  });

  it("hiçbir metin parola paylaşımını öğütlemez ya da kütüphane terimi taşımaz", () => {
    const hepsi = Object.values(metinler)
      .map((metin) => (typeof metin === "function" ? metin(1, 2) : metin))
      .join("\n");
    expect(hepsi).not.toMatch(/kütüphane/i);
    expect(hepsi).not.toMatch(/görevlendirilmiş kişi/i);
    expect(hepsi).not.toMatch(/en az iki|parolayı .*bilsin/i);
  });
});
