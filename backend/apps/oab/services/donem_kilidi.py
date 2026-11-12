"""Dönem kilidi (tasarım §5 O2) ve kural kopyasının bütünlüğü (§6.3 D7).

`term` taşıyan kayıt dönemi `KAPANDI` ise yazılamaz (sert). Beyaz liste yalnız işaret alanları, yeniden
basım ve işaretin kapattığı `EKSIK` satırıdır; bu yazmalar `KAPALI_DONEM` etiketiyle izlenir. `HAZIRLIK`
dönemine yalnız genel kurul hazırlığı yazılır. Dönemin kural kopyası özetini tutmuyorsa dönem salt
okur açılır: okuma açık, yazma kapalı (D7).

Geçiş kurulumunun kilidi (§7.9 "Senaryolar"; plan F1c 8. adımın kararı): geçiş kayıtları (genel kurulsuz
açılan ilk dönem, devralınan üyelik, programdan önceki seçilme sayılarının beyanı, karar defterinin geçiş
kaydı) ve iptal yolları "Geçiş kurulumu tamamlandı" işaretine (`OabTerm.transition_completed_on`) kadar
açıktır, sonra kilitlidir (`GecisKapali`, 409).
"""

from __future__ import annotations

from apps.oab.hatalar import DonemKapali, DonemSaltOkur, DonemYazilamaz, GecisKapali
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


# ---------------------------------------------------------------------------
# Geçiş kurulumunun kilidi (tasarım §7.9 "Senaryolar"; plan F1c 8. adımın kararı)
# ---------------------------------------------------------------------------
def gecis_donemi_mi(donem: OabTerm) -> bool:
    """Genel kurulsuz açılan (geçiş kurulumunun) dönemi mi? İptal edilmiş dönem sayılmaz."""
    return donem.opened_by_assembly_id is None and donem.status != TermStatus.IPTAL


def gecis_acik_mi(donem: OabTerm) -> bool:
    """Geçiş kayıtları bu döneme yazılabilir mi? Dönem genel kurulsuz açılmış, `ACIK` ve "Geçiş
    kurulumu tamamlandı" işareti konmamış olmalıdır."""
    return (
        donem.opened_by_assembly_id is None
        and donem.status == TermStatus.ACIK
        and donem.transition_completed_on is None
    )


def gecis_yazma_denetimi(donem: OabTerm) -> OabTerm:
    """Geçiş kaydı yazılmadan önce: dönemin güncel hâli geçişe açık değilse `GecisKapali` (409).

    Dönem kilidi ayrıca denetlenir (kural kopyası, kapanmış dönem; `yazma_denetimi`). Güncel kayıt
    döner: işaret başka bir istekte konmuş olabilir, bellekteki örneğe güvenilmez.
    """
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    yazma_denetimi(guncel)
    if not gecis_acik_mi(guncel):
        raise GecisKapali
    return guncel
