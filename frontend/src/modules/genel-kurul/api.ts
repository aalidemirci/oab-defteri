// Genel Kurul ekranının API istemcisi — backend `apps/oab/views_genel_kurul.py` (genel kurul listesi,
// planlama, sihirbazın yazma uçları, müdür ve Denetleme Kurulu yolları, dosya ekleri, genel kurul evrakı,
// adlı çıktı, dönem geçişi) ve `serializers_genel_kurul.py` ile BİREBİR (plan F2 §6.1; 11. adımın arka
// yüzü 11a, ekranı 11b). Gövde ve yanıt anahtarları sunucununkidir (snake_case).
//
// KİŞİSEL VERİ (altın kural 5): yanıtlar kişisizdir; yalnız divanın, adayların ve tutanağın okuyanlarının
// birlik kişisi adları çözülmüş gelir. Veli adı yalnız katılım işaretleri penceresinin okumasında (erişim
// günlüğüne yazılır) ve veli adlı çıktının dosyasındadır; ikisi de yalnız program yöneticisine açıktır,
// ön yüz onları saklamaz (bellekte, pencere açıkken). Gerekçe metinleri yanıtta yoktur.
//
// Uyarı + gerekçe (altın kural 3): gerekçe gövdede `gerekce` alanıyla gider; sunucu yalnız gerektiğinde
// ister (400 `gerekce_gerekli`; ortak bileşen `uyum/UyariGerekce`).

import { api } from "../../lib/api";
import type { IndirilenDosya } from "../../lib/api";
import type { BirlikDonemi } from "../birlik-donemi/api";
import type { OrganUyeligi } from "../gecis-kurulumu/api";

export type GenelKurulTuru = "OLAGAN" | "OLAGANUSTU";

/** Genel kurulun durumu (backend `AssemblyStatus`; tasarım §5.2.3, §7.1). */
export type GenelKurulDurumu =
  | "PLANLANDI"
  | "CAGRILDI"
  | "ILAN_EDILDI"
  | "YETER_SAYI_YOK"
  | "YAPILDI"
  | "TUTANAK_TAMAM"
  | "IPTAL";

/** Çağıran (backend `AssemblyCaller`). */
export type Cagiran =
  | "YONETIM_KURULU"
  | "OKUL_MUDURU"
  | "MUDUR_YENI_OKUL"
  | "DENETLEME_KURULU"
  | "UYE_BASVURUSU"
  | "BASKAN_VEYA_MUDUR_13_8"
  | "MUDUR_25_2";

export type Toplanti = "BIRINCI" | "IKINCI";

/** Gündem maddesinin türü (backend `AgendaItemKind`). */
export type GundemTuru =
  | "ACILIS"
  | "DIVAN_SECIMI"
  | "YK_FAALIYET_RAPORU"
  | "DK_RAPORU"
  | "IBRA"
  | "TAHMINI_BUTCE"
  | "YETKILENDIRME"
  | "SECIM_YK"
  | "SECIM_DK"
  | "ONERILER"
  | "DILEK"
  | "KAPANIS"
  | "DIGER";

export type GundemSonucu = "KABUL" | "RET" | "GORUSULDU";
export type IbraSonucu = "EDILDI" | "EDILMEDI" | "GORUSULMEDI";

/** Katılımın türe göre dağılımı (backend `AttendanceKind`). */
export type KatilimTuru = "VELI_KURSIYER" | "OGRETMEN" | "IDARECI" | "HAYIRSEVER" | "DIGER";
export const KATILIM_TURLERI: readonly KatilimTuru[] = [
  "VELI_KURSIYER",
  "OGRETMEN",
  "IDARECI",
  "HAYIRSEVER",
  "DIGER",
];

/** Liste satırı (kişisiz, serbest metin yok). */
export interface GenelKurulOzeti {
  id: number;
  kind: GenelKurulTuru;
  status: GenelKurulDurumu;
  term: number | null;
  opens_term: number | null;
  called_by: Cagiran | "";
  called_by_role: string;
  first_meeting_at: string | null;
  second_meeting_at: string | null;
  venue: string;
  held_at_meeting: Toplanti | "";
  quorum_required: number | null;
}

/** `GET assemblies/`. */
export interface GenelKurulListesi {
  kayitlar: GenelKurulOzeti[];
  acik_donem: number | null;
  /** Açık dönemin kural sürümü genel kurul kurallarını taşımıyor (U1): planlamadan önce güncellenir. */
  kural_surumu_guncellenmeli: boolean;
  planlama_bilgileri: string[];
}

