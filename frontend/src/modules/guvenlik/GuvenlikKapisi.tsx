// Güvenlik kapısı — hesap kuruluysa ve oturum açık değilse içerik yerine kilit ekranını;
// güvenlik dosyası kayıpsa (guvenlik.json silinmiş ya da yeniden adlandırılmış ya da içi
// bozuk) ayrı bir "güvenlik dosyası kayıp" ekranını gösterir. `KurulumKapisi` ile aynı
// desendedir, dört farkla:
//
// 1. Kilit ve açılış YEREL durumla değil, pencerenin yeniden yüklenmesiyle olur (tasarım
//    §4.4.3 "Ön yüz belleği", §13 D53; `lib/kilit.ts`): Kilitle, boşta kilit ve ön yüz
//    oturumu açık sanırken gelen 423 pencereyi yeniden yükler; kapı yeni pencerede durumu
//    sunucudan okur. Kapı okuduğu durumla "açık sanma" bayrağını yazar (döngü koruması).
//    Ön yüz kilitli olduğunu bilirken gelen 423 (`od:kilit-kapisi`; ör. kilit ekranı
//    açıkken güvenlik dosyası kayboldu) durumu yeniden okutur.
// 2. Hesap hiç kurulmamışsa kapı içeriği gösterir: kullanıcıyı sihirbazın ilk adımına
//    İÇTEKİ `KurulumKapisi` götürür. Bu kapı "parolasız kip" sunmaz (tasarım §4.4.3).
// 3. FAIL-OPEN'dır: durum ucu okunamazsa içeri alır. Gerçek kapı BACKEND'dedir
//    (`apps.okul.lock_middleware` → 423 `locked` / `guvenlik_dosyasi_kayip`) — burada
//    ikinci kez kilitlemek, uç hatasında kullanıcıyı kilit ekranına hapsetmek olurdu.
//    Okunamayan durum bayrağı KALDIRMAZ: okunamayan durum + 423 sonsuz yüklemeye dönmesin.
// 4. Görevli kipi yoktur (tasarım TK14): oturum açıkken içerik, kapalıyken kilit ekranı.

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { KILIT_KAPISI_OLAYI, oturumAcikSan } from "../../lib/kilit";
import { SkeletonList } from "../../ui/Skeleton";
import GuvenlikDosyasiKayip from "./GuvenlikDosyasiKayip";
import KilitEkrani from "./KilitEkrani";
import { guvenlikApi } from "./api";
import type { GuvenlikDurumu } from "./api";

/** Durum ucu okunamadığında kullanılan açık durum (fail-open — dosya başı notu). */
export const OKUNAMADI: GuvenlikDurumu = {
  password_set: false,
  locked: false,
  security_file_missing: false,
  reset_available: false,
  transition_pending: false,
  transition: "",
  recovery_key_confirmed: false,
  protected_fields: [],
  account_count: 0,
  recovery_key_no: null,
  recovery_key_date: null,
  corrupt_field_count: 0,
};

/** Okunan durum oturumun açık olduğunu mu söylüyor? (Hesap kurulu, kilit yok, dosya yerinde.) */
export function oturumAcikMi(d: GuvenlikDurumu): boolean {
  return d.password_set && !d.locked && !d.security_file_missing;
}

export default function GuvenlikKapisi({ children }: { children: ReactNode }) {
  const [durum, setDurum] = useState<GuvenlikDurumu | null>(null);

  const oku = useCallback(() => {
    let iptal = false;
    guvenlikApi
      .durum()
      .then((d) => {
        if (iptal) return;
        oturumAcikSan(oturumAcikMi(d));
        setDurum(d);
      })
      .catch(() => {
        if (!iptal) setDurum(OKUNAMADI);
      });
    return () => {
      iptal = true;
    };
  }, []);

  useEffect(() => oku(), [oku]);

  // 423 (ön yüz kilitli olduğunu bilirken): hangi kilidin kapandığını sunucu söyler.
  useEffect(() => {
    const dinleyici = () => void oku();
    window.addEventListener(KILIT_KAPISI_OLAYI, dinleyici);
    return () => window.removeEventListener(KILIT_KAPISI_OLAYI, dinleyici);
  }, [oku]);

  if (durum === null) return <SkeletonList rows={3} className="mx-auto max-w-3xl" />;

  // Kayıp dosya kilit ekranından ÖNCE gelir: dosya yokken hesap sarmalları da yoktur,
  // kilit ekranındaki hiçbir parola kabul edilmezdi.
  if (durum.security_file_missing) {
    return (
      <GuvenlikDosyasiKayip
        sifirlanabilir={durum.reset_available}
        onYenidenDenetle={() => void oku()}
      />
    );
  }

  if (durum.locked) return <KilitEkrani />;

  return <>{children}</>;
}
