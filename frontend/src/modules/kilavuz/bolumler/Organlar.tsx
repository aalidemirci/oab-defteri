// Kılavuz bölümü: Organlar (çapa `organlar`). Başlık, ikon ve sıra `KilavuzPage`'dedir. Ekran, sekme,
// düğme ve pencere adları `organlar/metinler`'den ve `organlar/OrganlarPage`'in sekme listesinden; belge
// kartının adları `evrak/metinler`'den; uyarı ve gerekçenin adları `uyum/metinler`'den. Kaynaklar:
// sözlük §1 "Organlar ekranı (F1c)", "Görev bölümü ve temsilci evrakı (F1c)", "Uyarı ve gerekçe
// bileşeni (F1c)"; tasarım §5.2.2, §7.2, §9.6; plan F1c kararları ve 5-6., 10., 11. adım notları (görev
// bölümünü yönetim kurulunda sekreter, Denetleme Kurulunda kurulun kendisi yazar; Denetleme Kurulu
// yedeğini program yöneticisi çağırır; görev alma engelinin dayanağını yalnız program yöneticisi ve
// yönetim kurulu rolleri okur; aylık toplantı günü kural değildir; belge kartları). Sert engeller
// CLAUDE.md altın kural 3'teki listedir. Alıntılar `docs/mevzuat/meb-okul-aile-birligi-yonetmeligi.md`
// ile birebirdir (md. 12/3, 13/6). Genel kurul ve yönetim kurulu toplantılarının ekranı bu sürümde
// yoktur, vaat edilmez. Düğmelerin hangi hesapta göründüğü ekranın yeteneklerine bağlıdır; bölüm her
// adımı anlatır, kimin yaptığını ekranın kendi cümlesiyle söyler.

import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  DUGME_YENIDEN_OLUSTUR,
  E01_ADI,
  E02_ADI,
  TASLAK_ACIKLAMASI,
  URETIM_UYARILARI_BASLIGI,
  URETIM_UYARILARI_NOTU,
} from "../../evrak/metinler";
import {
  ALAN_YEDEK_KARARI,
  BOLUM_ASILLAR,
  BOLUM_OTEKI,
  BOLUM_YEDEKLER,
  CIP_DEVRALINAN,
  CIP_ENGEL,
  DAYANAK_OKUMA_NOTU,
  DUGME_BILGILER,
  DUGME_DAYANAK,
  DUGME_DK_GOREV_BOLUMU,
  DUGME_DUSUR,
  DUGME_ENGEL,
  DUGME_GOREV_BOLUMU,
  DUGME_KAYDI_IPTAL,
  DUGME_KOMISYON_UYESI_EKLE,
  DUGME_OGRETMEN_EKLE,
  DUGME_YEDEK_CAGIR,
  DUSME_TURU_TR,
  ERTELE_YARDIMI,
  KADRO_UYARILARI_BASLIGI,
  ONERILER_BASLIGI,
  ORGANLAR_BASLIGI,
  SEKME_ALIM,
  SEKME_DK,
  SEKME_YK,
  TOPLANTI_GUNU_BASLIGI,
} from "../../organlar/metinler";
import { useYetki } from "../../oturum/yetki";
import {
  DONEM_KILIDI_BASLIGI,
  GEREKCE_BASLIGI,
  GEREKCEYLE_KAYDET,
  KURAL_SERT_BASLIGI,
} from "../../uyum/metinler";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Mevzuat } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Elle seçilebilen düşme türleri (olağanüstü genel kurulun seçimi elle seçilmez; sözlük). */
const ELLE_DUSME_TURLERI = (Object.keys(DUSME_TURU_TR) as Array<keyof typeof DUSME_TURU_TR>)
  .filter((tur) => tur !== "OLAGANUSTU_GK_SECIMI")
  .map((tur) => DUSME_TURU_TR[tur])
  .join(" · ");

