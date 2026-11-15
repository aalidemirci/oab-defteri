// Kılavuz bölümü: Yedek ve Geri Yükleme (çapa `yedek-ve-geri-yukleme`). Başlık, ikon ve sıra
// `KilavuzPage`'dedir. Ekran adları sabitlerinden gelir; davranışlar `YedektenGeriYukleme`,
// `GuvenlikDosyasiKayip`, `desktop/restore.py` ve tasarım §4.4.4, §4.4.7, §4.5'ten doğrulandı.
//
// Yeni bilgisayarda kısayol yalnız yedek klasörünü listeler (`restore._choose_backup`): USB
// bellekteki dosya önce o klasöre kopyalanır. Pardus komutu dosyanın yolunu da alır.

import { GERI_YUKLEME_KARTI_BASLIGI, EKSIK_EKLER_KARTI_BASLIGI } from "../../butunluk/metinler";
import { DIS_YEDEK_KARTI_BASLIGI } from "../../guvenlik/DisYedekKarti";
import { KURTARMA_BELGESI_ADI } from "../../guvenlik/kurtarma";
import {
  DOSYA_KAYIP_BASLIGI,
  EKLER_OLMADAN_GERI_YUKLE,
  KAPSAM_TAM_METNI,
  KAPSAM_YEREL_METNI,
  SIFRELI_YEDEK_DUGMESI,
  SIFRELI_YEDEK_KARTI_BASLIGI,
  SIFRELI_YEDEK_YAZILDI,
  YEDEK_DOSYASI_SEC,
  YEDEK_LISTESI_BASLIGI,
  YEDEK_RAPORU_ADI,
  YEDEK_TURU_GUNCELLEME,
  YEDEK_TURU_GUNLUK,
  YEDEK_TURU_KURULUM,
} from "../../guvenlik/metinler";
import { YENIDEN_BASLAT_BASLIGI } from "../../guvenlik/YenidenBaslatEkrani";
import { DUGME_SIFIRLA, KULLANICILAR_BASLIGI } from "../../kullanicilar/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KapiliEkran, KilavuzBolumu, Kod } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

const YEDEK_TURLERI: ReadonlyArray<
  readonly [ad: string, neZaman: string, tasir: string, sure: string]
> = [
  [
    YEDEK_TURU_GUNLUK,
    "Program günde bir kez kendiliğinden alır: açılışta ya da açıkken gün değişince.",
    KAPSAM_YEREL_METNI,
    "14 gün",
  ],
  [
    YEDEK_TURU_GUNCELLEME,
    "Yeni sürüm kayıtlarda düzenleme gerektiriyorsa program, kayıtlara dokunmadan önce kendiliğinden alır.",
    KAPSAM_YEREL_METNI,
    "Son 5 yedek",
  ],
  [
    YEDEK_TURU_KURULUM,
    "Kurulumda, program yöneticisi hesabı açılmadan önce alınır.",
    "Listede durur ama geri yüklenemez: içinde açık bir program yöneticisi hesabı yoktur.",
    "14 gün",
  ],
  [SIFRELI_YEDEK_KARTI_BASLIGI, "Siz kaydedersiniz.", KAPSAM_TAM_METNI, "Program silmez"],
];

