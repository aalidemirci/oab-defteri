"""Kilitli kip, çapa ve açılışın sistem olayları (TK16; tasarım §4.6.3, §4.2; plan F1b-1 alt commit c).

Varsayılan ortam kök `conftest.py`'dedir: oturum program yöneticisiyle açık, hesabın satırı ve
`TEST_IA`'lı iz anahtarı kurulu, zincir boş. Oturumu kapatan iki yol vardır: `OTURUM.kilitle`
(Kilitle, boşta, kapanış: `KILIT` satırı + çapa) ve `app_password.lock` (servis içi kapatma:
satır ve çapa yazmaz). Kilitli kip testleri birincisini kullanır.

Bölümler: çapa (`iz-durumu.json`) · kilitli satır (kapalı küme, tohum, mühürsüz satır, geri
yükleme notu) · açılışın olayları (`masaustu_kanca`: yedek, şema göçü) · gün işinin ertelenmesi ·
ileriye dönük güvenlik. Tasarım §10.6'nın adlı testleri: `test_sema_gocu_olayi_kilitli_kipte_
muhurlu`, `test_kilitliyken_gun_isi_is_verisi_yazmaz`; "kilitliyken yazma hata verir" maddesi
`test_kilitliyken_yazma_hata_verir`.
"""

from __future__ import annotations

import json
import os
import stat
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from django.apps import apps as django_apps
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from apps.okul import denetim_izi, erisim_gunlugu, iz_durumu, masaustu_kanca
from apps.okul.models import AccessLog, AuditAction, AuditTrail, Holiday
from apps.okul.oturum import (
    IZ_KIP_KILIDI,
    OTURUM,
    OturumDurumu,
    OturumHesabi,
    Yazar,
    kapanista_kilitle,
    sistem_olarak,
)
from apps.okul.services import app_password, geri_yukleme_notu
from apps.okul.services import calendar as calendar_service
from apps.okul.tests.oturum_ortak import SahteSaat, kurulum_durumunu_yaz, oturum_saatini_kur
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_IA, TEST_PAROLA, TEST_TANITICI, oturumu_ac_test
from shared import crypto, kanonik

pytestmark = pytest.mark.django_db

GUNLUK = "gunluk-2026-11-01.odbak"


def satirlar(**suz: Any) -> list[AuditTrail]:
    return list(AuditTrail.objects.filter(**suz).order_by("seq"))


def son_satir() -> AuditTrail:
    satir: AuditTrail | None = AuditTrail.objects.order_by("-seq").first()
    assert satir is not None
    return satir


def acik_olay() -> AuditTrail:
    """Zincire açık kipte bir satır (varsayılan yazar)."""
    with transaction.atomic():
        # `KILIT` değil: açık kipteki `KILIT` çapanın satırıdır; çapadan sonra kalırsa çapa
        # bayattır (`iz_dogrulama` "capa_bayat"). Herhangi bir hesap olayı yeter.
        return denetim_izi.olay(AuditAction.HESAP, model="okul.Account", object_id=TEST_HESAP_ID)


def kilitle() -> AuditTrail:
    """Zincir başlatılır ve oturum elle kilitlenir: `KILIT` satırı + çapa. KILIT satırını verir."""
    acik_olay()
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    return son_satir()


def ac() -> None:
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


def capa_tohumu(capa: AuditTrail) -> bytes:
    return denetim_izi.kilitli_tohum(TEST_IA, capa.seq, capa.mac)


def kilitli_mac(satir: AuditTrail, tohum: bytes) -> str:
    return kanonik.iz_mac(
        crypto.audit_locked_mac_key(tohum), denetim_izi.satir_alanlari(satir), satir.prev_mac
    )


# ============================================================ çapa (iz-durumu.json)


