// `erisim` modülü API istemcisi — Erişim Günlüğü ekranının tek ucu (plan F1b-2 "Erişim günlüğü
// okuma ucu"; tasarım §4.6.4, §4.4.2 "Erişim günlüğü" satırı). Backend
// `apps/okul/views_erisim_gunlugu.py` ve `apps/okul/erisim_gunlugu.liste` ile BİREBİR; yanıt
// anahtarları Türkçedir.
//
// `GET access-log/?baslangic=yyyy-aa-gg&bitis=yyyy-aa-gg&tur=<tür>&hesap=<kimlik>&sayfa=N`:
// bütün süzgeçler isteğe bağlıdır (boş değer gönderilmez); gün Europe/Istanbul'a göredir, iki uç
// dahildir; en yeni önce, sayfalı (`sayfa_boyutu` sunucunundur). Yanıt süzgeç seçeneklerini de
// taşır: `turler` (kapalı küme, görünen adıyla) ve `hesaplar` (günlükte satırı olan hesaplar).
//
// KİŞİSİZDİR: hesap rol etiketi (sıra no'suz, okuma anındaki rol), tanıtıcı ve açılış/kapanış
// günüyle gelir; ad-soyad YOKTUR. Okunan değer günlükte hiç yoktur (yalnız kaydın kimliği).
// OKUMA İZ BIRAKMAZ (ne denetim izi ne erişim günlüğü satırı). Yalnız program yöneticisi ve
// Denetleme Kurulu (yetenek `erisim_gunlugu`); öteki rollerde 403 `rol_yetkisiz`. Biçimsiz
// süzgeç 400 `validation_error`'dır ve iletisi süzgecin alanına bağlıdır (`fields`: `baslangic`,
// `bitis`, `tur`, `hesap`, `sayfa`; takvimin ucundaki gün ve ters aralık da — ters aralıkta
// `bitis`).

import { api } from "../../lib/api";

/** Okuyan hesabın kişisiz özeti (`erisim_gunlugu._satir_ozeti`, `_hesap_ozetleri`). */
export interface ErisimHesabi {
  id: string;
  /** Hesabın kaydı bulunamazsa (yalnız satırlarda) null. */
  tanitici: string | null;
  /** Rol etiketi, sıra no'suz (satırda okuma anındaki rol). */
  rol_etiketi: string;
  /** Açılış ve kapanış günü (yyyy-aa-gg, Europe/Istanbul); açık hesapta ya da okunamazsa null. */
  acilis: string | null;
  kapanis: string | null;
}

/** Günlüğün bir satırı. */
export interface ErisimSatiri {
  id: number;
  /** Okuma anı (ISO, Europe/Istanbul). */
  zaman: string;
  hesap: ErisimHesabi;
  /** Tür kodu (iç kod; ekrana `tur_adi` yazılır). */
  tur: string;
  tur_adi: string;
  /** Okunan kaydın modeli, kimliği ve alanı (iç kod; değer yoktur). */
  model: string | null;
  kayit: string | null;
  alan: string | null;
  /** Çıktıysa belgenin sha256'sı ve satır sayısı. */
  belge_ozeti: string | null;
  satir_sayisi: number | null;
}

/** Tür süzgecinin seçeneği. */
export interface ErisimTuru {
  tur: string;
  tur_adi: string;
}

/** `GET access-log/` yanıtı (`erisim_gunlugu.liste`). */
export interface ErisimGunluguSayfasi {
  satirlar: ErisimSatiri[];
  /** Süzgece uyan satır sayısı. */
  toplam: number;
  sayfa: number;
  /** En az 1. */
  sayfa_sayisi: number;
  sayfa_boyutu: number;
  turler: ErisimTuru[];
  /** Günlükte satırı olan hesaplar (rol sırasıyla, aynı tanıtıcıda açılış sırasıyla). */
  hesaplar: ErisimHesabi[];
}

/** Süzgeçler; boş metin gönderilmez. Tarihler ISO yyyy-aa-gg'dir (ekranda gg.aa.yyyy). */
export interface ErisimSuzgeci {
  baslangic?: string;
  bitis?: string;
  tur?: string;
  hesap?: string;
  sayfa?: number;
}

export const ERISIM_GUNLUGU_YOLU = "/access-log/";

/** React Query anahtarının kökü. */
export const ERISIM_GUNLUGU_ANAHTARI = ["erisim-gunlugu"] as const;

/** Süzgeçlerin sorgu metni: boş değerler ve ilk sayfa yazılmaz (sunucu varsayılanı). */
export function sorguMetni(suzgec: ErisimSuzgeci): string {
  const parametreler = new URLSearchParams();
  for (const ad of ["baslangic", "bitis", "tur", "hesap"] as const) {
    const deger = suzgec[ad];
    if (deger) parametreler.set(ad, deger);
  }
  if (suzgec.sayfa !== undefined && suzgec.sayfa > 1) {
    parametreler.set("sayfa", String(suzgec.sayfa));
  }
  const metin = parametreler.toString();
  return metin ? `?${metin}` : "";
}

export const erisimGunluguApi = {
  /** Günlüğün bir sayfası (yalnız okur; iz bırakmaz). */
  sayfa: (suzgec: ErisimSuzgeci) =>
    api.get<ErisimGunluguSayfasi>(`${ERISIM_GUNLUGU_YOLU}${sorguMetni(suzgec)}`),
};
