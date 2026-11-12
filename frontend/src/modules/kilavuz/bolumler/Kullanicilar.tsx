// Kılavuz bölümü: Kullanıcılar (çapa `kullanicilar`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
//
// Ekran adları `kullanicilar/metinler`'den gelir. Ekranı açamayan rolde adı bağlantı değildir
// (emsal `PrograminKonumu`); bölüm yine okunur, çünkü hesabını alan kişi geçici parolanın ve
// pusulanın ne olduğunu burada öğrenir. Kaynaklar: `kullanicilar/*`, sözlük §1 "Kullanıcılar",
// "Kullanıcılar ekranı", "Hesap teslim pusulası"; tasarım §4.4.4 "Geri yükleme yetkisi", §4.4.5; plan
// F1b-2 "Kendi hesabı ve ikinci program yöneticisi", 6. adım notu (yedekten sonra açılan ikinci
// program yöneticisi). BSG Yön. md. 10/1 korpustan doğrulandı; kapalı zarf okul uygulamasıdır.

import { SIFRELI_YEDEK_DUGMESI, SIFRELI_YEDEK_KARTI_BASLIGI } from "../../guvenlik/metinler";
import {
  ACILDI_BASLIGI,
  ALAN_AD_SOYAD,
  ALAN_GECICI_PAROLA,
  ALAN_ROL,
  ALAN_TANITICI,
  ASKIDAN_CIKARILDI_ILETISI,
  AYRINTI_BASLIGI,
  BU_OTURUM,
  DUGME_ASKIDAN_CIKAR,
  DUGME_HESABI_AC,
  DUGME_KAPAT,
  DUGME_PUSULA,
  DUGME_SIFIRLA,
  DUGME_SIFIRLA_ONAY,
  DUGME_YENI_HESAP,
  DUGME_YENI_ONERI,
  ETIKET_ACILIS,
  ETIKET_DURUM,
  ETIKET_HESAP_SAHIBI,
  ETIKET_KAPANIS,
  ETIKET_PAROLA_DEGISIMI,
  ETIKET_ROL,
  ETIKET_SIFIRLAMA,
  ETIKET_SON_GIRIS,
  ETIKET_SON_GIRISLER,
  ETIKET_TANITICI,
  KAPAMA_ONAY_BASLIGI,
  KULLANICILAR_BASLIGI,
  YENI_HESAP_BASLIGI,
} from "../../kullanicilar/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

const SIRALI_LISTE = "list-decimal space-y-1 pl-5";
const MADDELI_LISTE = "list-disc space-y-1 pl-5";

