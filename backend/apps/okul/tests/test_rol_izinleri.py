"""Rol-izin matrisi, uç kuralları, bekleyenler ve yetenekler (tasarım §4.4.2, TK13; plan F1b-2).

Matris tasarım belgesinin tablosuyla birebirdir (belge ayrıştırılır: belge ya da kod değişince
düşer). Her `/api/` ucu adıyla rol tablosundadır ya da açık oturumda kapalı olarak gerekçelidir;
kural matrisi aşamaz. Matristeki her Y hücresi ya etkin bir yazma kuralıyla karşılanır ya da
fazıyla "bekleyen" listesindedir (`test_rol_matrisi_hucre_anlik_goruntusu`; tasarım §4.4.2
"Testler (F1b)", §10.6). Bekleyen listeleri ve türetilmiş rol tablosu ANLIK GÖRÜNTÜDÜR:
değiştirmek bilinçli bir karardır, listeler yalnız küçülebilir.

Parametre denetçileri (`yalniz_sorgu`, `govdede_yok`) ve uç adı çözücüsü aile iskeletinden
AYNEN gelir; testleri de buradadır. Uç katmanının kapısı (`RolMiddleware`) `test_rol_koruma`,
servis katmanının kapısı (`yetki`) `test_yetki_kapisi`'ndedir.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from django.test import RequestFactory
from django.urls import resolve

from apps.okul import rol_izinleri
from apps.okul.rol_izinleri import (
    ACIK_OTURUMDA_KAPALI,
    BAGLANMAMIS_EYLEMLER,
    BEKLEYEN_DIPNOTLAR,
    BEKLEYEN_HUCRELER,
    EYLEM_KURALLARI,
    KURALLAR,
    MATRIS,
    OKUMA,
    ROLLER,
    YETENEKLER,
    YK_ROLLERI,
    Eylem,
    KuralTuru,
    RolKurali,
    Satir,
    etkin_hucreler,
    govdede_yok,
    hucre_coz,
    kural_rolleri,
    okuyabilen_roller,
    uc_adi,
    utf8_mi,
    yalniz_sorgu,
    yazabilen_roller,
    yetenekler,
)
from apps.okul.tests.api_gezgini import api_desenleri

HER = frozenset(ROLLER)
Y = frozenset({"yonetici"})
Y_YK = YK_ROLLERI | Y
Y_DK = frozenset({"yonetici", "denetleme_kurulu"})
DK = frozenset({"denetleme_kurulu"})
SEK = frozenset({"sekreter"})
Y_SEK = frozenset({"yonetici", "sekreter"})
_KISALTMA = {
    "H": HER,
    "Y": Y,
    "Y+YK": Y_YK,
    "Y+DK": Y_DK,
    "DK": DK,
    "SEK": SEK,
    "Y+SEK": Y_SEK,
}


def _depo_koku() -> Path:
    """Yerelde `depo/backend/...`; konteynerde backend `/app`, depo `/repo`."""
    yerel = Path(__file__).resolve().parents[4]
    for kok in (yerel, Path("/repo")):
        if (kok / "docs").is_dir() and (kok / "backend").is_dir():
            return kok
    pytest.fail(f"Depo kökü bulunamadı ({yerel} ya da /repo).")


def _api_adlari() -> set[str]:
    return {resolve(ornek).view_name for _, ornek in api_desenleri()}


# ============================================================ matris (tasarım tablosu)

#: Tasarım tablosunun "Alan" sütununda her satırı tanıtan parça (sıra tablonun sırasıdır).
_SATIR_PARCASI: dict[Satir, str] = {
    Satir.M1: "(M1)",
    Satir.M2: "(M2)",
    Satir.M3: "(M3)",
    Satir.M4: "(M4)",
    Satir.M5: "(M5)",
    Satir.M6: "(M6)",
    Satir.M7: "(M7)",
    Satir.M8: "(M8)",
    Satir.MUDUR_YAZISI: "Müdür yazısı",
    Satir.M9: "(M9;",
    Satir.M10: "(M10)",
    Satir.M11: "(M11)",
    Satir.M13_M14: "Kantin (M13), servis (M14)",
    Satir.M15: "(M15,",
    Satir.DENETIM_IZI: "Denetim izi",
    Satir.ERISIM_GUNLUGU: "Erişim günlüğü",
    Satir.KULLANICILAR: "Kullanıcılar:",
    Satir.GUVENLIK: "Güvenlik:",
    Satir.AYARLAR: "Ayarlar (",
    Satir.KISISEL_VERI: "Kişisel veri içeren çıktı",
    Satir.GUNCELLEME: "Güncelleme denetimi",
    Satir.KENDI: "Kendi parolasını değiştirme, Kilitle, Çık",
}


def _hucreler(satir: str) -> list[str]:
    return [h.strip() for h in satir.strip().strip("|").split("|")]


def _tasarim_tablosu() -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Tasarım §4.4.2'nin rol-izin tablosu: (başlıktaki rol sütunları, (Alan metni, hücreler)
    satırları). Tablo, rol sütunları ters tırnaklı tek "| Alan |" başlığıyla bulunur; sütun
    adları başlıktan OKUNUR (sırası ve adı varsayılmaz)."""
    belge = _depo_koku() / "docs" / "tasarim" / "2026-10-31-genel-tasarim.md"
    satirlar = belge.read_text(encoding="utf-8").splitlines()
    adaylar = [
        i
        for i, satir in enumerate(satirlar)
        if satir.startswith("| Alan |")
        and all(h.startswith("`") and h.endswith("`") for h in _hucreler(satir)[1:])
    ]
    assert len(adaylar) == 1, f"Rol-izin tablosunun başlığı tek değil: {adaylar}"
    bas = adaylar[0]
    sutunlar = [h.strip("`") for h in _hucreler(satirlar[bas])[1:]]
    tablo: list[tuple[str, list[str]]] = []
    for satir in satirlar[bas + 2 :]:
        if not satir.startswith("|"):
            break
        hucreler = _hucreler(satir)
        tablo.append((hucreler[0], hucreler[1:]))
    return sutunlar, tablo


