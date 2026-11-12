// Okul kartının ORTAK form alanları — kurulum sihirbazının 2. adımı ve Ayarlar → Okul Bilgileri
// aynı bileşeni kullanır (F1b 4. adım; genel tasarım §5.1 "`SchoolConfig`'e eklenen OAB
// alanları"). Form modeli, gövde dönüşümü ve zorunlu alan iletileri `okulBilgileri.ts`'tedir;
// metinler `metinler.ts`'te (sözlükte yazılı). Salt okur rol için aynı etiketlerle değer listesi
// (`OkulKartiListesi`) de buradadır.
//
// Alanlar: okul adı, kurum kodu, okul müdürü, il, ilçe (antet), kademeler (onay kutusu grubu;
// birden çok kademeli kurum hepsini seçer), öğrenci mevcudu ve tarihi (md. 9/2), yerleşim türü
// (md. 17/1-a-2), kantin işletme biçimi (md. 17/1; birlikçe işletiliyorsa md. 23/3'ün bilgisi —
// uyarıdır, engel değil), personel çalıştırma biçimi (K3, md. 6/1-d), eğitim kampüsü (md. 13/7),
// yeni okulun açılış tarihi (md. 9/1), veri sorumlusu (isteğe bağlı; aydınlatma metninde, F1b 5.
// adım) ve demirbaş onayı. Uzun seçenek etiketleri sarar (seçim
// alanları radyo grubudur, açılır liste değil): ekran 1366×768'de yatay kaydırmasız kalır.

import { useId } from "react";
import type { ReactNode } from "react";

import { formatDate, formatNumber, todayIso } from "../../lib/format";
import Icon from "../../ui/Icon";
import TextField from "../../ui/TextField";
import DemirbasAlanlari from "./DemirbasAlanlari";
import { CANTEEN_MODE_TR, SCHOOL_LEVEL_TR, SETTLEMENT_TYPE_TR, STAFFING_MODE_TR } from "./api";
import type { CanteenMode, SchoolConfig, SchoolLevel, SettlementType, StaffingMode } from "./api";
import {
  ACILIS_YARDIMI,
  KADEME_YARDIMI,
  KAMPUS_ETIKETI,
  KAMPUS_YARDIMI,
  KANTIN_ISLETME_BILGISI,
  KANTIN_YARDIMI,
  KURUM_KODU_YARDIMI,
  MEVCUT_TARIHI_YARDIMI,
  MEVCUT_YARDIMI,
  OKUL_ADI_YARDIMI,
  PERSONEL_YARDIMI,
  VERI_SORUMLUSU_ETIKETI,
  VERI_SORUMLUSU_YARDIMI,
  YERLESIM_YARDIMI,
} from "./metinler";
import { kademeleriSirala } from "./okulBilgileri";
import type { OkulFormu } from "./okulBilgileri";

/** Seçim haritası → seçenek listesi (anahtar sırası backend enum sırasıdır). */
function secenekler<T extends string>(harita: Record<T, string>): { value: T; label: string }[] {
  return (Object.keys(harita) as T[]).map((value) => ({ value, label: harita[value] }));
}

const KADEMELER = secenekler(SCHOOL_LEVEL_TR);
const YERLESIMLER = secenekler(SETTLEMENT_TYPE_TR);
const KANTINLER = secenekler(CANTEEN_MODE_TR);
const PERSONELLER = secenekler(STAFFING_MODE_TR);

const ETIKET_SINIFI = "mb-1.5 block text-label-medium font-semibold text-on-surface-variant";

/**
 * Kantin birlikçe işletiliyorsa görünen md. 23/3 bilgisi (uyarı tonunda; engel değil). Kendisi
 * canlı bölge değildir: formda her zaman DOM'da duran `role="status"` kabının içine girer
 * (içeriğiyle birlikte doğan canlı bölgeyi ekran okuyucular çoğu zaman duyurmaz).
 */
export function KantinIsletmeBilgisi() {
  return (
    <div className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
      <Icon name="info" size="lg" className="shrink-0" />
      <span className="min-w-0">{KANTIN_ISLETME_BILGISI}</span>
    </div>
  );
}

/**
 * Onay kutusu ya da radyo grubu: `fieldset` + `legend`; yardım ya da hata metni gruba
 * `aria-describedby` ile bağlanır (hata belirince duyurulur — `TextField` sözleşmesi).
 */
