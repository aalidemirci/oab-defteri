// Kılavuz bölümü: Programı Kurmak (çapa `programi-kurmak`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Programın bilgisayara kurulması, kaldırılması ve verinin yeri (plan F1b-6 kararları "Kılavuz": kurulum
// bölümü F1c kapısında; tasarım §14 F1c satırı "kılavuzun F1 bölümleri"). Kaynaklar:
// `packaging/windows/oab-defteri.iss` (iki kurulum seçeneği TK7, lisans sayfası, masaüstü kısayolu,
// WebView2, Başlat menüsündeki iki kısayol, son sayfanın veri notu, programın kurulumu yapan Windows
// hesabıyla açılması), `packaging/linux/BENIOKU.txt` (taşınabilir sürüm, `kur.sh`, `kaldir.sh`, veri
// yolları), `packaging/linux/prerm` (kaldırma veriyi silmez). Sözlük §1 "Kurulum ve kaldırma": "kurulum
// dosyası", "taşınabilir sürüm", "kurulu program"; kurulum dosyasının penceresi için "sihirbaz" yazılmaz
// (Kurulum Sihirbazı programın ilk açılış ekranıdır). Ortak Windows hesabıyla birlikte hangi seçeneğin
// kullanılacağı `GuvenlikVeKisiselVeriler` bölümündedir (tasarım §15 M-8, tehdit 20).

import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Kod } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function ProgramiKurmak(bolum: BolumProps) {
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program okulun demirbaş bilgisayarına kurulur ve yalnız o bilgisayarda çalışır. Kurulum
        dosyası okulapp.org/oab-defteri sayfasındadır; dosyalar indir.okulapp.org&apos;dan iner.
        Windows 10 ve 11&apos;de kurulum dosyası, Pardus&apos;ta <Kod>.deb</Kod> paketi ya da
        taşınabilir sürüm kullanılır.
      </p>

      <AltBaslik>Windows&apos;ta kurmak</AltBaslik>
      <ol className="list-decimal space-y-1 pl-5">
        <li>Kurulum dosyasını çalıştırın.</li>
        <li>
          Kurulum, programın kimin için kurulacağını sorar: yalnız sizin Windows hesabınız için ya
          da bilgisayardaki bütün kullanıcılar için. Programı kendi Windows hesabınızda tek başınıza
          kullanacaksanız yalnız kendiniz için kurun. Ayrı bir ortak hesap kullanılacaksa bütün
          kullanıcılar için kurun; bu seçenek bilgisayarın yönetici yetkisini ister. Nedeni{" "}
          <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran> bölümündedir.
        </li>
        <li>Lisans sözleşmesini okuyup kabul edin.</li>
        <li>
          İsterseniz “Masaüstü kısayolu oluştur” kutusunu işaretleyin. Başlat menüsüne iki kısayol
          eklenir: “OAB Defteri” ve “OAB Defteri — Yedekten Geri Yükle”.
        </li>
        <li>
          Kurulum bitince programı son sayfadan ya da Başlat menüsünden açın. Program ilk açılışta
          Kurulum Sihirbazı&apos;yla gelir (<Ekran to="/kilavuz#ilk-kurulum">İlk Kurulum</Ekran>).
        </li>
      </ol>
      <p>
        Bilgisayarda Microsoft Edge WebView2 bileşeni yoksa kurulum onu da kurar. Program ağ servisi
        sunmaz ve okul ağına port açmaz; kurulum güvenlik duvarına kural eklemez, programı Windows
        açılışında başlatmaz.
      </p>
      <Ipucu>
        Kayıtlar programı açan Windows hesabının kullanıcı klasörüne yazılır, programın kurulduğu
        klasöre yazılmaz. Programı hep aynı Windows hesabıyla açın: başka bir Windows hesabıyla
        açılan program bu kayıtları görmez, Kurulum Sihirbazı&apos;yla açılır.
      </Ipucu>

      <AltBaslik>Pardus&apos;ta kurmak</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>
            <Kod>.deb</Kod> paketi:
          </strong>{" "}
          bilgisayarın yönetici yetkisi varsa bunu kullanın. Paketi kurmak için uçbirimde{" "}
          <Kod>sudo apt install</Kod> komutuna paket dosyasının yolunu verin (paket dosyasının
          bulunduğu klasörde <Kod>sudo apt install ./</Kod> yazıp dosyanın adını ekleyin). Menü
          kaydı ve gereken öteki paketler kendiliğinden kurulur.
        </li>
        <li>
          <strong>Taşınabilir sürüm:</strong> yönetici yetkisi gerekmez. Arşivi açın, klasörde{" "}
          <Kod>./kur.sh</Kod> komutunu çalıştırın; program ev dizininize kurulur, menüye “OAB
          Defteri” eklenir. Arşivdeki BENIOKU.txt dosyası adımları ayrıca yazar.
        </li>
      </ul>
      <p>
        Pardus&apos;ta kayıtlar <Kod>~/.local/share/oab-defteri</Kod> klasöründedir. Taşınabilir
        sürümden <Kod>.deb</Kod> paketine geçecekseniz önce <Kod>./kaldir.sh</Kod> ile taşınabilir
        sürümü kaldırın, sonra paketi kurun; kayıtlar iki sürümde de aynı klasördedir.
      </p>

      <AltBaslik>Programı kaldırmak</AltBaslik>
      <p>
        Windows&apos;ta Ayarlar → Uygulamalar&apos;dan, Pardus&apos;ta <Kod>sudo apt remove</Kod>{" "}
        komutuyla ya da taşınabilir sürümde <Kod>./kaldir.sh</Kod> ile kaldırılır. Kaldırma yalnız
        program dosyalarını siler; kayıtlar ve yedekler kullanıcı klasöründe kalır. Kayıtları başka
        bir bilgisayara taşımak için şifreli yedek kullanılır (
        <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran>).
      </p>
      <p>
        Yeni sürümü kurmak için <Ekran to="/kilavuz#guncelleme">Güncelleme</Ekran> bölümüne bakın.
      </p>
    </KilavuzBolumu>
  );
}
