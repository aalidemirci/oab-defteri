// Oturum geçişleri — kilit ekranının, Kilitle'nin, parola değişiminin ve kurulumdaki ilk
// hesabın TEK yolu. Ekranlar uçları doğrudan çağırmaz, bu işlevleri çağırır: pencerenin
// yeniden yüklenip yüklenmeyeceği (tasarım §13 D53; plan F1b-1 "Oturum") tek yerde
// kararlaşır ve `lib/kilit.test.ts` onu burada sabitler.
//
// | Geçiş                                     | Pencere yeniden yüklenir mi?               |
// |-------------------------------------------|--------------------------------------------|
// | Kilit açma (`kilidiAc`)                   | evet (kilit ekranından açılış)             |
// | Kurtarma anahtarıyla açılış               | evet (kilit ekranından açılış)             |
// | Kilitle (`oturumuKilitle`)                | evet; uzun iş sürerken ertelenirse hayır   |
// | Kendi parolasını değiştirme               | hayır (hesap ve veri aynı)                 |
// | Kurulumdaki ilk hesap (`ilkHesabiKur`)    | hayır (sihirbaz anahtarı göstermeyi sürer) |
// | Boşta kilit süresi (`bostaKilitSuresini…`)| hayır (yalnız göstergenin süresi değişir)  |
//
// Boşta kilit ve 423 bu dosyada değildir: onları oturum yoklaması (`useOturum`) ve
// `lib/api.ts` görür, karar yine `lib/kilit.ts`'tedir.

import { ApiError } from "../../lib/api";
import { acildi, kilitlendi, oturumAcikSan } from "../../lib/kilit";
import { guvenlikApi } from "../guvenlik/api";
import type { IlkHesapGovdesi, IlkHesapSonucu } from "../guvenlik/api";
import { oturumApi } from "./api";
import type {
  BostaKilitSuresi,
  KilitAcmaGovdesi,
  KilitlemeSonucu,
  KurtarmaGovdesi,
  OturumOzeti,
} from "./api";

/**
 * Pencere yeniden yüklenmeden oturumun değiştiği an (kurulumdaki ilk hesap, ertelenen
 * Kilitle): oturum yoklaması (`useOturum`) bu olayla hemen yinelenir, üst çubuktaki
 * gösterge 15 sn'lik yoklamayı beklemez. Modüller arası iç olaydır; kullanıcı eylemi
 * sayılmaz.
 */
export const OTURUM_DEGISTI_OLAYI = "od:oturum-degisti";

function oturumDegistiYayinla(): void {
  window.dispatchEvent(new CustomEvent(OTURUM_DEGISTI_OLAYI));
}

/** Kilit ekranından açılış: başarıda pencere yeniden yüklenir (önceki hesabın belleği gider). */
export async function kilidiAc(govde: KilitAcmaGovdesi): Promise<OturumOzeti> {
  const ozet = await oturumApi.ac(govde);
  acildi();
  return ozet;
}

/** Kurtarma anahtarıyla açılış (yalnız program yöneticisi): başarıda pencere yeniden yüklenir. */
export async function kurtarmaAnahtariylaAc(govde: KurtarmaGovdesi): Promise<OturumOzeti> {
  const ozet = await oturumApi.kurtar(govde);
  acildi();
  return ozet;
}

/**
 * Kilitle. Sunucu uzun iş sürdüğü için kilidi ertelediyse (`sonuc: "ertelendi"`) pencere
 * yüklenmez, ekran "İşlem bitince kilitlenecek" der; iş bitince ilk istekte kilit
 * uygulanır ve yoklama onu görür. Öteki her sonuçta pencere yeniden yüklenir.
 *
 * Oturum bu arada kilitlenmişse (boşta süre doldu ya da güvenlik dosyası kayboldu) kilit
 * ucu 423 döner: kullanıcının istediği zaten olmuştur, pencere yine yüklenir ve `null`
 * döner (hata gösterilmez).
 */
export async function oturumuKilitle(): Promise<KilitlemeSonucu | null> {
  let sonuc: KilitlemeSonucu;
  try {
    sonuc = await oturumApi.kilitle();
  } catch (err) {
    if (err instanceof ApiError && err.status === 423) {
      kilitlendi("elle");
      return null;
    }
    throw err;
  }
  if (sonuc.sonuc === "ertelendi") oturumDegistiYayinla();
  else kilitlendi("elle");
  return sonuc;
}

/** Oturumdaki hesabın kendi parolası: pencere yeniden YÜKLENMEZ (oturum ve veri aynı). */
export function parolayiDegistir(parola: string, yeniParola: string): Promise<OturumOzeti> {
  return oturumApi.parolaDegistir(parola, yeniParola);
}

/**
 * Boşta kilit süresi (Ayarlar → Güvenlik; 3-30 dakika, tasarım TK14, D11): pencere
 * yeniden YÜKLENMEZ. Sunucu yeni süreyi bir sonraki istekte uygular; oturum özeti hemen
 * yeniden okunur ki üst çubuktaki geri sayım ve ipucu yeni süreyi göstersin.
 */
export async function bostaKilitSuresiniDegistir(dakika: number): Promise<BostaKilitSuresi> {
  const sonuc = await oturumApi.bostaKilitSuresiniYaz(dakika);
  oturumDegistiYayinla();
  return sonuc;
}

/**
 * Kurulumdaki ilk program yöneticisi hesabı: oturum bu hesapla açılır ama pencere
 * yeniden YÜKLENMEZ — sihirbaz kurtarma anahtarını göstermeyi sürdürür. Ön yüz bundan
 * sonra oturumu açık sanar: sonraki bir 423 kilitlenmedir.
 */
export async function ilkHesabiKur(govde: IlkHesapGovdesi): Promise<IlkHesapSonucu> {
  const sonuc = await guvenlikApi.kur(govde);
  oturumAcikSan(true);
  oturumDegistiYayinla();
  return sonuc;
}