def test_matris_tasarim_tablosuyla_birebir() -> None:
    """Tasarım §4.4.2 matrisi rol yetkisinin TEK bağlayıcı kaynağıdır: kod onun kopyasıdır.

    Tablo değişirse (hücre, üst simge, satır ya da başlıktaki sütun adı ve sırası) bu test
    düşer: hücreler başlıktaki sütun ADINA göre eşlenir, başlığın rol sütunları `ROLLER`'in
    kendisi olmalıdır. Bilinçli güncellemede `rol_izinleri._TABLO` ve buradaki satır parçaları
    birlikte değişir.
    """
    sutunlar, tablo = _tasarim_tablosu()
    assert sutunlar == list(ROLLER)
    satirlar = [s for s in Satir if s is not Satir.OTURUM]
    assert len(tablo) == len(satirlar) == len(MATRIS)
    for satir, (alan, hucreler) in zip(satirlar, tablo, strict=True):
        assert _SATIR_PARCASI[satir] in alan, (satir, alan)
        belgedeki = dict(zip(sutunlar, (hucre_coz(h) for h in hucreler), strict=True))
        assert belgedeki == MATRIS[satir], satir
    assert list(MATRIS) == satirlar


def test_hucre_cozumu() -> None:
    assert hucre_coz("Y") == ("Y", None)
    assert hucre_coz("O²") == ("O", 2)
    assert hucre_coz(" Y¹⁰ ") == ("Y", 10)
    assert hucre_coz("—") == ("—", None)
    for bozuk in ("X", "Y2", "—¹", ""):
        with pytest.raises(ValueError):
            hucre_coz(bozuk)


def test_matrisin_rol_sutunlari_hesap_rolleridir() -> None:
    assert ROLLER == (
        "yonetici",
        "baskan",
        "baskan_yardimcisi",
        "muhasip",
        "sekreter",
        "denetleme_kurulu",
        "mudur",
    )
    assert Satir.OTURUM not in MATRIS


# ============================================================ uç kuralları


def test_her_api_ucu_siniflandirildi() -> None:
    """Yeni uç varsayılan kapalıdır; ama kapalı olduğu bilinçli olmalı: her ad ya kuralda ya
    açık oturumda kapalı listesinde (gerekçesiyle)."""
    kuraldaki = {kural.uc for kural in KURALLAR}
    assert not kuraldaki & set(ACIK_OTURUMDA_KAPALI)
    assert kuraldaki | set(ACIK_OTURUMDA_KAPALI) == _api_adlari()
    assert all(gerekce.strip() for gerekce in ACIK_OTURUMDA_KAPALI.values())


def test_api_uc_adlari_tekildir() -> None:
    """Rol matrisi URL ADIYLA eşleşir (aile kuralı): aynı adı taşıyan ikinci bir desen
    (kopyala-yapıştır) matristeki izni sessizce devralırdı. Matrisin kanıtı bu tekliğe dayanır."""
    sayac = Counter(resolve(ornek).view_name for _, ornek in api_desenleri())
    assert sorted(ad for ad, adet in sayac.items() if adet > 1) == []


def _gorunum_sinifi(uc: str) -> Any:
    desen = next(ornek for _, ornek in api_desenleri() if resolve(ornek).view_name == uc)
    eslesme = resolve(desen)
    return getattr(eslesme.func, "view_class", None) or getattr(eslesme.func, "cls", None)


def test_kuraldaki_her_yontem_gorunumde_vardir() -> None:
    """Bayat kural kalmasın: kuralın açtığı her yöntem görünümde tanımlıdır (HEAD → GET)."""
    eksik: list[str] = []
    for kural in KURALLAR:
        gorunum = _gorunum_sinifi(kural.uc)
        for yontem in kural.yontemler:
            ad = "get" if yontem == "HEAD" else yontem.lower()
            if not hasattr(gorunum, ad):
                eksik.append(f"{kural.uc} {yontem}")
    assert eksik == []


def test_parametre_kurali_yok() -> None:
    """F1b'de kısmi yetki ayrı uçla verilir; parametre denetçili kural yoktur (anlık görüntü)."""
    assert [k.uc for k in KURALLAR if k.parametre is not None] == []


#: Okur hücresine yazma veren TEK dipnot: ² (tasarım §4.4.2 "Okuma": "Okur rolün bundan başka
#: yazması yalnız dipnotla verilen rol-özel işarettir (² …)"; ²: "Rol-özel işaretlerin tek
#: kaynağı bu dipnottur"; plan F1b-2 "hücre O ise yalnız okuma açılır"). Modülün sabitinden
#: BAĞIMSIZDIR: koruma kendine dayanmasın (⁷ müdüre M10 yazması vermez).
_OKURA_YAZMA_VEREN_DIPNOTLAR = frozenset({2})


def test_kurallar_matrisi_asmaz() -> None:
    """Hücre "—" ise o role hiçbir şey açılmaz; "O" ise yalnız okuma (² rol-özel işareti
    hariç); dipnotlu hücre yalnız o dipnotu anan kurala; daraltma dayanaklıdır."""
    for kural in KURALLAR:
        roller = kural_rolleri(kural)
        assert roller, kural.uc
        if kural.satir is Satir.OTURUM:
            assert roller == HER
            continue
        hucreler = MATRIS[kural.satir]
        for rol in roller:
            harf, dipnot = hucreler[rol]
            assert harf != "—", (kural.uc, rol)
            if kural.tur is KuralTuru.YAZMA:
                assert harf == "Y" or (
                    dipnot == kural.dipnot and dipnot in _OKURA_YAZMA_VEREN_DIPNOTLAR
                ), (kural.uc, rol)
                assert dipnot in (None, kural.dipnot), (kural.uc, rol)
        if kural.tur is KuralTuru.OKUMA:
            assert kural.yontemler == OKUMA, kural.uc
        assert ("GET" in kural.yontemler) == ("HEAD" in kural.yontemler), kural.uc
        assert "OPTIONS" not in kural.yontemler, kural.uc
        if kural.yalniz is not None or kural.dipnot is not None:
            assert kural.dayanak.strip(), kural.uc


