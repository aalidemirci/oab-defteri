"""Kilitli kip, çapa ve `iz-durumu.json` (tasarım §4.6.3; plan F1b-1 alt commit c).

DEK yokken iş verisi yazılmaz (tasarım §4.1). Kilitliyken denetim izine yalnız kapalı bir
kümedeki kişisiz sistem olayı düşer (`models.KILITLI_KIP_TURLERI`): `YEDEK` (alındı,
döndürüldü), `GOC` (şema göçü uygulandı), `GUN_ISI` (DEK istediği için ertelendi),
`BUTUNLUK`. Bu satırlar içerik MAC'i taşımaz, hiçbir veri değişikliğini meşrulaştıramaz ve İA
yerine **kilitli kip anahtarıyla** mühürlenir. Bu modül o anahtarın dosyasını ve yazımını
yönetir; satırın kendisini `denetim_izi.kilitli_olay` ekler.

`iz-durumu.json` (`guvenlik.json`'la aynı dizinde; atomik yazım, POSIX'te 0600 —
`apps.okul.gizli_dosya`)::

    {"surum": 1,
     "capa": {"seq": N, "mac": "<N. satırın mac'i>", "muhur": "<HMAC>"},
     "tohum": "<64 onaltılık hane>", "adim": k}

* **Çapa** (`capa_yaz`) her kilitlenmede ve oturum açıkken düzenli kapanışta yazılır
  (`oturum._kilit_izini_yaz`; `KILIT` satırından hemen sonra, anahtarlar düşmeden):
  `{seq, mac}` zincir başıdır, `muhur = HMAC(HKDF(İA, "od-iz-capa/v1"), seq ‖ mac)`.
  Aynı anda `tohum₀ = HKDF(İA, "od-iz-kilitli/v1", tuz = seq ‖ mac)` ve `adim = 0` yazılır.
  `seq ‖ mac` biçimi `shared.kanonik.capa_baytlari`'dadır (altın vektörle donmuş). Yeni
  çapa yazılamazsa eskisi silinir; silinemezse ilk kilit açılışı onu bayat bulur (`capa_yaz`).
* **Kilitli satır** (`_kilitli_yaz`): k'ıncı satır `HMAC(HKDF(tohumₖ, "od-iz-kilitli-mac/v1"),
  kanonik(satır) ‖ prev_mac)` ile mühürlenir, `key_ref = "<çapa seq>:<k>"`. Satırın MAC'i
  hesaplanınca, satır eklenmeden ÖNCE `tohumₖ₊₁ = SHA-256("ileri" ‖ tohumₖ)` ve `adim = k+1`
  dosyaya yazılır, eski tohum silinir (plan F1b-1: "tohum önce dosyada ilerler, sonra satır
  yazılır"). İkisi arasında süreç ölürse sondaki TEK kilitli satır eksik kalır; ilk kilit
  açılışı bunu kesinti sayar (bilgi), daha fazlası uyarıdır (`iz_dogrulama`). İleriye dönük
  güvenli mühürdür: dosyayı bir an okuyan kişi o andan önceki kilitli satırları ve kilit
  açıkken yazılmış hiçbir satırı değiştiremez (kalan risk: o andan sonraki kilitli satırları
  taklit edebilir; bu satırlar veri değiştirmez — tasarım §4.6.3).
* **Dosya yok ya da bozuk** → kilitli satır MÜHÜRSÜZ yazılır: `key_ref` boş, zincir
  anahtarı sırsız `kanonik.MUHURSUZ_ANAHTAR`. Satır zincire bağlıdır (sonraki satırların
  `prev_mac`'i kopmaz) ama mühürlü sayılmaz; ilk kilit açılışı "çapa yok" der.
* **İlk hesaptan önce** (zincir boşken; İA yok) olay YAZILMAZ (plan F1b-1).
* **Geri yükleme notu varken** kilitli satır yazılmaz: çapa eski veritabanınındır. Olay
  nota eklenir, ilk kilit açılışında açık anahtarla `SISTEM` satırı olarak yazılır
  (`services.geri_yukleme_notu`).
* **Kilitli yazım düşmüşse** (tohum dosyada ilerledi, satır yazılmadı: süreç öldü, işlem
  geri alındı, disk doldu) sonraki kilitli satır YAZILMAZ: boşluk sonda kalmalıdır ki ilk
  kilit açılışı onu kesinti (bilgi) saysın; arkasına yazılan satır onu ortaya alır, bulgu
  "eksik kilitli satır" uyarısına döner. Durum veritabanından ve dosyadan okunur (çapanın
  bir önceki adımının satırı yok mu; `_dusmus_yazim_var_mi`): süreç yeniden başlasa da
  sürer, ilk kilit açılışı çapayı yeniler ve kalkar. Arada gelen olay süreç belleğinde bekler
  (`_BELLEKTE_BEKLEYEN`; kendi anıyla) ve ilk kilit açılışında açık anahtarla `SISTEM` satırı
  olarak yazılır (`iz_dogrulama`). Süreç kilit açılmadan biterse bekleyen olay kaybolur;
  olay bekletilirken günlüğe yazılır (dosya adı yazılmaz; R1).

KİP SEÇİMİ (`sistem_olayi`): kullanıcı eylemi olmayan olayın tek kapısıdır. DEK ve İA
bellekteyse (oturum açık) satır açık kipte, `SISTEM` adına yazılır; değilse kilitli kipte.
Seçim ve yazım `oturum.IZ_KIP_KILIDI` altındadır: oturumun kilitlenmesi (`KILIT` satırı,
çapa, anahtarların düşmesi) aynı kilidi tutar, iki iş birbirinin ortasına girmez. Masaüstü
kabuğu bu kapıya `masaustu_kanca` üzerinden gelir: açılıştaki günlük ve göç öncesi yedek ile
göç Django ve tablo hazır olmadan olur; olgular tamponlanır, göçten sonra yazılır (tasarım
§4.2 adım 7-8; `desktop/main.py`).

GÜN İŞİ ERTELEMESİ (`gun_isi_ertelendi`): DEK isteyen gün işi kilitliyken ertelenir;
`GUN_ISI` satırı iş başına günde (Europe/Istanbul) EN ÇOK BİR kez yazılır — saatte bir
yeniden denenen iş her denemede satır doğurmasın. "Bugün yazıldı mı" veritabanından, not
varsa notta ve bellekte bekleyen olaylardan okunur; bekleyen olayın günü kendi anındandır
(`zaman`): süreç yeniden başlasa da aynı gün ikinci satır yazılmaz, dünden bekleyen olay
bugünkünü engellemez.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, time
from pathlib import Path
from typing import Any, Final

from django.db import transaction
from django.utils import timezone

from apps.okul import denetim_izi
from apps.okul.gizli_dosya import atomik_json_yaz
from apps.okul.models import KILITLI_KIP_TURLERI, AuditAction, AuditKeyMode, AuditTrail
from apps.okul.oturum import IZ_KIP_KILIDI, sistem_olarak
from apps.okul.services import geri_yukleme_notu
from shared import crypto, kanonik

logger = logging.getLogger("oab_defteri.okul")

DOSYA_ADI: Final = "iz-durumu.json"
SURUM: Final = 1
_ONALTILIK: Final = frozenset("0123456789abcdef")


class IzDurumuYok(LookupError):
    """`iz-durumu.json` yok (hiç kilitlenmemiş ya da silinmiş)."""


class IzDurumuBozuk(ValueError):
    """`iz-durumu.json` okunamıyor ya da beklenen biçimde değil."""


@dataclass(frozen=True)
class IzDurumu:
    """`iz-durumu.json`'ın içeriği: çapa ve kilitli kip tohumu (modül başlığı)."""

    capa_seq: int
    capa_mac: str
    muhur: str
    tohum: bytes = field(repr=False)
    adim: int

    def sozluk(self) -> dict[str, Any]:
        return {
            "surum": SURUM,
            "capa": {"seq": self.capa_seq, "mac": self.capa_mac, "muhur": self.muhur},
            "tohum": self.tohum.hex(),
            "adim": self.adim,
        }


