// Genel Bakış'ın pano kalemlerinin metinleri — tek kaynak (tasarım §7.10; sözlük §1 "Genel Bakış pano
// kalemleri (F1c)", §4.5). Pano kişisizdir: metinlerde kişi adı geçmez, kişi ancak kalemin götürdüğü
// ekranda görünür. Kurulların adları açık yazılır ("yönetim kurulu", "Denetleme Kurulu"); kısaltma
// kullanıcı metnine çıkmaz. Salt okur rolde yazmayı öğütleyen cümle yoktur: kalem yalnız durumu söyler.

import { formatDate } from "../../lib/format";
import type { IsKodu, PanoKalemi } from "./api";

/** Bölüm başlıkları (Başlık Düzeni; sözlük §1 "Yazım"). */
export const HAFTA_BASLIGI = "Bu Hafta Yapılacaklar";
export const AY_BASLIGI = "Bu Ay Sizden Beklenenler";
export const HAFTA_ACIKLAMASI =
  "Son günü yedi gün içinde olan ya da geçmiş işler önde, süresi olmayan işler ardından.";
export const AY_ACIKLAMASI = "Bu ay sizden beklenen işler; son günü yaklaşan ya da geçmiş iş önde.";
export const HAFTA_BOS = "Bu hafta yapılacak iş yok.";
export const AY_BOS = "Bu ay sizden beklenen iş yok.";
export const TAMAMLANACAKLAR_BASLIGI = "Tamamlanacaklar";
export const TAMAMLANACAKLAR_ACIKLAMASI =
  "Kayıtlarda henüz girilmemiş bilgiler. Bilgi girilince satır kendiliğinden kapanır; gerekçe istemez.";
export const PANO_YUKLENIYOR = "Yapılacaklar yükleniyor";
export const PANO_OKUNAMADI = "Yapılacaklar okunamadı.";
export const YENIDEN_DENE = "Yeniden dene";

/** Kalemin son günü. */
export const SON_GUN_ETIKETI = "Son gün";
export const SURESI_DOLDU = "Süresi doldu";
export const EKSIK_ROZETI = "Eksik";

/** Kalem başlıkları. */
export const YK_GOREV_BOLUMU_BASLIGI = "Yönetim kurulunun görev bölümü";
export const DK_GOREV_BOLUMU_BASLIGI = "Denetleme Kurulunun görev bölümü";
export const GECIS_BASLIGI = "Geçiş kurulumu";
export const KURAL_SURUMU_BASLIGI = "Kural sürümü güncellemesi";
export const YK_YEDEK_BASLIGI = "Yönetim kurulunda yedek çağrısı";
export const DK_YEDEK_BASLIGI = "Denetleme Kurulunda yedek çağrısı";
export const YK_KADRO_BASLIGI = "Yönetim kurulunun kadrosu";
export const DK_KADRO_BASLIGI = "Denetleme Kurulunun kadrosu";
export const HESAP_ONERISI_BASLIGI = "Hesap önerisi";
export const YARIM_TASLAK_BASLIGI = "Yarım kalan taslak";

/** Görev bölümü kalemlerinin açıklaması (md. 12/3, 14/1; süre kural paketinden). */
export const YK_GOREV_BOLUMU_ACIKLAMASI =
  "Kurul oluştuktan sonra görev bölümü henüz yapılmadı: başkan, başkan yardımcısı, muhasip ve sekreter seçilir.";
export const DK_GOREV_BOLUMU_ACIKLAMASI =
  "Genel kuruldan sonra görev bölümü henüz yapılmadı: asıl üyeler aralarından bir başkan seçer.";

/** Geçiş kurulumunun açık adımları (backend `gecis.yol_haritasi_durumu`). */
export const GECIS_ADIMI_CUMLESI: Record<string, string> = {
  donem: "İlk birlik dönemi girilmedi.",
  kurul: "Görevdeki kurul girilmedi.",
  sayac_beyani: "Programdan önceki seçilme sayıları beyan edilmedi.",
  karar_defteri: "Karar defteri girilmedi.",
  tamamla: "“Geçiş kurulumu tamamlandı” işareti konmadı.",
};

