// Kilitle eylemi — üst çubuktaki düğme ve kısayolu (Ctrl+Shift+L) ile Ayarlar → Güvenlik
// aynı yoldan kilitler (tasarım §4.4.3, TK14; plan F1b-1 "Oturum"). "Kullanıcı değiştir"
// ayrı bir eylem değildir: Kilitle + başka hesapla açmaktır.
//
// * Kilit pencereyi yeniden yükler (tasarım §13 D53; `eylemler.oturumuKilitle`).
// * Doğrulanmamış kurtarma anahtarı bellekte bekliyorsa (sihirbazın 1. adımı ya da
//   Ayarlar → Güvenlik'te yenilenmiş anahtar) ÖNCE sorulur: yükleme anahtarı ekrandan
//   kaldırır, bir daha gösterilemez; sonra kâğıttaki anahtar doğrulanır ya da yenisi
//   üretilir (plan F1b-1; `guvenlik/bekleyenAnahtar`). Sihirbazda iki grup tutup sunucu
//   damgayı yazdıysa ("Devam"a basılmamış olsa da) sorulmaz: anahtar doğrulanmıştır,
//   yüklemeden sonra sihirbaz onu yeniden istemez (`kilitlemedenOnceSorulmali`).
// * Uzun iş sürüyorsa sunucu kilidi erteler: ekran "İşlem bitince kilitlenecek" der
//   (oturum yeniden okunur, gösterge `kilit_bekliyor`u gösterir), iş bitince yoklama
//   kilidi görür.

import { useCallback, useRef } from "react";

import { useConfirm } from "../../ui/ConfirmProvider";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { kilitlemedenOnceSorulmali } from "../guvenlik/bekleyenAnahtar";
import { oturumuKilitle } from "./eylemler";
import { oturumHataMetni } from "./hatalar";

/** Kilitle'nin kısayolu (ipucu metni; sözlük §1 "Kilit ve çıkış"). */
export const KILITLE_KISAYOLU = "Ctrl+Shift+L";
/** `aria-keyshortcuts` biçimi. */
export const KILITLE_KISAYOLU_ARIA = "Control+Shift+L";

/** Kilit ertelendiğinde (uzun iş) ekrana yazılan cümle. */
export const KILIT_BEKLIYOR_METNI = "İşlem bitince kilitlenecek";

/** Doğrulanmamış anahtar ekrandayken Kilitle'nin sorusu (başlık soru, gövde sonuç; sözlük §3). */
export const BEKLEYEN_ANAHTAR_SORUSU = {
  title: "Program kilitlensin mi?",
  message:
    "Kurtarma anahtarının saklandığı henüz doğrulanmadı. Kilitleyince pencere yeniden " +
    "yüklenir ve anahtar ekrandan kalkar; bir daha gösterilmez. Sonra sakladığınız " +
    "kâğıttaki anahtarı doğrulamanız ya da yenisini üretmeniz gerekir.",
  confirmLabel: "Kilitle",
};

/** Ctrl+Shift+L mi? (Alt ve Meta'sız; tarayıcı/WebView2 kısayollarıyla çakışmasın.) */
export function kilitleKisayoluMu(e: KeyboardEvent): boolean {
  return e.ctrlKey && e.shiftKey && !e.altKey && !e.metaKey && (e.key === "L" || e.key === "l");
}

/** Kilitle işlevi (dosya başı notu); iki kez basılırsa ikinci istek gitmez. */
export function useKilitle(): () => Promise<void> {
  const confirm = useConfirm();
  const snackbar = useSnackbar();
  const suruyor = useRef(false);

  return useCallback(async () => {
    if (suruyor.current) return;
    suruyor.current = true;
    try {
      if (kilitlemedenOnceSorulmali() && !(await confirm(BEKLEYEN_ANAHTAR_SORUSU))) {
        return;
      }
      const sonuc = await oturumuKilitle();
      if (sonuc?.sonuc === "ertelendi") snackbar.show(`${KILIT_BEKLIYOR_METNI}.`);
    } catch (err) {
      snackbar.error(oturumHataMetni(err, "Kilitlenemedi."));
    } finally {
      suruyor.current = false;
    }
  }, [confirm, snackbar]);
}
