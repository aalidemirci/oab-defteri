"""Kilit açılışında denetim izinin kendiliğinden doğrulanması ve bütünlük kartları (§4.6.3).

Tasarım §4.4.3 "Kilit açılışında sıra": sarmal açılır → `Account` satırı var, durumu uygun,
mührü tutuyor mu (iki depo kuralı; tutmazsa oturum AÇILMAZ, `app_password`) → **çapa ve
kilitli satırlar doğrulanır → geri yükleme notu varsa denetim izine yazılır** → ertelenen
gün işleri ve veri göçleri koşar. Bu modül kalın yazılı iki adımdır; `app_password.
_start_session` DEK ve İA belleğe alındıktan sonra, `oturum.IZ_KIP_KILIDI` altında çağırır:

1. `hazirla` (yalnız okur): §4.6.3'ün üç denetimi —
   (1) çapanın mührü tutuyor mu ve veritabanında çapanın `seq` satırının `mac`'i çapaya eşit
   mi; değilse "denetim izi kuyruğu kesilmiş ya da veritabanı geri sarılmış" (`kuyruk_kesik`,
   `capa_muhru_tutmadi`; dosya yoksa `capa_yok`, okunamıyorsa `capa_bozuk`);
   (2) çapadan sonraki kilitli satırlar tohumdan yeniden türetilerek doğrulanır, adımları
   `0…adim-1` mi: sondaki TEK eksik satır kesintidir (`kesinti`, BİLGİ — tohum dosyada
   ilerledi, satır yazılamadan süreç öldü; plan F1b-1), daha fazlası, fazlası, sıra dışı ya
   da mühürsüz satır UYARIDIR; dosyadaki tohum `tohum_adim`'e eşit olmalıdır (`tohum_tutmadi`).
   Çapadan sonraki her satırın kipi geçerli ve kilitli satır kuralına uygun olmalıdır
   (`satir_kurali`). Çapadan sonra açık kipte bir `KILIT` satırı varsa çapa o kilitlenmede
   yenilenmemiştir (yazılamadı ya da dosya eski bir kopyayla değiştirildi): `capa_bayat`. Çapa
   her kilitlenmede `KILIT` satırına yazılır; oturum açıkken süreç ölürse (`KILIT` yok) çapadan
   sonra açık kipte satırlar kalır, bu meşrudur;
   (3) son 200 satırın zinciri ve satır kuralı (`denetim_izi.son_satirlari_dogrula`). Mühürsüz
   satır BİR KEZ bildirilir: daha önceki bir kilit açılışının (açık kipte, MAC'i tutan)
   `BUTUNLUK` satırı mühürsüz satır bildirdiyse ondan önceki mühürsüz satırlar yinelenmez;
   bildirilmemiş olan — çapadan önce kalmış olsa da — bulgudur (`_son_satirlari_ekle`).
   GERİ YÜKLEME NOTU ÇAPAYI AÇIKLIYORSA (1)-(2) yapılmaz: çapa eski veritabanınındır, uyarı
   yerine yalnız `GERI_YUKLEME` satırı düşer (tasarım §4.6.3 (1)). Not çapayı, notun İLK
   geri yüklemesinin kenara aldığı veritabanının zincir başıyla açıklar (`_not_capayi_
   acikliyor`): çapa o zincir başına eşit ya da onun gerisinde olmalıdır (kilitlenmeden sonra
   o veritabanına kilitli ya da açık satırlar eklenmiş olabilir); kenara alınan veritabanında
   zincir yoktuysa (dosya yoktu ya da izi boştu: yeni bilgisayara taşıma) ya da not yazılırken
   çapa yoktuysa (kurulumdan sonra hiç kilitlenmeden yapılan uygulama içi geri yükleme; notun
   `capa: null` kaydı) çapa da yok olmalıdır. Notun söylediği bunu tutmazsa (bayat ya da program dışından konmuş not; kuyruğu
   kesilmiş veritabanının geri yüklemeyle örtülmesi) ya da not okunamıyor, bozuk ya da zincir
   başı taşımıyorsa (kenara alınan dosya okunamadı) not çapayı açıklamaz: (1)-(2) not yokmuş
   gibi koşar, bulgu `GERI_YUKLEME` satırıyla BİRLİKTE yazılır.
2. `yaz` (kilit açılışının TEK veritabanı işleminde, `GIRIS`'ten önce): bulgu varsa TEK
   `BUTUNLUK` satırı (`SISTEM`; bulgu yoksa satır yok, plan F1b-1); notun her geri yüklemesi
   için `GERI_YUKLEME` satırı (oturumu açan hesabın; tasarım §4.4.4) ve bekleyen sistem
   olayları (`SISTEM`, açık anahtarla, olayın kendi anı `zaman` değeriyle): düşen bir kilitli
   yazımdan sonra süreç belleğinde bekleyenler (`iz_durumu`) ve notta bekleyenler; geri
   yüklemeden sonra iki depo karşılaştırması (`hesaplar.reconcile_two_stores`, §4.6.1 kural 4).
3. `tamamla` (işlem commit edildikten SONRA): not silinir, bellekte bekleyen yazılan olaylar
   düşer; çapa ya da kilitli satır bulgusu varsa ya da not işlendiyse çapa yenilenir (bulgu
   satıra geçti; aynı bulgu bir sonraki açılışta yinelenmesin — tasarım "geri yükleme notu …
   çapa yenilenir").

GİRİŞ ENGELLENMEZ (altın kural 3): bu bulgular sert engel değildir; doğrulamanın kendisi
beklenmedik biçimde düşerse de bulgu (`dogrulama_yapilamadi`) olur. Sert engel yalnız hesap
bütünlüğündedir (mühür, iki depo, İA çözülemezse, satırın izi; `app_password`). Satırlar
yazılamazsa giriş açılmaz: iz yazılamazsa yazma yapılamaz. DAR İSTİSNA (kullanıcı kararı 03.11.2026
"Boşluğu engelle"): hesabın son kaydından sonra izde SİLİNMİŞ ya da SIRASI DEĞİŞTİRİLMİŞ satır
(sıra boşluğu ya da tekrarlanan sıra, tamsayı olmayan sıra, kaydırılmış dayanak) girişi kapatır
— ama bu modülde değil, satırın izinin parçası olarak girişten ÖNCE (`services.satir_izi` "İZ
BOŞLUĞU"). Buradaki bulgular
— kuyruk kesme ve çapa bulguları (`kuyruk_kesik`, `capa_bayat`, `capa_yok`), MAC'i tutmayan ya da
kuralına uymayan satır, kilitli satır bulguları — girişi engellemez.

KARTLAR: durum ayrı bir dosyada değil denetim izinin kendisinde kalıcıdır. Kartlar rolüne
göre üç uçtan okunur (tasarım §4.4.2 "kısmi yetki ayrı uçla verilir"; plan F1b-2 "Bütünlük ucu
bölünür"): oturumdaki hesabın kendi kartları (`kendi_kartlari`; `GET security/integrity/`, her
rol: son girişler, parola yenilenme bildirimi, kâğıt çapası), denetim kartları
(`denetim_kartlari`; `GET security/integrity/audit/`, program yöneticisi ve Denetleme Kurulu:
bütünlük, geri yükleme ve mührü tutmayan hesaplar — §4.6.3, §4.6.1 kural 1, §4.4.4) ve iki depo
kartı (`iki_depo_karti`; `GET security/integrity/two-store/`, yalnız program yöneticisi:
sarmalı olmayan hesaplar, silinebilir sarmallar — §4.6.1 kural 4 — ve parola kaydının özeti
satırınkini tutmayan hesaplar). Kartlar ve parola yenilenme bildirimi YALNIZ açık kipte, iz
anahtarıyla mühürlü, kuralına uyan ve MAC'i tutan satırları okur
(`denetim_izi.acik_satir_dogrulayici`): kilitli kip ya da mühürsüz anahtarla (sırsız) eklenmiş
sahte bir `GIRIS`, `BUTUNLUK` ya da `GERI_YUKLEME` satırı karta çıkmaz, (3). denetimin
bulgusu olur. Bütünlük kartı oturumdaki hesabın bir önceki girişinden beri
yazılmış `BUTUNLUK` satırlarıdır (doğrulama bulgusu ve girişte hesap mührü tutmadı); her hesap
kendi bir sonraki girişinde görür. Geri yükleme kartı son `GERI_YUKLEME` satırıdır (aynı kilit
açılışında yazılmış öncekilerle birlikte: iki geri yükleme arasında kilit açılmadıysa asıl dönüş
yolu ilkinin kenara aldığı veritabanıdır) ve Denetleme Kurulu "gördüm" diyene dek kalır (aşağıda
"GÖRDÜM"). İki depo kartı ve mührü tutmayan hesaplar canlı
hesaplanır (`hesaplar.two_store_differences`); sahipsiz sarmalların silinmesi program
yöneticisinin onayıyladır (`POST security/integrity/orphan-wraps/`). Kartlar birbirinden
bağımsız okunur: biri okunamazsa adı o ucun `okunamayan` listesine girer, ön yüz bunu uyarı
kartıyla söyler ("Bütünlük Durumu Okunamadı"; `_kartlar`). Bulgu kodları iç
koddur, kullanıcı metnine çıkmaz: ön yüz sözlükteki metni yazar (`modules/butunluk/metinler`).
Kartlardaki hesap kişisizdir (`_hesap_ozeti`): kimlik, tanıtıcı, rol etiketi, açılış ve kapanış
günü (aynı tanıtıcıyı alan eski ve yeni hesap ayrılsın; orkestratör maddesi F-3); ad-soyad yok.

GÖRDÜM (`geri_yukleme_goruldu_mu`, `son_geri_yukleme`; yazımı `hesaplar.acknowledge_restore`,
`POST security/integrity/restore-seen/` `{seq}`; plan F1b-2 "Gördüm."; tasarım §4.4.4): geri
yükleme kartı, Denetleme Kurulunun bir üyesi son geri yüklemeye "Gördüm" deyince HERKES İÇİN
kalkar — program yöneticisinde de öteki üyelerde de (kullanıcı kararı 02.11.2026: bir üye yeter);
kimin gördüğü denetim izinde kalır (`ISARET` satırı: model denetim izinin kendisi, kimlik geri
yüklemenin `seq`'i, yazar o üyenin hesabı). Kart yalnız DOĞRULANAN bir `ISARET` satırıyla kalkar
(açık kipte, iz anahtarıyla mühürlü, yazarı Denetleme Kurulu hesabı; mühürsüz ya da başka rolün
satırı kaldırmaz) ve yalnız doğrulanan son `GERI_YUKLEME` satırına bağlanır. Aynı geri yüklemeye
ikinci "Gördüm" satır yazmaz; eski ya da olmayan bir `seq` reddedilir (409). Yeni bir geri
yükleme kendi kartını açar. Açık Denetleme Kurulu hesabı yoksa kart program yöneticisinde kalır:
program yöneticisi kartı kaldıramaz (rol kapısı ve servisin yetki kapısı).

PAROLA YENİLENME BİLDİRİMİ (`yenilenme_bildirimi`, uçta `bildirim_yaniti`; `GET|POST
security/integrity/reset-notice/`; tasarım §4.4.3, §4.3 tehdit 12): parolası sıfırlanan ya da kurtarma anahtarıyla yenilenen
hesabın sahibi, ilk girişinden sonra pencerede bildirimi ve o tarihten bu yana hesabıyla
yapılan girişleri görür; "Gördüm" bayrağı izli bir yazımla kaldırır
(`hesaplar.acknowledge_reset_notice`, `GUNCELLE` satırı).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final

from django.db.models import QuerySet
from django.utils import timezone

from apps.okul import denetim_izi, iz_durumu
from apps.okul.models import (
    KILITLI_KIP_TURLERI,
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditActor,
    AuditKeyMode,
    AuditTrail,
)
from apps.okul.oturum import (
    ham_an_sutunlari,
    hesap_ani,
    hesap_gunu,
    rol_etiketi,
    sistem_olarak,
)
from apps.okul.services import geri_yukleme_notu
from shared import crypto, kanonik

if TYPE_CHECKING:
    from apps.okul.services.hesaplar import TwoStoreDifferences

logger = logging.getLogger("oab_defteri.okul")

#: Kendiliğinden doğrulamanın kapsadığı son satır sayısı (§4.6.3 (3)).
SON_SATIR: Final = 200

# Bulgu kodları (iç kod; kullanıcı metnine çıkmaz).
CAPA_YOK: Final = "capa_yok"
CAPA_BOZUK: Final = "capa_bozuk"
CAPA_MUHRU_TUTMADI: Final = "capa_muhru_tutmadi"
CAPA_BAYAT: Final = "capa_bayat"
KUYRUK_KESIK: Final = "kuyruk_kesik"
KESINTI: Final = "kesinti"
KILITLI_SATIR_EKSIK: Final = "kilitli_satir_eksik"
KILITLI_SATIR_FAZLA: Final = "kilitli_satir_fazla"
KILITLI_SIRA: Final = "kilitli_sira"
KILITLI_MAC_TUTMADI: Final = "kilitli_mac_tutmadi"
MUHURSUZ_SATIR: Final = "muhursuz_satir"
TOHUM_TUTMADI: Final = "tohum_tutmadi"
DOGRULAMA_YAPILAMADI: Final = "dogrulama_yapilamadi"

#: Düzeyler: yalnız kesinti bilgidir, öteki her bulgu uyarıdır.
UYARI: Final = "uyari"
BILGI: Final = "bilgi"
_BILGI_KODLARI: Final = frozenset({KESINTI})

#: Kartta ve satırda listelenen bulgulu satır sırası sınırı (satır kişisiz sayıdır).
_AZAMI_BULGU_SATIRI: Final = 20

#: Kartlarda ve bildirimde okunan en çok satır (doğrulanamayan satırlar atlanırken sınır).
_KART_TARAMA_SINIRI: Final = 200

#: Yedeğin adı `GERI_YUKLEME` satırına yalnız programın ürettiği BİREBİR biçimdeyse girer
#: (`denetim_izi.program_yedegi_mi`). Kullanıcının seçtiği/yüklediği ya da yeniden adlandırdığı
#: dosyanın adı serbest metindir (kişi adı içerebilir; R1), satıra yazılmaz.
_DB_ONCEKI = re.compile(r"^db-onceki-\d{4}-\d{2}-\d{2}-\d{6}\.sqlite3$")


@dataclass
class KilitAcilisi:
    """Bir kilit açılışının doğrulama sonucu ve yazılacakları (`hazirla` doldurur)."""

    #: Bulgu kodu → bulgulu satır sıraları (boş olabilir).
    bulgular: dict[str, list[int]] = field(default_factory=dict)
    bas_seq: int | None = None
    capa_seq: int | None = None
    adim: int | None = None
    kilitli_satir: int | None = None
    #: Geri yükleme notu vardı (okunamasa da).
    not_vardi: bool = False
    #: Notun ilk geri yüklemesinin kenara aldığı veritabanının zincir başı (`_notun_onceki_basi`;
    #: `ZINCIR_YOKTU` ya da `(seq, mac)`); not bunu söylemiyorsa None.
    not_onceki_basi: tuple[int, str] | None = None
    #: Notun ilk geri yüklemesi yazılırken çapa yoktu (`_notun_capasi_yoktu`).
    not_capa_yoktu: bool = False
    #: Her geri yüklemenin `GERI_YUKLEME` satırı: (kimlik, değişen alanlar, değerler).
    geri_yuklemeler: list[tuple[str, list[str], dict[str, list[Any]]]] = field(default_factory=list)
    #: Bekleyen, denetlenmiş sistem olayları (önce bellekte bekleyenler, sonra nottakiler).
    bekleyen: list[dict[str, Any]] = field(default_factory=list)
    #: Bellekte bekleyen olaylardan bu açılışın aldığı sayı (`tamamla` listeden düşürür).
    bellekte_adet: int = 0
    capa_yenilensin: bool = False

    def ekle(self, kod: str, seq: int | None = None) -> None:
        satirlar = self.bulgular.setdefault(kod, [])
        if seq is not None and seq not in satirlar and len(satirlar) < _AZAMI_BULGU_SATIRI:
            satirlar.append(seq)

    @property
    def duzey(self) -> str | None:
        if not self.bulgular:
            return None
        return BILGI if set(self.bulgular) <= _BILGI_KODLARI else UYARI


# ---------------------------------------------------------------------------
# 1. Doğrulama (yalnız okur)
# ---------------------------------------------------------------------------
def hazirla(anahtar: denetim_izi.AcikAnahtar) -> KilitAcilisi:
    """Notu okur, (1)(2)(3)'ü uygular; HİÇBİR ŞEY yazmaz (modül başlığı). Hata yükseltmez."""
    acilis = KilitAcilisi()
    try:
        _hazirla(acilis)
    except Exception:  # noqa: BLE001 — doğrulama girişi engellemez (altın kural 3)
        logger.exception("Kilit açılışındaki denetim izi doğrulaması tamamlanamadı.")
        acilis.ekle(DOGRULAMA_YAPILAMADI)
    return acilis


