// Birlik Dönemi ve geçiş kurulumu API istemcisi — backend `apps/oab/views.py` (`TermListCreateView`,
// `TermDetailView`, `TermCancelView`, `TransitionView` ve geçiş uçları) ile BİREBİR (plan F1c-11).
// Gövde ve yanıt anahtarları sunucununkidir (snake_case). Kişi adı bu uçların hiçbirinde yoktur: üyelik
// ve kişi adları kendi uçlarından (`gecis-kurulumu/api`, `kisiler/birlikKisileriApi`) okunur.

import { api } from "../../lib/api";

/** Birlik döneminin durumu (backend `TermStatus`). */
export type DonemDurumu = "HAZIRLIK" | "ACIK" | "KAPANISTA" | "KAPANDI" | "IPTAL";

/** Birlik dönemi (`OabTermSerializer`). Kural sürümü salt okunurdur (plan F1c kararları). */
export interface BirlikDonemi {
  id: number;
  name: string;
  school_year: number;
  start_date: string | null;
  end_date: string | null;
  status: DonemDurumu;
  program_start_date: string | null;
  /** Dönemi açan genel kurul; geçiş kurulumunda açılan dönemde null. */
  opened_by_assembly: number | null;
  /** "Geçiş kurulumu tamamlandı" işaretinin günü (genel kurulsuz dönemde). */
  transition_completed_on: string | null;
  kural_paketi: { paket: string; rev: number };
  /** Dönemin dondurulmuş kural kopyası özetini tutuyor mu? (D7: tutmuyorsa dönem salt okur.) */
  kural_kopyasi_tutuyor: boolean;
}

/** Kadro ve açılış uyarısı satırı (kaydedilmez, gerekçe istemez): metin atıflıdır. */
export interface AtifliUyari {
  metin: string;
  atif: string;
  durum: string;
}

/** İlk birlik döneminin açılışı (`POST /oab/terms/`; tasarım §7.9 adım 1). */
export interface IlkDonemGovdesi {
  name: string;
  school_year: number;
  /** Son olağan genel kurulun günü (dönem başı). */
  start_date: string;
  /** Programa başlama günü; verilmezse bugün. */
  program_start_date?: string | null;
}

export interface IlkDonemYaniti extends BirlikDonemi {
  /** Görev süresi uyarıları (md. 12/2, 14/2): son genel kuruldan bu yana bir yıl geçmişse. */
  uyarilar: AtifliUyari[];
}

/** Geçiş kurulumunun durumu (backend `gecis.yol_haritasi_durumu`). */
export type GecisDurumu = "BASLAMADI" | "SURUYOR" | "TAMAMLANDI" | "GEREKMIYOR";

/** Açık adımların anahtarları (sırasıyla). */
export type GecisAdimi = "donem" | "kurul" | "sayac_beyani" | "karar_defteri" | "tamamla";

/** Karar defterinin tasdik makamı (backend `BookCertifier`). */
export type TasdikMakami = "NOTER" | "IL_ILCE_MEM";

/** Karar defterinin geçiş kaydı (`KararDefteriSerializer`). */
export interface KararDefteri {
  id: number;
  status: "KULLANIMDA" | "DOLDU" | "ARSIVDE" | "IPTAL";
  certified_by: TasdikMakami | "";
  certified_on: string | null;
  certification_no: string;
  page_count: number | null;
  opened_on: string | null;
  last_no_before_program: number | null;
  last_page_before_program: number | null;
}

/** Geçiş döneminin açık uyum satırı (sayaç "bilinmiyor" beyanı, defter tasdiki); kişisizdir. */
export interface GecisUyumSatiri {
  id: number;
  tur: "EKSIK" | "SAPMA" | "TAKVIM";
  /** Konunun modeli (`oab.OabPerson`, `oab.OrganMembership`, `oab.OfficialBook`) ve kimliği. */
  konu_turu: string;
  konu: string;
  metin: string;
  atif: string;
  gerekceli: boolean;
  /** Seçilme sayacı satırında beyanın alanı (`yk`, `dk_baskanlik`); öteki satırda boş. */
  sayac_alani: "yk" | "dk_baskanlik" | "";
}

/** `GET /oab/transition/`. */
export interface GecisOzeti {
  state: GecisDurumu;
  open_steps: GecisAdimi[];
  donem: BirlikDonemi | null;
  karar_defteri: KararDefteri | null;
  gorev_suresi_uyarilari: AtifliUyari[];
  uyum_satirlari: GecisUyumSatiri[];
}

export const birlikDonemiApi = {
  donemler: (): Promise<BirlikDonemi[]> => api.get<BirlikDonemi[]>("/oab/terms/"),

  donem: (id: number): Promise<BirlikDonemi> => api.get<BirlikDonemi>(`/oab/terms/${id}/`),

  ilkDonemiAc: (govde: IlkDonemGovdesi): Promise<IlkDonemYaniti> =>
    api.post<IlkDonemYaniti>("/oab/terms/", govde),

  /** Yanlış girilmiş geçiş döneminin iptali (gerekçe şifreli saklanır). */
  donemiIptalEt: (id: number, cancelReason: string): Promise<BirlikDonemi> =>
    api.post<BirlikDonemi>(`/oab/terms/${id}/cancel/`, { cancel_reason: cancelReason }),

  gecis: (): Promise<GecisOzeti> => api.get<GecisOzeti>("/oab/transition/"),
};
