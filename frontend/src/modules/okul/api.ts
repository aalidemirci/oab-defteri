// `okul` modülü API istemcisi — kurum künyesi/kurulum, ders yılı + dönemler,
// kapalı günler, personel sicili (ayrılış ve birleştirme), toplu içe aktarma (e-Okul
// mutabakatı dahil), veli listesi (yalnız sayılar) ve şablon indirme uçları. Backend
// `apps/okul/{urls,views,serializers}.py` ile BİREBİR. TCKN, cinsiyet, fotoğraf, unvan ve branş
// alanları YOKTUR; veliden yalnız adı-soyadı ve öğrencinin sınıfı alınır (T5), ekrana adı
// gelmez, sınıf başına sayı gelir. Öğrenci sicili, şube kataloğu ve öğrenim seviyeleri F1b 5.
// adımda söküldü (tasarım §5.1 ALMA). OAB'nin işleme envanteri genel tasarım §3.4'tedir.

import { api } from "../../lib/api";
import { unwrap } from "../../lib/pagination";
import type { Paginated } from "../../lib/pagination";

export type { Paginated };

// ---------------------------------------------------------------------------
// Ders yılı
// ---------------------------------------------------------------------------

/** Ders yılı — SchoolYearSerializer ile birebir (`is_active` salt-okunur). */
export interface SchoolYear {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface SchoolYearCreateBody {
  name: string;
  start_date: string;
  end_date: string;
}

export interface SchoolTerm {
  id: number;
  school_year: number;
  sequence: 1 | 2;
  name: string;
  start_date: string;
  end_date: string;
}

export interface SchoolTermConfigurationBody {
  first_term_end: string;
  second_term_start: string;
}

// ---------------------------------------------------------------------------
// Kapalı günler (resmî tatil, dini bayram, öğrenciye kapalı gün, idari izin)
// ---------------------------------------------------------------------------

/** Backend `HolidayKind` ile birebir. */
export type HolidayKind = "OFFICIAL" | "RELIGIOUS" | "SCHOOL_BREAK" | "OTHER";

/**
 * Tür adları (sözlük): ara tatil ve yarıyıl "öğrenciye kapalı gün" diye ayrı
 * adlandırılır, tek başına "tatil" denmez.
 */
export const HOLIDAY_KIND_TR: Record<HolidayKind, string> = {
  SCHOOL_BREAK: "Öğrenciye kapalı gün",
  OFFICIAL: "Resmî tatil",
  RELIGIOUS: "Dini bayram",
  OTHER: "İdari izin / diğer",
};

/** Kapalı gün kaydı — HolidaySerializer ile birebir. Tek günde başlangıç = bitiş. */
export interface Holiday {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  kind: HolidayKind;
  /** Dini bayram tarihi hesapla bulunmuş, Diyanet takvimiyle henüz kesinleşmemiş. */
  is_estimated: boolean;
}

/** Elle ekleme gövdesi — `is_estimated` gönderilmez (elle girilen tarih kesindir). */
export interface HolidayCreateBody {
  name: string;
  start_date: string;
  end_date: string;
  kind: HolidayKind;
}

/** `POST /holidays/seed/` sonucu. */
export interface HolidaySeedResult {
  year: number;
  /** Yeni eklenen kayıt sayısı. */
  created: number;
  /** Zaten var olduğu için atlanan kayıt sayısı. */
  skipped: number;
  /** false → programda bu yılın dini bayram tarihleri yok; elle girilmeli. */
  religious_available: boolean;
}

// ---------------------------------------------------------------------------
// Kurulum sihirbazı / kurum künyesi
// ---------------------------------------------------------------------------

/**
 * Sihirbaz adımları, sırasıyla — backend `services/setup.py::SETUP_STEPS` ile BİREBİR:
 * program yöneticisi hesabı + kurtarma anahtarı → okul bilgileri → ders yılı ve kapalı günler.
 */
export type SetupStep = "password" | "school" | "calendar";

export const SETUP_STEPS: readonly SetupStep[] = ["password", "school", "calendar"];

/** Aktif ders yılının özeti (`setup/status/` içinde; kişisel veri yok). */
export interface ActiveSchoolYearSummary {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  /** İki dönemin tarihleri tanımlı mı? (kurulumu tamamlamanın koşulu) */
  terms_ready: boolean;
}

/**
 * Başlangıç Yol Haritası'nda kullanıcının işaretlediği maddeler (backend tek kaynak:
 * `ROADMAP_MANUAL_ITEMS`). Parola paylaşımı maddesi yoktur: parola paylaşılmaz.
 */
export type RoadmapManualItem = "kurtarma_zarfi";

export interface RoadmapState {
  /** İşaretlenen madde → işaretlendiği gün (ISO). */
  marks: Partial<Record<RoadmapManualItem, string>>;
  /** Bütün maddeler tamamlanınca kullanıcı kartı gizleyebilir. */
  hidden: boolean;
}

/**
 * `GET /setup/status/` — sihirbaz kapısı, adım durumları, sicil sayaçları ve yol
 * haritası. Masaüstü sağlık denetiminin de ucudur: hafiftir ve KİŞİSEL VERİ İÇERMEZ.
 */
export interface SetupStatus {
  setup_completed: boolean;
  /** İlk program yöneticisi hesabı kurulu mu? Kurulu değilse sihirbaz ilk adımdan açılır. */
  password_set: boolean;
  /**
   * Kurtarma anahtarının saklandığı doğrulandı mı? 1. adım ancak hesap kurulu VE anahtar
   * doğrulanmışsa tamamdır; kurulumu önceden tamamlanmış programda yanlışsa yol haritası ve
   * Güvenlik ekranı uyarır.
   */
  recovery_key_confirmed: boolean;
  school_name: string;
  /**
   * Okul kartının zorunlu alanları tamam mı? (okul adı, il, ilçe, kurum kodu, kademe, öğrenci
   * mevcudu ve tarihi, yerleşim türü, kantin ve personel çalıştırma biçimi, demirbaş onayı —
   * backend `missing_school_fields`). Yol haritasının `okul_karti` maddesi de buna bakar.
   */
  school_info_complete: boolean;
  has_active_school_year: boolean;
  active_school_year: ActiveSchoolYearSummary | null;
  /** Eksik adımlar, sırasıyla (hepsi tamamsa boş) — backend kapısıyla aynı hesap. */
  missing_steps: SetupStep[];
  /** Personel sicilindeki kayıt sayısı (öğrenci mevcudu okul kartındadır, `SchoolConfig`). */
  personnel_count: number;
  /** Aktif ders yılıyla kesişen "öğrenciye kapalı gün" kaydı sayısı. */
  school_break_count: number;
  roadmap: RoadmapState;
}

/** Okulun kademesi — backend `SchoolLevel` ile birebir (değer adları ve sıra). */
export type SchoolLevel = "OKUL_ONCESI" | "ILKOKUL" | "ORTAOKUL" | "ORTAOGRETIM";

/** Kademe adları; anahtar sırası backend `SchoolLevel` sırasıdır (`levels` bu sırayla gider). */
export const SCHOOL_LEVEL_TR: Record<SchoolLevel, string> = {
  OKUL_ONCESI: "Okul öncesi",
  ILKOKUL: "İlkokul",
  ORTAOKUL: "Ortaokul",
  ORTAOGRETIM: "Ortaöğretim (lise)",
};

/** Yerleşim türü — backend `SettlementType` ile birebir (md. 17/1-a-2; kural paketinin koşulu). */
export type SettlementType = "BUYUKSEHIR" | "IL_MERKEZI_BUYUKSEHIR_DEGIL" | "DIGER";

export const SETTLEMENT_TYPE_TR: Record<SettlementType, string> = {
  BUYUKSEHIR: "Büyükşehir statüsündeki il",
  IL_MERKEZI_BUYUKSEHIR_DEGIL: "Büyükşehir statüsünde olmayan il merkezi",
  DIGER: "Büyükşehir statüsünde olmayan ilde, il merkezi dışında",
};

/** Kantin işletme biçimi — backend `CanteenMode` ile birebir (md. 17/1-a-1, 17/1-b-1, 23/3). */
export type CanteenMode = "KIRAYA_VERILIYOR" | "BIRLIKCE_ISLETILIYOR" | "KANTIN_YOK";

export const CANTEEN_MODE_TR: Record<CanteenMode, string> = {
  KIRAYA_VERILIYOR: "Kiraya veriliyor",
  BIRLIKCE_ISLETILIYOR: "Birlikçe işletiliyor",
  KANTIN_YOK: "Kantin ve benzeri yer yok",
};

/** Personel çalıştırma biçimi — backend `StaffingMode` ile birebir (K3, md. 6/1-d). */
export type StaffingMode = "DOGRUDAN_ISVEREN" | "HIZMET_ALIMI" | "CALISTIRMIYOR";

export const STAFFING_MODE_TR: Record<StaffingMode, string> = {
  DOGRUDAN_ISVEREN: "Birlik doğrudan işveren",
  HIZMET_ALIMI: "Hizmet alımıyla",
  CALISTIRMIYOR: "Personel çalıştırmıyor",
};

/**
 * Kurum künyesi (okul kartı) — `SchoolConfigSerializer` ile birebir: evrak antedi ve birliğin
 * hesaplarının okul bilgisi buradan çözülür (`setup_completed` salt-okunur). Bütün alanlar
 * kişisizdir. Seçilmemiş seçim alanı `""`, girilmemiş sayı ve tarih `null`dır.
 */
export interface SchoolConfig {
  school_name: string;
  province: string;
  district: string;
  principal_name: string;
  /** MEB kurum kodu: boş ya da altı rakam. */
  institution_code: string;
  /** Kademeler: tekrarsız, `SchoolLevel` sırasıyla. */
  levels: SchoolLevel[];
  /** Öğrenci mevcudu (0..99999); tarihiyle birlikte girilir (md. 9/2, 9/6, 21/3). */
  student_count: number | null;
  /** Mevcudun tarihi (ISO): sayının alındığı gün. */
  student_count_as_of: string | null;
  settlement_type: SettlementType | "";
  canteen_mode: CanteenMode | "";
  staffing_mode: StaffingMode | "";
  /** Okul bir eğitim kampüsünde mi? (md. 2/1, 13/7) */
  in_campus: boolean;
  /** Yeni açılan okulun açılış tarihi (ISO; isteğe bağlı, md. 9/1). */
  opened_on: string | null;
  /** "Bu bilgisayar okul demirbaşıdır" onayı (kurulumda zorunlu). */
  demirbas_onayi: boolean;
  /** Bilgisayarın demirbaş no'su (isteğe bağlı). */
  demirbas_no: string;
  /**
   * Veri sorumlusu ve iletişim bilgisi (serbest metin, isteğe bağlı; KVKK md. 10/1-a, E04).
   * Personel ve veli listesi aktarım ekranlarının aydınlatma metni buradan dolar.
   */
  data_controller_text: string;
  setup_completed: boolean;
}

/** PUT gövdesi kısmi olabilir — backend MERGE semantiği uygular. */
export type SchoolConfigBody = Partial<Omit<SchoolConfig, "setup_completed">>;

// ---------------------------------------------------------------------------
// Personel sicili
// ---------------------------------------------------------------------------

/**
 * Çözülemeyen şifreli alanlar (tasarım §13 D48; backend `CorruptFieldsMixin`): kilit
 * açıkken çözülemeyen alan `null` gelir ve adı bu listede durur (değer taşımaz). Ad ya
 * da soyad bozuksa türeyen `full_name` de `null`dır. Ekran "okunamadı" yazar
 * (`kisiler/ortak`). Liste her yanıtta vardır; test kalıpları atlayabilsin diye isteğe bağlı.
 */
export interface BozukAlanlar {
  bozuk_alanlar?: string[];
}

/** Görev türü — backend `MemberKind` ile birebir (tasarım §5.1; ekran adı "Görev türü"). */
export type MemberKind = "OGRETMEN" | "YONETICI" | "DIGER";

/**
 * Sözlük "Personelin türü": "öğretmen" · "yönetici" · "diğer personel" ("personel" tek başına
 * öğretmen anlamında kullanılmaz; "üye" denmez, diğer personel birliğin üyesi değildir).
 */
export const MEMBER_KIND_TR: Record<MemberKind, string> = {
  OGRETMEN: "Öğretmen",
  YONETICI: "Yönetici",
  DIGER: "Diğer personel",
};

/**
 * Personel sicili — PersonnelSerializer ile birebir (`full_name` türetilmiş).
 * Unvan ve branş bu programda YOKTUR (branş, küçük okulda öğretmeni kişiye bağlar).
 * `is_active`, `left_at` ve `leave_candidate_since` salt okunurdur: ayrılış
 * `leavePersonnel` ya da Ayrılış Havuzu kararıyla yapılır; kayıt silinmez.
 */
export interface Personnel extends BozukAlanlar {
  id: number;
  /** Şifreli; çözülemezse null (`BozukAlanlar`). */
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  member_kind: MemberKind;
  is_active: boolean;
  /** Ayrılış tarihi (ISO); aktif kişide null. */
  left_at: string | null;
  /** Ayrılış havuzuna giriş tarihi (ISO); doluysa ayrılış kararı bekliyor. */
  leave_candidate_since: string | null;
}

export interface PersonnelWriteBody {
  first_name: string;
  last_name: string;
  member_kind?: MemberKind;
}

// ---------------------------------------------------------------------------
// Ayrılış Havuzu — e-Okul aktarımı kimseyi ayırmaz ve silmez; listede bulunmayan
// aktif kişi burada karar bekler (backend `views_pool.py`).
// ---------------------------------------------------------------------------

/** Kişiyi havuza ekleyen aktarım: dosya adı (yapıştırılan listede boş) ve gün (ISO). */
export interface LeavePoolRun {
  id: number;
  file_name: string;
  date: string;
}

/**
 * Eşleşme gerekçesi — backend `name_match.MatchReason` ile birebir (§13 D30).
 * "Adı aynı" adaşı da yakalar; kullanıcı bunu ancak gerekçeyi görürse anlar.
 */
export type SimilarReason = "ayni_ad_soyad" | "ad_ayni_soyad_farkli" | "yazim_farki";

/** Aday satırında ve onay diyaloğunda yazılan gerekçe (eksik kod derlemede yakalanır). */
export const SIMILAR_REASON_TR: Record<SimilarReason, string> = {
  ayni_ad_soyad: "ad ve soyadı birebir aynı",
  ad_ayni_soyad_farkli: "adı aynı, soyadı farklı",
  yazim_farki: "ad-soyadında küçük yazım farkı",
};

/** Bilinmeyen kod (eski yanıt) ekranı boş bırakmasın: kısa ve dürüst karşılık. */
export function benzerlikGerekcesi(reason: string): string {
  return SIMILAR_REASON_TR[reason as SimilarReason] ?? "ad benzerliği";
}

/** Havuzdaki kişiyle "olası aynı kişi" olan, sonradan açılmış kayıt. */
export interface LeavePoolSimilar {
  id: number;
  full_name: string;
  member_kind: MemberKind;
  /** Adayın sicile eklendiği gün (ISO) — onay diyaloğunda ayırt edici bilgi. */
  created_on: string;
  reason: SimilarReason;
}

/** Havuzdaki personel — LeavePoolPersonnelSerializer ile birebir. */
export interface LeavePoolPersonnel extends BozukAlanlar {
  id: number;
  /** Şifreli addan türer; çözülemezse null (`BozukAlanlar`). */
  full_name: string | null;
  member_kind: MemberKind;
  leave_candidate_since: string;
  run: LeavePoolRun | null;
  /** Birleştirme adayları: havuzdaki kişi kaynak, aday hedef (`mergePersonnel`). */
  similar: LeavePoolSimilar[];
}

/** `GET /leave-pool/?summary=true` — yalnız sayı (Genel Bakış kartı). */
export interface LeavePoolSummary {
  personnel_count: number;
}

/** `GET /leave-pool/` — havuzdaki öğretmen ve diğer personel, TR sıralı. */
export interface LeavePool extends LeavePoolSummary {
  personnel: LeavePoolPersonnel[];
}

/** Bir kişi türü için karar: ayrıldı olarak işaretle / aktif kalsın (kimlikler). */
export interface LeavePoolDecision {
  leave?: number[];
  keep?: number[];
}

export interface LeavePoolResolveBody {
  personnel?: LeavePoolDecision;
}

/** Karar sonucu: uygulanan sayılar + havuzda kalan sayı. */
export interface LeavePoolResolveResult extends LeavePoolSummary {
  personnel_left: number;
  personnel_kept: number;
}

export interface PersonnelListParams {
  search?: string;
  onlyActive?: boolean;
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// İçe aktarma (Excel dosyası — e-Okul .xls ya da şablon .xlsx — VEYA pano metni)
// ---------------------------------------------------------------------------

/** Rapordaki tek satır sorunu (uyarı veya atlanan satır). */
export interface ImportIssue {
  row_number: number;
  field: string;
  issue: string;
  raw_value: string;
}

interface ImportReportBase {
  file_hash: string;
  file_name: string;
  total_rows: number;
  processed: number;
  /** Aynı içerik daha önce aktarılmış — UYARIDIR, engel değil. */
  already_imported: boolean;
  /** Önizleme (true) hiçbir şey yazmaz; commit false döner. */
  dry_run: boolean;
  warnings: ImportIssue[];
  skipped: ImportIssue[];
}

/** Havuza eklenecek (listede olmayan) aktif kişi — ad yalnız bu yanıtta gelir. */
export interface PoolPersonnel {
  id: number;
  full_name: string;
}

/**
 * "Olası aynı kişi": ada göre eşleşmeyen yeni satır ↔ listede olmayan kayıt.
 * `new_id` yalnız aktarımdan sonra dolar (önizlemede null); birleştirme
 * `mergePersonnel(existing_id, new_id)` ile yapılır (ya da Ayrılış Havuzu'ndan).
 */
export interface SimilarPair {
  row_number: number;
  row_name: string;
  existing_id: number;
  existing_name: string;
  new_id: number | null;
  /** Çiftin neden kurulduğu (§13 D30); eski raporlarda boş olabilir. */
  reason: SimilarReason | "";
}

/** Aktarım kimseyi ayırmaz: listede olmayan aktif personel ayrılış havuzuna girer. */
export interface PersonnelImportReport extends ImportReportBase {
  created_personnel: number;
  updated_personnel: number;
  unchanged_personnel: number;
  reactivated_personnel: number;
  pool_added_personnel: number;
  pool_removed_personnel: number;
  similar_pair_count: number;
  pool_added: PoolPersonnel[];
  similar_pairs: SimilarPair[];
}

/** Aktarım raporu — bugün yalnız personel (öğrenci aktarımı F1b 5. adımda söküldü). */
export type ImportReport = PersonnelImportReport;

/** İçe aktarma girdisi — dosya yolu (multipart) veya pano metni (JSON). */
export type ImportInput = { file: File } | { text: string };

/** Raporun sayaçlarını tek şekle indirger — rapor bileşeni türden bağımsız kalır. */
export function importCounts(report: ImportReport): {
  created: number;
  updated: number;
  unchanged: number;
  poolAdded: number;
  poolRemoved: number;
} {
  return {
    created: report.created_personnel,
    updated: report.updated_personnel,
    unchanged: report.unchanged_personnel,
    poolAdded: report.pool_added_personnel,
    poolRemoved: report.pool_removed_personnel,
  };
}

/** Şablon dosya adı — kaydetme penceresinde önerilir (backend ile aynı). */
export const PERSONNEL_TEMPLATE_FILENAME = "sablon-personel.xlsx";
export const PARENT_TEMPLATE_FILENAME = "sablon-veli-listesi.xlsx";

// ---------------------------------------------------------------------------
// Veli listesi (T5; genel tasarım §5.1 `ParentRoster`, §8.4) — yanıtlar YALNIZ SAYI taşır
// ---------------------------------------------------------------------------

/** Bir sınıfın satır sayısı (veli listesinin özeti). */
export interface ParentRosterClass {
  student_class: string;
  rows: number;
}

/** `GET parent-roster/`: sınıf başına sayı; ad yoktur. */
export interface ParentRosterSummary {
  total_rows: number;
  class_count: number;
  /** Son uygulanan aktarımın anı (ISO); liste boşsa null. */
  last_import_at: string | null;
  classes: ParentRosterClass[];
}

/** Aktarımda bir sınıfın etkisi: dosyadaki satır ve yerine geçen eski satır sayısı. */
export interface ParentClassImpact {
  student_class: string;
  rows: number;
  replaced_rows: number;
}

/** Aktarılamayan satır: satır no, alan kodu, neden — hücrenin değeri yoktur. */
export interface ParentRowIssue {
  row_number: number;
  field: string;
  issue: string;
}

/** Veli listesi aktarımının raporu (önizleme ve uygulama aynı biçim). */
export interface ParentImportReport {
  file_hash: string;
  file_name: string;
  total_rows: number;
  imported_rows: number;
  class_count: number;
  replaced_rows: number;
  kept_class_count: number;
  kept_rows: number;
  already_imported: boolean;
  dry_run: boolean;
  classes: ParentClassImpact[];
  issues: ParentRowIssue[];
}

/** Veli listesi yalnız dosyayla aktarılır (pano yolu yoktur). */
function parentImportRequest(path: string, file: File): Promise<ParentImportReport> {
  const form = new FormData();
  form.append("file", file);
  return api.postForm<ParentImportReport>(path, form);
}

// ---------------------------------------------------------------------------
// Yardımcılar
// ---------------------------------------------------------------------------

/** Parça yoksa yolu olduğu gibi bırakır (gereksiz "?" üretmez). */
function withQuery(path: string, parts: string[]): string {
  return parts.length > 0 ? `${path}?${parts.join("&")}` : path;
}

/** Düz dizi dönen uçları da sayfalama zarfına indirger (tek tüketim şekli). */
function asPage<T>(data: Paginated<T> | T[]): Paginated<T> {
  return Array.isArray(data)
    ? { count: data.length, next: null, previous: null, results: data }
    : data;
}

/**
 * Dosya yolu multipart (`file`), metin yolu JSON (`text`) — backend tam olarak birini
 * bekler. Mutabakat seçeneği yoktur: listede olmayanlar Ayrılış Havuzu'na girer, karar
 * orada verilir.
 */
function importRequest<R>(path: string, input: ImportInput): Promise<R> {
  if ("file" in input) {
    const form = new FormData();
    form.append("file", input.file);
    return api.postForm<R>(path, form);
  }
  return api.post<R>(path, { text: input.text });
}

export const okulApi = {
  // --- Kurulum sihirbazı ---

  getSetupStatus: (): Promise<SetupStatus> => api.get<SetupStatus>("/setup/status/"),

  getSchoolConfig: (): Promise<SchoolConfig> => api.get<SchoolConfig>("/setup/school-config/"),

  /** Kısmi gövde gönderilebilir — backend MERGE eder (verilmeyen alan korunur). */
  updateSchoolConfig: (body: SchoolConfigBody): Promise<SchoolConfig> =>
    api.put<SchoolConfig>("/setup/school-config/", body),

  /** Eksik adımda 400 `kurulum_eksik` — ileti hangi adımın eksik olduğunu söyler. */
  completeSetup: (): Promise<{ setup_completed: boolean }> =>
    api.post<{ setup_completed: boolean }>("/setup/complete/"),

  /** Yol haritasında elle işaretlenen bir maddeyi işaretler ya da işareti kaldırır. */
  markRoadmapItem: (item: RoadmapManualItem, done: boolean): Promise<RoadmapState> =>
    api.post<RoadmapState>("/setup/roadmap/", { item, done }),

  /** Kartı gizler (yalnız bütün maddeler tamamken) ya da yeniden gösterir. */
  setRoadmapHidden: (hidden: boolean): Promise<RoadmapState> =>
    api.post<RoadmapState>("/setup/roadmap/", { hidden }),

  // --- Ders yılları ---

  /** Ders yıllarını listeler (DRF sayfalı yanıt → düz dizi). */
  listSchoolYears: async (): Promise<SchoolYear[]> => {
    const data = await api.get<Paginated<SchoolYear>>("/school-years/?limit=200");
    return unwrap(data);
  },

  /** Yeni ders yılı oluşturur (pasif doğar; aktivasyon ayrı uçtan). */
  createSchoolYear: (body: SchoolYearCreateBody): Promise<SchoolYear> =>
    api.post<SchoolYear>("/school-years/", body),

  /** Ders yılını aktifleştirir — backend diğerlerini pasifler. */
  activateSchoolYear: (id: number): Promise<SchoolYear> =>
    api.post<SchoolYear>(`/school-years/${id}/activate/`),

  listSchoolTerms: (schoolYearId: number): Promise<SchoolTerm[]> =>
    api.get<SchoolTerm[]>(`/school-years/${schoolYearId}/terms/`),

  configureSchoolTerms: (
    schoolYearId: number,
    body: SchoolTermConfigurationBody,
  ): Promise<SchoolTerm[]> => api.put<SchoolTerm[]>(`/school-years/${schoolYearId}/terms/`, body),

  // --- Kapalı günler ---

  /** Takvim yılıyla KESİŞEN kayıtlar, tarih sırasıyla (yıl verilmezse hepsi). */
  listHolidays: (year?: number): Promise<Holiday[]> =>
    api.get<Holiday[]>(year === undefined ? "/holidays/" : `/holidays/?year=${year}`),

  createHoliday: (body: HolidayCreateBody): Promise<Holiday> =>
    api.post<Holiday>("/holidays/", body),

  deleteHoliday: (id: number): Promise<void> => api.del<void>(`/holidays/${id}/`),

  /** Yılın sabit resmî tatilleri + dini bayramlar; tekrar çağrılınca kopya üretmez. */
  seedHolidays: (year: number): Promise<HolidaySeedResult> =>
    api.post<HolidaySeedResult>("/holidays/seed/", { year }),

  // --- Personel ---

  listPersonnel: async (params: PersonnelListParams = {}): Promise<Paginated<Personnel>> => {
    const parts: string[] = [];
    if (params.search?.trim()) parts.push(`search=${encodeURIComponent(params.search.trim())}`);
    if (params.onlyActive) parts.push("only_active=true");
    if (params.limit !== undefined) parts.push(`limit=${params.limit}`);
    if (params.offset) parts.push(`offset=${params.offset}`);
    const data = await api.get<Paginated<Personnel> | Personnel[]>(withQuery("/personnel/", parts));
    return asPage(data);
  },

  getPersonnel: (id: number): Promise<Personnel> => api.get<Personnel>(`/personnel/${id}/`),

  createPersonnel: (body: PersonnelWriteBody): Promise<Personnel> =>
    api.post<Personnel>("/personnel/", body),

  updatePersonnel: (id: number, body: Partial<PersonnelWriteBody>): Promise<Personnel> =>
    api.patch<Personnel>(`/personnel/${id}/`, body),

  deletePersonnel: (id: number): Promise<void> => api.del<void>(`/personnel/${id}/`),

  /** "Ayrıldı olarak işaretle" — kayıt SİLİNMEZ, ayrılmış kayıt döner. */
  leavePersonnel: (id: number): Promise<Personnel> =>
    api.post<Personnel>(`/personnel/${id}/leave/`),

  /** "Olası aynı kişi": `sourceId` (eski kayıt) `intoId` (yeni kayıt) kaydına birleşir. */
  mergePersonnel: (sourceId: number, intoId: number): Promise<Personnel> =>
    api.post<Personnel>(`/personnel/${sourceId}/merge/`, { into_id: intoId }),

  // --- Ayrılış Havuzu ---

  /** Ayrılış kararı bekleyen öğretmen ve diğer personel (TR sıralı). */
  getLeavePool: (): Promise<LeavePool> => api.get<LeavePool>("/leave-pool/"),

  /** Yalnız sayı — Genel Bakış kartı (kişisel veri gelmez). */
  getLeavePoolSummary: (): Promise<LeavePoolSummary> =>
    api.get<LeavePoolSummary>("/leave-pool/?summary=true"),

  /**
   * Toplu karar (tek işlem): `leave` → ayrıldı olarak işaretle (kayıt kalır),
   * `keep` → aktif kalsın (havuzdan çıkar). Seçilenlerden biri artık havuzda
   * değilse hiçbir karar uygulanmaz (400).
   */
  resolveLeavePool: (body: LeavePoolResolveBody): Promise<LeavePoolResolveResult> =>
    api.post<LeavePoolResolveResult>("/leave-pool/resolve/", body),

  // --- İçe aktarma (önizleme hiçbir şey yazmaz; commit gerçek yazar) ---

  previewPersonnelImport: (input: ImportInput): Promise<PersonnelImportReport> =>
    importRequest<PersonnelImportReport>("/imports/personnel/preview/", input),

  commitPersonnelImport: (input: ImportInput): Promise<PersonnelImportReport> =>
    importRequest<PersonnelImportReport>("/imports/personnel/commit/", input),

  // --- Şablon indirme (xlsx blob) ---

  personnelTemplate: (): Promise<Blob> => api.getBlob("/templates/personnel/"),

  // --- Veli listesi (yalnız program yöneticisi) ---

  getParentRoster: (): Promise<ParentRosterSummary> =>
    api.get<ParentRosterSummary>("/parent-roster/"),

  /** "Veli listesini sil": bütün liste silinir; yanıt silinen satır sayısıdır. */
  deleteParentRoster: (): Promise<{ deleted_rows: number }> =>
    api.del<{ deleted_rows: number }>("/parent-roster/"),

  previewParentImport: (file: File): Promise<ParentImportReport> =>
    parentImportRequest("/imports/parents/preview/", file),

  commitParentImport: (file: File): Promise<ParentImportReport> =>
    parentImportRequest("/imports/parents/commit/", file),

  parentTemplate: (): Promise<Blob> => api.getBlob("/templates/parents/"),
};
