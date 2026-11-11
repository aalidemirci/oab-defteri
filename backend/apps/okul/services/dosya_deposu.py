"""Dosya deposu servisi: ekin yazımı ve okunması (tasarım TK22, §4.4.7, §5.2.8; plan F1b-3).

`file_storage.py` UYARLA (tasarım §12.A): sha256, uuid adı ve boyut sınırı AYNEN; libmagic ve
yalnız-PDF kalkar, dosya şifrelenir. Kap, sarmal, ad, tür denetimi ve atomik yazım saf katmandadır
(`shared.dosya_sifreleme`); burası `Attachment` satırını, yazım sırasını, yükleme sınırını ve
kurallarını tutar. F1b'de ek ucu ve ekranı YOKTUR; bu servisi çağıran ilk sahip F1c'de
`GeneratedDocument`'tır (plan F1b-3 "Dosya deposu"; `apps.oab` kaydeder, plan F1c 9. adım).
`Attachment` `apps/okul`'dadır (plan F1b-3 "Sapma").

YAZMA (`yaz`). Sıra (plan F1b-3 "Dosya deposu"; §4.4.7):

1. Reddedilen dosya için hiçbir şey yazılmaz (`validate_upload` ilkesi, tasarım §12.A): veli adı
   taşıyan belge (`kisi_listesi`; E07, adlı E08 depoya hiç yazılmaz, R9), geçersiz ad, kayıtlı
   olmayan sahip, sınırı aşan ya da kabul edilmeyen tür. `kisi_listesi`'nin varsayılanı YOKTUR:
   bayrağı unutan çağıran veli adlı belgeyi saklamasın, kararını yazsın. Sahibin kendi işareti de
   okunur (`personal_list` alanı olan sahipte veritabanındaki değer; `GeneratedDocument`): bayrak
   `False` verilse de işaretli sahibe ek yazılmaz. Sahip kaydedilmiş ve hâlâ var olan bir satır
   olmalıdır (silinmiş ama `pk`'sı dolu bayat örnek de reddedilir). Tür imza baytındandır; kabul
   kümesi sahibindir (`sahip_kaydet`: kullanıcı eki PDF, JPEG, PNG; üretilen evrak PDF ve DOCX).
   `mime` verilirse ona uymalıdır.
2. DEK bellekte değilse `crypto.KeyMissingError` (fail-closed; uç 409 `parola_gerekli`).
3. Önce dosya: `dosyalar/<stored_name>`, atomik yazıcıyla (0600, fsync, `os.replace`; var olan adın
   üzerine yazılmaz). Dizin yoksa 0700 kurulur, kip çekilir (yazıcılar umask'a güvenmez; §4.5).
4. Sonra TEK işlemde satır ve `OLUSTUR` iz satırı (`transaction_mode = "IMMEDIATE"`; yazma kuralı
   1). İşlem düşerse dosya YETİM kalır, silinmez: satırı olmayan dosya zararsızdır ve açılış
   taraması toplar (plan F1b-3 "Geri yükleme"). Ters sıra her kesintide kalıcı bir "dosya yok"
   bırakırdı.

Yazımın tamamı uzun iştir (`shared.bakim.UZUN_ISLER`): oturum işin ortasında kilitlenmez, DEK
bellekten düşmez (§4.2 "Uçuştaki iş"). Yazım ayrıca bakım kapısından geçer (`shared.bakim.KAPI`;
plan F1b-3 ekleri: "ilk çağıran gelince canlı geri yüklemenin depo takasıyla çakışmasına bakılır",
F1c 9. adım): canlı geri yükleme dosya deposunu takas ederken (`live_restore`) yazım başlamaz
(`DepoBakimda`), başlamış yazım bitmeden takas yapılmaz (geri yükleme uçuştaki işi bekler). Başarılı
geri yüklemeden sonra kapı program yeniden açılana dek kapalı kalır, yazım da reddedilir. Yazar
`yazar`'dır; iz satırı da aynı yazarla yazılır, `uploaded_by` `SISTEM`'de boştur.

OKUMA (`oku`). Baytlar bellekte çözülür, açık kopya diske yazılmaz (§4.4.7 "Açık kopya kuralı");
yanıt `indirme_yaniti`'dır (uçlar onu verir; ilk uç E01-E03 ile, F1c 10. adım): `FileResponse(BytesIO(
...))`, `HttpResponse` değildir — `wsgi.file_wrapper` yolu gömülü sunucunun yanıt tamponuna girmez
(`desktop/server.py`); ek olarak verilir, önbelleğe alınmaz (`no-store`), türü satırın `mime`'ıdır.
Sıra: DEK, imha, dosya, GCM, özet. İmha edilmiş satır ve diskte bulunmayan dosya `EkDosyasiYok`'tur
("dosya yok"; §4.4.7). Açılan içeriğin özeti satırdakini tutmazsa `EkOzetiTutmuyor`: kap sağlam olsa
da içerik başka bir ekindir ya da satır değiştirilmiştir. Özel nitelikli ekin okunması erişim
günlüğüne `OZEL_NITELIKLI_EK` satırı yazar (§4.6.4); bayt ancak satır yazıldıktan sonra verilir,
yazılamazsa verilmez (fail-closed). Günlük hesabın okumasının kaydıdır: `SISTEM` yazarında ya da
bağlamsız okuma reddedilir (`erisim_gunlugu.yaz`).

EKSİK EKLER (`eksik_ekler`; tasarım §4.4.7 "Yetim ve eksik dosya"): satırı olup dosyası olmayan
kayıt canlı okunur, Genel Bakış'taki Eksik Ekler kartı buradan beslenir. Plan F1b-3 "Eksik ve bozuk
ekler kişisiz bilgiyle listelenir": asıl dosya adı yalnız bu kartta ve kaydın kendisinde görünür,
kilit açıkken çözülür. Yanıt yalnız program yöneticisine ve Denetleme Kuruluna gider.

SAHİP KÜMESİ: `owner_type` kayıtlı model etiketlerinden gelir (`sahip_kaydet`); ilk ve bugünkü tek
sahip `oab.GeneratedDocument`'tır (`apps.oab.apps`; üretilen evrak: PDF ve DOCX). Sahibin
`verbose_name`'i Türkçedir: eksik ve bozuk ek listelerinin "kayıt türü" oradan okunur
(`geri_yukleme_ekleri.tur_adi`). Testler geçici sahip kaydeder (plan F1b-3).

Bu modül kişi adı içerebilen özgün adı günlüğe, iletiye ve iz satırına koymaz (R1; §4.6.2).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Final

from django.conf import settings
from django.db import models, transaction
from django.http import FileResponse
from django.utils import timezone

from apps.okul import denetim_izi, erisim_gunlugu
from apps.okul.models import AccessKind, Attachment, AttachmentSensitivity
from apps.okul.oturum import Yazar, yazar_olarak
from apps.okul.services.geri_yukleme_ekleri import tur_adi
from shared import crypto
from shared import dosya_sifreleme as ds
from shared.bakim import KAPI, UZUN_ISLER

#: `original_name`'in üst sınırı (karakter); şifreli sütun TEXT'tir, sınırı burası zorlar.
OZGUN_AD_UZUNLUGU: Final = 255

#: Eke sahip olabilen modellerin etiketleri (modül başlığı "SAHİP KÜMESİ").
_SAHIP_ETIKETLERI: set[str] = set()
#: Bunlardan üretilen evrak sahibi olanlar: kabul kümeleri `ds.URETILEN_EVRAK_TURLERI`'dir.
_URETILEN_EVRAK_SAHIPLERI: set[str] = set()
#: Sahibin veli adı taşıyan belge işaretinin alanı (R9; `GeneratedDocument.personal_list`).
KISI_LISTESI_ALANI: Final = "personal_list"


class DosyaDeposuHatasi(ValueError):
    """Ek reddedildi ya da açılamadı (Türkçe ileti; özgün adı taşımaz)."""


class KisiListesiSaklanmaz(DosyaDeposuHatasi):
    """Veli adı taşıyan belge depoya yazılmaz (R9; tasarım §4.4.7, §5.2.8)."""

    def __init__(self) -> None:
        super().__init__("Veli adı taşıyan belge saklanmaz; dosya yazılmadı.")


class EkSahibiHatasi(DosyaDeposuHatasi):
    """`owner` kayıtlı bir sahip modelin kaydedilmiş satırı değil."""


class DepoBakimda(DosyaDeposuHatasi):
    """Bakım kapısı kapalı (geri yükleme sürüyor ya da yapıldı): ek yazılmadı."""

    def __init__(self) -> None:
        super().__init__("Geri yükleme sürüyor; dosya yazılmadı. Biraz sonra yeniden deneyin.")


class EkDosyasiYok(DosyaDeposuHatasi):
    """Ekin dosyası yok: imha edilmiş ya da diskte bulunmuyor (tasarım §4.4.7 "dosya yok")."""

    def __init__(self) -> None:
        super().__init__("Dosya yok: bu ekin dosyası imha edilmiş ya da depoda bulunamadı.")


class DepoOkunamadi(DosyaDeposuHatasi):
    """Depo dizini okunamadı. Yol taşımaz: kart hatayı izle birlikte günlüğe yazar, yol hesap adını
    içerir. `from None` ile yükseltilir, yoksa zincirdeki `OSError` yolu yine yazdırırdı."""

    def __init__(self, neden: str) -> None:
        super().__init__(f"Dosya deposu okunamadı ({neden}).")


class EkOzetiTutmuyor(ds.DogrulamaHatasi):
    """Açılan içeriğin özeti satırdaki `sha256`'yı tutmuyor; bayt verilmez."""

    def __init__(self) -> None:
        super().__init__("Ek dosyası doğrulanamadı: içeriği kaydındaki özeti tutmuyor; açılmadı.")