/** Kural sürümü güncellemesi (F2; backend `kural_bagi.guncelleme_onerisi`; tasarım §6.2-5): programla açık
 * birlik döneminden daha yeni kural sürümü geldi. Kalem yalnız durumu söyler; geçiş farkı görülüp
 * onaylanınca yapılır ve kalem kendiliğinden düşer. */
export const KURAL_SURUMU_ACIKLAMASI =
  "Programla yeni bir kural sürümü geldi; açık birlik dönemi önceki sürümle hesaplanıyor.";

/** Hesap önerisindeki rolün adı (organ rolleri; sözlük §1 "Hesap"). */
export const ROL_ADI: Record<string, string> = {
  baskan: "Başkan",
  baskan_yardimcisi: "Başkan yardımcısı",
  muhasip: "Muhasip",
  sekreter: "Sekreter",
  denetleme_kurulu: "Denetleme Kurulu",
};

/** Aynı önerilerin tek kaleme toplandığı sayı (`ek.sayi`; yoksa 1). */
export function kalemSayisi(ek: PanoKalemi["ek"]): number {
  const sayi = Number(ek.sayi ?? 1);
  return Number.isInteger(sayi) && sayi > 1 ? sayi : 1;
}

/** "Başkan hesabı askıda: …" (backend `hesap_baglari.hesap_onerileri`; kişisiz). Aynı tür, rol ve
 * nedenli öneriler tek kalemdir; sayı birden çoksa cümle sayıyı söyler (aynı adlı bağlantı
 * yinelenmez). */
export function hesapOnerisiCumlesi(ek: PanoKalemi["ek"]): string {
  const rol = ROL_ADI[String(ek.rol)] ?? String(ek.rol);
  const sayi = kalemSayisi(ek);
  const askida = sayi > 1 ? `${rol} hesabı askıda (${sayi} hesap)` : `${rol} hesabı askıda`;
  const hesabin = sayi > 1 ? "Hesapların" : "Hesabın";
  if (ek.tur === "HESAP_KAPAT") {
    const neden =
      ek.neden === "GOREV_BOLUMU"
        ? "görev bölümünde görevi değişti"
        : "bağlı üyelik düştü ya da iptal edildi";
    return `${askida}: ${neden}. ${hesabin} kapatılması önerilir.`;
  }
  if (ek.tur === "HESAP_ASKIDAN_CIKAR") {
    return `${askida}, üyelik bağı yeniden geçerli. ${hesabin} askıdan çıkarılması önerilir.`;
  }
  const uyeye = sayi > 1 ? `Görevdeki ${sayi} üyeye` : "Görevdeki üyeye";
  return `${uyeye} hesap açılmadı (${rol}). Hesap açılması önerilir.`;
}

/** Denetleme Kurulunun yedek çağrısı: kural paketinin iletisi, birden çok üyede "(<n> üye)" ekiyle. */
export function yedekCagrisiCumlesi(kalem: Pick<PanoKalemi, "metin" | "ek">): string {
  const sayi = kalemSayisi(kalem.ek);
  return sayi > 1 ? `${kalem.metin} (${sayi} üye)` : kalem.metin;
}

/** Yarım metnin kutusu (bağlam; `useUyariGerekce(baglam)`, F1c 11. adım). Yedek çağrısı ve düşme
 * pencereleri iki kurulda da açılır: bağlamları kurulludur (backend `pano.TASLAK_EKRANLARI`). */
