"""Evrak kuralları — F1b'de hesap teslim pusulası (E63; plan F1b-2 "E63 hesap teslim pusulası").

Tasarım §10.5'in `ev::` testlerinden bu fazın payı; dosya F1c'de §10.1 dizinine taşınır (plan):

* `test_e63_pusulada_parola_alani_yok` — içerik modelinde ve PDF'te parola alanı, parola değeri ya
  da parola için boş satır yok; giriş adı, rol, iş özeti, BSG Yön. md. 9/2 kuralları, kilitleme ve
  "kapalı zarf" cümlesi var; dosyası saklanmaz.
* `test_katalog_kabul[E63]` — tasarım §9.6 "Kabul örneği" sütunu.
* `test_sayfa_butcesi[E63]` — gerçek uzunlukta uydurma veriyle (en uzun tanıtıcı, uzun okul ve ilçe
  adı, her rol): program yöneticisinin pusulası en çok iki, öteki rollerinki bir sayfa (kullanıcı
  kararı 04.11.2026; program yöneticisinin iş listesi fazlarla en çok uzayandır).
* `test_tckn_hicbir_belgede_yok` — programın bugün ürettiği belgelerde 11 haneli kimlik deseni yok
  (K9 ayarının kolları bağış kaydıyla F3'te gelir).

Ayrıca: ad-soyad basılmaz (hesap sahibinin de basanın da); kendi hesabına, kapalı hesaba ve kaydı ya
da izi tutmayan hesaba basılmaz (satırın `pusula` eylemi aynı nedeni söyler; mühür reddi de `BUTUNLUK`
satırı yazar, orkestratör maddesi F-1); izi `BASIM` satırıdır (kod ve PDF'in sha256'sı), erişim
günlüğüne girmez, hesabın satır izini değiştirmez; yanıt `no-store`, yalnız PDF; dosya adı rol
etiketini taşır, tanıtıcıyı taşımaz (F-2); iz yazılamazsa PDF verilmez; çizim sürerken kapatılan
hesaba basılmaz; "bu programda sizin işiniz" yalnız bugün programda yapılabilen işlerdir, her parça var
olan bir uca bağlıdır (F-4); atıflar korpusla doğrulanır; metinler sözlükte; içerik model sabitlerine
(parola kuralı, askı eşiği) bağlıdır.

Adlar, numaralar ve parolalar UYDURMADIR; T.C. kimlik numarası çalışırken üretilir (sözlük §2.1).
"""

from __future__ import annotations

import hashlib
import inspect
import io
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import pytest
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pypdf import PdfReader
from rest_framework.test import APIClient

from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import (
    AccessLog,
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditTrail,
    SchoolConfig,
)
from apps.okul.oturum import Yazar, rol_etiketi, yazar_olarak
from apps.okul.rol_izinleri import ROLLER, Satir, etkin_hucreler
from apps.okul.services import (
    app_password,
    hesap_kurallari,
    hesap_teslim_pusulasi,
    hesaplar,
    recovery_key_document,
)
from apps.okul.services import hesap_teslim_pusulasi as e63
from apps.okul.tests.hesap_ortak import (
    geri_sarilmis,
    ham_guncelle,
    hesap_ac,
    iz_dolgusu,
    iz_tetikleyicisiz,
    izde_bosluk_sonra_yoneticiyi_tazele,
    muhurle,
)
from conftest import TEST_DEK, TEST_HESAP_ADI, TEST_HESAP_ID, TEST_KURTARMA_ANAHTARI, TEST_PAROLA
from shared import evrak
from shared.exceptions import IZ_YAZILAMADI_KODU, IZ_YAZILAMADI_MESAJI, RolYetkisiz
from shared.letterhead import letterhead_unit
from shared.text import tr_upper

pytestmark = pytest.mark.django_db

API = "/api/v1/accounts/"
#: Uydurma geçici parola (politikaya uyar; aranacak belirgin dizgi).
GIZLI_GECICI = "Zarf-Icindeki-Gecici-9!"
#: Uydurma hesap sahibi (aranacak belirgin ad ve soyad).
UYDURMA_AD = "Pelinsu"
UYDURMA_SOYAD = "Uydurmakaya"
OKUL_ADI = "Örnek Ortaokulu"
#: Gerçek uzunlukta uydurma künye (sayfa bütçesi).
UZUN_OKUL = "Örnek Şehit Öğretmen Ayşe Örnekoğlu Mesleki ve Teknik Anadolu Lisesi"
UZUN_ILCE = "Örnekşehirköyübeldesi"
EN_UZUN_TANITICI = "a" * hesap_kurallari.MAX_LOGIN_NAME_LENGTH
#: Parola için alan ya da boş satır kalıpları (etiket + iki nokta; doldurma çizgisi).
_PAROLA_ETIKETI = re.compile(r"(?i)(geçici\s+)?(parola|şifre)\s*[:：]")
_DOLDURMA = re.compile(r"_{3,}|\.{4,}|…{2,}|-{4,}")
_ONBIR_HANE = re.compile(r"(?<!\d)\d{11}(?!\d)")
#: Tasarım §9.6'nın kabul örneğindeki cümle (BİREBİR).
ZARF_CUMLESI = (
    "İlk parolanız ayrı kapalı zarftadır; parolanızı kimseyle paylaşmayın, görünür yere yazmayın"
)


# ============================================================ yardımcılar


def _okul(**alanlar: Any) -> SchoolConfig:
    okul = SchoolConfig.load()
    for ad, deger in {"school_name": OKUL_ADI, "district": "Örnek İlçe", **alanlar}.items():
        setattr(okul, ad, deger)
    okul.save()
    return okul


def _bas(hesap_id: object) -> Any:
    return APIClient().post(f"{API}{hesap_id}/handover-slip/")


def _pdf(yanit: Any) -> bytes:
    return b"".join(yanit.streaming_content)


def _metin(pdf: bytes) -> str:
    return "\n".join(sayfa.extract_text() or "" for sayfa in PdfReader(io.BytesIO(pdf)).pages)


def _duz(metin: str) -> str:
    """Boşluksuz metin (PDF satır sonları ve iki yana yaslama karşılaştırmayı bozmasın)."""
    return re.sub(r"\s+", "", metin)


