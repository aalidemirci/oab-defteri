// Birlik Dönemi → Kural Sürümü Güncellemesi (tasarım §6.2-5 fark ekranı; plan F2 §6.1, 2. adımın ucu
// `oab-term-rule-revision`). Yalnız `kural_surumu_guncelleme` yeteneğinde çizilir (Ayarlar satırı:
// okuması da yazması da yalnız program yöneticisi). Gösterilen: dönemin bağlı sürümü, programla gelen en
// yeni sürüm, geçilecek sürüm (programla gelen daha yeni revizyonlar ve dönemin önceki bağları: eskiye
// seçim geri almadır), farkın beş listesi (eklenen, çıkarılan, yürürlüğü biten, değeri değişen,
// düzeltilen; her kural açıklaması ve madde atfıyla — kural kimliği yüzeye çıkmaz, sözlük §2) ve
// hesabı ya da uyarısı değişecek kayıtlar. Etkilenen kayıt varsa geçiş ayrıca onay ister (sunucu 409
// `revizyon_onayi_gerekli`); kapanmış dönemde geçiş sert engeldir (409 `donem_kapali`).

import { useEffect, useState } from "react";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import Select from "../../ui/Select";
import { useSnackbar } from "../../ui/SnackbarProvider";
import OnayKutusu from "../genel-kurul/OnayKutusu";
import { Dayanak, UyumHataBandi } from "../uyum/UyariGerekce";
import { uyumHatasiOku } from "../uyum/hatalar";
import type { UyumHatasi } from "../uyum/hatalar";
import { birlikDonemiApi } from "./api";
import type { BirlikDonemi, FarkKurali, KuralSurumu, KuralSurumuDurumu } from "./api";
import {
  ALAN_BAGLI_SURUM,
  ALAN_EN_YENI_SURUM,
  ALAN_HEDEF_SURUM,
  BILINMEYEN_KAYIT,
  DUGME_GERI_AL,
  DUGME_SURUMU_GUNCELLE,
  ETKILENEN_KAYITLAR,
  ETKILENEN_ONAYI,
  ETKILENEN_ONAYI_GEREKLI,
  FARK_BITEN,
  FARK_BOS,
  FARK_CIKARILAN,
  FARK_DEGER,
  FARK_DUZELTILEN,
  FARK_EKLENEN,
  KAYIT_TURU_TR,
  KURAL_GECILEMEZ,
  KURAL_GUNCEL,
  KURAL_GUNCELLEME_ACIKLAMASI,
  KURAL_GUNCELLEME_BASLIGI,
  KURAL_GUNCELLEME_OKUNAMADI,
  SURUM_GUNCELLENDI,
  SURUM_GUNCELLENEMEDI,
  etkilenenKayitMetni,
  kuralSurumuMetni,
} from "./metinler";

const anahtar = (s: KuralSurumu) => `${s.paket}#${s.rev}`;
const eskiMi = (a: KuralSurumu, b: KuralSurumu) =>
  a.paket < b.paket || (a.paket === b.paket && a.rev < b.rev);

