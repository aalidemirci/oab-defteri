// `butunluk` modülü API istemcisi — denetim izinin kullanıcıya görünen yüzü (tasarım §4.6.3,
// §4.6.1 kural 1 ve 4, §4.4.3, §4.3 tehdit 7 ve 12; plan F1b-1 "Denetim izi"). Backend
// `apps/okul/views_oturum.py` "security/integrity/*" bloğu ve `apps/okul/iz_dogrulama.py`
// (`kendi_kartlari`, `denetim_kartlari`, `iki_depo_karti`, `yenilenme_bildirimi`) ile BİREBİR.
//
// KİŞİSİZDİR: yanıtlarda ad-soyad YOKTUR; hesaplar kimlik, tanıtıcı ve rol etiketiyle gelir
// (kilit ekranındaki gibi; sözlük §5). Bulgu kodları (`kuyruk_kesik`, `capa_yok`…) iç koddur,
// ekrana çıkmaz: metni `metinler.ts` yazar (sözlük §2). Zamanlar Europe/Istanbul ISO
// metnidir (`+03:00`); ekranda `lib/format` ile gg.aa.yyyy SS:dd yazılır.
//
// Okumalar kullanıcı eylemi değildir (`X-OD-Etkinlik` gitmez; pano sorguları oturumu canlı
// tutmaz — tasarım §4.4.3). Yazmalar (sahipsiz sarmalın silinmesi, bildirimin "Gördüm"ü)
// denetim izine düşer (backend `test_izsiz_yazim.py`). Uçlar kilitliyken kapalıdır (423).
//
// ROLE GÖRE ÜÇ UÇ (tasarım §4.4.2 "kısmi yetki ayrı uçla verilir"; plan F1b-2): kendi kartları
// (`security/integrity/`: son girişler, parola yenilenme, kâğıt çapası) her role açıktır;
// denetim kartları (`audit/`: bütünlük, geri yükleme, mührü tutmayan hesaplar, eksik ekler)
// program yöneticisi ve Denetleme Kuruluna; iki depo kartı (`two-store/`) ve sahipsiz kaydın
// silinmesi yalnız program yöneticisine; geri yükleme kartının "Gördüm"ü (`restore-seen/`)
// yalnız Denetleme Kuruluna. Hangi ucun çağrılacağını oturum özetindeki yetenekler söyler
// (`butunluk_denetim`, `iki_depo`, `geri_yukleme_gordum`; `oturum/useOturum.useYetenekler`,
// `oturum/yetki`): rolün açamadığı uç ÇAĞRILMAZ. Kartlar tek bir bileşik durumdan beslenir (`ButunlukDurumu`,
// `birlestir`); mührü tutmayan hesaplar denetim kartlarından gelir ve "Hesaplar ve Güvenlik
// Dosyası" kartının listesinde durur (program yöneticisinde iki depo farkıyla birlikte).

import { api } from "../../lib/api";
import type { DosyaSayilari } from "../guvenlik/api";
import type { YetenekAdi } from "../oturum/api";

/** Bulgunun düzeyi: yalnız kesinti bilgidir, öteki her bulgu uyarıdır (`iz_dogrulama`). */
export type BulguDuzeyi = "uyari" | "bilgi";

