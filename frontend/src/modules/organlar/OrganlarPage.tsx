// Organlar ekranı (tasarım §5.2.2, §7.2; plan F1c kararları, 5-6. adım notları; ekranı F1c 11. adım).
// Sekmeler: Yönetim Kurulu · Denetleme Kurulu · Alım Komisyonu (`?tab=`). Her rol okur (M2 ve M8 "O");
// yazma denetimleri yeteneğe bağlıdır, rol adıyla dallanılmaz:
//
// * `organ_yazma` — Denetleme Kurulunun öğretmen koltuğuna seçilmiş üye, üyeliğin kişisiz bilgileri,
//   kaydın iptali, alım komisyonu üyesi (program yöneticisi ve yönetim kurulu rolleri);
// * `gorev_bolumu_yazma` — yönetim kurulunun görev bölümü ve yedek çağrısı (yalnız sekreter);
// * `dk_gorev_bolumu_yazma` — Denetleme Kurulunun görev bölümü, denetim planı ve tutanağı (yalnız
//   Denetleme Kurulu; M8 ⁵); `dk_yedek_cagirma` — Denetleme Kurulu yedeğinin çağrısı (program yöneticisi);
// * `uyelik_dusurme` — düşme (program yöneticisi ve sekreter); `gorev_alma_engeli` — engelin yazımı ve
//   dayanağının okunması (program yöneticisi ve yönetim kurulu rolleri; tasarım §4.4.2 ¹¹);
// * `karar_taslagi_uretme` — yönetim kurulu görev bölümü karar taslağı (program yöneticisi ve sekreter);
//   `toplanti_gunu_yazma` — aylık toplantı günü (aynı roller).
//
// Yönetim kurulu ve Denetleme Kurulunun veli üyesi genel kurulda seçilir (genel kurul akışı sonraki
// fazdadır); programdan önce seçilmiş görevdeki kurul geçiş kurulumundadır. Kadro geniş tablo değildir:
// satır, ayrıntısını ve eylemlerini pencerede açar (1366×768'de yatay kaydırma olmasın). Kadro uyarıları
// kaydedilmez, gerekçe istemez; sert engeller bantla, öteki uyarılar ortak "uyarı + gerekçe" bileşeniyle.
// Birlik dönemi yoksa boş durum; yazılamayan dönemde (kapanmış, D7) yazma denetimi çizilmez.

