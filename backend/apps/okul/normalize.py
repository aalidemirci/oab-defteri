"""Saf (DB'siz) normalize ediciler — sınıf metni, Türkçe büyük harf ve sıralama, ad bölme.

Aile iskeletinden alındı (iskelet bunu atalarının `apps/okul/normalize.py`
dosyasından sadeleştirmişti): TCKN/telefon/doğum tarihi/cinsiyet normalize
edicileri YOKTUR — program bu verileri hiç toplamaz (tasarım §3.4). Öğrenci sicili
ve okul numarasının kör indeks normalleştirmesi F1b 5. adımda öğrenci tarafıyla
söküldü (tasarım §5.1 ALMA).

Sınıf metni ayrıştırması (`normalize_class_section`) KALDI: veli listesindeki
öğrencinin sınıfı düz metindir ve yazımı normalleştirilir (plan "F1b-5 uygulama
kararları"; tasarım §5.1 `ParentRoster`). Ayrıştırma seviye kümesiyle
PARAMETRİKTİR; varsayılan küme okul içi sabittir (`GRADE_LEVELS`). Okul öncesi grupları
("Anasınıfı-A", "5 Yaş-A") seviye DEĞİLDİR ve ayrı çözülür (`normalize_preschool_group`);
okul öncesi izi taşıyan metin seviyeye hiç düşmez.

Saf fonksiyonlardır — kolay test edilir (tests/test_normalize).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection

from shared.text import tr_upper as _tr_upper

#: Okulda geçerli sınıf seviyeleri — OKUL İÇİ SABİT (1-12: ilkokul, ortaokul,
#: lise). Ders çizelgesine ya da okul türüne bağlı DEĞİLDİR; kademeye göre
#: daraltma okul kartının `levels` alanıyla gelir (tasarım §5.1; plan §2.2 adım 4).
GRADE_LEVELS: tuple[int, ...] = tuple(range(1, 13))

#: Hazırlık sınıfının seviye kodu (aile temsili: etiket 'Hz/A'). Yalnız çağıran
#: seviye kümesine koyduğunda tanınır (`normalize_class_section(valid_levels=…)`).
PREP_LEVEL = 0

# Türkçe karakter → ASCII büyük. YALNIZ anahtar kelime eşlemesi içindir
# ('HAZIRLIK' tanıma); şube harfine UYGULANMAZ — bkz. `_ascii_upper` / `tr_upper`.
_TR_UPPER_MAP = str.maketrans(
    {
        "ş": "S",
        "Ş": "S",
        "ı": "I",
        "İ": "I",
        "ğ": "G",
        "Ğ": "G",
        "ü": "U",
        "Ü": "U",
        "ö": "O",
        "Ö": "O",
        "ç": "C",
        "Ç": "C",
    }
)

#: Hazırlık sınıfını metinden tanıma deseni ('HAZIRLIK/A', 'HAZ A', 'HZ-B'…).
_PREP_RE = re.compile(r"\bHA?Z(IRLIK)?\b")


#: Şube harfi olabilecek karakterler (Türk alfabesi + ASCII).
_SECTION_CHARS = r"A-Za-zÇĞİÖŞÜçğıöşü"


def _ascii_upper(value: str) -> str:
    """Türkçe karakterleri ASCII'ye indirip büyük harfe çevirir (ANAHTAR KELİME eşlemesi).

    YALNIZ anahtar kelime araması içindir ('HAZIRLIK' tanıma gibi). Şube harfi
    için KULLANILMAZ: 'İ' ile 'I'yı tek harfe katlar — bkz. `tr_upper`.
    """
    return value.translate(_TR_UPPER_MAP).upper()


def tr_upper(value: str) -> str:
    """Türkçeye uygun büyük harf ('10/i' → '10/İ', '9/ş' → '9/Ş').

    ŞUBE HARFİ KATLAMASININ TEK DOĞRU YOLU BUDUR. `_ascii_upper` ile katlamak
    (aile iskeletinin 30.08.2026 öncesi davranışı) Türk alfabesinin ayrı harflerini birleştirir:
    e-Okul sınıf listesi şubeleri Türk alfabesi sırasıyla açar (…G, H, I, İ,
    J, K…), yani orta ölçekli bir okulda **hem 10/I hem 10/İ** bulunur. ASCII
    katlaması bu iki şubeyi tek şubeye çökertip iki ayrı sınıfın öğrencilerini
    sessizce aynı şubeye yazardı — gerçek bir e-Okul ihracında yakalandı.
    """
    return _tr_upper(value)  # tek uygulama: shared/text.py


#: Türk alfabesinin KENDİ harfleri: aksan ayıklamasından MUAFTIR. NFD ayrışması
#: 'İ'yi 'I' + birleşen noktaya, 'Ç'yi 'C'ye indirir; ayıklama bu harfleri
#: yutarsa Türkçenin AYRI harfleri tek harfe çöker — `tr_upper`'ın gerekçesinin
#: aynısı (10/I ile 10/İ iki ayrı şubedir).
_KORUNAN_HARFLER = frozenset("ÇĞIİÖŞÜçğıiöşü")

#: NFD ayrışmasının Türkçe için YANLIŞ ya da eksik sonuç verdiği harfler.
#: 'Î' ayrışınca NOKTASIZ 'I'ya iner; oysa düzeltme işaretli î Türkçede
#: NOKTALI i'dir ("millî", "Kâmil"). Ayrışmayan Latin harfleri (Ø, Æ, Ł…) da
#: elle eşlenir: ayıklama onlara dokunmaz, alfabe dışında kalırlardı.
_AKSAN_ISTISNALARI = {
    "Î": "İ",
    "Í": "İ",
    "Ì": "İ",
    "Ï": "İ",
    "Ĩ": "İ",
    "Ī": "İ",
    "Į": "İ",
    "Ø": "O",
    "Œ": "O",
    "Æ": "A",
    "Đ": "D",
    "Ð": "D",
    "Ł": "L",
    "Þ": "T",
    "ø": "o",
    "œ": "o",
    "æ": "a",
    "đ": "d",
    "ð": "d",
    "ł": "l",
    "þ": "t",
}

#: Karakter başına bir kez hesaplanan katlama (her kayıt ve her arama çağırır).
_AKSAN_ONBELLEGI: dict[str, str] = {}


def _harf_katla(ch: str) -> str:
    """Tek karakterin aksansız karşılığı; çözülemiyorsa karakterin kendisi."""
    if ch in _KORUNAN_HARFLER:
        return ch
    eslenik = _AKSAN_ISTISNALARI.get(ch)
    if eslenik is not None:
        return eslenik
    ayrisik = unicodedata.normalize("NFD", ch)
    temiz = "".join(parca for parca in ayrisik if not unicodedata.combining(parca))
    # Uzunluk 1:1 KALMALI: anahtar alanları girdiyle aynı boyda saklanır
    # (`Work.sort_key` 500 hane) ve Hangul gibi yazılar NFD'de birden çok
    # birleşmeyen parçaya ayrılır. Ayrışma tek harfe inmiyorsa dokunulmaz.
    return temiz if len(temiz) == 1 else ch


def fold_diacritics(value: object) -> str:
    """Düzeltme işaretli ve aksanlı Latin harflerini düz karşılığına indirir.

    'Kâmil' → 'Kamil', 'Rüzgâr' → 'Rüzgar', 'Émile' → 'Emile'. TÜRK ALFABESİNİN
    HARFLERİNE DOKUNMAZ: Ç/Ğ/I/İ/Ö/Ş/Ü olduğu gibi kalır, yani 'ılık' ile
    'ilik' ayrı kalmayı sürdürür.

    Gerekçe iki yönlüdür: düzeltme işareti çoğu klavyede zahmetlidir, kullanıcı
    "rüzgar" yazar ama künye "Rüzgâr" girilmiştir (arama); ve 'Â' Türk
    alfabesinde bulunmadığı için sıralamada harflerin önüne düşerdi (sıralama).
    """
    metin = "" if value is None else str(value)
    sonuc: list[str] = []
    for ch in metin:
        katlanmis = _AKSAN_ONBELLEGI.get(ch)
        if katlanmis is None:
            katlanmis = _harf_katla(ch)
            _AKSAN_ONBELLEGI[ch] = katlanmis
        sonuc.append(katlanmis)
    return "".join(sonuc)


#: Türk alfabesi sırası — şube harfi artık katlanmadığı için sıralama da
#: Türkçeleşmek ZORUNDA: kod noktası sırasında Ç/Ğ/İ/Ö/Ş/Ü harfleri 'Z'den
#: BÜYÜKTÜR, yani '10/Ç' ile '10/İ' basılan evrakta listenin sonuna düşer ve
#: '10/I' ile '10/İ' iki uca ayrılırdı.
#:
#: Q/W/X Türk alfabesinde YOKTUR ama Türkçe metinde sıradandır: yabancı kişi
#: adları (Woolf, Wilde) ve yabancı kökenli kurum ve firma adları bu harflerle
#: başlar. Alfabe dışı
#: sayılsalardı 0 önceliğiyle listenin EN BAŞINA düşerlerdi; bu yüzden Latin
#: sırasındaki yerlerine konurlar (…P Q R… ve …V W X Y Z), ICU'nun Türkçe
#: sıralamasıyla aynı.
_TR_ALFABE = "0123456789ABCÇDEFGĞHIİJKLMNOÖPQRSŞTUÜVWXYZ"
_TR_SIRA = {harf: sira for sira, harf in enumerate(_TR_ALFABE)}


def tr_sort_key(value: object) -> tuple[tuple[int, int], ...]:
    """Türk alfabesine göre sıralama anahtarı ('C' < 'Ç' < 'D', 'I' < 'İ' < 'J').

    Yalnız şube harfi için değil, ÇOK KELİMELİ adlar için de kullanılabilir.
    Bu yüzden her karakter (öncelik, değer) ikilisine açılır: alfabe dışı
    karakterler (boşluk, '/', '-') 0 önceliğiyle harflerden ÖNCE gelir — ASCII
    sezgisiyle aynı ('A Blok' < 'AB Blok'), aksi hâlde ayraç
    sınırındaki adlar birbirine karışırdı. Karşılaştırma büyük harf üzerinden
    yapılır (`tr_upper`) ve aksanlar düz karşılıklarına katlanır
    (`fold_diacritics`): 'Kâmil' ile 'Kamil' yan yana sıralanır, alfabe dışına
    düşmez.
    """
    buyuk = fold_diacritics(tr_upper("" if value is None else str(value)))
    return tuple(
        (1, _TR_SIRA[ch]) if ch in _TR_SIRA else (0, ord(ch))  #
        for ch in buyuk
    )


#: Okul öncesi yaş gruplarının kabul edilen yaşları ("3 Yaş" … "6 Yaş"). Sınıf seviyesi
#: DEĞİLDİR: "5 Yaş-A" ilkokulun 5-A'sı olamaz (`normalize_preschool_group`).
PRESCHOOL_AGES: tuple[int, ...] = (3, 4, 5, 6)

#: Metinde okul öncesi izi ('YAŞ' ya da 'ANASINIF' ile başlayan sözcük; ASCII'ye katlanmış
#: metinde). İz varsa metin sınıf seviyesi olarak HİÇ çözülmez (`normalize_class_section`):
#: "5 yaş A" bir zamanlar 5. sınıfın "YAŞ" şubesi sayılıyordu.
_OKUL_ONCESI_IZI = re.compile(r"(?<![A-Z])(YAS|ANA[\s.\-]*SINIF)")
#: "Anasınıfı" sözcüğü ("ANASINIFI", "ANA SINIFI", "ANA-SINIF"; katlanmış metinde).
_ANASINIFI_RE = re.compile(r"(?<![A-Z])ANA[\s.\-]*SINIFI?(?![A-Z])")
#: Yaş grubu: hemen önünde yaşı olan 'YAŞ' sözcüğü ("5 YAS", "5YAS", "5-YAS", "5. YAS").
_YAS_GRUBU_RE = re.compile(r"(?<!\d)(\d{1,2})[\s.\-]*YAS(?![A-Z])")
#: Yalnız 'YAŞ' sözcüğü (önünde yaş olmasa da sayılır: "Yaş A" çözülmez).
_YAS_SOZCUGU_RE = re.compile(r"(?<![A-Z])YAS(?![A-Z])")
#: Okul öncesi metnindeki dolgu sözcükleri ("5 Yaş Grubu A Şubesi"; katlanmış).
_OKUL_ONCESI_DOLGU = frozenset({"GRUBU", "GRUP", "SINIF", "SINIFI", "SUBE", "SUBESI"})


def is_preschool_text(value: object) -> bool:
    """Metin okul öncesi grubu mu anlatıyor ('Anasınıfı', 'yaş' sözcüğü)? Çözülüp çözülmediği
    ayrıdır (`normalize_preschool_group`); iz taşıyan metin sınıf seviyesine hiç düşmez."""
    if value is None:
        return False
    return _OKUL_ONCESI_IZI.search(_ascii_upper(str(value))) is not None


def normalize_preschool_group(value: object) -> tuple[int | None, str] | None:
    """Okul öncesi grubu → (yaş, şube); yaş None ise grup "Anasınıfı"dır. Çözümsüz → None.

    KURAL (tek ve belgeli; sözlük "Veli"): grubun kimliği YAŞ GRUBU ile ŞUBENİN birlikteliğidir.
    - 'yaş' sözcüğünün hemen önünde 3-6 arası bir yaş varsa grup o yaştır: '5 yaş A', '5 Yaş-A',
      '5 YAŞ / A', '5yaş a' → (5, 'A'). 'Anasınıfı' sözcüğü de varsa dolgu sayılır
      ('Anasınıfı 5 Yaş A' → (5, 'A')): yaş daha belirleyicidir.
    - Yaş yoksa 'Anasınıfı' (ya da 'Ana Sınıfı', 'anasınıf') grubu: 'Anasınıfı A' → (None, 'A').
    - Şube en çok BİR harf dizisidir ve Türkçe büyük harfle yazılır (`tr_upper`); şubesiz grup
      geçerlidir: 'Anasınıfı' → (None, ''), '5 Yaş' → (5, '').
    - Çözülmez (None): yaş 3-6 dışında ('2 yaş A', '7 yaş A'), önünde yaş olmayan 'yaş' ('Yaş A'),
      yaşın dışında rakam ('Anasınıfı 1', '5 yaş 2'), birden çok şube dizisi, iki yaş sözcüğü.
    "Grubu", "Sınıfı", "Şubesi" dolgudur. Okul öncesi değilse de None (`is_preschool_text`).
    """
    if value is None:
        return None
    s = str(value).strip()
    folded = _ascii_upper(s)
    if not s or _OKUL_ONCESI_IZI.search(folded) is None:
        return None
    if len(_YAS_SOZCUGU_RE.findall(folded)) > 1 or len(_ANASINIFI_RE.findall(folded)) > 1:
        return None
    yas_m = _YAS_GRUBU_RE.search(folded)
    yas: int | None = None
    if yas_m is not None:
        yas = int(yas_m.group(1))
        if yas not in PRESCHOOL_AGES:
            return None
    elif _YAS_SOZCUGU_RE.search(folded) is not None:
        return None  # 'yaş' var ama önünde yaş yok
    elif _ANASINIFI_RE.search(folded) is None:
        return None  # yalnız iz ('5YAŞA', 'Anasınıflar'): tanınmaz
    # Anahtar sözcükler KATLANMIŞ metinde bulunur, şube HAM metinden alınır ('İ' 'I'ya çökmesin;
    # `tr_upper` gerekçesi). Katlama uzunluğu değiştirdiyse (savunma dalı) katlanmış metne düşülür.
    kaynak = s if len(folded) == len(s) else folded
    kalan = list(kaynak)
    for desen in (_YAS_GRUBU_RE, _ANASINIFI_RE):
        for m in desen.finditer(folded):
            kalan[m.start() : m.end()] = " " * (m.end() - m.start())
    parcalar = [
        p
        for p in re.findall(rf"\d+|[{_SECTION_CHARS}]+", "".join(kalan))
        if _ascii_upper(p) not in _OKUL_ONCESI_DOLGU
    ]
    if any(p.isdigit() for p in parcalar) or len(parcalar) > 1:
        return None
    return yas, tr_upper(parcalar[0]) if parcalar else ""


def normalize_class_section(
    value: object, *, valid_levels: Collection[int] = GRADE_LEVELS
) -> tuple[int, str] | None:
    """'10/A', '10-A', '10 A' → (10, 'A'); küme dışı seviye veya çözümsüz → None.

    `valid_levels` çağırandan gelir (varsayılan 1-12).
    0 (Hazırlık) kümede ise 'HAZIRLIK/A', 'HZ A' gibi metinler (0, 'A') çözülür.
    Okul öncesi izi taşıyan metin ('5 yaş A', 'Anasınıfı A') HİÇBİR ZAMAN seviyeye çözülmez
    (None): okul öncesi grubu `normalize_preschool_group` ile ayrı çözülür.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    levels = frozenset(int(v) for v in valid_levels)
    folded = _ascii_upper(s)
    if _OKUL_ONCESI_IZI.search(folded) is not None:
        return None
    prep = _PREP_RE.search(folded) if PREP_LEVEL in levels else None
    if prep is not None:
        # Anahtar kelime KATLANMIŞ metinde bulunur, şube harfi HAM metinden
        # alınır — 'Hazırlık/İ' şubesi 'I'ya çökmesin (tr_upper gerekçesi).
        if len(folded) == len(s):  # translate+upper 1:1 kaldıysa konumlar eşleşir
            kalan = s[: prep.start()] + " " + s[prep.end() :]
        else:  # savunma dalı: katlama uzunluğu değiştirdiyse ASCII'ye düş
            kalan = _PREP_RE.sub(" ", folded)
        harfler = re.sub(rf"[^{_SECTION_CHARS}]", " ", kalan).split()
        if not harfler:
            return None
        return PREP_LEVEL, tr_upper(harfler[-1])
    level_m = re.search(r"\d{1,2}", s)
    section_m2 = re.search(rf"[{_SECTION_CHARS}]+", s)
    if level_m is None or section_m2 is None:
        return None
    level = int(level_m.group())
    if level not in levels:
        return None
    section = tr_upper(section_m2.group())
    return level, section


def split_full_name(value: object) -> tuple[str, str]:
    """'EMRE CAN YILMAZ' → ('EMRE CAN', 'YILMAZ'); tek kelime → (kelime, '').

    Son kelime soyad kabul edilir. Title Case uygulanmaz — ham bırakılır
    (görüntü biçimi sistemin başka katmanında uygulanır; TR büyük harf tuzağı).
    """
    if value is None:
        return "", ""
    parts = str(value).split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]
