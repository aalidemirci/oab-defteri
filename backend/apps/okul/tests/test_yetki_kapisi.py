"""Servis katmanının yetki kapısı (tasarım §4.4.2 "iki katman", dipnotlar 1-10; plan F1b-2).

`yetki(rol, eylem, kayıt)`: kapanmış dönem, maskesiz okuma, kişisel veri içeren çıktı,
rol-özel işaretler ve kayıt sahipliği tek kapıdan geçer; ret `RolYetkisiz` → 403
`rol_yetkisiz`. Dipnotların servisleri sonraki fazlardadır (müdür yazıları F2/F4, mali kayıtlar
F3, DK modülü F4): F1b'de her dipnot KAPININ KENDİSİYLE sahte kayıtla sınanır
(`test_rol_matrisi_dipnot_servis_testi`; plan F1b-2 kullanıcı kararı). Bağlı servisler
(hesap yönetimi, kurtarma anahtarı, boşta süre, yedek indirme, uygulama içi geri yükleme)
ayrıca gerçek çağrıyla sınanır: rol kapısının ardından servis de reddeder (derin savunma). ⁵
gerçek serviste de sınanır: Denetleme Kurulunun geri yükleme kartındaki "Gördüm"ü
(`test_dipnot_bes_gercek_serviste_yalniz_denetleme_kurulu`; plan F1b-2 kullanıcı kararı).
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass

import pytest
from rest_framework import serializers

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
    if dipnot in (4, 5, 6):
        # Kayıt sahipliği rol düzeyindedir: sahibi olan rolün hesapları düzenler.
        eylem = next(e for e, k in EYLEM_KURALLARI.items() if k.dipnot == dipnot and k.sahiplik)
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
    }
    for eylem in dipnotsuz:
        assert _gecen_roller(eylem) == {"yonetici"}, eylem
    # Dipnotlu eylemlerden bugün yalnız DK'nin "Gördüm"ü (⁵) servise bağlıdır (F1b-2 c3).
    assert set(BAGLANMAMIS_EYLEMLER) == set(Eylem) - dipnotsuz - {Eylem.GERI_YUKLEME_GORDUM}


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
        encrypted_backup.create_encrypted_backup()
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
