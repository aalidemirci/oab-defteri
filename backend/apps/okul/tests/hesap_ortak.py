"""Hesap testlerinin ortak yardımcıları (toplanmaz: dosya adı `test_` ile başlamaz).

Varsayılan ortam `backend/conftest.py`'dedir. Buradaki yardımcılar kilit AÇIKKEN
ve `yonetici_hesabi` fixtürü kuruluyken çağrılır (hesap servisleri DEK ve işlemi
yapan açık hesap ister). Adlar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

import base64
import itertools
import json
from contextlib import nullcontext
from datetime import date
from pathlib import Path
from typing import Any

from django.db import connection, transaction
from django.utils import timezone

from apps.okul import denetim_izi
from apps.okul.models import Account, AccountRole, AccountStatus, AuditAction, SchoolYear
from apps.okul.oturum import Yazar, sistem_olarak, yazar, yazar_olarak
from apps.okul.services import app_password, hesaplar
from conftest import TEST_DEK, TEST_HESAP_ID, TEST_IA
from shared import crypto

GECICI_PAROLA = "Gecici-Parola-1"
YENI_PAROLA = "Yeni-Parola-2!"
UCUNCU_PAROLA = "Ucuncu-Parola-3?"


def hesap_ac(
    role: str = AccountRole.MUHASIP,
    *,
    tanitici: str | None = None,
    ad: str = "Örnek Muhasip",
    parola: str = GECICI_PAROLA,
    uyelik: Any = None,
) -> Account:
    """Varsayılan program yöneticisiyle yeni hesap açar (`PAROLA_YENILENMELI`).

    Organ rolünde hesap üyeliğe bağlı açılır (plan F1c 7. adım): `uyelik` verilmezse
    `hesap_uyeligi` bulur ya da kurar (kilitliyken kurmaz: hesap açma kilit iletisiyle reddeder)."""
    if uyelik is None and role in hesaplar.ORGAN_ROLLERI and crypto.is_unlocked():
        uyelik = hesap_uyeligi(role)
    return hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=role,
        tanitici=tanitici or hesaplar.default_login_name(role),
        display_name=ad,
        temp_password=parola,
        uyelik=None if uyelik is None else getattr(uyelik, "pk", uyelik),
    )


#: Fabrikanın açtığı dönemin günü ve ders yılı (`apps.oab.tests.uyelik_ortak` ile aynı değerler:
#: oradaki `donem()` açık dönemi yeniden kullanır).
FABRIKA_DONEM_GUNU = date(2026, 10, 10)
_FABRIKA_SIRASI = itertools.count(1)
_AD_HARFLERI = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"


def _fabrika_eki() -> str:
    """Adaşlık sorusu çıkmasın diye her kişiye ayrı harf dizisi (rakamsız)."""
    sayi, harfler = next(_FABRIKA_SIRASI), ""
    while sayi:
        sayi, kalan = divmod(sayi - 1, len(_AD_HARFLERI))
        harfler = _AD_HARFLERI[kalan] + harfler
    return harfler


def fabrika_donemi() -> Any:
    """Açık birlik dönemi; yoksa uydurma ders yılıyla açılır (program yöneticisi adına)."""
    from apps.oab.models import OabTerm, TermStatus
    from apps.oab.services import donemler

    donem = OabTerm.objects.filter(status=TermStatus.ACIK).first()
    if donem is not None:
        return donem
    yil = SchoolYear.objects.filter(is_active=True).first() or SchoolYear.objects.create(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), is_active=True
    )
    with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol=AccountRole.YONETICI.value)):
        return donemler.create_term(
            name="2026-2027 birlik dönemi", school_year=yil, start_date=FABRIKA_DONEM_GUNU
        )


def hesap_uyeligi(role: str) -> Any:
    """Organ rolündeki hesabın bağlanacağı üyelik (F1b fabrikalarının bağı; plan F1c 7. adım).

    Açık dönemde (yoksa `fabrika_donemi`) önce rolün açık hesaba bağlı olmayan uygun üyeliği
    (`hesap_baglari.uygun_uyelikler`'in kuralı). Yoksa yönetim kurulu rolünde görevi taşıyan üye
    (görev tekildir), Denetleme Kurulunda kurul doluysa (bir veli, iki öğretmen; md. 14/1, sert)
    görevdeki ilk asıl: ikisi de bağlıdır, hesap açma rolün sınırıyla ya da üyeliğin açık hesabıyla
    reddeder. Kurulda yer varsa uydurma kişiyle devralınan görevli üyelik açılır (geçiş kurulumunun
    kaydı, tasarım §7.9): yönetim kurulunda veli asıl, Denetleme Kurulunda boş koltuğun grubu
    (önce veli, sonra öğretmen). Yazar program yöneticisidir.
    """
    from apps.oab import selectors
    from apps.oab.models import ElectedBy, MembershipSource, OrganType, PersonKind, SeatGroup
    from apps.oab.services import hesap_baglari, kisiler, uyelikler

    donem = fabrika_donemi()
    with yazar_olarak(Yazar(hesap_id=TEST_HESAP_ID, rol=AccountRole.YONETICI.value)):
        uygun = hesap_baglari.uygun_uyelikler(role)
        if uygun:
            return uygun[0]["uyelik"]
        gorev = hesap_baglari.ROL_GOREVLERI.get(role)
        organ = OrganType.YONETIM_KURULU if gorev is not None else OrganType.DENETLEME_KURULU
        gorevdekiler = selectors.gorevdeki_asillar(donem, organ)
        if gorev is not None:
            for mevcut in gorevdekiler:
                if mevcut.role == gorev:
                    return mevcut.pk
            grup = ""
        else:
            veli_var = any(u.seat_group == SeatGroup.VELI for u in gorevdekiler)
            if len(gorevdekiler) >= 3:
                return gorevdekiler[0].pk
            grup = SeatGroup.OGRETMEN if veli_var else SeatGroup.VELI
        ogretmen = grup == SeatGroup.OGRETMEN
        kisi = kisiler.create_person(
            kind=PersonKind.OGRETMEN if ogretmen else PersonKind.VELI,
            first_name=f"Uydurma {_fabrika_eki()}",
            last_name="Hesapoğlu",
            is_parent=not ogretmen,
            ayni_kisi_degil=True,
        )
        return uyelikler.assign_membership(
            term=donem,
            person=kisi,
            organ=organ,
            seat_type="ASIL",
            seat_group=grup,
            role=gorev or "UYE",
            elected_by=ElectedBy.OGRETMENLER_KURULU if ogretmen else ElectedBy.GENEL_KURUL,
            source=MembershipSource.DEVRALINAN,
            start_date=FABRIKA_DONEM_GUNU,
        ).pk


def rol_hesabi(role: str, *, ad: str = "Uydurma Hesap") -> Account:
    """YALNIZ ROL OTURUMU İÇİN açık (`ACIK`) hesap satırı: mühürlü, izli, BAĞSIZ.

    Yetki testleri rolün oturumunu ister; sınadıkları kurula görevli eklemek (hesap açmanın üyelik
    bağı) kadroyu ve görev bölümünün katılım listesini değiştirirdi. Satır `conftest.yonetici_hesabi`
    gibi doğrudan, `HESAP` satırıyla aynı işlemde yazılır (meşru program yazımı gibi; sarmal yok).
    Bağ kuralı burada sınanmaz: `hesap_ac` ve `test_hesap_baglari.py` sınar (plan F1c 7. adım).
    """
    kilitliydi = not crypto.is_unlocked()
    if kilitliydi:
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
    try:
        simdi = timezone.now()
        hesap = Account(
            login_name=hesaplar.default_login_name(role),
            role=role,
            display_name=ad,
            status=AccountStatus.ACIK,
            opened_at=simdi,
            password_changed_at=simdi,
        )
        baglam = sistem_olarak() if yazar() is None else nullcontext()
        with baglam, transaction.atomic():
            hesap.seal = hesap.compute_seal(TEST_DEK)
            hesap.save(force_insert=True)
            denetim_izi.kayit(
                AuditAction.HESAP, hesap, onceki=None, anahtar=denetim_izi.anahtari_coz(TEST_DEK)
            )
    finally:
        if kilitliydi:
            crypto.unload_key()
    return hesap


def muhurle(hesap: Account, **alanlar: Any) -> Account:
    """Alanları yazar, satırı test DEK'iyle YENİDEN mühürler ve `HESAP` iz satırını yazar.

    Meşru program yazımı gibidir: satır ve satırın son hâlinin içerik MAC'ini taşıyan iz satırı
    aynı işlemde (kullanıcı kararı 03.11.2026 "Girişte reddet": izi tutmayan satır giriş açmaz;
    `app_password` modül başlığı "SATIRIN İZİ"). Yazar o anki bağlamdır, yoksa `SISTEM`. Kilitli
    bir testte de çağrılabilsin diye DEK ve İA geçici olarak yüklenir (içerik MAC'i çözülmüş adı
    ister), önceki hâl korunur. Program DIŞINDAN yazım taklidi `ham_guncelle`'dir.
    """
    kilitliydi = not crypto.is_unlocked()
    if kilitliydi:
        crypto.load_key(TEST_DEK, audit_key=TEST_IA)
    try:
        baglam = sistem_olarak() if yazar() is None else nullcontext()
        with baglam, transaction.atomic():
            onceki = denetim_izi.anlik(hesap)
            for ad, deger in alanlar.items():
                setattr(hesap, ad, deger)
            hesap.seal = hesap.compute_seal(TEST_DEK)
            hesap.save(update_fields=[*alanlar, "seal"])
            denetim_izi.kayit(
                AuditAction.HESAP,
                hesap,
                onceki=onceki,
                anahtar=denetim_izi.anahtari_coz(TEST_DEK),
            )
    finally:
        if kilitliydi:
            crypto.unload_key()
    return hesap


def ham_guncelle(hesap_id: object, **alanlar: Any) -> None:
    """Program DIŞINDAN yazım taklidi: ham SQL, mühür yenilenmez (tehdit 19)."""
    atamalar = ", ".join(f"{ad} = %s" for ad in alanlar)
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE okul_account SET {atamalar} WHERE id = %s",  # noqa: S608 — test, sabit adlar
            [*alanlar.values(), str(hesap_id).replace("-", "")],
        )


def ham_satir(hesap_id: object) -> dict[str, Any]:
    """`okul_account` satırını ORM'siz okur (mühür, durum, tanıtıcı)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT login_name, role, status, seal, last_login_at FROM okul_account WHERE id = %s",
            [str(hesap_id).replace("-", "")],
        )
        satir = cursor.fetchone()
    assert satir is not None
    return dict(zip(("login_name", "role", "status", "seal", "last_login_at"), satir, strict=True))