export default function Kullanicilar(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      {yetki.acik("kullanicilar") ? (
        <p>
          Hesapları <Ekran to="/kullanicilar">{KULLANICILAR_BASLIGI}</Ekran> ekranında açar, kapatır
          ve parolalarını sıfırlarsınız.
        </p>
      ) : (
        <p>
          {KULLANICILAR_BASLIGI} ekranı hesabınızın rolüne açık değil; hesabınızla ilgili her iş
          için program yöneticisine başvurun. Aşağıdaki adımlar hesabınızın nasıl açıldığını ve size
          neyin teslim edileceğini anlatır.
        </p>
      )}
      <p>
        Her kişiye kendi hesabı açılır. Liste bütün hesapları gösterir; kapalı ve giriş yapamayan
        hesaplar da listededir, çünkü hesap kaydı silinmez. Sütunlar{" "}
        <strong>{ETIKET_TANITICI}</strong>, <strong>{ETIKET_ROL}</strong>,{" "}
        <strong>{ETIKET_HESAP_SAHIBI}</strong>, <strong>{ETIKET_DURUM}</strong> ve{" "}
        <strong>{ETIKET_SON_GIRIS}</strong>&apos;tir; oturumu açan hesabın yanında{" "}
        <strong>{BU_OTURUM}</strong> yazar.
      </p>
      <ul className={MADDELI_LISTE}>
        <li>
          <strong>Açık:</strong> hesap sahibi kilit ekranından girebilir.
        </li>
        <li>
          <strong>Parola yenilenmeli:</strong> hesap sahibi geçici parolayla girip kendi parolasını
          belirleyecek.
        </li>
        <li>
          <strong>Askıda:</strong> giriş kapalıdır; yanında nedeni yazar (ör. Hatalı parola
          denemesi).
        </li>
        <li>
          <strong>Kapalı:</strong> hesap kilit ekranından kalkmıştır; yanında kapanış günü yazar.
        </li>
      </ul>
      <p>
        Bir satıra basınca <strong>{AYRINTI_BASLIGI}</strong> penceresi açılır:{" "}
        <strong>{ETIKET_ACILIS}</strong>, varsa <strong>{ETIKET_KAPANIS}</strong>,{" "}
        <strong>{ETIKET_PAROLA_DEGISIMI}</strong>, <strong>{ETIKET_SIFIRLAMA}</strong> ve{" "}
        <strong>{ETIKET_SON_GIRISLER}</strong> burada yazar. Eylem düğmeleri de bu penceredir.
        Yapılamayan eylemin düğmesi kapalıdır ve nedeni yanında yazar.
      </p>

      <AltBaslik>Yeni hesap açmak için</AltBaslik>
      <ol className={SIRALI_LISTE}>
        <li>
          <strong>{DUGME_YENI_HESAP}</strong> düğmesine basın; <strong>{YENI_HESAP_BASLIGI}</strong>{" "}
          penceresi açılır.
        </li>
        <li>
          <strong>{ALAN_ROL}</strong> alanından kişinin rolünü seçin. Rolde yer yoksa nedeni alanın
          altında yazar: tek hesaplı rollerde “Bu rolde açık bir hesap zaten var; önce onu
          kapatın.”, Denetleme Kurulunda “Denetleme Kurulu için en çok 3 hesap açık olabilir.”
        </li>
        <li>
          <strong>{ALAN_TANITICI}</strong> alanını program doldurur, dilerseniz değiştirin. Tanıtıcı
          kilit ekranında herkese görünür; gerçek ad ya da kimlik numarası yazmayın. Yazarsanız
          program uyarır.
        </li>
        <li>
          <strong>{ALAN_AD_SOYAD}</strong> alanına hesap sahibinin adını yazın; şifreli saklanır,
          kilit ekranında görünmez.
        </li>
        <li>
          <strong>{ALAN_GECICI_PAROLA}</strong> alanı programın önerisiyle dolu gelir: 12 karakter,
          birbirine karışan harf ve rakam yok. Beğenmezseniz <strong>{DUGME_YENI_ONERI}</strong>{" "}
          düğmesine basın ya da değiştirin. Parolayı bir kâğıda yazın.
        </li>
        <li>
          <strong>{DUGME_HESABI_AC}</strong> düğmesine basın. <strong>{ACILDI_BASLIGI}</strong>{" "}
          yazınca <strong>{DUGME_PUSULA}</strong> düğmesiyle pusulayı PDF olarak kaydedip basın.
        </li>
      </ol>
      <Ipucu>
        Geçici parola yalnız onu yazdığınız pencerenin alanında görünür. Program onu bir daha
        göstermez; kopyalama düğmesi de yoktur. Parolayı kâğıda yazmadan düğmeye basmayın.
      </Ipucu>

      <AltBaslik>Geçici parolayı ve pusulayı teslim etmek için</AltBaslik>
      <p>
        Geçici parolayı yazdığınız kâğıdı kapalı zarfta hesap sahibine verin; herkesin görebileceği
        bir yere yazmayın (Bilgi ve Sistem Güvenliği Yönergesi md. 10/1). Kapalı zarf okul
        uygulamasıdır. Hesap teslim pusulası parola taşımaz: hesap sahibine tanıtıcısını,
        programdaki işini, ilk giriş adımlarını ve parola kurallarını anlatır. Zarfla birlikte
        verin; teslim eden ve teslim alan imzalar. Pusula kişisel veri içerir: asılmaz, okul dışına
        verilmez. Program pusulanın kopyasını saklamaz, dosya seçtiğiniz yerde kalır.
      </p>
      <p>
        Hesap sahibi ilk girişte geçici parolayı yazar ve kendi parolasını belirler; adımlar{" "}
        <Ekran to="/kilavuz#hesaplar-ve-oturum">Hesaplar ve Oturum</Ekran> bölümündedir. Pusula
        kapalı hesaba ve kendi hesabınıza basılmaz; askıdaki hesaba basılır.
      </p>
      <p>
        Pencere “Hesap açıldı, ancak parola kaydı güvenlik dosyasına yazılamadı” derse o pencerede
        yazdığınız geçici parola geçerli değildir; kâğıda yazdıysanız o kâğıdı vermeyin. Pencerenin
        sunduğu <strong>{DUGME_SIFIRLA}</strong> düğmesiyle yeni bir geçici parola verin; yeniden
        hesap açmayın.
      </p>

      <AltBaslik>Parolasını unutan birine yardım etmek için</AltBaslik>
      <ol className={SIRALI_LISTE}>
        <li>
          Satıra basın, <strong>{AYRINTI_BASLIGI}</strong> penceresinde{" "}
          <strong>{DUGME_SIFIRLA}</strong> düğmesine basın.
        </li>
        <li>
          <strong>{ALAN_GECICI_PAROLA}</strong> alanındaki öneriyi kâğıda yazın ve{" "}
          <strong>{DUGME_SIFIRLA_ONAY}</strong> düğmesine basın.
        </li>
        <li>Kâğıdı kapalı zarfta hesap sahibine verin.</li>
      </ol>
      <p>
        Eski parola artık geçmez, hesabın durumu <strong>Parola yenilenmeli</strong> olur. Hesap
        sahibine ilk girişinde parolasının sıfırlandığı ve o andan bu yana hesabıyla yapılan
        girişler gösterilir. Kendi parolanızı buradan sıfırlayamazsınız;{" "}
        <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran> sekmesindeki{" "}
        <strong>Parolayı değiştir</strong> penceresini kullanın.
      </p>
      <p>
        <strong>{ETIKET_DURUM}</strong> sütununda parola kaydının güvenlik dosyasında olmadığı ya da
        hesap kaydıyla uyuşmadığı yazıyorsa da çare parolayı sıfırlamaktır; bu çoğunlukla yedekten
        geri yüklemeden sonra olur.
      </p>

      <AltBaslik>Askıya düşen hesabı açmak için</AltBaslik>
      <p>
        Hesap üst üste yanlış parola denemesiyle askıya düştüyse <strong>{AYRINTI_BASLIGI}</strong>{" "}
        penceresinde <strong>{DUGME_ASKIDAN_CIKAR}</strong> düğmesine basın; program “
        {ASKIDAN_CIKARILDI_ILETISI}” der ve yanlış deneme sayacı sıfırlanır. Kişi parolasını da
        unuttuysa <strong>{DUGME_ASKIDAN_CIKAR}</strong> düğmesine gerek yoktur:{" "}
        <strong>{DUGME_SIFIRLA}</strong> düğmesi askıyı da kaldırır ve yeni geçici parola verir.
      </p>

      <AltBaslik>Görevi biten kişinin hesabını kapatmak için</AltBaslik>
      <p>
        <strong>{AYRINTI_BASLIGI}</strong> penceresinde <strong>{DUGME_KAPAT}</strong> düğmesine
        basın, <strong>{KAPAMA_ONAY_BASLIGI}</strong> sorusunu onaylayın. Hesap kilit ekranından
        kalkar, parola kaydı bu bilgisayarın güvenlik dosyasından silinir; hesap kaydı ve denetim
        izindeki kayıtları silinmez. Kapalı hesap yeniden açılmaz, gerekirse yeni hesap açılır. Tek
        hesaplı bir role yeni kişi gelecekse önce eski hesabı kapatın.
      </p>
      <p>Kendi hesabınızı kapatamazsınız; son program yöneticisi hesabı da kapatılamaz.</p>

      <AltBaslik>İkinci program yöneticisi hesabı açmak için</AltBaslik>
      <p>
        <strong>{ALAN_ROL}</strong> alanında program yöneticisini seçin; pencere bu hesabın ikinci
        bir program yöneticisi hesabı olarak açılacağını söyler. İki hesap olunca, biri parolasını
        unuttuğunda öteki sıfırlayabilir.
      </p>
      <p>
        Program yöneticisi değişiyorsa yeni kişiye bu yolla hesap açın; yeni kişi kendi hesabıyla
        girip eski hesabı kapatır. Bu işlem kayıtların anahtarını da kurtarma anahtarını da
        değiştirmez.
      </p>
      <Ipucu>
        Hesabı açtıktan sonra <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran>{" "}
        sekmesindeki <strong>{SIFRELI_YEDEK_KARTI_BASLIGI}</strong> kartından{" "}
        <strong>{SIFRELI_YEDEK_DUGMESI}</strong> düğmesiyle yeni bir yedek alın: daha eski bir
        yedekten geri yüklemede bu hesabın parolası işlemeyebilir. Nedeni{" "}
        <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran> bölümünün “Parola
        mı, kurtarma anahtarı mı” başlığındadır.
      </Ipucu>

      <AltBaslik>Düğmeler “program dışından değiştirilmiş” diyerek kapalıysa</AltBaslik>
      <p>
        Hesap kaydı ya da denetim izi tutmayan hesapta program bu kayda dokunmaz; bütün eylemler
        kapalıdır ve nedeni yanında yazar. Denetleme Kuruluna bildirin. Kayıtlar sağlam bir yedekten
        geri yüklenebilir.
      </p>
    </KilavuzBolumu>
  );
}
