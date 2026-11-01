// Kilit ekranı — hesap kuruluyken programın ilk yüzü (tasarım §4.4.3; plan F1b-1 "Oturum").
// Herkes programı KENDİ hesabıyla açar: ekran açık hesapları listeler, kullanıcı hesabını
// seçer ve parolasını yazar; yalnız o hesabın sarmalı denenir.
//
// * Liste `GET security/accounts/`tan gelir (kişi adı yok). Satır rol etiketi + tanıtıcıdır
//   (`HesapSecimi`). Askıdaki hesap (hatalı deneme askısı ya da üyelik/görev askısı)
//   "askıda — program yöneticisine başvurun" der, kaydı okunamayan satır "Hesap kaydı
//   okunamadı" der; ikisi de seçilemez. Tek seçilebilir hesap varsa İLK yüklemede seçili
//   gelir; liste sonradan tazelenince (askıdan sonra) başka bir hesap kendiliğinden
//   SEÇİLMEZ — seçilseydi askıya alınan kişinin yazdığı parola o hesaba hatalı deneme
//   diye sayılırdı.
// * Başka hesap seçilince önceki hata silinir (sayaç hesap başınadır; tasarım §4.3
//   tehdit 11). Hatalı denemenin gecikmesini (0/0/1/2/4 sn) backend uygular; o sürede
//   ekran "Denetleniyor…" der ve form kapalıdır.
// * Onuncu hatalı denemede (403 `hesap_askida`) seçim bırakılır, ileti hesap grubunun
//   altında kalır ve liste tazelenir: satır artık seçilemez.
// * 409 `parola_yenilenmeli` (geçici ya da 180 günü dolmuş parola): oturum açılmadan,
//   aynı ekranda yeni parola + tekrarı istenir ve kilit açma `yeni_parola` ile yinelenir.
//   Gerekçe kutusu "Yeni parola" alanına `aria-describedby` ile bağlıdır: odak alana
//   geçince ekran okuyucu nedenini de okur.
// * "Parolamı unuttum" yalnız program yöneticisi hesabı seçiliyken vardır (kurtarma
//   anahtarı yalnız onun içindir); öteki hesaplarda metin program yöneticisine yönlendirir.
//   Liste boşsa (kurtarma anahtarıyla geri yükleme sonrası; tasarım TK10) kurtarma yolu
//   doğrudan açılır ve hesap kurtarma listesinden seçilir (`KurtarmaIleAcma`).
// * Açılış (kilit açma ya da kurtarma) pencereyi yeniden yükler (tasarım §13 D53;
//   `oturum/eylemler`): önceki hesabın belleği yeni oturuma kalmaz.
//
// Hata hangi alanınsa orada çıkar: "Parola hatalı." Parola alanının, "Hesabınızı seçin."
// ve askı iletisi hesap grubunun, yeni parolanın reddi "Yeni parola"nın, eşleşmeme
// "Parola (tekrar)"ın altında; hesaba ya da alana bağlı olmayan ret (hesap mührü, iki depo,
// ağ) formun genel uyarısıdır. Odak her retten ve her geri dönüşten ("Vazgeç", "Parolayla
// açmaya dön") sonra forma döner: hesap seçiliyse Parola alanına, değilse ilk seçilebilir
// satıra (bu ekran kabuğun içinde çizilir; odak sayfa gövdesine düşerse klavye kullanıcısı
// kenar çubuğunu dolaşmak zorunda kalırdı).
// Hata kodları kullanıcı metnine çıkmaz (`oturum/hatalar`).

import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useDurumBasligi } from "../../ui/DurumBasligi";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import TextField from "../../ui/TextField";
import { oturumApi } from "../oturum/api";
import type { KilitEkraniHesabi } from "../oturum/api";
import { kilidiAc } from "../oturum/eylemler";
import { dogrulamaReddiMi, oturumHatasi } from "../oturum/hatalar";
import { yeniParolaHatalari } from "../oturum/parolaPolitikasi";
import YeniParolaAlanlari from "../oturum/YeniParolaAlanlari";
import HesapSecimi from "./HesapSecimi";
import type { HesapSecenegi } from "./HesapSecimi";
import KurtarmaIleAcma, { DENETLENIYOR_METNI } from "./KurtarmaIleAcma";
import { KAPSAM_METNI } from "./metinler";

