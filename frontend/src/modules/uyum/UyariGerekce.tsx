// Ortak "uyarı + gerekçe" bileşeni (plan F1c-11; CLAUDE.md altın kural 3; tasarım §5 O3, §6.1). Kalıcı
// uyarı bandı (`ui/UyariBandi`) DEĞİLDİR: o yalnız bilgi taşır, gerekçe almaz. Burada üç parça vardır:
//
// * `UyumSatiri` — bir uyum satırı (eksik · sapma · takvim): rozet, sunucunun kişisiz iletisi ve madde
//   atfı ("Dayanak: md. 12/4"). Eksik satır gerekçe istemez; sapma satırının gerekçesi alınmıştır.
// * `useUyariGerekce` — yazma akışının durumu: sunucu 400 `gerekce_gerekli` dönünce gerekçe kutusu
//   açılır, çağıran aynı isteği `gerekce` ile yeniden gönderir (`ek()`); gerekçe boşsa istek gitmez.
//   Toplu gerekçede (kök neden; O3) kök nedeni sunucu ya da çağıran koyar, kutu yalnız bunu söyler.
// * `UyariGerekceAlani` — gerekçe kutusu ya da sert engel, kural paketi (D1) ve dönem kilidi bandı.
//
// Gerekçe şifreli saklanır; ekranda yalnız yazılırken durur, geri okunmaz. Bağlam verilen kutuda yazılan
// metin YARIM METİN olarak kısa aralıklarla sunucuya yazılır (tasarım §7 "Yarım kalan metin"; hesap başına
// tek, şifreli kayıt; tarayıcı deposu değil): kayıt yapılınca ya da vazgeçilince silinir, aynı kutu yeniden
// açılınca metin geri gelir. Silme yalnız bu kutunun metnine dokunur: kutu bu oturumda yazmadıysa ya da
// metni geri getirmediyse silme gitmez, giden silme de kutunun bağlamıyla sınırlıdır (başka kutunun yarım
// metni kalır).
//
// Kutu açılınca odak gerekçe alanına geçer (görünür alana kaydırılır); alanın açıklaması uyarının metniyle
// ve dayanağıyla başlar, ekran okuyucu odakla birlikte okur (WCAG 4.1.3, 3.3.1).

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import { useAutosave } from "../../hooks/useAutosave";
import Icon from "../../ui/Icon";
import { yarimMetinApi } from "./api";
import type { UyumHatasi, UyumTuru } from "./hatalar";
import { uyumHatasiOku } from "./hatalar";
import {
  DAYANAK_ETIKETI,
  DONEM_KILIDI_BASLIGI,
  EKSIK_ACIKLAMASI,
  GEREKCE_BASLIGI,
  GEREKCE_ETIKETI,
  GEREKCE_YARDIMI,
  GEREKCE_ZORUNLU,
  KURAL_PAKETI_BASLIGI,
  KURAL_SERT_BASLIGI,
  SAPMA_ACIKLAMASI,
  SAPMA_GEREKCESIZ_ACIKLAMASI,
  TAKVIM_ACIKLAMASI,
  TOPLU_GEREKCE_NOTU,
  UYUM_EKSIK,
  UYUM_SAPMA,
  UYUM_TAKVIM,
} from "./metinler";

/** Uyum satırının ekrandaki verisi (kişisiz). */
export interface UyumSatiriVerisi {
  tur: UyumTuru;
  metin: string;
  atif?: string | null;
  /** Sapmanın gerekçesi alınmış mı? (Eksik ve takvim satırında anlamı yoktur.) */
  gerekceli?: boolean;
}

const TUR_ADI: Record<UyumTuru, string> = {
  EKSIK: UYUM_EKSIK,
  SAPMA: UYUM_SAPMA,
  TAKVIM: UYUM_TAKVIM,
};

const TUR_RENGI: Record<UyumTuru, string> = {
  EKSIK: "bg-secondary-container text-on-secondary-container",
  SAPMA: "bg-tertiary-container text-on-tertiary-container",
  TAKVIM: "bg-surface-container-highest text-on-surface-variant",
};

function turAciklamasi(satir: UyumSatiriVerisi): string {
  if (satir.tur === "EKSIK") return EKSIK_ACIKLAMASI;
  if (satir.tur === "TAKVIM") return TAKVIM_ACIKLAMASI;
  return satir.gerekceli === false ? SAPMA_GEREKCESIZ_ACIKLAMASI : SAPMA_ACIKLAMASI;
}

/** Madde atfı satırı ("Dayanak: md. 12/4"); `className` yazı boyutudur (varsayılan küçük yazı). */
export function Dayanak({
  atif,
  className = "text-body-small",
}: {
  atif: string | null | undefined;
  className?: string;
}) {
  if (!atif) return null;
  return (
    <span className={`${className} text-on-surface-variant`}>
      {DAYANAK_ETIKETI}: {atif}
    </span>
  );
}

