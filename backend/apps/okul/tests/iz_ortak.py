"""Denetim izi testlerinin ortak yardımcıları: bekçilerin model kümesi ve program DIŞINDAN satır taklidi.

Bekçilerin (izsiz yazım kapısı, alan sınıflaması, uydurma veri araması) model kümesi `bekci_modelleri`
ile gelir: `okul` ve `oab`. Uygulama adı dizedir: `okul` kodu `oab`'yi içe aktarmaz (plan "F1c adımları").

Sırrı olmayan biri (veri dosyasına yazabilen ama İA'yı ve `iz-durumu.json`'daki tohumu
bilmeyen) zincirin sonuna satır ekleyebilir: herkesin bildiği mühürsüz anahtarla
(`kanonik.MUHURSUZ_ANAHTAR`) MAC'i doğru hesaplar, veritabanı kısıtlarını dışarıdaki bir
`sqlite3` bağlantısında `PRAGMA ignore_check_constraints = ON` ile kapatır. Tetikleyiciler
yalnız güncellemeyi ve silmeyi keser; ekleme serbesttir. Doğrulama bu satırı türünün ve
kipinin kuralıyla yakalamalıdır (`denetim_izi.satir_kurali_tutuyor`).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from django.apps import apps as django_apps
from django.db import connection
from django.db.models import Model

from apps.okul import denetim_izi
from apps.okul.models import AuditTrail
from shared import kanonik

#: Denetim izi bekçilerinin kapsadığı uygulamalar.
IZ_UYGULAMALARI = ("okul", "oab")


def bekci_modelleri() -> list[type[Model]]:
    """Bekçilerin kapsadığı uygulamaların bütün modelleri."""
    return [
        model for ad in IZ_UYGULAMALARI for model in django_apps.get_app_config(ad).get_models()
    ]


def izlenen_modeller() -> list[type[Model]]:
    """Denetim izi listelerini taşıyan modeller (taşımayanı `LISTESIZ_MODELLER` adıyla sayar)."""
    return [model for model in bekci_modelleri() if hasattr(model, "IZ_DEGER_ALANLARI")]


def kor_indeks_alanlari(model: type[Model]) -> set[str]:
    """Kör indeks sütunları (`name_index` gibi `*_index` adlı alanlar).

    Kör indeks şifreli değildir, ama aday sözlüğüyle kişiyi ele verir: şifreli alan gibi korunur.
    """
    return {alan.name for alan in model._meta.fields if alan.name.endswith("_index")}


#: Sahte satırın anı (UTC); veritabanına saat dilimsiz UTC metni olarak girer.
SAHTE_AN = datetime(2026, 11, 1, 7, 30, tzinfo=UTC)


def sahte_satir(
    *,
    kisitsiz: bool = True,
    ham: dict[str, Any] | None = None,
    prev_mac: str | None = None,
    **alanlar: Any,
) -> AuditTrail:
    """Zincirin sonuna mühürsüz anahtarla MAC'i doğru bir satır ekler; satırı döndürür.

    Varsayılan satır kapalı kümedeki bir `SISTEM` yedek olayıdır (kurallara uyar); `alanlar`
    onu değiştirir (`account` tireli kimlik metnidir). `kisitsiz` doğruysa veritabanı
    kısıtları ekleme süresince kapatılır. `ham` MAC hesaplandıktan SONRA sütunların ham
    değerini değiştirir (ör. `{"account_id": "zzz"}`: Django'nun dönüştürücüsünün düştüğü
    biçimsiz değer); satır o zaman sütun dönüşümü düşmeden okunur (`denetim_izi.satirlari_oku`).
    `prev_mac` verilirse zincir başının MAC'i yerine o kullanılır (zincir başının `mac`'i ikili
    değerken, ardına biçimi doğru bir satır eklemek için).
    """
    bas = denetim_izi.zincir_basi()
    seq = 1 if bas is None else bas[0] + 1
    if prev_mac is None:
        prev_mac = "" if bas is None else bas[1]
    hesap = alanlar.pop("account", None)
    taslak = AuditTrail(
        seq=seq,
        at=SAHTE_AN,
        actor=alanlar.pop("actor", "SISTEM"),
        account_id=None if hesap is None else str(uuid.UUID(str(hesap))),
        role=alanlar.pop("role", ""),
        action=alanlar.pop("action", "YEDEK"),
        model=alanlar.pop("model", denetim_izi.YEDEK_DOSYASI),
        object_id=alanlar.pop("object_id", ""),
        changed_fields=alanlar.pop("changed_fields", []),
        values=alanlar.pop("values", {}),
        record_mac=alanlar.pop("record_mac", ""),
        label=alanlar.pop("label", ""),
        key_mode=alanlar.pop("key_mode", "KILITLI"),
        key_ref=alanlar.pop("key_ref", ""),
        prev_mac=prev_mac,
    )
    assert not alanlar, alanlar
    mac = kanonik.iz_mac(kanonik.MUHURSUZ_ANAHTAR, denetim_izi.satir_alanlari(taslak), prev_mac)
    sutunlar: dict[str, Any] = {
        "seq": seq,
        "at": SAHTE_AN.strftime("%Y-%m-%d %H:%M:%S"),
        "actor": taslak.actor,
        "account_id": None if hesap is None else uuid.UUID(str(hesap)).hex,
        "role": taslak.role,
        "action": taslak.action,
        "model": taslak.model,
        "object_id": taslak.object_id,
        "changed_fields": json.dumps(taslak.changed_fields),
        "values": json.dumps(taslak.values),
        "record_mac": taslak.record_mac,
        "label": taslak.label,
        "key_mode": taslak.key_mode,
        "key_ref": taslak.key_ref,
        "prev_mac": prev_mac,
        "mac": mac,
    }
    sutunlar.update(ham or {})
    adlar = ", ".join(f'"{ad}"' for ad in sutunlar)
    yer = ", ".join(["%s"] * len(sutunlar))
    with connection.cursor() as cursor:
        if kisitsiz:
            cursor.execute("PRAGMA ignore_check_constraints = ON")
        try:
            cursor.execute(
                f"INSERT INTO okul_audittrail ({adlar}) VALUES ({yer})",  # noqa: S608 — sabit adlar
                list(sutunlar.values()),
            )
        finally:
            if kisitsiz:
                cursor.execute("PRAGMA ignore_check_constraints = OFF")
    if ham:
        return next(denetim_izi.satirlari_oku(AuditTrail.objects.filter(seq=seq)))
    return AuditTrail.objects.get(seq=seq)
