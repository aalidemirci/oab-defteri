"""İzsiz yazım taraması ve kaydın özeti kapısı (TK16; tasarım §4.6.2, §14 F1b kapısı; plan F1b-1).

Plan F1b-1 "Denetim izi": okul çekirdeğinin bütün yazma servisleri izlidir; kişi silme ve
birleştirme 5. adımda yeniden yazılacağı için izsiz yazım taramasında ADIYLA muaftır.
Yeni bir izsiz yazma yolu eklenince bu dosyadaki testlerden en az biri düşer:

1. **Yazma uçları, çalışma anında** — URL desenleri dolaşılır (`_api_uclari`); her
   yazma yöntemi (POST, PUT, PATCH, DELETE) ya `IZLI_UCLAR`'da bir senaryoyla ya da
   `MUAF_UCLAR`'da gerekçesiyle durur. İki küme ile uçlar birebir eşit olmalıdır: yeni uç
   sınıflandırılmadan test düşer. İzli her uç gerçek istekle (ara katmanlar dahil: yazar
   bağlamı istek başında kurulur) sürülür; başarılı yanıttan sonra en az bir yeni iz
   satırı, beklenen türlerle, beklenen hesabın adına düşmüş olmalı; satırların içerik
   MAC'i kaydın bugünkü değerini tutmalı ve zincir bütün olmalıdır. Üstelik uçtan önce ve
   sonra okul tablolarının bütün satırları karşılaştırılır: değişen, eklenen ya da silinen
   HER kaydın bu istekte yazılmış bir iz satırı olmalı ve kayıt bütünlüğü (`kaydi_dogrula`)
   tutmalıdır — iki kayıt yazıp birini izleyen uç düşer.
2. **Kaynak taraması** — `apps/` altındaki bütün uygulamalar, `shared` ve masaüstü kabuğu
   (testler ve göçler hariç; modeller DAHİL) AST ile taranır: ORM yazma çağrısı (kural
   `_orm_yazimi_mi`'de: `update`, `create`, `delete`, modelin adlı yazım ilkeleri… HER
   alıcıda — queryset değişkeni, ilişki yöneticisi, seçicinin queryset'i) taşıyan her birim
   ya yazıcıyı (`denetim_izi.kayit`, `olay`, `degisiklik`, `kilit_olayi`, `basim`) doğrudan ya da `SAF_IZ_YARDIMCILARI`'nda
   ADIYLA duran bir yardımcıyla çağırmalı, ya izi çağıranları düşen modüle özel bir
   yardımcı olmalı (kurallar `_tara`'da) ya da `MUAF_ISLEVLER`'de (plan muafiyeti) ya da
   `ILKELLER`'de (yazıcı ve model ilkelleri) adıyla durmalıdır. Çağrılar (modül, işlev)
   çiftiyle eşlenir, ada göre DEĞİL: görünümün `delete` yöntemi bir ORM `.delete()`
   çağrısını izli kılmaz. Aynı adlı ORM dışı çağrılar (`set.update`, `hashlib…update`, salt
   okuyan `PRAGMA`) `ORM_DISI_CAGRILAR`'da adıyla ve gerekçesiyle durur. Uçtan sürülmeyen
   yollar (gün işi, konsol komutu, iç yardımcı) da böylece kapsanır. Ham SQL yazım sayılır;
   tek istisna kaynakta sabit `SELECT` metniyle çağrılan `execute`'tur (salt okuma: geri
   yükleme notunun kenara alınacak veritabanından zincir başını okuması). Kalan sınır:
   kaynak taraması yazılan kayıtla izlenen kaydın AYNI kayıt olduğunu göremez (veri akışı);
   uçlar için bunu madde 1'in tablo karşılaştırması yakalar.
3. **Kaydın özeti (R1)** — tasarım §4.6.2 kural 6 ve §14 F1b kapısı: "denetim izinde
   uydurma kişisel veri sıfır". Her izli model uydurma ad, telefon, T.C. kimlik no, adres
   ve serbest metinle yazılır, güncellenir, durumu değişir; sonra `AuditTrail`'in BÜTÜN
   sütunlarında bu değerler aranır — sonuç sıfır. Arşiv paketinin "denetim izi dökümü"
   (§8.5) henüz yoktur (F4); döküm gelince aynı arama ona da uygulanır. KVKK silmesi
   (`KVKK_SILME`, `denetim_izi.kvkk_silme`) bugün yalnız erişim günlüğünün saklama süresi
   silmesindedir (`apps.okul.erisim_gunlugu`; uydurma veriyle araması
   `test_erisim_gunlugu.py`'de); kişi silmenin satırı dönem kapanışıyla ve 5. adımla gelir,
   bugün kişi silme izsizdir (muafiyet).

ERİŞİM GÜNLÜĞÜ (`AccessLog`, tasarım §4.6.4) ZİNCİR DIŞIDIR: yazıcısı (`erisim_gunlugu.yaz`)
iz satırı yazmaz ve `MUAF_ISLEVLER`'de adıyla durur; model izin listesi taşımaz
(`LISTESIZ_MODELLER`). Uçların tablo karşılaştırmasında erişim günlüğünün yalnız EKLENEN
satırı izsiz geçer; silinen ya da değişen satırı ucu düşürür (`_YALNIZ_EKLENEN`). Saklama
süresi silmesi İZLİDİR: `KVKK_SILME` satırını yazıcının `kvkk_silme` girişiyle aynı işlemde
yazar; modelin silme ilkesi (`_AccessLogQuerySet._saklama_disini_sil`) `ILKELLER`'dedir, ilkelin
çağrısı bu taramada yazım sayılır (`_ILKEL_YAZIMLARI`). Bu tarama izli bir işlevin BÜTÜN
yazımlarını izli sayar: erişim günlüğüne doğrudan yazımı ve silmeyi izli işlevde de yakalayan
kaynak taraması (tek yazar `yaz`, tek silme yolu `suresi_dolanlari_sil`)
`test_erisim_gunlugu.py`'dedir.

Kişi adları, numaralar ve adresler UYDURMADIR.
"""

from __future__ import annotations

import ast
import json
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any

import desktop
import pytest
from desktop.backup_crypto import BOS_YEREL_MANIFESTO
from django.apps import apps as django_apps
from django.db import connection, transaction
from django.urls import URLPattern, URLResolver, get_resolver
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.test import APIClient

from apps.okul import denetim_izi, erisim_gunlugu, iz_durumu
from apps.okul.excel_ogrenci import ParserError
from apps.okul.models import (
    AccessKind,
    AccessLog,
    Account,
    AccountRole,
    AccountStatus,
    Attachment,
    AttachmentSensitivity,
    AuditTrail,
    ClassSection,
    Holiday,
    ImportRun,
    Personnel,
    SchoolConfig,
    SchoolTerm,
    SchoolYear,
    Student,
    SuspendReason,
)
from apps.okul.services import app_password, dosya_deposu, encrypted_backup, persons
from apps.okul.services import calendar as calendar_service
from apps.okul.services import imports as import_service
from apps.okul.services import school_year as school_year_service
from apps.okul.services import sections as section_service
from apps.okul.services import setup as setup_service
from apps.okul.services import terms as term_service
from apps.okul.services.templates import STUDENT_TEMPLATE_HEADERS
from apps.okul.tests.hesap_ortak import GECICI_PAROLA, YENI_PAROLA, hesap_ac, muhurle
from conftest import (
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    oturumu_ac_test,
    varsayilan_yazar,
)
from shared import crypto

YAZMA_YONTEMLERI = ("post", "put", "patch", "delete")
#: `backend/` kökü (kaynak taraması buradan göreli yol yazar).
KOK = Path(__file__).resolve().parents[3]

OGRENCI_BASLIGI = "Sınıf\tOkul No\tAdı Soyadı"
PERSONEL_BASLIGI = "Adı\tSoyadı\tGörevi\tBranşı"


# ============================================================ uçların dolaşılması


def _desenler(
    resolver: URLResolver | None = None, onek: str = ""
) -> Iterator[tuple[str, URLPattern]]:
    kok = resolver if resolver is not None else get_resolver()
    for desen in kok.url_patterns:
        yol = onek + str(desen.pattern)
        if isinstance(desen, URLResolver):
            yield from _desenler(desen, yol)
        else:
            yield yol, desen


def _yazma_uclari() -> set[tuple[str, str]]:
    """Adlı `/api/` uçlarının desteklediği her yazma yöntemi: (ad, YÖNTEM)."""
    uclar: set[tuple[str, str]] = set()
    for yol, desen in _desenler():
        if not yol.startswith("api/"):
            continue
        gorunum = getattr(desen.callback, "view_class", None) or getattr(
            desen.callback, "cls", None
        )
        for yontem in YAZMA_YONTEMLERI:
            if hasattr(gorunum, yontem):
                uclar.add((str(desen.name), yontem.upper()))
    return uclar


# ============================================================ senaryolar


@dataclass(frozen=True)
class Istek:
    """Sürülecek istek ve beklenen iz: türler kümesi birebir, satırların hesabı."""

    yol: str
    govde: dict[str, Any] | None
    beklenen: frozenset[str]
    #: Satırların hesabı; None: isteğin açtığı yeni hesap (ilk hesap).
    hesap: str | None = TEST_HESAP_ID


@dataclass(frozen=True)
class Senaryo:
    """Ucun hazırlığı (iz satırları sayımdan önce yazılır) ve ortamı."""

    kur: Callable[[pytest.MonkeyPatch], Istek]
    #: "acik" (varsayılan oturum) · "kilitli" · "parolasiz" (hesap kurulmamış ilk açılış).
    ortam: str = "acik"


def _turler(*adlar: str) -> frozenset[str]:
    return frozenset(adlar)


def _yil(ad: str = "2026-2027", *, aktif: bool = True, kayma: int = 0) -> SchoolYear:
    return school_year_service.create_school_year(
        name=ad,
        start_date=date(2026 + kayma, 9, 7),
        end_date=date(2027 + kayma, 6, 25),
        activate=aktif,
    )


def _ogrenci(**alanlar: Any) -> Student:
    varsayilan: dict[str, Any] = {
        "first_name": "Uydurcan",
        "last_name": "Örnekoğlu",
        "student_number": "501",
        "class_level": 9,
        "class_section": "A",
    }
    return persons.create_student(**{**varsayilan, **alanlar})


def _personel() -> Personnel:
    return persons.create_personnel(first_name="Uydurnur", last_name="Örnekkaya")


def _kurtarma_damgasi() -> None:
    """Kurtarma anahtarı saklandı damgası (test verisi; servisi ayrı senaryoda sürülür)."""
    yol = app_password.state_path()
    durum = json.loads(yol.read_text(encoding="utf-8"))
    durum["kurtarma"][app_password.RECOVERY_CONFIRMED_FIELD] = "2026-11-01T10:00:00+03:00"
    yol.write_text(json.dumps(durum, ensure_ascii=False, indent=2), encoding="utf-8")


def _kurulum(_: pytest.MonkeyPatch) -> Istek:
    _kurtarma_damgasi()
    setup_service.update_school_config(
        fields={
            "school_name": "Uydurma Ortaokulu",
            "kademe": "ORTAOKUL",
            "kisa_ad": "Uydurma OO",
            "demirbas_onayi": True,
        }
    )
    term_service.configure_terms(_yil(), first_end=date(2027, 1, 22), second_start=date(2027, 2, 8))
    return Istek("/api/v1/setup/complete/", None, _turler("DURUM"))


