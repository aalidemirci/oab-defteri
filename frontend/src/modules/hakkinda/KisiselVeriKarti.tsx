// Hakkında → Kişisel Veri: kişisel veri aydınlatma metninin (E04) belge kartı — görev bölümü evrakının
// kartının kalıbı (`evrak/EvrakKarti`; plan F2 10. adım). Her rol geçerli kaydı görür ve PDF ya da Word
// olarak kaydeder (basım okumadır; `BASIM` satırı backend'de okuma rolünde de yazılır). "Belgeyi
// oluştur" yalnız `aydinlatma_metni_uretme`'de (program yöneticisi; tasarım §9.6 E04 "Üreten") ve
// Okul Bilgileri'nde veri sorumlusu girilmişken çizilir. Veri sorumlusu boşken belge oluşturulmaz ve
// kaydedilmez (sert; plan F2 §9 S6 (iv), KE-20): kart uyarıyı ve Okul Bilgileri'ne bağlantıyı gösterir,
// basım düğmelerini çizmez (sunucu da 400 döner). Durum okunmadan ya da okunamadığında "Belgeyi
// oluştur" çizilmez. Her basımda geçerli uyarılar (onaylı ekran notu, KVKK md. 6/3'ün bendi; K9 açıkken
// bağışçı numarasının hukuki sebebi) sunucudan gelir ve kartta durur; belgeye basılmaz.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { saveBlob } from "../../lib/download";
import { formatDateTime } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import Button from "../../ui/Button";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { evrakApi, evrakYedekDosyaAdi } from "../evrak/api";
import type { EvrakBicimi } from "../evrak/api";
import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  E04_ADI,
  EVRAK_KAYDEDILEMEDI,
  EVRAK_OKUNAMADI,
  EVRAK_OLUSTURULAMADI,
  EVRAK_OLUSTURULDU,
  EVRAK_YOK,
  HAZIRLANIYOR,
  OLUSTURULUYOR,
  PDF_KAYDEDILDI,
  WORD_KAYDEDILDI,
  sonOlusturmaMetni,
} from "../evrak/metinler";
import { OKUL_BILGILERI_ADRESI } from "../kisiler/AydinlatmaMetni";
import { useYetki } from "../oturum/yetki";
import { aydinlatmaApi } from "./api";
import type { AydinlatmaDurumu } from "./api";
import {
  E04_VERI_SORUMLUSU_GIRILMEDI,
  OKUL_BILGILERI_BAGLANTISI,
  TEYIT_BASLIGI,
  TEYIT_NOTU,
} from "./metinler";

