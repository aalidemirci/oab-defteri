// Oturum ve kilit hatalarının TEK eşlemi: backend ret kodu → arayüz davranışı ve
// sözlüğe uyan metin (plan F1b-1 "Parola ve hatalı deneme"; tasarım §2.3.1; sözlük §2).
//
// Kodlar (`parola_yanlis`, `hesap_askida`…) kullanıcı metnine ÇIKMAZ: ekrana yalnız
// `oturumHatasi(...).metin` yazılır. Ekranlar davranışı (zorunlu parola değişimine geçiş,
// hesap listesinin tazelenmesi) `kod`a bakarak seçer; metni kodla kendileri kurmaz.
//
// Metnin kaynağı: backend iletileri Türkçedir, sözlüğe uyar ve kodun alt durumunu daha
// kesin söyler. SUNUCUNUN İLETİSİ HER ZAMAN ÖNCELİKLİDİR; buradaki metin yalnız ileti boşsa ya
// da kod biçiminde geldiyse (savunma derinliği) yazılır, bilinmeyen kodda çağıranın varsayılanı.
// Bu yüzden yedek metinler nedeni seçmez, kodun bütün nedenlerine ve iki bağlama (kilit ekranı;
// açık oturumdaki parola doğrulaması ve hesap işlemleri) uyar:
//
// * `hesap_muhru_tutmadi` (409; `app_password.AccountSealMismatch` ve alt sınıfları) — dört
//   neden: hesap kaydının mührü tutmadı (`seal`); satırın izi tutmadı, yani satır eski bir
//   kopyadan geri konmuş (`kayit_mac`, `AccountRecordStale`); hesabın son kaydından sonra denetim
//   izinde boşluk var (`iz_boslugu`, `AuditTrailGap`; iletisi değişen denetim izini anar);
//   parola kaydının özeti hesap kaydınınkini tutmadı (`wrap_digest`, `WrapDigestMismatch`;
//   iletisi bağsız kaydınkiyle aynıdır, çıkışı — "Parolamı unuttum", program yöneticisinin
//   sıfırlaması — söyler). Açık oturumda ve hesap işlemlerinde üç iletinin "kayda dokunulmadı" /
//   "işlem yapılmadı" karşılıkları gelir (`ISLEMDE_*`).
// * `iki_depo_tutarsiz` (409; `TwoStoreMismatch` ve alt sınıfları) — beş neden: parola kaydı bu
//   bilgisayarın güvenlik dosyasında yok; hesap kaydı yok ya da açık değil; güvenlik dosyası
//   başka bir veritabanının; iz anahtarı okunamadı (`AuditKeyUnreadable`); parola kaydı kimliğe
//   bağlı biçimde değil, yani bağsız kayıt (`UnboundWrap`; iletisi program dışı değişikliği anar
//   ve bildirim ister; açık oturumda "işlem yapılmadı" karşılığı).
// * `hesap_askida` onuncu hatalı denemede askıya alındığını da söyler.

import { ApiError, BEKLENMEYEN_HATA_ILETISI } from "../../lib/api";

/** Oturum uçlarının ret kodları (`views_oturum.py`, `lock_middleware`, `rol_middleware`, `shared.exceptions`). */
export const OTURUM_HATA_METINLERI = {
  parola_yanlis: "Parola hatalı.",
  hesap_askida: "Hesap askıda — program yöneticisine başvurun.",
  // Dört nedene ve iki bağlama uyan yedek (dosya başı): nedeni seçmez, "giriş açılmadı" demez.
  hesap_muhru_tutmadi:
    "Hesap kaydı, parola kaydı ya da denetim izi program dışından değiştirilmiş görünüyor; " +
    "işlem yapılmadı ve kayda dokunulmadı. Denetleme Kuruluna bildirin.",
  // Beş nedene ve iki bağlama uyan yedek (dosya başı).
  iki_depo_tutarsiz:
    "Hesap kaydı bu bilgisayarın güvenlik dosyasıyla uyuşmuyor; işlem yapılmadı. Program " +
    "yöneticisine ve Denetleme Kuruluna bildirin.",
  parola_yenilenmeli:
    "Parolanızı yenilemeniz gerekiyor (geçici parola ya da süresi dolan parola). Yeni " +
    "parolanızı belirleyin.",
  locked:
    "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın (parolanızı unuttuysanız program " +
    "yöneticisine başvurun).",
  guvenlik_dosyasi_kayip:
    "Güvenlik dosyası (guvenlik.json) bulunamadı ya da okunamıyor. Kayıtlar açılamaz.",
  parola_gerekli: "Önce program yöneticisi hesabını kurun.",
  // Rol reddi (403; `shared/exceptions.ROL_YETKISIZ_MESAJI` ile birebir; sözlük §1 "Program
  // yöneticisi ve roller"). Olayı `lib/api` yayınlar; metni çağıran ekran yazar.
  rol_yetkisiz: "Bu işlem hesabınızın rolüne açık değil.",
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
 * Kayıt reddi mi? Hesap kaydı, parola kaydı ya da denetim izi program dışından değiştirilmiş
 * görünüyor (`hesap_muhru_tutmadi`) ya da hesap kaydı bu bilgisayarın güvenlik dosyasıyla
 * uyuşmuyor (`iki_depo_tutarsiz`). Kilit ekranında (yalnız program yöneticisi hesabında) ve
 * kurtarma yolunda (yalnız program yöneticisinindir) bu retten sonra zarfın üçüncü durumunun yol
 * metni iletinin altında durur (kullanıcı kararı 04.11.2026).
 */
export function kayitReddiMi(kod: OturumHataKodu | null): boolean {
  return kod === "hesap_muhru_tutmadi" || kod === "iki_depo_tutarsiz";
}

/**
 * Sunucunun alan doğrulaması reddi mi (400 `validation_error`)? Parola uçlarında bu ret
 * gönderilen YENİ parolanındır (politika, eskisiyle aynılık): ekran iletiyi "Yeni parola"
 * alanına bağlar (hata hangi alanınsa orada; `parola_yanlis` ise mevcut parolanındır).
 */
export function dogrulamaReddiMi(err: unknown): boolean {
  return err instanceof ApiError && err.code === "validation_error";
}
