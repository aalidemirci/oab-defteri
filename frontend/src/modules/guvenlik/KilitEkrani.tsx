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
// * Liste dolu ama seçilebilir satır kalmadıysa (hepsi askıda, kaydı okunamıyor ya da giriş
//   kapalı; plan F1b-2 "Ön yüz" → "Kilit ekranı") liste yerinde kalır, Parola alanı ve "Aç"
//   kalkar; yerine yol gösterme metni ve "Kurtarma anahtarıyla aç" düğmesi gelir (hesap
//   kurtarma listesinden seçilir). Metin kullanıcı kararlarınındır: program yöneticisi
//   kurtarma anahtarıyla açar ("Parolamı unuttum" yolu), öteki hesaplar program yöneticisine
//   başvurur (askıyı o kaldırır, parolayı o sıfırlar); kayıtlar değiştirilmiş görünüyorsa
//   Denetleme Kuruluna bildirilir — kurtarma anahtarı zarfının üçüncü durumu (02.11.2026) ve
//   çaresi "yedekten geri yükleme ya da kurtarma anahtarıyla açılış" (03.11.2026). Zarfın
//   üçüncü durumunun sözleri belgede, anahtar panelinde ve sözlükte BİREBİR aynıdır
//   (`metinler.ZARFIN_UCUNCU_DURUMU`; backend `test_kurtarma_anahtari_pdf` hepsini sınar).
// * Açılış (kilit açma ya da kurtarma) pencereyi yeniden yükler (tasarım §13 D53;
//   `oturum/eylemler`): önceki hesabın belleği yeni oturuma kalmaz.
// * Çift gönderim yoktur: istek sürerken (ve açılıştan sonra, pencere yüklenirken) ikinci
//   gönderim `gonder`'in başında döner. Koruma bir ref'tir, durum değil: aynı olay döngüsünde
//   gelen iki gönderim (satırda Enter → `requestSubmit`, Enter'ın yinelenmesi) yeniden
//   çizimden önce geldiği için `calisiyor`'u ikisi de false görürdü.
//
// Hata hangi alanınsa orada çıkar: "Parola hatalı." Parola alanının, "Hesabınızı seçin."
// ve askı iletisi hesap grubunun, yeni parolanın reddi "Yeni parola"nın, eşleşmeme
// "Parola (tekrar)"ın altında; hesaba ya da alana bağlı olmayan ret (hesap kaydı, parola
// kaydı, denetim izi, iki depo, ağ) formun genel uyarısıdır ve sunucunun iletisi olduğu gibi
// yazılır (`oturum/hatalar`: sunucu iletisi önceliklidir). Kayıt reddinde (hesap kaydı, parola
// kaydı, denetim izi ya da iki depo; `oturum/hatalar.kayitReddiMi`) program yöneticisi hesabı
// seçiliyse iletinin altında zarfın üçüncü durumunun yol metni de durur
// (`KurtarmaIleAcma.KayitReddiYolu`; kullanıcı kararı 04.11.2026) ve odağın döndüğü alana
// bağlanır (Parola; yenilemede Yeni parola): satırı seçilebilir göründüğü hâlde girişi ve
// "Parolamı unuttum"u reddedilen program yöneticisinin çıkışı yedekten geri yüklemedir (parola
// kaydı reddinde metnin saydığı öteki çare, kurtarma anahtarıyla açılış, geçerlidir). Öteki
// hesaplarda sunucunun iletisi çareyi kendisi söyler (parola kaydında program yöneticisinin
// sıfırlaması; hesap kaydında program yöneticisine ve Denetleme Kuruluna bildirim). Odak her
// retten ve her geri dönüşten ("Vazgeç", "Parolayla açmaya dön") sonra forma döner: hesap seçiliyse Parola alanına, değilse
// ilk seçilebilir satıra, seçilebilir satır yoksa "Kurtarma anahtarıyla aç"a (bu ekran kabuğun
// içinde çizilir; odak sayfa gövdesine düşerse klavye kullanıcısı kenar çubuğunu dolaşmak
// zorunda kalırdı).
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
import { dogrulamaReddiMi, kayitReddiMi, oturumHatasi } from "../oturum/hatalar";
import { yeniParolaHatalari } from "../oturum/parolaPolitikasi";
import YeniParolaAlanlari from "../oturum/YeniParolaAlanlari";
import HesapSecimi from "./HesapSecimi";
import type { HesapSecenegi } from "./HesapSecimi";
import KurtarmaIleAcma, {
  DENETLENIYOR_METNI,
  KayitReddiYolu,
  UCUNCU_DURUM_YOL_METNI,
} from "./KurtarmaIleAcma";
import { KAPSAM_METNI } from "./metinler";

