// Gelen-Giden Evrak ekranı (plan F2 §6.1 M10; tasarım §5.2.8). Gezinmededir; okuma her role açıktır
// (müdür ve Denetleme Kurulu okur), yazma `evrak_kaydi` yeteneğindedir (program yöneticisi ve yönetim
// kurulu rolleri): defterin kaydı, elle gelen ve giden kayıt, kaydın eki. Okul müdürünün genel kurul
// yazısı programca giden evrak olarak işlenir (⁷); programın hazırladığı resmî yazı (E12) Genel Kurul'daki
// belge kartından öneriyle kaydedilir (U20). Numara tekilliği serttir (hesap bütünlüğü); sıra atlama
// uyarı + gerekçedir (ortak bileşen). Defter seçimi birden çok defterde çizilir; varsayılan kullanımdaki
// en yeni defterdir. Dolan defterin yerine yenisi defter varken de kaydedilir (başlıktaki "Defteri
// kaydet"); kaydedilen defter seçili olur. Liste yıl ve yönle süzülür; satır kaydın ayrıntısını ve eklerini pencerede açar.

import { useCallback, useEffect, useState } from "react";

import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import Dialog from "../../ui/Dialog";
import EmptyState from "../../ui/EmptyState";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { DUGME_KAPAT, SAYI_GECERSIZ } from "../genel-kurul/metinler";
import { Bilgi, EkListesi, SayiAlani, YazmaPenceresi, sayiOku } from "../genel-kurul/ortak";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { useYetki } from "../oturum/yetki";
import { gelenGidenApi } from "./api";
import type { DefterListesi, EvrakDefteri, EvrakKaydi, EvrakYonu, TasdikMakami } from "./api";
import {
  ALAN_ACILIS_GUNU,
  ALAN_DEFTER,
  ALAN_DIS_SAYI,
  ALAN_KARSI_TARAF,
  ALAN_KAYIT_NO,
  ALAN_KONU,
  ALAN_SAYFA_SAYISI,
  ALAN_SON_NO,
  ALAN_TARIH,
  ALAN_TASDIK_GUNU,
  ALAN_TASDIK_MAKAMI,
  ALAN_TASDIK_NO,
  ALAN_YIL,
  ALAN_YON,
  BUTUN_YONLER,
  DEFTERLER_OKUNAMADI,
  DEFTER_ACIKLAMASI,
  DEFTER_DURUMU_TR,
  DEFTER_KAYDEDILDI,
  DEFTER_KAYDEDILEMEDI,
  DEFTER_PENCERESI_BASLIGI,
  DEFTER_YOK,
  DEFTER_YOK_ACIKLAMASI,
  DUGME_DEFTER,
  DUGME_YENI_KAYIT,
  GELEN_GIDEN_ACIKLAMASI,
  GELEN_GIDEN_BASLIGI,
  KAYITLAR_BASLIGI,
  KAYITLAR_OKUNAMADI,
  KAYIT_ACIKLAMASI,
  KAYIT_AYRINTISI_BASLIGI,
  KAYIT_EKI_YARDIMI,
  KAYIT_EKLENDI,
  KAYIT_EKLENEMEDI,
  KAYIT_EKLERI,
  KAYIT_PENCERESI_BASLIGI,
  KAYIT_YOK,
  OKUNAMADI,
  PROGRAMIN_YAZISI,
  SIRADAKI_NO,
  SUTUN_KARSI_TARAF,
  SUTUN_KONU,
  SUTUN_NO,
  SUTUN_TARIH,
  SUTUN_YON,
  TARIH_GEREKLI,
  TASDIK_MAKAMI_TR,
  YON_TR,
  kayitNo,
} from "./metinler";