@pytest.mark.parametrize(
    ("kural", "ileti"),
    [
        (
            RolKurali(
                "x",
                frozenset({"POST"}),
                Satir.M1,
                KuralTuru.YAZMA,
                yalniz=frozenset({"muhasip"}),
                dayanak="d",
            ),
            "aşıyor",
        ),
        (RolKurali("x", frozenset({"GET"}), Satir.M1, KuralTuru.OKUMA), "HEAD"),
        (RolKurali("x", frozenset({"OPTIONS"}), Satir.M1, KuralTuru.YAZMA), "OPTIONS"),
        (RolKurali("x", frozenset({"POST"}), Satir.M1, KuralTuru.OKUMA), "Okuma"),
        (
            RolKurali("x", frozenset({"POST"}), Satir.M1, KuralTuru.YAZMA, dipnot=2, dayanak="d"),
            "dipnot",
        ),
        (RolKurali("x", frozenset({"POST"}), Satir.M2, KuralTuru.YAZMA, yalniz=Y), "dayanak"),
        (RolKurali("x", frozenset({"POST"}), Satir.ERISIM_GUNLUGU, KuralTuru.YAZMA), "hiçbir role"),
        (
            RolKurali("security-enable", frozenset({"POST"}), Satir.OTURUM, KuralTuru.YAZMA),
            "kapalı",
        ),
        # ⁷ okur hücresine yazma vermez: müdüre M10 (gelen-giden evrak) ucu açılamaz.
        (
            RolKurali(
                "x",
                frozenset({"POST"}),
                Satir.M10,
                KuralTuru.YAZMA,
                dipnot=7,
                yalniz=frozenset({"mudur"}),
                dayanak="d",
            ),
            "aşıyor",
        ),
    ],
    ids=[
        "daraltma_genisletir",
        "get_headsiz",
        "options",
        "okuma_post",
        "satirda_olmayan_dipnot",
        "dayanaksiz_daraltma",
        "kimseye_acilmaz",
        "acik_oturumda_kapali",
        "mudure_evrak_defteri",
    ],
)
def test_kural_tablosu_matrisi_asan_kurali_reddeder(kural: RolKurali, ileti: str) -> None:
    """Kural matrisi aşarsa ya da tutarsızsa modül YÜKLENMEZ (tablo kurulurken ValueError)."""
    with pytest.raises(ValueError, match=ileti):
        rol_izinleri._kurallari_dogrula((kural,))


def test_ayni_uc_yontem_iki_kuralda_olamaz() -> None:
    kural = RolKurali("x", frozenset({"POST"}), Satir.M1, KuralTuru.YAZMA)
    with pytest.raises(ValueError, match="iki kuralda"):
        rol_izinleri._kurallari_dogrula((kural, kural))


def test_okuma_ve_yazma_turetimi() -> None:
    assert okuyabilen_roller(Satir.M1) == HER
    assert okuyabilen_roller(Satir.ERISIM_GUNLUGU) == Y_DK
    assert yazabilen_roller(Satir.M1) == Y
    assert yazabilen_roller(Satir.M9) == Y_YK
    # Dipnotlu Y yalnız dipnotunu anana; okur hücresi yalnız rol-özel işaret dipnotuyla (²).
    assert "mudur" not in yazabilen_roller(Satir.M3)
    assert "mudur" in yazabilen_roller(Satir.M3, 1)
    assert yazabilen_roller(Satir.M5) == {"muhasip"}
    assert yazabilen_roller(Satir.M5, 2) == {"muhasip", "yonetici"}
    assert "mudur" not in yazabilen_roller(Satir.M13_M14, 9)
    # ⁷: müdürün kendi yazısını evrak defterine program işler; müdür M10'a yazmaz.
    assert yazabilen_roller(Satir.M10, 7) == Y_YK
    assert yazabilen_roller(Satir.KISISEL_VERI) == frozenset()
    assert yazabilen_roller(Satir.KISISEL_VERI, 10) == Y


def test_okur_hucresine_yalniz_iki_numarali_dipnot_yazma_verir() -> None:
    """Matristeki HER dipnotlu okur hücresi: rol o dipnotla yazabilir ancak dipnot ² ise
    (bağımsız sabit `_OKURA_YAZMA_VEREN_DIPNOTLAR`; bugün ² M5'te, ⁷ M10'da, ⁹ M13/M14'te)."""
    okur_dipnotlu = [
        (satir, rol, dipnot)
        for satir, hucreler in MATRIS.items()
        for rol, (harf, dipnot) in hucreler.items()
        if harf == "O" and dipnot is not None
    ]
    assert {d for _, _, d in okur_dipnotlu} == {2, 7, 9}
    for satir, rol, dipnot in okur_dipnotlu:
        assert (rol in yazabilen_roller(satir, dipnot)) is (
            dipnot in _OKURA_YAZMA_VEREN_DIPNOTLAR
        ), (satir, rol, dipnot)


