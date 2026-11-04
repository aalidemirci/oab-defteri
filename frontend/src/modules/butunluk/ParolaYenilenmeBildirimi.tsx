// Parola yenilenme bildirimi (tasarım §4.4.3 "Kurtarma anahtarıyla açılış", §4.3 tehdit 10 ve
// 12; plan F1b-1 alt commit c).
//
// Program yöneticisi bir hesabın parolasını sıfırladıysa ya da program yöneticisi hesabının
// parolası kurtarma anahtarıyla yenilendiyse, hesabın sahibi ilk girişinde "Parolanız
// gg.aa.yyyy tarihinde sıfırlandı." / "… kurtarma anahtarıyla yenilendi." bildirimini ve o
// tarihten bu yana HESABIYLA yapılan girişleri görür (başka hesabın girişi yoktur).
//
// NEREDE: kilit ekranından açılış pencereyi yeniden yükler (tasarım §13 D53) ve pencere
// önceki adreste açılır — kullanıcı Genel Bakış'a düşmeyebilir. Bildirim bu yüzden pano
// kartı değil, oturum açıkken uygulama kabuğunda (güvenlik kapısının içinde) kendiliğinden
// açılan bir penceredir; hangi sayfada açılırsa açılsın görünür.
//
// "Gördüm" bildirimi izli bir yazımla kapatır (`POST security/integrity/reset-notice/` →
// `GUNCELLE` satırı). Esc ya da pencere dışı tıklama yalnız bu pencereyi kapatır; bildirim
// bir sonraki girişte yeniden gösterilir. Kalan risk (dürüst): oturumu açan kişi bildirimi
// kapatabilir — sıfırlamayla hesabı devralan da. Kalıcı karşılık Genel Bakış'taki "Son
// Girişler" kartı ve denetim izidir; pencere bunu söyler.
//
// Durum okunamazsa (ağ, 423, hesap kurulmamış) hiçbir şey göstermez.

import { useEffect, useState } from "react";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { butunlukApi } from "./api";
import type { ParolaBildirimiYaniti, ParolaYenilenme } from "./api";
import { PAROLA_BILDIRIMI_BASLIGI, parolaYenilenmeCumlesi, parolaYenilenmeOgudu } from "./metinler";

/**
 * Yanıttaki bildirim; yoksa ya da biçimi beklenmedikse (eski sürüm, beklenmeyen gövde) null —
 * pencere yalnız okunabilir bir bildirimle açılır.
 */
export function bildirimiOku(yanit: unknown): ParolaYenilenme | null {
  if (yanit === null || typeof yanit !== "object") return null;
  const bildirim = (yanit as Partial<ParolaBildirimiYaniti>).parola_yenilenme;
  if (bildirim === null || bildirim === undefined || typeof bildirim.zaman !== "string") {
    return null;
  }
  return { ...bildirim, girisler: Array.isArray(bildirim.girisler) ? bildirim.girisler : [] };
}

export default function ParolaYenilenmeBildirimi() {
  const [bildirim, setBildirim] = useState<ParolaYenilenme | null>(null);
  const [acik, setAcik] = useState(false);
  const [mesgul, setMesgul] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  useEffect(() => {
    let iptal = false;
    butunlukApi
      .parolaBildirimi()
      .then((yanit) => {
        const okunan = bildirimiOku(yanit);
        if (iptal || okunan === null) return;
        setBildirim(okunan);
        setAcik(true);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  if (bildirim === null) return null;

  const gordum = async () => {
    setMesgul(true);
    setHata(null);
    try {
      setBildirim(bildirimiOku(await butunlukApi.parolaBildiriminiGordum()));
      setAcik(false);
    } catch (e) {
      setHata(hataOku(e, "Bildirim kaydedilemedi."));
    } finally {
      setMesgul(false);
    }
  };

  return (
    <Dialog
      open={acik}
      onClose={() => setAcik(false)}
      title={PAROLA_BILDIRIMI_BASLIGI}
      actions={
        <Button variant="filled" icon="task_alt" onClick={() => void gordum()} disabled={mesgul}>
          Gördüm
        </Button>
      }
    >
      <div className="space-y-3">
        <p className="text-body-large font-semibold text-on-surface">
          {parolaYenilenmeCumlesi(bildirim.tur, bildirim.zaman)}
        </p>
        {bildirim.girisler.length > 0 && (
          <div className="space-y-1">
            <p className="text-body-medium text-on-surface">
              O tarihten bu yana hesabınızla yapılan girişler:
            </p>
            <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
              {bildirim.girisler.map((an, i) => (
                <li key={an}>
                  {formatDateTime(an)}
                  {i === 0 ? " · bu oturum" : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-body-medium text-on-surface">{parolaYenilenmeOgudu(bildirim.tur)}</p>
        <p className="text-body-small text-on-surface-variant">
          Son girişleriniz Genel Bakış&apos;taki Son Girişler kartında da görünür. “Gördüm”e
          basmadan kapatırsanız bildirim bir sonraki girişinizde yeniden gösterilir.
        </p>
        {hata && <ErrorBand hata={hata} />}
      </div>
    </Dialog>
  );
}
