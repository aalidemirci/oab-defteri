"""Kural sürümü güncellemesinin ucu (tasarım §6.2-5; plan F2 §6.1, 2. adım).

Servisin kuralları `kurallar/test_kural_paketi.py`'dedir (`kp::`); burada ucun sözleşmesi sınanır: fark
okuması (en yeni revizyon varsayılan hedef, kural satırları açıklama ve atıfla, kimlik ekranda değil),
hedefler (programla gelen daha yeni revizyonlar ve dönemin önceki bağları; hiç bağlanmadığı eski
revizyon ve kopyası bozuk sürüm hedef değil, 400), geçiş, denetim izi, kapanmış dönemde 409
`donem_kapali`, paket yüklenemezse (D1) geçilemez ve 503, etkilenen kayıtta onay (409
`revizyon_onayi_gerekli`), olmayan revizyonda 400 ve rol kapısı: okuma da yazma da yalnız program
yöneticisinin (Ayarlar satırı, kural sürümü seçimi), öteki her rol 403 alır ve bağ değişmez. Durum
F1 kurulumunun hâlidir: dönem `r1` dağıtılmışken açıldı, program `r2` ile güncellendi. Adlar UYDURMADIR.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.oab.kurallar import yukleyici as yk
from apps.oab.models import (
    ComplianceItem,
    ComplianceKind,
    OabTerm,
    RulePackage,
    TermStatus,
)
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import paket_ortak
from apps.okul.models import AccountRole, AuditAction, AuditTrail

pytestmark = pytest.mark.django_db

PAKET = "OAB-2023.12"
R1 = paket_ortak.oku("OAB-2023.12.r1.json")


def _yol(donem: OabTerm) -> str:
    return f"/api/v1/oab/terms/{donem.pk}/rule-revision/"


def _dagit(monkeypatch: pytest.MonkeyPatch, *icerikler: dict[str, Any]) -> None:
    monkeypatch.setattr(
        yk._Onbellek,
        "durum",
        yk.PaketDurumu(paketler=tuple(yk.Paket.sozlukten(icerik) for icerik in icerikler)),
    )


def _r1e_bagli_donem(monkeypatch: pytest.MonkeyPatch) -> OabTerm:
    """Dönem yalnız `r1` dağıtılmışken açılır; sonra programla gelen bütün revizyonlar dağıtılır."""
    _dagit(monkeypatch, R1)
    donem = o.donem()
    _dagit(monkeypatch, *paket_ortak.REVIZYONLAR)
    return donem


def _bag(donem: OabTerm) -> tuple[str, int]:
    guncel = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    return str(guncel.rule_package.package), int(guncel.rule_package.rev)


def _istek(rol: AccountRole, yontem: str, yol: str, govde: dict[str, Any] | None = None) -> Any:
    def gonder() -> Any:
        istemci = APIClient()
        if yontem == "GET":
            return istemci.get(yol)
        return istemci.post(yol, govde or {}, format="json")

    if rol == AccountRole.YONETICI:
        return gonder()
    with o.rol_olarak(rol):
        return gonder()


def test_fark_okumasi_en_yeni_revizyona_kural_satirlariyla(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _r1e_bagli_donem(monkeypatch)
    yanit = APIClient().get(_yol(donem))
    assert yanit.status_code == 200, yanit.content
    veri = yanit.json()
    assert veri["bagli"] == {"paket": PAKET, "rev": 1}
    assert veri["en_yeni"] == veri["hedef"] == {"paket": PAKET, "rev": 2}
    assert veri["hedefler"] == [{"paket": PAKET, "rev": 2}]
    assert veri["gecilebilir"] is True
    fark = veri["fark"]
    assert (fark["eski"], fark["yeni"]) == ({"paket": PAKET, "rev": 1}, {"paket": PAKET, "rev": 2})
    assert len(fark["eklenen"]) == 8
    assert [s["id"] for s in fark["duzeltilen"]] == ["genel_kurul.olagan_son_ay"]
    assert fark["cikarilan"] == fark["biten"] == fark["deger_degisen"] == []
    assert fark["kayitlar"] == []
    assert fark["onay_gerekli"] is False
    for satir in [*fark["eklenen"], *fark["duzeltilen"]]:
        assert satir["aciklama"].strip(), satir
        assert satir["atif"].startswith("md. "), satir
    assert _bag(donem) == (PAKET, 1)  # okuma yazmaz


def test_en_yeni_revizyondaki_donemde_fark_bos_eski_revizyon_hedef_degil(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§6.2-4: dönem açılışta en yeni revizyona bağlanır; hiç bağlanmadığı eski revizyon (`r1`) geri
    alma hedefi değildir (§6.2-5 yapılmış geçişin geri alınmasıdır): okuması da geçişi de 400."""
    donem = o.donem()
    veri = APIClient().get(_yol(donem)).json()
    assert veri["bagli"] == veri["hedef"] == {"paket": PAKET, "rev": paket_ortak.EN_YENI_REV}
    assert veri["fark"] is None
    assert veri["hedefler"] == []
    assert APIClient().get(_yol(donem), {"paket": PAKET, "rev": "1"}).status_code == 400
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 1, "onay": True}, format="json")
    assert yanit.status_code == 400, yanit.content
    assert _bag(donem) == (PAKET, paket_ortak.EN_YENI_REV)
    assert not AuditTrail.objects.filter(model="kural.revizyon_gecisi").exists()


