// Kural paketiyle denetlenen yazmaların hata gövdelerini okur (backend `apps/oab/hatalar.py`,
// `apps/oab/kurallar/hatalar.py`; sözleşme `{code, message, fields}`). Dört tür ayrılır:
//
// * `gerekce` — 400 `gerekce_gerekli`: uyarı gerektiren kayıt gerekçesiz geçmez (altın kural 3). İleti
//   "Bu kayıt için gerekçe yazılmalıdır. <uyarı metni> (md. 12/4)." biçimindedir: ekran uyarıyı ve
//   atfı ayırıp gerekçe kutusunu açar; çağıran aynı isteği `gerekce` ile yeniden gönderir.
// * `sert` — 400 `kural_sert` ya da sonu madde atfıyla biten başka 400: sert engel (CLAUDE.md'de sayılan
//   hâller); gerekçe sorulmaz, kayıt yapılmaz.
// * `paket` — 503 `kural_paketi_yok` ya da `donem_kopyasi_dogrulanamadi` (tasarım §6.3 D1, D7): kural
//   kullanan yazma kapalıdır; okuma açık kalır.
// * `donem` — 409 `donem_kapali`, `donem_salt_okur`, `donem_yazilamaz`, `gecis_kapali`: dönemin ya da
//   geçiş kurulumunun kilidi (O2, D7, §7.9).
//
// Öteki hatalar uyum hatası değildir (`null`): çağıran kendi hata bandını (`ui/ErrorBand`) gösterir.

import { ApiError } from "../../lib/api";

export type UyumTuru = "EKSIK" | "SAPMA" | "TAKVIM";

export type UyumHatasiTuru = "gerekce" | "sert" | "paket" | "donem";

export interface UyumHatasi {
  tur: UyumHatasiTuru;
  /** Gösterilecek metin (atıf ayrıldıysa atıfsız gövde). */
  metin: string;
  /** Madde atfı ("md. 12/4"); yoksa null. */
  atif: string | null;
}

/** Gerekçe isteyen 400'ün ileti öneki (backend `GerekceGerekli`). */
const GEREKCE_ONEKI = "Bu kayıt için gerekçe yazılmalıdır.";

const PAKET_KODLARI = new Set(["kural_paketi_yok", "donem_kopyasi_dogrulanamadi"]);
const DONEM_KODLARI = new Set([
  "donem_kapali",
  "donem_salt_okur",
  "donem_yazilamaz",
  "gecis_kapali",
]);

// Sondaki parantez (bir iç parantez düzeyiyle: "kullanıcı kararı A-2 (gerekçe md. 14/4)").
const SON_PARANTEZ = /\s*\(((?:[^()]|\([^()]*\))+)\)\.?\s*$/;

/** Parantezin içeriği bir madde atfı mı? ("md. 12/4", "EK-2 md. 7", "kullanıcı kararı …") */
function atifMi(icerik: string): boolean {
  return /\bmd\.\s/.test(icerik) || icerik.startsWith("kullanıcı kararı");
}

/** İletinin sonundaki madde atfını ayırır: "… sınır (md. 12/4)." → ["… sınır.", "md. 12/4"]. */
export function atifAyir(ileti: string): { govde: string; atif: string | null } {
  const eslesme = SON_PARANTEZ.exec(ileti);
  if (eslesme === null || !atifMi(eslesme[1])) return { govde: ileti.trim(), atif: null };
  const govde = ileti.slice(0, eslesme.index).trim();
  return { govde: govde.endsWith(".") ? govde : `${govde}.`, atif: eslesme[1].trim() };
}

/** Hata bir uyum hatası mı? Değilse null (dosya başı). */
export function uyumHatasiOku(e: unknown): UyumHatasi | null {
  if (!(e instanceof ApiError)) return null;
  if (e.status === 400 && e.code === "gerekce_gerekli") {
    const uyari = e.message.startsWith(GEREKCE_ONEKI)
      ? e.message.slice(GEREKCE_ONEKI.length).trim()
      : e.message;
    const { govde, atif } = atifAyir(uyari);
    return { tur: "gerekce", metin: govde || e.message, atif };
  }
  if (e.status === 400) {
    const { govde, atif } = atifAyir(e.message);
    if (e.code === "kural_sert" || atif !== null) return { tur: "sert", metin: govde, atif };
    return null;
  }
  if (e.status === 503 && PAKET_KODLARI.has(e.code)) {
    return { tur: "paket", metin: e.message, atif: null };
  }
  if (e.status === 409 && DONEM_KODLARI.has(e.code)) {
    return { tur: "donem", metin: e.message, atif: null };
  }
  return null;
}
