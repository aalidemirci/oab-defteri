// Kılavuz bölümü: Güncelleme (çapa `guncelleme`). Başlık, ikon ve sıra `KilavuzPage`'dedir. Ekran
// adları `guncelleme/UpdatePanel.tsx`, `UpdateBanner.tsx` ve sözlük §4.7'den; güncelleme öncesi
// yedek `desktop/main.py` (`_goc_oncesi_yedegi_al`, yalnız bekleyen veri düzenlemesi varken).
// Programın ilk kurulumu bu bölümde değildir.

import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Kod } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function Guncelleme(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program kendiliğinden güncellenmez ve açılışta internete çıkmaz. Yeni sürüm yalnız “Şimdi
        denetle” düğmesine basıldığında denetlenir; bu istek kişisel veri taşımaz.
      </p>
      {yetki.acik("guncelleme") ? (
        <>
          <AltBaslik>Yeni sürüm var mı diye bakmak ve kurmak</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <Ekran to="/ayarlar?tab=guncelleme">Ayarlar → Güncelleme</Ekran>&apos;yi açın, “Şimdi
              denetle” düğmesine basın. “Kurulu sürüm” ve “Yayımlanan son sürüm” yan yana yazar.
              “Uygulama güncel.” görürseniz yapacak iş yoktur.
            </li>
            <li>
              “Yeni sürüm hazır” görürseniz Windows&apos;ta “Doğrula ve indir” düğmesine basın ve
              kurulum dosyasını kaydedeceğiniz yeri seçin. Dosya, bütünlüğü doğrulanmadan indirmeye
              sunulmaz.
            </li>
            <li>İndirme bitince programı kapatın ve indirdiğiniz kurulum dosyasını çalıştırın.</li>
            <li>Programı yeniden açıp kilit ekranından girin.</li>
          </ol>
          <p>
            Verileriniz kurulum klasörünün dışında tutulduğu için korunur. Denetim yeni sürüm
            bulduysa başka ekranlara geçtiğinizde üstte bir bant hatırlatır; “Daha sonra” düğmesi
            bandı o sürüm için kapatır.
          </p>

          <AltBaslik>Pardus&apos;ta güncellemek</AltBaslik>
          <p>
            Pardus ve Linux&apos;ta indirme düğmesi yoktur, güncelleme paketle yapılır: yeni sürümün{" "}
            <Kod>.deb</Kod> (ya da <Kod>.tar.gz</Kod>) dosyasını okulapp.org/oab-defteri sayfasından
            alıp eski sürümün üzerine kurun.
          </p>

          <AltBaslik>Okul ağı denetimi engelliyorsa</AltBaslik>
          <p>
            “Güncelleme sunucusuna ulaşılamadı; okul ağında engellenmiş olabilir.” diye başlayan
            ileti çıkarsa ekrandaki okulapp.org/oab-defteri bağlantısını açın. Bağlantı tarayıcıda
            açılır; yeni sürümü ve kurulum dosyalarını oradan görürsünüz, dosyalar
            indir.okulapp.org&apos;dan iner.
          </p>
        </>
      ) : (
        <p>
          Yeni sürümü program yöneticisi denetler ve kurar; güncelleme için program yöneticisine
          başvurun.
        </p>
      )}

      <AltBaslik>Güncellemeden sonraki ilk açılış</AltBaslik>
      <p>
        Yeni sürüm kayıtlarda düzenleme gerektiriyorsa program, kayıtlara dokunmadan önce
        kendiliğinden bir güncelleme öncesi yedek alır (
        <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran>). Bu yedek
        alınamazsa program veriyi korumak için açılmaz: diskte yer açıp programı yeniden başlatın.
      </p>
      <Ipucu>
        “Program sürümü eski” iletisi, daha yeni sürümün yazdığı veriyi eski programın açmaya
        çalıştığını gösterir. Program veriyi korumak için açılmaz; programı güncel sürüme yükseltip
        yeniden açın.
      </Ipucu>
    </KilavuzBolumu>
  );
}
