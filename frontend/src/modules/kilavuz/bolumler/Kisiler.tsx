// Kılavuz bölümü: Kişiler (çapa `kisiler`). Başlık, ikon ve sıra `KilavuzPage`'dedir. Veli listesi
// (`VeliListesi`) ve birlik kişileri (`BirlikKisileri`, F1c) kendi bölümlerindedir. Yazma adımları yalnız o yeteneği olan hesaba yazılır: kişi
// ekleme ve düzeltme, aktarım ve havuz kararı ayrı yeteneklerdir (`KisilerPage` rol süzmesi).

import type { ReactNode } from "react";

import {
  AKTAR,
  AYDINLATMA_BASLIGI,
  BIRLIK_KISILERI_SEKMESI,
  DAHA_ONCE_AKTARILMIS,
  DOSYA_ALANI_ETIKETI,
  GOREV_TURU_ETIKETI,
  GOREV_TURU_YARDIMI,
  KAYNAK_DOSYA_HATIRLATMASI,
  ONIZLE,
  ONIZLEME_BASLIGI,
  SABLON_INDIR,
  VELI_LISTESI_SEKMESI,
} from "../../kisiler/metinler";
import { MEMBER_KIND_TR, PERSONNEL_TEMPLATE_FILENAME } from "../../okul/api";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KapiliEkran, KilavuzBolumu, Kod } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Ekrandaki düğme, sekme ya da alan adı. */
function Ad({ children }: { children: ReactNode }) {
  return <strong className="font-medium text-on-surface">{children}</strong>;
}

