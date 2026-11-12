// Görev bölümü ve temsilci evrakının ekran metinleri — tek kaynak (sözlük §1 "Görev bölümü ve temsilci
// evrakı (F1c)"; belge adları backend `gorev_evraki.BELGE_ADLARI` ile birebir). Program karar defterinin
// yerine geçmez: karar taslağı defterine el ile yazılır (CLAUDE.md §1). Evrak kodları (E01…) yüzeye
// çıkmaz (sözlük §2).

/** Belgelerin adları (kartın başlığı). */
export const E01_ADI = "Yönetim kurulu görev bölümü, imza yetkisi ve temsilci karar taslağı";
export const E02_ADI = "Denetleme Kurulu görev bölümü tutanağı ve denetim planı";
export const E03_ADI = "Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi";

/** Kartın açıklamaları. */
export const TASLAK_ACIKLAMASI =
  "Karar taslağıdır: karar defterine el ile yazılır ve imzalanır; program karar defterinin yerine " +
  "geçmez.";
export const TUTANAK_ACIKLAMASI =
  "Denetleme Kurulunun görev bölümü toplantısının tutanağı ve denetim planı; kurul üyelerince " +
  "imzalanır.";

/** Kaydın durumu. */
export const EVRAK_YOK = "Belge henüz oluşturulmadı.";
export const EVRAK_OKUNAMADI = "Belgenin kaydı okunamadı.";

/** Düğmeler ve bildirimler. */
export const DUGME_OLUSTUR = "Belgeyi oluştur";
export const DUGME_YENIDEN_OLUSTUR = "Belgeyi yeniden oluştur";
export const OLUSTURULUYOR = "Oluşturuluyor…";
export const DUGME_PDF = "PDF olarak kaydet";
export const DUGME_WORD = "Word olarak kaydet";
export const HAZIRLANIYOR = "Hazırlanıyor…";
export const EVRAK_OLUSTURULDU = "Belge oluşturuldu.";
export const EVRAK_OLUSTURULAMADI = "Belge oluşturulamadı.";
export const PDF_KAYDEDILDI = "Belge PDF olarak kaydedildi.";
export const WORD_KAYDEDILDI = "Belge Word olarak kaydedildi.";
export const EVRAK_KAYDEDILEMEDI = "Belge kaydedilemedi.";

/** Basım uyarılarının listesi (üretimin yanıtı; belgeye basılmaz). */
export const URETIM_UYARILARI_BASLIGI = "Belgedeki boş yerler";
export const URETIM_UYARILARI_NOTU =
  "Bu uyarılar belgeye basılmaz. Eksik bilgiyi tamamlayıp belgeyi yeniden oluşturabilirsiniz.";

/** "Son oluşturma: gg.aa.yyyy SS:dd · 2. sürüm" */
export function sonOlusturmaMetni(an: string, surum: number): string {
  return `Son oluşturma: ${an} · ${surum}. sürüm`;
}