import { useCallback, useEffect, useId, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useTabParam } from "../../hooks/useTabParam";
import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import EmptyState from "../../ui/EmptyState";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import Tabs, { tabPanelProps } from "../../ui/Tabs";
import type { TabItem } from "../../ui/Tabs";
import { AtifliUyarilar } from "../birlik-donemi/BirlikDonemiPage";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { DONEM_YOK_BASLIGI } from "../birlik-donemi/metinler";
import EvrakKarti from "../evrak/EvrakKarti";
import { E01_ADI, E02_ADI, TASLAK_ACIKLAMASI, TUTANAK_ACIKLAMASI } from "../evrak/metinler";
import IptalPenceresi from "../gecis-kurulumu/IptalPenceresi";
import {
  GOREV_TR,
  KAYIT_IPTAL_EDILDI,
  KAYIT_IPTAL_EDILEMEDI,
  koltukMetni,
} from "../gecis-kurulumu/metinler";
import type { YetenekAdi } from "../oturum/api";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import { organlarApi } from "./api";
import type { Kadro, KadroOrgani, Uyelik } from "./api";
import { DonemBasligi, donemYazilir, gecisAcik, useDonemSecimi } from "./donem";
import { DkGorevBolumuPenceresi, YkGorevBolumuPenceresi } from "./GorevBolumuPenceresi";
import {
  ALIM_ACIKLAMASI,
  ASIL_YOK,
  BOLUM_ASILLAR,
  BOLUM_KOMISYON,
  BOLUM_OTEKI,
  BOLUM_YEDEKLER,
  CIP_DEVRALINAN,
  CIP_ENGEL,
  CIP_ERTELENDI,
  CIP_UZMANLIK,
  DK_SECIM_NOTU,
  DONEM_YOK_ORGAN_ACIKLAMASI,
  DUGME_BIRLIK_DONEMINE_GIT,
  DUGME_DK_GOREV_BOLUMU,
  DUGME_GOREV_BOLUMU,
  DUGME_KOMISYON_UYESI_EKLE,
  DUGME_OGRETMEN_EKLE,
  DURUM_TR,
  KADRO_OKUNAMADI,
  KADRO_UYARILARI_BASLIGI,
  KOMISYON_UYESI_YOK,
  ONERILER_BASLIGI,
  ORGANLAR_ACIKLAMASI,
  ORGANLAR_BASLIGI,
  OTEKI_ACIKLAMASI,
  SEKMELER_ETIKETI,
  SEKME_ALIM,
  SEKME_DK,
  SEKME_YK,
  UYELIK_IPTAL_BASLIGI,
  UYELIK_IPTAL_METNI,
  YEDEK_YOK,
  YK_SECIM_NOTU,
  acikUyariMetni,
  kadroOzeti,
  komisyonOzeti,
  satirEtiketi,
  yedektenCagrildiMetni,
} from "./metinler";
import ToplantiGunuKarti from "./ToplantiGunuKarti";
import { KomisyonUyesiPenceresi, OgretmenUyePenceresi } from "./UyeEklePenceresi";
import { BilgiPenceresi, DusmePenceresi, EngelPenceresi, YedekPenceresi } from "./UyelikEylemleri";
import UyelikPenceresi from "./UyelikPenceresi";
import type { UyelikEylemi } from "./UyelikPenceresi";

// TABS[0] varsayılan sekmedir (useTabParam fallback) — başa yeni anahtar EKLEME.
const TABS = ["yk", "dk", "alim"] as const;
type Sekme = (typeof TABS)[number];

export const TAB_ITEMS: TabItem[] = [
  { key: "yk", label: SEKME_YK, icon: "groups" },
  { key: "dk", label: SEKME_DK, icon: "fact_check" },
  { key: "alim", label: SEKME_ALIM, icon: "shopping_cart" },
];

