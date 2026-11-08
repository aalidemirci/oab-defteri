// Okul kartının form modeli ve zorunlu alan denetimi — kurulum sihirbazının 2. adımı ve
// Ayarlar → Okul Bilgileri AYNI formu ve AYNI kuralı kullanır (`OkulKartiAlanlari`). Küme
// backend'dekiyle aynıdır: `services/setup.py::missing_school_fields` (kurulumu tamamlama
// kapısı) ve `SchoolConfigSerializer` (bir kez girilen zorunlu alan sonradan boşaltılamaz).
// İletiler backend'le BİREBİR aynıdır; biri değişirse öteki de değişmeli.
//
// Formda sayı alanı metin olarak tutulur (kullanıcının yazdığı hâliyle), gövdede tam sayıya
// çevrilir. Metin alanları gövdede baştan ve sondan kırpılır (backend de kırpar). Mevcudun
// tarihi kayıtta boşsa formun varsayılanı bugündür (kullanıcı kararı 07.11.2026: "sayının
// alındığı gün, varsayılan bugün").

import { todayIso } from "../../lib/format";
import { SCHOOL_LEVEL_TR } from "./api";
import type {
  CanteenMode,
  SchoolConfig,
  SchoolConfigBody,
  SchoolLevel,
  SettlementType,
  StaffingMode,
} from "./api";

/** Öğrenci mevcudunun üst sınırı (backend kısıtıyla aynı). */
export const MEVCUT_EN_COK = 99999;

export interface OkulFormu {
  okulAdi: string;
  il: string;
  ilce: string;
  mudur: string;
  kurumKodu: string;
  kademeler: SchoolLevel[];
  /** Öğrenci mevcudu, yazıldığı gibi (gövdede tam sayıya çevrilir). */
  mevcut: string;
  /** Mevcudun tarihi (ISO yyyy-aa-gg) ya da "". */
  mevcutTarihi: string;
  yerlesim: SettlementType | "";
  kantin: CanteenMode | "";
  personel: StaffingMode | "";
  kampus: boolean;
  /** Okulun açılış tarihi (ISO) ya da "" (isteğe bağlı, boşaltılabilir). */
  acilis: string;
  demirbasOnayi: boolean;
  demirbasNo: string;
  /** Veri sorumlusu (isteğe bağlı serbest metin; aydınlatma metninde görünür). */
  veriSorumlusu: string;
}

/** Kademeler `SchoolLevel` sırasıyla (backend sırası); tekrar ve tanınmayan değer atılır. */
const KADEME_SIRASI = Object.keys(SCHOOL_LEVEL_TR) as SchoolLevel[];

export function kademeleriSirala(kademeler: readonly SchoolLevel[]): SchoolLevel[] {
  return KADEME_SIRASI.filter((k) => kademeler.includes(k));
}

/** Boş form (ilk açılış); mevcudun tarihi bugündür. */
export function bosOkulFormu(): OkulFormu {
  return {
    okulAdi: "",
    il: "",
    ilce: "",
    mudur: "",
    kurumKodu: "",
    kademeler: [],
    mevcut: "",
    mevcutTarihi: todayIso(),
    yerlesim: "",
    kantin: "",
    personel: "",
    kampus: false,
    acilis: "",
    demirbasOnayi: false,
    demirbasNo: "",
    veriSorumlusu: "",
  };
}

/** Kayıttan form; mevcudun tarihi kayıtta yoksa bugün. */
export function kayittanForma(c: SchoolConfig): OkulFormu {
  return {
    okulAdi: c.school_name,
    il: c.province,
    ilce: c.district,
    mudur: c.principal_name,
    kurumKodu: c.institution_code,
    kademeler: kademeleriSirala(c.levels),
    mevcut: c.student_count === null ? "" : String(c.student_count),
    mevcutTarihi: c.student_count_as_of ?? todayIso(),
    yerlesim: c.settlement_type,
    kantin: c.canteen_mode,
    personel: c.staffing_mode,
    kampus: c.in_campus,
    acilis: c.opened_on ?? "",
    demirbasOnayi: c.demirbas_onayi,
    demirbasNo: c.demirbas_no,
    veriSorumlusu: c.data_controller_text,
  };
}

