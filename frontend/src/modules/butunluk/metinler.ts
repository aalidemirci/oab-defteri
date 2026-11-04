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

/** Açılış günü kayıttan okunamadığında (program dışından yazılmış an; sözlük §1 "Denetim izi"). */
export const ACILIS_GUNU_OKUNAMADI = "açılış günü okunamadı";

/**
 * Hesabın açılış ve kapanış günü (orkestratör maddesi F-3; sözlük §1 "Denetim izi"): tanıtıcı
 * yalnız açık hesaplar arasında tekildir, kapanan "muhasip"in yerine açılan yeni hesap da
 * "muhasip" olabilir — iki hesap bu günlerle ayrılır: "açılış 01.11.2026" · "açılış 01.11.2026,
 * kapanış 03.11.2026". Açılış günü yoksa (kayıt söylemiyor) "açılış günü okunamadı"; kapanış
 * günü yoksa hesap açıktır (ya da kapanışı okunamadı; ikisi ayrılamaz) ve yazılmaz.
 *
 * Özet günleri taşımıyorsa (iki depo listeleri, eski yanıt: alanlar YOK) ya da hesabın kaydı
 * yoksa (tanıtıcı null) null: o hesabın günü bilinemez, ayrıca yazılmaz.
 */
export function hesapGunleri(hesap: HesapOzeti): string | null {
  if (hesap.tanitici === null) return null;
  if (hesap.acilis === undefined && hesap.kapanis === undefined) return null;
  const parcalar = [hesap.acilis ? `açılış ${formatDate(hesap.acilis)}` : ACILIS_GUNU_OKUNAMADI];
  if (hesap.kapanis) parcalar.push(`kapanış ${formatDate(hesap.kapanis)}`);
  return parcalar.join(", ");
}

/**
 * Hesabın kişisiz adı ve günleri: "Muhasip · tanıtıcı muhasip (açılış 01.11.2026, kapanış
 * 03.11.2026)" (`hesapEtiketi` + `hesapGunleri`). Kartlardaki ve Erişim Günlüğü'ndeki hesap bu
 * biçimle yazılır; günler yoksa yalnız ad.
 */
export function hesapEtiketiGunlu(hesap: HesapOzeti): string {
  const gunler = hesapGunleri(hesap);
  return gunler === null ? hesapEtiketi(hesap) : `${hesapEtiketi(hesap)} (${gunler})`;
}

// --- Değiştirilmiş Hesap Kaydı kartı (sözlük §4.5; §1 "Hesap kaydının ve denetim izinin
// tutmaması") ---------------------------------------------------------------------------------
// Girişte ya da bir hesap işleminde hesabın kaydı tutmadı; `BUTUNLUK` satırının alan adı bulgunun
// türüdür (`app_password._muhur_bozuk_izi`): `seal` (mühür), `kayit_mac` (satır eski bir kopyadan
// geri konmuş: denetim izindeki son kaydını tutmuyor), `iz_boslugu` (hesabın son kaydından sonra
// denetim izinden kayıt silinmiş ya da sırası değiştirilmiş) ve `wrap_digest` (parola kaydı hesap
// kaydındaki özeti tutmuyor). Metin nötrdür: olay giriş de olabilir hesap işlemi de (Kullanıcılar,
// "Gördüm", sahipsiz kaydın silinmesi; parola kaydında açık oturumdaki parola işlemi). "Rol değiştirilmiş olabilir" yalnız mühür bulgusundadır:
// öteki üçünde hesap kaydının mührü tutar, kayıttaki rol doğrudur.

/** Bulgunun türü (kartın grubu). Tanınmayan ya da boş kod mühür sayılır (fail-closed). */
export type HesapBulgusuTuru = "muhur" | "kayit" | "bosluk" | "parola_kaydi";

/** Hesap bulgusunun tanınan alan adları (backend `AccountSealMismatch.alan` ve alt sınıfları). */
const HESAP_BULGU_KODLARI: ReadonlySet<string> = new Set([
  "seal",
  "kayit_mac",
  "iz_boslugu",
  "wrap_digest",
]);

/** `BUTUNLUK` satırının alan adından kartın grubu (yukarıdaki not). */
export function hesapBulgusuTuru(kodlar: readonly string[]): HesapBulgusuTuru {
  if (kodlar.length === 0 || kodlar.some((k) => !HESAP_BULGU_KODLARI.has(k) || k === "seal")) {
    return "muhur";
  }
  if (kodlar.includes("kayit_mac")) return "kayit";
  if (kodlar.includes("iz_boslugu")) return "bosluk";
  return "parola_kaydi";
}

/** Mühür ve satırın izi (kaydı değiştirilmiş görünen hesap). */
export const KAYIT_DEGISMIS_GIRISI =
  "Kaydı program dışından değiştirilmiş görünen hesapla giriş ya da hesap işlemi denendi; " +
  "program işlemi yapmadı ve kayda dokunmadı:";
/** Yalnız mühür bulgusunda: kayıttaki rolün kendisi değiştirilmiş olabilir. */
export const ROL_DEGISMIS_OLABILIR = "Kayıtta yazan rol, değiştirilmiş rol olabilir.";
/** İz boşluğu: değişen hesap kaydı değil denetim izidir. */
export const IZ_BOSLUGU_GIRISI =
  "Denetim izinden kayıt silinmiş ya da kayıtların sırası program dışından değiştirilmiş " +
  "göründüğü için bu hesapla giriş ya da hesap işlemi açılmadı; program kayda dokunmadı:";