export default function OrganlarPage() {
  const yetki = useYetki();
  const secim = useDonemSecimi();
  const [tab, setTab] = useTabParam<Sekme>("tab", TABS, "yk");
  const { secili } = secim;
  // Salt okur notu (M2 "O"): açık sekmenin hiçbir yazma denetimini açamayan rol. Sekmeye göre
  // hesaplanır; ör. Denetleme Kurulu kendi sekmesinde yazar, yönetim kurulu ve alım komisyonunda okur.
  const acik = (...adlar: YetenekAdi[]) => adlar.some((a) => yetki.acik(a));
  const hicYazamaz =
    yetki.durum === "hazir" &&
    !(tab === "alim"
      ? acik("organ_yazma")
      : tab === "yk"
        ? acik(
            "organ_yazma",
            "gorev_bolumu_yazma",
            "uyelik_dusurme",
            "gorev_alma_engeli",
            "toplanti_gunu_yazma",
            "karar_taslagi_uretme",
          )
        : acik(
            "organ_yazma",
            "dk_gorev_bolumu_yazma",
            "dk_yedek_cagirma",
            "uyelik_dusurme",
            "gorev_alma_engeli",
          ));

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{ORGANLAR_BASLIGI}</h1>
          <p className="od-page-description">{ORGANLAR_ACIKLAMASI}</p>
        </div>
      </div>

      {hicYazamaz && <SaltOkurNotu />}
      {secim.hata && <ErrorBand hata={secim.hata} />}

      {secim.yukleniyor ? (
        <SkeletonList rows={5} />
      ) : secili === undefined ? (
        !secim.hata && (
          <EmptyState
            icon="groups"
            title={DONEM_YOK_BASLIGI}
            description={yetki.acik("birlik_donemi_yazma") ? DONEM_YOK_ORGAN_ACIKLAMASI : undefined}
            action={
              yetki.acik("birlik_donemi_yazma") ? (
                <Link
                  to="/birlik-donemi"
                  className="inline-flex text-label-large text-primary underline underline-offset-2"
                >
                  {DUGME_BIRLIK_DONEMINE_GIT}
                </Link>
              ) : undefined
            }
          />
        )
      ) : (
        <>
          <DonemBasligi secim={secim} />
          <Tabs
            items={TAB_ITEMS}
            active={tab}
            onChange={(key) => setTab(key as Sekme)}
            ariaLabel={SEKMELER_ETIKETI}
            idBase="organlar"
          />
          <div {...tabPanelProps("organlar", tab)} className="space-y-[var(--od-page-gap)]">
            {tab === "alim" ? (
              <KomisyonSekmesi key={`alim-${secili.id}`} donem={secili} />
            ) : (
              <KurulSekmesi
                key={`${tab}-${secili.id}`}
                donem={secili}
                organ={tab === "yk" ? "YK" : "DK"}
                onDonemGuncellendi={secim.guncelle}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ortak parçalar
// ---------------------------------------------------------------------------
function Bolum({
  baslik,
  aciklama,
  children,
}: {
  baslik: string;
  aciklama?: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-2">
      <div className="space-y-0.5">
        <h2 className="text-title-medium text-on-surface">{baslik}</h2>
        {aciklama && <p className="text-body-small text-on-surface-variant">{aciklama}</p>}
      </div>
      {children}
    </section>
  );
}

function Cip({ children, ton = "notr" }: { children: ReactNode; ton?: "notr" | "uyari" }) {
  const renk =
    ton === "uyari"
      ? "bg-tertiary-container text-on-tertiary-container"
      : "bg-surface-container-highest text-on-surface-variant";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-label-medium ${renk}`}>
      {children}
    </span>
  );
}

/** Kadro satırı: ad, görev ya da koltuk ve işaretler; tıklanınca ayrıntı penceresi açılır. Erişilebilir
 * adı "Ad Soyad kaydını aç" (ailenin satır deseni); özet ve işaretler açıklama olarak okunur. */
function UyeSatiri({
  uyelik,
  ozet,
  uyariSayisi,
  onAc,
}: {
  uyelik: Uyelik;
  /** Görev, koltuk ya da durum (adın yanında). */
  ozet: string;
  uyariSayisi: number;
  onAc: () => void;
}) {
  const aciklamaId = useId();
  return (
    <li>
      <button
        type="button"
        onClick={onAc}
        aria-label={satirEtiketi(uyelik.person_name ?? "—")}
        aria-describedby={`${aciklamaId}-ozet ${aciklamaId}-isaret`}
        className="flex w-full min-w-0 flex-wrap items-center gap-x-3 gap-y-1 rounded-shape-sm px-3 py-2.5 text-left transition-colors hover:bg-on-surface/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <span className="min-w-0 flex-1 basis-56 break-words text-body-large text-on-surface">
          {uyelik.person_name ?? "—"}
        </span>
        <span id={`${aciklamaId}-ozet`} className="text-body-medium text-on-surface-variant">
          {ozet}
        </span>
        <span id={`${aciklamaId}-isaret`} className="flex flex-wrap gap-1.5">
          {uyelik.promoted_on && <Cip>{yedektenCagrildiMetni(formatDate(uyelik.promoted_on))}</Cip>}
          {uyelik.source === "DEVRALINAN" && <Cip>{CIP_DEVRALINAN}</Cip>}
          {uyelik.retained_until_assembly && <Cip>{CIP_ERTELENDI}</Cip>}
          {uyelik.expertise_required && <Cip>{CIP_UZMANLIK}</Cip>}
          {uyelik.eligibility_bar === "VAR" && <Cip ton="uyari">{CIP_ENGEL}</Cip>}
          {uyariSayisi > 0 && <Cip ton="uyari">{acikUyariMetni(uyariSayisi)}</Cip>}
        </span>
      </button>
    </li>
  );
}

function UyeListesi({ children, bos }: { children: ReactNode[]; bos: string }) {
  if (children.length === 0) {
    return <p className="text-body-medium text-on-surface-variant">{bos}</p>;
  }
  return (
    <Card elevation={0} className="p-1">
      <ul className="divide-y divide-outline-variant/60">{children}</ul>
    </Card>
  );
}

type Pencere =
  | { tur: "uye"; uyelik: Uyelik }
  | { tur: UyelikEylemi; uyelik: Uyelik }
  | { tur: "gorev" }
  | { tur: "ekle" }
  | null;

function useKadro(donem: number, organ: KadroOrgani) {
  const [kadro, setKadro] = useState<Kadro | null>(null);
  const [tum, setTum] = useState<Uyelik[]>([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [yenile, setYenile] = useState(0);
  const tazele = useCallback(() => setYenile((k) => k + 1), []);

  useEffect(() => {
    let iptal = false;
    setYukleniyor(true);
    Promise.all([organlarApi.kadro(donem, organ), organlarApi.uyelikler(donem, organ)])
      .then(([okunan, liste]) => {
        if (iptal) return;
        setKadro(okunan);
        setTum(liste);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, KADRO_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setYukleniyor(false);
      });
    return () => {
      iptal = true;
    };
  }, [donem, organ, yenile]);

  return { kadro, tum, yukleniyor, hata, tazele };
}

/** Kaydın durumuna ve yeteneklere göre pencerenin eylemleri. */
function uyelikEylemleri(
  uyelik: Uyelik,
  organ: KadroOrgani,
  yetkiler: Record<"organ" | "yedek" | "dusme" | "engel" | "gecis", boolean>,
): UyelikEylemi[] {
  const sonuc: UyelikEylemi[] = [];
  const acik = uyelik.status === "ADAY" || uyelik.status === "SECILDI";
  const bekleyenYedek =
    uyelik.status === "SECILDI" && uyelik.seat_type === "YEDEK" && uyelik.promoted_on === null;
  if (acik && organ !== "ALIM_KOMISYONU" && yetkiler.engel) sonuc.push("engel");
  if (acik && organ !== "ALIM_KOMISYONU" && yetkiler.organ) sonuc.push("bilgi");
  if (bekleyenYedek && yetkiler.yedek) sonuc.push("yedek");
  if (uyelik.status === "SECILDI" && organ !== "ALIM_KOMISYONU" && yetkiler.dusme) {
    sonuc.push("dusme");
  }
  // Devralınan kaydın iptali geçiş kaydıdır: yalnız program yöneticisi ve yalnız geçiş açıkken ("Geçiş
  // kurulumu tamamlandı" işaretinden sonra sunucu 409 `gecis_kapali` verir; sunucu da denetler).
  if (acik && yetkiler.organ && (uyelik.source !== "DEVRALINAN" || yetkiler.gecis)) {
    sonuc.push("iptal");
  }
  return sonuc;
}

function satirOzeti(uyelik: Uyelik, organ: KadroOrgani): string {
  if (organ === "ALIM_KOMISYONU") return DURUM_TR[uyelik.status];
  if (uyelik.status !== "SECILDI") return DURUM_TR[uyelik.status];
  if (uyelik.seat_type === "YEDEK" && uyelik.promoted_on === null) {
    return koltukMetni(uyelik.seat_type, uyelik.seat_order);
  }
  return GOREV_TR[uyelik.role];
}

// ---------------------------------------------------------------------------
// Yönetim kurulu ve Denetleme Kurulu
// ---------------------------------------------------------------------------
function KurulSekmesi({
  donem,
  organ,
  onDonemGuncellendi,
}: {
  donem: BirlikDonemi;
  organ: "YK" | "DK";
  /** Toplantı günü kaydından sonra sunucunun döndürdüğü dönem kaydı (dönem seçimine yazılır). */
  onDonemGuncellendi: (donem: BirlikDonemi) => void;
}) {
  const yetki = useYetki();
  const snackbar = useSnackbar();
  const { kadro, tum, yukleniyor, hata, tazele } = useKadro(donem.id, organ);
  const [pencere, setPencere] = useState<Pencere>(null);
  const yazilir = donemYazilir(donem);
  const yk = organ === "YK";
  const yetkiler = {
    organ: yazilir && yetki.acik("organ_yazma"),
    yedek: yazilir && yetki.acik(yk ? "gorev_bolumu_yazma" : "dk_yedek_cagirma"),
    dusme: yazilir && yetki.acik("uyelik_dusurme"),
    engel: yazilir && yetki.acik("gorev_alma_engeli"),
    gecis: gecisAcik(donem) && yetki.acik("birlik_donemi_yazma"),
  };
  const gorevYazar = yazilir && yetki.acik(yk ? "gorev_bolumu_yazma" : "dk_gorev_bolumu_yazma");
  const uretir = yazilir && yetki.acik(yk ? "karar_taslagi_uretme" : "dk_gorev_bolumu_yazma");

  const uyariSayilari = useMemo(() => {
    const sayilar = new Map<number, number>();
    for (const s of kadro?.uyum_satirlari ?? [])
      sayilar.set(s.uyelik, (sayilar.get(s.uyelik) ?? 0) + 1);
    return sayilar;
  }, [kadro]);
  const oteki = tum.filter((u) => u.status !== "SECILDI");

  const kaydedildi = () => {
    setPencere(null);
    tazele();
  };
  const satir = (u: Uyelik) => (
    <UyeSatiri
      key={u.id}
      uyelik={u}
      ozet={satirOzeti(u, organ)}
      uyariSayisi={uyariSayilari.get(u.id) ?? 0}
      onAc={() => setPencere({ tur: "uye", uyelik: u })}
    />
  );

  return (
    <>
      {hata && <ErrorBand hata={hata} />}
      {yukleniyor && kadro === null ? (
        <SkeletonList rows={5} />
      ) : (
        kadro !== null && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-body-large text-on-surface">
                {kadroOzeti(kadro.kadro.asil, kadro.kadro.yedek)}
              </p>
              <div className="flex flex-wrap gap-2">
                {!yk && yetkiler.organ && (
                  <Button
                    variant="tonal"
                    icon="person_add"
                    onClick={() => setPencere({ tur: "ekle" })}
                  >
                    {DUGME_OGRETMEN_EKLE}
                  </Button>
                )}
                {gorevYazar && (
                  <Button icon="assignment_ind" onClick={() => setPencere({ tur: "gorev" })}>
                    {yk ? DUGME_GOREV_BOLUMU : DUGME_DK_GOREV_BOLUMU}
                  </Button>
                )}
              </div>
            </div>
            <p className="text-body-small text-on-surface-variant">
              {yk ? YK_SECIM_NOTU : DK_SECIM_NOTU}
            </p>
            <AtifliUyarilar uyarilar={kadro.kadro_uyarilari} baslik={KADRO_UYARILARI_BASLIGI} />
            {kadro.oneriler.length > 0 && (
              <Bolum baslik={ONERILER_BASLIGI}>
                <ul className="list-disc space-y-1 pl-5 text-body-medium text-on-surface">
                  {kadro.oneriler.map((o) => {
                    const uye = kadro.gorevdeki_asillar.find((u) => u.id === o.uyelik);
                    return (
                      <li key={`${o.uyelik}-${o.tur}-${o.metin}`} className="break-words">
                        {uye?.person_name ? `${uye.person_name}: ${o.metin}` : o.metin}
                      </li>
                    );
                  })}
                </ul>
              </Bolum>
            )}
            <Bolum baslik={BOLUM_ASILLAR}>
              <UyeListesi bos={ASIL_YOK}>{kadro.gorevdeki_asillar.map(satir)}</UyeListesi>
            </Bolum>
            <Bolum baslik={BOLUM_YEDEKLER}>
              <UyeListesi bos={YEDEK_YOK}>{kadro.bekleyen_yedekler.map(satir)}</UyeListesi>
            </Bolum>
            {oteki.length > 0 && (
              <Bolum baslik={BOLUM_OTEKI} aciklama={OTEKI_ACIKLAMASI}>
                <UyeListesi bos="">{oteki.map(satir)}</UyeListesi>
              </Bolum>
            )}
            {yk && (
              <ToplantiGunuKarti
                key={`toplanti-${donem.id}`}
                donem={donem.id}
                deger={donem.yk_meeting_day_rule ?? ""}
                yazabilir={yazilir && yetki.acik("toplanti_gunu_yazma")}
                onKaydedildi={onDonemGuncellendi}
              />
            )}
            <EvrakKarti
              donem={donem.id}
              kod={yk ? "E01" : "E02"}
              baslik={yk ? E01_ADI : E02_ADI}
              aciklama={yk ? TASLAK_ACIKLAMASI : TUTANAK_ACIKLAMASI}
              uretebilir={uretir}
            />
          </>
        )
      )}

      {pencere?.tur === "uye" && kadro !== null && (
        <UyelikPenceresi
          uyelik={pencere.uyelik}
          organ={organ}
          sayac={kadro.secilme_sayaclari.find((s) => s.uyelik === pencere.uyelik.id)}
          uyumSatirlari={kadro.uyum_satirlari.filter((s) => s.uyelik === pencere.uyelik.id)}
          oneriler={kadro.oneriler.filter((o) => o.uyelik === pencere.uyelik.id)}
          eylemler={uyelikEylemleri(pencere.uyelik, organ, yetkiler)}
          dayanakOkunur={yetki.acik("gorev_alma_engeli")}
          onEylem={(eylem) => setPencere({ tur: eylem, uyelik: pencere.uyelik })}
          onKapat={() => setPencere(null)}
        />
      )}
      {pencere?.tur === "engel" && (
        <EngelPenceresi
          uyelik={pencere.uyelik}
          onKapat={() => setPencere(null)}
          onKaydedildi={kaydedildi}
        />
      )}
      {pencere?.tur === "bilgi" && (
        <BilgiPenceresi
          uyelik={pencere.uyelik}
          onKapat={() => setPencere(null)}
          onKaydedildi={kaydedildi}
        />
      )}
      {pencere?.tur === "yedek" && (
        <YedekPenceresi
          uyelik={pencere.uyelik}
          organ={organ}
          onKapat={() => setPencere(null)}
          onKaydedildi={kaydedildi}
        />
      )}
      {pencere?.tur === "dusme" && (
        <DusmePenceresi
          uyelik={pencere.uyelik}
          onerilenTur={
            kadro?.oneriler.find((o) => o.uyelik === pencere.uyelik.id && o.tur === "DUSURME")
              ?.drop_kind
          }
          onerilenGun={
            kadro?.oneriler.find((o) => o.uyelik === pencere.uyelik.id && o.tur === "DUSURME")?.gun
          }
          onKapat={() => setPencere(null)}
          onKaydedildi={kaydedildi}
        />
      )}
      {pencere?.tur === "iptal" && (
        <IptalPenceresi
          baslik={UYELIK_IPTAL_BASLIGI}
          metin={UYELIK_IPTAL_METNI}
          yedekHata={KAYIT_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            await organlarApi.iptalEt(pencere.uyelik.id, gerekce);
            snackbar.success(KAYIT_IPTAL_EDILDI);
            kaydedildi();
          }}
        />
      )}
      {pencere?.tur === "gorev" &&
        kadro !== null &&
        (yk ? (
          <YkGorevBolumuPenceresi
            donem={donem.id}
            asillar={kadro.gorevdeki_asillar}
            onKapat={() => setPencere(null)}
            onKaydedildi={kaydedildi}
          />
        ) : (
          <DkGorevBolumuPenceresi
            donem={donem.id}
            asillar={kadro.gorevdeki_asillar}
            onKapat={() => setPencere(null)}
            onKaydedildi={kaydedildi}
          />
        ))}
      {pencere?.tur === "ekle" && (
        <OgretmenUyePenceresi
          donem={donem.id}
          onKapat={() => setPencere(null)}
          onEklendi={kaydedildi}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Alım komisyonu
// ---------------------------------------------------------------------------
function KomisyonSekmesi({ donem }: { donem: BirlikDonemi }) {
  const yetki = useYetki();
  const snackbar = useSnackbar();
  const { kadro, tum, yukleniyor, hata, tazele } = useKadro(donem.id, "ALIM_KOMISYONU");
  const [pencere, setPencere] = useState<Pencere>(null);
  const yazilir = donemYazilir(donem);
  const yetkiler = {
    organ: yazilir && yetki.acik("organ_yazma"),
    yedek: false,
    dusme: false,
    engel: false,
    gecis: gecisAcik(donem) && yetki.acik("birlik_donemi_yazma"),
  };
  const oteki = tum.filter((u) => u.status !== "SECILDI");
  const kaydedildi = () => {
    setPencere(null);
    tazele();
  };
  const satir = (u: Uyelik) => (
    <UyeSatiri
      key={u.id}
      uyelik={u}
      ozet={satirOzeti(u, "ALIM_KOMISYONU")}
      uyariSayisi={0}
      onAc={() => setPencere({ tur: "uye", uyelik: u })}
    />
  );

  return (
    <>
      {hata && <ErrorBand hata={hata} />}
      {yukleniyor && kadro === null ? (
        <SkeletonList rows={3} />
      ) : (
        kadro !== null && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-body-large text-on-surface">{komisyonOzeti(kadro.kadro.asil)}</p>
              {yetkiler.organ && (
                <Button
                  variant="tonal"
                  icon="person_add"
                  onClick={() => setPencere({ tur: "ekle" })}
                >
                  {DUGME_KOMISYON_UYESI_EKLE}
                </Button>
              )}
            </div>
            <p className="text-body-small text-on-surface-variant">{ALIM_ACIKLAMASI}</p>
            <AtifliUyarilar uyarilar={kadro.kadro_uyarilari} baslik={KADRO_UYARILARI_BASLIGI} />
            <Bolum baslik={BOLUM_KOMISYON}>
              <UyeListesi bos={KOMISYON_UYESI_YOK}>{kadro.gorevdeki_asillar.map(satir)}</UyeListesi>
            </Bolum>
            {oteki.length > 0 && (
              <Bolum baslik={BOLUM_OTEKI} aciklama={OTEKI_ACIKLAMASI}>
                <UyeListesi bos="">{oteki.map(satir)}</UyeListesi>
              </Bolum>
            )}
          </>
        )
      )}

      {pencere?.tur === "uye" && (
        <UyelikPenceresi
          uyelik={pencere.uyelik}
          organ="ALIM_KOMISYONU"
          sayac={undefined}
          uyumSatirlari={[]}
          oneriler={[]}
          eylemler={uyelikEylemleri(pencere.uyelik, "ALIM_KOMISYONU", yetkiler)}
          dayanakOkunur={false}
          onEylem={(eylem) => setPencere({ tur: eylem, uyelik: pencere.uyelik })}
          onKapat={() => setPencere(null)}
        />
      )}
      {pencere?.tur === "iptal" && (
        <IptalPenceresi
          baslik={UYELIK_IPTAL_BASLIGI}
          metin={UYELIK_IPTAL_METNI}
          yedekHata={KAYIT_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            await organlarApi.iptalEt(pencere.uyelik.id, gerekce);
            snackbar.success(KAYIT_IPTAL_EDILDI);
            kaydedildi();
          }}
        />
      )}
      {pencere?.tur === "ekle" && (
        <KomisyonUyesiPenceresi
          donem={donem.id}
          onKapat={() => setPencere(null)}
          onEklendi={kaydedildi}
        />
      )}
    </>
  );
}
