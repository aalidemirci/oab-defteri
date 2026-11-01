// Kurtarma anahtarıyla açılış — kilit ekranının "Parolamı unuttum" yolu (tasarım §4.4.3,
// §4.4.4; plan F1b-1 "Sıra ve sınır"). YALNIZ program yöneticisi içindir: var olan bir
// program yöneticisi hesabının parolası yenilenir ve oturum o hesapla açılır; başka rolün
// hesabı bu yolla açılmaz (backend de reddeder). Yeni program yöneticisi hesabı açan kol
// (müdür yardımcısı değişimi) F4'tedir.
//
// İki giriş:
// * Kilit ekranında bir program yöneticisi hesabı seçiliyken "Parolamı unuttum": hesap
//   bellidir (`hesap`).
// * Kilit ekranının listesi boşken (kayıtlar kurtarma anahtarıyla geri yüklendi; güvenlik
//   dosyasında hesap sarmalı yoktur, tasarım TK10): hesap `GET security/recover/`
//   listesinden seçilir.
// Kurtarma bir kerelik giriş değil parola yenilemedir: yeni parola politikaya uyar,
// kurtarma anahtarı bundan sonra da geçerli kalır. Başarıda pencere yeniden yüklenir
// (tasarım §13 D53; `oturum/eylemler`).
//
// Hata hangi alanınsa orada çıkar (ön denetim: hesap seçimi grubun, politika "Yeni
// parola"nın, eşleşmeme "Parola (tekrar)"ın altında); sunucunun reddi (çoğunlukla yanlış
// anahtar) formun genel uyarısıdır. Odak açılışta anahtar alanındadır; her retten sonra
// hatalı alana, sunucu reddinde anahtar alanına döner (alanlar istek sürerken kapalıydı).

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import { SkeletonList } from "../../ui/Skeleton";
import TextField from "../../ui/TextField";
import { oturumApi } from "../oturum/api";
import type { KurtarmaHesabi } from "../oturum/api";
import { kurtarmaAnahtariylaAc } from "../oturum/eylemler";
import { oturumHataMetni } from "../oturum/hatalar";
import { yeniParolaHatalari } from "../oturum/parolaPolitikasi";
import YeniParolaAlanlari from "../oturum/YeniParolaAlanlari";
import HesapSecimi from "./HesapSecimi";
import type { HesapSecenegi } from "./HesapSecimi";

/** Bekleme durumunun metni (kurtarma denemelerinin gecikmesi süreç içidir; plan F1b-1). */
export const DENETLENIYOR_METNI =
  "Denetleniyor… Yanlış denemelerden sonra yanıt birkaç saniye gecikebilir.";

/** Kurtarma yolunun açıklaması (sözlük §1 "Kurtarma anahtarı"). */
export const KURTARMA_YOLU_METNI =
  "Kurtarma anahtarı okul müdürlüğünde kapalı zarfta saklanan kâğıttadır. Anahtarla " +
  "program yöneticisi hesabının parolası yenilenir; anahtar bundan sonra da geçerli kalır.";

/** Kurtarma listesinde birden çok hesap varken seçilmeden gönderilince. */
export const YONETICI_SECIN_ILETISI = "Program yöneticisi hesabını seçin.";

interface KurtarmaIleAcmaProps {
  /** Kilit ekranında seçili program yöneticisi hesabı; null: hesap kurtarma listesinden seçilir. */
  hesap: HesapSecenegi | null;
  /** "Parolayla açmaya dön" (liste boşken verilmez: dönülecek parola yolu yoktur). */
  onVazgec?: () => void;
}

type OdakHedefi = "anahtar" | "hesap" | "yeni" | "tekrar";

function secenek(h: KurtarmaHesabi): HesapSecenegi {
  return {
    id: h.id,
    rolEtiketi: h.rol_etiketi,
    tanitici: h.tanitici,
    secilebilir: true,
    not: null,
  };
}