def test_capa_kilitlenmede_zincir_basina_yazilir_muhru_ve_tohumu_tutar() -> None:
    capa = kilitle()
    durum = iz_durumu.oku()
    assert capa.action == "KILIT"
    assert (durum.capa_seq, durum.capa_mac, durum.adim) == (capa.seq, capa.mac, 0)
    beklenen = kanonik.capa_muhru(crypto.audit_anchor_key(TEST_IA), capa.seq, capa.mac)
    assert durum.muhur == beklenen
    assert durum.tohum == capa_tohumu(capa)
    yol = iz_durumu.yol()
    assert yol.parent == app_password.state_path().parent  # guvenlik.json'la aynı dizin
    assert not yol.with_name(yol.name + ".tmp").exists()
    if os.name == "posix":
        assert stat.S_IMODE(yol.stat().st_mode) == 0o600


def test_bosta_kilitte_ve_duzenli_kapanista_capa_yazilir() -> None:
    kurulum_durumunu_yaz(tamam=True)
    acik_olay()
    saat = SahteSaat()
    oturum_saatini_kur(saat)
    saat.ilerlet(10 * 60)
    OTURUM.degerlendir()  # boşta kilit
    assert crypto.is_unlocked() is False
    assert iz_durumu.oku().capa_seq == son_satir().seq

    oturumu_ac_test()
    acik_olay()
    assert kapanista_kilitle() is True
    kapanis = son_satir()
    assert (kapanis.action, kapanis.actor) == ("KILIT", "SISTEM")
    assert iz_durumu.oku().capa_seq == kapanis.seq


def test_oturum_kapaliyken_kapanis_capa_yazmaz() -> None:
    acik_olay()
    app_password.lock()  # servis içi kapatma: satır da çapa da yok
    assert kapanista_kilitle() is False
    assert not iz_durumu.yol().exists()


def test_kilit_satiri_capa_ve_anahtarin_dusmesi_kip_kilidi_altindadir() -> None:
    """Kilitlenmenin iz parçası tek parça (oturum modül başlığı "ÇAPA"): kilit izi çağrılırken
    `IZ_KIP_KILIDI` bu iş parçacığındadır; sistem olayı araya giremez."""
    gorulen: list[bool] = []

    def izle(_hesap: OturumHesabi, _kim: Yazar) -> None:
        # Başka bir iş parçacığı (od-gunluk gibi) kilidi bu anda alamaz.
        sonuc: list[bool] = []
        deneyen = threading.Thread(target=lambda: sonuc.append(IZ_KIP_KILIDI.acquire(timeout=0.05)))
        deneyen.start()
        deneyen.join(5)
        gorulen.append(sonuc == [False])

    oturum = OturumDurumu(kilit_izi=izle, hesap_kurulu=lambda: True, dosya_kayip=lambda: False)
    oturum.ac(
        OturumHesabi(id=TEST_HESAP_ID, tanitici=TEST_TANITICI, rol="yonetici"),
        veri_anahtari=TEST_DEK,
        iz_anahtari=TEST_IA,
    )
    assert oturum.kilitle() == "kilitlendi"
    assert gorulen == [True]


def test_capa_yazilamasa_da_kilit_uygulanir(monkeypatch: pytest.MonkeyPatch) -> None:
    def yazilamadi(_durum: iz_durumu.IzDurumu) -> None:
        raise OSError("disk dolu")

    monkeypatch.setattr(iz_durumu, "_yaz", yazilamadi)
    acik_olay()
    assert OTURUM.kilitle() == "kilitlendi"
    assert crypto.is_unlocked() is False
    assert son_satir().action == "KILIT"
    assert not iz_durumu.yol().exists()


@pytest.mark.bos_zincir
def test_zincir_bosken_capa_yazilmaz() -> None:
    assert iz_durumu.capa_yaz() is False
    assert not iz_durumu.yol().exists()


@pytest.mark.parametrize(
    "icerik",
    [
        "{bozuk",
        "[]",
        # Derin iç içe JSON `json.loads`'ta RecursionError verir: bozuk sayılır, 500 değil.
        "[" * 100_000 + "]" * 100_000,
        json.dumps({"surum": 2}),
        json.dumps({"surum": 1, "capa": {"seq": 0, "mac": "0" * 64, "muhur": "0" * 64}}),
        json.dumps(
            {
                "surum": 1,
                "capa": {"seq": 3, "mac": "0" * 64, "muhur": "0" * 64},
                "tohum": "zz",
                "adim": 0,
            }
        ),
    ],
)
def test_bicimi_bozuk_iz_durumu_okunamaz(icerik: str) -> None:
    iz_durumu.yol().write_text(icerik, encoding="utf-8")
    with pytest.raises(iz_durumu.IzDurumuBozuk):
        iz_durumu.oku()


