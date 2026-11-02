// Genel Bakış'ta "Hesaplar ve Güvenlik Dosyası" kartı — iki depo farkı (tasarım §4.6.1
// kural 4; plan F1b-1 "Denetim izi"). Hesapların parolaları bu bilgisayarın güvenlik
// dosyasında, rolleri ve durumları veritabanındadır; ikisi uyuşmazsa (çoğunlukla yedekten
// geri yüklemeden sonra) fark burada listelenir:
//
// * Kaydı açık ama güvenlik dosyasında parolası olmayan hesaplar: sahipleri giriş yapamaz;
//   program geri yüklemeden sonraki ilk girişte onları "parola yenilenmeli" durumuna çekti,
//   program yöneticisi yeniden geçici parola verir.
// * Kaydı olmayan ya da kapalı hesapların güvenlik dosyasında kalan parola kayıtları. Kaydı
//   OLMAYAN hesabınki yalnız program yöneticisinin ONAYIYLA silinir (onay diyaloğu → `POST
//   security/integrity/orphan-wraps/`; her silme denetim izine `HESAP` satırı olarak düşer).
//   KAPALI hesabınkini program her kilit açılışında kendisi siler (backend `app_password.
//   _cleanup_closed_wraps`, tasarım §4.6.1 kural 3); listede yalnız o silme tamamlanamadıysa
//   (ör. dosyayı başka bir program tutuyordu) görünür, onayla hemen de silinebilir. Metin bu
//   ikisini ayırır. Kart yanıttaki güncel iki depo kartıyla yenilenir.
// * Kaydı program dışından değiştirilmiş görünen hesaplar: program onlara dokunmaz.
//
// ROL: ilk iki liste ve silme yalnız program yöneticisindedir (`security/integrity/two-store/`;
// tasarım §4.6.1 kural 4); mührü tutmayan hesaplar denetim kartlarından gelir ve Denetleme
// Kurulunda da görünür (kural 1). Öteki rollerde liste boş gelir, kart çizilmez.
//
// "Sarmal" kullanıcı metnine girmez: kullanıcıdaki adı hesabın güvenlik dosyasındaki
// **parola kaydı**dır (sözlük §1 "Denetim izi"). Hesaplar rol etiketi ve tanıtıcıyla anılır;
// ad-soyad yok.

import { useState } from "react";

import Button from "../../ui/Button";
import { useConfirm } from "../../ui/ConfirmProvider";
import ErrorBand, { hataOku } from "../../ui/ErrorBand";
import type { SayfaHatasi } from "../../ui/ErrorBand";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { butunlukApi } from "./api";
import type { IkiDepoFarki, IkiDepoHesabi, IkiDepoYaniti } from "./api";
import KartKabugu from "./KartKabugu";
import { IKI_DEPO_KARTI_BASLIGI, hesapEtiketi } from "./metinler";

/** Onay diyaloğunun başlığı (soru) — sözlük §3, §4.3. */
export const SILME_ONAY_BASLIGI = "Parola kaydı güvenlik dosyasından silinsin mi?";

/**
 * "Güvenlik dosyasında kalan eski parola kayıtları"nın açıklaması: listede hangi nedenler
 * varsa onların cümlesi (kapalı hesabınkini program kendisi siler; kaydı olmayanınkini
 * silmez) + onay cümlesi (sözlük §4.5).
 */
export function eskiKayitlarAciklamasi(hesaplar: readonly IkiDepoHesabi[]): string {
  const cumleler: string[] = [];
  if (hesaplar.some((h) => h.kapali)) {
    cumleler.push(
      "Kapalı hesapların parola kaydını program her kilit açılışında kendisi siler; burada " +
        "görünen kaydın silinmesi tamamlanamadı (ör. dosyayı başka bir program tutuyordu), bir " +
        "sonraki kilit açılışında yinelenir.",
    );
  }
  if (hesaplar.some((h) => !h.kapali)) {
    cumleler.push(
      "Veritabanında kaydı olmayan hesapların parola kaydını program kendiliğinden silmez.",
    );
  }
  cumleler.push("Program yöneticisi onaylarsa hemen silinir.");
  return cumleler.join(" ");
}

/** Silinecek kaydın nedeni: hesap kapalı ya da veritabanında kaydı yok. */
function neden(hesap: IkiDepoHesabi): string {
  return hesap.kapali ? "hesap kapalı" : "veritabanında kaydı yok";
}

/** Onay diyaloğunun gövdesi: sonuç (başlık soru, gövde sonuç — sözlük §3). */
export function silmeSonucu(hesap: IkiDepoHesabi): string {
  const ad = hesap.tanitici === null ? "Bu hesabın" : `“${hesap.tanitici}” tanıtıcılı hesabın`;
  return (
    `${ad} parola kaydı bu bilgisayarın güvenlik dosyasından ve arşiv kopyalarından silinir; ` +
    "tanıtıcı kilit ekranından kalkar ve onunla bir daha giriş yapılamaz. Silme denetim izine " +
    "yazılır ve geri alınamaz."
  );
}

