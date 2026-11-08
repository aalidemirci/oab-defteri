// e-Okul listesinden (ya da şablondan) aktarım paneli — önizle → aktar, MUTABAKATLA
// (genel tasarım §8.4). Dosya VEYA pano metni aynı boru hattından geçer.
//
// AKTARIM KİMSEYİ AYIRMAZ VE SİLMEZ (aile iskeletinden gelen kullanıcı kararı): listede
// bulunmayan aktif kişi Ayrılış Havuzu'na eklenir, durumu aktif kalır; dosyada
// bulunan havuzdaki kişi havuzdan kendiliğinden çıkar. Karar Kişiler → Ayrılış
// Havuzu'nda verilir. Önizleme "N kişi ayrılış havuzuna eklenecek, M kişi havuzdan
// çıkacak" der; ayrılış olmadığı için aktarım ayrıca onay istemez. Öğrenci aktarımı (şube
// kapsamı, "Bu dosya okulun tam listesidir" onayı, şube bazında etki tablosu) F1b 5. adımda
// öğrenci sicili ile söküldü (tasarım §5.1 ALMA); veli listesinin aktarımı ayrı paneldedir
// (`VeliListesi`: yalnız dosya, yalnız sayılar, sınıf bazında yerine koyma).
//
// Aydınlatma (KVKK md. 10/1; plan "F1b-5 uygulama kararları"): personelin aydınlatma metni
// aktarımdan önce, dosya seçiminin üstünde görünür (`AydinlatmaMetni`). Aktarım DOSYAYLA
// başarıyla bitince kaynak dosyanın silinmesi hatırlatılır (tasarım §4.3 tehdit 15;
// `KaynakDosyaHatirlatmasi`); yapıştırılan metinde dosya yoktur, hatırlatma da yoktur.
//
// Personel: listede olmayanlar havuza eklenir (eski "ayrıldı sayılsın mı?" seçimi
// kalktı); "olası aynı kişi" çiftleri gösterilir, aktarımdan sonra onaylı "Birleştir"
// ile eski kayıt yeni kayda katılır (Ayrılış Havuzu'ndan da yapılabilir). Görev
// sütunu yalnız görev türü için okunur; görev hücresi boş (ya da şablondaki görev türü
// tanınmayan) satırlar ve yönetici ya da öğretmen görevine benzeyip tam tanınmayan görevler
// ("Okul Müdürü", "Psikolojik Danışman"; yeni kayıtta tür yine kuralla verilir) "Görev türünü
// denetleyin" uyarısı alır; bu satırlarda var olan kaydın türü değişmez (elle düzeltme korunur).
//
// Dosya biçimleri (genel tasarım §8.1 A4, TK18): e-Okul .xls, şablon .xlsx ve .csv; makro içeren
// dosyayı sunucu okumadan reddeder (ileti sunucudan gelir). Seçim penceresinin süzgeci `accept`
// listesidir (WebView'ın kendi penceresi; masaüstünde ayrı bir Aç penceresi yoktur).
//
// Rol (plan F1b-2): panelin kendisi `eokul_aktarimi` yeteneğinde çizilir (Kişiler verir);
// "Birleştir" düğmeleri ayrıca `kisi_yazma`'ya bağlıdır (`birlestirebilir`; personel
// birleştirme ucu).
//
// Boy denetimi (kullanıcı kararı 05.11.2026 "Sınırı aşan düz dosyayı ön yüz de durdurur"): sınırı
// aşan gövde sunucuya varmadan sistemin geçici dizinine şifresiz iner (plan F1b-3 "Dosya deposu",
// Yükleme maddesi). Ekran dosyayı seçimde ve gönderimden önce boyuna bakar; aşan dosya hiç
// gönderilmez, ileti sunucununkiyle aynıdır (`shared/yukleme.py`). Sınır sunucudan gelir
// (`useYuklemeSiniri`); okunamazsa dosya gönderilir, sunucu reddeder. Karar dosyayı sayar:
// yapıştırılan metin bu denetimin dışındadır, panodan gelen liste sınırın çok altında kalır.

