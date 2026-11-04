// Kullanıcılar ekranının metinleri — tek kaynak (sözlük §1 "Kullanıcılar (F1b)", §4.1). Sunucunun
// iletileri (eylemlerin nedenleri, retler) burada YOKTUR: ekran onları sunucudan olduğu gibi yazar.
// Metinler rol adı saymaz (yetkinin kimde olduğu sunucunun işidir; §1 "Rol süzmesi"); "sarmal",
// "mühür" ve kodlar yüzeye çıkmaz (sözlük §2).

import { formatDate, formatDateTime } from "../../lib/format";
import { hesapEtiketi } from "../butunluk/metinler";
import type { HesapKisaltmasi, KullaniciSatiri, SifirlamaBilgisi } from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const KULLANICILAR_BASLIGI = "Kullanıcılar";

/** Sayfanın açıklaması (sözlük §4.1). */
export const KULLANICILAR_ACIKLAMASI =
  "Programı kullanan hesaplar. Herkes programı kendi hesabıyla ve kendi parolasıyla açar; " +
  "parola paylaşılmaz. Kapalı ve giriş yapamayan hesaplar da listededir: hesap kaydı silinmez.";

/** Liste okunamadığında (sunucunun iletisi yoksa). */
export const LISTE_OKUNAMADI = "Hesap listesi okunamadı.";
export const AYRINTI_OKUNAMADI = "Hesabın ayrıntısı okunamadı.";
export const SECENEKLER_OKUNAMADI = "Rol seçenekleri okunamadı.";

/** Pencere başlıkları (form: eylemin adı; bilgi: adı — sözlük §3). */
export const YENI_HESAP_BASLIGI = "Yeni hesap";
export const SIFIRLAMA_BASLIGI = "Parolayı sıfırla";
export const AYRINTI_BASLIGI = "Hesap ayrıntısı";
/** Kapama onayı (başlık soru, gövde sonuç; sözlük §3). */
export const KAPAMA_ONAY_BASLIGI = "Hesap kapatılsın mı?";

/** Eylem düğmeleri (cümle düzeni). */
export const DUGME_YENI_HESAP = "Yeni hesap";
export const DUGME_HESABI_AC = "Hesabı aç";
export const DUGME_SIFIRLA = "Parolayı sıfırla";
export const DUGME_SIFIRLA_ONAY = "Sıfırla";
export const DUGME_ASKIDAN_CIKAR = "Askıdan çıkar";
export const DUGME_KAPAT = "Hesabı kapat";
export const DUGME_PUSULA = "Hesap teslim pusulasını kaydet";
export const DUGME_YENI_ONERI = "Yeni öneri";

/** Tablo sütunları ve ayrıntı etiketleri. */
export const ETIKET_TANITICI = "Tanıtıcı";
export const ETIKET_ROL = "Rol";
export const ETIKET_HESAP_SAHIBI = "Hesap sahibi";
export const ETIKET_DURUM = "Durum";
export const ETIKET_SON_GIRIS = "Son giriş";
export const ETIKET_GIRIS = "Giriş";
export const ETIKET_ACILIS = "Açılış";
export const ETIKET_KAPANIS = "Kapanış";
export const ETIKET_PAROLA_DEGISIMI = "Son parola değişimi";
export const ETIKET_SIFIRLAMA = "Son sıfırlama";
export const ETIKET_SON_GIRISLER = "Kilit ekranından son girişler";
export const ETIKET_EYLEMLER = "Eylemler";
/** Oturumdaki hesabın işareti (satırda ve ayrıntıda). */
export const BU_OTURUM = "bu oturum";
/** Girebilen hesabın "Giriş" satırı. */
export const GIRIS_ACIK = "Kilit ekranından girebilir.";
/** Son girişler boşsa (SonGirislerKarti'nın cümlesi). */
export const GIRIS_YOK = "Bu hesapla henüz kilit ekranından giriş yapılmadı.";
/** Boş liste (savunma: oturumdaki hesap hep listededir). */
export const LISTE_BOS = "Gösterilecek hesap yok";

/** Form alanları. */
export const ALAN_ROL = "Rol";
export const ALAN_TANITICI = "Tanıtıcı";
export const ALAN_AD_SOYAD = "Ad-soyad";
export const ALAN_GECICI_PAROLA = "Geçici parola";
export const AD_SOYAD_YARDIMI =
  "Hesap sahibinin adı-soyadı; şifreli saklanır, kilit ekranında görünmez.";