/**
 * Yazılan mevcut → tam sayı. Boş → `null`; tam sayı değilse ya da aralık dışındaysa `NaN`.
 * Binlik noktayla yazılan sayı ("1.234") kabul edilir; ondalık ("12,5", "1.5") kabul edilmez.
 */
export function mevcutSayisi(metin: string): number | null {
  const temiz = metin.trim();
  if (!temiz) return null;
  const rakamlar = /^\d{1,3}(\.\d{3})+$/.test(temiz) ? temiz.replace(/\./g, "") : temiz;
  if (!/^\d+$/.test(rakamlar)) return Number.NaN;
  const sayi = Number(rakamlar);
  return sayi <= MEVCUT_EN_COK ? sayi : Number.NaN;
}

/** Formdan PUT gövdesi (tam gövde: sihirbaz ve Ayarlar bütün alanları birlikte yazar). */
export function formdanGovdeye(f: OkulFormu): SchoolConfigBody {
  const mevcut = mevcutSayisi(f.mevcut);
  return {
    school_name: f.okulAdi.trim(),
    province: f.il.trim(),
    district: f.ilce.trim(),
    principal_name: f.mudur.trim(),
    institution_code: f.kurumKodu.trim(),
    levels: kademeleriSirala(f.kademeler),
    student_count: mevcut === null || Number.isNaN(mevcut) ? null : mevcut,
    student_count_as_of: f.mevcutTarihi || null,
    settlement_type: f.yerlesim,
    canteen_mode: f.kantin,
    staffing_mode: f.personel,
    in_campus: f.kampus,
    opened_on: f.acilis || null,
    demirbas_onayi: f.demirbasOnayi,
    demirbas_no: f.demirbasNo.trim(),
    data_controller_text: f.veriSorumlusu.trim(),
  };
}

/** Eksik ya da geçersiz zorunlu alanlar → alan adı (backend alan kodu) → Türkçe ileti. */
export function okulBilgileriHatalari(f: OkulFormu): Record<string, string> {
  const hatalar: Record<string, string> = {};
  if (!f.okulAdi.trim()) hatalar.school_name = "Okul adı zorunludur.";
  if (!f.il.trim()) hatalar.province = "İl zorunludur.";
  if (!f.ilce.trim()) hatalar.district = "İlçe zorunludur.";
  const kod = f.kurumKodu.trim();
  if (!kod) hatalar.institution_code = "Kurum kodu zorunludur.";
  else if (!/^\d{6}$/.test(kod)) hatalar.institution_code = "Kurum kodu altı haneli bir sayıdır.";
  if (f.kademeler.length === 0) hatalar.levels = "En az bir kademe seçin.";
  const mevcut = mevcutSayisi(f.mevcut);
  if (mevcut === null) hatalar.student_count = "Öğrenci mevcudu zorunludur.";
  else if (Number.isNaN(mevcut)) {
    hatalar.student_count = "Öğrenci mevcudu 0 ile 99999 arasında bir tam sayıdır.";
  }
  if (!f.mevcutTarihi) hatalar.student_count_as_of = "Mevcudun tarihi zorunludur.";
  else if (f.mevcutTarihi > todayIso()) {
    hatalar.student_count_as_of = "Mevcudun tarihi bugünden sonra olamaz.";
  }
  if (!f.yerlesim) hatalar.settlement_type = "Yerleşim türünü seçin.";
  if (!f.kantin) hatalar.canteen_mode = "Kantin işletme biçimini seçin.";
  if (!f.personel) hatalar.staffing_mode = "Personel çalıştırma biçimini seçin.";
  if (!f.demirbasOnayi) {
    hatalar.demirbas_onayi = "Program yalnız okul demirbaşı bilgisayara kurulur; onay zorunludur.";
  }
  return hatalar;
}
