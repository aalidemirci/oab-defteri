// Yedekten geri yükleme kartı (Güvenlik sekmesi) — programın AÇILABİLDİĞİ
// senaryo: yanlış/eksik veri girişinden sonra eski bir güne dönüş. Program hiç
// açılmıyorsa (bozuk veritabanı) doğru araç masaüstü "--geri-yukle" kipidir
// (Başlat menüsü: "Yedekten Geri Yükle"); metin kullanıcıyı oraya yönlendirir.
//
// Akış: bu bilgisayardaki yedeklerin listesinden seçim YA DA elindeki yedek dosyası → parolanız
// veya kurtarma anahtarı (yedekler DAİMA şifrelidir; düz yedek dalı yok, tasarım TK8, §4.4.7) →
// onay → POST /backups/restore/. Başarıda backend "yeniden başlat" kapısını kurar (tüm API 503
// döner); kart dosya raporuyla olayı yayınlar, YenidenBaslatEkrani arayüzü örter. Parola/kurtarma
// anahtarı yalnız istek gövdesinde taşınır, hiçbir yere yazılmaz.
//
// Kaynak (kullanıcı kararı 06.11.2026 "Yedek dosyası yüklenmez, programın Aç penceresiyle seçilir")
// üçtür, aynı anda biri seçilidir: listeden ad, köprüden yol, kutudan File. Program penceresinde
// düğme Aç penceresini açar (`yedek_dosyasi_sor`): sunucuya yalnız yol ve sır küçük istekle gider,
// dosya yerinde okunur. Kutu yalnız köprünün olmadığı geliştirme kipindedir. İptalde önceki kaynak
// aynen kalır; köprünün reddi de iptal sayılır (pencere açılamazsa köprü zaten "" döner). Pencere
// açıkken kaynağı değiştiren ve isteği gönderen denetimler kapalıdır; sır alanları yalnız istek
// sürerken kapalıdır (pencere modaldır). Pencerede yapılan seçim DOM olayı üretmez, etkileşim elle
// kaydedilir (`lib/api`).
//
// Yol: yalnız bileşenin durumunda ve istek gövdesinde durur, kart sökülünce gider. Ekrana, konsola,
// hata iletisine, modül belleğine ya da tarayıcı deposuna GİRMEZ; ekranda yalnız dosyanın adı görünür.
//
// Tür ve kapsam (plan F1b-3 "Ekran adları"; kullanıcı kararı 06.11.2026 "Elden seçilen yedeğin
// başlığını sunucu okur"): her yedeğin türü adından türetilir, kapsamı listeden gelir; onay metni
// kapsamı söyler. Yol seçilince `POST backups/inspect/` listenin satırını verir, kart onu listedeki
// bileşenlerle yazar. Yanıt beklenirken "Geri yükle" kapalıdır, onay kapsamsız açılmasın. Yanıt yalnız
// kaynak hâlâ aynıysa yazılır: eski yanıt yeni seçimi ezmez. İstek düşerse kapsam yazılmaz, ad yoldan
// türetilir, geri yükleme engellenmez (dosyayı sunucu sınar). Kutudaki dosyanın başlığı istemcide
// okunmaz: kapsamı onayda yazmaz, geri yüklemeden sonra raporda görünür.
//
// Boy sınırı (kullanıcı kararı 06.11.2026): sunucunun gövde sınırını aşan dosya kutudan gönderilmez.
// Aç penceresinde seçilen dosya gönderilmez, bu sınır ona uygulanmaz.
//
// Bozuk ek (kullanıcı kararı 04.11.2026 "Bozuk ekte geri yükleme durur, ikinci onayla sürer"):
// 409 `ek_onayi_gerekli`de hiçbir şey değişmemiştir, sunucu da ilk denemeden hiçbir şey saklamaz.
// Kart iletiyi ve kişisiz listeyi gösterip ikinci düğmeyi açar; ikinci istek AYNI kaynağı (aynı
// `name`, aynı `yol` ya da aynı File nesnesi) ve aynı sırrı `ekler_olmadan_surdur` ile yollar,
// doğrulama baştan koşar. Kaynak ya da sır değişirse ikinci onay sıfırlanır: bu yüzden alanlar istek
// sürerken de kapalıdır, süren isteğin raporu başka bir kaynağın onayı olmasın. Durulunca odak
// panele alınır, ikinci düğmeye ALINMAZ: ikinci onay açık bir eylemdir, ilk onayın Enter'ı onu
// basmamalıdır.
//
// Süren istek (modül belleği, `yedekIsleri`): "sürüyor" bayrağı bileşenin dışındadır, kart sökülüp
// yeniden takılsa da düğme ve alanlar kapalı kalır, ikinci istek gitmez. Sır, yol ve File belleğe
// girmez. Başarı küresel olayla gider. Ret ise yalnız kartın durumuna yazılır: istek sürerken kart
// söküldüyse sunucunun iletisi kapatılana dek duran snackbar'la söylenir, kullanıcı akışı baştan
// yürütür.
//
// Yedeğin hangi sırla açıldığı (tasarım TK10, §4.4.4): yedek başlığı yalnız kurtarma
// bölümünü taşır, hesap sarmalı taşımaz. Bu yüzden
//   * PAROLA yolu oturumdaki hesabın BUGÜNKÜ parolasıdır ("Parolanız"): backend güncel
//     `guvenlik.json`'daki o hesabın sarmalını dener (gövdede `hesap` boş gider, backend
//     oturumdaki hesabı kullanır — `live_restore`). Yalnız bu bilgisayarda işler. Açık
//     oturumda geri yüklemeyi yalnız program yöneticisi yapar: uç rol kapısından, parola yolu
//     ayrıca servisin yetki kapısından geçer (`live_restore`).
//   * KURTARMA ANAHTARI yolu yedeğin alındığı gün geçerli olan anahtardır; listedeki
//     her yedek o anahtarın no'sunu ve tarihini taşır (`YedekDosyasi.kurtarma`) ve seçilen
//     yedeğin hangi kâğıtla açıldığı sır sorulmadan ÖNCE yazılır. Aç penceresinde seçilen dosyada
//     da öyledir; başlık okunamadıysa cümle bunu söyler. Kutudaki dosyanın başlığı istemcide
//     okunmaz; doğru anahtar değilse backend iletisi no'yu söyler.
// Gövde backend'in beklediği gibidir: `name`, `yol` YA DA `file`, `password` ya da
// `recovery_key` (anahtarlar İngilizce; `BackupRestoreRequestSerializer`).
//
// `kayipKipi`: güvenlik dosyası kayıp ekranında (GuvenlikDosyasiKayip) çıkış
// yolu olarak gösterilir; giriş metni o duruma göre yazılır. Backend yedek listesini, başlık
// okumayı ve geri yüklemeyi kayıp kilidinde de açık tutar. Kayıp kipinde oturum yoktur ve güncel
// güvenlik dosyası okunamaz: parola yolu İŞLEMEZ, yalnız kurtarma anahtarı alanı gösterilir.

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, etkilesimKaydet } from "../../lib/api";
import { formatBoyut, formatDateTime } from "../../lib/format";
import { yenidenBaslatGerekliYayinla } from "../../lib/restart";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { guvenlikApi } from "./api";
import type { DosyaRaporu, YedekDosyasi, YedekListesi } from "./api";
import EkListesi from "./EkListesi";
import { useAcmaKoprusu } from "./kaydetmeKoprusu";
import { kurtarmaKimligiMetni, yedekAnahtarCumlesi } from "./kurtarma";
import {
  EK_ONAYI_KART_DISINDA,
  EKLER_OLMADAN_GERI_YUKLE,
  ONCEKI_VERITABANI_KENARA_ALINIR,
  YEDEK_DOSYASI_COK_BUYUK,
  YEDEK_DOSYASI_ETIKETI,
  YEDEK_DOSYASI_SEC,
  YEDEK_DOSYASI_SECILIYOR,
  YEDEK_LISTESI_BASLIGI,
} from "./metinler";
import { AZAMI_YEDEK_DOSYASI, kapsamMetni, yedekAciklamasi, yoldanDosyaAdi } from "./yedekBilgisi";
import { geriYuklemeSuruyorYaz, useGeriYuklemeSuruyor } from "./yedekIsleri";

