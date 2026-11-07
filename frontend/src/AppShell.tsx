import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import CikisDugmesi from "./modules/cikis/CikisDugmesi";
import UpdateBanner from "./modules/guncelleme/UpdateBanner";
import OturumGostergesi from "./modules/oturum/OturumGostergesi";
import type { YetenekAdi } from "./modules/oturum/api";
import { useYetki } from "./modules/oturum/yetki";
import type { Yetki } from "./modules/oturum/yetki";
import DensitySwitcher from "./ui/DensitySwitcher";
import { DurumBasligiSaglayici, useDurumBasligiYonetimi } from "./ui/DurumBasligi";
import Icon from "./ui/Icon";
import ThemeSwitcher from "./ui/ThemeSwitcher";

export interface NavItem {
  to: string;
  label: string;
  icon: string;
  /**
   * Ekranın yeteneği (plan F1b-2 "Ön yüz"): verilirse girdi yalnız o yetenek açıkken görünür
   * (matriste "—" olan ekran gezinmede yer almaz); rotası `RolKapisi` ile aynı yeteneğe bağlanır.
   * Verilmeyen ekran her role en az okumaya açıktır.
   */
  yetenek?: YetenekAdi;
}

// Gezinme etiketi KISA addır. Ana sayfanın tek adı "Genel Bakış"tır (gezinme +
// üst çubuk + h1). OAB ekranları (birlik dönemi, organlar…) fazlarıyla birlikte
// eklenir; aile iskeletinin kütüphane ekranları F1a-2'de söküldü. Liste
// `App.test.tsx` "kabuk gezinmesi" testiyle sabittir. Genel Bakış, Kişiler, Ayarlar ve Kılavuz
// her role açıktır (Kişiler'de personeli her rol okur, Ayarlar'ı her rol okur); Kullanıcılar
// yalnız `kullanicilar`, Erişim Günlüğü yalnız `erisim_gunlugu` yeteneğinde görünür (program
// yöneticisi ve Denetleme Kurulu).
const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Genel Bakış", icon: "space_dashboard" },
  { to: "/kisiler", label: "Kişiler", icon: "group" },
  { to: "/kullanicilar", label: "Kullanıcılar", icon: "manage_accounts", yetenek: "kullanicilar" },
  { to: "/erisim-gunlugu", label: "Erişim Günlüğü", icon: "policy", yetenek: "erisim_gunlugu" },
  { to: "/ayarlar", label: "Ayarlar", icon: "settings" },
  { to: "/kilavuz", label: "Kılavuz", icon: "auto_stories" },
];

// Üst çubuk başlığı sayfanın h1'iyle AYNIDIR (docs/sozluk.md §4) — Başlık
// Düzeninde tam ad. Bir sayfanın h1'i değişirse burası da değişir; eşlik
// `App.test.tsx` "üst çubuk başlığı" testiyle korunur.
const PAGE_TITLES: Array<[prefix: string, title: string]> = [
  // Sıra anlamlıdır: alt sayfalar köke göre ÖNCE gelir.
  ["/kisiler", "Kişiler"],
  ["/kullanicilar", "Kullanıcılar"],
  ["/erisim-gunlugu", "Erişim Günlüğü"],
  ["/ayarlar", "Ayarlar"],
  ["/kilavuz", "Kullanım Kılavuzu"],
  ["/hakkinda", "Hakkında ve Lisans"],
  ["/kurulum", "Kurulum Sihirbazı"],
  ["/", "Genel Bakış"],
];

const COLLAPSE_KEY = "oab-defteri-sidebar-collapsed";

// Kenar çubuğu iki temada da koyudur: düğmeler `navLinkClass`ın pasif rengini taşır.
const KENAR_DUGME_RENGI = "text-on-sidebar-muted hover:bg-on-sidebar/8 hover:text-on-sidebar";

// Yan menü açıkken arka sayfa kaymasın diye kök öğeye yazılır. `max-lg`: yan menü `lg:hidden`dır;
// açıkken pencere büyütülürse menü gizlenir, sayfa kilitli kalmaz.
const ARKA_SAYFA_KILIDI = "max-lg:overflow-hidden";

/**
 * Rolün gördüğü gezinme girdileri: yeteneksiz girdi her zaman, yetenekli girdi yalnız yetenek
 * açıkken (yüklenirken ve özet okunamadıysa görünmez; kurulumda süzme yok — `oturum/yetki`).
 */
export function gezinmeGirdileri(girdiler: readonly NavItem[], yetki: Yetki): NavItem[] {
  return girdiler.filter((g) => g.yetenek === undefined || yetki.acik(g.yetenek));
}

function pageTitle(pathname: string): string {
  return (
    PAGE_TITLES.find(([prefix]) =>
      prefix === "/" ? pathname === "/" : pathname.startsWith(prefix),
    )?.[1] ?? "OAB Defteri"
  );
}

