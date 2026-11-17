// Kılavuz bölümü: Genel Kurul (çapa `genel-kurul`). Başlık, ikon ve sıra `KilavuzPage`'dedir. Ekran,
// adım, düğme ve pencere adları `genel-kurul/metinler`'den; belge adları `evrak/metinler`'den (kartlar
// katalogdan çizilir, adlar backend `genel_kurul_evraki.BELGE_ADLARI` ile birebir); pano kalemlerinin
// başlıkları `pano/metinler`'den. Kaynaklar: sözlük §1 "Genel Kurul ekranı (F2)", "Genel kurul evrakı
// (F2)"; tasarım §7.1 ("Kim" sütunu), §9.5-9.6; plan F2 §6.1, §7 (U1, U15, U23, U32, U33). Yazma adımları
// ekranın yetenekleriyle anlatılır: planlama ve tutanak `genel_kurul_yazma`, katılım işaretleri ve veli
// adlı çıktı `kisisel_veri_ciktisi`, yeni birlik döneminin açılışı `donem_gecisi_onayi`, iptal
// `genel_kurul_iptal`, giden evrak kaydı `evrak_kaydi`. Olağanüstü genel kurulda ikinci toplantı süresinin
// kaynağını söyleyen pano cümlesi kılavuza alınmaz (iç karar kodu taşır). Alıntılar
// `docs/mevzuat/meb-okul-aile-birligi-yonetmeligi.md` ile birebirdir (md. 9/1, 9/2, 9/3, 11/1-ç).