def test_gecilen_donemde_onceki_bag_geri_alma_hedefidir(monkeypatch: pytest.MonkeyPatch) -> None:
    """§6.2-5: `r1`'den `r2`'ye geçmiş dönemde `r1` geri alma hedefidir; geri alınınca `r2` yeniden
    ileri hedef olur."""
    donem = _r1e_bagli_donem(monkeypatch)
    assert (
        APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json").status_code == 200
    )
    veri = APIClient().get(_yol(donem)).json()
    assert veri["hedefler"] == [{"paket": PAKET, "rev": 1}]
    assert veri["fark"] is None  # en yeni revizyon dönemin bağı
    geri = APIClient().get(_yol(donem), {"paket": PAKET, "rev": "1"}).json()
    assert len(geri["fark"]["cikarilan"]) == 8
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 1}, format="json")
    assert yanit.status_code == 200, yanit.content
    assert _bag(donem) == (PAKET, 1)
    assert APIClient().get(_yol(donem)).json()["hedefler"] == [{"paket": PAKET, "rev": 2}]


def _sentetik_r3() -> dict[str, Any]:
    """Programla gelmiş gibi gösterilen, en yeni gerçek revizyonun aynısı bir üst revizyon."""
    icerik = deepcopy(paket_ortak.EN_YENI)
    icerik["rev"] = paket_ortak.EN_YENI_REV + 1
    icerik["degisiklikler"] = []
    return icerik