export const TASLAK_KUTUSU: Record<string, string> = {
  "gecis.devralinan": "Geçiş Kurulumu → görevdeki üye",
  "gecis.karar_defteri": "Geçiş Kurulumu → karar defteri",
  "gecis.sayac_beyani": "Geçiş Kurulumu → seçilme sayıları",
  "organlar.yk_gorev_bolumu": "Organlar → yönetim kurulunun görev bölümü",
  "organlar.yedek_cagrisi.yk": "Organlar → yönetim kurulunda yedek çağrısı",
  "organlar.yedek_cagrisi.dk": "Organlar → Denetleme Kurulunda yedek çağrısı",
  "organlar.dusme.yk": "Organlar → yönetim kurulunda üyeliğin düşmesi",
  "organlar.dusme.dk": "Organlar → Denetleme Kurulunda üyeliğin düşmesi",
  "organlar.dk_gorev_bolumu": "Organlar → Denetleme Kurulunun görev bölümü",
  "organlar.ogretmen_uye": "Organlar → öğretmen üye",
  "temsilciler.temsilci": "Temsilciler → temsilci",
};

/** "Organlar → yönetim kurulunun görev bölümü: gerekçe kutusunda kaydedilmemiş metin var." */
export function taslakCumlesi(baglam: string): string {
  return `${TASLAK_KUTUSU[baglam] ?? baglam}: gerekçe kutusunda kaydedilmemiş metin var.`;
}

// ---------------------------------------------------------------------------
// F2: genel kurul süreleri (plan F2 §6.3, 12. adım; backend `pano` "F2 kalemleri"). Süreler ve sınır
// günleri sunucunun kural paketinden okuduğu değerlerdir (`ek.son_gun`, `ek.ilan_gun`, `ek.sure_gun`);
// metinde sabit gün sayısı yoktur. Kişi adı yoktur; kalem genel kurulun ekranına götürür.
// ---------------------------------------------------------------------------
export const GK_OLAGAN_BASLIGI = "Olağan genel kurul";
export const GK_YENI_OKUL_BASLIGI = "Yeni açılan okulun ilk genel kurulu";
export const GK_ILAN_BASLIGI = "Genel kurulun ilanı";
export const GK_IKINCI_TOPLANTI_BASLIGI = "Genel kurulun ikinci toplantısı";
export const MUDUR_YAZISI_BASLIGI = "Okul müdürünün yazısı";
export const IBRA_BILDIRIMI_BASLIGI = "İbra edilmedi bildirimi";
export const DONEM_ONAYI_BASLIGI = "Yeni birlik döneminin açılışı";
/** TEFBİS takvim satırlarının başlıkları (yükümlülüğe göre; md. 23/5). */
export const TEFBIS_BASLIKLARI: Record<string, string> = {
  TEFBIS_YONETIM_BILGISI: "TEFBİS: yeni yönetimin bilgisi",
  TEFBIS_BANKA_BILGISI: "TEFBİS: banka hesap bilgileri",
  TEFBIS_BUTCE_GIRISI: "TEFBİS: tahmini bütçe",
};
export const TEFBIS_GIRISI_BASLIGI = "TEFBİS girişi";
/** Konum cümlesi (CLAUDE.md §1; sözlük §1 "TEFBİS"): TEFBİS kaleminin açıklamasının sonunda. */
export const TEFBIS_KONUMU = "Program TEFBİS'in yerine geçmez.";
/** Olağanüstü genel kurulda ikinci toplantı süresinin kaynağı (plan F2 §7 U10; atıf sunucudan). */
export const IKINCI_TOPLANTI_A1 =
  "md. 9/2 olağan genel kurulu düzenler; süre olağanüstü genel kurulda kullanıcı kararı A-1 ile uygulanır.";

/** İbra edilmedi bildirimi ve TEFBİS kalemleri süresizdir (mevzuatta süre yok): satırın işini yapan rol
 * (TEFBİS program yöneticisi, md. 23/5; ibra bildirimi program yöneticisi ve sekreter, md. 11/1-ç, 13/4;
 * yetenek `takvim_isareti`) işin yapıldığı günü kalemden girer, kalem düşer
 * (tasarım §7.10 "kalemin kapanması"; backend `uyum.takvim_satiri_yapildi`). */
