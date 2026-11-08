"""e-Okul mutabakatı — personel (aile iskeletinden; OAB'de tasarım §8.4).

Aile iskeletinin kullanıcı kararı: **aktarım hiç kimseyi ayırmaz ve hiç
kimseyi silmez.** Listede bulunmayan aktif kişi AYRILIŞ HAVUZUNA girer, durumu
aktif kalır; dosyada bulunan havuzdaki kişi havuzdan kendiliğinden çıkar. Karar
havuzda verilir (`test_ayrilis_havuzu.py`).

Öğrenci mutabakatı F1b 5. adımda öğrenci sicili ve aktarımıyla söküldü (tasarım §5.1 ALMA,
T5). Onun türden bağımsız koruma testleri (havuza giriş ayrılış değildir, aynı dosyanın ikinci
uygulaması değişiklik üretmez, önizleme uygulamayla aynı sonucu verir ve hiçbir şeyi
değiştirmez, kalıcı raporda ve günlükte ad yok) personel üzerinden sınanır
(`TestPersonelHavuzu`).

Personel mutabakatı: listede olmayanlar havuza girer (eski `mark_left_ids`
seçimi kalktı, gönderilse de yok sayılır), "olası aynı kişi" çiftleri, görev
metninden görev türü sınıflaması.

KİŞİSEL VERİ: havuza eklenecek kişilerin adları yalnız API yanıtındadır;
`ImportRun.report`'ta ve günlükte ad ve görev metni bulunmaz
(sentetik, ayırt edici adlarla aranır).

Bütün adlar uydurmadır (KVKK).
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.okul import selectors
from apps.okul.models import (
    AuditTrail,
    ImportRun,
    ImportStatus,
    MemberKind,
    Personnel,
)
from apps.okul.services import imports as import_service
from apps.okul.services import persons

pytestmark = pytest.mark.django_db

PERSONEL_BASLIK = "Adı\tSoyadı\tGörevi\tBranşı"

#: Ayırt edici sentetik değerler — raporda/günlükte aranırlar.
SENTETIK_AD = "ZEYNEPSENTETİK"
SENTETIK_SOYAD = "ÖRNEKOĞLU"


def _personel_metni(*satirlar: str) -> str:
    return "\n".join([PERSONEL_BASLIK, *satirlar])


def _personel(ad: str, soyad: str, **alanlar: Any) -> Personnel:
    kisi: Personnel = Personnel.objects.create(first_name=ad, last_name=soyad, **alanlar)
    return kisi


def _havuzda_mi(kayit: Personnel) -> bool:
    kayit.refresh_from_db()
    return kayit.leave_candidate_since is not None


@pytest.fixture(autouse=True)
def bos_kayit_defterleri(monkeypatch: pytest.MonkeyPatch) -> None:
    for ad in (
        "_obligation_checks",
        "_membership_checks",
        "_leave_hooks",
        "_merge_hooks",
        "_deletion_blocks",
    ):
        monkeypatch.setattr(persons, ad, [])


# ---------------------------------------------------------------------------
# Havuz ve önizleme (türden bağımsız koruma; öğrenci sökümünden personele taşındı)
# ---------------------------------------------------------------------------
class TestPersonelHavuzu:
    def test_havuza_giren_aktif_kalir_tarih_ve_aktarim_yazilir_kanca_cagrilmaz(self) -> None:
        """Havuza girmek ayrılış DEĞİLDİR: ayrılış kancası koşmaz, kayıt silinmez."""
        kancaya_gelen: list[int] = []
        persons.register_leave_hook(lambda kisi: kancaya_gelen.append(kisi.pk))
        _personel("AYŞE", "KAYA")
        eksik = _personel("MEHMET", "DEMİR")

        import_service.commit_personnel_text(text=_personel_metni("AYŞE\tKAYA\tÖğretmen\t"))

        assert kancaya_gelen == []
        eksik.refresh_from_db()
        assert (eksik.is_active, eksik.left_at) == (True, None)
        assert eksik.leave_candidate_since == timezone.localdate()
        kosu = ImportRun.objects.get(status=ImportStatus.COMPLETED)
        assert eksik.leave_candidate_run_id == kosu.pk
        assert Personnel.all_objects.filter(pk=eksik.pk, deleted_at__isnull=True).exists()

    def test_ayni_dosyanin_ikinci_uygulamasi_degisiklik_uretmez(self) -> None:
        _personel("AYŞE", "KAYA")
        _personel("MEHMET", "DEMİR")  # ilk uygulamada havuza girer
        metin = _personel_metni("AYŞE\tKAYA\tÖğretmen\t", "CEM\tYENİ\tMemur\t")

        ilk = import_service.commit_personnel_text(text=metin)
        assert (ilk.created_personnel, ilk.pool_added_personnel) == (1, 1)

        def durum() -> dict[int, Any]:
            return {
                p.pk: (p.updated_at, p.is_active, p.leave_candidate_since, p.leave_candidate_run_id)
                for p in Personnel.all_objects.all()
            }

        oncesi = durum()
        ikinci = import_service.commit_personnel_text(text=metin)

        assert ikinci.already_imported is True
        assert (
            ikinci.created_personnel,
            ikinci.updated_personnel,
            ikinci.unchanged_personnel,
            ikinci.pool_added_personnel,
            ikinci.pool_removed_personnel,
        ) == (0, 0, 2, 0, 0)
        assert durum() == oncesi

    def test_havuzda_bekleyen_yeniden_eksik_kalirsa_ilk_giris_ve_aktarim_korunur(self) -> None:
        _personel("AYŞE", "KAYA")
        bekleyen = _personel("MEHMET", "DEMİR")
        import_service.commit_personnel_text(text=_personel_metni("AYŞE\tKAYA\t\t"))
        ilk_kosu = ImportRun.objects.get(status=ImportStatus.COMPLETED)
        gecmis = timezone.localdate() - timedelta(days=20)
        Personnel.objects.filter(pk=bekleyen.pk).update(leave_candidate_since=gecmis)

        rapor = import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\t\t", "CEM\tYENİ\t\t")
        )

        assert rapor.pool_added_personnel == 0
        assert rapor.pool_added == []
        bekleyen.refresh_from_db()
        assert (bekleyen.leave_candidate_since, bekleyen.leave_candidate_run_id) == (
            gecmis,
            ilk_kosu.pk,
        )

    def test_onizleme_uygulamayla_ayni_sonucu_verir_ve_hicbir_sey_degistirmez(self) -> None:
        _personel("AYŞE", "KAYA")
        _personel("MEHMET", "DEMİR")
        _personel("ZEHRA", "ÇELİK")
        metin = _personel_metni("AYŞE\tKAYA\tMemur\t", "CEM\tYENİ\tÖğretmen\t")

        def durum() -> list[Any]:
            return sorted(
                Personnel.all_objects.values_list(
                    "pk",
                    "is_active",
                    "member_kind",
                    "updated_at",
                    "leave_candidate_since",
                    "leave_candidate_run",
                )
            )

        oncesi = durum()
        onizleme = import_service.preview_personnel_text(text=metin)

        assert durum() == oncesi
        uygulama = import_service.commit_personnel_text(text=metin)
        onizleme_sozlugu = {**onizleme.to_dict(), "dry_run": False}
        # Önizlemenin açtığı yeni kayıt geri alındığı için çiftlerin `new_id`'si boştur.
        assert onizleme_sozlugu == uygulama.to_dict() | {"already_imported": False}
        assert onizleme.dry_run is True
        assert onizleme.pool_added_personnel == 2
        assert (onizleme.updated_personnel, onizleme.created_personnel) == (1, 1)

    def test_yazim_yarida_kalirsa_aktarim_butunuyle_geri_alinir(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Güncelleme ve yeni kayıt yazıldıktan sonra havuza ekleme patlarsa hiçbir şey değişmez:
        kişiler, koşular ve denetim izi aynen kalır (`_ingest_personnel` atomiktir; atomiklik
        kaldırılırsa bu test düşer — veli listesinin eşi `test_veli_listesi.py`'de)."""
        _personel("AYŞE", "KAYA")
        _personel("MEHMET", "DEMİR")
        import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\t", "MEHMET\tDEMİR\tÖğretmen\t")
        )

        def durum() -> list[Any]:
            return sorted(
                Personnel.all_objects.values_list(
                    "pk",
                    "is_active",
                    "member_kind",
                    "updated_at",
                    "leave_candidate_since",
                    "leave_candidate_run",
                )
            )

        def kosular() -> list[Any]:
            return list(ImportRun.objects.order_by("pk").values_list("pk", "status", "report"))

        oncesi, kosular_once, iz_once = durum(), kosular(), AuditTrail.objects.count()

        def patlayan_havuz(*_a: object, **_k: object) -> bool:
            raise RuntimeError("uydurma yazım hatası")

        with monkeypatch.context() as yama:
            yama.setattr(persons, "add_to_leave_pool", patlayan_havuz)
            with pytest.raises(RuntimeError, match="uydurma yazım hatası"):
                # AYŞE güncellenir, CEM açılır, MEHMET havuza girerken yazım patlar.
                import_service.commit_personnel_text(
                    text=_personel_metni("AYŞE\tKAYA\tMemur\t", "CEM\tYENİ\tÖğretmen\t")
                )

        assert durum() == oncesi
        assert kosular() == kosular_once
        assert AuditTrail.objects.count() == iz_once

    def test_gunlukte_ad_yok(self, caplog: pytest.LogCaptureFixture) -> None:
        _personel(SENTETIK_AD, SENTETIK_SOYAD)
        with caplog.at_level(logging.DEBUG):
            import_service.commit_personnel_text(
                text=_personel_metni(f"{SENTETIK_AD}\tYENİSOYAD\t\t", "DİĞER\tKİŞİ\t\t")
            )

        assert caplog.records, "aktarım günlüğe sayısal özet yazmalı"
        assert "ayrılış havuzuna 1 eklendi" in caplog.text
        for iz in (SENTETIK_AD, SENTETIK_SOYAD, "YENİSOYAD", "DİĞER"):
            assert iz not in caplog.text, iz

    def test_kalici_raporda_ham_hucre_degeri_yok(self) -> None:
        """Satır sorununun ham hücre değeri yalnız API yanıtında kalır; kalıcı raporda alanı yok."""
        # Görev hücresi boş: görev türü denetim uyarısı (satır sorunu); branş hiç okunmaz.
        metin = _personel_metni("AYŞE\tKAYA\t\tUzman Kaptan")

        onizleme = import_service.preview_personnel_text(text=metin)
        import_service.commit_personnel_text(text=metin)

        assert "raw_value" in onizleme.to_dict()["warnings"][0]
        raporlar = json.dumps([r.report for r in ImportRun.objects.all()], ensure_ascii=False)
        assert ImportRun.objects.filter(status=ImportStatus.PREVIEWED).exists()
        assert "raw_value" not in raporlar
        assert "Kaptan" not in raporlar

    def test_onizleme_gunluge_bir_sey_yazmaz_ve_havuzu_degistirmez(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Önizleme geri sarılır: günlükte olmamış bir aktarım ya da ayrılış görünmemeli."""
        _personel("AYŞE", "KAYA")
        _personel("MEHMET", "DEMİR")
        _personel("ZEHRA", "ÇELİK")

        with caplog.at_level(logging.DEBUG, logger="oab_defteri.okul"):
            rapor = import_service.preview_personnel_text(text=_personel_metni("AYŞE\tKAYA\t\t"))

        assert rapor.pool_added_personnel == 2
        assert selectors.leave_pool_personnel() == []
        assert "uygulandı" not in caplog.text
        assert "ayrılışı işlendi" not in caplog.text
        assert "silindi" not in caplog.text


# ---------------------------------------------------------------------------
# Personel mutabakatı
# ---------------------------------------------------------------------------
class TestPersonelMutabakati:
    def test_listede_olmayan_personel_havuza_girer_aktif_kalir_kimse_ayrilmaz(self) -> None:
        _personel("AYŞE", "KAYA")
        eksik = _personel("MEHMET", "DEMİR")

        onizleme = import_service.preview_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\tFizik")
        )
        assert [(m.id, m.full_name) for m in onizleme.pool_added] == [(eksik.pk, "MEHMET DEMİR")]
        assert onizleme.pool_added_personnel == 1
        assert not _havuzda_mi(eksik)  # önizleme yazmaz

        uygulama = import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\tFizik")
        )
        assert uygulama.pool_added_personnel == 1
        eksik.refresh_from_db()
        assert (eksik.is_active, eksik.left_at) == (True, None)
        assert eksik.leave_candidate_since == timezone.localdate()
        assert not Personnel.all_objects.filter(is_active=False).exists()

    def test_eski_mark_left_ids_alani_yok_sayilir_kimse_ayrilmaz(self) -> None:
        """Eski kural (işaretlenenler ayrılır) KALKTI: seçim gönderilse de karar havuzdadır."""
        _personel("AYŞE", "KAYA")
        bir = _personel("MEHMET", "DEMİR")
        iki = _personel("ZEHRA", "ÇELİK")

        yanit = APIClient().post(
            "/api/v1/imports/personnel/commit/",
            {"text": _personel_metni("AYŞE\tKAYA\t\t"), "mark_left_ids": [bir.pk, iki.pk]},
            format="multipart",
        )

        assert yanit.status_code == 200, yanit.json()
        assert yanit.json()["pool_added_personnel"] == 2
        assert "left_personnel" not in yanit.json()
        for kisi in (bir, iki):
            kisi.refresh_from_db()
            assert (kisi.is_active, kisi.left_at) == (True, None)
            assert kisi.leave_candidate_since is not None
        assert Personnel.all_objects.count() == 3

    def test_havuzdaki_personel_listede_gorulunce_havuzdan_cikar(self) -> None:
        kisi = _personel("AYŞE", "KAYA")
        persons.add_to_leave_pool(kisi, run=None)

        rapor = import_service.commit_personnel_text(text=_personel_metni("AYŞE\tKAYA\t\t"))

        assert (rapor.unchanged_personnel, rapor.pool_removed_personnel) == (1, 1)
        assert not _havuzda_mi(kisi)

    def test_ayrilmis_personel_listede_gorulunce_yeniden_aktiflesir(self) -> None:
        kisi = _personel("AYŞE", "KAYA")
        persons.leave_personnel(kisi)

        rapor = import_service.commit_personnel_text(text=_personel_metni("AYŞE\tKAYA\tÖğretmen\t"))

        assert (rapor.created_personnel, rapor.reactivated_personnel) == (0, 1)
        kisi.refresh_from_db()
        assert (kisi.is_active, kisi.left_at) == (True, None)

    def test_adaslar_ayri_ayri_eslesir(self) -> None:
        """Aynı adı taşıyan iki personel, iki satırla iki ayrı kayda eşleşir."""
        _personel("AYŞE", "KAYA")
        _personel("AYŞE", "KAYA")

        rapor = import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\t", "AYŞE\tKAYA\tÖğretmen\t")
        )

        assert (rapor.created_personnel, rapor.unchanged_personnel, rapor.pool_added_personnel) == (
            0,
            2,
            0,
        )

    def test_olasi_ayni_kisi_ad_ayni_soyad_farkli(self) -> None:
        """Soyadı değişimi: yeni satır 'AYŞE BEYAZ' ↔ listede olmayan 'AYŞE KARA'."""
        eski = _personel("AYŞE", "KARA")
        _personel("ALİ", "VELİ")
        metin = _personel_metni("ALİ\tVELİ\t\t", "AYŞE\tBEYAZ\tÖğretmen\t")

        onizleme = import_service.preview_personnel_text(text=metin)
        assert [
            (c.row_number, c.row_name, c.existing_id, c.existing_name, c.new_id, c.reason)
            for c in onizleme.similar_pairs
        ] == [(3, "AYŞE BEYAZ", eski.pk, "AYŞE KARA", None, "ad_ayni_soyad_farkli")]

        uygulama = import_service.commit_personnel_text(text=metin)
        (cift,) = uygulama.similar_pairs
        yeni = Personnel.objects.get(pk=cift.new_id)
        assert yeni.full_name == "AYŞE BEYAZ"
        assert _havuzda_mi(eski)  # listede olmayan eski kayıt karar bekler

        # Birleştir: eski kayıt (kaynak) yeni kayda (hedef) katılır, eski silinir.
        yanit = APIClient().post(
            f"/api/v1/personnel/{cift.existing_id}/merge/", {"into_id": cift.new_id}, format="json"
        )
        assert yanit.status_code == 200
        assert not Personnel.all_objects.filter(pk=eski.pk).exists()
        assert selectors.leave_pool_personnel() == []

    def test_olasi_ayni_kisi_kucuk_yazim_farki(self) -> None:
        eski = _personel("SELİN", "ÖZTÜRK")

        rapor = import_service.preview_personnel_text(
            text=_personel_metni("SELİM\tÖZTÜRK\tÖğretmen\t")
        )

        # Gerekçe çiftle birlikte taşınır: kullanıcı neden eşleştiğini görsün (§13 D30).
        assert [(c.existing_id, c.reason) for c in rapor.similar_pairs] == [
            (eski.pk, "yazim_farki")
        ]

    def test_benzemeyen_kisiler_cift_olusturmaz(self) -> None:
        _personel("AYŞE", "KARA")
        _personel("MEHMET", "DEMİR")

        rapor = import_service.preview_personnel_text(
            text=_personel_metni("ZEYNEP\tKAYA\t\t", "CEM\tBEYAZ\t\t")
        )

        assert rapor.similar_pairs == []
        assert rapor.pool_added_personnel == 2

    def test_kalici_raporda_ad_yok_api_yanitinda_var(self) -> None:
        _personel(SENTETIK_AD, SENTETIK_SOYAD)
        metin = _personel_metni(f"{SENTETIK_AD}\tYENİSOYAD\tÖğretmen\t")

        yanit = APIClient().post(
            "/api/v1/imports/personnel/commit/", {"text": metin}, format="json"
        )

        assert yanit.status_code == 200
        assert yanit.json()["pool_added"][0]["full_name"] == f"{SENTETIK_AD} {SENTETIK_SOYAD}"
        assert yanit.json()["similar_pairs"][0]["row_name"] == f"{SENTETIK_AD} YENİSOYAD"
        run = ImportRun.objects.get(status=ImportStatus.COMPLETED)
        kalici = json.dumps(run.report, ensure_ascii=False)
        for iz in (SENTETIK_AD, SENTETIK_SOYAD, "YENİSOYAD"):
            assert iz not in kalici, iz
        assert (run.report["pool_added_personnel"], run.report["similar_pair_count"]) == (1, 1)
        assert "pool_added" not in run.report and "similar_pairs" not in run.report


class TestPersonelImportSilmezIlkesi:
    """KORUMA: tanınamayan personel satırı okulun bütün personelini havuza atamaz.

    Personelde kimlik anahtarı ad-soyaddır (okul no yok): sütunları kaymış ya da
    ad hücresi boş bir dosya listedeki HERKESİ "yok" gösterir; kapı hiç kimsedir.
    """

    def test_hic_satiri_islenemeyen_dosya_kimseyi_havuza_eklemez(self) -> None:
        bir = _personel("AYŞE", "KAYA")
        iki = _personel("MEHMET", "DEMİR")

        rapor = import_service.commit_personnel_text(
            text=_personel_metni("\t\tÖğretmen\tFizik", "\t\tMemur\t")
        )

        assert (rapor.processed, rapor.pool_added_personnel) == (0, 0)
        assert rapor.pool_added == []
        assert [(u.row_number, u.field, u.issue) for u in rapor.warnings] == [
            (1, import_service.POOL_FIELD, import_service.PERSONNEL_NOTHING_PROCESSED_MESSAGE)
        ]
        for kisi in (bir, iki):
            assert not _havuzda_mi(kisi)
            assert kisi.is_active is True
        assert not Personnel.all_objects.filter(is_active=False).exists()

    def test_adi_bos_satir_hic_kimseyi_havuza_eklemez(self) -> None:
        """Tek satırı kaymış dosya: işlenen satırlar yazılır, havuza ekleme durur."""
        gorulen = _personel("AYŞE", "KAYA")
        korunan = _personel("MEHMET", "DEMİR")

        rapor = import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\tFizik", "\t\tMemur\t")
        )

        assert (rapor.processed, rapor.pool_added_personnel) == (1, 0)
        assert [(s.row_number, s.field, s.issue) for s in rapor.skipped] == [
            (3, "full_name", import_service.PERSONNEL_UNIDENTIFIED_ROW_MESSAGE)
        ]
        assert not _havuzda_mi(korunan)
        assert not _havuzda_mi(gorulen)
        assert not Personnel.all_objects.filter(is_active=False).exists()

    def test_kapi_kalkinca_ayni_dosya_havuza_ekler(self) -> None:
        """Karşı kanıt: kapıyı açan tek fark tanınamayan satırdır."""
        korunan = _personel("MEHMET", "DEMİR")
        _personel("AYŞE", "KAYA")

        rapor = import_service.commit_personnel_text(
            text=_personel_metni("AYŞE\tKAYA\tÖğretmen\tFizik")
        )

        assert rapor.pool_added_personnel == 1
        assert _havuzda_mi(korunan)

    def test_zaten_havuzdaki_kisi_taninamayan_satirda_havuzda_kalir(self) -> None:
        """Kapı yalnız YENİ eklemeyi durdurur; bekleyen karar silinmez."""
        bekleyen = _personel("MEHMET", "DEMİR")
        persons.add_to_leave_pool(bekleyen, run=None)

        rapor = import_service.commit_personnel_text(text=_personel_metni("\t\tÖğretmen\t"))

        assert rapor.pool_added_personnel == 0
        assert _havuzda_mi(bekleyen)

    def test_kalici_raporda_havuz_uyarisi_var_ad_yok(self) -> None:
        _personel(SENTETIK_AD, SENTETIK_SOYAD)

        import_service.commit_personnel_text(text=_personel_metni(f"\t\t{SENTETIK_AD}\t"))

        run = ImportRun.objects.get(status=ImportStatus.COMPLETED)
        kalici = json.dumps(run.report, ensure_ascii=False)
        assert run.report["pool_added_personnel"] == 0
        assert import_service.PERSONNEL_NOTHING_PROCESSED_MESSAGE in kalici
        assert SENTETIK_AD not in kalici and SENTETIK_SOYAD not in kalici


# ---------------------------------------------------------------------------
# Görev metninden görev türü — metin hiçbir yerde saklanmaz
# ---------------------------------------------------------------------------


class TestGorevTuruSiniflamasi:
    GOREVLI_LISTE = _personel_metni(
        "ALİ\tBİR\tMüdür Yardımcısı\tTarih",
        "AYŞE\tİKİ\tSözleşmeli Öğretmen(657 S.K. 4/B)\tİngilizce",
        "CEM\tÜÇ\tMemur\t",
        "DENİZ\tDÖRT\tYardımcı Hizmetli\t",
        "EMEL\tBEŞ\tUzman Kaptan\t",
        "FATİH\tALTI\t\t",
    )

    def test_gorev_turune_cevrilir_bos_gorev_ogretmen_ve_uyari(self) -> None:
        rapor = import_service.commit_personnel_text(text=self.GOREVLI_LISTE)

        turler = {p.first_name: p.member_kind for p in Personnel.objects.all()}
        assert turler == {
            "ALİ": MemberKind.YONETICI,
            "AYŞE": MemberKind.OGRETMEN,
            "CEM": MemberKind.DIGER,
            "DENİZ": MemberKind.DIGER,
            "EMEL": MemberKind.DIGER,  # öğretmen ve yönetici değil → diğer personel
            "FATİH": MemberKind.OGRETMEN,  # boş görev → öğretmen + uyarı
        }
        uyarilar = [(u.row_number, u.field, u.raw_value) for u in rapor.warnings]
        assert uyarilar == [(7, "member_kind", "")]
        assert all("Görev türünü denetleyin" in u.issue for u in rapor.warnings)

    def test_supheli_gorev_turu_degismez_ama_denetim_uyarisi_alir(self) -> None:
        """Kullanıcı kararı harfiyen: "Okul Müdürü" ve "Usta Öğretici" diğer personel sayılır ve
        "Görev türünü denetleyin" uyarısı alır; "Rehber Öğretmen (Psikolojik Danışman)" içinde
        "öğretmen" geçtiği için kesin öğretmendir, uyarı almaz (görev metni yazılmaz)."""
        rapor = import_service.commit_personnel_text(
            text=_personel_metni(
                "GÜL\tYEDİ\tOkul Müdürü\t",
                "HAKAN\tSEKİZ\tRehber Öğretmen (Psikolojik Danışman)\t",
                "İPEK\tDOKUZ\tMüdür\t",
                "KAAN\tON\tUsta Öğretici\t",
            )
        )

        turler = {p.first_name: p.member_kind for p in Personnel.objects.all()}
        assert turler == {
            "GÜL": MemberKind.DIGER,
            "HAKAN": MemberKind.OGRETMEN,
            "İPEK": MemberKind.YONETICI,
            "KAAN": MemberKind.DIGER,
        }
        uyarilar = [(u.row_number, u.field, u.issue, u.raw_value) for u in rapor.warnings]
        mesaj = import_service.MEMBER_KIND_UNCERTAIN_MESSAGE
        assert uyarilar == [
            (2, "member_kind", mesaj, ""),
            (5, "member_kind", mesaj, ""),
        ]
        assert mesaj.startswith("Görev türünü denetleyin")
        kalici = json.dumps([r.report for r in ImportRun.objects.all()], ensure_ascii=False)
        for gorev in ("Okul Müdürü", "Psikolojik", "Usta Öğretici"):
            assert gorev not in kalici

    def test_supheli_gorevde_var_olan_kaydin_turu_korunur(self) -> None:
        """Elle düzeltilen tür sonraki aktarımda ezilmez: "Okul Müdürü" yönetici yapılmışsa
        belirsiz görev onu diğer personele geri çevirmez; uyarı yine düşer. İçinde "öğretmen" geçen
        görev kesindir: diğer personel kaydı öğretmene güncellenir, uyarı yoktur. Önizleme ve
        uygulama aynı sonucu verir (parite)."""
        mudur = _personel("GÜL", "YEDİ", member_kind=MemberKind.YONETICI)
        danisman = _personel("HAKAN", "SEKİZ", member_kind=MemberKind.DIGER)
        metin = _personel_metni(
            "GÜL\tYEDİ\tOkul Müdürü\t",
            "HAKAN\tSEKİZ\tRehber Öğretmen (Psikolojik Danışman)\t",
        )

        onizleme = import_service.preview_personnel_text(text=metin)
        rapor = import_service.commit_personnel_text(text=metin)

        for r in (onizleme, rapor):
            assert (r.updated_personnel, r.unchanged_personnel, r.created_personnel) == (1, 1, 0)
            assert [(u.row_number, u.issue) for u in r.warnings] == [
                (2, import_service.MEMBER_KIND_UNCERTAIN_MESSAGE),
            ]
        mudur.refresh_from_db()
        danisman.refresh_from_db()
        assert mudur.member_kind == MemberKind.YONETICI
        assert danisman.member_kind == MemberKind.OGRETMEN
        # Mesaj bunu doğru söyler.
        assert "Mevcut kaydın görev türü değişmez." in import_service.MEMBER_KIND_UNCERTAIN_MESSAGE

    def test_supheli_gorevde_yeni_kayit_kurala_gore_acilir(self) -> None:
        rapor = import_service.commit_personnel_text(
            text=_personel_metni("GÜL\tYEDİ\tOkul Müdürü\t")
        )

        assert rapor.created_personnel == 1
        assert Personnel.objects.get().member_kind == MemberKind.DIGER

    def test_kesin_gorevde_var_olan_kaydin_turu_guncellenir(self) -> None:
        """Tam eşleşen yönetici görevi ve "öğretmen" geçen görev bugünkü gibi türü günceller."""
        ali = _personel("ALİ", "BİR", member_kind=MemberKind.OGRETMEN)
        ayse = _personel("AYŞE", "İKİ", member_kind=MemberKind.DIGER)
        metin = _personel_metni(
            "ALİ\tBİR\tMüdür Yardımcısı\t",
            "AYŞE\tİKİ\tSözleşmeli Öğretmen(657 S.K. 4/B)\t",
        )

        onizleme = import_service.preview_personnel_text(text=metin)
        ali.refresh_from_db()
        assert ali.member_kind == MemberKind.OGRETMEN  # önizleme yazmaz
        rapor = import_service.commit_personnel_text(text=metin)

        for r in (onizleme, rapor):
            assert (r.updated_personnel, r.unchanged_personnel) == (2, 0)
            assert r.warnings == []
        ali.refresh_from_db()
        ayse.refresh_from_db()
        assert ali.member_kind == MemberKind.YONETICI
        assert ayse.member_kind == MemberKind.OGRETMEN

    def test_gorev_sutunu_yoksa_ogretmen_uyarisiz(self) -> None:
        rapor = import_service.commit_personnel_text(text="Adı\tSoyadı\nALİ\tBİR")

        assert Personnel.objects.get().member_kind == MemberKind.OGRETMEN
        assert rapor.warnings == []

    def test_gorev_ve_brans_metni_hicbir_yerde_saklanmaz(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.DEBUG):
            yanit = APIClient().post(
                "/api/v1/imports/personnel/commit/", {"text": self.GOREVLI_LISTE}, format="json"
            )
        assert yanit.status_code == 200

        izler = {
            "API yanıtı": json.dumps(yanit.json(), ensure_ascii=False),
            "ImportRun.report": json.dumps(
                [r.report for r in ImportRun.objects.all()], ensure_ascii=False
            ),
            "günlük": caplog.text,
        }
        for yer, metin in izler.items():
            for gorev in ("Sözleşmeli", "Memur", "Kaptan", "Hizmetli", "Tarih", "İngilizce"):
                assert gorev not in metin, (yer, gorev)
        # Model de bu veriyi tutacak alan taşımaz.
        assert not hasattr(Personnel.objects.first(), "title")
        assert not hasattr(Personnel.objects.first(), "branch")
