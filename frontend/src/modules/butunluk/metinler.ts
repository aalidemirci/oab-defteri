// Denetim izi kartlarının ve parola yenilenme bildiriminin metinleri — tek kaynak (docs/
// sozluk.md §1 "Denetim izi", §4.5; tasarım §4.6.3, §4.4.3).
//
// İÇ KOD YÜZEYE ÇIKMAZ (sözlük §2): backend bulguyu kodla verir (`kuyruk_kesik`,
// `capa_yok`…), burada sade Türkçe cümleye çevrilir; tanınmayan kod da kodu değil genel bir
// cümleyi yazar. "Çapa", "tohum", "mühür", "sarmal", "kip" kullanıcı metnine girmez: çapanın
// kullanıcıdaki adı **kilit işareti**dir (program her kilitlenmede denetim izinin son kaydını
// bir dosyaya işaretler), kâğıda inen satır "Kayıt no: N · Zincir: XXXX-XXXX"dir.
//
// KİŞİSİZDİR: hesap rol etiketi ve tanıtıcıyla anılır ("Muhasip · tanıtıcı muhasip"); ad-soyad
// hiçbir metne girmez (sözlük §5). Tarih ve saat `lib/format` ile yazılır.

import { formatDate } from "../../lib/format";
import type { HesapOzeti, KagitCapasi } from "./api";

/** Kart ve pencere adları (Başlık Düzeni; sözlük §3 "Başlık sabit addır", §4.5). */
export const DENETIM_IZI_KARTI_BASLIGI = "Denetim İzi Bütünlüğü";
export const DEGISTIRILMIS_HESAP_KARTI_BASLIGI = "Değiştirilmiş Hesap Kaydı";
export const GERI_YUKLEME_KARTI_BASLIGI = "Yedekten Geri Yükleme Yapıldı";
export const IKI_DEPO_KARTI_BASLIGI = "Hesaplar ve Güvenlik Dosyası";
export const SON_GIRISLER_KARTI_BASLIGI = "Son Girişler";
export const OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI = "Bütünlük Durumu Okunamadı";
/** Pencere başlığı cümle düzenindedir (sözlük §4.3 "Pencere başlıkları"). */
export const PAROLA_BILDIRIMI_BASLIGI = "Parola yenilenme bildirimi";

/**
 * Kilit açılışındaki denetimin bulguları (backend `iz_dogrulama` ve `denetim_izi` kodları).
 * Yalnız `kesinti` bilgidir; ötekiler uyarıdır.
 */
