// Organlar ekranının API istemcisi — backend `apps/oab/views.py` (`OrganRosterView`,
// `MembershipListCreateView`, `MembershipDetailView`, `MembershipEligibilityBasisView`,
// `YkDutyAssignmentView`, `DkDutyAssignmentView`, `MembershipSubstituteCall*View`, `MembershipDropView`,
// `MembershipCancelView`, `PurchaseCommitteeCreateView`, `TermMeetingDayView`,
// `TermLinkableDecisionsView`) ile BİREBİR (plan F1c 5-6. adımların uçları, 11. adımın ekranı). Gövde
// ve yanıt anahtarları sunucununkidir. Kadro okuması kişisizdir; kişi adı üyelik satırında çözülmüş
// gelir. Görev alma engelinin DAYANAĞI kadroda yoktur: ayrı uçtan okunur, okuması erişim günlüğüne
// yazılır ve yalnız `gorev_alma_engeli` yeteneğine açıktır (tasarım §4.4.2 ¹¹).

import { api } from "../../lib/api";
import type { AtifliUyari, BirlikDonemi } from "../birlik-donemi/api";
import type { KoltukTuru, OrganUyeligi, SecimKanali } from "../gecis-kurulumu/api";
import type { UyumTuru } from "../uyum/hatalar";

/** Kadrosu okunan organlar (sekmeler); "YK" ve "DK" kod değeridir, kullanıcı metnine çıkmaz. */
export type KadroOrgani = "YK" | "DK" | "ALIM_KOMISYONU";

/** Düşme türü (backend `DropKind`). */
export type DusmeTuru =
  | "OGRENCI_AYRILDI"
  | "DEVAMSIZLIK"
  | "ISTIFA"
  | "BASKA_KURUMDA_GOREV"
  | "OLAGANUSTU_GK_SECIMI"
  | "DIGER";

/** Görev alma engelinin dayanağı (backend `EligibilityBarBasis`; özel nitelikli). */
export type EngelDayanagi = "SUC_12_5_14_7" | "TEK_BIRLIK_12_4";

/** Kadro ekranının üyeliği: geçiş ekranının satırı + kadronun alanları (kişisiz; dayanak YOK). */
export interface Uyelik extends OrganUyeligi {
  votes: number | null;
  promoted_on: string | null;
  promoted_by_decision: number | null;
  representative_decision: number | null;
  drop_kind: DusmeTuru | "";
  eligibility_declared_on: string | null;
  single_birlik_declared_on: string | null;
  expertise_required: boolean;
  /** Görev alma engelinin hükmü (var ya da yok; dayanak ayrı uçtadır). */
  eligibility_bar: "VAR" | "YOK";
  eligibility_bar_found_on: string | null;
  retained_until_assembly: boolean;
  external_assignment_start: string | null;
  external_assignment_end: string | null;
}

/** Kayıttan hesaplanan öneri ya da hatırlatma (saklanmaz, gerekçe istemez; metin kişisizdir). */
export interface UyelikOnerisi {
  uyelik: number;
  tur: "DUSURME" | "YEDEK_CAGRISI" | "HATIRLATMA";
  metin: string;
  gun: string | null;
  drop_kind: DusmeTuru | "";
}

/** Üyeliğin açık uyum satırı, oturumdaki rolün görünümüyle (engel satırı role göre süzülür). */
export interface UyelikUyumSatiri {
  id: number;
  uyelik: number;
  tur: UyumTuru;
  metin: string;
  atif: string;
  gerekceli: boolean;
}

/** Seçilme sayacı: programın kayıtları ve programdan önceki beyan (`null`: bilinmiyor). */
export interface SecilmeSayaci {
  uyelik: number;
  program: number;
  beyan: number | null;
}

/** `GET terms/<pk>/roster/<organ>/`. */
export interface Kadro {
  organ: KadroOrgani;
  gorevdeki_asillar: Uyelik[];
  bekleyen_yedekler: Uyelik[];
  kadro: { asil: number; yedek: number };
  kadro_uyarilari: AtifliUyari[];
  oneriler: UyelikOnerisi[];
  uyum_satirlari: UyelikUyumSatiri[];
  secilme_sayaclari: SecilmeSayaci[];
}

/** Gerekçe isteyen yazmaların ortak alanı (ortak "uyarı + gerekçe" bileşeni ekler). */
interface Gerekceli {
  gerekce?: string;
}

/** Denetleme Kurulunun öğretmen koltuğuna seçilmiş üye (genel kurul dışı kanal; doğrudan seçilmiş). */
export interface OgretmenUyeGovdesi extends Gerekceli {
  term: number;
  person: number;
  organ: "DK";
  seat_type: KoltukTuru;
  seat_group: "OGRETMEN";
  elected_by: Extract<SecimKanali, "OGRETMENLER_KURULU" | "MEM_GOREVLENDIRME">;
  start_date: string | null;
  seat_order: number | null;
  evidence_note: string;
  mem_approval_no: string;
}

/** Üyeliğin kişisiz ayrıntıları (PATCH; yalnız gönderilen alanlar değişir). */
export interface UyelikGuncellemesi {
  seat_order?: number | null;
  mem_approval_no?: string;
  eligibility_declared_on?: string | null;
  single_birlik_declared_on?: string | null;
  external_assignment_start?: string | null;
  external_assignment_end?: string | null;
}

export interface KatilimSatiri {
  membership: number;
  present: boolean;
  excused: boolean;
}