def _hazirla(acilis: KilitAcilisi) -> None:
    bas = denetim_izi.zincir_basi()
    acilis.bas_seq = bas[0] if bas is not None else None
    _bellektekileri_al(acilis)
    _notu_oku(acilis)
    if bas is None:
        return  # ilk hesaptan önce: zincir yok, çapa da gerekmez
    if not acilis.not_vardi:
        _capayi_dogrula(acilis)
    elif not _not_capayi_acikliyor(acilis):
        logger.warning("Geri yükleme notu çapayı açıklamıyor; çapa denetimi yapılıyor.")
        _capayi_dogrula(acilis)
    _son_satirlari_ekle(acilis)


def _bellektekileri_al(acilis: KilitAcilisi) -> None:
    """Düşen bir kilitli yazımdan sonra bellekte bekleyen olaylar (`iz_durumu`; modül başlığı)."""
    bekleyenler = iz_durumu.bellekte_bekleyenler()
    acilis.bellekte_adet = len(bekleyenler)
    for olay in bekleyenler:
        try:
            acilis.bekleyen.append(_bekleyen_olay(olay))
        except (denetim_izi.IzYazilamadi, KeyError, TypeError, ValueError):
            logger.warning("Bellekte bekleyen biçimsiz olay atlandı.")


#: Kenara alınan veritabanında zincir yoktu (dosya yoktu ya da izi boştu): ilk satırın
#: `prev_mac`'i gibi `(0, "")` (`geri_yukleme_notu.BOS_ZINCIR`).
ZINCIR_YOKTU: Final = (0, "")


