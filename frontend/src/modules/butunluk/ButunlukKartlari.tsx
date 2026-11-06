// Genel Bakış'ın denetim izi uyarı kartları (tasarım §4.6.3 "Kilit açılışında kendiliğinden
// doğrulama", §4.6.1 kural 1 ve 4, §4.4.4 geri yükleme notu; plan F1b-1 "Bütünlük ve mühür
// kartları 1. adımda Genel Bakış'tadır"). Hepsi bütünlük uçlarının bileşik durumundan beslenir
// (`useButunlukDurumu`); söyleyecek bir şeyi olmayan kart hiçbir şey çizmez.
//
// * **Denetim İzi Bütünlüğü** — oturumdaki hesabın bir önceki girişinden beri kilit
//   açılışındaki denetimin bulguları (her bulgu kendi sade cümlesiyle; kod yok). Yalnız
//   "kesinti" varsa bilgi tonundadır. Bulgulardan biri değişiklik gösteriyorsa (`metinler.
//   degisiklikGosterir`; tanınmayan kod da) kart "değişiklik buldu" der ve geri yüklemeyi
//   öğütler; yalnız denetleyemeyen bulgular (kilit işareti yok ya da okunamadı, denetim
//   düştü…) varsa "bir bölümünü denetleyemedi" der: değişiklik iddia etmez, ama "değişiklik
//   değildir" de demez (denetlenemeyen bölümde bilinmez). Bulgu denetim izinde kalır, kart bir
//   sonraki girişte kalkar.
// * **Değiştirilmiş Hesap Kaydı** — girişte ya da bir hesap işleminde hesabın kaydı tutmadı:
//   işlem yapılmadı, kayda dokunulmadı (tehdit 19). Bulgular türüne göre üç grupta yazılır
//   (`metinler.hesapBulgusuTuru`): kaydı değiştirilmiş görünen hesap (mühür ya da satırın izi),
//   denetim izindeki boşluk, parola kaydı hesap kaydıyla uyuşmayan hesap. Hesap rol etiketi,
//   tanıtıcı ve günleriyle anılır; mühür bulgusunda rol kaydın BUGÜN söylediğidir
//   (değiştirilmiş olabilir; "kayıtta yazan rol"), ötekilerde kaydın mührü tutar.
// * **Yedekten Geri Yükleme Yapıldı** — son geri yükleme: yedeğin adı (programın ürettiği
//   yedekse), yedeği açan yol (hesap ya da kurtarma anahtarı no'su), uygulama içinden
//   yapıldıysa onu başlatan oturumun hesabı (kurtarma yolunda da; konsolda oturum yok),
//   kenara alınan önceki veritabanı ve onun son kaydı ("Kayıt no · Zincir"), yedeğin kapsamı ve
//   eklerin kişisiz sayıları (plan F1b-3 "Geri yükleme"; bu bilgiyi taşımayan eski satırda
//   çizilmez). Aralarında giriş yapılmadan birden çok geri yükleme olduysa hepsi sırasıyla
//   yazılır: yedekten sonraki
//   kayıtlar İLKİNİN kenara aldığı veritabanındadır. O veritabanı yoktuysa ya da izi boştuysa
//   (yeni bilgisayara taşıma) kart "kayıtlar ekrandan kalktı" demez. Kart Denetleme Kurulunun
//   bir üyesi "Gördüm" diyene dek kalır (plan F1b-2 "Gördüm."; kullanıcı kararı 02.11.2026: bir
//   üye yeter, kart herkes için kalkar, kimin gördüğü izde kalır). Düğme yalnız
//   `geri_yukleme_gordum` yeteneğinde çizilir (`GordumDugmesi`; `POST security/integrity/
//   restore-seen/` `{seq}`); yanıt güncel denetim kartlarıdır. Kartın gösterdiği geri yükleme
//   artık son geri yükleme değilse (409 `geri_yukleme_guncel_degil`) kartlar yeniden okunur ve
//   sunucunun iletisi düğmenin altında kalır. Açık Denetleme Kurulu hesabı yoksa kart program
//   yöneticisinde kalır; metni bunu söyler.
// * **Hesaplar ve Güvenlik Dosyası** — iki depo farkı ve mührü tutmayan hesaplar
//   (`IkiDepoKarti`; onaylı silme orada).
// * **Eksik Ekler** — satırı olup dosyası olmayan ekler, canlı (tasarım §4.4.7 "Yetim ve eksik
//   dosya"). Özgün ad yalnız bu kartta ve kaydın kendisinde görünür (kullanıcı kararı 04.11.2026;
//   uç kilitliyken kapalıdır). Depo okunamadıysa ("eksik_ekler" `okunamayan`'da) kart "eksik yok"
//   demez, okunamadığını söyler.
// * **Bütünlük Durumu Okunamadı** — kartlardan biri ya da hepsi okunamadı (`okunamayan`,
//   `useButunlukDurumu.okunamadi`; Son Girişler ve denetim izinin son kaydı da): bir uyarı ya
//   da giriş sessizce kaybolmaz (fail-closed).
//
// ROL: ilk üç kart, mührü tutmayan hesaplar ve eksik ekler denetim kartları ucundandır (program
// yöneticisi ve Denetleme Kurulu), iki depo farkı ve silme yalnız program yöneticisinde; öteki rollerde o
// uçlar çağrılmaz, kartları boş kalır (`butunluk/api.ts` "ROLE GÖRE ÜÇ UÇ"). "Bütünlük Durumu
// Okunamadı" her rolde kalır.

