// Kişiler → Veli Listesi (T5; genel tasarım §5.1 `ParentRoster`, §8.4; plan "F1b-5 uygulama
// kararları"). Yalnız program yöneticisine açık sekmedir (`veli_listesi` yeteneği; KisilerPage).
//
// EKRANDA AD YOKTUR: özet sınıf başına satır sayısıdır, önizleme ve sonuç yalnız sayıları ve
// aktarılamayan satırların numarasını ve nedenini gösterir (§8.4 (2)); veli adı taşıyan çıktılar
// (davet teslim çizelgesi, katılım cetveli) F2'dedir. Bir satır bir öğrencidir.
//
// Aktarım yalnız dosyayla yapılır (okulun doldurduğu iki sütunlu şablon; .xlsx, .xls, .csv —
// makro içeren dosyayı sunucu reddeder; pano yolu yoktur). Dosyadaki sınıflar listedeki aynı
// sınıfların yerini alır, ötekilere dokunulmaz (§8.4 (1)). Aydınlatma metni aktarımdan önce,
// dosya seçiminin üstündedir (`AydinlatmaMetni`). Boy denetimi personel paneliyle aynıdır
// (`AktarimPaneli.boyHatasi`; kullanıcı kararı 05.11.2026).
//
// "Veli listesini sil" bütün listeyi siler (onay penceresi; §5.4: program yöneticisi onayla elle
// siler, program zamanı denetlemez); denetim izine kişisiz bir satır düşer.
//
// Raporun "Aktarılamayan satırlar (N)" başlığı ve "Aktarılamayan" kutusu aynı sayıyı (satır)
// gösterir; başlık satırının uyarıları (aynı alana uyan ikinci sütun) satır değildir, ayrı
// "Başlık uyarıları" tablosundadır. Aktarım dosyayla bitince kaynak dosyanın silinmesi
// hatırlatılır (tasarım §4.3 tehdit 15; `KaynakDosyaHatirlatmasi`). Metinler `metinler.ts`'tedir.

import { useCallback, useEffect, useId, useRef, useState } from "react";

import { saveBlob } from "../../lib/download";
import { formatDateTime, formatNumber } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import EmptyState from "../../ui/EmptyState";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { useYuklemeSiniri } from "../oturum/useOturum";
import { okulApi, PARENT_TEMPLATE_FILENAME } from "../okul/api";
import type { ParentImportReport, ParentRosterSummary, ParentRowIssue } from "../okul/api";
import { boyHatasi, KABUL_EDILEN_DOSYALAR } from "./AktarimPaneli";
import AydinlatmaMetni from "./AydinlatmaMetni";
import {
  AKTAR,
  AKTARILAMAYAN_SATIR_YOK,
  aktarilamayanSatirlar,
  baslikUyarilari,
  CALISIYOR,
  DAHA_ONCE_AKTARILMIS,
  DOSYADAKI_SINIFLAR,
  DOSYAYI_KALDIR,
  ONIZLE,
  ONIZLEME_BASLIGI,
  ONIZLEME_YAPILAMADI,
  RAPOR_AKTARILACAK,
  RAPOR_AKTARILAMAYAN,
  RAPOR_AKTARILAN,
  RAPOR_DOKUNULMAYAN_SINIF,
  RAPOR_DOSYADAKI_SATIR,
  RAPOR_SILINECEK_ESKI_SATIR,
  RAPOR_SILINEN_ESKI_SATIR,
  RAPOR_SINIF,
  SABLON_INDIR,
  SABLON_INDIRILEMEDI,
  SORUN_ALAN_SUTUNU,
  SORUN_SATIR_SUTUNU,
  SORUN_SORUN_SUTUNU,
  VELI_AKTARILAMADI,
  VELI_AKTARILDI,
  VELI_AKTARIM_ACIKLAMASI,
  VELI_AKTARIM_BASLIGI,
  VELI_AKTARIM_SONUCU,
  VELI_ALAN_AD,
  VELI_ALAN_BASLIK,
  VELI_ALAN_SINIF,
  VELI_DOSYA_ALANI_ETIKETI,
  VELI_DOSYA_SECIN,
  VELI_LISTESI_ACIKLAMASI,
  VELI_LISTESI_BOS,
  VELI_LISTESI_OKUNAMADI,
  VELI_LISTESI_SEKMESI,
  VELI_LISTESINI_SIL,
  VELI_OZET_TABLO_BASLIGI,
  VELI_SATIR_SUTUNU,
  VELI_SILINEMEDI,
  VELI_SILME_ONAY_BASLIGI,
  VELI_SILME_ONAY_METNI,
  VELI_SINIF_SUTUNU,
  VELI_YERINE_KOYMA_ONIZLEME,
  VELI_YERINE_KOYMA_SONUC,
  veliOzetSatiri,
  veliSilindi,
} from "./metinler";
import { ErrorBand, hataOku, KaynakDosyaHatirlatmasi } from "./ortak";
import type { SayfaHatasi } from "./ortak";