# ============================================================ kilitli satır


def test_kilitliyken_sistem_olayi_kilitli_kipte_muhurlenir_tohum_dosyada_ilerler() -> None:
    capa = kilitle()
    tohum0 = capa_tohumu(capa)

    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK], silinen=["gunluk-2026-10-17.odbak"])
    alinan, silinen = satirlar(seq__gt=capa.seq)

    for satir, k in ((alinan, 0), (silinen, 1)):
        assert (satir.action, satir.actor, satir.account_id, satir.role) == (
            "YEDEK",
            "SISTEM",
            None,
            "",
        )
        assert (satir.key_mode, satir.key_ref, satir.record_mac) == (
            "KILITLI",
            f"{capa.seq}:{k}",
            "",
        )
    assert (alinan.object_id, alinan.changed_fields) == (GUNLUK, [])
    assert silinen.changed_fields == ["silindi"]
    tohum1 = kanonik.ileri_tohum(tohum0)
    assert alinan.mac == kilitli_mac(alinan, tohum0)
    assert silinen.mac == kilitli_mac(silinen, tohum1)
    assert silinen.prev_mac == alinan.mac  # zincir kilitli kipte de bağlıdır
    durum = iz_durumu.oku()
    assert (durum.adim, durum.tohum) == (2, kanonik.ileri_tohum(tohum1))
    # Çapa değişmez; dosya eski tohumları TAŞIMAZ.
    assert (durum.capa_seq, durum.capa_mac) == (capa.seq, capa.mac)
    metin = iz_durumu.yol().read_text(encoding="utf-8")
    assert tohum0.hex() not in metin and tohum1.hex() not in metin


def test_sema_gocu_olayi_kilitli_kipte_muhurlu() -> None:
    """Tasarım §10.6/§14 F1b kapısı: kilitliyken uygulanan göçün `GOC` satırı kilitli kip
    anahtarıyla mühürlüdür ve çapanın tohumundan doğrulanır (masaüstü göçten sonra
    `masaustu_kanca.goc_olayini_yaz`'ı çağırır; `desktop/main.prepare_data`)."""
    capa = kilitle()

    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0010_ornek"]) is True
    goc = son_satir()

    assert (goc.action, goc.model, goc.object_id) == ("GOC", denetim_izi.SEMA_GOCU, "0.2.0")
    assert goc.values == {"gocler": [None, ["okul.0010_ornek"]]}
    assert (goc.actor, goc.key_mode, goc.key_ref) == ("SISTEM", "KILITLI", f"{capa.seq}:0")
    # Mühür çapanın tohumundandır: İA ile tohum₀ türetilir, satırın MAC'i onunla tutar.
    assert goc.mac == kilitli_mac(goc, capa_tohumu(capa))
    assert goc.mac != kanonik.iz_mac(
        crypto.audit_chain_key(TEST_IA), denetim_izi.satir_alanlari(goc), goc.prev_mac
    )
    # Kilit açılışı doğrular: bulgu yok, BUTUNLUK satırı yok.
    ac()
    assert not satirlar(action="BUTUNLUK")
    assert denetim_izi.zinciri_dogrula() == []


def test_goc_yoksa_satir_yoktur() -> None:
    kilitle()
    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=[]) is False
    assert son_satir().action == "KILIT"


