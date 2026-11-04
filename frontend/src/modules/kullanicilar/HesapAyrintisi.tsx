// "Hesap ayrıntısı" penceresi (plan F1b-2 "Kullanıcılar uçları": `accounts/<id>/` — açan, kapatan,
// parola değişimi, sıfırlama, son girişler). Satırın bilgisi listeden hemen çizilir; ayrıntının
// ek alanları gelince yazılır (okunamazsa yalnız o bölüm okunamadı der).
//
// EYLEMLER satırındır ve SUNUCUNUNDUR (`eylemler`): her düğme yapılamıyorsa kapalıdır ve sunucunun
// nedeni yanında yazar; dört eylemin nedeni aynıysa (ör. kapalı hesap) neden bir kez yazılır.
// "Askıdan çıkar" ve "Hesap teslim pusulasını kaydet" bu pencerede yürür (sonuç snackbar'da, ret
// pencerede); "Parolayı sıfırla" ve "Hesabı kapat" pencereyi kapatıp kendi penceresini (sıfırlama
// formu, onay diyaloğu) açar: iki pencere üst üste açılmaz (odak tuzakları çakışmasın).

import { useQuery } from "@tanstack/react-query";
import { useId, useState } from "react";
import type { ReactNode } from "react";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand from "../../ui/ErrorBand";
import Skeleton from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { OkunamadiIsareti } from "../kisiler/ortak";
import { oturumHataMetni } from "../oturum/hatalar";
import EylemDugmesi from "./EylemDugmesi";
import { KULLANICILAR_ANAHTARI, kullanicilarApi } from "./api";
import type { EylemDurumu, KullaniciSatiri } from "./api";
import {
  ASKIDAN_CIKARILAMADI,
  ASKIDAN_CIKARILDI_ILETISI,
  ASKIDAN_CIKARILIYOR,
  AYRINTI_BASLIGI,
  AYRINTI_OKUNAMADI,
  BU_OTURUM,
  DUGME_ASKIDAN_CIKAR,
  DUGME_KAPAT,
  DUGME_PUSULA,
  DUGME_SIFIRLA,
  ETIKET_ACILIS,
  ETIKET_HESAP_SAHIBI,
  ETIKET_DURUM,
  ETIKET_EYLEMLER,
  ETIKET_GIRIS,
  ETIKET_KAPANIS,
  ETIKET_PAROLA_DEGISIMI,
  ETIKET_ROL,
  ETIKET_SIFIRLAMA,
  ETIKET_SON_GIRISLER,
  ETIKET_TANITICI,
  GIRIS_ACIK,
  GIRIS_YOK,
  HAZIRLANIYOR,
  PUSULA_HAZIRLANAMADI,
  PUSULA_KAYDEDILDI_ILETISI,
  anVeHesap,
  durumMetni,
  sifirlamaSatiri,
} from "./metinler";
import { pusulayiKaydet } from "./pusula";

interface Props {
  /** Listedeki güncel satır (eylemler ondan). */
  hesap: KullaniciSatiri;
  onClose: () => void;
  /** "Parolayı sıfırla": pencere kapanır, sıfırlama formu açılır. */
  onSifirla: (hesap: KullaniciSatiri) => void;
  /** "Hesabı kapat": pencere kapanır, onay diyaloğu açılır. */
  onKapat: (hesap: KullaniciSatiri) => void;
  /** Liste yeniden okunsun (eylemden sonra, başarılı ya da değil). */
  onDegisti: () => void;
}

type Surer = "askidan_cikar" | "pusula" | null;

function Satir({ etiket, children }: { etiket: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-0.5 sm:grid-cols-[12rem_1fr] sm:gap-4">
      <dt className="text-label-medium font-semibold text-on-surface-variant">{etiket}</dt>
      <dd className="text-body-medium text-on-surface">{children}</dd>
    </div>
  );
}

