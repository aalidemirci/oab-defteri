"""Gelen-giden evrak defteri ve kaydı, asgari denetim raporu, ilan kanıtının eki (F2 7. adım; tasarım
§5.2.4, §5.2.7, §5.2.8, §4.4.2 M8 ⁵, M10 ⁷; plan F2 §5.1, §6.2, §7 U12, U13).

Numara (defter, yıl, kayıt no) tekildir — sert (hesap bütünlüğü); sıra atlama uyarı + gerekçedir (akış
satırı). Karşı taraf ve konu şifrelidir, iz satırının değerlerine girmez. Rol kapısının negatif durumları
ret hiçbir şey yazmadan sınanır. Müdür ve Denetleme Kurulu çağrılarının kural testleri
`kurallar/test_genel_kurul_kurallari.py`'de, dipnot ¹ ve ⁷'nin gerçek servis testleri
`apps/okul/tests/test_yetki_kapisi.py`'dedir. Adlar ve metinler UYDURMADIR.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.oab.hatalar import DonemKapali, GerekceGerekli
from apps.oab.models import (
    AssemblyKind,
    AuditReport,
    AuditReportStatus,
    BookKind,
    BookStatus,
    ComplianceItem,
    ComplianceKind,
    DocumentDirection,
    DocumentRecord,
    OabTerm,
    OfficialBook,
    TermStatus,
)
from apps.oab.services import denetim, gelen_giden_evrak, kurullar, uyum
from apps.oab.services import genel_kurul as gk
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.okul import denetim_izi
from apps.okul.models import AccountRole, AuditTrail
from shared.exceptions import RolYetkisiz

pytestmark = pytest.mark.django_db

GUN = date(2026, 10, 1)
KARSI_TARAF = "Uydurma Kurum Müdürlüğü Pelinsu Uydurmakaya"
KONU = "Uydurma konu: gizli serbest metin örneği"
GEREKCE = uyum.Gerekce(metin="Uydurma gerekçe: önceki numara kâğıt defterde iptal edildi.")
PDF = b"%PDF-1.7 uydurma"


def _gelen(**alanlar: object) -> gelen_giden_evrak.EvrakKaydiSonucu:
    varsayilan: dict[str, object] = {
        "direction": DocumentDirection.GELEN,
        "tarih": GUN,
        "counterparty": KARSI_TARAF,
        "subject": KONU,
    }
    return gelen_giden_evrak.evrak_kaydet(**{**varsayilan, **alanlar})  # type: ignore[arg-type]


def _kayitlar() -> tuple[object, ...]:
    return (
        list(DocumentRecord.objects.order_by("pk").values()),
        list(OfficialBook.objects.order_by("pk").values()),
        list(AuditReport.objects.order_by("pk").values()),
        list(ComplianceItem.objects.order_by("pk").values()),
        AuditTrail.objects.count(),
    )


# ============================================================ defter ve numara
def test_kayit_sirayla_numaralanir_yil_tarihin_yilidir() -> None:
    """Numara verilmezse sıradaki numaradır; yıl evrakın tarihinin takvim yılıdır, yeni yılda 1'den
    başlar. Yön ve dış sayı açık, karşı taraf ve konu şifreli alandır."""
    gko.acik_donem()
    defter = gelen_giden_evrak.evrak_defteri_olustur(certified_by="IL_ILCE_MEM", page_count=100)
    assert defter.kind == BookKind.GELEN_GIDEN_EVRAK_DEFTERI
    ilk = _gelen(external_ref="E-2026-15").kayit
    ikinci = _gelen(direction=DocumentDirection.GIDEN).kayit
    yeni_yil = _gelen(tarih=date(2027, 1, 4)).kayit
    assert [(k.year, k.record_no) for k in (ilk, ikinci, yeni_yil)] == [
        (2026, 1),
        (2026, 2),
        (2027, 1),
    ]
    assert (ilk.book_id, ilk.term.status, ilk.external_ref) == (
        defter.pk,
        TermStatus.ACIK,
        "E-2026-15",
    )
    taze = DocumentRecord.objects.get(pk=ilk.pk)
    assert (taze.counterparty, taze.subject) == (KARSI_TARAF, KONU)


def test_ayni_numara_sert_reddedilir() -> None:
    """(defter, yıl, kayıt no) tekil — sert (hesap bütünlüğü: numara tekilliği); gerekçe aşamaz, hiçbir
    şey yazılmaz."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    _gelen()
    once = _kayitlar()
    with pytest.raises(ValueError, match="tekildir"):
        _gelen(record_no=1, gerekce=GEREKCE)
    assert _kayitlar() == once