/** Rol seçilmeden gönderilirse (sunucunun `_ROLE_MESSAGE`'ı ile birebir). */
export const ROL_SECIN_ILETISI = "Geçerli bir rol seçin.";

/**
 * Geçici parolanın kapalı zarfı (plan F1b-2 "Geçici parola"; BSG Yön. md. 10/1: parola herkesin
 * görebileceği yere yazılmaz — kapalı zarf okul uygulamasıdır). Atıf korpustan doğrulandı
 * (`docs/mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md#madde-10`).
 */
export const ZARF_METNI =
  "Geçici parolayı bir kâğıda yazıp kapalı zarfta hesap sahibine verin; herkesin görebileceği " +
  "bir yere yazmayın (Bilgi ve Sistem Güvenliği Yönergesi 10/1). Program bu parolayı bir daha " +
  "göstermez; hesap sahibi ilk girişte kendi parolasını belirler.";

/** Önerinin açıklaması (alanın altında). */
export const ONERI_YARDIMI =
  "Alandaki parola programın önerisidir: 12 karakter, birbirine karışan harf ve rakam yok. " +
  "Dilerseniz değiştirin.";

/** "Parolayı sıfırla" penceresinin açıklaması (tasarım §4.4.5, §4.3 tehdit 12). */
export const SIFIRLAMA_ACIKLAMASI =
  "Hesabın parolası geçici parolayla değiştirilir ve durumu “Parola yenilenmeli” olur; eski " +
  "parola artık geçmez. Hesap sahibine ilk girişinde parolasının sıfırlandığı ve o andan bu " +
  "yana hesabıyla yapılan girişler gösterilir.";

/** Hesap açmanın sonuç görünümü (geçici parola GÖSTERİLMEZ). */
export const ACILDI_BASLIGI = "Hesap açıldı.";
export const ACILDI_ZARF_METNI =
  "Geçici parolayı yazdığınız kâğıdı kapalı zarfta hesap sahibine verin. Program geçici " +
  "parolayı bir daha göstermez.";
export const PUSULA_ACIKLAMASI =
  "Hesap teslim pusulası hesap sahibine tanıtıcısını, programdaki işini, ilk giriş adımlarını " +
  "ve parola kurallarını anlatır; parola taşımaz. Basıp zarfla birlikte verin; teslim eden ve " +
  "teslim alan imzalar.";
/**
 * Hesap açıldı ama parola kaydı güvenlik dosyasına yazılamadı (sunucunun `OPEN_WRAP_MESSAGE`'ı
 * başta durur): pencerede yazılan geçici parola geçmez, çıkış parola sıfırlamasıdır.
 */
export const YARIM_ACILDI_METNI =
  "Bu pencerede yazılan geçici parola geçerli değil; kâğıda yazdıysanız o kâğıdı vermeyin. " +
  "Hesaba “Parolayı sıfırla” ile yeni bir geçici parola verin.";

/** Süren işler. */
export const ACILIYOR = "Açılıyor…";
export const SIFIRLANIYOR = "Sıfırlanıyor…";
export const HAZIRLANIYOR = "Hazırlanıyor…";
export const ASKIDAN_CIKARILIYOR = "Askıdan çıkarılıyor…";
export const KAPATILIYOR = "Hesap kapatılıyor…";

/** Snackbar'lar (tam cümle). */
export const SIFIRLANDI_ILETISI =
  "Parola sıfırlandı. Geçici parolayı kapalı zarfta hesap sahibine verin.";
export const ASKIDAN_CIKARILDI_ILETISI = "Hesap askıdan çıkarıldı.";
export const KAPATILDI_ILETISI = "Hesap kapatıldı.";
export const PUSULA_KAYDEDILDI_ILETISI = "Hesap teslim pusulası PDF olarak kaydedildi.";

/** Yedek hata iletileri (sunucunun iletisi yoksa). */
export const ACILAMADI = "Hesap açılamadı.";
export const SIFIRLANAMADI = "Parola sıfırlanamadı.";
export const ASKIDAN_CIKARILAMADI = "Hesap askıdan çıkarılamadı.";
export const KAPATILAMADI = "Hesap kapatılamadı.";
export const PUSULA_HAZIRLANAMADI = "Hesap teslim pusulası hazırlanamadı.";

/** Kapama onayının gövdesi: sonuç (sözlük §3). */
export function kapamaSonucu(hesap: Pick<KullaniciSatiri, "rol_etiketi" | "tanitici">): string {
  return (
    `${hesapAdi(hesap)} hesabı kapanır: kilit ekranından kalkar, parola kaydı bu bilgisayarın ` +
    "güvenlik dosyasından silinir. Hesap kaydı ve denetim izindeki kayıtları silinmez. Kapalı " +
    "hesap yeniden açılmaz; gerekirse yeni hesap açılır."
  );
}

