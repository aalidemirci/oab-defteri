"""Dosya deposu servisi: ekin yazımı ve okunması (tasarım TK22, §4.4.7, §5.2.8; plan F1b-3).

OYS `file_storage.py` UYARLA (tasarım §12.A): sha256, uuid adı ve boyut sınırı AYNEN; libmagic ve
yalnız-PDF kalkar, dosya şifrelenir. Kap, sarmal, ad, tür denetimi ve atomik yazım saf katmandadır
(`shared.dosya_sifreleme`); burası `Attachment` satırını, yazım sırasını, yükleme sınırını ve
kurallarını tutar. F1b'de ek ucu ve ekranı YOKTUR; bu servisi çağıran ilk sahip F1c'de
`GeneratedDocument`'tır (plan F1b-3 "Dosya deposu"). `Attachment` F1b'de `apps/okul`'dadır (plan
F1b-3 "Sapma").

YAZMA (`yaz`). Sıra (plan F1b-3 "Dosya deposu"; §4.4.7):

1. Reddedilen dosya için hiçbir şey yazılmaz (OYS `validate_upload` ilkesi): veli adı taşıyan belge
   (`kisi_listesi`; E07, adlı E08 depoya hiç yazılmaz, R9), geçersiz ad, kayıtlı olmayan sahip,
   sınırı aşan ya da kabul edilmeyen tür. `kisi_listesi`'nin varsayılanı YOKTUR: bayrağı unutan
   çağıran veli adlı belgeyi saklamasın, kararını yazsın. Tür imza baytındandır; `mime` verilirse
   ona uymalıdır.
2. DEK bellekte değilse `crypto.KeyMissingError` (fail-closed; uç 409 `parola_gerekli`).
3. Önce dosya: `dosyalar/<stored_name>`, atomik yazıcıyla (0600, fsync, `os.replace`; var olan adın
   üzerine yazılmaz). Dizin yoksa 0700 kurulur, kip çekilir (yazıcılar umask'a güvenmez; §4.5).
4. Sonra TEK işlemde satır ve `OLUSTUR` iz satırı (`transaction_mode = "IMMEDIATE"`; yazma kuralı
   1). İşlem düşerse dosya YETİM kalır, silinmez: satırı olmayan dosya zararsızdır ve açılış
   taraması toplar (plan F1b-3 "Geri yükleme"). Ters sıra her kesintide kalıcı bir "dosya yok"
   bırakırdı.

Yazımın tamamı uzun iştir (`shared.bakim.UZUN_ISLER`): oturum işin ortasında kilitlenmez, DEK
bellekten düşmez (§4.2 "Uçuştaki iş"). Yazar `yazar`'dır; iz satırı da aynı yazarla yazılır,
`uploaded_by` `SISTEM`'de boştur.

OKUMA (`oku`). Baytlar bellekte çözülür, açık kopya diske yazılmaz (§4.4.7 "Açık kopya kuralı");
yanıtın başlıkları ucun işidir (F1c). Ucun yanıtı `FileResponse(BytesIO(...))`'tir, `HttpResponse`
değildir: `wsgi.file_wrapper` yolu gömülü sunucunun yanıt tamponuna girmez (`desktop/server.py`).
Sıra: DEK, imha, dosya, GCM, özet. İmha edilmiş satır ve diskte bulunmayan dosya `EkDosyasiYok`'tur
("dosya yok"; §4.4.7). Açılan içeriğin özeti satırdakini tutmazsa `EkOzetiTutmuyor`: kap sağlam olsa
da içerik başka bir ekindir ya da satır değiştirilmiştir. Özel nitelikli ekin okunması erişim
günlüğüne `OZEL_NITELIKLI_EK` satırı yazar (§4.6.4); bayt ancak satır yazıldıktan sonra verilir,
yazılamazsa verilmez (fail-closed). Günlük hesabın okumasının kaydıdır: `SISTEM` yazarında ya da
bağlamsız okuma reddedilir (`erisim_gunlugu.yaz`).

SAHİP KÜMESİ: `owner_type` kayıtlı model etiketlerinden gelir (`sahip_kaydet`); F1b'de küme BOŞTUR,
ilk kaydı F1c'de sahibiyle birlikte gelir. Testler geçici sahip kaydeder (plan F1b-3).

Bu modül kişi adı içerebilen özgün adı günlüğe, iletiye ve iz satırına koymaz (R1; §4.6.2).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from django.conf import settings
from django.db import models, transaction

from apps.okul import denetim_izi, erisim_gunlugu
from apps.okul.models import AccessKind, Attachment, AttachmentSensitivity
from apps.okul.oturum import Yazar, yazar_olarak
from shared import crypto
from shared import dosya_sifreleme as ds
from shared.bakim import UZUN_ISLER

#: `dosyalar/` altındaki yetim dizininin adı (plan F1b-3 "Geri yükleme"; taraması (c) alt commit'i).
YETIM_DIZINI: Final = "yetim"
#: Depo dizinlerinin POSIX kipi (tasarım §4.5).
DIZIN_KIPI: Final = 0o700
#: `original_name`'in üst sınırı (karakter); şifreli sütun TEXT'tir, sınırı burası zorlar.
OZGUN_AD_UZUNLUGU: Final = 255

#: Eke sahip olabilen modellerin etiketleri (modül başlığı "SAHİP KÜMESİ").
_SAHIP_ETIKETLERI: set[str] = set()


class DosyaDeposuHatasi(ValueError):
    """Ek reddedildi ya da açılamadı (Türkçe ileti; özgün adı taşımaz)."""


class KisiListesiSaklanmaz(DosyaDeposuHatasi):
    """Veli adı taşıyan belge depoya yazılmaz (R9; tasarım §4.4.7, §5.2.8)."""

    def __init__(self) -> None:
        super().__init__("Veli adı taşıyan belge saklanmaz; dosya yazılmadı.")


class EkSahibiHatasi(DosyaDeposuHatasi):
    """`owner` kayıtlı bir sahip modelin kaydedilmiş satırı değil."""


class EkDosyasiYok(DosyaDeposuHatasi):
    """Ekin dosyası yok: imha edilmiş ya da diskte bulunmuyor (tasarım §4.4.7 "dosya yok")."""

    def __init__(self) -> None:
        super().__init__("Dosya yok: bu ekin dosyası imha edilmiş ya da depoda bulunamadı.")


class EkOzetiTutmuyor(ds.DogrulamaHatasi):
    """Açılan içeriğin özeti satırdaki `sha256`'yı tutmuyor; bayt verilmez."""

    def __init__(self) -> None:
        super().__init__("Ek dosyası doğrulanamadı: içeriği kaydındaki özeti tutmuyor; açılmadı.")


