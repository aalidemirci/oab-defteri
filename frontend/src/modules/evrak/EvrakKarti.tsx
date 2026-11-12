// Görev bölümü ve temsilci evrakının kartı (E01 Organlar → Yönetim Kurulu, E02 Organlar → Denetleme
// Kurulu, E03 Temsilciler; plan F1c 10. adım notları, 11. adım). Her rol dönemin geçerli kaydını görür ve
// PDF ya da Word olarak kaydeder (basım okumadır; `BASIM` satırı backend'de okuma rolünde de yazılır).
// "Belgeyi oluştur" yalnız üretebilen rolde (`uretebilir`: E01 ve E03 `karar_taslagi_uretme`, E02
// `dk_gorev_bolumu_yazma`) ve birlik dönemi yazılabilirken çizilir; yeniden oluşturma yeni sürümdür.
// Liste okunmadan ya da okunamadığında düğme çizilmez ve durum satırı "Belge henüz oluşturulmadı."
// demez: kaydın varlığı bilinmez, kullanıcı bilmeden yeni sürüm üretmesin.
// Üretimin basım uyarıları kartta listelenir, belgeye basılmaz. Dönem kilidi (409 `donem_kapali`,
// `donem_salt_okur`) ortak bantla, dosya deposu iletileri (409 `evrak_dosyasi_yazilamadi`,
// `evrak_dosyasi_acilamadi`) ve parola kapısı hata bandıyla gösterilir (ileti sunucunundur).

import { useCallback, useEffect, useState } from "react";

import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import { saveBlob } from "../../lib/download";
import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { UyumHataBandi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { evrakApi, evrakYedekDosyaAdi } from "./api";
import type { EvrakBicimi, EvrakKaydi, EvrakKodu } from "./api";
import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  EVRAK_KAYDEDILEMEDI,
  EVRAK_OKUNAMADI,
  EVRAK_OLUSTURULAMADI,
  EVRAK_OLUSTURULDU,
  EVRAK_YOK,
  HAZIRLANIYOR,
  OLUSTURULUYOR,
  PDF_KAYDEDILDI,
  URETIM_UYARILARI_BASLIGI,
  URETIM_UYARILARI_NOTU,
  WORD_KAYDEDILDI,
  sonOlusturmaMetni,
} from "./metinler";

type Hata = { tur: "uyum"; hata: UyumHatasi } | { tur: "sayfa"; hata: SayfaHatasi };

function hataSinifla(e: unknown, yedek: string): Hata {
  const uyum = uyumHatasiOku(e);
  return uyum !== null ? { tur: "uyum", hata: uyum } : { tur: "sayfa", hata: hataOku(e, yedek) };
}