def test_kilitliyken_yazma_hata_verir() -> None:
    """Tasarım §14 F1b kapısı: DEK yokken iş verisi yazılmaz; kilitli kip yalnız kapalı
    kümedeki SISTEM olayını yazar (yazıcı ve veritabanı kısıtı birlikte)."""
    kapa = kilitle()
    with pytest.raises(denetim_izi.IzAnahtariBellekteDegil):
        calendar_service.create_holiday(
            name="Uydurma idari izin",
            start_date=date(2026, 11, 20),
            end_date=date(2026, 11, 20),
            kind="OTHER",
        )
    assert not Holiday.objects.exists()
    with pytest.raises(denetim_izi.IzYazilamadi, match="kapalı küme"):
        iz_durumu.sistem_olayi("OLUSTUR", model=denetim_izi.YEDEK_DOSYASI, object_id="x")
    muhur = denetim_izi.KilitliMuhur(zincir_anahtari=b"\x00" * 32, key_ref=f"{kapa.seq}:0")
    with pytest.raises(denetim_izi.IzYazilamadi, match="SISTEM"), transaction.atomic():
        denetim_izi.kilitli_olay(
            AuditAction.YEDEK, model=denetim_izi.YEDEK_DOSYASI, object_id="x", muhur=muhur
        )  # varsayılan yazar hesaptır
    with pytest.raises(denetim_izi.IzYazilamadi, match="kapalı küme"), sistem_olarak():
        with transaction.atomic():
            denetim_izi.kilitli_olay(
                AuditAction.OLUSTUR, model=denetim_izi.YEDEK_DOSYASI, object_id="x", muhur=muhur
            )
    # Program dışından eklenen kapalı küme dışı kilitli satırı veritabanı reddeder.
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO okul_audittrail (seq, at, actor, account_id, role, action, model, "
            'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, '
            "prev_mac, mac) VALUES (%s, '2026-11-01 07:30:00', 'SISTEM', NULL, '', 'OLUSTUR', "
            "'x', 'x', '[]', '{}', '', '', 'KILITLI', '1:0', %s, %s)",
            [kapa.seq + 1, kapa.mac, "0" * 64],
        )
    assert son_satir().seq == kapa.seq


@pytest.mark.bos_zincir
def test_ilk_hesaptan_once_kilitli_olay_yazilmaz() -> None:
    """Zincir boşken (ilk hesaptan önce; İA yok) olay yazılmaz (plan F1b-1)."""
    app_password.lock()
    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK]) == 0
    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0001_initial"]) is False
    assert AuditTrail.objects.count() == 0


@pytest.mark.parametrize("bozuk", [False, True], ids=["dosya_yok", "dosya_bozuk"])
def test_iz_durumu_yoksa_ya_da_bozuksa_kilitli_satir_muhursuz_yazilir(bozuk: bool) -> None:
    capa = kilitle()
    if bozuk:
        iz_durumu.yol().write_text("{bozuk", encoding="utf-8")
    else:
        iz_durumu.yol().unlink()

    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    satir = son_satir()

    assert (satir.key_mode, satir.key_ref, satir.action) == ("KILITLI", "", "YEDEK")
    # Zincire bağlıdır ama sırsız anahtarla: mühürlü sayılmaz, doğrulama gösterir.
    assert satir.prev_mac == capa.mac
    assert satir.mac == kanonik.iz_mac(
        kanonik.MUHURSUZ_ANAHTAR, denetim_izi.satir_alanlari(satir), satir.prev_mac
    )
    oturumu_ac_test()
    assert denetim_izi.zinciri_dogrula() == [
        denetim_izi.ZincirBulgusu(satir.seq, denetim_izi.MUHURSUZ)
    ]


def test_geri_yukleme_notu_varken_kilitli_satir_yazilmaz_olay_nota_eklenir() -> None:
    kilitle()
    bas = son_satir().seq
    dizin = iz_durumu.dizin()
    geri_yukleme_notu.geri_yukleme_ekle(
        dizin,
        geri_yukleme_notu.geri_yukleme_kaydi(
            yedek=GUNLUK,
            onceki_dosya=None,
            onceki_sha256=None,
            onceki_zincir_basi=None,
            yol_bilgisi={"tur": "kurtarma", "no": 1},
        ),
    )
    durum = iz_durumu.oku()

    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK]) == 0
    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0010_ornek"]) is False

    assert son_satir().seq == bas  # satır yok
    assert iz_durumu.oku() == durum  # tohum ilerlemedi
    notu = geri_yukleme_notu.oku(dizin)
    assert notu is not None
    assert [olay["eylem"] for olay in notu["bekleyen_olaylar"]] == ["YEDEK", "GOC"]
    assert notu["bekleyen_olaylar"][1]["values"] == {"gocler": [None, ["okul.0010_ornek"]]}


