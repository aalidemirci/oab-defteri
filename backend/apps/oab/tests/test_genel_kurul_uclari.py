"""Genel kurul, genel kurul evrakı, yıllık iş takvimi ve gelen-giden evrak uçları (plan F2 §6.1, §6.2;
11. adımın arka yüzü, "11a").

Uç başına rol × izin tablosu (izinli/izinsiz; tablo elle yazılır, `rol_izinleri.KURALLAR`'dan
türetilmez), sihirbazın uçtan uca uç testleri (olağan genel kurul — pilot akışı: birinci toplantıda
yeter sayı yok, ikinci toplantı —, yeni açılan okulun ilk genel kurulu ve olağanüstü genel kurul:
Denetleme Kurulunun md. 14/5 çağrısı), veli adlı çıktının saklanmadığı ve erişim günlüğüne yazıldığı,
E04'ün katalogda üretilemediği, E12'nin evrak kaydının önerilip onayla kaydedildiği, dosya eklerinin
rolleri ve 10. adımın 11. adıma bıraktığı il/ilçe millî eğitim müdürlüğü bildiriminin metni. Kişi
adları ve tarihler UYDURMADIR.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, cast

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.oab.models import (
    AgendaItem,
    AssemblyKind,
    AuditReport,
    ComplianceItem,
    ComplianceObligation,
    DocumentRecord,
    GeneralAssembly,
    GeneratedDocument,
    OabTerm,
    TermStatus,
)
from apps.oab.services import gelen_giden_evrak, uyelik_gecisleri
from apps.oab.services import genel_kurul as gk
from apps.oab.services import genel_kurul_evraki as gke
from apps.oab.tests import genel_kurul_ortak as g
from apps.oab.tests import uyelik_ortak as o
from apps.okul import rol_izinleri
from apps.okul.models import (
    AccessKind,
    AccessLog,
    AccountRole,
    Attachment,
    AuditAction,
    AuditTrail,
    ParentRoster,
    SchoolConfig,
)

pytestmark = pytest.mark.django_db

API = "/api/v1/oab"
PDF = b"%PDF-1.7 uydurma"
GEREKCE = "Uydurma gerekçe: okul idaresinin yazısıyla kayda geçti."
#: Var olmayan kaydın kimliği (izinli rol rol kapısından geçer, görünüm 404 döner).
YOK = 999_999

#: Kişi adı taşıyan özgün dosya adı (uydurma): indirme adına girmez (sözlük §5).
KISI_ADLI_DOSYA = "Uydurma Ad Soyad faaliyet raporu.pdf"


def _ek_yukle(yol: str, ad: str = "ek.pdf", icerik: bytes = PDF) -> Any:
    from django.core.files.uploadedfile import SimpleUploadedFile

    return APIClient().post(yol, {"file": SimpleUploadedFile(ad, icerik)}, format="multipart")


def _bugun() -> str:
    return f"{timezone.localdate():%d.%m.%Y}"


# ============================================================ rol × izin tablosu

HER = frozenset(rol_izinleri.ROLLER)
Y = frozenset({"yonetici"})
SEK = "sekreter"
Y_SEK = frozenset({"yonetici", SEK})
Y_YK = frozenset({"yonetici", "baskan", "baskan_yardimcisi", "muhasip", SEK})
DK = frozenset({"denetleme_kurulu"})
MUD = frozenset({"mudur"})

#: (yöntem, yol, izinli roller) — tasarım §4.4.2 M1, M3, M8, M9, M10, kişisel veri satırı; §7.1 "Kim";
#: §9.6 "Üreten"; plan F2 §6.1, §6.2, §7 U23, U32, U33 (yol örnekleri; kayıt yoktur).
TABLO: tuple[tuple[str, str, frozenset[str]], ...] = (
    ("GET", f"{API}/assemblies/", HER),
    ("POST", f"{API}/assemblies/", Y_SEK),
    ("GET", f"{API}/assemblies/{YOK}/", HER),
    ("PATCH", f"{API}/assemblies/{YOK}/", Y_SEK | MUD),
    ("PUT", f"{API}/assemblies/{YOK}/agenda-order/", Y_SEK | MUD),
    ("POST", f"{API}/assemblies/{YOK}/call/", Y_SEK | {"baskan"}),
    ("POST", f"{API}/assemblies/{YOK}/principal-call/", MUD),
    ("POST", f"{API}/assemblies/{YOK}/audit-board-call/", DK),
    ("POST", f"{API}/assemblies/{YOK}/call-document/", Y),
    ("POST", f"{API}/assemblies/{YOK}/cancel/", Y),
    ("POST", f"{API}/assemblies/{YOK}/announcement/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/second-announcement/", Y_SEK),
    ("PUT", f"{API}/announcements/{YOK}/evidence/", Y_SEK),
    ("POST", f"{API}/announcements/{YOK}/attachments/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/first-meeting/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/second-meeting/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/attendance-corrections/", Y_SEK),
    ("GET", f"{API}/assemblies/{YOK}/attendance-marks/", Y),
    ("POST", f"{API}/assemblies/{YOK}/attendance-marks/", Y),
    ("POST", f"{API}/assemblies/{YOK}/agenda/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/removal/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/result/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/election/", Y_SEK),
    ("PUT", f"{API}/agenda-items/{YOK}/election-form/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/election-cancel/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/discharge/", Y_SEK),
    ("POST", f"{API}/agenda-items/{YOK}/attachments/", Y_YK),
    ("POST", f"{API}/agenda-items/{YOK}/audit-board-attachment/", DK),
    ("POST", f"{API}/assemblies/{YOK}/presiding-board/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/presiding-board-cancel/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/candidates/", Y_SEK),
    ("PATCH", f"{API}/assemblies/{YOK}/minutes/", Y_SEK),
    ("POST", f"{API}/assemblies/{YOK}/minutes-complete/", Y_SEK),
    ("GET", f"{API}/assemblies/{YOK}/term-transition/", HER),
    ("POST", f"{API}/assemblies/{YOK}/term-transition/", Y),
    ("GET", f"{API}/assembly-documents/catalog/", HER),
    ("GET", f"{API}/assemblies/{YOK}/documents/", HER),
    ("POST", f"{API}/assemblies/{YOK}/documents/e10/", Y_SEK | {"baskan"} | MUD),
    ("POST", f"{API}/assemblies/{YOK}/documents/e05/audit-board/", DK),
    ("POST", f"{API}/assemblies/{YOK}/documents/e07/named/", Y),
    ("GET", f"{API}/terms/{YOK}/annual-calendar/", HER),
    ("POST", f"{API}/terms/{YOK}/documents/e14/", Y),
    ("GET", f"{API}/document-books/", HER),
    ("POST", f"{API}/document-books/", Y_YK),
    ("GET", f"{API}/document-records/", HER),
    ("POST", f"{API}/document-records/", Y_YK),
    ("POST", f"{API}/document-records/{YOK}/attachments/", Y_YK),
    ("GET", f"{API}/documents/{YOK}/outgoing-record/", HER),
    ("POST", f"{API}/documents/{YOK}/outgoing-record/", Y_YK),
    ("GET", f"{API}/attachments/{YOK}/", HER),
)


def _iste(yontem: str, yol: str, govde: Any = None) -> Any:
    return APIClient().generic(
        yontem,
        yol,
        data="" if govde is None else json.dumps(govde),
        content_type="application/json",
    )


def _rol_yetkisiz(yanit: Any) -> bool:
    return bool(yanit.status_code == 403 and yanit.json().get("code") == "rol_yetkisiz")


@pytest.mark.parametrize(("yontem", "yol", "izinli"), TABLO, ids=[f"{t[0]} {t[1]}" for t in TABLO])
def test_uc_basina_rol_izin_tablosu(yontem: str, yol: str, izinli: frozenset[str]) -> None:
    """İzinli rol rol kapısından geçer (kayıt yok: 404 ya da gövde 400; 403 değil), izinsiz rol 403
    `rol_yetkisiz` alır. Tablo kurallarla da birebir (`rol_izinleri.acik_roller`)."""
    from django.urls import resolve

    assert rol_izinleri.acik_roller(resolve(yol).view_name, yontem) == izinli, yol
    for rol in rol_izinleri.ROLLER:
        with o.rol_olarak(AccountRole(rol)):
            yanit = _iste(yontem, yol, {})
        assert _rol_yetkisiz(yanit) == (rol not in izinli), (rol, yanit.status_code)


# ============================================================ uçtan uca: olağan genel kurul (pilot)


def _yanit(yanit: Any, kod: int = 200) -> Any:
    assert yanit.status_code == kod, (yanit.status_code, yanit.content[:500])
    return yanit.json()


def _gundem_maddesi(kurul: dict[str, Any], tur: str) -> dict[str, Any]:
    return next(m for m in kurul["gundem"] if m["kind"] == tur)


def test_olagan_genel_kurul_sihirbazi_ikinci_toplantida_secim_ve_donem_gecisi() -> None:
    """Pilot akışı uçlardan (plan F2 §2 madde 1): planla → yönetim kurulunun çağrısı (sekreter; karar
    bağı F3'e dek uyarı + gerekçe, S1) → ilan (yeter sayı dondurulur) → birinci toplantıda yeter sayı
    yok (programın hesabı; müdürün açılışı bilgi satırı) → ikinci toplantı → divan → aday ve seçim →
    ibra → tutanak bilgisi → tutanak tamam (dönem kendiliğinden açılmaz) → dönem geçişinin önizlemesi
    ve onayı (yalnız program yöneticisi, U32). Her adımda evrak üretilir."""
    eski = g.acik_donem()
    kurul = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/",
            {"kind": "OLAGAN", "first_meeting_at": "2026-10-20T10:00:00+03:00"},
        ),
        201,
    )["genel_kurul"]
    pk = kurul["id"]
    assert kurul["status"] == "PLANLANDI" and kurul["term"] == eski.pk
    assert [m["kind"] for m in kurul["gundem"]][:2] == ["ACILIS", "DIVAN_SECIMI"]
    assert any("öğrenci mevcudu" in b for b in kurul["bilgiler"])
    liste = _yanit(_iste("GET", f"{API}/assemblies/"))
    assert [k["id"] for k in liste["kayitlar"]] == [pk]
    assert liste["kural_surumu_guncellenmeli"] is False

    # Çağrı: program yöneticisi yönetim kurulunun çağrısını yazmaz (servisin daraltması, §7.1 "Kim");
    # sekreterde gerekçesiz 400 `gerekce_gerekli` (S1), gerekçeyle geçer.
    assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{pk}/call/", {"gerekce": GEREKCE}))
    with o.rol_olarak(AccountRole.SEKRETER):
        ret = _iste("POST", f"{API}/assemblies/{pk}/call/", {})
        assert ret.status_code == 400 and ret.json()["code"] == "gerekce_gerekli"
        cagri = _yanit(_iste("POST", f"{API}/assemblies/{pk}/call/", {"gerekce": GEREKCE}))
    assert cagri["genel_kurul"]["status"] == "CAGRILDI"
    gun = g.ILAN_GUNU.isoformat()
    ilan = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/announcement/",
            {
                "kanallar": {
                    "distributed_written_on": gun,
                    "posted_board_on": gun,
                    "published_web_on": gun,
                },
                "second_meeting_at": "2026-11-05T10:00:00+03:00",
            },
        )
    )["genel_kurul"]
    assert (ilan["status"], ilan["quorum_required"]) == ("ILAN_EDILDI", 64)
    assert gk.MUDUR_ACILIS_BILGISI in ilan["bilgiler"]
    with o.rol_olarak(AccountRole.SEKRETER):
        e05 = _yanit(
            _iste("POST", f"{API}/assemblies/{pk}/documents/e05/", {"toplanti": "BIRINCI"}), 201
        )
    assert e05["evrak"]["kod"] == "E05" and e05["evrak"]["toplanti"] == "BIRINCI"

    birinci = _yanit(_iste("POST", f"{API}/assemblies/{pk}/first-meeting/", {"attendee_count": 10}))
    assert birinci["genel_kurul"]["status"] == "YETER_SAYI_YOK"
    assert gk.MUDUR_ACILIS_BILGISI in birinci["bilgiler"]
    ikinci = _yanit(_iste("POST", f"{API}/assemblies/{pk}/second-meeting/", {"attendee_count": 20}))
    assert (ikinci["genel_kurul"]["status"], ikinci["genel_kurul"]["held_at_meeting"]) == (
        "YAPILDI",
        "IKINCI",
    )
    e64 = _yanit(
        _iste("POST", f"{API}/assemblies/{pk}/documents/e64/", {"toplanti": "IKINCI"}), 201
    )
    assert e64["evrak"]["kod"] == "E64"

    baskan, katip = o.kisi(), o.kisi()
    divan = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/presiding-board/",
            {"baskan": baskan.pk, "katip": katip.pk},
        ),
        201,
    )["genel_kurul"]["divan"]
    assert {u["person"] for u in divan} == {baskan.pk, katip.pk}
    # Divanın düzeltilmesi: kayıtlar silinmez, iptal olur; ayrıntı iptal edilmiş divanı göstermez ve
    # doğru divan yeniden seçilir.
    duzeltilen = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/presiding-board-cancel/",
            {"cancel_reason": GEREKCE},
        )
    )["genel_kurul"]["divan"]
    assert duzeltilen == []
    baskan, katip = o.kisi(), o.kisi()
    divan = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/presiding-board/",
            {"baskan": baskan.pk, "katip": katip.pk},
        ),
        201,
    )["genel_kurul"]["divan"]
    assert [(u["person"], u["role"]) for u in divan] == [(baskan.pk, "BASKAN"), (katip.pk, "KATIP")]

    adaylar = []
    for organ, adet in (("YK", 5), ("DK", 1)):
        for _ in range(adet):
            govde = {"person": o.kisi().pk, "organ": organ, "seat_type": "ASIL"}
            if organ == "DK":
                govde["seat_group"] = "VELI"
            aday = _yanit(_iste("POST", f"{API}/assemblies/{pk}/candidates/", govde), 201)
            assert aday["status"] == "ADAY" and "tckn" not in str(aday).lower()
            adaylar.append((organ, aday["id"]))
    ayrinti = _yanit(_iste("GET", f"{API}/assemblies/{pk}/"))
    for tur, organ in (("SECIM_YK", "YK"), ("SECIM_DK", "DK")):
        madde = _gundem_maddesi(ayrinti, tur)
        oylar = [
            {"uyelik": uyelik, "votes": 20 - i, "secildi": True}
            for i, (o_, uyelik) in enumerate(adaylar)
            if o_ == organ
        ]
        secim = _yanit(
            _iste(
                "POST",
                f"{API}/agenda-items/{madde['id']}/election/",
                {"adaylar": oylar, "liste": True, "acik_oy": True},
            )
        )
        assert secim["madde"]["result"]
    ibra = _gundem_maddesi(ayrinti, "IBRA")
    oylama = {"votes_for": 15, "votes_against": 3}
    sonuc = _yanit(
        _iste("POST", f"{API}/agenda-items/{ibra['id']}/discharge/", {"yk": oylama, "dk": oylama})
    )
    assert (sonuc["genel_kurul"]["discharge_yk"], sonuc["genel_kurul"]["discharge_dk"]) == (
        "EDILDI",
        "EDILDI",
    )
    tutanak = _yanit(
        _iste("PATCH", f"{API}/assemblies/{pk}/minutes/", {"handed_to_new_yk_on": "2026-11-06"})
    )["genel_kurul"]["tutanak"]
    assert tutanak["handed_to_new_yk_on"] == "2026-11-06"
    e10 = _yanit(_iste("POST", f"{API}/assemblies/{pk}/documents/e10/", {}), 201)
    assert e10["evrak"]["kod"] == "E10"

    tamam = _yanit(_iste("POST", f"{API}/assemblies/{pk}/minutes-complete/", {"gerekce": GEREKCE}))
    assert tamam["genel_kurul"]["status"] == "TUTANAK_TAMAM"
    hazirlik = OabTerm.objects.get(pk=tamam["genel_kurul"]["opens_term"])
    assert hazirlik.status == TermStatus.HAZIRLIK  # U32: tutanak tamamı dönemi açmaz
    onizleme = _yanit(_iste("GET", f"{API}/assemblies/{pk}/term-transition/"))
    assert onizleme["engeller"] == [] and onizleme["baslangic"] == "2026-11-05"
    assert onizleme["kapanacak_bitis"] == "2026-11-04"
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{pk}/term-transition/"))
    onay = _yanit(_iste("POST", f"{API}/assemblies/{pk}/term-transition/"))
    assert onay["yeni_donem"]["status"] == "ACIK" and onay["kapanacak"]["status"] == "KAPANISTA"
    belgeler = _yanit(_iste("GET", f"{API}/assemblies/{pk}/documents/"))
    assert {b["kod"] for b in belgeler} == {"E05", "E64", "E10"}
    # Basım genel indirme ucundan: okuyan her rol (Denetleme Kurulu da) basar.
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        basim = APIClient().get(f"{API}/documents/{e10['evrak']['id']}/pdf/")
    assert basim.status_code == 200 and basim["Content-Type"] == "application/pdf"


# ============================================================ uçtan uca: yeni açılan okul


def test_yeni_okul_sihirbazi_mudurun_daveti_ve_ilk_donemin_acilisi() -> None:
    """Yeni açılan okulun ilk genel kurulu (S5): kapanacak dönem yoktur; daveti yalnız okul müdürü
    kendi hesabından yazar (¹, M-11; program yöneticisi ve sekreter yazamaz). Evrak defteri kayıtlı
    olmadığından yazı deftere işlenmez (bilgi satırı, ⁷). Toplantı → divan → seçim → tutanak → dönem
    geçişi: hazırlık dönemi açılır, kapanacak dönem yoktur."""
    g.ders_yillari()
    g.mevcut()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(opened_on=date(2026, 9, 7))
    kurul = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/",
            {"kind": "OLAGAN", "first_meeting_at": "2026-10-20T10:00:00+03:00"},
        ),
        201,
    )["genel_kurul"]
    pk = kurul["id"]
    assert (kurul["term"], kurul["called_by"]) == (None, "MUDUR_YENI_OKUL")
    assert kurul["cagri_sahibi"] == "mudur"
    # Program yöneticisi ve sekreter müdürün yazısını yazamaz (rol kapısı ve servis).
    assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{pk}/principal-call/", {}))
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{pk}/call/", {"gerekce": GEREKCE}))
    with o.rol_olarak(AccountRole.MUDUR):
        davet = _yanit(_iste("POST", f"{API}/assemblies/{pk}/principal-call/", {}))
    assert davet["genel_kurul"]["status"] == "CAGRILDI"
    assert gk.MUDUR_YAZISI_DEFTERSIZ in davet["bilgiler"]
    assert not DocumentRecord.objects.exists()
    gun = g.ILAN_GUNU.isoformat()
    _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/announcement/",
            {
                "kanallar": {
                    "distributed_written_on": gun,
                    "posted_board_on": gun,
                    "published_web_on": gun,
                }
            },
        )
    )
    _yanit(_iste("POST", f"{API}/assemblies/{pk}/first-meeting/", {"attendee_count": g.KATILAN}))
    _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/presiding-board/",
            {"baskan": o.kisi().pk, "katip": o.kisi().pk},
        ),
        201,
    )
    ayrinti = _yanit(_iste("GET", f"{API}/assemblies/{pk}/"))
    uyeler = [
        _yanit(
            _iste(
                "POST",
                f"{API}/assemblies/{pk}/candidates/",
                {"person": o.kisi().pk, "organ": "YK", "seat_type": "ASIL"},
            ),
            201,
        )["id"]
        for _ in range(5)
    ]
    madde = _gundem_maddesi(ayrinti, "SECIM_YK")
    _yanit(
        _iste(
            "POST",
            f"{API}/agenda-items/{madde['id']}/election/",
            {
                "adaylar": [
                    {"uyelik": u, "votes": 60 - i, "secildi": True} for i, u in enumerate(uyeler)
                ],
                "liste": True,
                "acik_oy": True,
            },
        )
    )
    _yanit(_iste("POST", f"{API}/assemblies/{pk}/minutes-complete/", {"gerekce": GEREKCE}))
    onay = _yanit(_iste("POST", f"{API}/assemblies/{pk}/term-transition/"))
    assert onay["kapanacak"] is None and onay["yeni_donem"]["status"] == "ACIK"
    assert onay["yeni_donem"]["start_date"] == "2026-10-20"


# ============================================================ uçtan uca: olağanüstü (Denetleme Kurulu)


def test_olaganustu_dk_cagrisi_yalniz_md6_isaretiyle_ve_donem_acmaz() -> None:
    """Denetleme Kurulunun md. 14/5 çağrısı (⁵): rapor aynı istekte yazılır; md. 6 işareti yoksa çağrı
    reddedilir (S6 (ii), sert) ve rapor da yazılmaz (tek işlem). İşaretle çağrı açılır, iki bağ
    yazılır. Olağanüstü genel kurul dönem açmaz: dönem geçişinin önizlemesi 400 (md. 13/8)."""
    g.acik_donem()
    kurul = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/",
            {"kind": "OLAGANUSTU", "first_meeting_at": "2026-12-10T10:00:00+03:00"},
        ),
        201,
    )["genel_kurul"]
    pk = kurul["id"]
    govde: dict[str, Any] = {
        "call_reason": g.OLAGANUSTU_NEDEN,
        "gundem": [
            {"title": "Açılış ve yoklama", "kind": "ACILIS"},
            {"title": "Yönetim kurulu asıl ve yedek üye seçimi", "kind": "SECIM_YK"},
        ],
        "rapor": {
            "kind": "ARA",
            "report_date": "2026-11-20",
            "md6_violation_found": False,
            "irregularity_found": True,
        },
    }
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        ret = _iste("POST", f"{API}/assemblies/{pk}/audit-board-call/", govde)
        assert ret.status_code == 400, ret.content
        assert not AuditReport.objects.exists()
        govde["rapor"]["md6_violation_found"] = True
        cagri = _yanit(_iste("POST", f"{API}/assemblies/{pk}/audit-board-call/", govde))
    assert cagri["genel_kurul"]["status"] == "CAGRILDI"
    assert cagri["genel_kurul"]["cagri_sahibi"] == "denetleme_kurulu"
    assert gk.DK_YAZISI_BAGSIZ in cagri["bilgiler"]
    rapor = AuditReport.objects.get()
    assert rapor.escalated_assembly_id == pk
    # Program yöneticisi ve sekreter Denetleme Kurulunun çağrısını yazamaz.
    assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{pk}/audit-board-call/", govde))
    gun = date(2026, 11, 24).isoformat()
    _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{pk}/announcement/",
            {
                "kanallar": {
                    "distributed_written_on": gun,
                    "posted_board_on": gun,
                    "published_web_on": gun,
                }
            },
        )
    )
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        e05 = _yanit(
            _iste(
                "POST", f"{API}/assemblies/{pk}/documents/e05/audit-board/", {"toplanti": "BIRINCI"}
            ),
            201,
        )
    assert e05["evrak"]["kod"] == "E05"
    with o.rol_olarak(AccountRole.SEKRETER):
        # Denetleme Kurulunun kolunda E05'i sekreter üretmez (çağrının sahiplikli eylemi).
        assert _rol_yetkisiz(
            _iste("POST", f"{API}/assemblies/{pk}/documents/e05/", {"toplanti": "BIRINCI"})
        )
    _yanit(_iste("POST", f"{API}/assemblies/{pk}/first-meeting/", {"attendee_count": g.KATILAN}))
    ret = _iste("GET", f"{API}/assemblies/{pk}/term-transition/")
    assert ret.status_code == 400 and gk.DONEM_ACMAZ in str(ret.json())


# ============================================================ veli adlı çıktı ve katılım işareti


def test_adli_cikti_saklanmaz_erisim_gunlugune_yazilir_ve_yalniz_yoneticiye_acilir() -> None:
    """Veli adlı E07 (U15; R9, ¹⁰): tek istekte üretilir ve verilir, `no-store`; evrak kaydı dosyasız
    (`personal_list`, ek yok, içerik yok), erişim günlüğünde `VELI_LISTESI_CIKTISI` satırı (ad yok);
    kayıt yeniden basılmaz (404). Sekreter ve öteki roller 403."""
    g.veli_aktar([("UYDURMA VELİ", "9-A"), ("DENEME VELİ", "10/B")])
    kurul = g.ilanli_olagan()
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(
            _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e07/named/", {"bicim": "pdf"})
        )
    yanit = _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e07/named/", {"bicim": "pdf"})
    assert yanit.status_code == 200, yanit.content[:300]
    assert yanit["Cache-Control"] == "no-store" and yanit["Content-Type"] == "application/pdf"
    assert b"".join(cast(Any, yanit).streaming_content).startswith(b"%PDF")
    kayit = GeneratedDocument.objects.get(doc_type="E07", variant="ADLI")
    assert kayit.personal_list and kayit.row_count == 2 and not kayit.content_json
    assert not kayit.ekler().exists()
    (satir,) = AccessLog.objects.filter(kind=AccessKind.VELI_LISTESI_CIKTISI)
    assert satir.row_count == 2 and "UYDURMA" not in str(satir.__dict__)
    assert APIClient().get(f"{API}/documents/{kayit.pk}/pdf/").status_code == 404
    liste = _yanit(_iste("GET", f"{API}/assemblies/{kurul.pk}/documents/"))
    (adli,) = [b for b in liste if b["kip"] == "ADLI"]
    assert adli["bicimler"] == [] and adli["satir_sayisi"] == 2


def test_katilim_isaretleri_penceresi_yalniz_yonetici_ve_erisim_gunlugu() -> None:
    """U33: pencere veli adlarını sınıf başına verir, okuması erişim günlüğüne yazılır, yanıt
    önbelleğe alınmaz; işaret sayısı ayrıntıda öneridir (kişisiz). Sekreter 403."""
    g.veli_aktar([("UYDURMA VELİ", "9-A"), ("DENEME VELİ", "10/B")])
    kurul = g.ilanli_olagan()
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(
            _iste("GET", f"{API}/assemblies/{kurul.pk}/attendance-marks/?toplanti=BIRINCI")
        )
    yanit = _iste("GET", f"{API}/assemblies/{kurul.pk}/attendance-marks/?toplanti=BIRINCI")
    veri = _yanit(yanit)
    assert yanit["Cache-Control"] == "no-store"
    adlar = {s["veli"] for sinif in veri["siniflar"] for s in sinif["satirlar"]}
    assert adlar == {"UYDURMA VELİ", "DENEME VELİ"}
    assert AccessLog.objects.filter(kind=AccessKind.VELI_LISTESI_CIKTISI).count() == 1
    satirlar = list(ParentRoster.objects.values_list("pk", flat=True))
    isaret = _yanit(
        _iste(
            "POST",
            f"{API}/assemblies/{kurul.pk}/attendance-marks/",
            {"toplanti": "BIRINCI", "isaretle": satirlar},
        )
    )
    assert isaret == {"toplanti": "BIRINCI", "isaret_sayisi": 2}
    with o.rol_olarak(AccountRole.MUDUR):
        ayrinti = _yanit(_iste("GET", f"{API}/assemblies/{kurul.pk}/"))
    assert ayrinti["katilim_isareti_sayilari"] == {"BIRINCI": 2, "IKINCI": 0}
    assert "VELİ" not in str(ayrinti)


# ============================================================ katalog, E04, E12, takvim, ekler


def test_e04_katalogda_durur_ama_uretilmez() -> None:
    """E04'ün kurucusu yoktur (dört alt metin onay bekler, plan F2 §9 S8): katalogda üretilemez ve
    nedeni yanında; üretim ucu 400 (kayıt yazılmaz)."""
    katalog = _yanit(_iste("GET", f"{API}/assembly-documents/catalog/"))
    belgeler = {b["kod"]: b for b in katalog["belgeler"]}
    assert set(belgeler) == set(gke.KODLAR)
    assert (
        belgeler["E04"]["uretilebilir"] is False
        and "onay bekliyor" in belgeler["E04"]["uretilemez_nedeni"]
    )
    assert all(b["uretilebilir"] for kod, b in belgeler.items() if kod != "E04")
    assert belgeler["E07"]["kipler"] == ["KISISIZ", "ADLI"] and belgeler["E05"]["toplantili"]
    assert belgeler["E12"]["muhatapli"] and katalog["varsayilan_muhatap"] == "ILCE"
    assert set(katalog["muhatap_onerileri"]) == {"ILCE", "IL"}
    kurul = g.ilanli_olagan()
    ret = _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e04/", {})
    assert ret.status_code == 400 and gke.KOD_GECERSIZ in str(ret.json())
    ret = _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e14/", {})
    assert ret.status_code == 400
    assert not GeneratedDocument.objects.exists()


def _ibra_edilmemis_kurul() -> GeneralAssembly:
    kurul = g.yapilmis_olagan()
    gk.ibra_yaz(
        g.madde(kurul, "IBRA"),
        yk=g.IBRA_EDILMEDI,
        dk=g.IBRA_EDILDI,
        unaudited_documents_note="Uydurma: 2026 yılı kasa defteri.",
    )
    return kurul


def test_e12_muhatap_secimi_ve_giden_evrak_kaydi_onerilir_onayla_kaydedilir() -> None:
    """E12 (U20): muhatap il millî eğitim müdürlüğü seçilir; üretim kendiliğinden evrak kaydı yazmaz.
    Öneri (GET) yazmaz; onay (POST) giden evrakı üretilen evrak bağıyla kaydeder; ikinci kayıt 400 (bir
    yazı bir kez). Program yöneticisi üretir, sekreter üretemez (§9.6)."""
    kurul = _ibra_edilmemis_kurul()
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(_iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e12/", {}))
    e12 = _yanit(
        _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e12/", {"muhatap_secimi": "IL"}), 201
    )["evrak"]
    assert not DocumentRecord.objects.exists()
    gelen_giden_evrak.evrak_defteri_olustur()
    oneri = _yanit(_iste("GET", f"{API}/documents/{e12['id']}/outgoing-record/"))
    assert oneri["kayitli"] is None and oneri["direction"] == "GIDEN"
    assert "VALİLİĞİNE" in oneri["counterparty"] and oneri["subject"] == gke.E12_KONU
    assert oneri["onerilen_no"] == 1 and not DocumentRecord.objects.exists()
    govde = {k: oneri[k] for k in ("tarih", "counterparty", "subject")}
    with o.rol_olarak(AccountRole.SEKRETER):
        kayit = _yanit(_iste("POST", f"{API}/documents/{e12['id']}/outgoing-record/", govde), 201)
    assert kayit["kayit"]["generated_document"] == e12["id"]
    assert kayit["kayit"]["direction"] == "GIDEN" and kayit["kayit"]["record_no"] == 1
    ret = _iste("POST", f"{API}/documents/{e12['id']}/outgoing-record/", govde)
    assert ret.status_code == 400 and "bir kez" in str(ret.json())
    with o.rol_olarak(AccountRole.MUDUR):
        assert _rol_yetkisiz(_iste("POST", f"{API}/documents/{e12['id']}/outgoing-record/", govde))
        okuma = _yanit(_iste("GET", f"{API}/documents/{e12['id']}/outgoing-record/"))
    assert okuma["kayitli"]["kayit_no"] == 1


def test_secimsiz_olaganustu_kurulda_mem_bildirimi_gorevdeki_yonetim_kuruluna() -> None:
    """10. adımın 11. adıma bıraktığı düzeltme: yönetim kurulunu seçmeyen olağanüstü genel kurulda
    yeni yönetim kurulu yoktur; il/ilçe millî eğitim müdürlüğüne bildirimin takvim satırı ve E13'ün
    sonraki işler satırı görevdeki yönetim kurulunu anar (teslim alanlarla aynı kaynak)."""
    acik = g.acik_donem()
    kurul = g.planla(kind="OLAGANUSTU")
    with o.rol_olarak(AccountRole.SEKRETER):
        kurul = gk.cagir(
            kurul,
            called_by="YONETIM_KURULU",
            call_reason=g.OLAGANUSTU_NEDEN,
            gundem=(
                gk.GundemMaddesi(title="Açılış ve yoklama", kind="ACILIS"),
                gk.GundemMaddesi(title="Yönetim kurulunun ibrası", kind="IBRA"),
            ),
        ).kurul
    gk.ilan_et(kurul, kanallar=g.kanallar())
    kurul = gk.birinci_toplanti(kurul, katilim=g.katilim(g.KATILAN)).kurul
    gk.ibra_yaz(
        g.madde(kurul, "IBRA"),
        yk=g.IBRA_EDILMEDI,
        dk=None,
        unaudited_documents_note="Uydurma: kasa defteri.",
    )
    assert gk.secilen_kurullar(kurul) == (False, False)
    gk.tutanagi_tamamla(kurul, gerekce=g.GEREKCE)
    satir = ComplianceItem.objects.get(
        term=acik, obligation=ComplianceObligation.IBRA_EDILMEDI_BILDIRIMI
    )
    assert satir.message == gk.IBRA_BILDIRIMI_MESAJLARI[False]
    assert "görevdeki yönetim kurulu" in satir.message
    belge = str(gke.e13_belgesi(GeneralAssembly.objects.get(pk=kurul.pk), gke.Secim())[0])
    assert gke.IS_MEM_YAZILARI[False] in belge
    assert gke.IS_MEM_YAZILARI[True] not in belge


def test_yillik_is_takvimi_her_rol_okur_basimi_yalniz_yonetici() -> None:
    """M9: Yıllık İş Takvimi'nin verisi her role açık, kişisiz, okuma yazmaz; E14'ün basımını program
    yöneticisi üretir (§9.6) ve dönemin evrak listesinde görünür."""
    donem = g.acik_donem()
    for rol in rol_izinleri.ROLLER:
        with o.rol_olarak(AccountRole(rol)):
            veri = _yanit(_iste("GET", f"{API}/terms/{donem.pk}/annual-calendar/"))
        assert veri["kural_satirlari"] and veri["plan_satirlari"], rol
        assert all(s["kural"] and s["atif"] for s in veri["kural_satirlari"] if s["tarih"] != "………")
    assert not GeneratedDocument.objects.exists()
    with o.rol_olarak(AccountRole.SEKRETER):
        assert _rol_yetkisiz(_iste("POST", f"{API}/terms/{donem.pk}/documents/e14/"))
    e14 = _yanit(_iste("POST", f"{API}/terms/{donem.pk}/documents/e14/"), 201)["evrak"]
    liste = _yanit(_iste("GET", f"{API}/terms/{donem.pk}/documents/"))
    assert [b["kod"] for b in liste] == ["E14"] and liste[0]["ad"] == "Yıllık iş takvimi"
    assert APIClient().get(f"{API}/documents/{e14['id']}/xlsx/").status_code == 200


def test_dosya_ekleri_rolleri_ve_indirme() -> None:
    """U23, S13 (a): faaliyet raporu ve tahmini bütçe yönetim kurulu rolleri ve program yöneticisince,
    Denetleme Kurulunun raporu yalnız Denetleme Kurulunca eklenir; müdür eklemez. Dosya eki maddesi
    olmayan maddeye (açılış) ek eklenmez. Okuyan her rol indirir; indirilen dosyanın adı programın
    kalıbıdır (sözlük §3, §5): özgün ad kişi adı taşıyabilir, yalnız ekin kartında görünür."""
    kurul = g.cagrilmis_olagan()
    yk_raporu = g.madde(kurul, "YK_FAALIYET_RAPORU")
    dk_raporu = g.madde(kurul, "DK_RAPORU")
    acilis = g.madde(kurul, "ACILIS")

    def yukle(madde: AgendaItem, uc: str = "attachments", ad: str = "rapor.pdf") -> Any:
        return _ek_yukle(f"{API}/agenda-items/{madde.pk}/{uc}/", ad)

    with o.rol_olarak(AccountRole.MUHASIP):
        ek = _yanit(yukle(yk_raporu, ad=KISI_ADLI_DOSYA), 201)
        assert ek["ad"] == KISI_ADLI_DOSYA  # özgün ad kartta (kaydın kendisinde) görünür
        assert _rol_yetkisiz(yukle(dk_raporu))
        ret = yukle(acilis)
        assert ret.status_code == 400 and gk.DOSYA_EKI_MADDESI_DEGIL in str(ret.json())
    with o.rol_olarak(AccountRole.MUDUR):
        assert _rol_yetkisiz(yukle(yk_raporu))
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        assert _rol_yetkisiz(yukle(yk_raporu))
        _yanit(yukle(dk_raporu, "audit-board-attachment"), 201)
        assert _rol_yetkisiz(yukle(yk_raporu, "audit-board-attachment"))
        indir = APIClient().get(f"{API}/attachments/{ek['id']}/")
    assert indir.status_code == 200 and b"".join(cast(Any, indir).streaming_content) == PDF
    baslik = indir["Content-Disposition"]
    assert "Uydurma" not in baslik and "Soyad" not in baslik, baslik
    assert f"Genel-Kurul-Eki-Faaliyet-Raporu-ve-Kesin-Hesap_{_bugun()}.pdf" in baslik, baslik
    ayrinti = _yanit(_iste("GET", f"{API}/assemblies/{kurul.pk}/"))
    ekler = {m["kind"]: len(m["ekler"]) for m in ayrinti["gundem"] if m["dosya_eki_belgesi"]}
    assert ekler == {"YK_FAALIYET_RAPORU": 1, "DK_RAPORU": 1, "TAHMINI_BUTCE": 0}


def test_gelen_giden_evrak_defter_secimi_ve_kayit() -> None:
    """M10: defter (geçişteki son sıra no ile) ve gelen kayıt; sıra atlama uyarı + gerekçe; müdür ve
    Denetleme Kurulu okur, yazamaz."""
    g.acik_donem()
    defter = _yanit(_iste("POST", f"{API}/document-books/", {"last_no_before_program": 12}), 201)
    assert defter["siradaki_no"] in (1, 13)
    defterler = _yanit(_iste("GET", f"{API}/document-books/"))
    assert defterler["varsayilan"] == defter["id"]
    govde = {
        "direction": "GELEN",
        "tarih": "2026-10-01",
        "counterparty": "Uydurma Kurum",
        "subject": "Uydurma konu",
        "defter": defter["id"],
    }
    with o.rol_olarak(AccountRole.MUHASIP):
        kayit = _yanit(_iste("POST", f"{API}/document-records/", govde), 201)["kayit"]
    atlama = {**govde, "record_no": kayit["record_no"] + 5}
    ret = _iste("POST", f"{API}/document-records/", atlama)
    assert ret.status_code == 400 and ret.json()["code"] == "gerekce_gerekli"
    _yanit(_iste("POST", f"{API}/document-records/", {**atlama, "gerekce": GEREKCE}), 201)
    for rol in (AccountRole.MUDUR, AccountRole.DENETLEME_KURULU):
        with o.rol_olarak(rol):
            assert _rol_yetkisiz(_iste("POST", f"{API}/document-records/", govde))
            liste = _yanit(_iste("GET", f"{API}/document-records/?book={defter['id']}"))
        assert [k["counterparty"] for k in liste] == ["Uydurma Kurum", "Uydurma Kurum"]


def _madde_ekleri(madde: AgendaItem) -> Any:
    return Attachment.objects.filter(owner_type="oab.AgendaItem", owner_id=str(madde.pk))


def test_dosya_eki_cikarilan_maddeye_ve_kapanan_genel_kurula_eklenmez() -> None:
    """`genel_kurul.dosya_eki_ekle`'nin iki ret kolu: oylamayla çıkarılan madde (md. 9/4;
    `MADDE_CIKARILMIS`) ve ek yazılamayan durum (tutanağı tamamlanan genel kurul; `DURUM_GECERSIZ`).
    Madde eksiz kalır."""
    kurul = g.yapilmis_olagan()
    butce = g.madde(kurul, "TAHMINI_BUTCE")
    gk.gundemden_madde_cikar(butce, change_votes_for=50, change_votes_against=5)
    ret = _ek_yukle(f"{API}/agenda-items/{butce.pk}/attachments/")
    assert ret.status_code == 400 and gk.MADDE_CIKARILMIS in str(ret.json()), ret.content
    assert not _madde_ekleri(butce).exists()

    # Tutanak tamamlanınca ek yazılmaz (`_EK_YAZILABILIR`).
    gk.tutanagi_tamamla(kurul, gerekce=g.GEREKCE)
    rapor = g.madde(kurul, "YK_FAALIYET_RAPORU")
    ret = _ek_yukle(f"{API}/agenda-items/{rapor.pk}/attachments/")
    assert ret.status_code == 400 and gk.DURUM_GECERSIZ in str(ret.json()), ret.content
    assert not _madde_ekleri(rapor).exists()


def test_ek_indirme_ucu_uretilen_evraki_ve_imhali_eki_vermez() -> None:
    """İndirme ucu yalnız kullanıcı eklerini verir (`_EK_SAHIPLERI`): üretilen evrakın dosyası basım
    yolundadır (okuma satırı ve `BASIM` izi orada); bu uçtan 404, `BASIM` satırı yazılmaz. İmha edilen
    ek 404; HEAD dosya vermez (405)."""
    kurul = g.ilanli_olagan()
    with o.rol_olarak(AccountRole.SEKRETER):
        e05 = _yanit(
            _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e05/", {"toplanti": "BIRINCI"}),
            201,
        )["evrak"]
    uretilen = GeneratedDocument.objects.get(pk=e05["id"]).ekler().first()
    assert uretilen is not None
    basim = AuditTrail.objects.filter(action=AuditAction.BASIM).count()
    assert APIClient().get(f"{API}/attachments/{uretilen.pk}/").status_code == 404
    assert AuditTrail.objects.filter(action=AuditAction.BASIM).count() == basim

    butce = g.madde(kurul, "TAHMINI_BUTCE")
    ek = _yanit(_ek_yukle(f"{API}/agenda-items/{butce.pk}/attachments/"), 201)
    assert APIClient().head(f"{API}/attachments/{ek['id']}/").status_code == 405
    assert APIClient().get(f"{API}/attachments/{ek['id']}/").status_code == 200
    # Program dışı imha taklidi (KVKK imhası F4-F6'dadır): satır kalır, dosya verilmez.
    Attachment.objects.filter(pk=ek["id"]).update(
        purged_at=timezone.now(), key_wrap="", original_name=""
    )
    assert APIClient().get(f"{API}/attachments/{ek['id']}/").status_code == 404


def test_giden_evrak_kaydi_yalniz_gecerli_e12_ve_yalniz_giden() -> None:
    """E12'nin evrak kaydının sert engelleri (tek kaynak; hesap bütünlüğü): E12 dışındaki belge (E10;
    kişi adı taşır) önerilmez ve kaydedilmez; yeniden üretilen E12'nin eski sürümü kaydedilmez;
    üretilen yazı gelen evrak olarak bağlanmaz. Hiçbirinde kayıt yazılmaz."""
    kurul = _ibra_edilmemis_kurul()
    gelen_giden_evrak.evrak_defteri_olustur()
    e10 = _yanit(_iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e10/", {}), 201)["evrak"]
    govde = {"tarih": "2026-11-06", "counterparty": "Uydurma Müdürlük", "subject": "Uydurma"}
    gecersiz = gelen_giden_evrak.URETILEN_EVRAK_GECERSIZ
    ret = _iste("GET", f"{API}/documents/{e10['id']}/outgoing-record/")
    assert ret.status_code == 400 and gecersiz in str(ret.json()), ret.content
    ret = _iste("POST", f"{API}/documents/{e10['id']}/outgoing-record/", govde)
    assert ret.status_code == 400 and gecersiz in str(ret.json()), ret.content

    eski = _yanit(_iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e12/", {}), 201)["evrak"]
    yeni = _yanit(_iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e12/", {}), 201)["evrak"]
    assert eski["id"] != yeni["id"]
    ret = _iste("POST", f"{API}/documents/{eski['id']}/outgoing-record/", govde)
    assert ret.status_code == 400 and gecersiz in str(ret.json()), ret.content

    with pytest.raises(ValueError, match=gelen_giden_evrak.URETILEN_EVRAK_YALNIZ_GIDENDE):
        gelen_giden_evrak.evrak_kaydet(
            direction="GELEN",
            tarih=date(2026, 11, 6),
            counterparty="Uydurma Müdürlük",
            subject="Uydurma",
            generated_document=GeneratedDocument.objects.get(pk=yeni["id"]),
        )
    assert not DocumentRecord.objects.exists()


def test_veli_adli_cikti_giden_evrak_olarak_kaydedilmez() -> None:
    """Veli adlı E07 (`personal_list`; R9) giden evrak defterine bağlanmaz: öneri de kayıt da 400,
    kayıt yazılmaz."""
    g.veli_aktar([("UYDURMA VELİ", "9-A")])
    kurul = g.ilanli_olagan()
    gelen_giden_evrak.evrak_defteri_olustur()
    adli = _iste("POST", f"{API}/assemblies/{kurul.pk}/documents/e07/named/", {"bicim": "pdf"})
    assert adli.status_code == 200, adli.content[:300]
    kayit = GeneratedDocument.objects.get(personal_list=True)
    govde = {"tarih": "2026-10-05", "counterparty": "Uydurma Müdürlük", "subject": "Uydurma"}
    gecersiz = gelen_giden_evrak.URETILEN_EVRAK_GECERSIZ
    ret = _iste("GET", f"{API}/documents/{kayit.pk}/outgoing-record/")
    assert ret.status_code == 400 and gecersiz in str(ret.json()), ret.content
    ret = _iste("POST", f"{API}/documents/{kayit.pk}/outgoing-record/", govde)
    assert ret.status_code == 400 and gecersiz in str(ret.json()), ret.content
    assert not DocumentRecord.objects.exists()


def test_gelen_giden_evrak_eki_indirme_adi_ve_liste_suzgeci() -> None:
    """Evrak kaydının eki (taranmış evrak) kayıt numarasıyla indirilir; özgün ad (velinin dilekçesi
    kişi adı taşıyabilir) dosya adına girmez. Listenin süzgeci biçimsiz değerde 400 ve sözlükteki
    iletiyle döner: "²" gibi ASCII olmayan rakamlarda da (500 değil); tanınmayan yön boş liste değil
    400."""
    g.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    govde = {
        "direction": "GELEN",
        "tarih": "2026-10-01",
        "counterparty": "Uydurma Kurum",
        "subject": "Uydurma konu",
    }
    kayit = _yanit(_iste("POST", f"{API}/document-records/", govde), 201)["kayit"]
    ek = _yanit(
        _ek_yukle(
            f"{API}/document-records/{kayit['id']}/attachments/", "Uydurma Veli dilekçesi.pdf"
        ),
        201,
    )
    with o.rol_olarak(AccountRole.MUDUR):
        indir = APIClient().get(f"{API}/attachments/{ek['id']}/")
    assert indir.status_code == 200
    baslik = indir["Content-Disposition"]
    assert "Uydurma" not in baslik and "Veli" not in baslik, baslik
    beklenen = f"Gelen-Giden-Evrak-Eki-{kayit['year']}-{kayit['record_no']}_{_bugun()}.pdf"
    assert beklenen in baslik, baslik

    for sorgu, ileti in (
        ("year=%C2%B2", "Yıl geçersiz."),
        ("year=abc", "Yıl geçersiz."),
        ("book=%C2%B3", "Defter geçersiz."),
        ("direction=YANLIS", gelen_giden_evrak.YON_GECERSIZ),
    ):
        ret = APIClient().get(f"{API}/document-records/?{sorgu}")
        assert ret.status_code == 400 and ileti in str(ret.json()), (sorgu, ret.content)
    assert len(_yanit(_iste("GET", f"{API}/document-records/?direction=GELEN&year=2026"))) == 1
    # F1c'nin dönem parametresi de aynı tuzaktaydı: "²" 400 (500 değil).
    ret = APIClient().get(f"{API}/memberships/?term=%C2%B2&organ=YONETIM_KURULU")
    assert ret.status_code == 400, ret.content


def test_genel_uyelik_iptali_genel_kurul_kaydini_genel_kurulun_kapilarina_birakir() -> None:
    """Plan F2 §10.2 madde 26 (en dar seçenek): F1c'nin genel iptali (`oab-membership-cancel`) genel
    kurulun seçtiği üyeyi ve divanı iptal etmez (seçimin iptali ve divanın düzeltilmesi genel kurulun
    kendi uçlarıdır; S6 (i) tek kaynak); gündem maddesinin sonucu değişmez. Genel kurulun adayını
    yalnız adayı kaydeden roller (§7.1 "Kim") ve seçimin sonucu girilmeden iptal eder."""
    kurul = g.yapilmis_olagan()
    gk.divan_sec(kurul, baskan=o.kisi(), katip=o.kisi())
    yk = [g.aday(kurul) for _ in range(5)]
    secilen = g.secim(kurul, "SECIM_YK", yk).secilenler[0]
    divan = gk.kurulun_divani(kurul)[0]
    iptal = {"cancel_reason": "Uydurma yanlış kayıt."}
    seceni = uyelik_gecisleri.GENEL_KURUL_SECILENI_IPTALI
    with o.rol_olarak(AccountRole.MUHASIP):
        ret = APIClient().post(f"{API}/memberships/{secilen.pk}/cancel/", iptal, format="json")
    assert ret.status_code == 400 and seceni in str(ret.json()), ret.content
    ret = APIClient().post(f"{API}/memberships/{divan.pk}/cancel/", iptal, format="json")
    assert ret.status_code == 400 and seceni in str(ret.json()), ret.content
    assert g.madde(kurul, "SECIM_YK").result
    durumlar = {u.status for u in gk.kurulun_divani(kurul)}
    durumlar.add(type(secilen).objects.get(pk=secilen.pk).status)
    assert durumlar == {"SECILDI"}

    # Sonucu girilmiş kurulun sonradan kaydedilen adayı: sonuç seçimin iptaliyle düzelir.
    gec = g.aday(kurul)
    ret = APIClient().post(f"{API}/memberships/{gec.pk}/cancel/", iptal, format="json")
    assert ret.status_code == 400 and gk.GENEL_KURUL_ADAYI_IPTALI in str(ret.json()), ret.content
    # Sonucu girilmemiş kurulun (Denetleme Kurulu) adayı: muhasip iptal edemez, sekreter eder.
    dk_adayi = g.aday(kurul, organ="DK")
    with o.rol_olarak(AccountRole.MUHASIP):
        ret = APIClient().post(f"{API}/memberships/{dk_adayi.pk}/cancel/", iptal, format="json")
    assert _rol_yetkisiz(ret), ret.content
    with o.rol_olarak(AccountRole.SEKRETER):
        ret = APIClient().post(f"{API}/memberships/{dk_adayi.pk}/cancel/", iptal, format="json")
    assert ret.status_code == 200 and ret.json()["status"] == "IPTAL", ret.content
    # Genel kurulun kendi yolu açıktır: seçimin iptali seçilenleri iptal eder, sonucu boşaltır.
    iptaller = gk.secimi_iptal_et(g.madde(kurul, "SECIM_YK"), cancel_reason="Uydurma yanlış sonuç.")
    assert len(iptaller) == 5 and not g.madde(kurul, "SECIM_YK").result


# ============================================================ oturumun eylemleri (ekranın süzmesi; 11b)


def _oturum(pk: int) -> dict[str, Any]:
    return cast(dict[str, Any], _yanit(_iste("GET", f"{API}/assemblies/{pk}/"))["oturum"])


def test_oturumun_cagiranlari_ve_uretilebilir_belgeleri_rolun_kapisindan_gelir() -> None:
    """Ayrıntının `oturum` alanı (plan F2 11b): ön yüz rol adıyla dallanmaz, çağrı penceresinin
    seçeneklerini ve belge kartlarının "Belgeyi oluştur"unu buradan okur. Değerler yazmanın kendi
    kapısından (`_cagri_kapisi`, `_uretim_yetkisi`) gelir; okuma yazmaz."""
    g.acik_donem()
    olagan = g.planla()
    olaganustu = g.planla(AssemblyKind.OLAGANUSTU, g.an(date(2026, 12, 10)))
    beklenen_olagan = {
        AccountRole.YONETICI: [],
        AccountRole.SEKRETER: [{"called_by": "YONETIM_KURULU", "yol": "genel"}],
        AccountRole.BASKAN: [],
        AccountRole.MUDUR: [],
        AccountRole.DENETLEME_KURULU: [],
    }
    beklenen_olaganustu = {
        AccountRole.YONETICI: [{"called_by": "UYE_BASVURUSU", "yol": "genel"}],
        AccountRole.SEKRETER: [{"called_by": "YONETIM_KURULU", "yol": "genel"}],
        AccountRole.BASKAN: [{"called_by": "BASKAN_VEYA_MUDUR_13_8", "yol": "genel"}],
        AccountRole.MUDUR: [
            {"called_by": "OKUL_MUDURU", "yol": "mudur"},
            {"called_by": "BASKAN_VEYA_MUDUR_13_8", "yol": "mudur"},
            {"called_by": "MUDUR_25_2", "yol": "mudur"},
        ],
        AccountRole.DENETLEME_KURULU: [{"called_by": "DENETLEME_KURULU", "yol": "dk"}],
    }
    for rol, cagiranlar in beklenen_olagan.items():
        with o.rol_olarak(rol):
            izler = AuditTrail.objects.count()
            assert _oturum(olagan.pk)["cagiranlar"] == cagiranlar, rol
            # Çağrılmamış genel kurulda E05'in kolu yoktur (`CAGRI_YOK`).
            assert "E05" not in _oturum(olagan.pk)["uretilebilir_belgeler"], rol
            assert {(c["called_by"], c["yol"]) for c in _oturum(olaganustu.pk)["cagiranlar"]} == {
                (c["called_by"], c["yol"]) for c in beklenen_olaganustu[rol]
            }, rol
            assert AuditTrail.objects.count() == izler, rol  # okuma yazmaz

    # Çağrıdan sonra çağıran listesi boşalır; belgeler rolün "Üreten"inden (tasarım §9.6).
    g.olagan_cagir(olagan)
    for rol, belgeler in (
        (
            AccountRole.YONETICI,
            {"E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E64"},
        ),
        (AccountRole.SEKRETER, {"E05", "E06", "E07", "E08", "E09", "E10", "E11", "E13", "E64"}),
        (AccountRole.BASKAN, set()),
        (AccountRole.MUDUR, set()),
        (AccountRole.DENETLEME_KURULU, set()),
    ):
        with o.rol_olarak(rol):
            oturum = _oturum(olagan.pk)
        assert oturum["cagiranlar"] == [], rol
        assert set(oturum["uretilebilir_belgeler"]) == belgeler, rol
        assert "E04" not in oturum["uretilebilir_belgeler"]
