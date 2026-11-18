// Kılavuz bölümü: Genel Bakış (çapa `genel-bakis`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Yol haritası maddeleri ekranın kendi sabitinden okunur (`YOL_HARITASI_MADDELERI`); kart adları
// `butunluk/metinler` ve kart bileşenlerinden, ne yapılacağı kartların kendi cümlelerinden ve
// sözlük §4.5'ten. Son Girişler'deki satırın ekrandaki öteki sözcüğü sözlük §1 gereği yazılmaz.
// Pano kalemleri (F1c 12. adım; tasarım §7.10) `pano/metinler`'in başlıklarıyla yazılır: hangi kalemin
// hangi rolde çıktığı sunucunundur (`pano.KALEM_ROLLERI`), bölüm rol adı saymaz, yalnız iki görünümü
// (veli rollerinde "Bu Ay Sizden Beklenenler", ötekilerde "Bu Hafta Yapılacaklar") anlatır. F2: sekmeler
// (Özet, Yıllık İş Takvimi; sözlük §1 "Yıllık İş Takvimi (F2)"), genel kurul süreleri ve dönem onayı
// kalemleri (plan F2 §6.3, 12. adım), süresiz takvim işlerinin "Yapıldı" işareti (yalnız `takvim_isareti`),
// yıllık iş takviminin basımı (yalnız `yillik_is_takvimi_uretme`), yeni açılan okulun yol haritası maddesi
// (`GENEL_KURUL_MADDESI`). Olağanüstü genel kurulda ikinci toplantı süresinin cümlesi iç karar kodu
// taşıdığı için alınmaz. F2 istisnası (13. adım, kullanıcı teyidi bekler): yalnız tek role çıkan ya da
// işi tek role ait F2 kalemlerinde rol anılır — müdürün bekleyen yazısı (okul müdürü), dönem onayı ve
// TEFBİS işareti (program yöneticisi), ibra edilmedi bildiriminin işareti (program yöneticisi, sekreter);
// kaynağı `pano.KALEM_ROLLERI` ve `uyum.TAKVIM_ISARETLEYENLERI`dir, matris değişirse bu cümleler de
// değişir. F1c kalemleri için yukarıdaki kural sürer.