#: Türetilmiş rol tablosu: uç → yöntem → roller (H: her rol; Y: program yöneticisi; Y+YK:
#: program yöneticisi ve yönetim kurulu rolleri; Y+DK: program yöneticisi ve Denetleme Kurulu; DK:
#: yalnız Denetleme Kurulu; SEK: yalnız sekreter; Y+SEK: program yöneticisi ve sekreter).
#: Listede olmayan (uç, yöntem) her rolde kapalıdır (OPTIONS dahil).
ROL_TABLOSU: dict[str, dict[str, str]] = {
    "access-log": {"GET": "Y+DK", "HEAD": "Y+DK"},
    "account-close": {"POST": "Y"},
    "account-detail": {"GET": "Y", "HEAD": "Y"},
    "account-handover-slip": {"POST": "Y"},
    "account-list": {"GET": "Y", "HEAD": "Y", "POST": "Y"},
    "account-options": {"GET": "Y", "HEAD": "Y"},
    "account-reset-password": {"POST": "Y"},
    "account-unsuspend": {"POST": "Y"},
    "app-quit": {"POST": "H"},
    "backup-external-reminder": {"GET": "Y", "HEAD": "Y", "PUT": "Y"},
    "backup-inspect": {"POST": "Y"},
    "backup-list": {"GET": "Y", "HEAD": "Y"},
    "backup-report": {"POST": "Y"},
    "backup-restore": {"POST": "Y"},
    "dashboard-last-session": {"GET": "H", "HEAD": "H", "POST": "Y+YK"},
    "encrypted-backup-download": {"GET": "Y", "HEAD": "Y", "POST": "Y"},
    "holiday-detail": {"DELETE": "Y"},
    "holiday-list": {"GET": "H", "HEAD": "H", "POST": "Y"},
    "holiday-seed": {"POST": "Y"},
    "import-personnel-commit": {"POST": "Y"},
    "import-personnel-preview": {"POST": "Y"},
    "leave-pool": {"GET": "Y", "HEAD": "Y"},
    "leave-pool-resolve": {"POST": "Y"},
    "import-parents-commit": {"POST": "Y"},
    "import-parents-preview": {"POST": "Y"},
    "parent-roster": {"DELETE": "Y", "GET": "Y", "HEAD": "Y"},
    "personnel-detail": {"DELETE": "Y", "GET": "H", "HEAD": "H", "PATCH": "Y", "PUT": "Y"},
    "personnel-leave": {"POST": "Y"},
    "personnel-list": {"GET": "H", "HEAD": "H", "POST": "Y"},
    "personnel-merge": {"POST": "Y"},
    "school-year-activate": {"POST": "Y"},
    "school-year-list": {"GET": "H", "HEAD": "H", "POST": "Y"},
    "school-year-terms": {"GET": "H", "HEAD": "H", "PUT": "Y"},
    "security-accounts": {"GET": "H", "HEAD": "H"},
    "security-change-password": {"POST": "H"},
    "security-idle-lock": {"GET": "H", "HEAD": "H", "PUT": "Y"},
    "security-integrity": {"GET": "H", "HEAD": "H"},
    "security-integrity-audit": {"GET": "Y+DK", "HEAD": "Y+DK"},
    "security-integrity-orphan-wraps": {"POST": "Y"},
    "security-integrity-reset-notice": {"GET": "H", "HEAD": "H", "POST": "H"},
    "security-integrity-restore-seen": {"POST": "DK"},
    "security-integrity-two-store": {"GET": "Y", "HEAD": "Y"},
    "security-lock": {"POST": "H"},
    "security-recover": {"GET": "H", "HEAD": "H", "POST": "H"},
    "security-recovery-key-confirm": {"POST": "Y"},
    "security-recovery-key-pdf": {"POST": "Y"},
    "security-recovery-key-renew": {"POST": "Y"},
    "security-session": {"GET": "H", "HEAD": "H"},
    "security-state-reset": {"POST": "Y"},
    "security-status": {"GET": "H", "HEAD": "H"},
    "security-unlock": {"POST": "H"},
    "setup-complete": {"POST": "Y"},
    "setup-roadmap": {"POST": "Y"},
    "oab-membership-detail": {"GET": "H", "HEAD": "H", "PATCH": "Y+YK"},
    "oab-membership-eligibility-basis": {"GET": "Y+YK", "HEAD": "Y+YK", "PUT": "Y+YK"},
    "oab-membership-list": {"GET": "H", "HEAD": "H", "POST": "Y+YK"},
    # F1c 6. adım: tasarım §7.2'nin "Kim" sütunu (görev bölümü ve YK yedeği sekreter, DK yedeği
    # program yöneticisi, düşme ikisi); DK görev bölümü M8 ⁵.
    "oab-yk-duty-assignment": {"POST": "SEK"},
    "oab-dk-duty-assignment": {"POST": "DK"},
    "oab-membership-substitute-call-yk": {"POST": "SEK"},
    "oab-membership-substitute-call-dk": {"POST": "Y"},
    "oab-membership-drop": {"POST": "Y+SEK"},
    "oab-membership-cancel": {"POST": "Y+YK"},
    "oab-representative-list": {"GET": "H", "HEAD": "H", "POST": "Y+YK"},
    "oab-purchase-committee-list": {"POST": "Y+YK"},
    # F1c 10. adım: E01 ve E03'ü sekreter ve program yöneticisi, E02'yi Denetleme Kurulu üretir
    # (tasarım §9.6 "Üreten"); liste ve basım her role açıktır (okuma).
    "oab-document-e01": {"POST": "Y+SEK"},
    "oab-document-e02": {"POST": "DK"},
    "oab-document-e03": {"POST": "Y+SEK"},
    "oab-term-documents": {"GET": "H", "HEAD": "H"},
    "oab-document-download": {"GET": "H", "HEAD": "H"},
    "oab-okul-karti-bilgileri": {"GET": "H", "HEAD": "H"},
    "oab-organ-roster": {"GET": "H", "HEAD": "H"},
    "oab-person-detail": {"GET": "H", "HEAD": "H", "PATCH": "Y+YK"},
    "oab-person-from-parent": {"POST": "Y"},
    "oab-person-from-personnel": {"POST": "Y+YK"},
    "oab-person-list": {"GET": "H", "HEAD": "H", "POST": "Y+YK"},
    "oab-term-detail": {"GET": "H", "HEAD": "H"},
    "oab-term-list": {"GET": "H", "HEAD": "H", "POST": "Y"},
    # Geçiş kurulumu (F1c 11. adım): her rol okur, yalnız program yöneticisi yazar (§7.9 "Kim").
    "oab-term-cancel": {"POST": "Y"},
    # F1c 11. adımın ikinci parçası: yönetim kurulunun aylık toplantı günü E01'i üretenlerindir;
    # bağlanabilecek kararların listesi her role açıktır (M4 okuması).
    "oab-term-meeting-day": {"PUT": "Y+SEK"},
    "oab-term-linkable-decisions": {"GET": "H", "HEAD": "H"},
    # Gerekçe kutusunun yarım metni: her rol kendi kaydını yazar (KENDI satırı).
    "oab-draft-text": {"GET": "H", "HEAD": "H", "PUT": "H", "DELETE": "H"},
    # Genel Bakış'ın pano kalemleri (F1c 12. adım): her rol okur, kalemleri servis süzer (M9).
    "oab-dashboard": {"GET": "H", "HEAD": "H"},
    "oab-transition": {"GET": "H", "HEAD": "H"},
    "oab-transition-inherited": {"POST": "Y"},
    "oab-transition-election-counts": {"POST": "Y"},
    "oab-transition-decision-book": {"POST": "Y"},
    "oab-transition-decision-book-cancel": {"POST": "Y"},
    "oab-transition-complete": {"POST": "Y"},
    "setup-school-config": {"GET": "H", "HEAD": "H", "PUT": "Y"},
    "setup-status": {"GET": "H", "HEAD": "H"},
    "template-parents": {"GET": "Y", "HEAD": "Y"},
    "template-personnel": {"GET": "Y", "HEAD": "Y"},
    "update-installer": {"GET": "Y", "HEAD": "Y"},
    "update-latest": {"GET": "Y", "HEAD": "Y"},
}