export default function EvrakKarti({
  donem,
  kod,
  baslik,
  aciklama,
  uretebilir,
}: {
  donem: number;
  kod: EvrakKodu;
  /** Belgenin adı (sözlük; kodu yüzeye çıkmaz). */
  baslik: string;
  aciklama?: string;
  /** "Belgeyi oluştur" çizilsin mi? (Üreten rol ve yazılabilir birlik dönemi.) */
  uretebilir: boolean;
}) {
  const snackbar = useSnackbar();
  // undefined: liste henüz okunmadı (durum satırı boş, "Belgeyi oluştur" çizilmez); null: kayıt yok.
  const [kayit, setKayit] = useState<EvrakKaydi | null | undefined>(undefined);
  const [okunamadi, setOkunamadi] = useState(false);
  const [uyarilar, setUyarilar] = useState<string[]>([]);
  const [calisan, setCalisan] = useState<"uret" | EvrakBicimi | null>(null);
  const [hata, setHata] = useState<Hata | null>(null);

  const oku = useCallback(() => {
    evrakApi
      .liste(donem)
      .then((liste) => {
        setKayit(liste.find((k) => k.kod === kod) ?? null);
        setOkunamadi(false);
      })
      .catch(() => setOkunamadi(true));
  }, [donem, kod]);

  useEffect(oku, [oku]);

  const uret = async () => {
    setCalisan("uret");
    setHata(null);
    try {
      const sonuc = await evrakApi.uret(donem, kod);
      setKayit(sonuc.evrak);
      setUyarilar(sonuc.uyarilar);
      snackbar.success(EVRAK_OLUSTURULDU);
    } catch (e) {
      setHata(hataSinifla(e, EVRAK_OLUSTURULAMADI));
    } finally {
      setCalisan(null);
    }
  };

  const kaydet = async (bicim: EvrakBicimi) => {
    if (kayit == null) return;
    setCalisan(bicim);
    setHata(null);
    try {
      const { blob, ad } = await evrakApi.dosya(kayit.id, bicim);
      const sonuc = await saveBlob(blob, ad ?? evrakYedekDosyaAdi(kayit, bicim));
      if (sonuc === "hata")
        setHata({ tur: "sayfa", hata: hataOku(null, DOSYA_YAZILAMADI_ILETISI) });
      else if (sonuc !== "iptal")
        snackbar.success(bicim === "pdf" ? PDF_KAYDEDILDI : WORD_KAYDEDILDI);
    } catch (e) {
      setHata(hataSinifla(e, EVRAK_KAYDEDILEMEDI));
    } finally {
      setCalisan(null);
    }
  };

  const bicimVar = (bicim: string) => kayit?.bicimler.includes(bicim) ?? false;

  return (
    <Card elevation={0} className="space-y-3 p-[var(--od-panel-padding)]">
      <div className="flex items-start gap-3">
        <Icon name="description" size="lg" className="mt-0.5 shrink-0 text-primary" />
        <div className="min-w-0 flex-1 space-y-1">
          <h2 className="break-words text-title-small text-on-surface">{baslik}</h2>
          {aciklama && <p className="text-body-small text-on-surface-variant">{aciklama}</p>}
          <p className="text-body-medium text-on-surface-variant">
            {okunamadi
              ? EVRAK_OKUNAMADI
              : kayit === undefined
                ? null
                : kayit === null
                  ? EVRAK_YOK
                  : sonOlusturmaMetni(formatDateTime(kayit.uretim_zamani), kayit.surum)}
          </p>
        </div>
      </div>

      {hata?.tur === "uyum" && <UyumHataBandi hata={hata.hata} />}
      {hata?.tur === "sayfa" && <ErrorBand hata={hata.hata} />}

      {uyarilar.length > 0 && (
        <div
          role="status"
          className="space-y-1 rounded-shape-sm bg-tertiary-container px-4 py-3 text-on-tertiary-container"
        >
          <p className="text-label-large">{URETIM_UYARILARI_BASLIGI}</p>
          <ul className="list-disc space-y-0.5 pl-5 text-body-medium">
            {uyarilar.map((u) => (
              <li key={u} className="break-words">
                {u}
              </li>
            ))}
          </ul>
          <p className="text-body-small">{URETIM_UYARILARI_NOTU}</p>
        </div>
      )}

      <div className="flex flex-wrap justify-end gap-2">
        {kayit != null && bicimVar("PDF") && (
          <Button
            variant="tonal"
            icon="picture_as_pdf"
            disabled={calisan !== null}
            onClick={() => void kaydet("pdf")}
          >
            {calisan === "pdf" ? HAZIRLANIYOR : DUGME_PDF}
          </Button>
        )}
        {kayit != null && bicimVar("DOCX") && (
          <Button
            variant="tonal"
            icon="article"
            disabled={calisan !== null}
            onClick={() => void kaydet("docx")}
          >
            {calisan === "docx" ? HAZIRLANIYOR : DUGME_WORD}
          </Button>
        )}
        {uretebilir && kayit !== undefined && !okunamadi && (
          <Button icon="note_add" disabled={calisan !== null} onClick={() => void uret()}>
            {calisan === "uret"
              ? OLUSTURULUYOR
              : kayit === null
                ? DUGME_OLUSTUR
                : DUGME_YENIDEN_OLUSTUR}
          </Button>
        )}
      </div>
    </Card>
  );
}
