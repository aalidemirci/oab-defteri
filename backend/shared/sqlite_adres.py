"""Salt okunur SQLite adresi — ORM'siz okuyucuların tek URI kurucusu (tasarım §4.4.4; plan F1b-2).

Geri yüklemenin iki ORM'siz okuyucusu güncel veritabanını `mode=ro` URI'siyle açar:
`apps.okul.services.geri_yukleme_yetkisi` (parola yolunun hesap denetimi) ve
`apps.okul.services.geri_yukleme_notu.zincir_basi_oku` (kenara alınacak veritabanının zincir
başı). Adres burada, tek yerde kurulur; çünkü `Path.resolve().as_uri()` iki kurulumda
SQLite'ın açamadığı adres üretir ve okuyucu okunabilen veritabanını sessizce "okunamıyor"
sayardı:

* **UNC yol** (`\\\\sunucu\\pay\\OAB\\…`, taşınabilir sürümün `--data-dir`'i): `as_uri()`
  `file://sunucu/pay/…` verir. SQLite URI'de yalnız boş ya da `localhost` authority kabul
  eder (`SQLITE_ALLOW_URI_AUTHORITY` CPython derlemelerinde tanımlı değildir); öteki adlarda
  "invalid uri authority" hatası, `localhost`'ta ise sunucu adı düşer. Burada yol
  authority'siz yazılır: `file:////sunucu/pay/…` (dört eğik çizgi; SQLite yolu `//sunucu/…`
  olarak alır, Windows onu UNC'ye çevirir).
* **Eşlenmiş ağ sürücüsü** (`Z:\\OAB\\…`): Windows'ta `resolve()` sürücüyü UNC yola çevirir.
  Burada yol `resolve()` edilmez, `absolute()` ile mutlak yapılır; sürücü harfi korunur
  (`file:///Z:/OAB/…`).

Yol yüzde kodlanır (`?`, `#`, `%`, boşluk ve Türkçe harf; dosya sistemi kodlamasında
çözülemeyen baytlar `surrogateescape` ile korunur): SQLite `%HH`'yi çözer, `?` ve `#`
ise adresin yolunu bitirirdi. Modül yalnız standart kitaplığa dayanır (geri yükleme yetkisi
okuyucusu Django'suz koşar).
"""

from __future__ import annotations

from pathlib import Path, PurePath
from urllib.parse import quote


def salt_okunur_adres(yol: PurePath) -> str:
    """Veritabanı dosyasının salt okunur (`mode=ro`) SQLite URI'si (modül başlığı).

    `Path` verilirse `absolute()` ile mutlak yapılır (`resolve()` edilmez); saf yol
    (`PureWindowsPath`, `PurePosixPath`) mutlak olmalıdır, değilse `ValueError`.
    """
    if isinstance(yol, Path):
        yol = yol.absolute()
    if not yol.is_absolute():
        raise ValueError("Salt okunur SQLite adresi için mutlak yol gerekir.")
    duz = yol.as_posix()  # POSIX "/a/b"; Windows "C:/a/b" ya da UNC "//sunucu/pay/a"
    if not duz.startswith("/"):
        duz = "/" + duz  # sürücü harfi: "/C:/a/b" (SQLite Windows'ta baştaki "/"yi atar)
    return f"file://{quote(duz, safe='/:', errors='surrogateescape')}?mode=ro"
