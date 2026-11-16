"""Evrak kuralları — hesap teslim pusulası (E63; plan F1b-2) ve F1c'nin üç evrakı (E01, E02, E03;
plan F1c 10. adım).

Tasarım §10.5'in `ev::` testlerinden bugünkü pay; dosya F1c'nin 1. adımında §10.1 dizinine taşındı (plan).
F1c kümesi (tasarım §10.6 "Üç belge docx + PDF"): `test_katalog_kabul[E01-E03]`,
`test_docx_pdf_icerik_esdegerligi[E01-E03]` (Türkçe büyük harf dahil), `test_sayfa_butcesi[E01-E03]`,
`test_konum_kdt[E01, E03]` (E02'de yok), `test_mudur_bloklari_yalniz_93_tablosunda[E01-E03]`,
`test_imza_ad_soyad_bicimi`, `test_tckn_hicbir_belgede_yok[E01-E03]`,
`test_yeniden_basim_icerik_ozeti_ayni`, `test_ilk_uc_evrak_pilot_esdegerligi` ve
`test_karar_taslagi_varsayilan`. E63'ün testleri:

* `test_e63_pusulada_parola_alani_yok` — içerik modelinde ve PDF'te parola alanı, parola değeri ya
  da parola için boş satır yok; giriş adı, rol, iş özeti, BSG Yön. md. 9/2 kuralları, kilitleme ve
  "kapalı zarf" cümlesi var; dosyası saklanmaz.
* `test_katalog_kabul[E63]` — tasarım §9.6 "Kabul örneği" sütunu.
* `test_sayfa_butcesi[E63]` — en uzun uydurma veriyle (alanların üst sınırında tanıtıcı, okul adı,
  ilçe ve veri sorumlusu; en uzun boşta kilit süresi; her rol): her rolün pusulası en çok iki sayfa
  (kullanıcı kararı 11.11.2026: RYUE md. 7/1 gereği dipnot ve aydınlatma metni 9 punto olunca
  04.11.2026'nın "öteki rollerde bir sayfa" sınırı gevşedi; program yöneticisininki zaten ikiydi).
* `test_e63_punto_alt_siniri` — aynı veriyle, her rolde PDF'teki yazı boyutları geri okunur: yazı
  alanında 9 puntodan küçük metin yok (aydınlatma metni ve kişisel veri dipnotu 9), altlık 12.
* `test_tckn_hicbir_belgede_yok` — programın bugün ürettiği belgelerde 11 haneli kimlik deseni yok
  (K9 ayarının kolları bağış kaydıyla F3'te gelir).
* `test_katalogdaki_her_kodun_testi_var` — tasarım §9.5 ile §9.6 aynı 79 kodu taşır; fazı gelen her
  kodun kabul testi ve ad satırı vardır (faz süzmesi `faz_ortak`; plan F1b-6 kararları).

Ayrıca: ad-soyad basılmaz (hesap sahibinin de basanın da); kendi hesabına, kapalı hesaba ve kaydı ya
da izi tutmayan hesaba basılmaz (satırın `pusula` eylemi aynı nedeni söyler; mühür reddi de `BUTUNLUK`
satırı yazar, orkestratör maddesi F-1); üretimi `GeneratedDocument` kaydıdır (içerik JSON'u, dosyası
yok; yeniden üretim yeni sürüm, yeniden çizim aynı özet; plan F1c 9. adım), dosyanın izi `BASIM`
satırıdır (kod ve PDF'in sha256'sı), erişim günlüğüne girmez, hesabın satır izini değiştirmez; yazı
tipi evrak hattının Liberation Serif'idir; yanıt `no-store`, yalnız PDF; dosya adı rol
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
import zipfile
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import pytest
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from pypdf import PdfReader
from rest_framework.test import APIClient

from apps.oab import selectors
from apps.oab.kurallar import kural, kural_kaydi
from apps.oab.models import (
    AgendaItem,
    BoardDecision,
    DecisionKind,
    DecisionStatus,
    DocumentStatus,
    GeneralAssembly,
    GeneratedDocument,
    KararDurumuGecersiz,
    MeetingKind,
    MembershipStatus,
    OabPerson,
    OabTerm,
    OrganMembership,
    Representation,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import genel_kurul as gk
from apps.oab.services import genel_kurul_evraki as gke
from apps.oab.services import gorev_evraki, kisiler, kurullar, temsilciler, uyelikler
from apps.oab.tests import genel_kurul_evraki_ortak as gke_ortak
from apps.oab.tests import genel_kurul_ortak as gko
from apps.oab.tests import uyelik_ortak as o
from apps.oab.tests.kurallar import faz_ortak
from apps.oab.tests.kurallar import gorev_evraki_ortak as ge_ortak
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import (
    DATA_CONTROLLER_TEXT_MAX,
    IDLE_LOCK_MINUTES_MAX,
    AccessLog,
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditTrail,
    ParentRoster,
    Personnel,
    SchoolConfig,
)
from apps.okul.oturum import Yazar, rol_etiketi, yazar_olarak
from apps.okul.rol_izinleri import ROLLER, Satir, etkin_hucreler
from apps.okul.services import (
    app_password,
    dosya_deposu,
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
from shared import docx as cizici_
from shared import evrak
from shared.exceptions import IZ_YAZILAMADI_KODU, IZ_YAZILAMADI_MESAJI, RolYetkisiz
from shared.letterhead import letterhead_unit
from shared.tests.test_evrak_cizicileri import _ayristir
from shared.text import tr_upper

pytestmark = pytest.mark.django_db

API = "/api/v1/accounts/"
#: Uydurma geçici parola (politikaya uyar; aranacak belirgin dizgi).
GIZLI_GECICI = "Zarf-Icindeki-Gecici-9!"
#: Uydurma hesap sahibi (aranacak belirgin ad ve soyad).
UYDURMA_AD = "Pelinsu"
UYDURMA_SOYAD = "Uydurmakaya"
OKUL_ADI = "Örnek Ortaokulu"
EN_UZUN_TANITICI = "a" * hesap_kurallari.MAX_LOGIN_NAME_LENGTH


def _alan_ust_siniri(ornek: str, alan: str) -> str:
    """Okul kartı alanının üst sınırında, sözcüklü uydurma metin (tek parça metin PDF'te bölünmez,
    tek satır kalır ve sınamaz)."""
    sinir = getattr(SchoolConfig._meta.get_field(alan), "max_length", None)
    assert isinstance(sinir, int)
    return ((ornek + " ") * (sinir // len(ornek) + 1))[:sinir].rstrip().ljust(sinir, "a")


#: En uzun uydurma künye (sayfa bütçesi ve punto alt sınırı): alanların üst sınırında.
EN_UZUN_OKUL = _alan_ust_siniri(
    "Örnek Şehit Öğretmen Ayşe Örnekoğlu Mesleki ve Teknik Anadolu Lisesi", "school_name"
)
EN_UZUN_ILCE = _alan_ust_siniri("Örnekşehirköyübeldesi", "district")
EN_UZUN_VERI_SORUMLUSU = _alan_ust_siniri("Örnek Anadolu Lisesi Müdürlüğü", "data_controller_text")
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


#: `test_katalog_kabul`'un parametreleri; `test_katalogdaki_her_kodun_testi_var` kataloğa karşı sınar.
KATALOG_KABUL_KODLARI = (
    "E01",
    "E02",
    "E03",
    "E05",
    "E06",
    "E07",
    "E08",
    "E09",
    "E10",
    "E11",
    "E12",
    "E13",
    "E14",
    "E63",
    "E64",
)


@pytest.mark.parametrize("kod", KATALOG_KABUL_KODLARI)
def test_katalog_kabul(kod: str, yakalanan: list[evrak.Belge]) -> None:
    """Tasarım §9.6 "Kabul örneği" sütunu, kod başına (E01-E03: F1c 10. adım; E63: F1b; E05-E08 ve
    E64: F2 9. adım; E09-E14: F2 10. adım)."""
    if kod == e63.KOD:
        _kabul_e63(yakalanan)
    elif kod in GENEL_KURUL_EVRAKI_KABULLERI:
        GENEL_KURUL_EVRAKI_KABULLERI[kod]()
    else:
        GOREV_EVRAKI_KABULLERI[kod]()


def _kabul_e63(yakalanan: list[evrak.Belge]) -> None:
    """Tasarım §9.6 E63 "Kabul örneği": tanıtıcı, rol ve "bu programda sizin işiniz" matristen; ilk
    giriş adımları (geçici parolayla giriş → parolayı değiştirme); parola kuralları (BSG 9/2-a, b,
    ç); kilitleme (boşta kilit, "Kilitle", yanlış denemede artan bekleme); parola alanı yok; kapalı
    zarf cümlesi (9/2-e, 10/1); kişisel veri dipnotu; dosya saklanmaz. Plan: yalnız PDF, antet
    okulun, imza blokları elle, RYUE unsurları ve konum cümlesi yok."""
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
        e63.BUGUNKU_ISLER[satir].rol_adi(AccountRole.MUHASIP)
        for satir in etkin_hucreler(AccountRole.MUHASIP)
        if satir not in e63.EKRANSIZ_SATIRLAR
    ]
    assert [s[0] for s in isler.satirlar] == [
        "Kişiler, Organlar, Temsilciler: birlik kişileri, üyelik ve temsilci kaydı",
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
    # İmza blokları elle; konum cümlesi ve RYUE unsurları yok; kişisel veri dipnotu sonda.
    imza = next(b for b in belge.bloklar if isinstance(b, evrak.Imza))
    assert [(s.ad, s.gorev) for s in imza.sahipler] == [e63.TESLIM_EDEN, e63.TESLIM_ALAN]
    assert imza.tarih == ""
    assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar)
    for yok in ("Sayı:", "Konu:", "Sayın", "karar defteri", "TEFBİS"):
        assert yok not in metin
    dipnotlar = [b.metin for b in belge.bloklar if isinstance(b, evrak.Dipnot)]
    assert dipnotlar[0] == e63.AYDINLATMA_BASLIGI
    assert dipnotlar.count(evrak.KISISEL_VERI_DIPNOTU) == 1
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    assert "Uydurma Muhasip" not in metin and "Uydurma Muhasip" not in evrak.kanonik_json(belge)


#: Pusulanın en çok sayfası, her rolde (kullanıcı kararı 11.11.2026; program yöneticisininki
#: 04.11.2026'dan beri 2).
E63_SAYFA_SINIRI = 2


def _en_uzun_pusula(rol: str) -> evrak.Belge:
    """Rolün pusulası, en uzun uydurma veriyle: alanların üst sınırında tanıtıcı, okul adı, ilçe ve
    veri sorumlusu; en uzun boşta kilit süresi."""
    assert len(EN_UZUN_VERI_SORUMLUSU) == DATA_CONTROLLER_TEXT_MAX
    return e63.pusula_belgesi(
        tanitici=EN_UZUN_TANITICI,
        rol=rol,
        acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
        okul_adi=EN_UZUN_OKUL,
        ilce=EN_UZUN_ILCE,
        bosta_dakika=IDLE_LOCK_MINUTES_MAX,
        veri_sorumlusu=EN_UZUN_VERI_SORUMLUSU,
    )


@pytest.mark.parametrize("kod", KATALOG_KABUL_KODLARI)
def test_sayfa_butcesi(kod: str) -> None:
    """E63: en uzun uydurma veriyle sayfa bütçesi (`_en_uzun_pusula`): her rolün pusulası en çok iki
    sayfadır. Kullanıcı kararı 11.11.2026: RYUE md. 7/1 gereği yazı alanında 9 puntodan küçük metin
    olmaz (dipnot ve aydınlatma metni 9); yönetim kurulu ve öteki rollerin 04.11.2026'daki bir sayfa
    sınırı gevşedi, aydınlatma metni gerekirse ikinci yaprağa geçer. Program yöneticisi en çok "iş"
    satırını taşır ve listesi sonraki fazların ekranlarıyla uzar; sınırı zaten ikiydi.

    E01-E03 (F1c 10. adım): gerçek uzunlukta uydurma veriyle (`gorev_evraki_ortak`, `uzun=True`:
    uzun ad ve soyadlar, okul adı ve ilçe alanlarının üst sınırında; tam kadro, bütün temsilci
    satırları) `GOREV_EVRAKI_SAYFA_SINIRI`.

    E05-E14, E64 (F2 9. ve 10. adım): `_gk_sayfa_butcesi` (gerçek uzunlukta uydurma veri, kalabalık
    sınıflar; `GENEL_KURUL_EVRAKI_SAYFA_SINIRI`, bölümlü belgede bölüm başına `BOLUM_SAYFA_SINIRI`)."""
    if kod in gke.KODLAR:
        _gk_sayfa_butcesi(kod)
        return
    if kod != e63.KOD:
        kurulum = ge_ortak.tam_kurulum(uzun=True)
        belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
        sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(belge))).pages)
        assert 1 <= sayfa <= GOREV_EVRAKI_SAYFA_SINIRI[kod], (kod, sayfa)
        return
    for rol in ROLLER:
        sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(_en_uzun_pusula(rol)))).pages)
        assert 1 <= sayfa <= E63_SAYFA_SINIRI, (rol, sayfa)


def test_e63_punto_alt_siniri() -> None:
    """En uzun uydurma veriyle her rolün pusulasında PDF'teki yazı boyutları geri okunur (RYUE md.
    7/1; kullanıcı kararı 11.11.2026): yazı alanında 9 puntodan küçük metin yoktur; aydınlatma
    metninin başlığı ve kişisel veri dipnotu 9 punto, altlık 12 punto (md. 7/1 esası; md. 27)."""
    from shared import docx as cizici
    from shared.tests.test_evrak import pdf_yazi_boyutlari

    for rol in ROLLER:
        parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(_en_uzun_pusula(rol)))
        kucukler = [(m, b) for _s, m, b in parcalar if b < cizici.EN_KUCUK_PUNTO]
        assert parcalar and kucukler == [], (rol, kucukler)
        boyutlar = {m: b for _s, m, b in parcalar}
        assert boyutlar[e63.AYDINLATMA_BASLIGI] == cizici.DIPNOT_PUNTO, rol
        assert boyutlar[evrak.KISISEL_VERI_DIPNOTU] == cizici.DIPNOT_PUNTO, rol
        altlik = {b for _s, m, b in parcalar if m.startswith("OAB Defteri ·")}
        assert altlik == {float(cizici.ALTLIK_PUNTO)}, (rol, altlik)


@pytest.mark.parametrize(
    ("kart", "beklenen"),
    [
        (
            "Örnek Ortaokulu Müdürlüğü, Örnek Mah. No: 1",
            "Örnek Ortaokulu Müdürlüğü, Örnek Mah. No: 1",
        ),
        ("", e63.AYDINLATMA_VERI_SORUMLUSU_YERI),
        ("   ", e63.AYDINLATMA_VERI_SORUMLUSU_YERI),
    ],
)
def test_e63_aydinlatma_bolumu(kart: str, beklenen: str, yakalanan: list[evrak.Belge]) -> None:
    """Program kullanıcısının aydınlatma metni (tasarım §3.4; plan "F1b-6 uygulama kararları"):
    imza bloklarından hemen sonra dipnot olarak, onaylı sırayla; veri sorumlusu okul kartındandır,
    boşsa yerini söyler; ekran notu etiketsiz son satırdır; pusula kişisiz kalır."""
    _okul(data_controller_text=kart)
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")

    pdf = _pdf(_bas(hesap.id))

    (belge,) = yakalanan
    bloklar = list(belge.bloklar)
    bas = bloklar.index(evrak.Dipnot(e63.AYDINLATMA_BASLIGI))
    beklenen_metinler = [
        e63.AYDINLATMA_BASLIGI,
        f"Veri sorumlusu: {beklenen}",
        *e63.AYDINLATMA_SATIRLARI,
        e63.AYDINLATMA_NOTU,
    ]
    son = bas + len(beklenen_metinler)
    assert bloklar[bas:son] == [evrak.Dipnot(metin) for metin in beklenen_metinler]
    assert isinstance(bloklar[bas - 1], evrak.Imza)
    assert bloklar[son:] == [evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)]
    metin = _metin(pdf)
    duz = _duz(metin)
    for parca in beklenen_metinler:
        assert _duz(parca) in duz, parca
    assert "Ekran notu" not in metin
    assert "Uydurma Muhasip" not in metin


@pytest.mark.parametrize(
    "belge_adi",
    [*KATALOG_KABUL_KODLARI, "kurtarma_anahtari_belgesi"],
)
def test_tckn_hicbir_belgede_yok(belge_adi: str, yakalanan: list[evrak.Belge]) -> None:
    """Programın bugün ürettiği belgelerde 11 haneli kimlik deseni yok: kişi alanlarına sağlaması
    tutan uydurma T.C. kimlik numarası yazılır (hesap sahibinin ve okul müdürünün adı), çıktıda
    aranır. K9 ayarının kolları (`k9_kapali`, `k9_acik`) bağış kaydıyla F3'te eklenir. E01-E03
    (F1c 10. adım): numara belgenin basmadığı serbest metinlere yazılır (görev bölümü toplantısının
    gündemi, kararın metni, devralınan üyeliğin dayanak notu, dönemin programdan önceki kanıtı);
    Word ve PDF çıktısı, içerik JSON'u ve `BASIM` satırı aranır."""
    tckn = _saglamali_uydurma_numara("100000001")
    if belge_adi in gke.KODLAR:
        _genel_kurul_evraki_tckn(belge_adi, tckn)
        return
    if belge_adi in gorev_evraki.KODLAR:
        _gorev_evraki_tckn(belge_adi, tckn)
        return
    _okul(principal_name=f"Uydurma Müdür {tckn}")
    if belge_adi == "E63":
        hesap = hesap_ac(AccountRole.MUHASIP, ad=f"{UYDURMA_AD} {tckn}")
        yanit = _bas(hesap.id)
        assert yanit.status_code == 200
        pdf = _pdf(yanit)
        (belge,) = yakalanan
        icerik = evrak.kanonik_json(belge)
        satir = AuditTrail.objects.filter(action=AuditAction.BASIM).get()
        # PDF özeti ve object_id T.C. kimlik no taşıyamaz, ama 11 haneli desene rastlantıyla uyabilir:
        # özet güne ve belge metnine bağlıdır, kötü günde kapı her koşuda düşerdi. İkisi aramadan
        # çıkar, değerleri kilitlenir: satıra başka alan girerse bu test düşer.
        assert set(satir.values) == {"kod", "sha256"}
        assert satir.values["sha256"] == [None, hashlib.sha256(pdf).hexdigest()]
        assert satir.object_id == str(hesap.id)
        icerik += str(satir.values["kod"]) + str(satir.changed_fields)
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
        "veri_sorumlusu",
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
    """Dosyanın izi `BASIM` satırıdır: program yöneticisinin adına, model `okul.Account`, kimlik
    hesap; değerler yalnız kod ve PDF'in sha256'sı, içerik MAC'i yok. Üretimin kaydı ayrıca
    `GeneratedDocument` satırıdır (`OLUSTUR`, aynı işlemde; plan F1c 9. adım). Hesabın satır izi ve
    kaydın bütünlüğü değişmez (pusula hesabı aklamaz, eski kaydını örtmez); zincir bütün; erişim
    günlüğüne girmez."""
    _okul()
    hesap = hesap_ac(AccountRole.DENETLEME_KURULU, ad="Uydurma Denetçi")
    son, erisim = _son_seq(), AccessLog.objects.count()

    pdf = _pdf(_bas(hesap.id))

    kayit_satiri, satir = AuditTrail.objects.filter(seq__gt=son).order_by("seq")
    assert (kayit_satiri.action, kayit_satiri.model) == (
        AuditAction.OLUSTUR,
        "oab.GeneratedDocument",
    )
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
    assert denetim_izi.zinciri_dogrula() == []


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
            veri_sorumlusu="",
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
    sırasıyladır. Uçları bağlı ama ekranı henüz olmayan satır (`EKRANSIZ_SATIRLAR`; F2 11a: Genel
    Kurul ve Gelen-Giden Evrak) basılmaz, adı yazılmaz; liste bayatlamaz (her biri etkin bir satırdır,
    gerekçesi vardır)."""
    etkin = {satir for rol in ROLLER for satir in etkin_hucreler(rol)}
    ekransiz = set(e63.EKRANSIZ_SATIRLAR)
    assert ekransiz <= etkin
    assert all(gerekce.strip() for gerekce in e63.EKRANSIZ_SATIRLAR.values())
    assert set(e63.BUGUNKU_ISLER) == etkin - ekransiz
    for is_ in e63.BUGUNKU_ISLER.values():
        assert is_.parcalar and all(parca.ad.strip() for parca in is_.parcalar), is_
        assert not re.search(r"\b(YK|DK|DEK|M\d+|E\d{2})\b", is_.ad), is_.ad
    for rol in ROLLER:
        assert e63.isler(rol) == tuple(
            e63.BUGUNKU_ISLER[s].rol_adi(rol) for s in etkin_hucreler(rol) if s not in ekransiz
        )
        # Etkin satırın, rolün pusulasında en az bir parçası vardır (boş ad basılmaz).
        for satir in etkin_hucreler(rol):
            if satir not in ekransiz:
                assert e63.BUGUNKU_ISLER[satir].rol_parcalari(rol), (rol, satir)


def test_e63_is_parcalari_var_olan_uclara_karsilik_gelir() -> None:
    """Orkestratör maddesi F-4: her işin her parçası, pusulası basılan rolün o satırda bugün
    yazabildiği bir uca bağlıdır (uç yoksa ad yazılamaz: "hesap geçişi", "birlik döneminin
    açılması" bugün yazılamaz). Ters yönde, etkin satırın her yazma ucu bir parçada adlanır ya da
    `ADSIZ_UCLAR`'da gerekçesiyle durur: bir faz yeni bir uç getirince ad da büyür. Ekranı henüz
    olmayan satırın (`EKRANSIZ_SATIRLAR`) uçları adlanmaz; satır ekranıyla bütünüyle gelir."""
    adsiz_kullanilan: set[str] = set()
    kullanilan_parcalar: set[tuple[Satir, str]] = set()
    for rol in ROLLER:
        for satir in etkin_hucreler(rol):
            if satir in e63.EKRANSIZ_SATIRLAR:
                continue
            uclar = _yazma_uclari(satir, rol)
            adli: set[str] = set()
            # Pusula rolün parçalarını basar (`rol_parcalari`, F1c 4. adım: M2'de personel işleri
            # yalnız program yöneticisinin, birlik kişileri yönetim kurulu rollerinin de işidir).
            for parca in e63.BUGUNKU_ISLER[satir].rol_parcalari(rol):
                kullanilan_parcalar.add((satir, parca.ad))
                assert parca.uclar, (rol, satir, parca.ad)
                assert parca.uclar <= uclar, (rol, satir, parca.ad, parca.uclar - uclar)
                adli |= parca.uclar
            kalan = uclar - adli
            assert kalan <= set(e63.ADSIZ_UCLAR), (rol, satir, kalan - set(e63.ADSIZ_UCLAR))
            adsiz_kullanilan |= kalan
    # Adsız listesi bayatlamaz: her biri gerçekten adsız kalan bir yazma ucudur, gerekçesi vardır.
    assert adsiz_kullanilan == set(e63.ADSIZ_UCLAR)
    assert all(gerekce.strip() for gerekce in e63.ADSIZ_UCLAR.values())
    # Her parça en az bir rolün pusulasına girer (hiçbir role açılmayan parça bayattır).
    assert kullanilan_parcalar == {
        (satir, parca.ad) for satir, is_ in e63.BUGUNKU_ISLER.items() for parca in is_.parcalar
    }


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
    """Orkestratör maddesi F-4, rol rol: program yöneticisi dokuz iş (veli listesi F1b 5. adımda;
    birlik kişileri ve veli listesinden birlik kişisi ekleme F1c 4. adımda Kişiler işine girdi; birlik
    dönemi ve geçiş kurulumu F1c 11. adımda ekranıyla okul bilgileri işine girdi; Organlar ve
    Temsilciler F1c 11. adımın ikinci parçasında ekranlarıyla Kişiler işine girdi, satırın başlığı
    üç ekranın adıdır); yönetim kurulu rolleri birlik kişileri, üyelik ve temsilci kaydı (sekreter
    ayrıca görev bölümü, yedek çağrısı, düşme ve görev bölümü evrakı), Genel Bakış'ta son oturumun
    kontrolü ve kendi parolası; Denetleme Kurulu geri yükleme kartının "Gördüm"ü, Organlar'da kendi
    görev bölümü ve tutanağı ve kendi parolası; okul müdürü yalnız kendi parolası (müdür yazıları
    F2/F4'tedir). Sonraki fazların işleri hiçbir pusulada yoktur."""
    kendi = "Kendi parolanızı değiştirme, Kilitle, Çık"
    son_oturum = "Genel Bakış: son oturumun kontrolü (“Kontrol ettim”)"
    birlik_kisileri = "Kişiler, Organlar, Temsilciler: birlik kişileri, üyelik ve temsilci kaydı"
    beklenen = {
        AccountRole.YONETICI: (
            "Okul bilgileri, ders yılı ve dönemler, kapalı günler, birlik dönemi ve geçiş kurulumu",
            "Kişiler, Organlar, Temsilciler: öğretmen ve diğer personel kaydı, e-Okul aktarımı, "
            "ayrılış havuzu, birlik kişileri, veli listesinden birlik kişisi ekleme, üyelik ve "
            "temsilci kaydı, Denetleme Kurulu yedeğinin çağrısı, üyeliğin düşmesi, görev bölümü "
            "evrakı ve temsilci çizelgesi",
            son_oturum,
            "Kullanıcılar: hesap açma, kapama, askıdan çıkarma, parola sıfırlama, hesap teslim "
            "pusulası",
            "Güvenlik: kurtarma anahtarı, şifreli yedek, yedekten geri yükleme, yedek raporu, "
            "Genel Bakış'ta güvenlik dosyasında kalan eski parola kayıtlarının silinmesi",
            "Ayarlar: boşta kilit süresi",
            "Kişiler: veli listesinin aktarımı ve silinmesi",
            "Güncelleme denetimi",
            kendi,
        ),
        AccountRole.BASKAN: (birlik_kisileri, son_oturum, kendi),
        AccountRole.BASKAN_YARDIMCISI: (birlik_kisileri, son_oturum, kendi),
        AccountRole.MUHASIP: (birlik_kisileri, son_oturum, kendi),
        AccountRole.SEKRETER: (
            "Kişiler, Organlar, Temsilciler: birlik kişileri, üyelik ve temsilci kaydı, görev "
            "bölümü ve yedek çağrısı, üyeliğin düşmesi, görev bölümü evrakı ve temsilci çizelgesi",
            son_oturum,
            kendi,
        ),
        AccountRole.DENETLEME_KURULU: (
            "Genel Bakış: yedekten geri yükleme kartını görüldü olarak işaretleme (“Gördüm”), "
            "Organlar: Denetleme Kurulunun görev bölümü ve tutanağı",
            kendi,
        ),
        AccountRole.MUDUR: (kendi,),
    }
    assert set(beklenen) == set(ROLLER)
    # Organlar ve temsilciler F1c 11. adımın ikinci parçasında ekranlarıyla geldi: "organ" ve
    # "temsilci" gelecek işler arasından çıktı.
    gelecek = re.compile(
        r"(?i)hesap geçişi|anahtarının yenilenmesi|küçük alım|kural sürümü|"
        r"bağışçı|takvim|uyum kaydı|genel kurul|karar|gelir-gider|harcama|bütçe|kantin|servis|"
        r"denetim planı|müdür yazısı|devir-teslim|öğrenci"
    )
    for rol, isler in beklenen.items():
        assert e63.isler(rol) == isler, rol
        for ad in isler:
            assert not gelecek.search(ad), (rol, ad)


def test_e63_yazi_tipi_evrak_hattinin() -> None:
    """Yazı tipi evrak hattınınki: Liberation Serif, düz ve kalın (plan F1c kararları "Evrak biçimi";
    tasarım §9.1-8: E63 de bu hatta geçer). Pusulada Liberation Serif'te bulunmayan glif yoktur,
    DejaVu yedeği gömülmez."""
    belge = e63.pusula_belgesi(
        tanitici="muhasip",
        rol=AccountRole.MUHASIP,
        acilis=datetime(2026, 11, 3, 9, 0, tzinfo=UTC),
        okul_adi=OKUL_ADI,
        ilce=None,
        bosta_dakika=10,
        veri_sorumlusu="",
    )
    okuyucu = PdfReader(io.BytesIO(evrak.pdf_ciz(belge)))
    yazi_tipleri: set[str] = set()
    for sayfa in okuyucu.pages:
        kaynaklar: Any = sayfa["/Resources"]
        for tip in kaynaklar["/Font"].values():
            yazi_tipleri.add(str(tip.get_object()["/BaseFont"]).split("+", 1)[-1])
    assert yazi_tipleri == {"Liberation-Serif", "Liberation-Serif-Bold"}, yazi_tipleri


def test_e63_uretimi_evrak_kaydidir_dosyasi_saklanmaz() -> None:
    """E63 öteki evrak gibi `GeneratedDocument` kaydı alır (plan F1b-2 ekleri 04.11.2026 (3); F1c 9.
    adım): konu hesap, dönemsiz, kural paketsiz, biçim PDF, içerik JSON'u şifreli, dosyası yok;
    üreten program yöneticisi. Yeniden üretim yeni sürüm satırıdır, önceki `YERINI_ALDI` olur ve
    silinmez. Kayıtlı içerikten yeniden çizim aynı özeti verir; dosya deposuna bir şey yazılmaz."""
    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    dosyalar = _dosyalar()

    _bas(hesap.id)
    _bas(hesap.id)

    kayitlar = list(
        GeneratedDocument.objects.filter(
            subject_type="okul.Account", subject_id=str(hesap.id)
        ).order_by("version")
    )
    assert [(k.doc_type, k.version, k.status) for k in kayitlar] == [
        ("E63", 1, DocumentStatus.YERINI_ALDI),
        ("E63", 2, DocumentStatus.GECERLI),
    ]
    son = kayitlar[-1]
    assert (son.term_id, son.rule_package_id, son.formats, son.personal_list) == (
        None,
        None,
        ["PDF"],
        False,
    )
    assert str(son.generated_by_id) == TEST_HESAP_ID and son.ekler().count() == 0
    assert "Uydurma Muhasip" not in son.content_json
    belge = evrak_servisi.yeniden_ciz(son)
    assert belge.kod == "E63" and evrak.icerik_ozeti(belge) == son.content_sha256
    assert evrak.kanonik_json(belge) == son.content_json
    # İkinci üretim aynı veriden: içerik ve özet aynı, kayıt ayrı sürüm.
    assert kayitlar[0].content_sha256 == son.content_sha256
    assert _dosyalar() == dosyalar
    # Şifreli sütun düz metin taşımaz.
    from django.db import connection

    with connection.cursor() as imlec:
        imlec.execute("SELECT content_json FROM oab_generateddocument WHERE id = %s", [son.pk])
        (ham,) = imlec.fetchone()
    assert '"bloklar"' not in ham and "HESAP TESLİM" not in ham and ham != son.content_json
    for kayit in kayitlar:
        assert denetim_izi.kaydi_dogrula(GeneratedDocument, kayit.pk) is True


def test_e63_evrak_kaydi_yazilamazsa_pdf_verilmez(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kaydedici kayıtlı değilse (fail-closed) ya da kayıt düşerse PDF verilmez, `BASIM` yazılmaz."""
    from apps.okul.services import evrak_kaydi

    _okul()
    hesap = hesap_ac(AccountRole.MUHASIP, ad="Uydurma Muhasip")
    monkeypatch.setattr(evrak_kaydi, "_kaydedici", [])
    with pytest.raises(evrak_kaydi.EvrakKaydiYok):
        hesaplar.teslim_pusulasi(by_hesap_id=TEST_HESAP_ID, hesap_id=hesap.id)
    assert not AuditTrail.objects.filter(action=AuditAction.BASIM).exists()
    assert not GeneratedDocument.objects.exists()


# ============================================================ atıflar ve sözlük


def _depo_dosyasi(goreli: str) -> str:
    """Depo kökündeki dosya (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[5], Path("/repo")):
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
            veri_sorumlusu="",
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
    # Rolün pusulasındaki ad yalnız o rolün parçalarıdır (M2'de yönetim kurulu rolleri).
    yield from (
        e63.BUGUNKU_ISLER[satir].rol_adi(rol)
        for rol in ROLLER
        for satir in etkin_hucreler(rol)
        if satir not in e63.EKRANSIZ_SATIRLAR
    )
    yield e63.ILK_GIRIS_BASLIGI
    yield from (adim.format(tanitici="<tanıtıcı>") for adim in e63.ILK_GIRIS_ADIMLARI)
    yield e63.PAROLA_BASLIGI
    yield from e63.PAROLA_KURALLARI
    yield e63.KILIT_BASLIGI
    yield e63.BOSTA_KILIT.format(dakika="N")
    yield from (e63.KILITLE, e63.ARTAN_BEKLEME, e63.HATALI_DENEME_ASKISI, e63.YONETICI_ASKI_YOK)
    yield e63.KAPALI_ZARF
    yield from (e63.AYDINLATMA_BASLIGI, e63.AYDINLATMA_VERI_SORUMLUSU_ETIKETI)
    yield e63.AYDINLATMA_VERI_SORUMLUSU_YERI
    yield from e63.AYDINLATMA_SATIRLARI
    yield e63.AYDINLATMA_NOTU
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


# ============================================================ katalog (tasarım §9.5-§9.7)

TASARIM = "docs/tasarim/2026-10-31-genel-tasarim.md"
#: Fazı gelen kodların adı (ad → kod listesi, tasarım §10.5); kaynakla karşılaştırılmak için ELLE.
KATALOG_ADLARI = {
    "E01": "YK görev bölümü, imza yetkisi ve temsilci karar taslağı",
    "E02": "Denetleme Kurulu görev bölümü tutanağı ve denetim planı",
    "E03": "Birlik temsilcilerinin kurul ve komisyonlara görevlendirme çizelgesi",
    "E05": "Genel kurul toplantı çağrısı ve gündemi (dosya nüshası; duyuru kanıtıyla)",
    "E06": "Genel kurul duyurusu — ilan panosu ve internet sayfası (kişisiz)",
    "E07": "Üyelere elden yazılı davet ve sınıf teslim çizelgesi",
    "E08": "Genel kurul katılım cetveli",
    "E09": "YK ve DK (veli koltuğu) aday listeleri",
    "E10": "Genel kurul toplantı tutanağı",
    "E11": "İbra edilmeyen muhasebe evrakının teslim tutanağı (divan)",
    "E12": "İbra edilmediğine dair il/ilçe MEM'e resmî yazı",
    "E13": "Genel kurul sonuç bildirimi (okul müdürlüğüne)",
    "E14": "Yıllık iş takvimi",
    "E63": "Hesap teslim pusulası",
    "E64": "Genel kurul yeter sayı tespit tutanağı (sağlandı / sağlanamadı)",
}
#: Katalog dışı program belgeleri (tasarım §9.7): E-kodu almazlar.
PROGRAM_BELGELERI = (
    "Kurtarma anahtarı belgesi",
    "Kurtarma anahtarı zarfı imha tutanağı",
    "Yedek Raporu",
)
_KATALOG_SATIRI = re.compile(r"^\| (E\d{2}) \|(.*)\|$", re.MULTILINE)


def _bolum(baslangic: str, bitis: str) -> str:
    metin = _depo_dosyasi(TASARIM)
    bas = metin.index(f"\n{baslangic}")
    return metin[bas : metin.index(f"\n{bitis}", bas)]


def _katalog_95() -> list[tuple[str, str, str]]:
    """Tasarım §9.5'in satırları: (kod, belge adı, faz). Faz sütununun ilk sözcüğü alınır."""
    satirlar: list[tuple[str, str, str]] = []
    for kod, kalan in _KATALOG_SATIRI.findall(_bolum("### 9.5 ", "### 9.6 ")):
        sutunlar = kalan.split("|")
        satirlar.append((kod, sutunlar[0].strip(), sutunlar[-1].split()[0]))
    return satirlar


def test_katalogdaki_her_kodun_testi_var() -> None:
    """Tasarım §10.5. Faz süzmeli: fazı henüz gelmeyen kodun testi istenmez (plan F1b-6 kararları)."""
    satirlar = _katalog_95()
    kodlar = [kod for kod, _, _ in satirlar]
    # §9.5 ile §9.6 aynı 79 kodu, birer kez taşır.
    beklenen = [f"E{no:02d}" for no in range(1, 80)]
    assert sorted(kodlar) == beklenen
    kodlar_96 = [kod for kod, _ in _KATALOG_SATIRI.findall(_bolum("### 9.6 ", "### 9.7 "))]
    assert sorted(kodlar_96) == beklenen
    # Fazı gelen her kodun kabul testi ve ad satırı var; katalog dışı parametre yazım hatasıdır.
    gelenler = faz_ortak.fazi_gelenler({kod: faz for kod, _, faz in satirlar})
    assert gelenler <= set(KATALOG_KABUL_KODLARI) <= set(kodlar)
    assert gelenler <= set(KATALOG_ADLARI)
    adlar = {kod: ad for kod, ad, _ in satirlar}
    for kod, ad in KATALOG_ADLARI.items():
        assert adlar[kod] == ad
    # §7'nin andığı her belge kataloğun kodudur.
    atiflar = set(re.findall(r"\bE\d{2}\b", _bolum("## 7. ", "## 8. ")))
    assert atiflar and atiflar <= set(kodlar), sorted(atiflar - set(kodlar))
    # Program belgeleri kod almaz.
    program_bolumu = _bolum("### 9.7 ", "## 10. ")
    assert _KATALOG_SATIRI.findall(program_bolumu) == []
    for belge in PROGRAM_BELGELERI:
        assert belge in program_bolumu, belge
        assert belge not in adlar.values(), belge


@pytest.mark.parametrize(
    ("gecerli", "beklenen"),
    [("F1b", {"E63"}), ("F1c", {"E01", "E02", "E03", "E63"})],
)
def test_katalog_faz_suzmesi(gecerli: str, beklenen: set[str]) -> None:
    """Süzme gerçek katalogda: "F2 (metni F1b içe aktarma ekranında)" gibi notlu satır da okunur."""
    fazlar = {kod: faz for kod, _, faz in _katalog_95()}
    assert faz_ortak.fazi_gelenler(fazlar, gecerli=gecerli) == beklenen
    assert fazlar["E04"] == "F2"


# ============================================================ karar taslağı (F1c 6. adım)


@pytest.mark.django_db
def test_karar_taslagi_varsayilan() -> None:
    """AYNEN (tasarım §12.A, §10.5): karar "taslak" doğar (görev bölümü kaydının ürettiği karar da;
    program karar defterinin yerine geçmez, md. 13/5); "deftere işlendi" işareti yalnız kabul
    edilmiş karardan ve defter, sıra no ve sayfayla konur. Durum servisi F1c'de yalnız taslağı
    iptal eder; kabul, ret ve deftere işleme F3'ün karar defteri akışındadır."""
    donem = o.donem()
    uyeler = o.yk_kurulu(donem)
    karar = o.yk_gorev_bolumu(donem, {"SEKRETER": uyeler[0]}, gun=date(2026, 10, 20)).karar
    assert (karar.status, karar.kind) == (DecisionStatus.TASLAK, DecisionKind.GOREV_BOLUMU)
    assert (karar.book_id, karar.decision_no, karar.page_no) == (None, None, None)
    with pytest.raises(KararDurumuGecersiz):
        karar.status = DecisionStatus.DEFTERE_ISLENDI
        karar.save()
    BoardDecision.objects.filter(pk=karar.pk).update(status=DecisionStatus.KABUL_EDILDI)
    karar.refresh_from_db()
    karar.status = DecisionStatus.DEFTERE_ISLENDI
    with pytest.raises(IntegrityError), transaction.atomic():
        karar.save()
    defter = kurullar.karar_defteri_olustur(last_no_before_program=41, last_page_before_program=12)
    karar.book, karar.decision_no, karar.page_no = defter, 42, 13
    karar.save()
    assert BoardDecision.objects.get(pk=karar.pk).status == DecisionStatus.DEFTERE_ISLENDI
    toplanti = kurullar.toplanti_olustur(donem=donem, organ="YK", kind=MeetingKind.AYLIK)
    yeni = kurullar.karar_taslagi_olustur(toplanti, kind=DecisionKind.YEDEK_CAGIRMA)
    with pytest.raises(KararDurumuGecersiz, match="karar defteri ekranıyla"):
        kurullar.karar_durumu_yaz(yeni, DecisionStatus.KABUL_EDILDI)
    iptal = kurullar.karar_durumu_yaz(yeni, DecisionStatus.IPTAL)
    assert iptal.status == DecisionStatus.IPTAL
    with pytest.raises(KararDurumuGecersiz):
        iptal.status = DecisionStatus.TASLAK
        iptal.save()
    with pytest.raises(KararDurumuGecersiz):
        BoardDecision.objects.create(
            meeting=toplanti, kind=DecisionKind.YEDEK_CAGIRMA, status=DecisionStatus.KABUL_EDILDI
        )


# ============================================================ E01, E02, E03 (F1c 10. adım)

#: Sayfa bütçesi, gerçek uzunlukta uydurma veriyle (`ge_ortak.tam_kurulum(uzun=True)`). Tasarım sınırı
#: yazmaz (§9.1-4 "sayfa bütçesi gerçek uzunlukta uydurma veriyle sınanır"); ölçülen değerler: E01
#: üç sayfa (12 punto gövde, dört bölüm ve tam kadro; imza satırı tek yaprakta), E02 ve E03 iki.
GOREV_EVRAKI_SAYFA_SINIRI: dict[str, int] = {"E01": 3, "E02": 2, "E03": 2}
#: PDF altlığı (karşılaştırmaya girmez; UY-18).
_ALTLIK = re.compile(r"OAB Defteri · E\d{2} · Sayfa \d+\s*/\s*\d+")
#: Hiçbir F1c belgesinde basılmayan kurum kodu (okul kartının uydurma değeri; plan F1c kararları).
KURUM_KODU = "999001"


def _gorev_evraki_yolu(kod: str, donem: OabTerm) -> str:
    return f"/api/v1/oab/terms/{donem.pk}/documents/{kod.lower()}/"


def _uret(kod: str, donem: OabTerm) -> tuple[GeneratedDocument, list[str]]:
    """Üretim ucundan: E02 Denetleme Kurulu hesabıyla, ötekiler program yöneticisiyle."""
    yol = _gorev_evraki_yolu(kod, donem)
    if kod == gorev_evraki.E02:
        with o.rol_olarak(AccountRole.DENETLEME_KURULU):
            yanit = APIClient().post(yol, {}, format="json")
    else:
        yanit = APIClient().post(yol, {}, format="json")
    assert yanit.status_code == 201, yanit.content
    veri = yanit.json()
    return GeneratedDocument.objects.get(pk=veri["evrak"]["id"]), veri["uyarilar"]


def _dosya(kayit: GeneratedDocument, bicim: str) -> bytes:
    (ek,) = [e for e in kayit.ekler() if e.mime == evrak_servisi.BICIM_TURLERI[bicim]]
    return dosya_deposu.oku(ek)


def _akis(belge: evrak.Belge) -> str:
    return " ".join(evrak.metin_akisi(belge))


def _alt_basliklar(belge: evrak.Belge) -> list[str]:
    return [b.metin for b in belge.bloklar if isinstance(b, evrak.AltBaslik)]


def _bolum_tablolari(belge: evrak.Belge, bolum: str) -> list[evrak.Tablo]:
    """Bölüm başlığından sonraki (bir sonraki bölüme dek) tablolar."""
    tablolar: list[evrak.Tablo] = []
    icinde = False
    for blok in belge.bloklar:
        if isinstance(blok, evrak.AltBaslik):
            icinde = blok.metin == bolum
        elif icinde and isinstance(blok, evrak.Tablo):
            tablolar.append(blok)
    return tablolar


def _satirlar(tablo: evrak.Tablo) -> dict[str, str]:
    return {satir[0]: satir[1] for satir in tablo.satirlar}


def _imza_sahipleri(belge: evrak.Belge) -> list[tuple[str, str]]:
    """İmza bloklarının sahipleri (resmî yazının imza bölümü dahil; soldan sağa)."""
    return [
        (sahip.ad, sahip.gorev)
        for blok in belge.bloklar
        if isinstance(blok, evrak.Imza | evrak.ResmiImza)
        for sahip in blok.sahipler
    ]


def _ad(uyelik: Any) -> str:
    return evrak.ad_soyad(uyelik.person.first_name, uyelik.person.last_name)


def _e03_kisileri(belge: evrak.Belge) -> set[tuple[str, str]]:
    """E03'ün (kurul, "Ad SOYAD (Asıl|Yedek)") çiftleri: kurul adı yalnız ilk satırdadır."""
    (tablo,) = _bolum_tablolari(belge, gorev_evraki.E03_BOLUMLER[0])
    kurul, ciftler = "", set()
    for satir in tablo.satirlar:
        kurul = satir[1] or kurul
        if satir[2] != gorev_evraki.BOS:
            ciftler.add((kurul, f"{satir[2]} ({satir[3]})"))
    return ciftler


def _kabul_e01() -> None:
    """Tasarım §9.6 E01 "Kabul örneği": 5+5 kadro; dört görev dolu ve tekil; "kaçıncı dönem"
    sayaçtan; sütun başlığı "Beyan (okul uygulaması)", Yönetmelik maddesine bağlanmaz (KM-8); imza
    yetkisi başkan + muhasip (yokluğunda başkan yardımcısı); bankaya bildirim tarihi ve belgesi alanı;
    temsilci satırları E03 ile aynı kişiler; FR-006 A-D bölümleri. Plan: banka satırları "………"
    (F3); karar `TASLAK` iken sıra no ve sayfa "………"; KDT ve taslak ibaresi; kurum kodu yok."""
    kurulum = ge_ortak.tam_kurulum()
    kayit, uyarilar = _uret("E01", kurulum.donem)
    assert uyarilar == []
    assert sorted(kayit.formats) == ["DOCX", "PDF"] and kayit.ekler().count() == 2
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert belge.bloklar[0] == evrak.Baslik(
        gorev_evraki.BELGE_ADLARI["E01"], alt=evrak.TASLAK_IBARESI
    )
    assert _alt_basliklar(belge) == list(gorev_evraki.E01_BOLUMLER)
    assert [b[:2] for b in _alt_basliklar(belge)] == ["A.", "B.", "C.", "D."]

    toplanti = _satirlar(_bolum_tablolari(belge, gorev_evraki.E01_BOLUMLER[0])[0])
    # Kurulu seçen genel kurul dönemi açan genel kuruldur (olağanüstü kol `test_gorev_evraki`'nde).
    assert toplanti[gorev_evraki.GENEL_KURUL_SECIM_TARIHI] == "10.10.2026"
    assert kurulum.donem.start_date == date(2026, 10, 10)
    assert toplanti[gorev_evraki.KARAR_DEFTERI] == gorev_evraki.BOS
    assert toplanti[gorev_evraki.KATILAN] == "4/5"
    assert toplanti[gorev_evraki.TOPLANTI] == "17.10.2026 15:00 · Okul toplantı salonu"

    gorev, yedek = _bolum_tablolari(belge, gorev_evraki.E01_BOLUMLER[1])
    assert gorev.basliklar[3] == "Beyan (okul uygulaması)" and "md." not in gorev.basliklar[3]
    assert [s[0] for s in gorev.satirlar] == [
        "Başkan",
        "Başkan yardımcısı",
        "Muhasip",
        "Sekreter",
        "Üye",
    ]
    adlar = [_ad(u) for u in kurulum.yk_asillar]
    assert [s[1] for s in gorev.satirlar] == adlar and len(set(adlar)) == 5
    sayaclar = [str(uyelikler.secilme_sayaci(u.person, "YK")) for u in kurulum.yk_asillar]
    assert [s[2] for s in gorev.satirlar] == sayaclar == ["1"] * 5
    beyan = gorev_evraki.BEYAN.format(suc="16.10.2026", tek="16.10.2026")
    assert {s[3] for s in gorev.satirlar} == {beyan}
    assert [s[0] for s in yedek.satirlar] == ["1", "2", "3", "4", "5"]
    assert [s[1] for s in yedek.satirlar] == [_ad(u) for u in kurulum.yk_yedekler]

    imza = _satirlar(_bolum_tablolari(belge, gorev_evraki.E01_BOLUMLER[2])[0])
    assert imza[gorev_evraki.BANKA_HESABI] == gorev_evraki.BOS
    assert imza[gorev_evraki.BANKAYA_BILDIRIM] == gorev_evraki.BOS
    assert imza[gorev_evraki.MUSTEREK_IMZA] == gorev_evraki.MUSTEREK_IMZA_DEGERI.format(
        baskan=adlar[0], muhasip=adlar[2], yardimci=adlar[1]
    )

    duzen, temsilci = _bolum_tablolari(belge, gorev_evraki.E01_BOLUMLER[3])
    assert _satirlar(duzen)[gorev_evraki.AYLIK_TOPLANTI] == ge_ortak.TOPLANTI_GUNU_KURALI
    e01_kisileri = {(s[0], s[1]) for s in temsilci.satirlar}
    kayit_e03, _ = _uret("E03", kurulum.donem)
    assert e01_kisileri == _e03_kisileri(evrak_servisi.yeniden_ciz(kayit_e03))
    assert gorev_evraki.BOS not in {s[1] for s in temsilci.satirlar}
    assert len(e01_kisileri) == 11

    konum = next(i for i, b in enumerate(belge.bloklar) if isinstance(b, evrak.KonumCumlesi))
    assert belge.bloklar[konum] == evrak.KonumCumlesi(evrak.KDT)
    assert isinstance(belge.bloklar[konum + 1], evrak.Imza)
    assert _imza_sahipleri(belge) == list(
        zip(adlar, ["Başkan", "Başkan yardımcısı", "Muhasip", "Sekreter", "Üye"], strict=True)
    )
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    assert KURUM_KODU not in _akis(belge)


def _kabul_e02() -> None:
    """Tasarım §9.6 E02 "Kabul örneği": veli koltuğu genel kurul seçimi, iki öğretmen öğretmenler
    kurulu seçimi ayrı satırda; hayırsever yok; başkanlık sayacı ≤ 3; planda ≥ 2 ara denetim; müdür
    bloğu yok (MB-15). Üreten yalnız Denetleme Kurulu; konum cümlesi ve taslak ibaresi yok; imza
    Denetleme Kurulu asıl üyeleri ve "Bilgi: Birlik Başkanı"."""
    kurulum = ge_ortak.tam_kurulum()
    yol = _gorev_evraki_yolu("E02", kurulum.donem)
    assert APIClient().post(yol, {}, format="json").status_code == 403  # program yöneticisi
    kayit, uyarilar = _uret("E02", kurulum.donem)
    assert uyarilar == []
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert belge.bloklar[0] == evrak.Baslik(gorev_evraki.BELGE_ADLARI["E02"])
    assert _alt_basliklar(belge) == list(gorev_evraki.E02_BOLUMLER)
    assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar)
    akis = _akis(belge)
    assert evrak.TASLAK_IBARESI not in akis and evrak.KDT not in akis

    toplanti = _satirlar(_bolum_tablolari(belge, gorev_evraki.E02_BOLUMLER[0])[0])
    assert toplanti[gorev_evraki.GENEL_KURUL_TARIHI] == "10.10.2026"
    assert kurulum.donem.start_date == date(2026, 10, 10)
    assert toplanti[gorev_evraki.TOPLANTI] == "16.10.2026 15:00 · Okul toplantı salonu"

    (uyeler,) = _bolum_tablolari(belge, gorev_evraki.E02_BOLUMLER[1])
    kanallar = [s[0] for s in uyeler.satirlar]
    assert kanallar[:3] == [
        "Veli — genel kurul seçimi",
        "Öğretmen — öğretmenler kurulu seçimi",
        "Öğretmen — öğretmenler kurulu seçimi",
    ]
    assert [s[2] for s in uyeler.satirlar] == ["Asıl"] * 3 + ["Yedek"] * 3
    assert [s[3] for s in uyeler.satirlar[:3]] == ["Başkan", "Üye", "Üye"]
    assert "ayırsever" not in akis  # "Hayırsever" de "hayırsever" de yok
    sinir = kural("denetleme_kurulu.baskan_secilme_siniri", date(2026, 10, 16), kurulum.donem)
    assert uyeler.satirlar[0][4] == "1" and int(uyeler.satirlar[0][4]) <= sinir
    assert [s[4] for s in uyeler.satirlar[1:]] == [""] * 5

    (plan,) = _bolum_tablolari(belge, gorev_evraki.E02_BOLUMLER[2])
    ara = [s for s in plan.satirlar if s[0].endswith("ara denetim")]
    assert len(ara) >= 2 and [s[1] for s in ara] == ["15.01.2027", "15.04.2027"]

    baskan = kurulum.dk_asillar[0]
    assert _imza_sahipleri(belge) == [
        (_ad(baskan), "Denetleme Kurulu Başkanı"),
        (_ad(kurulum.dk_asillar[1]), "Üye"),
        (_ad(kurulum.dk_asillar[2]), "Üye"),
        (_ad(kurulum.yk_asillar[0]), "Bilgi: Birlik Başkanı"),
    ]
    # Antet okul müdürlüğünündür; müdür bloğu ("Okul Müdürü", "Görüldü") yok.
    assert "Okul Müdürü" not in akis and "örüldü" not in akis
    assert not [g for _a, g in _imza_sahipleri(belge) if "üdür" in g]
    assert KURUM_KODU not in akis


def _kabul_e03() -> None:
    """Tasarım §9.6 E03 "Kabul örneği": kademe satırları okul kartının kademe kesişimiyle (karma
    okulda ortaöğretimin ödül-disiplin ve kontenjan, ortaokulun davranış kurulu satırları birlikte);
    kampüsteki okulda kampüs yönetimi satırı; RPD satırında "öğretmenler kurulu belirler" notu;
    taşımacıyı tespit, muhammen bedel ve kiralama ihale komisyonu satırlarında başkanın adı
    kendiliğinden; pay dağıtım komisyonu satırı yalnız başkan seçildiyse; kantini olan okulda kantin
    denetim satırı; satırlar yalnız temsilciler çizelgesinden (§6.4.4), genel setin alım komisyonu,
    Öğretmenler Kurulu ve gözlemci satırları yok. İmza Sekreter + Birlik Başkanı; "Teslim alan: Okul
    Müdürü". Yönetim kurulu kararı bağlı değilse "………"."""
    kurulum = ge_ortak.tam_kurulum()
    kayit, uyarilar = _uret("E03", kurulum.donem)
    assert uyarilar == []
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert belge.bloklar[0] == evrak.Baslik(
        gorev_evraki.BELGE_ADLARI["E03"], alt=evrak.TASLAK_IBARESI
    )
    (tablo,) = _bolum_tablolari(belge, gorev_evraki.E03_BOLUMLER[0])
    kurul_adlari = [s[1] for s in tablo.satirlar if s[1]]
    cizelge = temsilciler.temsilci_cizelgesi(kurulum.donem)
    assert kurul_adlari == [s.ad for s in cizelge]
    etiket = {str(t): str(t.label) for t in Representation}
    for temsil in (
        Representation.ODUL_DISIPLIN_KURULU,
        Representation.KONTENJAN_KOMISYONU,
        Representation.DAVRANIS_DEGERLENDIRME_KURULU,
        Representation.KAMPUS_YONETIMI,
        Representation.KANTIN_DENETIM_KOMISYONU,
        Representation.RPD_YURUTME_KOMISYONU,
    ):
        assert etiket[temsil] in kurul_adlari, temsil
    assert evrak.Paragraf(gorev_evraki.RPD_NOTU) in belge.bloklar
    assert "öğretmenler kurulunda belirlenir" in gorev_evraki.RPD_NOTU
    baskan_adi = _ad(kurulum.yk_asillar[0])
    satir_no = {s[1]: i for i, s in enumerate(tablo.satirlar) if s[1]}
    for temsil in temsilciler.BASKANIN_KOMISYONLARI:
        satir = tablo.satirlar[satir_no[etiket[temsil]]]
        assert (satir[2], satir[4]) == (baskan_adi, gorev_evraki.BASKAN_SIFATIYLA)
    sosyal = tablo.satirlar[satir_no[etiket[Representation.SOSYAL_ETKINLIKLER_KURULU]]]
    assert sosyal[4] == "……… · 20.10.2026"
    kontenjan = tablo.satirlar[satir_no[etiket[Representation.KONTENJAN_KOMISYONU]]]
    assert kontenjan[4] == gorev_evraki.BOS  # karar bağı yok
    akis = _akis(belge)
    for yok in ("Öğretmenler Kurulu", "gözlemci", "Alım", "alım komisyonu", "Görüldü"):
        assert yok not in akis, yok
    assert etiket[Representation.PAY_DAGITIM_KOMISYONU] not in kurul_adlari
    assert _imza_sahipleri(belge) == [
        (_ad(kurulum.yk_asillar[3]), "Sekreter"),
        (baskan_adi, "Birlik Başkanı"),
        ("Gülten UYDURMACA", "Teslim alan: Okul Müdürü"),
    ]
    konum = next(i for i, b in enumerate(belge.bloklar) if isinstance(b, evrak.KonumCumlesi))
    assert isinstance(belge.bloklar[konum + 1], evrak.Imza)
    assert KURUM_KODU not in akis
    # Pay dağıtım komisyonu satırı başkan seçilince görünür (kanalı görevlendirmedir).
    temsilciler.temsilci_ekle(
        term=kurulum.donem,
        person=kurulum.yk_asillar[0].person,
        representation=Representation.PAY_DAGITIM_KOMISYONU,
        start_date=ge_ortak.TEMSILCI_GUNU,
    )
    yeni, _ = _uret("E03", kurulum.donem)
    (tablo,) = _bolum_tablolari(evrak_servisi.yeniden_ciz(yeni), gorev_evraki.E03_BOLUMLER[0])
    pay = next(s for s in tablo.satirlar if s[1] == etiket[Representation.PAY_DAGITIM_KOMISYONU])
    assert pay[2] == baskan_adi and pay[4] == gorev_evraki.KANALLAR["MEM_GOREVLENDIRME"]


GOREV_EVRAKI_KABULLERI = {"E01": _kabul_e01, "E02": _kabul_e02, "E03": _kabul_e03}


def _gorev_evraki_tckn(kod: str, tckn: str) -> None:
    """`test_tckn_hicbir_belgede_yok[E01-E03]`'ün gövdesi (yukarıda)."""
    kurulum = ge_ortak.tam_kurulum()
    for uyelik in (kurulum.yk_asillar[0], kurulum.dk_asillar[0], kurulum.yk_yedekler[0]):
        uyelikler.update_membership(uyelik, evidence_note=f"Uydurma dayanak {tckn}")
    for karar in BoardDecision.objects.filter(meeting__term=kurulum.donem):
        karar.text = f"Uydurma karar metni {tckn}"
        karar.save(update_fields=["text"])
    toplanti = kurulum.donem.board_meetings.first()
    assert toplanti is not None
    toplanti.agenda = f"Uydurma gündem {tckn}"
    toplanti.save(update_fields=["agenda"])
    kurulum.donem.pre_program_evidence = f"Uydurma kanıt {tckn}"
    kurulum.donem.save(update_fields=["pre_program_evidence"])

    kayit, _ = _uret(kod, kurulum.donem)
    pdf, docx = _dosya(kayit, "PDF"), _dosya(kayit, "DOCX")
    yanit = APIClient().get(f"/api/v1/oab/documents/{kayit.pk}/pdf/")
    assert yanit.status_code == 200
    satir = AuditTrail.objects.filter(action=AuditAction.BASIM).get()
    assert set(satir.values) == {"kod", "sha256"}
    metinler = [
        _metin(pdf),
        " ".join(cizici_.govde_metin_akisi(cizici_.ac(docx))),
        kayit.content_json,
        str(satir.values["kod"]),
        satir.object_id,
    ]
    for parca in metinler:
        assert not _ONBIR_HANE.search(parca)
        assert not _ONBIR_HANE.search(_duz(parca))
    assert tckn.encode() not in pdf


@pytest.mark.parametrize("kod", [k for k in KATALOG_KABUL_KODLARI if k != "E63"])
def test_docx_pdf_icerik_esdegerligi(kod: str) -> None:
    """Tasarım §10.5: kaydedilen iki dosyadan aynı kanonik metin akışı çıkar (gövde blokları belge
    sırasıyla, tablo hücreleri satır satır; PDF'te altlık ayıklanır; boşluk normalleştirilir);
    Word'de `w:caps` yok. Türkçe büyük harf: başlık `tr_upper`'dandır ("İ"), çıplak `.upper()` biçimi
    çıktıda yoktur. Genel kurul belgeleri (F2 9. adım): `_gk_docx_pdf_esdegerligi`."""
    if kod in gke.KODLAR:
        _gk_docx_pdf_esdegerligi(kod)
        return
    kurulum = ge_ortak.tam_kurulum()
    kayit, _ = _uret(kod, kurulum.donem)
    belge = evrak_servisi.yeniden_ciz(kayit)
    pdf_metni = _metin(_dosya(kayit, "PDF"))
    assert re.search(rf"OAB Defteri · {kod} · Sayfa 1\s*/\s*\d", pdf_metni)
    docx = _dosya(kayit, "DOCX")
    beklenen = _duz("".join(evrak.metin_akisi(belge)))
    assert _duz(_ALTLIK.sub("", pdf_metni)) == beklenen
    assert _duz("".join(cizici_.govde_metin_akisi(cizici_.ac(docx)))) == beklenen
    with zipfile.ZipFile(io.BytesIO(docx)) as arsiv:
        govde = arsiv.read("word/document.xml").decode("utf-8")
    assert "<w:caps" not in govde and "<w:smallCaps" not in govde
    ad = gorev_evraki.BELGE_ADLARI[kod]
    assert _duz(tr_upper(ad)) in _duz(pdf_metni)
    assert "İ" in tr_upper(ad) and _duz(ad.upper()) not in _duz(pdf_metni)


@pytest.mark.parametrize("kod", ["E01", "E03"])
def test_konum_kdt(kod: str) -> None:
    """§9.2: KDT gövdede, imza bloğunun hemen üstünde, 9 punto; başlıkta taslak ibaresi; altlıkta
    konum cümlesi yok."""
    from shared.tests.test_evrak import pdf_yazi_boyutlari

    kurulum = ge_ortak.tam_kurulum()
    belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
    (konum,) = [i for i, b in enumerate(belge.bloklar) if isinstance(b, evrak.KonumCumlesi)]
    assert belge.bloklar[konum] == evrak.KonumCumlesi(evrak.KDT)
    assert isinstance(belge.bloklar[konum + 1], evrak.Imza)
    baslik = belge.bloklar[0]
    assert isinstance(baslik, evrak.Baslik) and baslik.alt == evrak.TASLAK_IBARESI
    parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
    # Konum cümlesinin satırları (kısa parçalar başka bloklarda da geçebilir: "imzalanır;" gibi).
    konum_satirlari = {b for _s, m, b in parcalar if len(m) > 30 and m in evrak.KDT}
    assert konum_satirlari == {float(cizici_.KONUM_PUNTO)}
    altlik = [m for _s, m, _b in parcalar if m.startswith("OAB Defteri ·")]
    assert altlik and all(_ALTLIK.fullmatch(m) for m in altlik)


def test_konum_kdt_e02_de_yok() -> None:
    """E02 tutanaktır, karar taslağı değildir: konum cümlesi ve taslak ibaresi yoktur (§9.2)."""
    kurulum = ge_ortak.tam_kurulum()
    belge, _ = gorev_evraki.e02_belgesi(kurulum.donem)
    assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar)
    pdf_metni = _duz(_metin(evrak.pdf_ciz(belge)))
    assert _duz(evrak.KDT) not in pdf_metni and _duz(evrak.TASLAK_IBARESI) not in pdf_metni


@pytest.mark.parametrize(
    "kod",
    [
        "E01",
        "E02",
        "E03",
        *(f"E05_{kol}" for kol in gke.KOLLAR),
        "E06",
        "E07",
        "E08",
        "E64_saglandi",
        "E64_saglanamadi",
        "E64_saglanamadi_mudur",
        "E64_ikinci",
        "E09",
        "E10",
        "E10_mudur",
        "E11",
        "E12",
        "E13",
        "E14",
    ],
)
def test_mudur_bloklari_yalniz_93_tablosunda(kod: str) -> None:
    """MB-15, §9.3: müdür bloğu yalnız tablodaki belgelerde ve oradaki türüyle — E03'te "Teslim alan",
    E01 (yönetim kurulu belgesi) ve E02'de (Denetleme Kurulu, denetleyenin bağımsızlığı) yok; F1c
    belgelerinin hiçbirinde "Görüldü" bloğu yok. Genel kurul belgeleri (F2 9. adım; E05'in çağırana göre
    kolları, E64'ün sağlandı / sağlanamadı kolları): `_gk_mudur_bloklari`; 10. adımın belgeleri (E09-E14;
    E10'un müdürün çağırdığı genel kurul kolu): `_gk_ii_mudur_bloklari`."""
    if kod[:3] in GENEL_KURUL_EVRAKI_II:
        _gk_ii_mudur_bloklari(kod)
        return
    if kod[:3] in gke.KODLAR:
        _gk_mudur_bloklari(kod)
        return
    kurulum = ge_ortak.tam_kurulum()
    belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
    mudur = [gorev for _ad_, gorev in _imza_sahipleri(belge) if "Müdür" in gorev]
    assert mudur == (["Teslim alan: Okul Müdürü"] if kod == "E03" else [])
    assert "örüldü" not in _akis(belge)


def test_imza_ad_soyad_bicimi() -> None:
    """RYUE md. 17/2: imza bloğunda ad ilk harfi büyük, SOYAD `tr_upper` ile ("İ/ı" doğru); adı
    küçük harfle ve fazla boşlukla girilmiş kişi de böyle basılır. Okul müdürünün adı okul kartından
    (son sözcük soyadı)."""
    kurulum = ge_ortak.tam_kurulum()
    ge_ortak.okul_karti(principal_name="  ışıl   gülten  irmakçı ")
    kisiler.update_person(
        kurulum.yk_asillar[0].person,
        first_name="  ılgın  irem ",
        last_name="çiğdemoğlu",
        ayni_kisi_degil=True,
    )
    beklenen = "Ilgın İrem ÇİĞDEMOĞLU"
    for kod in gorev_evraki.KODLAR:
        belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
        adlar = {ad_ for ad_, _g in _imza_sahipleri(belge)}
        assert beklenen in adlar, kod
        for ad_ in adlar - {gorev_evraki.BOS}:
            *ilkler, soyad = ad_.split(" ")
            assert soyad == tr_upper(soyad), (kod, ad_)
            assert all(p[:1] == tr_upper(p[:1]) for p in ilkler), (kod, ad_)
    belge, _ = gorev_evraki.e03_belgesi(kurulum.donem)
    assert ("Işıl Gülten İRMAKÇI", "Teslim alan: Okul Müdürü") in _imza_sahipleri(belge)


def _indir(yol: str) -> bytes:
    yanit: Any = APIClient().get(yol)
    assert yanit.status_code == 200
    return b"".join(yanit.streaming_content)


def test_yeniden_basim_icerik_ozeti_ayni() -> None:
    """UY-13, §9.1-2: kayıtlı içerikten yeniden çizim aynı içerik özetini verir ve kaydedilen dosya
    aynı baytla basılır; kişi adı ve okul adı sonradan değişse de. Yeni üretim yeni sürümdür."""
    kurulum = ge_ortak.tam_kurulum()
    kayit, _ = _uret("E01", kurulum.donem)
    yol = f"/api/v1/oab/documents/{kayit.pk}/pdf/"
    ilk_pdf = _indir(yol)
    kisiler.update_person(kurulum.yk_asillar[0].person, first_name="Değişnur", ayni_kisi_degil=True)
    ge_ortak.okul_karti(school_name="Başka Örnek Ortaokulu")

    geri = evrak_servisi.yeniden_ciz(kayit)
    assert evrak.icerik_ozeti(geri) == kayit.content_sha256
    assert "Değişnur" not in _akis(geri) and "Başka Örnek" not in _akis(geri)
    assert _indir(yol) == ilk_pdf
    yeni, _ = _uret("E01", kurulum.donem)
    assert (yeni.version, yeni.status) == (2, DocumentStatus.GECERLI)
    assert yeni.content_sha256 != kayit.content_sha256
    assert GeneratedDocument.objects.get(pk=kayit.pk).status == DocumentStatus.YERINI_ALDI


#: Pilot eşdeğerlik (plan F1c kararları "Pilot eşdeğerlik"; tasarım §10.5): genel setin (GNL-OAB-FR-006,
#: 011, 022) bölüm ve alanları ELLE yazılmıştır; sağda belgedeki karşılığı ya da alınmama gerekçesi
#: (tasarım ve plan farkları). Gerçek örnekle elle karşılaştırma ertelenen sınamada kullanıcıdadır;
#: gerçek adlı belge depoya girmez.
PILOT: dict[str, list[tuple[str, str | None, str]]] = {
    "E01": [
        ("A. TOPLANTI", "A. Toplantı", ""),
        ("Genel kurul (seçim) tarihi", gorev_evraki.GENEL_KURUL_SECIM_TARIHI, ""),
        ("görev bölümü toplantısı tarih / saat / yer", gorev_evraki.TOPLANTI, ""),
        ("Katılan asıl üye sayısı", gorev_evraki.KATILAN, ""),
        ("karar: katılanların çoğunluğu", None, "md. 13/3: karar yeter sayısı üç (plan F1c-10)"),
        ("Karar defteri karar no", gorev_evraki.KARAR_DEFTERI, "taslakta ………"),
        ("B. GÖREV DAĞILIMI (md. 12/3) VE BEYANLAR", gorev_evraki.E01_BOLUMLER[1], ""),
        ("Görev", "Görev", ""),
        ("Adı ve soyadı", "Adı ve soyadı", ""),
        ("Kaçıncı dönem (md. 12/4 — en fazla 4)", "Kaçıncı dönem (md. 12/4)", "sınır pakette"),
        ("Beyan*", "Beyan (okul uygulaması)", "KM-8"),
        ("* Beyan dipnotu (md. 12/5, 12/4)", None, "beyan Yönetmeliğe bağlanmaz (KM-8)"),
        ("İmza", "İmza", ""),
        ("Yedek sırası (aldığı oy sırasıyla — md. 13/6)", "Yedek sırası (md. 13/6)", ""),
        ("Çağrılma tarihi (varsa)", "Çağrılma tarihi", ""),
        ("C. İMZA YETKİSİ VE BANKA (md. 18/2; 16/1)", gorev_evraki.E01_BOLUMLER[2], ""),
        ("Birlik banka hesabı (banka / şube / IBAN)", gorev_evraki.BANKA_HESABI, "F3'e dek ………"),
        ("Müşterek imza yetkilileri", gorev_evraki.MUSTEREK_IMZA, ""),
        ("Bankaya yetki bildirimi tarihi / belge", gorev_evraki.BANKAYA_BILDIRIM, "F3'e dek ………"),
        ("Okul müdürlüğüne bildirim", None, "tasarım §9.6 E01 veri kaynağında ve kabulünde yok"),
        ("D. ÇALIŞMA DÜZENİ KARARLARI (md. 13/3-5, 18/5)", gorev_evraki.E01_BOLUMLER[3], ""),
        ("Aylık toplantı günü (md. 13/3)", gorev_evraki.AYLIK_TOPLANTI, ""),
        ("Okul müdürüne aylık yazılı bildirim (md. 18/5)", gorev_evraki.AYLIK_BILDIRIM, ""),
        ("her ayın son iş günü", None, "md. 18/5 'her ayın sonunda' der (plan F1c-10)"),
        ("Koordinasyon (md. 13/4)", gorev_evraki.KOORDINASYON, ""),
        ("defter sorumluları", None, "korpusta dayanağı yok (altın kural 1)"),
        ("Birlik temsilcileri (kurul/komisyon)", "Birlik temsilcisi", "E03 ile aynı kaynak"),
        ("İmza: Başkan, Başkan Yrd., Muhasip, Sekreter, Üye", "Başkan yardımcısı", ""),
        ("Form kodları (OAB-FR-007/008/009/015/022)", None, "form kodu belgeye yazılmaz"),
        ("DAYANAK, kısaltma ve KVKK dipnotu, genel şablon notu", None, "kişisel veri dipnotu"),
    ],
    "E02": [
        ("A. TOPLANTI", "A. Toplantı", ""),
        ("Genel kurul tarihi", gorev_evraki.GENEL_KURUL_TARIHI, ""),
        ("Görev bölümü toplantısı — tarih / saat / yer", gorev_evraki.TOPLANTI, ""),
        ("Katılan asıl üye sayısı", gorev_evraki.KATILAN, ""),
        ("B. ÜYELER VE GÖREV BÖLÜMÜ (md. 14/1)", gorev_evraki.E02_BOLUMLER[1], ""),
        ("Seçim kanalı", "Seçim kanalı", ""),
        ("Adı ve soyadı", "Adı ve soyadı", ""),
        ("Asıl / yedek", "Asıl ya da yedek", ""),
        ("Görevi", "Görevi", ""),
        ("Kaçıncı başkanlık (md. 14/3 — en fazla 3)", "Kaçıncı başkanlık (md. 14/3)", ""),
        ("Beyan*", None, "tasarım §9.6 E02 veri kaynağında yok; beyan Yönetmeliğe bağlanmaz"),
        ("İmza", "İmza", ""),
        ("C. DENETİM PLANI (md. 14/4)", gorev_evraki.E02_BOLUMLER[2], ""),
        ("Denetim", "Denetim", ""),
        ("Planlanan tarih", "Planlanan tarih", ""),
        ("Kapsanan dönem", None, "dönemin denetim planı yalnız tarih tutar (tasarım §5.2.1)"),
        ("Rapor (OAB-FR-012/013) ve teslim", "Rapor", "form kodu yazılmaz"),
        ("Olağanüstü durum (md. 14/5)", None, "plan satırı değildir; çağrı F2'dedir"),
        ("İmza: Denetleme Kurulu Başkanı, Üye, Üye", "Denetleme Kurulu Başkanı", ""),
        ("Bilgi: Birlik Başkanı", "Bilgi: Birlik Başkanı", ""),
        ("Okul Müdürü (görüldü)", None, "MB-15 (plan F1c-10)"),
    ],
    "E03": [
        ("A. GÖREVLENDİRME ÇİZELGESİ", gorev_evraki.E03_BOLUMLER[0], ""),
        ("No", "Sıra", ""),
        ("Kurul / komisyon", "Kurul ya da komisyon", ""),
        ("Birlik temsilcisi (mevzuattaki sıfat) ve dayanak", None, "atıf kuralın kaydındadır"),
        ("Görevlendirilen (ad soyad) — asıl / yedek", "Görevlendirilen", ""),
        ("YK karar no / tarihi", "Yönetim kurulu kararı: sıra no ve tarih", ""),
        ("Okula bildirim", None, "tasarım §9.6 E03 veri kaynağında yok; teslim alan bloğu"),
        ("Mal ve Hizmet Alım (Harcama) Komisyonu", None, "plan F1c-10: alınmaz"),
        ("Öğretmenler Kurulu", None, "plan F1c-10: alınmaz (korpusta dayanağı yok)"),
        ("Genel kurul gözlemcileri", None, "plan F1c-10: alınmaz"),
        ("Not: eğitim kampüsü (md. 13/7)", "Kampüs yönetimi", "çizelgenin satırı"),
        ("B. DEĞİŞİKLİK KAYDI", None, "tasarım §9.6 E03 hücresinde yok"),
        ("İmza: Birlik Sekreteri, Birlik Başkanı", "Birlik Başkanı", ""),
        ("Teslim alan — Okul Müdürü", "Teslim alan: Okul Müdürü", "§9.3"),
    ],
}
#: Genel setten alınmayan, belgede geçmemesi gereken ibareler (plan F1c-10).
PILOT_ALINMAYANLAR: dict[str, tuple[str, ...]] = {
    "E01": ("katılanların çoğunluğu", "son iş günü", "md. 12/5", "OAB-FR", "Görüldü"),
    "E02": ("görüldü", "Okul Müdürü", "OAB-FR", "md. 14/7", "Beyan"),
    "E03": ("Öğretmenler Kurulu", "gözlemci", "Alım", "OAB-FR", "Değişiklik kaydı"),
}


def test_ilk_uc_evrak_pilot_esdegerligi() -> None:
    """Pilot eşdeğerlik (tasarım §10.5; plan F1c kararları): belgenin bölümleri tablodaki sırayla,
    tablodaki her karşılık belgede; karşılığı olmayan her şablon alanının gerekçesi yazılı; alınmayan
    ibareler belgede yok. Uydurma veriyle."""
    kurulum = ge_ortak.tam_kurulum()
    for kod, satirlar in PILOT.items():
        belge, _ = gorev_evraki.KURUCULAR[kod](kurulum.donem)
        akis = _akis(belge)
        bolumler = [k for _s, k, _n in satirlar if k is not None and k[1:3] == ". "]
        assert _alt_basliklar(belge) == bolumler, kod
        for sablon, karsilik, gerekce in satirlar:
            if karsilik is None:
                assert gerekce.strip(), (kod, sablon)
            else:
                assert karsilik in akis, (kod, sablon, karsilik)
        for ibare in PILOT_ALINMAYANLAR[kod]:
            assert ibare not in akis, (kod, ibare)


def _gorev_evraki_metinleri() -> Iterator[str]:
    """E01-E03'ün kullanıcıya görünen sabit metinleri (yer tutucular sözlükteki biçimiyle)."""
    g = gorev_evraki
    yield from g.BELGE_ADLARI.values()
    yield from (tr_upper(ad) for ad in g.BELGE_ADLARI.values())
    yield from (g.E01_GIRIS, g.E02_GIRIS, *g.E01_BOLUMLER, *g.E02_BOLUMLER, *g.E03_BOLUMLER)
    yield from (*g.KONU_BILGI, *g.KONU_KARAR)
    yield from (g.GENEL_KURUL_SECIM_TARIHI, g.GENEL_KURUL_TARIHI, g.TOPLANTI, g.KATILAN)
    yield from (g.KARAR_DEFTERI, *g.E01_GOREV_BASLIKLARI, *g.E01_YEDEK_BASLIKLARI)
    yield g.BEYAN.format(suc="gg.aa.yyyy", tek="gg.aa.yyyy")
    yield from (g.BANKA_HESABI, g.MUSTEREK_IMZA, g.BANKAYA_BILDIRIM)
    yield g.MUSTEREK_IMZA_DEGERI.format(baskan="Ad SOYAD", muhasip="Ad SOYAD", yardimci="Ad SOYAD")
    yield from (g.AYLIK_TOPLANTI, g.AYLIK_BILDIRIM, g.AYLIK_BILDIRIM_DEGERI)
    yield from (g.KOORDINASYON, g.KOORDINASYON_DEGERI, *g.TEMSILCI_BASLIKLARI)
    yield from (*g.E02_UYE_BASLIKLARI, g.VELI_KOLTUGU, g.KURSIYER_KOLTUGU, g.VELI_YA_DA_KURSIYER)
    yield from (g.OGRETMEN_KOLTUGU, *g.KANALLAR.values(), g.ASIL, g.YEDEK)
    yield g.YEDEKTEN_CAGRILDI.format(gun="gg.aa.yyyy")
    yield from (*g.E02_PLAN_BASLIKLARI, g.ARA_DENETIM.format(sira="N"), g.ARA_RAPOR)
    yield from (g.NIHAI_RAPOR, g.NIHAI_RAPOR_DEGERI, *g.E03_BASLIKLARI)
    yield from (g.KARAR_NO_TARIH.format(no="N", tarih="gg.aa.yyyy"), g.BASKAN_SIFATIYLA)
    yield from (g.RPD_NOTU, g.UNVAN_DK_BASKANI, g.UNVAN_BILGI_BASKAN, g.UNVAN_SEKRETER)
    yield from (g.UNVAN_BIRLIK_BASKANI, g.UNVAN_TESLIM_ALAN, g.BOS)
    yield from (g.UYARI_TOPLANTI_YOK, g.UYARI_GOREV_BOS.format(gorev="<görev>"))
    yield from (g.UYARI_KOLTUK_BOS, g.UYARI_AD_OKUNAMADI, g.UYARI_PLAN_YOK, g.UYARI_MUDUR_ADI_YOK)
    yield g.UYARI_MUDUR_SOYADI
    yield g.KOD_GECERSIZ


def test_gorev_evraki_metinleri_sozlukte_yazilidir() -> None:
    """Kullanıcıya görünen her metin sözlüğe girer (sözlük §1 "Görev bölümü ve temsilci evrakı
    (F1c)"); kaydedilen dosya adlarının kalıbı ve örnekleri de (§3 "Kaydedilen dosya adı")."""
    sozluk = _depo_dosyasi("docs/sozluk.md")
    eksik = [metin for metin in _gorev_evraki_metinleri() if f'**"{metin}"**' not in sozluk]
    assert eksik == []
    for kod in gorev_evraki.KODLAR:
        assert f"`{gorev_evraki.DOSYA_ADI_KOKLERI[kod]}_gg.aa.yyyy.pdf`" in sozluk, kod
        ornek = gorev_evraki.dosya_adi(kod, date(2026, 11, 11), "DOCX")
        assert f"`{ornek}`" in sozluk, ornek


def test_e01_b_bolumunun_atfi_yalniz_gorev_dagilimina_baglidir() -> None:
    """KM-8 (tasarım §9.6 E01; §6.4 `uyelik.suc_engeli`, `yonetim_kurulu.tek_birlik`): beyan okul
    uygulamasıdır, Yönetmelik maddesine bağlanmaz. B bölümünün başlığında md. 12/3 atfı "görev
    dağılımı"nın hemen ardındadır; "beyan" sözcüğü atıftan sonra gelir (genel şablonun sırası)."""
    baslik = gorev_evraki.E01_BOLUMLER[1]
    assert baslik == "B. Görev dağılımı (md. 12/3) ve beyanlar"
    assert baslik.index("Görev dağılımı (md. 12/3)") < baslik.index("beyan")
    assert not re.search(r"beyan\w*\s*\(md\.", baslik)


def test_e01_aylik_bildirim_md_18_5_lafziyla() -> None:
    """Md. 18/5 bildirimin konusunu sayar (gelirler, bağışlar, yönetim kurulu kararlarıyla yapılan
    harcamalar): E01'in aylık bildirim satırı fıkranın lafzıdır, korpus metninde birebir geçer."""
    korpus = _depo_dosyasi("docs/mevzuat/meb-okul-aile-birligi-yonetmeligi.md")
    assert f"(5) {gorev_evraki.AYLIK_BILDIRIM_DEGERI}" in korpus
    for konu in ("elde edilen gelirler", "alınan bağışlar", "yönetim kurulu kararlarıyla"):
        assert konu in gorev_evraki.AYLIK_BILDIRIM_DEGERI


# ============================================================ veli adlı belge (F2 8. adım; R9, U15)


def _adli_metin(icerik: bytes, bicim: str) -> str:
    """Verilen dosyanın metni (adların gerçekten dosyada olduğunu görmek için)."""
    from shared import xlsx

    if bicim == "PDF":
        return " ".join(s.extract_text() or "" for s in PdfReader(io.BytesIO(icerik)).pages)
    if bicim == "DOCX":
        return " ".join(cizici_.govde_metin_akisi(cizici_.ac(icerik)))
    return " ".join(xlsx.metin_akisi(icerik))


@pytest.mark.parametrize("kod", ["E07", "E08"])
def test_veli_adli_belge_saklanmaz(kod: str) -> None:
    """Plan F2 §2 kapısı ve §7 U15 (tasarım §5.2.8, §9.6 E07-E08; R9). İçerik 9. adımın gerçek
    kurucusundandır (teslim çizelgesi, veli adlı katılım cetveli); veli listesi uydurmadır.

    Veli adlı kip yalnız program yöneticisinin tek isteğinde üretilir ve verilir: dosya hiçbir yerde
    saklanmaz (dosya deposunda eki yok), içerik JSON'u saklanmaz (yalnız özet, satır sayısı ve tarih),
    yeniden basılmaz; aynı işlemde `BASIM` satırı (kod ve dosyanın sha256'sı) ve erişim günlüğünün
    `VELI_LISTESI_CIKTISI` satırı (dosyanın sha256'sı ve satır sayısı) yazılır; iz ve günlük veli adı
    taşımaz. Her biçimde (E07: Word, PDF; E08: ayrıca Excel). Arşiv paketine girmemesi F4'te
    (arşiv paketiyle) sınanır."""
    from apps.oab.hatalar import EvrakIcerigiSaklanmaz
    from apps.okul.models import AccessKind, Attachment

    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    for bicim in gke.ADLI_BICIMLER[kod]:
        son = _son_seq()
        cikti = gke.adli_uret_ve_ver(kod, kurul, bicim=bicim)
        ozet = hashlib.sha256(cikti.icerik).hexdigest()
        metin = "".join(_adli_metin(cikti.icerik, bicim).split())
        assert all("".join(veli.split()) in metin for veli, _ in gke_ortak.VELILER), bicim

        kayit = GeneratedDocument.objects.get(pk=cikti.kayit.pk)
        assert (kayit.doc_type, kayit.variant, kayit.personal_list) == (kod, "ADLI", True)
        assert (kayit.content_json, kayit.row_count) == ("", len(gke_ortak.VELILER))
        assert kayit.formats == [bicim] and kayit.status == DocumentStatus.GECERLI
        assert not Attachment.objects.filter(
            owner_type="oab.GeneratedDocument", owner_id=str(kayit.pk)
        ).exists()
        with pytest.raises(EvrakIcerigiSaklanmaz):
            evrak_servisi.yeniden_ciz(kayit)

        yeni = list(AuditTrail.objects.filter(seq__gt=son).order_by("seq"))
        basim = [s for s in yeni if s.action == AuditAction.BASIM]
        assert len(basim) == 1
        assert basim[0].values == {"kod": [None, kod], "sha256": [None, ozet]}
        assert (basim[0].model, basim[0].object_id) == ("oab.GeneralAssembly", str(kurul.pk))
        gunluk = AccessLog.objects.order_by("-pk").first()
        assert gunluk is not None
        assert (gunluk.kind, gunluk.document_sha256, gunluk.row_count) == (
            AccessKind.VELI_LISTESI_CIKTISI,
            ozet,
            len(gke_ortak.VELILER),
        )
        assert (gunluk.model, gunluk.object_id) == ("oab.GeneralAssembly", str(kurul.pk))
        izler = "".join(f"{s.values}{s.changed_fields}{s.object_id}" for s in yeni)
        for veli, _ in gke_ortak.VELILER:
            for parca in veli.split():
                assert parca not in izler, parca
    # Her basım yeni sürümdür; öncekinin yerini alır, silinmez.
    assert GeneratedDocument.objects.filter(doc_type=kod).count() == len(gke.ADLI_BICIMLER[kod])
    assert AccessLog.objects.filter(kind="VELI_LISTESI_CIKTISI").count() == len(
        gke.ADLI_BICIMLER[kod]
    )
    assert denetim_izi.zinciri_dogrula() == []


# ============================================================ Genel kurul evrakı I (F2 9. adım)
#
# E05, E06, E07, E08 ve E64 (plan F2 §8 9. adım; §4.1, §7 U14-U18, U34; tasarım §9.3, §9.6). Kurulum
# `genel_kurul_evraki_ortak.kurulum` (kol başına çağrılmış genel kurul; uydurma birlik, veli listesi
# ve okul kartı). Adlar UYDURMADIR.

_BIRINCI = "BIRINCI"
_IKINCI = "IKINCI"
_KISISIZ = "KISISIZ"


def _gk_uret(
    kod: str,
    kurul: Any,
    *,
    toplanti: str = "",
    kip: str = "",
    secim: gke.Secim | None = None,
    rol: AccountRole = AccountRole.SEKRETER,
) -> tuple[GeneratedDocument, tuple[str, ...]]:
    """Kişisiz üretim (`genel_kurul_evraki.uret`), verilen rolün hesabından."""
    if secim is not None:
        kip, toplanti = secim.kip, secim.toplanti
    with o.rol_olarak(rol):
        sonuc = gke.uret(kod, kurul, kip=kip, toplanti=toplanti)
    return sonuc.kayit, sonuc.uyarilar


def _gk_secim(kod: str) -> gke.Secim:
    """Kodun öntanımlı kipi ve toplantısı (U14, U34); kip ve toplantı almayan belgede boş."""
    if kod in gke.KIPLI_KODLAR:
        return gke.Secim(kip=_KISISIZ)
    if kod in gke.TOPLANTILI_KODLAR:
        return gke.Secim(toplanti=_BIRINCI)
    return gke.Secim()


def _gk_ureten(kod: str) -> AccountRole:
    """Kodun üreten rolü (tasarım §9.6 "Üreten"): E12 ve E14 yalnız program yöneticisinin."""
    return AccountRole.YONETICI if kod in ("E12", "E14") else AccountRole.SEKRETER


def _ureten_rol(kol: str) -> AccountRole:
    """E05'i üreten rol, kola göre (tasarım §9.6 E05 "Üreten")."""
    if kol in gke.MUDUR_KOLLARI:
        return AccountRole.MUDUR
    if kol == gke.KOL_DK_14_5:
        return AccountRole.DENETLEME_KURULU
    if kol == gke.KOL_BASKAN_13_8:
        return AccountRole.BASKAN
    return AccountRole.SEKRETER


def _yk_gorevli_adi(kurul: Any, role: str) -> str:
    (uyelik,) = [u for u in selectors.gorevdeki_asillar(kurul.term, "YK") if u.role == role]
    return _ad(uyelik)


def _kisi_adlari() -> list[str]:
    """Programdaki bütün kişi adları (birlik kişileri, veliler, personel, müdür): kişisiz belgede
    hiçbiri bulunmaz."""
    adlar = [str(k.first_name) for k in OabPerson.objects.all()]
    adlar += [str(k.last_name) for k in OabPerson.objects.all()]
    adlar += [str(s.full_name) for s in ParentRoster.objects.all()]
    adlar += [f"{p.first_name} {p.last_name}" for p in Personnel.objects.all()]
    adlar.append(ge_ortak.MUDUR)
    return [ad for ad in adlar if ad.strip()]


def _adsiz(metin: str) -> None:
    buyuk = tr_upper(" ".join(metin.split()))
    for ad in _kisi_adlari():
        assert tr_upper(" ".join(ad.split())) not in buyuk, ad


def _bilgi(belge: evrak.Belge) -> dict[str, str]:
    """Belgenin ilk "Konu | Bilgi" tablosu."""
    return _satirlar(_tablo(belge, "Konu"))


def _mudur_bloklari(belge: evrak.Belge) -> list[str]:
    return [gorev for _ad_, gorev in _imza_sahipleri(belge) if "Müdür" in gorev]


def _kabul_e05() -> None:
    """Tasarım §9.6 E05 "Kabul örneği" (yönetim kurulunun olağan çağrısı): yeter sayı 64 paketten
    (16 × 4); ikinci toplantının günü (≤ 30 gün); olağan gündem tohumdan (md. 11/1-e ve f dahil);
    duyuru kanıtı bölümü üç kanalın günüyle ve elle doldurulan görev unvanı sütunuyla, kişi adı yok;
    çağrı kararı bağlı değilse karar tarihi ve
    sayısı "………" (S1 (a)); imza Birlik Başkanı (Yönetim Kurulu adına) + Sekreter, "Görüldü — Okul
    Müdürü (md. 27/1)"; kişisel veri dipnotu; konum cümlesi ve taslak ibaresi yok. Word ve PDF
    saklanır."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    kayit, uyarilar = _gk_uret("E05", kurul, toplanti=_BIRINCI)
    assert kayit.formats == ["DOCX", "PDF"] and len(list(kayit.ekler())) == 2
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert belge.antet.alt_birim == "Okul-Aile Birliği"
    assert belge.bloklar[0] == evrak.Baslik(
        gke.BELGE_ADLARI["E05"], alt="Olağan genel kurul — Birinci toplantı"
    )
    bilgi = _bilgi(belge)
    assert bilgi[gke.SATIR_TUR] == "Olağan genel kurul"
    assert bilgi[gke.SATIR_CAGIRAN] == "Yönetim kurulu (md. 9/1)"
    assert bilgi[gke.SATIR_KARAR] == gorev_evraki.BOS and gke.UYARI_KARAR_YOK in uyarilar
    assert bilgi[gke.SATIR_YER] == gke_ortak.YER
    assert bilgi[gke.SATIR_BIRINCI] == "20.10.2026 10:00"
    assert bilgi[gke.SATIR_IKINCI] == "05.11.2026 10:00"
    assert bilgi[gke.SATIR_YETER_SAYI] == (
        "64 (yönetim ve denetleme kurullarının asıl ve yedek üye sayısı 16 × 4)"
    )
    assert gke.SATIR_CAGRI_NEDENI not in bilgi
    akis = _akis(belge)
    gun = kural("genel_kurul.ilan_en_az_gun")
    assert gke.ILAN_CUMLESI.format(gun=gun) in akis and f"en az {gun} gün" in akis
    otuz = kural("genel_kurul.ikinci_toplanti_en_gec_gun")
    assert gke.IKINCI_TOPLANTI_CUMLESI.format(gun=otuz) in akis
    (gundem,) = _bolum_tablolari(belge, gke.GUNDEM_BOLUMU)
    basliklar = list(
        AgendaItem.objects.filter(assembly=kurul).order_by("order").values_list("title", flat=True)
    )
    assert [s[1] for s in gundem.satirlar] == basliklar and len(basliklar) == 13
    (kanit,) = _bolum_tablolari(belge, gke.KANIT_BOLUMU)
    assert kanit.basliklar == ("Kanal", "Gün", "Yapanın görev unvanı (ad yazılmaz)")
    assert kanit.satirlar == (
        (gke.KANAL_ELDEN, "05.10.2026", ""),
        (gke.KANAL_PANO, "05.10.2026", ""),
        (gke.KANAL_INTERNET, "05.10.2026", ""),
        (gke.KANIT_ILAN_GUNU, "05.10.2026", ""),
    )
    assert _imza_sahipleri(belge) == [
        (_yk_gorevli_adi(kurul, "BASKAN"), gke.UNVAN_YK_ADINA_BASKAN),
        (_yk_gorevli_adi(kurul, "SEKRETER"), gke.UNVAN_SEKRETER),
        (gke_ortak.MUDUR_IMZASI, gke.UNVAN_GORULDU_E05),
    ]
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar)
    assert evrak.KDT not in akis and evrak.TASLAK_IBARESI not in akis


def _kabul_e06() -> None:
    """Tasarım §9.6 E06: kişisiz (hiçbir kişi adı yok; çağrı nedeni de yok), imza "Okul-Aile Birliği
    Yönetim Kurulu" (U17); PDF saklanır, web sayfası saklanmaz, kayıtlı içerikten çizilir (U18) ve
    aynı metni taşır; ikinci toplantı ilanı aynı kodla (U34)."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    kayit, _ = _gk_uret("E06", kurul, toplanti=_BIRINCI)
    assert kayit.formats == ["HTML", "PDF"]
    assert [ek.mime for ek in kayit.ekler()] == ["application/pdf"]
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _imza_sahipleri(belge) == [("", "Okul-Aile Birliği Yönetim Kurulu")]
    assert not any(isinstance(b, evrak.Dipnot) for b in belge.bloklar)
    bilgi = _bilgi(belge)
    assert list(bilgi) == [gke.SATIR_YER, gke.SATIR_BIRINCI, gke.SATIR_IKINCI]
    sayfa = evrak.web_html_ciz(belge)
    assert _duz("".join(_ayristir(sayfa).govde)) == _duz("".join(evrak.metin_akisi(belge)))
    _adsiz(_akis(belge))
    _adsiz(sayfa)
    # İkinci toplantının ilanı (birinci toplantıda yeter sayı sağlanamadı): ayrı geçerli satır.
    gke_ortak.birinci_toplantida_yetersiz(kurul)
    ikinci, _ = _gk_uret("E06", kurul, toplanti=_IKINCI)
    belge2 = evrak_servisi.yeniden_ciz(ikinci)
    assert belge2.bloklar[0] == evrak.Baslik(
        gke.BELGE_ADLARI["E06"], alt="Olağan genel kurul — İkinci toplantı"
    )
    assert list(_bilgi(belge2)) == [gke.SATIR_YER, gke.SATIR_IKINCI]
    assert gke.IKINCI_DAVET_GIRISI.format(tur="olağan") in _akis(belge2)
    assert GeneratedDocument.objects.get(pk=kayit.pk).status == DocumentStatus.GECERLI


def _kabul_e07() -> None:
    """Tasarım §9.6 E07 ve plan F2 §7 U14: kişisiz kip — davet mektubu ("Sayın Veli"), sınıf başına
    adet, kısa aydınlatma paragrafı ve tam metnin (E04) yeri; imza çağırana göre kurum adı (U17);
    saklanır, veli adı yok. Adlı kip — sınıf teslim çizelgesi: sınıf başına sayfa, veli adları,
    teslim eden sınıf rehber öğretmeni, kişisel veri dipnotu; saklanmaz (R9)."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    kayit, uyarilar = _gk_uret("E07", kurul, kip=_KISISIZ)
    assert (kayit.variant, kayit.formats, kayit.personal_list) == (_KISISIZ, ["DOCX", "PDF"], False)
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert evrak.Paragraf(gke.SAYIN_VELI) in belge.bloklar
    (adet,) = _bolum_tablolari(belge, gke.E07_ADET_BOLUMU)
    assert adet.satirlar == (("5-A", "1", "", ""), ("5-B", "1", "", ""), (gke.TOPLAM, "2", "", ""))
    assert any(isinstance(b, evrak.SayfaSonu) for b in belge.bloklar)
    assert _imza_sahipleri(belge) == [("", "Okul-Aile Birliği Yönetim Kurulu")]
    akis = _akis(belge)
    for metin in (gke.VELI_AYDINLATMA_AMACI, gke.AYDINLATMA_HAKLARINIZ, gke.E07_TAM_METIN_YERI):
        assert metin in akis
    assert f"Veri sorumlusu: {gke_ortak.VERI_SORUMLUSU}" in akis
    assert uyarilar == ()
    _adsiz(akis)
    # Adlı kip: yalnız program yöneticisi, tek istekte; içerik modeli kurucudan.
    cikti = gke.adli_uret_ve_ver("E07", kurul, bicim="PDF")
    assert (cikti.kayit.variant, cikti.kayit.row_count) == ("ADLI", 2)
    adli = gke.e07_adli_belgesi(kurul, "").belge
    assert _alt_basliklar(adli) == ["Sınıf: 5-A", "Sınıf: 5-B"]
    assert [s[1] for t in _bolum_tablolari(adli, "Sınıf: 5-A") for s in t.satirlar] == [
        "Pelinsu UYDURMAKAYA"
    ]
    assert set(_imza_sahipleri(adli)) == {("", gke.UNVAN_REHBER)}
    assert adli.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    assert GeneratedDocument.objects.get(pk=kayit.pk).status == DocumentStatus.GECERLI


def _kabul_e08() -> None:
    """Tasarım §9.6 E08 ve plan F2 §7 U14, U16: sınıf başına ayrı sayfa, sınıf sonunda boş satırlar,
    öğretmenler ve idareciler, diğer katılanlar, gözlemci bölümü boş satırlı; T.C. kimlik no ve telefon
    sütunu yok. Boş satırlı kip hiçbir ad taşımaz (parafta da) ve saklanır. Cetvel toplantıdan önce
    basılır: genel kurul yapılmadıkça (ilanlı; birinci toplantıda yeter sayı sağlanamayınca da) sonuç
    belli değildir, parafın iki kolu koşuluyla ve adsız basılır (tasarım §9.6 E08: yapıldıysa Divan
    Başkanı + Kâtip, yapılamadıysa Birlik Başkanı + Sekreter). Adlı kip veli ve personel adlarıyla ("Ad
    SOYAD"), genel kurul yapıldıktan sonra Divan Başkanı + Kâtip parafıyla."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    gke_ortak.personel_ekle()
    kayit, _ = _gk_uret("E08", kurul, kip=_KISISIZ)
    assert kayit.formats == ["DOCX", "PDF", "XLSX"] and kayit.personal_list is False
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _alt_basliklar(belge) == [
        "Veliler — sınıf: 5-A",
        "Veliler — sınıf: 5-B",
        gke.PERSONEL_BOLUMU,
        gke.DIGER_BOLUMU,
        gke.GOZLEMCI_BOLUMU,
    ]
    sayfa_sonlari = sum(isinstance(b, evrak.SayfaSonu) for b in belge.bloklar)
    assert sayfa_sonlari == len(_alt_basliklar(belge)) - 1
    (sinif,) = _bolum_tablolari(belge, "Veliler — sınıf: 5-A")
    assert len(sinif.satirlar) == 1 + gke.EK_BOS_SATIR
    assert all(s[1] == "" and s[2] == "5-A" for s in sinif.satirlar)
    (personel,) = _bolum_tablolari(belge, gke.PERSONEL_BOLUMU)
    assert len(personel.satirlar) == len(gke_ortak.PERSONEL) + gke.EK_BOS_SATIR
    (gozlemci,) = _bolum_tablolari(belge, gke.GOZLEMCI_BOLUMU)
    assert gozlemci.basliklar == gke.GOZLEMCI_BASLIKLARI
    assert len(gozlemci.satirlar) == gke.GOZLEMCI_SATIRI
    iki_kol = {
        ("", "Divan Başkanı — toplantı yapıldıysa"),
        ("", "Kâtip — toplantı yapıldıysa"),
        ("", "Birlik Başkanı — toplantı yapılamadıysa"),
        ("", "Sekreter — toplantı yapılamadıysa"),
    }
    assert set(_imza_sahipleri(belge)) == iki_kol
    basliklar = " ".join(
        h for b in belge.bloklar if isinstance(b, evrak.Tablo) for h in b.basliklar
    )
    for yok in ("T.C.", "kimlik", "Telefon", "telefon"):
        assert yok not in basliklar
    assert not any(isinstance(b, evrak.Dipnot) for b in belge.bloklar)
    _adsiz(_akis(belge))
    # Adlı kip ilanlı genel kurulda: adlar var, parafta ad yok (sonuç belli değil).
    adli = gke.e08_adli_belgesi(kurul, "")
    assert set(_imza_sahipleri(adli.belge)) == iki_kol
    # Birinci toplantıda yeter sayı sağlanamayınca ikinci toplantı beklenir: sonuç yine belli değil.
    yetersiz = gke_ortak.birinci_toplantida_yetersiz(kurul)
    for cetvel in (
        gke.e08_belgesi(yetersiz, gke.Secim(kip=_KISISIZ))[0],
        gke.e08_adli_belgesi(yetersiz, "").belge,
    ):
        assert set(_imza_sahipleri(cetvel)) == iki_kol
    # Adlı kip, genel kurul ikinci toplantıda yapıldıktan sonra (paraf divanın).
    kurul = gke_ortak.ikinci_toplantida_yapilmis(yetersiz)
    adli = gke.e08_adli_belgesi(kurul, "")
    assert adli.satir_sayisi == len(gke_ortak.VELILER)
    akis = _akis(adli.belge)
    assert "Pelinsu UYDURMAKAYA" in akis and "Sınamanur KURGUCU" in akis
    (personel,) = _bolum_tablolari(adli.belge, gke.PERSONEL_BOLUMU)
    assert ("1", "Denemeli YAPAYCI", "İdareci", "") in personel.satirlar
    divan = gk.kurulun_divani(kurul)
    assert set(_imza_sahipleri(adli.belge)) == {
        (_ad(divan[0]), gke.UNVAN_DIVAN_BASKANI),
        (_ad(divan[1]), gke.UNVAN_KATIP),
    }
    assert adli.belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)


def _kabul_e64() -> None:
    """Tasarım §9.6 E64: kişisiz, yalnız sayılar (KE-21): dondurulmuş yeter sayı, mevcut, katılan, türe
    göre dağılım, gözlemci ("katılım sayısına eklenmez", md. 9/5); sağlandıysa Divan Başkanı + Kâtip,
    yalnız unvan (ad yok), "Görüldü" yok; kişisel veri dipnotu yok. Saklanır ve yeniden basılır."""
    kurul = gke_ortak.birinci_toplantida_yapilmis(gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK)))
    kayit, uyarilar = _gk_uret("E64", kurul, toplanti=_BIRINCI)
    assert kayit.formats == ["DOCX", "PDF"] and kayit.content_json and uyarilar == ()
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert belge.bloklar[0] == evrak.Baslik(
        gke.BELGE_ADLARI["E64"], alt="Olağan genel kurul — Toplantı yeter sayısı sağlandı"
    )
    assert _bilgi(belge) == {
        gke.SATIR_TUR: "Olağan genel kurul",
        gke.SATIR_TOPLANTI: "Birinci toplantı",
        gke.SATIR_GUN_YER: f"20.10.2026 10:00 · {gke_ortak.YER}",
        gke.SATIR_MEVCUT: "120",
        gke.SATIR_YETER_SAYI: (
            "64 (yönetim ve denetleme kurullarının asıl ve yedek üye sayısı 16 × 4)"
        ),
        gke.SATIR_KATILAN: "70",
        gke.SATIR_GOZLEMCI: "6",
        gke.SATIR_SONUC: gke.SONUC_SAGLANDI,
    }
    (dagilim,) = _bolum_tablolari(belge, gke.DAGILIM_BOLUMU)
    assert dagilim.satirlar == (
        ("Veli ve kursiyer", "60"),
        ("Öğretmen", "8"),
        ("İdareci", "2"),
        ("Hayırsever", "0"),
        ("Diğer", "0"),
    )
    assert _imza_sahipleri(belge) == [("", gke.UNVAN_DIVAN_BASKANI), ("", gke.UNVAN_KATIP)]
    assert not any(isinstance(b, evrak.Dipnot) for b in belge.bloklar)
    akis = _akis(belge)
    _adsiz(akis)
    assert "örüldü" not in akis


