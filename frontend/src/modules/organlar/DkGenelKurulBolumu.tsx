// Organlar → Denetleme Kurulu sekmesinin genel kurul bölümü (plan F2 §6.1; M8 ⁵: yalnız Denetleme
// Kurulu, `dk_genel_kurul_yazma`). İki iş: md. 14/5'in olağanüstü genel kurul çağrısı ve Denetleme
// Kurulunun nihai raporunun genel kurula dosya eki (E33; md. 14/4).
//
// Çağrı: Denetleme Kurulu toplantının gününü ve yerini planlamaz (program yöneticisi ya da sekreter
// planlar; 7. adımın en dar seçimi); planlanmış olağanüstü genel kurula çağrıyı yazar. Pencere Genel
// Kurul'un çağrı penceresidir (`genel-kurul/CagriPenceresi`), yalnız Denetleme Kurulunun yoluyla:
// Yönetmeliğin 6. maddesine aykırılık işareti zorunlu, denetim raporu çağrıyla aynı istekte (U13; S6 (ii)
// sert). Seçenek sunucunundur (`oturum.cagiranlar`). Ek: gündeminde Denetleme Kurulu raporu maddesi olan,
// tutanağı tamamlanmamış genel kurullar.

import { useCallback, useEffect, useState } from "react";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import CagriPenceresi from "../genel-kurul/CagriPenceresi";
import { genelKurulApi } from "../genel-kurul/api";
import type { GenelKurul } from "../genel-kurul/api";
import {
  DK_CAGRI_ACIKLAMASI,
  DK_CAGRI_BASLIGI,
  DK_CAGRI_BOLUM_BASLIGI,
  DK_CAGRI_GENEL_KURUL_YOK,
  DK_RAPORU_EKI_ACIKLAMASI,
  DK_RAPORU_EKI_BASLIGI,
  DK_RAPORU_MADDESI_YOK,
  GENEL_KURULLAR_OKUNAMADI,
  genelKurulAdi,
} from "../genel-kurul/metinler";
import { Bolum, EkListesi } from "../genel-kurul/ortak";

const ACIK = new Set(["PLANLANDI", "CAGRILDI", "ILAN_EDILDI", "YETER_SAYI_YOK", "YAPILDI"]);

export default function DkGenelKurulBolumu() {
  const [kurullar, setKurullar] = useState<GenelKurul[] | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [cagri, setCagri] = useState<GenelKurul | null>(null);
  const [yenile, setYenile] = useState(0);
  const tazele = useCallback(() => setYenile((y) => y + 1), []);

  useEffect(() => {
    let iptal = false;
    genelKurulApi
      .liste()
      .then((l) =>
        Promise.all(
          l.kayitlar.filter((k) => ACIK.has(k.status)).map((k) => genelKurulApi.ayrinti(k.id)),
        ),
      )
      .then((ayrintilar) => {
        if (iptal) return;
        setKurullar(ayrintilar);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, GENEL_KURULLAR_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const cagrilabilir = (kurullar ?? []).filter((k) =>
    k.oturum.cagiranlar.some((c) => c.yol === "dk"),
  );
  const ekli = (kurullar ?? []).flatMap((k) =>
    k.gundem
      .filter((m) => m.kind === "DK_RAPORU" && !m.removed_by_vote)
      .map((m) => ({ kurul: k, madde: m })),
  );
  const ad = (k: GenelKurul) => genelKurulAdi(k.kind, formatDateTime(k.first_meeting_at));

  return (
    <div className="space-y-5">
      {hata && <ErrorBand hata={hata} />}
      <Bolum baslik={DK_CAGRI_BOLUM_BASLIGI} aciklama={DK_CAGRI_ACIKLAMASI}>
        {kurullar !== null &&
          (cagrilabilir.length === 0 ? (
            <p className="text-body-medium text-on-surface-variant">{DK_CAGRI_GENEL_KURUL_YOK}</p>
          ) : (
            <ul className="divide-y divide-outline-variant">
              {cagrilabilir.map((k) => (
                <li key={k.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <span className="min-w-0 break-words text-body-medium text-on-surface">
                    {ad(k)}
                  </span>
                  <Button icon="campaign" onClick={() => setCagri(k)}>
                    {DK_CAGRI_BASLIGI}
                  </Button>
                </li>
              ))}
            </ul>
          ))}
      </Bolum>
      <Bolum baslik={DK_RAPORU_EKI_BASLIGI} aciklama={DK_RAPORU_EKI_ACIKLAMASI}>
        {kurullar !== null &&
          (ekli.length === 0 ? (
            <p className="text-body-medium text-on-surface-variant">{DK_RAPORU_MADDESI_YOK}</p>
          ) : (
            <div className="space-y-4">
              {ekli.map(({ kurul, madde }) => (
                <EkListesi
                  key={madde.id}
                  baslik={ad(kurul)}
                  ekler={madde.ekler}
                  onEkle={async (dosya) => {
                    await genelKurulApi.dosyaEki(madde.id, dosya, true);
                    tazele();
                  }}
                />
              ))}
            </div>
          ))}
      </Bolum>
      {cagri !== null && (
        <CagriPenceresi
          kurul={cagri}
          yalnizYol="dk"
          onKapat={() => setCagri(null)}
          onKaydedildi={() => {
            setCagri(null);
            tazele();
          }}
        />
      )}
    </div>
  );
}