def _donemler(_: pytest.MonkeyPatch) -> Istek:
    yil = _yil()
    return Istek(
        f"/api/v1/school-years/{yil.pk}/terms/",
        {"first_term_end": "2027-01-22", "second_term_start": "2027-02-08"},
        _turler("OLUSTUR"),
    )


def _aktiflestir(_: pytest.MonkeyPatch) -> Istek:
    _yil()
    ikinci = _yil("2027-2028", aktif=False, kayma=1)
    return Istek(f"/api/v1/school-years/{ikinci.pk}/activate/", None, _turler("DURUM"))


def _kapali_gun_sil(_: pytest.MonkeyPatch) -> Istek:
    gun = calendar_service.create_holiday(
        name="Uydurma idari izin",
        start_date=date(2026, 11, 20),
        end_date=date(2026, 11, 20),
        kind="OTHER",
    )
    return Istek(f"/api/v1/holidays/{gun.pk}/", None, _turler("DURUM"))


def _ogrenci_guncelle_tam(_: pytest.MonkeyPatch) -> Istek:
    ogrenci = _ogrenci()
    govde = {
        "first_name": "Uydurcan",
        "last_name": "Örnekoğlu",
        "student_number": "501",
        "class_level": 9,
        "class_section": "B",
    }
    return Istek(f"/api/v1/students/{ogrenci.pk}/", govde, _turler("GUNCELLE"))


def _ogrenci_guncelle(_: pytest.MonkeyPatch) -> Istek:
    return Istek(f"/api/v1/students/{_ogrenci().pk}/", {"class_section": "B"}, _turler("GUNCELLE"))


def _personel_guncelle_tam(_: pytest.MonkeyPatch) -> Istek:
    govde = {"first_name": "Uydurnur", "last_name": "Örnekkaya", "member_kind": "STAFF"}
    return Istek(f"/api/v1/personnel/{_personel().pk}/", govde, _turler("GUNCELLE"))


def _personel_guncelle(_: pytest.MonkeyPatch) -> Istek:
    return Istek(
        f"/api/v1/personnel/{_personel().pk}/", {"member_kind": "STAFF"}, _turler("GUNCELLE")
    )


def _havuz_karari(_: pytest.MonkeyPatch) -> Istek:
    ogrenci = _ogrenci()
    persons.add_to_leave_pool(ogrenci, run=None)
    return Istek(
        "/api/v1/leave-pool/resolve/", {"students": {"keep": [ogrenci.pk]}}, _turler("DURUM")
    )


def _sube_ekle(_: pytest.MonkeyPatch) -> Istek:
    govde = {"school_year": _yil().pk, "class_level": 9, "class_section": "A"}
    return Istek("/api/v1/class-sections/", govde, _turler("OLUSTUR"))


def _sube_sil(_: pytest.MonkeyPatch) -> Istek:
    sube = section_service.create_class_section(
        school_year=_yil(), class_level=9, class_section="A"
    )
    return Istek(f"/api/v1/class-sections/{sube.pk}/", None, _turler("DURUM"))


def _ogrenci_listesi() -> dict[str, Any]:
    return {"text": "\n".join([OGRENCI_BASLIGI, "9/A\t501\tUYDURCAN ÖRNEKOĞLU"])}


def _personel_listesi() -> dict[str, Any]:
    return {"text": "\n".join([PERSONEL_BASLIGI, "UYDURNUR\tÖRNEKKAYA\tÖğretmen\t"])}


def _sifreli_yedek(monkeypatch: pytest.MonkeyPatch) -> Istek:
    # Görüntü sabit baytlardır: açık test işleminin dosyasından ayrı bağlantıyla okunmaz.
    monkeypatch.setattr(
        encrypted_backup,
        "goruntu_ve_manifesto",
        lambda _yol: (b"SQLite format 3\0", BOS_YEREL_MANIFESTO),
    )
    # Seçilen yer program dizinlerinin dışındadır: pytest'in temizlediği taban geçici dizin.
    usb = tempfile.mkdtemp(prefix="od-usb-", dir=app_password.state_path().parent.parent)
    hedef = Path(usb) / "oab-defteri-yedek-2026-11-06-101530.odbak"
    return Istek("/api/v1/backups/encrypted/", {"hedef": str(hedef)}, _turler("YEDEK"))


def _sahipsiz_sarmal(_: pytest.MonkeyPatch) -> Istek:
    """Satırı olmayan bir sarmal (geri yüklemeden sonraki hâl; tasarım §4.6.1 kural 4)."""
    sahipsiz = "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f"
    durum = json.loads(app_password.state_path().read_text(encoding="utf-8"))
    durum["hesaplar"].append({**durum["hesaplar"][0], "id": sahipsiz, "tanitici": "eski-hesap"})
    app_password._write_state(durum)
    return Istek(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [sahipsiz]}, _turler("HESAP")
    )


def _parola_bildirimi(_: pytest.MonkeyPatch) -> Istek:
    """Kurtarma anahtarıyla yenilenen parolanın bildirimi beklerken sahibinin "Gördüm"ü."""
    app_password.lock()
    app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
    )
    return Istek("/api/v1/security/integrity/reset-notice/", None, _turler("GUNCELLE"))


def _hesabi_kapat(_: pytest.MonkeyPatch) -> Istek:
    """Kullanıcılar: uydurma muhasibin hesabı kapatılır (`HESAP`; sarmalda sayaç yok)."""
    return Istek(f"/api/v1/accounts/{hesap_ac().id}/close/", None, _turler("HESAP"))


def _askidan_cikar(_: pytest.MonkeyPatch) -> Istek:
    """Kullanıcılar: üyeliği düşmüş (mühürlü, izli `ASKIDA`) uydurma muhasip askıdan çıkarılır."""
    hesap = muhurle(
        hesap_ac(), status=AccountStatus.ASKIDA, suspend_reason=SuspendReason.UYELIK_DUSTU
    )
    return Istek(f"/api/v1/accounts/{hesap.id}/unsuspend/", None, _turler("HESAP"))


def _parolayi_sifirla(_: pytest.MonkeyPatch) -> Istek:
    """Kullanıcılar: `PAROLA` ve iki aşamalı sarmal özetinin `HESAP` satırı (`hesaplar`)."""
    return Istek(
        f"/api/v1/accounts/{hesap_ac().id}/reset-password/",
        {"gecici_parola": YENI_PAROLA},
        _turler("PAROLA", "HESAP"),
    )


def _teslim_pusulasi(_: pytest.MonkeyPatch) -> Istek:
    """Kullanıcılar: uydurma muhasibin hesap teslim pusulası (E63) — tek izi `BASIM` satırıdır
    (dosya saklanmaz; hesap satırı değişmez)."""
    return Istek(f"/api/v1/accounts/{hesap_ac().id}/handover-slip/", None, _turler("BASIM"))


def _geri_yuklemeyi_gordum(_: pytest.MonkeyPatch) -> Istek:
    """Denetleme Kurulu: geri yükleme kartının "Gördüm"ü — tek izi `ISARET` satırıdır (kaydı
    denetim izinin kendi satırı; hiçbir tablo değişmez). Oturum uydurma DK üyesinindir."""
    dk = muhurle(
        hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi"), status=AccountStatus.ACIK
    )
    with transaction.atomic():
        geri = denetim_izi.olay(
            "GERI_YUKLEME",
            model=denetim_izi.GERI_YUKLEME_KAYDI,
            object_id="db-onceki-2026-11-01-091000.sqlite3",
        )
    oturumu_ac_test(str(dk.id), tanitici=dk.login_name, rol=AccountRole.DENETLEME_KURULU.value)
    return Istek(
        "/api/v1/security/integrity/restore-seen/",
        {"seq": geri.seq},
        _turler("ISARET"),
        hesap=str(dk.id),
    )


def _sabit(yol: str, govde: dict[str, Any] | None, *turler: str) -> Senaryo:
    return Senaryo(lambda _m: Istek(yol, govde, _turler(*turler)))


def _istek(fabrika: Callable[[], Istek], ortam: str = "acik") -> Senaryo:
    return Senaryo(lambda _m: fabrika(), ortam)


