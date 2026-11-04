"""Hesap satırının izi — kullanıcı kararı 03.11.2026 "Girişte reddet" (F1b-2 alt commit b4).

Hesap satırı denetim izindeki SON içerik MAC'li kaydını tutmalıdır (`services.satir_izi`,
`app_password` modül başlığı "SATIRIN İZİ"): mührü ve parola kaydının özeti tutsa da eski bir
kopyadan geri konmuş satır hiçbir yoldan giriş, oturum işlemi, kurtarma ya da hesap işlemi açmaz;
meşru hiçbir akış yanlış alarm vermez. Bu dosya:

* ALTIN LİSTE ve ORM EŞİTLİĞİ: içerik MAC'ine giren alanlar, ORM'siz okuyucunun ham sütun
  çevirisi (zaman, yabancı anahtar, bayrak, şifreli ad, bozuk ad) ve onarımın ORM'siz yazıcısının
  satırı `denetim_izi`'nin yazdığıyla birebir;
* SATIR GERİ SARMA: üç senaryo (sıfırlamadan sonra — Senaryo 1, yetkisi düşürülen ikinci program
  yöneticisi, kapanış) × giriş; aynı geri sarmada oturumdaki parola doğrulaması, kurtarma
  anahtarıyla açılış, hesap işlemleri (işlem gören ve işlemi yapan; aklamaz), iki depo
  karşılaştırması; çıkış: kurtarma anahtarıyla geri yükleme;
* İZİN DÜZENLENMESİ: `record_mac`'i boşaltmak, `key_ref`'i başka bir iz anahtarına çevirmek,
  kipi değiştirmek, sahte satır eklemek, biçimsiz değer yazmak, hesabın bütün iz satırlarını
  silmek fail-open'a çevirmez;
* İZ BOŞLUĞU (kullanıcı kararı 03.11.2026 "Boşluğu engelle", b5): hesabın son kaydından sonraki
  satırların silinmesi (200 satırlık pencerenin içinde ve dışında, ilgisiz satır da), silinip
  sonrakilerin aşağı kaydırılması, REAL sıraya taşınması ve BLOB sıra girişi, hesap işlemini,
  oturumdaki parola doğrulamasını ve kurtarma anahtarıyla açılışı kapatır; ilk reddin `BUTUNLUK`
  satırı, açılıştaki kilitli satır ve iz anahtarı tablosuna eklenen sahte, emekli anahtar kaymayı
  örtmez; birincil anahtarsız yeniden kurulmuş tabloda birebir kopya silmeyi örtmez; boşluklu çapa
  K-a'ya düşer; çıkış kurtarma anahtarıyla eski yedektir. Kuyruk kesme ENGELLEMEZ (çapa kartı),
  bozuk dayanak engellemez; tamsayı takası kalan risktir (sabitlenir); denetimin maliyeti HMAC
  sayısıyla sınırlıdır. Zincir başı tamsayı değilse, en büyük tamsayıdaysa ya da `mac`'i metin
  değilse yazıcılar Türkçe reddeder (O-3); parola değiştirmenin işlem içi reddi `BUTUNLUK` bırakır
  (O-4);
* YANLIŞ ALARM YOK: ilk kurulumdan kapanışa her meşru akış ve iki aşamalı yazımın kesintileri;
  geri yükleme ve onarım her çapa hâlinde (onarımın `SISTEM` `HESAP` satırları; ilk açılış
  açılır, zincir bulgusuz, kayıt bütünlüğü tutar);
* K-a birim düzeyinde (onarım satırının değişen alanları alan alan) ve `read_state`'in derin iç
  içe JSON'u;
* BAĞIMSIZ DENETİM BULGULARI: BLOB'a çevrilmiş iz sırası (giriş, iz anahtarı), sahte taze çapa
  (sıra kuralı), derin iç içe iz satırı (giriş, geri yükleme, notlu açılış), kararın verildiği
  hâle bağlanma (beklenen mühür) ve eşzamanlı meşru yazımın yanlış alarm vermemesi (tek anlık
  görüntü, yanlış alarm ayıklaması; güncel satırdan yeniden sınama).

Geri yükleme yetkisinin (konsol, masaüstü, uygulama içi) kolu `test_geri_yukleme_yetkisi.py`'de.
Adlar, parolalar ve kimlikler uydurmadır.
"""

from __future__ import annotations

import base64
import itertools
import json
import re
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from django.db import connection, connections, transaction
from django.utils import timezone

from apps.okul import denetim_izi, iz_dogrulama, iz_durumu, masaustu_kanca
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditActor,
    AuditKey,
    AuditKeyMode,
    AuditTrail,
    SuspendReason,
)
from apps.okul.oturum import OTURUM, Yazar, sistem_olarak, yazar_olarak
from apps.okul.services import (
    app_password,
    backup_restore,
    geri_yukleme_notu,
    geri_yukleme_yetkisi,
    hesaplar,
    ozet_onarimi,
    satir_izi,
)
from apps.okul.tests.geri_yukleme_ortak import (
    HesapSatiri,
    geri_yukle,
    goruntu,
    hesap_satiri_oku,
    programa_al,
    yetkili_sqlite,
)
from apps.okul.tests.hesap_ortak import (
    GECICI_PAROLA,
    UCUNCU_PAROLA,
    YENI_PAROLA,
    durum,
    durum_yaz,
    ham_guncelle,
    hesap_ac,
    muhurle,
)
from apps.okul.tests.iz_ortak import sahte_satir
from conftest import (
    TEST_DEK,
    TEST_HESAP_ID,
    TEST_IA,
    TEST_KURTARMA_ANAHTARI,
    TEST_PAROLA,
)
from shared import crypto, kanonik

pytestmark = pytest.mark.django_db

#: Reddedilen girişte verilen (uydurma) yeni parola ve meşru akışların sonraki parolası.
_SONRAKI_PAROLA = "Sonraki-Parola-9!"
_DORDUNCU_PAROLA = "Dorduncu-Parola-4%"

#: Uydurma kimlikler (K-a birim testleri).
_YONETICI_2 = "5a7b9c1d-2e3f-4a5b-8c6d-7e8f9a0b1c2d"
_MUHASIP = "1b2c3d4e-5f60-4a71-8b92-a3b4c5d6e7f8"
_SEKRETER = "2c3d4e5f-6071-4b82-9ca3-b4c5d6e7f809"
_BASKAN = "3d4e5f60-7182-4c93-8db4-c5d6e7f8091a"
_BASKAN_YARDIMCISI = "4e5f6071-8293-4da4-9ec5-d6e7f8091a2b"
#: Hesabın iz satırlarının çevrildiği uydurma "başka kayıt" (program dışından düzenleme).
_BASKA_KAYIT = "6f708192-a3b4-4c5d-8e6f-708192a3b4c5"

#: İçerik MAC'ine giren `Account` alanları — ALTIN LİSTE (sıra dahil; `satir_izi` modül başlığı).
#: Değişirse var olan satırların izi tutmaz: kümeyi değiştiren değişiklik `KAPALI` dahil BÜTÜN
#: satırların izini (önce eski hâlleriyle doğrulayıp) yeniden kurmalıdır; o adımın bugün yeri yoktur
#: (`satir_izi.HESAP_OZET_ALANLARI` yorumu; kullanıcı kararı bekler).
_ALTIN_LISTE = (
    "login_name",
    "role",
    "display_name",
    "status",
    "suspend_reason",
    "opened_at",
    "opened_by",
    "closed_at",
    "closed_by",
    "password_changed_at",
    "reset_at",
    "reset_by",
    "reset_kind",
    "reset_notice_pending",
    "last_login_at",
    "wrap_digest",
    "wrap_digest_pending",
    "seal",
)


# ============================================================ yardımcılar


def _son_seq() -> int:
    return int(AuditTrail.objects.order_by("-seq").values_list("seq", flat=True).first() or 0)


def _hesabin_son_kaydi(hesap_id: object) -> int:
    """Hesabın son içerik MAC'li iz satırının sırası (satırın eşleştiği kayıt)."""
    return int(
        AuditTrail.objects.filter(model="okul.Account", object_id=str(hesap_id))
        .exclude(record_mac="")
        .latest("seq")
        .seq
    )


def _ham(hesap_id: object) -> dict[str, Any]:
    """`okul_account` satırının BÜTÜN sütunları (ORM'siz, metin olarak): değişmezlik denetimi."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM okul_account WHERE id = %s", [str(hesap_id).replace("-", "")])
        satir = cursor.fetchone()
        adlar = [str(sutun[0]) for sutun in cursor.description]
    assert satir is not None
    return dict(zip(adlar, satir, strict=True))


_KOPYA_SAYACI = itertools.count(1)


def _kopyala(hesap_id: object) -> str:
    """Satırın o anki baytlarının "eski kopyası" (geçici tablo; türler ve baytlar aynen)."""
    tablo = f"kopya_{next(_KOPYA_SAYACI)}"
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TEMP TABLE {tablo} AS SELECT * FROM okul_account WHERE id = %s",  # noqa: S608
            [str(hesap_id).replace("-", "")],
        )
    return tablo


def _geri_sar(hesap_id: object, kopya: str) -> None:
    """Program DIŞINDAN satır geri sarma (SQLite tarayıcısı taklidi; kod gerekmez): satırın
    bütün sütunları eski kopyadakiyle değiştirilir — mühür ve özet dahil, ikisi de tutar."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM pragma_table_info('okul_account') WHERE name != 'id'")
        adlar = ", ".join(f'"{ad}"' for (ad,) in cursor.fetchall())
        cursor.execute(
            f"UPDATE okul_account SET ({adlar}) = (SELECT {adlar} FROM {kopya}) "  # noqa: S608
            "WHERE id = %s",
            [str(hesap_id).replace("-", "")],
        )


def _sarmal(hesap_id: object) -> dict[str, Any]:
    sarmal = app_password._find_wrap(durum(), hesap_id)
    assert sarmal is not None
    return dict(sarmal)


def _geri_koy(eski: dict[str, Any]) -> None:
    """Metin düzenleyici taklidi: aynı kimliğin sarmalını verilenle değiştirir (yoksa ekler)."""
    veri = durum()
    kalan = [h for h in veri["hesaplar"] if h["id"] != eski["id"]]
    veri["hesaplar"] = [*kalan, dict(eski)]
    durum_yaz(veri)


def _tetikleyicisiz(sql: str, params: list[Any]) -> None:
    """Program DIŞINDAN iz tablosu düzenlemesi: tetikleyiciler bu işlemde düşürülür."""
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_audittrail'"
        )
        tetikleyiciler = cursor.fetchall()
        for ad, _ in tetikleyiciler:
            cursor.execute(f'DROP TRIGGER "{ad}"')
        # Kısıtlar da kapatılır (kilitli kipte içerik MAC'i yasağı vb.; `iz_ortak.sahte_satir`).
        cursor.execute("PRAGMA ignore_check_constraints = ON")
        try:
            cursor.execute(sql, params)
        finally:
            cursor.execute("PRAGMA ignore_check_constraints = OFF")
        for _, tanim in tetikleyiciler:
            cursor.execute(tanim)


def _izi_tutar(hesap_id: object) -> bool:
    """Satırın izi, bellekteki DEK'le (ilk kurulumun kendi DEK'i), yoksa test DEK'iyle."""
    dek = crypto.active_key() or TEST_DEK
    return denetim_izi.hesap_izi_tutuyor(hesap_id, veri_anahtari=dek)


def _hepsi_izli() -> None:
    """Bütün `Account` satırları son iz kaydını tutar; kayıt bütünlüğü de aynı şeyi söyler."""
    kilitliydi = not crypto.is_unlocked()
    if kilitliydi:
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
    try:
        for kimlik in Account.objects.values_list("id", flat=True):
            assert _izi_tutar(kimlik), kimlik
            assert denetim_izi.kaydi_dogrula(Account, kimlik) is True, kimlik
    finally:
        if kilitliydi:
            crypto.unload_key()


def _tek_butunluk(hesap_id: object, son: int, alan: str = app_password.KAYIT_MAC_ALANI) -> None:
    """`son`'dan sonra yalnız `BUTUNLUK` satırı: hesabın kaydı, alanı `alan` (satırın izi
    `kayit_mac`, izdeki boşluk `iz_boslugu`; orkestratör maddesi C-4), `SISTEM`."""
    yeni = list(AuditTrail.objects.filter(seq__gt=son).order_by("seq"))
    assert [satir.action for satir in yeni] == [AuditAction.BUTUNLUK], yeni
    (satir,) = yeni
    assert (satir.model, satir.object_id, satir.changed_fields, satir.actor) == (
        "okul.Account",
        str(hesap_id),
        [alan],
        AuditActor.SISTEM,
    )


def _reddedilir(
    hata: pytest.ExceptionInfo[app_password.AccountRecordStale],
    ileti: str,
    *,
    neden: satir_izi.IzRetNedeni = satir_izi.IzRetNedeni.SATIR_IZI,
) -> None:
    """Satırın izinin reddi: kod, durum, ileti ve NEDEN (izdeki boşluk `AuditTrailGap`'tır; `satir_izi`
    "RET NEDENİ"). Neden karışırsa test düşer (satırın izi ile boşluk ayrı iletidir)."""
    assert isinstance(hata.value, app_password.AccountSealMismatch)
    assert not isinstance(hata.value, app_password.WrapDigestMismatch)
    assert (hata.value.code, hata.value.status_code) == ("hesap_muhru_tutmadi", 409)
    assert str(hata.value) == ileti
    assert hata.value.neden is neden
    assert isinstance(hata.value, app_password.AuditTrailGap) is neden.bosluk_mu
    assert hata.value.alan == (
        app_password.IZ_BOSLUGU_ALANI if neden.bosluk_mu else app_password.KAYIT_MAC_ALANI
    )


#: İz boşluğunun nedenleri (`satir_izi.IzRetNedeni`).
_SILME = satir_izi.IzRetNedeni.SILME
_TUR = satir_izi.IzRetNedeni.TUR
_KAYMA = satir_izi.IzRetNedeni.KAYMA


def _acik_muhasip() -> Account:
    """Açık (`ACIK`) uydurma muhasip; parolası `GECICI_PAROLA`."""
    return muhurle(hesap_ac(), status=AccountStatus.ACIK, password_changed_at=timezone.now())


def _ikinci_yonetici() -> Account:
    """Açık ikinci program yöneticisi (`yonetici-2`); parolası `GECICI_PAROLA`."""
    hesap = hesap_ac(AccountRole.YONETICI, tanitici="yonetici-2", ad="Örnek İkinci Yönetici")
    return muhurle(hesap, status=AccountStatus.ACIK, password_changed_at=timezone.now())


# ============================================================ senaryolar (kilitli biter)

#: Satır geri sarmanın üç senaryosu (görev metni): her biri (hesap kimliği, eski parola) döndürür;
#: program kilitlidir, satır eski kopyadan geri konmuştur, o günün sarmalı dosyadadır.
SENARYOLAR = ("sifirlama_sonrasi", "rol_dusurme", "kapanis")


