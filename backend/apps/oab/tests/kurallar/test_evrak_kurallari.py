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
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import pytest
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from pypdf import PdfReader
from rest_framework.test import APIClient

from apps.oab.kurallar import kural
from apps.oab.models import (
    BoardDecision,
    DecisionKind,
    DecisionStatus,
    DocumentStatus,
    GeneratedDocument,
    KararDurumuGecersiz,
    MeetingKind,
    OabTerm,
    Representation,
)
from apps.oab.services import evrak as evrak_servisi
from apps.oab.services import gorev_evraki, kisiler, kurullar, temsilciler, uyelikler
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
KATALOG_KABUL_KODLARI = ("E01", "E02", "E03", "E63")


@pytest.mark.parametrize("kod", KATALOG_KABUL_KODLARI)
def test_katalog_kabul(kod: str, yakalanan: list[evrak.Belge]) -> None:
    """Tasarım §9.6 "Kabul örneği" sütunu, kod başına (E01-E03: F1c 10. adım; E63: F1b)."""
    if kod == e63.KOD:
        _kabul_e63(yakalanan)
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


@pytest.mark.parametrize("kod", ["E01", "E02", "E03", "E63"])
def test_sayfa_butcesi(kod: str) -> None:
    """E63: en uzun uydurma veriyle sayfa bütçesi (`_en_uzun_pusula`): her rolün pusulası en çok iki
    sayfadır. Kullanıcı kararı 11.11.2026: RYUE md. 7/1 gereği yazı alanında 9 puntodan küçük metin
    olmaz (dipnot ve aydınlatma metni 9); yönetim kurulu ve öteki rollerin 04.11.2026'daki bir sayfa
    sınırı gevşedi, aydınlatma metni gerekirse ikinci yaprağa geçer. Program yöneticisi en çok "iş"
    satırını taşır ve listesi sonraki fazların ekranlarıyla uzar; sınırı zaten ikiydi.

    E01-E03 (F1c 10. adım): gerçek uzunlukta uydurma veriyle (`gorev_evraki_ortak`, `uzun=True`:
    uzun ad ve soyadlar, okul adı ve ilçe alanlarının üst sınırında; tam kadro, bütün temsilci
    satırları) `GOREV_EVRAKI_SAYFA_SINIRI`."""
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


@pytest.mark.parametrize("belge_adi", ["E01", "E02", "E03", "E63", "kurtarma_anahtari_belgesi"])
def test_tckn_hicbir_belgede_yok(belge_adi: str, yakalanan: list[evrak.Belge]) -> None:
    """Programın bugün ürettiği belgelerde 11 haneli kimlik deseni yok: kişi alanlarına sağlaması
    tutan uydurma T.C. kimlik numarası yazılır (hesap sahibinin ve okul müdürünün adı), çıktıda
    aranır. K9 ayarının kolları (`k9_kapali`, `k9_acik`) bağış kaydıyla F3'te eklenir. E01-E03
    (F1c 10. adım): numara belgenin basmadığı serbest metinlere yazılır (görev bölümü toplantısının
    gündemi, kararın metni, devralınan üyeliğin dayanak notu, dönemin programdan önceki kanıtı);
    Word ve PDF çıktısı, içerik JSON'u ve `BASIM` satırı aranır."""
    tckn = _saglamali_uydurma_numara("100000001")
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
    sırasıyladır."""
    etkin = {satir for rol in ROLLER for satir in etkin_hucreler(rol)}
    assert set(e63.BUGUNKU_ISLER) == etkin
    for is_ in e63.BUGUNKU_ISLER.values():
        assert is_.parcalar and all(parca.ad.strip() for parca in is_.parcalar), is_
        assert not re.search(r"\b(YK|DK|DEK|M\d+|E\d{2})\b", is_.ad), is_.ad
    for rol in ROLLER:
        assert e63.isler(rol) == tuple(
            e63.BUGUNKU_ISLER[s].rol_adi(rol) for s in etkin_hucreler(rol)
        )
        # Etkin satırın, rolün pusulasında en az bir parçası vardır (boş ad basılmaz).
        for satir in etkin_hucreler(rol):
            assert e63.BUGUNKU_ISLER[satir].rol_parcalari(rol), (rol, satir)


def test_e63_is_parcalari_var_olan_uclara_karsilik_gelir() -> None:
    """Orkestratör maddesi F-4: her işin her parçası, pusulası basılan rolün o satırda bugün
    yazabildiği bir uca bağlıdır (uç yoksa ad yazılamaz: "hesap geçişi", "birlik döneminin
    açılması" bugün yazılamaz). Ters yönde, etkin satırın her yazma ucu bir parçada adlanır ya da
    `ADSIZ_UCLAR`'da gerekçesiyle durur: bir faz yeni bir uç getirince ad da büyür."""
    adsiz_kullanilan: set[str] = set()
    kullanilan_parcalar: set[tuple[Satir, str]] = set()
    for rol in ROLLER:
        for satir in etkin_hucreler(rol):
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
        e63.BUGUNKU_ISLER[satir].rol_adi(rol) for rol in ROLLER for satir in etkin_hucreler(rol)
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
    "E63": "Hesap teslim pusulası",
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
    return [
        (sahip.ad, sahip.gorev)
        for blok in belge.bloklar
        if isinstance(blok, evrak.Imza)
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


@pytest.mark.parametrize("kod", ["E01", "E02", "E03"])
def test_docx_pdf_icerik_esdegerligi(kod: str) -> None:
    """Tasarım §10.5: kaydedilen iki dosyadan aynı kanonik metin akışı çıkar (gövde blokları belge
    sırasıyla, tablo hücreleri satır satır; PDF'te altlık ayıklanır; boşluk normalleştirilir);
    Word'de `w:caps` yok. Türkçe büyük harf: başlık `tr_upper`'dandır ("İ"), çıplak `.upper()` biçimi
    çıktıda yoktur."""
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


@pytest.mark.parametrize("kod", ["E01", "E02", "E03"])
def test_mudur_bloklari_yalniz_93_tablosunda(kod: str) -> None:
    """MB-15, §9.3: müdür bloğu yalnız tablodaki belgelerde ve oradaki türüyle — E03'te "Teslim alan",
    E01 (yönetim kurulu belgesi) ve E02'de (Denetleme Kurulu, denetleyenin bağımsızlığı) yok; hiçbir
    belgede "Görüldü" bloğu yok."""
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
