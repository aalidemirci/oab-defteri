// Genel kurulun ayrıntısı ve sihirbazı (plan F2 §6.1; tasarım §7.1): Planla → Çağrı → İlan ve davet →
// Toplantı → Tutanak → Sonrası. Adım genel kurulun durumundan çıkar; tamamlanmış adıma dönülür
// (`ui/Stepper`). Her adım kaydın bilgisini her role gösterir (M3: her rol okur); yazma denetimleri
// oturumun yeteneklerine bağlıdır (plan F1b-2 "Ön yüz"; rol adıyla dallanılmaz):
//
// * `genel_kurul_yazma` — planlama, toplantı bilgisi, ilan ve kanıtı, toplantılar, katılım düzeltmesi,
//   gündem değişikliği ve sonuçları, divan, aday, seçim, ibra, tutanak (servis tasarım §7.1'in "Kim"iyle
//   daraltır);
// * çağrı: seçenekler sunucunundur (`oturum.cagiranlar`; müdürün yazısı ve Denetleme Kurulunun çağrısı
//   kendi uçlarından);
// * `genel_kurul_iptal` — iptal ve çağrı yazısının evrak bağı; `donem_gecisi_onayi` — yeni birlik
//   döneminin açılışı (U32); `kisisel_veri_ciktisi` — katılım işaretleri penceresi ve veli adlı çıktı
//   (U33, U15); `genel_kurul_dosya_eki` ve `dk_genel_kurul_yazma` — dosya ekleri (U23);
//   `mudur_genel_kurul_yazisi` — müdürün kendi çağrısında toplantı bilgisi ve gündem sırası.
//
// Sert engeller, uyarı + gerekçe ve dönem kilidi ortak bileşenle gösterilir; son yazmanın uyarıları ve
// bilgi satırları kartın başında durur. İptal edilmiş ya da tutanağı tamamlanmış genel kurul salt okurdur.

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { formatDate, formatDateTime, formatNumber } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import Stepper from "../../ui/Stepper";
import type { StepperItem } from "../../ui/Stepper";
import { DONEM_DURUMU_TR } from "../birlik-donemi/metinler";
import IptalPenceresi from "../gecis-kurulumu/IptalPenceresi";
import { gelenGidenApi } from "../gelen-giden-evrak/api";
import type { EvrakKaydi } from "../gelen-giden-evrak/api";
import { kayitNo } from "../gelen-giden-evrak/metinler";
import { useYetki } from "../oturum/yetki";
import BelgeKartlari from "./BelgeKartlari";
import CagriPenceresi from "./CagriPenceresi";
import KatilimIsaretleriPenceresi from "./KatilimIsaretleriPenceresi";
import {
  AdayPenceresi,
  DivanPenceresi,
  GerekceliOnayPenceresi,
  GundemEklePenceresi,
  GundemSirasiPenceresi,
  GundemdenCikarPenceresi,
  IbraPenceresi,
  IlanPenceresi,
  KatilimDuzeltmePenceresi,
  SecimPenceresi,
  SonucPenceresi,
  ToplantiBilgisiPenceresi,
  ToplantiPenceresi,
  TutanakBilgileriPenceresi,
} from "./Pencereler";
import { genelKurulApi } from "./api";
import type {
  DonemGecisi,
  GecisSonucu,
  GenelKurul,
  GenelKurulDurumu,
  GundemMaddesi,
  Ilan,
  KatilimTuru,
  KuralOzeti,
  Toplanti,
} from "./api";
import {
  ADAYLAR_BASLIGI,
  ADAY_YOK,
  ADIM_CAGRI,
  ADIM_ILAN,
  ADIM_PLANLA,
  ADIM_SONRASI,
  ADIM_TOPLANTI,
  ADIM_TUTANAK,
  ALAN_BASVURAN_SAYISI,
  ALAN_BIRINCI_TOPLANTI,
  ALAN_BUTCEYI_SUNAN,
  ALAN_CAGIRAN,
  ALAN_CAGRI_NEDENI,
  ALAN_DIVAN_BASKANI,
  ALAN_DK_RAPORU_OKUYAN,
  ALAN_DONEM_BASLANGICI,
  ALAN_DURUM,
  ALAN_ELDEN_YAZILI,
  ALAN_GOZLEMCI,
  ALAN_IKINCI_TOPLANTI,
  ALAN_ILAN_GUNU,
  ALAN_ILAN_PANOSU,
  ALAN_INTERNET,
  ALAN_IPTAL_NEDENI,
  ALAN_KAPANACAK_BITIS,
  ALAN_KATIP,
  ALAN_KAPANACAK_DONEM,
  ALAN_KATILAN,
  ALAN_OGRENCI_MEVCUDU,
  ALAN_TESLIM_GUNU,
  ALAN_TUR,
  ALAN_UYE_SAYISI,
  ALAN_VELISI_KATILAN,
  ALAN_YAPILDIGI_TOPLANTI,
  ALAN_YENI_DONEM,
  ALAN_YER,
  ALAN_YETER_SAYI,
  ALAN_YK_RAPORU_OKUYAN,
  BOS_DEGER,
  CAGIRAN_TR,
  CAGRI_BASLIGI,
  CAGRI_SECENEGI_YOK,
  CAGRI_YAZISI_ACIKLAMASI,
  CAGRI_YAZISI_BAGLANAMADI,
  CAGRI_YAZISI_BAGLANDI,
  CAGRI_YAZISI_BAGLI,
  CAGRI_YAZISI_BAGSIZ,
  CAGRI_YAZISI_BASLIGI,
  DAGILIM_BASLIGI,
  DIVAN_BASLIGI,
  DIVAN_IPTAL_BASLIGI,
  DIVAN_IPTAL_EDILDI,
  DIVAN_IPTAL_EDILEMEDI,
  DIVAN_IPTAL_METNI,
  DIVAN_YOK,
  DK_GOREV_BOLUMU_AC,
  DONEM_ACIK_NOTU,
  DONEM_GECISI_ACIKLAMASI,
  DONEM_GECISI_BASLIGI,
  DONEM_GECISI_ENGELLERI,
  DONEM_GECISI_OKUNAMADI,
  DONEM_GECISI_ONAYLANAMADI,
  DONEM_GECISI_ONAYLANDI,
  DONEM_GECISI_ONAY_BASLIGI,
  DONEM_GECISI_ONAY_METNI,
  DOSYA_EKLERI_ACIKLAMASI,
  DOSYA_EKLERI_BASLIGI,
  DUGME_ADAY,
  DUGME_BIRINCI_TOPLANTI,
  DUGME_CAGRI,
  DUGME_CAGRI_YAZISI,
  DUGME_DIVAN,
  DUGME_DIVAN_IPTAL,
  DUGME_DONEM_GECISI,
  DUGME_GUNDEMDEN_CIKAR,
  DUGME_GUNDEM_EKLE,
  DUGME_GUNDEM_SIRASI,
  DUGME_IBRA,
  DUGME_IKINCI_ILAN,
  DUGME_IKINCI_TOPLANTI,
  DUGME_ILAN,
  DUGME_IPTAL,
  DUGME_KANIT,
  DUGME_KATILIM_DUZELTMESI,
  DUGME_KATILIM_ISARETLERI,
  DUGME_LISTEYE_DON,
  DUGME_SECIM,
  DUGME_SECIM_IPTAL,
  DUGME_SONUC,
  DUGME_TOPLANTI_BILGISI,
  DUGME_TUTANAK_BILGILERI,
  DUGME_TUTANAK_TAMAMLA,
  DURUM_TR,
  DUZELTMELER_BASLIGI,
  DUZELTME_ALANI_TR,
  GECIS_UYARILARI_BASLIGI,
  GENEL_KURUL_OKUNAMADI,
  GOREV_BOLUMU_ACIKLAMASI,
  GOREV_BOLUMU_BASLIGI,
  GUNDEMDEN_CIKARILDI,
  GUNDEM_BASLIGI,
  GUNDEM_BOS,
  GUNDEM_SONUCLARI_BASLIGI,
  GUNDEM_TURU_TR,
  IBRA_BASLIGI,
  IBRA_DK,
  IBRA_TR,
  IBRA_YK,
  ILANLAR_BASLIGI,
  ILAN_BASLIGI,
  ILAN_YOK,
  IPTAL_BASLIGI,
  IPTAL_EDILDI,
  IPTAL_EDILDI_NOTU,
  IPTAL_EDILEMEDI,
  IPTAL_METNI,
  KANIT_EKI_YARDIMI,
  KANIT_EKLERI,
  KATILIM_TURU_TR,
  KOLTUK_ASIL,
  KOLTUK_YEDEK,
  KURAL_UYARILARI_BASLIGI,
  OLAGANUSTU_DONEM_ACMAZ,
  OYLAMAYLA_EKLENDI,
  SECIN,
  SIHIRBAZ_ADIMLARI,
  SECIM_IPTAL_BASLIGI,
  SECIM_IPTAL_EDILDI,
  SECIM_IPTAL_EDILEMEDI,
  SECIM_IPTAL_METNI,
  SONRASI_BASLIGI,
  SONUC_TR,
  TEFBIS_ACIKLAMASI,
  TEFBIS_BASLIGI,
  TOPLANTI_BASLIGI,
  TOPLANTI_TR,
  TUR_TR,
  TUTANAK_BASLIGI,
  TUTANAK_BILGILERI_BASLIGI,
  TUTANAK_TAMAMLANAMADI,
  TUTANAK_TAMAMLANDI,
  TUTANAK_TAMAMLA_BASLIGI,
  TUTANAK_TAMAMLA_METNI,
  TUTANAK_TAMAM_NOTU,
  UYELIK_DURUMU_TR,
  YETER_SAYI_YOK_NOTU,
  YK_GOREV_BOLUMU_AC,
  duzeltmeMetni,
  genelKurulAdi,
  isaretOnerisi,
  oyMetni,
  oySayisi,
  yeterSayiMetni,
} from "./metinler";
import {
  Bilgi,
  BilgiSatirlari,
  Bolum,
  EkListesi,
  KuralUyarilari,
  YazmaPenceresi as GerekcesizYazma,
} from "./ortak";

