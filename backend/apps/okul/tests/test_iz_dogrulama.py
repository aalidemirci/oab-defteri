"""Kilit açılışında kendiliğinden doğrulama, geri yükleme notu ve bütünlük kartları (§4.6.3).

Tasarım §4.6.3 "Kilit açılışında kendiliğinden doğrulama": (1) çapa — mühür ve çapanın satırı,
(2) çapadan sonraki kilitli satırlar ve adım sayısı, (3) son 200 satırın zinciri. Bulgu varsa
TEK `BUTUNLUK` satırı (`SISTEM`) ve kart; giriş ENGELLENMEZ. Geri yükleme notu çapayı
açıklıyorsa çapa uyarısı yerine, açıklamıyorsa uyarıyla birlikte `GERI_YUKLEME` satırı
(oturumu açan hesabın), bekleyen sistem olayları (kendi anlarıyla), iki depo karşılaştırması;
çapa yenilenir. Tasarım §10.6'nın adlı testi:
`test_capa_ve_kuyruk_kesme_uyarisi`.

Varsayılan ortam kök `conftest.py`'dedir (oturum program yöneticisiyle açık, zincir boş).
Program DIŞINDAN yapılan değişiklik tetikleyiciler test işleminde düşürülerek taklit edilir
(test sonunda geri alınır). Hesap adları ve tanıtıcılar UYDURMADIR.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import denetim_izi, iz_dogrulama, iz_durumu, masaustu_kanca
from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, AuditTrail
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, geri_yukleme_notu, hesaplar
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    YENI_PAROLA,
    durum,
    durum_yaz,
    ham_guncelle,
    hesap_ac,
    muhurle,
    sarmal_kimlikleri,
)
from apps.okul.tests.iz_ortak import sahte_satir
from conftest import (
    TEST_HESAP_ID,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
    TEST_TANITICI,
    oturumu_ac_test,
)
from shared import kanonik

pytestmark = pytest.mark.django_db


def _gun(an: Any) -> str | None:
    """Hesabın Europe/Istanbul günü, yyyy-aa-gg (kartın `acilis`/`kapanis` biçimi; F-3)."""
    return None if an is None else f"{timezone.localtime(an):%Y-%m-%d}"


def yonetici_ozeti() -> dict[str, Any]:
    """Kartlardaki program yöneticisi hesabının kişisiz özeti (ad-soyad yok; açılış günü ve açık
    hesapta boş kapanış — orkestratör maddesi F-3)."""
    hesap = Account.objects.get(pk=TEST_HESAP_ID)
    return {
        "id": TEST_HESAP_ID,
        "tanitici": TEST_TANITICI,
        "rol_etiketi": "Program yöneticisi",
        "acilis": _gun(hesap.opened_at),
        "kapanis": None,
    }


GUNLUK = "gunluk-2026-11-01.odbak"
ONCEKI = "db-onceki-2026-11-01-101530.sqlite3"
SAHIPSIZ = "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f"
TETIKLEYICILER = ("okul_audittrail_no_delete", "okul_audittrail_no_update")


def satirlar(**suz: Any) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(**suz).order_by("seq"))


def son_satir() -> AuditTrail:
    satir: AuditTrail | None = AuditTrail.objects.order_by("-seq").first()
    assert satir is not None
    return satir


def butunluk() -> list[AuditTrail]:
    return satirlar(action="BUTUNLUK", model=denetim_izi.IZ_DOGRULAMASI)


def deger(satir: AuditTrail, ad: str) -> Any:
    return satir.values[ad][1]


def acik_olay() -> AuditTrail:
    with transaction.atomic():
        # `KILIT` değil: açık kipteki `KILIT` çapanın satırıdır; çapadan sonra kalırsa çapa
        # bayattır (`iz_dogrulama` "capa_bayat"). Herhangi bir hesap olayı yeter.
        return denetim_izi.olay(AuditAction.HESAP, model="okul.Account", object_id=TEST_HESAP_ID)


def kilitle() -> AuditTrail:
    """Bir satır + elle Kilitle (`KILIT` satırı ve çapa); KILIT satırını döndürür."""
    acik_olay()
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    return son_satir()


def ac() -> None:
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def tetikleyicisiz(sql: str, params: list[Any]) -> None:
    """Program DIŞINDAN yazım taklidi: tetikleyiciler bu test işleminde düşürülür."""
    with connection.cursor() as cursor:
        for ad in TETIKLEYICILER:
            cursor.execute(f"DROP TRIGGER IF EXISTS {ad}")
        cursor.execute(sql, params)


def not_kaydi(**degistir: Any) -> dict[str, Any]:
    alanlar: dict[str, Any] = {
        "yedek": GUNLUK,
        "onceki_dosya": ONCEKI,
        "onceki_sha256": "ab" * 32,
        "onceki_zincir_basi": {"seq": 42, "mac": "cd" * 32},
        "yol_bilgisi": {"tur": "hesap", "hesap": TEST_HESAP_ID, "tanitici": TEST_TANITICI},
    }
    alanlar.update(degistir)
    return geri_yukleme_notu.geri_yukleme_kaydi(**alanlar)


def notu_yaz(**degistir: Any) -> None:
    geri_yukleme_notu.geri_yukleme_ekle(iz_durumu.dizin(), not_kaydi(**degistir))


def pano(hesap_id: str | None) -> dict[str, Any]:
    """Üç bütünlük ucunun servis yanıtı tek sözlükte (kendi, denetim, iki depo kartları; plan
    F1b-2'de bölünmeden önceki biçim): `okunamayan` listeleri birleşir."""
    kendi = iz_dogrulama.kendi_kartlari(hesap_id)
    denetim = iz_dogrulama.denetim_kartlari(hesap_id)
    iki_depo = iz_dogrulama.iki_depo_karti()
    okunamayan = [*kendi["okunamayan"], *denetim["okunamayan"], *iki_depo["okunamayan"]]
    return {**kendi, **denetim, **iki_depo, "okunamayan": okunamayan}


# ============================================================ tutarlı iz


def test_tutarli_izde_kilit_acilisi_bulgu_satiri_yazmaz_capayi_yenilemez() -> None:
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    once = iz_durumu.oku()

    ac()

    assert not satirlar(action="BUTUNLUK")
    assert son_satir().action == "GIRIS"
    assert iz_durumu.oku() == once  # bulgu yoksa çapa kilitlenmede yenilenir


def test_oturum_acikken_cokme_sonrasi_eski_capa_ve_tohum_tutarlidir() -> None:
    """Oturum açıkken süreç ölürse çapa yazılmaz: eski çapanın tohumu sürer, açık satırlar
    çapadan sonra kalır. Bu meşru hâldir, bulgu değildir."""
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    ac()
    acik_olay()
    app_password.lock()  # çökme: KILIT ve çapa yok
    masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-02.odbak"])  # ertesi açılış
    assert iz_durumu.oku().adim == 2

    ac()

    assert not satirlar(action="BUTUNLUK")


# ============================================================ çapa ve kuyruk


@pytest.mark.parametrize("senaryo", ["kuyruk_kesildi", "dunku_kopya", "geri_yukleme_notu"])
def test_capa_ve_kuyruk_kesme_uyarisi(senaryo: str) -> None:
    """Tasarım §10.6 (GA-9): son satırlar silinirse ya da veritabanı dünkü kopyayla
    değiştirilirse ilk kilit açılışı "denetim izi kuyruğu kesilmiş ya da veritabanı geri
    sarılmış" uyarısı verir (`kuyruk_kesik`); geri yükleme notu bunu açıklıyorsa uyarı yerine
    `GERI_YUKLEME` satırı düşer. İkisinde de çapa yenilenir, uyarı yinelenmez."""
    for _ in range(3):
        acik_olay()
    if senaryo == "dunku_kopya":
        dun = kilitle()  # dün akşamki kilit: o zamanın çapası
        oturumu_ac_test()
        acik_olay()
        capa = kilitle()  # bugünkü çapa
        # Dünkü kopya: dünkü çapaya dek aynı satırlar, sonra kopyanın kendi (başka) satırları.
        tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq > %s", [dun.seq])
        oturumu_ac_test()
        while son_satir().seq < capa.seq:
            acik_olay()
        app_password.lock()
        assert son_satir().seq == capa.seq and son_satir().mac != capa.mac
    else:
        capa = kilitle()
        tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa.seq - 1])
    if senaryo == "geri_yukleme_notu":
        notu_yaz()

    ac()

    if senaryo == "geri_yukleme_notu":
        assert not satirlar(action="BUTUNLUK")
        (geri,) = satirlar(action="GERI_YUKLEME")
        assert (geri.actor, str(geri.account_id)) == ("HESAP", TEST_HESAP_ID)
        assert not geri_yukleme_notu.var_mi(iz_durumu.dizin())
    else:
        (satir,) = butunluk()
        assert (satir.actor, satir.account_id, satir.role) == ("SISTEM", None, "")
        assert deger(satir, "bulgular") == ["kuyruk_kesik"]
        assert deger(satir, "duzey") == "uyari"
        assert deger(satir, "bulgu_satirlari") == [capa.seq]
        assert satir.key_mode == "ACIK" and satir.record_mac == ""
    # Çapa yeni zincir başına (girişe) yenilendi; sonraki kilit-açılış bulgu vermez.
    assert iz_durumu.oku().capa_seq == son_satir().seq == satirlar(action="GIRIS")[-1].seq
    sayi = AuditTrail.objects.filter(action="BUTUNLUK").count()
    kilitle()
    ac()
    assert AuditTrail.objects.filter(action="BUTUNLUK").count() == sayi


