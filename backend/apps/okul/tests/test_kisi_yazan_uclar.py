"""Kişi yazan uçların ilk hesap kapısı (tasarım §5.3; plan §2.4).

"Parola kurulmadan kişi yazan uç 409" maddesinin kanıtı (ilk program yöneticisi
hesabı kurulmadan, 409 `parola_gerekli`). Test `config.urls`'ün
BÜTÜN desenlerini dolaşır:

1. `RequiresAdminPassword` taşıyan uçlar kümesi, aşağıdaki AÇIK listeye
   (`KISI_YAZAN_UCLAR`) birebir eşit olmalıdır.
2. Liste dışındaki `/api/` uçları da ANLIK GÖRÜNTÜYLE (`DIGER_UCLAR`)
   sabitlenir: yeni bir uç eklenince test düşer ve ekleyen, ucun kişi yazıp
   yazmadığına bilinçli karar verir (kişi yazıyorsa izin sınıfını takar ve
   üstteki listeye, yazmıyorsa alttaki listeye ekler).
3. `parolasiz` ortamda (ilk açılış, parola kurulmamış) listedeki her uç, desteklediği
   her yazma yöntemiyle **409 `parola_gerekli`** döner; okuma yöntemleri açıktır.

Savunma derinliği: izin sınıfı unutulsa bile şifreli alan anahtarsız yazmaz
(`KeyMissingError` → yine 409; `shared/tests/test_exceptions.py`).

Öğrenci uçları F1b 5. adımda söküldü (tasarım §5.1 ALMA); kapı personel ve veli listesi
uçlarıyla sınanır (plan "F1b-5 uygulama kararları": kapı testleri öğrenci yerine veli listesi ve
personel üzerinden).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from rest_framework.test import APIClient

from apps.oab.models import OabPerson
from apps.okul.models import ParentRoster, Personnel
from apps.okul.permissions import RequiresAdminPassword

# Kişi (personel) yazan uçlar — izin sınıfını taşımalıdır.
# Ayrılış, birleştirme ve ayrılış havuzu kararı da kişi yazar.
KISI_YAZAN_UCLAR = frozenset(
    {
        "personnel-list",
        "personnel-detail",
        "personnel-leave",
        "personnel-merge",
        "import-personnel-preview",
        "import-personnel-commit",
        "leave-pool-resolve",
        # Veli listesi (T5): aktarım (önizleme ve uygulama) ve "Veli listesini sil".
        "parent-roster",
        "import-parents-preview",
        "import-parents-commit",
        # Birlik kişileri (F1c 4. adım): elle kayıt, güncelleme, personelden ve veli listesinden kopya.
        "oab-person-list",
        "oab-person-detail",
        "oab-person-from-personnel",
        "oab-person-from-parent",
    }
)

# Anlık görüntü: kişi YAZMAYAN bütün `/api/` uçları. Yeni uç → bilinçli sınıflandırma.
DIGER_UCLAR = frozenset(
    {
        # Erişim günlüğünün okuma ekranı (plan F1b-2): yalnız okur (GET), iz bırakmaz.
        "access-log",
        # Kullanıcılar (plan F1b-2): hesap yazar, kişi sicili (personel) yazmaz. Açık
        # oturumda rol kapısı ve servisin yetki kapısı keser; kurulumda yazar ve veri anahtarı
        # yoktur (servis reddeder).
        "account-close",
        "account-detail",
        "account-handover-slip",
        "account-list",
        "account-options",
        "account-reset-password",
        "account-unsuspend",
        # Çık (tasarım §4.2): kişi yazmaz; her oturum durumunda parolasız.
        "app-quit",
        # Seçilen yedek dosyasının başlığını okur, hiçbir şey yazmaz.
        "backup-inspect",
        "backup-list",
        # Yedek Raporu: `BASIM` satırı yazar, kişi yazmaz.
        "backup-report",
        "backup-restore",
        # Dış yedek hatırlatması (tasarım §16 R6) veri dizinindeki dosyaya (tarih ve
        # süre) yazar — kişi sicili yazmaz.
        "backup-external-reminder",
        # Son oturum kartı (T15, §13 D4): kişisiz özet; POST yalnız süreç içi
        # "Kontrol ettim" onayıdır, hiçbir kayıt yazmaz.
        "dashboard-last-session",
        "encrypted-backup-download",
        "holiday-detail",
        "holiday-list",
        "holiday-seed",
        # Havuz listesi yalnız okur (GET); karar ucu yukarıdaki listededir.
        "leave-pool",
        "school-year-activate",
        "school-year-list",
        "school-year-terms",
        # Kilit ekranının hesap listesi: tanıtıcı + rol etiketi; kişi adı okumaz, yazmaz.
        "security-accounts",
        "security-change-password",
        "security-enable",
        # Boşta kilit süresi (Ayarlar → Güvenlik): okul ayarı, kişi yazmaz.
        "security-idle-lock",
        # Bütünlük kartları (tasarım §4.6.3; kendi, denetim ve iki depo kartları): denetim
        # izinden kişisiz özet; sahipsiz sarmalın onayla silinmesi `guvenlik.json`'a yazar —
        # kişi sicili yazmaz.
        "security-integrity",
        "security-integrity-audit",
        "security-integrity-orphan-wraps",
        # Parola yenilenme bildirimi: oturumdaki hesabın bayrağı (izli), kişi sicili yazmaz.
        "security-integrity-reset-notice",
        # Geri yükleme kartının "Gördüm"ü (plan F1b-2): yalnız `ISARET` iz satırı yazar.
        "security-integrity-restore-seen",
        "security-integrity-two-store",
        "security-lock",
        "security-recover",
        "security-recovery-key-confirm",
        "security-recovery-key-pdf",
        "security-recovery-key-renew",
        # Oturum özeti (tasarım §4.4.3): kişisiz.
        "security-session",
        "security-state-reset",
        "security-status",
        "security-unlock",
        "oab-okul-karti-bilgileri",
        # Birlik dönemi (F1c-3): kişi verisi yazmaz, kapı `Eylem.BIRLIK_DONEMI_YAZMA`.
        "oab-term-detail",
        "oab-term-list",
        "setup-complete",
        "setup-roadmap",
        "setup-school-config",
        "setup-status",
        "template-personnel",
        # Veli listesi şablonu: boş şablon dosyası, kişi okumaz ve yazmaz.
        "template-parents",
        "update-installer",
        "update-latest",
    }
)

YAZMA_YONTEMLERI = ("post", "put", "patch", "delete")

PAROLA_GEREKLI_GOVDESI = {
    "code": "parola_gerekli",
    "message": (
        "Kişi kaydı için önce program yöneticisi hesabını kurun (Kurulum Sihirbazı'nın ilk adımı)."
    ),
    "fields": {},
}


def _desenler(
    resolver: URLResolver | None = None, onek: str = ""
) -> Iterator[tuple[str, URLPattern]]:
    """(tam yol şablonu, desen) çiftleri — iç içe `include`'lar dahil."""
    kok = resolver if resolver is not None else get_resolver()
    for desen in kok.url_patterns:
        yol = onek + str(desen.pattern)
        if isinstance(desen, URLResolver):
            yield from _desenler(desen, yol)
        else:
            yield yol, desen


