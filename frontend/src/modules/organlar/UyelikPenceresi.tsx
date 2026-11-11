// Üyeliğin ayrıntı penceresi (Organlar; plan F1c 11. adım). Geniş kadro tablosu yerine satır bu pencerede
// açılır (1366×768'de yatay kaydırma olmasın). Her rol okur; eylem düğmeleri yeteneğe ve kaydın durumuna
// göre çizilir, kapı sunucudadır.
//
// Görev alma engeli: hüküm (var ya da yok) her rolde görünür; DAYANAK yalnız `gorev_alma_engeli`
// yeteneğinde (program yöneticisi ve yönetim kurulu rolleri) "Dayanağı göster" düğmesiyle okunur, okuma
// erişim günlüğüne yazılır (tasarım §4.4.2 ¹¹). Uyum satırları sunucudan rolün görünümüyle gelir:
// Denetleme Kurulu ve müdür engel satırını atıfsız genel metinle görür (kullanıcı kararı 10.11.2026).

import { useState } from "react";

import { formatDate } from "../../lib/format";
import Button from "../../ui/Button";
import Dialog from "../../ui/Dialog";
import { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import type { ReactNode } from "react";
import {
  ALAN_GOREV,
  ALAN_KOLTUK,
  ALAN_MEM_ONAY_NO,
  ALAN_SECILDIGI_GUN,
  ALAN_SECIM_KANALI,
  GOREV_TR,
  KOLTUK_GRUBU_OGRETMEN,
  KOLTUK_GRUBU_VELI,
  koltukMetni,
} from "../gecis-kurulumu/metinler";
import { UyumSatirlari } from "../uyum/UyariGerekce";
import { organlarApi } from "./api";
import type {
  EngelDayanagiYaniti,
  KadroOrgani,
  SecilmeSayaci,
  Uyelik,
  UyelikOnerisi,
  UyelikUyumSatiri,
} from "./api";
import {
  ALAN_CAGRI_GUNU,
  ALAN_DAYANAK,
  ALAN_DK_SAYAC,
  ALAN_DURUM,
  ALAN_DUSME,
  ALAN_ENGEL,
  ALAN_GOREVLENDIRME,
  ALAN_KAYIT,
  ALAN_SUC_BEYANI,
  ALAN_TEK_BIRLIK_BEYANI,
  ALAN_UZMANLIK,
  ALAN_YK_SAYAC,
  CIP_ERTELENDI,
  DAYANAK_OKUMA_NOTU,
  DAYANAK_OKUNAMADI,
  DUGME_BILGILER,
  DUGME_DAYANAK,
  DUGME_DUSUR,
  DUGME_ENGEL,
  DUGME_KAYDI_IPTAL,
  DUGME_YEDEK_CAGIR,
  DURUM_TR,
  DUSME_TURU_TR,
  ENGEL_DAYANAGI_TR,
  ENGEL_YOK,
  KAYIT_DEVRALINAN,
  KAYIT_PROGRAM,
  ONERILER_BASLIGI,
  SECIM_KANALI_TR,
  UYELIK_PENCERESI_BASLIGI,
  UYUM_BASLIGI,
  engelVarMetni,
  sayacMetni,
} from "./metinler";
import { PencereHatasi } from "./ortak";

/** Pencereden açılan eylem (pencere kapanır, eylemin penceresi açılır). */
export type UyelikEylemi = "engel" | "bilgi" | "yedek" | "dusme" | "iptal";

function Bilgi({ etiket, children }: { etiket: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-label-medium text-on-surface-variant">{etiket}</dt>
      <dd className="break-words text-body-medium text-on-surface">{children}</dd>
    </div>
  );
}

export default function UyelikPenceresi({
  uyelik,
  organ,
  sayac,
  uyumSatirlari,
  oneriler,
  eylemler,
  dayanakOkunur,
  onEylem,
  onKapat,
}: {
  uyelik: Uyelik;
  organ: KadroOrgani;
  sayac: SecilmeSayaci | undefined;
  uyumSatirlari: readonly UyelikUyumSatiri[];
  oneriler: readonly UyelikOnerisi[];
  /** Çizilecek eylemler (yetenek ve kaydın durumuna göre çağıran süzer). */
  eylemler: readonly UyelikEylemi[];
  /** "Dayanağı göster" düğmesi (`gorev_alma_engeli`). */
  dayanakOkunur: boolean;
  onEylem: (eylem: UyelikEylemi) => void;
  onKapat: () => void;
}) {
  const [dayanak, setDayanak] = useState<EngelDayanagiYaniti | null>(null);
  const [okunuyor, setOkunuyor] = useState(false);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  const dayanagiOku = async () => {
    setOkunuyor(true);
    setHata(null);
    try {
      setDayanak(await organlarApi.engelDayanagi(uyelik.id));
    } catch (e) {
      setHata(hataOku(e, DAYANAK_OKUNAMADI));
    } finally {
      setOkunuyor(false);
    }
  };

  const engelVar = uyelik.eligibility_bar === "VAR";
  const grup =
    uyelik.seat_group === "VELI"
      ? KOLTUK_GRUBU_VELI
      : uyelik.seat_group === "OGRETMEN"
        ? KOLTUK_GRUBU_OGRETMEN
        : null;
  const ogretmen = organ === "DK" && uyelik.seat_group === "OGRETMEN";
  const ETIKETLER: Record<UyelikEylemi, [string, string]> = {
    engel: [DUGME_ENGEL, "gpp_maybe"],
    bilgi: [DUGME_BILGILER, "edit"],
    yedek: [DUGME_YEDEK_CAGIR, "how_to_reg"],
    dusme: [DUGME_DUSUR, "person_remove"],
    iptal: [DUGME_KAYDI_IPTAL, "block"],
  };

  return (
    <Dialog
      open
      wide
      onClose={onKapat}
      title={uyelik.person_name ?? UYELIK_PENCERESI_BASLIGI}
      actions={
        <Button variant="filled" onClick={onKapat}>
          Kapat
        </Button>
      }
    >
      <div className="space-y-5">
        <PencereHatasi hata={hata} />
        <dl className="grid gap-4 sm:grid-cols-2">
          <Bilgi etiket={ALAN_DURUM}>
            {DURUM_TR[uyelik.status]}
            {uyelik.retained_until_assembly && ` · ${CIP_ERTELENDI}`}
          </Bilgi>
          {organ !== "ALIM_KOMISYONU" && (
            <Bilgi etiket={ALAN_KOLTUK}>
              {koltukMetni(uyelik.seat_type, uyelik.seat_order)}
              {grup && ` · ${grup}`}
            </Bilgi>
          )}
          {organ !== "ALIM_KOMISYONU" && <Bilgi etiket={ALAN_GOREV}>{GOREV_TR[uyelik.role]}</Bilgi>}
          <Bilgi etiket={ALAN_SECIM_KANALI}>{SECIM_KANALI_TR[uyelik.elected_by]}</Bilgi>
          <Bilgi etiket={ALAN_SECILDIGI_GUN}>{formatDate(uyelik.start_date)}</Bilgi>
          {uyelik.promoted_on && (
            <Bilgi etiket={ALAN_CAGRI_GUNU}>{formatDate(uyelik.promoted_on)}</Bilgi>
          )}
          <Bilgi etiket={ALAN_KAYIT}>
            {uyelik.source === "DEVRALINAN" ? KAYIT_DEVRALINAN : KAYIT_PROGRAM}
          </Bilgi>
          {uyelik.status === "DUSTU" && (
            <Bilgi etiket={ALAN_DUSME}>
              {uyelik.drop_kind ? DUSME_TURU_TR[uyelik.drop_kind] : "—"} ·{" "}
              {formatDate(uyelik.end_date)}
            </Bilgi>
          )}
          {ogretmen && uyelik.elected_by === "MEM_GOREVLENDIRME" && (
            <Bilgi etiket={ALAN_MEM_ONAY_NO}>{uyelik.mem_approval_no || "—"}</Bilgi>
          )}
          {ogretmen && (uyelik.external_assignment_start || uyelik.external_assignment_end) && (
            <Bilgi etiket={ALAN_GOREVLENDIRME}>
              {formatDate(uyelik.external_assignment_start)} –{" "}
              {formatDate(uyelik.external_assignment_end)}
            </Bilgi>
          )}
          {organ === "ALIM_KOMISYONU" && (
            <Bilgi etiket={ALAN_UZMANLIK}>{uyelik.expertise_required ? "Evet" : "Hayır"}</Bilgi>
          )}
          {organ !== "ALIM_KOMISYONU" && (
            <Bilgi etiket={ALAN_SUC_BEYANI}>{formatDate(uyelik.eligibility_declared_on)}</Bilgi>
          )}
          {organ === "YK" && (
            <Bilgi etiket={ALAN_TEK_BIRLIK_BEYANI}>
              {formatDate(uyelik.single_birlik_declared_on)}
            </Bilgi>
          )}
          {sayac && (
            <Bilgi etiket={organ === "DK" ? ALAN_DK_SAYAC : ALAN_YK_SAYAC}>
              {sayacMetni(sayac.program, sayac.beyan)}
            </Bilgi>
          )}
          <Bilgi etiket={ALAN_ENGEL}>
            {engelVar ? engelVarMetni(formatDate(uyelik.eligibility_bar_found_on)) : ENGEL_YOK}
          </Bilgi>
          {dayanak !== null && (
            <Bilgi etiket={ALAN_DAYANAK}>
              {dayanak.eligibility_bar_basis
                ? ENGEL_DAYANAGI_TR[dayanak.eligibility_bar_basis]
                : "—"}
              <span className="mt-0.5 block text-body-small text-on-surface-variant">
                {DAYANAK_OKUMA_NOTU}
              </span>
            </Bilgi>
          )}
        </dl>

        {uyumSatirlari.length > 0 && (
          <section className="space-y-1">
            <h3 className="text-title-small text-on-surface">{UYUM_BASLIGI}</h3>
            <UyumSatirlari satirlar={uyumSatirlari} baslik={UYUM_BASLIGI} />
          </section>
        )}
        {oneriler.length > 0 && (
          <section className="space-y-1">
            <h3 className="text-title-small text-on-surface">{ONERILER_BASLIGI}</h3>
            <ul className="list-disc space-y-1 pl-5 text-body-medium text-on-surface">
              {oneriler.map((o) => (
                <li key={`${o.tur}-${o.metin}`} className="break-words">
                  {o.metin}
                </li>
              ))}
            </ul>
          </section>
        )}

        {(eylemler.length > 0 || (dayanakOkunur && engelVar && dayanak === null)) && (
          <div className="flex flex-wrap gap-2">
            {dayanakOkunur && engelVar && dayanak === null && (
              <Button
                variant="outlined"
                icon="visibility"
                disabled={okunuyor}
                onClick={() => void dayanagiOku()}
              >
                {DUGME_DAYANAK}
              </Button>
            )}
            {eylemler.map((eylem) => (
              <Button
                key={eylem}
                variant={eylem === "iptal" ? "text" : "tonal"}
                icon={ETIKETLER[eylem][1]}
                onClick={() => onEylem(eylem)}
              >
                {ETIKETLER[eylem][0]}
              </Button>
            ))}
          </div>
        )}
      </div>
    </Dialog>
  );
}
