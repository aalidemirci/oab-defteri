// Oturum ve kilit hatalarının TEK eşlemi: backend ret kodu → arayüz davranışı ve
// sözlüğe uyan metin (plan F1b-1 "Parola ve hatalı deneme"; tasarım §2.3.1; sözlük §2).
//
// Kodlar (`parola_yanlis`, `hesap_askida`…) kullanıcı metnine ÇIKMAZ: ekrana yalnız
// `oturumHatasi(...).metin` yazılır. Ekranlar davranışı (zorunlu parola değişimine geçiş,
// hesap listesinin tazelenmesi) `kod`a bakarak seçer; metni kodla kendileri kurmaz.
//
// Metnin kaynağı: backend iletileri Türkçedir, sözlüğe uyar ve kodun alt durumunu daha
// kesin söyler (ör. `iki_depo_tutarsiz`'in dört nedeni: sarmal yok, satır yok, başka
// veritabanı, iz anahtarı okunamadı; onuncu hatalı denemede askıya alındığını söyleyen
// `hesap_askida`). Bu yüzden ileti doluysa o, boşsa ya da kod biçiminde geldiyse
// (savunma derinliği) buradaki metin yazılır. Bilinmeyen kodda çağıranın varsayılanı.

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";

/** Oturum uçlarının ret kodları (`views_oturum.py`, `lock_middleware`, `shared.exceptions`). */
export const OTURUM_HATA_METINLERI = {
  parola_yanlis: "Parola hatalı.",
  hesap_askida: "Hesap askıda — program yöneticisine başvurun.",
  hesap_muhru_tutmadi:
    "Hesap kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. Program " +
    "yöneticisine ve Denetleme Kuruluna bildirin.",
  iki_depo_tutarsiz:
    "Hesap kaydı bu bilgisayarın güvenlik dosyasıyla uyuşmuyor; giriş açılmadı. Program " +
    "yöneticisine başvurun.",
  parola_yenilenmeli:
    "Parolanızı yenilemeniz gerekiyor (geçici parola ya da süresi dolan parola). Yeni " +
    "parolanızı belirleyin.",
  locked:
    "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız program " +
    "yöneticisine başvurun).",
  guvenlik_dosyasi_kayip:
    "Güvenlik dosyası (guvenlik.json) bulunamadı ya da okunamıyor. Kayıtlar açılamaz.",
  parola_gerekli: "Önce program yöneticisi hesabını kurun.",
} as const;

export type OturumHataKodu = keyof typeof OTURUM_HATA_METINLERI;

export interface OturumHatasi {
  /** Tanınan ret kodu (davranış seçimi için); tanınmıyorsa null. */
  kod: OturumHataKodu | null;
  /** Ekrana yazılacak metin — kod içermez. */
  metin: string;
}

/** İletinin kendisi bir kod gibi mi görünüyor? (`parola_yanlis`, `400`) — ekrana yazılmaz. */
const KOD_BICIMI = /^[a-z0-9]+(?:_[a-z0-9]+)*$/;

function tanidikKod(kod: string): kod is OturumHataKodu {
  return Object.prototype.hasOwnProperty.call(OTURUM_HATA_METINLERI, kod);
}

/** Herhangi bir hatayı ekrana yazılabilir oturum hatasına çevirir (dosya başı notu). */
export function oturumHatasi(err: unknown, varsayilan: string): OturumHatasi {
  if (!(err instanceof ApiError)) {
    return { kod: null, metin: varsayilan };
  }
  const kod = tanidikKod(err.code) ? err.code : null;
  const ileti = err.message.trim();
  // Gövdesiz yanıtın genel iletisi ("Beklenmeyen bir hata oluştu.") de anlamsız sayılır:
  // tanınan kodda eşlemin metni, tanınmayanda çağıranın varsayılanı daha çok şey söyler.
  const anlamli = ileti !== "" && ileti !== BEKLENMEYEN_HATA_ILETISI && !KOD_BICIMI.test(ileti);
  if (anlamli) return { kod, metin: ileti };
  return { kod, metin: kod ? OTURUM_HATA_METINLERI[kod] : varsayilan };
}

/** Kısayol: yalnız metin. */
export function oturumHataMetni(err: unknown, varsayilan: string): string {
  return oturumHatasi(err, varsayilan).metin;
}

/**
 * Sunucunun alan doğrulaması reddi mi (400 `validation_error`)? Parola uçlarında bu ret
 * gönderilen YENİ parolanındır (politika, eskisiyle aynılık): ekran iletiyi "Yeni parola"
 * alanına bağlar (hata hangi alanınsa orada; `parola_yanlis` ise mevcut parolanındır).
 */
export function dogrulamaReddiMi(err: unknown): boolean {
  return err instanceof ApiError && err.code === "validation_error";
}
