"""Çalışan program içinden yedekten geri yükleme (Güvenlik sekmesi — API ayağı).

Dosya değişimini `backup_restore` çekirdeği yapar; bu modül ÇALIŞAN sunucuya
özgü tesisatı ekler ve view'a tek kapı sunar:

* yedek listesi — `app_password.backup_dir()` içindeki `.odbak` dosyaları
  (masaüstü `desktop/restore.py::list_backups` ile aynı kaynak, en yeniden
  eskiye) ve her birini açan kurtarma anahtarının kimliği (gömülü başlıktan, TK10);
* kullanıcının YÜKLEDİĞİ dosyanın geçici yazımı (`YedekYuklemeIsleyicisi`; plan F1b-3 "Dosya
  deposu"): gövde yedek dizinindeki `.yukleme-<hex>.tmp`'ye (0600) parça parça akar, belleğe
  alınmaz, genel yükleme sınırına takılmaz (yedek şifrelidir, açık kopya değildir). Geçici dosya
  uç bitince her durumda silinir, kullanıcının elindeki asıl dosya zaten kendindedir. Silinemezse
  yanıt değişmez, artığı açılış temizliği toplar;
* takas öncesi Django bağlantılarının kapatılması — Windows'ta SQLite dosyayı
  FILE_SHARE_DELETE olmadan açar; açık bağlantı varken `os.replace` erişim
  hatasıyla düşer (Linux'ta düşmez ama bağlantı eski dosyada asılı kalırdı);
* bakım kapısı: uçuştaki iş süresinde bitmezse takas yapılmaz, kapı yeniden açılır ve ileti
  "süren bir yedekleme ya da gün işi var" der (plan F1b-3 "Geri yükleme");
* başarıda anahtarın bellekten düşürülmesi + "yeniden başlat" kapısının
  kurulması (`restart_gate`): bellekteki DEK ve süreç durumu geri yüklenen
  veriye ait değildir, bekleyen göçler ancak açılışta koşar — sunucu bu
  hâliyle çalışmaya devam EDEMEZ.

Masaüstü kardeşi `desktop/restore.py` bozuk-veritabanı senaryosudur (pencere
hiç açılmadan `--geri-yukle`); bu modül programın AÇILABİLDİĞİ senaryo içindir
(yanlış veri girişi sonrası eski güne dönme; güvenlik dosyası kayıp kilidinden
çıkış — iki uç da o kilitte açıktır, `lock_middleware`). Yedekler daima
şifrelidir (düz yedek dalı yok, §13 D29); bir hesabın parolası ya da kurtarma
anahtarı gerekir. Parola/kurtarma anahtarı yalnız parametre olarak akar; hiçbir
günlük satırına ve hata metnine yazılmaz.

YETKİ (tasarım §4.4.4 "Geri yükleme yetkisi"; plan F1b-2). Uygulama içi geri yükleme
rol kapısından geçer (`RolMiddleware`: açık oturumda yalnız program yöneticisi). Servisin
kendi denetimi YALNIZ PAROLA YOLUNDADIR: parolası verilen hesap isteğin yazarı olan hesap
olmalıdır ve rolü program yöneticisidir (`rol_izinleri.Eylem.GERI_YUKLEME`; değilse 403
`rol_yetkisiz`); hesap verilmezse yazarın hesabı kullanılır, başka hesabın parolası geçmez
(400). Yazar yoksa (oturum yok) parola yolu reddedilir. Oturumdaki hesap `OTURUM`'dan değil
yazar bağlamından okunur: rol kararı, parolanın hesabı ve geri yüklemenin bağlandığı oturum
aynı görüntüdür. KURTARMA ANAHTARI YOLUNDA ROL DENETİMİ YOKTUR (konsolla aynı; anahtarın
kendisi yetkidir): güvenlik dosyası kayıp kilidinde oturumsuz ya da açık kalmış bir organ
oturumuyla da çıkış yolu açık kalır (rol kapısı o kipte kesmez, kilit kapısının listesi
geçerlidir; plan F1b-1 "Kayıp dosya kipinde yedekten geri yükleme yalnız kurtarma anahtarı
ister"). Parola yolunda çekirdek de hesabı konsoldaki gibi ORM'siz doğrular
(`backup_restore` → `geri_yukleme_yetkisi`; bağlantılar kapatıldıktan sonra, salt okunur):
oturumdaki program yöneticisinin kaydı tutmazsa (ör. program dışından değiştirilmişse) ret
`GeriYuklemeYetkisiz`'dir, bir `ValueError` olduğu için 400 döner; hiçbir dosya değişmez.

BOZUK EK (kullanıcı kararı 04.11.2026 "Bozuk ekte geri yükleme durur, ikinci onayla sürer"):
çekirdek `EkOnayiGerekli` ile durunca hiçbir şey değişmez, kapı kurulmaz, bakım kapısı açılır; uç
kişisiz yapılandırılmış yanıt döner. İkinci onay durumsuzdur: istek aynı yedekle ve
`ekler_olmadan_surdur` ile yeniden gelir, doğrulama baştan koşar, yüklenen dosya arada saklanmaz.

Geri yükleme UZUN İŞTİR (`shared.bakim.UZUN_ISLER`; tasarım §4.2, §4.4.3): sürerken
oturumun boşta ve elle kilidi ertelenir, DEK işin ortasında silinmez. Başarıda oturum
burada HEMEN kapanır (`app_password.lock`): DEK artık bu veritabanına ait değildir.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, Final, cast
from uuid import uuid4

from desktop.backup_crypto import (
    BACKUP_SUFFIX,
    BackupCryptoError,
    kap_basligini_oku,
    parse_security_state,
    read_embedded_recovery_metadata,
    recovery_key_identity,
    yeni_yedek_dosyasi,
)
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.files.uploadhandler import FileUploadHandler
from django.db import connections
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.okul import restart_gate, rol_izinleri
from apps.okul.oturum import yazar
from apps.okul.services import app_password, backup_restore, geri_yukleme_ekleri
from shared import bakim

logger = logging.getLogger("oab_defteri.restore")

#: Uçuştaki gün işinin bitmesi için en çok bekleme (sn).
BAKIM_BEKLEME_SN = 10.0
#: Bakım kapısının süresi doldu: takas yapılmadı (plan F1b-3 "Geri yükleme").
BAKIM_SURUYOR = (
    "Süren bir yedekleme ya da gün işi var; geri yükleme yapılmadı. Biraz sonra yeniden deneyin."
)
#: Yüklenen yedeğin geçici dosyasının öneki ve eki: `.odbak` BİLEREK değildir, rotasyon ve liste
#: yalnız o uzantıya bakar, yarım kalan dosya yedek sanılmamalı. Artığı açılış temizliği toplar.
YUKLEME_ONEKI: Final = ".yukleme-"
YUKLEME_EKI: Final = ".tmp"
#: Yüklenen yedek diske yazılamadı.
YEDEK_YAZILAMADI: Final = "Yedek dosyası yazılamadı; diskte yer olduğundan emin olun."


#: Parola yolunda başka hesabın parolası (sözlük: kod yok, "hesap" ve "oturum").
PAROLA_YALNIZ_OTURUM_HESABI = "Parola yalnız oturumdaki hesap için doğrulanır."
#: Oturum yokken parola yolu (kayıp kilidi ya da kurulum).
PAROLA_YOLU_OTURUM_ISTER = (
    "Parolayla geri yükleme yalnız açık oturumda, program yöneticisi hesabıyla yapılır; "
    "yedeği kurtarma anahtarıyla açın."
)


class LiveRestoreError(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata (view katmanı 400'e çevirir)."""


