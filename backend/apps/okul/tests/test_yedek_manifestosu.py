"""Yerel yedeğin manifestosu gerçek şemada (tasarım §4.4.7, TK22; plan F1b-3 "Kap ve manifesto").

Manifestonun kuralları `desktop/tests/test_backup.py`'de kısıtsız tabloyla sınanır (masaüstü Django
tanımaz, bozuk satır kurulabilir). Burada `Attachment`'ın göçle kurulan tablosu ve depo servisinin
yazdığı satırlar kullanılır: ham SQL'in okuduğu adlar modelle aynı kalsın, sayılar servisin yazdığı
açık boy ve özet olsun. Dosya adları ve içerikler uydurmadır.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from desktop.backup import EK_TABLOSU, goruntu_ve_manifesto, pre_anonim_backup
from desktop.backup_crypto import KAPSAM_YEREL, decrypt_bytes
from django.db import connection

from apps.okul.models import Attachment, AttachmentSensitivity, SchoolYear
from apps.okul.oturum import OTURUM
from apps.okul.services import app_password, dosya_deposu
from apps.okul.services import school_year as school_year_service
from conftest import TEST_DEK, varsayilan_yazar

PDF = b"%PDF-1.7\nuydurma belge icerigi\n"
JPEG = b"\xff\xd8\xff\xe0uydurma resim"
PNG = b"\x89PNG\r\n\x1a\nuydurma resim"


@pytest.fixture
def sahip(monkeypatch: pytest.MonkeyPatch) -> Iterator[SchoolYear]:
    """Geçici sahip kümesi (`SchoolYear`; F1b'de küme boştur)."""
    monkeypatch.setattr(dosya_deposu, "_SAHIP_ETIKETLERI", set())
    dosya_deposu.sahip_kaydet(SchoolYear)
    yield school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )


def _yaz(sahip: SchoolYear, icerik: bytes) -> Attachment:
    return dosya_deposu.yaz(
        icerik,
        original_name="Uydurgül Masalcıoğlu dilekçesi.pdf",
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=sahip,
        yazar=varsayilan_yazar(),
        kisi_listesi=False,
    )


def _imha_edilmis(ek: Attachment) -> None:
    """İmhalı satır (imha yolu F4-F6'dadır): satır kalır, sarmal ve ad boşalır."""
    Attachment.objects.filter(pk=ek.pk).update(
        purged_at=datetime(2026, 11, 4, 9, 0, tzinfo=UTC), key_wrap="", original_name=""
    )


def test_manifestonun_okudugu_tablo_ve_sutunlar_modelle_aynidir() -> None:
    """Masaüstü backend'i içe aktarmaz: ad burada sabittir; değişirse manifesto sessizce boşalırdı."""
    assert Attachment._meta.db_table == EK_TABLOSU
    sutunlar = {alan.column for alan in Attachment._meta.fields}
    assert {"stored_name", "size", "sha256", "purged_at"} <= sutunlar


@pytest.mark.django_db(transaction=True)
def test_kilitliyken_goruntu_gercek_ekleri_dek_ve_depo_olmadan_listeler(sahip: SchoolYear) -> None:
    """Açılıştaki yedek Django'dan önce, kilitliyken alınır: manifesto ne DEK'e ne depoya bakar.

    `size` ve `sha256` açık içeriğindir (OYS AYNEN); dosya depoda bulunmasa da listede durur.
    """
    birinci, ikinci, imhali = _yaz(sahip, PDF), _yaz(sahip, JPEG), _yaz(sahip, PNG)
    _imha_edilmis(imhali)
    for ek in (birinci, ikinci):
        (dosya_deposu.depo_dizini() / ek.stored_name).unlink()
    assert OTURUM.kilitle(neden="elle") == "kilitlendi"
    assert app_password.is_locked()

    _baytlar, manifesto = goruntu_ve_manifesto(Path(str(connection.settings_dict["NAME"])))

    assert manifesto.kapsam == KAPSAM_YEREL
    assert [(g.ad, g.boyut, g.sha256) for g in manifesto.dosyalar] == sorted(
        (ek.stored_name, len(icerik), hashlib.sha256(icerik).hexdigest())
        for ek, icerik in ((birinci, PDF), (ikinci, JPEG))
    )


@pytest.mark.django_db(transaction=True)
def test_yerel_yedek_manifestoyu_mihurlu_bolumde_tasir_ozgun_ad_goruntude_sifreli_kalir(
    sahip: SchoolYear, tmp_path: Path
) -> None:
    ek = _yaz(sahip, PDF)
    db = Path(str(connection.settings_dict["NAME"]))

    yedek = pre_anonim_backup(db, tmp_path, data_dir=app_password.state_path().parent)

    assert yedek is not None
    icerik = decrypt_bytes(yedek.read_bytes(), TEST_DEK)
    assert [girdi.ad for girdi in icerik.manifesto.dosyalar] == [ek.stored_name]
    assert "Masalcıoğlu".encode() not in icerik.veritabani
    assert "Masalcıoğlu".encode() not in icerik.manifesto.baytlar()