@pytest.mark.parametrize(
    "not_durumu",
    ["tutarli", "capa_notun_ilerisinde", "zincir_yoktu_dedi", "zincir_basi_yok", "okunamayan"],
)
def test_geri_yukleme_notu_capayi_aciklamiyorsa_uyari_da_yazilir(not_durumu: str) -> None:
    """Tasarım §4.6.3 (1): "geri yükleme notu bunu AÇIKLIYORSA uyarı yerine `GERI_YUKLEME`
    satırı". Not çapayı, ilk geri yüklemenin kenara aldığı veritabanının zincir başıyla
    açıklar: çapa ona eşit ya da onun gerisinde olmalıdır. Çapa notun söylediğinin ilerisindeyse
    (bayat ya da program dışından konmuş not; kuyruğu kesilmiş veritabanının geri yüklemeyle
    örtülmesi) ya da not okunamıyor ya da zincir başı taşımıyorsa çapa denetimi not yokmuş gibi
    koşar: uyarı `GERI_YUKLEME` satırıyla BİRLİKTE yazılır."""
    for _ in range(2):
        acik_olay()
    capa = kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])  # çapadan sonra kilitli satır
    bas = denetim_izi.zincir_basi()
    assert bas is not None and bas[0] > capa.seq
    # Geri yüklenen yedek çapadan eskidir: çapanın satırı ve sonrası yok.
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa.seq])
    if not_durumu == "okunamayan":
        geri_yukleme_notu.yol(iz_durumu.dizin()).write_text("{bozuk", encoding="utf-8")
    else:
        onceki = {
            "tutarli": {"seq": bas[0], "mac": bas[1]},
            "capa_notun_ilerisinde": {"seq": capa.seq - 1, "mac": "ab" * 32},
            "zincir_yoktu_dedi": dict(geri_yukleme_notu.BOS_ZINCIR),
            "zincir_basi_yok": None,
        }[not_durumu]
        notu_yaz(onceki_zincir_basi=onceki)

    ac()

    (geri,) = satirlar(action="GERI_YUKLEME")
    if not_durumu == "tutarli":
        assert not satirlar(action="BUTUNLUK")
    else:
        (satir,) = butunluk()
        assert deger(satir, "bulgular") == ["kuyruk_kesik"]
        assert deger(satir, "duzey") == "uyari"
        assert satir.seq < geri.seq < satirlar(action="GIRIS")[-1].seq
    assert not geri_yukleme_notu.var_mi(iz_durumu.dizin())
    assert iz_durumu.oku().capa_seq == son_satir().seq  # çapa yenilendi, uyarı yinelenmez
    sayi = AuditTrail.objects.filter(action="BUTUNLUK").count()
    kilitle()
    ac()
    assert AuditTrail.objects.filter(action="BUTUNLUK").count() == sayi


@pytest.mark.parametrize("onceki", ["dosya_yoktu", "izi_bostu"])
def test_yeni_bilgisayara_tasimada_capa_yoksa_not_bunu_aciklar(onceki: str) -> None:
    """Kenara alınan veritabanında zincir yoktuysa (kurulumdan hemen sonra geri yükleme, yeni
    bilgisayara taşıma) çapa da yoktur: not bunu açıklar, "çapa yok" uyarısı çıkmaz. Çapa
    VARKEN aynı not çapayı açıklamaz (çapa notun dediğinin ilerisindedir)."""
    kilitle()
    iz_durumu.yol().unlink()  # yeni bilgisayar: iz-durumu.json yok
    if onceki == "dosya_yoktu":
        notu_yaz(onceki_dosya=None, yol_bilgisi={"tur": "kurtarma", "no": 1})
    else:
        notu_yaz(onceki_zincir_basi=dict(geri_yukleme_notu.BOS_ZINCIR))

    ac()

    assert not satirlar(action="BUTUNLUK")
    assert len(satirlar(action="GERI_YUKLEME")) == 1


@pytest.mark.parametrize("capa_kaydi", ["yoktu", "bilinmiyor"])
def test_kurulumdan_sonra_hic_kilitlenmeden_geri_yukleme_capa_uyarisi_vermez(
    capa_kaydi: str,
) -> None:
    """Bağımsız denetim bulgusu: kurulum sihirbazı ilk hesabı açar (zincir başlar), aynı
    oturumda Ayarlar → Güvenlik → Yedekten geri yükle yapılır; çapa hiç yazılmamıştır ve
    kenara alınan veritabanının zinciri doludur. Not takastan önceki çapayı da yazar
    (`capa: null`): ilk kilit açılışı "not yazılırken çapa yoktu, şimdi de yok" hâlini
    açıklanmış sayar, "kilit işareti bulunamadı" uyarısı vermez (tasarım §4.6.3 (1)). Çapanın
    durumu notta yoksa (eski not ya da okunamadı) açıklanmış sayılmaz."""
    acik_olay()
    acik_olay()
    assert not iz_durumu.yol().exists()
    bas = denetim_izi.zincir_basi()
    assert bas is not None
    capa = {"onceki_capa": None} if capa_kaydi == "yoktu" else {}
    notu_yaz(onceki_zincir_basi={"seq": bas[0], "mac": bas[1]}, **capa)
    app_password.lock()  # canlı geri yükleme oturumu servis içinden kapatır: KILIT ve çapa yok

    ac()

    assert len(satirlar(action="GERI_YUKLEME")) == 1
    if capa_kaydi == "yoktu":
        assert not satirlar(action="BUTUNLUK")
    else:
        (satir,) = butunluk()
        assert deger(satir, "bulgular") == ["capa_yok"]
    assert iz_durumu.oku().capa_seq == son_satir().seq  # not işlendi, çapa yenilendi


def test_capa_varken_capa_yoktu_diyen_not_capa_denetimini_ortmez() -> None:
    """Not "çapa yoktu" der ama çapa vardır ve kuyruk kesilmiştir: not çapayı açıklamaz."""
    capa = kilitle()
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa.seq])
    notu_yaz(onceki_zincir_basi=None, onceki_capa=None)

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kuyruk_kesik"]


def test_capa_varken_zincir_yoktu_diyen_not_capa_bulgusunu_ortmez() -> None:
    capa = kilitle()
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa.seq])
    notu_yaz(onceki_dosya=None, yol_bilgisi={"tur": "kurtarma", "no": 1})

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kuyruk_kesik"]
    assert len(satirlar(action="GERI_YUKLEME")) == 1


def test_notun_ilk_geri_yuklemesi_capayi_aciklar_bozuk_onceki_not_aciklamaz() -> None:
    """İki geri yükleme arasında kilit açılmaz: çapa İLK kenara alınan veritabanını anlatır.
    Önceki notu bozuk olan not ilk geri yüklemeyi yitirmiştir; çapayı açıklamaz."""
    capa = kilitle()
    bas = {"seq": capa.seq, "mac": capa.mac}
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa.seq])
    notu_yaz(onceki_zincir_basi=bas)
    notu_yaz(onceki_zincir_basi=None)  # ikincisinin kenara aldığı okunamadı
    acilis = iz_dogrulama.KilitAcilisi()
    iz_dogrulama._notu_oku(acilis)
    assert acilis.not_onceki_basi == (capa.seq, capa.mac)
    assert iz_dogrulama._not_capayi_acikliyor(acilis) is True

    notu = geri_yukleme_notu.oku(iz_durumu.dizin())
    assert notu is not None
    assert iz_dogrulama._notun_onceki_basi({**notu, "bozuk_not_vardi": True}) is None
    assert iz_dogrulama._notun_onceki_basi({**notu, "geri_yuklemeler": []}) is None


def test_ortadaki_satirin_degistirilmesi_kilit_acilisinda_gorunur() -> None:
    acik_olay()
    orta = acik_olay()
    acik_olay()
    kilitle()
    tetikleyicisiz("UPDATE okul_audittrail SET object_id = %s WHERE seq = %s", ["baska", orta.seq])

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == [denetim_izi.MAC_TUTMADI]
    assert deger(satir, "bulgu_satirlari") == [orta.seq]
    assert deger(satir, "duzey") == "uyari"
    assert OTURUM.hesap() is not None  # giriş engellenmez (altın kural 3)


@pytest.mark.parametrize(
    ("bozulma", "kod"),
    [
        ("yok", "capa_yok"),
        ("bozuk", "capa_bozuk"),
        ("muhur", "capa_muhru_tutmadi"),
    ],
)
def test_capa_yoksa_bozuksa_ya_da_muhru_tutmazsa_uyari(bozulma: str, kod: str) -> None:
    kilitle()
    if bozulma == "yok":
        iz_durumu.yol().unlink()
    elif bozulma == "bozuk":
        iz_durumu.yol().write_text("{bozuk", encoding="utf-8")
    else:
        durum_ = iz_durumu.oku()
        iz_durumu._yaz(replace(durum_, muhur="0" * 64))

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == [kod]
    assert iz_durumu.oku().capa_seq == son_satir().seq


def test_muhursuz_kilitli_satir_capa_yok_uyarisidir() -> None:
    kilitle()
    iz_durumu.yol().unlink()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    muhursuz = son_satir()
    assert muhursuz.key_ref == ""

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["capa_yok", "muhursuz_satir"]
    assert deger(satir, "bulgu_satirlari") == [muhursuz.seq]
    # Çapa yenilendi: mühürsüz satır artık çapadan öncedir; sonraki açılış yinelemez.
    kilitle()
    ac()
    assert len(butunluk()) == 1


def test_capa_varken_muhursuz_kilitli_satir_uyaridir() -> None:
    """Çapa yerindeyken çapadan sonra mühürsüz kilitli satır: dosya bir an kaybolmuş ya da
    satır program dışından eklenmiştir."""
    kilitle()
    once = iz_durumu.oku()
    iz_durumu.yol().unlink()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    iz_durumu._yaz(once)

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["muhursuz_satir"]


# ============================================================ kilitli satırların sayısı


def test_sondaki_tek_eksik_kilitli_satir_kesintidir_bilgi_duzeyinde() -> None:
    """Plan F1b-1: tohum dosyada ilerledi, satır yazılamadan süreç öldü → kesinti (bilgi)."""
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    durum_ = iz_durumu.oku()
    iz_durumu._yaz(replace(durum_, tohum=kanonik.ileri_tohum(durum_.tohum), adim=durum_.adim + 1))

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kesinti"]
    assert deger(satir, "duzey") == "bilgi"
    assert (deger(satir, "adim"), deger(satir, "kilitli_satir")) == (2, 1)


