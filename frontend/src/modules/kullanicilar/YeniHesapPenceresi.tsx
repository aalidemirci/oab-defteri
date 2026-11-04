// "Yeni hesap" penceresi (plan F1b-2 "Kullanıcılar uçları", "Geçici parola", "Kendi hesabı ve
// ikinci program yöneticisi"; tasarım §4.4.5 "Hesap açma").
//
// FORM: rol (sunucunun seçenekleri, `accounts/options/`: rol etiketi sıra no'suz; açılamayan rol
// seçilince sunucunun nedeni alanın altında, gönderim kapalı; program yöneticisi rolünde sunucunun
// bilgisi — anahtar yenilemesi sonraki sürümde), tanıtıcı (rol seçilince sunucunun varsayılanı;
// kullanıcı değiştirdiyse rol değişimi onu ezmez), ad-soyad, geçici parola (programın önerisiyle
// dolu; `GeciciParolaAlani`). Ön denetim sunucunun kurallarıyla birebirdir (`hesapKurallari`,
// `parolaPolitikasi`) ve her ileti kendi alanının altında çıkar (`useFormErrors`); tanıtıcının
// kişisel veri uyarısı (ad-soyad ya da 11 ardışık rakam) gönderimden ÖNCE de görünür, engel değildir.
// Sunucunun alan hatası varsa alanına, yoksa (servis reddi, kaydı tutmayan hesap, iz yazılamadı)
// pencerenin genel iletisine yazılır. Her denemeden sonra liste yeniden okunur.
//
// YARIM AÇILIŞ (iki depo kuralı 2; sunucunun `OPEN_WRAP_MESSAGE`'ı, 400 `validation_error`):
// güvenlik dosyası yazılamadıysa hesap AÇILMIŞTIR ama parola kaydı yoktur. Pencere bunu iletinin
// metninden değil listeden anlar: gönderimden hemen önce hesapların kimlikleri okunur; alansız bir
// 400'den sonra liste yeniden okunur ve o kümede OLMAYAN, rolü ve tanıtıcısı gönderilenle aynı,
// kapalı olmayan bir hesap varsa hesabı bu deneme açmıştır (açık hesaplarda tanıtıcı tekildir:
// "Bu tanıtıcı açık bir başka hesapta kullanılıyor." reddinde de o tanıtıcılı açık hesap listededir,
// ama gönderimden önce de oradadır). O zaman form kapanır, geçici parola bellekten silinir ve
// pencere sunucunun iletisini hesabın adıyla gösterir; "Hesabı aç" yoktur (Denetleme Kurulu ve
// program yöneticisi rollerinde rol yeniden seçilince yeni varsayılan tanıtıcıyla aynı kişiye
// ikinci bir hesap açılırdı). Çıkış "Parolayı sıfırla"dır (düğme sunucunun `parola_sifirla`
// eylemiyle; pencere kapanır, sıfırlama penceresi açılır). Kimlikler okunamazsa yarım açılış
// sezilemez, ileti genel iletidir (ileti yine hesabın açıldığını söyler).
//
// SONUÇ: hesap açılınca pencere sonuç görünümüne geçer: hesabın adı, sunucunun uyarısı ve bilgisi,
// zarf hatırlatması ve hesap teslim pusulasının düğmesi (yapılamazsa sunucunun nedeni). Geçici
// parola sonuç görünümünde GÖSTERİLMEZ ve bellekten silinir. Form sökülünce odak sonucun başlığına
// (yarım açılışta iletiye) alınır: odak <body>'ye düşmez, ekran okuyucu sonucu okur (WCAG 2.4.3).

import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";

