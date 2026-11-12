// Görev bölümü ve temsilci evrakı (E01, E02, E03) — backend `apps/oab/views.py` (`TermDocumentListView`,
// `E01DocumentView`, `E02DocumentView`, `E03DocumentView`, `DocumentDownloadView`) ile BİREBİR (plan F1c
// 10. adım notları; düğmeleri 11. adımda). Üretim yeni sürüm kaydıdır (PDF ve Word birlikte); yanıttaki
// `uyarilar` basım uyarılarıdır, belgeye basılmaz. Basım GET'tir ve `BASIM` satırını okuma rolünde de
// yazar; ön yüz HEAD göndermez (sunucu 405). Dosya adı sunucunundur (`Content-Disposition`); okunamazsa
// aynı kalıp (belge + üretim günü) ön yüzde kurulur.

import { api } from "../../lib/api";
import { dosyaAdi } from "../../lib/download";
import { formatDateTime } from "../../lib/format";

export type EvrakKodu = "E01" | "E02" | "E03";
export type EvrakBicimi = "pdf" | "docx";

/** `GET terms/<pk>/documents/` satırı: dönemin geçerli kaydı (kişisiz). */
export interface EvrakKaydi {
  id: number;
  kod: EvrakKodu;
  ad: string;
  surum: number;
  durum: string;
  uretim_zamani: string;
  bicimler: string[];
}

/** Üretimin yanıtı: kayıt ve basım uyarıları (belgeye basılmaz). */
export interface EvrakUretimi {
  evrak: EvrakKaydi;
  uyarilar: string[];
}

/**
 * Kaydedilen dosya adının belge kısmı (backend `gorev_evraki.DOSYA_ADI_KOKLERI`; sözlük §3 "Kaydedilen
 * dosya adı"): sunucunun adı okunamazsa yedek ad bununla ve üretim günüyle kurulur.
 */
const DOSYA_KOKLERI: Record<EvrakKodu, string> = {
  E01: "Yönetim-Kurulu-Görev-Bölümü-Karar-Taslağı",
  E02: "Denetleme-Kurulu-Görev-Bölümü-Tutanağı",
  E03: "Temsilci-Görevlendirme-Çizelgesi",
};

/** Sunucunun adı yoksa: belge kökü + üretim günü (Europe/Istanbul) + uzantı. */
export function evrakYedekDosyaAdi(kayit: EvrakKaydi, bicim: EvrakBicimi): string {
  return dosyaAdi(
    [DOSYA_KOKLERI[kayit.kod], formatDateTime(kayit.uretim_zamani).slice(0, 10)],
    bicim,
  );
}

export const evrakApi = {
  liste: (donem: number): Promise<EvrakKaydi[]> =>
    api.get<EvrakKaydi[]>(`/oab/terms/${donem}/documents/`),

  uret: (donem: number, kod: EvrakKodu): Promise<EvrakUretimi> =>
    api.post<EvrakUretimi>(`/oab/terms/${donem}/documents/${kod.toLowerCase()}/`),

  /** Kaydın dosyası (basım; `BASIM` satırı yazılır). */
  dosya: (id: number, bicim: EvrakBicimi) => api.getDosya(`/oab/documents/${id}/${bicim}/`),
};