class YuklenenYedek(UploadedFile):
    """Akışla diske inmiş yedek: içeriği bellekte değil `yol`'dadır."""

    def __init__(self, akis: IO[bytes], yol: Path, ad: str, boyut: int) -> None:
        super().__init__(akis, name=ad, size=boyut)
        self.yol = yol


class YedekYuklemeIsleyicisi(FileUploadHandler):
    """Yedek yüklemesinin işleyicisi: gövdeyi `.yukleme-<hex>.tmp`'ye akıtır (modül başlığı).

    Bir istekte birden çok dosya gelebilir: her biri kaydedilir, `temizle` hepsini siler. Ucu çağıran
    her çıkış yolunda `temizle`'yi çağırır; kesilen yükleme kendi dosyasını da bırakmaz.
    """

    def __init__(self, request: Any = None) -> None:
        super().__init__(request)
        self._yollar: list[Path] = []
        self._akis: IO[bytes] | None = None

    def new_file(self, *args: Any, **kwargs: Any) -> None:
        super().new_file(*args, **kwargs)
        dizin = app_password.backup_dir()
        yol = dizin / f"{YUKLEME_ONEKI}{uuid4().hex}{YUKLEME_EKI}"
        try:
            dizin.mkdir(parents=True, exist_ok=True)
            self._akis = yeni_yedek_dosyasi(yol)
        except OSError as exc:
            raise ValidationError(YEDEK_YAZILAMADI) from exc
        self._yollar.append(yol)

    def receive_data_chunk(self, raw_data: bytes, start: int) -> None:
        assert self._akis is not None  # Django `new_file`dan sonra çağırır
        try:
            self._akis.write(raw_data)
        except OSError as exc:
            raise ValidationError(YEDEK_YAZILAMADI) from exc

    def file_complete(self, file_size: int) -> UploadedFile:
        assert self._akis is not None  # Django `new_file`dan sonra çağırır
        akis, self._akis = self._akis, None
        try:
            akis.close()
        except OSError as exc:
            raise ValidationError(YEDEK_YAZILAMADI) from exc
        return YuklenenYedek(akis, self._yollar[-1], str(self.file_name), file_size)

    def upload_interrupted(self) -> None:
        self.temizle()

    def temizle(self) -> None:
        """Açık kalan dosyayı kapatır, bu isteğin geçici dosyalarını siler. Hata yükseltmez.

        Uç bunu yanıt hazırken çağırır: hata hazır yanıtın yerine geçer, yapılmış takas sunucu hatası
        görünür, rapor kaybolurdu. Dosya dosya denenir; silinemeyeni açılış temizliği toplar. Ad ve
        yol günlüğe yazılmaz.
        """
        if self._akis is not None:
            akis, self._akis = self._akis, None
            try:
                akis.close()
            except OSError:
                logger.warning("Yüklenen yedeğin geçici dosyası kapatılamadı.")
        while self._yollar:
            try:
                self._yollar.pop().unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "Yüklenen yedeğin geçici dosyası silinemedi; açılış temizliği toplar."
                )


