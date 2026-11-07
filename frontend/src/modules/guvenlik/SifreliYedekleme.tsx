// Şifreli Yedek kartı (Ayarlar → Güvenlik; tasarım §4.4.7; plan F1b-3 kullanıcı kararı 04.11.2026
// "Şifreli yedeği program kaydeder"). Metin kullanıcı dilindedir: şifreleme algoritmalarının adı
// (teknik ayrıntı) burada geçmez, yalnız Hakkında sayfası anar (docs/sozluk.md §1).
//
// AKIŞ: adı sunucu önerir (`GET backups/encrypted/`), yeri pencerenin kaydetme köprüsü sorar,
// seçilen yol isteğin içinde gider (`POST backups/encrypted/`; masaüstü sunucuyu doğrudan çağırmaz,
// tasarım §4.1). Sunucu yedeği seçilen yere yazar, yeniden açıp denetler, sonra hatırlatma tarihi
// değişir. İptalde köprü "" döner: istek gitmez, hiçbir şey yazılmaz. Köprü yoksa (geliştirme kipi)
// düğme kapalıdır; bellek içi indirme yolu yoktur.
//
// BEKLEME: iş dakikalar sürebilir, istek zaman aşımısız beklenir; düğme iş boyunca kapalıdır,
// ikinci istek gitmez. Aşama, sonuç ve hata modül belleğindedir (`yedekIsleri`): kullanıcı beklerken
// başka ekrana geçip dönse de kart süren işi ve sonucunu gösterir. Başarı snackbar'la da söylenir.
// Hata kartta kalıcı satırdır, kullanıcı ekran başında beklemez; kart çizili değilse hatayı
// snackbar söyler. Kaydetme penceresindeki seçim DOM olayı üretmez, etkileşim elle kaydedilir.
//
// SON DENEME (kullanıcı kararı 06.11.2026 "Son şifreli yedek denemesi saklanır"): uzun iş biterken
// ertelenen kilit pencereyi yeniden yükler, modül belleği gider. Bellek boşsa, iş sürmüyorsa ve sunucu
// son denemeyi veriyorsa (`GET backups/external/`, `son_deneme`) kart onu gösterir; bellekte sonuç ya
// da hata varken aynı bilgi iki kez çizilmez. Kayıt kişisizdir: dosyanın adı ve yolu yoktur. Biçimi
// tutmayan alan tek başına null gelebilir, o parça yazılmaz. Kutu sayfa açılırken vardır, yeni bir
// olay değildir: `status` değildir, ekran okuyucuya duyurulmaz.
//
// DÜRÜST DİL: program dosyanın USB bellekte olduğunu bilemez; ekran seçilen yere yazıldığını ve
// denetlendiğini söyler. Yanıttaki `ad` kullanıcı serbest ad seçtiyse diskteki ad değildir, ekran
// onu dosyanın adı diye göstermez. Eksik ve bozuk ek ayrı sayılmaz (plan "Yedek alınırken bozuk olan
// ek eksik sayılır").

import { useCallback, useEffect, useState } from "react";

import { etkilesimKaydet } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { oturumHataMetni } from "../oturum/hatalar";
import { guvenlikApi } from "./api";
import type { DisYedekDurumu, SonDeneme } from "./api";
import { disYedekCumlesi, disYedekHatirlatmaCumlesi } from "./DisYedekKarti";
import { useKaydetmeKoprusu } from "./kaydetmeKoprusu";
import {
  SIFRELI_YEDEK_ALINAMADI,
  SIFRELI_YEDEK_DUGMESI,
  SIFRELI_YEDEK_HESAP_YOK,
  SIFRELI_YEDEK_KARTI_BASLIGI,
  SIFRELI_YEDEK_KAYDEDILEMEDI,
  SIFRELI_YEDEK_KAYDEDILIYOR,
  SIFRELI_YEDEK_METNI,
  SIFRELI_YEDEK_PENCERE_YOK,
  SIFRELI_YEDEK_SON_DENEME,
  SIFRELI_YEDEK_SURUYOR,
  SIFRELI_YEDEK_YAZILDI,
  SIFRELI_YEDEK_YER_METNI,
  SIFRELI_YEDEK_YER_SECILIYOR,
} from "./metinler";
import { eksikEkCumlesi, yedekBoyuSatiri } from "./yedekBilgisi";
import { sifreliYedekIsiniYaz, sifreliYedekKartiCizili, useSifreliYedekIsi } from "./yedekIsleri";
import type { SifreliYedekAsamasi } from "./yedekIsleri";

