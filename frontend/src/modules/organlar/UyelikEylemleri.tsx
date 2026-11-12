// Üyeliğin eylem pencereleri (plan F1c 6. adımın uçları; 11. adımın ekranı): görev alma engeli, kişisiz
// bilgiler, yedek çağrısı ve düşme. Uyarı gerektiren kayıt ortak "uyarı + gerekçe" bileşeniyle yazılır
// (sunucu 400 `gerekce_gerekli` → kutu açılır, aynı istek gerekçeyle yinelenir); sert engel ve dönem
// kilidi bantla gösterilir; öteki retler sunucunun iletisiyle hata bandındadır.
//
// Görev alma engelinin DAYANAĞI özel nitelikli veridir: pencere onu önceden okumaz (okuma erişim
// günlüğüne yazılırdı); yeni değer yazılırken seçilir. Yedek çağrısında yönetim kurulunun kararı yalnız
// kabul edilmiş ya da deftere işlenmiş yedek çağırma kararı olabilir; karar yoksa bağ verilmez ve sunucu
// gerekçe ister (akış satırı, Yönetmelik hükmü değildir). Düşmede "Olağanüstü genel kurul seçimi" türü
// elle seçilmez: o düşmeyi olağanüstü genel kurulun seçimi yazar.

import { useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import {
  ALAN_MEM_ONAY_NO,
  ALAN_YEDEK_SIRASI,
  PROGRAMA_BASLAMA_YARDIMI,
} from "../gecis-kurulumu/metinler";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { organlarApi } from "./api";
import type { DusmeTuru, EngelDayanagi, KadroOrgani, Uyelik, UyelikGuncellemesi } from "./api";
import {
  ALAN_DAYANAK,
  ALAN_DUSME_ACIKLAMASI,
  ALAN_DUSME_GUNU,
  ALAN_DUSME_TURU,
  ALAN_CAGRI_GUNU_GIRIS,
  ALAN_ENGEL_HUKMU,
  ALAN_ERTELE,
  ALAN_GOREVLENDIRME_BASLANGICI,
  ALAN_GOREVLENDIRME_BITISI,
  ALAN_KARAR_BAGLANMASIN,
  ALAN_SUC_BEYANI,
  ALAN_TEK_BIRLIK_BEYANI,
  ALAN_TESPIT_GUNU,
  ALAN_YEDEK_KARARI,
  BEYAN_YARDIMI,
  BILGILER_KAYDEDILDI,
  BILGILER_KAYDEDILEMEDI,
  BILGI_PENCERESI_BASLIGI,
  DUGME_DUSUR,
  DUGME_YEDEK_CAGIR,
  DUSME_ACIKLAMASI_YARDIMI,
  DUSME_METNI,
  DUSME_PENCERESI_BASLIGI,
  DUSME_TURU_SECIN,
  DUSME_TURU_TR,
  ENGEL_ACIKLAMASI,
  ENGEL_DAYANAGI_TR,
  ENGEL_DAYANAK_ZORUNLU,
  ENGEL_KAYDEDILDI,
  ENGEL_KAYDEDILEMEDI,
  ENGEL_PENCERESI_BASLIGI,
  ENGEL_VAR,
  ENGEL_YOK,
  ERTELE_YARDIMI,
  GOREVLENDIRME_YARDIMI,
  KARAR_BAGI_YARDIMI,
  KARAR_YOK,
  UYELIK_DUSURULDU,
  UYELIK_DUSURULEMEDI,
  UYELIK_ERTELENDI,
  YEDEK_CAGRILAMADI,
  YEDEK_CAGRILDI,
  YEDEK_METNI_DK,
  YEDEK_METNI_YK,
  YEDEK_PENCERESI_BASLIGI,
} from "./metinler";
import { PencereHatasi, kararSecenekleri, useBaglanabilirKararlar } from "./ortak";

const KAYDEDILIYOR = "Kaydediliyor…";

interface PencereProps {
  uyelik: Uyelik;
  onKapat: () => void;
  /** Kayıt yapıldı: pencere kapanır, kadro yeniden okunur. */
  onKaydedildi: () => void;
}

function Eylemler({
  busy,
  onVazgec,
  onGonder,
  etiket,
}: {
  busy: boolean;
  onVazgec: () => void;
  onGonder: () => void;
  etiket: string;
}) {
  return (
    <>
      <Button variant="text" onClick={onVazgec} disabled={busy}>
        Vazgeç
      </Button>
      <Button icon="check" onClick={onGonder} disabled={busy}>
        {busy ? KAYDEDILIYOR : etiket}
      </Button>
    </>
  );
}

// ---------------------------------------------------------------------------
// Görev alma engeli
// ---------------------------------------------------------------------------
const DAYANAK_SECENEKLERI = (Object.entries(ENGEL_DAYANAGI_TR) as [EngelDayanagi, string][]).map(
  ([value, label]) => ({ value, label }),
);

export function EngelPenceresi({ uyelik, onKapat, onKaydedildi }: PencereProps) {
  const snackbar = useSnackbar();
  const [hukum, setHukum] = useState<"VAR" | "YOK">(uyelik.eligibility_bar);
  const [dayanak, setDayanak] = useState<EngelDayanagi | "">("");
  const [gun, setGun] = useState(uyelik.eligibility_bar_found_on ?? "");
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const gonder = async () => {
    setHata(null);
    if (hukum === "VAR" && (!dayanak || !gun)) {
      setAlanHatasi(ENGEL_DAYANAK_ZORUNLU);
      return;
    }
    setBusy(true);
    try {
      await organlarApi.engelYaz(uyelik.id, {
        eligibility_bar: hukum,
        eligibility_bar_basis: hukum === "VAR" ? dayanak : "",
        eligibility_bar_found_on: hukum === "VAR" ? gun : null,
      });
      snackbar.success(ENGEL_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      setHata(hataOku(e, ENGEL_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={ENGEL_PENCERESI_BASLIGI}
      actions={
        <Eylemler busy={busy} onVazgec={onKapat} onGonder={() => void gonder()} etiket="Kaydet" />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <p className="text-body-medium text-on-surface-variant">{ENGEL_ACIKLAMASI}</p>
        <Select
          label={ALAN_ENGEL_HUKMU}
          value={hukum}
          onChange={(e) => {
            setHukum(e.target.value as "VAR" | "YOK");
            setAlanHatasi(undefined);
          }}
          options={[
            { value: "YOK", label: ENGEL_YOK },
            { value: "VAR", label: ENGEL_VAR },
          ]}
        />
        {hukum === "VAR" && (
          <>
            <Select
              label={ALAN_DAYANAK}
              required
              placeholder="Seçin"
              value={dayanak}
              onChange={(e) => {
                setDayanak(e.target.value as EngelDayanagi);
                setAlanHatasi(undefined);
              }}
              options={DAYANAK_SECENEKLERI}
              error={alanHatasi}
            />
            <TextField
              label={ALAN_TESPIT_GUNU}
              type="date"
              required
              value={gun}
              onChange={(e) => {
                setGun(e.target.value);
                setAlanHatasi(undefined);
              }}
            />
          </>
        )}
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Kişisiz bilgiler (beyan günleri, görevlendirme, MEM onay no, yedek sırası)
// ---------------------------------------------------------------------------
/** Değişen alanların gövdesi (değişmeyen alan gitmez; boş gün `null`). */
export function bilgiGovdesi(
  uyelik: Uyelik,
  form: Record<keyof UyelikGuncellemesi, string>,
): UyelikGuncellemesi {
  const govde: UyelikGuncellemesi = {};
  const gunAlanlari = [
    "eligibility_declared_on",
    "single_birlik_declared_on",
    "external_assignment_start",
    "external_assignment_end",
  ] as const;
  for (const alan of gunAlanlari) {
    const yeni = form[alan] || null;
    if (yeni !== (uyelik[alan] ?? null)) govde[alan] = yeni;
  }
  const memNo = form.mem_approval_no.trim();
  if (memNo !== uyelik.mem_approval_no) govde.mem_approval_no = memNo;
  const sira = form.seat_order ? Number(form.seat_order) : null;
  if (sira !== uyelik.seat_order) govde.seat_order = sira;
  return govde;
}

export function BilgiPenceresi({ uyelik, onKapat, onKaydedildi }: PencereProps) {
  const snackbar = useSnackbar();
  const ogretmen = uyelik.organ === "DK" && uyelik.seat_group === "OGRETMEN";
  const [form, setForm] = useState<Record<keyof UyelikGuncellemesi, string>>({
    eligibility_declared_on: uyelik.eligibility_declared_on ?? "",
    single_birlik_declared_on: uyelik.single_birlik_declared_on ?? "",
    external_assignment_start: uyelik.external_assignment_start ?? "",
    external_assignment_end: uyelik.external_assignment_end ?? "",
    mem_approval_no: uyelik.mem_approval_no,
    seat_order: uyelik.seat_order === null ? "" : String(uyelik.seat_order),
  });
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const alan = (ad: keyof UyelikGuncellemesi) => ({
    value: form[ad],
    onChange: (e: { target: { value: string } }) =>
      setForm((f) => ({ ...f, [ad]: e.target.value })),
  });

  const gonder = async () => {
    const govde = bilgiGovdesi(uyelik, form);
    if (Object.keys(govde).length === 0) {
      onKapat();
      return;
    }
    setBusy(true);
    setHata(null);
    try {
      await organlarApi.guncelle(uyelik.id, govde);
      snackbar.success(BILGILER_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      setHata(hataOku(e, BILGILER_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={onKapat}
      title={BILGI_PENCERESI_BASLIGI}
      actions={
        <Eylemler busy={busy} onVazgec={onKapat} onGonder={() => void gonder()} etiket="Kaydet" />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label={ALAN_SUC_BEYANI}
            type="date"
            helperText={BEYAN_YARDIMI}
            {...alan("eligibility_declared_on")}
          />
          {uyelik.organ === "YK" && (
            <TextField
              label={ALAN_TEK_BIRLIK_BEYANI}
              type="date"
              helperText={BEYAN_YARDIMI}
              {...alan("single_birlik_declared_on")}
            />
          )}
          {uyelik.seat_type === "YEDEK" && (
            <TextField label={ALAN_YEDEK_SIRASI} type="number" min={1} {...alan("seat_order")} />
          )}
          {ogretmen && (
            <>
              <TextField label={ALAN_MEM_ONAY_NO} maxLength={64} {...alan("mem_approval_no")} />
              <TextField
                label={ALAN_GOREVLENDIRME_BASLANGICI}
                type="date"
                helperText={GOREVLENDIRME_YARDIMI}
                {...alan("external_assignment_start")}
              />
              <TextField
                label={ALAN_GOREVLENDIRME_BITISI}
                type="date"
                {...alan("external_assignment_end")}
              />
            </>
          )}
        </div>
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Yedek çağrısı (yönetim kurulu: sekreter, karar bağıyla; Denetleme Kurulu: program yöneticisi)
// ---------------------------------------------------------------------------
export function YedekPenceresi({
  uyelik,
  organ,
  onKapat,
  onKaydedildi,
}: PencereProps & { organ: KadroOrgani }) {
  const snackbar = useSnackbar();
  const yk = organ === "YK";
  const kararlar = useBaglanabilirKararlar(uyelik.term, "YEDEK_CAGIRMA");
  const [gun, setGun] = useState("");
  const [karar, setKarar] = useState("");
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  // Bağlam kurulludur: pano kalemi taslağın yazıldığı kurulun sekmesine götürür (pano.TASLAK_EKRANLARI).
  const ug = useUyariGerekce(yk ? "organlar.yedek_cagrisi.yk" : "organlar.yedek_cagrisi.dk");

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    if (!ug.hazir()) return;
    setBusy(true);
    setHata(null);
    try {
      if (yk) {
        await organlarApi.ykYedekCagir(uyelik.id, {
          promoted_on: gun || null,
          promoted_by_decision: karar ? Number(karar) : null,
          ...ug.ek(),
        });
      } else {
        await organlarApi.dkYedekCagir(uyelik.id, gun || null);
      }
      ug.sifirla();
      snackbar.success(YEDEK_CAGRILDI);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, YEDEK_CAGRILAMADI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={vazgec}
      title={YEDEK_PENCERESI_BASLIGI}
      actions={
        <Eylemler
          busy={busy}
          onVazgec={vazgec}
          onGonder={() => void gonder()}
          etiket={ug.gerekceIstendi ? GEREKCEYLE_KAYDET : DUGME_YEDEK_CAGIR}
        />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <p className="break-words text-body-large text-on-surface">{uyelik.person_name ?? "—"}</p>
        <p className="text-body-medium text-on-surface-variant">
          {yk ? YEDEK_METNI_YK : YEDEK_METNI_DK}
        </p>
        <TextField
          label={ALAN_CAGRI_GUNU_GIRIS}
          type="date"
          value={gun}
          onChange={(e) => setGun(e.target.value)}
          helperText={PROGRAMA_BASLAMA_YARDIMI}
        />
        {yk &&
          (kararlar.length === 0 ? (
            <p className="text-body-medium text-on-surface-variant">{KARAR_YOK}</p>
          ) : (
            <Select
              label={ALAN_YEDEK_KARARI}
              value={karar}
              onChange={(e) => setKarar(e.target.value)}
              options={[
                { value: "", label: ALAN_KARAR_BAGLANMASIN },
                ...kararSecenekleri(kararlar),
              ]}
              helperText={KARAR_BAGI_YARDIMI}
            />
          ))}
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Düşme
// ---------------------------------------------------------------------------
/** Elle seçilebilen düşme türleri: olağanüstü genel kurulun seçimi o akışın düşmesidir (dosya başı). */
const ELLE_DUSME_TURLERI: DusmeTuru[] = [
  "OGRENCI_AYRILDI",
  "DEVAMSIZLIK",
  "ISTIFA",
  "BASKA_KURUMDA_GOREV",
  "DIGER",
];

export function DusmePenceresi({
  uyelik,
  onKapat,
  onKaydedildi,
  onerilenTur,
  onerilenGun,
}: PencereProps & { onerilenTur?: DusmeTuru | ""; onerilenGun?: string | null }) {
  const snackbar = useSnackbar();
  const [tur, setTur] = useState<DusmeTuru | "">(onerilenTur ?? "");
  const [gun, setGun] = useState(onerilenGun ?? "");
  const [aciklama, setAciklama] = useState("");
  const [ertele, setErtele] = useState(false);
  const [turHatasi, setTurHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  // Bağlam kurulludur (pencere yalnız yönetim kurulu ve Denetleme Kurulu sekmesinde açılır).
  const ug = useUyariGerekce(uyelik.organ === "YK" ? "organlar.dusme.yk" : "organlar.dusme.dk");
  // md. 7/2: yalnız yönetim kurulunda, öğrencisi ayrılan velinin (ya da kursiyerin) üyeliğinde.
  const erteleVar = uyelik.organ === "YK" && tur === "OGRENCI_AYRILDI";

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    if (!tur) {
      setTurHatasi(DUSME_TURU_SECIN);
      return;
    }
    if (!ug.hazir()) return;
    setBusy(true);
    setHata(null);
    try {
      await organlarApi.dusur(uyelik.id, {
        drop_kind: tur,
        end_date: gun || null,
        dropped_reason: aciklama.trim(),
        ertele: erteleVar && ertele,
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(erteleVar && ertele ? UYELIK_ERTELENDI : UYELIK_DUSURULDU);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, UYELIK_DUSURULEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={vazgec}
      title={DUSME_PENCERESI_BASLIGI}
      actions={
        <Eylemler
          busy={busy}
          onVazgec={vazgec}
          onGonder={() => void gonder()}
          etiket={ug.gerekceIstendi ? GEREKCEYLE_KAYDET : DUGME_DUSUR}
        />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <p className="break-words text-body-large text-on-surface">{uyelik.person_name ?? "—"}</p>
        <p className="text-body-medium text-on-surface-variant">{DUSME_METNI}</p>
        <Select
          label={ALAN_DUSME_TURU}
          required
          placeholder="Seçin"
          value={tur}
          onChange={(e) => {
            setTur(e.target.value as DusmeTuru);
            setTurHatasi(undefined);
          }}
          options={ELLE_DUSME_TURLERI.map((t) => ({ value: t, label: DUSME_TURU_TR[t] }))}
          error={turHatasi}
        />
        <TextField
          label={ALAN_DUSME_GUNU}
          type="date"
          value={gun}
          onChange={(e) => setGun(e.target.value)}
          helperText={PROGRAMA_BASLAMA_YARDIMI}
        />
        <TextField
          label={ALAN_DUSME_ACIKLAMASI}
          value={aciklama}
          maxLength={1000}
          onChange={(e) => setAciklama(e.target.value)}
          helperText={DUSME_ACIKLAMASI_YARDIMI}
        />
        {erteleVar && (
          <label className="flex items-start gap-3 text-body-medium text-on-surface">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 shrink-0 accent-primary"
              checked={ertele}
              onChange={(e) => setErtele(e.target.checked)}
            />
            <span className="min-w-0">
              <span className="block">{ALAN_ERTELE}</span>
              <span className="block text-body-small text-on-surface-variant">
                {ERTELE_YARDIMI}
              </span>
            </span>
          </label>
        )}
      </div>
    </Dialog>
  );
}
