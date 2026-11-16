// Genel Kurul sihirbazının yazma pencereleri (plan F2 §6.1; uçları 11a). Her pencere ortak "uyarı +
// gerekçe" akışıyla yazar (`ortak.YazmaPenceresi`): sunucu gerekçe isterse kutu açılır, sert engel ve dönem
// kilidi bantla gösterilir. Hesabı program yapar: yeter sayının sağlanıp sağlanmadığı, kararın ve ibranın
// sonucu oylardan hesaplanır (S2, S6 (iii)); pencere yalnız sayıları ve seçimleri alır. Kayıt silinmez:
// yanlış divan ve yanlış seçim gerekçeyle iptal edilip yeniden girilir (altın kural 4).

import { useState } from "react";

import Button from "../../ui/Button";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { KisiSecimi, useEtkinKisiler } from "../organlar/ortak";
import { KATILIM_TURLERI, genelKurulApi } from "./api";
import type {
  GecisSonucu,
  GenelKurul,
  GerekceEki,
  GundemMaddesi,
  GundemTuru,
  IlanKanallari,
  Ilan,
  KatilimTuru,
  Toplanti,
  TutanakGovdesi,
} from "./api";
import {
  ADAY_ACIKLAMASI,
  ADAY_KAYDEDILDI,
  ADAY_KAYDEDILEMEDI,
  ADAY_PENCERESI_BASLIGI,
  ALAN_ACIK_OY,
  ALAN_BIRINCI_TOPLANTI,
  ALAN_BUTCEYI_SUNAN,
  ALAN_DEGISIKLIK_KABUL,
  ALAN_DEGISIKLIK_RET,
  ALAN_DIVAN_BASKANI,
  ALAN_DK_RAPORU_OKUYAN,
  ALAN_DUZELTILEN_SAYI,
  ALAN_DUZELTME_GEREKCESI,
  ALAN_ELDEN_YAZILI,
  ALAN_GENEL_KURUL_TURU,
  ALAN_GOZLEMCI,
  ALAN_IBRA_EDILMEYEN_EVRAK,
  ALAN_IKINCI_TOPLANTI,
  ALAN_ILAN_PANOSU,
  ALAN_INTERNET,
  ALAN_KABUL,
  ALAN_KATILAN,
  ALAN_KATIP,
  ALAN_KOLTUK,
  ALAN_KURUL,
  ALAN_LISTE,
  ALAN_MADDE_BASLIGI,
  ALAN_OY,
  ALAN_RET,
  ALAN_SALONDAKI,
  ALAN_SECILDI,
  ALAN_SIRA,
  ALAN_SONUC_METNI,
  ALAN_SONUC_TURU,
  ALAN_TESLIM_GUNU,
  ALAN_TOPLANTI,
  ALAN_TUR,
  ALAN_VELISI_KATILAN,
  ALAN_YEDEK_SIRASI,
  ALAN_YENI_DEGER,
  ALAN_YER,
  ALAN_YK_RAPORU_OKUYAN,
  BIRINCI_TOPLANTI_BASLIGI,
  BIRINCI_TOPLANTI_GEREKLI,
  DAGILIM_BASLIGI,
  DAGILIM_YARDIMI,
  DIVAN_ACIKLAMASI,
  DIVAN_KAYDEDILDI,
  DIVAN_KAYDEDILEMEDI,
  DIVAN_PENCERESI_BASLIGI,
  DUGME_ASAGI,
  DUGME_DIVAN,
  DUGME_GUNDEMDEN_CIKAR,
  DUGME_GUNDEM_EKLE,
  DUGME_IBRA,
  DUGME_ILAN,
  DUGME_IKINCI_ILAN,
  DUGME_KANIT,
  DUGME_KAYDET,
  DUGME_PLANLA_KAYDET,
  DUGME_SECIM,
  DUGME_SONUC,
  DUGME_ADAY,
  DUGME_YUKARI,
  DUZELTME_ALANI_TR,
  DUZELTME_GEREKCESI_YAZIN,
  DUZELTME_KAYDEDILDI,
  DUZELTME_KAYDEDILEMEDI,
  GUNDEMDEN_CIKARILAMADI,
  GUNDEMDEN_CIKARILDI_BILDIRIMI,
  GUNDEMDEN_CIKAR_ACIKLAMASI,
  GUNDEMDEN_CIKAR_BASLIGI,
  GUNDEM_EKLENDI,
  GUNDEM_EKLENEMEDI,
  GUNDEM_EKLE_ACIKLAMASI,
  GUNDEM_EKLE_BASLIGI,
  GUNDEM_SIRASI_ACIKLAMASI,
  GUNDEM_SIRASI_BASLIGI,
  GUNDEM_SIRASI_KAYDEDILDI,
  GUNDEM_SIRASI_KAYDEDILEMEDI,
  GUNDEM_TURU_TR,
  IBRA_ACIKLAMASI,
  IBRA_DK,
  IBRA_EDILMEYEN_EVRAK_YARDIMI,
  IBRA_KAYDEDILDI,
  IBRA_KAYDEDILEMEDI,
  IBRA_PENCERESI_BASLIGI,
  IBRA_YK,
  IKINCI_ILAN_ACIKLAMASI,
  IKINCI_ILAN_BASLIGI,
  IKINCI_TOPLANTI_BASLIGI,
  IKINCI_TOPLANTI_GEREKLI,
  IKINCI_TOPLANTI_YARDIMI,
  ILAN_ACIKLAMASI,
  ILAN_KAYDEDILDI,
  ILAN_KAYDEDILEMEDI,
  ILAN_PENCERESI_BASLIGI,
  KANAL_YARDIMI,
  KANIT_KAYDEDILDI,
  KANIT_KAYDEDILEMEDI,
  KANIT_PENCERESI_BASLIGI,
  KATILAN_GEREKLI,
  KATILIM_DUZELTMESI_ACIKLAMASI,
  KATILIM_DUZELTMESI_BASLIGI,
  KATILIM_TURU_TR,
  KISI_SECIN,
  KOLTUK_ASIL,
  KOLTUK_YEDEK,
  MADDE_BASLIGI_GEREKLI,
  OYLAR_BIRLIKTE,
  PLANLANAMADI,
  PLANLANDI,
  PLANLA_ACIKLAMASI,
  PLANLA_BASLIGI,
  SALONDAKI_YARDIMI,
  SAYI_GECERSIZ,
  SECIM_ACIKLAMASI,
  SECIM_ADAYI_YOK,
  SECIM_KAYDEDILDI,
  SECIM_KAYDEDILEMEDI,
  SECIM_PENCERESI_BASLIGI,
  SECIN,
  SONUC_ACIKLAMASI,
  SONUC_KAYDEDILDI,
  SONUC_KAYDEDILEMEDI,
  SONUC_OYLANDI,
  SONUC_PENCERESI_BASLIGI,
  SONUC_TR,
  TESLIM_GUNU_YARDIMI,
  TOPLANTI_ACIKLAMASI,
  TOPLANTI_BILGISI_ACIKLAMASI,
  TOPLANTI_BILGISI_BASLIGI,
  TOPLANTI_BILGISI_KAYDEDILDI,
  TOPLANTI_BILGISI_KAYDEDILEMEDI,
  TOPLANTI_KAYDEDILDI,
  TOPLANTI_KAYDEDILEMEDI,
  TOPLANTI_TR,
  TUR_TR,
  TUTANAK_BILGILERI_BASLIGI,
  TUTANAK_BILGILERI_KAYDEDILDI,
  TUTANAK_BILGILERI_KAYDEDILEMEDI,
  YENI_DEGER_GEREKLI,
} from "./metinler";
import OnayKutusu from "./OnayKutusu";
import { SayiAlani, YazmaPenceresi, alanAni, sayiOku, yerelAn } from "./ortak";