export const YAPILDI_DUGMESI = "Yapıldı";
export const YAPILDI_PENCERESI_BASLIGI = "İşin yapıldığı gün";
export const YAPILDI_ACIKLAMASI =
  "İşin yapıldığı günü girin. Kayıt silinmez; işaretlenen iş listeden düşer ve bir daha değiştirilmez.";
export const ALAN_YAPILDIGI_GUN = "Yapıldığı gün";
export const YAPILDIGI_GUN_GEREKLI = "Yapıldığı günü girin.";
export const YAPILDI_KAYDEDILDI = "İş yapıldı olarak işaretlendi.";
export const YAPILDI_KAYDEDILEMEDI = "İş yapıldı olarak işaretlenemedi.";
export const YAPILDI_KAYDET = "Kaydet";
export const YAPILDI_VAZGEC = "Vazgeç";
export const YAPILDI_KAYDEDILIYOR = "Kaydediliyor…";

/** "Yapıldı" düğmesinin erişilebilir adı: "TEFBİS: tahmini bütçe — yapıldı olarak işaretle". */
export function yapildiDugmesiAdi(baslik: string): string {
  return `${baslik} — yapıldı olarak işaretle`;
}
/** İlan kanallarının adları (md. 9/3; `genel_kurul.ilan_kanallari` belirteçleri). */
export const ILAN_KANALI_ADI: Record<string, string> = {
  ELDEN_YAZILI: "elden yazılı bildirim",
  ILAN_PANOSU: "ilan panosu",
  INTERNET_SAYFASI: "internet sayfası",
};
/** Okul kartının tamamlanacağı: veri sorumlusu girilmedi (tasarım §9.6 E04; yalnız program yöneticisi). */
export const VERI_SORUMLUSU_TAMAMLANACAK =
  "Okul Bilgileri'nde veri sorumlusu girilmedi; kişisel veri aydınlatma metni bu bilgi olmadan oluşturulmaz.";

function gun(deger: PanoKalemi["ek"][string] | undefined): string {
  return deger ? formatDate(String(deger)) : "—";
}

/** Cümle içindeki sürenin dayanağı: " (md. 9/3)"; atıf yoksa boş (sunucunun `ek.ilan_atif`'i). */
function atifEki(atif: PanoKalemi["ek"][string] | undefined): string {
  return atif ? ` (${String(atif)})` : "";
}

/** Olağan genel kurul ve yeni açılan okulun ilk genel kurulu (md. 9/1): planlanmadı ya da birinci
 * toplantı sınırı aşıyor. Planlanmadıysa kalemin son günü sınırdaki toplantının ilanının son günüdür. */
export function genelKurulZamaniCumlesi(ek: PanoKalemi["ek"], yeniOkul: boolean): string {
  const son = gun(ek.son_gun);
  if (ek.durum === "SINIRI_ASIYOR") {
    return yeniOkul
      ? `Birinci toplantının günü, okulun açılışından sayılan son günü (${son}) aşıyor.`
      : `Birinci toplantının günü olağan genel kurulun son gününü (${son}) aşıyor.`;
  }
  const bas = yeniOkul
    ? "İlk genel kurul henüz planlanmadı. Okulun açılışından sayılan son toplantı günü:"
    : "Olağan genel kurul henüz planlanmadı. Toplantının son günü:";
  return `${bas} ${son}. Toplantı en az ${ek.ilan_gun} gün önce ilan edilir${atifEki(ek.ilan_atif)}; kalemin son günü ilanın son günüdür.`;
}