export default function KurtarmaIleAcma({ hesap, onVazgec }: KurtarmaIleAcmaProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const anahtarAlani = useRef<HTMLInputElement>(null);
  const yeniParolaAlani = useRef<HTMLInputElement>(null);
  const tekrarAlani = useRef<HTMLInputElement>(null);
  const [liste, setListe] = useState<HesapSecenegi[] | null>(hesap ? [hesap] : null);
  const [listeHatasi, setListeHatasi] = useState<string | null>(null);
  const [seciliId, setSeciliId] = useState<string | null>(hesap?.id ?? null);
  const [anahtar, setAnahtar] = useState("");
  const [yeniParola, setYeniParola] = useState("");
  const [tekrar, setTekrar] = useState("");
  const [hesapHatasi, setHesapHatasi] = useState<string | null>(null);
  const [yeniHatasi, setYeniHatasi] = useState<string | null>(null);
  const [tekrarHatasi, setTekrarHatasi] = useState<string | null>(null);
  const [hata, setHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);
  const [acildi, setAcildi] = useState(false);
  // Odak isteği (dosya başı notu): ilk değer açılıştaki anahtar alanıdır.
  const [odak, setOdak] = useState<{ n: number; hedef: OdakHedefi }>({ n: 0, hedef: "anahtar" });

  // Hesap kilit ekranında seçili değilse (liste boş) kurtarma listesi okunur.
  const listeOkunacak = hesap === null;
  useEffect(() => {
    if (!listeOkunacak) return;
    let iptal = false;
    oturumApi
      .kurtarmaHesaplari()
      .then((satirlar) => {
        if (iptal) return;
        setListe(satirlar.map(secenek));
        if (satirlar.length === 1) setSeciliId(satirlar[0].id);
      })
      .catch((err: unknown) => {
        if (!iptal) setListeHatasi(oturumHataMetni(err, "Hesap listesi okunamadı."));
      });
    return () => {
      iptal = true;
    };
  }, [listeOkunacak]);

  useEffect(() => {
    const hedefler: Record<OdakHedefi, () => HTMLElement | null> = {
      anahtar: () => anahtarAlani.current,
      hesap: () =>
        formRef.current?.querySelector<HTMLInputElement>('input[type="radio"]:not(:disabled)') ??
        null,
      yeni: () => yeniParolaAlani.current,
      tekrar: () => tekrarAlani.current,
    };
    hedefler[odak.hedef]()?.focus();
  }, [odak]);

  function odakIste(hedef: OdakHedefi) {
    setOdak((o) => ({ n: o.n + 1, hedef }));
  }

  function hatalariSil() {
    setHesapHatasi(null);
    setYeniHatasi(null);
    setTekrarHatasi(null);
    setHata(null);
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    hatalariSil();
    if (!seciliId) {
      setHesapHatasi(YONETICI_SECIN_ILETISI);
      odakIste("hesap");
      return;
    }
    const sorun = yeniParolaHatalari(yeniParola, tekrar);
    if (sorun.yeni || sorun.tekrar) {
      setYeniHatasi(sorun.yeni);
      setTekrarHatasi(sorun.tekrar);
      odakIste(sorun.yeni ? "yeni" : "tekrar");
      return;
    }
    setCalisiyor(true);
    try {
      await kurtarmaAnahtariylaAc({
        kurtarma_anahtari: anahtar,
        hesap: seciliId,
        yeni_parola: yeniParola,
      });
      // Pencere yeniden yükleniyor; o ana dek form kapalı kalır.
      setAcildi(true);
    } catch (err) {
      setHata(oturumHataMetni(err, "Kurtarma anahtarıyla açılamadı."));
      odakIste("anahtar");
    } finally {
      setCalisiyor(false);
    }
  }

  const kapali = calisiyor || acildi;

  return (
    <form
      ref={formRef}
      onSubmit={gonder}
      className="flex flex-col gap-4"
      aria-label="Kurtarma yolu"
    >
      <p className="text-body-medium text-on-surface-variant">{KURTARMA_YOLU_METNI}</p>

      {liste === null && listeHatasi === null && <SkeletonList rows={1} />}
      {listeHatasi && (
        <p role="alert" className="text-body-medium text-error">
          {listeHatasi}
        </p>
      )}
      {liste !== null && liste.length === 0 && (
        <p role="alert" className="text-body-medium text-error">
          Bu kayıtlarda kurtarma anahtarıyla açılabilecek bir program yöneticisi hesabı bulunamadı.
        </p>
      )}
      {liste !== null && liste.length > 0 && (
        <HesapSecimi
          secenekler={liste}
          seciliId={seciliId}
          onSec={(id) => {
            setSeciliId(id);
            hatalariSil();
          }}
          onEnter={() => anahtarAlani.current?.focus()}
          disabled={kapali}
          hata={hesapHatasi}
        />
      )}

      <TextField
        ref={anahtarAlani}
        label="Kurtarma anahtarı"
        value={anahtar}
        onChange={(e) => setAnahtar(e.target.value)}
        autoComplete="off"
        spellCheck={false}
        placeholder="ABCD-EFGH-…"
        disabled={kapali}
        required
      />
      <YeniParolaAlanlari
        ref={yeniParolaAlani}
        tekrarRef={tekrarAlani}
        yeniParola={yeniParola}
        onYeniParola={setYeniParola}
        tekrar={tekrar}
        onTekrar={setTekrar}
        yeniHata={yeniHatasi}
        tekrarHata={tekrarHatasi}
        disabled={kapali}
      />

      {hata && (
        <p role="alert" className="text-body-medium text-error">
          {hata}
        </p>
      )}
      {calisiyor && (
        <p role="status" className="text-body-small text-on-surface-variant">
          {DENETLENIYOR_METNI}
        </p>
      )}

      <Button type="submit" disabled={kapali || liste === null || liste.length === 0} block>
        {kapali ? "Açılıyor…" : "Kurtar ve aç"}
      </Button>
      {onVazgec && (
        <div className="flex justify-center">
          <Button variant="text" type="button" onClick={onVazgec} disabled={kapali}>
            Parolayla açmaya dön
          </Button>
        </div>
      )}
    </form>
  );
}
