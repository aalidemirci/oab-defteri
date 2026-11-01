// "Kurtarma Anahtarını Yenile" kartı (aile iskeletinden; OAB'deki yenileme plan §2.2
// adım 3, tasarım §13 D14).
//
// Anahtar kurulumda kaydedilemediyse (pencere kapandı, program çöktü) ya da sonradan
// kaybolduysa yenisi üretilir. Onay diyaloğu oturumdaki hesabın KENDİ parolasını ister
// (başlık soru, gövde sonuç — docs/sozluk.md §3; başka hesabın parolası geçmez, plan
// F1b-1 "Parola ve hatalı deneme"); backend parolayı o hesabın sarmalına karşı doğrular,
// aynı veri anahtarını YENİ kurtarma anahtarıyla sarmalar (no'su bir artar), önceki
// güvenlik dosyasını "guvenlik-arsiv" adıyla saklar ve yeni anahtarı BİR KEZ döndürür.
// Yenilemeyi yalnız program yöneticisinin yapması rol kapısıyla 2. adımda gelir (tasarım
// TK9; bugün yalnız program yöneticisi hesabı açılabilir).
//
// Yeni anahtar (ve kimliği) bileşen durumunda DEĞİL, rota ağacının dışındaki modül
// belleğinde bekletilir (`bekleyenAnahtar`): sayfa gezinmeyle sökülse de kaybolmaz
// (kilitlenme pencereyi yeniden yükler ve anahtarı siler; Kilitle önce sorar); sihirbaz
// ve Güvenlik ekranı onu `KurtarmaAnahtariPaneli` ile saklatıp doğrulatır. Metinler
// dürüsttür: eski yedeklerin eski anahtarla açıldığını ve yenilemenin ele geçmiş anahtara
// karşı koruma olmadığını söyler.
// Pencere açılınca parola alanı odaktadır (`ui/Dialog` `initialFocusRef`).

import { useRef, useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "../../lib/api";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Dialog from "../../ui/Dialog";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { guvenlikApi } from "./api";
import { bekleyenKurtarmaAnahtariniYaz } from "./bekleyenAnahtar";
import { guncelKurtarmaKimligi } from "./kurtarma";
import {
  ELE_GECMIS_ANAHTAR_METNI,
  ESKI_YEDEK_METNI,
  YENILEME_METNI,
  YENILEME_SONUCU_METNI,
} from "./metinler";

export default function KurtarmaAnahtariniYenileKarti({
  aciklama = YENILEME_METNI,
  onYenilendi,
}: {
  /** Kartın açıklaması (sihirbazda "kaydedemediyseniz yenisini üretin" vurgusuyla). */
  aciklama?: string;
  /** Yeni anahtar bekletildikten sonra çağrılır (durum tazelemesi için). */
  onYenilendi?: () => void;
}) {
  const snackbar = useSnackbar();
  const [acik, setAcik] = useState(false);
  const parolaAlani = useRef<HTMLInputElement>(null);
  const [parola, setParola] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);

  function kapat() {
    setAcik(false);
    setParola("");
    setHata(null);
  }

  async function yenile(e: FormEvent) {
    e.preventDefault();
    setHata(null);
    setCalisiyor(true);
    try {
      const sonuc = await guvenlikApi.kurtarmaAnahtariniYenile(parola);
      bekleyenKurtarmaAnahtariniYaz(sonuc.recovery_key, guncelKurtarmaKimligi(sonuc));
      kapat();
      snackbar.success("Yeni kurtarma anahtarı üretildi. Saklayıp doğrulayın.");
      onYenilendi?.();
    } catch (err) {
      setHata(err instanceof ApiError ? err.message : "Kurtarma anahtarı yenilenemedi.");
    } finally {
      setCalisiyor(false);
    }
  }

  return (
    <Card className="p-6">
      <div className="mb-2 flex items-center gap-3">
        <Icon name="autorenew" className="text-primary" />
        <h2 className="text-title-large text-on-surface">Kurtarma Anahtarını Yenile</h2>
      </div>
      <p className="text-body-medium text-on-surface-variant">{aciklama}</p>
      <div className="mt-4">
        <Button variant="tonal" icon="autorenew" onClick={() => setAcik(true)}>
          Kurtarma anahtarını yenile
        </Button>
      </div>

      <Dialog
        open={acik}
        onClose={kapat}
        title="Kurtarma anahtarı yenilensin mi?"
        initialFocusRef={parolaAlani}
      >
        <form onSubmit={yenile} className="flex flex-col gap-4">
          <p className="text-body-medium text-on-surface">{YENILEME_SONUCU_METNI}</p>
          <p className="text-body-medium text-on-surface-variant">{ESKI_YEDEK_METNI}</p>
          <p className="text-body-small text-on-surface-variant">{ELE_GECMIS_ANAHTAR_METNI}</p>
          <TextField
            ref={parolaAlani}
            label="Parolanız"
            type="password"
            value={parola}
            onChange={(e) => setParola(e.target.value)}
            autoComplete="current-password"
            helperText="Bu oturumu açan hesabın parolası."
            error={hata ?? undefined}
            required
          />
          <div className="flex justify-end gap-2">
            <Button variant="text" type="button" onClick={kapat}>
              Vazgeç
            </Button>
            <Button type="submit" icon="autorenew" disabled={calisiyor || !parola}>
              {calisiyor ? "Üretiliyor…" : "Yeni anahtar üret"}
            </Button>
          </div>
        </form>
      </Dialog>
    </Card>
  );
}
