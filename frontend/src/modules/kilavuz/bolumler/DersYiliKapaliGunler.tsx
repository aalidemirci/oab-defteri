// Kılavuz bölümü: Ders Yılları ve Kapalı Günler (çapa `ders-yili-kapali-gunler`). Başlık, ikon ve
// sıra `KilavuzPage`'dedir. Yazma adımları yalnız o yeteneği olan hesaba yazılır; öteki hesap
// iki sekmeyi salt okur görür (Ayarlar'ın rol süzmesi).

import type { ReactNode } from "react";

import { HOLIDAY_KIND_TR } from "../../okul/api";
import { useYetki } from "../../oturum/yetki";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

/** Ekrandaki düğme, sekme ya da alan adı. */
function Ad({ children }: { children: ReactNode }) {
  return <strong className="font-medium text-on-surface">{children}</strong>;
}

export default function DersYiliKapaliGunler(bolum: BolumProps) {
  const yetki = useYetki();
  const dersYiliYazar = yetki.acik("ders_yili_yazma");
  const kapaliGunYazar = yetki.acik("kapali_gun_yazma");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        Okulun takvimi Ayarlar&apos;da iki sekmededir:{" "}
        <Ekran to="/ayarlar?tab=ders-yillari">Ders Yılları</Ekran> ve{" "}
        <Ekran to="/ayarlar?tab=kapali-gunler">Kapalı Günler</Ekran>. Kurulum Sihirbazı&apos;nın
        üçüncü adımında girilen ders yılı ve kapalı günler de burada görünür.
      </p>

      <AltBaslik>Ders yılı ve dönemler</AltBaslik>
      <p>
        Aynı anda yalnız bir ders yılı aktif olabilir. Her ders yılının iki <Ad>ders dönemi</Ad>{" "}
        vardır: 1. dönem ders yılının başlangıcından 1. dönem bitişine, 2. dönem 2. dönem
        başlangıcından ders yılının bitişine kadardır; aradaki süre yarıyıldır. Bu tarihler,
        dönemlik gelir-gider duyurusunun (md. 13/10) ve kantinde yarıyıl ayının yarım kirasının
        (EK-2 md. 4) takvimidir. Ders dönemi, genel kuruldan genel kurula süren birlik döneminden
        ayrı bir kavramdır.
      </p>
      {dersYiliYazar ? (
        <>
          <AltBaslik>Yeni ders yılı açmak için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <Ekran to="/ayarlar?tab=ders-yillari">Ayarlar → Ders Yılları</Ekran> sekmesinde{" "}
              <Ad>Yeni Ders Yılı</Ad> kartına gelin.
            </li>
            <li>
              <Ad>Ders yılı adı</Ad> (2026-2027 gibi), <Ad>Başlangıç</Ad>, <Ad>Bitiş</Ad>,{" "}
              <Ad>1. dönem bitişi</Ad> ve <Ad>2. dönem başlangıcı</Ad> alanlarını doldurun.
            </li>
            <li>
              <Ad>Ders yılı oluştur</Ad> düğmesine basın. Yeni yıl pasif olarak açılır.
            </li>
            <li>
              Hazır olduğunuzda listedeki <Ad>Aktifleştir</Ad> düğmesine basın ve onaylayın. Öteki
              yıllar pasife çekilir.
            </li>
          </ol>
          <p>
            Ders yılı aktifleşince iki takvim yılının resmî tatilleri ve dini bayramları Kapalı
            Günler&apos;e kendiliğinden eklenir; var olan kayıt yinelenmez. Programda bir yılın dini
            bayram tarihleri yoksa bunu söyleyen bir ileti çıkar: o yılın bayramlarını Diyanet
            takvimine bakarak elle ekleyin.
          </p>

          <AltBaslik>Dönem tarihlerini düzeltmek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              Listede ders yılının satırındaki <Ad>Dönemler</Ad> düğmesine basın.
            </li>
            <li>
              <Ad>1. dönem bitişi</Ad> ve <Ad>2. dönem başlangıcı</Ad> tarihlerini girin. 2. dönem,
              1. dönem bittikten sonra başlamalı; iki tarih de ders yılının içinde kalmalıdır.
            </li>
            <li>
              <Ad>Dönemleri kaydet</Ad> düğmesine basın.
            </li>
          </ol>
          <Ipucu>
            Yarıyıl dönem tarihlerinden kendiliğinden kapalı gün olmaz. İş günüyle verilen süreler
            Kapalı Günler&apos;e baktığı için yarıyılı orada “{HOLIDAY_KIND_TR.SCHOOL_BREAK}” olarak
            da ekleyin.
          </Ipucu>
        </>
      ) : (
        <p>
          Dönem tarihlerini görmek için listedeki <Ad>Dönemler</Ad> düğmesine basın. Ders yılı açmak
          ya da tarih düzeltmek için program yöneticisine başvurun.
        </p>
      )}

      <AltBaslik>Kapalı günler ne işe yarar</AltBaslik>
      <p>
        Kapalı günler, mevzuatta iş günüyle verilen sürelerin takvimidir; belge karşılığı elden
        alınan bağışın beş iş günü içinde bankaya yatırılması (md. 16/3) böyle bir süredir. Hafta
        sonu, resmî tatil, dini bayram ve idari izin her zaman kapalı sayılır. Ara tatil ve yarıyıl
        öğrenciye kapalı gün olarak ayrı tutulur; bir sürenin hesabına girip girmediğini o sürenin
        kuralı belirler.
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <Ad>{HOLIDAY_KIND_TR.OFFICIAL}</Ad>: ulusal bayramlar ve genel tatiller.
        </li>
        <li>
          <Ad>{HOLIDAY_KIND_TR.RELIGIOUS}</Ad>: Ramazan ve Kurban Bayramı. Hesapla bulunmuş tarihin
          yanında “tahmini” rozeti durur; bu tarih bir gün kayabilir.
        </li>
        <li>
          <Ad>{HOLIDAY_KIND_TR.SCHOOL_BREAK}</Ad>: ara tatil ve yarıyıl.
        </li>
        <li>
          <Ad>{HOLIDAY_KIND_TR.OTHER}</Ad>: personelin de izinli olduğu, okulun kapalı kaldığı
          günler.
        </li>
      </ul>

      {kapaliGunYazar ? (
        <>
          <AltBaslik>Resmî tatilleri ve dini bayramları eklemek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <Ekran to="/ayarlar?tab=kapali-gunler">Ayarlar → Kapalı Günler</Ekran> sekmesinde{" "}
              <Ad>Yıl</Ad> seçin.
            </li>
            <li>
              <Ad>Resmî ve dini tatilleri ekle</Ad> düğmesine basın. Yeniden basmak kayıtları
              yinelemez; yalnız eksik olanları ekler.
            </li>
            <li>
              “Tahmini” rozetli bir tarihi Diyanet takvimiyle karşılaştırın. Tarih farklıysa kaydı
              silip doğru tarihle “{HOLIDAY_KIND_TR.RELIGIOUS}” türünde yeniden ekleyin; kayıtlar
              düzenlenmez.
            </li>
          </ol>
          <p>
            Arife günleri eklenmez: program kapalı günü tam gün tutar, yarım gün tutamaz. Okul arife
            günü bütünüyle kapalıysa o günü elle ekleyin.
          </p>

          <AltBaslik>Ara tatil, yarıyıl ya da idari izin eklemek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              <Ad>Kapalı Gün Ekle</Ad> kartında <Ad>Ad</Ad> ve <Ad>Tür</Ad> girin. Ara tatil ve
              yarıyıl için “{HOLIDAY_KIND_TR.SCHOOL_BREAK}” türünü seçin.
            </li>
            <li>
              <Ad>Başlangıç</Ad> ve <Ad>Bitiş</Ad> tarihlerini girin. Tek günlük kayıtta bitişi boş
              bırakabilirsiniz.
            </li>
            <li>
              <Ad>Ekle</Ad> düğmesine basın.
            </li>
          </ol>

          <AltBaslik>Kapalı günü silmek için</AltBaslik>
          <p>
            Satırdaki <Ad>Sil</Ad> düğmesine basıp onaylayın. Bundan sonraki süre hesaplarında o
            günler kapalı gün sayılmaz. Sildiğiniz resmî tatil ya da dini bayram,{" "}
            <Ad>Resmî ve dini tatilleri ekle</Ad> düğmesine yeniden basıldığında ya da o yılı
            kapsayan bir ders yılı aktifleştirildiğinde listeye geri gelir.
          </p>
        </>
      ) : (
        <p>
          Kapalı gün eklemek ya da silmek için program yöneticisine başvurun; “tahmini” rozetli bir
          tarihin Diyanet takvimiyle uyuşmadığını görürseniz de bildirin.
        </p>
      )}
    </KilavuzBolumu>
  );
}