/** Kullanıcı eki (kişisiz üst bilgi; özgün ad yalnız ekin satırında görünür). */
export interface Ek {
  id: number;
  ad: string | null;
  tur: string;
  boyut: number;
  yukleme_zamani: string | null;
}

export interface GundemMaddesi {
  id: number;
  order: number;
  kind: GundemTuru;
  title: string;
  notes: string | null;
  added_by_vote: boolean;
  removed_by_vote: boolean;
  change_votes_for: number | null;
  change_votes_against: number | null;
  result: GundemSonucu | "";
  result_text: string | null;
  votes_for: number | null;
  votes_against: number | null;
  present_count: number | null;
  /** Maddenin dosya eki belgesi (E34, E28, E33); eklenmeyen maddede boş. */
  dosya_eki_belgesi: string;
  ekler: Ek[];
}

/** İlan (genel kurulun duyurusu ve kanal kanıt günleri). */
export interface Ilan {
  id: number;
  kind: string;
  status: string;
  distributed_written_on: string | null;
  posted_board_on: string | null;
  removed_board_on: string | null;
  published_web_on: string | null;
  ekler: Ek[];
}

export interface TutanakKisisi {
  id: number;
  ad: string | null;
}

export interface Tutanak {
  yk_report_reader: TutanakKisisi | null;
  dk_report_reader: TutanakKisisi | null;
  budget_presenter: TutanakKisisi | null;
  unaudited_documents_note: string | null;
  handed_to_new_yk_on: string | null;
}

export interface KatilimDuzeltmesi {
  id: number;
  meeting: Toplanti;
  field: string;
  old_value: number | null;
  new_value: number;
  corrected_at: string | null;
}

/** Geçişin kural özeti satırı (kişisiz; atıflı). */
export interface KuralOzeti {
  kural: string;
  atif: string;
  mesaj: string;
  durum: "eksik" | "uyari";
  paket: string;
  rev: number;
}

export type CagriYolu = "genel" | "mudur" | "dk";

/** Oturumdaki rolün bu kayıtta yazabildikleri (sunucu kapısından; ön yüz rol adıyla dallanmaz). */
export interface OturumEylemleri {
  cagiranlar: { called_by: Cagiran; yol: CagriYolu }[];
  uretilebilir_belgeler: string[];
}

/** `GET assemblies/<pk>/`. */
export interface GenelKurul extends GenelKurulOzeti {
  call_reason: string | null;
  call_decision: number | null;
  call_document: number | null;
  call_audit_report: number | null;
  /** Çağrı yazısının sahibi olan rol (müdür ya da Denetleme Kurulu); yoksa null. */
  cagri_sahibi: string | null;
  member_application_count: number | null;
  member_count_declared: number | null;
  announced_on: string | null;
  second_announced_on: string | null;
  student_count_snapshot: number | null;
  quorum_base: number | null;
  quorum_multiplier: number | null;
  first_attendee_count: number | null;
  second_attendee_count: number | null;
  attendance_by_kind: Partial<Record<KatilimTuru, number>>;
  parent_students_count: number | null;
  observer_count: number | null;
  discharge_yk: IbraSonucu | "";
  discharge_dk: IbraSonucu | "";
  discharge_yk_votes_for: number | null;
  discharge_yk_votes_against: number | null;
  discharge_yk_present_count: number | null;
  discharge_dk_votes_for: number | null;
  discharge_dk_votes_against: number | null;
  discharge_dk_present_count: number | null;
  cancel_reason: string | null;
  rule_warnings: KuralOzeti[];
  gundem: GundemMaddesi[];
  ilanlar: Ilan[];
  divan: OrganUyeligi[];
  adaylar: (OrganUyeligi & { votes: number | null })[];
  tutanak: Tutanak | null;
  katilim_duzeltmeleri: KatilimDuzeltmesi[];
  katilim_isareti_sayilari: Record<Toplanti, number>;
  bilgiler: string[];
  oturum: OturumEylemleri;
}

/** Geçişin yanıtı: güncel ayrıntı, bu geçişin uyarıları ve bilgi satırları. */
export interface GecisSonucu {
  genel_kurul: GenelKurul;
  uyarilar: KuralOzeti[];
  bilgiler: string[];
}

export interface MaddeSonucu extends GecisSonucu {
  madde: GundemMaddesi;
}

/** Gerekçe alanı (ortak bileşenin `ek()`'i). */
export interface GerekceEki {
  gerekce?: string;
}