def list_backups() -> dict[str, Any]:
    """Yedek klasöründeki geri yüklenebilir `.odbak` dosyaları (en yeniden eskiye).

    `backup_dir` yanıtta bilinçli olarak vardır: kullanıcı elle aldığı bir
    yedeği nereye koyacağını ya da dosyaların nerede durduğunu buradan görür
    (tek bilgisayarda çalışan yerel program — yol kişisel veri değildir).

    Her satırın `kurtarma` alanı o yedeği açan kurtarma anahtarının kimliğidir:
    `{no, tarih}` (`tarih` ISO gün; arayüz gg.aa.yyyy yazar) ya da başlık yoksa,
    okunamıyorsa veya kullanılamıyorsa `null` (`_recovery_key_of`). Kullanıcı
    yeni bilgisayarda hangi kâğıdın hangi yedeği açtığını buradan görür (tasarım
    §4.4.4, TK10; anahtar yenilenince eski kâğıt eski yedekleri açmaya devam eder).
    Başlığın tuzu ve sarmalı ASLA dönmez.

    `kapsam` yedeğin ne taşıdığıdır: `"yerel"`, `"tam"` ya da okunamıyorsa `null` (`_kapsam_of`;
    plan F1b-3 "Kap ve manifesto": liste kapsamı kurtarma anahtarı olmadan okur).
    """
    dizin = app_password.backup_dir()
    satirlar: list[dict[str, Any]] = []
    if dizin.is_dir():
        for yol in dizin.glob(f"*{BACKUP_SUFFIX}"):
            if not yol.is_file():
                continue
            bilgi = yol.stat()
            satirlar.append(
                {
                    "name": yol.name,
                    "size": bilgi.st_size,
                    "modified_at": timezone.localtime(
                        datetime.fromtimestamp(bilgi.st_mtime, tz=UTC)
                    ).isoformat(),
                    "kurtarma": _recovery_key_of(yol),
                    "kapsam": _kapsam_of(yol),
                    "_mtime": bilgi.st_mtime,
                }
            )
    satirlar.sort(key=lambda satir: float(satir["_mtime"]), reverse=True)
    for satir in satirlar:
        del satir["_mtime"]
    return {"backup_dir": str(dizin), "backups": satirlar}


