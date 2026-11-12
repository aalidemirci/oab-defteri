// Kılavuz bölümü: Programın Konumu (çapa `programin-konumu`). Başlık, ikon ve sıra
// `KilavuzPage`'deki `BOLUMLER`'dedir. Konum cümlesi CLAUDE.md §1'dedir (bağlayıcı); kılavuzda
// md. 13/5, 23/2 ve 23/5 yazılır (tasarım §3.1, risk tablosu R2). Alıntılar
// `docs/mevzuat/meb-okul-aile-birligi-yonetmeligi.md` ile birebirdir.

import { YONETMELIK } from "../../../lib/mevzuat";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, KilavuzBolumu, Mevzuat } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/**
 * Sihirbazı açamayan rolde konum bölümünün son cümlesi (sözlük §1 "Rol süzmesi"; kullanıcı
 * kararı 04.11.2026).
 */
export const KILAVUZ_SIHIRBAZ_KAPALI_METNI =
  "İlk kurulum adımları Kurulum Sihirbazı'ndadır; girilen bilgiler Ayarlar'da görünür.";

export default function PrograminKonumu(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program <strong>karar defterinin ve TEFBİS&apos;in yerine geçmez.</strong> Karar defterine
        kararlar el ile yazılır ve defter noter tasdiklidir; birliğin gelir-gider kayıtlarını
        TEFBİS&apos;e okul idaresi girer. Program bunlara girilecek metni ve listeyi hazırlar,
        tutarlılığı denetler.
      </p>
      <p>
        Bunun dayanağı {YONETMELIK}&apos;nin (bu kılavuzda kısaca Yönetmelik; yalnız “md.” yazan
        atıflar bu Yönetmeliğindir) şu hükümleridir:
      </p>
      <Mevzuat kaynak="Yönetmelik md. 13/5">
        Yönetim kurulu kararları, karar defterine el ile yazılarak imzalanır.
      </Mevzuat>
      <Mevzuat kaynak="Yönetmelik md. 23/2">
        Yönetim kurulunca, yönetim kurulu karar defterinin noterce tasdik edilmesi zorunlu olup
        diğer defter ve belgeler ise birliğin bağlı bulunduğu il/ilçe millî eğitim müdürlüğünce
        tasdik edilir.
      </Mevzuat>
      <Mevzuat kaynak="Yönetmelik md. 23/5">
        Okul idaresi, okul-aile birliklerinin gelir ve gider kayıtları ile diğer mali işlemlerini
        Bakanlıkça kurulan merkezî bilgi sistemine (TEFBİS) kaydeder.
      </Mevzuat>
      <AltBaslik>Günlük işte ne demek</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          Yönetim kurulunun kararı, karar defterine el ile yazılıp imzalanır. Programdaki hiçbir
          kayıt ve programdan alınan hiçbir çıktı, defterdeki yazının ve imzanın yerini almaz.
        </li>
        <li>Noter tasdiki karar defteri içindir; program tasdikli defter sayılmaz.</li>
        <li>
          TEFBİS&apos;e girişi okul idaresi yapar. Program TEFBİS&apos;e bağlanmaz, oraya
          kendiliğinden kayıt yazmaz.
        </li>
      </ul>
      <p>
        Hangi ekranların açık olduğu hesabınızın rolüne göre değişir; açamadığınız bir ekran için
        program yöneticisine başvurun.
      </p>
      {/* Sihirbaz yalnız kurulumu tamamlayabilen hesaba açıktır (kullanıcı kararı 04.11.2026);
          öteki rollerde adı bağlantı değildir, rotası onları kapalı ekrana götürürdü. */}
      {yetki.acik("kurulum_tamamlama") ? (
        <p>
          İlk kurulum adımları için <Ekran to="/kurulum">Kurulum Sihirbazı</Ekran>&apos;nı açın.
        </p>
      ) : (
        <p>{KILAVUZ_SIHIRBAZ_KAPALI_METNI}</p>
      )}
    </KilavuzBolumu>
  );
}
