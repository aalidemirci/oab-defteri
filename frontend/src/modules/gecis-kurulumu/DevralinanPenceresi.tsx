// Görevdeki kurulun üyesi ya da birlik temsilcisi: devralınan kayıt (tasarım §7.9 adım 2; plan F1c 8.
// adım). Aday kaydı aranmaz; koltuk uygunluğu (kişi türü, okul müdürü yasağı, aynı kişinin iki kurulda
// bulunması, tek koltuk, görev tekilliği) sunucuda SERTTİR: ret, madde atfıyla bant olarak görünür. Uyarı
// gerektiren kayıt gerekçeyle yazılır (ortak "uyarı + gerekçe" bileşeni). Görev yalnız asıl üyeye verilir
// (tasarım §7.2 "asıl üyeler arasından"); Denetleme Kurulunda görevler başkan ve üyedir.

import { useCallback, useState } from "react";

import { useFormErrors } from "../../hooks/useFormErrors";
import Autocomplete from "../../ui/Autocomplete";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { BIRLIK_KISI_TURU_TR } from "../kisiler/birlikKisileriApi";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { TEMSIL_TURU_TR, gecisApi } from "./api";
import type {
  DevralinanGovdesi,
  KoltukGrubu,
  KoltukTuru,
  SecimKanali,
  TemsilTuru,
  UyelikGorevi,
} from "./api";
import {
  ALAN_GOREV,
  ALAN_KANIT,
  ALAN_KISI,
  ALAN_KOLTUK,
  ALAN_KOLTUK_GRUBU,
  ALAN_KURUL,
  ALAN_MEM_ONAY_NO,
  ALAN_SECILDIGI_GUN,
  ALAN_SECIM_KANALI,
  ALAN_TEMSIL,
  ALAN_YEDEK_SIRASI,
  GOREV_TR,
  KANIT_YARDIMI,
  KISI_ARA_YER_TUTUCU,
  KISI_BULUNAMADI,
  KISI_SECIN,
  KOLTUK_ASIL,
  KOLTUK_GRUBU_OGRETMEN,
  KOLTUK_GRUBU_VELI,
  KOLTUK_YEDEK,
  KURUL_DENETLEME,
  KURUL_TEMSILCI,
  KURUL_YONETIM,
  SECILDIGI_GUN_YARDIMI,
  SECIM_KANALI_MEM,
  SECIM_KANALI_OGRETMENLER_KURULU,
  TEMSIL_SECIN,
  UYE_EKLENDI,
  UYE_EKLENEMEDI,
  UYE_PENCERESI_BASLIGI,
} from "./metinler";

type Kurul = "YK" | "DK" | "TEMSILCI";

const KURUL_SECENEKLERI = [
  { value: "YK", label: KURUL_YONETIM },
  { value: "DK", label: KURUL_DENETLEME },
  { value: "TEMSILCI", label: KURUL_TEMSILCI },
];

const KOLTUK_SECENEKLERI = [
  { value: "ASIL", label: KOLTUK_ASIL },
  { value: "YEDEK", label: KOLTUK_YEDEK },
];

const GRUP_SECENEKLERI = [
  { value: "VELI", label: KOLTUK_GRUBU_VELI },
  { value: "OGRETMEN", label: KOLTUK_GRUBU_OGRETMEN },
];

const YK_GOREVLERI: UyelikGorevi[] = ["BASKAN", "BASKAN_YARDIMCISI", "MUHASIP", "SEKRETER", "UYE"];
const DK_GOREVLERI: UyelikGorevi[] = ["BASKAN", "UYE"];

const OGRETMEN_KANALLARI = [
  { value: "OGRETMENLER_KURULU", label: SECIM_KANALI_OGRETMENLER_KURULU },
  { value: "MEM_GOREVLENDIRME", label: SECIM_KANALI_MEM },
];

const TEMSIL_SECENEKLERI = (Object.entries(TEMSIL_TURU_TR) as [TemsilTuru, string][]).map(
  ([value, label]) => ({ value, label }),
);

