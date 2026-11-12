// Kişiler → Birlik Kişileri sekmesi (`?tab=birlik`; tasarım §5.2.2 `OabPerson`; plan F1c kararları
// "Kişiler ekranı"; F1c-11). Organlara ve temsilciliklere girecek kişilerin kaydıdır, personel
// sicilinden ayrıdır. Her rol okur (M2 satırı); yazma `birlik_kisi_yazma` yeteneğindedir (program
// yöneticisi ve yönetim kurulu), veli listesinden ekleme ayrıca `veli_listesi` ister (yalnız program
// yöneticisi; tasarım §8.4, ¹⁰).
//
// KVKK: T.C. kimlik no ve telefon YOKTUR (K9; tasarım §5.2.2). Veli listesinden yalnız yazılan ad kör
// indeksle aranır, liste dökülmez; kopyada ad ve soyad ayrıştırılır (son sözcük soyad), kayıttan
// düzeltilir. Silme yoktur: kişi PASİF olur; pasif kişide yalnız durum değişir. "Olası aynı kişi"
// (tasarım §13 D30): sunucu 409 `olasi_ayni_kisi` döner, kullanıcı aynı kişi olmadığını onaylarsa istek
// `ayni_kisi_degil` ile yinelenir. Programdan önceki seçilme sayıları geçiş kurulumunda beyan edilir;
// burada salt okunur.

import { useCallback, useEffect, useState } from "react";

import { useDebounced } from "../../hooks/useDebounced";
import { useFormErrors } from "../../hooks/useFormErrors";
import { ApiError } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import Autocomplete from "../../ui/Autocomplete";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import Dialog from "../../ui/Dialog";
import EmptyState from "../../ui/EmptyState";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { MEMBER_KIND_TR, okulApi } from "../okul/api";
import type { Personnel } from "../okul/api";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import { BIRLIK_KISI_TURU_TR, OLASI_AYNI_KISI_KODU, birlikKisileriApi } from "./birlikKisileriApi";
import type { BirlikKisiTuru, BirlikKisisi } from "./birlikKisileriApi";
import {
  ALAN_BIRLIK_TURU,
  ALAN_OKUL_MUDURU,
  ALAN_ONCEKI_DK,
  ALAN_ONCEKI_YK,
  ALAN_PERSONEL,
  ALAN_VELIDIR,
  ALAN_VELI_ADI,
  ALAN_YETISKIN_BEYANI,
  ARAMAYI_DEGISTIRIN,
  BIRLIK_KISILERI_ACIKLAMASI,
  BIRLIK_KISILERI_OKUNAMADI,
  BIRLIK_KISILERI_SEKMESI,
  BIRLIK_KISISINI_DUZENLE,
  BIRLIK_KISISI_ARAMAYA_UYAN_YOK,
  BIRLIK_KISISI_ARAMAYA_UYAN_YOK_ACIKLAMASI,
  BIRLIK_KISISI_AYRINTISI,
  BIRLIK_KISISI_ETKINLESTIRILDI,
  BIRLIK_KISISI_KAYDEDILDI,
  BIRLIK_KISISI_KAYDEDILEMEDI,
  BIRLIK_KISISI_PASIF_YAPILDI,
  BIRLIK_KISISI_YOK,
  BIRLIK_KISISI_YOK_ACIKLAMASI,
  DUGME_BIRLIK_KISISI_EKLE,
  DUGME_EKLE,
  DUGME_ETKINLESTIR,
  DUGME_PASIF_YAP,
  DUGME_PERSONELDEN_EKLE,
  DUGME_VELI_LISTESINDEN_EKLE,
  DURUM_AKTIF,
  DURUM_PASIF,
  OKUL_MUDURU_YARDIMI,
  OLASI_AYNI_KISI_BASLIGI,
  OLASI_AYNI_KISI_ONAYI,
  ONCEKI_SAYI_YARDIMI,
  ONCEKI_SAYI_YOK,
  PASIFLERI_GOSTER,
  PASIF_KISI_NOTU,
  PERSONELDEN_EKLE_BASLIGI,
  PERSONELDEN_EKLE_YARDIMI,
  PERSONEL_ARA_YER_TUTUCU,
  PERSONEL_BULUNAMADI,
  PERSONEL_SECIN,
  SUTUN_TUR,
  VELIDIR_YARDIMI,
  VELI_ADI_YARDIMI,
  VELI_ADI_ZORUNLU,
  VELI_LISTESINDEN_EKLE_BASLIGI,
  YENI_BIRLIK_KISISI,
  YETISKIN_BEYANI_YARDIMI,
} from "./metinler";
import { ErrorBand, KisiAdi, hataOku, kisiKaydiniMetni, okunamadiMi } from "./ortak";
import type { SayfaHatasi } from "./ortak";