def _senaryo(ad: str) -> tuple[str, str]:
    if ad == "sifirlama_sonrasi":
        # Senaryo 1: program yöneticisi muhasibin parolasını sıfırlar (geçici T) ve hemen
        # veritabanını kopyalar; muhasip T ile girip parolasını yeniler; satır kopyadan geri
        # sarılır, T'nin sarmalı arşivden (burada bellekten) geri konur.
        muhasip = _acik_muhasip()
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
        )
        kopya = _kopyala(muhasip.id)
        gecici = _sarmal(muhasip.id)
        app_password.lock()
        app_password.unlock(hesap_id=muhasip.id, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
        app_password.lock()
        _geri_sar(muhasip.id, kopya)
        _geri_koy(gecici)
        return str(muhasip.id), UCUNCU_PAROLA
    if ad == "rol_dusurme":
        # Rol hesap açıldıktan sonra değişmez; yetkinin düşmesi askı (görev bölümü) ya da
        # kapanıştır. İkinci program yöneticisi askıya alınır (F1c'nin servisi gibi, izli yazım);
        # satır askıdan önceki ACIK kopyasına geri sarılır — sarmal değişmemiştir.
        ikinci = _ikinci_yonetici()
        kopya = _kopyala(ikinci.id)
        muhurle(
            Account.objects.get(pk=ikinci.id),
            status=AccountStatus.ASKIDA,
            suspend_reason=SuspendReason.GOREV_BOLUMU,
        )
        app_password.lock()
        _geri_sar(ikinci.id, kopya)
        return str(ikinci.id), GECICI_PAROLA
    assert ad == "kapanis"
    # Kapanan hesap: sarmal dosyadan ve arşivlerden silinir (TK11); kapatılmadan önce saklanan
    # kopya geri konur, satır kapanıştan önceki ACIK kopyasına geri sarılır.
    muhasip = _acik_muhasip()
    kopya = _kopyala(muhasip.id)
    saklanan = _sarmal(muhasip.id)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    app_password.lock()
    _geri_sar(muhasip.id, kopya)
    _geri_koy(saklanan)
    return str(muhasip.id), GECICI_PAROLA


# ============================================================ altın liste ve ORM eşitliği


def test_icerik_macinin_alanlari_altin_listedir() -> None:
    """Kümeyi değiştiren değişiklik `KAPALI` dahil bütün satırların izini yeniden kurmalıdır
    (`satir_izi.HESAP_OZET_ALANLARI` yorumu)."""
    assert Account.IZ_OZET_ALANLARI == satir_izi.HESAP_OZET_ALANLARI == _ALTIN_LISTE


def test_sabitler_modelle_ayni() -> None:
    assert satir_izi.HESAP_MODELI == denetim_izi.model_etiketi(Account)
    assert satir_izi.AKTOR_SISTEM == AuditActor.SISTEM.value
    assert satir_izi.TUR_HESAP == AuditAction.HESAP.value
    assert satir_izi.KIP_ACIK == AuditKeyMode.ACIK.value
    assert satir_izi.IZ_ANAHTARI_BAYT == denetim_izi.IZ_ANAHTARI_BAYT
    sira = list(_ALTIN_LISTE)
    assert [sira.index(ad) for ad in satir_izi.ONARIM_ALANLARI] == sorted(
        sira.index(ad) for ad in satir_izi.ONARIM_ALANLARI
    )


@pytest.mark.parametrize("mikrosaniye", [0, 654321])
def test_orm_siz_okuyucu_orm_ile_ayni_alanlari_verir(mikrosaniye: int) -> None:
    """Ham sütun çevirisi ORM'in verdiğiyle BİREBİR: zamanlar (kesirli ve kesirsiz), yabancı
    anahtarlar (`opened_by`, `reset_by`), bildirim bayrağı, askı nedeni, şifreli ad; içerik MAC'i
    de aynı; çözülemeyen ad (düz metin) iki yolda aynı bozuk temsille girer."""
    an = datetime(2026, 11, 3, 9, 41, 7, mikrosaniye, tzinfo=UTC)
    muhasip = _acik_muhasip()
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id, temp_password=UCUNCU_PAROLA
    )
    muhurle(
        Account.objects.get(pk=muhasip.id),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.UYELIK_DUSTU,
        last_login_at=an,
        password_changed_at=an - timedelta(days=1),
    )
    hesap = Account.objects.get(pk=muhasip.id)
    assert hesap.opened_by_id is not None and hesap.reset_by_id is not None
    assert hesap.reset_notice_pending is True
    kimlik = str(hesap.id)

    def karsilastir() -> None:
        connection.ensure_connection()
        ham = satir_izi._hesap_satiri(connection.connection, kimlik)
        assert ham is not None
        orm_siz = satir_izi.hesap_ozet_alanlari(ham, TEST_DEK)
        orm = denetim_izi.anlik(Account.objects.get(pk=kimlik))
        assert orm_siz == {ad: orm[ad] for ad in _ALTIN_LISTE}
        assert kanonik.kodla(orm_siz) == kanonik.kodla({ad: orm[ad] for ad in _ALTIN_LISTE})
        assert kanonik.kayit_mac(
            crypto.record_summary_key(TEST_IA), "okul.Account", kimlik, orm_siz
        ) == denetim_izi.kayit_mac_hesapla(Account, kimlik)

    karsilastir()
    assert _izi_tutar(kimlik) and denetim_izi.kaydi_dogrula(Account, kimlik) is True
    ham_guncelle(kimlik, display_name="Düz Yazılmış Ad")  # program dışından düz metin
    karsilastir()
    assert not _izi_tutar(kimlik) and denetim_izi.kaydi_dogrula(Account, kimlik) is False


def test_satirin_izi_bicimsiz_degerde_hata_vermez_tutmaz() -> None:
    """Program dışından yazılmış biçimsiz değer (0/1 dışı bayrak, çözülemeyen zaman, metin
    sütununda ikili değer) denetimi istisnayla kesmez: satır tutmaz (fail-closed)."""
    muhasip = _acik_muhasip()
    for sutun, deger in (
        ("reset_notice_pending", 7),
        ("last_login_at", "dün öğleden sonra"),
        ("login_name", b"\xff\xfe"),
    ):
        once = _ham(muhasip.id)[sutun]
        ham_guncelle(muhasip.id, **{sutun: deger})
        assert _izi_tutar(muhasip.id) is False, sutun
        ham_guncelle(muhasip.id, **{sutun: once})
        assert _izi_tutar(muhasip.id) is True, sutun


# ============================================================ satır geri sarma: giriş


@pytest.mark.parametrize("senaryo", SENARYOLAR)
def test_satir_geri_sarma_girisi_acmaz(senaryo: str) -> None:
    """Kullanıcı kararı 03.11.2026: mühür ve özet tutar (geri sarma kod istemeden yapılır), ama
    satır son iz kaydını tutmaz — giriş açılmaz (409 `hesap_muhru_tutmadi`, mühür iletisi),
    `BUTUNLUK` satırı düşer (alan `kayit_mac`), hatalı deneme sayılmaz, satıra dokunulmaz."""
    hesap_id, parola = _senaryo(senaryo)
    satir = Account.objects.get(pk=hesap_id)
    # Geri sarma mühür ve özet denetiminden GEÇER: reddi yalnız satırın izi verir.
    assert satir.seal_matches(TEST_DEK)
    assert app_password.digest_matches(satir, app_password.wrap_digest(TEST_DEK, _sarmal(hesap_id)))
    assert satir.status == AccountStatus.ACIK or senaryo == "sifirlama_sonrasi"
    once = _ham(hesap_id)
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=hesap_id, password=parola, new_password=_SONRAKI_PAROLA)

    _reddedilir(hata, app_password._SEAL_MISMATCH_MESSAGE)
    assert OTURUM.hesap_id() is None and crypto.is_unlocked() is False
    _tek_butunluk(hesap_id, son)
    assert _ham(hesap_id) == once
    assert app_password.wrap_failure_state(hesap_id) == (0, False)
    # Yanlış parola yine yanlış parola sayılır (satırın izi parolanın yerini tutmaz).
    with pytest.raises(app_password.WrongPassword):
        app_password.unlock(hesap_id=hesap_id, password="Yanlis-Parola-1")


def test_satirin_izi_ozetten_ve_durumdan_once_denetlenir() -> None:
    """Sıra (`_open_account_for_login`): mühür → iz anahtarı → SATIRIN İZİ → özet → durum. Eski
    kopyadaki durum (askı) ya da eski kopyanın özeti kararı vermez: geri sarılmış satır her hâlde
    `AccountRecordStale` ve `kayit_mac` satırıdır (durum ve özet ancak güncel satırdan okunur)."""
    muhasip = muhurle(
        hesap_ac(),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.UYELIK_DUSTU,
        password_changed_at=timezone.now(),
    )
    askidaki = _kopyala(muhasip.id)
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    app_password.lock()
    _geri_sar(muhasip.id, askidaki)  # askıdaki kopya: durum reddi verirdi
    son = _son_seq()
    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    _tek_butunluk(muhasip.id, son)
    # Eski kopyanın özeti dosyadaki sarmalı da tutmasın: yine satırın izi (özet reddi değil).
    veri = durum()
    veri["hesaplar"] = [h for h in veri["hesaplar"] if h["id"] != str(muhasip.id)]
    durum_yaz(veri)
    app_password.write_account_wrap(
        data_key=TEST_DEK, hesap_id=muhasip.id, tanitici="muhasip", password=YENI_PAROLA
    )
    son = _son_seq()
    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=muhasip.id, password=YENI_PAROLA)
    _tek_butunluk(muhasip.id, son)


@pytest.mark.parametrize("islem", ["dogrulama", "degistirme", "kurtarma_yenileme"])
def test_oturum_acikken_geri_sarilan_satir_parola_islemini_gecmez(islem: str) -> None:
    """Oturum açıkken satır geri sarılırsa (yetkisi düşen program yöneticisi) parola doğrulaması,
    parola değiştirme ve kurtarma anahtarının yenilenmesi reddedilir; `BUTUNLUK` satırı düşer,
    satır, sarmal ve kurtarma bölümü değişmez."""
    ikinci = _ikinci_yonetici()
    kopya = _kopyala(ikinci.id)
    app_password.lock()
    app_password.unlock(hesap_id=ikinci.id, password=GECICI_PAROLA)
    with sistem_olarak():
        muhurle(
            Account.objects.get(pk=ikinci.id),
            status=AccountStatus.ASKIDA,
            suspend_reason=SuspendReason.GOREV_BOLUMU,
        )
    _geri_sar(ikinci.id, kopya)
    once, sarmal, kurtarma, son = (
        _ham(ikinci.id),
        _sarmal(ikinci.id),
        durum()["kurtarma"],
        _son_seq(),
    )

    with (
        yazar_olarak(Yazar(hesap_id=str(ikinci.id), rol=AccountRole.YONETICI)),
        pytest.raises(app_password.AccountRecordStale) as hata,
    ):
        if islem == "dogrulama":
            app_password.verify_password(hesap_id=ikinci.id, password=GECICI_PAROLA)
        elif islem == "degistirme":
            app_password.change_password(
                hesap_id=ikinci.id, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
            )
        else:
            app_password.renew_recovery_key(hesap_id=ikinci.id, password=GECICI_PAROLA)

    _reddedilir(hata, app_password.ISLEMDE_KAYIT_MESSAGE)
    _tek_butunluk(ikinci.id, son)
    assert (_ham(ikinci.id), _sarmal(ikinci.id), durum()["kurtarma"]) == (once, sarmal, kurtarma)


def test_geri_sarilan_yonetici_kurtarma_anahtariyla_acilmaz() -> None:
    """Kurtarma anahtarıyla açılış da satırın izini sorar: yetkisi düşürülüp geri sarılan program
    yöneticisinin parolası kurtarma anahtarıyla yenilenmez, sarmal yazılmaz, satır değişmez."""
    hesap_id, _parola = _senaryo("rol_dusurme")
    once, sarmal, son = _ham(hesap_id), _sarmal(hesap_id), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=hesap_id, new_password=_SONRAKI_PAROLA
        )

    _reddedilir(hata, app_password._SEAL_MISMATCH_MESSAGE)
    assert OTURUM.hesap_id() is None and crypto.is_unlocked() is False
    _tek_butunluk(hesap_id, son)
    assert (_ham(hesap_id), _sarmal(hesap_id)) == (once, sarmal)


# ============================================================ hesap işlemleri aklamaz


@pytest.mark.parametrize("islem", ["sifirlama", "kapama", "askidan_cikarma"])
def test_geri_sarilan_satiri_hesap_islemi_aklamaz(islem: str) -> None:
    """İşlem gören satırın izi tutmazsa sıfırlama, kapama ve askıdan çıkarma reddedilir (servisin
    iletisi; `BUTUNLUK` satırı): yeniden mühürleyip iz satırı yazmak geri sarmayı aklardı. Satır ve
    sarmal değişmez; giriş sonra da açılmaz."""
    hesap_id, parola = _senaryo("sifirlama_sonrasi")
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    once, sarmal, son = _ham(hesap_id), _sarmal(hesap_id), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        if islem == "sifirlama":
            hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=hesap_id, temp_password=_DORDUNCU_PAROLA
            )
        elif islem == "kapama":
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap_id)
        else:
            hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap_id)

    _reddedilir(hata, hesaplar._SEAL_MESSAGE)
    _tek_butunluk(hesap_id, son)
    assert (_ham(hesap_id), _sarmal(hesap_id)) == (once, sarmal)
    app_password.lock()
    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=hesap_id, password=parola, new_password=_SONRAKI_PAROLA)


def test_islemi_yapanin_geri_sarilan_satiri_hesap_islemi_acmaz() -> None:
    """İşlemi yapanın satırı da izini tutmalıdır (`hesaplar._actor`): oturum açıkken program
    yöneticisinin satırı eski kopyasına geri sarılırsa hesap açma reddedilir, satır yazılmaz."""
    kopya = _kopyala(TEST_HESAP_ID)
    app_password.change_password(
        hesap_id=TEST_HESAP_ID, current_password=TEST_PAROLA, new_password=YENI_PAROLA
    )
    _geri_sar(TEST_HESAP_ID, kopya)
    hesap_sayisi, son = Account.objects.count(), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        hesap_ac()

    _reddedilir(hata, hesaplar._SEAL_MESSAGE)
    _tek_butunluk(TEST_HESAP_ID, son)
    assert Account.objects.count() == hesap_sayisi


def test_iki_depo_karsilastirmasi_geri_sarilan_satira_dokunmaz() -> None:
    """İzi tutmayan satır mührü tutmayanların listesindedir (kart: kaydı program dışından
    değiştirilmiş görünen hesaplar); sarmalı silinse de parola yenilemeye çekilmez (satırı yeni bir
    iz satırıyla aklamaz)."""
    hesap_id, _parola = _senaryo("rol_dusurme")
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    fark = hesaplar.two_store_differences()
    assert fark.seal_mismatch == [hesap_id]
    assert hesap_id not in fark.digest_mismatch + fark.rows_without_wrap + fark.wraps_of_closed
    veri = durum()
    veri["hesaplar"] = [h for h in veri["hesaplar"] if h["id"] != hesap_id]
    durum_yaz(veri)
    once, son = _ham(hesap_id), _son_seq()

    fark = hesaplar.reconcile_two_stores()

    assert fark.seal_mismatch == [hesap_id] and fark.rows_without_wrap == []
    assert _ham(hesap_id) == once and _son_seq() == son


def test_iki_depo_karsilastirmasi_izi_bozuk_kapali_satirin_sarmalini_sildirmez() -> None:
    """Kapalı hesabın sarmalını yalnız mührü VE izi tutan `KAPALI` satır sildirir — iki depo
    karşılaştırmasında da (kilit açılışındaki temizliğin eşi bir alttaki testte): kapanmış hesabın
    son iz satırı program dışından bozulur ve sarmalı geri konur. Satır "kaydı program dışından
    değiştirilmiş görünen hesaplar"dadır (`seal_mismatch`), silinebilir sarmallarda değildir;
    program yöneticisinin onayı da sarmalı sildiremez: ret öteki hesap işlemlerindeki gibi 409 ve
    tek `BUTUNLUK` satırıdır (alan `kayit_mac`; orkestratör maddesi F-1, son sınama bulgusu)."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    sarmal = _sarmal(kimlik)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)
    _geri_koy(sarmal)
    son_kayit = _hesabin_son_kaydi(kimlik)
    _tetikleyicisiz(
        "UPDATE okul_audittrail SET record_mac = %s WHERE seq = %s", ["0" * 64, son_kayit]
    )

    fark = hesaplar.two_store_differences()

    assert kimlik in fark.seal_mismatch
    assert kimlik not in fark.wraps_of_closed and kimlik not in fark.removable_wraps
    son = _son_seq()
    with pytest.raises(app_password.AccountRecordStale) as hata:
        hesaplar.remove_orphan_wraps(by_hesap_id=TEST_HESAP_ID, hesap_idler=[kimlik])
    _reddedilir(hata, app_password.ISLEMDE_KAYIT_MESSAGE)
    _tek_butunluk(kimlik, son)
    assert app_password._find_wrap(durum(), kimlik) is not None


def test_geri_sarilan_kapali_satir_sarmal_sildirmez() -> None:
    """Kapalı hesap sarmalının temizliği yalnız mührü VE izi tutan `KAPALI` satır için koşar."""
    muhasip = _acik_muhasip()
    sarmal = _sarmal(muhasip.id)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=muhasip.id)
    kapali = _ham(muhasip.id)
    # Hayali: kapanmış satırın izi program dışından bozulmuş (izi tutmuyor) ve sarmal geri konmuş.
    _geri_koy(sarmal)
    son = _son_seq()
    _tetikleyicisiz(
        "UPDATE okul_audittrail SET record_mac = %s WHERE seq = %s",
        ["0" * 64, int(AuditTrail.objects.filter(object_id=str(muhasip.id)).latest("seq").seq)],
    )
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert app_password._find_wrap(durum(), muhasip.id) is not None
    assert _ham(muhasip.id) == kapali and _son_seq() > son


# ============================================================ izin düzenlenmesi fail-open değildir


def _geri_sarilmis_muhasip() -> tuple[str, int]:
    """Muhasip açılır, sonra askıya alınır (izli yazım R); satır askıdan önceki kopyasına geri
    sarılır. (kimlik, R'nin sırası) döner; program kilitlidir."""
    muhasip = _acik_muhasip()
    kopya = _kopyala(muhasip.id)
    muhurle(
        Account.objects.get(pk=muhasip.id),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.UYELIK_DUSTU,
    )
    r_seq = _son_seq()
    app_password.lock()
    _geri_sar(muhasip.id, kopya)
    return str(muhasip.id), r_seq


@pytest.mark.parametrize(
    "duzenleme",
    [
        "record_mac_bosaltma",
        "record_mac_eski_ia_ile",
        "kip_kilitli",
        "hesabin_butun_satirlari_silinir",
        "sahte_satir_eklenir",
        "changed_fields_bicimsiz",
        "at_bicimsiz",
    ],
)
def test_iz_duzenlemesi_denetimi_acmaz(duzenleme: str) -> None:
    """Geri sarmayı gizlemek için hesabın yeni iz satırı (R) düzenlenir: `record_mac` boşaltılır
    ya da başka bir iz anahtarıyla (eski İA) eski hâlin içerik MAC'iyle değiştirilir, kipi
    değiştirilir, hesabın bütün iz satırları silinir, sona sahte (mühürsüz) bir satır eklenir ya da
    R'ye çevrilemeyen bir değer yazılır (`changed_fields` JSON değil, `at` zaman değil; SQLite
    tarayıcısıyla, kod gerekmez). Hiçbiri denetimi daha eski bir satıra kaydırıp girişi açmaz: okunan
    her satırın kendi zincir MAC'i doğrulanır, biçimsiz satır atlanmaz (fail-closed), içerik MAC'li
    satır hiç yoksa satır tutmaz."""
    hesap_id, r_seq = _geri_sarilmis_muhasip()
    if duzenleme == "changed_fields_bicimsiz":
        _tetikleyicisiz("UPDATE okul_audittrail SET changed_fields = 'x' WHERE seq = %s", [r_seq])
    elif duzenleme == "at_bicimsiz":
        _tetikleyicisiz("UPDATE okul_audittrail SET \"at\" = 'dun aksam' WHERE seq = %s", [r_seq])
    elif duzenleme == "record_mac_bosaltma":
        _tetikleyicisiz("UPDATE okul_audittrail SET record_mac = '' WHERE seq = %s", [r_seq])
    elif duzenleme == "record_mac_eski_ia_ile":
        # En güçlü saldırgan: DEK yenilemesinden (F4) kalan ESKİ bir iz anahtarını biliyor (geçerli
        # ilk sırası daha küçük, emekli). Yeni satır R'yi o anahtarla yeniden mühürler: `key_ref`'i
        # ona, `record_mac`'i geri sarılmış hâlin o anahtarla içerik MAC'ine çevirir ve R'nin
        # zincir MAC'ini o anahtarla yeniden hesaplar (R'nin kendi MAC'i böylece tutar). R'nin
        # sırasında yürürlükteki anahtar o değildir: satır tutmaz.
        eski_ia = bytes(range(100, 132))
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
        try:
            anahtar = AuditKey.objects.create(
                key=base64.b64encode(eski_ia).decode("ascii"),
                valid_from_seq=0,
                retired_at=timezone.now(),
            )
            connection.ensure_connection()
            ham = satir_izi._hesap_satiri(connection.connection, hesap_id)
            assert ham is not None
            eski_mac = kanonik.kayit_mac(
                crypto.record_summary_key(eski_ia),
                "okul.Account",
                hesap_id,
                satir_izi.hesap_ozet_alanlari(ham, TEST_DEK),
            )
            satir = next(denetim_izi.satirlari_oku(AuditTrail.objects.filter(seq=r_seq)))
            satir.key_ref, satir.record_mac = str(anahtar.pk), eski_mac
            yeni_mac = kanonik.iz_mac(
                crypto.audit_chain_key(eski_ia), denetim_izi.satir_alanlari(satir), satir.prev_mac
            )
        finally:
            crypto.unload_key()
        _tetikleyicisiz(
            "UPDATE okul_audittrail SET key_ref = %s, record_mac = %s, mac = %s WHERE seq = %s",
            [str(anahtar.pk), eski_mac, yeni_mac, r_seq],
        )
    elif duzenleme == "kip_kilitli":
        _tetikleyicisiz("UPDATE okul_audittrail SET key_mode = 'KILITLI' WHERE seq = %s", [r_seq])
    elif duzenleme == "hesabin_butun_satirlari_silinir":
        _tetikleyicisiz(
            "DELETE FROM okul_audittrail WHERE model = 'okul.Account' AND object_id = %s",
            [hesap_id],
        )
    else:
        sahte_satir(
            action="GIRIS",
            actor="HESAP",
            account=hesap_id,
            role="muhasip",
            model="okul.Account",
            object_id=hesap_id,
        )
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=hesap_id, password=GECICI_PAROLA)

    _tek_butunluk(hesap_id, son)


