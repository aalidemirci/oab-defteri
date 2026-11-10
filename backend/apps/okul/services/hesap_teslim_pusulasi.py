"""Hesap teslim pusulası (E63) — içerik modeli (plan F1b-2 "E63 hesap teslim pusulası").

Tasarım §4.4.5 (hesap açma), §9.1 (tek içerik, iki çizici; "Parola hiçbir belgede yoktur"), §9.5
(E63: dayanak BSG Yön. md. 9/2, 10/1-2; biçim yalnız PDF; F1b) ve §9.6 (E63: veri kaynağı, imza
bloğu, kabul örneği). Bu modül YALNIZ içeriği kurar (`shared.evrak.Belge`); ayrı şablon yoktur,
PDF evrak hattının tek kapısından çizilir (`shared.evrak.pdf_ciz`; yazı tipi bugünkü hattınki,
DejaVu Sans). Yetki, kayıt denetimi, basım izi ve dosyanın verilişi `hesaplar.teslim_pusulasi` ve
`views_hesaplar`'dadır.

BASILANLAR (planın lafzı):

* tanıtıcı, rol (sıra no'suz etiket) ve açılış tarihi (gg.aa.yyyy, Europe/Istanbul günü);
* "Bu programda sizin işiniz": rolün bugün yazabildiği matris satırları
  (`rol_izinleri.etkin_hucreler`; ikinci bir matris doğmaz), satırların BUGÜNKÜ işleri
  `BUGUNKU_ISLER`'dedir (orkestratör maddesi F-4): yalnız bugün programda yapılabilen işler yazılır,
  her parça onu yapan uçlara bağlıdır, sonraki fazların işleri o fazlarla eklenir;
* ilk giriş adımları (geçici parolayla giriş → parolayı yenileme; kilit ekranının metinleriyle);
* parola kuralları (BSG Yön. md. 9/2-a, b, ç); yönergenin adı ilk atıfta açık yazılır, kısaltma
  ardından parantez içindedir (sözlük §3 "Kısaltma", RYUE md. 16/11; dipnotta değil);
* kilitleme: boşta kilit (md. 10/2), "Kilitle" (md. 7/4), hatalı denemede artan bekleme ve 10.
  hatada askı, askıyı program yöneticisi kaldırır (md. 7/3, 9/2-c; programa kıyasen). Program
  yöneticisi hesabı askıya alınmaz (`app_password` "HATALI DENEME"): onun pusulası bunu söyler;
* "İlk parolanız ayrı kapalı zarftadır…" cümlesi (md. 9/2-e, 10/1);
* dipnotlar (`shared.evrak.Dipnot`), imza bloklarından sonra: program kullanıcısının aydınlatma
  metni (KVKK md. 10/1; tasarım §3.4; plan "F1b-6 uygulama kararları"; veri sorumlusu okul kartındaki
  bilgidir, `data_controller_text`, boşsa yerini söyler) ve kişisel veri dipnotu (tasarım §9.1-5).

ATIFLARIN DOĞRULAMASI (altın kural 1; `docs/mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md`):
9/2-a "en az 8 karakter", 9/2-b "küçük harf, büyük harf, rakam ve simgelerin kullanıldığı karışık
yapı", 9/2-ç "en geç altı ayda bir değiştirilir", 9/2-e "herhangi bir kişi ile paylaşılmaz", 10/1
"herkes tarafından görülebilecek yerlere yazılmaz" doğrudan uygulamalara da bağlanır (md. 9/1:
"her türlü uygulama"; md. 10/1: "sistemlerde kullanılan şifreler"). 10/2 personelin bilgisayarının
kendiliğinden kilitlenmesini, 7/4 bilgisayar başından ayrılırken oturumun kilitlenmesini, 7/3 ve
9/2-c Bakanlık hesaplarının hatalı denemede geçersiz kılınmasını ve üst yetkilinin yeniden etkin
kılmasını düzenler: dördü programa KIYASEN anılır. "Artan bekleme", 180 günlük yenileme isteği ve
baştaki/sondaki boşluk yasağı programın kendi kurallarıdır, atıf almaz.

BASILMAYANLAR: ad-soyad (hesap sahibinin de basanın da; veri kaynağı yalnız tanıtıcı, rol, açılış
tarihi ve okul kartının anteti, boşta kilit süresi ve veri sorumlusu bilgisidir); parola alanı (ne değer ne boş satır);
RYUE unsurları (sayı, konu, muhatap) ve konum cümlesi. "Teslim eden" ve "Teslim alan" imza blokları
elle doldurulur. Antet okulundur (birlik satırı yoktur).

Bütün sabit metinler sözlüğe girer (sözlük §1 "Hesap teslim pusulası (F1b)"; testi
`test_evrak_kurallari.py`). Değişken yerler (`<tanıtıcı>`, `N`) sözlükte yer tutucuyla yazılır.
İndirme adı rol etiketini taşır, tanıtıcıyı ve adı taşımaz (`dosya_adi`; orkestratör maddesi F-2).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

from django.utils import timezone

from apps.okul.models import AccountRole
from apps.okul.oturum import rol_etiketi
from apps.okul.rol_izinleri import Satir, etkin_hucreler, yazabildigi_uclar
from shared import evrak
from shared.letterhead import letterhead_authority, letterhead_unit
from shared.text import tr_upper

#: Evrak kataloğu kodu (tasarım §9.5). Yalnız altlıkta görünür (sözlük §2 istisna 1).
KOD: Final = "E63"
#: Belgenin adı (sözlük §2 "Belge adları"): başlık `tr_upper` ile büyür, dosya adı buradan kurulur.
BELGE_ADI: Final = "Hesap teslim pusulası"

#: Künye tablosunun başlıkları (tek satır: tanıtıcı, rol etiketi, açılış tarihi).
KUNYE_BASLIKLARI: Final = ("Tanıtıcı", "Rol", "Açılış tarihi")
#: "Bu programda sizin işiniz" tablosunun başlığı (satırları `isler`).
IS_BASLIGI: Final = "Bu programda sizin işiniz"

# Bölüm paragrafları: "<başlık>: " + cümleler (iki noktadan sonra cümle büyük harfle başlar). Sayfa
# bütçesi (program yöneticisinde en çok iki, öteki rollerde bir sayfa; kullanıcı kararı 04.11.2026;
# `test_evrak_kurallari.py`) bölümlerin tablo yerine paragraf olmasını ister.
ILK_GIRIS_BASLIGI: Final = "İlk girişte"
#: İlk giriş adımları (kilit ekranının metinleriyle: "Parola", "Aç", "Yeni parola", "Parola
#: (tekrar)", "Parolayı yenile ve aç"; sözlük §1 "Parola"). `{tanitici}` hesabın tanıtıcısıdır.
ILK_GIRIS_ADIMLARI: Final = (
    "(1) OAB Defteri'ni açın; kilit ekranında tanıtıcısı “{tanitici}” olan hesabı seçin.",
    "(2) Kapalı zarftaki geçici parolayı “Parola” alanına yazıp “Aç” düğmesine basın.",
    "(3) Program yeni parola ister: kendi belirlediğiniz parolayı “Yeni parola” ve “Parola "
    "(tekrar)” alanlarına yazıp “Parolayı yenile ve aç” düğmesine basın.",
    "(4) Bundan sonra programı yalnız kendi parolanızla açarsınız; geçici parola artık geçmez.",
)
PAROLA_BASLIGI: Final = "Parola kuralları"
#: Kısaltma ilk geçtiği yerde açık biçimiyle, ardından parantez içinde yazılır (sözlük §3
#: "Kısaltma", RYUE md. 16/11): "BSG Yön." pusulada ilk kez burada geçer.
PAROLA_KURALLARI: Final = (
    "Parolanız en az 8 karakterdir; küçük harf, büyük harf, rakam ve simge içerir; başında ve "
    "sonunda boşluk olamaz.",
    "İlk iki kural Millî Eğitim Bakanlığı Bilgi ve Sistem Güvenliği Yönergesinin (BSG Yön.) "
    "md. 9/2-a ve 9/2-b bentlerindedir.",
    "Parolanızı en geç altı ayda bir değiştirirsiniz (BSG Yön. md. 9/2-ç); 180 gün dolunca "
    "program yeni parolanızı ister.",
)
KILIT_BASLIGI: Final = "Kilitleme"
#: Boşta kilit cümlesi; `{dakika}` okulun boşta kilit süresidir (Ayarlar → Güvenlik; TK14).
BOSTA_KILIT: Final = (
    "Program {dakika} dakika işlem yapılmazsa kendiliğinden kilitlenir; yeniden açmak için "
    "parolanız sorulur (BSG Yön. md. 10/2; programa kıyasen)."
)
KILITLE: Final = (
    "Bilgisayarın başından ayrılırken “Kilitle” düğmesine basın (BSG Yön. md. 7/4; programa "
    "kıyasen)."
)
ARTAN_BEKLEME: Final = "Parola üst üste yanlış girildikçe bekleme süresi artar."
#: Program yöneticisi DIŞINDAKİ hesaplarda 10. hatalı denemede askı (`app_password`
#: `SUSPEND_AFTER_FAILURES`; tasarım §15 M-12).
HATALI_DENEME_ASKISI: Final = (
    "Üst üste 10. yanlış denemede hesap askıya alınır; askıyı program yöneticisi kaldırır "
    "(BSG Yön. md. 7/3, 9/2-c; programa kıyasen)."
)
#: Program yöneticisi hesabında askı yoktur (kendi kendine hizmet reddi olurdu; `app_password`
#: "HATALI DENEME").
YONETICI_ASKI_YOK: Final = "Program yöneticisi hesabı yanlış denemede askıya alınmaz."
#: Tasarım §9.6'nın kabul örneğindeki cümle (BİREBİR) ve atfı.
KAPALI_ZARF: Final = (
    "İlk parolanız ayrı kapalı zarftadır; parolanızı kimseyle paylaşmayın, görünür yere "
    "yazmayın (BSG Yön. md. 9/2-e, 10/1)."
)
#: İmza blokları (tasarım §9.6: "Teslim eden: yönetici; Teslim alan: hesap sahibi (ad, imza,
#: tarih)"); ad-soyad basılmaz, elle yazılır.
TESLIM_EDEN: Final = ("Teslim eden", "Program yöneticisi (ad-soyad, imza, tarih)")
TESLIM_ALAN: Final = ("Teslim alan", "Hesap sahibi (ad-soyad, imza, tarih)")

# Program kullanıcısının aydınlatma metni (KVKK md. 10/1; tasarım §3.4; plan "F1b-6 uygulama
# kararları"). Kullanıcının 09.11.2026'da onayladığı metindir, BİREBİR: tek harf değiştirilmez. Ön
# yüzdeki karşılığı `kisiler/metinler.ts`'tedir; birebirliği
# `test_on_yuz_sozlugu.test_hesap_aydinlatmasi_onayli_metindir` sınar.
AYDINLATMA_BASLIGI: Final = "Kişisel veri aydınlatma metni"
AYDINLATMA_VERI_SORUMLUSU_ETIKETI: Final = "Veri sorumlusu:"
#: Okul kartındaki veri sorumlusu bilgisi boşken "Veri sorumlusu:" satırının değeri (sihirbazdaki gibi).
AYDINLATMA_VERI_SORUMLUSU_YERI: Final = "Okul Bilgileri'nde girilir"
#: "Veri sorumlusu:" satırından sonraki satırlar, sırasıyla.
AYDINLATMA_SATIRLARI: Final = (
    "Amaç: Programı kullanan hesabın açılması, role göre yetkilendirme ve yapılan işlemlerin kayda "
    "geçmesi. Hesabın ad-soyadı, tanıtıcısı ve rolü, giriş ve parola işlemleri, kişisel veri içeren "
    "kayıtların hangi hesapla okunduğu tutulur.",
    "Aktarım: Kişisel veriler kimseye aktarılmaz; program okulun bilgisayarında çalışır, dışarıya "
    "veri göndermez.",
    "Toplama yöntemi ve hukuki sebep: Ad-soyad, hesabı açan program yöneticisince girilir; işlemler "
    "program tarafından elektronik ortamda kaydedilir. Hukuki sebep: veri sorumlusunun hukuki "
    "yükümlülüğünü yerine getirmesi (KVKK md. 5/2-ç), güvenlik tedbiri (KVKK md. 12/1).",
    "Saklama: Hesap kapatılsa da hesap kaydı ve işlem izi silinmez; kişisel veri okuma günlüğünün "
    "satırları iki yıl sonra silinir.",
    "Haklarınız: KVKK md. 11'deki haklarınızı veri sorumlusuna başvurarak kullanabilirsiniz.",
)
#: Onaylı metnin ekran notu; etiketsiz, metnin son paragrafı olarak basılır.
AYDINLATMA_NOTU: Final = (
    "Hukuki sebep öneridir; veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir."
)


@dataclass(frozen=True)
class IsParcasi:
    """Bugünkü işin bir parçası ("kapama", "ders yılı ve dönemler") ve onu bugün yapan uçlar.

    `uclar` Django URL adlarıdır (`rol_izinleri.KURALLAR`'ın `uc`'u): her biri satırın, pusulası
    basılan rolün yazabildiği bir yazma kuralıdır (test). Ad, ucu ya da ekranı olmayan bir işi
    söyleyemez.
    """

    ad: str
    uclar: frozenset[str]


def _parca(ad: str, *uclar: str) -> IsParcasi:
    return IsParcasi(ad, frozenset(uclar))


@dataclass(frozen=True)
class BugunkuIs:
    """Bir matris satırının BUGÜN programda yapılabilen işi (orkestratör maddesi F-4).

    Ad `baslik` + ": " + parçalardır (başlık yoksa yalnız parçalar); iki noktadan sonrası liste
    olduğu için küçük harfle sürer. Pusulada rolün adı yalnız o rolün yazabildiği parçaları taşır
    (`rol_parcalari`; F1c 4. adım: M2'de personel işleri yalnız program yöneticisinin, birlik
    kişileri yönetim kurulu rollerinin de işidir). `ad` bütün parçalardır.
    """

    parcalar: tuple[IsParcasi, ...]
    baslik: str = ""

    def _ad(self, parcalar: tuple[IsParcasi, ...]) -> str:
        govde = ", ".join(parca.ad for parca in parcalar)
        return f"{self.baslik}: {govde}" if self.baslik else govde

    @property
    def ad(self) -> str:
        return self._ad(self.parcalar)

    def rol_parcalari(self, rol: str) -> tuple[IsParcasi, ...]:
        """Rolün bütün uçlarını yazabildiği parçalar (kurallardan türer; ikinci bir matris doğmaz)."""
        yazilabilir = yazabildigi_uclar(rol)
        return tuple(parca for parca in self.parcalar if parca.uclar <= yazilabilir)

    def rol_adi(self, rol: str) -> str:
        """Rolün pusulasındaki ad: yalnız o rolün parçalarıyla."""
        return self._ad(self.rol_parcalari(rol))


#: Rolün bugün yazabildiği matris satırlarının pusuladaki işleri (orkestratör maddesi F-4): YALNIZ
#: bugün programda yapılabilen işler yazılır, sonraki fazların işleri yazılmaz ("birlik döneminin
#: açılması" F1c, "hesap geçişi" ve "kayıtların anahtarının yenilenmesi" F4, takvim ve uyum kaydı
#: F2 …). Hangi satırların basılacağını `rol_izinleri.etkin_hucreler` söyler (tek yüklem; ikinci
#: bir matris doğmaz); burası yalnız satırın bugünkü ADINI ve adın parçalarını yapan uçları tutar.
#: FAZLARLA BÜYÜR: bir faz bir hücreyi bekleyenden çıkarınca ya da etkin bir satıra yeni bir yazma
#: ucu ekleyince işin adı ve parçası buraya eklenir — testler (`test_evrak_kurallari.py`) her etkin
#: satırın adını, her parçanın var olan bir uca karşılık geldiğini ve satırın her yazma ucunun bir
#: parçada adlandığını (ya da `ADSIZ_UCLAR`'da gerekçesiyle durduğunu) sınar. Adlar sözlüğe uyar
#: (sözlük §1 "Hesap teslim pusulası (F1b)"): kodsuz, kısaltmasız; ekran, kart ve düğme adları
#: sözlükteki gibidir.
BUGUNKU_ISLER: Final[Mapping[Satir, BugunkuIs]] = {
    Satir.M1: BugunkuIs(
        (
            _parca("Okul bilgileri", "setup-school-config"),
            _parca(
                "ders yılı ve dönemler",
                "school-year-list",
                "school-year-terms",
                "school-year-activate",
            ),
            _parca("kapalı günler", "holiday-list", "holiday-seed", "holiday-detail"),
        )
    ),
    Satir.M2: BugunkuIs(
        (
            _parca(
                "öğretmen ve diğer personel kaydı",
                "personnel-list",
                "personnel-detail",
                "personnel-leave",
                "personnel-merge",
            ),
            _parca("e-Okul aktarımı", "import-personnel-preview", "import-personnel-commit"),
            _parca("ayrılış havuzu", "leave-pool-resolve"),
            # Birlik kişileri (F1c 4. adım): program yöneticisi ve yönetim kurulu rolleri. Ekranı
            # Kişiler'in "Birlik Kişileri" sekmesidir (F1c 11. adım).
            _parca(
                "birlik kişileri",
                "oab-person-list",
                "oab-person-detail",
                "oab-person-from-personnel",
            ),
            # Veli listesinden kopya yalnız program yöneticisinindir (`rol_izinleri`).
            _parca("veli listesinden birlik kişisi ekleme", "oab-person-from-parent"),
        ),
        baslik="Kişiler",
    ),
    Satir.M8: BugunkuIs(
        (
            _parca(
                "yedekten geri yükleme kartını görüldü olarak işaretleme (“Gördüm”)",
                "security-integrity-restore-seen",
            ),
        ),
        baslik="Genel Bakış",
    ),
    Satir.M9: BugunkuIs(
        (_parca("son oturumun kontrolü (“Kontrol ettim”)", "dashboard-last-session"),),
        baslik="Genel Bakış",
    ),
    Satir.KULLANICILAR: BugunkuIs(
        (
            _parca("hesap açma", "account-list"),
            _parca("kapama", "account-close"),
            _parca("askıdan çıkarma", "account-unsuspend"),
            _parca("parola sıfırlama", "account-reset-password"),
            _parca("hesap teslim pusulası", "account-handover-slip"),
        ),
        baslik="Kullanıcılar",
    ),
    Satir.GUVENLIK: BugunkuIs(
        (
            _parca(
                "kurtarma anahtarı",
                "security-recovery-key-pdf",
                "security-recovery-key-confirm",
                "security-recovery-key-renew",
            ),
            _parca("şifreli yedek", "encrypted-backup-download", "backup-external-reminder"),
            _parca("yedekten geri yükleme", "backup-restore", "backup-inspect"),
            _parca("yedek raporu", "backup-report"),
            # Genel Bakış'ın "Hesaplar ve Güvenlik Dosyası" kartındaki liste ve "Güvenlik dosyasından
            # sil" düğmesi (sözlük §4.5): ad kartın alt başlığıdır.
            _parca(
                "Genel Bakış'ta güvenlik dosyasında kalan eski parola kayıtlarının silinmesi",
                "security-integrity-orphan-wraps",
            ),
        ),
        baslik="Güvenlik",
    ),
    Satir.AYARLAR: BugunkuIs(
        (_parca("boşta kilit süresi", "security-idle-lock"),), baslik="Ayarlar"
    ),
    Satir.KISISEL_VERI: BugunkuIs(
        (
            _parca(
                "veli listesinin aktarımı ve silinmesi",
                "import-parents-preview",
                "import-parents-commit",
                "parent-roster",
            ),
        ),
        baslik="Kişiler",
    ),
    Satir.GUNCELLEME: BugunkuIs(
        (_parca("Güncelleme denetimi", "update-latest", "update-installer"),)
    ),
    Satir.KENDI: BugunkuIs(
        (
            _parca("Kendi parolanızı değiştirme", "security-change-password"),
            _parca("Kilitle", "security-lock"),
            _parca("Çık", "app-quit"),
        )
    ),
}

#: Etkin satırlarda bilerek ADLANMAYAN yazma uçları ve gerekçeleri (orkestratör maddesi F-4; test
#: bunları satırın kapsamından düşer). Liste yalnız gerekçeyle büyür.
ADSIZ_UCLAR: Final[Mapping[str, str]] = {
    "oab-term-list": (
        "Birlik döneminin ekranı F1c'nin 11. adımındadır; pusula yalnız bugün programda yapılabilen "
        "işleri yazar, ekran gelince bu kayıt `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-list": (
        "Organlar ekranı F1c'nin 11. adımındadır; pusula yalnız bugün programda yapılabilen işleri "
        "yazar, ekran gelince organ üyelikleri `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-detail": (
        "Organlar ekranı F1c'nin 11. adımındadır; pusula yalnız bugün programda yapılabilen işleri "
        "yazar, ekran gelince organ üyelikleri `BUGUNKU_ISLER`'e geçer."
    ),
    # F1c 6. adım: görev bölümü, yedek çağrısı, düşme, iptal, görev alma engeli, temsilciler ve alım
    # komisyonu uçları ekransızdır (Organlar ve Temsilciler ekranları 11. adımda).
    "oab-yk-duty-assignment": (
        "Yönetim kurulunun görev bölümü Organlar ekranındadır (F1c 11. adım); ekran gelince "
        "`BUGUNKU_ISLER`'e geçer."
    ),
    "oab-dk-duty-assignment": (
        "Denetleme Kurulunun görev bölümü Organlar → Denetleme Kurulu'ndadır (F1c 11. adım); ekran "
        "gelince `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-substitute-call-yk": (
        "Yedek çağrısı Organlar ekranındadır (F1c 11. adım); ekran gelince `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-substitute-call-dk": (
        "Yedek çağrısı Organlar ekranındadır (F1c 11. adım); ekran gelince `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-drop": (
        "Üyeliğin düşmesi Organlar ekranındadır (F1c 11. adım); ekran gelince `BUGUNKU_ISLER`'e "
        "geçer."
    ),
    "oab-membership-cancel": (
        "Yanlış üyelik kaydının iptali Organlar ekranındadır (F1c 11. adım); ekran gelince "
        "`BUGUNKU_ISLER`'e geçer."
    ),
    "oab-membership-eligibility-basis": (
        "Görev alma engeli Organlar ekranındadır (F1c 11. adım); ekran gelince `BUGUNKU_ISLER`'e "
        "geçer."
    ),
    "oab-representative-list": (
        "Temsilciler ekranı F1c'nin 11. adımındadır; ekran gelince `BUGUNKU_ISLER`'e geçer."
    ),
    "oab-purchase-committee-list": (
        "Alım komisyonu Organlar ekranının sekmesidir (F1c 11. adım); ekran gelince "
        "`BUGUNKU_ISLER`'e geçer."
    ),
    "setup-complete": (
        "Kurulum Sihirbazı'nın son adımı; pusula kurulumdan sonra basılır, hesap sahibinin işi değildir."
    ),
    "setup-roadmap": (
        "Genel Bakış'taki Başlangıç Yol Haritası işaretleri; okul bilgileri işinin yan ürünüdür."
    ),
    "security-state-reset": (
        "Güvenlik dosyası kayıp ekranındaki sıfırlama; yalnız hiç hesap ve şifreli kayıt yokken "
        "açıktır, açık oturumda 409 döner; hesap sahibinin işi değildir."
    ),
    "security-integrity-reset-notice": (
        "Kendi parola yenilenme bildiriminin “Gördüm”ü; bildirim kendiliğinden açılır, ayrı iş "
        "değildir."
    ),
}


def isler(rol: str) -> tuple[str, ...]:
    """Rolün "bu programda sizin işiniz" satırları: `etkin_hucreler` sırasıyla, bugünkü adlarıyla
    (`BUGUNKU_ISLER`; yalnız rolün parçaları). Etkin satırın adı yoksa `KeyError` (test her etkin
    satırın adını sınar)."""
    return tuple(BUGUNKU_ISLER[satir].rol_adi(rol) for satir in etkin_hucreler(rol))


def _gun(an: datetime) -> str:
    """Anın Europe/Istanbul günü, gg.aa.yyyy."""
    return f"{timezone.localtime(an):%d.%m.%Y}"


def _bolum(baslik: str, cumleler: tuple[str, ...] | list[str]) -> str:
    """Bölüm paragrafı: "<başlık>: " + cümleler."""
    return f"{baslik}: " + " ".join(cumleler)


def _aydinlatma(veri_sorumlusu: str) -> tuple[evrak.Dipnot, ...]:
    """Aydınlatma bölümü; `veri_sorumlusu` okul kartındaki bilgidir (`data_controller_text`).

    Dipnot puntosuyla, imza bloklarından sonra durur: gövde puntosunda tek sayfa bütçesini aşar.
    """
    deger = veri_sorumlusu.strip() or AYDINLATMA_VERI_SORUMLUSU_YERI
    return tuple(
        evrak.Dipnot(metin)
        for metin in (
            AYDINLATMA_BASLIGI,
            f"{AYDINLATMA_VERI_SORUMLUSU_ETIKETI} {deger}",
            *AYDINLATMA_SATIRLARI,
            AYDINLATMA_NOTU,
        )
    )


def pusula_belgesi(
    *,
    tanitici: str,
    rol: str,
    acilis: datetime,
    okul_adi: str,
    ilce: str | None,
    bosta_dakika: int,
    veri_sorumlusu: str,
) -> evrak.Belge:
    """Pusulanın içerik modeli (modül başlığı). Girdiler kişisizdir: ad-soyad parametresi YOKTUR."""
    kilitleme = [BOSTA_KILIT.format(dakika=bosta_dakika), KILITLE, ARTAN_BEKLEME]
    kilitleme.append(YONETICI_ASKI_YOK if rol == AccountRole.YONETICI else HATALI_DENEME_ASKISI)
    adimlar = [adim.format(tanitici=tanitici) for adim in ILK_GIRIS_ADIMLARI]
    return evrak.Belge(
        kod=KOD,
        antet=evrak.Antet(
            tc="T.C.",
            authority=letterhead_authority(ilce),
            unit_line=letterhead_unit(okul_adi),
        ),
        bloklar=(
            evrak.Baslik(BELGE_ADI),
            evrak.Tablo(
                basliklar=KUNYE_BASLIKLARI,
                satirlar=((tanitici, rol_etiketi(rol), _gun(acilis)),),
            ),
            evrak.Tablo(basliklar=(IS_BASLIGI,), satirlar=tuple((is_,) for is_ in isler(rol))),
            evrak.Paragraf(_bolum(ILK_GIRIS_BASLIGI, adimlar)),
            evrak.Paragraf(_bolum(PAROLA_BASLIGI, PAROLA_KURALLARI)),
            evrak.Paragraf(_bolum(KILIT_BASLIGI, kilitleme)),
            evrak.Paragraf(KAPALI_ZARF),
            evrak.Imza(
                sahipler=(evrak.ImzaSahibi(*TESLIM_EDEN), evrak.ImzaSahibi(*TESLIM_ALAN)),
            ),
            *_aydinlatma(veri_sorumlusu),
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )


#: Dosya adında kullanılamayan karakterler (Windows'un yasakladığı dokuz karakter; ön yüzün
#: `lib/download.ts` `dosyaAdi` kuralı).
_DOSYA_ADI_YASAK = re.compile(r'[\\/:*?"<>|]')


def _dosya_parcasi(metin: str) -> str:
    """Dosya adının bir parçası (`dosyaAdi` kalıbı): yasak karakter atılır, boşluk tireye döner."""
    return re.sub(r"\s+", "-", _DOSYA_ADI_YASAK.sub("", metin).strip())


def dosya_adi(rol: str, gun: date | None = None) -> str:
    """İndirme adı: 'Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf' (yerel gün; orkestratör maddesi
    F-2). Program yöneticisinde 'Hesap-Teslim-Pusulası_Program-yöneticisi_03.11.2026.pdf'.

    Belge adı + kapsam + tarih (sözlük §3 "Kaydedilen dosya adı"): kapsam rol etiketidir (sıra
    no'suz; `oturum.rol_etiketi`) — aynı gün birkaç hesaba basılan pusulalar klasörde ayrılır. Ad
    tanıtıcıyı ve ad-soyadı TAŞIMAZ: tanıtıcıda hesap sahibinin adı ya da kimlik numarasına benzer
    bir sayı olabilir (program yalnız uyarır; `hesap_kurallari.login_name_warning`); dosya adları
    klasör listelerinde ve son kullanılanlar menüsünde görünür. Kalıp kurtarma anahtarı
    belgesininkidir (`recovery_key_document`); Türkçe harfler korunur, Content-Disposition'daki
    kodlamayı Django yapar (`filename*=utf-8''…`).
    """
    gun = gun or timezone.localdate()
    ad = "-".join(tr_upper(sozcuk[:1]) + sozcuk[1:] for sozcuk in BELGE_ADI.split())
    return f"{ad}_{_dosya_parcasi(rol_etiketi(rol))}_{gun:%d.%m.%Y}.pdf"
