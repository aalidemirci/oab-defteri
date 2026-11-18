"""Denetleme Kurulunun asgari denetim raporu (tasarım §5.2.4 `AuditReport`, §4.4.2 M8 ve dipnot ⁵; plan
F2 §7 U13, §6.2; F2 7. adım).

F2 yalnız Denetleme Kurulunun md. 14/5 olağanüstü genel kurul çağrısını açan kısmı yazar: dönem, tür,
rapor günü ve iki işaret (`models.denetim` başlığı). Rapor içeriği (kontrol listesi, bulgular), ara
raporun yönetim kuruluna, nihai raporun genel kurula sunuluşu, E32 ve E33 üretimi F4'tedir; ekranı
yoktur, işaret çağrı penceresinde konur (U13; uç ve pencere 11. adımda).

KİM (tasarım §4.4.2 M8 ⁵; K2). Yalnız Denetleme Kurulu yazar (`Eylem.DK_GENEL_KURUL_YAZMA`; sahiplikli,
DK yalnız kendi raporunu yazar). Yönetim kurulu rolleri ve program yöneticisi yazamaz: DK, yönetim
kurulunun faaliyetlerini inceler (md. 14/4). Çağrının kendisi `genel_kurul.cagir`'dadır
(`called_by=DENETLEME_KURULU`, `call_audit_report`); iki bağ aynı işlemde yazılır.

İKİ İŞARET (denetim MB-10). `irregularity_found` raporun usulsüzlük bayrağıdır, md. 14/5'in yolunu
açmaz (usulsüzlük müdürün md. 27/3 yoludur); çağrı yalnız `md6_violation_found` işaretli raporla açılır
(kullanıcı kararı S6 (ii), hukuken geçersiz işlem — sert).

Rapor açık birlik dönemine yazılır (denetlenen dönem). Kayıt silinmez (altın kural 4); yazma denetim
izine düşer.
"""

from __future__ import annotations

from datetime import date, datetime

from django.db import transaction

from apps.oab.models import AuditReport, AuditReportKind, OabTerm, TermStatus
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.services import app_password

RAPOR_TURU_GECERSIZ = "Denetim raporunun türü ara rapor ya da nihai rapor olmalıdır."
RAPOR_GUNU_GEREKLI = "Denetim raporunun günü girilmelidir."
ISARET_GECERSIZ = "Denetim raporunun işaretleri evet ya da hayır olmalıdır."
ACIK_DONEM_YOK = "Açık birlik dönemi yok; denetim raporu açık birlik dönemine yazılır."


@transaction.atomic
def denetim_raporu_yaz(
    *,
    kind: str,
    report_date: date,
    md6_violation_found: bool,
    irregularity_found: bool = False,
) -> AuditReport:
    """Asgari denetim raporunu yazar (`TASLAK`; modül başlığı). Tür ve rapor günü zorunludur (U13)."""
    app_password.require_password_set()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA)
    if kind not in AuditReportKind.values:
        raise ValueError(RAPOR_TURU_GECERSIZ)
    if not isinstance(report_date, date) or isinstance(report_date, datetime):
        raise ValueError(RAPOR_GUNU_GEREKLI)
    if not isinstance(md6_violation_found, bool) or not isinstance(irregularity_found, bool):
        raise ValueError(ISARET_GECERSIZ)
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    if donem is None:
        raise ValueError(ACIK_DONEM_YOK)
    # Sahiplik ve kapanmış dönem kaydın üstünde de sorulur (dönemin sahibi rol yoktur).
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.DK_GENEL_KURUL_YAZMA, donem)
    donem_kilidi.yazma_denetimi(donem)
    hesap = iz.yazar_hesabi()
    rapor = AuditReport.objects.create(
        term=donem,
        kind=kind,
        report_date=report_date,
        irregularity_found=irregularity_found,
        md6_violation_found=md6_violation_found,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(rapor, onceki=None)
    return rapor