/** İlan (md. 9/3): ilan bekliyor ya da kanıt günü girilmemiş kanal. */
export function ilanCumlesi(ek: PanoKalemi["ek"]): string {
  const toplanti = ek.toplanti === "IKINCI" ? "İkinci toplantı" : "Birinci toplantı";
  if (ek.durum === "KANIT_EKSIK") {
    const kanallar = String(ek.eksik ?? "")
      .split(",")
      .filter(Boolean)
      .map((k) => ILAN_KANALI_ADI[k] ?? k)
      .join(", ");
    return `${toplanti}nın ilanında kanıt günü girilmemiş kanal: ${kanallar}.`;
  }
  return `${toplanti} henüz ilan edilmedi; ilan toplantıdan en az ${ek.ilan_gun} gün önce yapılır.`;
}

/** Yeter sayı sağlanamadı: ikinci toplantı (md. 9/2; ilan süresi md. 9/3). Olağanüstü genel kurulda
 * sürenin kullanıcı kararı A-1 ile uygulandığı söylenir (U10; `ek.olaganustu`). */
export function ikinciToplantiCumlesi(ek: PanoKalemi["ek"]): string {
  const bas = `Birinci toplantıda yeter sayı sağlanamadı. İkinci toplantı birinci toplantıdan en geç ${ek.sure_gun} gün içinde yapılır`;
  const cumle =
    Number(ek.tarihli) === 1
      ? `${bas}.`
      : `${bas}; tarihi ilk ilanda yoksa en az ${ek.ilan_gun} gün önce ilan edilir${atifEki(ek.ilan_atif)}.`;
  return Number(ek.olaganustu) === 1 ? `${cumle} ${IKINCI_TOPLANTI_A1}` : cumle;
}

/** Müdürün bekleyen yazısı (yalnız müdür): yeni okulun daveti ya da çağrı yazısı. Kalemin son günü
 * ilanın son günüdür (birinci toplantı − ilan süresi, md. 9/3; sunucunun `ek.ilan_gun`, `ek.ilan_atif`'i):
 * cümle bunu söyler; süre gelmediyse yalnız ilk cümle. */
export function mudurYazisiCumlesi(ek: PanoKalemi["ek"]): string {
  const bas =
    ek.tur === "YENI_OKUL_DAVETI"
      ? "Yeni açılan okulda genel kurulu okul müdürü davet eder; çağrı henüz kaydedilmedi."
      : "Çağrı kaydedildi; “Genel kurul toplantı çağrısı ve gündemi” belgesi henüz oluşturulmadı.";
  if (ek.ilan_gun === undefined || ek.ilan_gun === "") return bas;
  return `${bas} Toplantı en az ${ek.ilan_gun} gün önce ilan edilir${atifEki(ek.ilan_atif)}; kalemin son günü ilanın son günüdür.`;
}

/** Dönem onayı (U32): süresiz, yalnız program yöneticisi. */
export function donemOnayiCumlesi(ek: PanoKalemi["ek"]): string {
  return `Genel kurulun tutanağı tamamlandı; yeni birlik döneminin açılması onay bekliyor. Dönemin başlangıcı genel kurulun yapıldığı gün: ${gun(ek.baslangic)}.`;
}

/** Bilgi bantları. Kural kopyasının bandı Birlik Dönemi ekranınınkiyle aynı sözdür; bandın bağlantısı
 * Organlar ekranıyla ortak metindir (`organlar/metinler.ts` `DUGME_BIRLIK_DONEMINE_GIT`, "Birlik
 * Dönemi ekranını aç"): gidilen ekranı her rol okur, "aç" yazma eylemi diye okunmaz. */
export const DONEM_YOK_BILGISI =
  "Birlik dönemi açılmadı. Organlarla ilgili işler birlik dönemi açılınca burada görünür.";
export const DONEM_IPTAL_BILGISI =
  "Son birlik dönemi iptal edildi; açık birlik dönemi yok. Organlarla ilgili işler birlik dönemi açılınca burada görünür.";

