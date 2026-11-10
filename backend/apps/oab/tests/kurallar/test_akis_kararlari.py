"""Akış, model ve KVKK kararları (`ak`, tasarım §10.7; F1c 5. adım: organ üyeliğinin kısıtları).

`OrganMembership`'in iki kısmi tekil kısıtı, ikisi de `IPTAL` olmayan kayıtlarda (tasarım §5.2.2; plan
F1c kararları; denetim UY-10): genel kurul bağı boşken (dönem, organ, kişi, temsil türü), doluyken
(dönem, organ, kişi, genel kurul). SQLite tekil dizinde NULL'ları ayrı saydığından tek kısıt genel
kurul dışı seçimlerde etkisiz kalırdı. Geçiş kurulumunda görevdeki kurul `DEVRALINAN` üyelikle aday
şartı olmadan seçilmiş açılır (§7.9); toplu sayaç beyanı geçiş kurulumunun adımıdır (8. adım).
Bir kişi aynı dönemde aynı kurulda tek koltuk tutar (kullanıcı kararı 10.11.2026; dosyanın sonu).
Kişi adları UYDURMADIR.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import IntegrityError, transaction

from apps.oab.models import (
    DropKind,
    ElectedBy,
    MembershipSource,
    MembershipStatus,
    OrganMembership,
    Representation,
    SeatGroup,
)
from apps.oab.services import uyelikler
from apps.oab.tests import uyelik_ortak as o

pytestmark = pytest.mark.django_db


def _ham(**alanlar: Any) -> OrganMembership:
    """Kısıtın kendisini sınamak için servissiz yazım (servis aynı durumu Türkçe iletiyle keser)."""
    varsayilan: dict[str, Any] = {
        "organ": "YK",
        "seat_type": "ASIL",
        "elected_by": ElectedBy.GENEL_KURUL,
        "status": MembershipStatus.SECILDI,
    }
    return OrganMembership.objects.create(**{**varsayilan, **alanlar})


def test_genel_kurulsuz_ayni_uyelik_iki_kez_reddedilir() -> None:
    donem = o.donem()
    kisi = o.kisi()
    o.devralinan(donem, kisi)
    with pytest.raises(ValueError, match="zaten var"):
        o.devralinan(donem, kisi)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=kisi)
    assert OrganMembership.objects.count() == 1


def test_iptal_uyelik_tekil_kisita_girmez() -> None:
    donem = o.donem()
    kisi = o.kisi()
    yanlis = o.devralinan(donem, kisi)
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    yeniden = o.devralinan(donem, kisi)
    assert yeniden.pk != yanlis.pk
    assert OrganMembership.objects.filter(person=kisi).count() == 2
    # Genel kurullu kısıtta da `IPTAL` kısıt dışıdır.
    kurul = o.olaganustu_genel_kurul(donem)
    ikinci = o.kisi()
    aday = o.yk_adayi(donem, ikinci, kurul)
    aday.status = MembershipStatus.IPTAL
    aday.save(update_fields=["status"])
    assert o.yk_adayi(donem, ikinci, kurul).status == MembershipStatus.ADAY


def test_genel_kurulsuz_kisitta_temsil_turu_ayirir() -> None:
    """Aynı veli iki kurulda temsilci olabilir; aynı kurulda iki kez olamaz (plan F1c kararları)."""
    donem = o.donem()
    kisi = o.kisi()
    temsilci = {"term": donem, "person": kisi, "organ": "TEMSILCI", "elected_by": "YK_KARARI"}
    _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    _ham(**temsilci, representation=Representation.SOSYAL_ETKINLIKLER_KURULU)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    assert OrganMembership.objects.filter(organ="TEMSILCI").count() == 2
    # Temsil türü temsilcide zorunlu, öteki organlarda boş dizedir (`NULL` değil).
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(**{**temsilci, "person": o.kisi()}, representation="")
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=o.kisi(), representation=Representation.DIGER)


def test_genel_kurullu_kisit_genel_kurulu_ayirir() -> None:
    """Aynı kişi aynı genel kurulda iki kez aday olamaz; başka genel kurulda olabilir (md. 13/8)."""
    donem = o.donem()
    kisi = o.kisi()
    ilk = o.olaganustu_genel_kurul(donem)
    o.yk_adayi(donem, kisi, ilk)
    with pytest.raises(ValueError, match="zaten var"):
        o.yk_adayi(donem, kisi, ilk)
    with pytest.raises(IntegrityError), transaction.atomic():
        _ham(term=donem, person=kisi, assembly=ilk, status=MembershipStatus.ADAY)
    ikinci = o.olaganustu_genel_kurul(donem)
    assert o.yk_adayi(donem, kisi, ikinci).status == MembershipStatus.ADAY


def test_devralinan_uyelik_aday_sarti_olmadan_secildi() -> None:
    """Geçiş kurulumunda görevdeki kurul devralınan üyelikle, aday kaydı olmadan seçilmiş açılır;
    genel kurul bağı yoktur, koltuk uygunluğu yine serttir (§7.9)."""
    donem = o.donem()
    uyelik = o.devralinan(donem, o.kisi(), role="BASKAN")
    assert (uyelik.status, uyelik.source, uyelik.assembly_id) == (
        MembershipStatus.SECILDI,
        MembershipSource.DEVRALINAN,
        None,
    )
    assert uyelik.start_date == o.GUN
    assert not OrganMembership.objects.filter(status=MembershipStatus.ADAY).exists()
    kurul = o.olaganustu_genel_kurul(donem)
    with pytest.raises(ValueError, match="yalnız genel kurul seçiminde"):
        uyelikler.assign_membership(
            term=donem,
            person=o.kisi(),
            organ="YK",
            seat_type="ASIL",
            elected_by=ElectedBy.GENEL_KURUL,
            assembly=kurul,
            source=MembershipSource.DEVRALINAN,
        )


# ============================================================ tek koltuk (kullanıcı kararı 10.11.2026)
# Bir kişi aynı dönemde aynı kurulda tek koltuk tutar (sert, hesap bütünlüğü; plan F1c 5. adım
# notları). Koltuk seçilmiş kayıttır: aday, düşmüş ve iptal kaydı koltuk değildir. Kural yalnız
# yönetim kurulunda ve Denetleme Kurulunda uygulanır.


def _dusur(uyelik: OrganMembership, tur: str) -> None:
    """Düşme servisi 6. adımda; durum makinesi geçişi ORM'le."""
    uyelik.status, uyelik.drop_kind = MembershipStatus.DUSTU, tur
    uyelik.save(update_fields=["status", "drop_kind"])