export default function HesapAyrintisi({ hesap, onClose, onSifirla, onKapat, onDegisti }: Props) {
  const snackbar = useSnackbar();
  const ortakNedenId = useId();
  const [surer, setSurer] = useState<Surer>(null);
  const [hata, setHata] = useState<string | null>(null);
  const ayrinti = useQuery({
    queryKey: [...KULLANICILAR_ANAHTARI, "ayrinti", hesap.id],
    queryFn: () => kullanicilarApi.ayrinti(hesap.id),
    retry: false,
  });
  const ek = ayrinti.data;
  const e = hesap.eylemler;

  async function askidanCikar() {
    setSurer("askidan_cikar");
    setHata(null);
    try {
      await kullanicilarApi.askidanCikar(hesap.id);
      snackbar.success(ASKIDAN_CIKARILDI_ILETISI);
    } catch (err) {
      setHata(oturumHataMetni(err, ASKIDAN_CIKARILAMADI));
    } finally {
      setSurer(null);
      onDegisti();
    }
  }

  async function pusula() {
    setSurer("pusula");
    setHata(null);
    try {
      await pusulayiKaydet(hesap);
      snackbar.success(PUSULA_KAYDEDILDI_ILETISI);
    } catch (err) {
      setHata(oturumHataMetni(err, PUSULA_HAZIRLANAMADI));
    } finally {
      setSurer(null);
      // Pusula satırı değiştirmez; ama ret (kaydı tutmayan hesap) satırın nedenini değiştirebilir.
      onDegisti();
    }
  }

  const eylemler: Array<{
    anahtar: string;
    durum: EylemDurumu;
    etiket: string;
    ikon: string;
    calisiyorEtiketi?: string;
    calisiyor?: boolean;
    onClick: () => void;
  }> = [
    {
      anahtar: "parola_sifirla",
      durum: e.parola_sifirla,
      etiket: DUGME_SIFIRLA,
      ikon: "lock_reset",
      onClick: () => onSifirla(hesap),
    },
    {
      anahtar: "askidan_cikar",
      durum: e.askidan_cikar,
      etiket: DUGME_ASKIDAN_CIKAR,
      ikon: "lock_open",
      calisiyorEtiketi: ASKIDAN_CIKARILIYOR,
      calisiyor: surer === "askidan_cikar",
      onClick: () => void askidanCikar(),
    },
    {
      anahtar: "pusula",
      durum: e.pusula,
      etiket: DUGME_PUSULA,
      ikon: "picture_as_pdf",
      calisiyorEtiketi: HAZIRLANIYOR,
      calisiyor: surer === "pusula",
      onClick: () => void pusula(),
    },
    {
      anahtar: "kapat",
      durum: e.kapat,
      etiket: DUGME_KAPAT,
      ikon: "person_off",
      onClick: () => onKapat(hesap),
    },
  ];
  // Dört eylem de aynı nedenle yapılamıyorsa neden bir kez yazılır (ör. kapalı hesap).
  const nedenler = new Set(eylemler.map((x) => (x.durum.yapilabilir ? null : x.durum.neden)));
  const ortakNeden =
    nedenler.size === 1 && eylemler.every((x) => !x.durum.yapilabilir && x.durum.neden)
      ? eylemler[0].durum.neden
      : null;

  return (
    <Dialog
      open
      wide
      onClose={onClose}
      title={AYRINTI_BASLIGI}
      actions={
        <Button variant="text" onClick={onClose}>
          Kapat
        </Button>
      }
    >
      <div className="flex flex-col gap-5">
        <dl className="flex flex-col gap-2">
          <Satir etiket={ETIKET_TANITICI}>
            <span className="font-mono">{hesap.tanitici}</span>
            {hesap.oturumdaki && <span className="text-on-surface-variant"> · {BU_OTURUM}</span>}
          </Satir>
          <Satir etiket={ETIKET_ROL}>{hesap.rol_etiketi}</Satir>
          <Satir etiket={ETIKET_HESAP_SAHIBI}>
            {hesap.ad_soyad === null ? <OkunamadiIsareti /> : hesap.ad_soyad}
          </Satir>
          <Satir etiket={ETIKET_DURUM}>{durumMetni(hesap)}</Satir>
          <Satir etiket={ETIKET_GIRIS}>
            {hesap.giris.yapabilir ? GIRIS_ACIK : (hesap.giris.neden ?? "—")}
          </Satir>
          <Satir etiket={ETIKET_ACILIS}>
            {ek ? anVeHesap(ek.acilis, "açan", ek.acan) : formatDateTime(hesap.acilis)}
          </Satir>
          {(hesap.kapanis !== null || ek?.kapatan) && (
            <Satir etiket={ETIKET_KAPANIS}>
              {ek ? anVeHesap(ek.kapanis, "kapatan", ek.kapatan) : formatDateTime(hesap.kapanis)}
            </Satir>
          )}
          {ek && (
            <>
              <Satir etiket={ETIKET_PAROLA_DEGISIMI}>{formatDateTime(ek.parola_degisimi)}</Satir>
              <Satir etiket={ETIKET_SIFIRLAMA}>{sifirlamaSatiri(ek.sifirlama)}</Satir>
            </>
          )}
        </dl>

        <section aria-label={ETIKET_SON_GIRISLER} className="flex flex-col gap-2">
          <h3 className="text-title-small text-on-surface">{ETIKET_SON_GIRISLER}</h3>
          {ayrinti.isPending ? (
            <Skeleton className="h-5 w-48" />
          ) : ayrinti.isError ? (
            <ErrorBand hata={oturumHataMetni(ayrinti.error, AYRINTI_OKUNAMADI)} />
          ) : ayrinti.data.son_girisler.length === 0 ? (
            <p className="text-body-medium text-on-surface-variant">{GIRIS_YOK}</p>
          ) : (
            <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
              {ayrinti.data.son_girisler.map((an, i) => (
                <li key={`${i}-${an}`}>{formatDateTime(an)}</li>
              ))}
            </ul>
          )}
        </section>

        <section aria-label={ETIKET_EYLEMLER} className="flex flex-col gap-3">
          <h3 className="text-title-small text-on-surface">{ETIKET_EYLEMLER}</h3>
          {eylemler.map((x) => (
            <EylemDugmesi
              key={x.anahtar}
              durum={x.durum}
              etiket={x.etiket}
              ikon={x.ikon}
              calisiyorEtiketi={x.calisiyorEtiketi}
              calisiyor={x.calisiyor}
              mesgul={surer !== null}
              onClick={x.onClick}
              ortakNedenId={ortakNeden !== null ? ortakNedenId : undefined}
            />
          ))}
          {ortakNeden !== null && (
            <p id={ortakNedenId} className="text-body-small text-on-surface-variant">
              {ortakNeden}
            </p>
          )}
          {hata && <ErrorBand hata={hata} />}
        </section>
      </div>
    </Dialog>
  );
}
