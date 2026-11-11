// Kılavuz bölümü: Birlik Kişileri (çapa `birlik-kisileri`). Başlık (sekmenin adı), ikon ve sıra
// `KilavuzPage`'dedir. Ekran adları `kisiler/metinler`'den ve türlerin görünen adları
// `kisiler/birlikKisileriApi`'den; sözlük §1 "Birlik kişileri (F1c)", "Kişiler (bugün)"; tasarım §5.2.2,
// §8.4; plan F1c kararları "Kişiler ekranı" (tür görünen adı "İdareci"), 4. adım notları (olası aynı kişi
// onayı, `is_principal`'ın kendiliğinden konması, veli listesinden ekleme yalnız program yöneticisinin)
// ve 11. adımın notları. Yazma adımları `birlik_kisi_yazma`'da, veli listesinden ekleme ayrıca
// `veli_listesi`'nde anlatılır. T.C. kimlik no ve telefon tutulmaz (K9).

import { BIRLIK_KISI_TURU_TR } from "../../kisiler/birlikKisileriApi";
import {
  ALAN_OKUL_MUDURU,
  ALAN_VELIDIR,
  ALAN_YETISKIN_BEYANI,
  BIRLIK_KISILERI_ACIKLAMASI,
  BIRLIK_KISILERI_SEKMESI,
  DUGME_BIRLIK_KISISI_EKLE,
  DUGME_ETKINLESTIR,
  DUGME_PASIF_YAP,
  DUGME_PERSONELDEN_EKLE,
  DUGME_VELI_LISTESINDEN_EKLE,
  OLASI_AYNI_KISI_BASLIGI,
  OLASI_AYNI_KISI_ONAYI,
  PASIFLERI_GOSTER,
  PERSONELDEN_EKLE_YARDIMI,
  VELI_ADI_YARDIMI,
} from "../../kisiler/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function BirlikKisileri(bolum: BolumProps) {
  const yetki = useYetki();
  const yazabilir = yetki.acik("birlik_kisi_yazma");
  const veliden = yazabilir && yetki.acik("veli_listesi");
  const turler = Object.values(BIRLIK_KISI_TURU_TR).join(" · ");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/kisiler?tab=birlik">Kişiler → {BIRLIK_KISILERI_SEKMESI}</Ekran> sekmesi
        organlara ve temsilciliklere girecek kişilerin kaydıdır. {BIRLIK_KISILERI_ACIKLAMASI}{" "}
        Sekmeyi her hesap okur. Ad ve soyad şifreli saklanır.
      </p>
      <p>
        Kişinin <strong>Tür</strong>ü şunlardan biridir: {turler}. “İdareci” okulun yöneticisidir
        (müdür, müdür başyardımcısı ve müdür yardımcısı); programın hesaplarındaki program
        yöneticisi ayrı bir kavramdır. Liste etkin kişileri gösterir; pasif kişiler için “
        {PASIFLERI_GOSTER}” kutusunu işaretleyin.
      </p>
      <p>Kişinin penceresindeki üç işaret organların denetiminde kullanılır:</p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <strong>{ALAN_VELIDIR}:</strong> yönetim kuruluna veli, on sekiz yaşını doldurmuş kursiyer
          ya da okul yaptıran hayırsever girer (md. 12/1); öğretmen ya da idareci de veliyse bu kutu
          işaretlenir.
        </li>
        <li>
          <strong>{ALAN_YETISKIN_BEYANI}:</strong> kursiyer yönetim kuruluna ve Denetleme Kuruluna
          on sekiz yaşını doldurmuşsa girer (md. 12/1, 14/1).
        </li>
        <li>
          <strong>{ALAN_OKUL_MUDURU}:</strong> okul müdürü yönetim kuruluna giremez. Kişinin adı
          Okul Bilgileri&apos;ndeki okul müdürünün adıyla aynıysa kutu kayıt açılırken kendiliğinden
          işaretlenir; yanlışsa kaldırılabilir.
        </li>
      </ul>
      <p>
        Pencerede programdan önceki seçilme sayıları da salt okunur görünür; bu sayılar geçiş
        kurulumunda beyan edilir (<Ekran to="/kilavuz#gecis-kurulumu">Geçiş Kurulumu</Ekran>).
      </p>

      {yazabilir ? (
        <>
          <AltBaslik>Birlik kişisi eklemek için</AltBaslik>
          <ul className="list-disc space-y-1 pl-5">
            <li>
              <strong>{DUGME_BIRLIK_KISISI_EKLE}</strong>: ad, soyad ve türü elle girin.
            </li>
            <li>
              <strong>{DUGME_PERSONELDEN_EKLE}</strong>: öğretmen ve diğer personel sicilinden
              seçin. {PERSONELDEN_EKLE_YARDIMI}
            </li>
            {veliden && (
              <li>
                <strong>{DUGME_VELI_LISTESINDEN_EKLE}</strong>: {VELI_ADI_YARDIMI}
              </li>
            )}
          </ul>
          <p>
            Yeni kişinin adı kayıttaki bir kişinin adına benziyorsa program “
            {OLASI_AYNI_KISI_BASLIGI}” diye sorar. Aynı kişiyse vazgeçip var olan kaydı kullanın;
            başka bir kişiyse “{OLASI_AYNI_KISI_ONAYI}” düğmesine basın.
          </p>
          <AltBaslik>Kullanılmayan kişi</AltBaslik>
          <p>
            Birlik kişisinin kaydı silinmez. Artık kullanılmayacak kişi “{DUGME_PASIF_YAP}”
            düğmesiyle pasif yapılır; pasif kişinin bilgileri değiştirilemez, yeniden gerektiğinde “
            {DUGME_ETKINLESTIR}” düğmesiyle etkinleştirilir.
          </p>
        </>
      ) : (
        <p>
          Bu sekme hesabınıza okuma için açıktır. Bir birlik kişisinin eklenmesi ya da düzeltilmesi
          için program yöneticisine başvurun.
        </p>
      )}
    </KilavuzBolumu>
  );
}
