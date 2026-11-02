// Genel Bakış'ın denetim izi uyarı kartları (tasarım §4.6.3 "Kilit açılışında kendiliğinden
// doğrulama", §4.6.1 kural 1 ve 4, §4.4.4 geri yükleme notu; plan F1b-1 "Bütünlük ve mühür
// kartları 1. adımda Genel Bakış'tadır"). Hepsi `GET security/integrity/` durumundan beslenir
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
// * **Değiştirilmiş Hesap Kaydı** — girişte hesap mührü tutmadı: giriş açılmadı, kayda
//   dokunulmadı (tehdit 19). Hesap rol etiketi ve tanıtıcıyla anılır; rol, kaydın BUGÜN
//   söylediğidir (değiştirilmiş olabilir).
// * **Yedekten Geri Yükleme Yapıldı** — son geri yükleme: yedeğin adı (programın ürettiği
//   yedekse), yedeği açan yol (hesap ya da kurtarma anahtarı no'su), uygulama içinden
//   yapıldıysa onu başlatan oturumun hesabı (kurtarma yolunda da; konsolda oturum yok),
//   kenara alınan önceki veritabanı ve onun son kaydı ("Kayıt no · Zincir"). Aralarında giriş
//   yapılmadan birden çok geri yükleme olduysa hepsi sırasıyla yazılır: yedekten sonraki
//   kayıtlar İLKİNİN kenara aldığı veritabanındadır. O veritabanı yoktuysa ya da izi boştuysa
//   (yeni bilgisayara taşıma) kart "kayıtlar ekrandan kalktı" demez. Kart Denetleme Kurulu
//   "gördüm" diyene dek kalır; Denetleme Kurulu hesapları ve o düğme F1b 2. adımdadır — bugün
//   kart hep durur.
// * **Hesaplar ve Güvenlik Dosyası** — iki depo farkı (`IkiDepoKarti`; onaylı silme orada).
// * **Bütünlük Durumu Okunamadı** — kartlardan biri ya da hepsi okunamadı (`okunamayan`,
//   `useButunlukDurumu.okunamadi`; Son Girişler ve denetim izinin son kaydı da): bir uyarı ya
//   da giriş sessizce kaybolmaz (fail-closed).
//
// Rol süzmesi (yalnız program yöneticisi ve Denetleme Kurulu görür) 2. adımdadır.

import { formatDateTime } from "../../lib/format";
import type {
  ButunlukBulgusu,
  ButunlukDurumu,
  GeriYuklemeKaydi,
  GeriYuklemeOzeti,
  HesapOzeti,
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
  GERI_YUKLEME_KARTI_BASLIGI,
  OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI,
  OKUNAMAYAN_BUTUNLUK_METNI,
  bulguMetinleri,
  degisiklikGosterir,
  hesapEtiketi,
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

/** Mührü tutmayan hesabın kişisiz anılışı: tanıtıcı + kaydın bugün söylediği rol. */
function degistirilmisHesap(hesap: HesapOzeti | null): string {
  if (hesap === null || hesap.tanitici === null) return "Kaydı okunamayan bir hesap";
  const rol = hesap.rol_etiketi === null ? "" : ` (kayıtta yazan rol: ${hesap.rol_etiketi})`;
  return `Tanıtıcısı “${hesap.tanitici}” olan hesap${rol}`;
}

export function DegistirilmisHesapKarti({ bulgular }: { bulgular: readonly ButunlukBulgusu[] }) {
  const muhurler = bulgular.filter((b) => b.tur === "muhur");
  if (muhurler.length === 0) return null;

  return (
    <KartKabugu
      id="degistirilmis-hesap-karti"
      baslik={DEGISTIRILMIS_HESAP_KARTI_BASLIGI}
      ikon="manage_accounts"
      ton="hata"
    >
      <p className="text-body-medium text-on-surface">
        Kaydı program dışından değiştirilmiş görünen hesapla giriş denendi; giriş açılmadı ve
        program kayda dokunmadı:
      </p>
      <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
        {muhurler.map((b) => (
          <li key={b.seq}>
            {degistirilmisHesap(b.hesap)} · {formatDateTime(b.zaman)}
          </li>
        ))}
      </ul>
      <p className="text-body-small text-on-surface-variant">
        Kayıtta yazan rol, değiştirilmiş rol olabilir. Durumu Denetleme Kuruluna bildirin.{" "}
        {KART_KALKAR_METNI}
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
      : `${hesapEtiketi(geri.yol_hesap)} hesabının parolası`;
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

/** Bir geri yüklemenin ayrıntıları: an, yedek, açan yol, başlatan oturum, kenara alınan. */
function GeriYuklemeAyrintisi({ geri }: { geri: GeriYuklemeKaydi }) {
  const oncekiSonKayit =
    geri.onceki_kayit_no !== null && geri.onceki_zincir !== null
      ? kagitCapasiSatiri({ kayit_no: geri.onceki_kayit_no, zincir: geri.onceki_zincir })
      : null;
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
                  <dd className="min-w-0 text-on-surface">{hesapEtiketi(geri.oturum_hesap)}</dd>
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
            </>
          )}
        </dl>
      )}
    </>
  );
}

/** Kartın dip cümlesinin ilk yarısı: ekrandan kalkan kayıtlar nerede (sözlük §4.5). */
export function geriYuklemeDipCumlesi(kayitlar: readonly GeriYuklemeKaydi[]): string {
  if (kayitlar.length > 0 && oncedenKayitYoktu(kayitlar[0])) {
    return "Geri yüklemeden önce bu bilgisayarda kayıt yoktu.";
  }
  return kayitlar.length > 1
    ? "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; ilk geri yüklemede " +
        "kenara alınan veritabanında durur."
    : "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; kenara alınan önceki " +
        "veritabanında durur.";
}

export function GeriYuklemeKarti({ geri }: { geri: GeriYuklemeOzeti | null }) {
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
        {geriYuklemeDipCumlesi(kayitlar)} Geri yüklemeyi kimin ve neden yaptığını Denetleme Kuruluna
        bildirin. Kart, son geri yüklemeyi göstermeyi sürdürür.
      </p>
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
  /** Sahipsiz parola kaydı silinince gelen güncel durum. */
  onDurum: (durum: ButunlukDurumu) => void;
}

/** Uyarı kartları, sırasıyla; söyleyecek bir şeyi olmayan çizilmez. */
export default function ButunlukKartlari({ durum, onDurum }: ButunlukKartlariProps) {
  return (
    <>
      {durum.okunamayan.length > 0 && <OkunamayanButunlukKarti />}
      <DenetimIziKarti bulgular={durum.butunluk} />
      <DegistirilmisHesapKarti bulgular={durum.butunluk} />
      <GeriYuklemeKarti geri={durum.geri_yukleme} />
      {durum.iki_depo !== null && durum.iki_depo.fark_var && (
        <IkiDepoKarti fark={durum.iki_depo} onDurum={onDurum} />
      )}
    </>
  );
}
