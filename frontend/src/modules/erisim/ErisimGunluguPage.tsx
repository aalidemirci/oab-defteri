// Erişim Günlüğü ekranı (plan F1b-2 "Erişim günlüğü okuma ucu", "Ön yüz"; tasarım §4.6.4,
// §4.4.2 "Erişim günlüğü" satırı: program yöneticisi ve Denetleme Kurulu okur, öteki roller
// göremez). Rota `RolKapisi` ile `erisim_gunlugu` yeteneğine bağlıdır, gezinme girdisi de
// (`AppShell` `NAV_ITEMS`). Kurulum durumunda süzme yoktur (rol kapısı).
//
// SÜZGEÇLER (`GET access-log/`): tarih aralığı (alanlar tarayıcının tarih alanıdır: ekranda
// gg.aa.yyyy, uca ISO yyyy-aa-gg gider; gün Europe/Istanbul'a göredir, iki uç dahil — sunucu
// hesaplar), tür (yanıttaki `turler`, görünen adıyla) ve hesap (yanıttaki `hesaplar`: rol etiketi
// + tanıtıcı + açılış/kapanış günü; aynı tanıtıcılı eski ve yeni hesap ayrılır). Süzgeç değişince
// ilk sayfaya dönülür. Seçenekler son okunan yanıttan gelir: biçimsiz bir süzgeç (400) onları
// silmez. 400'ün iletisi sunucunundur ve süzgecin alanına bağlıdır (`fields`; takvimin ucundaki
// gün ve ters aralık da): alanın altına yazılır; alana bağlanamayan ret sayfanın hata bandındadır.
//
// LİSTE: en yeni önce, sayfalı (sayfa boyutu sunucunun); sütunlar zaman, hesap, tür, okunan kayıt
// (model ve alan kodu yazılmaz; adları o okumaları getiren fazda `metinler`'e girer) ve çıktının
// satır sayısı. Ad-soyad yoktur. Bugün günlüğe yazan bir okuma olmadığı için süzgeçsiz liste boştur
// ve boş hâl bunu söyler; süzgeçli boş liste süzgeçleri anar.
//
// OKUMA İZ BIRAKMAZ (sunucu): ne denetim izine ne erişim günlüğüne satır yazılır.

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { parseApiFieldErrors } from "../../lib/formErrors";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import EmptyState from "../../ui/EmptyState";
import ErrorBand from "../../ui/ErrorBand";
import PaginationBar from "../../ui/PaginationBar";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import TextField from "../../ui/TextField";
import { oturumHataMetni } from "../oturum/hatalar";
import { ERISIM_GUNLUGU_ANAHTARI, erisimGunluguApi } from "./api";
import type { ErisimGunluguSayfasi, ErisimSatiri, ErisimSuzgeci } from "./api";
import {
  ALAN_BASLANGIC,
  ALAN_BITIS,
  ALAN_HESAP,
  ALAN_TUR,
  BOS_ACIKLAMA,
  BOS_BASLIK,
  BUTUN_HESAPLAR,
  BUTUN_TURLER,
  DUGME_TEMIZLE,
  ERISIM_GUNLUGU_ACIKLAMASI,
  ERISIM_GUNLUGU_BASLIGI,
  OKUNAMADI,
  SUTUN_CIKTI,
  SUTUN_HESAP,
  SUTUN_KAYIT,
  SUTUN_TUR,
  SUTUN_ZAMAN,
  SUZGECE_UYAN_YOK,
  SUZGECE_UYAN_YOK_ACIKLAMA,
  SUZGECLER,
  TABLO_ADI,
  ciktiMetni,
  erisimHesabi,
  okunanKayit,
} from "./metinler";

const SUTUNLAR: Column<ErisimSatiri>[] = [
  { header: SUTUN_ZAMAN, cell: (s) => formatDateTime(s.zaman) },
  { header: SUTUN_HESAP, cell: (s) => erisimHesabi(s.hesap) },
  { header: SUTUN_TUR, cell: (s) => s.tur_adi },
  { header: SUTUN_KAYIT, cell: (s) => okunanKayit(s) },
  { header: SUTUN_CIKTI, cell: (s) => ciktiMetni(s), align: "right" },
];

/** Alanın altına yazılan süzgeçler (sayfa numarasının reddi hata bandındadır). */
const ALANLI_SUZGECLER = ["baslangic", "bitis", "tur", "hesap"] as const;
type AlanliSuzgec = (typeof ALANLI_SUZGECLER)[number];

export interface SuzgecHatalari {
  /** Alanın altına yazılacak iletiler. */
  alanlar: Partial<Record<AlanliSuzgec, string>>;
  /** Alana bağlanamayan ret (hata bandı); yoksa null. */
  genel: string | null;
}

/**
 * Okuma hatasının ekrandaki yeri: 400 `validation_error`'ın süzgeç alanlarına bağlı iletileri
 * alanların altına; alana bağlanamayan ret (sayfa, başka alan, alansız ret, okuma hatası) hata
 * bandına — ileti sunucunundur, yoksa `OKUNAMADI`.
 */
export function suzgecHatalari(hata: unknown): SuzgecHatalari {
  if (hata === null || hata === undefined) return { alanlar: {}, genel: null };
  const alanlar: Partial<Record<AlanliSuzgec, string>> = {};
  let alansiz = false;
  if (hata instanceof ApiError && hata.code === "validation_error") {
    const hatalar = parseApiFieldErrors(hata) ?? {};
    for (const [ad, ileti] of Object.entries(hatalar)) {
      if ((ALANLI_SUZGECLER as readonly string[]).includes(ad)) {
        alanlar[ad as AlanliSuzgec] = ileti;
      } else {
        alansiz = true;
      }
    }
  }
  const bagli = Object.keys(alanlar).length > 0;
  return { alanlar, genel: bagli && !alansiz ? null : oturumHataMetni(hata, OKUNAMADI) };
}

