"""Dönem kilidi (tasarım §5 O2) ve kural kopyasının bütünlüğü (§6.3 D7).

`term` taşıyan kayıt dönemi `KAPANDI` ise yazılamaz (sert). Beyaz liste yalnız işaret alanları, yeniden
basım ve işaretin kapattığı `EKSIK` satırıdır; bu yazmalar `KAPALI_DONEM` etiketiyle izlenir. `HAZIRLIK`
dönemine yalnız genel kurul hazırlığı yazılır. Dönemin kural kopyası özetini tutmuyorsa dönem salt
okur açılır: okuma açık, yazma kapalı (D7).
"""

from __future__ import annotations

from apps.oab.hatalar import DonemKapali, DonemSaltOkur, DonemYazilamaz
from apps.oab.kurallar.yukleyici import icerik_ozeti
from apps.oab.models import OabTerm, RulePackage, TermStatus
from apps.okul.models import AuditLabel
from shared import kanonik


def kopya_tutuyor(kopya: RulePackage) -> bool:
    """Kopya kanonik özetini tutuyor mu? Kanonik biçime girmeyen içerik tutmuyor sayılır (`kodla`)."""
    try:
        return icerik_ozeti(kopya.content) == kopya.content_sha256
    except kanonik.KanonikHata:
        return False


def kural_kopyasi_tutuyor(donem: OabTerm) -> bool:
    """Dönemin dondurulmuş kopyası kanonik özetini tutuyor mu? (D7 dönem kolu)"""
    return kopya_tutuyor(donem.rule_package)


def yazma_denetimi(
    donem: OabTerm, *, beyaz_liste: bool = False, hazirlik_yazimi: bool = False
) -> str:
    """Döneme yazılabilir mi? Yazılamıyorsa dönem hatası yükseltir; izin satırının etiketini döner.

    `beyaz_liste`: kapanmış dönemde izinli işaret ya da yeniden basım (O2, R12). `hazirlik_yazimi`:
    genel kurul hazırlığı (aday ve seçim üyelikleri, tahmini bütçe, genel kurul evrakı).
    """
    if not kural_kopyasi_tutuyor(donem):
        raise DonemSaltOkur
    if donem.status == TermStatus.KAPANDI:
        if beyaz_liste:
            return str(AuditLabel.KAPALI_DONEM.value)
        raise DonemKapali
    if donem.status == TermStatus.IPTAL:
        raise DonemYazilamaz
    if donem.status == TermStatus.HAZIRLIK and not hazirlik_yazimi:
        raise DonemYazilamaz
    return ""
