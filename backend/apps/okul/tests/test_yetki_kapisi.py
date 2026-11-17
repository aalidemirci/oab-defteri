"""Servis katmanının yetki kapısı (tasarım §4.4.2 "iki katman", dipnotlar 1-10; plan F1b-2).

`yetki(rol, eylem, kayıt)`: kapanmış dönem, maskesiz okuma, kişisel veri içeren çıktı,
rol-özel işaretler ve kayıt sahipliği tek kapıdan geçer; ret `RolYetkisiz` → 403
`rol_yetkisiz`. Dipnotların servisleri F1b'de sonraki fazlardaydı (müdür yazıları F2/F4, mali
kayıtlar F3, DK modülü F4): F1b'de her dipnot KAPININ KENDİSİYLE sahte kayıtla sınanır
(`test_rol_matrisi_dipnot_servis_testi`; plan F1b-2 kullanıcı kararı). Bağlı servisler
(hesap yönetimi, kurtarma anahtarı, boşta süre, şifreli yedeğin kaydedilmesi, uygulama içi geri
yükleme) ayrıca gerçek çağrıyla sınanır: rol kapısının ardından servis de reddeder (derin
savunma). ⁵ gerçek serviste de sınanır: Denetleme Kurulunun geri yükleme kartındaki "Gördüm"ü
(`test_dipnot_bes_gercek_serviste_yalniz_denetleme_kurulu`; plan F1b-2 kullanıcı kararı). F2 7. adımdan
beri ¹ (müdürün kendi yazıları, sahiplik) ve ⁷ (gelen-giden evrak; müdür yazısının programca kaydı)
de gerçek serviste sınanır (dosyanın sonu; uydurma veriyle). F2 8. adımdan beri ¹⁰ de gerçek
serviste sınanır: veli adlı E07 ve E08 çıktısı (`genel_kurul_evraki.adli_uret_ve_ver`).
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass

import pytest
from django.utils import timezone
from rest_framework import serializers

from apps.oab.models import (
    AgendaItem,
    AssemblyCaller,
    AssemblyKind,
    AssemblyStatus,
    DocumentDirection,
    DocumentRecord,
    GeneralAssembly,
    OabTerm,
    TermStatus,
)
from apps.oab.services import denetim, gelen_giden_evrak, genel_kurul
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.okul import rol_izinleri
from apps.okul.models import Account, AccountRole, AccountStatus, AuditTrail, SchoolConfig
from apps.okul.oturum import OTURUM, SISTEM, Yazar, yazar_olarak
from apps.okul.rol_izinleri import (
    BAGLANMAMIS_EYLEMLER,
    EYLEM_KURALLARI,
    MATRIS,
    ROLLER,
    Eylem,
    EylemKurali,
    Satir,
    yazabilen_roller,
    yetki,
    yetki_oturum,
)
from apps.okul.services import app_password, encrypted_backup, hesaplar, recovery_key_document
from apps.okul.services import setup as setup_service
from apps.okul.tests.hesap_ortak import GECICI_PAROLA, YENI_PAROLA, hesap_ac, muhurle, sarmal
from apps.okul.views import _service_errors
from apps.okul.views_oturum import guvenlik_hatalari
from conftest import TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA, oturumu_ac_test
from shared.exceptions import ROL_YETKISIZ_MESAJI, RolYetkisiz, od_exception_handler

YK = frozenset({"baskan", "baskan_yardimcisi", "muhasip", "sekreter"})


@dataclass(frozen=True)
class SahteKayit:
    """Kapının sorduğu kayıt (Protocol `YetkiKaydi`): dönemi kapalı mı, kimin kaydı."""

    donem_kapali: bool = False
    sahip_rol: str | None = None


def _gecer(rol: str, eylem: Eylem, kayit: SahteKayit | None = None) -> bool:
    try:
        yetki(rol, eylem, kayit)
    except RolYetkisiz:
        return False
    return True


def _gecen_roller(eylem: Eylem, kayit: SahteKayit | None = None) -> frozenset[str]:
    return frozenset(rol for rol in ROLLER if _gecer(rol, eylem, kayit))


# ============================================================ dipnot başına kapı testi

#: Dipnot → (eylem → izinli roller). Tasarım §4.4.2 dipnotlarının lafzı.
_DIPNOT_EYLEMLERI: dict[int, dict[Eylem, frozenset[str]]] = {
    1: {
        # Müdür genel kurulun öteki işlerinde okurdur.
        Eylem.GENEL_KURUL_YAZMA: YK | {"yonetici"},
        Eylem.GENEL_KURUL_YENI_OKUL_DAVETI: frozenset({"mudur"}),
        Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR: frozenset({"mudur"}),
    },
    2: {
        # Mali kayıtlar yalnız muhasip; rol-özel işaretlerin tek kaynağı bu dipnot.
        Eylem.MALI_KAYIT: frozenset({"muhasip"}),
        Eylem.ISARET_DEFTERE_GECIRME: frozenset({"muhasip"}),
        Eylem.ISARET_TEFBIS_GIRISI: frozenset({"yonetici"}),
        Eylem.ISARET_KARAR_DEFTERE_ISLENDI: frozenset({"sekreter"}),
        Eylem.KARAR_DEFTERDE_SAKAT: frozenset({"sekreter"}),
    },
    3: {
        Eylem.HARCAMA_MALI_HALKA: frozenset({"muhasip"}),
        Eylem.HARCAMA_KARAR_KOMISYON_BELGE: YK | {"yonetici"},
    },
    # Talep halkası yalnız müdürün; program yöneticisi taslağını hazırlamaz.
    4: {Eylem.HARCAMA_TALEP: frozenset({"mudur"})},
    # YK rolleri ve program yöneticisi DK modülüne yazamaz.
    5: {
        Eylem.DENETIM_YAZMA: frozenset({"denetleme_kurulu"}),
        Eylem.DK_GOREV_BOLUMU_YAZMA: frozenset({"denetleme_kurulu"}),
        Eylem.DK_GENEL_KURUL_YAZMA: frozenset({"denetleme_kurulu"}),
        Eylem.GERI_YUKLEME_GORDUM: frozenset({"denetleme_kurulu"}),
    },
    6: {Eylem.MUDUR_UYARISI: frozenset({"mudur"})},
    # Müdür gelen-giden evraka yazmaz (O⁷). Kendi yazısının evrak defteri kaydını program,
    # müdür yazısının eylemiyle (¹, ⁴, ⁶) yan etki olarak işler: ayrı eylemi ve ucu yoktur.
    7: {Eylem.EVRAK_KAYDI: YK | {"yonetici"}},
    8: {
        Eylem.DONEM_KILIDI: frozenset({"yonetici"}),
        Eylem.HESAP_GECISI: frozenset({"yonetici"}),
        Eylem.DEK_YENILEME: frozenset({"yonetici"}),
    },
    # Müdür kantin ve servis akışlarında iş yapan rol değildir.
    9: {Eylem.KANTIN_SERVIS_YAZMA: YK | {"yonetici"}},
    # Kişisel veri içeren çıktı ve maskesiz T.C. kimlik no yalnız program yöneticisi.
    10: {
        Eylem.KISISEL_VERI_CIKTISI: frozenset({"yonetici"}),
        Eylem.MASKESIZ_TCKN: frozenset({"yonetici"}),
    },
}


@pytest.mark.parametrize("dipnot", range(1, 11))
def test_rol_matrisi_dipnot_servis_testi(dipnot: int) -> None:
    """Tasarım §4.4.2 Testler, §10.6: her dipnot için izinli roller geçer, öteki her rol
    `RolYetkisiz` alır. ², ⁴, ⁵, ⁶'da kapanmış dönem ve kayıt sahipliği de sınanır. Gerçek
    servis gelince aynı test o fazda servisle genişler (`BEKLEYEN_DIPNOTLAR`)."""
    eylemler = _DIPNOT_EYLEMLERI[dipnot]
    assert set(eylemler) == {e for e, k in EYLEM_KURALLARI.items() if k.dipnot == dipnot}
    for eylem, izinli in eylemler.items():
        assert _gecen_roller(eylem) == izinli, eylem
        assert _gecen_roller(eylem, SahteKayit()) == izinli, eylem
        for rol in set(ROLLER) - izinli:
            with pytest.raises(RolYetkisiz) as hata:
                yetki(rol, eylem)
            assert str(hata.value) == ROL_YETKISIZ_MESAJI

    kapali = SahteKayit(donem_kapali=True)
    if dipnot == 2:
        # Kapanmış dönemde yalnız işaret alanları yazılır (§5 O2); tutar değişmez.
        assert _gecen_roller(Eylem.ISARET_DEFTERE_GECIRME, kapali) == {"muhasip"}
        assert _gecen_roller(Eylem.ISARET_TEFBIS_GIRISI, kapali) == {"yonetici"}
        assert _gecen_roller(Eylem.ISARET_KARAR_DEFTERE_ISLENDI, kapali) == {"sekreter"}
        assert _gecen_roller(Eylem.MALI_KAYIT, kapali) == frozenset()
        assert _gecen_roller(Eylem.KARAR_DEFTERDE_SAKAT, kapali) == frozenset()
    if dipnot in (1, 4, 5, 6):
        # Kayıt sahipliği rol düzeyindedir: sahibi olan rolün hesapları düzenler (¹: müdürün yazıları,
        # F2 7. adımın ilk sahiplikli eylemleri; ⁵: Denetleme Kurulunun kendi raporu ve çağrısı).
        for eylem in (e for e, k in EYLEM_KURALLARI.items() if k.dipnot == dipnot and k.sahiplik):
            (sahip,) = eylemler[eylem]
            assert _gecer(sahip, eylem, SahteKayit(sahip_rol=sahip))
            assert not _gecer(sahip, eylem, SahteKayit(sahip_rol="yonetici"))
            assert not _gecer(sahip, eylem, kapali)


def test_her_dipnotun_eylemi_var_ve_kume_kapali() -> None:
    """Eylem kümesi kapalıdır (anlık görüntü); her dipnot (1-10) en az bir eyleme bağlıdır."""
    assert set(range(1, 11)) == {k.dipnot for k in EYLEM_KURALLARI.values()} - {None}
    assert set(EYLEM_KURALLARI) == set(Eylem)
    dipnotsuz = {e for e, k in EYLEM_KURALLARI.items() if k.dipnot is None}
    assert dipnotsuz == {
        Eylem.HESAP_YONETIMI,
        Eylem.KURTARMA_ANAHTARI,
        Eylem.GERI_YUKLEME,
        Eylem.YEDEK_INDIRME,
        Eylem.BOSTA_SURE_YAZMA,
        Eylem.BIRLIK_DONEMI_YAZMA,
        Eylem.KURAL_SURUMU_SECIMI,
    }
    for eylem in dipnotsuz:
        assert _gecen_roller(eylem) == {"yonetici"}, eylem
    # Dipnotlu eylemlerden bugün DK'nin "Gördüm"ü (⁵, F1b-2 (c)), görev bölümü (⁵, F1c 6. adım),
    # genel kurul yazma kapısı (¹, F2 4. adım), kişisel veri içeren çıktı (¹⁰, F2 5. adım: genel
    # kurulun katılım işaretleri), müdürün yazıları (¹), DK'nin md. 14/5 çağrısı (⁵) ve gelen-giden
    # evrak (⁷) (F2 7. adım) servise bağlıdır.
    assert set(BAGLANMAMIS_EYLEMLER) == set(Eylem) - dipnotsuz - {
        Eylem.GERI_YUKLEME_GORDUM,
        Eylem.DK_GOREV_BOLUMU_YAZMA,
        Eylem.GENEL_KURUL_YAZMA,
        Eylem.KISISEL_VERI_CIKTISI,
        Eylem.GENEL_KURUL_YENI_OKUL_DAVETI,
        Eylem.OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR,
        Eylem.DK_GENEL_KURUL_YAZMA,
        Eylem.EVRAK_KAYDI,
    }


def test_eylemler_matrisi_asmaz() -> None:
    """İzinli roller eylemin satırındaki Y hücrelerini aşamaz (plan F1b-2); dipnotlu Y hücresi
    yalnız o dipnotu anan eyleme açılır. Okur hücresinin TEK istisnası ²'nin rol-özel
    işaretidir (tasarım §4.4.2 "Okuma"; "TEFBİS'e girildi" program yöneticisinde); ⁷ müdüre
    evrak defterine yazma vermez. Hücreler modülün yüklemi kullanılmadan, matristen okunur."""
    for eylem, kural in EYLEM_KURALLARI.items():
        assert kural.satir is not Satir.OTURUM, eylem
        assert kural.roller <= yazabilen_roller(kural.satir, kural.dipnot), eylem
        assert kural.dayanak.strip(), eylem
        for rol in kural.roller:
            harf, hucre_dipnotu = MATRIS[kural.satir][rol]
            assert (harf == "Y" and hucre_dipnotu in (None, kural.dipnot)) or (
                harf == "O" and hucre_dipnotu == kural.dipnot == 2
            ), (eylem, rol)


@pytest.mark.parametrize(
    "kural",
    [
        EylemKurali(Satir.M8, frozenset({"yonetici"}), dipnot=5),
        EylemKurali(Satir.M5, frozenset({"yonetici"})),
        EylemKurali(Satir.M13_M14, frozenset({"mudur"}), dipnot=9),
        EylemKurali(Satir.OTURUM, frozenset({"yonetici"})),
        EylemKurali(Satir.M1, frozenset({"yonetici"}), dipnot=11),
        EylemKurali(Satir.M10, frozenset({"mudur"}), dipnot=7),
    ],
    ids=[
        "yonetici_dk_modulune",
        "o2_dipnotsuz",
        "mudur_kantine",
        "matris_disi",
        "olmayan_dipnot",
        "mudur_evrak_defterine",
    ],
)
def test_matrisi_asan_eylem_modulu_yuklemez(
    kural: EylemKurali, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(rol_izinleri.EYLEM_KURALLARI, Eylem.DENETIM_YAZMA, kural)
    with pytest.raises(ValueError):
        rol_izinleri._eylemleri_dogrula()


# ============================================================ rolün kaynağı ve ret türü


def test_yetki_oturum_yazarsiz_ve_sistem_yazarini_reddeder() -> None:
    with yazar_olarak(None), pytest.raises(RolYetkisiz):
        yetki_oturum(Eylem.HESAP_YONETIMI)
    with yazar_olarak(SISTEM), pytest.raises(RolYetkisiz):
        yetki_oturum(Eylem.HESAP_YONETIMI)
    with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol="yonetici")):
        yetki_oturum(Eylem.HESAP_YONETIMI)
    with pytest.raises(RolYetkisiz):
        yetki(None, Eylem.HESAP_YONETIMI)


def test_yetki_rolu_istek_basindaki_yazardan_okur() -> None:
    """Rol istek başındaki yazar görüntüsüdür (denetim izinin yazarıyla aynı): istek sürerken
    oturum başka hesaba geçse de karar değişmez (planın "`OTURUM.hesap().rol`" lafzının istek
    başındaki karşılığı)."""
    with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol="yonetici")):
        oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici="muhasip", rol="muhasip")
        yetki_oturum(Eylem.BOSTA_SURE_YAZMA)
    oturumu_ac_test()
    with (
        yazar_olarak(Yazar(hesap_id="0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", rol="muhasip")),
        pytest.raises(RolYetkisiz),
    ):
        assert OTURUM.hesap_id() == TEST_HESAP_ID
        yetki_oturum(Eylem.BOSTA_SURE_YAZMA)


def test_rol_yetkisiz_403_ve_kodu() -> None:
    """Ret `ValueError` ya da `OSError` değildir; hata işleyicisi 403 `rol_yetkisiz` verir."""
    assert not issubclass(RolYetkisiz, ValueError | OSError)
    yanit = od_exception_handler(
        RolYetkisiz(), {"view": None, "args": (), "kwargs": {}, "request": None}
    )
    assert yanit is not None
    assert yanit.status_code == 403
    assert yanit.data == {"code": "rol_yetkisiz", "message": ROL_YETKISIZ_MESAJI, "fields": {}}


@pytest.mark.parametrize("sarici", [_service_errors, guvenlik_hatalari])
def test_rol_yetkisiz_servis_hata_saricilarinda_400e_donmez(
    sarici: Callable[[], AbstractContextManager[None]],
) -> None:
    """Görünümlerin hata sarmalayıcıları `ValueError`'ı 400'e çevirir; rol reddi geçer."""
    with pytest.raises(RolYetkisiz), sarici():
        raise RolYetkisiz
    with pytest.raises(serializers.ValidationError), sarici():
        raise ValueError("Türkçe ileti")


# ============================================================ bağlı servisler (derin savunma)

MUHASIP_YAZARI = Yazar(hesap_id="0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", rol="muhasip")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "islem",
    ["ac", "kapat", "sifirla", "askidan_cikar", "sahipsiz_sil"],
)
def test_hesap_servisleri_yalniz_program_yoneticisi(islem: str) -> None:
    """Rol kapısının ardından servis de mühürlü satırın rolüyle hesap yönetimi yetkisini sorar;
    açık ve mühürlü bir muhasip hesabı kendi oturumunda hesap işlemi yapamaz, hiçbir şey
    yazılmaz."""
    muhasip = hesap_ac(AccountRole.MUHASIP, ad="Örnek Muhasip")
    muhasip = muhurle(Account.objects.get(pk=muhasip.id), status=AccountStatus.ACIK)
    hedef = hesap_ac(AccountRole.SEKRETER, ad="Örnek Sekreter")
    once = (AuditTrail.objects.count(), sarmal(hedef.id))
    islemler: dict[str, Callable[[], object]] = {
        "ac": lambda: hesaplar.open_account(
            by_hesap_id=muhasip.id,
            role=AccountRole.BASKAN,
            tanitici="baskan",
            display_name="Örnek Başkan",
            temp_password=GECICI_PAROLA,
        ),
        "kapat": lambda: hesaplar.close_account(by_hesap_id=muhasip.id, hesap_id=hedef.id),
        "sifirla": lambda: hesaplar.reset_password(
            by_hesap_id=muhasip.id, hesap_id=hedef.id, temp_password=YENI_PAROLA
        ),
        "askidan_cikar": lambda: hesaplar.unsuspend(by_hesap_id=muhasip.id, hesap_id=hedef.id),
        "sahipsiz_sil": lambda: hesaplar.remove_orphan_wraps(
            by_hesap_id=muhasip.id, hesap_idler=[]
        ),
    }

    with yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol="muhasip")):
        with pytest.raises(RolYetkisiz):
            islemler[islem]()

    assert (AuditTrail.objects.count(), sarmal(hedef.id)) == once
    assert not Account.objects.filter(role=AccountRole.BASKAN).exists()
    assert Account.objects.get(pk=hedef.id).status == AccountStatus.PAROLA_YENILENMELI


@pytest.mark.django_db
@pytest.mark.parametrize("kim", [None, SISTEM], ids=["yazarsiz", "sistem"])
def test_hesap_servisleri_yazarsiz_ve_sistem_yazariyla_calismaz(kim: Yazar | None) -> None:
    """Hesap işlemi kullanıcı eylemidir: yazar yoksa ya da `SISTEM` ise ret (plan F1b-1
    "by_hesap_id yazar bağlamındaki hesaba eşit olmalıdır"). Bildirimin kapatılması da."""
    hedef = hesap_ac(AccountRole.SEKRETER, ad="Örnek Sekreter")
    with yazar_olarak(kim):
        with pytest.raises(RolYetkisiz):
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hedef.id)
        with pytest.raises(RolYetkisiz):
            hesaplar.acknowledge_reset_notice(hesap_id=TEST_HESAP_ID)
    assert Account.objects.get(pk=hedef.id).status == AccountStatus.PAROLA_YENILENMELI


@pytest.mark.django_db
@pytest.mark.parametrize("islem", ["dogrula", "belge", "yenile"])
def test_kurtarma_anahtari_islemleri_yalniz_program_yoneticisi(islem: str) -> None:
    """Kurtarma anahtarının doğrulanması, belgesi ve yenilenmesi yalnız program yöneticisi;
    anahtar ve parola denenmez, dosya değişmez (tasarım §4.4.2 Güvenlik satırı).

    Yenilemede ret YALNIZ yazar kapısından gelebilmelidir: hesap gerçek program yöneticisi
    hesabıdır, parola doğrudur (kayıttaki rolün derin savunması ayrı testtedir). Bu, istek
    başında muhasip olan yazarın görünümünün oturumdaki program yöneticisi hesabını verdiği
    durumdur (plan F1b-2 "rolün kaynağı yazar bağlamıdır"). Dosya baytları değişmez: hatalı
    deneme sayacı da (güvenlik dosyasındadır) artmaz.
    """
    once = app_password.state_path().read_bytes()
    islemler: dict[str, Callable[[], object]] = {
        "dogrula": lambda: app_password.confirm_recovery_key(TEST_KURTARMA_ANAHTARI),
        "belge": lambda: recovery_key_document.render_recovery_key_pdf(TEST_KURTARMA_ANAHTARI),
        "yenile": lambda: app_password.renew_recovery_key(
            hesap_id=TEST_HESAP_ID, password=TEST_PAROLA
        ),
    }
    with yazar_olarak(MUHASIP_YAZARI), pytest.raises(RolYetkisiz):
        islemler[islem]()
    assert app_password.state_path().read_bytes() == once
    # Program yöneticisinin yazarıyla aynı çağrılar geçer.
    app_password.confirm_recovery_key(TEST_KURTARMA_ANAHTARI)
    assert app_password.verify_recovery_key(TEST_KURTARMA_ANAHTARI)


@pytest.mark.django_db
def test_kurtarma_yenileme_kayitta_program_yoneticisi_olmayan_hesabi_reddeder() -> None:
    """Derin savunma: yazar program yöneticisi olsa da parolası sorulacak hesabın kayıttaki
    rolü de program yöneticisi olmalı."""
    muhasip = hesap_ac(AccountRole.MUHASIP, ad="Örnek Muhasip")
    with pytest.raises(RolYetkisiz):
        app_password.renew_recovery_key(hesap_id=muhasip.id, password=GECICI_PAROLA)


@pytest.mark.django_db
def test_bosta_sure_yazimi_yalniz_program_yoneticisi() -> None:
    with yazar_olarak(MUHASIP_YAZARI), pytest.raises(RolYetkisiz):
        setup_service.set_idle_lock_minutes(dakika=15)
    assert SchoolConfig.load().idle_lock_minutes == 10
    assert setup_service.set_idle_lock_minutes(dakika=15) == 15


@pytest.mark.django_db
def test_yedek_indirme_yalniz_program_yoneticisi() -> None:
    once = AuditTrail.objects.count()
    with yazar_olarak(MUHASIP_YAZARI), pytest.raises(RolYetkisiz):
        encrypted_backup.sifreli_yedegi_kaydet("/uydurma/yer/yedek.odbak")
    assert AuditTrail.objects.count() == once


# ============================================================ ⁵ gerçek serviste: DK'nin "Gördüm"ü


def _geri_yukleme_satiri() -> AuditTrail:
    """Programın yazdığı (iz anahtarıyla mühürlü) bir `GERI_YUKLEME` satırı (uydurma dosya adı)."""
    from django.db import transaction

    from apps.okul import denetim_izi

    with transaction.atomic():
        return denetim_izi.olay(
            "GERI_YUKLEME",
            model=denetim_izi.GERI_YUKLEME_KAYDI,
            object_id="db-onceki-2026-11-01-091000.sqlite3",
        )


@pytest.mark.django_db
def test_dipnot_bes_gercek_serviste_yalniz_denetleme_kurulu() -> None:
    """Plan F1b-2 kullanıcı kararı: "⁵ (DK) gerçek serviste sınanır: DK'nin 'Gördüm'ü". Servis
    (`hesaplar.acknowledge_restore`) rol kapısını atlayan çağrıda da yalnız Denetleme Kurulunu
    geçirir: öteki her rolün yazarıyla `RolYetkisiz`, hiçbir satır yazılmaz; DK'nin açık, mühürlü
    hesabıyla `ISARET` satırı yazılır. Yazar DK görünse de işlemi yapanın MÜHÜRLÜ satırının rolü
    de DK olmalıdır (derin savunma: rol iki kez sorulur)."""
    geri = _geri_yukleme_satiri()
    dk = muhurle(
        hesap_ac(AccountRole.DENETLEME_KURULU, ad="Örnek Denetçi"), status=AccountStatus.ACIK
    )
    once = AuditTrail.objects.count()
    for rol in set(ROLLER) - {"denetleme_kurulu"}:
        with yazar_olarak(Yazar(hesap_id=str(dk.id), rol=rol)), pytest.raises(RolYetkisiz):
            hesaplar.acknowledge_restore(by_hesap_id=dk.id, seq=geri.seq)
    # Yazar DK diyor, işlemi yapanın satırı program yöneticisi: ikinci kapı reddeder.
    with (
        yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol="denetleme_kurulu")),
        pytest.raises(RolYetkisiz),
    ):
        hesaplar.acknowledge_restore(by_hesap_id=TEST_HESAP_ID, seq=geri.seq)
    assert AuditTrail.objects.count() == once

    with yazar_olarak(Yazar(hesap_id=str(dk.id), rol="denetleme_kurulu")):
        isaret = hesaplar.acknowledge_restore(by_hesap_id=dk.id, seq=geri.seq)

    assert isaret is not None and isaret.action == "ISARET"
    assert (str(isaret.account_id), isaret.role) == (str(dk.id), "denetleme_kurulu")
    assert AuditTrail.objects.count() == once + 1


# ============================================================ ¹ ve ⁷ gerçek serviste (F2 7. adım)


def _olaganustu_mudur_cagrisi(kurul: GeneralAssembly) -> genel_kurul.GenelKurulSonucu:
    return genel_kurul.cagir(
        kurul,
        called_by=AssemblyCaller.OKUL_MUDURU,
        call_reason=gko.OLAGANUSTU_NEDEN,
        gundem=gko.OLAGANUSTU_GUNDEM,
    )


@pytest.mark.django_db
def test_dipnot_bir_gercek_serviste_mudurun_kendi_yazisi_ve_sahiplik() -> None:
    """Tasarım §4.4.2 ¹ ve K2: müdürün olağanüstü genel kurul çağrısı (md. 9/6) yalnız müdürün hesabından
    yazılır (`OLAGANUSTU_GENEL_KURUL_CAGRISI_MUDUR`); öteki her rol `RolYetkisiz` alır, hiçbir şey
    yazılmaz (program yöneticisi taslak da hazırlamaz, M-11). Müdür genel kurulun öteki işlerinde okurdur
    (ilan). Sahiplik: müdürün çağrısındaki toplantı zamanı, yeri ve gündem sırası ilandan önce yalnız
    müdürce düzenlenir, başka rolce değiştirilmez (tasarım §4.4.2 "müdür yalnız kendi yazısını
    düzenler"); yönetim kurulunun çağırdığı genel kurulda aynı işler sekreterindir."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    once = AuditTrail.objects.exclude(action="HESAP").count()
    for rol in set(ROLLER) - {"mudur"}:
        with o.rol_olarak(AccountRole(rol)), pytest.raises(RolYetkisiz):
            _olaganustu_mudur_cagrisi(kurul)
    # Rolün oturumu için açılan hesabın `HESAP` satırı dışında iz yazılmaz.
    assert AuditTrail.objects.exclude(action="HESAP").count() == once
    with o.rol_olarak(AccountRole.MUDUR):
        sonuc = _olaganustu_mudur_cagrisi(kurul)
        with pytest.raises(RolYetkisiz):
            genel_kurul.ilan_et(kurul, kanallar=gko.kanallar())
    cagrilan = sonuc.kurul
    assert cagrilan.status == AssemblyStatus.CAGRILDI
    assert genel_kurul.cagri_sahibi(cagrilan) == "mudur"
    _yalniz_sahip_duzenler(cagrilan, AccountRole.MUDUR)
    # Yönetim kurulunun çağrısında sıra ve tarih ilandan önce sekreterce değişir (sahip yok).
    yk_kurulu = gko.olaganustu_cagir(gko.planla(kind=AssemblyKind.OLAGANUSTU))
    assert genel_kurul.cagri_sahibi(yk_kurulu) is None
    yk_sira = list(
        AgendaItem.objects.filter(assembly=yk_kurulu)
        .order_by("-order")
        .values_list("pk", flat=True)
    )
    with o.rol_olarak(AccountRole.SEKRETER):
        genel_kurul.gundem_sirasini_degistir(yk_kurulu, sira=yk_sira)


def _gundem_sirasi(kurul: GeneralAssembly) -> list[int]:
    return list(
        AgendaItem.objects.filter(assembly=kurul).order_by("order").values_list("pk", flat=True)
    )


def _yalniz_sahip_duzenler(kurul: GeneralAssembly, sahip: AccountRole) -> None:
    """Çağrılmış genel kurulda yazının sahibi toplantı zamanını, yerini ve gündem sırasını düzenler;
    öteki her rol `RolYetkisiz` alır, ret hiçbir şey yazmaz (modül başlığı "Sahiplik")."""
    eski_sira = _gundem_sirasi(kurul)
    yeni_sira = list(reversed(eski_sira))
    eski_zaman = GeneralAssembly.objects.get(pk=kurul.pk).first_meeting_at
    yeni_zaman = gko.an(gko.BIRINCI_GUN, saat=11)
    once = AuditTrail.objects.exclude(action="HESAP").count()
    for rol in sorted(set(ROLLER) - {sahip.value}):
        with o.rol_olarak(AccountRole(rol)):
            with pytest.raises(RolYetkisiz):
                genel_kurul.gundem_sirasini_degistir(kurul, sira=yeni_sira)
            with pytest.raises(RolYetkisiz):
                genel_kurul.toplanti_bilgisini_degistir(kurul, first_meeting_at=yeni_zaman)
    assert AuditTrail.objects.exclude(action="HESAP").count() == once
    assert GeneralAssembly.objects.get(pk=kurul.pk).first_meeting_at == eski_zaman
    assert _gundem_sirasi(kurul) == eski_sira
    with o.rol_olarak(sahip):
        genel_kurul.toplanti_bilgisini_degistir(
            kurul, first_meeting_at=yeni_zaman, venue="Uydurma konferans salonu"
        )
        genel_kurul.gundem_sirasini_degistir(kurul, sira=yeni_sira)
    guncel = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (guncel.status, guncel.first_meeting_at, guncel.venue) == (
        AssemblyStatus.CAGRILDI,
        yeni_zaman,
        "Uydurma konferans salonu",
    )
    assert _gundem_sirasi(kurul) == yeni_sira


@pytest.mark.django_db
@pytest.mark.parametrize("sahip", [AccountRole.MUDUR, AccountRole.DENETLEME_KURULU])
def test_sahiplik_13_8_mudur_kolu_ve_denetleme_kurulu_cagrisi(sahip: AccountRole) -> None:
    """Sahiplik (modül başlığı; tasarım §4.4.2): md. 13/8'in "başkan ya da müdür" çağrısını müdür
    yazdıysa yazı müdüründür (`called_by_role`), Denetleme Kurulunun md. 14/5 çağrısı Denetleme
    Kurulunundur. İlandan önce zaman, yer ve gündem sırasını yalnız sahip düzenler; sekreter ve program
    yöneticisi dahil başka rol değiştiremez."""
    gko.acik_donem()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    if sahip is AccountRole.MUDUR:
        with o.rol_olarak(AccountRole.MUDUR):
            genel_kurul.cagir(
                kurul,
                called_by=AssemblyCaller.BASKAN_VEYA_MUDUR_13_8,
                call_reason=gko.OLAGANUSTU_NEDEN,
                gundem=gko.OLAGANUSTU_GUNDEM,
            )
    else:
        with o.rol_olarak(AccountRole.DENETLEME_KURULU):
            rapor = denetim.denetim_raporu_yaz(
                kind="ARA", report_date=gko.ILAN_GUNU, md6_violation_found=True
            )
            genel_kurul.cagir(
                kurul,
                called_by=AssemblyCaller.DENETLEME_KURULU,
                call_reason=gko.OLAGANUSTU_NEDEN,
                gundem=gko.OLAGANUSTU_GUNDEM,
                call_audit_report=rapor,
            )
    cagrilan = GeneralAssembly.objects.get(pk=kurul.pk)
    assert (cagrilan.called_by_role, genel_kurul.cagri_sahibi(cagrilan)) == (sahip, sahip.value)
    _yalniz_sahip_duzenler(cagrilan, sahip)


@pytest.mark.django_db
def test_dipnot_yedi_gercek_serviste_mudur_yazmaz_yazisi_programca_islenir() -> None:
    """Tasarım §4.4.2 ⁷ ve M10: gelen-giden evrakı program yöneticisi ve yönetim kurulu rolleri yazar
    (`EVRAK_KAYDI`); müdür ve Denetleme Kurulu `RolYetkisiz` alır, hiçbir şey yazılmaz. Müdürün kendi
    yazısı evrak defterine program tarafından giden evrak olarak işlenir: müdürün çağrısının yan
    etkisidir, kaydın kendi iz satırı müdürün hesabıyladır (F0-F1 planı F1b-2 "ayrı izi"). Müdür kaydın
    ekini de yazamaz."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    once = AuditTrail.objects.exclude(action="HESAP").count()
    for rol in (AccountRole.MUDUR, AccountRole.DENETLEME_KURULU):
        with o.rol_olarak(rol):
            with pytest.raises(RolYetkisiz):
                gelen_giden_evrak.evrak_defteri_olustur()
            with pytest.raises(RolYetkisiz):
                gelen_giden_evrak.evrak_kaydet(
                    direction=DocumentDirection.GELEN, tarih=gko.ILAN_GUNU
                )
            # Yazı işleme yolu yalnız müdürün yazısının içinden: yazar müdür değilse ret.
            if rol is AccountRole.DENETLEME_KURULU:
                with pytest.raises(RolYetkisiz):
                    gelen_giden_evrak.mudur_yazisini_isle(
                        donem=OabTerm.objects.get(status=TermStatus.ACIK), subject="Uydurma konu"
                    )
    assert AuditTrail.objects.exclude(action="HESAP").count() == once
    gecenler: set[str] = set()
    for yazan in ("yonetici", *sorted(YK)):
        with o.rol_olarak(AccountRole(yazan)):
            # Müdürün yazısı bugünün tarihiyle işlenir: numaralar aynı yılda sıralansın.
            gelen_giden_evrak.evrak_kaydet(
                direction=DocumentDirection.GELEN, tarih=timezone.localdate()
            )
            gecenler.add(yazan)
    assert gecenler == {"yonetici", *YK}

    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.MUDUR) as mudur:
        sonuc = _olaganustu_mudur_cagrisi(kurul)
        assert sonuc.kurul.call_document_id is not None
        yazi = DocumentRecord.objects.get(pk=sonuc.kurul.call_document_id)
        with pytest.raises(RolYetkisiz):
            gelen_giden_evrak.evrak_kaydina_ek_ekle(yazi, b"%PDF-1.7 uydurma", dosya_adi="yazi.pdf")
    assert (yazi.direction, yazi.record_no) == (DocumentDirection.GIDEN, 1 + len(gecenler))
    izi = AuditTrail.objects.get(model="oab.DocumentRecord", object_id=str(yazi.pk))
    assert (izi.action, str(izi.account_id), izi.role) == ("OLUSTUR", str(mudur.id), "mudur")
    # Program yöneticisi kayda taranmış nüshayı ekler (M10).
    ek = gelen_giden_evrak.evrak_kaydina_ek_ekle(
        yazi, b"%PDF-1.7 uydurma", dosya_adi="mudur-yazisi.pdf"
    )
    assert list(yazi.ekler()) == [ek]


# ============================================================ ¹⁰ gerçek serviste (F2 8. adım)


@pytest.mark.django_db
def test_dipnot_on_gercek_serviste_adli_cikti_yalniz_program_yoneticisi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tasarım §4.4.2 ¹⁰ (R9; plan F2 §6.2, §7 U14-U15): veli adı taşıyan çıktı — adlı E07 teslim
    çizelgesi ve adlı E08 katılım cetveli — yalnız program yöneticisinin hesabından verilir
    (`Eylem.KISISEL_VERI_CIKTISI`; `genel_kurul_evraki.adli_uret_ve_ver`). Öteki her rol, kişisiz
    kipi üretebilen sekreter dahil, `RolYetkisiz` alır; ne evrak kaydı ne iz satırı ne erişim günlüğü
    satırı yazılır. İçerik 9. adımda; burada deneme kurucusuyla (`genel_kurul_evraki_ortak`)."""
    from apps.oab.models import DocumentFormat, GeneratedDocument
    from apps.oab.services import genel_kurul_evraki
    from apps.oab.tests import genel_kurul_evraki_ortak
    from apps.okul.models import AccessLog

    genel_kurul_evraki_ortak.kuruculari_kur(monkeypatch)
    kurul = gko.ilanli_olagan()
    once = (AuditTrail.objects.exclude(action="HESAP").count(), AccessLog.objects.count())
    for rol in sorted(set(ROLLER) - {"yonetici"}):
        with o.rol_olarak(AccountRole(rol)):
            for kod in genel_kurul_evraki.ADLI_KODLAR:
                with pytest.raises(RolYetkisiz):
                    genel_kurul_evraki.adli_uret_ve_ver(kod, kurul, bicim=DocumentFormat.PDF)
    assert not GeneratedDocument.objects.exists()
    assert (AuditTrail.objects.exclude(action="HESAP").count(), AccessLog.objects.count()) == once

    with o.rol_olarak(AccountRole.YONETICI):
        for kod in genel_kurul_evraki.ADLI_KODLAR:
            cikti = genel_kurul_evraki.adli_uret_ve_ver(kod, kurul, bicim=DocumentFormat.PDF)
            assert cikti.kayit.personal_list and cikti.icerik.startswith(b"%PDF")
    assert AccessLog.objects.count() == once[1] + len(genel_kurul_evraki.ADLI_KODLAR)
    assert {a.role for a in AccessLog.objects.all()} == {"yonetici"}
