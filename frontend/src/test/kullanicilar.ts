// Kullanıcılar testlerinin ortak verisi (sunucunun `_kullanici_satiri` biçimi). Adlar, tanıtıcılar
// ve kimlikler UYDURMADIR (KVKK; CLAUDE.md "Gerçek kişi verisi"). Eylemlerin nedenleri sunucunun
// iletileridir (`hesaplar.py`; sözlük §1 "Kullanıcılar (F1b)").

import type { KullaniciAyrintisi, KullaniciSatiri, RolSecenegi } from "../modules/kullanicilar/api";

export const KENDI_KAPAT = "Kendi hesabınızı kapatamazsınız.";
export const KENDI_SIFIRLA =
  "Kendi parolanızı buradan sıfırlayamazsınız; Ayarlar → Güvenlik'teki “Parolayı değiştir” " +
  "penceresini kullanın.";
export const KENDI_PUSULA = "Kendi hesabınızın teslim pusulasını basamazsınız.";
export const ASKIDA_DEGIL = "Hesap askıda değil.";
export const HESAP_KAPALI = "Hesap kapalı; kapalı hesap yeniden açılmaz, yeni hesap açılır.";
export const KAYIT_DEGISMIS =
  "Hesap kaydı program dışından değiştirilmiş görünüyor; program bu kayda dokunmaz. " +
  "Denetleme Kuruluna bildirin.";

const ACIK = { yapilabilir: true, neden: null };
const KAPALI = (neden: string) => ({ yapilabilir: false, neden });

/** Açık bir muhasip hesabı: sıfırlama, kapama ve pusula açık; askıdan çıkarma kapalı. */
export function hesapSatiri(ust: Partial<KullaniciSatiri> = {}): KullaniciSatiri {
  return {
    id: "6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e",
    tanitici: "muhasip",
    rol: "muhasip",
    rol_etiketi: "Muhasip",
    ad_soyad: "Deneme Muhasipoğlu",
    durum: "ACIK",
    durum_etiketi: "Açık",
    askida_nedeni: null,
    askida_nedeni_etiketi: null,
    kayit_tutuyor: true,
    oturumdaki: false,
    acilis: "2026-11-02T10:15:00+03:00",
    kapanis: null,
    son_giris: "2026-11-03T08:05:00+03:00",
    giris: { yapabilir: true, neden: null },
    eylemler: {
      kapat: ACIK,
      askidan_cikar: KAPALI(ASKIDA_DEGIL),
      parola_sifirla: ACIK,
      pusula: ACIK,
    },
    ...ust,
  };
}

/** Oturumdaki program yöneticisi: kendi hesabında eylemler sunucunun nedeniyle kapalı. */
export const KENDI_HESABI: KullaniciSatiri = hesapSatiri({
  id: "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d",
  tanitici: "yonetici",
  rol: "yonetici",
  rol_etiketi: "Program yöneticisi",
  ad_soyad: "Örnek Yönetici",
  oturumdaki: true,
  acilis: "2026-11-01T09:00:00+03:00",
  son_giris: "2026-11-04T08:30:00+03:00",
  eylemler: {
    kapat: KAPALI(KENDI_KAPAT),
    askidan_cikar: KAPALI(ASKIDA_DEGIL),
    parola_sifirla: KAPALI(KENDI_SIFIRLA),
    pusula: KAPALI(KENDI_PUSULA),
  },
});

/** Kapalı hesap: dört eylem aynı nedenle kapalı. */
export const KAPALI_HESAP: KullaniciSatiri = hesapSatiri({
  id: "9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b",
  tanitici: "sekreter",
  rol: "sekreter",
  rol_etiketi: "Sekreter",
  ad_soyad: "Uydurma Sekreter",
  durum: "KAPALI",
  durum_etiketi: "Kapalı",
  kapanis: "2026-11-03T16:40:00+03:00",
  giris: { yapabilir: false, neden: "Hesap kapalı." },
  eylemler: {
    kapat: KAPALI(HESAP_KAPALI),
    askidan_cikar: KAPALI(HESAP_KAPALI),
    parola_sifirla: KAPALI(HESAP_KAPALI),
    pusula: KAPALI(HESAP_KAPALI),
  },
});

/** Satırın ayrıntısı (ek alanlar boş). */
export function ayrinti(
  satir: KullaniciSatiri,
  ust: Partial<KullaniciAyrintisi> = {},
): KullaniciAyrintisi {
  return {
    ...satir,
    acan: { id: KENDI_HESABI.id, tanitici: "yonetici", rol_etiketi: "Program yöneticisi" },
    kapatan: null,
    parola_degisimi: null,
    sifirlama: null,
    son_girisler: [],
    ...ust,
  };
}

/** "Yeni hesap" penceresinin rol seçenekleri (sunucunun biçimi). */
export const ROL_SECENEKLERI: RolSecenegi[] = [
  {
    rol: "yonetici",
    rol_etiketi: "Program yöneticisi",
    acilabilir: true,
    neden: null,
    varsayilan_tanitici: "yonetici-2",
    bilgi:
      "Program yöneticisi değiştiğinde kayıtların anahtarının yenilenmesi programın sonraki bir " +
      "sürümünde gelecek; bu hesap ikinci bir program yöneticisi hesabı olarak açılır.",
  },
  {
    rol: "baskan",
    rol_etiketi: "Başkan",
    acilabilir: true,
    neden: null,
    varsayilan_tanitici: "baskan",
    bilgi: null,
  },
  {
    rol: "muhasip",
    rol_etiketi: "Muhasip",
    acilabilir: false,
    neden: "Bu rolde açık bir hesap zaten var; önce onu kapatın.",
    varsayilan_tanitici: "muhasip-2",
    bilgi: null,
  },
  {
    rol: "denetleme_kurulu",
    rol_etiketi: "Denetleme Kurulu",
    acilabilir: true,
    neden: null,
    varsayilan_tanitici: "dk-1",
    bilgi: null,
  },
];