def sahip_kaydet(model: type[models.Model], *, uretilen_evrak: bool = False) -> None:
    """Modeli ek sahipleri kümesine ekler (modül başlığı "SAHİP KÜMESİ"); idempotenttir.

    `uretilen_evrak`: sahibin ekleri programın ürettiği evraktır, kabul kümesi PDF ve DOCX'tir
    (`ds.URETILEN_EVRAK_TURLERI`); öteki sahiplerde kullanıcı eki kümesi (PDF, JPEG, PNG).
    """
    etiket = denetim_izi.model_etiketi(model)
    _SAHIP_ETIKETLERI.add(etiket)
    if uretilen_evrak:
        _URETILEN_EVRAK_SAHIPLERI.add(etiket)
    else:
        _URETILEN_EVRAK_SAHIPLERI.discard(etiket)


def kabul_turleri(model: type[models.Model]) -> tuple[ds.DosyaTuru, ...]:
    """Sahibin kabul ettiği dosya türleri (modül başlığı "YAZMA" 1)."""
    if denetim_izi.model_etiketi(model) in _URETILEN_EVRAK_SAHIPLERI:
        return ds.URETILEN_EVRAK_TURLERI
    return ds.KABUL_EDILEN_TURLER


def depo_dizini() -> Path:
    """Dosya deposunun dizini: veri dizinindeki `dosyalar/` (tasarım §2.3.2)."""
    return Path(settings.DOSYA_DEPOSU_DIR)


