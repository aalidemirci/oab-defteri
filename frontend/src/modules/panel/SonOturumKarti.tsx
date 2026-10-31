// Genel Bakış'ta "Son Oturumu Kontrol Edin" kartı (T15; tasarım §4.2 adım 3, §13 D4).
//
// Program önceki oturumda düzgün kapanmadıysa (elektrik kesintisi, zorla kapatma)
// son kayıtlar diske yazılmamış olabilir. Kart bunu söyler ve kullanıcıdan son
// oturumdaki kayıtları kontrol etmesini ister. "Kontrol ettim" kartı bu oturum
// için kapatır (onay süreç içindedir; bkz. `apps/okul/son_oturum.py`).
//
// Kart kişisel veri taşımaz. Durum okunamazsa kart gösterilmez; sayfanın geri
// kalanı çalışır.

import { useEffect, useState } from "react";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { panelApi } from "./api";
import type { SonOturumOzeti } from "./api";

export const SON_OTURUM_KARTI_BASLIGI = "Son Oturumu Kontrol Edin";

export default function SonOturumKarti() {
  const snackbar = useSnackbar();
  const [ozet, setOzet] = useState<SonOturumOzeti | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [mesgul, setMesgul] = useState(false);

  useEffect(() => {
    let iptal = false;
    panelApi
      .sonOturum()
      .then((o) => {
        if (!iptal) setOzet(o);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  if (ozet === null || !ozet.unexpected_shutdown) return null;

  const kontrolEttim = async () => {
    setMesgul(true);
    setHata(null);
    try {
      setOzet(await panelApi.kontrolEttim());
      snackbar.success("Son oturumun kontrolü tamamlandı.");
    } catch (e) {
      setHata(hataOku(e, "Kart kapatılamadı."));
    } finally {
      setMesgul(false);
    }
  };

  return (
    <section aria-labelledby="son-oturum-karti">
      <Card elevation={0} className="space-y-3 p-5">
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-shape-lg bg-tertiary-container text-on-tertiary-container">
            <Icon name="power_off" />
          </span>
          <div className="min-w-0 space-y-1">
            <h2 id="son-oturum-karti" className="text-title-medium font-semibold text-on-surface">
              {SON_OTURUM_KARTI_BASLIGI}
            </h2>
            <p className="text-body-medium text-on-surface">
              Program önceki oturumda düzgün kapanmadı (elektrik kesintisi ya da zorla kapatma
              olabilir). Son oturumdaki kayıtları kontrol edin.
            </p>
            <p className="text-body-small text-on-surface-variant">
              Kapanmadan hemen önce girdiğiniz bir kayıt yerinde değilse yeniden girin.
            </p>
          </div>
        </div>
        {hata && <ErrorBand hata={hata} />}
        <Button
          variant="tonal"
          icon="task_alt"
          onClick={() => void kontrolEttim()}
          disabled={mesgul}
        >
          Kontrol ettim
        </Button>
      </Card>
    </section>
  );
}
