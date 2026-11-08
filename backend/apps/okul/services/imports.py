"""Personel toplu içe aktarma ve e-Okul MUTABAKATI, veli listesi aktarımı — preview + commit.

Aile iskeletinden alındı (iskelet bunu atalarının `services/imports.py`
kalıbından uyarlamış, mutabakatla genişletmişti; OAB'de tasarım §8.4). Öğrenci
aktarımı F1b 5. adımda öğrenci sicili ve şube kataloğuyla birlikte söküldü (tasarım §5.1
ALMA, T5); yerine VELİ LİSTESİ aktarımı geldi (aşağıda "VELİ LİSTESİ" ve modülün son bölümü).

- **AKTARIM HİÇ KİMSEYİ AYIRMAZ VE SİLMEZ (aile iskeletinin kullanıcı kararı
  22.09.2026).** Mutabakatta listede bulunmayan aktif kişi AYRILIŞ HAVUZUNA
  girer (`persons.add_to_leave_pool`: giriş tarihi + bu aktarım), durumu AKTİF
  kalır; karar Kişiler → Ayrılış Havuzu'nda yöneticinindir. Dosyada bulunan kişi
  havuzdaysa kendiliğinden çıkar (`persons.remove_from_leave_pool`).
- **Personel mutabakatı:** eşleşme normalize ad-soyadla (Python; ad
  şifreli). Listede olmayan aktif personel havuza girer (eski `mark_left_ids`
  seçimi kalktı; karar havuzda verilir). Ada göre eşleşmeyen yeni satırla
  listede olmayan kişi arasında "olası aynı kişi" çifti üretilir (soyadı
  değişimi) — çift eşleşme GEREKÇESİNİ taşır (tasarım §13 D30: "adı aynı" adaşı da
  yakalar); birleştirme ayrı uçtandır (`persons.merge_personnel`) ve havuzdan
  da yapılabilir.
- **Havuza ekleme yalnız kanıtla (import silmez ilkesi).** Kimlik anahtarı ad olduğu
  için ad-soyadı boş bir satır (kaymış sütun) ya da hiç satırı işlenemeyen bir dosya
  hiç kimseyi havuza eklemez. Her durum önizlemede satır no ile söylenir.
- **Kişisel veri ve kalıcı iz:** havuza eklenecek kişilerin ADLARI yalnız API
  yanıtında (yönetim yüzeyi, açık oturum) döner; `ImportRun.report` (kalıcı)
  yalnız SAYILARI taşır (`to_run_dict`). Satır sorunlarına ad ve görev
  metni yazılmaz; hücrenin ham değeri (`raw_value`) yalnız API yanıtındadır,
  kalıcı rapordan silinir (kaymış sütunda kişi verisi taşıyabilir). Günlüğe
  yalnız sayılar düşer ve yalnız uygulamada yazılır (önizleme geri sarılır).
- Dosya (.xlsx ŞABLONU, e-Okul'un .xls İHRACI ve .csv; tasarım §8.1 A4) ile pano
  yapıştırması AYNI boru hattı: her girişten önce `rows` matrisi üretilir
  (`excel_ortak.dosyayi_oku` / `text_to_grid`), ardından `eokul.hazirla_personel_matrisi`
  e-Okul'a özgü dipnotları düzler, gerisi ortak. Makrolu dosya okunmadan reddedilir
  (tasarım TK18; `excel_ortak.dosyayi_oku`) ve FAILED izi bırakır.
- Idempotency UYARIDIR, ENGEL DEĞİL: aynı içerik (sha256) yeniden commit
  edilebilir — `already_imported=True` uyarısıyla MEVCUT COMPLETED `ImportRun`
  satırı güncellenir (koşullu unique bozulmaz). Aynı dosyanın ikinci uygulaması
  değişiklik üretmez.
- Önizleme deseni AYNEN: gerçek ingest (havuz yazımı dahil) atomic blokta
  koşulur ve `set_rollback(True)` ile geri alınır — %100 sonuç paritesi;
  ardından kalıcı PREVIEWED izi yazılır. Ingest zincirine `transaction.on_commit`
  EKLENEMEZ.
- Boş/çözülemeyen hücre mevcut veriyi SİLMEZ (import silmez ilkesi).
- **Denetim izi** (tasarım §4.6.2; plan F1b-1 alt commit c): her kayıt yazımı aynı
  işlemde KAYIT BAŞINA iz satırı yazar (`denetim_izi.degisiklik`): yeni personel
  `OLUSTUR`; görev türü değişikliği `GUNCELLE`; yeniden aktifleşme, havuza giriş ve havuzdan
  çıkış `DURUM` (ikisi birden değiştiyse iki satır); koşunun açılışı `OLUSTUR`, kapanışı
  `DURUM`. Değişmeyen kayıt yazılmaz, satırı da yoktur. Önizlemenin satırları veriyle
  birlikte geri sarılır; kalıcı PREVIEWED ve FAILED izleri kendi işlemlerinde `OLUSTUR`
  yazar. Kişi satırları değer taşımaz (KVKK silme kümesi); dosya adı ve rapor yalnız alan
  adıyla görünür.

VELİ LİSTESİ (T5; tasarım §8.4, plan "F1b-5 uygulama kararları"): okulun doldurduğu iki sütunlu
şablondan (`excel_veli`; .xlsx, .xls, .csv — pano yolu yoktur) `ParentRoster` satırları yazılır.

- **Sınıf bazında yerine koyma** (tasarım §8.4 (1)): dosyadaki sınıflar önceki listenin AYNI
  sınıflarının yerini alır; dosyada olmayan sınıflara dokunulmaz. Birlik dönemi F1c'de gelir; o
  güne dek "önceki parti" bütün canlı listedir. Satırlar birleştirilmez: bir satır bir öğrencidir.
- **Önizleme yalnız SAYI gösterir** (§8.4 (2)): satır ve sınıf sayısı, yerine geçecek her sınıfın
  yeni ve eski satır sayısı, dokunulmayan sınıflar, aktarılamayan satırların numarası ve nedeni.
  Raporda ad YOKTUR (API yanıtında da); hücre değeri de yoktur.
- **Kaynak sıra tutulmaz** (§5.1 `ParentRoster`): satırlar sınıf ve çözülmüş ad sırasıyla yazılır.
- **Denetim izi kişisiz parti satırıdır**: koşunun `OLUSTUR` ve `DURUM` satırları (tür `VELI`,
  içerik özeti, durum); veli satırı başına iz yazılmaz (`models.ParentRoster`). Yerine geçen eski
  satırların silinmesi aynı işlemde kişisiz `KVKK_SILME` satırıdır (tetik `AKTARIM`); "Veli
  listesini sil" de öyledir (tetik `ELLE_SILME`). Erişim günlüğüne yazılmaz (karar).
"""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from django.db import transaction
from django.db.models import Max, QuerySet
from django.utils import timezone

