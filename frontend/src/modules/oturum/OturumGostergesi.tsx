// Oturum göstergesi — AppShell üst çubuğunda (tasarım §4.4.3, TK14; plan F1b-1 "Oturum").
// Aile iskeletinin kip göstergesinin yerini alır: görevli kipi, "Yönetici kipine geç" ve
// Ctrl+Shift+G yoktur.
//
// Açık oturumda: oturumdaki hesabın rol etiketi (büyük) ve tanıtıcısı (küçük) — kişi adı
// DEĞİL (sözlük §5) — boşta kilide görsel geri sayım ve "Kilitle" (kısayol Ctrl+Shift+L).
// "Kullanıcı değiştir" ayrı düğme değildir: Kilitle + başka hesapla açmaktır.
// * Geri sayım ve boşta kilit ipucu yalnız kurulum tamamlandıktan sonra görünür (kurulum
//   sihirbazı bitene dek süre kilitlemez; tasarım §13 D15). Mutlak süre yoktur.
// * Uzun iş sürerken kilit ertelenmişse "İşlem bitince kilitlenecek" yazar, sayaç durur.
// * Geri sayım YALNIZ GÖRSELDİR: süre sunucuda tembel dolar; sayaç sıfıra inince oturum
//   sunucuya yeniden sorulur, kilitliyse pencere yeniden yüklenir (`useOturum`).
// Kilitli, kurulum (hesap yok), kayıp dosya ya da oturum okunamadıysa gösterge boştur
// (kilit ekranı ve sihirbaz kendi kapılarındadır).
//
// Kısayol Ctrl+Shift+L ("L" = lock): Ctrl ya da Alt tek başına seçilmedi, tarayıcı/WebView2
// kısayollarıyla (Ctrl+L adres çubuğu) çakışmasın. Düğmenin ipucunda ve
// `aria-keyshortcuts`'ta yazar.

import { useEffect, useState } from "react";

import { sonEtkinlikGonderimiAni } from "../../lib/api";
import Button from "../../ui/Button";
import Icon from "../../ui/Icon";
import {
  KILITLE_KISAYOLU,
  KILITLE_KISAYOLU_ARIA,
  KILIT_BEKLIYOR_METNI,
  kilitleKisayoluMu,
  useKilitle,
} from "./useKilitle";
import { kalanSaniye, sureBicimle, useEtkinlikNabzi, useOturum } from "./useOturum";

export default function OturumGostergesi() {
  const { ozet, alindi, yenile, ozetiYaz } = useOturum();
  const kilitle = useKilitle();
  const [simdi, setSimdi] = useState(() => Date.now());
  const durum = ozet?.durum;
  const sayacIsler = durum === "acik" && ozet?.bosta_kalan_sn != null;

  useEtkinlikNabzi(durum, ozetiYaz);

  // Saniyelik görsel geri sayım (yalnız sayaç işlerken).
  useEffect(() => {
    if (!sayacIsler) return;
    setSimdi(Date.now());
    const zamanlayici = window.setInterval(() => setSimdi(Date.now()), 1000);
    return () => window.clearInterval(zamanlayici);
  }, [sayacIsler]);

  const kalan = ozet ? kalanSaniye(ozet, alindi, simdi, sonEtkinlikGonderimiAni()) : null;
  const sureDoldu = kalan === 0;

  // Sayaç sıfırlandı: oturum sunucuda büyük olasılıkla kilitlendi, sor (yoklama görürse yükler).
  useEffect(() => {
    if (sureDoldu) yenile();
  }, [sureDoldu, yenile]);

  useEffect(() => {
    if (durum !== "acik") return;
    const dinle = (e: KeyboardEvent) => {
      if (!kilitleKisayoluMu(e) || e.repeat) return;
      e.preventDefault();
      void kilitle();
    };
    window.addEventListener("keydown", dinle);
    return () => window.removeEventListener("keydown", dinle);
  }, [durum, kilitle]);

  if (durum !== "acik" || !ozet?.hesap) return null;
  const { hesap } = ozet;

  // İpucu yalnız kurulumdan sonra; kurulumda süre işlemez (D15).
  const ipucu = ozet.kurulum_tamam
    ? `Program ${ozet.bosta_dk} dakika işlem yapılmazsa kilitlenir. Bilgisayar başından ` +
      "kalkarken Kilitle'ye basın."
    : undefined;

  return (
    <div className="flex min-w-0 items-center gap-1 sm:gap-2" aria-label="Oturum" role="group">
      <span
        className="inline-flex min-w-0 items-center gap-2 rounded-full bg-primary-container px-3 py-1 text-on-primary-container"
        title={ipucu}
      >
        <Icon name="account_circle" size="lg" />
        <span className="sr-only flex-col leading-tight md:not-sr-only md:flex">
          <span className="truncate text-label-large font-semibold">{hesap.rol_etiketi}</span>
          <span className="truncate text-label-small">{hesap.tanitici}</span>
        </span>
        {kalan !== null && (
          <span className="text-label-large tabular-nums" data-testid="oturum-geri-sayim">
            <span className="sr-only">, kilitlenmeye kalan süre </span>
            {sureBicimle(kalan)}
          </span>
        )}
      </span>

      {ozet.kilit_bekliyor && (
        <span role="status" className="text-label-medium text-on-surface-variant">
          {KILIT_BEKLIYOR_METNI}
        </span>
      )}

      <Button
        variant="text"
        icon="lock"
        onClick={() => void kilitle()}
        aria-label="Kilitle"
        aria-keyshortcuts={KILITLE_KISAYOLU_ARIA}
        title={`Kilitle (${KILITLE_KISAYOLU})`}
      >
        <span className="hidden lg:inline">Kilitle</span>
      </Button>
    </div>
  );
}
