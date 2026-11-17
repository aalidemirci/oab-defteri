// Kılavuz bölümü: Birlik Dönemi (çapa `birlik-donemi`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Ekran adları ve iletiler `birlik-donemi/metinler`'den; sözlük §1 "Birlik dönemi", "Birlik Dönemi ekranı
// (F1c)", "Kural paketi (F1c)"; plan F1c kararları (kural sürümü salt okunur, Ayarlar'da da satırı var;
// geçiş adımı atlanabilir), 8. adım notları (dönem iptali yalnız geçiş dönemi ve işaretten önce; iptal
// edilen dönem seçilme sayılarına girmez; veli satırları dönemsiz kalır), 3. ve 11. adım notları (kural
// kopyası doğrulanamayan dönem salt okur, bant). Kural paketinin iç kimliği ve kural kodları yazılmaz
// (sözlük §2). Yazma adımları yalnız `birlik_donemi_yazma`'da anlatılır. F2: genel kurulla açılış (olağan
// genel kurulun planlanmasıyla hazırlık dönemi, tutanaktan sonra program yöneticisinin onayı — plan F2 §7
// U3, U32; sözlük §1 "Birlik Dönemi ekranı — genel kurul ve kural sürümü güncellemesi (F2)"), yeni açılan
// okulun ilk genel kurulu (md. 9/1) ve kural sürümü güncellemesi (yalnız `kural_surumu_guncelleme`).

