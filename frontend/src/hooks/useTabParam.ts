import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Sekme seçimini URL query parametresinde tutar.
 *
 * Amaç derin-link: "/ayarlar?tab=guvenlik" gibi bir bağlantı ekranı doğrudan o
 * sekmede açar ve sayfa yenilendiğinde seçim korunur.
 *
 * - Geçersiz/eksik değer sessizce `fallback`'e düşer (kırık bağlantı hata üretmez).
 * - Varsayılan sekmede parametre URL'den SİLİNİR — adres çubuğu gereksiz
 *   şişmez, "/ayarlar" ile "/ayarlar?tab=ders-yillari" aynı ekranı gösterir.
 * - Geçiş `replace` ile yazılır: sekme gezinmesi tarayıcı geçmişini doldurmaz,
 *   geri tuşu kullanıcıyı bir önceki SAYFAYA götürür.
 */
export function useTabParam<T extends string>(
  paramName: string,
  allowed: readonly T[],
  fallback: T,
): [T, (next: T) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  const raw = searchParams.get(paramName);
  const active = allowed.includes(raw as T) ? (raw as T) : fallback;

  const setActive = useCallback(
    (next: T) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          if (next === fallback) {
            params.delete(paramName);
          } else {
            params.set(paramName, next);
          }
          return params;
        },
        { replace: true },
      );
    },
    [fallback, paramName, setSearchParams],
  );

  return [active, setActive];
}
