// Kılavuz bölümü: Genel Bakış (çapa `genel-bakis`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Yol haritası maddeleri ekranın kendi sabitinden okunur (`YOL_HARITASI_MADDELERI`); kart adları
// `butunluk/metinler` ve kart bileşenlerinden, ne yapılacağı kartların kendi cümlelerinden ve
// sözlük §4.5'ten. Son Girişler'deki satırın ekrandaki öteki sözcüğü sözlük §1 gereği yazılmaz.
// Pano kalemleri (F1c 12. adım; tasarım §7.10) `pano/metinler`'in başlıklarıyla yazılır: hangi kalemin
// hangi rolde çıktığı sunucunundur (`pano.KALEM_ROLLERI`), bölüm rol adı saymaz, yalnız iki görünümü
// (veli rollerinde "Bu Ay Sizden Beklenenler", ötekilerde "Bu Hafta Yapılacaklar") anlatır.

import {
  DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
  DENETIM_IZI_KARTI_BASLIGI,
  EKSIK_EKLER_KARTI_BASLIGI,
  GERI_YUKLEME_KARTI_BASLIGI,
  IKI_DEPO_KARTI_BASLIGI,
  OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI,
  SON_GIRISLER_KARTI_BASLIGI,
} from "../../butunluk/metinler";
import { DIS_YEDEK_KARTI_BASLIGI } from "../../guvenlik/DisYedekKarti";
import { DOGRULANMADI_BASLIGI } from "../../guvenlik/metinler";
import { useYetki } from "../../oturum/yetki";
import { YOL_HARITASI_MADDELERI } from "../../pano/BaslangicYolHaritasi";
import {
  AY_BASLIGI,
  DK_GOREV_BOLUMU_BASLIGI,
  DK_KADRO_BASLIGI,
  DK_YEDEK_BASLIGI,
  EKSIK_ROZETI,
  GECIS_BASLIGI,
  HAFTA_BASLIGI,
  HESAP_ONERISI_BASLIGI,
  SON_GUN_ETIKETI,
  SURESI_DOLDU,
  TAMAMLANACAKLAR_BASLIGI,
  YARIM_TASLAK_BASLIGI,
  YK_GOREV_BOLUMU_BASLIGI,
  YK_KADRO_BASLIGI,
  YK_YEDEK_BASLIGI,
} from "../../pano/metinler";
import { OKUNAMAYAN_ALANLAR_BASLIGI } from "../../pano/OkunamayanAlanlarKarti";
import { SON_OTURUM_KARTI_BASLIGI } from "../../pano/SonOturumKarti";
import { AltBaslik, Ekran, Ipucu, KapiliEkran, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function GenelBakis(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/">Genel Bakış</Ekran> programın ana sayfasıdır. Sıradaki işler ve uyarılar
        burada kart olarak görünür. Uyarı kartlarının çoğu yalnız söyleyecek bir şeyi varken çıkar;
        her kart her hesapta görünmez. Altta <strong>{SON_GIRISLER_KARTI_BASLIGI}</strong> ile
        Kişiler ve Ayarlar kartları durur.
      </p>

      <AltBaslik>Sizden beklenen işler</AltBaslik>
      <p>
        Sayfanın başında hesabınızın rolüne göre yapılacak işlerin listesi durur. Başkan, başkan
        yardımcısı, muhasip ve sekreter hesaplarında liste <strong>{AY_BASLIGI}</strong> başlığıyla
        ve büyük yazıyla gelir: son günü bu ayın içinde ya da önümüzdeki yedi günde olan işler
        listelenir. Öteki hesaplarda başlık <strong>{HAFTA_BASLIGI}</strong>dır: son günü yedi gün
        içinde olan işler. Son günü yaklaşan ya da geçmiş iş öndedir, süresi olmayan işler ardından
        gelir; işin altında “{SON_GUN_ETIKETI}” ya da “{SURESI_DOLDU}” yazar.
      </p>
      <p>
        Her iş bir bağlantıdır: basınca işin yapılacağı ekran ve sekme açılır. Altında ekranın adı
        ve varsa dayanağı (örneğin md. 12/3) yazar. Listede kişi adı geçmez; kişi, işin götürdüğü
        ekranda görünür. Liste saklanmaz, her açılışta ve gün değişince kayıtlardan yeniden
        hesaplanır; iş yapılınca kendiliğinden düşer. Listede şu işler çıkabilir:
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>{YK_GOREV_BOLUMU_BASLIGI}</strong> ve <strong>{DK_GOREV_BOLUMU_BASLIGI}</strong>:
          kurul oluştuktan sonra bir hafta içinde görev bölümü yapılır (md. 12/3, 14/1). Ayrıntı{" "}
          <Ekran to="/kilavuz#organlar">Organlar</Ekran> bölümündedir.
        </li>
        <li>
          <strong>{GECIS_BASLIGI}</strong>: geçiş kurulumunun açık adımları (
          <Ekran to="/kilavuz#gecis-kurulumu">Geçiş Kurulumu</Ekran>).
        </li>
        <li>
          <strong>{YK_YEDEK_BASLIGI}</strong> ve <strong>{DK_YEDEK_BASLIGI}</strong>: kurulda asıl
          üye eksildi ve çağrılmamış yedek var, ya da Denetleme Kurulunun öğretmen üyesi başka
          kurumda dört aydan fazla süreli görevlendirildi (md. 13/6, 14/6).
        </li>
        <li>
          <strong>{YK_KADRO_BASLIGI}</strong> ve <strong>{DK_KADRO_BASLIGI}</strong>: kurulun
          kadrosuna ilişkin uyarılar; Organlar ekranındaki kadro uyarılarının aynısıdır.
        </li>
        <li>
          <strong>{HESAP_ONERISI_BASLIGI}</strong>: üyeliği düşen ya da görevi değişen kişinin
          askıdaki hesabı için kapatma ya da askıdan çıkarma, hesabı olmayan görevli üye için hesap
          açma önerisi (<Ekran to="/kilavuz#kullanicilar">Kullanıcılar</Ekran>).
        </li>
        <li>
          <strong>{YARIM_TASLAK_BASLIGI}</strong>: bir gerekçe kutusunda yazıp kaydetmediğiniz metin
          var. Yalnız kendi hesabınızın yarım metni görünür; metnin kendisi listede yazmaz.
        </li>
      </ul>
      <p>
        <strong>{TAMAMLANACAKLAR_BASLIGI}</strong> bölümü kayıtlarda henüz girilmemiş bilgileri “
        {EKSIK_ROZETI}” rozetiyle sayar. Bilgi girilince satır kendiliğinden kapanır; gerekçe
        istemez. Birlik dönemi açılmadıysa ya da birlik döneminin kural kopyası doğrulanamadıysa
        listenin yerinde bir bilgi bandı çıkar ve Birlik Dönemi ekranına götürür (
        <Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>).
      </p>

      <AltBaslik>Kurulumdan sonra ne yaparım</AltBaslik>
      {yetki.acik("yol_haritasi") ? (
        <>
          <p>
            Kurulum bitince sayfada <strong>Başlangıç Yol Haritası</strong> kartı durur ve programı
            okulda kullanmaya başlamak için sıradaki işleri sayar:
          </p>
          <ol className="list-decimal space-y-1 pl-5">
            {YOL_HARITASI_MADDELERI.map((madde) => (
              <li key={madde.anahtar}>
                {madde.baslik}
                {madde.bag && (
                  <>
                    {" "}
                    (<Ekran to={madde.bag.to}>{madde.bag.etiket}</Ekran>)
                  </>
                )}
              </li>
            ))}
          </ol>
          <p>
            Zarf maddesi dışındakiler, iş yapıldığında kendiliğinden işaretlenir. Zarf maddesini siz
            “Yapıldı” kutusuyla işaretlersiniz; program zarfın kapatıldığını bilemez. Geçiş kurulumu
            maddesi “Geçiş kurulumu tamamlandı” işareti konunca kapanır; okulda henüz genel kurul
            yapılmadıysa birlik dönemi genel kurulla açılana dek açık kalır. Bütün maddeler bitince
            “Kartı gizle” düğmesi çıkar.
          </p>
          <p>
            Kartın başında “{DOGRULANMADI_BASLIGI}” uyarısı varsa anahtarı sakladıysanız{" "}
            <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran>&apos;te doğrulayın;
            kaydedemediyseniz aynı yerden yenisini üretin.
          </p>
        </>
      ) : (
        <p>
          Başlangıç Yol Haritası programın kurulum işlerini sıralar; bu kart hesabınızda görünmez.
          Hesabınızla yapacağınız iş için program yöneticisine başvurun.
        </p>
      )}

      <AltBaslik>Uyarı kartı çıktıysa ne yaparım</AltBaslik>
      <ul className="list-disc space-y-2 pl-5">
        <li>
          <strong>{SON_OTURUM_KARTI_BASLIGI}:</strong> program önceki oturumda düzgün kapanmadı
          (elektrik kesintisi ya da zorla kapatma olabilir). Son girdiğiniz kayıtlara bakın, yerinde
          olmayanı yeniden girin. Hesabınızda “Kontrol ettim” düğmesi varsa ardından ona basın.
        </li>
        <li>
          <strong>{DENETIM_IZI_KARTI_BASLIGI}:</strong> kilit açılırken yapılan denetimin
          bulgularını yazar. Kart “program dışından yapılmış olabilecek bir değişiklik buldu”
          diyorsa program yöneticisine ve Denetleme Kuruluna bildirin; gerekirse sağlam bir yedekten
          geri yüklenir. “Bir bölümünü denetleyemedi” diyorsa ve durum sonraki girişlerde de
          sürüyorsa program yöneticisine bildirin. Bulgu denetim izinde kayıtlıdır; kart bir sonraki
          girişinizde kalkar.
        </li>
        <li>
          <strong>{DEGISTIRILMIS_HESAP_KARTI_BASLIGI}:</strong> bir hesabın kaydı program dışından
          değiştirilmiş görünüyor ya da parola kaydıyla uyuşmuyor; program işlemi yapmadı. Durumu
          Denetleme Kuruluna bildirin.
        </li>
        <li>
          <strong>{GERI_YUKLEME_KARTI_BASLIGI}:</strong> son geri yüklemenin anını, yedeği ve yedeği
          açanı yazar. Geri yüklemenin kayıtlara etkisi{" "}
          <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran> bölümündedir.
          Geri yüklemeyi kimin ve neden yaptığı Denetleme Kuruluna bildirilir. Denetleme Kurulundan
          bir üyenin “Gördüm” demesi yeter, kart herkes için kalkar; programda Denetleme Kurulunun
          açık hesabı yoksa kart kalır.
        </li>
        <li>
          <strong>{IKI_DEPO_KARTI_BASLIGI}:</strong> bu bilgisayarın güvenlik dosyasındaki
          hesaplarla veritabanındaki hesap kayıtları uyuşmuyor; bu çoğunlukla yedekten geri
          yüklemeden sonra olur. Giriş yapamayan hesapların parolasını program yöneticisi{" "}
          <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
            Kullanıcılar
          </KapiliEkran>{" "}
          ekranında hesabın ayrıntısından sıfırlar.
        </li>
        <li>
          <strong>{EKSIK_EKLER_KARTI_BASLIGI}:</strong> kaydı duran bir ekin dosyası bu bilgisayarda
          bulunamadı. Program yöneticisine ve Denetleme Kuruluna bildirin; gerekirse ekleri taşıyan
          şifreli yedekten geri yüklenir.
        </li>
        <li>
          <strong>{OKUNAMAYAN_ALANLAR_BASLIGI}:</strong> bazı şifreli alanlar okunamadı ve ekranda
          “okunamadı” diye görünür. Okunamayan alanı yeniden yazmadan önce program yöneticisine ve
          Denetleme Kuruluna bildirin; gerekirse sağlam bir yedekten geri yüklenir.
        </li>
        <li>
          <strong>{OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI}:</strong> kartların bir kısmı okunamadı, bir
          uyarı ya da giriş gösterilemiyor olabilir. Program yöneticisine ve Denetleme Kuruluna
          bildirin.
        </li>
        <li>
          <strong>Ayrılış Havuzu:</strong> e-Okul listesinde bulunmadığı için karar bekleyen kişi
          sayısını yazar. Kararı{" "}
          <KapiliEkran to="/kisiler?tab=havuz" yetenek="ayrilis_havuzu">
            Kişiler → Ayrılış Havuzu
          </KapiliEkran>{" "}
          sekmesinde verilir.
        </li>
        <li>
          <strong>{DIS_YEDEK_KARTI_BASLIGI}:</strong> son şifreli yedeğin üzerinden hatırlatma
          süresi geçti; kart yalnız son kaydın tarihine bakar. Adımlar{" "}
          <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran> bölümündedir.
        </li>
      </ul>

      <AltBaslik>Son girişlerinize bakmak</AltBaslik>
      <p>
        {SON_GIRISLER_KARTI_BASLIGI} kartı hesabınızla kilit ekranından yapılan son girişleri
        gösterir; ilki “bu oturum” diye işaretlidir. Tanımadığınız bir giriş varsa parolanızı
        değiştirin ve Denetleme Kuruluna bildirin.
      </p>
      <Ipucu>
        Kartın altındaki “Denetim izinin son kaydı” satırını zaman zaman tarihiyle birlikte kâğıda
        not edin. Sonradan burada görülen kayıt no&apos;su kâğıttakinden küçükse kayıtlar geri
        sarılmıştır; Denetleme Kuruluna bildirin.
      </Ipucu>
    </KilavuzBolumu>
  );
}
