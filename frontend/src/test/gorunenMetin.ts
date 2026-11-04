// Testlerin ortak yardımcısı: bir öğenin kullanıcıya görünen metni. Material Symbols simgeleri
// ligatürdür — DOM'da simgenin adı metin olarak durur ("sync_problem", "task_alt") ama
// `aria-hidden` taşır ve ekranda harf olarak görünmez. "İç kod yüzeye çıkmaz" (sözlük §2)
// denetimleri simge adlarını kod sanmasın diye gizli öğeler çıkarılarak okunur.

/** Öğenin `aria-hidden="true"` alt öğeleri çıkarılmış metni. */
export function gorunenMetin(oge: Element): string {
  const kopya = oge.cloneNode(true) as Element;
  kopya.querySelectorAll('[aria-hidden="true"]').forEach((gizli) => gizli.remove());
  return kopya.textContent ?? "";
}