def test_dusen_kilitli_yazimdan_sonra_olaylar_bekler_bosluk_sonda_kesintidir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan F1b-1: tohum önce dosyada ilerler, sonra satır yazılır; sondaki TEK eksik satır
    kesintidir (bilgi). Çöküş dışı bir geri almada da (işlem düştü, disk doldu) süreç sonraki
    olayları kilitli kipte yazmayı sürdürseydi boşluk ortada kalır, bulgu yanlışlıkla uyarı
    olurdu. Düşen yazımdan sonra kilitli satır yazılmaz, tohum ilerlemez: olaylar (düşenin
    kendisi de) bellekte bekler ve ilk kilit açılışında kendi anlarıyla açık kipte yazılır."""
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])  # adım 0 yazıldı
    asil = AuditTrail.save

    def duser(self: AuditTrail, *args: Any, **kwargs: Any) -> None:
        if self.key_mode == "KILITLI":
            raise OSError("disk dolu")  # tohum ilerledi, işlem geri alınır
        asil(self, *args, **kwargs)

    with monkeypatch.context() as yama:
        yama.setattr(AuditTrail, "save", duser)
        assert masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-02.odbak"]) == 0
    durum_ = iz_durumu.oku()
    assert durum_.adim == 2  # adım 1'in satırı yok
    bas = son_satir().seq

    assert masaustu_kanca.yedek_olaylarini_yaz(silinen=["gunluk-2026-10-17.odbak"]) == 0
    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0010_ornek"]) is False
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is True
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is False  # günde bir: bellekte bekliyor
    assert son_satir().seq == bas and iz_durumu.oku() == durum_
    assert len(iz_durumu.bellekte_bekleyenler()) == 4

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kesinti"]
    assert deger(satir, "duzey") == "bilgi"
    yeni = satirlar(seq__gt=bas)
    assert [s.action for s in yeni] == ["BUTUNLUK", "YEDEK", "YEDEK", "GOC", "GUN_ISI", "GIRIS"]
    for olay in yeni[1:5]:
        assert (olay.actor, olay.key_mode, olay.account_id) == ("SISTEM", "ACIK", None)
        assert olay.values["zaman"][1].endswith("Z")
    assert (yeni[1].object_id, yeni[2].changed_fields) == ("gunluk-2026-11-02.odbak", ["silindi"])
    assert iz_durumu.bellekte_bekleyenler() == []
    assert iz_durumu.oku().adim == 0  # çapa yenilendi: kilitli yazım yeniden başlar
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_cokmeden_sonra_yeni_surec_bosluktan_sonra_kilitli_satir_yazmaz() -> None:
    """Süreç tohum ile satır arasında ölürse yeni süreç bunu dosyadan ve veritabanından görür
    (bellek boştur): kilitli satır yazmaz, olay ilk kilit açılışını bekler; boşluk sonda kalır."""
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    durum_ = iz_durumu.oku()
    iz_durumu._yaz(replace(durum_, tohum=kanonik.ileri_tohum(durum_.tohum), adim=durum_.adim + 1))
    bas = son_satir().seq

    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-02.odbak"]) == 0

    assert son_satir().seq == bas
    ac()
    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kesinti"]
    assert [s.action for s in satirlar(seq__gt=bas)] == ["BUTUNLUK", "YEDEK", "GIRIS"]


def test_birden_fazla_eksik_kilitli_satir_uyaridir() -> None:
    kilitle()
    durum_ = iz_durumu.oku()
    tohum = kanonik.ileri_tohum(kanonik.ileri_tohum(durum_.tohum))
    iz_durumu._yaz(replace(durum_, tohum=tohum, adim=2))

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kilitli_satir_eksik"]
    assert deger(satir, "duzey") == "uyari"


def test_ortadaki_kilitli_satir_silinirse_giris_acilmaz() -> None:
    """Kullanıcı kararı 03.11.2026 "Boşluğu engelle": hesabın son kaydından SONRA izden satır
    silinmişse (burada çapadan sonra kilitliyken yazılmış bir yedek satırı) giriş açılmaz. Ret
    izdeki boşluğundur, girişten önce verilir (`AuditTrailGap`, `BUTUNLUK` alanı `iz_boslugu`;
    orkestratör maddesi C-4): bu modülün doğrulaması koşmaz, `kilitli_satir_eksik` bulgusu
    yazılmaz. Silinen satır son kaydından ESKİYSE giriş açılır ve bulgu düşer (bir sonraki test)."""
    capa = kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=["a.odbak", "b.odbak", "c.odbak"])
    orta = satirlar(seq__gt=capa.seq)[1]
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [orta.seq])

    with pytest.raises(app_password.AuditTrailGap):
        ac()

    assert OTURUM.hesap() is None and not butunluk()
    (ret,) = satirlar(action="BUTUNLUK", model="okul.Account")
    assert ret.changed_fields == [app_password.IZ_BOSLUGU_ALANI]


def test_son_kayittan_eski_satir_silinirse_giris_acilir_zincir_bulgusu() -> None:
    """Boşluk denetimi yalnız hesabın son kaydından SONRASINA bakar (kullanıcı kararı 03.11.2026):
    ortadaki bir satır silinir ama program yöneticisi ondan sonra girmiştir (son kaydı yenidir).
    Giriş açılır; kilit açılışının doğrulaması boşluğu bulgu olarak gösterir (altın kural 3)."""
    acik_olay()
    orta = acik_olay()
    acik_olay()
    kilitle()
    ac()  # son kaydı (GIRIS) silinecek satırdan yeni
    kilitle()
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [orta.seq])

    ac()

    assert OTURUM.hesap() is not None
    satir = butunluk()[-1]
    assert {"sira_boslugu", "zincir_kopuk"} <= set(deger(satir, "bulgular"))


def test_dosyadaki_adim_geri_alinirsa_fazla_satir_ve_tohum_bulgusu() -> None:
    """Saldırgan son kilitli satırları gizlemek için adımı geri alamaz: önceki tohumu
    bilemez (tek yönlü), dosyanın tohumu adımla tutmaz."""
    kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=["a.odbak", "b.odbak"])
    durum_ = iz_durumu.oku()
    iz_durumu._yaz(replace(durum_, adim=1))

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["kilitli_satir_fazla", "tohum_tutmadi"]


def test_baska_capanin_kilitli_satiri_sira_bulgusudur() -> None:
    capa = kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    satir = son_satir()
    tetikleyicisiz(
        "UPDATE okul_audittrail SET key_ref = %s WHERE seq = %s", [f"{capa.seq - 1}:0", satir.seq]
    )

    ac()

    (bulgu,) = butunluk()
    # Başka çapaya bağlanan satır bu çapanın adımı sayılmaz (sondaki tek eksik: kesinti);
    # MAC'i de o çapanın tohumuyla tutmaz.
    assert deger(bulgu, "bulgular") == ["kesinti", "kilitli_sira", "mac_tutmadi"]


def test_dogrulama_yapilamazsa_bulgu_olur_giris_yine_acilir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def patla(_acilis: iz_dogrulama.KilitAcilisi) -> None:
        raise RuntimeError("deneme")

    kilitle()
    monkeypatch.setattr(iz_dogrulama, "_hazirla", patla)

    ac()

    assert OTURUM.hesap() is not None
    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["dogrulama_yapilamadi"]


# ============================================================ sırrı olmayanın eklediği satır


SAHTE_GIRIS: dict[str, Any] = {
    "action": "GIRIS",
    "actor": "HESAP",
    "account": TEST_HESAP_ID,
    "role": "yonetici",
    "model": "okul.Account",
    "object_id": TEST_HESAP_ID,
}
#: Kilit açılışından ÖNCE eklenen sahte giriş, satırın kendi izine girmesin diye başka bir
#: (uydurma) kaydın kimliğini taşır: hesabın kendi iz satırları arasındaki sahte satır girişi
#: açmaz (satırın izi tutmaz, fail-closed; `test_satir_izi.py`). "Son Girişler" kartı girişi
#: aktörün hesabından (`account`) süzer: kartın sınaması değişmez.
SAHTE_GIRIS_BASKA_KAYIT: dict[str, Any] = {
    **SAHTE_GIRIS,
    "object_id": "0e1d2c3b-4a59-4687-9a8b-7c6d5e4f3a2b",
}


def test_oturum_acikken_eklenen_sahte_giris_kilit_acilisinda_bulgu_olur_karta_gecmez() -> None:
    """Veri dosyasına yazabilen ama sırrı olmayan biri, oturum açıkken kuyruğa hesabın adına
    bir `GIRIS` satırı ekler (mühürsüz anahtar, kısıtlar kapalı). Satır kilitlenmede çapanın
    gerisinde kalır; kilit açılışının (3). denetimi onu kuralı ve mühürsüzlüğüyle bildirir,
    "Son Girişler" kartı ve parola bildirimi onu göstermez (tasarım §4.6.2 kural 2)."""
    kilitle()
    ac()
    sahte = sahte_satir(**SAHTE_GIRIS_BASKA_KAYIT)
    kilitle()

    ac()

    (satir,) = butunluk()
    assert {"satir_kurali", "muhursuz_satir"} <= set(deger(satir, "bulgular"))
    assert sahte.seq in deger(satir, "bulgu_satirlari")
    ozet = pano(TEST_HESAP_ID)
    assert len(ozet["son_girisler"]) == 2  # yalnız iki gerçek giriş
    assert all(not z.startswith("2026-11-01T10:30") for z in ozet["son_girisler"])


def test_oturum_acikken_eklenen_kurala_uyan_muhursuz_satir_bir_kez_bildirilir() -> None:
    """Kısıtları kapatmadan eklenebilen satır (kapalı kümedeki SISTEM `BUTUNLUK`): çapadan
    önce kalsa da bildirilmemiş mühürsüz satır bulgudur; bir sonraki açılış yinelemez. Sahte
    `BUTUNLUK` satırı bütünlük kartına geçmez."""
    kilitle()
    ac()
    sahte = sahte_satir(
        kisitsiz=False,
        action="BUTUNLUK",
        model=denetim_izi.IZ_DOGRULAMASI,
        values={"bulgular": [None, ["kuyruk_kesik"]]},
        changed_fields=["bulgular"],
    )
    kilitle()

    ac()

    (satir,) = [s for s in butunluk() if s.key_mode == "ACIK"]
    assert deger(satir, "bulgular") == ["muhursuz_satir"]
    assert deger(satir, "bulgu_satirlari") == [sahte.seq]
    kart = pano(TEST_HESAP_ID)["butunluk"]
    assert [k["seq"] for k in kart] == [satir.seq]  # sahte satır kart olmaz

    kilitle()
    ac()
    assert len([s for s in butunluk() if s.key_mode == "ACIK"]) == 1


def test_kilitliyken_gecersiz_kipli_sahte_giris_bulgudur() -> None:
    """Çapadan sonra kipi ne açık ne kilitli olan satır kilitli sayılmaz, gözden kaçmaz."""
    kilitle()
    sahte = sahte_satir(**{**SAHTE_GIRIS_BASKA_KAYIT, "key_mode": "XYZ"})

    ac()

    (satir,) = butunluk()
    assert "satir_kurali" in deger(satir, "bulgular")
    assert sahte.seq in deger(satir, "bulgu_satirlari")
    assert len(pano(TEST_HESAP_ID)["son_girisler"]) == 1


def test_sahte_giris_bir_onceki_girisi_kaydirip_gercek_bulguyu_gizleyemez() -> None:
    """Bütünlük kartının alt sınırı hesabın bir önceki girişidir; sahte bir `GIRIS` o sınırı
    öne kaydırıp gerçek `BUTUNLUK` satırını gizleyemez (kart yalnız doğrulanan satırı okur)."""
    kilitle()
    iz_durumu.yol().unlink()  # bu açılışta gerçek bir bulgu: çapa yok
    ac()
    sahte_satir(**SAHTE_GIRIS)

    kart = pano(TEST_HESAP_ID)["butunluk"]

    assert [(k["tur"], k["bulgular"]) for k in kart] == [("dogrulama", ["capa_yok"])]


def test_sahte_geri_yukleme_satiri_karta_gecmez() -> None:
    kilitle()
    ac()
    sahte_satir(action="GERI_YUKLEME", model=denetim_izi.GERI_YUKLEME_KAYDI)
    assert pano(TEST_HESAP_ID)["geri_yukleme"] is None


# ============================================================ yazılamayan çapa


def test_capa_yazilamazsa_eskisi_silinir_ilk_acilis_capa_yok_der(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eski çapa geçerli kalsaydı bu oturumun kuyruğu (açık satırlar ve `KILIT`) çapasız
    kalır, silinmesi görünmezdi: yazılamayan çapanın yerine eskisi silinir."""
    kilitle()  # çapa A
    ac()
    acik_olay()
    with monkeypatch.context() as yama:
        yama.setattr(iz_durumu, "_yaz", _yazilamadi_dosya)
        assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    assert not iz_durumu.yol().exists()
    # Saldırgan bu oturumun kuyruğunu siler (açık satır ve KILIT).
    tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq > %s", [satirlar(action="GIRIS")[-1].seq])

    ac()

    (satir,) = butunluk()
    assert "capa_yok" in deger(satir, "bulgular")