/** Satır sorunlarındaki alan kodlarının kullanıcı adları. */
const ALAN_ADI: Record<string, string> = {
  header: VELI_ALAN_BASLIK,
  full_name: VELI_ALAN_AD,
  student_class: VELI_ALAN_SINIF,
};

/** Başlık satırının uyarılarının alan kodu (sunucu `imports._ingest_parents`). */
const BASLIK_ALANI = "header";

const TABLO_SINIFI = "w-full border-collapse text-body-small";
const BASLIK_SATIRI =
  "border-b border-outline-variant text-left text-label-medium text-on-surface-variant";

export default function VeliListesi() {
  const [ozet, setOzet] = useState<ParentRosterSummary | null>(null);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [siliniyor, setSiliniyor] = useState(false);
  const [yenile, setYenile] = useState(0);
  const confirm = useConfirm();
  const snackbar = useSnackbar();

  const tazele = useCallback(() => setYenile((k) => k + 1), []);

  useEffect(() => {
    let iptal = false;
    setYukleniyor(true);
    okulApi
      .getParentRoster()
      .then((veri) => {
        if (iptal) return;
        setOzet(veri);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, VELI_LISTESI_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setYukleniyor(false);
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const sil = async () => {
    const ok = await confirm({
      title: VELI_SILME_ONAY_BASLIGI,
      message: VELI_SILME_ONAY_METNI,
      confirmLabel: VELI_LISTESINI_SIL,
    });
    if (!ok) return;
    setSiliniyor(true);
    setHata(null);
    try {
      const sonuc = await okulApi.deleteParentRoster();
      snackbar.success(veliSilindi(formatNumber(sonuc.deleted_rows)));
      tazele();
    } catch (e) {
      setHata(hataOku(e, VELI_SILINEMEDI));
    } finally {
      setSiliniyor(false);
    }
  };

  const satirVar = ozet !== null && ozet.total_rows > 0;

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-title-medium text-on-surface">{VELI_LISTESI_SEKMESI}</p>
          <p className="mt-0.5 max-w-3xl text-body-small text-on-surface-variant">
            {VELI_LISTESI_ACIKLAMASI}
          </p>
        </div>
        {satirVar && (
          <Button variant="outlined" icon="delete" onClick={sil} disabled={siliniyor}>
            {VELI_LISTESINI_SIL}
          </Button>
        )}
      </div>

      {hata && <ErrorBand hata={hata} />}

      {yukleniyor ? (
        <SkeletonList rows={3} />
      ) : ozet === null ? null : !satirVar ? (
        <EmptyState icon="family_restroom" title={VELI_LISTESI_BOS} />
      ) : (
        <OzetTablosu ozet={ozet} />
      )}

      <VeliAktarimPaneli onAktarildi={tazele} />
    </div>
  );
}

/** Sınıf başına satır sayısı ve toplam; ad yoktur. */
function OzetTablosu({ ozet }: { ozet: ParentRosterSummary }) {
  return (
    <Card elevation={0} className="space-y-2 p-[var(--od-panel-padding)]">
      <p className="text-body-small text-on-surface-variant">
        {veliOzetSatiri(
          formatNumber(ozet.total_rows),
          formatNumber(ozet.class_count),
          ozet.last_import_at ? formatDateTime(ozet.last_import_at) : null,
        )}
      </p>
      <div className="overflow-x-auto">
        <table className={TABLO_SINIFI}>
          <caption className="sr-only">{VELI_OZET_TABLO_BASLIGI}</caption>
          <thead>
            <tr className={BASLIK_SATIRI}>
              <th scope="col" className="p-2">
                {VELI_SINIF_SUTUNU}
              </th>
              <th scope="col" className="p-2 text-right">
                {VELI_SATIR_SUTUNU}
              </th>
            </tr>
          </thead>
          <tbody>
            {ozet.classes.map((c) => (
              <tr key={c.student_class} className="border-t border-outline-variant/50">
                <td className="p-2 text-on-surface">{c.student_class}</td>
                <td className="p-2 text-right text-on-surface">{formatNumber(c.rows)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Aktarım paneli (önizle → aktar)
// ---------------------------------------------------------------------------

function VeliAktarimPaneli({ onAktarildi }: { onAktarildi: () => void }) {
  const [dosya, setDosya] = useState<File | null>(null);
  const [rapor, setRapor] = useState<ParentImportReport | null>(null);
  /** Aktarım dosyayla başarıyla bitti: kaynak dosyanın silinmesi hatırlatılır. */
  const [aktarildi, setAktarildi] = useState(false);
  const [mesgul, setMesgul] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const snackbar = useSnackbar();
  const sinirMb = useYuklemeSiniri();
  const dosyaId = useId();
  const dosyaRef = useRef<HTMLInputElement>(null);
  const aktarilabilir = rapor !== null && rapor.dry_run;

  const calistir = async (kip: "onizle" | "aktar") => {
    if (!dosya) {
      setHata({ message: VELI_DOSYA_SECIN, parolaGerekli: false });
      return;
    }
    const buyuk = boyHatasi(dosya, sinirMb);
    if (buyuk !== null) {
      setHata(buyuk);
      return;
    }
    setMesgul(true);
    setHata(null);
    setAktarildi(false);
    try {
      const sonuc =
        kip === "onizle"
          ? await okulApi.previewParentImport(dosya)
          : await okulApi.commitParentImport(dosya);
      setRapor(sonuc);
      if (kip === "aktar") {
        setAktarildi(true);
        snackbar.success(VELI_AKTARILDI);
        onAktarildi();
      }
    } catch (e) {
      setHata(hataOku(e, kip === "onizle" ? ONIZLEME_YAPILAMADI : VELI_AKTARILAMADI));
    } finally {
      setMesgul(false);
    }
  };

  const sablonIndir = async () => {
    setHata(null);
    try {
      const blob = await okulApi.parentTemplate();
      if ((await saveBlob(blob, PARENT_TEMPLATE_FILENAME)) === "hata") {
        setHata({ message: DOSYA_YAZILAMADI_ILETISI, parolaGerekli: false });
      }
    } catch (e) {
      setHata(hataOku(e, SABLON_INDIRILEMEDI));
    }
  };

  return (
    <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-title-medium text-on-surface">{VELI_AKTARIM_BASLIGI}</p>
          <p className="mt-0.5 max-w-3xl text-body-small text-on-surface-variant">
            {VELI_AKTARIM_ACIKLAMASI}
          </p>
        </div>
        <Button variant="outlined" icon="download" onClick={sablonIndir}>
          {SABLON_INDIR}
        </Button>
      </div>

      <AydinlatmaMetni tur="veli" />

      <div>
        <label htmlFor={dosyaId} className="mb-1 block text-label-large text-on-surface-variant">
          {VELI_DOSYA_ALANI_ETIKETI}
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <input
            id={dosyaId}
            ref={dosyaRef}
            type="file"
            accept={KABUL_EDILEN_DOSYALAR}
            onChange={(e) => {
              const secilen = e.target.files?.[0] ?? null;
              setDosya(secilen);
              setRapor(null);
              setAktarildi(false);
              setHata(boyHatasi(secilen, sinirMb));
            }}
            className="block min-h-[var(--od-field-height)] min-w-0 flex-1 rounded-shape-sm border border-outline bg-surface-container-lowest px-3 py-2 text-body-medium text-on-surface file:mr-3 file:rounded-shape-sm file:border-0 file:bg-secondary-container file:px-3 file:py-1.5 file:text-label-large file:text-on-secondary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          />
          {dosya && (
            <Button
              variant="text"
              icon="close"
              onClick={() => {
                if (dosyaRef.current) dosyaRef.current.value = "";
                setDosya(null);
                setRapor(null);
                setAktarildi(false);
                setHata(null);
              }}
            >
              {DOSYAYI_KALDIR}
            </Button>
          )}
        </div>
      </div>

      {hata && <ErrorBand hata={hata} />}

      <div className="flex flex-wrap justify-end gap-2">
        <Button
          variant="tonal"
          icon="visibility"
          onClick={() => calistir("onizle")}
          disabled={mesgul}
        >
          {mesgul ? CALISIYOR : ONIZLE}
        </Button>
        <Button icon="upload" onClick={() => calistir("aktar")} disabled={mesgul || !aktarilabilir}>
          {AKTAR}
        </Button>
      </div>

      {aktarildi && <KaynakDosyaHatirlatmasi />}

      {rapor && <VeliRaporu rapor={rapor} />}
    </Card>
  );
}

/** Önizleme ya da sonuç: yalnız sayılar, sınıf etkisi ve aktarılamayan satırlar (ad yok). */
function VeliRaporu({ rapor }: { rapor: ParentImportReport }) {
  const onizleme = rapor.dry_run;
  const aktarilamayan = rapor.total_rows - rapor.imported_rows;
  const baslikSorunlari = rapor.issues.filter((s) => s.field === BASLIK_ALANI);
  const satirSorunlari = rapor.issues.filter((s) => s.field !== BASLIK_ALANI);
  const hucreler: { label: string; value: number }[] = [
    { label: RAPOR_DOSYADAKI_SATIR, value: rapor.total_rows },
    { label: onizleme ? RAPOR_AKTARILACAK : RAPOR_AKTARILAN, value: rapor.imported_rows },
    { label: RAPOR_AKTARILAMAYAN, value: aktarilamayan },
    { label: RAPOR_SINIF, value: rapor.class_count },
    {
      label: onizleme ? RAPOR_SILINECEK_ESKI_SATIR : RAPOR_SILINEN_ESKI_SATIR,
      value: rapor.replaced_rows,
    },
    { label: RAPOR_DOKUNULMAYAN_SINIF, value: rapor.kept_class_count },
  ];

  return (
    <div className="space-y-3 rounded-shape-md bg-surface-container-low p-4">
      <p className="text-title-small text-on-surface">
        {onizleme ? ONIZLEME_BASLIGI : VELI_AKTARIM_SONUCU}
      </p>

      {rapor.already_imported && (
        <div className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
          <Icon name="info" size="lg" />
          <span>{DAHA_ONCE_AKTARILMIS}</span>
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {hucreler.map((c) => (
          <div key={c.label} className="rounded-shape-sm bg-surface-container px-3 py-2">
            <dt className="text-label-small text-on-surface-variant">{c.label}</dt>
            <dd className="text-title-medium text-on-surface">{formatNumber(c.value)}</dd>
          </div>
        ))}
      </dl>

      <p className="text-body-small text-on-surface-variant">
        {onizleme ? VELI_YERINE_KOYMA_ONIZLEME : VELI_YERINE_KOYMA_SONUC}
      </p>

      {rapor.classes.length > 0 && (
        <div className="overflow-x-auto">
          <table className={TABLO_SINIFI}>
            <caption className="sr-only">{DOSYADAKI_SINIFLAR}</caption>
            <thead>
              <tr className={BASLIK_SATIRI}>
                <th scope="col" className="p-2">
                  {RAPOR_SINIF}
                </th>
                <th scope="col" className="p-2 text-right">
                  {RAPOR_DOSYADAKI_SATIR}
                </th>
                <th scope="col" className="p-2 text-right">
                  {onizleme ? RAPOR_SILINECEK_ESKI_SATIR : RAPOR_SILINEN_ESKI_SATIR}
                </th>
              </tr>
            </thead>
            <tbody>
              {rapor.classes.map((c) => (
                <tr key={c.student_class} className="border-t border-outline-variant/50">
                  <td className="p-2 text-on-surface">{c.student_class}</td>
                  <td className="p-2 text-right text-on-surface">{formatNumber(c.rows)}</td>
                  <td className="p-2 text-right text-on-surface">
                    {formatNumber(c.replaced_rows)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {baslikSorunlari.length > 0 && (
        <div>
          <p className="text-label-large text-on-surface-variant">
            {baslikUyarilari(formatNumber(baslikSorunlari.length))}
          </p>
          <SorunTablosu sorunlar={baslikSorunlari} />
        </div>
      )}

      <div>
        <p className="text-label-large text-on-surface-variant">
          {aktarilamayanSatirlar(formatNumber(aktarilamayan))}
        </p>
        {satirSorunlari.length === 0 ? (
          <EmptyState compact title={AKTARILAMAYAN_SATIR_YOK} icon="check_circle" />
        ) : (
          <SorunTablosu sorunlar={satirSorunlari} />
        )}
      </div>
    </div>
  );
}

/** Satır sorunlarının tablosu: satır no, alan, neden — hücrenin değeri yazılmaz. */
function SorunTablosu({ sorunlar }: { sorunlar: ParentRowIssue[] }) {
  return (
    <div className="mt-2 overflow-x-auto">
      <table className={TABLO_SINIFI}>
        <thead>
          <tr className={BASLIK_SATIRI}>
            <th className="p-2">{SORUN_SATIR_SUTUNU}</th>
            <th className="p-2">{SORUN_ALAN_SUTUNU}</th>
            <th className="p-2">{SORUN_SORUN_SUTUNU}</th>
          </tr>
        </thead>
        <tbody>
          {sorunlar.map((sorun, i) => (
            <tr
              key={`${sorun.row_number}-${sorun.field}-${i}`}
              className="border-t border-outline-variant/50"
            >
              <td className="p-2 text-on-surface-variant">{sorun.row_number}</td>
              <td className="p-2 text-on-surface-variant">
                {ALAN_ADI[sorun.field] ?? (sorun.field || "—")}
              </td>
              <td className="p-2 text-on-surface">{sorun.issue}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