/** Bozuk ekte durmanın kodu (backend `views.EK_ONAYI_GEREKLI`). */
const EK_ONAYI_GEREKLI = "ek_onayi_gerekli";

/** Geri yüklemenin kaynağı (dosya başı "Kaynak"). `sira` yanıtın hangi seçime ait olduğunu söyler. */
type Kaynak =
  | { tur: "liste"; ad: string }
  | {
      tur: "yol";
      yol: string;
      sira: number;
      ad: string;
      okunuyor: boolean;
      /** Başlık okuması düştüyse null. */
      ozet: YedekDosyasi | null;
    }
  | { tur: "dosya"; dosya: File };

/** Yedeğin satırı: liste ve Aç penceresinde seçilen dosya aynı bileşenle yazılır. */
function YedekSatiri({ ad, yedek }: { ad: string; yedek: YedekDosyasi | null }) {
  const aciklama = yedekAciklamasi(ad, yedek?.kapsam ?? null);
  const ayrinti =
    yedek &&
    [
      yedek.modified_at && formatDateTime(yedek.modified_at),
      formatBoyut(yedek.size),
      kurtarmaKimligiMetni(yedek.kurtarma),
    ]
      .filter(Boolean)
      .join(" · ");
  return (
    <span className="min-w-0 flex-1">
      <span className="block truncate font-mono text-body-medium text-on-surface">{ad}</span>
      {aciklama && <span className="block text-body-small text-on-surface">{aciklama}</span>}
      {ayrinti && <span className="block text-label-small text-on-surface-variant">{ayrinti}</span>}
    </span>
  );
}

