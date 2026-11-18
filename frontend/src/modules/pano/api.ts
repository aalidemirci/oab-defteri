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

/** Takvim satırının "Yapıldı" işareti (F2 12. adım; satırın işini yapan rol, yetenek `takvim_isareti`). */
export function takvimYapildiYolu(satir: number): string {
  return `/oab/compliance-items/${satir}/done/`;
}

/** İş kalemlerinin kodları (`isler`). */
export type IsKodu =
  | "YK_GOREV_BOLUMU"
  | "DK_GOREV_BOLUMU"
  | "GECIS_ADIMI"
  | "KURAL_SURUMU"
  | "YEDEK_CAGRISI"
  | "KADRO"
  | "HESAP_ONERISI"
  | "YARIM_TASLAK"
  // F2: genel kurul süreleri (plan F2 §6.3; backend `pano` "F2 kalemleri").
  | "GK_OLAGAN"
  | "GK_YENI_OKUL"
  | "GK_ILAN"
  | "GK_IKINCI_TOPLANTI"
  | "MUDUR_YAZISI"
  | "IBRA_BILDIRIMI"
  | "TEFBIS_GIRISI"
  | "DONEM_ONAYI";

/** Bilgi kalemlerinin kodları (`bilgiler`): bant olarak gösterilir. */
export type BilgiKodu = "KURAL_KOPYASI_DOGRULANAMADI" | "DONEM_YOK";

/** Bir pano kalemi (kişisiz). */
export interface PanoKalemi {
  /** `EKSIK`: açık uyum satırı; `VERI_SORUMLUSU`: okul kartının tamamlanacağı (yalnız program
   * yöneticisi; F2 12. adım). İkisi de "tamamlanacaklar"dadır. */
  kod: IsKodu | BilgiKodu | "EKSIK" | "VERI_SORUMLUSU";
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
  /** Kodun kişisiz ayrıntısı (geçiş adımı, kural sürümü güncellemesinin iki sürümü, hesap önerisinin
   * türü ve rolü, taslağın bağlamı, kurul);
   * `sayi`: aynı önerilerin tek kaleme toplandığı sayı (hesap önerisi, Denetleme Kurulunun yedek
   * çağrısı; kişisiz sayım). F2: `kurul` genel kurulun kimliği (kalem `?kurul=` ile ayrıntısına
   * götürür; kişi kimliği değildir), `durum`, `son_gun` (ISO), `ilan_gun`, `sure_gun` (kural
   * paketinin değerleri), `toplanti`, `eksik` (kanal belirteçleri, virgülle), `tur` (müdürün
   * yazısı), `tarihli`, `yukumluluk` (takvim satırı), `baslangic` (ISO), `ilan_atif` (cümledeki ilan
   * süresinin atfı, md. 9/3), `olaganustu` (1: olağanüstü genel kurulun ikinci toplantısı, A-1),
   * `satir` (takvim satırının kimliği: "Yapıldı" işareti için; kişi kimliği değildir), `salt_okur`
   * (takvim kalemi: satırın kendi döneminin kural kopyası doğrulanamıyor, D7; "Yapıldı" çizilmez,
   * sunucu da 409 `donem_salt_okur` verir). İbra edilmedi bildirimi ve TEFBİS kalemleri süresizdir
   * (`vade` null: mevzuatta süre yok). */
  ek: Record<string, string | number | boolean>;
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

/** Yıllık iş takvimi (`GET terms/<pk>/annual-calendar/`; E14'ün kaynağı, kişisiz; F2 11b). */
export interface YillikTakvim {
  donem: number;
  bolumler: string[];
  kural_satirlari: { tarih: string; is: string; kural: string; atif: string }[];
  plan_satirlari: { tarih: string; is: string; kaynak: string }[];
  uyarilar: string[];
}

export const panelApi = {
  sonOturum: (): Promise<SonOturumOzeti> =>
    api.get<SonOturumOzeti>(SON_OTURUM_YOLU, { etkinlik: false }),
  kontrolEttim: (): Promise<SonOturumOzeti> => api.post<SonOturumOzeti>(SON_OTURUM_YOLU, {}),
  kalemler: (): Promise<PanoYaniti> => api.get<PanoYaniti>(PANO_YOLU, { etkinlik: false }),
  yillikTakvim: (donem: number): Promise<YillikTakvim> =>
    api.get<YillikTakvim>(`/oab/terms/${donem}/annual-calendar/`),
  takvimYapildi: (satir: number, doneOn: string): Promise<{ id: number; done_on: string }> =>
    api.post<{ id: number; done_on: string }>(takvimYapildiYolu(satir), { done_on: doneOn }),
};