import {
  DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
  DENETIM_IZI_KARTI_BASLIGI,
  EKSIK_EKLER_KARTI_BASLIGI,
  GERI_YUKLEME_KARTI_BASLIGI,
  IKI_DEPO_KARTI_BASLIGI,
  OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI,
  SON_GIRISLER_KARTI_BASLIGI,
} from "../../butunluk/metinler";
import { DUGME_EXCEL, DUGME_OLUSTUR, DUGME_PDF, E14_ADI } from "../../evrak/metinler";
import { DIS_YEDEK_KARTI_BASLIGI } from "../../guvenlik/DisYedekKarti";
import { DOGRULANMADI_BASLIGI } from "../../guvenlik/metinler";
import { useYetki } from "../../oturum/yetki";
import { GENEL_KURUL_MADDESI, YOL_HARITASI_MADDELERI } from "../../pano/BaslangicYolHaritasi";
import {
  ALAN_YAPILDIGI_GUN,
  AY_BASLIGI,
  DK_GOREV_BOLUMU_BASLIGI,
  DK_KADRO_BASLIGI,
  DK_YEDEK_BASLIGI,
  DONEM_ONAYI_BASLIGI,
  EKSIK_ROZETI,
  GECIS_BASLIGI,
  GK_IKINCI_TOPLANTI_BASLIGI,
  GK_ILAN_BASLIGI,
  GK_OLAGAN_BASLIGI,
  GK_YENI_OKUL_BASLIGI,
  GORUNUM_AY,
  GORUNUM_YIL,
  HAFTA_BASLIGI,
  HESAP_ONERISI_BASLIGI,
  IBRA_BILDIRIMI_BASLIGI,
  KURAL_SURUMU_BASLIGI,
  MUDUR_YAZISI_BASLIGI,
  SEKME_OZET,
  SEKME_TAKVIM,
  SON_GUN_ETIKETI,
  SURESI_DOLDU,
  TAKVIM_ACIKLAMASI,
  TAKVIM_DONEM_YOK,
  TAKVIM_UYARILARI,
  TAMAMLANACAKLAR_BASLIGI,
  TARIHSIZ_ISLER,
  TEFBIS_BASLIKLARI,
  TEFBIS_KONUMU,
  VERI_SORUMLUSU_TAMAMLANACAK,
  YAPILDI_ACIKLAMASI,
  YAPILDI_DUGMESI,
  YAPILDI_PENCERESI_BASLIGI,
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
        Kişiler ve Ayarlar kartları durur. Sayfanın iki sekmesi vardır:{" "}
        <Ekran to="/?tab=ozet">{SEKME_OZET}</Ekran> (açılışta gelen, bu kartların sekmesi) ve{" "}
        <Ekran to="/?tab=takvim">{SEKME_TAKVIM}</Ekran>.
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
        hesaplanır; iş kayıtlarda yapılınca kendiliğinden düşer. Son günü olmayan TEFBİS girişleri
        ve ibra edilmedi bildirimi ise program dışında yapılır; bunlar “{YAPILDI_DUGMESI}”
        işaretiyle düşer (aşağıda). Listede şu işler çıkabilir:
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
        <li>
          <strong>{KURAL_SURUMU_BASLIGI}</strong>: programla yeni bir kural sürümü geldi; açık
          birlik dönemi önceki sürümle hesaplanıyor (
          <Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>).
        </li>
      </ul>
      <p>Genel kurulun süreleri de bu listededir (md. 9/1, 9/2, 9/3):</p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>{GK_OLAGAN_BASLIGI}</strong> ya da yeni açılan okulda{" "}
          <strong>{GK_YENI_OKUL_BASLIGI}</strong>: genel kurul planlanmadı ya da birinci toplantının
          günü son günü aşıyor. Genel kurul planlanmadıysa işin son günü ilanın son günüdür.
        </li>
        <li>
          <strong>{GK_ILAN_BASLIGI}</strong>: toplantı ilan edilmedi ya da bir ilan kanalının günü
          girilmedi.
        </li>
        <li>
          <strong>{GK_IKINCI_TOPLANTI_BASLIGI}</strong>: birinci toplantıda yeter sayı sağlanamadı;
          işin cümlesi ikinci toplantının süresini ve ilanını yazar.
        </li>
        <li>
          <strong>{MUDUR_YAZISI_BASLIGI}</strong>: yalnız okul müdürünün hesabında; yeni açılan
          okulun daveti ya da müdürün çağrısının belgesi bekliyor.
        </li>
        <li>
          <strong>{IBRA_BILDIRIMI_BASLIGI}</strong>: hesaplar ibra edilmedi; durum il/ilçe millî
          eğitim müdürlüğüne resmî yazıyla bildirilir (md. 11/1-ç).
        </li>
        <li>
          <strong>{DONEM_ONAYI_BASLIGI}</strong>: yalnız program yöneticisinin hesabında; genel
          kurulun tutanağı tamamlandı, yeni birlik döneminin açılışı onay bekliyor.
        </li>
        <li>
          {Object.values(TEFBIS_BASLIKLARI).map((baslik, i) => (
            <span key={baslik}>
              {i > 0 && " · "}
              <strong>{baslik}</strong>
            </span>
          ))}
          : olağan genel kuruldan sonra TEFBİS&apos;e okul idaresinin yapacağı girişler (md. 23/5).{" "}
          {TEFBIS_KONUMU}
        </li>
      </ul>
      <p>
        Ayrıntı <Ekran to="/kilavuz#genel-kurul">Genel Kurul</Ekran> bölümündedir.
      </p>
      {yetki.acik("takvim_isareti") ? (
        <p>
          TEFBİS girişlerinin ve ibra edilmedi bildiriminin son günü yoktur; satırda “
          {SON_GUN_ETIKETI}” yazmaz. İş yapılınca satırdaki “{YAPILDI_DUGMESI}” düğmesine basın:{" "}
          <strong>{YAPILDI_PENCERESI_BASLIGI}</strong> penceresinde{" "}
          <strong>{ALAN_YAPILDIGI_GUN}</strong> girilir. {YAPILDI_ACIKLAMASI} TEFBİS girişlerini
          program yöneticisi, ibra edilmedi bildirimini program yöneticisi ya da sekreter işaretler.
        </p>
      ) : (
        <p>
          TEFBİS girişlerinin ve ibra edilmedi bildiriminin son günü yoktur. Yapıldığını program
          yöneticisi ya da sekreter işaretler; işaretlenen iş listeden düşer.
        </p>
      )}
      <p>
        <strong>{TAMAMLANACAKLAR_BASLIGI}</strong> bölümü kayıtlarda henüz girilmemiş bilgileri “
        {EKSIK_ROZETI}” rozetiyle sayar. Bilgi girilince satır kendiliğinden kapanır; gerekçe
        istemez. Program yöneticisinin hesabında şu satır da çıkabilir: “
        {VERI_SORUMLUSU_TAMAMLANACAK}” (<Ekran to="/kilavuz#okul-karti">Okul Bilgileri</Ekran>).
        Birlik dönemi açılmadıysa ya da birlik döneminin kural kopyası doğrulanamadıysa listenin
        yerinde bir bilgi bandı çıkar ve Birlik Dönemi ekranına götürür (
        <Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>).
      </p>

      <AltBaslik>{SEKME_TAKVIM}</AltBaslik>
      <p>
        {TAKVIM_ACIKLAMASI} Sekmeyi her hesap okur. Üstten birlik dönemi ve görünüm seçilir:{" "}
        {GORUNUM_YIL} (ay ay sıralı) ya da {GORUNUM_AY} (tek ay). Her satırda işin dayanağı madde
        numarasıyla ya da okulun planı olarak yazar. Günü toplantıya göre değişen ya da henüz belli
        olmayan işler <strong>{TARIHSIZ_ISLER}</strong> listesinde, takvimde eksik kalan bilgiler{" "}
        <strong>{TAKVIM_UYARILARI}</strong> listesinde durur. Birlik dönemi yoksa şu yazar: “
        {TAKVIM_DONEM_YOK}”
      </p>
      <p>
        Sekmenin altında <strong>{E14_ADI}</strong> belgesinin kartı durur; belge “{DUGME_PDF}” ya
        da “{DUGME_EXCEL}” düğmesiyle kaydedilir.{" "}
        {yetki.acik("yillik_is_takvimi_uretme")
          ? `Belge açık birlik döneminde “${DUGME_OLUSTUR}” düğmesiyle oluşturulur; hazırlıktaki birlik döneminin takvimi oluşturulmaz.`
          : "Belgeyi program yöneticisi oluşturur."}
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
            maddesi “Geçiş kurulumu tamamlandı” işareti konunca kapanır; birlik dönemi geçiş
            kurulumuyla açılmamışsa olağan genel kurul planlanınca kapanır. Bütün maddeler bitince
            “Kartı gizle” düğmesi çıkar.
          </p>
          <p>
            Okul Bilgileri&apos;nde okulun açılış tarihi girilmişse geçiş kurulumu maddesinin
            yerinde “{GENEL_KURUL_MADDESI.baslik}” durur. {GENEL_KURUL_MADDESI.aciklama} Madde ilk
            genel kurul planlanınca kapanır; genel kurul iptal edilirse yeniden açılır (
            <Ekran to={GENEL_KURUL_MADDESI.bag?.to ?? "/genel-kurul"}>
              {GENEL_KURUL_MADDESI.bag?.etiket}
            </Ekran>
            ).
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