/** Ekranın h1'i — üst çubukta da bu yazar (docs/sozluk.md §4.2). */
export const KILIT_EKRANI_BASLIGI = "Kayıtlar kilitli";

/** Askıdaki hesabın etiketi (iki askı kaynağı da; sözlük §1 "Hesap"). */
export const ASKIDA_ETIKETI = "askıda — program yöneticisine başvurun";
/**
 * Üyelik ya da görev askısının nedeni (plan F1c 7. adım "Askı kilidi"; 11. adımda ekran iletisi): bağlı
 * kurul üyeliği düşen, iptal edilen ya da görev bölümünde görevi değişen hesap aynı işlemde askıya
 * alınır; oturumdaki hesapsa program sonraki istekte kilitlenir ve kişi bu ekrana döner. Listede böyle
 * bir hesap varsa listenin altında durur (hatalı deneme askısında çıkmaz; neden kodu
 * `UYELIK_DUSTU` · `GOREV_BOLUMU`).
 */
export const UYELIK_ASKISI_METNI =
  "Bağlı olduğu kurul üyeliği düşen, iptal edilen ya da görev bölümünde görevi değişen kişinin " +
  "hesabı askıya alınır; askıya alınan hesap o anda açık oturumun hesabıysa program kilitlenir. Askıdan " +
  "çıkarmayı ya da hesabı kapatıp görevdeki üyeye yeni hesap açmayı program yöneticisi yapar.";
/** Üyelik ya da görev askısının neden kodları (backend `SuspendReason`). */
const UYELIK_ASKISI_NEDENLERI: ReadonlySet<string> = new Set(["UYELIK_DUSTU", "GOREV_BOLUMU"]);

/** Rolü veritabanından okunamayan satır (backend `oturum.ROL_OKUNAMADI_ETIKETI`). */
export const OKUNAMADI_ETIKETI = "Hesap kaydı okunamadı";
/** Program yöneticisi olmayan hesap seçiliyken parolasını unutan kişiye. */
export const UNUTTUM_BASKA_ROL_METNI = "Parolanızı unuttuysanız program yöneticisine başvurun.";
/** Hesap seçilmeden gönderilince hesap grubunun altında. */
export const HESAP_SECIN_ILETISI = "Hesabınızı seçin.";
/**
 * Liste boşken kurtarma yolunun gerekçesi. Program böyle bir dosyayı yalnız kurtarma
 * anahtarıyla geri yüklemede yazar (tasarım TK10); öyle bir geri yükleme yoksa dosya program
 * dışından değiştirilmiştir (zarfın üçüncü durumu): Denetleme Kuruluna bildirilir.
 */
export const BOS_LISTE_METNI =
  "Bu bilgisayarın güvenlik dosyasında hesap parolası yok: kayıtlar kurtarma anahtarıyla " +
  "geri yüklendiyse böyledir. Program yöneticisi kurtarma anahtarıyla açar ve yeni " +
  "parolasını belirler; öteki hesaplar program yöneticisine başvurur. Böyle bir geri " +
  "yükleme yapılmadıysa güvenlik dosyası program dışından değiştirilmiş olabilir: " +
  "Denetleme Kuruluna bildirin.";

