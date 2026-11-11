// Geçiş kurulumunun yazma uçları ve organ üyeliklerinin okuması — backend `apps/oab/views.py`
// (`TransitionInheritedView`, `TransitionElectionCountsView`, `TransitionDecisionBookView`,
// `TransitionDecisionBookCancelView`, `TransitionCompleteView`, `MembershipListCreateView`,
// `MembershipCancelView`) ile BİREBİR (tasarım §7.9 adım 2-4; plan F1c 8. adımın kararı ve notları).
// Durum okuması `birlik-donemi/api`'dedir. Kaydı yalnız program yöneticisi yazar; işaretten sonra her
// yazma 409 `gecis_kapali` döner. Devralınan üyeliğin iptali genel iptal ucundandır.

import { api } from "../../lib/api";
import type { BirlikDonemi, KararDefteri, TasdikMakami } from "../birlik-donemi/api";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";

/** Organ (backend `OrganType`; "YK" ve "DK" kod değeridir, kullanıcı metnine çıkmaz). */
export type Organ = "YK" | "DK" | "TEMSILCI" | "ALIM_KOMISYONU" | "DIVAN";
export type KoltukTuru = "ASIL" | "YEDEK";
export type KoltukGrubu = "VELI" | "OGRETMEN" | "";
export type UyelikGorevi =
  "BASKAN" | "BASKAN_YARDIMCISI" | "MUHASIP" | "SEKRETER" | "KATIP" | "UYE";
export type SecimKanali =
  | "GENEL_KURUL"
  | "OGRETMENLER_KURULU"
  | "MEM_GOREVLENDIRME"
  | "YK_KARARI"
  | "OKUL_IDARESI"
  | "KENDILIGINDEN";
export type UyelikDurumu = "ADAY" | "SECILDI" | "DUSTU" | "IPTAL";

/** Temsil türleri (backend `Representation`; adlar modelin görünen adlarıdır). */
export const TEMSIL_TURU_TR = {
  ODUL_DISIPLIN_KURULU: "Okul öğrenci ödül ve disiplin kurulu",
  DAVRANIS_DEGERLENDIRME_KURULU: "Öğrenci davranışlarını değerlendirme kurulu",
  SOSYAL_ETKINLIKLER_KURULU: "Okul sosyal etkinlikler kurulu",
  KONTENJAN_KOMISYONU: "Kontenjan belirleme komisyonu",
  RPD_YURUTME_KOMISYONU: "Rehberlik ve psikolojik danışma hizmetleri yürütme komisyonu",
  TASIMACI_TESPIT_KOMISYONU: "Taşımacıyı tespit komisyonu",
  MUHAMMEN_BEDEL_KOMISYONU: "Muhammen bedel tespit komisyonu",
  KIRALAMA_IHALE_KOMISYONU: "Kiralama ihale komisyonu",
  PAY_DAGITIM_KOMISYONU: "Pay dağıtım komisyonu",
  KAMPUS_YONETIMI: "Kampüs yönetimi",
  KANTIN_DENETIM_KOMISYONU: "Kantin denetim komisyonu",
  DIGER: "Diğer",
} as const;
export type TemsilTuru = keyof typeof TEMSIL_TURU_TR;

/** Organ üyeliği (`OrganMembershipSerializer`; kadroya girmeyen alanlar burada da yoktur). */
export interface OrganUyeligi {
  id: number;
  term: number;
  person: number;
  /** Çözülmüş ad; okunamazsa null. */
  person_name: string | null;
  organ: Organ;
  role: UyelikGorevi;
  seat_type: KoltukTuru;
  seat_group: KoltukGrubu;
  seat_order: number | null;
  elected_by: SecimKanali;
  source: "PROGRAM" | "DEVRALINAN";
  evidence_note: string;
  representation: TemsilTuru | "";
  mem_approval_no: string;
  status: UyelikDurumu;
  start_date: string | null;
  end_date: string | null;
  bozuk_alanlar?: string[];
}

/** Devralınan kayıt (`DevralinanSerializer`): organ `TEMSILCI` ise `representation` zorunludur. */
export interface DevralinanGovdesi {
  organ: "YK" | "DK" | "TEMSILCI";
  person: number;
  seat_type?: KoltukTuru;
  seat_group?: KoltukGrubu;
  role?: UyelikGorevi;
  elected_by?: SecimKanali;
  representation?: TemsilTuru | "";
  start_date?: string | null;
  seat_order?: number | null;
  evidence_note?: string;
  mem_approval_no?: string;
  gerekce?: string;
}

/**
 * Bir kişinin seçilme sayısı beyanı: alan VERİLMEZSE değişmez, `null` "bilinmiyor"dur, sayı karar
 * defterinden sayılandır (tasarım §7.9 adım 3).
 */
export interface SayacBeyani {
  person: number;
  yk?: number | null;
  dk_baskanlik?: number | null;
}

export interface SayacBeyaniGovdesi {
  beyanlar: SayacBeyani[];
  /** "Bilinmiyor" beyanının tek (toplu) gerekçesi. */
  gerekce?: string;
  /** Verilmiş beyanın düzeltme gerekçesi. */
  duzeltme_gerekcesi?: string;
}

export interface SayacBeyaniYaniti {
  kisiler: BirlikKisisi[];
  bilinmeyen_sayisi: number;
}

export interface KararDefteriGovdesi {
  last_no_before_program: number | null;
  last_page_before_program: number | null;
  certified_by?: TasdikMakami | "";
  certified_on?: string | null;
  certification_no?: string;
  page_count?: number | null;
  opened_on?: string | null;
  gerekce?: string;
}

export const gecisApi = {
  /** Dönemin bir organdaki üyelikleri (iptal ve düşmüş kayıtlar dahil; sıra sunucunun). */
  uyelikler: (donem: number, organ: Organ): Promise<OrganUyeligi[]> =>
    api.get<OrganUyeligi[]>(`/oab/memberships/?term=${donem}&organ=${organ}`),

  devralinanEkle: (govde: DevralinanGovdesi): Promise<OrganUyeligi> =>
    api.post<OrganUyeligi>("/oab/transition/inherited/", govde),

  /** Devralınan üyeliğin iptali (genel iptal ucu; servis yalnız program yöneticisine açar). */
  uyeligiIptalEt: (id: number, cancelReason: string): Promise<OrganUyeligi> =>
    api.post<OrganUyeligi>(`/oab/memberships/${id}/cancel/`, { cancel_reason: cancelReason }),

  sayacBeyani: (govde: SayacBeyaniGovdesi): Promise<SayacBeyaniYaniti> =>
    api.post<SayacBeyaniYaniti>("/oab/transition/election-counts/", govde),

  kararDefteriKaydet: (govde: KararDefteriGovdesi): Promise<KararDefteri> =>
    api.post<KararDefteri>("/oab/transition/decision-book/", govde),

  kararDefteriniIptalEt: (id: number, cancelReason: string): Promise<KararDefteri> =>
    api.post<KararDefteri>(`/oab/transition/decision-book/${id}/cancel/`, {
      cancel_reason: cancelReason,
    }),

  tamamla: (): Promise<BirlikDonemi> => api.post<BirlikDonemi>("/oab/transition/complete/"),
};
