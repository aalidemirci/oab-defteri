// Kullanım Kılavuzu — statik içerik, çevrimdışı. Kabuk bileşenleri `KilavuzKabugu`'ndadır.
// Aile iskeletinin kütüphane kılavuzu F1a-2'de silindi; OAB'nin bölümleri her fazın
// özellikleriyle birlikte yazılır (tasarım §14). Bugün yalnız programın konumunu
// anlatan bölüm vardır (CLAUDE.md §1: konum cümlesi kılavuzda da yer alır).

import Card from "../../ui/Card";
import { Ekran, KilavuzBolumu, useCapayaKaydir } from "./KilavuzKabugu";

/** Bölümler (çapa → başlık + ikon), sayfadaki sırasıyla. Başlıklar Başlık Düzenindedir. */
const BOLUMLER = {
  "programin-konumu": { baslik: "Programın Konumu", ikon: "info" },
} as const;

type BolumId = keyof typeof BOLUMLER;

/** "Bu kılavuzda" listesi — bölüm çapaları ve başlıklar tek kaynaktan (test de okur). */
export const KILAVUZ_BOLUMLERI: ReadonlyArray<{ id: BolumId; baslik: string }> = (
  Object.keys(BOLUMLER) as BolumId[]
).map((id) => ({ id, baslik: BOLUMLER[id].baslik }));

export default function KilavuzPage() {
  useCapayaKaydir();
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header>
        <p className="text-label-medium font-semibold tracking-wide text-primary">OAB Defteri</p>
        <h1 className="mt-1 text-headline-medium font-semibold tracking-tight text-on-surface">
          Kullanım Kılavuzu
        </h1>
        <p className="mt-2 text-body-medium text-on-surface-variant">
          OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten çevrimdışı bir
          programdır; veriler yalnız bu bilgisayarda durur. Kılavuz, programa yeni özellikler
          geldikçe genişler.
        </p>
      </header>

      <Card className="p-5 sm:p-6">
        <nav aria-label="Kılavuz bölümleri">
          <p className="text-label-large font-semibold text-on-surface">Bu kılavuzda</p>
          <ol className="mt-2 grid list-decimal gap-x-8 gap-y-1 pl-5 text-body-medium sm:grid-cols-2">
            {KILAVUZ_BOLUMLERI.map((b) => (
              <li key={b.id}>
                <a
                  href={`#${b.id}`}
                  className="font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  {b.baslik}
                </a>
              </li>
            ))}
          </ol>
        </nav>
      </Card>

      <KilavuzBolumu id="programin-konumu" {...BOLUMLER["programin-konumu"]}>
        <p>
          Program <strong>karar defterinin ve TEFBİS&apos;in yerine geçmez.</strong> Karar defterine
          kararlar el ile yazılır ve defter noter tasdiklidir; birliğin gelir-gider kayıtlarını
          TEFBİS&apos;e okul idaresi girer. Program bunlara girilecek metni ve listeyi hazırlar,
          tutarlılığı denetler.
        </p>
        <p>
          İlk kurulum adımları için <Ekran to="/kurulum">Kurulum Sihirbazı</Ekran>&apos;nı açın.
        </p>
      </KilavuzBolumu>
    </div>
  );
}