def _notun_onceki_basi(notu: dict[str, Any]) -> tuple[int, str] | None:
    """Notun İLK geri yüklemesinin kenara aldığı veritabanının zincir başı; bilinmiyorsa None.

    Çapa o veritabanını anlatır (iki geri yükleme arasında kilit açılmaz, çapa yazılmaz;
    `geri_yukleme_notu`). Önceki notu bozuk olan not ilk geri yüklemeyi yitirmiştir: None.
    Kenara alınacak dosya yoktuysa (`onceki: null`) ya da izi boştuysa `ZINCIR_YOKTU`.
    """
    if notu.get(geri_yukleme_notu.BOZUK_NOT_ISARETI):
        return None
    kayitlar = notu.get("geri_yuklemeler")
    if not isinstance(kayitlar, list) or not kayitlar or not isinstance(kayitlar[0], dict):
        return None
    ilk = kayitlar[0]
    if "onceki" not in ilk:
        return None
    onceki = ilk["onceki"]
    if onceki is None:
        return ZINCIR_YOKTU
    bas = onceki.get("zincir_basi") if isinstance(onceki, dict) else None
    if not isinstance(bas, dict):
        return None
    seq, mac = bas.get("seq"), bas.get("mac")
    if isinstance(seq, bool) or not isinstance(seq, int) or not isinstance(mac, str):
        return None
    if (seq, mac) == ZINCIR_YOKTU:
        return ZINCIR_YOKTU
    if seq < 1 or not _mac_bicimi_mi(mac):
        return None
    return seq, mac


def _notun_capasi_yoktu(notu: dict[str, Any]) -> bool:
    """Notun İLK geri yüklemesi yazılırken `iz-durumu.json` yok muydu? (`capa: null`)

    Alan yoksa (eski not ya da çapa okunamadı) ya da önceki not bozuksa (ilk geri yükleme
    yitirildi) bilinmiyor: False.
    """
    if notu.get(geri_yukleme_notu.BOZUK_NOT_ISARETI):
        return False
    kayitlar = notu.get("geri_yuklemeler")
    if not isinstance(kayitlar, list) or not kayitlar or not isinstance(kayitlar[0], dict):
        return False
    return "capa" in kayitlar[0] and kayitlar[0]["capa"] is None


def _mac_bicimi_mi(deger: object) -> bool:
    return isinstance(deger, str) and len(deger) == 64 and set(deger) <= set("0123456789abcdef")


def _not_capayi_acikliyor(acilis: KilitAcilisi) -> bool:
    """Geri yükleme notu çapanın durumunu açıklıyor mu? (modül başlığı, 1. adım)

    Çapa kenara alınan veritabanının zincir başına eşit (`seq` ve `mac`) ya da onun gerisinde
    (`seq` küçük) olmalıdır; o veritabanında zincir yoktuysa ya da not yazılırken çapa yoktuysa
    çapa da yok olmalıdır. Çapanın mührü burada denetlenmez: notun anlattığı veritabanını başka
    bir kurulumun iz anahtarı mühürlemiş olabilir (geri yüklenen veritabanının anahtarıyla
    doğrulanamaz).
    """
    bas = acilis.not_onceki_basi
    try:
        durum = iz_durumu.oku()
    except iz_durumu.IzDurumuYok:
        return acilis.not_capa_yoktu or bas == ZINCIR_YOKTU
    except iz_durumu.IzDurumuBozuk:
        return False
    if bas is None or bas == ZINCIR_YOKTU:
        return False
    return durum.capa_seq < bas[0] or (
        durum.capa_seq == bas[0] and kanonik.esit(durum.capa_mac, bas[1])
    )


def _son_satirlari_ekle(acilis: KilitAcilisi) -> None:
    """(3): son 200 satırın zinciri ve satır kuralı; mühürsüz satır BİR KEZ bildirilir.

    Mühürsüz satır, bildirilmediği sürece bulgudur (`muhursuz_satir`) — çapadan önce kalmış
    olsa da: oturum açıkken sırsız anahtarla eklenen bir satır kilitlenmede çapanın gerisinde
    kalır, (2) onu görmez. Daha önceki bir kilit açılışının `BUTUNLUK` satırı mühürsüz satır
    bildirdiyse, o satırdan ÖNCEKİ mühürsüz satırlar o açılışta bildirilmiştir (her mühürsüz
    satır, kendisinden sonraki ilk kilit açılışının (3). denetiminin penceresindedir) ve
    yinelenmez. Sayılan `BUTUNLUK` satırı açık kipte, kuralına uygun, MAC'i tutan ve bu
    denetimde bulgusu olmayan satırdır: sırrı olmayan biri bildirilmiş gibi gösteremez.
    """
    bulgular = denetim_izi.son_satirlari_dogrula(SON_SATIR)
    muhursuzler = [b.seq for b in bulgular if b.kod == denetim_izi.MUHURSUZ]
    sinir = _bildirilmis_muhursuz_siniri(min(muhursuzler), bulgular) if muhursuzler else 0
    for bulgu in bulgular:
        if bulgu.kod != denetim_izi.MUHURSUZ:
            acilis.ekle(bulgu.kod, bulgu.seq)
        elif bulgu.seq >= sinir:
            acilis.ekle(MUHURSUZ_SATIR, bulgu.seq)


def _bildirilmis_muhursuz_siniri(ilk: int, bulgular: list[denetim_izi.ZincirBulgusu]) -> int:
    """Mühürsüz satır bildirmiş en yeni geçerli `BUTUNLUK` satırının sırası (`ilk`'ten sonra); yoksa 0."""
    kusurlu = {b.seq for b in bulgular}
    gecerli = denetim_izi.acik_satir_dogrulayici()
    sorgu: QuerySet[AuditTrail] = AuditTrail.objects.filter(
        action=AuditAction.BUTUNLUK,
        model=denetim_izi.IZ_DOGRULAMASI,
        key_mode=AuditKeyMode.ACIK,
        seq__gt=ilk,
    ).order_by("-seq")
    for satir in denetim_izi.satirlari_oku(sorgu):
        if satir.seq in kusurlu or not gecerli(satir):
            continue
        if MUHURSUZ_SATIR in _deger_listesi(satir, "bulgular"):
            return int(satir.seq)
    return 0


