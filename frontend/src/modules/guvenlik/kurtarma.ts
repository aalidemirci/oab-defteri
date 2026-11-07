// Kurtarma anahtarının istemci tarafı yardımcıları (tasarım §4.4.3; anahtarın PDF'i
// "Kurtarma anahtarı belgesi"dir, katalog dışı program belgesidir, E-kodu yoktur —
// tasarım §9.7).
//
// Anahtar SUNUCUDA SAKLANMAZ: kurulumda bir kez gösterilir; "saklandı mı"
// doğrulaması (iki grubu geri yazdırma) bu yüzden istemcide yapılır. Normalleştirme
// backend `app_password.normalize_recovery_key` ile AYNIDIR: Türkçe "İ" ve "ı"
// "I" olur, büyük harfe çevrilir, ASCII harf ve rakam dışındaki her şey (boşluk,
// tire) atılır, elle yazımda karışan 0→O, 1→I, 8→B düzeltilir (anahtar alfabesi
// A-Z ve 2-7'dir; 0, 1, 8, 9 yoktur). Türkçe klavyede büyük harfle yazılan "i"
// noktalı "İ" olur ve `toUpperCase` onu "I"ya çevirmez; eşleme bu yüzden önce
// yapılır. Anahtar Türkçe metin değildir: "i", "ı", "İ" hepsi "I" olmalıdır.
//
// Anahtarın KİMLİĞİ (no + üretim günü; tasarım TK10) sır değildir: belgede basılıdır,
// yedek listesi hangi anahtarın hangi yedeği açtığını onunla söyler. Ekrandaki biçimi
// buradaki iki yardımcıdan geçer (sözlük §1 "Kurtarma anahtarı").

import { useState } from "react";

import { dosyaAdi, saveBlob } from "../../lib/download";
import { formatDate, formatNumber, todayIso } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { oturumHataMetni } from "../oturum/hatalar";
import { guvenlikApi } from "./api";
import type { GuvenlikDurumu, KurtarmaKimligi } from "./api";

/** Anahtar dörtlü gruplardan oluşur (backend `RECOVERY_GROUP_SIZE`). */
export const GRUP_UZUNLUGU = 4;

/** Belgenin kullanıcıya görünen adı (sözlük §2; başlık yerinde de bu yazımla). */
export const KURTARMA_BELGESI_ADI = "Kurtarma anahtarı belgesi";

/**
 * Kaydedilen dosyanın adının kökü — backend `recovery_key_document.DOCUMENT_NAME` ile
 * BİREBİR ("Kurtarma Anahtarı Belgesi"; Content-Disposition ile aynı ad iner).
 */
export const KURTARMA_BELGESI_DOSYA_KOKU = "Kurtarma Anahtarı Belgesi";

export function kurtarmaAnahtariniNormallestir(deger: string): string {
  return deger
    .replace(/[İı]/g, "I")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .replace(/0/g, "O")
    .replace(/1/g, "I")
    .replace(/8/g, "B");
}

/** "ABCD-EFGH-…" → ["ABCD", "EFGH", …] (normalleştirilmiş). */
export function kurtarmaGruplari(anahtar: string): string[] {
  const sade = kurtarmaAnahtariniNormallestir(anahtar);
  const gruplar: string[] = [];
  for (let i = 0; i < sade.length; i += GRUP_UZUNLUGU) {
    gruplar.push(sade.slice(i, i + GRUP_UZUNLUGU));
  }
  return gruplar;
}

/**
 * Doğrulama için iki FARKLI grup sırası (0 tabanlı, artan). `rastgele` testte
 * sabitlenir; güvenlik amacı yoktur (sır değil, saklama denetimidir).
 */
export function rastgeleIkiGrup(
  adet: number,
  rastgele: () => number = Math.random,
): [number, number] {
  const birinci = Math.floor(rastgele() * adet) % adet;
  let ikinci = Math.floor(rastgele() * (adet - 1)) % (adet - 1);
  if (ikinci >= birinci) ikinci += 1;
  return birinci < ikinci ? [birinci, ikinci] : [ikinci, birinci];
}