def test_eski_capa_silinemezse_ilk_acilis_capayi_bayat_bulur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dosyayı tutan bir program yazımı da silmeyi de engellerse eski çapa yerinde kalır; ilk
    kilit açılışı çapadan sonra açık kipte kalan `KILIT` satırını görür: "çapa bayat"."""
    kilitle()
    ac()
    acik_olay()
    with monkeypatch.context() as yama:
        yama.setattr(iz_durumu, "_yaz", _yazilamadi_dosya)
        yama.setattr(iz_durumu, "yol", _SilinemeyenDosya)
        assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    kilit = son_satir()
    assert kilit.action == "KILIT" and iz_durumu.oku().capa_seq < kilit.seq

    ac()

    (satir,) = butunluk()
    assert deger(satir, "bulgular") == ["capa_bayat"]
    assert deger(satir, "bulgu_satirlari") == [kilit.seq]
    assert iz_durumu.oku().capa_seq == son_satir().seq  # çapa yenilendi


def _yazilamadi_dosya(_durum: iz_durumu.IzDurumu) -> None:
    raise PermissionError("dosyayı başka bir program tutuyor")


class _SilinemeyenDosya:
    """`iz-durumu.json`'un silinemeyen yolu (Windows'ta dosyayı tutan virüs tarayıcısı)."""

    def unlink(self, missing_ok: bool = False) -> None:
        raise PermissionError("silinemiyor")


# ============================================================ geri yükleme notu


def test_geri_yukleme_notu_ilk_kilit_acilisinda_satir_olur_bekleyenler_yazilir() -> None:
    """Tasarım §4.4.4: not `GERI_YUKLEME` satırı olur (oturumu açan hesabın; tanıtıcı satıra
    girmez), o açılışın sistem olayları açık anahtarla `SISTEM` satırı olarak yazılır, not
    silinir, çapa yenilenir."""
    kilitle()
    dizin = iz_durumu.dizin()
    notu_yaz()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-02.odbak"])
    masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0010_ornek"])
    bas = son_satir().seq

    ac()

    yeni = satirlar(seq__gt=bas)
    assert [s.action for s in yeni] == ["GERI_YUKLEME", "YEDEK", "GOC", "GIRIS"]
    geri = yeni[0]
    assert (geri.actor, str(geri.account_id), geri.model, geri.object_id) == (
        "HESAP",
        TEST_HESAP_ID,
        denetim_izi.GERI_YUKLEME_KAYDI,
        ONCEKI,
    )
    degerler = dict(geri.values)
    # Geri yüklemenin anı nottandır; satıra kanonik UTC metniyle girer.
    zaman = degerler.pop("zaman")
    assert zaman[0] is None and zaman[1].endswith("Z")
    assert degerler == {
        "yedek": [None, GUNLUK],
        "yol": [None, "hesap"],
        "hesap": [None, TEST_HESAP_ID],
        "onceki_sha256": [None, "ab" * 32],
        "onceki_seq": [None, 42],
        "onceki_mac": [None, "cd" * 32],
    }
    assert "tanitici" not in json.dumps(geri.values)
    for olay in yeni[1:3]:
        assert (olay.actor, olay.key_mode, olay.account_id) == ("SISTEM", "ACIK", None)
        # Olayın kendi anı (nota eklendiği an) izinli değerdir; satırın anı girişinkidir.
        assert olay.values["zaman"][0] is None and olay.values["zaman"][1].endswith("Z")
        assert olay.changed_fields == (["gocler"] if olay.action == "GOC" else [])
    assert yeni[2].values["gocler"] == [None, ["okul.0010_ornek"]]
    assert not geri_yukleme_notu.var_mi(dizin)
    assert not satirlar(action="BUTUNLUK")
    assert iz_durumu.oku().capa_seq == yeni[-1].seq
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_iki_geri_yukleme_iki_satir_kurtarma_yolu_no_tasir() -> None:
    kilitle()
    notu_yaz(yol_bilgisi={"tur": "kurtarma", "no": 3}, onceki_dosya=None)
    notu_yaz()

    ac()

    ilk, ikinci = satirlar(action="GERI_YUKLEME")
    assert ilk.object_id == "" and {ad: ilk.values[ad] for ad in ilk.values if ad != "zaman"} == {
        "yedek": [None, GUNLUK],
        "yol": [None, "kurtarma"],
        "kurtarma_no": [None, 3],
    }
    assert ikinci.object_id == ONCEKI


def test_aralarinda_giris_olmayan_geri_yuklemeler_kartta_birlikte_ilki_asil_donus_yolu() -> None:
    """Bağımsız denetim bulgusu: iki geri yükleme arasında kilit açılmazsa kart yalnız sonuncuyu
    gösteriyordu; yedekten sonraki kayıtlar İLK geri yüklemenin kenara aldığı veritabanındadır
    (`geri_yukleme_notu`: "ilk kenara alınan veritabanı asıl dönüş yoludur"). Kart sonuncuyu
    gösterir, aynı girişte yazılan öncekileri eskiden yeniye verir; sonraki bir geri yükleme
    kendi kartını açar (öncekiler bir önceki girişte kalır)."""
    kilitle()
    ilk_onceki = "db-onceki-2026-11-01-091000.sqlite3"
    notu_yaz(onceki_dosya=ilk_onceki, onceki_zincir_basi={"seq": 120, "mac": "ab" * 32})
    notu_yaz(onceki_zincir_basi={"seq": 80, "mac": "cd" * 32})

    ac()

    kart = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert kart["onceki_dosya"] == ONCEKI and kart["onceki_kayit_no"] == 80
    (ilk,) = kart["onceki_geri_yuklemeler"]
    assert ilk["onceki_dosya"] == ilk_onceki
    assert (ilk["onceki_kayit_no"], ilk["onceki_zincir"]) == (120, "ABAB-ABAB")
    assert ilk["seq"] < kart["seq"] and "onceki_geri_yuklemeler" not in ilk

    kilitle()
    notu_yaz(yol_bilgisi={"tur": "kurtarma", "no": 2})
    ac()

    sonraki = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert sonraki["kurtarma_no"] == 2 and sonraki["onceki_geri_yuklemeler"] == []


def test_bozuk_notun_ustune_geri_yuklemede_ayrintisiz_satir_once_yazilir_kart_sonuncuyu_gosterir() -> (
    None
):
    """Bağımsız denetim bulgusu: bozuk notun üstüne yeni geri yükleme eklenince (`bozuk_not_
    vardi`) ayrıntısız satır EN SONA yazılıyor, kart okunabilen son geri yüklemenin yedeğini,
    yolunu ve kenara alınan dosyasını gizleyip "ayrıntılar okunamadı" diyordu. Okunamayan
    geri yükleme öncekidir: satırı önce yazılır, kart sonuncuyu gösterir."""
    kilitle()
    geri_yukleme_notu.yol(iz_durumu.dizin()).write_text("{bozuk", encoding="utf-8")
    notu_yaz()  # bozuk notun üstüne: işaretli yeni not

    ac()

    ayrintisiz, okunan = satirlar(action="GERI_YUKLEME")
    assert ayrintisiz.changed_fields == ["not_okunamadi"]
    assert okunan.object_id == ONCEKI
    kart = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert kart["ayrintisiz"] is False
    assert (kart["yedek"], kart["onceki_dosya"]) == (GUNLUK, ONCEKI)
    (onceki,) = kart["onceki_geri_yuklemeler"]
    assert onceki["ayrintisiz"] is True


def test_geri_yukleme_ani_karta_yerel_saatle_gelir_bicimsiz_an_satira_girmez() -> None:
    """Kartın tarihi geri yüklemenin anıdır (nottan), satırın anı (ilk giriş) değil. Not
    program dışından değiştirilip saat dilimsiz ya da çözülemeyen an yazılırsa satıra girmez."""
    kilitle()
    kayit = not_kaydi()
    kayit["zaman"] = "2026-10-30T22:15:30+03:00"
    geri_yukleme_notu.geri_yukleme_ekle(iz_durumu.dizin(), kayit)
    bozuk = not_kaydi()
    bozuk["zaman"] = "2026-10-30T22:15:30"  # saat dilimsiz
    geri_yukleme_notu.geri_yukleme_ekle(iz_durumu.dizin(), bozuk)

    ac()

    ilk, ikinci = satirlar(action="GERI_YUKLEME")
    assert ilk.values["zaman"] == [None, "2026-10-30T19:15:30.000000Z"]
    assert "zaman" not in ikinci.values
    kart = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert kart["geri_yukleme_ani"] is None  # son geri yüklemenin anı okunamadı
    assert kart["zaman"].endswith("+03:00")
    assert iz_dogrulama._not_zamani("2026-10-30T22:15:30+03:00") is not None
    assert iz_dogrulama._not_zamani("tarih degil") is None
    assert iz_dogrulama._not_zamani(20261030) is None


def test_geri_yukleme_karti_anini_ve_acan_hesabi_kisisiz_verir() -> None:
    kilitle()
    kayit = not_kaydi()
    kayit["zaman"] = "2026-10-30T22:15:30+03:00"
    geri_yukleme_notu.geri_yukleme_ekle(iz_durumu.dizin(), kayit)

    ac()

    kart = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert kart["geri_yukleme_ani"] == "2026-10-30T22:15:30+03:00"
    assert kart["yol"] == "hesap" and kart["yol_hesap"] == yonetici_ozeti()
    assert (kart["onceki_kayit_no"], kart["onceki_zincir"]) == (42, "CDCD-CDCD")


def test_kurtarma_yoluyla_uygulama_ici_geri_yukleme_oturumdaki_hesaba_baglanir() -> None:
    """Oturum açıkken kurtarma anahtarıyla yapılan geri yükleme de onu başlatan hesaba bağlanır:
    satır `oturum_hesap`'ı taşır, kart kişisiz özetini verir (Hakkında "Açık oturum, sahibinin
    imzasıdır"; tanıtıcı satıra girmez)."""
    kilitle()
    notu_yaz(yol_bilgisi={"tur": "kurtarma", "no": 3}, oturum_hesabi=TEST_HESAP_ID)

    ac()

    (geri,) = satirlar(action="GERI_YUKLEME")
    assert geri.values["oturum_hesap"] == [None, TEST_HESAP_ID]
    assert "hesap" not in geri.values  # parola yolu değil
    kart = pano(TEST_HESAP_ID)["geri_yukleme"]
    assert (kart["yol"], kart["kurtarma_no"]) == ("kurtarma", 3)
    assert kart["oturum_hesap"] == yonetici_ozeti() and kart["yol_hesap"] is None


