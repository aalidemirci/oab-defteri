import Card from "../../ui/Card";
import Icon from "../../ui/Icon";

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
                §15 KE-20). Aydınlatma metni E04'tür (F2). */}
            <p className="mt-2 text-body-small text-on-surface-variant">
              İletinize öğrenci, veli ya da personel bilgisi, gerçek veri içeren ekran görüntüsü,
              yedek ya da veritabanı dosyası eklemeyin. Programdaki kişisel verilere ilişkin
              başvurular okul müdürlüğüne yapılır.
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
                Öğrenci, öğretmen ve diğer personelin ad-soyadları ile öğrencilerin okul numaraları
                Fernet (AES-128-CBC + HMAC-SHA256) ile şifrelenir; şifreleme anahtarı, yönetici
                parolasından Argon2id ile türetilen anahtarla korunur. Okul numarasıyla arama ve
                e-Okul eşleştirmesi, aynı anahtardan türetilen HMAC-SHA256 kör indeksle numaranın
                tamamı üzerinden yapılır.
              </li>
              <li>
                Şifreli yedekler (<span className="font-mono">.odbak</span>) X25519 ve AES-256-GCM
                ile şifrelenir; yedek, yönetici parolası ya da kurtarma anahtarıyla açılır.
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
