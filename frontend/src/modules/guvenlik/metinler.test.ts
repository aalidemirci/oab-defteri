// Güvenlik metinlerinin içerik kuralları (`metinler.ts` tek kaynaktır): parola
// paylaşımı öğütlenmez (MEB Bilgi ve Sistem Güvenliği Yönergesi md. 7/2, programa
// kıyasen — tasarım TK9; kullanıcı kararı T1), herkes programı kendi hesabıyla açar
// (tasarım TK14; tek bir "yönetici parolası" ve görevli kipi yoktur), program
// yöneticisi parolasını unutursa yol kurtarma anahtarıdır ve anahtar okul müdürlüğünde
// kapalı zarfta durur (kullanıcı kararı D3); dürüst sınırlar (tasarım §4.4.6) iç kod
// taşımaz; aile iskeletinin kütüphane terimleri metinlerde kalmaz.

import { describe, expect, it } from "vitest";

import * as metinler from "./metinler";

/** Bütün metinler tek dizide (işlevler örnek değerle, dürüst sınırlar başlık + metin). */
function hepsi(): string {
  return Object.values(metinler)
    .map((metin) => {
      if (typeof metin === "function") return metin(1, 2);
      if (Array.isArray(metin)) return metin.map((m) => `${m.baslik} ${m.metin}`).join("\n");
      return metin;
    })
    .join("\n");
}

describe("güvenlik metinleri", () => {
  it("kurma uyarısı parolanın paylaşılmamasını, kendi hesabını ve kurtarma anahtarı yolunu söyler", () => {
    expect(metinler.KURMA_UYARISI).toContain("Parolayı kimseyle paylaşmayın");
    expect(metinler.KURMA_UYARISI).toContain("herkes programı kendi hesabıyla");
    expect(metinler.KURMA_UYARISI).toMatch(/Program yöneticisi parolasını unutursa/);
    expect(metinler.KURMA_UYARISI).toMatch(/kurtarma\s+anahtarıyla açılır/);
    expect(metinler.KURMA_UYARISI).toContain("okul müdürlüğünde kapalı zarfta");
    // Aile iskeletinin "parolayı en az iki kişi bilsin" öğüdü kalmadı.
    expect(metinler.KURMA_UYARISI).not.toMatch(/en az iki|bilsin|paylaşın/i);
  });

  it("hiçbir metin parola paylaşımını öğütlemez, tek yönetici parolası ya da kütüphane terimi taşımaz", () => {
    const metin = hepsi();
    expect(metin).not.toMatch(/kütüphane/i);
    expect(metin).not.toMatch(/görevlendirilmiş kişi/i);
    expect(metin).not.toMatch(/en az iki|parolayı .*bilsin/i);
    // Görevli kipi kalktı (tasarım TK14): herkes programı kendi hesabıyla açar.
    expect(metin).not.toMatch(/görevli kipi|yönetici kipi/i);
    // Tek bir "yönetici parolası" yoktur; parola anlamında "şifre" kullanılmaz (sözlük §1).
    expect(metin).not.toMatch(/yönetici parolası/i);
    expect(metin).not.toMatch(/şifren(iz|i)\b|şifre ile|şifreyle/i);
    expect(metinler.KAPSAM_METNI).toContain("her hesabın kendi parolasıyla");
  });

  it("dürüst sınır: şifreli alanlar en zayıf hesap parolası kadar korunur", () => {
    expect(metinler.EN_ZAYIF_PAROLA_METNI).toMatch(/en zayıf hesap parolası kadar korunur/);
    const sinirlar = metinler.DURUST_SINIRLAR.map((s) => s.baslik);
    expect(sinirlar).toContain("Şifreli alanlar en zayıf hesap parolası kadar korunur.");
    expect(sinirlar).toContain("Rol bir şifreleme önlemi değildir.");
    expect(sinirlar).toContain("Açık oturum, sahibinin imzasıdır.");
  });

  it("dürüst sınırlar iç kod taşımaz, yalnız bugün olanı söyler", () => {
    const metin = metinler.DURUST_SINIRLAR.map((s) => `${s.baslik} ${s.metin}`).join("\n");
    // Sözlük §2: karar, faz, denetim kodları yüzeye çıkmaz.
    expect(metin).not.toMatch(/\b(TK\d+|D\d+|F\d|GA-|UY-|DEK)\b/);
    // Sonraki fazların işleri (zarf imhası, ihlal dökümü) vaat edilmez.
    expect(metin).not.toMatch(/imha|ihlal dökümü/i);
    // Kayıp ya da çalınmada bildirim yükümlülüğü mevzuat atfıyla (KVKK md. 12/5).
    expect(metin).toContain("KVKK md. 12/5");
    expect(metin).toContain("Ctrl+Shift+L");
  });

  it("kurtarma uyarısı anahtarın üç kullanımını sayar (belgedekiyle aynı)", () => {
    expect(metinler.KURTARMA_UYARISI).toMatch(/Program yöneticisi parolasını unutursa/);
    expect(metinler.KURTARMA_UYARISI).toMatch(/yeni bir bilgisayara taşınırsa/);
    expect(metinler.KURTARMA_UYARISI).toMatch(/güvenlik dosyası kaybolur veya bozulursa/);
  });

  it("eski yedek metni: yedek anahtarın no'sunu taşır, başka bilgisayarda yalnız eski anahtar açar", () => {
    expect(metinler.ESKI_YEDEK_METNI).toContain("kurtarma anahtarının no'sunu taşır");
    expect(metinler.ESKI_YEDEK_METNI).toMatch(/başka bir bilgisayarda .* yalnız eski kurtarma/);
    // Yedek başlığı hesap sarmalı taşımaz (tasarım TK10): "o dönemin parolası" denmez.
    expect(metinler.ESKI_YEDEK_METNI).not.toMatch(/dönemin .*parolası/);
  });
});
