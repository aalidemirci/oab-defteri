// OAB Defteri — kök route tanımı. Route ağacı fazlarla büyür (tasarım §14):
// aile iskeletinden gelen kabuk kurulum, kişiler, ayarlar, kılavuz ve hakkında
// ekranlarını taşır; OAB ekranları (birlik dönemi, organlar, pano…) F1c'den
// itibaren eklenir. Aile iskeletinin kütüphane ekranları F1a-2'de söküldü.
// Kilit ekranı (GuvenlikKapisi) kurulum kapısından ÖNCE gelir — hesap kuruluysa
// hiçbir veri ekranı (sihirbaz dahil) açılmadan kilit kişinin kendi hesabıyla
// açılmalıdır. Aile iskeletinin kip kapısı (görevli kipi) yoktur (tasarım TK14):
// oturum açıkken rotalar, kapalıyken kilit ekranı.

import { Route, Routes } from "react-router-dom";

import AppShell from "./AppShell";
import KurulumKapisi from "./KurulumKapisi";
import AyarlarPage from "./modules/ayarlar/AyarlarPage";
import GuvenlikKapisi from "./modules/guvenlik/GuvenlikKapisi";
import YenidenBaslatEkrani from "./modules/guvenlik/YenidenBaslatEkrani";
import HakkindaPage from "./modules/hakkinda/HakkindaPage";
import KilavuzPage from "./modules/kilavuz/KilavuzPage";
import KisilerPage from "./modules/kisiler/KisilerPage";
import KurulumPage from "./modules/kurulum/KurulumPage";
import PanelPage from "./modules/panel/PanelPage";

export default function App() {
  return (
    <AppShell>
      {/* Geri yükleme sonrası tam ekran "yeniden başlatın" örtüsü — kapıların
          DIŞINDA: kilit/kurulum durumu ne olursa olsun her şeyi örtmelidir. */}
      <YenidenBaslatEkrani />
      <GuvenlikKapisi>
        <KurulumKapisi>
          <Routes>
            <Route path="/" element={<PanelPage />} />
            {/* Kurulum sihirbazı — kapının izin verdiği tek rota (bkz. KurulumKapisi). */}
            <Route path="/kurulum" element={<KurulumPage />} />
            {/* Öğretmen ve diğer personel sicili, e-Okul içe aktarma. */}
            <Route path="/kisiler" element={<KisilerPage />} />
            {/* Ders yılı, şubeler, okul bilgileri, güvenlik, güncelleme. */}
            <Route path="/ayarlar" element={<AyarlarPage />} />
            {/* Kullanım kılavuzu (statik içerik, çevrimdışı). */}
            <Route path="/kilavuz" element={<KilavuzPage />} />
            <Route path="/hakkinda" element={<HakkindaPage />} />
          </Routes>
        </KurulumKapisi>
      </GuvenlikKapisi>
    </AppShell>
  );
}
