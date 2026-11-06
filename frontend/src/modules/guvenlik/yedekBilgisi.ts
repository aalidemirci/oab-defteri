// Yedek listesinin ve dosya raporunun ekran metinleri (tasarım §4.4.7; plan F1b-3 "Ekran adları",
// "Eksik ve bozuk ekler kişisiz bilgiyle listelenir"). Sabit sözler `metinler.ts`'tedir; burada
// yalnız veriden kurulan satırlar durur.
//
// TÜR: yedek listesi tür alanı taşımaz, tür dosya adından türetilir. Desenler programın ürettiği
// adlardır (`denetim_izi._PROGRAM_YEDEGI`); elle adlandırılmış dosyada tür yazılmaz. F4'te gelen
// türlerin (`pre-anonim`, `pre-kapanis`, `pre-dek-yenileme`) adları F4'tedir.
//
// EK SATIRI konsoldakiyle aynı sırayı taşır (`geri_yukleme_ekleri.EkSatiri.metin`): durum, kayıt
// türü, kayıt no, yükleme tarihi, boy. Özgün dosya adı burada yoktur (R1): yalnız program açıkken,
// kaydın kendisinde ve Genel Bakış'taki bütünlük uyarısında görünür.

import { formatBoyut, formatDate, formatNumber } from "../../lib/format";
import type { DosyaSayilari, EkSatiri, YedekKapsami } from "./api";
import {
  EK_DURUMU_BOZUK,
  EK_DURUMU_EKSIK,
  EK_SORUNU_YOK,
  EK_TARIHI_YOK,
  EK_YEDEKTE_YOKTU,
  KAPSAM_TAM_METNI,
  KAPSAM_YEREL_METNI,
  YEDEK_TURU_GUNCELLEME,
  YEDEK_TURU_GUNLUK,
  YEDEK_TURU_KURULUM,
} from "./metinler";

/**
 * Yükleme kutusunun göndereceği en büyük yedek dosyası (kullanıcı kararı 06.11.2026 "1 GB üstü
 * şifreli yedek yükleme kutusundan açılır"). Kutu yalnız köprünün olmadığı geliştirme kipindedir;
 * Aç penceresinde seçilen dosya gönderilmez, bu sınır ona uygulanmaz. `desktop/server.py`
 * `AZAMI_ISTEK_GOVDESI` ile aynı değerdir; backend testi ikisini karşılaştırır.
 */
export const AZAMI_YEDEK_DOSYASI = 8 * 1024 ** 3;

const GUN = String.raw`\d{4}-\d{2}-\d{2}`;
const SURUM = String.raw`\d{1,4}\.\d{1,4}\.\d{1,4}(?:-(?:alpha|beta|rc|dev)(?:\.\d{1,4})?)?`;

const TURLER: readonly (readonly [RegExp, string])[] = [
  [new RegExp(`^gunluk-${GUN}\\.odbak$`), YEDEK_TURU_GUNLUK],
  [new RegExp(`^pre-migrate-${SURUM}-${GUN}\\.odbak$`), YEDEK_TURU_GUNCELLEME],
  [new RegExp(`^pre-parola-acilis-${GUN}-\\d{6}\\.odbak$`), YEDEK_TURU_KURULUM],
];

/** Yedeğin görünen türü; adı programın desenine uymuyorsa null (dosya başı notu). */
export function yedekTuru(ad: string): string | null {
  return TURLER.find(([desen]) => desen.test(ad))?.[1] ?? null;
}

/** Yedeğin kapsamının metni; okunamıyorsa null. */
export function kapsamMetni(kapsam: YedekKapsami | null): string | null {
  if (kapsam === "yerel") return KAPSAM_YEREL_METNI;
  if (kapsam === "tam") return KAPSAM_TAM_METNI;
  return null;
}

/** Listenin satırı: tür ve kapsam yan yana; ikisi de yoksa null. */
export function yedekAciklamasi(ad: string, kapsam: YedekKapsami | null): string | null {
  const parcalar = [yedekTuru(ad), kapsamMetni(kapsam)].filter((parca) => parca !== null);
  return parcalar.length > 0 ? parcalar.join(" · ") : null;
}

