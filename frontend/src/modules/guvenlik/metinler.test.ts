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

  it("dürüst sınır: her iş denetim izine yazılır (istisnasız); iz değişikliği gösterir, önlemez", () => {
    const sinir = (baslik: string) =>
      metinler.DURUST_SINIRLAR.find((s) => s.baslik === baslik)?.metin ?? "";
    // F1b alt commit c'den beri doğru: yazmalar oturumdaki hesabın adına denetim izinde.
    const oturum = sinir("Açık oturum, sahibinin imzasıdır.");
    expect(oturum).toMatch(/her iş o hesabın adına denetim izine yazılır/);
    // F1b 5. adım: personel silme ve birleştirme de izlidir; "tek istisna" cümlesi kalktı.
    expect(oturum).not.toMatch(/istisna/);
    // Geri yükleme ilk girişte, başlatan hesapla birlikte yazılır (kurtarma yolunda da).
    expect(oturum).toMatch(
      /Yedekten geri yükleme, ardından yapılan ilk girişte, onu başlatan\s+hesapla/,
    );
    // Tasarım §4.6.3 "Kalan risk": eski kopya + kilit işareti fark edilmez; son katman kâğıt.
    const iz = sinir("Denetim izi değişikliği gösterir, önlemez.");
    expect(iz).toMatch(/eski bir kopyayla değiştirilirse\s+fark etmez/);
    expect(iz).toMatch(/baştan\s+hesaplayabilir/);
    expect(iz).toContain("“Kayıt no · Zincir” satırını");
    expect(iz).toContain("Son Girişler kartında");
    // Teknik terimler bu kartta yok (sözlük §1 "Denetim izi").
    expect(`${oturum} ${iz}`).not.toMatch(/çapa|tohum|sarmal|mühür|HMAC/i);
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
    expect(metinler.KURTARMA_UYARISI).toContain("Kayıtlara üç durumda bu anahtarla erişilir");
    expect(metinler.KURTARMA_UYARISI).toContain("program yöneticisi parolasını unutursa");
    expect(metinler.KURTARMA_UYARISI).toContain("kayıtlar yeni bir bilgisayara taşınırken");
    // Zarfın üçüncü durumu ve çaresi kullanıcı kararlarının sözleriyle, BİREBİR (02.11.2026,
    // 03.11.2026; belge ve sözlükle eşitliğini backend `test_kurtarma_anahtari_pdf` sınar).
    expect(metinler.KURTARMA_UYARISI).toContain(metinler.ZARFIN_UCUNCU_DURUMU);
    expect(metinler.KURTARMA_UYARISI).toContain(metinler.UCUNCU_DURUMUN_CARESI);
    // Eski, dar söz kalmadı.
    expect(metinler.KURTARMA_UYARISI).not.toMatch(/kaybolur veya bozulursa/);
  });

  it("zarfın üçüncü durumu ve çaresi kullanıcı kararlarının sözleridir", () => {
    expect(metinler.ZARFIN_UCUNCU_DURUMU).toBe(
      "bu bilgisayarın güvenlik dosyası ya da kayıtları kaybolduğunda, bozulduğunda ya da " +
        "program dışından değiştirildiğinde",
    );
    expect(metinler.UCUNCU_DURUMUN_CARESI).toBe(
      "yedekten geri yükleme ya da kurtarma anahtarıyla açılış",
    );
  });

  it("eski yedek metni: yedek anahtarın no'sunu taşır, başka bilgisayarda yalnız eski anahtar açar", () => {
    expect(metinler.ESKI_YEDEK_METNI).toContain("kurtarma anahtarının no'sunu taşır");
    expect(metinler.ESKI_YEDEK_METNI).toMatch(/başka bir bilgisayarda .* yalnız eski kurtarma/);
    // Yedek başlığı hesap sarmalı taşımaz (tasarım TK10): "o dönemin parolası" denmez.
    expect(metinler.ESKI_YEDEK_METNI).not.toMatch(/dönemin .*parolası/);
  });
});
