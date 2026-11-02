"""Veri dizinindeki küçük gizli JSON dosyalarının atomik yazımı (tasarım §4.5, §4.6.3).

`iz-durumu.json` (çapa ve kilitli kip tohumu; `apps.okul.iz_durumu`) ve
`geri-yukleme-notu.json` (`apps.okul.services.geri_yukleme_notu`) `guvenlik.json`'la aynı
dizinde durur (plan F1b-1 "Denetim izi"). İkisi de yarım yazılmamalıdır: elektrik kesintisi
yarım bir çapa bırakırsa ilk kilit açılışı yanlış "çapa bozuk" uyarısı verir, yarım bir tohum
kilitli satırları mühürsüz bırakırdı.

YAZIM (tasarım §4.6.3 "atomik yazım, Linux'ta 0600"): önce `<ad>.tmp` 0600 kipiyle açılır,
içerik yazılır, `fsync` edilir (aile: `desktop/clean_shutdown.write_marker`), sonra
`os.replace` ile asıl adın yerine konur. POSIX'te geçici dosyanın kipi açıkça 0600'e çekilir
(önceki bir kesintiden kalmış `.tmp` başka kiple durabilir; `O_CREAT`'in kipi yalnız yeni
dosyaya uygulanır). Açılıştaki `umask 077` (tasarım §13 D52) aynı sonucu zaten verir; bu
modül ona güvenmez. Windows'ta dosya kullanıcı profilindedir (`%LOCALAPPDATA%`), kip
anlamsızdır.

Modül yalnız standart kitaplığı kullanır: ORM'siz geri yükleme çekirdeği de çağırır.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

#: Gizli dosyaların POSIX kipi (tasarım §4.5; aile `desktop/paths.py`).
GIZLI_KIP: Final = 0o600


def atomik_json_yaz(yol: Path, veri: Mapping[str, Any]) -> None:
    """`veri`'yi `yol`'a atomik yazar: 0600 geçici dosya → fsync → yerine koy (modül başlığı).

    Hata hâlinde geçici dosya silinir, asıl dosyaya dokunulmaz; `OSError` çağırana gider.
    """
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_name(yol.name + ".tmp")
    baytlar = json.dumps(veri, ensure_ascii=False, indent=2).encode("utf-8")
    bayraklar = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0)
    try:
        tanitici = os.open(gecici, bayraklar, GIZLI_KIP)
        with os.fdopen(tanitici, "wb") as dosya:
            dosya.write(baytlar)
            dosya.flush()
            os.fsync(dosya.fileno())
        if os.name == "posix":
            os.chmod(gecici, GIZLI_KIP)
        os.replace(gecici, yol)
    except BaseException:
        gecici.unlink(missing_ok=True)
        raise