def test_son_iz_satirini_silmek_tek_basina_girisi_kapatir() -> None:
    """Satır geri sarılmadan yalnız son iz satırı silinirse satır (yeni hâli) daha eski satırı
    tutmaz: giriş açılmaz (silme denetimi gevşetmez)."""
    muhasip = _acik_muhasip()
    muhurle(Account.objects.get(pk=muhasip.id), password_changed_at=timezone.now())
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [_son_seq()])
    dek = crypto.active_key() or TEST_DEK
    # Zincir başı silindi: ondan sonra izde boşluk görünmez, neden satırın izidir ("RET NEDENİ").
    karar = denetim_izi.hesap_izi_karari(muhasip.id, veri_anahtari=dek)
    assert karar == satir_izi.IzKarari(None, satir_izi.IzRetNedeni.SATIR_IZI)
    app_password.lock()
    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=muhasip.id, password=GECICI_PAROLA)
    _reddedilir(hata, app_password._SEAL_MISMATCH_MESSAGE)


def _kendi_son_kaydi_ortadan_silinmis_muhasip() -> str:
    """Açık muhasip; meşru bir yazım muhasibin KENDİ son içerik MAC'li iz satırını (S2) yazar,
    ardından ilgisiz satırlar yazılır ve S2 zincirin ORTASINDAN silinir (SQLite tarayıcısı taklidi;
    hesap satırına dokunulmaz). Muhasibin kimliğini döndürür."""
    kimlik = str(_acik_muhasip().id)
    muhurle(Account.objects.get(pk=kimlik), password_changed_at=timezone.now())
    s2 = _hesabin_son_kaydi(kimlik)
    _dolgu(2)
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [s2])
    return kimlik


def test_kendi_son_kaydi_ortadan_silinen_hesabin_girisi_iz_boslugudur() -> None:
    """Orkestratör maddesi C-4 (bağımsız denetim bulgusu): hesabın KENDİ son içerik MAC'li iz
    satırı zincirin ortasından silinir, satıra dokunulmaz. Yürüyüş bir önceki kendi satırına iner;
    onun içerik MAC'i bugünkü alanları tutmaz — ama değişen hesap kaydı değil denetim izidir (o
    satırdan sonra izde boşluk var): neden `SILME`, ileti iz boşluğunun, `BUTUNLUK` alanı
    `iz_boslugu` (`satir_izi` "RET NEDENİ"). Karar aynıdır: ret, hatalı deneme sayılmaz, satır
    değişmez. Kuyruk kesmede (zincir başı silinir) neden satırın izi kalır (bir önceki test)."""
    kimlik = _kendi_son_kaydi_ortadan_silinmis_muhasip()
    dek = crypto.active_key() or TEST_DEK
    assert denetim_izi.hesap_izi_karari(kimlik, veri_anahtari=dek) == satir_izi.IzKarari(
        None, _SILME
    )
    app_password.lock()
    iz_durumu.yol().unlink(missing_ok=True)
    once, son = _ham(kimlik), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=_SILME)
    _tek_butunluk(kimlik, son, app_password.IZ_BOSLUGU_ALANI)
    assert _ham(kimlik) == once and app_password.wrap_failure_state(kimlik) == (0, False)


def test_kendi_son_kaydi_ortadan_silinen_hesabin_islemi_iz_boslugudur() -> None:
    """Aynı silme, program yöneticisinin oturumu açıkken (onun kaydı boşluktan SONRA tazelenir):
    muhasibin parolasının sıfırlanması iz boşluğu iletisiyle reddedilir (`hesaplar._GAP_MESSAGE`,
    `BUTUNLUK` alanı `iz_boslugu`), Kullanıcılar satırı da boşluğun nedenini söyler."""
    kimlik = _kendi_son_kaydi_ortadan_silinmis_muhasip()
    muhurle(Account.objects.get(pk=TEST_HESAP_ID), password_changed_at=timezone.now())
    once, son = _ham(kimlik), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=_DORDUNCU_PAROLA
        )

    _reddedilir(hata, hesaplar._GAP_MESSAGE, neden=_SILME)
    _tek_butunluk(kimlik, son, app_password.IZ_BOSLUGU_ALANI)
    assert _ham(kimlik) == once
    satir = hesaplar.kullanici_satiri(kimlik)
    assert satir is not None
    assert satir["eylemler"]["parola_sifirla"]["neden"] == hesaplar._ROW_GAP_MESSAGE


def test_bilinen_sinir_kuyruk_satirla_birlikte_kesilirse_giris_acilir_capa_gosterir() -> None:
    """KALAN RİSK (`app_password` "KALAN RİSKLER" (b); `satir_izi` "KAPSAMIN SINIRI"): satır geri
    sarılır VE ondan sonraki iz satırları (kuyruk) silinirse satır kopyanın son iz satırını tutar,
    giriş açılır. Kilit açılışının çapa denetimi kuyruğun kesildiğini `BUTUNLUK` bulgusu olarak
    gösterir (`kuyruk_kesik`). Test riski sabitler: kapanırsa ret testine döner."""
    hesap_id, r_seq = _geri_sarilmis_muhasip()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"  # çapa R'den sonraki KILIT satırında
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [r_seq])

    app_password.unlock(hesap_id=hesap_id, password=GECICI_PAROLA)

    assert OTURUM.hesap_id() == hesap_id
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert "kuyruk_kesik" in bulgu.values["bulgular"][1]


def test_ara_satir_silinirse_giris_acilmaz_pencere_icinde() -> None:
    """Kullanıcı kararı 03.11.2026 "Boşluğu engelle" (b4'te kalan riskti): satır geri sarılır ve
    hesabın yeni iz satırı (R) zincirin ORTASINDAN silinir. Satır daha eski satırı tutar ama ondan
    sonra izde boşluk vardır (`satir_izi` "İZ BOŞLUĞU" (a)): giriş açılmaz, ret izdeki boşluğundur
    (`AuditTrailGap`, iz boşluğu iletisi, `BUTUNLUK` alanı `iz_boslugu`; orkestratör maddesi C-4),
    hatalı deneme sayılmaz, satır değişmez. Çapa da yoktur: kuyruk ya da çapa bulgusu değil,
    boşluk reddeder."""
    hesap_id, r_seq = _geri_sarilmis_muhasip()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    app_password.lock()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [r_seq])
    iz_durumu.yol().unlink(missing_ok=True)
    once, son = _ham(hesap_id), _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=hesap_id, password=GECICI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=_SILME)
    _tek_butunluk(hesap_id, son, app_password.IZ_BOSLUGU_ALANI)
    assert _ham(hesap_id) == once and app_password.wrap_failure_state(hesap_id) == (0, False)
    # Program yöneticisinin son kaydı (girişi) boşluktan YENİDİR: o girer, doğrulama boşluğu
    # bulgu olarak gösterir (bedel yalnız son kaydı boşluktan eski hesaplaradır).
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert {"sira_boslugu", "zincir_kopuk"} <= set(bulgu.values["bulgular"][1])
    assert r_seq + 1 in bulgu.values["bulgu_satirlari"][1]  # pencere boşluğun yerini gösterir


def test_ara_satir_pencere_disinda_silinirse_de_giris_acilmaz() -> None:
    """Kullanıcı kararı 03.11.2026 "Boşluğu engelle" (b4'te bağımsız denetimin bulgusu, kalan
    riskti): hesabın yeni iz satırı (R) silinir ve ondan sonra 200'den çok satır yazılmıştır —
    kilit açılışının 200 satırlık penceresinin ve çapanın göremediği yer. Boşluk denetimi pencereye
    bağlı değildir (S'den zincir başına sayım): giriş açılmaz."""
    hesap_id, r_seq = _geri_sarilmis_muhasip()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    for _ in range(210):  # programın meşru, izli olayları
        with sistem_olarak(), transaction.atomic():
            denetim_izi.olay(AuditAction.BUTUNLUK, model="okul.Deneme", object_id="x")
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"  # çapa zincir başında
    son = _son_seq()
    assert son - r_seq > iz_dogrulama.SON_SATIR
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [r_seq])
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=hesap_id, password=GECICI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=_SILME)
    assert OTURUM.hesap_id() is None
    _tek_butunluk(hesap_id, son, app_password.IZ_BOSLUGU_ALANI)


# ============================================================ iz boşluğu (kullanıcı kararı "Boşluğu engelle")

#: Geri sarmayı gizlemek için hesabın yeni iz satırlarına yapılan program dışı değişiklikler
#: (`satir_izi` "İZ BOŞLUĞU"): satırlar silinir; silinir ve sonrakiler aşağı kaydırılır (yeniden
#: numaralama); eşleşen satırın gerisine REAL sıralarla taşınır ve boşlukları ilgisiz satırlarla
#: doldurulur; sıraları BLOB'a çevrilir.
DEGISIMLER = ("silme", "yeniden_numaralama", "real_tasima", "blob_sira")
#: Her değişikliğin ret nedeni (`satir_izi` "RET NEDENİ"; orkestratör maddesi C-4): silme (a),
#: kaydırma (c), REAL sıra ve BLOB sıra (b).
DEGISIMIN_NEDENI = {
    "silme": satir_izi.IzRetNedeni.SILME,
    "yeniden_numaralama": satir_izi.IzRetNedeni.KAYMA,
    "real_tasima": satir_izi.IzRetNedeni.TUR,
    "blob_sira": satir_izi.IzRetNedeni.TUR,
}
#: Program dışı değişikliklerin dolgu satırları (ilgisiz, programın meşru yazdığı satırlar).
_DOLGU_ADEDI = 12


def _dolgu(adet: int = _DOLGU_ADEDI) -> list[int]:
    """Programın meşru yazdığı, hesaplarla ilgisiz `adet` açık kip satırı; sıralarını döndürür."""
    sira: list[int] = []
    for _ in range(adet):
        with sistem_olarak(), transaction.atomic():
            satir = denetim_izi.olay(AuditAction.HESAP, model="okul.Deneme", object_id="dolgu")
        sira.append(int(satir.seq))
    return sira


def _yeni_satirlari(hesap_id: object, sira: int) -> list[int]:
    """Hesabın `sira`'dan SONRAKİ iz satırlarının sıraları (geri sarmayı gizlemek için oynanır)."""
    return sorted(
        int(s)
        for s in AuditTrail.objects.filter(
            model="okul.Account", object_id=str(hesap_id), seq__gt=sira
        ).values_list("seq", flat=True)
    )


def _sira_tasi(eski: object, yeni: object) -> None:
    _tetikleyicisiz("UPDATE okul_audittrail SET seq = %s WHERE seq = %s", [yeni, eski])


def _izi_degistir(hesap_id: object, sira: int, degisim: str, dolgu: list[int]) -> None:
    """SQLite tarayıcısı taklidi (kod gerekmez): hesabın `sira`'dan sonraki iz satırları yürüyüşten
    çıkarılır (`DEGISIMLER`; `tamsayi_takasi` bilinen sınırdır). `dolgu` eşleşen satırdan ÖNCE
    yazılmış ilgisiz satırlardır (boşlukları doldurmak için)."""
    yeniler = _yeni_satirlari(hesap_id, sira)
    assert yeniler, "hesabın eşleşen satırdan sonra iz satırı olmalı"
    if degisim in ("silme", "yeniden_numaralama"):
        for seq in yeniler:
            _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [seq])
        if degisim == "yeniden_numaralama":
            # Artan sırayla: her satır bir alttaki boş yere iner (birincil anahtar çakışmaz).
            kalan = sorted(
                int(s)
                for s in AuditTrail.objects.filter(seq__gt=sira).values_list("seq", flat=True)
            )
            for yeni, eski in enumerate(kalan, start=sira + 1):
                if eski != yeni:
                    _sira_tasi(eski, yeni)
    elif degisim == "real_tasima":
        assert len(yeniler) <= len(dolgu)
        for i, seq in enumerate(yeniler):
            _sira_tasi(seq, sira - 0.5 - i / 1000)  # eşleşen satırın gerisi (REAL)
        for bosluk, eski in zip(yeniler, dolgu, strict=False):
            _sira_tasi(eski, bosluk)  # boşluklar ilgisiz satırlarla dolar: sayım tutar
    elif degisim == "tamsayi_takasi":
        assert len(yeniler) <= len(dolgu)
        for bosluk, eski in zip(yeniler, dolgu, strict=False):
            _sira_tasi(bosluk, -1)
            _sira_tasi(eski, bosluk)
            _sira_tasi(-1, eski)
    else:
        assert degisim == "blob_sira"
        for seq in yeniler:
            _tetikleyicisiz(
                "UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [seq]
            )


def _butunluk_sayisi() -> int:
    return AuditTrail.objects.filter(action=AuditAction.BUTUNLUK).count()


def _senaryo1_degistirilmis(degisim: str) -> tuple[str, int, int]:
    """Senaryo 1'in geri sarması + izin değiştirilmesi; program kilitlidir, T'nin sarmalı
    dosyadadır. (muhasip kimliği, eşleşen satırın sırası S, değişiklikten sonraki BUTUNLUK
    sayısı) döner. Dolgu satırları S'den önce yazılır."""
    dolgu = _dolgu()
    kimlik, sifirlama, kopya, gecici = _sifirlanmis_muhasip()
    app_password.lock()
    _geri_sar(kimlik, kopya)
    _geri_koy(gecici)
    _izi_degistir(kimlik, sifirlama, degisim, dolgu)
    return kimlik, sifirlama, _butunluk_sayisi()


def _boslukta_butunluk(
    hesap_id: str, degisim: str, sayi: int, caplog: pytest.LogCaptureFixture
) -> None:
    """Reddin `BUTUNLUK` satırı (alan `iz_boslugu`; orkestratör maddesi C-4); BLOB sıralı zincir
    başında yazıcı yazmaz (O-3, Türkçe `IzYazilamadi`): olay günlüğe düşer."""
    if degisim == "blob_sira":
        assert _butunluk_sayisi() == sayi
        assert "Hesap kaydının tutmadığı denetim izine yazılamadı." in caplog.text
        return
    satir = AuditTrail.objects.filter(action=AuditAction.BUTUNLUK).latest("seq")
    assert _butunluk_sayisi() == sayi + 1
    assert (satir.object_id, satir.changed_fields, satir.actor) == (
        hesap_id,
        [app_password.IZ_BOSLUGU_ALANI],
        AuditActor.SISTEM,
    )


