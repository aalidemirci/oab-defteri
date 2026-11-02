"""Hesaplar — konsol kurtarma aracı (tasarım §4.3, §4.4.4; F1b-1).

Arayüz açılamadığında (kayıp güvenlik dosyası şüphesi, kilitli veriyle destek
çağrısı) destek elinin yoludur; komut yalnız veri klasörüne erişebilen kişi
tarafından çalıştırılabilir. Rol denetimi (konsol işlerini yalnız program
yöneticisi yapar) 2. adımdadır (tasarım §4.4.2).

Kullanım (paketlenmiş kurulumda `manage.py` yoktur; bu araç geliştirme ve
destek senaryosu içindir):

    python manage.py app_password status
    python manage.py app_password enable --tanitici yonetici --ad "Ad Soyad"
                                                   # ilk program yöneticisi; anahtar basar
    python manage.py app_password recover --hesap yonetici
                                                   # kurtarma anahtarıyla yeni parola

Hesapsız kipe dönme işlemi yoktur (tasarım §5.3). Aileden kalan `resume`
(düz metin şifreleme geçişini tamamlama) kalktı: ilk hesap kişi tabloları boşken
açılır, şifrelenecek düz satır yoktur (tasarım §13 D29; plan F1b-1).

Parolalar VARSAYILAN OLARAK gizli istemle (getpass) alınır — komut satırı
geçmişine ve süreç listesine düşmez. `--password/--new-password/--recovery-key`
seçenekleri yalnız otomasyon/test içindir ve bu riski taşır.

DENETİM İZİ (tasarım §4.6.2; plan F1b-1 alt commit c): konsolda istek yoktur, yazar
bağlamını ara katman kurmaz. Komut yazarını AÇIKÇA verir: `SISTEM` (`sistem_olarak`).
`enable` ve `recover`'ın kendi satırları plan gereği o hesabındır (ilk hesap ve kurtarmayla
açılış yazarı servis içinde kendisi kurar); bağlamın işi, ileride bu komuta eklenecek bir
yazımın yazarsız kalıp reddedilmesi yerine sistem işi olarak izlenmesidir.
"""

from __future__ import annotations

from getpass import getpass
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.okul.oturum import sistem_olarak
from apps.okul.services import app_password, hesap_kurallari

ACTIONS = ("status", "enable", "recover")


class Command(BaseCommand):
    help = "İlk program yöneticisi hesabını kurar, durumu gösterir ya da kurtarma anahtarıyla açar."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("action", choices=ACTIONS, help="Yapılacak işlem.")
        parser.add_argument(
            "--tanitici", default="yonetici", help="enable: ilk hesabın tanıtıcısı."
        )
        parser.add_argument("--ad", default=None, help="enable: hesap sahibinin adı-soyadı.")
        parser.add_argument(
            "--hesap", default=None, help="recover: program yöneticisi hesabının tanıtıcısı."
        )
        parser.add_argument("--password", default=None, help="Parola (otomasyon; risklidir).")
        parser.add_argument("--new-password", default=None, help="Yeni parola (otomasyon).")
        parser.add_argument("--recovery-key", default=None, help="Kurtarma anahtarı (otomasyon).")

    def handle(self, *args: Any, **options: Any) -> None:
        action = str(options["action"])
        try:
            with sistem_olarak():
                getattr(self, f"_{action}")(options)
        except ValueError as exc:  # AppPasswordError ve kural ihlalleri
            raise CommandError(str(exc)) from exc

    # -- işlemler ----------------------------------------------------------
    def _status(self, options: dict[str, Any]) -> None:
        durum = app_password.status()
        self.stdout.write(f"Hesap kurulu     : {'evet' if durum['password_set'] else 'hayır'}")
        self.stdout.write(f"Kilitli          : {'evet' if durum['locked'] else 'hayır'}")
        if durum["security_file_missing"]:
            self.stdout.write(
                self.style.ERROR(
                    "Güvenlik dosyası: KAYIP — " + app_password.SECURITY_FILE_MISSING_MESSAGE
                )
            )
        self.stdout.write(f"Hesap sayısı     : {durum['account_count']}")
        if durum["recovery_key_no"] is not None:
            self.stdout.write(
                f"Kurtarma anahtarı: {durum['recovery_key_no']} numaralı, "
                f"{durum['recovery_key_date'] or 'tarihsiz'}"
            )
        self.stdout.write("Yarım geçiş      : " + (durum["transition"] or "yok"))
        self.stdout.write("Korunan alanlar  : " + ", ".join(durum["protected_fields"]))
        self.stdout.write(f"Güvenlik dosyası : {app_password.state_path()}")

    def _enable(self, options: dict[str, Any]) -> None:
        tanitici = str(options.get("tanitici") or "yonetici")
        ad = options.get("ad") or input("Hesap sahibinin adı-soyadı: ")
        parola = self._ask(
            options, "password", "İlk program yöneticisinin parolası: ", confirm=True
        )
        kurtarma = app_password.enable(tanitici=tanitici, display_name=str(ad), password=parola)
        self.stdout.write(self.style.SUCCESS("Program yöneticisi hesabı kuruldu."))
        uyari = hesap_kurallari.login_name_warning(tanitici, str(ad))
        if uyari:
            self.stdout.write(self.style.WARNING(uyari))
        self.stdout.write("")
        self.stdout.write("KURTARMA ANAHTARI (bir daha gösterilmez — yazdırın ve saklayın):")
        self.stdout.write(self.style.WARNING(f"    {kurtarma}"))

    def _recover(self, options: dict[str, Any]) -> None:
        tanitici = options.get("hesap") or input("Program yöneticisi hesabının tanıtıcısı: ")
        hesap_id = app_password.account_id_for_login_name(str(tanitici))
        if hesap_id is None:
            raise CommandError("Bu tanıtıcıyla açık bir hesap bulunamadı.")
        anahtar = options.get("recovery_key") or input("Kurtarma anahtarı: ")
        yeni = self._ask(options, "new_password", "Yeni parola: ", confirm=True)
        app_password.unlock_with_recovery(
            recovery_key=str(anahtar), hesap_id=hesap_id, new_password=yeni
        )
        self.stdout.write(self.style.SUCCESS("Kurtarma başarılı; yeni parola geçerli."))

    # -- yardımcı ----------------------------------------------------------
    def _ask(self, options: dict[str, Any], key: str, prompt: str, *, confirm: bool = False) -> str:
        verilen = options.get(key)
        if verilen:
            return str(verilen)
        deger = getpass(prompt)
        if confirm and deger != getpass("Parolayı yeniden girin: "):
            raise CommandError("Parolalar eşleşmedi.")
        return deger
