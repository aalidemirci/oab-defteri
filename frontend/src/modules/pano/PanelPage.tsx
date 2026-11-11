// Genel Bakış (hub). Sayfanın TEK adı "Genel Bakış"tır (gezinme + üst çubuk + h1);
// kart başlıkları gittikleri sayfanın h1'iyle aynıdır.
//
// Kartlar: "Başlangıç Yol Haritası" (kurulumdan sonra sıradaki işler; bütün
// maddeler tamamlanınca gizlenebilir), "Son Oturumu Kontrol Edin" (beklenmedik
// kapanıştan sonra — T15, tasarım §13 D4), denetim izinin uyarı kartları ("Denetim İzi
// Bütünlüğü", "Değiştirilmiş Hesap Kaydı", "Yedekten Geri Yükleme Yapıldı", "Hesaplar ve
// Güvenlik Dosyası" — tasarım §4.6.3, §4.6.1; `modules/butunluk`), "Okunamayan Kayıt
// Alanları" (çözülemeyen şifreli alan varsa yalnız sayı — tasarım §13 D48), "Ayrılış
// Havuzu" (havuz boş değilse "N kişi ayrılış kararı bekliyor"), dış yedek hatırlatması,
// "Son Girişler" (oturumdaki hesabın girişleri ve denetim izinin son kaydı — kâğıt çapası)
// ve gezinme kartları. Denetim izi kartları bütünlük uçlarının tek bileşik okumasından
// beslenir (`useButunlukDurumu`): hangi ucun çağrılacağını oturum özetinin yetenekleri söyler
// (`useYetenekler`; denetim kartları ve "Eksik Ekler" program yöneticisi ve Denetleme Kurulunda,
// iki depo kartı yalnız program yöneticisinde; "Son Girişler" her rolde). Okuma beklenmedik biçimde düşerse
// kartların yerine "Bütünlük Durumu Okunamadı" uyarısı çıkar (bir uyarı sessizce kaybolmasın),
// sayfanın geri kalanı çalışır; kilitliyken (423) hiçbiri çizilmez. Oturum özeti (yetenekler)
// okunamazsa da aynı uyarı çıkar: yalnız her role açık kendi kartları okunur, denetim ve iki
// depo uçları yetenek bilinmeden çağrılmaz; özet yüklenirken uyarı yoktur. Backend tek kartı
// okuyamazsa adını `okunamayan`'a yazar; "Son Girişler" kartı okunamayan bölümünü "henüz giriş
// yok" diye değil "okunamadı" diye yazar.
// Öteki kartların rol süzmesi (plan F1b-2 "Ön yüz"; kaynak `oturum/yetki`): "Başlangıç Yol
// Haritası" yalnız `yol_haritasi`'nda (maddeleri ve işaretleri program yöneticisinin kurulum
// işleridir; kartın her denetimi bir yazmadır); "Son Oturumu Kontrol Edin" her rolde, "Kontrol
// ettim" yalnız `son_oturum_onay`'da; "Ayrılış Havuzu" yalnız `ayrilis_havuzu`'nda, "Şifreli
// Yedeği USB Belleğe Alın" yalnız `guvenlik`'te (uçları o rollere kapalıdır, çağrılmaz);
// "Okunamayan Kayıt Alanları" ve gezinme kartları her rolde (açıklamaları rolün göreceğini
// söyler). Geri yükleme kartının "Gördüm"ü yalnız `geri_yukleme_gordum`'da (Denetleme Kurulu;
// bir üye yeter, kart herkes için kalkar); iki depo kartının Kullanıcılar bağlantısı yalnız
// `kullanicilar`'da.
// Aile iskeletinin kütüphane kartları (katalog şablonu, dolaşım, sayım, raporlar,
// saklama, yıl akışları) F1a-2'de söküldü. OAB'nin pano kalemleri (§7.10; F1c 12. adım "pano kabuğu")
// başlığın hemen altındaki listededir (`PanoKalemleri`): rolün "Bu Hafta Yapılacaklar"ı ya da veli
// rollerinde "Bu Ay Sizden Beklenenler"i ve "Tamamlanacaklar"; her rolde çizilir, rol süzmesi
// sunucudadır. Klasörün adı `pano`dur (plan F1c kararları); görünen ad yalnız "Genel Bakış"tır.
//
// Durum `GET /setup/status/`'tan tek kez okunur (kişisel veri yok). Okunamazsa
// yol haritası gösterilmez; sayfanın geri kalanı çalışır.

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../lib/api";
import HubFeatureCard from "../../ui/HubFeatureCard";
import { useSnackbar } from "../../ui/SnackbarProvider";
import ButunlukKartlari, { OkunamayanButunlukKarti } from "../butunluk/ButunlukKartlari";
import SonGirislerKarti from "../butunluk/SonGirislerKarti";
import { butunlukYetkisi } from "../butunluk/api";
import useButunlukDurumu from "../butunluk/useButunlukDurumu";
import DisYedekKarti from "../guvenlik/DisYedekKarti";
import { okulApi } from "../okul/api";
import type { RoadmapManualItem, SetupStatus } from "../okul/api";
import { useYetenekler } from "../oturum/useOturum";
import { useYetki } from "../oturum/yetki";
import AyrilisHavuzuKarti from "./AyrilisHavuzuKarti";
import BaslangicYolHaritasi from "./BaslangicYolHaritasi";
import OkunamayanAlanlarKarti from "./OkunamayanAlanlarKarti";
import PanoKalemleri from "./PanoKalemleri";
import SonOturumKarti from "./SonOturumKarti";

/** Gezinme kartlarının açıklamaları: rolün o sayfada göreceğini söyler (sözlük §4.5). */
export const KISILER_KARTI_ACIKLAMASI =
  "Öğretmen ve diğer personel sicili; e-Okul listelerinden içe aktarma.";