/** Sihirbazın adımları (sırasıyla). */
const ADIMLAR = [
  { key: "planla", label: ADIM_PLANLA, icon: "event" },
  { key: "cagri", label: ADIM_CAGRI, icon: "campaign" },
  { key: "ilan", label: ADIM_ILAN, icon: "mail" },
  { key: "toplanti", label: ADIM_TOPLANTI, icon: "groups" },
  { key: "tutanak", label: ADIM_TUTANAK, icon: "description" },
  { key: "sonrasi", label: ADIM_SONRASI, icon: "flag" },
] as const;

/** Durumun sihirbazdaki adımı: işin süren adımı (tamamlanmışlara dönülür). */
const DURUM_ADIMI: Record<Exclude<GenelKurulDurumu, "IPTAL">, number> = {
  PLANLANDI: 1,
  CAGRILDI: 2,
  ILAN_EDILDI: 3,
  YETER_SAYI_YOK: 3,
  YAPILDI: 4,
  TUTANAK_TAMAM: 5,
};

/** Sürmekte olan adım (iptal edilmiş kurulda kaydın ulaştığı adım). */
export function surenAdim(kurul: GenelKurul): number {
  if (kurul.status !== "IPTAL") return DURUM_ADIMI[kurul.status];
  if (kurul.held_at_meeting) return 4;
  if (kurul.announced_on) return 3;
  if (kurul.called_by) return 2;
  return 1;
}

const IPTAL_EDILEBILIR: readonly GenelKurulDurumu[] = [
  "PLANLANDI",
  "CAGRILDI",
  "ILAN_EDILDI",
  "YETER_SAYI_YOK",
];
const KANIT_YAZILABILIR: readonly GenelKurulDurumu[] = ["ILAN_EDILDI", "YETER_SAYI_YOK", "YAPILDI"];
const ISARET_YAZILABILIR: readonly GenelKurulDurumu[] = [
  "ILAN_EDILDI",
  "YETER_SAYI_YOK",
  "YAPILDI",
];
const DUZELTILEBILIR: readonly GenelKurulDurumu[] = ["YETER_SAYI_YOK", "YAPILDI", "TUTANAK_TAMAM"];
const ACIK_DURUMLAR: readonly GenelKurulDurumu[] = [
  "PLANLANDI",
  "CAGRILDI",
  "ILAN_EDILDI",
  "YETER_SAYI_YOK",
  "YAPILDI",
];
const YAZI_BAGLANAN = ["UYE_BASVURUSU", "DENETLEME_KURULU"];

