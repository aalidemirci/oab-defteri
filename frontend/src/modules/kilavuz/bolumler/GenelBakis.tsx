// Kılavuz bölümü: Genel Bakış (çapa `genel-bakis`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Yol haritası maddeleri ekranın kendi sabitinden okunur (`YOL_HARITASI_MADDELERI`); kart adları
// `butunluk/metinler` ve kart bileşenlerinden, ne yapılacağı kartların kendi cümlelerinden ve
// sözlük §4.5'ten. Son Girişler'deki satırın ekrandaki öteki sözcüğü sözlük §1 gereği yazılmaz.

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

      <AltBaslik>Kurulumdan sonra ne yaparım</AltBaslik>
      {yetki.acik("yol_haritasi") ? (
        <>
          <p>
            Kurulum bitince sayfanın başında <strong>Başlangıç Yol Haritası</strong> kartı durur ve
            programı okulda kullanmaya başlamak için sıradaki dört işi sayar:
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
            İlk üç madde, iş yapıldığında kendiliğinden işaretlenir. Zarf maddesini siz “Yapıldı”
            kutusuyla işaretlersiniz; program zarfın kapatıldığını bilemez. Bütün maddeler bitince
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