import { useState } from "react";

import { ApiError } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import ErrorBand from "../../ui/ErrorBand";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { eklerOzeti, kapsamMetni } from "../guvenlik/yedekBilgisi";
import { oturumHataMetni } from "../oturum/hatalar";
import { butunlukApi, EKSIK_EKLER_KARTI } from "./api";
import type {
  ButunlukBulgusu,
  ButunlukDurumu,
  DenetimKartlari,
  EksikEk,
  GeriYuklemeKaydi,
  GeriYuklemeOzeti,
  HesapOzeti,
  IkiDepoYaniti,
} from "./api";
import IkiDepoKarti from "./IkiDepoKarti";
import KartKabugu from "./KartKabugu";
import {
  BILINMEYEN_BULGU_METNI,
  DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
  DENETIM_BILGI_CUMLESI,
  DENETIM_DEGISIKLIK_CUMLESI,
  DENETIM_DENETLENEMEDI_CUMLESI,
  DENETIM_DENETLENEMEDI_DIP_CUMLESI,
  DENETIM_IZI_KARTI_BASLIGI,
  DENETLEME_KURULUNA_BILDIRIN,
  EKSIK_EKLER_DIP_CUMLESI,
  EKSIK_EKLER_KARTI_BASLIGI,
  EKSIK_EKLER_OKUNAMADI_METNI,
  GERI_YUKLEME_BILDIRIN,
  GERI_YUKLEME_EKLER_ETIKETI,
  GERI_YUKLEME_KAPSAM_ETIKETI,
  GERI_YUKLEME_KARTI_BASLIGI,
  GORDUM_ACIKLAMASI,
  GORDUM_DUGMESI,
  GORDUM_KART_KALKTI,
  GORDUM_KAYDEDILEMEDI,
  GORDUM_KAYDEDILIYOR,
  IZ_BOSLUGU_GIRISI,
  KAYIT_DEGISMIS_GIRISI,
  OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI,
  OKUNAMAYAN_BUTUNLUK_METNI,
  PAROLA_KAYDI_ACIKLAMASI,
  PAROLA_KAYDI_GIRISI,
  ROL_DEGISMIS_OLABILIR,
  bulguMetinleri,
  degisiklikGosterir,
  eksikEklerGirisi,
  eksikEkSatiri,
  hesapBulgusuTuru,
  hesapEtiketiGunlu,
  hesapGunleri,
  kagitCapasiSatiri,
} from "./metinler";

const KART_KALKAR_METNI =
  "Bulgu denetim izinde kayıtlıdır; bu kart bir sonraki girişinizde kalkar.";