/** Pencerelerin ortak özellikleri: başarılı yazmanın sonucu (yoksa ayrıntı yeniden okunur). */
export interface PencereOzellikleri {
  onKapat: () => void;
  onKaydedildi: (sonuc: GecisSonucu | null) => void;
}

type Hatalar = Record<string, string>;

function useHatalar(): [Hatalar, (h: Hatalar) => boolean] {
  const [hatalar, setHatalar] = useState<Hatalar>({});
  const kur = (h: Hatalar) => {
    setHatalar(h);
    return Object.keys(h).length === 0;
  };
  return [hatalar, kur];
}

/** Sayı alanlarını okur: geçersizse hatayı yazar. */
function sayilariDenetle(alanlar: Record<string, string>, hatalar: Hatalar): void {
  for (const [ad, deger] of Object.entries(alanlar)) {
    if (sayiOku(deger) === "gecersiz") hatalar[ad] = SAYI_GECERSIZ;
  }
}

function sayi(deger: string): number | null {
  const okunan = sayiOku(deger);
  return okunan === "gecersiz" ? null : okunan;
}

function MetinAlani({
  id,
  etiket,
  deger,
  onDegis,
  yardim,
  hata,
  zorunlu = false,
}: {
  id: string;
  etiket: string;
  deger: string;
  onDegis: (metin: string) => void;
  yardim?: string;
  hata?: string;
  zorunlu?: boolean;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-label-medium font-semibold text-on-surface-variant"
      >
        {etiket}
        {zorunlu && <span className="text-error"> *</span>}
      </label>
      <textarea
        id={id}
        rows={3}
        maxLength={4000}
        value={deger}
        onChange={(e) => onDegis(e.target.value)}
        aria-invalid={hata ? true : undefined}
        className="block w-full rounded-shape-xs border border-outline bg-surface px-3 py-2 text-body-medium text-on-surface outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
      />
      {hata && (
        <p role="alert" className="mt-1 text-body-small text-error">
          {hata}
        </p>
      )}
      {yardim && <p className="mt-1 text-body-small text-on-surface-variant">{yardim}</p>}
    </div>
  );
}

export { MetinAlani };

// ---------------------------------------------------------------------------
// Planla ve toplantı bilgisi
// ---------------------------------------------------------------------------
export function PlanlaPenceresi({ onKapat, onKaydedildi }: PencereOzellikleri) {
  const snackbar = useSnackbar();
  const [tur, setTur] = useState<"OLAGAN" | "OLAGANUSTU">("OLAGAN");
  const [an, setAn] = useState("");
  const [yer, setYer] = useState("");
  const [hatalar, kur] = useHatalar();
  return (
    <YazmaPenceresi
      baslik={PLANLA_BASLIGI}
      dugme={DUGME_PLANLA_KAYDET}
      yedekHata={PLANLANAMADI}
      baglam="genel_kurul.planla"
      onKapat={onKapat}
      dogrula={() => kur(an ? {} : { an: BIRINCI_TOPLANTI_GEREKLI })}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.planla({
          kind: tur,
          first_meeting_at: yerelAn(an),
          venue: yer.trim(),
          ...ek,
        });
        snackbar.success(PLANLANDI);
        onKaydedildi(sonuc);
      }}
      ikon="event"
    >
      <p className="text-body-medium text-on-surface-variant">{PLANLA_ACIKLAMASI}</p>
      <Select
        label={ALAN_GENEL_KURUL_TURU}
        value={tur}
        onChange={(e) => setTur(e.target.value as "OLAGAN" | "OLAGANUSTU")}
        options={[
          { value: "OLAGAN", label: TUR_TR.OLAGAN },
          { value: "OLAGANUSTU", label: TUR_TR.OLAGANUSTU },
        ]}
      />
      <TextField
        label={ALAN_BIRINCI_TOPLANTI}
        type="datetime-local"
        required
        value={an}
        onChange={(e) => setAn(e.target.value)}
        error={hatalar.an}
      />
      <TextField
        label={ALAN_YER}
        value={yer}
        maxLength={200}
        onChange={(e) => setYer(e.target.value)}
      />
    </YazmaPenceresi>
  );
}