def _deger_listesi(satir: AuditTrail, ad: str) -> list[Any]:
    """Satırın `values[ad]` çiftinin "sonra" değeri liste ise o liste; değilse boş liste."""
    cift = (satir.values or {}).get(ad) if isinstance(satir.values, dict) else None
    if isinstance(cift, list) and len(cift) == 2 and isinstance(cift[1], list):
        return list(cift[1])
    return []


def _capayi_dogrula(acilis: KilitAcilisi) -> None:
    """(1) çapa ve (2) çapadan sonraki kilitli satırlar."""
    try:
        durum = iz_durumu.oku()
    except iz_durumu.IzDurumuYok:
        acilis.ekle(CAPA_YOK)
        acilis.capa_yenilensin = True
        _muhursuzleri_ekle(acilis)
        return
    except iz_durumu.IzDurumuBozuk:
        acilis.ekle(CAPA_BOZUK)
        acilis.capa_yenilensin = True
        _muhursuzleri_ekle(acilis)
        return
    acilis.capa_seq, acilis.adim = durum.capa_seq, durum.adim
    ia = denetim_izi.sirayi_muhurleyen_ia(durum.capa_seq)
    beklenen = (
        kanonik.capa_muhru(crypto.audit_anchor_key(ia), durum.capa_seq, durum.capa_mac)
        if ia is not None
        else ""
    )
    if ia is None or not kanonik.esit(durum.muhur, beklenen):
        acilis.ekle(CAPA_MUHRU_TUTMADI)
        acilis.capa_yenilensin = True
        return
    satir_mac = AuditTrail.objects.filter(seq=durum.capa_seq).values_list("mac", flat=True).first()
    if satir_mac is None or not kanonik.esit(str(satir_mac), durum.capa_mac):
        acilis.ekle(KUYRUK_KESIK, durum.capa_seq)
        acilis.capa_yenilensin = True
        return
    _kilitli_satirlari_dogrula(acilis, durum, ia)


def _muhursuzleri_ekle(acilis: KilitAcilisi) -> None:
    """Çapa yokken: mühürsüz kilitli satırların (en yeni) sıraları. Çapa yenilenince bu
    satırlar çapadan önce kalır, sonraki açılışlar onları yinelemez."""
    sorgu = AuditTrail.objects.filter(key_mode=AuditKeyMode.KILITLI, key_ref="")
    for seq in sorgu.order_by("-seq").values_list("seq", flat=True)[:_AZAMI_BULGU_SATIRI]:
        acilis.ekle(MUHURSUZ_SATIR, int(seq))


def _kilitli_satirlari_dogrula(acilis: KilitAcilisi, durum: iz_durumu.IzDurumu, ia: bytes) -> None:
    """(2): çapadan sonraki satırlar — kilitli olanlar tohumdan; adımlar `0…adim-1`, dosyanın
    tohumu; açık kipteki `KILIT` çapanın bayatladığını, geçersiz kip ya da kuralına uymayan
    kilitli satır program dışı eklemeyi gösterir (modül başlığı)."""
    tohumlar = [denetim_izi.kilitli_tohum(ia, durum.capa_seq, durum.capa_mac)]

    def tohum(adim: int) -> bytes:
        while len(tohumlar) <= adim:
            tohumlar.append(kanonik.ileri_tohum(tohumlar[-1]))
        return tohumlar[adim]

    gorulen: list[int] = []
    sorgu: QuerySet[AuditTrail] = AuditTrail.objects.filter(seq__gt=durum.capa_seq).order_by("seq")
    for satir in denetim_izi.satirlari_oku(sorgu):
        if satir.key_mode == AuditKeyMode.ACIK:
            # Oturum açıkken çöken sürecin satırları meşrudur; ama kilitlenmenin `KILIT`
            # satırı çapanın ta kendisi olmalıydı (`oturum._kilit_izini_yaz`).
            if satir.action == AuditAction.KILIT:
                acilis.ekle(CAPA_BAYAT, satir.seq)
            continue
        if satir.key_mode != AuditKeyMode.KILITLI or not denetim_izi.satir_kurali_tutuyor(satir):
            acilis.ekle(denetim_izi.SATIR_KURALI, satir.seq)
            if satir.key_mode != AuditKeyMode.KILITLI:
                continue
        if satir.key_ref == "":
            acilis.ekle(MUHURSUZ_SATIR, satir.seq)
            continue
        ref = denetim_izi.kilitli_ref_coz(satir.key_ref)
        if ref is None or ref[0] != durum.capa_seq:
            acilis.ekle(KILITLI_SIRA, satir.seq)  # başka bir çapanın ya da biçimsiz başvuru
            continue
        adim = ref[1]
        if gorulen and adim <= gorulen[-1]:
            acilis.ekle(KILITLI_SIRA, satir.seq)  # yinelenen ya da geriye giden adım
        gorulen.append(adim)
        anahtar = crypto.audit_locked_mac_key(tohum(adim))
        if not denetim_izi.mac_tutuyor(anahtar, satir):
            acilis.ekle(KILITLI_MAC_TUTMADI, satir.seq)
    acilis.kilitli_satir = len(gorulen)
    beklenen = set(range(durum.adim))
    mevcut = set(gorulen)
    if mevcut - beklenen:
        acilis.ekle(KILITLI_SATIR_FAZLA)
    eksik = beklenen - mevcut
    if eksik == {durum.adim - 1}:
        acilis.ekle(KESINTI)  # tohum ilerledi, satır yazılamadan süreç öldü (plan F1b-1)
    elif eksik:
        acilis.ekle(KILITLI_SATIR_EKSIK)
    if not kanonik.esit(tohum(durum.adim).hex(), durum.tohum.hex()):
        acilis.ekle(TOHUM_TUTMADI)
    if acilis.bulgular:
        acilis.capa_yenilensin = True


def _notu_oku(acilis: KilitAcilisi) -> None:
    """Geri yükleme notunu okur, satırlarını ve bekleyen olayları denetleyerek hazırlar."""
    dizin = iz_durumu.dizin()
    try:
        notu = geri_yukleme_notu.oku(dizin)
    except geri_yukleme_notu.NotOkunamadi:
        logger.warning("Geri yükleme notu okunamadı; ayrıntısız geri yükleme satırı yazılacak.")
        acilis.not_vardi = True
        acilis.capa_yenilensin = True
        acilis.geri_yuklemeler.append(("", ["not_okunamadi"], {}))
        return
    if notu is None:
        return
    acilis.not_vardi = True
    acilis.capa_yenilensin = True
    acilis.not_onceki_basi = _notun_onceki_basi(notu)
    acilis.not_capa_yoktu = _notun_capasi_yoktu(notu)
    if not notu.get("geri_yuklemeler") or notu.get(geri_yukleme_notu.BOZUK_NOT_ISARETI):
        # Not var ama geri yükleme kaydı yok ya da önceki not bozuktu: olgu yine kayda geçer.
        # Bozuk notun geri yüklemesi okunabilen kayıtlardan ÖNCEdir: satırı da önce yazılır
        # (satırların sırası geri yüklemelerin sırasıdır; kart sonuncuyu "son" sayar).
        acilis.geri_yuklemeler.append(("", ["not_okunamadi"], {}))
    for kayit in notu.get("geri_yuklemeler", []):
        acilis.geri_yuklemeler.append(_geri_yukleme_satiri(kayit))
    for olay in notu.get("bekleyen_olaylar", []):
        try:
            acilis.bekleyen.append(_bekleyen_olay(olay))
        except (denetim_izi.IzYazilamadi, KeyError, TypeError, ValueError):
            logger.warning("Geri yükleme notunda biçimsiz bekleyen olay atlandı.")


def _not_zamani(deger: Any) -> datetime | None:
    """Notun `zaman` alanı (geri yüklemenin ya da bekleyen olayın anı); biçimsizse `None`.

    Tek kural `geri_yukleme_notu.zaman_coz`'dadır: saat dilimsiz ya da çözülemeyen metin
    satıra girmez (not dosyası program dışından değiştirilebilir).
    """
    return geri_yukleme_notu.zaman_coz(deger)