export const KISILER_KARTI_SALT_OKUR_ACIKLAMASI = "Öğretmen ve diğer personel sicili.";
export const AYARLAR_KARTI_ACIKLAMASI = "Ders yılı, okul bilgileri, güvenlik, yedek ve güncelleme.";
export const AYARLAR_KARTI_SALT_OKUR_ACIKLAMASI =
  "Ders yılı, okul bilgileri, parolanız ve boşta kilit süresi.";

export default function PanelPage() {
  const snackbar = useSnackbar();
  const yetki = useYetki();
  const [durum, setDurum] = useState<SetupStatus | null>(null);
  const { yetenekler, hata: yetenekHatasi } = useYetenekler();
  const butunluk = useButunlukDurumu(
    yetenekler === null ? null : butunlukYetkisi(yetenekler),
    yetenekHatasi,
  );

  useEffect(() => {
    let iptal = false;
    okulApi
      .getSetupStatus()
      .then((s) => {
        if (!iptal) setDurum(s);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  const isaretle = useCallback(
    async (madde: RoadmapManualItem, yapildi: boolean) => {
      try {
        const roadmap = await okulApi.markRoadmapItem(madde, yapildi);
        setDurum((d) => (d ? { ...d, roadmap } : d));
      } catch (e) {
        snackbar.error(e instanceof ApiError ? e.message : "İşaret kaydedilemedi.");
      }
    },
    [snackbar],
  );

  const gizle = useCallback(async () => {
    try {
      const roadmap = await okulApi.setRoadmapHidden(true);
      setDurum((d) => (d ? { ...d, roadmap } : d));
      snackbar.success("Başlangıç yol haritası gizlendi.");
    } catch (e) {
      snackbar.error(e instanceof ApiError ? e.message : "Kart gizlenemedi.");
    }
  }, [snackbar]);

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header>
        <h1 className="text-headline-medium font-semibold tracking-tight text-on-surface">
          Genel Bakış
        </h1>
        <p className="mt-2 text-body-medium text-on-surface-variant">
          Okul-aile birliğinin işlerini yürüttüğü yerel araç. Veriler yalnız bu bilgisayarda durur.
        </p>
      </header>
      {/* Pano kalemleri (§7.10): rolün listesi; kişisiz, sunucuda her okumada hesaplanır. */}
      <PanoKalemleri />
      {yetki.acik("yol_haritasi") && durum && !durum.roadmap.hidden && (
        <BaslangicYolHaritasi
          durum={durum}
          onIsaretle={(madde, yapildi) => void isaretle(madde, yapildi)}
          onGizle={() => void gizle()}
        />
      )}
      {/* T15 (§13 D4): beklenmedik kapanıştan sonra "Son Oturumu Kontrol Edin". */}
      <SonOturumKarti kontrolEdebilir={yetki.acik("son_oturum_onay")} />
      {/* Denetim izinin uyarı kartları (tasarım §4.6.3, §4.6.1): söyleyecek bir şeyi
          olmayan kart çizilmez; kişisiz (hesap rol etiketi ve tanıtıcıyla). */}
      {/* Kartlar okunamayanı zaten söylüyorsa (`okunamayan` dolu) ikinci kart çizilmez. */}
      {butunluk.okunamadi && !butunluk.durum?.okunamayan.length && <OkunamayanButunlukKarti />}
      {butunluk.durum && (
        <ButunlukKartlari
          durum={butunluk.durum}
          onIkiDepo={butunluk.ikiDepoyuYaz}
          gordum={
            yetki.acik("geri_yukleme_gordum")
              ? { onDenetim: butunluk.denetimiYaz, onYenile: butunluk.yenile }
              : null
          }
          kullanicilarAcik={yetki.acik("kullanicilar")}
        />
      )}
      {/* D48: çözülemeyen şifreli alan yoksa görünmez; kişisiz, yalnız sayı. */}
      <OkunamayanAlanlarKarti />
      {/* Havuz boşsa görünmez; yalnız sayı okunur. Ucu yalnız `ayrilis_havuzu`'nda açık. */}
      {yetki.acik("ayrilis_havuzu") && <AyrilisHavuzuKarti />}
      {/* Dış yedek hatırlatması — son şifreli yedek kaydından (yoksa ilk hesabın
          kurulumundan) süre dolunca; yalnız tarih ve gün sayısı. Ucu yalnız `guvenlik`'te. */}
      {yetki.acik("guvenlik") && <DisYedekKarti />}
      {/* Oturumdaki hesabın son girişleri ve denetim izinin son kaydı (kâğıt çapası). */}
      {butunluk.durum && (
        <SonGirislerKarti
          girisler={butunluk.durum.son_girisler}
          capa={butunluk.durum.kagit_capasi}
          girislerOkunamadi={butunluk.durum.okunamayan.includes("son_girisler")}
          capaOkunamadi={butunluk.durum.okunamayan.includes("kagit_capasi")}
        />
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <HubFeatureCard
          to="/kisiler"
          icon="group"
          title="Kişiler"
          description={
            yetki.acik("eokul_aktarimi")
              ? KISILER_KARTI_ACIKLAMASI
              : KISILER_KARTI_SALT_OKUR_ACIKLAMASI
          }
        />
        <HubFeatureCard
          to="/ayarlar"
          icon="settings"
          title="Ayarlar"
          description={
            yetki.acik("guvenlik") && yetki.acik("guncelleme")
              ? AYARLAR_KARTI_ACIKLAMASI
              : AYARLAR_KARTI_SALT_OKUR_ACIKLAMASI
          }
        />
      </div>
    </div>
  );
}
