// Geçiş Kurulumu ekranı (tasarım §7.9 adım 1-4, "Senaryolar"; plan F1c kararları "Geçiş adımı
// atlanabilir", 8. adımın kararı ve notları; ekranı F1c-11). Gezinmede yoktur: Birlik Dönemi'nden, kurulum
// sihirbazından ve Genel Bakış'ın yol haritasından açılır. Her rol okur (M1 satırı); yazma yalnız
// `birlik_donemi_yazma` yeteneğindedir (program yöneticisi; tasarım §7.9 "Kim: yonetici").
//
// Adımlar: (1) ilk birlik dönemi, (2) görevdeki kurul (devralınan üyelik ve temsilci; iptal yalnız program
// yöneticisinin), (3) programdan önceki seçilme sayıları ("Bilinmiyor" tek gerekçeyle), (4) karar defteri
// (son sıra no ve sayfa; tasdik yoksa gerekçe), (5) "Geçiş kurulumu tamamlandı" işareti. İşaretten sonra
// geçiş kayıtları SALT OKUNURDUR (sunucu 409 `gecis_kapali`). Yanlış kayıt değiştirilmez: gerekçeyle
// iptal edilip yeniden girilir. Birlik dönemi genel kurulla açılmışsa geçiş gerekmez. Dönemin kural kopyası
// doğrulanamadıysa (D7) dönem salt okunurdur: D7 bandı çıkar, yazma denetimleri gösterilmez (sunucu da
// 409 `donem_salt_okur` döner). Yazılamayan hâlde boş bölümler öğütsüz "girilmedi" cümlesi gösterir.

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { AtifliUyarilar } from "../birlik-donemi/BirlikDonemiPage";
import { birlikDonemiApi } from "../birlik-donemi/api";
import type { GecisOzeti, KararDefteri } from "../birlik-donemi/api";
import {
  BIRLIK_DONEMI_BASLIGI,
  GOREV_SURESI_BASLIGI,
  KURAL_KOPYASI_BOZUK,
} from "../birlik-donemi/metinler";
import { birlikKisileriApi } from "../kisiler/birlikKisileriApi";
import type { BirlikKisisi } from "../kisiler/birlikKisileriApi";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import { UyumHataBandi, UyumSatirlari } from "../uyum/UyariGerekce";
import type { UyumSatiriVerisi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { TEMSIL_TURU_TR, gecisApi } from "./api";
import type { OrganUyeligi } from "./api";
import DevralinanPenceresi from "./DevralinanPenceresi";
import IlkDonemFormu from "./IlkDonemFormu";
import IptalPenceresi from "./IptalPenceresi";
import KararDefteriFormu from "./KararDefteriFormu";
import SayacBeyaniPenceresi, { BILINMIYOR } from "./SayacBeyaniPenceresi";
import type { SayacSatiri } from "./SayacBeyaniPenceresi";
import {
  ACIK_ADIMLAR_ETIKETI,
  ALAN_DEFTER_ACILIS,
  ALAN_SAYFA_SAYISI,
  ALAN_SON_SAYFA,
  ALAN_SON_SIRA_NO,
  ALAN_TASDIK_GUNU,
  ALAN_TASDIK_MAKAMI,
  ALAN_TASDIK_NO,
  DEFTER_ACIKLAMASI,
  DEFTER_BASLIGI,
  DEFTER_BOS,
  DEFTER_IPTAL_BASLIGI,
  DEFTER_IPTAL_METNI,
  DEFTER_UYUM_BASLIGI,
  DEVRALINAN_IPTAL_BASLIGI,
  DEVRALINAN_IPTAL_METNI,
  DUGME_KAYDI_IPTAL,
  DUGME_SAYAC_BEYANI,
  DUGME_TAMAMLA,
  DUGME_TAMAMLANDI_ISARETLE,
  DUGME_UYE_EKLE,
  DURUM_ETIKETI,
  GECIS_ACIKLAMASI,
  GECIS_ADIMI_TR,
  GECIS_BASLIGI,
  GECIS_DURUMU_TR,
  GECIS_OKUNAMADI,
  GECIS_TAMAMLANAMADI,
  GECIS_TAMAMLANDI,
  GEREKMIYOR_NOTU,
  GOREV_TR,
  ILK_DONEM_ACIKLAMASI,
  ILK_DONEM_BASLIGI,
  ILK_DONEM_BOS,
  KAYIT_IPTAL_EDILDI,
  KAYIT_IPTAL_EDILEMEDI,
  KURUL_ACIKLAMASI,
  KURUL_BASLIGI,
  KURUL_BOS,
  KURUL_DENETLEME,
  KURUL_YONETIM,
  SAYAC_ACIKLAMASI,
  SAYAC_ACIKLAMASI_BILGI,
  SAYAC_BASLIGI,
  SAYAC_BILINMIYOR,
  SAYAC_GIRILMEDI,
  SAYAC_KISI_YOK,
  SAYAC_UYUM_BASLIGI,
  SUTUN_AD_SOYAD,
  SUTUN_GOREV,
  SUTUN_KOLTUK,
  SUTUN_KURUL,
  TAMAMLA_ACIKLAMASI,
  TAMAMLA_BASLIGI,
  TAMAMLA_ONAY_BASLIGI,
  TAMAMLA_ONAY_METNI,
  TASDIK_MEM,
  TASDIK_NOTER,
  acikAdimlarCumlesi,
  koltukMetni,
  tamamlandiNotu,
} from "./metinler";

/** Görevdeki kurulun okunduğu organlar. */
const KURUL_ORGANLARI = ["YK", "DK", "TEMSILCI"] as const;

function kurulAdi(u: OrganUyeligi): string {
  if (u.organ === "YK") return KURUL_YONETIM;
  if (u.organ === "DK") return KURUL_DENETLEME;
  return u.representation ? TEMSIL_TURU_TR[u.representation] : "—";
}

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
    <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
      <div className="space-y-1">
        <h2 className="text-title-medium text-on-surface">{baslik}</h2>
        {aciklama && <p className="text-body-medium text-on-surface-variant">{aciklama}</p>}
      </div>
      {children}
    </Card>
  );
}