import {
  DUGME_EXCEL,
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  E05_ADI,
  E06_ADI,
  E07_ADI,
  E08_ADI,
  E09_ADI,
  E10_ADI,
  E11_ADI,
  E12_ADI,
  E13_ADI,
  E64_ADI,
  URETIM_UYARILARI_BASLIGI,
} from "../../evrak/metinler";
import {
  ADAY_ACIKLAMASI,
  ADIM_CAGRI,
  ADIM_ILAN,
  ADIM_PLANLA,
  ADIM_SONRASI,
  ADIM_TOPLANTI,
  ADIM_TUTANAK,
  ADLI_CIKTI_ACIKLAMASI,
  ADLI_CIKTI_BASLIGI,
  ALAN_BIRINCI_TOPLANTI,
  ALAN_ELDEN_YAZILI,
  ALAN_GENEL_KURUL_TURU,
  ALAN_GOZLEMCI,
  ALAN_ILAN_PANOSU,
  ALAN_INTERNET,
  ALAN_KATILAN,
  ALAN_KIP,
  ALAN_OGRENCI_MEVCUDU,
  ALAN_TESLIM_GUNU,
  ALAN_VELISI_KATILAN,
  ALAN_YER,
  ALAN_YETER_SAYI,
  BELGELER_ACIKLAMASI,
  BELGELER_BASLIGI,
  CAGIRAN_TR,
  CAGRI_OLAGANUSTU_ACIKLAMASI,
  CAGRI_OLAGAN_ACIKLAMASI,
  CAGRI_YAZISI_ACIKLAMASI,
  DAGILIM_BASLIGI,
  DIVAN_ACIKLAMASI,
  DIVAN_IPTAL_METNI,
  DONEM_GECISI_ACIKLAMASI,
  DONEM_GECISI_BASLIGI,
  DONEM_GECISI_ONAY_METNI,
  DOSYA_EKLERI_ACIKLAMASI,
  DOSYA_EKLERI_BASLIGI,
  DUGME_ADAY,
  DUGME_ADLI_EXCEL,
  DUGME_ADLI_PDF,
  DUGME_ADLI_WORD,
  DUGME_BIRINCI_TOPLANTI,
  DUGME_CAGRI,
  DUGME_CAGRI_YAZISI,
  DUGME_DIVAN,
  DUGME_DIVAN_IPTAL,
  DUGME_DONEM_GECISI,
  DUGME_EVRAK_KAYDI,
  DUGME_GUNDEMDEN_CIKAR,
  DUGME_GUNDEM_EKLE,
  DUGME_GUNDEM_SIRASI,
  DUGME_IBRA,
  DUGME_IKINCI_ILAN,
  DUGME_IKINCI_TOPLANTI,
  DUGME_ILAN,
  DUGME_IPTAL,
  DUGME_KANIT,
  DUGME_KATILIM_DUZELTMESI,
  DUGME_KATILIM_ISARETLERI,
  DUGME_PLANLA,
  DUGME_SECIM,
  DUGME_SECIM_IPTAL,
  DUGME_SONUC,
  DUGME_TOPLANTI_BILGISI,
  DUGME_TUTANAK_BILGILERI,
  DUGME_TUTANAK_TAMAMLA,
  DUGME_WEB,
  DURUM_TR,
  EVRAK_KAYDI_ACIKLAMASI,
  GENEL_KURUL_BASLIGI,
  GOREV_BOLUMU_ACIKLAMASI,
  GUNDEMDEN_CIKAR_ACIKLAMASI,
  GUNDEM_EKLE_ACIKLAMASI,
  IBRA_ACIKLAMASI,
  IBRA_EDILMEYEN_EVRAK_YARDIMI,
  IKINCI_ILAN_ACIKLAMASI,
  IKINCI_TOPLANTI_YARDIMI,
  ILAN_ACIKLAMASI,
  IPTAL_METNI,
  KANAL_YARDIMI,
  KANIT_EKI_YARDIMI,
  KATILIM_DUZELTMESI_ACIKLAMASI,
  KATILIM_ISARETLERI_ACIKLAMASI,
  KIP_ADLI,
  KIP_KISISIZ,
  KURAL_SURUMU_AC,
  KURAL_SURUMU_GUNCELLENMELI,
  KURAL_SURUMU_GUNCELLENMELI_BASVURUN,
  LISTE_BASLIGI,
  MUHATAP_YARDIMI,
  OLAGANUSTU_DONEM_ACMAZ,
  PLANLAMA_BILGILERI_BASLIGI,
  PLANLA_ACIKLAMASI,
  SECIM_ACIKLAMASI,
  SECIM_IPTAL_METNI,
  SONUC_ACIKLAMASI,
  TEFBIS_ACIKLAMASI,
  TESLIM_GUNU_YARDIMI,
  TOPLANTI_ACIKLAMASI,
  TOPLANTI_BILGISI_ACIKLAMASI,
  TUTANAK_TAMAMLA_METNI,
  TUTANAK_TAMAM_NOTU,
  UYE_SAYISI_YARDIMI,
  YETER_SAYI_YOK_NOTU,
} from "../../genel-kurul/metinler";
import { SEKME_DK, SEKME_YK } from "../../organlar/metinler";
import { useYetki } from "../../oturum/yetki";
import {
  DONEM_ONAYI_BASLIGI,
  GK_IKINCI_TOPLANTI_BASLIGI,
  GK_ILAN_BASLIGI,
  GK_OLAGAN_BASLIGI,
  GK_YENI_OKUL_BASLIGI,
  IBRA_BILDIRIMI_BASLIGI,
  MUDUR_YAZISI_BASLIGI,
  TEFBIS_BASLIKLARI,
} from "../../pano/metinler";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Mevzuat } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Sihirbazın adımları, ekrandaki sırayla. */
const GENEL_KURUL_ADIMLARI = [
  ADIM_PLANLA,
  ADIM_CAGRI,
  ADIM_ILAN,
  ADIM_TOPLANTI,
  ADIM_TUTANAK,
  ADIM_SONRASI,
] as const;

/** Durum adları, genel kurulun ilerleyişiyle. */
const DURUMLAR = Object.values(DURUM_TR).join(" · ");

/** Çağıranların ekrandaki adları (yönetim kurulu dışındakiler madde atfıyla). */
const CAGIRANLAR = Object.values(CAGIRAN_TR);

/** TEFBİS takvim satırlarının başlıkları. */
const TEFBIS_SATIRLARI = Object.values(TEFBIS_BASLIKLARI).join(" · ");

/** Kartı olan belgeler, sihirbazın sırasıyla. */
const BELGELER: ReadonlyArray<readonly [ad: string, ne: string]> = [
  [E05_ADI, "çağrı kaydedildikten sonra, toplantı başına"],
  [E06_ADI, "toplantı başına; ilan panosu ve internet sayfası için"],
  [E07_ADI, "ilanla birlikte; davetin sınıf sınıf teslimi için"],
  [E08_ADI, "toplantıda imzalanacak cetvel"],
  [E09_ADI, "adaylar girildikten sonra"],
  [E64_ADI, "toplantı başına; toplantıda yeter sayının tespiti"],
  [E10_ADI, "divan, gündem sonuçları, ibra ve seçimle"],
  [E11_ADI, "hesaplar ibra edilmediğinde"],
  [E12_ADI, "hesaplar ibra edilmediğinde; program yöneticisi oluşturur"],
  [E13_ADI, "tutanak tamamlandıktan sonra"],
];

