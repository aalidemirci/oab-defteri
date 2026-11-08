// Kılavuz bölümü: Hesaplar ve Oturum (çapa `hesaplar-ve-oturum`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
//
// Kılavuz kilitliyken açılmaz (`GuvenlikKapisi`) ve kilit ekranından kılavuza bağlantı yoktur:
// parolayı unutunca ne yapılacağı burada ÖNCEDEN öğretilir. Rol tablosu yazılmaz (sözlük §1 "Rol
// süzmesi"); ekranın kendi cümlesi neyse o yazılır ("program yöneticisine başvurun"). Kaynaklar:
// `guvenlik/KilitEkrani`, `guvenlik/KurtarmaIleAcma`, `oturum/parolaPolitikasi`, `oturum/useKilitle`,
// `oturum/RolKapisi`, `butunluk/ParolaYenilenmeBildirimi`; sözlük §1 "Parola", "Hesap", "Kurtarma
// anahtarı", "Kilit ve çıkış", §4.2; tasarım §4.4.3, §4.4.5, §4.4.6. Atıflar korpustan doğrulandı
// (BSG Yön. md. 7, 9, 10); md. 7 ve 10/2 programa kıyasen anılır (sözlük §1 "Hesap teslim pusulası").

import { YONERGE } from "../../../lib/mevzuat";
import {
  PAROLA_BILDIRIMI_BASLIGI,
  SON_GIRISLER_KARTI_BASLIGI,
  parolaYenilenmeOgudu,
} from "../../butunluk/metinler";
import {
  BOSTA_DK_EN_AZ,
  BOSTA_DK_EN_COK,
  BOSTA_DK_VARSAYILAN,
  BOSTA_KILIT_KARTI_BASLIGI,
} from "../../guvenlik/BostaKilitSuresiKarti";
import { HESAP_KARTI_BASLIGI, PAROLA_DEGISTI_ILETISI } from "../../guvenlik/GuvenlikAyarlari";
import {
  ASKIDA_ETIKETI,
  KILIT_EKRANI_BASLIGI,
  KURTARMA_ILE_AC_ETIKETI,
  OKUNAMADI_ETIKETI,
  UNUTTUM_BASKA_ROL_METNI,
} from "../../guvenlik/KilitEkrani";
import {
  PAROLA_CUMLESI_ONERISI,
  PAROLA_EN_COK,
  PAROLA_KURALI_METNI,
} from "../../oturum/parolaPolitikasi";
import {
  EKRAN_ROLE_KAPALI_ILETISI,
  SALT_OKUR_ILETISI,
  YETKI_OKUNAMADI_ILETISI,
} from "../../oturum/RolKapisi";
import { KILITLE_KISAYOLU, KILIT_BEKLIYOR_METNI } from "../../oturum/useKilitle";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, KapiliEkran, Tus } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

const SIRALI_LISTE = "list-decimal space-y-1 pl-5";
const MADDELI_LISTE = "list-disc space-y-1 pl-5";