def test_acik_oturumda_sistem_olayi_acik_kipte_sistemin_satiridir() -> None:
    acik_olay()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK])
    satir = son_satir()
    assert (satir.action, satir.actor, satir.key_mode) == ("YEDEK", "SISTEM", "ACIK")
    assert satir.key_ref.isdigit()
    assert not iz_durumu.yol().exists()  # açık kipte tohum yoktur


def test_tohum_satirdan_once_ilerler_kesintide_satir_eksik_kalir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan F1b-1: tohum önce dosyada ilerler, sonra satır yazılır. Satır yazılamadan süreç
    ölürse (burada kayıt hatası) dosya bir adım ileridedir, satır yoktur (doğrulama bunu
    kesinti sayar; `test_iz_dogrulama.py`). Olay kaybolmaz: ilk kilit açılışına dek bellekte
    bekler."""
    capa = kilitle()
    asil = AuditTrail.save

    def olur(self: AuditTrail, *args: Any, **kwargs: Any) -> None:
        if self.key_mode == "KILITLI":
            assert iz_durumu.oku().adim == 1  # kaydetmeden ÖNCE dosya ilerlemiş
            raise OSError("elektrik kesildi")
        asil(self, *args, **kwargs)

    monkeypatch.setattr(AuditTrail, "save", olur)
    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK]) == 0  # hata yükseltmez
    assert son_satir().seq == capa.seq
    durum = iz_durumu.oku()
    assert (durum.adim, durum.tohum) == (1, kanonik.ileri_tohum(capa_tohumu(capa)))
    assert [(o["eylem"], o["object_id"]) for o in iz_durumu.bellekte_bekleyenler()] == [
        ("YEDEK", GUNLUK)
    ]


def test_tohum_ilerlemeden_dusen_kilitli_yazim_bosluk_birakmaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tohum dosyaya yazılamadıysa satır da yazılmaz, boşluk yoktur: olay günlüğe düşer,
    sonraki olaylar kilitli kipte yazılmayı sürdürür."""
    capa = kilitle()

    def yazilamadi(_durum: iz_durumu.IzDurumu) -> None:
        raise PermissionError("dosyayı başka bir program tutuyor")

    with monkeypatch.context() as yama:
        yama.setattr(iz_durumu, "_yaz", yazilamadi)
        assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK]) == 0
    assert iz_durumu.oku().adim == 0 and iz_durumu.bellekte_bekleyenler() == []

    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-02.odbak"]) == 1
    assert son_satir().key_ref == f"{capa.seq}:0"


def test_masaustu_kancasi_iz_yazilamasa_da_hata_yukseltmez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def patla(*_a: object, **_k: object) -> None:
        raise RuntimeError("deneme")

    monkeypatch.setattr(iz_durumu, "sistem_olayi", patla)
    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK], silinen=[GUNLUK]) == 0
    assert masaustu_kanca.goc_olayini_yaz(surum="0.2.0", gocler=["okul.0010_ornek"]) is False


# ============================================================ gün işinin ertelenmesi


@dataclass(frozen=True)
class GunIsi:
    """Sınanan gün işi: kapının kaydı, işin izlediği model ve işin veriye dokunup dokunmadığı."""

    kayit: masaustu_kanca.GunlukIsKaydi
    model: str
    yapildi: Callable[[], bool]