from apps.okul import (
    denetim_izi,
    eokul,
    excel_ortak,
    excel_personel,
    excel_veli,
    name_match,
    normalize,
    selectors,
)
from apps.okul.excel_ortak import ParserError
from apps.okul.excel_personel import ParsedPersonnelRow, PersonnelColumnMapping
from apps.okul.excel_veli import ParentRowIssue, ParsedParentRow
from apps.okul.models import (
    ImportRun,
    ImportSourceType,
    ImportStatus,
    MemberKind,
    ParentRoster,
    Personnel,
)
from apps.okul.services import app_password, persons
from shared.crypto import has_corrupt

logger = logging.getLogger("oab_defteri.okul")

#: Önizlemede "görev türünü denetleyin" uyarısı (satır no ile; ad ve görev metni yok): görev
#: hücresi boş ya da şablonun görev türü tanınmadı.
MEMBER_KIND_CHECK_MESSAGE = (
    "Görev türünü denetleyin: görev bilgisi boş ya da tanınmadı. Yeni kayıt öğretmen olarak "
    "açılır; mevcut kaydın görev türü değişmez."
)
#: Ad-soyadı boş personel satırı: kimlik anahtarı ad olduğu için havuza ekleme durur.
PERSONNEL_UNIDENTIFIED_ROW_MESSAGE = (
    "Ad-soyad boş; satır atlandı. Bu satırdaki kişi tanınamadığı için hiçbir kişi ayrılış "
    "havuzuna eklenmedi."
)
PERSONNEL_NOTHING_PROCESSED_MESSAGE = (
    "Dosyada işlenebilen personel satırı bulunamadı; hiçbir kişi ayrılış havuzuna eklenmedi."
)
#: Genel (satıra bağlı olmayan) havuz uyarılarının alan kodu (arayüz: "Ayrılış havuzu").
POOL_FIELD = "leave_pool"


@dataclass
class ImportIssue:
    """İçe aktarmada bir satır sorunu (atlama veya uyarı). Kişi adı taşımaz.

    `raw_value` hücrenin ham değeridir. Sütunları kaymış bir dosyada kişi verisi
    taşıyabilir: yalnız API yanıtında döner, kalıcı rapordan `_strip_raw_values` ile silinir.
    """

    row_number: int
    field: str
    issue: str
    raw_value: str = ""


def _strip_raw_values(veri: dict[str, Any]) -> dict[str, Any]:
    """Kalıcı `ImportRun.report` için satır sorunlarından ham hücre değerini siler."""
    for anahtar in ("warnings", "skipped"):
        for sorun in veri.get(anahtar, []):
            sorun.pop("raw_value", None)
    return veri


