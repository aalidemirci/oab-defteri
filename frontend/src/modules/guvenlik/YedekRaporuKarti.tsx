// "Yedek Raporu" kartı (program belgesi, tasarım §9.7; kullanıcı kararı 04.11.2026 "Yedek raporu";
// kart başlığı belge adıdır, sözlük §2-§3). Tek sayfa, kişisiz PDF: bu bilgisayardaki yedekler,
// yedekleri açan kurtarma anahtarları, kenara alınan önceki veritabanları, son şifreli yedek,
// hatırlatma süresi. Yalnız program yöneticisi basar (yetenek `guvenlik`; kartı `GuvenlikAyarlari`
// süzer). Dosyası saklanmaz, basımı `BASIM` satırıdır; adı sunucu kurar, ekranın kurduğu ad yalnız
// o ad okunamazsa kullanılır (sözlük §3 "Kaydedilen dosya adı"). Satır PDF üretilince yazılır:
// kaydetme penceresinde iptal satırı geri almaz, bildirim yalnız dosya kaydedilince çıkar.

import { useState } from "react";

import { dosyaAdi, saveBlob } from "../../lib/download";
import { formatDate, todayIso } from "../../lib/format";
import { DOSYA_YAZILAMADI_ILETISI } from "../../lib/metinler";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { oturumHataMetni } from "../oturum/hatalar";
import { guvenlikApi } from "./api";
import {
  YEDEK_RAPORU_ADI,
  YEDEK_RAPORU_HAZIRLANAMADI,
  YEDEK_RAPORU_KAYDEDILDI,
  YEDEK_RAPORU_METNI,
} from "./metinler";

export default function YedekRaporuKarti() {
  const snackbar = useSnackbar();
  const [calisiyor, setCalisiyor] = useState(false);

  async function kaydet() {
    setCalisiyor(true);
    try {
      const { blob, ad } = await guvenlikApi.yedekRaporu();
      const sonuc = await saveBlob(
        blob,
        ad ?? dosyaAdi([YEDEK_RAPORU_ADI, formatDate(todayIso())], "pdf"),
      );
      if (sonuc === "hata") snackbar.error(DOSYA_YAZILAMADI_ILETISI);
      else if (sonuc !== "iptal") snackbar.success(YEDEK_RAPORU_KAYDEDILDI);
    } catch (error) {
      snackbar.error(oturumHataMetni(error, YEDEK_RAPORU_HAZIRLANAMADI));
    } finally {
      setCalisiyor(false);
    }
  }

  return (
    <Card className="p-6">
      <div className="mb-2 flex items-center gap-3">
        <Icon name="picture_as_pdf" className="text-primary" />
        <h2 className="text-title-large text-on-surface">{YEDEK_RAPORU_ADI}</h2>
      </div>
      <p className="text-body-medium text-on-surface-variant">{YEDEK_RAPORU_METNI}</p>
      <div className="mt-4">
        <Button variant="tonal" icon="download" onClick={() => void kaydet()} disabled={calisiyor}>
          {calisiyor ? "Hazırlanıyor…" : "PDF olarak kaydet"}
        </Button>
      </div>
    </Card>
  );
}