def test_sira_atlama_uyari_gerekceyle_kaydedilir_bosluk_doldurma_uyarisiz() -> None:
    """Tasarım §5.2.8 "Sıra atlama uyarı": sıradakinden büyük numara gerekçesiz kaydedilmez; gerekçeyle
    kaydedilir, konusu kayıt olan atıfsız akış satırı açılır. Atlanan boş numaraya sonradan yazmak sırayı
    bozmaz, uyarı vermez."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    _gelen()
    once = _kayitlar()
    with pytest.raises(GerekceGerekli):
        _gelen(record_no=4)
    assert _kayitlar() == once
    sonuc = _gelen(record_no=4, gerekce=GEREKCE)
    assert [u["kural"] for u in sonuc.uyarilar] == [gelen_giden_evrak.SIRA_ATLAMA_AKISI]
    assert "2 bekleniyordu" in sonuc.uyarilar[0]["mesaj"]
    (satir,) = ComplianceItem.objects.filter(rule_id=gelen_giden_evrak.SIRA_ATLAMA_AKISI)
    assert (satir.kind, satir.subject_type, satir.subject_id, satir.rule_package) == (
        ComplianceKind.SAPMA,
        "oab.DocumentRecord",
        str(sonuc.kayit.pk),
        "",
    )
    dolduran = _gelen(record_no=2)
    assert dolduran.uyarilar == ()
    assert _gelen().kayit.record_no == 5


def test_gecisteki_son_sira_no_sonraki_numarayi_belirler() -> None:
    """Geçiş kaydındaki "programdan önceki son sıra no" defterin programa kaydedildiği yılın
    numarasıdır: o yılın ilk program kaydı onun bir fazlasıdır; başka yılda 1'dir. Son sıra no ve
    altındaki numaralar o yıl kâğıt defterde kullanılmıştır: elle verilse de gerekçeyle de reddedilir —
    sert (numara tekilliği), hiçbir şey yazılmaz; ertesi yılda serbesttir."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur(last_no_before_program=37)
    bu_yil = timezone.localdate().year
    once = _kayitlar()
    for numara in (1, 10, 37):
        with pytest.raises(ValueError, match="programdan önce defterde kullanıldı"):
            _gelen(tarih=date(bu_yil, 1, 2), record_no=numara, gerekce=GEREKCE)
    assert _kayitlar() == once
    assert _gelen(tarih=date(bu_yil, 1, 2)).kayit.record_no == 38
    assert _gelen(tarih=date(bu_yil + 1, 1, 2)).kayit.record_no == 1
    assert _gelen(tarih=date(bu_yil + 1, 1, 3), record_no=2).kayit.record_no == 2


def test_defter_ve_donem_kosullari() -> None:
    """Kayıt kullanımdaki gelen-giden evrak defterine ve açık birlik dönemine yazılır: defter yoksa,
    karar defteri ya da kullanımda olmayan (dolmuş) defter verilirse ya da açık dönem yoksa reddedilir;
    tarih gün olmalıdır. Ret hiçbir şey yazmaz."""
    once_donem = OabTerm.objects.count()
    with pytest.raises(ValueError, match="Açık birlik dönemi yok"):
        _gelen()
    assert OabTerm.objects.count() == once_donem
    gko.acik_donem()
    with pytest.raises(ValueError, match="defteri kaydedilmedi"):
        _gelen()
    karar = kurullar.karar_defteri_olustur()
    with pytest.raises(ValueError, match="gelen-giden evrak defteri değil"):
        _gelen(defter=karar)
    dolan = gelen_giden_evrak.evrak_defteri_olustur()
    OfficialBook.objects.filter(pk=dolan.pk).update(status=BookStatus.DOLDU)
    gelen_giden_evrak.evrak_defteri_olustur()
    once = _kayitlar()
    with pytest.raises(ValueError, match="kullanımda değil"):
        _gelen(defter=dolan)
    assert _kayitlar() == once
    with pytest.raises(ValueError, match="tarihi"):
        _gelen(tarih=datetime(2026, 10, 1, 9, 0, tzinfo=timezone.get_current_timezone()))
    with pytest.raises(ValueError, match="yönü"):
        _gelen(direction="ICERDEN")


