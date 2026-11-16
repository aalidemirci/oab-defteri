// Genel Kurul ekranı (plan F2 §6.1; tasarım §5.2.3, §7.1). Gezinmededir, her role okumaya açıktır (M3:
// yazma program yöneticisi ve yönetim kurulu rolleri — tasarım §7.1'in "Kim"iyle daraltılmış —, okul
// müdürü yalnız kendi yazıları; Denetleme Kurulu ve öteki roller okur). Liste en yeni genel kurul
// üstte; satır seçilince ayrıntı ve sihirbaz açılır (`?kurul=<kimlik>`; başka ekranlar doğrudan bağlanır).
//
// Planlama `genel_kurul_yazma`'dadır. Açık birlik döneminin kural sürümü genel kurul kurallarını
// taşımıyorsa (U1) planlamadan önce Birlik Dönemi'ndeki kural sürümü güncellemesine götürülür; bu bir
// hesap bütünlüğü koşuludur (kural bulunmadan hesap yapılamaz). Planlamanın bilgi satırları (öğrenci
// mevcudu ve tarihi, veli listesi önerisi) sunucunundur.

import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import EmptyState from "../../ui/EmptyState";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import GenelKurulAyrintisi from "./GenelKurulAyrintisi";
import { PlanlaPenceresi } from "./Pencereler";
import { genelKurulApi } from "./api";
import type { GenelKurulListesi, GenelKurulOzeti } from "./api";
import {
  DUGME_PLANLA,
  DURUM_TR,
  GENEL_KURULLAR_OKUNAMADI,
  GENEL_KURUL_ACIKLAMASI,
  GENEL_KURUL_BASLIGI,
  GENEL_KURUL_YOK,
  GENEL_KURUL_YOK_ACIKLAMASI,
  KURAL_SURUMU_AC,
  KURAL_SURUMU_GUNCELLENMELI,
  KURAL_SURUMU_GUNCELLENMELI_BASVURUN,
  LISTE_BASLIGI,
  PLANLAMA_BILGILERI_BASLIGI,
  SUTUN_BIRINCI_TOPLANTI,
  SUTUN_DURUM,
  SUTUN_TUR,
  TUR_TR,
  genelKurulAdi,
} from "./metinler";
import { BilgiSatirlari } from "./ortak";

/** Genel Kurul ekranının adresi. */
export const GENEL_KURUL_ADRESI = "/genel-kurul";

/** Genel kurulun ekrandaki adresi (`?kurul=`). */
export function genelKurulAdresi(id: number): string {
  return `${GENEL_KURUL_ADRESI}?kurul=${id}`;
}

/** Genel kurul ekranında yazma yeteneklerinden biri açık mı? (Yoksa salt okur notu çizilir.) */
const YAZMA_YETENEKLERI = [
  "genel_kurul_yazma",
  "genel_kurul_cagri",
  "genel_kurul_evraki",
  "genel_kurul_dosya_eki",
  "genel_kurul_iptal",
  "mudur_genel_kurul_yazisi",
  "dk_genel_kurul_yazma",
] as const;