def test_dagitilmayan_onceki_bag_kopyasindan_hedeftir_bozuk_kopya_hedef_degil(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geri alma hedefi programla gelmese de dondurulmuş kopyasından okunur (§6.2-5); dönemin bağı ve
    hiç bağlanmadığı eski revizyon listede yoktur; kopyası tutmayan hedef listelenmez, okuması da
    geçişi de 400 (D7)."""
    son = paket_ortak.EN_YENI_REV
    r3 = _sentetik_r3()
    donem = o.donem()  # açılış bağı en yeni gerçek revizyon
    _dagit(monkeypatch, *paket_ortak.REVIZYONLAR, r3)
    gecis = APIClient().post(_yol(donem), {"paket": PAKET, "rev": son + 1}, format="json")
    assert gecis.status_code == 200, gecis.content
    # Program sentetik revizyonu artık taşımıyor; dönem dağıtılandan yeni (ör. yedekten dönüş).
    _dagit(monkeypatch, *paket_ortak.REVIZYONLAR)
    veri = APIClient().get(_yol(donem)).json()
    assert veri["hedefler"] == [{"paket": PAKET, "rev": son}]
    assert (veri["hedef"], veri["fark"]) == (None, None)
    geri = APIClient().post(_yol(donem), {"paket": PAKET, "rev": son}, format="json")
    assert geri.status_code == 200, geri.content
    # Geri alınan sentetik revizyon programda yok; kopyasından hedeftir.
    veri = APIClient().get(_yol(donem)).json()
    assert veri["hedefler"] == [{"paket": PAKET, "rev": son + 1}]
    assert veri["fark"] is None  # en yeni dağıtılan dönemin bağı
    sorgu = {"paket": PAKET, "rev": str(son + 1)}
    assert APIClient().get(_yol(donem), sorgu).json()["fark"]["eski"] == {
        "paket": PAKET,
        "rev": son,
    }

    kopya = RulePackage.objects.get(package=PAKET, rev=son + 1)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE oab_rulepackage SET content = json_set(content, '$.bozuk', 1) WHERE id = %s",
            [kopya.pk],
        )
    assert APIClient().get(_yol(donem)).json()["hedefler"] == []
    assert APIClient().get(_yol(donem), sorgu).status_code == 400
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": son + 1}, format="json")
    assert yanit.status_code == 400, yanit.content
    assert _bag(donem) == (PAKET, son)


def test_paket_yuklenemezse_gecilemez_gecis_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """D1: `gecilebilir` geçişin kapısıyla aynı ölçüdür; paket yüklenemezse onay düğmesi kapalı, geçiş
    503 `kural_paketi_yok`, bağ değişmez."""
    donem = _r1e_bagli_donem(monkeypatch)
    monkeypatch.setattr(yk._Onbellek, "durum", yk.PaketDurumu(hatalar=("Uydurma D1 hatası",)))
    veri = APIClient().get(_yol(donem)).json()
    assert veri["gecilebilir"] is False
    assert (veri["en_yeni"], veri["hedefler"], veri["fark"]) == (None, [], None)
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json")
    assert yanit.status_code == 503, yanit.content
    assert yanit.json()["code"] == "kural_paketi_yok"
    assert _bag(donem) == (PAKET, 1)


def test_gecis_ucu_baglar_ve_denetim_izine_yazar(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _r1e_bagli_donem(monkeypatch)
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json")
    assert yanit.status_code == 200, yanit.content
    veri = yanit.json()
    assert veri["kural_paketi"] == {"paket": PAKET, "rev": 2}
    assert len(veri["fark"]["eklenen"]) == 8
    assert _bag(donem) == (PAKET, 2)
    olay = AuditTrail.objects.get(model="kural.revizyon_gecisi", object_id=str(donem.pk))
    assert olay.values == {"paket": [PAKET, PAKET], "rev": [1, 2]}
    assert olay.term_id == donem.pk
    assert olay.account_id is not None
    guncelleme = AuditTrail.objects.filter(
        model="oab.OabTerm", object_id=str(donem.pk), action=AuditAction.GUNCELLE
    ).latest("seq")
    assert "rule_package" in guncelleme.changed_fields
    assert guncelleme.account_id == olay.account_id
    # Aynı sürüme ikinci geçiş yapılmaz.
    yeniden = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json")
    assert yeniden.status_code == 400, yeniden.content


def test_kapanmis_donemde_gecis_409_bag_degismez(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _r1e_bagli_donem(monkeypatch)
    OabTerm.objects.filter(pk=donem.pk).update(
        status=TermStatus.KAPANDI, end_date=date(2027, 10, 1)
    )
    assert APIClient().get(_yol(donem)).json()["gecilebilir"] is False
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json")
    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "donem_kapali"
    assert _bag(donem) == (PAKET, 1)
    assert not AuditTrail.objects.filter(model="kural.revizyon_gecisi").exists()


def test_etkilenen_kayitta_gecis_onay_ister(monkeypatch: pytest.MonkeyPatch) -> None:
    """§6.2-3a: düzeltilen kuralın açık satırı varsa fark onu listeler, geçiş onaysız yapılmaz."""
    donem = _r1e_bagli_donem(monkeypatch)
    satir = ComplianceItem.objects.create(
        term=donem,
        kind=ComplianceKind.EKSIK,
        rule_id="genel_kurul.olagan_son_ay",
        rule_package=PAKET,
        rev=1,
        message="Uydurma ileti",
    )
    fark = APIClient().get(_yol(donem)).json()["fark"]
    assert fark["kayitlar"] == [
        {
            "model": "oab.ComplianceItem",
            "kayit_id": str(satir.pk),
            "kural_id": "genel_kurul.olagan_son_ay",
        }
    ]
    assert fark["onay_gerekli"] is True
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2}, format="json")
    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "revizyon_onayi_gerekli"
    assert _bag(donem) == (PAKET, 1)
    onayli = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 2, "onay": True}, format="json")
    assert onayli.status_code == 200, onayli.content
    assert _bag(donem) == (PAKET, 2)


def test_olmayan_revizyon_ve_bozuk_sorgu_400(monkeypatch: pytest.MonkeyPatch) -> None:
    donem = _r1e_bagli_donem(monkeypatch)
    assert APIClient().get(_yol(donem), {"paket": PAKET, "rev": "9"}).status_code == 400
    assert APIClient().get(_yol(donem), {"paket": PAKET, "rev": "iki"}).status_code == 400
    yanit = APIClient().post(_yol(donem), {"paket": PAKET, "rev": 9}, format="json")
    assert yanit.status_code == 400, yanit.content
    assert _bag(donem) == (PAKET, 1)


@pytest.mark.parametrize("rol", [r for r in AccountRole if r != AccountRole.YONETICI])
def test_okuma_ve_gecis_yalniz_program_yoneticisinin(
    monkeypatch: pytest.MonkeyPatch, rol: AccountRole
) -> None:
    """Tasarım §4.4.2 Ayarlar satırı (kural sürümü seçimi: yalnız yonetici), §6.2-5; plan F2 §6.1."""
    donem = _r1e_bagli_donem(monkeypatch)
    assert _istek(rol, "GET", _yol(donem)).status_code == 403
    yanit = _istek(rol, "POST", _yol(donem), {"paket": PAKET, "rev": 2, "onay": True})
    assert yanit.status_code == 403, yanit.content
    assert yanit.json()["code"] == "rol_yetkisiz"
    assert _bag(donem) == (PAKET, 1)
    assert not AuditTrail.objects.filter(model="kural.revizyon_gecisi").exists()