def _geri_yukleme_satiri(kayit: Any) -> tuple[str, list[str], dict[str, list[Any]]]:
    """Notun bir geri yükleme kaydından satırın kimliği, değişen alanları ve değerleri.

    Yalnız izinli, kişisiz değerler (`denetim_izi.GERI_YUKLEME_KAYDI`); biçimi tutmayan değer
    atlanır. Tanıtıcı satıra girmez (modül başlığı, `geri_yukleme_notu`).
    """
    if not isinstance(kayit, dict):
        return "", ["not_okunamadi"], {}
    degerler: dict[str, Any] = {}
    zaman = _not_zamani(kayit.get("zaman"))
    if zaman is not None:
        degerler["zaman"] = zaman  # satıra UTC `Z` metni olarak girer (`kanonik.duz`)
    yedek = kayit.get("yedek")
    if isinstance(yedek, str) and denetim_izi.program_yedegi_mi(yedek):
        degerler["yedek"] = yedek
    # Uygulama içi geri yüklemede oturumdaki hesap (kurtarma anahtarı yolunda da): geri
    # yükleme, onu başlatan oturumun hesabına bağlanır (Hakkında "Açık oturum, sahibinin
    # imzasıdır"). Konsol geri yüklemesinde oturum yoktur.
    oturum = denetim_izi.kimlik_metni_ya_da_none(Account, kayit.get("oturum"))
    if oturum is not None:
        degerler["oturum_hesap"] = oturum
    yol = kayit.get("yol")
    if isinstance(yol, dict):
        tur = yol.get("tur")
        if tur in (geri_yukleme_notu.YOL_HESAP, geri_yukleme_notu.YOL_KURTARMA):
            degerler["yol"] = tur
        no = yol.get("no")
        if isinstance(no, int) and not isinstance(no, bool):
            degerler["kurtarma_no"] = no
        hesap = denetim_izi.kimlik_metni_ya_da_none(Account, yol.get("hesap"))
        if hesap is not None:
            degerler["hesap"] = hesap
    kimlik = ""
    onceki = kayit.get("onceki")
    if isinstance(onceki, dict):
        dosya = onceki.get("dosya")
        if isinstance(dosya, str) and _DB_ONCEKI.match(dosya):
            kimlik = dosya
        ozet = onceki.get("sha256")
        if _mac_bicimi_mi(ozet):
            degerler["onceki_sha256"] = ozet
        bas = onceki.get("zincir_basi")
        if isinstance(bas, dict):
            seq, mac = bas.get("seq"), bas.get("mac")
            if isinstance(seq, int) and not isinstance(seq, bool) and isinstance(mac, str):
                degerler["onceki_seq"] = seq  # 0: kenara alınanın izi boştu
                if _mac_bicimi_mi(mac):
                    degerler["onceki_mac"] = mac
    return (
        kimlik,
        sorted(degerler),
        denetim_izi.izinli_degerler(
            denetim_izi.GERI_YUKLEME_KAYDI, {ad: [None, deger] for ad, deger in degerler.items()}
        ),
    )


#: Notta bekleyen olayın nesneleri: yalnız sistem olaylarının kişisiz dosya nesneleri.
_SISTEM_OLAYI_NESNELERI: Final = frozenset(
    {
        denetim_izi.YEDEK_DOSYASI,
        denetim_izi.SEMA_GOCU,
        denetim_izi.GUN_ISI_ERTELEME,
        denetim_izi.IZ_DOGRULAMASI,
    }
)
#: Sistem olayının kimliği, alan adları ve metin değerleri programın ürettiği kodlardır
#: (yedek adı, sürüm, göç adı, iş adı): ASCII, boşluksuz. Not dosyası program dışından
#: değiştirilip serbest metin (kişi adı) yazılmışsa olay satıra GİRMEZ (R1).
_KOD = re.compile(r"^[A-Za-z0-9._:+-]{0,80}$")


def _kod_mu(deger: Any) -> bool:
    if isinstance(deger, str):
        return bool(_KOD.match(deger))
    if isinstance(deger, list):
        return all(_kod_mu(ic) for ic in deger)
    return deger is None or (isinstance(deger, int) and not isinstance(deger, bool))


def _bekleyen_olay(olay: Any) -> dict[str, Any]:
    """Bekleyen olayı yeniden denetler (not dosyası program dışından değişmiş olabilir).

    Tür kilitli kipin kapalı kümesinden, nesne sistem olaylarının dosya nesnelerinden,
    kimlik, alan adları ve değerler program kodu biçiminde olmalıdır; değerler ayrıca
    nesnenin izin listesinden geçer. Olayın kendi anı (`zaman`; saat dilimli) satıra `zaman`
    değeri olarak girer, okunamazsa girmez; değerlerin içinde gelen `zaman` biçimsizdir
    (program onu oraya yazmaz). Tutmayan olay atlanır (girişi engellemez).
    """
    if not isinstance(olay, dict) or olay.get("eylem") not in KILITLI_KIP_TURLERI:
        raise ValueError("biçimsiz olay")
    model, kimlik = olay["model"], olay["object_id"]
    alanlar = olay.get("changed_fields", [])
    degerler = olay.get("values") or {}
    if model not in _SISTEM_OLAYI_NESNELERI or not isinstance(alanlar, list):
        raise ValueError("biçimsiz olay")
    if model == denetim_izi.YEDEK_DOSYASI:
        # Yedeğin kimliği yalnız programın ürettiği addır; değilse boş (doğrudan yazımla
        # aynı kural: `iz_durumu._olay_kaydi`, `denetim_izi.yedek_kimligi`).
        kimlik = denetim_izi.yedek_kimligi(kimlik)
    if not isinstance(kimlik, str) or not _kod_mu(kimlik) or not _kod_mu(alanlar):
        raise ValueError("biçimsiz olay")
    if not isinstance(degerler, dict) or not all(_kod_mu(list(c)) for c in degerler.values()):
        raise ValueError("biçimsiz olay")
    if "zaman" in degerler:
        raise ValueError("biçimsiz olay")
    zaman = _not_zamani(olay.get("zaman"))
    if zaman is not None:
        degerler = {**degerler, "zaman": [None, zaman]}
    return {
        "eylem": olay["eylem"],
        "model": model,
        "object_id": kimlik[:64],
        "changed_fields": alanlar,
        "values": denetim_izi.izinli_degerler(model, degerler),
    }


# ---------------------------------------------------------------------------
# 2. Yazım (kilit açılışının işleminde) ve 3. tamamlama
# ---------------------------------------------------------------------------
def yaz(
    acilis: KilitAcilisi,
    *,
    anahtar: denetim_izi.AcikAnahtar,
    sarmali_yazilacak: frozenset[str] = frozenset(),
) -> None:
    """Bulgu, geri yükleme ve bekleyen olay satırları; geri yüklemeden sonra iki depo.

    Çağıranın işleminde ve oturumu açan hesabın yazar bağlamında çağrılır (modül başlığı).
    `sarmali_yazilacak`: sarmalı bu işlemin SONUNDA `guvenlik.json`'a yazılacak hesaplar
    (kurtarma anahtarıyla açılış; `app_password._start_session`). İki depo karşılaştırması
    onları sarmallı sayar: işlem düşerse sarmal da yazılmaz, satır da geri alınır.
    """
    if acilis.bulgular:
        degerler: dict[str, Any] = {
            "bulgular": sorted(acilis.bulgular),
            "duzey": acilis.duzey,
            "capa_seq": acilis.capa_seq,
            "adim": acilis.adim,
            "kilitli_satir": acilis.kilitli_satir,
            "bulgu_satirlari": sorted({s for liste in acilis.bulgular.values() for s in liste}),
        }
        dolu = {ad: [None, deger] for ad, deger in degerler.items() if deger not in (None, [])}
        with sistem_olarak():
            denetim_izi.olay(
                AuditAction.BUTUNLUK,
                model=denetim_izi.IZ_DOGRULAMASI,
                object_id=str(acilis.bas_seq or 0),
                changed_fields=sorted(dolu),
                values=dolu,
                anahtar=anahtar,
            )
        logger.warning(
            "Denetim izi doğrulaması bulgu verdi (%s): %s",
            acilis.duzey,
            ", ".join(sorted(acilis.bulgular)),
        )
    for kimlik, alanlar, degerleri in acilis.geri_yuklemeler:
        denetim_izi.olay(
            AuditAction.GERI_YUKLEME,
            model=denetim_izi.GERI_YUKLEME_KAYDI,
            object_id=kimlik,
            changed_fields=alanlar,
            values=degerleri,
            anahtar=anahtar,
        )
    with sistem_olarak():
        for olay in acilis.bekleyen:
            denetim_izi.olay(
                olay["eylem"],
                model=olay["model"],
                object_id=olay["object_id"],
                changed_fields=olay["changed_fields"],
                values=olay["values"],
                anahtar=anahtar,
            )
    if acilis.not_vardi:
        # Geç içe aktarım: hesap servisleri güvenlik çekirdeğini içe aktarır.
        from apps.okul.services import hesaplar

        hesaplar.reconcile_two_stores(sarmali_yazilacak=sarmali_yazilacak)