@pytest.mark.parametrize(
    "ad",
    [
        "Uydurma Kisi yedegi.odbak",
        # Programın önekini koruyup ada bir kişi adı eklenmiş dosyalar.
        "oab-defteri-yedek-2026-11-02-101530-Uydurma.odbak",
        "oab-defteri-yedek-Uydurma.odbak",
        "gunluk-2026-11-01-Uydurma.odbak",
        "gunluk-2026-11-01 Pelinsu Uydurmakaya.odbak",
        "pre-migrate-Uydurma-2026-11-01.odbak",
        "pre-anonim-2026-11-01-101530-Uydurma.odbak",
    ],
)
def test_kullanicinin_sectigi_ya_da_adlandirdigi_yedek_adi_satira_girmez(ad: str) -> None:
    """Programın BİREBİR biçimde üretmediği dosya adı serbest metindir (kişi adı içerebilir;
    R1): önekini taşısa da satıra ve karta girmez (sözlük: "Elden getirilen dosya (adı kayda
    geçmez)")."""
    kilitle()
    notu_yaz(yedek=ad)

    ac()

    (geri,) = satirlar(action="GERI_YUKLEME")
    assert "yedek" not in geri.values
    assert "Uydurma" not in json.dumps(geri.values) + geri.object_id
    assert pano(TEST_HESAP_ID)["geri_yukleme"]["yedek"] is None


@pytest.mark.parametrize(
    "ad",
    [
        "gunluk-2026-11-01.odbak",
        "pre-migrate-0.2.0-2026-11-01.odbak",
        "pre-migrate-1.0.0-beta.10-2026-11-01.odbak",
        "pre-anonim-2026-11-01-101530.odbak",
        "pre-anonim-2026-11-01-101530-2.odbak",
        "oab-defteri-yedek-2026-11-02-101530.odbak",
    ],
)
def test_programin_urettigi_yedek_adlari_kayda_gecer(ad: str) -> None:
    assert denetim_izi.program_yedegi_mi(ad) is True
    assert denetim_izi.yedek_kimligi(ad) == ad
    assert denetim_izi.yedek_kimligi(f"klasor/{ad}") == ""


def test_rotasyonun_sildigi_elle_konmus_dosyanin_adi_yedek_satirina_girmez() -> None:
    """Rotasyon tarihi adın herhangi bir yerinde arar: elle konmuş "gunluk-<gün> <ad>.odbak" da
    silinir. Olay kalır, ad girmez — açık kipte, kilitli kipte ve geri yükleme notunda aynı
    kural (`denetim_izi.yedek_kimligi`)."""
    elle = "gunluk-2026-10-01 Pelinsu Uydurmakaya.odbak"
    assert masaustu_kanca.yedek_olaylarini_yaz(silinen=[elle]) == 1  # oturum açık: açık kip
    kilitle()
    assert masaustu_kanca.yedek_olaylarini_yaz(silinen=[elle]) == 1  # kilitli kip
    notu_yaz()
    masaustu_kanca.yedek_olaylarini_yaz(silinen=[elle])  # notta bekler

    ac()

    yedekler = satirlar(action="YEDEK")
    assert len(yedekler) == 3
    assert {(s.object_id, tuple(s.changed_fields)) for s in yedekler} == {("", ("silindi",))}
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail")
        assert "Uydurma" not in json.dumps([list(map(str, s)) for s in cursor.fetchall()])


@pytest.mark.parametrize("icerik", ["{bozuk", "[" * 30_000 + "]" * 30_000])
def test_bozuk_not_ayrintisiz_geri_yukleme_satiri_yazar(icerik: str) -> None:
    """Biçimsiz ya da derin iç içe (`RecursionError`) not ayrıntısız `GERI_YUKLEME` satırıdır; not
    tüketilir, çapa ve son satırların doğrulaması kesilmez (bulgu yok)."""
    kilitle()
    geri_yukleme_notu.yol(iz_durumu.dizin()).write_text(icerik, encoding="utf-8")

    ac()

    (geri,) = satirlar(action="GERI_YUKLEME")
    assert (geri.object_id, geri.changed_fields, geri.values) == ("", ["not_okunamadi"], {})
    assert not geri_yukleme_notu.var_mi(iz_durumu.dizin())
    assert not satirlar(action="BUTUNLUK")


def test_notta_bicimsiz_bekleyen_olay_atlanir_giris_acilir() -> None:
    """Not dosyası program dışından değiştirilebilir: kapalı küme dışı tür, sistem olayı
    olmayan nesne, izinsiz değer ve serbest metin (uydurma kişi adı) satıra GİRMEZ (R1).
    Programın üretmediği yedek adı doğrudan yazımdaki gibi düşer, olay boş kimlikle kalır
    (`denetim_izi.yedek_kimligi`)."""
    kilitle()
    notu_yaz()
    notu = geri_yukleme_notu.oku(iz_durumu.dizin())
    assert notu is not None
    # Program dışından değiştirilmiş not: olaylar dosyaya doğrudan yazılır.
    notu["bekleyen_olaylar"] += [
        {"eylem": "OLUSTUR", "model": "x", "object_id": "1"},
        {
            "eylem": "YEDEK",
            "model": denetim_izi.YEDEK_DOSYASI,
            "object_id": "x",
            "values": {"ad": [1, 2]},
        },
        {"eylem": "YEDEK", "model": "okul.Student", "object_id": "1"},
        {"eylem": "YEDEK", "model": denetim_izi.YEDEK_DOSYASI, "object_id": "Uydurma Kişi"},
        {
            "eylem": "GOC",
            "model": denetim_izi.SEMA_GOCU,
            "object_id": "0.2.0",
            "changed_fields": ["gocler"],
            "values": {"gocler": [None, ["Uydurma Kişi"]]},
        },
        # Anı değerlerin içinde: program oraya yazmaz, olay atlanır.
        {
            "eylem": "GUN_ISI",
            "model": denetim_izi.GUN_ISI_ERTELEME,
            "object_id": "deneme-is",
            "values": {"zaman": [None, "2026-10-30T05:00:00.000000Z"]},
        },
        "bozuk",
    ]
    geri_yukleme_notu.yol(iz_durumu.dizin()).write_text(json.dumps(notu), encoding="utf-8")

    ac()

    yeni = satirlar(seq__gt=satirlar(action="KILIT")[-1].seq)
    assert [s.action for s in yeni] == ["GERI_YUKLEME", "YEDEK", "GIRIS"]
    assert yeni[1].object_id == "" and "zaman" not in yeni[1].values  # anı yok: girmez
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_audittrail")
        assert "Uydurma" not in json.dumps([list(map(str, s)) for s in cursor.fetchall()])