def yukleme_siniri() -> int:
    """Ekin açık boyu üst sınırı (bayt): ayardaki yükleme sınırıyla biçim sınırının küçüğü."""
    return min(int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE), ds.AZAMI_ACIK_BOY)


def _veri_anahtari(dek: bytes | None = None) -> bytes:
    """Verilen ya da bellekteki DEK; yoksa `KeyMissingError` (fail-closed)."""
    anahtar = crypto.active_key() if dek is None else dek
    if anahtar is None:
        raise crypto.KeyMissingError("Ek dosyası için veri anahtarı bellekte değil.")
    return anahtar


def _ozgun_ad(ad: object) -> str:
    """Özgün adı denetler; ad hiçbir yola girmez, yalnız şifreli sütuna yazılır."""
    if not isinstance(ad, str) or not ad.strip():
        raise DosyaDeposuHatasi("Ekin dosya adı boş olamaz.")
    if len(ad) > OZGUN_AD_UZUNLUGU:
        raise DosyaDeposuHatasi(f"Ekin dosya adı en çok {OZGUN_AD_UZUNLUGU} karakter olabilir.")
    return ad


def _sahip_bagi(owner: models.Model) -> tuple[str, str]:
    """`owner`'dan (`owner_type`, `owner_id`); kayıtlı değilse, kaydedilmemişse ya da satırı artık
    yoksa ret. Sahip veli adı taşıyan belgeyse (`KISI_LISTESI_ALANI` veritabanında doğru)
    `KisiListesiSaklanmaz`."""
    model = type(owner)
    etiket = denetim_izi.model_etiketi(model)
    if etiket not in _SAHIP_ETIKETLERI:
        raise EkSahibiHatasi("Bu kayıt türüne ek bağlanamaz.")
    # Silinen örnekte `pk` boşalır, `adding` değişmez; `owner_id` "None" metni olurdu.
    if owner._state.adding or owner.pk is None:
        raise EkSahibiHatasi("Ek yalnız kaydedilmiş bir kayda bağlanır.")
    # Bayat örnek: `pk`'sı dolu ama satırı silinmiş (ya da hiç yazılmamış) sahip.
    satir = model._base_manager.filter(pk=owner.pk)
    if not satir.exists():
        raise EkSahibiHatasi("Ek yalnız kaydedilmiş bir kayda bağlanır.")
    alanlar = {alan.name for alan in model._meta.get_fields()}
    if KISI_LISTESI_ALANI in alanlar and satir.filter(**{KISI_LISTESI_ALANI: True}).exists():
        raise KisiListesiSaklanmaz()
    return etiket, denetim_izi.kimlik_metni(model, owner.pk)