export default function GenelKurul(bolum: BolumProps) {
  const yetki = useYetki();
  const yaz = yetki.acik("genel_kurul_yazma");
  const kisisel = yetki.acik("kisisel_veri_ciktisi");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/genel-kurul">{GENEL_KURUL_BASLIGI}</Ekran> ekranı okul-aile birliğinin olağan ve
        olağanüstü genel kurullarını planlamadan tutanağa ve genel kuruldan sonraki işlere kadar
        adım adım kaydeder. Ekranı her hesap okur. Kayıt silinmez; yanlış kayıt gerekçeyle
        düzeltilir. Program <strong>karar defterinin ve TEFBİS&apos;in yerine geçmez</strong>:
        programın hazırladığı tutanak ve yazılar imzalanıp birliğin dosyasına konur, TEFBİS&apos;e
        girişi okul idaresi yapar (md. 23/5).
      </p>
      <p>
        <strong>{LISTE_BASLIGI}</strong> listesinde en yeni genel kurul üsttedir; satıra basınca
        genel kurulun ayrıntısı açılır. Ayrıntının üstündeki adımlar şunlardır:{" "}
        {GENEL_KURUL_ADIMLARI.join(" → ")}. Program genel kurulun durumuna göre sıradaki adımı açar;
        tamamlanmış bir adıma basınca o adımın kayıtları görünür. Durumlar: {DURUMLAR}. İptal
        edilmiş genel kurulun kayıtları salt okunurdur. Tutanak tamamlandıktan sonra ayrıntıda şu
        yazar: “{TUTANAK_TAMAM_NOTU}” Belgeler yeni sürümle yeniden oluşturulabilir; yeni birlik
        döneminin açılışı ve {ADIM_SONRASI} adımının işleri tutanaktan sonra yapılır.
      </p>
      {!yaz && (
        <p>
          Genel kurulun kayıtlarını program yöneticisi ve sekreter girer; hesabınız bu kayıtları
          okur. Bir kayıtta yanlış görürseniz program yöneticisine başvurun.
        </p>
      )}

      <AltBaslik>Genel kurul ne zaman toplanır</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 9/1">
        Genel kurul, birliğin üyelerinden meydana gelir. Genel kurul, birlik yönetim kurulunun
        davetiyle her yıl en geç Ekim ayının sonuna kadar; yeni açılan okullarda ise okul müdürünün
        daveti üzerine okulun açıldığı tarihten itibaren en geç iki ay içinde okulda toplanır.
      </Mevzuat>
      <p>
        Olağan genel kurul planlanmadıysa ya da birinci toplantının günü son günü aşıyorsa Genel
        Bakış&apos;ta <strong>{GK_OLAGAN_BASLIGI}</strong> işi çıkar. Okul Bilgileri&apos;nde okulun
        açılış tarihi girilmiş ve okulda henüz birlik dönemi açılmamışsa (iptal edilen birlik dönemi
        sayılmaz) okul yeni açılmış sayılır: iş <strong>{GK_YENI_OKUL_BASLIGI}</strong> adıyla gelir
        ve son gün açılış tarihinden sayılır. Birlik dönemi açıldıktan sonra açılış tarihi dolu
        kalsa da iş <strong>{GK_OLAGAN_BASLIGI}</strong> adıyla gelir ve son gün Ekim ayının
        sonudur. Genel kurul planlanmadıysa işin son günü, toplantının son gününden ilan süresi
        kadar öncesidir. Okul müdürü genel kurulun zamanında ve Yönetmeliğe uygun yapılmasını sağlar
        (md. 27/1).
      </p>

      <AltBaslik>1. {ADIM_PLANLA}</AltBaslik>
      {yaz ? (
        <>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              Ekranın başındaki “{DUGME_PLANLA}” düğmesine basın. Liste boşsa ekran da genel kurulu
              planlayarak başlamayı önerir.
            </li>
            <li>
              <strong>{ALAN_GENEL_KURUL_TURU}</strong>, <strong>{ALAN_BIRINCI_TOPLANTI}</strong> ve{" "}
              <strong>{ALAN_YER}</strong> alanlarını doldurup kaydedin. {PLANLA_ACIKLAMASI}
            </li>
            <li>
              Ekrandaki <strong>{PLANLAMA_BILGILERI_BASLIGI}</strong> satırları planlamaya giren
              bilgileri (öğrenci mevcudu ve tarihi, veli listesi) hatırlatır.
            </li>
          </ol>
          <p>
            {TOPLANTI_BILGISI_ACIKLAMASI} Bunun için {ADIM_PLANLA} adımında “
            {DUGME_TOPLANTI_BILGISI}” ve “{DUGME_GUNDEM_SIRASI}” düğmeleri vardır. Genel kurul
            gündem maddelerini sırasıyla görüşür (md. 9/4).
          </p>
          <p>
            Açık birlik döneminin kural sürümü genel kurulun kurallarını taşımıyorsa planlama
            düğmesi görünmez ve şu bant çıkar:{" "}
            {yetki.acik("kural_surumu_guncelleme") ? (
              <>
                “{KURAL_SURUMU_GUNCELLENMELI}” Bandın “{KURAL_SURUMU_AC}” bağlantısıyla Birlik
                Dönemi&apos;ne gidip kural sürümünü güncelleyin (
                <Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>).
              </>
            ) : (
              <>“{KURAL_SURUMU_GUNCELLENMELI_BASVURUN}”</>
            )}
          </p>
        </>
      ) : (
        <p>
          Genel kurulu program yöneticisi ya da sekreter planlar. Olağan genel kurul planlanınca
          yeni birlik dönemi hazırlık durumunda açılır ve gündem Yönetmeliğin saydığı maddelerle
          hazırlanır.
        </p>
      )}

      <AltBaslik>2. {ADIM_CAGRI}</AltBaslik>
      <p>
        {CAGRI_OLAGAN_ACIKLAMASI} {CAGRI_OLAGANUSTU_ACIKLAMASI} Ekranda çağıranın adı yazar; yönetim
        kurulu dışındaki çağıranlarda dayanak madde de yazar:
      </p>
      <ul className="list-disc space-y-1 pl-5">
        {CAGIRANLAR.map((ad) => (
          <li key={ad}>{ad}</li>
        ))}
      </ul>
      <p>
        Çağrıyı çağıranın hesabı “{DUGME_CAGRI}” düğmesiyle kaydeder: yönetim kurulunun çağrısını
        sekreter, birlik başkanının çağrısını (md. 13/8) başkan, üyelerin yazılı başvurusunu program
        yöneticisi girer. Okul müdürü yeni açılan okulda daveti ve kendi çağrısını kendi hesabından
        yazar; bu yazı beklerken müdürün Genel Bakış&apos;ında{" "}
        <strong>{MUDUR_YAZISI_BASLIGI}</strong> işi çıkar. Denetleme Kurulunun çağrısı Organlar
        ekranından yazılır (<Ekran to="/kilavuz#organlar">Organlar</Ekran>). Çağrı seçeneği olmayan
        hesapta düğme görünmez.
      </p>
      <p>
        Üyelerin başvurusunda {UYE_SAYISI_YARDIMI} {CAGRI_YAZISI_ACIKLAMASI} Bağlamayı program
        yöneticisi “{DUGME_CAGRI_YAZISI}” düğmesiyle yapar (
        <Ekran to="/kilavuz#gelen-giden-evrak">Gelen-Giden Evrak</Ekran>).
      </p>

      <AltBaslik>3. {ADIM_ILAN}</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 9/3">
        Genel kurul toplantılarının yeri, zamanı ve gündemi en az onbeş gün önceden üyelere elden
        yazılı olarak bildirilir, okul ilan panosu ile okulun internet sayfasında duyurulur.
      </Mevzuat>
      <p>{ILAN_ACIKLAMASI}</p>
      {yaz && (
        <p>
          İlan “{DUGME_ILAN}” düğmesiyle kaydedilir. Pencerede üç kanalın günü girilir:{" "}
          <strong>{ALAN_ELDEN_YAZILI}</strong>, <strong>{ALAN_ILAN_PANOSU}</strong> ve{" "}
          <strong>{ALAN_INTERNET}</strong>. {KANAL_YARDIMI} {IKINCI_TOPLANTI_YARDIMI} Sonradan
          yapılan kanalın günü “{DUGME_KANIT}” düğmesiyle girilir. İlanın kartına kanıt dosyası
          eklenir: {KANIT_EKI_YARDIMI}
        </p>
      )}
      <p>
        İlandan sonra ayrıntıda <strong>{ALAN_YETER_SAYI}</strong> ve hesabın dayandığı{" "}
        <strong>{ALAN_OGRENCI_MEVCUDU}</strong> yazar. İlan yapılmadıysa ya da bir kanalın günü
        girilmediyse Genel Bakış&apos;ta <strong>{GK_ILAN_BASLIGI}</strong> işi çıkar.
      </p>

      <AltBaslik>4. {ADIM_TOPLANTI}</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 9/2">
        Genel kurul, katılan üyelerle toplanır ve bunların çoğunluğu ile karar alır. Ancak toplantı
        yeter sayısı, yönetim ve denetleme kurullarının asıl ve yedek üye sayısının dört katından,
        öğrenci mevcudu yüzün altında olan okullarda ise yönetim ve denetleme kurullarının asıl ve
        yedek üye sayısının iki katından az olamaz. Genel kurulun toplanamaması durumunda, en geç
        otuz gün içinde çoğunluk aranmaksızın toplantı yapılır ve kararlar katılanların çoğunluğu
        ile alınır.
      </Mevzuat>
      <p>
        Genel kurula katılan üyeler katılım cetvelini imzalar (md. 10/1-a); toplantıyı okul müdürü
        açar (md. 10/1-b). Okul müdürü yönetim kurulu üyesi değildir, toplantıyı divan yönetir.{" "}
        {TOPLANTI_ACIKLAMASI}
      </p>
      {yaz && (
        <p>
          Toplantıdan sonra “{DUGME_BIRINCI_TOPLANTI}” düğmesiyle <strong>{ALAN_KATILAN}</strong>,{" "}
          <strong>{ALAN_VELISI_KATILAN}</strong>, <strong>{ALAN_GOZLEMCI}</strong> ve{" "}
          <strong>{DAGILIM_BASLIGI}</strong> girilir. Yanlış girilen sayı “
          {DUGME_KATILIM_DUZELTMESI}” düğmesiyle düzeltilir. {KATILIM_DUZELTMESI_ACIKLAMASI}
        </p>
      )}
      <p>
        {YETER_SAYI_YOK_NOTU} {IKINCI_ILAN_ACIKLAMASI} Bu durumda Genel Bakış&apos;ta{" "}
        <strong>{GK_IKINCI_TOPLANTI_BASLIGI}</strong> işi çıkar.
        {yaz && (
          <>
            {" "}
            İkinci toplantının günü ilk ilanda yoksa “{DUGME_IKINCI_ILAN}” düğmesiyle ilan edilir;
            toplantıdan sonra sayılar “{DUGME_IKINCI_TOPLANTI}” düğmesiyle girilir.
          </>
        )}
      </p>
      {kisisel ? (
        <p>
          Sayımı kolaylaştırmak için {ADIM_TOPLANTI} adımında “{DUGME_KATILIM_ISARETLERI}” düğmesi
          vardır. {KATILIM_ISARETLERI_ACIKLAMASI}
        </p>
      ) : (
        <p>
          Veli adlarını gösteren işaret penceresi ve veli adı taşıyan çıktılar yalnız program
          yöneticisinin hesabında açılır.
        </p>
      )}

      <AltBaslik>5. {ADIM_TUTANAK}</AltBaslik>
      <p>
        {ADIM_TUTANAK} adımı toplantıda olanları sırasıyla kaydeder. Bu adımın kayıtlarını program
        yöneticisi ve sekreter girer.
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>Divan:</strong> {DIVAN_ACIKLAMASI}
          {yaz && (
            <>
              {" "}
              Kayıt “{DUGME_DIVAN}” düğmesiyle yapılır, yanlış kayıt “{DUGME_DIVAN_IPTAL}”
              düğmesiyle düzeltilir. {DIVAN_IPTAL_METNI}
            </>
          )}
        </li>
        <li>
          <strong>Gündem sonuçları:</strong> {SONUC_ACIKLAMASI} {GUNDEM_EKLE_ACIKLAMASI}{" "}
          {GUNDEMDEN_CIKAR_ACIKLAMASI}
          {yaz && (
            <>
              {" "}
              Düğmeler: “{DUGME_SONUC}”, “{DUGME_GUNDEM_EKLE}”, “{DUGME_GUNDEMDEN_CIKAR}”.
            </>
          )}
        </li>
        <li>
          <strong>İbra:</strong> {IBRA_ACIKLAMASI} {IBRA_EDILMEYEN_EVRAK_YARDIMI}
          {yaz && <> Sonuç “{DUGME_IBRA}” düğmesiyle girilir.</>}
        </li>
        <li>
          <strong>Adaylar ve seçim:</strong> {ADAY_ACIKLAMASI} Seçim asıl ve yedek olarak liste
          hâlinde oylanır (md. 10/1-d). {SECIM_ACIKLAMASI}
          {yaz && (
            <>
              {" "}
              Düğmeler: “{DUGME_ADAY}”, “{DUGME_SECIM}”. Yanlış sonuç “{DUGME_SECIM_IPTAL}”
              düğmesiyle düzeltilir. {SECIM_IPTAL_METNI}
            </>
          )}{" "}
          Seçilenler Organlar ekranında kurulun asıl ve yedek üyesi olarak görünür.
        </li>
        <li>
          <strong>Tutanağın bilgileri:</strong> raporları okuyanlar, tahmini bütçeyi sunan ve{" "}
          <strong>{ALAN_TESLIM_GUNU}</strong>. {TESLIM_GUNU_YARDIMI}
          {yaz && <> Bilgiler “{DUGME_TUTANAK_BILGILERI}” düğmesiyle girilir.</>}
        </li>
      </ul>
      <Mevzuat kaynak="Yönetmelik md. 11/1-ç">
        Genel kurulda hesaplar ibra edilmediğinde diğer gündem maddelerinin görüşülmesine devam
        edilir. Divan, ibra edilmeyen muhasebe evraklarını tutanak altına alarak seçilen yeni
        yönetim ve denetleme kuruluna teslim eder. Bu durum, yeni yönetim kurulu ve okul yönetimi
        tarafından il/ilçe millî eğitim müdürlüğüne resmî yazıyla bildirilir.
      </Mevzuat>
      <p>
        Hesaplar ibra edilmezse Genel Bakış&apos;ta <strong>{IBRA_BILDIRIMI_BASLIGI}</strong> işi
        çıkar. Bu işin son günü yoktur; yazı gönderilince program yöneticisi ya da sekreter işi
        yapıldı olarak işaretler (<Ekran to="/kilavuz#genel-bakis">Genel Bakış</Ekran>).
      </p>
      {yaz ? (
        <p>
          Bütün kayıtlar girilince “{DUGME_TUTANAK_TAMAMLA}” düğmesine basın.{" "}
          {TUTANAK_TAMAMLA_METNI}
        </p>
      ) : (
        <p>{TUTANAK_TAMAMLA_METNI}</p>
      )}

      <AltBaslik>6. {ADIM_SONRASI}</AltBaslik>
      <p>
        <strong>{DONEM_GECISI_BASLIGI}:</strong> {DONEM_GECISI_ACIKLAMASI}{" "}
        {yetki.acik("donem_gecisi_onayi") ? (
          <>
            Onay “{DUGME_DONEM_GECISI}” düğmesiyle verilir. {DONEM_GECISI_ONAY_METNI} Onay beklerken
            Genel Bakış&apos;ta <strong>{DONEM_ONAYI_BASLIGI}</strong> işi çıkar.
          </>
        ) : (
          <>Onayı program yöneticisi verir.</>
        )}{" "}
        {OLAGANUSTU_DONEM_ACMAZ}
      </p>
      <p>
        <strong>Görev bölümü:</strong> {GOREV_BOLUMU_ACIKLAMASI} Bir haftalık süre genel kurulun
        yapıldığı günden sayılır. Adımdaki bağlantılar Organlar ekranının {SEKME_YK} ve {SEKME_DK}{" "}
        sekmelerine götürür (<Ekran to="/kilavuz#organlar">Organlar</Ekran>).
      </p>
      <p>
        <strong>TEFBİS:</strong> {TEFBIS_ACIKLAMASI} Genel Bakış&apos;ta şu işler çıkar:{" "}
        {TEFBIS_SATIRLARI}. Bu işlerin son günü yoktur; girişten sonra program yöneticisi işi
        yapıldı olarak işaretler. Program TEFBİS&apos;e bağlanmaz, oraya kayıt yazmaz.
      </p>

      <AltBaslik>{DOSYA_EKLERI_BASLIGI}</AltBaslik>
      <p>
        {DOSYA_EKLERI_ACIKLAMASI} Yönetim kurulunun belgelerini yönetim kurulu rolleri ve program
        yöneticisi, Denetleme Kurulunun raporunu Denetleme Kurulu ekler. Ekler gündemdeki maddenin
        adıyla listelenir.
      </p>

      <AltBaslik>{BELGELER_BASLIGI}</AltBaslik>
      <p>{BELGELER_ACIKLAMASI} Kartlar şunlardır:</p>
      <ul className="list-disc space-y-1 pl-5">
        {BELGELER.map(([ad, ne]) => (
          <li key={ad}>
            <strong>{ad}</strong>: {ne}.
          </li>
        ))}
      </ul>
      <ol className="list-decimal space-y-1 pl-5">
        <li>
          Belgeyi oluşturabilen hesapta kartta “{DUGME_OLUSTUR}” düğmesi görünür. Genel kurul
          belgelerini program yöneticisi ve sekreter oluşturur; çağrı ve gündemi çağıran hesap
          oluşturur. Toplantı başına belgede toplantı seçilir.
        </li>
        <li>
          Davette ve katılım cetvelinde <strong>{ALAN_KIP}</strong> seçilir: {KIP_KISISIZ} ya da{" "}
          {KIP_ADLI}. Kişisiz biçim veli adı taşımaz.
        </li>
        <li>
          Kartta <strong>{URETIM_UYARILARI_BASLIGI}</strong> çıkarsa okuyun; eksik bilgiyi
          tamamlayıp belgeyi yeniden oluşturabilirsiniz.
        </li>
        <li>
          “{DUGME_PDF}”, “{DUGME_WORD}”, “{DUGME_EXCEL}” ya da “{DUGME_WEB}” düğmesiyle dosyayı
          seçtiğiniz yere kaydedin; kartta belgenin hangi biçimleri varsa o düğmeler görünür.
          Kaydetmeyi her hesap yapabilir.
        </li>
        <li>İl/ilçe millî eğitim müdürlüğüne giden resmî yazıda {MUHATAP_YARDIMI}</li>
      </ol>
      {kisisel && (
        <p>
          <strong>{ADLI_CIKTI_BASLIGI}:</strong> “{DUGME_ADLI_PDF}”, “{DUGME_ADLI_WORD}” ya da “
          {DUGME_ADLI_EXCEL}” düğmesi davetin teslim çizelgesini ve katılım cetvelini veli adlarıyla
          üretir. {ADLI_CIKTI_ACIKLAMASI}
        </p>
      )}
      {yetki.acik("evrak_kaydi") && (
        <p>
          Resmî yazının kartındaki “{DUGME_EVRAK_KAYDI}” düğmesi yazıyı giden evrak olarak kaydeder.{" "}
          {EVRAK_KAYDI_ACIKLAMASI} Kayıt{" "}
          <Ekran to="/kilavuz#gelen-giden-evrak">Gelen-Giden Evrak</Ekran> ekranında görünür.
        </p>
      )}
      <Ipucu>
        Programın hazırladığı tutanak, cetvel ve yazılar imzalanıp birliğin genel kurul tutanak
        dosyasına konur (md. 23/1-a); program bu dosyanın yerine geçmez.
      </Ipucu>

      <AltBaslik>Genel kurulun iptali</AltBaslik>
      {yetki.acik("genel_kurul_iptal") ? (
        <p>
          Yanlış açılmış ya da yapılmayacak genel kurul ayrıntının başındaki “{DUGME_IPTAL}”
          düğmesiyle gerekçe yazılarak iptal edilir. {IPTAL_METNI}
        </p>
      ) : (
        <p>
          Genel kurulun iptalini program yöneticisi gerekçesiyle yapar. {IPTAL_METNI} Gerektiğinde
          program yöneticisine başvurun.
        </p>
      )}
    </KilavuzBolumu>
  );
}