def test_notta_bekleyen_olay_kendi_anini_tasir_saat_dilimsiz_an_girmez() -> None:
    """Notta bekleyen olay günler sonra, ilk kilit açılışında yazılır: satırın anı girişin
    anıdır, olayın KENDİ anı `zaman` değeridir (UTC; `GERI_YUKLEME`'deki gibi). Saat dilimsiz
    ya da çözülemeyen an satıra girmez, olay yine yazılır."""
    kilitle()
    notu_yaz()
    dizin = iz_durumu.dizin()
    for zaman in ("2026-10-30T08:00:00+03:00", "2026-10-30T08:00:00", "tarih degil"):
        geri_yukleme_notu.bekleyen_olay_ekle(
            dizin,
            {
                "eylem": "YEDEK",
                "model": denetim_izi.YEDEK_DOSYASI,
                "object_id": GUNLUK,
                "changed_fields": [],
                "values": {},
                "zaman": zaman,
            },
        )

    ac()

    ilk, ikinci, ucuncu = satirlar(action="YEDEK")
    assert ilk.values == {"zaman": [None, "2026-10-30T05:00:00.000000Z"]}
    assert kanonik.duz(ilk.at) != ilk.values["zaman"][1]  # satırın anı girişin anıdır
    assert ikinci.values == {} and ucuncu.values == {}
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == []


def test_kilit_acilisi_duserse_not_kalir_satir_yazilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    def yazilamadi(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzYazilamadi("deneme")

    kilitle()
    notu_yaz()
    monkeypatch.setattr(denetim_izi, "kayit", yazilamadi)

    with pytest.raises(denetim_izi.IzYazilamadi):
        ac()

    assert geri_yukleme_notu.var_mi(iz_durumu.dizin())
    assert not satirlar(action="GERI_YUKLEME")
    assert OTURUM.hesap() is None


def test_geri_yuklemeden_sonra_iki_depo_karsilastirilir_sahipsiz_sarmal_onayla_silinir() -> None:
    """Tasarım §4.6.1 kural 4: sarmalı olmayan açık hesap `PAROLA_YENILENMELI` olur (SISTEM);
    satırı olmayan sarmal listelenir ve yalnız program yöneticisinin onayıyla silinir."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    muhurle(Account.objects.get(pk=muhasip.id), status=AccountStatus.ACIK)
    veri = durum()
    sahipsiz = {**veri["hesaplar"][0], "id": SAHIPSIZ, "tanitici": "eski-hesap"}
    veri["hesaplar"] = [h for h in veri["hesaplar"] if h["id"] != str(muhasip.id)] + [sahipsiz]
    durum_yaz(veri)
    kilitle()
    notu_yaz(yol_bilgisi={"tur": "kurtarma", "no": 1})
    bas = son_satir().seq

    ac()

    assert Account.objects.get(pk=muhasip.id).status == AccountStatus.PAROLA_YENILENMELI
    (hesap_izi,) = satirlar(seq__gt=bas, action="HESAP")
    assert (hesap_izi.actor, hesap_izi.object_id) == ("SISTEM", str(muhasip.id))
    assert SAHIPSIZ in sarmal_kimlikleri()  # onaysız silinmez
    iki_depo = pano(TEST_HESAP_ID)["iki_depo"]
    assert iki_depo["fark_var"] is True
    assert iki_depo["silinebilir_sarmallar"] == [
        {"id": SAHIPSIZ, "tanitici": "eski-hesap", "rol_etiketi": None, "kapali": False}
    ]
    assert iki_depo["sarmalsiz_hesaplar"] == [
        {
            "id": str(muhasip.id),
            "tanitici": muhasip.login_name,
            "rol_etiketi": "Muhasip",
            "kapali": False,
        }
    ]

    yanit = APIClient().post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [SAHIPSIZ]}, format="json"
    )

    assert yanit.status_code == 200, yanit.content
    assert yanit.json()["silinen"] == [SAHIPSIZ]
    assert yanit.json()["iki_depo"]["silinebilir_sarmallar"] == []
    assert SAHIPSIZ not in sarmal_kimlikleri()
    silme = son_satir()
    assert (silme.action, silme.actor, str(silme.account_id), silme.model) == (
        "HESAP",
        "HESAP",
        TEST_HESAP_ID,
        denetim_izi.HESAP_SARMALI,
    )


def test_geri_yuklemeden_sonra_kurtarmayla_acilan_yonetici_yenilemeye_cekilmez() -> None:
    """Kurtarma anahtarıyla geri yüklemeden sonra güvenlik dosyasında program yöneticisinin
    sarmalı yoktur; kurtarmayla açılış sarmalı işlemin SONUNDA yazar (`app_password.
    _start_session`). Aynı işlemdeki iki depo karşılaştırması onu sarmallı sayar: hesap
    `PAROLA_YENILENMELI`'ye çekilmez, `HESAP` satırı yazılmaz."""
    kilitle()
    veri = durum()
    veri["hesaplar"] = [h for h in veri["hesaplar"] if h["id"] != TEST_HESAP_ID]
    durum_yaz(veri)
    notu_yaz(yol_bilgisi={"tur": "kurtarma", "no": 1})
    bas = son_satir().seq

    app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_TANITICI, new_password=YENI_PAROLA
    )

    assert Account.objects.get(pk=TEST_HESAP_ID).status == AccountStatus.ACIK
    # `HESAP`: iki aşamalı özetin bekleyen adımı (`app_password` modül başlığı); sarmalı olmayan
    # hesabı parola yenilemeye çeken `HESAP` satırı değildir (o `SISTEM`'in olurdu).
    assert [s.action for s in satirlar(seq__gt=bas)] == [
        "HESAP",
        "KURTARMA",
        "GERI_YUKLEME",
        "GIRIS",
    ]
    assert str(satirlar(seq__gt=bas)[0].account_id) == TEST_HESAP_ID
    assert TEST_HESAP_ID in sarmal_kimlikleri()
    assert pano(TEST_HESAP_ID)["iki_depo"]["fark_var"] is False


def test_sahipsiz_olmayan_sarmalin_silinmesi_reddedilir() -> None:
    yanit = APIClient().post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [TEST_HESAP_ID]}, format="json"
    )
    assert yanit.status_code == 400
    assert TEST_HESAP_ID in sarmal_kimlikleri()


# ============================================================ kartlar


def test_butunluk_ucu_kartlari_kagit_capasini_ve_son_girisleri_verir() -> None:
    kilitle()
    ac()

    yanit = APIClient().get("/api/v1/security/integrity/")

    assert yanit.status_code == 200
    veri = yanit.json()
    # Kısmi yetki ayrı uçla (plan F1b-2): kendi kartları, denetim kartları, iki depo kartı.
    assert set(veri) == {"kagit_capasi", "son_girisler", "parola_yenilenme", "okunamayan"}
    bas = son_satir()
    assert veri["kagit_capasi"] == {
        "kayit_no": bas.seq,
        "zincir": f"{bas.mac[:4]}-{bas.mac[4:8]}".upper(),
    }
    assert len(veri["son_girisler"]) == 1 and veri["son_girisler"][0].endswith("+03:00")
    assert veri["parola_yenilenme"] is None
    assert veri["okunamayan"] == []
    denetim = APIClient().get("/api/v1/security/integrity/audit/").json()
    assert denetim == {"butunluk": [], "geri_yukleme": None, "muhru_tutmayan": [], "okunamayan": []}
    iki_depo = APIClient().get("/api/v1/security/integrity/two-store/").json()
    assert iki_depo == {
        "iki_depo": {
            "fark_var": False,
            "sarmalsiz_hesaplar": [],
            "silinebilir_sarmallar": [],
            "ozeti_tutmayan_hesaplar": [],
        },
        "okunamayan": [],
    }


@pytest.mark.parametrize(
    "ham",
    [{"account_id": "zzz"}, {"at": "2026-13-45 25:00:00"}, {"at": "dun aksam"}],
    ids=["bicimsiz-hesap", "gecersiz-tarih", "tarih-degil"],
)
def test_bicimsiz_sutunlu_satir_ucu_ve_kilit_acilisini_dusurmez(ham: dict[str, Any]) -> None:
    """Bağımsız denetim bulgusu: sırrı olmayan biri sıradan bir `sqlite3` istemcisiyle hesap
    kimliği `"zzz"` olan bir `GERI_YUKLEME` satırı ekler (CHECK kısıtlarının hepsi tutar).
    Django yabancı anahtarı UUID dönüştürücüsüyle okuduğu için satır modele yüklenirken
    düşüyordu: bütünlük ucu 500 dönüyor, bütün kartlar sessizce kayboluyor, kilit açılışı
    yalnız "denetlenemedi" yazıyordu. Aynı sınıf: anı tarih olmayan satır. Artık sütunlar ham
    okunur; satırın bulgusu `satir_kurali` olur, uç 200 döner, satır karta çıkmaz."""
    acik_olay()
    bozuk = sahte_satir(
        kisitsiz=False,
        action="GERI_YUKLEME",
        model=denetim_izi.GERI_YUKLEME_KAYDI,
        actor="HESAP",
        account=TEST_HESAP_ID,
        role="yonetici",
        key_mode="ACIK",
        ham=ham,
    )
    try:
        assert denetim_izi.satir_kurali_tutuyor(bozuk) is False
        assert denetim_izi.acik_satir_dogrulayici()(bozuk) is False
        app_password.lock()

        ac()

        (satir,) = butunluk()
        assert "satir_kurali" in deger(satir, "bulgular")
        assert bozuk.seq in deger(satir, "bulgu_satirlari")
        assert "dogrulama_yapilamadi" not in deger(satir, "bulgular")
        assert APIClient().get("/api/v1/security/integrity/").status_code == 200
        yanit = APIClient().get("/api/v1/security/integrity/audit/")
        assert yanit.status_code == 200
        veri = yanit.json()
        assert veri["okunamayan"] == [] and veri["geri_yukleme"] is None
        assert "satir_kurali" in veri["butunluk"][0]["bulgular"]
    finally:
        # Biçimsiz hesap kimliği yabancı anahtarı tutmaz: test işleminin sonundaki kısıt
        # denetimi düşmesin diye satır kaldırılır (tetikleyiciler bu işlemde düşürülür).
        tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [bozuk.seq])


