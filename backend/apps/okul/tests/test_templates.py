"""İndirilebilir içe aktarma şablonları (tasarım §8.4) — gidiş-dönüş sözleşmesi.

Şablonun var olma nedeni TEKTİR: idareci doldurur ve AYNI içe aktarma ucuna
yükler; "ayrı bir şablon kod yolu" YOKTUR. Bu yüzden asıl sabitlenen davranış
başlık metni değil GİDİŞ-DÖNÜŞTÜR — şablon başlıkları parser sinonimlerinden
koparsa program kendi verdiği dosyayı geri okuyamaz ve hata kullanıcıya
"zorunlu sütun bulunamadı" diye yansır.

Örnek satırlar uydurmadır (KVKK): şablon depoya ve dağıtım paketine girer. Öğrenci şablonu
F1b 5. adımda öğrenci aktarımıyla söküldü (tasarım §5.1 ALMA); ucunun yokluğu sınanır.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import pytest
from django.http import StreamingHttpResponse
from rest_framework.test import APIClient

from apps.okul import excel_ortak
from apps.okul.models import MemberKind, Personnel
from apps.okul.services import imports as import_service
from apps.okul.services import templates as template_service

XLSX_TURU = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _dolu_satirlar(xlsx: bytes) -> list[list[str]]:
    """Şablonu İÇE AKTARMANIN KENDİ okuyucusuyla açar (boş satırlar elenir)."""
    satirlar = excel_ortak.read_sheet(xlsx)
    return [
        [str(hucre) for hucre in satir]
        for satir in satirlar
        if any(str(hucre or "").strip() for hucre in satir)
    ]


def _govde(yanit: object) -> bytes:
    assert isinstance(yanit, StreamingHttpResponse)
    return b"".join(cast(Iterable[bytes], yanit.streaming_content))


def test_personel_sablonu_baslik_satiri_ve_tek_ornek_satir_tasir() -> None:
    satirlar = _dolu_satirlar(template_service.personnel_template_xlsx())

    assert satirlar[0] == list(template_service.PERSONNEL_TEMPLATE_HEADERS)
    assert len(satirlar) == 2
    # Örnek satır yer tutucudur — gerçek bir kişiye benzeyen ad taşımaz (KVKK).
    assert satirlar[1][:2] == ["ÖRNEK", "ÖĞRETMEN"]


@pytest.mark.django_db
def test_personel_sablonu_ice_aktarma_ucundan_oldugu_gibi_gecer() -> None:
    """Gidiş-dönüş: indirilen şablon HİÇ dokunulmadan aynı uca yüklenebilir.

    Ayrı 'Adı' / 'Soyadı' sütunları + 'Üye Türü' tanınır; unvan/branş sütunu yoktur. Başlıklardan
    biri sinonim listesinden koparsa bu test "zorunlu sütun bulunamadı" ile düşer.
    """
    rapor = import_service.commit_personnel_file(
        file_bytes=template_service.personnel_template_xlsx(), file_name="sablon-personel.xlsx"
    )

    assert rapor.skipped == []
    assert (rapor.total_rows, rapor.processed, rapor.created_personnel) == (1, 1, 1)
    kisi = Personnel.objects.get()
    assert kisi.full_name == "ÖRNEK ÖĞRETMEN"
    assert kisi.member_kind == MemberKind.TEACHER
    assert rapor.warnings == []


def test_sablon_indirme_ucu_excel_eki_dondurur() -> None:
    """Uç sözleşmesi: tarayıcı/WebView dosyayı EK olarak ve .xlsx adıyla indirir.

    Veritabanına dokunmaz (kurulumdan önce, boş programda da indirilebilmeli).
    """
    yanit = APIClient().get("/api/v1/templates/personnel/")

    assert yanit.status_code == 200
    assert yanit["Content-Type"] == XLSX_TURU
    assert "attachment" in yanit["Content-Disposition"]
    assert "sablon-personel.xlsx" in yanit["Content-Disposition"]
    assert _dolu_satirlar(_govde(yanit))[0] == list(template_service.PERSONNEL_TEMPLATE_HEADERS)


def test_ogrenci_sablonu_yoktur() -> None:
    """Öğrenci şablonu ve ucu F1b 5. adımda söküldü (tasarım §5.1 ALMA, T5)."""
    assert not hasattr(template_service, "student_template_xlsx")
    assert not hasattr(template_service, "STUDENT_TEMPLATE_HEADERS")


def test_personel_sablonunda_unvan_ve_brans_sutunu_yoktur() -> None:
    """Tasarım §8.4: şablon unvan/branş istemez; "Üye Türü" yalnız öğretmen / diğer personel."""
    basliklar = [
        excel_ortak.normalize_header(b) for b in template_service.PERSONNEL_TEMPLATE_HEADERS
    ]
    assert not [b for b in basliklar for yasak in ("unvan", "brans", "gorev") if yasak in b]


@pytest.mark.django_db
def test_personel_sablonu_diger_personel_degerini_tanir() -> None:
    rapor = import_service.commit_personnel_text(
        text="Adı\tSoyadı\tÜye Türü\nÖRNEK\tKİŞİ\tDiğer personel\nÖRNEK\tİKİ\tÖğretmen"
    )

    assert rapor.warnings == []
    turler = {p.last_name: p.member_kind for p in Personnel.objects.all()}
    assert turler == {"KİŞİ": MemberKind.STAFF, "İKİ": MemberKind.TEACHER}
