// Kılavuz bölümü: Gelen-Giden Evrak (çapa `gelen-giden-evrak`). Başlık, ikon ve sıra `KilavuzPage`'dedir.
// Ekran, alan ve düğme adları `gelen-giden-evrak/metinler`'den; resmî yazının kaydı `genel-kurul/metinler`'
// den. Kaynaklar: sözlük §1 "Gelen-Giden Evrak ekranı (F2)"; tasarım §5.2.8; plan F2 §6.1 (M10), §7 U20.
// Yazma `evrak_kaydi`'ndadır (program yöneticisi ve yönetim kurulu rolleri); okul müdürü ve Denetleme
// Kurulu okur. Numara tekilliği serttir (hesap bütünlüğü), sıra atlama uyarı + gerekçedir. Program
// gelen-giden evrak defterinin yerine geçmez (md. 23/1-c, 23/2).

import {
  DUGME_EVRAK_KAYDI,
  EVRAK_KAYDI_ACIKLAMASI,
  GENEL_KURUL_BASLIGI,
} from "../../genel-kurul/metinler";
import {
  ALAN_DIS_SAYI,
  ALAN_KARSI_TARAF,
  ALAN_SON_NO,
  ALAN_TASDIK_MAKAMI,
  ALAN_YIL,
  ALAN_YON,
  DEFTER_ACIKLAMASI,
  DEFTER_YOK,
  DUGME_DEFTER,
  DUGME_YENI_KAYIT,
  GELEN_GIDEN_BASLIGI,
  KAYIT_ACIKLAMASI,
  KAYIT_EKI_YARDIMI,
  PROGRAMIN_YAZISI,
  SIRADAKI_NO,
  TASDIK_MAKAMI_TR,
  YON_TR,
} from "../../gelen-giden-evrak/metinler";
import { useYetki } from "../../oturum/yetki";
import { GEREKCE_BASLIGI } from "../../uyum/metinler";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Mevzuat } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function GelenGidenEvrak(bolum: BolumProps) {
  const yazabilir = useYetki().acik("evrak_kaydi");
  return (
    <KilavuzBolumu {...bolum}>
      <p>
        <Ekran to="/gelen-giden-evrak">{GELEN_GIDEN_BASLIGI}</Ekran> ekranı birliğe gelen ve
        birlikten giden yazıların kaydını tutar. Gelen-giden evrak defteri yönetim kurulunun
        tutmakla sorumlu olduğu defterlerdendir (md. 23/1-c); yazışmaları sekreter yürütür (md.
        13/4). Program <strong>gelen-giden evrak defterinin yerine geçmez</strong>: deftere
        geçirilecek kaydı tutar, numarayı verir ve tekrarını önler.
      </p>
      <p>
        Ekranı her hesap okur; kayıtları program yöneticisi ve yönetim kurulu rolleri girer, okul
        müdürü ve Denetleme Kurulu okur.
        {!yazabilir && <> Bir kayıtta yanlış görürseniz program yöneticisine başvurun.</>}
      </p>

      <AltBaslik>Defter</AltBaslik>
      <Mevzuat kaynak="Yönetmelik md. 23/2">
        Yönetim kurulunca, yönetim kurulu karar defterinin noterce tasdik edilmesi zorunlu olup
        diğer defter ve belgeler ise birliğin bağlı bulunduğu il/ilçe millî eğitim müdürlüğünce
        tasdik edilir.
      </Mevzuat>
      {yazabilir ? (
        <p>
          Defter kaydedilmemişse ekranda “{DEFTER_YOK}” yazar. “{DUGME_DEFTER}” düğmesiyle defterin
          tasdik bilgisini girin; <strong>{ALAN_TASDIK_MAKAMI}</strong> seçenekleri:{" "}
          {Object.values(TASDIK_MAKAMI_TR).join(" · ")}. {DEFTER_ACIKLAMASI} Bu sayı{" "}
          <strong>{ALAN_SON_NO}</strong> alanına girilir. Defter dolunca yenisi aynı düğmeyle
          kaydedilir; birden çok defter varsa listenin üstünden seçilir.
        </p>
      ) : (
        <p>
          Defteri program yöneticisi ya da yönetim kurulu rolleri tasdik bilgisiyle kaydeder;
          kayıtlar bu deftere numaralanır.
        </p>
      )}

      <AltBaslik>Kayıtlar</AltBaslik>
      <p>
        Liste <strong>{ALAN_YIL}</strong> ve <strong>{ALAN_YON}</strong> ({YON_TR.GELEN} ya da{" "}
        {YON_TR.GIDEN}) ile süzülür. Kayıt numarası her yıl birden başlar; ekranda “{SIRADAKI_NO}”
        yazar. Satıra basınca kaydın ayrıntısı ve ekleri açılır.
      </p>
      {yazabilir && (
        <ol className="list-decimal space-y-1 pl-5">
          <li>“{DUGME_YENI_KAYIT}” düğmesine basın.</li>
          <li>
            Yönü, tarihi, <strong>{ALAN_KARSI_TARAF}</strong>, konuyu ve varsa{" "}
            <strong>{ALAN_DIS_SAYI}</strong> alanını girin. {KAYIT_ACIKLAMASI}
          </li>
          <li>
            Sıra atlanırsa “{GEREKCE_BASLIGI}” kutusu açılır; gerekçeyle kaydedilir. Kullanılmış
            numarayla kayıt hiç yapılmaz.
          </li>
          <li>Kaydın penceresinden taranmış evrak eklenir: {KAYIT_EKI_YARDIMI}</li>
        </ol>
      )}

      <AltBaslik>Programın hazırladığı yazılar</AltBaslik>
      <p>
        Okul müdürünün genel kurul yazısı program tarafından giden evrak olarak kaydedilir.
        Programın hazırladığı resmî yazı (hesapların ibra edilmediğini bildiren yazı) kendiliğinden
        kaydedilmez: {GENEL_KURUL_BASLIGI} ekranındaki belge kartında “{DUGME_EVRAK_KAYDI}”
        düğmesiyle kaydedilir. {EVRAK_KAYDI_ACIKLAMASI} Bu kayıtların ayrıntısında “
        {PROGRAMIN_YAZISI}” yazar (<Ekran to="/kilavuz#genel-kurul">Genel Kurul</Ekran>).
      </p>
      <Ipucu>
        Kaydı programa girdikten sonra tasdikli gelen-giden evrak defterine de aynı numarayla yazın;
        program defterin yerine geçmez.
      </Ipucu>
    </KilavuzBolumu>
  );
}