function sayacSecimi(
  deger: number | null,
  kisi: number,
  alan: "yk" | "dk_baskanlik",
  ozet: GecisOzeti,
): string {
  if (deger !== null) return String(deger);
  const bilinmiyor = ozet.uyum_satirlari.some(
    (s) => s.konu_turu === "oab.OabPerson" && s.konu === String(kisi) && s.sayac_alani === alan,
  );
  return bilinmiyor ? BILINMIYOR : "";
}

function sayacMetni(secim: string): string {
  if (secim === "") return SAYAC_GIRILMEDI;
  return secim === BILINMIYOR ? SAYAC_BILINMIYOR : secim;
}

function DefterBilgisi({ defter }: { defter: KararDefteri }) {
  const makam =
    defter.certified_by === "NOTER"
      ? TASDIK_NOTER
      : defter.certified_by === "IL_ILCE_MEM"
        ? TASDIK_MEM
        : "—";
  const satirlar: Array<[string, string]> = [
    [ALAN_SON_SIRA_NO, String(defter.last_no_before_program ?? "—")],
    [ALAN_SON_SAYFA, String(defter.last_page_before_program ?? "—")],
    [ALAN_TASDIK_MAKAMI, makam],
    [ALAN_TASDIK_GUNU, formatDate(defter.certified_on)],
    [ALAN_TASDIK_NO, defter.certification_no || "—"],
    [ALAN_SAYFA_SAYISI, String(defter.page_count ?? "—")],
    [ALAN_DEFTER_ACILIS, formatDate(defter.opened_on)],
  ];
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {satirlar.map(([etiket, deger]) => (
        <div key={etiket} className="min-w-0">
          <dt className="text-label-medium text-on-surface-variant">{etiket}</dt>
          <dd className="break-words text-body-medium text-on-surface">{deger}</dd>
        </div>
      ))}
    </dl>
  );
}

type Pencere =
  | { tur: "uye" }
  | { tur: "sayac" }
  | { tur: "uye-iptal"; uyelik: OrganUyeligi }
  | { tur: "defter-iptal"; defter: KararDefteri }
  | null;