/**
 * Hesabın kişisiz adı: "Muhasip · tanıtıcı muhasip" (sözlük §1 "Hesap"; Genel Bakış kartlarının
 * `butunluk/metinler.hesapEtiketi` kalıbı — ayrıntıdaki açan, kapatan ve sıfırlayan onunla yazılır).
 */
export function hesapAdi(hesap: Pick<KullaniciSatiri, "rol_etiketi" | "tanitici">): string {
  return hesapEtiketi({ id: "", tanitici: hesap.tanitici, rol_etiketi: hesap.rol_etiketi });
}

/** Ayrıntıdaki ilgili hesabın adı (kaydı yoksa yalnız tanıtıcı ya da "Kaydı okunamayan hesap"). */
export function kisaltmaAdi(hesap: HesapKisaltmasi): string {
  return hesapEtiketi(hesap);
}

/** Satırın erişilebilir adı (tıklanabilir satır). */
export function satirEtiketi(hesap: Pick<KullaniciSatiri, "rol_etiketi" | "tanitici">): string {
  return `${hesapAdi(hesap)} hesabının ayrıntısını aç`;
}

/**
 * Sıfırlamanın türü (backend `ResetKind` etiketleri; kod ekrana çıkmaz). Türü kayıtlı değilse
 * (program bu hâli yazmaz; yalnız program dışı değişiklikte doğar) "Parola yenilendi".
 */
export function sifirlamaTuru(tur: string | null): string {
  if (tur === "SIFIRLAMA") return "Parola sıfırlandı";
  if (tur === "KURTARMA") return "Kurtarma anahtarıyla yenilendi";
  return "Parola yenilendi";
}

/**
 * Ayrıntının an + ilgili hesap satırı: "03.11.2026 10:15 · açan: Program yöneticisi · tanıtıcı
 * yonetici". An okunamazsa "—" (sunucu okunamayan anı boş verir); hesap yoksa yalnız an.
 */
export function anVeHesap(
  an: string | null,
  onEk: "açan" | "kapatan" | "yapan",
  hesap: HesapKisaltmasi | null,
): string {
  const zaman = formatDateTime(an);
  return hesap === null ? zaman : `${zaman} · ${onEk}: ${kisaltmaAdi(hesap)}`;
}

/** Son sıfırlamanın satırı: "Parola sıfırlandı · 03.11.2026 10:15 · yapan: …"; yoksa "—". */
export function sifirlamaSatiri(sifirlama: SifirlamaBilgisi | null): string {
  if (sifirlama === null) return "—";
  return `${sifirlamaTuru(sifirlama.tur)} · ${anVeHesap(sifirlama.zaman, "yapan", sifirlama.yapan)}`;
}

/**
 * Satırın durum metni: durum etiketi, askıda ise askının nedeni, kapalıysa kapanış günü
 * ("Askıda · Hatalı parola denemesi", "Kapalı · 03.11.2026").
 */
export function durumMetni(
  hesap: Pick<KullaniciSatiri, "durum" | "durum_etiketi" | "askida_nedeni_etiketi" | "kapanis">,
): string {
  if (hesap.askida_nedeni_etiketi) return `${hesap.durum_etiketi} · ${hesap.askida_nedeni_etiketi}`;
  if (hesap.durum === "KAPALI" && hesap.kapanis) {
    return `${hesap.durum_etiketi} · ${formatDate(hesap.kapanis)}`;
  }
  return hesap.durum_etiketi;
}

/**
 * Satırda girişin nedeni gösterilir mi? Giriş kapalıysa evet; yalnız kapalı ve kaydı tutan hesapta
 * hayır ("Hesap kapalı." durumla aynı şeyi söyler). Kaydı tutmayan kapalı hesabın nedeni kayıt
 * iletisidir, gösterilir.
 */
export function girisNedeniGorunur(
  hesap: Pick<KullaniciSatiri, "durum" | "kayit_tutuyor" | "giris">,
): boolean {
  if (hesap.giris.yapabilir || !hesap.giris.neden) return false;
  return hesap.durum !== "KAPALI" || !hesap.kayit_tutuyor;
}

/** Hesap tablosunun erişilebilir adı (ekran okuyucu tabloyu bu adla duyurur). */
export const TABLO_ADI = "Hesaplar";