@pytest.fixture
def yakalanan(monkeypatch: pytest.MonkeyPatch) -> list[evrak.Belge]:
    """Servisin çizdiği içerik modeli (gerçek çizici koşar)."""
    belgeler: list[evrak.Belge] = []
    asil = evrak.pdf_ciz

    def ciz(belge: evrak.Belge, sablonlar: Path | None = None) -> bytes:
        belgeler.append(belge)
        return asil(belge, sablonlar)

    monkeypatch.setattr(evrak, "pdf_ciz", ciz)
    return belgeler


def _hucreler(belge: evrak.Belge) -> list[str]:
    return [
        hucre
        for blok in belge.bloklar
        if isinstance(blok, evrak.Tablo)
        for satir in (blok.basliklar, *blok.satirlar)
        for hucre in satir
    ]


def _tablo(belge: evrak.Belge, baslik: str) -> evrak.Tablo:
    return next(b for b in belge.bloklar if isinstance(b, evrak.Tablo) and b.basliklar[0] == baslik)


def _dosyalar() -> dict[str, tuple[int, int]]:
    """Programın dosya yazabildiği dizinler: veri dizini (veritabanı hariç), güvenlik, yedek."""
    kokler = [
        Path(settings.DATA_DIR),
        app_password.state_path().parent,
        Path(app_password.backup_dir()),
    ]
    sonuc: dict[str, tuple[int, int]] = {}
    for kok in kokler:
        if not kok.is_dir():
            continue
        for yol in kok.rglob("*"):
            if yol.is_file() and not yol.name.startswith("db.sqlite3"):
                bilgi = yol.stat()
                sonuc[str(yol)] = (bilgi.st_size, bilgi.st_mtime_ns)
    return sonuc


def _son_seq() -> int:
    bas = denetim_izi.zincir_basi()
    return 0 if bas is None else int(bas[0])


def _saglamali_uydurma_numara(ilk_dokuz: str) -> str:
    """T.C. kimlik numarası sağlamasına UYAN uydurma numara (kaynakta hazır yazılmaz; sözlük §2.1)."""
    hane = [int(k) for k in ilk_dokuz]
    tek = hane[0] + hane[2] + hane[4] + hane[6] + hane[8]
    cift = hane[1] + hane[3] + hane[5] + hane[7]
    onuncu = (tek * 7 - cift) % 10
    return f"{ilk_dokuz}{onuncu}{(sum(hane) + onuncu) % 10}"


# ============================================================ ev:: testleri


@pytest.mark.parametrize("rol", [AccountRole.MUHASIP, AccountRole.YONETICI])
def test_e63_pusulada_parola_alani_yok(rol: str, yakalanan: list[evrak.Belge]) -> None:
    """İçerik modelinde ve PDF'te parola alanı, parola değeri ya da parola için boş satır yok;
    giriş adı, rol, iş özeti, BSG Yön. md. 9/2 kuralları, kilitleme ve kapalı zarf cümlesi var;
    dosyası saklanmaz."""
    _okul()
    tanitici = "yonetici-2" if rol == AccountRole.YONETICI else "muhasip"
    hesap = hesap_ac(rol, tanitici=tanitici, ad="Uydurma Hesap Sahibi", parola=GIZLI_GECICI)
    once = _dosyalar()

    yanit = _bas(hesap.id)

    assert yanit.status_code == 200, getattr(yanit, "content", b"")[:300]
    pdf = _pdf(yanit)
    (belge,) = yakalanan
    metin, json_metni = _metin(pdf), evrak.kanonik_json(belge)
    # Parola alanı yok: etiketli alan, parola başlıklı sütun, boş ya da doldurma çizgili hücre.
    assert {b for b in _hucreler(belge) if not b.strip() or _DOLDURMA.search(b)} == set()
    basliklar = {h for b in belge.bloklar if isinstance(b, evrak.Tablo) for h in b.basliklar}
    assert basliklar == {*e63.KUNYE_BASLIKLARI, e63.IS_BASLIGI}
    for parca in (*evrak.metin_akisi(belge), metin):
        assert not _PAROLA_ETIKETI.search(parca), parca
        assert not _DOLDURMA.search(parca), parca
    # Parola değeri yok (geçici parola, basan program yöneticisinin parolası): ne modelde ne
    # PDF'te ne de PDF'in ham baytlarında.
    for gizli in (GIZLI_GECICI, TEST_PAROLA):
        assert gizli not in json_metni and gizli not in metin
        assert gizli.encode() not in pdf
    # Olması gerekenler.
    duz = _duz(metin)
    for beklenen in (
        tanitici,
        rol_etiketi(rol),
        *e63.isler(rol),
        *e63.PAROLA_KURALLARI,
        e63.KILITLE,
        e63.ARTAN_BEKLEME,
        e63.KAPALI_ZARF,
    ):
        assert _duz(beklenen) in duz, beklenen
    assert "(BSGYön.)md.9/2-ave9/2-b" in duz and "BSGYön.md.9/2-ç" in duz
    assert _dosyalar() == once, "pusulanın dosyası saklanmamalı"