export function ToplantiBilgisiPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const [an, setAn] = useState(alanAni(kurul.first_meeting_at));
  const [yer, setYer] = useState(kurul.venue);
  const [hatalar, kur] = useHatalar();
  return (
    <YazmaPenceresi
      baslik={TOPLANTI_BILGISI_BASLIGI}
      dugme={DUGME_KAYDET}
      yedekHata={TOPLANTI_BILGISI_KAYDEDILEMEDI}
      baglam={`genel_kurul.toplanti_bilgisi.${kurul.id}`}
      onKapat={onKapat}
      dogrula={() => kur(an ? {} : { an: BIRINCI_TOPLANTI_GEREKLI })}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.toplantiBilgisi(kurul.id, {
          first_meeting_at: yerelAn(an),
          venue: yer.trim(),
          ...ek,
        });
        snackbar.success(TOPLANTI_BILGISI_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
    >
      <p className="text-body-medium text-on-surface-variant">{TOPLANTI_BILGISI_ACIKLAMASI}</p>
      <TextField
        label={ALAN_BIRINCI_TOPLANTI}
        type="datetime-local"
        required
        value={an}
        onChange={(e) => setAn(e.target.value)}
        error={hatalar.an}
      />
      <TextField
        label={ALAN_YER}
        value={yer}
        maxLength={200}
        onChange={(e) => setYer(e.target.value)}
      />
    </YazmaPenceresi>
  );
}

