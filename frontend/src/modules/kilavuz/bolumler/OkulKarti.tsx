// Kılavuz bölümü: Okul Bilgileri (çapa `okul-karti`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Alanların yardım metinleri ve seçenek adları ekranın sabitlerinden gelir: ekrandaki söz
// değişirse kılavuz da değişir. Oran ve eşik yazılmaz (altın kural 2); yalnız madde atfı durur.

import type { ReactNode } from "react";

import {
  CANTEEN_MODE_TR,
  SCHOOL_LEVEL_TR,
  SETTLEMENT_TYPE_TR,
  STAFFING_MODE_TR,
} from "../../okul/api";
import {
  ACILIS_YARDIMI,
  KADEME_YARDIMI,
  KAMPUS_ETIKETI,
  KAMPUS_YARDIMI,
  KANTIN_ISLETME_BILGISI,
  KANTIN_YARDIMI,
  KURUM_KODU_YARDIMI,
  MEVCUT_YARDIMI,
  OKUL_ADI_YARDIMI,
  PERSONEL_YARDIMI,
  VERI_SORUMLUSU_ETIKETI,
  VERI_SORUMLUSU_YARDIMI,
  YERLESIM_YARDIMI,
} from "../../okul/metinler";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Seçenek adları, ekrandaki sırayla. */
function secenekler(adlar: Record<string, string>): string {
  return Object.values(adlar).join(" · ");
}

function Alan({ ad, children }: { ad: string; children: ReactNode }) {
  return (
    <li>
      <strong className="font-medium text-on-surface">{ad}.</strong> {children}
    </li>
  );
}

export default function OkulKarti(bolum: BolumProps) {
  const yazabilir = useYetki().acik("okul_karti_yazma");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/ayarlar?tab=okul">Ayarlar → Okul Bilgileri</Ekran> okulun künyesini ve mevzuatın
        okula göre değişen hükümlerine temel olan bilgileri tutar. Kurulum Sihirbazı&apos;nın ikinci
        adımı aynı alanları aynı adlarla gösterir; orada girdiğiniz bilgi burada görünür.
      </p>

      {yazabilir ? (
        <>
          <AltBaslik>Okul bilgilerini güncellemek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <Ekran to="/ayarlar?tab=okul">Ayarlar → Okul Bilgileri</Ekran> sekmesini açın.
            </li>
            <li>Değişen alanları düzeltin. Zorunlu alanlar boş bırakılamaz.</li>
            <li>
              <strong className="font-medium text-on-surface">Kaydet</strong> düğmesine basın.
            </li>
          </ol>
          <p>
            Zorunlu olmayan alanlar <strong className="font-medium">Okul müdürü</strong>, eğitim
            kampüsü işareti, <strong className="font-medium">Okulun açılış tarihi</strong>,{" "}
            <strong className="font-medium">{VERI_SORUMLUSU_ETIKETI}</strong> ve bilgisayarın
            demirbaş no&apos;sudur.
          </p>
        </>
      ) : (
        <p>
          Bu sekme hesabınıza okuma için açıktır: alanlar form yerine liste olarak görünür. Bir
          bilgi yanlış ya da eksikse program yöneticisine başvurun.
        </p>
      )}

      <AltBaslik>Okulun künyesi</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <Alan ad="Okul adı">{OKUL_ADI_YARDIMI}</Alan>
        <Alan ad="İl ve İlçe">Okulun bulunduğu il ve ilçe.</Alan>
        <Alan ad="Okul müdürü">Okul müdürünün adı-soyadı.</Alan>
        <Alan ad="Kurum kodu">{KURUM_KODU_YARDIMI}</Alan>
        <Alan ad="Kademe">
          {secenekler(SCHOOL_LEVEL_TR)}. {KADEME_YARDIMI}
        </Alan>
      </ul>

      <AltBaslik>Mevzuata bağlı bilgiler</AltBaslik>
      <ul className="list-disc space-y-1 pl-5">
        <Alan ad="Öğrenci mevcudu ve Mevcudun tarihi">
          {MEVCUT_YARDIMI} Tarih, sayının alındığı gündür ve bugünden sonra olamaz. Mevcut değişince
          ikisini birlikte güncelleyin.
        </Alan>
        <Alan ad="Yerleşim türü">
          {secenekler(SETTLEMENT_TYPE_TR)}. {YERLESIM_YARDIMI}
        </Alan>
        <Alan ad="Kantin işletme biçimi">
          {secenekler(CANTEEN_MODE_TR)}. {KANTIN_YARDIMI}
        </Alan>
        <Alan ad="Personel çalıştırma biçimi">
          {secenekler(STAFFING_MODE_TR)}. {PERSONEL_YARDIMI}
        </Alan>
        <Alan ad={KAMPUS_ETIKETI.replace(/\.$/, "")}>Onay kutusudur. {KAMPUS_YARDIMI}</Alan>
        <Alan ad="Okulun açılış tarihi">{ACILIS_YARDIMI}</Alan>
      </ul>
      <Ipucu>
        Kantin işletme biçiminde “{CANTEEN_MODE_TR.BIRLIKCE_ISLETILIYOR}” seçilince alanın altında
        şu bilgi çıkar: “{KANTIN_ISLETME_BILGISI}” Bu yalnız bir bilgidir, kaydı engellemez.
      </Ipucu>

      <AltBaslik>Veri sorumlusu</AltBaslik>
      <p>
        {VERI_SORUMLUSU_YARDIMI} Alan isteğe bağlıdır ve en çok 500 karakter alır. Boş bırakılırsa
        aydınlatma metninin “Veri sorumlusu:” satırında uyarı çıkar; aktarım yine de yapılabilir.
        Metni duyurmadan önce bu alanı doldurun.
      </p>
      <p>
        Bu alana kimin yazılacağına program karar vermez, okul müdürlüğü belirler. Sorunun neden
        açık olduğu <Ekran to="/kilavuz#guvenlik-ve-kvkk">Güvenlik ve Kişisel Veriler</Ekran>{" "}
        bölümünde anlatılır.
      </p>

      <AltBaslik>Bilgisayarın demirbaş bilgisi</AltBaslik>
      <p>
        “Bu bilgisayar okul demirbaşıdır.” onayı zorunludur: kişisel bilgisayarlar kurum ağında
        izinsiz kullanılamaz ve Bakanlığa ait veri Bakanlık sistemlerinde barındırılır (Bilgi ve
        Sistem Güvenliği Yönergesi md. 11/8, 11/23). “Bilgisayarın demirbaş no&apos;su” isteğe
        bağlıdır; taşınır kaydındaki numaradır ve kurtarma anahtarı belgesinde de basılır.
      </p>
    </KilavuzBolumu>
  );
}