function DefterPenceresi({
  onKapat,
  onKaydedildi,
}: {
  onKapat: () => void;
  onKaydedildi: (defter: EvrakDefteri) => void;
}) {
  const snackbar = useSnackbar();
  const [makam, setMakam] = useState<TasdikMakami | "">("IL_ILCE_MEM");
  const [tasdikGunu, setTasdikGunu] = useState("");
  const [tasdikNo, setTasdikNo] = useState("");
  const [sayfa, setSayfa] = useState("");
  const [sonNo, setSonNo] = useState("");
  const [acilis, setAcilis] = useState("");
  const [hatalar, setHatalar] = useState<Record<string, string>>({});
  return (
    <YazmaPenceresi
      baslik={DEFTER_PENCERESI_BASLIGI}
      dugme={DUGME_DEFTER}
      yedekHata={DEFTER_KAYDEDILEMEDI}
      baglam="gelen_giden_evrak.defter"
      onKapat={onKapat}
      dogrula={() => {
        const h: Record<string, string> = {};
        if (sayiOku(sayfa) === "gecersiz") h.sayfa = SAYI_GECERSIZ;
        if (sayiOku(sonNo) === "gecersiz") h.sonNo = SAYI_GECERSIZ;
        setHatalar(h);
        return Object.keys(h).length === 0;
      }}
      onGonder={async () => {
        const sayi = (m: string) => {
          const s = sayiOku(m);
          return typeof s === "number" && s > 0 ? s : null;
        };
        const yeni = await gelenGidenApi.defterKaydet({
          certified_by: makam,
          certified_on: tasdikGunu || null,
          certification_no: tasdikNo.trim(),
          page_count: sayi(sayfa),
          last_no_before_program: sayi(sonNo),
          opened_on: acilis || null,
        });
        snackbar.success(DEFTER_KAYDEDILDI);
        onKaydedildi(yeni);
      }}
      ikon="menu_book"
    >
      <p className="text-body-medium text-on-surface-variant">{DEFTER_ACIKLAMASI}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Select
          label={ALAN_TASDIK_MAKAMI}
          value={makam}
          onChange={(e) => setMakam(e.target.value as TasdikMakami)}
          options={(Object.keys(TASDIK_MAKAMI_TR) as TasdikMakami[]).map((m) => ({
            value: m,
            label: TASDIK_MAKAMI_TR[m],
          }))}
        />
        <TextField
          label={ALAN_TASDIK_GUNU}
          type="date"
          value={tasdikGunu}
          onChange={(e) => setTasdikGunu(e.target.value)}
        />
        <TextField
          label={ALAN_TASDIK_NO}
          value={tasdikNo}
          maxLength={64}
          onChange={(e) => setTasdikNo(e.target.value)}
        />
        <SayiAlani
          etiket={ALAN_SAYFA_SAYISI}
          deger={sayfa}
          onDegis={setSayfa}
          hata={hatalar.sayfa}
        />
        <SayiAlani etiket={ALAN_SON_NO} deger={sonNo} onDegis={setSonNo} hata={hatalar.sonNo} />
        <TextField
          label={ALAN_ACILIS_GUNU}
          type="date"
          value={acilis}
          onChange={(e) => setAcilis(e.target.value)}
        />
      </div>
    </YazmaPenceresi>
  );
}

function KayitPenceresi({
  defter,
  onKapat,
  onKaydedildi,
}: {
  defter: number;
  onKapat: () => void;
  onKaydedildi: () => void;
}) {
  const snackbar = useSnackbar();
  const [yon, setYon] = useState<EvrakYonu>("GELEN");
  const [tarih, setTarih] = useState("");
  const [no, setNo] = useState("");
  const [karsi, setKarsi] = useState("");
  const [konu, setKonu] = useState("");
  const [disSayi, setDisSayi] = useState("");
  const [hatalar, setHatalar] = useState<Record<string, string>>({});
  return (
    <YazmaPenceresi
      baslik={KAYIT_PENCERESI_BASLIGI}
      dugme={DUGME_YENI_KAYIT}
      yedekHata={KAYIT_EKLENEMEDI}
      baglam="gelen_giden_evrak.kayit"
      onKapat={onKapat}
      dogrula={() => {
        const h: Record<string, string> = {};
        if (!tarih) h.tarih = TARIH_GEREKLI;
        if (sayiOku(no) === "gecersiz") h.no = SAYI_GECERSIZ;
        setHatalar(h);
        return Object.keys(h).length === 0;
      }}
      onGonder={async (ek) => {
        const okunan = sayiOku(no);
        await gelenGidenApi.kaydet({
          direction: yon,
          tarih,
          counterparty: karsi.trim(),
          subject: konu.trim(),
          external_ref: disSayi.trim(),
          record_no: typeof okunan === "number" && okunan > 0 ? okunan : null,
          defter,
          ...ek,
        });
        snackbar.success(KAYIT_EKLENDI);
        onKaydedildi();
      }}
      genis
      ikon="move_to_inbox"
    >
      <p className="text-body-medium text-on-surface-variant">{KAYIT_ACIKLAMASI}</p>
      <div className="grid gap-3 sm:grid-cols-3">
        <Select
          label={ALAN_YON}
          value={yon}
          onChange={(e) => setYon(e.target.value as EvrakYonu)}
          options={(["GELEN", "GIDEN"] as const).map((y) => ({ value: y, label: YON_TR[y] }))}
        />
        <TextField
          label={ALAN_TARIH}
          type="date"
          required
          value={tarih}
          onChange={(e) => setTarih(e.target.value)}
          error={hatalar.tarih}
        />
        <SayiAlani etiket={ALAN_KAYIT_NO} deger={no} onDegis={setNo} hata={hatalar.no} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label={ALAN_KARSI_TARAF}
          value={karsi}
          maxLength={1000}
          onChange={(e) => setKarsi(e.target.value)}
        />
        <TextField
          label={ALAN_DIS_SAYI}
          value={disSayi}
          maxLength={64}
          onChange={(e) => setDisSayi(e.target.value)}
        />
      </div>
      <TextField
        label={ALAN_KONU}
        value={konu}
        maxLength={1000}
        onChange={(e) => setKonu(e.target.value)}
      />
    </YazmaPenceresi>
  );
}