def dizin() -> Path:
    """`guvenlik.json`'un dizini (plan F1b-1: iki dosya onunla aynı dizindedir)."""
    # Geç içe aktarım: güvenlik çekirdeği bu modülü kilit açılışında kullanır.
    from apps.okul.services import app_password

    return app_password.state_path().parent


def yol() -> Path:
    return dizin() / DOSYA_ADI


def _hex_mi(deger: object, uzunluk: int) -> bool:
    return isinstance(deger, str) and len(deger) == uzunluk and set(deger) <= _ONALTILIK


def _tamsayi_mi(deger: object, en_az: int) -> bool:
    return isinstance(deger, int) and not isinstance(deger, bool) and deger >= en_az


def oku() -> IzDurumu:
    """Dosyayı okur ve biçimini denetler; yoksa `IzDurumuYok`, bozuksa `IzDurumuBozuk`.

    Mühür burada DENETLENMEZ (İA ister); onu ilk kilit açılışı yapar (`iz_dogrulama`).
    """
    dosya = yol()
    if not dosya.exists():
        raise IzDurumuYok(DOSYA_ADI)
    try:
        veri: Any = json.loads(dosya.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise IzDurumuBozuk(DOSYA_ADI) from exc
    capa = veri.get("capa") if isinstance(veri, dict) else None
    if (
        not isinstance(veri, dict)
        or veri.get("surum") != SURUM
        or not isinstance(capa, dict)
        or not _tamsayi_mi(capa.get("seq"), 1)
        or not _hex_mi(capa.get("mac"), 64)
        or not _hex_mi(capa.get("muhur"), 64)
        or not _hex_mi(veri.get("tohum"), 2 * kanonik.TOHUM_BAYT)
        or not _tamsayi_mi(veri.get("adim"), 0)
        or veri["adim"] > denetim_izi.AZAMI_ADIM
    ):
        raise IzDurumuBozuk(DOSYA_ADI)
    return IzDurumu(
        capa_seq=int(capa["seq"]),
        capa_mac=str(capa["mac"]),
        muhur=str(capa["muhur"]),
        tohum=bytes.fromhex(str(veri["tohum"])),
        adim=int(veri["adim"]),
    )


def _yaz(durum: IzDurumu) -> None:
    atomik_json_yaz(yol(), durum.sozluk())


def yeni_capa(ia: bytes, seq: int, mac: str) -> IzDurumu:
    """Zincir başı `(seq, mac)` için çapa: mühür, `tohum₀`, `adim = 0` (tasarım §4.6.3)."""
    return IzDurumu(
        capa_seq=seq,
        capa_mac=mac,
        muhur=kanonik.capa_muhru(crypto.audit_anchor_key(ia), seq, mac),
        tohum=denetim_izi.kilitli_tohum(ia, seq, mac),
        adim=0,
    )


def capa_yaz() -> bool:
    """Zincir başını çapa olarak yazar, kilitli kip tohumunu sıfırlar. HATA YÜKSELTMEZ.

    Kilitlenmede ve oturum açıkken düzenli kapanışta (`oturum._kilit_izini_yaz`), ilk kilit
    açılışında çapa bulgusu ya da geri yükleme notu varsa (`iz_dogrulama.tamamla`) çağrılır.
    Mühür ve tohum çapanın satırını mühürleyen İA'yla hesaplanır (bellekteki DEK'le
    çözülür). Zincir boşsa (ilk hesaptan önce) ya da DEK bellekte değilse (oturum servis
    içinden kapandı; çökmeyle aynı hâl) yazılmaz. Yazılamazsa olay günlüğe düşer, False döner:
    kilit ve giriş bunun için durmaz.

    YAZILAMAYAN ÇAPA ESKİSİNİ GEÇERSİZ KILAR. Atomik yazım asıl dosyaya dokunmadan düşer:
    önceki kilitlenmenin çapası geçerli kalsaydı ilk kilit açılışı onu doğrular, bu oturumun
    kuyruğu (açık satırlar ve `KILIT`) çapasız kalır, silinmesi görünmezdi. Bu yüzden eski
    dosya silinmeye çalışılır: sonraki kilitli satırlar mühürsüz yazılır, ilk kilit açılışı
    "çapa yok" der. Silme de düşerse (dosyayı tutan virüs tarayıcısı) ilk kilit açılışı,
    çapadan sonra açık kipte bir `KILIT` satırı görüp "çapa bayat" der (`iz_dogrulama`).
    """
    with IZ_KIP_KILIDI:
        try:
            bas = denetim_izi.zincir_basi()
            if bas is None:
                return False
            ia = denetim_izi.sirayi_muhurleyen_ia(bas[0])
            if ia is None:
                raise denetim_izi.IzYazilamadi("Çapanın satırını mühürleyen iz anahtarı yok.")
            _yaz(yeni_capa(ia, *bas))
        except crypto.KeyMissingError:
            logger.info("Veri anahtarı bellekte değil; denetim izi çapası yazılmadı.")
            return False
        except Exception:  # noqa: BLE001 — kilit ve giriş çapa yüzünden durmaz
            logger.warning("Denetim izi çapası yazılamadı.", exc_info=True)
            _eski_capayi_gecersiz_kil()
            return False
    logger.info("Denetim izi çapası yazıldı (%d).", bas[0])
    return True


def _eski_capayi_gecersiz_kil() -> None:
    """Yazılamayan çapanın yerine eskisini siler (`capa_yaz` belge dizesi). Hata yükseltmez."""
    try:
        yol().unlink(missing_ok=True)
    except Exception:  # noqa: BLE001 — silinemezse ilk kilit açılışı "çapa bayat" der
        logger.error(
            "Eski denetim izi çapası silinemedi; ilk kilit açılışı çapayı bayat bulacak.",
            exc_info=True,
        )
    else:
        logger.warning("Eski denetim izi çapası silindi; ilk kilit açılışı 'çapa yok' diyecek.")


# ---------------------------------------------------------------------------
# Sistem olayları: kip seçimi ve kilitli yazım
# ---------------------------------------------------------------------------
def _olay_kaydi(
    eylem: str,
    model: str,
    object_id: str,
    changed_fields: Iterable[str],
    values: Mapping[str, Sequence[Any]] | None,
) -> dict[str, Any]:
    """Olayın denetlenmiş, kanonik ilkel biçimi (geri yükleme notunda bekleyen olay olarak da).

    Yedek dosyasının kimliği yalnız programın ürettiği addır (`denetim_izi.yedek_kimligi`):
    elle konmuş ya da yeniden adlandırılmış dosyanın adı serbest metindir, satıra ve nota
    girmez (R1); olay boş kimlikle kalır.
    """
    if eylem not in KILITLI_KIP_TURLERI:
        raise denetim_izi.IzYazilamadi(f"Sistem olayı yalnız kapalı kümedendir: {eylem}")
    alanlar = list(changed_fields)
    if not all(isinstance(ad, str) for ad in alanlar):
        raise denetim_izi.IzYazilamadi("Değişen alanlar yalnız alan adlarıdır.")
    if model == denetim_izi.YEDEK_DOSYASI:
        object_id = denetim_izi.yedek_kimligi(object_id)
    return {
        "eylem": eylem,
        "model": model,
        "object_id": object_id,
        "changed_fields": alanlar,
        "values": denetim_izi.izinli_degerler(model, values),
    }


def _kilitli_muhur(durum: IzDurumu | None) -> denetim_izi.KilitliMuhur:
    """Sıradaki kilitli satırın mührü; dosya yoksa ya da bozuksa mühürsüz (modül başlığı)."""
    if durum is None:
        return denetim_izi.KilitliMuhur(zincir_anahtari=kanonik.MUHURSUZ_ANAHTAR, key_ref="")

    def ilerlet() -> None:
        # Tohum dosyada satırdan ÖNCE ilerler; eski tohum dosyadan silinir (plan F1b-1).
        _yaz(replace(durum, tohum=kanonik.ileri_tohum(durum.tohum), adim=durum.adim + 1))

    return denetim_izi.KilitliMuhur(
        zincir_anahtari=crypto.audit_locked_mac_key(durum.tohum),
        key_ref=denetim_izi.kilitli_ref(durum.capa_seq, durum.adim),
        kaydetmeden_once=ilerlet,
    )


#: Düşen bir kilitli yazımdan sonra ilk kilit açılışını bekleyen olaylar (modül başlığı;
#: `IZ_KIP_KILIDI` altında). Her biri geri yükleme notundaki bekleyen olayla aynı biçimdedir
#: (`_olay_kaydi` + `zaman`).
_BELLEKTE_BEKLEYEN: list[dict[str, Any]] = []


def bellekte_bekleyenler() -> list[dict[str, Any]]:
    """Bellekte bekleyen olayların kopyası (ilk kilit açılışı yazar; `iz_dogrulama`)."""
    with IZ_KIP_KILIDI:
        return [dict(olay) for olay in _BELLEKTE_BEKLEYEN]


def bellekte_bekleyenleri_birak(adet: int) -> None:
    """İlk `adet` bekleyen olay yazıldı (kilit açılışının işlemi commit edildi): listeden düşer."""
    with IZ_KIP_KILIDI:
        del _BELLEKTE_BEKLEYEN[:adet]


def _dusmus_yazim_var_mi(durum: IzDurumu) -> bool:
    """Tohum dosyada ilerlemiş ama son adımın satırı yok mu? (modül başlığı; işlemin içinde)

    Çapadan sonraki `adim - 1`'inci kilitli satır veritabanında yoksa bir önceki kilitli yazım
    düşmüştür: tohum ilerledi, satır yazılmadı.
    """
    if durum.adim == 0:
        return False
    return not AuditTrail.objects.filter(
        seq__gt=durum.capa_seq,
        key_mode=AuditKeyMode.KILITLI,
        key_ref=denetim_izi.kilitli_ref(durum.capa_seq, durum.adim - 1),
    ).exists()


def _bellekte_beklet(olay: dict[str, Any]) -> None:
    """Olayı ilk kilit açılışına bırakır (kendi anıyla); günlüğe düşer, dosya adı yazılmaz."""
    _BELLEKTE_BEKLEYEN.append({**olay, "zaman": geri_yukleme_notu.an_metni()})
    logger.warning(
        "Önceki kilitli denetim izi yazımı tamamlanamamış; %s olayı ilk kilit açılışına "
        "bırakıldı (bekleyen: %d).",
        olay["eylem"],
        len(_BELLEKTE_BEKLEYEN),
    )


def _kilitli_yaz(olay: dict[str, Any]) -> AuditTrail | None:
    """Kilitli kipte yazar (`IZ_KIP_KILIDI` ve `SISTEM` bağlamı çağırandadır).

    Geri yükleme notu varsa olay nota eklenir (None); zincir boşsa yazılmaz (None); bir önceki
    kilitli yazım düşmüşse olay bellekte bekler (None; modül başlığı). Bu yazımın kendisi
    tohum ilerledikten SONRA düşerse (satır ya da işlemin sonu yazılamadı) olay da bellekte
    bekler (None): boşluk artık sondadır, olay kaybolmaz. Tohum ilerlemeden düşen yazım hata
    yükseltir (boşluk yoktur; çağıran günlüğe düşürür).
    """
    notun_dizini = dizin()
    if geri_yukleme_notu.var_mi(notun_dizini):
        geri_yukleme_notu.bekleyen_olay_ekle(notun_dizini, olay)
        logger.info("Geri yükleme notu var; %s olayı ilk kilit açılışına bırakıldı.", olay["eylem"])
        return None
    durum: IzDurumu | None = None
    try:
        with transaction.atomic():
            if not AuditTrail.objects.exists():
                return None  # ilk hesaptan önce olay yazılmaz (plan F1b-1)
            try:
                durum = oku()
            except (IzDurumuYok, IzDurumuBozuk):
                logger.warning("iz-durumu.json yok ya da bozuk; kilitli satır mühürsüz yazılıyor.")
                durum = None
            if _BELLEKTE_BEKLEYEN or (durum is not None and _dusmus_yazim_var_mi(durum)):
                # Boşluk sonda kalsın: ilk kilit açılışı onu kesinti sayar (plan F1b-1).
                _bellekte_beklet(olay)
                return None
            return denetim_izi.kilitli_olay(
                olay["eylem"],
                model=olay["model"],
                object_id=olay["object_id"],
                changed_fields=olay["changed_fields"],
                values=olay["values"],
                muhur=_kilitli_muhur(durum),
            )
    except Exception:
        if durum is None or not _tohum_ilerledi_mi(durum):
            raise
        logger.warning(
            "Kilitli denetim izi satırı tohum ilerledikten sonra yazılamadı.", exc_info=True
        )
        _bellekte_beklet(olay)
        return None


def _tohum_ilerledi_mi(durum: IzDurumu) -> bool:
    """Düşen yazımda tohum dosyada ilerlemiş mi? (`_kilitli_yaz`; okunamıyorsa hayır)"""
    try:
        return oku().adim > durum.adim
    except (IzDurumuYok, IzDurumuBozuk):
        return False


def sistem_olayi(
    eylem: str,
    *,
    model: str,
    object_id: str,
    changed_fields: Iterable[str] = (),
    values: Mapping[str, Sequence[Any]] | None = None,
) -> AuditTrail | None:
    """Kullanıcı eylemi olmayan olayın tek kapısı: oturum açıksa açık kip, değilse kilitli kip.

    Yazar daima `SISTEM`'dir. Tür kilitli kipin kapalı kümesindendir (açık kipte de: sistem
    olayı yalnız bunlardır). Yazılan satırı döndürür; ilk hesaptan önce, geri yükleme notu
    varken (olay nota bırakıldı) ya da düşen bir kilitli yazımdan sonra (olay bellekte bekler)
    None. Öteki hatalarda hata yükseltir: çağıran (masaüstü kancası) günlüğe düşürür.
    """
    olay = _olay_kaydi(eylem, model, object_id, changed_fields, values)
    with IZ_KIP_KILIDI, sistem_olarak():
        if crypto.is_unlocked() and crypto.active_audit_key() is not None:
            try:
                with transaction.atomic():
                    return denetim_izi.olay(
                        eylem,
                        model=model,
                        object_id=olay["object_id"],
                        changed_fields=olay["changed_fields"],
                        values=olay["values"],
                    )
            except denetim_izi.IzAnahtariBellekteDegil:
                # Oturum tam bu an servis içinden kapandı (`OTURUM.kapat`): kilitli kip.
                logger.info("Oturum kapandı; %s olayı kilitli kipte yazılıyor.", eylem)
        return _kilitli_yaz(olay)


# ---------------------------------------------------------------------------
# Gün işi ertelemesi
# ---------------------------------------------------------------------------
def _bugunun_baslangici() -> datetime:
    """Bugünün (Europe/Istanbul) başlangıcı, saat dilimli."""
    return timezone.make_aware(datetime.combine(timezone.localdate(), time.min))


def _bugun_bekliyor_mu(ad: str) -> bool:
    """İşin bugünün (Europe/Istanbul) anıyla bekleyen bir `GUN_ISI` olayı var mı? (not, bellek)

    Bekleyen olayın günü kendi anındandır (`zaman`); anı okunamayan olay bugünün sayılmaz.
    """
    bekleyen: list[Any] = list(_BELLEKTE_BEKLEYEN)
    try:
        notu = geri_yukleme_notu.oku(dizin())
    except geri_yukleme_notu.NotOkunamadi:
        notu = None
    if notu:
        bekleyen += notu.get("bekleyen_olaylar", [])
    bugun = timezone.localdate()
    for olay in bekleyen:
        if not isinstance(olay, dict):
            continue
        if olay.get("eylem") != AuditAction.GUN_ISI or olay.get("object_id") != ad:
            continue
        an = geri_yukleme_notu.zaman_coz(olay.get("zaman"))
        if an is not None and timezone.localdate(an) == bugun:
            return True
    return False


def _bugun_yazildi_mi(ad: str) -> bool:
    if AuditTrail.objects.filter(
        action=AuditAction.GUN_ISI,
        model=denetim_izi.GUN_ISI_ERTELEME,
        object_id=ad,
        at__gte=_bugunun_baslangici(),
    ).exists():
        return True
    return _bugun_bekliyor_mu(ad)


def gun_isi_ertelendi(ad: str) -> bool:
    """DEK istediği için ertelenen gün işinin `GUN_ISI` satırı; günde bir (modül başlığı).

    Satır yazıldıysa (ya da nota ya da belleğe bırakıldıysa) True; bugün zaten yazılmışsa ya
    da zincir boşsa False.
    """
    with IZ_KIP_KILIDI:
        if _bugun_yazildi_mi(ad):
            return False
        satir = sistem_olayi(AuditAction.GUN_ISI, model=denetim_izi.GUN_ISI_ERTELEME, object_id=ad)
        return satir is not None or _bugun_bekliyor_mu(ad)


def _reset_for_tests() -> None:
    """Yalnız testler için: bellekte bekleyen olaylar süreç içidir, testler arasında sızar."""
    with IZ_KIP_KILIDI:
        _BELLEKTE_BEKLEYEN.clear()