def test_dusen_uye_ayni_donemde_ayni_kurula_yeniden_secilebilir() -> None:
    """Olağanüstü genel kurul aynı dönemde yeni kurul seçer, görevdeki eski üyelikler düşer
    (`OLAGANUSTU_GK_SECIMI`; tasarım §7.1, md. 13/8); eski üye yeniden seçilebilir. Düşmüş kayıt
    koltuk değildir; seçilme sayacına ise ikisi de girer (§15 B-12)."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    kurul = o.olaganustu_genel_kurul(donem)
    eski = o.devralinan(donem, kisi)
    aday = o.yk_adayi(donem, kisi, kurul)  # aday kaydı koltuk değil: görevdeki üye aday olabilir
    with pytest.raises(ValueError, match="tek koltuk"):
        uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    _dusur(eski, DropKind.OLAGANUSTU_GK_SECIMI)
    yeni = uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU)
    assert yeni.status == MembershipStatus.SECILDI
    durumlar = sorted(OrganMembership.objects.filter(person=kisi).values_list("status", flat=True))
    assert durumlar == [MembershipStatus.DUSTU, MembershipStatus.SECILDI]


def test_secilmeyen_aday_kaydi_koltuk_degil() -> None:
    """Seçilmeyen aday kaydı aday kalır; aynı kişi dönemin başka genel kurulunda seçilebilir
    (md. 13/8). Aday kaydı koltuk değildir: seçilme anında yalnız seçilmiş kayıtlar sayılır."""
    donem = o.donem()
    kisi = o.kisi(external_yk_terms=0)
    ilk = o.yk_adayi(donem, kisi, o.olaganustu_genel_kurul(donem))
    ikinci = o.yk_adayi(donem, kisi, o.olaganustu_genel_kurul(donem))
    assert uyelikler.elect_membership(ikinci, start_date=o.SECIM_GUNU).status == (
        MembershipStatus.SECILDI
    )
    assert OrganMembership.objects.get(pk=ilk.pk).status == MembershipStatus.ADAY


def test_iptal_kayit_koltuk_degil() -> None:
    """İptal edilmiş kayıt hiç olmamıştır (yanlış kayıt): aynı kurulda başka koltuğu engellemez."""
    donem = o.donem()
    kisi = o.ogretmen(is_parent=True)
    yanlis = o.dk_ogretmeni(donem, kisi)
    yanlis.status = MembershipStatus.IPTAL
    yanlis.save(update_fields=["status"])
    kurul = o.olaganustu_genel_kurul(donem)
    aday = uyelikler.assign_membership(
        term=donem,
        person=kisi,
        organ="DK",
        seat_type="ASIL",
        seat_group=SeatGroup.VELI,
        elected_by=ElectedBy.GENEL_KURUL,
        assembly=kurul,
    )
    assert uyelikler.elect_membership(aday, start_date=o.SECIM_GUNU).status == (
        MembershipStatus.SECILDI
    )


def test_tek_koltuk_temsilcide_uygulanmaz() -> None:
    """Temsilcide temsil türleri ayrı koltuktur (genel kurulsuz tekil kısıt temsil türüyle ayırır):
    aynı veli iki kurulda temsilci olabilir; tek koltuk yalnız yönetim kurulu ve Denetleme Kurulunda."""
    assert frozenset({"YK", "DK"}) == uyelikler.TEK_KOLTUKLU_KURULLAR
    donem = o.donem()
    kisi = o.kisi()
    temsilci = {"term": donem, "person": kisi, "organ": "TEMSILCI", "elected_by": "YK_KARARI"}
    _ham(**temsilci, representation=Representation.ODUL_DISIPLIN_KURULU)
    ikinci = _ham(**temsilci, representation=Representation.SOSYAL_ETKINLIKLER_KURULU)
    assert not uyelikler._ikinci_koltuk(ikinci)
    # Aynı durum yönetim kurulunda ikinci koltuktur (servis dışı yazılmış kayıt üstünde).
    _ham(term=donem, person=kisi, assembly=o.olaganustu_genel_kurul(donem))
    yk = _ham(term=donem, person=kisi, assembly=o.olaganustu_genel_kurul(donem))
    assert uyelikler._ikinci_koltuk(yk)