@pytest.fixture(params=["deneme-tohum", erisim_gunlugu.SILME_ISI])
def gun_isi(request: pytest.FixtureRequest) -> Iterator[GunIsi]:
    """DEK isteyen iki gün işi: kapalı günleri tohumlayan deneme işi (izli iş verisi yazar) ve
    ÜRETİMDEKİ erişim günlüğü silmesi (`OkulConfig.ready`'nin kaydettiği; süresi dolmuş satırı
    siler, `KVKK_SILME` yazar)."""
    masaustu_kanca._reset_for_tests()
    yapildi: Callable[[], bool]
    if request.param == "deneme-tohum":

        def tohumla() -> bool:
            return calendar_service.seed_holidays(2026).created > 0

        masaustu_kanca.gunluk_is_kaydet("deneme-tohum", tohumla)
        model, yapildi = "okul.Holiday", Holiday.objects.exists
    else:
        django_apps.get_app_config("okul").ready()  # üretimdeki kayıt yolu
        eski = AccessLog.objects.create(
            at=timezone.now() - timedelta(days=3 * 366),
            account_id=TEST_HESAP_ID,
            role="yonetici",
            kind="KISI_DOKUMU",
            model="okul.Student",
            object_id="7",
        )

        def silindi() -> bool:
            return not AccessLog.objects.filter(pk=eski.pk).exists()

        model, yapildi = "okul.AccessLog", silindi

    try:
        (kayit,) = [is_ for is_ in masaustu_kanca.gunluk_isler() if is_.ad == request.param]
        yield GunIsi(kayit=kayit, model=model, yapildi=yapildi)
    finally:
        masaustu_kanca._reset_for_tests()


def test_kilitliyken_gun_isi_is_verisi_yazmaz(gun_isi: GunIsi) -> None:
    """Tasarım §10.6/§14 F1b kapısı: DEK isteyen gün işi kilitliyken iş verisi yazmaz; ertelenir,
    `GUN_ISI` satırı iş başına günde bir kez (kilitli kipte, `SISTEM`) yazılır. Kilit açılınca
    sonraki deneme işi yapar. Gerçek erişim günlüğü silmesiyle de sınanır (plan F1b-1)."""
    capa = kilitle()

    assert gun_isi.kayit.calistir() is False
    assert gun_isi.kayit.calistir() is False  # saat sonraki deneme: ikinci satır yok

    assert not gun_isi.yapildi()
    (ertele,) = satirlar(seq__gt=capa.seq)
    assert (ertele.action, ertele.model, ertele.object_id) == (
        "GUN_ISI",
        denetim_izi.GUN_ISI_ERTELEME,
        gun_isi.kayit.ad,
    )
    assert (ertele.actor, ertele.key_mode, ertele.key_ref) == ("SISTEM", "KILITLI", f"{capa.seq}:0")

    ac()
    assert not satirlar(action="BUTUNLUK")  # kilitli satır çapanın tohumuyla doğrulandı
    assert gun_isi.kayit.calistir() is True
    assert gun_isi.yapildi()
    izleri = satirlar(model=gun_isi.model)
    assert izleri and all(s.actor == "SISTEM" and s.key_mode == "ACIK" for s in izleri)


def test_gun_isi_ertelemesi_acik_oturumda_da_gunde_bir_kezdir() -> None:
    acik_olay()
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is True
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is False
    assert iz_durumu.gun_isi_ertelendi("baska-is") is True
    assert [s.object_id for s in satirlar(action="GUN_ISI")] == ["deneme-is", "baska-is"]


def test_gun_isi_ertelemesi_notta_bekliyorsa_yinelenmez() -> None:
    kilitle()
    dizin = iz_durumu.dizin()
    geri_yukleme_notu.bekleyen_olay_ekle(
        dizin,
        {
            "eylem": "GUN_ISI",
            "model": denetim_izi.GUN_ISI_ERTELEME,
            "object_id": "deneme-is",
            "changed_fields": [],
            "values": {},
        },
    )
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is False
    notu = geri_yukleme_notu.oku(dizin)
    assert notu is not None and len(notu["bekleyen_olaylar"]) == 1
    assert notu["bekleyen_olaylar"][0]["zaman"]  # olay eklendiği anı taşır