import { useFormErrors } from "../../hooks/useFormErrors";
import { ApiError } from "../../lib/api";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import ErrorBand from "../../ui/ErrorBand";
import Icon from "../../ui/Icon";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import { oturumHataMetni } from "../oturum/hatalar";
import {
  TANITICI_KURALI_METNI,
  adSoyadNormallestir,
  adSoyadSorunu,
  taniticiNormallestir,
  taniticiSorunu,
  taniticiUyarisi,
} from "../oturum/hesapKurallari";
import { parolaSorunu } from "../oturum/parolaPolitikasi";
import EylemDugmesi from "./EylemDugmesi";
import GeciciParolaAlani from "./GeciciParolaAlani";
import { KULLANICILAR_ANAHTARI, kullanicilarApi } from "./api";
import type { HesapAcmaSonucu, KullaniciSatiri, RolSecenegi } from "./api";
import { geciciParolaOner } from "./geciciParola";
import {
  ACILAMADI,
  ACILDI_BASLIGI,
  ACILDI_ZARF_METNI,
  ACILIYOR,
  AD_SOYAD_YARDIMI,
  ALAN_AD_SOYAD,
  ALAN_ROL,
  ALAN_TANITICI,
  DUGME_HESABI_AC,
  DUGME_PUSULA,
  DUGME_SIFIRLA,
  HAZIRLANIYOR,
  PUSULA_ACIKLAMASI,
  PUSULA_HAZIRLANAMADI,
  PUSULA_KAYDEDILDI_ILETISI,
  ROL_SECIN_ILETISI,
  SECENEKLER_OKUNAMADI,
  YARIM_ACILDI_METNI,
  YENI_HESAP_BASLIGI,
  hesapAdi,
} from "./metinler";
import { pusulayiKaydet } from "./pusula";

/** Formun alanları (sunucunun gövde anahtarlarıyla aynı: sunucunun alan hatası alanına düşer). */
type Alan = "rol" | "tanitici" | "ad_soyad" | "gecici_parola";
const ALANLAR: readonly string[] = ["rol", "tanitici", "ad_soyad", "gecici_parola"];

/** Hesap açıldı ama parola kaydı yazılamadı (dosya başı "YARIM AÇILIŞ"). */
interface YarimAcilis {
  hesap: KullaniciSatiri;
  /** Sunucunun iletisi (`OPEN_WRAP_MESSAGE`). */
  ileti: string;
}

interface Props {
  onClose: () => void;
  /** Liste yeniden okunsun (başarıda ve retten sonra). */
  onDegisti: () => void;
  /** Yarım açılışın çıkışı: pencere kapanır, hesabın "Parolayı sıfırla" penceresi açılır. */
  onSifirla: (hesap: KullaniciSatiri) => void;
}

/** Bilgi ya da uyarı bandı (tonal yüzey; kurulum sihirbazının kalıbı). */
function Bant({
  ikon,
  ton,
  children,
}: {
  ikon: string;
  ton: "uyari" | "bilgi";
  children: ReactNode;
}) {
  const renk =
    ton === "uyari"
      ? "bg-tertiary-container text-on-tertiary-container"
      : "bg-secondary-container text-on-secondary-container";
  return (
    <div className={`flex items-start gap-2 rounded-shape-sm px-4 py-3 text-body-medium ${renk}`}>
      <Icon name={ikon} size="lg" className="shrink-0" />
      <span>{children}</span>
    </div>
  );
}

/** Gönderimden önceki hesapların kimlikleri; okunamazsa null (yarım açılış sezilemez). */
async function hesapKimlikleri(): Promise<ReadonlySet<string> | null> {
  try {
    return new Set((await kullanicilarApi.liste()).map((h) => h.id));
  } catch {
    return null;
  }
}

/**
 * Alansız 400'den sonra: hesabı bu deneme mi açtı? Gönderimden önce listede OLMAYAN, rolü ve
 * tanıtıcısı gönderilenle aynı, kapalı olmayan hesap (dosya başı "YARIM AÇILIŞ"); yoksa null.
 * İleti metniyle dallanılmaz.
 */
