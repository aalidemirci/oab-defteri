// `kullanicilar` modülü API istemcisi — Kullanıcılar ekranının uçları (plan F1b-2 "Kullanıcılar
// uçları"; tasarım §4.4.2 Kullanıcılar satırı, §4.4.5). Backend `apps/okul/views_hesaplar.py` ve
// `apps/okul/services/hesaplar.py` (`_kullanici_satiri`, `kullanici_ayrintisi`,
// `kullanici_secenekleri`) ile BİREBİR; gövde ve yanıt anahtarları Türkçedir. Uçların hepsi
// yalnız program yöneticisine açıktır (yetenek `kullanicilar`; rol kapısı ve servisin yetki
// kapısı); yalnız açık oturumda (kilitliyken 423).
//
// SÖZLEŞME: satırın eylemlerini ve yapılamama nedenlerini SUNUCU hesaplar (`eylemler`); ön yüz
// yalnız eşler, nedeni kendisi kurmaz. Rol etiketi sıra no'suzdur. Kodlar (`durum`,
// `askida_nedeni`, `sifirlama.tur`) kullanıcı metnine çıkmaz; ekran etiketleri yazar.
//
// GEÇİCİ PAROLA yalnız istek gövdesinde gider (`gecici_parola`); hiçbir yanıtta dönmez. Öneriyi
// ön yüz kurar (`geciciParola.ts`), sunucu yalnız politikayı denetler.
//
// RET: servis reddi 400 `validation_error` (Türkçe ileti, alan yok); kaydı ya da izi tutmayan
// hesap 409 `hesap_muhru_tutmadi`; denetim izi yazılamazsa 409 `iz_yazilamadi`; rol 403
// `rol_yetkisiz`. Güvenlik dosyası yazılamazsa da 400 `validation_error`'dır ve ileti neyin
// yapılıp neyin yapılmadığını söyler (hesap açılmış, kapanmış, parolası "Parola yenilenmeli"ye
// düşmüş olabilir): ekran her yazma isteğinden sonra (başarılı ya da değil) listeyi yeniden okur.
// Hesap açmanın bu reddinde ayırt edici kod yoktur: "Yeni hesap" penceresi hesabın açıldığını
// gönderimden önceki ve sonraki listeden anlar (`YeniHesapPenceresi` "YARIM AÇILIŞ").

import { api } from "../../lib/api";
import type { IndirilenDosya } from "../../lib/api";
import type { RolKodu } from "../oturum/api";

/** Hesabın durumu (backend `AccountStatus`); ekrana `durum_etiketi` yazılır. */
export type HesapDurumu = "ACIK" | "PAROLA_YENILENMELI" | "ASKIDA" | "KAPALI";

/** Bir eylemin yapılıp yapılamayacağı; yapılamıyorsa nedeni (kullanıcı metni). */
export interface EylemDurumu {
  yapilabilir: boolean;
  neden: string | null;
}

/** Satırın eylemleri (backend `EYLEM_*`). `pusula` hesap teslim pusulasıdır. */
export interface SatirEylemleri {
  kapat: EylemDurumu;
  askidan_cikar: EylemDurumu;
  parola_sifirla: EylemDurumu;
  pusula: EylemDurumu;
}

/** `GET accounts/` satırı (`hesaplar._kullanici_satiri`; geçici parola YOK). */
export interface KullaniciSatiri {
  id: string;
  /** Kilit ekranında görünen hesap adı (gerçek ad değildir). */
  tanitici: string;
  rol: RolKodu | string;
  /** Sıra no'suz rol etiketi ("Program yöneticisi", "Denetleme Kurulu"). */
  rol_etiketi: string;
  /** Hesap sahibinin adı-soyadı; çözülemezse null (ekran "okunamadı" yazar). */
  ad_soyad: string | null;
  durum: HesapDurumu | string;
  durum_etiketi: string;
  /** Askı kodu (`HATALI_DENEME`, `UYELIK_DUSTU`…); askıda değilse null. */
  askida_nedeni: string | null;
  askida_nedeni_etiketi: string | null;
  /** Hesabın kaydı (mühür, satır izi, iz boşluğu) tutuyor mu? */
  kayit_tutuyor: boolean;
  /** Oturumdaki hesabın kendisi mi? */
  oturumdaki: boolean;
  /** Açılış, kapanış ve son giriş anları (ISO, Europe/Istanbul); yoksa ya da okunamazsa null. */
  acilis: string | null;
  kapanis: string | null;
  son_giris: string | null;
  /** Hesap bugün kilit ekranından girebilir mi; giremiyorsa nedeni. */
  giris: { yapabilir: boolean; neden: string | null };
  eylemler: SatirEylemleri;
}