function navLinkClass(isActive: boolean, collapsed: boolean): string {
  const base = `group relative flex min-h-11 items-center overflow-hidden rounded-shape-md text-label-large font-medium transition-all duration-short-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
    collapsed ? "justify-center px-2" : "gap-3 px-3"
  }`;
  return isActive
    ? `${base} bg-sidebar-active text-on-sidebar shadow-elevation-1`
    : `${base} text-on-sidebar-muted hover:bg-on-sidebar/8 hover:text-on-sidebar`;
}

function SidebarContent({
  collapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const girdiler = gezinmeGirdileri(NAV_ITEMS, useYetki());
  return (
    // Kısa pencerede içerik kendi içinde kayar (gerçek pencere sınaması 07.11.2026: alttaki
    // satırlar görünmüyordu, tekerlek arkadaki sayfayı kaydırıyordu). Kap `aside`ın içindedir,
    // kendisi değil: `aside` kaydırılsaydı kenardan taşan daraltma düğmesi kırpılırdı.
    // Kaydırmanın arkaya geçmemesi (`overscroll-contain`) yalnız yan menüdedir (lg altı): masaüstünde
    // uzun pencerede kap taşmazken de tekerleği tutuyor, sayfa kaymıyordu (sınama 07.11.2026, kusur 22).
    <div className="od-sidebar-scroll flex min-h-0 flex-1 flex-col overflow-y-auto max-lg:overscroll-contain">
      <div
        className={`flex h-20 shrink-0 items-center border-b border-on-sidebar/10 ${
          collapsed ? "justify-center px-2" : "gap-3 px-4"
        }`}
      >
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg bg-on-sidebar/95 shadow-elevation-2">
          <img src="/app-logo.png" alt="" className="h-10 w-10 object-contain" />
        </span>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-title-medium font-semibold tracking-tight text-on-sidebar">
              OAB Defteri
            </p>
          </div>
        )}
      </div>

      {!collapsed && (
        <p className="px-5 pb-2 pt-5 text-label-small font-semibold uppercase tracking-widest text-on-sidebar-muted/70">
          Çalışma alanı
        </p>
      )}
      <nav aria-label="Ana gezinme" className="flex flex-1 flex-col gap-1.5 px-3 py-2">
        {/* Rol bazlı gezinme (tasarım §4.4.2; plan F1b-2): kaynak yeteneklerdir. */}
        {girdiler.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            title={collapsed ? item.label : undefined}
            aria-label={collapsed ? item.label : undefined}
            onClick={onNavigate}
            className={({ isActive }) => navLinkClass(isActive, collapsed)}
          >
            <span aria-hidden="true" className="state-layer" />
            <Icon name={item.icon} size="xl" filled className="relative z-10 shrink-0 opacity-95" />
            {!collapsed && <span className="relative z-10 truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="space-y-1 border-t border-on-sidebar/10 p-3">
        {!collapsed && (
          <div className="mb-2 rounded-shape-md border border-on-sidebar/10 bg-on-sidebar/5 px-3 py-2.5">
            <p className="flex items-center gap-2 text-label-medium text-on-sidebar">
              <span className="h-2 w-2 rounded-full bg-success" />
              Yerel çalışma
            </p>
            <p className="mt-0.5 text-body-small text-on-sidebar-muted">Veriler bu cihazda</p>
          </div>
        )}
        <NavLink
          to="/hakkinda"
          title={collapsed ? "Hakkında ve Lisans" : undefined}
          aria-label={collapsed ? "Hakkında ve Lisans" : undefined}
          onClick={onNavigate}
          className={({ isActive }) => navLinkClass(isActive, collapsed)}
        >
          <span aria-hidden="true" className="state-layer" />
          <Icon name="info" size="xl" filled className="relative z-10 shrink-0 opacity-95" />
          {!collapsed && <span className="relative z-10 truncate">Hakkında ve Lisans</span>}
        </NavLink>
        <DensitySwitcher collapsed={collapsed} className={KENAR_DUGME_RENGI} />
        <ThemeSwitcher satir collapsed={collapsed} className={KENAR_DUGME_RENGI} />
      </div>
    </div>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(
    () => window.localStorage.getItem(COLLAPSE_KEY) === "true",
  );
  const [mobileOpen, setMobileOpen] = useState(false);
  // Program durumu ekranları (kilitli, güvenlik dosyası kayıp, yeniden başlat)
  // açıkken üst çubukta o ekranın h1'i yazar — sözlük §4.2. Adrese bağlı
  // olmadıkları için başlığı kendileri bildirir (ui/DurumBasligi).
  const { durumBasligi, yaz } = useDurumBasligiYonetimi();
  const title = durumBasligi ?? pageTitle(location.pathname);
  const yetki = useYetki();

  // Sayfa değişince kaydırma başa döner (gerçek pencere sınaması 07.11.2026). Kaydıran pencerenin
  // kendisidir: kök `min-h-screen`dir, `main`in yüksekliği sınırsızdır, kendi içinde kaymaz. Yalnız
  // yol adına bakılır: sekme (`?tab=`) ve çapa (`#`) aynı sayfadır, kaydırmaya dokunulmaz. Çapalı
  // gelişte (`/kilavuz#bolum`) bu etki önce koşar, `useCapayaKaydir`ın etkisi sonra bölüme götürür.
  // Çizimden önce koşar: yeni sayfa eski kaydırma yerinde görünmez. İlk açılışta dokunulmaz.
  const oncekiYol = useRef(location.pathname);
  useLayoutEffect(() => {
    if (oncekiYol.current === location.pathname) return;
    oncekiYol.current = location.pathname;
    window.scrollTo(0, 0);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const kok = document.documentElement;
    kok.classList.add(ARKA_SAYFA_KILIDI);
    return () => kok.classList.remove(ARKA_SAYFA_KILIDI);
  }, [mobileOpen]);

  const toggleCollapsed = () => {
    setCollapsed((current) => {
      const next = !current;
      window.localStorage.setItem(COLLAPSE_KEY, String(next));
      return next;
    });
  };

  return (
    <div className="flex min-h-screen bg-surface text-on-surface">
      <aside
        className={`od-sidebar-glow sticky top-0 z-40 hidden h-screen shrink-0 flex-col transition-[width] duration-medium-1 ease-emphasized lg:flex ${
          collapsed ? "w-[4.75rem]" : "w-60"
        }`}
      >
        <SidebarContent collapsed={collapsed} />
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Kenar çubuğunu genişlet" : "Kenar çubuğunu daralt"}
          title={collapsed ? "Kenar çubuğunu genişlet" : "Kenar çubuğunu daralt"}
          className="absolute -right-3 top-24 flex h-7 w-7 items-center justify-center rounded-full border border-outline-variant bg-surface-container-lowest text-on-surface-variant shadow-elevation-2 transition hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <Icon name={collapsed ? "chevron_right" : "chevron_left"} size="sm" />
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-outline-variant/70 bg-surface-container-lowest/95 px-4 backdrop-blur-md sm:px-5 lg:px-7">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Gezinme menüsünü aç"
            className="od-icon-button lg:hidden"
          >
            <Icon name="menu" />
          </button>
          <img src="/app-logo.png" alt="" className="h-9 w-9 shrink-0 object-contain lg:hidden" />
          {/* Başlık üst çubukta kalan yerin tamamını alır: yer yetmezse kısalır, yetiyorsa
              kesilmez. Sabit genişlikte "Programı kapatıp yeniden açın" geniş pencerede de
              kesiliyordu. */}
          <div className="min-w-0 flex-1">
            <p className="truncate text-title-medium font-semibold text-on-surface">{title}</p>
            <p className="hidden truncate text-body-small text-on-surface-variant lg:block">
              OAB Defteri
            </p>
          </div>

          {/* Tema anahtarı YALNIZ kenar çubuğundadır (görünüm ayarları bir arada:
              yoğunluk + tema; dar ekranda menü çekmecesinden erişilir). Eskiden
              burada ikinci bir kopyası vardı — aynı ayarın iki düğmesi hangisinin
              "asıl" olduğu sorusunu doğuruyordu. */}

          {/* Oturum göstergesi (tasarım §4.4.3, TK14): oturumdaki hesabın rol etiketi ve
              tanıtıcısı, boşta kilide görsel geri sayım (kurulumdan sonra), "Kilitle"
              (Ctrl+Shift+L). Kilitliyken, kurulumda ve oturum okunamazsa boştur. */}
          <div className="ml-auto flex min-w-0 items-center gap-1">
            <OturumGostergesi />
            {/* Çık (tasarım §4.2 "Kapanış"): her durumda görünür ve parolasızdır;
                pencerenin çarpısıyla aynı düzenli kapanış yoludur (T6, tepsi yoktur). */}
            <CikisDugmesi />
          </div>
        </header>

        <main className="min-w-0 flex-1 overflow-x-hidden px-4 py-5 sm:px-5 lg:px-7 lg:py-6">
          <div className="mx-auto w-full max-w-[100rem]">
            {/* Güncelleme bandı açılışta DENETİM YAPMAZ (tasarım TK4): yalnız
                Ayarlar → Güncelleme'deki elle denetimin sonucunu gösterir.
                Açılışta `/updates/` isteği çıkmadığı `App.test.tsx`'te sabittir.
                Yalnız güncelleme yeteneğinde (program yöneticisi; plan F1b-2 "Ayarlar ve
                bant"): öteki rollerde Güncelleme sekmesi de yoktur. */}
            {yetki.acik("guncelleme") && <UpdateBanner />}
            <DurumBasligiSaglayici yaz={yaz}>{children}</DurumBasligiSaglayici>
          </div>
        </main>
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 animate-scrim-in bg-scrim/50 backdrop-blur-sm"
            aria-label="Gezinme menüsünü kapat"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="od-sidebar-glow relative flex h-full w-72 animate-dialog-in flex-col shadow-elevation-4">
            <SidebarContent collapsed={false} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}
    </div>
  );
}
