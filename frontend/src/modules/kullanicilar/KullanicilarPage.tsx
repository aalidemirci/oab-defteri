// Kullanıcılar ekranı (plan F1b-2 "Kullanıcılar uçları", "Kendi hesabı ve ikinci program
// yöneticisi", "E63"; tasarım §4.4.2 Kullanıcılar satırı, §4.4.5). Matriste yalnız program
// yöneticisi Y'dir, öteki roller "—": rota `RolKapisi` ile `kullanicilar` yeteneğine bağlıdır,
// gezinme girdisi de (`AppShell` `NAV_ITEMS`). Kurulum durumunda süzme yoktur (rol kapısı).
//
// LİSTE (`GET accounts/`): BÜTÜN hesaplar — giriş yapamayanlar ve kapalılar dahil, sunucunun
// sırasıyla (açıklar önce rol sırasıyla, kapalılar sonda). Sütunlar tanıtıcı, rol (sıra no'suz),
// hesap sahibi (çözülemezse "okunamadı"), durum (askının ve kapanışın ayrıntısıyla; girişi
// kapalıysa sunucunun nedeni altında) ve son giriş. Satır tıklanınca (ya da Enter/Space) "Hesap
// ayrıntısı" açılır; eylemler oradadır ve sunucunundur (`HesapAyrintisi`).
//
// EYLEMLER: "Yeni hesap" (`YeniHesapPenceresi`; sonuçta hesap teslim pusulası), "Parolayı sıfırla"
// (`ParolaSifirlamaPenceresi`), "Askıdan çıkar" ve pusula (ayrıntı penceresinde), "Hesabı kapat"
// (onay diyaloğu, `ConfirmProvider`). Her yazmadan sonra — başarılı ya da değil — liste, açık
// ayrıntı ve seçenekler yeniden okunur (`KULLANICILAR_ANAHTARI`): güvenlik dosyası yazılamadığında
// da (400) veritabanı adımı yerinde kalır, hesap kapanmış ya da açılmış olabilir; ileti bunu
// söyler. Kapamanın reddi sayfanın hata bandındadır. Hesap açıldığı hâlde parola kaydı yazılamadıysa
// "Yeni hesap" penceresi formu kapatır ve çıkışı ("Parolayı sıfırla") sunar: pencere kapanır,
// hesabın sıfırlama penceresi açılır (`YeniHesapPenceresi` "YARIM AÇILIŞ").
//
// Geçici parola hiçbir yanıtta yoktur; ekranda yalnız onu yazan pencerenin alanında görünür.

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import { useConfirm } from "../../ui/ConfirmProvider";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import EmptyState from "../../ui/EmptyState";
import ErrorBand from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { OkunamadiIsareti } from "../kisiler/ortak";
import { oturumHataMetni } from "../oturum/hatalar";
import HesapAyrintisi from "./HesapAyrintisi";
import ParolaSifirlamaPenceresi from "./ParolaSifirlamaPenceresi";
import YeniHesapPenceresi from "./YeniHesapPenceresi";
import { KULLANICILAR_ANAHTARI, kullanicilarApi } from "./api";
import type { KullaniciSatiri } from "./api";
import {
  BU_OTURUM,
  DUGME_KAPAT,
  DUGME_YENI_HESAP,
  ETIKET_DURUM,
  ETIKET_HESAP_SAHIBI,
  ETIKET_ROL,
  ETIKET_SON_GIRIS,
  ETIKET_TANITICI,
  KAPAMA_ONAY_BASLIGI,
  KAPATILAMADI,
  KAPATILDI_ILETISI,
  KAPATILIYOR,
  KULLANICILAR_ACIKLAMASI,
  KULLANICILAR_BASLIGI,
  LISTE_BOS,
  LISTE_OKUNAMADI,
  TABLO_ADI,
  durumMetni,
  girisNedeniGorunur,
  kapamaSonucu,
  satirEtiketi,
} from "./metinler";

/** Durum hücresi: durum metni; giriş kapalıysa sunucunun nedeni altında (kayıt bozuksa simgeli). */
function DurumHucresi({ hesap }: { hesap: KullaniciSatiri }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span>{durumMetni(hesap)}</span>
      {girisNedeniGorunur(hesap) && (
        <span
          className={`flex items-start gap-1 text-body-small ${
            hesap.kayit_tutuyor ? "text-on-surface-variant" : "text-error"
          }`}
        >
          {!hesap.kayit_tutuyor && <Icon name="error" size="sm" className="mt-0.5 shrink-0" />}
          <span>{hesap.giris.neden}</span>
        </span>
      )}
    </div>
  );
}