export function GundemSirasiPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const [sira, setSira] = useState<GundemMaddesi[]>(kurul.gundem);
  const tasi = (i: number, yon: -1 | 1) =>
    setSira((s) => {
      const yeni = [...s];
      const j = i + yon;
      [yeni[i], yeni[j]] = [yeni[j], yeni[i]];
      return yeni;
    });
  return (
    <YazmaPenceresi
      baslik={GUNDEM_SIRASI_BASLIGI}
      dugme={DUGME_KAYDET}
      yedekHata={GUNDEM_SIRASI_KAYDEDILEMEDI}
      baglam={`genel_kurul.gundem_sirasi.${kurul.id}`}
      onKapat={onKapat}
      onGonder={async () => {
        const sonuc = await genelKurulApi.gundemSirasi(
          kurul.id,
          sira.map((m) => m.id),
        );
        snackbar.success(GUNDEM_SIRASI_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
    >
      <p className="text-body-medium text-on-surface-variant">{GUNDEM_SIRASI_ACIKLAMASI}</p>
      <ol className="divide-y divide-outline-variant">
        {sira.map((m, i) => (
          <li key={m.id} className="flex flex-wrap items-center gap-2 py-2">
            <span className="min-w-0 flex-1 break-words text-body-medium text-on-surface">
              {i + 1}. {m.title}
            </span>
            <Button
              variant="text"
              icon="arrow_upward"
              disabled={i === 0}
              aria-label={`${m.title}: ${DUGME_YUKARI}`}
              onClick={() => tasi(i, -1)}
            >
              {DUGME_YUKARI}
            </Button>
            <Button
              variant="text"
              icon="arrow_downward"
              disabled={i === sira.length - 1}
              aria-label={`${m.title}: ${DUGME_ASAGI}`}
              onClick={() => tasi(i, 1)}
            >
              {DUGME_ASAGI}
            </Button>
          </li>
        ))}
      </ol>
    </YazmaPenceresi>
  );
}

// ---------------------------------------------------------------------------
// İlan, ikinci toplantının ilanı, kanıt günleri
// ---------------------------------------------------------------------------
function KanalAlanlari({
  kanallar,
  setKanallar,
}: {
  kanallar: IlanKanallari;
  setKanallar: (k: IlanKanallari) => void;
}) {
  const alan = (ad: keyof IlanKanallari, etiket: string) => (
    <TextField
      label={etiket}
      type="date"
      value={kanallar[ad] ?? ""}
      onChange={(e) => setKanallar({ ...kanallar, [ad]: e.target.value || null })}
      helperText={KANAL_YARDIMI}
    />
  );
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {alan("distributed_written_on", ALAN_ELDEN_YAZILI)}
      {alan("posted_board_on", ALAN_ILAN_PANOSU)}
      {alan("published_web_on", ALAN_INTERNET)}
    </div>
  );
}

function kanallarDolu(k: IlanKanallari): IlanKanallari | null {
  return k.distributed_written_on || k.posted_board_on || k.published_web_on ? k : null;
}

export function IlanPenceresi({
  kurul,
  mod,
  ilan,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul; mod: "ilan" | "ikinci" | "kanit"; ilan?: Ilan }) {
  const snackbar = useSnackbar();
  const [kanallar, setKanallar] = useState<IlanKanallari>({
    distributed_written_on: ilan?.distributed_written_on ?? null,
    posted_board_on: ilan?.posted_board_on ?? null,
    published_web_on: ilan?.published_web_on ?? null,
  });
  const [ikinci, setIkinci] = useState(alanAni(kurul.second_meeting_at));
  const [hatalar, kur] = useHatalar();
  const baslik =
    mod === "ilan"
      ? ILAN_PENCERESI_BASLIGI
      : mod === "ikinci"
        ? IKINCI_ILAN_BASLIGI
        : KANIT_PENCERESI_BASLIGI;
  return (
    <YazmaPenceresi
      baslik={baslik}
      dugme={mod === "ilan" ? DUGME_ILAN : mod === "ikinci" ? DUGME_IKINCI_ILAN : DUGME_KANIT}
      yedekHata={mod === "kanit" ? KANIT_KAYDEDILEMEDI : ILAN_KAYDEDILEMEDI}
      baglam={`genel_kurul.${mod}.${kurul.id}`}
      onKapat={onKapat}
      dogrula={() => kur(mod === "ikinci" && !ikinci ? { ikinci: IKINCI_TOPLANTI_GEREKLI } : {})}
      onGonder={async (ek) => {
        let sonuc: GecisSonucu;
        if (mod === "ilan") {
          sonuc = await genelKurulApi.ilan(kurul.id, {
            kanallar: kanallarDolu(kanallar),
            second_meeting_at: ikinci ? yerelAn(ikinci) : null,
            ...ek,
          });
        } else if (mod === "ikinci") {
          sonuc = await genelKurulApi.ikinciIlan(kurul.id, {
            second_meeting_at: yerelAn(ikinci),
            kanallar: kanallarDolu(kanallar),
            ...ek,
          });
        } else {
          sonuc = await genelKurulApi.kanit(ilan?.id ?? 0, { ...kanallar, ...ek });
        }
        snackbar.success(mod === "kanit" ? KANIT_KAYDEDILDI : ILAN_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
      ikon="campaign"
    >
      <p className="text-body-medium text-on-surface-variant">
        {mod === "ikinci" ? IKINCI_ILAN_ACIKLAMASI : ILAN_ACIKLAMASI}
      </p>
      <KanalAlanlari kanallar={kanallar} setKanallar={setKanallar} />
      {mod !== "kanit" && (
        <TextField
          label={ALAN_IKINCI_TOPLANTI}
          type="datetime-local"
          required={mod === "ikinci"}
          value={ikinci}
          onChange={(e) => setIkinci(e.target.value)}
          helperText={mod === "ilan" ? IKINCI_TOPLANTI_YARDIMI : undefined}
          error={hatalar.ikinci}
        />
      )}
    </YazmaPenceresi>
  );
}

// ---------------------------------------------------------------------------
// Toplantının sayıları ve katılım düzeltmesi
// ---------------------------------------------------------------------------
export function ToplantiPenceresi({
  kurul,
  toplanti,
  onerilen,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul; toplanti: Toplanti; onerilen?: string }) {
  const snackbar = useSnackbar();
  const [katilan, setKatilan] = useState("");
  const [velisi, setVelisi] = useState("");
  const [gozlemci, setGozlemci] = useState("");
  const [dagilim, setDagilim] = useState<Record<KatilimTuru, string>>({
    VELI_KURSIYER: "",
    OGRETMEN: "",
    IDARECI: "",
    HAYIRSEVER: "",
    DIGER: "",
  });
  const [hatalar, kur] = useHatalar();
  const dogrula = () => {
    const h: Hatalar = {};
    if (katilan.trim() === "") h.katilan = KATILAN_GEREKLI;
    sayilariDenetle({ katilan, velisi, gozlemci, ...dagilim }, h);
    return kur(h);
  };
  return (
    <YazmaPenceresi
      baslik={toplanti === "BIRINCI" ? BIRINCI_TOPLANTI_BASLIGI : IKINCI_TOPLANTI_BASLIGI}
      dugme={DUGME_KAYDET}
      yedekHata={TOPLANTI_KAYDEDILEMEDI}
      baglam={`genel_kurul.toplanti.${kurul.id}.${toplanti}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async (ek) => {
        const dagilimSayilari: Partial<Record<KatilimTuru, number>> = {};
        for (const tur of KATILIM_TURLERI) {
          const s = sayi(dagilim[tur]);
          if (s !== null) dagilimSayilari[tur] = s;
        }
        const govde = {
          attendee_count: sayi(katilan) ?? 0,
          attendance_by_kind: dagilimSayilari,
          parent_students_count: sayi(velisi),
          observer_count: sayi(gozlemci),
          ...ek,
        };
        const sonuc =
          toplanti === "BIRINCI"
            ? await genelKurulApi.birinciToplanti(kurul.id, govde)
            : await genelKurulApi.ikinciToplanti(kurul.id, govde);
        snackbar.success(TOPLANTI_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
      ikon="groups"
    >
      <p className="text-body-medium text-on-surface-variant">{TOPLANTI_ACIKLAMASI}</p>
      {onerilen && <p className="text-body-small text-on-surface-variant">{onerilen}</p>}
      <div className="grid gap-3 sm:grid-cols-3">
        <SayiAlani
          etiket={ALAN_KATILAN}
          deger={katilan}
          onDegis={setKatilan}
          zorunlu
          hata={hatalar.katilan}
        />
        <SayiAlani
          etiket={ALAN_VELISI_KATILAN}
          deger={velisi}
          onDegis={setVelisi}
          hata={hatalar.velisi}
        />
        <SayiAlani
          etiket={ALAN_GOZLEMCI}
          deger={gozlemci}
          onDegis={setGozlemci}
          hata={hatalar.gozlemci}
        />
      </div>
      <fieldset className="space-y-2">
        <legend className="text-label-large text-on-surface">{DAGILIM_BASLIGI}</legend>
        <p className="text-body-small text-on-surface-variant">{DAGILIM_YARDIMI}</p>
        <div className="grid gap-3 sm:grid-cols-3">
          {KATILIM_TURLERI.map((tur) => (
            <SayiAlani
              key={tur}
              etiket={KATILIM_TURU_TR[tur]}
              deger={dagilim[tur]}
              onDegis={(m) => setDagilim((d) => ({ ...d, [tur]: m }))}
              hata={hatalar[tur]}
            />
          ))}
        </div>
      </fieldset>
    </YazmaPenceresi>
  );
}

/** Seçilen toplantının düzeltilebilen sayıları (sunucunun kapalı listesi; toplantıya göre). */
export function duzeltilebilenAlanlar(toplanti: Toplanti): string[] {
  return Object.keys(DUZELTME_ALANI_TR).filter((alan) =>
    toplanti === "BIRINCI" ? alan !== "second_attendee_count" : alan !== "first_attendee_count",
  );
}

export function KatilimDuzeltmePenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const [toplanti, setToplanti] = useState<Toplanti>(
    kurul.held_at_meeting === "IKINCI" ? "IKINCI" : "BIRINCI",
  );
  const [alan, setAlan] = useState("");
  const [deger, setDeger] = useState("");
  const [gerekce, setGerekce] = useState("");
  const [hatalar, kur] = useHatalar();
  const dogrula = () => {
    const h: Hatalar = {};
    if (!alan) h.alan = SECIN;
    const okunan = sayiOku(deger);
    if (okunan === null) h.deger = YENI_DEGER_GEREKLI;
    else if (okunan === "gecersiz") h.deger = SAYI_GECERSIZ;
    if (!gerekce.trim()) h.gerekce = DUZELTME_GEREKCESI_YAZIN;
    return kur(h);
  };
  return (
    <YazmaPenceresi
      baslik={KATILIM_DUZELTMESI_BASLIGI}
      dugme={DUGME_KAYDET}
      yedekHata={DUZELTME_KAYDEDILEMEDI}
      baglam={`genel_kurul.katilim_duzeltmesi.${kurul.id}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.katilimDuzelt(kurul.id, {
          toplanti,
          degerler: { [alan]: sayi(deger) ?? 0 },
          justification: gerekce.trim(),
          ...ek,
        });
        snackbar.success(DUZELTME_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
    >
      <p className="text-body-medium text-on-surface-variant">{KATILIM_DUZELTMESI_ACIKLAMASI}</p>
      <Select
        label={ALAN_TOPLANTI}
        value={toplanti}
        onChange={(e) => {
          setToplanti(e.target.value as Toplanti);
          setAlan("");
        }}
        options={(["BIRINCI", "IKINCI"] as const).map((t) => ({
          value: t,
          label: TOPLANTI_TR[t],
        }))}
      />
      <Select
        label={ALAN_DUZELTILEN_SAYI}
        value={alan}
        placeholder={SECIN}
        onChange={(e) => setAlan(e.target.value)}
        options={duzeltilebilenAlanlar(toplanti).map((a) => ({
          value: a,
          label: DUZELTME_ALANI_TR[a],
        }))}
        error={hatalar.alan}
      />
      <SayiAlani
        etiket={ALAN_YENI_DEGER}
        deger={deger}
        onDegis={setDeger}
        zorunlu
        hata={hatalar.deger}
      />
      <MetinAlani
        id="duzeltme-gerekcesi"
        etiket={ALAN_DUZELTME_GEREKCESI}
        deger={gerekce}
        onDegis={setGerekce}
        zorunlu
        hata={hatalar.gerekce}
      />
    </YazmaPenceresi>
  );
}

// ---------------------------------------------------------------------------
// Divan, gündem sonucu, gündem değişikliği
// ---------------------------------------------------------------------------
export function DivanPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const [baskan, setBaskan] = useState<BirlikKisisi | null>(null);
  const [katip, setKatip] = useState<BirlikKisisi | null>(null);
  const [hatalar, kur] = useHatalar();
  return (
    <YazmaPenceresi
      baslik={DIVAN_PENCERESI_BASLIGI}
      dugme={DUGME_DIVAN}
      yedekHata={DIVAN_KAYDEDILEMEDI}
      baglam={`genel_kurul.divan.${kurul.id}`}
      onKapat={onKapat}
      dogrula={() =>
        kur({
          ...(baskan === null ? { baskan: KISI_SECIN } : {}),
          ...(katip === null ? { katip: KISI_SECIN } : {}),
        })
      }
      onGonder={async (ek) => {
        if (baskan === null || katip === null) return;
        const sonuc = await genelKurulApi.divan(kurul.id, {
          baskan: baskan.id,
          katip: katip.id,
          ...ek,
        });
        snackbar.success(DIVAN_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      ikon="gavel"
    >
      <p className="text-body-medium text-on-surface-variant">{DIVAN_ACIKLAMASI}</p>
      <div className="space-y-1">
        <p className="text-label-large text-on-surface">{ALAN_DIVAN_BASKANI}</p>
        <KisiSecimi kisiler={kisiler} secili={baskan} onSecim={setBaskan} hata={hatalar.baskan} />
      </div>
      <div className="space-y-1">
        <p className="text-label-large text-on-surface">{ALAN_KATIP}</p>
        <KisiSecimi kisiler={kisiler} secili={katip} onSecim={setKatip} hata={hatalar.katip} />
      </div>
    </YazmaPenceresi>
  );
}

export function SonucPenceresi({
  madde,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { madde: GundemMaddesi }) {
  const snackbar = useSnackbar();
  const [tur, setTur] = useState<"OYLANDI" | "GORUSULDU">(
    madde.result === "GORUSULDU" ? "GORUSULDU" : "OYLANDI",
  );
  const [kabul, setKabul] = useState(madde.votes_for?.toString() ?? "");
  const [ret, setRet] = useState(madde.votes_against?.toString() ?? "");
  const [salonda, setSalonda] = useState(madde.present_count?.toString() ?? "");
  const [metin, setMetin] = useState(madde.result_text ?? "");
  const [hatalar, kur] = useHatalar();
  const dogrula = () => {
    const h: Hatalar = {};
    if (tur === "OYLANDI") {
      sayilariDenetle({ kabul, ret, salonda }, h);
      if (!h.kabul && !h.ret && (kabul.trim() === "" || ret.trim() === ""))
        h.kabul = OYLAR_BIRLIKTE;
    }
    return kur(h);
  };
  return (
    <YazmaPenceresi
      baslik={SONUC_PENCERESI_BASLIGI}
      dugme={DUGME_SONUC}
      yedekHata={SONUC_KAYDEDILEMEDI}
      baglam={`genel_kurul.sonuc.${madde.id}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async () => {
        const sonuc = await genelKurulApi.kararSonucu(
          madde.id,
          tur === "GORUSULDU"
            ? { result: "GORUSULDU", result_text: metin.trim() }
            : {
                votes_for: sayi(kabul),
                votes_against: sayi(ret),
                present_count: sayi(salonda),
                result_text: metin.trim(),
              },
        );
        snackbar.success(SONUC_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
    >
      <p className="break-words text-body-large text-on-surface">{madde.title}</p>
      <p className="text-body-medium text-on-surface-variant">{SONUC_ACIKLAMASI}</p>
      <Select
        label={ALAN_SONUC_TURU}
        value={tur}
        onChange={(e) => setTur(e.target.value as "OYLANDI" | "GORUSULDU")}
        options={[
          { value: "OYLANDI", label: SONUC_OYLANDI },
          { value: "GORUSULDU", label: SONUC_TR.GORUSULDU },
        ]}
      />
      {tur === "OYLANDI" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <SayiAlani etiket={ALAN_KABUL} deger={kabul} onDegis={setKabul} hata={hatalar.kabul} />
          <SayiAlani etiket={ALAN_RET} deger={ret} onDegis={setRet} hata={hatalar.ret} />
          <SayiAlani
            etiket={ALAN_SALONDAKI}
            deger={salonda}
            onDegis={setSalonda}
            yardim={SALONDAKI_YARDIMI}
            hata={hatalar.salonda}
          />
        </div>
      )}
      <MetinAlani id="sonuc-metni" etiket={ALAN_SONUC_METNI} deger={metin} onDegis={setMetin} />
    </YazmaPenceresi>
  );
}

const EKLENEBILIR_TURLER: GundemTuru[] = ["DIGER", "ONERILER", "DILEK", "YETKILENDIRME"];

export function GundemEklePenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const [baslik, setBaslik] = useState("");
  const [tur, setTur] = useState<GundemTuru>("DIGER");
  const [sira, setSira] = useState("");
  const [kabul, setKabul] = useState("");
  const [ret, setRet] = useState("");
  const [hatalar, kur] = useHatalar();
  const dogrula = () => {
    const h: Hatalar = {};
    if (!baslik.trim()) h.baslik = MADDE_BASLIGI_GEREKLI;
    sayilariDenetle({ sira, kabul, ret }, h);
    return kur(h);
  };
  return (
    <YazmaPenceresi
      baslik={GUNDEM_EKLE_BASLIGI}
      dugme={DUGME_GUNDEM_EKLE}
      yedekHata={GUNDEM_EKLENEMEDI}
      baglam={`genel_kurul.gundem_ekle.${kurul.id}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.gundemeEkle(kurul.id, {
          title: baslik.trim(),
          kind: tur,
          sira: sayi(sira) || null,
          change_votes_for: sayi(kabul),
          change_votes_against: sayi(ret),
          ...ek,
        });
        snackbar.success(GUNDEM_EKLENDI);
        onKaydedildi(sonuc);
      }}
      ikon="playlist_add"
    >
      <p className="text-body-medium text-on-surface-variant">{GUNDEM_EKLE_ACIKLAMASI}</p>
      <TextField
        label={ALAN_MADDE_BASLIGI}
        required
        maxLength={200}
        value={baslik}
        onChange={(e) => setBaslik(e.target.value)}
        error={hatalar.baslik}
      />
      <div className="grid gap-3 sm:grid-cols-2">
        <Select
          label={ALAN_TUR}
          value={tur}
          onChange={(e) => setTur(e.target.value as GundemTuru)}
          options={EKLENEBILIR_TURLER.map((t) => ({ value: t, label: GUNDEM_TURU_TR[t] }))}
        />
        <SayiAlani etiket={ALAN_SIRA} deger={sira} onDegis={setSira} hata={hatalar.sira} />
        <SayiAlani
          etiket={ALAN_DEGISIKLIK_KABUL}
          deger={kabul}
          onDegis={setKabul}
          hata={hatalar.kabul}
        />
        <SayiAlani etiket={ALAN_DEGISIKLIK_RET} deger={ret} onDegis={setRet} hata={hatalar.ret} />
      </div>
    </YazmaPenceresi>
  );
}

export function GundemdenCikarPenceresi({
  madde,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { madde: GundemMaddesi }) {
  const snackbar = useSnackbar();
  const [kabul, setKabul] = useState("");
  const [ret, setRet] = useState("");
  const [hatalar, kur] = useHatalar();
  return (
    <YazmaPenceresi
      baslik={GUNDEMDEN_CIKAR_BASLIGI}
      dugme={DUGME_GUNDEMDEN_CIKAR}
      yedekHata={GUNDEMDEN_CIKARILAMADI}
      baglam={`genel_kurul.gundemden_cikar.${madde.id}`}
      onKapat={onKapat}
      dogrula={() => {
        const h: Hatalar = {};
        sayilariDenetle({ kabul, ret }, h);
        return kur(h);
      }}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.gundemdenCikar(madde.id, {
          change_votes_for: sayi(kabul),
          change_votes_against: sayi(ret),
          ...ek,
        });
        snackbar.success(GUNDEMDEN_CIKARILDI_BILDIRIMI);
        onKaydedildi(sonuc);
      }}
      ikon="playlist_remove"
    >
      <p className="break-words text-body-large text-on-surface">{madde.title}</p>
      <p className="text-body-medium text-on-surface-variant">{GUNDEMDEN_CIKAR_ACIKLAMASI}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <SayiAlani
          etiket={ALAN_DEGISIKLIK_KABUL}
          deger={kabul}
          onDegis={setKabul}
          hata={hatalar.kabul}
        />
        <SayiAlani etiket={ALAN_DEGISIKLIK_RET} deger={ret} onDegis={setRet} hata={hatalar.ret} />
      </div>
    </YazmaPenceresi>
  );
}

// ---------------------------------------------------------------------------
// İbra, aday, seçim, tutanağın bilgileri
// ---------------------------------------------------------------------------
export function IbraPenceresi({
  kurul,
  madde,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul; madde: GundemMaddesi }) {
  const snackbar = useSnackbar();
  const ilk = (d: number | null) => (d === null ? "" : String(d));
  const [yk, setYk] = useState({
    kabul: ilk(kurul.discharge_yk_votes_for),
    ret: ilk(kurul.discharge_yk_votes_against),
    salonda: ilk(kurul.discharge_yk_present_count),
  });
  const [dk, setDk] = useState({
    kabul: ilk(kurul.discharge_dk_votes_for),
    ret: ilk(kurul.discharge_dk_votes_against),
    salonda: ilk(kurul.discharge_dk_present_count),
  });
  const [not, setNot] = useState(kurul.tutanak?.unaudited_documents_note ?? "");
  const [hatalar, kur] = useHatalar();
  const oylama = (o: { kabul: string; ret: string; salonda: string }) =>
    o.kabul.trim() === "" && o.ret.trim() === ""
      ? null
      : {
          votes_for: sayi(o.kabul) ?? 0,
          votes_against: sayi(o.ret) ?? 0,
          present_count: sayi(o.salonda),
        };
  const dogrula = () => {
    const h: Hatalar = {};
    for (const [onek, o] of [
      ["yk", yk],
      ["dk", dk],
    ] as const) {
      const alt: Hatalar = {};
      sayilariDenetle({ kabul: o.kabul, ret: o.ret, salonda: o.salonda }, alt);
      for (const [a, v] of Object.entries(alt)) h[`${onek}.${a}`] = v;
      if ((o.kabul.trim() === "") !== (o.ret.trim() === "")) h[`${onek}.kabul`] = OYLAR_BIRLIKTE;
    }
    return kur(h);
  };
  const kurulAlanlari = (
    etiket: string,
    onek: "yk" | "dk",
    o: { kabul: string; ret: string; salonda: string },
    set: (o: { kabul: string; ret: string; salonda: string }) => void,
  ) => (
    <fieldset className="space-y-2">
      <legend className="text-label-large text-on-surface">{etiket}</legend>
      <div className="grid gap-3 sm:grid-cols-3">
        <SayiAlani
          etiket={ALAN_KABUL}
          deger={o.kabul}
          onDegis={(m) => set({ ...o, kabul: m })}
          hata={hatalar[`${onek}.kabul`]}
        />
        <SayiAlani
          etiket={ALAN_RET}
          deger={o.ret}
          onDegis={(m) => set({ ...o, ret: m })}
          hata={hatalar[`${onek}.ret`]}
        />
        <SayiAlani
          etiket={ALAN_SALONDAKI}
          deger={o.salonda}
          onDegis={(m) => set({ ...o, salonda: m })}
          hata={hatalar[`${onek}.salonda`]}
        />
      </div>
    </fieldset>
  );
  return (
    <YazmaPenceresi
      baslik={IBRA_PENCERESI_BASLIGI}
      dugme={DUGME_IBRA}
      yedekHata={IBRA_KAYDEDILEMEDI}
      baglam={`genel_kurul.ibra.${madde.id}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async () => {
        const sonuc = await genelKurulApi.ibra(madde.id, {
          yk: oylama(yk),
          dk: oylama(dk),
          unaudited_documents_note: not.trim(),
        });
        snackbar.success(IBRA_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
    >
      <p className="text-body-medium text-on-surface-variant">{IBRA_ACIKLAMASI}</p>
      {kurulAlanlari(IBRA_YK, "yk", yk, setYk)}
      {kurulAlanlari(IBRA_DK, "dk", dk, setDk)}
      <MetinAlani
        id="ibra-edilmeyen-evrak"
        etiket={ALAN_IBRA_EDILMEYEN_EVRAK}
        deger={not}
        onDegis={setNot}
        yardim={IBRA_EDILMEYEN_EVRAK_YARDIMI}
      />
    </YazmaPenceresi>
  );
}

export function AdayPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const [kisi, setKisi] = useState<BirlikKisisi | null>(null);
  const [organ, setOrgan] = useState<"YK" | "DK">("YK");
  const [koltuk, setKoltuk] = useState<"ASIL" | "YEDEK">("ASIL");
  const [hatalar, kur] = useHatalar();
  return (
    <YazmaPenceresi
      baslik={ADAY_PENCERESI_BASLIGI}
      dugme={DUGME_ADAY}
      yedekHata={ADAY_KAYDEDILEMEDI}
      baglam={`genel_kurul.aday.${kurul.id}`}
      onKapat={onKapat}
      dogrula={() => kur(kisi === null ? { kisi: KISI_SECIN } : {})}
      onGonder={async (ek) => {
        if (kisi === null) return;
        await genelKurulApi.aday(kurul.id, {
          person: kisi.id,
          organ,
          seat_type: koltuk,
          // Genel kurul Denetleme Kuruluna yalnız veli koltuğunu seçer (md. 11/1-b).
          seat_group: organ === "DK" ? "VELI" : "",
          ...ek,
        });
        snackbar.success(ADAY_KAYDEDILDI);
        onKaydedildi(null);
      }}
      ikon="person_add"
    >
      <p className="text-body-medium text-on-surface-variant">{ADAY_ACIKLAMASI}</p>
      <KisiSecimi kisiler={kisiler} secili={kisi} onSecim={setKisi} hata={hatalar.kisi} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Select
          label={ALAN_KURUL}
          value={organ}
          onChange={(e) => setOrgan(e.target.value as "YK" | "DK")}
          options={[
            { value: "YK", label: IBRA_YK },
            { value: "DK", label: IBRA_DK },
          ]}
        />
        <Select
          label={ALAN_KOLTUK}
          value={koltuk}
          onChange={(e) => setKoltuk(e.target.value as "ASIL" | "YEDEK")}
          options={[
            { value: "ASIL", label: KOLTUK_ASIL },
            { value: "YEDEK", label: KOLTUK_YEDEK },
          ]}
        />
      </div>
    </YazmaPenceresi>
  );
}

interface AdaySatiri {
  uyelik: number;
  ad: string;
  koltuk: string;
  oy: string;
  secildi: boolean;
  sira: string;
}

export function SecimPenceresi({
  kurul,
  madde,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul; madde: GundemMaddesi }) {
  const snackbar = useSnackbar();
  const organ = madde.kind === "SECIM_DK" ? "DK" : "YK";
  const [satirlar, setSatirlar] = useState<AdaySatiri[]>(
    kurul.adaylar
      .filter((a) => a.organ === organ && a.status === "ADAY")
      .map((a) => ({
        uyelik: a.id,
        ad: a.person_name ?? "—",
        koltuk: a.seat_type === "YEDEK" ? KOLTUK_YEDEK : KOLTUK_ASIL,
        oy: a.votes === null ? "" : String(a.votes),
        secildi: false,
        sira: "",
      })),
  );
  const [liste, setListe] = useState(true);
  const [acikOy, setAcikOy] = useState(true);
  const [hatalar, kur] = useHatalar();
  const degistir = (i: number, alan: Partial<AdaySatiri>) =>
    setSatirlar((s) => s.map((x, j) => (j === i ? { ...x, ...alan } : x)));
  const dogrula = () => {
    const h: Hatalar = {};
    satirlar.forEach((s, i) => {
      if (sayiOku(s.oy) === "gecersiz") h[`oy.${i}`] = SAYI_GECERSIZ;
      if (sayiOku(s.sira) === "gecersiz") h[`sira.${i}`] = SAYI_GECERSIZ;
    });
    return kur(h);
  };
  return (
    <YazmaPenceresi
      baslik={SECIM_PENCERESI_BASLIGI}
      dugme={DUGME_SECIM}
      yedekHata={SECIM_KAYDEDILEMEDI}
      baglam={`genel_kurul.secim.${madde.id}`}
      onKapat={onKapat}
      dogrula={dogrula}
      onGonder={async (ek) => {
        const sonuc = await genelKurulApi.secim(madde.id, {
          adaylar: satirlar.map((s) => ({
            uyelik: s.uyelik,
            votes: sayi(s.oy),
            secildi: s.secildi,
            seat_order: sayi(s.sira) || null,
          })),
          liste,
          acik_oy: acikOy,
          ...ek,
        });
        snackbar.success(SECIM_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
      ikon="how_to_vote"
    >
      <p className="break-words text-body-large text-on-surface">{madde.title}</p>
      <p className="text-body-medium text-on-surface-variant">{SECIM_ACIKLAMASI}</p>
      {satirlar.length === 0 ? (
        <p className="text-body-medium text-on-surface-variant">{SECIM_ADAYI_YOK}</p>
      ) : (
        <ul className="divide-y divide-outline-variant">
          {satirlar.map((s, i) => (
            <li
              key={s.uyelik}
              className="grid gap-2 py-2 sm:grid-cols-[1fr_7rem_7rem] sm:items-end"
            >
              <div className="min-w-0 space-y-1">
                <p className="break-words text-body-medium text-on-surface">
                  {s.ad} · {s.koltuk}
                </p>
                <OnayKutusu
                  etiket={ALAN_SECILDI}
                  secili={s.secildi}
                  onDegis={(d) => degistir(i, { secildi: d })}
                />
              </div>
              <SayiAlani
                etiket={ALAN_OY}
                deger={s.oy}
                onDegis={(m) => degistir(i, { oy: m })}
                hata={hatalar[`oy.${i}`]}
              />
              <SayiAlani
                etiket={ALAN_YEDEK_SIRASI}
                deger={s.sira}
                onDegis={(m) => degistir(i, { sira: m })}
                hata={hatalar[`sira.${i}`]}
              />
            </li>
          ))}
        </ul>
      )}
      <OnayKutusu etiket={ALAN_LISTE} secili={liste} onDegis={setListe} />
      <OnayKutusu etiket={ALAN_ACIK_OY} secili={acikOy} onDegis={setAcikOy} />
    </YazmaPenceresi>
  );
}

export function TutanakBilgileriPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: PencereOzellikleri & { kurul: GenelKurul }) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const tutanak = kurul.tutanak;
  // Kayıtlı kişi seçim kutusunda adıyla görünür (pasif kişi etkin listede olmayabilir).
  const kayitli = (k: { id: number; ad: string | null } | null | undefined): BirlikKisisi | null =>
    k ? ({ id: k.id, full_name: k.ad, kind: "DIGER" } as unknown as BirlikKisisi) : null;
  const [ykOkuyan, setYkOkuyan] = useState(kayitli(tutanak?.yk_report_reader));
  const [dkOkuyan, setDkOkuyan] = useState(kayitli(tutanak?.dk_report_reader));
  const [sunan, setSunan] = useState(kayitli(tutanak?.budget_presenter));
  const [teslim, setTeslim] = useState(tutanak?.handed_to_new_yk_on ?? "");
  const kisiAlani = (
    etiket: string,
    secili: BirlikKisisi | null,
    set: (k: BirlikKisisi | null) => void,
  ) => (
    <div className="space-y-1">
      <p className="text-label-large text-on-surface">{etiket}</p>
      <KisiSecimi kisiler={kisiler} secili={secili} onSecim={set} />
    </div>
  );
  /** Kısmi yazım: yalnız değişen alan gider (verilmeyen alan yazılmaz; sunucu sözleşmesi). */
  const govde = (): TutanakGovdesi => {
    const g: TutanakGovdesi = {};
    const kisi = (
      ad: "yk_report_reader" | "dk_report_reader" | "budget_presenter",
      yeni: BirlikKisisi | null,
    ) => {
      const eski = tutanak?.[ad]?.id ?? null;
      if ((yeni?.id ?? null) !== eski) g[ad] = yeni?.id ?? null;
    };
    kisi("yk_report_reader", ykOkuyan);
    kisi("dk_report_reader", dkOkuyan);
    kisi("budget_presenter", sunan);
    if ((teslim || null) !== (tutanak?.handed_to_new_yk_on ?? null)) {
      g.handed_to_new_yk_on = teslim || null;
    }
    return g;
  };
  return (
    <YazmaPenceresi
      baslik={TUTANAK_BILGILERI_BASLIGI}
      dugme={DUGME_KAYDET}
      yedekHata={TUTANAK_BILGILERI_KAYDEDILEMEDI}
      baglam={`genel_kurul.tutanak.${kurul.id}`}
      onKapat={onKapat}
      onGonder={async () => {
        const g = govde();
        if (Object.keys(g).length === 0) {
          onKapat();
          return;
        }
        const sonuc = await genelKurulApi.tutanak(kurul.id, g);
        snackbar.success(TUTANAK_BILGILERI_KAYDEDILDI);
        onKaydedildi(sonuc);
      }}
      genis
    >
      {kisiAlani(ALAN_YK_RAPORU_OKUYAN, ykOkuyan, setYkOkuyan)}
      {kisiAlani(ALAN_DK_RAPORU_OKUYAN, dkOkuyan, setDkOkuyan)}
      {kisiAlani(ALAN_BUTCEYI_SUNAN, sunan, setSunan)}
      <TextField
        label={ALAN_TESLIM_GUNU}
        type="date"
        value={teslim}
        onChange={(e) => setTeslim(e.target.value)}
        helperText={TESLIM_GUNU_YARDIMI}
      />
    </YazmaPenceresi>
  );
}

/** Gerekçe kutusunun tek başına yazma onayı (tutanağın tamamlanması; açık eksikler gerekçeyle). */
export function GerekceliOnayPenceresi({
  baslik,
  metin,
  dugme,
  yedekHata,
  baglam,
  onGonder,
  onKapat,
}: {
  baslik: string;
  metin: string;
  dugme: string;
  yedekHata: string;
  baglam: string;
  onGonder: (ek: GerekceEki) => Promise<void>;
  onKapat: () => void;
}) {
  return (
    <YazmaPenceresi
      baslik={baslik}
      dugme={dugme}
      yedekHata={yedekHata}
      baglam={baglam}
      onGonder={onGonder}
      onKapat={onKapat}
      ikon="task_alt"
    >
      <p className="text-body-medium text-on-surface">{metin}</p>
    </YazmaPenceresi>
  );
}
