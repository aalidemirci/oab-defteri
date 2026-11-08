// Testlerin ortak `SchoolConfig` kalıpları (backend `SchoolConfigSerializer` alan kümesiyle
// birebir; F1b 4. adım). Alan kümesi değiştikçe her test dosyası ayrı ayrı güncellenmesin diye
// tek yerde durur; testler yalnız farkı yazar. Veriler uydurmadır ("Örnek" önekli).

import type { SchoolConfig } from "../modules/okul/api";

/** İlk açılış: okul kartı boş. */
export const BOS_OKUL_KARTI: SchoolConfig = {
  school_name: "",
  province: "",
  district: "",
  principal_name: "",
  institution_code: "",
  levels: [],
  student_count: null,
  student_count_as_of: null,
  settlement_type: "",
  canteen_mode: "",
  staffing_mode: "",
  in_campus: false,
  opened_on: null,
  demirbas_onayi: false,
  demirbas_no: "",
  setup_completed: false,
};

/** Bütün zorunlu alanları dolu okul kartı (kurulum tamamlanmış). */
export const ORNEK_OKUL_KARTI: SchoolConfig = {
  ...BOS_OKUL_KARTI,
  school_name: "Örnek Anadolu Lisesi",
  province: "İstanbul",
  district: "Örnek İlçe",
  institution_code: "123456",
  levels: ["ORTAOGRETIM"],
  student_count: 1234,
  student_count_as_of: "2026-10-01",
  settlement_type: "BUYUKSEHIR",
  canteen_mode: "KIRAYA_VERILIYOR",
  staffing_mode: "CALISTIRMIYOR",
  demirbas_onayi: true,
  setup_completed: true,
};