@dataclass
class PoolPersonnel:
    """Havuza eklenecek personel — AD İÇERİR: yalnız API yanıtında."""

    id: int
    full_name: str


@dataclass
class SimilarPair:
    """ "Olası aynı kişi": ada göre eşleşmeyen yeni satır ↔ listede olmayan kayıt.

    AD İÇERİR: yalnız API yanıtında. `new_id` yalnız uygulamada dolar (önizlemede
    yeni kayıt geri alındığı için None'dır); birleştirme `personnel/<existing_id>/merge/`
    ucuna `{into_id: new_id}` ile yapılır (aktarım sonucundan ya da ayrılış havuzundan).
    `reason` çiftin NEDEN kurulduğudur (`MatchReason` kodu): "adı aynı" adaşı da
    yakalar, kullanıcı bunu ancak gerekçeyi görürse anlar (§13 D30).
    """

    row_number: int
    row_name: str
    existing_id: int
    existing_name: str
    new_id: int | None = None
    reason: str = ""


@dataclass
class PersonnelImportReport:
    """Personel içe aktarma özeti (UI raporu; `to_run_dict` → ImportRun.report).

    Aktarım kimseyi ayırmaz: listede olmayan aktif personel ayrılış havuzuna
    girer (`pool_added_personnel`: bu aktarımla YENİ giren), listede görülen
    havuzdaki kişi çıkar (`pool_removed_personnel`).
    """

    file_hash: str
    file_name: str = ""
    total_rows: int = 0
    processed: int = 0
    created_personnel: int = 0
    updated_personnel: int = 0
    unchanged_personnel: int = 0
    #: Güncellenenlerin içinde: ayrılmışken listede yeniden görülen personel.
    reactivated_personnel: int = 0
    pool_added_personnel: int = 0
    pool_removed_personnel: int = 0
    similar_pair_count: int = 0
    already_imported: bool = False
    dry_run: bool = False
    pool_added: list[PoolPersonnel] = field(default_factory=list)
    similar_pairs: list[SimilarPair] = field(default_factory=list)
    warnings: list[ImportIssue] = field(default_factory=list)
    skipped: list[ImportIssue] = field(default_factory=list)

    def add_warning(self, row: int, field_name: str, issue: str, raw: str = "") -> None:
        self.warnings.append(ImportIssue(row, field_name, issue, raw))

    def add_skip(self, row: int, field_name: str, issue: str, raw: str = "") -> None:
        self.skipped.append(ImportIssue(row, field_name, issue, raw))

    def to_dict(self) -> dict[str, Any]:
        """API yanıtı (yönetim yüzeyi): havuza eklenecek kişilerin ve çiftlerin adları dahil."""
        return asdict(self)

    def to_run_dict(self) -> dict[str, Any]:
        """Kalıcı `ImportRun.report`: yalnız sayılar — ad listeleri ve ham hücreler ÇIKARILIR."""
        veri = asdict(self)
        veri.pop("pool_added", None)
        veri.pop("similar_pairs", None)
        return _strip_raw_values(veri)

    def summary_tr(self) -> str:
        return (
            f"Personel içe aktarma: {self.processed}/{self.total_rows} satır — "
            f"{self.created_personnel} yeni, {self.updated_personnel} güncellenen, "
            f"{self.unchanged_personnel} değişmeyen; "
            f"{self.pool_added_personnel} kişi ayrılış havuzuna eklendi, "
            f"{self.pool_removed_personnel} kişi havuzdan çıktı; "
            f"{len(self.warnings)} uyarı, {len(self.skipped)} atlanan."
        )


# ---------------------------------------------------------------------------
# Girdi normalize — dosya ve pano aynı matris biçimine iner
# ---------------------------------------------------------------------------
def file_hash(file_bytes: bytes) -> str:
    """Yüklenen dosyanın SHA256 özeti (aynı içerik tespiti için)."""
    return hashlib.sha256(file_bytes).hexdigest()


def text_hash(text: str) -> str:
    """Yapıştırılan metnin SHA256 özeti (satır sonları normalize edilir)."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def text_to_grid(text: str) -> list[list[Any]]:
    """Pano metnini satır matrisine çevirir (tab ayraçlı — Excel kopyala/yapıştır)."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [list(line.split("\t")) for line in normalized.split("\n")]


def _grid_from_file(file_bytes: bytes, file_name: str = "") -> list[list[Any]]:
    """Dosya baytlarını matrise çevirir (.xlsx, e-Okul'un .xls'i, .csv); makrolu ya da okunamayan
    dosyada ParserError (`excel_ortak.dosyayi_oku`)."""
    return excel_ortak.dosyayi_oku(file_bytes, file_name)