@pytest.mark.parametrize("degisim", DEGISIMLER)
def test_iz_boslugu_girisi_acmaz(degisim: str, caplog: pytest.LogCaptureFixture) -> None:
    """Kullanıcı kararı 03.11.2026 "Boşluğu engelle": Senaryo 1'in geri sarmasıyla birlikte
    muhasibin sıfırlamadan sonraki iz satırları silinir, silinip sonrakiler aşağı kaydırılır,
    eşleşen satırın gerisine REAL sıralarla taşınır (boşlukları ilgisiz satırlarla doldurulur) ya
    da sıraları BLOB'a çevrilir. Yürüyüş eski satırı en yeni sanardı; izde boşluk vardır: giriş
    açılmaz (`AuditTrailGap`, iz boşluğu iletisi, neden değişikliğin türü; orkestratör maddesi C-4),
    `BUTUNLUK` satırı (`iz_boslugu`), sayaç ve satır değişmez, T'nin sarmalı yerinde kalır."""
    kimlik, _sira, sayi = _senaryo1_degistirilmis(degisim)
    once, sarmal = _ham(kimlik), _sarmal(kimlik)

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=DEGISIMIN_NEDENI[degisim])
    assert OTURUM.hesap_id() is None and crypto.is_unlocked() is False
    _boslukta_butunluk(kimlik, degisim, sayi, caplog)
    assert (_ham(kimlik), _sarmal(kimlik)) == (once, sarmal)
    assert app_password.wrap_failure_state(kimlik) == (0, False)


@pytest.mark.parametrize("degisim", DEGISIMLER)
def test_iz_boslugu_hesap_islemini_acmaz(degisim: str, caplog: pytest.LogCaptureFixture) -> None:
    """Aynı değişiklik program yöneticisinin oturumu açıkken yapılır: muhasibin parolasının
    sıfırlanması (hesap servisi) reddedilir — işlem gören ya da (kaydırmada son kaydı da kayan)
    işlemi yapan satırın izi tutmaz; satır ve sarmal değişmez."""
    dolgu = _dolgu()
    kimlik, sifirlama, kopya, gecici = _sifirlanmis_muhasip()
    _geri_sar(kimlik, kopya)
    _geri_koy(gecici)
    _izi_degistir(kimlik, sifirlama, degisim, dolgu)
    once, sarmal = _ham(kimlik), _sarmal(kimlik)

    with pytest.raises(app_password.AccountRecordStale) as hata:
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=_DORDUNCU_PAROLA
        )

    # Hesap servisinin iz boşluğu iletisi (mühür iletisinin kalıbı; orkestratör maddesi C-4).
    _reddedilir(hata, hesaplar._GAP_MESSAGE, neden=DEGISIMIN_NEDENI[degisim])
    assert (_ham(kimlik), _sarmal(kimlik)) == (once, sarmal)
    if degisim == "blob_sira":
        assert "Hesap kaydının tutmadığı denetim izine yazılamadı." in caplog.text


@pytest.mark.parametrize("degisim", DEGISIMLER)
def test_iz_boslugu_oturumdaki_parola_ve_kurtarma_yolunu_acmaz(degisim: str) -> None:
    """Yetkisi düşürülen ikinci program yöneticisi (oturumu açıkken askıya alınır, satırı askıdan
    önceki kopyasına geri sarılır, askı ve giriş satırları izden çıkarılır): oturumdaki parola
    doğrulaması ve — kilitlendikten sonra — kurtarma anahtarıyla açılış reddedilir; satır ve
    sarmal değişmez."""
    dolgu = _dolgu()
    ikinci = _ikinci_yonetici()
    kimlik = str(ikinci.id)
    sira = _hesabin_son_kaydi(kimlik)
    kopya = _kopyala(kimlik)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)
    with sistem_olarak():
        muhurle(
            Account.objects.get(pk=kimlik),
            status=AccountStatus.ASKIDA,
            suspend_reason=SuspendReason.GOREV_BOLUMU,
        )
    _dolgu(2)  # askıdan sonra da ilgisiz satırlar (silme kuyruk kesmesi olmasın)
    _geri_sar(kimlik, kopya)
    _izi_degistir(kimlik, sira, degisim, dolgu)
    once, sarmal = _ham(kimlik), _sarmal(kimlik)

    with (
        yazar_olarak(Yazar(hesap_id=kimlik, rol=AccountRole.YONETICI)),
        pytest.raises(app_password.AccountRecordStale) as hata,
    ):
        app_password.verify_password(hesap_id=kimlik, password=GECICI_PAROLA)
    _reddedilir(hata, app_password.ISLEMDE_BOSLUK_MESSAGE, neden=DEGISIMIN_NEDENI[degisim])

    app_password.lock()
    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=kimlik, new_password=_SONRAKI_PAROLA
        )
    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=DEGISIMIN_NEDENI[degisim])
    assert OTURUM.hesap_id() is None
    assert (_ham(kimlik), _sarmal(kimlik)) == (once, sarmal)


def test_bilinen_sinir_tamsayi_takasi_girisi_acar_pencere_gosterir() -> None:
    """KALAN RİSK (kullanıcı kararı 03.11.2026: girişte görünmeyebilir; `satir_izi` "KAPSAMIN
    SINIRI"): muhasibin sıfırlamadan sonraki iz satırları, eşleşen satırdan önce yazılmış ilgisiz
    satırlarla TAMSAYI sıralarıyla yer değiştirir. Boşluk yoktur, bütün sıralar tamsayıdır,
    dayanak satırı kaymamıştır: geri sarılmış satır girer. Taşınan satırların kendi MAC'i bozulur:
    kilit açılışının 200 satırlık penceresindeyse `BUTUNLUK` bulgusu olur (dışındaysa yalnız
    Denetleme Kurulu modülünün tam zincir denetimi gösterir). Test riski sabitler."""
    kimlik, _sira, _sayi = _senaryo1_degistirilmis("tamsayi_takasi")

    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)

    assert OTURUM.hesap_id() == kimlik  # kalan risk
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert "mac_tutmadi" in bulgu.values["bulgular"][1]


def test_bilinen_sinir_dayanagi_bozulan_kaydirma_girisi_acar_pencere_gosterir() -> None:
    """KALAN RİSK (dayanak denetimi FAIL-CLOSED değildir; `satir_izi` "İZ BOŞLUĞU" (c), "KAPSAMIN
    SINIRI"; bağımsız denetim sondası P1): kaydırmaya (yeniden numaralama) ek olarak dayanak
    satırının tek bir hücresi (`label`) program dışından değiştirilir. Dayanağın MAC'i hiçbir
    sırada tutmaz: kayma işareti yoktur, geri sarılmış satır girer. Kaydırılan satırların kendi
    MAC'i bozuktur: 200 satırlık pencerede `BUTUNLUK` bulgusu olur. Test riski sabitler (hangi
    yolun kapanacağı kullanıcı kararıdır); kapanırsa ret testine döner."""
    kimlik, sira, _sayi = _senaryo1_degistirilmis("yeniden_numaralama")
    dayanak = (
        AuditTrail.objects.filter(seq__gt=sira, key_mode=AuditKeyMode.ACIK)
        .exclude(action=AuditAction.BUTUNLUK)
        .order_by("-seq")
        .values_list("seq", flat=True)
        .first()
    )
    assert dayanak is not None
    _tetikleyicisiz("UPDATE okul_audittrail SET label = 'x' WHERE seq = %s", [dayanak])

    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)

    assert OTURUM.hesap_id() == kimlik  # kalan risk
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert "mac_tutmadi" in bulgu.values["bulgular"][1]


def test_ilgisiz_satirin_silinmesi_son_kaydi_eski_hesaplari_reddeder() -> None:
    """Kabul edilen bedel (kullanıcı kararı 03.11.2026): izden İLGİSİZ tek bir satır silinmişse
    (hesap satırı geri sarılmamış olsa da) son kaydı o satırdan ESKİ her hesap reddedilir; son
    kaydı silinen satırdan YENİ olan girer. Çıkış (kurtarma anahtarıyla değişiklikten önceki
    yedeğin geri yüklenmesi) `test_iz_boslugu_cikisi_kurtarma_anahtariyla_eski_yedektir`'te."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    dolgu = _dolgu(3)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)  # yöneticinin kaydı yenilenir
    app_password.lock()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])

    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)

    assert app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA) is not None


def test_kuyruk_kesme_girisi_engellemez_capa_gosterir() -> None:
    """Orkestratör kararı O-2: en yeni satırların (kuyruğun) silinmesi boşluk bırakmaz, yeni zincir
    başı meşru ve MAC'i tutan bir satırdır — giriş AÇILIR, çapa `kuyruk_kesik` kartını verir. Ardından
    program açılışta kilitli kipte satır yazsa da (tohumu veritabanında olmayan çapadan; günlük
    yedeğin satırı) dayanak denetimi yanlış alarm vermez."""
    _dolgu(3)
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    capa = _son_seq()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq >= %s", [capa - 1])
    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-03.odbak"]) == 1

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    assert OTURUM.hesap_id() == TEST_HESAP_ID
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert "kuyruk_kesik" in bulgu.values["bulgular"][1]


def test_dayanak_ilk_reddin_butunluk_satiriyla_ortulmez() -> None:
    """Yalnız zincir başını doğrulamak yetmezdi: reddedilen her giriş başa (açık kipte) bir
    `BUTUNLUK` satırı ekler, program açılışta günlük yedeğin kilitli satırını ekler. Kaydırmadan
    sonra eklenen bu satırlar dayanak sayılmaz (programın giriş olmadan yazdığı satırlar): ikinci,
    üçüncü deneme de reddedilir ("iki kez dene" yolu yoktur)."""
    kimlik, _sira, _sayi = _senaryo1_degistirilmis("yeniden_numaralama")
    for _ in range(2):
        with pytest.raises(app_password.AccountRecordStale):
            app_password.unlock(
                hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA
            )
    # Program açılır: günlük yedeğin kilitli satırı başa yazılır (kimse girmeden).
    assert masaustu_kanca.yedek_olaylarini_yaz(alinan=["gunluk-2026-11-03.odbak"]) == 1
    bas = AuditTrail.objects.order_by("-seq").first()
    assert bas is not None and bas.key_mode == AuditKeyMode.KILITLI

    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)


def test_dayanak_bozuksa_giris_engellenmez() -> None:
    """Dayanak denetimi FAIL-CLOSED DEĞİLDİR (`satir_izi` "İZ BOŞLUĞU" (c)): zincirin başına
    program dışından eklenmiş, MAC'i hiçbir sırada tutmayan açık kip satırı (kayma işareti değil)
    girişi kapatmaz; kilit açılışının doğrulaması onu bulgu olarak gösterir (altın kural 3)."""
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    gercek = AuditTrail.objects.order_by("-seq").first()
    assert gercek is not None
    sahte_satir(
        action="GIRIS",
        actor="HESAP",
        account=TEST_HESAP_ID,
        role="yonetici",
        model="okul.Account",
        object_id=_BASKA_KAYIT,
        key_mode="ACIK",
        key_ref=gercek.key_ref,
    )
    app_password.lock()  # `KILIT` yazmaz: sahte satır zincir başında, dayanak odur

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    assert OTURUM.hesap_id() == TEST_HESAP_ID
    bulgu = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, model=denetim_izi.IZ_DOGRULAMASI
    ).latest("seq")
    assert "mac_tutmadi" in bulgu.values["bulgular"][1]


#: Program dışından `okul_auditkey`'e eklenen sahte, emekli, çözülemeyen anahtar satırı (tek
#: INSERT, kod gerekmez); geçerli ilk sırası verilir.
_SAHTE_EMEKLI_ANAHTAR = (
    'INSERT INTO okul_auditkey (id, "key", valid_from_seq, created_at, retired_at) '
    "VALUES (99, 'x', %s, '2026-11-03 08:00:00', '2026-11-03 08:00:00')"
)


def test_sahte_emekli_anahtar_kaymayi_ortmez() -> None:
    """Bağımsız denetim bulgusu (b5): kaydırmayla (yeniden numaralama) birlikte, İLK denemeden önce
    iz anahtarı tablosuna sahte, emekli bir satır (geçerli ilk sırası S+1) eklenir. Yürürlük
    kuralıyla çözülseydi dayanağın sırası ve `seq + d`'lerin hepsi o çözülemeyen anahtara bağlanır,
    kayma araması anahtarsız kalır, giriş açılırdı (hesabın kendi satırları S'nin gerisinde, gerçek
    anahtarla doğrulanır; etkin anahtar değişmediği için yazım da bozulmaz). Kayma araması İA'yı
    `key_ref`'ten yürürlüksüz çözer (`satir_izi` "İZ BOŞLUĞU" (c)): giriş açılmaz; satır, sayaç ve
    sarmal değişmez. Sahte anahtarsız kol `test_iz_boslugu_girisi_acmaz[yeniden_numaralama]`'dır."""
    kimlik, sira, sayi = _senaryo1_degistirilmis("yeniden_numaralama")
    with connection.cursor() as cursor:
        cursor.execute(_SAHTE_EMEKLI_ANAHTAR, [sira + 1])
    once, sarmal = _ham(kimlik), _sarmal(kimlik)

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=_KAYMA)
    assert OTURUM.hesap_id() is None
    assert _butunluk_sayisi() == sayi + 1
    assert (_ham(kimlik), _sarmal(kimlik)) == (once, sarmal)
    assert app_password.wrap_failure_state(kimlik) == (0, False)


def _birincil_anahtarsiz_yeniden_kur(baglanti: sqlite3.Connection) -> None:
    """SQLite tarayıcısının "Tabloyu değiştir" işlemi taklidi (kod gerekmez): `okul_audittrail`
    aynı sütunlar ve verilerle, BİRİNCİL ANAHTARSIZ yeniden kurulur; sıranın (tekil olmayan)
    indeksi yeniden kurulur."""
    baglanti.execute("CREATE TABLE yeni_iz AS SELECT * FROM okul_audittrail")
    baglanti.execute("DROP TABLE okul_audittrail")
    baglanti.execute("ALTER TABLE yeni_iz RENAME TO okul_audittrail")
    baglanti.execute("CREATE INDEX iz_sira ON okul_audittrail (seq)")


def test_birincil_anahtarsiz_tabloda_birebir_kopya_silmeyi_ortmez(tmp_path: Path) -> None:
    """Bağımsız denetim bulgusu (b5): silme sayımı ("İZ BOŞLUĞU" (a)) birincil anahtarın
    tekilliğine GÜVENMEZ. Tablo birincil anahtarsız yeniden kurulur (yanlış alarm yok: karar
    değişmez), hesabın son kaydından sonraki satırlar silinir ve yerlerine S'den sonraki ilgisiz
    bir satırın BİREBİR kopyaları (aynı sıra, aynı MAC) eklenir: `COUNT(*)` ve `MAX` tutar, bütün
    sıralar tamsayıdır, dayanak (zincir başı) dokunulmamıştır. Farklı sıraların sayısı tutmaz:
    satır tutmaz."""
    db = tmp_path / "iz.sqlite3"
    _uzun_iz(db, 10)  # program yöneticisinin kaydı 1, ardından 2…11 ilgisiz satır
    with closing(sqlite3.connect(db)) as baglanti:
        assert satir_izi.hesap_izi_sirasi(baglanti, TEST_HESAP_ID, TEST_DEK) == 1
        _birincil_anahtarsiz_yeniden_kur(baglanti)
        baglanti.commit()
        assert satir_izi.hesap_izi_sirasi(baglanti, TEST_HESAP_ID, TEST_DEK) == 1

        baglanti.execute("DELETE FROM okul_audittrail WHERE seq IN (3, 4, 6)")
        for _ in range(3):
            baglanti.execute(
                "INSERT INTO okul_audittrail SELECT * FROM okul_audittrail WHERE seq = 5 LIMIT 1"
            )
        baglanti.commit()
        assert baglanti.execute(
            "SELECT COUNT(*), MAX(seq) FROM okul_audittrail WHERE seq > 1"
        ).fetchone() == (10, 11)

        assert satir_izi.hesap_izi_sirasi(baglanti, TEST_HESAP_ID, TEST_DEK) is None