GENEL_KURUL_EVRAKI_KABULLERI = {
    "E05": _kabul_e05,
    "E06": _kabul_e06,
    "E07": _kabul_e07,
    "E08": _kabul_e08,
    "E64": _kabul_e64,
}


def _gk_kurulu(kod: str, *, uzun: bool = False) -> Any:
    """Kodun eşdeğerlik ve sayfa bütçesi kurulumu (konusu): yönetim kurulunun çağrısıyla ilan edilmiş
    olağan genel kurul ve uydurma personel; E64'te birinci toplantıda yeter sayı sağlanamamış. 10.
    adımın belgelerinde (E09-E13) birinci toplantıda yapılmış ve tutanağı yazılmış genel kurul (E11 ve
    E12'de yönetim kurulu ibra edilmemiş; S4 (a)); E14'te okul planı girilmiş açık dönem."""
    if kod == "E14":
        return gke_ortak.takvimli_donem(uzun=uzun)
    if kod in GENEL_KURUL_EVRAKI_II:
        kurul_ = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=kod in ("E11", "E12"), uzun=uzun)
        gke_ortak.personel_ekle()
        return kurul_
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK, uzun=uzun))
    gke_ortak.personel_ekle()
    if kod == "E64":
        kurul = gke_ortak.birinci_toplantida_yetersiz(kurul)
    return kurul


