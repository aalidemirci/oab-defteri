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
  (`rol_izinleri.etkin_hucreler`; ikinci bir matris doğmaz), satırların adları `IS_ADLARI`'ndadır
  (tasarım §4.4.2 tablosunun "Alan" sütunu, kodsuz ve kısaltmasız);
* ilk giriş adımları (geçici parolayla giriş → parolayı yenileme; kilit ekranının metinleriyle);
* parola kuralları (BSG Yön. md. 9/2-a, b, ç); yönergenin adı ilk atıfta açık yazılır, kısaltma
  ardından parantez içindedir (sözlük §3 "Kısaltma", RYUE md. 16/11; dipnotta değil);
* kilitleme: boşta kilit (md. 10/2), "Kilitle" (md. 7/4), hatalı denemede artan bekleme ve 10.
  hatada askı, askıyı program yöneticisi kaldırır (md. 7/3, 9/2-c; programa kıyasen). Program
  yöneticisi hesabı askıya alınmaz (`app_password` "HATALI DENEME"): onun pusulası bunu söyler;
* "İlk parolanız ayrı kapalı zarftadır…" cümlesi (md. 9/2-e, 10/1);
* dipnot (`shared.evrak.Dipnot`): kişisel veri dipnotu (tasarım §9.1-5).

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
tarihi ve okul kartının anteti ile boşta kilit süresidir); parola alanı (ne değer ne boş satır);
RYUE unsurları (sayı, konu, muhatap) ve konum cümlesi. "Teslim eden" ve "Teslim alan" imza blokları
elle doldurulur. Antet okulundur (birlik satırı yoktur).

Bütün sabit metinler sözlüğe girer (sözlük §1 "Hesap teslim pusulası (F1b)"; testi
`test_evrak_kurallari.py`). Değişken yerler (`<tanıtıcı>`, `N`) sözlükte yer tutucuyla yazılır.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Final

from django.utils import timezone

from apps.okul.models import AccountRole
from apps.okul.oturum import rol_etiketi
from apps.okul.rol_izinleri import Satir, etkin_hucreler
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
# bütçesi (tek sayfa; `test_evrak_kurallari.py`) bölümlerin tablo yerine paragraf olmasını ister.
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

#: Matris satırlarının pusuladaki adları (tasarım §4.4.2 tablosunun "Alan" sütunu; kodsuz,
#: kısaltmasız, sözlüğe uygun: "okul kartı" ekranda "okul bilgileri"dir, "bütçe" tahmini
#: bütçedir, "DEK yenileme" kayıtların anahtarının yenilenmesidir; ayraç içi açıklamalar düşer).
#: Program yöneticisinin satırları tek sayfaya sığsın diye birer satırdır (sayfa bütçesi).
#: `OTURUM` matriste yoktur, adı da yoktur. Satır düzeyindedir (`etkin_hucreler` satırı verir):
#: adın bir parçasının ekranı sonraki fazdaysa da satır adıyla basılır.
IS_ADLARI: Final[Mapping[Satir, str]] = {
    Satir.M1: "Okul bilgileri, ders yılı, kapalı günler, birlik döneminin açılması ve kapanması",
    Satir.M2: "Kişiler, organlar, temsilciler, yönetim kurulu görev bölümü, yedek üye çağrısı",
    Satir.M3: "Genel kurul",
    Satir.M4: "Yönetim kurulu toplantısı, katılım, karar taslağı",
    Satir.M5: "Gelir-gider kaydı, banka eşleme, makbuz koçanı ve yaprağı, kasa",
    Satir.M6: "Harcama zinciri",
    Satir.M7: "Tahmini bütçe, ilan, aylık bildirim, faaliyet raporu",
    Satir.M8: (
        "Denetim: Denetleme Kurulu görev bölümü, denetim planı, kontrol listesi, bulgu, ara ve "
        "nihai rapor, olağanüstü genel kurul çağrısı, kayıt bütünlüğü denetimi"
    ),
    Satir.MUDUR_YAZISI: "Müdür yazısı: birlik başkanına yazılı uyarı",
    Satir.M9: "Takvim, pano ve uyum kaydı",
    Satir.M10: "Gelen-giden evrak, belge dosyası",
    Satir.M11: "Devir-teslim ve dönem kapanışı",
    Satir.M13_M14: "Kantin ve servis",
    Satir.M15: "Personel",
    Satir.DENETIM_IZI: "Denetim izi",
    Satir.ERISIM_GUNLUGU: "Erişim günlüğü",
    Satir.KULLANICILAR: (
        "Kullanıcılar: hesap açma, kapama, askıdan çıkarma, parola sıfırlama, hesap geçişi"
    ),
    Satir.GUVENLIK: (
        "Güvenlik: kurtarma anahtarı, yedek indirme, geri yükleme, kayıtların anahtarının "
        "yenilenmesi"
    ),
    Satir.AYARLAR: (
        "Ayarlar: boşta kilit süresi, küçük alım sınırı, kural sürümü, bağışçı kimlik numarası"
    ),
    Satir.KISISEL_VERI: "Kişisel veri içeren çıktı ve dışa aktarım",
    Satir.GUNCELLEME: "Güncelleme denetimi",
    Satir.KENDI: "Kendi parolanızı değiştirme, Kilitle, Çık",
}


def isler(rol: str) -> tuple[str, ...]:
    """Rolün "bu programda sizin işiniz" satırları (`etkin_hucreler` sırasıyla; ad `IS_ADLARI`)."""
    return tuple(IS_ADLARI[satir] for satir in etkin_hucreler(rol))


def _gun(an: datetime) -> str:
    """Anın Europe/Istanbul günü, gg.aa.yyyy."""
    return f"{timezone.localtime(an):%d.%m.%Y}"


def _bolum(baslik: str, cumleler: tuple[str, ...] | list[str]) -> str:
    """Bölüm paragrafı: "<başlık>: " + cümleler."""
    return f"{baslik}: " + " ".join(cumleler)


def pusula_belgesi(
    *,
    tanitici: str,
    rol: str,
    acilis: datetime,
    okul_adi: str,
    ilce: str | None,
    bosta_dakika: int,
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
            evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU),
        ),
    )


def dosya_adi(gun: date | None = None) -> str:
    """İndirme adı: 'Hesap-Teslim-Pusulası_03.11.2026.pdf' (yerel gün).

    Ad tanıtıcıyı TAŞIMAZ: tanıtıcıda hesap sahibinin adı olabilir (program yalnız uyarır;
    `hesap_kurallari.login_name_warning`); dosya adları klasör listelerinde ve son kullanılanlar
    menüsünde görünür. Kalıp kurtarma anahtarı belgesininkidir (`recovery_key_document`).
    """
    gun = gun or timezone.localdate()
    ad = "-".join(tr_upper(sozcuk[:1]) + sozcuk[1:] for sozcuk in BELGE_ADI.split())
    return f"{ad}_{gun:%d.%m.%Y}.pdf"
