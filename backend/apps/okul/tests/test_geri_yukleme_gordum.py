"""Geri yükleme kartının "Gördüm"ü (plan F1b-2 "Gördüm."; tasarım §4.4.4, §4.4.2 M8 ⁵).

`POST security/integrity/restore-seen/` `{seq}`, yalnız Denetleme Kurulu:

* `ISARET` satırı (model denetim izinin kendisi, kimlik geri yüklemenin `seq`'i, yazar o üye);
  kart HERKES İÇİN kalkar — program yöneticisinde de öteki üyelerde de (kullanıcı kararı
  02.11.2026: bir üye yeter); kimin gördüğü izde kalır.
* Kart yalnız doğrulanan bir `ISARET` satırıyla ve yalnız doğrulanan son `GERI_YUKLEME` satırına
  bağlı olarak kalkar: mühürsüz, başka rolün ya da geri yüklemeden önce yazılmış `ISARET` kaldırmaz.
* Aynı geri yüklemeye ikinci "Gördüm" satır yazmaz; eski ya da olmayan `seq` 409.
* Açık DK hesabı yoksa kart program yöneticisinde kalır (program yöneticisi kaldıramaz).
* C-2: reddedilen işlemin `BUTUNLUK` satırı yanıttan sonra kalır (istek boyu işlem yok).

Adlar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from django.db import transaction
from rest_framework.test import APIClient

from apps.okul import denetim_izi, iz_dogrulama, rol_izinleri
from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import SISTEM, Yazar, yazar_olarak
from apps.okul.services import app_password, hesaplar
from apps.okul.tests.hesap_ortak import geri_sarilmis, hesap_ac, muhurle
from apps.okul.tests.iz_ortak import sahte_satir
from apps.okul.views_oturum import GORDUM_SIRASI_EKSIK, GORDUM_SIRASI_GECERSIZ
from conftest import TEST_HESAP_ID, oturumu_ac_test
from shared.exceptions import ROL_YETKISIZ_MESAJI, RolYetkisiz

pytestmark = pytest.mark.django_db

YOL = "/api/v1/security/integrity/restore-seen/"
KARTLAR = "/api/v1/security/integrity/audit/"
DK = AccountRole.DENETLEME_KURULU.value
#: Uydurma kenara alınan veritabanı adları (programın biçimi).
ONCEKI_1 = "db-onceki-2026-11-01-091000.sqlite3"
ONCEKI_2 = "db-onceki-2026-11-02-101500.sqlite3"


def _dk(ad: str = "Uydurma Denetçi", tanitici: str | None = None) -> Account:
    """Açık (mühürlü, izli) uydurma Denetleme Kurulu hesabı."""
    return muhurle(hesap_ac(DK, ad=ad, tanitici=tanitici), status=AccountStatus.ACIK)


def _geri_yukleme(onceki: str = ONCEKI_1) -> AuditTrail:
    """Programın yazdığı (iz anahtarıyla mühürlü) bir `GERI_YUKLEME` satırı."""
    with transaction.atomic():
        return denetim_izi.olay(
            AuditAction.GERI_YUKLEME, model=denetim_izi.GERI_YUKLEME_KAYDI, object_id=onceki
        )


def _oturum(hesap: Account) -> None:
    oturumu_ac_test(str(hesap.id), tanitici=hesap.login_name, rol=str(hesap.role))


def _yonetici_oturumu() -> None:
    oturumu_ac_test()


def _kart(hesap_id: object = TEST_HESAP_ID) -> dict[str, Any] | None:
    kart: dict[str, Any] | None = iz_dogrulama.denetim_kartlari(str(hesap_id))["geri_yukleme"]
    return kart


def _isaretler() -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(action=AuditAction.ISARET).order_by("seq"))


def _son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else int(bas[0])


def _gordum(seq: object) -> Any:
    return APIClient().post(YOL, {"seq": seq}, format="json")


# ============================================================ olağan akış


def test_bir_dk_uyesinin_gordumu_karti_herkes_icin_kaldirir() -> None:
    """Kullanıcı kararı 02.11.2026: bir DK üyesi yeter; kart program yöneticisinde ve öteki
    üyede de kalkar; kimin gördüğü `ISARET` satırında kalır (model denetim izi, kimlik `seq`)."""
    birinci = _dk("Uydurma Birinci Denetçi", "dk-1")
    ikinci = _dk("Uydurma İkinci Denetçi", "dk-2")
    geri = _geri_yukleme()
    kart = _kart()
    assert kart is not None and kart["seq"] == geri.seq
    assert APIClient().get(KARTLAR).json()["geri_yukleme"]["seq"] == geri.seq

    _oturum(birinci)
    yanit = _gordum(geri.seq)

    assert yanit.status_code == 200, yanit.content
    govde = yanit.json()
    assert set(govde) == {"butunluk", "geri_yukleme", "muhru_tutmayan", "okunamayan"}
    assert govde["geri_yukleme"] is None
    (isaret,) = _isaretler()
    assert (isaret.model, isaret.object_id) == ("okul.AuditTrail", str(geri.seq))
    assert (str(isaret.account_id), isaret.role, isaret.actor) == (str(birinci.id), DK, "HESAP")
    assert (isaret.changed_fields, isaret.values, isaret.record_mac) == ([], {}, "")
    assert isaret.key_mode == "ACIK" and isaret.seq > geri.seq
    for hesap_id in (TEST_HESAP_ID, birinci.id, ikinci.id):
        assert _kart(hesap_id) is None, hesap_id
    _yonetici_oturumu()
    assert APIClient().get(KARTLAR).json()["geri_yukleme"] is None
    assert denetim_izi.zinciri_dogrula() == []


def test_ayni_geri_yuklemeye_ikinci_gordum_satir_yazmaz() -> None:
    birinci = _dk("Uydurma Birinci Denetçi", "dk-1")
    ikinci = _dk("Uydurma İkinci Denetçi", "dk-2")
    geri = _geri_yukleme()
    _oturum(birinci)
    assert _gordum(geri.seq).status_code == 200
    son = _son_seq()

    assert _gordum(geri.seq).status_code == 200
    _oturum(ikinci)
    yanit = _gordum(geri.seq)

    assert yanit.status_code == 200 and yanit.json()["geri_yukleme"] is None
    assert _son_seq() == son
    assert len(_isaretler()) == 1


def test_yeni_geri_yukleme_karti_yeniden_acar_eski_gordum_kaldirmaz() -> None:
    dk = _dk()
    ilk = _geri_yukleme(ONCEKI_1)
    _oturum(dk)
    assert _gordum(ilk.seq).status_code == 200
    assert _kart() is None

    yeni = _geri_yukleme(ONCEKI_2)

    kart = _kart()
    assert kart is not None and kart["seq"] == yeni.seq
    assert _gordum(yeni.seq).status_code == 200
    assert _kart() is None
    assert [s.object_id for s in _isaretler()] == [str(ilk.seq), str(yeni.seq)]


# ============================================================ eski ya da olmayan seq


@pytest.mark.parametrize("hal", ["eski", "olmayan", "baska_tur", "kart_yok"])
def test_eski_ya_da_olmayan_seq_409_ve_satir_yazmaz(hal: str) -> None:
    """Plan F1b-2: "Eski `seq` 409 alır." Olmayan kayıt, geri yükleme olmayan satır ve hiç
    geri yükleme yokken de aynı: kartın gösterdiği son geri yükleme değil."""
    dk = _dk()
    if hal == "kart_yok":
        seq = _son_seq()
    else:
        ilk = _geri_yukleme(ONCEKI_1)
        son = _geri_yukleme(ONCEKI_2)
        seq = {"eski": ilk.seq, "olmayan": son.seq + 50, "baska_tur": dk_satiri(dk)}[hal]
    _oturum(dk)
    once = _son_seq()

    yanit = _gordum(seq)

    assert yanit.status_code == 409, yanit.content
    assert yanit.json() == {
        "code": "geri_yukleme_guncel_degil",
        "message": hesaplar.RESTORE_CARD_STALE_MESSAGE,
        "fields": {},
    }
    assert _son_seq() == once
    assert _isaretler() == []


def dk_satiri(dk: Account) -> int:
    """DK hesabının açılışının `HESAP` satırı (geri yükleme olmayan, doğrulanan bir satır)."""
    satir = AuditTrail.objects.filter(action=AuditAction.HESAP, object_id=str(dk.id)).first()
    assert satir is not None
    return int(satir.seq)


@pytest.mark.parametrize(
    ("govde", "ileti"),
    [
        ({}, GORDUM_SIRASI_EKSIK),
        ({"seq": None}, GORDUM_SIRASI_EKSIK),
        ({"seq": "abc"}, GORDUM_SIRASI_GECERSIZ),
        ({"seq": 0}, GORDUM_SIRASI_GECERSIZ),
        ({"seq": 2**63}, GORDUM_SIRASI_GECERSIZ),
    ],
)
def test_bicimsiz_seq_400(govde: dict[str, Any], ileti: str) -> None:
    dk = _dk()
    _geri_yukleme()
    _oturum(dk)

    yanit = APIClient().post(YOL, govde, format="json")

    assert yanit.status_code == 400, yanit.content
    # İleti alanın altındadır (`fields`); bağlamsız "eksik" iletisi genel cümlede kalmaz
    # (`shared.exceptions._CONTEXT_FREE_CODES`), biçim iletisi `message`'a da çıkar.
    assert yanit.json()["fields"]["seq"] == [ileti]
    if ileti == GORDUM_SIRASI_GECERSIZ:
        assert yanit.json()["message"] == ileti
    assert _isaretler() == []


# ============================================================ yalnız doğrulanan satırlar


def test_dogrulanmayan_isaret_karti_kaldirmaz() -> None:
    """Kart yalnız doğrulanan `ISARET` satırıyla kalkar: sırrı olmayanın (mühürsüz anahtar)
    eklediği DK adına `ISARET`, iz anahtarıyla yazılmış ama yazarı DK olmayan `ISARET` ve geri
    yüklemeden ÖNCE yazılmış (kimliği sonraki sırayı anan) `ISARET` kartı kaldırmaz."""
    dk = _dk()
    # Geri yüklemeden önce, gelecek geri yükleme satırının sırasını anan DK işareti.
    with yazar_olarak(Yazar(hesap_id=str(dk.id), rol=DK)), transaction.atomic():
        denetim_izi.olay(
            AuditAction.ISARET, model=iz_dogrulama.IZ_SATIRI_MODELI, object_id=str(_son_seq() + 2)
        )
    geri = _geri_yukleme()
    assert geri.seq == _son_seq()
    # Program yöneticisinin adına (iz anahtarıyla) işaret: yazarı DK değil.
    with transaction.atomic():
        denetim_izi.olay(
            AuditAction.ISARET, model=iz_dogrulama.IZ_SATIRI_MODELI, object_id=str(geri.seq)
        )
    # Mühürsüz anahtarla DK adına işaret.
    sahte_satir(
        action="ISARET",
        actor="HESAP",
        account=str(dk.id),
        role=DK,
        model=iz_dogrulama.IZ_SATIRI_MODELI,
        object_id=str(geri.seq),
        key_mode="ACIK",
        key_ref="1",
    )

    kart = _kart()

    assert kart is not None and kart["seq"] == geri.seq


def test_gordum_dogrulanmayan_geri_yukleme_satirina_baglanmaz() -> None:
    """Sırrı olmayanın eklediği sahte `GERI_YUKLEME` kartın konusu olamaz: onun sırası 409 alır,
    gerçek son geri yükleme kartta kalır ve "Gördüm"le kalkar."""
    dk = _dk()
    gercek = _geri_yukleme()
    sahte = sahte_satir(
        action="GERI_YUKLEME",
        actor="HESAP",
        account=TEST_HESAP_ID,
        role="yonetici",
        model=denetim_izi.GERI_YUKLEME_KAYDI,
        object_id=ONCEKI_2,
        key_mode="ACIK",
        key_ref="1",
    )
    kart = _kart()
    assert kart is not None and kart["seq"] == gercek.seq
    _oturum(dk)

    assert _gordum(sahte.seq).status_code == 409
    assert _gordum(gercek.seq).status_code == 200
    assert _kart() is None


# ============================================================ rol


def test_dk_hesabi_yoksa_kart_program_yoneticisinde_kalir() -> None:
    """Plan F1b-2: "Açık DK hesabı yoksa kart program yöneticisinde kalır": program yöneticisi
    kartı görür, kaldıramaz (rol kapısı)."""
    geri = _geri_yukleme()

    yanit = _gordum(geri.seq)

    assert yanit.status_code == 403
    assert yanit.json() == {"code": "rol_yetkisiz", "message": ROL_YETKISIZ_MESAJI, "fields": {}}
    kart = _kart()
    assert kart is not None and kart["seq"] == geri.seq
    assert _isaretler() == []


@pytest.mark.parametrize("rol", [r for r in rol_izinleri.ROLLER if r != DK])
def test_dk_disindaki_her_rol_403(rol: str) -> None:
    """Uç katmanı: yönetim kurulu rolleri DK modülüne yazamaz (tasarım §4.4.2 ⁵), müdür ve program
    yöneticisi de."""
    geri = _geri_yukleme()
    oturumu_ac_test("0b4c2d1e-7a3f-4e5d-9c8b-1a2b3c4d5e6f", tanitici=rol, rol=rol)

    yanit = _gordum(geri.seq)

    assert yanit.status_code == 403 and yanit.json()["code"] == "rol_yetkisiz"
    assert _isaretler() == []


@pytest.mark.parametrize("kim", [None, SISTEM], ids=["yazarsiz", "sistem"])
def test_servis_yazarsiz_ve_sistem_yazariyla_calismaz(kim: Yazar | None) -> None:
    geri = _geri_yukleme()
    with yazar_olarak(kim), pytest.raises(RolYetkisiz):
        hesaplar.acknowledge_restore(by_hesap_id=TEST_HESAP_ID, seq=geri.seq)
    assert _isaretler() == []


def test_servis_rolu_hesabi_denetlemeden_once_sorar() -> None:
    """Derin savunma ve sıra: rolü açık olmayan yazar hesap denetimine (satırın izi) hiç
    ulaşmaz — kaydı geri sarılmış bir muhasibin denemesi `BUTUNLUK` satırı da yazmaz."""
    muhasip = geri_sarilmis(muhurle(hesap_ac(AccountRole.MUHASIP), status=AccountStatus.ACIK))
    geri = _geri_yukleme()
    son = _son_seq()

    with (
        yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol="muhasip")),
        pytest.raises(RolYetkisiz),
    ):
        hesaplar.acknowledge_restore(by_hesap_id=str(muhasip.id), seq=geri.seq)

    assert _son_seq() == son


# ============================================================ C-2: ret satırı kalır


@pytest.mark.django_db(transaction=True)
def test_reddedilen_gordum_butunluk_satirini_birakir() -> None:
    """Orkestratör maddesi C-2 (otomatik commit kipinde, üretimdeki gibi): DK üyesinin satırı eski
    kopyaya geri sarılmıştır; uç 409 `hesap_muhru_tutmadi` döner, reddin `BUTUNLUK` satırı (alan
    `kayit_mac`) yanıttan SONRA da kalır, `ISARET` yazılmaz, kart kalır."""
    dk = geri_sarilmis(_dk())
    geri = _geri_yukleme()
    _oturum(dk)
    son = _son_seq()

    yanit = _gordum(geri.seq)

    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "hesap_muhru_tutmadi"
    satirlar = list(AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BUTUNLUK))
    assert [(s.object_id, s.changed_fields) for s in satirlar] == [
        (str(dk.id), [app_password.KAYIT_MAC_ALANI])
    ]
    assert _isaretler() == []
    assert _kart() is not None


# ============================================================ sözlük


def _sozluk() -> str:
    """`docs/sozluk.md` (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / "docs" / "sozluk.md"
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail("docs/sozluk.md bulunamadı.")


def test_gordum_iletileri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Geri yükleme kartının “Gördüm”ü
    (F1b)")."""
    sozluk = _sozluk()
    for ileti in (
        hesaplar.RESTORE_CARD_STALE_MESSAGE,
        GORDUM_SIRASI_EKSIK,
        GORDUM_SIRASI_GECERSIZ,
        "Gördüm",
    ):
        assert f'**"{ileti}"**' in sozluk, ileti
