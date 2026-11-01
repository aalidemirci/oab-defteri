// `guvenlik` modülü API istemcisi — güvenlik durumu, ilk hesap, kurtarma anahtarı
// belgesi, doğrulama ve yenileme, kayıp güvenlik dosyası ve yedekler.
// Backend `apps/okul/{urls,views}.py` "security/*" ve "backups/*" bloklarıyla BİREBİR.
// Oturum uçları (özet, kilit ekranının hesap listesi, kilit açma, Kilitle, kurtarma
// anahtarıyla açılış, kendi parolasını değiştirme, boşta kilit süresi) ayrı istemcidedir:
// `modules/oturum/api.ts` (backend `views_oturum.py`; tasarım §4.4.3).
// Parolalar YALNIZ gövdede taşınır; hiçbir yanıtta geri dönmez. Tek istisna
// `enable` ve `renew` yanıtlarındaki `recovery_key`: tek seferlik üretilir, bir daha
// alınamaz. İlk hesap zorunludur: "parolayı kaldır" ucu YOKTUR (tasarım §4.4.3).

import { api } from "../../lib/api";

/** `GET /security/status/` — sır ve kişi adı içermez, her açılışta okunur (`app_password.status`). */
export interface GuvenlikDurumu {
  /**
   * İlk program yöneticisi hesabı kurulu mu? Veri klasöründe `guvenlik.json` VAR ya da
   * veritabanında anahtar izi dolu (dosya kaybolsa bile "kurulu" sayılır).
   */
  password_set: boolean;
  /** Kurulu ve oturum açık değil → veri okunamaz (kilit ekranı). */
  locked: boolean;
  /**
   * Güvenlik dosyası kayıp: hesap kurulmuş ama `guvenlik.json` bulunamıyor ya da
   * okunamıyor (boş, bozuk, sarmal bölümleri eksik — backend ikisini ayırmaz).
   * Kayıtlar açılamaz; çıkış yolu dosyanın yedeğini geri koymak ya da bir
   * yedekten geri yüklemektir (backend 423 `guvenlik_dosyasi_kayip`).
   */
  security_file_missing: boolean;
  /** İlk hesabın kurulumu sürüyor mu (`guvenlik.json` `gecis`; yarım kalan kurulumu backend çözer)? */
  transition_pending: boolean;
  /** `"KURULUM"` | `""` (şema 2; F4'te DEK yenilemesi eklenir). */
  transition: string;
  /**
   * Kayıp ekranında "Güvenlik dosyasını sıfırla ve kuruluma dön" yolu açık mı? Yalnız
   * dosya okunamıyor + kayıtların anahtarı henüz veritabanına işlenmemiş + hiç kişi
   * kaydı yokken (korunan veri yok). Aksi hâlde backend 409 döner.
   */
  reset_available: boolean;
  /**
   * Kurtarma anahtarının saklandığı doğrulandı mı? (`guvenlik.json`'daki damga.) Kurulum
   * bu doğrulama olmadan tamamlanmaz; yenilenen anahtar yeniden doğrulanana dek yanlıştır.
   */
  recovery_key_confirmed: boolean;
  /** Korunan alanların Türkçe adları — arayüz metni bunları listeler. */
  protected_fields: string[];
  /** Güvenlik dosyasındaki hesap sarmalı sayısı (kurtarmayla geri yüklemeden sonra 0). */
  account_count: number;
  /** Kurtarma anahtarının no'su (her yeni anahtarda bir artar; tasarım TK10); yoksa null. */
  recovery_key_no: number | null;
  /** Kurtarma anahtarının üretim günü (ISO `yyyy-aa-gg`; ekranda gg.aa.yyyy); yoksa null. */
  recovery_key_date: string | null;
  /**
   * Bu süreçte okunan ve çözülemeyen şifreli alan sayısı (tasarım §13 D48). Sıfırdan
   * büyükse Genel Bakış'ta "okunamadı" kartı durur.
   */
  corrupt_field_count: number;
}

