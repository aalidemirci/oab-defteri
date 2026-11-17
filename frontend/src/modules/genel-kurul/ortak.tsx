// Genel Kurul ekranlarının ortak parçaları: uyarı + gerekçe akışlı yazma penceresi (F1c'nin ortak
// bileşeni `uyum/UyariGerekce`), sayı ve gün-saat alanları, bilgi satırları, kural özetleri, kullanıcı
// eklerinin listesi (indirme ve ekleme) ve dosya kaydetmenin ortak sonucu.
//
// Gün-saat: ekran `datetime-local` alanıyla yerel saati alır; gövdeye Europe/Istanbul farkıyla (+03:00)
// gider. Sunucu anı yerel farkıyla döndürür (`timezone.localtime(...).isoformat()`): alanın değeri ilk
// on altı karakterdir.

import { useRef, useState } from "react";
import type { ReactNode } from "react";

import { saveBlob } from "../../lib/download";
import { formatBoyut, formatDateTime } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { Dayanak, UyariGerekceAlani, useUyariGerekce } from "../uyum/UyariGerekce";
import { atifAyir } from "../uyum/hatalar";
import { GEREKCEYLE_KAYDET } from "../uyum/metinler";
import { ekYedekDosyaAdi, genelKurulApi } from "./api";
import type { Ek, GerekceEki, KuralOzeti } from "./api";
import {
  BILGILER_BASLIGI,
  DOSYA_SECIN,
  DUGME_DOSYA_EKLE,
  DUGME_EKI_KAYDET,
  DUGME_VAZGEC,
  EK_ADI_OKUNAMADI,
  EK_EKLENDI,
  EK_EKLENEMEDI,
  EK_KAYDEDILDI,
  EK_KAYDEDILEMEDI,
  EK_YOK,
  KAYDEDILIYOR,
} from "./metinler";

/** Europe/Istanbul'un sabit farkı (2016'dan beri yaz saati yok). */
const YEREL_FARK = "+03:00";

/** `datetime-local` değeri → sunucunun anı ("2026-10-20T10:00" → "2026-10-20T10:00:00+03:00"). */
export function yerelAn(deger: string): string {
  return `${deger}:00${YEREL_FARK}`;
}

/** Sunucunun anı → `datetime-local` değeri (yerel farkla döner; ilk on altı karakter). */
export function alanAni(an: string | null): string {
  return an ? an.slice(0, 16) : "";
}

/** Sayı alanının değeri: boş → null; sıfır ya da pozitif tam sayı değilse "gecersiz". */
export function sayiOku(metin: string): number | null | "gecersiz" {
  const temiz = metin.trim();
  if (temiz === "") return null;
  if (!/^\d+$/.test(temiz)) return "gecersiz";
  return Number(temiz);
}

/** Sıfır ya da pozitif tam sayı alanı (metin olarak tutulur; boş bırakılabilir). */
export function SayiAlani({
  etiket,
  deger,
  onDegis,
  yardim,
  hata,
  zorunlu = false,
}: {
  etiket: string;
  deger: string;
  onDegis: (metin: string) => void;
  yardim?: string;
  hata?: string;
  zorunlu?: boolean;
}) {
  return (
    <TextField
      label={etiket}
      inputMode="numeric"
      value={deger}
      required={zorunlu}
      onChange={(e) => onDegis(e.target.value)}
      helperText={yardim}
      error={hata}
    />
  );
}

