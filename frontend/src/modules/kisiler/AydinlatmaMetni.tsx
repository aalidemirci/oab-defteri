// Aktarım ekranlarının kişisel veri aydınlatma metni (KVKK md. 10/1; genel tasarım §8.4
// "Aydınlatma"; plan "F1b-5 uygulama kararları"). Personel aktarım paneli personel metnini, veli
// listesi aktarım paneli veli metnini AKTARMADAN ÖNCE, dosya seçiminin üstünde gösterir.
//
// Metinler kullanıcının onayladığı biçimdedir ve `metinler.ts`'ten BİREBİR gelir; burada yalnız
// satırların başlığı ("Amaç:", "Aktarım:" …) kalın yazılır, metin değişmez. "Veri sorumlusu:"
// satırının değeri Okul Bilgileri'ndeki veri sorumlusu bilgisidir (`data_controller_text`): boşken
// yerine uyarı ve Ayarlar → Okul Bilgileri bağlantısı çıkar, AKTARIM ENGELLENMEZ (yalnız bilgi);
// okunamazsa bunu söyler. Ekran notu metnin altında not olarak durur.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Icon from "../../ui/Icon";
import { okulApi } from "../okul/api";
import {
  AYDINLATMA_AKTARIM,
  AYDINLATMA_BASLIGI,
  AYDINLATMA_EKRAN_NOTU,
  AYDINLATMA_HAKLARINIZ,
  AYDINLATMA_VERI_SORUMLUSU_ETIKETI,
  PERSONEL_AYDINLATMA_AMACI,
  PERSONEL_AYDINLATMA_GIRISI,
  PERSONEL_AYDINLATMA_SAKLAMA,
  PERSONEL_AYDINLATMA_TOPLAMA,
  VELI_AYDINLATMA_AMACI,
  VELI_AYDINLATMA_GIRISI,
  VELI_AYDINLATMA_SAKLAMA,
  VELI_AYDINLATMA_TOPLAMA,
  VERI_SORUMLUSU_BAGLANTISI,
  VERI_SORUMLUSU_GIRILMEDI,
  VERI_SORUMLUSU_OKUNAMADI,
} from "./metinler";

/** Okul Bilgileri sekmesinin adresi (Ayarlar → `?tab=okul`). */
export const OKUL_BILGILERI_ADRESI = "/ayarlar?tab=okul";

export type AydinlatmaTuru = "personel" | "veli";

const METINLER: Record<
  AydinlatmaTuru,
  { giris: string; amac: string; toplama: string; saklama: string }
> = {
  personel: {
    giris: PERSONEL_AYDINLATMA_GIRISI,
    amac: PERSONEL_AYDINLATMA_AMACI,
    toplama: PERSONEL_AYDINLATMA_TOPLAMA,
    saklama: PERSONEL_AYDINLATMA_SAKLAMA,
  },
  veli: {
    giris: VELI_AYDINLATMA_GIRISI,
    amac: VELI_AYDINLATMA_AMACI,
    toplama: VELI_AYDINLATMA_TOPLAMA,
    saklama: VELI_AYDINLATMA_SAKLAMA,
  },
};

/** "Başlık: metin" satırı — başlık kalın; metin olduğu gibi (birebirlik bozulmaz). */
function Satir({ metin }: { metin: string }) {
  const ayrac = metin.indexOf(": ");
  if (ayrac < 0) return <p>{metin}</p>;
  return (
    <p>
      <span className="font-semibold">{metin.slice(0, ayrac + 1)}</span>
      {metin.slice(ayrac + 1)}
    </p>
  );
}

/** Veri sorumlusunun durumu: yükleniyor (undefined), okunamadı (null), metin (boş olabilir). */
type VeriSorumlusu = string | null | undefined;

function VeriSorumlusuSatiri({ deger }: { deger: VeriSorumlusu }) {
  if (deger === undefined) {
    return <p className="font-semibold">{AYDINLATMA_VERI_SORUMLUSU_ETIKETI}</p>;
  }
  if (deger !== null && deger.trim()) {
    return (
      <p className="whitespace-pre-line break-words">
        <span className="font-semibold">{AYDINLATMA_VERI_SORUMLUSU_ETIKETI}</span> {deger.trim()}
      </p>
    );
  }
  return (
    <div className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-3 py-2 text-on-tertiary-container">
      <Icon name="warning" size="lg" className="mt-0.5 shrink-0" />
      <div className="min-w-0 space-y-1">
        <p>
          <span className="font-semibold">{AYDINLATMA_VERI_SORUMLUSU_ETIKETI}</span>{" "}
          {deger === null ? VERI_SORUMLUSU_OKUNAMADI : VERI_SORUMLUSU_GIRILMEDI}
        </p>
        {deger !== null && (
          <Link
            to={OKUL_BILGILERI_ADRESI}
            className="inline-flex text-label-large text-primary underline underline-offset-2"
          >
            {VERI_SORUMLUSU_BAGLANTISI}
          </Link>
        )}
      </div>
    </div>
  );
}

export default function AydinlatmaMetni({ tur }: { tur: AydinlatmaTuru }) {
  const [veriSorumlusu, setVeriSorumlusu] = useState<VeriSorumlusu>(undefined);
  const metin = METINLER[tur];

  useEffect(() => {
    let iptal = false;
    okulApi
      .getSchoolConfig()
      .then((kart) => {
        if (!iptal) setVeriSorumlusu(kart.data_controller_text ?? "");
      })
      .catch(() => {
        if (!iptal) setVeriSorumlusu(null);
      });
    return () => {
      iptal = true;
    };
  }, []);

  return (
    <section
      aria-label={AYDINLATMA_BASLIGI}
      className="space-y-2 rounded-shape-md border border-outline-variant bg-surface-container-lowest p-4 text-body-small text-on-surface"
    >
      <h3 className="flex items-center gap-2 text-label-large text-on-surface">
        <Icon name="policy" size="lg" className="shrink-0" />
        {AYDINLATMA_BASLIGI}
      </h3>
      <Satir metin={metin.giris} />
      <VeriSorumlusuSatiri deger={veriSorumlusu} />
      <Satir metin={metin.amac} />
      <Satir metin={AYDINLATMA_AKTARIM} />
      <Satir metin={metin.toplama} />
      <Satir metin={metin.saklama} />
      <Satir metin={AYDINLATMA_HAKLARINIZ} />
      <p className="text-on-surface-variant italic">{AYDINLATMA_EKRAN_NOTU}</p>
    </section>
  );
}