/** Formun değerlerinden gövde (dosya başı: alanlar kurula ve koltuğa göre). */
export function devralinanGovdesi(f: {
  kisi: number;
  kurul: Kurul;
  koltuk: KoltukTuru;
  grup: KoltukGrubu;
  gorev: UyelikGorevi;
  kanal: SecimKanali;
  temsil: TemsilTuru | "";
  sira: string;
  gun: string;
  kanit: string;
  memNo: string;
}): DevralinanGovdesi {
  const ortak = {
    person: f.kisi,
    seat_type: f.koltuk,
    start_date: f.gun || null,
    evidence_note: f.kanit.trim(),
  };
  if (f.kurul === "TEMSILCI") {
    return { ...ortak, organ: "TEMSILCI", representation: f.temsil };
  }
  const asil = f.koltuk === "ASIL";
  const govde: DevralinanGovdesi = {
    ...ortak,
    organ: f.kurul,
    role: asil ? f.gorev : "UYE",
    seat_order: !asil && f.sira ? Number(f.sira) : null,
    elected_by: "GENEL_KURUL",
  };
  if (f.kurul === "DK") {
    govde.seat_group = f.grup;
    if (f.grup === "OGRETMEN") {
      govde.elected_by = f.kanal;
      if (f.kanal === "MEM_GOREVLENDIRME") govde.mem_approval_no = f.memNo.trim();
    }
  }
  return govde;
}