def durum() -> dict[str, Any]:
    veri = app_password.read_state()
    assert veri is not None
    return veri


def sarmal_kimlikleri() -> list[str]:
    return [str(h["id"]) for h in durum()["hesaplar"]]


def sarmal(hesap_id: object) -> dict[str, Any]:
    for hesap in durum()["hesaplar"]:
        if hesap["id"] == str(hesap_id):
            return dict(hesap)
    raise AssertionError(f"sarmal yok: {hesap_id}")


def durum_yaz(veri: dict[str, Any]) -> None:
    app_password._write_state(veri)


def bagsiz_sarmal(
    hesap_id: object, tanitici: str, parola: str, *, dek: bytes = TEST_DEK
) -> dict[str, Any]:
    """F1b-1'in BAĞSIZ hesap sarmalı (eski dosya taklidi): anahtar `Argon2id(parola, tuz)`'un
    kendisidir, kimlik türetime girmez, `turetim` alanı yoktur. Program artık böyle sarmal
    YAZMAZ ve AÇMAZ (`app_password` modül başlığı "HESAP SARMALI KİMLİĞE BAĞLIDIR")."""
    tuz = crypto.new_salt()
    anahtar = crypto.derive_key(parola, salt=tuz, params=app_password._kdf_of(durum()))
    return {
        "id": str(hesap_id),
        "tanitici": tanitici,
        "salt": base64.b64encode(tuz).decode("ascii"),
        "sarmal": crypto.wrap_key(dek, wrapping_key=anahtar),
        "hatali": 0,
        "askida": False,
    }


