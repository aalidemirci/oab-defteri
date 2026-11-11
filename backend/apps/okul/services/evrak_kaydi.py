"""Okul çekirdeğinin ürettiği evrakın kaydı — `oab`'nin kayıt defteri (plan F1c 9. adım).

Her üretim bir `GeneratedDocument` satırıdır (tasarım §5.2.8, §9.1-2); model `apps.oab`'dadır ve
`okul` onu Python düzeyinde içe aktarmaz (plan "F1c adımları"; bekçisi `apps/oab/tests/test_iskelet.py`).
Bu yüzden kaydedici kayıt defterinden gelir: `apps.oab` açılışta kaydeder
(`register_document_recorder`; `AppConfig.ready`, idempotent). Kaydedici kayıtlı değilse evrak
verilmez (fail-closed: izsiz üretim yok). Bugünkü tek çağıran hesap teslim pusulasıdır (E63;
`hesaplar.teslim_pusulasi`): konu hesap, biçim PDF, dosya saklanmaz.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Protocol

from django.db import models

from shared import evrak


class EvrakKaydedici(Protocol):
    """Evrakın kaydını yazan işlev (`apps.oab.services.evrak.okul_evraki_kaydet`)."""

    def __call__(
        self, belge: evrak.Belge, *, konu: models.Model, bicimler: Iterable[str]
    ) -> Any: ...


class EvrakKaydiYok(RuntimeError):
    """Evrak kaydedicisi kayıtlı değil: evrak verilmez (fail-closed)."""

    def __init__(self) -> None:
        super().__init__("Evrak kaydı yazılamıyor; belge verilmedi.")


#: Kayıtlı kaydedici (en çok bir; `register_document_recorder`).
_kaydedici: list[Callable[..., Any]] = []


def register_document_recorder(fn: EvrakKaydedici) -> None:
    """Kaydediciyi kaydeder (`AppConfig.ready`; idempotent, son kayıt geçerlidir)."""
    _kaydedici[:] = [fn]


def kaydet(belge: evrak.Belge, *, konu: models.Model, bicimler: Iterable[str]) -> Any:
    """Evrakın kaydını yazar; çağıranın işlemindedir. Kaydedici yoksa `EvrakKaydiYok`."""
    if not _kaydedici:
        raise EvrakKaydiYok()
    return _kaydedici[0](belge, konu=konu, bicimler=bicimler)
