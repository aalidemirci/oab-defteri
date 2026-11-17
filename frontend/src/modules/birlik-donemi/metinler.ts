// Birlik Dönemi ekranının metinleri — tek kaynak (sözlük §1 "Birlik dönemi", §4.1 "Birlik Dönemi").
// "Birlik dönemi" genel kuruldan genel kurula süren dönemdir; ders yılının iki dönemi (ders dönemi) ayrı
// kavramdır, tek başına "dönem" ders dönemiyle karışacak yerde yazılmaz (T3). Kural paketinin iç kimliği
// (kural kodları) yüzeye çıkmaz; paketin adı ve revizyonu salt okunur gösterilir (plan F1c kararları).

import type { DonemDurumu } from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const BIRLIK_DONEMI_BASLIGI = "Birlik Dönemi";

export const BIRLIK_DONEMI_ACIKLAMASI =
  "Okul-aile birliğinin genel kuruldan genel kurula süren dönemi. Her birlik dönemi açıldığı " +
  "günkü kural sürümüyle hesaplanır; kapanmış birlik dönemi salt okunurdur.";

/** Birlik dönemi yokken. */
export const DONEM_YOK_BASLIGI = "Birlik dönemi açılmadı";
export const DONEM_YOK_ACIKLAMASI =
  "Program okula bir birlik döneminin ortasında giriyorsa birlik dönemini geçiş kurulumuyla açın. " +
  "Okulda daha önce genel kurul yapılmadıysa geçiş kurulumu gerekmez.";

export const DONEMLER_OKUNAMADI = "Birlik dönemleri okunamadı.";

/** Liste ve ayrıntı. */
export const DONEMLER_BASLIGI = "Birlik Dönemleri";
export const DONEM_AYRINTISI_BASLIGI = "Birlik Döneminin Bilgileri";
export const SUTUN_AD = "Ad";
export const SUTUN_BASLANGIC = "Başlangıç";
export const SUTUN_BITIS = "Bitiş";
export const SUTUN_DURUM = "Durum";
export const ALAN_DERS_YILI = "Ders yılı";
export const ALAN_BASLANGIC = "Başlangıç (genel kurul günü)";
export const ALAN_PROGRAM_BASLAMA = "Programa başlama günü";
export const ALAN_KURAL_SURUMU = "Kural sürümü";
export const KURAL_SURUMU_YARDIMI =
  "Birlik dönemi açıldığı günkü kural sürümüyle hesaplanır; sürüm yalnız program yöneticisinin " +
  "onayıyla, Birlik Dönemi → Kural Sürümü Güncellemesi'nde farkı görülerek değişir.";
export const ALAN_ACILIS = "Açılış";
export const ACILIS_GECIS = "Geçiş kurulumuyla açıldı";
export const ACILIS_GENEL_KURUL = "Genel kurulla açıldı";
/** Hazırlık dönemi: genel kurul planlandı, dönem genel kuruldan sonra açılır (U3, U32). */
export const ACILIS_HAZIRLIK = "Genel kuruldan sonra program yöneticisinin onayıyla açılır";
/** Dönemi açacak genel kurul iptal edildi (hazırlık dönemi de iptal). */
export const ACILIS_IPTAL = "Dönemi açacak genel kurul iptal edildi";
export const DUGME_GENEL_KURULU_AC = "Genel kurulu aç";
/** Yeni açılan okul (S5 (iii)): ilk birlik dönemi ilk genel kurulla açılır. */
export const DONEM_YOK_YENI_OKUL_ACIKLAMASI =
  "Okul yeni açıldı: ilk birlik dönemi ilk genel kurulla açılır. Genel kurulu planlayın; okul " +
  "müdürü daveti kendi hesabından yazar.";
/** Boş durumdaki bağlantı (sözlük §3: bağlantı metni gittiği yeri adıyla söyler; yol haritasınınkiyle aynı). */
export const BAG_GENEL_KURUL_EKRANI = "Genel Kurul'u aç";

/** Kural sürümü güncellemesi (tasarım §6.2-5; yalnız program yöneticisi). */
export const KURAL_GUNCELLEME_BASLIGI = "Kural Sürümü Güncellemesi";
export const KURAL_GUNCELLEME_ACIKLAMASI =
  "Programla yeni kural sürümü gelince birlik dönemi kendiliğinden geçmez: farkı görüp onaylayın. " +
  "Hesabı ya da uyarısı değişecek kayıt varsa listesi gösterilir ve geçiş ayrıca onay ister. " +
  "Önceki sürüme geri dönülebilir; kapanmış birlik döneminin sürümü değişmez.";