def arsivler() -> list[Path]:
    return sorted(app_password.state_path().parent.glob("guvenlik-arsiv-*.json"))


def arsiv_yaz(ad: str, veri: dict[str, Any]) -> Path:
    yol = app_password.state_path().with_name(f"guvenlik-arsiv-{ad}.json")
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return yol


def arsivdeki_kimlikler(yol: Path) -> list[str]:
    veri = json.loads(yol.read_text(encoding="utf-8"))
    return [str(h["id"]) for h in veri.get("hesaplar", [])]


# ============================================================ program dışı değişiklik taklitleri
#: (Kullanıcılar uçlarının ve hesap teslim pusulasının testleri; F1b-2 c1'den taşındı.)


def iz_tetikleyicisiz(sql: str, params: list[Any]) -> None:
    """Program DIŞINDAN iz tablosu düzenlemesi (SQLite tarayıcısı taklidi; tetikleyiciler bu
    işlemde düşürülür, sonra aynen kurulur)."""
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'okul_audittrail'"
        )
        tetikleyiciler = cursor.fetchall()
        for ad, _ in tetikleyiciler:
            cursor.execute(f'DROP TRIGGER "{ad}"')
        cursor.execute(sql, params)
        for _, tanim in tetikleyiciler:
            cursor.execute(tanim)