export default function YedekVeGeriYukleme(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program her gün kendiliğinden yedek alır; ama bu yedekler aynı bilgisayardadır ve ekleri
        taşımaz. Disk bozulur ya da bilgisayar kaybolursa onlar da gider. Okulun elinde kalan kopya,
        USB belleğe kaydettiğiniz şifreli yedektir.
      </p>
      {yetki.acik("guvenlik") ? (
        <p>
          Yedek kartları <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran> sekmesindedir.
        </p>
      ) : (
        <p>
          Yedek almak ya da geri yüklemek gerekirse program yöneticisine başvurun: bu kartlar
          hesabınızın Ayarlar → Güvenlik sekmesinde görünmez.
        </p>
      )}
      <Ipucu>
        Bu bölümü sorun çıkmadan önce okuyun. Program kilitliyken ya da açılmazken Kılavuz görünmez.
      </Ipucu>

      <AltBaslik>Program hangi yedekleri alır</AltBaslik>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-body-small">
          <thead>
            <tr className="border-b border-outline-variant text-on-surface">
              <th className="py-2 pr-3 font-semibold">Yedek</th>
              <th className="py-2 pr-3 font-semibold">Ne zaman</th>
              <th className="py-2 pr-3 font-semibold">Neyi taşır</th>
              <th className="py-2 font-semibold">Ne kadar durur</th>
            </tr>
          </thead>
          <tbody>
            {YEDEK_TURLERI.map(([ad, neZaman, tasir, sure]) => (
              <tr key={ad} className="border-b border-outline-variant align-top">
                <td className="py-2 pr-3 font-medium text-on-surface">{ad}</td>
                <td className="py-2 pr-3">{neZaman}</td>
                <td className="py-2 pr-3">{tasir}</td>
                <td className="py-2">{sure}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        Yedeklerin hepsi şifrelidir; şifresiz kopya üretilmez. Program kendi yedeklerini tablodaki
        süreyle siler; program açılmadan geçen günlerde silme bekler.
      </p>

      <AltBaslik>Şifreli yedeği USB belleğe kaydetmek için</AltBaslik>
      <ol className="list-decimal space-y-1 pl-5">
        <li>USB belleği takın.</li>
        <li>
          Ayarlar → Güvenlik → {SIFRELI_YEDEK_KARTI_BASLIGI} kartında “{SIFRELI_YEDEK_DUGMESI}”
          düğmesine basın.
        </li>
        <li>
          Açılan pencerede yer olarak USB belleği seçin. Dosyanın adını program önerir; uzantısını
          değiştirmeyin. Pardus&apos;ta USB belleği pencerenin solundaki listeden seçin; ad alanına
          tam yol yazmayın.
        </li>
        <li>
          Bekleyin: program dosyayı yazar, yeniden açıp denetler. Bu iş birkaç dakika sürebilir.
        </li>
        <li>
          Kartta “{SIFRELI_YEDEK_YAZILDI}” yazısını, dosyanın boyunu ve taşıdığı ek sayısını görün.
          Belleği çıkarın ve bilgisayardan ayrı saklayın.
        </li>
      </ol>
      <p>
        Program dosyanın USB bellekte olduğunu bilemez, yalnız seçilen yere sağlam yazıldığını
        bilir: yeri siz doğru seçmelisiniz.
      </p>
      <Ipucu>
        Yer olarak USB belleği ya da okulun ağ diskini seçin; bulut depolama hizmetine yüklemeyin
        (Bilgi ve Sistem Güvenliği Yönergesi md. 11/23).
      </Ipucu>

      <AltBaslik>Hatırlatmayı ayarlamak ve yedekleri görmek için</AltBaslik>
      <p>
        Süre dolunca <Ekran to="/">Genel Bakış</Ekran>&apos;ta “{DIS_YEDEK_KARTI_BASLIGI}” kartı
        çıkar. Süreyi {SIFRELI_YEDEK_KARTI_BASLIGI} kartındaki “Hatırlatma süresi” seçiminden
        değiştirirsiniz (7, 14, 30, 60 ya da 90 gün; başlangıçta 30 gün). Hiç şifreli yedek
        kaydedilmediyse kart, ilk hesap kurulduktan 7 gün sonra çıkar.
      </p>
      <p>
        {YEDEK_RAPORU_ADI} kartındaki “PDF olarak kaydet” düğmesi bu bilgisayardaki yedeklerin tek
        sayfalık dökümünü verir: türleri, tarihleri, yedekleri açan kurtarma anahtarları ve son
        şifreli yedek. Belgede kişi adı yoktur.
      </p>

      <AltBaslik>Eski bir güne dönmek için</AltBaslik>
      <ol className="list-decimal space-y-1 pl-5">
        <li>Ayarlar → Güvenlik → Yedekten Geri Yükleme kartını bulun.</li>
        <li>
          “{YEDEK_LISTESI_BASLIGI}” listesinden birini seçin. USB bellekteki yedek için “
          {YEDEK_DOSYASI_SEC}” düğmesine basın; program dosyayı yerinde okur, silmez.
        </li>
        <li>Kart, seçilen yedeği hangi kurtarma anahtarının açtığını yazar. Ona bakın.</li>
        <li>“Parolanız” ya da “Kurtarma anahtarı” alanlarından birini doldurun.</li>
        <li>“Geri yükle” düğmesine basın ve onay penceresini okuyun.</li>
        <li>
          “{YENIDEN_BASLAT_BASLIGI}” ekranı gelince programdan çıkın ve yeniden açın. Ekrandaki
          “Ekler” satırı eklerin durumunu söyler.
        </li>
      </ol>
      <ul className="list-disc space-y-1 pl-5">
        <li>O yedekten sonra girilen kayıtlar ekrandan kalkar.</li>
        <li>
          Geri yüklemeden önceki veritabanı veri klasöründe kenara alınır; 14 gün saklanır, sonra
          silinir.
        </li>
        <li>
          Yeniden açılışta Genel Bakış&apos;ta “{GERI_YUKLEME_KARTI_BASLIGI}” kartı çıkar; kartta ne
          yapılacağı <Ekran to="/kilavuz#genel-bakis">Genel Bakış</Ekran> bölümündedir.
        </li>
        <li>
          Yedekteki bir ek bozuksa geri yükleme hiçbir şeyi değiştirmeden durur ve eklerin kişisiz
          listesini verir. “{EKLER_OLMADAN_GERI_YUKLE}” düğmesi kayıtları o ekler olmadan geri
          yükler; “Vazgeç” işlemi bırakır.
        </li>
      </ul>

      <AltBaslik>Parola mı, kurtarma anahtarı mı</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>Parolanız:</strong> oturumu açan program yöneticisinin bugünkü parolasıdır ve
          yalnız bu bilgisayarda alınmış yedeği açar.
        </li>
        <li>
          <strong>Kurtarma anahtarı:</strong> yedeğin alındığı gün geçerli olan anahtardır. Başka
          bir bilgisayarda ve güvenlik dosyası kayıpken tek yol budur. Anahtar okul müdürlüğündeki
          kapalı zarftadır.
        </li>
      </ul>
      <p>
        Bu bilgisayardaki güncel kayıtlar okunamıyorsa program parolayı yedeğin içindeki hesaplarla
        denetler. Yedek alındıktan sonra açılmış ikinci bir program yöneticisi hesabı o yedekte
        yoktur, bu hesabın parolasıyla geri yükleme yapılamaz. Parolası yedekten sonra değişmiş
        program yöneticisi için de aynısı geçerlidir. Bu durumlarda çıkış kurtarma anahtarıdır.
      </p>

      {yetki.acik("guvenlik") ? (
        <>
          <AltBaslik>Kurtarma anahtarını yenilemek için</AltBaslik>
          <p>
            Kâğıt kaybolduysa <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran>{" "}
            sekmesindeki Kurtarma Anahtarını Yenile kartından yeni anahtar üretin.
          </p>
          <ol className="list-decimal space-y-1 pl-5">
            <li>“Kurtarma anahtarını yenile” düğmesine basın.</li>
            <li>
              “Parolanız” alanına oturumu açan hesabın parolasını yazın, “Yeni anahtar üret”
              düğmesine basın.
            </li>
            <li>
              Yeni anahtar bir kez gösterilir, no&apos;su bir artar. Saklayın, “Sakladım, doğrula”
              düğmesine basın ve program hangi iki grubu sorarsa yazın. Doğrulamadan programı
              kapatmayın, kilitlemeyin.
            </li>
            <li>
              Yeni kâğıdı okul müdürlüğündeki zarfa koyun. Eski kâğıt elinizdeyse “Eski anahtar —
              bugünden önceki yedekler için” diye işaretleyip ayrı saklayın.
            </li>
          </ol>
          <p>
            Hesapların parolaları değişmez, kayıtlar yeniden şifrelenmez. Kâğıt başkasının eline
            geçtiyse yenileme tek başına yetmez:{" "}
            <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran> bölümünü
            okuyun.
          </p>

          <AltBaslik>Kurtarma anahtarı belgesini yeniden almak için</AltBaslik>
          <p>
            Elle yazılmış kâğıdın temiz kopyası gerekirse aynı sekmedeki {KURTARMA_BELGESI_ADI}{" "}
            kartında “Kurtarma anahtarı” alanına elinizdeki anahtarı yazıp “PDF olarak kaydet”
            düğmesine basın. Anahtar programda saklanmadığı için anahtarsız belge alınamaz.
            PDF&apos;i bu bilgisayarda bırakmayın.
          </p>
        </>
      ) : (
        <p>
          Kurtarma anahtarının yenilenmesi ya da belgesinin yeniden alınması gerekirse program
          yöneticisine başvurun.
        </p>
      )}

      <AltBaslik>Program hiç açılmıyorsa</AltBaslik>
      <p>
        Program kapalıyken Windows&apos;ta Başlat menüsündeki “OAB Defteri — Yedekten Geri Yükle”
        kısayolunu, Pardus&apos;ta uçbirimden <Kod>oab-defteri --geri-yukle</Kod> komutunu
        çalıştırın. Açılan pencerede:
      </p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>Bu bilgisayardaki yedekler listelenir; geri yüklenecek yedeğin numarasını yazın.</li>
        <li>
          Program yöneticisi hesabının tanıtıcısını ve parolasını yazın. Kurtarma anahtarıyla
          açacaksanız tanıtıcıyı boş bırakıp anahtarı yazın.
        </li>
        <li>“Devam edilsin mi?” sorusuna e yazın.</li>
        <li>İş bitince programı her zamanki gibi açın.</li>
      </ol>

      <AltBaslik>Kayıtları yeni bilgisayara taşımak için</AltBaslik>
      <ol className="list-decimal space-y-1 pl-5">
        <li>Eski bilgisayar açılıyorsa son bir şifreli yedek kaydedin.</li>
        <li>
          Okul müdürlüğündeki zarftan o yedeğin kurtarma anahtarını alın. Taşınan yedeğin kayıtları,
          ekleri ve üretilen evrakı birlikte taşıması için şifreli yedek kullanın.
        </li>
        <li>Programı yeni bilgisayara kurun, ama açıp sihirbazı doldurmayın.</li>
        <li>
          Başlat menüsündeki kısayolu bir kez çalıştırın. Pencere “Yedek klasörü” yolunu yazar ve
          klasör boş olduğu için durur. USB bellekteki yedeği o klasöre kopyalayıp kısayolu yeniden
          çalıştırın. Pardus&apos;ta komutun ardına yedek dosyasının yolunu yazmanız yeterlidir.
        </li>
        <li>
          Yedeğin numarasını yazın, tanıtıcıyı boş bırakın, kurtarma anahtarını yazın ve onaylayın.
        </li>
        <li>
          Programı açın. Kilit ekranı kurtarma yolunu doğrudan açar: anahtarı yazın, program
          yöneticisi hesabını seçin, yeni parolayı belirleyin ve “Kurtar ve aç” düğmesine basın.
        </li>
        <li>
          Öteki hesapların durumu “Parola yenilenmeli” olur.{" "}
          <KapiliEkran to="/kullanicilar" yetenek="kullanicilar">
            {KULLANICILAR_BASLIGI}
          </KapiliEkran>{" "}
          ekranında her biri için “{DUGME_SIFIRLA}” ile geçici parola verin.
        </li>
        <li>
          Genel Bakış&apos;ta “{EKSIK_EKLER_KARTI_BASLIGI}” kartı çıkmadığına bakın. Kart çıkarsa
          dosyası gelmeyen ekler orada yazar.
        </li>
      </ol>
      <p>
        Sihirbazı daha önce bitirdiyseniz aynı yedeği Yedekten Geri Yükleme kartındaki “
        {YEDEK_DOSYASI_SEC}” düğmesiyle seçip “Kurtarma anahtarı” alanını doldurabilirsiniz.
        Sihirbazın verdiği kurtarma anahtarı bundan sonra geçmez; yedeğin anahtarı geçerlidir.
      </p>

      <AltBaslik>“{DOSYA_KAYIP_BASLIGI}” ekranı çıkarsa</AltBaslik>
      <p>
        Hesapların ve kayıtların anahtarını saklayan güvenlik dosyası kaybolmuş ya da bozulmuştur;
        dosya olmadan kayıtlar açılamaz. Program yöneticisine haber verin. Ekrandaki yollar
        şunlardır:
      </p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          Dosyanın sağlam bir kopyası varsa onu, ekranda yazan adla veri klasörüne geri koyup
          “Yeniden denetle” düğmesine basın.
        </li>
        <li>
          Kopya yoksa ekranın altındaki Yedekten Geri Yükleme kartından en yeni yedeği seçin. Burada
          parola işlemez, yedeğin kurtarma anahtarı gerekir. Program yeniden açılınca kilit
          ekranında kurtarma anahtarıyla açıp program yöneticisinin yeni parolasını belirlersiniz. O
          yedekten sonra girilen kayıtlar ekrandan kalkar.
        </li>
        <li>
          Korunacak kayıt yoksa ekranda Güvenlik Dosyasını Sıfırlama kartı da görünür; “Güvenlik
          dosyasını sıfırla ve kuruluma dön” okunamayan dosyayı arşivleyip kurulum sihirbazını açar.
          Kart görünmüyorsa bu yol kapalıdır.
        </li>
      </ol>

      <AltBaslik>USB bellekteki yedeği saklamak ve imha etmek için</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          USB bellekteki yedek programın dışındadır: program ona ulaşamaz, onu silemez. Saklanması
          ve imhası okulun sorumluluğundadır.
        </li>
        <li>
          Yedek, alındığı günkü bütün kayıtları taşır. Programdan sonradan silinen kişisel veri,
          daha önce kaydettiğiniz yedekte durmayı sürdürür.
        </li>
        <li>
          Yeni bir şifreli yedek kaydedip denetlendiğini gördükten sonra, gereği kalmayan eski
          yedekleri bellekten silin. Bellek başka işe verilecekse içinde yedek bırakmayın.
        </li>
        <li>
          Her yedek kendi kurtarma anahtarıyla açılır. Anahtarı yenilediyseniz eski kâğıdı “Eski
          anahtar” diye işaretleyip saklayın; o anahtarla açılan yedekler durdukça kâğıdı atmayın.
          Eski kâğıt yok edilirse o yedekler başka bir bilgisayarda açılamaz.
        </li>
      </ul>
    </KilavuzBolumu>
  );
}
