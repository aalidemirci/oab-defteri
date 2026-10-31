// Görevli kipinin ana ekranı (U5). Görevli kipinde rotaların YERİNE gösterilir:
// görevli yönetici ekranlarına (kişiler, ayarlar, yedek…) ulaşamaz. Backend bunu
// ayrıca keser (403 `kip_yetkisiz`); bu ekran kullanıcıya boş ya da hata dolu
// sayfalar yerine ne yapacağını söyler.
//
// Aile iskeletinde görevli ekranı kütüphanenin masa işlerini (dolaşım masası,
// etiket doğrulama, katalogda arama, teslimden geri alma, sayım okutması)
// taşıyordu; bunlar kütüphane uygulamasıyla birlikte F1a-2'de söküldü. Görevli
// kipi F1b'de OAB'nin oturum ve rol düzenine dönüşür (tasarım §4.4, §12.B
// `kip` → `oturum`). Sayfanın h1'i "Görevli Kipi"dir (üst çubukla aynı).

import { useState } from "react";

import Button from "../../ui/Button";
import Icon from "../../ui/Icon";
import YoneticiParolaDiyalogu from "./YoneticiParolaDiyalogu";
import type { KipOzeti } from "./api";

/** Üst çubuk başlığı sayfanın h1'iyle aynıdır. */
export const GOREVLI_EKRANI_BASLIGI = "Görevli Kipi";

export const GOREVLI_EKRANI_METNI =
  "Bu kipte kayıt işlemi yapılmaz; yönetici işlemleri için yönetici kipine geçin.";

/**
 * Kurtarma anahtarı (kurulumda verilen ya da Ayarlar → Güvenlik'te yenilenen)
 * doğrulanmadan görevli kipine geçilirse (düğme, kısayol) gösterilir: anahtar
 * kaybolmadı, yönetici kipine dönülünce anahtarın gösterildiği ekran onu yeniden
 * gösterir (`guvenlik/bekleyenAnahtar`). Kurulum sürerken süreler kipi düşürmez.
 */
export const BEKLEYEN_ANAHTAR_METNI =
  "Kurtarma anahtarınız henüz doğrulanmadı. Yönetici kipine geçtiğinizde anahtar yeniden gösterilir; programı kapatmayın.";

function BekleyenAnahtarUyarisi() {
  return (
    <p className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-4 py-3 text-left text-body-medium text-on-tertiary-container">
      <Icon name="key" size="lg" />
      <span>{BEKLEYEN_ANAHTAR_METNI}</span>
    </p>
  );
}

export default function GorevliEkrani({
  onGecti,
  anahtarBekliyor = false,
}: {
  onGecti: (ozet: KipOzeti) => void;
  /** Kurulumda doğrulanmamış kurtarma anahtarı bellekte bekliyor mu? */
  anahtarBekliyor?: boolean;
}) {
  const [diyalogAcik, setDiyalogAcik] = useState(false);

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-headline-small text-on-surface">{GOREVLI_EKRANI_BASLIGI}</h1>
          <p className="mt-1 text-body-medium text-on-surface-variant">{GOREVLI_EKRANI_METNI}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button icon="admin_panel_settings" onClick={() => setDiyalogAcik(true)}>
            Yönetici kipine geç
          </Button>
        </div>
      </div>
      {anahtarBekliyor && <BekleyenAnahtarUyarisi />}
      <YoneticiParolaDiyalogu
        open={diyalogAcik}
        onClose={() => setDiyalogAcik(false)}
        onGecti={onGecti}
      />
    </div>
  );
}