def _yinelenen_basliklari_ayikla(pdf: str, beklenen: str, belge: evrak.Belge) -> str:
    """PDF'te sayfaya bölünen tablonun başlık satırı yeni sayfada yinelenir (WeasyPrint `thead`):
    yinelenen başlık altlık gibi baskının işidir, içerik değildir; modelin akışında olmayan yerde
    duran başlık satırı ayıklanır (iki metin boşluksuz)."""
    basliklar = sorted(
        {_duz("".join(b.basliklar)) for b in belge.bloklar if isinstance(b, evrak.Tablo)},
        key=len,
        reverse=True,
    )
    sonuc: list[str] = []
    i = j = 0
    while j < len(pdf):
        if i < len(beklenen) and pdf[j] == beklenen[i]:
            sonuc.append(pdf[j])
            i += 1
            j += 1
            continue
        yinelenen = next((b for b in basliklar if b and pdf.startswith(b, j)), None)
        if yinelenen is None:
            sonuc.append(pdf[j:])
            break
        j += len(yinelenen)
    return "".join(sonuc)


def _gk_docx_pdf_esdegerligi(kod: str) -> None:
    """`test_docx_pdf_icerik_esdegerligi`'nin genel kurul kolu: saklanan Word ve PDF (E06'da PDF ve web
    sayfası; E08 ve E14'te ayrıca Excel) aynı metin akışını taşır; Türkçe büyük harf `tr_upper`'dandır.
    Sayfaya bölünen tablonun PDF'te yinelenen başlık satırı ayıklanır (`_yinelenen_basliklari_ayikla`).
    Resmî yazının (E12) başlığı yoktur (RYUE: konu satırı)."""
    from shared import xlsx

    kurul = _gk_kurulu(kod)
    kayit, _ = _gk_uret(kod, kurul, secim=_gk_secim(kod), rol=_gk_ureten(kod))
    belge = evrak_servisi.yeniden_ciz(kayit)
    beklenen = _duz("".join(evrak.metin_akisi(belge)))
    pdf_metni = _metin(_dosya(kayit, "PDF"))
    assert re.search(rf"OAB Defteri · {kod} · Sayfa 1\s*/\s*\d", pdf_metni)
    pdf_akisi = _duz(_ALTLIK.sub("", pdf_metni))
    assert _yinelenen_basliklari_ayikla(pdf_akisi, beklenen, belge) == beklenen
    if kod == "E14":
        assert [ek.mime for ek in kayit.ekler()] == ["application/pdf"]
    elif kod == "E06":
        assert _duz("".join(_ayristir(evrak.web_html_ciz(belge)).govde)) == beklenen
    else:
        docx = _dosya(kayit, "DOCX")
        assert _duz("".join(cizici_.govde_metin_akisi(cizici_.ac(docx)))) == beklenen
        with zipfile.ZipFile(io.BytesIO(docx)) as arsiv:
            govde = arsiv.read("word/document.xml").decode("utf-8")
        assert "<w:caps" not in govde and "<w:smallCaps" not in govde
    if kod in ("E08", "E14"):
        assert _duz("".join(xlsx.metin_akisi(evrak.xlsx_ciz(belge)))) == beklenen
    if kod != "E12":
        assert _duz(tr_upper(gke.BELGE_ADLARI[kod])) in _duz(pdf_metni)


