// Genel Bakış → Yıllık İş Takvimi sekmesi (plan F2 §6.1; tasarım §7.10; M9: her rol okur). Veri E14'ün
// kaynağıdır (`GET terms/<pk>/annual-calendar/`, backend `genel_kurul_evraki.yillik_is_takvimi`):
// süre kurallarının satırları (madde atfıyla; kural kimliği yüzeye çıkmaz, sözlük §2) ve okulun planı.
// Kişisizdir, okuma yazmaz. Görünüm yıl (ay ay gruplanmış) ya da tek ay; günü göreli ya da kesinleşmemiş
// satır ("toplantı gününden en az 15 gün önce", "………") ayrı listededir. Kural paketi okunamazsa sunucu
// satırları boş verir (D1). E14'ün basımı F1c'nin evrak kartıyladır (PDF ve Excel; üretimi yalnız
// `yillik_is_takvimi_uretme`'de ve açık birlik döneminde — hazırlıktaki dönemin takvimi yazılmaz).

import { useEffect, useMemo, useState } from "react";

import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import EvrakKarti from "../evrak/EvrakKarti";
import { E14_ADI } from "../evrak/metinler";
import { birlikDonemiApi } from "../birlik-donemi/api";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { varsayilanDonem } from "../organlar/donem";
import { useYetki } from "../oturum/yetki";
import { Dayanak } from "../uyum/UyariGerekce";
import { panelApi } from "./api";
import type { YillikTakvim } from "./api";
import {
  ALAN_AY,
  ALAN_GORUNUM,
  ALAN_TAKVIM_DONEMI,
  GORUNUM_AY,
  GORUNUM_YIL,
  TAKVIM_ACIKLAMASI,
  TAKVIM_AY_BOS,
  TAKVIM_BOS,
  TAKVIM_DONEM_YOK,
  TAKVIM_KAYNAK,
  TAKVIM_OKUNAMADI,
  TAKVIM_UYARILARI,
  TARIHSIZ_ISLER,
  ayBasligi,
} from "./metinler";

/** Takvimin bir satırı (iki bölüm tek listede; bölüm adı satırda). */
export interface TakvimSatiri {
  tarih: string;
  is: string;
  bolum: string;
  atif: string | null;
  kaynak: string | null;
  /** Satırın ilk günü (gg.aa.yyyy); göreli ya da boş tarihte null. */
  gun: { yil: number; ay: number; gun: number } | null;
}

/** Tarih metninin ilk günü: "20.10.2026", "01.09.2026 – 30.01.2027" → 2026-10-20; göreli metin null. */
export function ilkGun(tarih: string): TakvimSatiri["gun"] {
  const m = /^(\d{2})\.(\d{2})\.(\d{4})/.exec(tarih.trim());
  if (!m) return null;
  return { yil: Number(m[3]), ay: Number(m[2]) - 1, gun: Number(m[1]) };
}

export function takvimSatirlari(takvim: YillikTakvim): TakvimSatiri[] {
  const [kuralBolumu = "", planBolumu = ""] = takvim.bolumler;
  const satirlar: TakvimSatiri[] = [
    ...takvim.kural_satirlari.map((s) => ({
      tarih: s.tarih,
      is: s.is,
      bolum: kuralBolumu,
      atif: s.atif || null,
      kaynak: null,
      gun: ilkGun(s.tarih),
    })),
    ...takvim.plan_satirlari.map((s) => ({
      tarih: s.tarih,
      is: s.is,
      bolum: planBolumu,
      atif: null,
      kaynak: s.kaynak || null,
      gun: ilkGun(s.tarih),
    })),
  ];
  const sira = (s: TakvimSatiri) => (s.gun ? s.gun.yil * 10000 + s.gun.ay * 100 + s.gun.gun : 0);
  return satirlar.sort((a, b) => sira(a) - sira(b));
}

const ayAnahtari = (yil: number, ay: number) => `${yil}-${String(ay + 1).padStart(2, "0")}`;

