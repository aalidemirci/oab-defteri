"""Ön yüzün F1b-2 ve F1b-3 metinleri sözlükte yazılıdır (docs/sozluk.md; CLAUDE.md "kullanıcıya
görünen her metin sözlüğe uyar").

Ön yüzün konteyneri `docs/`'u görmez; birebirlik burada sınanır (backend konteyneri depo kökünü
`/repo`'da görür; `test_kurtarma_anahtari_pdf._depo_dosyasi` kalıbı). Kapsam: F1b 2. adımın
metin modülleri (Kullanıcılar, Erişim Günlüğü, rol kapısı ve yetki, denetim izi kartları) ve
güvenlik metinleri (F1b 3. adımın ekranları `guvenlik/metinler.ts`'ten okur), kapanış pencereleri.
Her dosyadaki düz `export const AD(: tip)? = "…" (+ "…")*;` dizesi, boşluklar tekleştirilip
tırnaklar (“ ” → ") eşitlenerek sözlükte aranır. Hesaplanan ya da şablon dizesi kapsam dışıdır
(işlevlerin metinleri sözlükte kalıp olarak yazılıdır, ör. "Parola sıfırlandı · gg.aa.yyyy …").
Kullanıcıya görünmeyen sabit (kod, yol) çıkarsa `ISTISNALAR`'a adıyla ve gerekçesiyle girer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from desktop.backup import KAPSAM_METINLERI
from desktop.server import AZAMI_ISTEK_GOVDESI
from desktop.window import KAPANIS_BEKLIYOR_OLAYI

#: Kapsanan ön yüz dosyaları (depo köküne göre).
DOSYALAR = (
    "frontend/src/modules/kullanicilar/metinler.ts",
    "frontend/src/modules/erisim/metinler.ts",
    "frontend/src/modules/oturum/RolKapisi.tsx",
    "frontend/src/modules/oturum/yetki.tsx",
    "frontend/src/modules/butunluk/metinler.ts",
    "frontend/src/modules/guvenlik/metinler.ts",
    "frontend/src/modules/cikis/metinler.ts",
)

#: Kullanıcıya görünmeyen düz dize sabitleri (dosya, ad) → gerekçe. Bugün boştur.
ISTISNALAR: dict[tuple[str, str], str] = {}

_SABIT = re.compile(
    r'export const (\w+)(?::\s*[\w.<>\[\]| ]+)?\s*=\s*((?:"(?:[^"\\]|\\.)*"\s*\+?\s*)+);'
)
_PARCA = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _depo_dosyasi(goreli: str) -> str:
    """Depo kökündeki dosya (yerelde depo kökü, konteynerde `/repo`)."""
    for kok in (Path(__file__).resolve().parents[4], Path("/repo")):
        yol = kok / goreli
        if yol.is_file():
            return yol.read_text(encoding="utf-8")
    pytest.fail(f"{goreli} bulunamadı.")


def _sabitler(kaynak: str) -> dict[str, str]:
    """Kaynaktaki düz dize sabitleri: ad → değer (kaçışlar JSON kuralıyla çözülür)."""
    return {
        eslesme.group(1): "".join(
            json.loads(f'"{parca}"') for parca in _PARCA.findall(eslesme.group(2))
        )
        for eslesme in _SABIT.finditer(kaynak)
    }


def _sade(metin: str) -> str:
    """Boşluklar tekleştirilir, tırnaklar eşitlenir (sözlük satırları da sarılır)."""
    return re.sub(r"\s+", " ", metin.replace("“", '"').replace("”", '"')).strip()


def test_on_yuz_metinleri_sozlukte_yazilidir() -> None:
    sozluk = _sade(_depo_dosyasi("docs/sozluk.md"))
    eksik: list[str] = []
    sayi = 0
    for goreli in DOSYALAR:
        for ad, deger in _sabitler(_depo_dosyasi(goreli)).items():
            if (goreli, ad) in ISTISNALAR:
                continue
            sayi += 1
            if _sade(deger) not in sozluk:
                eksik.append(f"{goreli}: {ad} = {deger!r}")
    assert not eksik, "Sözlükte yazılı olmayan ön yüz metinleri:\n" + "\n".join(eksik)
    # Kapsam boşalmasın (ör. dosya taşındı, kalıp artık eşleşmiyor).
    assert sayi >= 100, sayi


def test_yedek_kapsami_metinleri_konsoldakiyle_birebirdir() -> None:
    """Onay ekranı ve konsol kapsamı aynı sözle söyler (kullanıcı kararı 04.11.2026 "Ekran adları")."""
    sabitler = _sabitler(_depo_dosyasi("frontend/src/modules/guvenlik/metinler.ts"))
    assert {sabitler["KAPSAM_YEREL_METNI"], sabitler["KAPSAM_TAM_METNI"]} == set(
        KAPSAM_METINLERI.values()
    )


def test_ekranin_yedek_siniri_sunucunun_govde_siniridir() -> None:
    """Ekran sunucunun keseceği dosyayı göndermez (kullanıcı kararı 06.11.2026)."""
    kaynak = _depo_dosyasi("frontend/src/modules/guvenlik/yedekBilgisi.ts")
    eslesme = re.search(r"AZAMI_YEDEK_DOSYASI = (\d+) \* 1024 \*\* 3;", kaynak)
    assert eslesme is not None
    assert int(eslesme.group(1)) * 1024**3 == AZAMI_ISTEK_GOVDESI


def test_ekranin_boy_iletisi_sunucununkiyle_aynidir() -> None:
    """Sınırı aşan düz dosyanın iletisi iki yerde aynı sözdür (kullanıcı kararı 05.11.2026)."""
    ekran = re.search(
        r"`(Dosya çok büyük; en çok )\$\{sinirMb\}( MB olabilir\.)`",
        _depo_dosyasi("frontend/src/modules/kisiler/AktarimPaneli.tsx"),
    )
    sunucu = re.search(
        r'"(Dosya çok büyük; en çok )\{settings\.MAX_UPLOAD_SIZE_MB\}( MB olabilir\.)"',
        _depo_dosyasi("backend/shared/yukleme.py"),
    )
    assert ekran is not None and sunucu is not None
    assert ekran.groups() == sunucu.groups()


def test_kapanis_olayi_masaustundekiyle_birebirdir() -> None:
    """Pencere ön yüzün dinlediği olayı yollar (plan F1b-3 "Uzun iş, çarpı, temiz kapanış")."""
    kaynak = _depo_dosyasi("frontend/src/modules/cikis/KapanisPenceresi.tsx")
    eslesme = re.search(r'KAPANIS_BEKLIYOR_OLAYI = "([^"]+)";', kaynak)
    assert eslesme is not None
    assert eslesme.group(1) == KAPANIS_BEKLIYOR_OLAYI


def test_sabit_okuyucu_birlesik_ve_tipli_dizeyi_okur() -> None:
    """Okuyucu `+` ile birleşen çok satırlı dizeyi ve tipli sabiti okur; şablon dizesini okumaz."""
    kaynak = (
        'export const A = "bir " +\n  "iki";\n'
        'export const B: string = "üç \\"dört\\"";\n'
        "export const C = `beş ${x}`;\n"
    )
    assert _sabitler(kaynak) == {"A": "bir iki", "B": 'üç "dört"'}