def test_karsi_taraf_ve_konu_izde_deger_olarak_gorunmez() -> None:
    """Tasarım §5.3: karşı taraf ve konu şifreli serbest metindir; iz satırında yalnız adıyla görünür."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kayit = _gelen().kayit
    (satir,) = AuditTrail.objects.filter(model="oab.DocumentRecord", object_id=str(kayit.pk))
    metin = f"{satir.values} {satir.changed_fields}"
    assert "Pelinsu" not in metin and "gizli serbest" not in metin
    assert denetim_izi.kaydi_dogrula(DocumentRecord, kayit.pk) is True


@pytest.mark.parametrize("rol", [AccountRole.MUDUR, AccountRole.DENETLEME_KURULU])
def test_evrak_kaydini_mudur_ve_denetleme_kurulu_yazamaz(rol: AccountRole) -> None:
    """M10 (⁷): müdür ve Denetleme Kurulu gelen-giden evrakı okur; defter, kayıt ve ek yazamaz, ret hiçbir
    şey yazmaz."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kayit = _gelen().kayit
    with o.rol_olarak(rol):
        once = _kayitlar()
        with pytest.raises(RolYetkisiz):
            gelen_giden_evrak.evrak_defteri_olustur()
        with pytest.raises(RolYetkisiz):
            _gelen()
        with pytest.raises(RolYetkisiz):
            gelen_giden_evrak.evrak_kaydina_ek_ekle(kayit, PDF, dosya_adi="yazi.pdf")
        assert _kayitlar() == once
    assert not kayit.ekler().exists()


def test_evrak_kaydina_ek_yazilir_kapanmis_donemde_yazilmaz() -> None:
    """Kayıt dosya deposunun kullanıcı eki sahibidir (PDF, JPEG, PNG; `ekler()`); kapanmış dönemin
    kaydına ek yazılmaz (O2)."""
    donem = gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kayit = _gelen().kayit
    with o.rol_olarak(AccountRole.SEKRETER):
        ek = gelen_giden_evrak.evrak_kaydina_ek_ekle(kayit, PDF, dosya_adi="gelen-yazi.pdf")
    assert list(kayit.ekler()) == [ek]
    assert (ek.owner_type, ek.owner_id, ek.mime) == (
        "oab.DocumentRecord",
        str(kayit.pk),
        "application/pdf",
    )
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    with pytest.raises(DonemKapali):
        gelen_giden_evrak.evrak_kaydina_ek_ekle(kayit, PDF, dosya_adi="ikinci.pdf")
    assert kayit.ekler().count() == 1


def test_mudur_yazisi_yalniz_mudurun_eylemiyle_islenir() -> None:
    """⁷: müdür yazısını işleme yolunun kendi kapısı yoktur, müdür yazısının eyleminin içinden çağrılır;
    derin savunma olarak yazar müdür değilse ret, hiçbir şey yazılmaz."""
    donem = gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    for rol in (AccountRole.YONETICI, AccountRole.SEKRETER, AccountRole.DENETLEME_KURULU):
        with o.rol_olarak(rol):
            once = _kayitlar()
            with pytest.raises(RolYetkisiz):
                gelen_giden_evrak.mudur_yazisini_isle(donem=donem, subject="Uydurma konu")
            assert _kayitlar() == once


