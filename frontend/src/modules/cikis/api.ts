// Çık — arayüzden düzenli kapanış (tasarım §4.2-4, §5.10-18, TB13).
//
// Pencerenin çarpısı da programı kapatır (T6, tasarım §4.5); pencere süslemesi
// olmayan Linux masaüstünde programdan çıkmanın yolu bu uçtur. Backend
// `apps/okul/views_app.py::AppQuitView` ile BİREBİR: görevli kipinde gövdede
// yönetici parolası; parolasız istek 403 `cikis_parolasi_gerekli`; yanlış parola
// 400 "Parola hatalı."; kilitli, yönetici kipi ve "yeniden başlat" durumunda
// parolasız. Başarı 202.

import { api } from "../../lib/api";

/** Görevli kipinde parolasız istek (backend `views_app.py`). */
export const CIKIS_PAROLASI_GEREKLI = "cikis_parolasi_gerekli";

/** Program masaüstü penceresinde çalışmıyor (geliştirme sunucusu). */
export const CIKIS_KULLANILAMIYOR = "cikis_kullanilamiyor";

export const cikisApi = {
  /**
   * Düzenli kapanışı başlatır. Etkinlik başlığı gönderilmez: çıkış yönetici
   * kipini canlı tutmamalıdır. Parola yalnız gövdede gider.
   */
  cik: (password?: string) =>
    api.post<{ durum: string }>("/app/quit/", password ? { password } : {}, { etkinlik: false }),
};