def _parse_personnel_grid(
    grid: list[list[Any]],
) -> tuple[PersonnelColumnMapping, list[ParsedPersonnelRow]]:
    grid, notes = eokul.hazirla_personel_matrisi(grid)
    mapping = excel_personel.detect_columns(grid)
    if not mapping.is_usable:
        missing = ", ".join(mapping.missing_critical)
        raise ParserError(f"Zorunlu sütun(lar) bulunamadı: {missing}.")
    mapping.warnings = [*notes, *mapping.warnings]
    return mapping, excel_personel.parse_rows(grid, mapping)


# ---------------------------------------------------------------------------
# ImportRun yaşam döngüsü (idempotency uyarısı + koşullu unique koruması)
# ---------------------------------------------------------------------------
def _open_run(*, source_type: str, source_hash: str, file_name: str) -> tuple[ImportRun, bool]:
    """Koşu kaydını açar → (run, zaten_tamamlanmış_mı)."""
    existing: ImportRun | None = ImportRun.objects.filter(
        source_type=source_type, file_hash=source_hash, status=ImportStatus.COMPLETED
    ).first()
    if existing is not None:
        onceki = denetim_izi.anlik(existing)
        existing.status = ImportStatus.RUNNING
        existing.started_at = timezone.now()
        existing.finished_at = None
        if file_name:
            existing.file_name = file_name
        existing.save(
            update_fields=["status", "started_at", "finished_at", "file_name", "updated_at"]
        )
        denetim_izi.degisiklik(existing, onceki=onceki)
        return existing, True
    run = ImportRun.objects.create(
        source_type=source_type,
        file_name=file_name,
        file_hash=source_hash,
        status=ImportStatus.RUNNING,
    )
    denetim_izi.degisiklik(run, onceki=None)
    return run, False


def _close_run(run: ImportRun, report_dict: dict[str, Any]) -> None:
    onceki = denetim_izi.anlik(run)
    run.status = ImportStatus.COMPLETED
    run.finished_at = timezone.now()
    run.report = report_dict
    run.save(update_fields=["status", "finished_at", "report", "updated_at"])
    denetim_izi.degisiklik(run, onceki=onceki)


# ---------------------------------------------------------------------------
# Personel içe aktarma + mutabakat
# ---------------------------------------------------------------------------
def _match_reason(row: ParsedPersonnelRow, person: Personnel) -> name_match.MatchReason | None:
    """ "Olası aynı kişi" gerekçesi (tek kural `name_match`); çift değilse None."""
    return name_match.match_reason(
        first_a=row.first_name,
        full_a=row.raw_full_name,
        first_b=person.first_name,
        full_b=person.full_name,
    )


@dataclass
class _PersonnelRun:
    report: PersonnelImportReport
    by_key: dict[str, list[Personnel]] = field(default_factory=dict)
    matched_ids: set[int] = field(default_factory=set)
    created: list[tuple[ParsedPersonnelRow, Personnel]] = field(default_factory=list)
    #: Ad-soyadı boş satır görüldü: kim olduğu bilinemediği için kimse havuza eklenmez
    #: (kimlik anahtarı addır).
    unidentified: bool = False
    #: Genel (satıra bağlı olmayan) havuz uyarılarının yazılacağı başlık satırı.
    header_row_number: int = 1


