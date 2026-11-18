// Genel kurulun çağrı penceresi (`PLANLANDI → CAGRILDI`; tasarım §7.1, plan F2 §1.1-3, §7 U12, U13).
// Seçenekler sunucunundur (`oturum.cagiranlar`: oturumdaki rolün yazabildiği çağıranlar ve uçları); ön
// yüz rol adıyla dallanmaz. Üç uç vardır: yönetim kurulunun, başkanın md. 13/8 ve üyelerin başvurusunun
// çağrısı (`call`), okul müdürünün yazısı (`principal-call`; yeni açılan okulun daveti ya da olağanüstü
// çağrı, ¹) ve Denetleme Kurulunun md. 14/5 çağrısı (`audit-board-call`, ⁵; denetim raporu aynı istekte,
// Yönetmeliğin 6. maddesine aykırılık işareti zorunlu — S6 (ii), sert). Olağanüstü genel kurulda çağrı
// nedeni ve gündem girilir (md. 9/6); üyelerin başvurusunda başvuran ve üye sayısı (U12) ve başvuru
// yazısının gelen evrak kaydı. Organlar → Denetleme Kurulu sekmesi aynı pencereyi kullanır.

import { useEffect, useState } from "react";

import Select from "../../ui/Select";
import TextField from "../../ui/TextField";
import { gelenGidenApi } from "../gelen-giden-evrak/api";
import type { EvrakKaydi } from "../gelen-giden-evrak/api";
import { formatDate } from "../../lib/format";
import { genelKurulApi } from "./api";
import type {
  Cagiran,
  CagriGundemMaddesi,
  CagriYolu,
  GecisSonucu,
  GenelKurul,
  GerekceEki,
  GundemTuru,
} from "./api";
import {
  ALAN_BASVURAN_SAYISI,
  ALAN_BASVURU_YAZISI,
  ALAN_CAGIRAN,
  ALAN_CAGRI_GUNDEMI,
  ALAN_CAGRI_NEDENI,
  ALAN_GUNDEM_MADDESI,
  ALAN_MD6_AYKIRILIK,
  ALAN_RAPOR_GUNU,
  ALAN_RAPOR_TURU,
  ALAN_TUR,
  ALAN_USULSUZLUK,
  ALAN_UYE_SAYISI,
  BASVURU_YAZISI_YOK,
  CAGIRAN_TR,
  CAGRI_KAYDEDILDI,
  CAGRI_KAYDEDILEMEDI,
  CAGRI_NEDENI_GEREKLI,
  CAGRI_OLAGANUSTU_ACIKLAMASI,
  CAGRI_OLAGAN_ACIKLAMASI,
  CAGRI_PENCERESI_BASLIGI,
  DK_CAGRI_ACIKLAMASI,
  DK_CAGRI_BASLIGI,
  DUGME_CAGRI,
  DUGME_MADDEYI_KALDIR,
  DUGME_MADDE_EKLE,
  GUNDEM_GEREKLI,
  GUNDEM_TURU_TR,
  MD6_ISARETI_ZORUNLU,
  RAPOR_ARA,
  RAPOR_GUNU_GEREKLI,
  RAPOR_NIHAI,
  SAYI_GECERSIZ,
  SECIN,
  USULSUZLUK_YARDIMI,
  UYE_SAYISI_YARDIMI,
} from "./metinler";
import OnayKutusu from "./OnayKutusu";
import { SayiAlani, YazmaPenceresi, sayiOku } from "./ortak";
import Button from "../../ui/Button";
import { useSnackbar } from "../../ui/SnackbarProvider";

const GUNDEM_TURLERI = Object.keys(GUNDEM_TURU_TR) as GundemTuru[];

interface Satir {
  title: string;
  kind: GundemTuru;
}