/** Kalemin götürdüğü ekranın adı ("Organlar → Yönetim Kurulu"; sözlük §4.1, §4.3). */
const EKRAN_ADI: Record<string, string> = {
  "/organlar": "Organlar",
  "/temsilciler": "Temsilciler",
  "/kisiler": "Kişiler",
  "/birlik-donemi": "Birlik Dönemi",
  "/birlik-donemi/gecis-kurulumu": "Geçiş Kurulumu",
  "/kullanicilar": "Kullanıcılar",
  "/genel-kurul": "Genel Kurul",
  "/ayarlar": "Ayarlar",
};
const SEKME_ADI: Record<string, string> = {
  yk: "Yönetim Kurulu",
  dk: "Denetleme Kurulu",
  alim: "Alım Komisyonu",
  birlik: "Birlik Kişileri",
  okul: "Okul Bilgileri",
};

export function ekranAdi(kalem: Pick<PanoKalemi, "rota" | "sekme">): string {
  const ekran = EKRAN_ADI[kalem.rota] ?? kalem.rota;
  const sekme = SEKME_ADI[kalem.sekme];
  return sekme ? `${ekran} → ${sekme}` : ekran;
}

/** Kalemin başlığı. */
export function kalemBasligi(kalem: PanoKalemi): string {
  const dk = kalem.ek.organ === "DK";
  const basliklar: Record<IsKodu, string> = {
    YK_GOREV_BOLUMU: YK_GOREV_BOLUMU_BASLIGI,
    DK_GOREV_BOLUMU: DK_GOREV_BOLUMU_BASLIGI,
    GECIS_ADIMI: GECIS_BASLIGI,
    KURAL_SURUMU: KURAL_SURUMU_BASLIGI,
    YEDEK_CAGRISI: dk ? DK_YEDEK_BASLIGI : YK_YEDEK_BASLIGI,
    KADRO: dk ? DK_KADRO_BASLIGI : YK_KADRO_BASLIGI,
    HESAP_ONERISI: HESAP_ONERISI_BASLIGI,
    YARIM_TASLAK: YARIM_TASLAK_BASLIGI,
    GK_OLAGAN: GK_OLAGAN_BASLIGI,
    GK_YENI_OKUL: GK_YENI_OKUL_BASLIGI,
    GK_ILAN: GK_ILAN_BASLIGI,
    GK_IKINCI_TOPLANTI: GK_IKINCI_TOPLANTI_BASLIGI,
    MUDUR_YAZISI: MUDUR_YAZISI_BASLIGI,
    IBRA_BILDIRIMI: IBRA_BILDIRIMI_BASLIGI,
    TEFBIS_GIRISI: TEFBIS_BASLIKLARI[String(kalem.ek.yukumluluk)] ?? TEFBIS_GIRISI_BASLIGI,
    DONEM_ONAYI: DONEM_ONAYI_BASLIGI,
  };
  return basliklar[kalem.kod as IsKodu] ?? "";
}

/** Kalemin açıklaması: sunucunun kişisiz iletisi ya da kodun cümlesi. */
export function kalemAciklamasi(kalem: PanoKalemi): string {
  switch (kalem.kod) {
    case "YK_GOREV_BOLUMU":
      return YK_GOREV_BOLUMU_ACIKLAMASI;
    case "DK_GOREV_BOLUMU":
      return DK_GOREV_BOLUMU_ACIKLAMASI;
    case "GECIS_ADIMI":
      return GECIS_ADIMI_CUMLESI[String(kalem.ek.adim)] ?? "";
    case "KURAL_SURUMU":
      return KURAL_SURUMU_ACIKLAMASI;
    case "HESAP_ONERISI":
      return hesapOnerisiCumlesi(kalem.ek);
    case "YARIM_TASLAK":
      return taslakCumlesi(String(kalem.ek.baglam));
    case "YEDEK_CAGRISI":
      return yedekCagrisiCumlesi(kalem);
    case "GK_OLAGAN":
      return genelKurulZamaniCumlesi(kalem.ek, false);
    case "GK_YENI_OKUL":
      return genelKurulZamaniCumlesi(kalem.ek, true);
    case "GK_ILAN":
      return ilanCumlesi(kalem.ek);
    case "GK_IKINCI_TOPLANTI":
      return ikinciToplantiCumlesi(kalem.ek);
    case "MUDUR_YAZISI":
      return mudurYazisiCumlesi(kalem.ek);
    case "DONEM_ONAYI":
      return donemOnayiCumlesi(kalem.ek);
    case "TEFBIS_GIRISI":
      return `${kalem.metin} ${TEFBIS_KONUMU}`;
    default:
      return kalem.metin;
  }
}