/** Yönetim kurulunun görev bölümü: verilen görevler (en az biri), toplantı ve katılım. */
export interface YkGorevBolumuGovdesi extends Gerekceli {
  held_at: string;
  place: string;
  katilim: KatilimSatiri[];
  baskan?: number;
  baskan_yardimcisi?: number;
  muhasip?: number;
  sekreter?: number;
}

/** Denetleme Kurulunun görev bölümü ve denetim planı. */
export interface DkGorevBolumuGovdesi extends Gerekceli {
  held_at: string;
  place: string;
  katilim: KatilimSatiri[];
  baskan: number;
  denetim_plani: string[] | null;
}

export interface GorevBolumuYaniti {
  toplanti: number;
  karar: number;
  karar_durumu: string;
  uyelikler: Uyelik[];
}

export interface DusmeGovdesi extends Gerekceli {
  drop_kind: DusmeTuru;
  end_date: string | null;
  dropped_reason: string;
  ertele: boolean;
}

export interface YkYedekCagrisiGovdesi extends Gerekceli {
  promoted_on: string | null;
  promoted_by_decision: number | null;
}

export interface EngelGovdesi {
  eligibility_bar: "VAR" | "YOK";
  eligibility_bar_basis: EngelDayanagi | "";
  eligibility_bar_found_on: string | null;
}

/** Görev alma engelinin dayanağının okuması (erişim günlüğüne yazılır). */
export interface EngelDayanagiYaniti {
  eligibility_bar: "VAR" | "YOK";
  /** Okunamayan değerde null. */
  eligibility_bar_basis: EngelDayanagi | null;
  eligibility_bar_found_on: string | null;
}

export interface AlimKomisyonuGovdesi {
  term: number;
  person: number;
  expertise_required: boolean;
  start_date: string | null;
}

/** Bağlanabilecek (kabul edilmiş ya da deftere işlenmiş) yönetim kurulu kararı; metni dönmez. */
export interface BaglanabilirKarar {
  id: number;
  kind: string;
  status: "KABUL_EDILDI" | "DEFTERE_ISLENDI";
  decision_no: number | null;
  page_no: number | null;
  decision_date: string | null;
  toplanti_gunu: string | null;
}

const UYELIK = "/oab/memberships/";

export const organlarApi = {
  kadro: (donem: number, organ: KadroOrgani): Promise<Kadro> =>
    api.get<Kadro>(`/oab/terms/${donem}/roster/${organ}/`),

  /** Organın bütün üyelikleri (aday, seçilmiş, düşmüş, iptal; sıra sunucunun). */
  uyelikler: (donem: number, organ: KadroOrgani): Promise<Uyelik[]> =>
    api.get<Uyelik[]>(`${UYELIK}?term=${donem}&organ=${organ}`),

  ogretmenUyeEkle: (govde: OgretmenUyeGovdesi): Promise<Uyelik> => api.post<Uyelik>(UYELIK, govde),

  guncelle: (id: number, govde: UyelikGuncellemesi): Promise<Uyelik> =>
    api.patch<Uyelik>(`${UYELIK}${id}/`, govde),

  iptalEt: (id: number, cancelReason: string): Promise<Uyelik> =>
    api.post<Uyelik>(`${UYELIK}${id}/cancel/`, { cancel_reason: cancelReason }),

  dusur: (id: number, govde: DusmeGovdesi): Promise<Uyelik> =>
    api.post<Uyelik>(`${UYELIK}${id}/drop/`, govde),

  ykYedekCagir: (id: number, govde: YkYedekCagrisiGovdesi): Promise<Uyelik> =>
    api.post<Uyelik>(`${UYELIK}${id}/substitute-call/yk/`, govde),

  dkYedekCagir: (id: number, promotedOn: string | null): Promise<Uyelik> =>
    api.post<Uyelik>(`${UYELIK}${id}/substitute-call/dk/`, { promoted_on: promotedOn }),

  engelYaz: (id: number, govde: EngelGovdesi): Promise<unknown> =>
    api.put<unknown>(`${UYELIK}${id}/eligibility-basis/`, govde),

  /** Dayanağı okur: okuma erişim günlüğüne yazılır (yalnız düğmeyle, kendiliğinden okunmaz). */
  engelDayanagi: (id: number): Promise<EngelDayanagiYaniti> =>
    api.get<EngelDayanagiYaniti>(`${UYELIK}${id}/eligibility-basis/`),

  ykGorevBolumu: (donem: number, govde: YkGorevBolumuGovdesi): Promise<GorevBolumuYaniti> =>
    api.post<GorevBolumuYaniti>(`/oab/terms/${donem}/duty-assignment/yk/`, govde),

  dkGorevBolumu: (donem: number, govde: DkGorevBolumuGovdesi): Promise<GorevBolumuYaniti> =>
    api.post<GorevBolumuYaniti>(`/oab/terms/${donem}/duty-assignment/dk/`, govde),

  alimKomisyonuEkle: (govde: AlimKomisyonuGovdesi): Promise<Uyelik> =>
    api.post<Uyelik>("/oab/purchase-committee/", govde),

  /** Yönetim kurulunun aylık toplantı günü (serbest metin; boş metin siler). */
  toplantiGunu: (donem: number, metin: string): Promise<BirlikDonemi> =>
    api.put<BirlikDonemi>(`/oab/terms/${donem}/meeting-day/`, { yk_meeting_day_rule: metin }),

  baglanabilirKararlar: (donem: number): Promise<BaglanabilirKarar[]> =>
    api.get<BaglanabilirKarar[]>(`/oab/terms/${donem}/linkable-decisions/`),
};
