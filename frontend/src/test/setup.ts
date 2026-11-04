// Vitest global setup (Tur 43, Tur 46).
// `@testing-library/jest-dom` ek matcher'ları (toBeInTheDocument vb.) Vitest'e
// kayıt eder. tsconfig.json `types` listesinde de tanımlı.

import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

import { kilitDurumunuSifirla, pencereIcerigi } from "../lib/kilit";
import { bekleyenKurtarmaAnahtariniYaz } from "../modules/guvenlik/bekleyenAnahtar";

// Tur 46: jsdom `window.matchMedia` sağlamıyor; ThemeSwitcher/`useTheme` sistem
// tema sorgusu için ona ihtiyaç duyar. Varsayılan açık tema yanıtı ile mock.
if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

// Pencerenin yeniden yüklenmesi (tasarım §13 D53; `lib/kilit.ts`) jsdom'da uygulanmaz:
// tek çağrı noktası her testte TAZE bir taklitle değiştirilir (casus değil: dosyaların
// `restoreAllMocks`'u gerçek yüklemeyi geri getirmesin). Kilit ve açılış akışlarını
// sınayan testler `pencereIcerigi.yenidenYukle` taklidinin çağrılarına bakar.
beforeEach(() => {
  pencereIcerigi.yenidenYukle = vi.fn<() => void>();
});

// Her testten sonra render edilen DOM'u temizle (yan etki sızıntısını önler).
afterEach(() => {
  cleanup();
  // Modül belleğindeki bekleyen kurtarma anahtarı testten teste taşınmasın.
  bekleyenKurtarmaAnahtariniYaz(null);
  // "Açık sanma" bayrağı ve "yükleme istendi" işareti testten teste taşınmasın.
  kilitDurumunuSifirla();
});