export default function CagriPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
  yalnizYol,
}: {
  kurul: Pick<GenelKurul, "id" | "kind" | "term" | "oturum">;
  onKapat: () => void;
  onKaydedildi: (sonuc: GecisSonucu) => void;
  /** Yalnız bu yolun çağıranları (Organlar → Denetleme Kurulu: "dk"). */
  yalnizYol?: CagriYolu;
}) {
  const snackbar = useSnackbar();
  const secenekler = kurul.oturum.cagiranlar.filter(
    (c) => yalnizYol === undefined || c.yol === yalnizYol,
  );
  const [cagiran, setCagiran] = useState<Cagiran | "">(
    secenekler.length === 1 ? secenekler[0].called_by : "",
  );
  const [neden, setNeden] = useState("");
  const [gundem, setGundem] = useState<Satir[]>([{ title: "", kind: "DIGER" }]);
  const [basvuran, setBasvuran] = useState("");
  const [uyeSayisi, setUyeSayisi] = useState("");
  const [yazi, setYazi] = useState("");
  const [gelenler, setGelenler] = useState<EvrakKaydi[]>([]);
  const [raporTuru, setRaporTuru] = useState<"ARA" | "NIHAI">("ARA");
  const [raporGunu, setRaporGunu] = useState("");
  const [md6, setMd6] = useState(false);
  const [usulsuzluk, setUsulsuzluk] = useState(false);
  const [hatalar, setHatalar] = useState<Record<string, string>>({});

  const secenek = secenekler.find((c) => c.called_by === cagiran);
  const olaganustu = kurul.kind === "OLAGANUSTU";
  const dk = secenek?.yol === "dk";
  const basvuru = cagiran === "UYE_BASVURUSU";

  useEffect(() => {
    if (!basvuru) return;
    let iptal = false;
    gelenGidenApi
      .kayitlar({ direction: "GELEN" })
      .then((liste) => {
        if (!iptal) setGelenler(liste.filter((k) => k.term === kurul.term));
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, [basvuru, kurul.term]);

  const dogrula = (): boolean => {
    const yeni: Record<string, string> = {};
    if (!cagiran) yeni.cagiran = SECIN;
    if (olaganustu) {
      if (!neden.trim()) yeni.neden = CAGRI_NEDENI_GEREKLI;
      if (!gundem.some((s) => s.title.trim())) yeni.gundem = GUNDEM_GEREKLI;
    }
    if (basvuru) {
      if (sayiOku(basvuran) === "gecersiz") yeni.basvuran = SAYI_GECERSIZ;
      if (sayiOku(uyeSayisi) === "gecersiz") yeni.uyeSayisi = SAYI_GECERSIZ;
    }
    if (dk) {
      if (!raporGunu) yeni.raporGunu = RAPOR_GUNU_GEREKLI;
      if (!md6) yeni.md6 = MD6_ISARETI_ZORUNLU;
    }
    setHatalar(yeni);
    return Object.keys(yeni).length === 0;
  };

  const maddeler = (): CagriGundemMaddesi[] =>
    gundem.filter((s) => s.title.trim()).map((s) => ({ title: s.title.trim(), kind: s.kind }));

  const gonder = async (ek: GerekceEki) => {
    if (!secenek) return;
    const ortak = olaganustu ? { call_reason: neden.trim(), gundem: maddeler() } : {};
    let sonuc: GecisSonucu;
    if (secenek.yol === "dk") {
      sonuc = await genelKurulApi.dkCagrisi(kurul.id, {
        call_reason: neden.trim(),
        gundem: maddeler(),
        rapor: {
          kind: raporTuru,
          report_date: raporGunu,
          md6_violation_found: md6,
          irregularity_found: usulsuzluk,
        },
        ...ek,
      });
    } else if (secenek.yol === "mudur") {
      sonuc = await genelKurulApi.mudurCagrisi(kurul.id, {
        called_by: olaganustu ? secenek.called_by : "",
        ...ortak,
        ...ek,
      });
    } else {
      const sayilar = basvuru
        ? {
            member_application_count: sayiOku(basvuran) as number | null,
            member_count_declared: sayiOku(uyeSayisi) as number | null,
            call_document: yazi ? Number(yazi) : null,
          }
        : {};
      sonuc = await genelKurulApi.cagir(kurul.id, {
        called_by: olaganustu ? secenek.called_by : "",
        ...ortak,
        ...sayilar,
        ...ek,
      });
    }
    snackbar.success(CAGRI_KAYDEDILDI);
    onKaydedildi(sonuc);
  };

  return (
    <YazmaPenceresi
      baslik={yalnizYol === "dk" ? DK_CAGRI_BASLIGI : CAGRI_PENCERESI_BASLIGI}
      dugme={DUGME_CAGRI}
      yedekHata={CAGRI_KAYDEDILEMEDI}
      baglam={`genel_kurul.cagri.${kurul.id}`}
      onGonder={gonder}
      onKapat={onKapat}
      dogrula={dogrula}
      genis={olaganustu}
      ikon="campaign"
    >
      <p className="text-body-medium text-on-surface-variant">
        {dk
          ? DK_CAGRI_ACIKLAMASI
          : olaganustu
            ? CAGRI_OLAGANUSTU_ACIKLAMASI
            : CAGRI_OLAGAN_ACIKLAMASI}
      </p>
      {secenekler.length > 1 ? (
        <Select
          label={ALAN_CAGIRAN}
          value={cagiran}
          placeholder={SECIN}
          onChange={(e) => setCagiran(e.target.value as Cagiran)}
          options={secenekler.map((c) => ({ value: c.called_by, label: CAGIRAN_TR[c.called_by] }))}
          error={hatalar.cagiran}
        />
      ) : (
        secenek && (
          <p className="text-body-medium text-on-surface">
            {ALAN_CAGIRAN}: {CAGIRAN_TR[secenek.called_by]}
          </p>
        )
      )}

      {olaganustu && (
        <>
          <div>
            <label
              htmlFor="cagri-nedeni"
              className="mb-1.5 block text-label-medium font-semibold text-on-surface-variant"
            >
              {ALAN_CAGRI_NEDENI}
              <span className="text-error"> *</span>
            </label>
            <textarea
              id="cagri-nedeni"
              rows={3}
              maxLength={4000}
              value={neden}
              onChange={(e) => setNeden(e.target.value)}
              aria-invalid={hatalar.neden ? true : undefined}
              className="block w-full rounded-shape-xs border border-outline bg-surface px-3 py-2 text-body-medium text-on-surface outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
            />
            {hatalar.neden && (
              <p role="alert" className="mt-1 text-body-small text-error">
                {hatalar.neden}
              </p>
            )}
          </div>
          <fieldset className="space-y-3">
            <legend className="text-label-large text-on-surface">{ALAN_CAGRI_GUNDEMI}</legend>
            {gundem.map((satir, i) => (
              <div key={i} className="grid gap-2 sm:grid-cols-[1fr_14rem_auto] sm:items-start">
                <TextField
                  label={`${ALAN_GUNDEM_MADDESI} ${i + 1}`}
                  value={satir.title}
                  maxLength={200}
                  onChange={(e) =>
                    setGundem((g) =>
                      g.map((s, j) => (j === i ? { ...s, title: e.target.value } : s)),
                    )
                  }
                />
                <Select
                  label={ALAN_TUR}
                  value={satir.kind}
                  onChange={(e) =>
                    setGundem((g) =>
                      g.map((s, j) => (j === i ? { ...s, kind: e.target.value as GundemTuru } : s)),
                    )
                  }
                  options={GUNDEM_TURLERI.map((t) => ({ value: t, label: GUNDEM_TURU_TR[t] }))}
                />
                {gundem.length > 1 && (
                  <Button
                    variant="text"
                    icon="delete"
                    className="sm:mt-6"
                    aria-label={`${DUGME_MADDEYI_KALDIR} ${i + 1}`}
                    onClick={() => setGundem((g) => g.filter((_, j) => j !== i))}
                  >
                    {DUGME_MADDEYI_KALDIR}
                  </Button>
                )}
              </div>
            ))}
            {hatalar.gundem && (
              <p role="alert" className="text-body-small text-error">
                {hatalar.gundem}
              </p>
            )}
            <Button
              variant="tonal"
              icon="add"
              onClick={() => setGundem((g) => [...g, { title: "", kind: "DIGER" }])}
            >
              {DUGME_MADDE_EKLE}
            </Button>
          </fieldset>
        </>
      )}

      {basvuru && (
        <div className="grid gap-3 sm:grid-cols-2">
          <SayiAlani
            etiket={ALAN_BASVURAN_SAYISI}
            deger={basvuran}
            onDegis={setBasvuran}
            hata={hatalar.basvuran}
          />
          <SayiAlani
            etiket={ALAN_UYE_SAYISI}
            deger={uyeSayisi}
            onDegis={setUyeSayisi}
            yardim={UYE_SAYISI_YARDIMI}
            hata={hatalar.uyeSayisi}
          />
          <div className="sm:col-span-2">
            {gelenler.length === 0 ? (
              <p className="text-body-small text-on-surface-variant">{BASVURU_YAZISI_YOK}</p>
            ) : (
              <Select
                label={ALAN_BASVURU_YAZISI}
                value={yazi}
                placeholder={SECIN}
                onChange={(e) => setYazi(e.target.value)}
                options={gelenler.map((k) => ({
                  value: String(k.id),
                  label: `${k.year}/${k.record_no} · ${formatDate(k.date)}`,
                }))}
              />
            )}
          </div>
        </div>
      )}

      {dk && (
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Select
              label={ALAN_RAPOR_TURU}
              value={raporTuru}
              onChange={(e) => setRaporTuru(e.target.value as "ARA" | "NIHAI")}
              options={[
                { value: "ARA", label: RAPOR_ARA },
                { value: "NIHAI", label: RAPOR_NIHAI },
              ]}
            />
            <TextField
              label={ALAN_RAPOR_GUNU}
              type="date"
              required
              value={raporGunu}
              onChange={(e) => setRaporGunu(e.target.value)}
              error={hatalar.raporGunu}
            />
          </div>
          <OnayKutusu
            etiket={ALAN_MD6_AYKIRILIK}
            secili={md6}
            onDegis={setMd6}
            hata={hatalar.md6}
          />
          <OnayKutusu
            etiket={ALAN_USULSUZLUK}
            secili={usulsuzluk}
            onDegis={setUsulsuzluk}
            yardim={USULSUZLUK_YARDIMI}
          />
        </div>
      )}
    </YazmaPenceresi>
  );
}
