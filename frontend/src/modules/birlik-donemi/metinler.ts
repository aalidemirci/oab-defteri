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
  "Birlik dönemi açıldığı günkü kural sürümüyle hesaplanır; sürüm bu ekranda değiştirilmez.";
export const ALAN_ACILIS = "Açılış";
export const ACILIS_GECIS = "Geçiş kurulumuyla açıldı";
export const ACILIS_GENEL_KURUL = "Genel kurulla açıldı";
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
