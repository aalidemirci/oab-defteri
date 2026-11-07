// Ayarlar sayfası (aile iskeleti kalıbı) — altı sekme: ders yılları (dönemlerle), kapalı
// günler (resmî/dini tatil, öğrenciye kapalı gün), şubeler, okul bilgileri (okul kartı:
// evrak antedi, kurum kodu, kademeler, öğrenci mevcudu ve tarihi, yerleşim türü, kantin ve
// personel çalıştırma biçimi, eğitim kampüsü, açılış tarihi, demirbaş onayı ve no; alanlar
// sihirbazın 2. adımıyla ORTAK — `okul/OkulKartiAlanlari`), güvenlik
// (hesabın kendi parolası, boşta kilit süresi, şifreleme, kurtarma anahtarı ve belgesi,
// yedek) ve güncelleme (yalnız elle denetim). Aile iskeletinin dört kütüphane paneli (Kütüphane Politikası, Bölümler,
// Ağ Kataloğu, Saklama) F1a-2'de söküldü.
//
// Rol süzmesi (plan F1b-2 "Ayarlar ve bant"; kaynak `oturum/yetki`, matris kopyalanmaz): okul
// sekmeleri her role açıktır, yazma denetimleri yeteneğe bağlıdır — Ders Yılları
// `ders_yili_yazma`, Kapalı Günler `kapali_gun_yazma`, Şubeler `sube_yazma`, Okul Bilgileri
// `okul_karti_yazma`. Yeteneği olmayan rolde sekme salt okurdur: başında `SaltOkurNotu`, düğme ve
// form yoktur (Okul Bilgileri değerleri liste olarak yazar). Güncelleme sekmesi yalnız
// `guncelleme`'de görünür (adresle gelinirse varsayılan sekme açılır); Güvenlik sekmesinin
// kartları kendi yeteneklerine bakar (`GuvenlikAyarlari`). "Diğer Ayarlar"ın Kurulum Sihirbazı
// kartı yalnız `kurulum_tamamlama`'dadır (sihirbazın her denetimi bir yazmadır). Özet
// yüklenirken sekmeler yerine iskelet durur: yanlış sekme ya da düğme bir an görünmesin.

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { useTabParam } from "../../hooks/useTabParam";
import { ApiError } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { parseApiFieldErrors } from "../../lib/formErrors";
import { gradeLevelLabel } from "../../lib/gradeLevels";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import EmptyState from "../../ui/EmptyState";
import HubFeatureCard from "../../ui/HubFeatureCard";
import Icon from "../../ui/Icon";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import Tabs, { tabPanelProps } from "../../ui/Tabs";
import type { TabItem } from "../../ui/Tabs";
import TextField from "../../ui/TextField";
import UpdatePanel from "../guncelleme/UpdatePanel";
import GuvenlikAyarlari from "../guvenlik/GuvenlikAyarlari";
import OkulKartiAlanlari, { OkulKartiListesi } from "../okul/OkulKartiAlanlari";
import { okulApi } from "../okul/api";
import type {
  ClassSection,
  GradeLevelOption,
  SchoolConfig,
  SchoolTerm,
  SchoolYear,
} from "../okul/api";
import { OKUL_KARTI_ACIKLAMASI } from "../okul/metinler";
import {
  bosOkulFormu,
  formdanGovdeye,
  kayittanForma,
  okulBilgileriHatalari,
} from "../okul/okulBilgileri";
import type { OkulFormu } from "../okul/okulBilgileri";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import KapaliGunlerPaneli from "../takvim/KapaliGunlerPaneli";
import { eksikDiniBayramIletisi, tatilleriTohumla } from "../takvim/tatilTohumu";

// TABS[0] varsayılan sekmedir (useTabParam fallback) — başa yeni anahtar EKLEME.
const TABS = [
  "ders-yillari",
  "kapali-gunler",
  "subeler",
  "okul",
  "guvenlik",
  "guncelleme",
] as const;
type TabKey = (typeof TABS)[number];

const TAB_ITEMS: TabItem[] = [
  { key: "ders-yillari", label: "Ders Yılları", icon: "calendar_month" },
  { key: "kapali-gunler", label: "Kapalı Günler", icon: "event_busy" },
  { key: "subeler", label: "Şubeler", icon: "meeting_room" },
  { key: "okul", label: "Okul Bilgileri", icon: "apartment" },
  { key: "guvenlik", label: "Güvenlik", icon: "lock" },
  { key: "guncelleme", label: "Güncelleme", icon: "system_update" },
];

