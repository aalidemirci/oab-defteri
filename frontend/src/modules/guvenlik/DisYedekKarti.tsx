// Genel Bakış'ta "Şifreli Yedeği USB Belleğe Alın" kartı (tasarım §4.3 tehdit 18, §16 R6).
//
// Otomatik yedekler bu bilgisayardadır ve ekleri taşımaz: disk bozulur, bilgisayar değişir ya da
// program yeniden kurulursa onlar da, ekler de gider. Okulun elinde kalan tek kopya, Ayarlar →
// Güvenlik'ten USB belleğe kaydedilen şifreli yedektir; kayıtları, ekleri ve üretilen evrakı
// birlikte taşır (tasarım §4.4.7). Sunucu son kaydın tarihini veri klasöründe tutar
// (`GET backups/external/`); süre dolunca (varsayılan 30 gün; hiç kayıt yoksa ilk hesap kurulduktan
// 7 gün sonra) kart çıkar. Süre dolmadıysa, okunamazsa ya da hesap kurulmamışsa hiçbir şey
// göstermez.
//
// Dürüst dil: program dosyanın USB bellekte olduğunu bilemez, yalnız seçilen yere sağlam yazıldığını
// bilir; kart "son kayıt"ı söyler ve USB belleğe kaydetmeyi ister. Kişisel veri yok (yalnız tarih
// ve gün sayısı).

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { formatDate, formatNumber } from "../../lib/format";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { guvenlikApi } from "./api";
import type { DisYedekDurumu } from "./api";

/** Kartın adı (docs/sozluk.md §4) — başlık ve testler buradan okur. */
export const DIS_YEDEK_KARTI_BASLIGI = "Şifreli Yedeği USB Belleğe Alın";
/** Güvenlik sekmesinin adresi (Şifreli Yedek kartı orada). */
export const GUVENLIK_ADRESI = "/ayarlar?tab=guvenlik";

/** Kartın durum cümlesi — son kayıt ya da hiç kayıt olmadığı (gün sayısıyla). */
export function disYedekCumlesi(durum: DisYedekDurumu): string {
  if (durum.last_download) {
    const gun = durum.days_since ?? 0;
    return `Son şifreli yedek ${formatDate(durum.last_download)} tarihinde kaydedildi (${formatNumber(gun)} gün önce).`;
  }
  return "Bu bilgisayardan henüz şifreli yedek kaydedilmedi.";
}

/**
 * Hatırlatmanın durumu (Güvenlik → Şifreli Yedek kartı): süre dolduysa ne yapılacağı,
 * dolmadıysa Genel Bakış'ın kaç gün sonra hatırlatacağı. Hiç kayıt yokken ve süre
 * dolmamışken (parola yeni kurulmuş) `null` — ilk hatırlatmanın günü sunucudadır.
 */
export function disYedekHatirlatmaCumlesi(durum: DisYedekDurumu): string | null {
  if (durum.remind) {
    return "Hatırlatma süresi doldu: şifreli yedeği USB belleğe kaydedin.";
  }
  if (durum.last_download && durum.days_since !== null) {
    const kalan = Math.max(1, durum.reminder_days - durum.days_since);
    return `Genel Bakış ${formatNumber(kalan)} gün sonra yeniden hatırlatır.`;
  }
  return null;
}

export default function DisYedekKarti() {
  const [durum, setDurum] = useState<DisYedekDurumu | null>(null);

  useEffect(() => {
    let iptal = false;
    guvenlikApi
      .disYedek()
      .then((d) => {
        if (!iptal) setDurum(d);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  if (durum === null || !durum.remind) return null;

  return (
    <section aria-labelledby="dis-yedek-karti">
      <Card elevation={0} className="p-5">
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg bg-tertiary-container text-on-tertiary-container">
            <Icon name="save" />
          </span>
          <div className="min-w-0 space-y-1">
            <h2 id="dis-yedek-karti" className="text-title-medium font-semibold text-on-surface">
              {DIS_YEDEK_KARTI_BASLIGI}
            </h2>
            <p className="text-body-medium text-on-surface">{disYedekCumlesi(durum)}</p>
            <p className="text-body-small text-on-surface-variant">
              Programın her gün aldığı yedekler bu bilgisayardadır ve ekleri taşımaz; disk bozulursa
              onlar da, ekler ve üretilen evrak da gider. Şifreli yedek kayıtları, ekleri ve
              üretilen evrakı birlikte taşır: onu USB belleğe kaydedin ve belleği bilgisayardan ayrı
              saklayın.
            </p>
            <Link
              to={GUVENLIK_ADRESI}
              className="inline-flex pt-1 text-label-large text-primary underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              Ayarlar → Güvenlik&apos;i aç
            </Link>
          </div>
        </div>
      </Card>
    </section>
  );
}