def test_rol_tablosu_anlik_goruntusu() -> None:
    """Bir uca rol eklemek ya da çıkarmak bilinçli bir karardır: bu görüntü de güncellenir."""
    gercek: dict[str, dict[str, frozenset[str]]] = {}
    for kural in KURALLAR:
        for yontem in kural.yontemler:
            gercek.setdefault(kural.uc, {})[yontem] = kural_rolleri(kural)
    beklenen = {
        uc: {yontem: _KISALTMA[kisa] for yontem, kisa in yontemler.items()}
        for uc, yontemler in ROL_TABLOSU.items()
    }
    assert gercek == beklenen


# ============================================================ bekleyenler ve hücreler

#: Ucu ya da servisi olmayan Y hücreleri, fazlarıyla (plan F1b-2 kullanıcı kararı). YALNIZ
#: KÜÇÜLEBİLİR; "F1b" fazlısı kalmadı (Kullanıcılar c1'de, DK'nin M8 hücresi c3'te "Gördüm"le
#: bağlandı; `test_f1b_fazli_bekleyen_kalmadi`).
BEKLEYEN_HUCRE_GORUNTUSU: dict[str, dict[str, set[str]]] = {
    # "F1c": M2 × YK rolleri birlik kişilerinin uçlarıyla bağlandı (F1c 4. adım).
    "F2": {
        "M3": {*Y_YK, "mudur"},
        "M10": set(Y_YK),
    },
    "F3": {"M4": set(Y_YK), "M5": {"muhasip"}},
    "F4": {
        "M6": {*Y_YK, "mudur"},
        "M7": set(Y_YK),
        "MUDUR_YAZISI": {"mudur"},
        "M11": set(Y_YK),
    },
    "F5": {"M13_M14": set(Y_YK)},
    "F8+": {"M15": set(Y_YK)},
}


def test_bekleyen_hucreler_anlik_goruntusu() -> None:
    gercek: dict[str, dict[str, set[str]]] = {}
    for (satir, rol), faz in BEKLEYEN_HUCRELER.items():
        gercek.setdefault(faz, {}).setdefault(satir.value, set()).add(rol)
    assert gercek == BEKLEYEN_HUCRE_GORUNTUSU


def _karsilanan_hucreler() -> set[tuple[Satir, str]]:
    """Etkin bir yazma kuralının karşıladığı (satır, rol) hücreleri."""
    return {
        (kural.satir, rol)
        for kural in KURALLAR
        if kural.tur is KuralTuru.YAZMA and kural.satir is not Satir.OTURUM
        for rol in kural_rolleri(kural)
    }


def test_rol_matrisi_hucre_anlik_goruntusu() -> None:
    """Tasarım §4.4.2 "Testler (F1b)", §10.6: matristeki her (satır, rol, Y) hücresi ya etkin
    bir yazma kuralıyla karşılanır ya da fazıyla bekleyen listesindedir. Bekleyende olup kuralı
    olan hücre bayattır (bağlandıysa listeden çıkmalıdır); bekleyendeki her hücre Y'dir."""
    karsilanan = _karsilanan_hucreler()
    for satir, hucreler in MATRIS.items():
        for rol, (harf, _) in hucreler.items():
            if harf != "Y":
                continue
            assert ((satir, rol) in karsilanan) != ((satir, rol) in BEKLEYEN_HUCRELER), (
                satir,
                rol,
            )
    for satir, rol in BEKLEYEN_HUCRELER:
        assert MATRIS[satir][rol][0] == "Y", (satir, rol)


def test_etkin_hucreler_bekleyende_olmayan_y_hucreleridir() -> None:
    """Hesap teslim pusulasının "bu programda sizin işiniz" özeti ve hücre görüntüsü tek yüklem."""
    assert [s.value for s in etkin_hucreler("yonetici")] == [
        "M1",
        "M2",
        "M9",
        "KULLANICILAR",
        "GUVENLIK",
        "AYARLAR",
        "KISISEL_VERI",
        "GUNCELLEME",
        "KENDI",
    ]
    # YK rollerinin M2 hücresi birlik kişilerinin uçlarıyla bağlandı (F1c 4. adım).
    for rol in YK_ROLLERI:
        assert [s.value for s in etkin_hucreler(rol)] == ["M2", "M9", "KENDI"]
    # DK'nin M8 hücresi geri yükleme kartının "Gördüm"üyle bağlandı (F1b-2 (c)).
    assert [s.value for s in etkin_hucreler("denetleme_kurulu")] == ["M8", "KENDI"]
    assert [s.value for s in etkin_hucreler("mudur")] == ["KENDI"]
    for rol in ROLLER:
        assert set(etkin_hucreler(rol)) == {
            satir for satir, rol_ in _karsilanan_hucreler() if rol_ == rol
        }


def test_bekleyen_dipnotlar_anlik_goruntusu() -> None:
    """Gerçek servisi olmayan dipnotlar, fazlarıyla (yalnız küçülebilir). Her dipnot (1-10) ya
    bağlı bir eylemle gerçek serviste sınanır ya da burada bekler; ikisi birden olamaz."""
    assert dict(BEKLEYEN_DIPNOTLAR) == {
        1: "F2",
        2: "F3",
        3: "F4",
        4: "F4",
        6: "F4",
        7: "F2",
        8: "F4",
        9: "F5",
        10: "F2",
    }
    for dipnot in range(1, 11):
        bagli = any(
            kural.dipnot == dipnot and eylem not in BAGLANMAMIS_EYLEMLER
            for eylem, kural in EYLEM_KURALLARI.items()
        )
        assert bagli != (dipnot in BEKLEYEN_DIPNOTLAR), dipnot


