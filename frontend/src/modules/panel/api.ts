// Genel Bakış (pano) uçlarının istemcisi.
//
// Son oturum kartı (T15; tasarım §4.2 adım 3, §13 D4): masaüstü kabuğu önceki
// oturumun temiz kapanış işaretini bulamadıysa kart gösterilir. Sorgu kullanıcı
// eylemi değildir (`X-OD-Etkinlik` gitmez); "Kontrol ettim" eylemdir.

import { api } from "../../lib/api";

export interface SonOturumOzeti {
  unexpected_shutdown: boolean;
  /** Bu oturumun başlangıcı (ISO 8601): "son oturum" bundan öncekidir. */
  process_started_at: string;
}

export const SON_OTURUM_YOLU = "/dashboard/last-session/";

export const panelApi = {
  sonOturum: (): Promise<SonOturumOzeti> =>
    api.get<SonOturumOzeti>(SON_OTURUM_YOLU, { etkinlik: false }),
  kontrolEttim: (): Promise<SonOturumOzeti> => api.post<SonOturumOzeti>(SON_OTURUM_YOLU, {}),
};