@pytest.mark.parametrize("zaman", ["dun", "okunamayan"])
def test_gun_isi_ertelemesi_dunden_bekleyen_olay_bugunu_engellemez(zaman: str) -> None:
    """Günde bir kuralı bekleyen olayın KENDİ gününe bakar (`zaman`): dünden notta bekleyen
    olay bugünün satırını engellemez; anı okunamayan olay bugünün sayılmaz."""
    kilitle()
    dizin = iz_durumu.dizin()
    an = (
        (timezone.localtime() - timedelta(days=1)).isoformat(timespec="seconds")
        if zaman == "dun"
        else "2026-10-30T08:00:00"  # saat dilimsiz
    )
    geri_yukleme_notu.bekleyen_olay_ekle(
        dizin,
        {
            "eylem": "GUN_ISI",
            "model": denetim_izi.GUN_ISI_ERTELEME,
            "object_id": "deneme-is",
            "changed_fields": [],
            "values": {},
            "zaman": an,
        },
    )

    assert iz_durumu.gun_isi_ertelendi("deneme-is") is True
    assert iz_durumu.gun_isi_ertelendi("deneme-is") is False  # bugünkü artık notta
    notu = geri_yukleme_notu.oku(dizin)
    assert notu is not None and len(notu["bekleyen_olaylar"]) == 2


# ============================================================ ileriye dönük güvenlik


def test_sonraki_tohum_onceki_kilitli_satirlari_yeniden_muhurleyemez() -> None:
    """Tasarım §4.6.3: dosyayı bir an okuyan kişi (İA'sız) o andan önce yazılmış kilitli
    satırları değiştiremez. Saldırgan dosyadaki güncel tohumla eski satırı yeniden mühürler:
    doğrulama (veritabanından türetilen anahtar) tutmadığını görür."""
    capa = kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK, "gunluk-2026-11-02.odbak"])
    ilk, ikinci = satirlar(seq__gt=capa.seq)
    calinan = iz_durumu.oku().tohum  # tohum₂: dosyada yalnız bu var

    # Saldırgan ilk satırın kimliğini değiştirip elindeki tek tohumdan türeyen anahtarla mühürler.
    alanlar = {**denetim_izi.satir_alanlari(ilk), "object_id": "sahte.odbak"}
    for tohum in (calinan, kanonik.ileri_tohum(calinan)):
        sahte_mac = kanonik.iz_mac(crypto.audit_locked_mac_key(tohum), alanlar, ilk.prev_mac)
        with connection.cursor() as cursor:
            for ad in ("okul_audittrail_no_update", "okul_audittrail_no_delete"):
                cursor.execute(f"DROP TRIGGER IF EXISTS {ad}")
            cursor.execute(
                "UPDATE okul_audittrail SET object_id = %s, mac = %s WHERE seq = %s",
                ["sahte.odbak", sahte_mac, ilk.seq],
            )
        oturumu_ac_test()
        bulgular = denetim_izi.zinciri_dogrula(ilk=ilk.seq)
        assert denetim_izi.ZincirBulgusu(ilk.seq, denetim_izi.MAC_TUTMADI) in bulgular
        # İkinci satırın prev_mac'i değişmeyen asıl MAC'e bağlıdır: zincir de kopar.
        assert denetim_izi.ZincirBulgusu(ikinci.seq, denetim_izi.ZINCIR_KOPUK) in bulgular
        app_password.lock()


def test_tohumlar_veritabanindan_tek_yonlu_turer() -> None:
    """Kilitli satırın anahtarı çapa satırından türer; adım ileri gider, geri gelmez."""
    capa = kilitle()
    masaustu_kanca.yedek_olaylarini_yaz(alinan=[GUNLUK, "gunluk-2026-11-02.odbak"])
    oturumu_ac_test()
    cozucu = denetim_izi.kilitli_zincir_anahtarlari()
    ilk, ikinci = satirlar(seq__gt=capa.seq)
    tohum0 = capa_tohumu(capa)
    assert cozucu(ilk) == crypto.audit_locked_mac_key(tohum0)
    assert cozucu(ikinci) == crypto.audit_locked_mac_key(kanonik.ileri_tohum(tohum0))
    assert denetim_izi.zinciri_dogrula() == []


def test_iz_durumu_yolu_guvenlik_dizinindedir(guvenlik_ortami: Path) -> None:
    assert iz_durumu.yol() == guvenlik_ortami / "iz-durumu.json"
    assert geri_yukleme_notu.yol(iz_durumu.dizin()) == guvenlik_ortami / "geri-yukleme-notu.json"