def test_f1b_fazli_bekleyen_kalmadi() -> None:
    """F1b'nin 2. adımının kapısı (plan F1b-2 kullanıcı kararı: "her fazın kapısına 'bu fazın
    hücreleri ve dipnotları bağlandı' maddesi girer"): üç bekleyen listesinde de faz değeri "F1b"
    olan kalmaz — Kullanıcılar hücresi uçlarıyla, Denetleme Kurulunun M8 hücresi, ⁵ dipnotu ve
    `GERI_YUKLEME_GORDUM` eylemi geri yükleme kartının "Gördüm"üyle bağlandı."""
    assert "F1b" not in set(BEKLEYEN_HUCRELER.values())
    assert "F1b" not in set(BEKLEYEN_DIPNOTLAR.values())
    assert "F1b" not in set(BAGLANMAMIS_EYLEMLER.values())
    assert (Satir.M8, "denetleme_kurulu") not in BEKLEYEN_HUCRELER
    assert 5 not in BEKLEYEN_DIPNOTLAR
    assert Eylem.GERI_YUKLEME_GORDUM not in BAGLANMAMIS_EYLEMLER


def test_f1c_fazli_bekleyen_kalmadi() -> None:
    """F1c kapısı (13. adım; tasarım §14 ortak madde 4; 6. adımın "Bitti" ölçütü de buydu): üç
    bekleyen listesinde faz değeri "F1c" ya da adı "F1" ile başlayan kalem yoktur; listelerde yalnız
    sonraki fazlar (F2 ve sonrası) kalır. `DENETIM_YAZMA` bölündü: görev bölümü ve denetim planı yeni
    eylemle bağlandı, kalanın fazı F2'dir (md. 14/5 çağrısı; tasarım §4.4.2 "Testler")."""
    for liste in (BEKLEYEN_HUCRELER, BEKLEYEN_DIPNOTLAR, BAGLANMAMIS_EYLEMLER):
        fazlar = set(liste.values())
        assert not {faz for faz in fazlar if faz.startswith("F1")}, fazlar
        assert fazlar <= {"F2", "F3", "F4", "F5", "F6", "F7", "F8+"}, fazlar
    assert Eylem.DK_GOREV_BOLUMU_YAZMA not in BAGLANMAMIS_EYLEMLER
    assert BAGLANMAMIS_EYLEMLER[Eylem.DENETIM_YAZMA] == "F2"


def test_m8_yazma_uclari_gordum_ve_dk_gorev_bolumudur_ve_yalniz_dk_ya_aciktir() -> None:
    """M8'in bugünkü yazma kuralları "Gördüm", DK görev bölümü (F1c 6. adım) ve görev bölümü
    tutanağıyla denetim planının belgesidir (E02, F1c 10. adım); hepsi ⁵ dipnotunu adıyla anar, yalnız
    Denetleme Kuruluna açılır (YK rolleri DK modülüne yazamaz, program yöneticisi de; tasarım §4.4.2
    ⁵)."""
    kurallar = [k for k in KURALLAR if k.satir is Satir.M8 and k.tur is KuralTuru.YAZMA]
    assert sorted((k.uc, tuple(sorted(k.yontemler)), k.dipnot) for k in kurallar) == [
        ("oab-dk-duty-assignment", ("POST",), 5),
        ("oab-document-e02", ("POST",), 5),
        ("security-integrity-restore-seen", ("POST",), 5),
    ]
    for kural in kurallar:
        assert kural_rolleri(kural) == frozenset({"denetleme_kurulu"})
    erisim = [k for k in KURALLAR if k.satir is Satir.ERISIM_GUNLUGU]
    assert [(k.uc, k.tur) for k in erisim] == [("access-log", KuralTuru.OKUMA)]
    assert kural_rolleri(erisim[0]) == okuyabilen_roller(Satir.ERISIM_GUNLUGU) == Y_DK


# ============================================================ eylemlerin servise bağlanışı

_BACKEND = Path(__file__).resolve().parents[3]

#: Yetki kapısının işlevleri (`rol_izinleri.yetki`, `rol_izinleri.yetki_oturum`).
_KAPI_ISLEVLERI = frozenset({"yetki", "yetki_oturum"})


def _eylem_sinifi_mi(dugum: ast.expr) -> bool:
    """`Eylem` ya da `rol_izinleri.Eylem` (nitelikli ad)."""
    if isinstance(dugum, ast.Name):
        return dugum.id == "Eylem"
    return isinstance(dugum, ast.Attribute) and dugum.attr == "Eylem"


def _kapiya_sorulan_eylemler(kaynak: str) -> set[str]:
    """Kaynakta `yetki(...)` ya da `yetki_oturum(...)` ÇAĞRISININ argümanında geçen `Eylem.<AD>`
    adları (AST taraması: belge dizesi, yorum ve çağrı dışındaki anma sayılmaz)."""
    adlar: set[str] = set()
    for dugum in ast.walk(ast.parse(kaynak)):
        if not isinstance(dugum, ast.Call):
            continue
        islev = dugum.func
        if isinstance(islev, ast.Name):
            islev_adi = islev.id
        elif isinstance(islev, ast.Attribute):
            islev_adi = islev.attr
        else:
            continue
        if islev_adi not in _KAPI_ISLEVLERI:
            continue
        for arguman in [*dugum.args, *(k.value for k in dugum.keywords)]:
            for alt in ast.walk(arguman):
                if isinstance(alt, ast.Attribute) and _eylem_sinifi_mi(alt.value):
                    adlar.add(alt.attr)
    return adlar


def _servislerde_kapiya_sorulan_eylemler() -> set[Eylem]:
    """`apps/` altındaki üretim kaynaklarında kapıya sorulan eylemler (testler, göçler ve
    tanımın kendisi hariç)."""
    adlar: set[str] = set()
    for yol in sorted((_BACKEND / "apps").rglob("*.py")):
        if "tests" in yol.parts or yol.name == "rol_izinleri.py" or "migrations" in yol.parts:
            continue
        adlar |= _kapiya_sorulan_eylemler(yol.read_text(encoding="utf-8"))
    return {Eylem[ad] for ad in adlar}


