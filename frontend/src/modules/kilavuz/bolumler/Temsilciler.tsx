// Kılavuz bölümü: Temsilciler (çapa `temsilciler`). Başlık, ikon ve sıra `KilavuzPage`'dedir. Ekran adları
// `temsilciler/metinler`'den, belge kartının adları `evrak/metinler`'den, seçim kanalının adı
// `organlar/metinler`'den. Kaynaklar: sözlük §1 "Temsilciler ekranı (F1c)", "Görev bölümü ve temsilci
// evrakı (F1c)"; tasarım §5.2.2 "Temsil türleri", §6.4.4; plan F1c kararları "Temsilciler ayrı ekran",
// 6. ve 10-11. adım notları (kurul temsilcisini yönetim kurulu kararı belirler; birlik başkanı bazı
// komisyonlara başkan sıfatıyla kendiliğinden girer; karar bağı yalnız kabul edilmiş ya da deftere
// işlenmiş karar; çizelge belgenin tek kaynağıdır). Genelge maddesi kod biçiminde yazılmaz (sözlük §2).

import {
  DUGME_OLUSTUR,
  DUGME_PDF,
  DUGME_WORD,
  E03_ADI,
  TASLAK_ACIKLAMASI,
} from "../../evrak/metinler";
import { DUGME_KAYDI_IPTAL, SECIM_KANALI_TR } from "../../organlar/metinler";
import { useYetki } from "../../oturum/yetki";
import {
  ALAN_GOREVLENDIRME_GUNU,
  ALAN_KARAR,
  CIZELGE_BASLIGI,
  CIP_KARAR_BAGLI,
  DUGME_TEMSILCI_EKLE,
  DURUM_EKSIK,
  DURUM_UYARI,
  TEMSILCILER_ACIKLAMASI,
  TEMSILCILER_BASLIGI,
} from "../../temsilciler/metinler";
import { AltBaslik, Ekran, KilavuzBolumu } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function Temsilciler(bolum: BolumProps) {
  const yetki = useYetki();
  const ekleyebilir = yetki.acik("temsilci_yazma");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/temsilciler">{TEMSILCILER_BASLIGI}</Ekran> ekranı: {TEMSILCILER_ACIKLAMASI}{" "}
        Ekranı her hesap okur; kayıtlar birlik dönemine yazılır.
      </p>
      <p>
        <strong>{CIZELGE_BASLIGI}</strong> okulun kademesine, kantinine ve okul bilgilerine göre
        birlik temsilcisi gereken kurul ve komisyonları kart kart sayar: okul öğrenci ödül ve
        disiplin kurulu, okul sosyal etkinlikler kurulu, kontenjan belirleme komisyonu, rehberlik ve
        psikolojik danışma hizmetleri yürütme komisyonu, kantin denetim komisyonu gibi. Her kartta
        temsilciler adı ve koltuğuyla (asıl ya da yedek) yazar; birlik başkanının kendiliğinden
        girdiği komisyonlarda “{SECIM_KANALI_TR.KENDILIGINDEN}”, karara bağlı kayıtta “
        {CIP_KARAR_BAGLI}” işareti durur. Kartın durumu “{DURUM_UYARI}” ya da “{DURUM_EKSIK}” ise
        altındaki ileti nedeni ve dayanağı yazar; ileti kaydı engellemez.
      </p>

      {ekleyebilir ? (
        <>
          <AltBaslik>Temsilci girmek için</AltBaslik>
          <ol className="list-decimal space-y-1 pl-5">
            <li>Kurul ya da komisyonun kartındaki “{DUGME_TEMSILCI_EKLE}” düğmesine basın.</li>
            <li>
              Kişiyi, koltuğu ve <strong>{ALAN_GOREVLENDIRME_GUNU}</strong> alanını doldurun. Kişi
              önce <Ekran to="/kilavuz#birlik-kisileri">Birlik Kişileri</Ekran>&apos;nde kaydedilmiş
              olmalıdır.
            </li>
            <li>
              <strong>{ALAN_KARAR}</strong> alanında temsilciyi belirleyen kararı seçin. Yalnız
              kabul edilmiş ya da karar defterine işlenmiş yönetim kurulu kararı bağlanabilir;
              bağlanacak karar yoksa kayıt gerekçe ister.
            </li>
          </ol>
        </>
      ) : (
        <p>Temsilcinin girilmesi ya da düzeltilmesi için program yöneticisine başvurun.</p>
      )}
      <p>
        Yanlış kayıt temsilcinin yanındaki “{DUGME_KAYDI_IPTAL}” düğmesiyle gerekçe yazılarak iptal
        edilir; kayıt silinmez. Birlik başkanının kendiliğinden girdiği satırlar görev bölümüyle
        açılır; başkanlığı bırakanın satırları düşer, yeni başkanınki açılır.
      </p>

      <AltBaslik>Görevlendirme çizelgesi</AltBaslik>
      <p>
        Ekranın altındaki <strong>{E03_ADI}</strong> kartı çizelgeyi belge olarak verir; belge
        ekrandaki çizelgenin aynısıdır. {TASLAK_ACIKLAMASI} Belgeyi sekreter ya da program
        yöneticisi “{DUGME_OLUSTUR}” düğmesiyle oluşturur, her hesap “{DUGME_PDF}” ya da “
        {DUGME_WORD}” düğmesiyle kaydeder. Belgenin sonunda okul müdürünün teslim aldığı imza bloğu
        vardır. Belgenin oluşturulması ve sürümleri <Ekran to="/kilavuz#organlar">Organlar</Ekran>{" "}
        bölümündeki görev bölümü belgeleriyle aynıdır.
      </p>
    </KilavuzBolumu>
  );
}
