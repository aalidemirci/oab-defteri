// `oturum` modülü API istemcisi — kişisel hesaplar ve tek oturum (tasarım §4.4.3, TK14;
// plan F1b-1 "Oturum"). Aile iskeletinin kip istemcisinin (`/security/mode/*`) yerini
// alır; görevli kipi ve kip uçları yoktur. Backend `apps/okul/views_oturum.py` ve
// `apps/okul/oturum.py::OturumDurumu.ozet` ile BİREBİR. Gövde anahtarları Türkçedir.
//
// Parolalar ve kurtarma anahtarı YALNIZ gövdede taşınır; hiçbir yanıtta dönmez. Kişi
// adı (ad-soyad) bu uçların HİÇBİRİNDE yoktur: kilit ekranı ve üst çubuk hesabı rol
// etiketi ve tanıtıcıyla gösterir (tasarım §4.4.3, sözlük §5).
//
// Pencerenin yeniden yüklenmesi (tasarım §13 D53) bu istemcide DEĞİLDİR: kilit açma,
// kurtarma ve Kilitle akışları `eylemler.ts`'ten geçer, yükleme `lib/kilit.ts`'tedir.

import { api } from "../../lib/api";

/** Backend `apps/okul/oturum.py` durumları (API ve arayüz bu dizeleri kullanır). */
export type OturumDurumAdi = "kurulum" | "kilitli" | "acik" | "guvenlik_dosyasi_kayip";

/** Backend `AccountRole` kodları (tasarım §2.3.1); kullanıcı metnine çıkmaz (sözlük §2). */
export type RolKodu =
  | "yonetici"
  | "baskan"
  | "baskan_yardimcisi"
  | "muhasip"
  | "sekreter"
  | "denetleme_kurulu"
  | "mudur";

/**
 * Backend `apps/okul/rol_izinleri.YETENEKLER`'in adları (tasarım §4.4.2; plan F1b-2): ön yüz
 * süzmesinin TEK kaynağı oturum özetindeki `hesap.yetenekler`'dir, ön yüz rol matrisini
 * kopyalamaz. İki listenin eşitliğini backend testi sınar (`test_rol_izinleri.
 * test_yetenek_adlari_on_yuzle_birebir`, bu diziyi kaynaktan okur: dizi yalnız çift tırnaklı
 * adlardan oluşur). Ön yüzde aranan her ad `YetenekAdi` türüyle yazılır: listeden düşen ad
 * typecheck'i kırar (adı değişen yetenek sessizce "yok" sayılmasın).
 */
export const YETENEK_ADLARI = [
  "ayrilis_havuzu",
  "bosta_sure_yazma",
  "butunluk_denetim",
  "ders_yili_yazma",
  "eokul_aktarimi",
  "erisim_gunlugu",
  "geri_yukleme_gordum",
  "guncelleme",
  "guvenlik",
  "iki_depo",
  "kapali_gun_yazma",
  "kisi_yazma",
  "kullanicilar",
  "kurulum_tamamlama",
  "ogrenciler",
  "okul_karti_yazma",
  "son_oturum_onay",
  "sube_yazma",
  "yol_haritasi",
] as const;

export type YetenekAdi = (typeof YETENEK_ADLARI)[number];

/** Oturumdaki hesabın kişisiz özeti (`OturumHesabi.ozet`). */
export interface OturumHesabi {
  id: string;
  /** Kilit ekranında görünen hesap adı (gerçek ad değildir; ör. `yonetici`, `dk-1`). */
  tanitici: string;
  rol: RolKodu;
  /** Kullanıcıya görünen rol adı; `yonetici` için kısa "Program yöneticisi". */
  rol_etiketi: string;
  /**
   * Rolün yetenekleri (`YETENEK_ADLARI`'ndan; sunucu türetir). Bilinmeyen ad yok sayılır,
   * olmayan yetenek "açık değil" demektir (fail-closed).
   */
  yetenekler: string[];
}

/** `GET /security/session/` yanıtı (`OturumDurumu.ozet`). */
export interface OturumOzeti {
  durum: OturumDurumAdi;
  /** Yalnız açık oturumda dolu. */
  hesap: OturumHesabi | null;
  /** Boşta kilit süresi (dakika; 3-30, varsayılan 10). */
  bosta_dk: number;
  /**
   * Boşta kilide kalan saniye. Yalnız açık oturumda, kilit beklemiyorken ve kurulum
   * tamamlanmışken doludur (kurulum sihirbazı bitene dek süre işlemez; tasarım §13 D15).
   * Ön yüzdeki geri sayım yalnız görseldir; karar her istekte sunucuda verilir.
   */
  bosta_kalan_sn: number | null;
  /** Uzun iş sürerken istenen kilit ertelendi: iş bitince uygulanacak. */
  kilit_bekliyor: boolean;
  /** Kurulum sihirbazı tamamlandı mı? (Boşta kilidin ve geri sayımın koşulu.) */
  kurulum_tamam: boolean;
  /** Düz dosya yüklemesinin sınırı (MB; `settings.MAX_UPLOAD_SIZE_MB`). */
  yukleme_siniri_mb: number;
}

