// Birlik Dönemi ekranı (plan F1c-11; tasarım §5.2.1 `OabTerm`, §7.9, T3). Her role okumaya açıktır
// (matrisin M1 satırı); yazma yalnız `birlik_donemi_yazma` yeteneğindedir (program yöneticisi).
//
// Gösterilen: birlik dönemleri (birden çoksa liste; satır seçilince ayrıntı), seçili dönemin bilgileri,
// kural sürümü (SALT OKUNUR; dönem açıldığı günkü sürümle hesaplanır, plan F1c kararları), dönem
// kilidi (kapanmış dönem salt okur, O2) ve kural kopyası doğrulanamadıysa D7 bandı (dönem salt okur
// açılır), görev süresi uyarıları (kaydedilmez, gerekçe istemez) ve geçiş kurulumunun durumu.
// Yazma: yanlış girilmiş geçiş döneminin iptali (gerekçe şifreli; "Geçiş kurulumu tamamlandı"
// işaretinden önce). Dönem açılışı geçiş kurulumunda ya da sihirbazdadır; F2'nin genel kurul yolu bu
// ekranda yoktur. Birlik dönemi yoksa organ ekranları da boş durum gösterir (plan F1c kararları).

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import EmptyState from "../../ui/EmptyState";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import IptalPenceresi from "../gecis-kurulumu/IptalPenceresi";
import { GECIS_DURUMU_TR, tamamlandiNotu } from "../gecis-kurulumu/metinler";
import { okulApi } from "../okul/api";
import type { SchoolYear } from "../okul/api";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import { Dayanak } from "../uyum/UyariGerekce";
import { atifAyir } from "../uyum/hatalar";
import { birlikDonemiApi } from "./api";
import type { AtifliUyari, BirlikDonemi, GecisOzeti } from "./api";
import {
  ACILIS_GECIS,
  ACILIS_GENEL_KURUL,
  ALAN_ACILIS,
  ALAN_BASLANGIC,
  ALAN_DERS_YILI,
  ALAN_KURAL_SURUMU,
  ALAN_PROGRAM_BASLAMA,
  BIRLIK_DONEMI_ACIKLAMASI,
  BIRLIK_DONEMI_BASLIGI,
  BITIS_YOK,
  DONEM_AYRINTISI_BASLIGI,
  DONEM_DURUMU_TR,
  DONEM_IPTAL_BASLIGI,
  DONEM_IPTAL_EDILDI,
  DONEM_IPTAL_EDILEMEDI,
  DONEM_IPTAL_METNI,
  DONEM_KAPANDI_NOTU,
  DONEM_YOK_ACIKLAMASI,
  DONEM_YOK_BASLIGI,
  DONEMLER_BASLIGI,
  DONEMLER_OKUNAMADI,
  DUGME_DONEMI_IPTAL,
  DUGME_GECISI_AC,
  GECIS_KARTI_ACIKLAMASI,
  GECIS_KARTI_BASLIGI,
  GOREV_SURESI_BASLIGI,
  KURAL_KOPYASI_BOZUK,
  KURAL_SURUMU_YARDIMI,
  SUTUN_AD,
  SUTUN_BASLANGIC,
  SUTUN_BITIS,
  SUTUN_DURUM,
  kuralSurumuMetni,
} from "./metinler";

/** Geçiş Kurulumu ekranının adresi. */
export const GECIS_ADRESI = "/birlik-donemi/gecis-kurulumu";

/** Varsayılan dönem: açık olan; yoksa iptal edilmemiş en yenisi; yoksa ilki. */
function varsayilanDonem(donemler: readonly BirlikDonemi[]): BirlikDonemi | undefined {
  return (
    donemler.find((d) => d.status === "ACIK") ??
    [...donemler].reverse().find((d) => d.status !== "IPTAL") ??
    donemler[0]
  );
}

