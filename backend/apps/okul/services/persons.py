"""Personel kayıt işlemleri, ayrılış yolu, ayrılış havuzu ve unutma kancası.

Tasarım §5.1, §5.4, §8.4. İnce servis katmanı — doğrulama/normalize
serializer'da, yazma burada. View ORM çağırmaz (katman disiplini).

UNUTMA KANCASI — KAYIT DEFTERLERİ (aile iskeletinden UYARLANDI). Okul
çekirdeğindeki kişinin başka uygulamalardaki kayıtlarla bağı olabilir (OAB'de
organ üyeliği, komisyon, imza bloğu, bağış ya da sözleşme — tasarım §5.4); okul
çekirdeği bu bağları bilmez, bu yüzden düzen kayıt defterlerine ayrıldı.
Bağımlılık yönü <uygulama> → okul'dur: okul diğer uygulamaları import etmez,
her uygulama kendi denetimini `AppConfig.ready` içinde buraya kaydeder. OAB
modelleri kancalarını F1c'den itibaren kaydeder (tasarım §12.B); F1c 4. adımdan beri
birlik kişisinin personel bağı (`OabPerson.personnel`) bağ denetimini ve birleştirme
kancasını kaydeder (`apps.oab.services.kisiler`):

- `register_obligation_check(fn)` → `fn(kişi) -> list[str]`: kişinin AÇIK
  yükümlülüklerinin Türkçe gerekçeleri. Gerekçe KİŞİ ADI İÇERMEZ (hata
  metnine ve günlüğe ad yazılmaz — sözlük §5).
- `register_membership_check(fn)` → `fn(kişi) -> bool`: kişi birlik
  kayıtlarına bağlanmış mı (bağlıysa kullanıcı silemez, aşağıda SİLME).
- `register_leave_hook(fn)` → `fn(kişi)`: ayrılışta çağrılır.
- `register_merge_hook(fn)` → `fn(kaynak, hedef)`: personel birleştirmede
  kaynağın bağlarını hedefe taşır.
- `register_deletion_block(fn)` → `fn(kişi) -> list[str]`: açık yükümlülük
  olmasa da kişiye bağlı kalıcı kaydı olan kişinin kullanıcı silmesini
  gerekçeyle reddeder.

Kancalar AYNI veritabanı işleminde koşar: hata verirlerse durum değişikliği de
geri sarılır. Kancalar yalnız veritabanına yazmalıdır (dosya, ağ yan etkisi yok).

AYRILIŞ HAVUZU (aile iskeletinden; tasarım §5.1 personel ayrılış havuzunu
alır). e-Okul listesinde bulunmayan kişi doğrudan silinmez, bir havuza girer ve
karar orada verilir; kayıt silinmez, yalnız aktiflik durumu değişir.

- e-Okul aktarımı hiç kimseyi AYIRMAZ ve SİLMEZ. Listede bulunmayan aktif kişi
  havuza girer (`add_to_leave_pool`: giriş tarihi + hangi aktarımla); durumu
  AKTİF kalır. Dosyada yeniden görülen kişi havuzdan kendiliğinden çıkar
  (`remove_from_leave_pool`).
- Karar yöneticinindir (`resolve_leave_pool`, tek tek ya da toplu): "Ayrıldı
  olarak işaretle" ayrılış yolundan geçirir, "Aktif kalsın" yalnız havuzdan
  çıkarır.
- Havuzdaki kişi DB kısıtıyla aktiftir (`ck_personnel_leave_candidate_active`).
- Havuz yalnız personeli taşır: öğrenci sicili F1b 5. adımda söküldü (tasarım §5.1
  ALMA); veli listesi havuz kullanmaz, sınıf bazında yerine konur (tasarım §8.4).

AYRILIŞ YOLU (tasarım §5.1): `left_at = localdate()`, `is_active=False`, havuz alanları
temizlenir, sonra ayrılış kancaları. **Ayrılış kaydı SİLMEZ** — bağdan ve yükümlülükten bağımsız (ailenin
eski "bağsız ve yükümlülüksüz → katı sil" dalı aile iskeletinde kalkmıştı).
Ayrılmış kişinin kaydının akıbeti saklama kuralındadır: ayrıldı işaretlenen ve
hiçbir birlik kaydına bağı olmayan personel, ayrılışı izleyen dönem kapanışında
silinir (tasarım §5.4). Bu silmeyi yapan iş henüz yoktur; dönem kapanışıyla
gelir (tasarım §7.8).

SİLME (kullanıcının bilinçli eylemi, "Sil" düğmesi): açık yükümlülük ya da
silme engeli varsa gerekçeyle reddedilir; kişi birlik kayıtlarına bağlıysa
silinmez, ayrılış yoluna yönlendirilir (`MEMBER_DELETE_MESSAGE`; birlik kaydı
silinmez — CLAUDE.md §2 altın kural 4); bağı yoksa katı silinir. Katı silme
BİLİNÇLİDİR: yanlış girilmiş kaydın yumuşak silmesi kişi verisini süresiz
tutardı. Personele bağlanan birlik kaydı F1c 4. adımdan beri birlik kişisidir
(`OabPerson.personnel`; tasarım §5.4: bağı olanın adı birlik kişisinde kalır): bağlı personel
silinmez (bağ denetimi). Hesap kendi ad-soyadını taşır, kişiye bağlanmaz; organ üyeliği ve imza
bloğu bağları birlik kişisinin üstünden gelir.

DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c). Her yazım veriyle AYNI işlemde iz
satırı yazar (`denetim_izi.degisiklik`): oluşturma `OLUSTUR`, ad/görev türü değişikliği
`GUNCELLE`, ayrılış ve havuza giriş-çıkış `DURUM` (durum alanları modeldedir). Personel
KVKK silme kümesindedir: satır yalnız alan ADLARINI taşır, değer taşımaz.
Önceki hâl yazmadan önce, aynı işlemde alınır. Toplu karar (`resolve_leave_pool`) kişi
başına satır yazar. Kayıt silinmez kuralının KVKK istisnası olan iki katı silme de izlidir
(plan "F1b-5 uygulama kararları"; tasarım §4.6.2 kural 4, §5 O1): kullanıcının silmesi
(`delete_personnel`, tetik `ELLE_SILME`) ve birleştirmede kaynağın silinmesi
(`merge_personnel`, tetik `BIRLESTIRME`) silmeyle AYNI işlemde kişisiz bir `KVKK_SILME`
satırı yazar (`denetim_izi.kvkk_silme`: model, alan adları, adet, kaydın günü, tetik; kimlik
ve değer yok).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi
from apps.okul.models import ImportRun, MemberKind, Personnel
from apps.okul.services import app_password

logger = logging.getLogger("oab_defteri.okul")

#: Kayıt defterlerinin kişi türü. Bugün yalnız personel: öğrenci sicili F1b 5. adımda söküldü;
#: veli listesi havuza girmez (tasarım §8.4: bir satır bir öğrenci, sınıf bazında yerine konur).
type Person = Personnel

type ObligationCheck = Callable[[Person], Iterable[str]]
type MembershipCheck = Callable[[Person], bool]
type LeaveHook = Callable[[Person], None]
type MergeHook = Callable[[Personnel, Personnel], None]
type DeletionBlock = Callable[[Person], Iterable[str]]

_obligation_checks: list[ObligationCheck] = []
_membership_checks: list[MembershipCheck] = []
_leave_hooks: list[LeaveHook] = []
_merge_hooks: list[MergeHook] = []
_deletion_blocks: list[DeletionBlock] = []

#: Ayrılış havuzu alanları.
POOL_FIELDS: tuple[str, str] = ("leave_candidate_since", "leave_candidate_run")

ALREADY_LEFT_MESSAGE = "Bu kişi zaten ayrıldı olarak işaretli."
MEMBER_DELETE_MESSAGE = (
    "Bu kişi birlik kayıtlarına bağlı; kaydı silinemez. Okuldan ayrıldıysa "
    "“Ayrıldı olarak işaretle” eylemini kullanın."
)
SELF_MERGE_MESSAGE = "Bir kişi kendisiyle birleştirilemez."
POOL_EMPTY_MESSAGE = "Karar verilecek kişi seçilmedi."
POOL_CONFLICT_MESSAGE = "Aynı kişi için hem “Ayrıldı olarak işaretle” hem “Aktif kalsın” seçilemez."
POOL_STALE_MESSAGE = (
    "Seçilen kişilerden bazıları artık ayrılış havuzunda değil. Listeyi yenileyip "
    "yeniden seçin; hiçbir karar uygulanmadı."
)


# ---------------------------------------------------------------------------
# Kayıt defterleri
# ---------------------------------------------------------------------------
def _register(registry: list[Any], fn: Any) -> None:
    """İdempotent kayıt (`AppConfig.ready` iki kez koşsa da kanca bir kez çağrılır)."""
    if fn not in registry:
        registry.append(fn)


def register_obligation_check(fn: ObligationCheck) -> None:
    """Açık yükümlülük denetimi: `fn(kişi)` Türkçe gerekçe listesi döner (ad içermez)."""
    _register(_obligation_checks, fn)


def register_membership_check(fn: MembershipCheck) -> None:
    """Bağ denetimi: `fn(kişi)` kişi birlik kayıtlarına bağlanmışsa True döner."""
    _register(_membership_checks, fn)


def register_leave_hook(fn: LeaveHook) -> None:
    """Ayrılış kancası: `fn(kişi)` ayrılış (LEFT + tarih) yazıldıktan sonra koşar."""
    _register(_leave_hooks, fn)


def register_merge_hook(fn: MergeHook) -> None:
    """Birleştirme kancası: `fn(kaynak, hedef)` kaynağın bağlarını hedefe taşır."""
    _register(_merge_hooks, fn)


def register_deletion_block(fn: DeletionBlock) -> None:
    """Silme engeli: `fn(kişi)` kapanmış da olsa kişiye bağlı kayıt varsa gerekçe döner.

    Açık yükümlülükten AYRIDIR: kapanmış bir kayıt kişinin yükümlülüğü değildir
    ama kişiyi PROTECT ile tutabilir; o bağı kullanıcının "Sil"i koparmaz
    (saklama kuralı, tasarım §5.4).
    """
    _register(_deletion_blocks, fn)


def deletion_blocks(person: Person) -> list[str]:
    """Kişinin silinmesini engelleyen (yükümlülük dışı) kayıtların gerekçeleri."""
    gerekceler: list[str] = []
    for check in _deletion_blocks:
        gerekceler.extend(check(person))
    return list(dict.fromkeys(g for g in gerekceler if g))


def open_obligations(person: Person) -> list[str]:
    """Kişinin açık yükümlülük gerekçeleri (tekilleştirilmiş, kayıt sırasıyla)."""
    gerekceler: list[str] = []
    for check in _obligation_checks:
        gerekceler.extend(check(person))
    return list(dict.fromkeys(g for g in gerekceler if g))


def was_ever_member(person: Person) -> bool:
    """Kişi birlik kayıtlarına bağlanmış mı? (F1c 4. adım: birlik kişisinin personel bağı)"""
    return any(check(person) for check in _membership_checks)


# ---------------------------------------------------------------------------
# Ortak yollar
# ---------------------------------------------------------------------------
def _is_active(person: Person) -> bool:
    return person.is_active


def _run_leave_hooks(person: Person) -> None:
    for hook in _leave_hooks:
        hook(person)


def _ensure_deletable(person: Person) -> None:
    """Kullanıcı silmesi: açık yükümlülük, silme engeli ya da birlik bağı varsa Türkçe ret (400)."""
    gerekceler = open_obligations(person)
    if gerekceler:
        raise ValidationError("Kayıt silinemez: " + " ".join(gerekceler))
    engeller = deletion_blocks(person)
    if engeller:
        raise ValidationError(" ".join(engeller))
    if was_ever_member(person):
        raise ValidationError(MEMBER_DELETE_MESSAGE)


def _changed_fields(instance: Any, fields: dict[str, Any]) -> list[str]:
    return [name for name, value in fields.items() if getattr(instance, name) != value]


# ---------------------------------------------------------------------------
# Ayrılış havuzu (tasarım §5.1 `Personnel`)
# ---------------------------------------------------------------------------
def in_leave_pool(person: Person) -> bool:
    """Kişi ayrılış havuzunda mı (karar bekliyor mu)?"""
    return person.leave_candidate_since is not None


def add_to_leave_pool(person: Person, *, run: ImportRun | None) -> bool:
    """Aktif kişiyi ayrılış havuzuna ekler; durumu AKTİF kalır. Eklendiyse True.

    Kişi zaten havuzdaysa dokunulmaz: ilk giriş tarihi ve onu ekleyen aktarım
    korunur (aynı dosyanın ikinci uygulaması değişiklik üretmez). Yalnız havuz
    alanları yazılır — ada dokunulmaz, anahtar gerekmez.
    """
    if not _is_active(person):
        raise ValidationError(ALREADY_LEFT_MESSAGE)
    if in_leave_pool(person):
        return False
    with transaction.atomic():
        onceki = denetim_izi.anlik(person)
        person.leave_candidate_since = timezone.localdate()
        person.leave_candidate_run = run
        person.save(update_fields=[*POOL_FIELDS, "updated_at"])
        denetim_izi.degisiklik(person, onceki=onceki)
    return True


def remove_from_leave_pool(person: Person, *, save: bool = True) -> bool:
    """Kişiyi havuzdan çıkarır (dosyada görüldü ya da "Aktif kalsın"). Havuzdaysa True.

    `save=False`: çağıran aynı kaydı başka alanlarla birlikte kendisi kaydeder ve izler
    (e-Okul aktarımı; `POOL_FIELDS`'i kendi `update_fields`'ine ekler).
    """
    if not in_leave_pool(person):
        return False
    if not save:
        person.leave_candidate_since = None
        person.leave_candidate_run = None
        return True
    with transaction.atomic():
        onceki = denetim_izi.anlik(person)
        person.leave_candidate_since = None
        person.leave_candidate_run = None
        person.save(update_fields=[*POOL_FIELDS, "updated_at"])
        denetim_izi.degisiklik(person, onceki=onceki)
    return True


@dataclass(frozen=True)
class PoolDecision:
    """Bir kişi türü için havuz kararı: ayrılacakların ve aktif kalacakların kimlikleri.

    Yinelenen kimlikler tekilleştirilir (sıra korunur).
    """

    leave: tuple[int, ...] = ()
    keep: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "leave", tuple(dict.fromkeys(self.leave)))
        object.__setattr__(self, "keep", tuple(dict.fromkeys(self.keep)))

    def ids(self) -> set[int]:
        return {*self.leave, *self.keep}


def _pool_members(ids: Collection[int]) -> dict[int, Personnel]:
    """Kimlikleri havuzdaki AKTİF canlı personele çözer; biri eksikse hiçbir şey yapılmaz."""
    if not ids:
        return {}
    bulunan = {
        kayit.pk: kayit
        for kayit in Personnel.objects.filter(
            pk__in=ids, leave_candidate_since__isnull=False, is_active=True
        )
    }
    if len(bulunan) != len(set(ids)):
        raise ValidationError(POOL_STALE_MESSAGE)
    return bulunan


@transaction.atomic
def resolve_leave_pool(*, personnel: PoolDecision | None = None) -> dict[str, int]:
    """Ayrılış havuzu kararı — tek tek ya da toplu; TEK işlem (ya hepsi ya hiçbiri).

    `leave` → ayrılış yolu (`is_active=False` + `left_at`, havuzdan çıkış,
    ayrılış kancaları; kayıt SİLİNMEZ). `keep` → "Aktif kalsın": yalnız havuzdan
    çıkar. Seçilen kişi havuzda değilse (başka pencerede karar verilmiş, ayrılmış,
    silinmiş) bütün karar reddedilir. Günlüğe yalnız sayılar yazılır.
    """
    app_password.require_password_set()
    personnel = personnel or PoolDecision()
    if set(personnel.leave) & set(personnel.keep):
        raise ValidationError(POOL_CONFLICT_MESSAGE)
    if not personnel.ids():
        raise ValidationError(POOL_EMPTY_MESSAGE)

    personeller = _pool_members(personnel.ids())
    for pk in personnel.leave:
        leave_personnel(personeller[pk], log=False)
    for pk in personnel.keep:
        remove_from_leave_pool(personeller[pk])

    sonuc = {
        "personnel_left": len(personnel.leave),
        "personnel_kept": len(personnel.keep),
    }
    logger.info(
        "Ayrılış havuzu kararı: %d personel ayrıldı, %d personel aktif kaldı.",
        sonuc["personnel_left"],
        sonuc["personnel_kept"],
    )
    return sonuc


# ---------------------------------------------------------------------------
# Personel
# ---------------------------------------------------------------------------
@transaction.atomic
def create_personnel(**fields: Any) -> Personnel:
    app_password.require_password_set()
    fields.setdefault("member_kind", MemberKind.OGRETMEN)
    person: Personnel = Personnel.objects.create(**fields)
    denetim_izi.degisiklik(person, onceki=None)
    return person


@transaction.atomic
def update_personnel(person: Personnel, **fields: Any) -> Personnel:
    """Yalnız DEĞİŞEN alanı yazar. Ayrılış `leave_personnel` ile olur."""
    changed = _changed_fields(person, fields)
    if changed:
        onceki = denetim_izi.anlik(person)
        for name in changed:
            setattr(person, name, fields[name])
        person.save(update_fields=[*changed, "updated_at"])
        denetim_izi.degisiklik(person, onceki=onceki)
    return person


@transaction.atomic
def leave_personnel(person: Personnel, *, log: bool = True) -> Personnel:
    """Ayrılış yolu (tasarım §5.1): `is_active=False` + `left_at`, havuzdan çıkış, kancalar.

    Kayıt SİLİNMEZ. `log=False`: toplu çağıran (havuz kararı) kişi başına günlük satırı
    yazdırmaz; kendi sayısal özetini yazar.
    """
    if not person.is_active:
        raise ValidationError(ALREADY_LEFT_MESSAGE)
    onceki = denetim_izi.anlik(person)
    person.is_active = False
    person.left_at = timezone.localdate()
    remove_from_leave_pool(person, save=False)
    person.save(update_fields=["is_active", "left_at", *POOL_FIELDS, "updated_at"])
    denetim_izi.degisiklik(person, onceki=onceki)
    _run_leave_hooks(person)
    if log:
        logger.info("Personel ayrılışı işlendi; kayıt saklandı.")
    return person


def reactivate_personnel(person: Personnel) -> None:
    """Ayrılmış (canlı) personel listede yeniden görüldü: aktif, `left_at` temizlenir."""
    person.is_active = True
    person.left_at = None


def _kaydin_gunu(person: Personnel) -> date:
    """`KVKK_SILME` satırının "en yeni" günü: silinen tek kaydın oluşturulduğu gün (§4.6.4)."""
    return timezone.localdate(person.created_at)


@transaction.atomic
def delete_personnel(person: Personnel) -> None:
    """Kullanıcı silmesi: açık yükümlülük, silme engeli ve birlik bağı yoksa KATI silinir.

    Denetim izine `KVKK_SILME` satırı düşer (tetik `ELLE_SILME`; modül başlığı).
    """
    app_password.require_password_set()
    _ensure_deletable(person)
    person.hard_delete()
    # Bütün satır silinir (`alanlar=None`); kimlik ve değer satıra girmez (modül başlığı).
    denetim_izi.kvkk_silme(
        Personnel, adet=1, en_yeni=_kaydin_gunu(person), tetik=denetim_izi.KVKK_TETIK_ELLE_SILME
    )
    logger.info("Personel kaydı silindi.")


@transaction.atomic
def merge_personnel(source: Personnel, target: Personnel) -> Personnel:
    """ "Olası aynı kişi" birleştirmesi: kaynağın bağları hedefe taşınır, kaynak KATI silinir.

    Tipik kullanım soyadı değişimidir: e-Okul'dan yeni adla gelen kayıt HEDEF,
    listede artık bulunmayan (ayrılış havuzundaki) eski kayıt KAYNAKTIR.
    Birleştirme aktarım önizlemesinden sonra ya da ayrılış havuzundan yapılır.
    İki kayıt da canlı olmalıdır (görünüm yalnız canlı kayıtları çözer) ve aynı
    kişi olamaz. Taşıma birleştirme kancalarıyla yapılır (F1c 4. adımdan beri birlik
    kişisinin personel bağı hedefe taşınır; `apps.oab.services.kisiler`).

    Kaynağın silinmesi denetim izine `KVKK_SILME` satırıyla düşer (tetik `BIRLESTIRME`; modül
    başlığı); hedef kayıt değişmez. Kancaların taşıdığı bağların izini kancalar yazar.
    """
    app_password.require_password_set()
    if source.pk == target.pk:
        raise ValidationError(SELF_MERGE_MESSAGE)
    if source.deleted_at is not None or target.deleted_at is not None:
        raise ValidationError("Birleştirilecek iki kayıt da sicilde bulunmalıdır.")
    for hook in _merge_hooks:
        hook(source, target)
    source.hard_delete()
    denetim_izi.kvkk_silme(
        Personnel, adet=1, en_yeni=_kaydin_gunu(source), tetik=denetim_izi.KVKK_TETIK_BIRLESTIRME
    )
    logger.info("Personel kayıtları birleştirildi.")
    return target