def _api_uclari() -> dict[str, URLPattern]:
    """Adlı bütün `/api/` desenleri (SPA catch-all `api/` dışında kalır)."""
    uclar: dict[str, URLPattern] = {}
    for yol, desen in _desenler():
        if yol.startswith("api/"):
            assert desen.name, f"Adsız API deseni: {yol}"
            assert desen.name not in uclar, f"Aynı ad iki kez: {desen.name}"
            uclar[desen.name] = desen
    return uclar


def _gorunum_sinifi(desen: URLPattern) -> Any:
    return getattr(desen.callback, "view_class", None) or getattr(desen.callback, "cls", None)


def _izin_siniflari(desen: URLPattern) -> list[Any]:
    return list(getattr(_gorunum_sinifi(desen), "permission_classes", []) or [])


def _url(desen: URLPattern) -> str:
    """Converter'lı yolları örnek değerle doldurur (`<int:pk>` → 1)."""
    ornek = {ad: 1 for ad in desen.pattern.converters}
    return reverse(str(desen.name), kwargs=ornek)


def test_kisi_yazan_uclar_izin_sinifini_tasir_ve_liste_tam() -> None:
    uclar = _api_uclari()
    korunan = {ad for ad, desen in uclar.items() if RequiresAdminPassword in _izin_siniflari(desen)}
    assert korunan == KISI_YAZAN_UCLAR


def test_liste_disi_uclar_anlik_goruntuyle_sabit() -> None:
    """Yeni bir API ucu eklendiyse: kişi yazıyor mu? Karar verip doğru listeye ekleyin."""
    uclar = set(_api_uclari())
    assert uclar - KISI_YAZAN_UCLAR == DIGER_UCLAR
    assert KISI_YAZAN_UCLAR <= uclar


@pytest.mark.django_db
def test_parolasizken_kisi_yazan_her_uc_yazma_yontemiyle_409_doner(parolasiz: Path) -> None:
    client = APIClient()
    denenen = 0
    for ad, desen in sorted(_api_uclari().items()):
        if ad not in KISI_YAZAN_UCLAR:
            continue
        gorunum = _gorunum_sinifi(desen)
        for yontem in YAZMA_YONTEMLERI:
            if not hasattr(gorunum, yontem):
                continue
            yanit = client.generic(
                yontem.upper(), _url(desen), data="{}", content_type="application/json"
            )
            assert yanit.status_code == 409, (ad, yontem, yanit.status_code)
            assert yanit.json() == PAROLA_GEREKLI_GOVDESI, (ad, yontem)
            denenen += 1
    # 1 liste (POST) + 1 ayrıntı (PUT/PATCH/DELETE) + 2 içe aktarma (POST)
    # + 1 ayrılış (POST) + 1 birleştirme (POST) + 1 havuz kararı (POST)
    # + veli listesi: silme (DELETE) ve 2 aktarım (POST)
    # + birlik kişileri: liste (POST), ayrıntı (PATCH), 2 kopya (POST).
    # Aile iskeletinin kütüphane uçları (üyelik, kart basımı, dolaşım masası,
    # teslim, saklama tetiği) F1a-2'de, öğrenci uçları F1b 5. adımda söküldü.
    assert denenen == 1 + 1 * 3 + 2 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 2
    assert not Personnel.all_objects.exists()
    assert not ParentRoster.objects.exists()
    assert not OabPerson.objects.exists()


@pytest.mark.django_db
def test_parolasizken_okuma_acik(parolasiz: Path) -> None:
    client = APIClient()
    assert client.get("/api/v1/personnel/").status_code == 200
    assert client.get("/api/v1/leave-pool/").status_code == 200
    assert client.get("/api/v1/parent-roster/").status_code == 200


@pytest.mark.django_db
def test_parola_kuruluyken_kisi_yazilir() -> None:
    """Varsayılan ortam (parola kurulu + kilit açık): izin sınıfı geçirir."""
    yanit = APIClient().post(
        "/api/v1/personnel/",
        {"first_name": "DENEME", "last_name": "ÖĞRETMEN", "member_kind": "DIGER"},
        format="json",
    )
    assert yanit.status_code == 201, yanit.json()