def iz_dolgusu(adet: int) -> list[int]:
    """Programın meşru yazdığı, hesaplarla ilgisiz açık kip satırları; sıraları."""
    siralar: list[int] = []
    for _ in range(adet):
        with sistem_olarak(), transaction.atomic():
            siralar.append(
                int(denetim_izi.olay(AuditAction.HESAP, model="okul.Deneme", object_id="dolgu").seq)
            )
    return siralar


def geri_sarilmis(hesap: Account) -> Account:
    """Satırın izi tutmaz: satırın baytları kopyalanır, meşru bir yazım (izli) yapılır, satır
    kopyaya geri sarılır (mühür tutar, son iz kaydı tutmaz; `satir_izi` "SORUN")."""
    tablo = f"kopya_{str(hesap.id).replace('-', '')}"
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TEMP TABLE {tablo} AS SELECT * FROM okul_account WHERE id = %s",  # noqa: S608
            [str(hesap.id).replace("-", "")],
        )
    muhurle(Account.objects.get(pk=hesap.id), reset_notice_pending=True, status=hesap.status)
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM pragma_table_info('okul_account') WHERE name != 'id'")
        adlar = ", ".join(f'"{ad}"' for (ad,) in cursor.fetchall())
        cursor.execute(
            f"UPDATE okul_account SET ({adlar}) = (SELECT {adlar} FROM {tablo}) "  # noqa: S608
            "WHERE id = %s",
            [str(hesap.id).replace("-", "")],
        )
    return Account.objects.get(pk=hesap.id)


def izde_bosluk_sonra_yoneticiyi_tazele() -> None:
    """İzden ilgisiz bir satır silinir (iz boşluğu); program yöneticisinin kaydı boşluktan SONRA
    meşru bir yazımla tazelenir (oturumdaki hesap boşluktan etkilenmez, son kaydı eski hesaplar
    etkilenir)."""
    dolgu = iz_dolgusu(3)
    iz_tetikleyicisiz("DELETE FROM okul_audittrail WHERE seq = %s", [dolgu[1]])
    muhurle(Account.objects.get(pk=TEST_HESAP_ID), password_changed_at=timezone.now())
