"""Üretilen evrakın kaydı, dosyası ve yeniden basımı (tasarım §5.2.8, §9.1-2; plan F1c 9. adım).

KAYIT (`kaydet`). Evrakın içerik modeli (`shared.evrak.Belge`) çizildikten sonra çağrılır; satır ve
izi TEK işlemdedir (`transaction_mode = "IMMEDIATE"`). Sıra:

1. Kod evrak kataloğu biçimindedir (`E01`…`E79`), konu kaydedilmiş bir satırdır.
2. Dönem verildiyse dönem kilidinden geçer (O2): kapanmış dönemde de yazılır, satırın izi
   `KAPALI_DONEM` etiketini taşır (beyaz liste "yeniden basım"; `donem_kilidi.yazma_denetimi`).
   Kapanmış dönemde içerik değişmez: aynı konunun aynı evrakının geçerli satırı varsa yeni içeriğin
   özeti onunkiyle aynı olmalıdır (§5.2.8), değilse `DonemKapali`; geçerli satırı olmayan ilk kayıt
   (kapanmış dönemden üretilen evrak, ör. E39 arşiv paketi, §7.8) serbesttir. Veli adı taşıyan
   belge beyaz listede değildir (O2 "veli adı taşıyan belge hariç", §5.2.8): kapanmış döneme
   yazılmaz (`DonemKapali`). Kural kopyası tutmayan dönem salt okurdur, iptal edilmiş dönem yazılmaz; hazırlıktaki döneme
   yalnız genel kurul hazırlığının evrakı yazılır (`hazirlik_yazimi`).
3. Aynı konunun aynı evrakının geçerli satırı `YERINI_ALDI` olur (`DURUM` satırı; silinmez), yeni
   satır bir sonraki sürümdür (`OLUSTUR`). Kural paketi dönemin bağlı kopyasıdır; dönemsiz evrakta
   (E63) boştur.
4. İçerik: kanonik JSON (`kanonik_json`, şifreli sütun) ve özeti (`content_sha256`). Veli adı taşıyan
   belgede (R9, `kisi_listesi`) içerik saklanmaz, yalnız özeti ve satır sayısı kalır.

Yazar oturumun yazarıdır (`created_by`, `generated_by`); `SISTEM` yazarında ikisi boştur. Konu `okul`
tarafında olabilir (E63'te hesap): `okul` bu modülü içe aktarmaz, kayıt defterinden çağırır
(`apps.okul.services.evrak_kaydi`; `AppConfig.ready`).

DOSYA (`dosya_ekle`). Üretilen dosya (PDF ya da DOCX) dosya deposuna bu satırın eki olarak yazılır
(`dosya_deposu.yaz`; tür denetimi sahibin kümesiyle, veli adı taşıyan belgeye ek yazılmaz). Biçim
satırın `formats`'ında olmalıdır. E63'ün dosyası saklanmaz (tasarım §9.1-2): bu işlevi çağırmaz.

YENİDEN BASIM (`yeniden_ciz`). İçerik kayıtlı JSON'dan modele geri çevrilir (`shared.evrak.belge_coz`):
JSON çözülemezse, kanonik biçimi tutmazsa ya da özeti satırdakini tutmazsa belge basılmaz
(`EvrakIcerigiTutmuyor`). Böylece kapanmış dönemin belgesi program, şablon ya da ana veri değişse de
aynı içerik özetini verir (§6.2-6). Veli adı taşıyan belgenin içeriği yoktur (`EvrakIcerigiSaklanmaz`).
Basım izi ve rol kapısı çağıranındır (evrakın ucu; E01-E03 10. adımda).
"""

from __future__ import annotations

from collections.abc import Iterable

from django.db import models, transaction
from django.utils import timezone

from apps.oab.hatalar import DonemKapali, EvrakIcerigiSaklanmaz, EvrakIcerigiTutmuyor
from apps.oab.models import (
    DocumentFormat,
    DocumentStatus,
    EvrakKaydiGecersiz,
    GeneratedDocument,
    OabTerm,
)
from apps.oab.models.evrak import EVRAK_KODU
from apps.oab.services import donem_kilidi, iz
from apps.okul import denetim_izi
from apps.okul.models import Attachment, AttachmentSensitivity, AuditLabel
from apps.okul.oturum import yazar
from apps.okul.services import dosya_deposu
from shared import dosya_sifreleme as ds
from shared import evrak

#: Biçimin dosya deposundaki türü (imza baytından belirlenen MIME; `ds.URETILEN_EVRAK_TURLERI`).
BICIM_TURLERI: dict[str, str] = {DocumentFormat.PDF: ds.PDF.mime, DocumentFormat.DOCX: ds.DOCX.mime}

KOD_GECERSIZ = "Evrak kodu biçimsiz."
KONU_GECERSIZ = "Evrak yalnız kaydedilmiş bir kayıt için üretilir."
BICIM_GECERSIZ = "Evrakın biçim listesi geçersiz."
BICIM_KAYITTA_YOK = "Bu biçim evrakın kaydında yok; dosya eklenmedi."
GECERLI_DEGIL = "Yerini yeni sürüme bırakmış evraka dosya eklenmez."


def _bicimler(bicimler: Iterable[str]) -> list[str]:
    liste = sorted(set(bicimler))
    if not liste or not set(liste) <= set(DocumentFormat.values):
        raise EvrakKaydiGecersiz(BICIM_GECERSIZ)
    return liste


