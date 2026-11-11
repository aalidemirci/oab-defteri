// Kılavuz bölümü: Birlik Dönemi (çapa `birlik-donemi`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Ekran adları ve iletiler `birlik-donemi/metinler`'den; sözlük §1 "Birlik dönemi", "Birlik Dönemi ekranı
// (F1c)", "Kural paketi (F1c)"; plan F1c kararları (kural sürümü salt okunur, Ayarlar'da da satırı var;
// geçiş adımı atlanabilir), 8. adım notları (dönem iptali yalnız geçiş dönemi ve işaretten önce; iptal
// edilen dönem seçilme sayılarına girmez; veli satırları dönemsiz kalır), 3. ve 11. adım notları (kural
// kopyası doğrulanamayan dönem salt okur, bant). Kural paketinin iç kimliği ve kural kodları yazılmaz
// (sözlük §2). Yazma adımları yalnız `birlik_donemi_yazma`'da anlatılır.

import {
  ACILIS_GECIS,
  ALAN_ACILIS,
  ALAN_BASLANGIC,
  ALAN_DERS_YILI,
  ALAN_KURAL_SURUMU,
  ALAN_PROGRAM_BASLAMA,
  BIRLIK_DONEMI_BASLIGI,
  DONEM_AYRINTISI_BASLIGI,
  DONEM_IPTAL_METNI,
  DONEM_KAPANDI_NOTU,
  DONEMLER_BASLIGI,
  DUGME_DONEMI_IPTAL,
  DUGME_GECISI_AC,
  GOREV_SURESI_BASLIGI,
  KURAL_KOPYASI_BOZUK,
  KURAL_SURUMU_AYARLAR_BASLIGI,
  KURAL_SURUMU_YARDIMI,
} from "../../birlik-donemi/metinler";
import { useYetki } from "../../oturum/yetki";
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
        yazılır. Ekranı her hesap okur; birlik dönemini program yöneticisi açar ve iptal eder.
      </p>
      <p>
        Birden çok birlik dönemi varsa <strong>{DONEMLER_BASLIGI}</strong> listesinden birini seçin.{" "}
        <strong>{DONEM_AYRINTISI_BASLIGI}</strong> kartı şu satırları yazar: {ALAN_DERS_YILI} ·{" "}
        {ALAN_BASLANGIC} · {ALAN_PROGRAM_BASLAMA} · {ALAN_ACILIS} · {ALAN_KURAL_SURUMU}. Programa
        başlama günü, programın birlik dönemine girdiği gündür; ondan önceki işler programda değil,
        birliğin kendi defterlerindedir.
      </p>

      <AltBaslik>Birlik dönemi nasıl açılır</AltBaslik>
      <p>
        Program okula bir birlik döneminin ortasında giriyorsa birlik dönemi Kurulum
        Sihirbazı&apos;nın dördüncü adımında ya da Geçiş Kurulumu&apos;nda son olağan genel kurulun
        günüyle açılır; ekranda “{ACILIS_GECIS}” yazar. Görevdeki kurulun girilmesi{" "}
        <Ekran to="/kilavuz#gecis-kurulumu">Geçiş Kurulumu</Ekran> bölümündedir.{" "}
        {yazabilir && (
          <>Ekrandaki Geçiş Kurulumu kartının “{DUGME_GECISI_AC}” bağlantısı oraya götürür. </>
        )}
        Okulda daha önce genel kurul yapılmadıysa bu sürümde birlik dönemi açılmaz; o zamana dek
        Organlar ve Temsilciler ekranları boş görünür.
      </p>

      <AltBaslik>Kural sürümü</AltBaslik>
      <p>
        Program yeter sayıları, süreleri, kurulların bileşimini ve seçilme sınırlarını
        Yönetmelik&apos;in maddelerine dayanan kural paketinden okur; her uyarı dayanağını madde
        numarasıyla yazar. {KURAL_SURUMU_YARDIMI} Kural paketi sonradan değişse de kapanmış birlik
        döneminin hesabı değişmez.
      </p>
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