def test_mudurun_25_2_cagrisi_deftere_islenir() -> None:
    """md. 25/2 hâlinde müdürün olağanüstü çağrısı (yetki md. 9/6'nın 2023 ek ibaresinden): müdürün
    hesabından yazılır, yazısı evrak defterine giden evrak olarak işlenir; konu atfı md. 9/6 ve 25/2."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.MUDUR):
        sonuc = gk.cagir(
            kurul,
            called_by="MUDUR_25_2",
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
        )
    assert sonuc.kurul.call_document_id is not None
    yazi = DocumentRecord.objects.get(pk=sonuc.kurul.call_document_id)
    assert yazi.subject == "Olağanüstü genel kurul toplantı çağrısı (md. 9/6, 25/2)"
    assert yazi.counterparty == gelen_giden_evrak.MUDUR_YAZISI_MUHATABI
    assert gk.MUDUR_YAZISI_ISLENDI.format(yil=yazi.year, no=yazi.record_no) in sonuc.bilgiler
    assert gk.cagri_sahibi(sonuc.kurul) == "mudur"


def test_olaganustude_yeni_okul_cagiraninin_yazisi_olaganustu_cagri_konusuyla_islenir() -> None:
    """Plan F2 §3.2: `MUDUR_YENI_OKUL` olağanüstü genel kurulda listede olmayan çağırandır (uyarı +
    gerekçe). Müdürün yazısı evrak defterine olağan yeni okul daveti (md. 9/1) diye değil, müdürün
    olağanüstü çağrısı (md. 9/6) konusuyla işlenir; olağanda yeni okul davetinin konusu değişmez."""
    gko.acik_donem()
    gelen_giden_evrak.evrak_defteri_olustur()
    kurul = gko.planla(kind=AssemblyKind.OLAGANUSTU)
    with o.rol_olarak(AccountRole.MUDUR):
        sonuc = gk.cagir(
            kurul,
            called_by="MUDUR_YENI_OKUL",
            call_reason=gko.OLAGANUSTU_NEDEN,
            gundem=gko.OLAGANUSTU_GUNDEM,
            gerekce=gko.GEREKCE,
        )
    assert [u["kural"] for u in sonuc.uyarilar] == ["genel_kurul.olaganustu_cagiranlar"]
    assert sonuc.kurul.call_document_id is not None
    yazi = DocumentRecord.objects.get(pk=sonuc.kurul.call_document_id)
    assert yazi.subject == "Olağanüstü genel kurul toplantı çağrısı (md. 9/6)"
    assert gk.mudur_yazisi_konusu(AssemblyKind.OLAGAN, "MUDUR_YENI_OKUL") == (
        "Genel kurul toplantı çağrısı (yeni açılan okul; md. 9/1)"
    )


# ============================================================ asgari denetim raporu (U13)
@pytest.mark.parametrize(
    "rol",
    [
        AccountRole.YONETICI,
        AccountRole.BASKAN,
        AccountRole.BASKAN_YARDIMCISI,
        AccountRole.MUHASIP,
        AccountRole.SEKRETER,
        AccountRole.MUDUR,
    ],
)
def test_denetim_raporunu_yalniz_denetleme_kurulu_yazar(rol: AccountRole) -> None:
    """Tasarım §4.4.2 ⁵: Denetleme Kurulu denetim modülüne yazar; yönetim kurulu rolleri ve program
    yöneticisi yazamaz (DK, YK'nin faaliyetini inceler; md. 14/4), müdür de. Ret hiçbir şey yazmaz."""
    gko.acik_donem()
    with o.rol_olarak(rol):
        once = _kayitlar()
        with pytest.raises(RolYetkisiz):
            denetim.denetim_raporu_yaz(kind="ARA", report_date=GUN, md6_violation_found=True)
        assert _kayitlar() == once


def test_denetim_raporu_turu_ve_gunu_zorunlu_acik_doneme_yazilir() -> None:
    """U13: rapor türü ve günü zorunlu; rapor taslak açılır, açık birlik dönemine yazılır, izlidir."""
    with o.rol_olarak(AccountRole.DENETLEME_KURULU):
        with pytest.raises(ValueError, match="Açık birlik dönemi yok"):
            denetim.denetim_raporu_yaz(kind="ARA", report_date=GUN, md6_violation_found=True)
    donem = gko.acik_donem()
    with o.rol_olarak(AccountRole.DENETLEME_KURULU) as dk:
        with pytest.raises(ValueError, match="türü"):
            denetim.denetim_raporu_yaz(kind="YILLIK", report_date=GUN, md6_violation_found=True)
        with pytest.raises(ValueError, match="günü"):
            denetim.denetim_raporu_yaz(
                kind="NIHAI",
                report_date=None,  # type: ignore[arg-type]
                md6_violation_found=True,
            )
        rapor = denetim.denetim_raporu_yaz(
            kind="NIHAI", report_date=GUN, md6_violation_found=False, irregularity_found=True
        )
    assert (rapor.term_id, rapor.status, rapor.md6_violation_found, rapor.irregularity_found) == (
        donem.pk,
        AuditReportStatus.TASLAK,
        False,
        True,
    )
    (satir,) = AuditTrail.objects.filter(model="oab.AuditReport", object_id=str(rapor.pk))
    assert (str(satir.account_id), satir.role) == (str(dk.id), "denetleme_kurulu")


# ============================================================ ilan kanıtının eki
def test_ilan_kanitina_ek_ilan_ve_toplanti_rolleri_yazar() -> None:
    """İlan kaydı dosya deposunun kullanıcı eki sahibidir (kanal kanıtı: pano fotoğrafı, sayfa
    görüntüsü); eki ilan ve toplantının "Kim"i (program yöneticisi, sekreter) yazar, öteki roller
    `RolYetkisiz` alır; iptal edilmiş genel kurulun ilanına ek yazılmaz."""
    kurul = gko.ilanli_olagan()
    (duyuru,) = gk.kurulun_duyurulari(kurul)
    for rol in (AccountRole.BASKAN, AccountRole.MUDUR, AccountRole.DENETLEME_KURULU):
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            gk.ilan_kanitina_ek_ekle(duyuru, PDF, dosya_adi="pano.pdf")
    with o.rol_olarak(AccountRole.SEKRETER):
        ek = gk.ilan_kanitina_ek_ekle(duyuru, PDF, dosya_adi="pano.pdf")
    assert list(duyuru.ekler()) == [ek]
    assert ek.owner_type == "oab.Announcement"
    gk.iptal_et(kurul, cancel_reason="Uydurma: tarih yanlış girildi.")
    with pytest.raises(ValueError):
        gk.ilan_kanitina_ek_ekle(duyuru, PDF, dosya_adi="ikinci.pdf")
    assert duyuru.ekler().count() == 1