#: Sayfa bütçesi, gerçek uzunlukta uydurma veriyle (`uzun=True`; uzun ad, okul adı ve ilçe; E08'de ve
#: adlı E07'de ayrıca 34 velili iki sınıf). Tasarım sınırı yazmaz (§9.1-4); ölçülen değerler: E05 iki
#: sayfa, E06 bir, E07'nin kişisiz kipi üç (iki sayfalık davet mektubu ve sınıf adetleri), E64 iki.
#: E08 ve adlı E07'nin her bölümü kendi sayfasında başlar: bütçe bölüm başına iki sayfadır (ölçülen:
#: kalabalık sınıf iki, öteki bölümler bir).
GENEL_KURUL_EVRAKI_SAYFA_SINIRI: dict[str, int] = {"E05": 2, "E06": 1, "E07": 3, "E64": 2}
BOLUM_SAYFA_SINIRI = 2
#: Kalabalık sınıfın uydurma veli sayısı (sayfa bütçesi).
_KALABALIK_SINIF = 34


def _gk_sayfa_butcesi(kod: str) -> None:
    kurul = _gk_kurulu(kod, uzun=True)
    gko.veli_aktar(
        [
            (f"Ayşegül Nurhayat {sira:02d} Varsayımcıgil Örnekçioğlu", sinif)
            for sinif in ("6-A", "7-B")
            for sira in range(_KALABALIK_SINIF)
        ],
        ad="kalabalik.xlsx",
    )
    if kod == "E08":
        for belge in (
            gke.e08_belgesi(kurul, gke.Secim(kip=_KISISIZ))[0],
            gke.e08_adli_belgesi(kurul, "").belge,
        ):
            bolum = len(_alt_basliklar(belge))
            sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(belge))).pages)
            assert bolum <= sayfa <= bolum * BOLUM_SAYFA_SINIRI, (bolum, sayfa)
        return
    belge, _ = gke.KURUCULAR[kod](kurul, _gk_secim(kod))
    sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(belge))).pages)
    assert 1 <= sayfa <= GENEL_KURUL_EVRAKI_SAYFA_SINIRI[kod], (kod, sayfa)
    if kod == "E07":
        adli = gke.e07_adli_belgesi(kurul, "").belge
        bolum = len([b for b in adli.bloklar if isinstance(b, evrak.AltBaslik)])
        sayfa = len(PdfReader(io.BytesIO(evrak.pdf_ciz(adli))).pages)
        assert bolum <= sayfa <= bolum * BOLUM_SAYFA_SINIRI, (bolum, sayfa)


