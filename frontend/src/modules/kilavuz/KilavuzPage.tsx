// Kullanım Kılavuzu — statik içerik, çevrimdışı. Kabuk bileşenleri `KilavuzKabugu`'ndadır, her
// bölüm `bolumler/` altında kendi dosyasındadır. Aile iskeletinin kütüphane kılavuzu F1a-2'de
// silindi; OAB'nin bölümleri her fazın özellikleriyle birlikte yazılır (tasarım §14).
//
// Bölüm eklemek: `bolumler/` altına dosyayı koy, `BOLUMLER`'e satırını ekle. Çapa, başlık, ikon
// ve sıra YALNIZ buradadır; bölüm dosyası bunları `BolumProps` olarak alır.

import Card from "../../ui/Card";
import { VELI_LISTESI_SEKMESI } from "../kisiler/metinler";
import { KULLANICILAR_BASLIGI } from "../kullanicilar/metinler";
import CikisVeKapanis from "./bolumler/CikisVeKapanis";
import DersYiliKapaliGunler from "./bolumler/DersYiliKapaliGunler";
import GenelBakis from "./bolumler/GenelBakis";
import Guncelleme from "./bolumler/Guncelleme";
import GuvenlikVeKisiselVeriler from "./bolumler/GuvenlikVeKisiselVeriler";
import HesaplarVeOturum from "./bolumler/HesaplarVeOturum";
import IlkKurulum from "./bolumler/IlkKurulum";
import Kisiler from "./bolumler/Kisiler";
import Kullanicilar from "./bolumler/Kullanicilar";
import OkulKarti from "./bolumler/OkulKarti";
import PrograminKonumu from "./bolumler/PrograminKonumu";
import VeliListesi from "./bolumler/VeliListesi";
import YedekVeGeriYukleme from "./bolumler/YedekVeGeriYukleme";
import { useCapayaKaydir } from "./KilavuzKabugu";

/**
 * Bölümler (çapa → başlık + ikon + içerik), sayfadaki sırasıyla: kullanıcının iş sırası.
 * Başlıklar Başlık Düzenindedir ve ekrandaki adı taşır ("okul kartı" ekranda geçmez: sözlük §1).
 */
const BOLUMLER = {
  "programin-konumu": { baslik: "Programın Konumu", ikon: "info", Bolum: PrograminKonumu },
  "ilk-kurulum": { baslik: "İlk Kurulum", ikon: "flag", Bolum: IlkKurulum },
  "genel-bakis": { baslik: "Genel Bakış", ikon: "space_dashboard", Bolum: GenelBakis },
  "hesaplar-ve-oturum": { baslik: "Hesaplar ve Oturum", ikon: "key", Bolum: HesaplarVeOturum },
  kullanicilar: { baslik: KULLANICILAR_BASLIGI, ikon: "manage_accounts", Bolum: Kullanicilar },
  "okul-karti": { baslik: "Okul Bilgileri", ikon: "apartment", Bolum: OkulKarti },
  "ders-yili-kapali-gunler": {
    baslik: "Ders Yılları ve Kapalı Günler",
    ikon: "calendar_month",
    Bolum: DersYiliKapaliGunler,
  },
  kisiler: { baslik: "Kişiler", ikon: "group", Bolum: Kisiler },
  "veli-listesi": { baslik: VELI_LISTESI_SEKMESI, ikon: "family_restroom", Bolum: VeliListesi },
  "yedek-ve-geri-yukleme": {
    baslik: "Yedek ve Geri Yükleme",
    ikon: "backup",
    Bolum: YedekVeGeriYukleme,
  },
  "guvenlik-ve-kvkk": {
    baslik: "Güvenlik ve Kişisel Veriler",
    ikon: "shield",
    Bolum: GuvenlikVeKisiselVeriler,
  },
  guncelleme: { baslik: "Güncelleme", ikon: "system_update", Bolum: Guncelleme },
  "cikis-ve-kapanis": {
    baslik: "Çıkış ve Kapanış",
    ikon: "power_settings_new",
    Bolum: CikisVeKapanis,
  },
} as const;

type BolumId = keyof typeof BOLUMLER;

/** "Bu kılavuzda" listesi — bölüm çapaları ve başlıklar tek kaynaktan (test de okur). */
export const KILAVUZ_BOLUMLERI: ReadonlyArray<{ id: BolumId; baslik: string }> = (
  Object.keys(BOLUMLER) as BolumId[]
).map((id) => ({ id, baslik: BOLUMLER[id].baslik }));

export default function KilavuzPage() {
  useCapayaKaydir();
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header>
        <p className="text-label-medium font-semibold tracking-wide text-primary">OAB Defteri</p>
        <h1 className="mt-1 text-headline-medium font-semibold tracking-tight text-on-surface">
          Kullanım Kılavuzu
        </h1>
        <p className="mt-2 text-body-medium text-on-surface-variant">
          OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten çevrimdışı bir
          masaüstü programıdır; veriler yalnız bu bilgisayarda durur. Kılavuz, programda bugün
          bulunan ekranları anlatır.
        </p>
      </header>

      <Card className="p-5 sm:p-6">
        <nav aria-label="Kılavuz bölümleri">
          <p className="text-label-large font-semibold text-on-surface">Bu kılavuzda</p>
          <ol className="mt-2 grid list-decimal gap-x-8 gap-y-1 pl-5 text-body-medium sm:grid-cols-2">
            {KILAVUZ_BOLUMLERI.map((b) => (
              <li key={b.id}>
                <a
                  href={`#${b.id}`}
                  className="font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  {b.baslik}
                </a>
              </li>
            ))}
          </ol>
        </nav>
      </Card>

      {KILAVUZ_BOLUMLERI.map(({ id }) => {
        const { Bolum, baslik, ikon } = BOLUMLER[id];
        return <Bolum key={id} id={id} baslik={baslik} ikon={ikon} />;
      })}
    </div>
  );
}