type Secenekler = Pick<ErisimGunluguSayfasi, "turler" | "hesaplar">;

export default function ErisimGunluguPage() {
  const [baslangic, setBaslangic] = useState("");
  const [bitis, setBitis] = useState("");
  const [tur, setTur] = useState("");
  const [hesap, setHesap] = useState("");
  const [sayfa, setSayfa] = useState(1);
  const [secenekler, setSecenekler] = useState<Secenekler | null>(null);

  const suzgec: ErisimSuzgeci = { baslangic, bitis, tur, hesap, sayfa };
  const sorgu = useQuery({
    queryKey: [...ERISIM_GUNLUGU_ANAHTARI, suzgec],
    queryFn: () => erisimGunluguApi.sayfa(suzgec),
    retry: false,
    // Süzgeç değişirken önceki sayfa yerinde kalır (tablo sıçramasın).
    placeholderData: keepPreviousData,
  });
  const veri = sorgu.data;

  // Seçenekler son okunan yanıttandır: biçimsiz bir süzgeç (400) onları silmez.
  useEffect(() => {
    if (veri) setSecenekler({ turler: veri.turler, hesaplar: veri.hesaplar });
  }, [veri]);

  // Son sayfadan büyük bir sayfada kalındıysa (kayıtlar bu arada azaldı) son sayfaya dönülür.
  useEffect(() => {
    if (veri && !sorgu.isPlaceholderData && veri.satirlar.length === 0 && veri.toplam > 0) {
      if (sayfa > veri.sayfa_sayisi) setSayfa(veri.sayfa_sayisi);
    }
  }, [veri, sorgu.isPlaceholderData, sayfa]);

  const hatalar = suzgecHatalari(sorgu.isError ? sorgu.error : null);
  const suzgecVar = Boolean(baslangic || bitis || tur || hesap);

  /** Süzgeç değişince ilk sayfaya dönülür. */
  function degistir(ata: (deger: string) => void) {
    return (deger: string) => {
      ata(deger);
      setSayfa(1);
    };
  }

  function temizle() {
    setBaslangic("");
    setBitis("");
    setTur("");
    setHesap("");
    setSayfa(1);
  }

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{ERISIM_GUNLUGU_BASLIGI}</h1>
          <p className="od-page-description">{ERISIM_GUNLUGU_ACIKLAMASI}</p>
        </div>
      </div>

      <div role="group" aria-label={SUZGECLER}>
        <Card
          elevation={0}
          className="grid items-start gap-3 p-[var(--od-panel-padding)] shadow-elevation-1 sm:grid-cols-2 lg:grid-cols-[10rem_10rem_minmax(12rem,1fr)_minmax(14rem,1fr)_auto]"
        >
          <TextField
            label={ALAN_BASLANGIC}
            type="date"
            value={baslangic}
            max={bitis || undefined}
            onChange={(e) => degistir(setBaslangic)(e.target.value)}
            error={hatalar.alanlar.baslangic}
          />
          <TextField
            label={ALAN_BITIS}
            type="date"
            value={bitis}
            min={baslangic || undefined}
            onChange={(e) => degistir(setBitis)(e.target.value)}
            error={hatalar.alanlar.bitis}
          />
          <Select
            label={ALAN_TUR}
            placeholder={BUTUN_TURLER}
            value={tur}
            onChange={(e) => degistir(setTur)(e.target.value)}
            options={(secenekler?.turler ?? []).map((t) => ({ value: t.tur, label: t.tur_adi }))}
            error={hatalar.alanlar.tur}
          />
          <Select
            label={ALAN_HESAP}
            placeholder={BUTUN_HESAPLAR}
            value={hesap}
            onChange={(e) => degistir(setHesap)(e.target.value)}
            options={(secenekler?.hesaplar ?? []).map((h) => ({
              value: h.id,
              label: erisimHesabi(h),
            }))}
            error={hatalar.alanlar.hesap}
          />
          <div className="flex items-end self-stretch">
            <Button variant="text" icon="filter_alt_off" onClick={temizle} disabled={!suzgecVar}>
              {DUGME_TEMIZLE}
            </Button>
          </div>
        </Card>
      </div>

      {hatalar.genel !== null && <ErrorBand hata={hatalar.genel} />}

      {sorgu.isPending ? (
        <SkeletonList rows={4} />
      ) : sorgu.isError || !veri ? null : veri.satirlar.length === 0 ? (
        suzgecVar ? (
          <EmptyState
            icon="filter_alt"
            title={SUZGECE_UYAN_YOK}
            description={SUZGECE_UYAN_YOK_ACIKLAMA}
          />
        ) : (
          <EmptyState icon="policy" title={BOS_BASLIK} description={BOS_ACIKLAMA} />
        )
      ) : (
        <div className="space-y-3" aria-busy={sorgu.isFetching || undefined}>
          <DataTable<ErisimSatiri> caption={TABLO_ADI} columns={SUTUNLAR} rows={veri.satirlar} />
          <PaginationBar
            count={veri.toplam}
            offset={(veri.sayfa - 1) * veri.sayfa_boyutu}
            pageSize={veri.sayfa_boyutu}
            onOffset={(offset) => setSayfa(Math.floor(offset / veri.sayfa_boyutu) + 1)}
          />
        </div>
      )}
    </div>
  );
}
