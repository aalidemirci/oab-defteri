// Hakkında → Kişisel Veri kartının metinleri — tek kaynak (sözlük §1 "Hakkında ve Lisans"; belge adı
// backend `genel_kurul_evraki.BELGE_ADLARI["E04"]` ile birebir, `evrak/metinler.E04_ADI`). Düğme ve durum
// satırları görev bölümü evrakının kartıyla ortaktır (`evrak/metinler`).

/** Kartın başlığı. */
export const KISISEL_VERI_BASLIGI = "Kişisel Veri";

/** Kartın açıklaması. */
export const KISISEL_VERI_ACIKLAMASI =
  "Okul-aile birliğinin işlerinde kişisel verisi işlenen kişilerin aydınlatma metni (KVKK md. 10): " +
  "veli ve üye, personel, istekli, kiracı ve çalışan, bağışçı ve tedarikçi. Genel kurul davetindeki " +
  "kısa metin, tamamının okul ilan panosunda ve okulun internet sayfasında olduğunu söyler; " +
  "belgenin PDF'i oraya konur. Programdaki kişisel verilere ilişkin başvurular okul müdürlüğüne " +
  "yapılır.";

/** Okul Bilgileri'nde veri sorumlusu boşken (üretilmez ve basılmaz; sunucu da reddeder). */
export const E04_VERI_SORUMLUSU_GIRILMEDI =
  "Okul Bilgileri'nde veri sorumlusu bilgisi girilmedi. Aydınlatma metni bu bilgi olmadan " +
  "oluşturulmaz ve kaydedilmez.";

/** Okul Bilgileri sekmesine bağlantı (Başlangıç Yol Haritası ve aktarım ekranlarıyla aynı). */
export const OKUL_BILGILERI_BAGLANTISI = "Ayarlar → Okul Bilgileri'ni aç";

/** Her basımda geçerli uyarılar (sunucunun; belgeye basılmaz). */
export const TEYIT_BASLIGI = "Okul müdürlüğünce teyit edilecekler";
export const TEYIT_NOTU = "Bu uyarılar belgeye basılmaz.";