/** Sayfanın açıklaması: yazabilen rolde (program yöneticisi) ve salt okur rolde (sözlük §4.1). */
export const AYARLAR_ACIKLAMASI =
  "Ders yılı, kapalı günler, şube kataloğu, okul künyesi, parolanız, boşta kilit süresi, " +
  "kurtarma anahtarı, yedekler ve güncelleme burada yönetilir. Okul künyesi programın bastığı " +
  "evrakın antedinde kullanılır.";
export const AYARLAR_SALT_OKUR_ACIKLAMASI =
  "Ders yılı, kapalı günler, şube kataloğu ve okul künyesi burada görüntülenir; parolanızı " +
  "Güvenlik sekmesinden değiştirirsiniz. Okul künyesi programın bastığı evrakın antedinde " +
  "kullanılır.";

/** Salt okur sekmelerin metinleri (yazma denetimleri gizliyken; sözlük §1 "Rol süzmesi"). */
export const DERS_YILI_YOK_SALT_OKUR = "Henüz ders yılı tanımlanmadı.";
export const DONEMLER_YOK_SALT_OKUR = "Bu ders yılının dönemleri henüz girilmedi.";
export const SUBE_ACIKLAMASI_SALT_OKUR =
  "Öğrenci aktarımında görülen şubeler buraya kendiliğinden eklenir.";
export const SUBE_YOK_SALT_OKUR = "Bu ders yılında kayıtlı şube yok.";

/** Backend hatasını alan-bazlı haritaya VEYA genel hata bandına dağıtır. */
function splitApiError(
  err: unknown,
  fallback: string,
): { fields: Record<string, string>; message: string | null } {
  const fields = parseApiFieldErrors(err) ?? {};
  if (Object.keys(fields).length > 0) return { fields, message: null };
  return { fields: {}, message: err instanceof ApiError ? err.message : fallback };
}

/**
 * Sayfa genelinde tekrar eden M3 hata bandı. `role="alert"`: bant yükleme/kaydetme
 * başarısız olunca sonradan DOM'a girer, canlı bölge olmadan ekran okuyucu susardı.
 */
function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-shape-sm bg-error-container px-4 py-3 text-body-medium text-on-error-container"
    >
      <Icon name="error" size="lg" />
      <span>{message}</span>
    </div>
  );
}

