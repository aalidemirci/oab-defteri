"""Son oturum kartı — beklenmedik kapanıştan sonra pano uyarısı (T15; tasarım §4.2 adım 3, §13 D4).

Masaüstü kabuğu açılışta önceki oturumun temiz kapanış işaretini okur ve sonucu
`OD_ONCEKI_OTURUM` ile süreç içindeki backend'e taşır (`desktop/clean_shutdown.py`).
İşaret yoksa önceki oturum düzensiz bitmiştir (elektrik kesintisi, zorla
sonlandırma); WAL'deki son kayıtlar diske yazılmamış olabilir. Pano bu yüzden
"son oturumdaki kayıtları kontrol edin" kartını gösterir.

Aile iskeletinde kartın okuyucusu ve bu sürecin başlangıç damgası kütüphane
uygulamasındaydı; OAB'de okul çekirdeğindedir (`OkulConfig.ready` damgayı
koyar). Damga, ileride kartta listelenecek "son oturumdaki kayıtlar"ın üst
sınırıdır: bu süreçten ÖNCE yazılmış kayıtlar.

**"Kontrol ettim"** kartı bu oturum için kapatır. Onay SÜREÇ İÇİNDEDİR (dosyaya
ya da veritabanına yazılmaz): bu oturum temiz kapanırsa sonraki açılışta kart
zaten çıkmaz; yine düzensiz biterse yeniden çıkması doğrudur. Kart kişisel veri
taşımaz.
"""

from __future__ import annotations

import threading
from datetime import datetime

from django.utils import timezone

_kilit = threading.Lock()
_kapanis_onaylandi = False
_surec_baslangici: datetime | None = None


def mark_process_start(now: datetime | None = None) -> datetime:
    """Bu sürecin başlangıcını işaretler (bir kez; `OkulConfig.ready`)."""
    global _surec_baslangici
    with _kilit:
        if _surec_baslangici is None:
            _surec_baslangici = now or timezone.now()
        return _surec_baslangici


def process_started_at() -> datetime:
    """Bu süreç (oturum) ne zaman başladı? İşaret yoksa şimdi işaretlenir."""
    return mark_process_start()


def previous_session_unexpected() -> bool:
    """Önceki oturum beklenmedik biçimde mi kapandı? (masaüstünün `OD_ONCEKI_OTURUM`'u)

    Değişken yoksa (geliştirme sunucusu, testler) `False`: kart gösterilmez.
    """
    from desktop.clean_shutdown import PreviousSession, previous_session_from_env

    return previous_session_from_env() is PreviousSession.UNEXPECTED


def kart_gosterilsin() -> bool:
    """Kart gösterilsin mi? (önceki oturum düzensiz + bu oturumda onaylanmadı)"""
    with _kilit:
        onaylandi = _kapanis_onaylandi
    return not onaylandi and previous_session_unexpected()


def onayla() -> None:
    """'Kontrol ettim': kart bu oturum boyunca gösterilmez."""
    global _kapanis_onaylandi
    with _kilit:
        _kapanis_onaylandi = True


def ozet() -> dict[str, object]:
    """Pano kartının kişisiz özeti."""
    return {
        "unexpected_shutdown": kart_gosterilsin(),
        "process_started_at": process_started_at().isoformat(),
    }


def _reset_for_tests() -> None:
    """Yalnız testler: onayı sıfırlar (süreç damgası korunur)."""
    global _kapanis_onaylandi
    with _kilit:
        _kapanis_onaylandi = False
