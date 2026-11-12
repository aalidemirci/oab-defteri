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

/** Hesap önerisindeki rolün adı (organ rolleri; sözlük §1 "Hesap"). */
export const ROL_ADI: Record<string, string> = {
  baskan: "Başkan",
  baskan_yardimcisi: "Başkan yardımcısı",
  muhasip: "Muhasip",
  sekreter: "Sekreter",
  denetleme_kurulu: "Denetleme Kurulu",
};

/** Aynı önerilerin tek kaleme toplandığı sayı (`ek.sayi`; yoksa 1). */
export function kalemSayisi(ek: Record<string, string | number>): number {
  const sayi = Number(ek.sayi ?? 1);
  return Number.isInteger(sayi) && sayi > 1 ? sayi : 1;
}

/** "Başkan hesabı askıda: …" (backend `hesap_baglari.hesap_onerileri`; kişisiz). Aynı tür, rol ve
 * nedenli öneriler tek kalemdir; sayı birden çoksa cümle sayıyı söyler (aynı adlı bağlantı
 * yinelenmez). */
export function hesapOnerisiCumlesi(ek: Record<string, string | number>): string {
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
};
const SEKME_ADI: Record<string, string> = {
  yk: "Yönetim Kurulu",
  dk: "Denetleme Kurulu",
  alim: "Alım Komisyonu",
  birlik: "Birlik Kişileri",
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
    YEDEK_CAGRISI: dk ? DK_YEDEK_BASLIGI : YK_YEDEK_BASLIGI,
    KADRO: dk ? DK_KADRO_BASLIGI : YK_KADRO_BASLIGI,
    HESAP_ONERISI: HESAP_ONERISI_BASLIGI,
    YARIM_TASLAK: YARIM_TASLAK_BASLIGI,
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
    case "HESAP_ONERISI":
      return hesapOnerisiCumlesi(kalem.ek);
    case "YARIM_TASLAK":
      return taslakCumlesi(String(kalem.ek.baglam));
    case "YEDEK_CAGRISI":
      return yedekCagrisiCumlesi(kalem);
    default:
      return kalem.metin;
  }
}

/** "Son gün 22.10.2026" ya da "Süresi doldu · 17.10.2026". */
export function vadeCumlesi(kalem: Pick<PanoKalemi, "vade" | "gecikti">): string {
  if (!kalem.vade) return "";
  const gun = formatDate(kalem.vade);
  return kalem.gecikti ? `${SURESI_DOLDU} · ${gun}` : `${SON_GUN_ETIKETI} ${gun}`;
}
