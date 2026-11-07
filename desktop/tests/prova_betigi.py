"""Geri yükleme provasının ALT SÜREÇ betiği — gerçek ayarlar, gerçek veritabanı.

Masaüstü testleri asgari Django ayarlarıyla koşar (`conftest.py`); temiz makinede
geri yükleme provası ise gerçek şemayı, gerçek şifrelemeyi ve gerçek yedek
kapsayıcısını ister. Bu betik `python -m desktop.tests.prova_betigi <komut>` ile
AYRI süreçte koşar ve sonucunu stdout'un son satırına JSON olarak yazar. Toplanmaz
(`test_` ile başlamaz).

Komutlar:

* `hazirla --data-dir A --usb U` — göç, ilk program yöneticisi hesabı (tanıtıcı
  `yonetici`) + kurtarma anahtarı (doğrulanmış), uydurma kişi kayıtları, uydurma bir ek (plan
  F1b-3 "Ötekiler": F1b'de ek ekleyen ekran yoktur, ek betikle tohumlanır), **dış yedek**
  (kullanıcının kaydettiği şifreli tam yedek, `encrypted_backup`) U klasörüne.
* `dogrula --data-dir B (--parola P | --kurtarma K --yeni-parola P2) [--hesap T]` —
  kilidi hesabın parolasıyla ya da kurtarma anahtarıyla (program yöneticisinin
  parolası yenilenir) açar, özeti yazar.
* `gelecek-yedek --data-dir A --parola P --usb U` — veritabanına programın
  tanımadığı bir göç kaydı yazıp dış yedek alır, sonra kaydı siler (daha yeni bir
  sürümün yedeği; eski-sürüm kapısının geri yükleme yolu).
* `sihirbaz --data-dir B --parola P2` — yeni bilgisayarda kurucunun "programı
  çalıştır" kutusuyla açılan programda sihirbazın BAŞKA bir hesapla kurulması
  (göç + ilk hesap + doğrulanmış anahtar, kişi verisi yok). Geri yüklemeden önce
  yabancı bir güvenlik dosyası, yedek anahtarı ve boş veritabanı bırakır (aile
  iskeletinin düzeltmesi).
* `gun-kapisi --data-dir A --parola P` — gün değişimi kapısını (`od-gunluk`) gerçek
  işleriyle bir kez çalıştırır: yerleşik günlük yedek + backend'in kayıtlı bütün
  işleri. Ağ tuzağı altında koşar (açılışta dış istek yok testinin kapıyı da
  kapsaması).
* `ek-oku --data-dir B --parola P | --kurtarma K` — kilidi açar ve tohumlanan eki depodan çözer:
  tam yedeğin eki taşıdığının kanıtı (tasarım §10.6, F1b kapısı "ekler dâhil").
* `uzun-is-surerken --data-dir A` — gerçek programı (`desktop.main.run`) pencere yerine uzun iş
  tutan bir oturumla açar, "uzun is suruyor" yazıp bekler. Test süreci öldürür.

Aile iskeletinin katalog, üyelik, ödünç ve verilmiş kart defteri adımları
kütüphane uygulamasıyla birlikte söküldü (F1a-2); OAB'nin kayıtları geldikçe
özete eklenir.

Bütün veriler UYDURMADIR (CLAUDE.md §2, altın kural 5). Argon2 ucuz profille kurulur: parametreler
güvenlik dosyasına yazılır ve yedeğin başlığıyla taşınır; algoritma aynıdır.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from desktop.django_bootstrap import prepare_django, run_migrations
from desktop.paths import ENV_APP_HOME, resolve_app_paths, resolve_backend_dir

#: Uydurma hesap ve parola (yalnız bu provanın geçici veri dizini için).
TANITICI = "yonetici"
HESAP_ADI = "Deneme Yönetici"
PAROLA = "Prova-Yonetici-Parolasi-1"
YENI_PAROLA = "Prova-Yeni-Parola-2"
#: Sahte "gelecek sürüm" göçü (program tanımaz).
GELECEK_GOC = ("okul", "9999_gelecek_surum")
#: Uydurma ekin içeriği (PDF imzası türü geçirir) ve özgün adı.
EK_ICERIGI = b"%PDF-1.4\nuydurma prova eki\n%%EOF\n"
EK_ADI = "uydurma-ek.pdf"

_UCUZ_KDF = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}


def _django(veri_koku: str) -> Path:
    os.environ[ENV_APP_HOME] = veri_koku
    paths = resolve_app_paths()
    paths.ensure()
    prepare_django(resolve_backend_dir(), paths.data)
    return paths.data


def _oturum_yazari() -> Any:
    from apps.okul.oturum import OTURUM, Yazar

    hesap = OTURUM.hesap()
    if hesap is None:
        raise SystemExit("oturum açık değil")
    return Yazar.hesaptan(hesap)


@contextmanager
def _oturum_istegi() -> Iterator[None]:
    """Açık oturumdaki hesabın isteği gibi: yazar bağlamı istek başında kurulur.

    Programda bunu ara katman yapar (`lock_middleware`); betik servisi doğrudan çağırdığı
    için bağlamı kendisi kurar. Denetim izi yazarsız yazmayı reddeder (tasarım §4.6.2):
    kurtarma anahtarı damgası `KURTARMA`, dış yedek `YEDEK` satırı yazar.
    """
    from apps.okul.oturum import yazar_olarak

    with yazar_olarak(_oturum_yazari()):
        yield


def _ozet() -> dict[str, Any]:
    """Veri eşitliğinin ölçüsü: şifreli adlar ÇÖZÜLMÜŞ olarak, TR sırasıyla değil pk ile."""
    from apps.okul.models import Personnel, Student

    return {
        "ogrenciler": [
            [o.first_name, o.last_name, o.student_number, o.class_level, o.class_section]
            for o in Student.objects.order_by("pk")
        ],
        "personel": [[p.first_name, p.last_name] for p in Personnel.objects.order_by("pk")],
    }


def _ek_tohumla() -> str:
    """Uydurma ek: depoda dosya, tabloda satır; tam yedek bunları taşır.

    Geçici sahip ders yılıdır: F1b'de sahip kümesi boştur, ilk sahip F1c'de gelir (plan "Dosya
    deposu").
    """
    from datetime import date

    from apps.okul.models import AttachmentSensitivity, SchoolYear
    from apps.okul.services import dosya_deposu
    from apps.okul.services import school_year as school_year_service

    dosya_deposu.sahip_kaydet(SchoolYear)
    yil = school_year_service.create_school_year(
        name="2026-2027", start_date=date(2026, 9, 7), end_date=date(2027, 6, 25), activate=True
    )
    ek = dosya_deposu.yaz(
        EK_ICERIGI,
        original_name=EK_ADI,
        sensitivity=AttachmentSensitivity.NORMAL,
        owner=yil,
        yazar=_oturum_yazari(),
        kisi_listesi=False,
    )
    return str(ek.stored_name)


def hazirla(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)  # backend/ sys.path'e ÖNCE girer; `apps` ancak sonra import edilir
    from apps.okul.models import MemberKind, Personnel, Student
    from apps.okul.services import app_password, encrypted_backup
    from shared import crypto

    run_migrations()
    crypto.DEFAULT_KDF = crypto.KdfParams.from_dict(_UCUZ_KDF)
    kurtarma = app_password.enable(tanitici=TANITICI, display_name=HESAP_ADI, password=PAROLA)
    with _oturum_istegi():
        app_password.confirm_recovery_key(kurtarma)

    Student.objects.create(
        first_name="Deneme Çağla",
        last_name="Öğrenci Işıklı",
        student_number="700123",
        class_level=9,
        class_section="A",
    )
    Student.objects.create(
        first_name="Deneme İlkay",
        last_name="Şahinoğlu",
        student_number="700124",
        class_level=10,
        class_section="B",
    )
    Personnel.objects.create(
        first_name="Deneme Şükrü", last_name="Öğretmenoğlu", member_kind=MemberKind.TEACHER
    )

    # Dış yedek: kullanıcının Ayarlar → Güvenlik'ten USB belleğe kaydettiği şifreli yedek.
    usb = Path(args.usb)
    usb.mkdir(parents=True, exist_ok=True)
    with _oturum_istegi():
        ek = _ek_tohumla()
        yedek = usb / encrypted_backup.onerilen_ad()
        sonuc = encrypted_backup.sifreli_yedegi_kaydet(str(yedek))
    return {
        "tanitici": TANITICI,
        "parola": PAROLA,
        "kurtarma": kurtarma,
        "yedek": str(yedek),
        "ek": ek,
        "yedek_ozeti": sonuc.yanit(),
        "beklenen": _ozet(),
    }


def _ac(tanitici: str, parola: str) -> None:
    """Tanıtıcısı verilen hesabın parolasıyla kilidi açar (kilit ekranının karşılığı)."""
    from apps.okul.services import app_password

    hesap_id = app_password.account_id_for_login_name(tanitici)
    if hesap_id is None:
        raise SystemExit(f"hesap yok: {tanitici}")
    app_password.unlock(hesap_id=hesap_id, password=parola)


def dogrula(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)
    from apps.okul.services import app_password

    if args.parola:
        _ac(args.hesap, args.parola)
    else:
        hesap_id = app_password.account_id_for_login_name(args.hesap)
        app_password.unlock_with_recovery(
            recovery_key=args.kurtarma, hesap_id=hesap_id, new_password=args.yeni_parola
        )
    return {"ozet": _ozet(), "durum": app_password.status()}


def ek_oku(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)
    from apps.okul.models import Attachment
    from apps.okul.services import app_password, dosya_deposu

    if args.parola:
        _ac(args.hesap, args.parola)
    else:
        hesap_id = app_password.account_id_for_login_name(args.hesap)
        app_password.unlock_with_recovery(
            recovery_key=args.kurtarma, hesap_id=hesap_id, new_password=args.yeni_parola
        )
    with _oturum_istegi():
        ek = Attachment.objects.get(stored_name=args.ad)
        acik = dosya_deposu.oku(ek)
    return {"ayni": acik == EK_ICERIGI, "ad": ek.original_name}


def uzun_is_surerken(args: argparse.Namespace) -> dict[str, Any]:
    """Gerçek açılış ve sunucu; pencere yerine uzun iş tutan oturum. Süreci test öldürür."""
    from desktop import main as masaustu

    def oturum(*_a: Any, **_k: Any) -> None:
        from shared.bakim import UZUN_ISLER

        with UZUN_ISLER.is_():
            sys.stdout.write("uzun is suruyor\n")
            sys.stdout.flush()
            threading.Event().wait()

    masaustu.run_window_session = oturum
    return {"kod": masaustu.run(["--data-dir", args.data_dir])}


def gelecek_yedek(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder

    from apps.okul.services import encrypted_backup

    _ac(args.hesap, args.parola)
    usb = Path(args.usb)
    usb.mkdir(parents=True, exist_ok=True)
    yedek = usb / "gelecek-surum-yedegi.odbak"
    kayit = MigrationRecorder(connection)
    kayit.record_applied(*GELECEK_GOC)
    try:
        with _oturum_istegi():
            encrypted_backup.sifreli_yedegi_kaydet(str(yedek))
    finally:
        kayit.record_unapplied(*GELECEK_GOC)
    return {"yedek": str(yedek)}


def sihirbaz(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)
    from apps.okul.services import app_password
    from shared import crypto

    run_migrations()
    crypto.DEFAULT_KDF = crypto.KdfParams.from_dict(_UCUZ_KDF)
    kurtarma = app_password.enable(
        tanitici=TANITICI, display_name="Deneme Başka Yönetici", password=args.parola
    )
    with _oturum_istegi():
        app_password.confirm_recovery_key(kurtarma)
    return {"durum": app_password.status()}


def gun_kapisi(args: argparse.Namespace) -> dict[str, Any]:
    _django(args.data_dir)
    from desktop.gunluk import GunDegisimiKapisi
    from desktop.main import gunluk_yedek_isi

    _ac(args.hesap, args.parola)
    paths = resolve_app_paths()
    kapi = GunDegisimiKapisi(damga_yolu=paths.data / "kapi-sinamasi.json")
    kapi.kaydet("gunluk-yedek", gunluk_yedek_isi(paths))
    backend_is_sayisi = kapi.backend_islerini_ekle()
    biten = kapi.tik()
    return {"isler": list(kapi.is_adlari), "backend_is_sayisi": backend_is_sayisi, "biten": biten}


def main(argv: list[str] | None = None) -> int:
    ayristirici = argparse.ArgumentParser(prog="prova_betigi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)
    h = alt.add_parser("hazirla")
    h.add_argument("--data-dir", required=True)
    h.add_argument("--usb", required=True)
    d = alt.add_parser("dogrula")
    d.add_argument("--data-dir", required=True)
    d.add_argument("--parola", default="")
    d.add_argument("--kurtarma", default="")
    d.add_argument("--yeni-parola", default=YENI_PAROLA)
    d.add_argument("--hesap", default=TANITICI)
    g = alt.add_parser("gelecek-yedek")
    g.add_argument("--data-dir", required=True)
    g.add_argument("--parola", required=True)
    g.add_argument("--usb", required=True)
    g.add_argument("--hesap", default=TANITICI)
    s = alt.add_parser("sihirbaz")
    s.add_argument("--data-dir", required=True)
    s.add_argument("--parola", required=True)
    c = alt.add_parser("gun-kapisi")
    c.add_argument("--data-dir", required=True)
    c.add_argument("--parola", required=True)
    c.add_argument("--hesap", default=TANITICI)
    e = alt.add_parser("ek-oku")
    e.add_argument("--data-dir", required=True)
    e.add_argument("--ad", required=True)
    e.add_argument("--parola", default="")
    e.add_argument("--kurtarma", default="")
    e.add_argument("--yeni-parola", default=YENI_PAROLA)
    e.add_argument("--hesap", default=TANITICI)
    u = alt.add_parser("uzun-is-surerken")
    u.add_argument("--data-dir", required=True)
    args = ayristirici.parse_args(argv)
    islem = {
        "hazirla": hazirla,
        "dogrula": dogrula,
        "gelecek-yedek": gelecek_yedek,
        "sihirbaz": sihirbaz,
        "gun-kapisi": gun_kapisi,
        "ek-oku": ek_oku,
        "uzun-is-surerken": uzun_is_surerken,
    }[args.komut]
    sonuc = islem(args)
    sys.stdout.write(json.dumps(sonuc, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
