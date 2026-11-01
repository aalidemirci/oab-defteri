// Genel Bakış'ta "Okunamayan Kayıt Alanları" kartı (tasarım TK8 (3), §13 D48; plan F1b-1
// "Denetim izi").
//
// Kilit açıkken çözülemeyen şifreli alan düz metin diye dönmez: API'de `null` gelir,
// ekranda "okunamadı" yazar (`kisiler/ortak`). Sunucu bu süreçte okunan çözülemeyen alan
// sayısını güvenlik durumunda bildirir (`GET security/status/` → `corrupt_field_count`;
// program açıldığından beri, aynı alan bir kez sayılır). Sayı sıfırdan büyükse bu kart
// çıkar; sıfırsa, okunamazsa ya da durum okunamazsa hiçbir şey göstermez.
//
// KİŞİSİZDİR: yalnız sayı söylenir; hangi kaydın hangi alanı olduğu kartta yazmaz (sözlük
// §5). Nedenini kesin bilemez: kayıt program dışından değiştirilmiş (SQLite'ta şifreli
// sütuna yazılmış düz metin) ya da veritabanı bozulmuş olabilir; kart bunu söyler ve
// kaydı yeniden yazmadan önce bildirilmesini ister. Bütünlük (zincir) ve hesap mührü
// kartları denetim iziyle gelir; rol süzmesi 2. adımda, pano kabuğu F1c'de.

import { useEffect, useState } from "react";

import { formatNumber } from "../../lib/format";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { guvenlikApi } from "../guvenlik/api";

/** Kartın adı (docs/sozluk.md §4.5). */
export const OKUNAMAYAN_ALANLAR_BASLIGI = "Okunamayan Kayıt Alanları";

export default function OkunamayanAlanlarKarti() {
  const [sayi, setSayi] = useState(0);

  useEffect(() => {
    let iptal = false;
    guvenlikApi
      .durum()
      .then((d) => {
        if (!iptal) setSayi(d.corrupt_field_count ?? 0);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  if (sayi <= 0) return null;

  return (
    <section aria-labelledby="okunamayan-alanlar-karti">
      <Card elevation={0} className="p-5">
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg bg-error-container text-on-error-container">
            <Icon name="report" />
          </span>
          <div className="min-w-0 space-y-1">
            <h2
              id="okunamayan-alanlar-karti"
              className="text-title-medium font-semibold text-on-surface"
            >
              {OKUNAMAYAN_ALANLAR_BASLIGI}
            </h2>
            <p className="text-body-medium text-on-surface">
              Program açıldığından beri {formatNumber(sayi)} şifreli alan okunamadı; bu alanlar
              ekranda “okunamadı” diye görünür.
            </p>
            <p className="text-body-small text-on-surface-variant">
              Kayıt program dışından değiştirilmiş ya da veritabanı bozulmuş olabilir. Okunamayan
              alanı yeniden yazmadan önce program yöneticisine ve Denetleme Kuruluna bildirin;
              gerekirse sağlam bir yedekten geri yüklenir.
            </p>
          </div>
        </div>
      </Card>
    </section>
  );
}
