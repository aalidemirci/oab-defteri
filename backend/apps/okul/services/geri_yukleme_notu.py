"""Geri yükleme notu — `geri-yukleme-notu.json` (tasarım §4.4.4, §4.6.3; plan F1b-1 alt commit c).

Geri yükleme veritabanını başkasıyla değiştirir: kenara alınan veritabanına iz satırı
yazılamaz, yenisinde oturum yoktur ve `iz-durumu.json`'daki çapa artık o veritabanını
anlatmaz. Ortak geri yükleme çekirdeği (`backup_restore.restore_database`; uygulama içi
geri yükleme, konsol `--geri-yukle` ve `manage.py restore_backup` aynı yoldan geçer) bu
yüzden olguları bu nota yazar. Not ilk kilit açılışında denetim izine `GERI_YUKLEME` satırı
olarak geçer; notun kaydettiği zincir başı çapayı açıklıyorsa çapa uyarısının yerine,
açıklamıyorsa uyarıyla birlikte (`apps.okul.iz_dogrulama`, tasarım §4.6.3 (1)); çapa
yenilenir, iki depo karşılaştırılır (tasarım §4.6.1 kural 4).

İÇERİK (tasarım §4.4.4)::

    {"surum": 1,
     "geri_yuklemeler": [{
         "zaman": "<yerel ISO>",
         "yedek": "<yedeğin dosya adı>",
         "onceki": {"dosya": "db-onceki-<damga>.sqlite3", "sha256": "…",
                    "zincir_basi": {"seq": N, "mac": "…"} | {"seq": 0, "mac": ""} | null}
                   | null,
         "yol": {"tur": "hesap", "hesap": "<kimlik>", "tanitici": "…"}
              | {"tur": "kurtarma", "no": N},
         "capa": {"seq": N, "mac": "…"} | null,
         "oturum": "<uygulama içi geri yüklemede oturumdaki hesabın kimliği>"}],
     "bekleyen_olaylar": [{"eylem", "model", "object_id", "changed_fields", "values",
                           "zaman": "<yerel ISO>"}]}

* İki geri yükleme arasında kilit açılmazsa ikincisi LİSTEYE eklenir: ilk kenara alınan
  veritabanı asıl dönüş yoludur, bilgisi ezilmez. Çapa da onu anlatır: ilk kilit açılışı
  çapayı İLK kaydın zincir başıyla karşılaştırır (`iz_dogrulama`, tasarım §4.6.3 (1)).
* Not varken kilitli satır yazılmaz (tasarım §4.6.3): çapa eski veritabanınındır. O açılışın
  sistem olayları (günlük yedek, şema göçü, ertelenen gün işi) `bekleyen_olaylar`'a eklenir
  ve ilk kilit açılışında açık anahtarla `SISTEM` satırı olarak yazılır (`iz_durumu`). Olay
  nota eklendiği anı taşır (`zaman`): satırın anı ilk kilit açılışınındır, olayın kendi anı
  satıra izinli değer olarak girer.
* Takastan ÖNCE `iz-durumu.json`'daki çapa da yazılır (`capa`; mühür ve tohum YAZILMAZ): dosya
  yoksa `null` ("çapa yoktu"), okunamıyorsa alan hiç yazılmaz ("bilinmiyor"). Kurulumdan sonra
  hiç kilitlenmeden yapılan geri yüklemede çapa yoktur ve kenara alınan veritabanının zinciri
  doludur: ilk kilit açılışı "not yazılırken çapa yoktu, şimdi de yok" hâlini notun açıkladığı
  durum sayar, "çapa yok" uyarısı vermez (`iz_dogrulama`).
* Kenara alınan veritabanının zincir başı ORM'siz okunur: takastan ÖNCE, salt okunur
  `sqlite3` bağlantısıyla (`mode=ro`). İz boşsa `{"seq": 0, "mac": ""}` (ilk satırın
  `prev_mac`'i gibi: "zincir yoktu"), tablo yoksa ya da dosya okunamıyorsa `null`
  ("bilinmiyor"); kenara alınacak dosya hiç yoksa `onceki` `null`dır. Zincir başı izde kaldığı
  için kâğıt çapasıyla sonradan da karşılaştırılabilir (§4.4.4).
* Tanıtıcı notta durur (yerel dosya: program yöneticisi hangi hesabın parolasıyla geri
  yükledi), iz satırına GİRMEZ — kişinin adını içerebilir; satır hesabın kimliğini taşır.
* Uygulama içi geri yüklemede oturumdaki hesabın kimliği de notta durur (`oturum`; kurtarma
  anahtarı yolunda da): geri yükleme, onu başlatan oturumun hesabına bağlanır (Hakkında
  "Açık oturum, sahibinin imzasıdır"). Konsol geri yüklemesinde oturum yoktur, alan yazılmaz.
* Bozuk not okunamadı sayılır (`NotOkunamadi`): ilk kilit açılışı yine `GERI_YUKLEME`
  satırı yazar (ayrıntısız) ve notu siler. Bozuk notun üstüne yeni olgu yazılırken eski
  içerik kurtarılamaz; yeni not `bozuk_not_vardi` işaretini taşır.

Not ilk kilit açılışının veritabanı işlemi commit edildikten SONRA silinir (`tuket`): işlem
düşerse not kalır, sonraki açılış yeniden dener. Dosya `guvenlik.json`'la aynı dizindedir ve
atomik yazılır (`apps.okul.gizli_dosya`). Modül ORM kullanmaz.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from django.utils import timezone

from apps.okul.gizli_dosya import atomik_json_yaz
from shared import sqlite_adres

DOSYA_ADI: Final = "geri-yukleme-notu.json"
SURUM: Final = 1
#: Bozuk bir notun üzerine yazılan yeni notun işareti (modül başlığı).
BOZUK_NOT_ISARETI: Final = "bozuk_not_vardi"

#: Yol türleri (`yol.tur`).
YOL_HESAP: Final = "hesap"
YOL_KURTARMA: Final = "kurtarma"

#: İzi boş veritabanının zincir başı: "zincir yoktu" (modül başlığı; ilk satırın `prev_mac`'i).
BOS_ZINCIR: Final[dict[str, Any]] = {"seq": 0, "mac": ""}

#: Takastan önceki çapa okunamadı: kayıtta `capa` alanı yazılmaz (modül başlığı).
CAPA_BILINMIYOR: Final = "bilinmiyor"


class NotOkunamadi(ValueError):
    """Geri yükleme notu var ama okunamıyor ya da beklenen biçimde değil."""


def an_metni() -> str:
    """Notun anları (geri yüklemenin ve bekleyen olayın): yerel saat, saat dilimli ISO."""
    return timezone.localtime().isoformat(timespec="seconds")


def zaman_coz(deger: Any) -> datetime | None:
    """Notun bir `zaman` alanı (ISO, saat dilimli) → an; biçimsizse `None`.

    Not dosyası program dışından değiştirilebilir: saat dilimsiz ya da çözülemeyen metin
    satıra girmez (kanonik biçim saat dilimli zaman ister; satıra UTC `Z` metni olarak girer).
    """
    if not isinstance(deger, str):
        return None
    try:
        an = datetime.fromisoformat(deger)
    except ValueError:
        return None
    return an if an.tzinfo is not None else None


def yol(dizin: Path) -> Path:
    """Notun yolu: `guvenlik.json`'la aynı dizin (plan F1b-1)."""
    return dizin / DOSYA_ADI


