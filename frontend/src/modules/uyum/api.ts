// Gerekçe kutusunun yarım metni — backend `apps/oab/views.DraftTextView` (`/oab/drafts/`) ile BİREBİR
// (tasarım §7 "Yarım kalan metin"; plan F1c 3. adım notları). Oturumdaki hesabın tek, şifreli kaydıdır:
// tarayıcı deposunda TUTULMAZ (`hooks/useAutosave`: kişisel veri taşıyabilir). Yarım metin yoksa sunucu
// 204 döner. Panodaki "yarım kalan taslak" kalemi F1c'nin 12. adımındadır.

import { api } from "../../lib/api";

export interface YarimMetin {
  metin: string;
  /** Kutunun bağlamı (ör. `gecis.karar_defteri`): aynı kutu açılınca metin geri getirilir. */
  baglam: string;
  guncelleme: string;
}

export const yarimMetinApi = {
  /** Oturumdaki hesabın yarım metni; yoksa null. */
  oku: async (): Promise<YarimMetin | null> =>
    (await api.get<YarimMetin | undefined>("/oab/drafts/", { etkinlik: false })) ?? null,
  /** Yazar; boş metin kaydı siler. */
  kaydet: (metin: string, baglam: string): Promise<void> =>
    api.put<void>("/oab/drafts/", { metin, baglam }),
  /** Yalnız bu bağlamın kaydını siler (başka kutunun yarım metni kalır). Bağlam kişisiz bir kutu adıdır. */
  temizle: (baglam: string): Promise<void> =>
    api.del<void>(`/oab/drafts/?baglam=${encodeURIComponent(baglam)}`),
};