/** Kaydedilmeyen, gerekçe istemeyen atıflı uyarıların listesi (görev süresi). */
export function AtifliUyarilar({
  uyarilar,
  baslik,
}: {
  uyarilar: readonly AtifliUyari[];
  baslik: string;
}) {
  if (uyarilar.length === 0) return null;
  return (
    <ul
      aria-label={baslik}
      className="space-y-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
    >
      {uyarilar.map((u) => {
        const { govde } = atifAyir(u.metin);
        return (
          <li key={u.metin} className="flex items-start gap-2">
            <Icon name="warning" size="lg" className="mt-0.5 shrink-0" />
            <span className="min-w-0 space-y-0.5">
              <span className="block break-words text-body-medium">{govde}</span>
              <Dayanak atif={u.atif} />
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function Bilgi({ etiket, children }: { etiket: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-label-medium text-on-surface-variant">{etiket}</dt>
      <dd className="break-words text-body-medium text-on-surface">{children}</dd>
    </div>
  );
}

export default function BirlikDonemiPage() {
  const yetki = useYetki();
  const yazabilir = yetki.acik("birlik_donemi_yazma");
  const snackbar = useSnackbar();
  const [donemler, setDonemler] = useState<BirlikDonemi[]>([]);
  const [gecis, setGecis] = useState<GecisOzeti | null>(null);
  const [yillar, setYillar] = useState<SchoolYear[]>([]);
  const [seciliId, setSeciliId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [iptalAcik, setIptalAcik] = useState(false);
  const [yenile, setYenile] = useState(0);

  const tazele = useCallback(() => setYenile((k) => k + 1), []);

  useEffect(() => {
    let iptal = false;
    setLoading(true);
    Promise.all([birlikDonemiApi.donemler(), birlikDonemiApi.gecis()])
      .then(([liste, ozet]) => {
        if (iptal) return;
        setDonemler(liste);
        setGecis(ozet);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, DONEMLER_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setLoading(false);
      });
    // Ders yılının adı ayrı okunur; okunamazsa no'suyla değil "—" ile gösterilir.
    okulApi
      .listSchoolYears()
      .then((liste) => {
        if (!iptal) setYillar(liste);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const secili = useMemo(
    () => donemler.find((d) => d.id === seciliId) ?? varsayilanDonem(donemler),
    [donemler, seciliId],
  );
  const yilAdi = (id: number) => yillar.find((y) => y.id === id)?.name ?? "—";
  const gecisDonemi = gecis?.donem ?? null;
  const seciliGecisDonemi = secili !== undefined && gecisDonemi?.id === secili.id;
  const iptalEdilebilir =
    yazabilir &&
    secili !== undefined &&
    gecisDonemi?.id === secili.id &&
    secili.status === "ACIK" &&
    secili.transition_completed_on === null &&
    // D7: kural kopyası doğrulanamayan dönem salt okunurdur (sunucu iptali de 409 ile reddeder).
    secili.kural_kopyasi_tutuyor;

  const sutunlar: Column<BirlikDonemi>[] = [
    { header: SUTUN_AD, cell: (d) => d.name },
    { header: SUTUN_BASLANGIC, cell: (d) => formatDate(d.start_date) },
    { header: SUTUN_BITIS, cell: (d) => (d.end_date ? formatDate(d.end_date) : BITIS_YOK) },
    { header: SUTUN_DURUM, cell: (d) => DONEM_DURUMU_TR[d.status] },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{BIRLIK_DONEMI_BASLIGI}</h1>
          <p className="od-page-description">{BIRLIK_DONEMI_ACIKLAMASI}</p>
        </div>
      </div>

      {!yazabilir && yetki.durum === "hazir" && <SaltOkurNotu />}
      {hata && <ErrorBand hata={hata} />}

      {loading ? (
        <SkeletonList rows={4} />
      ) : secili === undefined ? (
        !hata && (
          <EmptyState
            icon="event_note"
            title={DONEM_YOK_BASLIGI}
            // Salt okur rolde yazmayı öğütleyen cümle düşer (sözlük §1 "Rol süzmesi").
            description={yazabilir ? DONEM_YOK_ACIKLAMASI : undefined}
            action={
              yazabilir ? (
                <Link
                  to={GECIS_ADRESI}
                  className="inline-flex text-label-large text-primary underline underline-offset-2"
                >
                  {DUGME_GECISI_AC}
                </Link>
              ) : undefined
            }
          />
        )
      ) : (
        <>
          {donemler.length > 1 && (
            <section aria-labelledby="donemler-basligi" className="space-y-3">
              <h2 id="donemler-basligi" className="text-title-medium text-on-surface">
                {DONEMLER_BASLIGI}
              </h2>
              <DataTable<BirlikDonemi>
                columns={sutunlar}
                rows={donemler}
                caption={DONEMLER_BASLIGI}
                onRowClick={(d) => setSeciliId(d.id)}
                rowLabel={(d) => `${d.name} bilgilerini göster`}
              />
            </section>
          )}

          <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="text-title-medium text-on-surface">{DONEM_AYRINTISI_BASLIGI}</h2>
                <p className="break-words text-body-medium text-on-surface-variant">
                  {secili.name} · {DONEM_DURUMU_TR[secili.status]}
                </p>
              </div>
              {iptalEdilebilir && (
                <Button variant="outlined" icon="block" onClick={() => setIptalAcik(true)}>
                  {DUGME_DONEMI_IPTAL}
                </Button>
              )}
            </div>

            {!secili.kural_kopyasi_tutuyor && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-shape-sm bg-error-container px-4 py-3 text-body-medium text-on-error-container"
              >
                <Icon name="gpp_bad" size="lg" className="shrink-0" />
                <span>{KURAL_KOPYASI_BOZUK}</span>
              </div>
            )}
            {secili.status === "KAPANDI" && (
              <p role="note" className="text-body-medium text-on-surface-variant">
                {DONEM_KAPANDI_NOTU}
              </p>
            )}

            <dl className="grid gap-4 sm:grid-cols-2">
              <Bilgi etiket={ALAN_DERS_YILI}>{yilAdi(secili.school_year)}</Bilgi>
              <Bilgi etiket={ALAN_BASLANGIC}>{formatDate(secili.start_date)}</Bilgi>
              <Bilgi etiket={SUTUN_BITIS}>
                {secili.end_date ? formatDate(secili.end_date) : BITIS_YOK}
              </Bilgi>
              <Bilgi etiket={ALAN_PROGRAM_BASLAMA}>{formatDate(secili.program_start_date)}</Bilgi>
              <Bilgi etiket={ALAN_ACILIS}>
                {secili.opened_by_assembly === null ? ACILIS_GECIS : ACILIS_GENEL_KURUL}
              </Bilgi>
              <Bilgi etiket={ALAN_KURAL_SURUMU}>
                {kuralSurumuMetni(secili.kural_paketi)}
                <span className="mt-0.5 block text-body-small text-on-surface-variant">
                  {KURAL_SURUMU_YARDIMI}
                </span>
              </Bilgi>
            </dl>

            {seciliGecisDonemi && (
              <AtifliUyarilar
                uyarilar={gecis?.gorev_suresi_uyarilari ?? []}
                baslik={GOREV_SURESI_BASLIGI}
              />
            )}
          </Card>

          {gecis !== null && (gecisDonemi !== null || gecis.state === "BASLAMADI") && (
            <Card elevation={0} className="space-y-3 p-[var(--od-panel-padding)]">
              <h2 className="text-title-medium text-on-surface">{GECIS_KARTI_BASLIGI}</h2>
              <p className="text-body-medium text-on-surface-variant">{GECIS_KARTI_ACIKLAMASI}</p>
              <p className="text-body-medium text-on-surface">
                {gecisDonemi?.transition_completed_on
                  ? tamamlandiNotu(formatDate(gecisDonemi.transition_completed_on))
                  : `${SUTUN_DURUM}: ${GECIS_DURUMU_TR[gecis.state]}`}
              </p>
              <Link
                to={GECIS_ADRESI}
                className="inline-flex text-label-large text-primary underline underline-offset-2"
              >
                {DUGME_GECISI_AC}
              </Link>
            </Card>
          )}
        </>
      )}

      {iptalAcik && secili !== undefined && (
        <IptalPenceresi
          baslik={DONEM_IPTAL_BASLIGI}
          metin={DONEM_IPTAL_METNI}
          yedekHata={DONEM_IPTAL_EDILEMEDI}
          onKapat={() => setIptalAcik(false)}
          onIptal={async (gerekce) => {
            await birlikDonemiApi.donemiIptalEt(secili.id, gerekce);
            setIptalAcik(false);
            setSeciliId(null);
            snackbar.success(DONEM_IPTAL_EDILDI);
            tazele();
          }}
        />
      )}
    </div>
  );
}
