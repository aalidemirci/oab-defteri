"""Gelen-giden evrak defteri ve kaydı (tasarım §5.2.8 `DocumentRecord`, §4.4.2 M10 ve dipnot ⁷; plan
F2 §1.1-11, §5.1, §6.2; F2 7. adım).

Program gelen-giden evrak defterinin yerine geçmez (md. 23/1-c; defter il/ilçe millî eğitim
müdürlüğünce tasdiklidir, md. 23/2): deftere yazılacak kaydı tutar, numaranın tekilliğini ve sırasını
denetler. Uç ve ekran 11. adımdadır (Gelen-Giden Evrak ekranı).

KİM (tasarım §4.4.2 M10; ⁷). Defteri ve kaydı program yöneticisi ile yönetim kurulu rolleri yazar
(`Eylem.EVRAK_KAYDI`); Denetleme Kurulu ve müdür okur. Müdürün kendi yazısı (yeni okulda genel kurul
daveti, olağanüstü genel kurul çağrısı) evrak defterine PROGRAM tarafından işlenir: kayıt müdür
yazısı eyleminin yan etkisidir, ayrı eylemi ve ucu yoktur (`mudur_yazisini_isle`; çağıranı
`genel_kurul.cagir`, müdür eyleminin kapısından sonra). Kaydın kendi `OLUSTUR` iz satırı vardır, yazarı
müdürün hesabıdır (F0-F1 planı F1b-2 "müdür yazısının evrak kaydının ayrı izi").

DEFTER. Defter `OfficialBook(GELEN_GIDEN_EVRAK_DEFTERI)`'dir, dönemsizdir; kayıt kullanımdaki (`KULLANIMDA`)
defterin en yenisine yazılır. Tasdik bilgisi boş bırakılabilir. Tasarım §5.2.8 tasdik kaydı yokken ya
da yanlış makamla (md. 23/2: karar defteri dışındaki defterler il/ilçe millî eğitim müdürlüğünce) kullanımı
uyarı sayar; kural paketinde bu kural yoktur (`r2`; tasarımın kural tablosunda öteki defterlerin tasdiki
kural kimliği almaz, defter ekranı ve E22 F3'tedir) ve program bu adımda denetlemez. Kuralın `r2`'ye
eklenmesi ya da F3'e ertelenmesi kullanıcıya sorulacaktır (plan F2 7. adım). Geçiş kaydındaki
"programdan önceki son sıra no" (`last_no_before_program`) defterin programa kaydedildiği takvim
yılının numarasıdır (yerel gün); o yılın ilk program kaydının beklenen numarası onun bir fazlasıdır.

NUMARA. (defter, yıl, kayıt no) tekildir — sert (hesap bütünlüğü: numara tekilliği; veritabanı kısıtı
`uq_documentrecord_defter_yil_no`). Yıl evrakın tarihinin takvim yılıdır. Numara verilmezse sıradaki
numara yazılır; sıradakinden büyük numara sıra atlatır: uyarı + gerekçe (tasarım §5.2.8 "Sıra atlama
uyarı"; Yönetmelik maddesine ve kural paketine dayanmaz, akış satırıdır — `SIRA_ATLAMA_AKISI`, konu
kayıttır). Atlanmış boş numaraya sonradan yazmak sırayı bozmaz, uyarı vermez. Geçişteki son sıra no ve
altındaki numaralar o yılın kâğıt defterde kullanılmış numaralarıdır, boş değildir: elle verilse de
reddedilir — sert (numara tekilliği).

ŞİFRELEME (tasarım §5.3). Karşı taraf ve konu serbest metindir, şifrelidir; değer listesine ve iz
satırının değerlerine girmez (içerik MAC'indedir). Dış sayı (karşı tarafın ya da EBYS'nin sayısı)
açıktır. Ekler dosya deposuna kayıt sahibiyle yazılır (`evrak_kaydina_ek_ekle`; kullanıcı eki kümesi
PDF, JPEG, PNG; `apps.oab.apps` sahibi kaydeder).

Kayıt silinmez (altın kural 4). Her yazma denetim izine düşer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Final

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.oab.models import (
    BookCertifier,
    BookKind,
    BookStatus,
    DocumentDirection,
    DocumentRecord,
    OabTerm,
    OfficialBook,
    TermStatus,
)
from apps.oab.services import donem_kilidi, iz, uyum
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AccountRole, Attachment, AttachmentSensitivity
from apps.okul.oturum import yazar
from apps.okul.services import app_password, dosya_deposu
from shared.exceptions import RolYetkisiz

# ---------------------------------------------------------------------------
# İletiler (kullanıcıya görünür; sözlük §1)
# ---------------------------------------------------------------------------
DEFTER_YOK = "Gelen-giden evrak defteri kaydedilmedi; önce kullanımdaki gelen-giden evrak defterini kaydedin."
DEFTER_TURU_GECERSIZ = "Bu defter gelen-giden evrak defteri değil."
DEFTER_KULLANIMDA_DEGIL = "Bu defter kullanımda değil; kayıt kullanımdaki deftere yazılır."
TASDIK_MAKAMI_GECERSIZ = "Tasdik eden makam geçersiz."
SAYI_GECERSIZ = "Sayılar 1 ya da daha büyük tam sayı olmalıdır."
YON_GECERSIZ = "Evrakın yönü gelen ya da giden olmalıdır."
TARIH_GECERSIZ = "Evrakın tarihi girilmelidir."
KAYIT_NO_GECERSIZ = "Kayıt no 1 ya da daha büyük tam sayı olmalıdır."
KAYIT_NO_KULLANILDI = (
    "Bu defterde bu yılın {no} numaralı kaydı var; kayıt no defterde ve yılda tekildir (hesap "
    "bütünlüğü)."
)
KAYIT_NO_GECIS_ONCESI = (
    "Bu yılın {no} numarası programdan önce defterde kullanıldı (programdan önceki son sıra no {son}); "
    "kayıt no defterde ve yılda tekildir (hesap bütünlüğü)."
)
DIS_SAYI_UZUN = "Dış sayı en çok {uzunluk} karakter olabilir."
ACIK_DONEM_YOK = "Açık birlik dönemi yok; evrak kaydı açık birlik dönemine yazılır."

#: Sıra atlamanın akış satırı (tasarım §5.2.8 "Sıra atlama uyarı"; Yönetmelik maddesi değildir, atıf
#: basılmaz; `uyum.akis_sapmasi`).
SIRA_ATLAMA_AKISI: Final = "akis.evrak_kaydi_sira_atlama"
SIRA_ATLAMA: Final = (
    "Kayıt no sıradaki numara değil ({beklenen} bekleniyordu); defterde atlanan numara kalır (program "
    "uyarısıdır, Yönetmelik hükmü değildir)."
)

#: Müdür yazısının programca kaydında karşı taraf (yazının muhatabı; kişisiz).
MUDUR_YAZISI_MUHATABI: Final = "Okul-aile birliği üyeleri"

_DIS_SAYI_MAX: Final = DocumentRecord._meta.get_field("external_ref").max_length or 0


@dataclass(frozen=True)
class EvrakKaydiSonucu:
    """Kaydın sonucu: kayıt ve bu yazımda çıkan uyarılar (akış satırları)."""

    kayit: DocumentRecord
    uyarilar: tuple[dict[str, Any], ...] = ()


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _kapi() -> None:
    """M10 yazma kapısı (⁷: müdür okur; kendi yazısını program işler)."""
    app_password.require_password_set()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.EVRAK_KAYDI)


def _secimli_sayi(deger: object) -> int | None:
    if deger is None:
        return None
    if not isinstance(deger, int) or isinstance(deger, bool) or deger < 1:
        raise ValueError(SAYI_GECERSIZ)
    return deger


def evrak_defteri() -> OfficialBook | None:
    """Kullanımdaki gelen-giden evrak defterinin en yenisi (modül başlığı "Defter"); yoksa `None`."""
    defter: OfficialBook | None = (
        OfficialBook.objects.filter(
            kind=BookKind.GELEN_GIDEN_EVRAK_DEFTERI, status=BookStatus.KULLANIMDA
        )
        .order_by("-id")
        .first()
    )
    return defter


def _defter(defter: OfficialBook | None) -> OfficialBook:
    if defter is None:
        bulunan = evrak_defteri()
        if bulunan is None:
            raise ValueError(DEFTER_YOK)
        return bulunan
    guncel = OfficialBook.objects.get(pk=defter.pk)
    if guncel.kind != BookKind.GELEN_GIDEN_EVRAK_DEFTERI:
        raise ValueError(DEFTER_TURU_GECERSIZ)
    if guncel.status != BookStatus.KULLANIMDA:
        raise ValueError(DEFTER_KULLANIMDA_DEGIL)
    return guncel


def gecis_oncesi_son_no(defter: OfficialBook, yil: int) -> int | None:
    """Defterin o yılda programdan önce kullanılmış son sıra no'su: yalnız defterin programa kaydedildiği
    takvim yılında (yerel gün; modül başlığı "Defter"), girilmişse."""
    if (
        defter.last_no_before_program is not None
        and timezone.localtime(defter.created_at).year == yil
    ):
        return int(defter.last_no_before_program)
    return None


def beklenen_kayit_no(defter: OfficialBook, yil: int) -> int:
    """Defterin o yılda sıradaki numarası (modül başlığı "Defter", "Numara")."""
    son = DocumentRecord.objects.filter(book=defter, year=yil).aggregate(son=Max("record_no"))[
        "son"
    ]
    if son is not None:
        return int(son) + 1
    gecis_oncesi = gecis_oncesi_son_no(defter, yil)
    if gecis_oncesi is not None:
        return gecis_oncesi + 1
    return 1


def _kaydi_yaz(
    *,
    defter: OfficialBook,
    donem: OabTerm,
    direction: str,
    tarih: date,
    counterparty: str,
    subject: str,
    external_ref: str,
    record_no: int,
) -> DocumentRecord:
    hesap = iz.yazar_hesabi()
    kayit = DocumentRecord.objects.create(
        book=defter,
        direction=direction,
        year=tarih.year,
        record_no=record_no,
        date=tarih,
        counterparty=counterparty,
        subject=subject,
        external_ref=external_ref,
        term=donem,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kayit, onceki=None)
    return kayit


# ---------------------------------------------------------------------------
# Defter
# ---------------------------------------------------------------------------
@transaction.atomic
def evrak_defteri_olustur(
    *,
    certified_by: str = "",
    certified_on: date | None = None,
    certification_no: str = "",
    page_count: int | None = None,
    last_no_before_program: int | None = None,
    opened_on: date | None = None,
) -> OfficialBook:
    """Gelen-giden evrak defterini kaydeder (`OLUSTUR`; dönemsiz). Tasdik bilgisi boş bırakılabilir;
    geçişte defterdeki son sıra no girilir (modül başlığı "Defter")."""
    _kapi()
    if certified_by and certified_by not in BookCertifier.values:
        raise ValueError(TASDIK_MAKAMI_GECERSIZ)
    hesap = iz.yazar_hesabi()
    defter = OfficialBook.objects.create(
        kind=BookKind.GELEN_GIDEN_EVRAK_DEFTERI,
        certified_by=certified_by,
        certified_on=certified_on,
        certification_no=certification_no.strip(),
        page_count=_secimli_sayi(page_count),
        last_no_before_program=_secimli_sayi(last_no_before_program),
        opened_on=opened_on,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(defter, onceki=None)
    return defter


# ---------------------------------------------------------------------------
# Kayıt
# ---------------------------------------------------------------------------
@transaction.atomic
def evrak_kaydet(
    *,
    direction: str,
    tarih: date,
    counterparty: str = "",
    subject: str = "",
    external_ref: str = "",
    record_no: int | None = None,
    defter: OfficialBook | None = None,
    gerekce: uyum.Gerekce | None = None,
) -> EvrakKaydiSonucu:
    """Gelen ya da giden evrakı deftere kaydeder (modül başlığı "Numara"). Kayıt açık birlik dönemine
    yazılır; numara verilmezse sıradaki numaradır, sıradakinden büyükse uyarı + gerekçe."""
    _kapi()
    if direction not in DocumentDirection.values:
        raise ValueError(YON_GECERSIZ)
    if not isinstance(tarih, date) or isinstance(tarih, datetime):
        raise ValueError(TARIH_GECERSIZ)
    dis_sayi = external_ref.strip()
    if len(dis_sayi) > _DIS_SAYI_MAX:
        raise ValueError(DIS_SAYI_UZUN.format(uzunluk=_DIS_SAYI_MAX))
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    if donem is None:
        raise ValueError(ACIK_DONEM_YOK)
    donem_kilidi.yazma_denetimi(donem)
    guncel_defter = _defter(defter)
    beklenen = beklenen_kayit_no(guncel_defter, tarih.year)
    if record_no is None:
        numara = beklenen
    else:
        if not isinstance(record_no, int) or isinstance(record_no, bool) or record_no < 1:
            raise ValueError(KAYIT_NO_GECERSIZ)
        numara = record_no
    gecis_oncesi = gecis_oncesi_son_no(guncel_defter, tarih.year)
    if gecis_oncesi is not None and numara <= gecis_oncesi:
        raise ValueError(KAYIT_NO_GECIS_ONCESI.format(no=numara, son=gecis_oncesi))
    if DocumentRecord.objects.filter(
        book=guncel_defter, year=tarih.year, record_no=numara
    ).exists():
        raise ValueError(KAYIT_NO_KULLANILDI.format(no=numara))
    kayit = _kaydi_yaz(
        defter=guncel_defter,
        donem=donem,
        direction=direction,
        tarih=tarih,
        counterparty=counterparty.strip(),
        subject=subject.strip(),
        external_ref=dis_sayi,
        record_no=numara,
    )
    uyarilar: list[dict[str, Any]] = []
    if numara > beklenen:
        mesaj = SIRA_ATLAMA.format(beklenen=beklenen)
        uyum.akis_sapmasi(SIRA_ATLAMA_AKISI, mesaj, donem=donem, konu=kayit, gerekce=gerekce)
        uyarilar.append(
            {
                "kural": SIRA_ATLAMA_AKISI,
                "atif": "",
                "mesaj": mesaj,
                "durum": "uyari",
                "paket": "",
                "rev": None,
            }
        )
    return EvrakKaydiSonucu(kayit=kayit, uyarilar=tuple(uyarilar))


def mudur_yazisini_isle(*, donem: OabTerm, subject: str) -> DocumentRecord | None:
    """Müdür yazısını evrak defterine giden evrak olarak işler (dipnot ⁷; modül başlığı "Kim").

    Kendi kapısı yoktur: müdür yazısı eyleminin içinden, o eylemin kapısından sonra çağrılır
    (`genel_kurul.cagir`); derin savunma olarak yazar müdür değilse ret. Kullanımdaki defter yoksa
    kayıt yazılmaz, `None` döner (çağıran bilgi satırı verir; yeni açılan okulda birliğin defteri
    henüz yoktur). Tarih bugünün yerel günü, numara sıradaki numaradır. Kayıt dönemin hazırlık
    yazımıdır (yeni okulun ilk genel kurulunda dönem hazırlık dönemidir)."""
    kim = yazar()
    if kim is None or kim.sistem_mi or kim.rol != AccountRole.MUDUR.value:
        raise RolYetkisiz
    defter = evrak_defteri()
    if defter is None:
        return None
    guncel_donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
    donem_kilidi.yazma_denetimi(guncel_donem, hazirlik_yazimi=True)
    bugun = timezone.localdate()
    return _kaydi_yaz(
        defter=defter,
        donem=guncel_donem,
        direction=DocumentDirection.GIDEN,
        tarih=bugun,
        counterparty=MUDUR_YAZISI_MUHATABI,
        subject=subject,
        external_ref="",
        record_no=beklenen_kayit_no(defter, bugun.year),
    )


def evrak_kaydina_ek_ekle(
    kayit: DocumentRecord,
    icerik: bytes,
    *,
    dosya_adi: str,
    sensitivity: str = AttachmentSensitivity.NORMAL,
) -> Attachment:
    """Kayda ek (taranmış evrak) yazar: dosya deposu, sahip bu kayıt (modül başlığı "Şifreleme").

    Dönem kilidi denetlenir; kapanmış dönemin kaydına ek yazılmaz (O2)."""
    _kapi()
    guncel = DocumentRecord.objects.select_related("term__rule_package").get(pk=kayit.pk)
    donem_kilidi.yazma_denetimi(guncel.term, hazirlik_yazimi=True)
    return dosya_deposu.yaz(
        icerik,
        original_name=dosya_adi,
        sensitivity=sensitivity,
        owner=guncel,
        yazar=yazar(),
        kisi_listesi=False,
    )
