# OAB Defteri — Aile İskeleti Envanteri (F0-7)

*31.10.2026 · Durum: **taslak**, F0-8 genel tasarımının girdisi. Dayanak: [F0-F1 planı](../plan/2026-10-31-f0-f1-plani.md)
§1.2 F0-7, §1.3, §1.4, §2.1-2.2 · [ön değerlendirme](2026-10-31-on-degerlendirme.md) §7.1.*

---

## 1. Giriş

| | |
|---|---|
| Kaynak | Kütüphane Defteri `origin/main`, commit **9a3829d** (çıkarılmış ağaç; `.git` yok). Kardeş depoya dokunulmadı |
| Kıyas | Kelebek Sınav `main` (07a9eb4) — yalnız `desktop/window.py`, `desktop/main.py`, paketleme gereksinimleri okundu |
| Okunanlar | Kaynağın `CLAUDE.md`'si (tamamı), genel tasarım §1-§4.5, §6.1-§6.4, §10-§13, §14.1 tablo ve F1 ekleri başı, `docs/teknik-borc.md` (tamamı), iskelet dizinlerinin kodu (seçerek) |
| Yöntem | Dosya ağacı ve grep; kimlik kalıntısı sayımları host'ta **salt okuma** betiğiyle, `test_kimlik_kalintisi.py`'nin `katla()` kuralıyla yapıldı. **Hiçbir test koşulmadı** (aile kuralı: test yalnız Docker'da) |
| Büyüklük | Kaynak ağaç 1.044 dosya (`node_modules` hariç). F1a kopya kümesi (ALMA'lar düşülünce) **≈425 dosya**; bunların **185'i** en az bir eski kimlik izi taşıyor (§4.2) |

**Sınıflar.**

| Sınıf | Anlamı |
|---|---|
| **AYNEN** | Davranış ve imza değişmez; yalnız kimlik sabitleri (§4) çevrilir |
| **UYARLA** | Değişir; satırda gerekçe ve zamanı yazılı |
| **ALMA** | Sökülür; bağları §3'te |

**Zaman sütunu** (plan §2.1): **F1a-1** ham kopya + kimlik çevirisi · **F1a-2** arındırma (ALMA, T6, "ağ servisi
sunmaz", bağımlılık zinciri) · **F1a-3** evrak spike'ı (T2) · **F1b** güvenlik çekirdeği, roller (T1), personel (T5) ·
**sonra** ilgili faz.

**Yazım.** Tablolarda düz cümle **gözlemdir** (dosyada olan). **Ö:** ile başlayan cümle **öneridir**. Emin
olunamayan yerde "doğrulanmadı" yazar. Yollar kaynak köke görecelidir. Kimlik değerleri (GUID, e-posta, anahtar)
alıntılanmaz.

---

## 2. Dizin dizin kopya haritası

### 2.1 Depo kökü

| Yol | Sınıf | Zaman | Not |
|---|---|---|---|
| `VERSION` | UYARLA | F1a-1 | İçerik `2026.10.0-beta.1`. Ö: kopyalanmaz, OAB'nin ilk sürüm numarası yazılır |
| `SECURITY.md` | UYARLA | F1a-1 | `.kdbak`, "ağ kataloğu yüzeyi", okul/kart numarası metinleri değişir. İletişim satırı kalır |
| `THIRD_PARTY_LICENSES/` (102 dosya, 66 bileşen) | UYARLA | F1a-2 | **Üretilmiş dizindir, elle düzenlenmez** (`packaging/lisanslar/uret.sh`, Docker + ağ ister). segno, pystray, six çıkar; python-docx, lxml girer. Ö: kopyalamak yerine F1a-2 sonunda `uret.sh` ile yeniden üretilir |
| `docker-compose.yml` | UYARLA | F1a-1 | **Plan listesinde yok, gerekli** (bütün test/lint düzeni buna dayanır). Proje adı ve "yerel ağa katalog" yorumu değişir |
| `.gitignore` | UYARLA (birleştirme) | F1a-1 | OAB deposunda zaten var (`*.csv`, `*.odbak`, xls/xlsx dahil). Kütüphane'nin dosyasından eksik kalanlar: **sentetik e-Okul personel örneğinin adıyla istisnası** (`!backend/apps/okul/tests/veri/eokul_personel_listesi.xls` — yoksa `*.xls` kuralı test verisini depoya sokmaz, CI'da test düşer), kapı geçici dosyası (`.od-depo-listesi.tmp`), `.claude/settings.local.json`, evrak denemesi çıktısı dizini. Ö: `*.docx`, `*.ods` (şablon istisnası adıyla) |
| `.gitattributes` | — | — | OAB deposunda zaten var, Kütüphane'ninkiyle bayt bayt aynı |
| `.github/ISSUE_TEMPLATE/` (2) | UYARLA | F1a-1 | Listede yok. Depo adresi değişir |
| `LICENSE` | — | — | OAB deposunda zaten var (PolyForm Noncommercial 1.0.0, K7). Inno `LicenseFile` ve `.deb` DEP-5 bunu okur |
| `README.md`, `CLAUDE.md`, `AGENTS.md` | ALMA | — | OAB'nin kendileri var. Ö: OAB README'si köken anlatırsa kimlik taramasına takılır (§4.3) |
| `docs/` | ALMA | — | Kütüphane'nin belgeleri. İki istisna §2.10'da (iskelet testlerinin okuduğu belgeler) |

### 2.2 `.github/workflows/`

| Dosya | Sınıf | Not |
|---|---|---|
| `kapilar.yml` | UYARLA | `gates.sh`'i olduğu gibi koşar. Gecelik `KD_YAVAS=1` girdisi ölçüm ve ağ provası içindir; ikisi de ALMA'lık bölümlerde (§8.1, §10.1-5) |
| `paketleme.yml` | UYARLA | Kurulum provası matrisi `["11","12"]` → `13` eklenir (§8.5); adlar; R2 adımı |
| `r2-yukle.yml` | UYARLA | Önek `packaging/r2-yukle.sh`'den gelir. Yayın işi, kullanıcı onaylıdır |

### 2.3 `docker/`

| Dosya | Sınıf | Not |
|---|---|---|
| `backend.Dockerfile` | AYNEN + kimlik | Dizinde yalnız bu dosya var; ön yüz kabı `docker-compose.yml`'de `node:20-slim` imajıdır. Son satırda `runserver 0.0.0.0:8000` geliştirme komutu duruyor (compose `sleep infinity` ile ezer). Ö: satır silinir, "yalnız 127.0.0.1" değişmezinin taramasına aday olmasın. T2 seçeneği (b)/(c) seçilirse imaja LibreOffice girer |

### 2.4 `scripts/`

| Dosya | Sınıf | Not |
|---|---|---|
| `gates.sh` | UYARLA | Adımları §8.1'de. `KD_YAVAS` dalı (ölçüm + `ag_katalogu_provasi.sh`) sökülür; `.kd-depo-listesi.tmp` adı değişir |
| `ag_katalogu_provasi.py` / `.sh` | ALMA | F5 ağ kanıtı (iki kap, 50 istemci) |
| `deneme_verisi.py` (1.682 satır) | ALMA | Kütüphane kataloğu ve e-Okul öğrenci listesi üretir. Ö: F7'de OAB'nin uydurma veri üreticisi aynı kalıpla (stdlib + openpyxl, çıktı depoya girmez) yazılır |
| `ekran_goruntuleri/` (5) | ALMA (şimdilik) | Site görüntüleri; katalog denetçisini içe aktarır. Site adımında kalıp olarak döner |

### 2.5 `desktop/` (27 modül + 34 test dosyası)

| Modül | Sınıf | Zaman | Not |
|---|---|---|---|
| `__init__.py` | UYARLA | F1a-1 | Belge dizesi |
| `ag.py` | ALMA | F1a-2 | IP adayları; yalnız `katalog_kontrol` kullanır |
| `backup.py` | UYARLA | F1a-1/sonra | `.kdbak`, günlük yedek + 14 gün rotasyonu, göç öncesi yedek, `pre-anonim` (saklama tetiği — OAB'de saklama fazına kadar boşta) |
| `backup_crypto.py` | AYNEN + kimlik; F1b UYARLA | F1a-1, F1b | MAGIC ve iki HKDF dizgesi (§4.1). `is_usable_security_state` T1 şemasına göre değişir (§6.3) |
| `clean_shutdown.py` | UYARLA | F1a-1 | Temiz kapanış işareti (T15). İleti "ödünç ve iade işlemlerini kontrol edin" der; `KD_ONCEKI_OTURUM` → `OD_ONCEKI_OTURUM` |
| `dagitim.py` | ALMA | F1a-2 | Yalnız Pardus taşınabilir arşivde katalogu kapatmak için (KB-2). `--dagitim-duman` (çıkış 11) onunla gider |
| `dialogs.py`, `integrity.py`, `version.py` | AYNEN | F1a-1 | |
| `django_bootstrap.py` | AYNEN + kimlik | F1a-1 | `wal_checkpoint` (TB14), bilinmeyen göç denetimi |
| `errors.py` | UYARLA | F1a-2 | Çıkış kodları 0-11; 11 (`--dagitim-duman`) boşa düşer. Ö: kod numarası yeniden kullanılmaz, "ayrılmış" yazılır |
| `gunluk.py` | UYARLA | F1a-2 | Gün değişimi kapısı kalır (program gece açık bırakılabilir). Uyku engelleme ve IP işi sökülür |
| `guvenlik_duvari.py` (865 satır) | ALMA | F1a-2 | §3.4 |
| `instance_channel.py` | AYNEN + kimlik | F1a-1 | Adlı olaylar `.Goster` / `.Kapat`; kurucu kapatma olayı ve ikinci açılışta pencereyi öne getirme T6'da da gerekir |
| `katalog_kontrol.py`, `katalog_server.py` | ALMA | F1a-2 | §3.2 |
| `lock.py` | UYARLA | F1a-2 | Mutex adları; "Program tepside çalışıyor olabilir…" iletisi |
| `logging_setup.py`, `paths.py`, `session_guard.py`, `win32_objects.py` | AYNEN + kimlik | F1a-1 | |
| `main.py` | UYARLA | F1a-2 | Tepsi, katalog, `--tepside`, gün kapısının uyku bağı, `--autotest`'te katalog kaldırma (§9.3) |
| `powershell.py` | ALMA | F1a-2 | Yalnız `ag.py` ve `guvenlik_duvari.py` kullanır |
| `restore.py` | UYARLA | F1a-2 | `RUNNING_MESSAGE` tepsiyi anlatır |
| `server.py` | UYARLA | F1a-2 | Kod AYNEN; belge dizesindeki "Ağ Kataloğu ayrı bir dinleyicidir" paragrafı geri çevrilir |
| `tray.py` (714 satır) | ALMA + **parça taşıma** | F1a-2 | Linux Qt kurulumu bu dosyadadır; tepsiyle birlikte silinirse Pardus penceresi bozulur (§3.1, §10.3) |
| `window.py` | UYARLA | F1a-2 | T6 (§10.3) |

**Testler (34).** ALMA: `test_ag`, `test_dagitim`, `test_guvenlik_duvari`, `test_katalog_kontrol`, `test_katalog_yuk`,
`test_sozluk_metinleri` (yalnız katalog modüllerinin metnini tarar), `test_tray` (Qt kurulum testleri taşınır).
**Parça taşınacak:** `test_katalog_server.py` — §5.10-1 değişmez testleri (yönetim sunucusu yalnız `127.0.0.1`,
`main.py` host vermez, `0.0.0.0` taraması) bu dosyadadır, `test_server.py`'ye geçer; `test_main_f5.py` — WAL checkpoint
(TB14) ve kapanış sırası testleri taşınır. UYARLA: `test_main`, `test_window_controller`, `test_window_f5`,
`test_restore`, `test_gunluk`, `test_acilista_dis_istek`, `test_geri_yukleme_provasi` + `prova_betigi.py` (verilmiş kart
defteri bağı), `alt_surec.py` (`KD_KATALOG_PORT`), `conftest.py`. Gerisi AYNEN.

### 2.6 `packaging/`

| Yol | Sınıf | Not |
|---|---|---|
| `README.md` | UYARLA | Zincirlerin anlatımı; pystray, segno ve katalog paragrafları çıkar |
| `depo_sizintisi.py` / `veri_sizintisi.py` | UYARLA | §8.3 |
| `requirements-paketleme.txt` | UYARLA | `pystray`, `six` çıkar; `pywebview`, `pythonnet` (win32), `QtPy` + `PySide6==6.8.3` (linux), `pyinstaller` kalır |
| `r2-yukle.sh` | UYARLA | `R2_ONEK` |
| `fontlar/` (DejaVu + lisans) | AYNEN | `--pdf-duman` bu fontu arar |
| `ikonlar/` (12) | UYARLA | Logo kütüphaneye özgü ("Raf ve etiket", TB4 kapanışı). `logo_uret.py` / `ikon_uret.py` üreteç kalıbı (elle çizilmiş 16/24/32, `.ico` yedi kare) korunur, çizim yeni. Dosya adları kimlik taramasına takılır (§4.3) |
| `linux/apt_dene.sh`, `docker-build.sh`, `postinst`, `prerm` | AYNEN + kimlik | `prerm` açık programı kapatmaz (TB40) |
| `linux/build.sh` | UYARLA | ufw/firewalld kurulumu, katalog öz sınaması, adlar |
| `linux/debian-control.tmpl` | UYARLA | `Description` "isteğe bağlı ağ kataloğu" paragrafı taşır (§3.9) |
| `linux/kutuphane-defteri.desktop` | UYARLA | Ad, `Keywords`, `StartupWMClass` |
| `linux/kur.sh`, `kaldir.sh`, `BENIOKU.txt` | UYARLA | Taşınabilir arşiv; BENIOKU katalog anlatır |
| `linux/kap-ici-test.sh`, `test-kurulum.sh` | UYARLA | `--dagitim-duman` adımı çıkar; Debian 13 (§8.5) |
| `linux/ufw-*`, `linux/firewalld-*.xml` | ALMA | §3.4 |
| `lisanslar/lisanslar.py` | UYARLA | pystray kaynağı, segno, Qt GPL ayıklaması (kalır), yazılı teklif metni üreticisi, `KD_WITH_QT`/`KD_DLL_DIR` |
| `lisanslar/on_yuz_paketleri.mjs`, `uret.sh` | AYNEN + kimlik | |
| `pyinstaller/fonts.conf.tmpl`, `fonts.paket.conf` | AYNEN | |
| `pyinstaller/giris.py` | UYARLA | `RUNTIME_MODULES` (segno çıkar, docx girer), `DESKTOP_RUNTIME_MODULES` (pystray, six çıkar; `clr` kalır), `--dagitim-duman` çıkar; Ö: `--evrak-duman` eklenir (§7.3) |
| `pyinstaller/kutuphane_defteri.spec` | UYARLA → `oab_defteri.spec` | `Tree(backend/katalog)`, `collect_submodules("segno"/"pystray")`, `module_collection_mode={"pystray":"py"}` çıkar; Qt GPL ayıklaması, UCRT süzgeci, fontconfig yerleşimi kalır |
| `pyinstaller/rthook_kd.py` | UYARLA → `rthook_od.py` | UAC yardımcı kipi dalı (`--guvenlik-duvari-kurali`) sökülür |
| `windows/build.ps1`, `dll_kapanisi.py`, `paket_kapanisi.py` | AYNEN + kimlik | |
| `windows/kutuphane-defteri.iss` | UYARLA | §10.3 ve §3.4; Ö: `PrivilegesRequired` yeniden düşünülür (§11-1) |
| `windows/gorev-kur.ps1` | ALMA | Otomatik başlatma görevi (tepsi kararı U3'ün parçası) |
| `windows/NOTLAR.md` | UYARLA | W13-W20 (tepsi, oturum iptali, güvenlik duvarı, otomatik başlatma, UAC, uyku) düşer ya da değişir |
| `windows/dll/` | — | Boş; `.gitignore`'da |
| `tests/test_ag_katalogu_paketi.py` | ALMA | |
| `tests/test_kimlik_kalintisi.py`, `test_lisans_kapisi.py`, `test_spec_kapsami.py`, `test_rthook.py`, `test_ikonlar.py`, `test_depo_sizintisi.py`, `test_veri_sizintisi.py`, `test_surum_yolu.py` | UYARLA | §4.3, §5 |
| `tests/test_apt_dene.py`, `test_betik_kodlamasi.py`, `test_paket_kapanisi.py`, `test_paketleme_tetigi.py` | AYNEN + kimlik | |

### 2.7 `backend/` kök, `config/`, `shared/`

| Yol | Sınıf | Not |
|---|---|---|
| `conftest.py`, `manage.py`, `requirements-dev.txt` | AYNEN + kimlik | **Listede yok, gerekli** |
| `pyproject.toml` | UYARLA | **Listede yok, gerekli.** `testpaths` ve `--cov=katalog` katalog paketini sayar; ruff kuralları, mypy strict, kapsam eşiği 75 kalır |
| `requirements.txt` | UYARLA | §5.1 |
| `apps/__init__.py` | AYNEN | |
| `config/settings.py` | UYARLA | `INSTALLED_APPS`'te `apps.kutuphane`; belge dizesindeki "Yerel ağa açılan tek yüzey salt-okur Ağ Kataloğu'dur" (satır 5-8); `SECRET_KEY` varsayılanı ve test veritabanı adı program adını taşır; dosya tabanlı test veritabanının gerekçesi katalogtur (Ö: kalabilir, zararsız) |
| `config/urls.py` | UYARLA | `include("apps.kutuphane.urls")` |
| `config/wsgi.py` | AYNEN | |
| `shared/barcode128.py` (+test) | ALMA | §3.5 |
| `shared/crypto.py` | AYNEN + kimlik | §6 |
| `shared/exceptions.py` | UYARLA | `kd_exception_handler` adı; `{code, message, fields}` sözleşmesi aynen |
| `shared/letterhead.py` | UYARLA | Antet "T.C. / <İLÇE> KAYMAKAMLIĞI / <Okul> Müdürlüğü" kurar. Ö: birlik yazıları için ikinci antet ihtiyacı F0-8 evrak kataloğunda karara bağlanır (biçimi mevzuattan doğrulanmadı) |
| `shared/models.py`, `pdf.py`, `text.py`, `working_days.py` | AYNEN | `working_days` plan F1b'deki "tatil ve iş günü hesabı"nın karşılığı |

### 2.8 `backend/apps/okul/`

| Yol | Sınıf | Zaman | Not |
|---|---|---|---|
| `models.py` | UYARLA | F1b | `SchoolConfig`'te kütüphaneye özgü `kutuphane_saatleri`; OAB alanları (kurum kodu, mevcut, yerleşim türü, kantin modu, banka/IBAN) plan §2.2'de. `Student`, `ClassSection` T5'e bağlı (§11-3) |
| `migrations/0001-0006` | ALMA | F1b | Ö: OAB'de kurulu veri yok; tek `0001_initial` ile başlanır |
| `eokul.py`, `excel_ogrenci.py`, `tests/veri/eokul_sinif_listesi.xls` | ALMA | F1b | e-Okul **öğrenci** listesi ayrıştırıcıları (T5: öğrenci listesi alınmaz) |
| `excel_personel.py`, `tests/veri/eokul_personel_listesi.xls`, `uret_eokul_ornekleri.py` | UYARLA | F1b | "Görevi" sütunu yalnız üye türü için geçici okunur (Kütüphane F1 eki 2); OAB'de öğretmen/yönetici ayrımı |
| `kip.py`, `kip_izinleri.py`, `kip_middleware.py`, `views_mode.py` | UYARLA | F1b | Görevli/yönetici kipi → oturum + rol (§6.3) |
| `lock_middleware.py`, `restart_gate.py` | AYNEN / UYARLA | F1a-2 | `restart_gate` iletisi "tepsiden Çık" |
| `masaustu_kanca.py` | UYARLA | F1a-2 | `KatalogKontrolu` protokolü ve bakım kapısı sökülür; çıkış kancası ve gün işleri kaydı kalır |
| `name_match.py`, `normalize.py` | AYNEN | — | Personel birleştirme, TR katlama |
| `permissions.py` | UYARLA | F1b | `RequiresAdminPassword` → rol izinleri |
| `selectors.py`, `serializers.py`, `views.py`, `urls.py` | UYARLA | F1b | Öğrenci dalları (T5) |
| `views_app.py` | UYARLA | F1a-2 | `app/quit/`'te görevli kipi parola dalı |
| `views_calendar.py`, `views_yedek.py` | AYNEN | — | Kapalı günler; dış yedek hatırlatması |
| `views_pool.py` | UYARLA | F1b | Ayrılış havuzu (personel) |
| `services/app_password.py` (1.157 satır) | UYARLA | F1b | T1 (§6.3) |
| `services/backup_restore.py`, `live_restore.py` | UYARLA | F1a-2, F1b | Katalog bakım kapısı (F1a-2); aday güvenlik durumları (F1b) |
| `services/calendar.py`, `dis_yedek.py`, `recovery_key_document.py`, `school_year.py`, `terms.py` | AYNEN | — | |
| `services/encrypted_backup.py` | AYNEN + kimlik | F1a-1 | İndirme adı `kutuphane-defteri-yedek-<damga>.kdbak` |
| `services/imports.py`, `persons.py` | UYARLA | F1b | Öğrenci mutabakatı sökülür; `persons.py`'nin kayıt defteri kancaları (açık yükümlülük) OAB modelleriyle doldurulur |
| `services/sections.py` | T5'e bağlı | F1b | |
| `services/setup.py` | UYARLA | F1b | Adımlar plan §2.2; yol haritası el maddelerinde `katalog_sablonu`, `btr_gorusmesi` |
| `services/templates.py` | UYARLA | F1b | Öğrenci şablonu çıkar |
| `services/updates.py` | UYARLA | F1a-1 | Varsayılan depo ve kurulum dosyası deseni program adını taşır |
| `management/commands/app_password.py`, `restore_backup.py` | UYARLA | F1b | `--parola` → hesap + parola |
| `tests/` (37) | çoğu AYNEN; 6'sı kütüphaneye bağlı | F1a-2 | UYARLA: `test_cikis_ucu`, `test_dis_istek_kapilari`, `test_imports`, `test_kip_koruma`, `test_kisi_yazan_uclar`; ALMA: `test_geri_yukleme_katalog`. T5 ile öğrenci testleri (F1b) ayrıca düşer |

### 2.9 `backend/templates/`

| Yol | Sınıf | Not |
|---|---|---|
| `BENIOKU.md`, `print/_design.css`, `documents/base.html` | AYNEN | Ortak evrak tabanı; `--pdf-duman` bunu işler |
| `documents/kurtarma_anahtari.html` | AYNEN + kimlik | E14 kurtarma anahtarı çıktısı (`okul` uygulamasının tek PDF'i) |
| `documents/aydinlatma_metni.html` | UYARLA (sonra) | İçerik kütüphanenindir; KVKK md. 10 asgari unsur kalıbı işe yarar (veri sorumlusu sorusu F0-5 (b)) |
| `documents/gorev_devri_notu.html` | ALMA | E18; T1 ile anlamı değişir (§6.3) |
| Kalan 19 şablon (etiket, kart, pusula, sayım, ayıklama, ilişik, teslim, katalog afişi, ağ bilgi notu…) | ALMA | |

### 2.10 Plan listesinde **olmayan** ALMA'lık uygulamalar (kopyalanmaz)

| Yol | Büyüklük | Not |
|---|---|---|
| `backend/apps/kutuphane/` | 256 dosya (~49 bin satır kod + ~39 bin satır test) | §3.7 |
| `backend/katalog/` | 34 dosya | §3.2 |

**İskelet testlerinin okuduğu belgeler:** `packaging/tests/test_ikonlar.py` → `docs/site-icerigi.md`;
`desktop/tests/test_sozluk_metinleri.py` → `docs/sozluk.md` (test ALMA). Ö: `test_ikonlar`'ın site belgesi bağı F1a'da
koparılır ya da OAB'nin site içeriği belgesi o güne yazılır.

### 2.11 `frontend/`

| Yol | Sınıf | Not |
|---|---|---|
| Yapılandırma: `package.json`, `package-lock.json`, `vite.config.ts`, `vitest.config.ts`, `tsconfig.json`, `tailwind.config.js`, `postcss.config.js`, `eslint.config.js`, `.prettierrc`, `.prettierignore`, `.dockerignore`, `index.html` | AYNEN / UYARLA | **Listede yok, gerekli.** `package.json` adı; `tailwind.config.js` `--kd-*` değişkenleri; `vitest.config.ts` kapsam eşiği 82/82/78/55 |
| `public/app-logo.png` | UYARLA | Logo |
| `src/` kökü: `App.tsx`, `AppShell.tsx`, `main.tsx`, `index.css`, `KurulumKapisi.tsx`, `vite-env.d.ts` + 4 test | UYARLA | **Listede yok, gerekli.** `App.tsx` rotaları yaklaşık 20 ALMA sayfasını içe aktarır; `index.css` 28 satır `--kd-*` |
| `src/ui/` (50) | AYNEN | Tek istisna `BarcodeInput.tsx` (+test): ALMA (yalnız kütüphane modülleri kullanır) |
| `src/lib/` (15) | AYNEN / UYARLA | `api.ts` (`X-KD-Etkinlik`), `kilit.ts`/`kip.ts`/`restart.ts` (`kd:` olayları), `mevzuat.ts` (Kütüphaneler Yönetmeliği adı), `format.ts` (`formatAccessionNo` ALMA), `gradeLevels.ts` (T5) |
| `src/hooks/` (11) | AYNEN | `useDensity`, `useTheme` saklama anahtarları değişir |
| `src/test/` (6) | UYARLA / ALMA | `setup.ts`, `kurulumDurumu.ts` kalır; dört kütüphane verisi dosyası ALMA |
| `modules/kurulum` | UYARLA | Adımlar plan §2.2 |
| `modules/guvenlik` (26) | UYARLA | `GorevDevri.tsx` `/library/handover/…` uçlarını çağırır — uçlar `apps/kutuphane`'dedir (§3.7); kilit ekranı T1 |
| `modules/ayarlar` | UYARLA | Dört kütüphane panelini içe aktarır (Ağ Kataloğu, Kütüphane Politikası, Bölümler, Saklama) |
| `modules/hakkinda` | UYARLA | "İki dış istek kapısı" ve Ağ Kataloğu paragrafları (§3.9) |
| `modules/kilavuz` | UYARLA | **"Kabuk" ayrı dosya değil:** `KilavuzPage.tsx` 5.080 satırdır, kabuk bileşenleri (Adim/Ipucu/Mevzuat/Ekran) ve içerik aynı dosyada. Ö: kabuk ayıklanır, içerik silinir |
| `modules/panel` ("pano") | UYARLA | Altı kütüphane modülünün kartlarını içe aktarır (katalog şablonu, raporlar, saklama, sayım, dolaşım, yıl akışı) |
| `modules/guncelleme` | AYNEN + metin | `denetimOlayi.ts` "iki kapı" yorumu |
| `modules/cikis`, `modules/kip`, `modules/okul`, `modules/takvim`, `modules/kisiler` | UYARLA / AYNEN | **Listede yok, gerekli:** Çık düğmesi (TB13 dersi), kip/oturum göstergesi ve kapısı (T1), okul bilgileri ve demirbaş, kapalı günler (plan F1b sihirbaz 3. adım), personel aktarımı (T5). `kip` ve `kisiler` kütüphane modüllerini içe aktarır |
| `modules/` agkatalogu, ayiklama, dokumler, dolasim, kayip, kutuphane, raporlar, saklama, sayim, teslim, uyelik, yil | ALMA | 159 dosya. Ö: `saklama` ve `dokumler` (KVKK md. 11 kişi dökümü) ileride kalıp olarak bakılır |

### 2.12 Plan §2.1'den sapmalar — özet

1. **Listede yok ama gerekli:** `docker-compose.yml`, `.github/ISSUE_TEMPLATE/`, `.gitignore` birleştirmesi (§2.1);
   `backend/` kökü (`conftest.py`, `manage.py`, `pyproject.toml`, `requirements*.txt`), `backend/templates/`;
   `frontend/` yapılandırması, `public/`, `src/` kökü, `src/test/`; modüller `cikis`, `kip`, `okul`, `takvim`, `kisiler`.
2. **Listede var ama biçimi farklı:** "kılavuz kabuğu" ayrı dosya değil (5.080 satırlık tek dosya); "pano" `modules/panel`;
   `THIRD_PARTY_LICENSES` üretilmiş dizin; `docker/` tek dosya.
3. **Listede "aynen" görünen ama ALMA taşıyan dizinler:** `desktop/` (7 ALMA modül), `packaging/` (5 ALMA dosya),
   `scripts/` (4'ten 3'ü ALMA), `shared/` (`barcode128.py`).
4. **Ham kopya ara commit'i çalışmaz:** `config/settings.py` (`INSTALLED_APPS`), `config/urls.py`, `desktop/main.py`
   (katalog) ve `frontend` (rotalar, panel, ayarlar) listede olmayan modülleri içe aktarır. Ö: F1a-1 commit'i kapısız
   ara adım sayılır; kapı F1a-2 sonunda. Ya da bu dört yer F1a-1'de en az düzeyde kesilir.
5. **Bağımlılık zinciri "üç yer" değil:** Kütüphane'de dört halka + lisans halkasıdır (§5.2). Plan §2.1 madde 2 metni
   düzeltilmeli.

---

## 3. ALMA listesinin yeri ve bağları

### 3.1 Tepsi

| | |
|---|---|
| **Dosyalar** | `desktop/tray.py`; `packaging/windows/gorev-kur.ps1`; `.iss` görevleri `otobaslat`, `otobaslat\tepside` + `[Run]` + `[UninstallRun]` görev silme; `--tepside` bayrağı |
| **Zincir** | `requirements-paketleme.txt` (pystray, six — win32) ↔ `test_spec_kapsami.PAKETLEME_IMPORT_ESLEME` ↔ spec Windows bloğu (`collect_submodules("pystray")`, `six.moves`, `PIL.ImageDraw`, `PIL.IcoImagePlugin`) + `module_collection_mode` ↔ `giris.DESKTOP_RUNTIME_MODULES` ↔ `test_lisans_kapisi.BEKLENEN_PYTHON_KUMELERI` + pystray/six platform sınamaları ↔ `lisanslar.py` (pystray kaynağı pakette, LGPL yazılı teklifi) |
| **Kırılacaklar** | `main.py`: `TrayActions`, `start_tray`, `tepsi_eylemleri`, `kip_durumu`, `_gorevli_kipine_gec`, `_kilitle`. `window.py`: `WindowController.tray_available`, `on_closing` gizleme, `ask_quit_in_spa` + `kd:cik-iste` olayı (ön yüz `modules/cikis`). **Linux:** `load_qt` (`QT_API=pyside6` sabitlemesi, `QtWebEngineWidgets`'ın `QApplication`'dan önce yüklenmesi), `prepare_qt_application` (pencere simgesi, `setQuitOnLastWindowClosed`), SIGTERM → "Çık" köprüsü (oturum kapanışında temiz kapanış işareti) — üçü de `tray.py`'dedir. İletiler: `lock.py`, `restore.py`, `restart_gate.py`, `.iss` `[Code]` ("tepsi simgesine sağ tıklayıp Çık"). Testler: `test_tray`, `test_main_f5`, `test_window_f5`, `test_window_controller`, `test_spec_kapsami`, `test_lisans_kapisi`, `test_ikonlar` (tepsi yüzeyi). Belge: NOTLAR W13, W14, W17, W20; TB42 |
| **Yapılacak** | Ö: Qt kurulumu ve SIGTERM köprüsü yeni `desktop/qt_kurulum.py`'ye taşınır (tepsisiz `QtTray`'in zaten yaptığı iş), sonra `tray.py` silinir |

### 3.2 Ağ kataloğu sunucusu ve denetimi

| | |
|---|---|
| **Dosyalar** | `backend/katalog/` (34); `desktop/katalog_server.py`, `katalog_kontrol.py`; `apps/kutuphane/ag_katalogu.py`, `katalog_gorunumleri.py` (`kd_katalog_*` görünümleri, göç kancaları), `KatalogAyari` modeli |
| **Kırılacaklar** | **`main.serve` `--autotest` kipinde katalogu kaldırır; kalkmazsa çıkış 6** — katalog silinip satır kalırsa paket duman testi düşer. `masaustu_kanca.KatalogKontrolu` + `live_restore` bakım kapısı. Spec `Tree(backend/katalog)`. `pyproject` `testpaths`/`--cov=katalog`. **§5.10-1 değişmez testleri `test_katalog_server.py`'de**. `test_dis_istek_kapilari.IZINLI` (`desktop/katalog_server.py` satırı). `setup.ROADMAP_MANUAL_ITEMS` `btr_gorusmesi`. `gates.sh` ağ provası + `kapilar.yml` gecelik. `KD_KATALOG_PORT`/`HOST`. Ön yüz Ayarlar → Ağ Kataloğu, tepsi menüsü |

### 3.3 Ağ Doktoru

| | |
|---|---|
| **Dosyalar** | `apps/kutuphane/services/ag_doktoru.py`, `views_ag_doktoru.py`, `ag_belgeleri.py`; `desktop/ag.py`, `powershell.py`; ön yüz `modules/agkatalogu/`; şablonlar `ag_hizmeti_bilgi_notu.html`, `katalog_afisi.html` |
| **Kırılacaklar** | `App.tsx` rotası, `AppShell` gezinmesi, `AyarlarPage`, kılavuz. **segno** (yer imi QR'ı) Ağ Doktoru'nda da kullanılır — segno'yu söküp Ağ Doktoru'nu bırakmak olmaz, ikisi birlikte gider |

### 3.4 Güvenlik duvarı kuralları

| | |
|---|---|
| **Dosyalar** | `desktop/guvenlik_duvari.py`; `.iss`: `katalogizni` görevi, `[Registry]` HKLM port değeri, `netsh` `[Run]`, kural adı ve anahtar `#define`'ları; `packaging/linux/ufw-*`, `firewalld-*.xml` ve `build.sh` kurulum satırları |
| **Kırılacaklar** | `main.run`'daki UAC yardımcı kipi dalı (`--guvenlik-duvari-kurali`); `rthook_kd.py`'deki aynı bayrağın ikizi ve `test_rthook` eşitlik testi; `test_guvenlik_duvari`; NOTLAR W15, W16, W18. **Sonuç:** kurucunun yönetici istemesinin (U4) ana gerekçesi düşer (§11-1) |

### 3.5 Barkod ve etiket

| | |
|---|---|
| **Dosyalar** | `shared/barcode128.py` (+test); `apps/kutuphane/labels/` (13), `barcode.py`, `services/label_render.py`; `ui/BarcodeInput.tsx` (+test); şablonlar `etiket_*`; `lib/format.formatAccessionNo` |
| **Zincir** | segno: `requirements.txt` → `DAGITIM_IMPORT_ESLEME` → spec `collect_submodules("segno")` → `RUNTIME_MODULES` → lisans kümesi. **`test_bagimlilik_duman_gercek_listeyle_gelistirme_kabinda_gecer` `"segno" in RUNTIME_MODULES` diye sabit sınar** — o satır da değişir |

### 3.6 ISBN ve künye

| | |
|---|---|
| **Dosyalar** | `apps/kutuphane/isbn.py`, `kunye/` (10), `views_kunye.py`; ön yüz `CevrimdisiKunyePaneli` |
| **Kırılacaklar** | `test_dis_istek_kapilari` (`IZINLI`, `GUNCELLEME_KULLANICILARI`, "masaüstü künye modülünü içe aktarmaz" testi); T11 cümlesinin kopyaları (§3.9) |

### 3.7 `apps/kutuphane` ve ekranları

| Bağ | Nerede | Etki |
|---|---|---|
| Uygulama kaydı | `settings.INSTALLED_APPS`, `config/urls.py` | Django kalkmaz |
| `ready()` kayıtları | `apps/kutuphane/apps.py` | Kişi kancaları (`persons.py` kayıt defteri boş kalır — sorun değil), **kip süre kaynağı** (`kip.sure_kaynagini_kaydet(policy…)` — yoksa varsayılan 3/30 dk), gün işleri (çok okunanlar, saklama taraması), katalog görünümü göç kancaları, `mark_process_start` (T15 "son oturum" kartı) |
| Görev devri uçları | `library/handover/`, `…/start/`, `…/note/` (`urls_gorev_devri.py`, `gorev_devri.py`) | Ön yüz `guvenlik/GorevDevri.tsx` ve `api.ts` kırılır; `app_password.start_handover` okul'dadır ama E18 PDF'i kütüphanededir |
| Son oturum kartı | `apps/kutuphane/pano.py` | `clean_shutdown.publish` yazar, okuyan yalnız kütüphane |
| Saklama | `services/saklama.py`; `backup.py` ve `persons.py` belge dizeleri | `pre-anonim` yedeği tetiklenmez (zararsız) |
| Testler | okul testlerinden 6'sı, `desktop/tests/test_geri_yukleme_provasi.py` + `prova_betigi.py`, `packaging/tests/test_ikonlar.py` | §2.5, §2.8 |
| Saha kabulü eşleme testi | `apps/kutuphane/tests/test_saha_kabulu_belgesi.py` | NOTLAR, teknik borç ve tasarım eşlemesini sınar; uygulamayla birlikte gider. Ö: OAB F7'de kendi eşleme testini yazar |
| Ön yüz | 12 modül + `App.tsx`, `AppShell`, `panel`, `ayarlar`, `kip`, `kisiler`, `kilavuz` testleri | `tsc` ilk koşuda kırılır |
| Evrak | `templates/documents/` 23 şablonun 20'si | §2.9 |

### 3.8 Kütüphaneye özgü ama ALMA listesinde adı geçmeyenler

- `desktop/dagitim.py` + `--dagitim-duman` (yalnız katalog kapısı için var).
- `desktop/gunluk.py`'deki uyku engelleme (`SetThreadExecutionState` / `systemd-inhibit`; yalnız katalog açıkken).
- `SchoolConfig.kutuphane_saatleri`, `setup` yol haritası maddeleri, `lib/mevzuat.ts` Yönetmelik adı.
- `.iss` otomatik başlatma (tepsi kararı U3'ün parçası).
- e-Okul öğrenci ayrıştırıcıları (T5).

### 3.9 "Ağ servisi sunar" ifadeleri — geri çevrilecek yerler

| Yer | Bugünkü ifade (özet) |
|---|---|
| `backend/config/settings.py:5-8` | "Yerel ağa açılan tek yüzey salt-okur Ağ Kataloğu'dur" |
| `desktop/server.py:14-16` | "Ağ Kataloğu ayrı bir dinleyicidir… yönetim API'si hiçbir koşulda ağa açılmaz" |
| `desktop/main.py:10-23` (belge dizesi) | Adım 10-11 katalog ve tepsi |
| `backend/apps/okul/masaustu_kanca.py:3-13` | Katalog dinleyicisi süreçte |
| `docker-compose.yml:6-7` | "paketli program yerel ağa salt-okur bir KATALOG dinleyicisi sunar" |
| `SECURITY.md` | Kapsam: "ağ kataloğu yüzeyi" |
| `packaging/linux/debian-control.tmpl` | "İsteğe bağlı ağ kataloğu açılırsa…" |
| `packaging/linux/BENIOKU.txt`, `packaging/README.md`, `windows/NOTLAR.md`, `.iss` başlığı (satır 17-33) | Katalog, güvenlik duvarı, tepsi |
| `frontend/src/modules/hakkinda/HakkindaPage.tsx` "Teknik Bilgiler" | "Dış istek yalnız … iki durumda" + Ağ Kataloğu maddesi |
| `frontend/src/modules/guncelleme/denetimOlayi.ts` | "iki kapı" yorumu |
| `backend/apps/okul/tests/test_dis_istek_kapilari.py` | İzinli dış istemci listesi |

Ö: tek cümle bütün kopyalara aynen konur — *"Program ağ servisi sunmaz: yönetim sunucusu yalnız `127.0.0.1`'de,
rastgele portta ve oturum belirteciyle dinler; hiçbir port okul ağına açılmaz. Dış istek yalnız kullanıcının başlattığı
güncelleme denetiminden çıkar."* Değişmez testi daralır: `0.0.0.0` hiçbir üretim kaynağında geçmez (tek muafiyet
`window.py`'deki WebView2 sürüm damgası).

---

## 4. Kimlik sabitleri

### 4.1 Çeviri tablosu

| Öğe | Kütüphane değeri | Yeri (örnek) | OAB (plan §1.4) | Not |
|---|---|---|---|---|
| Ortam değişkeni öneki | `KD_*` (25 ad) | `config/settings.py:27`, `desktop/session_guard.py` | `OD_*` | Kalanlar: `SESSION_TOKEN`, `DEBUG`, `APP_VERSION`, `APP_HOME`, `DATA_DIR`, `SECURITY_DIR`, `BACKUP_DIR`, `BACKEND_DIR`, `FRONTEND_DIR`, `RTHOOK_UYARI`, `ONCEKI_OTURUM`, `SECRET_KEY`, `MAX_UPLOAD_SIZE_MB`, `UPDATE_REPOSITORY`, `WITH_QT`, `DLL_DIR`, `SKIP_PIP`, `BUILD_IMAGE`, `AG_TUZAGI_KAYIT`. ALMA: `KATALOG_PORT`, `KATALOG_HOST`, `PROVA_ESER`, `EKRAN_DERLE`, `YAVAS` (yavaş test kalmazsa) |
| Veri dizini | `KutuphaneDefteri` / `kutuphane-defteri` | `desktop/paths.py:24-25` | `OABDefteri` / `oab-defteri` | |
| Oturum çerezi | `kd_oturum` | `session_guard.SESSION_COOKIE_NAME` | `od_oturum` | |
| Oturum başlığı | `X-KD-Token` | `session_guard.TOKEN_HEADER` | `X-OD-Token` | |
| Etkinlik başlığı | `X-KD-Etkinlik` | `frontend/src/lib/api.ts:35`, `kip_middleware` | **planda yok** | Ö: `X-OD-Etkinlik` (T1'de boşta süre kalırsa) |
| Yedek uzantısı / MAGIC | `.kdbak` / `KDBAK\x02` | `desktop/backup_crypto.py:25,30` | `.odbak` / `ODBAK\x02` | `.gitignore`, `depo_sizintisi`, `veri_sizintisi`, `SECURITY.md` aynı anda |
| Yedek HKDF bilgileri | `KutuphaneDefteri/backup/private/v1`, `…/envelope/v1` | `backup_crypto.py:34-35` | `OABDefteri/backup/...` | İki dizge |
| Kör indeks HKDF | `kd-kor-indeks` | `shared/crypto.py:173` | `od-kor-indeks` | |
| Anahtar parmak izi HMAC | `kd-anahtar-parmak-izi` | `shared/crypto.py:168` | **planda yok** | Ö: `od-anahtar-parmak-izi` |
| Yedek indirme adı | `kutuphane-defteri-yedek-<damga>.kdbak` | `services/encrypted_backup.py:48` | — | Ö: `oab-defteri-yedek-<damga>.odbak` |
| Inno AppId | sabit GUID | `.iss:84` | yeni GUID | Asla yeniden kullanılmaz |
| Mutex | `KutuphaneDefteri`, `Global\KutuphaneDefteri` | `desktop/lock.py:42-43`, `.iss:198` | `OABDefteri`, `Global\OABDefteri` | |
| Adlı olaylar | `KutuphaneDefteri.Goster` / `.Kapat` | `instance_channel.py:45-46`, `.iss:197` | **planda yok** | Ö: `OABDefteri.Goster` / `.Kapat` |
| AUMID | `KutuphaneDefteri.Desktop` | `window.py:50`, `.iss:56` | `OABDefteri.Desktop` | |
| exe / dağıtım adı | `kutuphane-defteri.exe` | `.iss:55`, spec `DIST_NAME` | `oab-defteri.exe` | Çıktı adları (`build.ps1`, `build.sh`, `.iss` `OutputBaseFilename`) ve `updates.INSTALLER_PATTERN` birlikte |
| Pencere başlığı / argparse | `Kütüphane Defteri` / `kutuphane-defteri` | `window.py:45`, `main.py:135` | — | Ö: "OAB Defteri" / `oab-defteri` |
| Kurulum dizini | `{autopf}\Kütüphane Defteri` | `.iss` `AppName` | — | Ö: `OAB Defteri` |
| spec / rthook | `kutuphane_defteri.spec`, `rthook_kd.py` | `packaging/pyinstaller/` | `oab_defteri.spec`, `rthook_od.py` | |
| Logger | `kutuphane_defteri` + alt adlar (`.server`, `.window`, `.okul`, `.guvenlik`, `.restore`…) | `logging_setup.py:25` | `oab_defteri` | Alt adlar dahil |
| İş parçacıkları | `kd-wsgi`, `kd-kanal`, `kd-gunluk`, `kd-cikis` | `server.py:132`, `instance_channel.py:56`, `gunluk.py:63`, `main.py:243` | `od-wsgi` (yalnız bu) | Ö: `od-kanal`, `od-gunluk`, `od-cikis`. ALMA: `kd-katalog*`, `kd-tepsi` |
| Debian paketi | `kutuphane-defteri`, Section `education` | `debian-control.tmpl` | `oab-defteri`, `education` | `/opt/…`, `/usr/bin/…`, `.desktop` adı, `StartupWMClass`, hicolor simge adı (`tray.THEME_ICON_NAME`, `build.sh`), doc dizini, `.tar.gz` adı aynı anda |
| Simge dosyaları | `kutuphane-defteri-{16…512}.png`, `.ico`, `-logo.png` | `packaging/ikonlar/`, `window.WINDOW_ICON_FILE`, spec `ICON` | — | Dosya adları da kimlik taramasına girer |
| Güncelleme deposu | varsayılan `<kullanıcı>/kutuphane-defteri` | `services/updates.py:38` | **planda yok** | GitHub deposu adı yayın işidir (kullanıcı onaylı) |
| Issue şablonu | depo adresi | `.github/ISSUE_TEMPLATE/config.yml:4` | — | |
| Site | palet `kd`, `src/data/kd-release.json`, `KDLayout.astro`, `src/pages/kutuphane-defteri/**`, `public/kutuphane-defteri.png` | kaynak `CLAUDE.md` §6 | palet `od`, `od-release.json`, sayfa `okulapp.org/oab-defteri` | Ö: `ODLayout.astro`, `public/oab-defteri.png` |
| R2 | `kutuphane-defteri/` | `packaging/r2-yukle.sh:52` | `oab-defteri/` | |
| Compose proje adı | `kutuphane-defteri` | `docker-compose.yml` | — | Ö: `oab-defteri` |
| Ön yüz paket adı | `kutuphane-defteri-frontend` | `frontend/package.json` | — | |
| CSS değişkenleri ve sınıflar | `--kd-*` (index.css 28, tailwind 8 satır), `kd-page-title/-header/-description` | `frontend/src/index.css`, `tailwind.config.js` | **planda yok** | Ö: `--od-*`, `od-page-*`. Sitedeki "palet" ile karıştırılmamalı |
| DOM olayları | `kd:cik-iste`, `kd:kilit-kapisi`, `kd:kip-yetkisiz`, `kd:yeniden-baslat-gerekli`, `kd:guncelleme-denetlendi` | `window.py:304`, `lib/kilit.ts`, `lib/kip.ts`, `lib/restart.ts` | **planda yok** | Ö: `od:*`; `cik-iste` T6'da düşer |
| Tarayıcı deposu anahtarları | `kutuphane-defteri-density`, `-sidebar-collapsed`, `-dismissed-update`, `-okuma-sesi`; `oys-theme` | `useDensity.ts`, `AppShell.tsx:74`, `UpdateBanner.tsx:22`, `BarcodeInput.tsx`, `useTheme.ts` | **planda yok** | Ö: `oab-defteri-*`. `oys-theme` OYS kalıntısıdır, mevcut taramaya takılmaz |
| İstisna işleyicisi | `kd_exception_handler` | `shared/exceptions.py`, `settings` | — | Ö: `od_exception_handler` |
| Django gizli anahtar varsayılanı / test VT | program adını taşır | `settings.py:47`, `:154` | — | |
| Kapı geçici dosyası | `.kd-depo-listesi.tmp` | `scripts/gates.sh`, `.gitignore` | — | |
| Test geçici dizinleri | `kd-guvenlik`, `kd-yedek` | `backend/conftest.py:109-110` | — | |
| Inno katalog kimlikleri | kural adı, HKLM anahtarı, görev adı, `RunOnceId` | `.iss:62-66, 186` | ALMA | |
| Katalog görünümleri | `kd_katalog_*` | `apps/kutuphane` | ALMA | |

### 4.2 Kalıntı taraması sayımları (host'ta salt okuma; TR katlamalı)

| Kalıp | Bütün ağaç (`docs` dahil) | Kod (`docs`, `CLAUDE.md`, `AGENTS.md` hariç) | **F1a kopya kümesi** (≈425 dosya) |
|---|---|---|---|
| `kutuphane[ _-]?defteri` (plan) | 150 dosya | 141 | 83 dosya / 398 satır |
| `k[uü]t[uü]phane[ _-]?defteri` (öneri) | 210 | 194 | **110 / 506** |
| `kd[_:-]` | 228 | 221 | 101 / 315 |
| `x-kd-` | 30 | 27 | 12 / 19 |
| `kdbak` | 51 | 44 | 39 / 190 |
| `kelebek` | 6 | 0 | 0 |
| `ks[_:-]`, `x-ks-`, `ksbak` | 4 / 4 / 4 | 0 | 0 |
| `disiplin[ _-]?defteri`, `x-dd-`, `ddbak` | 4 / 4 / 4 | 0 | 0 |

Kopya kümesinde en az bir kalıba (öneri kalıplarıyla) takılan **185 dosya** var. KS/DD kalıplarının "bütün ağaç"
eşleşmeleri yalnız `docs/`, `CLAUDE.md` ve kalıpları taşıyan test dosyasındandır.

**Bulgu (plan §1.4'te kusur).** `katla()` yalnız `İ/I/ı`'yı katlar; `ü` katlanmaz. Plan kalıbı `kutuphane[ _-]?defteri`
"Kütüphane Defteri"yi **yakalamaz** — kopya kümesinde 27 dosya yalnız bu yazımı taşıyor (pencere başlığı, Inno
`AppName`, `.desktop`, Hakkında, ileti metinleri). Ö: kalıp `k[uü]t[uü]phane[ _-]?defteri` olur. `kd[_:-]` için de
KS kalıbındaki kelime sınırı (`(?<![^\W_])`) eklenir.

### 4.3 `test_kimlik_kalintisi.py` nasıl çalışıyor, OAB'ye nasıl uyarlanır

**Gözlem.**
- Depo kökünden dosya ağacını dolaşır (kapta git yok; izlenen liste değil ağaç). Her dosyanın **yolu** (`yol:0`) ve
  her **satırı** taranır; NUL baytı taşıyan dosya ikili sayılıp içerik taranmaz (ad yine taranır).
- Eşleşme satır satır, `katla()` (İ/I/ı → i, ayrışık U+0307 silinir, `casefold`) uygulanmış metinde.
- Atlananlar: `.git`, `node_modules`, `__pycache__`, `*_cache`; yollar `docs`, `frontend/dist`, `backend/data`, `build`,
  `dist`, `.claude/settings.local.json`. Tam yolla muaf: `CLAUDE.md`, `AGENTS.md`. `TEKNIK_BORC_MUAFIYETLERI` boş.
- Dosya kendi kalıplarını karakter sınıfıyla (`k[e]lebek`), örneklerini `|` bölücüsüyle yazar; kendini muaf tutmadan
  taramadan geçer.
- Ek testler: kapsam boş değil (`README.md`, `docker-compose.yml`, `scripts/gates.sh`, `kapilar.yml`, `settings.py`,
  `base.html`, `main.py`, `.iss`, spec, test dosyasının kendisi, `frontend/package.json` taranmalı; `docs` taranmamalı),
  kelime sınırı yanlış pozitif vermez (Inno `Tasks:`, `gitleaks:allow`), kalıplar örnekleri yakalar, muaf dosyalar
  depoda var, teknik borç muafiyeti hâlâ gerekli.

**Ö: OAB uyarlaması.**
1. `KALIPLAR`: KS/DD kalıpları aynen kalır; Kütüphane kalıpları eklenir — `k[uü]t[uü]phane[ _-]?defteri`,
   `(?<![^\W_])k[d][_:-]`, `x-k[d]-`, `k[d]bak`. İsteğe bağlı `(?<![^\W_])o[y]s-` (OYS kalıntısı).
2. `test_tarama_kapsami_bos_degil` beklenen yolları OAB adlarına çevrilir (`packaging/windows/oab-defteri.iss`,
   `packaging/pyinstaller/oab_defteri.spec`).
3. `test_kaliplar_kalintiyi_yakalar`'a "Kütüphane Defteri", "KÜTÜPHANE DEFTERİ", `X-K|D-Token`, `yedek.k|dbak`,
   `KutuphaneDefteri.Kapat` örnekleri eklenir.
4. Muafiyet: `CLAUDE.md`, `AGENTS.md` (köken anlatır). OAB `README.md`'si herkese açıktır ve kapsamda kalır — köken
   cümlesi yazılmaz ya da muafiyet gerekçesiyle eklenir (kullanıcı kararı).
5. Ö: arındırma için **ayrı ve uyarı düzeyinde** bir "alan kalıntısı" listesi (ödünç, nüsha, barkod, ISBN, tepsi,
   görevli kipi, Ağ Kataloğu) F1a-2'de bir kez elle koşulur. Kapıya girmez: "katalog" (evrak kataloğu) gibi meşru
   kullanımlar var.

---

## 5. Bağımlılık zinciri

### 5.1 Python bağımlılıkları (`backend/requirements.txt`)

| Paket | Sürüm | Kütüphane'de kullanım | OAB |
|---|---|---|---|
| Django / djangorestframework | 5.1.15 / 3.15.2 | çekirdek | kalır |
| argon2-cffi / cryptography | 23.1.0 / 48.0.1 | parola türetme, Fernet, HKDF, X25519, AES-GCM | kalır |
| openpyxl | 3.1.5 | xlsx okuma/yazma | **zaten var**, kalır |
| xlrd | 2.0.1 | e-Okul `.xls` | kalır (personel listesi, T5) |
| Pillow | 12.3.0 | evrak raster, ikon, tepsi | kalır |
| weasyprint | 68.0 | PDF | kalır |
| pypdf | 6.14.2 | `--pdf-duman` geri okuma | kalır |
| segno | 1.6.1 | etiket QR, Ağ Doktoru QR | **çıkar** |
| whitenoise / waitress | 6.12.0 / 3.0.2 | SPA servisi, WSGI | kalır |
| — | — | — | **python-docx eklenir** (yok); geçişli **lxml** gelir. Ö: lxml de doğrudan pinlenir (lisans kümesi ve kısıt dosyası sürümü bağlasın) |

Paketleme (`packaging/requirements-paketleme.txt`): `pyinstaller==6.11.1`, `pywebview==5.3.2`, `pythonnet==3.0.5`
(win32), `pystray==0.19.5` + `six==1.17.0` (win32 — **çıkar**), `QtPy==2.4.3` + `PySide6==6.8.3` (linux — kalır;
6.9.1+ Pardus 21'de açılmaz, TB27).

### 5.2 Halkalar ve birlikte bakım

| Halka | Yer | Denetleyen |
|---|---|---|
| 1 | `backend/requirements.txt` (pin) | — |
| 2 | `packaging/tests/test_spec_kapsami.py::DAGITIM_IMPORT_ESLEME` (dağıtım → modül) | yeni pin eşlemesizse test kırılır |
| 3 | spec `hiddenimports` (`collect_submodules("<modül>")` ya da `"<modül>"` dizesi) | aynı test, statik |
| 4 | `packaging/pyinstaller/giris.py::RUNTIME_MODULES` | `test_runtime_modules_requirements_ile_senkron` (küme eşitliği); paketli ikilide `--bagimlilik-duman` gerçekten içe aktarır |
| Lisans | `bash packaging/lisanslar/uret.sh` → `THIRD_PARTY_LICENSES/` + `test_lisans_kapisi.BEKLENEN_PYTHON_KUMELERI` (Windows ve Linux ayrı küme) + `lisanslar.py kisitlar` (pip kısıt dosyası) + derlemede `lisanslar.py paket` (yalnız GPL'li bileşende durur) | kapı testi; derleme |
| Masaüstü | `requirements-paketleme.txt` (win32 işaretli) ↔ `PAKETLEME_IMPORT_ESLEME` ↔ spec Windows bloğu ↔ `DESKTOP_RUNTIME_MODULES` | `test_masaustu_modulleri_*` |
| Linux Qt | `QtPy` + `PySide6` (linux işaretli) ↔ spec `WITH_QT` bloğu ↔ `LINUX_DUMAN_DISI` ↔ `build.sh` adım 4b (QtWebEngineProcess var mı) | test + derleme |
| npm | `package.json` ↔ `on_yuz_paketleri.mjs` (Vite çıktısındaki paketler) ↔ `lisanslar.py npm-denetle` | `gates.sh` |

**Plan sapması:** plan §2.1 madde 2 "üç yere" diyor; Kütüphane'de dört halka + lisans halkasıdır. Yeni bağımlılık
`uret.sh` koşulmadan kapıdan geçmez.

### 5.3 OAB için değişiklik listesi

| Değişiklik | Dokunulacak yerler |
|---|---|
| segno çıkar | requirements · `DAGITIM_IMPORT_ESLEME` · spec · `RUNTIME_MODULES` · `test_bagimlilik_duman_gercek_listeyle…` (segno'yu adıyla sınıyor) · lisans kümesi · `lisanslar.py` |
| pystray, six çıkar | paketleme gereksinimleri · `PAKETLEME_IMPORT_ESLEME` · spec Windows bloğu + `module_collection_mode` · `DESKTOP_RUNTIME_MODULES` · lisans kümesi ve pystray/six platform sınamaları · `lisanslar.py` (pystray kaynağı, yazılı teklif kapsamı) · NOTLAR W13, W20, W22 |
| python-docx (+ lxml) girer | requirements · eşleme (`"python-docx": "docx"`, `"lxml": "lxml"`) · spec (`collect_submodules("docx")`; python-docx'in iç şablon dosyaları için `collect_data_files("docx")` gerekip gerekmediği **doğrulanmadı**) · `RUNTIME_MODULES` · lisans kümesi (iki platform) · `uret.sh` · Ö: `--evrak-duman` |
| Ön yüz | F1a'da npm değişikliği yok |

---

## 6. Güvenlik çekirdeği

### 6.1 Bugünkü yapı (gözlem)

| Bileşen | Dosya | Nasıl |
|---|---|---|
| Veri anahtarı (DEK) | `shared/crypto.py` | 32 bayt rastgele; kurulumda bir kez üretilir, **hiç değişmez** |
| Parola türetme | `crypto.derive_key` | Argon2id, RFC 9106 düşük bellek profili (64 MiB, t=3, p=4, ~0,2 sn); parametreler `guvenlik.json`'da saklanır |
| Sarma (zarf) | `crypto.wrap_key` / `unwrap_key` | DEK, paroladan türetilen anahtarla **Fernet** ile sarılır; ayrı parola özeti tutulmaz — sarmalın çözülmesi parolanın kanıtıdır |
| Güvenlik dosyası | `guvenlik.json` (veri dizini) | `surum`, `kdf`, `parola{salt,sarmal}`, `kurtarma{salt,sarmal,dogrulandi,gorev_devri}`, `gecis` |
| Parmak izi | `SchoolConfig.app_password_hash` | `HMAC(DEK, "kd-anahtar-parmak-izi")`; DB ile güvenlik dosyasının eşleştiğini gösterir |
| Kurtarma anahtarı | `app_password.generate_recovery_key` | 20 bayt → base32 → 8 dörtlü grup; normalleştirme `İ/ı → I`, `0/1/8 → O/I/B`. Kurulum, anahtarın saklandığı doğrulanmadan tamamlanmaz (damga). Yenileme aynı DEK'i yeni anahtarla sarar, öncekini `guvenlik-arsiv-*`e kopyalar |
| Alan şifrelemesi | `EncryptedTextField` / `EncryptedCharField` | Fernet; boş dize şifrelenmez; **anahtar yokken yazma `KeyMissingError`** (→ 409 `parola_gerekli`); kilitliyken okuma token'ı aynen döndürür. Şifreli alanda DB araması yok |
| Kör indeks | `crypto.blind_index` | `HMAC-SHA256(HKDF(DEK, "kd-kor-indeks"), normalize(değer))`; teklik kısıtı indekste; parola değişimi bozmaz |
| Kayıp kilidi (fail-closed) | `app_password.security_file_missing`, `backup_crypto.is_usable_security_state` | Parmak izi dolu + dosya yok **ya da** dosya var ama kullanılamaz → "güvenlik dosyası kayıp": yalnız durum ve geri yükleme açık. Korunacak veri yoksa "sıfırla ve kuruluma dön" |
| `enable()` ön koşulları | `app_password.enable` | Dosya yok, parmak izi boş, kişi tabloları boş. Sıra: dosya → `pre-parola` yedeği → tek işlemde satırlar + parmak izi → `gecis=TAMAM` |
| Yanlış parola | `_delay_after_failure` | 0, 0, 1, 2, 4 sn kademeli; kalıcı kilit yok (kendi kendine hizmet reddi olurdu) |
| Oturum belirteci | `desktop/session_guard.py` | Her açılışta rastgele; URL'de `?t=` → `HttpOnly` çerez; başlık alternatifi; belirteçsiz istek 403. Yalnız `KD_SESSION_TOKEN` doluyken yüklenir |
| Ara katman sırası | `settings.MIDDLEWARE` | belirteç → güvenlik → whitenoise → common → `RestartRequired` (503) → `AppLock` (423) → `KipMiddleware` (403 `kip_yetkisiz`) |
| Kipler | `apps/okul/kip.py` | `kurulum`, `kilitli`, `guvenlik_dosyasi_kayip`, `yonetici`, `gorevli`. Görevli kipi uç **ve parametre** düzeyinde izin listesi, yeni uç varsayılan kapalı; URL desenlerini dolaşan koruma testi |
| Oturum süreleri | `kip.kip_sureleri` | Boşta 3 dk, mutlak 30 dk (yönetici → görevli); kaynak `LibraryPolicy` (kütüphanede); yalnız `X-KD-Etkinlik` başlıklı istek tazeler; uykuyu sayan saat; kurulum bitene kadar süreler kipi düşürmez (TB19) |
| Şifreli yedek | `desktop/backup_crypto.py`, `backup.py` | `MAGIC(6) + geçici X25519 açık anahtar(32) + nonce(12) + uzunluk(4) + kurtarma başlığı + AES-256-GCM(gövde, başlık AAD)`. Yedek özel anahtarı `HKDF(DEK, ".../backup/private/v1")`; açık anahtar `yedekleme.json`'da (parolasız yedek alınabilsin). **Başlık, alındığı anın bütün `guvenlik.json`'unu düz taşır** |
| Yedek türleri | `backup.py`, `app_password` | Günlük (14 gün), göç öncesi (son 5), `pre-parola`, `pre-anonim`; `Connection.backup()` ile, WAL kopyası yasak |
| Eski program kapısı | `desktop/version.py` | Sürüm damgası + tanınmayan göç kaydı → çıkış 4 |
| Görev devri | `app_password.start_handover` + `apps/kutuphane/gorev_devri.py` | Parola ve kurtarma anahtarı tek atomik yazımda; DEK döndürülmez (TB17, TB23) |

### 6.2 Kelebek ile fark

Kütüphane, Kelebek'in "kör indeks yok" kararından ve parolasız dalından bilinçli ayrıldı; TB26'ya göre üç denetim
bulgusu (GA-2, UY-1, SU-25) Kelebek'te hâlâ açık. OAB bu çekirdeği Kütüphane'den aldığı için kapalı hâli devralır.

### 6.3 T1 (b) — kişisel hesaplar bu yapıya nasıl oturur

**Uyum.** Zarf tasarımı zaten "aynı DEK, birden çok sarmal" üzerine kurulu (bugün iki sarmal: parola ve kurtarma). Hesap
başına sarmal bu yapının doğal genişlemesidir: veri yeniden şifrelenmez, kör indeks ve yedek anahtarı DEK'ten türediği
için değişmez, kurtarma anahtarı deseni aynen kalır. Unutulan hesap parolası, kilidi açık yönetici tarafından DEK'i yeni
geçici parolayla sararak sıfırlanabilir.

**Ö: şema (sürüm 2, değerler yer tutucu).**

```json
{
  "surum": 2,
  "kdf": {"time_cost": 3, "memory_cost": 65536, "parallelism": 4},
  "hesaplar": [
    {"id": "<hesap-kimliği>", "tanitici": "<giriş adı>", "salt": "<…>", "sarmal": "<…>"}
  ],
  "kurtarma": {"salt": "<…>", "sarmal": "<…>", "dogrulandi": "<zaman damgası>"},
  "gecis": "TAMAM"
}
```

- **Rol `guvenlik.json`'da değil DB'de** (`Hesap` modeli: kimlik, rol, ad-soyad şifreli, organ üyeliği bağı F1c'de,
  açılış/kapanış tarihi). Giriş, `tanitici`'yla sarmal bulunur, parola sarmalı çözerse kilit açılır; DB'den rol okunur.
- **`tanitici` gerçek ad olmaz** (ör. "muhasip", "baskan"): dosya ve her yedeğin başlığı düz metindir.
- **Süreç içi tek oturum:** bugünkü `KipDurumu` → `OturumDurumu` (kilitli · hesap kimliği · rol). Kullanıcı değiştirmek
  = kilitle + başka hesapla aç. Boşta süre dolunca **kilit** (görevliye iniş yok). Ö: varsayılan süre karar ister.
- **Rol izinleri** görevli kipinin deseniyle: uç + yöntem matrisi, yeni uç varsayılan kapalı, URL dolaşan koruma testi
  (`test_kip_koruma` kalıbı). Salt okur roller (Denetleme Kurulu, müdür) yalnız güvenli yöntemler + açıkça izinli
  evrak çıktıları.
- **Denetim izi yeni modeldir:** Kütüphane'de `AuditLog` bilerek yok (tasarım §11 B4). OAB altın kural 4 ister; her
  yazma oturumdaki hesap kimliğiyle kayda düşer.

**Değişecek dosyalar (F1b).** `apps/okul/services/app_password.py` (şema 2, `enable` → ilk yönetici hesabı, `unlock(hesap,
parola)`, hesap ekle/kapat, yönetici sıfırlaması, görev devri yerine dönem sonu hesap kapanışı) · `desktop/backup_crypto.py`
(`is_usable_security_state`, `recovery_metadata`) · `services/backup_restore.py` (aday durumlar, hesap seçimi) ·
`desktop/restore.py` + `management/commands/restore_backup.py`, `app_password.py` (`--hesap`) · `kip.py`, `kip_izinleri.py`,
`kip_middleware.py`, `views_mode.py`, `permissions.py`, `views_app.py` · `models.py` (Hesap, DenetimIzi) · `shared/crypto.py`
(yalnız kimlik dizgeleri; ilkel işlevler aynen) · ön yüz `guvenlik/KilitEkrani`, `KurulumPage` 1. adım, `GuvenlikAyarlari`,
`kip/*` → oturum, yeni Kullanıcılar ekranı, `lib/api.ts` · testler `test_app_password`, `test_kip*`, `test_backup_restore`,
`test_guvenlik_sifirlama`, `test_kurtarma_*`, desktop geri yükleme provası.

**Riskler (dürüst sınırlar).**
1. **Rol kriptografik değildir.** Her hesap aynı DEK'i açar; salt okur rolün kısıtı uygulama düzeyindedir. Parolasını
   bilen biri veri dizinini kopyalayıp DEK'i dışarıda türetebilir. Ö: Kütüphane'nin "kaza önleyici, güvenlik sınırı
   değil" dili (tasarım §4.2-4) aynen yazılır; hesapların değeri **izlenebilirliktir**.
2. **TB17/TB23 OAB'de ağırlaşır.** Hesaplar dönemlik, veli üyeler okul dışındandır. Kapatılan hesabın sarmalı eski
   yedeklerin başlığında ve `guvenlik-arsiv-*` dosyalarında kalır; eski parola + eski başlık → DEK → sonraki yedekler de
   açılır. Ö: (i) yedek başlığına yalnız `kurtarma` bölümü konur (yeni bilgisayara geri yükleme kurtarma anahtarı
   ister); (ii) hesap kapanınca arşiv kopyalarından da sarmal silinir; (iii) dönem kapanışında DEK döndürme (Kütüphane
   v1 dışı bırakmıştı) — karar.
3. Hesap sayısı ve Argon2id: girişte yalnız seçilen hesabın sarmalı denenir; hepsi denenirse süre hesap sayısıyla büyür.

---

## 7. Evrak hattı

### 7.1 Bugünkü yapı (gözlem)

| Parça | Yer | Not |
|---|---|---|
| PDF tek kapısı | `shared/pdf.py::html_to_pdf` | Süreç geneli kilit + paylaşılan `FontConfiguration` (eşzamanlı basım Pango'da bellek bozuyordu); `shared/tests/test_pdf.py` başka `write_pdf` çağrısına izin vermez |
| Şablon tabanı | `templates/documents/base.html` + `print/_design.css` (`{% include %}`) | DejaVu Sans; `text-transform` yasak; `@page` altlığında "Sayfa n / m" |
| Antet | `shared/letterhead.py` | T.C. / `<İLÇE> KAYMAKAMLIĞI` / `<Okul> Müdürlüğü`; ilçe `tr_upper` ile |
| Türkçe harf | `shared/text.py` (`tr_upper`, `tr_lower`, `tr_title`); eşleştirme `apps/okul/normalize.py` | Çıplak `.upper()` yasak |
| `--pdf-duman` | `packaging/pyinstaller/giris.py` | Ayarsız Django `Engine` ile taban şablondan Türkçe örnek; pypdf ile geri okur: `ĞÜŞİÖÇ ığüşiöç`, "Sayfa", gömülü DejaVu; başarısızlıkta fontconfig tanısı; çıkış 8 |
| Excel | `openpyxl` (`services/templates.py` kalıbı), e-Okul `.xls` `xlrd` | |
| İndirme | `lib/download.ts::saveBlob` + `window.py` `ALLOW_DOWNLOADS` | |
| WeasyPrint tuzakları | kaynak `CLAUDE.md` §3 | px birimi, tablo yüksekliği, `table-layout: fixed`, `break-inside`, **gerçek uzunlukta veriyle sayfa bütçesi testi** |
| Belge izi | `apps/kutuphane` `BelgeIzi` (tür, tarih/sayı, sha256) | ALMA ama kalıp OAB "Evrak + sha256" modeline uyar |

**İskelette olmayanlar:** tutar yazıyla (Kütüphane'de yok; OYS'de olup olmadığı F0-6'da bakılır — doğrulanmadı), para
yardımcıları (`Decimal`, kuruş yuvarlama), docx üretimi, birlik antedi. Ön yüzde `formatPrice` sayıyı `Number`'a
çevirir: gösterim için yeterli; Ö: OAB'de toplam ön yüzde hesaplanmaz.

### 7.2 T2 seçenekleri iskelet açısından

| Seçenek | İskelete etkisi | Değerlendirme |
|---|---|---|
| (a) HTML → WeasyPrint PDF + ayrı docx şablonu | `shared/pdf.py` ve `--pdf-duman` aynen; docx yanına eklenir | PDF yolu kanıtlı, iki platformda bağımsız. Bedel: içerik iki yerde |
| (b) docx şablonu → PDF'i LibreOffice/Word'den | WeasyPrint kalır ama evrakta kullanılmaz; dış programa bağımlılık | Windows'ta LibreOffice garanti değil; Word otomasyonu ek bağımlılık ve kırılgan (doğrulanmadı). PDF'in varlığı kurulum ortamına bağlanır |
| (c) tek docx, PDF yalnız LibreOffice varsa | (b) gibi | Windows okulların çoğunda PDF yok demek olabilir (ölçülmedi) |

**Ö: ekleme noktası (en az müdahale).**
1. `shared/docx.py` — python-docx'e tek kapı (`shared/pdf.py`'nin eşi): belge dili `tr-TR`; büyük harf biçimi (`w:caps`)
   **kullanılmaz** (Word/LibreOffice dile göre çevirir ama metin her ortamda doğru kalsın diye veri `tr_upper`'dan gelir);
   yazı tipi adı verilir, gömülmez (Pardus'ta eşdeğer font yerine geçer — doğrulanmadı).
2. `shared/evrak.py` — "belge tanımı + bağlam → {pdf, docx}" cephesi. İçerik (cümleler, tablolar, imza blokları) **tek
   yerde Python'da** kurulur; HTML şablonu ve docx kurucusu yalnız düzeni taşır. Bu, (a)'nın iki şablon yükünü düzen
   katmanına indirir. Spike bunu sınar.
3. Şablonlar: `templates/documents/*.html` (PDF) + `templates/docx/` (gerekirse yer tutuculu Word şablonu).
4. İsteğe bağlı `shared/libreoffice.py` — yalnız (b)/(c) seçilirse: zaman aşımlı `soffice --headless --convert-to pdf`,
   kullanıcının LibreOffice profiline dokunmayan geçici profil dizini (doğrulanmadı).
5. Duman ve test: Ö: `--evrak-duman` (aynı bağlamdan docx üret → python-docx ile geri oku → Türkçe örnek metin ve "İ"),
   içerik eşdeğerliği testi (pypdf metni ↔ python-docx metni), `w:caps` yokluğu.
6. Sızıntı kapıları: `.docx` şablonları adıyla muaf; başka `.docx` depoda ve pakette yasak (§8.3).

Not: kullanıcı Word dosyasını düzenledikten sonra programın PDF'i o hâli yansıtmaz; PDF "programın taslağı" olarak
adlandırılmalı (ekran metni karar ister).

---

## 8. Kapılar ve araçlar

### 8.1 `scripts/gates.sh` adım adım

Her adım `docker compose run --rm -T` ile koşar; çıkış koduna **ek olarak** kapta `KAPI_OK_<ad>` nöbetçisi aranır (bu
makinede `compose run` çıkış kodunu zaman zaman yutuyor). `MSYS_NO_PATHCONV=1`.

| # | Adım | Servis / komut |
|---|---|---|
| 1 | **Depo sızıntısı (KVKK)** — en başta | host `git ls-files -z` → `.kd-depo-listesi.tmp`; kapta `python packaging/depo_sizintisi.py` |
| 2 | backend `pytest` | kapsam eşiği 75 (`apps`, `shared`, `katalog`) |
| 3 | `KD_YAVAS=1` ise: `pytest -m yavas` + `ag_katalogu_provasi.sh` | yalnız gecelik CI |
| 4-6 | `ruff check`, `ruff format --check`, `mypy` (strict) | backend |
| 7 | desktop + packaging `pytest` — **ayrı süreç** (günlük yapılandırmasını değiştirir) | `-w /repo` |
| 8-11 | desktop ve packaging için ruff + mypy | `backend/pyproject.toml` ile |
| 12 | `scripts/` ruff + format + mypy | |
| 13-15 | ön yüz `tsc --noEmit`, `eslint`, `prettier --check` | `frontend` |
| 16 | ön yüz lisans listesi | `on_yuz_paketleri.mjs` → `lisanslar.py npm-denetle` |
| 17 | `vitest --coverage` | JSON raporunda `success:true`, kapsam özeti üretilmiş, "does not meet" yok (82/82/78/55) |

**OAB:** 3. adım sökülür. Yavaş işaretli testlerin hepsi `apps/kutuphane` ve `katalog`'dadır; kalmayınca `-m yavas` hiç
test seçmez ve pytest büyük olasılıkla 5 koduyla çıkar (doğrulanmadı) — gecelik CI kırmızı olur.

### 8.2 Docker düzeni

`docker-compose.yml`: `backend` (`docker/backend.Dockerfile`, Python 3.12-slim + WeasyPrint sistem kitaplıkları + DejaVu,
`./backend:/app` ve `.:/repo`, `PYTHONPATH=/repo`, `KD_DEBUG=1`) ve `frontend` (`node:20-slim`). Port açılmaz;
`sleep infinity`. Host'a Python/Node kurulmaz. Compose kök olarak yazdığı için `backend/data/` ve önbellekler root
sahipli olabilir.

### 8.3 Sızıntı denetimleri

| | `packaging/depo_sizintisi.py` | `packaging/veri_sizintisi.py` |
|---|---|---|
| Ne | İzlenen dosyalar | Paket dizini + son arşivler (`.zip`, `.tar.gz`, `.deb`; yalnız üye adları) |
| Yol/uzantı | `.xls .xlsx .xlsm .csv .sqlite .sqlite3 .db .kdbak`; `backend/data/`, `data/raw/`, `media/` | aynı uzantı kümesi (eşitliği test sınar) + `-wal/-shm`, `guvenlik.json`, `yedekleme.json`, `surum.json` |
| İçerik | 11 haneli sayılarda **TCKN sağlaması** (yanlış pozitifi eler); kilit/özet dosyaları muaf | içerik okunmaz |
| Muafiyet | Sentetik e-Okul örnekleri **adıyla**, joker yok | adıyla |
| Çıktı | Yalnız konum; değer basılmaz | aynı |

**Ö: OAB eklemeleri.** `.kdbak` → `.odbak`; `.docx` ve `.ods` riskli uzantıya (şablonlar adıyla muaf); **IBAN taraması**
(TR + 24 hane, mod-97 sağlaması — TCKN deseninin eşi; bağışçı, taşımacı ve kiracı IBAN'ları kişisel veridir); sınıf
listesi muafiyeti çıkar (T5). Ö: `.pdf` için karar — banka özeti ve TEFBİS çıktısı PDF olarak da gelebilir; bugün
yalnız ikili sayılıp taranmıyor. Kütüphane'nin `.gitignore`'unda `*.csv` yoktu (depo kapısı yakalar ama önlemez); OAB'nin
mevcut `.gitignore`'u bunu zaten ekliyor.

### 8.4 Duman kipleri ve çıkış kodları

| Kip | Ne sınar | Kod |
|---|---|---|
| `--autotest` | Açılış zinciri + sağlık denetimi; **bugün katalogu da kaldırır** | 0 / 6 |
| `--pdf-duman [dosya]` | Şablon pakette, WeasyPrint DLL'leri, Türkçe + gömülü DejaVu | 8 |
| `--bagimlilik-duman` | `RUNTIME_MODULES` (+ Windows'ta `DESKTOP_RUNTIME_MODULES`) gerçekten içe aktarılır | 10 |
| `--dagitim-duman` | Pardus kurulu/taşınabilir ayrımı | 11 — ALMA |
| `--geri-yukle` | Yedekten geri yükleme | 9 |

Diğerleri: 1 beklenmedik, 2 zaten çalışıyor, 3 veritabanı bozuk, 4 şema yeni, 5 göç, 6 sunucu, 7 WebView2 yok.

### 8.5 `test-kurulum.sh` ve Debian 13

**Gözlem.** `test-kurulum.sh` `dist/cikti/*.deb`'i temiz `debian:11` ve `debian:12` kaplarında `kap-ici-test.sh` ile
sınar: `dpkg -i` → `apt_dene apt-get -f install` → dosya yerleşimi → lisans dosyaları (DEP-5, `paket-icerigi.txt`) →
`libreadline` ve Qt'nin yalnız GPL'li modülleri yok → Windows'a özgü pywebview dosyaları yok → `--bagimlilik-duman` →
`--pdf-duman` → `--dagitim-duman kurulu` → iki kez `--autotest` → `dpkg -r`. Paket bullseye kabında derlenir (glibc
2.31 tabanı). `apt_dene.sh` bullseye güvenlik deposunu tarihli arşive sabitler (Debian 11 LTS bitti, TB5).

**Debian 13 için gerekenler.**
1. `test-kurulum.sh` `SURUMLER=(11 12 13)`; `paketleme.yml` `linux-kurulum` matrisi `["11","12","13"]`.
2. CI "git" adımındaki `sources.list` koşulu: debian:13 de deb822 kullanır, koşul atlar (12'deki gibi).
3. `.deb` `Depends` satırı: Debian 13'te 64 bit zaman geçişiyle bazı kitaplıkların adı değişti (`libasound2` →
   `libasound2t64`, `libglib2.0-0` → `libglib2.0-0t64` gibi). amd64'te yeni paketlerin eski adı sanal olarak
   sağlaması beklenir; `apt-get -f install` çözer mi — **doğrulanmadı**, prova gösterecek.
4. PySide6 6.8.3'ün Pardus 25 / Debian 13 grafik yığınıyla açılması (tavan Pardus 21 içindi, alt sınır sorunu
   beklenmez) — doğrulanmadı.
5. `--dagitim-duman` adımı `kap-ici-test.sh`'ten çıkar.

### 8.6 CI iş akışları

| İş akışı | Tetik | İşler |
|---|---|---|
| `kapilar.yml` | push main, PR, gecelik, elle | backend imajı → `npm ci` → `gates.sh` |
| `paketleme.yml` | `v*` etiketi ve ilgili yollar | ön yüz derlemesi → Linux (`.deb` + `.tar.gz`) → temiz Debian provası (matris) → Windows (DLL kapanışı, PyInstaller, duman, Inno) → etiket ↔ `VERSION` kapısı → yayın: `veri_sizintisi` son paketlerde, SHA256SUMS, GitHub Release, R2 |
| `r2-yukle.yml` | elle | var olan Release'i R2'ye yükler (secret zorunlu) |

Yayın adımları kullanıcı onaylıdır (OAB altın kural 8).

### 8.7 Saha kabulü belgesi

`docs/saha-kabulu.md` (1.355 satır): işaretlenebilir protokol — Windows 11 uçtan uca + Pardus kısaltılmış zincir,
belgelerin yazıcı çıktısı çizelgesi, bulgu kaydı ve §26 "kaynak madde → protokol adımı" eşleme tablosu (NOTLAR W
maddeleri, çek-listesi, saha hazırlık hattı, teknik borç, F<n> ekleri). Eksiksizliğini `apps/kutuphane`'deki
`test_saha_kabulu_belgesi.py` sınar. Uydurma deneme verisi `scripts/deneme_verisi.py`'den. Ö: OAB F7'de aynı yapı
(protokol + eşleme testi + uydurma veri üreticisi) yeniden yazılır; bugün kopyalanmaz.

---

## 9. Pencere davranışı (T6)

### 9.1 Kütüphane'de tepsi nasıl bağlı (gözlem)

| Katman | Davranış |
|---|---|
| `window.WindowController.on_closing` | Çarpı `False` döndürür: tepsi varsa `hide()`, yoksa `minimize()`. Yalnız "Çık"tan sonra `True` |
| Windows oturum kapanışı | `.NET FormClosing` işleyicisi `WindowsShutDown`/`TaskManagerClosing`'de iptali geri alır |
| Çık yolları | tepsi menüsü, arayüzdeki Çık (`POST app/quit/`, görevli kipinde parola), kurucunun `.Kapat` olayı, Linux SIGTERM |
| Kapanış sırası (`main.serve` finally) | kancalar → katalog denetçisi → gün kapısı → katalog → yönetim sunucusu → **WAL checkpoint** → temiz kapanış işareti → kilit |
| Kurucu | `AppMutex` yok; `InitializeSetup/Uninstall` `.Kapat`'ı işaretler, 30 sn mutex bekler, olmazsa "tepsi simgesinden Çık" iletisi |

### 9.2 Kelebek Sınav'da çarpı = çık (gözlem)

`desktop/window.py::open_window` `closing` işleyicisi bağlamaz; çarpı pywebview penceresini kapatır, `webview.start`
döner, `main.serve`'in `finally`'si yalnız `server.stop()` çağırır. Tepsi, tek kopya kanalı, temiz kapanış işareti,
açık WAL checkpoint ve Linux SIGTERM köprüsü yok; ikinci açılış "zaten çalışıyor" hatasıyla biter. Linux'ta PyQt5.

### 9.3 OAB'de ne değişir (öneri)

**Kelebek'in davranışı, Kütüphane'nin kazanımlarıyla.**

| Yer | Değişiklik |
|---|---|
| `window.py` | `on_closing` kapanmayı iptal etmez (ya da işleyici bağlanmaz); `tray_available`, `ask_quit_in_spa`, `kd:cik-iste` gider. `show()` (ikinci açılışta öne getirme) ve `request_quit()` (kurucu olayı, arayüzdeki Çık) kalır. Oturum kapanışı geçişi gereksizleşir (iptal yok) — Ö: testle sabitlenip silinir |
| `main.py` | `start_tray`/`TrayActions`/`--tepside`/katalog/uyku sökülür; Linux'ta pencereden önce `qt_kurulum.hazirla()` (QT_API, QtWebEngineWidgets sırası, pencere simgesi) + SIGTERM köprüsü. Kapanış zinciri (gün kapısı → sunucu → WAL checkpoint → temiz kapanış işareti → kilit) **aynen kalır** |
| Qt | `setQuitOnLastWindowClosed`: pywebview son pencere kapanınca döngüyü kendisi bitirir (tray.py belgesi). Değer ve Pardus davranışı F1a'da elle doğrulanır |
| `instance_channel.py`, `lock.py` | Kalır: ikinci açılış pencereyi öne getirir, kurucu programı düzenli kapatır. İletiler "tepside" demez |
| `restore.py`, `restart_gate.py`, `.iss [Code]` | "Tepsideki simgeden Çık" → "Programı kapatıp yeniden deneyin" |
| `.iss` | `otobaslat`, `tepside` görevleri ve `gorev-kur.ps1` gider. Ö: `AppMutex` yine kullanılmaz (olay yolu WAL checkpoint'li düzenli kapanış sağlar) |
| Ön yüz | `cikis` modülü kalır (Linux'ta pencere süslemesi olmayan masaüstü — TB13 dersi; "yeniden başlat" ekranının "Programdan çık"ı); görevli parolası dalı gider |
| Kanıt | Birim: `on_closing` kapanmayı iptal etmez, `serve` sonrası checkpoint ve işaret yazılır. "Exe açılır, çarpıyla kapanır" F1a kapısında **elle** doğrulanır (CI pencereye tıklayamaz) — NOTLAR'a madde |

---

## 10. Devralınan kusurlar (`docs/teknik-borc.md`)

**OAB'ye:** *geçer* = iskeletle birlikte gelir · *geçmez* = ALMA'lık bölümde kalır · *farklı* = kavram geçer, OAB'de
başka biçim alır.

| TB | Konu | OAB'ye | Not | Öncelik |
|---|---|---|---|---|
| TB1 | Şube, üye türü, tarihler düz metin | farklı | Şifreleme kapsamı OAB modelinde yeniden yazılır (tutar, tarih, karar no düz; kişi adları, iletişim, IBAN şifreli?) — F0-8 §5 | yüksek (tasarım) |
| TB2 | Katalogda slowloris | geçmez | | — |
| TB3 | `synchronous=FULL` maliyeti | geçer | Yazma hacmi düşük; kalır. HDD ölçümü saha işi | düşük |
| TB5 | Debian 11 derleme tabanı | geçer | Bullseye ana deposu arşive taşınınca derleme 404 verir; Debian 13 provası eklenir | orta |
| TB6 | İmzasız exe + dinleyen port | geçer (yarısı) | Port kısmı düşer; SmartScreen kalır | düşük |
| TB7 | Her güncelleme yönetici ister | karar | Güvenlik duvarı gidince yönetici kurulum gerekçesi zayıflar (§11-1) | orta |
| TB8 | Anonimleştirilen bağlar yedeklerde | farklı | OAB saklama kuralları gelince aynı yedek düzeni | sonra |
| TB9 | Silme Yönetmeliği depoda yok | geçer | Ö: F0-1 korpusuna eklenir | orta |
| TB17 | Kurtarma anahtarı yenileme ele geçmiş anahtarı geçersiz kılmaz | geçer, **ağırlaşır** | T1 ile hesaplar dönemlik (§6.3-2) | **yüksek** |
| TB18 | "Olası aynı kişi" ad benzerliğiyle | geçer | Personel aktarımı ve ayrılış havuzu kalırsa birlikte gelir | düşük |
| TB19 | Kurulum bitmeden kip süreyle kapanmaz | farklı | Kip yerine oturum kilidi; karar yeniden | orta |
| TB20-TB22 | ISBN uç, Open Library, ISBN-10/barkod | geçmez | | — |
| TB23 | Yedekler eski parolayla açılır | geçer, **ağırlaşır** | TB17 ile aynı | **yüksek** |
| TB24 | Şifreleme öncesi düz metin | geçer | `enable()` boş tablo şartıyla kuramsal | düşük |
| TB25 | Okul ağı bilgisi depoya girmez | farklı | Ağ belgesi yok; Ö: kural "banka, IBAN, TEFBİS bilgisi depoya girmez"e genişler, IBAN taraması (§8.3) | orta |
| TB26 | Kardeş projede açık denetim bulguları | geçer (bilgi) | OAB kapalı hâli devralır; Kelebek'te açık | — |
| TB27 | PySide6 6.8.3 tavanı ve boyut | geçer | `.deb` ~180 MB; Pardus 21 desteği kararıyla bağlı | orta |
| TB28 | Lisans dizini — kararlı öncesi iki iş | geçer | MSYS2 kaynak arşivi, Qt bildirim metni; python-docx/lxml ile yeniden üretim | orta |
| TB29-TB35 | Etiket, Ağ Doktoru UAC, authorizer, son sınıf, kart no, görevli barkodu, dışa aktarım | geçmez | | — |
| TB36 | Büyük dökümlerde PDF süresi | farklı | Tek PDF kilidi; uzun gelir-gider dökümünde aynı soru. Ö: Excel asıl çalışma biçimi | düşük |
| TB37, TB38 | Profil yasağı taraması, istatistik dönemleri | geçmez | | — |
| TB39 | Bağı koparılan kayıt arşivdeki asılla eşleşir | farklı | OAB saklama tasarımında aynı sınır doğar | sonra |
| TB40 | Pardus paketi açık programı kapatmaz | geçer | Çarpı = çık ile olasılık düşer, ortadan kalkmaz | düşük |
| TB41, TB42 | Taşınabilir Windows'ta katalog, tepsi simgesi | geçmez | Logo dersi (elle çizilmiş 16/24/32) logo işine taşınır | — |
| *Kapanan* TB4 | Logo geçiciydi | farklı | OAB'nin de yeni logosu gerekir; geçici logo kimlik taramasında muafiyet ister | düşük |
| *Kapanan* TB13, TB14 | Tepsisiz Linux çıkış yolu; WAL checkpoint | geçer (kapalı hâliyle) | Çık düğmesi ve checkpoint korunmalı | — |
| *Kapanan* TB10-TB12, TB15, TB16 | Katalog soketi, waitress hataları, F0 kalıntıları, ayrılmış kişi | geçmez | | — |

### 10.1 İskelet incelemesinde görülen ek kusurlar (teknik borçta yok)

1. Kalıntı kalıbı `kutuphane[ _-]?defteri` "Kütüphane"yi kaçırır (§4.2).
2. §5.10-1 değişmez testleri `test_katalog_server.py`'de; katalogla birlikte silinirse "yalnız 127.0.0.1" kanıtı kaybolur.
3. Linux Qt kurulumu ve SIGTERM köprüsü `tray.py`'de; tepsiyle birlikte silinirse Pardus penceresi bozulur.
4. `--autotest` katalogu kaldırır; katalog gidince 6 koduyla düşer.
5. `gates.sh` yavaş dalı yavaş test kalmayınca kırmızı (doğrulanmadı).
6. `pyproject.toml` `katalog` test yolu ve kapsamı.
7. `test_bagimlilik_duman_gercek…` segno'yu adıyla sınar.
8. Kütüphane `.gitignore`'unda `*.csv` yok (OAB'ninkinde var); depo kapısında IBAN taraması yok. OAB `.gitignore`'u
   sentetik e-Okul örneğinin istisnasını taşımıyor.
9. Görev devri ekranı `apps/kutuphane` uçlarına bağlı.
10. Kip süreleri `LibraryPolicy`'den beslenir (yoksa varsayılan).
11. `Dockerfile` son satırı `0.0.0.0` dinleyen geliştirme komutu.
12. `oys-theme` saklama anahtarı (OYS kalıntısı).

### 10.2 F1a'da düzeltilmesi önerilenler

1. Kimlik kalıbı `k[uü]t[uü]phane[ _-]?defteri` + `kd` kelime sınırı (plan §1.4 ve test birlikte).
2. §5.10-1 testlerini `test_server.py`'ye taşı; `0.0.0.0` taramasını daralt; Dockerfile `CMD` satırını sil.
3. `desktop/qt_kurulum.py`'yi `tray.py`'den ayır, sonra tepsiyi sök.
4. `--autotest`'ten katalog adımını çıkar; `--dagitim-duman`'ı sök, 11'i "ayrılmış" bırak.
5. `gates.sh`, `kapilar.yml`, `pyproject.toml`'dan yavaş/katalog dallarını çıkar.
6. Bağımlılık zinciri: segno, pystray, six çıkar (bütün halkalar + lisans kümesi + `uret.sh`); python-docx T2 spike'ıyla.
7. `.gitignore` birleştirmesi (sentetik personel örneğinin adıyla istisnası, kapı geçici dosyası) ve sızıntı kapıları:
   `.odbak`, `*.docx` (şablon istisnası adıyla), IBAN taraması.
8. Görev devri kartını ve `library/handover` bağını sök (OAB devir-teslimi F4'te).
9. "Ağ servisi sunmaz" + "tek dış istek kapısı" cümlesini bütün kopyalara koy (§3.9).
10. Debian 13 provası (TB5); `Depends` t64 davranışını prova göstersin.
11. `VERSION` sıfırla; `THIRD_PARTY_LICENSES`'ı yeniden üret (TB28).

---

## 11. Açık sorular ve riskler

1. **Kurulum yetkisi.** Kütüphane'de yönetici kurulumunun (U4, TB7) ana gerekçesi güvenlik duvarı kuralıydı. OAB'de
   kural yok: Kelebek gibi `PrivilegesRequired=lowest` (BTR'siz güncelleme) mi, Program Files'ta yönetici kurulumu mu?
   Karar F0-8'de.
2. **T1 sınırları.** Rolün kriptografik olmadığı (§6.3-1) kullanıcıya açıkça söylenmeli. Dönemlik hesaplarda eski
   sarmalların yedek başlığında kalması (§6.3-2): seçenek (i)+(ii) mi, DEK döndürme mi, kalan risk mi?
3. **T5 ve öğrenci modeli.** `Student`, `ClassSection`, öğrenci ayrıştırıcıları F1a arındırmasında mı, F1b'de mi
   sökülür? Sınıf veli temsilcileri için şube bilgisi gerekir mi (OAB mevzuatından doğrulanmadı)?
4. **Boşta süre.** Görevli kipi yokken boşta süre dolunca kilit — varsayılan kaç dakika?
5. **T2.** python-docx'in PyInstaller'da veri dosyası ihtiyacı ve lxml'in Windows paket boyutu/lisans kümesi —
   doğrulanmadı. Pardus'ta Times New Roman yerine geçen font, resmî yazı biçimi açısından yeterli mi (yönetmelikten
   doğrulanmadı)?
6. **Birlik antedi.** Okul antedi (`letterhead.py`) birlik yazılarına uyar mı, yoksa ikinci antet mi?
7. **Debian 13.** t64 ad değişikliği ve Qt 6.8.3 — prova sonucu bekleniyor.
8. **Ön yüz kapsam eşiği.** 159 kütüphane dosyası (testleriyle) sökülünce 82/78/55 eşiğinin tutup tutmadığı bilinmiyor;
   F1a kapısında görülür.
9. **Ham kopya commit'i kırmızı.** Ara commit kapısız mı sayılacak, yoksa dört bağ F1a-1'de mi kesilecek (§2.12-4)?
10. **Saklama ve görev devri altyapısı.** Kütüphane'nin saklama tetiği, `pre-anonim` yedeği ve E18 görev devri notu OAB'de
    F4'e (dönem kapanışı, devir-teslim) kalıp olarak bekler; iskelet onları sökülmüş devralır.
11. **Logo ve site.** Yeni logo (TB4 dersi) ve okulapp.org alanı (`od` paleti, `od-release.json`) — site ortak yayın
    alanıdır, yalnız kendi alanına ve kullanıcı onayıyla.
12. **Lisans üretimi.** `uret.sh` Docker ve ağ ister; F1a kapısının bir adımı ağ bağımlıdır.
13. **README ve köken.** Herkese açık README'de "Kütüphane Defteri'nden türedi" yazılırsa kimlik taramasına takılır;
    yazılmaması ya da muafiyet kullanıcı kararı.