/** Yolun dosya adı; ekran Windows ve Pardus yolunu görür, iki ayraç da tanınır. */
export function yoldanDosyaAdi(yol: string): string {
  return yol.slice(Math.max(yol.lastIndexOf("/"), yol.lastIndexOf("\\")) + 1);
}

/** Şifreli yedeğin boy ve ek satırı; son denemede okunamayan parça yazılmaz, ikisi yoksa null. */
export function yedekBoyuSatiri(boyut: number | null, ekSayisi: number | null): string | null {
  const parcalar = [
    ...(boyut === null ? [] : [`Boy: ${formatBoyut(boyut)}`]),
    ...(ekSayisi === null ? [] : [`Taşıdığı ek: ${formatNumber(ekSayisi)}`]),
  ];
  return parcalar.length > 0 ? parcalar.join(" · ") : null;
}

/** Eksik ya da bozuk ekin kişisiz satırı (dosya başı notu). */
export function ekSatiriMetni(ek: EkSatiri): string {
  const durum = ek.durum === "bozuk" ? EK_DURUMU_BOZUK : EK_DURUMU_EKSIK;
  return [
    ek.yedekte_yoktu ? `${durum} (${EK_YEDEKTE_YOKTU})` : durum,
    ek.kayit_turu,
    ...(ek.kayit_no ? [`no ${ek.kayit_no}`] : []),
    ek.yukleme_tarihi ? formatDate(ek.yukleme_tarihi) : EK_TARIHI_YOK,
    formatBoyut(ek.boyut),
  ].join(" · ");
}

/** Yedek alınırken eksik kalan eklerin cümlesi; eksik ile bozuk ayrı sayılmaz (plan 05.11.2026). */
export function eksikEkCumlesi(sayi: number): string {
  return `${formatNumber(sayi)} ek ${EK_YEDEKTE_YOKTU}.`;
}

/**
 * Sayıların metni, sıfır olan yazılmaz (ekran kararı; sözlük §1 "Yedek"). İkinci onayla sürülen
 * geri yüklemede `onayla_suruldu` bozuk eklerin kendisidir (`geri_yukleme_ekleri.rapor`): aynı ekler
 * iki kez sayılmaz, yalnız onay parçasında yazılır.
 */
function sayilarMetni(sayilar: Omit<DosyaSayilari, "kapsam">): string {
  const parcalar = [
    [sayilar.yerine_konan, "ek yerine kondu"],
    [sayilar.yetimden_donen, "ek geri alındı"],
    [sayilar.eksik, "ek eksik"],
    [sayilar.bozuk - sayilar.onayla_suruldu, "ek bozuk"],
    [sayilar.onayla_suruldu, "bozuk ek onayla geride bırakıldı"],
  ] as const;
  const dolu = parcalar
    .filter(([sayi]) => sayi > 0)
    .map(([sayi, metin]) => `${formatNumber(sayi)} ${metin}`);
  return dolu.length > 0 ? dolu.join(" · ") : EK_SORUNU_YOK;
}

/** Yeniden başlat ekranının "Ekler" satırı: kişisiz sayılar. */
export function eklerSatiri(sayilar: DosyaSayilari): string {
  return `Ekler: ${sayilarMetni(sayilar)}`;
}

/**
 * Geri yükleme kartının "Ekler" satırı. Kart denetim izinin satırından okur: eski satır dosya
 * bilgisi taşımaz, biçimi tutmayan sayı satıra girmez. Sayılardan biri yoksa null: olmayan sayı
 * sıfır sayılıp "eksik ya da bozuk ek yok" denmez.
 */
export function eklerOzeti(sayilar: Partial<DosyaSayilari>): string | null {
  const { yerine_konan, yetimden_donen, eksik, bozuk, onayla_suruldu } = sayilar;
  if (
    yerine_konan === undefined ||
    yetimden_donen === undefined ||
    eksik === undefined ||
    bozuk === undefined ||
    onayla_suruldu === undefined
  ) {
    return null;
  }
  return sayilarMetni({ yerine_konan, yetimden_donen, eksik, bozuk, onayla_suruldu });
}
