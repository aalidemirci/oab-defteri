// "Güncelleme denetlendi" olayı — Ayarlar → Güncelleme'deki elle denetimin
// sonucunu kabuktaki banda taşır. Program açılışta denetim YAPMAZ (tasarım
// TK4; MEB ağında dış istekler engelli olabilir). Program ağ servisi sunmaz:
// yönetim sunucusu yalnız 127.0.0.1'de, rastgele portta ve oturum belirteciyle
// dinler; hiçbir port okul ağına açılmaz. Dış istek yalnız kullanıcının başlattığı
// güncelleme denetiminden çıkar — "Şimdi denetle" düğmesi (tasarım §4.1). Bant
// kendi başına istek atmaz, yalnız bu olayı dinler. Desen `lib/restart.ts` ile aynıdır.

import type { UpdateStatus } from "./api";

export const DENETIM_OLAYI = "od:guncelleme-denetlendi";

export function denetimSonucunuYayinla(status: UpdateStatus): void {
  window.dispatchEvent(new CustomEvent<UpdateStatus>(DENETIM_OLAYI, { detail: status }));
}