def _gk_mudur_bloklari(parametre: str) -> None:
    """`test_mudur_bloklari_yalniz_93_tablosunda`'nın genel kurul kolu (tasarım §9.3; MB-3, KE-10):
    E05'te müdürün çağrısında "Okul Müdürü" (çağıran ve imzacı), öteki kollarda "Görüldü — Okul Müdürü
    (md. 27/1)"; E06, E07, E08'de müdür bloğu yok; E64'te yalnız sağlanamadıysa ve müdür çağırmadıysa
    "Görüldü" (§9.3 "Görüldü (müdür çağırmadıysa)"); ikinci toplantının E64'ünde yok."""
    kod, _, kol = parametre.partition("_")
    if kod == "E05":
        kurul = gke_ortak.kurulum(kol)
        kayit, _ = _gk_uret("E05", kurul, toplanti=_BIRINCI, rol=_ureten_rol(kol))
        belge = evrak_servisi.yeniden_ciz(kayit)
        mudurun = kol in gke.MUDUR_KOLLARI
        assert _mudur_bloklari(belge) == (
            [gke.UNVAN_OKUL_MUDURU] if mudurun else [gke.UNVAN_GORULDU_E05]
        )
        assert ("örüldü" in _akis(belge)) is not mudurun
        return
    mudurun = parametre == "E64_saglanamadi_mudur"
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_MUDUR_9_6 if mudurun else gke.KOL_YK))
    secim = _gk_secim(kod)
    if parametre == "E64_saglandi":
        kurul = gke_ortak.birinci_toplantida_yapilmis(kurul)
    elif parametre.startswith("E64_saglanamadi"):
        kurul = gke_ortak.birinci_toplantida_yetersiz(kurul)
    elif parametre == "E64_ikinci":
        kurul = gke_ortak.ikinci_toplantida_yapilmis(gke_ortak.birinci_toplantida_yetersiz(kurul))
        secim = gke.Secim(toplanti=_IKINCI)
    kayit, _ = _gk_uret(kod, kurul, secim=secim)
    belge = evrak_servisi.yeniden_ciz(kayit)
    beklenen = [gke.UNVAN_GORULDU] if parametre == "E64_saglanamadi" else []
    assert _mudur_bloklari(belge) == beklenen
    assert ("örüldü" in _akis(belge)) is bool(beklenen)
    assert "Teslim alan" not in _akis(belge)


