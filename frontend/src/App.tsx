// OAB Defteri — kök route tanımı. Route ağacı fazlarla büyür (tasarım §14):
// aile iskeletinden gelen kabuk kurulum, kişiler, ayarlar, kılavuz ve hakkında
// ekranlarını taşır; OAB ekranları (birlik dönemi, organlar, pano…) F1c'den
// itibaren eklenir. Aile iskeletinin kütüphane ekranları F1a-2'de söküldü.
// Kilit ekranı (GuvenlikKapisi) kurulum kapısından ÖNCE gelir — hesap kuruluysa
// hiçbir veri ekranı (sihirbaz dahil) açılmadan kilit kişinin kendi hesabıyla
// açılmalıdır. Aile iskeletinin kip kapısı (görevli kipi) yoktur (tasarım TK14):
// oturum açıkken rotalar, kapalıyken kilit ekranı.
//
// Rol süzmesi (plan F1b-2 "Ön yüz"; `modules/oturum/yetki`): `YetkiSaglayici` kabuğun DIŞINDA
// durur — gezinme, güncelleme bandı ve sayfalar aynı yetenekleri okur. Matriste "—" olan ekran
// gezinmede yoktur ve rotası `RolKapisi` ile bağlanır ("Bu ekran hesabınızın rolüne açık
// değil."); "O" olan ekran açılır, yazma denetimlerini kendisi gizler. Bugün Genel Bakış, Birlik
// Dönemi ve Geçiş Kurulumu (F1c 11. adım), Kişiler, Ayarlar, Kılavuz ve Hakkında her role en az
// okumaya açıktır (sözlük §4). Organlar ve Temsilciler ekranları F1c 11. adımın ikinci
// parçasındadır. Kurulum Sihirbazı'nın her denetimi bir yazmadır: rotası `kurulum_tamamlama`'ya
// bağlıdır ve öteki rollerde kendi iletisini verir (kullanıcı kararı 04.11.2026: matristeki "O"ya istisna; kurulum durumunda süzme yoktur). Kullanıcılar (`/kullanicilar`)
// matriste yalnız program yöneticisinde Y, öteki rollerde "—"dir: rotası `kullanicilar`
// yeteneğine bağlıdır. Erişim Günlüğü (`/erisim-gunlugu`) matriste program yöneticisi ve Denetleme
// Kurulunda O, öteki rollerde "—"dir: rotası `erisim_gunlugu` yeteneğine bağlıdır.

import { Route, Routes } from "react-router-dom";

import AppShell from "./AppShell";
import KurulumKapisi from "./KurulumKapisi";
import AyarlarPage from "./modules/ayarlar/AyarlarPage";
import BirlikDonemiPage from "./modules/birlik-donemi/BirlikDonemiPage";
import KapanisPenceresi from "./modules/cikis/KapanisPenceresi";
import ErisimGunluguPage from "./modules/erisim/ErisimGunluguPage";
import { ERISIM_GUNLUGU_BASLIGI } from "./modules/erisim/metinler";
import ParolaYenilenmeBildirimi from "./modules/butunluk/ParolaYenilenmeBildirimi";
import GecisKurulumuPage from "./modules/gecis-kurulumu/GecisKurulumuPage";
import GuvenlikKapisi from "./modules/guvenlik/GuvenlikKapisi";
import YenidenBaslatEkrani from "./modules/guvenlik/YenidenBaslatEkrani";
import HakkindaPage from "./modules/hakkinda/HakkindaPage";
import KilavuzPage from "./modules/kilavuz/KilavuzPage";
import KisilerPage from "./modules/kisiler/KisilerPage";
import KullanicilarPage from "./modules/kullanicilar/KullanicilarPage";
import { KULLANICILAR_BASLIGI } from "./modules/kullanicilar/metinler";
import KurulumPage from "./modules/kurulum/KurulumPage";
import RolKapisi, { KURULUM_SIHIRBAZI_KAPALI_ILETISI } from "./modules/oturum/RolKapisi";
import { YetkiSaglayici } from "./modules/oturum/yetki";
import PanelPage from "./modules/panel/PanelPage";

export default function App() {
  return (
    <YetkiSaglayici>
      <AppShell>
        {/* Geri yükleme sonrası tam ekran "yeniden başlatın" örtüsü — kapıların
            DIŞINDA: kilit/kurulum durumu ne olursa olsun her şeyi örtmelidir. */}
        <YenidenBaslatEkrani />
        {/* Uzun iş sürerken gelen kapanışın iletisi: çarpı her ekranda basılabilir, kapıların
            DIŞINDADIR (kilit, kurulum ve yeniden başlat ekranında da açılır). */}
        <KapanisPenceresi />
        <GuvenlikKapisi>
          {/* Parola yenilenme bildirimi (tasarım §4.4.3, tehdit 12): parolası sıfırlanan ya da
              kurtarma anahtarıyla yenilenen hesabın sahibine, kilit ekranından açılıştan sonra
              hangi sayfada olursa olsun pencere olarak çıkar; bildirim yoksa hiçbir şey çizmez. */}
          <ParolaYenilenmeBildirimi />
          <KurulumKapisi>
            <Routes>
              <Route path="/" element={<PanelPage />} />
              {/* Kurulum sihirbazı — kapının izin verdiği tek rota (bkz. KurulumKapisi). Her
                  denetimi bir yazmadır: kurulum durumu dışında `kurulum_tamamlama`'ya bağlı. */}
              <Route
                path="/kurulum"
                element={
                  <RolKapisi
                    yetenek="kurulum_tamamlama"
                    baslik="Kurulum Sihirbazı"
                    kapaliIletisi={KURULUM_SIHIRBAZI_KAPALI_ILETISI}
                  >
                    <KurulumPage />
                  </RolKapisi>
                }
              />
              {/* Birlik dönemi ve geçiş kurulumu (F1c 11. adım): her role okumaya açık (M1); yazma
                  denetimleri `birlik_donemi_yazma`'ya bağlıdır. Geçiş Kurulumu gezinmede yoktur. */}
              <Route path="/birlik-donemi" element={<BirlikDonemiPage />} />
              <Route path="/birlik-donemi/gecis-kurulumu" element={<GecisKurulumuPage />} />
              {/* Öğretmen ve diğer personel sicili, e-Okul içe aktarma, birlik kişileri. */}
              <Route path="/kisiler" element={<KisilerPage />} />
              {/* Hesaplar (yalnız `kullanicilar` yeteneği; matriste öteki roller "—"). */}
              <Route
                path="/kullanicilar"
                element={
                  <RolKapisi yetenek="kullanicilar" baslik={KULLANICILAR_BASLIGI}>
                    <KullanicilarPage />
                  </RolKapisi>
                }
              />
              {/* Erişim günlüğü (yalnız `erisim_gunlugu` yeteneği; matriste öteki roller "—"). */}
              <Route
                path="/erisim-gunlugu"
                element={
                  <RolKapisi yetenek="erisim_gunlugu" baslik={ERISIM_GUNLUGU_BASLIGI}>
                    <ErisimGunluguPage />
                  </RolKapisi>
                }
              />
              {/* Ders yılı, kapalı günler, okul bilgileri, güvenlik, güncelleme. */}
              <Route path="/ayarlar" element={<AyarlarPage />} />
              {/* Kullanım kılavuzu (statik içerik, çevrimdışı). */}
              <Route path="/kilavuz" element={<KilavuzPage />} />
              <Route path="/hakkinda" element={<HakkindaPage />} />
            </Routes>
          </KurulumKapisi>
        </GuvenlikKapisi>
      </AppShell>
    </YetkiSaglayici>
  );
}
