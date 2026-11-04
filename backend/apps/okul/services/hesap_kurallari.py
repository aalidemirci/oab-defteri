"""Hesap kuralları — parola politikası, tanıtıcı ve ad-soyad doğrulaması (F1b-1).

Bağımlılığı olmayan saf kurallar; hem `app_password` (ilk hesap, kilit açılışında
parola yenileme, parola değişimi, kurtarma) hem `hesaplar` (hesap açma, parola
sıfırlama) buradan doğrular. Bütün iletiler Türkçedir ve sözlüğe uyar ("parola",
"tanıtıcı", "program yöneticisi"; iç kod yok).

PAROLA POLİTİKASI (tasarım TK15, §15 M-4; plan F1b-1 "Parola ve hatalı deneme"):

* En az 8, en çok 128 karakter (BSG Yön. md. 9/2-a; üst sınır kilit ekranından
  kaynak tüketimini keser: her deneme 64 MiB Argon2id'dir).
* Küçük harf, büyük harf, rakam ve simge zorunludur (BSG Yön. md. 9/2-b; v1'de
  ayarı yoktur). Türkçe harfler harf sayılır (`ç`, `ğ`, `ı` küçük; `Ç`, `Ğ`, `İ`
  büyük). Simge harf, rakam ve boşluk dışındaki her karakterdir; parola
  cümlesindeki ara boşluk serbesttir ama simge sayılmaz.
  Rakam yalnız onluk rakamdır (`str.isdecimal`, Unicode `Nd`): `²`, `①` gibi üst
  simge ya da daireli rakamlar rakam sayılmaz (`isdigit` onları da sayardı). Ön yüzün
  ön denetimi (`oturum/parolaPolitikasi.ts`) her türü aynı Unicode özelliğiyle
  denetler; iki tarafın ortak vaka tablosu `test_hesaplar.py` ile
  `parolaPolitikasi.test.ts`'tedir.
* Parola KIRPILMAZ; başında ya da sonunda boşluk olan parola kabul edilmez (aile
  kurulumda kırpıp açılışta kırpmıyordu: sonu boşluklu parola kurulduktan sonra
  açılamazdı).
* Güç göstergesi ve organ hesabına önerilen 12 karakterlik parola cümlesi ön
  yüzün yerel kuralıdır (yeni bağımlılık yok); sunucu yalnız sert kuralları uygular.

TANITICI (tasarım §4.4.4): kilit ekranında görünen hesap adıdır, gerçek ad olmaz.
Varsayılanı rolden türer (`yonetici`, `yonetici-2`, `muhasip`, `dk-1`); program
yöneticisi değiştirebilir. Tanıtıcı ad-soyaddaki üç harften uzun bir sözcüğü ya da T.C.
kimlik numarasına benzeyen 11 ardışık rakamı içeriyorsa program UYARIR, engellemez
(`login_name_warning`; altın kural 3).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from apps.okul.excel_ogrenci import normalize_header
from apps.okul.models import AccountRole
from shared.text import tr_lower

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
#: Parolanın en uzun ömrü (gün); dolunca kilit açılışı yeni parolayı ister (TK15, BSG 9/2-ç).
PASSWORD_MAX_AGE_DAYS = 180

MAX_LOGIN_NAME_LENGTH = 32
MAX_DISPLAY_NAME_LENGTH = 150
#: Tanıtıcı uyarısında aranan ad sözcüğünün en kısa boyu (üç harften uzun).
_NAME_WORD_MIN = 4

_LOGIN_NAME_RE = re.compile(r"^[a-zçğıöşü][a-zçğıöşü0-9._-]{1,31}$")

# Kullanıcı iletileri (parola değildir; S105).
PASSWORD_EDGE_SPACE_MESSAGE = "Parolanın başında ya da sonunda boşluk olamaz."  # noqa: S105
PASSWORD_TOO_SHORT_MESSAGE = f"Parola en az {MIN_PASSWORD_LENGTH} karakter olmalıdır."  # noqa: S105
PASSWORD_TOO_LONG_MESSAGE = f"Parola en çok {MAX_PASSWORD_LENGTH} karakter olabilir."  # noqa: S105
LOGIN_NAME_EMPTY_MESSAGE = "Tanıtıcı boş olamaz."
LOGIN_NAME_INVALID_MESSAGE = (
    f"Tanıtıcı 2-{MAX_LOGIN_NAME_LENGTH} karakter olmalıdır; küçük harfle başlar, küçük "
    "harf, rakam, nokta, tire ya da alt çizgi içerir."
)
DISPLAY_NAME_EMPTY_MESSAGE = "Hesap sahibinin adı-soyadı boş olamaz."
DISPLAY_NAME_TOO_LONG_MESSAGE = (
    f"Hesap sahibinin adı-soyadı en çok {MAX_DISPLAY_NAME_LENGTH} karakter olabilir."
)
LOGIN_NAME_WARNING_MESSAGE = (
    "Tanıtıcı hesap sahibinin adını içeriyor. Tanıtıcı kilit ekranında herkese görünür; "
    "rolden türeyen bir tanıtıcı seçmeniz önerilir."
)
#: Tanıtıcıda 11 ardışık rakam (T.C. kimlik numarasına benzer; orkestratör maddesi F-5). Uyarıdır,
#: engel değildir; kalıbı ad-soyad uyarısınınkidir.
LOGIN_NAME_TCKN_WARNING_MESSAGE = (
    "Tanıtıcı T.C. kimlik numarasına benzeyen 11 haneli bir sayı içeriyor. Tanıtıcı kilit "
    "ekranında herkese görünür; rolden türeyen bir tanıtıcı seçmeniz önerilir."
)
#: T.C. kimlik numarasına benzeyen dizi: en az 11 ardışık onluk rakam (sağlama aranmaz; 12 ya da
#: daha uzun dizi de bir 11'liyi içerir). Tanıtıcı biçimi yalnız ASCII rakamı kabul eder.
_TCKN_BENZERI = re.compile(r"[0-9]{11}")

#: Rolden türeyen varsayılan tanıtıcının kökü. Birden çok hesabı olabilen rollerde
#: sıra eki gelir: ilk program yöneticisi `yonetici`, ikincisi `yonetici-2`;
#: Denetleme Kurulu `dk-1`, `dk-2`, `dk-3` (tasarım §4.4.4).
_DEFAULT_LOGIN_ROOTS: dict[str, str] = {
    AccountRole.YONETICI.value: "yonetici",
    AccountRole.BASKAN.value: "baskan",
    AccountRole.BASKAN_YARDIMCISI.value: "baskan-yardimcisi",
    AccountRole.MUHASIP.value: "muhasip",
    AccountRole.SEKRETER.value: "sekreter",
    AccountRole.DENETLEME_KURULU.value: "dk",
    AccountRole.MUDUR.value: "mudur",
}


class AccountRuleError(ValueError):
    """Kural ihlali; ileti kullanıcıya olduğu gibi gösterilir (view katmanı 400'e çevirir)."""


def validate_password(password: str) -> str:
    """Parolayı politikaya göre doğrular; parolayı DEĞİŞTİRMEDEN döndürür.

    Eksik karakter türleri tek iletide sayılır ("eksik: büyük harf, simge").
    Parola hiçbir iletide yankılanmaz.
    """
    if password != password.strip():
        raise AccountRuleError(PASSWORD_EDGE_SPACE_MESSAGE)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AccountRuleError(PASSWORD_TOO_SHORT_MESSAGE)
    if len(password) > MAX_PASSWORD_LENGTH:
        raise AccountRuleError(PASSWORD_TOO_LONG_MESSAGE)
    eksik: list[str] = []
    if not any(ch.islower() for ch in password):
        eksik.append("küçük harf")
    if not any(ch.isupper() for ch in password):
        eksik.append("büyük harf")
    if not any(ch.isdecimal() for ch in password):
        eksik.append("rakam")
    if not any(not ch.isalnum() and not ch.isspace() for ch in password):
        eksik.append("simge")
    if eksik:
        raise AccountRuleError(
            "Parola küçük harf, büyük harf, rakam ve simge içermelidir; eksik: "
            + ", ".join(eksik)
            + "."
        )
    return password


def validate_login_name(value: str) -> str:
    """Tanıtıcıyı doğrular; baştaki ve sondaki boşluğu atıp Türkçe küçük harfe çevirir."""
    tanitici = tr_lower(value.strip())
    if not tanitici:
        raise AccountRuleError(LOGIN_NAME_EMPTY_MESSAGE)
    if not _LOGIN_NAME_RE.fullmatch(tanitici):
        raise AccountRuleError(LOGIN_NAME_INVALID_MESSAGE)
    return tanitici


def validate_display_name(value: str) -> str:
    """Ad-soyadı doğrular (boş olamaz, en çok 150 karakter); kırpılmış değeri döndürür."""
    ad = " ".join(value.split())
    if not ad:
        raise AccountRuleError(DISPLAY_NAME_EMPTY_MESSAGE)
    if len(ad) > MAX_DISPLAY_NAME_LENGTH:
        raise AccountRuleError(DISPLAY_NAME_TOO_LONG_MESSAGE)
    return ad


def login_name_warning(login_name: str, display_name: str) -> str | None:
    """Tanıtıcının kişisel veri uyarısı; yoksa None. Uyarı engel değildir (altın kural 3).

    İki hâl, öncelik sırasıyla:

    1. Tanıtıcıda T.C. kimlik numarasına benzeyen 11 ardışık rakam (`LOGIN_NAME_TCKN_WARNING_MESSAGE`;
       orkestratör maddesi F-5; K9: kimlik numarası varsayılan kapalıdır, kilit ekranında hiç
       görünmemeli).
    2. Tanıtıcı ad-soyaddaki üç harften uzun bir sözcüğü içeriyor (`LOGIN_NAME_WARNING_MESSAGE`).
       Karşılaştırma Türkçe harfleri ASCII'ye katlayarak yapılır ("Şükrü" ≡ "sukru"): `sukru.k`
       de `ŞÜKRÜ` adını açık eder.

    Alan tek iletidir (hesap açma yanıtının `uyari`'sı, kurulumun `login_name_warning`'i, yönetim
    komutu): ikisi birden varsa birincisi verilir.
    """
    if _TCKN_BENZERI.search(login_name):
        return LOGIN_NAME_TCKN_WARNING_MESSAGE
    tanitici = normalize_header(login_name).replace(" ", "")
    for sozcuk in normalize_header(display_name).split():
        if len(sozcuk) >= _NAME_WORD_MIN and sozcuk in tanitici:
            return LOGIN_NAME_WARNING_MESSAGE
    return None


def default_login_name(role: str, taken: Iterable[str]) -> str:
    """Rolden türeyen, `taken` içinde olmayan ilk tanıtıcı (tasarım §4.4.4).

    Program yöneticisinde ilk ad eksizdir (`yonetici`, `yonetici-2`, …), Denetleme
    Kurulunda sıra baştan eklenir (`dk-1`, `dk-2`, …); tek hesaplı rollerde kök yeter
    (kök doluysa `-2` eklenir).
    """
    kok = _DEFAULT_LOGIN_ROOTS.get(role, role.replace("_", "-"))
    alinmis = set(taken)
    adaylar: Iterable[str]
    if role == AccountRole.DENETLEME_KURULU:
        adaylar = (f"{kok}-{sira}" for sira in range(1, 100))
    else:
        adaylar = (kok if sira == 1 else f"{kok}-{sira}" for sira in range(1, 100))
    for aday in adaylar:
        if aday not in alinmis:
            return aday
    raise AccountRuleError(LOGIN_NAME_INVALID_MESSAGE)  # pragma: no cover — 99 hesap olmaz
