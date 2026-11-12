// Organlar ekranının kayıt pencereleri: Denetleme Kurulunun öğretmen koltuğuna seçilmiş üye (öğretmenler
// kurulu ya da il/ilçe millî eğitim müdürlüğü görevlendirmesi; genel kurul dışı kanal, doğrudan seçilmiş
// açılır) ve alım komisyonu üyesi (md. 18/1). Yönetim kurulu ve Denetleme Kurulunun veli koltuğu genel
// kurulda seçilir: genel kurul akışıyla gelir, bu pencerede yoktur. Koltuk uygunluğu (kişi türü, aynı
// kişinin iki kurulda bulunmaması, tek koltuk) sunucuda serttir: ret, madde atfıyla bant olarak görünür;
// uyarı gerektiren kayıt (ör. onay no'su girilmemiş görevlendirme) gerekçeyle yazılır.

import { useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import {
  ALAN_KANIT,
  ALAN_KOLTUK,
  ALAN_MEM_ONAY_NO,
  ALAN_SECILDIGI_GUN,
  ALAN_SECIM_KANALI,
  ALAN_YEDEK_SIRASI,
  KANIT_YARDIMI,
  KISI_SECIN,
  KOLTUK_ASIL,
  KOLTUK_YEDEK,
  PROGRAMA_BASLAMA_YARDIMI,
  SECIM_KANALI_MEM,
  SECIM_KANALI_OGRETMENLER_KURULU,
} from "../gecis-kurulumu/metinler";
import type { KoltukTuru } from "../gecis-kurulumu/api";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { organlarApi } from "./api";
import type { OgretmenUyeGovdesi } from "./api";
import {
  ALAN_BASLANGIC_GUNU,
  ALAN_UZMANLIK,
  ALIM_ACIKLAMASI,
  KOMISYON_PENCERESI_BASLIGI,
  OGRETMEN_ACIKLAMASI,
  OGRETMEN_PENCERESI_BASLIGI,
  UYE_EKLENDI,
  UYE_EKLENEMEDI,
  UZMANLIK_YARDIMI,
} from "./metinler";
import { KisiSecimi, PencereHatasi, useEtkinKisiler } from "./ortak";

type Kanal = OgretmenUyeGovdesi["elected_by"];

/** Formdan gövde (yedek sırası yalnız yedekte, onay no yalnız görevlendirmede). */
export function ogretmenGovdesi(f: {
  donem: number;
  kisi: number;
  koltuk: KoltukTuru;
  kanal: Kanal;
  sira: string;
  gun: string;
  kanit: string;
  memNo: string;
}): OgretmenUyeGovdesi {
  return {
    term: f.donem,
    person: f.kisi,
    organ: "DK",
    seat_type: f.koltuk,
    seat_group: "OGRETMEN",
    elected_by: f.kanal,
    start_date: f.gun || null,
    seat_order: f.koltuk === "YEDEK" && f.sira ? Number(f.sira) : null,
    evidence_note: f.kanit.trim(),
    mem_approval_no: f.kanal === "MEM_GOREVLENDIRME" ? f.memNo.trim() : "",
  };
}

interface Props {
  donem: number;
  onKapat: () => void;
  onEklendi: () => void;
}

function Eylemler({
  busy,
  gerekce,
  onVazgec,
  onGonder,
}: {
  busy: boolean;
  gerekce: boolean;
  onVazgec: () => void;
  onGonder: () => void;
}) {
  return (
    <>
      <Button variant="text" onClick={onVazgec} disabled={busy}>
        Vazgeç
      </Button>
      <Button icon="check" onClick={onGonder} disabled={busy}>
        {busy ? "Kaydediliyor…" : gerekce ? GEREKCEYLE_KAYDET : "Kaydet"}
      </Button>
    </>
  );
}

export function OgretmenUyePenceresi({ donem, onKapat, onEklendi }: Props) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const [kisi, setKisi] = useState<BirlikKisisi | null>(null);
  const [koltuk, setKoltuk] = useState<KoltukTuru>("ASIL");
  const [kanal, setKanal] = useState<Kanal>("OGRETMENLER_KURULU");
  const [sira, setSira] = useState("");
  const [gun, setGun] = useState("");
  const [kanit, setKanit] = useState("");
  const [memNo, setMemNo] = useState("");
  const [kisiHatasi, setKisiHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const ug = useUyariGerekce("organlar.ogretmen_uye");

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    setHata(null);
    if (kisi === null) {
      setKisiHatasi(KISI_SECIN);
      return;
    }
    if (!ug.hazir()) return;
    setBusy(true);
    try {
      await organlarApi.ogretmenUyeEkle({
        ...ogretmenGovdesi({ donem, kisi: kisi.id, koltuk, kanal, sira, gun, kanit, memNo }),
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(UYE_EKLENDI);
      onEklendi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, UYE_EKLENEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={OGRETMEN_PENCERESI_BASLIGI}
      actions={
        <Eylemler
          busy={busy}
          gerekce={ug.gerekceIstendi}
          onVazgec={vazgec}
          onGonder={() => void gonder()}
        />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <p className="text-body-medium text-on-surface-variant">{OGRETMEN_ACIKLAMASI}</p>
        <KisiSecimi
          kisiler={kisiler}
          secili={kisi}
          onSecim={(k) => {
            setKisi(k);
            setKisiHatasi(undefined);
          }}
          hata={kisiHatasi}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label={ALAN_KOLTUK}
            value={koltuk}
            onChange={(e) => setKoltuk(e.target.value as KoltukTuru)}
            options={[
              { value: "ASIL", label: KOLTUK_ASIL },
              { value: "YEDEK", label: KOLTUK_YEDEK },
            ]}
          />
          <Select
            label={ALAN_SECIM_KANALI}
            value={kanal}
            onChange={(e) => setKanal(e.target.value as Kanal)}
            options={[
              { value: "OGRETMENLER_KURULU", label: SECIM_KANALI_OGRETMENLER_KURULU },
              { value: "MEM_GOREVLENDIRME", label: SECIM_KANALI_MEM },
            ]}
          />
          {kanal === "MEM_GOREVLENDIRME" && (
            <TextField
              label={ALAN_MEM_ONAY_NO}
              value={memNo}
              maxLength={64}
              onChange={(e) => setMemNo(e.target.value)}
            />
          )}
          {koltuk === "YEDEK" && (
            <TextField
              label={ALAN_YEDEK_SIRASI}
              type="number"
              min={1}
              value={sira}
              onChange={(e) => setSira(e.target.value)}
            />
          )}
          <TextField
            label={ALAN_SECILDIGI_GUN}
            type="date"
            value={gun}
            onChange={(e) => setGun(e.target.value)}
            helperText={PROGRAMA_BASLAMA_YARDIMI}
          />
          <TextField
            className="sm:col-span-2"
            label={ALAN_KANIT}
            value={kanit}
            maxLength={1000}
            onChange={(e) => setKanit(e.target.value)}
            helperText={KANIT_YARDIMI}
          />
        </div>
      </div>
    </Dialog>
  );
}

export function KomisyonUyesiPenceresi({ donem, onKapat, onEklendi }: Props) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const [kisi, setKisi] = useState<BirlikKisisi | null>(null);
  const [uzmanlik, setUzmanlik] = useState(false);
  const [gun, setGun] = useState("");
  const [kisiHatasi, setKisiHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const gonder = async () => {
    setHata(null);
    if (kisi === null) {
      setKisiHatasi(KISI_SECIN);
      return;
    }
    setBusy(true);
    try {
      await organlarApi.alimKomisyonuEkle({
        term: donem,
        person: kisi.id,
        expertise_required: uzmanlik,
        start_date: gun || null,
      });
      snackbar.success(UYE_EKLENDI);
      onEklendi();
    } catch (e) {
      setHata(hataOku(e, UYE_EKLENEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={KOMISYON_PENCERESI_BASLIGI}
      actions={
        <Eylemler busy={busy} gerekce={false} onVazgec={onKapat} onGonder={() => void gonder()} />
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <p className="text-body-medium text-on-surface-variant">{ALIM_ACIKLAMASI}</p>
        <KisiSecimi
          kisiler={kisiler}
          secili={kisi}
          onSecim={(k) => {
            setKisi(k);
            setKisiHatasi(undefined);
          }}
          hata={kisiHatasi}
        />
        <label className="flex items-start gap-3 text-body-medium text-on-surface">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 shrink-0 accent-primary"
            checked={uzmanlik}
            onChange={(e) => setUzmanlik(e.target.checked)}
          />
          <span className="min-w-0">
            <span className="block">{ALAN_UZMANLIK}</span>
            <span className="block text-body-small text-on-surface-variant">
              {UZMANLIK_YARDIMI}
            </span>
          </span>
        </label>
        <TextField
          label={ALAN_BASLANGIC_GUNU}
          type="date"
          value={gun}
          onChange={(e) => setGun(e.target.value)}
          helperText={PROGRAMA_BASLAMA_YARDIMI}
        />
      </div>
    </Dialog>
  );
}