def restore_and_require_restart(
    *,
    name: str = "",
    yuklenen: YuklenenYedek | None = None,
    hesap: str = "",
    password: str = "",
    recovery_key: str = "",
    ekler_olmadan_surdur: bool = False,
) -> dict[str, Any]:
    """Yedeği veritabanının yerine koyar ve süreci "yeniden başlat" kapısına alır.

    Kaynak ikisinden biridir: `name` (yedek klasöründen) YA DA `yuklenen` (kullanıcının yüklediği,
    diske akmış dosya; silmek ucun işidir). Hata hâlinde hedefe dokunulmaz (çekirdek garantisi) ve
    kapı KURULMAZ: kullanıcı yeniden dener. İş uzun iş sayacındadır (modül başlığı). Yetki (modül
    başlığı "YETKİ") hiçbir dosyaya ve bakım kapısına dokunmadan önce denetlenir.
    `ekler_olmadan_surdur` ikinci onaydır (modül başlığı "BOZUK EK").
    """
    kim = yazar()
    oturum_hesabi = None if kim is None or kim.sistem_mi else kim.hesap_id
    if password:
        if oturum_hesabi is None:
            raise LiveRestoreError(PAROLA_YOLU_OTURUM_ISTER)
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.GERI_YUKLEME)
        hesap = _parola_hesabi(hesap, oturum_hesabi)
    with bakim.UZUN_ISLER.is_():
        return _restore(
            name=name,
            yuklenen=yuklenen,
            hesap=hesap,
            password=password,
            recovery_key=recovery_key,
            oturum_hesabi=oturum_hesabi,
            ekler_olmadan_surdur=ekler_olmadan_surdur,
        )


def _parola_hesabi(hesap: str, oturum_hesabi: str) -> str:
    """Parola yolunun hesabı: verilmediyse ya da oturumdaki hesabı anıyorsa o (kimliğiyle).

    `hesap` kimlik ya da tanıtıcıdır (çekirdeğin `--hesap` kuralı); güncel güvenlik
    dosyasındaki sarmallardan çözülür. Başka bir hesabı anıyorsa ret (400): parolası sorulan
    hesap yazarın hesabıdır (yetki kararı onun rolüyle verildi).
    """
    istenen = hesap.strip()
    if not istenen or istenen == oturum_hesabi:
        return oturum_hesabi
    for sarmal in app_password.account_wraps():
        if istenen in (sarmal["tanitici"], sarmal["id"]):
            if sarmal["id"] == oturum_hesabi:
                return oturum_hesabi
            break
    raise LiveRestoreError(PAROLA_YALNIZ_OTURUM_HESABI)


