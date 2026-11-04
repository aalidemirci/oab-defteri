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
//   dosyasında hesap sarmalı yoktur, tasarım TK10) ya da listede seçilebilir satır
//   kalmayınca ("Kurtarma anahtarıyla aç"; plan F1b-2 "Kilit ekranı"): hesap
//   `GET security/recover/` listesinden seçilir.
// Kurtarma bir kerelik giriş değil parola yenilemedir: yeni parola politikaya uyar,
// kurtarma anahtarı bundan sonra da geçerli kalır. Başarıda pencere yeniden yüklenir
// (tasarım §13 D53; `oturum/eylemler`).
//
// Hata hangi alanınsa orada çıkar (ön denetim: hesap seçimi grubun, politika "Yeni
// parola"nın, eşleşmeme "Parola (tekrar)"ın altında); sunucunun reddi (çoğunlukla yanlış
// anahtar) formun genel uyarısıdır ve sunucunun iletisi olduğu gibi yazılır (hesap kaydı,
// parola kaydı ya da denetim izi değiştirilmiş görünüyorsa da; o kayıt reddinde iletinin
// altında zarfın üçüncü durumunun yol metni de durur, kullanıcı kararı 04.11.2026). Odak
// açılışta anahtar alanındadır; her retten sonra hatalı alana, sunucu reddinde anahtar
// alanına döner (alanlar istek sürerken kapalıydı).
//
// Çift gönderim yoktur (kilit ekranının kalıbı): istek sürerken ve açılıştan sonra ikinci
// gönderim `gonder`'in başında döner; koruma ref'tir, aynı olay döngüsündeki iki Enter'ı da
// keser.

import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import { SkeletonList } from "../../ui/Skeleton";
import TextField from "../../ui/TextField";
import { oturumApi } from "../oturum/api";
import type { KurtarmaHesabi } from "../oturum/api";
import { kurtarmaAnahtariylaAc } from "../oturum/eylemler";
import { kayitReddiMi, oturumHataMetni, oturumHatasi } from "../oturum/hatalar";
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

/**
 * Kurtarma listesi boşsa (açık bir program yöneticisi satırı yok): bu yolun sonu. Olağan
 * işleyişte açık bir program yöneticisi hep kalır (oturumdaki hesap kendini kapatamaz; askı
 * nedenleri organ hesaplarınındır), bu yüzden metin kayıtların değişmiş olabileceğini söyler;
 * çıkış zarfın üçüncü durumunun öteki çaresi, yedekten geri yüklemedir (kullanıcı kararı
 * 03.11.2026). Kilitliyken uygulama içi geri yükleme yoktur.
 */
export const KURTARILACAK_HESAP_YOK_METNI =
  "Bu kayıtlarda kurtarma anahtarıyla açılabilecek bir program yöneticisi hesabı bulunamadı. " +
  "Kayıtlar bozulmuş ya da program dışından değiştirilmiş olabilir: Denetleme Kuruluna " +
  "bildirin ve kayıtları yedekten geri yükleyin (programı kapatıp Windows'ta Başlat " +
  "menüsündeki “OAB Defteri — Yedekten Geri Yükle” kısayoluyla, Pardus'ta " +
  "oab-defteri --geri-yukle komutuyla).";

/**
 * Zarfın üçüncü durumunun yol metni (kullanıcı kararları 02.11.2026 ve 03.11.2026; sözler
 * `metinler.ZARFIN_UCUNCU_DURUMU` ve `metinler.UCUNCU_DURUMUN_CARESI` ile birebir). Denetleme
 * Kuruluna bildirim ister. Kilit ekranında seçilebilir satır kalmayınca yol gösterme
 * kutusunda, kilit ekranında ve kurtarma yolunda kayıt reddinden sonra iletinin altında durur
 * (`KayitReddiYolu`; kullanıcı kararı 04.11.2026). Kilitliyken uygulama içi geri yükleme yoktur
 * (oturum ister): yol Başlat menüsündeki kısayol ve Pardus'taki komuttur; ikisi çalışan
 * programla açılmaz (desktop `restore.RUNNING_MESSAGE`).
 */
export const UCUNCU_DURUM_YOL_METNI =
  "Kayıtlar bozulmuş ya da program dışından değiştirilmiş görünüyorsa (ör. satırda “Hesap " +
  "kaydı okunamadı” yazıyorsa) Denetleme Kuruluna bildirin. Bu, kurtarma anahtarı zarfının " +
  "üçüncü durumudur: bu bilgisayarın güvenlik dosyası ya da kayıtları kaybolduğunda, " +
  "bozulduğunda ya da program dışından değiştirildiğinde çare yedekten geri yükleme ya da " +
  "kurtarma anahtarıyla açılıştır. Yedekten geri yüklemek için programı kapatıp Windows'ta " +
  "Başlat menüsündeki “OAB Defteri — Yedekten Geri Yükle” kısayolunu, Pardus'ta " +
  "oab-defteri --geri-yukle komutunu kullanın.";

/**
 * Kayıt reddinden (`oturum/hatalar.kayitReddiMi`) sonra iletinin altındaki yol metni. Satırı
 * seçilebilir göründüğü hâlde girişi ve "Parolamı unuttum"u reddedilen program yöneticisinin
 * çıkışı yedekten geri yüklemedir; metin bunu söyler (yeni söz yok). Yalnız program yöneticisi
 * hesabında çizilir (kurtarma yolu zaten yalnız onundur) ve odağın döndüğü alana
 * `aria-describedby` ile bağlanır (`id`): ekran okuyucu yolu da okur.
 */
export function KayitReddiYolu({ id }: { id: string }) {
  return (
    <p
      id={id}
      className="rounded-shape-md bg-tertiary-container p-3 text-body-medium text-on-tertiary-container"
    >
      {UCUNCU_DURUM_YOL_METNI}
    </p>
  );
}

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
  const kayitYoluId = useId();
  const anahtarAlani = useRef<HTMLInputElement>(null);
  const yeniParolaAlani = useRef<HTMLInputElement>(null);
  const tekrarAlani = useRef<HTMLInputElement>(null);
  // Çift gönderim koruması (dosya başı notu).
  const gonderimSuruyor = useRef(false);
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
  // Sunucu reddi bir kayıt reddi mi? Öyleyse yol metni iletinin altında durur.
  const [kayitReddi, setKayitReddi] = useState(false);
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
    setKayitReddi(false);
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    if (gonderimSuruyor.current) return;
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
    gonderimSuruyor.current = true;
    setCalisiyor(true);
    try {
      await kurtarmaAnahtariylaAc({
        kurtarma_anahtari: anahtar,
        hesap: seciliId,
        yeni_parola: yeniParola,
      });
      // Pencere yeniden yükleniyor; o ana dek form kapalı kalır, koruma kalkmaz.
      setAcildi(true);
    } catch (err) {
      gonderimSuruyor.current = false;
      const { kod, metin } = oturumHatasi(err, "Kurtarma anahtarıyla açılamadı.");
      setHata(metin);
      setKayitReddi(kayitReddiMi(kod));
      odakIste("anahtar");
    } finally {
      setCalisiyor(false);
    }
  }

  const kapali = calisiyor || acildi;
  // Kayıt reddinin yol metni odağın döndüğü Kurtarma anahtarı alanını açıklar.
  const kayitYoluBagi = hata && kayitReddi ? kayitYoluId : undefined;

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
          {KURTARILACAK_HESAP_YOK_METNI}
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
        describedBy={kayitYoluBagi}
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
      {kayitYoluBagi && <KayitReddiYolu id={kayitYoluBagi} />}
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