function KayitAyrintisi({
  kayit,
  ekleyebilir,
  onKapat,
  onDegisti,
}: {
  kayit: EvrakKaydi;
  ekleyebilir: boolean;
  onKapat: () => void;
  onDegisti: () => void;
}) {
  return (
    <Dialog
      open
      onClose={onKapat}
      title={KAYIT_AYRINTISI_BASLIGI}
      actions={
        <Button variant="text" onClick={onKapat}>
          {DUGME_KAPAT}
        </Button>
      }
    >
      <div className="space-y-4">
        <dl className="grid gap-3 sm:grid-cols-2">
          <Bilgi etiket={SUTUN_NO}>{kayitNo(kayit.year, kayit.record_no)}</Bilgi>
          <Bilgi etiket={SUTUN_YON}>{YON_TR[kayit.direction]}</Bilgi>
          <Bilgi etiket={SUTUN_TARIH}>{formatDate(kayit.date)}</Bilgi>
          <Bilgi etiket={ALAN_DIS_SAYI}>{kayit.external_ref || "—"}</Bilgi>
          <Bilgi etiket={ALAN_KARSI_TARAF}>{kayit.counterparty ?? OKUNAMADI}</Bilgi>
          <Bilgi etiket={ALAN_KONU}>{kayit.subject ?? OKUNAMADI}</Bilgi>
        </dl>
        {kayit.generated_document !== null && (
          <p className="text-body-small text-on-surface-variant">{PROGRAMIN_YAZISI}</p>
        )}
        <EkListesi
          ekler={kayit.ekler}
          baslik={KAYIT_EKLERI}
          yardim={KAYIT_EKI_YARDIMI}
          onEkle={
            ekleyebilir
              ? async (dosya) => {
                  await gelenGidenApi.ekEkle(kayit.id, dosya);
                  onDegisti();
                }
              : undefined
          }
        />
      </div>
    </Dialog>
  );
}