def tamamla(acilis: KilitAcilisi) -> None:
    """İşlem commit edildikten sonra: not silinir, bellekte bekleyen yazılanlar düşer,
    gerekiyorsa çapa yenilenir. Hata yükseltmez."""
    if acilis.bellekte_adet:
        iz_durumu.bellekte_bekleyenleri_birak(acilis.bellekte_adet)
    if acilis.not_vardi:
        try:
            geri_yukleme_notu.tuket(iz_durumu.dizin())
        except OSError:
            logger.error("Geri yükleme notu silinemedi; sonraki kilit açılışı yeniden işler.")
    if acilis.capa_yenilensin:
        iz_durumu.capa_yaz()


# ---------------------------------------------------------------------------
# Kartlar (Genel Bakış; `GET security/integrity/`)
# ---------------------------------------------------------------------------
#: "Son girişler" kartının satır sayısı.
SON_GIRIS_SAYISI: Final = 10
#: Bütünlük kartının en çok satırı.
_AZAMI_KART: Final = 20


def _yerel(an: Any) -> str:
    return str(timezone.localtime(an).isoformat())


Suzgec = Callable[[AuditTrail], bool]


def _dogrulanmis(sorgu: QuerySet[AuditTrail], adet: int, gecerli: Suzgec) -> list[AuditTrail]:
    """Sorgunun en yeni satırlarından süzgeçten geçen ilk `adet` satır (modül başlığı "KARTLAR").

    Yalnız açık kipteki satırlar okunur; doğrulanamayan satır atlanır. En çok
    `_KART_TARAMA_SINIRI` satıra bakılır: program dışından yığılmış satırlar kartı oyalamasın.
    Satırlar sütun dönüşümü düşmeden okunur (`denetim_izi.satirlari_oku`): biçimsiz hesap
    kimliği ya da an taşıyan satır kartı düşürmez, süzgeçten geçmez.
    """
    sonuc: list[AuditTrail] = []
    sirali = sorgu.filter(key_mode=AuditKeyMode.ACIK).order_by("-seq")
    for satir in denetim_izi.satirlari_oku(sirali, adet=_KART_TARAMA_SINIRI):
        if gecerli(satir):
            sonuc.append(satir)
            if len(sonuc) >= adet:
                break
    return sonuc


def _onceki_giris_seq(hesap_id: str, gecerli: Suzgec) -> int:
    """Hesabın bir önceki girişinin sırası (bu oturumun `GIRIS`'inden önceki); yoksa 0."""
    girisler = _dogrulanmis(
        AuditTrail.objects.filter(action=AuditAction.GIRIS, account_id=hesap_id), 2, gecerli
    )
    return int(girisler[1].seq) if len(girisler) > 1 else 0


def _butunluk_kartlari(hesap_id: str | None, gecerli: Suzgec) -> list[dict[str, Any]]:
    alt = _onceki_giris_seq(hesap_id, gecerli) if hesap_id else 0
    satirlar = _dogrulanmis(
        AuditTrail.objects.filter(action=AuditAction.BUTUNLUK, seq__gt=alt), _AZAMI_KART, gecerli
    )
    kartlar: list[dict[str, Any]] = []
    for satir in satirlar:
        if satir.model != _HESAP_MODELI:
            # Kilit açılışı doğrulaması (`IZ_DOGRULAMASI`). Hesap mührü dışındaki her
            # `BUTUNLUK` satırı bu biçimdedir; değeri yoksa düzey uyarı, bulgu listesi boştur.
            degerler = satir.values or {}
            kartlar.append(
                {
                    "seq": satir.seq,
                    "zaman": _yerel(satir.at),
                    "tur": "dogrulama",
                    "duzey": (degerler.get("duzey") or [None, UYARI])[1],
                    "bulgular": (degerler.get("bulgular") or [None, []])[1],
                    "hesap": None,
                }
            )
        else:
            kartlar.append(
                {
                    "seq": satir.seq,
                    "zaman": _yerel(satir.at),
                    "tur": "muhur",
                    "duzey": UYARI,
                    "bulgular": list(satir.changed_fields or []),
                    "hesap": _hesap_ozeti(satir.object_id),
                }
            )
    return kartlar


#: Hesap mührü bulgusunun (`app_password._muhur_bozuk_izi`) model adı.
_HESAP_MODELI: Final = denetim_izi.model_etiketi(Account)


def _hesap_ozeti(hesap_id: object) -> dict[str, Any]:
    """Kartlardaki hesabın kişisiz özeti: kimlik, tanıtıcı, rol etiketi, açılış ve kapanış günü
    (ad-soyad YOK).

    Rol etiketi veritabanındaki satırınkidir (kilit ekranındaki gibi; `oturum.rol_etiketi`);
    satır yoksa ya da kimlik biçimsizse tanıtıcı, rol etiketi ve günler `None`'dır. Mührü tutmayan
    satırın rolü program dışından değiştirilmiş olabilir: kart onu "kaydın söylediği" diye
    gösterir, doğrulanmış saymaz. Açılış ve kapanış günü (`acilis`, `kapanis`; Europe/Istanbul
    günü, yyyy-aa-gg; açık hesapta `kapanis` None) kapanan hesapla aynı tanıtıcıyı alan yeni hesabı
    ayırır (orkestratör maddesi F-3; erişim günlüğüyle aynı karar, `oturum.hesap_gunu`). İki an
    ORM dönüştürücüsü olmadan, ham metin okunur (`oturum.ham_an_sutunlari`, `hesap_ani`): program
    dışından yazılmış geçersiz tek bir an kartı — bütünlük grubunu, geri yükleme kartını — düşürmez,
    o gün "kaydın söylemediği"dir (None; bağımsız denetim bulgusu).
    """
    kimlik = denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id)
    satir = None
    if kimlik is not None:
        satir = (
            Account.objects.filter(pk=kimlik)
            .annotate(**ham_an_sutunlari())
            .values("login_name", "role", "ham_acilis", "ham_kapanis")
            .first()
        )
    return {
        "id": kimlik or str(hesap_id),
        "tanitici": None if satir is None else satir["login_name"],
        "rol_etiketi": None if satir is None else rol_etiketi(satir["role"]),
        "acilis": None if satir is None else hesap_gunu(hesap_ani(satir["ham_acilis"])),
        "kapanis": None if satir is None else hesap_gunu(hesap_ani(satir["ham_kapanis"])),
    }


#: "Gördüm"ün `ISARET` satırının modeli: işaretlenen kayıt denetim izinin kendi satırıdır (kimlik
#: geri yüklemenin `seq`'i; plan F1b-2 "Gördüm.").
IZ_SATIRI_MODELI: Final = denetim_izi.model_etiketi(AuditTrail)
#: "Gördüm" diyebilen rol (tasarım §4.4.2 M8 ⁵; `rol_izinleri.Eylem.GERI_YUKLEME_GORDUM`).
_GOREN_ROL: Final = AccountRole.DENETLEME_KURULU.value


def son_geri_yukleme(gecerli: Suzgec) -> AuditTrail | None:
    """Doğrulanan son `GERI_YUKLEME` satırı (kartın konusu); yoksa None."""
    bulunan = _dogrulanmis(AuditTrail.objects.filter(action=AuditAction.GERI_YUKLEME), 1, gecerli)
    return bulunan[0] if bulunan else None


