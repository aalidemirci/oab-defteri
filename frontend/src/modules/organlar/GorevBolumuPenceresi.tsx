// Görev bölümü pencereleri (tasarım §7.2; plan F1c 6. adım notları; ekranı 11. adımda).
//
// * Yönetim kurulu (yalnız sekreter, `gorev_bolumu_yazma`): verilen görevler dört görevin alt kümesidir
//   (dönem içi görev değişimi; verilen görevin önceki sahibi üye olur), en az biri; bir üyeye tek görev.
//   Görevdeki her asılın katılım satırı zorunludur (katıldı · özürlü · özürsüz; özrün nedeni tutulmaz).
// * Denetleme Kurulu (yalnız Denetleme Kurulu, `dk_gorev_bolumu_yazma`): başkan zorunlu, denetim planı
//   tarihleri isteğe bağlı (dönem ayarı; "yılda en az iki" kuralı sonraki fazdadır).
//
// Süre (md. 12/3, 14/1) ve başkanlık sayacı (md. 14/3) uyarı + gerekçedir (ortak bileşen); görev
// tekilliği ve tarih sırası serttir (bant). Toplantı zamanı yerel saattir (sunucu Europe/Istanbul okur).

import { useState } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { GOREV_TR } from "../gecis-kurulumu/metinler";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { organlarApi } from "./api";
import type { KatilimSatiri, Uyelik } from "./api";
import {
  ALAN_TOPLANTI_ZAMANI,
  ALAN_YER,
  ASIL_UYE_YOK_GOREV_BOLUMU,
  BASKAN_SECIN,
  DENETIM_PLANI_BASLIGI,
  DK_GOREV_BOLUMU_ACIKLAMASI,
  DK_GOREV_BOLUMU_BASLIGI,
  DUGME_INCELEME_GUNU_EKLE,
  DUGME_KALDIR,
  GOREV_BOLUMU_KAYDEDILDI,
  GOREV_BOLUMU_KAYDEDILEMEDI,
  GOREV_DEGISMESIN,
  GOREV_SECIN,
  KATILDI,
  KATILIM_BASLIGI,
  OZURLU,
  OZURSUZ,
  TEK_GOREV,
  TOPLANTI_ZAMANI_ZORUNLU,
  YK_GOREV_BOLUMU_ACIKLAMASI,
  YK_GOREV_BOLUMU_BASLIGI,
  incelemeGunuEtiketi,
  kaldirEtiketi,
} from "./metinler";
import { PencereHatasi } from "./ortak";

type Katilim = "KATILDI" | "OZURLU" | "OZURSUZ";

const KATILIM_SECENEKLERI = [
  { value: "KATILDI", label: KATILDI },
  { value: "OZURLU", label: OZURLU },
  { value: "OZURSUZ", label: OZURSUZ },
];

/** Yönetim kurulunun görev bölümünde verilebilen görevler ve gövde alanları. */
const YK_GOREVLERI = [
  ["BASKAN", "baskan"],
  ["BASKAN_YARDIMCISI", "baskan_yardimcisi"],
  ["MUHASIP", "muhasip"],
  ["SEKRETER", "sekreter"],
] as const;

type YkGorevi = (typeof YK_GOREVLERI)[number][0];

/** Katılım seçimleri → gövdenin satırları (görevdeki her asıl). */
export function katilimSatirlari(
  asillar: readonly Uyelik[],
  secim: Record<number, Katilim>,
): KatilimSatiri[] {
  return asillar.map((u) => {
    const deger = secim[u.id] ?? "KATILDI";
    return { membership: u.id, present: deger === "KATILDI", excused: deger === "OZURLU" };
  });
}

function KatilimTablosu({
  asillar,
  secim,
  onSecim,
}: {
  asillar: readonly Uyelik[];
  secim: Record<number, Katilim>;
  onSecim: (id: number, deger: Katilim) => void;
}) {
  return (
    <fieldset className="space-y-2">
      <legend className="mb-1 text-label-large text-on-surface">{KATILIM_BASLIGI}</legend>
      <ul className="divide-y divide-outline-variant">
        {asillar.map((u) => (
          <li key={u.id} className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1 py-2">
            <span className="min-w-0 flex-1 break-words text-body-medium text-on-surface">
              {u.person_name ?? "—"}
            </span>
            <Select
              className="w-40"
              label=""
              aria-label={`${u.person_name ?? ""} · ${KATILIM_BASLIGI}`}
              value={secim[u.id] ?? "KATILDI"}
              onChange={(e) => onSecim(u.id, e.target.value as Katilim)}
              options={KATILIM_SECENEKLERI}
            />
          </li>
        ))}
      </ul>
    </fieldset>
  );
}

