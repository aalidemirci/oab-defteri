// Hakkında → Kişisel Veri: kişisel veri aydınlatma metni (E04; konusu okul kartı) — backend
// `apps/oab/views_genel_kurul.py` `E04DocumentView` ile BİREBİR (plan F2 10. adım). GET her role açıktır
// ve yazmaz: geçerli kayıt, Okul Bilgileri'nde veri sorumlusunun girilip girilmediği ve her basımda
// geçerli basım uyarıları (belgeye basılmaz). POST yeni sürümü üretir (yalnız program yöneticisi);
// veri sorumlusu boşken sunucu 400 döner (üretilmez ve basılmaz). Basım genel indirme ucundadır
// (`evrakApi.dosya`; `BASIM` satırı okuma rolünde de yazılır).

import { api } from "../../lib/api";
import type { EvrakKaydi, EvrakUretimi } from "../evrak/api";

/** `GET /oab/documents/e04/` yanıtı. */
export interface AydinlatmaDurumu {
  /** Geçerli kayıt; hiç üretilmediyse null. */
  evrak: EvrakKaydi | null;
  /** Okul Bilgileri'nde veri sorumlusu girildi mi? Girilmediyse belge üretilmez ve basılmaz. */
  veri_sorumlusu_girildi: boolean;
  /** Her basımda geçerli uyarılar (okul müdürlüğünce teyit edilecekler; belgeye basılmaz). */
  basim_uyarilari: string[];
}

export const aydinlatmaApi = {
  durum: (): Promise<AydinlatmaDurumu> => api.get<AydinlatmaDurumu>("/oab/documents/e04/"),

  uret: (): Promise<EvrakUretimi> => api.post<EvrakUretimi>("/oab/documents/e04/"),
};