const SUTUNLAR: Column<KullaniciSatiri>[] = [
  {
    header: ETIKET_TANITICI,
    cell: (h) => (
      <>
        <span className="font-mono">{h.tanitici}</span>
        {h.oturumdaki && <span className="text-on-surface-variant"> · {BU_OTURUM}</span>}
      </>
    ),
  },
  { header: ETIKET_ROL, cell: (h) => h.rol_etiketi },
  {
    header: ETIKET_HESAP_SAHIBI,
    cell: (h) => (h.ad_soyad === null ? <OkunamadiIsareti /> : h.ad_soyad),
  },
  { header: ETIKET_DURUM, cell: (h) => <DurumHucresi hesap={h} /> },
  { header: ETIKET_SON_GIRIS, cell: (h) => formatDateTime(h.son_giris) },
];

export default function KullanicilarPage() {
  const queryClient = useQueryClient();
  const snackbar = useSnackbar();
  const confirm = useConfirm();
  const liste = useQuery({
    queryKey: [...KULLANICILAR_ANAHTARI, "liste"],
    queryFn: kullanicilarApi.liste,
    retry: false,
  });
  const [seciliId, setSeciliId] = useState<string | null>(null);
  const [sifirlanan, setSifirlanan] = useState<KullaniciSatiri | null>(null);
  const [yeniAcik, setYeniAcik] = useState(false);
  const [hata, setHata] = useState<string | null>(null);
  const [kapatiliyor, setKapatiliyor] = useState(false);

  const yenile = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: KULLANICILAR_ANAHTARI });
  }, [queryClient]);

  // Ayrıntı penceresi listedeki GÜNCEL satırı gösterir (eylemden sonra yeniden okunan).
  const secili = liste.data?.find((h) => h.id === seciliId) ?? null;

  async function kapat(hesap: KullaniciSatiri) {
    // Ayrıntı penceresi kapanır, onay diyaloğu açılır (iki pencere üst üste açılmaz).
    setSeciliId(null);
    const onay = await confirm({
      title: KAPAMA_ONAY_BASLIGI,
      message: kapamaSonucu(hesap),
      confirmLabel: DUGME_KAPAT,
    });
    if (!onay) return;
    setHata(null);
    setKapatiliyor(true);
    try {
      await kullanicilarApi.kapat(hesap.id);
      snackbar.success(KAPATILDI_ILETISI);
    } catch (err) {
      // Güvenlik dosyası yazılamadıysa (400) hesap kapanmıştır: ileti bunu söyler, liste yenilenir.
      setHata(oturumHataMetni(err, KAPATILAMADI));
    } finally {
      setKapatiliyor(false);
      yenile();
    }
  }

  function sifirla(hesap: KullaniciSatiri) {
    setSeciliId(null);
    setSifirlanan(hesap);
  }

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{KULLANICILAR_BASLIGI}</h1>
          <p className="od-page-description">{KULLANICILAR_ACIKLAMASI}</p>
        </div>
        <Button
          icon="person_add"
          onClick={() => {
            setHata(null);
            setYeniAcik(true);
          }}
        >
          {DUGME_YENI_HESAP}
        </Button>
      </div>

      {hata && <ErrorBand hata={hata} />}
      {kapatiliyor && (
        <p role="status" className="text-body-small text-on-surface-variant">
          {KAPATILIYOR}
        </p>
      )}

      {liste.isPending ? (
        <SkeletonList rows={4} />
      ) : liste.isError ? (
        <ErrorBand hata={oturumHataMetni(liste.error, LISTE_OKUNAMADI)} />
      ) : liste.data.length === 0 ? (
        <EmptyState icon="manage_accounts" title={LISTE_BOS} />
      ) : (
        <DataTable<KullaniciSatiri>
          caption={TABLO_ADI}
          columns={SUTUNLAR}
          rows={liste.data}
          onRowClick={(h) => setSeciliId(h.id)}
          rowLabel={satirEtiketi}
        />
      )}

      {secili !== null && (
        <HesapAyrintisi
          hesap={secili}
          onClose={() => setSeciliId(null)}
          onSifirla={sifirla}
          onKapat={(h) => void kapat(h)}
          onDegisti={yenile}
        />
      )}
      {sifirlanan !== null && (
        <ParolaSifirlamaPenceresi
          hesap={sifirlanan}
          onClose={() => setSifirlanan(null)}
          onDegisti={yenile}
        />
      )}
      {yeniAcik && (
        <YeniHesapPenceresi
          onClose={() => setYeniAcik(false)}
          onDegisti={yenile}
          onSifirla={(h) => {
            // Yarım açılışın çıkışı: "Yeni hesap" kapanır, sıfırlama açılır (üst üste değil).
            setYeniAcik(false);
            sifirla(h);
          }}
        />
      )}
    </div>
  );
}