/**
 * Satırın silme düğmesinin erişilebilir adı: HANGİ hesabın kaydı silinecek (sözlük §5
 * "eylemde belirtme hâliyle"; onay diyaloğuyla aynı anılış). Görünür metin "Güvenlik
 * dosyasından sil" adın içinde kalır (WCAG 2.5.3). Birden çok sahipsiz kayıt olduğunda ekran
 * okuyucunun düğme listesi onları birbirinden ayırır; silme geri alınamaz.
 */
export function silDugmesiAdi(hesap: IkiDepoHesabi): string {
  const kimin = hesap.tanitici === null ? "Bu hesabın" : `“${hesap.tanitici}” tanıtıcılı hesabın`;
  return `${kimin} parola kaydını güvenlik dosyasından sil`;
}

function HesapListesi({ hesaplar }: { hesaplar: readonly IkiDepoHesabi[] }) {
  return (
    <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
      {hesaplar.map((h) => (
        <li key={h.id}>{hesapEtiketi(h)}</li>
      ))}
    </ul>
  );
}

interface IkiDepoKartiProps {
  fark: IkiDepoFarki;
  /** Silmeden dönen güncel iki depo kartı (`useButunlukDurumu.ikiDepoyuYaz`). */
  onIkiDepo: (yanit: IkiDepoYaniti) => void;
}

export default function IkiDepoKarti({ fark, onIkiDepo }: IkiDepoKartiProps) {
  const confirm = useConfirm();
  const snackbar = useSnackbar();
  const [silinen, setSilinen] = useState<string | null>(null);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);

  if (!fark.fark_var) return null;

  const sil = async (hesap: IkiDepoHesabi) => {
    const onay = await confirm({
      title: SILME_ONAY_BASLIGI,
      message: silmeSonucu(hesap),
      confirmLabel: "Sil",
    });
    if (!onay) return;
    setSilinen(hesap.id);
    setHata(null);
    try {
      onIkiDepo(await butunlukApi.sahipsizSarmallariSil([hesap.id]));
      snackbar.success("Parola kaydı güvenlik dosyasından silindi.");
    } catch (e) {
      setHata(hataOku(e, "Parola kaydı silinemedi."));
    } finally {
      setSilinen(null);
    }
  };

  return (
    <KartKabugu id="iki-depo-karti" baslik={IKI_DEPO_KARTI_BASLIGI} ikon="sync_problem" ton="uyari">
      <p className="text-body-medium text-on-surface">
        Bu bilgisayarın güvenlik dosyasındaki hesaplarla veritabanındaki hesap kayıtları uyuşmuyor.
        Bu çoğunlukla yedekten geri yüklemeden sonra olur.
      </p>
      {fark.sarmalsiz_hesaplar.length > 0 && (
        <div className="space-y-1">
          <h3 className="text-title-small font-semibold text-on-surface">
            Giriş yapamayan hesaplar
          </h3>
          <p className="text-body-small text-on-surface-variant">
            Bu hesapların parolası güvenlik dosyasında yok; sahipleri giriş yapamaz. Program
            yöneticisinin bu hesaplara yeniden geçici parola vermesi gerekir.
          </p>
          <HesapListesi hesaplar={fark.sarmalsiz_hesaplar} />
        </div>
      )}
      {fark.silinebilir_sarmallar.length > 0 && (
        <div className="space-y-1">
          <h3 className="text-title-small font-semibold text-on-surface">
            Güvenlik dosyasında kalan eski parola kayıtları
          </h3>
          <p className="text-body-small text-on-surface-variant">
            {eskiKayitlarAciklamasi(fark.silinebilir_sarmallar)}
          </p>
          <ul className="space-y-2">
            {fark.silinebilir_sarmallar.map((h) => (
              <li key={h.id} className="flex flex-wrap items-center justify-between gap-2">
                <span className="min-w-0 text-body-medium text-on-surface">
                  {hesapEtiketi(h)} · {neden(h)}
                </span>
                <Button
                  variant="outlined"
                  icon="delete"
                  onClick={() => void sil(h)}
                  disabled={silinen !== null}
                  aria-label={silDugmesiAdi(h)}
                >
                  {silinen === h.id ? "Siliniyor…" : "Güvenlik dosyasından sil"}
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {fark.muhru_tutmayan.length > 0 && (
        <div className="space-y-1">
          <h3 className="text-title-small font-semibold text-on-surface">
            Kaydı değiştirilmiş görünen hesaplar
          </h3>
          <p className="text-body-small text-on-surface-variant">
            Bu hesapların kaydı program dışından değiştirilmiş görünüyor; program onlara dokunmaz.
            Durumu Denetleme Kuruluna bildirin.
          </p>
          <HesapListesi hesaplar={fark.muhru_tutmayan} />
        </div>
      )}
      {hata && <ErrorBand hata={hata} />}
    </KartKabugu>
  );
}
