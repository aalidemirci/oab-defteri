// Ayarlar'daki kural sürümü satırı (plan F1c kararları "kural sürümü F1c'de Ayarlar'da salt okunur";
// tasarım §4.4.2 Ayarlar satırı "kural sürümü seçimi"). Her rol görür (Ayarlar her rolde okunur). Sürüm
// SALT OKUNURDUR: her birlik dönemi açıldığı günkü kural sürümüyle hesaplanır; seçim ve fark ekranı bu
// karta eklenmez. Gösterilen dönem Birlik Dönemi ekranının varsayılanıdır (açık olan; yoksa iptal
// edilmemiş en yenisi). Dönemin kural kopyası doğrulanamıyorsa (D7) Birlik Dönemi'nin bandı yazılır.

import { useEffect, useState } from "react";

import Card from "../../ui/Card";
import { varsayilanDonem } from "../organlar/donem";
import { birlikDonemiApi } from "./api";
import type { BirlikDonemi } from "./api";
import {
  ALAN_KURAL_SURUMU,
  DONEMLER_OKUNAMADI,
  KURAL_KOPYASI_BOZUK,
  KURAL_SURUMU_AYARLAR_BASLIGI,
  KURAL_SURUMU_YARDIMI,
  kuralSurumuMetni,
} from "./metinler";
import { ILK_DONEM_BOS } from "../gecis-kurulumu/metinler";

export default function KuralSurumuKarti() {
  const [donem, setDonem] = useState<BirlikDonemi | null | undefined>(undefined);
  const [hata, setHata] = useState(false);

  useEffect(() => {
    let iptal = false;
    birlikDonemiApi
      .donemler()
      .then((liste) => {
        if (!iptal) setDonem(varsayilanDonem(liste) ?? null);
      })
      .catch(() => {
        if (!iptal) setHata(true);
      });
    return () => {
      iptal = true;
    };
  }, []);

  return (
    <section className="space-y-3">
      <h2 className="text-title-medium text-on-surface">{KURAL_SURUMU_AYARLAR_BASLIGI}</h2>
      <Card elevation={0} className="space-y-1 p-[var(--od-panel-padding)]">
        {hata ? (
          <p className="text-body-medium text-on-surface-variant">{DONEMLER_OKUNAMADI}</p>
        ) : donem === undefined ? null : donem === null ? (
          <p className="text-body-medium text-on-surface-variant">{ILK_DONEM_BOS}</p>
        ) : (
          <dl className="space-y-1">
            <dt className="text-label-medium text-on-surface-variant">{ALAN_KURAL_SURUMU}</dt>
            <dd className="break-words text-body-medium text-on-surface">
              {kuralSurumuMetni(donem.kural_paketi)} · {donem.name}
            </dd>
            <dd className="text-body-small text-on-surface-variant">{KURAL_SURUMU_YARDIMI}</dd>
            {!donem.kural_kopyasi_tutuyor && (
              <dd role="alert" className="text-body-small text-error">
                {KURAL_KOPYASI_BOZUK}
              </dd>
            )}
          </dl>
        )}
      </Card>
    </section>
  );
}
