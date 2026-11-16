// Genel kurulun belge kartları (tasarım §9.5, §9.6; plan F2 §4, §6.1; F1c'nin `evrak/EvrakKarti` kalıbı).
// Kartlar katalogdan çizilir: E05-E13 ve E64 (E04 Hakkında'da, E14 Genel Bakış'tadır). Her rol geçerli
// kaydı görür ve kayıtlı biçimleriyle kaydeder (basım okumadır; `BASIM` satırı sunucuda). "Belgeyi
// oluştur" yalnız oturumdaki rolün üretebildiği belgede çizilir (`oturum.uretilebilir_belgeler`; sunucu
// tasarım §9.6'nın "Üreten"ine ve E05'te çağırana göre söyler); Denetleme Kurulunun çağrısında çağrı
// yazısı kendi ucundan üretilir. Toplantı başına belgelerde (E05, E06, E64) toplantı, iki kipli
// belgelerde (E07, E08) kişisiz kip seçilir; VELİ ADLI kip yalnız `kisisel_veri_ciktisi`'nde ayrı
// düğmelerle tek istekte üretilip verilir, saklanmaz (U15). Resmî yazıda (E12) muhatap il ya da ilçe
// millî eğitim müdürlüğünden seçilir ve basımdan önce düzenlenir (U20, S11 (a)); yazı kendiliğinden
// evrak defterine kaydedilmez: öneri görülüp onaylanır (`evrak_kaydi`). Üretimin basım uyarıları kartta
// durur, belgeye basılmaz.

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatDateTime } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import {
  DUGME_EXCEL,
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  EVRAK_KAYDEDILEMEDI,
  EVRAK_OKUNAMADI,
  EVRAK_OLUSTURULAMADI,
  EVRAK_OLUSTURULDU,
  EVRAK_YOK,
  EXCEL_KAYDEDILDI,
  HAZIRLANIYOR,
  OLUSTURULUYOR,
  PDF_KAYDEDILDI,
  URETIM_UYARILARI_BASLIGI,
  URETIM_UYARILARI_NOTU,
  WORD_KAYDEDILDI,
  sonOlusturmaMetni,
} from "../evrak/metinler";
import { gelenGidenApi } from "../gelen-giden-evrak/api";
import type { GidenKayitOnerisi } from "../gelen-giden-evrak/api";
import {
  ALAN_DIS_SAYI,
  ALAN_KARSI_TARAF,
  ALAN_KAYIT_NO,
  ALAN_KONU,
  ALAN_TARIH,
} from "../gelen-giden-evrak/metinler";
import { UyumHataBandi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { genelKurulApi } from "./api";
import type { GenelKurul, GkBicim, GkEvrakKaydi, Katalog, KatalogSatiri, Toplanti } from "./api";
import {
  ADLI_CIKTI_ACIKLAMASI,
  ADLI_CIKTI_BASLIGI,
  ADLI_CIKTI_KAYDEDILDI,
  ADLI_CIKTI_YAZILAMADI,
  ALAN_BELGE_TOPLANTISI,
  ALAN_MUHATAP,
  ALAN_MUHATAP_BIRIM,
  ALAN_MUHATAP_IDARE,
  BELGELER_ACIKLAMASI,
  BELGELER_BASLIGI,
  DUGME_ADLI_EXCEL,
  DUGME_ADLI_PDF,
  DUGME_ADLI_WORD,
  DUGME_EVRAK_KAYDET,
  DUGME_EVRAK_KAYDI,
  DUGME_WEB,
  GIDEN_KAYDEDILDI,
  GIDEN_KAYDEDILEMEDI,
  EVRAK_KAYDI_ACIKLAMASI,
  EVRAK_KAYDI_BASLIGI,
  EVRAK_KAYDI_OKUNAMADI,
  KATALOG_OKUNAMADI,
  MUHATAP_IL,
  MUHATAP_ILCE,
  MUHATAP_YARDIMI,
  TOPLANTI_TR,
  SAYI_GECERSIZ,
  WEB_KAYDEDILDI,
  adliKayitMetni,
  kayitliMetni,
} from "./metinler";
import { SayiAlani, YazmaPenceresi, dosyayiKaydet, sayiOku } from "./ortak";

/** Genel Kurul ekranındaki belgeler (katalog sırasıyla; E04 ve E14 burada değil). */
export const GK_BELGELERI = [
  "E05",
  "E06",
  "E07",
  "E08",
  "E64",
  "E09",
  "E10",
  "E11",
  "E12",
  "E13",
] as const;

type Hata = { tur: "uyum"; hata: UyumHatasi } | { tur: "sayfa"; hata: SayfaHatasi };

function hataSinifla(e: unknown, yedek: string): Hata {
  const uyum = uyumHatasiOku(e);
  return uyum !== null ? { tur: "uyum", hata: uyum } : { tur: "sayfa", hata: hataOku(e, yedek) };
}

const BICIM_DUGMESI: Record<
  string,
  { bicim: GkBicim; etiket: string; ikon: string; basari: string }
> = {
  PDF: { bicim: "pdf", etiket: DUGME_PDF, ikon: "picture_as_pdf", basari: PDF_KAYDEDILDI },
  DOCX: { bicim: "docx", etiket: DUGME_WORD, ikon: "article", basari: WORD_KAYDEDILDI },
  XLSX: { bicim: "xlsx", etiket: DUGME_EXCEL, ikon: "table_view", basari: EXCEL_KAYDEDILDI },
  HTML: { bicim: "html", etiket: DUGME_WEB, ikon: "language", basari: WEB_KAYDEDILDI },
};

// Katalog `adli_bicimler`'i sunucunun biçim adlarıyla (büyük harf) verir; uç küçük harf bekler.
const ADLI_DUGMESI: Record<
  string,
  { bicim: "pdf" | "docx" | "xlsx"; etiket: string; ikon: string }
> = {
  PDF: { bicim: "pdf", etiket: DUGME_ADLI_PDF, ikon: "picture_as_pdf" },
  DOCX: { bicim: "docx", etiket: DUGME_ADLI_WORD, ikon: "article" },
  XLSX: { bicim: "xlsx", etiket: DUGME_ADLI_EXCEL, ikon: "table_view" },
};

function EvrakKaydiPenceresi({ kayit, onKapat }: { kayit: GkEvrakKaydi; onKapat: () => void }) {
  const snackbar = useSnackbar();
  const [oneri, setOneri] = useState<GidenKayitOnerisi | null>(null);
  const [okunamadi, setOkunamadi] = useState<SayfaHatasi | null>(null);
  const [tarih, setTarih] = useState("");
  const [karsi, setKarsi] = useState("");
  const [konu, setKonu] = useState("");
  const [disSayi, setDisSayi] = useState("");
  const [no, setNo] = useState("");
  const [noHatasi, setNoHatasi] = useState<string | undefined>(undefined);

  useEffect(() => {
    let iptal = false;
    gelenGidenApi
      .gidenOnerisi(kayit.id)
      .then((o) => {
        if (iptal) return;
        setOneri(o);
        setTarih(o.tarih);
        setKarsi(o.counterparty);
        setKonu(o.subject);
        setNo(o.onerilen_no === null ? "" : String(o.onerilen_no));
      })
      .catch((e: unknown) => {
        if (!iptal) setOkunamadi(hataOku(e, EVRAK_KAYDI_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [kayit.id]);

  return (
    <YazmaPenceresi
      baslik={EVRAK_KAYDI_BASLIGI}
      dugme={DUGME_EVRAK_KAYDET}
      yedekHata={GIDEN_KAYDEDILEMEDI}
      baglam={`genel_kurul.giden_kayit.${kayit.id}`}
      onKapat={onKapat}
      dogrula={() => {
        // Rakam olmayan numara sessizce sıradaki numaraya dönmesin (gelen-giden kayıt penceresi gibi).
        const gecersiz = sayiOku(no) === "gecersiz";
        setNoHatasi(gecersiz ? SAYI_GECERSIZ : undefined);
        return oneri !== null && oneri.kayitli === null && !gecersiz;
      }}
      onGonder={async (ek) => {
        await gelenGidenApi.gidenKaydet(kayit.id, {
          tarih,
          counterparty: karsi.trim(),
          subject: konu.trim(),
          external_ref: disSayi.trim(),
          record_no: (() => {
            const okunan = sayiOku(no);
            return typeof okunan === "number" && okunan > 0 ? okunan : null;
          })(),
          ...ek,
        });
        snackbar.success(GIDEN_KAYDEDILDI);
        onKapat();
      }}
      ikon="move_to_inbox"
    >
      <p className="text-body-medium text-on-surface-variant">{EVRAK_KAYDI_ACIKLAMASI}</p>
      {okunamadi && <ErrorBand hata={okunamadi} />}
      {oneri?.kayitli && (
        <p role="status" className="text-body-medium text-on-surface">
          {kayitliMetni(oneri.kayitli.yil, oneri.kayitli.kayit_no)}
        </p>
      )}
      {oneri && oneri.kayitli === null && (
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField
            label={ALAN_TARIH}
            type="date"
            value={tarih}
            onChange={(e) => setTarih(e.target.value)}
          />
          <SayiAlani etiket={ALAN_KAYIT_NO} deger={no} onDegis={setNo} hata={noHatasi} />
          <TextField
            label={ALAN_KARSI_TARAF}
            value={karsi}
            maxLength={1000}
            onChange={(e) => setKarsi(e.target.value)}
          />
          <TextField
            label={ALAN_KONU}
            value={konu}
            maxLength={1000}
            onChange={(e) => setKonu(e.target.value)}
          />
          <TextField
            label={ALAN_DIS_SAYI}
            value={disSayi}
            maxLength={64}
            onChange={(e) => setDisSayi(e.target.value)}
          />
        </div>
      )}
    </YazmaPenceresi>
  );
}

function BelgeKarti({
  kurul,
  satir,
  kayitlar,
  katalog,
  onUretildi,
  adliAcik,
  evrakKaydiAcik,
}: {
  kurul: GenelKurul;
  satir: KatalogSatiri;
  kayitlar: GkEvrakKaydi[] | null;
  katalog: Katalog;
  onUretildi: () => void;
  adliAcik: boolean;
  evrakKaydiAcik: boolean;
}) {
  const snackbar = useSnackbar();
  const [toplanti, setToplanti] = useState<Toplanti>(
    kurul.held_at_meeting === "IKINCI" ? "IKINCI" : "BIRINCI",
  );
  const [muhatapSecimi, setMuhatapSecimi] = useState<"IL" | "ILCE">(katalog.varsayilan_muhatap);
  const [idare, setIdare] = useState(katalog.muhatap_onerileri[katalog.varsayilan_muhatap].idare);
  const [birim, setBirim] = useState(katalog.muhatap_onerileri[katalog.varsayilan_muhatap].birim);
  const [uyarilar, setUyarilar] = useState<string[]>([]);
  const [calisan, setCalisan] = useState<string | null>(null);
  const [hata, setHata] = useState<Hata | null>(null);
  const [kayitPenceresi, setKayitPenceresi] = useState(false);

  const kip = satir.kipler.length > 0 ? "KISISIZ" : "";
  const kayit =
    kayitlar === null
      ? undefined
      : (kayitlar.find(
          (k) =>
            k.kod === satir.kod &&
            !k.kisi_listesi &&
            (k.kip || "") === kip &&
            (k.toplanti || "") === (satir.toplantili ? toplanti : ""),
        ) ?? null);
  const adliKayit = kayitlar?.find((k) => k.kod === satir.kod && k.kisi_listesi) ?? null;
  const dkYolu = satir.kod === "E05" && kurul.called_by === "DENETLEME_KURULU";
  const uretebilir = kurul.oturum.uretilebilir_belgeler.includes(satir.kod) && kayit !== undefined;

  const uret = async () => {
    setCalisan("uret");
    setHata(null);
    try {
      const sonuc = dkYolu
        ? await genelKurulApi.dkCagriYazisi(kurul.id, toplanti)
        : await genelKurulApi.evrakUret(kurul.id, satir.kod, {
            kip,
            toplanti: satir.toplantili ? toplanti : "",
            ...(satir.muhatapli
              ? { muhatap_secimi: muhatapSecimi, muhatap_idare: idare, muhatap_birim: birim }
              : {}),
          });
      setUyarilar(sonuc.uyarilar);
      snackbar.success(EVRAK_OLUSTURULDU);
      onUretildi();
    } catch (e) {
      setHata(hataSinifla(e, EVRAK_OLUSTURULAMADI));
    } finally {
      setCalisan(null);
    }
  };

  const kaydet = async (bicim: string) => {
    if (kayit == null) return;
    const d = BICIM_DUGMESI[bicim];
    setCalisan(bicim);
    setHata(null);
    try {
      const { blob, ad } = await genelKurulApi.evrakDosyasi(kayit.id, d.bicim);
      await dosyayiKaydet(blob, ad ?? `${satir.ad}.${d.bicim}`, d.basari, snackbar);
    } catch (e) {
      setHata(hataSinifla(e, EVRAK_KAYDEDILEMEDI));
    } finally {
      setCalisan(null);
    }
  };

  const adli = async (bicim: "pdf" | "docx" | "xlsx") => {
    setCalisan(`adli-${bicim}`);
    setHata(null);
    try {
      const { blob, ad } = await genelKurulApi.adliEvrak(kurul.id, satir.kod, bicim, "");
      await dosyayiKaydet(blob, ad ?? `${satir.ad}.${bicim}`, ADLI_CIKTI_KAYDEDILDI, snackbar);
      onUretildi();
    } catch (e) {
      setHata(hataSinifla(e, ADLI_CIKTI_YAZILAMADI));
    } finally {
      setCalisan(null);
    }
  };

  const muhatabiSec = (anahtar: "IL" | "ILCE") => {
    setMuhatapSecimi(anahtar);
    setIdare(katalog.muhatap_onerileri[anahtar].idare);
    setBirim(katalog.muhatap_onerileri[anahtar].birim);
  };

  return (
    <Card elevation={0} className="space-y-3 p-[var(--od-panel-padding)]">
      <div className="flex items-start gap-3">
        <Icon name="description" size="lg" className="mt-0.5 shrink-0 text-primary" />
        <div className="min-w-0 flex-1 space-y-1">
          <h4 className="break-words text-title-small text-on-surface">{satir.ad}</h4>
          <p className="text-body-medium text-on-surface-variant">
            {kayitlar === null
              ? EVRAK_OKUNAMADI
              : kayit == null
                ? EVRAK_YOK
                : sonOlusturmaMetni(formatDateTime(kayit.uretim_zamani), kayit.surum)}
          </p>
        </div>
      </div>

      {satir.toplantili && (
        <Select
          className="max-w-xs"
          label={ALAN_BELGE_TOPLANTISI}
          value={toplanti}
          onChange={(e) => setToplanti(e.target.value as Toplanti)}
          options={(["BIRINCI", "IKINCI"] as const).map((t) => ({
            value: t,
            label: TOPLANTI_TR[t],
          }))}
        />
      )}
      {satir.muhatapli && uretebilir && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Select
            label={ALAN_MUHATAP}
            value={muhatapSecimi}
            onChange={(e) => muhatabiSec(e.target.value as "IL" | "ILCE")}
            options={[
              { value: "ILCE", label: MUHATAP_ILCE },
              { value: "IL", label: MUHATAP_IL },
            ]}
          />
          <TextField
            label={ALAN_MUHATAP_IDARE}
            value={idare}
            maxLength={160}
            onChange={(e) => setIdare(e.target.value)}
            helperText={MUHATAP_YARDIMI}
          />
          <TextField
            label={ALAN_MUHATAP_BIRIM}
            value={birim}
            maxLength={160}
            onChange={(e) => setBirim(e.target.value)}
          />
        </div>
      )}

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
        {kayit != null &&
          kayit.bicimler
            .filter((b) => b in BICIM_DUGMESI)
            .map((b) => (
              <Button
                key={b}
                variant="tonal"
                icon={BICIM_DUGMESI[b].ikon}
                disabled={calisan !== null}
                onClick={() => void kaydet(b)}
              >
                {calisan === b ? HAZIRLANIYOR : BICIM_DUGMESI[b].etiket}
              </Button>
            ))}
        {satir.muhatapli && kayit != null && evrakKaydiAcik && (
          <Button variant="outlined" icon="move_to_inbox" onClick={() => setKayitPenceresi(true)}>
            {DUGME_EVRAK_KAYDI}
          </Button>
        )}
        {uretebilir && (
          <Button icon="note_add" disabled={calisan !== null} onClick={() => void uret()}>
            {calisan === "uret"
              ? OLUSTURULUYOR
              : kayit === null
                ? DUGME_OLUSTUR
                : DUGME_YENIDEN_OLUSTUR}
          </Button>
        )}
      </div>

      {adliAcik && satir.kipler.includes("ADLI") && (
        <div className="space-y-2 rounded-shape-sm border border-outline-variant px-4 py-3">
          <p className="text-label-large text-on-surface">{ADLI_CIKTI_BASLIGI}</p>
          <p className="text-body-small text-on-surface-variant">{ADLI_CIKTI_ACIKLAMASI}</p>
          {adliKayit && (
            <p className="text-body-small text-on-surface-variant">
              {adliKayitMetni(formatDateTime(adliKayit.uretim_zamani), adliKayit.satir_sayisi)}
            </p>
          )}
          <div className="flex flex-wrap justify-end gap-2">
            {satir.adli_bicimler
              .filter((b) => b in ADLI_DUGMESI)
              .map((b) => (
                <Button
                  key={b}
                  variant="outlined"
                  icon={ADLI_DUGMESI[b].ikon}
                  disabled={calisan !== null}
                  onClick={() => void adli(ADLI_DUGMESI[b].bicim)}
                >
                  {calisan === `adli-${ADLI_DUGMESI[b].bicim}`
                    ? HAZIRLANIYOR
                    : ADLI_DUGMESI[b].etiket}
                </Button>
              ))}
          </div>
        </div>
      )}

      {kayitPenceresi && kayit != null && (
        <EvrakKaydiPenceresi kayit={kayit} onKapat={() => setKayitPenceresi(false)} />
      )}
    </Card>
  );
}

export default function BelgeKartlari({
  kurul,
  adliAcik,
  evrakKaydiAcik,
}: {
  kurul: GenelKurul;
  adliAcik: boolean;
  evrakKaydiAcik: boolean;
}) {
  const [katalog, setKatalog] = useState<Katalog | null>(null);
  const [katalogHatasi, setKatalogHatasi] = useState<SayfaHatasi | null>(null);
  const [kayitlar, setKayitlar] = useState<GkEvrakKaydi[] | null | undefined>(undefined);

  useEffect(() => {
    let iptal = false;
    genelKurulApi
      .katalog()
      .then((k) => {
        if (!iptal) setKatalog(k);
      })
      .catch((e: unknown) => {
        if (!iptal) setKatalogHatasi(hataOku(e, KATALOG_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, []);

  const oku = useCallback(() => {
    genelKurulApi
      .evrakListesi(kurul.id)
      .then(setKayitlar)
      .catch(() => setKayitlar(null));
  }, [kurul.id]);

  useEffect(oku, [oku, kurul.status]);

  const satirlar = useMemo(
    () =>
      GK_BELGELERI.map((kod) => katalog?.belgeler.find((b) => b.kod === kod)).filter(
        (b): b is KatalogSatiri => b !== undefined && b.uretilebilir,
      ),
    [katalog],
  );

  return (
    <section aria-labelledby="gk-belgeleri" className="space-y-3">
      <div>
        <h2 id="gk-belgeleri" className="text-title-medium text-on-surface">
          {BELGELER_BASLIGI}
        </h2>
        <p className="text-body-small text-on-surface-variant">{BELGELER_ACIKLAMASI}</p>
      </div>
      {katalogHatasi && <ErrorBand hata={katalogHatasi} />}
      {katalog !== null && kayitlar !== undefined && (
        <div className="grid gap-3 lg:grid-cols-2">
          {satirlar.map((satir) => (
            <BelgeKarti
              key={satir.kod}
              kurul={kurul}
              satir={satir}
              kayitlar={kayitlar}
              katalog={katalog}
              onUretildi={oku}
              adliAcik={adliAcik}
              evrakKaydiAcik={evrakKaydiAcik}
            />
          ))}
        </div>
      )}
    </section>
  );
}