@transaction.atomic
def _ingest_personnel(
    *,
    grid: list[list[Any]],
    source_hash: str,
    file_name: str = "",
) -> PersonnelImportReport:
    """Matristeki personel satırlarını yazar ve mutabakatı uygular (ada göre eşleşme).

    Eşleşme anahtarı normalize edilmiş ad-soyaddır — ad ŞİFRELİ saklandığından
    dizin daima Python tarafında kurulur (çözülmüş değerlerle; kilitliyken API
    kapısı zaten 423 verir). Adaşlar tek tek tüketilir: aynı adı taşıyan iki
    satır iki ayrı kayda eşleşir (biri "listede yok" sayılmaz). Aktif kayıt
    ayrılmış kayıttan önce eşleşir; ayrılmış kayıt eşleşirse yeniden aktifleşir.

    Kimseyi ayırmaz ve silmez: listede olmayan aktif personel ayrılış
    havuzuna girer; karar (ayrıldı / aktif kalsın / birleştir) havuzda verilir.
    "Olası aynı kişi" çiftleri bütün listede olmayanlarla kurulur (zaten havuzda
    bekleyenler dahil).

    Havuza ekleme yalnız KANITLA yapılır (import silmez ilkesi): ad-soyadı boş bir satır görüldüyse o kişi tanınamadığı
    için hiç kimse havuza eklenmez; hiç satır işlenemeyen dosya da kimseyi
    eklemez. İki durum da önizlemede söylenir (satır no ile, ad yazılmadan).
    """
    app_password.require_password_set()
    mapping, rows = _parse_personnel_grid(grid)
    report = PersonnelImportReport(file_hash=source_hash, file_name=file_name, total_rows=len(rows))
    run, already = _open_run(
        source_type=ImportSourceType.PERSONEL, source_hash=source_hash, file_name=file_name
    )
    report.already_imported = already
    for header_warning in mapping.warnings:
        report.add_warning(mapping.header_row + 1, "header", header_warning)

    mevcut = sorted(Personnel.objects.all(), key=lambda p: (not p.is_active, p.pk))
    kosu = _PersonnelRun(report=report, header_row_number=mapping.header_row + 1)
    for person in mevcut:
        # Çözülemeyen adlı kayıt ada göre eşleşmez (tasarım §13 D48): listede bulunmamış
        # sayılır ve ayrılış havuzunda kararı bekler; adı ve yazımı değişmez.
        if not has_corrupt(person):
            kosu.by_key.setdefault(name_match.name_key(person.full_name), []).append(person)
    for row in rows:
        _process_personnel_row(row, kosu)

    listede_yok = selectors.personnel_sorted(
        p for p in mevcut if p.is_active and p.pk not in kosu.matched_ids
    )
    report.similar_pairs = [
        SimilarPair(
            row_number=row.row_number,
            row_name=row.raw_full_name,
            existing_id=person.pk,
            existing_name=person.full_name,
            new_id=new_person.pk,
            reason=str(gerekce),
        )
        for row, new_person in kosu.created
        for person in listede_yok
        if not has_corrupt(person) and (gerekce := _match_reason(row, person)) is not None
    ]
    report.similar_pair_count = len(report.similar_pairs)

    _reconcile_personnel(kosu, listede_yok, run)

    _close_run(run, report.to_run_dict())
    return report


def _reconcile_personnel(kosu: _PersonnelRun, listede_yok: list[Personnel], run: ImportRun) -> None:
    """Listede olmayan aktif personeli AYRILIŞ HAVUZUNA ekler (tasarım §5.1 `Personnel`).

    Hiç kimse ayrılmaz ve silinmez: havuza giren kişinin durumu AKTİF kalır,
    karar havuzda verilir. Zaten havuzda olan kişi yeniden sayılmaz (ilk giriş
    tarihi ve aktarımı korunur).

    Havuza ekleme yalnız KANITLA yapılır (import silmez ilkesi). Personelde
    kimlik anahtarı ad-soyaddır; sütunları kaymış ya da ad hücresi boş bir dosya
    listedeki herkesi "yok" gösterirdi. İki kapı vardır: hiç satır işlenemeyen
    dosya kimseyi eklemez, ad-soyadı boş bir satır görülen dosya da eklemeyi
    tümüyle durdurur.
    """
    report = kosu.report
    if report.processed == 0:
        report.add_warning(kosu.header_row_number, POOL_FIELD, PERSONNEL_NOTHING_PROCESSED_MESSAGE)
        return
    if kosu.unidentified:
        return  # gerekçe satır satır söylendi (PERSONNEL_UNIDENTIFIED_ROW_MESSAGE)
    for person in listede_yok:
        if persons.add_to_leave_pool(person, run=run):
            report.pool_added.append(PoolPersonnel(id=person.pk, full_name=person.full_name))
            report.pool_added_personnel += 1


def _process_personnel_row(row: ParsedPersonnelRow, kosu: _PersonnelRun) -> None:
    """Tek personel satırı: ada göre bul/oluştur; boş hücre mevcut veriyi silmez.

    Bulunan aktif kişi ayrılış havuzundaysa havuzdan çıkar. Ad-soyadı boş satır
    atlanır ve havuza eklemeyi durdurur: kişi tanınamadığı için listede olmayan
    herhangi biri olabilir (`_reconcile_personnel`).
    """
    report = kosu.report
    if not row.first_name and not row.last_name:
        kosu.unidentified = True
        report.add_skip(row.row_number, "full_name", PERSONNEL_UNIDENTIFIED_ROW_MESSAGE)
        return
    if row.member_kind_unrecognized:
        report.add_warning(row.row_number, "member_kind", MEMBER_KIND_CHECK_MESSAGE)

    adaylar = [
        p
        for p in kosu.by_key.get(name_match.name_key(row.raw_full_name), [])
        if p.pk not in kosu.matched_ids
    ]
    if not adaylar:
        person = Personnel.objects.create(
            first_name=row.first_name,
            last_name=row.last_name,
            member_kind=row.member_kind or MemberKind.OGRETMEN,
        )
        denetim_izi.degisiklik(person, onceki=None)
        kosu.created.append((row, person))
        kosu.matched_ids.add(person.pk)
        report.created_personnel += 1
        report.processed += 1
        return

    person = adaylar[0]
    changed: list[str] = []
    reactivated = not person.is_active
    if reactivated:
        persons.reactivate_personnel(person)
        changed += ["is_active", "left_at"]
    if row.member_kind and person.member_kind != row.member_kind:
        person.member_kind = row.member_kind
        changed.append("member_kind")
    havuzdan = persons.remove_from_leave_pool(person, save=False)
    yazilacak = [*changed, *(persons.POOL_FIELDS if havuzdan else ())]
    if yazilacak:
        # Önceki hâl veritabanından okunur: bellekteki örnek yukarıda değişti.
        onceki = denetim_izi.anlik(person)
        person.save(update_fields=[*yazilacak, "updated_at"])
        denetim_izi.degisiklik(person, onceki=onceki)
    if changed:
        report.updated_personnel += 1
        if reactivated:
            report.reactivated_personnel += 1
    else:
        report.unchanged_personnel += 1
    if havuzdan:
        report.pool_removed_personnel += 1
    kosu.matched_ids.add(person.pk)
    report.processed += 1