const TUR_SECENEKLERI = (Object.entries(BIRLIK_KISI_TURU_TR) as [BirlikKisiTuru, string][]).map(
  ([value, label]) => ({ value, label }),
);

/** Çözülemeyen adın yardım metni (KisilerPage ile aynı söz; tasarım §13 D48). */
const OKUNAMAYAN_AD_YARDIMI = "Kayıtlı değer okunamadı; kaydetmek için yeniden yazın.";

/** "Olası aynı kişi" sorusunu sorar; onaylanırsa isteği `ayni_kisi_degil` ile yineler. */
function useAyniKisiSorusu() {
  const confirm = useConfirm();
  return useCallback(
    async <T,>(istek: (ayniKisiDegil: boolean) => Promise<T>): Promise<T | null> => {
      try {
        return await istek(false);
      } catch (e) {
        if (!(e instanceof ApiError) || e.code !== OLASI_AYNI_KISI_KODU) throw e;
        const ok = await confirm({
          title: OLASI_AYNI_KISI_BASLIGI,
          message: e.message,
          confirmLabel: OLASI_AYNI_KISI_ONAYI,
        });
        return ok ? istek(true) : null;
      }
    },
    [confirm],
  );
}

function OncekiSayi({ deger }: { deger: number | null }) {
  return <>{deger === null ? ONCEKI_SAYI_YOK : formatNumber(deger)}</>;
}

function Onay({
  etiket,
  yardim,
  checked,
  disabled,
  onChange,
}: {
  etiket: string;
  yardim: string;
  checked: boolean;
  disabled: boolean;
  onChange: (deger: boolean) => void;
}) {
  return (
    <label className="flex min-h-10 items-start gap-3 text-body-medium text-on-surface">
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 size-5 shrink-0 accent-primary"
      />
      <span className="min-w-0">
        {etiket}
        <span className="mt-1 block text-body-small text-on-surface-variant">{yardim}</span>
      </span>
    </label>
  );
}