#: İzli yazma uçları: (URL adı, yöntem) → senaryo. Beklenen türler BİREBİR karşılaştırılır.
IZLI_UCLAR: dict[tuple[str, str], Senaryo] = {
    ("setup-school-config", "PUT"): _sabit(
        "/api/v1/setup/school-config/", {"school_name": "Uydurma Ortaokulu"}, "GUNCELLE"
    ),
    ("setup-complete", "POST"): Senaryo(_kurulum),
    ("setup-roadmap", "POST"): _sabit(
        "/api/v1/setup/roadmap/", {"item": "kurtarma_zarfi", "done": True}, "GUNCELLE"
    ),
    ("school-year-list", "POST"): _sabit(
        "/api/v1/school-years/",
        {"name": "2027-2028", "start_date": "2027-09-06", "end_date": "2028-06-23"},
        "OLUSTUR",
    ),
    ("school-year-terms", "PUT"): Senaryo(_donemler),
    ("school-year-activate", "POST"): Senaryo(_aktiflestir),
    ("holiday-list", "POST"): _sabit(
        "/api/v1/holidays/",
        {
            "name": "Uydurma idari izin",
            "start_date": "2026-11-20",
            "end_date": "2026-11-20",
            "kind": "OTHER",
        },
        "OLUSTUR",
    ),
    ("holiday-seed", "POST"): _sabit("/api/v1/holidays/seed/", {"year": 2026}, "OLUSTUR"),
    ("holiday-detail", "DELETE"): Senaryo(_kapali_gun_sil),
    ("student-list", "POST"): _sabit(
        "/api/v1/students/",
        {
            "first_name": "Uydurcan",
            "last_name": "Örnekoğlu",
            "student_number": "501",
            "class_level": 9,
            "class_section": "A",
        },
        "OLUSTUR",
    ),
    ("student-detail", "PUT"): Senaryo(_ogrenci_guncelle_tam),
    ("student-detail", "PATCH"): Senaryo(_ogrenci_guncelle),
    ("student-leave", "POST"): _istek(
        lambda: Istek(f"/api/v1/students/{_ogrenci().pk}/leave/", None, _turler("DURUM"))
    ),
    ("personnel-list", "POST"): _sabit(
        "/api/v1/personnel/", {"first_name": "Uydurnur", "last_name": "Örnekkaya"}, "OLUSTUR"
    ),
    ("personnel-detail", "PUT"): Senaryo(_personel_guncelle_tam),
    ("personnel-detail", "PATCH"): Senaryo(_personel_guncelle),
    ("personnel-leave", "POST"): _istek(
        lambda: Istek(f"/api/v1/personnel/{_personel().pk}/leave/", None, _turler("DURUM"))
    ),
    ("leave-pool-resolve", "POST"): Senaryo(_havuz_karari),
    ("class-section-list", "POST"): Senaryo(_sube_ekle),
    ("class-section-detail", "DELETE"): Senaryo(_sube_sil),
    # Önizlemenin kayıt yazımları geri sarılır; kalıcı olan yalnız PREVIEWED koşusudur.
    ("import-students-preview", "POST"): _istek(
        lambda: Istek("/api/v1/imports/students/preview/", _ogrenci_listesi(), _turler("OLUSTUR"))
    ),
    ("import-students-commit", "POST"): _istek(
        lambda: Istek(
            "/api/v1/imports/students/commit/", _ogrenci_listesi(), _turler("OLUSTUR", "DURUM")
        )
    ),
    ("import-personnel-preview", "POST"): _istek(
        lambda: Istek("/api/v1/imports/personnel/preview/", _personel_listesi(), _turler("OLUSTUR"))
    ),
    ("import-personnel-commit", "POST"): _istek(
        lambda: Istek(
            "/api/v1/imports/personnel/commit/", _personel_listesi(), _turler("OLUSTUR", "DURUM")
        )
    ),
    # İlk hesap: satırlar yeni hesabındır (plan F1b-1); okul kartı parmak iziyle oluşur.
    ("security-enable", "POST"): _istek(
        lambda: Istek(
            "/api/v1/security/enable/",
            {"tanitici": "yonetici", "ad_soyad": "Uydurma Yönetici", "parola": YENI_PAROLA},
            _turler("HESAP", "KURTARMA", "OLUSTUR"),
            hesap=None,
        ),
        "parolasiz",
    ),
    ("security-unlock", "POST"): _istek(
        lambda: Istek(
            "/api/v1/security/unlock/",
            {"hesap": TEST_HESAP_ID, "parola": TEST_PAROLA},
            _turler("GIRIS"),
        ),
        "kilitli",
    ),
    ("security-lock", "POST"): _sabit("/api/v1/security/lock/", None, "KILIT"),
    ("security-recover", "POST"): _istek(
        lambda: Istek(
            "/api/v1/security/recover/",
            {
                "kurtarma_anahtari": TEST_KURTARMA_ANAHTARI,
                "hesap": TEST_HESAP_ID,
                "yeni_parola": YENI_PAROLA,
            },
            # `HESAP`: iki aşamalı sarmal özetinin bekleyen adımı (ayrı işlem; `app_password`).
            _turler("HESAP", "KURTARMA", "GIRIS"),
        ),
        "kilitli",
    ),
    ("security-change-password", "POST"): _sabit(
        "/api/v1/security/change-password/",
        {"parola": TEST_PAROLA, "yeni_parola": YENI_PAROLA},
        "HESAP",  # iki aşamalı sarmal özetinin bekleyen adımı
        "PAROLA",
    ),
    ("security-idle-lock", "PUT"): _sabit(
        "/api/v1/security/idle-lock/", {"dakika": 15}, "GUNCELLE"
    ),
    ("security-recovery-key-confirm", "POST"): _sabit(
        "/api/v1/security/recovery-key/confirm/",
        {"recovery_key": TEST_KURTARMA_ANAHTARI},
        "KURTARMA",
    ),
    ("security-recovery-key-renew", "POST"): _sabit(
        "/api/v1/security/recovery-key/renew/", {"password": TEST_PAROLA}, "KURTARMA"
    ),
    ("encrypted-backup-download", "POST"): Senaryo(_sifreli_yedek),
    ("security-integrity-orphan-wraps", "POST"): Senaryo(_sahipsiz_sarmal),
    ("security-integrity-reset-notice", "POST"): Senaryo(_parola_bildirimi),
    ("security-integrity-restore-seen", "POST"): Senaryo(_geri_yuklemeyi_gordum),
    ("backup-external-reminder", "PUT"): _sabit(
        "/api/v1/backups/external/", {"reminder_days": 14}, "GUNCELLE"
    ),
    # Kullanıcılar (plan F1b-2): hesap açma, kapama, askıdan çıkarma, parola sıfırlama, hesap
    # teslim pusulası.
    ("account-list", "POST"): _sabit(
        "/api/v1/accounts/",
        {
            "rol": "muhasip",
            "tanitici": "muhasip",
            "ad_soyad": "Uydurma Muhasip",
            "gecici_parola": GECICI_PAROLA,
        },
        "HESAP",
    ),
    ("account-close", "POST"): Senaryo(_hesabi_kapat),
    ("account-unsuspend", "POST"): Senaryo(_askidan_cikar),
    ("account-reset-password", "POST"): Senaryo(_parolayi_sifirla),
    ("account-handover-slip", "POST"): Senaryo(_teslim_pusulasi),
    # Yedek Raporu (plan F1b-3): dosya saklanmaz, tek izi `BASIM` satırıdır.
    ("backup-report", "POST"): _sabit("/api/v1/backups/report/", None, "BASIM"),
}

#: Plan F1b-1'in adıyla muaf tuttuğu yollar: kişi silme ve birleştirme 5. adımda yeniden
#: yazılır (katı silme kaydı yok eder; `KVKK_SILME` satırı dönem kapanışıyla gelir).
PLAN_MUAFIYETI = (
    "Plan F1b-1 'Denetim izi': kişi silme ve birleştirme 5. adımda yeniden yazılacağı için "
    "izsiz yazım taramasında adıyla muaftır."
)

#: İz satırı YAZMAYAN yazma uçları ve gerekçeleri. Yeni bir uç buraya ancak gerekçesiyle girer.
MUAF_UCLAR: dict[tuple[str, str], str] = {
    ("student-detail", "DELETE"): PLAN_MUAFIYETI,
    ("personnel-detail", "DELETE"): PLAN_MUAFIYETI,
    ("personnel-merge", "POST"): PLAN_MUAFIYETI,
    ("app-quit", "POST"): (
        "Kayıt yazmaz: düzenli kapanışı başlatır. Oturum açıksa kapanış kilidi `KILIT` "
        "satırını oturumdaki hesabın adına yazar (masaüstü kancası, "
        "`oturum.kapanista_kilitle`; `test_denetim_izi.py`)."
    ),
    ("dashboard-last-session", "POST"): (
        "Kayıt yazmaz: 'Kontrol ettim' onayı süreç içidir (dosyaya ve veritabanına yazılmaz)."
    ),
    ("security-recovery-key-pdf", "POST"): (
        "Kayıt yazmaz: kurtarma anahtarı belgesinin basımı iz satırı yazmaz (plan F1b-1 "
        "'guvenlik.json şema 2'; birlik evrakı değildir, tasarım §9.7)."
    ),
    ("security-state-reset", "POST"): (
        "Yalnız hesap ve iz anahtarı YOKKEN çalışır (parmak izi ve şifreli tablolar boş): "
        "zincir yoktur, ilk hesaptan önce olay yazılmaz (plan F1b-1)."
    ),
    ("backup-restore", "POST"): (
        "Veritabanını değiştirir: satır kenara alınan veritabanına yazılamaz, yenisinde oturum "
        "yoktur. Ortak çekirdek `geri-yukleme-notu.json`'u yazar; `GERI_YUKLEME` satırı nottan "
        "ilk kilit açılışında yazılır (tasarım §4.4.4; `iz_dogrulama`, `test_iz_dogrulama.py`)."
    ),
}


def test_her_yazma_ucu_siniflandirilmistir() -> None:
    """Yeni bir yazma ucu eklendiyse: iz yazıyor mu? Senaryoyla IZLI_UCLAR'a ya da
    gerekçesiyle MUAF_UCLAR'a ekleyin (modül başlığı, madde 1)."""
    assert not set(IZLI_UCLAR) & set(MUAF_UCLAR)
    assert _yazma_uclari() == set(IZLI_UCLAR) | set(MUAF_UCLAR)
    assert all(gerekce.strip() for gerekce in MUAF_UCLAR.values())


def _son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else bas[0]


def _parametreler() -> list[Any]:
    return [
        pytest.param(
            uc,
            id=f"{uc[0]}-{uc[1]}",
            marks=[pytest.mark.hesapsiz] if senaryo.ortam == "parolasiz" else [],
        )
        for uc, senaryo in sorted(IZLI_UCLAR.items())
    ]


#: Tablo karşılaştırmasının dışında kalan okul modelleri: izin kendisi ve iz anahtarı
#: (`LISTESIZ_MODELLER`; anahtar ilk hesapla aynı işlemde yazılır).
_KARSILASTIRMA_DISI = frozenset({"AuditTrail", "AuditKey"})
#: Satırı iz satırı DOĞURMAYAN, yalnız eklenen modeller: zincir dışı erişim günlüğü (tasarım
#: §4.6.4). Eklenen satırı izsiz geçer; silinen ya da değişen satırı ucu düşürür (satır
#: değişmez, yalnız saklama süresinin gün işi siler — `KVKK_SILME`; bir uç silmez).
_YALNIZ_EKLENEN = frozenset({"okul.AccessLog"})


def _tablolar() -> dict[str, dict[str, tuple[Any, ...]]]:
    """Okul modellerinin BÜTÜN satırları, ham SQL ile: model etiketi → {kimlik metni: satır}.

    Ham okunur: şifreli sütun token'ıyla karşılaştırılır (kilitliyken de okunur, çözülmez).
    Kimlik `denetim_izi.kimlik_metni` biçimindedir (iz satırının `object_id`'siyle aynı).
    """
    sonuc: dict[str, dict[str, tuple[Any, ...]]] = {}
    for model in django_apps.get_app_config("okul").get_models():
        if model.__name__ in _KARSILASTIRMA_DISI:
            continue
        pk = model._meta.pk
        assert pk is not None
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{model._meta.db_table}"')  # noqa: S608 — sabit ad
            sutunlar = [kolon[0] for kolon in cursor.description]
            sira = sutunlar.index(pk.column)
            sonuc[denetim_izi.model_etiketi(model)] = {
                denetim_izi.kimlik_metni(model, satir[sira]): tuple(satir)
                for satir in cursor.fetchall()
            }
    return sonuc


def _degisen_kayitlar(
    once: dict[str, dict[str, tuple[Any, ...]]], sonra: dict[str, dict[str, tuple[Any, ...]]]
) -> set[tuple[str, str]]:
    """Eklenen, değişen ya da silinen kayıtlar: (model etiketi, kimlik metni)."""
    degisen: set[tuple[str, str]] = set()
    for etiket in once.keys() | sonra.keys():
        eski, yeni = once.get(etiket, {}), sonra.get(etiket, {})
        degisen |= {
            (etiket, kimlik)
            for kimlik in eski.keys() | yeni.keys()
            if eski.get(kimlik) != yeni.get(kimlik)
        }
    return degisen


def _eklenen_gunluk_satirlari(
    once: dict[str, dict[str, tuple[Any, ...]]], degisen: set[tuple[str, str]]
) -> set[tuple[str, str]]:
    """Değişenlerden yalnız eklenen erişim günlüğü satırları (önceki görüntüde olmayanlar)."""
    return {
        (etiket, kimlik)
        for etiket, kimlik in degisen
        if etiket in _YALNIZ_EKLENEN and kimlik not in once.get(etiket, {})
    }


