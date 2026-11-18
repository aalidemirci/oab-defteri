"""Resmî evrak antedi (letterhead) — ailenin `shared/letterhead.py`'sinden UYARLA.

documents/base.html ortak resmî antedi kullanır:

    T.C.
    <İLÇE> KAYMAKAMLIĞI          (kurum satırı TAMAMI büyük harf)
    <Okul Adı> Müdürlüğü          (birim satırı — Resmî Yazışma Usulü)

Aile iskeletindeki uyarlama: kaynaktaki ortam değişkeni geri-düşüşleri atıldı — kimlik
tek kaynaktan (``apps.okul.models.SchoolConfig``) çözülür ve buraya parametre
olarak geçer; ``shared`` (altyapı) katmanı model import etmez (katman kuralı
korunur). İlçe boşsa antette yer-tutucu noktalar görünür.
"""

from __future__ import annotations

from shared.text import tr_upper

#: Birliğin kendi belgelerinde antedin altına eklenen satır (tasarım §9.1-8 "Birlik antedi"; plan
#: F1c kararları "Evrak biçimi"). Birlik okul bünyesinde kurulur ve okulun adını alır (OAB Yön.
#: md. 5): ayrı logo yoktur, satır RYUE md. 10/2'deki birim satırı gibi okul antedinin altındadır.
#: Kurum kodu antede girmez. Evrak hattındaki kullanımı `shared.evrak.birlik_anteti`'dir.
BIRLIK_SATIRI = "Okul-Aile Birliği"


def letterhead_authority(district: str | None = None) -> str:
    """Antedin ikinci satırı: '<İLÇE> KAYMAKAMLIĞI' (ilçe yoksa yer-tutucu).

    İlçe adı TÜRKÇE büyük harfe çevrilir: ayarda "Beşiktaş" yazılıysa antet
    "Beşiktaş KAYMAKAMLIĞI" basıyordu (kurum satırı tamamı büyük harf olmalı).
    Çıplak `.upper()` kullanılmaz (i→I tuzağı).
    """
    name = (district or "").strip()
    return f"{tr_upper(name)} KAYMAKAMLIĞI" if name else "…………… KAYMAKAMLIĞI"


def letterhead_unit(school_name: str) -> str:
    """Antedin birim satırı: '<Okul Adı> Müdürlüğü' (ad boşsa yer-tutucu).

    Resmî yazışma usulünde okul ayrı, "Okul Müdürlüğü" ayrı satır DEĞİLDİR;
    birim satırı okul adıyla birlikte tek satırdır.
    """
    name = " ".join((school_name or "").split())
    if not name:
        return "…………… Müdürlüğü"
    return name if name.endswith("Müdürlüğü") else f"{name} Müdürlüğü"


#: Resmî yazının muhatabı olan millî eğitim müdürlükleri (RYUE md. 14/5'in birim satırı; ilk harfleri
#: büyük, md. 14/2).
MEM_ILCE = "İlçe Millî Eğitim Müdürlüğü"
MEM_IL = "İl Millî Eğitim Müdürlüğü"


def mem_muhatabi(birim: str, *, il: str | None, ilce: str | None) -> tuple[str, str]:
    """Okulun il ya da ilçe millî eğitim müdürlüğüne yazısının muhatabı: (idare, birim).

    Kullanıcı kararı S11 (a) (plan F2 §9, 15.11.2026): RYUE md. 14/5'in ana kuralı iki hâlde de
    uygulanır — ilk satır bağlı olunan mülki idare büyük harfle ve yönelme ekiyle ("<İLÇE>
    KAYMAKAMLIĞINA", "<İL> VALİLİĞİNE"; md. 14/2), ikinci satır parantez içinde birim (çizici
    parantezi ekler). Ad boşsa yer tutucu basılır. Muhatap basımda düzenlenebilir alandır: bu işlev
    yalnız önerisidir (plan F2 §7 U20).
    """
    if birim == MEM_ILCE:
        ad = (ilce or "").strip()
        return (f"{tr_upper(ad)} KAYMAKAMLIĞINA" if ad else "…………… KAYMAKAMLIĞINA", MEM_ILCE)
    if birim == MEM_IL:
        ad = (il or "").strip()
        return (f"{tr_upper(ad)} VALİLİĞİNE" if ad else "…………… VALİLİĞİNE", MEM_IL)
    raise ValueError("Muhatap birimi il ya da ilçe millî eğitim müdürlüğü olmalı.")


def letterhead_context(
    *,
    school_name: str,
    unit: str = "",
    district: str | None = None,
    principal_name: str | None = None,
) -> dict[str, str]:
    """PDF şablonları için ortak antet bağlamı (T.C. + kaymakamlık + okul + birim).

    `principal_name` UYGUNDUR/imza bloklarında kullanılır.
    """
    return {
        "tc": "T.C.",
        "authority": letterhead_authority(district),
        "school_name": school_name,
        "unit": unit,
        "unit_line": letterhead_unit(school_name),
        "principal_name": (principal_name or "").strip(),
    }
