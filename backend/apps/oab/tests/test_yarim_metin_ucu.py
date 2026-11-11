"""Gerekçe kutusunun yarım metni ucu (tasarım §7 "Yarım kalan metin"; plan F1c 3. adım notları "yarım
metin kaydının ucu 11. adımda"): oturumdaki hesabın tek, şifreli kaydı; boş metin ve silme kaydı kaldırır;
denetim izine satır yazmaz; başka hesabın taslağı okunmaz. Metinler UYDURMADIR."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.oab.models import DraftText
from apps.okul.models import AccountRole, AccountStatus, AuditTrail
from apps.okul.tests.hesap_ortak import hesap_ac, muhurle
from conftest import oturumu_ac_test

pytestmark = pytest.mark.django_db

UC = "/api/v1/oab/drafts/"


def test_yarim_metin_yazilir_okunur_ve_silinir_iz_yazmaz() -> None:
    istemci = APIClient()
    assert istemci.get(UC).status_code == 204  # yarım metin yok
    once = AuditTrail.objects.count()
    yanit = istemci.put(
        UC, {"metin": "Uydurma yarım gerekçe", "baglam": "gecis.karar_defteri"}, format="json"
    )
    assert yanit.status_code == 204, yanit.content
    veri = istemci.get(UC).json()
    assert (veri["metin"], veri["baglam"]) == ("Uydurma yarım gerekçe", "gecis.karar_defteri")
    # Hesap başına tek kayıt: yeni metin eskisinin yerine geçer.
    istemci.put(UC, {"metin": "Uydurma ikinci metin"}, format="json")
    assert DraftText.objects.count() == 1
    assert istemci.get(UC).json()["metin"] == "Uydurma ikinci metin"
    # Boş metin kaydı siler; silme ucu da.
    istemci.put(UC, {"metin": "   "}, format="json")
    assert not DraftText.objects.exists()
    istemci.put(UC, {"metin": "Uydurma"}, format="json")
    assert istemci.delete(UC).status_code == 204
    assert not DraftText.objects.exists()
    assert AuditTrail.objects.count() == once


def test_yarim_metin_hesabindir() -> None:
    APIClient().put(UC, {"metin": "Yöneticinin uydurma taslağı"}, format="json")
    dk = muhurle(
        hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi"), status=AccountStatus.ACIK
    )
    oturumu_ac_test(str(dk.id), tanitici=dk.login_name, rol=AccountRole.DENETLEME_KURULU.value)
    istemci = APIClient()
    assert istemci.get(UC).status_code == 204
    assert (
        istemci.put(UC, {"metin": "Denetçinin uydurma taslağı"}, format="json").status_code == 204
    )
    assert DraftText.objects.count() == 2


def test_baglamli_silme_baska_kutunun_metnini_silmez() -> None:
    """Bir kutunun kaydı ya da vazgeçişi (`?baglam=`) hesabın başka kutuya ait yarım metnini silmez;
    aynı bağlamın metni silinir. Bağlamsız silme bütün kaydı kaldırır (tasarım §7 "Yarım kalan
    metin")."""
    istemci = APIClient()
    istemci.put(
        UC, {"metin": "Uydurma defter gerekçesi", "baglam": "gecis.karar_defteri"}, format="json"
    )
    assert istemci.delete(UC + "?baglam=gecis.devralinan").status_code == 204
    assert DraftText.objects.count() == 1
    assert istemci.get(UC).json()["metin"] == "Uydurma defter gerekçesi"
    assert istemci.delete(UC + "?baglam=gecis.karar_defteri").status_code == 204
    assert not DraftText.objects.exists()
    istemci.put(UC, {"metin": "Uydurma", "baglam": "gecis.sayac_beyani"}, format="json")
    assert istemci.delete(UC).status_code == 204
    assert not DraftText.objects.exists()