@pytest.mark.parametrize("kod", ["E63"])
def test_katalog_kabul(kod: str, yakalanan: list[evrak.Belge]) -> None:
    """Tasarım §9.6 E63 "Kabul örneği": tanıtıcı, rol ve "bu programda sizin işiniz" matristen; ilk
    giriş adımları (geçici parolayla giriş → parolayı değiştirme); parola kuralları (BSG 9/2-a, b,
    ç); kilitleme (boşta kilit, "Kilitle", yanlış denemede artan bekleme); parola alanı yok; kapalı
    zarf cümlesi (9/2-e, 10/1); kişisel veri dipnotu; dosya saklanmaz. Plan: yalnız PDF, antet
    okulun, imza blokları elle, RYUE unsurları ve konum cümlesi yok."""
    assert kod == e63.KOD
    _okul(idle_lock_minutes=15)
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")

    yanit = _bas(hesap.id)

    assert yanit.status_code == 200
    assert yanit["Content-Type"] == "application/pdf"
    pdf = _pdf(yanit)
    assert pdf.startswith(b"%PDF")
    (belge,) = yakalanan
    assert belge.kod == "E63"
    metin = _metin(pdf)
    duz = _duz(metin)
    # Antet okulun (birlik satırı yok); başlık belgenin adı; altlık kodlu.
    assert belge.antet.unit_line == letterhead_unit(OKUL_ADI) and belge.antet.alt_birim == ""
    assert belge.bloklar[0] == evrak.Baslik(e63.BELGE_ADI)
    assert "HESAPTESLİMPUSULASI" in duz and "OABDefteri·E63·Sayfa1/1" in duz
    # Tanıtıcı, rol (sıra no'suz) ve açılış tarihi; ad-soyad yok.
    kunye = _tablo(belge, "Tanıtıcı")
    assert kunye.satirlar == (
        ("muhasip", "Muhasip", f"{timezone.localtime(hesap.opened_at):%d.%m.%Y}"),
    )
    # "Bu programda sizin işiniz" matristen (etkin hücreler, sırasıyla; bugünkü adlarıyla).
    isler = _tablo(belge, e63.IS_BASLIGI)
    assert [s[0] for s in isler.satirlar] == [
        e63.BUGUNKU_ISLER[satir].ad for satir in etkin_hucreler(AccountRole.MUHASIP)
    ]
    assert [s[0] for s in isler.satirlar] == [
        "Genel Bakış: son oturumun kontrolü (“Kontrol ettim”)",
        "Kendi parolanızı değiştirme, Kilitle, Çık",
    ]
    # İlk giriş: geçici parolayla giriş → parolayı yenileme (kilit ekranının metinleri).
    for parca in ("“muhasip”", "geçici parolayı “Parola”", "“Aç”", "“Parolayı yenile ve aç”"):
        assert _duz(parca) in duz, parca
    # Parola kuralları ve kilitleme (boşta kilit okulun süresiyle).
    assert _duz(e63.BOSTA_KILIT.format(dakika=15)) in duz
    assert _duz(e63.KILITLE) in duz and _duz(e63.ARTAN_BEKLEME) in duz
    assert _duz(e63.HATALI_DENEME_ASKISI) in duz
    assert _duz(ZARF_CUMLESI) in duz
    # İmza blokları elle; konum cümlesi ve RYUE unsurları yok; tek dipnot (kişisel veri) sonda.
    imza = next(b for b in belge.bloklar if isinstance(b, evrak.Imza))
    assert [(s.ad, s.gorev) for s in imza.sahipler] == [e63.TESLIM_EDEN, e63.TESLIM_ALAN]
    assert imza.tarih == ""
    assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar)
    for yok in ("Sayı:", "Konu:", "Sayın", "karar defteri", "TEFBİS"):
        assert yok not in metin
    assert [b for b in belge.bloklar if isinstance(b, evrak.Dipnot)] == [
        evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    ]
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    assert "Uydurma Muhasip" not in metin and "Uydurma Muhasip" not in evrak.kanonik_json(belge)


@pytest.mark.parametrize("kod", ["E63"])
def test_sayfa_butcesi(kod: str) -> None:
    """Gerçek uzunlukta uydurma veriyle sayfa bütçesi: her rol, en uzun tanıtıcı, uzun okul ve ilçe
    adı, iki haneli boşta kilit süresi. Program yöneticisinin pusulası en çok iki, öteki rollerinki bir
    sayfadır (kullanıcı kararı 04.11.2026): program yöneticisi en çok "iş" satırını taşır ve listesi
    sonraki fazların ekranlarıyla uzar."""
    assert kod == e63.KOD
    for rol in ROLLER:
        sinir = 2 if rol == AccountRole.YONETICI else 1
        belge = e63.pusula_belgesi(
            tanitici=EN_UZUN_TANITICI,
            rol=rol,
            acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
            okul_adi=UZUN_OKUL,
            ilce=UZUN_ILCE,
            bosta_dakika=30,
        )
        sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(belge))).pages)
        assert 1 <= sayfa <= sinir, (rol, sayfa)


@pytest.mark.parametrize("belge_adi", ["E63", "kurtarma_anahtari_belgesi"])
def test_tckn_hicbir_belgede_yok(belge_adi: str, yakalanan: list[evrak.Belge]) -> None:
    """Programın bugün ürettiği belgelerde 11 haneli kimlik deseni yok: kişi alanlarına sağlaması
    tutan uydurma T.C. kimlik numarası yazılır (hesap sahibinin ve okul müdürünün adı), çıktıda
    aranır. K9 ayarının kolları (`k9_kapali`, `k9_acik`) bağış kaydıyla F3'te eklenir."""
    tckn = _saglamali_uydurma_numara("100000001")
    _okul(principal_name=f"Uydurma Müdür {tckn}")
    if belge_adi == "E63":
        hesap = hesap_ac(AccountRole.MUHASIP, ad=f"{UYDURMA_AD} {tckn}")
        yanit = _bas(hesap.id)
        assert yanit.status_code == 200
        pdf = _pdf(yanit)
        (belge,) = yakalanan
        icerik = evrak.kanonik_json(belge)
        satir = AuditTrail.objects.filter(action=AuditAction.BASIM).get()
        icerik += str(satir.values) + str(satir.changed_fields) + satir.object_id
    else:
        pdf = recovery_key_document.render_recovery_key_pdf(TEST_KURTARMA_ANAHTARI)
        icerik = ""
    metin = _metin(pdf)
    for parca in (metin, _duz(metin), icerik):
        assert not _ONBIR_HANE.search(parca)
    assert tckn.encode() not in pdf


# ============================================================ ad-soyad, ret, iz