export default function GelenGidenEvrakPage() {
  const yetki = useYetki();
  const yazabilir = yetki.acik("evrak_kaydi");
  const [defterler, setDefterler] = useState<DefterListesi | null>(null);
  const [defterHatasi, setDefterHatasi] = useState<SayfaHatasi | null>(null);
  const [defter, setDefter] = useState<number | null>(null);
  const [yil, setYil] = useState<number>(new Date().getFullYear());
  const [yon, setYon] = useState<EvrakYonu | "">("");
  const [kayitlar, setKayitlar] = useState<EvrakKaydi[] | null>(null);
  const [kayitHatasi, setKayitHatasi] = useState<SayfaHatasi | null>(null);
  const [pencere, setPencere] = useState<"defter" | "kayit" | EvrakKaydi | null>(null);
  const [yenile, setYenile] = useState(0);
  const tazele = useCallback(() => setYenile((y) => y + 1), []);

  useEffect(() => {
    let iptal = false;
    gelenGidenApi
      .defterler()
      .then((d) => {
        if (iptal) return;
        setDefterler(d);
        setDefterHatasi(null);
        setDefter((onceki) => onceki ?? d.varsayilan ?? d.defterler[0]?.id ?? null);
      })
      .catch((e: unknown) => {
        if (!iptal) setDefterHatasi(hataOku(e, DEFTERLER_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  useEffect(() => {
    if (defter === null) return;
    let iptal = false;
    gelenGidenApi
      .kayitlar({ book: defter, year: yil, direction: yon })
      .then((l) => {
        if (iptal) return;
        setKayitlar(l);
        setKayitHatasi(null);
        setPencere((p) =>
          typeof p === "object" && p !== null ? (l.find((k) => k.id === p.id) ?? p) : p,
        );
      })
      .catch((e: unknown) => {
        if (!iptal) setKayitHatasi(hataOku(e, KAYITLAR_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [defter, yil, yon, yenile]);

  const seciliDefter = defterler?.defterler.find((d) => d.id === defter);
  const buYil = new Date().getFullYear();
  const yillar = Array.from({ length: 6 }, (_, i) => buYil - i);

  const sutunlar: Column<EvrakKaydi>[] = [
    { header: SUTUN_NO, cell: (k) => kayitNo(k.year, k.record_no) },
    { header: SUTUN_YON, cell: (k) => YON_TR[k.direction] },
    { header: SUTUN_TARIH, cell: (k) => formatDate(k.date) },
    {
      header: SUTUN_KARSI_TARAF,
      cell: (k) => <span className="break-words">{k.counterparty ?? OKUNAMADI}</span>,
    },
    {
      header: SUTUN_KONU,
      cell: (k) => <span className="break-words">{k.subject ?? OKUNAMADI}</span>,
    },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{GELEN_GIDEN_BASLIGI}</h1>
          <p className="od-page-description">{GELEN_GIDEN_ACIKLAMASI}</p>
        </div>
        {yazabilir && defterler !== null && defterler.defterler.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <Button variant="outlined" icon="menu_book" onClick={() => setPencere("defter")}>
              {DUGME_DEFTER}
            </Button>
            {defter !== null && (
              <Button icon="add" onClick={() => setPencere("kayit")}>
                {DUGME_YENI_KAYIT}
              </Button>
            )}
          </div>
        )}
      </div>

      {!yazabilir && yetki.durum === "hazir" && <SaltOkurNotu />}
      {defterHatasi && <ErrorBand hata={defterHatasi} />}

      {defterler === null ? (
        !defterHatasi && <SkeletonList rows={4} />
      ) : defterler.defterler.length === 0 ? (
        <EmptyState
          icon="menu_book"
          title={DEFTER_YOK}
          description={yazabilir ? DEFTER_YOK_ACIKLAMASI : undefined}
          action={
            yazabilir ? (
              <Button icon="menu_book" onClick={() => setPencere("defter")}>
                {DUGME_DEFTER}
              </Button>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {defterler.defterler.length > 1 && (
              <Select
                label={ALAN_DEFTER}
                value={String(defter ?? "")}
                onChange={(e) => setDefter(Number(e.target.value))}
                options={defterler.defterler.map((d) => ({
                  value: String(d.id),
                  label: `${formatDate(d.opened_on ?? d.certified_on)} · ${DEFTER_DURUMU_TR[d.status] ?? d.status}`,
                }))}
              />
            )}
            <Select
              label={ALAN_YIL}
              value={String(yil)}
              onChange={(e) => setYil(Number(e.target.value))}
              options={yillar.map((y) => ({ value: String(y), label: String(y) }))}
            />
            <Select
              label={ALAN_YON}
              value={yon}
              onChange={(e) => setYon(e.target.value as EvrakYonu | "")}
              options={[
                { value: "", label: BUTUN_YONLER },
                { value: "GELEN", label: YON_TR.GELEN },
                { value: "GIDEN", label: YON_TR.GIDEN },
              ]}
            />
          </div>
          {seciliDefter && (
            <p className="text-body-small text-on-surface-variant">
              {SIRADAKI_NO}: {kayitNo(buYil, seciliDefter.siradaki_no)}
            </p>
          )}
          {kayitHatasi && <ErrorBand hata={kayitHatasi} />}
          <section aria-labelledby="gge-kayitlar" className="space-y-3">
            <h2 id="gge-kayitlar" className="text-title-medium text-on-surface">
              {KAYITLAR_BASLIGI}
            </h2>
            {kayitlar === null ? (
              !kayitHatasi && <SkeletonList rows={4} />
            ) : kayitlar.length === 0 ? (
              <p className="text-body-medium text-on-surface-variant">{KAYIT_YOK}</p>
            ) : (
              <DataTable<EvrakKaydi>
                columns={sutunlar}
                rows={kayitlar}
                caption={KAYITLAR_BASLIGI}
                onRowClick={(k) => setPencere(k)}
                rowLabel={(k) => `${kayitNo(k.year, k.record_no)} kaydını aç`}
              />
            )}
          </section>
        </>
      )}

      {pencere === "defter" && (
        <DefterPenceresi
          onKapat={() => setPencere(null)}
          onKaydedildi={(yeni) => {
            setPencere(null);
            setDefter(yeni.id);
            tazele();
          }}
        />
      )}
      {pencere === "kayit" && defter !== null && (
        <KayitPenceresi
          defter={defter}
          onKapat={() => setPencere(null)}
          onKaydedildi={() => {
            setPencere(null);
            tazele();
          }}
        />
      )}
      {typeof pencere === "object" && pencere !== null && (
        <KayitAyrintisi
          kayit={pencere}
          ekleyebilir={yazabilir}
          onKapat={() => setPencere(null)}
          onDegisti={tazele}
        />
      )}
    </div>
  );
}