# ---------------------------------------------------------------------------
# Kamu API — dosya ve pano girişleri (preview/commit)
# ---------------------------------------------------------------------------
def commit_personnel_file(*, file_bytes: bytes, file_name: str = "") -> PersonnelImportReport:
    return _personnel_entry(
        lambda: _grid_from_file(file_bytes, file_name),
        file_hash(file_bytes),
        file_name,
        preview=False,
    )


def commit_personnel_text(*, text: str) -> PersonnelImportReport:
    return _personnel_entry(lambda: text_to_grid(text), text_hash(text), "", preview=False)


def preview_personnel_file(*, file_bytes: bytes, file_name: str = "") -> PersonnelImportReport:
    return _personnel_entry(
        lambda: _grid_from_file(file_bytes, file_name),
        file_hash(file_bytes),
        file_name,
        preview=True,
    )


def preview_personnel_text(*, text: str) -> PersonnelImportReport:
    return _personnel_entry(lambda: text_to_grid(text), text_hash(text), "", preview=True)


def _personnel_entry(
    grid_supplier: Callable[[], list[list[Any]]],
    source_hash: str,
    file_name: str,
    *,
    preview: bool,
) -> PersonnelImportReport:
    """Ortak giriş: ParserError'da kalıcı FAILED izi bırakır ve hatayı yükseltir.

    Ingest atomiktir — hata rollback'i RUNNING satırını da siler; FAILED izi bu
    yüzden ingest işleminin DIŞINDA, kendi işleminde yazılır (geçmiş görünümü boş
    kalmasın; iz satırı ile aynı işlemde).
    """
    try:
        grid = grid_supplier()
        if preview:
            return _preview_personnel(grid=grid, source_hash=source_hash, file_name=file_name)
        report = _ingest_personnel(grid=grid, source_hash=source_hash, file_name=file_name)
    except ParserError as exc:
        _record_failed(ImportSourceType.PERSONEL, source_hash, file_name, exc)
        raise
    # Günlüğe yalnız sayılar (kişi adı yok — sözlük §5).
    logger.info(
        "Personel aktarımı uygulandı: %d yeni, %d güncellenen, %d değişmeyen; "
        "ayrılış havuzuna %d eklendi, havuzdan %d çıktı.",
        report.created_personnel,
        report.updated_personnel,
        report.unchanged_personnel,
        report.pool_added_personnel,
        report.pool_removed_personnel,
    )
    return report


def _preview_personnel(
    *, grid: list[list[Any]], source_hash: str, file_name: str = ""
) -> PersonnelImportReport:
    """Personel aktarımını YAZMADAN simüle eder (gerçek ingest + mutabakat + rollback)."""
    with transaction.atomic():
        report = _ingest_personnel(grid=grid, source_hash=source_hash, file_name=file_name)
        transaction.set_rollback(True)
    report.dry_run = True
    # Önizlemenin açtığı yeni kayıtlar geri alındı: kimlikleri anlamsızdır.
    for pair in report.similar_pairs:
        pair.new_id = None
    _record_preview(ImportSourceType.PERSONEL, report.file_hash, file_name, report.to_run_dict())
    return report


@transaction.atomic
def _record_preview(
    source_type: str, source_hash: str, file_name: str, report_dict: dict[str, Any]
) -> None:
    """Kalıcı PREVIEWED izi (geçmiş görünümü) — geri sarılan işlemin DIŞINDA, kendi
    işleminde iz satırıyla yazılır; ad içermez."""
    run = ImportRun.objects.create(
        source_type=source_type,
        file_name=file_name,
        file_hash=source_hash,
        status=ImportStatus.PREVIEWED,
        finished_at=timezone.now(),
        report=report_dict,
    )
    denetim_izi.degisiklik(run, onceki=None)