async function yarimAcilanHesap(
  onceki: ReadonlySet<string>,
  rol: string,
  tanitici: string,
): Promise<KullaniciSatiri | null> {
  try {
    const sonraki = await kullanicilarApi.liste();
    return (
      sonraki.find(
        (h) =>
          !onceki.has(h.id) && h.rol === rol && h.tanitici === tanitici && h.durum !== "KAPALI",
      ) ?? null
    );
  } catch {
    return null;
  }
}

export default function YeniHesapPenceresi({ onClose, onDegisti, onSifirla }: Props) {
  const secenekler = useQuery({
    queryKey: [...KULLANICILAR_ANAHTARI, "secenekler"],
    queryFn: kullanicilarApi.secenekler,
    staleTime: 0,
    gcTime: 0,
    retry: false,
  });
  const [sonuc, setSonuc] = useState<HesapAcmaSonucu | null>(null);
  const [yarim, setYarim] = useState<YarimAcilis | null>(null);

  return (
    <Dialog
      open
      wide
      onClose={onClose}
      title={YENI_HESAP_BASLIGI}
      actions={
        sonuc || yarim ? (
          <Button variant="filled" onClick={onClose}>
            Kapat
          </Button>
        ) : undefined
      }
    >
      {sonuc ? (
        <SonucGorunumu sonuc={sonuc} />
      ) : yarim ? (
        <YarimAcilisGorunumu yarim={yarim} onSifirla={onSifirla} />
      ) : secenekler.isPending ? (
        <SkeletonList rows={4} />
      ) : secenekler.isError ? (
        <div className="flex flex-col gap-4">
          <ErrorBand hata={oturumHataMetni(secenekler.error, SECENEKLER_OKUNAMADI)} />
          <div className="flex justify-end">
            <Button variant="text" onClick={onClose}>
              Vazgeç
            </Button>
          </div>
        </div>
      ) : (
        <HesapFormu
          roller={secenekler.data.roller}
          onClose={onClose}
          onAcildi={setSonuc}
          onYarim={setYarim}
          onDegisti={onDegisti}
        />
      )}
    </Dialog>
  );
}