function SatirListesi({ satirlar, baslik }: { satirlar: TakvimSatiri[]; baslik: string }) {
  return (
    <ul aria-label={baslik} className="divide-y divide-outline-variant">
      {satirlar.map((s, i) => (
        <li key={`${i}-${s.is}`} className="grid gap-1 py-2 sm:grid-cols-[11rem_1fr]">
          <span className="break-words text-label-large text-on-surface">{s.tarih}</span>
          <span className="min-w-0 space-y-0.5">
            <span className="block break-words text-body-medium text-on-surface">{s.is}</span>
            <span className="flex flex-wrap gap-x-3 text-body-small text-on-surface-variant">
              <span>{s.bolum}</span>
              {s.atif && <Dayanak atif={s.atif} />}
              {s.kaynak && (
                <span>
                  {TAKVIM_KAYNAK}: {s.kaynak}
                </span>
              )}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function YillikIsTakvimi() {
  const yetki = useYetki();
  const [donemler, setDonemler] = useState<BirlikDonemi[] | null>(null);
  const [donemId, setDonemId] = useState<number | null>(null);
  const [takvim, setTakvim] = useState<YillikTakvim | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [gorunum, setGorunum] = useState<"YIL" | "AY">("YIL");
  const [ay, setAy] = useState<string>("");

  useEffect(() => {
    let iptal = false;
    birlikDonemiApi
      .donemler()
      .then((l) => {
        if (iptal) return;
        const acik = l.filter((d) => d.status !== "IPTAL");
        setDonemler(acik);
        setDonemId(varsayilanDonem(acik)?.id ?? null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, TAKVIM_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, []);

  useEffect(() => {
    if (donemId === null) return;
    let iptal = false;
    setTakvim(null);
    panelApi
      .yillikTakvim(donemId)
      .then((t) => {
        if (iptal) return;
        setTakvim(t);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, TAKVIM_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [donemId]);

  const satirlar = useMemo(() => (takvim ? takvimSatirlari(takvim) : []), [takvim]);
  const aylar = useMemo(() => {
    const harita = new Map<string, { yil: number; ay: number; satirlar: TakvimSatiri[] }>();
    for (const s of satirlar) {
      if (!s.gun) continue;
      const anahtar = ayAnahtari(s.gun.yil, s.gun.ay);
      const kayit = harita.get(anahtar) ?? { yil: s.gun.yil, ay: s.gun.ay, satirlar: [] };
      kayit.satirlar.push(s);
      harita.set(anahtar, kayit);
    }
    return [...harita.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [satirlar]);
  const tarihsiz = satirlar.filter((s) => !s.gun);
  // Seçilen ay bu dönemin aylarında yoksa (dönem değişti) ilk aya düşülür.
  const seciliAy = aylar.some(([anahtar]) => anahtar === ay) ? ay : (aylar[0]?.[0] ?? "");
  const donem = donemler?.find((d) => d.id === donemId);

  if (donemler !== null && donemler.length === 0) {
    return <p className="text-body-medium text-on-surface-variant">{TAKVIM_DONEM_YOK}</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-body-medium text-on-surface-variant">{TAKVIM_ACIKLAMASI}</p>
      {hata && <ErrorBand hata={hata} />}
      <div className="grid gap-3 sm:grid-cols-3">
        {donemler !== null && donemler.length > 1 && (
          <Select
            label={ALAN_TAKVIM_DONEMI}
            value={String(donemId ?? "")}
            onChange={(e) => {
              setDonemId(Number(e.target.value));
              setAy("");
            }}
            options={donemler.map((d) => ({ value: String(d.id), label: d.name }))}
          />
        )}
        <Select
          label={ALAN_GORUNUM}
          value={gorunum}
          onChange={(e) => setGorunum(e.target.value as "YIL" | "AY")}
          options={[
            { value: "YIL", label: GORUNUM_YIL },
            { value: "AY", label: GORUNUM_AY },
          ]}
        />
        {gorunum === "AY" && aylar.length > 0 && (
          <Select
            label={ALAN_AY}
            value={seciliAy}
            onChange={(e) => setAy(e.target.value)}
            options={aylar.map(([anahtar, a]) => ({
              value: anahtar,
              label: ayBasligi(a.ay, a.yil),
            }))}
          />
        )}
      </div>

      {takvim === null ? (
        !hata && <SkeletonList rows={5} />
      ) : (
        <>
          {takvim.uyarilar.length > 0 && (
            <div
              role="status"
              className="space-y-1 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
            >
              <p className="text-label-large">{TAKVIM_UYARILARI}</p>
              <ul className="list-disc space-y-0.5 pl-5 text-body-medium">
                {takvim.uyarilar.map((u) => (
                  <li key={u} className="break-words">
                    {u}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {satirlar.length === 0 ? (
            <p className="text-body-medium text-on-surface-variant">{TAKVIM_BOS}</p>
          ) : gorunum === "YIL" ? (
            <div className="space-y-4">
              {aylar.map(([anahtar, a]) => (
                <section key={anahtar} className="space-y-1">
                  <h3 className="text-title-small text-on-surface">{ayBasligi(a.ay, a.yil)}</h3>
                  <SatirListesi satirlar={a.satirlar} baslik={ayBasligi(a.ay, a.yil)} />
                </section>
              ))}
            </div>
          ) : (
            (() => {
              const secili = aylar.find(([anahtar]) => anahtar === seciliAy)?.[1];
              return secili ? (
                <SatirListesi
                  satirlar={secili.satirlar}
                  baslik={ayBasligi(secili.ay, secili.yil)}
                />
              ) : (
                <p className="text-body-medium text-on-surface-variant">{TAKVIM_AY_BOS}</p>
              );
            })()
          )}
          {tarihsiz.length > 0 && (
            <section className="space-y-1">
              <h3 className="text-title-small text-on-surface">{TARIHSIZ_ISLER}</h3>
              <SatirListesi satirlar={tarihsiz} baslik={TARIHSIZ_ISLER} />
            </section>
          )}
        </>
      )}

      {donem !== undefined && (
        <EvrakKarti
          key={`e14-${donem.id}`}
          donem={donem.id}
          kod="E14"
          baslik={E14_ADI}
          uretebilir={
            yetki.acik("yillik_is_takvimi_uretme") &&
            donem.status === "ACIK" &&
            donem.kural_kopyasi_tutuyor
          }
        />
      )}
    </div>
  );
}
