// Kılavuz bölümü: Güvenlik ve Kişisel Veriler (çapa `guvenlik-ve-kvkk`). Başlık, ikon ve sıra
// `KilavuzPage`'dedir. Dayanak: tasarım §3.4 ("Veri sorumlusu", aydınlatma, e-Okul kaynaklı veri),
// §4.3 (sınır cümlesi, tehdit 6 ve 20), §4.4.6 (dürüst sınırlar), §4.5 "Hesap ve bilgisayar", M-8,
// TK7; KVKK ve Yönerge atıfları docs/mevzuat'tan doğrulandı.
//
// Dürüst sınırların metni Hakkında'yla tek kaynaktır (`DURUST_SINIRLAR`). Denetim izi maddesindeki
// satır adı ("Zincir") kılavuzda geçmez (sözlük §1): aynı satır kartın başlığıyla anılır.

import { ERISIM_GUNLUGU_BASLIGI } from "../../erisim/metinler";
import { DURUST_SINIRLAR, KAPSAM_DISI_METNI, KAPSAM_METNI } from "../../guvenlik/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

const SINIR_SATIRI = "“Kayıt no · Zincir” satırını";
const SINIR_SATIRI_KILAVUZDA = "“Denetim izinin son kaydı” satırını";

export default function GuvenlikVeKisiselVeriler(bolum: BolumProps) {
  const yetki = useYetki();
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <strong>
          Program bir izlenebilirlik ve kaza önleme aracıdır; asıl güvenlik sınırı Windows hesabı ve
          disk şifrelemesidir
        </strong>{" "}
        (Windows&apos;ta BitLocker, Pardus&apos;ta LUKS). Programdaki hesaplar “kim, ne zaman, ne
        yaptı” sorusunu cevaplar. Bilgisayarı korumak gibi teknik ve idari tedbirleri almak veri
        sorumlusunun yükümlülüğüdür (Kişisel Verilerin Korunması Kanunu, KVKK md. 12/1); veri
        sorumlusunun kim olduğu bu bölümün sonundaki “Okul müdürlüğünün değerlendireceği sorular”
        başlığındadır.
      </p>

      <AltBaslik>Program neyi şifreler</AltBaslik>
      <p>{KAPSAM_METNI}</p>
      <p>{KAPSAM_DISI_METNI}</p>
      <p>
        Durumu <Ekran to="/ayarlar?tab=guvenlik">Ayarlar → Güvenlik</Ekran> sekmesindeki Şifreleme
        kartında görürsünüz.
      </p>

      <AltBaslik>Bilgisayarı hazırlamak için</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          Programı okul demirbaşı bir bilgisayara kurun. Evdeki bir bilgisayara kurulması önerilmez:
          kişisel veri ve mali kayıt kurum dışına çıkar, devir zorlaşır.
        </li>
        <li>Diski şifreleyin: Windows&apos;ta BitLocker, Pardus&apos;ta LUKS.</li>
        <li>
          Kayıtlar, programı çalıştıran Windows hesabının klasöründedir; başka bir Windows hesabıyla
          açılan programda görünmez. Pardus&apos;ta programı kendi kullanıcı hesabınızda çalıştırın.
        </li>
      </ul>

      <AltBaslik>Ayrı bir Windows hesabı açmak için</AltBaslik>
      <p>
        Öneri, zorunlu değil: bilgisayarda yönetici yetkisi olmayan ayrı bir “OAB” Windows hesabı
        açın. Böylece program yöneticisinin e-Okul ve e-posta gibi hizmetlerin açık olduğu kişisel
        oturumu velilere açılmaz.
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          Bu ortak hesabın parolası yalnız görevdeki kurul üyelerinde ve program yöneticisinde olur.
          Kurul değiştiğinde parolayı program yöneticisi değiştirir.
        </li>
        <li>
          Ortak hesap kullanılacaksa kurulumda bütün kullanıcılar için kurmayı seçin. Bu seçenek ve
          sonraki her güncelleme bilgisayarın yönetici yetkisini ister; karşılığında program
          dosyalarını ortak hesap değiştiremez.
        </li>
        <li>
          Programı kendi Windows hesabınızda tek başınıza kullanıyorsanız yalnız kendiniz için
          kurmak yeterlidir.
        </li>
        <li>
          Yalnız bir kullanıcı için kurulumu ortak hesapla birlikte kullanmayın: ortak hesabı
          kullanan herkes program dosyalarını değiştirip başkalarının parolasını toplayabilir.
        </li>
      </ul>
      <Ipucu>
        Bu öneri Bilgi ve Sistem Güvenliği Yönergesini tam karşılamaz. Yönergenin md. 7/2, 7/4 ve
        9/2-e hükümleri herkesin kendi hesabıyla oturum açmasını ve parolasını paylaşmamasını
        öngörür (7. madde Bakanlığın ağ hesapları içindir, burada kıyasen anılır). Ortak hesabın
        parolasını kurul üyeleri bilir. Programdaki kişisel hesaplar “kim yaptı” sorusunu cevaplar,
        ama Windows oturumundaki bu sapmayı gidermez.
      </Ipucu>

      <AltBaslik>Programın dürüst sınırları</AltBaslik>
      <ul className="list-disc space-y-2 pl-5">
        {DURUST_SINIRLAR.map((sinir) => (
          <li key={sinir.baslik}>
            <strong className="text-on-surface">{sinir.baslik}</strong>{" "}
            {sinir.metin.replace(SINIR_SATIRI, SINIR_SATIRI_KILAVUZDA)}
          </li>
        ))}
      </ul>
      <p>
        Aynı maddeler <Ekran to="/hakkinda">Hakkında ve Lisans</Ekran> ekranındaki Dürüst Sınırlar
        kartında da yazılıdır; programın kullandığı yöntemler aynı ekrandaki Teknik Bilgiler
        kartındadır.
      </p>
      <p>
        Açıkça söyleyelim: bir hesabın parolasını bilen ve veri klasörünü kopyalayabilen biri, rolü
        ne olursa olsun kayıtların tamamını programın dışında okuyabilir. Bu yüzden disk şifrelemesi
        ve ayrı Windows hesabı önerilir.
      </p>

      <AltBaslik>Bilgisayar, disk ya da USB bellek kaybolursa ya da çalınırsa</AltBaslik>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          Durumu hemen okul müdürlüğüne iletin. İşlenen kişisel veriler kanuni olmayan yollarla
          başkalarınca elde edilirse veri sorumlusu bunu en kısa sürede ilgilisine ve Kişisel
          Verileri Koruma Kuruluna bildirir (KVKK md. 12/5). Program bu bildirimi yapmaz.
        </li>
        <li>
          Neyin ve ne zaman kaybolduğunu yazın: bilgisayar mı, disk mi, USB bellek mi; disk şifreli
          miydi; bellekte hangi tarihli yedek vardı.
        </li>
        <li>
          Hangi verilerin etkilendiğini değerlendirmek için bu bölümdeki “Program neyi şifreler”
          başlığına bakın. Şifrelenen alanlar da en zayıf hesap parolası kadar korunur.
        </li>
        <li>Kurtarma anahtarı zarfının yerinde ve kapalı olduğunu denetleyin.</li>
        <li>
          Bilgisayar kaybolduysa kayıtları son şifreli yedekten yeni bilgisayara taşıyın (
          <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedek ve Geri Yükleme</Ekran>). O yedekten
          sonra girilen kayıtlar yoktur.
        </li>
        <li>
          Bilgisayar duruyor ama bir parola başkasına geçmiş olabilirse o parolayı değiştirin ya da
          program yöneticisine sıfırlatın. Dürüst sınırlardaki parola maddesini de okuyun.
        </li>
        <li>
          Kurtarma anahtarı kâğıdı başkasının eline geçtiyse yenileme tek başına yetmez: kayıtların
          anahtarı değişmez, eski yedekler eski anahtarla açılabilir. Durumu okul müdürlüğüne
          bildirin.
        </li>
      </ol>

      <AltBaslik>{ERISIM_GUNLUGU_BASLIGI}&apos;nü okumak için</AltBaslik>
      {yetki.acik("erisim_gunlugu") ? (
        <p>
          <Ekran to="/erisim-gunlugu">{ERISIM_GUNLUGU_BASLIGI}</Ekran> ekranını açın. Tarih aralığı,
          “Tür” ve “Hesap” süzgeçleriyle arayabilirsiniz; “Süzgeçleri temizle” listeyi geri getirir.
        </p>
      ) : (
        <p>
          {ERISIM_GUNLUGU_BASLIGI} bu hesaba açık değildir; bir kaydı öğrenmeniz gerekirse program
          yöneticisine başvurun.
        </p>
      )}
      <p>
        Günlük, kişisel veriye dokunan hassas okumaları ve kişisel veri içeren çıktıları gösterir:
        hangi hesapla, ne zaman ve hangi kayıt okundu. Okunan değer günlükte yoktur; günlüğü okumak
        iz bırakmaz. Kayıtlar iki yıl saklanır, sonra silinir. Programın bugünkü ekranlarında
        günlüğe yazan bir okuma olmadığı için liste boştur.
      </p>

      <AltBaslik>Programı kullananların verileri</AltBaslik>
      <p>
        Bu kılavuz ve ilk kurulum ekranı yalnız programı kullananları bilgilendirir. Hesap açılan
        kişinin adı-soyadı, rolü, hesap olayları ve kişisel veri okumaları; hesap, denetim izi ve
        erişim günlüğü için tutulur, dışarıya aktarılmaz. Personel ve veliler için aydınlatma ayrı
        bir iştir (KVKK md. 10/1); metni aktarım ekranlarındadır (
        <Ekran to="/kilavuz#kisiler">Kişiler</Ekran>,{" "}
        <Ekran to="/kilavuz#veli-listesi">Veli Listesi</Ekran>).
      </p>

      <AltBaslik>Okul müdürlüğünün değerlendireceği sorular</AltBaslik>
      <p>Aşağıdaki soruların cevabını program da bu kılavuz da vermez.</p>
      <ul className="list-disc space-y-2 pl-5">
        <li>
          <strong className="text-on-surface">Veri sorumlusu kim?</strong> Birlik, okul bünyesinde
          kurulan ve tüzel kişiliği olmayan bir yapıdır (Yönetmelik md. 5/1). Veri sorumlusunun
          birlik mi okul ya da Bakanlık mı olduğunu belirleyen bir Kişisel Verileri Koruma Kurulu
          kararı bulunamadı. Okul müdürlüğünün belirlediği bilgi{" "}
          <Ekran to="/ayarlar?tab=okul">Ayarlar → Okul Bilgileri</Ekran> sekmesindeki Veri sorumlusu
          alanına yazılır.
        </li>
        <li>
          <strong className="text-on-surface">
            Veri Sorumluları Siciline (VERBİS) kayıt gerekir mi?
          </strong>{" "}
          Sicile kayıt zorunluluğu ve Kurulun belirleyeceği istisna KVKK md. 16/2&apos;dedir. Birlik
          kayıtlarının programa girilmesi, kâğıt kayda dayanan bir istisnanın okul için
          geçerliliğini değiştirebilir. İstisnayı getiren Kurul kararları programın mevzuat
          derlemesinde bulunmadığı için bu kılavuz hüküm vermez.
        </li>
        <li>
          <strong className="text-on-surface">Hukuki sebep doğru mu?</strong> Aydınlatma metnindeki
          hukuki sebep öneridir; veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir.
        </li>
        <li>
          <strong className="text-on-surface">Birlik “3. şahıs” sayılır mı?</strong> Yönerge,
          yetkili kullanıcının öğretmen, öğrenci ve velilerin kişisel bilgilerini üçüncü kişilerle
          paylaşmasını yasaklar (Yönerge md. 5/8, 6/7). Birliğin bu hükümler karşısındaki yeri veri
          sorumlusu sorusuna bağlıdır. Program bu yüzden veli listesinde yalnız veli adını ve
          öğrencinin sınıfını tutar (<Ekran to="/kilavuz#veli-listesi">Veli Listesi</Ekran>).
        </li>
      </ul>
    </KilavuzBolumu>
  );
}
