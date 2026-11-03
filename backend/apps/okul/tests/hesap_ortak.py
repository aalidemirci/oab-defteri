"""Hesap testlerinin ortak yardımcıları (toplanmaz: dosya adı `test_` ile başlamaz).

Varsayılan ortam `backend/conftest.py`'dedir. Buradaki yardımcılar kilit AÇIKKEN
ve `yonetici_hesabi` fixtürü kuruluyken çağrılır (hesap servisleri DEK ve işlemi
yapan açık hesap ister). Adlar uydurmadır; gerçek kişi değildir.
"""

from __future__ import annotations

import base64
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from django.db import connection, transaction

from apps.okul import denetim_izi
from apps.okul.models import Account, AccountRole, AuditAction
from apps.okul.oturum import sistem_olarak, yazar
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
) -> Account:
    """Varsayılan program yöneticisiyle yeni hesap açar (`PAROLA_YENILENMELI`)."""
    return hesaplar.open_account(
        by_hesap_id=TEST_HESAP_ID,
        role=role,
        tanitici=tanitici or hesaplar.default_login_name(role),
        display_name=ad,
        temp_password=parola,
    )


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