type Pencere =
  | null
  | { tur: "cagri" }
  | { tur: "cagri_yazisi" }
  | { tur: "toplanti_bilgisi" }
  | { tur: "gundem_sirasi" }
  | { tur: "ilan" }
  | { tur: "ikinci_ilan" }
  | { tur: "kanit"; ilan: Ilan }
  | { tur: "toplanti"; toplanti: Toplanti }
  | { tur: "isaretler" }
  | { tur: "duzeltme" }
  | { tur: "divan" }
  | { tur: "divan_iptal" }
  | { tur: "sonuc"; madde: GundemMaddesi }
  | { tur: "gundem_ekle" }
  | { tur: "gundemden_cikar"; madde: GundemMaddesi }
  | { tur: "ibra"; madde: GundemMaddesi }
  | { tur: "aday" }
  | { tur: "secim"; madde: GundemMaddesi }
  | { tur: "secim_iptal"; madde: GundemMaddesi }
  | { tur: "tutanak" }
  | { tur: "tamamla" }
  | { tur: "iptal" };

function deger(sayi: number | null): string {
  return sayi === null ? BOS_DEGER : formatNumber(sayi);
}

function GundemListesi({
  gundem,
  eylemler,
}: {
  gundem: readonly GundemMaddesi[];
  eylemler?: (m: GundemMaddesi) => ReactNode;
}) {
  if (gundem.length === 0) {
    return <p className="text-body-medium text-on-surface-variant">{GUNDEM_BOS}</p>;
  }
  return (
    <ol aria-label={GUNDEM_BASLIGI} className="divide-y divide-outline-variant">
      {gundem.map((m) => (
        <li key={m.id} className="flex flex-wrap items-start justify-between gap-2 py-2">
          <div className="min-w-0 flex-1">
            <p
              className={`break-words text-body-medium text-on-surface ${m.removed_by_vote ? "line-through" : ""}`}
            >
              {m.order}. {m.title}
            </p>
            <p className="text-body-small text-on-surface-variant">
              {[
                GUNDEM_TURU_TR[m.kind],
                m.added_by_vote ? OYLAMAYLA_EKLENDI : null,
                m.removed_by_vote ? GUNDEMDEN_CIKARILDI : null,
                m.result ? SONUC_TR[m.result] : null,
                m.votes_for !== null || m.votes_against !== null
                  ? oyMetni(m.votes_for, m.votes_against, m.present_count)
                  : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
            {m.result_text && (
              <p className="break-words text-body-small text-on-surface-variant">{m.result_text}</p>
            )}
          </div>
          {eylemler && <div className="flex flex-wrap gap-2">{eylemler(m)}</div>}
        </li>
      ))}
    </ol>
  );
}

function CagriYazisiPenceresi({
  kurul,
  onKapat,
  onKaydedildi,
}: {
  kurul: GenelKurul;
  onKapat: () => void;
  onKaydedildi: (sonuc: GecisSonucu) => void;
}) {
  const snackbar = useSnackbar();
  const [kayitlar, setKayitlar] = useState<EvrakKaydi[]>([]);
  const [secili, setSecili] = useState("");
  const [hata, setHata] = useState("");
  useEffect(() => {
    let iptal = false;
    gelenGidenApi
      .kayitlar(kurul.called_by === "UYE_BASVURUSU" ? { direction: "GELEN" } : {})
      .then((l) => {
        if (!iptal) setKayitlar(l.filter((k) => k.term === kurul.term));
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, [kurul.called_by, kurul.term]);
  return (
    <GerekcesizYazma
      baslik={CAGRI_YAZISI_BASLIGI}
      dugme={DUGME_CAGRI_YAZISI}
      yedekHata={CAGRI_YAZISI_BAGLANAMADI}
      baglam={`genel_kurul.cagri_yazisi.${kurul.id}`}
      onKapat={onKapat}
      dogrula={() => {
        setHata(secili ? "" : SECIN);
        return secili !== "";
      }}
      onGonder={async () => {
        const sonuc = await genelKurulApi.cagriYazisi(kurul.id, Number(secili));
        snackbar.success(CAGRI_YAZISI_BAGLANDI);
        onKaydedildi(sonuc);
      }}
    >
      <p className="text-body-medium text-on-surface-variant">{CAGRI_YAZISI_ACIKLAMASI}</p>
      <Select
        label={CAGRI_YAZISI_BASLIGI}
        value={secili}
        placeholder={SECIN}
        onChange={(e) => setSecili(e.target.value)}
        options={kayitlar.map((k) => ({
          value: String(k.id),
          label: `${kayitNo(k.year, k.record_no)} · ${formatDate(k.date)}`,
        }))}
        error={hata || undefined}
      />
    </GerekcesizYazma>
  );
}

function DonemGecisiBolumu({
  kurul,
  onaylayabilir,
  onOnaylandi,
}: {
  kurul: GenelKurul;
  onaylayabilir: boolean;
  onOnaylandi: () => void;
}) {
  const snackbar = useSnackbar();
  const confirm = useConfirm();
  const [gecis, setGecis] = useState<DonemGecisi | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let iptal = false;
    genelKurulApi
      .donemGecisi(kurul.id)
      .then((g) => {
        if (!iptal) setGecis(g);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, DONEM_GECISI_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [kurul.id]);

  const onayla = async () => {
    const tamam = await confirm({
      title: DONEM_GECISI_ONAY_BASLIGI,
      message: DONEM_GECISI_ONAY_METNI,
      confirmLabel: DUGME_DONEM_GECISI,
    });
    if (!tamam) return;
    setBusy(true);
    setHata(null);
    try {
      const sonuc = await genelKurulApi.donemGecisiniOnayla(kurul.id);
      setGecis({ ...sonuc, engeller: [] });
      snackbar.success(DONEM_GECISI_ONAYLANDI);
      onOnaylandi();
    } catch (e) {
      setHata(hataOku(e, DONEM_GECISI_ONAYLANAMADI));
    } finally {
      setBusy(false);
    }
  };

  const acik = gecis?.yeni_donem.status === "ACIK";
  return (
    <Bolum baslik={DONEM_GECISI_BASLIGI} aciklama={DONEM_GECISI_ACIKLAMASI}>
      {hata && <ErrorBand hata={hata} />}
      {gecis === null ? (
        !hata && <SkeletonList rows={2} />
      ) : (
        <>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Bilgi etiket={ALAN_YENI_DONEM}>
              {gecis.yeni_donem.name} · {DONEM_DURUMU_TR[gecis.yeni_donem.status]}
            </Bilgi>
            <Bilgi etiket={ALAN_DONEM_BASLANGICI}>{formatDate(gecis.baslangic)}</Bilgi>
            {gecis.kapanacak && (
              <>
                <Bilgi etiket={ALAN_KAPANACAK_DONEM}>
                  {gecis.kapanacak.name} · {DONEM_DURUMU_TR[gecis.kapanacak.status]}
                </Bilgi>
                <Bilgi etiket={ALAN_KAPANACAK_BITIS}>{formatDate(gecis.kapanacak_bitis)}</Bilgi>
              </>
            )}
          </dl>
          {acik ? (
            <p role="status" className="text-body-medium text-on-surface">
              {DONEM_ACIK_NOTU}
            </p>
          ) : (
            <>
              {gecis.engeller.length > 0 && (
                <BilgiSatirlari bilgiler={gecis.engeller} baslik={DONEM_GECISI_ENGELLERI} />
              )}
              {onaylayabilir && gecis.engeller.length === 0 && (
                <div className="flex justify-end">
                  <Button icon="event_available" disabled={busy} onClick={() => void onayla()}>
                    {DUGME_DONEM_GECISI}
                  </Button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </Bolum>
  );
}

export default function GenelKurulAyrintisi({
  kurulId,
  onListeyeDon,
  onDegisti,
}: {
  kurulId: number;
  onListeyeDon: () => void;
  /** Liste yenilensin (durum değişti). */
  onDegisti: () => void;
}) {
  const yetki = useYetki();
  const snackbar = useSnackbar();
  const [kurul, setKurul] = useState<GenelKurul | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [son, setSon] = useState<{ uyarilar: KuralOzeti[]; bilgiler: string[] } | null>(null);
  const [pencere, setPencere] = useState<Pencere>(null);
  const [adim, setAdim] = useState<number | null>(null);
  const [yenile, setYenile] = useState(0);

  useEffect(() => {
    let iptal = false;
    genelKurulApi
      .ayrinti(kurulId)
      .then((k) => {
        if (iptal) return;
        setKurul(k);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, GENEL_KURUL_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [kurulId, yenile]);

  // Durum değişince süren adım gösterilir.
  const durum = kurul?.status;
  useEffect(() => setAdim(null), [durum]);

  const tazele = useCallback(() => setYenile((y) => y + 1), []);

  const yazildi = useCallback(
    (sonuc: GecisSonucu | null) => {
      setPencere(null);
      if (sonuc === null) {
        tazele();
      } else {
        setKurul(sonuc.genel_kurul);
        setSon({ uyarilar: sonuc.uyarilar, bilgiler: sonuc.bilgiler });
      }
      onDegisti();
    },
    [onDegisti, tazele],
  );

  if (kurul === null) {
    return hata ? <ErrorBand hata={hata} /> : <SkeletonList rows={6} />;
  }

  const yaz = yetki.acik("genel_kurul_yazma");
  const st = kurul.status;
  const acikKurul = ACIK_DURUMLAR.includes(st);
  const sahip = kurul.cagri_sahibi;
  // Çağrı yazısının alanları (toplantı zamanı, gündem sırası) ilandan önce: sahibi müdürse müdür,
  // sahipsiz çağrıda genel kurul yazma kapısı (`genel_kurul._duzenleme_kapisi`).
  const ilandanOnce = st === "PLANLANDI" || st === "CAGRILDI";
  const cagriAlanlariYazilir =
    ilandanOnce &&
    (st === "PLANLANDI" || sahip === null
      ? yaz
      : sahip === "mudur" && yetki.acik("mudur_genel_kurul_yazisi"));
  const sure = surenAdim(kurul);
  // Düzeltilen divanın kayıtları silinmez, `IPTAL` olur (sunucu ayrıntıda göstermez; burada da ayrılır).
  const etkinDivan = kurul.divan.filter((u) => u.status !== "IPTAL");
  const gosterilen = adim ?? sure;
  const adimlar: StepperItem[] = ADIMLAR.map((a, i) => ({
    key: a.key,
    label: a.label,
    icon: a.icon,
    status: i === gosterilen ? "current" : i < sure ? "done" : "upcoming",
  }));
  const ikinciIlan = kurul.ilanlar.length > 1 || kurul.second_announced_on !== null;
  const ekYazilir = (m: GundemMaddesi) =>
    acikKurul &&
    !m.removed_by_vote &&
    (m.kind === "DK_RAPORU"
      ? yetki.acik("dk_genel_kurul_yazma")
      : yetki.acik("genel_kurul_dosya_eki"));
  const dosyaEkiMaddeleri = kurul.gundem.filter((m) => m.dosya_eki_belgesi);

  const planla = (
    <div className="space-y-4">
      <dl className="grid gap-3 sm:grid-cols-2">
        <Bilgi etiket={ALAN_TUR}>{TUR_TR[kurul.kind]}</Bilgi>
        <Bilgi etiket={ALAN_BIRINCI_TOPLANTI}>{formatDateTime(kurul.first_meeting_at)}</Bilgi>
        <Bilgi etiket={ALAN_YER}>{kurul.venue || BOS_DEGER}</Bilgi>
      </dl>
      <Bolum
        baslik={GUNDEM_BASLIGI}
        eylem={
          cagriAlanlariYazilir && (
            <>
              <Button
                variant="tonal"
                icon="edit_calendar"
                onClick={() => setPencere({ tur: "toplanti_bilgisi" })}
              >
                {DUGME_TOPLANTI_BILGISI}
              </Button>
              {kurul.gundem.length > 1 && (
                <Button
                  variant="tonal"
                  icon="swap_vert"
                  onClick={() => setPencere({ tur: "gundem_sirasi" })}
                >
                  {DUGME_GUNDEM_SIRASI}
                </Button>
              )}
            </>
          )
        }
      >
        <GundemListesi gundem={kurul.gundem} />
      </Bolum>
    </div>
  );

  const cagri = (
    <div className="space-y-4">
      {kurul.called_by ? (
        <dl className="grid gap-3 sm:grid-cols-2">
          <Bilgi etiket={ALAN_CAGIRAN}>{CAGIRAN_TR[kurul.called_by]}</Bilgi>
          {kurul.kind === "OLAGANUSTU" && (
            <Bilgi etiket={ALAN_CAGRI_NEDENI}>{kurul.call_reason ?? BOS_DEGER}</Bilgi>
          )}
          {kurul.called_by === "UYE_BASVURUSU" && (
            <>
              <Bilgi etiket={ALAN_BASVURAN_SAYISI}>{deger(kurul.member_application_count)}</Bilgi>
              <Bilgi etiket={ALAN_UYE_SAYISI}>{deger(kurul.member_count_declared)}</Bilgi>
            </>
          )}
          {YAZI_BAGLANAN.includes(kurul.called_by) && (
            <Bilgi etiket={CAGRI_YAZISI_BASLIGI}>
              {kurul.call_document !== null ? CAGRI_YAZISI_BAGLI : CAGRI_YAZISI_BAGSIZ}
            </Bilgi>
          )}
        </dl>
      ) : (
        st === "PLANLANDI" &&
        kurul.oturum.cagiranlar.length === 0 && (
          <p className="text-body-medium text-on-surface-variant">{CAGRI_SECENEGI_YOK}</p>
        )
      )}
      <div className="flex flex-wrap justify-end gap-2">
        {st === "PLANLANDI" && kurul.oturum.cagiranlar.length > 0 && (
          <Button icon="campaign" onClick={() => setPencere({ tur: "cagri" })}>
            {DUGME_CAGRI}
          </Button>
        )}
        {acikKurul &&
          YAZI_BAGLANAN.includes(kurul.called_by) &&
          kurul.call_document === null &&
          yetki.acik("genel_kurul_iptal") && (
            <Button variant="tonal" icon="link" onClick={() => setPencere({ tur: "cagri_yazisi" })}>
              {DUGME_CAGRI_YAZISI}
            </Button>
          )}
      </div>
    </div>
  );

  const ilan = (
    <div className="space-y-4">
      <dl className="grid gap-3 sm:grid-cols-2">
        <Bilgi etiket={ALAN_ILAN_GUNU}>{formatDate(kurul.announced_on)}</Bilgi>
        <Bilgi etiket={ALAN_YETER_SAYI}>
          {kurul.quorum_required === null
            ? BOS_DEGER
            : yeterSayiMetni(kurul.quorum_required, kurul.quorum_base, kurul.quorum_multiplier)}
        </Bilgi>
        <Bilgi etiket={ALAN_OGRENCI_MEVCUDU}>{deger(kurul.student_count_snapshot)}</Bilgi>
        <Bilgi etiket={ALAN_IKINCI_TOPLANTI}>{formatDateTime(kurul.second_meeting_at)}</Bilgi>
      </dl>
      <Bolum baslik={ILANLAR_BASLIGI}>
        {kurul.ilanlar.length === 0 ? (
          <p className="text-body-medium text-on-surface-variant">{ILAN_YOK}</p>
        ) : (
          <ul className="space-y-3">
            {kurul.ilanlar.map((d) => (
              <li
                key={d.id}
                className="space-y-3 rounded-shape-sm border border-outline-variant p-3"
              >
                <dl className="grid gap-3 sm:grid-cols-3">
                  <Bilgi etiket={ALAN_ELDEN_YAZILI}>{formatDate(d.distributed_written_on)}</Bilgi>
                  <Bilgi etiket={ALAN_ILAN_PANOSU}>{formatDate(d.posted_board_on)}</Bilgi>
                  <Bilgi etiket={ALAN_INTERNET}>{formatDate(d.published_web_on)}</Bilgi>
                </dl>
                <EkListesi
                  ekler={d.ekler}
                  baslik={KANIT_EKLERI}
                  yardim={KANIT_EKI_YARDIMI}
                  onEkle={
                    yaz && KANIT_YAZILABILIR.includes(st)
                      ? async (dosya) => {
                          await genelKurulApi.ilanEki(d.id, dosya);
                          tazele();
                        }
                      : undefined
                  }
                />
                {yaz && KANIT_YAZILABILIR.includes(st) && (
                  <div className="flex justify-end">
                    <Button
                      variant="tonal"
                      icon="edit_calendar"
                      onClick={() => setPencere({ tur: "kanit", ilan: d })}
                    >
                      {DUGME_KANIT}
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Bolum>
      <div className="flex flex-wrap justify-end gap-2">
        {st === "CAGRILDI" && yaz && (
          <Button icon="campaign" onClick={() => setPencere({ tur: "ilan" })}>
            {DUGME_ILAN}
          </Button>
        )}
        {st === "YETER_SAYI_YOK" && yaz && !ikinciIlan && (
          <Button
            variant="tonal"
            icon="campaign"
            onClick={() => setPencere({ tur: "ikinci_ilan" })}
          >
            {DUGME_IKINCI_ILAN}
          </Button>
        )}
      </div>
    </div>
  );

  const dagilim = Object.entries(kurul.attendance_by_kind ?? {}) as [KatilimTuru, number][];
  const isaretSayisi = (t: Toplanti) => kurul.katilim_isareti_sayilari?.[t] ?? 0;
  const toplanti = (
    <div className="space-y-4">
      {st === "YETER_SAYI_YOK" && (
        <p role="note" className="text-body-medium text-on-surface">
          {YETER_SAYI_YOK_NOTU}
        </p>
      )}
      <dl className="grid gap-3 sm:grid-cols-2">
        <Bilgi etiket={`${TOPLANTI_TR.BIRINCI} · ${ALAN_KATILAN}`}>
          {deger(kurul.first_attendee_count)}
        </Bilgi>
        <Bilgi etiket={`${TOPLANTI_TR.IKINCI} · ${ALAN_KATILAN}`}>
          {deger(kurul.second_attendee_count)}
        </Bilgi>
        <Bilgi etiket={ALAN_YAPILDIGI_TOPLANTI}>
          {kurul.held_at_meeting ? TOPLANTI_TR[kurul.held_at_meeting] : BOS_DEGER}
        </Bilgi>
        <Bilgi etiket={ALAN_VELISI_KATILAN}>{deger(kurul.parent_students_count)}</Bilgi>
        <Bilgi etiket={ALAN_GOZLEMCI}>{deger(kurul.observer_count)}</Bilgi>
        {dagilim.length > 0 && (
          <Bilgi etiket={DAGILIM_BASLIGI}>
            {dagilim.map(([t, s]) => `${KATILIM_TURU_TR[t]} ${formatNumber(s)}`).join(" · ")}
          </Bilgi>
        )}
      </dl>
      {(["BIRINCI", "IKINCI"] as const)
        .filter((t) => isaretSayisi(t) > 0)
        .map((t) => (
          <p key={t} className="text-body-small text-on-surface-variant">
            {TOPLANTI_TR[t]} · {isaretOnerisi(isaretSayisi(t))}
          </p>
        ))}
      {kurul.katilim_duzeltmeleri.length > 0 && (
        <Bolum baslik={DUZELTMELER_BASLIGI}>
          <ul className="space-y-1 text-body-medium text-on-surface">
            {kurul.katilim_duzeltmeleri.map((d) => (
              <li key={d.id} className="break-words">
                {duzeltmeMetni(
                  TOPLANTI_TR[d.meeting],
                  DUZELTME_ALANI_TR[d.field] ?? d.field,
                  deger(d.old_value),
                  formatNumber(d.new_value),
                )}{" "}
                · {formatDateTime(d.corrected_at)}
              </li>
            ))}
          </ul>
        </Bolum>
      )}
      <div className="flex flex-wrap justify-end gap-2">
        {yetki.acik("kisisel_veri_ciktisi") && ISARET_YAZILABILIR.includes(st) && (
          <Button
            variant="outlined"
            icon="checklist"
            onClick={() => setPencere({ tur: "isaretler" })}
          >
            {DUGME_KATILIM_ISARETLERI}
          </Button>
        )}
        {yaz && DUZELTILEBILIR.includes(st) && (
          <Button variant="tonal" icon="edit" onClick={() => setPencere({ tur: "duzeltme" })}>
            {DUGME_KATILIM_DUZELTMESI}
          </Button>
        )}
        {yaz && st === "ILAN_EDILDI" && (
          <Button
            icon="groups"
            onClick={() => setPencere({ tur: "toplanti", toplanti: "BIRINCI" })}
          >
            {DUGME_BIRINCI_TOPLANTI}
          </Button>
        )}
        {yaz && st === "YETER_SAYI_YOK" && (
          <Button icon="groups" onClick={() => setPencere({ tur: "toplanti", toplanti: "IKINCI" })}>
            {DUGME_IKINCI_TOPLANTI}
          </Button>
        )}
      </div>
    </div>
  );

  const toplantida = st === "YAPILDI" && yaz;
  const maddeEylemleri = (m: GundemMaddesi) => {
    if (!toplantida || m.removed_by_vote) return null;
    if (m.kind === "IBRA") {
      return (
        <Button variant="tonal" onClick={() => setPencere({ tur: "ibra", madde: m })}>
          {DUGME_IBRA}
        </Button>
      );
    }
    if (m.kind === "SECIM_YK" || m.kind === "SECIM_DK") {
      return m.result ? (
        <Button variant="text" onClick={() => setPencere({ tur: "secim_iptal", madde: m })}>
          {DUGME_SECIM_IPTAL}
        </Button>
      ) : (
        <Button variant="tonal" onClick={() => setPencere({ tur: "secim", madde: m })}>
          {DUGME_SECIM}
        </Button>
      );
    }
    return (
      <>
        <Button variant="tonal" onClick={() => setPencere({ tur: "sonuc", madde: m })}>
          {DUGME_SONUC}
        </Button>
        {!m.result && (
          <Button variant="text" onClick={() => setPencere({ tur: "gundemden_cikar", madde: m })}>
            {DUGME_GUNDEMDEN_CIKAR}
          </Button>
        )}
      </>
    );
  };
  const ibraMetni = (s: GenelKurul["discharge_yk"]) => (s ? IBRA_TR[s] : BOS_DEGER);
  const tutanak = (
    <div className="space-y-5">
      <Bolum
        baslik={DIVAN_BASLIGI}
        eylem={
          toplantida &&
          (etkinDivan.length === 0 ? (
            <Button variant="tonal" icon="gavel" onClick={() => setPencere({ tur: "divan" })}>
              {DUGME_DIVAN}
            </Button>
          ) : (
            <Button variant="text" onClick={() => setPencere({ tur: "divan_iptal" })}>
              {DUGME_DIVAN_IPTAL}
            </Button>
          ))
        }
      >
        {etkinDivan.length === 0 ? (
          <p className="text-body-medium text-on-surface-variant">{DIVAN_YOK}</p>
        ) : (
          <ul className="space-y-1 text-body-medium text-on-surface">
            {etkinDivan.map((u) => (
              <li key={u.id} className="break-words">
                {u.person_name ?? BOS_DEGER} ·{" "}
                {u.role === "KATIP" ? ALAN_KATIP : ALAN_DIVAN_BASKANI}
              </li>
            ))}
          </ul>
        )}
      </Bolum>
      <Bolum
        baslik={GUNDEM_SONUCLARI_BASLIGI}
        eylem={
          toplantida && (
            <Button
              variant="tonal"
              icon="playlist_add"
              onClick={() => setPencere({ tur: "gundem_ekle" })}
            >
              {DUGME_GUNDEM_EKLE}
            </Button>
          )
        }
      >
        <GundemListesi gundem={kurul.gundem} eylemler={maddeEylemleri} />
      </Bolum>
      <Bolum baslik={IBRA_BASLIGI}>
        <dl className="grid gap-3 sm:grid-cols-2">
          <Bilgi etiket={IBRA_YK}>
            {ibraMetni(kurul.discharge_yk)}
            {kurul.discharge_yk_votes_for !== null &&
              ` · ${oyMetni(kurul.discharge_yk_votes_for, kurul.discharge_yk_votes_against, kurul.discharge_yk_present_count)}`}
          </Bilgi>
          <Bilgi etiket={IBRA_DK}>
            {ibraMetni(kurul.discharge_dk)}
            {kurul.discharge_dk_votes_for !== null &&
              ` · ${oyMetni(kurul.discharge_dk_votes_for, kurul.discharge_dk_votes_against, kurul.discharge_dk_present_count)}`}
          </Bilgi>
        </dl>
      </Bolum>
      <Bolum
        baslik={ADAYLAR_BASLIGI}
        eylem={
          yaz &&
          acikKurul && (
            <Button variant="tonal" icon="person_add" onClick={() => setPencere({ tur: "aday" })}>
              {DUGME_ADAY}
            </Button>
          )
        }
      >
        {kurul.adaylar.length === 0 ? (
          <p className="text-body-medium text-on-surface-variant">{ADAY_YOK}</p>
        ) : (
          <ul className="divide-y divide-outline-variant">
            {kurul.adaylar.map((a) => (
              <li key={a.id} className="py-1.5 text-body-medium text-on-surface">
                <span className="break-words">{a.person_name ?? BOS_DEGER}</span>
                <span className="block text-body-small text-on-surface-variant">
                  {[
                    a.organ === "DK" ? IBRA_DK : IBRA_YK,
                    a.seat_type === "YEDEK" ? KOLTUK_YEDEK : KOLTUK_ASIL,
                    UYELIK_DURUMU_TR[a.status],
                    a.votes !== null ? oySayisi(a.votes) : null,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Bolum>
      <Bolum
        baslik={TUTANAK_BILGILERI_BASLIGI}
        eylem={
          yaz &&
          (st === "YAPILDI" || st === "TUTANAK_TAMAM") && (
            <Button variant="tonal" icon="edit_note" onClick={() => setPencere({ tur: "tutanak" })}>
              {DUGME_TUTANAK_BILGILERI}
            </Button>
          )
        }
      >
        <dl className="grid gap-3 sm:grid-cols-2">
          <Bilgi etiket={ALAN_YK_RAPORU_OKUYAN}>
            {kurul.tutanak?.yk_report_reader?.ad ?? BOS_DEGER}
          </Bilgi>
          <Bilgi etiket={ALAN_DK_RAPORU_OKUYAN}>
            {kurul.tutanak?.dk_report_reader?.ad ?? BOS_DEGER}
          </Bilgi>
          <Bilgi etiket={ALAN_BUTCEYI_SUNAN}>
            {kurul.tutanak?.budget_presenter?.ad ?? BOS_DEGER}
          </Bilgi>
          <Bilgi etiket={ALAN_TESLIM_GUNU}>{formatDate(kurul.tutanak?.handed_to_new_yk_on)}</Bilgi>
        </dl>
      </Bolum>
      {toplantida && (
        <div className="flex justify-end">
          <Button icon="task_alt" onClick={() => setPencere({ tur: "tamamla" })}>
            {DUGME_TUTANAK_TAMAMLA}
          </Button>
        </div>
      )}
    </div>
  );

  const sonrasi = (
    <div className="space-y-5">
      {kurul.kind === "OLAGAN" && kurul.opens_term !== null ? (
        <DonemGecisiBolumu
          kurul={kurul}
          onaylayabilir={yetki.acik("donem_gecisi_onayi")}
          onOnaylandi={onDegisti}
        />
      ) : (
        <p className="text-body-medium text-on-surface-variant">{OLAGANUSTU_DONEM_ACMAZ}</p>
      )}
      <Bolum baslik={GOREV_BOLUMU_BASLIGI} aciklama={GOREV_BOLUMU_ACIKLAMASI}>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/organlar"
            className="text-label-large text-primary underline underline-offset-2"
          >
            {YK_GOREV_BOLUMU_AC}
          </Link>
          <Link
            to="/organlar?tab=dk"
            className="text-label-large text-primary underline underline-offset-2"
          >
            {DK_GOREV_BOLUMU_AC}
          </Link>
        </div>
      </Bolum>
      {kurul.kind === "OLAGAN" && (
        <Bolum baslik={TEFBIS_BASLIGI}>
          <p className="text-body-medium text-on-surface-variant">{TEFBIS_ACIKLAMASI}</p>
        </Bolum>
      )}
    </div>
  );

  const icerikler = [planla, cagri, ilan, toplanti, tutanak, sonrasi];
  const basliklar = [
    ADIM_PLANLA,
    CAGRI_BASLIGI,
    ILAN_BASLIGI,
    TOPLANTI_BASLIGI,
    TUTANAK_BASLIGI,
    SONRASI_BASLIGI,
  ];

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="break-words text-title-medium text-on-surface">
              {genelKurulAdi(kurul.kind, formatDateTime(kurul.first_meeting_at))}
            </h2>
            <p className="text-body-medium text-on-surface-variant">
              {ALAN_DURUM}: {DURUM_TR[st]}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="text" icon="arrow_back" onClick={onListeyeDon}>
              {DUGME_LISTEYE_DON}
            </Button>
            {yetki.acik("genel_kurul_iptal") && IPTAL_EDILEBILIR.includes(st) && (
              <Button variant="outlined" icon="block" onClick={() => setPencere({ tur: "iptal" })}>
                {DUGME_IPTAL}
              </Button>
            )}
          </div>
        </div>
        {st === "IPTAL" && (
          <div className="space-y-1">
            <p role="note" className="text-body-medium text-on-surface">
              {IPTAL_EDILDI_NOTU}
            </p>
            {kurul.cancel_reason && (
              <p className="break-words text-body-small text-on-surface-variant">
                {ALAN_IPTAL_NEDENI}: {kurul.cancel_reason}
              </p>
            )}
          </div>
        )}
        {st === "TUTANAK_TAMAM" && (
          <p role="note" className="text-body-medium text-on-surface-variant">
            {TUTANAK_TAMAM_NOTU}
          </p>
        )}
        {son && <KuralUyarilari satirlar={son.uyarilar} baslik={GECIS_UYARILARI_BASLIGI} />}
        <BilgiSatirlari bilgiler={[...new Set([...(son?.bilgiler ?? []), ...kurul.bilgiler])]} />
        <KuralUyarilari satirlar={kurul.rule_warnings} baslik={KURAL_UYARILARI_BASLIGI} />
        <Stepper items={adimlar} ariaLabel={SIHIRBAZ_ADIMLARI} onSelect={(_, i) => setAdim(i)} />
        <section aria-label={basliklar[gosterilen]} className="space-y-3">
          <h3 className="text-title-small text-on-surface">{basliklar[gosterilen]}</h3>
          {icerikler[gosterilen]}
        </section>
      </Card>

      {dosyaEkiMaddeleri.length > 0 && (
        <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
          <div>
            <h2 className="text-title-medium text-on-surface">{DOSYA_EKLERI_BASLIGI}</h2>
            <p className="text-body-small text-on-surface-variant">{DOSYA_EKLERI_ACIKLAMASI}</p>
          </div>
          {dosyaEkiMaddeleri.map((m) => (
            <EkListesi
              key={m.id}
              ekler={m.ekler}
              baslik={GUNDEM_TURU_TR[m.kind]}
              onEkle={
                ekYazilir(m)
                  ? async (dosya) => {
                      await genelKurulApi.dosyaEki(m.id, dosya, m.kind === "DK_RAPORU");
                      tazele();
                    }
                  : undefined
              }
            />
          ))}
        </Card>
      )}

      <BelgeKartlari
        kurul={kurul}
        adliAcik={yetki.acik("kisisel_veri_ciktisi")}
        evrakKaydiAcik={yetki.acik("evrak_kaydi")}
      />

      {pencere?.tur === "cagri" && (
        <CagriPenceresi kurul={kurul} onKapat={() => setPencere(null)} onKaydedildi={yazildi} />
      )}
      {pencere?.tur === "cagri_yazisi" && (
        <CagriYazisiPenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "toplanti_bilgisi" && (
        <ToplantiBilgisiPenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "gundem_sirasi" && (
        <GundemSirasiPenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {(pencere?.tur === "ilan" || pencere?.tur === "ikinci_ilan" || pencere?.tur === "kanit") && (
        <IlanPenceresi
          kurul={kurul}
          mod={pencere.tur === "ilan" ? "ilan" : pencere.tur === "ikinci_ilan" ? "ikinci" : "kanit"}
          ilan={pencere.tur === "kanit" ? pencere.ilan : undefined}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "toplanti" && (
        <ToplantiPenceresi
          kurul={kurul}
          toplanti={pencere.toplanti}
          onerilen={
            isaretSayisi(pencere.toplanti) > 0
              ? isaretOnerisi(isaretSayisi(pencere.toplanti))
              : undefined
          }
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "isaretler" && (
        <KatilimIsaretleriPenceresi
          kurul={kurul.id}
          ilkToplanti={
            st === "YETER_SAYI_YOK" || kurul.held_at_meeting === "IKINCI" ? "IKINCI" : "BIRINCI"
          }
          onKapat={() => setPencere(null)}
          onKaydedildi={() => yazildi(null)}
        />
      )}
      {pencere?.tur === "duzeltme" && (
        <KatilimDuzeltmePenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "divan" && (
        <DivanPenceresi kurul={kurul} onKapat={() => setPencere(null)} onKaydedildi={yazildi} />
      )}
      {pencere?.tur === "divan_iptal" && (
        <IptalPenceresi
          baslik={DIVAN_IPTAL_BASLIGI}
          metin={DIVAN_IPTAL_METNI}
          yedekHata={DIVAN_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            const sonuc = await genelKurulApi.divanIptal(kurul.id, gerekce);
            snackbar.success(DIVAN_IPTAL_EDILDI);
            yazildi(sonuc);
          }}
        />
      )}
      {pencere?.tur === "sonuc" && (
        <SonucPenceresi
          madde={pencere.madde}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "gundem_ekle" && (
        <GundemEklePenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "gundemden_cikar" && (
        <GundemdenCikarPenceresi
          madde={pencere.madde}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "ibra" && (
        <IbraPenceresi
          kurul={kurul}
          madde={pencere.madde}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "aday" && (
        <AdayPenceresi kurul={kurul} onKapat={() => setPencere(null)} onKaydedildi={yazildi} />
      )}
      {pencere?.tur === "secim" && (
        <SecimPenceresi
          kurul={kurul}
          madde={pencere.madde}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "secim_iptal" && (
        <IptalPenceresi
          baslik={SECIM_IPTAL_BASLIGI}
          metin={SECIM_IPTAL_METNI}
          yedekHata={SECIM_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            const sonuc = await genelKurulApi.secimIptal(pencere.madde.id, gerekce);
            snackbar.success(SECIM_IPTAL_EDILDI);
            yazildi(sonuc);
          }}
        />
      )}
      {pencere?.tur === "tutanak" && (
        <TutanakBilgileriPenceresi
          kurul={kurul}
          onKapat={() => setPencere(null)}
          onKaydedildi={yazildi}
        />
      )}
      {pencere?.tur === "tamamla" && (
        <GerekceliOnayPenceresi
          baslik={TUTANAK_TAMAMLA_BASLIGI}
          metin={TUTANAK_TAMAMLA_METNI}
          dugme={DUGME_TUTANAK_TAMAMLA}
          yedekHata={TUTANAK_TAMAMLANAMADI}
          baglam={`genel_kurul.tutanak_tamamla.${kurul.id}`}
          onKapat={() => setPencere(null)}
          onGonder={async (ek) => {
            const sonuc = await genelKurulApi.tutanagiTamamla(kurul.id, ek);
            snackbar.success(TUTANAK_TAMAMLANDI);
            yazildi(sonuc);
          }}
        />
      )}
      {pencere?.tur === "iptal" && (
        <IptalPenceresi
          baslik={IPTAL_BASLIGI}
          metin={IPTAL_METNI}
          yedekHata={IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            const sonuc = await genelKurulApi.iptalEt(kurul.id, gerekce);
            snackbar.success(IPTAL_EDILDI);
            yazildi(sonuc);
          }}
        />
      )}
    </div>
  );
}