function FarkListesi({ baslik, kurallar }: { baslik: string; kurallar: FarkKurali[] }) {
  if (kurallar.length === 0) return null;
  return (
    <div className="space-y-1">
      <p className="text-label-large text-on-surface">{baslik}</p>
      <ul aria-label={baslik} className="divide-y divide-outline-variant">
        {kurallar.map((k) => (
          <li key={k.id} className="py-1.5">
            <span className="block break-words text-body-medium text-on-surface">{k.aciklama}</span>
            <Dayanak atif={k.atif} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function KuralSurumuGuncellemesi({
  donem,
  onGuncellendi,
}: {
  donem: BirlikDonemi;
  onGuncellendi: () => void;
}) {
  const snackbar = useSnackbar();
  const [durum, setDurum] = useState<KuralSurumuDurumu | null>(null);
  const [hedef, setHedef] = useState<KuralSurumu | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [uyum, setUyum] = useState<UyumHatasi | null>(null);
  const [onay, setOnay] = useState(false);
  const [onayHatasi, setOnayHatasi] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [yenile, setYenile] = useState(0);

  useEffect(() => {
    let iptal = false;
    birlikDonemiApi
      .kuralSurumu(donem.id, hedef ?? undefined)
      .then((d) => {
        if (iptal) return;
        setDurum(d);
        setHata(null);
        setOnay(false);
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, KURAL_GUNCELLEME_OKUNAMADI));
      });
    return () => {
      iptal = true;
    };
  }, [donem.id, hedef, yenile]);

  const secili = hedef ?? durum?.hedef ?? null;
  const fark = durum?.fark ?? null;
  const geriAlma = secili !== null && durum !== null && eskiMi(secili, durum.bagli);

  const gec = async () => {
    if (secili === null || fark === null) return;
    if (fark.onay_gerekli && !onay) {
      setOnayHatasi(ETKILENEN_ONAYI_GEREKLI);
      return;
    }
    setBusy(true);
    setHata(null);
    setUyum(null);
    try {
      await birlikDonemiApi.kuralSurumunuGecir(donem.id, secili, onay);
      snackbar.success(SURUM_GUNCELLENDI);
      setHedef(null);
      setYenile((y) => y + 1);
      onGuncellendi();
    } catch (e) {
      const okunan = uyumHatasiOku(e);
      if (okunan) setUyum(okunan);
      else setHata(hataOku(e, SURUM_GUNCELLENEMEDI));
    } finally {
      setBusy(false);
    }
  };

  const farkBos =
    fark !== null &&
    [fark.eklenen, fark.cikarilan, fark.biten, fark.deger_degisen, fark.duzeltilen].every(
      (l) => l.length === 0,
    );

  return (
    <Card elevation={0} className="space-y-4 p-[var(--od-panel-padding)]">
      <div>
        <h2 className="text-title-medium text-on-surface">{KURAL_GUNCELLEME_BASLIGI}</h2>
        <p className="text-body-small text-on-surface-variant">{KURAL_GUNCELLEME_ACIKLAMASI}</p>
      </div>
      {hata && <ErrorBand hata={hata} />}
      {uyum && <UyumHataBandi hata={uyum} />}
      {durum !== null && (
        <>
          <dl className="grid gap-3 sm:grid-cols-2">
            <div className="min-w-0">
              <dt className="text-label-medium text-on-surface-variant">{ALAN_BAGLI_SURUM}</dt>
              <dd className="text-body-medium text-on-surface">{kuralSurumuMetni(durum.bagli)}</dd>
            </div>
            <div className="min-w-0">
              <dt className="text-label-medium text-on-surface-variant">{ALAN_EN_YENI_SURUM}</dt>
              <dd className="text-body-medium text-on-surface">
                {durum.en_yeni ? kuralSurumuMetni(durum.en_yeni) : "—"}
              </dd>
            </div>
          </dl>
          {!durum.gecilebilir ? (
            <p className="text-body-medium text-on-surface-variant">{KURAL_GECILEMEZ}</p>
          ) : (
            <>
              {durum.hedefler.length > 0 && (
                <Select
                  className="max-w-md"
                  label={ALAN_HEDEF_SURUM}
                  value={secili ? anahtar(secili) : ""}
                  onChange={(e) =>
                    setHedef(durum.hedefler.find((h) => anahtar(h) === e.target.value) ?? null)
                  }
                  options={durum.hedefler.map((h) => ({
                    value: anahtar(h),
                    label: kuralSurumuMetni(h),
                  }))}
                />
              )}
              {fark === null ? (
                <p className="text-body-medium text-on-surface-variant">{KURAL_GUNCEL}</p>
              ) : (
                <div className="space-y-4">
                  {farkBos && (
                    <p className="text-body-medium text-on-surface-variant">{FARK_BOS}</p>
                  )}
                  <FarkListesi baslik={FARK_EKLENEN} kurallar={fark.eklenen} />
                  <FarkListesi baslik={FARK_CIKARILAN} kurallar={fark.cikarilan} />
                  <FarkListesi baslik={FARK_BITEN} kurallar={fark.biten} />
                  <FarkListesi baslik={FARK_DEGER} kurallar={fark.deger_degisen} />
                  <FarkListesi baslik={FARK_DUZELTILEN} kurallar={fark.duzeltilen} />
                  {fark.kayitlar.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-label-large text-on-surface">{ETKILENEN_KAYITLAR}</p>
                      <ul aria-label={ETKILENEN_KAYITLAR} className="list-disc pl-5">
                        {fark.kayitlar.map((k) => (
                          <li
                            key={`${k.model}-${k.kayit_id}-${k.kural_id}`}
                            className="text-body-medium text-on-surface"
                          >
                            {etkilenenKayitMetni(
                              KAYIT_TURU_TR[k.model] ?? BILINMEYEN_KAYIT,
                              k.kayit_id,
                            )}
                          </li>
                        ))}
                      </ul>
                      <OnayKutusu
                        etiket={ETKILENEN_ONAYI}
                        secili={onay}
                        onDegis={(d) => {
                          setOnay(d);
                          setOnayHatasi(undefined);
                        }}
                        hata={onayHatasi}
                      />
                    </div>
                  )}
                  <div className="flex justify-end">
                    <Button
                      icon={geriAlma ? "undo" : "upgrade"}
                      disabled={busy}
                      onClick={() => void gec()}
                    >
                      {geriAlma ? DUGME_GERI_AL : DUGME_SURUMU_GUNCELLE}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </Card>
  );
}