export default function GecisKurulumuPage() {
  const yetki = useYetki();
  const yazabilir = yetki.acik("birlik_donemi_yazma");
  const snackbar = useSnackbar();
  const confirm = useConfirm();
  const [ozet, setOzet] = useState<GecisOzeti | null>(null);
  const [uyelikler, setUyelikler] = useState<OrganUyeligi[]>([]);
  const [kisiler, setKisiler] = useState<BirlikKisisi[]>([]);
  const [loading, setLoading] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [tamamlaHatasi, setTamamlaHatasi] = useState<UyumHatasi | SayfaHatasi | null>(null);
  const [pencere, setPencere] = useState<Pencere>(null);
  const [yenile, setYenile] = useState(0);
  const tazele = useCallback(() => setYenile((k) => k + 1), []);

  useEffect(() => {
    let iptal = false;
    setLoading(true);
    (async () => {
      const okunan = await birlikDonemiApi.gecis();
      const donem = okunan.donem;
      const [listeler, kisiListesi] = await Promise.all([
        donem === null
          ? Promise.resolve([] as OrganUyeligi[][])
          : Promise.all(KURUL_ORGANLARI.map((o) => gecisApi.uyelikler(donem.id, o))),
        birlikKisileriApi.liste(),
      ]);
      return { okunan, uyeler: listeler.flat(), kisiListesi };
    })()
      .then(({ okunan, uyeler, kisiListesi }) => {
        if (iptal) return;
        setOzet(okunan);
        setUyelikler(uyeler);
        setKisiler(kisiListesi);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, GECIS_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setLoading(false);
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const donem = ozet?.donem ?? null;
  // Geçişe açık: geçiş dönemi açık, işaret konmamış ve kural kopyası tutuyor (D7 değil; sunucu yine de
  // denetler).
  const acik =
    donem !== null &&
    donem.status === "ACIK" &&
    donem.transition_completed_on === null &&
    donem.kural_kopyasi_tutuyor;
  const yazilir = yazabilir && acik;
  const etkinKisiler = useMemo(() => kisiler.filter((k) => k.status === "AKTIF"), [kisiler]);
  const devralinanlar = useMemo(
    () => uyelikler.filter((u) => u.source === "DEVRALINAN" && u.status !== "IPTAL"),
    [uyelikler],
  );

  const sayacSatirlari: SayacSatiri[] = useMemo(() => {
    if (ozet === null) return [];
    const kisiKaydi = new Map(kisiler.map((k) => [k.id, k]));
    const satirlar = new Map<number, SayacSatiri>();
    for (const u of devralinanlar) {
      if (u.organ !== "YK" && u.organ !== "DK") continue;
      const kisi = kisiKaydi.get(u.person);
      if (kisi === undefined) continue;
      const satir = satirlar.get(kisi.id) ?? {
        kisi: kisi.id,
        ad: kisi.full_name ?? u.person_name ?? "—",
        yk: false,
        dk: false,
        ykDegeri: sayacSecimi(kisi.external_yk_terms, kisi.id, "yk", ozet),
        dkDegeri: sayacSecimi(kisi.external_dk_chair_terms, kisi.id, "dk_baskanlik", ozet),
      };
      if (u.organ === "YK") satir.yk = true;
      if (u.organ === "DK") satir.dk = true;
      satirlar.set(kisi.id, satir);
    }
    return [...satirlar.values()];
  }, [devralinanlar, kisiler, ozet]);

  const sayacUyumSatirlari: UyumSatiriVerisi[] = useMemo(() => {
    // Aynı ileti kişi başına yinelenir: liste iletiyle tekilleşir (kişisizdir).
    const gorulen = new Set<string>();
    const sonuc: UyumSatiriVerisi[] = [];
    for (const s of ozet?.uyum_satirlari ?? []) {
      if (s.sayac_alani === "" || gorulen.has(s.metin)) continue;
      gorulen.add(s.metin);
      sonuc.push({ tur: s.tur, metin: s.metin, atif: s.atif, gerekceli: s.gerekceli });
    }
    return sonuc;
  }, [ozet]);

  const defterUyumSatirlari: UyumSatiriVerisi[] = (ozet?.uyum_satirlari ?? [])
    .filter((s) => s.konu_turu === "oab.OfficialBook")
    .map((s) => ({ tur: s.tur, metin: s.metin, atif: s.atif, gerekceli: s.gerekceli }));

  const tamamla = async () => {
    if (ozet === null) return;
    const eksik = acikAdimlarCumlesi(ozet.open_steps);
    const ok = await confirm({
      title: TAMAMLA_ONAY_BASLIGI,
      message: eksik ? `${TAMAMLA_ONAY_METNI} ${eksik}` : TAMAMLA_ONAY_METNI,
      confirmLabel: DUGME_TAMAMLANDI_ISARETLE,
    });
    if (!ok) return;
    setTamamlaHatasi(null);
    try {
      await gecisApi.tamamla();
      snackbar.success(GECIS_TAMAMLANDI);
      tazele();
    } catch (e) {
      setTamamlaHatasi(uyumHatasiOku(e) ?? hataOku(e, GECIS_TAMAMLANAMADI));
    }
  };

  const sutunlar: Column<OrganUyeligi>[] = [
    { header: SUTUN_AD_SOYAD, cell: (u) => u.person_name ?? "—" },
    { header: SUTUN_KURUL, cell: kurulAdi },
    { header: SUTUN_KOLTUK, cell: (u) => koltukMetni(u.seat_type, u.seat_order) },
    { header: SUTUN_GOREV, cell: (u) => (u.organ === "TEMSILCI" ? "—" : GOREV_TR[u.role]) },
  ];
  if (yazilir) {
    sutunlar.push({
      header: <span className="sr-only">{DUGME_KAYDI_IPTAL}</span>,
      align: "right",
      cell: (u) => (
        <Button
          variant="text"
          icon="block"
          // Dar sütunda düğme metni iki satıra kırılmasın (11a ekran görüntüsü; 11b düzeltmesi).
          className="whitespace-nowrap"
          aria-label={`${u.person_name ?? ""} ${DUGME_KAYDI_IPTAL}`.trim()}
          onClick={() => setPencere({ tur: "uye-iptal", uyelik: u })}
        >
          {DUGME_KAYDI_IPTAL}
        </Button>
      ),
    });
  }

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{GECIS_BASLIGI}</h1>
          <p className="od-page-description">{GECIS_ACIKLAMASI}</p>
        </div>
      </div>

      {!yazabilir && yetki.durum === "hazir" && <SaltOkurNotu />}
      {hata && <ErrorBand hata={hata} />}

      {loading ? (
        <SkeletonList rows={5} />
      ) : (
        ozet !== null && (
          <>
            <Card elevation={0} className="space-y-2 p-[var(--od-panel-padding)]">
              <p className="text-body-large text-on-surface">
                {DURUM_ETIKETI}: {GECIS_DURUMU_TR[ozet.state]}
              </p>
              {donem !== null && !donem.kural_kopyasi_tutuyor && (
                <div
                  role="alert"
                  className="flex items-start gap-2 rounded-shape-sm bg-error-container px-4 py-3 text-body-medium text-on-error-container"
                >
                  <Icon name="gpp_bad" size="lg" className="shrink-0" />
                  <span>{KURAL_KOPYASI_BOZUK}</span>
                </div>
              )}
              {ozet.state === "GEREKMIYOR" && (
                <p className="text-body-medium text-on-surface-variant">{GEREKMIYOR_NOTU}</p>
              )}
              {donem?.transition_completed_on && (
                <p role="note" className="text-body-medium text-on-surface-variant">
                  {tamamlandiNotu(formatDate(donem.transition_completed_on))}
                </p>
              )}
              {ozet.open_steps.length > 0 && (
                <p className="text-body-medium text-on-surface-variant">
                  {ACIK_ADIMLAR_ETIKETI}: {ozet.open_steps.map((a) => GECIS_ADIMI_TR[a]).join(", ")}
                </p>
              )}
              <Link
                to="/birlik-donemi"
                className="inline-flex text-label-large text-primary underline underline-offset-2"
              >
                {BIRLIK_DONEMI_BASLIGI}
              </Link>
            </Card>

            {ozet.state !== "GEREKMIYOR" && (
              <>
                <Bolum baslik={ILK_DONEM_BASLIGI} aciklama={ILK_DONEM_ACIKLAMASI}>
                  {donem === null ? (
                    yazabilir ? (
                      <IlkDonemFormu onAcildi={() => tazele()} />
                    ) : (
                      <p className="text-body-medium text-on-surface-variant">{ILK_DONEM_BOS}</p>
                    )
                  ) : (
                    <div className="space-y-3">
                      <p className="break-words text-body-medium text-on-surface">
                        {donem.name} · {formatDate(donem.start_date)}
                      </p>
                      <AtifliUyarilar
                        uyarilar={ozet.gorev_suresi_uyarilari}
                        baslik={GOREV_SURESI_BASLIGI}
                      />
                    </div>
                  )}
                </Bolum>

                {donem !== null && (
                  <>
                    <Bolum baslik={KURUL_BASLIGI} aciklama={KURUL_ACIKLAMASI}>
                      {yazilir && (
                        <div className="flex justify-end">
                          <Button icon="group_add" onClick={() => setPencere({ tur: "uye" })}>
                            {DUGME_UYE_EKLE}
                          </Button>
                        </div>
                      )}
                      {devralinanlar.length === 0 ? (
                        <p className="text-body-medium text-on-surface-variant">{KURUL_BOS}</p>
                      ) : (
                        <DataTable<OrganUyeligi>
                          columns={sutunlar}
                          rows={devralinanlar}
                          caption={KURUL_BASLIGI}
                        />
                      )}
                    </Bolum>

                    <Bolum
                      baslik={SAYAC_BASLIGI}
                      aciklama={yazilir ? SAYAC_ACIKLAMASI : SAYAC_ACIKLAMASI_BILGI}
                    >
                      {sayacSatirlari.length === 0 ? (
                        <p className="text-body-medium text-on-surface-variant">
                          {yazilir ? SAYAC_KISI_YOK : KURUL_BOS}
                        </p>
                      ) : (
                        <ul className="divide-y divide-outline-variant">
                          {sayacSatirlari.map((s) => (
                            <li
                              key={s.kisi}
                              className="flex flex-wrap justify-between gap-x-4 gap-y-1 py-2 text-body-medium"
                            >
                              <span className="min-w-0 break-words text-on-surface">{s.ad}</span>
                              <span className="text-on-surface-variant">
                                {s.yk && `${KURUL_YONETIM}: ${sayacMetni(s.ykDegeri)}`}
                                {s.yk && s.dk && " · "}
                                {s.dk && `${KURUL_DENETLEME}: ${sayacMetni(s.dkDegeri)}`}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                      <UyumSatirlari satirlar={sayacUyumSatirlari} baslik={SAYAC_UYUM_BASLIGI} />
                      {yazilir && sayacSatirlari.length > 0 && (
                        <div className="flex justify-end">
                          <Button
                            variant="tonal"
                            icon="pin"
                            onClick={() => setPencere({ tur: "sayac" })}
                          >
                            {DUGME_SAYAC_BEYANI}
                          </Button>
                        </div>
                      )}
                    </Bolum>

                    <Bolum baslik={DEFTER_BASLIGI} aciklama={DEFTER_ACIKLAMASI}>
                      {ozet.karar_defteri !== null ? (
                        <>
                          <DefterBilgisi defter={ozet.karar_defteri} />
                          <UyumSatirlari
                            satirlar={defterUyumSatirlari}
                            baslik={DEFTER_UYUM_BASLIGI}
                          />
                          {yazilir && (
                            <div className="flex justify-end">
                              <Button
                                variant="text"
                                icon="block"
                                onClick={() =>
                                  ozet.karar_defteri !== null &&
                                  setPencere({ tur: "defter-iptal", defter: ozet.karar_defteri })
                                }
                              >
                                {DUGME_KAYDI_IPTAL}
                              </Button>
                            </div>
                          )}
                        </>
                      ) : yazilir ? (
                        <KararDefteriFormu onKaydedildi={tazele} />
                      ) : (
                        <p className="text-body-medium text-on-surface-variant">{DEFTER_BOS}</p>
                      )}
                    </Bolum>

                    {yazilir && (
                      <Bolum baslik={TAMAMLA_BASLIGI} aciklama={TAMAMLA_ACIKLAMASI}>
                        {tamamlaHatasi &&
                          ("tur" in tamamlaHatasi ? (
                            <UyumHataBandi hata={tamamlaHatasi} />
                          ) : (
                            <ErrorBand hata={tamamlaHatasi} />
                          ))}
                        <div className="flex justify-end">
                          <Button icon="task_alt" onClick={() => void tamamla()}>
                            {DUGME_TAMAMLA}
                          </Button>
                        </div>
                      </Bolum>
                    )}
                  </>
                )}
              </>
            )}
          </>
        )
      )}

      {pencere?.tur === "uye" && (
        <DevralinanPenceresi
          kisiler={etkinKisiler}
          onKapat={() => setPencere(null)}
          onEklendi={() => {
            setPencere(null);
            tazele();
          }}
        />
      )}
      {pencere?.tur === "sayac" && (
        <SayacBeyaniPenceresi
          satirlar={sayacSatirlari}
          onKapat={() => setPencere(null)}
          onKaydedildi={() => {
            setPencere(null);
            tazele();
          }}
        />
      )}
      {pencere?.tur === "uye-iptal" && (
        <IptalPenceresi
          baslik={DEVRALINAN_IPTAL_BASLIGI}
          metin={DEVRALINAN_IPTAL_METNI}
          yedekHata={KAYIT_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            await gecisApi.uyeligiIptalEt(pencere.uyelik.id, gerekce);
            setPencere(null);
            snackbar.success(KAYIT_IPTAL_EDILDI);
            tazele();
          }}
        />
      )}
      {pencere?.tur === "defter-iptal" && (
        <IptalPenceresi
          baslik={DEFTER_IPTAL_BASLIGI}
          metin={DEFTER_IPTAL_METNI}
          yedekHata={KAYIT_IPTAL_EDILEMEDI}
          onKapat={() => setPencere(null)}
          onIptal={async (gerekce) => {
            await gecisApi.kararDefteriniIptalEt(pencere.defter.id, gerekce);
            setPencere(null);
            snackbar.success(KAYIT_IPTAL_EDILDI);
            tazele();
          }}
        />
      )}
    </div>
  );
}