function HesapFormu({
  roller,
  onClose,
  onAcildi,
  onYarim,
  onDegisti,
}: {
  roller: RolSecenegi[];
  onClose: () => void;
  onAcildi: (sonuc: HesapAcmaSonucu) => void;
  onYarim: (yarim: YarimAcilis) => void;
  onDegisti: () => void;
}) {
  const [rol, setRol] = useState("");
  const [tanitici, setTanitici] = useState("");
  // Kullanıcı tanıtıcıyı elle değiştirdiyse rol değişimi onu ezmez.
  const [taniticiElle, setTaniticiElle] = useState(false);
  const [adSoyad, setAdSoyad] = useState("");
  const [parola, setParola] = useState(() => geciciParolaOner());
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors<Alan>();
  const [genelHata, setGenelHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);
  const taniticiAlani = useRef<HTMLInputElement>(null);
  const adAlani = useRef<HTMLInputElement>(null);
  const parolaAlani = useRef<HTMLInputElement>(null);

  const secili = roller.find((r) => r.rol === rol) ?? null;
  // Açılamayan rolün nedeni sunucunundur; gönderim kapalıdır.
  const rolNedeni = secili !== null && !secili.acilabilir ? secili.neden : null;
  const onUyari = taniticiUyarisi(tanitici, adSoyad);

  function rolDegisti(yeni: string) {
    setRol(yeni);
    if (!taniticiElle) {
      setTanitici(roller.find((r) => r.rol === yeni)?.varsayilan_tanitici ?? "");
    }
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    clearErrors();
    setGenelHata(null);
    // İstemci ön denetimi (otorite sunucudur; iletiler birebir). Her ileti kendi alanında.
    const sorunlar: Array<[Alan, string | null]> = [
      ["rol", secili === null ? ROL_SECIN_ILETISI : rolNedeni],
      ["tanitici", taniticiSorunu(tanitici)],
      ["ad_soyad", adSoyadSorunu(adSoyad)],
      ["gecici_parola", parolaSorunu(parola)],
    ];
    const hatalilar = sorunlar.filter((s): s is [Alan, string] => s[1] !== null);
    hatalilar.forEach(([alan, ileti]) => setFieldError(alan, ileti));
    if (hatalilar.length > 0) {
      odakla(hatalilar[0][0]);
      return;
    }
    setCalisiyor(true);
    const govde = {
      rol,
      tanitici: taniticiNormallestir(tanitici),
      ad_soyad: adSoyadNormallestir(adSoyad),
      gecici_parola: parola,
    };
    // Yarım açılışı sezmek için gönderimden önceki hesaplar (dosya başı "YARIM AÇILIŞ").
    const onceki = await hesapKimlikleri();
    try {
      const yanit = await kullanicilarApi.ac(govde);
      // Geçici parola sonuç görünümünde yoktur ve bellekte bekletilmez.
      setParola("");
      onAcildi(yanit);
    } catch (err) {
      const alan = applyApiError(err);
      if (alan !== null && ALANLAR.includes(alan)) {
        odakla(alan);
      } else {
        const acilan =
          onceki !== null && err instanceof ApiError && err.status === 400
            ? await yarimAcilanHesap(onceki, govde.rol, govde.tanitici)
            : null;
        if (acilan !== null) {
          setParola("");
          onYarim({ hesap: acilan, ileti: oturumHataMetni(err, ACILAMADI) });
        } else {
          setGenelHata(oturumHataMetni(err, ACILAMADI));
        }
      }
    } finally {
      setCalisiyor(false);
      onDegisti();
    }
  }

  function odakla(alan: Alan) {
    const alanlar: Partial<Record<Alan, typeof taniticiAlani>> = {
      tanitici: taniticiAlani,
      ad_soyad: adAlani,
      gecici_parola: parolaAlani,
    };
    alanlar[alan]?.current?.focus();
  }

  return (
    <form onSubmit={gonder} noValidate className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Select
          className="sm:col-span-2"
          label={ALAN_ROL}
          placeholder="Seçin"
          value={rol}
          onChange={(e) => rolDegisti(e.target.value)}
          options={roller.map((r) => ({ value: r.rol, label: r.rol_etiketi }))}
          error={errors.rol ?? rolNedeni ?? undefined}
          disabled={calisiyor}
          required
        />
        {secili?.bilgi && (
          <div className="sm:col-span-2">
            <Bant ikon="info" ton="bilgi">
              {secili.bilgi}
            </Bant>
          </div>
        )}
        <TextField
          ref={taniticiAlani}
          label={ALAN_TANITICI}
          value={tanitici}
          onChange={(e) => {
            setTanitici(e.target.value);
            setTaniticiElle(true);
          }}
          autoComplete="off"
          spellCheck={false}
          helperText={TANITICI_KURALI_METNI}
          error={errors.tanitici}
          disabled={calisiyor}
          required
        />
        <TextField
          ref={adAlani}
          label={ALAN_AD_SOYAD}
          value={adSoyad}
          onChange={(e) => setAdSoyad(e.target.value)}
          autoComplete="off"
          helperText={AD_SOYAD_YARDIMI}
          error={errors.ad_soyad}
          disabled={calisiyor}
          required
        />
        {onUyari && (
          <div role="status" className="sm:col-span-2">
            <Bant ikon="warning" ton="uyari">
              {onUyari}
            </Bant>
          </div>
        )}
        <div className="sm:col-span-2">
          <GeciciParolaAlani
            ref={parolaAlani}
            deger={parola}
            onDeger={setParola}
            hata={errors.gecici_parola}
            disabled={calisiyor}
          />
        </div>
      </div>
      {genelHata && <ErrorBand hata={genelHata} />}
      <div className="flex justify-end gap-2">
        <Button variant="text" type="button" onClick={onClose}>
          Vazgeç
        </Button>
        <Button type="submit" icon="person_add" disabled={calisiyor || rolNedeni !== null}>
          {calisiyor ? ACILIYOR : DUGME_HESABI_AC}
        </Button>
      </div>
    </form>
  );
}