@transaction.atomic
def kaydet(
    belge: evrak.Belge,
    *,
    konu: models.Model,
    bicimler: Iterable[str],
    donem: OabTerm | None = None,
    kisi_listesi: bool = False,
    satir_sayisi: int | None = None,
    hazirlik_yazimi: bool = False,
) -> GeneratedDocument:
    """Üretimin kaydı (modül başlığı "KAYIT"); yeni sürüm satırını döner."""
    if not EVRAK_KODU.fullmatch(belge.kod):
        raise EvrakKaydiGecersiz(KOD_GECERSIZ)
    if konu.pk is None or konu._state.adding:
        raise EvrakKaydiGecersiz(KONU_GECERSIZ)
    liste = _bicimler(bicimler)
    etiket = ""
    if donem is not None:
        donem = OabTerm.objects.select_related("rule_package").get(pk=donem.pk)
        # Veli adı taşıyan belge beyaz listede değildir (O2, §5.2.8): kapanmış dönemde ret.
        etiket = donem_kilidi.yazma_denetimi(
            donem, beyaz_liste=not kisi_listesi, hazirlik_yazimi=hazirlik_yazimi
        )
    konu_turu = denetim_izi.model_etiketi(type(konu))
    konu_kimligi = denetim_izi.kimlik_metni(type(konu), konu.pk)
    oncekiler = GeneratedDocument.objects.filter(
        doc_type=belge.kod, subject_type=konu_turu, subject_id=konu_kimligi
    )
    json_metni = evrak.kanonik_json(belge)
    ozet = evrak.metin_ozeti(json_metni)
    if etiket == AuditLabel.KAPALI_DONEM:
        # Kapanmış dönemde yeniden basım geçerli satırın içeriğini verir (§5.2.8, O2): farklı içerik
        # yazılmaz. Geçerli satırı olmayan ilk kayıt (kapanmış dönemden üretilen evrak) serbesttir.
        gecerli_ozet = (
            oncekiler.filter(status=DocumentStatus.GECERLI)
            .values_list("content_sha256", flat=True)
            .first()
        )
        if gecerli_ozet is not None and gecerli_ozet != ozet:
            raise DonemKapali
    hesap = iz.yazar_hesabi()
    simdi = timezone.now()
    son = oncekiler.order_by("-version").values_list("version", flat=True).first()
    for gecerli in oncekiler.filter(status=DocumentStatus.GECERLI):
        onceki = denetim_izi.anlik(gecerli)
        gecerli.status = DocumentStatus.YERINI_ALDI
        gecerli.updated_by_id = hesap
        gecerli.save(update_fields=["status", "updated_at", "updated_by"])
        denetim_izi.degisiklik(gecerli, onceki=onceki, label=etiket)
    kayit = GeneratedDocument.objects.create(
        doc_type=belge.kod,
        subject_type=konu_turu,
        subject_id=konu_kimligi,
        term=donem,
        version=(son or 0) + 1,
        formats=liste,
        content_sha256=ozet,
        content_json="" if kisi_listesi else json_metni,
        personal_list=kisi_listesi,
        row_count=satir_sayisi,
        rule_package=donem.rule_package if donem is not None else None,
        generated_at=simdi,
        generated_by_id=hesap,
        created_by_id=hesap,
        updated_by_id=hesap,
    )
    denetim_izi.degisiklik(kayit, onceki=None, label=etiket)
    return kayit


def dosya_ekle(
    kayit: GeneratedDocument, icerik: bytes, *, bicim: str, dosya_adi: str
) -> Attachment:
    """Üretilen dosyayı kaydın eki olarak saklar (modül başlığı "DOSYA").

    Satırın güncel hâli okunur: yerini almış kayda ve kaydında olmayan biçime dosya eklenmez. Veli
    adı taşıyan belge dosya deposunda reddedilir (`KisiListesiSaklanmaz`).
    """
    guncel = GeneratedDocument.objects.get(pk=kayit.pk)
    if bicim not in guncel.formats or bicim not in BICIM_TURLERI:
        raise EvrakKaydiGecersiz(BICIM_KAYITTA_YOK)
    if guncel.status != DocumentStatus.GECERLI:
        raise EvrakKaydiGecersiz(GECERLI_DEGIL)
    return dosya_deposu.yaz(
        icerik,
        original_name=dosya_adi,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=guncel,
        yazar=yazar(),
        kisi_listesi=guncel.personal_list,
        mime=BICIM_TURLERI[bicim],
    )


def yeniden_ciz(kayit: GeneratedDocument) -> evrak.Belge:
    """Kayıtlı içerikten içerik modeli (modül başlığı "YENİDEN BASIM"); özet satırdakiyle aynıdır."""
    guncel = GeneratedDocument.objects.get(pk=kayit.pk)
    if guncel.personal_list:
        raise EvrakIcerigiSaklanmaz
    metin = guncel.content_json
    if not isinstance(metin, str) or evrak.metin_ozeti(metin) != guncel.content_sha256:
        raise EvrakIcerigiTutmuyor
    try:
        return evrak.belge_coz(metin)
    except evrak.BelgeCozulemedi:
        raise EvrakIcerigiTutmuyor from None


def okul_evraki_kaydet(
    belge: evrak.Belge, *, konu: models.Model, bicimler: Iterable[str]
) -> GeneratedDocument:
    """`okul` tarafının dönemsiz evrakı (E63: konu hesap; dosyası saklanmaz). Kayıt defterine
    kaydedilen işlev budur (`apps.okul.services.evrak_kaydi`; `AppConfig.ready`)."""
    return kaydet(belge, konu=konu, bicimler=bicimler)
