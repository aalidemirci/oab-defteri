// Kılavuz bölümü: İlk Kurulum (çapa `ilk-kurulum`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Adımlar `kurulum/KurulumPage.tsx` ve sözlük §4.4'ten; anahtarın saklanması
// `guvenlik/KurtarmaAnahtariPaneli.tsx` ve `guvenlik/metinler.ts`'ten. Kurulum bitmeden Kılavuz
// açılmaz (`KurulumKapisi`), bölüm bu yüzden sihirbazı yarıda bırakanı ve yeniden açanı da düşünür.
// Programın bilgisayara kurulması bu bölümde değildir (`packaging/README.md`).

import { KURTARMA_BELGESI_ADI } from "../../guvenlik/kurtarma";
import {
  DOGRULANMADI_BASLIGI,
  ELLE_YAZ_METNI,
  UCUNCU_DURUMUN_CARESI,
  ZARFIN_UCUNCU_DURUMU,
} from "../../guvenlik/metinler";
import { PAROLA_KURALI_METNI } from "../../oturum/parolaPolitikasi";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KapiliEkran, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function IlkKurulum(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program ilk açıldığında Kurulum Sihirbazı gelir. Sihirbaz bitmeden öteki ekranlar açılmaz,
        bu kılavuz da açılmaz. Bu bölüm adımların ne istediğini ve bir adım yarım kalırsa ne
        yapılacağını anlatır. Adımlar bu sırayla gelir:
      </p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>Program Yöneticisi Hesabı (atlanamaz)</li>
        <li>Okul Bilgileri</li>
        <li>Ders Yılı ve Kapalı Günler</li>
      </ol>

      <AltBaslik>1. adım: program yöneticisi hesabını kurmak</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>Tanıtıcı</strong> kilit ekranında herkese görünen hesap adıdır; gerçek ad
          yazılmaz. Alan “yonetici” önerisiyle gelir.
        </li>
        <li>
          <strong>Ad-soyad</strong> hesap sahibinindir; şifreli saklanır, kilit ekranında görünmez.
        </li>
        <li>
          <strong>Parola</strong> ve <strong>Parola (tekrar)</strong>: {PAROLA_KURALI_METNI}
        </li>
      </ul>
      <p>
        “Hesabı kur” düğmesine basınca hesap kurulur. Bu hesabın kaydı silinmez; açık başka bir
        program yöneticisi hesabı yokken kapatılamaz, parolası değiştirilebilir; program yöneticisi
        değişirse izlenecek yol <Ekran to="/kilavuz#kullanicilar">Kullanıcılar</Ekran> bölümündedir.
        Parolayı kimseyle paylaşmayın: herkes programı kendi hesabıyla ve kendi parolasıyla açar.
        Öteki hesaplar kurulumdan sonra{" "}
        <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
          Kullanıcılar
        </KapiliEkran>{" "}
        ekranında açılır.
      </p>

      <AltBaslik>Kurtarma anahtarını saklamak</AltBaslik>
      <p>
        Hesap kurulunca <strong>Kurtarma Anahtarınız</strong> paneli anahtarı, no&apos;su ve üretim
        tarihiyle gösterir. Anahtar programda saklanmaz ve bir daha gösterilmez. Kayıtlara üç
        durumda bu anahtarla erişilir:
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>program yöneticisi parolasını unutursa;</li>
        <li>kayıtlar yeni bir bilgisayara taşınırken;</li>
        <li>
          {ZARFIN_UCUNCU_DURUMU} (çaresi {UCUNCU_DURUMUN_CARESI}).
        </li>
      </ul>
      <p>
        Saklamanın üç yolu vardır: “Yazdır” düğmesiyle kâğıda basmak, “PDF olarak kaydet” düğmesiyle{" "}
        {KURTARMA_BELGESI_ADI} adlı PDF&apos;i USB belleğe kaydetmek ya da kâğıda elle yazmak.{" "}
        {ELLE_YAZ_METNI}
      </p>
      <Ipucu>
        Kâğıdı zarfa koyup kapatın ve okul müdürlüğünde kilitli dolapta saklayın; zarf veliye
        geçmez. Anahtar yalnız program yöneticisi içindir, zarf yalnız yukarıdaki üç durumda açılır.
        PDF dosyasını bu bilgisayarda bırakmayın.
      </Ipucu>
      <p>
        Sakladıktan sonra “Sakladım, doğrula” düğmesine basın ve program hangi iki grubu sorarsa
        sakladığınız kopyaya bakarak yazın. İki grup tutunca “Devam” düğmesi açılır; anahtarın
        saklandığı doğrulanmadan sonraki adıma geçilmez. Beş dakika işlem yapılmazsa anahtar ekranda
        gizlenir; kaybolmaz, “Anahtarı göster” düğmesiyle geri gelir.
      </p>

      <AltBaslik>Anahtar doğrulanmadan ekrandan kalktıysa</AltBaslik>
      <p>
        Pencere kapandıysa, program çöktüyse ya da Kilitle&apos;ye bastıysanız anahtar yeniden
        gösterilmez (Kilitle önce “Program kilitlensin mi?” diye sorar). Sihirbazın ilk adımı “
        {DOGRULANMADI_BASLIGI}” uyarısıyla açılır ve iki yol sunar:
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>Kurtarma Anahtarını Doğrula:</strong> anahtarı kaydettiyseniz kâğıttaki ya da
          PDF&apos;teki anahtarı olduğu gibi yazın.
        </li>
        <li>
          <strong>Kurtarma Anahtarını Yenile:</strong> kaydedemediyseniz parolanızla yeni bir
          anahtar üretin. Yeni anahtarın no&apos;su bir artar, anahtar bir kez gösterilir; saklayıp
          doğrulamadan programı kapatmayın. Hesapların parolaları değişmez, kayıtlar yeniden
          şifrelenmez.
        </li>
      </ul>

      <AltBaslik>2. adım: okul bilgileri</AltBaslik>
      <p>
        Okul adı, il, ilçe, kurum kodu, kademe, öğrenci mevcudu ve mevcudun tarihi, yerleşim türü,
        kantin işletme biçimi, personel çalıştırma biçimi ve “Bu bilgisayar okul demirbaşıdır.”
        onayı zorunludur. Alanlar <Ekran to="/ayarlar?tab=okul">Ayarlar → Okul Bilgileri</Ekran> ile
        aynıdır; ne işe yaradıkları <Ekran to="/kilavuz#okul-karti">Okul Bilgileri</Ekran>{" "}
        bölümündedir. “Kaydet ve devam et” düğmesiyle geçin.
      </p>

      <AltBaslik>3. adım: ders yılı ve kapalı günler</AltBaslik>
      <p>
        <strong>Yeni Ders Yılı</strong> kartında ad, başlangıç, bitiş, 1. dönem bitişi ve 2. dönem
        başlangıcı önerilmiş gelir. Tarihleri okulunuzun takvimine göre düzeltip “Ders yılını kaydet
        ve aktifleştir” düğmesine basın. Yıl aktifleşince iki takvim yılının resmî ve dini tatilleri
        kendiliğinden eklenir. Ara tatil ve yarıyılı “öğrenciye kapalı gün” olarak bu adımda ya da
        sonra girersiniz; ayrıntısı{" "}
        <Ekran to="/kilavuz#ders-yili-kapali-gunler">Ders Yılları ve Kapalı Günler</Ekran>{" "}
        bölümündedir.
      </p>
      <p>
        Son düğme “Kurulumu tamamla”dır; eksik adım varken kapalıdır. Kurulum bitince Genel Bakış
        açılır ve menüdeki bölümler kullanılabilir. Personel aktarımı sihirbazda değildir; sıradaki
        işler <Ekran to="/kilavuz#genel-bakis">Genel Bakış</Ekran> bölümünde anlatılan Başlangıç Yol
        Haritası&apos;ndadır.
      </p>

      <AltBaslik>Sihirbazı yarıda bıraktıysanız</AltBaslik>
      <p>
        Program kapanırsa kaydettikleriniz durur. Yeniden açtığınızda, hesap kurulmuşsa önce kilit
        ekranından parolanızla girersiniz; sihirbaz ilk eksik adımdan sürer.
      </p>

      <AltBaslik>Sihirbazı sonradan açmak</AltBaslik>
      {yetki.acik("kurulum_tamamlama") ? (
        <p>
          Kurulumdan sonra <Ekran to="/kurulum">Kurulum Sihirbazı</Ekran> menüde görünmez;{" "}
          <Ekran to="/ayarlar">Ayarlar</Ekran> sayfasının altındaki Diğer Ayarlar bölümünde kartıyla
          açılır. Okul bilgilerini ve takvimi sihirbazı açmadan Ayarlar&apos;dan da
          değiştirebilirsiniz.
        </p>
      ) : (
        <p>
          Kurulum Sihirbazı&apos;nı yalnız kurulumu tamamlayabilen hesap açar; girilen bilgiler{" "}
          <Ekran to="/ayarlar">Ayarlar</Ekran>&apos;da görünür. Yanlış gördüğünüz bir bilgi için
          program yöneticisine başvurun.
        </p>
      )}
    </KilavuzBolumu>
  );
}