/** Kartlardaki hesabın kişisiz özeti (`iz_dogrulama._hesap_ozeti`). */
export interface HesapOzeti {
  id: string;
  /** Kilit ekranındaki hesap adı; hesabın kaydı yoksa null. */
  tanitici: string | null;
  /** Kaydın söylediği rol etiketi ("Program yöneticisi", "Muhasip"); kayıt yoksa null. */
  rol_etiketi: string | null;
  /**
   * Hesabın açılış ve kapanış günü (yyyy-aa-gg, Europe/Istanbul; açık hesapta `kapanis` null,
   * kayıt yoksa ikisi de null): kapanan hesapla aynı tanıtıcıyı alan yeni hesabı ayırır. Denetim
   * kartlarının hesabında gelir; iki depo listelerinde yoktur (orada `kapali` ayırır).
   */
  acilis?: string | null;
  kapanis?: string | null;
  /**
   * Yalnız geri yükleme kartında, kimliği geçerli ama yerine konan kayıtlarda satırı olmayan
   * hesapta true (`iz_dogrulama._geri_yukleme_hesabi`); öteki hesaplarda alan yoktur.
   */
  yedekte_yok?: boolean;
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
  /**
   * Dosya ayağının kişisiz sayıları (plan F1b-3 "Geri yükleme"). Bu bilgiyi taşımayan eski satırda
   * boş nesnedir; biçimi tutmayan değer satıra girmediği için alanlar tek tek eksik olabilir.
   */
  dosyalar: Partial<DosyaSayilari>;
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

/** `GET /security/integrity/two-store/`'un `iki_depo`'su (tasarım §4.6.1 kural 4). */
export interface IkiDepoKaydi {
  /** Sarmalsız hesap ya da silinebilir kayıt var mı? */
  fark_var: boolean;
  /** Kaydı açık ama güvenlik dosyasında parolası olmayan hesaplar (giriş yapamaz). */
  sarmalsiz_hesaplar: IkiDepoHesabi[];
  /** Kaydı olmayan ya da kapalı hesapların güvenlik dosyasında kalan parola kayıtları. */
  silinebilir_sarmallar: IkiDepoHesabi[];
  /**
   * Parola kaydı hesap kaydındaki özeti tutmayan hesaplar (eski ya da program dışından konmuş
   * parola kaydı; giriş yapamaz, çaresi program yöneticisinin parola sıfırlaması, program
   * yöneticisinin kendi hesabıysa kurtarma anahtarıyla açılış). Sunucu F1b-2 (b3)'ten beri yollar;
   * yanıtta yoksa boş sayılır. Kartta "Parola kaydı hesap kaydıyla uyuşmayan hesaplar" listesidir
   * (`IkiDepoKarti`).
   */
  ozeti_tutmayan_hesaplar?: IkiDepoHesabi[];
}

/**
 * "Hesaplar ve Güvenlik Dosyası" kartının durumu: iki depo farkı (yalnız program yöneticisi)
 * ve mührü tutmayan hesaplar (denetim kartlarından; program yöneticisi ve Denetleme Kurulu).
 */
export interface IkiDepoFarki extends IkiDepoKaydi {
  /** Kaydı ya da denetim izi program dışından değiştirilmiş görünen hesaplar (dokunulmaz). */
  muhru_tutmayan: IkiDepoHesabi[];
}

/**
 * Satırı olup depoda dosyası bulunmayan ek (`dosya_deposu.eksik_ekler`; tasarım §4.4.7 "Yetim ve
 * eksik dosya"). Özgün ad yalnız burada ve kaydın kendisinde görünür (kullanıcı kararı 04.11.2026
 * "Eksik ve bozuk ekler kişisiz bilgiyle listelenir"); kişi adı taşıyabilir, başka yere yazılmaz.
 */
export interface EksikEk {
  kayit_turu: string;
  kayit_no: string;
  /** ISO gün (`yyyy-aa-gg`); ekranda gg.aa.yyyy. */
  yukleme_tarihi: string;
  /** Bayt cinsinden boy. */
  boyut: number;
  /** Çözülemeyen adda null. */
  ozgun_ad: string | null;
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

/** `GET /security/integrity/` — oturumdaki hesabın kendi kartları (her rol). */
export interface KendiKartlari {
  kagit_capasi: KagitCapasi | null;
  son_girisler: string[];
  parola_yenilenme: ParolaYenilenme | null;
  okunamayan: string[];
}

/** `GET /security/integrity/audit/` — denetim kartları (program yöneticisi, Denetleme Kurulu). */
export interface DenetimKartlari {
  butunluk: ButunlukBulgusu[];
  geri_yukleme: GeriYuklemeOzeti | null;
  muhru_tutmayan: IkiDepoHesabi[];
  /** Depo okunamazsa boştur ve adı `okunamayan`'dadır: boş liste "eksik yok" demek değildir. */
  eksik_ekler: EksikEk[];
  okunamayan: string[];
}

/** `GET /security/integrity/two-store/` — iki depo kartı (yalnız program yöneticisi). */
export interface IkiDepoYaniti {
  /** Fark hesaplanamazsa null. */
  iki_depo: IkiDepoKaydi | null;
  okunamayan: string[];
}

/** Rolün açabildiği bütünlük uçları (oturum özetinin yeteneklerinden). */
export interface ButunlukYetkisi {
  /** `audit/` (yetenek `butunluk_denetim`). */
  denetim: boolean;
  /** `two-store/` ve sahipsiz kaydın silinmesi (yetenek `iki_depo`). */
  ikiDepo: boolean;
}

/** Denetim kartlarının yeteneği (`audit/`). Ad `YetenekAdi` türüyle bağlıdır. */
export const DENETIM_YETENEGI: YetenekAdi = "butunluk_denetim";
/** İki depo kartının ve sahipsiz kaydın silinmesinin yeteneği. */
export const IKI_DEPO_YETENEGI: YetenekAdi = "iki_depo";

/** Oturum özetinin yeteneklerinden bütünlük uçlarının yetkisi (ön yüz matrisi kopyalamaz). */
export function butunlukYetkisi(yetenekler: readonly string[]): ButunlukYetkisi {
  return {
    denetim: yetenekler.includes(DENETIM_YETENEGI),
    ikiDepo: yetenekler.includes(IKI_DEPO_YETENEGI),
  };
}

/** Genel Bakış'ın bütünlük kartlarının bileşik durumu (üç ucun yanıtı birleşir; `birlestir`). */
export interface ButunlukDurumu {
  butunluk: ButunlukBulgusu[];
  geri_yukleme: GeriYuklemeOzeti | null;
  /** Kilit kapalıyken, fark hesaplanamazsa ya da rol iki ucu da açamıyorsa null. */
  iki_depo: IkiDepoFarki | null;
  /** Dosyası bulunamayan ekler (denetim kartlarından; öteki rollerde boş). */
  eksik_ekler: EksikEk[];
  /** Zincir boşsa null. */
  kagit_capasi: KagitCapasi | null;
  /** Oturumdaki hesabın son girişleri (en yeni önce, en çok 10). */
  son_girisler: string[];
  parola_yenilenme: ParolaYenilenme | null;
  /**
   * Okunamayan kartların adları (`butunluk`, `geri_yukleme`…): backend tek kartın hatasını
   * öteki kartlara yaymaz, adını o ucun yanıtına yazar; ön yüz uyarı kartıyla söyler.
   */
  okunamayan: string[];
}

/** `POST /security/integrity/orphan-wraps/` yanıtı: silinenler + güncel iki depo kartı. */
export interface SahipsizSarmalSonucu extends IkiDepoYaniti {
  silinen: string[];
}

/**
 * `GET|POST /security/integrity/reset-notice/` yanıtı. Bildirim okunamazsa (program dışından
 * bozulmuş sıfırlama anı) `parola_yenilenme` null'dır ve adı `okunamayan`'dadır (uç 500 dönmez;
 * Genel Bakış'ın kartı aynı durumu "okunamadı" diye söyler, pencere çizilmez).
 */
export interface ParolaBildirimiYaniti {
  parola_yenilenme: ParolaYenilenme | null;
  okunamayan?: string[];
}

export const BUTUNLUK_YOLU = "/security/integrity/";
export const DENETIM_KARTLARI_YOLU = "/security/integrity/audit/";
export const IKI_DEPO_YOLU = "/security/integrity/two-store/";
export const SAHIPSIZ_SARMAL_YOLU = "/security/integrity/orphan-wraps/";
export const PAROLA_BILDIRIMI_YOLU = "/security/integrity/reset-notice/";
/** Geri yükleme kartının "Gördüm"ü (yalnız Denetleme Kurulu; yetenek `geri_yukleme_gordum`). */
export const GERI_YUKLEME_GORDUM_YOLU = "/security/integrity/restore-seen/";

type Nesne = Record<string, unknown>;

function nesneMi(deger: unknown): deger is Nesne {
  return deger !== null && typeof deger === "object" && !Array.isArray(deger);
}

function liste<T>(deger: unknown): T[] {
  return Array.isArray(deger) ? [...(deger as T[])] : [];
}

/** Eksik ekler kartının `okunamayan`'daki adı: depo okunamadı, kart "eksik yok" demez. */
export const EKSIK_EKLER_KARTI = "eksik_ekler";

/** Denetim kartları ucunun kartları (yanıtı okunamazsa adları `okunamayan`'a yazılır). */
const DENETIM_KARTLARI = ["butunluk", "geri_yukleme", "muhru_tutmayan", EKSIK_EKLER_KARTI] as const;

/**
 * "Hesaplar ve Güvenlik Dosyası" kartının durumu: iki depo kaydı (eksik liste boş) ve mührü
 * tutmayan hesaplar. Kayıt yoksa ve mührü tutmayan hesap da yoksa null.
 */
export function ikiDepoFarki(
  kayit: IkiDepoKaydi | null | undefined,
  muhruTutmayan: readonly IkiDepoHesabi[],
): IkiDepoFarki | null {
  if ((kayit === null || kayit === undefined) && muhruTutmayan.length === 0) return null;
  return {
    fark_var: Boolean(kayit?.fark_var) || muhruTutmayan.length > 0,
    sarmalsiz_hesaplar: liste<IkiDepoHesabi>(kayit?.sarmalsiz_hesaplar),
    silinebilir_sarmallar: liste<IkiDepoHesabi>(kayit?.silinebilir_sarmallar),
    ozeti_tutmayan_hesaplar: liste<IkiDepoHesabi>(kayit?.ozeti_tutmayan_hesaplar),
    muhru_tutmayan: [...muhruTutmayan],
  };
}

/**
 * Üç ucun yanıtını kartların bileşik durumuna çevirir. Çağrılmayan uç `null`'dır (kartları
 * boş). Kendi kartları nesne değilse durum okunamamıştır (null); çağrılan öteki uç nesne
 * değilse kartlarının adı `okunamayan`'a girer (uyarı sessizce kaybolmaz). Eksik alan boştur.
 */
export function birlestir(
  kendi: unknown,
  denetim: unknown,
  ikiDepo: unknown,
): ButunlukDurumu | null {
  if (!nesneMi(kendi)) return null;
  const okunamayan = liste<string>(kendi.okunamayan);
  const d: Nesne = nesneMi(denetim) ? denetim : {};
  if (denetim !== null && !nesneMi(denetim)) okunamayan.push(...DENETIM_KARTLARI);
  else okunamayan.push(...liste<string>(d.okunamayan));
  const i: Nesne = nesneMi(ikiDepo) ? ikiDepo : {};
  if (ikiDepo !== null && !nesneMi(ikiDepo)) okunamayan.push("iki_depo");
  else okunamayan.push(...liste<string>(i.okunamayan));
  return {
    butunluk: liste<ButunlukBulgusu>(d.butunluk),
    geri_yukleme: (d.geri_yukleme as GeriYuklemeOzeti | null | undefined) ?? null,
    iki_depo: ikiDepoFarki(
      i.iki_depo as IkiDepoKaydi | null | undefined,
      liste<IkiDepoHesabi>(d.muhru_tutmayan),
    ),
    eksik_ekler: liste<EksikEk>(d.eksik_ekler),
    kagit_capasi: (kendi.kagit_capasi as KagitCapasi | null | undefined) ?? null,
    son_girisler: liste<string>(kendi.son_girisler),
    parola_yenilenme: (kendi.parola_yenilenme as ParolaYenilenme | null | undefined) ?? null,
    okunamayan,
  };
}

/**
 * Sahipsiz kaydın silinmesinden dönen iki depo kartını bileşik duruma yazar: mührü tutmayan
 * hesaplar (denetim kartlarından) korunur, iki depo kartının okunamayan adı yenilenir.
 */
export function ikiDepoyuBirlestir(durum: ButunlukDurumu, yanit: unknown): ButunlukDurumu {
  const y: Nesne = nesneMi(yanit) ? yanit : {};
  return {
    ...durum,
    iki_depo: ikiDepoFarki(
      y.iki_depo as IkiDepoKaydi | null | undefined,
      durum.iki_depo?.muhru_tutmayan ?? [],
    ),
    okunamayan: [
      ...durum.okunamayan.filter((ad) => ad !== "iki_depo"),
      ...(nesneMi(yanit) ? liste<string>(y.okunamayan) : ["iki_depo"]),
    ],
  };
}

/**
 * Denetim kartları ucunun güncel yanıtını ("Gördüm"den dönen) bileşik duruma yazar: bütünlük,
 * geri yükleme, mührü tutmayan hesaplar ve eksik ekler yenilenir; iki depo kaydı (yalnız program
 * yöneticisi) korunur, denetim kartlarının okunamayan adları yenilenir. Yanıt nesne değilse denetim kartları
 * okunamamış sayılır (uyarı sessizce kaybolmaz).
 */
export function denetimiBirlestir(durum: ButunlukDurumu, yanit: unknown): ButunlukDurumu {
  const y: Nesne = nesneMi(yanit) ? yanit : {};
  const iki = durum.iki_depo;
  // İki depo kaydının kendisi (mührü tutmayanlar dışında); `fark_var`ı sunucunun kuralıyla.
  const kayit: IkiDepoKaydi | null =
    iki === null
      ? null
      : {
          fark_var:
            iki.sarmalsiz_hesaplar.length > 0 ||
            iki.silinebilir_sarmallar.length > 0 ||
            (iki.ozeti_tutmayan_hesaplar?.length ?? 0) > 0,
          sarmalsiz_hesaplar: iki.sarmalsiz_hesaplar,
          silinebilir_sarmallar: iki.silinebilir_sarmallar,
          ozeti_tutmayan_hesaplar: iki.ozeti_tutmayan_hesaplar ?? [],
        };
  const denetimAdlari: readonly string[] = DENETIM_KARTLARI;
  return {
    ...durum,
    butunluk: liste<ButunlukBulgusu>(y.butunluk),
    geri_yukleme: (y.geri_yukleme as GeriYuklemeOzeti | null | undefined) ?? null,
    iki_depo: ikiDepoFarki(kayit, liste<IkiDepoHesabi>(y.muhru_tutmayan)),
    eksik_ekler: liste<EksikEk>(y.eksik_ekler),
    okunamayan: [
      ...durum.okunamayan.filter((ad) => !denetimAdlari.includes(ad)),
      ...(nesneMi(yanit) ? liste<string>(y.okunamayan) : DENETIM_KARTLARI),
    ],
  };
}

export const butunlukApi = {
  /** Oturumdaki hesabın kendi kartları (her rol; kullanıcı eylemi değil). */
  kendiKartlari: () => api.get<KendiKartlari>(BUTUNLUK_YOLU, { etkinlik: false }),
  /** Denetim kartları (program yöneticisi ve Denetleme Kurulu; kullanıcı eylemi değil). */
  denetimKartlari: () => api.get<DenetimKartlari>(DENETIM_KARTLARI_YOLU, { etkinlik: false }),
  /** İki depo kartı (yalnız program yöneticisi; kullanıcı eylemi değil). */
  ikiDepo: () => api.get<IkiDepoYaniti>(IKI_DEPO_YOLU, { etkinlik: false }),
  /**
   * Kartların bileşik durumu: YALNIZ rolün açabildiği uçlar çağrılır (`yetki`). Bir uç
   * düşerse hepsi düşer; çağıran "okunamadı" ya da kilit diye değerlendirir.
   */
  durum: async (yetki: ButunlukYetkisi): Promise<ButunlukDurumu | null> => {
    const [kendi, denetim, ikiDepo] = await Promise.all([
      butunlukApi.kendiKartlari(),
      yetki.denetim ? butunlukApi.denetimKartlari() : Promise.resolve(null),
      yetki.ikiDepo ? butunlukApi.ikiDepo() : Promise.resolve(null),
    ]);
    return birlestir(kendi, denetim, ikiDepo);
  },
  /**
   * Program yöneticisinin onayıyla güvenlik dosyasında kalan sahipsiz parola kayıtlarını
   * siler (her biri `HESAP` satırı). Onaydan sonra fark değiştiyse 400. Yanıt güncel iki
   * depo kartıdır (`ikiDepoyuBirlestir`).
   */
  sahipsizSarmallariSil: (hesaplar: string[]) =>
    api.post<SahipsizSarmalSonucu>(SAHIPSIZ_SARMAL_YOLU, { hesaplar }),
  /** Oturumdaki hesabın parola yenilenme bildirimi (kullanıcı eylemi değil). */
  parolaBildirimi: () => api.get<ParolaBildirimiYaniti>(PAROLA_BILDIRIMI_YOLU, { etkinlik: false }),
  /** "Gördüm": bildirim izli bir yazımla kapanır; yanıt güncel bildirimdir (null). */
  parolaBildiriminiGordum: () => api.post<ParolaBildirimiYaniti>(PAROLA_BILDIRIMI_YOLU, {}),
  /**
   * Geri yükleme kartının "Gördüm"ü (yalnız Denetleme Kurulu): `seq` kartın gösterdiği son geri
   * yüklemedir. Kart herkes için kalkar (bir üye yeter); aynı geri yüklemeye ikinci "Gördüm" bir
   * şey yazmaz (200). Eski ya da olmayan `seq` 409 `geri_yukleme_guncel_degil`. Yanıt güncel
   * denetim kartlarıdır (`denetimiBirlestir`).
   */
  geriYuklemeyiGordum: (seq: number) =>
    api.post<DenetimKartlari>(GERI_YUKLEME_GORDUM_YOLU, { seq }),
};