// ---------------------------------------------------------------------------
// Ekleme, düzenleme ve ayrıntı penceresi
// ---------------------------------------------------------------------------
function KisiPenceresi({
  kisi,
  yazabilir,
  onKapat,
  onKaydedildi,
}: {
  /** null: yeni kayıt. */
  kisi: BirlikKisisi | null;
  yazabilir: boolean;
  onKapat: () => void;
  onKaydedildi: () => void;
}) {
  const snackbar = useSnackbar();
  const sor = useAyniKisiSorusu();
  const [tur, setTur] = useState<BirlikKisiTuru>(kisi?.kind ?? "VELI");
  const [ad, setAd] = useState(kisi?.first_name ?? "");
  const [soyad, setSoyad] = useState(kisi?.last_name ?? "");
  const [veli, setVeli] = useState(kisi?.is_parent ?? true);
  const [yetiskin, setYetiskin] = useState(kisi?.adult_declared ?? false);
  const [mudur, setMudur] = useState(kisi?.is_principal ?? false);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors();
  const pasif = kisi?.status === "PASIF";
  const kilitli = !yazabilir || pasif;

  const turDegisti = (yeni: BirlikKisiTuru) => {
    setTur(yeni);
    // Yeni kayıtta veli işareti türden gelir (sunucunun varsayılanı); kullanıcı değiştirebilir.
    if (kisi === null) setVeli(yeni === "VELI");
  };

  const kaydet = async () => {
    clearErrors();
    setHata(null);
    if (!ad.trim() || !soyad.trim()) {
      if (!ad.trim()) setFieldError("first_name", "Ad zorunludur.");
      if (!soyad.trim()) setFieldError("last_name", "Soyad zorunludur.");
      return;
    }
    setBusy(true);
    try {
      const sonuc = await sor((ayniKisiDegil) =>
        kisi === null
          ? birlikKisileriApi.ekle({
              kind: tur,
              first_name: ad.trim(),
              last_name: soyad.trim(),
              is_parent: veli,
              adult_declared: yetiskin,
              ayni_kisi_degil: ayniKisiDegil,
            })
          : birlikKisileriApi.guncelle(kisi.id, {
              kind: tur,
              first_name: ad.trim(),
              last_name: soyad.trim(),
              is_parent: veli,
              adult_declared: yetiskin,
              is_principal: mudur,
              ayni_kisi_degil: ayniKisiDegil,
            }),
      );
      if (sonuc === null) {
        setBusy(false);
        return;
      }
      snackbar.success(BIRLIK_KISISI_KAYDEDILDI);
      onKaydedildi();
    } catch (e) {
      applyApiError(e);
      setHata(hataOku(e, BIRLIK_KISISI_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  const durumDegistir = async () => {
    if (kisi === null) return;
    setBusy(true);
    setHata(null);
    try {
      await birlikKisileriApi.guncelle(kisi.id, { status: pasif ? "AKTIF" : "PASIF" });
      snackbar.success(pasif ? BIRLIK_KISISI_ETKINLESTIRILDI : BIRLIK_KISISI_PASIF_YAPILDI);
      onKaydedildi();
    } catch (e) {
      setHata(hataOku(e, BIRLIK_KISISI_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  const baslik = !yazabilir
    ? BIRLIK_KISISI_AYRINTISI
    : kisi === null
      ? YENI_BIRLIK_KISISI
      : BIRLIK_KISISINI_DUZENLE;

  return (
    <Dialog
      open
      onClose={onKapat}
      title={baslik}
      actions={
        yazabilir ? (
          <>
            {kisi !== null && (
              <Button
                variant="text"
                icon={pasif ? "person_check" : "person_off"}
                onClick={() => void durumDegistir()}
                disabled={busy}
              >
                {pasif ? DUGME_ETKINLESTIR : DUGME_PASIF_YAP}
              </Button>
            )}
            <Button variant="text" onClick={onKapat} disabled={busy}>
              Vazgeç
            </Button>
            {!pasif && (
              <Button icon="check" onClick={() => void kaydet()} disabled={busy}>
                {busy ? "Kaydediliyor…" : "Kaydet"}
              </Button>
            )}
          </>
        ) : (
          <Button variant="text" onClick={onKapat}>
            Kapat
          </Button>
        )
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        {pasif && yazabilir && (
          <p role="note" className="text-body-medium text-on-surface-variant">
            {PASIF_KISI_NOTU}
          </p>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label="Ad"
            required
            disabled={kilitli}
            value={ad}
            onChange={(e) => setAd(e.target.value)}
            error={errors.first_name}
            helperText={
              kisi !== null && okunamadiMi(kisi, "first_name") ? OKUNAMAYAN_AD_YARDIMI : undefined
            }
          />
          <TextField
            label="Soyad"
            required
            disabled={kilitli}
            value={soyad}
            onChange={(e) => setSoyad(e.target.value)}
            error={errors.last_name}
            helperText={
              kisi !== null && okunamadiMi(kisi, "last_name") ? OKUNAMAYAN_AD_YARDIMI : undefined
            }
          />
          <Select
            label={ALAN_BIRLIK_TURU}
            disabled={kilitli}
            value={tur}
            onChange={(e) => turDegisti(e.target.value as BirlikKisiTuru)}
            options={TUR_SECENEKLERI}
            error={errors.kind}
          />
        </div>
        <Onay
          etiket={ALAN_VELIDIR}
          yardim={VELIDIR_YARDIMI}
          checked={veli}
          disabled={kilitli}
          onChange={setVeli}
        />
        <Onay
          etiket={ALAN_YETISKIN_BEYANI}
          yardim={YETISKIN_BEYANI_YARDIMI}
          checked={yetiskin}
          disabled={kilitli}
          onChange={setYetiskin}
        />
        {kisi !== null && (
          <Onay
            etiket={ALAN_OKUL_MUDURU}
            yardim={OKUL_MUDURU_YARDIMI}
            checked={mudur}
            disabled={kilitli}
            onChange={setMudur}
          />
        )}
        {kisi !== null && (
          <dl className="grid gap-3 sm:grid-cols-2">
            <div className="min-w-0">
              <dt className="text-label-medium text-on-surface-variant">{ALAN_ONCEKI_YK}</dt>
              <dd className="text-body-medium text-on-surface">
                <OncekiSayi deger={kisi.external_yk_terms} />
              </dd>
            </div>
            <div className="min-w-0">
              <dt className="text-label-medium text-on-surface-variant">{ALAN_ONCEKI_DK}</dt>
              <dd className="text-body-medium text-on-surface">
                <OncekiSayi deger={kisi.external_dk_chair_terms} />
              </dd>
            </div>
            <p className="text-body-small text-on-surface-variant sm:col-span-2">
              {ONCEKI_SAYI_YARDIMI}
            </p>
          </dl>
        )}
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Personelden ve veli listesinden ekleme
// ---------------------------------------------------------------------------
function PersoneldenEklePenceresi({
  onKapat,
  onEklendi,
}: {
  onKapat: () => void;
  onEklendi: () => void;
}) {
  const snackbar = useSnackbar();
  const sor = useAyniKisiSorusu();
  const [personel, setPersonel] = useState<Personnel | null>(null);
  // Kararlı arama işlevi (`Autocomplete` etkisinin bağımlılığıdır).
  const ara = useCallback(
    async (sorgu: string) =>
      (await okulApi.listPersonnel({ search: sorgu, limit: 20 })).results.filter(
        (p) => p.is_active,
      ),
    [],
  );
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const ekle = async () => {
    setHata(null);
    if (personel === null) {
      setAlanHatasi(PERSONEL_SECIN);
      return;
    }
    setBusy(true);
    try {
      const sonuc = await sor((ayniKisiDegil) =>
        birlikKisileriApi.personeldenEkle(personel.id, ayniKisiDegil),
      );
      if (sonuc === null) {
        setBusy(false);
        return;
      }
      snackbar.success(BIRLIK_KISISI_KAYDEDILDI);
      onEklendi();
    } catch (e) {
      setHata(hataOku(e, BIRLIK_KISISI_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={PERSONELDEN_EKLE_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={onKapat} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="person_add" onClick={() => void ekle()} disabled={busy}>
            {busy ? "Kaydediliyor…" : DUGME_EKLE}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        <Autocomplete<Personnel>
          label={ALAN_PERSONEL}
          required
          placeholder={PERSONEL_ARA_YER_TUTUCU}
          selected={personel}
          search={ara}
          onSelect={(p) => {
            setPersonel(p);
            setAlanHatasi(undefined);
          }}
          onClear={() => setPersonel(null)}
          getLabel={(p) => p.full_name ?? ""}
          getSublabel={(p) => MEMBER_KIND_TR[p.member_kind]}
          getKey={(p) => p.id}
          emptyText={PERSONEL_BULUNAMADI}
          helperText={PERSONELDEN_EKLE_YARDIMI}
          error={alanHatasi}
        />
      </div>
    </Dialog>
  );
}

function VeliListesindenEklePenceresi({
  onKapat,
  onEklendi,
}: {
  onKapat: () => void;
  onEklendi: () => void;
}) {
  const snackbar = useSnackbar();
  const sor = useAyniKisiSorusu();
  const [ad, setAd] = useState("");
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const ekle = async () => {
    setHata(null);
    if (!ad.trim()) {
      setAlanHatasi(VELI_ADI_ZORUNLU);
      return;
    }
    setBusy(true);
    try {
      const sonuc = await sor((ayniKisiDegil) =>
        birlikKisileriApi.veliListesindenEkle(ad.trim(), ayniKisiDegil),
      );
      if (sonuc === null) {
        setBusy(false);
        return;
      }
      snackbar.success(BIRLIK_KISISI_KAYDEDILDI);
      onEklendi();
    } catch (e) {
      setHata(hataOku(e, BIRLIK_KISISI_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={VELI_LISTESINDEN_EKLE_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={onKapat} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="person_add" onClick={() => void ekle()} disabled={busy}>
            {busy ? "Kaydediliyor…" : DUGME_EKLE}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        <TextField
          label={ALAN_VELI_ADI}
          required
          autoComplete="off"
          maxLength={255}
          value={ad}
          onChange={(e) => {
            setAd(e.target.value);
            setAlanHatasi(undefined);
          }}
          error={alanHatasi}
          helperText={VELI_ADI_YARDIMI}
        />
      </div>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Sekme
// ---------------------------------------------------------------------------
type Pencere = { tur: "kisi"; kisi: BirlikKisisi | null } | { tur: "personel" } | { tur: "veli" };

export default function BirlikKisileri({
  yazabilir,
  velidenEkleyebilir,
}: {
  /** Ekleme, düzenleme, personelden ekleme (`birlik_kisi_yazma`). */
  yazabilir: boolean;
  /** Veli listesinden ekleme (`birlik_kisi_yazma` ve `veli_listesi`). */
  velidenEkleyebilir: boolean;
}) {
  const [arama, setArama] = useState("");
  const aranan = useDebounced(arama);
  const [pasifler, setPasifler] = useState(false);
  const aramaVar = aranan.trim() !== "";
  const [kisiler, setKisiler] = useState<BirlikKisisi[]>([]);
  const [loading, setLoading] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [pencere, setPencere] = useState<Pencere | null>(null);
  const [yenile, setYenile] = useState(0);

  useEffect(() => {
    let iptal = false;
    setLoading(true);
    birlikKisileriApi
      .liste({ search: aranan, onlyActive: !pasifler })
      .then((liste) => {
        if (iptal) return;
        setKisiler(liste);
        setHata(null);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, BIRLIK_KISILERI_OKUNAMADI));
      })
      .finally(() => {
        if (!iptal) setLoading(false);
      });
    return () => {
      iptal = true;
    };
  }, [aranan, pasifler, yenile]);

  const kapat = () => setPencere(null);
  const kaydedildi = () => {
    setPencere(null);
    setYenile((k) => k + 1);
  };

  const sutunlar: Column<BirlikKisisi>[] = [
    { header: "Ad soyad", cell: (k) => <KisiAdi kayit={k} /> },
    { header: SUTUN_TUR, cell: (k) => BIRLIK_KISI_TURU_TR[k.kind] },
    { header: "Durum", cell: (k) => (k.status === "AKTIF" ? DURUM_AKTIF : DURUM_PASIF) },
  ];

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-title-medium text-on-surface">{BIRLIK_KISILERI_SEKMESI}</p>
          {!loading && (
            <p className="text-body-small text-on-surface-variant">
              {formatNumber(kisiler.length)} kayıt
            </p>
          )}
        </div>
        {yazabilir && (
          <div className="flex flex-wrap gap-2">
            <Button icon="person_add" onClick={() => setPencere({ tur: "kisi", kisi: null })}>
              {DUGME_BIRLIK_KISISI_EKLE}
            </Button>
            <Button variant="tonal" icon="badge" onClick={() => setPencere({ tur: "personel" })}>
              {DUGME_PERSONELDEN_EKLE}
            </Button>
            {velidenEkleyebilir && (
              <Button
                variant="tonal"
                icon="family_restroom"
                onClick={() => setPencere({ tur: "veli" })}
              >
                {DUGME_VELI_LISTESINDEN_EKLE}
              </Button>
            )}
          </div>
        )}
      </div>

      <p className="text-body-medium text-on-surface-variant">{BIRLIK_KISILERI_ACIKLAMASI}</p>
      {!yazabilir && <SaltOkurNotu />}

      <Card
        elevation={0}
        className="grid items-end gap-3 bg-surface-container-lowest p-[var(--od-panel-padding)] sm:grid-cols-2"
      >
        <TextField
          label="Ara"
          value={arama}
          onChange={(e) => setArama(e.target.value)}
          placeholder="Ad soyad…"
        />
        <label className="flex min-h-10 items-center gap-3 text-body-medium text-on-surface">
          <input
            type="checkbox"
            checked={pasifler}
            onChange={(e) => setPasifler(e.target.checked)}
            className="size-5 shrink-0 accent-primary"
          />
          {PASIFLERI_GOSTER}
        </label>
      </Card>

      {hata && <ErrorBand hata={hata} />}

      {loading ? (
        <SkeletonList rows={4} />
      ) : kisiler.length === 0 ? (
        !hata && (
          // Arama doluyken boş sonuç "kişi yok" demek değildir: yeni kayda değil aramaya yönlendirilir
          // (olası aynı kişi, D30). Okunan listeyle tutarlı olsun diye gecikmeli `aranan` kullanılır.
          <EmptyState
            icon="groups"
            title={aramaVar ? BIRLIK_KISISI_ARAMAYA_UYAN_YOK : BIRLIK_KISISI_YOK}
            description={
              aramaVar
                ? pasifler
                  ? ARAMAYI_DEGISTIRIN
                  : BIRLIK_KISISI_ARAMAYA_UYAN_YOK_ACIKLAMASI
                : yazabilir
                  ? BIRLIK_KISISI_YOK_ACIKLAMASI
                  : undefined
            }
          />
        )
      ) : (
        <DataTable<BirlikKisisi>
          columns={sutunlar}
          rows={kisiler}
          caption={BIRLIK_KISILERI_SEKMESI}
          onRowClick={(k) => setPencere({ tur: "kisi", kisi: k })}
          rowLabel={(k) => `${kisiKaydiniMetni(k)} aç`}
        />
      )}

      {pencere?.tur === "kisi" && (
        <KisiPenceresi
          kisi={pencere.kisi}
          yazabilir={yazabilir}
          onKapat={kapat}
          onKaydedildi={kaydedildi}
        />
      )}
      {pencere?.tur === "personel" && (
        <PersoneldenEklePenceresi onKapat={kapat} onEklendi={kaydedildi} />
      )}
      {pencere?.tur === "veli" && (
        <VeliListesindenEklePenceresi onKapat={kapat} onEklendi={kaydedildi} />
      )}
    </div>
  );
}