/** `POST /security/state/reset/` yanıtı: kenara alınan bozuk dosyanın adı + yeni durum. */
export interface SifirlamaSonucu extends GuvenlikDurumu {
  archived_as: string;
}

/**
 * `POST /security/enable/` gövdesi — ilk program yöneticisi hesabı (tasarım §4.4.4).
 * Anahtarlar Türkçedir (oturum sözleşmesi). Ad-soyad şifreli saklanır ve kilit
 * ekranında GÖSTERİLMEZ; tanıtıcının varsayılanı `yonetici`dir.
 */
export interface IlkHesapGovdesi {
  tanitici: string;
  ad_soyad: string;
  parola: string;
}

/** `POST /security/enable/` yanıtı: durum + TEK SEFERLİK kurtarma anahtarı. */
export interface IlkHesapSonucu extends GuvenlikDurumu {
  recovery_key: string;
  /**
   * Tanıtıcı ad-soyaddaki üç harften uzun bir sözcüğü içeriyorsa uyarı metni
   * (`hesap_kurallari.login_name_warning`; engel değil); yoksa null.
   */
  login_name_warning: string | null;
}

/** `POST /security/recovery-key/renew/` yanıtı: durum + TEK SEFERLİK YENİ kurtarma anahtarı. */
export interface AnahtarYenilemeSonucu extends GuvenlikDurumu {
  recovery_key: string;
}

/**
 * Bir kurtarma anahtarının kimliği: no'su ve üretim günü (tasarım TK10, §9.7). Sır
 * değildir; kurtarma anahtarı belgesinde de basılıdır. Güvenlik durumu (güncel anahtar),
 * ilk hesap ve yenileme yanıtları (yeni anahtar) ve yedek listesi (yedeği açan anahtar)
 * bu kimliği taşır.
 */
export interface KurtarmaKimligi {
  no: number | null;
  /** ISO gün (`yyyy-aa-gg`); ekranda gg.aa.yyyy. */
  tarih: string | null;
}

/**
 * Bir yedeği açan kurtarma anahtarının kimliği (yedek başlığından; `live_restore`).
 * Kullanıcı yeni bilgisayarda hangi kâğıdın hangi yedeği açtığını buradan görür.
 */
export type YedekKurtarmaKimligi = KurtarmaKimligi;

/** `GET /backups/` satırı — yedek klasöründeki bir yedek dosyası (daima şifreli). */
export interface YedekDosyasi {
  name: string;
  /** Bayt cinsinden boyut. */
  size: number;
  /** Son değişme anı (ISO tarih-saat, yerel dilim). */
  modified_at: string;
  /** Yedeği açan kurtarma anahtarının kimliği; başlık yok ya da okunamıyorsa null. */
  kurtarma: YedekKurtarmaKimligi | null;
}

export interface YedekListesi {
  /** Yedeklerin durduğu klasör — kullanıcı elden getirdiği dosyayı buradan bilir. */
  backup_dir: string;
  /** En yeniden eskiye sıralı. */
  backups: YedekDosyasi[];
}

/** `POST /backups/restore/` yanıtı. Başarıda backend "yeniden başlat" kapısını kurar. */
export interface GeriYuklemeSonucu {
  /** Kenara alınan önceki veritabanının adı (hedef yoksa boş). */
  old_db_name: string;
  /** guvenlik.json yedekteki kurtarma başlığından yeniden yazıldı mı? */
  state_written: boolean;
  restart_required: boolean;
}

/**
 * `GET/PUT /backups/external/` — dış yedek hatırlatması (tasarım §4.3 tehdit 18, §16 R6).
 * Tarih, şifreli yedek her indirildiğinde sunucuda kendiliğinden yazılır (veri
 * klasöründeki dosyada; veritabanında değil — geri yükleme onu geri sarmaz).
 */