/** Takılınca odağı alan öğenin ref'i (form sökülünce odak <body>'ye düşmesin; dosya başı). */
function useTakilincaOdak<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  return ref;
}

/** Hesap açıldı: ad, sunucunun uyarısı ve bilgisi, zarf, pusula (geçici parola YOK). */
function SonucGorunumu({ sonuc }: { sonuc: HesapAcmaSonucu }) {
  const snackbar = useSnackbar();
  const baslik = useTakilincaOdak<HTMLParagraphElement>();
  const [hazirlaniyor, setHazirlaniyor] = useState(false);
  const [hata, setHata] = useState<string | null>(null);

  async function pusulaKaydet() {
    setHazirlaniyor(true);
    setHata(null);
    try {
      await pusulayiKaydet(sonuc.hesap);
      snackbar.success(PUSULA_KAYDEDILDI_ILETISI);
    } catch (err) {
      setHata(oturumHataMetni(err, PUSULA_HAZIRLANAMADI));
    } finally {
      setHazirlaniyor(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div role="status" className="flex items-start gap-3">
        <Icon name="check_circle" className="shrink-0 text-primary" />
        <div>
          <p ref={baslik} tabIndex={-1} className="text-title-medium text-on-surface outline-none">
            {ACILDI_BASLIGI}
          </p>
          <p className="mt-1 text-body-medium text-on-surface">{hesapAdi(sonuc.hesap)}</p>
        </div>
      </div>
      {sonuc.uyari && (
        <Bant ikon="warning" ton="uyari">
          {sonuc.uyari}
        </Bant>
      )}
      {sonuc.bilgi && (
        <Bant ikon="info" ton="bilgi">
          {sonuc.bilgi}
        </Bant>
      )}
      <Bant ikon="mail_lock" ton="bilgi">
        {ACILDI_ZARF_METNI}
      </Bant>
      <p className="text-body-medium text-on-surface-variant">{PUSULA_ACIKLAMASI}</p>
      <EylemDugmesi
        durum={sonuc.hesap.eylemler.pusula}
        etiket={DUGME_PUSULA}
        calisiyorEtiketi={HAZIRLANIYOR}
        calisiyor={hazirlaniyor}
        ikon="picture_as_pdf"
        variant="tonal"
        onClick={() => void pusulaKaydet()}
      />
      {hata && <ErrorBand hata={hata} />}
    </div>
  );
}

/**
 * Hesap açıldı, parola kaydı yazılamadı (dosya başı "YARIM AÇILIŞ"): sunucunun iletisi, hesabın
 * adı, geçici parolanın geçmediği ve çıkış ("Parolayı sıfırla"; sunucunun eylemi). Form, geçici
 * parola, zarf notu ve pusula YOK.
 */
function YarimAcilisGorunumu({
  yarim,
  onSifirla,
}: {
  yarim: YarimAcilis;
  onSifirla: (hesap: KullaniciSatiri) => void;
}) {
  const ileti = useTakilincaOdak<HTMLParagraphElement>();
  return (
    <div className="flex flex-col gap-4">
      <div role="alert" className="flex items-start gap-3">
        <Icon name="error" className="shrink-0 text-error" />
        <div>
          <p ref={ileti} tabIndex={-1} className="text-title-medium text-on-surface outline-none">
            {yarim.ileti}
          </p>
          <p className="mt-1 text-body-medium text-on-surface">{hesapAdi(yarim.hesap)}</p>
        </div>
      </div>
      <Bant ikon="warning" ton="uyari">
        {YARIM_ACILDI_METNI}
      </Bant>
      <EylemDugmesi
        durum={yarim.hesap.eylemler.parola_sifirla}
        etiket={DUGME_SIFIRLA}
        ikon="lock_reset"
        variant="tonal"
        onClick={() => onSifirla(yarim.hesap)}
      />
    </div>
  );
}
