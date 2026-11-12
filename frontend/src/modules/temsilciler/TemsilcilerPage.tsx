// Temsilciler ekranı (tasarım §5.2.2 "Temsil türleri", §6.4.4; plan F1c kararları "Temsilciler ayrı
// ekran", 6. adım notları; ekranı F1c 11. adım). Her rol okur (M2 "O"); temsilci kaydı `temsilci_yazma`,
// kaydın iptali `organ_yazma` (genel üyelik iptal ucu), çizelgenin belgesi (E03) `karar_taslagi_uretme`
// yeteneğindedir (program yöneticisi ve sekreter).
//
// Çizelge sunucunundur (E03'ün tek kaynağı): satırlar kademe ve kantin koşulundan, kampüs satırı okul
// kartından gelir; satırın uyarısı ve eksikliği kural paketinin atıflı iletisidir (kaydedilmez, gerekçe
// istemez). Kantin denetim komisyonu satırı kurallıdır (Genelge 2020/8 A-1); rehberlik ve psikolojik
// danışma hizmetleri yürütme komisyonunun notu kuralın yorumudur. Karar bağı yalnız kabul edilmiş ya da
// deftere işlenmiş yönetim kurulu kararıdır (taslak bağlanamaz); kayıt yazımda uyarı + gerekçe ister,
// sert engeller (pasif kişi, aynı kayıt) bantla gösterilir.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Dialog from "../../ui/Dialog";
import EmptyState from "../../ui/EmptyState";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import type { BirlikDonemi } from "../birlik-donemi/api";
import { DONEM_YOK_BASLIGI } from "../birlik-donemi/metinler";
import EvrakKarti from "../evrak/EvrakKarti";
import { E03_ADI, TASLAK_ACIKLAMASI } from "../evrak/metinler";
import IptalPenceresi from "../gecis-kurulumu/IptalPenceresi";
import { TEMSIL_TURU_TR } from "../gecis-kurulumu/api";
import type { KoltukTuru, TemsilTuru } from "../gecis-kurulumu/api";
import {
  ALAN_KOLTUK,
  ALAN_TEMSIL,
  KAYIT_IPTAL_EDILDI,
  KAYIT_IPTAL_EDILEMEDI,
  KISI_SECIN,
  KOLTUK_ASIL,
  KOLTUK_YEDEK,
  PROGRAMA_BASLAMA_YARDIMI,
  TEMSIL_SECIN,
  koltukMetni,
} from "../gecis-kurulumu/metinler";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { organlarApi } from "../organlar/api";
import type { Uyelik } from "../organlar/api";
import { DonemBasligi, donemYazilir, gecisAcik, useDonemSecimi } from "../organlar/donem";
import {
  ALAN_KARAR_BAGLANMASIN,
  DONEM_YOK_ORGAN_ACIKLAMASI,
  DUGME_BIRLIK_DONEMINE_GIT,
  DUGME_KAYDI_IPTAL,
  KARAR_BAGI_YARDIMI,
  SECIM_KANALI_TR,
} from "../organlar/metinler";
import {
  KisiSecimi,
  PencereHatasi,
  kararSecenekleri,
  useBaglanabilirKararlar,
  useEtkinKisiler,
} from "../organlar/ortak";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import { UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { Dayanak } from "../uyum/UyariGerekce";
import { atifAyir } from "../uyum/hatalar";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { temsilcilerApi } from "./api";
import type { CizelgeSatiri } from "./api";
import {
  ALAN_GOREVLENDIRME_GUNU,
  ALAN_KARAR,
  CIP_KARAR_BAGLI,
  CIZELGE_BASLIGI,
  CIZELGE_BOS,
  CIZELGE_OKUNAMADI,
  DUGME_TEMSILCI_EKLE,
  DURUM_EKSIK,
  DURUM_UYARI,
  TEMSILCILER_ACIKLAMASI,
  TEMSILCILER_BASLIGI,
  TEMSILCI_EKLENDI,
  TEMSILCI_EKLENEMEDI,
  TEMSILCI_GIRILMEDI,
  TEMSILCI_IPTAL_BASLIGI,
  TEMSILCI_IPTAL_METNI,
  TEMSILCI_PENCERESI_BASLIGI,
  temsilciIptalEtiketi,
  temsilciMetni,
} from "./metinler";

const TEMSIL_SECENEKLERI = (Object.entries(TEMSIL_TURU_TR) as [TemsilTuru, string][]).map(
  ([value, label]) => ({ value, label }),
);

export default function TemsilcilerPage() {
  const yetki = useYetki();
  const secim = useDonemSecimi();
  const { secili } = secim;
  const hicYazamaz =
    yetki.durum === "hazir" && !yetki.acik("temsilci_yazma") && !yetki.acik("organ_yazma");

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{TEMSILCILER_BASLIGI}</h1>
          <p className="od-page-description">{TEMSILCILER_ACIKLAMASI}</p>
        </div>
      </div>

      {hicYazamaz && <SaltOkurNotu />}
      {secim.hata && <ErrorBand hata={secim.hata} />}

      {secim.yukleniyor ? (
        <SkeletonList rows={5} />
      ) : secili === undefined ? (
        !secim.hata && (
          <EmptyState
            icon="diversity_3"
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
          <Cizelge key={secili.id} donem={secili} />
        </>
      )}
    </div>
  );
}

function SatirDurumu({ satir }: { satir: CizelgeSatiri }) {
  if (!satir.metin) return null;
  const { govde, atif } = atifAyir(satir.metin);
  const eksik = satir.durum === "eksik";
  return (
    <div className="flex items-start gap-2">
      <span
        className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-label-medium ${
          eksik
            ? "bg-secondary-container text-on-secondary-container"
            : "bg-tertiary-container text-on-tertiary-container"
        }`}
      >
        {eksik ? DURUM_EKSIK : DURUM_UYARI}
      </span>
      <span className="min-w-0 space-y-0.5">
        <span className="block break-words text-body-medium text-on-surface">{govde}</span>
        <Dayanak atif={atif} />
      </span>
    </div>
  );
}

type Pencere = { tur: "ekle"; temsil?: TemsilTuru } | { tur: "iptal"; uyelik: Uyelik } | null;

function Cizelge({ donem }: { donem: BirlikDonemi }) {
  const yetki = useYetki();
  const snackbar = useSnackbar();
  const [satirlar, setSatirlar] = useState<CizelgeSatiri[] | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [pencere, setPencere] = useState<Pencere>(null);
  const [yenile, setYenile] = useState(0);
  const tazele = useCallback(() => setYenile((k) => k + 1), []);
  const yazilir = donemYazilir(donem);
  const ekleyebilir = yazilir && yetki.acik("temsilci_yazma");
  const iptalEdebilir = yazilir && yetki.acik("organ_yazma");
  // Devralınan kaydın iptali geçiş kaydıdır: program yöneticisi, geçiş açıkken (sunucu da denetler).
  const devralinanIptal = gecisAcik(donem) && yetki.acik("birlik_donemi_yazma");

  useEffect(() => {
    let iptal = false;
    temsilcilerApi
      .cizelge(donem.id)
      .then((liste) => {
        if (iptal) return;
        setSatirlar(liste);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, CIZELGE_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [donem.id, yenile]);

  const kaydedildi = () => {
    setPencere(null);
    tazele();
  };

  return (
    <>
      {hata && <ErrorBand hata={hata} />}
      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-title-medium text-on-surface">{CIZELGE_BASLIGI}</h2>
          {ekleyebilir && (
            <Button icon="person_add" onClick={() => setPencere({ tur: "ekle" })}>
              {DUGME_TEMSILCI_EKLE}
            </Button>
          )}
        </div>
        {satirlar === null ? (
          !hata && <SkeletonList rows={5} />
        ) : satirlar.length === 0 ? (
          <p className="text-body-medium text-on-surface-variant">{CIZELGE_BOS}</p>
        ) : (
          <ul className="space-y-3">
            {satirlar.map((satir) => (
              <li key={satir.representation}>
                <Card elevation={0} className="space-y-2 p-[var(--od-panel-padding)]">
                  <h3 className="break-words text-title-small text-on-surface">{satir.ad}</h3>
                  <SatirDurumu satir={satir} />
                  {satir.notlar.map((not) => (
                    <p key={not} className="break-words text-body-small text-on-surface-variant">
                      {not}
                    </p>
                  ))}
                  {satir.uyeler.length === 0 ? (
                    <p className="text-body-medium text-on-surface-variant">{TEMSILCI_GIRILMEDI}</p>
                  ) : (
                    <ul className="divide-y divide-outline-variant/60">
                      {satir.uyeler.map((u) => (
                        <li
                          key={u.id}
                          className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-2"
                        >
                          <span className="min-w-0 flex-1 basis-56 break-words text-body-medium text-on-surface">
                            {temsilciMetni(
                              u.person_name ?? "—",
                              koltukMetni(u.seat_type, u.seat_order),
                            )}
                          </span>
                          <span className="flex flex-wrap items-center gap-1.5">
                            {u.elected_by === "KENDILIGINDEN" && (
                              <span className="inline-flex rounded-full bg-surface-container-highest px-2 py-0.5 text-label-medium text-on-surface-variant">
                                {SECIM_KANALI_TR.KENDILIGINDEN}
                              </span>
                            )}
                            {u.representative_decision !== null && (
                              <span className="inline-flex rounded-full bg-surface-container-highest px-2 py-0.5 text-label-medium text-on-surface-variant">
                                {CIP_KARAR_BAGLI}
                              </span>
                            )}
                            {iptalEdebilir && (u.source !== "DEVRALINAN" || devralinanIptal) && (
                              <Button
                                variant="text"
                                icon="block"
                                className="whitespace-nowrap"
                                aria-label={temsilciIptalEtiketi(satir.ad, u.person_name)}
                                onClick={() => setPencere({ tur: "iptal", uyelik: u })}
                              >
                                {DUGME_KAYDI_IPTAL}
                              </Button>
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {ekleyebilir && (
                    <div className="flex justify-end">
                      <Button
                        variant="text"
                        icon="add"
                        aria-label={`${satir.ad}: ${DUGME_TEMSILCI_EKLE}`}
                        onClick={() => setPencere({ tur: "ekle", temsil: satir.representation })}
                      >
                        {DUGME_TEMSILCI_EKLE}
                      </Button>
                    </div>
                  )}
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <EvrakKarti
        donem={donem.id}
        kod="E03"
        baslik={E03_ADI}
        aciklama={TASLAK_ACIKLAMASI}
        uretebilir={yazilir && yetki.acik("karar_taslagi_uretme")}
      />

      {pencere?.tur === "ekle" && (
        <TemsilciPenceresi
          donem={donem.id}
          temsil={pencere.temsil}
          onKapat={() => setPencere(null)}
          onEklendi={kaydedildi}
        />
      )}
      {pencere?.tur === "iptal" && (
        <IptalPenceresi
          baslik={TEMSILCI_IPTAL_BASLIGI}
          metin={TEMSILCI_IPTAL_METNI}
          yedekHata={KAYIT_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            await organlarApi.iptalEt(pencere.uyelik.id, gerekce);
            snackbar.success(KAYIT_IPTAL_EDILDI);
            kaydedildi();
          }}
        />
      )}
    </>
  );
}

function TemsilciPenceresi({
  donem,
  temsil: ilkTemsil,
  onKapat,
  onEklendi,
}: {
  donem: number;
  temsil?: TemsilTuru;
  onKapat: () => void;
  onEklendi: () => void;
}) {
  const snackbar = useSnackbar();
  const kisiler = useEtkinKisiler();
  const kararlar = useBaglanabilirKararlar(donem);
  const [kisi, setKisi] = useState<BirlikKisisi | null>(null);
  const [temsil, setTemsil] = useState<TemsilTuru | "">(ilkTemsil ?? "");
  const [koltuk, setKoltuk] = useState<KoltukTuru>("ASIL");
  const [gun, setGun] = useState("");
  const [karar, setKarar] = useState("");
  const [alanHatalari, setAlanHatalari] = useState<{ kisi?: string; temsil?: string }>({});
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const ug = useUyariGerekce("temsilciler.temsilci");

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    setHata(null);
    const hatalar: { kisi?: string; temsil?: string } = {};
    if (kisi === null) hatalar.kisi = KISI_SECIN;
    if (!temsil) hatalar.temsil = TEMSIL_SECIN;
    setAlanHatalari(hatalar);
    if (kisi === null || !temsil || !ug.hazir()) return;
    setBusy(true);
    try {
      await temsilcilerApi.ekle({
        term: donem,
        person: kisi.id,
        representation: temsil,
        seat_type: koltuk,
        start_date: gun || null,
        representative_decision: karar ? Number(karar) : null,
        ...ug.ek(),
      });
      ug.sifirla();
      snackbar.success(TEMSILCI_EKLENDI);
      onEklendi();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, TEMSILCI_EKLENEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      wide
      onClose={vazgec}
      title={TEMSILCI_PENCERESI_BASLIGI}
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
        <PencereHatasi hata={hata} />
        <UyariGerekceAlani durum={ug} />
        <Select
          label={ALAN_TEMSIL}
          required
          placeholder="Seçin"
          value={temsil}
          onChange={(e) => {
            setTemsil(e.target.value as TemsilTuru);
            setAlanHatalari((h) => ({ ...h, temsil: undefined }));
          }}
          options={TEMSIL_SECENEKLERI}
          error={alanHatalari.temsil}
        />
        <KisiSecimi
          kisiler={kisiler}
          secili={kisi}
          onSecim={(k) => {
            setKisi(k);
            setAlanHatalari((h) => ({ ...h, kisi: undefined }));
          }}
          hata={alanHatalari.kisi}
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
          <TextField
            label={ALAN_GOREVLENDIRME_GUNU}
            type="date"
            value={gun}
            onChange={(e) => setGun(e.target.value)}
            helperText={PROGRAMA_BASLAMA_YARDIMI}
          />
        </div>
        <Select
          label={ALAN_KARAR}
          value={karar}
          onChange={(e) => setKarar(e.target.value)}
          options={[{ value: "", label: ALAN_KARAR_BAGLANMASIN }, ...kararSecenekleri(kararlar)]}
          helperText={KARAR_BAGI_YARDIMI}
          disabled={kararlar.length === 0}
        />
      </div>
    </Dialog>
  );
}
