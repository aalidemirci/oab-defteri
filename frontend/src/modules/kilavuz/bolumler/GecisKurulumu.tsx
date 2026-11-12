// Kılavuz bölümü: Geçiş Kurulumu (çapa `gecis-kurulumu`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Ekran adları `gecis-kurulumu/metinler`'den; sözlük §1 "Geçiş kurulumu (F1c)"; tasarım §7.9; plan F1c
// kararları "Geçiş adımı atlanabilir", 8. adımın kararı ve notları (her geçiş kaydının iptal yolu,
// "Geçiş kurulumu tamamlandı" işaretinden sonra kilit, sayaç beyanının gerekçeli düzeltmesi, karar
// defterinin tasdik uyarısı md. 23/2). Geçiş kaydını yalnız program yöneticisi yazar
// (`birlik_donemi_yazma`); öteki hesaplara adımlar okuma için anlatılır. Mali kısım bu sürümde yoktur,
// vaat edilmez.

import {
  ALAN_DK_BASKANLIK_SAYISI,
  ALAN_KANIT,
  ALAN_KOLTUK,
  ALAN_KURUL,
  ALAN_SECILDIGI_GUN,
  ALAN_SON_SAYFA,
  ALAN_SON_SIRA_NO,
  ALAN_TASDIK_GUNU,
  ALAN_TASDIK_MAKAMI,
  ALAN_YK_SAYISI,
  DEFTER_BASLIGI,
  DUGME_DEFTERI_KAYDET,
  DUGME_KAYDI_IPTAL,
  DUGME_SAYAC_BEYANI,
  DUGME_TAMAMLA,
  DUGME_UYE_EKLE,
  GECIS_BASLIGI,
  ILK_DONEM_BASLIGI,
  KURUL_BASLIGI,
  SAYAC_BASLIGI,
  SAYAC_BILINMIYOR,
  TAMAMLA_BASLIGI,
} from "../../gecis-kurulumu/metinler";
import { BIRLIK_KISILERI_SEKMESI } from "../../kisiler/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function GecisKurulumu(bolum: BolumProps) {
  const yetki = useYetki();
  const yazabilir = yetki.acik("birlik_donemi_yazma");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Program okula bir birlik döneminin ortasında girdiyse programdan önce başlamış birlik dönemi
        ve görevdeki kurul <Ekran to="/birlik-donemi/gecis-kurulumu">{GECIS_BASLIGI}</Ekran>{" "}
        ekranında programa alınır. Ekran menüde yoktur; Birlik Dönemi ekranından, Kurulum
        Sihirbazı&apos;ndan ve Genel Bakış&apos;taki yol haritasından açılır. Geçiş kayıtlarını
        program yöneticisi girer, öteki hesaplar okur.
      </p>
      <p>
        Ekranın başında durum (Başlamadı, Sürüyor, Tamamlandı ya da Gerekmiyor) ve açık adımlar
        yazar. Birlik dönemi genel kurulla açıldıysa geçiş kurulumu gerekmez. Her geçiş kaydı
        denetim izinde geçiş kaydı olarak durur.
      </p>

      <AltBaslik>Adımlar</AltBaslik>
      <ol className="list-decimal space-y-2 pl-5">
        <li>
          <strong>{ILK_DONEM_BASLIGI}:</strong> sihirbazın dördüncü adımında açılmadıysa birlik
          dönemi burada son olağan genel kurulun günüyle açılır (
          <Ekran to="/kilavuz#ilk-kurulum">İlk Kurulum</Ekran>).
        </li>
        <li>
          <strong>{KURUL_BASLIGI}:</strong> görevdeki yönetim kurulu, Denetleme Kurulu ve birlik
          temsilcileri devralınan kayıt olarak girilir; aday kaydı aranmaz. Kişiler önce{" "}
          <Ekran to="/kisiler?tab=birlik">Kişiler → {BIRLIK_KISILERI_SEKMESI}</Ekran>&apos;nde
          kaydedilir.
          {yazabilir && (
            <>
              {" "}
              “{DUGME_UYE_EKLE}” düğmesiyle kişiyi, <strong>{ALAN_KURUL}</strong>,{" "}
              <strong>{ALAN_KOLTUK}</strong> ve görevi seçin; yedekte yedek sırasını, temsilcide
              temsil edilen kurul ya da komisyonu girin. <strong>{ALAN_SECILDIGI_GUN}</strong> boş
              bırakılırsa birlik döneminin başı sayılır. <strong>{ALAN_KANIT}</strong> alanına
              seçimin nereden bilindiğini yazın (örneğin görev bölümü kararının karar defterindeki
              sıra no&apos;su).
            </>
          )}{" "}
          Kişinin türü, okul müdürünün yönetim kuruluna girememesi ve aynı kişinin iki kurulda
          bulunmaması devralınan kayıtta da denetlenir.
        </li>
        <li>
          <strong>{SAYAC_BASLIGI}:</strong> yönetim kurulu başkan ve üyeleri en fazla dört defa (md.
          12/4), Denetleme Kurulu başkanı en fazla üç defa (md. 14/3) seçilebilir. Program
          programdan önceki seçilmeleri bilemez; görevdeki kurulun kişileri için karar defterinden
          sayılan sayı beyan edilir: <strong>{ALAN_YK_SAYISI}</strong> ve{" "}
          <strong>{ALAN_DK_BASKANLIK_SAYISI}</strong>. Beyan görevdeki seçimi de içerir. Sayı
          bilinmiyorsa “{SAYAC_BILINMIYOR}” seçilir; “{SAYAC_BILINMIYOR}” denen bütün kişiler için
          seçilme sınırı uyarısı tek gerekçeyle kapanır. Bilinmeyen sayı seçilmeyi engellemez.
          {yazabilir && (
            <>
              {" "}
              Beyan “{DUGME_SAYAC_BEYANI}” düğmesiyle verilir; verilmiş bir sayı değişirse düzeltme
              gerekçesi istenir.
            </>
          )}
        </li>
        <li>
          <strong>{DEFTER_BASLIGI}:</strong> program karar defterinin yerine geçmez. Programdan
          önceki <strong>{ALAN_SON_SIRA_NO}</strong> ve <strong>{ALAN_SON_SAYFA}</strong> girilir.
          Karar defteri noterce tasdik edilir (md. 23/2): <strong>{ALAN_TASDIK_MAKAMI}</strong> ve{" "}
          <strong>{ALAN_TASDIK_GUNU}</strong> girilmezse ya da makam noter değilse defter için bir
          gerekçe istenir.
          {yazabilir && <> Kayıt “{DUGME_DEFTERI_KAYDET}” düğmesiyle yapılır.</>}
        </li>
        <li>
          <strong>{TAMAMLA_BASLIGI}:</strong> adımlar bitince ya da eksik bırakılacaksa “
          {DUGME_TAMAMLA}” düğmesiyle “Geçiş kurulumu tamamlandı” işareti konur. İşaretten sonra
          geçiş kayıtları kilitlenir: eklenemez, düzeltilemez, iptal edilemez. İşaret konmadan önce
          bütün kayıtları gözden geçirin.
        </li>
      </ol>

      <AltBaslik>Yanlış girilen geçiş kaydı</AltBaslik>
      <p>
        Geçiş kaydının alanları sonradan değiştirilmez. Yanlış kayıt “{DUGME_KAYDI_IPTAL}”
        düğmesiyle gerekçe yazılarak iptal edilir, doğru bilgi yeni kayıtla girilir; iptal edilen
        kayıt silinmez. Devralınan üyelik iptal edilince ona bağlı hesap aynı anda askıya alınır.
        Birlik döneminin kendisi yanlışsa Birlik Dönemi ekranından iptal edilir (
        <Ekran to="/kilavuz#birlik-donemi">Birlik Dönemi</Ekran>). Bunların hepsi “Geçiş kurulumu
        tamamlandı” işaretine kadar yapılabilir.
      </p>
      {!yazabilir && <p>Geçiş kaydında bir yanlış görürseniz program yöneticisine bildirin.</p>}
      {yazabilir && (
        <Ipucu>
          Geçiş kurulumunun açık adımları Genel Bakış&apos;taki yapılacak işler listesinde ve
          Başlangıç Yol Haritası&apos;nda görünür; adım tamamlanınca kendiliğinden düşer.
        </Ipucu>
      )}
    </KilavuzBolumu>
  );
}
