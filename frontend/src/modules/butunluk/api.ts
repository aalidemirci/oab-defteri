// `butunluk` modülü API istemcisi — denetim izinin kullanıcıya görünen yüzü (tasarım §4.6.3,
// §4.6.1 kural 1 ve 4, §4.4.3, §4.3 tehdit 7 ve 12; plan F1b-1 "Denetim izi"). Backend
// `apps/okul/views_oturum.py` "security/integrity/*" bloğu ve `apps/okul/iz_dogrulama.py`
// (`pano_ozeti`, `yenilenme_bildirimi`) ile BİREBİR.
//
// KİŞİSİZDİR: yanıtlarda ad-soyad YOKTUR; hesaplar kimlik, tanıtıcı ve rol etiketiyle gelir
// (kilit ekranındaki gibi; sözlük §5). Bulgu kodları (`kuyruk_kesik`, `capa_yok`…) iç koddur,
// ekrana çıkmaz: metni `metinler.ts` yazar (sözlük §2). Zamanlar Europe/Istanbul ISO
// metnidir (`+03:00`); ekranda `lib/format` ile gg.aa.yyyy SS:dd yazılır.
//
// Okumalar kullanıcı eylemi değildir (`X-OD-Etkinlik` gitmez; pano sorguları oturumu canlı
// tutmaz — tasarım §4.4.3). Yazmalar (sahipsiz sarmalın silinmesi, bildirimin "Gördüm"ü)
// denetim izine düşer (backend `test_izsiz_yazim.py`). Uçlar kilitliyken kapalıdır (423).
// Rol süzmesi (kartları yalnız program yöneticisi ve Denetleme Kurulu görür, silmeyi yalnız
// program yöneticisi yapar) F1b 2. adımdadır; bugün açık oturumdaki her hesaba görünür.

import { api } from "../../lib/api";

/** Bulgunun düzeyi: yalnız kesinti bilgidir, öteki her bulgu uyarıdır (`iz_dogrulama`). */
export type BulguDuzeyi = "uyari" | "bilgi";

/** Kartlardaki hesabın kişisiz özeti (`iz_dogrulama._hesap_ozeti`). */
export interface HesapOzeti {
  id: string;
  /** Kilit ekranındaki hesap adı; hesabın kaydı yoksa null. */
  tanitici: string | null;
  /** Kaydın söylediği rol etiketi ("Program yöneticisi", "Muhasip"); kayıt yoksa null. */
  rol_etiketi: string | null;
}

/**
 * Oturumdaki hesabın bir önceki girişinden beri yazılmış bir `BUTUNLUK` satırı: kilit
 * açılışındaki denetimin bulguları (`dogrulama`) ya da girişte tutmayan hesap mührü (`muhur`).
 */
export interface ButunlukBulgusu {
  seq: number;
  /** Satırın anı (ISO, Europe/Istanbul). */
  zaman: string;
  tur: "dogrulama" | "muhur";
  duzey: BulguDuzeyi;
  /** İç kodlar (`kuyruk_kesik`…; mühürde `seal`) — ekrana `metinler.bulguMetni` yazar. */
  bulgular: string[];
  /** Yalnız `muhur`'da: kaydı değiştirilmiş görünen hesap. */
  hesap: HesapOzeti | null;
}

/** Bir `GERI_YUKLEME` satırının kişisiz özeti (tasarım §4.4.4). */
export interface GeriYuklemeKaydi {
  seq: number;
  /** Satırın anı: geri yüklemeden sonraki ilk kilit açılışı (ISO, Europe/Istanbul). */
  zaman: string;
  /** Geri yüklemenin kendi anı (geri yükleme notundan); okunamadıysa null. */
  geri_yukleme_ani: string | null;
  /** Satırı yazan, yani geri yüklemeden sonra ilk giren hesap. */
  hesap: HesapOzeti | null;
  /** Geri yüklemeyi açan yol: bir hesabın parolası ya da kurtarma anahtarı. */
  yol: "hesap" | "kurtarma" | null;
  /** `yol === "hesap"` ise o hesap. */
  yol_hesap: HesapOzeti | null;
  /**
   * Uygulama içinden yapılan geri yüklemeyi başlatan oturumun hesabı (iki yolda da);
   * konsoldan yapılan geri yüklemede oturum yoktur (null).
   */
  oturum_hesap: HesapOzeti | null;
  /** `yol === "kurtarma"` ise anahtar no'su. */
  kurtarma_no: number | null;
  /** Programın ürettiği yedeğin adı; elle seçilen dosyanın adı kayda geçmez (null). */
  yedek: string | null;
  /** Kenara alınan önceki veritabanının dosya adı (`db-onceki-…`). */
  onceki_dosya: string | null;
  onceki_sha256: string | null;
  /** Kenara alınan veritabanının son kaydı ("Kayıt no · Zincir"). */
  onceki_kayit_no: number | null;
  onceki_zincir: string | null;
  /** Geri yükleme notu okunamadı: olgu kayıtlı, ayrıntılar yok. */
  ayrintisiz: boolean;
}

