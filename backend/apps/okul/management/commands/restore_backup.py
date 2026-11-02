"""Yedekten geri yükleme — konsol aracı (destek/geliştirme).

Paketlenmiş kurulumda `manage.py` yoktur; son kullanıcı aynı çekirdeği
`oab-defteri --geri-yukle` ile çalıştırır (desktop/restore.py). Bu komut
geliştirme ortamı ve uzaktan destek senaryosu içindir:

    python manage.py restore_backup <yedek.odbak>              # hesap ve parola sorar
    python manage.py restore_backup <yedek> --hesap yonetici   # o hesabın parolası sorulur
    python manage.py restore_backup <yedek> --recovery-key ...
    python manage.py restore_backup <yedek> --yes              # onay sorusu atlanır

Komut veritabanına ORM üzerinden HİÇ dokunmaz — hedef dosya bozuk olabilir,
geri yüklemenin varlık sebebi de budur. Parola yolu güncel `guvenlik.json`'daki
hesabın sarmalıyla işler (`--hesap` tanıtıcıdır); başka bilgisayarda alınmış yedek
yalnız kurtarma anahtarıyla açılır (tasarım TK10). Parola yolunda geri yüklemeyi yalnız
program yöneticisi yapar: rol denetimi `desktop/restore.py` ile aynıdır, çünkü ikisi de aynı
çekirdekten geçer (`backup_restore`, `geri_yukleme_yetkisi`; ORM'siz). Ret
`GeriYuklemeYetkisiz` bir `BackupRestoreError`'dır, `CommandError` olarak döner; hiçbir dosya
değişmez. Kurtarma anahtarı yolunda rol denetimi yoktur. Var olan bir hesabın parolasını alan
TEK yönetim komutu budur (`app_password` komutunun başlığı). Sırlar varsayılan olarak gizli
istemle (getpass)
alınır; `--password/--recovery-key` yalnız otomasyon/test içindir ve komut
geçmişine düşme riskini taşır (bkz. app_password komutu).

UYARI: komut çalışırken program AÇIK OLMAMALIDIR — masaüstü kabuğu tek-instance
kilidini kullanır, `manage.py` o kilidi almaz.
"""

from __future__ import annotations

from getpass import getpass
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.okul.services import backup_restore


class Command(BaseCommand):
    help = "Bir şifreli .odbak yedeğini veritabanının yerine geri yükler."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("backup", help="Geri yüklenecek yedek dosyası (.odbak).")
        parser.add_argument(
            "--hesap", default=None, help="Program yöneticisi hesabının tanıtıcısı (parola yolu)."
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Program yöneticisi hesabının parolası (otomasyon; risklidir).",
        )
        parser.add_argument("--recovery-key", default=None, help="Kurtarma anahtarı (otomasyon).")
        parser.add_argument("--yes", action="store_true", help="Onay sorusunu atlar.")

    def handle(self, *args: Any, **options: Any) -> None:
        yedek = Path(str(options["backup"])).expanduser()
        try:
            icerik = yedek.read_bytes()
        except OSError as exc:
            raise CommandError(f"Yedek dosyası okunamadı: {yedek}") from exc
        try:
            backup_restore.inspect_backup(icerik)
        except backup_restore.BackupRestoreError as exc:
            raise CommandError(str(exc)) from exc

        hedef = self._database_path()
        self.stdout.write(f"Yedek : {yedek}")
        self.stdout.write(f"Hedef : {hedef}")
        self.stdout.write(
            f"Mevcut veritabanı silinmez; '{backup_restore.OLD_DB_PREFIX}-*' adıyla kenara alınır."
        )
        if not options["yes"]:
            yanit = input("Devam edilsin mi? [e/H] ").strip().lower()
            if yanit not in {"e", "evet"}:
                self.stdout.write("Geri yükleme iptal edildi.")
                return

        hesap = options.get("hesap")
        parola = options.get("password")
        anahtar = options.get("recovery_key")
        if not parola and not anahtar:
            if not hesap:
                hesap = input(
                    "Program yöneticisi hesabının tanıtıcısı "
                    "(kurtarma anahtarıyla açmak için boş bırakın): "
                )
            if hesap:
                parola = getpass("Hesabın parolası: ")
            else:
                anahtar = input("Kurtarma anahtarı: ")

        try:
            sonuc = backup_restore.restore_database(
                yedek, hedef, hesap=hesap, password=parola, recovery_key=anahtar
            )
        except backup_restore.BackupRestoreError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Geri yükleme tamamlandı."))
        if sonuc.old_db_path is not None:
            self.stdout.write(f"Önceki veritabanı: {sonuc.old_db_path}")
        if sonuc.state_written:
            self.stdout.write(
                "guvenlik.json yedekteki kurtarma başlığından yeniden yazıldı; programı "
                "kurtarma anahtarıyla açıp program yöneticisinin parolasını belirleyin."
            )
        self.stdout.write(
            "Program açıldığında gerekli şema güncellemeleri kendiliğinden uygulanır."
        )

    def _database_path(self) -> Path:
        """Hedef dosyanın yolu — bağlantı AÇILMAZ (dosya bozuk olabilir)."""
        ad = str(settings.DATABASES["default"].get("NAME") or "")
        if not ad or ad == ":memory:" or "mode=memory" in ad:
            raise CommandError("Veritabanı dosya tabanlı değil; geri yükleme uygulanamaz.")
        return Path(ad)