/** Seçilebilir satır kalmayınca kurtarma yolunu açan düğme (plan F1b-2 "Kilit ekranı"). */
export const KURTARMA_ILE_AC_ETIKETI = "Kurtarma anahtarıyla aç";

/**
 * Seçilebilir satır kalmayınca yol gösterme: kim ne yapar (kullanıcı kararı 03.11.2026 —
 * program yöneticisi için "Parolamı unuttum", öteki hesaplar için program yöneticisinin
 * sıfırlaması; askıyı da program yöneticisi kaldırır, backend `hesaplar.unsuspend`).
 */
export const SECILEBILIR_HESAP_YOK_METNI =
  "Bu listede seçilebilecek hesap kalmadı. Program yöneticisi aşağıdaki “Kurtarma " +
  "anahtarıyla aç” düğmesiyle (“Parolamı unuttum” yolu) açar ve yeni parolasını belirler. " +
  "Öteki hesaplar program yöneticisine başvurur: askıyı o kaldırır, parolayı o sıfırlar.";

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
  // Seçilebilir satır kalmayınca yol gösterme ve "Kurtarma anahtarıyla aç" (odağın son hedefi).
  const yolGostermeRef = useRef<HTMLDivElement>(null);
  // Çift gönderim koruması (dosya başı notu): istek sürerken ve açılıştan sonra true.
  const gonderimSuruyor = useRef(false);
  const bilgiId = useId();
  const yolGostermeId = useId();
  const kayitYoluId = useId();
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
  // Genel hata program yöneticisi hesabının kayıt reddi mi (`kayitReddiMi`)? Öyleyse yol metni
  // iletinin altında durur ve odağın döndüğü alana bağlanır (dosya başı notu).
  const [kayitReddi, setKayitReddi] = useState(false);
  const [calisiyor, setCalisiyor] = useState(false);
  const [acildi, setAcildi] = useState(false);

  // Odak yeniden çizimden SONRA verilir: alanlar istek sürerken kapalıydı, kip değişince
  // alanlar yeniden takılır. Hedef: yenileme kipinde "Yeni parola" (eşleşmemede "Parola
  // (tekrar)"); parola kipinde hesap seçiliyse "Parola", değilse ilk seçilebilir satır;
  // seçilebilir satır yoksa "Kurtarma anahtarıyla aç".
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
    else hedef = ilkSecilebilir() ?? yolGostermeRef.current?.querySelector("button") ?? null;
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
    setKayitReddi(false);
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
    // `requestSubmit` `gonder`'den geçer: süren gönderim varsa orada döner (çift gönderim yok).
    if (parola !== "") formRef.current?.requestSubmit();
    else parolaAlani.current?.focus();
  }

  /** Seçilebilir satır kalmayınca: kurtarma yolu, hesap kurtarma listesinden seçilir. */
  function kurtarmayaGec() {
    hatalariSil();
    setKip("kurtarma");
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    // Çift gönderim koruması (dosya başı notu): süren gönderimin hataları da silinmez.
    if (gonderimSuruyor.current) return;
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
    gonderimSuruyor.current = true;
    setCalisiyor(true);
    try {
      await kilidiAc({
        hesap: secili.id,
        parola,
        ...(kip === "yenile" ? { yeni_parola: yeniParola } : {}),
      });
      // Pencere yeniden yükleniyor; o ana dek form kapalı kalır (içerik görünmez) ve koruma
      // kalkmaz: yüklenen pencereye ikinci bir açılış gitmez.
      setAcildi(true);
    } catch (err) {
      gonderimSuruyor.current = false;
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
        // Yalnız program yöneticisi hesabında: öteki hesaplarda sunucunun iletisi çareyi kendisi
        // söyler (parola kaydında program yöneticisinin sıfırlaması; dosya başı notu).
        setKayitReddi(kayitReddiMi(kod) && yoneticiSecili);
        if (kip === "parola") setParola("");
        odakIste();
      }
    } finally {
      setCalisiyor(false);
    }
  }

  const kapali = calisiyor || acildi;
  // Kayıt reddinin yol metni odağın döndüğü alanı açıklar (Parola; yenilemede Yeni parola).
  const kayitYoluBagi = genelHata && kayitReddi ? kayitYoluId : undefined;
  const bosListe = hesaplar !== null && hesaplar.length === 0;
  // Liste dolu ama hiçbir satır seçilemiyor (dosya başı notu): parola yolu yerine yol gösterme.
  // Kip ayrıca sorulmaz: kurtarma kipinde form çizilmez, yenileme kipinde seçili (seçilebilir)
  // bir hesap vardır ve liste o kipte tazelenmez (askıda önce parola kipine dönülür).
  const yolGoster =
    hesaplar !== null && hesaplar.length > 0 && !secenekler.some((h) => h.secilebilir);
  const uyelikAskisiVar = (hesaplar ?? []).some(
    (h) => h.askida_nedeni !== null && UYELIK_ASKISI_NEDENLERI.has(h.askida_nedeni),
  );

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

        {/* Seçili program yöneticisinin "Parolamı unuttum"u ya da (seçilebilir satır yokken)
            "Kurtarma anahtarıyla aç": ikincisinde hesap kurtarma listesinden seçilir. */}
        {!bosListe && hesaplar !== null && kip === "kurtarma" && (
          <KurtarmaIleAcma
            hesap={secili !== null ? hesapSecenegi(secili) : null}
            onVazgec={parolayaDon}
          />
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

            {uyelikAskisiVar && (
              <p role="note" className="text-body-small text-on-surface-variant">
                {UYELIK_ASKISI_METNI}
              </p>
            )}

            {yolGoster ? (
              <div ref={yolGostermeRef} className="flex flex-col gap-3">
                <div
                  id={yolGostermeId}
                  className="flex flex-col gap-2 rounded-shape-md bg-tertiary-container p-3 text-body-medium text-on-tertiary-container"
                >
                  <p>{SECILEBILIR_HESAP_YOK_METNI}</p>
                  <p>{UCUNCU_DURUM_YOL_METNI}</p>
                </div>
                <Button
                  variant="tonal"
                  icon="key"
                  type="button"
                  onClick={kurtarmayaGec}
                  aria-describedby={yolGostermeId}
                  block
                >
                  {KURTARMA_ILE_AC_ETIKETI}
                </Button>
              </div>
            ) : kip === "parola" ? (
              <TextField
                ref={parolaAlani}
                label="Parola"
                type="password"
                value={parola}
                onChange={(e) => setParola(e.target.value)}
                autoComplete="current-password"
                error={parolaHatasi ?? undefined}
                describedBy={kayitYoluBagi}
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
                  aciklamaId={
                    [bilgi ? bilgiId : undefined, kayitYoluBagi].filter(Boolean).join(" ") ||
                    undefined
                  }
                  disabled={kapali}
                />
              </>
            )}

            {genelHata && (
              <p role="alert" className="text-body-medium text-error">
                {genelHata}
              </p>
            )}
            {kayitYoluBagi && <KayitReddiYolu id={kayitYoluBagi} />}

            {calisiyor && (
              <p role="status" className="text-body-small text-on-surface-variant">
                {DENETLENIYOR_METNI}
              </p>
            )}

            {!yolGoster && (
              <Button type="submit" disabled={kapali} block>
                {kapali ? "Açılıyor…" : kip === "yenile" ? "Parolayı yenile ve aç" : "Aç"}
              </Button>
            )}

            {kip === "yenile" && (
              <div className="flex justify-center">
                <Button variant="text" type="button" onClick={parolayaDon} disabled={kapali}>
                  Vazgeç
                </Button>
              </div>
            )}

            {kip === "parola" && yoneticiSecili && (
              <div className="flex justify-center">
                <Button variant="text" type="button" onClick={kurtarmayaGec} disabled={kapali}>
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