/** Ayrıntıdaki ilgili hesap (açan, kapatan, sıfırlayan): kişisiz. */
export interface HesapKisaltmasi {
  id: string;
  /** Hesabın kaydı yoksa null. */
  tanitici: string | null;
  rol_etiketi: string | null;
}

/** Son sıfırlama: tür kodu (`SIFIRLAMA` ya da `KURTARMA`), an ve yapan. */
export interface SifirlamaBilgisi {
  tur: string | null;
  zaman: string | null;
  yapan: HesapKisaltmasi | null;
}

/** `GET accounts/<id>/` yanıtı (`hesaplar.kullanici_ayrintisi`). */
export interface KullaniciAyrintisi extends KullaniciSatiri {
  acan: HesapKisaltmasi | null;
  kapatan: HesapKisaltmasi | null;
  parola_degisimi: string | null;
  sifirlama: SifirlamaBilgisi | null;
  /** Kilit ekranından son girişler (ISO anlar, en yeni önce). */
  son_girisler: string[];
}

/** `GET accounts/options/` satırı (`hesaplar.kullanici_secenekleri`). */
export interface RolSecenegi {
  rol: RolKodu;
  rol_etiketi: string;
  acilabilir: boolean;
  /** Açılamıyorsa nedeni (hesap açmanın vereceği iletinin aynısı). */
  neden: string | null;
  /** Rolden türeyen, açık hesaplarda kullanılmayan ilk tanıtıcı. */
  varsayilan_tanitici: string;
  /** Program yöneticisi rolünde ikinci program yöneticisinin bilgisi; yoksa null. */
  bilgi: string | null;
}

export interface KullaniciSecenekleri {
  roller: RolSecenegi[];
}

/** `POST accounts/` gövdesi. */
export interface HesapAcmaGovdesi {
  rol: string;
  tanitici: string;
  ad_soyad: string;
  gecici_parola: string;
}

/** `POST accounts/` yanıtı (201). */
export interface HesapAcmaSonucu {
  hesap: KullaniciSatiri;
  /** Tanıtıcının kişisel veri uyarısı (engel değil); yoksa null. */
  uyari: string | null;
  /** Program yöneticisi rolünde ikinci program yöneticisinin bilgisi; yoksa null. */
  bilgi: string | null;
}

/** Eylem uçlarının yanıtı: güncel satır. */
export interface SatirYaniti {
  hesap: KullaniciSatiri;
}

const KOK = "/accounts/";

export const kullanicilarApi = {
  /** Bütün hesaplar (giriş yapamayanlar ve kapalılar dahil; sunucu sıralar). */
  liste: async () => (await api.get<{ hesaplar: KullaniciSatiri[] }>(KOK)).hesaplar,
  /** "Yeni hesap" penceresinin rol seçenekleri. */
  secenekler: () => api.get<KullaniciSecenekleri>(`${KOK}options/`),
  /** Hesabın ayrıntısı ve son girişleri. */
  ayrinti: (id: string) => api.get<KullaniciAyrintisi>(`${KOK}${id}/`),
  /** Hesap açma (geçici parola yalnız gövdede). */
  ac: (govde: HesapAcmaGovdesi) => api.post<HesapAcmaSonucu>(KOK, govde),
  /** Hesabı kapatır (parola kaydı güvenlik dosyasından silinir). */
  kapat: (id: string) => api.post<SatirYaniti>(`${KOK}${id}/close/`),
  /** Askıdan çıkarır. */
  askidanCikar: (id: string) => api.post<SatirYaniti>(`${KOK}${id}/unsuspend/`),
  /** Parolayı geçici parolayla sıfırlar. */
  parolaSifirla: (id: string, gecici_parola: string) =>
    api.post<SatirYaniti>(`${KOK}${id}/reset-password/`, { gecici_parola }),
  /** Hesap teslim pusulası (PDF); adı sunucunun `Content-Disposition`'ındandır. */
  pusula: (id: string): Promise<IndirilenDosya> => api.postDosya(`${KOK}${id}/handover-slip/`),
};

/**
 * Kullanıcılar sorgularının ortak anahtarı (react-query): liste `[…, "liste"]`, ayrıntı
 * `[…, "ayrinti", id]`, seçenekler `[…, "secenekler"]`. Her yazmadan sonra bu önek geçersiz kılınır:
 * liste, açık ayrıntı ve seçenekler birlikte yeniden okunur.
 */
export const KULLANICILAR_ANAHTARI = ["kullanicilar"] as const;
