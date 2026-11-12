// Kılavuz bölümü: Veli Listesi (çapa `veli-listesi`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Sekme kişisel veri taşıdığı için yalnız `veli_listesi` yeteneğinde görünür: adımlar o hesaba
// yazılır, öteki hesap listenin ne olduğunu ve ne tutulduğunu okur.

import type { ReactNode } from "react";

import {
  AKTAR,
  AYDINLATMA_BASLIGI,
  DAHA_ONCE_AKTARILMIS,
  KAYNAK_DOSYA_HATIRLATMASI,
  ONIZLE,
  ONIZLEME_BASLIGI,
  RAPOR_AKTARILACAK,
  RAPOR_AKTARILAMAYAN,
  RAPOR_DOKUNULMAYAN_SINIF,
  RAPOR_DOSYADAKI_SATIR,
  RAPOR_SILINECEK_ESKI_SATIR,
  RAPOR_SINIF,
  SABLON_INDIR,
  VELI_DOSYA_ALANI_ETIKETI,
  VELI_LISTESI_ACIKLAMASI,
  VELI_LISTESINI_SIL,
  VELI_SILME_ONAY_METNI,
  VELI_YERINE_KOYMA_ONIZLEME,
} from "../../kisiler/metinler";
import { PARENT_TEMPLATE_FILENAME } from "../../okul/api";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KapiliEkran, KilavuzBolumu, Kod } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Ekrandaki düğme, sekme ya da alan adı. */
function Ad({ children }: { children: ReactNode }) {
  return <strong className="font-medium text-on-surface">{children}</strong>;
}

export default function VeliListesi(bolum: BolumProps) {
  const yetkili = useYetki().acik("veli_listesi");
  return (
    <KilavuzBolumu {...bolum}>
      <p>{VELI_LISTESI_ACIKLAMASI}</p>
      <p>
        Listeden yalnız velinin adı-soyadı ve öğrencinin sınıfı alınır. Telefon, adres, T.C. kimlik
        numarası, öğrencinin adı ve numarası alınmaz. e-Okul veli adı veren rapor sunmadığı için
        liste okulun doldurduğu şablondan gelir.
      </p>

      {yetkili ? (
        <>
          <AltBaslik>Listeyi aktarmak için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <KapiliEkran to="/kisiler?tab=veli" yetenek="veli_listesi">
                Kişiler → Veli Listesi
              </KapiliEkran>{" "}
              sekmesinde <Ad>{SABLON_INDIR}</Ad> düğmesiyle <Kod>{PARENT_TEMPLATE_FILENAME}</Kod>{" "}
              dosyasını kaydedin.
            </li>
            <li>
              Her öğrenci için bir satır doldurun: <Ad>Velinin Adı Soyadı</Ad> ve{" "}
              <Ad>Öğrencinin Sınıfı</Ad>. Başlıkları değiştirmeyin; başka sütun okunmaz. Şablondaki
              “ÖRNEK VELİ” satırını silin; silinmezse satır olarak aktarılır.
            </li>
            <li>
              <Ad>{AYDINLATMA_BASLIGI}</Ad> kutusunu okuyun. Metni velilere okul duyurur; kutunun
              başındaki not nasıl duyurulacağını söyler. “Veri sorumlusu:” satırı boşsa önce{" "}
              <Ekran to="/ayarlar?tab=okul">Ayarlar → Okul Bilgileri</Ekran>&apos;ndeki alanı
              doldurun; aktarım bu bilgi olmadan da yapılabilir.
            </li>
            <li>
              <Ad>{VELI_DOSYA_ALANI_ETIKETI}</Ad> alanından dosyayı seçip <Ad>{ONIZLE}</Ad>{" "}
              düğmesine basın. <Ad>{ONIZLEME_BASLIGI}</Ad> başlığıyla yalnız sayılar gelir:{" "}
              <Ad>{RAPOR_DOSYADAKI_SATIR}</Ad>, <Ad>{RAPOR_AKTARILACAK}</Ad>,{" "}
              <Ad>{RAPOR_AKTARILAMAYAN}</Ad>, <Ad>{RAPOR_SINIF}</Ad>,{" "}
              <Ad>{RAPOR_SILINECEK_ESKI_SATIR}</Ad>, <Ad>{RAPOR_DOKUNULMAYAN_SINIF}</Ad>.
            </li>
            <li>
              Sonuç doğruysa <Ad>{AKTAR}</Ad> düğmesine basın. Bu düğme önizlemeden önce kapalıdır.
            </li>
            <li>{KAYNAK_DOSYA_HATIRLATMASI}</li>
          </ol>
          <p>
            Dosya Excel ya da CSV olarak kaydedilebilir; makro içeren dosya kabul edilmez.{" "}
            {DAHA_ONCE_AKTARILMIS}
          </p>

          <AltBaslik>Sınıf nasıl yazılır</AltBaslik>
          <p>
            Öğrencinin sınıfı 9-A, 10/B, Hazırlık-A, Anasınıfı-A ya da 5 Yaş-A biçiminde yazılır;
            “9/A” ve “9 A” de tanınır. Okul öncesi grupları ayrı tutulur: 4 Yaş-B ile 5 Yaş-B iki
            ayrı gruptur. İki çocuklu veli iki satırdır, satırlar birleştirilmez.
          </p>

          <AltBaslik>Bir sınıfın listesini yenilemek için</AltBaslik>
          <p>
            Listeyi sınıf sınıf güncelleyebilirsiniz. {VELI_YERINE_KOYMA_ONIZLEME} Liste satır satır
            düzenlenmez, tek bir satır da silinmez; düzeltme, sınıfın dosyasını yeniden aktararak
            yapılır.
          </p>
          <Ipucu>
            Bir sınıfın dosyasını eksiksiz gönderin: o sınıfın eski satırlarının yerine yalnız
            dosyadaki satırlar geçer. <Ad>{RAPOR_AKTARILAMAYAN}</Ad> kutusundaki satırlar listeye
            girmez; tablodaki satır numarası ve nedene bakıp dosyayı düzeltin, sınıfın bütün
            satırlarıyla yeniden aktarın.
          </Ipucu>

          <AltBaslik>Listeyi silmek için</AltBaslik>
          <p>
            <Ad>{VELI_LISTESINI_SIL}</Ad> düğmesine basıp onaylayın. {VELI_SILME_ONAY_METNI}
          </p>
          <p>
            Program listeyi kendiliğinden silmez. Aydınlatma metninin “Saklama:” satırında yazılı
            süreye uymak için, liste artık gerekmediğinde silmeyi siz yaparsınız.
          </p>
        </>
      ) : (
        <p>
          Liste kişisel veri taşıdığı için bu sekme her hesapta görünmez. Liste hakkında bir sorunuz
          varsa program yöneticisine başvurun.
        </p>
      )}
    </KilavuzBolumu>
  );
}