@pytest.mark.django_db(transaction=True)
def test_iz_boslugu_cikisi_kurtarma_anahtariyla_eski_yedektir(tmp_path: Path) -> None:
    """Çıkış gerçekten vardır (kabul edilen bedelin çıkışı): ilgisiz bir satır silinmiş izde ne
    muhasip ne program yöneticisi girer; program yöneticisinin PAROLA yolu geri yüklemede de güncel
    veritabanındaki boşluğu görür (`RET_IZ_BOSLUGU`, hiçbir dosya değişmez). Kurtarma anahtarıyla,
    değişiklikten ÖNCE alınmış yedek geri yüklenir; ardından ikisi de girer."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    yedek = goruntu(tmp_path / "yedek.sqlite3")
    dolgu = _dolgu(3)
    app_password.lock()
    _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])
    for hesap_id, parola in ((kimlik, GECICI_PAROLA), (TEST_HESAP_ID, TEST_PAROLA)):
        with pytest.raises(app_password.AccountRecordStale):
            app_password.unlock(hesap_id=hesap_id, password=parola)
    guncel = goruntu(tmp_path / "guncel.sqlite3")

    with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as ret:
        geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    assert ret.value.kod == geri_yukleme_yetkisi.RET_IZ_BOSLUGU
    assert (tmp_path / "canli" / "db.sqlite3").read_bytes() == guncel

    db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    _dosyada_hepsi_izli(db)
    programa_al(db)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)
    assert OTURUM.hesap_id() == kimlik


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("capa", ["bosluksuz", "bosluklu"])
def test_bosluklu_capa_k_a_ya_duser(capa: str, tmp_path: Path) -> None:
    """Özet onarımının çapası da aynı işlevden geçer: muhasip yedekten SONRA parolasını değiştirir;
    boşluksuz taze çapada yeni parolasının özeti geri yüklenen satıra taşınır (yeni parolayla
    girer). Çapanın izinde muhasibin son kaydından sonra bir satır silinmişse çapa o hesap için
    kullanılamaz (K-a): dosyadaki yeni sarmal geri yüklenen satırın (yedek günündeki) özetini
    tutmaz, iki özet boşaltılır — yeni parola açmaz (`WrapDigestMismatch`)."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    yedek = goruntu(tmp_path / "yedek.sqlite3")
    _muhasip_degistirir(kimlik, GECICI_PAROLA, YENI_PAROLA)
    dolgu = _dolgu(3)
    if capa == "bosluklu":
        _tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])
    guncel = goruntu(tmp_path / "guncel.sqlite3")

    db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    satir = hesap_satiri_oku(db, kimlik)
    _dosyada_hepsi_izli(db)
    programa_al(db)
    app_password.lock()
    if capa == "bosluksuz":
        assert satir[6] == app_password.wrap_digest(TEST_DEK, _sarmal(kimlik))
        assert app_password.unlock(hesap_id=kimlik, password=YENI_PAROLA).id == muhasip.id
    else:
        assert (satir[6], satir[7]) == ("", "")
        with pytest.raises(app_password.WrapDigestMismatch):
            app_password.unlock(hesap_id=kimlik, password=YENI_PAROLA)


#: Performans ölçümünün iz uzunluğu (görev: 20 000+ satır).
_OLCUM_SATIRI = 25_000


def _uzun_iz(db: Path, adet: int) -> None:
    """Program yöneticisinin satırından sonra `adet` meşru (MAC'i tutan, açık kip, `SISTEM`)
    ilgisiz satır: hesabın son kaydından zincir başına uzun bir aralık (en kötü sayım)."""
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[HesapSatiri(TEST_HESAP_ID, "yonetici")])
    zincir = crypto.audit_chain_key(TEST_IA)
    with closing(sqlite3.connect(db)) as baglanti:
        seq, prev = baglanti.execute(
            "SELECT seq, mac FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        an = datetime(2026, 11, 3, 8, 0, tzinfo=UTC)
        satirlar: list[tuple[Any, ...]] = []
        for _ in range(adet):
            seq += 1
            alanlar = {
                "seq": seq,
                "at": an,
                "actor": "SISTEM",
                "account": None,
                "role": "",
                "action": "HESAP",
                "model": "okul.Deneme",
                "object_id": "olcum",
                "term": None,
                "changed_fields": [],
                "values": {},
                "record_mac": "",
                "compliance_item": None,
                "label": "",
                "key_mode": "ACIK",
                "key_ref": "1",
            }
            mac = kanonik.iz_mac(zincir, alanlar, prev)
            satirlar.append(
                (seq, satir_izi.django_zamani(an), "SISTEM", "", "HESAP", "okul.Deneme", "olcum")
                + ("[]", "{}", "", "", "ACIK", "1", prev, mac)
            )
            prev = mac
        baglanti.executemany(
            "INSERT INTO okul_audittrail VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            satirlar,
        )
        baglanti.commit()


#: Duvar saati sınırları GEVŞEKTİR (gerilemeyi yakalar; kapı `--cov` ve dal kapsamıyla koşar, kayma
#: araması saf Python döngüsü olduğu için kapsam altında ~3 kat yavaşlar — bağımsız denetim bulgusu).
#: Asıl sınır algoritmiktir: HMAC sayısı (`_mac_cagrilari`).
_MESRU_SURE_SINIRI = 0.5
_BOZUK_SURE_SINIRI = 5.0


def _sure(baglanti: sqlite3.Connection) -> tuple[float, int | None]:
    """`hesap_izi_sirasi`'nın en iyi süresi (5 deneme) ve sonucu."""
    en_iyi, sonuc = float("inf"), None
    for _ in range(5):
        basla = time.perf_counter()
        sonuc = satir_izi.hesap_izi_sirasi(baglanti, TEST_HESAP_ID, TEST_DEK)
        en_iyi = min(en_iyi, time.perf_counter() - basla)
    return en_iyi, sonuc


def _mac_cagrilari(baglanti: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch) -> int:
    """Bir `hesap_izi_sirasi` çağrısındaki zincir MAC hesabı (`_mac_tutuyor`) sayısı."""
    asil = satir_izi._mac_tutuyor
    sayac = 0

    def sayan(*args: Any, **kwargs: Any) -> bool:
        nonlocal sayac
        sayac += 1
        return asil(*args, **kwargs)

    with monkeypatch.context() as yama:
        yama.setattr(satir_izi, "_mac_tutuyor", sayan)
        satir_izi.hesap_izi_sirasi(baglanti, TEST_HESAP_ID, TEST_DEK)
    return sayac


def test_iz_boslugu_denetiminin_suresi_uzun_izde(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kullanıcı kararı: "ucuz olmalı, girişi yavaşlatmamalı". Program yöneticisinin son kaydından
    sonra 25 000 satır. Algoritmik sınır: meşru izde denetim hesabın kendi satırları ve dayanak
    için birer HMAC yapar (doğrusal yürüyüş yok); dayanak bozuksa kayma araması en çok
    `KAYMA_SINIRI` HMAC, kaymışsa ilk bulduğunda durur. Duvar saati sınırları gevşektir (kapsam
    ölçümü altında da geçer); süreler `-s` ile yazdırılır (raporda)."""
    db = tmp_path / "uzun.sqlite3"
    _uzun_iz(db, _OLCUM_SATIRI)
    with closing(sqlite3.connect(db)) as baglanti:
        mesru, sonuc = _sure(baglanti)
        assert sonuc == 1
        assert _mac_cagrilari(baglanti, monkeypatch) == 2  # hesabın satırı + dayanak
        # Dayanak (zincir başı) program dışından değiştirilir: MAC hiçbir sırada tutmaz.
        baglanti.execute(
            "UPDATE okul_audittrail SET object_id = 'baska' WHERE seq = "
            "(SELECT MAX(seq) FROM okul_audittrail)"
        )
        baglanti.commit()
        bozuk, sonuc = _sure(baglanti)
        assert sonuc == 1  # bozuk dayanak kayma işareti değildir
        assert _mac_cagrilari(baglanti, monkeypatch) == 2 + satir_izi.KAYMA_SINIRI
        # Kaydırma: bir satır silinir, sonrakiler aşağı kayar (dayanak kaymıştır).
        baglanti.execute(
            "UPDATE okul_audittrail SET object_id = 'olcum' WHERE seq = "
            "(SELECT MAX(seq) FROM okul_audittrail)"
        )
        baglanti.execute("DELETE FROM okul_audittrail WHERE seq = 5000")
        # İki adımda (eksiye, sonra bir aşağı): toplu güncellemede birincil anahtar çakışmasın.
        baglanti.execute("UPDATE okul_audittrail SET seq = -seq WHERE seq > 5000")
        baglanti.execute("UPDATE okul_audittrail SET seq = -seq - 1 WHERE seq < 0")
        baglanti.commit()
        kayma, sonuc = _sure(baglanti)
        assert sonuc is None
        assert _mac_cagrilari(baglanti, monkeypatch) == 3  # d = 1'de bulunur
    print(
        f"\nİz boşluğu denetimi, {_OLCUM_SATIRI} satır: meşru {mesru * 1000:.1f} ms, "
        f"bozuk dayanak {bozuk * 1000:.1f} ms, kaymış dayanak {kayma * 1000:.1f} ms"
    )
    assert mesru < _MESRU_SURE_SINIRI
    assert bozuk < _BOZUK_SURE_SINIRI and kayma < _BOZUK_SURE_SINIRI


# ============================================================ O-3 ve O-4


@pytest.mark.parametrize("bicim", ["blob_orta", "blob_bas", "metin", "real", "azami_tamsayi"])
def test_zincir_basi_tamsayi_degilse_yazici_turkce_reddeder(
    bicim: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Orkestratör kararı O-3: zincirin başına oturan tamsayı olmayan sıra (program dışından:
    ortadaki bir satırın sırası BLOB'a çevrilir — eskiden `int(b"57") + 1` var olan bir sırayla
    çakışır, her iz yazımı `IntegrityError` verirdi; baş satırınki BLOB'a, metne ya da kesirli
    REAL'e çevrilir — eskiden zincir sessizce yanlış yere uzar ya da `ValueError` verirdi) yazıcıyı
    ve zincir başı okuyucusunu Türkçe `IzYazilamadi` ile durdurur: satır yazılmaz. Reddedilen
    girişin `BUTUNLUK` satırı da yazılamaz, olay günlüğe düşer; giriş zaten açılmaz.

    Bağımsız denetim bulgusu (b5): baş satırın sırası SQLite'ın en büyük tamsayısıysa
    (`satir_izi.EN_BUYUK_SIRA`; `CHECK seq >= 0` ve tetikleyiciler kesmez) `+ 1` taşardı
    (`OverflowError`): yazıcı aynı Türkçe iletiyle reddeder. Okuyucu böyle bir başı okur (değeri
    tamsayıdır); giriş (a)'nın sayımıyla kapanır."""
    _dolgu(3)
    son = _son_seq()
    if bicim == "blob_orta":
        hedef = son - 1
        _tetikleyicisiz(
            "UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [hedef]
        )
    elif bicim == "blob_bas":
        _tetikleyicisiz("UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [son])
    elif bicim == "metin":
        _tetikleyicisiz("UPDATE okul_audittrail SET seq = 'son satir' WHERE seq = %s", [son])
    elif bicim == "azami_tamsayi":
        _sira_tasi(son, satir_izi.EN_BUYUK_SIRA)
    else:
        _tetikleyicisiz("UPDATE okul_audittrail SET seq = %s WHERE seq = %s", [son + 0.5, son])
    adet = AuditTrail.objects.count()

    with (
        pytest.raises(denetim_izi.IzYazilamadi, match="Denetim izinin son kaydı bozuk"),
        sistem_olarak(),
        transaction.atomic(),
    ):
        denetim_izi.olay(AuditAction.BUTUNLUK, model="okul.Deneme", object_id="x")
    if bicim == "azami_tamsayi":
        bas = denetim_izi.zincir_basi()
        assert bas is not None and bas[0] == satir_izi.EN_BUYUK_SIRA
    else:
        with pytest.raises(denetim_izi.IzYazilamadi, match="Denetim izinin son kaydı bozuk"):
            denetim_izi.zincir_basi()
    assert AuditTrail.objects.count() == adet

    app_password.lock()
    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert AuditTrail.objects.count() == adet
    assert "Hesap kaydının tutmadığı denetim izine yazılamadı." in caplog.text


def test_zincir_basinin_mac_i_metin_degilse_yazici_turkce_reddeder() -> None:
    """O-3'ün uzantısı (bağımsız denetim bulgusu, b5): baş satırın `mac`'i program dışından ikili
    değere (BLOB) çevrilirse yazıcı onu `prev_mac` yapmaz — eskiden ham kanonik hatası
    (`KanonikHata`) çıkardı; Türkçe `IzYazilamadi` verir, satır yazılmaz. (Tamsayı değeri sütun
    yakınlığıyla metin saklanır, bu dalı sınamaz: ikili değer `CAST(mac AS BLOB)` ile yazılır.)"""
    _dolgu(3)
    son = _son_seq()
    _tetikleyicisiz("UPDATE okul_audittrail SET mac = CAST(mac AS BLOB) WHERE seq = %s", [son])
    with connection.cursor() as cursor:
        cursor.execute("SELECT typeof(mac) FROM okul_audittrail WHERE seq = %s", [son])
        assert cursor.fetchone() == ("blob",)
    adet = AuditTrail.objects.count()

    with (
        pytest.raises(denetim_izi.IzYazilamadi, match="Denetim izinin son kaydı bozuk"),
        sistem_olarak(),
        transaction.atomic(),
    ):
        denetim_izi.olay(AuditAction.BUTUNLUK, model="okul.Deneme", object_id="x")

    assert AuditTrail.objects.count() == adet


def test_onarim_yazicisi_en_buyuk_sirada_turkce_reddeder(tmp_path: Path) -> None:
    """Bağımsız denetim bulgusu (b5): onarımın ORM'siz yazıcısı (`hesap_satirlarini_izle`), zincir
    başının sırası yeni satırlara yer bırakmıyorsa (SQLite'ın en büyük tamsayısı) `OverflowError`
    yerine `IzYazilamadi` verir (`ozet_onarimi` onu `OnarimYazilamadi`'ye çevirir); satır eklenmez.
    (`ozetleri_onar` bu başa varamaz: böyle bir izde hiçbir satırın izi tutmaz, onarılacak satır
    yoktur — denetim yazıcının kendi sözleşmesidir.)"""
    db = tmp_path / "iz.sqlite3"
    yetkili_sqlite(db, dek=TEST_DEK, hesaplar=[HesapSatiri(TEST_HESAP_ID, "yonetici")], wal=False)
    with closing(sqlite3.connect(db)) as baglanti:
        baglanti.execute(
            "UPDATE okul_audittrail SET seq = ? WHERE seq = (SELECT MAX(seq) FROM okul_audittrail)",
            (satir_izi.EN_BUYUK_SIRA,),
        )
        baglanti.commit()
        adet = baglanti.execute("SELECT COUNT(*) FROM okul_audittrail").fetchone()

        with pytest.raises(satir_izi.IzYazilamadi, match="zincir başı biçimsiz"):
            satir_izi.hesap_satirlarini_izle(
                baglanti,
                {TEST_HESAP_ID: ["seal"]},
                TEST_DEK,
                an=datetime(2026, 11, 3, 8, 0, tzinfo=UTC),
            )
        baglanti.rollback()

        assert baglanti.execute("SELECT COUNT(*) FROM okul_audittrail").fetchone() == adet


def test_parola_degistirmenin_ikinci_adiminda_ret_butunluk_satiri_birakir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orkestratör kararı O-4: `change_password`'ün 2. adımı satırın izini işlemin İÇİNDE yeniden
    denetler. 1. adım commit edildikten sonra satır program dışından eski kopyasına geri sarılırsa
    ret o işlemin içinde doğar; reddin `BUTUNLUK` satırı eskiden işlemle birlikte geri alınıyordu.
    Artık işlem geri alındıktan sonra yazılır: tek `BUTUNLUK` satırı (`SISTEM`, `kayit_mac`),
    parola değişmez (satır ve sarmal)."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)
    kopya = _kopyala(kimlik)
    sarmal = _sarmal(kimlik)
    asil = app_password.write_wrap_digests
    durum_: dict[str, Any] = {}

    def birinci_adimdan_sonra(*args: Any, **kwargs: Any) -> bool:
        yazdi = asil(*args, **kwargs)
        # 1. adımın işlemi (bekleyen özet ve `HESAP` satırı) commit edilmeden hemen önce satır
        # program dışından eski kopyasına geri sarılır: 2. adım geri sarılmış satırı görür.
        _geri_sar(kimlik, kopya)
        durum_["geri_sarildi"] = True
        durum_["son"] = _son_seq()
        return yazdi

    monkeypatch.setattr(app_password, "write_wrap_digests", birinci_adimdan_sonra)

    with (
        yazar_olarak(Yazar(hesap_id=kimlik, rol=AccountRole.MUHASIP)),
        pytest.raises(app_password.AccountRecordStale) as hata,
    ):
        app_password.change_password(
            hesap_id=kimlik, current_password=GECICI_PAROLA, new_password=YENI_PAROLA
        )

    _reddedilir(hata, app_password.ISLEMDE_KAYIT_MESSAGE)
    assert durum_.get("geri_sarildi") is True
    _tek_butunluk(kimlik, durum_["son"])
    assert _sarmal(kimlik) == sarmal


# ============================================================ yanlış alarm yok: yaşam döngüsü


@pytest.mark.hesapsiz
def test_ilk_kurulumun_satiri_izlidir_giris_acilir(parolasiz: Path) -> None:
    kurtarma = app_password.enable(
        tanitici="yonetici", display_name="Örnek Yönetici", password=YENI_PAROLA
    )
    assert kurtarma
    _hepsi_izli()
    (hesap,) = Account.objects.all()
    app_password.lock()
    app_password.unlock(hesap_id=hesap.id, password=YENI_PAROLA)
    _hepsi_izli()


def test_yanlis_alarm_yok_hesap_yasam_dongusu() -> None:
    """Her meşru akıştan sonra bütün satırlar son iz kaydını tutar ve giriş açılır (görev 2)."""
    _hepsi_izli()
    muhasip = hesap_ac()  # açma (PAROLA_YENILENMELI)
    _hepsi_izli()
    kimlik = str(muhasip.id)
    muhasip_yazari = Yazar(hesap_id=kimlik, rol=AccountRole.MUHASIP)

    app_password.lock()  # ilk giriş ve zorunlu yenileme
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA, new_password=YENI_PAROLA)
    _hepsi_izli()
    with yazar_olarak(muhasip_yazari):  # parola değiştirme
        app_password.change_password(
            hesap_id=kimlik, current_password=YENI_PAROLA, new_password=UCUNCU_PAROLA
        )
        app_password.verify_password(hesap_id=kimlik, password=UCUNCU_PAROLA)
    _hepsi_izli()

    # 180 gün yenilemesi (zaman geçer: izli yazım) ve bildirim kapanışı.
    muhurle(
        Account.objects.get(pk=kimlik),
        password_changed_at=timezone.now() - timedelta(days=181),
    )
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    _hepsi_izli()

    # Kurtarma anahtarıyla açılış ve anahtar yenileme (program yöneticisi).
    app_password.lock()
    app_password.unlock_with_recovery(
        recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
    )
    _hepsi_izli()
    app_password.renew_recovery_key(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    hesaplar.acknowledge_reset_notice(hesap_id=TEST_HESAP_ID)
    _hepsi_izli()

    # Sıfırlama ve sahibinin girişi; bildirimin kapanması.
    hesaplar.reset_password(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=GECICI_PAROLA)
    _hepsi_izli()
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA, new_password=_DORDUNCU_PAROLA)
    with yazar_olarak(muhasip_yazari):
        hesaplar.acknowledge_reset_notice(hesap_id=kimlik)
    _hepsi_izli()

    # Askı (görev bölümü; izli yazım) ve askıdan çıkarma; hatalı deneme askısı.
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    muhurle(
        Account.objects.get(pk=kimlik),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.GOREV_BOLUMU,
    )
    _hepsi_izli()
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)
    _hepsi_izli()
    app_password.lock()
    for _ in range(app_password.SUSPEND_AFTER_FAILURES):
        with pytest.raises(app_password.UnlockRefused):
            app_password.unlock(hesap_id=kimlik, password="Yanlis-Parola-1")
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=_DORDUNCU_PAROLA)
    _hepsi_izli()

    # Kapama.
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)
    _hepsi_izli()
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=YENI_PAROLA)
    _hepsi_izli()