def _restore(
    *,
    name: str,
    yuklenen: YuklenenYedek | None,
    hesap: str,
    password: str,
    recovery_key: str,
    oturum_hesabi: str | None,
    ekler_olmadan_surdur: bool,
) -> dict[str, Any]:
    hedef = _database_path()
    kaynak = yuklenen.yol if yuklenen is not None else _resolve_named(name)
    # Ortak bakım kapısı takastan ÖNCE kapanır (§4.1, §13 D3): yeni gün işi (günlük yedek)
    # başlamaz, uçuştaki iş bitene dek beklenir. Süre dolarsa takas yapılmaz (modül başlığı):
    # dosya deposu takası süren bir tam yedekle çakışırdı.
    if not bakim.KAPI.bakima_al(bekleme_sn=BAKIM_BEKLEME_SN):
        bakim.KAPI.bakimdan_cik()
        logger.warning("Bakım kapısı: uçuştaki iş süresinde bitmedi; geri yükleme yapılmadı.")
        raise LiveRestoreError(BAKIM_SURUYOR)
    try:
        # Takas öncesi TÜM bağlantılar kapatılır; sonraki istekler zaten
        # restart_gate'e takılacağından yeniden açılmaları sorun olmaz.
        connections.close_all()
        sonuc = backup_restore.restore_database(
            kaynak,
            hedef,
            hesap=hesap or None,
            password=password or None,
            recovery_key=recovery_key or None,
            # Geri yükleme onu başlatan oturumun hesabına bağlanır (kurtarma yolunda da).
            oturum_hesabi=oturum_hesabi,
            ekler_olmadan_surdur=ekler_olmadan_surdur,
            # Geçici dosyanın adı kayda geçmez: yüklenen dosyanın özgün adı denenir.
            yedek_adi=str(yuklenen.name) if yuklenen is not None else None,
        )
    except BaseException:
        # Çekirdekten hata çıktıysa takas yapılmamıştır (çekirdek garantisi; takastan sonraki
        # adımlar hata yükseltmez): gün işleri yeniden koşabilir.
        bakim.KAPI.bakimdan_cik()
        raise
    # Başarı: bakım kapısı program yeniden açılana dek KAPALI kalır.
    # Bellekteki DEK eski veritabanına aittir; düşürülür. Kapı kurulunca kilit
    # ekranı dahil tüm API kesilir — tek çıkış programı kapatıp yeniden açmaktır.
    app_password.lock()
    restart_gate.mark_restart_required()
    # Yedeğin adı burada yazılmaz: seçilen dosyanın adı serbest metin olabilir (çekirdek süzer).
    logger.info("API'den geri yükleme uygulandı; yeniden başlatma bekleniyor.")
    return {
        "old_db_name": sonuc.old_db_path.name if sonuc.old_db_path is not None else "",
        "state_written": sonuc.state_written,
        "restart_required": True,
        "dosya_raporu": sonuc.dosya_raporu.yanit(),
    }


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------
def _recovery_key_of(yol: Path) -> dict[str, Any] | None:
    """Yedeği açan kurtarma anahtarının kimliği `{no, tarih}`; bilinemiyorsa None.

    Yalnız dosyanın başı okunur (`read_embedded_recovery_metadata`). Başlık
    kullanılamıyorsa (şema 1, kurtarma bölümü eksik, bozuk) kimlik de gösterilmez:
    o yedek kurtarma anahtarıyla zaten açılamaz (`parse_security_state` tek kuraldır).
    Okuma hatası listeyi düşürmez; satır kimliksiz görünür. Ayrıştırma da istisna
    sızdırmaz (`parse_security_state` derin iç içe JSON'un RecursionError'ını dâhil
    None'a çevirir): tek bir bozuk yedek, kayıp kilidinin çıkış yolu olan listeyi
    düşüremez.
    """
    try:
        ham = read_embedded_recovery_metadata(yol)
    except (OSError, BackupCryptoError):
        return None
    return cast("dict[str, Any] | None", recovery_key_identity(parse_security_state(ham)))


def _kapsam_of(yol: Path) -> str | None:
    """Yedeğin kapsam kodu, yalnız dosyanın başından; okunamıyorsa None, listeyi düşürmez."""
    try:
        return geri_yukleme_ekleri.KAPSAM_KODLARI.get(kap_basligini_oku(yol).kapsam)
    except (OSError, BackupCryptoError):
        return None


def _resolve_named(name: str) -> Path:
    """Yedek klasöründeki adı yola çevirir; klasör dışına çıkışı reddeder."""
    duz_ad = name.strip()
    if (
        not duz_ad
        or not duz_ad.endswith(BACKUP_SUFFIX)
        # Yol ayracı denetimi platformdan bağımsız elle yapılır: testler
        # Linux'ta koşar, hedef makine Windows'tur; ikisinde de ".." ve
        # ayraçlı adlar klasör dışına işaret edebilir.
        or "/" in duz_ad
        or "\\" in duz_ad
        or duz_ad != Path(duz_ad).name
    ):
        # Kullanıcı metninde uzantı geçmez (docs/sozluk.md "Yedek" satırı).
        raise LiveRestoreError("Geçerli bir yedek dosyası adı verin (yedek klasöründeki listeden).")
    yol = app_password.backup_dir() / duz_ad
    if not yol.is_file():
        raise LiveRestoreError(f"Yedek klasöründe böyle bir dosya yok: {duz_ad}")
    return yol


def _database_path() -> Path:
    """Hedef dosyanın yolu — bağlantı AÇILMAZ (restore_backup komutuyla aynı kural)."""
    ad = str(settings.DATABASES["default"].get("NAME") or "")
    if not ad or ad == ":memory:" or "mode=memory" in ad:
        raise LiveRestoreError("Veritabanı dosya tabanlı değil; geri yükleme uygulanamaz.")
    return Path(ad)