function SecimGrubu({
  etiket,
  zorunlu,
  yardim,
  hata,
  className = "",
  children,
}: {
  etiket: string;
  zorunlu?: boolean;
  yardim?: string;
  hata?: string;
  className?: string;
  children: ReactNode;
}) {
  const id = useId();
  const aciklamaId = hata || yardim ? `${id}-desc` : undefined;
  return (
    <fieldset aria-describedby={aciklamaId} className={`min-w-0 ${className}`.trim()}>
      <legend className={ETIKET_SINIFI}>
        {etiket}
        {zorunlu && <span className="text-error"> *</span>}
      </legend>
      <div className="flex flex-wrap gap-x-6 gap-y-1">{children}</div>
      {(hata || yardim) && (
        <p
          id={aciklamaId}
          role={hata ? "alert" : undefined}
          className={`mt-1 text-body-small ${hata ? "text-error" : "text-on-surface-variant"}`}
        >
          {hata || yardim}
        </p>
      )}
    </fieldset>
  );
}

/** Grubun tek seçeneği (onay kutusu ya da radyo); uzun etiket sarar. */
function Secenek({
  tur,
  ad,
  etiket,
  secili,
  gecersiz,
  disabled,
  onSec,
}: {
  tur: "checkbox" | "radio";
  ad: string;
  etiket: string;
  secili: boolean;
  gecersiz: boolean;
  disabled?: boolean;
  onSec: (secili: boolean) => void;
}) {
  return (
    <label className="flex min-h-10 min-w-0 items-start gap-2 py-1.5 text-body-medium text-on-surface">
      <input
        type={tur}
        name={ad}
        checked={secili}
        disabled={disabled}
        aria-invalid={gecersiz ? true : undefined}
        onChange={(e) => onSec(e.target.checked)}
        className="mt-0.5 size-5 shrink-0 accent-primary"
      />
      <span className="min-w-0">{etiket}</span>
    </label>
  );
}

function RadyoGrubu<T extends string>({
  etiket,
  yardim,
  hata,
  secenekler: liste,
  deger,
  disabled,
  onSec,
}: {
  etiket: string;
  yardim: string;
  hata?: string;
  secenekler: { value: T; label: string }[];
  deger: T | "";
  disabled?: boolean;
  onSec: (deger: T) => void;
}) {
  const ad = useId();
  return (
    <SecimGrubu etiket={etiket} zorunlu yardim={yardim} hata={hata} className="sm:col-span-2">
      {liste.map((s) => (
        <Secenek
          key={s.value}
          tur="radio"
          ad={ad}
          etiket={s.label}
          secili={deger === s.value}
          gecersiz={Boolean(hata)}
          disabled={disabled}
          onSec={(secili) => {
            if (secili) onSec(s.value);
          }}
        />
      ))}
    </SecimGrubu>
  );
}

export interface OkulKartiAlanlariProps {
  form: OkulFormu;
  /** Alan hataları: backend alan kodu → ileti (`okulBilgileriHatalari` ya da sunucu). */
  errors: Partial<Record<string, string>>;
  onChange: (degisiklik: Partial<OkulFormu>) => void;
  disabled?: boolean;
}

/**
 * Okul kartının form alanları. Kendi `<form>`unu çizmez: çağıranın ızgarasına (iki sütun,
 * `sm:grid-cols-2`) girer; sihirbazda "Kaydet ve devam et", Ayarlar'da "Kaydet" çağırandadır.
 */