export const BULGU_METINLERI: Readonly<Record<string, string>> = {
  kuyruk_kesik:
    "Denetim izinin son kayıtları silinmiş ya da veritabanı daha eski bir kopyayla " +
    "değiştirilmiş (geri sarılmış) görünüyor.",
  capa_yok:
    "Kilit işareti bulunamadı; denetim izinin sonu denetlenemedi. Program hiç kilitlenmeden " +
    "kapandıysa (elektrik kesintisi, zorla kapatma) bu beklenebilir; işaret silindiyse son " +
    "kayıtlar da silinmiş olabilir.",
  capa_bozuk: "Kilit işareti okunamadı (dosya bozuk); denetim izinin sonu denetlenemedi.",
  capa_muhru_tutmadi: "Kilit işareti program dışından değiştirilmiş.",
  capa_bayat:
    "Kilit işareti son kilitlenmede yenilenememiş ya da eski bir kopyayla değiştirilmiş; " +
    "denetim izinin sonu tam denetlenemedi.",
  kesinti:
    "Program kilitliyken bir sistem olayının (ör. günlük yedek) denetim izine yazımı yarıda " +
    "kalmış: program kapanmış ya da kayıt yazılamamış (elektrik kesintisi, zorla kapatma ya da " +
    "dolu disk olabilir). Bu bir bilgidir; iş kayıtları etkilenmez.",
  kilitli_satir_eksik:
    "Program kilitliyken yazılan olaylardan bazıları denetim izinde yok; silinmiş olabilir.",
  kilitli_satir_fazla:
    "Denetim izinde, kilit işaretinin saymadığı ve program kilitliyken yazılmış görünen olaylar " +
    "var; işaret eski bir kopyayla değiştirilmiş olabilir.",
  kilitli_sira: "Program kilitliyken yazılan olayların sırası bozuk.",
  kilitli_mac_tutmadi: "Program kilitliyken yazılan bir olay program dışından değiştirilmiş.",
  muhursuz_satir:
    "Kilit işareti yokken yazılmış olaylar var; bunların sonradan değiştirilip " +
    "değiştirilmediği denetlenemez.",
  muhursuz:
    "Kilit işareti yokken yazılmış olaylar var; bunların sonradan değiştirilip " +
    "değiştirilmediği denetlenemez.",
  tohum_tutmadi:
    "Kilit işareti denetim iziyle uyuşmuyor; eski bir kopyayla değiştirilmiş olabilir.",
  dogrulama_yapilamadi: "Denetim izi kilit açılışında beklenmeyen bir hata yüzünden denetlenemedi.",
  sira_boslugu: "Denetim izinin ortasından kayıt silinmiş.",
  zincir_kopuk: "Denetim izinin zinciri kırık: kayıtlar arasındaki bağ tutmuyor.",
  mac_tutmadi: "Denetim izinde program dışından değiştirilmiş kayıt var.",
  satir_kurali:
    "Denetim izinde, türüne ya da yazılış biçimine uymayan bir kayıt var; program dışından " +
    "eklenmiş olabilir.",
  anahtar_yok:
    "Denetim izinde, denetlemek için gereken anahtarı bulunamayan kayıt var; kayıt ya da " +
    "anahtarı program dışından değiştirilmiş olabilir.",
};

/**
 * DENETLEYEMEYEN bulgular: denetim izinin bir bölümü denetlenemedi (kilit işareti yok ya da
 * okunamadı, denetimin kendisi düştü, kilit işareti yokken yazılmış olaylar). Değişiklik
 * görülmedi demek DEĞİLDİR: denetlenemeyen bölümde değişiklik olup olmadığı bilinmez. Yalnız
 * bunlar (ve bilgi) varsa kart değişiklik iddia etmez, geri yüklemeyi öğütlemez, ama "değişiklik
 * yok" da demez. Öteki her kod — tanınmayan kod da (fail-closed) — DEĞİŞİKLİK GÖSTERİR.
 * `anahtar_yok` değişikliktir: bugün meşru bir nedeni yoktur (iz anahtarı silinmez, yenilenmesi
 * sonraki fazdadır); program dışından yazılmış bir kaydın ya da anahtar başvurusunun sonucudur.
 */
export const DENETLENEMEDI_KODLARI: ReadonlySet<string> = new Set([
  "capa_yok",
  "capa_bozuk",
  "dogrulama_yapilamadi",
  "muhursuz_satir",
  "muhursuz",
]);

/** Bilgi düzeyindeki tek bulgu: kesinti. */
const BILGI_KODLARI: ReadonlySet<string> = new Set(["kesinti"]);

/** Bulgu kodu bir değişiklik gösteriyor mu? (denetleyemeyen ve bilgi kodları göstermez) */
export function degisiklikGosterir(kod: string): boolean {
  return !DENETLENEMEDI_KODLARI.has(kod) && !BILGI_KODLARI.has(kod);
}

/** Denetim İzi Bütünlüğü kartının giriş cümleleri (sözlük §4.5). */
export const DENETIM_BILGI_CUMLESI = "Kilit açılırken yapılan denetim bir bilgi verdi:";
export const DENETIM_DEGISIKLIK_CUMLESI =
  "Kilit açılırken yapılan denetim, denetim izinde program dışından yapılmış olabilecek bir " +
  "değişiklik buldu:";
export const DENETIM_DENETLENEMEDI_CUMLESI =
  "Kilit açılırken yapılan denetim, denetim izinin bir bölümünü denetleyemedi:";
/** Yalnız denetleyemeyen bulgu varken kartın dip cümlesi: değişiklik ne iddia edilir ne yadsınır. */
export const DENETIM_DENETLENEMEDI_DIP_CUMLESI =
  "Denetlenemeyen bölümde değişiklik olup olmadığı bilinmiyor; orada yapılmış bir değişiklik " +
  "görünmez. Durum sonraki girişlerde de sürerse program yöneticisine bildirin.";

