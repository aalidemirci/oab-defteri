// "Boşta Kilit Süresi" kartı — Ayarlar → Güvenlik (tasarım TK14, D11; plan F1b-1
// "Oturum"). Program bu kadar dakika işlem yapılmazsa kendiliğinden kilitlenir;
// süre 3-30 dakikadır, varsayılanı 10'dur (`SchoolConfig.idle_lock_minutes`; uç
// `GET|PUT security/idle-lock/`, gövde `{dakika}`). Mutlak oturum süresi yoktur.
//
// * Kural backend'dedir; aralık ve tam sayı burada da ÖNCEDEN denetlenir, iletiler
//   backend'inkiyle birebirdir (`views_oturum.BostaKilitSuresiSerializer`).
// * Kayıt pencereyi yeniden YÜKLEMEZ; oturum özeti hemen yeniden okunur ki üst
//   çubuktaki geri sayım ve ipucu yeni süreyi göstersin (`eylemler.bostaKilitSuresiniDegistir`).
// * Kurulum sihirbazı bitene dek süre işlemez (tasarım §13 D15); metin bunu söyler.
// * Yalnız açık oturumda okunur ve yazılır (kilitliyken uç 423 döner; bu ekran zaten
//   açık oturumdadır). Süreyi her rol okur, yalnız `bosta_sure_yazma` yeteneği yazar (plan
//   F1b-2 "Ayarlar"; `yazabilir`, Güvenlik sekmesi verir): öteki rollerde alan ve "Kaydet"
//   yerine "Boşta kilit süresi N dakika." yazar.

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "../../lib/api";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { oturumApi } from "../oturum/api";
import { bostaKilitSuresiniDegistir } from "../oturum/eylemler";

/** Kartın adı (docs/sozluk.md §4.6). */
export const BOSTA_KILIT_KARTI_BASLIGI = "Boşta Kilit Süresi";

export const BOSTA_DK_EN_AZ = 3;
export const BOSTA_DK_EN_COK = 30;
export const BOSTA_DK_VARSAYILAN = 10;

// Backend iletileriyle BİREBİR (`views_oturum.BostaKilitSuresiSerializer`).
export const BOSTA_DK_ARALIK_ILETISI = `Boşta kilit süresi ${BOSTA_DK_EN_AZ} ile ${BOSTA_DK_EN_COK} dakika arasında olmalıdır.`;
export const BOSTA_DK_TAM_SAYI_ILETISI = "Boşta kilit süresi tam sayı (dakika) olmalıdır.";
export const BOSTA_DK_BOS_ILETISI = "Boşta kilit süresini dakika olarak girin.";

/**
 * Tam sayı biçimi — DRF `IntegerField` ile aynı: sondaki ".0" kabul edilir ("15.0" → 15),
 * kesirli değer ("7.5") edilmez. Ön denetim backend'den katı olmasın (otorite backend).
 */
const TAM_SAYI = /^-?\d+(\.0*)?$/;

/** Alandaki metnin sorunu (backend sırasıyla) ya da null. */
export function bostaDakikaSorunu(deger: string): string | null {
  const metin = deger.trim();
  if (metin === "") return BOSTA_DK_BOS_ILETISI;
  if (!TAM_SAYI.test(metin)) return BOSTA_DK_TAM_SAYI_ILETISI;
  const dakika = Number(metin);
  return dakika < BOSTA_DK_EN_AZ || dakika > BOSTA_DK_EN_COK ? BOSTA_DK_ARALIK_ILETISI : null;
}

/** Salt okur satırı (sözlük §1 "Kilit ve çıkış"). */
export function bostaSuresiCumlesi(dakika: number): string {
  return `Boşta kilit süresi ${dakika} dakika.`;
}

export default function BostaKilitSuresiKarti({
  yazabilir,
}: {
  /** Süreyi yazabilir mi (`bosta_sure_yazma`)? Değilse yalnız okunur. */
  yazabilir: boolean;
}) {
  const snackbar = useSnackbar();
  const [kayitli, setKayitli] = useState<number | null>(null);
  const [okunamadi, setOkunamadi] = useState(false);
  const [deger, setDeger] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);

  useEffect(() => {
    let iptal = false;
    oturumApi
      .bostaKilitSuresi()
      .then(({ dakika }) => {
        if (iptal) return;
        setKayitli(dakika);
        setDeger(String(dakika));
      })
      .catch(() => {
        if (!iptal) setOkunamadi(true);
      });
    return () => {
      iptal = true;
    };
  }, []);

  async function kaydet(e: FormEvent) {
    e.preventDefault();
    const sorun = bostaDakikaSorunu(deger);
    setHata(sorun);
    if (sorun) return;
    setCalisiyor(true);
    try {
      const { dakika } = await bostaKilitSuresiniDegistir(Number(deger.trim()));
      setKayitli(dakika);
      setDeger(String(dakika));
      snackbar.success(`Boşta kilit süresi ${dakika} dakika olarak kaydedildi.`);
    } catch (err) {
      setHata(err instanceof ApiError ? err.message : "Boşta kilit süresi kaydedilemedi.");
    } finally {
      setCalisiyor(false);
    }
  }

  return (
    <Card className="p-6">
      <div className="mb-2 flex items-center gap-3">
        <Icon name="timer" className="text-primary" />
        <h2 className="text-title-large text-on-surface">{BOSTA_KILIT_KARTI_BASLIGI}</h2>
      </div>
      <p className="text-body-medium text-on-surface-variant">
        Program bu kadar dakika işlem yapılmazsa kendiliğinden kilitlenir; kilidi herkes kendi
        hesabıyla açar. Süre {BOSTA_DK_EN_AZ} ile {BOSTA_DK_EN_COK} dakika arasındadır, varsayılanı{" "}
        {BOSTA_DK_VARSAYILAN} dakikadır. Kurulum sihirbazı bitene dek süre işlemez; uzun bir iş
        sürerken kilit iş bitince uygulanır.
      </p>
      {okunamadi ? (
        <p role="alert" className="mt-4 text-body-small text-error">
          Boşta kilit süresi okunamadı.
        </p>
      ) : kayitli === null ? (
        <SkeletonList rows={1} className="mt-4" />
      ) : !yazabilir ? (
        <p className="mt-4 text-body-large text-on-surface">{bostaSuresiCumlesi(kayitli)}</p>
      ) : (
        // `noValidate`: tarayıcının kendi (İngilizce olabilen) aralık balonu yerine
        // sözlüğe uyan ileti alanın altında çıksın.
        <form
          onSubmit={kaydet}
          noValidate
          className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-start"
        >
          <TextField
            className="sm:w-48"
            label="Boşta kilit süresi (dakika)"
            type="number"
            inputMode="numeric"
            min={BOSTA_DK_EN_AZ}
            max={BOSTA_DK_EN_COK}
            step={1}
            value={deger}
            onChange={(e) => setDeger(e.target.value)}
            error={hata ?? undefined}
            required
          />
          <Button
            type="submit"
            variant="tonal"
            icon="save"
            className="sm:mt-7"
            disabled={calisiyor || deger.trim() === String(kayitli)}
          >
            {calisiyor ? "Kaydediliyor…" : "Kaydet"}
          </Button>
        </form>
      )}
    </Card>
  );
}