def geri_yukleme_goruldu_mu(geri_yukleme: AuditTrail, gecerli: Suzgec) -> bool:
    """Denetleme Kurulunun bir üyesi bu geri yüklemeye "Gördüm" dedi mi? (modül başlığı "GÖRDÜM")

    Yalnız DOĞRULANAN bir `ISARET` satırı sayılır: açık kipte, iz anahtarıyla mühürlü, kuralına
    uyan; modeli denetim izinin kendisi, kimliği geri yüklemenin sırası, geri yükleme satırından
    SONRA yazılmış ve yazarı bir Denetleme Kurulu hesabı (rol ve hesap satırın MAC'ine girer).
    Mühürsüz ya da başka rolün `ISARET`'i kartı kaldırmaz.
    """
    sorgu = AuditTrail.objects.filter(
        action=AuditAction.ISARET,
        model=IZ_SATIRI_MODELI,
        object_id=str(geri_yukleme.seq),
        seq__gt=geri_yukleme.seq,
    )
    return bool(
        _dogrulanmis(
            sorgu,
            1,
            lambda satir: (
                satir.actor == AuditActor.HESAP and satir.role == _GOREN_ROL and gecerli(satir)
            ),
        )
    )


def _geri_yukleme_karti(gecerli: Suzgec) -> dict[str, Any] | None:
    """Son geri yükleme kartı: zamanca SON geri yüklemenin özeti + aynı kilit açılışında yazılmış
    öncekiler (`onceki_geri_yuklemeler`, eskiden yeniye). Denetleme Kurulunun bir üyesi son geri
    yüklemeye "Gördüm" dediyse kart HERKES İÇİN kalkar (None; modül başlığı "GÖRDÜM").

    İki geri yükleme arasında kilit açılmazsa ilk kilit açılışı notun her kaydı için bir satır
    yazar (`_notu_oku`; satır sırası geri yüklemelerin sırasıdır). Yedeğin alındığı günden
    sonraki kayıtlar İLK geri yüklemenin kenara aldığı veritabanındadır (asıl dönüş yolu;
    `geri_yukleme_notu`): kart yalnız sonuncuyu gösterseydi yanlış dosyayı gösterirdi. Aynı
    açılışın satırları, sonuncudan önceki son `GIRIS`'ten sonra yazılmış olanlardır.
    """
    bulunan = _dogrulanmis(
        AuditTrail.objects.filter(action=AuditAction.GERI_YUKLEME), _AZAMI_KART, gecerli
    )
    if not bulunan:
        return None
    son = bulunan[0]
    if geri_yukleme_goruldu_mu(son, gecerli):
        return None
    giris = _dogrulanmis(
        AuditTrail.objects.filter(action=AuditAction.GIRIS, seq__lt=son.seq), 1, gecerli
    )
    alt = int(giris[0].seq) if giris else 0
    ayni_acilis = [satir for satir in bulunan[1:] if satir.seq > alt]
    kart = _geri_yukleme_ozeti(son)
    kart["onceki_geri_yuklemeler"] = [_geri_yukleme_ozeti(s) for s in reversed(ayni_acilis)]
    return kart


def _geri_yukleme_ozeti(satir: AuditTrail) -> dict[str, Any]:
    """Bir `GERI_YUKLEME` satırının kişisiz özeti (kartın alanları)."""
    degerler = {ad: cift[1] for ad, cift in (satir.values or {}).items()}
    onceki_mac = degerler.get("onceki_mac")
    geri_yukleme_ani = _not_zamani(degerler.get("zaman"))
    return {
        "seq": satir.seq,
        # Satırın anı: geri yüklemeden sonraki ilk kilit açılışı.
        "zaman": _yerel(satir.at),
        # Geri yüklemenin kendi anı (nottan; eski satırda ya da bozuk notta yok).
        "geri_yukleme_ani": None if geri_yukleme_ani is None else _yerel(geri_yukleme_ani),
        "hesap": None if satir.account_id is None else _hesap_ozeti(satir.account_id),
        "yol": degerler.get("yol"),
        # Parola yolunda geri yüklemeyi açan hesap: satırdaki kimliğinden kişisiz özeti
        # (tanıtıcı satıra yazılmaz, `_geri_yukleme_satiri`; burada güncel satırdan okunur).
        "yol_hesap": (
            _hesap_ozeti(degerler["hesap"]) if isinstance(degerler.get("hesap"), str) else None
        ),
        # Uygulama içi geri yüklemeyi başlatan oturumun hesabı (iki yolda da; konsolda yok).
        "oturum_hesap": (
            _hesap_ozeti(degerler["oturum_hesap"])
            if isinstance(degerler.get("oturum_hesap"), str)
            else None
        ),
        "kurtarma_no": degerler.get("kurtarma_no"),
        "yedek": degerler.get("yedek"),
        "onceki_dosya": satir.object_id or None,
        "onceki_sha256": degerler.get("onceki_sha256"),
        "onceki_kayit_no": degerler.get("onceki_seq"),
        "onceki_zincir": (
            kanonik.zincir_kisaltmasi(onceki_mac) if isinstance(onceki_mac, str) else None
        ),
        "ayrintisiz": "not_okunamadi" in (satir.changed_fields or []),
    }


def _iki_depo_ozeti(kimlikler: list[str]) -> list[dict[str, Any]]:
    """Kişisiz satırlar: tanıtıcı (satırdan, yoksa sarmaldan), rol etiketi (satır yoksa `None`)
    ve hesabın kapalı olup olmadığı (silinebilir sarmalın iki nedeni ayrılsın)."""
    from apps.okul.services import app_password

    sarmal_tanitici = {sarmal["id"]: sarmal["tanitici"] for sarmal in app_password.account_wraps()}
    satirlar = {
        str(satir["id"]): satir
        for satir in Account.objects.values("id", "login_name", "role", "status")
    }
    sonuc: list[dict[str, Any]] = []
    for kimlik in kimlikler:
        satir = satirlar.get(kimlik)
        sonuc.append(
            {
                "id": kimlik,
                "tanitici": (satir["login_name"] if satir else None) or sarmal_tanitici.get(kimlik),
                "rol_etiketi": rol_etiketi(satir["role"]) if satir else None,
                "kapali": satir is not None and satir["status"] == AccountStatus.KAPALI,
            }
        )
    return sonuc


def _iki_depo_farki() -> TwoStoreDifferences | None:
    """Canlı fark; hesaplanamazsa (güvenlik dosyası ya da DEK yok) None."""
    from apps.okul.services import app_password, hesaplar

    try:
        return hesaplar.two_store_differences()
    except (app_password.AppPasswordError, crypto.KeyMissingError):
        return None


def _iki_depo_karti() -> dict[str, Any] | None:
    """Sarmalı olmayan açık hesaplar, onayla silinebilir sarmallar (§4.6.1 kural 4) ve parola
    kaydının özeti satırınkini tutmayan hesaplar ("SARMALIN TAZELİĞİ", `app_password`).

    Mührü tutmayan hesaplar bu kartta değildir: onlar kural 1'in kartıdır, denetim kartlarıyla
    program yöneticisine ve Denetleme Kuruluna gider (`_muhru_tutmayan`).
    """
    fark = _iki_depo_farki()
    if fark is None:
        return None
    sarmalsiz = list(fark.rows_without_wrap)
    silinebilir = list(fark.removable_wraps)
    ozeti_tutmayan = list(fark.digest_mismatch)
    return {
        "fark_var": bool(sarmalsiz or silinebilir or ozeti_tutmayan),
        "sarmalsiz_hesaplar": _iki_depo_ozeti(sarmalsiz),
        "silinebilir_sarmallar": _iki_depo_ozeti(silinebilir),
        # Parola kaydı satırdaki özeti tutmayan hesaplar (kullanıcı kararı 03.11.2026): giriş
        # yapamaz; çaresi program yöneticisinin parola sıfırlamasıdır (ekran işi d'dedir).
        "ozeti_tutmayan_hesaplar": _iki_depo_ozeti(ozeti_tutmayan),
    }


def _muhru_tutmayan() -> list[dict[str, Any]]:
    """Kaydı ya da izi tutmayan hesaplar (mührü tutmayan, eski bir kopyadan geri konmuş ya da son
    kaydından sonra denetim izinden kayıt silinmiş; `seal_mismatch`; §4.6.1 kural 1: hiçbir
    işleme konu olmaz; kart program yöneticisi ve Denetleme Kurulu panosuna). Fark
    hesaplanamazsa boş liste."""
    fark = _iki_depo_farki()
    return [] if fark is None else _iki_depo_ozeti(list(fark.seal_mismatch))


def _kagit_capasi() -> dict[str, Any] | None:
    bas = denetim_izi.zincir_basi()
    if bas is None:
        return None
    return {"kayit_no": bas[0], "zincir": kanonik.zincir_kisaltmasi(bas[1])}


