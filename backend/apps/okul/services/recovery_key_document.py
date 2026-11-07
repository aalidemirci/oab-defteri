"""Kurtarma anahtarı belgesi — PDF.

Programın kendi güvenlik belgesidir; birlik evrakı değildir, katalog dışıdır ve
E-kodu almaz (tasarım §9.7 "program belgeleri", §12.B). Saklama yeri okul
müdürlüğünde kapalı zarftır, veliye geçmez (kullanıcı kararı D3; T1). Basımı iz
satırı yazmaz (plan F1b-1 "`guvenlik.json` şema 2"; birlik evrakı değildir).

Metin OAB'nindir (tasarım §13 D50, §12.B; plan F1b-1): herkes programı kendi
hesabıyla ve kendi parolasıyla açar, parola paylaşılmaz (BSG Yön. md. 7/2, 9/2-e);
anahtar yalnız program yöneticisi içindir ve üç durumda kullanılır — parolası
unutulduğunda, kayıtlar yeni bilgisayara taşınırken ve zarfın üçüncü durumunda
(`UCUNCU_DURUM`: bu bilgisayarın güvenlik dosyası ya da kayıtları kaybolduğunda,
bozulduğunda ya da program dışından değiştirildiğinde; kullanıcı kararı 02.11.2026). Üçüncü
durumun çaresi `UCUNCU_DURUMUN_CARESI`'dir: yedekten geri yükleme ya da kurtarma anahtarıyla
açılış (kullanıcı kararı 03.11.2026) — güvenlik dosyası kayıpken parola yolu işlemez (tasarım
§4.4.4), program yöneticisinin parola kaydı program dışından değiştirilmişse "Parolamı unuttum"
açar, hesap kaydı ya da denetim izi değiştirilmişse değişiklikten önceki bir yedek kurtarma
anahtarıyla geri yüklenir. Zarf yalnız bu üç durumda açılır. Üçüncü durumun sözleri belgede,
anahtar panelinin uyarısında (ön yüz `guvenlik/metinler.KURTARMA_UYARISI`), kilit ekranının
yol gösterme metninde (`KurtarmaIleAcma.UCUNCU_DURUM_YOL_METNI`) ve sözlükte BİREBİR aynıdır
(`test_kurtarma_anahtari_pdf.test_ucuncu_durum_metni_her_yerde_birebir`).

Belge anahtarın KİMLİĞİNİ de basar: anahtar no'su ve üretim tarihi (`guvenlik.json`
`kurtarma.no` ve `kurtarma.tarih`; tasarım §9.7, TK10). No her yeni anahtarda bir artar; yedek başlığı da aynı kimliği taşır, yani
kâğıt hangi yedekleri açtığını kendisi söyler ve devir-teslimde zarfın yalnız no'su
ve tarihi yazılır. Ailedeki "yönetici parolası" dili ve "parola en az iki kişide"
öğüdü yoktur. Eski kâğıt atılmaz, işaretlenip saklanır: bugünkü yenileme kayıtların
anahtarını değiştirmez, eski anahtar yenilemeden önceki yedekleri açmaya devam eder
(tasarım §4.4.6-2); zarfın imha tutanağı DEK yenilemesiyle F4'tedir.

Kurulum sihirbazının ilk adımında kullanıcı kurtarma anahtarını yazdırır, PDF
olarak kaydeder (USB bellek) ya da elle yazar; sihirbaz, anahtarın saklandığı
doğrulanmadan tamamlanmaz (`app_password.confirm_recovery_key`). Bu modül PDF
yolunu üretir:

1. Anahtar ÖNCE doğrulanır (`app_password.verify_recovery_key_identity`): kurtarma
   sarmalını gerçekten açmayan anahtar basılmaz — yanlış yazılmış bir anahtarın
   kâğıda geçip zarfta "güvende" sanılması, parolanın unutulduğu gün veri
   kaybı demekti. Yanlış denemede kademeli gecikme uygulanır. Anahtarın no'su ve
   tarihi, doğrulamanın okuduğu AYNI durumdan gelir (arada yenileme olsaydı eski
   anahtarın kâğıdına yenisinin no'su basılırdı).
2. Belge `documents/base.html` tabanıyla (resmî antet: okul adı sihirbazın bu
   adımında henüz girilmemiş olabilir, antet o zaman elle doldurulacak yer
   tutucu basar) ve TEK KAPIDAN (`shared.pdf.html_to_pdf`) basılır.

Anahtar sunucuda SAKLANMAZ: yalnız istek gövdesinde gelir, bu işlevin yerel
değişkeninde yaşar ve yanıtın PDF'ine girer. Hiçbir günlüğe, hata iletisine ya
da dosya adına yazılmaz (koruma testi `test_kurtarma_anahtari_pdf.py` caplog ile
denetler).
"""

from __future__ import annotations

from datetime import date