/** "Tamamlanacaklar" satırının metni: uyum satırının iletisi ya da okul kartının satırı. */
export function tamamlanacakMetni(kalem: Pick<PanoKalemi, "kod" | "metin">): string {
  return kalem.kod === "VERI_SORUMLUSU" ? VERI_SORUMLUSU_TAMAMLANACAK : kalem.metin;
}

/** "Son gün 22.10.2026" ya da "Süresi doldu · 17.10.2026". */
export function vadeCumlesi(kalem: Pick<PanoKalemi, "vade" | "gecikti">): string {
  if (!kalem.vade) return "";
  const gun = formatDate(kalem.vade);
  return kalem.gecikti ? `${SURESI_DOLDU} · ${gun}` : `${SON_GUN_ETIKETI} ${gun}`;
}

// ---------------------------------------------------------------------------
// Genel Bakış'ın sekmeleri ve Yıllık İş Takvimi (F2 11b; plan F2 §6.1 M9: her rol okur, E14'ü
// program yöneticisi basar). Takvimin satırları E14'ün kaynağındandır (`genel_kurul_evraki.
// yillik_is_takvimi`): süre kuralları (madde atfıyla) ve okul planı. Kural kimliği yüzeye çıkmaz.
// ---------------------------------------------------------------------------

export const SEKME_OZET = "Özet";
export const SEKME_TAKVIM = "Yıllık İş Takvimi";
export const GENEL_BAKIS_SEKMELERI = "Genel Bakış bölümleri";
export const TAKVIM_ACIKLAMASI =
  "Birlik döneminin süreye bağlı işleri ve okulun planı. Süre kurallarının günü birlik döneminin " +
  "kural sürümünden ve kayıtlardan hesaplanır; günü kesinleşmemiş işler ayrıca listelenir.";
export const TAKVIM_DONEM_YOK =
  "Birlik dönemi açılmadı; yıllık iş takvimi birlik dönemine göre kurulur.";
export const TAKVIM_OKUNAMADI = "Yıllık iş takvimi okunamadı.";
export const ALAN_TAKVIM_DONEMI = "Birlik dönemi";
export const ALAN_GORUNUM = "Görünüm";
export const GORUNUM_YIL = "Yıl";
export const GORUNUM_AY = "Ay";
export const ALAN_AY = "Ay";
export const TAKVIM_AY_BOS = "Bu ayda iş yok.";
export const TAKVIM_BOS = "Takvimde iş yok.";
export const TARIHSIZ_ISLER = "Günü göreli ya da kesinleşmemiş işler";
export const TAKVIM_UYARILARI = "Takvimdeki boş yerler";
export const TAKVIM_KAYNAK = "Kaynak";

/** Ayların adları (ocak = 0). */
export const AY_ADLARI = [
  "Ocak",
  "Şubat",
  "Mart",
  "Nisan",
  "Mayıs",
  "Haziran",
  "Temmuz",
  "Ağustos",
  "Eylül",
  "Ekim",
  "Kasım",
  "Aralık",
] as const;

/** "Ekim 2026" */
export function ayBasligi(ay: number, yil: number): string {
  return `${AY_ADLARI[ay]} ${yil}`;
}