export interface PlanlaGovdesi extends GerekceEki {
  kind: GenelKurulTuru;
  first_meeting_at: string;
  venue?: string;
}

export interface CagriGundemMaddesi {
  title: string;
  kind?: GundemTuru;
}

export interface CagriGovdesi extends GerekceEki {
  called_by?: Cagiran | "";
  call_reason?: string;
  gundem?: CagriGundemMaddesi[];
  member_application_count?: number | null;
  member_count_declared?: number | null;
  call_document?: number | null;
}

export interface DenetimRaporuGovdesi {
  kind: "ARA" | "NIHAI";
  report_date: string;
  md6_violation_found: boolean;
  irregularity_found?: boolean;
}

export interface DkCagriGovdesi extends GerekceEki {
  call_reason: string;
  gundem: CagriGundemMaddesi[];
  rapor: DenetimRaporuGovdesi;
}

export interface IlanKanallari {
  distributed_written_on: string | null;
  posted_board_on: string | null;
  published_web_on: string | null;
}

export interface KatilimGovdesi extends GerekceEki {
  attendee_count: number;
  attendance_by_kind?: Partial<Record<KatilimTuru, number>>;
  parent_students_count?: number | null;
  observer_count?: number | null;
}

export interface KatilimDuzeltmeGovdesi extends GerekceEki {
  toplanti: Toplanti;
  degerler: Record<string, number>;
  justification: string;
}

/** Katılım işaretleri penceresinin satırı (veli adı; yalnız program yöneticisi, erişim günlüğü). */
export interface IsaretSatiri {
  id: number;
  veli: string | null;
  isaretli: boolean;
  oteki_toplanti: boolean;
  baska_isaret: boolean;
}

export interface KatilimIsaretleri {
  toplanti: Toplanti;
  siniflar: { sinif: string; satirlar: IsaretSatiri[] }[];
}

export interface KararGovdesi {
  result?: GundemSonucu | null;
  votes_for?: number | null;
  votes_against?: number | null;
  present_count?: number | null;
  result_text?: string;
}

export interface AdayOyu {
  uyelik: number;
  votes: number | null;
  secildi: boolean;
  seat_order?: number | null;
}

export interface SecimGovdesi extends GerekceEki {
  adaylar: AdayOyu[];
  liste?: boolean | null;
  acik_oy?: boolean | null;
  result_text?: string;
}

export interface IbraOylamasi {
  votes_for: number;
  votes_against: number;
  present_count?: number | null;
}

export interface IbraGovdesi {
  yk: IbraOylamasi | null;
  dk: IbraOylamasi | null;
  unaudited_documents_note?: string;
}

export interface AdayGovdesi extends GerekceEki {
  person: number;
  organ: "YK" | "DK";
  seat_type: "ASIL" | "YEDEK";
  seat_group?: "VELI" | "OGRETMEN" | "";
}

export interface TutanakGovdesi {
  yk_report_reader?: number | null;
  dk_report_reader?: number | null;
  budget_presenter?: number | null;
  handed_to_new_yk_on?: string | null;
}

/** Dönem geçişinin önizlemesi ve onayı (U32). */
export interface DonemGecisi {
  genel_kurul: number;
  yeni_donem: BirlikDonemi;
  baslangic: string;
  kapanacak: BirlikDonemi | null;
  kapanacak_bitis: string | null;
  engeller: string[];
}

/** Genel kurul evrakının kataloğu (tasarım §9.5). */
export interface KatalogSatiri {
  kod: string;
  ad: string;
  konu: string;
  bicimler: string[];
  kipler: ("KISISIZ" | "ADLI")[];
  /** Sunucunun biçim adları (`DocumentFormat`: büyük harf). */
  adli_bicimler: ("PDF" | "DOCX" | "XLSX")[];
  toplantili: boolean;
  muhatapli: boolean;
  ureten_roller: string[];
  okuma_satiri: string;
  uretilebilir: boolean;
  uretilemez_nedeni: string;
}

export interface MuhatapOnerisi {
  idare: string;
  birim: string;
}

export interface Katalog {
  belgeler: KatalogSatiri[];
  muhatap_onerileri: Record<"IL" | "ILCE", MuhatapOnerisi>;
  varsayilan_muhatap: "IL" | "ILCE";
}