def test_e63_ad_soyad_basilmaz(yakalanan: list[evrak.Belge]) -> None:
    """Veri kaynağı yalnız giriş adı, rol ve açılış tarihidir (tasarım §9.6): hesap sahibinin de basan
    program yöneticisinin de adı ne modelde ne PDF'te (büyük harfli biçimi dahil)."""
    _okul()
    hesap = hesap_ac(AccountRole.SEKRETER, ad=f"{UYDURMA_AD} {UYDURMA_SOYAD}")
    pdf = _pdf(_bas(hesap.id))
    (belge,) = yakalanan
    metin, json_metni = _metin(pdf), evrak.kanonik_json(belge)
    for ad in (UYDURMA_AD, UYDURMA_SOYAD, TEST_HESAP_ADI):
        for bicim in (ad, tr_upper(ad), ad.casefold()):
            assert bicim not in metin and bicim not in json_metni, bicim
    # İçerik modelinin girdileri kişisizdir: ad-soyad parametresi yoktur.
    assert set(inspect.signature(e63.pusula_belgesi).parameters) == {
        "tanitici",
        "rol",
        "acilis",
        "okul_adi",
        "ilce",
        "bosta_dakika",
    }


@pytest.mark.parametrize("durum_", ["kendi", "kapali", "muhur", "satir_izi", "iz_boslugu"])
def test_e63_basilmaz(durum_: str) -> None:
    """Kendi hesabına, kapalı hesaba ve kaydı (mühür, satır izi) ya da izi (boşluk) tutmayan hesaba
    basılmaz: servis kapamanın sırası ve iletileriyle reddeder, `BASIM` satırı yazılmaz; mühür,
    satır izi ya da iz boşluğu reddinde `BUTUNLUK` satırı kalır (alan `seal`, `kayit_mac` ya da
    `iz_boslugu`; orkestratör maddesi F-1: mühür kolu da yazar, kapamadaki gibi). Satırın `pusula`
    eylemi aynı nedeni önceden söyler."""
    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    hedef = str(hesap.id)
    satir_nedeni: str
    butunluk: list[tuple[str, str, list[str]]] = []
    if durum_ == "kendi":
        hedef = TEST_HESAP_ID
        kod, ileti, satir_nedeni = 400, hesaplar._OWN_SLIP_MESSAGE, hesaplar._OWN_SLIP_MESSAGE
    elif durum_ == "kapali":
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        kod, ileti, satir_nedeni = 400, hesaplar._CLOSED_MESSAGE, hesaplar._CLOSED_MESSAGE
    elif durum_ == "muhur":
        ham_guncelle(hesap.id, status=AccountStatus.ACIK)
        kod, ileti, satir_nedeni = 409, hesaplar._SEAL_MESSAGE, hesaplar._ROW_SEAL_MESSAGE
        butunluk = [(AuditAction.BUTUNLUK, hedef, ["seal"])]
    elif durum_ == "satir_izi":
        geri_sarilmis(hesap)
        kod, ileti, satir_nedeni = 409, hesaplar._SEAL_MESSAGE, hesaplar._ROW_SEAL_MESSAGE
        butunluk = [(AuditAction.BUTUNLUK, hedef, [app_password.KAYIT_MAC_ALANI])]
    else:
        izde_bosluk_sonra_yoneticiyi_tazele()
        kod, ileti, satir_nedeni = 409, hesaplar._GAP_MESSAGE, hesaplar._ROW_GAP_MESSAGE
        butunluk = [(AuditAction.BUTUNLUK, hedef, [app_password.IZ_BOSLUGU_ALANI])]
    satir = next(s for s in APIClient().get(API).json()["hesaplar"] if s["id"] == hedef)
    assert satir["eylemler"]["pusula"] == {"yapilabilir": False, "neden": satir_nedeni}
    son = _son_seq()

    yanit = _bas(hedef)

    assert yanit.status_code == kod, yanit.content
    assert yanit["Content-Type"].startswith("application/json")
    assert yanit.json()["message"] == ileti
    yeni = AuditTrail.objects.filter(seq__gt=son).order_by("seq")
    assert not yeni.filter(action=AuditAction.BASIM).exists()
    assert list(yeni.values_list("action", "object_id", "changed_fields")) == butunluk
    if kod == 409:
        assert yanit.json()["code"] == "hesap_muhru_tutmadi"


def test_e63_satirda_basilabilir_ve_askidaki_hesaba_basilir() -> None:
    """Açık ve askıdaki (hatalı deneme askısı dosyada) hesabın `pusula` eylemi açıktır; askıdaki
    hesaba basılır (yalnız kapalı, kendi ve kaydı tutmayan hesap reddedilir)."""
    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    veri = app_password.read_state()
    assert veri is not None
    for bolum in veri["hesaplar"]:
        if bolum["id"] == str(hesap.id):
            bolum["askida"], bolum["hatali"] = True, 10
    app_password._write_state(veri)
    satir = next(s for s in APIClient().get(API).json()["hesaplar"] if s["id"] == str(hesap.id))
    assert satir["askida_nedeni"] == "HATALI_DENEME"
    assert satir["eylemler"]["pusula"] == {"yapilabilir": True, "neden": None}
    assert _bas(hesap.id).status_code == 200


def test_e63_izi_basim_satiridir_erisim_gunlugune_girmez() -> None:
    """Tek izi `BASIM` satırıdır: program yöneticisinin adına, model `okul.Account`, kimlik hesap;
    değerler yalnız kod ve PDF'in sha256'sı, içerik MAC'i yok. Hesabın satır izi ve kaydın bütünlüğü
    değişmez (pusula hesabı aklamaz, eski kaydını örtmez); zincir bütün; erişim günlüğüne girmez."""
    _okul()
    hesap = hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi")
    son, erisim = _son_seq(), AccessLog.objects.count()

    pdf = _pdf(_bas(hesap.id))

    (satir,) = AuditTrail.objects.filter(seq__gt=son)
    assert (satir.action, satir.actor, str(satir.account_id), satir.role) == (
        AuditAction.BASIM,
        "HESAP",
        TEST_HESAP_ID,
        "yonetici",
    )
    assert (satir.model, satir.object_id) == ("okul.Account", str(hesap.id))
    assert satir.changed_fields == []
    assert satir.values == {"kod": [None, "E63"], "sha256": [None, hashlib.sha256(pdf).hexdigest()]}
    assert satir.record_mac == ""
    assert AccessLog.objects.count() == erisim
    assert denetim_izi.zinciri_dogrula() == []
    assert denetim_izi.kaydi_dogrula(Account, hesap.id) is True
    hesap = Account.objects.get(pk=hesap.id)
    assert denetim_izi.hesap_izi_tutuyor(
        hesap.id, veri_anahtari=TEST_DEK, beklenen_muhur=hesap.seal
    )
    # İkinci basım ikinci satırdır (yeniden üretim; dosya yine saklanmaz).
    _bas(hesap.id)
    assert AuditTrail.objects.filter(seq__gt=son, action=AuditAction.BASIM).count() == 2