/** Hatırlatma süresi seçenekleri (gün; sunucu 7-90 aralığını ayrıca denetler). */
const SURE_SECENEKLERI = [7, 14, 30, 60, 90].map((gun) => ({
  value: String(gun),
  label: `${gun} gün`,
}));

const DUGME_ETIKETI: Record<SifreliYedekAsamasi, string> = {
  bos: SIFRELI_YEDEK_DUGMESI,
  yer: SIFRELI_YEDEK_YER_SECILIYOR,
  yazim: SIFRELI_YEDEK_KAYDEDILIYOR,
};

/** Son denemenin kutusu (dosya başı "SON DENEME"). */
function SonDenemeKutusu({ deneme }: { deneme: SonDeneme }) {
  const basarili = deneme.sonuc === "basarili";
  const boy = yedekBoyuSatiri(deneme.boyut, deneme.ek_sayisi);
  const eksik = deneme.eksik ?? 0;
  return (
    <div
      className={`mt-3 rounded-shape-sm px-3 py-2 text-body-small ${
        basarili
          ? "bg-secondary-container text-on-secondary-container"
          : "bg-error-container text-on-error-container"
      }`}
    >
      <p>
        {SIFRELI_YEDEK_SON_DENEME} {formatDateTime(deneme.an)}
      </p>
      <p>{basarili ? SIFRELI_YEDEK_YAZILDI : SIFRELI_YEDEK_ALINAMADI}</p>
      {basarili && boy && <p>{boy}</p>}
      {basarili && eksik > 0 && <p>{eksikEkCumlesi(eksik)}</p>}
      {!basarili && deneme.ileti && <p>{deneme.ileti}</p>}
    </div>
  );
}

