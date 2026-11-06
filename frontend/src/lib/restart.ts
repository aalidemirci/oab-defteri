// "Yeniden başlat gerekli" olayı — backend `restart_gate`'in arayüz ayağı.
// Yedekten geri yükleme uygulandıktan sonra backend TÜM API isteklerini
// 503 `restart_required` ile keser; `lib/api.ts` bu kodu görünce olayı
// yayınlar (sayfa yenilense bile ilk API çağrısında ekran geri gelir),
// geri yükleme akışı da başarıda olayı doğrudan yayınlar. Dinleyen tek yer
// `modules/guvenlik/YenidenBaslatEkrani`dir. Geri yükleme akışı olayla birlikte dosya raporunu
// verir (`detail`), ekran kişisiz sayıları ondan yazar. `lib/api.ts`in yayını rapor taşımaz: sayfa
// yenilenince ekran raporsuz gelir, daha önce gelmiş raporu da silmez.

export const YENIDEN_BASLAT_OLAYI = "od:yeniden-baslat-gerekli";

export function yenidenBaslatGerekliYayinla(ayrinti?: unknown): void {
  window.dispatchEvent(new CustomEvent(YENIDEN_BASLAT_OLAYI, { detail: ayrinti }));
}