export default function OkulKartiAlanlari({
  form,
  errors,
  onChange,
  disabled,
}: OkulKartiAlanlariProps) {
  const kademeAd = useId();
  const bugun = todayIso();

  const kademeDegistir = (kademe: SchoolLevel, secili: boolean) => {
    const kalan = form.kademeler.filter((k) => k !== kademe);
    onChange({ kademeler: kademeleriSirala(secili ? [...kalan, kademe] : kalan) });
  };

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <TextField
        className="sm:col-span-2"
        label="Okul adı"
        required
        disabled={disabled}
        value={form.okulAdi}
        onChange={(e) => onChange({ okulAdi: e.target.value })}
        error={errors.school_name}
        placeholder="Örn. Örnek Anadolu Lisesi"
        helperText={OKUL_ADI_YARDIMI}
      />
      <TextField
        label="İl"
        required
        disabled={disabled}
        value={form.il}
        onChange={(e) => onChange({ il: e.target.value })}
        error={errors.province}
      />
      <TextField
        label="İlçe"
        required
        disabled={disabled}
        value={form.ilce}
        onChange={(e) => onChange({ ilce: e.target.value })}
        error={errors.district}
      />
      <TextField
        label="Okul müdürü"
        disabled={disabled}
        value={form.mudur}
        onChange={(e) => onChange({ mudur: e.target.value })}
        error={errors.principal_name}
        helperText="Evrak imza bloğunda görünür; boş bırakılırsa şablon yer tutucu basar."
      />
      <TextField
        label="Kurum kodu"
        required
        disabled={disabled}
        inputMode="numeric"
        autoComplete="off"
        // Uzunluk sınırı yok: tarayıcı `maxLength`i kırpmadan önce uygular, baştaki boşlukla
        // yapıştırılan geçerli kodun son hanesi düşerdi. Denetim kırpılmış değerdedir.
        value={form.kurumKodu}
        onChange={(e) => onChange({ kurumKodu: e.target.value })}
        error={errors.institution_code}
        helperText={KURUM_KODU_YARDIMI}
      />

      <SecimGrubu
        etiket="Kademe"
        zorunlu
        yardim={KADEME_YARDIMI}
        hata={errors.levels}
        className="sm:col-span-2"
      >
        {KADEMELER.map((k) => (
          <Secenek
            key={k.value}
            tur="checkbox"
            ad={kademeAd}
            etiket={k.label}
            secili={form.kademeler.includes(k.value)}
            gecersiz={Boolean(errors.levels)}
            disabled={disabled}
            onSec={(secili) => kademeDegistir(k.value, secili)}
          />
        ))}
      </SecimGrubu>

      <TextField
        label="Öğrenci mevcudu"
        required
        disabled={disabled}
        inputMode="numeric"
        autoComplete="off"
        value={form.mevcut}
        onChange={(e) => onChange({ mevcut: e.target.value })}
        error={errors.student_count}
        helperText={MEVCUT_YARDIMI}
      />
      <TextField
        label="Mevcudun tarihi"
        type="date"
        required
        disabled={disabled}
        max={bugun}
        value={form.mevcutTarihi}
        onChange={(e) => onChange({ mevcutTarihi: e.target.value })}
        error={errors.student_count_as_of}
        helperText={MEVCUT_TARIHI_YARDIMI}
      />

      <RadyoGrubu<SettlementType>
        etiket="Yerleşim türü"
        yardim={YERLESIM_YARDIMI}
        hata={errors.settlement_type}
        secenekler={YERLESIMLER}
        deger={form.yerlesim}
        disabled={disabled}
        onSec={(yerlesim) => onChange({ yerlesim })}
      />
      <RadyoGrubu<CanteenMode>
        etiket="Kantin işletme biçimi"
        yardim={KANTIN_YARDIMI}
        hata={errors.canteen_mode}
        secenekler={KANTINLER}
        deger={form.kantin}
        disabled={disabled}
        onSec={(kantin) => onChange({ kantin })}
      />
      {/* Canlı bölge her zaman DOM'dadır; bilgi seçimle içine girer (duyurulsun diye). */}
      <div role="status" className="empty:hidden sm:col-span-2">
        {form.kantin === "BIRLIKCE_ISLETILIYOR" && <KantinIsletmeBilgisi />}
      </div>
      <RadyoGrubu<StaffingMode>
        etiket="Personel çalıştırma biçimi"
        yardim={PERSONEL_YARDIMI}
        hata={errors.staffing_mode}
        secenekler={PERSONELLER}
        deger={form.personel}
        disabled={disabled}
        onSec={(personel) => onChange({ personel })}
      />

      <div className="min-w-0 sm:col-span-2">
        <label className="flex min-h-10 items-start gap-3 text-body-medium text-on-surface">
          <input
            type="checkbox"
            checked={form.kampus}
            disabled={disabled}
            onChange={(e) => onChange({ kampus: e.target.checked })}
            className="mt-0.5 size-5 shrink-0 accent-primary"
          />
          <span className="min-w-0">
            {KAMPUS_ETIKETI}
            <span className="mt-1 block text-body-small text-on-surface-variant">
              {KAMPUS_YARDIMI}
            </span>
          </span>
        </label>
        {errors.in_campus && (
          <p role="alert" className="mt-1 text-body-small text-error">
            {errors.in_campus}
          </p>
        )}
      </div>

      <TextField
        label="Okulun açılış tarihi"
        type="date"
        disabled={disabled}
        value={form.acilis}
        onChange={(e) => onChange({ acilis: e.target.value })}
        error={errors.opened_on}
        helperText={ACILIS_YARDIMI}
      />

      <TextField
        className="sm:col-span-2"
        label={VERI_SORUMLUSU_ETIKETI}
        disabled={disabled}
        maxLength={250}
        value={form.veriSorumlusu}
        onChange={(e) => onChange({ veriSorumlusu: e.target.value })}
        error={errors.data_controller_text}
        helperText={VERI_SORUMLUSU_YARDIMI}
      />

      <div className="sm:col-span-2">
        <DemirbasAlanlari
          onay={form.demirbasOnayi}
          no={form.demirbasNo}
          errors={errors}
          onOnay={(demirbasOnayi) => onChange({ demirbasOnayi })}
          onNo={(demirbasNo) => onChange({ demirbasNo })}
        />
      </div>
    </div>
  );
}