export default function SifreliYedekleme({ parolaKurulu }: { parolaKurulu: boolean }) {
  const snackbar = useSnackbar();
  const kopruHazir = useKaydetmeKoprusu();
  const { asama, sonuc, hata } = useSifreliYedekIsi();
  // Dış yedek hatırlatması: son kaydın tarihi (sunucu, kayıtla yazar) + süre.
  const [disYedek, setDisYedek] = useState<DisYedekDurumu | null>(null);
  const sonDeneme = asama === "bos" && !sonuc && !hata ? (disYedek?.son_deneme ?? null) : null;

  const disYedegiOku = useCallback(() => {
    guvenlikApi
      .disYedek()
      .then(setDisYedek)
      .catch(() => undefined);
  }, []);

  // Tarih kayıtla değişir: `sonuc` kartın kendi isteğinden de, sökülmüş kartın isteğinden de gelir.
  useEffect(() => {
    if (parolaKurulu) disYedegiOku();
  }, [parolaKurulu, disYedegiOku, sonuc]);

  async function kaydet() {
    const kopru = window.pywebview?.api;
    if (!kopru?.kaydetme_yeri_sor) return;
    sifreliYedekIsiniYaz({ asama: "yer" });
    try {
      const { onerilen_ad } = await guvenlikApi.sifreliYedekAdi();
      const hedef = await kopru.kaydetme_yeri_sor(onerilen_ad);
      if (!hedef) return;
      // Yer seçimi gerçek kullanıcı eylemidir; pencerede geçen süre boşta sayılmasın (dosya başı).
      etkilesimKaydet();
      sifreliYedekIsiniYaz({ asama: "yazim", sonuc: null, hata: null });
      const yeni = await guvenlikApi.sifreliYedegiKaydet(hedef);
      sifreliYedekIsiniYaz({ sonuc: yeni });
      snackbar.success(
        yeni.eksik > 0
          ? `${SIFRELI_YEDEK_YAZILDI} ${eksikEkCumlesi(yeni.eksik)}`
          : SIFRELI_YEDEK_YAZILDI,
      );
    } catch (error) {
      const ileti = oturumHataMetni(error, SIFRELI_YEDEK_KAYDEDILEMEDI);
      sifreliYedekIsiniYaz({ sonuc: null, hata: ileti });
      if (!sifreliYedekKartiCizili()) snackbar.error(ileti);
    } finally {
      sifreliYedekIsiniYaz({ asama: "bos" });
    }
  }

  const hatirlatma = disYedek ? disYedekHatirlatmaCumlesi(disYedek) : null;

  async function sureDegisti(deger: string) {
    try {
      setDisYedek(await guvenlikApi.disYedekSuresi(Number(deger)));
      snackbar.success("Hatırlatma süresi kaydedildi.");
    } catch (error) {
      snackbar.error(oturumHataMetni(error, "Hatırlatma süresi kaydedilemedi."));
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-start gap-3">
        <Icon name="backup" className="mt-0.5 text-primary" />
        <div className="min-w-0 flex-1">
          <h2 className="text-title-large text-on-surface">{SIFRELI_YEDEK_KARTI_BASLIGI}</h2>
          <p className="mt-2 text-body-medium text-on-surface-variant">{SIFRELI_YEDEK_METNI}</p>
          <p className="mt-2 text-body-small text-on-surface-variant">{SIFRELI_YEDEK_YER_METNI}</p>
          {!parolaKurulu && (
            <p className="mt-3 rounded-shape-md bg-error-container p-3 text-body-small text-on-error-container">
              {SIFRELI_YEDEK_HESAP_YOK}
            </p>
          )}
          {parolaKurulu && !kopruHazir && (
            <p className="mt-3 text-body-small text-on-surface-variant">
              {SIFRELI_YEDEK_PENCERE_YOK}
            </p>
          )}
          <div className="mt-5">
            <Button
              icon="save"
              onClick={() => void kaydet()}
              disabled={asama !== "bos" || !parolaKurulu || !kopruHazir}
            >
              {DUGME_ETIKETI[asama]}
            </Button>
          </div>
          {asama === "yazim" && (
            <p role="status" className="mt-3 text-body-small text-on-surface-variant">
              {SIFRELI_YEDEK_SURUYOR}
            </p>
          )}
          {hata && (
            <p role="alert" className="mt-3 text-body-small text-error">
              {hata}
            </p>
          )}
          {sonuc && (
            <div
              role="status"
              className="mt-3 rounded-shape-sm bg-secondary-container px-3 py-2 text-body-small text-on-secondary-container"
            >
              <p>{SIFRELI_YEDEK_YAZILDI}</p>
              <p>{yedekBoyuSatiri(sonuc.boyut, sonuc.ek_sayisi)}</p>
              {sonuc.eksik > 0 && <p>{eksikEkCumlesi(sonuc.eksik)}</p>}
            </div>
          )}
          {sonDeneme && <SonDenemeKutusu deneme={sonDeneme} />}
          {parolaKurulu && disYedek && (
            <div className="mt-5 flex flex-wrap items-end gap-4">
              <div className="min-w-48 flex-1 space-y-1">
                <p className="text-body-medium text-on-surface">{disYedekCumlesi(disYedek)}</p>
                {hatirlatma &&
                  (disYedek.remind ? (
                    <p
                      role="status"
                      className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-3 py-2 text-body-small text-on-tertiary-container"
                    >
                      <Icon name="notification_important" size="sm" />
                      <span>{hatirlatma}</span>
                    </p>
                  ) : (
                    <p className="text-body-small text-on-surface-variant">{hatirlatma}</p>
                  ))}
              </div>
              <Select
                label="Hatırlatma süresi"
                className="w-40"
                options={SURE_SECENEKLERI}
                value={String(disYedek.reminder_days)}
                onChange={(e) => void sureDegisti(e.target.value)}
                helperText="Genel Bakış bu süre dolunca hatırlatır."
              />
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