#: İki aşamalı yazımın kesintileri (`test_sarmal_tazeligi.py` ile aynı yazıcılar).
_KESINTILER = ("dosya_yazilamadi", "dosya_yazilip_commit_olmadi", "bekleyen_yazilamadi")


@pytest.mark.parametrize("kesinti", _KESINTILER)
@pytest.mark.parametrize("yazici", ["kilit_yenileme", "parola_degistirme", "kurtarma", "sifirlama"])
def test_yanlis_alarm_yok_iki_asamali_yazimin_kesintileri(
    yazici: str, kesinti: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Her kesinti noktasında satır son iz kaydını tutar ve sonraki ilk açılış (o an dosyada
    duran meşru sarmalın parolasıyla) açılır; açılıştan sonra da izlidir."""
    if yazici == "kilit_yenileme":
        hesap = hesap_ac()
        app_password.lock()
        kimlik, eski, yeni = str(hesap.id), GECICI_PAROLA, YENI_PAROLA

        def calistir() -> object:
            return app_password.unlock(hesap_id=kimlik, password=eski, new_password=yeni)

    elif yazici == "parola_degistirme":
        kimlik, eski, yeni = TEST_HESAP_ID, TEST_PAROLA, YENI_PAROLA

        def calistir() -> object:
            app_password.change_password(hesap_id=kimlik, current_password=eski, new_password=yeni)
            return None

    elif yazici == "kurtarma":
        app_password.lock()
        kimlik, eski, yeni = TEST_HESAP_ID, TEST_PAROLA, YENI_PAROLA

        def calistir() -> object:
            return app_password.unlock_with_recovery(
                recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=kimlik, new_password=yeni
            )

    else:
        hesap = _acik_muhasip()
        kimlik, eski, yeni = str(hesap.id), GECICI_PAROLA, UCUNCU_PAROLA

        def calistir() -> object:
            return hesaplar.reset_password(
                by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=yeni
            )

    gercek_sarmal = app_password._replace_wrap
    gercek_kayit = Account.save

    def yazilamadi(_d: dict[str, Any], _y: dict[str, Any]) -> None:
        raise OSError("disk dolu")

    def yazip_dus(d: dict[str, Any], y: dict[str, Any]) -> None:
        gercek_sarmal(d, y)
        raise OSError("süreç öldü")

    def bekleyen_dus(satir: Account, *args: Any, **kwargs: Any) -> None:
        if "wrap_digest_pending" in (kwargs.get("update_fields") or ()) and (
            satir.wrap_digest_pending
        ):
            raise OSError("veritabanı kilitli")
        gercek_kayit(satir, *args, **kwargs)

    with monkeypatch.context() as yama:
        if kesinti == "dosya_yazilamadi":
            yama.setattr(app_password, "_replace_wrap", yazilamadi)
        elif kesinti == "dosya_yazilip_commit_olmadi":
            yama.setattr(app_password, "_replace_wrap", yazip_dus)
        else:
            yama.setattr(Account, "save", bekleyen_dus)
        with pytest.raises(OSError):
            calistir()
    _hepsi_izli()
    app_password.lock()
    acan = yeni if kesinti == "dosya_yazilip_commit_olmadi" else eski
    try:
        app_password.unlock(hesap_id=kimlik, password=acan)
    except app_password.PasswordRenewalRequired:
        app_password.unlock(hesap_id=kimlik, password=acan, new_password=_SONRAKI_PAROLA)
    assert OTURUM.hesap_id() == kimlik
    _hepsi_izli()


# ============================================================ geri yükleme, onarımın izi


def _onarim_satirlari(db: Path, bas: int) -> list[tuple[str, str, str, str, list[str]]]:
    """Geri yüklenen dosyada `bas`'tan sonraki iz satırları: (aktör, tür, model, kimlik, alanlar)."""
    with closing(sqlite3.connect(db)) as baglanti:
        satirlar = baglanti.execute(
            "SELECT actor, action, model, object_id, changed_fields FROM okul_audittrail "
            "WHERE seq > ? ORDER BY seq",
            (bas,),
        ).fetchall()
    return [(a, t, m, k, json.loads(d)) for a, t, m, k, d in satirlar]


def _dosyada_hepsi_izli(db: Path) -> None:
    with closing(sqlite3.connect(db)) as baglanti:
        kimlikler = [str(uuid.UUID(k)) for (k,) in baglanti.execute("SELECT id FROM okul_account")]
        for kimlik in kimlikler:
            assert satir_izi.hesap_izi_tutuyor(baglanti, kimlik, TEST_DEK), kimlik


def _yedek_basi(icerik_yolu: Path) -> int:
    with closing(sqlite3.connect(icerik_yolu)) as baglanti:
        satir = baglanti.execute("SELECT MAX(seq) FROM okul_audittrail").fetchone()
    return int(satir[0] or 0)


def _muhasip_degistirir(kimlik: str, eski: str, yeni: str) -> None:
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=eski)
    with yazar_olarak(Yazar(hesap_id=kimlik, rol=AccountRole.MUHASIP)):
        app_password.change_password(hesap_id=kimlik, current_password=eski, new_password=yeni)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "capa",
    ["taze_tasinan", "taze_capadan", "bayat_capada_yok", "capada_kapali", "okunamiyor"],
)
def test_onarimin_izi_ilk_acilisi_acar_zincir_bulgusuz(capa: str, tmp_path: Path) -> None:
    """Onarımın değiştirdiği her satır aynı işlemde `SISTEM` `HESAP` satırını alır (K-e; seçenek
    (i)): geri yüklenen dosyada her satır izini tutar; program o veritabanıyla açılınca ilk kilit
    açılışı (geri yükleme notu ve iki depo karşılaştırmasıyla) açılır, zincir bulgusuzdur ve kayıt
    bütünlüğü tutar. Çapa hâlleri: taze çapa (dosyadaki sarmala taşınır / çapanın özetleri geçer),
    bayat çapa (çift geri yükleme: çapada satırı yok), çapada `KAPALI`, okunamayan çapa (K-a)."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    yedek_yolu = tmp_path / "yedek.sqlite3"
    guncel: bytes | None
    if capa == "bayat_capada_yok":
        b1 = goruntu(tmp_path / "b1.sqlite3")
        ikinci = hesap_ac(AccountRole.SEKRETER, tanitici="sekreter", ad="Örnek Sekreter")
        kimlik = str(ikinci.id)
        yedek = goruntu(yedek_yolu)
        guncel = goruntu(tmp_path / "guncel.sqlite3")
        ilk = geri_yukle(tmp_path, b1, guncel, hesap="yonetici", password=TEST_PAROLA)
        guncel = ilk.read_bytes()
    else:
        yedek = goruntu(yedek_yolu)
        if capa == "capada_kapali":
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)
        else:
            _muhasip_degistirir(kimlik, GECICI_PAROLA, YENI_PAROLA)
        if capa == "taze_capadan":
            # Biri geri yüklemeden ÖNCE eski sarmalı koyar: çapanın özetleri geçer.
            arsiv = [
                b
                for a in sorted(app_password.state_path().parent.glob("guvenlik-arsiv-*.json"))
                for b in json.loads(a.read_text(encoding="utf-8")).get("hesaplar", [])
                if b.get("id") == kimlik
                and app_password._try_unwrap_account(b, durum(), GECICI_PAROLA) is not None
            ]
            _geri_koy(arsiv[0])
        guncel = None if capa == "okunamiyor" else goruntu(tmp_path / "guncel.sqlite3")
    bas = _yedek_basi(yedek_yolu)

    if capa == "okunamiyor":
        db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)
    else:
        db = geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)

    onarim = _onarim_satirlari(db, bas)
    assert onarim, "onarım satır değiştirmeliydi"
    for aktor, tur, model, nesne, alanlar in onarim:
        assert (aktor, tur, model) == ("SISTEM", "HESAP", "okul.Account")
        assert alanlar and set(alanlar) <= set(satir_izi.ONARIM_ALANLARI)
        assert nesne in {kimlik, TEST_HESAP_ID}
    assert kimlik in {satir[3] for satir in onarim}
    _dosyada_hepsi_izli(db)
    programa_al(db)
    assert denetim_izi.zinciri_dogrula() == []
    _hepsi_izli()
    app_password.lock()
    try:
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    except app_password.WrapDigestMismatch:
        assert capa == "okunamiyor"  # K-a: yönetici parolası yedekten sonra değişmediyse açar
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=TEST_HESAP_ID, new_password=YENI_PAROLA
        )
    assert OTURUM.hesap_id() == TEST_HESAP_ID
    _hepsi_izli()
    assert denetim_izi.zinciri_dogrula() == []
    if capa == "taze_tasinan":
        app_password.lock()
        assert app_password.unlock(hesap_id=kimlik, password=YENI_PAROLA).id == muhasip.id


@pytest.mark.django_db(transaction=True)
def test_onarimin_orm_siz_satiri_denetim_izininkiyle_birebir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ORM/ORM'siz eşitlik: aynı durumdan, aynı anla ve aynı değişiklikle `denetim_izi`'nin yazdığı
    satır ile onarımın ORM'siz yazıcısının yazdığı satır alan alan aynıdır (sıra, an, aktör, kip,
    `key_ref`, değişen alanlar, değerler, içerik MAC'i, `prev_mac`, zincir MAC'i); ham sütun
    biçimi de (Django'nun saat dilimsiz UTC metni, JSON metni) aynıdır."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    once = goruntu(tmp_path / "once.sqlite3")
    an = datetime(2026, 11, 3, 8, 15, 42, 123456, tzinfo=UTC)
    monkeypatch.setattr(timezone, "now", lambda: an)
    hesap = Account.objects.get(pk=kimlik)
    with sistem_olarak(), transaction.atomic():
        app_password.write_wrap_digests(hesap, TEST_DEK, asil="", bekleyen="")
    orm = AuditTrail.objects.order_by("-seq").first()
    assert orm is not None and orm.object_id == kimlik
    yeni = Account.objects.get(pk=kimlik)

    kopya = tmp_path / "kopya.sqlite3"
    kopya.write_bytes(once)
    with closing(sqlite3.connect(kopya)) as yazici:
        yazici.execute(
            "UPDATE okul_account SET wrap_digest = ?, wrap_digest_pending = ?, seal = ? "
            "WHERE id = ?",
            ("", "", yeni.seal, muhasip.id.hex),
        )
        (seq,) = satir_izi.hesap_satirlarini_izle(
            yazici, {kimlik: list(orm.changed_fields)}, TEST_DEK, an=an
        )
        yazici.commit()
        ham_orm_siz = yazici.execute(
            'SELECT "at", changed_fields, "values" FROM okul_audittrail WHERE seq = ?', (seq,)
        ).fetchone()
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT CAST("at" AS TEXT), changed_fields, "values" FROM okul_audittrail '
            "WHERE seq = %s",
            [orm.seq],
        )
        ham_orm = cursor.fetchone()

    assert seq == orm.seq
    assert tuple(ham_orm_siz) == tuple(ham_orm)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}", ham_orm_siz[0])
    programa_al(kopya)
    orm_siz = AuditTrail.objects.get(seq=seq)
    for alan in ("record_mac", "prev_mac", "mac", "key_ref", "key_mode", "actor"):
        assert getattr(orm_siz, alan) == getattr(orm, alan), alan
    assert denetim_izi.satir_alanlari(orm_siz) == denetim_izi.satir_alanlari(orm)
    assert denetim_izi.satir_kurali_tutuyor(orm_siz)
    assert denetim_izi.zinciri_dogrula() == []
    assert denetim_izi.kaydi_dogrula(Account, kimlik) is True


@pytest.mark.django_db(transaction=True)
def test_reddedilen_satirin_cikisi_kurtarma_anahtariyla_geri_yuklemedir(tmp_path: Path) -> None:
    """Çıkış gerçekten vardır (zarfın üçüncü durumu): geri sarılmış satır giriş, sıfırlama ve
    kapamayı açmaz; kurtarma anahtarıyla, geri sarmadan önceki bir yedek geri yüklenir. Çapa
    (geri sarılmış satırı taşıyan güncel veritabanı) o hesap için KULLANILAMAZ: izi tutmayan çapa
    satırının özetleri geri yüklenen satıra taşınmaz (aklanmaz); dosyada geri konmuş T'nin sarmalı
    durduğu için iki özet boşaltılır (K-a). T açmaz; program yöneticisi girer, parolayı sıfırlar,
    muhasip yeni geçici parolasıyla girer."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    hesaplar.reset_password(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA)
    kopya, gecici = _kopyala(kimlik), _sarmal(kimlik)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    yedek = goruntu(tmp_path / "yedek.sqlite3")
    app_password.lock()
    _geri_sar(kimlik, kopya)
    _geri_koy(gecici)
    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    guncel = goruntu(tmp_path / "guncel.sqlite3")

    db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    satir = hesap_satiri_oku(db, kimlik)
    assert (satir[6], satir[7]) == ("", "")
    _dosyada_hepsi_izli(db)
    programa_al(db)
    with pytest.raises(app_password.WrapDigestMismatch):
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    hesaplar.reset_password(
        by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=_DORDUNCU_PAROLA
    )
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=_DORDUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    assert OTURUM.hesap_id() == kimlik
    _hepsi_izli()


# ============================================================ K-a (birim) ve okuma


def _onar(
    tmp_path: Path, yeni: list[HesapSatiri], ozetler: dict[str, str | None]
) -> tuple[ozet_onarimi.OnarimSonucu, Path]:
    yeni_db = tmp_path / "yeni.sqlite3"
    yetkili_sqlite(yeni_db, dek=TEST_DEK, hesaplar=yeni, wal=False)
    sonuc = ozet_onarimi.ozetleri_onar(
        onceki_db=tmp_path / "yok.sqlite3", yeni_db=yeni_db, dek=TEST_DEK, sarmal_ozetleri=ozetler
    )
    return sonuc, yeni_db