import {
  ACILIS_GECIS,
  ACILIS_GENEL_KURUL,
  ACILIS_HAZIRLIK,
  ACILIS_IPTAL,
  ALAN_ACILIS,
  ALAN_BASLANGIC,
  ALAN_DERS_YILI,
  ALAN_KURAL_SURUMU,
  ALAN_PROGRAM_BASLAMA,
  BAG_GENEL_KURUL_EKRANI,
  BIRLIK_DONEMI_BASLIGI,
  BITIS_YOK,
  DONEM_AYRINTISI_BASLIGI,
  DONEM_DURUMU_TR,
  DONEM_IPTAL_METNI,
  DONEM_KAPANDI_NOTU,
  DONEMLER_BASLIGI,
  DONEM_YOK_BASLIGI,
  DONEM_YOK_YENI_OKUL_ACIKLAMASI,
  DUGME_DONEMI_IPTAL,
  DUGME_GECISI_AC,
  DUGME_GERI_AL,
  DUGME_SURUMU_GUNCELLE,
  ETKILENEN_KAYITLAR,
  ETKILENEN_ONAYI,
  FARK_BITEN,
  FARK_CIKARILAN,
  FARK_DEGER,
  FARK_DUZELTILEN,
  FARK_EKLENEN,
  GOREV_SURESI_BASLIGI,
  KURAL_GUNCEL,
  KURAL_GUNCELLEME_ACIKLAMASI,
  KURAL_GUNCELLEME_BASLIGI,
  KURAL_KOPYASI_BOZUK,
  KURAL_SURUMU_AYARLAR_BASLIGI,
  KURAL_SURUMU_YARDIMI,
} from "../../birlik-donemi/metinler";
import { ADIM_SONRASI, DONEM_GECISI_ONAY_METNI, IPTAL_METNI } from "../../genel-kurul/metinler";
import { useYetki } from "../../oturum/yetki";
import { KURAL_SURUMU_BASLIGI } from "../../pano/metinler";
import { AltBaslik, Ekran, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function BirlikDonemi(bolum: BolumProps) {
  const yetki = useYetki();
  const yazabilir = yetki.acik("birlik_donemi_yazma");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/birlik-donemi">{BIRLIK_DONEMI_BASLIGI}</Ekran> ekranı okul-aile birliğinin genel
        kuruldan genel kurula süren dönemini gösterir. Birlik dönemi ders yılının iki döneminden
        (ders dönemi) ayrıdır; organların, temsilcilerin ve belgelerin kayıtları birlik dönemine
        yazılır. Ekranı her hesap okur. Birlik dönemi genel kurulla açılır; program okula bir birlik
        döneminin ortasında giriyorsa program yöneticisi onu geçiş kurulumuyla açar.
      </p>
      <p>
        Birden çok birlik dönemi varsa <strong>{DONEMLER_BASLIGI}</strong> listesinden birini seçin.{" "}
        <strong>{DONEM_AYRINTISI_BASLIGI}</strong> kartı şu satırları yazar: {ALAN_DERS_YILI} ·{" "}
        {ALAN_BASLANGIC} · {ALAN_PROGRAM_BASLAMA} · {ALAN_ACILIS} · {ALAN_KURAL_SURUMU}. Programa
        başlama günü, programın birlik dönemine girdiği gündür; ondan önceki işler programda değil,
        birliğin kendi defterlerindedir. Durumlar: {Object.values(DONEM_DURUMU_TR).join(" · ")}.
        Açık birlik döneminin bitişinde “{BITIS_YOK}” yazar.
      </p>

      <AltBaslik>Birlik dönemi nasıl açılır</AltBaslik>
      <ul className="list-disc space-y-2 pl-5">
        <li>
          <strong>Genel kurulla:</strong> olağan genel kurul planlanınca yeni birlik dönemi hazırlık
          durumunda açılır; <strong>{ALAN_ACILIS}</strong> satırında “{ACILIS_HAZIRLIK}” yazar.
          Genel kurulun tutanağı tamamlanınca program yöneticisi açılışı genel kurulun{" "}
          {ADIM_SONRASI} adımında onaylar: {DONEM_GECISI_ONAY_METNI} Yeni birlik dönemi genel
          kurulun yapıldığı gün başlar; satırda “{ACILIS_GENEL_KURUL}” yazar (
          <Ekran to="/kilavuz#genel-kurul">Genel Kurul</Ekran>).
        </li>
        <li>
          <strong>Geçiş kurulumuyla:</strong> program okula bir birlik döneminin ortasında giriyorsa
          birlik dönemi Kurulum Sihirbazı&apos;nın dördüncü adımında ya da Geçiş Kurulumu&apos;nda
          son olağan genel kurulun günüyle açılır; satırda “{ACILIS_GECIS}” yazar. Görevdeki kurulun
          girilmesi <Ekran to="/kilavuz#gecis-kurulumu">Geçiş Kurulumu</Ekran> bölümündedir.
          {yazabilir && (
            <> Ekrandaki Geçiş Kurulumu kartının “{DUGME_GECISI_AC}” bağlantısı oraya götürür.</>
          )}
        </li>
        <li>
          <strong>Yeni açılan okulda:</strong> İlk genel kurul okulun açıldığı tarihten başlayarak
          en geç iki ay içinde toplanır (md. 9/1).{" "}
          {yetki.acik("genel_kurul_yazma") ? (
            <>
              Okul Bilgileri&apos;nde okulun açılış tarihi girilmişse ve henüz birlik dönemi yoksa
              ekran şunu yazar: “{DONEM_YOK_YENI_OKUL_ACIKLAMASI}” Ekrandaki “
              {BAG_GENEL_KURUL_EKRANI}” bağlantısı Genel Kurul ekranını açar.
            </>
          ) : (
            <>
              Birlik dönemi açılmadıysa ekranda yalnız “{DONEM_YOK_BASLIGI}” yazar. İlk genel kurulu
              program yöneticisi ya da sekreter planlar.
            </>
          )}
        </li>
      </ul>
      <p>
        Hiç birlik dönemi yokken Organlar ve Temsilciler ekranları boş görünür. Organlar ekranından
        kayıt yalnız açık birlik dönemine yazılır.
      </p>

      <AltBaslik>Kural sürümü</AltBaslik>
      <p>
        Program yeter sayıları, süreleri, kurulların bileşimini ve seçilme sınırlarını
        Yönetmelik&apos;in maddelerine dayanan kural paketinden okur; her uyarı dayanağını madde
        numarasıyla yazar. {KURAL_SURUMU_YARDIMI} Kapanmış birlik döneminin hesabı değişmez.
      </p>
      {yetki.acik("kural_surumu_guncelleme") ? (
        <>
          <p>
            Programla yeni bir kural sürümü gelince Genel Bakış&apos;ta{" "}
            <strong>{KURAL_SURUMU_BASLIGI}</strong> işi çıkar. Açık ya da hazırlıktaki birlik
            döneminin ayrıntısında <strong>{KURAL_GUNCELLEME_BASLIGI}</strong> bölümü durur.{" "}
            {KURAL_GUNCELLEME_ACIKLAMASI}
          </p>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              Farkı okuyun: {FARK_EKLENEN} · {FARK_CIKARILAN} · {FARK_BITEN} · {FARK_DEGER} ·{" "}
              {FARK_DUZELTILEN}.
            </li>
            <li>
              <strong>{ETKILENEN_KAYITLAR}</strong> listesi çıkarsa okuyun ve “{ETKILENEN_ONAYI}”
              kutusunu işaretleyin.
            </li>
            <li>“{DUGME_SURUMU_GUNCELLE}” düğmesine basın.</li>
          </ol>
          <p>
            Önceki sürüme “{DUGME_GERI_AL}” düğmesiyle dönülür. Birlik dönemi en yeni sürümdeyse
            bölümde “{KURAL_GUNCEL}” yazar. Genel kurul, genel kurulun kurallarını taşıyan kural
            sürümüyle planlanır; gerekirse önce bu güncelleme yapılır.
          </p>
        </>
      ) : (
        <p>
          Programla yeni bir kural sürümü gelince birlik dönemi kendiliğinden geçmez; farkı görüp
          geçişi program yöneticisi onaylar. Bir sorunuz varsa program yöneticisine başvurun.
        </p>
      )}
      <p>
        Aynı bilgi <Ekran to="/ayarlar">Ayarlar</Ekran> sayfasının altındaki{" "}
        <strong>{KURAL_SURUMU_AYARLAR_BASLIGI}</strong> bölümünde de salt okunur olarak yazar: açık
        birlik döneminin kural sürümü, açık birlik dönemi yoksa iptal edilmemiş en son birlik
        döneminin.
      </p>

      <AltBaslik>Uyarılar ve bantlar</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>{GOREV_SURESI_BASLIGI}:</strong> yönetim kurulunun ve Denetleme Kurulunun görev
          süresi bir yıldır (md. 12/2, 14/2). Son genel kuruldan bu yana bir yıl geçtiyse uyarı
          çıkar; uyarı kaydedilmez, gerekçe istemez.
        </li>
        <li>
          Kapanmış birlik döneminde “{DONEM_KAPANDI_NOTU}” yazar; o döneme kayıt eklenmez, kayıt
          değiştirilmez.
        </li>
        <li>
          Programın birlik dönemi için sakladığı kural kopyası doğrulanamazsa şu bant çıkar: “
          {KURAL_KOPYASI_BOZUK}” Bu durumda kayıtlar okunur ama o birlik dönemine yazılmaz; yazma
          düğmeleri görünmez. Aynı bant Genel Bakış&apos;ta ve Ayarlar&apos;da da çıkar.
        </li>
      </ul>

      <AltBaslik>Yanlış açılmış birlik dönemi</AltBaslik>
      <p>
        Hazırlıktaki birlik dönemi kendi başına iptal edilmez; onu açan genel kurul iptal edilince o
        da iptal edilir. Genel kurulun iptal penceresi şunu yazar: “{IPTAL_METNI}” Birlik döneminin
        satırında “{ACILIS_IPTAL}” yazar.
      </p>
      {yazabilir ? (
        <>
          <p>
            Geçiş kurulumuyla açılan birlik dönemi yanlış girildiyse (yanlış gün, yanlış ders yılı)
            alanları değiştirilmez; “{DUGME_DONEMI_IPTAL}” düğmesiyle iptal edilir. Düğme yalnız
            “Geçiş kurulumu tamamlandı” işaretinden önce görünür. {DONEM_IPTAL_METNI} İptal
            gerekçesi şifreli saklanır.
          </p>
          <p>
            İptal edilen birlik döneminin kayıtları seçilme sayılarına girmez. Veli listesinin
            satırları o birlik dönemine bağlı olmaktan çıkar ve sonra açılan birlik dönemine
            bağlanır.
          </p>
        </>
      ) : (
        <p>
          Birlik dönemi yanlış girildiyse program yöneticisine başvurun: kayıt değiştirilmez,
          gerekçeyle iptal edilip yeniden açılır.
        </p>
      )}
    </KilavuzBolumu>
  );
}
