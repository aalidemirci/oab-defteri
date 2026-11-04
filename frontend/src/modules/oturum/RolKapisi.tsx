// Rol kapısının ön yüz ayağı (plan F1b-2 "Ön yüz"; tasarım §4.4.2): matriste "—" olan ekran
// gezinmede yer almaz (`AppShell` `NAV_ITEMS`), adresine yine de gelinirse rota bu ekranı
// gösterir: "Bu ekran hesabınızın rolüne açık değil." (sözlük §1 "Program yöneticisi ve
// roller"). "O" olan ekran açılır, yazma denetimleri gizlenir; okul sekmeleri gibi salt okur
// bölümlerin başında `SaltOkurNotu` durur. Süzmenin kaynağı yeteneklerdir (`yetki.tsx`);
// kurulum durumunda süzme yoktur (kapı içeriği gösterir).
//
// Özet yüklenirken iskelet çizilir (ekran sıçramasın); hiç okunamadıysa ekran "rolünüze açık
// değil" demez — bilinmeyeni söyler, yoklama özeti okuyunca kapı kendiliğinden açılır.

import type { ReactNode } from "react";

import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import type { YetenekAdi } from "./api";
import { useYetki } from "./yetki";

/** Rolün açamadığı ekranın tek iletisi (plan F1b-2 lafzı; sözlük §1). */
export const EKRAN_ROLE_KAPALI_ILETISI = "Bu ekran hesabınızın rolüne açık değil.";

/** Oturum özeti hiç okunamadığında (fail-closed; sözlük §1). */
export const YETKI_OKUNAMADI_ILETISI =
  "Hesabınızın rolü okunamadığı için bu ekran gösterilemiyor. Biraz sonra yeniden deneyin.";

/** Salt okur bölümün notu ("O" hücresi: ekran açılır, yazma denetimleri gizlenir; sözlük §1). */
export const SALT_OKUR_ILETISI = "Bu bölüm hesabınızın rolüne yalnız okuma için açık.";

/**
 * Kurulum Sihirbazı'nın öteki rollerdeki iletisi (kullanıcı kararı 04.11.2026: matriste "O"
 * olsa da sihirbazın her denetimi bir yazmadır, salt okur kipi yoktur; okulun bilgileri
 * Ayarlar'da salt okur görünür). Rol adı saymaz (sözlük §1 "Rol süzmesi").
 */
export const KURULUM_SIHIRBAZI_KAPALI_ILETISI =
  "Kurulum Sihirbazı yalnız kurulumu tamamlayabilen hesaba açıktır; bu bilgiler Ayarlar'da " +
  "görünür.";

interface RolKapisiProps {
  /** Ekranın yeteneği (`YETENEK_ADLARI`'ndan). */
  yetenek: YetenekAdi;
  /** Ekranın h1'i (üst çubuktaki başlıkla aynı; sözlük §4). Kapalı ekran da onu yazar. */
  baslik: string;
  /**
   * Rolün açamadığı ekranın iletisi; verilmezse tek ileti (`EKRAN_ROLE_KAPALI_ILETISI`).
   * Özet okunamadıysa her ekran `YETKI_OKUNAMADI_ILETISI`'ni yazar.
   */
  kapaliIletisi?: string;
  children: ReactNode;
}

/** Kapalı ekran: sayfanın h1'i + tek ileti. */
function KapaliEkran({ baslik, ileti }: { baslik: string; ileti: string }) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">{baslik}</h1>
        </div>
      </div>
      <Card elevation={0} className="flex items-start gap-3 p-6">
        <Icon name="lock" className="shrink-0 text-on-surface-variant" />
        <p className="text-body-large text-on-surface">{ileti}</p>
      </Card>
    </div>
  );
}

/** Ekranı yeteneğe bağlar: açıksa içerik, değilse kapalı ekran (dosya başı). */
export default function RolKapisi({
  yetenek,
  baslik,
  kapaliIletisi = EKRAN_ROLE_KAPALI_ILETISI,
  children,
}: RolKapisiProps) {
  const yetki = useYetki();
  if (yetki.durum === "yukleniyor") {
    return <SkeletonList rows={3} className="mx-auto max-w-3xl" />;
  }
  if (yetki.acik(yetenek)) return <>{children}</>;
  return (
    <KapaliEkran
      baslik={baslik}
      ileti={yetki.durum === "okunamadi" ? YETKI_OKUNAMADI_ILETISI : kapaliIletisi}
    />
  );
}

/** Salt okur bölümün başındaki not (`role="note"`; ekran okuyucu bölümle birlikte okur). */
export function SaltOkurNotu({ className = "" }: { className?: string }) {
  return (
    <p
      role="note"
      className={`flex items-start gap-2 rounded-shape-sm bg-secondary-container px-4 py-3 text-body-small text-on-secondary-container ${className}`}
    >
      <Icon name="visibility" size="lg" className="shrink-0" />
      <span>{SALT_OKUR_ILETISI}</span>
    </p>
  );
}