export default function KisiselVeriKarti() {
  const snackbar = useSnackbar();
  const yetki = useYetki();
  // undefined: durum henüz okunmadı; null: okunamadı.
  const [durum, setDurum] = useState<AydinlatmaDurumu | null | undefined>(undefined);
  const [calisan, setCalisan] = useState<"uret" | EvrakBicimi | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const oku = useCallback(() => {
    aydinlatmaApi
      .durum()
      .then(setDurum)
      .catch(() => setDurum(null));
  }, []);

  useEffect(oku, [oku]);

  const kayit = durum?.evrak ?? null;
  const girildi = durum?.veri_sorumlusu_girildi ?? false;

  const uret = async () => {
    setCalisan("uret");
    setHata(null);
    try {
      const sonuc = await aydinlatmaApi.uret();
      setDurum((onceki) =>
        onceki == null
          ? onceki
          : { ...onceki, evrak: sonuc.evrak, basim_uyarilari: sonuc.uyarilar },
      );
      snackbar.success(EVRAK_OLUSTURULDU);
    } catch (e) {
      setHata(hataOku(e, EVRAK_OLUSTURULAMADI));
    } finally {
      setCalisan(null);
    }
  };

  const kaydet = async (bicim: EvrakBicimi) => {
    if (kayit === null) return;
    setCalisan(bicim);
    setHata(null);
    try {
      const { blob, ad } = await evrakApi.dosya(kayit.id, bicim);
      const sonuc = await saveBlob(blob, ad ?? evrakYedekDosyaAdi(kayit, bicim));
      if (sonuc === "hata") setHata(hataOku(null, DOSYA_YAZILAMADI_ILETISI));
      else if (sonuc !== "iptal")
        snackbar.success(bicim === "pdf" ? PDF_KAYDEDILDI : WORD_KAYDEDILDI);
    } catch (e) {
      setHata(hataOku(e, EVRAK_KAYDEDILEMEDI));
    } finally {
      setCalisan(null);
    }
  };

  const bicimVar = (bicim: string) => kayit?.bicimler.includes(bicim) ?? false;
  const basilir = kayit !== null && girildi;
  const uretilir = durum != null && girildi && yetki.acik("aydinlatma_metni_uretme");

  return (
    <section
      aria-label={E04_ADI}
      className="space-y-3 rounded-shape-md border border-outline-variant p-[var(--od-panel-padding)]"
    >
      <div className="flex items-start gap-3">
        <Icon name="description" size="lg" className="mt-0.5 shrink-0 text-primary" />
        <div className="min-w-0 flex-1 space-y-1">
          <h3 className="break-words text-title-small text-on-surface">{E04_ADI}</h3>
          <p className="text-body-medium text-on-surface-variant">
            {durum === null
              ? EVRAK_OKUNAMADI
              : durum === undefined
                ? null
                : kayit === null
                  ? EVRAK_YOK
                  : sonOlusturmaMetni(formatDateTime(kayit.uretim_zamani), kayit.surum)}
          </p>
        </div>
      </div>

      {durum != null && !girildi && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-3 py-2 text-on-tertiary-container"
        >
          <Icon name="warning" size="lg" className="mt-0.5 shrink-0" />
          <div className="min-w-0 space-y-1 text-body-medium">
            <p>{E04_VERI_SORUMLUSU_GIRILMEDI}</p>
            <Link
              to={OKUL_BILGILERI_ADRESI}
              className="inline-flex text-label-large text-primary underline underline-offset-2"
            >
              {OKUL_BILGILERI_BAGLANTISI}
            </Link>
          </div>
        </div>
      )}

      {hata && <ErrorBand hata={hata} />}

      {durum != null && durum.basim_uyarilari.length > 0 && (
        <div
          role="status"
          className="space-y-1 rounded-shape-sm bg-surface-container-high px-4 py-3 text-on-surface"
        >
          <p className="text-label-large">{TEYIT_BASLIGI}</p>
          <ul className="list-disc space-y-0.5 pl-5 text-body-medium">
            {durum.basim_uyarilari.map((u) => (
              <li key={u} className="break-words">
                {u}
              </li>
            ))}
          </ul>
          <p className="text-body-small text-on-surface-variant">{TEYIT_NOTU}</p>
        </div>
      )}

      <div className="flex flex-wrap justify-end gap-2">
        {basilir && bicimVar("PDF") && (
          <Button
            variant="tonal"
            icon="picture_as_pdf"
            disabled={calisan !== null}
            onClick={() => void kaydet("pdf")}
          >
            {calisan === "pdf" ? HAZIRLANIYOR : DUGME_PDF}
          </Button>
        )}
        {basilir && bicimVar("DOCX") && (
          <Button
            variant="tonal"
            icon="article"
            disabled={calisan !== null}
            onClick={() => void kaydet("docx")}
          >
            {calisan === "docx" ? HAZIRLANIYOR : DUGME_WORD}
          </Button>
        )}
        {uretilir && (
          <Button icon="note_add" disabled={calisan !== null} onClick={() => void uret()}>
            {calisan === "uret"
              ? OLUSTURULUYOR
              : kayit === null
                ? DUGME_OLUSTUR
                : DUGME_YENIDEN_OLUSTUR}
          </Button>
        )}
      </div>
    </section>
  );
}