/** Ekranın h1'i — üst çubukta da bu yazar (docs/sozluk.md §4.2). */
export const KILIT_EKRANI_BASLIGI = "Kayıtlar kilitli";

/** Askıdaki hesabın etiketi (iki askı kaynağı da; sözlük §1 "Hesap"). */
export const ASKIDA_ETIKETI = "askıda — program yöneticisine başvurun";
/** Rolü veritabanından okunamayan satır (backend `oturum.ROL_OKUNAMADI_ETIKETI`). */
export const OKUNAMADI_ETIKETI = "Hesap kaydı okunamadı";
/** Program yöneticisi olmayan hesap seçiliyken parolasını unutan kişiye. */
export const UNUTTUM_BASKA_ROL_METNI = "Parolanızı unuttuysanız program yöneticisine başvurun.";
/** Hesap seçilmeden gönderilince hesap grubunun altında. */
export const HESAP_SECIN_ILETISI = "Hesabınızı seçin.";
/** Liste boşken kurtarma yolunun gerekçesi. */
export const BOS_LISTE_METNI =
  "Bu bilgisayarın güvenlik dosyasında hesap parolası yok: kayıtlar kurtarma anahtarıyla " +
  "geri yüklendiyse böyledir. Program yöneticisi kurtarma anahtarıyla açar ve yeni " +
  "parolasını belirler; öteki hesaplar program yöneticisine başvurur.";

/** Kilit ekranı satırı → seçim satırı (seçilemezliğin nedeni metne çevrilir). */
export function hesapSecenegi(h: KilitEkraniHesabi): HesapSecenegi {
  const okunamadi = h.rol === null;
  let not: string | null = null;
  if (h.askida_nedeni !== null) not = ASKIDA_ETIKETI;
  else if (!okunamadi && !h.secilebilir) not = "giriş kapalı — program yöneticisine başvurun";
  return {
    id: h.id,
    rolEtiketi: okunamadi ? OKUNAMADI_ETIKETI : h.rol_etiketi,
    tanitici: h.tanitici,
    secilebilir: h.secilebilir && !okunamadi,
    not,
  };
}

type Kip = "parola" | "yenile" | "kurtarma";

/** Odak isteği: `n` her istekte artar; `tekrar` eşleşmeme reddinde tekrar alanına götürür. */
interface OdakIstegi {
  n: number;
  tekrar: boolean;
}