export const KURAL_GUNCELLEME_OKUNAMADI = "Kural sürümünün durumu okunamadı.";
export const ALAN_BAGLI_SURUM = "Bağlı sürüm";
export const ALAN_EN_YENI_SURUM = "Programla gelen en yeni sürüm";
export const ALAN_HEDEF_SURUM = "Geçilecek sürüm";
export const KURAL_GUNCEL = "Birlik dönemi programla gelen en yeni kural sürümünde.";
export const KURAL_GECILEMEZ = "Bu birlik döneminin kural sürümü değiştirilemez.";
export const FARK_EKLENEN = "Eklenen kurallar";
export const FARK_CIKARILAN = "Çıkarılan kurallar";
export const FARK_BITEN = "Yürürlüğü biten kurallar";
export const FARK_DEGER = "Değeri değişen kurallar";
export const FARK_DUZELTILEN = "Düzeltilen kurallar";
export const FARK_BOS = "İki sürüm arasında kural farkı yok.";
export const ETKILENEN_KAYITLAR = "Hesabı ya da uyarısı değişecek kayıtlar";
export const ETKILENEN_ONAYI =
  "Bu kayıtların hesabının ya da uyarısının değişeceğini gördüm; geçişi onaylıyorum.";
export const ETKILENEN_ONAYI_GEREKLI = "Etkilenen kayıtların listesini onaylayın.";
export const DUGME_SURUMU_GUNCELLE = "Kural sürümünü güncelle";
export const DUGME_GERI_AL = "Önceki sürüme geri al";
export const SURUM_GUNCELLENDI = "Kural sürümü güncellendi.";
export const SURUM_GUNCELLENEMEDI = "Kural sürümü güncellenemedi.";
export const BILINMEYEN_KAYIT = "Kayıt";
/** Etkilenen kaydın türü (model kodu yüzeye çıkmaz; sözlük §2). */
export const KAYIT_TURU_TR: Readonly<Record<string, string>> = {
  "oab.GeneralAssembly": "Genel kurul",
  "oab.ComplianceItem": "Uyum satırı",
};

/** "Genel kurul · kayıt 12" */
export function etkilenenKayitMetni(tur: string, kimlik: string): string {
  return `${tur} · kayıt ${kimlik}`;
}
export const BITIS_YOK = "Sonraki olağan genel kurul";
/** Ayarlar'daki salt okunur kural sürümü satırının bölüm başlığı (plan F1c kararları). */
export const KURAL_SURUMU_AYARLAR_BASLIGI = "Kural Sürümü";

/** D7: dönemin kural kopyası doğrulanamadı (backend `DonemSaltOkur` iletisiyle aynı söz). */
export const KURAL_KOPYASI_BOZUK =
  "Bu birlik döneminin kural kopyası doğrulanamadığı için dönem salt okunur açıldı. Yedekten geri " +
  "yükleme için program yöneticisine başvurun.";

/** Kapanmış dönem (O2). */
export const DONEM_KAPANDI_NOTU = "Bu birlik dönemi kapandı; kayıtları salt okunurdur.";

/** Görev süresi uyarılarının listesi (md. 12/2, 14/2; kaydedilmez, gerekçe istemez). */
export const GOREV_SURESI_BASLIGI = "Görev süresi uyarıları";

/** Geçiş kurulumu kartı. */
export const GECIS_KARTI_BASLIGI = "Geçiş Kurulumu";
export const GECIS_KARTI_ACIKLAMASI =
  "Program okula birlik döneminin ortasında girdiyse görevdeki kurul, programdan önceki seçilme " +
  "sayıları ve karar defterinin son sıra no'su geçiş kurulumunda girilir.";
export const DUGME_GECISI_AC = "Geçiş kurulumunu aç";

/** Dönem iptali (yalnız geçiş dönemi, "Geçiş kurulumu tamamlandı" işaretinden önce). */
export const DUGME_DONEMI_IPTAL = "Birlik dönemini iptal et";
export const DONEM_IPTAL_BASLIGI = "Birlik dönemi iptal edilsin mi?";
export const DONEM_IPTAL_METNI =
  "Yanlış girilmiş birlik dönemi iptal edilir: kayıt silinmez, iptal gerekçesiyle kalır. Dönemde " +
  "görevdeki üye ya da açık karar defteri kaydı varsa önce onlar iptal edilir. Sonra doğru " +
  "bilgiyle yeni birlik dönemi açılır.";
export const DONEM_IPTAL_EDILDI = "Birlik dönemi iptal edildi.";
export const DONEM_IPTAL_EDILEMEDI = "Birlik dönemi iptal edilemedi.";

/** Durumların görünen adları (backend `TermStatus`). */
export const DONEM_DURUMU_TR: Record<DonemDurumu, string> = {
  HAZIRLIK: "Hazırlık",
  ACIK: "Açık",
  KAPANISTA: "Kapanışta",
  KAPANDI: "Kapandı",
  IPTAL: "İptal edildi",
};

/** "OAB-2023.12 · 1. revizyon" */
export function kuralSurumuMetni(kural: { paket: string; rev: number }): string {
  return `${kural.paket} · ${kural.rev}. revizyon`;
}