import { useId, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { saveBlob } from "../../lib/download";
import { formatNumber } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import EmptyState from "../../ui/EmptyState";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { useYuklemeSiniri } from "../oturum/useOturum";
import {
  benzerlikGerekcesi,
  importCounts,
  okulApi,
  PERSONNEL_TEMPLATE_FILENAME,
} from "../okul/api";
import type {
  ImportInput,
  ImportIssue,
  ImportReport,
  PersonnelImportReport,
  SimilarPair,
} from "../okul/api";
import {
  DAHA_ONCE_AKTARILMIS,
  DOSYA_ALANI_ETIKETI,
  DOSYAYI_KALDIR,
  PERSONEL_AKTARIM_ACIKLAMASI,
} from "./metinler";
import { ErrorBand, HAVUZ_ADRESI, hataOku, KaynakDosyaHatirlatmasi } from "./ortak";
import type { SayfaHatasi } from "./ortak";
import AydinlatmaMetni from "./AydinlatmaMetni";

/** Aktarımın türü — bu panelde yalnız personel (veli listesinin paneli `VeliListesi`'dir). */
export type ImportKind = "personnel";

const IMPORT_LABEL: Record<ImportKind, { title: string; hint: string; template: string }> = {
  personnel: {
    title: "e-Okul Raporundan veya Şablondan Öğretmen ve Diğer Personeli Aktar",
    hint: PERSONEL_AKTARIM_ACIKLAMASI,
    template: PERSONNEL_TEMPLATE_FILENAME,
  },
};

/** Dosya seçiminin süzgeci: e-Okul .xls, şablon .xlsx, .csv (tasarım §8.1 A4). */
export const KABUL_EDILEN_DOSYALAR = [
  ".xls",
  ".xlsx",
  ".csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/csv",
].join(",");

/** Havuzun ne olduğu — önizleme ve sonuçta aynı cümle. */
const HAVUZ_ACIKLAMASI =
  "Aktarım kimseyi ayırmaz ve kimsenin kaydını silmez: listede bulunmayanların durumu aktif kalır, karar Ayrılış Havuzu'nda verilir.";

/** Rapor satır sorunlarındaki alan kodlarının kullanıcı adları. */
const ALAN_ADI: Record<string, string> = {
  header: "Başlık",
  leave_pool: "Ayrılış havuzu",
  full_name: "Ad-soyad",
  member_kind: "Görev türü",
};

/** Sınırı aşan dosyanın iletisi; dosya sınırdaysa ya da sınır bilinmiyorsa null. */
export function boyHatasi(dosya: File | null, sinirMb: number | null): SayfaHatasi | null {
  if (dosya === null || sinirMb === null || dosya.size <= sinirMb * 1024 * 1024) return null;
  return { message: `Dosya çok büyük; en çok ${sinirMb} MB olabilir.`, parolaGerekli: false };
}

export default function AktarimPaneli({
  kind,
  onImported,
  birlestirebilir,
}: {
  kind: ImportKind;
  onImported: () => void;
  /** "Birleştir" düğmeleri (personel birleştirme; `kisi_yazma`). */
  birlestirebilir: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [report, setReport] = useState<ImportReport | null>(null);
  /** Aktarım dosyayla başarıyla bitti: kaynak dosyanın silinmesi hatırlatılır. */
  const [dosyadanAktarildi, setDosyadanAktarildi] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<SayfaHatasi | null>(null);
  const snackbar = useSnackbar();
  const confirm = useConfirm();
  const sinirMb = useYuklemeSiniri();
  const fileId = useId();
  const textId = useId();
  // Seçimi geri almak için gerçek DOM alanına erişim şart: `value` sıfırlanmadan
  // aynı dosya yeniden seçilemez ve tarayıcı "dosya seçilmedi" durumuna dönmez.
  const fileRef = useRef<HTMLInputElement>(null);

  const labels = IMPORT_LABEL[kind];
  // Dosya öncelikli: ikisi birden doluysa backend 400 döner, o yüzden tek girdi seçilir.
  const input: ImportInput | null = file ? { file } : text.trim() ? { text } : null;
  // Aktarma yalnız önizlemeden sonra açılır (dry_run raporu görülmeden yazma yok).
  const canCommit = report !== null && report.dry_run;

  /** Girdi değişince eski önizleme geçersizdir. */
  const sifirla = () => {
    setReport(null);
    setDosyadanAktarildi(false);
    setError(null);
  };

  const run = async (mode: "preview" | "commit") => {
    if (!input) {
      setError({ message: "Önce bir dosya seçin ya da listeyi yapıştırın.", parolaGerekli: false });
      return;
    }
    const buyuk = boyHatasi(file, sinirMb);
    if (buyuk !== null) {
      setError(buyuk);
      return;
    }
    setBusy(true);
    setError(null);
    setDosyadanAktarildi(false);
    try {
      const result: ImportReport =
        mode === "preview"
          ? await okulApi.previewPersonnelImport(input)
          : await okulApi.commitPersonnelImport(input);
      setReport(result);
      if (mode === "commit") {
        setDosyadanAktarildi("file" in input);
        snackbar.success("İçe aktarma tamamlandı.");
        onImported();
      }
    } catch (e) {
      setError(hataOku(e, mode === "preview" ? "Önizleme yapılamadı." : "İçe aktarma yapılamadı."));
    } finally {
      setBusy(false);
    }
  };

  const downloadTemplate = async () => {
    setError(null);
    try {
      const blob = await okulApi.personnelTemplate();
      if ((await saveBlob(blob, labels.template)) === "hata") {
        setError({ message: DOSYA_YAZILAMADI_ILETISI, parolaGerekli: false });
      }
    } catch (e) {
      setError(hataOku(e, "Şablon indirilemedi."));
    }
  };

  const birlestir = async (pair: SimilarPair) => {
    if (pair.new_id === null || report === null) return;
    // Geri alınamaz işlem + yalnız ad benzerliğiyle bulunmuş aday (§13 D30):
    // gerekçe yazılır ve onay düğmesi doğrulama kutusuyla açılır.
    const ok = await confirm({
      title: "Bu iki kayıt aynı kişi mi?",
      message:
        `Kayıttaki kişi: “${pair.existing_name}” (listede bulunamadı). Listedeki ${pair.row_number}. satır: “${pair.row_name}”. ` +
        `Çift yalnız ad benzerliğiyle kuruldu (${benzerlikGerekcesi(pair.reason)}); okula yeni gelen bir adaş da olabilir. ` +
        `Onaylarsanız “${pair.existing_name}” kaydının bağları “${pair.row_name}” kaydına taşınır ve eski kayıt silinir. Bu işlem geri alınamaz.`,
      confirmLabel: "Birleştir",
      acknowledgeLabel: "Bu iki kaydın aynı kişi olduğunu doğruladım",
    });
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      await okulApi.mergePersonnel(pair.existing_id, pair.new_id);
      setReport({
        ...report,
        similar_pairs: report.similar_pairs.filter((p) => p !== pair),
        pool_added: report.pool_added.filter((m) => m.id !== pair.existing_id),
      });
      snackbar.success("Kayıtlar birleştirildi.");
      onImported();
    } catch (e) {
      setError(hataOku(e, "Kayıtlar birleştirilemedi."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-title-medium text-on-surface">{labels.title}</p>
          <p className="mt-0.5 max-w-3xl text-body-small text-on-surface-variant">{labels.hint}</p>
        </div>
        <Button variant="outlined" icon="download" onClick={downloadTemplate}>
          Şablon indir
        </Button>
      </div>

      <AydinlatmaMetni tur="personel" />

      <div>
        <label htmlFor={fileId} className="mb-1 block text-label-large text-on-surface-variant">
          {DOSYA_ALANI_ETIKETI}
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <input
            id={fileId}
            ref={fileRef}
            type="file"
            /* e-Okul ihraçları BÜYÜK harfli .XLS uzantısıyla iner; tarayıcı
               accept eşleşmesi büyük/küçük harfe duyarsızdır ama MIME tipini
               tanımayan Windows kurulumları için uzantı listesi de verilir. Makrolu
               biçimler (.xlsm…) listede yoktur; elle seçilirse sunucu reddeder. */
            accept={KABUL_EDILEN_DOSYALAR}
            onChange={(e) => {
              const secilen = e.target.files?.[0] ?? null;
              setFile(secilen);
              setReport(null);
              setDosyadanAktarildi(false);
              setError(boyHatasi(secilen, sinirMb));
            }}
            className="block min-h-[var(--od-field-height)] flex-1 rounded-shape-sm border border-outline bg-surface-container-lowest px-3 py-2 text-body-medium text-on-surface file:mr-3 file:rounded-shape-sm file:border-0 file:bg-secondary-container file:px-3 file:py-1.5 file:text-label-large file:text-on-secondary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          />
          {file && (
            <Button
              variant="text"
              icon="close"
              onClick={() => {
                if (fileRef.current) fileRef.current.value = "";
                setFile(null);
                sifirla();
              }}
            >
              {DOSYAYI_KALDIR}
            </Button>
          )}
        </div>
      </div>

      <div>
        <label htmlFor={textId} className="mb-1 block text-label-large text-on-surface-variant">
          Ya da tabloyu yapıştırın
        </label>
        <textarea
          id={textId}
          rows={3}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            sifirla();
          }}
          disabled={file !== null}
          placeholder="Excel satırlarını kopyalayıp buraya yapıştırın…"
          className="block w-full rounded-shape-xs border border-outline bg-surface px-4 py-3 text-body-medium text-on-surface outline-none placeholder:text-on-surface-variant/60 focus-visible:ring-2 focus-visible:ring-primary focus:border-primary disabled:opacity-50"
        />
      </div>

      {error && <ErrorBand hata={error} />}

      <div className="flex flex-wrap justify-end gap-2">
        <Button variant="tonal" icon="visibility" onClick={() => run("preview")} disabled={busy}>
          {busy ? "Çalışıyor…" : "Önizle"}
        </Button>
        <Button icon="upload" onClick={() => run("commit")} disabled={busy || !canCommit}>
          Aktar
        </Button>
      </div>

      {dosyadanAktarildi && <KaynakDosyaHatirlatmasi />}

      {report && (
        <ImportReportView
          report={report}
          onMerge={birlestirebilir ? birlestir : undefined}
          busy={busy}
        />
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Rapor görünümü
// ---------------------------------------------------------------------------

function ImportReportView({
  report,
  onMerge,
  busy,
}: {
  report: ImportReport;
  /** Yoksa "Birleştir" çizilmez (`birlestirebilir`). */
  onMerge?: (pair: SimilarPair) => void;
  busy: boolean;
}) {
  const counts = importCounts(report);
  const cells: { label: string; value: number }[] = [
    { label: "Toplam satır", value: report.total_rows },
    { label: "İşlenen", value: report.processed },
    { label: "Yeni", value: counts.created },
    { label: "Güncellenen", value: counts.updated },
    { label: "Değişmeyen", value: counts.unchanged },
    { label: report.dry_run ? "Havuza eklenecek" : "Havuza eklenen", value: counts.poolAdded },
    { label: report.dry_run ? "Havuzdan çıkacak" : "Havuzdan çıkan", value: counts.poolRemoved },
  ];

  return (
    <div className="space-y-3 rounded-shape-md bg-surface-container-low p-4">
      <p className="text-title-small text-on-surface">
        {report.dry_run ? "Önizleme — hiçbir kayıt yazılmadı" : "İçe aktarma sonucu"}
      </p>

      {report.already_imported && (
        <div className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
          <Icon name="info" size="lg" />
          <span>{DAHA_ONCE_AKTARILMIS}</span>
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {cells.map((c) => (
          <div key={c.label} className="rounded-shape-sm bg-surface-container px-3 py-2">
            <dt className="text-label-small text-on-surface-variant">{c.label}</dt>
            <dd className="text-title-medium text-on-surface">{formatNumber(c.value)}</dd>
          </div>
        ))}
      </dl>

      <HavuzOzeti report={report} poolAdded={counts.poolAdded} poolRemoved={counts.poolRemoved} />

      <PersonelMutabakati report={report} onMerge={onMerge} busy={busy} />

      <IssueTable
        title={`Uyarılar (${report.warnings.length})`}
        issues={report.warnings}
        emptyText="Uyarı yok."
      />
      <IssueTable
        title={`Atlanan satırlar (${report.skipped.length})`}
        issues={report.skipped}
        emptyText="Atlanan satır yok."
      />
    </div>
  );
}

/** "N … ayrılış havuzuna eklenecek, M … havuzdan çıkacak" + havuza bağlantı. */
function HavuzOzeti({
  report,
  poolAdded,
  poolRemoved,
}: {
  report: ImportReport;
  poolAdded: number;
  poolRemoved: number;
}) {
  const birim = "kişi";
  const cumle = report.dry_run
    ? `${formatNumber(poolAdded)} ${birim} ayrılış havuzuna eklenecek, ${formatNumber(poolRemoved)} ${birim} havuzdan çıkacak.`
    : `${formatNumber(poolAdded)} ${birim} ayrılış havuzuna eklendi, ${formatNumber(poolRemoved)} ${birim} havuzdan çıktı.`;
  return (
    <div className="flex items-start gap-2 rounded-shape-sm bg-surface-container px-4 py-3 text-body-medium text-on-surface">
      <Icon name="pending_actions" size="lg" className="mt-0.5 shrink-0" />
      <div className="min-w-0 space-y-1">
        <p className="text-label-large">{cumle}</p>
        <p className="text-body-small text-on-surface-variant">{HAVUZ_ACIKLAMASI}</p>
        {!report.dry_run && poolAdded > 0 && (
          <Link
            to={HAVUZ_ADRESI}
            className="inline-flex text-label-large text-primary underline underline-offset-2"
          >
            Ayrılış Havuzu&apos;nu aç
          </Link>
        )}
      </div>
    </div>
  );
}

function PersonelMutabakati({
  report,
  onMerge,
  busy,
}: {
  report: PersonnelImportReport;
  onMerge?: (pair: SimilarPair) => void;
  busy: boolean;
}) {
  const ciftteki = new Set(report.similar_pairs.map((p) => p.existing_id));
  const turUyarisi = report.warnings.filter((w) => w.field === "member_kind").length;

  return (
    <div className="space-y-3">
      {turUyarisi > 0 && (
        <div className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
          <Icon name="warning" size="lg" />
          <span>
            {formatNumber(turUyarisi)} satırda görev türünü denetleyin: görev bilgisi boş ya da tam
            tanınmadı. Nedeni ve satır numaraları aşağıdaki uyarılar tablosundadır. Bu satırlarda
            mevcut kaydın görev türü değişmez, yeni kayıt kurala göre açılır; gerekirse kişiyi
            düzenleyip doğru görev türünü seçin, seçiminiz sonraki aktarımlarda korunur.
          </span>
        </div>
      )}

      {report.pool_added.length > 0 && (
        <div className="space-y-2">
          <p className="text-label-large text-on-surface">
            {report.dry_run
              ? `Listede olmayan ${formatNumber(report.pool_added.length)} kişi ayrılış havuzuna eklenecek`
              : `Listede olmayan ${formatNumber(report.pool_added.length)} kişi ayrılış havuzuna eklendi`}
          </p>
          <p className="text-body-small text-on-surface-variant">
            Durumları aktif kalır; okuldan ayrılıp ayrılmadıklarına Ayrılış Havuzu&apos;nda karar
            verirsiniz.
          </p>
          <ul className="space-y-1">
            {report.pool_added.map((m) => (
              <li key={m.id} className="text-body-medium text-on-surface">
                {m.full_name}
                {ciftteki.has(m.id) && (
                  <span className="ml-2 text-body-small text-on-surface-variant">
                    (olası aynı kişi — aşağıya bakın)
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.similar_pairs.length > 0 && (
        <div className="space-y-2">
          <p className="text-label-large text-on-surface">
            Olası aynı kişi ({formatNumber(report.similar_pairs.length)})
          </p>
          <p className="text-body-small text-on-surface-variant">
            {report.dry_run
              ? "Listedeki yeni ad, kayıttaki bir kişiye benziyor (ör. soyadı değişimi). Aktardıktan sonra iki kaydı burada ya da Ayrılış Havuzu'nda birleştirebilirsiniz."
              : "Birleştirilen eski kaydın bağları yeni kayda taşınır ve eski kayıt silinir."}
          </p>
          <ul className="space-y-2">
            {report.similar_pairs.map((p) => (
              <li
                key={`${p.row_number}-${p.existing_id}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-shape-sm bg-surface-container px-3 py-2"
              >
                <span className="text-body-medium text-on-surface">
                  Satır {p.row_number}: {p.row_name} ↔ kayıttaki {p.existing_name}
                  {/* Neden çift? Kural adı yeterli sayar; adaş da buraya düşer (§13 D30). */}
                  <span className="block text-body-small text-on-surface-variant">
                    Neden aday: {benzerlikGerekcesi(p.reason)}
                  </span>
                </span>
                {onMerge !== undefined && !report.dry_run && p.new_id !== null && (
                  <Button
                    variant="tonal"
                    icon="merge"
                    disabled={busy}
                    onClick={() => onMerge(p)}
                    aria-label={`${p.existing_name} kaydını ${p.row_name} kaydıyla birleştir`}
                  >
                    Birleştir
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function IssueTable({
  title,
  issues,
  emptyText,
}: {
  title: string;
  issues: ImportIssue[];
  emptyText: string;
}) {
  return (
    <div>
      <p className="text-label-large text-on-surface-variant">{title}</p>
      {issues.length === 0 ? (
        <EmptyState compact title={emptyText} icon="check_circle" />
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full border-collapse text-body-small">
            <thead>
              <tr className="border-b border-outline-variant text-left text-label-medium text-on-surface-variant">
                <th className="p-2">Satır</th>
                <th className="p-2">Alan</th>
                <th className="p-2">Sorun</th>
                <th className="p-2">Değer</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue, i) => (
                <tr
                  key={`${issue.row_number}-${issue.field}-${i}`}
                  className="border-t border-outline-variant/50"
                >
                  <td className="p-2 text-on-surface-variant">{issue.row_number}</td>
                  <td className="p-2 text-on-surface-variant">
                    {ALAN_ADI[issue.field] ?? (issue.field || "—")}
                  </td>
                  <td className="p-2 text-on-surface">{issue.issue}</td>
                  <td className="p-2 text-on-surface-variant">{issue.raw_value || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