/** Genel kurulun geçerli evrak kaydı (veli adlı kayıt dosyasızdır: yalnız tür, tarih, satır sayısı). */
export interface GkEvrakKaydi {
  id: number;
  kod: string;
  ad: string;
  kip: "KISISIZ" | "ADLI" | "";
  toplanti: Toplanti | "";
  surum: number;
  durum: string;
  uretim_zamani: string;
  bicimler: string[];
  kisi_listesi: boolean;
  satir_sayisi: number | null;
}

export interface EvrakUretimGovdesi {
  kip?: "KISISIZ" | "ADLI" | "";
  toplanti?: Toplanti | "";
  muhatap_secimi?: "IL" | "ILCE" | "";
  muhatap_idare?: string | null;
  muhatap_birim?: string;
}

export interface GkEvrakUretimi {
  evrak: GkEvrakKaydi;
  uyarilar: string[];
}

export type GkBicim = "pdf" | "docx" | "xlsx" | "html";

const G = "/oab/assemblies";

export const genelKurulApi = {
  liste: (): Promise<GenelKurulListesi> => api.get<GenelKurulListesi>(`${G}/`),
  planla: (govde: PlanlaGovdesi): Promise<GecisSonucu> => api.post<GecisSonucu>(`${G}/`, govde),
  ayrinti: (id: number): Promise<GenelKurul> => api.get<GenelKurul>(`${G}/${id}/`),
  toplantiBilgisi: (
    id: number,
    govde: { first_meeting_at: string; venue?: string } & GerekceEki,
  ): Promise<GecisSonucu> => api.patch<GecisSonucu>(`${G}/${id}/`, govde),

  // Çağrı: üç yol (sunucu çağırana göre daraltır; seçenekler `oturum.cagiranlar`'dan).
  cagir: (id: number, govde: CagriGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/call/`, govde),
  mudurCagrisi: (id: number, govde: CagriGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/principal-call/`, govde),
  dkCagrisi: (id: number, govde: DkCagriGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/audit-board-call/`, govde),
  cagriYazisi: (id: number, kayit: number): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/call-document/`, { kayit }),

  // İlan ve davet.
  ilan: (
    id: number,
    govde: { kanallar: IlanKanallari | null; second_meeting_at: string | null } & GerekceEki,
  ): Promise<GecisSonucu> => api.post<GecisSonucu>(`${G}/${id}/announcement/`, govde),
  ikinciIlan: (
    id: number,
    govde: { second_meeting_at: string; kanallar: IlanKanallari | null } & GerekceEki,
  ): Promise<GecisSonucu> => api.post<GecisSonucu>(`${G}/${id}/second-announcement/`, govde),
  kanit: (ilan: number, govde: IlanKanallari & GerekceEki): Promise<GecisSonucu> =>
    api.put<GecisSonucu>(`/oab/announcements/${ilan}/evidence/`, govde),
  ilanEki: (ilan: number, dosya: File): Promise<Ek> => {
    const form = new FormData();
    form.append("file", dosya);
    return api.postForm<Ek>(`/oab/announcements/${ilan}/attachments/`, form);
  },

  // Toplantılar, iptal, katılım.
  birinciToplanti: (id: number, govde: KatilimGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/first-meeting/`, govde),
  ikinciToplanti: (id: number, govde: KatilimGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/second-meeting/`, govde),
  iptalEt: (id: number, cancelReason: string): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/cancel/`, { cancel_reason: cancelReason }),
  katilimDuzelt: (id: number, govde: KatilimDuzeltmeGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/attendance-corrections/`, govde),
  katilimIsaretleri: (id: number, toplanti: Toplanti): Promise<KatilimIsaretleri> =>
    api.get<KatilimIsaretleri>(`${G}/${id}/attendance-marks/?toplanti=${toplanti}`),
  isaretle: (
    id: number,
    govde: { toplanti: Toplanti; isaretle: number[]; kaldir: number[] },
  ): Promise<{ toplanti: Toplanti; isaret_sayisi: number }> =>
    api.post(`${G}/${id}/attendance-marks/`, govde),

  // Gündem, karar, seçim, ibra, dosya ekleri.
  gundemeEkle: (
    id: number,
    govde: {
      title: string;
      kind?: GundemTuru;
      sira?: number | null;
      change_votes_for?: number | null;
      change_votes_against?: number | null;
    } & GerekceEki,
  ): Promise<MaddeSonucu> => api.post<MaddeSonucu>(`${G}/${id}/agenda/`, govde),
  gundemSirasi: (id: number, sira: number[]): Promise<GecisSonucu> =>
    api.put<GecisSonucu>(`${G}/${id}/agenda-order/`, { sira }),
  gundemdenCikar: (
    madde: number,
    govde: { change_votes_for?: number | null; change_votes_against?: number | null } & GerekceEki,
  ): Promise<MaddeSonucu> => api.post<MaddeSonucu>(`/oab/agenda-items/${madde}/removal/`, govde),
  kararSonucu: (madde: number, govde: KararGovdesi): Promise<MaddeSonucu> =>
    api.post<MaddeSonucu>(`/oab/agenda-items/${madde}/result/`, govde),
  secim: (madde: number, govde: SecimGovdesi): Promise<MaddeSonucu> =>
    api.post<MaddeSonucu>(`/oab/agenda-items/${madde}/election/`, govde),
  secimIptal: (madde: number, cancelReason: string): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`/oab/agenda-items/${madde}/election-cancel/`, {
      cancel_reason: cancelReason,
    }),
  ibra: (madde: number, govde: IbraGovdesi): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`/oab/agenda-items/${madde}/discharge/`, govde),
  dosyaEki: (madde: number, dosya: File, dk = false): Promise<Ek> => {
    const form = new FormData();
    form.append("file", dosya);
    const yol = dk ? "audit-board-attachment" : "attachments";
    return api.postForm<Ek>(`/oab/agenda-items/${madde}/${yol}/`, form);
  },
  /** Ekin dosyası (indirme adı sunucunun: belge adı + gün; özgün ad dosya adına girmez). */
  ekIndir: (ek: number): Promise<IndirilenDosya> => api.getDosya(`/oab/attachments/${ek}/`),

  // Divan, adaylar, tutanak, dönem geçişi.
  divan: (
    id: number,
    govde: { baskan: number; katip: number } & GerekceEki,
  ): Promise<GecisSonucu> => api.post<GecisSonucu>(`${G}/${id}/presiding-board/`, govde),
  divanIptal: (id: number, cancelReason: string): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/presiding-board-cancel/`, { cancel_reason: cancelReason }),
  aday: (id: number, govde: AdayGovdesi): Promise<OrganUyeligi> =>
    api.post<OrganUyeligi>(`${G}/${id}/candidates/`, govde),
  tutanak: (id: number, govde: TutanakGovdesi): Promise<GecisSonucu> =>
    api.patch<GecisSonucu>(`${G}/${id}/minutes/`, govde),
  tutanagiTamamla: (id: number, govde: GerekceEki): Promise<GecisSonucu> =>
    api.post<GecisSonucu>(`${G}/${id}/minutes-complete/`, govde),
  donemGecisi: (id: number): Promise<DonemGecisi> =>
    api.get<DonemGecisi>(`${G}/${id}/term-transition/`),
  donemGecisiniOnayla: (id: number): Promise<DonemGecisi> =>
    api.post<DonemGecisi>(`${G}/${id}/term-transition/`),

  // Genel kurul evrakı.
  katalog: (): Promise<Katalog> => api.get<Katalog>("/oab/assembly-documents/catalog/"),
  evrakListesi: (id: number): Promise<GkEvrakKaydi[]> =>
    api.get<GkEvrakKaydi[]>(`${G}/${id}/documents/`),
  evrakUret: (id: number, kod: string, govde: EvrakUretimGovdesi): Promise<GkEvrakUretimi> =>
    api.post<GkEvrakUretimi>(`${G}/${id}/documents/${kod.toLowerCase()}/`, govde),
  /** Denetleme Kurulunun çağrı yazısı (E05, md. 14/5 kolu; ⁵). */
  dkCagriYazisi: (id: number, toplanti: Toplanti | ""): Promise<GkEvrakUretimi> =>
    api.post<GkEvrakUretimi>(`${G}/${id}/documents/e05/audit-board/`, { toplanti }),
  /** Veli adlı çıktı (tek istekte üretilir ve verilir; saklanmaz; R9). */
  adliEvrak: (
    id: number,
    kod: string,
    bicim: "pdf" | "docx" | "xlsx",
    toplanti: Toplanti | "",
  ): Promise<IndirilenDosya> =>
    api.postDosya(`${G}/${id}/documents/${kod.toLowerCase()}/named/`, { bicim, toplanti }),
  /** Kaydın dosyası (basım; `BASIM` satırı yazılır). */
  evrakDosyasi: (kayit: number, bicim: GkBicim): Promise<IndirilenDosya> =>
    api.getDosya(`/oab/documents/${kayit}/${bicim}/`),
};