export default function KilitEkrani() {
  useDurumBasligi(KILIT_EKRANI_BASLIGI);
  const parolaAlani = useRef<HTMLInputElement>(null);
  const yeniParolaAlani = useRef<HTMLInputElement>(null);
  const tekrarAlani = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const bilgiId = useId();
  const [hesaplar, setHesaplar] = useState<KilitEkraniHesabi[] | null>(null);
  const [listeHatasi, setListeHatasi] = useState<string | null>(null);
  const [seciliId, setSeciliId] = useState<string | null>(null);
  const [kip, setKip] = useState<Kip>("parola");
  const [parola, setParola] = useState("");
  const [yeniParola, setYeniParola] = useState("");
  const [tekrar, setTekrar] = useState("");
  const [bilgi, setBilgi] = useState<string | null>(null);
  // Hatalar alan alan (dosya başı notu).
  const [parolaHatasi, setParolaHatasi] = useState<string | null>(null);
  const [yeniHatasi, setYeniHatasi] = useState<string | null>(null);
  const [tekrarHatasi, setTekrarHatasi] = useState<string | null>(null);
  const [hesapHatasi, setHesapHatasi] = useState<string | null>(null);
  const [genelHata, setGenelHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);
  const [acildi, setAcildi] = useState(false);

  // Odak yeniden çizimden SONRA verilir: alanlar istek sürerken kapalıydı, kip değişince
  // alanlar yeniden takılır. Hedef: yenileme kipinde "Yeni parola" (eşleşmemede "Parola
  // (tekrar)"); parola kipinde hesap seçiliyse "Parola", değilse ilk seçilebilir satır.
  const [odak, setOdak] = useState<OdakIstegi>({ n: 0, tekrar: false });
  const odakIste = useCallback((tekrarAlanina = false) => {
    setOdak((o) => ({ n: o.n + 1, tekrar: tekrarAlanina }));
  }, []);
  useEffect(() => {
    if (odak.n === 0) return;
    const form = formRef.current;
    const ilkSecilebilir = () =>
      form?.querySelector<HTMLInputElement>('input[type="radio"]:not(:disabled)') ?? null;
    let hedef: HTMLElement | null;
    if (odak.tekrar && tekrarAlani.current) hedef = tekrarAlani.current;
    else if (yeniParolaAlani.current) hedef = yeniParolaAlani.current;
    else if (form?.querySelector('input[type="radio"]:checked')) hedef = parolaAlani.current;
    else hedef = ilkSecilebilir();
    hedef?.focus();
  }, [odak]);

  // Liste en az bir kez okundu mu? Tek hesabın kendiliğinden seçimi yalnız ilk okumadadır.
  const listeOkundu = useRef(false);
  const hesaplariOku = useCallback(() => {
    setListeHatasi(null);
    oturumApi
      .hesaplar()
      .then((liste) => {
        const ilkOkuma = !listeOkundu.current;
        listeOkundu.current = true;
        setHesaplar(liste);
        const secilebilir = liste.map(hesapSecenegi).filter((h) => h.secilebilir);
        setSeciliId((onceki) => {
          if (onceki !== null && secilebilir.some((h) => h.id === onceki)) return onceki;
          return ilkOkuma && secilebilir.length === 1 ? secilebilir[0].id : null;
        });
        odakIste();
      })
      .catch((err: unknown) => {
        setListeHatasi(oturumHatasi(err, "Hesap listesi okunamadı.").metin);
      });
  }, [odakIste]);

  useEffect(() => {
    hesaplariOku();
  }, [hesaplariOku]);

  const secenekler = (hesaplar ?? []).map(hesapSecenegi);
  const secili = hesaplar?.find((h) => h.id === seciliId) ?? null;
  const yoneticiSecili = secili?.rol === "yonetici";

  function hatalariSil() {
    setParolaHatasi(null);
    setYeniHatasi(null);
    setTekrarHatasi(null);
    setHesapHatasi(null);
    setGenelHata(null);
  }

  function parolaKipineDon() {
    setKip("parola");
    setParola("");
    setYeniParola("");
    setTekrar("");
    setBilgi(null);
    hatalariSil();
  }

  /** "Vazgeç" ve "Parolayla açmaya dön": parola adımına dönülür, odak forma gelir. */
  function parolayaDon() {
    parolaKipineDon();
    odakIste();
  }

  function hesapSec(id: string) {
    setSeciliId(id);
    // Hata ve yarım kalan yenileme önceki hesabındır (sayaç hesap başına). Odak satırda
    // kalır: ok tuşlarıyla satırlar arasında dolaşılabilsin.
    parolaKipineDon();
  }

  function satirdaEnter() {
    if (parola !== "") formRef.current?.requestSubmit();
    else parolaAlani.current?.focus();
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    hatalariSil();
    if (secili === null) {
      setHesapHatasi(HESAP_SECIN_ILETISI);
      odakIste();
      return;
    }
    if (kip === "yenile") {
      const sorun = yeniParolaHatalari(yeniParola, tekrar, parola);
      if (sorun.yeni || sorun.tekrar) {
        setYeniHatasi(sorun.yeni);
        setTekrarHatasi(sorun.tekrar);
        odakIste(sorun.yeni === null);
        return;
      }
    }
    setCalisiyor(true);
    try {
      await kilidiAc({
        hesap: secili.id,
        parola,
        ...(kip === "yenile" ? { yeni_parola: yeniParola } : {}),
      });
      // Pencere yeniden yükleniyor; o ana dek form kapalı kalır (içerik görünmez).
      setAcildi(true);
    } catch (err) {
      const { kod, metin } = oturumHatasi(err, "Kilit açılamadı.");
      if (kod === "parola_yenilenmeli") {
        setKip("yenile");
        setBilgi(metin);
        odakIste();
      } else if (kod === "hesap_askida") {
        // Onuncu hatalı deneme: hesap askıya alındı. Seçim bırakılır (liste tazelenince
        // başka hesap kendiliğinden seçilmez), ileti hesap grubunun altında kalır.
        parolaKipineDon();
        setSeciliId(null);
        setHesapHatasi(metin);
        hesaplariOku();
      } else if (kod === "parola_yanlis") {
        // Yenileme ekranında da (geçici parola bu arada değişti) parola adımına dönülür.
        parolaKipineDon();
        setParolaHatasi(metin);
        odakIste();
      } else if (kip === "yenile" && dogrulamaReddiMi(err)) {
        // Sunucu yeni parolayı reddetti: yenileme adımında kalınır, yazılanlar korunur.
        setYeniHatasi(metin);
        odakIste();
      } else {
        setGenelHata(metin);
        if (kip === "parola") setParola("");
        odakIste();
      }
    } finally {
      setCalisiyor(false);
    }
  }

  const kapali = calisiyor || acildi;
  const bosListe = hesaplar !== null && hesaplar.length === 0;

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card elevation={1} className="w-full max-w-md p-6">
        <div className="mb-4 flex items-center gap-3">
          <Icon name="lock" size="lg" className="text-primary" />
          <h1 className="text-headline-small text-on-surface">{KILIT_EKRANI_BASLIGI}</h1>
        </div>

        {hesaplar === null && listeHatasi === null && <SkeletonList rows={2} />}

        {listeHatasi !== null && (
          <div className="flex flex-col items-start gap-3">
            <p role="alert" className="text-body-medium text-error">
              {listeHatasi}
            </p>
            <Button variant="tonal" icon="refresh" onClick={hesaplariOku}>
              Yeniden dene
            </Button>
          </div>
        )}

        {bosListe && (
          <div className="flex flex-col gap-4">
            <p className="text-body-medium text-on-surface">{BOS_LISTE_METNI}</p>
            <KurtarmaIleAcma hesap={null} />
          </div>
        )}

        {!bosListe && hesaplar !== null && kip === "kurtarma" && secili !== null && (
          <KurtarmaIleAcma hesap={hesapSecenegi(secili)} onVazgec={parolayaDon} />
        )}

        {!bosListe && hesaplar !== null && kip !== "kurtarma" && (
          <form ref={formRef} onSubmit={gonder} className="flex flex-col gap-4">
            <HesapSecimi
              secenekler={secenekler}
              seciliId={seciliId}
              onSec={hesapSec}
              onEnter={satirdaEnter}
              disabled={kapali || kip === "yenile"}
              hata={hesapHatasi}
            />

            {kip === "parola" ? (
              <TextField
                ref={parolaAlani}
                label="Parola"
                type="password"
                value={parola}
                onChange={(e) => setParola(e.target.value)}
                autoComplete="current-password"
                error={parolaHatasi ?? undefined}
                disabled={kapali}
                required
              />
            ) : (
              <>
                {bilgi && (
                  <p
                    id={bilgiId}
                    className="rounded-shape-md bg-tertiary-container p-3 text-body-medium text-on-tertiary-container"
                  >
                    {bilgi}
                  </p>
                )}
                <YeniParolaAlanlari
                  ref={yeniParolaAlani}
                  tekrarRef={tekrarAlani}
                  yeniParola={yeniParola}
                  onYeniParola={setYeniParola}
                  tekrar={tekrar}
                  onTekrar={setTekrar}
                  yeniHata={yeniHatasi}
                  tekrarHata={tekrarHatasi}
                  aciklamaId={bilgi ? bilgiId : undefined}
                  disabled={kapali}
                />
              </>
            )}

            {genelHata && (
              <p role="alert" className="text-body-medium text-error">
                {genelHata}
              </p>
            )}

            {calisiyor && (
              <p role="status" className="text-body-small text-on-surface-variant">
                {DENETLENIYOR_METNI}
              </p>
            )}

            <Button type="submit" disabled={kapali} block>
              {kapali ? "Açılıyor…" : kip === "yenile" ? "Parolayı yenile ve aç" : "Aç"}
            </Button>

            {kip === "yenile" && (
              <div className="flex justify-center">
                <Button variant="text" type="button" onClick={parolayaDon} disabled={kapali}>
                  Vazgeç
                </Button>
              </div>
            )}

            {kip === "parola" && yoneticiSecili && (
              <div className="flex justify-center">
                <Button
                  variant="text"
                  type="button"
                  onClick={() => {
                    hatalariSil();
                    setKip("kurtarma");
                  }}
                  disabled={kapali}
                >
                  Parolamı unuttum
                </Button>
              </div>
            )}
            {kip === "parola" && secili !== null && !yoneticiSecili && (
              <p className="text-center text-body-small text-on-surface-variant">
                {UNUTTUM_BASKA_ROL_METNI}
              </p>
            )}
          </form>
        )}

        <p className="mt-4 border-t border-outline-variant pt-4 text-body-small text-on-surface-variant">
          {KAPSAM_METNI}
        </p>
      </Card>
    </div>
  );
}
