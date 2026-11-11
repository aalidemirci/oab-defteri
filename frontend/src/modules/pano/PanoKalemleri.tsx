// Genel Bakış'ın pano kalemleri (tasarım §7.10 "Pano ve takvim"; plan F1c 12. adım "pano kabuğu").
//
// Açılış ekranının listesi: rolün "Bu Hafta Yapılacaklar"ı — son günü yedi gün içinde olan ya da
// geçmiş kalemler önde (sunucu son güne göre sıralar), süresi olmayan işler ardından; son günü
// pencerenin ötesindeki kalem listeye girmez (takvim görünümü ve E14 sonraki fazdadır). Veli
// rollerinde (sunucunun `gorunum: "ay"`ı; ön yüz rol adıyla dallanmaz) varsayılan görünüm "Bu Ay
// Sizden Beklenenler"dir ve büyük yazıyla açılır (§7.10 "Teslim yolu"; R5): başlık, açıklama, son gün,
// dayanak, götürdüğü ekran, rozet ve bilgi bandı birlikte bir basamak büyür; pencere ayın son
// günüdür, en az yedi gün. Ailenin yoğunluk ayarı yazı boyutunu değiştirmez (yalnız denetim yüksekliği), bu
// yüzden büyük yazı listenin kendi sınıflarıdır; kullanıcının yoğunluk seçimine dokunulmaz.
// "Tamamlanacaklar" ayrı bölümdür (açık `ComplianceItem(EKSIK)`; O3), boşsa çizilmez.
//
// Kalemler saklanmaz: her açılışta ve gün değişiminde (yerel gün dakikada bir yoklanır, değişince
// sorgu anahtarı değişir) sunucuda yeniden hesaplanır; sorgu hiç taze sayılmaz (`staleTime: 0`), bu
// yüzden ilgili kayıt başka ekranda yazılınca Genel Bakış'a dönüş yeni okumadır. Kalem kişisizdir, gerekçe istemez ve tek tıkla
// götürdüğü ekrana (rota + sekme) açılır; kişi ancak orada, rolün okuma yetkisi içinde görünür.
// Bilgi bantları (kural kopyası doğrulanamayan dönem, açık birlik dönemi yok) listenin başındadır.
// Kilitliyken (423) ya da anahtar düşmüşken (409) hata söylenmez: kilit ekranı gelir.

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { todayIso } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import Skeleton from "../../ui/Skeleton";
import { KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { okunamadiSayilir } from "../butunluk/useButunlukDurumu";
import { DUGME_BIRLIK_DONEMINE_GIT } from "../organlar/metinler";
import { Dayanak } from "../uyum/UyariGerekce";
import { panelApi } from "./api";
import type { PanoKalemi, PanoYaniti } from "./api";
import {
  AY_ACIKLAMASI,
  AY_BASLIGI,
  AY_BOS,
  DONEM_IPTAL_BILGISI,
  DONEM_YOK_BILGISI,
  EKSIK_ROZETI,
  HAFTA_ACIKLAMASI,
  HAFTA_BASLIGI,
  HAFTA_BOS,
  PANO_OKUNAMADI,
  PANO_YUKLENIYOR,
  TAMAMLANACAKLAR_ACIKLAMASI,
  TAMAMLANACAKLAR_BASLIGI,
  YENIDEN_DENE,
  ekranAdi,
  kalemAciklamasi,
  kalemBasligi,
  vadeCumlesi,
} from "./metinler";

export const PANO_SORGU_ANAHTARI = "pano";
/** Yerel günün yoklama aralığı (gün değişimi). */
export const GUN_YOKLAMA_MS = 60_000;
/** "Bu hafta": bugünden itibaren gün sayısı (tasarım §7.10 "vadesi yedi gün içinde"). */
const HAFTA_GUN = 7;

/** Yerel gün (ISO); `GUN_YOKLAMA_MS`'de bir yoklanır, gün değişince yeni değer döner. */
export function useGunAnahtari(aralikMs: number = GUN_YOKLAMA_MS): string {
  const [gun, setGun] = useState(todayIso);
  useEffect(() => {
    const saat = window.setInterval(() => setGun(todayIso()), aralikMs);
    return () => window.clearInterval(saat);
  }, [aralikMs]);
  return gun;
}

/** Takvim günü (UTC alanlarıyla kurulmuş `Date`) → ISO; saat dilimi kayması yoktur. */
function isoGun(gun: Date): string {
  const ay = String(gun.getUTCMonth() + 1).padStart(2, "0");
  const gunu = String(gun.getUTCDate()).padStart(2, "0");
  return `${gun.getUTCFullYear()}-${ay}-${gunu}`;
}

/** Görünümün son günü (ISO): haftada bugün + 7, ayda ayın son günü (en az bugün + 7). */
export function pencereSonu(bugun: string, gorunum: PanoYaniti["gorunum"]): string {
  const [yil, ay, gun] = bugun.split("-").map(Number);
  const hafta = new Date(Date.UTC(yil, ay - 1, gun + HAFTA_GUN));
  if (gorunum === "hafta") return isoGun(hafta);
  const aySonu = new Date(Date.UTC(yil, ay, 0));
  return isoGun(aySonu > hafta ? aySonu : hafta);
}

/** Listeye giren işler: süresizler ve son günü pencere içinde ya da geçmiş olanlar (sunucu sırası). */
export function gorunenIsler(yanit: PanoYaniti): PanoKalemi[] {
  const son = pencereSonu(yanit.bugun, yanit.gorunum);
  return yanit.isler.filter((kalem) => kalem.vade === null || kalem.vade <= son);
}

function hedef(kalem: PanoKalemi): string {
  return kalem.sekme ? `${kalem.rota}?tab=${kalem.sekme}` : kalem.rota;
}

function bilgiMetni(kalem: PanoKalemi): string {
  if (kalem.kod === "KURAL_KOPYASI_DOGRULANAMADI") return KURAL_KOPYASI_BOZUK;
  return kalem.ek.son_durum === "IPTAL" ? DONEM_IPTAL_BILGISI : DONEM_YOK_BILGISI;
}

/** Satırın ikincil yazısı (dayanak, ekran, tamamlanacaklar açıklaması): veli görünümünde bir basamak büyük. */
function metaBoyutu(buyuk: boolean): string {
  return buyuk ? "text-body-medium" : "text-body-small";
}

function Bilgiler({ bilgiler, buyuk }: { bilgiler: PanoKalemi[]; buyuk: boolean }) {
  if (bilgiler.length === 0) return null;
  return (
    <div className="mt-4 space-y-2">
      {bilgiler.map((bilgi) => (
        <div
          key={bilgi.kod}
          role="status"
          className={`flex items-start gap-2 rounded-shape-md bg-secondary-container px-4 py-3 text-on-secondary-container ${buyuk ? "text-body-large" : "text-body-medium"}`}
        >
          <Icon name="info" />
          <div className="min-w-0">
            <p className="break-words">{bilgiMetni(bilgi)}</p>
            <Link
              to={hedef(bilgi)}
              className="mt-1 inline-flex items-center gap-1 text-label-large font-medium underline-offset-4 hover:underline"
            >
              {DUGME_BIRLIK_DONEMINE_GIT}
              <Icon name="arrow_forward" size="sm" />
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

function IsSatiri({ kalem, buyuk }: { kalem: PanoKalemi; buyuk: boolean }) {
  const vade = vadeCumlesi(kalem);
  const meta = metaBoyutu(buyuk);
  return (
    <li>
      <Link
        to={hedef(kalem)}
        className="group flex items-start gap-3 rounded-shape-md px-2 py-3 hover:bg-on-surface/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <Icon
          name={kalem.gecikti ? "schedule" : kalem.vade ? "event" : "radio_button_unchecked"}
          className={`mt-0.5 ${kalem.gecikti ? "text-error" : "text-on-surface-variant"}`}
        />
        <span className="min-w-0 flex-1 space-y-0.5">
          <span
            className={`block break-words font-medium text-on-surface ${buyuk ? "text-title-large" : "text-body-large"}`}
          >
            {kalemBasligi(kalem)}
          </span>
          <span
            className={`block break-words text-on-surface-variant ${buyuk ? "text-body-large" : "text-body-medium"}`}
          >
            {kalemAciklamasi(kalem)}
          </span>
          <span
            className={`flex flex-wrap items-center gap-x-3 gap-y-1 text-on-surface-variant ${meta}`}
          >
            {vade && (
              <span
                className={`font-medium ${kalem.gecikti ? "text-error" : "text-on-surface"} ${buyuk ? "text-body-large" : ""}`}
              >
                {vade}
              </span>
            )}
            <Dayanak atif={kalem.atif} className={meta} />
            <span>{ekranAdi(kalem)}</span>
          </span>
        </span>
        <Icon name="arrow_forward" className="mt-0.5 shrink-0 text-primary" />
      </Link>
    </li>
  );
}

function TamamlanacakSatiri({ kalem, buyuk }: { kalem: PanoKalemi; buyuk: boolean }) {
  const meta = metaBoyutu(buyuk);
  return (
    <li>
      <Link
        to={hedef(kalem)}
        className="flex items-start gap-3 rounded-shape-md px-2 py-2 hover:bg-on-surface/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <span
          className={`mt-0.5 inline-flex shrink-0 items-center rounded-full bg-secondary-container px-2 py-0.5 text-on-secondary-container ${buyuk ? "text-label-large" : "text-label-medium"}`}
        >
          {EKSIK_ROZETI}
        </span>
        <span className="min-w-0 flex-1 space-y-0.5">
          <span
            className={`block break-words text-on-surface ${buyuk ? "text-body-large" : "text-body-medium"}`}
          >
            {kalem.metin}
          </span>
          <span className={`flex flex-wrap gap-x-3 text-on-surface-variant ${meta}`}>
            <Dayanak atif={kalem.atif} className={meta} />
            <span>{ekranAdi(kalem)}</span>
          </span>
        </span>
        <Icon name="arrow_forward" className="mt-0.5 shrink-0 text-primary" />
      </Link>
    </li>
  );
}

export default function PanoKalemleri() {
  const gun = useGunAnahtari();
  const sorgu = useQuery({
    queryKey: [PANO_SORGU_ANAHTARI, gun],
    queryFn: panelApi.kalemler,
    retry: false,
    // Her açılış yeni okumadır (tasarım §7.10 "her açılışta … hesaplanır"): ailenin 30 sn'lik
    // tazeliği burada geçerli değil; bağlanışta yeniden okunur (odakta yeniden okuma açılmaz).
    staleTime: 0,
  });

  if (sorgu.isPending) {
    return (
      <Card elevation={1} className="p-5 sm:p-6">
        <div role="status" aria-busy="true" className="space-y-3">
          <span className="sr-only">{PANO_YUKLENIYOR}</span>
          <Skeleton className="h-6 w-56" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </Card>
    );
  }
  if (sorgu.isError) {
    if (!okunamadiSayilir(sorgu.error)) return null;
    return (
      <div
        role="alert"
        className="flex flex-wrap items-center justify-between gap-3 rounded-shape-md bg-error-container px-4 py-3 text-body-medium text-on-error-container"
      >
        <span className="flex items-center gap-2">
          <Icon name="error" />
          {PANO_OKUNAMADI}
        </span>
        <Button variant="tonal" icon="refresh" onClick={() => void sorgu.refetch()}>
          {YENIDEN_DENE}
        </Button>
      </div>
    );
  }

  const yanit = sorgu.data;
  const buyuk = yanit.gorunum === "ay";
  const isler = gorunenIsler(yanit);
  return (
    <Card elevation={1} className="p-5 sm:p-6">
      <section aria-labelledby="pano-isler-baslik">
        <div className="flex items-start gap-4">
          <span
            aria-hidden="true"
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg bg-primary-container text-primary"
          >
            <Icon name="checklist" />
          </span>
          <div className="min-w-0 flex-1">
            <h2
              id="pano-isler-baslik"
              className={`font-semibold text-on-surface ${buyuk ? "text-headline-small" : "text-title-medium"}`}
            >
              {buyuk ? AY_BASLIGI : HAFTA_BASLIGI}
            </h2>
            <p
              className={`mt-1 text-on-surface-variant ${buyuk ? "text-body-large" : "text-body-medium"}`}
            >
              {buyuk ? AY_ACIKLAMASI : HAFTA_ACIKLAMASI}
            </p>
          </div>
        </div>
        <Bilgiler bilgiler={yanit.bilgiler} buyuk={buyuk} />
        {isler.length === 0 ? (
          <p
            className={`mt-4 text-on-surface-variant ${buyuk ? "text-body-large" : "text-body-medium"}`}
          >
            {buyuk ? AY_BOS : HAFTA_BOS}
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-outline-variant/50">
            {isler.map((kalem, i) => (
              <IsSatiri key={`${kalem.kod}-${i}`} kalem={kalem} buyuk={buyuk} />
            ))}
          </ul>
        )}
        {yanit.tamamlanacaklar.length > 0 && (
          <section aria-labelledby="pano-tamamlanacaklar-baslik" className="mt-5">
            <h3
              id="pano-tamamlanacaklar-baslik"
              className={`font-semibold text-on-surface ${buyuk ? "text-title-large" : "text-title-small"}`}
            >
              {TAMAMLANACAKLAR_BASLIGI}
            </h3>
            <p className={`mt-0.5 text-on-surface-variant ${metaBoyutu(buyuk)}`}>
              {TAMAMLANACAKLAR_ACIKLAMASI}
            </p>
            <ul className="mt-2 divide-y divide-outline-variant/50">
              {yanit.tamamlanacaklar.map((kalem, i) => (
                <TamamlanacakSatiri key={`eksik-${i}`} kalem={kalem} buyuk={buyuk} />
              ))}
            </ul>
          </section>
        )}
      </section>
    </Card>
  );
}