/** Bütünlük kartlarından biri ya da hepsi okunamadı (sözlük §4.5). */
export const OKUNAMAYAN_BUTUNLUK_METNI =
  "Denetim izinin kartları tam okunamadı; bir uyarı ya da giriş gösterilemiyor olabilir. " +
  "Program yöneticisine ve Denetleme Kuruluna bildirin.";

/** Son Girişler kartının okunamayan bölümleri (backend `okunamayan`; sözlük §4.5). */
export const SON_GIRISLER_OKUNAMADI_METNI =
  "Son girişler okunamadı; tanımadığınız bir giriş burada gösterilemiyor olabilir.";
export const SON_KAYIT_OKUNAMADI_METNI = "Denetim izinin son kaydı okunamadı.";

/** Tanınmayan bulgu kodunda yazılan cümle (kod yazılmaz). */
export const BILINMEYEN_BULGU_METNI = "Denetim izinde tanınmayan bir bulgu var.";

/** Bir bulgu kodunun cümlesi; tanınmayan kodda genel cümle (kod ekrana çıkmaz). */
export function bulguMetni(kod: string): string {
  return Object.prototype.hasOwnProperty.call(BULGU_METINLERI, kod)
    ? BULGU_METINLERI[kod]
    : BILINMEYEN_BULGU_METNI;
}

/** Bulgu kodlarının cümleleri; aynı cümle bir kez yazılır (ör. iki tanınmayan kod). */
export function bulguMetinleri(kodlar: readonly string[]): string[] {
  return [...new Set(kodlar.map(bulguMetni))];
}

/** Kâğıt çapası satırı (tasarım §4.6.3): "Kayıt no: N · Zincir: XXXX-XXXX". No ayrımsızdır. */
export function kagitCapasiSatiri(capa: KagitCapasi): string {
  return `Kayıt no: ${capa.kayit_no} · Zincir: ${capa.zincir}`;
}

/**
 * Hesabın kişisiz adı: "Muhasip · tanıtıcı muhasip" (sözlük §1 "Hesap"; Ayarlar → Güvenlik'in
 * "Bu oturum: …" satırıyla aynı biçim). Kaydı olmayan hesapta yalnız tanıtıcı yazar.
 */
export function hesapEtiketi(hesap: HesapOzeti): string {
  if (hesap.tanitici === null) return hesap.rol_etiketi ?? "Kaydı okunamayan hesap";
  if (hesap.rol_etiketi === null) return `tanıtıcı ${hesap.tanitici}`;
  return `${hesap.rol_etiketi} · tanıtıcı ${hesap.tanitici}`;
}

/**
 * Parola yenilenme bildiriminin ilk cümlesi (tasarım §4.4.3, tehdit 12): "Parolanız
 * gg.aa.yyyy tarihinde sıfırlandı." / "… kurtarma anahtarıyla yenilendi.".
 */
export function parolaYenilenmeCumlesi(tur: string, zaman: string): string {
  const tarih = formatDate(zaman);
  if (tur === "SIFIRLAMA") return `Parolanız ${tarih} tarihinde sıfırlandı.`;
  if (tur === "KURTARMA") return `Parolanız ${tarih} tarihinde kurtarma anahtarıyla yenilendi.`;
  return `Parolanız ${tarih} tarihinde yenilendi.`;
}

/** Bildirimin ne yapılacağını söyleyen cümlesi (türe göre). */
export function parolaYenilenmeOgudu(tur: string): string {
  if (tur === "KURTARMA") {
    return (
      "Kurtarma anahtarını siz kullanmadıysanız ya da tanımadığınız bir giriş varsa okul " +
      "müdürlüğüne ve Denetleme Kuruluna bildirin: anahtarın saklandığı zarf açılmış demektir."
    );
  }
  return (
    "Parolanızın sıfırlanmasını siz istemediyseniz ya da tanımadığınız bir giriş varsa " +
    "Denetleme Kuruluna bildirin."
  );
}