/** `POST /security/lock/` yanıtı: kilidin sonucu + güncel özet. */
export interface KilitlemeSonucu extends OturumOzeti {
  /** `ertelendi`: uzun iş sürüyor, kilit iş bitince uygulanır (`kilit_bekliyor`). */
  sonuc: "kilitlendi" | "ertelendi" | "zaten_kilitli";
}

/**
 * `GET /security/accounts/` satırı — kilit ekranının hesap listesi (`hesaplar.lock_screen_accounts`).
 * Liste `guvenlik.json`'daki sarmallardan çıkar; ad-soyad ASLA dönmez.
 */
export interface KilitEkraniHesabi {
  id: string;
  tanitici: string;
  /** Rolü veritabanından okunamayan satırda null (satır seçilemez). */
  rol: RolKodu | null;
  /**
   * Rol etiketi; aynı rolde birden çok hesap varsa açılış sırasıyla no eklenir
   * ("Denetleme Kurulu 2"). Rol okunamadıysa "Hesap kaydı okunamadı".
   */
  rol_etiketi: string;
  secilebilir: boolean;
  /**
   * Askının nedeni: hatalı deneme askısı (`HATALI_DENEME`) ya da `Account.status = ASKIDA`
   * nedeni; askıda değilse null. İki kaynak da aynı biçimde gösterilir (plan F1b-1).
   */
  askida_nedeni: string | null;
}

/**
 * `GET /security/recover/` satırı — kurtarma anahtarıyla açılabilecek program yöneticisi
 * hesapları (`hesaplar.recovery_accounts`). Kurtarma anahtarıyla geri yüklemeden sonra
 * kilit ekranı listesi boştur (sarmal yok, tasarım TK10); hesap buradan seçilir.
 */
export interface KurtarmaHesabi {
  id: string;
  tanitici: string;
  rol_etiketi: string;
  /** Bu bilgisayarın güvenlik dosyasında sarmalı var mı (yoksa kurtarma onu yeniden kurar)? */
  sarmali_var: boolean;
}

/** `POST /security/unlock/` gövdesi. `yeni_parola` yalnız 409 `parola_yenilenmeli`den sonra. */
export interface KilitAcmaGovdesi {
  /** Hesabın kimliği (`KilitEkraniHesabi.id`). */
  hesap: string;
  parola: string;
  yeni_parola?: string;
}

/** `POST /security/recover/` gövdesi; `hesap` kimlik ya da tanıtıcıdır. */
export interface KurtarmaGovdesi {
  kurtarma_anahtari: string;
  hesap: string;
  yeni_parola: string;
}

/** `GET|PUT /security/idle-lock/` gövdesi ve yanıtı (yalnız açık oturumda; kilitliyken 423). */
export interface BostaKilitSuresi {
  dakika: number;
}

export const oturumApi = {
  /**
   * Oturum özeti. Varsayılan olarak `X-OD-Etkinlik` GÖNDERMEZ: periyodik yoklama
   * oturumu canlı tutmamalıdır (tasarım §4.4.3). `etkinlik: true` yalnız gerçek bir
   * etkileşimin hemen ardından verilir (etkinlik nabzı, `useOturum`); başlığı yine
   * `lib/api` son etkileşime bakarak ekler.
   */
  ozet: (etkinlik = false) => api.get<OturumOzeti>("/security/session/", { etkinlik }),
  /** Kilit ekranının hesap listesi (kilitliyken açık; kişi adı yok). */
  hesaplar: () => api.get<KilitEkraniHesabi[]>("/security/accounts/", { etkinlik: false }),
  /** Kilit açma. Başarıda yanıt güncel özettir; pencereyi `eylemler.kilidiAc` yeniden yükler. */
  ac: (govde: KilitAcmaGovdesi) => api.post<OturumOzeti>("/security/unlock/", govde),
  /** Kilitle (her rolde, parolasız). Uzun iş sürerken `sonuc: "ertelendi"`. */
  kilitle: () => api.post<KilitlemeSonucu>("/security/lock/"),
  /** Kurtarma anahtarıyla açılabilecek program yöneticisi hesapları. */
  kurtarmaHesaplari: () => api.get<KurtarmaHesabi[]>("/security/recover/", { etkinlik: false }),
  /** Kurtarma anahtarıyla açılış: program yöneticisi hesabının parolası yenilenir. */
  kurtar: (govde: KurtarmaGovdesi) => api.post<OturumOzeti>("/security/recover/", govde),
  /** Oturumdaki hesabın kendi parolası (yalnız açık oturumda; pencere yeniden yüklenmez). */
  parolaDegistir: (parola: string, yeni_parola: string) =>
    api.post<OturumOzeti>("/security/change-password/", { parola, yeni_parola }),
  /** Boşta kilit süresi (Ayarlar → Güvenlik). */
  bostaKilitSuresi: () => api.get<BostaKilitSuresi>("/security/idle-lock/"),
  bostaKilitSuresiniYaz: (dakika: number) =>
    api.put<BostaKilitSuresi>("/security/idle-lock/", { dakika }),
};
