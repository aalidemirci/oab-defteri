// Kullanıcılar satırının bir eylemi: düğme + yapılamıyorsa SUNUCUNUN nedeni (plan F1b-2
// "Sözleşme": eylemleri sunucu hesaplar, ön yüz yalnız eşler). Neden düğmenin yanında görünür metin
// olarak durur ve düğmeye `aria-describedby` ile bağlıdır (kapalı düğme odak almaz; nedeni yalnız
// ipucunda bırakmak klavye ve ekran okuyucu kullanıcısından gizlerdi). Aynı nedeni paylaşan
// düğmeler için neden bir kez yazılır: çağıran `ortakNedenId` verir, düğme kendi nedenini çizmez.

import { useId } from "react";

import Button from "../../ui/Button";
import type { EylemDurumu } from "./api";

interface EylemDugmesiProps {
  durum: EylemDurumu;
  etiket: string;
  /** İstek sürerken düğmenin etiketi ("Hazırlanıyor…"). */
  calisiyorEtiketi?: string;
  calisiyor?: boolean;
  /** Başka bir eylem sürüyor: düğme kapalı, etiket değişmez. */
  mesgul?: boolean;
  ikon: string;
  variant?: "filled" | "tonal" | "outlined" | "text";
  onClick: () => void;
  /** Ortak nedenin öğesi verilirse düğme kendi nedenini çizmez, ona bağlanır. */
  ortakNedenId?: string;
}

export default function EylemDugmesi({
  durum,
  etiket,
  calisiyorEtiketi,
  calisiyor = false,
  mesgul = false,
  ikon,
  variant = "outlined",
  onClick,
  ortakNedenId,
}: EylemDugmesiProps) {
  const nedenId = useId();
  const neden = durum.yapilabilir ? null : durum.neden;
  const aciklayan = neden === null ? undefined : (ortakNedenId ?? nedenId);
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
      <Button
        type="button"
        variant={variant}
        icon={ikon}
        className="shrink-0 self-start"
        onClick={onClick}
        disabled={!durum.yapilabilir || calisiyor || mesgul}
        aria-describedby={aciklayan}
      >
        {calisiyor && calisiyorEtiketi ? calisiyorEtiketi : etiket}
      </Button>
      {neden !== null && ortakNedenId === undefined && (
        <p id={nedenId} className="text-body-small text-on-surface-variant">
          {neden}
        </p>
      )}
    </div>
  );
}