/** Sunucunun bilgi satırları (kişisiz; madde atfı ayrı satırda). */
export function BilgiSatirlari({
  bilgiler,
  baslik = BILGILER_BASLIGI,
}: {
  bilgiler: readonly string[];
  baslik?: string;
}) {
  if (bilgiler.length === 0) return null;
  return (
    <ul
      aria-label={baslik}
      className="space-y-2 rounded-shape-sm bg-secondary-container px-4 py-3 text-on-secondary-container"
    >
      {bilgiler.map((b) => {
        const { govde, atif } = atifAyir(b);
        return (
          <li key={b} className="flex items-start gap-2">
            <Icon name="info" size="lg" className="mt-0.5 shrink-0" />
            <span className="min-w-0 break-words text-body-medium">
              <span>{govde}</span>
              {atif && (
                <span className="block">
                  <Dayanak atif={atif} className="text-body-small" />
                </span>
              )}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

/** Kuralların açık uyarıları ve eksikleri (kişisiz, atıflı; kaydedilmez, gerekçe istemez). Görünümü
 * Birlik Dönemi'nin atıflı uyarı listesiyle aynıdır. */
export function KuralUyarilari({
  satirlar,
  baslik,
}: {
  satirlar: readonly KuralOzeti[];
  baslik: string;
}) {
  if (satirlar.length === 0) return null;
  return (
    <ul
      aria-label={baslik}
      className="space-y-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
    >
      {satirlar.map((s) => {
        const { govde } = atifAyir(s.mesaj);
        return (
          <li key={`${s.kural}-${s.mesaj}`} className="flex items-start gap-2">
            <Icon name="warning" size="lg" className="mt-0.5 shrink-0" />
            <span className="min-w-0 space-y-0.5">
              <span className="block break-words text-body-medium">{govde}</span>
              <Dayanak atif={s.atif} />
            </span>
          </li>
        );
      })}
    </ul>
  );
}

/**
 * Uyarı + gerekçe akışlı yazma penceresi: sunucu 400 `gerekce_gerekli` dönünce gerekçe kutusu açılır,
 * aynı istek gerekçeyle yinelenir; sert engel ve dönem kilidi bantla, öteki retler hata bandıyla
 * gösterilir. `onGonder` başarılıysa pencereyi çağıran kapatır.
 */
export function YazmaPenceresi({
  baslik,
  dugme,
  yedekHata,
  baglam,
  onGonder,
  onKapat,
  children,
  dogrula,
  genis = false,
  ikon = "save",
}: {
  baslik: string;
  dugme: string;
  yedekHata: string;
  /** Gerekçe kutusunun yarım metin bağlamı (kişisiz kutu adı). */
  baglam: string;
  onGonder: (ek: GerekceEki) => Promise<void>;
  onKapat: () => void;
  children: ReactNode;
  /** Gönderimden önceki alan denetimi; false dönerse istek gitmez. */
  dogrula?: () => boolean;
  genis?: boolean;
  ikon?: string;
}) {
  const ug = useUyariGerekce(baglam);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const vazgec = () => {
    ug.sifirla();
    onKapat();
  };

  const gonder = async () => {
    if (dogrula && !dogrula()) return;
    if (!ug.hazir()) return;
    setBusy(true);
    setHata(null);
    try {
      await onGonder(ug.ek());
      ug.sifirla();
    } catch (e) {
      if (!ug.yakala(e)) setHata(hataOku(e, yedekHata));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={vazgec}
      title={baslik}
      wide={genis}
      actions={
        <>
          <Button variant="text" onClick={vazgec} disabled={busy}>
            {DUGME_VAZGEC}
          </Button>
          <Button icon={ikon} onClick={() => void gonder()} disabled={busy}>
            {busy ? KAYDEDILIYOR : ug.gerekceIstendi ? GEREKCEYLE_KAYDET : dugme}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {hata && <ErrorBand hata={hata} />}
        <UyariGerekceAlani durum={ug} />
        {children}
      </div>
    </Dialog>
  );
}

/**
 * Kaydetme sonucu: dosya yazılamadıysa hata, iptalde sessiz, kaydedilince bildirim. `saveBlob`'un
 * sarmalayıcısıdır: önerilen ad (uzantısıyla) çağıranda kurulur, süzgeç taraması
 * (`desktop/tests/test_kayit_suzgecleri.py`) adı çağrı yerinden çözer.
 */
export async function dosyayiKaydet(
  blob: Blob,
  ad: string,
  basari: string,
  snackbar: { success: (m: string) => void; error: (m: string) => void },
): Promise<void> {
  const sonuc = await saveBlob(blob, ad);
  if (sonuc === "hata") snackbar.error(DOSYA_YAZILAMADI_ILETISI);
  else if (sonuc !== "iptal") snackbar.success(basari);
}

/**
 * Kullanıcı eklerinin listesi: her ek indirilir (adı sunucunun: belge adı + gün; özgün ad yalnız
 * satırda görünür). `onEkle` verilirse dosya seçilip eklenir (PDF, JPEG, PNG; tür ve boy sunucuda).
 */
export function EkListesi({
  ekler,
  onEkle,
  baslik,
  yardim,
}: {
  ekler: readonly Ek[];
  onEkle?: (dosya: File) => Promise<void>;
  baslik: string;
  yardim?: string;
}) {
  const snackbar = useSnackbar();
  const girdi = useRef<HTMLInputElement>(null);
  const [secili, setSecili] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const indir = async (ek: Ek) => {
    try {
      const { blob, ad } = await genelKurulApi.ekIndir(ek.id);
      await dosyayiKaydet(blob, ad ?? ekYedekDosyaAdi(ek), EK_KAYDEDILDI, snackbar);
    } catch (e) {
      snackbar.error(hataOku(e, EK_KAYDEDILEMEDI).message);
    }
  };

  const ekle = async () => {
    if (!onEkle) return;
    if (secili === null) {
      setHata({ message: DOSYA_SECIN, parolaGerekli: false });
      return;
    }
    setBusy(true);
    setHata(null);
    try {
      await onEkle(secili);
      setSecili(null);
      if (girdi.current) girdi.current.value = "";
      snackbar.success(EK_EKLENDI);
    } catch (e) {
      setHata(hataOku(e, EK_EKLENEMEDI));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-2">
      <p className="text-label-large text-on-surface">{baslik}</p>
      {yardim && <p className="text-body-small text-on-surface-variant">{yardim}</p>}
      {ekler.length === 0 ? (
        <p className="text-body-medium text-on-surface-variant">{EK_YOK}</p>
      ) : (
        <ul aria-label={baslik} className="divide-y divide-outline-variant">
          {ekler.map((ek) => (
            <li key={ek.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <span className="min-w-0 break-words text-body-medium text-on-surface">
                {ek.ad ?? EK_ADI_OKUNAMADI}
                <span className="block text-body-small text-on-surface-variant">
                  {formatDateTime(ek.yukleme_zamani)} · {formatBoyut(ek.boyut)}
                </span>
              </span>
              <Button
                variant="text"
                icon="download"
                aria-label={`${ek.ad ?? EK_ADI_OKUNAMADI} dosyasını kaydet`}
                onClick={() => void indir(ek)}
              >
                {DUGME_EKI_KAYDET}
              </Button>
            </li>
          ))}
        </ul>
      )}
      {onEkle && (
        <div className="space-y-2">
          {hata && <ErrorBand hata={hata} />}
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={girdi}
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              aria-label={`${baslik}: ${DUGME_DOSYA_EKLE}`}
              className="min-w-0 max-w-full text-body-small text-on-surface"
              onChange={(e) => setSecili(e.target.files?.[0] ?? null)}
            />
            <Button variant="tonal" icon="attach_file" disabled={busy} onClick={() => void ekle()}>
              {busy ? KAYDEDILIYOR : DUGME_DOSYA_EKLE}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

/** Bölüm: başlık + içerik (Başlık Düzeni; sözlük §3). */
export function Bolum({
  baslik,
  aciklama,
  eylem,
  children,
}: {
  baslik: string;
  aciklama?: string;
  eylem?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-title-small text-on-surface">{baslik}</h3>
          {aciklama && <p className="text-body-small text-on-surface-variant">{aciklama}</p>}
        </div>
        {eylem && <div className="flex flex-wrap gap-2">{eylem}</div>}
      </div>
      {children}
    </section>
  );
}

/** Tanım listesinin satırı. */
export function Bilgi({ etiket, children }: { etiket: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-label-medium text-on-surface-variant">{etiket}</dt>
      <dd className="break-words text-body-medium text-on-surface">{children}</dd>
    </div>
  );
}
