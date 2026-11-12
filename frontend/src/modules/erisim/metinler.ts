// Erişim Günlüğü ekranının metinleri — tek kaynak (sözlük §1 "Erişim günlüğü (F1b)", "Erişim
// Günlüğü ekranı (F1b)", §4.1). Türlerin görünen adları ve süzgeçlerin ret iletileri SUNUCUNUNDUR
// (`erisim_gunlugu.TUR_ADLARI`, `*_MESAJI`): ekran onları yanıttan olduğu gibi yazar. İç kodlar
// (tür kodu, model ve alan kodu: `okul.Personnel`, `first_name`) yüzeye çıkmaz (sözlük §2).
//
// KİŞİSİZDİR: hesap rol etiketi, tanıtıcı ve açılış/kapanış günüyle anılır ("Muhasip · tanıtıcı
// muhasip (açılış 01.11.2026, kapanış 03.11.2026)"; `butunluk/metinler.hesapEtiketiGunlu` ile
// aynı yazım): tanıtıcı yalnız açık hesaplar arasında tekildir, kapanan hesapla aynı tanıtıcıyı
// alan yeni hesap günleriyle ayrılır (orkestratör maddesi F-3).

import { formatNumber } from "../../lib/format";
import { hesapEtiketiGunlu } from "../butunluk/metinler";
import type { ErisimHesabi, ErisimSatiri } from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const ERISIM_GUNLUGU_BASLIGI = "Erişim Günlüğü";

/** Sayfanın açıklaması (sözlük §4.1). */
export const ERISIM_GUNLUGU_ACIKLAMASI =
  "Kişisel veriye dokunan hassas okumaların ve kişisel veri içeren çıktıların kaydı: hangi " +
  "hesapla, ne zaman ve hangi kayıt okundu. Okunan değer günlükte yoktur; günlüğü okumak iz " +
  "bırakmaz. En yeni kayıt üstte.";

/** Süzgeçlerin alanları ve seçenekleri. */
export const ALAN_BASLANGIC = "Başlangıç";
export const ALAN_BITIS = "Bitiş";
export const ALAN_TUR = "Tür";
export const ALAN_HESAP = "Hesap";
export const BUTUN_TURLER = "Bütün türler";
export const BUTUN_HESAPLAR = "Bütün hesaplar";
export const DUGME_TEMIZLE = "Süzgeçleri temizle";
/** Süzgeç bölgesinin erişilebilir adı. */
export const SUZGECLER = "Süzgeçler";

/** Tablonun erişilebilir adı ve sütunları. */
export const TABLO_ADI = "Erişim günlüğü kayıtları";
export const SUTUN_ZAMAN = "Zaman";
export const SUTUN_HESAP = "Hesap";
export const SUTUN_TUR = "Tür";
export const SUTUN_KAYIT = "Okunan kayıt";
export const SUTUN_CIKTI = "Çıktı";

/** Boş hâller. */
export const BOS_BASLIK = "Erişim günlüğünde kayıt yok";
export const BOS_ACIKLAMA =
  "Kişisel veriye dokunan hassas bir okuma ya da kişisel veri içeren bir çıktı henüz yok; böyle " +
  "bir işlem yapıldığında kaydı burada görünür.";
export const SUZGECE_UYAN_YOK = "Süzgeçlere uyan kayıt yok";
export const SUZGECE_UYAN_YOK_ACIKLAMA = "Süzgeçleri değiştirin ya da temizleyin.";

/** Okuma hatası (sunucunun iletisi yoksa). */
export const OKUNAMADI = "Erişim günlüğü okunamadı.";

/** Kaydı bulunamayan hesap (satırdaki rol okuma anınındır). */
export const HESAP_KAYDI_BULUNAMADI = "hesap kaydı bulunamadı";

/**
 * Model ve alan kodlarının ekrandaki adları (sözlük §1 "Erişim günlüğü (F1b)": o okumaları getiren
 * fazda eklenir). F1c: organ üyeliğindeki görev alma engelinin dayanağı (özel nitelikli alan).
 * Eşlemde olmayan kod yazılmaz.
 */
export const MODEL_ADLARI: Readonly<Record<string, string>> = {
  "oab.OrganMembership": "Organ üyeliği",
};
export const ALAN_ADLARI: Readonly<Record<string, string>> = {
  eligibility_bar_basis: "görev alma engelinin dayanağı",
};
/** Eşlemde adı olmayan model ya da alan (kod ekrana çıkmaz). */
export const BILINMEYEN_KAYIT_TURU = "Bilinmeyen kayıt türü";
export const BILINMEYEN_ALAN = "bilinmeyen alan";

function adi(eslem: Readonly<Record<string, string>>, kod: string, yedek: string): string {
  return Object.prototype.hasOwnProperty.call(eslem, kod) ? eslem[kod] : yedek;
}

/**
 * Okuyan hesabın anılışı: "Muhasip · tanıtıcı muhasip (açılış 01.11.2026)"; kaydı bulunamayan
 * hesapta satırdaki rol + "hesap kaydı bulunamadı".
 */
export function erisimHesabi(hesap: ErisimHesabi): string {
  if (hesap.tanitici === null) return `${hesap.rol_etiketi} · ${HESAP_KAYDI_BULUNAMADI}`;
  return hesapEtiketiGunlu(hesap);
}

/**
 * Okunan kaydın anılışı: kayıt türünün adı, kimliği ve alanın adı ("Personel · kimlik 7 · …");
 * model yoksa "—". Kod yazılmaz: eşlemde adı olmayan model ya da alan "bilinmeyen" diye yazılır.
 */
export function okunanKayit(satir: Pick<ErisimSatiri, "model" | "kayit" | "alan">): string {
  if (satir.model === null) return "—";
  const parcalar = [adi(MODEL_ADLARI, satir.model, BILINMEYEN_KAYIT_TURU)];
  if (satir.kayit !== null) parcalar.push(`kimlik ${satir.kayit}`);
  if (satir.alan !== null) parcalar.push(adi(ALAN_ADLARI, satir.alan, BILINMEYEN_ALAN));
  return parcalar.join(" · ");
}

/** Çıktının satır sayısı ("12 satır"); çıktı değilse "—". */
export function ciktiMetni(satir: Pick<ErisimSatiri, "satir_sayisi">): string {
  return satir.satir_sayisi === null ? "—" : `${formatNumber(satir.satir_sayisi)} satır`;
}