/**
 * Son geri yükleme kartı: zamanca SON geri yükleme; Denetleme Kurulu "gördüm" diyene dek
 * kalır. İki geri yükleme arasında kilit açılmadıysa aynı girişte yazılan öncekiler
 * `onceki_geri_yuklemeler`'dedir (eskiden yeniye): yedeğin alındığı günden sonraki kayıtlar
 * İLK geri yüklemenin kenara aldığı veritabanındadır (`iz_dogrulama._geri_yukleme_karti`).
 */
export interface GeriYuklemeOzeti extends GeriYuklemeKaydi {
  onceki_geri_yuklemeler: GeriYuklemeKaydi[];
}

/** İki depo farkındaki hesap: özet + hesabın kapalı olup olmadığı. */
export interface IkiDepoHesabi extends HesapOzeti {
  kapali: boolean;
}

/** `guvenlik.json` ile veritabanındaki hesapların canlı farkı (tasarım §4.6.1 kural 4). */
export interface IkiDepoFarki {
  fark_var: boolean;
  /** Kaydı açık ama güvenlik dosyasında parolası olmayan hesaplar (giriş yapamaz). */
  sarmalsiz_hesaplar: IkiDepoHesabi[];
  /** Kaydı olmayan ya da kapalı hesapların güvenlik dosyasında kalan parola kayıtları. */
  silinebilir_sarmallar: IkiDepoHesabi[];
  /** Kaydı program dışından değiştirilmiş görünen hesaplar (hiçbir işleme konu olmaz). */
  muhru_tutmayan: IkiDepoHesabi[];
}

/** Denetim izinin son kaydı — kâğıt çapası (tasarım §4.6.3): "Kayıt no: N · Zincir: XXXX-XXXX". */
export interface KagitCapasi {
  kayit_no: number;
  /** Son kaydın mührünün ilk 8 onaltılık hanesi, büyük harf, 4-4 ("C3ED-8364"). */
  zincir: string;
}

/** Parola yenilenme bildirimi (tasarım §4.4.3, tehdit 12). */
export interface ParolaYenilenme {
  /** `SIFIRLAMA` (program yöneticisi sıfırladı) ya da `KURTARMA` (kurtarma anahtarıyla). */
  tur: string;
  /** Yenilenme anı (ISO, Europe/Istanbul). */
  zaman: string;
  /** O andan bu yana YALNIZ bu hesabın girişleri, en yeni önce (ilki bu oturum). */
  girisler: string[];
}

/** `GET /security/integrity/` — Genel Bakış'ın bütünlük kartları. */
export interface ButunlukDurumu {
  butunluk: ButunlukBulgusu[];
  geri_yukleme: GeriYuklemeOzeti | null;
  /** Kilit kapalıyken ya da fark hesaplanamazsa null. */
  iki_depo: IkiDepoFarki | null;
  /** Zincir boşsa null. */
  kagit_capasi: KagitCapasi | null;
  /** Oturumdaki hesabın son girişleri (en yeni önce, en çok 10). */
  son_girisler: string[];
  parola_yenilenme: ParolaYenilenme | null;
  /**
   * Okunamayan kartların adları (`butunluk`, `geri_yukleme`…): backend tek kartın hatasını
   * öteki kartlara yaymaz, adını buraya yazar; ön yüz uyarı kartıyla söyler.
   */
  okunamayan: string[];
}

/** `POST /security/integrity/orphan-wraps/` yanıtı: silinenler + güncel kartlar. */
export interface SahipsizSarmalSonucu extends ButunlukDurumu {
  silinen: string[];
}

/** `GET|POST /security/integrity/reset-notice/` yanıtı. */
export interface ParolaBildirimiYaniti {
  parola_yenilenme: ParolaYenilenme | null;
}

export const BUTUNLUK_YOLU = "/security/integrity/";
export const SAHIPSIZ_SARMAL_YOLU = "/security/integrity/orphan-wraps/";
export const PAROLA_BILDIRIMI_YOLU = "/security/integrity/reset-notice/";

export const butunlukApi = {
  /** Kartların durumu (kullanıcı eylemi değil). */
  durum: () => api.get<ButunlukDurumu>(BUTUNLUK_YOLU, { etkinlik: false }),
  /**
   * Program yöneticisinin onayıyla güvenlik dosyasında kalan sahipsiz parola kayıtlarını
   * siler (her biri `HESAP` satırı). Onaydan sonra fark değiştiyse 400.
   */
  sahipsizSarmallariSil: (hesaplar: string[]) =>
    api.post<SahipsizSarmalSonucu>(SAHIPSIZ_SARMAL_YOLU, { hesaplar }),
  /** Oturumdaki hesabın parola yenilenme bildirimi (kullanıcı eylemi değil). */
  parolaBildirimi: () => api.get<ParolaBildirimiYaniti>(PAROLA_BILDIRIMI_YOLU, { etkinlik: false }),
  /** "Gördüm": bildirim izli bir yazımla kapanır; yanıt güncel bildirimdir (null). */
  parolaBildiriminiGordum: () => api.post<ParolaBildirimiYaniti>(PAROLA_BILDIRIMI_YOLU, {}),
};
