"""Gerekçe kutusunun yarım metni: hesap başına tek, şifreli kayıt (tasarım §7 "Yarım kalan metin").

Metin kaydedilince ya da vazgeçilince `temizle` çağrılır. Kutunun ucu ve panodaki "yarım kalan taslak"
kalemi ön yüzle (F1c'nin 11. ve 12. adımları) gelir. Kısa aralıklarla yazıldığı için denetim izine
satır yazmaz: `test_izsiz_yazim.MUAF_ISLEVLER`.
"""

from __future__ import annotations

from apps.oab.models import DraftText
from apps.oab.services import iz


def kaydet(metin: str, *, baglam: str = "") -> None:
    """Hesabın yarım metnini yazar; boş metin kaydı siler (tutulacak yarım metin kalmamıştır)."""
    hesap = iz.hesap_zorunlu()
    if not metin.strip():
        DraftText.objects.filter(account_id=hesap).delete()
        return
    DraftText.objects.update_or_create(
        account_id=hesap, defaults={"text": metin, "context": baglam}
    )


def oku() -> DraftText | None:
    """Oturumdaki hesabın yarım metni."""
    return DraftText.objects.filter(account_id=iz.hesap_zorunlu()).first()


def temizle(baglam: str = "") -> None:
    """Metin kaydedildi ya da vazgeçildi: yarım metin silinir.

    `baglam` verilirse kayıt yalnız o kutunun bağlamındaysa silinir: bir kutunun kaydı ya da vazgeçişi
    hesabın başka kutuya ait yarım metnini silmez (hesap başına tek kayıt; tasarım §7 "Yarım kalan
    metin" — temizlenen, kaydedilen ya da vazgeçilen kutunun metnidir).
    """
    kayitlar = DraftText.objects.filter(account_id=iz.hesap_zorunlu())
    if baglam:
        kayitlar = kayitlar.filter(context=baglam)
    kayitlar.delete()
