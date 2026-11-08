// Kişiler sayfasının ortak parçaları: durum rozeti ("Ayrıldı · gg.aa.yyyy",
// "Ayrılış kararı bekliyor"), Ayrılış Havuzu'nun adresi ve çözülemeyen şifreli alanın
// "okunamadı" işareti. Sayfa (KisilerPage), aktarım paneli (AktarimPaneli) ve Ayrılış
// Havuzu (AyrilisHavuzu) paylaşır.
//
// "OKUNAMADI" (tasarım TK8 (3), §13 D48; plan F1b-1 "Denetim izi"): kilit açıkken
// çözülemeyen şifreli alan API'de `null` gelir ve kaydın `bozuk_alanlar` listesinde
// adıyla durur (ad ya da soyad bozuksa türeyen `full_name` de `null`dır). Ekran o alanı
// BOŞ HÜCRE olarak göstermez — "veri yok" ile "veri okunamadı" karışmasın — yerine
// "okunamadı" yazar. Kişinin adı hiçbir yerde tahmin edilmez; metinde "adı okunamayan
// kayıt" denir. Genel Bakış'taki "Okunamayan Kayıt Alanları" kartı sayıyı söyler.
//
// Hata bandı ve `hataOku` aile iskeletinde `ui/ErrorBand`'e taşındı; buradan yeniden
// dışa verilir, çağrı yerleri değişmedi.

import { formatDate } from "../../lib/format";
import Icon from "../../ui/Icon";
import { KAYNAK_DOSYA_HATIRLATMASI } from "./metinler";

export { default as ErrorBand, hataOku, PAROLA_GEREKLI_KODU } from "../../ui/ErrorBand";
export type { SayfaHatasi } from "../../ui/ErrorBand";

/** Ayrılış Havuzu sekmesinin adresi (Kişiler → `?tab=havuz`). */
export const HAVUZ_ADRESI = "/kisiler?tab=havuz";

/** Çözülemeyen şifreli alanın ekrandaki karşılığı (sözlük §1 "Şifreleme"). */
export const OKUNAMADI_METNI = "okunamadı";

/** `bozuk_alanlar` taşıyan kayıt (backend `CorruptFieldsMixin`; yoksa alan bozuk değildir). */
export interface BozukAlanli {
  bozuk_alanlar?: string[];
}

/** Kaydın verilen alanlarından biri çözülemedi mi? */
export function okunamadiMi(kayit: BozukAlanli, ...alanlar: string[]): boolean {
  const bozuk = kayit.bozuk_alanlar ?? [];
  return alanlar.some((alan) => bozuk.includes(alan));
}

/** Ad-soyad okunamıyor mu? (`full_name` ad ve soyaddan türer.) */
export function adOkunamadi(kayit: BozukAlanli & { full_name: string | null }): boolean {
  return kayit.full_name === null || okunamadiMi(kayit, "first_name", "last_name", "full_name");
}

/** Hücrede ve ayrıntıda "okunamadı" işareti (renk tek başına anlam taşımaz: metin de var). */
export function OkunamadiIsareti() {
  return (
    <span className="inline-flex items-center gap-1 italic text-error">
      <Icon name="error" size="sm" />
      {OKUNAMADI_METNI}
    </span>
  );
}

/** Kişinin ad hücresi: ad-soyad ya da "okunamadı". */
export function KisiAdi({ kayit }: { kayit: BozukAlanli & { full_name: string | null } }) {
  return adOkunamadi(kayit) ? <OkunamadiIsareti /> : <>{kayit.full_name}</>;
}

/** Metin içinde (erişilebilir ad) kişinin adı: okunamazsa "Adı okunamayan kayıt". */
export function kisiAdiMetni(kayit: BozukAlanli & { full_name: string | null }): string {
  return adOkunamadi(kayit) ? "Adı okunamayan kayıt" : (kayit.full_name ?? "");
}

/**
 * Eylem adındaki belirtme hâli (erişilebilir ad): "Ad Soyad kaydını" ya da "Adı okunamayan
 * kaydı" — `kisiAdiMetni` + " kaydını" okunamayanda "kayıt kaydını" ikilemesi kurardı.
 */
export function kisiKaydiniMetni(kayit: BozukAlanli & { full_name: string | null }): string {
  return adOkunamadi(kayit) ? "Adı okunamayan kaydı" : `${kayit.full_name ?? ""} kaydını`;
}

/**
 * Onay diyaloğundaki özne: “Ad Soyad” ya da "Adı okunamayan bu kayıt"; `kaydi` verilirse
 * "“Ad Soyad” kaydı" biçimi (okunamayanda yine "Adı okunamayan bu kayıt").
 */
export function kisiOznesi(
  kayit: BozukAlanli & { full_name: string | null },
  kaydi = false,
): string {
  if (adOkunamadi(kayit)) return "Adı okunamayan bu kayıt";
  return kaydi ? `“${kayit.full_name}” kaydı` : `“${kayit.full_name}”`;
}

/**
 * Sicil durum rozeti: aktif kişide "Aktif", ayrılmışta "Ayrıldı · gg.aa.yyyy".
 * Ayrılış havuzundaki (aktif) kişide ek rozet: "Ayrılış kararı bekliyor".
 */
export function DurumRozeti({
  aktif,
  leftAt,
  havuzda = false,
}: {
  aktif: boolean;
  leftAt: string | null;
  havuzda?: boolean;
}) {
  if (aktif && havuzda) {
    return (
      <span className="inline-flex flex-wrap items-center gap-2">
        <span>Aktif</span>
        <span className="inline-flex items-center gap-1 rounded-full bg-tertiary-container px-2 py-0.5 text-label-medium text-on-tertiary-container">
          <Icon name="pending_actions" size="sm" />
          Ayrılış kararı bekliyor
        </span>
      </span>
    );
  }
  if (aktif) return <span>Aktif</span>;
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-surface-container-highest px-2 py-0.5 text-label-medium text-on-surface-variant">
      <Icon name="logout" size="sm" />
      {leftAt ? `Ayrıldı · ${formatDate(leftAt)}` : "Ayrıldı"}
    </span>
  );
}

/**
 * Aktarım dosyayla başarıyla bitince kaynak dosyanın silinmesini hatırlatır (genel tasarım §4.3
 * tehdit 15: içe aktarılan liste diskte kalır; program kalanını koruyamaz). Personel ve veli
 * listesi aktarım panelleri gösterir.
 */
export function KaynakDosyaHatirlatmasi() {
  return (
    <div
      role="note"
      className="flex items-start gap-2 rounded-shape-sm bg-secondary-container px-4 py-3 text-body-medium text-on-secondary-container"
    >
      <Icon name="delete_sweep" size="lg" className="mt-0.5 shrink-0" />
      <span>{KAYNAK_DOSYA_HATIRLATMASI}</span>
    </div>
  );
}