export default function GenelKurulPage() {
  const yetki = useYetki();
  const [params, setParams] = useSearchParams();
  const [liste, setListe] = useState<GenelKurulListesi | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [planla, setPlanla] = useState(false);
  const [yenile, setYenile] = useState(0);
  const seciliHam = params.get("kurul");
  const secili = seciliHam && /^\d+$/.test(seciliHam) ? Number(seciliHam) : null;

  useEffect(() => {
    let iptal = false;
    genelKurulApi
      .liste()
      .then((l) => {
        if (iptal) return;
        setListe(l);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, GENEL_KURULLAR_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const tazele = useCallback(() => setYenile((y) => y + 1), []);
  const sec = useCallback(
    (id: number | null) =>
      setParams(
        (p) => {
          const yeni = new URLSearchParams(p);
          if (id === null) yeni.delete("kurul");
          else yeni.set("kurul", String(id));
          return yeni;
        },
        { replace: false },
      ),
    [setParams],
  );

  const planlayabilir = yetki.acik("genel_kurul_yazma");
  // Kural sürümü güncellemesinin bölümü yalnız bu yetenekte çizilir; öteki planlayıcıya yol öğütlenmez.
  const guncelleyebilir = yetki.acik("kural_surumu_guncelleme");
  const yazabilir = YAZMA_YETENEKLERI.some((y) => yetki.acik(y));
  const guncellenmeli = liste?.kural_surumu_guncellenmeli ?? false;

  const sutunlar: Column<GenelKurulOzeti>[] = [
    { header: SUTUN_TUR, cell: (k) => TUR_TR[k.kind] },
    { header: SUTUN_BIRINCI_TOPLANTI, cell: (k) => formatDateTime(k.first_meeting_at) },
    { header: SUTUN_DURUM, cell: (k) => DURUM_TR[k.status] },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{GENEL_KURUL_BASLIGI}</h1>
          <p className="od-page-description">{GENEL_KURUL_ACIKLAMASI}</p>
        </div>
        {secili === null && planlayabilir && liste !== null && !guncellenmeli && (
          <Button icon="event" onClick={() => setPlanla(true)}>
            {DUGME_PLANLA}
          </Button>
        )}
      </div>

      {!yazabilir && yetki.durum === "hazir" && <SaltOkurNotu />}
      {hata && <ErrorBand hata={hata} />}

      {secili !== null ? (
        <GenelKurulAyrintisi
          key={secili}
          kurulId={secili}
          onListeyeDon={() => sec(null)}
          onDegisti={tazele}
        />
      ) : liste === null ? (
        !hata && <SkeletonList rows={4} />
      ) : (
        <>
          {planlayabilir && guncellenmeli && (
            <div
              role="alert"
              className="flex items-start gap-3 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
            >
              <Icon name="rule" size="lg" className="mt-0.5 shrink-0" />
              <div className="min-w-0 space-y-1">
                <p className="text-body-medium">
                  {guncelleyebilir
                    ? KURAL_SURUMU_GUNCELLENMELI
                    : KURAL_SURUMU_GUNCELLENMELI_BASVURUN}
                </p>
                {guncelleyebilir && (
                  <Link
                    to="/birlik-donemi"
                    className="inline-flex text-label-large underline underline-offset-2"
                  >
                    {KURAL_SURUMU_AC}
                  </Link>
                )}
              </div>
            </div>
          )}
          {planlayabilir && (
            <BilgiSatirlari
              bilgiler={liste.planlama_bilgileri}
              baslik={PLANLAMA_BILGILERI_BASLIGI}
            />
          )}
          {liste.kayitlar.length === 0 ? (
            <EmptyState
              icon="how_to_vote"
              title={GENEL_KURUL_YOK}
              // U1: kural sürümü güncellenmeden genel kurul planlanmaz; "planlayarak başlayın"
              // öğüdü bantla çelişmesin diye o durumda verilmez (11b'nin notu).
              description={planlayabilir && !guncellenmeli ? GENEL_KURUL_YOK_ACIKLAMASI : undefined}
            />
          ) : (
            <section aria-labelledby="gk-listesi" className="space-y-3">
              <h2 id="gk-listesi" className="text-title-medium text-on-surface">
                {LISTE_BASLIGI}
              </h2>
              <DataTable<GenelKurulOzeti>
                columns={sutunlar}
                rows={liste.kayitlar}
                caption={LISTE_BASLIGI}
                onRowClick={(k) => sec(k.id)}
                rowLabel={(k) =>
                  `${genelKurulAdi(k.kind, formatDateTime(k.first_meeting_at))} kaydını aç`
                }
              />
            </section>
          )}
        </>
      )}

      {planla && (
        <PlanlaPenceresi
          onKapat={() => setPlanla(false)}
          onKaydedildi={(sonuc) => {
            setPlanla(false);
            tazele();
            if (sonuc !== null) sec(sonuc.genel_kurul.id);
          }}
        />
      )}
    </div>
  );
}