export default function AyarlarPage() {
  const yetki = useYetki();
  // Güncelleme sekmesi yalnız güncelleme yeteneğinde (adresle gelinirse varsayılana düşer).
  const sekmeler = TABS.filter((k) => k !== "guncelleme" || yetki.acik("guncelleme"));
  const [tab, setTab] = useTabParam<TabKey>("tab", sekmeler, "ders-yillari");
  const tamYazar =
    yetki.acik("okul_karti_yazma") && yetki.acik("guvenlik") && yetki.acik("guncelleme");

  // Ders yılları SAYFA düzeyinde tutulur: hem "Ders Yılları" hem "Şubeler"
  // sekmesi aynı listeden beslenir; aktivasyon sonrası ikisi birden tazelenir.
  const [years, setYears] = useState<SchoolYear[]>([]);
  const [yearsLoading, setYearsLoading] = useState(true);
  const [yearsError, setYearsError] = useState<string | null>(null);

  const loadYears = useCallback(() => {
    setYearsLoading(true);
    okulApi
      .listSchoolYears()
      .then((rows) => {
        setYears(rows);
        setYearsError(null);
      })
      .catch((e: unknown) =>
        setYearsError(e instanceof ApiError ? e.message : "Ders yılları yüklenemedi."),
      )
      .finally(() => setYearsLoading(false));
  }, []);
  useEffect(loadYears, [loadYears]);

  return (
    <div className="space-y-6">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">Ayarlar</h1>
          <p className="od-page-description">
            {tamYazar ? AYARLAR_ACIKLAMASI : AYARLAR_SALT_OKUR_ACIKLAMASI}
          </p>
        </div>
      </div>

      {yetki.durum === "yukleniyor" ? (
        <SkeletonList rows={4} />
      ) : (
        <>
          <Tabs
            items={TAB_ITEMS.filter((t) => (sekmeler as readonly string[]).includes(t.key))}
            active={tab}
            onChange={(key) => setTab(key as TabKey)}
            ariaLabel="Ayarlar bölümleri"
            idBase="ayarlar"
          />

          <div {...tabPanelProps("ayarlar", tab)} className="space-y-6">
            {tab === "ders-yillari" && (
              <DersYillariPanel
                years={years}
                loading={yearsLoading}
                error={yearsError}
                onReload={loadYears}
                yazabilir={yetki.acik("ders_yili_yazma")}
              />
            )}
            {tab === "kapali-gunler" && (
              <KapaliGunlerPaneli saltOkur={!yetki.acik("kapali_gun_yazma")} />
            )}
            {tab === "subeler" && (
              <SubelerPanel
                years={years}
                yearsLoading={yearsLoading}
                yazabilir={yetki.acik("sube_yazma")}
              />
            )}
            {tab === "okul" && <OkulBilgileriPanel yazabilir={yetki.acik("okul_karti_yazma")} />}
            {tab === "guvenlik" && <GuvenlikAyarlari />}
            {tab === "guncelleme" && <UpdatePanel />}
          </div>
        </>
      )}

      {yetki.acik("kurulum_tamamlama") && (
        <section className="space-y-3">
          <h2 className="text-title-medium text-on-surface">Diğer Ayarlar</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* Kurulum tamamlandıktan sonra sihirbaza gezinilebilir tek yol burasıdır
                (menüde yer almaz); adımları gözden geçirmek isteyen kullanıcı sıkışmasın. */}
            <HubFeatureCard
              to="/kurulum"
              icon="checklist"
              title="Kurulum Sihirbazı"
              description="Program yöneticisi hesabı, okul bilgileri, ders yılı ve kapalı gün adımlarını yeniden gözden geçirin."
            />
          </div>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 1. Ders yılları
// ---------------------------------------------------------------------------

function DersYillariPanel({
  years,
  loading,
  error,
  onReload,
  yazabilir,
}: {
  years: SchoolYear[];
  loading: boolean;
  error: string | null;
  onReload: () => void;
  /** Ders yılı oluşturma, aktifleştirme ve dönem kaydı (`ders_yili_yazma`). */
  yazabilir: boolean;
}) {
  return (
    <div className="space-y-6">
      {!yazabilir && <SaltOkurNotu />}
      {error && <ErrorBanner message={error} />}

      <Card elevation={1} className="p-6">
        <p className="text-title-medium text-on-surface">Ders Yılları</p>
        <p className="mt-1 text-body-medium text-on-surface-variant">
          Aynı anda yalnız BİR ders yılı aktif olabilir. Şube kataloğu ve e-Okul aktarımı aktif yıla
          bağlanır.
        </p>

        {loading ? (
          <SkeletonList rows={3} className="mt-4" />
        ) : years.length === 0 ? (
          <div className="mt-2">
            <EmptyState
              compact
              icon="calendar_month"
              title={
                yazabilir
                  ? "Henüz ders yılı tanımlanmadı. Aşağıdaki formdan ilk yılı oluşturun."
                  : DERS_YILI_YOK_SALT_OKUR
              }
            />
          </div>
        ) : (
          <ul className="mt-4 divide-y divide-outline-variant/50">
            {years.map((y) => (
              <SchoolYearRow key={y.id} year={y} onChanged={onReload} yazabilir={yazabilir} />
            ))}
          </ul>
        )}
      </Card>

      {yazabilir && <SchoolYearCreateCard onCreated={onReload} />}
    </div>
  );
}

function SchoolYearRow({
  year,
  onChanged,
  yazabilir,
}: {
  year: SchoolYear;
  onChanged: () => void;
  yazabilir: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [editingTerms, setEditingTerms] = useState(false);
  const snackbar = useSnackbar();
  const confirm = useConfirm();

  const activate = async () => {
    const ok = await confirm({
      title: "Ders yılı aktifleştirilsin mi?",
      message: `“${year.name}” aktif ders yılı olur; aynı anda yalnız bir yıl aktif olabildiğinden diğer yıllar pasife çekilir. Bundan sonraki e-Okul aktarımlarında görülen şubeler bu yılın kataloğuna eklenir.`,
      confirmLabel: "Aktifleştir",
    });
    if (!ok) return;
    setBusy(true);
    setErr(null);
    try {
      await okulApi.activateSchoolYear(year.id);
      // Ders yılının iki takvim yılına resmî ve dini tatiller eklenir (sihirbazla aynı
      // kural): tatilsiz kalan yılda tatiller iş günü sayılır, iş günüyle verilen süreler
      // yanlış hesaplanır.
      const eksikDini = eksikDiniBayramIletisi(await tatilleriTohumla(year));
      const ileti = `“${year.name}” aktif ders yılı oldu; resmî ve dini tatiller eklendi.`;
      // Eksik dini bayram elle girilmeli: ileti kapatılana dek kalır.
      if (eksikDini) snackbar.show(`${ileti} ${eksikDini}`, { duration: null });
      else snackbar.success(ileti);
      onChanged();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Ders yılı aktifleştirilemedi.");
      setBusy(false);
    }
  };

  return (
    <li className="space-y-3 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2 text-body-large text-on-surface">
            {year.name}
            {year.is_active && (
              <span className="inline-flex items-center gap-1 rounded-shape-xl bg-primary-container px-2 py-0.5 text-label-small text-on-primary-container">
                <Icon name="check_circle" size="sm" />
                Aktif
              </span>
            )}
          </p>
          <p className="text-label-small text-on-surface-variant">
            {formatDate(year.start_date)} – {formatDate(year.end_date)}
          </p>
          {err && (
            <p role="alert" className="text-label-small text-error">
              {err}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="text"
            icon="date_range"
            onClick={() => setEditingTerms((value) => !value)}
          >
            Dönemler
          </Button>
          {yazabilir && !year.is_active && (
            <Button variant="text" icon="play_circle" onClick={activate} disabled={busy}>
              Aktifleştir
            </Button>
          )}
        </div>
      </div>
      {editingTerms && <SchoolTermEditor year={year} yazabilir={yazabilir} />}
    </li>
  );
}

/** Dönemlerin salt okur görünümü (tarih aralıkları gg.aa.yyyy; dönem yoksa söylenir). */
function DonemAraliklari({ terms }: { terms: SchoolTerm[] }) {
  if (terms.length !== 2) {
    return <p className="text-body-small text-on-surface-variant">{DONEMLER_YOK_SALT_OKUR}</p>;
  }
  return (
    <p className="text-body-medium text-on-surface">
      1. dönem: {formatDate(terms[0].start_date)} – {formatDate(terms[0].end_date)} · 2. dönem:{" "}
      {formatDate(terms[1].start_date)} – {formatDate(terms[1].end_date)}
    </p>
  );
}

function SchoolTermEditor({ year, yazabilir }: { year: SchoolYear; yazabilir: boolean }) {
  const snackbar = useSnackbar();
  const [terms, setTerms] = useState<SchoolTerm[]>([]);
  const [firstEnd, setFirstEnd] = useState("");
  const [secondStart, setSecondStart] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    okulApi
      .listSchoolTerms(year.id)
      .then((rows) => {
        setTerms(rows);
        setFirstEnd(rows.find((term) => term.sequence === 1)?.end_date ?? "");
        setSecondStart(rows.find((term) => term.sequence === 2)?.start_date ?? "");
      })
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : "Dönemler yüklenemedi."),
      )
      .finally(() => setBusy(false));
  }, [year.id]);

  const save = async () => {
    if (!firstEnd || !secondStart) {
      setError("Her iki dönem sınır tarihi de seçilmelidir.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const rows = await okulApi.configureSchoolTerms(year.id, {
        first_term_end: firstEnd,
        second_term_start: secondStart,
      });
      setTerms(rows);
      snackbar.success(`${year.name} dönem takvimi kaydedildi.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Dönemler kaydedilemedi.");
    } finally {
      setBusy(false);
    }
  };

  if (!yazabilir) {
    // Salt okur: tarih alanları ve "Dönemleri kaydet" yok; dönemler aralık olarak yazılır.
    return (
      <div className="space-y-2 rounded-shape-sm bg-surface-container-low p-4">
        {busy ? (
          <SkeletonList rows={1} />
        ) : error ? (
          <p role="alert" className="text-label-small text-error">
            {error}
          </p>
        ) : (
          <DonemAraliklari terms={terms} />
        )}
      </div>
    );
  }

  return (
    <div className="rounded-shape-sm bg-surface-container-low p-4">
      <p className="text-body-small text-on-surface-variant">
        1. dönem ders yılı başlangıcında, 2. dönem ders yılı bitişinde sonlanır. Aradaki boşluk
        yarıyıl tatilidir; yarıyıla bağlı hesaplar (ör. kantinde yarıyıl ayının kirası) bu tarihlere
        dayanır. Yarıyılı Kapalı Günler sekmesinde öğrenciye kapalı gün olarak da ekleyin; iş
        günüyle verilen süreler o takvime bakar.
      </p>
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <TextField
          label="1. dönem bitişi"
          type="date"
          value={firstEnd}
          onChange={(event) => setFirstEnd(event.target.value)}
        />
        <TextField
          label="2. dönem başlangıcı"
          type="date"
          value={secondStart}
          onChange={(event) => setSecondStart(event.target.value)}
        />
      </div>
      {terms.length === 2 && (
        <p className="mt-2 text-label-small text-on-surface-variant">
          {formatDate(terms[0].start_date)} – {formatDate(terms[0].end_date)} ·{" "}
          {formatDate(terms[1].start_date)} – {formatDate(terms[1].end_date)}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-2 text-label-small text-error">
          {error}
        </p>
      )}
      <div className="mt-3 flex justify-end">
        <Button variant="tonal" onClick={() => void save()} disabled={busy}>
          {busy ? "Kaydediliyor…" : "Dönemleri kaydet"}
        </Button>
      </div>
    </div>
  );
}

function SchoolYearCreateCard({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [firstTermEnd, setFirstTermEnd] = useState("");
  const [secondTermStart, setSecondTermStart] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const snackbar = useSnackbar();

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    // İstemci tarafı yalnız BOŞ alanları yakalar; tarih sırası doğrulaması
    // backend'in tek doğruluk kaynağıdır (400 → alan altında gösterilir).
    const missing: Record<string, string> = {};
    if (!name.trim()) missing.name = "Ders yılı adı yazılmalıdır.";
    if (!startDate) missing.start_date = "Başlangıç tarihi seçilmelidir.";
    if (!endDate) missing.end_date = "Bitiş tarihi seçilmelidir.";
    if (!firstTermEnd) missing.first_term_end = "1. dönem bitişi seçilmelidir.";
    if (!secondTermStart) missing.second_term_start = "2. dönem başlangıcı seçilmelidir.";
    if (Object.keys(missing).length > 0) {
      setFieldErrors(missing);
      return;
    }
    setFieldErrors({});
    setBusy(true);
    try {
      const created = await okulApi.createSchoolYear({
        name: name.trim(),
        start_date: startDate,
        end_date: endDate,
      });
      await okulApi.configureSchoolTerms(created.id, {
        first_term_end: firstTermEnd,
        second_term_start: secondTermStart,
      });
      snackbar.success("Ders yılı oluşturuldu.");
      setName("");
      setStartDate("");
      setEndDate("");
      setFirstTermEnd("");
      setSecondTermStart("");
      onCreated();
    } catch (err) {
      const split = splitApiError(err, "Ders yılı oluşturulamadı.");
      setFieldErrors(split.fields);
      setFormError(split.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card elevation={1} className="p-6">
      <p className="text-title-medium text-on-surface">Yeni Ders Yılı</p>
      <p className="mt-1 text-body-medium text-on-surface-variant">
        Yeni yıl PASİF doğar; hazır olduğunuzda listeden aktifleştirirsiniz.
      </p>
      <form className="mt-4 space-y-4" onSubmit={submit} noValidate>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <TextField
            label="Ders yılı adı"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="2026-2027"
            error={fieldErrors.name}
          />
          <TextField
            label="Başlangıç"
            required
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            error={fieldErrors.start_date}
          />
          <TextField
            label="Bitiş"
            required
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            error={fieldErrors.end_date}
          />
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <TextField
            label="1. dönem bitişi"
            required
            type="date"
            value={firstTermEnd}
            onChange={(event) => setFirstTermEnd(event.target.value)}
            error={fieldErrors.first_term_end}
          />
          <TextField
            label="2. dönem başlangıcı"
            required
            type="date"
            value={secondTermStart}
            onChange={(event) => setSecondTermStart(event.target.value)}
            error={fieldErrors.second_term_start}
          />
        </div>
        {formError && <ErrorBanner message={formError} />}
        <div className="flex justify-end">
          <Button type="submit" icon="add" disabled={busy}>
            {busy ? "Oluşturuluyor…" : "Ders yılı oluştur"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 2. Şubeler (şube kataloğu — ders yılı başına; aktarım kendiliğinden doldurur)
// ---------------------------------------------------------------------------

function SubelerPanel({
  years,
  yearsLoading,
  yazabilir,
}: {
  years: SchoolYear[];
  yearsLoading: boolean;
  /** Şube ekleme ve kaldırma (`sube_yazma`). */
  yazabilir: boolean;
}) {
  const [yearId, setYearId] = useState<number | null>(null);
  const [rows, setRows] = useState<ClassSection[]>([]);
  const [levels, setLevels] = useState<GradeLevelOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState("");
  const [section, setSection] = useState("");
  const [busy, setBusy] = useState(false);
  const snackbar = useSnackbar();
  const confirm = useConfirm();

  useEffect(() => {
    if (yearId === null && years.length > 0) {
      setYearId((years.find((y) => y.is_active) ?? years[0]).id);
    }
  }, [years, yearId]);

  useEffect(() => {
    okulApi
      .getGradeLevels()
      .then((r) => {
        setLevels(r.levels);
        if (r.levels.length > 0) setLevel(String(r.levels[0].value));
      })
      .catch(() => setLevels([]));
  }, []);

  const load = useCallback(() => {
    if (yearId === null) {
      setRows([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    okulApi
      .listClassSections(yearId)
      .then((items) => {
        setRows(items);
        setError(null);
      })
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : "Şube kataloğu yüklenemedi."),
      )
      .finally(() => setLoading(false));
  }, [yearId]);
  useEffect(load, [load]);

  const ekle = async () => {
    if (yearId === null || !section.trim() || !level) return;
    setBusy(true);
    try {
      await okulApi.createClassSection({
        school_year: yearId,
        class_level: Number(level),
        class_section: section.trim(),
      });
      snackbar.success("Şube eklendi.");
      setSection("");
      load();
    } catch (e) {
      snackbar.error(e instanceof ApiError ? e.message : "Şube eklenemedi.");
    } finally {
      setBusy(false);
    }
  };

  const sil = async (row: ClassSection) => {
    const ok = await confirm({
      title: "Şube katalogdan kaldırılsın mı?",
      message: `${row.class_label} şubesi seçim listelerinden kalkar. Öğrenci kayıtları etkilenmez; içe aktarma bu şubeyi yeniden görürse şube tekrar eklenir.`,
      confirmLabel: "Kaldır",
    });
    if (!ok) return;
    try {
      await okulApi.deleteClassSection(row.id);
      snackbar.success(`${row.class_label} kaldırıldı.`);
      load();
    } catch (e) {
      snackbar.error(e instanceof ApiError ? e.message : "Şube kaldırılamadı.");
    }
  };

  return (
    <div className="space-y-6">
      {!yazabilir && <SaltOkurNotu />}
      {error && <ErrorBanner message={error} />}

      <Card elevation={1} className="p-6">
        <p className="text-title-medium text-on-surface">Şube Kataloğu</p>
        <p className="mt-1 text-body-medium text-on-surface-variant">
          {yazabilir
            ? "Öğrenci aktarımında görülen şubeler buraya kendiliğinden eklenir; eksik kalan şubeyi aşağıdan elle ekleyebilirsiniz."
            : SUBE_ACIKLAMASI_SALT_OKUR}
        </p>

        <div className="mt-4 max-w-sm">
          <Select
            label="Ders yılı"
            value={yearId === null ? "" : String(yearId)}
            onChange={(e) => setYearId(Number(e.target.value))}
            options={years.map((y) => ({
              value: String(y.id),
              label: `${y.name}${y.is_active ? " (aktif)" : ""}`,
            }))}
          />
        </div>

        {yearsLoading || loading ? (
          <SkeletonList rows={3} className="mt-4" />
        ) : rows.length === 0 ? (
          <div className="mt-2">
            <EmptyState
              compact
              icon="meeting_room"
              title={
                yazabilir
                  ? "Bu ders yılında kayıtlı şube yok. Öğrenci listesi aktarınca şubeler kendiliğinden gelir; aşağıdan elle de ekleyebilirsiniz."
                  : SUBE_YOK_SALT_OKUR
              }
            />
          </div>
        ) : (
          <ul className="mt-4 flex flex-wrap gap-2">
            {rows.map((row) => (
              <li
                key={row.id}
                className="flex items-center gap-1 rounded-shape-sm bg-surface-container px-3 py-1.5 text-body-medium text-on-surface"
              >
                {row.class_label}
                {yazabilir && (
                  <button
                    type="button"
                    aria-label={`${row.class_label} şubesini kaldır`}
                    onClick={() => void sil(row)}
                    className="ml-1 flex h-6 w-6 items-center justify-center rounded-shape-xs text-on-surface-variant transition hover:bg-surface-container-high hover:text-error focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <Icon name="close" size="sm" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}

        {yazabilir && (
          <div className="mt-5 grid grid-cols-1 items-end gap-3 sm:grid-cols-[10rem_8rem_auto]">
            <Select
              label="Sınıf düzeyi"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              options={levels.map((l) => ({
                value: String(l.value),
                label: gradeLevelLabel(l.value),
              }))}
            />
            <TextField
              label="Şube"
              value={section}
              onChange={(e) => setSection(e.target.value)}
              placeholder="A"
            />
            <Button
              icon="add"
              onClick={() => void ekle()}
              disabled={busy || yearId === null || !section.trim() || !level}
            >
              Şube ekle
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3. Okul bilgileri (okul kartı — sihirbazın 2. adımıyla ortak alanlar)
// ---------------------------------------------------------------------------

function OkulBilgileriPanel({ yazabilir }: { yazabilir: boolean }) {
  const [kayit, setKayit] = useState<SchoolConfig | null>(null);
  const [form, setForm] = useState<OkulFormu>(bosOkulFormu);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const snackbar = useSnackbar();

  useEffect(() => {
    let iptal = false;
    okulApi
      .getSchoolConfig()
      .then((c) => {
        if (iptal) return;
        setKayit(c);
        setForm(kayittanForma(c));
        setError(null);
      })
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : "Okul bilgileri yüklenemedi."),
      )
      .finally(() => {
        if (!iptal) setLoading(false);
      });
    return () => {
      iptal = true;
    };
  }, []);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    // Sihirbazın 2. adımıyla aynı zorunlu alan kuralı: bir kez girilen zorunlu alan buradan
    // boşaltılamaz (backend de reddeder).
    const hatalar = okulBilgileriHatalari(form);
    setFieldErrors(hatalar);
    if (Object.keys(hatalar).length > 0) {
      setError("Zorunlu alanları doldurun.");
      return;
    }
    setBusy(true);
    try {
      await okulApi.updateSchoolConfig(formdanGovdeye(form));
      snackbar.success("Okul bilgileri kaydedildi.");
    } catch (err) {
      const split = splitApiError(err, "Okul bilgileri kaydedilemedi.");
      setFieldErrors(split.fields);
      setError(split.message);
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <SkeletonList rows={4} />;

  if (!yazabilir) {
    // Salt okur (`okul_karti_yazma` yok): form yerine değerler; etiketler formunkidir.
    return (
      <div className="space-y-6">
        <SaltOkurNotu />
        <Card elevation={1} className="p-6">
          <p className="text-title-medium text-on-surface">Okul Bilgileri</p>
          <p className="mt-1 text-body-medium text-on-surface-variant">{OKUL_KARTI_ACIKLAMASI}</p>
          {error || kayit === null ? (
            <div className="mt-4">
              <ErrorBanner message={error ?? "Okul bilgileri yüklenemedi."} />
            </div>
          ) : (
            <OkulKartiListesi kayit={kayit} />
          )}
        </Card>
      </div>
    );
  }

  return (
    <Card elevation={1} className="p-6">
      <p className="text-title-medium text-on-surface">Okul Bilgileri</p>
      <p className="mt-1 text-body-medium text-on-surface-variant">{OKUL_KARTI_ACIKLAMASI}</p>
      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <form className="mt-4" onSubmit={submit} noValidate>
        <OkulKartiAlanlari
          form={form}
          errors={fieldErrors}
          onChange={(degisiklik) => setForm((f) => ({ ...f, ...degisiklik }))}
        />
        <div className="mt-4 flex justify-end">
          <Button type="submit" icon="check" disabled={busy}>
            {busy ? "Kaydediliyor…" : "Kaydet"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