def _girisler(hesap_id: str, gecerli: Suzgec, *, sonra: Any = None) -> list[str]:
    sorgu = AuditTrail.objects.filter(action=AuditAction.GIRIS, account_id=hesap_id)
    if sonra is not None:
        sorgu = sorgu.filter(at__gte=sonra)
    return [_yerel(satir.at) for satir in _dogrulanmis(sorgu, SON_GIRIS_SAYISI, gecerli)]


def hesabin_girisleri(hesap_id: object) -> list[str]:
    """Hesabın kilit ekranından yaptığı son girişler (Kullanıcılar → hesap ayrıntısı; plan F1b-2
    "Kullanıcılar uçları"): YALNIZ o hesabın `GIRIS` satırları, en yeni önce, en çok
    `SON_GIRIS_SAYISI`; yalnız doğrulanan açık kip satırları (modül başlığı "KARTLAR"). Kimlik
    biçimsizse boş liste. Yalnız okur."""
    kimlik = denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id)
    if kimlik is None:
        return []
    return _girisler(kimlik, denetim_izi.acik_satir_dogrulayici())


def yenilenme_bildirimi(hesap_id: object) -> dict[str, Any] | None:
    """Parola sıfırlandıysa ya da kurtarma anahtarıyla yenilendiyse sahibine bildirim (tehdit 12).

    `{tur, zaman, girisler}`: tür `SIFIRLAMA` ya da `KURTARMA` (ön yüz sözlükteki cümleyi
    yazar; kod ekrana çıkmaz), yenilenme anı ve o andan bu yana YALNIZ bu hesabın `GIRIS`
    satırları (en yeni önce, en çok `SON_GIRIS_SAYISI`; yalnız doğrulanan satırlar, modül
    başlığı "KARTLAR"). Bildirim beklemiyorsa, hesap yoksa ya da kimlik biçimsizse `None`.
    Bildirim bekliyor ama sıfırlama anı okunamıyorsa hata yükselir (`bildirim_yaniti` ve kartlar
    ucu onu `okunamayan`a çevirir). Yalnız okur; bayrağı `hesaplar.acknowledge_reset_notice`
    kaldırır.
    """
    return _yenilenme_bildirimi(hesap_id, None)


def bildirim_yaniti(hesap_id: object) -> dict[str, Any]:
    """`GET|POST security/integrity/reset-notice/` yanıtı: `{parola_yenilenme, okunamayan}`.

    Bildirim kartlar ucunun kalıbıyla okunur (`_kartlar`; orkestratör maddesi (d0)-2): program
    dışından bozulmuş sıfırlama anı (geçersiz, yerel saate çevrilemeyen ya da biçimsiz) uç 500
    vermez; `parola_yenilenme` None, `okunamayan` `["parola_yenilenme"]` olur (Genel Bakış'ın
    kartı aynı durumu "okunamadı" diye söyler, bildirim sessizce kaybolmaz). DEK düşmüşse ret
    olduğu gibi yükselir. Yalnız okur.
    """
    return _kartlar({"parola_yenilenme": (lambda: yenilenme_bildirimi(hesap_id), None)})


def _yenilenme_bildirimi(hesap_id: object, gecerli: Suzgec | None) -> dict[str, Any] | None:
    kimlik = denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id)
    if kimlik is None:
        return None
    # Yalnız bildirimin üç sütunu okunur (orkestratör maddesi (d0)-2): program dışından bozulmuş
    # açılış ya da kapanış anı (ORM'nin dönüştürücüsü ValueError yükseltir) bildirimi düşürmez.
    # Sıfırlama anının kendisi okunamıyorsa (geçersiz, yerel saate çevrilemeyen ya da biçimsiz an)
    # okuma düşer; kartlar ucunda ve bildirim ucunda kart `okunamayan` listesine girer (sessizce
    # kaybolmaz, uç 500 dönmez; `_kartlar`, `bildirim_yaniti`).
    hesap = (
        Account.objects.filter(pk=kimlik)
        .values("reset_notice_pending", "reset_at", "reset_kind")
        .first()
    )
    if hesap is None or not hesap["reset_notice_pending"]:
        return None
    if hesap["reset_at"] is None:
        # Program bildirimi anıyla birlikte yazar; biçimsiz an ORM'de None okunur ("zzz").
        raise ValueError("Sıfırlama anı okunamadı.")
    if gecerli is None:
        gecerli = denetim_izi.acik_satir_dogrulayici()
    return {
        "tur": hesap["reset_kind"],
        "zaman": _yerel(hesap["reset_at"]),
        "girisler": _girisler(kimlik, gecerli, sonra=hesap["reset_at"]),
    }


def _kartlar(uretenler: dict[str, tuple[Callable[[], Any], Any]]) -> dict[str, Any]:
    """Kartları birbirinden bağımsız üretir; okunamayanın adı `okunamayan` listesine girer.

    Beklenmeyen bir hata (program dışından bozulmuş bir satır) yalnız o kartı boş bırakır, ön
    yüz bunu uyarı kartıyla söyler — kartlar sessizce kaybolmaz, uç 500 dönmez. DEK düşmüşse
    (oturum istek ortasında kilitlendi) ret olduğu gibi yükselir (409).
    """
    okunamayan: list[str] = []
    ozet: dict[str, Any] = {}
    for ad, (uret, bos) in uretenler.items():
        try:
            ozet[ad] = uret()
        except crypto.KeyMissingError:
            raise
        except Exception:  # noqa: BLE001 — tek kartın hatası öteki kartları düşürmez
            logger.exception("Genel Bakış'ın bütünlük kartı okunamadı (%s).", ad)
            okunamayan.append(ad)
            ozet[ad] = bos
    ozet["okunamayan"] = okunamayan
    return ozet


def _hesap_kimligi(hesap_id: str | None) -> str | None:
    return denetim_izi.kimlik_metni_ya_da_none(Account, hesap_id) if hesap_id else None


def kendi_kartlari(hesap_id: str | None) -> dict[str, Any]:
    """Oturumdaki hesabın kendi kartları (`GET security/integrity/`; her rol; modül başlığı).

    `son_girisler` ve `parola_yenilenme` YALNIZ bu hesabındır (başka hesabın girişi dönmez);
    hesap kimliği verilmezse boştur. `kagit_capasi` denetim izinin son kaydıdır (tasarım
    §4.6.3: son girişler kartında görünür). Yalnız doğrulanan açık kip satırları okunur.
    """
    kimlik = _hesap_kimligi(hesap_id)
    gecerli = denetim_izi.acik_satir_dogrulayici()
    uretenler: dict[str, tuple[Callable[[], Any], Any]] = {"kagit_capasi": (_kagit_capasi, None)}
    if kimlik:
        uretenler["son_girisler"] = (lambda: _girisler(kimlik, gecerli), [])
        uretenler["parola_yenilenme"] = (lambda: _yenilenme_bildirimi(kimlik, gecerli), None)
    ozet = _kartlar(uretenler)
    ozet.setdefault("son_girisler", [])
    ozet.setdefault("parola_yenilenme", None)
    return ozet


def denetim_kartlari(hesap_id: str | None) -> dict[str, Any]:
    """Denetim kartları (`GET security/integrity/audit/`; program yöneticisi ve Denetleme Kurulu).

    `butunluk`: oturumdaki hesabın bir önceki girişinden beri yazılmış `BUTUNLUK` satırları;
    `geri_yukleme`: son geri yükleme kartı; `muhru_tutmayan`: kaydı ya da denetim izi program
    dışından değiştirilmiş görünen hesaplar (canlı).
    """
    kimlik = _hesap_kimligi(hesap_id)
    gecerli = denetim_izi.acik_satir_dogrulayici()
    return _kartlar(
        {
            "butunluk": (lambda: _butunluk_kartlari(kimlik, gecerli), []),
            "geri_yukleme": (lambda: _geri_yukleme_karti(gecerli), None),
            "muhru_tutmayan": (_muhru_tutmayan, []),
        }
    )


def iki_depo_karti() -> dict[str, Any]:
    """İki depo kartı (`GET security/integrity/two-store/`; yalnız program yöneticisi).

    `iki_depo` fark hesaplanamazsa (güvenlik dosyası ya da DEK yok) `None`'dır; sahipsiz
    sarmalın onayla silinmesinin yanıtı da bu karttır.
    """
    return _kartlar({"iki_depo": (_iki_depo_karti, None)})