def test_denetim_izi_basim_bicimsiz_degeri_reddeder() -> None:
    """`BASIM` satırı yalnız evrak kodu (`E01`…`E79` biçimi) ve 64 haneli küçük onaltılık özet taşır;
    başka bir değer (ör. bir ad, biçimsiz özet) iz yazıcısında reddedilir (kaydın özeti, R1)."""
    son = _son_seq()
    for kod, ozet in (
        ("E63", "x" * 64),
        (UYDURMA_AD, "0" * 64),
        ("E63", "A" * 64),
        ("E63", "0" * 63),
        ("E630", "0" * 64),
    ):
        with transaction.atomic(), pytest.raises(denetim_izi.IzYazilamadi):
            denetim_izi.basim(model="okul.Account", object_id=TEST_HESAP_ID, kod=kod, sha256=ozet)
    assert _son_seq() == son


def test_e63_yaniti_pdf_no_store_ve_ek() -> None:
    """Yalnız PDF; bellekten, önbelleğe alınmadan, ek olarak. Dosya adı rol etiketini taşır,
    tanıtıcıyı ve adı taşımaz (orkestratör maddesi F-2); Türkçe harfli ad Content-Disposition'da
    RFC 5987 biçimiyle kodlanır (kurtarma anahtarı belgesinin kalıbı)."""
    _okul()
    hesap = hesap_ac(AccountRole.BASKAN, tanitici="uydurmaca", ad="Uydurmaca Başkanoğlu")
    yanit = _bas(hesap.id)
    assert yanit.status_code == 200
    assert yanit["Content-Type"] == "application/pdf"
    assert yanit["Cache-Control"] == "no-store"
    bugun = f"{timezone.localdate():%d.%m.%Y}"
    beklenen = f"Hesap-Teslim-Pusulası_Başkan_{bugun}.pdf"
    baslik = yanit["Content-Disposition"]
    assert baslik == f"attachment; filename*=utf-8''{quote(beklenen)}"
    assert unquote(baslik.split("''", 1)[1]) == beklenen
    for yok in ("uydurmaca", "Uydurmaca", "Başkanoğlu"):
        assert yok not in unquote(baslik)


@pytest.mark.parametrize(
    ("rol", "parca"),
    [
        (AccountRole.YONETICI, "Program-yöneticisi"),
        (AccountRole.BASKAN, "Başkan"),
        (AccountRole.BASKAN_YARDIMCISI, "Başkan-yardımcısı"),
        (AccountRole.MUHASIP, "Muhasip"),
        (AccountRole.SEKRETER, "Sekreter"),
        (AccountRole.DENETLEME_KURULU, "Denetleme-Kurulu"),
        (AccountRole.MUDUR, "Okul-müdürü"),
    ],
)
def test_e63_dosya_adi_rol_etiketini_tasir(rol: str, parca: str) -> None:
    """Orkestratör maddesi F-2: belge adı + rol etiketi (sıra no'suz, boşluk tire) + gün; dosya
    sisteminin yasakladığı karakter yok; ön yüzün `dosyaAdi` kalıbı (sözlük §3)."""
    ad = e63.dosya_adi(rol, date(2026, 11, 3))
    assert ad == f"Hesap-Teslim-Pusulası_{parca}_03.11.2026.pdf"
    assert not re.search(r'[\\/:*?"<>|\s]', ad)


def test_e63_dosya_adi_sira_no_ve_tanitici_tasimaz() -> None:
    """Aynı rolde birden çok hesap olsa da rol etiketi sıra no'suzdur (sıra no yalnız kilit
    ekranında): ikinci program yöneticisinin ve ikinci Denetleme Kurulu üyesinin pusulası rolün
    adını taşır; tanıtıcı (`yonetici-2`, `dk-2`) ve kilit ekranının sıra no'lu etiketi girmez."""
    _okul()
    hesap_ac(AccountRole.DENETLEME_KURULU, tanitici="dk-1", ad="Uydurma Denetçi Bir")
    for rol, tanitici in (
        (AccountRole.YONETICI, "yonetici-2"),
        (AccountRole.DENETLEME_KURULU, "dk-2"),
    ):
        hesap = hesap_ac(rol, tanitici=tanitici, ad="Uydurma Hesap Sahibi")
        yanit = _bas(hesap.id)
        assert yanit.status_code == 200
        baslik = unquote(yanit["Content-Disposition"])
        assert baslik.endswith(e63.dosya_adi(rol))
        assert tanitici not in baslik and "-2_" not in baslik and "Uydurma" not in baslik


def test_e63_iz_yazilamazsa_pdf_verilmez() -> None:
    """İz yazılamazsa PDF verilmez (tasarım §4.6.2: iz yazılamazsa yazma yapılmaz): zincir başının
    `mac`'i program dışından BLOB'a çevrilmiştir (hesapların satır izi bundan etkilenmez); yanıt 409
    `iz_yazilamadi`, sabit ileti, gövde JSON'dur."""
    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    (bas,) = iz_dolgusu(1)
    iz_tetikleyicisiz("UPDATE okul_audittrail SET mac = CAST(mac AS BLOB) WHERE seq = %s", [bas])

    yanit = _bas(hesap.id)

    assert yanit.status_code == 409, getattr(yanit, "content", b"")[:300]
    assert yanit.json() == {
        "code": IZ_YAZILAMADI_KODU,
        "message": IZ_YAZILAMADI_MESAJI,
        "fields": {},
    }
    assert not AuditTrail.objects.filter(action=AuditAction.BASIM).exists()


