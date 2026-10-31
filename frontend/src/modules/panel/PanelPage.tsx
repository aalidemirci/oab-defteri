// Genel Bakış (hub). Sayfanın TEK adı "Genel Bakış"tır (gezinme + üst çubuk + h1);
// kart başlıkları gittikleri sayfanın h1'iyle aynıdır.
//
// Kartlar: "Başlangıç Yol Haritası" (kurulumdan sonra sıradaki işler; bütün
// maddeler tamamlanınca gizlenebilir), "Son Oturumu Kontrol Edin" (beklenmedik
// kapanıştan sonra — T15, tasarım §13 D4), "Ayrılış Havuzu" (havuz boş değilse
// "N kişi ayrılış kararı bekliyor"), dış yedek hatırlatması ve gezinme kartları.
// Aile iskeletinin kütüphane kartları (katalog şablonu, dolaşım, sayım, raporlar,
// saklama, yıl akışları) F1a-2'de söküldü; OAB pano kartları F1c'de gelir (§7.10).
//
// Durum `GET /setup/status/`'tan tek kez okunur (kişisel veri yok). Okunamazsa
// yol haritası gösterilmez; sayfanın geri kalanı çalışır.

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../lib/api";
import HubFeatureCard from "../../ui/HubFeatureCard";
import { useSnackbar } from "../../ui/SnackbarProvider";
import DisYedekKarti from "../guvenlik/DisYedekKarti";
import { okulApi } from "../okul/api";
import type { RoadmapManualItem, SetupStatus } from "../okul/api";
import AyrilisHavuzuKarti from "./AyrilisHavuzuKarti";
import BaslangicYolHaritasi from "./BaslangicYolHaritasi";
import SonOturumKarti from "./SonOturumKarti";

export default function PanelPage() {
  const snackbar = useSnackbar();
  const [durum, setDurum] = useState<SetupStatus | null>(null);

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
          Okul-aile birliğinin işlerini yürüttüğü yerel araç. Veriler yalnız bu bilgisayarda
          durur.
        </p>
      </header>
      {durum && !durum.roadmap.hidden && (
        <BaslangicYolHaritasi
          durum={durum}
          onIsaretle={(madde, yapildi) => void isaretle(madde, yapildi)}
          onGizle={() => void gizle()}
        />
      )}
      {/* T15 (§13 D4): beklenmedik kapanıştan sonra "Son Oturumu Kontrol Edin". */}
      <SonOturumKarti />
      {/* Havuz boşsa görünmez; yalnız sayı okunur. */}
      <AyrilisHavuzuKarti />
      {/* Dış yedek hatırlatması — son şifreli yedek indirmesinden (yoksa parola
          kurulumundan) süre dolunca; yalnız tarih ve gün sayısı. */}
      <DisYedekKarti />
      <div className="grid gap-4 sm:grid-cols-2">
        <HubFeatureCard
          to="/kisiler"
          icon="group"
          title="Kişiler"
          description="Öğretmen ve diğer personel sicili; e-Okul listelerinden içe aktarma."
        />
        <HubFeatureCard
          to="/ayarlar"
          icon="settings"
          title="Ayarlar"
          description="Ders yılı, şubeler, okul bilgileri, güvenlik, yedek ve güncelleme."
        />
      </div>
    </div>
  );
}