def test_eylem_taramasi_yalniz_kapi_cagrisini_sayar() -> None:
    """Belge dizesinde ya da yorumda anılan eylem bağlı sayılmaz (yalnız küçülebilen bekleyen
    listesinden bir eylem yorumla çıkarılamasın); iki çağrı biçimi de sayılır."""
    kaynak = '''
"""Modül başlığı `rol_izinleri.Eylem.MALI_KAYIT` ile kapıya sorar."""
# yetki_oturum(Eylem.DONEM_KILIDI)
from apps.okul import rol_izinleri
from apps.okul.rol_izinleri import Eylem, yetki


def servis(rol):
    """`Eylem.HESAP_GECISI` ile sorulur."""
    eylem = Eylem.DEK_YENILEME
    yetki(rol, Eylem.HESAP_YONETIMI)
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURTARMA_ANAHTARI, kayit=None)
    rol_izinleri.yetki(rol, eylem=rol_izinleri.Eylem.GERI_YUKLEME)
    return eylem
'''
    assert _kapiya_sorulan_eylemler(kaynak) == {
        "HESAP_YONETIMI",
        "KURTARMA_ANAHTARI",
        "GERI_YUKLEME",
    }


def test_eylem_baglama_anlik_goruntusu() -> None:
    """Bağlı eylemin servisi `yetki(…, Eylem.<AD>)` ya da `yetki_oturum(Eylem.<AD>)` ÇAĞIRIR
    (AST; belge dizesi ve yorum sayılmaz); bağlanmamış eylem fazıyla donmuş listededir (yalnız
    küçülebilir). Bağlanmamış görünüp kaynakta çağrılan eylem bayattır."""
    cagrilan = _servislerde_kapiya_sorulan_eylemler()
    assert cagrilan == set(Eylem) - set(BAGLANMAMIS_EYLEMLER)
    assert cagrilan == {
        Eylem.HESAP_YONETIMI,
        Eylem.KURTARMA_ANAHTARI,
        Eylem.GERI_YUKLEME,
        Eylem.YEDEK_INDIRME,
        Eylem.BOSTA_SURE_YAZMA,
        Eylem.BIRLIK_DONEMI_YAZMA,
        Eylem.KURAL_SURUMU_SECIMI,
        Eylem.GERI_YUKLEME_GORDUM,
        Eylem.DK_GOREV_BOLUMU_YAZMA,
    }


# ============================================================ yetenekler


def test_yetenekler_kurallardan_turer() -> None:
    """Rolün yeteneği kümedeki HER (uç, yöntem) ona açıksa vardır; her çiftin kuralı vardır."""
    for ad, ciftler in YETENEKLER.items():
        assert ciftler, ad
        for rol in ROLLER:
            beklenen = all(rol in rol_izinleri.acik_roller(uc, y) for uc, y in ciftler)
            assert (ad in yetenekler(rol)) is beklenen, (ad, rol)
    assert yetenekler(None) == []
    assert yetenekler("bilinmeyen") == []


def _on_yuzun_yetenek_adlari() -> list[str]:
    """Ön yüzün `frontend/src/modules/oturum/api.ts` `YETENEK_ADLARI` dizisi (kaynaktan okunur;
    dizi yalnız çift tırnaklı adlardan oluşmalıdır — yorum ya da hesaplanan öğe kabul edilmez)."""
    yol = _depo_koku() / "frontend" / "src" / "modules" / "oturum" / "api.ts"
    eslesme = re.search(
        r"export const YETENEK_ADLARI = \[(.*?)\] as const;", yol.read_text(encoding="utf-8"), re.S
    )
    assert eslesme is not None, f"{yol}: `YETENEK_ADLARI` dizisi bulunamadı."
    ogeler = [o.strip() for o in eslesme.group(1).split(",") if o.strip()]
    bicimsiz = [o for o in ogeler if not re.fullmatch(r'"[a-z_]+"', o)]
    assert bicimsiz == [], bicimsiz
    return [o.strip('"') for o in ogeler]


def test_yetenek_adlari_on_yuzle_birebir() -> None:
    """Ön yüz süzmesinin tek kaynağı yeteneklerdir (plan F1b-2): ön yüzün ad listesi (ve ondan
    türeyen `YetenekAdi` türü) arka yüzün `YETENEKLER`'iyle AYNIDIR. Bir taraftaki ad değişince
    bu test düşer; adı değişen yetenek ön yüzde sessizce "yok" sayılmaz."""
    assert _on_yuzun_yetenek_adlari() == sorted(YETENEKLER)


def test_yetenek_adlari_ve_rollerin_yetenekleri_anlik_goruntusu() -> None:
    """Adların listesi ve her rolün yetenekleri (anlık görüntü; ön yüzle eşitliği
    `test_yetenek_adlari_on_yuzle_birebir` sınar)."""
    tum = sorted(YETENEKLER)
    assert tum == [
        "ayrilis_havuzu",
        "birlik_donemi_yazma",
        "birlik_kisi_yazma",
        "bosta_sure_yazma",
        "butunluk_denetim",
        "ders_yili_yazma",
        "dk_gorev_bolumu_yazma",
        "dk_yedek_cagirma",
        "eokul_aktarimi",
        "erisim_gunlugu",
        "geri_yukleme_gordum",
        "gorev_alma_engeli",
        "gorev_bolumu_yazma",
        "guncelleme",
        "guvenlik",
        "iki_depo",
        "kapali_gun_yazma",
        "karar_taslagi_uretme",
        "kisi_yazma",
        "kullanicilar",
        "kurulum_tamamlama",
        "okul_karti_yazma",
        "organ_yazma",
        "son_oturum_onay",
        "temsilci_yazma",
        "toplanti_gunu_yazma",
        "uyelik_dusurme",
        "veli_listesi",
        "yol_haritasi",
    ]
    # "Gördüm" ve Denetleme Kurulunun görev bölümü yalnız Denetleme Kurulunundur; yönetim kurulunun
    # görev bölümünü ve yedek çağrısını yalnız sekreter yazar (tasarım §7.2 "Kim").
    yalniz_baskalari = {"geri_yukleme_gordum", "dk_gorev_bolumu_yazma", "gorev_bolumu_yazma"}
    assert yetenekler("yonetici") == [ad for ad in tum if ad not in yalniz_baskalari]
    # Görev alma engelini yönetim kurulu rolleri de yazar ve dayanağını okur (tasarım §4.4.2 ¹¹); düşme,
    # görev bölümü evrakı ve aylık toplantı günü sekreterle program yöneticisinindir (F1c 11. adım).
    yk_ortak = [
        "birlik_kisi_yazma",
        "gorev_alma_engeli",
        "organ_yazma",
        "son_oturum_onay",
        "temsilci_yazma",
    ]
    for rol in YK_ROLLERI - {"sekreter"}:
        assert yetenekler(rol) == yk_ortak
    assert yetenekler("sekreter") == sorted(
        [
            *yk_ortak,
            "gorev_bolumu_yazma",
            "karar_taslagi_uretme",
            "toplanti_gunu_yazma",
            "uyelik_dusurme",
        ]
    )
    assert yetenekler("denetleme_kurulu") == [
        "butunluk_denetim",
        "dk_gorev_bolumu_yazma",
        "erisim_gunlugu",
        "geri_yukleme_gordum",
    ]
    assert yetenekler("mudur") == []


