// Çık düğmesi ve diyaloğu — üst çubukta her durumda görünür (tasarım §4.2, §4.5).
//
// * Her oturum durumunda (açık, kilitli, kurulum, kayıp güvenlik dosyası) aynı
//   "Programdan çıkılsın mı?" onayı; PAROLASIZDIR. Aile iskeletinin görevli kipindeki
//   parola dalı görevli kipiyle kalktı (tasarım §12.B; plan F1b-1 "Oturum").
// * Pencerenin çarpısı da programı kapatır (T6, tasarım §4.5); tepsi yoktur.
//
// Başarıda program kapanır: pencere birazdan kendiliğinden kaybolur.

import { useId, useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { oturumHataMetni } from "../oturum/hatalar";
import { cikisApi } from "./api";

function hataMesaji(err: unknown): string {
  return oturumHataMetni(err, "Programdan çıkılamadı.");
}

interface CikisDiyaloguProps {
  open: boolean;
  onClose: () => void;
}

export function CikisDiyalogu({ open, onClose }: CikisDiyaloguProps) {
  const formId = useId();
  const [hata, setHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);
  const [kapaniyor, setKapaniyor] = useState(false);

  function kapat() {
    setHata(null);
    onClose();
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    setHata(null);
    setCalisiyor(true);
    try {
      await cikisApi.cik();
      setKapaniyor(true);
    } catch (err) {
      setHata(hataMesaji(err));
    } finally {
      setCalisiyor(false);
    }
  }

  if (kapaniyor) {
    return (
      <Dialog open={open} onClose={() => undefined} title="Program kapanıyor">
        <p role="status">OAB Defteri kapanıyor…</p>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={open}
      onClose={kapat}
      // Sözlük §3: onay diyaloğunun başlığı soru, gövdesi sonuçtur.
      title="Programdan çıkılsın mı?"
      actions={
        <>
          <Button variant="text" type="button" onClick={kapat}>
            Vazgeç
          </Button>
          <Button type="submit" form={formId} icon="power_settings_new" disabled={calisiyor}>
            {calisiyor ? "Kapatılıyor…" : "Çık"}
          </Button>
        </>
      }
    >
      <form id={formId} onSubmit={gonder} className="flex flex-col gap-4">
        <p>Program kapanır. Pencerenin çarpısı da programı aynı biçimde kapatır.</p>
        {hata && (
          <p role="alert" className="text-body-medium text-error">
            {hata}
          </p>
        )}
      </form>
    </Dialog>
  );
}

/** Üst çubuktaki Çık düğmesi. */
export default function CikisDugmesi() {
  const [acik, setAcik] = useState(false);

  return (
    <>
      <Button
        variant="text"
        icon="power_settings_new"
        onClick={() => setAcik(true)}
        aria-label="Çık"
        title="Programdan çık"
      >
        <span className="hidden xl:inline">Çık</span>
      </Button>
      <CikisDiyalogu open={acik} onClose={() => setAcik(false)} />
    </>
  );
}

/**
 * "Programı kapatıp yeniden açın" ekranındaki doğrudan çıkış (parolasız; o ekran
 * diyalogların üstündedir, onay sorulmaz: programın yeniden açılması şarttır).
 */
export function DogrudanCikisDugmesi() {
  const [durum, setDurum] = useState<"bekliyor" | "kapaniyor" | "hata">("bekliyor");
  const [ileti, setIleti] = useState<string | null>(null);

  async function cik() {
    setIleti(null);
    try {
      await cikisApi.cik();
      setDurum("kapaniyor");
    } catch (err) {
      setDurum("hata");
      setIleti(hataMesaji(err));
    }
  }

  if (durum === "kapaniyor") {
    return (
      <p role="status" className="mt-5 text-body-medium text-on-surface-variant">
        OAB Defteri kapanıyor…
      </p>
    );
  }
  return (
    <div className="mt-5 flex flex-col items-center gap-2">
      <Button icon="power_settings_new" onClick={() => void cik()}>
        Programdan çık
      </Button>
      {ileti && (
        <p role="alert" className="text-body-small text-error">
          {ileti}
        </p>
      )}
    </div>
  );
}
