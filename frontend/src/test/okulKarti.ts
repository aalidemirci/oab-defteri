// Testlerin ortak `SchoolConfig` kalıpları (backend `SchoolConfigSerializer` alan kümesiyle
// birebir; F1b 4. adım). Alan kümesi değiştikçe her test dosyası ayrı ayrı güncellenmesin diye
// tek yerde durur; testler yalnız farkı yazar. Veriler uydurmadır ("Örnek" önekli).

import type { SchoolConfig } from "../modules/okul/api";
import type { KantinBilgisi } from "../modules/okul/kuralBilgileri";

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
  data_controller_text: "",
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

/** Kural paketinden gelen md. 23/3 bilgisinin metni (sözlükteki metin; uç sınaması backend'dedir). */
export const KANTIN_ISLETME_BILGISI =
  "Kantin ve benzeri yerler birlikçe işletilir ve vergi mükellefiyeti doğarsa birlik hakkında " +
  "213 sayılı Vergi Usul Kanunu hükümleri uygulanır (md. 23/3).";

export const ORNEK_KANTIN_BILGISI: KantinBilgisi = {
  modlar: ["BIRLIKCE_ISLETILIYOR"],
  metin: KANTIN_ISLETME_BILGISI,
  paket: "OAB-2023.12",
  rev: 1,
};