export interface DisYedekDurumu {
  /** Son şifreli yedek indirmenin anı (ISO); hiç yoksa null. */
  last_download: string | null;
  /** Hatırlatma süresi (gün). */
  reminder_days: number;
  /** Son indirmeden (yoksa ilk hesabın kurulmasından) bu yana geçen gün. */
  days_since: number | null;
  /** Genel Bakış kartı gösterilsin mi? */
  remind: boolean;
  min_reminder_days: number;
  max_reminder_days: number;
}

export const guvenlikApi = {
  durum: () => api.get<GuvenlikDurumu>("/security/status/"),
  /**
   * İlk program yöneticisi hesabı (yalnız ilk kurulumda). Oturum bu hesapla açılır;
   * pencere YENİDEN YÜKLENMEZ (tasarım §13 D53: yalnız kilitlenme ve kilit ekranından
   * açılış) — sihirbaz kurtarma anahtarını göstermeyi sürdürür. Akış
   * `modules/oturum/eylemler.ts::ilkHesabiKur` üzerinden geçer.
   */
  kur: (govde: IlkHesapGovdesi) => api.post<IlkHesapSonucu>("/security/enable/", govde),
  /**
   * Kurtarma anahtarı belgesi (PDF). Anahtar yalnız gövdede gider; backend onu
   * kurtarma sarmalına karşı doğrular, yanlışsa 400 (kademeli gecikmeyle). Anahtar
   * sunucuda saklanmaz. Kilitliyken 423.
   */
  kurtarmaAnahtariPdf: (recovery_key: string) =>
    api.postBlob("/security/recovery-key/pdf/", { recovery_key }),
  /**
   * Anahtarın saklandığını doğrular: TAM anahtar gider, backend onu kurtarma sarmalına
   * karşı doğrulayıp güvenlik dosyasına damga yazar (yanlışsa 400, kademeli gecikmeyle).
   * Kurulum bu damga olmadan tamamlanmaz. Kilitliyken 423.
   */
  kurtarmaAnahtariniDogrula: (recovery_key: string) =>
    api.post<GuvenlikDurumu>("/security/recovery-key/confirm/", { recovery_key }),
  /**
   * Kurtarma anahtarını yeniler: oturumdaki hesabın kendi parolasını ister (gövde
   * anahtarı backend'de hâlâ İngilizce `password`; başka hesabın parolası geçmez, plan
   * F1b-1). Yanıttaki YENİ anahtar tek seferliktir, no'su bir artar; damga silinir, yeni
   * anahtar yeniden doğrulanmalıdır. Kayıtlar yeniden şifrelenmez. Kilitliyken 423.
   */
  kurtarmaAnahtariniYenile: (password: string) =>
    api.post<AnahtarYenilemeSonucu>("/security/recovery-key/renew/", { password }),
  /** Kayıp ekranındaki "sıfırla ve kuruluma dön" (yalnız `reset_available` iken). */
  sifirla: () => api.post<SifirlamaSonucu>("/security/state/reset/"),
  // Yedekten geri yükleme (Güvenlik sekmesi; güvenlik dosyası kayıpken de açık).
  // Parola/kurtarma anahtarı yalnız form gövdesinde taşınır; `geriYukle` çok
  // parçalı gönderir (dosya yüklemesi ile aynı uç — kaynak `name` YA DA `file`).
  yedekler: () => api.get<YedekListesi>("/backups/"),
  geriYukle: (form: FormData) => api.postForm<GeriYuklemeSonucu>("/backups/restore/", form),
  // Dış yedek hatırlatması. Pano kartı okuması kullanıcı etkinliği sayılmaz.
  disYedek: () => api.get<DisYedekDurumu>("/backups/external/", { etkinlik: false }),
  disYedekSuresi: (reminder_days: number) =>
    api.put<DisYedekDurumu>("/backups/external/", { reminder_days }),
};