def test_kullanicilar_yetenegi_satirin_butun_uclarini_kapsar() -> None:
    """Kullanıcılar ekranı tek yetenektir (`kullanicilar`): Kullanıcılar satırına bağlı her (uç,
    yöntem) — hesap teslim pusulası dahil (plan F1b-2 "E63") — o yeteneğe girer; ön yüz bir eylemi
    yetenekte olmadığı için sessizce gizlemesin. HEAD okumanın eşidir, ayrı sayılmaz."""
    satirin_uclari = {
        (kural.uc, yontem)
        for kural in KURALLAR
        if kural.satir is Satir.KULLANICILAR
        for yontem in kural.yontemler
        if yontem != "HEAD"
    }
    assert satirin_uclari == set(YETENEKLER["kullanicilar"])
    assert ("account-handover-slip", "POST") in YETENEKLER["kullanicilar"]


def test_yetenegin_kuralsiz_cifti_reddedilir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        rol_izinleri.YETENEKLER,
        "bayat",
        frozenset({("boyle-bir-uc-yok", "GET")}),
    )
    with pytest.raises(ValueError, match="kuralı olmayan"):
        rol_izinleri._yetenekleri_dogrula()


# ============================================================ izinli_mi


def test_izinli_mi_adsiz_uc_ve_bilinmeyen_rol_kapali() -> None:
    assert rol_izinleri.izinli_mi("school-year-list", "GET", "muhasip") is True
    assert rol_izinleri.izinli_mi("school-year-list", "get", "muhasip") is True
    assert rol_izinleri.izinli_mi(None, "GET", "yonetici") is False
    assert rol_izinleri.izinli_mi("school-year-list", "GET", None) is False
    assert rol_izinleri.izinli_mi("school-year-list", "GET", "admin") is False
    assert rol_izinleri.izinli_mi("school-year-list", "OPTIONS", "yonetici") is False
    assert rol_izinleri.izinli_mi("security-enable", "POST", "yonetici") is False


def test_parametre_denetcisi_yanlis_derse_istek_kesilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parametre denetçili kural (F1b'de yok; mekanizma aileden): denetçi yanlışsa kapalı,
    istek yoksa fail-closed."""
    kural = RolKurali(
        "school-year-list", OKUMA, Satir.M1, KuralTuru.OKUMA, parametre=yalniz_sorgu("q")
    )
    monkeypatch.setitem(rol_izinleri._TABLO_KURAL, ("school-year-list", "GET"), kural)
    istek = RequestFactory().get("/api/v1/school-years/?q=1")
    assert rol_izinleri.izinli_mi("school-year-list", "GET", "muhasip", istek) is True
    istek = RequestFactory().get("/api/v1/school-years/?format=json")
    assert rol_izinleri.izinli_mi("school-year-list", "GET", "muhasip", istek) is False
    assert rol_izinleri.izinli_mi("school-year-list", "GET", "muhasip") is False


# ============================================================ parametre denetçileri (aile)


def test_yalniz_sorgu_denetcisi_bilinmeyen_anahtari_keser() -> None:
    denetci = yalniz_sorgu("q", "limit")

    assert denetci(RequestFactory().get("/api/v1/x/?q=a&limit=5")) is True
    assert denetci(RequestFactory().get("/api/v1/x/")) is True
    assert denetci(RequestFactory().get("/api/v1/x/?q=a&format=json")) is False


@pytest.mark.parametrize(
    ("icerik", "govde", "sorgu", "gecer"),
    [
        ("application/json", b'{"ad": "x"}', "", True),
        ("application/json", b"", "", True),  # boş gövde: görünüm doğrulamayla reddeder
        ("application/json", b'{"ad": "x", "yasak": ""}', "", False),  # değer değil varlık
        ("application/json", b'{"ad": "x"}', "?yasak=1", False),
        ("application/x-www-form-urlencoded", b"ad=x", "", False),
        ("application/json", b"[1, 2]", "", False),
        ("application/json", b"{bozuk", "", False),
        ("application/json; charset=utf-7", b'{"ad":"x","yasak+AF8-":"1"}', "", False),
        ("application/json; charset=latin-1", b'{"ad": "x"}', "", False),
        ("application/json; charset=UTF-8", b'{"ad": "x"}', "", True),
    ],
)
def test_govdede_yok_denetcisi_okuyamadigini_gecirmez(
    icerik: str, govde: bytes, sorgu: str, gecer: bool
) -> None:
    """Denetçi ile görünüm aynı baytları farklı okuyamasın: JSON nesnesi, UTF-8, fail-closed."""
    istek = RequestFactory().generic("POST", "/api/v1/x/" + sorgu, govde, content_type=icerik)

    assert govdede_yok("yasak")(istek) is gecer


def test_karakter_kumesi_adi_esnek_okunur() -> None:
    assert utf8_mi(None) is True
    assert utf8_mi(' "UTF_8" ') is True
    assert utf8_mi("utf8") is True
    assert utf8_mi("windows-1254") is False


def test_ad_alanli_uc_adi_cozulur() -> None:
    assert uc_adi("/api/v1/security/session/") == "security-session"
    assert uc_adi("/api/v1/boyle-bir-uc-yok/") is None