def sahip_kaydet(model: type[models.Model]) -> None:
    """Modeli ek sahipleri kümesine ekler (modül başlığı "SAHİP KÜMESİ")."""
    _SAHIP_ETIKETLERI.add(denetim_izi.model_etiketi(model))


def depo_dizini() -> Path:
    """Dosya deposunun dizini: veri dizinindeki `dosyalar/` (tasarım §2.3.2)."""
    return Path(settings.DOSYA_DEPOSU_DIR)


def yukleme_siniri() -> int:
    """Ekin açık boyu üst sınırı (bayt): ayardaki yükleme sınırıyla biçim sınırının küçüğü."""
    return min(int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE), ds.AZAMI_ACIK_BOY)


def _depo_dizinini_kur() -> Path:
    """Dizini yoksa kurar, POSIX'te 0700'e çeker (modül başlığı adım 3); yolu döndürür."""
    dizin = depo_dizini()
    dizin.mkdir(mode=DIZIN_KIPI, parents=True, exist_ok=True)
    if os.name == "posix":
        dizin.chmod(DIZIN_KIPI)
    return dizin


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
    """`owner`'dan (`owner_type`, `owner_id`); kayıtlı değilse ya da kaydedilmemişse ret."""
    model = type(owner)
    etiket = denetim_izi.model_etiketi(model)
    if etiket not in _SAHIP_ETIKETLERI:
        raise EkSahibiHatasi("Bu kayıt türüne ek bağlanamaz.")
    # Silinen örnekte `pk` boşalır, `adding` değişmez; `owner_id` "None" metni olurdu.
    if owner._state.adding or owner.pk is None:
        raise EkSahibiHatasi("Ek yalnız kaydedilmiş bir kayda bağlanır.")
    return etiket, denetim_izi.kimlik_metni(model, owner.pk)


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
    sinir = yukleme_siniri()
    if len(icerik) > sinir:
        raise ds.BoyutSiniriHatasi(f"Dosya çok büyük; en çok {sinir // (1024 * 1024)} MB olabilir.")
    if mime is not None and mime != ds.tur_belirle(icerik):
        raise ds.TurHatasi("Dosyanın içeriği bildirilen türle uyuşmuyor.")
    with UZUN_ISLER.is_():
        sarmal_anahtari = crypto.file_wrap_key(_veri_anahtari())
        hazir = ds.dosya_hazirla(icerik, sarmal_anahtari=sarmal_anahtari)
        ds.depoya_yaz(_depo_dizinini_kur(), hazir.stored_name, hazir.kap)
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