def _genel_kurul_evraki_tckn(kod: str, tckn: str) -> None:
    """`test_tckn_hicbir_belgede_yok`'un genel kurul kolu: numara belgenin okuduğu ama basmadığı serbest
    metne yazılır — kapanacak dönemin yönetim kurulu üyeliklerinin ve genel kurulun kendi üyelik
    kayıtlarının (aday, seçilen, divan; E09-E13 bunları basar) dayanak notu; Word, PDF (E06'da web
    sayfası), içerik JSON'u ve veli adlı kipin dosyaları aranır."""
    kurul = _gk_kurulu(kod)
    donem = kurul if kod == "E14" else kurul.term
    assert donem is not None
    uyelikler_ = list(selectors.gorevdeki_asillar(donem, "YK"))
    if kod != "E14":
        uyelikler_ += OrganMembership.objects.filter(
            assembly=kurul, status__in=(MembershipStatus.ADAY, MembershipStatus.SECILDI)
        )
        if kod in GENEL_KURUL_EVRAKI_II:
            assert any(u.assembly_id == kurul.pk for u in uyelikler_), kod
    for uyelik in uyelikler_:
        uyelikler.update_membership(uyelik, evidence_note=f"Uydurma dayanak {tckn}")
    kayit, _ = _gk_uret(kod, kurul, secim=_gk_secim(kod), rol=_gk_ureten(kod))
    belge = evrak_servisi.yeniden_ciz(kayit)
    metinler = [_metin(_dosya(kayit, "PDF")), kayit.content_json]
    if kod == "E14":
        from shared import xlsx

        metinler.append(" ".join(xlsx.metin_akisi(evrak.xlsx_ciz(belge))))
    elif kod == "E06":
        metinler.append(evrak.web_html_ciz(belge))
    else:
        metinler.append(" ".join(cizici_.govde_metin_akisi(cizici_.ac(_dosya(kayit, "DOCX")))))
    if kod in gke.ADLI_KODLAR:
        for bicim in gke.ADLI_BICIMLER[kod]:
            cikti = gke.adli_uret_ve_ver(kod, kurul, bicim=bicim)
            metinler.append(_adli_metin(cikti.icerik, bicim))
    # Boşluklar silinince katılım cetvelinin art arda sıra numaraları ("1 2 … 10") 11 haneli desene
    # benzer: boşluksuz metinde numaranın kendisi aranır.
    for parca in metinler:
        assert not _ONBIR_HANE.search(parca)
        assert tckn not in _duz(parca)


@pytest.mark.parametrize("kol", list(gke.KOLLAR))
def test_e05_imza_cagirana_gore(kol: str) -> None:
    """Tasarım §9.6 E05 "İmza" ve §9.3 (MB-3): yönetim kurulunun çağrısında Birlik Başkanı (Yönetim
    Kurulu adına) + Sekreter ve "Görüldü — Okul Müdürü (md. 27/1)"; başkanın md. 13/8 çağrısında Birlik
    Başkanı ve "Görüldü"; müdürün çağrısında (md. 9/1, 9/6, 13/8, 25/2) Okul Müdürü, "Görüldü" bloğu
    yok, antet okulun; Denetleme Kurulunun çağrısında (md. 14/5) asıl üyeleri ve "Görüldü"; üyelerin
    başvurusunda (KE-11) Birlik Başkanı ve "Görüldü", basım uyarısıyla. Üreten de çağırana göredir
    (`E05_URETENLER`, çağrının sahiplikli eylemi): kolun izinli rolleri dışındaki HER rol üretemez, ret
    hiçbir kayıt yazmaz."""
    kurul = gke_ortak.kurulum(kol)
    rol = _ureten_rol(kol)
    izinli = {AccountRole.YONETICI, AccountRole.SEKRETER} if rol == AccountRole.SEKRETER else {rol}
    for yabanci in AccountRole:
        if yabanci in izinli:
            continue
        with o.rol_olarak(yabanci), pytest.raises(RolYetkisiz):
            gke.uret("E05", kurul, toplanti=_BIRINCI)
    assert not GeneratedDocument.objects.exists()
    if rol == AccountRole.SEKRETER:
        # Yönetim kurulunun çağrısında ve üyelerin başvurusunda program yöneticisi de üretir.
        _gk_uret("E05", kurul, toplanti=_BIRINCI, rol=AccountRole.YONETICI)
    kayit, uyarilar = _gk_uret("E05", kurul, toplanti=_BIRINCI, rol=rol)
    belge = evrak_servisi.yeniden_ciz(kayit)
    sahipler = _imza_sahipleri(belge)
    gorulmus = (gke_ortak.MUDUR_IMZASI, gke.UNVAN_GORULDU_E05)
    if kol in gke.MUDUR_KOLLARI:
        assert sahipler == [(gke_ortak.MUDUR_IMZASI, gke.UNVAN_OKUL_MUDURU)]
        assert belge.antet.alt_birim == ""
    elif kol == gke.KOL_YK:
        assert sahipler == [
            (_yk_gorevli_adi(kurul, "BASKAN"), gke.UNVAN_YK_ADINA_BASKAN),
            (_yk_gorevli_adi(kurul, "SEKRETER"), gke.UNVAN_SEKRETER),
            gorulmus,
        ]
    elif kol == gke.KOL_DK_14_5:
        assert kurul.term is not None
        asillar = selectors.gorevdeki_asillar(kurul.term, "DK")
        assert sorted(sahipler[:-1]) == sorted(
            (_ad(u), gke.UNVAN_DK_BASKANI if u.role == "BASKAN" else gke.UNVAN_DK_UYESI)
            for u in asillar
        )
        assert sahipler[0][1] == gke.UNVAN_DK_BASKANI and sahipler[-1] == gorulmus
    else:
        assert sahipler == [(_yk_gorevli_adi(kurul, "BASKAN"), gke.UNVAN_BIRLIK_BASKANI), gorulmus]
    assert (gke.UYARI_YUZDE_10 in uyarilar) is (kol == gke.KOL_YUZDE_10)
    if kol not in gke.MUDUR_KOLLARI:
        assert belge.antet.alt_birim == "Okul-Aile Birliği"
    assert _bilgi(belge)[gke.SATIR_CAGIRAN] == gke.CAGIRAN_METINLERI.get(kol, gke.CAGIRAN_YK_OLAGAN)


@pytest.mark.parametrize("kod", ["E06", "E07"])
@pytest.mark.parametrize("kol", list(gke.KOLLAR))
def test_duyuru_ve_davet_imzasi_cagirana_gore(kod: str, kol: str) -> None:
    """Plan F2 §7 U17 (öneri adı): E06 ve E07'nin kişisiz imzası çağırana göre kurum adıdır — yönetim
    kurulunun çağrısında "Okul-Aile Birliği Yönetim Kurulu", müdürün çağrısında (yeni okul dahil, S5
    (ii)) "Okul Müdürlüğü" (antet okulun), Denetleme Kurulunun çağrısında "Okul-Aile Birliği Denetleme
    Kurulu", başkanın md. 13/8 çağrısında ve üyelerin başvurusunda (KE-11) "Okul-Aile Birliği
    Başkanı". Kişi adı yoktur."""
    kurul = gke_ortak.kurulum(kol)
    kayit, _ = _gk_uret(kod, kurul, secim=_gk_secim(kod))
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _imza_sahipleri(belge) == [("", gke.KURUM_ADLARI[kol])]
    assert (belge.antet.alt_birim == "") is (kol in gke.MUDUR_KOLLARI)
    _adsiz(_akis(belge))


@pytest.mark.parametrize(
    "durum",
    [
        "E07_kisisiz_adli",
        "E08_bos_adli",
        "E64_birinci_ikinci",
        "E05_birinci_ikinci",
        "E06_birinci_ikinci",
    ],
)
def test_ayni_kodlu_belgeler_birbirini_gecersiz_kilmaz(durum: str) -> None:
    """Plan F2 §7 U34 (öneri adı): aynı genel kurulun aynı kodlu belgeleri kip ve toplantı başına ayrı
    geçerli satırdır — adlı E07/E08 kişisiz davetin ve boş satırlı cetvelin yerini almaz; ikinci
    toplantının E64'ü birinci toplantının "sağlanamadı" tespitinin, ikinci toplantı ilanının E05/E06'sı
    birinci ilanınkinin yerini almaz."""
    kod = durum[:3]
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    if kod in gke.ADLI_KODLAR:
        ilk, _ = _gk_uret(kod, kurul, kip=_KISISIZ)
        sonraki = gke.adli_uret_ve_ver(kod, kurul, bicim="PDF").kayit
    else:
        kurul = gke_ortak.birinci_toplantida_yetersiz(kurul)
        ilk, _ = _gk_uret(kod, kurul, toplanti=_BIRINCI)
        if kod == "E64":
            kurul = gke_ortak.ikinci_toplantida_yapilmis(kurul)
        sonraki, _ = _gk_uret(kod, kurul, toplanti=_IKINCI)
    durumlar = dict(GeneratedDocument.objects.values_list("pk", "status"))
    assert durumlar[ilk.pk] == durumlar[sonraki.pk] == DocumentStatus.GECERLI
    assert {k.pk for k in gke.evrak_listesi(kurul)} >= {ilk.pk, sonraki.pk}


@pytest.mark.parametrize("durum", ["E05_yeni_okul", "E05_olaganustu"])
def test_mudur_yazilari_yalniz_mudur_hesabindan(durum: str) -> None:
    """Tasarım §9.3 "Kendi yazıları" (M-11; ¹): yeni açılan okulun genel kurul daveti (md. 9/1) ve
    müdürün olağanüstü çağrısı (md. 9/6) müdürün yazısıdır; E05'i yalnız müdürün hesabı üretir.
    Program yöneticisi, yönetim kurulu rolleri ve Denetleme Kurulu üretemez; ret hiçbir kayıt
    yazmaz."""
    kol = gke.KOL_MUDUR_9_1 if durum == "E05_yeni_okul" else gke.KOL_MUDUR_9_6
    kurul = gke_ortak.kurulum(kol)
    for rol in (
        AccountRole.YONETICI,
        AccountRole.SEKRETER,
        AccountRole.BASKAN,
        AccountRole.MUHASIP,
        AccountRole.DENETLEME_KURULU,
    ):
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            gke.uret("E05", kurul, toplanti=_BIRINCI)
    assert not GeneratedDocument.objects.exists()
    with o.rol_olarak(AccountRole.MUDUR) as mudur:
        kayit = gke.uret("E05", kurul, toplanti=_BIRINCI).kayit
    assert kayit.generated_by_id == mudur.pk
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _bilgi(belge)[gke.SATIR_CAGIRAN] == gke.CAGIRAN_METINLERI[kol]


def test_duyurularda_kisi_adi_yok() -> None:
    """Tasarım §9.1-5, §9.6 E06: duyuru (ilan panosu ve internet sayfası) hiçbir kişi adı taşımaz —
    birlik kişileri, veliler, personel ve okul müdürü; başkanınki de. Olağanüstü genel kurulun çağrı
    nedeni serbest metindir, E06'ya basılmaz (E05'te basılır). Her iki toplantının duyurusu; içerik,
    PDF ve web sayfası."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_BASKAN_13_8))
    gke_ortak.personel_ekle()
    gke_ortak.birinci_toplantida_yetersiz(kurul)
    for toplanti in (_BIRINCI, _IKINCI):
        kayit, _ = _gk_uret("E06", kurul, toplanti=toplanti)
        belge = evrak_servisi.yeniden_ciz(kayit)
        for metin in (_akis(belge), evrak.web_html_ciz(belge), _metin(_dosya(kayit, "PDF"))):
            _adsiz(metin)
            assert _duz(gko.OLAGANUSTU_NEDEN) not in _duz(metin)
        assert gke.GUNDEME_BAGLILIK in _akis(belge)
    e05, _ = _gk_uret("E05", kurul, toplanti=_BIRINCI, rol=AccountRole.BASKAN)
    assert gko.OLAGANUSTU_NEDEN in _akis(evrak_servisi.yeniden_ciz(e05))


def test_kisa_aydinlatma_paragrafi() -> None:
    """Tasarım §9.1-5 (KM-6) `ev::test_kisa_aydinlatma_paragrafi[E07]`: kişisel verinin toplandığı
    belgede (elden yazılı davet) kısa aydınlatma paragrafı ve tam metnin (Kişisel veri aydınlatma
    metni, E04) yeri vardır. Paragrafın cümleleri kullanıcının 08.11.2026'da onayladığı veli metninden
    BİREBİR alınır (ön yüzdeki metinle aynı); veri sorumlusu okul kartından, boşken "………" ve basım
    uyarısı (E04'ün sert kuralı S6 (iv) davete uygulanmaz)."""
    from apps.okul.tests.test_on_yuz_sozlugu import _depo_dosyasi as on_yuz_dosyasi
    from apps.okul.tests.test_on_yuz_sozlugu import _sabitler

    on_yuz = _sabitler(on_yuz_dosyasi("frontend/src/modules/kisiler/metinler.ts"))
    assert on_yuz["VELI_AYDINLATMA_AMACI"] == gke.VELI_AYDINLATMA_AMACI
    assert on_yuz["AYDINLATMA_HAKLARINIZ"] == gke.AYDINLATMA_HAKLARINIZ
    assert on_yuz["AYDINLATMA_VERI_SORUMLUSU_ETIKETI"] == gke.AYDINLATMA_VERI_SORUMLUSU_ETIKETI
    assert gke.BELGE_ADLARI["E04"] in gke.E07_TAM_METIN_YERI

    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK))
    kayit, uyarilar = _gk_uret("E07", kurul, kip=_KISISIZ)
    bloklar = list(evrak_servisi.yeniden_ciz(kayit).bloklar)
    bas = bloklar.index(evrak.AltBaslik(gke.E07_AYDINLATMA_BASLIGI))
    assert bloklar[bas + 1 : bas + 5] == [
        evrak.Paragraf(gke.VELI_AYDINLATMA_AMACI),
        evrak.Paragraf(f"Veri sorumlusu: {gke_ortak.VERI_SORUMLUSU}"),
        evrak.Paragraf(gke.AYDINLATMA_HAKLARINIZ),
        evrak.Paragraf(gke.E07_TAM_METIN_YERI),
    ]
    assert isinstance(bloklar[bas + 5], evrak.Imza) and uyarilar == ()
    SchoolConfig.objects.filter(pk=SchoolConfig.SINGLETON_PK).update(data_controller_text="")
    kayit, uyarilar = _gk_uret("E07", kurul, kip=_KISISIZ)
    assert (
        evrak.Paragraf(f"Veri sorumlusu: {gorev_evraki.BOS}")
        in evrak_servisi.yeniden_ciz(kayit).bloklar
    )
    assert uyarilar == (gke.UYARI_VERI_SORUMLUSU_YOK,)


@pytest.mark.parametrize(("ogrenci", "yeter_sayi", "carpan"), [(99, 32, 2), (100, 64, 4)])
def test_e64_yeter_sayi_mevcuda_gore(ogrenci: int, yeter_sayi: int, carpan: int) -> None:
    """Tasarım §9.6 E64 "99 öğrenci → 32, 100 → 64" (md. 9/2): yeter sayı ilanda kural paketinden
    dondurulur (kodda sabit yok), E64 dondurulmuş değeri basar. Sağlanamadıysa imza Birlik Başkanı +
    Sekreter + "Görüldü — Okul Müdürü" (KE-10; kişisiz: yalnız unvan) ve ikinci toplantının günü
    basılır."""
    kurul = gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK, ogrenci=ogrenci))
    assert kurul.quorum_required == yeter_sayi
    kurul = gke_ortak.birinci_toplantida_yetersiz(kurul)
    kayit, _ = _gk_uret("E64", kurul, toplanti=_BIRINCI)
    belge = evrak_servisi.yeniden_ciz(kayit)
    bilgi = _bilgi(belge)
    assert bilgi[gke.SATIR_YETER_SAYI] == (
        f"{yeter_sayi} (yönetim ve denetleme kurullarının asıl ve yedek üye sayısı 16 × {carpan})"
    )
    assert bilgi[gke.SATIR_MEVCUT] == str(ogrenci) and bilgi[gke.SATIR_KATILAN] == "10"
    assert bilgi[gke.SATIR_SONUC] == gke.SONUC_SAGLANAMADI
    assert bilgi[gke.SATIR_IKINCI] == "05.11.2026 10:00"
    assert _imza_sahipleri(belge) == [
        ("", gke.UNVAN_BIRLIK_BASKANI),
        ("", gke.UNVAN_SEKRETER),
        ("", gke.UNVAN_GORULDU),
    ]
    _adsiz(_akis(belge))


def test_genel_kurul_evraki_i_konum_cumlesi_ve_taslak_ibaresi_yok() -> None:
    """Plan F2 §4.1: konum cümlesi F2'de yalnız E13'tedir; KDT ve taslak ibaresi hiçbir F2 belgesinde
    yoktur. Kişisel veri dipnotu yalnız kişi adı taşıyan belgelerde (E05, adlı E07 ve E08); E64
    kişisizdir (KE-21)."""
    kurul = gke_ortak.birinci_toplantida_yetersiz(gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK)))
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, _gk_secim(kod))[0]
        for kod in ("E05", "E06", "E07", "E08", "E64")
    }
    belgeler["E07_adli"] = gke.e07_adli_belgesi(kurul, "").belge
    belgeler["E08_adli"] = gke.e08_adli_belgesi(kurul, "").belge
    for ad, belge in belgeler.items():
        akis = _akis(belge)
        assert not any(isinstance(b, evrak.KonumCumlesi) for b in belge.bloklar), ad
        assert evrak.KDT not in akis and evrak.TASLAK_IBARESI not in akis, ad
        dipnotlu = evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU) in belge.bloklar
        assert dipnotlu is (ad in ("E05", "E07_adli", "E08_adli")), ad


def test_genel_kurul_evraki_i_punto_ve_ad_soyad() -> None:
    """Tasarım §9.1-8 ve RYUE md. 7/1, 17/2 (F1c emsali `test_e63_punto_alt_siniri`,
    `test_imza_ad_soyad_bicimi`): E05-E08 ve E64'te (iki kipiyle) yazı alanında 9 puntodan küçük metin
    yok, altlık 12 punto; imza bloğundaki her ad "Ad SOYAD" biçiminde (soyadı `tr_upper`)."""
    from shared import docx as cizici
    from shared.tests.test_evrak import pdf_yazi_boyutlari

    kurul = gke_ortak.birinci_toplantida_yetersiz(gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_YK)))
    gke_ortak.personel_ekle()
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, _gk_secim(kod))[0]
        for kod in ("E05", "E06", "E07", "E08", "E64")
    }
    belgeler.update(
        {f"{kod}_adli": gke.ADLI_KURUCULAR[kod](kurul, "").belge for kod in gke.ADLI_KODLAR}
    )
    adlar = 0
    for ad, belge in belgeler.items():
        parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
        kucukler = [(m, b) for _s, m, b in parcalar if b < cizici.EN_KUCUK_PUNTO]
        assert parcalar and kucukler == [], (ad, kucukler)
        altlik = {b for _s, m, b in parcalar if m.startswith("OAB Defteri ·")}
        assert altlik == {float(cizici.ALTLIK_PUNTO)}, (ad, altlik)
        for imza_adi, _gorev in _imza_sahipleri(belge):
            if imza_adi in ("", gorev_evraki.BOS):
                continue
            *ilkler, soyad = imza_adi.split(" ")
            assert soyad == tr_upper(soyad) and ilkler, (ad, imza_adi)
            assert all(p[:1] == tr_upper(p[:1]) for p in ilkler), (ad, imza_adi)
            adlar += 1
    assert adlar >= len(("E05 başkan", "E05 sekreter", "E05 müdür"))


