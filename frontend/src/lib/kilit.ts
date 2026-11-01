// Kilit ve ön yüz belleği — tasarım §4.4.3 "Ön yüz belleği", §13 D53 (denetim GA-23);
// plan F1b-1 "Oturum". Backend kilit kapısının (`apps/okul/lock_middleware`) arayüz
// ayağı ve pencere içeriğini yeniden yükleyen TEK yer.
//
// NEDEN YENİDEN YÜKLEME. Kilitlenmede ve kilit ekranından her açılışta önceki hesabın
// yüklediği maskesiz veri (react-query önbelleği, modül belleği: bekleyen kurtarma
// anahtarı, `lib/api` etkileşim saatleri, açık formlar) sonraki hesabın oturumunda
// kalmamalıdır. Tek tek temizlemek yerine pencere içeriği yeniden yüklenir: oturum
// çerezi kalır (masaüstü `session_guard`), SPA her yolu `index.html`'e verir; sağlayıcılar
// ve önbellek sıfırdan kurulur.
//
// İKİ AN, BAŞKA YOK (plan F1b-1):
//   1. Kilitlenme — elle Kilitle (`kilitlendi("elle")`), oturum yoklamasının gördüğü
//      boşta kilit (`kilitlendi("yoklama")`) ya da ön yüz oturumu AÇIK SANIRKEN gelen
//      423 `locked` / `guvenlik_dosyasi_kayip` (`kilitKapisiYaniti`).
//   2. Kilit ekranından açılış — kilit açma ya da kurtarma anahtarıyla açılış (`acildi`).
// Kurulumdaki ilk hesap (enable) ve parola değişimi yeniden YÜKLEMEZ: ilkinde sihirbaz
// kurtarma anahtarını ekranda tutmayı sürdürür, ikincisinde hesap ve veri aynıdır.
//
// DÖNGÜ KORUMASI. 423 yalnız ön yüz oturumu açık sanırken yeniden yükler; ön yüz
// kilitli olduğunu zaten biliyorsa (kilit ekranı ya da kayıp dosya ekranı gösteriliyor)
// 423 yalnız `od:kilit-kapisi` olayını yayınlar ve güvenlik kapısı durumu yeniden okur.
// Yeniden yüklemeden sonra kapı durumu sunucudan okur, kilitliyse "açık sanma" bayrağı
// kalkmış başlar: aynı 423 ikinci yüklemeyi doğuramaz. Bir yükleme istendikten sonra
// (sayfa henüz boşalmadan uçuştaki öteki 423'ler de dönebilir) ikinci istek yok sayılır.
// Bayrağı yalnız OLUMLU okunmuş açık durum kaldırır: durum ucu okunamayınca (fail-open)
// bayrak kalkmaz, yoksa okunamayan durum + 423 sonsuz yüklemeye dönerdi.
//
// Yeniden yükleme jsdom'da uygulanmaz: tek çağrı noktası `pencereIcerigi.yenidenYukle`dir,
// testler onu taklit eder (`test/setup.ts`; `kilit.test.ts`).

/** 423 gövdesindeki kodlar (`lock_middleware`). */
export const KILIT_KAPISI_KODLARI: ReadonlySet<string> = new Set([
  "locked",
  "guvenlik_dosyasi_kayip",
]);

/**
 * Ön yüz kilitli olduğunu bilirken gelen 423'ün olayı: güvenlik kapısı
 * (`modules/guvenlik/GuvenlikKapisi`) dinler ve durumu yeniden okur (ör. kilit ekranı
 * açıkken güvenlik dosyası kayboldu → kayıp dosya ekranı). `lib/restart.ts` deseni.
 */
export const KILIT_KAPISI_OLAYI = "od:kilit-kapisi";

/** Kilitlenmenin nedeni (yalnız okunaklılık ve testler için; davranışı `elle` ayırır). */
export type KilitlenmeNedeni = "elle" | "yoklama" | "kilit-kapisi";

/** Pencere içeriğinin TEK yeniden yükleme noktası (testler taklit eder). */
export const pencereIcerigi = {
  yenidenYukle(): void {
    window.location.reload();
  },
};

let acikSaniliyor = false;
let yukleniyor = false;

/** Ön yüz oturumu açık sanıyor mu? (Döngü korumasının bayrağı; dosya başı notu.) */
export function oturumAcikSaniliyor(): boolean {
  return acikSaniliyor;
}

/**
 * Bayrağı yazar. Güvenlik kapısı durumu okuyunca, oturum yoklaması özeti alınca ve
 * ilk hesap kurulunca çağırır. Kilit ve kayıp dosya ekranı gösterilirken `false`'tur.
 */
export function oturumAcikSan(acik: boolean): void {
  acikSaniliyor = acik;
}

/** Bu pencerede yeniden yükleme istendi mi? (Sayfa boşalana dek ikinci istek yok sayılır.) */
export function yenidenYuklemeIstendi(): boolean {
  return yukleniyor;
}

function yenidenYukle(): void {
  if (yukleniyor) return;
  yukleniyor = true;
  acikSaniliyor = false;
  pencereIcerigi.yenidenYukle();
}

/**
 * Oturum kilitlendi: pencere içeriği yeniden yüklenir. Elle Kilitle her zaman yükler
 * (kullanıcının kendi eylemi; ön yüz kurulumdayken bayrak henüz kalkmamış olabilir).
 * Yoklamanın ya da 423'ün gördüğü kilit yalnız ön yüz oturumu açık sanırken yükler.
 * Yükleme yapıldıysa `true` döner.
 */
export function kilitlendi(neden: KilitlenmeNedeni): boolean {
  if (yukleniyor) return false;
  if (neden !== "elle" && !acikSaniliyor) return false;
  yenidenYukle();
  return true;
}

/** Kilit ekranından açılış (kilit açma ya da kurtarma anahtarı): pencere yeniden yüklenir. */
export function acildi(): void {
  yenidenYukle();
}

/**
 * `lib/api.ts`'in 423 kancası: ön yüz oturumu açık sanıyorsa kilitlenmedir (yükle);
 * değilse yalnız olay yayınlanır, güvenlik kapısı durumu yeniden okur.
 */
export function kilitKapisiYaniti(code: string): void {
  if (!KILIT_KAPISI_KODLARI.has(code) || yukleniyor) return;
  if (kilitlendi("kilit-kapisi")) return;
  window.dispatchEvent(new CustomEvent(KILIT_KAPISI_OLAYI));
}

/** Yalnız testler için: modül düzeyindeki bayrakları sıfırlar (`test/setup.ts`). */
export function kilitDurumunuSifirla(): void {
  acikSaniliyor = false;
  yukleniyor = false;
}