export default function HesaplarVeOturum(bolum: BolumProps) {
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Herkes programı kendi hesabıyla ve kendi parolasıyla açar; parola paylaşılmaz. Bir hesap bir
        kişi ve bir roldür. Hesabın kilit ekranında görünen adı <strong>tanıtıcı</strong>dır;
        kişinin adı kilit ekranında ve üst çubukta görünmez.
      </p>
      <Ipucu>
        Program kilitliyken bu kılavuz açılmaz. “Parolanızı unuttuysanız” başlığını bugünden okuyun;
        ihtiyaç anında buraya bakamazsınız.
      </Ipucu>

      <AltBaslik>Programı açmak için</AltBaslik>
      <ol className={SIRALI_LISTE}>
        <li>
          <strong>{KILIT_EKRANI_BASLIGI}</strong> ekranında <strong>Hesap</strong> listesinden kendi
          satırınızı seçin. Satırda rol etiketi (ör. Muhasip, Denetleme Kurulu 2), altında tanıtıcı
          yazar.
        </li>
        <li>
          <strong>Parola</strong> alanına parolanızı yazıp <strong>Aç</strong> düğmesine basın.
        </li>
        <li>
          Parolanız geçiciyse ya da 180 günü dolduysa program aynı ekranda yeni parola ister.{" "}
          <strong>Yeni parola</strong> ve <strong>Parola (tekrar)</strong> alanlarını doldurup{" "}
          <strong>Parolayı yenile ve aç</strong> düğmesine basın. Yeni parola eskisiyle aynı olamaz.
        </li>
      </ol>
      <p>
        Satırınız seçilemiyorsa yanındaki yazıya bakın: <strong>{ASKIDA_ETIKETI}</strong> yazıyorsa
        program yöneticisi askıyı kaldırmadan giriş açılmaz; <strong>{OKUNAMADI_ETIKETI}</strong>{" "}
        yazıyorsa aşağıdaki “Listede seçilebilecek hesap kalmadıysa” başlığına bakın. Kapatılmış
        hesap listede görünmez.
      </p>

      <AltBaslik>Parolanızı yanlış girdiyseniz</AltBaslik>
      <p>
        Parola üst üste yanlış girildikçe bekleme süresi artar; bu sırada ekran{" "}
        <strong>Denetleniyor…</strong> der. Doğru parolayla yapılan giriş sayacı sıfırlar.
      </p>
      <p>
        Program yöneticisi dışındaki hesaplarda üst üste 10. yanlış denemede hesap askıya alınır;
        askıyı program yöneticisi kaldırır ({YONERGE} md. 7/3 ve 9/2-c&apos;ye kıyasen; bundan sonra
        kısaca Yönerge). Program yöneticisi hesabı yanlış denemede askıya alınmaz, ama bekleme
        süresi onda da işler.
      </p>

      <AltBaslik>Parola kuralları</AltBaslik>
      <p>
        {PAROLA_KURALI_METNI} Parola en çok {PAROLA_EN_COK} karakter olabilir; Türkçe harfler harf
        sayılır. {PAROLA_CUMLESI_ONERISI} Yeni parolanın altındaki{" "}
        <strong>Zayıf · Orta · İyi · Güçlü</strong> göstergesi programın önerisidir, kabul ya da ret
        kararı değildir.
      </p>
      <p>
        En az sekiz karakter ve karışık yapı Yönerge md. 9/2-a ve 9/2-b bentlerindedir. Parola en
        geç altı ayda bir değiştirilir (Yönerge md. 9/2-ç); 180 gün dolunca program yeni parolanızı
        ister. Parolanızı kimseyle paylaşmayın (Yönerge md. 9/2-e), herkesin görebileceği bir yere
        yazmayın (Yönerge md. 10/1).
      </p>

      <AltBaslik>Parolanızı değiştirmek için</AltBaslik>
      <p>
        <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran> sekmesinde{" "}
        <strong>{HESAP_KARTI_BASLIGI}</strong> kartındaki <strong>Parolayı değiştir</strong>{" "}
        düğmesine basın. <strong>Mevcut parola</strong>, <strong>Yeni parola</strong> ve{" "}
        <strong>Parola (tekrar)</strong> alanlarını doldurup <strong>Uygula</strong> düğmesine
        basın; program “{PAROLA_DEGISTI_ILETISI}” der.
      </p>
      <p>
        Parola değişince eski parola programda giriş açmaz. Bu korumanın programın dışındaki sınırı{" "}
        <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran> bölümündedir.
      </p>

      <AltBaslik>Parolanızı unuttuysanız</AltBaslik>
      <p>
        <strong>Program yöneticisi değilseniz</strong> kilit ekranı “{UNUTTUM_BASKA_ROL_METNI}” der.
        Program yöneticisi parolanızı sıfırlar ve size kapalı zarfta yeni bir geçici parola verir;
        ilk girişinizde kendi parolanızı belirlersiniz.
      </p>
      <p>
        <strong>Program yöneticisiyseniz</strong> iki yolunuz vardır: başka bir program yöneticisi
        hesabı varsa o sizin parolanızı sıfırlayabilir; yoksa kurtarma anahtarını kullanırsınız.
        Kurtarma anahtarı okul müdürlüğünde kapalı zarfta saklanan kâğıttadır ve yalnız program
        yöneticisi hesabı içindir; başka rolün hesabı bu yolla açılmaz.
      </p>
      <ol className={SIRALI_LISTE}>
        <li>Kurtarma anahtarının yazılı olduğu kâğıdı okul müdürlüğündeki zarftan alın.</li>
        <li>
          Kilit ekranında program yöneticisi hesabınızı seçin ve <strong>Parolamı unuttum</strong>{" "}
          düğmesine basın.
        </li>
        <li>
          <strong>Kurtarma anahtarı</strong> alanına anahtarı yazın; <strong>Yeni parola</strong> ve{" "}
          <strong>Parola (tekrar)</strong> alanlarını doldurup <strong>Kurtar ve aç</strong>{" "}
          düğmesine basın. Vazgeçerseniz <strong>Parolayla açmaya dön</strong> düğmesine basın.
        </li>
        <li>İş bitince kâğıdı yeniden kapalı zarfa koyup okul müdürlüğüne verin.</li>
      </ol>
      <p>
        Anahtar kullanılmakla bitmez, bundan sonra da geçerli kalır. Bu açılış denetim izine
        yazılır. Zarfın hangi durumlarda açılacağı{" "}
        <Ekran to="/kilavuz#ilk-kurulum">İlk Kurulum</Ekran> bölümündedir.
      </p>

      <AltBaslik>Parolanız sıfırlandıysa ya da yenilendiyse</AltBaslik>
      <p>
        İlk girişinizde <strong>{PAROLA_BILDIRIMI_BASLIGI}</strong> penceresi açılır: tarihi ve o
        tarihten bu yana hesabınızla yapılan girişleri yazar. {parolaYenilenmeOgudu("SIFIRLAMA")}{" "}
        {parolaYenilenmeOgudu("KURTARMA")} <strong>Gördüm</strong> düğmesine basmadan kapatırsanız
        bildirim bir sonraki girişinizde yeniden gösterilir. Son girişleriniz{" "}
        <Ekran to="/">Genel Bakış</Ekran>&apos;taki <strong>{SON_GIRISLER_KARTI_BASLIGI}</strong>{" "}
        kartında da görünür.
      </p>

      <AltBaslik>Listede seçilebilecek hesap kalmadıysa</AltBaslik>
      <p>
        Bütün satırlar seçilemez durumdaysa <strong>Parola</strong> alanı ve <strong>Aç</strong>{" "}
        düğmesi kalkar, yerine <strong>{KURTARMA_ILE_AC_ETIKETI}</strong> düğmesi gelir. Program
        yöneticisi bu düğmeyle açar ve yeni parolasını belirler. Öteki hesaplar program yöneticisine
        başvurur: askıyı o kaldırır, parolayı o sıfırlar.
      </p>
      <p>
        Liste tamamen boş geliyorsa program kurtarma yolunu doğrudan açar; kayıtlar kurtarma
        anahtarıyla geri yüklendiyse liste böyle gelir. Program yöneticisi yeni parolasını belirler,
        öteki hesaplara{" "}
        <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
          Kullanıcılar
        </KapiliEkran>{" "}
        ekranından yeni geçici parola verir. Böyle bir geri yükleme yapılmadıysa güvenlik dosyası
        program dışından değiştirilmiş olabilir: Denetleme Kuruluna bildirin.
      </p>
      <p>
        Kayıtlar bozulmuş ya da program dışından değiştirilmiş görünüyorsa Denetleme Kuruluna
        bildirin. Kilit ekranındayken program içinden geri yükleme yapılamaz: programı kapatıp{" "}
        <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran> bölümündeki
        “Program hiç açılmıyorsa” adımlarını izleyin.
      </p>

      <AltBaslik>Giriş “program dışından değiştirilmiş” diye reddedilirse</AltBaslik>
      <p>
        “Hesap kaydı program dışından değiştirilmiş görünüyor” ya da “Denetim izinden kayıt
        silinmiş” diye başlayan ileti, kaydın programın dışından değiştiğini gösterir. Bu bir yanlış
        deneme sayılmaz, kayda dokunulmaz ve olay denetim izine yazılır. İletide kime bildirileceği
        yazar; o kişilere bildirin, tekrar tekrar denemeyin.
      </p>

      <AltBaslik>Bilgisayarın başından kalkarken</AltBaslik>
      <p>
        Üst çubuktaki <strong>Kilitle</strong> düğmesine basın ya da <Tus>{KILITLE_KISAYOLU}</Tus>{" "}
        tuşlarını kullanın. Program açık kalır, kayıtlar kilitlenir.{" "}
        <strong>Açık oturum, sahibinin imzasıdır:</strong> oturum açıkken yapılan her iş o hesabın
        adına denetim izine yazılır. Bilgisayar başından ayrılırken kilitlemek ve boşta kilit
        Yönerge md. 7/4 ve 10/2&apos;ye kıyasen uygulanır.
      </p>
      <ul className={MADDELI_LISTE}>
        <li>
          Kilitlenince ve kilit açılınca pencere yeniden yüklenir; açık formda kaydetmediğiniz bilgi
          kaybolur.
        </li>
        <li>
          Uzun bir iş sürerken kilit ertelenir, ekranda <strong>{KILIT_BEKLIYOR_METNI}</strong>{" "}
          yazar.
        </li>
        <li>
          Başka bir hesaba geçmek için ayrı bir düğme yoktur: <strong>Kilitle</strong> düğmesine
          basıp kilit ekranında o hesabı seçin. Programı kapatmak ayrı bir iştir;{" "}
          <Ekran to="/kilavuz#cikis-ve-kapanis">Çıkış ve Kapanış</Ekran> bölümüne bakın.
        </li>
      </ul>

      <AltBaslik>Program kendiliğinden kilitlendiyse</AltBaslik>
      <p>
        Program belli bir süre işlem yapılmazsa kendiliğinden kilitlenir; kalan süre üst çubukta
        görünür. Süre {BOSTA_DK_EN_AZ} ile {BOSTA_DK_EN_COK} dakika arasındadır, varsayılanı{" "}
        {BOSTA_DK_VARSAYILAN} dakikadır. Bugünkü süreyi{" "}
        <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran> sekmesindeki{" "}
        <strong>{BOSTA_KILIT_KARTI_BASLIGI}</strong> kartında görürsünüz; kartta değiştirme alanı
        yoksa süre için program yöneticisine başvurun. Kurulum tamamlanana dek süre işlemez. Bunun
        dışında oturumun bir üst süresi yoktur.
      </p>

      <AltBaslik>Bir ekran ya da düğme size görünmüyorsa</AltBaslik>
      <p>
        Her hesap rolünün açık olduğu ekranları görür. Bu programda sizin yapacağınız işler,
        hesabınız açılırken verilen hesap teslim pusulasının “Bu programda sizin işiniz” tablosunda
        yazılıdır. Size kapalı bir iş gerekiyorsa program yöneticisine başvurun.
        Karşılaşabileceğiniz iletiler:
      </p>
      <ul className={MADDELI_LISTE}>
        <li>
          <strong>{EKRAN_ROLE_KAPALI_ILETISI}</strong> Ekran size kapalıdır; kayıtlara bir şey
          olmamıştır.
        </li>
        <li>
          <strong>{SALT_OKUR_ILETISI}</strong> Bölümü okursunuz, yazma düğmeleri çizilmez.
        </li>
        <li>
          <strong>Bu işlem hesabınızın rolüne açık değil.</strong> İşlem yapılmamıştır. Düğme
          ekranda kalmışsa sayfayı yeniden açın.
        </li>
        <li>
          <strong>{YETKI_OKUNAMADI_ILETISI}</strong> Program hesabınızın rolünü o an okuyamadı; bu,
          size kapalı olduğu anlamına gelmez.
        </li>
      </ul>
      <p>
        Roller programın içindeki ayrımdır, kayıtların şifrelenmesini değiştirmez; bu sınır{" "}
        <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran> bölümünde
        anlatılır.
      </p>
    </KilavuzBolumu>
  );
}
