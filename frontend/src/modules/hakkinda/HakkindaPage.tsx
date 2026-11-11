import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { DURUST_SINIRLAR } from "../guvenlik/metinler";

export default function HakkindaPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <header>
        <p className="text-label-medium font-semibold tracking-wide text-primary">OAB Defteri</p>
        <h1 className="mt-1 text-headline-medium font-semibold tracking-tight text-on-surface">
          Hakkında ve Lisans
        </h1>
        <p className="mt-2 text-body-medium text-on-surface-variant">
          Programın konumu, geliştiricisi, iletişim bilgileri ve kullanım koşulları.
        </p>
      </header>

      {/* Tanım ve konum notu CLAUDE.md §1'e ve tasarım §3.1'e bağlıdır; Kullanım
          Kılavuzu'ndaki "Programın Konumu" ile aynı dildedir (docs/sozluk.md §1). Program
          karar defterinin ve TEFBİS'in yerine geçmez, bunlara girilecek metni ve listeyi
          hazırlar; kendine "otomasyon sistemi" adını vermez. Simge logonun motifidir
          (okul çatısı altında aile: iki yetişkin ve bir çocuk). */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-primary-container text-on-primary-container">
            <Icon name="family_restroom" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">Program</h2>
            <p className="mt-2 text-body-medium text-on-surface-variant">
              OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten çevrimdışı
              bir masaüstü programıdır.
            </p>
            <p className="mt-3 rounded-shape-md bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
              Program karar defterinin ve TEFBİS&apos;in yerine geçmez. Karar defterine kararlar el
              ile yazılır ve defter noter tasdiklidir; birliğin gelir-gider kayıtlarını
              TEFBİS&apos;e okul idaresi girer. Program bunlara girilecek metni ve listeyi hazırlar,
              tutarlılığı denetler.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-primary-container text-on-primary-container">
            <Icon name="person" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">Geliştirici</h2>
            <p className="mt-2 text-body-large text-on-surface">Ahmet Ali DEMİRCİ</p>
            <a
              href="mailto:aalidemirci@gmail.com"
              className="mt-1 inline-flex items-center gap-1.5 text-body-medium font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <Icon name="mail" size="base" />
              aalidemirci@gmail.com
            </a>
            <p className="mt-3 text-body-medium text-on-surface-variant">
              Programla ilgili talep, öneri, hata bildirimi ve şikâyetlerinizi bu e-posta adresine
              iletebilirsiniz.
            </p>
            {/* KVKK (CLAUDE.md §2 altın kural 5, SECURITY.md): kişi verisi destek iletisine
                girmez. Okulun kayıtlarına ilişkin başvuru okul müdürlüğüne yönelir; veri
                sorumlusunun kim olduğu okul müdürlüğünün değerlendirmesidir (tasarım §3.4,
                §15 KE-20); bilgisi okul kartındadır (`data_controller_text`). Aydınlatma
                metinleri personel ve veli listesi aktarım ekranlarındadır (F1b 5. adım),
                belgesi E04 F2'de gelir. */}
            <p className="mt-2 text-body-small text-on-surface-variant">
              İletinize öğrenci, veli ya da personel bilgisi, gerçek veri içeren ekran görüntüsü,
              yedek ya da veritabanı dosyası eklemeyin. Programdaki kişisel verilere ilişkin
              başvurular okul müdürlüğüne yapılır; veri sorumlusu bilgisi Ayarlar → Okul
              Bilgileri'nde, aydınlatma metinleri personel ve veli listesi aktarım ekranlarındadır.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-secondary-container text-on-secondary-container">
            <Icon name="license" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">
              Ücretsiz ve Ticari Olmayan Kullanım
            </h2>
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Bu sürüm <strong>PolyForm Noncommercial License 1.0.0</strong> ile sunulur. Eğitim
              kurumları, kamu kurumları, kâr amacı gütmeyen kuruluşlar ve bireyler programı ticari
              olmayan amaçlarla ücretsiz kullanabilir.
            </p>
            <div className="mt-4 rounded-shape-md bg-tertiary-container px-4 py-3 text-body-medium text-on-tertiary-container">
              Program ücretle dağıtılamaz; ücretli teknik destek paketinin, ticari ürünün,
              barındırılan veya yönetilen bir hizmetin parçası olarak sunulamaz. Böyle bir kullanım
              için geliştiriciden ayrıca yazılı ticari lisans alınmalıdır.
            </div>
            <p className="mt-4 text-body-small text-on-surface-variant">
              Gelecekte yayımlanacak sürümlerin lisans veya fiyatlandırma koşulları değişebilir.
              Ücretsiz yayımlanmış bir sürüm ise kendi lisans koşullarıyla ücretsiz ve ticari
              olmayan kullanıma açık kalır. Tam ve bağlayıcı koşullar programla birlikte gelen
              LICENSE dosyasındadır.
            </p>
            <a
              href="https://polyformproject.org/licenses/noncommercial/1.0.0"
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 text-label-large font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              Lisansın resmî metni
              <Icon name="open_in_new" size="sm" />
            </a>
          </div>
        </div>
      </Card>

      {/* LGPL-3.0 §4(c): çalışırken telif bildirimi gösteren program, LGPL kitaplığın
          telif bildirimini de gösterir ve GPL/LGPL metinlerine yönlendirir (lisans kümesi:
          tasarım §11.4). Dosya adları paketin gerçek yerleşimidir (THIRD_PARTY_LICENSES). */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-surface-container-high text-on-surface-variant">
            <Icon name="deployed_code" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">
              Üçüncü Taraf Bileşenler
            </h2>
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Program açık kaynaklı üçüncü taraf bileşenlerle birlikte dağıtılır; her bileşen kendi
              lisansıyla kullanılır. Aşağıdaki kitaplıklar GNU Kısıtlı Genel Kamu Lisansı (LGPL-3.0)
              ile kullanılır:
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-body-medium text-on-surface-variant">
              <li>
                Pardus&apos;ta pencere: Qt 6 ve PySide6 — Copyright © The Qt Company Ltd. ve katkıda
                bulunanlar.
              </li>
            </ul>
            <p className="mt-3 text-body-small text-on-surface-variant">
              Bütün bileşenlerin adları, sürümleri, telif bildirimleri, lisans metinleri ve LGPL
              kitaplıkların kaynak koduna erişim bilgisi, programın kurulduğu klasördeki{" "}
              <span className="font-mono">THIRD_PARTY_LICENSES</span> klasöründedir:{" "}
              <span className="font-mono">BENIOKU.txt</span> (dizin),{" "}
              <span className="font-mono">LGPL-3.0-metni.txt</span> ve{" "}
              <span className="font-mono">GPL-3.0-metni.txt</span>.
            </p>
          </div>
        </div>
      </Card>

      {/* Dürüst sınırlar (tasarım §4.4.6; kılavuza da girer): programın korumasının
          nerede bittiği sade dille, iç kod olmadan. Metinler güvenlik metinlerinin tek
          kaynağındadır (`guvenlik/metinler.DURUST_SINIRLAR`); yalnız bugün doğru olan
          söylenir. KVKK md. 12/5 atfı kanonik metindedir (docs/mevzuat/6698-kvkk.md). */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-tertiary-container text-on-tertiary-container">
            <Icon name="policy" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">Dürüst Sınırlar</h2>
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Program kişisel verileri korumak için önlem alır; ama her önlemin bir sınırı vardır.
              Bilmeniz gerekenler:
            </p>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-body-medium text-on-surface-variant">
              {DURUST_SINIRLAR.map(({ baslik, metin }) => (
                <li key={baslik}>
                  <strong className="font-semibold text-on-surface">{baslik}</strong> {metin}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Şifreleme yöntemlerinin ADI yalnız burada geçer (docs/sozluk.md §1):
          ayar ekranları "güçlü şifrelemeyle korunur" der, merak eden ya da
          bilişim sorumlusuna bilgi verecek olan ayrıntıyı bu kartta bulur. */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-shape-md bg-surface-container-high text-on-surface-variant">
            <Icon name="shield_lock" size="xl" />
          </span>
          <div>
            <h2 className="text-title-large font-semibold text-on-surface">Teknik Bilgiler</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-body-medium text-on-surface-variant">
              <li>
                Program çevrimdışı çalışır; veriler yalnız bu bilgisayarda tutulur. Program ağ
                servisi sunmaz: yönetim sunucusu yalnız 127.0.0.1&apos;de, rastgele portta ve oturum
                belirteciyle dinler; hiçbir port okul ağına açılmaz. Dış istek yalnız kullanıcının
                başlattığı güncelleme denetiminden çıkar: Ayarlar → Güncelleme&apos;de “Şimdi
                denetle” düğmesine bastığınızda yayımlanan son sürümü GitHub&apos;dan soran anonim
                denetim. Program açılışta internete çıkmaz; hiçbir durumda kişisel veri dışarı
                çıkmaz.
              </li>
              <li>
                Öğretmen ve diğer personelin ad-soyadları, velilerin ad-soyadları, birlik
                kişilerinin ad-soyadları, hesap sahiplerinin ad-soyadları ve eklerin özgün dosya
                adları Fernet (AES-128-CBC + HMAC-SHA256) ile şifrelenir. Velinin ve birlik
                kişisinin adı için ayrıca, kayıtların anahtarından HKDF ile türetilen ayrı bir
                anahtarla HMAC-SHA256 kör indeksi tutulur; ad şifreli kaldığından indeks yalnız aynı
                adın bulunması için kullanılır: veli listesinden birlik kişisi eklenirken yazılan
                adın satırını ve yeni birlik kişisinde “olası aynı kişi”yi bulur. Veli listesindeki
                öğrencinin sınıfı şifrelenmez. Şifreleme anahtarı her hesap için ayrı şifrelenir ve
                güvenlik dosyasında o hesabın parola kaydında durur: hesabın parolasından Argon2id
                ile türetilen anahtar onu tek başına açar; kurtarma anahtarının da kendi kaydı
                vardır.
              </li>
              <li>
                Denetim izinin her kaydı, bir önceki kaydın mührüyle birlikte HMAC-SHA256 ile
                mühürlenir (zincir); kaydın içeriğinin özeti de aynı anahtardan türeyen ayrı bir
                HMAC-SHA256 ile satıra yazılır. Mühür anahtarı kayıtların anahtarıyla şifreli olarak
                veritabanında durur. Program kilitliyken yazılan sistem olayları (yedek, güncelleme)
                her adımda ileri giden ayrı bir anahtarla mühürlenir. Kâğıda not edilen “Zincir” son
                kaydın mührünün ilk sekiz onaltılık hanesidir.
              </li>
              <li>
                Ekler ve üretilen evrak veri klasöründe, her dosya kendi rastgele anahtarıyla
                AES-256-GCM ile şifreli durur. Dosyanın anahtarı, kayıtların anahtarından HKDF ile
                türetilen ayrı bir anahtarla AES-256-GCM ile şifrelenip ekin kaydında saklanır.
              </li>
              <li>
                Şifreli yedekler (<span className="font-mono">.odbak</span>) X25519 ve AES-256-GCM
                ile şifrelenir. Yedeğin başlığı yalnız kurtarma anahtarının kaydını ve no&apos;sunu
                taşır, hesapların parola kayıtlarını taşımaz: yedek bu bilgisayarda program
                yöneticisinin parolasıyla, başka bir bilgisayarda yalnız kurtarma anahtarıyla
                açılır.
              </li>
              <li>
                Bu bilgisayardaki yedekler veritabanını ve eklerin listesini (rastgele üretilmiş ad,
                boy, SHA-256 özeti) taşır, dosyaların kendisini taşımaz. Kaydedilen şifreli yedekte
                bunların ardına dosya bölümü gelir: ekler zaten şifreli olduğu için ikinci kez
                şifrelenmeden sırayla yazılır, anahtarları yedeğin şifreli bölümündeki
                veritabanındadır. Liste şifreli bölümdedir; geri yükleme her dosyayı onunla
                denetler.
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