def _izsiz_degisiklikler(
    once: dict[str, dict[str, tuple[Any, ...]]],
    sonra: dict[str, dict[str, tuple[Any, ...]]],
    izlenen: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """İzi olmayan değişiklikler: eklenen erişim günlüğü satırı dışında değişen her kayıt.

    Silinen ya da değişen erişim günlüğü satırı burada kalır: onun iz satırı yoktur
    (`KVKK_SILME`'nin kimliği boştur), uç düşer.
    """
    degisen = _degisen_kayitlar(once, sonra)
    return degisen - _eklenen_gunluk_satirlari(once, degisen) - izlenen


@pytest.mark.django_db
@pytest.mark.parametrize("uc", _parametreler())
def test_izli_yazma_ucu_iz_satiri_yazar(
    uc: tuple[str, str], request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Her izli uç gerçek istekle sürülür: yeni satırlar, türler, hesap, içerik MAC'i, zincir;
    değişen HER kaydın bu istekte iz satırı vardır ve kayıt bütünlüğü tutar (madde 1)."""
    senaryo = IZLI_UCLAR[uc]
    if senaryo.ortam == "parolasiz":
        request.getfixturevalue("parolasiz")
    istek = senaryo.kur(monkeypatch)
    if senaryo.ortam == "kilitli":
        # Düzenli kilitlenme gibi çapa yazılır (zincir varsayılan hesabın satırıyla başlar):
        # kilit açılışı çapasız zinciri "çapa yok" bulgusuyla `BUTUNLUK` satırına yazardı.
        iz_durumu.capa_yaz()
        app_password.lock()
    bas = _son_seq()
    once = _tablolar()

    yanit = APIClient().generic(
        uc[1],
        istek.yol,
        data=json.dumps(istek.govde) if istek.govde is not None else "",
        content_type="application/json",
    )

    assert 200 <= yanit.status_code < 300, (uc, yanit.status_code, yanit.content[:300])
    yeni = list(AuditTrail.objects.filter(seq__gt=bas).order_by("seq"))
    assert yeni, f"{uc}: başarılı yazma iz satırı bırakmadı"
    assert {satir.action for satir in yeni} == istek.beklenen, uc
    hesap = istek.hesap
    if hesap is None:
        hesap = str(Account.objects.get(login_name="yonetici").pk)
    for satir in yeni:
        assert satir.actor == "HESAP", (uc, satir)
        assert str(satir.account_id) == hesap, (uc, satir)
    # Değişen her kaydın bu istekte yazılmış bir iz satırı vardır (iki kayıt yazıp birini
    # izleyen uç burada düşer); erişim günlüğünde yalnız ekleme izsiz geçer.
    sonra = _tablolar()
    degisen = _degisen_kayitlar(once, sonra)
    izsiz = _izsiz_degisiklikler(once, sonra, {(satir.model, satir.object_id) for satir in yeni})
    assert not izsiz, (uc, sorted(izsiz))
    if crypto.is_unlocked():
        assert denetim_izi.zinciri_dogrula() == []
        for etiket, kimlik in sorted(degisen - _eklenen_gunluk_satirlari(once, degisen)):
            model = django_apps.get_model(etiket)
            if model._base_manager.filter(pk=kimlik).exists():
                assert denetim_izi.kaydi_dogrula(model, kimlik) is True, (uc, etiket, kimlik)
        for satir in yeni:
            if not satir.record_mac:
                continue
            model = django_apps.get_model(satir.model)
            if model._base_manager.filter(pk=satir.object_id).exists():
                assert denetim_izi.kaydi_dogrula(model, satir.object_id) is True, (uc, satir)


# ============================================================ kaynak taraması

#: Yazıcının giriş noktaları (`denetim_izi`).
YAZICI_GIRISLERI = frozenset(
    {"kayit", "olay", "degisiklik", "kilit_olayi", "kilitli_olay", "kvkk_silme", "basim"}
)
#: Model örneği yazımı (`save`, katı silme, geri alma): konumsal argümansız çağrı. Konumsal
#: argümanlı `save` ORM dışıdır (openpyxl `kitap.save(tampon)`).
_ORNEK_YAZIMLARI = frozenset({"save", "hard_delete", "restore"})
#: Yönetici, queryset ve ilişki yöneticisi yazımı: alıcısı NE OLURSA OLSUN yazım sayılır —
#: `qs = X.objects.filter(..); qs.update(..)`, `yil.terms.update_or_create(..)`,
#: `selectors.active_students().update(..)` de. `delete` yalnız konumsal argümansızken
#: (örnek ya da queryset silmesi; `cache.delete(anahtar)` ORM dışıdır). Aynı adlı ORM dışı
#: çağrılar (`set.update`, `hashlib…update`) `ORM_DISI_CAGRILAR`'da ADIYLA ve gerekçesiyle.
_TOPLU_YAZIMLAR = frozenset(
    {
        "create",
        "get_or_create",
        "update_or_create",
        "bulk_create",
        "bulk_update",
        "update",
        "_raw_delete",  # model yöntemlerini atlar; üretimde çağrısı yoktur
    }
)
#: Ham SQL yazımı.
_HAM_SQL = frozenset({"execute", "executemany", "executescript"})
#: Modelin adlı yazım ilkeleri (`ILKELLER`'de duran ilkelin kendisi): çağrısı, alıcısı ne olursa
#: olsun yazımdır — çağıran izlemiyorsa düşer.
_ILKEL_YAZIMLARI = frozenset({"_saklama_disini_sil"})

#: Yazım taşıyan ama izlenmesi gerekmeyen İLKELLER (göreli dosya yolu, birim) → gerekçe.
#: Dosyanın tamamı taranır: modele yeni bir yazım eklenirse yakalanır, yalnız burada adı
#: geçen ilkel muaftır.
_MODEL_ILKELI = (
    "Modelin yumuşak silme / geri alma ilkesi (`shared.models`): kendisi kayıt yazar ama izi "
    "onu çağıran servis düşer (`degisiklik`, `deleted_at`'li `DURUM` satırı); servislerin "
    "çağrısı bu taramanın kapsamındadır."
)
ILKELLER: dict[tuple[str, str], str] = {
    ("apps/okul/denetim_izi.py", "_ekle"): (
        "Yazıcının kendisi: zincirin satırını ekler (iz satırının izi olmaz)."
    ),
    ("apps/okul/services/satir_izi.py", "hesap_satirlarini_izle"): (
        "Yazıcının geri yüklemedeki ORM'siz eşi (kullanıcı kararı 03.11.2026, K-e): özet "
        "onarımının değiştirdiği her hesap satırı için zincirin sonuna `SISTEM` `HESAP` satırı "
        "ekler (iz satırının izi olmaz). Biçimi `_ekle`'ninkiyle birebirdir; eşitliği "
        "`test_satir_izi.py` sınar."
    ),
    ("shared/models.py", "BaseModel.delete"): _MODEL_ILKELI,
    ("shared/models.py", "BaseModel.hard_delete"): _MODEL_ILKELI,
    ("shared/models.py", "BaseModel.restore"): _MODEL_ILKELI,
    ("shared/models.py", "SoftDeleteQuerySet.delete"): _MODEL_ILKELI,
    ("shared/models.py", "SoftDeleteQuerySet.hard_delete"): _MODEL_ILKELI,
    ("apps/okul/models.py", "_AccessLogQuerySet._saklama_disini_sil"): (
        "Erişim günlüğünün tek silme ilkesi (saklama süresi dolan satırlar): kendisi siler, "
        "izini (`KVKK_SILME`) çağıranı düşer. Bu tarama ilkelin çağrısını yazım sayar "
        "(`_ILKEL_YAZIMLARI`): çağıran yazıcıyı (`denetim_izi.kvkk_silme`) çağırmıyorsa düşer — "
        "bugün tek çağıranı `erisim_gunlugu.suresi_dolanlari_sil` izlidir. Çağıranın TEK "
        "olduğunu ve iz satırının silmeyle AYNI işlemde yazıldığını tarama göremez; onları "
        "`test_erisim_gunlugu.py` sınar (kaynak taraması ve geri alma testi)."
    ),
}

#: İzsiz kalabilen işlevler (göreli dosya yolu, birim) → gerekçe. Başka muafiyet yoktur.
MUAF_ISLEVLER: dict[tuple[str, str], str] = {
    ("apps/okul/services/persons.py", "delete_student"): PLAN_MUAFIYETI,
    ("apps/okul/services/persons.py", "delete_personnel"): PLAN_MUAFIYETI,
    ("apps/okul/services/persons.py", "merge_personnel"): PLAN_MUAFIYETI,
    ("apps/okul/services/ozet_onarimi.py", "ozetleri_onar"): (
        "Geri yüklemenin parola kaydı özeti onarımı (kullanıcı kararı 03.11.2026): ORM'siz, "
        "takastan ÖNCE geri yüklenecek `.tmp` dosyasında; o veritabanında oturum yoktur, "
        "`denetim_izi` yazıcısı çağrılamaz. Değiştirdiği her satırın izi aynı `sqlite3` "
        "işleminde ORM'siz yazıcının `SISTEM` `HESAP` satırıdır "
        "(`satir_izi.hesap_satirlarini_izle`, ilkeller listesinde); geri yüklemenin kendisi ilk "
        "kilit açılışında `GERI_YUKLEME` satırıyla izlenir."
    ),
    ("apps/okul/erisim_gunlugu.py", "yaz"): (
        "Erişim günlüğünün tek yazıcısı: günlük zincir dışıdır (tasarım §4.6.4), satırı iz "
        "satırı doğurmaz; silmesi izlidir (`KVKK_SILME`)."
    ),
}

#: Yazımın izini düşen SAF iz yardımcıları (göreli dosya yolu, birim) → gerekçe. Yalnız
#: bunları çağırmak bir yazımı izli kılar; kendisi yazan, sistem olayı yazan
#: (`iz_durumu.sistem_olayi`, `iz_dogrulama.yaz`) ya da başka bir kaydı izleyen servis
#: SAYILMAZ (o kendi kaydını izler, çağıranın yazdığını değil). Her biri yazıcıyı doğrudan
#: çağırır ve kendisi ORM yazımı taşımaz (`test_saf_iz_yardimcilari_gercekten_saftir`).
SAF_IZ_YARDIMCILARI: dict[tuple[str, str], str] = {
    ("apps/okul/services/setup.py", "_izle"): (
        "Okul kartının yazımının satırı: verilen kaydı `denetim_izi.kayit` ile izler "
        "(OLUSTUR ya da verilen tür); başka iş yapmaz."
    ),
}

#: Yazım adını taşıyan ama ORM'e dokunmayan çağrılar: (göreli dosya yolu, birim, çağrının
#: kaynak metni) → gerekçe. Yeni bir eşleşme ancak gerekçesiyle girer; bayat kayıt düşer
#: (`test_orm_disi_cagrilar_bayat_degildir`).
ORM_DISI_CAGRILAR: dict[tuple[str, str, str], str] = {
    ("apps/okul/services/app_password.py", "_archived_wrap_ids", "kimlikler.update"): (
        "Python kümesi (`set.update`): arşivlerdeki sarmal kimlikleri."
    ),
    ("apps/okul/services/geri_yukleme_notu.py", "dosya_ozeti", "ozet.update"): (
        "`hashlib.sha256().update`: kenara alınan dosyanın özeti."
    ),
    ("apps/okul/services/satir_izi.py", "okuma_islemi", "baglanti.execute"): (
        "Okuma işleminin sınırları (`BEGIN`, `COMMIT`, hata yolunda `ROLLBACK`): kayıt yazmaz; "
        "satırın izinin okumaları tek anlık görüntüdedir (bağımsız denetim bulgusu: yanlış alarm)."
    ),
    ("desktop/backup.py", "_goruntunun_manifestosu", "goruntu.execute"): (
        "Yedek görüntüsünden `SELECT`: manifestoyu okur, kayıt yazmaz; canlı veritabanına dokunmaz."
    ),
    ("desktop/backup.py", "wal_bosalt", "baglanti.execute"): (
        "`PRAGMA wal_checkpoint`: kayıt yazmaz, WAL günlüğünü ana dosyaya aktarır."
    ),
    ("desktop/django_bootstrap.py", "unknown_applied_migrations", "bilinen.update"): (
        "Python kümesi (`set.update`): bilinen göç adları."
    ),
    ("desktop/integrity.py", "check_database_integrity", "connection.execute"): (
        "`PRAGMA integrity_check`: açılıştaki bütünlük denetimi, salt okur."
    ),
    ("desktop/window.py", "WindowController._one_getir", "window.restore"): (
        "Pencereyi simge durumundan geri getirir (pywebview); veritabanına dokunmaz."
    ),
}

#: Taramanın kökleri: `apps/` altındaki BÜTÜN uygulamalar, `shared` ve masaüstü kabuğu.
MASAUSTU = Path(desktop.__file__).resolve().parent


def _salt_okuma_sorgusu_mu(cagri: ast.Call) -> bool:
    """Ham SQL'in ilk argümanı `SELECT` ile başlayan sabit bir metin mi? (salt okuma)

    Yalnız kaynakta görünen sabit metin sayılır: değişkenle, biçimlenmiş metinle ya da
    `executescript` ile verilen sorgu yazım sayılır (fail-closed). Örnek: geri yükleme
    notunun kenara alınacak veritabanının zincir başını salt okunur `sqlite3` ile okuması.
    """
    if not cagri.args or not isinstance(cagri.args[0], ast.Constant):
        return False
    metin = cagri.args[0].value
    return isinstance(metin, str) and metin.lstrip().upper().startswith("SELECT ")


def _orm_yazimi_mi(cagri: ast.Call) -> bool:
    """ORM ya da ham SQL yazımı mı? (kural `_TOPLU_YAZIMLAR`'ın yorumunda)"""
    if not isinstance(cagri.func, ast.Attribute):
        return False
    ad = cagri.func.attr
    if ad in _HAM_SQL:
        return not (ad == "execute" and _salt_okuma_sorgusu_mu(cagri))
    if ad in _ORNEK_YAZIMLARI or ad == "delete":
        return not cagri.args
    return ad in _TOPLU_YAZIMLAR or ad in _ILKEL_YAZIMLARI


def _yazici_cagrisi_mi(cagri: ast.Call) -> bool:
    return (
        isinstance(cagri.func, ast.Attribute)
        and cagri.func.attr in YAZICI_GIRISLERI
        and isinstance(cagri.func.value, ast.Name)
        and cagri.func.value.id == "denetim_izi"
    )


def _noktali_ad(dugum: ast.expr) -> str | None:
    """`a.b.c` biçimindeki ad zinciri (yalnız ad ve öznitelik); değilse None."""
    if isinstance(dugum, ast.Name):
        return dugum.id
    if isinstance(dugum, ast.Attribute):
        ust = _noktali_ad(dugum.value)
        return None if ust is None else f"{ust}.{dugum.attr}"
    return None


def _modul_yolu(noktali: str) -> list[str]:
    """Modülün göreli dosya yolu adayları (`desktop.x` → `desktop/x.py`)."""
    taban = noktali.replace(".", "/")
    return [f"{taban}.py", f"{taban}/__init__.py"]


@dataclass
class _Islev:
    """Tarama birimi: modül düzeyindeki işlev ya da `Sınıf.yöntem` (iç işlevleri dahil)."""

    ad: str
    satir: int
    sinif: str | None = None
    #: ORM yazımları: (satır, çağrının kaynak metni).
    yazimlar: list[tuple[int, str]] = field(default_factory=list)
    #: Çözülmemiş çağrılar: ("ad", f) ya da ("oznitelik", "a.b", f).
    cagrilar: list[tuple[str, ...]] = field(default_factory=list)
    yazici: bool = False


@dataclass
class _Modul:
    yol: str
    birimler: dict[str, _Islev]
    #: Yerel ad → modülün noktalı adı (`import x.y as z`, `from x import y` y bir modülse).
    modul_adlari: dict[str, str]
    #: Yerel ad → (modülün noktalı adı, işlev adı) (`from x.y import f`).
    islev_adlari: dict[str, tuple[str, str]]


def _modulu_tara(yol: str, kaynak: str) -> _Modul:
    """Bir dosyanın birimleri, ORM yazımları, çağrıları ve içe aktarmaları.

    İç içe işlev dıştakinin parçasıdır (yazımı ve izi aynı birime sayılır). Modül düzeyindeki
    çağrılar `<modül>` birimidir; sınıf yöntemi `Sınıf.yöntem` adını taşır.
    """
    agac = ast.parse(kaynak)
    birimler: dict[str, _Islev] = {"<modül>": _Islev("<modül>", 0)}
    modul_adlari: dict[str, str] = {}
    islev_adlari: dict[str, tuple[str, str]] = {}

    def aktarim(dugum: ast.AST) -> None:
        if isinstance(dugum, ast.Import):
            for ad in dugum.names:
                if ad.asname:
                    modul_adlari[ad.asname] = ad.name
                else:
                    kok = ad.name.split(".")[0]
                    modul_adlari[kok] = kok
        elif isinstance(dugum, ast.ImportFrom) and dugum.module and not dugum.level:
            for ad in dugum.names:
                yerel = ad.asname or ad.name
                modul_adlari[yerel] = f"{dugum.module}.{ad.name}"
                islev_adlari[yerel] = (dugum.module, ad.name)

    def gez(dugum: ast.AST, islev: _Islev) -> None:
        for ic in ast.iter_child_nodes(dugum):
            if isinstance(ic, ast.Import | ast.ImportFrom):
                aktarim(ic)
                continue
            if isinstance(ic, ast.Call):
                if _orm_yazimi_mi(ic):
                    islev.yazimlar.append((ic.lineno, ast.unparse(ic.func)))
                if _yazici_cagrisi_mi(ic):
                    islev.yazici = True
                if isinstance(ic.func, ast.Name):
                    islev.cagrilar.append(("ad", ic.func.id))
                elif isinstance(ic.func, ast.Attribute):
                    alici = _noktali_ad(ic.func.value)
                    if alici is not None:
                        islev.cagrilar.append(("oznitelik", alici, ic.func.attr))
            gez(ic, islev)

    def birim_ekle(dugum: ast.FunctionDef | ast.AsyncFunctionDef, sinif: str | None) -> None:
        ad = dugum.name if sinif is None else f"{sinif}.{dugum.name}"
        birim = _Islev(ad, dugum.lineno, sinif)
        birimler[ad] = birim
        gez(dugum, birim)

    for ust in agac.body:
        if isinstance(ust, ast.FunctionDef | ast.AsyncFunctionDef):
            birim_ekle(ust, None)
        elif isinstance(ust, ast.ClassDef):
            for ic in ust.body:
                if isinstance(ic, ast.FunctionDef | ast.AsyncFunctionDef):
                    birim_ekle(ic, ust.name)
                else:
                    gez(ic, birimler["<modül>"])
        elif isinstance(ust, ast.Import | ast.ImportFrom):
            aktarim(ust)
        else:
            gez(ust, birimler["<modül>"])
    return _Modul(yol, birimler, modul_adlari, islev_adlari)


Birim = tuple[str, str]


def _cozumle(moduller: dict[str, _Modul]) -> dict[Birim, set[Birim]]:
    """Her birimin çağırdığı TARANAN birimler: (modül, işlev) çiftiyle, ada göre DEĞİL.

    Aynı modüldeki ad, `self.f`/`cls.f` (aynı sınıf), içe aktarılmış modülün özniteliği
    (`app_password.f`, `apps.okul.iz_durumu.f`) ve `from m import f` çözülür. Başka bir
    alıcıdaki çağrı (`nesne.delete()`, `gun.save()`) HİÇBİR birime çözülmez: ORM yazımının
    adı bir görünüm yöntemiyle aynı olsa da ("delete") iz çağrısı sayılmaz.
    """

    def bul(noktali: str, islev: str) -> Birim | None:
        for aday in _modul_yolu(noktali):
            if aday in moduller and islev in moduller[aday].birimler:
                return (aday, islev)
        return None

    kenarlar: dict[Birim, set[Birim]] = {}
    for yol, modul in moduller.items():
        for ad, birim in modul.birimler.items():
            hedefler: set[Birim] = set()
            for cagri in birim.cagrilar:
                hedef: Birim | None = None
                if cagri[0] == "ad":
                    if cagri[1] in modul.birimler:
                        hedef = (yol, cagri[1])
                    elif cagri[1] in modul.islev_adlari:
                        hedef = bul(*modul.islev_adlari[cagri[1]])
                else:
                    alici, islev = cagri[1], cagri[2]
                    if alici in ("self", "cls") and birim.sinif is not None:
                        yontem = f"{birim.sinif}.{islev}"
                        hedef = (yol, yontem) if yontem in modul.birimler else None
                    else:
                        kok, _, kalan = alici.partition(".")
                        if kok in modul.modul_adlari:
                            tam = modul.modul_adlari[kok] + (f".{kalan}" if kalan else "")
                            hedef = bul(tam, islev)
                if hedef is not None and hedef != (yol, ad):
                    hedefler.add(hedef)
            kenarlar[(yol, ad)] = hedefler
    return kenarlar


@dataclass(frozen=True)
class TaramaSonucu:
    """Kaynak taramasının sonucu: izsiz yazımlar ve kullanılan muafiyet kayıtları."""

    #: (dosya, birim, satır, çağrı metni).
    izsizler: list[tuple[str, str, int, str]]
    #: Eşleşen ORM dışı çağrı kayıtları (bayatlık denetimi için).
    kullanilan_orm_disi: set[tuple[str, str, str]]
    #: Her birim: (yazıcıyı doğrudan çağırır mı, ORM yazımı var mı).
    birimler: dict[Birim, tuple[bool, bool]]


def _tara(
    kaynaklar: dict[str, str],
    *,
    saf_yardimcilar: Iterable[Birim] = (),
    orm_disi: Iterable[tuple[str, str, str]] = (),
    ilkeller: Iterable[Birim] = (),
) -> TaramaSonucu:
    """İzsiz ORM yazımı taşıyan birimler (kural modül başlığında, madde 2).

    Yazım taşıyan birim şu üç hâlden birinde izlidir: (1) yazıcıyı doğrudan çağırır;
    (2) ADIYLA verilmiş bir saf iz yardımcısını (`SAF_IZ_YARDIMCILARI`) çağırır; (3) modüle
    özel (`_` önekli) bir yardımcıdır, en az bir çağıranı vardır ve BÜTÜN çağıranları
    izcidir. İzci, (1) ya da (2) olan birimdir ya da AYNI modüldeki `_` önekli bir izciyi
    çağıran birimdir (ör. `setup._satiri_al`: satırı alır ya da oluşturur; çağıranı
    `set_roadmap_mark` izini `_save_roadmap` → `_izle` üzerinden düşer). Eşleme (modül, işlev)
    çiftiyledir (`_cozumle`). Kendi kaydının izini yazan BAŞKA bir servisi çağırmak yetmez: o
    servis kendi kaydını izler, çağıranın yazdığını değil — yardımcının arkasında da: başka
    modülün servisini (`hesaplar.close_account`) ya da kamuya açık bir sistem olayı kapısını
    (`iz_durumu.sistem_olayi`, `iz_dogrulama.yaz`) çağıran birim bu yüzden izci DEĞİLDİR,
    onun `_` önekli yardımcısının yazımı izsiz sayılır (bağımsız denetim bulgusu).
    """
    moduller = {yol: _modulu_tara(yol, kaynak) for yol, kaynak in kaynaklar.items()}
    kenarlar = _cozumle(moduller)
    saf = set(saf_yardimcilar)
    orm_disi_kumesi = set(orm_disi)
    ilkel_kumesi = set(ilkeller)
    kullanilan: set[tuple[str, str, str]] = set()

    yazimlar: dict[Birim, list[tuple[int, str]]] = {}
    for yol, modul in moduller.items():
        for ad, birim in modul.birimler.items():
            gercek = []
            for satir, metin in birim.yazimlar:
                if (yol, ad, metin) in orm_disi_kumesi:
                    kullanilan.add((yol, ad, metin))
                else:
                    gercek.append((satir, metin))
            yazimlar[(yol, ad)] = gercek

    cagiranlar: dict[Birim, set[Birim]] = {}
    for kaynak_birim, hedefler in kenarlar.items():
        for hedef in hedefler:
            cagiranlar.setdefault(hedef, set()).add(kaynak_birim)

    yazici = {
        (yol, ad)
        for yol, modul in moduller.items()
        for ad, birim in modul.birimler.items()
        if birim.yazici
    }

    def ozel(birim_: Birim) -> bool:
        return birim_[1].rsplit(".", 1)[-1].startswith("_")

    dogrudan = yazici | {birim_ for birim_, hedefler in kenarlar.items() if hedefler & saf}
    # İzci: yazıcıyı ya da bir saf iz yardımcısını doğrudan çağıran birim; yayılım YALNIZ aynı
    # modüldeki `_` önekli bir izciye giden kenarla (başka modülün servisi ya da kamuya açık
    # bir kapı çağıranı izci yapmaz; belge dizesi).
    izci = set(dogrudan)
    degisti = True
    while degisti:
        degisti = False
        for birim_, hedefler in kenarlar.items():
            if birim_ in izci:
                continue
            if any(h in izci and h[0] == birim_[0] and ozel(h) for h in hedefler):
                izci.add(birim_)
                degisti = True
    izli = set(dogrudan)
    for birim_ in kenarlar:
        ust = cagiranlar.get(birim_, set()) - {birim_}
        if ozel(birim_) and ust and ust <= izci:
            izli.add(birim_)

    izsizler = [
        (yol, ad, satir, metin)
        for (yol, ad), liste in sorted(yazimlar.items())
        if liste and (yol, ad) not in izli and (yol, ad) not in ilkel_kumesi
        for satir, metin in liste[:1]
    ]
    return TaramaSonucu(
        izsizler=izsizler,
        kullanilan_orm_disi=kullanilan,
        birimler={
            (yol, ad): (birim.yazici, bool(yazimlar[(yol, ad)]))
            for yol, modul in moduller.items()
            for ad, birim in modul.birimler.items()
        },
    )


def _izsiz_yazimlar(kaynaklar: dict[str, str]) -> list[tuple[str, str, int]]:
    """Gerçek muafiyet listeleriyle izsiz yazımlar: (dosya, birim, satır)."""
    sonuc = _tara(
        kaynaklar,
        saf_yardimcilar=SAF_IZ_YARDIMCILARI,
        orm_disi=ORM_DISI_CAGRILAR,
        ilkeller=ILKELLER,
    )
    return [(yol, ad, satir) for yol, ad, satir, _ in sonuc.izsizler]


def _taranan_kaynaklar() -> dict[str, str]:
    """`apps/` altındaki bütün uygulamalar, `shared` ve masaüstü kabuğu (testler ve göçler hariç).

    Anahtar `backend/`'e göreli yoldur; masaüstü dosyaları `desktop/…` adını taşır (modülün
    noktalı adıyla aynı). Modeller de taranır: yeni bir model yazımı yakalanır, yalnız
    `ILKELLER`'de adı geçen birim muaftır.
    """
    kaynaklar: dict[str, str] = {}
    kokler = [(KOK / "apps", KOK), (KOK / "shared", KOK), (MASAUSTU, MASAUSTU.parent)]
    for dizin, taban in kokler:
        for yol in sorted(dizin.rglob("*.py")):
            if "tests" in yol.parts or "migrations" in yol.parts:
                continue
            kaynaklar[yol.relative_to(taban).as_posix()] = yol.read_text(encoding="utf-8")
    return kaynaklar


def test_okul_cekirdeginde_izsiz_orm_yazimi_yok() -> None:
    """Madde 2: ORM yazımı taşıyan her işlev izlidir ya da adıyla muaftır."""
    ihlaller = [
        f"{yol}:{satir} {ad}"
        for yol, ad, satir in _izsiz_yazimlar(_taranan_kaynaklar())
        if (yol, ad) not in MUAF_ISLEVLER
    ]
    assert ihlaller == []


def test_muafiyetler_bayat_degildir() -> None:
    """Muaf işlev hâlâ vardır ve gerçekten izsiz yazar: düzelen yol listeden düşer. İlkeller
    hâlâ yazar; muafiyet listelerinin hepsi gerekçelidir."""
    kaynaklar = _taranan_kaynaklar()
    izsiz = {(yol, ad) for yol, ad, _ in _izsiz_yazimlar(kaynaklar)}
    assert set(MUAF_ISLEVLER) <= izsiz
    sonuc = _tara(kaynaklar)
    assert all(sonuc.birimler.get(ilkel, (False, False))[1] for ilkel in ILKELLER), ILKELLER
    for liste in (MUAF_ISLEVLER, ILKELLER, SAF_IZ_YARDIMCILARI, ORM_DISI_CAGRILAR):
        assert all(str(gerekce).strip() for gerekce in liste.values())


def test_orm_disi_cagrilar_bayat_degildir() -> None:
    """Her ORM dışı çağrı kaydı bugün bir çağrıyla eşleşir (dar liste: yalnız gerçek eşleşmeler)."""
    sonuc = _tara(_taranan_kaynaklar(), orm_disi=ORM_DISI_CAGRILAR)
    assert sonuc.kullanilan_orm_disi == set(ORM_DISI_CAGRILAR)


def test_saf_iz_yardimcilari_gercekten_saftir() -> None:
    """Saf iz yardımcısı yazıcıyı DOĞRUDAN çağırır ve kendisi ORM yazımı taşımaz."""
    sonuc = _tara(_taranan_kaynaklar())
    for yardimci in SAF_IZ_YARDIMCILARI:
        assert sonuc.birimler.get(yardimci) == (True, False), yardimci


#: Gerçek ağaca eklenen izsiz yazımlar (inceleme bulguları): her biri yakalanmalıdır.
_SONDA = """
from apps.okul import denetim_izi, iz_durumu, iz_dogrulama, selectors
from apps.okul.models import AccessLog, Holiday, SchoolYear
from apps.okul.services import hesaplar


def izsiz_yumusak_silme(gun):
    gun.delete()


def izsiz_toplu_silme():
    Holiday.objects.filter(kind="OTHER").delete()


def izsiz_sube_silme(sube):
    sube.delete()


def izsiz_queryset_degiskeni():
    qs = SchoolYear.objects.filter(is_active=True)
    qs.update(is_active=False)


def izsiz_iliski_yoneticisi(yil):
    yil.terms.update_or_create(term_no=1)
    yil.class_sections.create(class_level=9, class_section="A")


def izsiz_secici(_):
    selectors.active_students().update(class_section="B")


def sistem_olayiyla_izlenmis_sanilan(gun):
    gun.save()
    iz_durumu.sistem_olayi("YEDEK", model="yedek.dosya", object_id="")


def dogrulama_yazisiyla_izlenmis_sanilan(gun, acilis, anahtar):
    gun.save()
    iz_dogrulama.yaz(acilis, anahtar=anahtar)


def _kaydet(gun):
    gun.save()


def sistem_olayi_yardimcinin_arkasinda(gun):
    _kaydet(gun)
    iz_durumu.sistem_olayi("YEDEK", model="yedek.dosya", object_id="")


def _kapat(yil):
    SchoolYear.objects.filter(pk=yil.pk).update(is_active=False)


def baska_servis_yardimcinin_arkasinda(by, hid, yil):
    hesaplar.close_account(by_hesap_id=by, hesap_id=hid)
    _kapat(yil)


def _dogrulama_yardimcisi(gun):
    gun.save()


def dogrulama_yazisi_yardimcinin_arkasinda(gun, acilis, anahtar):
    _dogrulama_yardimcisi(gun)
    iz_dogrulama.yaz(acilis, anahtar=anahtar)


class GorunumGibi:
    def delete(self, request):
        return None

    def post(self, gun):
        gun.save()
        self.delete(None)


def izli_silme(gun):
    onceki = denetim_izi.anlik(gun)
    gun.delete()
    denetim_izi.degisiklik(gun, onceki=onceki)


def izsiz_ham_silme():
    Holiday.objects.filter(kind="OTHER")._raw_delete("default")


def izsiz_gunluk_silme(sinir):
    AccessLog.objects.all()._saklama_disini_sil(sinir)


def izli_gunluk_silme(sinir, gun):
    adet = AccessLog.objects.all()._saklama_disini_sil(sinir)
    denetim_izi.kvkk_silme(AccessLog, adet=adet, en_yeni=gun, tetik="GUN_ISI")
"""


def test_gercek_agaca_eklenen_izsiz_yazimlar_yakalanir() -> None:
    """İnceleme bulgusu: eşleme ada göre yapılınca görünümlerin `delete`/`post` yöntemleri ve
    `iz_dogrulama.yaz` "saf iz yardımcısı" sayılıyor, gerçek ağaçta izsiz `.delete()` geçiyordu.
    Eşleme artık (modül, işlev) çiftiyledir; ORM yazımının adı iz çağrısı sayılmaz; queryset
    değişkeni, ilişki yöneticisi ve seçicinin queryset'i de yazımdır. Aynı kalıplar `_` önekli
    bir yardımcının arkasına alınınca da yakalanır (bağımsız denetim bulgusu): sistem olayı
    kapısını, doğrulama yazısını ya da başka modülün servisini çağıran birim izci değildir.
    Erişim günlüğünün silme ilkesini `KVKK_SILME` yazmadan çağıran birim de yakalanır."""
    kaynaklar = {**_taranan_kaynaklar(), "apps/okul/services/sonda.py": _SONDA}
    bulunan = {ad for yol, ad, _ in _izsiz_yazimlar(kaynaklar) if yol.endswith("sonda.py")}
    assert bulunan == {
        "izsiz_ham_silme",
        "izsiz_gunluk_silme",
        "izsiz_yumusak_silme",
        "izsiz_toplu_silme",
        "izsiz_sube_silme",
        "izsiz_queryset_degiskeni",
        "izsiz_iliski_yoneticisi",
        "izsiz_secici",
        "sistem_olayiyla_izlenmis_sanilan",
        "dogrulama_yazisiyla_izlenmis_sanilan",
        "_kaydet",
        "_kapat",
        "_dogrulama_yardimcisi",
        "GorunumGibi.post",
    }


@pytest.mark.django_db
def test_tablo_karsilastirmasi_iki_kayit_yazip_birini_izleyen_yolu_yakalar() -> None:
    """Madde 1'in karşılaştırmasının kendisi: kaynak taraması "izli" dese de (yazıcı aynı
    işlevde çağrılıyor) izsiz yazılan ikinci kayıt bulunur."""
    once = _tablolar()
    bas = _son_seq()
    with transaction.atomic():
        calendar_service.create_holiday(
            name="Uydurma izli gün",
            start_date=date(2026, 11, 20),
            end_date=date(2026, 11, 20),
            kind="OTHER",
        )
        izsiz = Holiday.objects.create(
            name="Uydurma izsiz gün",
            start_date=date(2026, 11, 21),
            end_date=date(2026, 11, 21),
            kind="OTHER",
        )
    izlenen = {(satir.model, satir.object_id) for satir in AuditTrail.objects.filter(seq__gt=bas)}
    assert _degisen_kayitlar(once, _tablolar()) - izlenen == {("okul.Holiday", str(izsiz.pk))}


@pytest.mark.django_db
def test_tablo_karsilastirmasi_erisim_gunlugunde_yalniz_eklemeyi_gecirir() -> None:
    """Zincir dışı erişim günlüğü karşılaştırmadan bütünüyle çıkmaz (inceleme bulgusu): izli
    bir yolda eklenen satır izsiz geçer, SİLİNEN satır yakalanır. `_base_manager` modelin
    silme reddini atlar ve DELETE tetikleyicisi yoktur; bu yolu ancak karşılaştırma görür."""
    eski = AccessLog.objects.create(
        at=timezone.now() - timedelta(days=30),
        account_id=TEST_HESAP_ID,
        role="yonetici",
        kind=AccessKind.KISI_DOKUMU,
        model="okul.Holiday",
        object_id="1",
    )
    once = _tablolar()
    assert ("okul.AccessLog" in once) and str(eski.pk) in once["okul.AccessLog"]
    bas = _son_seq()
    with transaction.atomic():
        gun = calendar_service.create_holiday(
            name="Uydurma izli gün",
            start_date=date(2026, 11, 20),
            end_date=date(2026, 11, 20),
            kind="OTHER",
        )
        yeni = erisim_gunlugu.yaz(AccessKind.KISI_DOKUMU, model=Holiday, object_id=gun.pk)
        AccessLog._base_manager.filter(pk=eski.pk).delete()
    izlenen = {(satir.model, satir.object_id) for satir in AuditTrail.objects.filter(seq__gt=bas)}

    sonra = _tablolar()
    assert ("okul.AccessLog", str(yeni.pk)) in _degisen_kayitlar(once, sonra)
    assert _izsiz_degisiklikler(once, sonra, izlenen) == {("okul.AccessLog", str(eski.pk))}


def test_tarayici_izsiz_yazimi_yakalar_yardimciyi_ve_baska_kaydi_ayirir() -> None:
    """Tarayıcının kendisi: gerçek ihlali yakalar; yorum, belge ve ORM dışı `save` sayılmaz."""
    kaynak = '''
"""`Student.objects.create(...)` belge metnidir."""
from apps.okul import denetim_izi
from apps.okul.services import app_password

def izsiz(fields):
    return Holiday.objects.create(**fields)

def izli(fields):
    kayit = Holiday.objects.create(**fields)
    denetim_izi.degisiklik(kayit, onceki=None)

def _izle(nesne):
    denetim_izi.kayit("GUNCELLE", nesne, onceki=None)

def yardimciyla(nesne):
    nesne.save(update_fields=["ad"])
    _izle(nesne)

def toplu():
    Holiday.objects.filter(kind="X").update(kind="Y")

def ham(cursor):
    cursor.execute("UPDATE x SET y = 1")

def salt_okur(baglanti):
    return baglanti.execute("SELECT seq, mac FROM x ORDER BY seq DESC LIMIT 1").fetchone()

def degiskenli_sorgu(baglanti, sorgu):
    baglanti.execute(sorgu)

def okur_gibi_yazar(baglanti):
    baglanti.executescript("SELECT 1; DELETE FROM x")

def orm_disi(kitap, tampon, onbellek):
    kitap.save(tampon)
    onbellek.delete("anahtar")

def ayni_adli_orm_disi(kume):
    kume.update(["a"])

def ic_yardimcili(nesne):
    def ic():
        nesne.delete()
    ic()
    denetim_izi.olay("KILIT", model="x", object_id="1")

def ic_izsiz(nesne):
    def ic():
        nesne.hard_delete()
    ic()

class Servis:
    def yaz(self, nesne):
        nesne.save()

    def baska_modulden(self, nesne):
        nesne.save()
        app_password._kurtarma_izi(None, {})

    def _yontem_yardimcisi(self, nesne):
        nesne.save()

    def yontemle_izler(self, nesne):
        self._yontem_yardimcisi(nesne)
        denetim_izi.degisiklik(nesne, onceki=None)

def _olustur():
    return Holiday.objects.get_or_create(pk=1)

def cagiran_izler():
    kayit, _ = _olustur()
    denetim_izi.degisiklik(kayit, onceki=None)

def _yetim():
    Holiday.objects.create(name="x")

def _kaydi_al():
    return Holiday.objects.get_or_create(pk=2)

def _kaydet_ve_izle(nesne):
    _izle(nesne)

def isaretle():
    kayit, _ = _kaydi_al()
    _kaydet_ve_izle(kayit)

def izsiz_cagiran():
    _yetim()

def servis_yazar(nesne):
    nesne.save()
    denetim_izi.degisiklik(nesne, onceki=None)

def baska_servisi_cagirir(nesne):
    nesne.save()
    servis_yazar(nesne)
'''
    baska = """
from apps.okul import denetim_izi

def _kurtarma_izi(eski, yeni):
    denetim_izi.olay("KURTARMA", model="guvenlik.kurtarma", object_id="1")
"""
    kaynaklar = {"ornek.py": kaynak, "apps/okul/services/app_password.py": baska}
    sonuc = _tara(
        kaynaklar,
        saf_yardimcilar={
            ("ornek.py", "_izle"),
            ("apps/okul/services/app_password.py", "_kurtarma_izi"),
        },
        orm_disi={("ornek.py", "ayni_adli_orm_disi", "kume.update")},
    )
    assert {ad for _, ad, _, _ in sonuc.izsizler} == {
        "izsiz",
        "toplu",
        "ham",
        # Yalnız sabit `SELECT` metniyle `execute` salt okumadır; değişkenli sorgu ve
        # `executescript` yazım sayılır (fail-closed).
        "degiskenli_sorgu",
        "okur_gibi_yazar",
        "ic_izsiz",
        "Servis.yaz",
        "_yetim",
        "baska_servisi_cagirir",
    }
    assert sonuc.kullanilan_orm_disi == {("ornek.py", "ayni_adli_orm_disi", "kume.update")}
    # Saf yardımcı listede değilse onu çağırmak yazımı izli kılmaz.
    yalin = {ad for _, ad, _, _ in _tara(kaynaklar).izsizler}
    assert {"yardimciyla", "Servis.baska_modulden"} <= yalin


# ============================================================ kaydın özeti: uydurma kişi verisi sıfır


def _saglamali_uydurma_numara(ilk_dokuz: str) -> str:
    """T.C. kimlik numarası sağlamasına UYAN uydurma numara (son iki hane hesaplanır).

    Numara kaynakta HAZIR yazılmaz, çalışma anında üretilir: depo sızıntı kapısı
    (packaging/depo_sizintisi.py) sağlamaya uyan her 11 haneli sayıyı kişisel veri
    sayar — kapının kendi testleri (test_depo_sizintisi._saglamali_numara) de aynı
    yolu izler. Sağlamaya uyması bilinçlidir: iz tablosunda aranan değer gerçek bir
    numaranın biçimini taşımalı.
    """
    hane = [int(k) for k in ilk_dokuz]
    tek = hane[0] + hane[2] + hane[4] + hane[6] + hane[8]
    cift = hane[1] + hane[3] + hane[5] + hane[7]
    onuncu = (tek * 7 - cift) % 10
    return f"{ilk_dokuz}{onuncu}{(sum(hane) + onuncu) % 10}"


#: Uydurma kişi verisi — hiçbiri gerçek kişiye ait değildir.
UYDURMA_AD = "Pelinsu"
UYDURMA_SOYAD = "Uydurmakaya"
UYDURMA_TELEFON = "05329876543"
UYDURMA_TELEFON_ARALIKLI = "0532 987 65 43"
UYDURMA_TCKN = _saglamali_uydurma_numara("100000001")
UYDURMA_ADRES = "Hayal Mahallesi Masal Sokak No 7"
UYDURMA_METIN = "gizli serbest metin örneği"
#: Serbest metin alanlarının içeriği (alan uzunluğu izin verdikçe hepsi bir arada).
UYDURMA_UZUN = (
    f"{UYDURMA_AD} {UYDURMA_SOYAD} {UYDURMA_TELEFON_ARALIKLI} {UYDURMA_TCKN} "
    f"{UYDURMA_ADRES} {UYDURMA_METIN}"
)
ARANACAKLAR = (
    UYDURMA_AD,
    UYDURMA_SOYAD,
    UYDURMA_AD.casefold(),
    UYDURMA_SOYAD.casefold(),
    "PELİNSU",
    "UYDURMAKAYA",
    UYDURMA_TELEFON,
    UYDURMA_TELEFON[1:],
    UYDURMA_TELEFON_ARALIKLI,
    UYDURMA_TCKN,
    "Hayal Mahallesi",
    "Masal Sokak",
    UYDURMA_METIN,
)


def _iz_metni() -> str:
    """`okul_audittrail`'in BÜTÜN sütunları, ham SQL ile (ORM dönüşümü yok)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail ORDER BY seq")
        return json.dumps(
            [list(map(str, satir)) for satir in cursor.fetchall()], ensure_ascii=False
        )


def _ham_sutunlar(tablo: str, sutunlar: tuple[str, ...]) -> list[str]:
    """Şifreli sütunların veritabanındaki ham token'ları (izde de geçmemeli)."""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(sutunlar)} FROM {tablo}")  # noqa: S608 — sabit adlar
        return [str(deger) for satir in cursor.fetchall() for deger in satir if deger]


def _xlsx(satirlar: list[tuple[str, ...]]) -> bytes:
    kitap = Workbook()
    sayfa = kitap.active
    assert sayfa is not None
    sayfa.append(list(STUDENT_TEMPLATE_HEADERS))
    for satir in satirlar:
        sayfa.append(list(satir))
    tampon = BytesIO()
    kitap.save(tampon)
    return tampon.getvalue()


@pytest.mark.django_db
def test_denetim_izinde_uydurma_kisisel_veri_yok(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tasarım §4.6.2 kural 6, §14 F1b kapısı (modül başlığı, madde 3).

    Her izli model (`Account`, `SchoolConfig`, `SchoolYear`, `SchoolTerm`, `Holiday`,
    `Student`, `Personnel`, `ClassSection`, `ImportRun`, `Attachment`) uydurma kişi verisiyle
    yazılır, güncellenir ve durumu değişir; iz satırlarının hiçbir sütununda bu değerler,
    parçaları, büyük-küçük harf biçimleri ve şifreli token'ları geçmez. Arşiv dökümü henüz yoktur.
    """
    # Hesap (ad-soyad şifreli kişi verisi).
    hesap_ac(AccountRole.MUHASIP, ad=f"{UYDURMA_AD} {UYDURMA_SOYAD}")
    # Okul kartı: okul adı, il, ilçe, kısa ad, müdür adı serbest metin / kişi adı.
    setup_service.update_school_config(
        fields={
            "school_name": UYDURMA_UZUN,
            "province": UYDURMA_SOYAD,
            "district": UYDURMA_AD,
            "principal_name": f"{UYDURMA_AD} {UYDURMA_SOYAD}",
            "kisa_ad": UYDURMA_TELEFON,
            "kademe": "ORTAOKUL",
        }
    )
    # Ders yılı (ad elle yazılan metindir), dönemler, aktifleştirme.
    yil = school_year_service.create_school_year(
        name=f"{UYDURMA_SOYAD} {UYDURMA_TCKN}"[:32],
        start_date=date(2026, 9, 7),
        end_date=date(2027, 6, 25),
        activate=True,
    )
    term_service.configure_terms(yil, first_end=date(2027, 1, 22), second_start=date(2027, 2, 8))
    term_service.configure_terms(yil, first_end=date(2027, 1, 15), second_start=date(2027, 2, 1))
    # Kapalı gün: ad serbest metin; tohumlama ve yumuşak silme.
    gun = calendar_service.create_holiday(
        name=UYDURMA_UZUN[:128],
        start_date=date(2026, 11, 20),
        end_date=date(2026, 11, 20),
        kind="OTHER",
    )
    calendar_service.delete_holiday(gun)
    calendar_service.seed_holidays(2026)
    # Öğrenci: ad, soyad, okul no; güncelleme, havuz, ayrılış.
    ogrenci = persons.create_student(
        first_name=UYDURMA_AD,
        last_name=f"{UYDURMA_SOYAD} {UYDURMA_ADRES}",
        student_number=UYDURMA_TCKN,
        class_level=9,
        class_section="A",
    )
    persons.update_student(
        ogrenci, first_name=f"{UYDURMA_AD} {UYDURMA_METIN}", last_name=UYDURMA_TELEFON
    )
    persons.add_to_leave_pool(ogrenci, run=None)
    persons.leave_student(ogrenci)
    # Personel: ad, soyad; güncelleme, ayrılış.
    personel = persons.create_personnel(first_name=UYDURMA_AD, last_name=UYDURMA_UZUN[:100])
    persons.update_personnel(personel, last_name=f"{UYDURMA_SOYAD} {UYDURMA_TELEFON}")
    persons.leave_personnel(personel)
    # Şube (elle ve aktarımla), aktarım koşusu (dosya adı serbest metin), önizleme.
    section_service.create_class_section(school_year=yil, class_level=10, class_section="B")
    dosya = _xlsx([("9/C", "777", f"{UYDURMA_AD} {UYDURMA_METIN}", UYDURMA_SOYAD)])
    dosya_adi = f"{UYDURMA_AD} {UYDURMA_SOYAD} {UYDURMA_TELEFON_ARALIKLI}.xlsx"
    import_service.preview_students_file(file_bytes=dosya, file_name=dosya_adi)
    import_service.commit_students_file(file_bytes=dosya, file_name=dosya_adi)
    # Aynı öğrenci başka şubeyle ve yeni adla: aktarımın güncelleme yolu.
    ikinci = _xlsx([("9/D", "777", f"{UYDURMA_SOYAD} {UYDURMA_ADRES}", UYDURMA_AD)])
    import_service.commit_students_file(file_bytes=ikinci, file_name=f"{UYDURMA_METIN}.xlsx")
    import_service.commit_personnel_text(
        text="\n".join([PERSONEL_BASLIGI, f"{UYDURMA_AD}\t{UYDURMA_SOYAD}\tÖğretmen\t"])
    )
    with pytest.raises(ParserError):
        import_service.commit_students_file(file_bytes=b"bozuk", file_name=dosya_adi)
    # Ek: özgün dosya adı kişi adı taşıyabilir, sarmal güvenlik öğesidir (plan F1b-3).
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", {"okul.SchoolYear"})
    dosya_deposu.yaz(
        b"%PDF-1.7 uydurma",
        original_name=f"{UYDURMA_AD} {UYDURMA_SOYAD} {UYDURMA_TCKN} {UYDURMA_METIN}.pdf",
        sensitivity=AttachmentSensitivity.OZEL_NITELIKLI,
        owner=yil,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )

    metin = _iz_metni()
    modeller = set(AuditTrail.objects.values_list("model", flat=True))
    assert {
        "okul.Account",
        "okul.SchoolConfig",
        "okul.SchoolYear",
        "okul.SchoolTerm",
        "okul.Holiday",
        "okul.Student",
        "okul.Personnel",
        "okul.ClassSection",
        "okul.ImportRun",
        "okul.Attachment",
    } <= modeller
    for parca in ARANACAKLAR:
        assert parca not in metin, parca
    tokenlar = [
        *_ham_sutunlar("okul_student", ("first_name", "last_name", "student_number")),
        *_ham_sutunlar("okul_personnel", ("first_name", "last_name")),
        *_ham_sutunlar("okul_account", ("display_name",)),
        *_ham_sutunlar("okul_attachment", ("original_name", "key_wrap", "sha256")),
    ]
    assert tokenlar
    for token in tokenlar:
        assert token not in metin
    # Şifreli alanların değiştiği yalnız ADIYLA görünür.
    assert "first_name" in metin and "school_name" in metin and "file_name" in metin
    assert "original_name" in metin
    # Yolların hepsi izlidir: izi olan her kaydın içerik MAC'i son satırını tutar.
    assert denetim_izi.zinciri_dogrula() == []
    for etiket, kimlik in set(
        AuditTrail.objects.exclude(record_mac="").values_list("model", "object_id")
    ):
        model = django_apps.get_model(etiket)
        if model._base_manager.filter(pk=kimlik).exists():
            assert denetim_izi.kaydi_dogrula(model, kimlik) is True, (etiket, kimlik)


@pytest.mark.django_db
def test_kisi_satirlari_deger_tasimaz_okul_no_dahil() -> None:
    """KVKK silme kümesindeki modellerin (`Student`, `Personnel`) satırları değer taşımaz."""
    ogrenci = persons.create_student(
        first_name="Uydurcan", last_name="Örnekoğlu", student_number="501", class_level=9
    )
    persons.leave_student(ogrenci)
    personel = persons.create_personnel(first_name="Uydurnur", last_name="Örnekkaya")
    persons.leave_personnel(personel)
    satirlar = AuditTrail.objects.filter(model__in=["okul.Student", "okul.Personnel"])
    assert satirlar.count() == 4
    assert all(satir.values == {} for satir in satirlar)


# ============================================================ toplu aktarım süresi

#: Ölçülen süre (Docker, tek çekirdek; kayıt başına ~5 sorgu): sınır gevşektir, gerilemeyi
#: yakalar. Ölçüm raporda: 2000 satırlık aktarım ve önizlemesi birkaç saniyedir.
AKTARIM_SATIRI = 2000
AKTARIM_SINIRI_SN = 60.0


@pytest.mark.django_db
def test_iki_bin_satirlik_aktarim_kayit_basina_iz_yazar_ve_makul_surer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Toplu yazım kayıt başına satırdır; 2000 satırlık aktarım ve önizlemesi makul sürer."""
    SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    satirlar = [
        f"{9 + i % 4}/{'ABCD'[i % 4]}\t{1000 + i}\tUYDURMA{i} ÖRNEK{i}"
        for i in range(AKTARIM_SATIRI)
    ]
    metin = "\n".join([OGRENCI_BASLIGI, *satirlar])

    basla = time.perf_counter()
    import_service.preview_students_text(text=metin)
    onizleme_sn = time.perf_counter() - basla
    assert AuditTrail.objects.filter(model="okul.Student").count() == 0  # geri sarıldı

    basla = time.perf_counter()
    rapor = import_service.commit_students_text(text=metin)
    uygulama_sn = time.perf_counter() - basla

    assert rapor.created_students == AKTARIM_SATIRI
    assert (
        AuditTrail.objects.filter(model="okul.Student", action="OLUSTUR").count() == AKTARIM_SATIRI
    )
    assert AuditTrail.objects.filter(model="okul.ClassSection").count() == 4
    with capsys.disabled():
        print(
            f"\n[ölçüm] {AKTARIM_SATIRI} satır: önizleme {onizleme_sn:.1f} sn, "
            f"uygulama {uygulama_sn:.1f} sn"
        )
    assert onizleme_sn < AKTARIM_SINIRI_SN and uygulama_sn < AKTARIM_SINIRI_SN


# ============================================================ izli modeller


#: Denetim izi listelerini TAŞIMAYAN modeller ve gerekçeleri.
LISTESIZ_MODELLER = {
    "AuditTrail": "İzin kendisi (ekleme-yalnız; tek yazarı denetim_izi).",
    "AuditKey": "İz anahtarı: ilk hesapla aynı işlemde yazılır, iz satırı mühürünün anahtarıdır.",
    "AccessLog": (
        "Erişim günlüğü: zincir dışı, değer tutmaz (tasarım §4.6.4); silmesi `KVKK_SILME`."
    ),
}
IZLI_MODELLER = (
    Account,
    SchoolConfig,
    SchoolYear,
    SchoolTerm,
    Holiday,
    Student,
    Personnel,
    ClassSection,
    ImportRun,
    Attachment,
)


def test_okul_modellerinin_hepsi_izli_ya_da_gerekceli_listesizdir() -> None:
    """Yeni bir okul modeli izin listeleri olmadan eklenemez (yazıcı onu yazmaz)."""
    modeller = {model.__name__ for model in django_apps.get_app_config("okul").get_models()}
    listesiz = {
        ad for ad in modeller if not hasattr(django_apps.get_model("okul", ad), "IZ_DEGER_ALANLARI")
    }
    assert listesiz == set(LISTESIZ_MODELLER)
    assert modeller - listesiz == {model.__name__ for model in IZLI_MODELLER}


@pytest.mark.parametrize("model", IZLI_MODELLER, ids=lambda m: m.__name__)
def test_durum_alanlari_modelin_alanlaridir(model: Any) -> None:
    alanlar = {a.name for a in model._meta.concrete_fields if not a.primary_key}
    durum = set(getattr(model, "IZ_DURUM_ALANLARI", ()))
    assert durum <= alanlar
    if "deleted_at" in alanlar:  # yumuşak silme daima durum geçişidir
        assert "deleted_at" in durum
    assert "updated_at" not in durum