def test_ikili_macli_sahte_giris_son_girisleri_silmez_kilit_acilisinda_degisikliktir() -> None:
    """Bağımsız denetim bulgusu: sırrı olmayan biri hesabın adına `mac` sütunu ikili (BLOB),
    anahtar başvurusu geçerli bir `GIRIS` satırı ve ardına biçimi doğru bir satır ekler (program
    yazmayı sürdürür). Kartın süzgeci `kanonik.esit(bytes, …)`'te düşüyor: Son Girişler ve
    bütünlük kartı "okunamadı" oluyor, ön yüz "henüz giriş yapılmadı" diyordu; kilit açılışında
    doğrulama yarıda kesilip yalnız "denetlenemedi" yazıyordu. Artık satır süzgeçten geçmez
    (kartlar gerçek girişi gösterir); kilit açılışında değişiklik bulgusudur."""
    kilitle()
    ac()
    gercek = satirlar(action="GIRIS")[-1]
    sahte = sahte_satir(
        **{**SAHTE_GIRIS_BASKA_KAYIT, "key_mode": "ACIK", "key_ref": gercek.key_ref},
        ham={"mac": b"\x00" * 32},
    )
    sahte_satir(prev_mac="0" * 64)

    ozet = pano(TEST_HESAP_ID)
    assert ozet["okunamayan"] == []
    assert len(ozet["son_girisler"]) == 1 and ozet["kagit_capasi"] is not None

    app_password.lock()
    ac()

    (satir,) = butunluk()
    bulgular = deger(satir, "bulgular")
    assert "satir_kurali" in bulgular and "dogrulama_yapilamadi" not in bulgular
    assert sahte.seq in deger(satir, "bulgu_satirlari")
    ozet = pano(TEST_HESAP_ID)
    assert ozet["okunamayan"] == [] and len(ozet["son_girisler"]) == 2
    assert "satir_kurali" in ozet["butunluk"][0]["bulgular"]


def test_okunamayan_kart_otekileri_dusurmez_adi_okunamayan_listesine_girer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kartlar birbirinden bağımsız okunur: beklenmeyen bir hata yalnız o kartı boş bırakır,
    adı `okunamayan`'a girer (ön yüz uyarı kartıyla söyler); anahtar düşmüşse ret yükselir."""
    kilitle()
    ac()

    def dustu(*_a: object, **_k: object) -> None:
        raise ValueError("badly formed hexadecimal UUID string")

    monkeypatch.setattr(iz_dogrulama, "_geri_yukleme_karti", dustu)
    ozet = pano(TEST_HESAP_ID)
    assert ozet["okunamayan"] == ["geri_yukleme"] and ozet["geri_yukleme"] is None
    assert ozet["kagit_capasi"] is not None and len(ozet["son_girisler"]) == 1

    def anahtar_yok(*_a: object, **_k: object) -> None:
        raise denetim_izi.IzAnahtariBellekteDegil()

    monkeypatch.setattr(iz_dogrulama, "_kagit_capasi", anahtar_yok)
    with pytest.raises(denetim_izi.IzAnahtariBellekteDegil):
        pano(TEST_HESAP_ID)


def test_butunluk_ucu_kilitliyken_kapalidir() -> None:
    kilitle()
    for ek in ("", "audit/", "two-store/"):
        assert APIClient().get(f"/api/v1/security/integrity/{ek}").status_code == 423
    yanit = APIClient().post(
        "/api/v1/security/integrity/orphan-wraps/", {"hesaplar": [SAHIPSIZ]}, format="json"
    )
    assert yanit.status_code == 423


def test_butunluk_karti_bir_sonraki_giriste_kalkar_geri_yukleme_karti_kalir() -> None:
    """Bütünlük kartı hesabın önceki girişinden beri yazılanlardır; geri yükleme kartı
    Denetleme Kurulu "gördüm" diyene dek (2. adım) kalır."""
    kilitle()
    notu_yaz()  # not çapayı açıklar (çapa notun zincir başının gerisinde): kart geri yüklemedir
    ac()
    ozet = pano(TEST_HESAP_ID)
    assert ozet["butunluk"] == []
    assert ozet["geri_yukleme"]["onceki_zincir"] == "CDCD-CDCD"
    assert ozet["geri_yukleme"]["onceki_kayit_no"] == 42
    assert ozet["geri_yukleme"]["hesap"] == yonetici_ozeti()
    assert ozet["geri_yukleme"]["yol_hesap"] == yonetici_ozeti()  # parola yolunu açan hesap

    kilitle()
    iz_durumu.yol().unlink()  # çapa yok → bu açılışta bütünlük bulgusu
    ac()
    kart = pano(TEST_HESAP_ID)
    assert [(k["tur"], k["bulgular"]) for k in kart["butunluk"]] == [("dogrulama", ["capa_yok"])]

    kilitle()
    ac()
    sonraki = pano(TEST_HESAP_ID)
    assert sonraki["butunluk"] == []
    assert sonraki["geri_yukleme"] is not None


def test_muhru_tutmayan_hesap_denetim_kartlarindadir_iki_depo_kartinda_degil() -> None:
    """Tasarım §4.6.1 kural 1: mührü tutmayan hesabın kartı program yöneticisi ve Denetleme
    Kurulu panosuna (denetim kartları ucu); iki depo kartı (kural 4) yalnız program
    yöneticisinindir ve sarmalsız hesaplarla silinebilir kayıtları taşır (plan F1b-2)."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    ham_guncelle(muhasip.id, role="sekreter")  # program dışından rol değişimi (tehdit 19)

    denetim = iz_dogrulama.denetim_kartlari(TEST_HESAP_ID)
    iki_depo = iz_dogrulama.iki_depo_karti()

    assert denetim["muhru_tutmayan"] == [
        {
            "id": str(muhasip.id),
            "tanitici": muhasip.login_name,
            "rol_etiketi": "Sekreter",
            "kapali": False,
        }
    ]
    assert iki_depo["iki_depo"] == {
        "fark_var": False,
        "sarmalsiz_hesaplar": [],
        "silinebilir_sarmallar": [],
        "ozeti_tutmayan_hesaplar": [],
    }
    assert denetim["okunamayan"] == [] and iki_depo["okunamayan"] == []


def test_girista_muhur_tutmazsa_program_yoneticisi_kart_gorur() -> None:
    muhasip = hesap_ac(AccountRole.MUHASIP)
    kilitle()
    ham_guncelle(muhasip.id, role="sekreter")  # program dışından rol değişimi (tehdit 19)
    with pytest.raises(app_password.AccountSealMismatch):
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

    ac()

    (kart,) = pano(TEST_HESAP_ID)["butunluk"]
    assert (kart["tur"], kart["bulgular"], kart["duzey"]) == ("muhur", ["seal"], "uyari")
    # Rol etiketi kaydın SÖYLEDİĞİdir (program dışından "sekreter" yapıldı); ad-soyad yok; açık
    # hesabın açılış günü var, kapanışı yok (F-3).
    assert kart["hesap"] == {
        "id": str(muhasip.id),
        "tanitici": muhasip.login_name,
        "rol_etiketi": "Sekreter",
        "acilis": _gun(muhasip.opened_at),
        "kapanis": None,
    }


#: Program dışından yazılmış anlar: biçime uyan ama geçersiz (30 Şubat; Django'nun dönüştürücüsü
#: ValueError yükseltir) ve yerel güne çevrilemeyen (9999'un son saati; OverflowError).
BOZUK_ANLAR = ["2026-02-30 10:00:00.000000", "9999-12-31 23:59:59.000000"]


@pytest.mark.parametrize("bozuk", BOZUK_ANLAR)
def test_hesabin_bozuk_acilis_ani_butunluk_kartini_dusurmez(bozuk: str) -> None:
    """Bağımsız denetim bulgusu (F-3'ün gerilemesi): mühür kartını doğuran hesabın açılış ve kapanış
    anı program dışından bozulursa kart `butunluk`'ta kalır, günleri None'dır (kaydın söylemediği);
    bütünlük grubu (kilit açılışı doğrulamasının kartlarıyla) `okunamayan`'a düşmez. Eskiden hesap
    özeti anı ORM'nin dönüştürücüsüyle okuyordu: tek değer bütün grubu düşürürdü."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    kilitle()
    ham_guncelle(muhasip.id, role="sekreter")
    with pytest.raises(app_password.AccountSealMismatch):
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    ac()
    # Kapanış da dolu olsun diye durum da program dışından KAPALI yapılır (veritabanı kısıtı).
    ham_guncelle(muhasip.id, status=AccountStatus.KAPALI, opened_at=bozuk, closed_at=bozuk)

    ozet = pano(TEST_HESAP_ID)

    assert "butunluk" not in ozet["okunamayan"]
    (kart,) = ozet["butunluk"]
    assert (kart["tur"], kart["bulgular"]) == ("muhur", ["seal"])
    assert kart["hesap"] == {
        "id": str(muhasip.id),
        "tanitici": muhasip.login_name,
        "rol_etiketi": "Sekreter",
        "acilis": None,
        "kapanis": None,
    }


def test_geri_yuklemeyi_acan_hesabin_bozuk_acilis_ani_karti_dusurmez() -> None:
    """Bağımsız denetim bulgusu (F-3'ün gerilemesi): geri yüklemeyi açan hesabın açılış anı program
    dışından bozulursa geri yükleme kartı yine görünür (Denetleme Kurulu "Gördüm" diyebilir);
    hesabın günü None'dır."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    kilitle()
    notu_yaz(yol_bilgisi={"tur": "hesap", "hesap": str(muhasip.id), "tanitici": "muhasip"})
    ac()
    ham_guncelle(muhasip.id, opened_at=BOZUK_ANLAR[0])

    ozet = pano(TEST_HESAP_ID)

    assert "geri_yukleme" not in ozet["okunamayan"]
    kart = ozet["geri_yukleme"]
    assert kart is not None and kart["yol"] == "hesap"
    assert kart["yol_hesap"] == {
        "id": str(muhasip.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": None,
        "kapanis": None,
    }


def test_kartlarda_ayni_taniticili_eski_ve_yeni_hesap_acilis_ve_kapanisla_ayrilir() -> None:
    """Orkestratör maddesi F-3: tanıtıcı yalnız açık hesaplar arasında tekildir. Kapanan "muhasip"
    ile yerine açılan yeni "muhasip"in kart özetleri aynı tanıtıcıyı ve rol etiketini taşır; ikisini
    açılış ve kapanış günü (Europe/Istanbul, yyyy-aa-gg; açık hesapta kapanış yok) ayırır."""
    eski = hesap_ac(AccountRole.MUHASIP)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=eski.id)
    # Eski hesap geçen yıl açılmış, geçen ay kapanmış; anlar UTC'de gece yarısından önce,
    # Europe/Istanbul'da ertesi gündür (gün yerel gündür). Satır meşru yazım gibi mühürlenir.
    eski = muhurle(
        Account.objects.get(pk=eski.id),
        opened_at=datetime(2025, 8, 31, 21, 30, tzinfo=UTC),
        closed_at=datetime(2026, 10, 14, 22, 15, tzinfo=UTC),
    )
    yeni = hesap_ac(AccountRole.MUHASIP)
    assert eski.login_name == yeni.login_name

    ozet_eski = iz_dogrulama._hesap_ozeti(eski.id)
    ozet_yeni = iz_dogrulama._hesap_ozeti(yeni.id)

    assert ozet_eski == {
        "id": str(eski.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": "2025-09-01",
        "kapanis": "2026-10-15",
    }
    assert ozet_yeni == {
        "id": str(yeni.id),
        "tanitici": "muhasip",
        "rol_etiketi": "Muhasip",
        "acilis": _gun(yeni.opened_at),
        "kapanis": None,
    }
    assert ozet_eski != ozet_yeni
    # Biçimsiz ya da olmayan kimlik: günler de yoktur.
    assert iz_dogrulama._hesap_ozeti("biçimsiz") == {
        "id": "biçimsiz",
        "tanitici": None,
        "rol_etiketi": None,
        "acilis": None,
        "kapanis": None,
    }


def test_parola_sifirlanan_hesabin_sahibi_bildirimi_ve_sonraki_girisleri_gorur() -> None:
    """Tehdit 12: sıfırlama sahibine ilk girişte bildirilir; başka hesabın girişleri dönmez."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=GECICI_PAROLA
    )
    kilitle()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)

    ozet = pano(str(muhasip.id))

    bildirim = ozet["parola_yenilenme"]
    assert bildirim is not None and bildirim["tur"] == "SIFIRLAMA"
    assert len(bildirim["girisler"]) == 1
    assert len(ozet["son_girisler"]) == 1
    assert pano(TEST_HESAP_ID)["son_girisler"] == []