function OrtakAlanlar({
  zaman,
  setZaman,
  yer,
  setYer,
  zamanHatasi,
}: {
  zaman: string;
  setZaman: (v: string) => void;
  yer: string;
  setYer: (v: string) => void;
  zamanHatasi?: string;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <TextField
        label={ALAN_TOPLANTI_ZAMANI}
        type="datetime-local"
        required
        value={zaman}
        onChange={(e) => setZaman(e.target.value)}
        error={zamanHatasi}
      />
      <TextField
        label={ALAN_YER}
        value={yer}
        maxLength={128}
        onChange={(e) => setYer(e.target.value)}
      />
    </div>
  );
}

interface Props {
  donem: number;
  /** Görevdeki asıllar (seçilmiş asıl ve yedekten çağrılan). */
  asillar: readonly Uyelik[];
  onKapat: () => void;
  onKaydedildi: () => void;
}

export function YkGorevBolumuPenceresi({ donem, asillar, onKapat, onKaydedildi }: Props) {
  const snackbar = useSnackbar();
  const [zaman, setZaman] = useState("");
  const [yer, setYer] = useState("");
  const [gorevler, setGorevler] = useState<Record<YkGorevi, string>>({
    BASKAN: "",
    BASKAN_YARDIMCISI: "",
    MUHASIP: "",
    SEKRETER: "",
  });
  const [katilim, setKatilim] = useState<Record<number, Katilim>>({});
  const [alanHatalari, setAlanHatalari] = useState<{ zaman?: string; gorev?: string }>({});
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const ug = useUyariGerekce("organlar.yk_gorev_bolumu");
  const secenekler = [
    { value: "", label: GOREV_DEGISMESIN },
    ...asillar.map((u) => ({ value: String(u.id), label: u.person_name ?? "—" })),
  ];

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    const verilen = Object.values(gorevler).filter(Boolean);
    const hatalar: { zaman?: string; gorev?: string } = {};
    if (!zaman) hatalar.zaman = TOPLANTI_ZAMANI_ZORUNLU;
    if (verilen.length === 0) hatalar.gorev = GOREV_SECIN;
    else if (new Set(verilen).size !== verilen.length) hatalar.gorev = TEK_GOREV;
    setAlanHatalari(hatalar);
    if (hatalar.zaman || hatalar.gorev || !ug.hazir()) return;
    setBusy(true);
    setHata(null);
    const atananlar = Object.fromEntries(
      YK_GOREVLERI.filter(([gorev]) => gorevler[gorev]).map(([gorev, alan]) => [
        alan,
        Number(gorevler[gorev]),
      ]),
    );
    try {
      await organlarApi.ykGorevBolumu(donem, {
        held_at: zaman,
        place: yer.trim(),
        katilim: katilimSatirlari(asillar, katilim),
        ...atananlar,
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(GOREV_BOLUMU_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, GOREV_BOLUMU_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={YK_GOREV_BOLUMU_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={vazgec} disabled={busy}>
            Vazgeç
          </Button>
          <Button
            icon="check"
            onClick={() => void gonder()}
            disabled={busy || asillar.length === 0}
          >
            {busy ? "Kaydediliyor…" : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : "Kaydet"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <p className="text-body-medium text-on-surface-variant">{YK_GOREV_BOLUMU_ACIKLAMASI}</p>
        {asillar.length === 0 ? (
          <p className="text-body-medium text-on-surface">{ASIL_UYE_YOK_GOREV_BOLUMU}</p>
        ) : (
          <>
            <OrtakAlanlar
              zaman={zaman}
              setZaman={setZaman}
              yer={yer}
              setYer={setYer}
              zamanHatasi={alanHatalari.zaman}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              {YK_GOREVLERI.map(([gorev]) => (
                <Select
                  key={gorev}
                  label={GOREV_TR[gorev]}
                  value={gorevler[gorev]}
                  onChange={(e) => setGorevler((g) => ({ ...g, [gorev]: e.target.value }))}
                  options={secenekler}
                />
              ))}
            </div>
            {alanHatalari.gorev && (
              <p role="alert" className="text-body-small text-error">
                {alanHatalari.gorev}
              </p>
            )}
            <KatilimTablosu
              asillar={asillar}
              secim={katilim}
              onSecim={(id, deger) => setKatilim((k) => ({ ...k, [id]: deger }))}
            />
          </>
        )}
      </div>
    </Dialog>
  );
}

export function DkGorevBolumuPenceresi({ donem, asillar, onKapat, onKaydedildi }: Props) {
  const snackbar = useSnackbar();
  const [zaman, setZaman] = useState("");
  const [yer, setYer] = useState("");
  const [baskan, setBaskan] = useState("");
  const [plan, setPlan] = useState<string[]>([]);
  const [katilim, setKatilim] = useState<Record<number, Katilim>>({});
  const [alanHatalari, setAlanHatalari] = useState<{ zaman?: string; baskan?: string }>({});
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const ug = useUyariGerekce("organlar.dk_gorev_bolumu");

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    const hatalar: { zaman?: string; baskan?: string } = {};
    if (!zaman) hatalar.zaman = TOPLANTI_ZAMANI_ZORUNLU;
    if (!baskan) hatalar.baskan = BASKAN_SECIN;
    setAlanHatalari(hatalar);
    if (hatalar.zaman || hatalar.baskan || !ug.hazir()) return;
    setBusy(true);
    setHata(null);
    const gunler = plan.filter(Boolean);
    try {
      await organlarApi.dkGorevBolumu(donem, {
        held_at: zaman,
        place: yer.trim(),
        baskan: Number(baskan),
        katilim: katilimSatirlari(asillar, katilim),
        denetim_plani: gunler.length > 0 ? gunler : null,
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(GOREV_BOLUMU_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, GOREV_BOLUMU_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={DK_GOREV_BOLUMU_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={vazgec} disabled={busy}>
            Vazgeç
          </Button>
          <Button
            icon="check"
            onClick={() => void gonder()}
            disabled={busy || asillar.length === 0}
          >
            {busy ? "Kaydediliyor…" : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : "Kaydet"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <p className="text-body-medium text-on-surface-variant">{DK_GOREV_BOLUMU_ACIKLAMASI}</p>
        {asillar.length === 0 ? (
          <p className="text-body-medium text-on-surface">{ASIL_UYE_YOK_GOREV_BOLUMU}</p>
        ) : (
          <>
            <OrtakAlanlar
              zaman={zaman}
              setZaman={setZaman}
              yer={yer}
              setYer={setYer}
              zamanHatasi={alanHatalari.zaman}
            />
            <Select
              label={GOREV_TR.BASKAN}
              required
              placeholder="Seçin"
              value={baskan}
              onChange={(e) => setBaskan(e.target.value)}
              options={asillar.map((u) => ({ value: String(u.id), label: u.person_name ?? "—" }))}
              error={alanHatalari.baskan}
            />
            <KatilimTablosu
              asillar={asillar}
              secim={katilim}
              onSecim={(id, deger) => setKatilim((k) => ({ ...k, [id]: deger }))}
            />
            <fieldset className="space-y-2">
              <legend className="mb-1 text-label-large text-on-surface">
                {DENETIM_PLANI_BASLIGI}
              </legend>
              {plan.map((gun, i) => (
                <div key={i} className="flex flex-wrap items-end gap-2">
                  <TextField
                    className="w-56"
                    label={incelemeGunuEtiketi(i + 1)}
                    type="date"
                    value={gun}
                    onChange={(e) =>
                      setPlan((p) => p.map((eski, j) => (j === i ? e.target.value : eski)))
                    }
                  />
                  <Button
                    variant="text"
                    icon="delete"
                    aria-label={kaldirEtiketi(i + 1)}
                    onClick={() => setPlan((p) => p.filter((_, j) => j !== i))}
                  >
                    {DUGME_KALDIR}
                  </Button>
                </div>
              ))}
              <Button variant="tonal" icon="add" onClick={() => setPlan((p) => [...p, ""])}>
                {DUGME_INCELEME_GUNU_EKLE}
              </Button>
            </fieldset>
          </>
        )}
      </div>
    </Dialog>
  );
}