def eksik_ekler() -> list[dict[str, Any]]:
    """Satırı olup depoda düzenli dosyası bulunmayan ekler, eskiden yeniye (modül başlığı).

    İmhalı satırın dosyası zaten yoktur, sayılmaz. Özgün ad satır satır, yalnız eksik ekte çözülür;
    çözülemeyen ad `None`'dır (`CorruptField` metin değildir). Depo dizini okunamazsa
    `DepoOkunamadi` yükselir: okunamayan depo boş sayılmaz.
    """
    try:
        depodakiler = set(ds.depodaki_dosyalar(depo_dizini()))
    except OSError as hata:
        raise DepoOkunamadi(type(hata).__name__) from None
    satirlar = (
        Attachment.objects.filter(purged_at__isnull=True)
        .defer("original_name", "key_wrap")
        .order_by("uploaded_at", "stored_name")
    )
    return [
        {
            "kayit_turu": tur_adi(ek.owner_type),
            "kayit_no": ek.owner_id,
            "yukleme_tarihi": timezone.localtime(ek.uploaded_at).date().isoformat(),
            "boyut": ek.size,
            "ozgun_ad": ek.original_name if isinstance(ek.original_name, str) else None,
        }
        for ek in satirlar
        if ek.stored_name not in depodakiler
    ]