def test_e63_cizim_surerken_kapatilan_hesaba_basilmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Basım izi hesabın kapalı olmadığını AYNI işlemde yeniden sorar: çizim sürerken kapatılan
    hesaba pusula verilmez, `BASIM` satırı yazılmaz."""
    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    asil = evrak.pdf_ciz

    def kapatarak_ciz(belge: evrak.Belge, sablonlar: Path | None = None) -> bytes:
        hesaplar.close_account(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
        return asil(belge, sablonlar)

    monkeypatch.setattr(evrak, "pdf_ciz", kapatarak_ciz)

    yanit = _bas(hesap.id)

    assert yanit.status_code == 400
    assert yanit.json()["message"] == hesaplar._CLOSED_MESSAGE
    assert not AuditTrail.objects.filter(action=AuditAction.BASIM).exists()


def test_e63_yalniz_program_yoneticisi() -> None:
    """Rol kapısının ardından servis de yetki kapısına sorar (derin savunma): açık, mühürlü ve izli
    bir muhasip hesabı (yazar bağlamıyla aynı) başka bir hesabın pusulasını isterse `RolYetkisiz`
    alır; hiçbir şey çizilmez ve yazılmaz. Uçta öteki roller 403 alır
    (`test_kullanicilar_uclari.test_kullanicilar_yalniz_program_yoneticisine_acik`)."""
    muhasip = muhurle(
        hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip"),
        status=AccountStatus.ACIK,
        password_changed_at=timezone.now(),
    )
    hedef = hesap_ac(AccountRole.SEKRETER, ad="Uydurma Sekreter")
    son = _son_seq()
    with yazar_olarak(Yazar(hesap_id=str(muhasip.id), rol="muhasip")), pytest.raises(RolYetkisiz):
        hesaplar.teslim_pusulasi(by_hesap_id=muhasip.id, hesap_id=hedef.id)
    assert _son_seq() == son


# ============================================================ içerik kuralları


def test_e63_kilitleme_rolune_gore() -> None:
    """Program yöneticisi hesabı askıya alınmaz (`app_password` "HATALI DENEME"): onun pusulası askıyı
    anmaz; öteki rollerde 10. yanlış denemenin askısı ve kaldıranı yazılır. Sayılar program sabitleriyle
    aynıdır (parola en az 8, 180 gün, 10. deneme)."""
    for rol in ROLLER:
        belge = e63.pusula_belgesi(
            tanitici="hesap",
            rol=rol,
            acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
            okul_adi=OKUL_ADI,
            ilce=None,
            bosta_dakika=10,
        )
        akis = " ".join(evrak.metin_akisi(belge))
        yonetici = rol == AccountRole.YONETICI
        assert (e63.YONETICI_ASKI_YOK in akis) is yonetici, rol
        assert (e63.HATALI_DENEME_ASKISI in akis) is not yonetici, rol
    assert f"{app_password.SUSPEND_AFTER_FAILURES}. yanlış" in e63.HATALI_DENEME_ASKISI
    assert f"en az {hesap_kurallari.MIN_PASSWORD_LENGTH} karakter" in e63.PAROLA_KURALLARI[0]
    assert f"{hesap_kurallari.PASSWORD_MAX_AGE_DAYS} gün" in e63.PAROLA_KURALLARI[-1]


def _yazma_uclari(satir: Satir, rol: str) -> set[str]:
    """Satırın, rolün bugün yazabildiği uçları (`rol_izinleri.KURALLAR`'ın yazma kuralları)."""
    return {
        kural.uc
        for kural in rol_izinleri.KURALLAR
        if kural.satir is satir
        and kural.tur is rol_izinleri.KuralTuru.YAZMA
        and rol in rol_izinleri.kural_rolleri(kural)
    }


def test_e63_bugunku_isler_yalniz_etkin_satirlardadir() -> None:
    """Orkestratör maddesi F-4: pusula yalnız bugün programda yapılabilen işleri yazar. Bugünkü
    işlerin anahtarları TAM OLARAK bir rolün etkin satırlarıdır (`etkin_hucreler`, tek yüklem):
    etkin satırın adı eksik olamaz, bekleyen satıra (sonraki fazın işine) ad yazılamaz. Adlarda iç
    kod ve kullanılmaz kısaltma (YK, DK, M1…) yoktur; her rolün işleri `etkin_hucreler`
    sırasıyladır."""
    etkin = {satir for rol in ROLLER for satir in etkin_hucreler(rol)}
    assert set(e63.BUGUNKU_ISLER) == etkin
    for is_ in e63.BUGUNKU_ISLER.values():
        assert is_.parcalar and all(parca.ad.strip() for parca in is_.parcalar), is_
        assert not re.search(r"\b(YK|DK|DEK|M\d+|E\d{2})\b", is_.ad), is_.ad
    for rol in ROLLER:
        assert e63.isler(rol) == tuple(e63.BUGUNKU_ISLER[s].ad for s in etkin_hucreler(rol))


def test_e63_is_parcalari_var_olan_uclara_karsilik_gelir() -> None:
    """Orkestratör maddesi F-4: her işin her parçası, pusulası basılan rolün o satırda bugün
    yazabildiği bir uca bağlıdır (uç yoksa ad yazılamaz: "hesap geçişi", "birlik döneminin
    açılması" bugün yazılamaz). Ters yönde, etkin satırın her yazma ucu bir parçada adlanır ya da
    `ADSIZ_UCLAR`'da gerekçesiyle durur: bir faz yeni bir uç getirince ad da büyür."""
    adsiz_kullanilan: set[str] = set()
    for rol in ROLLER:
        for satir in etkin_hucreler(rol):
            uclar = _yazma_uclari(satir, rol)
            adli: set[str] = set()
            for parca in e63.BUGUNKU_ISLER[satir].parcalar:
                assert parca.uclar, (rol, satir, parca.ad)
                assert parca.uclar <= uclar, (rol, satir, parca.ad, parca.uclar - uclar)
                adli |= parca.uclar
            kalan = uclar - adli
            assert kalan <= set(e63.ADSIZ_UCLAR), (rol, satir, kalan - set(e63.ADSIZ_UCLAR))
            adsiz_kullanilan |= kalan
    # Adsız listesi bayatlamaz: her biri gerçekten adsız kalan bir yazma ucudur, gerekçesi vardır.
    assert adsiz_kullanilan == set(e63.ADSIZ_UCLAR)
    assert all(gerekce.strip() for gerekce in e63.ADSIZ_UCLAR.values())


def test_e63_guvenlik_dosyasi_sifirlamasi_is_diye_yazilmaz() -> None:
    """Orkestratör maddesi F-4, "adın gerçekten var olan bir uç/ekrana karşılık gelmesi" (bağımsız
    denetim bulgusu): matrisin Güvenlik satırındaki "Güvenlik dosyasını sıfırla ve kuruluma dön"
    ucu yalnız güvenlik dosyası kayıp ekranındadır ve yalnız hiç hesap ve şifreli kayıt yokken
    açıktır. Pusulası basılabilen bir hesap varken (açık oturumda) her zaman 409
    `sifirlama_uygun_degil` döner: hesap sahibinin bugün yapabildiği bir iş değildir, hiçbir parçada
    adlanmaz, gerekçesiyle adsızdır."""
    yanit = APIClient().post("/api/v1/security/state/reset/", {}, format="json")

    assert yanit.status_code == 409, yanit.content
    assert yanit.json()["code"] == "sifirlama_uygun_degil"
    assert "security-state-reset" in e63.ADSIZ_UCLAR
    assert not any(
        "security-state-reset" in parca.uclar
        for is_ in e63.BUGUNKU_ISLER.values()
        for parca in is_.parcalar
    )


def test_e63_her_rolun_pusulasi_bugunku_islerdir() -> None:
    """Orkestratör maddesi F-4, rol rol: program yöneticisi sekiz iş; yönetim kurulu rolleri
    Genel Bakış'ta son oturumun kontrolü ve kendi parolası; Denetleme Kurulu geri yükleme kartının
    "Gördüm"ü ve kendi parolası; okul müdürü yalnız kendi parolası (müdür yazıları F2/F4'tedir).
    Sonraki fazların işleri hiçbir pusulada yoktur."""
    kendi = "Kendi parolanızı değiştirme, Kilitle, Çık"
    son_oturum = "Genel Bakış: son oturumun kontrolü (“Kontrol ettim”)"
    beklenen = {
        AccountRole.YONETICI: (
            "Okul bilgileri, ders yılı ve dönemler, kapalı günler, şubeler",
            "Kişiler: öğretmen ve diğer personel kaydı, e-Okul aktarımı, ayrılış havuzu",
            son_oturum,
            "Kullanıcılar: hesap açma, kapama, askıdan çıkarma, parola sıfırlama, hesap teslim "
            "pusulası",
            "Güvenlik: kurtarma anahtarı, şifreli yedek, yedekten geri yükleme, Genel Bakış'ta "
            "güvenlik dosyasında kalan eski parola kayıtlarının silinmesi",
            "Ayarlar: boşta kilit süresi",
            "Güncelleme denetimi",
            kendi,
        ),
        AccountRole.BASKAN: (son_oturum, kendi),
        AccountRole.BASKAN_YARDIMCISI: (son_oturum, kendi),
        AccountRole.MUHASIP: (son_oturum, kendi),
        AccountRole.SEKRETER: (son_oturum, kendi),
        AccountRole.DENETLEME_KURULU: (
            "Genel Bakış: yedekten geri yükleme kartını görüldü olarak işaretleme (“Gördüm”)",
            kendi,
        ),
        AccountRole.MUDUR: (kendi,),
    }
    assert set(beklenen) == set(ROLLER)
    gelecek = re.compile(
        r"(?i)birlik dönemi|hesap geçişi|anahtarının yenilenmesi|küçük alım|kural sürümü|"
        r"bağışçı|takvim|uyum kaydı|genel kurul|karar|gelir-gider|harcama|bütçe|kantin|servis|"
        r"organ|temsilci|denetim planı|müdür yazısı|devir-teslim|öğrenci"
    )
    for rol, isler in beklenen.items():
        assert e63.isler(rol) == isler, rol
        for ad in isler:
            assert not gelecek.search(ad), (rol, ad)


def test_e63_yazi_tipi_evrak_hattinin() -> None:
    """Yazı tipi bugünkü evrak hattınınki (DejaVu Sans; plan F1b-2 "Yazı tipi")."""
    belge = e63.pusula_belgesi(
        tanitici="muhasip",
        rol=AccountRole.MUHASIP,
        acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
        okul_adi=OKUL_ADI,
        ilce=None,
        bosta_dakika=10,
    )
    okuyucu = PdfReader(io.BytesIO(evrak.pdf_ciz(belge)))
    yazi_tipleri: set[str] = set()
    for sayfa in okuyucu.pages:
        kaynaklar: Any = sayfa["/Resources"]
        for tip in kaynaklar["/Font"].values():
            yazi_tipleri.add(str(tip.get_object()["/BaseFont"]).split("+", 1)[-1])
    assert yazi_tipleri and all(ad.startswith("DejaVu") for ad in yazi_tipleri), yazi_tipleri


# ============================================================ atıflar ve sözlük


def _depo_dosyasi(goreli: str) -> str:
    """Depo kökündeki dosya (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / goreli
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail(f"{goreli} bulunamadı.")


def _bsg_maddesi(no: int) -> str:
    korpus = _depo_dosyasi("docs/mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md")
    bas = korpus.index(f'<a id="madde-{no}"></a>')
    son = korpus.find('<a id="madde-', bas + 1)
    return korpus[bas : son if son != -1 else None]


def _hukum(madde: int, fikra: int, bent: str | None) -> str:
    """Korpustaki fıkranın (ve bendin) metni; yoksa boş."""
    metin = _bsg_maddesi(madde)
    bas = metin.find(f"({fikra})")
    if bas == -1:
        return ""
    son = metin.find(f"({fikra + 1})", bas)
    fikra_metni = metin[bas : son if son != -1 else None]
    if bent is None:
        return fikra_metni
    eslesme = re.search(rf"(?m)^{re.escape(bent)}\) (.+)$", fikra_metni)
    return "" if eslesme is None else eslesme.group(1)


#: Pusuladaki her BSG Yön. atfı ve korpusta o hükmün söylediği (altın kural 1; plan F1b-2 "E63").
BEKLENEN_ATIFLAR: dict[tuple[int, int, str | None], str] = {
    (9, 2, "a"): "en az 8",
    (9, 2, "b"): "küçük harf, büyük harf, rakam ve simgelerin",
    (9, 2, "ç"): "en geç altı ayda bir değiştirilir",
    (9, 2, "c"): "hatalı girilmesi sonucu, kullanıcı hesabı",
    (9, 2, "e"): "herhangi bir kişi ile paylaşılmaz",
    (10, 1, None): "herkes tarafından görülebilecek yerlere yazılmaz",
    (10, 2, None): "otomatik olarak şifre ile oturum açmasını",
    (7, 3, None): "hatalı giren kullanıcının",
    (7, 4, None): "oturumunu kilitler",
}


def _pusulanin_atiflari() -> set[tuple[int, int, str | None]]:
    metinler = [
        *e63.PAROLA_KURALLARI,
        e63.BOSTA_KILIT,
        e63.KILITLE,
        e63.ARTAN_BEKLEME,
        e63.HATALI_DENEME_ASKISI,
        e63.YONETICI_ASKI_YOK,
        e63.KAPALI_ZARF,
        *e63.ILK_GIRIS_ADIMLARI,
    ]
    atiflar: set[tuple[int, int, str | None]] = set()
    for metin in metinler:
        # İlk atıf kısaltmayı açar: "… Yönergesinin (BSG Yön.) md. 9/2-a ve 9/2-b …".
        for grup in re.findall(r"BSG Yön\.\)? md\. ([0-9/a-zç, -]+)", metin):
            for madde, fikra, bent in re.findall(r"(\d+)/(\d+)(?:-([a-zç]))?", grup):
                atiflar.add((int(madde), int(fikra), bent or None))
    return atiflar


def test_e63_atiflari_korpusla_dogrulanir() -> None:
    """Pusuladaki her atıf (madde, fıkra, bent) kanonik metinde vardır ve o hüküm pusulanın dayandığı
    şeyi söyler; atıf kümesi planın listesidir (md. 9/2-a, b, ç, c, e; 10/1, 10/2; 7/3, 7/4)."""
    assert _pusulanin_atiflari() == set(BEKLENEN_ATIFLAR)
    for (madde, fikra, bent), soz in BEKLENEN_ATIFLAR.items():
        hukum = _hukum(madde, fikra, bent)
        assert soz in hukum, (madde, fikra, bent, hukum[:120])
    # Kıyasen anılan hükümler (Bakanlık hesapları, personelin bilgisayarı, Başkanlık politikası).
    for metin in (e63.BOSTA_KILIT, e63.KILITLE, e63.HATALI_DENEME_ASKISI):
        assert metin.endswith("programa kıyasen).")


def test_e63_kisaltma_ilk_geciste_acilir() -> None:
    """Sözlük §3 "Kısaltma" (RYUE md. 16/11; bağımsız denetim bulgusu): "BSG Yön." pusulada İLK
    geçtiği yerde yönergenin korpustaki açık adıyla, ardından parantez içinde yazılır; açılımı
    dipnota bırakılmaz. Her rolde (işler tablosu rolden role değişir)."""
    korpus = _depo_dosyasi("docs/mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md")
    (ad,) = re.findall(r'(?m)^mevzuat-adi: "(.+)"$', korpus)
    kok = ad.removesuffix("i")  # "… Yönergesi" ya da ekli "… Yönergesinin"
    for rol in ROLLER:
        belge = e63.pusula_belgesi(
            tanitici="hesap",
            rol=rol,
            acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
            okul_adi=OKUL_ADI,
            ilce=None,
            bosta_dakika=10,
        )
        akis = " ".join(evrak.metin_akisi(belge))
        ilk = akis.index("BSG Yön.")
        acilim = re.search(rf"{re.escape(kok)}\w* \(BSG Yön\.\)", akis)
        assert acilim is not None and acilim.start() < ilk < acilim.end(), (rol, akis[:ilk])
        assert not [b for b in belge.bloklar if isinstance(b, evrak.Dipnot) and "BSG" in b.metin]


def _e63_metinleri() -> Iterator[str]:
    yield tr_upper(e63.BELGE_ADI)
    yield from e63.KUNYE_BASLIKLARI
    yield e63.IS_BASLIGI
    yield from (is_.ad for is_ in e63.BUGUNKU_ISLER.values())
    yield e63.ILK_GIRIS_BASLIGI
    yield from (adim.format(tanitici="<tanıtıcı>") for adim in e63.ILK_GIRIS_ADIMLARI)
    yield e63.PAROLA_BASLIGI
    yield from e63.PAROLA_KURALLARI
    yield e63.KILIT_BASLIGI
    yield e63.BOSTA_KILIT.format(dakika="N")
    yield from (e63.KILITLE, e63.ARTAN_BEKLEME, e63.HATALI_DENEME_ASKISI, e63.YONETICI_ASKI_YOK)
    yield e63.KAPALI_ZARF
    yield from (*e63.TESLIM_EDEN, *e63.TESLIM_ALAN)
    yield evrak.KISISEL_VERI_DIPNOTU
    yield hesaplar._OWN_SLIP_MESSAGE


def test_e63_metinleri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Hesap teslim pusulası (F1b)")."""
    sozluk = _depo_dosyasi("docs/sozluk.md")
    eksik = [metin for metin in _e63_metinleri() if f'**"{metin}"**' not in sozluk]
    assert eksik == []
    # İndirme adının kalıbı ve örnekleri (orkestratör maddesi F-2; §1 ve §2 "Belge adları").
    assert sozluk.count("`Hesap-Teslim-Pusulası_<rol etiketi>_gg.aa.yyyy.pdf`") >= 2
    for rol in (AccountRole.MUHASIP, AccountRole.YONETICI):
        ornek = hesap_teslim_pusulasi.dosya_adi(rol, date(2026, 11, 3))
        assert f"`{ornek}`" in sozluk, ornek
    assert "Hesap-Teslim-Pusulası_gg.aa.yyyy.pdf" not in sozluk