/**
 * Parola kaydının özeti tutmadı (kilit ekranında ya da açık oturumdaki parola işleminde: parola
 * değiştirme, kurtarma anahtarının yenilenmesi — `app_password._check_session_password` aynı
 * `wrap_digest` satırını yazar). Metin bu yüzden "giriş açılmadı" demez.
 */
export const PAROLA_KAYDI_GIRISI =
  "Parola kaydı hesap kaydındakiyle uyuşmayan hesapla giriş ya da parola işlemi denendi; " +
  "program işlemi yapmadı ve kayıtlara dokunmadı.";
/** Parola kaydı bulgusunun açıklaması ve çaresi (ardından kartın ortak dip cümlesi gelir). */
export const PAROLA_KAYDI_ACIKLAMASI =
  "Parola kaydı program dışından değiştirilmiş ya da yedekten geri yüklemeden sonra eski kalmış " +
  "olabilir; hesap kaydındaki rol doğrudur. Hesabın parolasını program yöneticisi sıfırlar " +
  "(program yöneticisinin kendi hesabıysa “Parolamı unuttum” yolundan kurtarma anahtarıyla " +
  "açılır).";
/** Kartın ortak dip cümlesi (bütün türler). */
export const DENETLEME_KURULUNA_BILDIRIN = "Durumu Denetleme Kuruluna bildirin.";

// --- Yedekten Geri Yükleme Yapıldı kartının "Gördüm"ü (sözlük §1 "Geri yükleme kartının
// “Gördüm”ü (F1b)", §4.5; plan F1b-2 "Gördüm."; kullanıcı kararı 02.11.2026) -----------------

export const GORDUM_DUGMESI = "Gördüm";
export const GORDUM_KAYDEDILIYOR = "Kaydediliyor…";
/** "Gördüm" kartı kaldırdığında (snackbar). */
export const GORDUM_KART_KALKTI = "Geri yükleme kartı herkes için kalktı.";
/** Sunucunun iletisi yoksa. */
export const GORDUM_KAYDEDILEMEDI = "“Gördüm” kaydedilemedi.";
/** "Gördüm" diyebilen hesapta (Denetleme Kurulu) kartın dip cümlesi. */
export const GORDUM_ACIKLAMASI =
  "Denetleme Kurulundan bir üyenin “Gördüm” demesi yeter: kart herkes için kalkar, kimin " +
  "gördüğü denetim izinde kalır.";
/** "Gördüm" diyemeyen hesapta (program yöneticisi) kartın dip cümleleri. */
export const GERI_YUKLEME_BILDIRIN =
  "Geri yüklemeyi kimin ve neden yaptığını Denetleme Kuruluna bildirin. Kart, Denetleme " +
  "Kurulunun bir üyesi “Gördüm” deyince herkes için kalkar; programda Denetleme Kurulunun açık " +
  "hesabı yoksa kart kalır.";

// --- Hesaplar ve Güvenlik Dosyası kartı (sözlük §4.5) ---------------------------------------

/** Kartın giriş cümlesi: iki depo farkı (parola kaydı olmayan, kalan ya da tutmayan hesap). */
export const IKI_DEPO_GIRISI =
  "Bu bilgisayarın güvenlik dosyasındaki hesaplarla veritabanındaki hesap kayıtları uyuşmuyor.";
/** Yalnız geri yüklemenin doğurduğu farklarda (giriş yapamayan ya da kalan eski kayıt). */
export const IKI_DEPO_GERI_YUKLEME_CUMLESI = "Bu çoğunlukla yedekten geri yüklemeden sonra olur.";
export const OZETI_TUTMAYAN_BASLIGI = "Parola kaydı hesap kaydıyla uyuşmayan hesaplar";
export const OZETI_TUTMAYAN_ACIKLAMASI =
  "Bu hesapların güvenlik dosyasındaki parola kaydı hesap kaydındakiyle uyuşmuyor; sahipleri " +
  "giriş yapamaz. Parola kaydı program dışından değiştirilmiş ya da yedekten geri yüklemeden " +
  "sonra eski kalmış olabilir. Parolalarını program yöneticisi Kullanıcılar ekranında hesabın " +
  "ayrıntısından sıfırlar (“Parolayı sıfırla”); program yöneticisinin kendi hesabıysa kilit " +
  "ekranındaki “Parolamı unuttum” yolundan kurtarma anahtarıyla açılır. Durumu Denetleme " +
  "Kuruluna bildirin.";
/**
 * Kaydı ya da izi tutmayan hesaplar (backend `TwoStoreDifferences.seal_mismatch`: mührü tutmayan,
 * eski bir kopyadan geri konmuş ya da son kaydından sonra denetim izinden kayıt silinmiş): değişen
 * hesap kaydı da olabilir denetim izi de, metin ikisini de kapsar.
 */
export const MUHRU_TUTMAYAN_BASLIGI =
  "Kaydı ya da denetim izi program dışından değiştirilmiş görünen hesaplar";
export const MUHRU_TUTMAYAN_ACIKLAMASI =
  "Bu hesapların kaydı ya da denetim izindeki kayıtları program dışından değiştirilmiş " +
  "görünüyor; program onlara dokunmaz. Durumu Denetleme Kuruluna bildirin.";
/** Kullanıcılar ekranına bağlantı (parolayı sıfırlanacak hesap varken; `kullanicilar` yeteneği). */
export const KULLANICILARI_AC = "Kullanıcılar'ı aç";

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