# ============================================================ Genel kurul evrakı II (F2 10. adım)
#
# E09, E10, E11, E12, E13 ve E14 (plan F2 §8 10. adım; §4.1, §7 U20-U22, KE-19, S4, S11; tasarım §9.1,
# §9.3, §9.5, §9.6). E04 dört alt metnin kullanıcı onayından sonra yazılır (plan F2 §9 S8 (i)); onun
# testleri (`test_e04_dort_alt_metin_veri_sorumlusu_bossa_basilmaz` ve kodun öteki parametreleri) o
# işle eklenir. Kurulum `genel_kurul_evraki_ortak.yapilmis_tutanakli` (birinci toplantıda yapılmış,
# tutanağı yazılmış olağan genel kurul) ve `takvimli_donem`. Adlar UYDURMADIR.

#: 10. adımın belgeleri (E04 hariç).
GENEL_KURUL_EVRAKI_II = ("E09", "E10", "E11", "E12", "E13", "E14")


def _tablo_satirlari(belge: evrak.Belge, bolum: str) -> list[tuple[str, ...]]:
    return [satir for tablo in _bolum_tablolari(belge, bolum) for satir in tablo.satirlar]


def _secilen_adlari(kurul: Any, organ: str) -> list[str]:
    return [_ad(u) for u in gke._kurul_secilenleri(kurul, organ)]


def _kabul_e09() -> None:
    """Tasarım §9.6 E09 "Kabul örneği": Denetleme Kurulunun öğretmen koltukları oylamaya girmez (bilgi
    satırı; sayılar kural paketinden); yönetim kurulu adayı veli, kursiyer ya da hayırseverdir (kişi
    türüyle); aday listesi ile E10'un seçim sonucu aynı kişilerdir (seçilmeyen aday listede kalır,
    seçim sonucunda yoktur). İmza Divan Başkanı + Kâtip; kişisel veri dipnotu; Word ve PDF saklanır."""
    kurul = gke_ortak.yapilmis_tutanakli()
    kayit, _ = _gk_uret("E09", kurul)
    assert kayit.formats == ["DOCX", "PDF"] and len(list(kayit.ekler())) == 2
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _alt_basliklar(belge) == [gke.YK_ADAY_BOLUMU, gke.DK_ADAY_BOLUMU]
    yk = _tablo_satirlari(belge, gke.YK_ADAY_BOLUMU)
    assert {s[3] for s in yk} <= {"Veli", "Kursiyer", "Hayırsever"}
    koltuklar = kural("denetleme_kurulu.koltuklar")["OGRETMEN"]
    bilgi = gke.DK_OGRETMEN_BILGISI.format(asil=koltuklar["ASIL"], yedek=koltuklar["YEDEK"])
    assert evrak.Paragraf(bilgi) in belge.bloklar
    dk = _tablo_satirlari(belge, gke.DK_ADAY_BOLUMU)
    assert [s[2] for s in dk] == ["Asıl", "Yedek"] and "Öğretmen" not in {s[3] for s in dk}
    # Tek kaynak: seçilenler aday listesindedir; seçilmeyen aday yalnız aday listesindedir.
    e10 = gke.e10_belgesi(kurul, gke.Secim())[0]
    secilenler = [s[1] for s in _tablo_satirlari(e10, gke.E10_BOLUMLER[4])]
    secilenler = [ad for ad in secilenler if ad in {s[1] for s in yk + dk}]
    assert set(_secilen_adlari(kurul, "YK")) < {s[1] for s in yk}
    assert set(_secilen_adlari(kurul, "DK")) == {s[1] for s in dk}
    assert len(secilenler) == gke_ortak.YK_ASIL + gke_ortak.YK_YEDEK + 2
    divan = gk.kurulun_divani(kurul)
    assert _imza_sahipleri(belge) == [
        (_ad(divan[0]), gke.UNVAN_DIVAN_BASKANI),
        (_ad(divan[1]), gke.UNVAN_KATIP),
    ]
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)


def _kabul_e10() -> None:
    """Tasarım §9.6 E10: yönetim kurulu ve Denetleme Kurulunun ibrası ayrı oylama satırıdır; "ibra
    edilmedi" E11 ve E12'yi açar (S4 (a)), ibra edildiyse ikisi üretilmez; bütçe "görüşüldü" yazar,
    tutar basılmaz (U22); gündem değişikliğinin oylaması satır olarak. İmza Divan Başkanı + Kâtip ve
    "Görüldü — Okul Müdürü (md. 27/1)"; tarih genel kurulun yapıldığı gün."""
    kurul = gke_ortak.yapilmis_tutanakli()
    kayit, _ = _gk_uret("E10", kurul)
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert [b for b in _alt_basliklar(belge) if b[1:3] == ". "] == list(gke.E10_BOLUMLER)
    (ibra,) = _bolum_tablolari(belge, gke.E10_BOLUMLER[3])
    assert ibra.basliklar == gke.IBRA_BASLIKLARI
    assert ibra.satirlar == (
        (gke.KURUL_YK, "İbra edildi", "12", "3", "18"),
        (gke.KURUL_DK, "İbra edildi", "12", "3", "18"),
    )
    (gundem, okuyanlar) = _bolum_tablolari(belge, gke.E10_BOLUMLER[2])
    sonuclar = {satir[1]: satir[2] for satir in gundem.satirlar}
    assert sonuclar["Tahmini bütçenin görüşülmesi"] == gke.SONUC_BUTCE
    assert sonuclar[
        "İhtiyaçların giderilmesi için yönetim kurulunun yetkilendirilmesi"
    ] == gke.SONUC_METNI.format(
        sonuc=gke.SONUC_KABUL.format(oylar="kabul 60, ret 5"), metin=gke_ortak.YETKILENDIRME_METNI
    )
    assert _tablo_satirlari(belge, gke.GUNDEM_DEGISIKLIGI_BOLUMU) == [
        (gke_ortak.EKLENEN_MADDE, gke.DEGISIKLIK_EKLENDI, "kabul 50, ret 10")
    ]
    assert {s[0] for s in okuyanlar.satirlar} == {
        gke.SATIR_YK_RAPORU,
        gke.SATIR_DK_RAPORU_OKUYAN,
        gke.SATIR_BUTCEYI_SUNAN,
    }
    akis = _akis(belge)
    assert " TL" not in akis and "hesapları ibra edilmedi;" not in akis
    divan = gk.kurulun_divani(kurul)
    imza = next(b for b in belge.bloklar if isinstance(b, evrak.Imza))
    assert imza.tarih == "20.10.2026"
    assert _imza_sahipleri(belge) == [
        (_ad(divan[0]), gke.UNVAN_DIVAN_BASKANI),
        (_ad(divan[1]), gke.UNVAN_KATIP),
        (gke_ortak.MUDUR_IMZASI, gke.UNVAN_GORULDU_E05),
    ]
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)
    # İbra edildi: yan akışın belgeleri üretilmez, hiçbir kayıt yazılmaz.
    once = GeneratedDocument.objects.count()
    for kod in ("E11", "E12"):
        with pytest.raises(ValueError, match=re.escape(gke.IBRA_EDILMEDIKCE_URETILMEZ)):
            _gk_uret(kod, kurul, rol=AccountRole.YONETICI)
    assert GeneratedDocument.objects.count() == once


def _kabul_e11() -> None:
    """Tasarım §9.6 E11: evrak tek tek listelidir (tutanağın notunun her satırı), tarih genel kurulun
    yapıldığı gündür. İmza Divan Başkanı + Kâtip; teslim alan yeni yönetim kurulu ve Denetleme Kurulu
    adına birer üye (ad elle yazılır; olağan genel kurul ikisini de seçer, giriş cümlesi aynı
    kaynaktan). E12'nin ekidir, okul dışına gider: kişisel veri dipnotu yok (10. adımın kararı).
    Word ve PDF saklanır."""
    kurul = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True)
    kayit, _ = _gk_uret("E11", kurul)
    assert kayit.formats == ["DOCX", "PDF"]
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _tablo_satirlari(belge, gke.E11_LISTE_BOLUMU) == [
        ("1", "Uydurma gider belgeleri dosyası (Ocak-Mart)"),
        ("2", "Uydurma banka dekontları (12 adet)"),
    ]
    imza = next(b for b in belge.bloklar if isinstance(b, evrak.Imza))
    assert imza.tarih == "20.10.2026"
    divan = gk.kurulun_divani(kurul)
    assert _imza_sahipleri(belge) == [
        (_ad(divan[0]), gke.UNVAN_DIVAN_BASKANI),
        (_ad(divan[1]), gke.UNVAN_KATIP),
        ("", gke.UNVAN_TESLIM_ALAN_YK),
        ("", gke.UNVAN_TESLIM_ALAN_YENI_DK),
    ]
    assert gke.TESLIM_ALANLAR[(True, True)] in _akis(belge)
    assert not any(isinstance(b, evrak.Dipnot) for b in belge.bloklar)


def _kabul_e12() -> None:
    """Tasarım §9.6 E12: RYUE — sayı ("………", okulun yazışma sisteminde verilir; U20), gg.aa.yyyy
    tarih, konu, muhatap (kullanıcı kararı S11 (a): "… KAYMAKAMLIĞINA" ve altında "(İlçe Millî Eğitim
    Müdürlüğü)"), ek E11. İmza Yönetim Kurulu adına Birlik Başkanı (yeni) + Okul Müdürü; taslağı
    program yöneticisi üretir (KE-19). Okul dışına gider: kişisel veri dipnotu yok."""
    kurul = gke_ortak.gorev_bolumlu(gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True))
    kayit, uyarilar = _gk_uret("E12", kurul, rol=AccountRole.YONETICI)
    assert kayit.formats == ["DOCX", "PDF"] and uyarilar == (gke.UYARI_SAYI,)
    belge = evrak_servisi.yeniden_ciz(kayit)
    bas = belge.bloklar[0]
    assert isinstance(bas, evrak.ResmiYazi)
    assert (bas.sayi, bas.konu) == (gorev_evraki.BOS, gke.E12_KONU)
    assert re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", bas.tarih)
    assert (bas.muhatap, bas.birim) == ("ÖRNEK İLÇE KAYMAKAMLIĞINA", "İlçe Millî Eğitim Müdürlüğü")
    assert belge.bloklar[-1] == evrak.Ekler((gke.BELGE_ADLARI["E11"],))
    assert gke.TESLIM_ALANLAR[(True, True)] in _akis(belge)
    baskan = gke._yeni_gorevli(kurul, "BASKAN")
    assert baskan is not None
    assert _imza_sahipleri(belge) == [
        (_ad(baskan), gke.UNVAN_YK_ADINA_BASKAN),
        (gke_ortak.MUDUR_IMZASI, gke.UNVAN_OKUL_MUDURU),
    ]
    assert not any(isinstance(b, evrak.Dipnot) for b in belge.bloklar)


def _kabul_e13() -> None:
    """Tasarım §9.6 E13: seçilenler E10 ile aynı kayıtlar; sonraki adımlar tarihli (görev bölümü
    kural paketinin günüyle — en çok bir hafta —, banka imza yetkisi, TEFBİS girişi); bildirim okul
    uygulamasıdır, "Yönetmelik gereği" denmez (MB-11); konum cümlesi TFB. İmza Birlik Başkanı (yeni) +
    Sekreter (yeni) ve "Teslim alan: Okul Müdürü"."""
    kurul = gke_ortak.gorev_bolumlu(gke_ortak.yapilmis_tutanakli())
    kayit, uyarilar = _gk_uret("E13", kurul)
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert uyarilar == ()
    yk = [s[1] for s in _tablo_satirlari(belge, gke.E13_BOLUMLER[1])]
    dk = [s[1] for s in _tablo_satirlari(belge, gke.E13_BOLUMLER[2])]
    e10 = gke.e10_belgesi(kurul, gke.Secim())[0]
    e10_secilenler = [s[1] for s in _tablo_satirlari(e10, gke.E10_BOLUMLER[4])]
    assert yk + dk == [ad for ad in e10_secilenler if ad in yk + dk]
    assert yk == _secilen_adlari(kurul, "YK") and dk == _secilen_adlari(kurul, "DK")
    sonraki = {s[0]: (s[1], s[2]) for s in _tablo_satirlari(belge, gke.E13_BOLUMLER[3])}
    yedi = kural("yonetim_kurulu.gorev_bolumu_gun")
    son = date(2026, 10, 20) + timedelta(days=yedi)
    assert sonraki[gke.IS_YK_GOREV_BOLUMU] == (f"en geç {son:%d.%m.%Y}", "md. 12/3")
    assert sonraki[gke.IS_DK_GOREV_BOLUMU][1] == "md. 14/1"
    assert sonraki[gke.IS_BANKA] == (gke.GOREV_BOLUMUNDEN_SONRA, "md. 18/2")
    assert sonraki[gke.IS_TEFBIS] == (gke.GENEL_KURULDAN_SONRA, "md. 23/5")
    assert gke.IS_MEM_YAZISI not in sonraki
    akis = _akis(belge)
    assert "Yönetmelik gereği" not in akis and "gereği" not in akis
    baskan, sekreter = gke._yeni_gorevli(kurul, "BASKAN"), gke._yeni_gorevli(kurul, "SEKRETER")
    assert baskan is not None and sekreter is not None
    assert _imza_sahipleri(belge) == [
        (_ad(baskan), gke.UNVAN_BIRLIK_BASKANI),
        (_ad(sekreter), gke.UNVAN_SEKRETER),
        (gke_ortak.MUDUR_IMZASI, gorev_evraki.UNVAN_TESLIM_ALAN),
    ]
    assert belge.bloklar[-1] == evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU)


def _kabul_e14() -> None:
    """Tasarım §9.6 E14: her süre kuralı satırı kural kimliği ve atıf taşır; okul planı satırları ayrı
    bölümde; Ekim sonu, 15 gün, 30 gün, 7 gün ve arz bedelinin 10'u ve 20'si doğru (değerler kural
    paketinden). Kişisiz, imzasız; PDF saklanır, Excel kayıtlı içerikten çizilir (U18)."""
    from apps.oab.kurallar.erisim import atif_metni

    donem = gke_ortak.takvimli_donem()
    gko.planla()  # dönemi kapatacak olağan genel kurul: birinci toplantı 20.10.2026
    kayit, uyarilar = _gk_uret("E14", donem, rol=AccountRole.YONETICI)
    assert kayit.formats == ["PDF", "XLSX"] and uyarilar == ()
    assert [ek.mime for ek in kayit.ekler()] == ["application/pdf"]
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert _alt_basliklar(belge) == list(gke.E14_BOLUMLER)
    satirlar = _tablo_satirlari(belge, gke.E14_BOLUMLER[0])
    kurallar = {s[2]: s for s in satirlar}
    assert set(kurallar) == set(gke.E14_KURALLARI)
    for kural_id, satir in kurallar.items():
        assert satir[3] == atif_metni(kural_kaydi(kural_id)), kural_id
    yedi = kural("yonetim_kurulu.gorev_bolumu_gun")
    son = gko.DONEM_BASI + timedelta(days=yedi)
    assert kurallar["yonetim_kurulu.gorev_bolumu_gun"][0] == f"en geç {son:%d.%m.%Y}"
    on_bes = kural("genel_kurul.ilan_en_az_gun")
    ilan = gko.BIRINCI_GUN - timedelta(days=on_bes)
    assert kurallar["genel_kurul.ilan_en_az_gun"][0] == f"en geç {ilan:%d.%m.%Y}"
    assert kurallar["genel_kurul.olagan_son_ay"][0] == "en geç 31.10.2026"
    otuz = kural("genel_kurul.ikinci_toplanti_en_gec_gun")
    ikinci = gko.BIRINCI_GUN + timedelta(days=otuz)
    assert kurallar["genel_kurul.ikinci_toplanti_en_gec_gun"][0] == f"en geç {ikinci:%d.%m.%Y}"
    for kural_id in ("arz_bedeli.sozlesme_vade_gunu", "arz_bedeli.yonetmelik_vade_gunu"):
        assert kurallar[kural_id][0] == gke.ARZ_GUNU.format(gun=kural(kural_id))
    assert kural("arz_bedeli.sozlesme_vade_gunu") < kural("arz_bedeli.yonetmelik_vade_gunu")
    plan = _tablo_satirlari(belge, gke.E14_BOLUMLER[1])
    assert {s[2] for s in plan} == {gke.KAYNAK_DERS_YILI, gke.KAYNAK_DONEM}
    assert (gke_ortak.YK_TOPLANTI_GUNU, gke.IS_YK_TOPLANTISI, gke.KAYNAK_DONEM) in plan
    assert ("15.01.2026", gke.IS_DK_DENETIMI.format(sira=1), gke.KAYNAK_DONEM) in plan
    assert not any(isinstance(b, evrak.Imza | evrak.Dipnot) for b in belge.bloklar)
    _adsiz(_akis(belge))


GENEL_KURUL_EVRAKI_KABULLERI.update(
    {
        "E09": _kabul_e09,
        "E10": _kabul_e10,
        "E11": _kabul_e11,
        "E12": _kabul_e12,
        "E13": _kabul_e13,
        "E14": _kabul_e14,
    }
)
GENEL_KURUL_EVRAKI_SAYFA_SINIRI.update({"E09": 2, "E10": 3, "E11": 1, "E12": 1, "E13": 2, "E14": 2})


def _gk_ii_belgesi(kod: str, *, mudurun: bool = False) -> tuple[Any, evrak.Belge]:
    """10. adımın belgesi kaydedilerek üretilir (yeniden çizilir): E11 ve E12'de yönetim kurulu ibra
    edilmemiş; `mudurun`: müdürün olağanüstü çağrısıyla (md. 9/6) yapılmış genel kurul."""
    konu: OabTerm | GeneralAssembly
    if kod == "E14":
        konu = gke_ortak.takvimli_donem()
    elif mudurun:
        konu = gke_ortak.tutanakli(
            gke_ortak.birinci_toplantida_yapilmis(
                gke_ortak.ilanli(gke_ortak.kurulum(gke.KOL_MUDUR_9_6))
            )
        )
    else:
        konu = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=kod in ("E11", "E12"))
    kayit, _ = _gk_uret(kod, konu, rol=_gk_ureten(kod))
    return konu, evrak_servisi.yeniden_ciz(kayit)


#: §9.3 tablosunda 10. adımın belgelerinin müdür blokları (MB-15): E10'da "Görüldü" (müdür
#: çağırmadıysa), E12 okul idaresinin resmî yazısı (imza Okul Müdürü), E13 "Teslim alan"; E09, E11 ve
#: E14'te müdür bloğu yok.
MUDUR_BLOKLARI_II: dict[str, list[str]] = {
    "E09": [],
    "E10": ["Görüldü — Okul Müdürü (md. 27/1)"],
    "E10_mudur": [],
    "E11": [],
    "E12": ["Okul Müdürü"],
    "E13": ["Teslim alan: Okul Müdürü"],
    "E14": [],
}


def _gk_ii_mudur_bloklari(parametre: str) -> None:
    """`test_mudur_bloklari_yalniz_93_tablosunda`'nın 10. adım kolu (tasarım §9.3; MB-15)."""
    _, belge = _gk_ii_belgesi(parametre[:3], mudurun=parametre == "E10_mudur")
    assert _mudur_bloklari(belge) == MUDUR_BLOKLARI_II[parametre]
    assert ("örüldü" in _akis(belge)) is (parametre == "E10")


@pytest.mark.parametrize("kod", ["E13"])
def test_konum_tfb(kod: str) -> None:
    """Tasarım §9.2 TFB (md. 23/5): konum cümlesi gövdede, imza bloğunun hemen üstünde, 9 punto; metni
    BİREBİR; altlıkta konum cümlesi yok. F2'de TFB yalnız E13'tedir (plan F2 §4.1)."""
    from shared.tests.test_evrak import pdf_yazi_boyutlari

    _, belge = _gk_ii_belgesi(kod)
    (konum,) = [i for i, b in enumerate(belge.bloklar) if isinstance(b, evrak.KonumCumlesi)]
    assert belge.bloklar[konum] == evrak.KonumCumlesi(evrak.TFB)
    assert isinstance(belge.bloklar[konum + 1], evrak.Imza)
    tasarim = _bolum("### 9.2 ", "### 9.3 ")
    assert f'| **TFB** | "{evrak.TFB}" |' in tasarim
    parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
    konum_satirlari = {b for _s, m, b in parcalar if len(m) > 30 and m in evrak.TFB}
    assert konum_satirlari == {float(cizici_.KONUM_PUNTO)}
    altlik = [m for _s, m, _b in parcalar if m.startswith("OAB Defteri ·")]
    assert altlik and all(_ALTLIK.fullmatch(m) for m in altlik)


def test_genel_kurul_evraki_ii_konum_cumlesi_dipnot_ve_taslak_ibaresi() -> None:
    """Plan F2 §4.1: konum cümlesi F2'de yalnız E13'tedir (TFB), öteki belgelerde (E05-E12, E14, E64)
    yoktur; KDT ve taslak ibaresi hiçbir F2 belgesinde yoktur. Kişisel veri dipnotu kişi adı taşıyan iç
    belgelerdedir (E09, E10, E13); E12 okul dışına giden resmî yazıdır, E11 onun ekidir ve onunla okul
    dışına gider ("okul dışına verilmez" basılmaz; 10. adımın kararı), E14 kişisizdir."""
    kurul = gke_ortak.gorev_bolumlu(gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True))
    assert kurul.term is not None
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, _gk_secim(kod))[0]
        for kod in ("E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E64")
    }
    belgeler["E14"] = gke.e14_belgesi(kurul.term, gke.Secim())[0]
    assert set(belgeler) == set(gke.KURUCULAR)
    for kod, belge in belgeler.items():
        akis = _akis(belge)
        konumlar = [b for b in belge.bloklar if isinstance(b, evrak.KonumCumlesi)]
        assert konumlar == ([evrak.KonumCumlesi(evrak.TFB)] if kod == "E13" else []), kod
        assert evrak.KDT not in akis and evrak.TASLAK_IBARESI not in akis, kod
        if kod in GENEL_KURUL_EVRAKI_II:
            dipnotlu = evrak.Dipnot(evrak.KISISEL_VERI_DIPNOTU) in belge.bloklar
            assert dipnotlu is (kod in ("E09", "E10", "E13")), kod