export default function Kisiler(bolum: BolumProps) {
  const yetki = useYetki();
  const yazabilir = yetki.acik("kisi_yazma");
  const aktarabilir = yetki.acik("eokul_aktarimi");
  const havuzAcik = yetki.acik("ayrilis_havuzu");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Kişiler ekranının sekmeleri hesabın rolüne göre görünür. Veli listesi ve birlik kişileri
        kendi bölümlerinde anlatılır (
        <Ekran to="/kilavuz#veli-listesi">{VELI_LISTESI_SEKMESI}</Ekran>,{" "}
        <Ekran to="/kilavuz#birlik-kisileri">{BIRLIK_KISILERI_SEKMESI}</Ekran>); bu bölüm öğretmen
        ve diğer personelin sicilini ve Ayrılış Havuzu&apos;nu anlatır.
      </p>
      <p>
        <Ekran to="/kisiler?tab=personel">Kişiler → Öğretmenler ve Diğer Personel</Ekran> okulun
        sicilidir. Sicilde yalnız ad-soyad ve görev türü tutulur; T.C. kimlik numarası, unvan ve
        branş tutulmaz. <Ad>{GOREV_TURU_ETIKETI}</Ad> üç değer alır: {MEMBER_KIND_TR.OGRETMEN} ·{" "}
        {MEMBER_KIND_TR.YONETICI} · {MEMBER_KIND_TR.DIGER}.
      </p>
      <p>
        <Ad>Durum</Ad> sütunu kişinin okulda olup olmadığını söyler: <Ad>Aktif</Ad>,{" "}
        <Ad>Ayrılış kararı bekliyor</Ad> (son aktarılan listede bulunmadı, kişi hâlâ aktiftir) ya da{" "}
        <Ad>Ayrıldı · gg.aa.yyyy</Ad>.
      </p>
      {!yazabilir && (
        <p>
          Bu sekme hesabınıza okuma için açıktır. Bir kaydın eklenmesi ya da düzeltilmesi için
          program yöneticisine başvurun.
        </p>
      )}

      {yazabilir && (
        <>
          <AltBaslik>Bir kişiyi elle eklemek ya da düzeltmek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              Yeni kayıt için <Ad>Kişi ekle</Ad> düğmesine, var olan kayıt için listede kişinin
              satırına basın.
            </li>
            <li>
              <Ad>Ad</Ad>, <Ad>Soyad</Ad> ve <Ad>{GOREV_TURU_ETIKETI}</Ad> alanlarını doldurun.{" "}
              {GOREV_TURU_YARDIMI}
            </li>
            <li>
              <Ad>Kaydet</Ad> düğmesine basın.
            </li>
          </ol>

          <AltBaslik>Okuldan ayrılan kişi için</AltBaslik>
          <p>
            Kişinin satırına basın, açılan <Ad>Kişiyi düzenle</Ad> penceresinde{" "}
            <Ad>Ayrıldı olarak işaretle</Ad> düğmesini kullanın. Kişi okuldan ayrılmış sayılır ve
            seçicilerden düşer; kaydı bu işlemle silinmez, sicilde “Ayrıldı · gg.aa.yyyy” rozetiyle
            kalır. Aydınlatma metninin “Saklama:” satırında duyurulan silmeyi program kendiliğinden
            yapmaz.
          </p>
          <p>
            Aynı penceredeki <Ad>Sil</Ad> düğmesi yanlış girilmiş kayıtlar içindir ve geri alınamaz.
            Birlik kayıtlarına bağlı kişi silinemez. Denetim izine yalnız bir kaydın silindiği
            yazılır, kişinin adı yazılmaz.
          </p>
        </>
      )}

      {aktarabilir && (
        <>
          <AltBaslik>Listeyi e-Okul&apos;dan aktarmak için</AltBaslik>
          <p>
            Program e-Okul&apos;a bağlanmaz; okulun e-Okul&apos;dan aldığı dosyayı okur. Panel,
            sekmenin altındadır.
          </p>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              e-Okul&apos;da Kurum İşlemleri → Raporlar → OOK01001R1 — Personel Listesi raporunu
              Excel olarak indirin. Dosyayı değiştirmeyin.
            </li>
            <li>
              Panelde <Ad>{AYDINLATMA_BASLIGI}</Ad> kutusunu okuyun. Bu metin kişisel verisi
              aktarılan personele okulda duyurulur; duyuruyu okul yapar. Kutunun altındaki notun
              söylediği gibi veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir (
              <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran>).
            </li>
            <li>
              <Ad>{DOSYA_ALANI_ETIKETI}</Ad> alanından dosyayı seçip <Ad>{ONIZLE}</Ad> düğmesine
              basın. <Ad>{ONIZLEME_BASLIGI}</Ad> başlığıyla sonuç gelir.
            </li>
            <li>
              Sayıları denetleyin: <Ad>Toplam satır</Ad>, <Ad>İşlenen</Ad>, <Ad>Yeni</Ad>,{" "}
              <Ad>Güncellenen</Ad>, <Ad>Değişmeyen</Ad>, <Ad>Havuza eklenecek</Ad>,{" "}
              <Ad>Havuzdan çıkacak</Ad>. Altındaki tablolar uyarıları ve atlanan satırları satır
              numarasıyla gösterir.
            </li>
            <li>
              Sonuç doğruysa <Ad>{AKTAR}</Ad> düğmesine basın.
            </li>
            <li>{KAYNAK_DOSYA_HATIRLATMASI}</li>
          </ol>
          <p>
            Rapordan ad-soyad okunur; “Görevi” sütunu yalnız görev türünü belirlemek için kullanılır
            ve saklanmaz, unvan ve branş okunmaz. Kişiler ad-soyada göre eşlenir.{" "}
            {DAHA_ONCE_AKTARILMIS}
          </p>

          <AltBaslik>e-Okul raporu yerine şablon ya da tablo kullanmak için</AltBaslik>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <Ad>{SABLON_INDIR}</Ad> düğmesiyle <Kod>{PERSONNEL_TEMPLATE_FILENAME}</Kod> dosyasını
              kaydedin. Sütunları <Ad>Adı</Ad>, <Ad>Soyadı</Ad> ve <Ad>Görev Türü</Ad>dür.
              Şablondaki “ÖRNEK ÖĞRETMEN” satırını silin; silinmezse kişi olarak aktarılır. Dosya
              Excel ya da CSV olarak kaydedilebilir.
            </li>
            <li>
              Elinizdeki tabloyu kopyalayıp <Ad>Ya da tabloyu yapıştırın</Ad> alanına
              yapıştırabilirsiniz.
            </li>
          </ul>
          <p>
            Makro içeren dosya kabul edilmez; dosyayı Excel&apos;de “Excel Çalışma Kitabı (*.xlsx)”
            olarak kaydedip yeniden yükleyin. PDF desteklenmez.
          </p>

          <AltBaslik>“Görev türünü denetleyin” uyarısı çıkınca</AltBaslik>
          <p>
            e-Okul&apos;un “Görevi” sütunu şöyle okunur: Müdür, Müdür Başyardımcısı ve Müdür
            Yardımcısı yönetici; içinde “öğretmen” geçen görev öğretmen; öteki görevler diğer
            personel sayılır. Görev boşsa ya da yönetici veya öğretmen görevine benzeyip tam
            tanınmadıysa (“Müdür Yrd.”, “Psikolojik Danışman” gibi) satır uyarı alır. Bu satırlarda
            var olan kaydın görev türü değişmez, yeni kayıt kurala göre açılır (görev boşsa öğretmen
            olarak).
          </p>
          <p>
            Gerekirse kişiyi düzenleyip doğru görev türünü seçin; seçiminiz sonraki aktarımlarda
            korunur.
          </p>
        </>
      )}

      <AltBaslik>Ayrılış Havuzu</AltBaslik>
      <p>
        Aktarım kimseyi ayırmaz ve kimsenin kaydını silmez. Son listede bulunmayan öğretmen ve diğer
        personel{" "}
        <KapiliEkran to="/kisiler?tab=havuz" yetenek="ayrilis_havuzu">
          Ayrılış Havuzu
        </KapiliEkran>
        &apos;nda karar bekler; bu sürede durumu aktif kalır. Dosyada bulunan kişi havuzdan
        kendiliğinden çıkar.
      </p>
      {havuzAcik ? (
        <>
          <AltBaslik>Havuzdaki kişiler hakkında karar vermek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <KapiliEkran to="/kisiler?tab=havuz" yetenek="ayrilis_havuzu">
                Kişiler → Ayrılış Havuzu
              </KapiliEkran>{" "}
              sekmesinde kişileri işaretleyin. Tek tek ya da hepsini birden seçebilirsiniz.
            </li>
            <li>
              Okulda kalanlar için <Ad>Aktif kalsın</Ad>, okuldan ayrılanlar için{" "}
              <Ad>Ayrıldı olarak işaretle</Ad> düğmesine basın.
            </li>
          </ol>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <Ad>Aktif kalsın</Ad> kişiyi yalnız havuzdan çıkarır; sonraki listede yine yoksa kişi
              havuza döner.
            </li>
            <li>
              <Ad>Ayrıldı olarak işaretle</Ad> kaydı silmez. Sonraki bir e-Okul listesinde yeniden
              görünen kişinin kaydı yeniden aktif olur.
            </li>
          </ul>
          <Ipucu>
            Listede ad-soyadı boş bir satır varsa o aktarımda hiç kimse havuza eklenmez, çünkü o
            satırdaki kişi tanınamaz. Satırı düzeltip yeniden aktarın.
          </Ipucu>
        </>
      ) : (
        <p>
          “Ayrılış kararı bekliyor” durumundaki bir kişi için karar gerekiyorsa program yöneticisine
          başvurun.
        </p>
      )}

      {(aktarabilir || havuzAcik) && (
        <>
          <AltBaslik>“Olası aynı kişi” çıkınca</AltBaslik>
          <p>
            Listedeki yeni ad kayıttaki bir kişiye benziyorsa (soyadı değişimi gibi) iki kayıt yan
            yana gösterilir ve her satır neden aday olduğunu yazar. Aday yalnız ad benzerliğiyle
            bulunur; okula yeni gelen bir adaş da olabilir.
          </p>
          {yazabilir ? (
            <>
              <p>
                Aynı kişiyse onu ayrıldı diye işaretlemeyin, <Ad>Birleştir</Ad> düğmesini kullanın.
                Düğme aktarımdan sonra sonuç ekranında ve Ayrılış Havuzu&apos;nda görünür. Açılan{" "}
                <Ad>Bu iki kayıt aynı kişi mi?</Ad> penceresinde iki kaydı karşılaştırıp doğrulama
                kutusunu işaretleyin.
              </p>
              <p>
                Birleştirilen eski kaydın bağları yeni kayda taşınır, eski kayıt silinir. Bu işlem
                geri alınamaz.
              </p>
            </>
          ) : (
            <p>İki kaydın birleştirilmesi için program yöneticisine başvurun.</p>
          )}
        </>
      )}
    </KilavuzBolumu>
  );
}