/** 409 `ek_onayi_gerekli`nin ekrandaki hâli: sunucunun iletisi ve kişisiz rapor. */
interface EkOnayi {
  ileti: string;
  rapor: DosyaRaporu;
}

function ekOnayiOku(err: unknown): EkOnayi | null {
  if (!(err instanceof ApiError) || err.code !== EK_ONAYI_GEREKLI) return null;
  const rapor = err.govde.rapor as DosyaRaporu | undefined;
  return rapor ? { ileti: err.message, rapor } : null;
}

interface YedektenGeriYuklemeProps {
  /** Güvenlik dosyası kayıp ekranında mı gösteriliyor? (giriş metni değişir) */
  kayipKipi?: boolean;
}

export default function YedektenGeriYukleme({ kayipKipi = false }: YedektenGeriYuklemeProps) {
  const confirm = useConfirm();
  const snackbar = useSnackbar();
  const koprudenSecilir = useAcmaKoprusu();
  const [liste, setListe] = useState<YedekListesi | null>(null);
  const [listeHata, setListeHata] = useState<string | null>(null);
  const [kaynak, setKaynak] = useState<Kaynak | null>(null);
  const [pencereAcik, setPencereAcik] = useState(false);
  const secimSirasi = useRef(0);
  const dosyaRef = useRef<HTMLInputElement>(null);
  const [parola, setParola] = useState("");
  const [anahtar, setAnahtar] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const calisiyor = useGeriYuklemeSuruyor();
  // Bozuk ekte durulduysa ikinci onayın durumu (dosya başı notu).
  const [ekOnayi, setEkOnayi] = useState<EkOnayi | null>(null);
  const ikinciOnayRef = useRef<HTMLDivElement>(null);
  // Bu kart hâlâ çizili mi? Ret yalnız çizili kartın durumuna yazılabilir (dosya başı notu).
  const takili = useRef(false);
  const mesgul = calisiyor || pencereAcik;
  // Seçilen yedeğin satırı (anahtar kimliği ve kapsamı buradan okunur); kutudaki dosyanın satırı yoktur.
  const seciliSatir =
    kaynak?.tur === "liste"
      ? (liste?.backups.find((y) => y.name === kaynak.ad) ?? null)
      : kaynak?.tur === "yol"
        ? kaynak.ozet
        : null;
  // Seçilen dosyada okuma bitince cümle hep yazılır: başlık okunamadıysa cümle bunu söyler.
  const anahtarCumlesiVar = kaynak?.tur === "yol" ? !kaynak.okunuyor : seciliSatir !== null;

  const yukle = useCallback(() => {
    guvenlikApi
      .yedekler()
      .then((veri) => {
        setListe(veri);
        setListeHata(null);
      })
      .catch((err: unknown) =>
        setListeHata(err instanceof ApiError ? err.message : "Yedek listesi okunamadı."),
      );
  }, []);
  useEffect(yukle, [yukle]);

  useEffect(() => {
    takili.current = true;
    return () => {
      takili.current = false;
    };
  }, []);

  useEffect(() => {
    if (ekOnayi !== null) ikinciOnayRef.current?.focus();
  }, [ekOnayi]);

  function kaynagiDegistir(yeni: Kaynak | null, ileti: string | null = null) {
    setKaynak(yeni);
    setHata(ileti);
    setEkOnayi(null);
  }

  function kutudanSec(yeni: File | null) {
    if (yeni === null) {
      // Kutu boşalınca yalnız kutunun kaynağı gider: listedeki seçim kalır.
      kaynagiDegistir(kaynak?.tur === "dosya" ? null : kaynak);
      return;
    }
    kaynagiDegistir(
      { tur: "dosya", dosya: yeni },
      yeni.size > AZAMI_YEDEK_DOSYASI ? YEDEK_DOSYASI_COK_BUYUK : null,
    );
  }

  function listedenSec(ad: string) {
    kaynagiDegistir({ tur: "liste", ad });
    if (dosyaRef.current) dosyaRef.current.value = "";
  }

  function yolSecildi(yol: string) {
    secimSirasi.current += 1;
    const sira = secimSirasi.current;
    const ad = yoldanDosyaAdi(yol);
    kaynagiDegistir({ tur: "yol", yol, sira, ad, okunuyor: true, ozet: null });
    // Yanıt yalnız kaynak hâlâ bu seçimse yazılır (dosya başı "Tür ve kapsam"). Ad yanıttan alınır:
    // Pardus'ta dosya adında ters bölü olabilir, yoldan türetilen ad o zaman eksik kalır.
    const yaz = (ozet: YedekDosyasi | null) =>
      setKaynak((simdiki) =>
        simdiki?.tur === "yol" && simdiki.sira === sira
          ? { ...simdiki, ad: ozet?.name ?? simdiki.ad, okunuyor: false, ozet }
          : simdiki,
      );
    guvenlikApi.yedekBasligi(yol).then(yaz, () => yaz(null));
  }

  async function yedekDosyasiSec() {
    const kopru = window.pywebview?.api;
    if (!kopru?.yedek_dosyasi_sor) return;
    setPencereAcik(true);
    let yol = "";
    try {
      yol = await kopru.yedek_dosyasi_sor();
    } catch {
      // İptal sayılır (dosya başı "Kaynak").
    } finally {
      setPencereAcik(false);
    }
    if (!yol) return;
    etkilesimKaydet();
    if (takili.current) yolSecildi(yol);
  }

  function parolaDegisti(deger: string) {
    setParola(deger);
    setEkOnayi(null);
  }

  function anahtarDegisti(deger: string) {
    setAnahtar(deger);
    setEkOnayi(null);
  }

  async function gonder(eklerOlmadan: boolean) {
    if (kaynak === null) return;
    setHata(null);
    geriYuklemeSuruyorYaz(true);
    try {
      const form = new FormData();
      if (kaynak.tur === "dosya") form.append("file", kaynak.dosya);
      else if (kaynak.tur === "yol") form.append("yol", kaynak.yol);
      else form.append("name", kaynak.ad);
      if (parola && !kayipKipi) form.append("password", parola);
      if (anahtar) form.append("recovery_key", anahtar);
      if (eklerOlmadan) form.append("ekler_olmadan_surdur", "true");
      const sonuc = await guvenlikApi.geriYukle(form);
      // Backend kapıyı kurdu; ekran örtülür — sırları bellekte tutmaya gerek yok.
      setParola("");
      setAnahtar("");
      setEkOnayi(null);
      yenidenBaslatGerekliYayinla(sonuc.dosya_raporu);
    } catch (err) {
      const durma = ekOnayiOku(err);
      const ileti =
        durma?.ileti ?? (err instanceof ApiError ? err.message : "Geri yükleme uygulanamadı.");
      if (!takili.current) {
        snackbar.error(durma ? `${ileti} ${EK_ONAYI_KART_DISINDA}` : ileti, { duration: null });
      } else if (durma) setEkOnayi(durma);
      else setHata(ileti);
    } finally {
      geriYuklemeSuruyorYaz(false);
    }
  }

  async function geriYukle() {
    setHata(null);
    if (kaynak === null) return;
    if (kaynak.tur === "dosya" && kaynak.dosya.size > AZAMI_YEDEK_DOSYASI) {
      setHata(YEDEK_DOSYASI_COK_BUYUK);
      return;
    }
    if (!parola && !anahtar) {
      setHata(
        kayipKipi
          ? "Yedekler şifrelidir; yedeğin kurtarma anahtarını girin."
          : "Yedekler şifrelidir; parolanızı ya da kurtarma anahtarını girin.",
      );
      return;
    }
    // Başlık soru, gövde sonuç (docs/sozluk.md §3) — soru gövdede yinelenmez.
    const kapsam = kapsamMetni(seciliSatir?.kapsam ?? null);
    const onay = await confirm({
      title: "Yedekten geri yüklensin mi?",
      message:
        `“${kaynak.tur === "dosya" ? kaynak.dosya.name : kaynak.ad}” yedeği mevcut ` +
        "veritabanının yerine konur; o yedekten sonra " +
        "girdiğiniz kayıtlar ekrandan kalkar. " +
        (kapsam ? `Yedeğin kapsamı: ${kapsam}. ` : "") +
        `${ONCEKI_VERITABANI_KENARA_ALINIR} İşlem sonrası program kapatılıp yeniden açılmalıdır.`,
      confirmLabel: "Geri yükle",
    });
    if (onay) await gonder(false);
  }

  return (
    <Card className="p-6">
      <div className="flex items-start gap-3">
        <Icon name="settings_backup_restore" className="mt-0.5 text-primary" />
        <div className="min-w-0 flex-1">
          <h2 className="text-title-large text-on-surface">Yedekten Geri Yükleme</h2>
          {kayipKipi ? (
            <p className="mt-2 text-body-medium text-on-surface-variant">
              En yeni yedeği ya da elinizdeki yedek dosyasını seçin.{" "}
              {ONCEKI_VERITABANI_KENARA_ALINIR} Geri yükleme uygulandıktan sonra program kapatılıp
              yeniden açılmalıdır.
            </p>
          ) : (
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Yanlış veri girişinden sonra eski bir güne dönmek için listedeki yedeklerden birini ya
              da elinizdeki yedek dosyasını seçin. {ONCEKI_VERITABANI_KENARA_ALINIR} Geri yükleme
              uygulandıktan sonra program kapatılıp yeniden açılmalıdır.
            </p>
          )}
          <p className="mt-2 text-body-small text-on-surface-variant">
            Program hiç açılmıyorsa (bozuk veritabanı) bu ekrana ulaşamazsınız; o durumda
            Windows&apos;ta Başlat menüsündeki “OAB Defteri — Yedekten Geri Yükle” kısayolunu,
            Pardus/Linux&apos;ta uçbirimden{" "}
            <span className="font-mono">oab-defteri --geri-yukle</span> komutunu kullanın.
          </p>

          {liste === null && listeHata === null ? (
            <SkeletonList rows={2} className="mt-4" />
          ) : listeHata !== null ? (
            <p role="alert" className="mt-4 text-body-small text-error">
              {listeHata}
            </p>
          ) : liste !== null && liste.backups.length === 0 ? (
            <p className="mt-4 text-body-medium text-on-surface-variant">
              Yedek klasöründe geri yüklenebilir dosya yok. Program her gün ilk açılışta günlük
              yedek alır (program yöneticisi hesabı kurulduktan sonra); elinizde bir yedek dosyası
              varsa aşağıdan seçebilirsiniz.
            </p>
          ) : (
            liste !== null && (
              <fieldset className="mt-4">
                <legend className="text-label-large text-on-surface-variant">
                  {YEDEK_LISTESI_BASLIGI}
                </legend>
                <ul className="mt-2 max-h-56 space-y-1 overflow-y-auto pr-1">
                  {liste.backups.map((yedek) => (
                    <li key={yedek.name}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-shape-sm px-3 py-2 hover:bg-surface-container">
                        <input
                          type="radio"
                          name="geri-yukleme-yedegi"
                          checked={kaynak?.tur === "liste" && kaynak.ad === yedek.name}
                          onChange={() => listedenSec(yedek.name)}
                          disabled={mesgul}
                          className="h-5 w-5 accent-primary"
                        />
                        <YedekSatiri ad={yedek.name} yedek={yedek} />
                      </label>
                    </li>
                  ))}
                </ul>
              </fieldset>
            )
          )}

          {liste !== null && (
            <p className="mt-2 text-label-small text-on-surface-variant">
              Yedek klasörü: <span className="font-mono">{liste.backup_dir}</span>
            </p>
          )}

          {koprudenSecilir ? (
            <div className="mt-4">
              <p className="mb-1 text-label-large text-on-surface-variant">
                {YEDEK_DOSYASI_ETIKETI}
              </p>
              <Button
                variant="outlined"
                icon="folder_open"
                onClick={() => void yedekDosyasiSec()}
                disabled={mesgul}
              >
                {pencereAcik ? YEDEK_DOSYASI_SECILIYOR : YEDEK_DOSYASI_SEC}
              </Button>
              {kaynak?.tur === "yol" && (
                <div className="mt-2 flex rounded-shape-sm bg-surface-container px-3 py-2">
                  <YedekSatiri ad={kaynak.ad} yedek={kaynak.ozet} />
                </div>
              )}
            </div>
          ) : (
            <div className="mt-4">
              <label
                htmlFor="geri-yukleme-dosyasi"
                className="mb-1 block text-label-large text-on-surface-variant"
              >
                {YEDEK_DOSYASI_ETIKETI}
              </label>
              <input
                id="geri-yukleme-dosyasi"
                ref={dosyaRef}
                type="file"
                accept=".odbak"
                onChange={(e) => kutudanSec(e.target.files?.[0] ?? null)}
                disabled={calisiyor}
                className="block min-h-[var(--od-field-height)] w-full rounded-shape-sm border border-outline bg-surface-container-lowest px-3 py-2 text-body-medium text-on-surface file:mr-3 file:rounded-shape-sm file:border-0 file:bg-secondary-container file:px-3 file:py-1.5 file:text-label-large file:text-on-secondary-container focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              />
            </div>
          )}

          {/* Sır sorulmadan ÖNCE: seçilen yedeği hangi kurtarma anahtarı açıyor (TK10). */}
          {anahtarCumlesiVar && (
            <p
              role="status"
              className="mt-4 flex items-start gap-2 rounded-shape-sm bg-secondary-container px-4 py-3 text-body-medium text-on-secondary-container"
            >
              <Icon name="key" size="lg" />
              <span>{yedekAnahtarCumlesi(seciliSatir?.kurtarma)}</span>
            </p>
          )}

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {!kayipKipi && (
              <TextField
                label="Parolanız"
                type="password"
                value={parola}
                onChange={(e) => parolaDegisti(e.target.value)}
                autoComplete="current-password"
                disabled={calisiyor}
                helperText="Bu oturumu açan hesabın bugünkü parolası; yalnız bu bilgisayarda alınmış yedeği açar. İkisinden birini girin."
              />
            )}
            <TextField
              label="Kurtarma anahtarı"
              value={anahtar}
              onChange={(e) => anahtarDegisti(e.target.value)}
              autoComplete="off"
              disabled={calisiyor}
              helperText={
                kayipKipi
                  ? "Yedeğin alındığı gün geçerli olan kurtarma anahtarı (kurtarma anahtarı belgesindeki)."
                  : "Parolayla açılmıyorsa (ör. başka bilgisayarda alınmış yedek) yedeğin alındığı gün geçerli olan anahtar."
              }
            />
          </div>

          {hata && (
            <p role="alert" className="mt-3 text-body-small text-error">
              {hata}
            </p>
          )}

          {ekOnayi && (
            <div
              ref={ikinciOnayRef}
              role="alert"
              tabIndex={-1}
              className="mt-3 rounded-shape-sm bg-error-container p-4 text-on-error-container outline-none"
            >
              <p className="text-body-medium">{ekOnayi.ileti}</p>
              <EkListesi ekler={ekOnayi.rapor.ekler} />
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  icon="settings_backup_restore"
                  onClick={() => void gonder(true)}
                  disabled={mesgul}
                >
                  {calisiyor ? "Geri yükleniyor…" : EKLER_OLMADAN_GERI_YUKLE}
                </Button>
                <Button variant="text" onClick={() => setEkOnayi(null)} disabled={calisiyor}>
                  Vazgeç
                </Button>
              </div>
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <Button
              icon="settings_backup_restore"
              onClick={() => void geriYukle()}
              disabled={
                mesgul ||
                ekOnayi !== null ||
                kaynak === null ||
                (kaynak.tur === "yol" && kaynak.okunuyor)
              }
            >
              {calisiyor && ekOnayi === null ? "Geri yükleniyor…" : "Geri yükle"}
            </Button>
            <Button variant="text" icon="refresh" onClick={yukle} disabled={calisiyor}>
              Listeyi yenile
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