export default function DevralinanPenceresi({
  kisiler,
  onKapat,
  onEklendi,
}: {
  /** Seçilebilecek etkin birlik kişileri. */
  kisiler: readonly BirlikKisisi[];
  onKapat: () => void;
  onEklendi: () => void;
}) {
  const snackbar = useSnackbar();
  const [kisi, setKisi] = useState<BirlikKisisi | null>(null);
  const [kurul, setKurul] = useState<Kurul>("YK");
  const [koltuk, setKoltuk] = useState<KoltukTuru>("ASIL");
  const [grup, setGrup] = useState<KoltukGrubu>("VELI");
  const [gorev, setGorev] = useState<UyelikGorevi>("UYE");
  const [kanal, setKanal] = useState<SecimKanali>("OGRETMENLER_KURULU");
  const [temsil, setTemsil] = useState<TemsilTuru | "">("");
  const [sira, setSira] = useState("");
  const [gun, setGun] = useState("");
  const [kanit, setKanit] = useState("");
  const [memNo, setMemNo] = useState("");
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors();
  const ug = useUyariGerekce("gecis.devralinan");

  // Arama işlevi kararlı olmalı: `Autocomplete` onu etkinin bağımlılığında tutar (her çizimde yeni
  // işlev aramayı yeniden başlatırdı).
  const ara = useCallback(
    async (sorgu: string) => {
      const aranan = sorgu.toLocaleLowerCase("tr");
      return kisiler.filter((k) => (k.full_name ?? "").toLocaleLowerCase("tr").includes(aranan));
    },
    [kisiler],
  );

  // Vazgeçilince yarım metin silinir (kayıt yapılmadı).
  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const kurulDegisti = (yeni: Kurul) => {
    setKurul(yeni);
    setGorev("UYE");
  };

  const gonder = async () => {
    clearErrors();
    setHata(null);
    let eksik = false;
    if (kisi === null) {
      setFieldError("person", KISI_SECIN);
      eksik = true;
    }
    if (kurul === "TEMSILCI" && !temsil) {
      setFieldError("representation", TEMSIL_SECIN);
      eksik = true;
    }
    if (eksik || kisi === null || !ug.hazir()) return;
    setBusy(true);
    try {
      await gecisApi.devralinanEkle({
        ...devralinanGovdesi({
          kisi: kisi.id,
          kurul,
          koltuk,
          grup,
          gorev,
          kanal,
          temsil,
          sira,
          gun,
          kanit,
          memNo,
        }),
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(UYE_EKLENDI);
      onEklendi();
    } catch (e) {
      if (!ug.yakala(e)) {
        applyApiError(e);
        setHata(hataOku(e, UYE_EKLENEMEDI));
      }
      setBusy(false);
    }
  };

  const gorevler = kurul === "DK" ? DK_GOREVLERI : YK_GOREVLERI;

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={UYE_PENCERESI_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={vazgec} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="check" onClick={() => void gonder()} disabled={busy}>
            {busy ? "Kaydediliyor…" : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : "Kaydet"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        <UyariGerekceAlani durum={ug} />
        <Autocomplete<BirlikKisisi>
          label={ALAN_KISI}
          required
          placeholder={KISI_ARA_YER_TUTUCU}
          selected={kisi}
          minChars={1}
          search={ara}
          onSelect={setKisi}
          onClear={() => setKisi(null)}
          getLabel={(k) => k.full_name ?? ""}
          getSublabel={(k) => BIRLIK_KISI_TURU_TR[k.kind]}
          getKey={(k) => k.id}
          emptyText={KISI_BULUNAMADI}
          error={errors.person}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label={ALAN_KURUL}
            value={kurul}
            onChange={(e) => kurulDegisti(e.target.value as Kurul)}
            options={KURUL_SECENEKLERI}
          />
          <Select
            label={ALAN_KOLTUK}
            value={koltuk}
            onChange={(e) => setKoltuk(e.target.value as KoltukTuru)}
            options={KOLTUK_SECENEKLERI}
          />
          {kurul === "TEMSILCI" && (
            <Select
              className="sm:col-span-2"
              label={ALAN_TEMSIL}
              required
              value={temsil}
              onChange={(e) => setTemsil(e.target.value as TemsilTuru)}
              options={TEMSIL_SECENEKLERI}
              placeholder="Seçin"
              error={errors.representation}
            />
          )}
          {kurul === "DK" && (
            <Select
              label={ALAN_KOLTUK_GRUBU}
              value={grup}
              onChange={(e) => setGrup(e.target.value as KoltukGrubu)}
              options={GRUP_SECENEKLERI}
              error={errors.seat_group}
            />
          )}
          {kurul === "DK" && grup === "OGRETMEN" && (
            <Select
              label={ALAN_SECIM_KANALI}
              value={kanal}
              onChange={(e) => setKanal(e.target.value as SecimKanali)}
              options={OGRETMEN_KANALLARI}
              error={errors.elected_by}
            />
          )}
          {kurul === "DK" && grup === "OGRETMEN" && kanal === "MEM_GOREVLENDIRME" && (
            <TextField
              label={ALAN_MEM_ONAY_NO}
              value={memNo}
              maxLength={64}
              onChange={(e) => setMemNo(e.target.value)}
              error={errors.mem_approval_no}
            />
          )}
          {kurul !== "TEMSILCI" && koltuk === "ASIL" && (
            <Select
              label={ALAN_GOREV}
              value={gorev}
              onChange={(e) => setGorev(e.target.value as UyelikGorevi)}
              options={gorevler.map((g) => ({ value: g, label: GOREV_TR[g] }))}
              error={errors.role}
            />
          )}
          {kurul !== "TEMSILCI" && koltuk === "YEDEK" && (
            <TextField
              label={ALAN_YEDEK_SIRASI}
              type="number"
              min={1}
              value={sira}
              onChange={(e) => setSira(e.target.value)}
              error={errors.seat_order}
            />
          )}
          <TextField
            label={ALAN_SECILDIGI_GUN}
            type="date"
            value={gun}
            onChange={(e) => setGun(e.target.value)}
            error={errors.start_date}
            helperText={SECILDIGI_GUN_YARDIMI}
          />
          <TextField
            className="sm:col-span-2"
            label={ALAN_KANIT}
            value={kanit}
            maxLength={1000}
            onChange={(e) => setKanit(e.target.value)}
            error={errors.evidence_note}
            helperText={KANIT_YARDIMI}
          />
        </div>
      </div>
    </Dialog>
  );
}