/** Öğrenci mevcudunun salt okur yazımı: "1.234 · 01.11.2026 itibarıyla"; girilmemişse "". */
export function mevcutYazimi(sayi: number | null, tarih: string | null): string {
  if (sayi === null) return "";
  return tarih ? `${formatNumber(sayi)} · ${formatDate(tarih)} itibarıyla` : formatNumber(sayi);
}

/**
 * Okul kartının salt okur listesi (`okul_karti_yazma` yeteneği olmayan rol): formun
 * etiketleriyle, boş değer "—". Kantin birlikçe işletiliyorsa md. 23/3'ün bilgisi burada da
 * görünür.
 */
export function OkulKartiListesi({ kayit }: { kayit: SchoolConfig }) {
  const satirlar: Array<[etiket: string, deger: string]> = [
    ["Okul adı", kayit.school_name],
    ["İl", kayit.province],
    ["İlçe", kayit.district],
    ["Okul müdürü", kayit.principal_name],
    ["Kurum kodu", kayit.institution_code],
    [
      "Kademe",
      kademeleriSirala(kayit.levels)
        .map((k) => SCHOOL_LEVEL_TR[k])
        .join(", "),
    ],
    ["Öğrenci mevcudu", mevcutYazimi(kayit.student_count, kayit.student_count_as_of)],
    ["Yerleşim türü", kayit.settlement_type ? SETTLEMENT_TYPE_TR[kayit.settlement_type] : ""],
    ["Kantin işletme biçimi", kayit.canteen_mode ? CANTEEN_MODE_TR[kayit.canteen_mode] : ""],
    [
      "Personel çalıştırma biçimi",
      kayit.staffing_mode ? STAFFING_MODE_TR[kayit.staffing_mode] : "",
    ],
    [KAMPUS_ETIKETI, kayit.in_campus ? "Evet" : "Hayır"],
    ["Okulun açılış tarihi", kayit.opened_on ? formatDate(kayit.opened_on) : ""],
    ["Bilgisayarın demirbaş no'su", kayit.demirbas_no],
    [VERI_SORUMLUSU_ETIKETI, kayit.data_controller_text],
  ];
  return (
    <>
      <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
        {satirlar.map(([etiket, deger]) => (
          <div key={etiket} className="min-w-0">
            <dt className="text-label-medium text-on-surface-variant">{etiket}</dt>
            <dd className="break-words text-body-large text-on-surface">{deger.trim() || "—"}</dd>
          </div>
        ))}
      </dl>
      {kayit.canteen_mode === "BIRLIKCE_ISLETILIYOR" && (
        <div className="mt-4">
          <KantinIsletmeBilgisi />
        </div>
      )}
      {kayit.demirbas_onayi && (
        <p className="mt-4 text-body-medium text-on-surface">Bu bilgisayar okul demirbaşıdır.</p>
      )}
    </>
  );
}
