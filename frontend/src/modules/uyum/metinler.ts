// Ortak "uyarı + gerekçe" bileşeninin metinleri — tek kaynak (sözlük §1 "Uyarı, gerekçe, engel (kural
// paketi)" ve "Uyarı ve gerekçe (F1c)"; CLAUDE.md altın kural 3). Program doğrusunu gösterir, sapma
// gerekçesiyle kayda geçer; henüz girilmemiş bilgi EKSİKTİR, gerekçe istemez; sert engel yalnız CLAUDE.md'de
// sayılan hâllerdedir. Uyarının kendi metni ve madde atfı SUNUCUNUNDUR (kural paketinin `uyari_metni`;
// "… (md. 12/4)."): ekran onu olduğu gibi yazar, atfı ayrıca "Dayanak" satırında gösterir. Kural kimliği
// (`yonetim_kurulu.secilme_siniri`) yüzeye çıkmaz (sözlük §2).

/** Uyum satırının türleri (tasarım §5.2.7 `ComplianceItem.kind`). */
export const UYUM_EKSIK = "Eksik";
export const UYUM_SAPMA = "Sapma";
export const UYUM_TAKVIM = "Takvim";

/** Türün kısa açıklaması (rozetin yanında). */
export const EKSIK_ACIKLAMASI = "Bilgi henüz girilmedi; gerekçe istemez.";
export const SAPMA_ACIKLAMASI = "Kayıt gerekçesiyle kayda geçti.";
export const SAPMA_GEREKCESIZ_ACIKLAMASI = "Kayıt bu uyarıyla açık duruyor.";
export const TAKVIM_ACIKLAMASI = "Süreye bağlı yükümlülük.";

/** Madde atfının etiketi ("Dayanak: md. 12/4"). */
export const DAYANAK_ETIKETI = "Dayanak";

/** Gerekçe isteyen uyarının kutusu. */
export const GEREKCE_BASLIGI = "Bu kayıt gerekçe istiyor";
export const GEREKCE_ETIKETI = "Gerekçe";
export const GEREKCE_YARDIMI =
  "Program doğrusunu gösterir; kayıt yazdığınız gerekçeyle kayda geçer.";
export const TOPLU_GEREKCE_NOTU =
  "Bu gerekçe aynı nedene bağlı bütün kayıtlarda kullanılır; her kayıt için yeniden sorulmaz.";
export const GEREKCE_ZORUNLU = "Gerekçe yazın.";
export const GEREKCEYLE_KAYDET = "Gerekçeyle kaydet";

/** Sert engel, kural paketi ve dönem kilidi bantlarının başlıkları. */
export const KURAL_SERT_BASLIGI = "Kayıt yapılmadı";
export const KURAL_PAKETI_BASLIGI = "Kural paketi okunamadı";
export const DONEM_KILIDI_BASLIGI = "Bu kayıt yazılamaz";