# ============================================================ parola yenilenme bildirimi

BILDIRIM_UCU = "/api/v1/security/integrity/reset-notice/"
#: Bildirim yokken ucun yanıtı (okunamayan kart da yok; `iz_dogrulama.bildirim_yaniti`).
BILDIRIM_YOK: dict[str, object] = {"parola_yenilenme": None, "okunamayan": []}


def _sifirla_ve_sahibiyle_ac() -> Account:
    """Program yöneticisi muhasibin parolasını sıfırlar; sahibi geçici parolayla açar."""
    muhasip = hesap_ac(AccountRole.MUHASIP)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=GECICI_PAROLA
    )
    kilitle()
    app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    return muhasip


def test_parola_bildirimi_sahibine_gorunur_gordum_izli_yazimla_kapatir() -> None:
    """Tasarım §4.4.3, tehdit 12: bildirim oturumdaki hesabındır ve kişisizdir; "Gördüm"
    bayrağı `GUNCELLE` satırıyla kaldırır (yazar sahibinin hesabı, içerik MAC'i tutar);
    sıfırlamanın anı ve türü kayıtta kalır; ikinci "Gördüm" hiçbir şey yazmaz (fikirdeş)."""
    muhasip = _sifirla_ve_sahibiyle_ac()
    istemci = APIClient()

    okuma = istemci.get(BILDIRIM_UCU)

    assert okuma.status_code == 200
    bildirim = okuma.json()["parola_yenilenme"]
    assert bildirim["tur"] == "SIFIRLAMA"
    assert bildirim["zaman"].endswith("+03:00")
    assert len(bildirim["girisler"]) == 1
    assert "Örnek Muhasip" not in okuma.content.decode("utf-8")  # ad-soyad dönmez
    bas = son_satir().seq

    yanit = istemci.post(BILDIRIM_UCU, {}, format="json")

    assert yanit.status_code == 200, yanit.content
    assert yanit.json() == BILDIRIM_YOK
    hesap = Account.objects.get(pk=muhasip.id)
    assert hesap.reset_notice_pending is False
    assert hesap.reset_kind == "SIFIRLAMA" and hesap.reset_at is not None
    (gordu,) = satirlar(seq__gt=bas)
    assert (gordu.action, gordu.actor, str(gordu.account_id), gordu.role) == (
        "GUNCELLE",
        "HESAP",
        str(muhasip.id),
        "muhasip",
    )
    assert (gordu.model, gordu.object_id) == ("okul.Account", str(muhasip.id))
    assert gordu.changed_fields == ["reset_notice_pending"]
    assert gordu.values == {"reset_notice_pending": [True, False]}
    assert denetim_izi.kaydi_dogrula(Account, muhasip.id) is True
    assert denetim_izi.zinciri_dogrula() == []
    assert istemci.get(BILDIRIM_UCU).json() == BILDIRIM_YOK

    ikinci = istemci.post(BILDIRIM_UCU, {}, format="json")

    assert ikinci.status_code == 200
    assert son_satir().seq == gordu.seq


def test_kurtarma_bildirimi_kurtarma_turundedir_ve_yalniz_sonraki_girisleri_sayar() -> None:
    """Kurtarma anahtarıyla yenilenen parola (tasarım §4.4.3): bildirim türü `KURTARMA`;
    girişler yenilenme anından sonrakilerdir, son girişler kartı öncekileri de gösterir."""
    kilitle()
    ac()  # yenilemeden önceki giriş
    kilitle()
    app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_TANITICI, new_password=YENI_PAROLA
    )

    bildirim = APIClient().get(BILDIRIM_UCU).json()["parola_yenilenme"]

    assert bildirim["tur"] == "KURTARMA"
    assert len(bildirim["girisler"]) == 1
    assert len(pano(TEST_HESAP_ID)["son_girisler"]) == 2


def test_baska_hesabin_bildirimi_bu_uctan_ne_okunur_ne_kapatilir() -> None:
    muhasip = hesap_ac(AccountRole.MUHASIP)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=GECICI_PAROLA
    )
    bas = son_satir().seq
    istemci = APIClient()

    assert istemci.get(BILDIRIM_UCU).json() == BILDIRIM_YOK
    assert istemci.post(BILDIRIM_UCU, {}, format="json").json() == BILDIRIM_YOK

    assert Account.objects.get(pk=muhasip.id).reset_notice_pending is True
    assert son_satir().seq == bas


def test_parola_bildirimi_ucu_kilitliyken_kapalidir() -> None:
    kilitle()
    assert APIClient().get(BILDIRIM_UCU).status_code == 423
    assert APIClient().post(BILDIRIM_UCU, {}, format="json").status_code == 423


def test_muhru_tutmayan_hesabin_bildirimi_kapatilmaz() -> None:
    """Mührü tutmayan satıra hiçbir servis dokunmaz (tehdit 19): ret ve bayrak yerinde; reddin
    TEK izi `BUTUNLUK` satırıdır (`SISTEM`, alan `seal`; orkestratör maddesi F-1 — eskiden mühür
    kolu satır yazmıyordu), `GUNCELLE` satırı yoktur."""
    ham_guncelle(TEST_HESAP_ID, reset_notice_pending=True, role="muhasip")
    bas = son_satir().seq

    yanit = APIClient().post(BILDIRIM_UCU, {}, format="json")

    assert yanit.status_code == 409
    assert Account.objects.get(pk=TEST_HESAP_ID).reset_notice_pending is True
    yeni = satirlar(seq__gt=bas)
    assert [(s.action, s.actor, s.model, s.object_id, s.changed_fields) for s in yeni] == [
        ("BUTUNLUK", "SISTEM", "okul.Account", TEST_HESAP_ID, ["seal"])
    ]


def test_kenara_alinan_veritabaninin_zincir_basi_salt_okunur_okunur(tmp_path: Any) -> None:
    import sqlite3
    from contextlib import closing

    db = tmp_path / "eski.sqlite3"
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute("CREATE TABLE okul_audittrail (seq INTEGER PRIMARY KEY, mac TEXT)")
        baglanti.executemany(
            "INSERT INTO okul_audittrail VALUES (?, ?)", [(1, "aa" * 32), (2, "bb" * 32)]
        )
        baglanti.commit()
    assert geri_yukleme_notu.zincir_basi_oku(db) == {"seq": 2, "mac": "bb" * 32}
    # İzi boş veritabanı: "zincir yoktu" (yeni bilgisayara taşıma; çapa da yoktur).
    izsiz = tmp_path / "izsiz.sqlite3"
    with closing(sqlite3.connect(izsiz)) as baglanti:
        baglanti.execute("CREATE TABLE okul_audittrail (seq INTEGER PRIMARY KEY, mac TEXT)")
        baglanti.commit()
    assert geri_yukleme_notu.zincir_basi_oku(izsiz) == {"seq": 0, "mac": ""}
    # Tablo yok ya da dosya okunamıyor: zincir başı bilinmiyor.
    bos = tmp_path / "bos.sqlite3"
    sqlite3.connect(bos).close()
    assert geri_yukleme_notu.zincir_basi_oku(bos) is None
    bozuk = tmp_path / "bozuk.sqlite3"
    bozuk.write_bytes(b"veritabani degil" * 100)
    assert geri_yukleme_notu.zincir_basi_oku(bozuk) is None
    assert geri_yukleme_notu.zincir_basi_oku(tmp_path / "yok.sqlite3") is None