from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.okul.models import SchoolConfig
from apps.okul.services import app_password
from shared.letterhead import letterhead_context
from shared.pdf import html_to_pdf
from shared.text import tr_upper

#: Belgenin görünen adı — TEK SABİT: belgenin başlığı (`tr_upper` ile büyük harf;
#: şablonda text-transform yoktur) ve kaydedilen dosyanın adı (`recovery_key_pdf_filename`,
#: yanıtın Content-Disposition'ı) buradan kurulur. Ön yüz aynı adı kurar
#: (`frontend/src/modules/guvenlik/kurtarma.ts` + `lib/download.ts` `dosyaAdi`: boşluk
#: tireye döner, tarih alt çizgiyle eklenir). Ad tasarım §9.7'dedir; katalog kodu
#: yoktur (sözlük §2 "Belge adları"; cümle içinde "Kurtarma anahtarı belgesi").
DOCUMENT_NAME = "Kurtarma Anahtarı Belgesi"

TEMPLATE_NAME = "documents/kurtarma_anahtari.html"

#: Kurtarma anahtarı zarfının üçüncü durumu — kullanıcı kararı 02.11.2026'nın sözü, TEK SABİT:
#: belge şablona bunu basar (`ucuncu_durum`); ön yüzün `metinler.ZARFIN_UCUNCU_DURUMU`'su, anahtar
#: panelinin uyarısı, kilit ekranının yol gösterme metni ve sözlük aynı sözü taşır (test).
UCUNCU_DURUM = (
    "bu bilgisayarın güvenlik dosyası ya da kayıtları kaybolduğunda, bozulduğunda ya da "
    "program dışından değiştirildiğinde"
)
#: Üçüncü durumun çaresi — kullanıcı kararı 03.11.2026'nın sözü (yukarıdaki not). Şablonda
#: "çare … açılıştır" diye basılır: söz değişirse şablonun eki de gözden geçirilir.
UCUNCU_DURUMUN_CARESI = "yedekten geri yükleme ya da kurtarma anahtarıyla açılış"


def recovery_key_pdf_filename(today: date | None = None) -> str:
    """İndirme adı: 'Kurtarma-Anahtarı-Belgesi_22.09.2026.pdf' (yerel tarih, UTC değil).

    Ad anahtarın hiçbir parçasını taşımaz (dosya adları klasör listelerinde,
    son kullanılanlar menüsünde ve günlüklerde görünür). Anahtar no'su da adda
    yoktur: ad basım gününü söyler, no belgenin içindedir.
    """
    gun = today or timezone.localdate()
    return f"{DOCUMENT_NAME.replace(' ', '-')}_{gun:%d.%m.%Y}.pdf"


def _gun(iso: object) -> str:
    """ISO günü kâğıttaki biçime çevirir (gg.aa.yyyy); yoksa boş (elle doldurulacak yer)."""
    if not isinstance(iso, str) or not iso:
        return ""
    return f"{date.fromisoformat(iso):%d.%m.%Y}"


# Django hata raporlarında (DEBUG sayfası, e-posta raporlayıcı) yerel değişkenler
# basılır; anahtarı ve onu taşıyan bağlam/HTML gizlenir.
@sensitive_variables("recovery_key", "gruplar", "context")
def render_recovery_key_pdf(recovery_key: str) -> bytes:
    """Anahtarı doğrular ve belgenin PDF'ini üretir; yanlışsa `AppPasswordError` (400)."""
    gruplar, kimlik = app_password.verify_recovery_key_identity(recovery_key)
    no = (kimlik or {}).get("no")
    config = SchoolConfig.load()
    context = {
        **letterhead_context(
            school_name=config.school_name,
            district=config.district,
            principal_name=config.principal_name,
        ),
        "document_title": tr_upper(DOCUMENT_NAME),
        # Anahtarın kimliği (`kurtarma.no`, `kurtarma.tarih`; ISO gün kurala göre
        # doğrulanmıştır). Okunamazsa elle doldurulacak çizgi basılır; şema 2
        # dosyasında ikisi de vardır.
        "key_no": str(no) if no is not None else "",
        "key_date": _gun((kimlik or {}).get("tarih")),
        "asset_no": config.demirbas_no.strip(),
        # Zarfın üçüncü durumu ve çaresi (kullanıcı kararları; tek sabit, modül başlığı).
        "ucuncu_durum": UCUNCU_DURUM,
        "ucuncu_durumun_caresi": UCUNCU_DURUMUN_CARESI,
        # Gruplar numaralı basılır: sihirbazın doğrulama adımı ("2. ve 6. grubu
        # yazın") ve elle yazım bu numaralara göre yapılır.
        "key_groups": [
            {"no": sira, "chars": list(grup)} for sira, grup in enumerate(gruplar, start=1)
        ],
    }
    return html_to_pdf(render_to_string(TEMPLATE_NAME, context))