/** Bir uyum satırı: rozet + ileti + dayanak (renk tek başına anlam taşımaz: rozet metni var). */
export function UyumSatiri({ satir }: { satir: UyumSatiriVerisi }) {
  return (
    <div className="flex min-w-0 flex-wrap items-start gap-x-3 gap-y-1 py-2">
      <span
        className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-label-medium ${TUR_RENGI[satir.tur]}`}
      >
        {TUR_ADI[satir.tur]}
      </span>
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="break-words text-body-medium text-on-surface">{satir.metin}</p>
        <p className="flex flex-wrap gap-x-3 text-body-small text-on-surface-variant">
          <span>{turAciklamasi(satir)}</span>
          <Dayanak atif={satir.atif} />
        </p>
      </div>
    </div>
  );
}

/** Satırların listesi (boşsa hiçbir şey çizmez). */
export function UyumSatirlari({
  satirlar,
  baslik,
}: {
  satirlar: readonly UyumSatiriVerisi[];
  /** Listenin erişilebilir adı. */
  baslik: string;
}) {
  if (satirlar.length === 0) return null;
  return (
    <ul aria-label={baslik} className="divide-y divide-outline-variant">
      {satirlar.map((satir, i) => (
        <li key={`${i}-${satir.metin}`}>
          <UyumSatiri satir={satir} />
        </li>
      ))}
    </ul>
  );
}

/** Yazma akışının uyarı + gerekçe durumu (dosya başı). */
export interface UyariGerekceDurumu {
  /** Son yazmanın uyum hatası (yoksa null). */
  hata: UyumHatasi | null;
  /** Gerekçe kutusu açık mı? (sunucu gerekçe istedi) */
  gerekceIstendi: boolean;
  gerekce: string;
  setGerekce: (metin: string) => void;
  /** Kutunun alan hatası ("Gerekçe yazın."). */
  alanHatasi: string | undefined;
  /** İsteğe eklenecek alan: gerekçe istendiyse `{ gerekce }`, değilse boş. */
  ek: () => { gerekce?: string };
  /** Gerekçe istendi ama boşsa alan hatasını yazar ve false döner (istek gitmez). */
  hazir: () => boolean;
  /** Hata bir uyum hatasıysa durumu kurar ve true döner; değilse false (çağıran gösterir). */
  yakala: (e: unknown) => boolean;
  /** Durumu temizler (başarılı kayıttan ya da vazgeçilince); yarım metin de silinir. */
  sifirla: () => void;
}

/**
 * `yarimMetinBaglami`: verilirse gerekçe kutusunun metni yarım metin olarak kaydedilir (dosya başı);
 * verilmezse kutu yalnız bellektedir.
 */
export function useUyariGerekce(yarimMetinBaglami?: string): UyariGerekceDurumu {
  const [hata, setHata] = useState<UyumHatasi | null>(null);
  const [gerekceIstendi, setGerekceIstendi] = useState(false);
  const [gerekce, setGerekceHam] = useState("");
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const baglam = yarimMetinBaglami ?? "";
  const yarimMetin = useAutosave<{ metin: string }>({
    save: (degisen) => yarimMetinApi.kaydet(degisen.metin ?? "", baglam),
    enabled: baglam !== "",
  });
  const { notifyChange, markSaved } = yarimMetin;
  // Kutu açılınca aynı bağlamın yarım metni (kullanıcı henüz yazmadıysa) geri getirilir.
  const yazildi = useRef(false);
  // Sunucudaki kayıt bu kutunun mu? (bu kutu yazdı ya da metni geri getirdi; dosya başı)
  const geriGeldi = useRef(false);
  useEffect(() => {
    if (!gerekceIstendi || baglam === "") return;
    let iptal = false;
    yarimMetinApi
      .oku()
      .then((taslak) => {
        if (!iptal && !yazildi.current && taslak !== null && taslak.baglam === baglam) {
          geriGeldi.current = true;
          setGerekceHam(taslak.metin);
        }
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, [gerekceIstendi, baglam]);

  const setGerekce = useCallback(
    (metin: string) => {
      yazildi.current = true;
      setGerekceHam(metin);
      setAlanHatasi(undefined);
      notifyChange({ metin });
    },
    [notifyChange],
  );

  const ek = useCallback(
    () => (gerekceIstendi && gerekce.trim() ? { gerekce: gerekce.trim() } : {}),
    [gerekceIstendi, gerekce],
  );

  const hazir = useCallback(() => {
    if (gerekceIstendi && !gerekce.trim()) {
      setAlanHatasi(GEREKCE_ZORUNLU);
      return false;
    }
    return true;
  }, [gerekceIstendi, gerekce]);

  const yakala = useCallback((e: unknown) => {
    const okunan = uyumHatasiOku(e);
    setHata(okunan);
    if (okunan === null) return false;
    // Gerekçe kutusu bir kez açılınca kayıt tamamlanana dek açık kalır (sonraki ret başka türden olsa
    // da yazılan gerekçe kaybolmaz).
    if (okunan.tur === "gerekce") setGerekceIstendi(true);
    return true;
  }, []);

  const sifirla = useCallback(() => {
    setHata(null);
    setGerekceIstendi(false);
    setGerekceHam("");
    setAlanHatasi(undefined);
    // Bu kutu yazmadıysa ya da metni geri getirmediyse sunucudaki kayıt başka kutunundur: silinmez.
    const sil = yazildi.current || geriGeldi.current;
    yazildi.current = false;
    geriGeldi.current = false;
    if (baglam !== "") {
      markSaved(); // bekleyen yazma iptal edilir
      if (sil) yarimMetinApi.temizle(baglam).catch(() => undefined);
    }
  }, [baglam, markSaved]);

  return useMemo(
    () => ({ hata, gerekceIstendi, gerekce, setGerekce, alanHatasi, ek, hazir, yakala, sifirla }),
    [hata, gerekceIstendi, gerekce, setGerekce, alanHatasi, ek, hazir, yakala, sifirla],
  );
}

const BANT_BASLIGI: Record<Exclude<UyumHatasi["tur"], "gerekce">, string> = {
  sert: KURAL_SERT_BASLIGI,
  paket: KURAL_PAKETI_BASLIGI,
  donem: DONEM_KILIDI_BASLIGI,
};

/** Sert engel, kural paketi (D1) ve dönem kilidi bandı (`role="alert"`). */
export function UyumHataBandi({ hata }: { hata: UyumHatasi }) {
  if (hata.tur === "gerekce") return null;
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-shape-sm bg-error-container px-4 py-3 text-on-error-container"
    >
      <Icon name={hata.tur === "sert" ? "block" : "error"} size="lg" className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-label-large">{BANT_BASLIGI[hata.tur]}</p>
        <p className="break-words text-body-medium">{hata.metin}</p>
        {hata.atif && (
          <p className="text-body-small">
            {DAYANAK_ETIKETI}: {hata.atif}
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * Yazma formunun uyarı + gerekçe alanı: gerekçe istendiyse uyarı ve gerekçe kutusu, öteki uyum
 * hatalarında bant. Hata yoksa hiçbir şey çizmez.
 */
export function UyariGerekceAlani({
  durum,
  toplu = false,
}: {
  durum: UyariGerekceDurumu;
  /** Gerekçe toplu mu (aynı kök nedene bağlı kayıtlar; O3)? Kutunun altında not durur. */
  toplu?: boolean;
}) {
  const kimlik = useId();
  const alanRef = useRef<HTMLTextAreaElement>(null);
  const { hata, gerekceIstendi } = durum;
  // Kutu açılınca odak gerekçe alanına geçer: kutu kaydırılan diyalog gövdesinin görünmeyen yerinde de
  // olsa görünür alana gelir, ekran okuyucu uyarıyı alanın açıklamasıyla okur (dosya başı).
  useEffect(() => {
    if (!gerekceIstendi) return;
    alanRef.current?.focus();
    alanRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [gerekceIstendi]);
  if (!gerekceIstendi) return hata ? <UyumHataBandi hata={hata} /> : null;
  // Kutu açıkken gelen sonraki uyum hatası (ör. başka bir kuralın gerekçesi) bandın metnini yeniler.
  const uyari = hata?.tur === "gerekce" ? hata : null;
  const uyariId = `${kimlik}-uyari`;
  const yardimId = `${kimlik}-yardim`;
  const hataId = `${kimlik}-hata`;
  const aciklamaIdleri = [uyari && uyariId, durum.alanHatasi && hataId, yardimId]
    .filter(Boolean)
    .join(" ");
  return (
    <div className="space-y-3">
      {hata && hata.tur !== "gerekce" && <UyumHataBandi hata={hata} />}
      <div
        role="group"
        aria-labelledby={`${kimlik}-baslik`}
        className="space-y-3 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
      >
        <div className="flex items-start gap-3">
          <Icon name="warning" size="lg" className="mt-0.5 shrink-0" />
          <div className="min-w-0 flex-1 space-y-1">
            <p id={`${kimlik}-baslik`} className="text-label-large">
              {GEREKCE_BASLIGI}
            </p>
            {uyari && (
              <div id={uyariId} className="space-y-1">
                <p className="break-words text-body-medium">{uyari.metin}</p>
                {uyari.atif && (
                  <p className="text-body-small">
                    {DAYANAK_ETIKETI}: {uyari.atif}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
        <div>
          <label htmlFor={`${kimlik}-alan`} className="mb-1 block text-label-medium font-semibold">
            {GEREKCE_ETIKETI}
            <span className="text-error"> *</span>
          </label>
          <textarea
            ref={alanRef}
            id={`${kimlik}-alan`}
            rows={3}
            maxLength={1000}
            value={durum.gerekce}
            onChange={(e) => durum.setGerekce(e.target.value)}
            aria-invalid={durum.alanHatasi ? true : undefined}
            aria-describedby={aciklamaIdleri}
            className="block w-full rounded-shape-xs border border-outline bg-surface px-3 py-2 text-body-medium text-on-surface outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
          />
          {durum.alanHatasi && (
            <p id={hataId} role="alert" className="mt-1 text-body-small text-error">
              {durum.alanHatasi}
            </p>
          )}
          <p id={yardimId} className="mt-1 text-body-small">
            {GEREKCE_YARDIMI}
            {toplu && ` ${TOPLU_GEREKCE_NOTU}`}
          </p>
        </div>
      </div>
    </div>
  );
}