export function DenetimIziKarti({ bulgular }: { bulgular: readonly ButunlukBulgusu[] }) {
  const denetimler = bulgular.filter((b) => b.tur === "dogrulama");
  if (denetimler.length === 0) return null;
  const yalnizBilgi = denetimler.every((b) => b.duzey === "bilgi");
  // Bulgu listesi okunamayan uyarı satırı da değişiklik sayılır (fail-closed).
  const degisiklik =
    !yalnizBilgi &&
    denetimler.some(
      (b) =>
        b.duzey !== "bilgi" && (b.bulgular.length === 0 || b.bulgular.some(degisiklikGosterir)),
    );
  const giris = yalnizBilgi
    ? DENETIM_BILGI_CUMLESI
    : degisiklik
      ? DENETIM_DEGISIKLIK_CUMLESI
      : DENETIM_DENETLENEMEDI_CUMLESI;

  return (
    <KartKabugu
      id="denetim-izi-karti"
      baslik={DENETIM_IZI_KARTI_BASLIGI}
      ikon={yalnizBilgi ? "info" : "gpp_maybe"}
      ton={yalnizBilgi ? "bilgi" : degisiklik ? "hata" : "uyari"}
    >
      <p className="text-body-medium text-on-surface">{giris}</p>
      <ul className="space-y-2">
        {denetimler.map((b) => {
          const metinler = bulguMetinleri(b.bulgular);
          return (
            <li key={b.seq}>
              <p className="text-label-large text-on-surface-variant">
                {formatDateTime(b.zaman)}
                {b.duzey === "bilgi" ? " · bilgi" : ""}
              </p>
              <ul className="mt-1 list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
                {(metinler.length > 0 ? metinler : [BILINMEYEN_BULGU_METNI]).map((metin) => (
                  <li key={metin}>{metin}</li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>
      {degisiklik && (
        <p className="text-body-small text-on-surface-variant">
          Kayıtlar program dışından değiştirilmiş ya da veritabanı eski bir kopyayla değiştirilmiş
          olabilir. Program yöneticisine ve Denetleme Kuruluna bildirin; gerekirse sağlam bir
          yedekten geri yüklenir.
        </p>
      )}
      {!yalnizBilgi && !degisiklik && (
        <p className="text-body-small text-on-surface-variant">
          {DENETIM_DENETLENEMEDI_DIP_CUMLESI}
        </p>
      )}
      <p className="text-body-small text-on-surface-variant">{KART_KALKAR_METNI}</p>
    </KartKabugu>
  );
}

const KAYIT_OKUNAMAYAN_HESAP = "Kaydı okunamayan bir hesap";

/**
 * Mührü tutmayan hesabın kişisiz anılışı: tanıtıcı + kaydın bugün söylediği rol (değiştirilmiş
 * olabilir) ve günleri: "Tanıtıcısı “muhasip” olan hesap (kayıtta yazan rol: Sekreter; açılış
 * 01.11.2026)".
 */
export function degistirilmisHesap(hesap: HesapOzeti | null): string {
  if (hesap === null || hesap.tanitici === null) return KAYIT_OKUNAMAYAN_HESAP;
  const ekler = [
    hesap.rol_etiketi === null ? null : `kayıtta yazan rol: ${hesap.rol_etiketi}`,
    hesapGunleri(hesap),
  ].filter((ek): ek is string => ek !== null);
  const ek = ekler.length === 0 ? "" : ` (${ekler.join("; ")})`;
  return `Tanıtıcısı “${hesap.tanitici}” olan hesap${ek}`;
}

/** Mührü tutan hesabın anılışı (satırın izi, iz boşluğu, parola kaydı): kayıttaki rol doğrudur. */
function muhurluHesap(hesap: HesapOzeti | null): string {
  if (hesap === null || hesap.tanitici === null) return KAYIT_OKUNAMAYAN_HESAP;
  return hesapEtiketiGunlu(hesap);
}

function BulguListesi({
  bulgular,
  ad,
}: {
  bulgular: readonly ButunlukBulgusu[];
  ad: (b: ButunlukBulgusu) => string;
}) {
  return (
    <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
      {bulgular.map((b) => (
        <li key={b.seq}>
          {ad(b)} · {formatDateTime(b.zaman)}
        </li>
      ))}
    </ul>
  );
}

/**
 * Değiştirilmiş Hesap Kaydı (sözlük §4.5): hesap bulguları türüne göre üç grupta yazılır —
 * kaydı değiştirilmiş görünen hesap (mühür ya da satırın izi), denetim izindeki boşluk, parola
 * kaydı (`metinler.hesapBulgusuTuru`). Metin nötrdür: olay giriş de olabilir hesap işlemi de.
 */
export function DegistirilmisHesapKarti({ bulgular }: { bulgular: readonly ButunlukBulgusu[] }) {
  const hesapBulgulari = bulgular.filter((b) => b.tur === "muhur");
  if (hesapBulgulari.length === 0) return null;
  const turu = (b: ButunlukBulgusu) => hesapBulgusuTuru(b.bulgular);
  const kayit = hesapBulgulari.filter((b) => turu(b) === "muhur" || turu(b) === "kayit");
  const bosluk = hesapBulgulari.filter((b) => turu(b) === "bosluk");
  const parolaKaydi = hesapBulgulari.filter((b) => turu(b) === "parola_kaydi");
  const muhurVar = kayit.some((b) => turu(b) === "muhur");

  return (
    <KartKabugu
      id="degistirilmis-hesap-karti"
      baslik={DEGISTIRILMIS_HESAP_KARTI_BASLIGI}
      ikon="manage_accounts"
      ton="hata"
    >
      {kayit.length > 0 && (
        <div className="space-y-1">
          <p className="text-body-medium text-on-surface">{KAYIT_DEGISMIS_GIRISI}</p>
          <BulguListesi
            bulgular={kayit}
            ad={(b) => (turu(b) === "muhur" ? degistirilmisHesap(b.hesap) : muhurluHesap(b.hesap))}
          />
          {muhurVar && (
            <p className="text-body-small text-on-surface-variant">{ROL_DEGISMIS_OLABILIR}</p>
          )}
        </div>
      )}
      {bosluk.length > 0 && (
        <div className="space-y-1">
          <p className="text-body-medium text-on-surface">{IZ_BOSLUGU_GIRISI}</p>
          <BulguListesi bulgular={bosluk} ad={(b) => muhurluHesap(b.hesap)} />
        </div>
      )}
      {parolaKaydi.length > 0 && (
        <div className="space-y-1">
          <p className="text-body-medium text-on-surface">{PAROLA_KAYDI_GIRISI}</p>
          <BulguListesi bulgular={parolaKaydi} ad={(b) => muhurluHesap(b.hesap)} />
          <p className="text-body-small text-on-surface-variant">{PAROLA_KAYDI_ACIKLAMASI}</p>
        </div>
      )}
      <p className="text-body-small text-on-surface-variant">
        {DENETLEME_KURULUNA_BILDIRIN} {KART_KALKAR_METNI}
      </p>
    </KartKabugu>
  );
}

/** Yedeği açan yolun cümlesi (tasarım §4.4.4 "kullanılan yol"). */
function yedegiAcan(geri: GeriYuklemeKaydi): string {
  if (geri.yol === "kurtarma") {
    return geri.kurtarma_no === null
      ? "Kurtarma anahtarı"
      : `Kurtarma anahtarı (anahtar no ${geri.kurtarma_no})`;
  }
  if (geri.yol === "hesap") {
    return geri.yol_hesap === null
      ? "Bir hesabın parolası"
      : `${hesapEtiketiGunlu(geri.yol_hesap)} hesabının parolası`;
  }
  return "Okunamadı";
}

/**
 * Geri yüklemeden önce bu bilgisayarda kayıt yok muydu? Kenara alınacak veritabanı yoktu ya da
 * izi boştu (yeni bilgisayara taşıma; ilk hesap kurulmadan kayıt girilemez). Ayrıntısız ya da
 * son kaydı bilinmeyen geri yüklemede bilinmez: hayır.
 */
export function oncedenKayitYoktu(geri: GeriYuklemeKaydi): boolean {
  if (geri.ayrintisiz) return false;
  return (
    geri.onceki_kayit_no === 0 || (geri.onceki_dosya === null && geri.onceki_kayit_no === null)
  );
}

/**
 * Bir geri yüklemenin ayrıntıları: an, yedek, açan yol, başlatan oturum, kenara alınan, kapsam ve
 * ekler. Dosya bilgisini taşımayan eski satırda (`dosyalar` boş) kapsam ve ek satırı çizilmez.
 */
function GeriYuklemeAyrintisi({ geri }: { geri: GeriYuklemeKaydi }) {
  const oncekiSonKayit =
    geri.onceki_kayit_no !== null && geri.onceki_zincir !== null
      ? kagitCapasiSatiri({ kayit_no: geri.onceki_kayit_no, zincir: geri.onceki_zincir })
      : null;
  const dosyalar = geri.dosyalar ?? {};
  const kapsam = kapsamMetni(dosyalar.kapsam ?? null);
  const ekler = eklerOzeti(dosyalar);
  return (
    <>
      {geri.ayrintisiz && (
        <p className="text-body-medium text-on-surface">
          Geri yüklemenin ayrıntıları okunamadı; olgu denetim izinde kayıtlıdır.
        </p>
      )}
      {(geri.geri_yukleme_ani !== null || !geri.ayrintisiz) && (
        <dl className="grid gap-x-4 gap-y-1 text-body-medium sm:grid-cols-[auto_1fr]">
          {geri.geri_yukleme_ani !== null && (
            <>
              <dt className="text-label-large text-on-surface-variant">Geri yükleme anı</dt>
              <dd className="min-w-0 text-on-surface">{formatDateTime(geri.geri_yukleme_ani)}</dd>
            </>
          )}
          {!geri.ayrintisiz && (
            <>
              <dt className="text-label-large text-on-surface-variant">Yedek</dt>
              <dd className="min-w-0 break-words text-on-surface">
                {geri.yedek !== null ? (
                  <span className="font-mono">{geri.yedek}</span>
                ) : (
                  "Elden getirilen dosya (adı kayda geçmez)"
                )}
              </dd>
              <dt className="text-label-large text-on-surface-variant">Yedeği açan</dt>
              <dd className="min-w-0 text-on-surface">{yedegiAcan(geri)}</dd>
              {geri.oturum_hesap !== null && (
                <>
                  <dt className="text-label-large text-on-surface-variant">Başlatan oturum</dt>
                  <dd className="min-w-0 text-on-surface">
                    {hesapEtiketiGunlu(geri.oturum_hesap)}
                  </dd>
                </>
              )}
              {geri.onceki_dosya !== null && (
                <>
                  <dt className="text-label-large text-on-surface-variant">
                    Kenara alınan önceki veritabanı
                  </dt>
                  <dd className="min-w-0 break-words font-mono text-on-surface">
                    {geri.onceki_dosya}
                  </dd>
                </>
              )}
              {oncekiSonKayit !== null && (
                <>
                  <dt className="text-label-large text-on-surface-variant">
                    Önceki veritabanının son kaydı
                  </dt>
                  <dd className="min-w-0 font-mono text-on-surface">{oncekiSonKayit}</dd>
                </>
              )}
              {kapsam !== null && (
                <>
                  <dt className="text-label-large text-on-surface-variant">
                    {GERI_YUKLEME_KAPSAM_ETIKETI}
                  </dt>
                  <dd className="min-w-0 text-on-surface">{kapsam}</dd>
                </>
              )}
              {ekler !== null && (
                <>
                  <dt className="text-label-large text-on-surface-variant">
                    {GERI_YUKLEME_EKLER_ETIKETI}
                  </dt>
                  <dd className="min-w-0 text-on-surface">{ekler}</dd>
                </>
              )}
            </>
          )}
        </dl>
      )}
    </>
  );
}

/**
 * Kartın dip cümlesinin ilk yarısı: ekrandan kalkan kayıtlar nerede (sözlük §4.5). Kenara alınan
 * veritabanı 14 günlük rotasyondadır (tasarım §4.4.7), kart ise "Gördüm"e dek kalır ve iz
 * satırından okuduğu adı göstermeyi sürdürür: cümle dosyanın silineceğini söyler.
 */
export function geriYuklemeDipCumlesi(kayitlar: readonly GeriYuklemeKaydi[]): string {
  if (kayitlar.length > 0 && oncedenKayitYoktu(kayitlar[0])) {
    return "Geri yüklemeden önce bu bilgisayarda kayıt yoktu.";
  }
  return kayitlar.length > 1
    ? "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; ilk geri yüklemede " +
        "kenara alınan veritabanında durur. O dosya geri yüklemeden 14 gün sonra silinir."
    : "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; kenara alınan önceki " +
        "veritabanında durur. O dosya geri yüklemeden 14 gün sonra silinir.";
}

/** "Gördüm"ün işi (yalnız `geri_yukleme_gordum` yeteneğinde verilir). */
export interface GordumIslemi {
  /** Başarılı "Gördüm"den dönen güncel denetim kartları (`useButunlukDurumu.denetimiYaz`). */
  onDenetim: (yanit: DenetimKartlari) => void;
  /** Kartlar yeniden okunur (409 `geri_yukleme_guncel_degil`; `useButunlukDurumu.yenile`). */
  onYenile: () => void;
}

/** Kartın gösterdiği geri yükleme artık son geri yükleme değil (backend `RestoreCardStale`). */
const GUNCEL_DEGIL_KODU = "geri_yukleme_guncel_degil";

/**
 * Denetleme Kurulunun "Gördüm"ü (dosya başı): kartın gösterdiği (son) geri yüklemenin `seq`'i
 * gider. Başarıda yanıttaki güncel kartlar yazılır; kart kalktıysa snackbar söyler (düğme
 * kaybolur, odak düşer). Ret düğmenin altında sunucunun iletisiyle kalır; 409
 * `geri_yukleme_guncel_degil`de kartlar ayrıca yeniden okunur.
 */
function GordumDugmesi({ seq, islem }: { seq: number; islem: GordumIslemi }) {
  const snackbar = useSnackbar();
  const [mesgul, setMesgul] = useState(false);
  const [hata, setHata] = useState<string | null>(null);

  const gordum = async () => {
    setMesgul(true);
    setHata(null);
    try {
      const yanit = await butunlukApi.geriYuklemeyiGordum(seq);
      if (yanit.geri_yukleme === null || yanit.geri_yukleme === undefined) {
        snackbar.success(GORDUM_KART_KALKTI);
      }
      islem.onDenetim(yanit);
    } catch (e) {
      setHata(oturumHataMetni(e, GORDUM_KAYDEDILEMEDI));
      if (e instanceof ApiError && e.code === GUNCEL_DEGIL_KODU) islem.onYenile();
    } finally {
      setMesgul(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <Button variant="filled" icon="task_alt" onClick={() => void gordum()} disabled={mesgul}>
          {mesgul ? GORDUM_KAYDEDILIYOR : GORDUM_DUGMESI}
        </Button>
      </div>
      {hata && <ErrorBand hata={hata} />}
    </div>
  );
}

interface GeriYuklemeKartiProps {
  geri: GeriYuklemeOzeti | null;
  /** "Gördüm" (yalnız `geri_yukleme_gordum` yeteneğinde); verilmezse düğme yoktur. */
  gordum?: GordumIslemi | null;
}

export function GeriYuklemeKarti({ geri, gordum = null }: GeriYuklemeKartiProps) {
  if (geri === null) return null;
  // Eskiden yeniye; sonuncusu zamanca son geri yüklemedir.
  const kayitlar: GeriYuklemeKaydi[] = [...geri.onceki_geri_yuklemeler, geri];
  const coklu = kayitlar.length > 1;

  return (
    <KartKabugu
      id="geri-yukleme-karti"
      baslik={GERI_YUKLEME_KARTI_BASLIGI}
      ikon="settings_backup_restore"
      ton="uyari"
    >
      <p className="text-body-medium text-on-surface">
        {coklu
          ? `Kayıtlar, aralarında giriş yapılmadan ${kayitlar.length} kez yedekten geri ` +
            "yüklendi; geri yüklemeler, ardından yapılan ilk girişte denetim izine yazıldı."
          : "Kayıtlar bir yedekten geri yüklendi; geri yükleme, ardından yapılan ilk girişte " +
            "denetim izine yazıldı."}
      </p>
      <dl className="grid gap-x-4 gap-y-1 text-body-medium sm:grid-cols-[auto_1fr]">
        <dt className="text-label-large text-on-surface-variant">Denetim izine yazıldığı an</dt>
        <dd className="min-w-0 text-on-surface">{formatDateTime(geri.zaman)}</dd>
      </dl>
      {coklu ? (
        <ol className="space-y-3">
          {kayitlar.map((kayit, i) => (
            <li key={kayit.seq} className="space-y-1">
              <h3 className="text-title-small font-semibold text-on-surface">
                {i === kayitlar.length - 1
                  ? `${i + 1}. geri yükleme (son)`
                  : `${i + 1}. geri yükleme`}
              </h3>
              <GeriYuklemeAyrintisi geri={kayit} />
            </li>
          ))}
        </ol>
      ) : (
        <GeriYuklemeAyrintisi geri={geri} />
      )}
      <p className="text-body-small text-on-surface-variant">
        {geriYuklemeDipCumlesi(kayitlar)}{" "}
        {gordum === null ? GERI_YUKLEME_BILDIRIN : GORDUM_ACIKLAMASI}
      </p>
      {gordum !== null && <GordumDugmesi seq={geri.seq} islem={gordum} />}
    </KartKabugu>
  );
}

interface EksikEklerKartiProps {
  ekler: readonly EksikEk[];
  /** Depo okunamadı: boş liste "eksik yok" demek değildir. */
  okunamadi: boolean;
}

/**
 * Eksik Ekler (dosya başı): söyleyecek bir şey yoksa çizilmez. Liste uzun olabilir (depo silindiyse
 * bütün ekler); kendi içinde kayar. Ad kişi adı taşıyabilir, yalnız burada görünür.
 */
export function EksikEklerKarti({ ekler, okunamadi }: EksikEklerKartiProps) {
  if (ekler.length === 0 && !okunamadi) return null;
  return (
    <KartKabugu
      id="eksik-ekler-karti"
      baslik={EKSIK_EKLER_KARTI_BASLIGI}
      ikon="attach_file"
      ton="uyari"
    >
      {okunamadi && (
        <p className="text-body-medium text-on-surface">{EKSIK_EKLER_OKUNAMADI_METNI}</p>
      )}
      {ekler.length > 0 && (
        <>
          <p className="text-body-medium text-on-surface">{eksikEklerGirisi(ekler.length)}</p>
          {/* Kendi içinde kayar; klavyeyle de kaysın diye odak alır. */}
          <ul
            tabIndex={0}
            aria-label={EKSIK_EKLER_KARTI_BASLIGI}
            className="max-h-40 list-disc space-y-0.5 overflow-y-auto pl-5 pr-1 text-body-medium text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            {ekler.map((ek, sira) => (
              <li key={sira} className="break-words">
                {eksikEkSatiri(ek)}
              </li>
            ))}
          </ul>
          <p className="text-body-small text-on-surface-variant">{EKSIK_EKLER_DIP_CUMLESI}</p>
        </>
      )}
    </KartKabugu>
  );
}

/**
 * Bütünlük kartlarından biri ya da hepsi okunamadı (backend `okunamayan` ya da okuma düştü):
 * uyarı ya da giriş sessizce kaybolmaz (fail-closed). Son Girişler de kapsanır: o kart kendi
 * okunamayan bölümünü ayrıca söyler (`SonGirislerKarti`). Kart adları iç koddur, yazılmaz.
 */
export function OkunamayanButunlukKarti() {
  return (
    <KartKabugu
      id="okunamayan-butunluk-karti"
      baslik={OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI}
      ikon="report"
      ton="uyari"
    >
      <p className="text-body-medium text-on-surface">{OKUNAMAYAN_BUTUNLUK_METNI}</p>
    </KartKabugu>
  );
}

interface ButunlukKartlariProps {
  durum: ButunlukDurumu;
  /** Sahipsiz parola kaydı silinince gelen güncel iki depo kartı. */
  onIkiDepo: (yanit: IkiDepoYaniti) => void;
  /** Geri yükleme kartının "Gördüm"ü (yalnız `geri_yukleme_gordum` yeteneğinde). */
  gordum?: GordumIslemi | null;
  /** İki depo kartında Kullanıcılar'a bağlantı (yalnız `kullanicilar` yeteneğinde). */
  kullanicilarAcik?: boolean;
}

/** Uyarı kartları, sırasıyla; söyleyecek bir şeyi olmayan çizilmez. */
export default function ButunlukKartlari({
  durum,
  onIkiDepo,
  gordum = null,
  kullanicilarAcik = false,
}: ButunlukKartlariProps) {
  return (
    <>
      {durum.okunamayan.length > 0 && <OkunamayanButunlukKarti />}
      <DenetimIziKarti bulgular={durum.butunluk} />
      <DegistirilmisHesapKarti bulgular={durum.butunluk} />
      <GeriYuklemeKarti geri={durum.geri_yukleme} gordum={gordum} />
      {durum.iki_depo !== null && durum.iki_depo.fark_var && (
        <IkiDepoKarti
          fark={durum.iki_depo}
          onIkiDepo={onIkiDepo}
          kullanicilarAcik={kullanicilarAcik}
        />
      )}
      <EksikEklerKarti
        ekler={durum.eksik_ekler}
        okunamadi={durum.okunamayan.includes(EKSIK_EKLER_KARTI)}
      />
    </>
  );
}
