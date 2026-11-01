"""Kurtarma anahtarı belgesi — PDF.

Programın kendi güvenlik belgesidir; birlik evrakı değildir, katalog dışıdır ve
E-kodu almaz (tasarım §9.7 "program belgeleri", §12.B). Saklama yeri okul
müdürlüğünde kapalı zarftır, veliye geçmez (kullanıcı kararı D3; T1).

Kurulum sihirbazının ilk adımında kullanıcı kurtarma anahtarını yazdırır, PDF
olarak kaydeder (USB bellek) ya da elle yazar; sihirbaz, anahtarın saklandığı
doğrulanmadan tamamlanmaz (`app_password.confirm_recovery_key`). Bu modül PDF
yolunu üretir:

1. Anahtar ÖNCE doğrulanır (`app_password.verify_recovery_key`): kurtarma
   sarmalını gerçekten açmayan anahtar basılmaz — yanlış yazılmış bir anahtarın
   kâğıda geçip zarfta "güvende" sanılması, parolanın unutulduğu gün veri
   kaybı demekti. Yanlış denemede kademeli gecikme uygulanır.
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

#: Belgenin görünen adı; indirilen dosyanın adı buradan kurulur (ön yüz
#: `kurtarma.ts` aynı adı kurar). Katalog kodu yoktur (tasarım §9.7; sözlük §2).
DOCUMENT_NAME = "Kurtarma Anahtarı Çıktısı"

TEMPLATE_NAME = "documents/kurtarma_anahtari.html"


def recovery_key_pdf_filename(today: date | None = None) -> str:
    """İndirme adı: 'Kurtarma-Anahtarı-Çıktısı_22.09.2026.pdf' (yerel tarih, UTC değil).

    Ad anahtarın hiçbir parçasını taşımaz (dosya adları klasör listelerinde,
    son kullanılanlar menüsünde ve günlüklerde görünür).
    """
    gun = today or timezone.localdate()
    return f"{DOCUMENT_NAME.replace(' ', '-')}_{gun:%d.%m.%Y}.pdf"


# Django hata raporlarında (DEBUG sayfası, e-posta raporlayıcı) yerel değişkenler
# basılır; anahtarı ve onu taşıyan bağlam/HTML gizlenir.
@sensitive_variables("recovery_key", "gruplar", "context")
def render_recovery_key_pdf(recovery_key: str) -> bytes:
    """Anahtarı doğrular ve belgenin PDF'ini üretir; yanlışsa `AppPasswordError` (400)."""
    gruplar = app_password.verify_recovery_key(recovery_key)
    config = SchoolConfig.load()
    context = {
        **letterhead_context(
            school_name=config.school_name,
            district=config.district,
            principal_name=config.principal_name,
        ),
        "document_title": "KURTARMA ANAHTARI",
        "issued_on": f"{timezone.localdate():%d.%m.%Y}",
        "asset_no": config.demirbas_no.strip(),
        # Gruplar numaralı basılır: sihirbazın doğrulama adımı ("2. ve 6. grubu
        # yazın") ve elle yazım bu numaralara göre yapılır.
        "key_groups": [
            {"no": sira, "chars": list(grup)} for sira, grup in enumerate(gruplar, start=1)
        ],
    }
    return html_to_pdf(render_to_string(TEMPLATE_NAME, context))
