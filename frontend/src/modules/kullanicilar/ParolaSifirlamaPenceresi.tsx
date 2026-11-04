// "Parolayı sıfırla" penceresi (plan F1b-2 "Geçici parola"; tasarım §4.4.5 "Parola unutuldu").
// Alan programın önerisiyle dolu gelir (`GeciciParolaAlani`); gönderimden önce parola kuralı
// denetlenir (`parolaSorunu`; otorite sunucudur, iletiler birebir). Başarıda pencere kapanır,
// snackbar zarfı hatırlatır; geçici parola hiçbir yerde gösterilmez ve bellekte bekletilmez.
// Ret pencerenin genel iletisidir (sunucunun Türkçe iletisi: askıdaki hesap, kaydı tutmayan hesap,
// güvenlik dosyası yazılamadı…). Her denemeden sonra liste yeniden okunur (`onDegisti`): güvenlik
// dosyası yazılamazsa hesap yine de "Parola yenilenmeli"ye düşmüş olabilir.
// Kendi hesabında eylem sunucunun nedeniyle kapalıdır; pencere oradan açılmaz.

import { useRef, useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { oturumHataMetni } from "../oturum/hatalar";
import { parolaSorunu } from "../oturum/parolaPolitikasi";
import GeciciParolaAlani from "./GeciciParolaAlani";
import { kullanicilarApi } from "./api";
import type { KullaniciSatiri } from "./api";
import { geciciParolaOner } from "./geciciParola";
import {
  DUGME_SIFIRLA_ONAY,
  SIFIRLAMA_ACIKLAMASI,
  SIFIRLAMA_BASLIGI,
  SIFIRLANAMADI,
  SIFIRLANDI_ILETISI,
  SIFIRLANIYOR,
  hesapAdi,
} from "./metinler";

interface Props {
  hesap: KullaniciSatiri;
  onClose: () => void;
  /** Liste yeniden okunsun (başarıda ve retten sonra). */
  onDegisti: () => void;
}

export default function ParolaSifirlamaPenceresi({ hesap, onClose, onDegisti }: Props) {
  const snackbar = useSnackbar();
  const alan = useRef<HTMLInputElement>(null);
  const [parola, setParola] = useState(() => geciciParolaOner());
  const [alanHatasi, setAlanHatasi] = useState<string | undefined>(undefined);
  const [genelHata, setGenelHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);

  function kapat() {
    setParola("");
    onClose();
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    setGenelHata(null);
    const sorun = parolaSorunu(parola);
    setAlanHatasi(sorun ?? undefined);
    if (sorun) {
      alan.current?.focus();
      return;
    }
    setCalisiyor(true);
    try {
      await kullanicilarApi.parolaSifirla(hesap.id, parola);
      setParola("");
      snackbar.success(SIFIRLANDI_ILETISI);
      onClose();
    } catch (err) {
      setGenelHata(oturumHataMetni(err, SIFIRLANAMADI));
    } finally {
      setCalisiyor(false);
      onDegisti();
    }
  }

  return (
    <Dialog open onClose={kapat} title={SIFIRLAMA_BASLIGI} initialFocusRef={alan}>
      <form onSubmit={gonder} noValidate className="flex flex-col gap-4">
        <p className="text-body-medium text-on-surface">
          Hesap: <strong>{hesapAdi(hesap)}</strong>
        </p>
        <p className="text-body-medium text-on-surface-variant">{SIFIRLAMA_ACIKLAMASI}</p>
        <GeciciParolaAlani
          ref={alan}
          deger={parola}
          onDeger={setParola}
          hata={alanHatasi}
          disabled={calisiyor}
        />
        {genelHata && (
          <p role="alert" className="text-body-medium text-error">
            {genelHata}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="text" type="button" onClick={kapat}>
            Vazgeç
          </Button>
          <Button type="submit" icon="lock_reset" disabled={calisiyor || parola === ""}>
            {calisiyor ? SIFIRLANIYOR : DUGME_SIFIRLA_ONAY}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