export default function Organlar(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/organlar">{ORGANLAR_BASLIGI}</Ekran> ekranı okul-aile birliğinin kurullarını
        gösterir: <Ekran to="/organlar?tab=yk">{SEKME_YK}</Ekran>,{" "}
        <Ekran to="/organlar?tab=dk">{SEKME_DK}</Ekran> ve{" "}
        <Ekran to="/organlar?tab=alim">{SEKME_ALIM}</Ekran>. Ekranı her hesap okur; kayıtlar birlik
        dönemine yazılır, birden çok birlik dönemi varsa üstten seçilir. Birlik dönemi açılmadıysa
        ekran boş görünür (<Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>). Program karar
        defterinin yerine geçmez: kurulun kararları karar defterine el ile yazılır.
      </p>

      <AltBaslik>Kadroyu okumak</AltBaslik>
      <p>
        Kurul sekmesinde kadro özeti (asıl ve yedek üye sayısı), <strong>{BOLUM_ASILLAR}</strong>,{" "}
        <strong>{BOLUM_YEDEKLER}</strong> ve <strong>{BOLUM_OTEKI}</strong> durur. Öteki kayıtlar
        aday, düşen ve iptal edilen kayıtlardır; kayıt silinmez. Bir satıra basınca üyeliğin
        penceresi açılır: durum, koltuk, görev, seçildiği yer ve gün, seçilme sayısı ve açık
        uyarılar burada yazar. Satırda “{CIP_DEVRALINAN}” işareti geçiş kurulumuyla girilen kaydı, “
        {CIP_ENGEL}” işareti görev alma engelini gösterir.
      </p>
      <p>
        <strong>{KADRO_UYARILARI_BASLIGI}</strong> eksik koltukları, başkanı seçilmemiş kurulu ve
        benzeri durumları dayanağıyla yazar; <strong>{ONERILER_BASLIGI}</strong> yapılması önerilen
        işleri (yedek çağrısı, düşme önerisi) sayar. Uyarı kaydı engellemez.
      </p>

      <AltBaslik>Uyarı, gerekçe ve engel</AltBaslik>
      <p>
        Program doğrusunu gösterir. Kayıt bir hükümden sapıyorsa “{GEREKCE_BASLIGI}” kutusu açılır;
        uyarının metni ve dayanağı kutuda yazar. Gerekçeyi yazıp “{GEREKCEYLE_KAYDET}” düğmesine
        basarsanız kayıt gerekçesiyle kayda geçer. Henüz girilmemiş bilgi eksik sayılır, gerekçe
        istemez. Kutu açıkken yazdığınız metin kendiliğinden saklanır: program kapansa da kaybolmaz,
        Genel Bakış yarım kalan taslak olarak hatırlatır; Vazgeç metni siler.
      </p>
      <p>
        Şu durumlarda kayıt hiç yapılmaz ve “{KURAL_SERT_BASLIGI}” bandı çıkar: okul müdürü yönetim
        kuruluna eklenemez; aynı kişi aynı birlik döneminde hem yönetim kurulunda hem Denetleme
        Kurulunda olamaz; aynı kişi aynı kurulda ikinci koltuk alamaz; bir görev (örneğin başkanlık)
        iki kişiye verilemez; kurula mevzuatın saymadığı türde kişi giremez (yönetim kuruluna veli,
        on sekiz yaşını doldurmuş kursiyer ya da okul yaptıran hayırsever girer, md. 12/1). Kapanmış
        birlik döneminde ya da tamamlanmış geçiş kurulumunda “{DONEM_KILIDI_BASLIGI}” bandı çıkar.
      </p>

      <AltBaslik>Üyeler nereden gelir</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          Yönetim kurulunu ve Denetleme Kurulunun veli üyesini genel kurul seçer. Programdan önce
          seçilmiş görevdeki kurul geçiş kurulumunda girilir (
          <Ekran to="/kilavuz#gecis-kurulumu">Geçiş Kurulumu</Ekran>); bu sürümde genel kurulun
          seçimi programda yapılmaz.
        </li>
        <li>
          Denetleme Kurulunun öğretmen üyelerini öğretmenler kurulu seçer; okulda yeteri kadar
          öğretmen yoksa il/ilçe millî eğitim müdürü onayıyla başka okulların öğretmenleri
          görevlendirilir (md. 14/1). Bu üyeler “{DUGME_OGRETMEN_EKLE}” düğmesiyle girilir.
        </li>
        <li>
          Alım komisyonu en az üç kişidir (md. 18/1); üyeler “{DUGME_KOMISYON_UYESI_EKLE}”
          düğmesiyle girilir. Yönetim kurulu üyesi olmayan birlik üyesi yalnız uzmanlık gerektiren
          işlerde komisyona girer.
        </li>
        <li>
          Kişiler önce <Ekran to="/kilavuz#birlik-kisileri">Birlik Kişileri</Ekran>&apos;nde
          kaydedilir.
        </li>
      </ul>

      <AltBaslik>Görev bölümü</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 12/3">
        Yönetim kurulu, seçimden sonraki ilk hafta içinde okulda toplanarak üyeleri arasından bir
        başkan, bir başkan yardımcısı, bir muhasip ve bir sekreter seçerek görev ve iş bölümü yapar.
        Yönetim kurulu üyelerinden üyeliği sona erenlerin yerine yedeklerin çağrılmasıyla oluşan
        yeni yönetim kurulu bir hafta içinde toplanarak aralarında görev dağılımı yaparlar.
      </Mevzuat>
      <p>
        Yönetim kurulunun görev bölümünü sekreter “{DUGME_GOREV_BOLUMU}” düğmesiyle girer:
        toplantının günü, saati ve yeri, görevdeki her asıl üyenin katılımı ve verilen görevler.
        Yalnız verilen görevler seçilir; görevin önceki sahibi üye olur. Kayıt bir görev bölümü
        toplantısı ve karar taslağı açar. Görevi değişen üyenin hesabı askıya alınır; yeni görevin
        hesabı Kullanıcılar ekranında açılır. Başkan seçilmeden de görev bölümü kaydedilir, kadro
        uyarısı başkanı eksik gösterir.
      </p>
      <p>
        Denetleme Kurulunun asıl üyeleri genel kuruldan sonraki ilk hafta içinde toplanıp
        aralarından bir başkan seçer (md. 14/1). Bunu Denetleme Kurulu kendi hesabıyla “
        {DUGME_DK_GOREV_BOLUMU}” düğmesinden girer; denetim planına yönetim kurulunun
        faaliyetlerinin inceleneceği günler yazılır, kurul bu incelemeyi yılda en az iki defa yapar
        (md. 14/4).
      </p>
      <p>
        Görev bölümünün son günü Genel Bakış&apos;ta yapılacak iş olarak görünür. Yönetim kurulunda
        bir haftalık süre kurulun bugünkü bileşiminin oluştuğu günden sayılır; bileşim değişmeden
        yapılan görev değişimi süreye bağlı değildir.
      </p>

      <AltBaslik>Yedek çağrısı</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 13/6">
        Özürsüz olarak üst üste üç toplantıya katılmayan yönetim kurulu üyesinin görevi sona erer.
        Bu şekilde görevi sona erenler ile öğrencisinin okuldan ayrılması veya öğrenciliğin sona
        ermesi nedenleriyle yönetim kurulu üyeliği sona eren velinin yerine yedek üyeler, aldıkları
        oy sırasına göre asıl üye olarak göreve çağırılır.
      </Mevzuat>
      <p>
        Yedek üye, penceresindeki “{DUGME_YEDEK_CAGIR}” düğmesiyle çağrılır. Yönetim kurulunda
        yedekler oy sırasıyla çağrılır; sıra dışı çağrı gerekçe ister.{" "}
        <strong>{ALAN_YEDEK_KARARI}</strong> alanında yalnız kabul edilmiş ya da karar defterine
        işlenmiş yönetim kurulu kararı bağlanabilir; karar bağlanmadan yapılan çağrı gerekçe ister.
        Yeni bileşimle kurul bir hafta içinde yeniden görev dağılımı yapar. Denetleme Kurulunun
        yedeği yönetim kurulu kararı gerekmeden çağrılır ve kendi koltuğunun asıl yerine geçer;
        öğretmen üye başka kurumda dört aydan fazla süreli görevlendirilirse yerine yedeği çağrılır
        (md. 14/6).
      </p>

      <AltBaslik>Üyeliğin düşmesi ve kaydın iptali</AltBaslik>
      <p>
        Üyeliği sona eren üyenin penceresinde “{DUGME_DUSUR}” düğmesi kullanılır. Düşme türleri:{" "}
        {ELLE_DUSME_TURLERI}. Olağanüstü genel kurulun seçimiyle düşme elle girilmez. Yönetim
        kurulunda öğrencisi okuldan ayrılan velide ek bir kutu çıkar: {ERTELE_YARDIMI} Düşen üyelik
        kurulun geçmişinde kalır; üyeliğe bağlı hesap aynı anda askıya alınır.
      </p>
      <p>
        Yanlış girilmiş kayıt “{DUGME_KAYDI_IPTAL}” düğmesiyle gerekçe yazılarak iptal edilir; kayıt
        silinmez, değiştirilmez. Doğru bilgi yeni kayıtla girilir. İptal edilen kayıt koltuk tutmaz
        ve seçilme sayısına girmez. Beyan günleri, yedek sırası ve görevlendirme tarihleri gibi
        bilgiler “{DUGME_BILGILER}” düğmesiyle tamamlanır.
      </p>

      <AltBaslik>Görev alma engeli</AltBaslik>
      <p>
        Suç engeli (md. 12/5, 14/7) ve başka birlik yönetiminde görev (md. 12/4) “{DUGME_ENGEL}”
        düğmesiyle tespit günüyle kaydedilir. Engelin dayanağı özel nitelikli kişisel veridir:
        şifreli saklanır, yalnız program yöneticisi ve yönetim kurulu rolleri okur.{" "}
        {yetki.acik("gorev_alma_engeli")
          ? `Dayanak önceden gösterilmez; “${DUGME_DAYANAK}” düğmesine basınca açılır. ${DAYANAK_OKUMA_NOTU}`
          : "Hesabınızda satırda yalnız engelin var olduğu görünür."}
      </p>

      <AltBaslik>{TOPLANTI_GUNU_BASLIGI}</AltBaslik>
      <p>
        Yönetim kurulu eğitim ve öğretim yılı içinde ayda bir toplanır (md. 13/3); günü kurul
        belirler. Yönetim Kurulu sekmesindeki {TOPLANTI_GUNU_BASLIGI} kartına gün serbest metinle
        yazılır (örneğin “her ayın ilk salısı”). Program bu günü karar taslağına yazar, ona bağlı
        bir kural koymaz.
      </p>

      <AltBaslik>Görev bölümü belgeleri</AltBaslik>
      <p>
        Yönetim Kurulu sekmesinde <strong>{E01_ADI}</strong>, Denetleme Kurulu sekmesinde{" "}
        <strong>{E02_ADI}</strong> kartı durur. {TASLAK_ACIKLAMASI}
      </p>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          Görev bölümünü girdikten sonra “{DUGME_OLUSTUR}” düğmesine basın. Yönetim kurulunun karar
          taslağını sekreter ya da program yöneticisi, Denetleme Kurulunun tutanağını Denetleme
          Kurulu oluşturur.
        </li>
        <li>
          Kartta <strong>{URETIM_UYARILARI_BASLIGI}</strong> listesi çıkarsa okuyun.{" "}
          {URETIM_UYARILARI_NOTU}
        </li>
        <li>
          “{DUGME_PDF}” ya da “{DUGME_WORD}” düğmesiyle dosyayı seçtiğiniz yere kaydedin. Kaydetmeyi
          her hesap yapabilir; her kaydetme denetim izine yazılır.
        </li>
      </ol>
      <p>
        Bilgi değişirse “{DUGME_YENIDEN_OLUSTUR}” yeni bir sürüm üretir; önceki sürüm silinmez.
        Banka hesabının satırları ve karar defterindeki sıra no ile sayfa, bu bilgiler programda
        girilene dek belgede “………” diye boş basılır; elle doldurulur. Belgede T.C. kimlik numarası
        ve kurum kodu yoktur.
      </p>
      <Ipucu>
        Karar taslağı karar defterine el ile yazılır ve imzalanır (md. 13/5); programın çıktısı
        defterin yerine geçmez. Denetleme Kurulunun tutanağı kurul üyelerince imzalanır.
      </Ipucu>
    </KilavuzBolumu>
  );
}
