// Temsilciler ekranının metinleri — tek kaynak (sözlük §1 "Temsilciler ekranı (F1c)", §4.1). Temsil
// türlerinin adları backend `Representation`'ınkidir (`gecis-kurulumu/api.TEMSIL_TURU_TR`). Satırın uyarı
// metni kural paketinindir (atıflı). Program karar defterinin yerine geçmez (CLAUDE.md §1).

import { DUGME_KAYDI_IPTAL } from "../organlar/metinler";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const TEMSILCILER_BASLIGI = "Temsilciler";
export const TEMSILCILER_ACIKLAMASI =
  "Birliğin kurul ve komisyonlardaki temsilcileri. Kurul temsilcilerini yönetim kurulu kararı " +
  "belirler; birlik başkanı bazı komisyonlara başkan sıfatıyla kendiliğinden girer. Kayıt silinmez; " +
  "yanlış kayıt gerekçeyle iptal edilir.";

export const CIZELGE_BASLIGI = "Temsilciler Çizelgesi";
export const CIZELGE_OKUNAMADI = "Temsilciler çizelgesi okunamadı.";
export const CIZELGE_BOS = "Bu birlik döneminde gösterilecek kurul ya da komisyon yok.";
export const TEMSILCI_GIRILMEDI = "Temsilci girilmedi.";

/** Satırın işaretleri. */
export const DURUM_UYARI = "Uyarı";
export const DURUM_EKSIK = "Eksik";
export const CIP_KARAR_BAGLI = "Yönetim kurulu kararına bağlı";

/** Düğmeler. */
export const DUGME_TEMSILCI_EKLE = "Temsilci ekle";

/** Temsilci penceresi. */
export const TEMSILCI_PENCERESI_BASLIGI = "Temsilci ekle";
export const ALAN_GOREVLENDIRME_GUNU = "Görevlendirme günü";
export const ALAN_KARAR = "Yönetim kurulu kararı";
export const TEMSILCI_EKLENDI = "Temsilci eklendi.";
export const TEMSILCI_EKLENEMEDI = "Temsilci eklenemedi.";

/** İptal. */
export const TEMSILCI_IPTAL_BASLIGI = "Temsilci kaydı iptal edilsin mi?";
export const TEMSILCI_IPTAL_METNI =
  "Kayıt silinmez, iptal gerekçesiyle kalır. Doğru bilgi yeni kayıtla girilir.";

/** Temsilci satırındaki iptal düğmesinin erişilebilir adı: "Kurulun adı: Ad Soyad Kaydı iptal et"
 * ("Temsilci ekle" düğmesinin "Kurulun adı: …" deseni; aynı kişi iki kartta temsilciyse adlar ayrılır). */
export function temsilciIptalEtiketi(kurul: string, ad: string | null): string {
  return `${kurul}: ${ad ? `${ad} ` : ""}${DUGME_KAYDI_IPTAL}`;
}

/** "Ad Soyad · Yedek" */
export function temsilciMetni(ad: string, koltuk: string): string {
  return `${ad} · ${koltuk}`;
}