def test_kullanilamayan_capada_dosyadakini_tutmayan_ozetler_bosaltilir(tmp_path: Path) -> None:
    """K-a: çapa okunamıyor. Dosyadaki sarmal satırın asıl ya da bekleyen özetini tutuyorsa
    özetler kalır; tutmuyorsa ya da dosyada sarmal yoksa iki özet boşaltılır, satır yeniden
    mühürlenir ve onarım `SISTEM` `HESAP` satırıyla izlenir. Mührü tutmayan satıra dokunulmaz."""
    tutan = HesapSatiri(TEST_HESAP_ID, "yonetici", ozet="aa" * 32)
    bekleyeni_tutan = HesapSatiri(
        _YONETICI_2, "yonetici-2", ozet="bb" * 32, bekleyen_ozet="cc" * 32
    )
    tutmayan = HesapSatiri(_MUHASIP, "muhasip", role="muhasip", ozet="dd" * 32)
    sarmalsiz = HesapSatiri(_SEKRETER, "sekreter", role="sekreter", ozet="ee" * 32)
    muhursuz = HesapSatiri(_BASKAN, "baskan", role="baskan", ozet="ff" * 32, muhur="0" * 64)
    bekleyeni_dolu = HesapSatiri(
        _BASKAN_YARDIMCISI,
        "baskan-yardimcisi",
        role="baskan_yardimcisi",
        ozet="ab" * 32,
        bekleyen_ozet="cd" * 32,
    )
    ozetler: dict[str, str | None] = {
        tutan.id: "aa" * 32,
        bekleyeni_tutan.id: "cc" * 32,
        tutmayan.id: "12" * 32,
        muhursuz.id: "34" * 32,
        bekleyeni_dolu.id: "56" * 32,
    }
    satirlar = [tutan, bekleyeni_tutan, tutmayan, sarmalsiz, muhursuz, bekleyeni_dolu]

    sonuc, db = _onar(tmp_path, satirlar, ozetler)

    assert sonuc.capa_okunamadi and not sonuc.atlandi
    assert sonuc.bosaltilan == tuple(sorted([tutmayan.id, sarmalsiz.id, bekleyeni_dolu.id]))
    assert set(sonuc.degismeyen) == {tutan.id, bekleyeni_tutan.id}
    for satir in (tutmayan, sarmalsiz, bekleyeni_dolu):
        assert (hesap_satiri_oku(db, satir.id)[6], hesap_satiri_oku(db, satir.id)[7]) == ("", "")
    assert hesap_satiri_oku(db, tutan.id)[6] == "aa" * 32
    assert hesap_satiri_oku(db, muhursuz.id)[6] == "ff" * 32  # dokunulmadı
    # Onarımın iz satırı YALNIZ değişen alanların adlarını taşır (tasarım §4.6.2), model sırasıyla:
    # bekleyen özeti zaten boş olan satırda bekleyen değişmemiştir.
    onarim = _onarim_satirlari(db, len(satirlar))
    assert {satir[3]: satir[4] for satir in onarim} == {
        tutmayan.id: ["wrap_digest", "seal"],
        sarmalsiz.id: ["wrap_digest", "seal"],
        bekleyeni_dolu.id: ["wrap_digest", "wrap_digest_pending", "seal"],
    }
    with closing(sqlite3.connect(db)) as baglanti:
        for satir in (tutan, bekleyeni_tutan, tutmayan, sarmalsiz, bekleyeni_dolu):
            assert satir_izi.hesap_izi_tutuyor(baglanti, satir.id, TEST_DEK), satir.login_name


def test_izi_tutmayan_geri_yuklenen_satir_onarilmaz_aklanmaz(tmp_path: Path) -> None:
    """Geri yüklenen veritabanında izi tutmayan (yedekten önce geri sarılmış) satıra onarım dokunmaz:
    yeniden mühürleyip iz satırı yazmak onu aklardı. Satır sonra da izini tutmaz."""
    izsiz = HesapSatiri(_MUHASIP, "muhasip", role="muhasip", ozet="dd" * 32, iz=False)

    sonuc, db = _onar(tmp_path, [izsiz], {izsiz.id: "12" * 32})

    assert sonuc.bosaltilan == () and sonuc.degismeyen == ()
    assert hesap_satiri_oku(db, izsiz.id)[6] == "dd" * 32
    assert _onarim_satirlari(db, 0) == []
    with closing(sqlite3.connect(db)) as baglanti:
        assert not satir_izi.hesap_izi_tutuyor(baglanti, izsiz.id, TEST_DEK)


def test_onarim_izi_yazilamazsa_onarim_yapilmaz(tmp_path: Path) -> None:
    """ETKİN iz anahtarı geri yüklenen veritabanında bu DEK'le çözülmüyorsa (satırların izi eski
    anahtarla doğrulanır) onarımın izi yazılamaz: `OnarimYazilamadi` (geri yükleme yarıda kalır),
    satır da değişmez (aynı işlem; izsiz yazım yok)."""
    tutmayan = HesapSatiri(_MUHASIP, "muhasip", role="muhasip", ozet="dd" * 32)
    yeni_db = tmp_path / "yeni.sqlite3"
    yetkili_sqlite(yeni_db, dek=TEST_DEK, hesaplar=[tutmayan], wal=False)
    with closing(sqlite3.connect(yeni_db)) as baglanti:
        baglanti.execute(
            "INSERT INTO okul_auditkey VALUES (2, 'gAAAAbozuk', 100, '2026-11-03 08:00:00', NULL)"
        )
        baglanti.commit()

    with pytest.raises(ozet_onarimi.OnarimYazilamadi):
        ozet_onarimi.ozetleri_onar(
            onceki_db=tmp_path / "yok.sqlite3",
            yeni_db=yeni_db,
            dek=TEST_DEK,
            sarmal_ozetleri={tutmayan.id: "12" * 32},
        )
    assert hesap_satiri_oku(yeni_db, tutmayan.id)[6] == "dd" * 32


def test_derin_ic_ice_guvenlik_dosyasi_turkce_ret_verir() -> None:
    """`json.loads` derin iç içe dizide `RecursionError` yükseltir: `read_state` onu bozuk dosya
    sayar (`AppPasswordError`; aile kuralı `parse_security_state`); kilit ekranının listesi boş,
    kilit açılışı 500 değil Türkçe ret."""
    app_password.state_path().write_text("[" * 50_000 + "]" * 50_000, encoding="utf-8")
    with pytest.raises(app_password.AppPasswordError, match="okunamadı ya da bozuk"):
        app_password.read_state()
    assert app_password.account_wraps() == []
    app_password.lock()
    with pytest.raises(app_password.AppPasswordError):
        app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)


# ============================================================ bağımsız denetim: biçim, soy, derinlik, yarış


def _sifirlanmis_muhasip() -> tuple[str, int, str, dict[str, Any]]:
    """Senaryo 1'in ilk yarısı: muhasip açılır; program yöneticisi parolasını geçici T
    (`UCUNCU_PAROLA`) ile sıfırlar ve hemen satırın kopyasını alır; muhasip T ile girip parolasını
    yeniler (`YENI_PAROLA`); program yöneticisi döner (oturum onundur). (kimlik, sıfırlamanın son
    içerik MAC'li iz satırının sırası, satırın kopyası, T'nin sarmalı) döner."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    hesaplar.reset_password(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA)
    sifirlama = _hesabin_son_kaydi(kimlik)
    kopya, gecici = _kopyala(kimlik), _sarmal(kimlik)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    assert _hesabin_son_kaydi(kimlik) > sifirlama
    return kimlik, sifirlama, kopya, gecici


def test_eski_iz_satirinin_sirasi_blob_yapilinca_giris_acilmaz(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Bağımsız denetim bulgusu (BLOB sıra; `satir_izi` adım 2 "TÜR ŞARTI"): `seq` rowid takma adı
    değildir, program dışından BLOB saklar ve SQLite sıralamasında bütün tamsayılardan büyüktür.
    Senaryo 1'in geri sarmasına ek olarak sıfırlamanın (geri sarılmış satırın eşleştiği) iz
    satırının sırası BLOB'a çevrilir (`CAST(seq AS BLOB)`: aynı baytlar, aynı zincir MAC'i); o satır
    "en yeni" okunsaydı T açardı. Okunan ilk satırın sırası tamsayı değildir: giriş açılmaz
    (`AuditTrailGap`, neden tür, iz boşluğu iletisi; orkestratör maddesi C-4), sayaç artmaz, satır
    değişmez.

    Zincirin başına oturan BLOB sıralı satırda yazıcı (`denetim_izi._ekle`) yazmaz (O-3: Türkçe
    `IzYazilamadi`; eskiden `int(b"…") + 1` sırayı çakıştırıyordu): `BUTUNLUK` satırı yazılamaz,
    olay günlüğe düşer."""
    kimlik, sifirlama, kopya, gecici = _sifirlanmis_muhasip()
    app_password.lock()
    _geri_sar(kimlik, kopya)
    _tetikleyicisiz(
        "UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [sifirlama]
    )
    _geri_koy(gecici)
    once = _ham(kimlik)

    with pytest.raises(app_password.AccountRecordStale) as hata:
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)

    _reddedilir(hata, app_password.IZ_BOSLUGU_MESSAGE, neden=_TUR)
    assert OTURUM.hesap_id() is None and crypto.is_unlocked() is False
    assert _ham(kimlik) == once
    assert app_password.wrap_failure_state(kimlik) == (0, False)
    assert "Hesap kaydının tutmadığı denetim izine yazılamadı." in caplog.text  # bilinen sınır


def test_iz_anahtari_satirinin_sirasi_tamsayi_degilse_hicbir_satir_dogrulanmaz(
    tmp_path: Path,
) -> None:
    """Tür şartı iz anahtarı satırlarına da uygulanır: `valid_from_seq`'i program dışından BLOB'a
    çevrilmiş anahtar satırı yürürlük kuralını güvenilmez kılar; hiçbir hesabın izi doğrulanmaz
    (fail-closed; çıkış yedekten geri yüklemedir)."""
    db = tmp_path / "db.sqlite3"
    yetkili_sqlite(
        db, dek=TEST_DEK, hesaplar=[HesapSatiri(TEST_HESAP_ID, "yonetici", ozet="aa" * 32)]
    )
    with closing(sqlite3.connect(db)) as baglanti:
        assert satir_izi.hesap_izi_tutuyor(baglanti, TEST_HESAP_ID, TEST_DEK)
        baglanti.execute("UPDATE okul_auditkey SET valid_from_seq = CAST(valid_from_seq AS BLOB)")
        baglanti.commit()
        assert not satir_izi.hesap_izi_tutuyor(baglanti, TEST_HESAP_ID, TEST_DEK)
        assert not baglanti.in_transaction  # okuma işlemi kapandı


def _bas_satirini_ekle(kaynak: Path, hedef: Path) -> None:
    """SQLite tarayıcısı taklidi (tek INSERT, kod gerekmez): kaynağın son iz satırı (aynı `seq`,
    aynı `mac`) hedefe BAŞKA bir kayda çevrilmiş olarak eklenir."""
    with closing(sqlite3.connect(kaynak)) as baglanti:
        sutunlar = [str(s[1]) for s in baglanti.execute("PRAGMA table_info(okul_audittrail)")]
        liste = ", ".join(f'"{s}"' for s in sutunlar)
        satir = baglanti.execute(
            f"SELECT {liste} FROM okul_audittrail ORDER BY seq DESC LIMIT 1"  # noqa: S608 — test
        ).fetchone()
    degerler = dict(zip(sutunlar, satir, strict=True))
    degerler["object_id"] = _BASKA_KAYIT
    yer_tutucular = ", ".join("?" * len(sutunlar))
    with closing(sqlite3.connect(hedef)) as baglanti:
        baglanti.execute(
            f"INSERT INTO okul_audittrail ({liste}) VALUES ({yer_tutucular})",  # noqa: S608 — test
            [degerler[s] for s in sutunlar],
        )
        baglanti.commit()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
@pytest.mark.parametrize("yol", ["bas_eklenir", "kayit_cevrilir", "sira_blob"])
def test_sahte_taze_capa_gecici_parolayi_taze_yedege_tasimaz(
    yol: str, sir: str, tmp_path: Path
) -> None:
    """Bağımsız denetim bulguları (sahte tazelik; BLOB sıra): Senaryo 1'in geri yükleme yolu. Taze
    yedek muhasip parolasını yeniledikten SONRA alınır; çapa (güncel veritabanı) program dışından
    şöyle hazırlanır:

    * `bas_eklenir`: sıfırlamadan hemen sonra alınmış düz kopyaya taze yedeğin son iz satırı
      başka bir kayda çevrilerek eklenir (tek INSERT) — çapa "taze" görünür, muhasibin satırı
      kopyanın sıfırlama satırını tutar;
    * `kayit_cevrilir`: güncel veritabanında satır kopyaya geri sarılır, muhasibin sıfırlamadan
      sonraki iz satırları başka kayda çevrilir — çapa gerçekten tazedir;
    * `sira_blob`: güncel veritabanında satır geri sarılır, sıfırlama satırının sırası BLOB'a
      çevrilir.

    T'nin sarmalı geri yüklemeden ÖNCE `guvenlik.json`'a konur. Çapanın muhasip satırı geri
    yüklenen satırdan ESKİ bir iz kaydını tutar (sıra kuralı) ya da sırası tamsayı olmayan bir iz
    satırı okutur (tür şartı): çapa o hesap için kullanılamaz (K-a), dosyadaki T geri yüklenen
    satırın özetini tutmaz, iki özet boşaltılır. T açmaz (K2 "mali kayıtları yalnız muhasip
    girer")."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    hesaplar.reset_password(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA)
    sifirlama = _hesabin_son_kaydi(kimlik)
    eski_kopya_yolu = tmp_path / "eski-kopya.sqlite3"
    goruntu(eski_kopya_yolu)  # program yöneticisi hemen düz kopya alır
    kopya, gecici = _kopyala(kimlik), _sarmal(kimlik)
    app_password.lock()
    app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=YENI_PAROLA)
    app_password.lock()
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
    taze_yolu = tmp_path / "taze-yedek.sqlite3"
    taze_yedek = goruntu(taze_yolu)
    assert Account.objects.get(pk=kimlik).wrap_digest
    if yol == "bas_eklenir":
        _bas_satirini_ekle(taze_yolu, eski_kopya_yolu)
        guncel = eski_kopya_yolu.read_bytes()
    else:
        _geri_sar(kimlik, kopya)
        if yol == "kayit_cevrilir":
            _tetikleyicisiz(
                "UPDATE okul_audittrail SET object_id = %s WHERE model = 'okul.Account' "
                "AND object_id = %s AND seq > %s",
                [_BASKA_KAYIT, kimlik, sifirlama],
            )
        else:
            _tetikleyicisiz(
                "UPDATE okul_audittrail SET seq = CAST(seq AS BLOB) WHERE seq = %s", [sifirlama]
            )
        guncel = goruntu(tmp_path / "guncel.sqlite3")
    _geri_koy(gecici)

    if sir == "parola" and yol != "kayit_cevrilir":
        # Kullanıcı kararı 03.11.2026 "Boşluğu engelle": çapanın izinde boşluk (`bas_eklenir`:
        # yedeğin başı kopyanın başından kopuk bir sırayla eklendi) ya da tamsayı olmayan sıra
        # (`sira_blob`) varsa program yöneticisinin satırı da izini tutmuş sayılmaz — parola yolu
        # daha takastan önce reddedilir, hiçbir dosya değişmez; çıkış kurtarma anahtarıdır.
        with pytest.raises(backup_restore.GeriYuklemeYetkisiz) as ret:
            geri_yukle(tmp_path, taze_yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
        assert ret.value.kod == geri_yukleme_yetkisi.RET_IZ_BOSLUGU
        assert (tmp_path / "canli" / "db.sqlite3").read_bytes() == guncel
        sir = "kurtarma"
    if sir == "parola":
        db = geri_yukle(tmp_path, taze_yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    else:
        db = geri_yukle(tmp_path, taze_yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    satir = hesap_satiri_oku(db, kimlik)
    assert (satir[6], satir[7]) == ("", "")
    _dosyada_hepsi_izli(db)
    programa_al(db)
    app_password.lock()
    with pytest.raises(app_password.WrapDigestMismatch):
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    assert OTURUM.hesap_id() is None
    # Meşru program yöneticisi K-a'dan etkilenmez (parolası yedekten sonra değişmedi).
    assert app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA) is not None


def _derin_iz_satiri(hesap_id: str) -> None:
    """SQLite tarayıcısı taklidi: hesabın kaydına, değerleri derin iç içe bir iz satırı eklenir
    (`key_ref` geçerli anahtar; `json.loads` C tarayıcısıyla açar, Python özyinelemesi kodlayamaz;
    zincir MAC'i önemsiz)."""
    son = AuditTrail.objects.order_by("-seq").values_list("seq", "mac").first()
    assert son is not None
    anahtar = AuditKey.objects.order_by("-valid_from_seq").values_list("pk", flat=True).first()
    derin = "[" * 1300 + "0" + "]" * 1300
    degerler = '{"x": [' + derin + ", 0]}"
    json.loads(degerler)
    _tetikleyicisiz(
        'INSERT INTO okul_audittrail (seq, "at", actor, account_id, role, action, model, '
        'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, prev_mac, '
        "mac) VALUES (%s, %s, 'SISTEM', NULL, '', 'BUTUNLUK', 'okul.Account', %s, '[]', %s, '', "
        "'', 'ACIK', %s, %s, %s)",
        [
            int(son[0]) + 1,
            "2026-11-03 08:00:00",
            hesap_id,
            degerler,
            str(anahtar),
            son[1],
            "a" * 64,
        ],
    )


def test_derin_ic_ice_iz_satiri_girisi_turkce_reddeder() -> None:
    """Bağımsız denetim bulgusu (derinlik): hesabın kaydına eklenmiş derin iç içe değerli bir iz
    satırı zincir MAC'inin kanonik kodlamasında `RecursionError` doğuruyordu (500). Kodlama onu
    `KanonikHata` sayar: satır tutmaz — `AccountRecordStale` ve `BUTUNLUK` (`kayit_mac`)."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    _derin_iz_satiri(kimlik)
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)

    _tek_butunluk(kimlik, son)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
def test_derin_ic_ice_iz_satiri_geri_yuklemeyi_dusurmez(sir: str, tmp_path: Path) -> None:
    """Derin iç içe iz satırı çapada da `RecursionError` değil "tutmuyor"dur: geri yükleme (parola
    ve kurtarma anahtarı yolu; zarfın üçüncü durumunun çıkışı) tamamlanır, çapa o hesap için
    kullanılamaz (K-a): dosyadaki sarmal geri yüklenen satırın özetini tuttuğu için özetler kalır,
    muhasip girer."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    yedek = goruntu(tmp_path / "yedek.sqlite3")
    app_password.lock()
    _derin_iz_satiri(kimlik)
    guncel = goruntu(tmp_path / "guncel.sqlite3")

    if sir == "parola":
        db = geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    else:
        db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    assert hesap_satiri_oku(db, kimlik)[6] == app_password.wrap_digest(TEST_DEK, _sarmal(kimlik))
    programa_al(db)
    assert app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA).id == muhasip.id