def yaz(
    icerik: bytes,
    *,
    original_name: str,
    sensitivity: str,
    owner: models.Model,
    yazar: Yazar | None,
    kisi_listesi: bool,
    mime: str | None = None,
) -> Attachment:
    """Eki depoya yazar: önce dosya, sonra tek işlemde satır ve iz satırı (modül başlığı "YAZMA").

    Reddedilen dosya için diske hiçbir şey yazılmaz. Dosya yazıldıktan sonra işlem düşerse istisna
    çağırana gider ve dosya yetim kalır.
    """
    if kisi_listesi:
        raise KisiListesiSaklanmaz()
    if yazar is None:
        raise denetim_izi.IzYazilamadi("Yazar bağlamı olmayan ek yazılamaz (tasarım §4.6.2).")
    ad = _ozgun_ad(original_name)
    if sensitivity not in AttachmentSensitivity.values:
        raise DosyaDeposuHatasi("Ekin hassasiyeti geçersiz.")
    sahip_turu, sahip_kimligi = _sahip_bagi(owner)
    turler = kabul_turleri(type(owner))
    sinir = yukleme_siniri()
    if len(icerik) > sinir:
        raise ds.BoyutSiniriHatasi(f"Dosya çok büyük; en çok {sinir // (1024 * 1024)} MB olabilir.")
    if mime is not None and mime != ds.tur_belirle(icerik, turler):
        raise ds.TurHatasi("Dosyanın içeriği bildirilen türle uyuşmuyor.")
    with UZUN_ISLER.is_(), KAPI.is_() as izin:
        if not izin:
            raise DepoBakimda()
        sarmal_anahtari = crypto.file_wrap_key(_veri_anahtari())
        hazir = ds.dosya_hazirla(icerik, sarmal_anahtari=sarmal_anahtari, turler=turler)
        ds.depoya_yaz(ds.dizin_kur(depo_dizini()), hazir.stored_name, hazir.kap)
        with yazar_olarak(yazar), transaction.atomic():
            ek = Attachment.objects.create(
                stored_name=hazir.stored_name,
                original_name=ad,
                key_wrap=hazir.key_wrap,
                sha256=hazir.sha256,
                mime=hazir.mime,
                size=hazir.size,
                sensitivity=sensitivity,
                owner_type=sahip_turu,
                owner_id=sahip_kimligi,
                uploaded_by_id=yazar.hesap_id,
            )
            denetim_izi.degisiklik(ek, onceki=None)
    return ek


def oku(ek: Attachment, dek: bytes | None = None) -> bytes:
    """Ekin açık baytlarını bellekte verir; `dek` verilmezse bellekteki DEK (modül başlığı "OKUMA").

    Yanlış DEK, başka bir ada taşınmış kap ve bozuk dosya `ds.DogrulamaHatasi`'dır.
    """
    anahtar = _veri_anahtari(dek)
    if ek.purged_at is not None:
        raise EkDosyasiYok()
    try:
        acik = ds.depodan_ac(
            depo_dizini(),
            ek.stored_name,
            key_wrap=ek.key_wrap,
            sarmal_anahtari=crypto.file_wrap_key(anahtar),
        )
    except FileNotFoundError:
        raise EkDosyasiYok() from None
    if ds.acik_ozet(acik) != ek.sha256:
        raise EkOzetiTutmuyor()
    if ek.sensitivity == AttachmentSensitivity.OZEL_NITELIKLI:
        erisim_gunlugu.yaz(AccessKind.OZEL_NITELIKLI_EK, model=Attachment, object_id=ek.pk)
    return acik


def indirme_yaniti(ek: Attachment, *, dosya_adi: str) -> FileResponse:
    """Ekin indirme yanıtı (modül başlığı "OKUMA"): açık baytlar bellekte (`oku`), yanıt
    `FileResponse(BytesIO(...))`, ek olarak ve önbelleğe alınmadan. Dosya adı çağıranındır (sözlük §3
    "Kaydedilen dosya adı"); özgün ad kullanılmaz, kişi adı taşıyabilir."""
    yanit = FileResponse(
        BytesIO(oku(ek)), as_attachment=True, filename=dosya_adi, content_type=ek.mime
    )
    yanit["Cache-Control"] = "no-store"
    return yanit
