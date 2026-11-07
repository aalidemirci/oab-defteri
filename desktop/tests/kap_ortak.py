"""Yedek kabını kuran testlerin TEK ortak yardımcısı (toplanmaz: dosya adı `test_` ile başlamaz).

Plan F1b-3 "Kap ve manifesto": kabın bayt düzeni bir kez daha değişirse testler tek yerden uyar;
hiçbir test kabı elle kurmaz. Masaüstü ve backend testleri buradan alır (backend testleri
`desktop`'u zaten içe aktarır; `PYTHONPATH` depo köküdür).

Üretim yazıcıları kullanılabilir kurtarma başlığı ister (`backup_crypto`, "BAŞLIKSIZ YEDEK
ÜRETİLMEZ"). Testler bozuk ve eski kapları da kurmak zorundadır: başlıksız, şema 1 başlıklı, kapsamı
tutmayan, dosya bölümü bozuk kap. Bu yüzden yardımcı yazıcıların kapısının altındaki mühürleme
adımını kullanır; yazıcıların kendisi kendi testlerinde sınanır.
"""

from __future__ import annotations

from typing import Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from desktop.backup_crypto import (
    BOS_YEREL_MANIFESTO,
    DOSYA_BOLUMU_SONU,
    KAPSAM_TAM,
    Manifesto,
    _header_bytes,
    _muhurle,
    private_key_from_data_key,
    recovery_header_from_state,
)


def durum_basligi(durum: Any) -> bytes:
    """Güvenlik durumunun yedek başlığı (TK10 izdüşümü); izdüşümü yoksa boş bayt."""
    baslik = recovery_header_from_state(durum)
    return _header_bytes(baslik) if baslik is not None else b""


def bolum_girdisi(ad: bytes, govde: bytes, *, boy: int | None = None) -> bytes:
    """Dosya bölümünün bir girdisi; `boy` verilirse boy alanı gövdeyi tutmaz (bozuk kap)."""
    return ad + (len(govde) if boy is None else boy).to_bytes(8, "big") + govde


def kap_kur(
    veritabani: bytes,
    dek: bytes,
    *,
    baslik: bytes = b"",
    manifesto: Manifesto = BOS_YEREL_MANIFESTO,
    ham_manifesto: bytes | None = None,
    kapsam: int | None = None,
    dosya_bolumu: bytes | None = None,
    ephemeral: X25519PrivateKey | None = None,
    nonce: bytes | None = None,
) -> bytes:
    """Bu DEK'in yedek anahtarıyla mühürlü kap.

    Kapsam manifestodan gelir. Tam yedekte `dosya_bolumu` verilmezse bölüm yalnız bitiş
    işaretidir. `ham_manifesto` ve `kapsam` mühürlenen manifesto baytlarını ve başlıktaki kapsam
    baytını dışarıdan verir (bozuk kap sınamaları); `ephemeral` ve `nonce` altın vektör içindir.
    """
    bayt = kapsam if kapsam is not None else manifesto.kapsam
    aad, muhurlu = _muhurle(
        veritabani,
        manifesto.baytlar() if ham_manifesto is None else ham_manifesto,
        bayt,
        private_key_from_data_key(dek).public_key(),
        baslik,
        ephemeral=ephemeral,
        nonce=nonce,
    )
    if dosya_bolumu is None and bayt == KAPSAM_TAM:
        dosya_bolumu = DOSYA_BOLUMU_SONU
    return aad + muhurlu + (dosya_bolumu or b"")