/** Güvenlik durumundaki (ya da ilk hesap / yenileme yanıtındaki) güncel anahtarın kimliği. */
export function guncelKurtarmaKimligi(durum: GuvenlikDurumu): KurtarmaKimligi {
  // `?? null`: eski ya da eksik yanıtta alan hiç gelmeyebilir; kimlik yine null'la kurulur.
  return { no: durum.recovery_key_no ?? null, tarih: durum.recovery_key_date ?? null };
}

/**
 * Kimliğin kısa satırı: "Anahtar no 3 · üretim tarihi 01.11.2026". Biri yoksa yalnız
 * öteki yazılır; ikisi de yoksa null (ekran satırı hiç göstermez).
 */
export function kurtarmaKimligiMetni(kimlik: KurtarmaKimligi | null | undefined): string | null {
  if (!kimlik) return null;
  const parcalar: string[] = [];
  if (typeof kimlik.no === "number") parcalar.push(`Anahtar no ${formatNumber(kimlik.no)}`);
  if (kimlik.tarih) {
    const tarih = formatDate(kimlik.tarih);
    parcalar.push(parcalar.length > 0 ? `üretim tarihi ${tarih}` : `Üretim tarihi ${tarih}`);
  }
  return parcalar.length > 0 ? parcalar.join(" · ") : null;
}

/**
 * Yedeği hangi anahtarın açtığı (tasarım TK10: "bu yedek <no> numaralı, <tarih> tarihli
 * kurtarma anahtarıyla açılır"). Kimlik bilinmiyorsa (başlık yok ya da okunamıyor) bunu
 * açıkça söyler.
 */
export function yedekAnahtarCumlesi(kimlik: KurtarmaKimligi | null | undefined): string {
  const no = typeof kimlik?.no === "number" ? kimlik.no : null;
  const tarih = kimlik?.tarih ? formatDate(kimlik.tarih) : null;
  if (no !== null && tarih !== null) {
    return `Bu yedek ${formatNumber(no)} numaralı, ${tarih} tarihli kurtarma anahtarıyla açılır.`;
  }
  if (no !== null) return `Bu yedek ${formatNumber(no)} numaralı kurtarma anahtarıyla açılır.`;
  if (tarih !== null) return `Bu yedek ${tarih} tarihli kurtarma anahtarıyla açılır.`;
  return "Bu yedeği hangi kurtarma anahtarının açtığı okunamadı.";
}

/** Kaydedilen PDF'in adı: belge adı + YEREL tarih (backend `recovery_key_pdf_filename` ile aynı). */
export function kurtarmaBelgesiDosyaAdi(): string {
  return dosyaAdi([KURTARMA_BELGESI_DOSYA_KOKU, formatDate(todayIso())], "pdf");
}

/**
 * Kurtarma anahtarı belgesini (PDF) ister ve kaydeder. Backend anahtarı kurtarma sarmalına karşı
 * doğrular; yanlışsa Türkçe iletiyle 400 döner, dosya kaydedilmez. `indir` yalnız dosya kaydedilince
 * `true` döner: iptalde hata da yoktur, `false`tur; kart anahtar alanını boşaltmaz, bildirim
 * çıkmaz. Yazılamazsa `hata` iletiyi taşır.
 */
export function useKurtarmaBelgesi() {
  const [indiriliyor, setIndiriliyor] = useState(false);
  const [hata, setHata] = useState<string | null>(null);

  async function indir(anahtar: string): Promise<boolean> {
    setIndiriliyor(true);
    setHata(null);
    try {
      const pdf = await guvenlikApi.kurtarmaAnahtariPdf(anahtar);
      // Pencere son klasörde değil ev klasöründe açılır: anahtar şifreli yedeğin yanına önerilmez
      // (kullanıcı kararı 07.11.2026 "Hep ev klasöründe").
      const sonuc = await saveBlob(pdf, kurtarmaBelgesiDosyaAdi(), { evKlasorunde: true });
      if (sonuc === "hata") setHata(DOSYA_YAZILAMADI_ILETISI);
      return sonuc !== "hata" && sonuc !== "iptal";
    } catch (err) {
      setHata(oturumHataMetni(err, "Kurtarma anahtarı belgesi hazırlanamadı."));
      return false;
    } finally {
      setIndiriliyor(false);
    }
  }

  return { indir, indiriliyor, hata };
}
