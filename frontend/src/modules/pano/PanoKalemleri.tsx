// Genel Bakış'ın pano kalemleri (tasarım §7.10 "Pano ve takvim"; plan F1c 12. adım "pano kabuğu").
//
// Açılış ekranının listesi: rolün "Bu Hafta Yapılacaklar"ı — son günü yedi gün içinde olan ya da
// geçmiş kalemler önde (sunucu son güne göre sıralar), süresi olmayan işler ardından; son günü
// pencerenin ötesindeki kalem listeye girmez (takvim görünümü ve E14 Genel Bakış → Yıllık İş Takvimi
// sekmesindedir; F2 11b). Veli rollerinde (sunucunun `gorunum: "ay"`ı; ön yüz rol adıyla dallanmaz) varsayılan görünüm "Bu Ay
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
// F2 (12. adım): genel kurul süreleri, müdürün bekleyen yazısı, ibra edilmedi bildirimi, TEFBİS
// girişleri ve dönem onayı genel kurulun ekranına (`?kurul=`), veri sorumlusunun tamamlanacağı Ayarlar →
// Okul Bilgileri'ne götürür. İbra edilmedi bildirimi ve TEFBİS kalemleri süresizdir (mevzuatta süre yok);
// satırın işini yapan rol (yetenek `takvim_isareti`: program yöneticisi ve sekreter; sekreter yalnız ibra
// bildirimini görür, servis satıra göre yeniden daraltır) kalemin yanındaki "Yapıldı" ile işin yapıldığı
// günü girer, kalem düşer (tasarım §7.10 "kalemin kapanması"). Satırın kendi döneminin kural kopyası
// doğrulanamıyorsa (D7) dönem salt okurdur: düğme çizilmez (sunucu da 409 verir). Karar bant yerine
// kalemin `ek.salt_okur` bayrağındadır: takvim kalemi kapanıştaki dönemden de gelir, bant yalnız açık
// dönemi söyler; bayrağı sunucu, ucun 409'unu veren işlevle satırın dönemine göre koyar.
// Kilitliyken (423) ya da anahtar düşmüşken (409) hata söylenmez: kilit ekranı gelir.

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { todayIso } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import Skeleton from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { KURAL_KOPYASI_BOZUK } from "../birlik-donemi/metinler";
import { okunamadiSayilir } from "../butunluk/useButunlukDurumu";
import { DUGME_BIRLIK_DONEMINE_GIT } from "../organlar/metinler";
import { useYetki } from "../oturum/yetki";
import { Dayanak } from "../uyum/UyariGerekce";
import { panelApi } from "./api";
import type { PanoKalemi, PanoYaniti } from "./api";
import {
  ALAN_YAPILDIGI_GUN,
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
  YAPILDIGI_GUN_GEREKLI,
  YAPILDI_ACIKLAMASI,
  YAPILDI_DUGMESI,
  YAPILDI_KAYDEDILDI,
  YAPILDI_KAYDEDILEMEDI,
  YAPILDI_KAYDEDILIYOR,
  YAPILDI_KAYDET,
  YAPILDI_PENCERESI_BASLIGI,
  YAPILDI_VAZGEC,
  YENIDEN_DENE,
  ekranAdi,
  kalemAciklamasi,
  kalemBasligi,
  tamamlanacakMetni,
  vadeCumlesi,
  yapildiDugmesiAdi,
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

/** Kalemin götürdüğü adres: rota, sekme (`?tab=`) ve genel kurul kalemlerinde ayrıntı (`?kurul=`). */
export function hedef(kalem: Pick<PanoKalemi, "rota" | "sekme" | "ek">): string {
  const sorgu = new URLSearchParams();
  if (kalem.sekme) sorgu.set("tab", kalem.sekme);
  if (kalem.ek.kurul !== undefined && kalem.ek.kurul !== "")
    sorgu.set("kurul", String(kalem.ek.kurul));
  const metin = sorgu.toString();
  return metin ? `${kalem.rota}?${metin}` : kalem.rota;
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

/** Takvim satırının kalemi (ibra edilmedi bildirimi, TEFBİS): "Yapıldı" işaretinin satırı (`ek.satir`). */
const TAKVIM_KODLARI = new Set(["IBRA_BILDIRIMI", "TEFBIS_GIRISI"]);

/** Kalemin işaretlenebilir takvim satırı (yalnız takvim kalemlerinde; satırın dönemi salt okursa —
 * `ek.salt_okur`, D7 — ya da satır yoksa null). */
export function takvimSatiri(kalem: Pick<PanoKalemi, "kod" | "ek">): number | null {
  if (!TAKVIM_KODLARI.has(kalem.kod) || kalem.ek.salt_okur === true) return null;
  const satir = Number(kalem.ek.satir);
  return Number.isInteger(satir) && satir > 0 ? satir : null;
}

/** İşin yapıldığı günün penceresi (tasarım §7.10 "kalemin kapanması"): gün bugünden sonra olamaz
 * (sunucu da reddeder); kaydedilince pano yeniden okunur ve kalem düşer. */
function YapildiPenceresi({
  satir,
  baslik,
  onKapat,
}: {
  satir: number;
  baslik: string;
  onKapat: () => void;
}) {
  const snackbar = useSnackbar();
  const queryClient = useQueryClient();
  const [gun, setGun] = useState(todayIso);
  const [alanHatasi, setAlanHatasi] = useState("");
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [busy, setBusy] = useState(false);

  const kaydet = async () => {
    if (!gun) {
      setAlanHatasi(YAPILDIGI_GUN_GEREKLI);
      return;
    }
    setAlanHatasi("");
    setBusy(true);
    setHata(null);
    try {
      await panelApi.takvimYapildi(satir, gun);
      snackbar.success(YAPILDI_KAYDEDILDI);
      await queryClient.invalidateQueries({ queryKey: [PANO_SORGU_ANAHTARI] });
      onKapat();
    } catch (e) {
      setHata(hataOku(e, YAPILDI_KAYDEDILEMEDI));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onKapat}
      title={YAPILDI_PENCERESI_BASLIGI}
      actions={
        <>
          <Button variant="text" onClick={onKapat} disabled={busy}>
            {YAPILDI_VAZGEC}
          </Button>
          <Button icon="check" onClick={() => void kaydet()} disabled={busy}>
            {busy ? YAPILDI_KAYDEDILIYOR : YAPILDI_KAYDET}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-body-large font-medium text-on-surface">{baslik}</p>
        <p className="text-body-medium text-on-surface-variant">{YAPILDI_ACIKLAMASI}</p>
        <TextField
          label={ALAN_YAPILDIGI_GUN}
          type="date"
          required
          max={todayIso()}
          value={gun}
          onChange={(e) => setGun(e.target.value)}
          error={alanHatasi || undefined}
        />
        {hata && <ErrorBand hata={hata} />}
      </div>
    </Dialog>
  );
}

function IsSatiri({
  kalem,
  buyuk,
  isaretlenebilir,
}: {
  kalem: PanoKalemi;
  buyuk: boolean;
  isaretlenebilir: boolean;
}) {
  const vade = vadeCumlesi(kalem);
  const meta = metaBoyutu(buyuk);
  const satir = isaretlenebilir ? takvimSatiri(kalem) : null;
  const [pencere, setPencere] = useState(false);
  return (
    <li className="flex items-start gap-2">
      <Link
        to={hedef(kalem)}
        className="group flex min-w-0 flex-1 items-start gap-3 rounded-shape-md px-2 py-3 hover:bg-on-surface/8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
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
      {satir !== null && (
        <div className="shrink-0 py-2">
          <Button
            variant="outlined"
            icon="check"
            aria-label={yapildiDugmesiAdi(kalemBasligi(kalem))}
            onClick={() => setPencere(true)}
          >
            {YAPILDI_DUGMESI}
          </Button>
        </div>
      )}
      {pencere && satir !== null && (
        <YapildiPenceresi
          satir={satir}
          baslik={kalemBasligi(kalem)}
          onKapat={() => setPencere(false)}
        />
      )}
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
            {tamamlanacakMetni(kalem)}
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
  const isaretlenebilir = useYetki().acik("takvim_isareti");
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
              <IsSatiri
                key={`${kalem.kod}-${i}`}
                kalem={kalem}
                buyuk={buyuk}
                isaretlenebilir={isaretlenebilir}
              />
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