def var_mi(dizin: Path) -> bool:
    """Not var mı? (okunabilir olup olmadığına bakmaz)"""
    return yol(dizin).exists()


def _bos() -> dict[str, Any]:
    return {"surum": SURUM, "geri_yuklemeler": [], "bekleyen_olaylar": []}


def oku(dizin: Path) -> dict[str, Any] | None:
    """Notu okur; yoksa None, bozuksa `NotOkunamadi`.

    Derin iç içe JSON (`json.loads`'un `RecursionError`'ı) da bozuk nottur (aile kuralı;
    `app_password.read_state`): yoksa geri yükleme takastan SONRA notu yazarken düşer, her açılışta
    da notun okunması iz doğrulamasını keserdi.
    """
    dosya = yol(dizin)
    if not dosya.exists():
        return None
    try:
        veri: Any = json.loads(dosya.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise NotOkunamadi("Geri yükleme notu okunamadı.") from exc
    if (
        not isinstance(veri, dict)
        or veri.get("surum") != SURUM
        or not isinstance(veri.get("geri_yuklemeler"), list)
        or not isinstance(veri.get("bekleyen_olaylar"), list)
    ):
        raise NotOkunamadi("Geri yükleme notu beklenen biçimde değil.")
    return veri


def _guncel_ya_da_bos(dizin: Path) -> dict[str, Any]:
    """Var olan not (eklemek için) ya da boş not; bozuk not işaretli boş nota döner."""
    try:
        veri = oku(dizin)
    except NotOkunamadi:
        bos = _bos()
        bos[BOZUK_NOT_ISARETI] = True
        return bos
    return veri if veri is not None else _bos()


def geri_yukleme_kaydi(
    *,
    yedek: str,
    onceki_dosya: str | None,
    onceki_sha256: str | None,
    onceki_zincir_basi: dict[str, Any] | None,
    yol_bilgisi: dict[str, Any],
    oturum_hesabi: str | None = None,
    onceki_capa: dict[str, Any] | str | None = CAPA_BILINMIYOR,
) -> dict[str, Any]:
    """Bir geri yüklemenin notdaki kaydı (modül başlığındaki biçim).

    `onceki_capa`: takastan önceki çapa `{seq, mac}`, yoksa None; `CAPA_BILINMIYOR` ise
    alan yazılmaz.
    """
    onceki: dict[str, Any] | None = None
    if onceki_dosya is not None:
        onceki = {
            "dosya": onceki_dosya,
            "sha256": onceki_sha256,
            "zincir_basi": onceki_zincir_basi,
        }
    kayit: dict[str, Any] = {
        "zaman": an_metni(),
        "yedek": yedek,
        "onceki": onceki,
        "yol": dict(yol_bilgisi),
    }
    if onceki_capa != CAPA_BILINMIYOR:
        kayit["capa"] = onceki_capa
    if oturum_hesabi:
        kayit["oturum"] = str(oturum_hesabi)
    return kayit


def geri_yukleme_ekle(dizin: Path, kayit: dict[str, Any]) -> None:
    """Geri yüklemenin kaydını nota ekler (not yoksa oluşturur); atomik yazım."""
    veri = _guncel_ya_da_bos(dizin)
    veri["geri_yuklemeler"].append(kayit)
    atomik_json_yaz(yol(dizin), veri)


def bekleyen_olay_ekle(dizin: Path, olay: dict[str, Any]) -> None:
    """Not varken yazılamayan kilitli kip olayını nota ekler (ilk kilit açılışında yazılır).

    Olay eklendiği anı taşır (`zaman`; verilmişse korunur): ilk kilit açılışı onu satıra
    izinli değer olarak yazar, gün işi ertelemesinin "günde bir" kuralı da ona bakar.
    """
    kayit = dict(olay)
    if not kayit.get("zaman"):
        kayit["zaman"] = an_metni()
    veri = _guncel_ya_da_bos(dizin)
    veri["bekleyen_olaylar"].append(kayit)
    atomik_json_yaz(yol(dizin), veri)


def tuket(dizin: Path) -> None:
    """İlk kilit açılışının işlemi commit edildikten sonra notu siler."""
    yol(dizin).unlink(missing_ok=True)


def zincir_basi_oku(db_path: Path) -> dict[str, Any] | None:
    """Veritabanının zincir başı `{seq, mac}` — salt okunur `sqlite3`, ORM'siz (§4.4.4).

    İz boşsa `BOS_ZINCIR` ("zincir yoktu": kurulumdan hemen sonra yapılan geri yükleme, yeni
    bilgisayara taşıma). Dosya yoksa, tablo yoksa ya da dosya okunamıyorsa (bozuk
    veritabanı konsol geri yüklemesinin varlık sebebidir) None: zincir başı bilinmiyor.
    """
    if not db_path.is_file():
        return None
    # Adres `geri_yukleme_yetkisi` ile ortaktır (`shared.sqlite_adres`): `resolve()` edilmez,
    # UNC yol authority'siz yazılır; yoksa ağdaki veri dizininde zincir başı "bilinmiyor" kalırdı.
    adres = sqlite_adres.salt_okunur_adres(db_path)
    try:
        with closing(sqlite3.connect(adres, uri=True, timeout=5)) as baglanti:
            satir = baglanti.execute(
                "SELECT seq, mac FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
            ).fetchone()
    except sqlite3.Error:
        return None
    if satir is None:
        return dict(BOS_ZINCIR)
    seq, mac = satir
    if isinstance(seq, bool) or not isinstance(seq, int) or not isinstance(mac, str):
        return None
    return {"seq": seq, "mac": mac}


def dosya_ozeti(dosya: Path) -> str:
    """Dosyanın sha256'sı (onaltılık); kenara alınan veritabanının özeti (§4.4.4)."""
    ozet = hashlib.sha256()
    with dosya.open("rb") as akim:
        for parca in iter(lambda: akim.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest()
