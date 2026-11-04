// Çık — arayüzden düzenli kapanış (tasarım §4.2, §4.5).
//
// Pencerenin çarpısı da programı kapatır (T6, tasarım §4.5); pencere süslemesi
// olmayan Linux masaüstünde programdan çıkmanın yolu bu uçtur. Backend
// `apps/okul/views_app.py::AppQuitView` ile BİREBİR: HER oturum durumunda (açık,
// kilitli, kurulum, kayıp güvenlik dosyası, "yeniden başlat") parolasızdır. Aile
// iskeletinin görevli kipindeki parola dalı (`cikis_parolasi_gerekli`) görevli kipiyle
// kalktı (tasarım §12.B). Başarı 202.

import { api } from "../../lib/api";

/** Program masaüstü penceresinde çalışmıyor (geliştirme sunucusu). */
export const CIKIS_KULLANILAMIYOR = "cikis_kullanilamiyor";

export const cikisApi = {
  /**
   * Düzenli kapanışı başlatır. Etkinlik başlığı gönderilmez: çıkış oturumu canlı
   * tutmamalıdır. Gövde boştur (parola yoktur).
   */
  cik: () => api.post<{ durum: string }>("/app/quit/", {}, { etkinlik: false }),
};