@pytest.mark.parametrize("kod", ["E12"])
def test_resmi_yazi_ryue_unsurlari(kod: str) -> None:
    """Tasarım §9.1-4, §10.5 (RYUE md. 10-18): okul antedi (md. 10/3; birlik satırı yok), belgenin ilk
    bloğu sayı, tarih (gg.aa.yyyy, md. 12), konu (sonunda noktalama yok, md. 13/1) ve muhatap (büyük
    harf, birim parantezde — md. 14/2, 14/5; kullanıcı kararı S11 (a)); metin paragrafları 1,25 cm
    içeriden ve iki yana yaslı (md. 16/4), son paragraf üst makama "arz ederim" (md. 16/12); imza
    bölümünde ad "Ad SOYAD" (md. 17/2), üst unvan (Okul Müdürü) sağda (md. 17/11); "Ek:" imzadan sonra,
    tek ekte yanında (md. 18/1-2). Word'de paragraf girintisi ve imzanın sağ hücresi sınanır."""
    kurul = gke_ortak.gorev_bolumlu(gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True))
    kayit, _ = _gk_uret(kod, kurul, rol=AccountRole.YONETICI)
    belge = evrak_servisi.yeniden_ciz(kayit)
    okul = SchoolConfig.load()
    assert belge.antet == evrak.okul_anteti(okul_adi=okul.school_name, ilce=okul.district)
    bas = belge.bloklar[0]
    assert isinstance(bas, evrak.ResmiYazi)
    assert bas.sayi and re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", bas.tarih)
    assert bas.konu[-1] not in ".,;:!?…" and bas.muhatap == tr_upper(bas.muhatap)
    metinler = [b for b in belge.bloklar if isinstance(b, evrak.MetinParagrafi)]
    assert [b.metin for b in metinler][-1] == "Bilgilerinizi arz ederim."
    assert not any(isinstance(b, evrak.Paragraf | evrak.Imza) for b in belge.bloklar)
    (imza,) = [b for b in belge.bloklar if isinstance(b, evrak.ResmiImza)]
    assert evrak.resmi_imza_hucreleri(imza)[1] == evrak.ImzaSahibi(
        gke_ortak.MUDUR_IMZASI, gke.UNVAN_OKUL_MUDURU
    )
    for sahip in imza.sahipler:
        *adlar, soyad = sahip.ad.split(" ")
        assert soyad == tr_upper(soyad) and adlar
    assert evrak.metin_akisi(belge)[-1] == f"Ek: {gke.BELGE_ADLARI['E11']}"
    docx = cizici_.ac(_dosya(kayit, "DOCX"))
    girintiler = [
        p.paragraph_format.first_line_indent
        for p in docx.paragraphs
        if p.text in {b.metin for b in metinler}
    ]
    assert len(girintiler) == len(metinler)
    assert all(g is not None and round(g.cm, 2) == evrak.METIN_GIRINTISI_CM for g in girintiler)
    son_tablo = [t for t in docx.tables if "Okul Müdürü" in t.rows[0].cells[-1].text][-1]
    sol, sag = son_tablo.rows[0].cells
    assert gke_ortak.MUDUR_IMZASI in sag.text and gke.UNVAN_YK_ADINA_BASKAN in sol.text


@pytest.mark.parametrize("kod", ["E12"])
def test_okul_idaresi_yazilarinin_taslagi_yonetici(kod: str) -> None:
    """Tasarım §9.3 "Okul idaresinin resmî yazıları", §9.6, §10.5 (KE-19): taslağı program yöneticisi
    oluşturur, imza bloğu Okul Müdürüdür; müdür hesabı gerekmez (programda müdür hesabı yokken de
    üretilir), müdür rolü ve öteki roller bu belgeye yazamaz (ret hiçbir kayıt yazmaz); E12 müdürün
    kendi yazısı sayılmaz."""
    kurul = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True)
    # Program yöneticisi müdür hesabı yokken üretir: ret denemeleri rol hesaplarını (müdürünki dahil)
    # açtığından üretim onlardan önce, müdür hesabının yokluğu üretimin hemen önünde sınanır.
    assert not Account.objects.filter(role=AccountRole.MUDUR).exists()
    with o.rol_olarak(AccountRole.YONETICI) as yonetici:
        assert not Account.objects.filter(role=AccountRole.MUDUR).exists()
        kayit = gke.uret(kod, kurul).kayit
    assert kayit.generated_by_id == yonetici.pk
    belge = evrak_servisi.yeniden_ciz(kayit)
    assert gke.UNVAN_OKUL_MUDURU in [gorev for _ad_, gorev in _imza_sahipleri(belge)]
    for rol in AccountRole:
        if rol == AccountRole.YONETICI:
            continue
        with o.rol_olarak(rol), pytest.raises(RolYetkisiz):
            gke.uret(kod, kurul)
    assert list(GeneratedDocument.objects.filter(doc_type=kod)) == [kayit]


def test_yk_ve_gk_belgelerinde_mudur_yazar_degil() -> None:
    """Tasarım §9.3, §10.5 (MB-3): okul müdürü yönetim kurulu belgelerinde ve genel kurul belgelerinde
    yazar ya da imzacı değildir — E05'te (yeni okul ve müdürün olağanüstü çağrısı hariç) ve E10'da
    "Okul Müdürü" yalnız "Görüldü" bloğundadır; E09 ve E11'de müdür bloğu yoktur, E13'te yalnız
    "Teslim alan"dır (bildirim okul müdürlüğüne yapılır). E05'in öteki çağrı kolları
    `test_e05_imza_cagirana_gore`'dedir; E28 ve E34 F4'tedir."""
    kurul = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True)
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, gke.Secim())[0] for kod in ("E09", "E10", "E11", "E13")
    }
    belgeler["E05"] = gke.e05_belgesi(kurul, gke.Secim(toplanti=_BIRINCI))[0]
    izinli = {
        "E05": {gke.UNVAN_GORULDU_E05},
        "E10": {gke.UNVAN_GORULDU_E05},
        "E13": {gorev_evraki.UNVAN_TESLIM_ALAN},
    }
    for kod, belge in belgeler.items():
        mudur = {gorev for _ad_, gorev in _imza_sahipleri(belge) if "Müdür" in gorev}
        assert mudur == izinli.get(kod, set()), kod
        assert all("örüldü" in gorev or "Teslim" in gorev for gorev in mudur), kod


def test_genel_kurul_evraki_ii_punto_ve_ad_soyad() -> None:
    """Tasarım §9.1-8 ve RYUE md. 7/1, 17/2: E09-E14'te yazı alanında 9 puntodan küçük metin yok,
    altlık 12 punto; imza bloğundaki (resmî yazının imza bölümü dahil) her ad "Ad SOYAD"."""
    from shared import docx as cizici
    from shared.tests.test_evrak import pdf_yazi_boyutlari

    kurul = gke_ortak.gorev_bolumlu(gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True))
    assert kurul.term is not None
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, gke.Secim())[0]
        for kod in ("E09", "E10", "E11", "E12", "E13")
    }
    belgeler["E14"] = gke.e14_belgesi(kurul.term, gke.Secim())[0]
    adlar = 0
    for kod, belge in belgeler.items():
        parcalar = pdf_yazi_boyutlari(evrak.pdf_ciz(belge))
        kucukler = [(m, b) for _s, m, b in parcalar if b < cizici.EN_KUCUK_PUNTO]
        assert parcalar and kucukler == [], (kod, kucukler)
        altlik = {b for _s, m, b in parcalar if m.startswith("OAB Defteri ·")}
        assert altlik == {float(cizici.ALTLIK_PUNTO)}, (kod, altlik)
        for imza_adi, _gorev in _imza_sahipleri(belge):
            if imza_adi in ("", gorev_evraki.BOS):
                continue
            *ilkler, soyad = imza_adi.split(" ")
            assert soyad == tr_upper(soyad) and ilkler, (kod, imza_adi)
            assert all(p[:1] == tr_upper(p[:1]) for p in ilkler), (kod, imza_adi)
            adlar += 1
    assert adlar >= len(("E10 divan", "E10 kâtip", "E12 başkan", "E12 müdür", "E13 başkan"))


#: Pilot eşdeğerlik (plan F2 §2 "Evrak genel setle içerik eşdeğer"; tasarım §10.5; F1c'nin
#: `PILOT` kalıbı): genel setin GNL-OAB-FR-002…005 ve RH-001 Bölüm 6 bölüm ve alanları ELLE yazılmıştır
#: (kamuya açık genel şablon; kişisel veri içeren pilot nüsha açılmadı); sağda belgedeki karşılığı ya
#: da alınmama gerekçesi. Gerçek pilot belgeleriyle elle karşılaştırma kullanıcıdadır (plan F2 §1.2).
PILOT_GK: dict[str, list[tuple[str, str | None, str]]] = {
    "E05": [
        ("Toplantı türü", "Genel kurulun türü", ""),
        ("Davet kararı (YK karar no / tarihi)", "Yönetim kurulunun çağrı kararı", "S1 (a)"),
        ("1. toplantı — tarih / saat / yer", "Birinci toplantı: gün ve saat", ""),
        ("2. toplantı (en geç 30 gün içinde)", "İkinci toplantı: gün ve saat", ""),
        ("Toplantı yeter sayısı (md. 9/2)", "Toplantı yeter sayısı (md. 9/2)", ""),
        ("Duyuru tarihi (en az 15 gün önce)", "İlan günü (en geç kanalın günü)", ""),
        ("Duyuru kanalları (üçü birlikte)", "Okul ilan panosu", ""),
        ("B. GÜNDEM", "Gündem", ""),
        ("Saygı duruşu ve İstiklal Marşı", "Saygı duruşu ve İstiklal Marşı", "U24 (teamül)"),
        ("D. DUYURU KANITI (md. 9/3)", "Duyuru kanıtı (md. 9/3)", ""),
        ("Nasıl / kim", "Yapanın görev unvanı (ad yazılmaz)", "ad yazılmaz"),
        ("Kanıt (dosyada)", None, "kanıt ilan kaydının dosya ekidir; belgeye basılmaz"),
    ],
    "E06": [
        ("GENEL KURUL DUYURUSU", "GENEL KURUL DUYURUSU", ""),
        ("… salonunda, yukarıdaki gündemle", "Toplantının yeri", ""),
        ("İkinci toplantı … çoğunluk aranmaksızın", "çoğunluk aranmaksızın", ""),
        ("Tüm üyeler davetlidir (md. 7/1)", "birliğin üyeleri genel kurula davetlidir", ""),
        ("Gözlemci öğrenciler (md. 9/5)", None, "tasarım §9.6 E06 kabulünde yok"),
        (
            "Birlik Yönetim Kurulu adına — Birlik Başkanı",
            "Okul-Aile Birliği Yönetim Kurulu",
            "§4.3",
        ),
        ("Duyuru tarihi", None, "ilan günü E05'in duyuru kanıtındadır"),
    ],
    "E08": [
        ("B. KATILIM CETVELİ (üyeler — md. 7/1)", "Veliler — sınıf: 5-A", "sınıf başına sayfa"),
        ("Adı ve soyadı", "Velinin adı ve soyadı", ""),
        ("Üyelik sıfatı (veli — sınıf · öğretmen · yönetici)", "Öğrencinin sınıfı", ""),
        ("İmza", "İmza", ""),
        ("Cetvel sayfaları divan başkanı ve kâtipçe paraflanır", "Divan Başkanı", "iki kol"),
        ("C. GÖZLEMCİ ÖĞRENCİLER (md. 9/5)", "Gözlemci öğrenciler", ""),
        ("Gözlemcinin adı ve soyadı", None, "gözlemcinin adı alınmaz (T5)"),
        ("Sıfatı · sınıf / şube", "Kurul ya da sınıf seviyesi", ""),
    ],
    "E64": [
        ("Toplantı tarihi / saati / yeri", "Toplantının günü, saati ve yeri", ""),
        ("Toplantı (1./2.)", "Toplantı", ""),
        ("Katılım cetveline göre katılan üye sayısı", "Katılım cetvelini imzalayan", ""),
        ("Cetvel sayfa sayısı", None, "sayfa sayısı programda tutulmaz"),
        ("Tespit: sağlandı / sağlanamadı", "Sonuç", ""),
        ("D. TESPİT VE İMZALAR — Divan Başkanı, Kâtip", "Divan Başkanı", ""),
        ("Birlik Başkanı (YK adına), Okul Müdürü (açılışı yapan)", None, "§4.3: yalnız divan"),
    ],
    "E09": [
        ("D. SEÇİM SONUÇLARI — adaylık şartı (md. 11/1-a, 12/1)", "A. Yönetim kurulu adayları", ""),
        ("YÖNETİM KURULU — adı soyadı", "Adı ve soyadı", ""),
        ("Asıl / yedek", "Asıl ya da yedek", ""),
        ("Kaçıncı dönem (md. 12/4)", "Önceki seçilme sayısı (md. 12/4)", ""),
        ("Oy", None, "oy seçim sonucundadır (genel kurul toplantı tutanağı)"),
        ("DENETLEME KURULU (veli) — adı soyadı", "B. Denetleme Kurulu veli koltuğu adayları", ""),
        ("Öğretmen üyeler öğretmenler kurulunca seçilmiştir", "öğretmenler kurulunca", ""),
        ("Md. 12/5 suç engeli", None, "beyan Yönetmeliğe bağlanmaz (KM-8)"),
    ],
    "E10": [
        ("A. TOPLANTI BİLGİLERİ", "A. Toplantı", ""),
        ("Toplantı türü (çağıran)", "Çağıran", ""),
        ("Tarih / saat / yer", "Toplantının günü, saati ve yeri", ""),
        ("Toplantı (1./2.) ve yeter sayı", "Toplantı yeter sayısı (md. 9/2)", ""),
        ("Çağrı ve duyuru (md. 9/3)", "İlan günü (md. 9/3)", ""),
        ("B. AÇILIŞ VE DİVAN (md. 10/1-b, c)", "B. Açılış ve divan (md. 10/1-b, c)", ""),
        ("Açılış — Okul Müdürü", "Toplantının açılışını okul müdürü yaptı", ""),
        ("Divan başkanı — oylama", "Divan Başkanı", "divanın oyu tutulmaz"),
        ("Gündem aynen / oy çokluğuyla değiştirildi (md. 9/4)", "Gündem değişikliği (md. 9/4)", ""),
        ("C. GÜNDEM MADDELERİNİN GÖRÜŞÜLMESİ VE KARARLAR", "C. Gündem maddeleri ve sonuçları", ""),
        ("Faaliyet raporu … tarafından okundu", "Yönetim kurulu faaliyet raporunu okuyan", ""),
        ("Gelir toplamı, gider toplamı, bakiye (TL)", None, "tutarlar faaliyet raporundadır (F4)"),
        ("Denetleme kurulu nihai raporu — okundu", "Denetleme Kurulu raporunu okuyan", ""),
        ("İBRA — kabul / ret / çekimser", "D. İbra (md. 11/1-c, ç)", "çekimser yok (S2)"),
        ("Tahmini bütçe — … TL; kabul", "Görüşüldü; ek: Tahmini bütçe", "U22: tutar yok"),
        ("Yetkilendirme (md. 11/1-e)", "Kabul edildi", ""),
        ("Seçimler (liste hâlinde açık oy)", "E. Seçim sonuçları", ""),
        ("Kapanış — teslim (md. 10/1-ç)", "F. Kapanış (md. 10/1-ç)", ""),
        ("E. İMZALAR — Görüldü — Okul Müdürü (md. 27/1)", "Görüldü — Okul Müdürü (md. 27/1)", ""),
        ("İş bu tutanak … sayfa; ekleri", None, "ekler genel kurul kaydının dosyalarıdır"),
    ],
    "E11": [
        ("İbra edilmeyen muhasebe evrakı (md. 11/1-ç)", "İbra edilmeyen muhasebe evrakı", ""),
        ("Devralan imza", "Teslim alan: Yeni Yönetim Kurulu adına üye", ""),
        ("Adet · son no · tutar", None, "evrak tek tek listelenir; tutar mali kayıtlarda (F3)"),
    ],
    "E13": [
        ("A. GENEL KURUL SONUCU", "A. Genel kurulun sonucu", ""),
        ("Genel kurul tarihi / türü", "Genel kurulun türü", ""),
        ("İbra durumu (YK / DK)", "Yönetim kurulunun ibrası", ""),
        ("Yeni yönetim kurulu (5 asıl / 5 yedek)", "B. Seçilen yönetim kurulu", ""),
        ("Denetleme kurulu veli üyesi", "C. Seçilen Denetleme Kurulu veli üyesi", ""),
        ("Tahmini bütçe — kabul (… TL)", "Görüşüldü; ek: Tahmini bütçe", "U22"),
        ("C. SONRAKİ ADIMLAR VE BİLDİRİMLER", "D. Sonraki işler", ""),
        ("Okul müdürlüğüne yazılı bildirim", None, "belgenin kendisidir; atıf basılmaz (MB-11)"),
        ("İbra edilmeme hâlinde il/ilçe MEM'e resmî yazı", "il/ilçe millî eğitim", ""),
        ("Yönetim kurulu görev bölümü (ilk hafta)", "Yönetim kurulunun görev bölümü", ""),
        ("Denetleme kurulu görev bölümü (ilk hafta)", "Denetleme Kurulunun görev bölümü", ""),
        ("Banka müşterek imza yetkisi (md. 18/2)", "Bankaya müşterek imza yetkililerinin", ""),
        ("TEFBİS girişi (okul idaresi)", "TEFBİS'e yeni yönetimin", ""),
        ("Bütçenin duyurusu; temsilci görevlendirmesi", None, "duyuru F4'te (U22); temsilci E01"),
        ("B. DEVİR-TESLİM LİSTESİ", None, "devir-teslim tutanağı F4'te (U29)"),
    ],
    "E14": [
        ("Genel kuruldan ≥ 15 gün önce — çağrı (md. 9/3)", "genel_kurul.ilan_en_az_gun", ""),
        ("OLAĞAN GENEL KURUL (en geç Ekim sonu)", "genel_kurul.olagan_son_ay", ""),
        ("İkinci toplantı (≤ 30 gün)", "genel_kurul.ikinci_toplanti_en_gec_gun", ""),
        ("Yönetim kurulu görev bölümü (ilk hafta)", "yonetim_kurulu.gorev_bolumu_gun", ""),
        ("Denetleme kurulu görev bölümü (ilk hafta)", "denetleme_kurulu.gorev_bolumu_gun", ""),
        ("Arz bedeli (sözleşme) 10'u; Yönetmelik 20'si", "arz_bedeli.sozlesme_vade_gunu", ""),
        ("Her ay yönetim kurulu toplantısı", "Yönetim kurulunun aylık toplantısı", "okul planı"),
        ("Denetleme kurulu ara denetimleri", "Denetleme Kurulunun 1. ara denetimi", "okul planı"),
        ("Ders yılı başlangıcı", "Ders yılının başlangıcı", ""),
        ("Sene başı öğretmenler kurulunda DK öğretmen seçimi", None, "programda kaydı yok"),
        ("Her ayın son iş günü — aylık bildirim (öneri)", None, "rehberin önerisi; kuralı yok"),
        ("Kantin kirası her ayın 5-15'i", None, "kira takvimi F3'te"),
        ("TEFBİS: genel kuruldan hemen sonra", None, "süre kural değildir (takvim satırı)"),
        ("Dönem sonu gelir-gider duyurusu (öneri)", None, "md. 13/10 F4'te"),
    ],
}
#: Genel setten bilinçli olarak alınmayan ibareler (plan F2 §4.3), belgede geçmez.
PILOT_GK_ALINMAYANLAR: dict[str, tuple[str, ...]] = {
    "E05": ("OAB-FR", "GNL-OAB"),
    "E06": ("Birlik Başkanı", "OAB-FR"),
    "E08": ("Öğrencinin adı", "numarası", "kimlik", "OAB-FR"),
    "E64": ("Birlik Başkanı", "Okul Müdürü", "OAB-FR"),
    "E09": ("OAB-FR", "md. 12/5"),
    "E10": ("çekimser", " TL", "OAB-FR"),
    "E11": ("tutar", "OAB-FR"),
    "E13": ("Yönetmelik gereği", " TL", "OAB-FR"),
    "E14": ("son iş günü", "5-15", "OAB-FR"),
}
#: Genel setin imzacısı olup belgede imzacı olmayan unvanlar (§4.3: OYS davetiyesinde "Okul Müdürü";
#: FR-003 D'de sağlansa da Birlik Başkanı ve açılışı yapan müdür).
PILOT_GK_ALINMAYAN_IMZALAR: dict[str, tuple[str, ...]] = {
    "E05": ("Okul Müdürü",),
    "E64": ("Birlik Başkanı", "Okul Müdürü (açılışı yapan)"),
}


def test_genel_kurul_evraki_pilot_esdegerligi() -> None:
    """Pilot eşdeğerlik (plan F2 §2, §4.3; öneri adı): genel setin (GNL-OAB-FR-002…005, RH-001 Bölüm
    6) her alanının belgede karşılığı ya da yazılı alınmama gerekçesi var; lettered bölümler tablodaki
    sırayla; alınmayan ibareler ve imzacılar belgede yok. Uydurma veriyle; kurallar yönetim kurulunun
    çağrısıyla birinci toplantıda yapılmış olağan genel kuruldur (E64 sağlandı)."""
    kurul = gke_ortak.yapilmis_tutanakli(ibra_edilmedi=True)
    gke_ortak.personel_ekle()
    assert kurul.term is not None
    belgeler = {
        kod: gke.KURUCULAR[kod](kurul, _gk_secim(kod))[0]
        for kod in ("E05", "E06", "E08", "E64", "E09", "E10", "E11", "E13")
    }
    belgeler["E14"] = gke.e14_belgesi(kurul.term, gke.Secim())[0]
    assert set(belgeler) == set(PILOT_GK) == set(PILOT_GK_ALINMAYANLAR)
    for kod, satirlar in PILOT_GK.items():
        belge = belgeler[kod]
        akis = _akis(belge)
        bolumler = [k for _s, k, _n in satirlar if k is not None and k[1:3] == ". "]
        harfli = [b for b in _alt_basliklar(belge) if b[1:3] == ". "]
        assert [k for b in harfli for k in bolumler if b.startswith(k)] == bolumler, kod
        for sablon, karsilik, gerekce in satirlar:
            if karsilik is None:
                assert gerekce.strip(), (kod, sablon)
            else:
                assert karsilik in akis, (kod, sablon, karsilik)
        for ibare in PILOT_GK_ALINMAYANLAR[kod]:
            assert ibare not in akis, (kod, ibare)
        imzacilar = {gorev for _ad_, gorev in _imza_sahipleri(belge)}
        for unvan in PILOT_GK_ALINMAYAN_IMZALAR.get(kod, ()):
            assert unvan not in imzacilar, (kod, unvan)
