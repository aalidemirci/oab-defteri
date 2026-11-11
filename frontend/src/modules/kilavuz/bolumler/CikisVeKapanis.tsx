// Kılavuz bölümü: Çıkış ve Kapanış (çapa `cikis-ve-kapanis`). Başlık, ikon ve sıra
// `KilavuzPage`'dedir. Kaynak: `cikis/CikisDugmesi.tsx`, `cikis/KapanisPenceresi.tsx`, sözlük §1
// "Kilit ve çıkış" ve §4.2, tasarım §4.2 "Kapanış — tek yol" (uzun iş, en çok 60 sn, kaydedilmemiş
// form) ve §4.5 "Çarpı".

import { KAPANIS_BEKLENIYOR_METNI, PROGRAM_KAPANIYOR_BASLIGI } from "../../cikis/metinler";
import { SIFRELI_YEDEK_YAZILDI } from "../../guvenlik/metinler";
import { YENIDEN_BASLAT_BASLIGI } from "../../guvenlik/YenidenBaslatEkrani";
import { KILITLE_KISAYOLU } from "../../oturum/useKilitle";
import { SON_OTURUM_KARTI_BASLIGI } from "../../pano/SonOturumKarti";
import { AltBaslik, Ekran, Ipucu, KilavuzBolumu, Tus } from "../KilavuzKabugu";
import type { BolumProps } from "../KilavuzKabugu";

export default function CikisVeKapanis(bolum: BolumProps) {
  return (
    <KilavuzBolumu {...bolum}>
      <AltBaslik>Programı kapatmak</AltBaslik>
      <p>
        Üst çubuktaki <strong>Çık</strong> düğmesine basın; “Programdan çıkılsın mı?” sorusunu “Çık”
        ile onaylayın. Parola sorulmaz, kilit ekranında da böyledir. Pencerenin çarpısı da programı
        aynı biçimde kapatır, ama soru sormaz. Program kapanınca arka planda açık kalmaz.
      </p>
      <Ipucu>
        Kapatmadan önce açık formu kaydedin: kapanış, kaydetmediğiniz alanları saklamaz. Oturum
        açıksa program kapanırken kilitlenir; yeniden açtığınızda kilit ekranından parolanızla
        girersiniz.
      </Ipucu>

      <AltBaslik>Masadan kısa süre kalkarken</AltBaslik>
      <p>
        Programı kapatmanız gerekmez: <strong>Kilitle</strong> düğmesi ya da{" "}
        <Tus>{KILITLE_KISAYOLU}</Tus> programı açık bırakır, kayıtları kilitler. Ayrıntısı{" "}
        <Ekran to="/kilavuz#hesaplar-ve-oturum">Hesaplar ve Oturum</Ekran> bölümündedir.
      </p>

      <AltBaslik>Uzun bir iş sürerken kapatırsanız</AltBaslik>
      <p>
        Şifreli yedeğin kaydı ya da yedekten geri yükleme gibi uzun bir iş sürerken Çık, çarpı ya da
        Windows oturumunun kapatılması programı hemen kapatmaz. “{PROGRAM_KAPANIYOR_BASLIGI}”
        penceresi “{KAPANIS_BEKLENIYOR_METNI}” der; bu pencere kapatılamaz. Kapanış en çok 60 saniye
        ertelenir. İş bu sürede biterse program kendisi kapanır, beklemek yeter. İş o sürede
        bitmezse program yine kapanır ve iş yarım kalabilir. Şifreli yedek birkaç dakika sürebildiği
        için bu iş sürerken programı kapatmayın. Yedek bitmeden kapandıysa programı yeniden açıp
        şifreli yedeği yeniden kaydedin ve kartta “{SIFRELI_YEDEK_YAZILDI}” yazısını görün.
      </p>

      <AltBaslik>Program düzgün kapanmadıysa</AltBaslik>
      <p>
        Elektrik kesilirse, program zorla kapatılırsa ya da uzun bir iş 60 saniyede bitmezse bir
        sonraki açılışta <Ekran to="/kilavuz#genel-bakis">Genel Bakış</Ekran> bölümünde anlatılan{" "}
        <strong>{SON_OTURUM_KARTI_BASLIGI}</strong> kartı çıkar. Kapanmadan hemen önce girdiğiniz
        kayıtlara bakın, yerinde olmayanı yeniden girin.
      </p>

      <AltBaslik>“{YENIDEN_BASLAT_BASLIGI}” ekranı</AltBaslik>
      <p>
        <Ekran to="/kilavuz#yedek-ve-geri-yukleme">Yedekten geri yüklemenin</Ekran> ardından
        programın yeniden açılması gerekir. Bu ekranda “Programdan çık” düğmesine basın, sonra
        programı yeniden açın.
      </p>
    </KilavuzBolumu>
  );
}
