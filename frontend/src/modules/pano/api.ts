// Genel Bakış (pano) uçlarının istemcisi.
//
// Son oturum kartı (T15; tasarım §4.2 adım 3, §13 D4): masaüstü kabuğu önceki
// oturumun temiz kapanış işaretini bulamadıysa kart gösterilir. Sorgu kullanıcı
// eylemi değildir (`X-OD-Etkinlik` gitmez); "Kontrol ettim" eylemdir.
//
// Pano kalemleri (tasarım §7.10; F1c 12. adım) — backend `apps/oab/services/pano.py` ile BİREBİR:
// kalemler sunucuda her okumada kaynaklardan hesaplanır, saklanmaz ve kişisizdir (kod, gün, kural
// paketinin kişisiz iletisi, atıf, götürdüğü ekran). Rol süzmesi sunucudadır; ön yüz rol adıyla
// dallanmaz, görünümü (`gorunum`) yanıttan okur. Okuma kullanıcı eylemi değildir (boşta sayacını
// tazelemez).

import { api } from "../../lib/api";

export interface SonOturumOzeti {
  unexpected_shutdown: boolean;
  /** Bu oturumun başlangıcı (ISO 8601): "son oturum" bundan öncekidir. */
  process_started_at: string;
}

export const SON_OTURUM_YOLU = "/dashboard/last-session/";
export const PANO_YOLU = "/oab/dashboard/";

/** İş kalemlerinin kodları (`isler`). */
export type IsKodu =
  | "YK_GOREV_BOLUMU"
  | "DK_GOREV_BOLUMU"
  | "GECIS_ADIMI"
  | "YEDEK_CAGRISI"
  | "KADRO"
  | "HESAP_ONERISI"
  | "YARIM_TASLAK";

/** Bilgi kalemlerinin kodları (`bilgiler`): bant olarak gösterilir. */
export type BilgiKodu = "KURAL_KOPYASI_DOGRULANAMADI" | "DONEM_YOK";

/** Bir pano kalemi (kişisiz). */
export interface PanoKalemi {
  kod: IsKodu | BilgiKodu | "EKSIK";
  /** Son gün (ISO); süresiz kalemde null. */
  vade: string | null;
  /** Son gün geçti mi (sunucunun günüyle). */
  gecikti: boolean;
  /** Götürdüğü ekran ve sekmesi (`?tab=`). */
  rota: string;
  sekme: string;
  /** Kural paketinin kişisiz iletisi (kadro, yedek çağrısı, tamamlanacak); yoksa boş. */
  metin: string;
  /** Madde atfı ("md. 12/3"); yoksa boş. */
  atif: string;
  /** Kodun kişisiz ayrıntısı (geçiş adımı, hesap önerisinin türü ve rolü, taslağın bağlamı, kurul);
   * `sayi`: aynı önerilerin tek kaleme toplandığı sayı (hesap önerisi, Denetleme Kurulunun yedek
   * çağrısı; kişisiz sayım). */
  ek: Record<string, string | number>;
}

export interface PanoYaniti {
  /** Sunucunun günü (Europe/Istanbul, ISO). */
  bugun: string;
  /** Rolün varsayılan görünümü: veli rollerinde "ay" ("bu ay sizden beklenenler"). */
  gorunum: "ay" | "hafta";
  bilgiler: PanoKalemi[];
  isler: PanoKalemi[];
  tamamlanacaklar: PanoKalemi[];
}

export const panelApi = {
  sonOturum: (): Promise<SonOturumOzeti> =>
    api.get<SonOturumOzeti>(SON_OTURUM_YOLU, { etkinlik: false }),
  kontrolEttim: (): Promise<SonOturumOzeti> => api.post<SonOturumOzeti>(SON_OTURUM_YOLU, {}),
  kalemler: (): Promise<PanoYaniti> => api.get<PanoYaniti>(PANO_YOLU, { etkinlik: false }),
};