@transaction.atomic
def _record_failed(source_type: str, source_hash: str, file_name: str, error: Exception) -> None:
    """Kalıcı FAILED izi (kendi işleminde, iz satırıyla). `error` metni yalnız yapısal
    bilgidir (sütun adları) — PII yok."""
    run = ImportRun.objects.create(
        source_type=source_type,
        file_name=file_name,
        file_hash=source_hash,
        status=ImportStatus.FAILED,
        finished_at=timezone.now(),
        report={"error": str(error)},
    )
    denetim_izi.degisiklik(run, onceki=None)


# ---------------------------------------------------------------------------
# Veli listesi (T5; tasarım §8.4) — sınıf bazında yerine koyma, önizlemede yalnız sayılar
# ---------------------------------------------------------------------------
@dataclass
class ParentClassImpact:
    """Dosyadaki bir sınıfın etkisi: yeni satır sayısı ve yerine geçen eski satır sayısı."""

    student_class: str
    rows: int
    replaced_rows: int


@dataclass
class ParentImportReport:
    """Veli listesi aktarımının raporu — YALNIZ SAYILAR (tasarım §8.4 (2)); ad ve hücre değeri yok.

    API yanıtı ile kalıcı `ImportRun.report` aynıdır (`to_dict` = `to_run_dict`): sınıf adları
    ("10-A") kişisel veri değildir, satır sorunları yalnız satır no ve neden taşır.
    """

    file_hash: str
    file_name: str = ""
    #: Dosyadaki dolu veri satırları (aktarılabilir + aktarılamayan).
    total_rows: int = 0
    #: Aktarılabilir (aktarılan) satırlar.
    imported_rows: int = 0
    #: Dosyadaki sınıf sayısı (yerine geçecek sınıflar).
    class_count: int = 0
    #: Dosyadaki sınıfların listeden silinen (silinecek) eski satırları.
    replaced_rows: int = 0
    #: Dosyada olmayan, dokunulmayan sınıflar ve satırları.
    kept_class_count: int = 0
    kept_rows: int = 0
    already_imported: bool = False
    dry_run: bool = False
    classes: list[ParentClassImpact] = field(default_factory=list)
    #: Aktarılamayan satırlar ve başlık uyarıları (satır no, alan kodu, neden).
    issues: list[ParentRowIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_run_dict(self) -> dict[str, Any]:
        return asdict(self)


def _veli_satirlarini_sil(silinecek: QuerySet[ParentRoster], *, tetik: str) -> int:
    """Veli satırlarını katı siler ve aynı işlemde kişisiz `KVKK_SILME` satırını yazar.

    Silinen sayı ve en yeni satırın günü (Europe/Istanbul) izdedir; ad ve sınıf yoktur (tasarım
    §4.6.2 kural 4). Silinecek satır yoksa ne siler ne yazar. Çağıranın işlemindedir.
    """
    en_yeni = silinecek.aggregate(en_yeni=Max("created_at"))["en_yeni"]
    if en_yeni is None:
        return 0
    adet, _ = silinecek.delete()
    denetim_izi.kvkk_silme(
        ParentRoster, adet=adet, en_yeni=timezone.localdate(en_yeni), tetik=tetik
    )
    return adet


def delete_parent_roster() -> int:
    """ "Veli listesini sil" (program yöneticisi; tasarım §5.4: genel kuruldan sonra elle de
    silinebilir): BÜTÜN liste katı silinir, kişisiz `KVKK_SILME` satırı yazılır (tetik
    `ELLE_SILME`; KVKK md. 4/2-ç, 7). Liste boşsa hiçbir şey yazılmaz. Dönem kapanışının silmesi
    F4'tedir.

    Silinen satır sayısını döndürür. Aktarım partilerinin `ImportRun` satırları kalır (yalnız
    sayı taşırlar).
    """
    app_password.require_password_set()
    with transaction.atomic():
        adet = _veli_satirlarini_sil(
            ParentRoster.objects.all(), tetik=denetim_izi.KVKK_TETIK_ELLE_SILME
        )
    # Günlüğe yalnız sayı (kişi adı yok — sözlük §5).
    logger.info("Veli listesi silindi: %d satır.", adet)
    return adet


def _siniflari_yerine_koy(
    run: ImportRun, sinifa_gore: dict[str, list[ParsedParentRow]]
) -> dict[str, int]:
    """Dosyadaki sınıfların eski satırlarını siler, yenilerini yazar → sınıf → eski satır sayısı.

    Satırlar sınıf ve çözülmüş ad sırasıyla yazılır: kaynak dosyadaki sıra tutulmaz (tasarım
    §5.1 `ParentRoster`). Kör indeks `save()`'te dolar: toplu yazım yoktur (`create`).
    """
    eski = ParentRoster.objects.filter(student_class__in=list(sinifa_gore))
    eski_sayilari = Counter(eski.values_list("student_class", flat=True))
    en_yeni = eski.aggregate(en_yeni=Max("created_at"))["en_yeni"]
    if en_yeni is not None:
        adet, _ = eski.delete()
        denetim_izi.kvkk_silme(
            ParentRoster,
            adet=adet,
            en_yeni=timezone.localdate(en_yeni),
            tetik=denetim_izi.KVKK_TETIK_AKTARIM,
        )
    for sinif in sorted(sinifa_gore, key=excel_veli.sinif_sira_anahtari):
        for row in sorted(sinifa_gore[sinif], key=lambda r: normalize.tr_sort_key(r.full_name)):
            ParentRoster.objects.create(
                import_run=run, full_name=row.full_name, student_class=sinif
            )
    return dict(eski_sayilari)


@transaction.atomic
def _ingest_parents(
    *, grid: list[list[Any]], source_hash: str, file_name: str = ""
) -> ParentImportReport:
    """Veli listesini yazar: dosyadaki sınıflar yerine konur, ötekilere dokunulmaz (§8.4 (1)).

    Denetim izi kişisiz parti satırıdır: koşunun açılışı (`OLUSTUR`) ve kapanışı (`DURUM`);
    yerine geçen eski satırların silinmesi `KVKK_SILME` (tetik `AKTARIM`).
    """
    app_password.require_password_set()
    mapping, rows, issues = excel_veli.parse_grid(grid)
    report = ParentImportReport(file_hash=source_hash, file_name=file_name)
    report.issues = [
        *(ParentRowIssue(mapping.header_row + 1, "header", uyari) for uyari in mapping.warnings),
        *issues,
    ]
    report.total_rows = len({r.row_number for r in rows} | {i.row_number for i in issues})
    report.imported_rows = len(rows)
    run, already = _open_run(
        source_type=ImportSourceType.VELI, source_hash=source_hash, file_name=file_name
    )
    report.already_imported = already

    sinifa_gore: dict[str, list[ParsedParentRow]] = {}
    for row in rows:
        sinifa_gore.setdefault(row.student_class, []).append(row)
    eski_sayilari = _siniflari_yerine_koy(run, sinifa_gore)
    report.classes = [
        ParentClassImpact(sinif, len(sinifa_gore[sinif]), eski_sayilari.get(sinif, 0))
        for sinif in sorted(sinifa_gore, key=excel_veli.sinif_sira_anahtari)
    ]
    report.class_count = len(report.classes)
    report.replaced_rows = sum(eski_sayilari.values())
    kalan = ParentRoster.objects.exclude(student_class__in=list(sinifa_gore))
    report.kept_rows = kalan.count()
    report.kept_class_count = kalan.values("student_class").distinct().count()

    _close_run(run, report.to_run_dict())
    return report


def preview_parents_file(*, file_bytes: bytes, file_name: str = "") -> ParentImportReport:
    return _parents_entry(file_bytes, file_name, preview=True)


def commit_parents_file(*, file_bytes: bytes, file_name: str = "") -> ParentImportReport:
    return _parents_entry(file_bytes, file_name, preview=False)


def _parents_entry(file_bytes: bytes, file_name: str, *, preview: bool) -> ParentImportReport:
    """Ortak giriş (personelinkiyle aynı sözleşme): ParserError'da kalıcı FAILED izi.

    Önizleme gerçek yazımı atomic blokta koşar ve geri sarar (%100 parite), ardından kalıcı
    PREVIEWED izini yazar (`_record_preview`).
    """
    source_hash = file_hash(file_bytes)
    try:
        grid = _grid_from_file(file_bytes, file_name)
        if preview:
            with transaction.atomic():
                report = _ingest_parents(grid=grid, source_hash=source_hash, file_name=file_name)
                transaction.set_rollback(True)
            report.dry_run = True
            _record_preview(ImportSourceType.VELI, source_hash, file_name, report.to_run_dict())
            return report
        report = _ingest_parents(grid=grid, source_hash=source_hash, file_name=file_name)
    except ParserError as exc:
        _record_failed(ImportSourceType.VELI, source_hash, file_name, exc)
        raise
    # Günlüğe yalnız sayılar (kişi adı yok — sözlük §5).
    logger.info(
        "Veli listesi aktarımı uygulandı: %d satır, %d sınıf; %d eski satırın yerine geçti, "
        "%d satır aktarılamadı.",
        report.imported_rows,
        report.class_count,
        report.replaced_rows,
        report.total_rows - report.imported_rows,
    )
    return report