def test_derin_ic_ice_iz_satiri_ve_geri_yukleme_notu_girisi_dusurmez() -> None:
    """Geri yükleme notu varken (sahte not da yeter) kilit açılışı iki depoyu karşılaştırır; derin
    iç içe iz satırı bu karşılaştırmayı da düşürmez: program yöneticisi girer, satır "kaydı program
    dışından değiştirilmiş görünen hesaplar"dadır."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    _derin_iz_satiri(kimlik)
    notu = {"surum": geri_yukleme_notu.SURUM, "geri_yuklemeler": [{}], "bekleyen_olaylar": []}
    geri_yukleme_notu.yol(iz_durumu.dizin()).write_text(json.dumps(notu), encoding="utf-8")

    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)

    assert OTURUM.hesap_id() == TEST_HESAP_ID
    assert kimlik in hesaplar.two_store_differences().seal_mismatch


#: SQLite tamsayısından uzun, `int()`'in dönüşüm sınırını (4300 hane) aşan rakam dizisi.
_UZUN_KEY_REF = "1" * 4301


def _uzun_key_ref_li_bas_satiri() -> None:
    """SQLite tarayıcısı taklidi: zincirin başına `key_ref`'i 4301 haneli, açık kipte ilgisiz bir
    kaydın satırı eklenir (zincir MAC'i önemsiz). Kayma denetiminin dayanağı olur."""
    son = AuditTrail.objects.order_by("-seq").values_list("seq", "mac").first()
    assert son is not None
    _tetikleyicisiz(
        'INSERT INTO okul_audittrail (seq, "at", actor, account_id, role, action, model, '
        'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, prev_mac, '
        "mac) VALUES (%s, %s, 'SISTEM', NULL, '', 'GUNCELLE', 'okul.SchoolConfig', '1', '[]', "
        "'{}', '', '', 'ACIK', %s, %s, %s)",
        [int(son[0]) + 1, "2026-11-03 08:00:00", _UZUN_KEY_REF, son[1], "a" * 64],
    )


def test_uzun_rakam_dizisi_anahtar_basvurusu_degildir() -> None:
    """Son sınama bulgusu: `int()` 4300 haneden uzun metinde `ValueError` verir. SQLite
    tamsayısından (19 hane) uzun başvuru biçimsizdir; doğrulama istisnayla yarıda kesilmez."""
    assert denetim_izi.acik_ref_coz(_UZUN_KEY_REF) is None
    assert denetim_izi.acik_ref_coz("1" * 20) is None
    assert denetim_izi.acik_ref_coz("1" * 19) == int("1" * 19)
    assert denetim_izi.kilitli_ref_coz(f"{_UZUN_KEY_REF}:1") is None
    assert denetim_izi.kilitli_ref_coz(f"1:{_UZUN_KEY_REF}") is None


def test_uzun_key_ref_li_bas_satiri_girisi_dusurmez() -> None:
    """Son sınama bulgusu: zincir başının `key_ref`'i 4301 hane olunca kayma denetimi ham
    `ValueError` (500) veriyordu, bütün hesapların girişi tek hücreyle düşüyordu. Başvuru
    biçimsizdir: dayanağın MAC'i doğrulanamaz, kayma işareti değildir ("İZ BOŞLUĞU" (c)); giriş
    açılır, satır son 200 satırın doğrulamasında bulgu olur."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    _uzun_key_ref_li_bas_satiri()

    assert app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA).id == muhasip.id
    assert OTURUM.hesap_id() == kimlik


def test_hesabin_son_kaydinin_uzun_key_ref_i_satiri_tutmaz() -> None:
    """Hesabın KENDİ son iz satırının `key_ref`'i 4301 hane: satırı mühürleyen İA bulunamaz, satır
    tutmaz — `AccountRecordStale` ve tek `BUTUNLUK` (`kayit_mac`); `ValueError` değil."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    app_password.lock()
    _tetikleyicisiz(
        "UPDATE okul_audittrail SET key_ref = %s WHERE seq = %s",
        [_UZUN_KEY_REF, _hesabin_son_kaydi(kimlik)],
    )
    son = _son_seq()

    with pytest.raises(app_password.AccountRecordStale):
        app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA)

    _tek_butunluk(kimlik, son)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("sir", ["parola", "kurtarma"])
def test_uzun_key_ref_li_bas_satiri_geri_yuklemeyi_dusurmez(sir: str, tmp_path: Path) -> None:
    """Son sınama bulgusu: aynı hücre geri yükleme yetkisini ve özet onarımının çapasını da ham
    `ValueError`'la düşürüyor, kurtarma anahtarıyla geri yükleme dahil (kullanıcı kararındaki
    çıkış) hiçbir geri yükleme tamamlanmıyordu. Artık iki yol da tamamlanır, muhasip girer."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    yedek = goruntu(tmp_path / "yedek.sqlite3")
    app_password.lock()
    _uzun_key_ref_li_bas_satiri()
    guncel = goruntu(tmp_path / "guncel.sqlite3")

    if sir == "parola":
        db = geri_yukle(tmp_path, yedek, guncel, hesap="yonetici", password=TEST_PAROLA)
    else:
        db = geri_yukle(tmp_path, yedek, guncel, recovery_key=TEST_KURTARMA_ANAHTARI)

    programa_al(db)
    assert app_password.unlock(hesap_id=kimlik, password=GECICI_PAROLA).id == muhasip.id


def test_satirin_izi_kararin_verildigi_hale_baglidir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bağımsız denetim bulgusu (denetim ile kullanım ayrı anlıklarda): kilit açılışı satırı ORM'le
    okur (özet ve durum o kopyadan), izini ayrı bir okumayla doğrular. Bir betik iki okuma arasında
    satırı geri sarılmış hâlden (T'nin özeti) güncel hâle çevirirse güncel hâlin izi tutar, karar
    ise eski kopyadan verilirdi (T açardı). Beklenen mühür iki okumayı aynı hâle bağlar: ilk denetim
    tutmaz, yanlış alarm ayıklaması güncel satırı döndürür, karar ondan verilir — T'nin özeti
    tutmaz (`WrapDigestMismatch`), giriş açılmaz."""
    kimlik, _sifirlama, kopya, gecici = _sifirlanmis_muhasip()
    guncel = _kopyala(kimlik)
    app_password.lock()
    _geri_sar(kimlik, kopya)
    _geri_koy(gecici)
    gercek = denetim_izi.hesap_izi_tutuyor
    cagri = {"sayi": 0}

    def araya_gir(hesap_id: Any, **secenekler: Any) -> bool:
        cagri["sayi"] += 1
        if cagri["sayi"] == 1:
            _geri_sar(kimlik, guncel)  # betik: ORM okumasından sonra satır güncel hâle döner
        return gercek(hesap_id, **secenekler)

    monkeypatch.setattr(denetim_izi, "hesap_izi_tutuyor", araya_gir)
    with pytest.raises(app_password.WrapDigestMismatch):
        app_password.unlock(hesap_id=kimlik, password=UCUNCU_PAROLA, new_password=_SONRAKI_PAROLA)
    assert cagri["sayi"] >= 2 and OTURUM.hesap_id() is None


def test_eszamanli_askidan_cikarma_yanlis_alarm_vermez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bağımsız denetim bulgusu (yanlış alarm): çift tıklanan "askıdan çıkar". İkinci istek satırı
    `ASKIDA` okur; satırın izi denetlenmeden önce birinci istek satırı askıdan çıkarıp commit eder
    (meşru yazım: satır ve iz satırı birlikte). Mühür değişmiştir, ilk denetim tutmaz; yazıcılarla
    sıralı işlemde yinelenen denetim güncel satırın izini tutar bulur: ikinci istek güncel satırla
    sürer (askıda değil; yalnız dosyadaki sayaç sıfırlanır), silinemez bir `BUTUNLUK` satırı
    düşmez."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    muhurle(
        Account.objects.get(pk=kimlik),
        status=AccountStatus.ASKIDA,
        suspend_reason=SuspendReason.GOREV_BOLUMU,
    )
    gercek = denetim_izi.hesap_izi_tutuyor
    tetik = {"oldu": False}

    def araya_gir(hesap_id: Any, **secenekler: Any) -> bool:
        if not tetik["oldu"] and str(hesap_id) == kimlik:
            tetik["oldu"] = True
            hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)  # birinci istek
        return gercek(hesap_id, **secenekler)

    monkeypatch.setattr(denetim_izi, "hesap_izi_tutuyor", araya_gir)
    son = _son_seq()
    hesap = hesaplar.unsuspend(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)  # ikinci istek

    assert tetik["oldu"] and hesap.status == AccountStatus.ACIK
    assert not AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BUTUNLUK).exists()
    _hepsi_izli()


def test_eszamanli_kapatilan_hesap_sifirlanmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Yanlış alarm ayıklamasının döndürdüğü güncel satır kararın satırıdır: parola sıfırlaması
    hesabı `ACIK` okur; satırın izi denetlenmeden önce başka bir istek hesabı kapatır (meşru yazım).
    Ayıklama güncel (`KAPALI`) satırı döndürür, işlem gören yeniden sınanır: sıfırlama kapalı hesabı
    yeniden açmaz (servisin kapalı hesap iletisi), `BUTUNLUK` satırı düşmez."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    gercek = denetim_izi.hesap_izi_tutuyor
    tetik = {"oldu": False}

    def araya_gir(hesap_id: Any, **secenekler: Any) -> bool:
        if not tetik["oldu"] and str(hesap_id) == kimlik:
            tetik["oldu"] = True
            hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik)  # öteki istek
        return gercek(hesap_id, **secenekler)

    monkeypatch.setattr(denetim_izi, "hesap_izi_tutuyor", araya_gir)
    son = _son_seq()
    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesaplar.reset_password(
            by_hesap_id=TEST_HESAP_ID, hesap_id=kimlik, temp_password=UCUNCU_PAROLA
        )

    assert tetik["oldu"] and str(hata.value) == hesaplar._CLOSED_MESSAGE
    assert Account.objects.get(pk=kimlik).status == AccountStatus.KAPALI
    assert not AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BUTUNLUK).exists()


def _denetimden_once_askiya_al(monkeypatch: pytest.MonkeyPatch, kimlik: str) -> dict[str, bool]:
    """Hesabın satırı ORM'le okunduktan sonra, izi denetlenmeden önce askıya alınır (meşru, izli
    yazım; görev bölümü)."""
    gercek = denetim_izi.hesap_izi_tutuyor
    tetik = {"oldu": False}

    def araya_gir(hesap_id: Any, **secenekler: Any) -> bool:
        if not tetik["oldu"] and str(hesap_id) == kimlik:
            tetik["oldu"] = True
            muhurle(
                Account.objects.get(pk=kimlik),
                status=AccountStatus.ASKIDA,
                suspend_reason=SuspendReason.GOREV_BOLUMU,
            )
        return gercek(hesap_id, **secenekler)

    monkeypatch.setattr(denetim_izi, "hesap_izi_tutuyor", araya_gir)
    return tetik


def test_eszamanli_askiya_alinan_islemi_yapan_hesap_islemi_yapamaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """İşlemi yapanın satırı da güncel hâlden yeniden sınanır (`hesaplar._actor`): program
    yöneticisi hesap açarken satırı askıya alınırsa (izi denetlenmeden önce) ayıklama güncel
    (`ASKIDA`) satırı döndürür, işlem yapılmaz (servisin işlemi yapan iletisi)."""
    tetik = _denetimden_once_askiya_al(monkeypatch, TEST_HESAP_ID)
    hesap_sayisi = Account.objects.count()

    with pytest.raises(hesaplar.AccountServiceError) as hata:
        hesap_ac()

    assert tetik["oldu"] and str(hata.value) == hesaplar._ACTOR_MESSAGE
    assert Account.objects.count() == hesap_sayisi


def test_eszamanli_askiya_alinan_yonetici_kurtarma_anahtariyla_acilmaz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kurtarma anahtarıyla açılış rolü ve durumu doğrulanmış (dönen) satırda yeniden sorar: ikinci
    program yöneticisinin satırı izi denetlenmeden önce askıya alınırsa kurtarma onu açmaz (askıyı
    `ACIK`'a çevirmez), sarmal yazılmaz."""
    ikinci = _ikinci_yonetici()
    kimlik = str(ikinci.id)
    app_password.lock()
    sarmal = _sarmal(kimlik)
    tetik = _denetimden_once_askiya_al(monkeypatch, kimlik)

    with pytest.raises(app_password.AppPasswordError) as hata:
        app_password.unlock_with_recovery(
            recovery_key=TEST_KURTARMA_ANAHTARI, hesap_id=kimlik, new_password=_SONRAKI_PAROLA
        )

    assert tetik["oldu"] and str(hata.value) == app_password._RECOVERY_ONLY_ADMIN_MESSAGE
    assert OTURUM.hesap_id() is None
    assert Account.objects.get(pk=kimlik).status == AccountStatus.ASKIDA
    assert _sarmal(kimlik) == sarmal


@pytest.mark.django_db(transaction=True)
def test_satirin_izi_tek_anlik_goruntude_okunur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bağımsız denetim bulgusu (yanlış alarm): satır, iz anahtarları ve iz satırları ayrı
    deyimlerle okunuyordu; WAL kipinde her deyim kendi anlık görüntüsünü görür. Satır okunduktan
    hemen sonra başka bir iş parçacığı aynı hesaba meşru bir yazım commit eder (satır + son hâlin iz
    satırı): okumalar tek okuma işleminde olduğu için denetim eski satırı eski iziyle karşılaştırır,
    tutar der (yanlış "tutmuyor" yok); bağlantıda açık işlem kalmaz."""
    muhasip = _acik_muhasip()
    kimlik = str(muhasip.id)
    gercek = satir_izi._hesap_satiri
    tetik = {"oldu": False}
    hatalar: list[BaseException] = []

    def yazici() -> None:
        try:
            hesap = Account.objects.get(pk=kimlik)
            with sistem_olarak(), transaction.atomic():
                app_password.write_wrap_digests(
                    hesap, TEST_DEK, asil=hesap.wrap_digest, bekleyen="ab" * 32
                )
        except BaseException as exc:  # noqa: BLE001 — iş parçacığının hatası teste taşınır
            hatalar.append(exc)
        finally:
            connections.close_all()

    def araya_gir(baglanti: Any, hesap_kimligi: str) -> Any:
        ham = gercek(baglanti, hesap_kimligi)
        if not tetik["oldu"] and threading.current_thread() is threading.main_thread():
            tetik["oldu"] = True
            is_parcacigi = threading.Thread(target=yazici)
            is_parcacigi.start()
            is_parcacigi.join()
        return ham

    monkeypatch.setattr(satir_izi, "_hesap_satiri", araya_gir)
    assert denetim_izi.hesap_izi_tutuyor(kimlik, veri_anahtari=TEST_DEK)
    monkeypatch.undo()

    assert tetik["oldu"] and hatalar == []
    assert not connection.connection.in_transaction
    assert Account.objects.get(pk=kimlik).wrap_digest_pending == "ab" * 32  # yazım commit edildi
    assert denetim_izi.hesap_izi_tutuyor(kimlik, veri_anahtari=TEST_DEK)


@pytest.mark.django_db(transaction=True)
def test_cift_gonderilen_giris_yanlis_alarm_vermez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bağımsız denetim bulgusu (yanlış alarm): "Aç" düğmesine çift gönderim — iki eşzamanlı kilit
    açılışı. Birincisi, ikincinin satır okuması ile iz okuması arasında oturumu açar (`GIRIS`
    yazımı). İkincisi `AccountRecordStale` almaz; hesabın `BUTUNLUK` satırı düşmez."""
    app_password.lock()
    gercek = satir_izi._hesap_satiri
    tetik = {"oldu": False}
    hatalar: list[BaseException] = []

    def birinci_istek() -> None:
        try:
            app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)
        except BaseException as exc:  # noqa: BLE001 — iş parçacığının hatası teste taşınır
            hatalar.append(exc)
        finally:
            connections.close_all()

    def araya_gir(baglanti: Any, hesap_kimligi: str) -> Any:
        ham = gercek(baglanti, hesap_kimligi)
        if not tetik["oldu"] and threading.current_thread() is threading.main_thread():
            tetik["oldu"] = True
            is_parcacigi = threading.Thread(target=birinci_istek)
            is_parcacigi.start()
            is_parcacigi.join()
        return ham

    monkeypatch.setattr(satir_izi, "_hesap_satiri", araya_gir)
    app_password.unlock(hesap_id=TEST_HESAP_ID, password=TEST_PAROLA)  # ikinci istek
    monkeypatch.undo()

    assert tetik["oldu"] and hatalar == []
    assert OTURUM.hesap_id() == TEST_HESAP_ID
    assert not AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK, object_id=TEST_HESAP_ID
    ).exists()
