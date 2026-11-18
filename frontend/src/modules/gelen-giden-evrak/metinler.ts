// Gelen-Giden Evrak ekranının metinleri — tek kaynak (sözlük §1 "Gelen-Giden Evrak ekranı (F2)", §4.1;
// plan F2 §6.1 M10; tasarım §5.2.8). Gelen-giden evrak defteri il/ilçe millî eğitim müdürlüğünce
// tasdiklidir (md. 23/1-2); program defterin yerine geçmez, deftere geçirilecek kaydı tutar.

import type { EvrakYonu, TasdikMakami } from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const GELEN_GIDEN_BASLIGI = "Gelen-Giden Evrak";
export const GELEN_GIDEN_ACIKLAMASI =
  "Birliğe gelen ve birlikten giden yazıların kaydı. Kayıt numarası her yıl birden başlar; numara " +
  "bir kez kullanılır. Okul müdürünün genel kurul yazısı programca giden evrak olarak işlenir; " +
  "programın hazırladığı resmî yazı Genel Kurul'daki belge kartından kaydedilir. Program gelen-" +
  "giden evrak defterinin yerine geçmez.";

/** Defter. */
export const DEFTER_YOK = "Gelen-giden evrak defteri kayıtlı değil";
export const DEFTER_YOK_ACIKLAMASI =
  "Birliğin tasdikli gelen-giden evrak defterini kaydedin; kayıtlar bu deftere numaralanır.";
export const DEFTERLER_OKUNAMADI = "Gelen-giden evrak defterleri okunamadı.";
export const ALAN_DEFTER = "Defter";
export const DUGME_DEFTER = "Defteri kaydet";
export const DEFTER_PENCERESI_BASLIGI = "Gelen-giden evrak defteri";
export const DEFTER_ACIKLAMASI =
  "Defter il/ilçe millî eğitim müdürlüğünce tasdik edilir (md. 23/2). Program kullanılmaya " +
  "başlanmadan önce deftere yazılmış son sıra no girilirse programın numaraları ondan sonra sürer.";
export const ALAN_TASDIK_MAKAMI = "Tasdik eden makam";
export const ALAN_TASDIK_GUNU = "Tasdik günü";
export const ALAN_TASDIK_NO = "Tasdik no";
export const ALAN_SAYFA_SAYISI = "Sayfa sayısı";
export const ALAN_SON_NO = "Programdan önceki son sıra no";
export const ALAN_ACILIS_GUNU = "Defterin açılış günü";
export const DEFTER_KAYDEDILDI = "Defter kaydedildi.";
export const DEFTER_KAYDEDILEMEDI = "Defter kaydedilemedi.";
export const DEFTER_DURUMU_TR: Record<string, string> = {
  KULLANIMDA: "Kullanımda",
  DOLDU: "Doldu",
  ARSIVDE: "Arşivde",
  IPTAL: "İptal edildi",
};
export const TASDIK_MAKAMI_TR: Record<TasdikMakami, string> = {
  IL_ILCE_MEM: "İl/ilçe millî eğitim müdürlüğü",
  NOTER: "Noter",
};

/** Süzgeçler ve tablo. */
export const ALAN_YIL = "Yıl";
export const ALAN_YON = "Yön";
export const BUTUN_YONLER = "Gelen ve giden";
export const YON_TR: Record<EvrakYonu, string> = { GELEN: "Gelen", GIDEN: "Giden" };
export const KAYITLAR_BASLIGI = "Kayıtlar";
export const KAYIT_YOK = "Bu süzgece uyan kayıt yok.";
export const KAYITLAR_OKUNAMADI = "Kayıtlar okunamadı.";
export const SUTUN_NO = "Sıra no";
export const SUTUN_YON = "Yön";
export const SUTUN_TARIH = "Tarih";
export const SUTUN_KARSI_TARAF = "Gönderen ya da gönderilen";
export const SUTUN_KONU = "Konu";
export const OKUNAMADI = "okunamadı";
export const SIRADAKI_NO = "Bu yılın sıradaki numarası";

/** Yeni kayıt ve ayrıntı. */
export const DUGME_YENI_KAYIT = "Yeni kayıt";
export const KAYIT_PENCERESI_BASLIGI = "Yeni evrak kaydı";
export const KAYIT_ACIKLAMASI =
  "Numara boş bırakılırsa defterin sıradaki numarası verilir. Sıra atlanırsa program gerekçe ister; " +
  "aynı numara ikinci kez kullanılmaz.";
export const ALAN_TARIH = "Tarih";
export const ALAN_KAYIT_NO = "Kayıt no";
export const ALAN_KARSI_TARAF = "Gönderen ya da gönderilen";
export const ALAN_KONU = "Konu";
export const ALAN_DIS_SAYI = "Yazının sayısı";
export const TARIH_GEREKLI = "Tarihi girin.";
export const KAYIT_EKLENDI = "Evrak kaydedildi.";
export const KAYIT_EKLENEMEDI = "Evrak kaydedilemedi.";
export const KAYIT_AYRINTISI_BASLIGI = "Evrak kaydı";
export const KAYIT_EKLERI = "Ekler";
export const KAYIT_EKI_YARDIMI = "Taranmış evrak (PDF, JPEG, PNG).";
export const PROGRAMIN_YAZISI = "Programın hazırladığı yazı";
export const DUGME_KAYDI_AC = "Kaydı aç";

/** "2026/14" */
export function kayitNo(yil: number, no: number): string {
  return `${yil}/${no}`;
}
