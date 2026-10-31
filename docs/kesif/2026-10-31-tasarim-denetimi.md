# Tasarım denetimi — 31.10.2026

> [`../tasarim/2026-10-31-genel-tasarim.md`](../tasarim/2026-10-31-genel-tasarim.md) taslağının (v1) yedi mercekten
> bağımsız eleştirisi (F0-9). Denetçiler belgeyi yazanlardan ayrıdır; her bulgu yazıldığı sırada kaynağa (korpus,
> Kütüphane Defteri ve OYS kaynak kodu, saha notu, genel OAB seti) karşı sınandı. Çürütülen adaylar yazılmadı, yalnız
> sayıldı. Bulguların tasarıma işlenişi §İşleniş'tedir.

Önem dağılımı: yüksek 41 · orta 62 · düşük 26 · toplam 129.

| Mercek | Bulgu | Yüksek | Orta | Düşük | Çürütülen aday |
|---|---|---|---|---|---|
| GA · Güvenlik, ağ ve mimari | 24 | 7 | 13 | 4 | 9 |
| KM · KVKK ve hukuki konum | 18 | 5 | 7 | 6 | 13 |
| MA · Mevzuat atıfları I — kural paketi ve testler | 18 | 6 | 9 | 3 | 17 |
| MB · Mevzuat atıfları II — veri modeli, akışlar, aktarım, evrak | 15 | 7 | 7 | 1 | 24 |
| UY · Uygulanabilirlik | 20 | 7 | 7 | 6 | 12 |
| SU · Saha ve kullanıcı deneyimi | 16 | 6 | 7 | 3 | 7 |
| EK · Eksiklik ve tutarlılık | 18 | 3 | 12 | 3 | 19 |
| **Toplam** | **129** | **41** | **62** | **26** | **101** |

**Etiketler.** DOĞRU = bulgu tamamen doğrulandı · KISMEN = bir kısmı doğrulandı (hangisi olduğu "Doğrulama"da).
**Önem.** yüksek = mevzuata aykırılık, veri kaybı, KVKK ihlali, güvenlik açığı ya da F1'i bozacak hata · orta = bölgesel
yanlış ya da eksik · düşük = netlik, tutarlılık, biçim.

---
## Güvenlik, ağ ve mimari (24)

*Kaynak kısaltmaları: "tasarım" = `docs/tasarim/2026-10-31-genel-tasarim.md`; "iskelet" = Kütüphane Defteri `origin/main` 9a3829d (`kutuphane-main/` çıkarımı); "envanter" = `docs/kesif/2026-10-31-iskelet-envanteri.md`; "BSG" = `docs/mevzuat/meb-bilgi-ve-sistem-guvenligi-yonergesi.md`.*

### GA-1 · DOĞRU · yüksek · §5.3 (satır 842-844), TK8 (satır 101), §4.3 tehdit 18 (satır 408), §4.5 (satır 586-587)

**Sorun.** Tasarım `Attachment` ve `GeneratedDocument` dosyalarını (karar defteri sayfa fotoğrafı, ilan kanıtı, pay dekontu, kantin belgesi taraması, üretilen bütün PDF/DOCX/XLSX) diskte ayrı dosya olarak tutuyor. Yedek düzeni ise aileden olduğu gibi alınıyor ve aile yedeği **yalnız SQLite görüntüsüdür**. Günlük yedek, `pre-*` yedekleri, kullanıcının indirdiği `.odbak` ve USB'ye alınan dış yedek bu dosyaları taşımaz. Sonuç: disk arızasında (tehdit 18) ve "yeni bilgisayara taşıma" akışında (§4.5: kurulum → `.odbak` geri yükleme) bütün ekler ve üretilmiş evrak kaybolur; veritabanındaki satırlar var olmayan dosyaları gösterir. Yıl sonu arşiv paketi (§8.5) yalnız kapanmış dönemi kapsar ve geri yüklenemez.

**Doğrulama.** İskelet `desktop/backup.py:3-7`: "Dosya kopyalama YAPILMAZ … `Connection.backup()` ise SQLite'ın kendi çevrimiçi yedek API'sini kullanır"; `backup.py:92` `database_snapshot`, indirme yedeği de aynı işlevle (`apps/okul/services/encrypted_backup.py:20-35`). İskelette ek dosyası saklayan ve şifreleyen bir yapı yok (`MEDIA_ROOT` yalnız `config/settings.py:189`'da tanımlı, kullanan yok). Tasarım:842 "dosyaları … diskte şifreli durur"; TK8 (tasarım:101) yedeği "X25519 + AES-256-GCM şifreli yedek (`Connection.backup()`)" diye aileden aynen alıyor; tehdit 18 (tasarım:408) karşılık olarak "günlük yedek, dış (USB) yedek" sayıyor; §4.5 (tasarım:586-587) taşımayı yalnız `.odbak` ile tarif ediyor. Belgede dosyaların yedeğe girdiğini söyleyen bir cümle yok (grep: "media", "yedek" + "ek").

**Düzeltme.** §4.4.4'e ve TK8'e yedek kapsamı yazılmalı: `.odbak` kabı, veritabanı görüntüsüne ek olarak şifreli dosya deposunu (dosyalar zaten DEK'ten türeyen anahtarla şifreli; kap içinde ikinci kez AES-GCM) taşır; kap biçimi sürümlenir (`ODBAK\x03`) ve geri yükleme dosya deposunu da takas eder. Kapsam boyutu büyürse ayrım açıkça yazılır: "günlük yedek yalnız veritabanı, haftalık/dış yedek tam". Tehdit 18 ve §4.5 taşıma kontrol listesi buna göre düzeltilir; F1 kapısındaki "şifreli yedek → geri yükleme" uçtan uca adımına "ekli bir kayıt geri yüklemeden sonra açılır" testi eklenir. §12.B'de `backup.py`, `backup_crypto.py`, `encrypted_backup.py`, `backup_restore.py` satırlarına bu değişiklik işlenir.

### GA-2 · DOĞRU · yüksek · §5.3 (satır 842-844), TK12 (satır 105), §4.4.4 (satır 506-507, 521-528), §12.B (satır 2504, 2578-2586)

**Sorun.** Dosya düzeyi şifreleme ailede olmayan yeni bir kriptografik bileşen, ama tasarımda tanımsız ve DEK yenilemesine dahil değil. (1) TK12 ve §4.4.4 DEK yenilemesinde yeniden şifrelenecekleri "şifreli alanlar, kör indeksler, parmak izi, yedek anahtar çifti ve denetim izi mührü" diye sayıyor; dosyalar listede yok. Yenilemeden sonra dosya anahtarı yeni DEK'ten türer, eski dosyalar açılamaz: veri kaybı. (2) §5.3 dosya anahtarının HKDF bilgi dizgesini "§4 kimlik sabitlerinde" diye gösteriyor, §2.3'te böyle bir satır yok; geçici açık kopyanın temizlenmesini "§4'te" diye gösteriyor, §4'te yok. (3) §4.4.4 DEK'ten türeyenleri sayarken dosya anahtarını anmıyor. (4) TK8 güvenlik çekirdeğini "aileden aynen" sayıyor, `shared/crypto.py` §12.B'de "yalnız kimlik dizgeleri; ilkel işlevler aynen" diye AYNEN; §12.B YENİ tablosunda dosya şifrelemesi modülü yok.

**Doğrulama.** Tasarım:105 ve :524 sayımı (dosya yok); tasarım:842-844 "DEK'ten HKDF ile türeyen dosya anahtarıyla … (bilgi dizgesi §4 kimlik sabitlerinde) … geçici kopyanın temizlenmesi §4'tedir"; grep "HKDF" yalnız 109, 146, 147, 149, 507, 814, 842'de geçiyor, dosya anahtarı dizgesi yok; tasarım:506-507 "Kör indeks, yedek anahtar çifti ve denetim izi mührü DEK'ten HKDF ile türer". İskelet `shared/crypto.py` yalnız alan şifrelemesi, sarmal ve kör indeks sağlar; ne orada ne `apps/okul` içinde dosya şifreleyen bir işlev var; Kütüphane `teknik-borc.md` TB17 (F11 değerlendirmesi, madde 2) DEK döndürmede "veri dizinindeki … defter yeniden hesaplanmalı … yoksa güvence sessizce düşerdi" diye aynı türden bir DB dışı kalemi ayrıca saymıştı.

**Düzeltme.** §4.4.4'e "Dosya anahtarı" maddesi: `HKDF(DEK, "od-dosya/v1")`, AES-256-GCM, dosya başına rastgele nonce, `Attachment.id` AAD; §2.3.1'e bilgi dizgesi satırı. TK12 ve §4.4.4 yenileme sırasına "dosya deposu yeni anahtarla yeniden yazılır (önce yeni adla, işlem tamamlanınca eskiler silinir; `gecis` yarıda kalırsa iki küme de durur)" adımı eklenir. Açık kopya kuralı §4'e yazılır: indirme yanıtı bellekten akar, sunucu tarafında geçici dosya bırakılmaz, yanıt `Cache-Control: no-store` taşır. §12.B YENİ tablosuna `shared/dosya_sifreleme.py` (+ testleri), F1b; TK8'in "aileden aynen" ifadesi "aile + dosya şifrelemesi (yeni)" olarak düzeltilir.

### GA-3 · DOĞRU · yüksek · §12.B UYARLA (satır 2528, 2553), §4.4.2 (satır 466), §4.4.4 (satır 515-518)

**Sorun.** Rol matrisi geri yüklemeyi yalnız `yonetici`ye veriyor. Ama tasarım `--geri-yukle` konsol akışını "`--hesap` + parola ya da kurtarma anahtarı" ile açıyor ve geri yükleme çekirdeği aile kuralı gereği veritabanına hiç dokunmuyor; rol veritabanında olduğu için bu yolda rol **denetlenemez**. Muhasip, DK üyesi ya da başka bir hesap sahibi kendi parolasıyla Başlat menüsündeki "Yedekten Geri Yükle" kısayolundan bütün veritabanını 14 gün öncesine (ya da USB'deki herhangi bir yedeğe) geri sarabilir. Denetim izi de veritabanında olduğu için onunla birlikte geri sarılır; geri yükleme olayının kendisi yeni veritabanına yazılmaz. Böylece hem matris hem altın kural 4'ün izlenebilirliği teknik bilgi gerektirmeden aşılır.

**Doğrulama.** Tasarım:2528 "`restore.py` `--hesap` + parola ya da kurtarma anahtarı"; :2553 "`restore_backup`: `--parola` → `--hesap` + parola"; :516 "(1) güncel `guvenlik.json` + seçilen hesabın parolası"; :466 "Güvenlik: kurtarma anahtarı, geri yükleme … | Y | — | — | — | — | — | —". İskelet `apps/okul/services/backup_restore.py:14-17` "VERİTABANINA HİÇ DOKUNULMAZ … bu modülde ORM importu ve sorgusu yoktur"; `desktop/restore.py:14-15` kurulum Başlat menüsüne "Yedekten Geri Yükle" kısayolu koyar. Akış Django ara katmanından geçmez, `RolMiddleware` devreye girmez.

**Düzeltme.** §4.4.4'e kural: konsol geri yüklemesi yalnız **kurtarma anahtarıyla** ya da yedeğin içinden çözülen `Hesap` tablosunda rolü `yonetici` olan hesabın parolasıyla yapılır (çözüm bellekte, geçici SQLite bağlantısıyla `Hesap` satırı okunup rol denetlenir; değilse kenara alma yapılmadan durur). Geri yüklemeden sonra ilk açılışta yeni veritabanının denetim izine "geri yükleme: yedek adı, kenara alınan `db-onceki-<damga>` adı, kullanılan yol (hesap/kurtarma)" satırı yazılır ve panoda kalıcı kart çıkar; `db-onceki-*` dosyaları DK incelemesi bitmeden silinmez. §12.B `restore.py` ve `backup_restore.py` satırlarına bu iş, F1b kapısına "yonetici olmayan hesapla `--geri-yukle` reddedilir" testi eklenir.

### GA-4 · DOĞRU · yüksek · TK12 (satır 105), §4.4.4 (satır 526-528), §15.5 M-2 (satır 2774) ↔ §4.3 tehdit 10 (satır 400)

**Sorun.** Kurtarma anahtarının nerede saklanacağı çelişkili. Tehdit 10 "müdürlükte kapalı zarf" diyor; TK12, §4.4.4 ve M-2 ise her dönem basılan yeni anahtarın "devir dosyasına girdiğini", eskilerin de "devir dosyasında kapalı zarfta kaldığını" söylüyor. TK12 dönem devrinin (devir-teslim akışının) bir adımıdır; o akışta dosya eski YK'den yeni YK'ye (veli başkan ve muhasibe) teslim edilir. Kurtarma anahtarı DEK'i doğrudan verir ve yeni yönetici parolası belirletir (§4.4.3); yani program üzerindeki tam yetki her yıl veli kuruluna geçer ve bütün eski anahtarlar aynı dosyada birikir. TK12'nin gerekçesi ("eski kurulun bildiği hiçbir şey … yeni dönemin verisini ve yedeğini açmaz") bu durumda çöker: dosyayı bir yıl elinde tutan kurul, o dosyadaki bütün anahtarları görmüştür.

**Doğrulama.** Tasarım:400 "müdürlükte kapalı zarf"; :105 "yeni kurtarma anahtarı basılır, devir dosyasına girer"; :526-528 "devir dosyasına girer … Eski kurtarma anahtarı … devir dosyasında kapalı zarfta kalır"; :2774 aynı. Devir-teslimin tarafları: tasarım:765 `Handover.handed_by`, `received_by` "(→ `OabPerson`, çoğul: başkan, muhasip)", :1542 "eski baskan ve muhasip teslim eder, yeni baskan ve muhasip teslim alır". İskelet kurtarma anahtarı belgesi de "Zarfı müdürlükte, kilitli dolapta saklayın" diyor (`templates/documents/kurtarma_anahtari.html:71-72`).

**Düzeltme.** Tek kural yazılmalı: kurtarma anahtarı **okul müdürlüğünde** kilitli dolapta, mühürlü zarfta durur; birlik devir dosyasına yalnız "zarf müdürlükte, tarih, zarf no" kaydı (`HandoverItem kind=PROGRAM_HESABI`, anahtarın kendisi değil) girer. Eski anahtarlar müdürlükte "<tarih> öncesi yedekler için" etiketli ayrı zarflarda tutulur ve ilgili yedekler kalmayınca yok edilir (TB23 dili). TK12, §4.4.4, M-2 ve tehdit 10 bu cümleyle eşitlenir; kurtarma anahtarı belgesinin (E14) saklama talimatı aynı kuralı basar.

### GA-5 · DOĞRU · yüksek · §5.4 (satır 889-894), §7.8 (satır 1543), §2.3.2 (satır 186-189), §12.B (satır 2523)

**Sorun.** Dönem kapanışında silinen kişisel veri (veli listesi, bağışçı T.C. kimlik no, telefonlar) yedeklerde süresiz kalıyor; §5.4'teki "en çok 14 gün" iddiası yanlış. (1) Kapanıştan hemen önce alınan `pre-kapanis-<tarih>.odbak` veli listesinin tamamını taşır; ailenin rotasyonu yalnız `gunluk-` ve `pre-anonim-` öneklerini günle siler, tanımadığı öneke dokunmaz. `pre-kapanis` ve `pre-dek-yenileme` hiç silinmez. (2) `pre-migrate-` yedekleri günle değil "son 5" adetle tutulur; güncellemeler seyrekse kapanıştan önceki bir göç yedeği aylarca kalır. Ailede bu yedekler saklama tetiğinde ayrıca siliniyordu (ALMA'lık `apps/kutuphane/services/saklama.py`); tasarımın kapanış adımlarında karşılığı yok. (3) `pre-kapanis` öneki §2.3.2'deki yedek adları listesinde ve §12.B `backup.py` satırında yok. (4) Ailenin silme sonrası `wal_checkpoint(TRUNCATE)` adımı (TB24) kapanış silmeleri için yazılmamış.

**Doğrulama.** Tasarım:892-894 "Silinen veri günlük yedeklerde ve `pre-kapanis` yedeğinde en çok 14 gün kalır"; :1543 "`pre-kapanis-<tarih>.odbak` yedeği … Veli listesi, T.C. kimlik no'lar ve süresi dolan telefonlar silinir"; :186-189 önek listesinde `pre-kapanis-` yok; :2523 `backup.py` UYARLA satırında yalnız `pre-anonim` ve `pre-dek-yenileme`. İskelet `desktop/backup.py:375-380` döngü yalnız `(DAILY_PREFIX, PRE_ANONIM_PREFIX)`; :366-367 "adı desenlerimize uymayan her şey) DOKUNULMAZ"; :382-391 `pre-migrate` adetle; `docs/teknik-borc.md` TB24 "`services.saklama.wal_bosalt`".

**Düzeltme.** §5.4 "Çalışma biçimi" (5) şöyle yazılmalı: kapanış silmelerinden sonra (a) `wal_checkpoint(TRUNCATE)`; (b) tetik anından eski `pre-migrate-*` yedekleri silinir (ailenin `pre_migrate_before` + `remove_pre_migrate_named` kalıbı); (c) `pre-kapanis-*` ve `pre-dek-yenileme-*` günlük rotasyona (14 gün) eklenir; (d) kullanıcıya "bu tarihten önce dışarı aldığınız yedekler silinen veriyi taşır" kartı gösterilir. §2.3.2'ye `pre-kapanis-` öneki, §12.B `backup.py` satırına `rotate_backups` önek kümesinin genişlemesi işlenir; F4 kapısına "kapanıştan 15 gün sonra yedek klasöründe veli adı içeren yedek yok" testi eklenir.

### GA-6 · DOĞRU · yüksek · §4.4.2 (satır 468), §9.6 (satır 1885, 1898-1899), §5.2.8 (satır 763), §8.5 (satır 1681, 1688), §5.4 (satır 861, 879)

**Sorun.** Veli listesi, katılım cetveli (E08) ve davetiye teslim çizelgesi (E07) üzerinden hem rol kısıtını hem T5 silmesini aşıyor. (1) Matris "kişisel veri içeren dışa aktarım (veli listesi …)" işini yalnız `yonetici`ye veriyor. Ama §9.6 "kaydedilmiş belgeyi her okur rol basabilir" diyor ve E08 veli adı ile sınıfı taşıyan **xlsx** dâhil üretiliyor. DK üyesi ve müdür dahil her okur rol veli listesini Excel olarak alabilir. (2) `GeneratedDocument` dosyaları "üretilen evrak" sayılıp hiç silinmiyor ve arşiv paketinin `01-evrak/` bölümüne "dönemin bütün" dosyalarıyla giriyor. Veli adları dönem kapanışından sonra E08/E07 dosyalarında kalıcı olarak durur. Bu, T5'in "liste dönem kapanışında silinir" kararını ve §8.5'in "dışarıda kalanlar: veli listesi" cümlesini boşa çıkarır. §5.4 yalnız cetvelin "izini" (sha256) saklamaktan söz ediyor, dosyanın akıbetini söylemiyor.

**Doğrulama.** Tasarım:468 "Kişisel veri içeren dışa aktarım (veli listesi, kişi dökümü) | Y | — …"; :1885 "kaydedilmiş belgeyi her okur rol basabilir"; :1822 E08 biçimi "docx+pdf, xlsx"; :1899 E08 veri kaynağı "`ParentRoster` (veli adı + öğrencinin sınıfı)"; :1898 E07 "teslim çizelgesinde veli adı"; :763 "Aynı nesne için yeniden üretim yeni sürüm satırıdır; eski satır silinmez"; :861 "üretilen evrak … Silinmez, anonimleştirilmez"; :1681 "`01-evrak/` Dönemin bütün `GeneratedDocument` dosyaları"; :1688 "Dışarıda kalanlar: veli listesi"; :78 T5 "liste dönem kapanışında silinir".

**Düzeltme.** §5.4'e kural: veli adı taşıyan belgeler (E07 çizelgesi, adlı E08) `GeneratedDocument.personal_roster=True` işaretiyle üretilir. Dosyaları dönem kapanışında veli listesiyle birlikte silinir (`purged_at`, tür/tarih/sha256/satır sayısı kalır) ve arşiv paketine girmez; arşive boş satırlı E08 ya da yalnız sayı tablosu girer. §9.6'ya istisna: bu belgeleri yalnız `yonetici` ve `sekreter` basar/indirir, her indirme erişim günlüğüne düşer. Matrisin 468. satırına "adlı katılım cetveli ve teslim çizelgesi dahil" notu eklenir.

### GA-7 · DOĞRU · yüksek · TK16 (satır 109), §4.4.4 (satır 509-510), §5 giriş ve §5.1 (satır 594, 625), §5.3 (satır 822-840), §12.B (satır 2543, 2585)

**Sorun.** Güvenlik çekirdeğinin üç yeni modeli hiçbir yerde tanımlı değil, çünkü §4 ile §5 birbirine gönderiyor: `Hesap` ("alanları §5"), `DenetimIzi` ("model §5") ve "erişim günlüğü" (hiçbir yerde model yok). §5 ise "hesap ve denetim izi modelleri … mimaride (§4)" diyor. F1b'nin ana işi bu modeller ve kapısı onlara bağlı (her yazma denetim izinde, rol testleri). Ayrıca KVKK açısından iki boşluk var. (1) §5.3 şifreleme tablosunda `Hesap` (ad-soyad) ve `DenetimIzi` satırı yok. (2) TK16 "satırlar kaydın özetini taşır" diyor. "Özet" kayıt içeriğinin kopyası mı, HMAC özeti mi belirsiz. Kopyaysa denetim izi şifreli alanların düz kopyasını tutar, silinmez olduğu için de veli listesi, T.C. kimlik no ve telefon silmelerini (§5.4) etkisiz kılar. Arşiv paketine giren "denetim izi dökümü" de aynı veriyi dışarı taşır.

**Doğrulama.** Tasarım:109 "Öneri; model §5"; :509-510 "(`Hesap`, alanları §5)"; :594 "hesap ve denetim izi modelleri ile şifreleme çekirdeği mimaride (§4)"; :625 "Hesap modeli … ve ekleme-yalnız denetim izi §4'te tanımlanır"; :2543 "`Hesap`, `DenetimIzi` §5'te"; :2585 "(alanlar §5)". §5.3 tablosu (tasarım:822-840) bu iki modeli içermiyor. "Erişim günlüğü" tasarım:445, 847, 871, 1637, 1703'te geçiyor, model tanımı yok. :891 yalnız silme satırları için "kişisiz satır" diyor. :1682 arşivde "denetim izi dökümü". Envanter:533 `Hesap` için "ad-soyad şifreli" öngörmüştü.

**Düzeltme.** §5.1'e (ya da §4.4'e, tek yerde) üç model tablosu eklenmeli. (a) `Hesap`: `id`, `tanitici`, `role`, `person` → `OabPerson`, `membership` → `OrganMembership`, `opened_at/by`, `closed_at/by`, `password_set_at`, `reset_pending`, `display_name` (şifreli). (b) `DenetimIzi`: `seq` (tekil, artan), `at`, `account` (boş = sistem), `role`, `action`, `subject_type/id`, `before_state/after_state`, `record_mac` = HMAC(denetim anahtarı, kaydın kanonik düz değerleri) — **içerik kopyası tutulmaz**, `prev_mac`, `mac`. (c) `ErisimGunlugu`: zincir dışı, 2 yıl saklama (B-9). §5.3 tablosuna `Hesap.display_name` şifreli, `DenetimIzi` "kişisel içerik yok (yalnız MAC)" satırları eklenir. TK16 metni "özet = MAC" diye netleşir.

### GA-8 · DOĞRU · orta · TK16 (satır 109), §4.1 (satır 328-330), §4.2 adım 7-8 (satır 344-345)

**Sorun.** TK16'ya göre her yazma `DenetimIzi`'ne düşer ve satırlar `HKDF(DEK, "od-denetim-izi")` anahtarlı HMAC zinciriyle mühürlenir. §4.1 ise sistem işlerinin ("günlük yedek, göç, dönem kilidi denetimi") "sistem yazarıyla" denetim izine düştüğünü söylüyor. Bu işler program kilitliyken, DEK bellekte yokken koşar: günlük yedek ve göç açılışın 7. ve 8. adımıdır, kilit ekranından (adım 12) önce gelir; `od-gunluk` kilitliyken de saatte bir çalışır. Bu anlarda zincir anahtarı yoktur, yani yazıldığı gibi uygulanamaz. Üç kaçış yolu da riskli. Sistem satırını mühürsüz yazmak saldırgana sahte "bekleyen satır" ekleme kapısı açar; bir sonraki kilit açılışı onları mühürler. Yazmamak altın kural 4'ü deler. Göçü engellemek programı açılmaz kılar.

**Doğrulama.** Tasarım:109 "Her yazma `DenetimIzi`'ne … HMAC zinciriyle mühürlenir (anahtar `HKDF(DEK, …)`)"; :328-330 "Yazar bağlamı olmayan yazma reddedilir; sistem işleri (günlük yedek, göç, dönem kilidi denetimi) `sistem` yazarıyla düşer"; :344-345 adım 7 günlük yedek, adım 8 `migrate`; :349 adım 12 kilit ekranı. İskelet `shared/crypto.py:27-36`: anahtar "kilit açıldıktan sonra kilitlenene dek bellekte kalır", açılışta yoktur.

**Düzeltme.** TK16'ya ayrım yazılmalı: (a) kullanıcı yazmaları zincire DEK'le, anında mühürlenir; (b) DEK yokken yapılan sistem olayları ayrı bir `SistemOlayi` tablosuna mühürsüz düşer. Tür kümesi kapalıdır (yedek alındı, göç uygulandı, gün kapısı). Yalnız masaüstü süreci yazar ve veri kaydı değiştirmez. Kilit ilk açıldığında bu satırlar sırayla zincire **"mühürsüz geldi"** işaretiyle aktarılır ve DK ekranında ayrı gösterilir. Veri kaydını değiştiren sistem işi (dönem kilidi gibi) DEK yokken çalışmaz; ilk kilit açılışından sonra kuyruktan koşar. Göçler veri satırı yazmaz kuralı §14'e eklenir; veri göçü gerekirse ilk kilit açılışında koşar.

### GA-9 · DOĞRU · orta · §4.3 tehdit 7 (satır 397), TK16 (satır 109), §12.B (satır 2504)

**Sorun.** Tehdit 7'nin karşılığı, program dışından yapılan değişikliği tasarımın söylediği kadar görünür kılmıyor. (1) **Kuyruk kesme ve geri sarma:** HMAC zincirinin dışarıda bir çapası yok (kapanmış dönem için kâğıttaki özet dışında). Parolası olmayan biri son kaydı ve onun denetim izi satırlarını birlikte silebilir ya da `db.sqlite3`'ü dünkü kopyayla değiştirebilir. Zincir yine tutarlı görünür. (2) **Şifreli alanlar sanıldığı gibi değiştirilemez değil:** ailenin `from_db_value`'su çözülemeyen değeri hata vermeden düz metin olarak döndürür. SQLite'ta şifreli sütuna yazılan düz metin (karar metni, bağışçı adı, açıklama) programda meşru veri gibi görünür. Fernet bağlam taşımadığı için bir satırın token'ı başka satıra taşınabilir. OAB'de düz metin dönemi hiç olmadığı için bu hoşgörünün gerekçesi de yok. (3) Denetim yalnız DK'nin elle başlattığı "kayıt bütünlüğü denetimi"ne bağlı; açılışta ya da kilit açılışında kendiliğinden bir denetim yok.

**Doğrulama.** Tasarım:397 karşılıklar: "kayıt özeti + HMAC zinciri … DK'nin 'kayıt bütünlüğü denetimi'; kapanmış dönemin özet değerinin devir-teslim tutanağına basılması"; :109 "Zincir, program dışından … düz alan değiştirilmesini görünür kılar". İskelet `shared/crypto.py:340-354`: kilit açıkken `InvalidToken` ya da `UnicodeEncodeError` hâlinde `return cast("str | None", value)`, açıklaması "Türkçe harf içeren değer tanım gereği düz metindir". §12.B (tasarım:2504) `crypto.py`'yi "ilkel işlevler aynen" diye AYNEN alıyor; D29 (tasarım:2633) "OAB'de düz yedek hiç olmadı".

**Düzeltme.** (a) Zincir başı (son `seq` + kısa MAC) her kilit açılışında ekranda ve "son girişler" kartında gösterilir. Aylık bildirim (`MonthlyReport`) belgesine ve deftere geçirilecek aylık baskıya "kayıt no: N, zincir: XXXX-XXXX" satırı basılır; böylece çapa her ay kâğıda iner. Kilitle'de ve düzenli kapanışta `guvenlik.json`'a DEK'ten türeyen anahtarla mühürlü "son görülen seq" yazılır. Açılışta veritabanındaki `seq` bundan küçükse uyarı verilir; bu yalnız veritabanının geri sarılmasını yakalar. İki dosyanın birlikte geri sarılmasına karşı aylık kâğıt çapası kalır. (b) OAB'de `from_db_value` katı kipte çalışır: token olmayan dolu değer ve çözülemeyen token, `BozukAlan` işaretiyle döner ve panoya "bütünlük uyarısı" düşer. Hoşgörü yalnız `gecis` sürerken açılır. Bu değişiklik §12.B'de `crypto.py` UYARLA olarak yazılır. (c) `record_mac` kanonik düz değerler üzerinden hesaplanır (GA-7), token taşımasını da yakalar. Kilit açılışında son N satır kendiliğinden doğrulanır.

### GA-10 · DOĞRU · orta · §4.4.4 (satır 509-510), TK13 (satır 106), §4.3 (satır 389-408)

**Sorun.** Yetki kararı veritabanındaki düz `Hesap.rol` alanından okunuyor. Program bu alanı kullanmadan önce doğrulamıyor. Ortak Windows hesabını kullanabilen biri (M-8 önerisiyle bütün kurul üyeleri) taşınabilir bir SQLite aracıyla kendi hesabının rolünü `yonetici` yapabilir; bunun için parola bile gerekmez. Sonra kendi parolasıyla girer, program içinden yönetici olarak çalışır: başka hesapların parolasını sıfırlar ve onların adına işlem yapar, maskesiz T.C. kimlik no görür, veli listesini dışa aktarır. "Rol kriptografik değildir" sınırı okuma için yazılmış (tehdit 6). Bu düşük maliyetli yükseltme yolu tehdit tablosunda yok. Tehdit 7 yalnız "tutar, tarih, karar no" sayıyor ve zinciri ancak DK elle denetler.

**Doğrulama.** Tasarım:509-510 "Rol, ad-soyad, organ bağı ve açılış/kapanış tarihi veritabanındadır"; :106 "Rol kriptografik değildir: kaza önleyici + izlenebilirlik"; tehdit 4 (:394) yalnız program içi denemeyi, tehdit 6 (:396) program dışı okumayı, tehdit 7 (:397) düz mali alanları sayıyor; rol alanının değiştirilmesi hiçbir satırda yok. Envanter:533-534 "Giriş, `tanitici`'yla sarmal bulunur … DB'den rol okunur".

**Düzeltme.** §4.3'e satır eklenmeli: "Program dışından `Hesap` satırında rol ya da durum değiştirilir (parola gerekmez)". Karşılık: her `Hesap` satırı `HMAC(HKDF(DEK, "od-hesap/v1"), id‖rol‖durum‖açılış‖kapanış)` mührü taşır. Kilit açılışında DEK yüklendikten hemen sonra seçilen hesabın mührü doğrulanır; tutmazsa oturum açılmaz, olay `SistemOlayi`'na düşer. Kalan risk dürüstçe yazılır: parolasını bilen biri DEK'i dışarıda türetip mührü de yeniden hesaplayabilir (tehdit 6); mühür bu yolu kod yazmayı gerektiren bir işe çevirir.

### GA-11 · DOĞRU · orta · §4.4.4 (satır 508-518), §4.4.1 (satır 432-434), TK11 (satır 104)

**Sorun.** Hesap durumu iki ayrı depoda tutuluyor: `guvenlik.json` (`hesaplar[]`: tanıtıcı, tuz, sarmal) ve veritabanı (`Hesap`: rol, açılış, kapanış). İkisi arasındaki tutarlılık tanımsız. (1) **Geri yükleme:** aday (1) güncel `guvenlik.json` ile eski bir veritabanını eşler. Yedekten sonra kapatılan hesap veritabanında açık görünür ama sarmalı yoktur. Yedekten sonra açılan hesabın sarmalı vardır ama `Hesap` satırı yoktur; DEK'i açar, rolü bulunamaz. Programın bu durumda ne yapacağı (girişi reddetmek mi) yazılmamış. (2) **"Aynı işlemde kapanır":** üyelik düşünce hesap kapanışı hem SQLite işlemi hem `guvenlik.json` ile bütün `guvenlik-arsiv-*` dosyalarının yeniden yazılmasıdır. Dosya yazımı SQLite işlemine giremez; sıra ve yarıda kalma hâli tanımsız. (3) Rotasyon (TK12) sırasında da iki depo ayrı anlarda yazılır (GA-12).

**Doğrulama.** Tasarım:508-510 iki deponun alanları; :516 "(1) güncel `guvenlik.json` + seçilen hesabın parolası"; :433-434 "hesap **aynı işlemde** kapanır"; :104 "sarmalı `guvenlik.json`'dan ve bütün `guvenlik-arsiv-*` kopyalarından silinir". İskelet `backup_restore.py:14-17` (geri yükleme veritabanına dokunmaz) ve `app_password.py:291-297` (`_write_state` dosyayı .tmp → replace ile yazar, SQLite işleminin dışında).

**Düzeltme.** §4.4.4'e "iki depo kuralı" yazılmalı. (a) Yetki için ikisi birden gerekir: sarmal açılır **ve** `Hesap` satırı var, açık, mühürlüdür (GA-10); biri eksikse giriş reddedilir. (b) Kapanış sırası: önce veritabanı işlemi (`closed_at`), sonra `guvenlik.json` ve arşivler. Dosya adımı yarıda kalırsa açılışta "kapalı hesabın sarmalı duruyor" denetimi sarmalı siler (fikirdeş). (c) Geri yüklemeden sonraki ilk kilit açılışında iki depo karşılaştırılır; fark `yonetici`ye liste olarak gösterilir, veritabanında açık ama sarmalı olmayan hesaplar "parola yenilenmeli" durumuna düşer. F1b testleri bu üç hâli kapsar.

### GA-12 · DOĞRU · orta · TK12 (satır 105), §4.4.4 (satır 521-528), §4.4.5 (satır 540-542), §7.8 (satır 1540-1543)

**Sorun.** DEK yenileme akışında dört eksik var. (1) **Yarıda kalma:** sıra "tek SQLite işleminde … yeni DEK'le → `yonetici` sarmalı ve yeni kurtarma sarmalı" biçiminde. İşlem kaydedilip sarmallar yazılmadan kesinti olursa yeni DEK yalnız bellekteydi ve kaybolur. Açılışta eski sarmalla açılan DEK veritabanının parmak iziyle eşleşmez ve kilit açılmaz. Atıf yapılan "ailenin `resume_pending` deseni" bunu çözemez: o yalnız bellekteki tek anahtarla şifreleme geçişini yeniden koşar. (2) **Yeni dönem hesapları:** §7.8'de yeni kurulun hesapları görev bölümünde, yani dönem kapanışından ve dolayısıyla rotasyondan önce açılıyor. Rotasyonda bunların hepsi geçici parolaya düşer; metin yalnız "`mudur`, ikinci yönetici" diyor. (3) **Pencere:** genel kurul ile rotasyon arasında yeni dönemin yazdığı veri o arada eski DEK'le yedeklenir (`gunluk-*`, `pre-kapanis`, `pre-dek-yenileme`). Görevdeyken `guvenlik.json` kopyalamış eski üye bu yedekleri açar; "yeni dönemin verisini açmaz" iddiası bu pencere için doğru değil. (4) **MY değişimi:** en geniş yetkili hesap sahibinin ayrılışı DEK yenilemesini tetiklemiyor, yalnız kurtarma anahtarı yenileniyor. Bu, TB17'ye göre ele geçmiş anahtara karşı koruma sağlamaz.

**Doğrulama.** Tasarım:522-526 sıra; :525 "açık kalan öteki hesaplar (`mudur`, ikinci yönetici) geçici parolaya düşer"; :1540 "Yeni rol hesapları açılır, devir imzalanınca eski YK ve DK hesapları kapanır" ve :1543 kapanış sonra; :105 gerekçe "Eski kurulun bildiği hiçbir şey … yeni dönemin verisini ve yedeğini açmaz"; :542 "MY değişti | … kurtarma anahtarı yenilenir". İskelet `app_password.py:1069-1092` (`resume_pending` tek anahtar), `:1115-1120` ("Bu güvenlik dosyası bu veritabanına ait değil"); `teknik-borc.md` TB17 F11 değerlendirmesi "Yarıda kesilen bir döndürme … iki DEK'in karıştığı bir veritabanı bırakabileceği için … kendi geri yükleme provasını ister".

**Düzeltme.** §4.4.4 sırası şöyle düzeltilmeli. (a) Yeni DEK, veritabanı işleminden **önce** `yonetici` parolası ve yeni kurtarma anahtarıyla sarılıp `gecis: {tur: "DEK_YENILEME", yeni: {…sarmallar}, eski_parmak_izi, yeni_parmak_izi}` olarak `guvenlik.json`'a atomik yazılır. Açılışta veritabanı parmak izi hangisine eşitse o DEK kullanılır, geçiş tamamlanır ya da `gecis` silinir. (b) Rotasyon sayımına "bu dönemde açılmış organ hesapları" eklenir; ya da sıra değiştirilir: dönem kapanışı ve rotasyon tamamlanmadan yeni organ hesabı açılmaz (görev bölümü kaydı hesapsız yapılır). (c) TK12 gerekçesi "rotasyondan **sonraki** veri ve yedekler" diye daraltılır ve aradaki yedeklerin sayısı devir notuna yazılır. (d) §4.4.5 "MY değişti" satırına "DEK yenilenir (TK12 akışı, dönem kapanışı ön koşulu aranmaz)" eklenir. Akış için F4'te ayrı bir yarıda kesme provası (her adımdan sonra süreç öldürme) kapı maddesi olur.

### GA-13 · DOĞRU · orta · §4.2 Kapanış (satır 354-360), §4.5 Çarpı (satır 557), TK5 (satır 98)

**Sorun.** T6 ile çarpı programı onaysız kapatıyor. Tasarım bunun riskini yalnız "kaydedilmemiş form kaybı" olarak kabul ediyor. Uçuştaki sunucu işlemleri (banka özeti uygulama, dönem kapanışı ve arşiv paketi, DEK yenileme, canlı geri yükleme, dosya eki yazımı) da kesilir. Kapanış zinciri sunucuyu durdurup 2 sn bekliyor; WSGI iş parçacıkları süreçle ölüyor. SQLite işlemi geri alınır ama dosya + veritabanı + `guvenlik.json` arasında yayılan çok adımlı işler yarıda kalır. Üstelik temiz kapanış işareti bu durumda da yazılır. Bir sonraki açılışta T15'in "son oturumdaki kayıtları kontrol edin" kartı çıkmaz. Kütüphane'de çarpı programı gizlediği için bu yol pratikte yoktu.

**Doğrulama.** Tasarım:357 sıra "… yönetim sunucusu → WAL checkpoint → temiz kapanış işareti"; :359-360 "Kaydedilmemiş form kaybı kabul edilen risktir"; :557 "onay sorulmaz". İskelet `desktop/server.py:159-170` (`server.close()` + `thread.join(timeout=2.0)`, "thread daemon olduğu için süreç kapanışını bloklamaz"); `desktop/main.py:522` `serve` 0 döndürünce `write_marker_quietly` koşulsuz; `desktop/clean_shutdown.py:12-13` "işaret yalnız düzenli çıkışta … yeniden yazılır; süreç öldürülürse eksik kalır".

**Düzeltme.** §4.2'ye "uçuştaki iş" kuralı eklenmeli. `shared/bakim.py`'deki kapı uzun yazma işlerini sayar. Çarpıda iş sürüyorsa pywebview `closing` işleyicisi kapanışı bir kez erteler ve "İşlem bitiyor, program kendiliğinden kapanacak" iletisi gösterir; bu onay sorusu değil bekletmedir, T6 korunur. İş bitince kapanış sürer. Süreç yine de öldürülürse (zorla kapatma, elektrik) çok adımlı işler `gecis` günlüğüyle sürdürülür. Temiz kapanış işareti yalnız sayaç sıfırken yazılır. Birim testleri: "iş sürerken çarpı → iş tamamlanır, sonra çıkılır" ve "iş öldürüldü → işaret yok".

### GA-14 · DOĞRU · orta · TK7 (satır 100), §4.5 M-8 (satır 578-583), §2.3.1 (satır 133)

**Sorun.** TK7'nin kullanıcı başına kurulumu programın ikili dosyalarını (`%LOCALAPPDATA%\Programs\OAB Defteri`: exe, `_internal`, Python modülleri) programı çalıştıran Windows hesabına **yazılabilir** kılıyor. M-8'in önerdiği ortak "OAB" hesabını bütün kurul üyeleri kullanacağı için, bu hesaba girebilen herkes programı değiştirip başkalarının parolasını ve DEK'i toplayabilir. Kütüphane'nin yönetici kurulum gerekçelerinden biri de "kurulum dizini standart kullanıcıya salt okunur" idi. TK7 bunu anmıyor; riskler sütununda yalnız AppLocker var. Aynı güven sorunu güncelleme yolunda da var. İndirilen kurucu kullanıcı önbelleğinde bekliyor. Ayrıca `OD_UPDATE_REPOSITORY` "yalnız geliştirme ve test içindir" denmesine rağmen ailede paketli yapıda da okunuyor. Kullanıcı ortam değişkeni ayarlayabilen biri güncelleme denetimini kendi deposuna yönlendirebilir ve SHA-256 o deponun özetiyle doğrulanır.

**Doğrulama.** Tasarım:100 "`PrivilegesRequired=lowest` … varsayılan kullanıcı başına kurulum … Risk: AppLocker/SRP …"; :578 "yönetici yetkisi olmayan ayrı bir 'OAB' Windows hesabı"; :133 "`OD_UPDATE_REPOSITORY` yalnız geliştirme ve test içindir". İskelet `packaging/windows/kutuphane-defteri.iss:7-11` "PrivilegesRequired=admin … Kurulum dizini standart kullanıcıya SALT OKUNURDUR"; `apps/okul/services/updates.py:39` `GITHUB_REPOSITORY = os.environ.get("KD_UPDATE_REPOSITORY", …)` koşulsuz.

**Düzeltme.** TK7'nin gerekçe ve risk sütunlarına şu yazılmalı: "kullanıcı başına kurulumda ikili dosyalar o Windows hesabınca değiştirilebilir. M-8'deki ortak hesapla birlikte kullanılırsa program dosyalarının bütünlüğü korunmaz." M-1 varsayılanı yeniden tartılmalı: ortak OAB hesabı kullanılıyorsa yönetici kurulumu (Program Files) önerilir; kullanıcı başına kurulum yalnız MY'nin kişisel hesabında tek kullanıcı senaryosu için kalır. Kılavuz bu ayrımı yazar. `OD_UPDATE_REPOSITORY` paketli yapıda (`sys.frozen`) yok sayılır; bu bir testle sabitlenir (§12.B `updates.py` satırına eklenir).

### GA-15 · DOĞRU · orta · TK9 (satır 102), TK15 (satır 108), §4.3 tehdit 11 (satır 401), §4.5 (satır 579-581), §15.5 M-8 (satır 2778)

**Sorun.** BSG Yönergesi md. 7 seçici uygulanıyor. (1) TK9 kişisel hesapları md. 7/2 ve 7/4'e dayandırıyor. Oysa M-8'in ortak "OAB" Windows hesabının parolası bütün kurul üyelerince bilinir ve bu md. 7/2'ye ("şifresi'ni bir başkası ile paylaşmaz") ve md. 9/2-e'ye ("Şifreler herhangi bir kişi ile paylaşılmaz") aykırıdır. §4.5 sapma olarak yalnız md. 7/4'ü anıyor. (2) Hatalı giriş kilidi için yalnız md. 9/2-c'nin "kilitlenebilir" ifadesi alınmış. Md. 7/3'teki "üst üste birkaç kez hatalı giren kullanıcının, kullanıcı hesabı geçersiz kılınır … bir üst yetkilisi tarafından … tekrar aktif" hükmü hiç tartışılmıyor. Ailenin kalıcı kilit reddinin gerekçesi ("hesabı açacak bir yönetici yoktur") OAB'de geçerli değil, çünkü `yonetici` organ hesaplarının parolasını sıfırlayabiliyor. (3) TK15'teki "ilk girişte geçici parola değiştirilir" kuralının dayanağı md. 9/2 değil, md. 7/2'dir.

**Doğrulama.** BSG:156 (md. 7/2), :158 (md. 7/3), :160 (md. 7/4), :210 (md. 9/2-c), :216 (md. 9/2-e). Tasarım:102 "BSG Yön. md. 7/2, 7/4 (kullanıcı adı ve şifre paylaşılmaz …)"; :579-581 yalnız md. 7/4; :401 yalnız 9/2-c; :108 geçici parola kuralı md. 9/2'ye bağlı. İskelet `app_password.py:113-117` "kalıcı kilitlenme YOKTUR — çevrimdışı bir programda hesabı açacak bir yönetici yoktur".

**Düzeltme.** §4.5 sapma cümlesi "md. 7/2, 7/4 ve 9/2-e" diye tamamlanmalı ve ortak hesap parolasının kimde olduğu, ne zaman değiştirileceği (kurul değişiminde) kılavuz maddesi olmalı. Tehdit 11'e md. 7/3 tartışması eklenmeli. Öneri: organ hesaplarında 10 ardışık hatalı denemede hesap "askıda" olur ve `yonetici` sıfırlayarak açar (md. 7/3'ün karşılığı). `yonetici` hesabında kalıcı kilit olmaz; kurtarma anahtarı yolu kalır ve bu ayrım gerekçesiyle yazılır. Kademeli gecikme süreç geneli değil hesap başına sayılır. TK15'in dayanak sütunu md. 7/2'yi de gösterir.

### GA-16 · DOĞRU · orta · §4.4.4 (satır 508), §4.3 tehdit 9 (satır 399), TK15 (satır 108)

**Sorun.** Her hesap sarmalı, DEK'i tek başına veren bağımsız bir çevrimdışı saldırı hedefidir. Ailede iki sarmal vardı: yönetici parolası ve 160 bitlik kurtarma anahtarı. OAB'de dönemde yaklaşık 8 hesap var ve çoğu, parolayı bir yıl kullanacak velilerin 8 karakterlik parolası. Disk ya da bilgisayar çalınırsa (tehdit 9) `guvenlik.json` veritabanıyla aynı dizindedir. Şifreli alanların gücü o anda en zayıf hesap parolasının Argon2id'e karşı direncine iner. Tehdit 9 bu durumu "Fernet alan şifrelemesi" diye koruma sayıyor ve kalan risk olarak yalnız düz alanları gösteriyor.

**Doğrulama.** Tasarım:508 `hesaplar: [{id, tanitici, salt, sarmal}]` (hesap başına sarmal); :399 tehdit 9 karşılığı ve kalan riski; :108 "En az 8 karakter". İskelet `shared/crypto.py:145-158` (`unwrap_key`: her sarmal DEK'i doğrudan verir), `app_password.py:246-248` (`guvenlik.json` veri dizininde, `db.sqlite3`'ün yanında); envanter:562 yalnız giriş süresini tartışıyor.

**Düzeltme.** Tehdit 9'un kalan riski şöyle yazılmalı: "`guvenlik.json` aynı diskte; şifreli alanlar en zayıf hesap parolası kadar korunur. Tam koruma BitLocker." TK15'e organ hesapları için en az 12 karakterlik parola cümlesi önerisi ve sihirbazda güç göstergesi eklenmeli. Argon2id profili (64 MiB, t=3) parola sayısı arttığı için bir kademe yükseltilmeli ya da gerekçesiyle aynı bırakılmalı. Kapanan hesabın sarmalının silinmesi (TK11) bu yüzeyi daralttığı için ayrıca anılmalı.

### GA-17 · DOĞRU · orta · §4.4.3 (satır 487), §4.4.5 (satır 538, 542), §4.3 tehdit 10 ve 12 (satır 400, 402)

**Sorun.** "Kurtarma anahtarı + yeni yönetici parolası → AÇIK(hesap, rol)" geçişinde parolası yenilenecek hesap belirsiz. Var olan `yonetici` hesabının parolası yenilenirse, anahtarı kullanan kişi o hesabın sahibi adına çalışır. MY değişiminde "kurtarma anahtarıyla gelen" yeni MY, giden MY'nin hesabıyla iş yapmış olur; anahtar müdürlükte durduğu için müdür de MY'nin hesabını devralabilir. Tehdit 12 yönetici sıfırlaması için "sahibine ilk girişte bildirim" öngörüyor; kurtarma yolunda böyle bir bildirim de, ayrı bir denetim izi olayı da yok.

**Doğrulama.** Tasarım:487 geçiş; :538 "kurtarma anahtarı + yeni parola"; :542 "MY değişti | … | Giden ya da kurtarma anahtarıyla gelen"; :402 tehdit 12 yalnız "`yonetici` başka bir hesabın parolasını sıfırlayıp" durumu. İskelet `app_password.py:1024-1046` `unlock_with_recovery`, tek hesaplı şemada "parola" bölümünü yeniden yazar.

**Düzeltme.** §4.4.3'e kural yazılmalı. Kurtarma anahtarıyla açılışta kullanıcı ya bir `yonetici` hesabının parolasını yeniler ya da (MY değişimi) **yeni** bir `yonetici` hesabı açar. Her iki durumda olay denetim izine "kurtarma anahtarıyla açıldı (hangi hesap)" diye ayrı türle düşer. Parolası yenilenen hesabın sahibine, tehdit 12'deki gibi ilk girişinde bildirim gösterilir. Tehdit 10'un karşılık sütununa bu iki madde eklenir.

### GA-18 · DOĞRU · orta · TK13 (satır 106), §4.4.2 (satır 441-446, 472-481), §9.6 (satır 1885), §14 F1b kapısı (satır 2681)

**Sorun.** TK13 rol izinlerini "uç + yöntem matrisi" ve "URL desenlerini dolaşan koruma testi" ile tanımlıyor. §4.4.2'deki matris ise modül düzeyinde ve kısmi yetkilerle dolu: müdür M3'te yalnız iki yazıyı, M6'da yalnız talebi yazar (¹ ²); M11'de dönem kilidi ve hesap kapanışı yalnız `yonetici`nindir (⁶); maskesiz okuma yalnız `yonetici`nindir; kapanmış dönem her rolde salt okurdur; rol-özel işaretler §7'de. Bu kısıtların hangisinin uçta, hangisinin serviste denetleneceği yazılmamış. URL dolaşan test yalnız uç düzeyini kanıtlar; F1b kapısındaki "müdür yalnız kendi yazılarına yazar" maddesini sınayacak bir test biçimi tanımlı değil. Ailenin izin listesinde ayrıca "parametre" düzeyi vardı (`govdede_yok`, `yalniz_sorgu`); TK13 bunu anmıyor.

**Doğrulama.** Tasarım:106 "Sunucu tarafında uç + yöntem matrisi (`rol_izinleri.py`) … URL desenlerini dolaşan koruma testi"; :444-445 "bu matris modül düzeyindedir"; :472-481 dipnotlar; :1885 "`mudur` yalnız kendi yazılarını (E25, E35, yeni okulda E05) üretir"; :2681 F1b kapısı. İskelet `apps/okul/kip_izinleri.py:14-41` "Kural düzeyi: uç + yöntem (+ parametre)".

**Düzeltme.** §4.4.2'ye iki katman yazılmalı. (a) **Uç katmanı** (`rol_izinleri.py`): kısmi yetkiler ayrı uçlarla verilir (ör. `expense-files/<id>/request/` yalnız `mudur` ve `yonetici`; `terms/<id>/close/` yalnız `yonetici`). Parametre denetçisi aileden alınır. (b) **Servis katmanı**: kapanmış dönem, maskesiz okuma, rol-özel işaretler `servis.yetki(rol, eylem, kayıt)` tek kapısından geçer. F1b'ye her dipnot için birer servis testi ve "matristeki her (rol, satır, Y) hücresi için en az bir uç" anlık görüntü testi eklenir.

### GA-19 · DOĞRU · orta · §12.B AYNEN (satır 2505-2506), §2.3.3 (satır 207)

**Sorun.** AYNEN sınıfına alınan iki güvenlik dosyası T1 ile çelişen ve kütüphaneye özgü metin taşıyor. AYNEN "yalnız kimlik sabitleri çevrilir" demek olduğu için bu metinler değişmeden gelir. Kalıntı taraması da onları yakalamaz. (1) Kurtarma anahtarı belgesi (`kurtarma_anahtari.html`) "Yönetici parolası en az iki görevlendirilmiş kişide bulunsun" diye öğütlüyor; bu, kişisel hesap kararına (T1, TK9) ve BSG md. 7/2, 9/2-e'ye aykırı. Aynı belgede "okulun kütüphane işlerini yürüttüğü yerel araç", "öğrenci … okul numaraları", "kütüphane masasında" ifadeleri var. (2) `lock_middleware.py`'nin 423 iletisi "Kayıtlar yönetici parolasıyla kilitli. Devam etmek için yönetici parolasını girin" diyor; OAB'de her kullanıcı kendi hesabıyla açar. §2.3.3 yalın "kütüphane" sözcüğünü bilerek taramıyor.

**Doğrulama.** Tasarım:2505 `lock_middleware.py`, `recovery_key_document.py` AYNEN; :2506 `documents/kurtarma_anahtari.html` AYNEN; :207 "Taranmaz: yalın 'kütüphane' …". İskelet `templates/documents/kurtarma_anahtari.html:40, 61-65, 73-74, 78`; `apps/okul/lock_middleware.py:113`.

**Düzeltme.** Bu iki dosya §12.B'de UYARLA'ya alınmalı (F1b). Kurtarma anahtarı belgesinin metni OAB'ye göre yeniden yazılır: amacı, saklama yeri (GA-4: müdürlük), "parola paylaşılmaz; her kişi kendi hesabıyla" maddesi, dönemlik yenileme ve eski anahtarın akıbeti. Kilit iletisi "Kayıtlar kilitli. Hesabınızı seçip parolanızla açın" olur. F1a-2'deki elle "alan kalıntısı" listesine şu üç dosya adıyla eklenir: `kurtarma_anahtari.html`, `lock_middleware.py`, `recovery_key_document.py`.

### GA-20 · KISMEN · orta · §4.5 Hesap ve bilgisayar (satır 571-587), §2.3.1 Veri dizini (satır 134)

**Sorun.** Tasarımın erişim sınırı tartışması tamamen Windows'a göre yazılmış ("veri tek Windows hesabında durur"). Linux için veri, günlük ve önbellek dizinlerinin izinleri hiç anılmıyor. Aile bu dizinleri varsayılan umask'la oluşturuyor ve yalnız kanal soketini 0600 yapıyor. Ev dizini başka kullanıcılara açık bir Pardus kurulumunda öteki yerel hesaplar `db.sqlite3`'teki düz alanları (tutar, IBAN, sınıf), `guvenlik.json`'u (GA-16 çevrimdışı saldırısı) ve yedekleri okuyabilir. Okul bilgisayarlarında birden çok yerel hesap olağandır.

**Doğrulama.** Doğrulanan kısım: iskelet `desktop/paths.py:78-81` `directory.mkdir(parents=True, exist_ok=True)` (mod verilmiyor); kaynakta tek `chmod` `desktop/instance_channel.py:190` (`0o600`, soket). Tasarım:575-577 ve :134 yalnız yerleşimi veriyor, izin kuralı yok. Doğrulanamayan kısım: Pardus 21/23/25'in yeni kullanıcı ev dizini için varsayılan izni bu çalışmada denetlenmedi; risk o değere bağlıdır.

**Düzeltme.** §4.5'e Linux maddesi eklenmeli. Program açılışta `os.umask(0o077)` uygular. Veri, günlük, önbellek ve yedek dizinlerini 0700 oluşturur, var olanları 0700'e çeker; `guvenlik.json`, `yedekleme.json` ve `.odbak` 0600 yazılır. `.deb` `postinst` kullanıcı dizinine dokunmaz. Test: Linux'ta açılıştan sonra dizin ve dosya kipleri. Kılavuza "Pardus'ta programı kendi kullanıcı hesabınızda çalıştırın" notu girer.

### GA-21 · DOĞRU · düşük · §4.1 Değişmezler (satır 317-319), §4.3 tehdit 2 (satır 392), §12.B UYARLA settings.py (satır 2541)

**Sorun.** §4.1 "Paketli yapıda `ALLOWED_HOSTS` yalnız `127.0.0.1` ve `localhost`; `backend` adı yalnız `OD_SESSION_TOKEN` boşken eklenir" kuralını "testle kilitlenir" başlığı altında, var olan bir değişmez gibi yazıyor. İskelette bu koşul yok: `backend` her zaman listede ve kilitleyen test de yok. Kütüphane tasarımı bunu önceki denetimin GA-13 bulgusuyla yazmış ama kod uygulanmamış. §12.B'nin `settings.py` UYARLA satırında bu değişiklik yok. TK1'in "haritada olmayan iyileştirme yapılmaz" kuralıyla birlikte okununca değişiklik yapılamaz hâle geliyor. Tehdit 2 ise karşılığını bu kurala dayandırıyor.

**Doğrulama.** İskelet `backend/config/settings.py:58` `ALLOWED_HOSTS = ["127.0.0.1", "localhost", "backend"]` (koşulsuz); test dizinlerinde yalnız `desktop/tests/conftest.py:65` ayar geçersiz kılması var. Kütüphane `docs/tasarim/2026-09-21-genel-tasarim.md:361` koşulu "(GA-13)" diye anıyor. Tasarım:317-319, :392, :2541 (satırda `ALLOWED_HOSTS` yok), :94 TK1.

**Düzeltme.** §12.B `settings.py` satırına "`ALLOWED_HOSTS` koşullu (`OD_SESSION_TOKEN` doluysa `backend` yok) + test" eklenmeli. §13.A'ya "D: aile tasarımında yazılı, kodda uygulanmamış GA-13" satırı açılmalı (F1a-2). §4.1'deki ifade, iş yapılana dek "yapılacak" diye işaretlenmeli.

### GA-22 · KISMEN · düşük · §4.1 (satır 320), TK4 (satır 97), §4.3 tehdit 16 (satır 406)

**Sorun.** "Dış bağlantı yalnız `updates.py`'den çıkar" değişmezinin iki açığı var. (1) PDF hattı WeasyPrint'i `url_fetcher` vermeden çağırıyor. Belgedeki ya da CSS'teki her `http(s)` adresi kütüphanenin kendi istemcisiyle indirilir. Koruma testi yalnız proje kodunun ağ modülü içe aktarmalarını taradığı için bunu görmez. Yeni evrak hattı (`shared/evrak.py`) dış kaynaklı metni (banka açıklaması, e-Okul adları) HTML'e çevirdiğinde bir kaçış hatası dış istek doğurabilir. (2) Tehdit 16 "yalnız `github.com`/`api.github.com`" diyor. Kod yalnız ilk adresi denetliyor; `urlopen` yönlendirmeleri hedef denetimi yapmadan izliyor.

**Doğrulama.** Doğrulanan: iskelet `backend/shared/pdf.py:51` `HTML(string=html).write_pdf(font_config=…)` (url_fetcher yok); `apps/okul/tests/test_dis_istek_kapilari.py:9-11` tarama yalnız proje kaynağında ağ istemcisi "import eden her modül"e bakıyor; `apps/okul/services/updates.py:185-188` `urlopen(…)` ve `:220-226` `_safe_release_url` yalnız JSON'daki adresi denetliyor. Doğrulanmayan: GitHub'ın kurucu indirmesini hangi alana yönlendirdiği bu çalışmada ağdan denetlenmedi; bu yüzden ikinci madde ifade düzeltmesidir.

**Düzeltme.** `shared/pdf.py` ve `shared/evrak.py` yalnız `data:` ve paket içi `file:` kabul eden bir `url_fetcher` verir; öteki şemalarda istisna yükselir. Test: `<img src="http://…">` içeren belge PDF'e çevrilirken ağ tuzağı tetiklenmez. Tehdit 16 metni şöyle düzeltilir: "ilk istek yalnız github.com/api.github.com'a; yönlendirme izlenir; güven çapası SHA-256'dır." Gerekirse yönlendirme hedefi için izinli alan kümesi koda yazılır.

### GA-23 · DOĞRU · düşük · TK14 (satır 107), §4.4.3 (satır 488), §4.4.2 (satır 445-446)

**Sorun.** Kullanıcı değiştirmek "Kilitle + başka hesapla aç" ile yapılıyor. Pencere ve ön yüz süreci aynı kalıyor. Ailede kilit tek kişiye aitti; ön yüz kilitlenince sorgu önbelleğini temizlemiyordu. OAB'de bir önceki hesabın yüklediği veri sonraki hesabın oturumunda ön yüz belleğinde kalabilir. Buna `yonetici`ye özgü maskesiz T.C. kimlik no, tam IBAN ve kişi dökümü de dahildir. Tasarım oturum değişiminde ön yüz durumunun ne olacağını söylemiyor.

**Doğrulama.** Tasarım:107 "kullanıcı değiştirmek = Kilitle + başka hesapla aç"; :445-446 maskesiz okumalar yalnız belirli rolde. İskelet `frontend/src/lib/kilit.ts` yalnız olay yayınlıyor; `frontend/src/modules/guvenlik` ve `kip` içinde `queryClient.clear`/`removeQueries` yok (grep).

**Düzeltme.** §4.4.3'e kural yazılmalı: kilitlenme (elle, boşta ya da 423) ve her kilit açılışı ön yüzde sorgu önbelleğini ve modül belleğini sıfırlar. En basit yol pencere içeriğini yeniden yüklemektir; oturum çerezi kalır. Bunu sabitleyen bir Vitest testi yazılır.

### GA-24 · DOĞRU · düşük · §8.5 (satır 1694), §15.4 B-10 (satır 2767) ↔ §11 (satır 2297-2331, 2355-2364)

**Sorun.** Arşiv paketinin korunması için önerilen `pyzipper` "§11'e yeni bağımlılık" diye anılıyor. Ama §11.1 tablosunda ve §11.4 lisans kümesinde yok. §11'in kendi kuralı her bağımlılık değişikliğinin dört halkaya ve lisans kümesine birlikte işlenmesini istiyor. Geçişli bağımlılıklar ve lisansları da belirsiz kalıyor.

**Doğrulama.** Tasarım:1694 "Yeni bağımlılık (ör. `pyzipper`) §11 bağımlılık kesim listesine girer"; :2767 "(`pyzipper`, §11'e yeni bağımlılık)"; §11.1 (tasarım:2315-2331) B1-B15 arasında yok; :2297-2298 "dört halkaya ve lisans kümesine birlikte".

**Düzeltme.** §11.1'e "B16 · pyzipper · ADAY · arşiv paketi şifreleme (B-10) · F4" satırı, §11.4'e "Giren (aday)" satırı eklenmeli. Geçişli bağımlılıklar F4 başında çözülmüş kurulumdan çıkarılıp pinlenmeli. Dört halka ve lisans kapısı aynı değişiklikte güncellenmeli.

Çürütülen aday: 9

---

## KVKK ve hukuki konum (18)

*Denetlenen belge: `docs/tasarim/2026-10-31-genel-tasarim.md` (TASLAK v1, 2823 satır). Satır numaraları bu belgedendir;
kaynak atıfları `dosya:satır` biçimindedir. Önem dağılımı: yüksek 5 · orta 7 · düşük 6.*

### KM-1 · DOĞRU · yüksek · §5.2.8, §5.4, §6.2-6, §8.5, §9.6 (satır 763, 861-862, 879-884, 1021-1023, 1681, 1688, 1898-1899, 2762)

**Sorun.** T5'in "liste dönem kapanışında silinir" kararı evrak dosyalarıyla fiilen deliniyor. Veli adını ve
öğrencinin sınıfını taşıyan iki belge var: E07'nin sınıf teslim çizelgesi ve E08 katılım cetveli (docx, pdf, ayrıca
xlsx). İkisi de `GeneratedDocument` kaydıdır, dosyaları `Attachment` olarak saklanır. §5.4 "üretilen evrak"ı
"silinmez, anonimleştirilmez" sınıfına koyar; arşiv paketi `01-evrak/` de dönemin bütün `GeneratedDocument`
dosyalarını alır. Sonuçta `ParentRoster` satırları silinse bile aynı liste program içinde ve arşiv paketinde saklama
süresi boyunca durur. Tasarım tarama için aynı gerekçeyi kendisi yazmış ("tarama aynı kişisel veriyi ikinci kez ve
süresiz tutardı", 883-884), ama üretilen dosyayı gözden kaçırmış. Bir çatışma daha var: §6.2-6, kapanmış dönemin
evrakı yeniden basıldığında içerik özetinin aynı çıkmasını istiyor. Liste silindikten sonra E07 ve E08 adlarla
yeniden üretilemez. Yani dosya ya saklanacak (KVKK md. 4/2-ç ve 7/1'e aykırı) ya da değişmez bozulacak.

**Doğrulama.** Kaynak kullanıcı kararı: plan §1.8 (`docs/plan/2026-10-31-f0-f1-plani.md:224`). Kararın açık
noktası ("imzalı cetvelin taraması mı, yalnız sayılar mı") F0-8'e bırakılmıştı. Tasarımdaki dayanaklar:
- 1898: E07 "teslim çizelgesinde veli adı". 1899: E08 "`ParentRoster` (veli adı + öğrencinin sınıfı)". 1822: E08
  biçimi "docx+pdf, xlsx".
- 763: `GeneratedDocument` `files → Attachment` taşır; "eski satır silinmez".
- 861: "Birlik kayıtları: … üretilen evrak … | Silinmez, anonimleştirilmez".
- 1681: `01-evrak/` "Dönemin bütün `GeneratedDocument` dosyaları". 1688 "Dışarıda kalanlar: veli listesi" diyor ama
  yalnız modeli dışarıda bırakıyor.
- 879 ve 2762 (B-11) yalnız "izi (sha256)" saklamayı tarif ediyor; dosyanın akıbeti yazılı değil.
- 1021-1023: kapanmış dönemde yeniden basımda "içerik özeti … aynı çıkar".

KVKK md. 4/2-ç ve 4/2-d `docs/mevzuat/6698-kvkk.md:44`'te, md. 7/1 aynı dosyanın 62. satırında. Katılım cetvelinin
aslı kâğıttır ve genel kurul tutanak dosyasında saklanır (Yön. md. 10/1-a ve 23/1-a, 23/6:
`meb-okul-aile-birligi-yonetmeligi.md:155, 382, 404`). Programdaki kopya resmî kaydın yerine geçmiyor.

**Düzeltme.**
- §5.2.8'e `GeneratedDocument.personal_list` (ya da evrak kataloğunda `kisi_listesi: true`) bayrağı eklensin. E07
  çizelgesi ve adlı E08 bu sınıfa girsin.
- Bu sınıfın dosyaları basılıp kaydedildikten sonra en geç dönem kapanışında `ParentRoster` ile aynı işlemde imha
  edilsin. Satır kalır, `purged_at` dolar; tür, tarih, satır sayısı ve sha256 iz olarak durur.
- §5.4 tablosuna "Veli adı taşıyan üretilmiş evrak dosyası" satırı yazılsın. §8.5 `01-evrak/` bu dosyaları
  dışarıda bıraksın, yerlerine yalnız iz satırı girsin.
- §6.2-6'ya istisna eklensin: "kişi listesi taşıyan evrak, kaynak verisi silindikten sonra yeniden basılmaz; iz
  satırı gösterilir".
- F4 kapısına test: "kapanıştan sonra hiçbir `Attachment`, arşiv üyesi ya da `03-veri` kaydı `ParentRoster`'dan
  türemiş ad taşımaz".

### KM-2 · DOĞRU · yüksek · TK16, §4.1, §5 girişi, §5.1, §5.3, §5.4, §8.5, §12.B (satır 109, 328-330, 593-594, 625, 822-840, 861, 891, 1682, 2543, 2585)

**Sorun.** Denetim izi, hesap ve erişim günlüğü modelleri hiçbir yerde tanımlanmamış. Bu modeller KVKK silme
düzeninin temeli olduğu hâlde açıkta kalıyor.

TK16'ya göre izin satırları "kaydın özetini taşır", ekleme-yalnızdır ve HMAC zinciriyle mühürlenir. Bu "özet"in
neyi içerdiği belirsiz. Ad, telefon, veli listesi satırı ya da K9 açıksa bağışçı T.C. kimlik no'su özete girerse
§5.4'teki her silme boşa düşer. Bu satırlar silinemez, çünkü zincir kırılır ve altın kural 4 çiğnenir. Satırlar
arşiv paketine de "denetim izi dökümü" olarak girer. §5.4'ün (4). maddesi yalnız **silme** satırlarını kişisiz
yapıyor; ilk yazma satırları hakkında bir şey demiyor.

`Hesap` modeli ad-soyad taşıyor, erişim günlüğü de "kim kimin T.C. kimlik no'sunu gördü" bilgisini. Bu iki model ve
denetim izi §5.3 şifreleme tablosunda da yok. Model tanımları iki bölüm arasında birbirine gönderilip boşta
kalıyor: §4 → §5 → §4.

**Doğrulama.**
- Döngüsel gönderme: 109 (TK16) "model §5"; 328-330 "(TK16, model §5)"; 593-594 "hesap ve denetim izi modelleri …
  mimaride (§4)"; 625 "ekleme-yalnız denetim izi §4'te tanımlanır"; 2543 "`Hesap`, `DenetimIzi` §5'te"; 2585
  "(alanlar §5)". §4.4'te alan listesi yok. 509-510'a göre ad-soyad "veritabanındadır (`Hesap`, alanları §5)".
- Belgede `AccessLog` benzeri bir erişim günlüğü modeli hiç geçmiyor. Yalnız 445, 847, 871 ve 1703'te ad olarak
  anılıyor.
- 822-840'taki şifreleme tablosunda `Hesap`, `DenetimIzi` ve erişim günlüğü satırı yok.
- 861: denetim izi "Silinmez, anonimleştirilmez". 891: "her silme ve boşaltma denetim izine kişisiz satır yazar".
  1682: `02-defterler/` "denetim izi dökümü".
- KVKK md. 7/1 (`6698-kvkk.md:62`), işleme sebebi ortadan kalkan verinin silinmesini istiyor. Silinen alanın değeri
  ekleme-yalnız bir izde kalırsa bu yükümlülük karşılanmaz.

**Düzeltme.**
- §5'e üç model tablosu yazılsın: `Hesap`, `DenetimIzi`, `ErisimGunlugu`.
- `DenetimIzi.ozet` için bağlayıcı bir kural konsun: özet yalnız model adı, kayıt kimliği, değişen **alan adları**,
  açık (kişisiz) alanların eski ve yeni değerleri ve şifreli alanlar için "değişti" işareti taşır. Kişi adı, telefon,
  T.C. kimlik no, serbest metin ve `ParentRoster` alanı özete hiçbir biçimde girmez; şifreli hâli de girmez.
- F1b kapısına test: her model için yazma yapılır, sonra `DenetimIzi` satırlarında bilinen uydurma ad ve
  telefonlar aranır; sonuç sıfır olmalı.
- `Hesap.ad_soyad` şifreli olsun (kör indeks gerekmez).
- `ErisimGunlugu` görenin hesabını, alan adını, kayıt kimliğini ve zamanı tutsun; değeri tutmasın. Saklama süresi
  B-9'daki gibi kalsın.
- Arşiv paketindeki denetim izi dökümü aynı kuralla üretilsin.

### KM-3 · DOĞRU · yüksek · §3.4, §5.2.2, §5.2.9, §5.3, §6.4.8 (satır 268-271, 666, 780, 827, 836, 1188)

**Sorun.** Tasarım "adli sicil verisi … tutulmaz" diyor, ama kantin isteklisi için ceza mahkûmiyeti bilgisini açık
alanda tutuyor. `Bidder.crime_bar` alanının değerlerinden biri `ENGEL_VAR`. Bu değer gerçek kişi istekli için "12/5
suçlarından yargı kararıyla tespit edilmiş mahkûmiyeti var" demektir, yani KVKK md. 6/1'deki "ceza mahkûmiyeti …
ile ilgili veri"dir. §5.3 bu alanı "engel işaretleri" adıyla **açık** sütununa koymuş. Serbest metin
`disqualified_reason` da şifreli listede yok; §5.3'ün "her serbest metin şifrelidir" ilkesine aykırı ve aynı bilgiyi
yazıya dökebilir. §6.4.8'deki "beyan işareti, içerik tutulmaz" notu modelle çelişiyor.

Aynı sızıntı organ üyeliğinde daha dolaylı biçimde var. `drop_kind = NITELIK_KAYBI` açık alandır. Yönetmelik
"niteliği haiz olmadıkları sonradan anlaşılan" ifadesini yalnız 12/5 ve 14/7'nin suç hükmünde kullanıyor. Bu yüzden
alan, kişinin mahkûmiyetine işaret eder (KISMEN: değer başka bir nitelik kaybı için de seçilebilir).

Arşiv paketi `03-veri/` bütün bu alanları süresiz taşıyacak (KM-5). Özel nitelikli veri için md. 6/3'teki işleme
şartının ve 6/4'teki "Kurul tarafından belirlenen yeterli önlemler"in değerlendirmesi belgede yok.

**Doğrulama.**
- Tasarım: 780 `crime_bar` (`BEYAN_YOK_DEDI` · `ENGEL_VAR`) ve "`ENGEL_VAR` ise seçilemez — sert"; 836 Bidder
  açık: "engel işaretleri"; 270-271 "adli sicil verisi … tutulmaz"; 1188 "beyan işareti, içerik tutulmaz"; 666
  `drop_kind` içinde `NITELIK_KAYBI`; 827 `OrganMembership` açık alanları.
- Korpus: KVKK md. 6/1, 6/3 ve 6/4 (`6698-kvkk.md:56`). Yön. md. 20/11 ("12 nci maddenin beşinci fıkrasında sayılan
  suçları işledikleri yargı kararıyla tespit edilenler ihalelere katılamazlar", `meb-okul-aile-birligi-yonetmeligi.md:333`).
  md. 12/5'in son cümlesi (:195) ve md. 14/7 (:237) "niteliği haiz olmadıkları" der.
- Kullanıcı kararı F0-b (81) yalnız engelin **sert** olmasını istiyor; engel sebebinin kayıtta tutulmasını
  istemiyor.

**Düzeltme.**
- `crime_bar` ve `kinship_bar` tek bir alanda birleşsin: `katilim_engeli` (`YOK` · `VAR`). Değer hangi bentten
  geldiğini söylemesin; sert engel bu alana bağlansın.
- Gerekçe yalnız şifreli bir alanda dursun (`engel_gerekce`, `sensitivity=OZEL_NITELIKLI`). Okuması erişim günlüğüne
  düşsün, arşiv paketinin `03-veri/` bölümüne varsayılan olarak girmesin.
- `disqualified_reason` §5.3 listesine eklensin. Kapalı bir gerekçe listesi olsun; "adli sicil içeriği yazılmaz"
  uyarısı gösterilsin.
- `drop_kind` içindeki `NITELIK_KAYBI`, `DIGER` ile birleşsin. Düşme belgesi ve gerekçesi şifreli kalsın.
- §3.4'e md. 6/3-6/4 notu eklensin. Programın bu veriyi hangi şarta dayanarak işlediği (bkz. KM-7) ve Kurul'un
  "yeterli önlemler" kararının korpusta olmadığı yazılsın. Karar BENIOKU §6'ya "bekliyor" diye girsin.

### KM-4 · KISMEN · yüksek · T5, §4.4.2, §5.2.2, §7.1, §8.4, §9.6 (satır 78, 441-442, 468, 667, 1351-1352, 1664-1669, 1822, 1885, 1898-1899)

**Sorun.** Tasarım BSG Yönergesi'nin md. 7, 9, 10 ve 11'ine sık atıf yapıyor. T5'e en doğrudan uyan iki hükmü ise
hiç anmıyor: md. 5/8 ve 6/7.

md. 5/8, okuldaki yetkili kullanıcının velilere ait kişisel bilgileri "3. şahıslar ile paylaşamaz" olduğunu
söylüyor. Ad soyad ve "okuduğu okul" bu bilgiler arasında sayılıyor. Tasarımda e-Okul'dan MY'nin aldığı veli listesi
veli rollerine açılıyor:
- E07 ve E08'i (adlı, xlsx dâhil) `sekreter` üretir.
- Kaydedilmiş belgeyi "her okur rol basabilir"; bu roller YK'nin veli üyeleri ve DK'dir.
- Adlı katılım cetveli genel kurulda bütün katılımcılar arasında dolaşır. Her veli öteki velilerin adını ve
  çocuğunun sınıfını görür.

Rol matrisi "Kişisel veri içeren dışa aktarım (veli listesi …)" satırını yalnız `yonetici`ye veriyor. E08 xlsx
çıktısı ise bir veli listesi dışa aktarımıdır ve `sekreter` de üretebiliyor; matris bununla çelişiyor.

KISMEN etiketinin nedeni: birliğin ve YK'deki velilerin md. 5/8 anlamında "3. şahıs" sayılıp sayılmadığı yoruma
açık (birlik "okullar bünyesinde" kurulur, Yön. md. 5/1). Ama tasarım bu değerlendirmeyi hiç yapmamış. T5 bu
değerlendirmeye dayanıyor.

**Doğrulama.**
- BSG md. 5/8 (`meb-bilgi-ve-sistem-guvenligi-yonergesi.md:118`): "hiçbir sebepten ötürü … velilere ait kişisel
  bilgileri … 3. şahıslar ile paylaşamazlar. Gerekli görüldüğü zaman … Başkanlıktan talepte bulunurlar". md. 6/7
  (:143) aynı yöndedir.
- Tasarım: 468 dışa aktarım yalnız `yonetici`; 1899 E08 "Üreten: yonetici, sekreter"; 1822 E08 "xlsx"; 1885
  "kaydedilmiş belgeyi her okur rol basabilir"; 441-442 "Okuma, … evrak çıktısını … almayı da kapsar"; 1351
  "katılım cetveli adlarla ve sınıfla basılır".
- Belgede "md. 5/8", "6/7" ve "3. şahıs" geçmiyor (arama sonucu boş).

**Düzeltme.**
- §3.4'e "e-Okul kaynaklı veri" alt başlığı eklensin. BSG md. 5/8 ve 6/7 alıntılansın. Birliğin bu hükümler
  karşısındaki konumu veri sorumlusu sorusuyla birlikte (F0-e b) kılavuzda okul müdürlüğüne açık soru olarak
  bırakılsın.
- Teknik sınır konsun: `ParentRoster` okuması ve adlı E07, E08 üretimi yalnız `yonetici` rolünde olsun. Veli
  rolleri ve DK yalnız sayıları ve boş satırlı cetveli görsün. E08 xlsx yalnız `yonetici`ye açık olsun. 468.
  satırla E08 satırı eşitlensin.
- Adlı cetvelde dolaşımı daraltan bir düzen önerilsin: her sınıf ayrı sayfada, imza masasında görevli elinde. Kâğıt
  basımı "Kişisel veri içerir" dipnotuyla, imzadan sonra genel kurul tutanak dosyasına konsun.
- T5'in bu sınırlarla uygulanması kullanıcıya §15'te ayrı soru olarak sorulsun. Seçenekler: (a) yukarıdaki
  sınırlarla adlı cetvel, (b) adlı cetvel yalnız MY'nin elinde, (c) BSG 5/8'in son cümlesine göre il/ilçe yoluyla
  görüş.

### KM-5 · DOĞRU · yüksek · §5.4, §7.8, §8.5 (satır 865, 868, 1543, 1682-1689; B-5 2763, B-7 2764)

**Sorun.** Arşiv paketi, §5.4'ün boşaltma kararlarını saklama süresi boyunca geçersiz kılıyor. `03-veri/` "her
model için kayıt listesi"ni şifresi çözülmüş olarak alıyor. Dışarıda bıraktığı yalnız dört şey var: veli listesi,
T.C. kimlik no, özel nitelikli ekler, anahtarlar.

Böylece şu veriler paketin içinde kalıyor: `OabPerson.phone`, seçilmeyen isteklinin adres, telefon ve e-postası
(`Bidder.contact_*`), `crime_bar` ve `disqualified_reason` (KM-3), `dropped_reason`. Paket "defter ve belgelerin
okulda saklandığı süre boyunca" tutulacak. B-7 telefonu, B-5 istekli iletişim bilgisini yıllar içinde boşaltıyor;
pakette bu veriler kalıcı olur.

§7.8'deki sıra da sorunu büyütüyor: arşiv paketi, "veli listesi, T.C. kimlik no'lar ve süresi dolan telefonlar
silinir" adımından **önce** üretiliyor.

**Doğrulama.**
- 1683: `03-veri/` "Her model için kayıt listesi; şifreli alanlar çözülmüş". 1688-1689: dışarıda kalanlar listesi;
  telefon ve iletişim bilgisi bu listede yok. 1675: amaç "okulda saklandığı süre boyunca".
- 1543 sıralaması: "`pre-kapanis` yedeği · … · Arşiv paketi üretilir (§8.5) · Veli listesi, T.C. kimlik no'lar ve
  süresi dolan telefonlar silinir".
- 865: telefon "dönemin kapanışında boşaltılır". 868: istekli iletişimi "Kesinleşme + 2 yıl".
- KVKK md. 4/2-d ve 7/1 (`6698-kvkk.md:44, 62`).

**Düzeltme.**
- §8.5'e alan düzeyinde bir dışlama listesi yazılsın: `OabPerson.phone`, `Bidder.contact_*`, `engel_gerekce` ve
  `disqualified_reason`, `dropped_reason` ve §5.4'te süreli boşaltılan her alan. Liste tek bir sabitten (§5.4
  tablosundan) üretilsin, testle kilitlensin.
- §7.8'de sıra tersine çevrilsin: önce kapanış silmeleri, sonra arşiv paketi.
- `docs/arsiv-paketi.md` şemasına bir kural yazılsın: "süreli kişisel veri alanı pakete girmez".
- F4 kapısına test: arşiv paketinde uydurma telefon ve e-posta kalıbı sıfır olmalı.

### KM-6 · KISMEN · orta · §3.4, §5.1, §9.5-9.6 E04, E07; §15.2 KE-20 (satır 266-267, 629-641, 1818, 1895, 1898, 2733)

**Sorun.** Aydınlatma yükümlülüğü yanlış muhataba ve eksik kapsamla kurulmuş. §3.4 aydınlatmayı "kılavuzda ve ilk
kurulumda" veriyor. Bu iki yerin muhatabı program kullanıcısıdır. KVKK md. 10 ise bilginin "ilgili kişilere" ve
verinin "elde edilmesi sırasında" verilmesini ister.

E04'ün kapsamı yalnız "veli, bağışçı, organ üyesi". Programın veri işlediği başka kişi kümeleri dışarıda kalmış:
- e-Okul'dan topluca alınan öğretmen ve yönetici adları (`Personnel`),
- kantin ve servis istekliliği yapan gerçek kişiler,
- kantin çalışanı, şoför ve rehber personel (`BidderDocument.subject_name`),
- gerçek kişi tedarikçiler,
- program kullanıcıları.

Veliler için ulaştırma kanalı da yok. Bütün velilere ulaşan tek belge E07 davet mektubu ve o "kişisiz" kurgulanmış;
aydınlatma notu taşımıyor.

E04'ün veri kaynağı "okul kartı (veri sorumlusu alanı, KE-20)" diye yazılmış. Bu alan §5.1'deki `SchoolConfig`
ekleri arasında yok.

**Doğrulama.**
- KVKK md. 10/1 (`6698-kvkk.md:82`).
- Tasarım: 267 "aydınlatma metni kılavuzda ve ilk kurulumda"; 1818 E04 kapsamı; 1898 E07 "Davet mektubu kişisiz
  ('Sayın Veli')"; 629-641 `SchoolConfig` ek alanları arasında veri sorumlusu alanı yok; 2733 KE-20 "Okul kartındaki
  alandan dolar".
- KISMEN etiketinin nedeni: E04'ün metni "F1b içe aktarma ekranında" da gösteriliyor (1818). Yani konu tamamen
  atlanmamış, ama muhatap ve kapsam eksik.

**Düzeltme.**
- E04 dört alt metne bölünsün: veli ve üye; personel; istekli ve çalışan; bağışçı ve tedarikçi.
- Ulaştırma noktaları yazılsın:
  - E07 davet mektubuna kısa aydınlatma paragrafı ve tam metnin nerede okunacağı.
  - Kantin ilanına ve servis ilanına (E48), şartname teslim tutanağına (E50) istekli metni.
  - E46 ve E58 belge tesliminde çalışan metni.
  - Bağışta, E20/E21'e "aydınlatma verildi" işareti.
- `SchoolConfig`'e `data_controller_text` (veri sorumlusu ve iletişim) alanı eklensin. Boşken E04 basılmasın.
- §3.4'teki cümle düzeltilsin: "Aydınlatma metni ilgili kişiye verinin elde edildiği anda verilir (KVKK md. 10).
  Kılavuz ve ilk kurulum ekranı yalnız kullanıcıyı bilgilendirir."

### KM-7 · DOĞRU · orta · §3.4, §5.2.2, §5.4, E04 (satır 262-278, 665, 857, 867, 1895)

**Sorun.** Tasarım işleme amaçlarını ve hukuki sebepleri hiçbir yerde veri kategorisine eşlememiş. KVKK md. 5
belgede bir kez bile anılmıyor; md. 6 yalnız 867. satırda ve bentsiz geçiyor. Bunun üç sonucu var:

(1) E04'ün kabul ölçütü "KVKK 10/1 a-d unsurlarının her biri ayrı başlıkta" diyor. 10/1-ç "hukuki sebep" ister;
tasarımda bu başlığı dolduracak içerik yok.

(2) Bazı alanların amacı yazılmamış. `OabPerson.phone` örneğin: program SMS ya da e-posta göndermiyor (§8.4-4), ama
alan yine de var. md. 4/2-c "belirli, açık ve meşru amaç" ister.

(3) Kantin çalışanının adli sicil ve portör belgesi için md. 6/3'ün hangi bendine dayanıldığı yazılmamış. 6/3-b
"**kanunlarda** açıkça öngörülmesi" der; OAB Yönetmeliği md. 20/7 ve 23/4 kanun değil, yönetmeliktir. 6/3-f
istihdamdaki hukuki yükümlülüğü sayar, ama bu çalışanların işvereni birlik değil kiracıdır. Bu gerçek bir hukuki
gerilimdir ve tasarımda görünmüyor.

**Doğrulama.**
- KVKK md. 4/2-c, 5/2, 6/3 ve 10/1-ç (`6698-kvkk.md:44, 50, 56, 82`).
- Tasarımda "hukuki sebep", "md. 5", "5/2" ve "madde-5" aramaları KVKK için sonuç vermiyor. 867'de yalnız "[KVKK
  md. 6]" var.
- 665: `phone` "(şifreli, isteğe bağlı)"; amaç yazılmamış. 1669: "Telefon ve iletişim yoktur … program SMS ya da
  e-posta göndermez".
- Yön. md. 20/7 ve 23/4 (`meb-okul-aile-birligi-yonetmeligi.md:325, 400`).

**Düzeltme.** §3.4'e bir "işleme envanteri" tablosu eklensin. Sütunlar: veri kategorisi · ilgili kişi grubu · amaç ·
hukuki sebep (KVKK maddesi ve dayanak hüküm) · saklama (§5.4 satırı) · aktarım (yok / TEFBİS'e okul idaresi / MEM).
E04 bu tablodan dolsun. Örnek satırlar:
- Organ üyesi: md. 5/2-ç; Yön. md. 12, 13/5, 18/2.
- Bağışçı adı: md. 5/2-ç; Yön. md. 6/1-f, 16, 23/5.
- İstekli: md. 5/2-c ve 5/2-ç; Yön. md. 20, U-E md. 6.
- Veli listesi: md. 5/2-ç; Yön. md. 9/3, 10/1-a. "Zorunlu" unsurunun boş satırlı cetvel seçeneği karşısında
  değerlendirilmesi açık soru olarak yazılsın.
- Kantin çalışanı belgesi: md. 6/3 bendi **DOĞRULANMADI**. Kılavuzda okul müdürlüğüne açık soru olarak gitsin.

`OabPerson.phone` için amaç yazılsın, yoksa alan kaldırılsın.

### KM-8 · DOĞRU · orta · §3.3, §6.4.2, §6.4.6, §6.4.8, §7.1, §7.4 (satır 270, 1089, 1090, 1149, 1188, 1340, 1427)

**Sorun.** Dört kural, mevzuatta olmayan bir "beyan alınması" yükümlülüğünü madde numarasına bağlıyor:
`yonetim_kurulu.tek_birlik`, `uyelik.suc_engeli_beyani`, `harcama.alim_komisyonu_uyeleri` (12/5 beyanı) ve
`kantin.istekli_suc_engeli` ("beyan işareti").

Atıf yapılan maddelerin hiçbiri beyandan söz etmiyor:
- md. 12/4 yalnız "aynı anda birden fazla birlik yönetiminde görev alamazlar" der.
- md. 12/5, 14/7 ve 20/11 suçlu olanların görev alamayacağını ve sonradan anlaşılırsa görevin sona ereceğini
  söyler.

Beyan, bu yasağı uygulamanın bir **okul yöntemidir**; §3.3'teki ayrımda "okul ayarı / uygulaması" sınıfına girer.
Uyarı metni ve E01'deki "beyan sütunu" ise kullanıcıya bunu "md. 12/5 gereği" diye sunacak. Bu, altın kural 1'e ve
§3.3'ün "mevzuat gereği diye sunulmaz" ilkesine aykırı.

Kökeni OYS envanterindeki "md. 12/5 beyan ister" cümlesidir (S-20); korpusta karşılığı yok.

**Doğrulama.**
- Korpus: md. 12/4 ve 12/5 (`meb-okul-aile-birligi-yonetmeligi.md:193, 195`), 14/7 (:237), 20/11 (:333).
  Korpusun tamamında "beyan" araması OAB maddelerinde sonuç vermiyor; yalnız servis U-E'de "adres beyanı" geçiyor.
- Envanter: `2026-10-31-oys-oab-envanteri.md:739` "md. 12/5 beyan ister".
- Tasarım: 1089, 1090 ve 1188 kuralları "Madde" sütununda 12/4, 12/5, 14/7 ve 20/11'e bağlıyor. Aynı tabloda
  1084 ve 1110'daki benzer kurallara "Yorum + proje kararı" / "kullanıcı kararı" notu düşülmüş; bu dört kurala
  düşülmemiş.

**Düzeltme.**
- Kural paketinde hüküm ile yöntem ayrılsın. Hüküm: md. 12/5 ve 14/7 (görev alamaz; sonradan anlaşılırsa görev
  sona erer) ile md. 12/4 (tek birlik). Bunlar [B] ya da sert bağlam olarak kalsın.
- Beyan ayrı bir "okul uygulaması" kaydı olsun: `kaynak: okul_uygulamasi`, `madde` boş, ileti "Okulunuzun
  uygulaması: beyan alındı mı?". Atıf kilidi (§6.3 D3) böyle kayıtlar için ayrı bir tür tanısın.
- E01'deki sütun başlığı "Beyan (okul uygulaması)" olsun.

### KM-9 · KISMEN · orta · §3.4 (satır 264-267)

**Sorun.** §3.4, KVKK'nın kâğıt kayda uygulanışını yanlış aktarıyor ve asıl sonucu düşürüyor. Cümle şu:
"Masaüstü program, kâğıt kaydın 'yalnız otomatik olmayan yollarla işleme' istisnasını ortadan kaldırır". Atıf
çapasız ([KVKK]). Okuyan, kâğıt kaydın KVKK dışında olduğunu ve programla kapsama girdiğini anlar.

Oysa KVKK md. 2 ve 3/1-e, otomatik olmayan işlemeyi de "veri kayıt sisteminin parçası olmak kaydıyla" kapsama
alır. Karar defteri, katılım cetveli ve koçan zaten yapılandırılmış kayıtlardır. Ön değerlendirmedeki aynı cümle
VERBİS istisnaları bağlamında yazılmıştı (Kurul kararları 2018/32, 2018/87 …). Tasarım bu bağlamı ve onun asıl
sonucunu kaybetmiş: KVKK md. 16'daki sicile kayıt yükümlülüğü. VERBİS ve md. 16 belgede hiç geçmiyor. Kurul'un
istisna kararları korpusta da yok.

KISMEN etiketinin nedeni: VERBİS sonucu ön değerlendirmenin bağlamından çıkarılmıştır. Kurul kararlarının metni
korpusta olmadığı için doğrulanamadı.

**Doğrulama.**
- KVKK md. 2 (`6698-kvkk.md:30`) "veri kayıt sisteminin parçası olmak kaydıyla otomatik olmayan yollarla işleyen".
  md. 16/2 (:120) sicile kayıt.
- Ön değerlendirme `2026-10-31-on-degerlendirme.md:238-240`: "VERBİS istisnaları (2018/32, 2018/87, …) …
  **Dikkat:** kâğıt kayıt … istisnasına girer".
- BENIOKU §4 ve §6'da Kurul kararı yok (`docs/mevzuat/BENIOKU.md:58-109`).
- Tasarımda "VERBİS" araması sonuç vermiyor.

**Düzeltme.** Cümle şöyle yazılsın: "KVKK otomatik olmayan işlemeyi de veri kayıt sisteminin parçasıysa kapsar (md.
2); birliğin kâğıt kayıtları zaten kapsamdadır. Program, kâğıt kayda dayanan VERBİS kayıt istisnasının (Kurul
kararları; korpusta değil, DOĞRULANMADI) okul için geçerliliğini değiştirebilir (md. 16)." VERBİS sorusu veri
sorumlusu sorusuyla birlikte kılavuzdaki açık sorulara eklensin. Kurul kararları BENIOKU §6'ya "bekliyor" olarak
girsin.

### KM-10 · DOĞRU · orta · §2.3.2, §5.4 çalışma biçimi, §7.8, §12.B, §14 (satır 189, 889-894, 1543, 2523, 2588-2589, 2680-2689)

**Sorun.** §5.4'ün silme düzeninin yedekte, fazda ve kapıda karşılığı yok.

(1) Tasarım "Silinen veri günlük yedeklerde ve `pre-kapanis` yedeğinde en çok 14 gün kalır" diyor. Bu vaadi
taşıyan bir mekanizma tanımlanmamış:
- `pre-kapanis` öneki §2.3.2'deki yedek önekleri listesinde ve `backup.py` UYARLA satırında yok.
- İskelette 14 günlük rotasyon yalnız günlük yedeğe uygulanıyor. Göç öncesi yedekler "son 5" kuralıyla tutuluyor,
  `pre-parola` ve `pre-anonim` için bir süre yok.
- Yıllık `pre-kapanis` yedeği "son 5" gibi tutulursa silinen veli listesi, T.C. kimlik no'lar ve telefonlar yıllarca
  yedekte kalır.

(2) §5.4, tetikten önce `pre-anonim` yedeği alınacağını söylüyor (890). §2.3.2 ve §12.B ise "`pre-anonim-` saklama
fazına kadar kullanılmaz" diyor (189, 2523).

(3) §14 faz planında bir "saklama fazı" yok. Süreli silmeler (istekli iletişimi, erişim günlüğü, taramalar) hiçbir
faza bağlanmamış. Dönem kapanışı silmelerini içeren F4'ün kod kapısında da bir silme testi yok. Altın kural 7'ye
göre faz kapıdan geçmeden kapanmaz; KVKK silmesi bu yüzden kapı dışında kalıyor.

**Doğrulama.**
- Tasarım: 893 vaat; 187-189 önek listesi (`pre-kapanis` yok); 2523 `backup.py` satırı; 1543 `pre-kapanis-<tarih>.odbak`;
  2588-2589 "saklama ve anonimleştirme, F4+"; 2685 F4 kapısı yalnız "kesin hesap = banka; devir tutanağı ve arşiv
  paketi … okunabilir".
- İskelet: `2026-10-31-iskelet-envanteri.md:503` "Günlük (14 gün), göç öncesi (son 5), `pre-parola`, `pre-anonim`".

**Düzeltme.**
- §2.3.2'ye `pre-kapanis-` öneki eklensin.
- `backup.py` UYARLA satırına bir kural yazılsın: `pre-kapanis` ve `pre-anonim` yedekleri günlük yedekle aynı 14
  günlük rotasyona girer; rotasyon her yedek türü için testle kilitlenir.
- 189 ve 2523'teki "saklama fazına kadar kullanılmaz" ifadesi F4 ile değiştirilsin.
- §14'te F4'e "dönem kapanışı KVKK silmeleri" kalemi eklensin. F4 kapısına şu test girsin: kapanıştan sonra veri
  tabanında, `DenetimIzi`'nde, arşiv paketinde ve 15. günden sonra yedek dizininde uydurma veli adı, telefon ve
  T.C. kimlik no kalmamalı.
- Süreli silmeler (B-5, B-9) ayrı bir faza (F5/F6) yazılsın.

### KM-11 · KISMEN · orta · §4.3 tehdit 9, §5.2.2, §5.2.5, §5.3 ilke (satır 399, 667, 721, 817-820, 826, 831)

**Sorun.** Tehdit 9'daki "kişi adı olmadan kişiye bağlanmaz" iddiası, şifreleme kapsamının iki boşluğu yüzünden
tutmuyor.

(a) `BankTransaction.fingerprint`, "hesap + tarih + tutar + bakiye + referans + açıklamanın normalize özeti"nden
oluşuyor ve açık alanda duruyor. Anahtarlı olduğu yazılmamış. TK12'deki DEK yenileme listesinde de geçmiyor; oradaki
"parmak izi" anahtar parmak izidir. Özetin öteki girdileri zaten açıkta. Diski ele geçiren biri elindeki bir ad
listesiyle şifreli açıklamayı (gönderenin adı, "BAĞIŞ" gibi) tek tek deneyip doğrulayabilir (doğrulama saldırısı).
Bu, §5.3'ün "kişiye ait bilgi içerebilecek her alan şifrelidir" ilkesini dolaylı yoldan deliyor.

(b) `ParentRoster.row_no` (kaynak dosyadaki satır sırası) ve `student_class` açık duruyor. Aynı e-Okul sınıf
listesine erişen biri (herhangi bir öğretmen) sınıf ve satır no ikilisinden veliyi bulur, açık katılım işaretinden
de genel kurula katılıp katılmadığını okur.

KISMEN etiketinin nedeni: (a) özetin nasıl kurulacağı belirtilmemiş, risk anahtarsız uygulamaya bağlı. (b)'deki
veri kısa ömürlüdür ve dönem kapanışında silinir.

**Doğrulama.**
- Tasarım: 721 `fingerprint` tanımı; 831 BankTransaction açık alanları: "parmak izi"; 105 TK12 yeniden
  hesaplanacaklar listesi: "şifreli alanlar, kör indeksler, parmak izi" (anahtar parmak izi, 512). Hareket parmak
  izi için anahtar yok.
- 667 `row_no`; 826 `ParentRoster` açık: "`student_class`, katılım işareti"; 399 tehdit 9 iddiası.
- KVKK md. 3/1-d "kimliği belirli veya belirlenebilir" (`6698-kvkk.md:36`).

**Düzeltme.**
- `fingerprint` = `HMAC-SHA256(HKDF(DEK, "od-hareket-parmak-izi"), normalize(...))` olsun. Bilgi dizgesi §2.3.1'e
  eklensin, TK12'nin yeniden hesaplama listesine girsin.
- §5.3'e ilke cümlesi eklensin: "Şifreli alandan türeyen her özet anahtarlıdır."
- `row_no` kaldırılsın; sıralama çözülmüş ada göre Python'da yapılsın. Ya da `row_no` şifreli tutulsun.
- Tehdit 9'daki "kalan risk" hücresi gerçek kapsama göre yeniden yazılsın.

### KM-12 · DOĞRU · orta · §5.1, §5.4, §8.4, §12.B (satır 622, 859-871, 1663, 2588)

**Sorun.** §5.4 tablosunda iki kişi kümesinin saklama kuralı yok.

(1) `Personnel`: e-Okul personel listesinden okulun **bütün** öğretmen ve yöneticilerinin adları alınıyor. Çoğu hiç
OAB görevi almaz. Ayrılış havuzu "aynen" alınıyor. Kütüphane'de havuz kimseyi silmez; silmeyi Kütüphane'nin saklama
servisi yapar ve OAB o servisi almıyor ("kalıp olarak sonra bakılacaklar"). Sonuç: okuldan ayrılan ve birlikte
hiçbir kaydı olmayan personelin adı süresiz kalır.

(2) Organ üyesi ya da aday olmamış `OabPerson` kayıtları. Tablo yalnız organ üyesi ya da aday olmuş kişide adın
kalacağını söylüyor (866). Öteki kişilerin akıbeti yazılı değil.

**Doğrulama.**
- Tasarım: 622 `Personnel` "Ayrılış havuzu (Kütüphane F1 eki 7) aynen"; 859-871 tabloda `Personnel` satırı yok;
  2588 `saklama.py` ALMA (kalıp).
- Kütüphane sözlüğü: "Aktarım kimseyi ayırmaz ve kimsenin kaydını silmez" (`kutuphane-main/docs/sozluk.md:58`).
- KVKK md. 4/2-d ve 7/1 (`6698-kvkk.md:44, 62`).

**Düzeltme.** §5.4'e iki satır eklensin:
- "`Personnel`: ayrıldı işaretlenen ve hiçbir birlik kaydına (`OabPerson.personnel`, organ, komisyon, imza bloğu)
  bağı olmayan kişi, ayrılışı izleyen dönem kapanışında silinir. Bağı olanın adı `OabPerson`'da kalır."
- "Bağsız `OabPerson`: hiçbir üyelik, aday, bağış, komisyon, imza ya da devir kaydına bağlanmamış kişi, dönem
  kapanışında silinir."

İkisi de KM-10'daki F4 silme testine girsin.

### KM-13 · DOĞRU · düşük · §9.1-5, §9.5-9.6 E56, §10.5 (satır 1731-1733, 1870, 1947, 2269)

**Sorun.** E56 ("Sözleşme imzalanan taşımacıların ilanı", pdf ve html) ilan panosuna ve okulun web sitesine
taşımacının ad/unvanını ve iş iletişimini koyuyor. Taşımacı gerçek kişiyse bu bir kişi adıdır. Mevzuat bunu
istiyor (U-E md. 10/3), ama CLAUDE.md altın kural 5 "duyuru ve ilan çıktılarında kişi adı yok" der.

§9.1-5 ilan çıktılarını sayarken yalnız E06, E29 ve E30'u sayıyor. İstisna yalnız bir testin içinde kalmış
("E56'da yalnız taşımacı unvanı"). Proje kuralından bu sapma kullanıcıya sorulmamış, §15'te de kayıtlı değil.

**Doğrulama.**
- U-E md. 10/3 (`okul-servisi-calistirma-usul-esaslari.md:195`): "sözleşme imzalanan taşımacıların bilgileri …
  ilan panolarında ve web sitesinde yayınlanır".
- Tasarım: 1731 "İlan panosu ve internet çıktılarında (E06, E29, E30) hiçbir kişi adı yoktur"; 1947 E56 "Yalnız
  taşımacının ad/unvanı ve iş iletişimi"; 2269 test notu.
- CLAUDE.md altın kural 5.

**Düzeltme.**
- §9.1-5'e E56 açıkça yazılsın: "Mevzuat gereği istisna (U-E md. 10/3); yalnız ad/unvan ve iş telefonu; adres,
  şoför ve veli verisi yok; ilan kaldırılınca (`removed_board_on`) web dosyası da kaldırılır."
- §15.2'ye "altın kural 5'in E56 istisnası" kullanıcı onayı için satır olarak eklensin.

### KM-14 · DOĞRU · düşük · §5.3, §9.1-5, §9.6 E20, §15.4 B-8 (satır 847, 1733, 1911, 2765)

**Sorun.** K9 açıkken bağışçı T.C. kimlik no'sunun dışa aktarım dosyasına girip girmediği konusunda belge kendi
içinde çelişiyor:
- §5.3 ve B-8 "hiçbir dışa aktarım dosyasına girmez" diyor.
- §9.1-5 aynı cümlede önce "hiçbir belgede yoktur", sonra "K9 açıksa yalnız bağış çizelgesinde maskeli" diyor.
- E20 "Bağış kabul ve kayıt izleme çizelgesi" docx, pdf ve **xlsx** biçiminde üretiliyor. Maskeli kimlik no'yu
  dosyaya taşıyor.

**Doğrulama.** 847, 1733, 1911 (E20: "T.C. kimlik no yalnız K9 açıkken maskeli"), 1834 (E20 biçimleri), 2765.

**Düzeltme.** Tek kural seçilsin. Önerilen kural: "T.C. kimlik no hiçbir dosyaya girmez; E20'de 'kimlik no
kayıtlı: evet/hayır' sütunu bulunur." Ya da maskeli gösterim kabul edilirse §5.3 ve B-8 "maskeli dışında" diye
düzeltilsin. Maske biçimi (görünen hane sayısı) yazılsın.

### KM-15 · DOĞRU · düşük · §3.4, §5.4, §15.4 B-5 (satır 272-275, 867-868, 2763)

**Sorun.** Saklanması gereken kişisel belgelerle ilgili üç bölüm birbirini tutmuyor.

(1) §3.4, kantin çalışanı ve personel belgelerinin "şifreli dosya olarak, erişim günlüğüyle, saklama süresi kural
paketinde" tutulacağını söylüyor. §5.4 ise varsayılan olarak "tarama alınmaz" diyor ve süreyi "öneri" olarak
veriyor. B-5 süreyi "DOĞRULANMADI" diye işaretliyor. §6.4'te kantin belgeleri için bir saklama kuralı da yok;
yalnız `personel.sgk_saklama_yil` var. Altın kural 1'e göre doğrulanmamış süre zaten kural paketine giremez.

(2) Seçilmeyen isteklinin iletişim bilgisi için iki ayrı süre yazılmış. §5.4 "Kesinleşme + 2 yıl" diyor. B-5
"aynı sürede" diyor; buradaki süre "sözleşme sonu + 2 yıl"dır ve beş yıllık bir kantin sözleşmesinde yedi yıla
çıkar.

**Doğrulama.** 275, 867 ("Varsayılan: tarama alınmaz"; "Sözleşme sonu + 2 yıl (öneri)"), 868 ("Kesinleşme + 2 yıl"),
2763. §6.4 tablolarında saklama araması yalnız 1245'i buluyor.

**Düzeltme.**
- §3.4 cümlesi şöyle olsun: "asıl kâğıt birlik dosyasında; program varsayılan olarak yalnız görüldü tarihi ve
  geçerlilik sonunu tutar; tarama eklenirse şifreli ve erişim günlüklü; süre öneri (DOĞRULANMADI), okul ayarı".
- İstekli iletişimi için tek süre seçilip §5.4 ve B-5 eşitlensin. Öneri: kesinleşme + itiraz süresi; sözleşme
  tarafı olan seçilmiş isteklinin iletişim bilgisi sözleşme sonuna dek kalsın.

### KM-16 · DOĞRU · düşük · §3.5, §5.1, §5.2.2 (satır 291-292, 632, 672)

**Sorun.** Okul türü kapsamı ile veri modeli birbirini tutmuyor. §3.5 yaygın eğitim kurumlarını ("üye tanımı
farklı") ve kampüs okullarını kapsam dışı sayıyor. Buna karşın:
- `SchoolConfig.level` `YAYGIN` ve `KARMA` değerlerini sunuyor. Yaygın eğitim seçen okul, örgün eğitimin üye
  tanımıyla hesaplanır. Yaygın eğitimde usta öğretici, eğitsel kulüp üyesi ve gönüllü de üyedir (Yön. md. 4/1-e).
- Temsil türlerinde `KAMPUS_YONETIMI` (md. 13/7) var.

Ayrıca Yönetmelik kapsamına kampüs okullarını açıkça alıyor (md. 2/1 "eğitim kampüslerinde yer alan okullar
dâhil"). Kampüsteki resmî örgün okulun neden kapsam dışı kaldığı yazılmamış.

**Doğrulama.**
- Tasarım: 291-292 kapsam dışı listesi; 632 `level` değerleri; 672 `KAMPUS_YONETIMI`.
- Yön. md. 2/1 ve 4/1-e (`meb-okul-aile-birligi-yonetmeligi.md:35, 57`), md. 13/7 (:212).

**Düzeltme.** v1'de `level`'dan `YAYGIN` kaldırılsın (ya da seçilince "kapsam dışı" uyarısı çıksın).
`KARMA`'nın anlamı yazılsın. "Kampüs okulları" kapsam dışı listesinden çıkarılsın: kampüsteki resmî örgün okul
kapsamdadır, `KAMPUS_YONETIMI` temsil satırı da bunun içindir. Yoksa gerekçe §3.5'e yazılsın.

### KM-17 · KISMEN · düşük · §10, §13.B D42 (satır 1977-1978, 2385, 2661)

**Sorun.** Tasarım, OYS'deki gerçek taşımacı firma adının uydurma adla değiştirileceğini ve "sızıntı denetimi bu
adları da arar" diye yazıyor. Kapının bu adı neye karşı arayacağı ise tanımlanmamış. Denetim betiği ya da test
dosyası adı düz metin olarak içerirse ad, depo kamuya açıldığında oraya girer. Firma bir şahıs işletmesiyse bu
kişisel veridir.

KISMEN etiketinin nedeni: uygulama henüz yazılmadı. Ama tasarım "değer belgeye yazılmaz" demekle yetiniyor; koda
ve teste girmeyeceğini söylemiyor.

**Doğrulama.** 1977-1978 "sızıntı denetimi bu adları da arar"; 2661 "(değer belgeye yazılmaz)". BENIOKU §1 "Depo
kamuya açılacaktır" (`docs/mevzuat/BENIOKU.md:22`).

**Düzeltme.** D42'ye yöntem yazılsın. Kapı yasaklı adları ya depo dışındaki, `.gitignore`'lu yerel bir dosyadan
okusun (`.od-yasakli-adlar.txt`; yoksa kapı "atlandı" yazar ve CI'da sır olarak verilir), ya da yalnız katlanmış
adın SHA-256 özetini tutup belirteç penceresi özetleriyle karşılaştırsın. Ad depoda hiçbir biçimde düz metin
bulunmasın.

### KM-18 · DOĞRU · düşük · §4.3, §4.4.6 (satır 380-408, 544-551)

**Sorun.** Tehdit modeli veri ihlali senaryolarını sayıyor: dönemi biten üyenin elindeki kopya (5), disk ya da USB
yedeğinin çalınması (9), diskte kalan çıktı dosyaları (15). Ama bu olayların KVKK'daki sonucunu hiç yazmıyor:
md. 12/5'e göre veri sorumlusu durumu "en kısa sürede ilgilisine ve Kurula bildirir". Kılavuza ve Hakkında'ya
girecek "dürüst sınırlar" listesinde de bu adım yok. Program bildirime yardım edebilir: yedeğin tarihine göre
etkilenen kişi grupları ve veri kategorileri dökümü, kişi dökümü (§8.6). Tasarım bu desteği planlamamış.

**Doğrulama.** KVKK md. 12/5 (`6698-kvkk.md:94`). Tasarımda "ihlal" ve "12/5" (KVKK) aramaları sonuç vermiyor;
yalnız 386'da md. 12/1 anılıyor.

**Düzeltme.** §4.4.6'ya beşinci madde eklensin: "Kayıp ya da çalınma hâlinde KVKK md. 12/5 bildirimi okulun
(veri sorumlusunun) işidir; kılavuzdaki kontrol listesini izleyin." §8.6'ya "ihlal dökümü" çıktısı eklensin
(`yonetici`; seçilen tarihteki veri kategorileri ve kişi sayıları, kişisiz).

---

Çürütülen aday: 13

*Çürütülenlerin özeti:*
1. Silme Yönetmeliğinin korpusta olmaması tasarımda zaten D20 olarak kayıtlı.
2. Sitede konum ibaresi §3.1'de bağlanmış.
3. Kör indeks DEK'ten türeyen HMAC anahtarıyla kurulmuş; anahtarsız denenemez.
4. Arşiv Yönetmeliği atıfları (9/4, 17/1, 18, 20/2, 24, 4/1-r, 11/5) metinle uyuşuyor.
5. Özel okulu kapsam dışı bırakan "md. 15 ve 17 'resmî okullarda'" gerekçesi doğru.
6. "Kâğıt koçandan girilir" doğru; EK-1'de kimlik no alanı var.
7. README ve LICENSE'ta unvan ve kurum adı yok.
8. `saha.md` anonim.
9. Bağışçı kimlik no'sunun dönem kapanışında boşaltılması bilinçli bir sadeleştirme; süre doğrulanamadığı için
   bulgu sayılmadı.
10. E08'deki gözlemci öğrenci listesi için ad tutan bir model yok.
11. Arşiv Yönetmeliği md. 23'teki dijitalleştirme hükmü birliğe doğrudan uygulanmıyor ("yükümlüler").
12. Silinen listeden sonra genel kurul kanıtı kaybolmuyor: sayılar donuk, aslı kâğıtta (md. 23/1-a, 23/6).
13. Arşiv paketinin USB'de şifrelenmesi B-10 ile karşılanmış.

---

## Mevzuat atıfları I — kural paketi ve testler (18)

*Denetlenen belge: `docs/tasarim/2026-10-31-genel-tasarim.md` (TASLAK v1, 2824 satır). Kapsam: §6 (satır 898-1302) ve
§10 (satır 1974-2292). Satır numaraları bu belgedendir. Korpus atıfları `dosya#çapa` ve fıkra/bent biçimindedir;
kök `docs/mevzuat/`. 146 kuralın her satırı korpustaki madde metniyle karşılaştırıldı. §6.4'teki bütün çapa
bağlantılarının korpusta var olduğu betikle denetlendi. §10.3'te her kuralın en az bir testi var. Mülga fıkraya ya da
(Değişik:…) öncesi lafza dayanan kural bulunmadı. U-E'deki eski 5/7 yıl ve 5362 atıfları doğru biçimde OSAY'ın güncel
hâliyle değiştirilmiş. Önem dağılımı: yüksek 6 · orta 9 · düşük 3.*

### MA-1 · DOĞRU · yüksek · §6.4.3 (satır 1110), §6.1 (satır 955, 995-999), §15.1 A-2 (satır 2713), §14 F2/F7 (satır 2683, 2688) `denetleme_kurulu.yk_uyesi_olamaz`

**Sorun.** Kuralın yürürlüğü 31.10.2026'da, kullanıcı kararının günü başlıyor. `kural(id, tarih)` olayın tarihine
bakar (satır 995-997). Organ üyeliğinin olayı genel kuruldaki seçimdir. 2026-2027 döneminin genel kurulu md. 9/1
gereği en geç 31.10.2026'da yapılır. Tasarımın F2 kapısı ve F7'deki paralel beta da tam bu dönem üzerinden yürür.
Bu dönemde, 31.10.2026'dan önceki her geriye dönük girişte olduğu gibi, kural yürürlükte görünmez. Bu iki sonuçtan
birini doğurur:
- Değer bulunamadığı için yazma kapanır (fail-closed, satır 998-999).
- Aynı kişi hem YK'ye hem DK'ye kaydedilir.

Her iki durumda da kullanıcının "sert" kararı ilk gerçek dönemde işlemez.

Yöntem de tutarsız. Aynı türden bir kullanıcı kararı kuralı olan `yonetim_kurulu.okul_muduru_uye_olamaz` 01.12.2023'te
başlıyor (satır 1084).

İkinci kusur atıfta. `madde` = md. 14/4 ve `atif` ekranda "md. 14/4" diye basılır (satır 997). Oysa md. 14/4 bu yasağı
söylemez; Not sütunu da "dayanak lafız değil" diyor. Satırda `yorum` alanı yok, bu yüzden arayüz sert engeli
Yönetmelik hükmü gibi gösterir. Altın kural 1'e göre doğrulanamayan hüküm arayüze girmez.

**Doğrulama.**
- md. 14/4 (`meb-okul-aile-birligi-yonetmeligi.md#madde-14`, fıkra 4): "Denetleme kurulu, yılda en az iki defa
  yönetim kurulunun faaliyetlerini inceler…". YK üyeliğiyle bağdaşmazlık hükmü yok. md. 12 ve 14'ün başka hiçbir
  fıkrasında da yok.
- md. 9/1: genel kurul "her yıl en geç Ekim ayının sonuna kadar" toplanır.
- Tasarım §14: F2 kapısı "Pilot okulun 2026-2027 genel kurul akışı", F7 "2026-2027 dönemine **paralel** beta".
- §15.1 A-2 ve plan §1.8 (satır 239) "dayanak aranmaz, kullanıcı kararı" diyor. Yürürlüğün karar günüyle
  başlaması gerektiğine dair bir karar yok.

**Düzeltme.**
- `yururluk.baslangic` 01.12.2023 olmalı. Bu, md. 14/1'in bugünkü lafzının tarihidir ve
  `okul_muduru_uye_olamaz` ile aynı yöntemdir.
- `yorum` alanı şöyle yazılmalı: "Yönetmelikte açık yasak yok; kullanıcı kararı 31.10.2026 (§15.1 A-2). md. 14/4
  gerekçedir, dayanak değildir."
- Aynı biçim KE-15 gereği `okul_muduru_uye_olamaz` için de yazılmalı.
- Şemaya `dayanak_turu` alanı (`lafiz` · `yorum` · `kullanici_karari`) eklenmeli. `atif` metni buna göre
  "kullanıcı kararı (md. 14/4 gerekçe)" diye basılmalı.
- Test `dk::test_ekim_2026_genel_kurulunda_da_gecerli` eklenmeli: genel kurul 15.10.2026'daysa engel sert olmalı.

### MA-2 · DOĞRU · yüksek · §6.1 (satır 959-964), §6.4.11 (satır 1270-1275) ↔ §2 F0-b (satır 81)

**Sorun.** §6.1, sert türe üçüncü bir gerekçe ekliyor: "değeri hesapta kullanılan parametre". §6.4.11 23 sert kuralı
buna dayandırıyor ve dağılımı "altın kural 3'ün üç gerekçesi" diye sunuyor. Oysa altın kural 3'te iki gerekçe var:
hesap bütünlüğü ve hukuken geçersiz işlem (suç ya da hısımlık engeli, OLUR). Tasarımın kendi §2 F0-b satırı da yalnız
bu ikisini sayıyor. Plan §1.8'de ve §15.1'de parametreler için bir kullanıcı kararı yok.

OYS envanteri S-23 üç engeli F0-8'e açık bırakmıştı: serviste muhammen bedel, ikili kriter, TÜFE'nin yalnız kirada
uygulanması. Tasarım bu kategoriyle üçünü de kullanıcıya sormadan sert yapmış.

Sorun yalnız etiket değil. Sert türün tanımı "program kuraldan sapan kaydı kaydetmez" (satır 959). Bu tanım sözleşme
ve kayıt parametrelerine uygulanınca gerçekte olan şeyler kaydedilemez:
- teminatı %6 olmayan bir sözleşme (`kira.kesin_teminat_oran`),
- 9 ya da 12 dışında bir ay sayısı (`kira.ay_sayisi`) ve yarıyıl çarpanı (`kira.yariyil_ayi_carpani`),
- TÜFE'den farklı uygulanmış bir kira artışı (`kira.tufe_artisi`),
- pazarlık dışında bir usulle yapılmış kiralama (`kantin.kiralama_usulu`),
- tahliye cezası (`kira.tahliye_gunluk_ceza_oran`).

Arz ve pay oranlarında (7 kural) kiracının bankaya yatırdığı gerçek tutar hesaptan saparsa ne olacağı tanımsız.
K1 kararı işlem düzeyinde kayıt ve banka eşlemesi istiyor; bir banka hareketi reddedilemez. EK-3 puanlaması ve
personel kuralları ayrıca MA-5 ve MA-3'te ele alındı.

**Doğrulama.**
- CLAUDE.md satır 54-59: "Sert engel yalnız hesap bütünlüğünde (toplamlar, numara tekilliği, kapanmış dönem, yeter
  sayı hesabı) ve mevzuatın hukuken geçersiz saydığı işlemlerde: … Eksik belge, taksit sayısı, puan sınırı gibi
  sapmalar uyarı + gerekçedir."
- Tasarım satır 81 (F0-b) aynı iki gerekçeyi sayıyor.
- grep: "hesap parametresi" ifadesi `docs/` altında yalnız tasarımın 959, 964 ve 1272. satırlarında geçiyor.
- `docs/kesif/2026-10-31-oys-oab-envanteri.md:748` (S-23) açık soruyu kaydediyor.

**Düzeltme.** İki yoldan biri seçilmeli.
- (a) §15.1'e tek bir soru eklenir: "Değeri hesapta kullanılan parametreler sert mi?" Kullanıcı evet derse karar
  altın kural 3'e ve F0-b'ye yazılır.
- (b) Kurallar yeniden sınıflanır. Paket değerleri zaten salt okunur (satır 926-927, 1026-1027); "parametre
  değiştirilemez" demek için sert tür gerekmez. Bu 23 kural `uyari` olur: program yasal tutarı hesaplar, sözleşmede
  ya da bankada görünen gerçek değeri kaydeder, sapmayı uyarı + gerekçe olarak tutar. Sert tür yalnız iç tutarlılık
  denetiminde kalır: pay tablosunun toplamı 1,00 olmalı (D5) ve kuruş artığı (KE-3).

İki grupta tür pratikte etkisizdir, ama yine de doğru etiketlenmeli:
- yalnız uyarı kurallarına girdi veren hesap yardımcıları (`kira.yirmi_yil_*`),
- kayıtta karşılığı olan bir alanı bulunmayan kurallar (`servis.ucret_tarifesi`, `vergi.damga_harc_muafiyeti`,
  `kantin.kdv_istisnasi`, `personel.sgk_saklama_yil`).

§6.4.11'deki sayımlar ve "üç gerekçe" cümlesi seçilen yola göre düzeltilmeli.

### MA-3 · DOĞRU · yüksek · §6.4.10 (satır 1247, 1249) `personel.yillik_izin_gun`, `personel.ihbar_hafta`

**Sorun.**
1. İzin tablosu 4857 md. 53'teki yaş tabanını atlıyor. 18 ve altı ile 50 ve üstü yaştaki işçinin izni 20 günden az
   olamaz. Kuralın hesapladığı değer bu işçiler için yanlış çıkar. Örneğin 52 yaşında, 2 yıllık bir işçiye 14 gün
   hesaplanır.
2. İki kural da asgari süredir ve sözleşmeyle artırılabilir. Sert ve sabit bir "hesap parametresi" olarak
   kurulduklarında sözleşmede yazan daha uzun izin ya da ihbar süresi kaydedilemez (bkz. MA-2).
3. Basamak sınırları yazılmamış. "5 yıl dahil" 14 günlük, "15 yıl dahil" 26 günlük basamaktadır. Tablodaki
   "1-5 · 5-15 · 15+" yazımı 5. ve 15. yılı belirsiz bırakıyor.
4. İhbar kuralı yalnız belirsiz süreli sözleşmelerde uygulanır; bu koşul yazılmamış.

**Doğrulama.**
- `4857-is-kanunu.md#madde-53`, 4. paragraf a-c: "Bir yıldan beş yıla kadar (beş yıl dahil) olanlara ondört günden,
  … Onbeş yıl (dahil) ve daha fazla olanlara yirmialtı günden, Az olamaz."
- Aynı maddenin 5. paragrafı: "onsekiz ve daha küçük yaştaki işçilerle elli ve daha yukarı yaştaki işçilere
  verilecek yıllık ücretli izin süresi yirmi günden az olamaz."
- 6. paragraf: "… sözleşmeleri ile artırılabilir."
- `#madde-17`, 1. paragraf: "Belirsiz süreli iş sözleşmelerinin…". 3. paragraf: "Bu süreler asgari olup
  sözleşmeler ile artırılabilir."

**Düzeltme.**
- `personel.yillik_izin_gun` değeri bir tablo olmalı:
  - hizmet ≤ 5 yıl → 14 gün,
  - 5 yıl < hizmet < 15 yıl → 20 gün,
  - hizmet ≥ 15 yıl → 26 gün,
  - işçi 18 yaşında ya da altında, veya 50 yaşında ya da üstündeyse en az 20 gün.
- Bu kuralda `karsilastirma: en_az`, tür `uyari` olmalı; atıf "4857 md. 53, 4-6. paragraf".
- `personel.ihbar_hafta` da `en_az` + `uyari` olmalı. `kosul` "belirsiz süreli sözleşme", atıf "md. 17, 2. paragraf
  a-d ve 3. paragraf".
- `pr::test_izin_14_20_26_basamaklari` şu durumları sınamalı:
  - 5. yıl = 14 gün,
  - 15. yıl = 26 gün,
  - 50 yaşında, 2 yıllık işçi = 20 gün,
  - sözleşmeyle verilen 24 gün → uyarısız.

### MA-4 · DOĞRU · yüksek · §6.4.9 (satır 1219), §6.4.11 (satır 1271-1272), §10.3 (satır 2169) `servis.komisyon_karari`

**Sorun.** Kural dört ayrı hükmü tek bir sert kurala bağlıyor:
- kararlar çoğunlukla alınır,
- oylar eşitse başkanın tarafı kabul edilir,
- çekimser kalınamaz,
- muhalif üyenin şerhi zorunludur.

İlk ikisi karar yeter sayısı hesabıdır; sert olabilir. Son ikisi usul hükmüdür. Altın kural 3'ün hiçbir sert
gerekçesine girmez; plan §1.8'de de bunlar için kullanıcı kararı yok.

Bu iki hüküm sert kalırsa, komisyonda gerçekten çekimser oy verilmişse ya da muhalif üye şerh yazmamışsa tutanak
programa olduğu gibi girilemez (`sv::test_cekimser_oy_kaydedilemez`, `test_muhalif_serhi_zorunlu`). Kullanıcı ya
gerçeği değiştirerek kaydeder ya da hiç kaydedemez. Altın kural 3 tam bu sonucu önlemek için var.

**Doğrulama.** U-E md. 4/1 (`okul-servisi-calistirma-usul-esaslari.md#madde-4`): "komisyon kararları çoğunlukla
alınır. Oyların eşit olması hâlinde başkanın bulunduğu taraf çoğunlukta kabul edilir. Kararlarda çekimser kalınamaz.
Muhalif kalan üye karşı oy gerekçesini kararın altına yazarak imzalamak zorundadır." CLAUDE.md satır 54-59'a göre sert
engel yalnız yeter sayı hesabında ve suç, hısımlık ya da OLUR hâlinde kullanılır.

**Düzeltme.** Kural ikiye bölünmeli; kimlikler henüz yayımlanmadığı için bu mümkün.
- `servis.komisyon_karar_cogunlugu` sert kalır: çoğunluk ve eşitlikte başkanın tarafı.
- `servis.komisyon_cekimser_ve_serh` uyarı olur: çekimser oy ya da şerhsiz muhalif varsa uyarı + gerekçe.

Testler `sv::test_cekimser_oy_gerekceyle_kaydedilir` ve `sv::test_serhsiz_muhalif_uyari` olmalı. §6.4.11'deki
"servis komisyon kararı" sayımı güncellenmeli.

### MA-5 · DOĞRU · yüksek · §6.4.9 (satır 1221-1222), §10.3 (satır 2171), §10.4 (satır 2202, 2241) ↔ §12 (satır 2485) `servis.ek3_puanlama`

**Sorun.** `servis.ek3_puanlama` sert tanımlanmış ("kademe değerleri değiştirilemez"). §10.4 de
`test_ikili_kriter_yalniz_0_veya_max` testini OYS'den **AYNEN** alıyor. Bu, kademe dışı bir puanın kaydedilemeyeceği
anlamına gelir.

Oysa kullanıcı "puan sınırı" sapmasını uyarı yaptı (plan §1.8, CLAUDE.md altın kural 3). Tasarımın §12'si de aynı testi
"kademe dışı puan uyarı" diyerek UYARLA'ya geçiriyor. Belge kendi içinde çelişiyor.

Sonuç da tutarsız:
- azamiyi aşan 6 puan gerekçeyle kaydedilir (`ek3_kriter_azami_puan` uyarı türünde),
- ama 4. kritere verilen 3 puan sert engele takılır.

Test adı da yanıltıcı. EK-3'te ikili olan yalnız 4. kriter. 2. kriter 5 ya da 1, 3. kriter 5, 3 ya da 0 puan alır.

**Doğrulama.**
- U-E EK-3 (`#ek-3`): kriter 2 "Özmal olması durumunda 5 puan, Kiralık olması halinde 1 puan"; kriter 3 "İlçe …
  5 puan, İl … 3 puan"; kriter 4 "5 puan".
- Tasarım satır 2485: "`test_ikili_kriter_yalniz_0_veya_max` (kademe dışı puan uyarı)", sınıfı UYARLA.
- Aynı test satır 2241'de ve 2171'de AYNEN.
- Envanter S-23 (`oys-oab-envanteri.md:748-750`) "ikili kriter"i açık bir sert engel olarak listeliyor.

**Düzeltme.**
- `servis.ek3_puanlama` tablo verisi olarak kalmalı, ama kademe dışı puan girişi `uyari` olmalı ve gerekçeyle
  kaydedilmeli.
- Test, UYARLA sınıfında `sv::test_kademe_disi_puan_uyari[kriter_4]` olmalı.
- 2. ve 3. kriterin ara değerleri (1 ve 3) için uyarısız bir test eklenmeli.
- §10.4'teki sayım AYNEN 30 · UYARLA 39 · ALMA 2 olmalı; bu, §12'deki sınıflamayla da uyumludur.

### MA-6 · DOĞRU · yüksek · §6.4.8 (satır 1185), §10.3 (satır 2139) `kantin.istekli_belge_sarti`

**Sorun.** Değer "20/4 belgelerinden biri" olarak yazılmış. Oysa md. 20/4 iki kademeli:
- **Birinci kademe:** kantin işletmeciliğinden alınmış ustalık ya da iş yeri açma belgesi.
- **İkinci kademe:** alan ya da dal ustalık ve iş yeri açma belgesi, diploma, kalfalık belgesi, kurs bitirme belgesi.
  Bunlar **yalnız isteklilerin hiçbirinde** birinci kademe belge yoksa geçerlidir.

Kural bu iki kademeyi düzleştiriyor. Birinci kademe belgesi olan bir istekli varken diplomayla katılan istekli için
program uyarı üretmez. OYS'deki tek mantıksal alan da kademeyi taşımıyordu (envanter satır 412). Tasarım sert → uyarı
dönüşümünü yapmış, ama değeri düzeltmemiş.

**Doğrulama.** md. 20/4 (`#madde-20`, fıkra 4; Değişik 01.12.2023): "… kantin işletmeciliğinden alınmış ustalık
belgesine veya kantin işletmeciliğinden alınmış iş yeri açma belgesine sahip olma şartı aranır. Ancak isteklilerin
hiçbirinde yukarıda sayılan belgelerin bulunmaması durumunda … şartı aranır." G.2024/35 (`#degisiklikler`) iş yeri
açma belgesinin ustalık belgesiyle "aynı önceliğe" alındığını söylüyor; demek ki öncelik sırası bilinçli konmuş.

**Düzeltme.** Değer şöyle olmalı:

```json
{
  "birinci_kademe": ["kantin_ustalik", "kantin_isyeri_acma"],
  "ikinci_kademe": ["(20/4'ün ikinci cümlesindeki belgeler)"],
  "ikinci_kademe_kosulu": "hiçbir istekli birinci kademe belge taşımıyor"
}
```

Uyarı iki durumda çıkmalı: istekli hiç belge taşımıyorsa, ya da birinci kademe belgeli bir istekli varken başka bir
istekli ikinci kademe belgeyle katılıyorsa. Testler `kn::test_birinci_kademe_varken_diploma_uyari` ve
`kn::test_hicbirinde_birinci_kademe_yoksa_diploma_uyarisiz` olmalı.

### MA-7 · DOĞRU · orta · §6.2-2 (satır 1008), §6.4.11 DOĞRULANMADI-14 (satır 1295), §5.2.2 (satır 666, 673) ↔ plan §2.3 (satır 287-290) `harcama.alim_komisyonu_*`, kantin denetim temsilcisi, divan

**Sorun.** §6.2-2, r1'i "plan §2.3'teki liste + organ ve temsilci kuralları" diye tanımlıyor. r1 bu tanımı üç yerde
karşılamıyor.
- **(a) Alım komisyonu.** Plan §2.3'ün F1c organlarında "alım komisyonu (en az 3, md. 18/1)" var ve `ALIM_KOMISYONU`
  organ türü F1c'de açılıyor (satır 666). Buna karşın `harcama.alim_komisyonu_en_az` ve `_uyeleri` F4'te giriyor.
  F1c'de kurulan komisyon kural denetimi olmadan kalır. Sapma "F1 eki" olarak da yazılmamış.
- **(b) Kantin denetim temsilcisi.** Plan §2.3 temsilciler arasında "kantin denetim"i sayıyor. Tasarım bunu
  DOĞRULANMADI-14'e koymuş. Oysa sorun dayanağın yokluğu değil, korpusta çapa eksikliği: Genelge 2020/8'in metni
  korpusta duruyor ve hükmü açık. Tasarım "BENIOKU §6'ya işlenir" diyor, ama BENIOKU §6'da böyle bir satır yok.
- **(c) Divan.** `DIVAN` organı da F1c'de açılıyor (satır 666), ama `genel_kurul.divan_uye_turleri` F2'de giriyor.

**Doğrulama.**
- `okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md`, A-1/a ve A-1/b: "… okul aile birliği
  yönetiminden 1 (bir) velinin katılımı ile oluşturulan komisyonca her ay gerçekleştirilir."
- grep: dosyada hiç `<a id>` yok.
- `BENIOKU.md` §6'da Genelge 2020/8 satırı yok.
- Plan satır 288-289.

**Düzeltme.**
- F0 içinde Genelge 2020/8'e A-1/a ve A-1/b çapaları eklenmeli. BENIOKU §2 çapaların değiştirilmesini yasaklar,
  eklenmesini yasaklamaz. BENIOKU §4'e de not düşülmeli.
- Ardından `temsilci.kantin_denetim_komisyonu` (birlik yönetiminden 1 veli) r1'e, `kantin.denetim_aylik` F5'e
  girmeli.
- Alım komisyonu kuralları için iki yol var: ya r1'e alınmalı, ya da §6.2-2'deki cümle düzeltilip sapma plan §2.3'e
  "F1 eki" olarak işlenmeli. Divan için de aynısı yapılmalı.

### MA-8 · DOĞRU · orta · §6.4.7 (satır 1168, 1175), §6.4.5 (satır 1140) `kira.ay_sayisi`, `etkinlik.ders_saatleri_disinda`, `arz_bedeli.takip_sorumlulari`

**Sorun.** Üç kuralda asıl atıf, kuralın değerini ya da kapsamını taşımıyor.
- **`kira.ay_sayisi`** ("9 ya da 12", asıl atıf md. 19/3, yürürlük 09.02.2012). md. 19/3 "dokuz" demiyor. Yaz ve
  yarıyıl tatili dışındaki açık günleri ve tam yıl için on iki ayı söylüyor. "Dokuz ay; Haziran, Temmuz, Ağustos yok"
  yalnız EK-2 md. 4'te, yani 01.12.2023 tarihli metinde geçiyor.
- **`etkinlik.ders_saatleri_disinda`** ("gelir getirici etkinlik ders saatleri dışında", md. 15/1-c). 15/1-c bir gelir
  kaynağı tanımıdır ve **üçüncü kişilerin** okulda düzenlediği etkinlikleri anlatır. Birliğin kendi etkinlikleri için
  bağlayıcı metin SEY 5/3'tür: etkinlikler "öncelikle ders saatleri dışında" yapılır, "zorunlu hâllerde ders
  saatleri içinde de" yapılabilir. Genel bir uyarı, birliğin ders saatindeki meşru bir etkinliği için yanlış uyarı
  üretir.
- **`arz_bedeli.takip_sorumlulari`** (17/1-b-5). Hüküm bent (b)'nin, yani işletme hâlinin altında. Kiraya verme
  hâlinde uygulanması, KE-17'nin 17/1-b-4 için yaptığı yorumun aynısıdır; ama burada yorum olarak işaretlenmemiş.

**Doğrulama.**
- md. 19/3 (`#madde-19`, fıkra 3).
- EK-2 md. 4 (`#genel-sartlar-madde-4`): "Okulların tatil olduğu dönemde (Haziran, Temmuz ve Ağustos ayları)
  işletilmeyen yerler için dokuz ay".
- md. 15/1-c (`#madde-15`): "Kamu kurum ve kuruluşları, özel hukuk tüzel kişilikleri ve gerçek kişilerin … saatler
  dışında gerçekleştirecekleri … etkinliklerinden sağlanan gelirlerden".
- SEY 5/3 (`meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md#madde-5`).
- md. 17/1-b-5 (`#madde-17`).

**Düzeltme.**
- `kira.ay_sayisi`: asıl madde EK-2 md. 4, ek madde md. 19/3, yürürlük 01.12.2023 olmalı.
- Etkinlik kuralına `kosul: {düzenleyen: üçüncü_kişi}` eklenmeli. Birlik etkinliğinde uyarı çıkmamalı; SEY 5/3 bilgi
  notu olarak kalmalı. Testler `ml::test_ucuncu_kisi_etkinligi_ders_saatinde_uyari` ve
  `ml::test_birlik_etkinligi_ders_saatinde_uyarisiz` olmalı.
- Takip kuralına `yorum` eklenmeli: "bent (b)'de; kiraya vermede de uygulanır, KE-17 gibi".

### MA-9 · DOĞRU · orta · §6.4.7-6.4.8 (eksik satırlar) — kantin

**Sorun.** Korpusta sayısal dayanağı olan üç kantin hükmü tabloda yok.
- **Fesih tazminatı.** md. 22/4 ve EK-2 md. 22'nin 2. paragrafına göre, sayılan fesih hâllerinde üç şey olur: kesin
  teminat gelir kaydedilir, cari kiralama döneminin (9 ya da 12 aylık) kira bedeli tazminat olarak alınır ve sonraki
  döneme ait alınmış kira tazminata mahsup edilir. Program bu tazminatın arzını zaten hesaplıyor
  (`arz_bedeli.diger_tahsilat_oran`, satır 1169), ama tazminatın kendi tutarını veren bir kural yok.
- **Bakanlık tahliyesi.** EK-2 md. 18: tebligattan sonra 15 gün içinde tahliye.
- **Pay dağıtım komisyonu.** md. 17/1-b-3: il/ilçe hesabındaki paraları dağıtan komisyonda iki birlik başkanı
  bulunur. Birlik başkanı bu komisyona seçilirse bu bir temsilci kaydıdır; şu an temsilci listesinde yok.

**Doğrulama.**
- md. 22/4 (`#madde-22`, fıkra 4): "… kesin teminatı gelir kaydedilir ve cari yıl/ay kira bedeli tazminat olarak
  tahsil edilir. … alınan kira bedeli öncelikle kiracıdan alınacak tazminata mahsup edilir."
- EK-2 md. 22 (`#genel-sartlar-madde-22`, 2. paragraf): "cari kiralama dönemine ilişkin (9 aylık veya 12 aylık) kira
  bedeli tazminat olarak tahsil edilir".
- EK-2 md. 18 (`#genel-sartlar-madde-18`).
- md. 17/1-b-3 (`#madde-17`).

**Düzeltme.** Üç kural eklenmeli ve 146'lık sayıma katılmalı.
- `kira.fesih_tazminati`: cari dönem kirası (`kira.ay_sayisi`na göre), kesin teminatın gelir kaydı ve mahsup. Asıl
  madde 22/4, ek madde EK-2 md. 22 2. paragraf; giriş F5.
- `kira.bakanlik_tahliye_gun` (15): uyarı, bilgi düzeyinde.
- `temsilci.pay_dagitim_komisyonu`: uyarı, yalnız kayıt; dayanak md. 17/1-b-3.

### MA-10 · DOĞRU · orta · §6.4.9 (eksik satırlar; satır 1234 ve 1236 notları) — servis

**Sorun.** Korpusta sayısal dayanağı olan bazı servis hükümleri ya tabloda hiç yok ya da yalnız Not sütununda duruyor.
Not sütununda kalan değer pakete girmez ve koda sabit olarak gömülür; bu D8'e aykırıdır. Eksik hükümler:
- **Araç yaşının hesap yöntemi.** Yaş, imal tarihinden sonraki ilk takvim yılı taban alınarak hesaplanır. Bu olmadan
  `servis.arac_yasi_en_fazla` testindeki 12/13 sınırı keyfî kalır.
- **B sınıfında geçen sürenin sayılması** (OSAY 9/5, Ek 19.08.2025). D sınıfı için en fazla 1 yıl, D1 sınıfı için en
  fazla 3 yıl sayılır. Şu an yalnız Not sütununda.
- **Tüzel kişide tescil oranı.** Araçların en az üçte biri tüzel kişi adına tescilli olmalı (OSAY 8/3, U-E 6/1-ç,
  EK-1 md. 7/f).
- **Öz mal sınırı.** Tüzel kişi aracı en fazla iki okulda öz mal gösterilebilir (U-E EK-1 md. 6/ç).
- **Fesih ihtarı.** Taşımacı yükümlülüğünü yazılı bildirimden sonra 15 gün içinde yerine getirmezse sözleşme
  feshedilir (U-E 11/1-ç). Kantindeki karşılığı `kira.fesih_ihtar_gun` tabloda var.
- **Oda kaydı belgesinin tarihi.** Belge "işin yapıldığı yıl içinde" alınmış olmalı (U-E 6/1-b, c).

**Doğrulama.**
- OSAY 4/1-f (`okul-servis-araclari-yonetmeligi.md#madde-4`): "Taşıtların yaşı fabrikasınca imal edildiği tarihten
  sonra gelen ilk takvim yılı esas alınarak hesaplanacaktır."
- OSAY 9/5 (`#madde-9`): "D sınıfı … en fazla 1 yılı, … D1 sınıfı … en fazla 3 yılı".
- OSAY 8/3 (`#madde-8`, Değişik 19.08.2025): "en az üçte birinin tüzel kişilik adına tescilli olması zorunludur".
- U-E `#ek-1-madde-6` (ç): "en fazla iki okulda öz mal olarak gösterilir".
- U-E `#madde-11` (1/ç): "on beş gün içinde".
- U-E `#madde-6` (1/b, c).

**Düzeltme.** Altı kural eklenmeli; hepsi uyarı türünde ve F6'da:
- `servis.arac_yasi_hesabi`: model yılı + 1 taban,
- `servis.sofor_b_sinifi_sayilan_yil`: {D: 1, D1: 3}, yürürlük 19.08.2025,
- `servis.tuzel_kisi_tescil_orani`: 1/3,
- `servis.ozmal_en_fazla_okul`: 2,
- `servis.fesih_ihtar_gun`: 15,
- `servis.oda_belgesi_ayni_yil`.

`sv::test_belge_ve_yas_sinirlari` testine model yılı + 1 ve B sınıfı sayımı parametreleri eklenmeli.

### MA-11 · KISMEN · orta · §6.4.2 (satır 1083), §5.2.2 (satır 665), §10.3 (satır 2046, 2055) `yonetim_kurulu.uye_turleri`, `genel_kurul.divan_uye_turleri`

**Sorun.** Kuralın değeri md. 12/1 ile aynı: veli, 18 yaşını doldurmuş kursiyer, hayırsever. Ama Not ve test
"öğretmen ve yönetici türü reddedilir" diyor ve `OabPerson.kind` tek değerli (`VELI` · `OGRETMEN` · `IDARECI` …).

Okulda çocuğu okuyan bir öğretmen ya da müdür yardımcısı md. 12/1'e göre velidir ve YK'ye seçilebilir. Kullanıcı
kararı (KE-15) yalnız okul müdürünü dışarıda bıraktı. e-Okul personel aktarımından gelen kişi `OGRETMEN` ya da
`IDARECI` türünde olur. Sert kural bu kişiyi YK'ye sokmaz; divanda da (uyarı türü) yanlış uyarı üretir.

KISMEN, çünkü bir kaçış yolu var: kişi `VELI` türüyle ikinci kez açılabilir. Ama bu yol adaşlık uyarısı doğurur ve
dönem sayacını iki kayda böler.

**Doğrulama.** md. 12/1 (`#madde-12`): "veliler/on sekiz yaşını doldurmuş kursiyerler ile … hayırseverler arasından
seçilen". md. 4/1-f veliyi "öğrencinin annesini/babasını …" diye tanımlıyor; öğretmen olmak veliliği kaldırmaz.
md. 10/1-c (divan) da aynı ölçütü kullanıyor.

**Düzeltme.**
- Uygunluk kişinin işine göre değil, veli olup olmadığına göre denetlenmeli. Bunun için ya `OabPerson`'a `is_parent`
  işareti eklenmeli ya da `kind` çok değerli olmalı.
- Not şöyle düzeltilmeli: "Veli olmayan öğretmen ve idareci reddedilir; okul müdürü veli olsa da reddedilir (KE-15)."
- Test `yk::test_veli_olan_ogretmen_yk_ye_eklenebilir` eklenmeli.

### MA-12 · KISMEN · orta · §6.1 (satır 955, 995-997), §6.4.7-6.4.8 (EK-2 ve md. 21 kaynaklı kurallar), §14 F5 (satır 2686)

**Sorun.** EK-2'ye ve md. 21'e dayanan kantin kurallarının yürürlüğü 01.12.2023'te başlıyor. Örnekler:
`kira.kesin_teminat_oran`, `kira.odeme_gunleri`, `arz_bedeli.sozlesme_vade_gunu`, `kira.yer_teslimi_gun`,
`kira.sozlesme_en_fazla_yil`, `kira.tufe_artisi`. Korpusta eski EK-2 metni yok.

`kural()` olayın tarihine baktığı için, 01.12.2023'ten önce imzalanmış ve hâlâ süren bir sözleşmede sözleşme tarihine
bağlı denetimler (teminat oranı, yer teslimi, süre) yürürlükte bir değer bulamaz. Yönetmelik bu tür sözleşmelerin
varlığını öngörüyor (geçici md. 4); beş yıllık bir sözleşme pekâlâ 2022'de imzalanmış olabilir. F5 kapısı da
"pilot okulun 2026-2027 kantin sözleşmesi" üzerine kurulu.

KISMEN, çünkü servislerin `kural()`'a hangi tarihi geçireceği tasarımda yazılmamış. Ödeme ve kira artışı gibi
2026'daki olaylar bu sorundan etkilenmez.

**Doğrulama.**
- Tasarım satır 955: yürürlük "dayanak fıkranın bugünkü lafzının yürürlüğe girdiği tarih". Satır 995-997:
  "`tarih` verilmezse olayın tarihi … kullanılır".
- EK-2 başlığı "(Değişik:RG-1/12/2023-32386) EK-2"; md. 21 başlığı "(Değişik:RG-1/12/2023-32386)".
- `#gecici-madde-4`: "Bu maddenin yürürlüğe girdiği tarihten önce … sözleşme bitim tarihine kadar devam eder".

**Düzeltme.**
- §6.1'e şu kural yazılmalı: sözleşmeye bağlı kurallar sözleşmenin tarihine değil, denetlenen olayın (ödeme, artış,
  yenileme, teslim) tarihine bakar.
- 01.12.2023'ten önceki sözleşmelerde teminat, ay sayısı ve ödeme günü gibi değerler sözleşme alanından okunmalı.
  Kural yalnız uyarı üretmeli ve "sözleşme tarihindeki EK-2 metni korpusta yok" notunu taşımalı.
- Test `kn::test_2023_oncesi_sozlesme_kaydedilir_ve_uyari_notu` eklenmeli.

### MA-13 · DOĞRU · orta · §6.4 madde sütunu — fıkra ve paragraf eksik

**Sorun.** Altın kural atıfın fıkra ve bent düzeyinde olmasını istiyor; şema da `fikra_bicimi=paragraf` alanını
öngörüyor (satır 950). D4 testi "EK-2 md. 7" ve "4857 md. 17" için paragraf denetimi vaat ediyor (satır 2014). Ama
tablodaki şu atıflar madde düzeyinde kalmış:
- **EK-2 md. 7 (beş paragraf):**
  - 1. paragraf: `arz_bedeli.kira_oran`, `donem_ay`, `sozlesme_vade_gunu`,
  - 2. paragraf: `pay_dagitimi.genel`, `kira.odeme_gunleri`,
  - 3. paragraf: `kira.mucbir_sebep_indirimi`,
  - 4. paragraf: `kira.ust_uste_odememe_fesih`.
- **EK-2 md. 6:** `kira.sozlesme_en_fazla_yil` için beş yıl yalnız 2. paragrafta geçiyor (1. paragrafta süre boş:
  "…. yıl"); `kira.tufe_artisi` 1. paragrafta.
- **EK-2 md. 22 (üç paragraf):** `kira.tahliye_gunluk_ceza_oran` 1. paragrafta.
- **4857 md. 53, 56 ve 17 (`personel.*`):** paragraf ve bent yok (bkz. MA-3).
- **2886 md. 84** (`kira.ihaleden_yasaklama_yil` ek atfı): paragraf yok.
- **`vergi.damga_harc_muafiyeti`:** atıf yalnız "[24]", fıkra yok.

**Doğrulama.** Paragraf yapıları korpusta görülüyor:
`meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-6`, `-7` ve `-22`;
`4857-is-kanunu.md#madde-53` ve `#madde-17`. md. 24 (`#madde-24`) yalnız (1) fıkrasını taşıyor.

**Düzeltme.** Tabloya paragraf ve bentler yazılmalı; örneğin "EK-2 md. 7/1. paragraf", "4857 md. 53/4. paragraf a-c",
"md. 24/1". D4 testi her satırda fıkra ya da paragraf alanını zorunlu tutmalı: `fikra` boşsa ve madde tek fıkralı
değilse test kırmızı olmalı.

### MA-14 · DOĞRU · orta · §6.3 D4 (satır 1036), §10.2 (satır 2014)

**Sorun.** Atıf kilidi yalnız fıkranın "(Mülga:" ile başlamasını yakalıyor. Korpusta aynı sonucu doğuran başka
şerhler de var ve hiçbiri yakalanmıyor:
- bent düzeyinde mülga,
- Danıştay yürütmeyi durdurma şerhi (OSAY 5/2-b; EK-2 Özel Şartlar md. 1'deki ibare),
- Danıştay iptal şerhi (OSAY 5/2-d'nin 2025 öncesi hâli; OSAY 15/4'teki "iptal ibare").

Bugün bunlara dayanan bir kural yok. Ama kilidin işi, gelecekteki bir revizyonda böyle bir atıfı engellemek.
`test_mulga_fikraya_atif_yakalanir` ise yalnız md. 20/10'u sınıyor.

**Doğrulama.**
- `okul-servis-araclari-yonetmeligi.md#madde-5`, 2/b: "(Danıştay Sekizinci Dairesinin 2/2/2022 tarihli … kararı ile
  yürütmesi durdurulan bent: …)".
- Aynı maddenin 2/d bendi: "(… iptal bent) (Yeniden Düzenleme:RG-19/8/2025-32991)".
- EK-2 `#ozel-sartlar-madde-1`: "yürütmesi durdurulan ibare".

**Düzeltme.** D4 şu üç durumda kırmızı vermeli:
1. Atıf yapılan bent ya da alt bent "(Mülga" ile başlıyorsa.
2. Atıf yapılan bent ya da fıkra "yürütmesi durdurulan" ifadesini içeriyorsa.
3. "iptal bent" ya da "iptal ibare" geçiyor ve ardından "(Yeniden Düzenleme:" gelmiyorsa.

Testler `kp::test_yd_bende_atif_yakalanir` (OSAY 5/2-b) ve `kp::test_yeniden_duzenlenen_iptal_bent_gecer`
(OSAY 5/2-d) eklenmeli.

### MA-15 · DOĞRU · orta · §10.1 (satır 2001), §10.3 — test eksikleri

**Sorun.**

(a) §10.1, eşikli kurallarda "sınırın iki yanı"nın sınanacağını söylüyor. Ama şu testler yalnız ihlal tarafını
sınıyor:
- YK toplantı yeter sayısı (yalnız 3) ve karar yeter sayısı (yalnız 2),
- alım komisyonu (yalnız 2 kişi), %10 başvuru (yalnız altı),
- kira ödeme günü (yalnız 16; 4'ü yok), yer teslimi (yalnız 16), öğrenci sayısı değişimi (%25), kantin ve servis fesih
  ihtarı,
- sözleşme imzası (10 gün), taksit (yalnız 10), izin bölümü (yalnız 9 gün),
- öğretmen görevlendirmesi (4 ay), şoför yaşı (yalnız 66; 26 alt sınırı yok).

(b) Bazı testler kuralın dediğini sınamıyor:
- `genel_kurul.secim_bicimi` (satır 2047) yalnız DK öğretmen koltuğuna bakıyor; "liste hâlinde, açık oy" sınanmıyor.
- `uyelik.suc_engeli_beyani` (satır 2062) yalnız alanın biçimine bakıyor; beyan yoksa uyarı çıktığı sınanmıyor.
- `kantin.calisan_niteligi` (satır 2143) yalnız ters notu sınıyor; belgesi olmayan çalışana uyarı çıktığı sınanmıyor.
- `kantin.hisimlik_derecesi` (satır 2141) 2./3. derece sınırını ve kayın hısımlığını sınamıyor.
- `bagis.kayit_doneminde_toplanmaz` (satır 2091) diploma dönemini sınamıyor.

(c) `kira.yirmi_yil_ilave`: 16.03.2020 ile 06.09.2021 arasındaki tarih farkı 539 gün. Genelge iki ucu da sayarak
540 diyor. Test sabit 540'ı sınamalı; değer tarih çıkarmasıyla hesaplanırsa bir gün eksik çıkar.

**Doğrulama.**
- md. 13/3: "en az dört üyenin … karar yeter sayısı üçtür".
- md. 20/8: "ikinci dereceye kadar kan ve kayın".
- G.2011/40 madde 1: "kayıt-kabullerinde ve diploma verilirken".
- G.2024/35 `#bolum-iii-4`: "(540 gün)".
- Tarih farkı: `date(2021,9,6) - date(2020,3,16)` = 539 gün.

**Düzeltme.**
- Her eşik için uyarısız taraf eklenmeli. Örnekler: `yk::test_4_katilimla_toplanti_gecerli`,
  `yk::test_3_kabul_oyuyla_karar_alindi`, `ml::test_uc_kisilik_komisyon_uyarisiz`,
  `pd::test_kira_4unde_uyari_5inde_uyarisiz`.
- (b)'deki kurallar için çekirdek testler eklenmeli: `kn::test_ucuncu_derece_hisim_katilabilir`,
  `kn::test_kayin_hisim_ikinci_derece_engel`, `ml::test_diploma_doneminde_bagis_uyari`,
  `kn::test_belgesiz_calisan_uyari`, `yk::test_beyansiz_uyeye_uyari`, `gk::test_secim_liste_ve_acik_oy`.
- `kn::test_540_sabit_tarih_farkindan_hesaplanmaz` eklenmeli.

### MA-16 · DOĞRU · düşük · §6.4 — işaretsiz yorumlar ve değer eksikleri

**Sorun.** Bazı değerler lafzın ötesine geçiyor ama `yorum` alanıyla işaretlenmemiş; şema bunu istiyor (satır 957):
- **"her yıl" → "12 ay":** `kantin.yillik_yenileme` (20/7, 23/4) ve `servis.saglik_raporu_ay` (OSAY 9/1-c, 9/2-ç).
- **`genel_kurul.gundem_degisikligi`:** md. 9/4 yalnız "ekleme ve çıkarma" diyor; kurala "sıra değişikliği"
  eklenmiş. Yorumun sert bir kuralda olması ayrıca sorunlu: oylanmadan yapılmış bir sıra değişikliği kaydedilemez.
- **`genel_kurul.ikinci_toplanti_en_gec_gun`:** sürenin "birinci toplantı gününden" başladığı yorum.
- **`genel_kurul.yeter_sayi_taban`:** üye sayısı fiilî üye olarak değil, kadro (16) olarak okunmuş.
- **`bagis.elden_yatirma_is_gunu`:** sürenin "kabulü izleyen iş gününden" başladığı yorum.
- **`kira.ust_uste_odememe_fesih`:** lafız "iki defa üst üste" (ödeme sayısı) diyor, değer "2 ay".

Bir de değer eksiği var. `uyelik.ayrilan_veli_devam` yalnız "velinin üyeliği" diyor. md. 7/2'ye 2023'te eklenen ibare
on sekiz yaşını doldurmuş kursiyeri de kapsıyor; kuralın yürürlüğü de zaten 01.12.2023.

**Doğrulama.**
- md. 9/4 (`#madde-9`): "Gündem maddelerine ekleme ve çıkarma yapılarak değiştirilmesinde oy çokluğu aranır."
- md. 7/2 (`#madde-7`): "velilerin (Ek ibare:RG-1/12/2023-32386) /on sekiz yaşını doldurmuş kursiyerlerin üyelikleri
  devam eder."
- md. 20/7: "Her yıl …"; OSAY 9/1-c: "her yıl …".
- EK-2 md. 7, 4. paragraf: "iki defa üst üste ödemeyen".

**Düzeltme.**
- Listelenen satırlara `yorum` alanı yazılmalı.
- `gundem_degisikligi` kuralındaki sıra değişikliği ya ayrı bir uyarı kuralına alınmalı ya da çıkarılmalı.
- `ayrilan_veli_devam` değerine "/18 yaşını doldurmuş kursiyer" eklenmeli.
- `ust_uste_odememe_fesih` kuralının birimi `adet` (ödeme) olmalı.

### MA-17 · DOĞRU · düşük · §6.1 (satır 955) ↔ §6.4 yürürlük sütunu

**Sorun.** Şema yürürlüğü "dayanak fıkranın bugünkü lafzının yürürlüğe girdiği tarih" diye tanımlıyor. Tablo ise iki
yöntemi karışık kullanıyor.
- **Fıkra düzeyi:** Değer daha eski olduğu hâlde fıkradaki şerhin tarihi yazılmış.
  `yonetim_kurulu.asil_uye`/`yedek_uye` ve `denetleme_kurulu.asil_uye`/`yedek_uye` 01.12.2023'te başlıyor; oysa 5+5
  ve 3+3 2012 metninde de var.
- **Değer düzeyi:** Fıkrada şerh olduğu hâlde ilk yayım tarihi yazılmış.
  - `genel_kurul.olaganustu_basvuru_oran` ve `olaganustu_gundeme_baglilik` 09.02.2012; md. 9/6'da 2023 tarihli bir
    Ek ibare var ve %10 aynı cümlede.
  - `harcama.organ_uyesine_odeme` 09.02.2012; md. 25/1'de 10.06.2022 tarihli bir Değişik ibare var.
  - `temsilci.kontenjan_komisyonu` 13.09.2014; OKY 25/1-a'da 08.09.2023 tarihli bir ibare var.
  - `temsilci.odul_disiplin_kurulu` 07.09.2013; OKY 185/1'de 2025 tarihli bir ibare var.
  - `personel.yillik_izin_gun` 10.06.2003; md. 53'te 2014 tarihli bir ek cümle var.
  - `bagis.ayni_teslim` ve `harcama.tasinir_kaydi` 09.02.2012; değerdeki "VİF" TMY'nin 10.10.2024 metninden geliyor.

v1'de bütün olaylar 2023 sonrasına düştüğü için bu karışıklığın hesaba etkisi yok; istisnaları MA-1 ve MA-12. Ama
§6.2-3'teki tarihçe mekanizması, ilk değer değişikliğinde yanlış aralık üretir.

**Doğrulama.** Şerhler korpusta:
- md. 9/6: "(Ek ibare:RG-1/12/2023-32386)",
- md. 25/1: "(Değişik ibare:RG-10/6/2022-31862)",
- OKY `#madde-25`: "(Değişik ibare:RG-8/9/2023-32303)",
- OKY `#madde-185`: "(Değişik ibare:RG-22/2/2025-32821)",
- 4857 `#madde-53`: "(Ek cümle: 10/9/2014-6552/5 md.)",
- TMY `#madde-41`, 2. fıkra.

**Düzeltme.** Satır 955 "değerin bugünkü hâliyle yürürlüğe girdiği tarih" olarak değiştirilmeli; işlevsel olarak
doğru olan budur. Tablo tek yönteme çekilmeli:
- 5+5 ve 3+3 kuralları 09.02.2012,
- `olaganustu_cagiranlar` 01.12.2023 olarak kalır,
- VİF geçen iki kural 10.10.2024.

### MA-18 · DOĞRU · düşük · §10.6 (satır 2283), §6.4.11 (satır 1270, 1274), §6.4.4 (satır 1119, 1121)

**Sorun.** Dört küçük tutarsızlık var.
- §10.6'daki F1 kapısı "`r1`'deki 49 kural" diyor; §6.4.11 ve §14 (satır 2674) 50 diyor. Tablodan yapılan sayım 50:
  GK 8, YK 15, DK 8, temsilci 9, gelir 2, kantin 7, personel 1.
- §6.4.11, `okul_muduru_uye_olamaz`'ı "hukuken geçersiz işlem" grubunda sayıyor. Oysa §15.1 KE-15 "Açık yasak yok …
  yorumu … ve kullanıcı kararı" diyor. Doğru sayım: kullanıcı kararı 2, hukuken geçersiz işlem 5.
- `temsilci.sosyal_etkinlikler_kurulu` notundaki "md. 6/2" belirsiz. Satırın atfı SEY olduğu için SEY 6/2 gibi
  okunuyor; kastedilen OAB Yönetmeliği md. 6/2.
- `temsilci.rpd_yurutme_komisyonu`: RPD 16/5'e göre komisyonun "diğer üyeleri her ders yılı başında öğretmenler
  kurulunda belirlenir". Yani birlik temsilcisini YK kararı değil, öğretmenler kurulu belirler. E01 ve E03'teki YK
  temsilci kararı bu satır için bilgi düzeyinde kalmalı.

**Doğrulama.** Sayım §6.4.1-6.4.10'daki "Giriş" sütununda F1c ile başlayan satırlardan yapıldı. §15.1 satır 2714.
RPD `#madde-16`, fıkra 5.

**Düzeltme.**
- Satır 2283 "50 kural" olmalı.
- §6.4.11 dağılımı düzeltilmeli; MA-2 ile birlikte yeniden yazılması uygun olur.
- SEY satırının notu "OAB Yön. md. 6/2" olmalı.
- RPD satırına ek atıf olarak 16/5 eklenmeli; notu "öğretmenler kurulu belirler, birlik önerir" olmalı.

---

Çürütülen aday: 17
Sınanan kural: 146 / 146

---

## Mevzuat atıfları II — veri modeli, akışlar, aktarım, evrak (15)

> Mercek: `docs/tasarim/2026-10-31-genel-tasarim.md` §3, §5, §7, §8, §9 (satır 219-296, 591-897, 1307-1708, 1709-1973).
> Bu aralıktaki 596 korpus bağlantısının (102 tekil çapa) hepsinin çapası korpusta var; her çapanın yanında yazan fıkra,
> bent ve hüküm korpus metniyle karşılaştırıldı. Rol ve [S]/[U] işaretleri CLAUDE.md K2, plan §1.8, tasarım §4.4.2
> (rol-izin matrisi), §6 (satır 962-964 sert tanımı ve kural tablosu) ve §15.1 kullanıcı kararlarıyla sınandı.
>
> Önem dağılımı: yüksek 7 · orta 7 · düşük 1.

### MB-1 · DOĞRU · yüksek · §7.1 (satır 1336, 1338)

**Sorun.** §7.1, olağanüstü genel kurulda ikinci toplantıyı kapatıyor. İlan geçişinde "olağanüstüde ikinci toplantı
alanı açılmaz (§15 A-1)" yazıyor (satır 1336). Yeter sayı bulunamayınca da "Olağanüstüde: yeni çağrı önerilir (§15
A-1)" diyor (satır 1338). Oysa A-1 bunun tersini karara bağladı. Tasarımın kendi içinde de çelişki var: satır 698,
1339 (`YETER_SAYI_YOK → YAPILDI` "olağan ve olağanüstü"), 1068 (`genel_kurul.ikinci_toplanti_cogunluk_aranmaz`
"Olağan ve olağanüstü GK") ve 2040 (`test_olaganustu_ikinci_toplanti_cogunluksuz`). §7.1 bu haliyle uygulanırsa ikinci
toplantı tarihi davetiyede (E05) basılamaz. Yeni çağrı da yeniden 64/32 yeter sayısı ister; bu, kullanıcı kararını
fiilen geçersiz kılar.

**Doğrulama.** Plan §1.8: "md. 9/2'deki ikinci toplantı olağanüstüde de uygulanır (öneriden farklı)". Tasarım §15.1
A-1 (satır 2709) cevabı "Evet" diye veriyor. Dayanak [md. 9/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) (2.
fıkra son cümle): "en geç otuz gün içinde çoğunluk aranmaksızın toplantı yapılır". Genel OAB seti de (GNL-OAB-FR-002
satır 3, 6) olağanüstü seçeneğinde ikinci toplantı tarihini basıyor.

**Düzeltme.** Satır 1336'daki ibare şöyle değişmeli: "olağanda ve olağanüstüde ikinci toplantı tarihi birinciden en
geç 30 gün sonra [U] (§15 A-1)". Satır 1338'deki "Olağanüstüde: yeni çağrı önerilir" cümlesi silinmeli; yerine
"olağanüstüde de ikinci toplantı (§15 A-1)" yazılmalı. E05 kabul ölçütüne (satır 1896) şu ölçüt eklenmeli:
"olağanüstüde 2. toplantı tarihi basılır".

### MB-2 · DOĞRU · yüksek · §5.2.3 `AgendaItem` (satır 694)

**Sorun.** Veri modeli, olağanüstü genel kurulda çağrı gündemi dışına madde eklemeyi **sert** sayıyor: "md. 9/6
gündeme bağlılık — sert, hukuken geçersiz karar; kural paketi bunu uyarı sayıyor: §6.4.1 ile birleştirmede
eşitlenmeli; §15'e öneri B-13". B-13 ise kullanıcıya soruldu ve karara bağlandı. Model kısıtı kararla, akışla (satır
1340: "[U] (§15 B-13 …)"), kural tablosuyla (satır 1073: `genel_kurul.olaganustu_gundeme_baglilik` U) ve testle
(satır 2045: `test_olaganustu_gundem_disi_madde_uyari`) çelişiyor.

**Doğrulama.** Tasarım §15.1 B-13 (satır 2712): "**Uyarı + gerekçe** — … altın kural 3'ün sert listesi genişlemez".
Plan §1.8 "Gündeme bağlılık (olağanüstü) | Uyarı + gerekçe". [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9)
yalnızca "Gündeme bağlılık ilkesi geçerlidir" diyor. Hüküm yaptırım ya da geçersizlik öngörmüyor; "hukuken geçersiz
karar" nitelemesinin korpusta dayanağı yok.

**Düzeltme.** Satır 694'teki parantez şöyle olmalı: "([md. 9/6] gündeme bağlılık — uyarı + gerekçe, kullanıcı kararı
§15.1 B-13)". "sert, hukuken geçersiz karar" ve "birleştirmede eşitlenmeli" ibareleri silinmeli.

### MB-3 · DOĞRU · yüksek · §9.6 (satır 1886, 1896) + §9.3 (satır 1765, 1773) + §10 (satır 2266)

**Sorun.** Evrak kataloğu, olağanüstü genel kurul çağrısını müdürün ve Denetleme Kurulunun yazamayacağı biçimde
kuruyor. Kullanıcı kararları M-5 ve M-6 ise ikisine de bu yetkiyi veriyor.
- §9.6 giriş cümlesi (satır 1886): "`denetleme_kurulu` yalnız E02, E32, E33'ü; `mudur` yalnız kendi yazılarını (E25,
  E35, yeni okulda E05) üretir".
- E05 satırında (satır 1896) Üreten "sekreter, yonetici; yeni okulda mudur", imza bloğu "Birlik Başkanı (YK adına) +
  Sekreter; Görüldü — Okul Müdürü".
- §9.3'teki müdür listesi (satır 1765) olağanüstü çağrıyı saymıyor.
- §9.3 tablosu (satır 1773) "olağanüstüde çağırana göre" ile "müdür yalnız 'Görüldü'" ibaresini yan yana yazıyor.
- `ev::test_yk_ve_gk_belgelerinde_mudur_yazar_degil` (satır 2266) "E05 (yeni okul hariç)" için müdürü yalnız
  "Görüldü" blokunda arıyor. Müdürün çağırdığı olağanüstü genel kurulda bu test haklı belgeyi kırar.

Bu kurgu uygulanırsa DK, [md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14) çağrısını programda yazamaz. Müdürün
9/6, 13/8 ve 25/2 çağrıları da Başkan + Sekreter imzasıyla basılır; bu yanlış imzacıdır.

**Doğrulama.** Tasarım §15.1 (satır 2710-2711) M-5 "Müdür, olağanüstü genel kurul çağrısını da yazabilsin mi? —
Evet", M-6 "Denetleme Kurulu … denetim modülünden yazabilsin mi? — Evet". Plan §1.8: "Müdür olağanüstü genel kurul
çağrısını, DK md. 14/5 çağrısını programda yazar". K2 (tasarım satır 66) ve rol matrisi dipnotları ¹ ve ³ (satır
472-478) de bunu söylüyor. [md. 9/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-9) ve
[13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13) çağıranları sayıyor ("yönetim kurulu, okul müdürü ve … denetleme
kurulunun çağrısı", "başkan veya okul müdürü tarafından"). GNL-OAB-FR-012 satır 50 DK'nin çağrısını FR-002'ye, yani
E05'e bağlıyor.

**Düzeltme.**
- §9.6 giriş cümlesi şöyle olmalı: "`denetleme_kurulu` E02, E32, E33 ve md. 14/5 hâlinde E05'i; `mudur` E25, E35, E05
  (yeni okulda md. 9/1; olağanüstüde md. 9/6, 13/8, 25/2) ve md. 27/3 MEM bildirimini üretir".
- E05 satırı:
  - Üreten: "… ; olağanüstüde çağırana göre mudur ya da denetleme_kurulu".
  - İmza bloğu: "çağırana göre: Birlik Başkanı (YK adına) + Sekreter · Okul Müdürü (9/1, 9/6, 13/8, 25/2) · DK asıl üyeleri
    (14/5) · %10 başvurusunda KE-11".
- §9.3 satır 1765'teki müdür listesine olağanüstü çağrı eklenmeli. Satır 1773'teki "müdür yalnız 'Görüldü'" ibaresi
  "müdür çağırmadıysa 'Görüldü'" olmalı.
- Test satır 2266'ya istisna yazılmalı: "E05 (yeni okul ve müdürün olağanüstü çağrısı hariç)".
- Yan not (§4, merceğin dışında): §4.4.1'deki `mudur` satırının dayanak sütunu (satır 426) da 9/6, 13/8 ve 25/2'yi
  eklemeli.

### MB-4 · DOĞRU · yüksek · §7.6 (satır 1480, 1484) + §7.7 (satır 1515, 1519-1523) + §7.2 (satır 1372, 1375) + §7.1 (satır 1335)

**Sorun.** §7'deki "Kim" sütunu bazı geçişleri K2'ye ve rol matrisine aykırı rollere veriyor.
- **Müdür, yazma yetkisi olmadığı modüllerde.** §7 "Kim"i "işi asıl yürüten rol" diye tanımlıyor (satır 1311). Buna
  rağmen kantinde `BILDIRILDI` (mudur, yonetici) ve `IMZALANDI → YURURLUKTE` (yonetici, mudur) geçişleri müdüre
  veriliyor. Serviste `HAZIRLIK`, `INCELEME → DEGERLENDIRME`, `DEGERLENDIRME → KOMISYON_KARARI`, `ONAYDA`, `TEBLIG` ve
  `SOZLESME` geçişlerinin hepsinde `mudur` var. Rol matrisinde ise Kantin (M13) ve servis (M14) satırında `mudur` "O"
  (satır 462). KE-19 (satır 2731) "müdür rolüne K2'de yazılanlardan başka yetki eklenmez" diyor. §9.6 de bu belgelerin
  (E40, E43, E44, E48-E57) Üreten'ini `yonetici` yazıyor (satır 1886-1888).
- **YK rolü DK'nin işinde.** §7.2 görev bölümü satırı (satır 1372) DK'nin başkan seçimini ve "DK görev bölümü
  tutanağı"nı `sekreter`e veriyor. E02'nin Üreten'i ise "denetleme_kurulu (üyelik kaydı yonetici)" (satır 1893). Yedek
  çağırma satırı (satır 1375) DK öğretmen yedeğinin çağrısını "sekreter (YK kararıyla)" yürütüyor. Yönetmelik YK'ye
  DK'nin yedeğini çağırma yetkisi vermiyor. Ayrıca A-2'nin ilkesi denetleyen ile denetlenenin ayrılığıdır.
- **Başkan eksik.** md. 13/8'deki çağrıyı başkan da yapabilir. §7.1 olağanüstü satırının "Kim" sütununda (satır 1335)
  `baskan` yok; yalnız "sekreter (YK kararı)" var.

**Doğrulama.**
- K2 (satır 66): müdür "yalnız kendi yazılarını (harcama talebi md. 18/1, uyarı md. 27/3, yeni okulda genel kurul
  daveti md. 9/1, olağanüstü genel kurul çağrısı md. 9/6 …) yazar".
- Plan §1.8 K2 satırları: DK "gelir-gider, karar, üyelik kayıtlarına yazamaz".
- [md. 14/6](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14): "yerlerine yedekleri çağırılır" (edilgen; YK'ye yetki
  yok).
- [md. 13/8](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13): "öncelikle başkan veya okul müdürü tarafından … çağrılır".
- Servis: [U-E md. 3/1-e](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-3) ve
  [4/1](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-4). Müdür komisyonun başkanıdır; ama bu, kâğıt üzerindeki
  sıfattır, program rolü değildir. §9.6 da "kâğıdı müdür imzalar" diyor.

**Düzeltme.**
- §7.6 ve §7.7'de `mudur` geçen Kim hücreleri `yonetici` olmalı; müdürün sıfatı "(kâğıtta Okul Müdürü / Komisyon
  Başkanı imzalar)" notu olarak yazılmalı.
- §7.2 görev bölümü satırı ikiye ayrılmalı:
  - YK görev bölümü → `sekreter`.
  - DK görev bölümü → `yonetici` (üyelik kaydı) + `denetleme_kurulu` (E02).
- Yedek çağırma satırında DK yedeği YK kararından ayrılmalı: "DK yedeği: `yonetici` kaydeder (md. 14/6); YK kararı
  gerekmez".
- §7.1 satır 1335'in Kim sütununa "baskan (md. 13/8)" eklenmeli.

### MB-5 · KISMEN · yüksek · §5.2.9 `Tender`/`TenderApproval` (satır 777, 779) + §7.6 (satır 1482)

**Sorun.** Kantin kiralamasında "Onay `OLUR` olmadan `KESINLESTI` olmaz — sert" kuralı dayanaksız. Tasarımın kendisi
"kantinde onay makamı korpusta bulunamadı — DOĞRULANMADI, makam elle girilir" diyor. Kural paketinde de karşılığı yok:
§6'da yalnız `servis.olur_olmadan_kesinlesmez` var (satır 1223), kantin için onay kuralı ya da çapa yok. §6'nın sert
tanımı (satır 962-964) "mülki amir onayı olmadan kesinleştirme" diyor; ama mülki amir onayı servisin kavramıdır,
kantinde onay makamı belirsiz. Kural paketi dışında, çapasız bir sert engel altın kural 1'e aykırı: "doğrulanamayan
hüküm koda girmez". Kural ayrıca §3.2'deki atıf kilidinin de dışında kalıyor.

**Doğrulama.**
- [Genelge 2024/35 I-8](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-i-8) ve
  [II-5](../mevzuat/okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md#bolum-ii-5): "Komisyon tarafından ihale süreci
  tamamlanıp işletmeci tespit edildikten sonra işletmeci ile okul aile birliği arasında kiralama sözleşmesi imzalanır".
  Arada onay adımı yok.
- Korpustaki [2886](../mevzuat/2886-devlet-ihale-kanunu.md#madde-51) dosyasında yalnız md. 51, 75, 83, 84 var. İhale kararının
  ita amirince onayı md. 40'tadır ve korpusta değildir.
- [md. 29](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-29) hüküm bulunmayan hâlde 2886'yı uygular. Yani onay büyük
  olasılıkla gerçekten vardır; ama korpusta kanıtı yok. "KISMEN" bu yüzden.
- Plan §1.8'deki "OLUR'suz kesinleştirme sert engel" kararı kullanıcınındır; hangi makamın onayı olduğu ise
  sorulmamış.

**Düzeltme.** İki yoldan biri seçilmeli; ikisi de kullanıcıya sorularak:
- (a) 2886 md. 40 kısmi dosyaya eklenir ve md. 29 köprüsüyle `kantin.onay_olmadan_kesinlesmez` kuralı açılır. Kuralın
  çapası 2886 md. 40 olur, makam "ita amiri" diye yazılır.
- (b) O güne kadar kantin `KARAR → KESINLESTI` geçişi [U] olur (onay kaydı yok → gerekçe) ve §7.6 satır 1482 buna göre
  düzeltilir.

Her iki yolda da satır 777'deki "(§7.6, §7.7)" ibaresi ayrılmalı: sert yalnız servis için (OSAY 8/2) yazılmalı.

### MB-6 · DOĞRU · yüksek · §5.2.9 `OabContract` (satır 783) + §7.6 (satır 1484) + §7.7 (satır 1517)

**Sorun.** İki [S] işareti §6'nın sert tanımının ve kural paketinin dışında kalıyor.
- (1) "Yer teslimi imzadan önce olamaz ([md. 21/2]) — sert" (satır 783) ve "imzadan önce yer teslimi yok [S]" (satır
  1484). Kural tablosu aynı hükmü `kira.yer_teslimi_gun` adıyla **U** yazıyor ("imzasız teslim yok", satır 1199).
  Testi de uyarı bekliyor: `kn::test_imzasiz_sozlesmede_teslim_uyari` (satır 2153).
- (2) Servis başvurusunda "verilen dosya geri alınamaz [S — kayıt kilidi]" (satır 1517). Bu hükmün §6'da kuralı yok.
  Altın kural 4'ün "silinmez" hükmü zaten kaydı koruyor. [S] bundan fazlasını, yani "geri çekildi" kaydını engelliyorsa,
  kural paketinin dışında bir sert engel olur.

**Doğrulama.** Tasarım satır 962-964'teki sert tanımı üç durum sayıyor: hesap bütünlüğü · hukuken geçersiz işlem
(kantin isteklisinde suç ve hısımlık, mülki amir onayı olmadan kesinleştirme, F1 organ bileşimi) · hesapta kullanılan
parametre. B-13 (satır 2712) "sert listesi genişlemez" diyor. Hükümlerin kendisi:
- [md. 21/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-21): "Kira sözleşmesi taraflarca imzalanmadan yer teslimi
  yapılamaz". Bu bir yasak; ama gerçekleşmiş teslimin kaydı hukuken geçersiz bir işlem değil, bir sapmadır.
- [U-E md. 7/2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-7): "verilen dosyalar herhangi bir sebeple geri
  alınamaz".

Altın kural 3'e göre program doğrusunu gösterir, sapma gerekçesiyle kayda geçer.

**Düzeltme.**
- Satır 783 ve 1484'te md. 21/2 için "sert" yerine "[U] (`kira.yer_teslimi_gun`)" yazılmalı.
- Satır 1517'deki "[S — kayıt kilidi]" kaldırılmalı. Yerine "teslim edilen dosya silinmez (altın kural 4); geri çekme
  talebi [U] + gerekçe" yazılmalı ve §6'ya `servis.dosya_geri_alinamaz` (U, U-E 7/2) eklenmeli.
- Kullanıcı bu ikisini sert istiyorsa §6'nın sert tanımı (satır 962-964) ve CLAUDE.md altın kural 3 açıkça
  genişletilmeli.

### MB-7 · KISMEN · yüksek · §5.2.5 `EMANET` (satır 713-714) + §7.6 Fesih ve tahliye (satır 1487)

**Sorun.** Tasarım, kesin teminatın fesihteki kaderini tek kurala bağlıyor: "fesihte 'gelir kaydedilir' md. 22/4"
(satır 713-714). Fesih satırı (satır 1487) da EK-2 md. 7'deki iki ay ödememe feshini önerdikten hemen sonra "kesin
teminat gelir kaydedilir (`EMANET` → gelir), cari dönem kirası tazminat" diyor. Oysa ödememe feshinde teminatın akışı
farklıdır: birlik alacağını teminattan düşer, artanı kiracıya iade eder. Sözleşme olağan biçimde sona erdiğinde de
teminat iade edilir. Tek kural uygulanırsa ödememe feshinde kiracının iadesi gereken para birliğe gelir yazılır ve
TEFBİS'e yanlış gelir girer.

**Doğrulama.**
- [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) (4.
  paragraf): "aylık kira bedelini iki defa üst üste ödemeyen kiracının sözleşmesi birlikçe tek taraflı olarak
  feshedilir. Bu durumda, Birliğin alacakları, kesin teminat tutarından mahsup edilir varsa kalan tutar kiracıya iade
  edilir."
- [md. 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) ve
  [EK-2 md. 22](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-22) (2.
  paragraf) gelir kaydını sayılı hâllere bağlıyor: fesih talebi, faaliyetin durdurulması, amaç dışı kullanım,
  taahhüdün yerine getirilmemesi, izin ve ruhsat iptali.
- [EK-2 md. 8](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-8):
  "sözleşme bitiminde … kiracıya iade edilir".
- "KISMEN", çünkü 22/4'teki "taahhüdünü … yerine getirmemesi" ödememeyi de kapsıyor gibi okunabilir. Ödememe için
  özel hüküm ise EK-2 md. 7/4'tür.

**Düzeltme.** `EMANET` çıkışları üç ayrı akış olarak yazılmalı:
- (a) [md. 22/4] / EK-2 md. 22/2 hâlleri → teminat gelir kaydı + cari dönem kira tazminatı.
- (b) EK-2 md. 7/4 ödememe feshi → alacak kadar mahsup (gelir) + kalanın iadesi (`EMANET` → çıkış).
- (c) Sözleşme sonu (EK-2 md. 8) → alacak yoksa iade.

Satır 713-714 "fesihte hâline göre gelir kaydı ya da mahsup ve iade" diye düzeltilmeli. md. 22/4 ile EK-2 md. 7/4
arasındaki örtüşme §15'e yorum sorusu olarak yazılmalı.

### MB-8 · KISMEN · orta · §5.2.9 `BidderDocument` (satır 781) + §7.6 Belge yenileme (satır 1486) + §3.4 (satır 272-275)

**Sorun.** Tasarım "Portör ve adli sicil **çalışandan** istenir, istekliden değil" diyor (satır 781) ve §7.6'da bunu
[B] bilgi olarak tekrarlıyor (satır 1486). İhale aşaması için bu doğru: md. 20/4-5'teki istekli belgeleri bunlar
değildir. Ama sözleşmeden sonra kiracının (işletmecinin) kendi portör, adli sicil ve hijyen belgesi de birlikçe
saklanacak belgelerdendir. Kantini kiracı bizzat çalıştırdığı için hijyen belgesi onun için de zorunludur. Model ve
akış bu belgeleri yalnız `CALISAN` öznesine bağlıyor. E46'nın adı ise "Kantin **işletmeci** ve çalışan belge izleme
çizelgesi" (satır 1860). §3.4 de "Kantin çalışanlarının belgeleri (md. 20/7, 23/4)" diyerek işletmeciyi düşürüyor.

**Doğrulama.**
- [md. 23/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23): "Kantin ve benzeri yerleri çalıştıran **işletmeciler
  ile** çalıştırdıkları kişilere ilişkin … portör muayenesi, adli sicil ve arşiv kaydı … belgeler birlikçe muhafaza
  edilir."
- [EK-2 md. 9](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-9): "Kantin
  bizzat kiracı tarafından çalıştırılacaktır."
- [HEY md. 5/1](../mevzuat/hijyen-egitimi-yonetmeligi.md#madde-5): "Bizzat çalışmaları durumunda iş yeri sahipleri ve işletenleri
  de bu eğitimi almaya mecburdur."

**Düzeltme.**
- Satır 781 şöyle düzeltilmeli: "İhale aşamasında portör ve adli sicil istekli belgesi değildir (md. 20/4-5);
  sözleşmeden sonra kiracının ve çalışanların portör, adli sicil ve hijyen belgeleri izlenir (md. 23/4; EK-2 md. 9;
  HEY 5/1)". `subject`'e `KIRACI` eklenmeli ya da seçilen istekli için `ISTEKLI` bu belgelerle açılmalı.
- §7.6 satır 1486'daki [B] metni ve §3.4 satır 272 "işletmeci ve çalışanlar" olmalı.

### MB-9 · DOĞRU · orta · §7.6 Tahsilat (satır 1493) + §9.1-7 (satır 1737-1738) + E42 (satır 1856, 1933)

**Sorun.** Kantin sözleşmesi (E42) EK-2'yi lafız kilidiyle, "karakter karakter aynı" basıyor. EK-2 md. 7/2 ise pay
dağılımını sabit yazar: %10 il, %10 ilçe, %80 birlik. Büyükşehir statüsünde olmayan il merkezindeki okulda Yönetmelik
farklı dağılım ister: ilçe payı yok, il %20. Program payı Yönetmeliğe göre hesaplıyor (E24 kabulü, satır 1915;
`pay_dagitimi.il_merkezi`). Bu okullarda imzalanan sözleşme ise "%10'u (…TL) İl, %10'u (…TL) İlçe" diyecek: ya
boşluklara Yönetmelikle çelişen tutarlar girecek ya da metin hesapla çelişecek. Tasarımda bu çatışma hiç ele
alınmamış; EK-2 "Özel Şartlar" yalnız bir kez geçiyor (satır 1483, "25 genel şart + özel şartlar").

**Doğrulama.**
- [EK-2 md. 7](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-7) (2.
  paragraf): "%10'u … İl Millî Eğitim Müdürlüğüne, %10'u … İlçe Millî Eğitim Müdürlüğüne, %80'i de … birliğin".
- [md. 17/1-a-2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-17): "Büyükşehir statüsünde olmayan il merkezlerindeki
  birliklerde ise gelirin % 20'si il millî eğitim müdürlüğünün banka hesabına, yatırılır."
- EK-2'nin "ÖZEL ŞARTLAR MADDE 2"si boş bırakılmış bir alandır.

**Düzeltme.** E42'ye kural eklenmeli:
- `settlement_type = IL_MERKEZI_BUYUKSEHIR_DEGIL` ise Özel Şartlar md. 2'ye şu metin basılmalı: "Genel Şartlar 7 nci
  maddenin ikinci paragrafındaki dağılım, Yönetmeliğin 17/1-a-2 hükmü gereği %80 birlik, %20 il millî eğitim müdürlüğü
  olarak uygulanır; ilçe payı ayrılmaz."
- Genel şart 7/2'nin boşlukları da buna göre doldurulmalı (ilçe "—"). KE-7'deki dipnot kalıbı örnek alınabilir.
- §15'e karar sorusu (KE-n) olarak eklenmeli ve E42 kabul ölçütüne il merkezi senaryosu yazılmalı.

### MB-10 · KISMEN · orta · §7.1 (satır 1335) + §5.2.4 `AuditReport` (satır 707) + E32 (satır 1923)

**Sorun.** DK'nin olağanüstü çağrı koşulu tasarımda genişlemiş. §7.1, DK çağrısını "([md. 14/5], usulsüzlük
tespiti)" diye yazıyor (satır 1335). `AuditReport` "Bir `UYGUNSUZ` madde → `irregularity_found`" kuralını (OYS
mantığı AYNEN) `escalated_assembly` (md. 14/5) ile yan yana koyuyor (satır 707). E32 kabulü "aykırılıkta md. 14/5
seçeneği" diyor; testin adı da `test_dk_uygunsuz_bulgu_usulsuzluk_isareti` (satır 2043). Böylece kontrol listesindeki
herhangi bir uygunsuzluk (örneğin mühürsüz koçan) olağanüstü genel kurul çağrısını tetikleyebilir. Hüküm ise
yalnızca md. 6'daki görev ve yetkilere aykırı faaliyette DK'ye çağrı yetkisi verir. "Usulsüzlük veya uygunsuzluk"
müdürün md. 27/3 yolunun lafzıdır.

**Doğrulama.**
- [md. 14/5](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-14): "yönetim kurulunun **6 ncı maddede sayılan birliğin görev
  ve yetkilerine aykırı faaliyetlerini** tespit etmesi hâlinde genel kurulu olağanüstü toplantıya çağırır".
- [md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27): "usulsüzlük veya uygunsuzluk görmesi halinde".
- Genel set doğru ayrımı yapıyor: GNL-OAB-FR-012 satır 48-50'de iki ayrı kutu var; "md. 6'ya aykırı faaliyet yok" ve
  "Md. 6'daki görev ve yetkilere aykırı faaliyet tespit edildi → md. 14/5".

**Düzeltme.**
- Satır 1335'teki "usulsüzlük tespiti" ibaresi "md. 6'daki görev ve yetkilere aykırı faaliyet tespiti" olmalı.
- `AuditReport`'a `md6_aykiri_faaliyet` alanı eklenmeli; bu alanı DK açıkça işaretler. `irregularity_found` yalnız
  rapor bayrağı kalmalı; 14/5 önerisi yalnız `md6_aykiri_faaliyet` doğruysa görünmeli.
- Test adı "…_md6_aykirilik_isareti" olmalı.

### MB-11 · DOĞRU · orta · §7.1 (satır 1340) ↔ §9.5 E13 (satır 1827)

**Sorun.** "Genel kurul sonuç bildirimi" için iki bölüm iki ayrı dayanak söylüyor. §7.1 "dayanağı korpusta bulunamadı —
saha belgesi, DOĞRULANMADI" diyor. Katalog ise E13'e kesin dayanak veriyor: "[10/1-ç], [13/4], [27/1]". Bu üç fıkranın
hiçbiri birliğe sonucu okul müdürlüğüne bildirme yükümü koymuyor. Altın kural 1'e göre doğrulanmayan dayanak evraka
basılmaz.

**Doğrulama.**
- [md. 10/1-ç](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-10): "bütün tutanak ve belgeler yeni seçilen yönetim
  kuruluna teslim edilir". Muhatap müdür değil.
- [md. 13/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-13): "yazışmalar okul müdürü ile koordineli yapılır".
  Koordinasyon hükmü; bildirim yükümü değil.
- [md. 27/1](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27): müdür genel kurulun usulüne uygun yapılmasını sağlar.
- GNL-OAB-FR-005 bu belgeyi "md. 13/4, 27/1"e bağlıyor; katalog bu atıfları sorgulamadan almış.

**Düzeltme.** E13'ün dayanak hücresi şöyle olmalı: "Yönetmelikte açık bildirim hükmü yok (DOĞRULANMADI); okul
uygulaması — dolaylı: [13/4] koordinasyon, [27/1]". Belgenin altlığına dayanak "okul uygulaması" diye basılmalı ve
hüküm diye sunulmamalı. §7.1 ile §9.5 tek ifadede birleşmeli.

### MB-12 · DOĞRU · orta · §7 "Evrak" sütunları ↔ §9.5 katalog (satır 1813-1878) + rol matrisi (satır 458)

**Sorun.** §7 akışlarında adı geçen yirmiye yakın belgenin katalogda kodu yok. Bir kısmını mevzuat açıkça istiyor;
bir kısmı ise tasarımın kendi kararlarına dayanak oluyor.
- **Servis (U-E zorunlulukları).**
  - Komisyon kararının tebliği yazısı (satır 1522). [U-E md. 8/6](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-8)
    "Tebligat Kanunu hükümlerince bildirilir" der; sözleşmenin 10 günlük süresi bu tebliğden başlar.
  - Komisyon kararının onaya sunulması yazısı (satır 1521; U-E 8/5, OSAY 8/2).
  - Taşımacıyı tespit komisyonu görevlendirme yazısı (satır 1515; U-E 3/1-e, OSAY 6/1-b).
  - Servis işlem dosyası kapağı (U-E 5/2).
  - Tip şartname (EK-1, U-E 5/1). [EK-1 md. 2](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#ek-1-madde-2): "Bu Tip
    Şartname, sözleşmenin eki ve ayrılmaz parçasıdır". KE-9 (satır 2722) EK-1'in basılacağını varsayıyor; ama lafız
    kilidi (§9.1-7) yalnız E42 ve E55'i sayıyor.
  - Değerlendirme tutanağı (satır 1519).
  - Servis yükümlülük ihtarı ve fesih bildirimi (satır 1526; U-E md. 11/1-ç, EK-2 md. 7/f).
- **Kantin.**
  - YK fesih kararı ve fesih bildirimi (satır 1487; [md. 22/1, 22/4](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22),
    EK-2 md. 7/4, 15, 22).
  - Tahliye edilmeyen yer için okul yönetiminin bildirimi:
    [EK-2 md. 24](../mevzuat/meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md#genel-sartlar-madde-24) (İl
    Muhakemat Müdürlüğü / İl Özel İdaresi), [md. 22/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-22) ve
    [md. 28/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-28) (mülki idare amiri). Bunlar hiçbir akışta da yok.
- **Müdür.** [md. 27/3](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-27) 2. cümle: "il/ilçe milli eğitim müdürlüğüne
  durumu bildirerek denetlenmesini talep eder". Rol matrisi bu yazıyı "MEM'e bildirim" diye müdüre veriyor (satır
  458); katalogda yalnız E35 (uyarı) var.
- **Organ ve mali.**
  - Yedek üye çağrı yazısı (satır 1375; md. 13/6, 14/6).
  - Bankaya imza yetkisi bildirimi (satır 1372, 1542; md. 18/2).
  - Kasa sayım tutanağı (satır 1542; md. 16/3).
  - İptal ve kayıp yaprak tutanağı ve koçan iptal tutanağı (satır 1451, 1454; md. 16/5-7).
  - Biten koçanlar teslim listesi (satır 1453; md. 23/6).
  - Karar defteri dizini (satır 1370, 1543).
  - Dönem kapanış kontrol listesi (satır 1543).

**Doğrulama.** Yukarıdaki satırlar §7'nin evrak sütunlarından alındı ve E01-E62 başlıklarıyla tek tek karşılaştırıldı.
Faz dağılımı (satır 1878) 62 kodu sayıyor; bu belgelerin hiçbiri o sayıya girmiyor. Mevzuat dayanakları yukarıdaki
çapalardadır.

**Düzeltme.** §7'deki her evrak adı ya bir koda bağlanmalı ya da "program üretmez" diye §9.7'ye yazılmalı.
- **Mevzuatın istediği belgeler yeni kod almalı:** servis tebliği (U-E 8/6), onaya sunma (U-E 8/5), komisyon
  görevlendirme (U-E 3/1-e), tip şartname EK-1 (lafız kilidiyle; §9.1-7'ye eklenir), servis ve kantin fesih bildirimi,
  md. 27/3 MEM bildirimi (müdür; K2'nin "uyarı md. 27/3" kalemi bunu da kapsamalı), tahliye ve ihtilaf bildirimi
  (md. 28/3, EK-2 md. 24).
- **Kasa sayımı, iptal yaprak, biten koçan ve imza yetkisi bildirimi:** E37 ya da E22'nin bölümü olarak açıkça
  bağlanmalı.
- Faz sayımı güncellenmeli.

### MB-13 · KISMEN · orta · §3.1 makbuz koçanı satırı (satır 228) + §5.2.6 (satır 739) + §7.8 kapanış (satır 1561) + §9.7 (satır 1961)

**Sorun.** Tasarım koçanın resmî kayıt olarak dayanağını yalnız [16/5-7] ve EK-1'e bağlıyor. Oysa koçan md. 23'e göre
YK'nin tutmakla yükümlü olduğu "belgeler"dendir (23/1-e). Biten koçanlar da 23/6'ya göre okulda saklanır. Daha önemli
bir boşluk var: [23/2](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23) karar defteri dışındaki "diğer defter **ve
belgeler**"in il/ilçe MEM'ce tasdik edileceğini söylüyor. Koçanların bu tasdike tabi olup olmadığı tasarımda hiç
sorulmamış. `ReceiptBookRegistry`'de tasdik alanı yok. Kapanıştaki "Defterlerin tasdik kaydı yok" denetimi (satır
1561) yalnız `OfficialBook`'a bakıyor.

**Doğrulama.**
- [md. 23/1-e](../mevzuat/meb-okul-aile-birligi-yonetmeligi.md#madde-23): "Gelir/gider makbuzu, alındı belgesi/harcama
  belgesi".
- 23/2: "diğer defter ve belgeler ise birliğin bağlı bulunduğu il/ilçe millî eğitim müdürlüğünce tasdik edilir".
- 23/6: "biten koçanlar … okulda muhafaza edilir".
- TKB E.4 §3.1/2 ([bolum-3-1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-3-1)) aynı ifadeyi tekrarlıyor.
- GNL-OAB-FR-015'te de koçan bölümünde (B) tasdik sütunu yok. Yorum açık, hüküm belirsiz; "KISMEN" bu yüzden.

**Düzeltme.**
- §3.1 satır 228'in dayanak hücresi şöyle olmalı: "[md. 16/5-7], [23/1-e], [23/6]; EK-1".
- §15'e yorum sorusu eklenmeli: "23/2'deki 'belgeler' makbuz koçanlarını kapsar mı?"
- Cevap gelene kadar `ReceiptBookRegistry`'ye isteğe bağlı `certified_by` ve `certified_on` alanları konmalı (boşken
  bilgi [B]); E22 kabulüne de koçan tasdik sütunu eklenmeli.

### MB-14 · DOĞRU · orta · fıkra/bent ve nitelemede yanlışlar (satır 251, 776, 1456, 1461, 1704, 1817, 1841, 1850)

**Sorun ve doğrulama.** Atıf dayanaksız değil, ama fıkra, bent ya da nitelendirme yanlış:
- **Satır 776** (`RentableAsset.full_year`): "12 ay; aksi 9 ay, [md. 19/3]". md. 19/3 "eğitim ve öğretime açık olduğu
  günler"i söyler, "9 ay" demez. 9 ay ve Haziran-Ağustos, [EK-2 md. 4]'tedir: "işletilmeyen yerler için dokuz ay".
  Düzeltme: "[md. 19/3]; [EK-2 md. 4] (9 ay)".
- **E03, satır 1817**: dayanak "[13/4-5]". Temsilci görevlendirmesinin dayanakları başka fıkralardadır:
  - [13/7] (kampüs);
  - [19/1] ve [20/3] (birlik başkanı muhammen bedel ve ihale komisyonunda);
  - U-E 3/1-e;
  - [17/1-b-3] (iki birlik başkanının katıldığı pay komisyonu).

  Kabul ölçütü (satır 1894) "muhammen bedel ve ihale komisyonu satırları" diyor. GNL-OAB-FR-022'nin dayanağı da 13/7,
  19/1, 20/3, 20/8'i sayıyor. Düzeltme: bu fıkralar eklenmeli; 13/5 yalnız "karar defterine işlenir" için kalmalı.
- **E36, satır 1850**: "[15/1-c]" üçüncü kişilerin okulda ders saatleri dışında yaptığı etkinliklerin gelirine
  ilişkindir. Birliğin kendi etkinlik ve kampanyası [6/1-c] ve [6/1-f]'dir ("sosyal, kültürel etkinlikler ve
  kampanyalar düzenlemek"). Düzeltme: 6/1-c ve 6/1-f eklenmeli; 15/1-c "üçüncü kişi etkinliği" notuyla kalmalı.
- **E27, satır 1841**: dayanağa "[18/5]" (başkanın aylık bildirimi) girmiş; ödeme onayıyla ilgisi yok. Düzeltme:
  çıkarılmalı.
- **Satır 251** (§3.2): "md. 16/7 ve 23/6'daki 1988 arşiv yönetmeliği". Yalnız 16/7 "16/5/1988 tarihli ve 19816
  sayılı" der. 23/6 tarihsiz, dinamik bir atıftır ve doğrudan yürürlükteki Yönetmeliği gösterir. Düzeltme: "md.
  16/7'deki 1988 atfı (23/6 tarihsizdir, yürürlükteki Yönetmeliğe gider)".
- **Satır 1456 ve 1704**: Tablo 4 "TKB E.4 §4" ([bolum-4]) çapasıyla gösteriliyor. Tablo 4 aslında §4.1'dedir
  ([bolum-4-1](../mevzuat/okul-aile-birlikleri-denetim-rehberi.md#bolum-4-1)); Tablo 3 ise §4 başlığının altındadır. Düzeltme:
  satır 1456'da `#bolum-4-1`; satır 1704'te "§4 Tablo 3, §4.1 Tablo 4".
- **Satır 1461** (§7.6): "Kiralamayı il/ilçe MEM yürütür". Kiraya veren birliktir: [md. 20/1-2] "birlik tarafından
  kiraya verilmesi", G.2024/35 I-8 ve II-5 "işletmeci ile okul aile birliği arasında … sözleşmesi". MEM muhammen bedel
  komisyonunu kurar ve ilanı yapar (G.2024/35 II-2, II-3); ihaleyi md. 20/3 komisyonu yapar. Düzeltme: "Kiraya veren
  birliktir; muhammen bedel komisyonunu ve ilanı il/ilçe MEM, pazarlığı md. 20/3 komisyonu yürütür".

### MB-15 · DOĞRU · düşük · biçim ve iç tutarlılık (§9.1-9.7)

- **Müdürün "Görüldü" bloğu.** §9.3 (satır 1758-1767), müdürün "yalnız mevzuatın ona rol verdiği yerde" göründüğünü
  söylüyor ve bu yerleri sayıyor. Ama E02 (satır 1893), E32 (satır 1923), E37 (satır 1928) ve E61 (satır 1952) de
  "Görüldü — Okul Müdürü" taşıyor ve listede yoklar. Örneğin DK ara raporunu [14/4] YK'ye sunar. Ya bu bloklar
  listeye md. 27/2 (denetim) gerekçesiyle eklenmeli ya da kaldırılmalı.
- **E37 devralan.** §9.6 E37 (satır 1928) "Devralan yeni YK adına üye" diyor; §7.8 (satır 1542) "yeni baskan ve
  muhasip teslim alır". İkisi tek ifadede birleşmeli.
- **E56 imzası.** E56 (satır 1947) "… Okulu Müdürlüğü" diyor. [U-E md. 10/3](../mevzuat/okul-servisi-calistirma-usul-esaslari.md#madde-10)
  ise "Taşımacıyı tespit komisyonlarınca … yayınlanır" der. İmza "Taşımacıyı Tespit Komisyonu Başkanı" olmalı.
- **Çapasız atıflar.** Çapasız yalın atıflar atıf kilidi taramasından kaçar; çapalı biçime çevrilmeli.
  - Satır 1776: "27/1".
  - Satır 1820: E06 "9/6".
  - Satır 1789-1795: "U-E 5/3", "U-E 8/1", "U-E 3/1-c".
  - Satır 1963-1966: "G.2024/35 II-3", "23/2", "23/5", "TMY 16/1, 41/2".
- **RYUE maddeleri.** §9.1-4 (satır 1727-1730) resmî yazıları "RYUE md. 7, 12 ve 17" biçimine bağlıyor. E12 kabulü
  (satır 1903) ise sayı, konu ve muhatap da istiyor. Listeye
  [RYUE md. 11](../mevzuat/resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md#madde-11) (sayı), md. 13
  (konu) ve md. 14 (muhatap) eklenmeli.

---

Çürütülen aday: 24 · Sınanan bağlantı: 596 (102 tekil çapa; hepsi korpusta var)

> Çürütülenlerden bazıları:
> - Müdürün YK'ye eklenmemesi ve aynı kişinin YK ile DK'de olmaması: ikisi de sert ve kullanıcı kararı (KE-15, A-2).
> - TÜFE, %6 teminat ve KDV [S]: §6'ya göre "hesapta kullanılan parametre".
> - YK katılım satırı zorunluluğu: yeter sayı hesabının girdisi.
> - Ücreti velinin ödemesi: U-E 3/1-f ve EK-2 md. 6/b ile doğrulandı.
> - KE-9 istisnası: EK-1 md. 6, EK-2 md. 4 ve 7'de doğrulandı.
> - OSAY 8/3'ün çoklu taşımacıya dayanak olması: "birlikte taşıma hizmeti".
> - E52'de eksik belgenin uyarı olması: plan §1.8 kullanıcı kararı.
> - md. 22/5 yasaklı isteklinin [U] olması: sert listesi kapalı.
> - md. 7/2 ile 13/8 yeter sayı farkı (4 ve 3): doğru kurulmuş.
> - EK-1'in md. 16/5 makbuzuyla bağı: korpus notu kuruyor.
> - Doğru çıkan atıflar: DAHY 9/4, 11/5, 17/1, 20/2 ve 24; Genelge 2024/35 I-2, I-3, I-5, I-9 ve II-1 süreleri; U-E
>   8/5 ve 8/6 süreleri; G.2011/40'taki "diploma"; TMY 16/1 ve 41/2; E12 imzacıları; E42 imzacıları; md. 21/5; md. 12/4
>   ve 14/3 sınırları; 10'u ve 20'si arz vadesi (F0-a).

---

## Uygulanabilirlik (20)

*Mercek: tasarım yazıldığı gibi kodlanırsa çalışır mı. Satır numaraları denetlenen belgeden
(`docs/tasarim/2026-10-31-genel-tasarim.md`, "s."). Kaynak yolları Kütüphane Defteri ve OYS çıkarımlarının köküne göredir: `kutuphane-main/…`
(Kütüphane Defteri 9a3829d), `oys-main/…` (OYS). Önem dağılımı: yüksek 7 · orta 7 · düşük 6.*

### UY-1 · DOĞRU · yüksek · §4.1 (satır 328-330) ↔ TK16 (satır 109) ↔ §4.2 (satır 344-347) ↔ §4.4.3 (satır 499-500)

**Sorun.** Denetim izinin HMAC zinciri DEK'ten türeyen anahtarla mühürleniyor; ama tasarım, DEK'in bellekte
olmadığı anlarda da veritabanına yazma öngörüyor. (a) Açılışta 7. adım (günlük yedek) ve 8. adım (`migrate`), 12.
adımdaki kilit ekranından önce koşuyor ve "sistem işleri (günlük yedek, göç, dönem kilidi denetimi) `sistem`
yazarıyla düşer". (b) `od-gunluk` saatte bir koşuyor; boşta kilit DEK'i bellekten siliyor; §5.4'teki aday tespiti
"açılışta ve gün değişiminde" pano kartı yazıyor. Bu yazmaların denetim izi satırı mühürlenemez: ya zincir
mühürsüz satırla kırılır ya da yazma `KeyMissingError` ile düşer, yani her açılışta göç ve yedek adımı bozulur. (c)
Tembel kilit "her istekte" tetikleniyor: uzun bir işin (kapanış, arşiv paketi, DEK yenileme) ortasında gelen durum
sorgusu DEK'i silebilir ve iş, işlemin ortasında anahtarsız kalır. Bu ailede yeni bir durum: Kütüphane'de boşta
kalınca görevli kipine iniliyordu ve DEK bellekte kalıyordu.

**Doğrulama.** Tasarım s. 109: "HMAC zinciriyle mühürlenir (anahtar `HKDF(DEK, "od-denetim-izi")`)"; s. 329-330:
"Yazar bağlamı olmayan yazma reddedilir; sistem işleri … `sistem` yazarıyla düşer"; s. 344-352 açılış sırası (7, 8
→ 12); s. 499-500: "oturum kilitlenir, DEK bellekten silinir"; s. 308: "açılışta + saatte bir"; s. 889. Kaynak:
`kutuphane-main/backend/shared/crypto.py:8-12` ("programın kilidi açılana kadar YOKTUR") ve `:33-34` (kilitleme =
kapatmak veya Kilitle; boşta silme yok); `…/apps/okul/services/app_password.py:1095-1097` (`lock()` →
`crypto.unload_key()`); `…/apps/kutuphane/services/saklama.py:1032-1046`: gün işi kilit durumuna bakmadan
`durum_yaz` ile veritabanına yazıyor. OAB bu kalıbı aynen alıyor (s. 889). `sistem` rol listesinde yok (s. 143).

**Düzeltme.** (1) Kural: DEK yokken veritabanına yazılmaz. Gün işleri kilitliyken "kilitli" sonucu döner ve
kilit açılınca koşar (Kütüphane'deki "bakimda → bir saat sonra" deseni). (2) Göç ve yedek olayları kişisiz bir
bekleyen-olay dosyasına (`bekleyen-olaylar.json`) yazılır, ilk kilit açılışında `sistem` yazarıyla zincire
mühürlenir. (3) `sistem` yazarının modeldeki karşılığı tanımlanır: `hesap` boş olabilir ve `aktor` alanı
`HESAP` ya da `SISTEM` değerini alır. (4) `OturumDurumu`'na "uzun iş sürüyor" sayacı eklenir; sayaç sıfır değilken
tembel kilit ertelenir. Kapanış, arşiv paketi ve DEK yenilemesi sayacı artırır. (5) Testler: kilitliyken gün işi
yazmaz · göç olayı ilk açılışta mühürlenir · uzun iş sürerken gelen durum sorgusu kilitlemez.

### UY-2 · DOĞRU · yüksek · §5 (satır 594, 625) ↔ §4.4.4 (satır 510) ↔ TK16 (satır 109) ↔ §12.B (satır 2543, 2585)

**Sorun.** F1b'nin teslim ettiği `Hesap` ve `DenetimIzi` modelleri hiçbir yerde tanımlanmamış; iki bölüm
birbirine gönderiyor. Erişim günlüğünün modeli de yok. Tanımsız kalan "kaydın özeti", altın kural 4 ile KVKK
silmesini çatıştırıyor. Denetim izi ekleme-yalnız ve HMAC zincirli. Özet kişisel alanın değerini (şifreli bile
olsa) taşırsa, §5.4'teki silmeler denetim izinde geri kalır ve DEK'le açılabilir: veli listesi, T.C. kimlik no,
telefon, seçilmeyen isteklinin iletişim bilgisi. Erişim günlüğü zincirin içindeyse 2 yılda silinmesi (s. 871)
zinciri kırar. Ayrıca §5.3 şifreleme tablosu `Hesap`'taki ad-soyadı kapsamıyor. Gönderme yapılan ama alanı
olmayan başka parçalar da var: `ComplianceItem.resolved_at` alan listesinde yok; genel kurul katılımının
"gerekçeli düzeltme satırı" için model yok.

**Doğrulama.** s. 594: "hesap ve denetim izi modelleri … mimaride (§4)"; s. 625: "denetim izi §4'te tanımlanır";
s. 109 TK16 Durum: "Öneri; model §5"; s. 510: "(`Hesap`, alanları §5)"; s. 2543: "`Hesap`, `DenetimIzi` §5'te";
s. 2585: "(alanlar §5)". §4 ve §5'in hiçbirinde alan tablosu yok. §5.3 tablosunda (s. 822-840) iki model de
geçmiyor. s. 755: `ComplianceItem` alanları arasında `resolved_at` yok, aynı satır onu kullanıyor. s. 693:
"yalnız gerekçeli düzeltme satırıyla değişir".

**Düzeltme.** §5.1'e üç tablo eklenir. (1) `Hesap`: tanıtıcı, rol, ad-soyad (şifreli), `membership`, açılış ve
kapanış tarihi, durum. (2) `DenetimIzi`: sıra, zaman, `hesap`/`aktor`, rol, model, kayıt id, işlem, önceki ve
sonraki durum, **değişen alan adları** (değer yok; yalnız tutar, tarih, durum gibi kişisiz alanların değeri), gerekçe
bağı, `onceki_mac`, `mac`. Kural: şifreli ya da kişisel alanın değeri denetim izine girmez. (3) `ErisimGunlugu`:
zincir dışı, silinebilir. §5.3'e üç modelin satırı, `ComplianceItem`'a `resolved_at`, `GeneralAssembly`'ye
düzeltme satırı modeli (`AttendanceCorrection`) yazılır. Test: kişisel alan içeren kayıt yazılınca denetim izinde
değer yoktur.

### UY-3 · DOĞRU · yüksek · TK12 (satır 105) ↔ §4.4.4 (satır 521-528) ↔ §5.3 (satır 842-843) ↔ §2.3.1 (satır 146-149)

**Sorun.** DEK yenilemesi diskteki şifreli dosyaları kapsamıyor. `Attachment` ve `GeneratedDocument` dosyaları
DEK'ten türeyen anahtarla şifreli; yenileme ise yalnız şifreli alanları, kör indeksleri, parmak izini, yedek
anahtarını ve zincir mührünü yeni DEK'le yazıyor, sonra eski DEK'in kopyalarını siliyor. Yenilemeden sonra bütün
ekler ve üretilmiş evrak dosyaları açılamaz. Bu kalıcı veri kaybıdır ve her dönem devrinde (F4) yaşanır. Dosya
anahtarının HKDF bilgi dizgesi de yazılmamış. `BankTransaction.fingerprint`'in anahtarlı mı (HMAC) yoksa düz özet
mi olduğu belirsiz: anahtarlıysa yenileme listesinde yok, düz özetse şifreli açıklamanın sözlük saldırısına açık bir
izi olur.

**Doğrulama.** s. 105: "şifreli alanlar, kör indeksler, parmak izi, yedek anahtar çifti ve denetim izi mührü yeni
DEK'le"; s. 524: "tek SQLite işleminde şifreli alanlar, kör indeksler, parmak izi ve zincir mührü"; s. 527: "eski
DEK'in arşiv kopyaları silinir"; s. 842-843: dosyalar "DEK'ten HKDF ile türeyen dosya anahtarıyla diskte şifreli
durur (bilgi dizgesi §4 kimlik sabitlerinde)". Kimlik sabitleri §4'te değil §2.3.1'de; oradaki HKDF ve HMAC
satırlarında (s. 146-149) dosya dizgesi yok. Kaynak: Kütüphane'de dosya şifrelemesi yok (`…/desktop/backup_crypto.py`
ve `…/shared/crypto.py` dışında HKDF kullanılmıyor); özellik yeni ve deseni ailede yok.

**Düzeltme.** İki yoldan biri seçilir. (a) Dosyalar ayrı rastgele dosya anahtarıyla şifrelenir, anahtar DEK'le
sarılıp `Attachment.key_wrap` alanında tutulur; yenilemede yalnız sarmallar yeniden yazılır ve bu, SQLite işlemine
girer. (b) TK12'ye "dosyaları yeniden şifrele" adımı eklenir: yeni anahtarla geçici dosyaya yazılır, atomik
yeniden adlandırılır, ilerleme `gecis` işaretinde tutulur, yarıda kalırsa açılışta sürdürülür. Hangisi seçilirse
seçilsin: kimlik tablosuna `od-dosya` dizgesi yazılır; `fingerprint` için "HMAC(HKDF(DEK, "od-banka-parmak-izi"))"
yazılıp yenileme listesine eklenir. Test: yenilemeden sonra her `Attachment` açılır.

### UY-4 · DOĞRU · yüksek · O2 (satır 603) ↔ §7.8 (satır 1555-1556) ↔ §7.3 (satır 1403-1405) ↔ §6.2-6 (satır 1021-1023) ↔ §5.2.8 (satır 763)

**Sorun.** Dönem kilidi, tasarımın kendisinin kapanıştan sonra beklediği yazmaları da sert biçimde engelliyor.
(a) Kapanış denetimi "TEFBİS'e girilmemiş", "deftere geçirilmemiş kayıt" ve "deftere işlenmemiş karar"
maddelerini yalnız uyarı sayıyor. Oysa bu işaretler kapanmış dönemin `LedgerEntry` ve `BoardDecision` satırlarına
yazılıyor. Kapanıştan sonra konamazlar: kayıtlar "TEFBİS'e girilecekler" listesinde sonsuza dek kalır. (b) Kapanmış
dönemin kaydı yeni dönemde ters kayıtla düzeltildiğinde asıl kayda `tefbis_fix_needed` yazılamaz. (c) Kapanmış
dönem evrakının yeniden basımı engellenir. Basım `term`'i kapanmış döneme bağlı yeni bir `GeneratedDocument` satırı
ister ve eski satırı `YERINI_ALDI` yapar; ikisi de O2'ye takılır. Oysa §6.2-6 ve E39 bu basımı vaat ediyor, ve
evrak izi okuma rollerinde de yazılıyor. Kayıt düzeyindeki "`KESIN` kayıt değişmez — sert" kuralı (s. 723) da
işaret alanlarını istisna etmiyor. `BoardDecision` satırında bu kapsam doğru verilmiş: "metin ve oylar değişmez".

**Doğrulama.** s. 603: "`term` taşıyan her kayıt, dönemi `KAPANDI` ise yazılamaz (sert)"; s. 443: "Kapanmış
dönem her rolde salt okurdur"; s. 1555-1556: TEFBİS ve defter eksikleri "uyarı"; s. 1403-1404: işaretler
`posted_*` ve `tefbis_entered_*` alanlarına yazılıyor (alanlar s. 723); s. 1370: `KABUL_EDILDI → DEFTERE_ISLENDI`;
s. 763: "Aynı nesne için yeniden üretim yeni sürüm satırıdır"; s. 1023: yeniden basımda özet aynı çıkar; s. 2274
(F4 testi).

**Düzeltme.** O2'ye ve `KESIN` kilidine açık bir beyaz liste yazılır: `posted_book`, `posted_page`, `posted_at`,
`tefbis_entered_at/by`, `tefbis_fix_needed`, `BoardDecision`'ın `DEFTERE_ISLENDI` geçişi ve defter alanları,
`GeneratedDocument` ekleme ve `YERINI_ALDI` geçişi, `ComplianceItem.resolved_at`. Tutar, tarih, hesap, metin ve oy
kilitli kalır. Daha temiz seçenek: bu işaretler dönem kilidinin dışındaki ekleme-yalnız bir `KayitIsareti`
tablosuna taşınır. Test: kapanmış dönemde "TEFBİS'e girildi" konur, tutar değiştirilemez.

### UY-5 · DOĞRU · yüksek · §7.1 (satır 1340, 1342) ↔ §5.2.1 (satır 654) ↔ §5.2.2 (satır 666) ↔ §5.2.3 (satır 693) ↔ §5.2.7 (satır 751)

**Sorun.** Yeni birlik dönemi, ona ait kayıtlar oluştuktan sonra açılıyor. Genel kurulda seçilenler
(`SECILDI`, `YAPILDI → TUTANAK_TAMAM` geçişinde), adaylar ve tahmini bütçe yeni döneme aittir. Bütçenin `term`'i
"uygulanacağı dönem"dir ve evrakı `ILAN_EDILDI`'de basılır. Yeni `OabTerm` ise ancak "`TUTANAK_TAMAM` sonrası"
açılıyor. `OrganMembership.term` ve `OabBudget.term` zorunlu yabancı anahtar ve tekil kısıtın parçası. Kayıt ya eski
döneme yazılır (o zaman "görevdeki üye", dönem sayacı, dönemlik hesaplar ve dönem devrinde hesap kapanışı yanlış
sonuç verir) ya da hiç yazılamaz. `GeneralAssembly.term` bilinçli olarak eski dönemdir ("olağanda kapanacak
dönem"); bu yüzden genel kuruldan yeni döneme ulaşan bir yol da yok.

**Doğrulama.** s. 1340: seçim, "seçilen yalnız aynı genel kurulun adayından [S]", YAPILDI → TUTANAK_TAMAM; s. 1342:
"`TUTANAK_TAMAM` sonrası … yeni `OabTerm` açılır"; s. 693: `GeneralAssembly.term` = "olağanda kapanacak dönem";
s. 666: `OrganMembership` "(dönem, organ, kişi, genel kurul) … tekil"; s. 751: `OabBudget.term` "(bütçenin
uygulanacağı dönem)"; s. 1336: tahmini bütçe evrakı `ILAN_EDILDI` geçişinde. Kaynak: OYS'de dönem ile genel kurul
arasında böyle bir sıra kurulmamış. `oys-main/backend/apps/okul_aile_birligi/services.py:333-348`
(`record_assembly_outcome`) yalnız sayı ve durum yazıyor; sorun OAB'nin "genel kurul eski döneme ait" kararından
doğuyor.

**Düzeltme.** Genel kurul `ILAN_EDILDI` olunca yeni dönem `HAZIRLIK` durumunda açılır. Tarih aralığı boştur;
çakışma ve tarih–dönem kısıtları bu durumda uygulanmaz. Adaylar, seçim ve bütçe bu döneme yazılır.
`TUTANAK_TAMAM`'da `start_date` toplantı günü olur, dönem `ACIK`'a geçer, eskisi `KAPANISTA`'ya. Genel kurul `IPTAL`
olursa `HAZIRLIK` dönemi de `IPTAL` olur. Durum kümesi `HAZIRLIK → ACIK → KAPANISTA → KAPANDI` olur ve "en çok bir
`HAZIRLIK`" kısıtı eklenir. F2 testi: ikinci toplantıda yapılan genel kurulda seçilen YK yeni dönemdedir.

### UY-6 · DOĞRU · yüksek · §5.2.5 (satır 720-721) ↔ §7.3 (satır 1394-1396) ↔ §8.2 (satır 1605-1607)

**Sorun.** Geri alınan banka partisi yeniden aktarılamıyor. `fingerprint` koşulsuz tekil; geri alınan partinin
satırları silinmiyor, `void` oluyor; içe aktarımda "parmak izi çakışan satır elenir". Yanlış hesap ya da yanlış
sütun profiliyle yapılan aktarım geri alınıp düzeltilmiş dosyayla yeniden yapılınca, bütün satırlar `void`
kopyalarıyla çakıştığı için sessizce düşer. Hareketler programa bir daha giremez. Kapanışta "hepsi tam eşli" ve banka
bakiyesi denkliği sert kural olduğundan sonuç ya dönemin kapanamaması ya da eksik defterdir.

**Doğrulama.** s. 721: "`fingerprint` … tekil — sert (çift aktarım)"; s. 1396: "`UYGULANDI → GERI_ALINDI` … satırlar
`void` olur, silinmez"; s. 1394 ve s. 1606: "Aynı parmak izli satır elenir [S]"; s. 1549 ve s. 1551: kapanışta
sert denetimler. Kaynak: SQLite kısmi tekil dizini destekliyor (bkz. UY-10 doğrulaması); koşullu tekil kısıt deseni
OYS'de zaten kullanılıyor (`oys-main/backend/apps/okul_aile_birligi/models/*.py`,
`condition=Q(deleted_at__isnull=True)`).

**Düzeltme.** `UniqueConstraint(fields=["fingerprint"], condition=Q(void=False))`; eleme yalnız `void` olmayan
satırlara karşı yapılır. Önizleme "daha önce geri alınmış partiden N satır yeniden alınacak" bilgisini verir. Test:
içe aktar → geri al → yeniden aktar = aynı satır sayısı.

### UY-7 · DOĞRU · yüksek · §5.2.6 (satır 740) ↔ §5.2.5 (satır 723) ↔ §7.3 (satır 1405) ↔ §7.5 (satır 1443, 1450-1451)

**Sorun.** Kullanılan makbuz yaprağının çıkışı yok, bu yüzden kesinleşmiş makbuzlu gelir düzeltilemiyor.
Yaprak–kayıt bağı 1:1 ve "bir yaprak bir kayda" sert. `KULLANILDI` durumundan hiçbir geçiş tanımlı değil. `KESIN`
kayıt değişmez; düzeltme ters kayıt ve yeni kayıtla yapılır. Ama yeni kayıt için "makbuzlu gelirde yaprak zorunlu"
kuralı sert, kâğıttaki aynı yaprak ise eski kayda bağlı. Sonuç olarak kesinleşmiş makbuzlu gelirin hiçbir alanı
düzeltilemez: tutar, hesap, TEFBİS tipi, tarih. Ayrıca `IPTAL` edilen kayıtta yaprak `KULLANILDI` kalır ve koçan
envanteri ile TKB Tablo 4 yanlış çıkar. Kâğıtta sonradan iptal edilen kullanılmış yaprak da programa işlenemez,
çünkü `KULLANILDI → IPTAL` geçişi yok.

**Doğrulama.** s. 740: "`ledger_entry` → `LedgerEntry` (1:1)", "bir yaprak bir kayda — sert", "`IPTAL` ve `KAYIP`
geri alınamaz"; s. 1443: "yaprak `BOS → KULLANILDI | IPTAL | KAYIP`" (`KULLANILDI`'dan geçiş yok); s. 723:
"`KESIN` kayıt değişmez — sert", "Makbuzlu gelirde yaprak zorunlu ve yaprak tutarı = kayıt tutarı — sert"; s. 1405:
"Geçmiş ya da girilmiş kayıt ters kayıtla (`reversal_of`) [S]".

**Düzeltme.** Yaprak bağı `TransactionMatch` deseniyle ayrı bir tabloya alınır: `LeafUse(yaprak, kayıt, durum:
ETKIN|COZULDU)`, kısıt "bir yaprağın en çok bir etkin kullanımı". Ters kayıt eski bağı `COZULDU` yapar, düzeltilmiş
kayıt aynı yaprağa bağlanır. Ters kaydın kendisi yaprak istemez. `KULLANILDI → IPTAL` geçişi eklenir: kâğıtta iptal,
gerekçe zorunlu, iz kalır ve bağlı kayıt ters kayda zorlanır. `LedgerEntry.receipt_leaf` alanı kalkar (tek kaynak,
O6).

### UY-8 · DOĞRU · orta · §4.4.1 (satır 432-436) ↔ §4.4.5 (satır 535, 539-540) ↔ §7.2 (satır 1372) ↔ §7.8 (satır 1540) ↔ §4.4.4 (satır 524-525) ↔ §4.4.2 (satır 465)

**Sorun.** Hesap yaşam döngüsü dört yerde dört ayrı biçimde yazılmış. (a) Eski görev sahibinin hesabı ne zaman
kapanıyor: §7.2'ye göre görev bölümünde, §7.8'e göre devir imzalanınca, §4.4.1 ve §4.4.5'e göre dönem devrinde
("bütün organ hesapları"). (b) Dönem devri eski dönemin kapanışıdır; o güne kadar yeni YK'nin görev bölümünde açılan
hesaplar çoktan vardır ve "bütün organ hesapları" onları da kapatır. (c) DEK yenilemesi dönem kapanışından sonra
yapılıyor; "açık kalan öteki hesaplar" olarak yalnız `mudur` ve ikinci yönetici sayılıyor. Yeni dönemin organ
hesaplarının sarmalı eski DEK'te kalır ve bu kişiler giriş yapamaz. (d) Görev bölümünü ve düşmeyi sekreter kaydediyor
ve bu kayıt hesap açıp kapatıyor; matris ise hesap açma ve kapamayı yalnız `yonetici`'ye veriyor. (e) "Aynı işlemde
kapanır" diyor, ama sarmalın `guvenlik.json`'dan ve arşiv kopyalarından silinmesi dosya işidir, SQLite işlemine
girmez.

**Doğrulama.** s. 433-436: "Üyelik düştüğünde … hesap **aynı işlemde** kapanır", "Dönem devrinde bütün organ
hesapları kapanır"; s. 540: "Dönem devri (F4) | Bütün organ hesapları kapanır"; s. 539: "Kim: Düşmeyi kaydeden
yazar"; s. 1372: "Görev bölümü rol hesaplarını açar, önceki görev sahibinin hesabını kapatır" (Kim: sekreter);
s. 1540: "devir imzalanınca eski YK ve DK hesapları kapanır"; s. 521, 524-525: "ön koşul dönem kapanışı tamam …
açık kalan öteki hesaplar (`mudur`, ikinci yönetici)"; s. 465: hesap açma/kapama "Y" yalnız `yonetici`.

**Düzeltme.** §4.4.5'e tek bir olay tablosu yazılır (olay → hesaba etkisi → kim → ne zaman); öteki bölümler bu
tabloya gönderme yapar. Görev bölümü ve düşme hesap açıp kapatmaz, "hesap önerisi" üretir; yonetici onaylar.
"Dönem devri" ifadesi "eski dönemin üyeliklerine bağlı hesaplar" diye daraltılır. DEK yenilemesinde açık bütün
hesaplar geçici parolaya düşer. Dosya tarafı ailenin `gecis`/`resume_pending` deseniyle iki aşamalı yapılır.

### UY-9 · DOĞRU · orta · §7.4 (satır 1430) ↔ §7.3 (satır 1400) ↔ §5.2.5 (satır 723, 725) ↔ §5.2.7 (satır 749) ↔ §5.2.10 (satır 799)

**Sorun.** Kasadan ödenen harcamanın dosyası kapanamıyor. §7.3 kasadan doğrudan gideri uyarı ve gerekçeyle kabul
ediyor. §7.4 ise `ODENDI` için "ödeme hareketi içe aktarılıp eşlenmeden geçiş yok [S]" diyor; `KASA` kaydı bankayla
eşlenemiyor. Kasadan ödenen dosya `ODEME_TALIMATI`'nda takılır ve kapanışta sonsuza dek "açık harcama dosyası"
olarak kalır. İkinci sorun ödeme bağının sayısı: `ExpenseFile.payment_entry` 1—1, `LedgerEntry.expense_file` ise
n—1. Avans ve kalan gibi iki ödemeli bir alım ifade edilemez; aynı bağ iki yerde tutulduğu için birbiriyle
çelişebilir (O6 tek kaynak ihlali).

**Doğrulama.** s. 1400: "kasadan doğrudan gider [U]"; s. 1430: "`ODEME_TALIMATI → ODENDI` … eşlenmeden geçiş yok
[S]"; s. 725: "`KASA` kaydı bankayla eşlenmez"; s. 749: `payment_entry` → `LedgerEntry`; s. 723:
`expense_file` → `ExpenseFile`; s. 799: "`ExpenseFile` 1—1 ödeme `LedgerEntry`"; s. 1557: kapanışta açık dosya
uyarısı.

**Düzeltme.** Ödeme bağı tek yönde tutulur (`LedgerEntry.expense_file`); `payment_entry` kaldırılır. `ODENDI`
koşulu şöyle yazılır: dosyaya bağlı `KESIN` gider kayıtlarının toplamı fatura tutarına eşit ve her kayıt ya bankayla
tam eşli ya da `KASA` kaydı (kasa yolu uyarı + gerekçe). Kasa yolunda banka ödeme talimatı (E27) yerine kasa çıkış
tutanağı basılır. Test: iki taksitli ödeme ve kasadan ödeme `ODENDI`'ye ulaşır.

### UY-10 · DOĞRU · orta · O1 (satır 602) ↔ §5.2.2 (satır 666) ↔ §5.2.3 (satır 694) ↔ §5.2.7 (satır 751-752) ↔ §5.2.9 (satır 783)

**Sorun.** Birçok kısıt "iptal olmayan" koşuluna bağlanmış ama ilgili modellerde `IPTAL` durumu yok. O1, yanlış
kaydın `IPTAL`'e geçeceğini ve OYS'nin `deleted_at` koşullu kısıtlarının "iptal olmayan" koşuluna döneceğini
söylüyor. Oysa `OrganMembership` (`ADAY → SECILDI → DUSTU`), `OabBudget` ve `OabContract` durumlarında `IPTAL` yok;
`BudgetLine` ve `AgendaItem`'da durum alanı hiç yok. Silme ucu da olmadığı için şunlar ifade edilemez: yanlış
girilen bütçe satırı, yanlış aday kaydı, gündemden oyla çıkarılan madde (`genel_kurul.gundem_degisikligi`:
"Ekleme, çıkarma …"). Ayrıca `OrganMembership`'in tekil anahtarındaki `assembly`, genel kurul dışı seçimlerde ve
ilk dönemde boştur: öğretmenler kurulu, YK kararı, temsilci, MEM görevlendirmesi. SQLite tekil dizinde NULL'ları
birbirinden farklı saydığı için kısıt bu kayıtlarda etkisiz kalır ve aynı kişi aynı organa iki kez yazılabilir.
Django 5.1'in `nulls_distinct` seçeneği SQLite'ta yok. Son olarak `(assembly, order)` tekilliği SQLite'ta
ertelenemez; sıra değişikliği iki adımlı güncelleme ister.

**Doğrulama.** s. 602: "Kesinleşmemiş yanlış kayıt `IPTAL` durumuna geçer … 'iptal olmayan' koşuluna döner";
s. 666: durumlar `ADAY`/`SECILDI`/`DUSTU`, "(dönem, organ, kişi, genel kurul) iptal olmayanlarda tekil",
`assembly` "divanda zorunlu" (başka yerde boş); s. 751: "Dönem başına bir iptal olmayan bütçe" ama durumlar
`TASLAK → YK_HAZIRLADI → GK_GORUSULDU → DUYURULDU`; s. 783: "(süreç, yüklenici) iptal olmayanlarda tekil" ama
durumlarda `IPTAL` yok; s. 694 `AgendaItem` (genel kurul, sıra) tekil, durum yok; s. 1070. Kaynak: OYS kısıtı
`oys-main/…/models/membership.py:119-123` (`condition=Q(deleted_at__isnull=True)`). Doğrulama koşusu (sqlite3
3.45.1): `create unique index u on m(term,organ,person,assembly) where status<>'IPTAL'` dizini, `assembly` NULL
olan iki aynı satırı kabul etti.

**Düzeltme.** Bu modellere `IPTAL` durumu (gerekçe ve kim alanlarıyla) eklenir; `BudgetLine`'a `is_cancelled`,
`AgendaItem`'a `removed_by_vote` alanı. `OrganMembership` için iki kısmi kısıt kurulur: `assembly IS NOT NULL` →
(term, organ, person, assembly), `assembly IS NULL` → (term, organ, person); ikisi de `IPTAL` hariç. Gündem sırası
servis katmanında geçici değerle iki adımda değiştirilir.

### UY-11 · DOĞRU · orta · §7.1 (satır 1336, 1338) ↔ §15.1 A-1 (satır 2709); §5.2.3 (satır 694) ↔ B-13 (satır 2712); §9.6 E25 (satır 1916) ↔ M-11 (satır 2732)

**Sorun.** Üç kullanıcı kararı belgenin her yerine yayılmamış; aynı geçiş iki ayrı biçimde yazılmış. (a) A-1
(olağanüstü genel kurulda da ikinci toplantı yapılır): §7.1'in iki satırı eski öneriyi taşıyor. (b) B-13
(olağanüstüde gündem dışı madde uyarı + gerekçe): §5.2.3 bunu hâlâ sert diye yazıyor. (c) M-11 (müdür yazılarının
taslağını yonetici hazırlayamaz): E25 satırı tersini söylüyor. Kodlayan kişi, örneğin olağanüstü genel kurulda
ikinci toplantı alanını açmazsa `gk::test_olaganustu_ikinci_toplanti_cogunluksuz` testi (s. 2040) durum makinesiyle
çelişir.

**Doğrulama.** s. 1336: "olağanüstüde ikinci toplantı alanı açılmaz (§15 A-1)"; s. 1338: "Olağanüstüde: yeni çağrı
önerilir (§15 A-1)". Karşısında s. 698, 1068, 1282, 1339 ("olağan ve olağanüstü — §15 A-1") ve 2709 ("**Evet**").
s. 694: "sert, hukuken geçersiz karar; kural paketi bunu uyarı sayıyor: … eşitlenmeli"; karşısında s. 1073 (U),
1340 ([U], §15 B-13), 2712 ("**Uyarı + gerekçe**"). s. 1916: "mudur (yonetici taslak hazırlayabilir)"; karşısında
s. 479 ("`yonetici` taslak hazırlayamaz"), 1886 ve 2732 ("**Hayır**").

**Düzeltme.** s. 1336 "olağanüstüde de ikinci toplantı tarihi en geç 30 gün [U]", s. 1338 "olağan ve olağanüstüde
ikinci toplantı ilanı" olarak düzeltilir. s. 694'teki sert ibare ve "eşitlenmeli" notu silinir, yerine "[U],
§15.1 B-13" yazılır. s. 1916'daki "(yonetici taslak hazırlayabilir)" ibaresi silinir.

### UY-12 · DOĞRU · orta · §6.1 (satır 954, 986) ↔ §5.1 (satır 627-641) ↔ §6.4.4 (satır 1117-1125) ↔ §10.3 (satır 2084)

**Sorun.** Kural paketinin `kosul` sözlüğü okul kartına bağlanmamış. (a) Anahtarlar Türkçe (`okul.kademe`,
`okul.yerlesim_turu`), değerler küçük harf (`ortaogretim`, `il_merkezi_buyuksehir_degil`); `SchoolConfig`'te ise
alanlar `level` ve `settlement_type`, değerler büyük harf. Eşleme hiçbir yerde tanımlı değil. (b) `level` alanı
`KARMA` değerini alabiliyor, ama `kosul` tek değerlik listelerle yazılmış. Karma bir okulda (ör. ortaokul + lise)
ödül-disiplin, kontenjan ve davranış kurulu temsilcilerinin hiçbiri çıkmaz. (c) `temsilci.kampus_yonetimi`
kuralının koşulu "eğitim kampüsünde"; okul kartında kampüs alanı yok, kampüs okulları da kapsam dışı. Buna rağmen
kural ve testi F1c kapısında. Temsilci kurallarının dokuzu da F1c'de girdiği için F1c'nin temsilci evrakını (E03)
doğrudan etkiliyor.

**Doğrulama.** s. 954: `{"okul.kademe": ["ortaogretim"]}`; s. 986: `{"okul.yerlesim_turu":
["il_merkezi_buyuksehir_degil"]}`; s. 632: `level` (`… ORTAOGRETIM · YAYGIN · KARMA`); s. 634: `settlement_type`
(`BUYUKSEHIR · IL_MERKEZI_BUYUKSEHIR_DEGIL · DIGER`); s. 627-641: kampüs alanı yok; s. 291: "Kapsam dışı (sonra): …
kampüs okulları"; s. 1125: `kosul`: eğitim kampüsünde; s. 2084: `tm::test_kampus_kosulu_yoksa_satir_yok` (F1c).

**Düzeltme.** §6.1'e `kosul` anahtar sözlüğü yazılır (`okul.kademe` → `SchoolConfig.level`, `okul.yerlesim_turu` →
`settlement_type`, `okul.kantin` → `canteen_mode`, `okul.personel` → `staffing_mode`). Değerler enum değeriyle
birebir yazılır ve JSON Schema'da `enum` ile kilitlenir; D1 bilinmeyen anahtar ya da değeri reddeder. Karma okul
için `level` yerine çok değerli `levels` alanı kullanılır ve `kosul` "kesişim boş değil" diye değerlendirilir.
Kampüs için ya `SchoolConfig.in_campus` alanı eklenir ya da kural v1'den çıkarılıp kapsam dışı listesine taşınır.

### UY-13 · DOĞRU · orta · §6.2-6 (satır 1021-1023) ↔ §9.1-2 (satır 1721-1723) ↔ O7 (satır 608) ↔ §9.6 E39 (satır 1930) ↔ §10.5 (satır 2274)

**Sorun.** "Kapanmış dönemin evrakı yeniden basıldığında içerik özeti aynı çıkar" vaadinin tasarımda karşılığı
yok. Dondurulan girdiler yalnız kural paketi ve O7'nin iki anlık görüntüsü (öğrenci mevcudu, yerleşim türü). İçerik
modeli ise basım anında koddan ve güncel kayıtlardan kuruluyor. Şunlar değişebilir: antetteki okul adı ve kurum
kodu (`SchoolConfig`), sonradan düzeltilen kişi adları (`OabPerson`), program güncellemesiyle değişen içerik
kurucuları ve şablon metinleri. F4 testi aynı program sürümünde koştuğu için geçer; sahada bir güncellemeden sonra
özet değişir ve E39'un kabul ölçütü bozulur.

**Doğrulama.** s. 1022-1023: "içerik özeti … aynı çıkar"; s. 1721-1723: özet, "içerik modelinin kanonik JSON'unun
SHA-256'sı"; s. 608: O7 yalnız "öğrenci mevcudu, yerleşim türü"; s. 631: antet `SchoolConfig`'ten; s. 1718-1719:
içerik "Python'da … kurulur" (kod); s. 1930: E39 "kapanmış dönemde içerik özeti aynı".

**Düzeltme.** Kapanışta her evrakın kanonik içerik JSON'u dondurulur (`GeneratedDocument.content_json`, şifreli)
ve yeniden basım bu JSON'dan çizilir; özet kendiliğinden aynı kalır. Bu seçilmezse vaat "aynı program sürümü ve
aynı ana veriyle" diye daraltılır ve `GeneratedDocument`'e `builder_version` (program sürümü + evrak şablon sürümü)
alanı eklenir.

### UY-14 · DOĞRU · orta · §5.1 (satır 643-645) ↔ §5.2.5 (satır 726) ↔ §14 (satır 2681-2684)

**Sorun.** F1b'deki kurulum sihirbazı, sonraki fazların modellerine dayanıyor. Sihirbazın 4. adımı `BankAccount`,
`LedgerAccount` ve ilk `OpeningBalance` kayıtlarını oluşturuyor. Oysa sihirbaz F1b'de, `OabTerm` F1c'de, hesap planı
ve devreden bakiye F3'te. `OpeningBalance.term` zorunlu ve (dönem, hesap) tekil; sihirbazın adımları arasında dönem
açma yok ("ilk birlik dönemi … açılır" cümlesi bakiye adımından sonra geliyor). İlk dönemin `opened_by_assembly`
alanı için programda bir genel kurul kaydı da yok. F1'in uçtan uca kapısı ise bu sırayı istiyor: "kurulum → sihirbaz →
okul kartı → dönem".

**Doğrulama.** s. 643-645: "4) `BankAccount`, `LedgerAccount` ve ilk `OpeningBalance` … İlk birlik dönemi
(`OabTerm`) son olağan genel kurulun tarihiyle açılır"; s. 726: `OpeningBalance` `term` … "(dönem, hesap) tekil";
s. 2681: F1b "kurulum sihirbazı"; s. 2682: F1c "Birlik dönemi"; s. 2684: F3 "hesap planı … devreden bakiye"; s. 654:
`opened_by_assembly` → `GeneralAssembly` (boş bırakılabileceği yazılmamış). Plan §2.2 (s. 266-267) ve §2.4 (s. 317).

**Düzeltme.** F1b sihirbazı 1-3. adımlarla sınırlanır. "İlk birlik dönemi" adımı F1c'de, "banka, hesap planı,
devreden bakiye" adımı F3'te sihirbaza eklenir. Sıra "dönem → `OpeningBalance`" olarak yazılır. `opened_by_assembly`
için `null=True` tanımlanır ve "ilk kurulum" anlamı not edilir.

### UY-15 · DOĞRU · düşük · §6.2-2 (satır 1007-1009) ↔ §6.4 (satır 1053) ↔ D6 (satır 1038) ↔ §10.1 (satır 1996-1998)

**Sorun.** §6.2-2, bir kuralın pakete "onu kullanan kodun ve davranış testinin geldiği fazda" girdiğini söylüyor.
Oysa 16 kural F1c'de pakete girip davranış testini F2-F8'de alıyor. Bu, D6 meta testini iki yoldan birine itiyor.
D6 "her kuralın `@pytest.mark.kural` işaretli en az bir testi var" diye denetler. `kp::test_atif_kilidi[<id>]` ve
`kp::test_deger_tablosu[<id>]` parametreleri bu işareti taşıyorsa, D6 her kural için kendiliğinden geçer ve davranış
testi eksikliğini hiç yakalamaz. Taşımıyorsa F1c kapısı bu 16 kural yüzünden kırmızı kalır. Ayrıca ailenin
`--strict-markers` ayarı yüzünden `kural` işaretinin kaydedilmesi gerekiyor.

**Doğrulama.** Tablolardan yeniden sayım (betikle), F1c'de girip davranışı sonra gelen kurallar: `genel_kurul.olagan_son_ay`,
`ilan_en_az_gun`, `ikinci_toplanti_en_gec_gun`, `ikinci_toplanti_cogunluk_aranmaz` (F2); `yonetim_kurulu.toplanti_yeter_sayi`,
`karar_yeter_sayi`, `devamsizlik_siniri`, `bagis.elden_yatirma_is_gunu`, `makbuz.cilt_yaprak`, `arz_bedeli.kira_oran`,
`sozlesme_vade_gunu`, `yonetmelik_vade_gunu`, `pay_dagitimi.genel`, `il_merkezi` (F3); `arz_bedeli.isletme_oran`
(F5); `personel.sgk_saklama_yil` (F8) — 16 kural (s. 1059-1245). s. 1997: "parametreli testte her parametre kendi
işaretini alır". Kaynak: `kutuphane-main/backend/pyproject.toml:49` (`--strict-markers`).

**Düzeltme.** İşaret ikiye ayrılır: `kural_deger` ve `kural_davranis`. Pakete kural başına `davranis_fazi` alanı
eklenir. D6, `davranis_fazi` geçerli faza eşit ya da ondan küçük olan kurallarda `kural_davranis` işaretini arar.
§6.2-2'deki cümle tabloya uydurulur. İki işaret `pyproject` `markers` listesine kaydedilir.

### UY-16 · DOĞRU · düşük · §6.2-1 (satır 1003-1006) ↔ §6.2-2 (satır 1009) ↔ §6.2-3 (satır 1010-1012) ↔ §6.2-5 (satır 1017-1019)

**Sorun.** "Hata düzeltmesi" türündeki revizyonun anlamı tanımsız. §6.2-1, `rev`'i "bir hatanın düzeltilmesi" için de
artırıyor. §6.2-3 ise değer değişikliğini yalnız yürürlük tarihli ikinci kayıtla çözüyor. Hata düzeltmesinin bir
yürürlük tarihi yoktur, çünkü değer baştan yanlıştı. İki çözümden biri seçilmek zorunda ve ikisi de belgeyle
çelişiyor: ya eski yanlış değer geçmiş olaylara uygulanmaya devam eder, ya da aynı aralıkta değer değişir. İkincisinde
§6.2-2'nin "açık dönemin yeni revizyona geçişi hesap değiştirmez" cümlesi yanlış olur. §6.2-5'in geçiş ekranı da
"değişen kurallar" listesi gösteriyor.

**Doğrulama.** s. 1005-1006: "… bir hatanın düzeltilmesi"; s. 1009: "geçişi hesap değiştirmez"; s. 1010-1012:
"aynı `id` ile ikinci bir kayıt … aralıkları çakışamaz (D2)"; s. 1018: "eklenen, biten, değişen kurallar".

**Düzeltme.** Üçüncü bir değişiklik türü tanımlanır: "düzeltme" (aynı `id`, aynı aralık, değer değişir,
`degisiklik_notu`'nda işaretli). Geçiş ekranında "hesabı değişecek kayıtlar" listesi zorunlu olur. §6.2-2'deki cümle
"yalnız ekleme revizyonlarında" diye daraltılır. D2'ye "düzeltme kaydı önceki revizyondaki aynı aralığın yerini
alır" kuralı eklenir.

### UY-17 · DOĞRU · düşük · §11.1 B10, B12 (satır 2326, 2328) ↔ §11.4 (satır 2363)

**Sorun.** B10 ve B12'de "doğrulanmadı" diye bırakılan iki nokta doğrulanabiliyor ve ikisinin de cevabı "evet".
(a) python-docx'in `Document()` çağrısı varsayılan şablonu paket dizininden dosya yoluyla okuyor; bu yüzden donmuş
pakette `collect_data_files("docx")` zorunlu. Eksik kalırsa `--evrak-duman` (çıkış 12) paketli ikilide düşer.
(b) `typing_extensions` "gelebilir" değil, kesin gelir: modül düzeyinde içe aktarılıyor. Aile lisans kümesinde
zaten var (pywebview'un geçişli bağımlılığı olarak); bu yüzden §11.4'teki "Giren (gelirse)" satırı yanlış. Yeni olan
yalnız backend çalışma zamanının ona doğrudan bağlanması: `requirements.txt` pini ve `RUNTIME_MODULES` eşlemesi.

**Doğrulama.** Yerel python-docx 1.2.0: `docx/api.py:34-37` (`os.path.join(_thisdir, "templates",
"default.docx")`); `docx/blkcntnr.py:13` (`from typing_extensions import TypeAlias`, `TYPE_CHECKING` dışında);
`python_docx-1.2.0.dist-info/METADATA`: `Requires-Dist: typing_extensions>=4.9.0`. Aile: `kutuphane-main/THIRD_PARTY_LICENSES/BENIOKU.txt:353`
("typing_extensions 4.16.0"); `kutuphane-main/packaging/tests/test_lisans_kapisi.py:323, 368, 392-394` (Windows ve
Linux kümelerinde, pywebview zinciri); spec veri dosyalarını açıkça topluyor (`kutuphane-main/packaging/pyinstaller/kutuphane_defteri.spec:115-120`).

**Düzeltme.** B10 "spec `collect_submodules("docx")` + `collect_data_files("docx")` (zorunlu)" diye yazılır. B12'de
`typing_extensions` kesin olarak backend pinine ve dört halkaya alınır; lisans satırı "Kalan (artık backend
çalışma zamanında da)" olur. `--evrak-duman` paketli ikilide `Document()` ile boş belge açmayı da sınar.

### UY-18 · KISMEN · düşük · §10.5 (satır 2272) ↔ §9 (satır 1714) ↔ §9.2 (satır 1742)

**Sorun.** PDF ↔ Word içerik eşdeğerliği testinin karşılaştırma ölçütü tanımsız: test yalnız "python-docx metni
↔ pypdf metni aynı" diyor. python-docx'in `Document.paragraphs` özelliği yalnız gövde paragraflarını verir; tablolar
ve altlık dışarıda kalır. PDF'te ise altlık her sayfada tekrar eder. Altlıktaki "Sayfa n/m" Word'de bir alan
kodudur ve python-docx değerini hesaplamaz. Konum cümlesinin yeri de belirsiz: "belge altlığında, imza bloklarının
üstünde" deniyor, yani altlık mı gövde mi belli değil. Naif bir karşılaştırma F1a-3 ve F1c kapılarında ya kırmızı
yanar ya da yanlış yere yeşil yanar. Bu bulgu KISMEN: sonuç uygulamaya bağlı, ama ölçütün tanımsızlığı kesin.

**Doğrulama.** Yerel python-docx 1.2.0 ile denendi: gövde paragrafı, tablo ve altlık içeren belgede
`[p.text for p in d.paragraphs]` = `['Govde']`. Tasarım s. 1714: "OAB Defteri · E07 · Sayfa n/m"; s. 1742: "belge
altlığında, imza bloklarının üstünde".

**Düzeltme.** Karşılaştırma tanımlanır. İki çıktıdan da aynı "kanonik metin akışı" çıkarılır: gövde blokları belge
sırasıyla, tablo hücreleri satır satır. PDF'te altlık bölgesi ve sayfa numarası ayıklanır; boşluk ve satır sonu
normalleştirilir. Konum cümlesi gövdede, imza bloğunun üstünde sabitlenir; altlıkta yalnız "OAB Defteri · Exx ·
Sayfa" kalır ve karşılaştırmaya girmez.

### UY-19 · DOĞRU · düşük · §10.6 (satır 2283) ↔ §6.4.11 (satır 1253, 1268) ↔ §14 (satır 2674); §2.3.1 (satır 133)

**Sorun.** İki sayım tutarsız. (a) `r1`'in kural sayısı F1 kapısında 49, öteki iki yerde 50. (b) Kimlik tablosu
"`KD_*` (25 ad)" diyor, ama aynı satırda 19 kalan ve 5 ALMA olmak üzere 24 ad listeli.

**Doğrulama.** §6.4 tabloları betikle yeniden sayıldı: 146 kural, 43 sert, 103 uyarı, 50'si F1c'de; bölüm bazındaki
sayılar da §6.4.11 ile aynı. Yani 50 doğru, s. 2283'teki "49" yanlış. Kütüphane kaynağında `KD_[A-Z0-9_]+` taraması
24 farklı ad veriyor (`.py`, `.sh`, `.ps1`, `.iss`, `.yml`, `.ts`, `.toml`, `.spec` …); 25 sayısı iskelet
envanterinden (s. 344) aktarılmış.

**Düzeltme.** s. 2283'te "49" → "50"; s. 133'te "25 ad" → "24 ad". Envanter de düzeltilir.

### UY-20 · DOĞRU · düşük · §9.6 (satır 1901-1949) ↔ §5 (satır 665, 749, 761, 781, 784) ↔ §12.A (satır 2463) ↔ §9.2 (satır 1746) ↔ §2.3.3 (satır 200)

**Sorun.** Evrak kataloğu ile veri modeli arasında adlandırma ve veri kaynağı tutarsızlıkları var:
- E10 `OrganMembership (SEÇİLDİ)` yazıyor; enum değeri ASCII `SECILDI` (O8).
- E20 ve E21 veri kaynağı olarak `OabPerson (bağışçı)` gösteriyor; oysa §5.2.2 "bağışçı kişi kaydı açmaz (bağışçı
  adı gelir kaydında)" diyor. Doğru kaynak `LedgerEntry.donor_name`.
- E22 `DocumentRecord (defterler, tasdik)` gösteriyor; defter ve tasdik bilgisi `OfficialBook`'ta.
- E46 ve E58 `ComplianceItem (belge türü, tarih, geçerlilik)` gösteriyor; belge türü ve geçerlilik
  `BidderDocument.document_type` ve `valid_until` alanlarında.
- E26 alım komisyonunu `OrganMembership (alım komisyonu)`'ndan okuyor, `ExpenseFile.commission_members` ise ayrı bir
  çoka çok bağ: aynı bilgi iki yerde (O6 ihlali).
- §12.A'da `add_installments` için "> 9 uyarı" yazıyor. Oysa `ContractInstallment` artık kantinin 12 aylık kira
  takvimi ve "1-9 taksit kısıtı kalkar" denmiş; bu hâliyle 12 aylık her sözleşme uyarı üretir.
- Evrak kodları Kütüphane'nin kodlarıyla çakışıyor: "Kütüphane E18 kalıbı" (s. 542, 2572) ve "Kütüphane Defteri
  E13 kalıbı" (s. 1818). OAB'de E18 TEFBİS listesi, E13 genel kurul sonuç bildirimi.
- Konum kısa adı "KD", kalıntı kalıbıyla (`(?<![^\W_])kd[_:-]`) çakışıyor. `konum_kd_metni`, `KONUM_KD_METNI`
  ya da `konum-kd-…` gibi doğal tanımlayıcılar F1a kapısını kırar; `docs/` dışındaki kod taranıyor.

**Doğrulama.** s. 1901, 1911-1913, 1917, 1937, 1949 karşısında s. 665, 749, 761, 781, 784, 2463, 542, 2572, 1818,
1746, 200. Kalıp Python `re` ile katlanmış metinde denendi: `konum_kd_metni` → eşleşir, `KONUM_KD` → eşleşmez,
`konum-kd-metni` → eşleşir.

**Düzeltme.** Katalogdaki veri kaynakları modellere göre düzeltilir: `SECILDI`; `LedgerEntry.donor_name`;
`OfficialBook`; `BidderDocument`. Alım komisyonu tek kaynağa indirilir: `ExpenseFile.commission_members` kalkar ve
komisyon `OrganMembership(ALIM_KOMISYONU)` + dosya bağı ile tutulur, ya da tersi. `add_installments` notu "kantin
takviminde taksit sınırı yok; servis taksidi yalnız `fee_installments_max` bilgisi" olarak yazılır. Kütüphane
kalıplarına "KütD-E18" gibi önekli atıf yapılır. Konum kısa adları "KDT / TFB / DFT" olarak değiştirilir (ya da
kodda yalnız tam adlar kullanılır) ve kalıntı testinin örnek listesine bir negatif örnek eklenir.

---

Çürütülen aday: 12 — (1) önizlemenin geri sarılması (§8.1 A1) ile kalıcı `ONIZLEME` durumu çelişmiyor: Kütüphane
önizlemeyi geri sarıp ardından kalıcı bir PREVIEWED izi yazıyor (`kutuphane-main/backend/apps/okul/services/imports.py:53-56`);
(2) atıf kilidi Docker'da `docs/mevzuat/`i görüyor: compose `.:/repo` bağlıyor (`docker-compose.yml`); (3) tek
yazar ve HMAC zincirinin sıralanması kurulabilir: `transaction_mode: IMMEDIATE` mevcut (`backend/config/settings.py:146`);
(4) çok satırlı kısıtlar (eşleşme toplamı, dönem aralığı çakışmazlığı) SQLite'ta CHECK ile kurulamıyor, ama
IMMEDIATE işlem altında servis katmanında tutarlı kurulabiliyor; (5) çıkış kodları 0-11 aileyle aynı
(`desktop/errors.py`); (6) ara katman sırası ailenin sırasıyla aynı (`settings.py:72-101`); (7) D3'ün kaynak atıfları
doğru (`desktop/gunluk.py:246-252`, `live_restore.py:111`, `masaustu_kanca.py:123`); (8) §6.4.11 sayımları
tablolarla aynı (146/43/103/50); (9) 62 evraklık faz dağılımı ve §9.2 konum listeleri §9.6 ile aynı; (10) 71 OYS
testi (31/38/2), 29 model (5/23/1) ve 373 test sayımları tutarlı; (11) §6.4'teki 146 kural kimliğinin hepsi
§10.3'te karşılanıyor ve §6.1'in alan listesi bütün önekleri kapsıyor; (12) "`0.0.0.0` tek muafiyet `window.py`"
doğru (`desktop/window.py:59-60`).

---

## Saha ve kullanıcı deneyimi (16)

### SU-1 · DOĞRU · yüksek · §7 okuma kılavuzu (satır 1311-1315), §4.4.2 (satır 443-446, 454), §7.3 (satır 1384-1406)

**Sorun.** §7.3'ün "Kim" sütunu aylık mali işin hemen her adımını muhasibe veriyor: banka dosyası, hareketten gelir ve
gider kaydı, eşleme, `TASLAK → KESIN`, "deftere geçirildi", ay sonu. Saha ise programın başında çoğunlukla müdür
yardımcısının oturduğunu, muhasibin ayda bir geldiğini söylüyor. MY'nin muhasip yerine kayıt girip giremeyeceği
sorusunun cevabı iki bölüm arasında döngüde kalmış. §7 cevabı §4'e, §4 de §7'ye gönderiyor. İki ihtimalin ikisi de
sahada sorun çıkarır:

- **İşaretler role kilitlenirse:** MY'nin aylık TEFBİS işi gönüllünün ziyaretini bekler. TEFBİS listesine yalnız
  `KESIN` kayıt girer, `KESIN`'i de muhasip yapar.
- **Kilitlenmezse:** MY bütün işi kendi hesabıyla yapar. Denetim izi muhasibin işini MY'ye yazar. Kişisel hesap
  kararının (T1) gerekçesi olan "kim yaptı" cevabı, md. 13/4'teki sorumludan ayrışır (gelir-gider işlemlerini muhasip
  yürütür).

Aylık adımların sırası ve takvimi de hiçbir yerde birlikte yazılı değil: içe aktarım → sınıflama → kesinleştirme →
defter baskısı → TEFBİS listesi → işaretler → mutabakat → bildirim. §7.3 bunları ayrı satırlarda veriyor ve sıralarını
"serbest" bırakıyor (satır 1386).

**Doğrulama.**

- **Saha.** Saha.md'ye göre programı çoğunlukla MY kullanıyor (madde 10), muhasip ayda bir geliyor (madde 1a), MY de
  TEFBİS'e ayda bir giriyor (madde 2). Tasarım §1 bunu tekrarlıyor (satır 34-36).
- **Döngüsel atıf.** Satır 1313-1314: "`yonetici`nin başka rolün işini operatör olarak girip giremeyeceği §4 rol
  matrisindedir". Satır 443-445 ise "Rol-özel işaretler (…) §7'dedir; bu matris modül düzeyindedir" diyor.
- **Kısıt yok.** Matriste M5 beş role de Y veriyor (satır 454); işaret düzeyinde kısıt hiçbir yerde yazılmamış. Tek
  açık hüküm E18'deki "'girildi' işaretini yonetici koyar" (satır 1909).
- **Bağımlılık.** TEFBİS işareti yalnız `KESIN` kayda konuyor (satır 1404 [S]); `KESIN`'in sahibi muhasip
  (satır 1402).
- **Ölçek.** Ayda ~35 banka hareketi var (ön değerlendirme satır 64). Her biri en az dört program eylemi istiyor:
  oluşturma, `KESIN`, deftere geçirme işareti, TEFBİS işareti.
- **Saha bilgisi eksik.** Plan F0-4 muhasiple de görüşülmesini öngörüyordu (plan satır 66-67); saha.md'de yalnız MY
  görüşülmüş (satır 10). Muhasibin bu işi programda nasıl yapacağına dair saha bilgisi yok.
- **OYS.** OYS'de operatör "yalnız okul idaresi"ydi (plan satır 89).

**Düzeltme.**

1. §4.4.2'ye işaret düzeyinde bir tablo eklensin. Satırlar: `TASLAK` kayıt, `KESIN`, deftere geçirildi, TEFBİS'e
   girildi, karar deftere işlendi, harcama halkaları. Sütunlar: yapabilen roller ve "adına" girebilen roller.
2. Öneri: `yonetici` her işareti yapabilsin, ama veli rolüne ait işarette "kâğıttaki sorumlu" alanı (ör. muhasip)
   zorunlu olsun. Denetim izi iki adı birlikte yazsın: "giren: yonetici · sorumlu: muhasip". "TEFBİS'e girildi" yalnız
   `yonetici`de kalsın.
3. §7.3'e "Aylık döngü" alt bölümü eklensin. Bölüm adım sırasını, her adımın varsayılan sahibini ve takvimdeki yerini,
   hangi adımın hangisini beklediğini yazsın. Önerilen sıra:
   - ayın son iş günü: banka içe aktarımı (MY);
   - muhasibin aylık oturumunda ya da MY tarafından "adına": sınıflama ve `KESIN`;
   - ardından E17, E18, E31.
4. Pilot okulun muhasibiyle (veli) kısa bir görüşme F3'ten önce saha.md'ye eklensin.

### SU-2 · DOĞRU · yüksek · §5.2.7 `ExpenseFile` (satır 749), §5.2.10 (satır 799), §7.4 (satır 1413-1435)

**Sorun.** Bir harcama dosyasının tek bir ödeme kaydı var. Bu yüzden her dönemde tekrarlayan ödemelerin her biri ayrı
bir dosya açıyor: hizmet alımı personeli, bakım sözleşmesi, lisans. Her dosya yedi durumdan geçiyor (`TALEP → KARAR →
ALIM → BELGE → ODEME_TALIMATI → ODENDI → KAPANDI`) ve geçişleri beş-altı ayrı rol yürütüyor. Aylık bir hizmet alımı
yılda 12 dosya ve 70'i aşkın geçiş demek.

Saha 6'daki küçük alım da aynı uzun yolu yürüyor. Genel karar (A-11) gerekçeyi kendiliğinden bağlıyor ama geçiş
sayısını azaltmıyor. Oysa pilot okulda bu alımlar fiilen yalnız YK kararıyla yapılıyor. Sonuçta program, iş
azaltmasının beklendiği en sık iki durumda işi artırıyor.

**Doğrulama.**

- **Tek ödeme.** `ExpenseFile.payment_entry` tek bir `LedgerEntry`'dir (satır 749). İlişki "ExpenseFile 1—1 ödeme
  `LedgerEntry`" diye yazılmış (satır 799). "Gider kaydı dosyaya bağlanmadan dosya `ODENDI` olmaz — sert"
  (satır 749).
- **Sürekli ödeme türü var ama çoklu ödeme yok.** `SUREKLI_ODEME` türü tanımlı, ödeme alanı yine tek.
- **Dosyasız yol dar.** Hizmet alımı K3 gereği "harcama zincirinden geçer" (satır 636). Dosyasız gider yalnız banka
  masrafı, vergi, MEM payı ve arz bedeli için açık (satır 750, 1434-1435).
- **Roller.** Zincirin geçişlerini müdür, MY, sekreter, muhasip ve başkan yürütüyor (satır 1425-1431).
- **Sahada sıklık.** Sürekli ödemelerin (personel hizmet alımı, bakım sözleşmeleri, lisanslar, banka masrafı) sık
  olduğunu ön değerlendirme §1.2 yazıyor (satır 69-71). Küçük alım için saha.md madde 6 var. A-11 (satır 2753)
  yalnız gerekçe sorununu çözüyor.

**Düzeltme.**

1. `SUREKLI_ODEME` dosyası birden çok ödeme alsın (1—n). Kalıp kantindeki `ContractInstallment` olsun:
   - talep, karar, komisyon ve sözleşme bir kez girilir;
   - her dönemde yalnız fatura girilir ve ödeme hareketi eşlenir;
   - dosya sözleşme bitince ya da dönem sonunda `KAPANDI` olur.

   §5.2.7'ye bir ödeme çizelgesi modeli eklensin. Alanları: dönem, fatura no/tarih/tutar, ödeme kaydı, VİF.
2. Sınırın altındaki ve genel karar kapsamındaki küçük alım için tek ekranlık bir yol tanımlansın. Fatura, ödeme
   hareketi ve genel karar bağı bir seferde girilir. `TALEP`, `KARAR` ve `ALIM` kendiliğinden işlenir ve denetim izine
   "genel karar kapsamında kısa yol" diye düşer.
3. §7.4 tablosuna bu iki yol satır olarak eklensin. F4 kapısına "12 aylık hizmet alımı tek dosyada" senaryosu girsin.

### SU-3 · DOĞRU · yüksek · §5 O3 (satır 604), §6.1 (satır 959-961), §7 okuma kılavuzu (satır 1316-1317)

**Sorun.** Uyarılı kayıt, kaydın her yazımında gerekçe istiyor. Tasarım iki ayrı durumu aynı biçimde ele alıyor:

- **eksik:** alan henüz boş, süreçte sonra dolacak;
- **sapma:** kural bilerek uygulanmıyor.

Aynı kök neden de her kayıtta yeniden gerekçe istiyor. Örnekler:

- Karar defterinin tasdik kaydı girilmemişse, deftere işlenen her karar ayrı gerekçe istiyor (satır 1370).
- Programdan önceki seçilme sayısı bilinmeyen her aday uyarı üretiyor (satır 1088). İlk yıllarda bu, her aday demek.
- Genel kurul `TUTANAK_TAMAM`'a geçerken beyanı işaretlenmemiş her organ üyesi için ayrı gerekçe isteniyor
  (satır 1340). YK üyeleri iki beyan (suç engeli, tek birlik), DK veli üyeleri bir beyan taşıyor. Tek geçişte istenen
  gerekçe sayısı yirmiyi aşabiliyor.
- Taşınır kayıt yetkilisinin henüz düzenlemediği VİF numarası için gerekçe isteniyor (satır 1428).

Kullanıcı "sonra girilecek" yazmaya alışır. Denetleme Kurulu'nun "bütün sapmaları tek listede" görmesi (satır 604) de
anlamını yitirir, çünkü liste gerçek sapma olmayan satırlarla dolar.

**Doğrulama.**

- **Kural.** O3 açık: "Uyarılı yazma gerekçesiz geçmez" (satır 604). Her (kayıt, kural) çifti ayrı bir
  `ComplianceItem(SAPMA)` satırı açıyor.
- **İstisna yok.** §7'deki [U] tanımı "uyarı + gerekçe (sapma `ComplianceItem`'a yazılır)" diyor (satır 1316-1317).
  Taslak ya da ara durum için istisna tanınmamış.
- **Altyapı hazır.** Tasarım çözülen uyarıyı zaten izliyor ("kayıt düzeltilip uyarı kalkınca `resolved_at`",
  satır 755). Yani "eksik" durumunun altyapısı var; sorun gerekçenin istendiği anda.
- **Sayı sorun değil.** 103 uyarı kuralının 38'i seyrek yaşanan kantin ve servis akışlarındadır (satır 1265-1266).
  Asıl yük, sık akışlarda aynı uyarının kayıt başına tekrarlanması.

**Düzeltme.**

1. O3 üç durumla yeniden yazılsın: uygun · eksik · sapma. "Eksik" kayıt gerekçe istemez, panoda "tamamlanacaklar"
   listesine düşer.
2. Gerekçe yalnız kaydı kapatan geçişte, uyarı o anda hâlâ duruyorsa istensin: `KESIN`, `DEFTERE_ISLENDI`,
   `ODENDI`/`KAPANDI`, `TUTANAK_TAMAM`, dönem kapanışı.
3. Aynı kural ve aynı kök neden için tek gerekçe yeterli olsun:
   - "tasdik kaydı yok" uyarısı her defter için bir kez sorulsun;
   - "programdan önceki seçilme sayısı bilinmiyor" uyarısı ilk kurulumda tek beyanla kapansın.
4. Sık gerekçeler için seçilebilir kalıplar olsun: "genel karar no …", "VİF bekleniyor".
5. §10'a test eklensin: uyarılı taslak kayıt gerekçesiz kaydedilir; `KESIN` geçişi gerekçe ister.

### SU-4 · KISMEN · yüksek · §5.1 kurulum sırası (satır 643-645), §5.2.2 (satır 666), §7.8 kapanış denetimi (satır 1549-1551), §14 F7 (satır 2688, 2691)

**Sorun.** Program bir okula hep dönemin ortasında girecek. Pilot okulda da öyle olacak: beta F4'ten sonra başlıyor ve
2026-2027 dönemine paralel yürüyor. Tasarım dönem ortasında başlamanın yolunu tanımlamamış. Bunun dört sonucu var:

- **Mali taraf.** İlk dönem son genel kurulun tarihiyle açılıyor. Açılış bakiyesinin hangi güne ait olduğu ve genel
  kuruldan kuruluma kadarki hareketlerin girilip girilmeyeceği yazılı değil. Girilmezse kesin hesap, faaliyet raporu
  ve dönemlik duyuru kısmi çıkar. Girilirse, defterde ve TEFBİS'te zaten bulunan aylar kayıt kayıt yeniden
  işaretlenir; toplu işaret yalnız TEFBİS'te var.
- **Organlar.** `SECILDI` durumu yalnız aynı genel kurulun `ADAY` kaydından doğabiliyor (sert). Görevdeki kurul ise
  programdan önceki bir genel kurulda seçilmiş. Veli hesabı da ancak "seçildi" üyelikle ve görev bölümüyle açılıyor
  (satır 432-433). Mevcut başkana ve muhasibe hesap açmak için ya geçmiş genel kurul geriye dönük işletilmeli ya da
  kural delinmeli.
- **Seçilme sayacı.** Geçmişi bilinmeyen her kişi uyarı üretiyor (SU-3).
- **Faz sırası.** F1c organları F2'deki genel kurul akışından önce kuruyor. Yani genel kurul kaydı olmadan organ
  girişi zaten gerekiyor, ama model kuralıyla uyumlu yolu yazılmamış.

**Doğrulama.**

- **Açılış.** Satır 643-645: "İlk birlik dönemi (`OabTerm`) son olağan genel kurulun tarihiyle açılır, devreden bakiye
  elle girilir." `OpeningBalance` `ILK_KURULUM_ELLE` ve `evidence_date` alanlarını taşıyor (satır 726). Elle açılış
  yolu var, ama tarihi dönem başından farklıysa ne olacağı yazılmamış; bulgunun KISMEN olmasının nedeni bu.
- **Kapanış.** Sert koşullar: bitişe kadar bütün hareketler tam eşli ve bakiye bankaya eşit (satır 1549-1551).
- **Organ kuralı.** Satır 666: "`SECILDI` yalnız aynı genel kurulun `ADAY` kaydından olur (tek kaynak — sert)". Aynı
  satırda `assembly` alanı yalnız divanda zorunlu tutuluyor; bu da kuralın görevdeki kurula nasıl uygulanacağını
  belirsiz bırakıyor.
- **Sayaç.** Satır 1088 ve 665: geçmiş seçilmeler `external_yk_terms` alanına "eski karar defterinden beyan" diye
  giriliyor.
- **Faz sırası.** F1c organları F2'den önce kuruyor (satır 2682-2683).
- **Beta.** F4'ten sonra başlıyor ve dönemle paralel yürüyor (satır 2688, 2691).
- **Kurulum.** Kurulumdaki "başlangıç yol haritası" (plan satır 267) bu konuları kapsamıyor.

**Düzeltme.** Kurulum sihirbazına "dönem ortasında başlama" adımı eklensin; §5.1 ve §7.8'e de yazılsın:

1. **Başlama tarihi.** Programa başlama tarihi girilir. Açılış bakiyesi o günün ekstre bakiyesidir
   (`evidence_date`). Dönem başı ile başlama tarihi arası "programdan önce" sayılır: kesin hesapta ve E30'da bu aralık
   için kanıtlı tek bir toplam satırı ya da "kapsam dışı" ibaresi basılır. Kapanış denetimi hareketleri yalnız başlama
   tarihinden sonrası için arar.
2. **Görevdeki kurul.** "Programdan önce seçildi" diye girilir: `assembly` boş, `elected_by = GENEL_KURUL`, kanıt
   olarak karar defteri sıra no'su. Satır 666'daki sert kuralın istisnası açıkça yazılır.
3. **Seçilme sayısı.** Geçmiş seçilme sayıları için toplu "bilinmiyor / karar defterinden" beyanı alınır.
4. **Toplu işaret.** Geriye dönük girilen kayıtlara toplu "deftere geçirildi / TEFBİS'e girildi" işareti
   konabilir.
5. **Kapılar.** F1c kapısına "dönem ortasında kurulum" senaryosu eklenir. F7'ye pilotun beta başlangıç tarihi ve
   devralma adımları yazılır.

### SU-5 · DOĞRU · yüksek · §4.4.2 M9 (satır 459), §5.2.7 `ComplianceItem` (satır 755), §14 (satır 2677-2689), §16 R5 (satır 2792)

**Sorun.** Ön değerlendirme programı üç işle tanımlıyor: kurumsal hafıza, evrak motoru, mevzuat takvimi. M9 için de
"açılış ekranında 'bu hafta yapılacaklar'" diyor. Tasarımda ise ne takvimin ne panonun bölümü var; ikisi de hiçbir
faza konmamış.

Oysa süreye bağlı uyarıların tek teslim yolu pano: aylık YK toplantısı, kasada 5 iş günü, aylık bildirim, MEM
denetimi, belge süreleri, arz vadeleri. Yazılı olmayanlar:

- panonun hangi kaynaktan beslendiği;
- hangi rolün neyi gördüğü;
- ayda bir gelen veliye girişte ne gösterileceği (ör. "bu ay sizden beklenenler: 34 hareket sınıflanacak, 2 karar
  deftere işlenecek").

R5'in karşı önlemi ("velilere sihirbaz, büyük yazı, az ekran") da hiçbir bölümde tasarlanmamış ve hiçbir kapıda
ölçülmüyor.

**Doğrulama.**

- **Ön değerlendirme.** Programın üç tanımı §0'da (satır 11-12), M9 satır 356'da, veli yetkinliği riski satır 533'te.
- **Tasarımda pano.** Yalnız dağınık atıflarla geçiyor: satır 340, 1157 ("pano hatırlatması"), 1365 ("ay toplantısız
  geçiyorsa pano"), 1400 ("kasa sayacı panoda"), 2475 ("pano 'yaklaşan işler'").
- **Takvim kaydı.** `ComplianceItem`'ın takvim türü var, ama sürelerin "… panoya düşer, buraya kopyalanmaz" olduğunu
  söylüyor (satır 755). Panoya neyin, nasıl düştüğü ise tanımlanmamış.
- **Faz planı.** §14'ün faz satırlarında pano, takvim ya da M9 yok. F2'de yalnız E14 yıllık iş takvimi var; o da PDF
  ve xlsx belgesi (satır 1828).
- **Plan.** F1c'deki pano yalnız "başlangıç yol haritası" (plan satır 267, 303).

**Düzeltme.**

1. Yeni bir §7.9 "Pano ve takvim" bölümü yazılsın. Kaynaklar: kural paketindeki süre kuralları,
   `ComplianceItem(TAKVIM)`, modellerdeki vadeler ve SU-3'teki "tamamlanacaklar".
2. Bölüm rol başına görünümü tanımlasın:
   - muhasip: içe aktarılacak ay, `KESIN` bekleyen kayıtlar, eşlenmemiş hareketler;
   - sekreter: deftere işlenmemiş kararlar, gelecek toplantı;
   - başkan: imzalanacak bildirim ve talimatlar;
   - DK: inceleme takvimi;
   - MY: bütün liste.

   Her kalem tek tıkla ilgili ekrana götürsün.
3. Panonun iskeleti ve genel kurul süreleri F2'ye, mali vadeler F3-F4'e yazılsın. Her faz kapısında o fazın pano
   kalemleri test edilsin.
4. R5'in karşılığı somutlaşsın: veli rolleri büyük yazıyla açılsın (ailenin yoğunluk ayarı), girişte yalnız "bu ay"
   görünümü gelsin.

### SU-6 · DOĞRU · yüksek · §4.4.1 (satır 435-436), §4.4.4 DEK yenileme (satır 521-526), §4.4.5 (satır 540), §7.2 (satır 1372), §7.8 (satır 1540-1543)

**Sorun.** Eski organ hesaplarının dönem devrinde ne zaman kapanacağı üç yerde üç ayrı biçimde yazılmış: görev
bölümünde, devir imzalanınca ve dönem devrinde. Hangisi seçilirse seçilsin iki pratik sorun çıkıyor:

1. **Eski dönemi kimin kapatacağı belli değil.**
   - Devir genel kurul günü yapılıyor (md. 10/1-ç) ve eski muhasibin hesabı o gün kapanıyor.
   - Eski dönemin son haftalarının hareketleri henüz girilmemiş. Sert kapanış koşulları ise bekliyor: bitişe kadar
     bütün hareketler tam eşli olmalı, `TASLAK` kayıt kalmamalı. Bu iş MY'ye ya da yeni muhasibe düşüyor, ama tasarım
     bunu yazmıyor.
   - Kapanışı "baskan onaylar" (satır 1543). O tarihte açık tek başkan hesabı yeni başkanınki; yani yeni başkan
     yürütmediği dönemi onaylıyor.
   - Eski dönem kapanmadan sonraki genel kurul gelirse yeni dönem açılamıyor, çünkü en çok bir dönem `KAPANISTA`
     durumunda olabiliyor (satır 654). Bu durumda ne yapılacağı yazılmamış.
2. **Yeni velilerin parolaları ikinci kez sıfırlanıyor.** DEK yenilemenin ön koşulu dönem kapanışı. Yeni kurulun
   hesapları ise görev bölümünde, kapanıştan haftalar önce açılıyor. Yenileme "açık kalan öteki hesapları" geçici
   parolaya düşürdüğü için yeni kurulun hesapları birkaç hafta sonra yeniden sıfırlanıyor. MY de bütün yeni kurula
   ikinci kez geçici parola dağıtıyor.

**Doğrulama.**

- **Üç ayrı kapanış anı.**
  - Satır 435: "Dönem devrinde bütün organ hesapları kapanır."
  - Satır 1372: "Görev bölümü rol hesaplarını açar, önceki görev sahibinin hesabını kapatır."
  - Satır 1540: "devir imzalanınca eski YK ve DK hesapları kapanır."
- **Devrin zamanı.** Satır 1541: "toplantı sonunda bütün tutanak ve belgeler yeni YK'ye teslim edilir".
- **DEK yenileme.** Ön koşulu "dönem kapanışı tamam" (satır 521). Yenilemede "açık kalan öteki hesaplar (mudur, ikinci
  yönetici) geçici parolaya düşer" (satır 525); bu parantez yeni dönemin hesaplarını hesaba katmıyor.
- **Varsayılan.** M-2'nin varsayılanı "Yapılır" (satır 2774).
- **Banka uyarısı.** Devirde "banka bakiyesi = mutabık defter bakiyesi" uyarısı var (satır 1542). Aylık ritimde
  (saha 1a) bu uyarı genel kurul günü hemen her yıl çıkar.

**Düzeltme.**

1. **Tek kural.** Eski organ hesapları devirde kapansın (satır 1540 esas alınsın); satır 435 ve 1372 buna göre
   düzeltilsin. Eski dönemin kalan işi MY'ye "adına" girişle kalsın (SU-1).
2. **Kapanış onayı.** Kapanışı MY onaylasın, yeni başkana bilgi gitsin. "baskan onaylar" ifadesi düzeltilsin.
3. **DEK yenilemenin ön koşulu.** "Dönem kapanışı tamam" yerine şu olsun: "eski organ hesapları kapandı, yeni organ
   hesabı henüz açılmadı". Yani yenileme devirle görev bölümü arasında yapılsın. Yeni hesaplar yeni DEK'le, tek
   geçici parolayla açılsın. §7.8'deki adım sırası buna göre yazılsın.
4. **Kapanmayan dönem.** `KAPANISTA` dönem bir sonraki genel kurula kadar kapanmazsa ne olacağı §7.8'e yazılsın:
   uyarı takvimi ve MY için son tarih.

### SU-7 · DOĞRU · orta · §5.2.5 `LedgerEntry` (satır 723), §7.3 (satır 1403-1404), §8.3 (satır 1639-1640), §16 R1 (satır 2788)

**Sorun.** Program defteri ve TEFBİS'i doldurmuyor (A-13, K6), ikisi de yine elle yazılıyor. Buna bir iş ekleniyor:
kullanıcı elle yazdıktan sonra programa dönüp her kaydı işaretliyor.

- "Deftere geçirildi" işareti kayıt başına defter ve sayfa istiyor.
- Toplu işaret yalnız TEFBİS'te var.
- Karar defterine işlenen her kararın sıra no'su ve sayfası tek tek elle giriliyor.

R1, "çift iş algısı"na karşı "iş azalır" diyor, ama bu geri işaretleme yükünü hesaba katmıyor ve hiçbir kapıda
ölçmüyor.

**Doğrulama.**

- **Kayıt başına alan.** `posted_book`, `posted_page` ve `posted_at` her kayıtta ayrı tutuluyor (satır 723).
- **Defter işareti.** Satır 1403: "il/ilçe MEM tasdikli gelir-gider defteri ve sayfası girilir".
- **Toplu işaret.** Yalnız TEFBİS için yazılmış (satır 1639).
- **Karar.** Defter sıra no'su ve sayfası kararda elle tutuluyor; sıra no "geri gider ya da atlarsa uyarı"
  (satır 706, 1370).
- **Elle yazım sürüyor.** A-13'e göre program yalnız geçirilecek baskıyı üretiyor (satır 2755).
- **Ölçek.** Ayda ~35 kayıt (ön değerlendirme satır 64).

**Düzeltme.**

1. E17 tasdikli defterin sayfa düzeninde basılsın; sayfa başına satır sayısı okul ayarı olsun. Baskıdan sonra tek bir
   işlem ("bu baskı X defterinin a-b sayfalarına geçirildi") bütün satırların sayfasını kendiliğinden yazsın.
2. Kararın sıra no'su ve sayfası, defterdeki son kayıttan öneri olarak dolsun.
3. TEFBİS toplu işareti E18'in satır sırasıyla çalışsın.
4. F7 kabulünde aylık geri işaretleme süresi ölçülsün; böylece R1'in iddiası sınanır (SU-9).

### SU-8 · KISMEN · orta · §5.2.7 `MonthlyReport` (satır 754), §6.4.6 (satır 1153), §7.3 Ay sonu (satır 1406), §9.6 E31 (satır 1922)

**Sorun.** Md. 18/5 aylık bildirimi "her ayın sonunda" istiyor. Bildirimin verisi kayıtlardan, kayıtlar da banka içe
aktarımından geliyor; muhasip ise ayda bir geliyor. Bu yüzden ayın son günlerinin hareketleri bildirim üretilirken
çoğu zaman programda yok. Program iki yoldan birine zorlanıyor, ikisi de sorunlu:

- Bildirim zamanında, eksik veriyle basılır. O aya tarihli kayıtlar sonradan girilince E31 kabulündeki "Ay toplamları
  E17 ile aynı" koşulu bozulur.
- Bildirim tam veriyle ama geç basılır. Bu durumda "ay bitti, bildirim yok" uyarısı her ay gerekçe ister (SU-3).

Tasarım bildirimin kesim tarihini ve teslimden sonra o aya düşen kaydın nereye gideceğini yazmıyor.

**Doğrulama.**

- **Mevzuat.** Yön. md. 18/5: "her ayın sonunda yazılı olarak bildirir".
- **Model.** `MonthlyReport.snapshot` "kayıtlardan" dolar, durumu `TASLAK → TESLIM_EDILDI` (satır 754).
- **Kural ve kabul.** "Ay bitti, bildirim yok → uyarı" kuralı satır 1153'te, E31 kabulü satır 1922'de.
- **Saha.** Muhasip ayda bir geliyor (saha.md madde 1a).
- **Rehber.** GNL-OAB-RH-001 Bölüm 6, YK toplantısı için "öneri: ilk hafta", başkanın bildirimi için "her ayın son iş
  günü" diyor.
- **Neden KISMEN.** Sürenin kendisi mevzuattan geliyor ve uyarı yerinde. Eksik olan, verinin hangi tarihte
  kesileceği.

**Düzeltme.**

1. E31'e "… tarihine kadar içe aktarılan hareketler" diye bir kesim satırı basılsın.
2. `TESLIM_EDILDI`'den sonra o aya tarihli yeni bir kayıt girilirse, kayıt sonraki ayın bildiriminde "önceki aylara ait
   geç kayıtlar" bölümüne girsin.
3. E31 kabulü "kesim tarihine kadar E17 ile aynı" diye düzeltilsin.
4. SU-1'deki aylık döngüde ayın son iş günü banka içe aktarımı MY'nin adımı olsun; başkanın bildirimi o içe aktarımdan
   basılsın.

### SU-9 · DOĞRU · orta · §14 kapılar (satır 2680-2689), §2.1 F0-d (satır 83), §16 R1 ve R5 (satır 2788, 2792)

**Sorun.** Faz kapılarının hiçbiri kullanıcıyı ölçmüyor:

- F2-F6 "evrak birebir üretilir" ve "uydurma dönem programdan kapanır" diyor.
- F7 "saha kabulü protokolü uyarlanır" diyor, ama ölçüt vermiyor.
- Böylece tasarımın iki ana riski, R1 (çift iş) ve R5 (veli yetkinliği), hiçbir kapıda sınanmıyor.

F7'deki "paralel beta (defter ve TEFBİS esas kalır)" ifadesi, beta boyunca üçlü kayıt demek. Neyin ölçüleceği
yazılmazsa beta R1'i doğrulayan bir deneyime döner. Ayrıca:

- Tek saha, geliştirmenin yürütüldüğü okul.
- Mali akışın asıl kullanıcısı olan muhasiple hiç görüşülmedi.
- F2 kabulü geçmiş bir genel kurulun evrakını sonradan yeniden üretiyor. Genel kurul sihirbazının canlı kullanımı
  (15 gün kuralı, ikinci toplantı) ancak bir sonraki Ekim'de yaşanacak; kapı bunu planlamıyor.

**Doğrulama.**

- **Kapılar.** §14'ün kapı sütunu satır 2680-2689'da.
- **Tek saha.** F0-d yalnız pilot okulu öngörüyor (satır 83; saha.md satır 3-4). Ön değerlendirmenin başlığına göre
  pilot okul, "geliştirmenin yürütüldüğü ortaöğretim kurumu" (satır 5).
- **Görüşmeler.** Plan F0-4, MY ve muhasiple görüşülmesini öngörüyordu (plan satır 66-67); saha.md'de yalnız MY
  görüşülmüş (satır 10).
- **F2 kabulü geçmişe dönük.** Kapı "pilot okulun 2026-2027 genel kurul akışı" diyor (satır 2683). Olağan genel kurul
  Ekim sonuna kadar yapıldığından (satır 1059) bu toplantı, belgenin tarihi olan 31.10.2026'da çoktan yapılmış olmalı.

**Düzeltme.** F7 kapısına ölçülebilir saha ölçütleri yazılsın:

1. Muhasip ve sekreter (veli) aylık işini MY yardımı olmadan yapar; gözlem notu saha.md'ye girer.
2. MY'nin aylık TEFBİS ve defter işinin süresi, programla ve programsız iki ay karşılaştırılır.
3. Beta süresince defter E17'den, TEFBİS E18'den yazılır. Böylece paralel yürütme ek bir elle kayıt doğurmaz.
4. Bir sonraki olağan genel kurul sihirbazla canlı yürütülür; beta takvimi Ekim'i kapsar.
5. F3'ten önce pilot okulun muhasibiyle görüşülür.

### SU-10 · DOĞRU · orta · §4.4.2 dipnot ² ve ⁴ (satır 475-479), §7.4 TALEP (satır 1425), §9.6 E25 (satır 1916), §15.2 M-11 (satır 2732)

**Sorun.** Okul yönetiminin harcama talep yazısını (E25) kimin hazırlayacağı belgede çelişkili. Bu yazı her harcama
dosyasının ilk halkası ve yılda 20-40 kez yazılıyor. M-11 okunduğu gibi uygulanırsa talep, programı fiilen kullanmayan
müdürün hesabına bağlanır (saha 10). Sonuç ikisinden biri olur:

- müdür her talep için programa girer;
- ya da MY talebi "gelen evrak" olarak kaydeder ve programın E25'i hiç kullanılmaz. Bu durumda E27 kontrol listesinin
  E25'ten dolan kısmı boş kalır.

**Doğrulama.** Tasarımın ilgili cümleleri birbirini tutmuyor:

- **E25 satırı.** "Üreten: mudur (yonetici taslak hazırlayabilir)" (satır 1916).
- **M-11.** "K2'deki üç müdür yazısının taslağını `yonetici` hazırlayabilsin mi? **Hayır**" (satır 2732). K2'nin
  saydığı yazıların ilki harcama talebi (satır 66).
- **Dipnot ².** "Yönetmelik 'okul yönetimi' der; `yonetici` (müdür yardımcısı) zaten yazar" (satır 475-476).
- **Dipnot ⁴.** "`yonetici` taslak hazırlayamaz" kısıtını yalnız md. 27/3 yazısı için koyuyor (satır 479).
- **§7.4.** `TALEP` adımında "mudur (talep yazısını yazar) ya da yonetici (gelen talebi `DocumentRecord`'a kaydeder)"
  diyor (satır 1425).
- **E27.** Kontrol listesi E25'ten doluyor (satır 1918).

M-11 §15.2'de bir varsayılan, kullanıcı kararı değil. K2 müdürü sınırlıyor ("yalnız kendi yazılarını yazar"), MY'yi
sınırlamıyor.

**Düzeltme.** M-11 yalnız şu yazılarla sınırlansın: md. 27/3 uyarısı (E35) ile md. 9/1 ve 9/6 çağrıları. E25'in
taslağını `yonetici` hazırlasın; müdür kâğıdı imzalasın ya da isterse kendi hesabından tek tıkla "onayladım" işareti
koysun. Dipnot ², §7.4, E25 ve M-11 bu cümleyle eşitlensin.

### SU-11 · KISMEN · orta · §5.2.4 (satır 704, 706), §6.4.2 (satır 1093-1094), §7.2 (satır 1360, 1366-1370)

**Sorun.** Sahada yeter sayısız toplantıda alınmış ya da üç kabul oyuna ulaşmamış kararlar da karar defterine
yazılabiliyor. Sert kurallar bu kararların programa kaydını tümden engelliyor: program böyle bir kararı "deftere
işlendi" diye bile tutamıyor. Ön değerlendirme ise programın "defterin dijital izini" tutacağını söylüyor.

Denetleme Kurulu'nun görmesi gereken bu usulsüzlük programda yalnız bir yerde kalıyor: sonraki kararda çıkan "sıra no
atladı" uyarısının gerekçe metni. Kullanıcı ise kararı programa sokmak için katılımı ya da oyları olduğundan yüksek
girmeye itiliyor.

**Doğrulama.**

- **Toplantı kuralı.** `YAPILDI` için en az dört üye gerekiyor (sert; satır 704, 1366).
- **Karar kuralı.** `KABUL_EDILDI` için toplantının `YAPILDI` olması ve en az üç kabul oyu gerekiyor (sert; satır 706,
  1369).
- **Defter işareti.** `DEFTERE_ISLENDI` yalnız `KABUL_EDILDI`'den gelebiliyor (satır 1360).
- **Ön değerlendirme.** §0-4 programın "defterin dijital izini tutar" olduğunu söylüyor (satır 31-33). §1.3-3, YK'nin
  toplanamadığını ve imzaların evlerde toplandığını anlatıyor (satır 87-88).
- **Tasarım.** §3.1'e göre yardımcı kaydın değeri, taslağın defterdeki hâliyle tutarlılığı (satır 235-236).
- **Neden KISMEN.** Programın kendi ürettiği kararda sert kural yerinde. Eksik olan, defterde fiilen var olan kararın
  kaydı.

**Düzeltme.** `BoardDecision`'a `DEFTERDE_SAKAT` durumu eklensin ("deftere yazılmış, yeter sayısı yok"). Bu durumdaki
kayıt:

- yalnız defter sıra no'su, sayfa ve gerçek oyları taşır;
- hiçbir bağlı akışı beslemez (harcama, koçan, görev bölümü);
- DK listesine ve kapanış denetimine kendiliğinden düşer.

Sert kuralın anlamı "kaydedilemez"den "program bu kararı geçerli saymaz"a çevrilsin.

### SU-12 · KISMEN · orta · §2.2 TK12 (satır 105), §4.3 tehdit 10 (satır 400), §4.4.4 (satır 515, 526-528), §15.5 M-2 (satır 2774)

**Sorun.** Kurtarma anahtarının nerede saklanacağı iki farklı biçimde yazılmış:

- tehdit modelinde "müdürlükte kapalı zarf";
- DEK yenilemede ve M-2'de "devir dosyasına girer".

Devir dosyası (E37) eski kuruldan yeni kurula, yani gönüllü velilere geçiyor. Ayrıca her dönem yeni bir anahtar
basılıyor ve eskileri, eski yedekler saklandıkça kalıyor; okulda yıllar içinde birden çok zarf birikiyor. Yedek
başlığında anahtarın kimliği ya da tarihi yok. Yeni bilgisayara taşırken ya da arızadan sonra hangi zarfın hangi
yedeği açacağı bilinemiyor.

**Doğrulama.**

- **Müdürlük.** Satır 400: "Yalnız `yonetici` yeniler; müdürlükte kapalı zarf".
- **Devir dosyası.** Satır 105 ve 526: "yeni kurtarma anahtarı basılır, … devir dosyasına girer". Satır 527-528: eski
  kurtarma anahtarı "devir dosyasında kapalı zarfta kalır".
- **E37.** Devreden ve devralan kurul imzalıyor (satır 1928).
- **Yedek başlığı.** `{surum, kdf, kurtarma}` (satır 515); anahtar kimliği yok.
- **Neden KISMEN.** Belge "devir dosyası"nın ne olduğunu açık söylemiyor: MY'nin devir notu mu, YK'ler arası devir mi?
  MY devir notu satır 542'de ayrıca anılıyor.

**Düzeltme.**

1. "Devir dosyası" ifadesi "okul müdürlüğünde saklanan kurtarma anahtarı zarfı" diye değiştirilsin.
2. E37'ye zarfın kendisi değil, yalnız "kurtarma anahtarı müdürlükte, üretim tarihi …" satırı girsin.
3. Anahtar çıktısına ve yedek başlığına anahtarın üretim tarihi ve sıra numarası yazılsın. Geri yüklemede program "bu
   yedek … tarihli anahtarla açılır" desin.
4. Kılavuza zarfın saklanması ve yedekler imha edilince zarfın da imhası yazılsın.

### SU-13 · DOĞRU · orta · §14 (satır 2677-2689), kılavuz atıfları (satır 232, 265, 386, 396, 405, 544, 581, 587, 894, 1631, 2778), §9.5-9.7 katalog

**Sorun.** Tasarım birçok konuyu kılavuza bırakıyor: konum ibaresi, BitLocker ve ayrı Windows hesabı, BSG sapması,
yeni bilgisayara taşıma kontrol listesi, çıktıların imhası, dürüst sınırlar, veri sorumlusu sorusu. Buna karşılık
kılavuz yalnız F1 planında bir madde olarak geçiyor; F2-F7 kapılarında ne kılavuz ne eğitim var.

Kurul her Ekim yeniden kuruluyor ve her yıl yeni gönüllü veliler programı baştan öğreniyor. Tasarımda bu yeni kurulun
ilk oturumu için bir yol yok. Hesap açılırken veliye verilecek bir belge de yok (tanıtıcı, rol, ilk giriş, "bu
programda sizin işiniz"). Uygulamada eğiticilik MY'ye kalıyor ve bu yük hiçbir yerde görünmüyor.

**Doğrulama.**

- **Kılavuz atıfları.** Kılavuz en az 15 yerde anılıyor (başlıktaki satırlar).
- **Plan.** Plan §2.4'ün F1 kapısında "Kılavuzda F1 bölümleri (kurulum, okul kartı, kullanıcılar, organlar)" maddesi
  var (plan satır 320).
- **Tasarım kapıları.** §14'ün kapı sütununda kılavuz ya da eğitim maddesi yok (satır 2680-2689).
- **Yıllık değişim.** Ön değerlendirme §1.1: "Her ekimde yeni ekip" (satır 52).
- **Katalog.** E01-E62 arasında hesap teslim ya da rol tanıtım belgesi yok. §9.7 yalnız kurtarma anahtarı çıktısını
  anıyor (satır 1968).

**Düzeltme.**

1. Plan §2.4'teki F1 deseni §14'teki her kapıya taşınsın: "kılavuzun bu faza ait bölümü yazıldı".
2. Kılavuza "yeni kurulun ilk ayı" bölümü eklensin. Her rol için bir sayfa: ne zaman gelinir, hangi kâğıtla gelinir,
   hangi ekrana bakılır.
3. Kataloğa hesap açılışında basılan bir "hesap teslim pusulası" eklensin: tanıtıcı, rol, ilk giriş, parola kuralları
   ve kilitleme. Parola pusulaya yazılmasın ya da kapalı zarfta verilsin (BSG Yön. md. 10/1).
4. R5'in karşı önlemi bu iki belgeye bağlansın.

### SU-14 · KISMEN · düşük · §8.3 (satır 1637), §9.6 E18 (satır 1909)

**Sorun.** TEFBİS, kişiden gelen kayıtta T.C. kimlik no ve ad-soyad istiyor. K9 varsayılan olarak kapalı olduğundan
MY bu numarayı her bağış satırında kâğıttan bulacak. Tasarım bu kâğıdın ne olduğunu iki yerde farklı söylüyor: §8.3
"makbuzdan ya da dekonttan" diyor, E18 kabulü "kâğıt koçandan" diyor. Bankaya havaleyle gelen bağışın koçan yaprağı
yok. Dekontta T.C. kimlik no'nun bulunup bulunmadığı da tasarımda doğrulanmamış.

**Doğrulama.**

- **TEFBİS.** Ön değerlendirme §2.5'e göre kişiden gelen kayıtta "T.C. kimlik no ve ad-soyad zorunlu"
  (2009 kılavuzu; satır 201).
- **K9 gerekçesi.** "MY bunu makbuz/dekonttan doğrudan TEFBİS'e girebilir" (satır 518).
- **İki ifade.** Tasarımın satır 1637'si "makbuzdan ya da dekonttan girilecek", satır 1909'u "kâğıt koçandan girilir"
  diyor.
- **Neden KISMEN.** K9 bilerek alınmış bir karar. Eksik olan, listenin MY'yi doğru kâğıda götürmesi.

**Düzeltme.** E18'de kişiden gelen her satıra bir "kimlik no kaynağı" sütunu eklensin. Değerleri: makbuz
seri-cilt-sıra, dekont referansı ya da "kâğıt kaynak yok — bağışçıdan alınmalı". İki ifade bu sütuna göre tek metinde
birleşsin.

### SU-15 · DOĞRU · düşük · §4.5 Ekran (satır 564), §14 kapılar (satır 2680-2689)

**Sorun.** Hedef cihaz, 4 GB RAM ve 1366×768 ekranlı eski okul bilgisayarı. Bu hedef yalnız §4.5'te bir cümle olarak
geçiyor; hiçbir faz kapısında elle ya da otomatik olarak denetlenmiyor. En yoğun ekranlar (banka eşleme, genel kurul
tutanağı, harcama dosyası) bu çözünürlükte ilk kez sahada görülecek.

**Doğrulama.**

- **Hedef.** "1366×768" yalnız satır 564'te geçiyor.
- **Kapılar.** F1a-F7 kapılarında ekran ya da bellek ölçütü yok.
- **Gereksinim.** Ön değerlendirme §5.2 bu hedefi işlevsel olmayan gereksinim sayıyor (satır 370).

**Düzeltme.**

1. F1a'nın elle denetim listesine (`NOTLAR.md`, satır 569) bir madde girsin: ana ekranlar 1366×768'de yatay
   kaydırmasız açılır.
2. Mali ekranlar için aynı denetim F3 kapısına girsin; denetim ~35 hareketli bir ayla yapılsın.
3. F7 saha kabulünde, 4 GB'lık makinede açılış süresi ve bir evrakın PDF üretim süresi not edilsin.

### SU-16 · KISMEN · düşük · §4.2 Kapanış (satır 359-360), §4.5 Çarpı (satır 557)

**Sorun.** Çarpı programı onay sormadan kapatıyor. Adım adım kayıt yalnız "uzun akışlarda" var (genel kurul
sihirbazı, harcama zinciri). Gönüllü velinin uzun serbest metin yazdığı alanlar bu kapsamda değil: karar metni, DK
bulgusu, gerekçe. Yanlışlıkla basılan çarpı bu metinleri siler. Bilgisayar kullanımı zayıf veli kullanıcıda (R5) bu
sık yaşanır.

**Doğrulama.**

- **Kabul edilen risk.** Satır 359-360: "Kaydedilmemiş form kaybı kabul edilen risktir; uzun akışlar … adım adım
  sunucuya kaydedilir".
- **Kullanıcı kararı.** T6, çarpının programı kapatmasını istiyor (satır 79).
- **Tasarım seçimi.** "Onay sorulmaz" kısmı ise tasarımın Kelebek Sınav'dan aldığı davranış (TK5, satır 98).
- **Neden KISMEN.** T6 bağlayıcı; önerilen düzeltme T6'yı değiştirmiyor.

**Düzeltme.**

1. Serbest metinli formlar (`BoardDecision.text`, `AuditReport.findings`, gerekçe) açıkken kısa aralıklarla sunucuya
   `TASLAK` kaydı yapılsın; bu modellerde `TASLAK` durumu zaten var. Kapanış davranışı (T6) değişmez.
2. Program yeniden açıldığında "yarım kalan taslak" panoda görünsün.
3. Taslak tarayıcı deposuna yazılmasın, çünkü kişisel veri orada şifresiz kalır (TK8).

Çürütülen aday: 7

---

## Eksiklik ve tutarlılık (18)

*Denetlenen: `docs/tasarim/2026-10-31-genel-tasarim.md` (taslak v1). Satır numaraları bu belgedendir; başka dosyadan
yapılan atıflarda dosya adı yazılır. Karşılaştırılanlar: CLAUDE.md (diskteki güncel hâli), plan, ön değerlendirme, OYS
ve iskelet envanterleri, genel OAB setinin metni (FR-001…023, RH-001). Dağılım: yüksek 3 · orta 12 · düşük 3.*

### EK-1 · DOĞRU · yüksek · §7.1 (satır 1336, 1338) ↔ §15.1 A-1 (satır 2709); §5.2.3 (satır 694) ↔ §15.1 B-13 (satır 2712)

**Sorun.** İki kullanıcı kararı bütün bölümlere işlenmemiş.
- **A-1.** Kullanıcı, md. 9/2'deki çoğunluk aranmayan ikinci toplantının olağanüstü genel kurulda da uygulanmasına
  karar verdi. §7.1'in iki hücresi kararın tersini söylüyor: `CAGRILDI → ILAN_EDILDI` satırında "olağanüstüde ikinci
  toplantı alanı açılmaz (§15 A-1)", `ILAN_EDILDI → YETER_SAYI_YOK` satırında "Olağanüstüde: yeni çağrı önerilir
  (§15 A-1)". Hemen alttaki satır (1339) ise "ikinci toplantı; olağan ve olağanüstü — §15 A-1" diyor. Alan açılmazsa
  `gk::test_olaganustu_ikinci_toplanti_cogunluksuz` (2040) yazılamaz.
- **B-13.** Kullanıcı, olağanüstü genel kurulda gündem dışı madde için "uyarı + gerekçe" dedi. §5.2.3'teki
  `AgendaItem` satırı hâlâ "sert, hukuken geçersiz karar; kural paketi bunu uyarı sayıyor: §6.4.1 ile birleştirmede
  eşitlenmeli; §15'e öneri B-13" diyor. B-13 artık öneri değil, karar.

**Doğrulama.** §15.1 A-1 (2709): "**Evet** — md. 9/2'deki ikinci toplantı … olağanüstüde de uygulanır". Aynı karar
§5.2.3 (698), §6.4.1 `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` notu (1068: "Olağan ve olağanüstü GK") ve
plan §1.8'de (plan:236) var. B-13 (2712): "**Uyarı + gerekçe**"; §6.4.1 `genel_kurul.olaganustu_gundeme_baglilik`
U (1073), §7.1 (1340) "[U] (§15 B-13…)", plan §1.8 (plan:238). Çelişen yalnız 1336, 1338 ve 694.

**Düzeltme.** 1336: "olağanüstüde de ikinci toplantı tarihi birinciden en geç 30 gün sonra [U] (A-1)". 1338:
"Olağanüstüde de ikinci toplantı ilanı (A-1)"; "yeni çağrı önerilir" silinsin. 694: "Olağanüstüde çağrı gündemi
dışında madde eklenirse uyarı + gerekçe (`genel_kurul.olaganustu_gundeme_baglilik`; kullanıcı kararı B-13)";
"sert, hukuken geçersiz karar" ve "eşitlenmeli" ibareleri silinsin.

### EK-2 · DOĞRU · yüksek · §4.4 (satır 426, 458, 472-479) ↔ §7.6-§7.7 ↔ §9.3 (satır 1765-1766) ↔ §9.6 (satır 1886, 1896, 1916) ↔ §10.5 (satır 2266) ↔ §15 M-5, M-6, M-11 (satır 2710-2711, 2732)

**Sorun.** Müdürün ve Denetleme Kurulunun yazma yetkisi (K2 + M-5, M-6, M-11) bölümlere göre değişiyor.
1. **M-5 §9'a işlenmemiş.** §2.1 K2 (66), matris dipnotu ¹ (472-474) ve §7.1 (1335) müdüre olağanüstü genel kurul
   çağrısını veriyor. §9.3 müdürün yazılarını "E25 harcama talebi, E35 uyarı, yeni okulda E05 çağrı" diye, §9.6 (1886)
   "`mudur` yalnız kendi yazılarını (E25, E35, yeni okulda E05) üretir" diye sayıyor; E05'in Üreten'i (1896) "sekreter,
   yonetici; yeni okulda mudur". Olağanüstü çağrı hiçbir kodda müdürün değil. §10.5'teki
   `ev::test_yk_ve_gk_belgelerinde_mudur_yazar_degil` (2266) E05'te müdürü yalnız yeni okulda yazar sayıyor; müdürün
   olağanüstü çağrısı bu testi kırmızıya çevirir.
2. **M-6 katalogda karşılıksız.** §7.1 (1335) evrak olarak "Olağanüstü genel kurul çağrı yazısı (müdür ya da DK)"
   sayıyor; katalogda bu adla kod yok. §9.6 (1886) DK'yi E02, E32, E33 ile sınırlıyor; E32'nin kabulünde yalnız
   "aykırılıkta md. 14/5 seçeneği" var.
3. **M-11 bayat ve çelişkili.** M-11 (2732): "K2'deki **üç** müdür yazısının taslağını `yonetici` hazırlayabilsin mi? —
   **Hayır**". K2 bugün dört yazı sayıyor (66; CLAUDE.md K2). Harcama talebi K2 yazısıdır, ama E25'in Üreten'i (1916)
   "mudur (yonetici taslak hazırlayabilir)", matris dipnotu ² (475-476) "`yonetici` (müdür yardımcısı) zaten yazar".
   Dipnot ⁴ (479) M-11'i yalnız uyarı yazısına uyguluyor.
4. **§7'de müdür kantin ve servis işinde.** "Kim" sütunu müdürü şu geçişlere koyuyor: `BILDIRILDI` "mudur, yonetici"
   (1480), `IMZALANDI → YURURLUKTE` "yonetici, mudur" (1484), servis `HAZIRLIK`, `INCELEME → DEGERLENDIRME`,
   `KOMISYON_KARARI → ONAYDA → KESINLESTI`, `KESINLESTI → TEBLIG_EDILDI`, `TEBLIG_EDILDI → SOZLESME` (1515, 1519,
   1521-1523). Matriste kantin ve serviste `mudur` **O** (462); KE-19 (2731): "müdür rolüne K2'de yazılanlardan başka
   yetki eklenmez".
5. **MEM'e bildirim.** Matris (458) müdür yazılarına "MEM'e bildirim (md. 27/3)" ekliyor. K2 yalnız uyarıyı sayıyor;
   bildirimin evrak kodu da yok (E35 yalnız "birlik başkanına yazılı uyarı"). §4.4.1 müdür satırının dayanağında
   (426) md. 9/6 yok.

**Doğrulama.** Satırlar yukarıda alıntılandı. CLAUDE.md:79 K2: müdür "yalnız kendi yazılarını (harcama talebi, md. 27/3
uyarısı, yeni okulda genel kurul daveti, olağanüstü genel kurul çağrısı) yazar". Plan §1.8 (plan:237): "Müdür
olağanüstü genel kurul çağrısını, DK md. 14/5 çağrısını programda yazar".

**Düzeltme.**
- E05 Üreten: "sekreter, yonetici; yeni okulda ve olağanüstüde çağırana göre mudur (M-5)". §9.3 ve §9.6 listelerine
  "olağanüstü GK çağrısı (E05)" eklensin; §10.5 testinin istisnası "yeni okul ve müdürün olağanüstü çağrısı" olsun.
- DK'nin md. 14/5 çağrısı: ya "E32'nin çağrı bölümü" diye yazılsın ya ayrı kod verilip §9.6 DK listesine eklensin.
- M-11 "dört" diye düzeltilsin. E25 için tek karar verilsin: ya "yalnız mudur; yonetici gelen talebi `DocumentRecord`'a
  kaydeder" (§7.4 1425 ile uyumlu) ve dipnot ² düzeltilir, ya da M-11'e E25 istisnası yazılıp kullanıcıya sorulur.
- §7.6-§7.7'de müdür "Kim" sütunundan çıkıp "kâğıtta imzalar" notuna alınsın (KE-19).
- MEM'e bildirim ya kullanıcıya sorulup K2'ye eklensin ve E35'e bölüm olarak girsin, ya da matristen çıksın.

### EK-3 · DOĞRU · yüksek · §7 Evrak sütunu (satır 1370-1543) ↔ §9.5 katalog (satır 1813-1878)

**Sorun.** §7'nin okuma kılavuzu "Evrak: üretilen belgenin adı; kodu, şablonu ve biçimi evrak kataloğundadır (§9)"
diyor (1318). Ama §7'de üretilen belge diye adı geçen şu belgelerin katalogda kodu, fazı, şablonu, imza bloğu ve testi
yok:
- **YK:** Yedek üye çağrı yazısı (1375) · Bankaya imza yetkisi (değişikliği) bildirimi (1372, 1542) · Karar defteri
  dizini (1370, 1543; M12b'de sürüm 2 sayılıyor ama §7 bunu F3-F4 akışında üretiyor).
- **Koçan:** İptal ve kayıp yaprak tutanağı (1451) · Koçan iptal tutanağı (1454).
- **Kantin:** Fesih bildirimi (1487). E47 yalnız md. 22/1-e ihtarıdır.
- **Servis:** Taşımacıyı tespit komisyonu görevlendirme yazısı, servis işlem dosyası kapağı, tip şartname (1515) ·
  Değerlendirme tutanağı (1519; E53 yalnız EK-3 hâlinde) · Komisyon kararının onaya sunulması yazısı (1521) · Komisyon
  kararının tebliği yazısı (1522; U-E md. 8/6 tebliği zorunlu kılar) · Servis yükümlülük bildirimi ve fesih bildirimi
  (1526).
- **Kapanış:** Kasa sayım tutanağı (1542) · Dönem kapanış kontrol listesi (1543).

(Olağanüstü genel kurul çağrı yazısı EK-2'dedir.)

**Doğrulama.** Bu adların her biri belgede yalnız §7'deki satırında geçiyor; §9.5 tablosunda ve §9.7'deki "programın
üretmediği belgeler"de yoklar. §9.5'in "= **62**" sayımı (1878) bunları içermiyor. Söz dağarcığı testi E48-E58
aralığını tarıyor (2268); kodsuz servis yazıları testin dışında kalır.

**Düzeltme.** Her belge için üç yoldan biri: katalog kodu (dayanak, kaynak, biçim, faz, §9.6 satırı) · §9.7'de
"program üretmez" satırı ve nedeni · §7'den silinmesi. Servisin tebliğ ve onaya sunma yazıları E48-E58 aralığına,
yani söz dağarcığı testinin kapsamına alınsın; §9.5 faz dağılımı sayımı güncellensin.

### EK-4 · DOĞRU · orta · §4.4.2 (satır 441-481) ↔ §4.4.5 (satır 539) ↔ §7 (satır 1311-1315, 1372) ↔ §9.6 (satır 1885)

**Sorun.** Kimin neyi yazabileceği dört yerde farklı anlatılıyor ve hangisinin bağlayıcı olduğu yazılı değil.
1. **Döngüsel atıf.** §4.4.2 (444) rol-özel işaretleri §7'ye bırakıyor; §7 (1313-1314) "`yonetici`nin başka rolün
   işini operatör olarak girip giremeyeceği §4 rol matrisindedir" diyor. Matriste böyle bir hüküm yok. TK13'ün uç +
   yöntem matrisi §7'deki "Kim"i mi, §9.6'daki "Üreten"i mi uygulayacak, belirsiz.
2. **§9.6 matristen dar.** "Üreten: belgeyi programda oluşturup düzenleyebilen rol" (1885). `yonetici` matriste
   bütün birlik modüllerinde Y (450-463; §4.4.1 420 "Bütün birlik modülleri"; saha 10'a göre programı çoğunlukla MY
   kullanır). Buna karşın E15, E16, E17, E19, E20, E21, E23, E24, E28, E30, E31, E36, E41, E45, E47'nin Üreten'inde
   yok. `baskan` M4'te Y, E15'te yok.
3. **§7 Kim ↔ §9.6 Üreten.** Dönemlik duyuruyu §7.3 (1407) `yonetici`ye veriyor, E30'un Üreten'i yalnız muhasip
   (1921); §8.6 (1705) "Duyuru web metni | yonetici". Aylık kira-pay ve arz çizelgesi §7.6'da (1494, 1496)
   yonetici/baskan, E24'te muhasip (1915). TÜFE bildirimi §7.6'da (1485) yonetici, E45'te "muhasip, sekreter" (1936).
   İhtar ve fesih §7.6'da (1487) "baskan, yonetici", E47'de sekreter (1938). Ayni bağış §7.3'te (1401) "muhasip,
   yonetici", E21'de muhasip (1912).
4. **Hesap açma ve kapama.** Matriste (465) "hesap açma, kapama, parola sıfırlama" yalnız `yonetici`. §4.4.5 (539)
   üyelik düşünce hesabı "Düşmeyi kaydeden yazar" kapatıyor. §7.2 (1372) "Görev bölümü rol hesaplarını açar, önceki
   görev sahibinin hesabını kapatır" diyor ve Kim sütununda `sekreter` var.
5. **DK'nin kendi kaydı.** DK başkan seçimini (md. 14/1) §7.2'de (1372) sekreter kaydediyor. E02'de (1893) "üyelik
   kaydı yonetici" yazıyor; denetim planı ise bir "ayar" (918). Ayarlar yalnız `yonetici`ye açık (467), M2'de DK O.
   DK kendi görev bölümünü ve planını giremiyor. Bu, dipnot ³ (478) "YK rolleri DK modülüne yazamaz" ile ve K2'deki
   "DK yalnız denetim modülüne yazar" çizgisiyle ters düşüyor.
6. *(KISMEN)* Matris okur rollere evrak çıktısı veriyor (441-442), ama "Kişisel veri içeren dışa aktarım (veli
   listesi, kişi dökümü)" yalnız `yonetici`ye açık (468). Veli adlarını taşıyan E07 ve E08'in (xlsx dâhil) Üreten'inde
   sekreter de var (1898-1899).

**Doğrulama.** Satırlar yukarıda alıntılandı; E-kodlarının Üreten değerleri §9.6 tablosundan (1892-1953) tek tek
okundu.

**Düzeltme.** §4.4.2'ye bağlayıcılık paragrafı yazılsın. Öneri: matris modül düzeyinde bağlayıcıdır, §9.6 Üreten
belge düzeyinde bağlayıcıdır, §7 Kim bilgilendiricidir ve "operatör" sorusunu matris cevaplar. §9.6 Üreten'e
`yonetici` eklensin ya da hangi belgeyi neden üretemediği yazılsın. Hesap açma ve kapama için tek kural seçilsin:
üyelik düşmesi ve görev bölümü hesap işlemi **önerir**, uygulayan `yonetici`dir; ya da matrise istisna yazılsın.
DK görev bölümü ve denetim planı M8'e alınsın (DK yazar). Veli adlı çıktıların (E07, E08) hangi rollere açık olduğu
matriste yazılsın.

### EK-5 · DOĞRU · orta · §6.4 ↔ §5.2.9 ↔ §7 ↔ §10.3 (sert / uyarı türü)

**Sorun.** Aynı hükmün türü bölüme göre değişiyor:
- `genel_kurul.gundem_degisikligi` §6.4.1'de S (1070); §6.4.11'in sert sayımında da var (1271, "GK karar ve gündem
  çoğunluğu"). §7.1'de (1340) "gündem değişikliği oy çokluğuyla [U]".
- `genel_kurul.karar_cogunlugu` ve `genel_kurul.ikinci_toplanti_cogunluk_aranmaz` S (1068-1069); §7.1'de (1339)
  "çoğunluk aranmaz, kararlar katılanların çoğunluğuyla [B]".
- `servis.komisyon_karari` S; değeri "muhalif şerhi zorunlu" (1219), testi `sv::test_muhalif_serhi_zorunlu` (2169).
  §7.7'de (1520) "muhalif oyda şerh boş [U]".
- İmzadan önce yer teslimi: §5.2.9'da (783) "sert", §7.6'da (1484) "[S]". §6.4.8'de `kira.yer_teslimi_gun` U (1199),
  notu "imzasız teslim yok"; §10.3'teki testin adı `kn::test_imzasiz_sozlesmede_teslim_uyari` (2153). Bu sert, §6.4.11
  sert listesinde (1270-1275) de yok.
- DK öğretmen koltuklarının GK oylamasına girmemesi §7.1'de (1340) [S]; testi U kuralı `genel_kurul.secim_bicimi`
  (1075, 2047) altında. *(KISMEN: `denetleme_kurulu.koltuklar` S de konuyu kapsıyor.)*
- `arz_bedeli.takip_sorumlulari` U (1168); §7.6'da (1496) [B].

**Doğrulama.** Alıntılar yukarıda; §6.4 tablolarının tür sütunu betikle sayıldı (146 kural, 43 S, 103 U — §6.4.11 ile
aynı).

**Düzeltme.** Tür tek kaynaktan (§6.4) gelsin; §7 etiketleri ona göre düzeltilsin. Yer teslimi için iki yoldan biri:
ayrı sert kural (ör. `kira.imzadan_once_teslim_yok`, sert gerekçesiyle ve §6.4.11 sayımına girerek) ya da §5.2.9 ve
§7.6'da [U]. Muhalif şerhinin türüne karar verilip kural değeri, test adı ve §7.7 eşitlensin.

### EK-6 · DOĞRU · orta · §2.1 F0-b (satır 81), §6.1 (satır 962-964), §6.4.11 (satır 1270-1275), §15.1 B-13 (satır 2712) ↔ CLAUDE.md altın kural 3

**Sorun.** Sert engelin kapsamı belgenin içinde ve CLAUDE.md'yle farklı tanımlanıyor. CLAUDE.md altın kural 3 ve §2.1
F0-b kapalı bir liste veriyor: hesap bütünlüğü (toplamlar, numara tekilliği, kapanmış dönem, yeter sayı hesabı) +
hukuken geçersiz işlem (kantin isteklisinde suç ya da hısımlık engeli, OLUR'suz kesinleştirme). §6.1 bunu "üç
durum"a genişletiyor: hesap bütünlüğüne "oranlar" ekleniyor, hukuken geçersiz işleme "F1 kapısındaki organ bileşimi
kişi türleri" ekleniyor ve üçüncü gerekçe olarak "değeri hesapta kullanılan parametre" (23 kural) geliyor. §6.4.11
buna bir de "kullanıcı kararı" ekliyor. Öte yandan aynı belge B-13'ü "altın kural 3'ün sert listesi genişlemez"
gerekçesiyle uyarıda bırakıyor (2712; §7.1 1340).

Sonuç olarak iki grup kural CLAUDE.md'nin listesine uymuyor:
- Kullanıcının sert dediği A-2 (`denetleme_kurulu.yk_uyesi_olamaz`) ve KE-15 (müdür YK'ye giremez) CLAUDE.md'de yok.
- Kullanıcıya sorulmadan sert yapılan kayıt engelleri de var: `denetleme_kurulu.koltuklar` (1105),
  `servis.ucret_tarifesi` (1229; uç 400 döner, 2179), `kantin.kiralama_usulu` (1184: "Başka yöntem seçeneği yok"),
  `personel.sgk_saklama_yil` (silme kilidi, 1245).

**Doğrulama.** CLAUDE.md:54-59: "Sert engel yalnız hesap bütünlüğünde (…) ve mevzuatın hukuken geçersiz saydığı
işlemlerde: kantin kiralamasında suç ya da hısımlık engeli olan isteklinin kabulü, mülki amir onayı (OLUR) olmadan
kesinleştirme". Plan §1.8 (plan:231) bu kararın "CLAUDE.md altın kural 3'e yazıldı"ğını söylüyor; A-2 ve KE-15'in
"Olamaz, sert" kararları plan:239-240'ta.

**Düzeltme.** §6.1'deki gerekçe listesi kullanıcıya onaylatılsın; ardından CLAUDE.md altın kural 3 ve §2.1 F0-b aynı
metne getirilsin. Bu metne A-2, KE-15 ve plan §2.4'teki "YK'ye veli olmayan eklenemez" kuralı da girsin. "Hesap
parametresi" yalnız "değer kullanıcıca değiştirilemez" anlamında tanımlansın; kayıt engelleyen parametre kuralları
(servis ücret alanı, kiralama usulü) ayrıca sayılsın. B-13'ün gerekçesi buna göre yeniden yazılsın.

### EK-7 · DOĞRU · orta · §14 (satır 2681-2686) ↔ §6.4.7 ↔ §9.5 ↔ §10.3 ↔ §5.1 (satır 643-645) ↔ plan §2.2, §3

**Sorun.** Üç yerde faz ataması çelişiyor.
1. **Kantin kira-pay.** E24 F3'te (1838). §6.4.7 ve §10.3'te (2117-2132) şu kuralların davranış kapısı F3:
   `arz_bedeli.kira_oran`, `arz_bedeli.donem_ay`, iki vade kuralı, `pay_dagitimi.genel`, `pay_dagitimi.il_merkezi`,
   `kira.odeme_gunleri`, `kira.yariyil_ayi_carpani`, `kira.ay_sayisi`, `kantin.kdv_istisnasi`,
   `arz_bedeli.takip_sorumlulari`. Plan §3 de F3'e "kantin kira-pay hesabı" koyuyor (plan:329). Buna karşın §14'ün F3
   satırında (2684) kantin yok, F5 satırı (2686) ise "aylık kira takvimi, arz bedeli (10'u / 20'si) ve pay dağılımı"
   diyor. F3 kapısında kantin yok. Bu kuralların dayandığı modellerin (`OabContract`, `ContractInstallment`,
   `ShareStatement`) hangi fazda geleceği yazılı değil.
2. **Genel kurul raporları ve devir.** §14 F2 (2683) "raporlar, ibra, bütçe, seçim, sonuç yazısı, görev bölümü,
   devir-teslim" diyor; F2 kapısı GK akışının genel setle eşdeğer üretilmesini istiyor. Oysa E28 tahmini bütçe, E33 DK
   nihai raporu, E34 YK faaliyet raporu ve E37 devir-teslim F4'te (1842, 1847-1848, 1851); §14 F4 (2685) de
   "devir-teslim" diyor. §7.1'de `CAGRILDI → ILAN_EDILDI` geçişinin evrakı (1336) bu belgelere dayanıyor.
3. **F1b.** §14 F1b (2681) kurulum sihirbazını ve veli aktarımını F1b'ye koyuyor. Sihirbazın 4. adımı `BankAccount`,
   `LedgerAccount` ve ilk `OpeningBalance`'ı yazar (643-645). `OpeningBalance.term` (726) `OabTerm`'e bağlı;
   `OabTerm` F1c'de, "devreden bakiye" ise F3'te (2684). `ParentRoster.term` (667) de F1c modeline bağlı.

**Doğrulama.** Satırlar ve plan atıfları yukarıda. Plan §2.2 (plan:266-267) sihirbazın 4. adımını F1b'de sayıyor.

**Düzeltme.** Kantin kira-pay için tek karar: ya §14 F3'e "kantin kira-pay hesabı (E24) ve gereken sözleşme alanları"
eklensin ve F3 kapısına örnek girsin, ya da kuralların ve E24'ün fazı F5'e alınsın. F2'nin belge listesi §9.5 ile
eşitlensin: ya E28, E33, E34, E37 F2'ye alınsın, ya da F2 kapısı bu belgeleri F4'e bıraksın. F1b sihirbazının 4.
adımı ve veli aktarımı için ya model F1b'ye alınsın, ya da adım F1c/F3'e ertelenip plan §2.2'ye "F0 eki" yazılsın.

### EK-8 · DOĞRU · orta · §4.4.4 (satır 509-510), TK16 (satır 109) ↔ §5 (satır 594, 625) ↔ §12.B (satır 2543, 2585); §5.3; §5.4 (satır 871)

**Sorun.** `Hesap` ve `DenetimIzi` modellerinin alanları hiçbir bölümde tanımlı değil; atıflar birbirine gönderiyor:
- §5 (594, 625): "hesap ve denetim izi modelleri … mimaride (§4)", "§4'te tanımlanır".
- §4.4.4 (509-510): "Rol, ad-soyad, organ bağı ve açılış/kapanış tarihi veritabanındadır (`Hesap`, alanları §5)".
- TK16 (109): "Öneri; model §5". §12.B (2543, 2585): "`Hesap`, `DenetimIzi` §5'te", "(alanlar §5)".

KVKK erişim günlüğünün de modeli yok. Bu günlük hassas okumaları tutuyor (§4.4.2 445) ve saklama süresi var (§5.4
871, B-9). §5.3'teki şifreleme tablosunda ne `Hesap` (ad-soyad tutar) ne de `DenetimIzi` (kaydın özetini taşır) var.
Bu yüzden "kişi adı … her alan şifrelidir" ilkesinin bu iki tabloda nasıl uygulanacağı belirsiz. Plan §2.4 "her yazma
denetim izine kim-ne-zaman düşer" testini F1 kapısına koyuyor; yani bu modeller F1b'nin ilk işi.

**Doğrulama.** Satırlar yukarıda; §5.1-§5.2 tablolarında `Hesap` ya da `DenetimIzi` adlı bir satır yok.

**Düzeltme.** §5.1'e üç model eklensin:
- `Hesap`: tanıtıcı, rol, ad-soyad (şifreli), organ üyeliği bağı, açılış, kapanış, son giriş, sıfırlama işareti.
- `DenetimIzi`: zaman, hesap, rol, işlem, model ve kimlik, önceki ve sonraki durum, kayıt özeti, `ComplianceItem`
  bağı, önceki HMAC, HMAC.
- `ErisimGunlugu`: hesap, okunan alan türü, kayıt, zaman.

§5.3'e bu modellerin satırları eklensin; TK16 "Öneri; model §5" ve §2.3.1 (149) "§5 modeli kabul ederse" ifadeleri
güncellensin.

### EK-9 · DOĞRU · orta · §6.4.5 (satır 1133, 1139-1140), §9.5-§9.6 E36 (satır 1850, 1927) ↔ §5, §7

**Sorun.** Sosyal-kültürel etkinlik ve kampanya işi için iki kural ve bir belge var, ama modeli ve akışı yok. Bu işin
dayanakları: Yön. md. 6/2, 15/1-c, 19/4; SEY md. 5/8; ön değerlendirme §2.4 ("etkinlik/kampanya hesabı");
GNL-OAB-FR-020. Eksikler:
- `etkinlik.onay_zinciri` notu "Her aşamanın tarih/sayı alanı" istiyor; hiçbir modelde bu alanlar yok.
- `etkinlik.ders_saatleri_disinda` etkinliğin zamanını ister; böyle bir alan yok.
- `gelir.proje_protokol_ucret_yasak` notu (1133) "Etkinlik gelirinde onay kutusu" diyor; `LedgerEntry`'de bu alan yok.
- E36'nın veri kaynağı "`LedgerEntry` (etkinlik)" ve `DocumentRecord`. FR-020 ise onay zincirini (B), gelir
  kalemlerini (C) ve gider kalemlerini (D) tek bir etkinliğe bağlıyor; bu bağı kuracak kayıt yok.
- §7'de etkinlik akışı yok.

**Doğrulama.** Belgede "etkinlik" ya da "kampanya" geçen satırlar tarandı: model ya da akış satırı yok. FR-020 B'deki
onay zinciri: YK kararı → Sosyal Etkinlikler Kurulu incelemesi → müdürün uygunluk görüşü → il/ilçe MEM onayı.

**Düzeltme.** §5.2.7'ye bir etkinlik modeli eklensin (ör. `SocialEvent`): tür, ad, tarih-saat, sorumlu YK üyesi, YK
kararı, SEK inceleme tarihi ve sayısı, müdür görüşü tarihi ve sayısı, MEM onayı tarihi ve sayısı, "proje/protokol
kapsamında değil" beyanı, durum. `LedgerEntry.event` bağı kurulsun. §7'ye kısa bir akış girsin (TASLAK → ONAYDA →
ONAYLANDI → YAPILDI → KAPANDI); F4 kapısına E36 örneği eklensin.

### EK-10 · KISMEN · orta · §14 F1b-F1c (satır 2681-2682), §10.6 (satır 2279) ↔ plan §2.4 (plan:309, 320)

**Sorun.** Plan §2.4'teki F1 kod kapısının iki maddesi tasarımda karşılıksız:
- (a) "dönemi kapanmış kullanıcı giremez": §14 F1b kapısında yok. Tasarım dönem devrindeki hesap kapanışını F4'e
  koyuyor (§4.4.5 540), dolayısıyla F1'de bu maddeyi sınayacak akış yok.
- (b) "Kılavuzda F1 bölümleri (kurulum, okul kartı, kullanıcılar, organlar)": §14'te hiçbir faz kapısında kılavuz yok.

Ayrıca §10.6 (2279) "aile güvenlik ve rol testleri §4'te" diyor, ama §4'te bu testlerin listesi yok. Orada yalnız
TK13'ün "URL desenlerini dolaşan koruma testi" geçiyor; plan §2.4'ün beş güvenlik maddesi (409, kilitliyken yazma,
güvenlik dosyası, kör indeks, şifreli yedek) adıyla hiçbir yerde sınanmıyor.

**Doğrulama.** Plan:307-320 ile tasarım 2680-2682 ve 2277-2291 karşılaştırıldı. *KISMEN:* F1c'de üyelik düşünce hesap
"aynı işlemde" kapanıyor (§4.4.1 433); maddenin bir kısmı F1'de sınanabilir.

**Düzeltme.** F1b ya da F1c kapısına "kapanmış hesap giremez (üyelik düşmesi ve elle kapanış; dönem devri F4'te)"
yazılsın ve plana F0 eki düşülsün. Kılavuz maddesi F1c kapısına eklensin. §4.4'e F1b güvenlik ve rol testlerinin
adları listelensin ya da §10.6'daki atıf düzeltilsin.

### EK-11 · DOĞRU · orta · §12.A (satır 2485) ↔ §10.4 (satır 2203-2204, 2222, 2241, 2248)

**Sorun.** OYS testlerinin sınıfı iki bölümde farklı.
- `test_ikili_kriter_yalniz_0_veya_max`: §12.A UYARLA'ya geçtiğini söylüyor; §10.4'te (2241) AYNEN.
- `test_mazeretli_devamsizlik_dusurmez` ve `test_araya_bir_katilim_girerse_seri_bozulur`: §12.A "AYNEN kalır"
  diyor; §10.4'te (2222) UYARLA ("sayım toplantılar üzerinden"). Seri bozulması, S-19'un düzelttiği davranışın ta
  kendisi; test AYNEN taşınırsa kayıt üzerinden sayım korunmuş olur.
- `test_gecikme_zammi`: §10.4'te (2248) ALMA. Envanter §6.1'de `test_share.py` için ALMA sayısı 0, yani bu test
  envanterde UYARLA'ydı. §12.A ise ALMA'yı 27'de bırakıyor.
- §12.A "**Üç** test" sınıf değiştiriyor diyor; §10.4'ün sapma listesi (2203-2204) en az yedi test sayıyor: üç
  devamsızlık, belge eksikliği, taksit, puan sınırı ve iki puanlama.

Bu yüzden §12.A'daki "66 · 280 · 27" toplamı yanlış.

**Doğrulama.** Envanter §6.1 (oys-oab-envanteri.md:532, 556, 557, 565): `test_board.py` 5 AYNEN / 1 UYARLA,
`test_scoring.py` 4 / 1, `test_share.py` 3 / 3 / 0 ALMA; toplam 69 / 277 / 27. §10.4'ün kendi toplamı (31 · 38 · 2 = 71) betikle doğrulandı ve tutarlı.

**Düzeltme.** §10.4 esas alınsın; §12.A'daki test satırı her test için bir kez sınıf yazılarak yeniden sayılsın.
Envanterin sınıfından sapan her test §10.4'teki sapma listesine girsin.

### EK-12 · DOĞRU · orta · §9.6 veri kaynağı sütunu ↔ §5

**Sorun.** Bazı belgelerin veri kaynağı, §5'te olmayan alan ya da modellere dayanıyor:
- E04 (1895): "okul kartı (veri sorumlusu alanı, KE-20)". `SchoolConfig`'e eklenen alanlar tablosunda (627-641) böyle
  bir alan yok; KE-20 (2733) de "okul kartındaki alandan dolar" diyor.
- E08 (1899): "gözlemci öğrenciler (ayrı liste)". `GeneralAssembly` yalnız `observer_count` tutuyor (693); T5 gereği
  öğrenci adı da alınmıyor.
- E14 (1905): "ayarlar (YK günü, DK planı)". §6 (918) bu ayarları sayıyor ama §5'te karşılık gelen alan yok.
- E25 (1916) "ExpenseFile (talep, gerekçe, kalemler)" ve E26 (1917) "ExpenseFile (teklifler, komisyon, teslim)".
  `ExpenseFile`'da (749) kalem, gerekçe, teklif (FR-017 B, piyasa araştırması) ve teslim alanı yok.
- Alım komisyonu iki yerde tutuluyor: `ExpenseFile.commission_members` (→ `OabPerson`, 749) ve
  `OrganMembership(organ=ALIM_KOMISYONU)` (666). E26 ikisini birden okuyor; bu, O6 "tek kaynak" ilkesine (607)
  aykırı.
- E46 (1937) ve E58 (1949): "`ComplianceItem` (belge türü, tarih, geçerlilik)". Bu alanlar `BidderDocument`'tadır
  (`document_type`, `seen_on`, `valid_until`; 781); `ComplianceItem`'da (755) yoklar.

**Doğrulama.** §5 tabloları ile §9.6 satırları tek tek karşılaştırıldı.

**Düzeltme.** Eksik alanlar §5'e eklensin: `SchoolConfig` için veri sorumlusu ve YK toplantı günü; DK planı için ya
ayrı bir model ya da `OabTerm` alanı; `ExpenseFile` için kalem, teklif ve teslim alt tabloları. Ya da veri kaynağı
düzeltilsin: E46 ve E58 → `BidderDocument`, E08'in gözlemci bölümü → boş satırlı. Alım komisyonu için tek kaynak
seçilsin.

### EK-13 · DOĞRU · orta · §4.3 (satır 382), §4.4.2 (satır 445) ↔ §5.2.5 (satır 719), §5.3 (satır 818) ↔ §9.6 E01, E27 (satır 1892, 1918)

**Sorun.** Kurumsal IBAN'ın ne kadar hassas olduğu bölümden bölüme değişiyor; ödeme alıcısının IBAN'ı ise modelde
hiç yok.
- §5.2.5 ve §5.3 kurumsal IBAN'ı açık alan sayıyor.
- §4.4.2 "tam IBAN" okumasını erişim günlüğüne düşen hassas okuma sayıyor.
- §4.3 IBAN'ı kişisel veri olarak korunan varlıklar arasına koyuyor.
- E01 aynı IBAN'ı maskeli, E27 tam basıyor.

Modeldeki tek IBAN `BankAccount.iban`. Banka ödeme talimatı (E27, md. 18/2) için gereken alıcı hesabının IBAN'ı
`ExpenseFile`'da (749) yok; banka dökümünde de karşı tarafın IBAN'ı okunmuyor (1601).

**Doğrulama.** Belgedeki bütün IBAN geçişleri tarandı (382, 407, 445, 719, 818, 1394, 1601-1602, 1892, 1918).

**Düzeltme.** Kurumsal IBAN için tek karar verilsin. Öneri: açık, maskesiz, günlüksüz; §4.3 ve §4.4.2 buna göre
düzeltilsin. Ters karar verilirse §5.3'e işlensin. Alıcı IBAN'ı gerekiyorsa `ExpenseFile.payee_iban` eklensin
(şifreli, mod-97 denetimli, hassas okuma); gerekmiyorsa E27'nin kabulüne "alıcı IBAN'ı kâğıtta elle yazılır" notu
girsin.

### EK-14 · DOĞRU · orta · ön değerlendirme §5.1-§5.2, §2.5; RH-001 Bölüm 6 ↔ tasarım

**Sorun.** Kaynak belgelerdeki bazı gereksinimlerin tasarımda karşılığı yok; "bilerek bırakıldı" diye de yazılmamış.
- **M13 ve §2.5:** "kiracıya Ba bildirimine yetecek tahsilat belgesi". Katalogda yok; belgede "Ba" hiç geçmiyor.
- **M10 ve §5.2:** "yazı ve ekleri ayrı dosya (EBYS)". Evrak hattında (TK17, §9.1) yok.
- **§5.2, Para:** "tutarın yazıyla okunuşu (evrak motorlarındaki `yazi_ile()`)". Yok. E27 ödeme talimatı ve E42
  sözleşme gibi belgelerde gerekir.
- *(KISMEN)* **M9:** "açılış ekranında 'bu hafta yapılacaklar'". Yalnız §12.A'da (2475) "vade taramaları pano
  'yaklaşan işler'e" notu var; panonun neyi göstereceği tanımlı değil.
- *(KISMEN)* **RH-001, FR-005 C, FR-001 B-16:** genel kuruldan hemen sonra TEFBİS'e yeni yönetimin, banka hesap
  bilgilerinin ve tahmini bütçenin girilmesi (DR 5.2/10). E18 yalnız `LedgerEntry`'leri listeliyor;
  `ComplianceItem` yükümlülüklerinde (755) bu iş yok. Tasarımda yalnız E13'ün kabul örneğinde (1904) bir kontrol
  satırı var.

Tevkifat hesabı bulgu değildir: tasarım onu §3.3'te bilinçli olarak bilgi metnine indirmiş.

**Doğrulama.** Kaynaklar: on-degerlendirme.md:227 (Ba, tevkifat), 357 (EBYS), 361 (M13), 356 (M9), 373 (yazıyla
tutar); RH-001 satır 105; FR-005 satır 26. Bu terimler tasarımda arandı; karşılık bulunamadı.

**Düzeltme.** Her madde için karar yazılsın: katalog kodu, §9.1 ilkesi ya da §15'e "sürüm 2" veya "alınmaz" satırı.
TEFBİS'e bütçe ve banka bilgisi girişi için `ComplianceItem`'a `TEFBIS_BUTCE_GIRISI` ve `TEFBIS_BANKA_BILGISI`
yükümlülükleri eklensin ya da E18'e ayrı bir bölüm konsun.

### EK-15 · DOĞRU · orta · §5.3 (satır 842-844), §8.5 (satır 1695), §11.3 (satır 2352-2353), §12.B (satır 2542) → §4, §9

**Sorun.** Beş karar başka bir bölüme havale edilmiş, ama o bölümde yazılı değil:
- Dosya anahtarının HKDF bilgi dizgesi "§4 kimlik sabitlerinde" deniyor (843); §2.3.1'in kripto satırlarında
  (145-151) yok.
- "geçici kopyanın temizlenmesi §4'tedir" (844); §4'te yok.
- "PDF/A çıktısı (WeasyPrint) §9'da değerlendirilir" (1695); §9'da yok.
- "Word çıktısında yazı tipi … Pardus'taki karşılığı §9'da" (2352-2353); §9'da yok. Bu, iskelet envanterindeki §11-5
  açık sorusudur.
- "birlik antedi kararı §9" (2542); §9'da yok. Bu da iskelet envanterindeki §11-6 açık sorusudur. E01-E03 F1c'de
  basılacağından birlik antedi F1c'nin ön koşulu.

**Doğrulama.** §9'da (1709-1968) "antet", "yazı tipi" (yalnız 1730'da RYUE için anılıyor), "Pardus" ve "PDF/A"
arandı; karar yok. §4'te "geçici" ve dosya anahtarı arandı; sonuç yok.

**Düzeltme.**
- §2.3.1'e dosya anahtarının HKDF dizgesi için bir satır eklensin (ör. `od-dosya-anahtari`).
- §4.5'e ya da §5.3'e geçici dosya temizliği yazılsın (çıkışta ve açılışta tarama).
- §9.1'e üç karar girsin: yazı tipi (Windows/Pardus eşlemesi, gömülüp gömülmeyeceği), PDF/A ve antet (okul antedi
  altına "Okul-Aile Birliği" satırı mı, ayrı birlik antedi mi).

### EK-16 · KISMEN · düşük · §12.A ↔ OYS envanteri S-27; plan §2.3 ekranları

**Sorun.** S-27 (OYS ön yüzü `modules/okul-aile-birligi/` envanterlenmedi) tasarımda hiçbir karara bağlanmamış.
§12.A ön yüzden söz etmiyor; §12.B'nin YENİ tablosunda (2580-2586) ön yüz modülü olarak yalnız `kullanicilar` var.
Plan §2.3'ün F1c ekranlarının (Birlik Dönemi, Organlar, Temsilciler) kaynağı yazılı değil: OYS'den mi uyarlanacak,
yeni mi yazılacak?

**Doğrulama.** Tasarımda S-27'ye hiç atıf yok; S-10, S-12, S-13, S-15 ve S-29 da kimlikle anılmıyor, ama içerikleri
§4.4, §7.1-§7.2, §5.2.5 ve §14'te karşılanıyor. *KISMEN:* ekran tasarımı genel tasarımın kapsamı dışında
sayılabilir.

**Düzeltme.** §12.A'ya OYS ön yüzü için bir satır eklensin ("ALMA — ekranlar aile kitiyle yeni" ya da "UYARLA") ve
S-27'ye atıf yapılsın. F1c ön yüz modülleri §12.B'nin YENİ tablosuna yazılsın.

### EK-17 · DOĞRU · düşük · §7.1 (satır 1340) ↔ §9.5 E13 (satır 1827); §9.1-4 (satır 1727) ↔ §9.2 (satır 1746, 1750)

**Sorun.**
- (a) §7.1 "Genel kurul sonuç bildirimi (dayanağı korpusta bulunamadı — saha belgesi, DOĞRULANMADI)" diyor. §9.5'te
  aynı belgeye (E13) dayanak olarak md. 10/1-ç, 13/4 ve 27/1 yazılmış.
- (b) §9.1-4 E40'ı RYUE biçiminde resmî yazı sayıyor. §9.2 ise ona KD konum cümlesini ("Bu metin yönetim kurulu karar
  taslağıdır…") veriyor; KD taşıyan belgelerin başlığına da "TASLAK — karar defterine geçirilecek metin" basılıyor
  (1750). Sonuç: il/ilçe MEM'e gidecek bildirim yazısı "taslak" ve "karar taslağı" ibaresiyle basılır.

**Doğrulama.** Alıntılar yukarıda. E40'ın tanımı (1854): "Kantinin kiralanacağına dair bildirim (okul müdürlüğü
vasıtasıyla il/ilçe MEM'e)".

**Düzeltme.**
- E13'ün dayanak durumu tek yerde yazılsın: ya "DOĞRULANMADI, okul uygulaması" ya madde atfı.
- E40 ikiye ayrılsın: KD taşıyan YK kararı taslağı ve konum cümlesi taşımayan RYUE bildirim yazısı. Ya da E40 KD
  listesinden çıkarılsın.
- Aynı ayrım E41 (işletmeciye gidecek cevap yazısı) için de değerlendirilsin.

### EK-18 · DOĞRU · düşük · sayım ve adlandırma

**Sorun ve doğrulama.**
- §10.6 (2283) "`r1`'deki 49 kural" diyor. §6.4.11 (1253), §14 (2674) ve plan §1.7 50 diyor; §6.4 tabloları betikle
  sayıldığında da F1c girişi 50.
- `pre-kapanis-` yedek öneki §5.4 (893) ve §7.8'de (1543) kullanılıyor, ama §2.3.2'nin yedek önekleri listesinde
  (186-189) ve §12.B'nin `backup.py` satırında (2523) yok.
- Aynı kullanıcı kararı farklı kimlikle anılıyor: §2.1'de "F0-e" (84); §5.1 (641), §5.2.5 (727) ve §6'da (919-920)
  "F0-5 c", "F0-5 d".
- Kütüphane'nin evrak kodları OAB kodlarıyla karışıyor: E04'ün kaynağı "Kütüphane Defteri E13 kalıbı" (1818); §12.B'de
  "`gorev_devri_notu.html` (E18)" (2572, 2589); §4.4.5'te "Kütüphane E18 kalıbı" (542). Oysa OAB'de E13 genel kurul
  sonuç bildirimi, E18 TEFBİS listesidir.
- `denetleme_kurulu.yk_uyesi_olamaz` kuralının yürürlüğü 31.10.2026 yazılmış (1110). §6.1 (955) yürürlüğü "dayanak
  fıkranın bugünkü lafzının yürürlüğe girdiği tarih" diye tanımlıyor; kullanıcı kararının tarihi bu tanıma uymuyor.

**Düzeltme.**
- 2283'teki 49 → 50.
- `pre-kapanis-` §2.3.2'ye ve §12.B'nin `backup.py` satırına eklensin.
- Kararın kimliği tek olsun: "F0-e (c)", "F0-e (d)".
- Kütüphane'nin kodları ayırt edici biçimde yazılsın (ör. "KD-E13", "KD-E18").
- Şemaya kullanıcı kararına dayanan kurallar için bir alan eklensin (ör. `dayanak_turu: kullanici_karari`) ve
  yürürlük alanının bu kurallarda ne taşıdığı tanımlansın.

---

Çürütülen aday: 19

*Kısa liste:*
- GNL setinin 23 formu ve RH-001'in katalogda karşılıksız kalması: hepsi en az bir koda bağlı.
- OYS'nin 19 şablonu: hepsi bir koda girmiş.
- S-10, S-12, S-13, S-15, S-29: kimlikle anılmıyorlar ama içerikleri karşılanmış.
- Kural paketi sayımı (146 / 43 / 103 / F1c 50 ve tablo başına sayılar).
- Sertlerin dağılımı (13 / 23 / 6 / 1).
- §9.5'in faz dağılımı (62).
- §12.A'nın model sayımı (29 = 5 / 23 / 1).
- §15'teki 52 karar ve kimlikler (tanımsız atıf yok).
- §10.4'ün iç sayımı (71 = 31 / 38 / 2).
- §6.4 ↔ §10.3 kural kimliği eşlemesi (her kuralın testi var, öksüz kimlik yok).
- İskelet envanterindeki TB ve §10.1 kusurlarının §13'e eşlenmesi.
- Durum adları (§5 ↔ §7).
- E20'de maskeli T.C. kimlik no ile "dışa aktarıma girmez" kuralı arasında çelişki.
- RH-001 takviminin genel kapsaması (yalnız TEFBİS satırı EK-14'e girdi).
- Plan §2.3'ün F1c kural listesinin `r1`'de olması.
- CLAUDE.md'nin K2, K3, K6 satırlarının bayat olması (diskteki CLAUDE.md güncel).
- TK14'ün mutlak oturum süresini kaldırması (§15 M-3'te sapma olarak yazılı).
- Dönem devrinde hesap kapanışının zamanlaması (§4.4.1 ↔ §7.8).
- Kantin denetim komisyonunun kural paketinde olmaması (DOĞRULANMADI-14'te gerekçeli).

---

<a id="işleniş"></a>

## İşleniş

*31.10.2026.* Bulgular genel tasarıma üç düzeltici grup — G1 mimari ve güvenlik (§2.2-§2.3, §4, §11, §12.B, §13), G2
alan (§3, §5, §7, §8, §12.A), G3 kural paketi, evrak ve testler (§6, §9, §10) — ve ana oturum (§1-§2.1, §14-§17)
tarafından işlendi. Gruplar birbirinin bölümündeki payı aktarım notuyla bıraktı; ana oturum notları birleştirmede
uyguladı, çelişenleri uzlaştırdı ve belgeyi **taslak v2** olarak tek dosyada topladı. Beş bulgu kullanıcı kararı
gerektirdi: D1 (MA-2), D2 (SU-1), D3 (GA-4), D4 (MB-5), D5 (KM-13) —
[genel tasarım §15.1b](../tasarim/2026-10-31-genel-tasarim.md#151b-denetim-sonrası-kullanıcı-kararları-31102026).

Durum: **işlendi 125** · **kısmen 4** · **reddedildi 0** · **ertelendi 0** · toplam 129.
"İşlendi", önerinin amacının karşılandığını söyler; düzenek önerilenden farklıysa notta gerekçesi vardır. "Kısmen",
bulgunun bir parçasının bilinçli olarak farklı çözüldüğünü ya da dış bir işe (korpus çapası, kullanıcı sorusu)
bağlandığını gösterir. Bulguların içindeki tekil önerilerden gerekçeyle alınmayanlar notlarda yazılıdır. "Nerede"
sütunundaki § atıfları genel tasarım taslak v2'ye aittir; notlardaki "aktarımda" ibaresi o payın başka grubun
bölümünde birleştirmede işlendiğini gösterir; köşeli parantez işleyeni verir.

| Bulgu | Önem | Durum | Nerede | Not |
|---|---|---|---|---|
| GA-1 | yüksek | işlendi | TK8, TK22 (§2.2); §2.3.1 MAGIC `ODBAK\x03`; §4.4.7 yedek türleri ve kap; §4.3 tehdit 18; §4.5 taşıma; §12.B `backup.py`, `backup_crypto.py`, `encrypted_backup.py`, `restore.py`; §13 D49 | R10'un amacı karşılandı, düzeneği farklı: **dışarı çıkan yedek** (indirme, USB, taşıma) veritabanı + dosya deposunun tamamı; **yerel yedekler** veritabanı + manifesto. Gerekçe: yerel yedek aynı diskte, disk arızasında depoyla birlikte gider; dosyalar değişmediği için veritabanı yedeği depoyla tutarlı kalır; her günlük yedeğe dosya koymak büyüyen depoyu 14 kez çoğaltırdı. Taşımadan sonra "ekli kayıt açılıyor" denetimi §4.5'te; F1b kapı testi aktarımda [G1] |
| GA-2 | yüksek | işlendi | §4.4.4 "Dosya anahtarı"; §4.4.7 açık kopya kuralı; §2.3.1 `od-dosya-sarmal/v1`, `ODDOSYA\x01`; TK8 (aileden ayrılış 1), TK12 sayımı; §12.B YENİ `shared/dosya_sifreleme.py` | Düzeltme önerisindeki "HKDF(DEK) dosya anahtarı + yenilemede dosyaları yeniden yaz" yerine UY-3'ün (a) yolu seçildi: dosya başına rastgele anahtar, DEK'ten türeyen anahtarla sarılı (`Attachment.key_wrap`). DEK yenilemesi dosyaları yeniden yazmaz, sarmalları tek SQLite işleminde yeniler → yarıda kalan dosya yazımı ve iki küme dosya hâli doğmaz. R10'dan sapma aktarımda gerekçeli [G1] |
| GA-3 | yüksek | işlendi | §4.4.4 "Geri yükleme yetkisi"; §4.3 tehdit 21; §4.2 çıkış kodu 9; §12.B `restore.py`, `restore_backup`, `backup_restore.py` | Konsol geri yüklemesi yalnız kurtarma anahtarıyla ya da `yonetici` parolasıyla; rol güncel veritabanından salt okunur `sqlite3` ile (ORM yok, aile kuralı korunur), okunamazsa yedeğin görüntüsünden. `geri-yukleme-notu.json` → ilk kilit açılışında `GERI_YUKLEME` satırı + DK kartı. Önerideki "`db-onceki-*` DK incelemesi bitmeden silinmez" kabul edilmedi: KVKK 14 gün sınırını süresiz kılardı; yerine kenara alınan VT'nin sha256'sı ve zincir başı iz satırına yazılır, dosya 14 gün durur [G1] |
| GA-4 | yüksek | işlendi | TK9, TK12; §4.3 tehdit 10; §4.4.4 DEK yenileme 6-7; §4.4.6-2; §12.B `kurtarma_anahtari.html` | Birleştirmede (U4): zarf imha tutanağı katalog dışı program belgesidir (§9.7). D3 uygulandı: anahtar okul müdürlüğünde mühürlü zarfta; devir tutanağına yalnız "zarf müdürlükte, mührü sağlam; no, tarih". Eski zarf, yeni anahtarla tam yedek açılıp doğrulandıktan sonra imha tutanağıyla yok edilir. Denetimin "E14" atfı yanlış (E14 yıllık iş takvimidir); kurtarma anahtarı belgesi katalog dışı program belgesidir [G1] |
| GA-5 | yüksek | işlendi | §4.4.7 "Rotasyon ve KVKK sınırı"; §2.3.2 önek kümesi; §12.B `backup.py`; §13 D49, D23 | Bütün yerel önekler + `db-onceki-` 14 gün; KVKK tetiğinden eski `pre-migrate` adıyla silinir; `wal_checkpoint(TRUNCATE)`; dışarı alınmış yedek kartı; F4 testi. "En çok 14 gün" yalnız yerel yedek için ve program açıkken koşar diye dürüstçe yazıldı. §5.4 metni aktarımda [G1] |
| GA-6 | yüksek | işlendi | §4.4.2 matris (kişisel veri çıktısı satırı, dipnot ¹⁰, "okuma" istisnası); §4.6.4 `VELI_LISTESI_CIKTISI`; §4.4.7 (E07/E08 depoya yazılmaz) | R9: adlı E07/E08 yalnız `yonetici`; dosya saklanmaz, arşive girmez; her basım erişim günlüğüne. Önerideki "sekreter de basar" R9 gereği alınmadı. §5.4, §8.5, §9.6 payı G2/G3'te (R9) [G1] |
| GA-7 | yüksek | işlendi | §4.6.1-§4.6.5 (yeni); TK16 "model §4.6"; §2.3.1 İA dizgeleri; §12.B `models.py` ve YENİ | R1. Özet = kayıt kimliği + alan adları + izinli kişisiz alan değerleri + içerik MAC'i; kopya yok. `Account.display_name` şifreli. `AccessLog` zincir dışı, 2 yıl. §5.1, §5.3 atıfları aktarımda [G1] |
| GA-8 | orta | işlendi | §4.6.3 "Kilitliyken yazım"; §4.1 değişmez; TK16, TK19; §4.2 adım 7-8 | R11: İA DEK'ten bağımsız; kilitliyken kapalı kümedeki kişisiz sistem olayları ileriye dönük güvenli kilitli kip anahtarıyla (İA'dan çapa anında türeyen tohum, `iz-durumu.json`) mühürlenir; veri değiştiren sistem işi ilk kilit açılışına ertelenir; göçler yalnız şema. Önerideki ayrı `SistemOlayi` tablosu gerekmedi: tek tablo, tek zincir, satırlar ekleme-yalnız kalır [G1] |
| GA-9 | orta | işlendi | §4.6.3 çapa, kendiliğinden doğrulama, kâğıt çapası; §4.6.2 içerik MAC'i; TK8 katı kip; §12.B `crypto.py` UYARLA; §13 D48; §4.3 tehdit 7 | (a) çapa her kilitlenmede, aylık kâğıda iner; (b) `from_db_value` katı kip; (c) `record_mac` kanonik düz değerler üzerinden, token taşımasını yakalar; kilit açılışında son 200 satır. Çapa önerideki gibi `guvenlik.json`'a değil ayrı `iz-durumu.json`'a yazılır: `guvenlik.json`'un her yazımı arşiv kopyası doğurur. Kâğıt çapası basımı §9'da (aktarım) [G1] |
| GA-10 | orta | işlendi | §4.6.1 `seal`; §4.3 tehdit 19; §4.4.3 kilit açılış sırası; §2.3.1 `od-hesap-muhru/v1` | Mühür tutmazsa oturum açılmaz, satıra dokunulmaz (yeniden mühürlemek değiştirilmiş rolü meşrulaştırırdı), iz + kart. Kalan risk dürüstçe yazıldı [G1] |
| GA-11 | orta | işlendi | §4.6.1 "İki depo kuralı"; TK11; §4.4.5 "Geri yükleme" satırı | Dört hâl: giriş, açma sırası, kapama sırası (önce VT), geri yükleme karşılaştırması; F1b testleri [G1] |
| GA-12 | orta | işlendi | §4.4.4 DEK yenileme 1-7 ve "Yarıda kalma"; TK12; §4.4.5 hesap geçişi ve MY değişti satırları; §4.3 tehdit 5 | (a) yeni DEK veritabanından önce `gecis`'e; açılışta parmak izi karşılaştırması (DEK istemez); (b) yenileme görev bölümü ile yeni hesapların açılışı arasında (hesap geçişi), yeni hesaplar tek geçici parolayla; (c) gerekçe "yenilemeden sonraki" diye daraltıldı, pencere kalan risk; (d) MY değişiminde DEK yenilenir. Kesme provası F4 kapısına (aktarım §14) [G1] |
| GA-13 | orta | işlendi | §4.2 "Uçuştaki iş"; TK5; §4.5 Çarpı ve Kanıt; §12.B `window.py`, `clean_shutdown.py`, `shared/bakim.py` | Bir kez erteleme, en çok 60 sn, soru değil bekletme (T6 korunur); işaret yalnız sayaç sıfırken; iki test [G1] |
| GA-14 | orta | işlendi | TK7; §4.3 tehdit 20; §4.5 M-8 maddesi; §2.3.1 `OD_UPDATE_REPOSITORY` notu; §12.B `updates.py`; §13 D51, D16 | Ortak "OAB" Windows hesabında yönetici kurulumu; kullanıcı başına kurulum yalnız tek kullanıcılı senaryo. `OD_UPDATE_REPOSITORY` paketli yapıda okunmaz; kurucu çalıştırılmadan önce SHA-256 yeniden doğrulanır. M-1 varsayılanının metni §15'te (aktarım) [G1] |
| GA-15 | orta | işlendi | TK9 (md. 9/2-e), TK15 (md. 7/2, 7/3); §4.3 tehdit 11; §4.5 M-8 sapması ve kılavuz maddesi; §4.4.4 `hatali`/`askida` | Organ ve müdür hesabında 10 ardışık hatada askı, `yonetici` açar; `yonetici` hesabında askı yok (gerekçeli); gecikme hesap başına. Yeni açık karar **M-12** (aktarım) [G1] |
| GA-16 | orta | işlendi | §4.3 tehdit 9 kalan risk; TK15; §4.4.6-5 | 12 karakter parola cümlesi önerisi + güç göstergesi. Argon2id profili gerekçesiyle aynı bırakıldı (hesap sayısı deneme maliyetini değiştirmez; 4 GB makinede giriş süresi); TK11'in yüzeyi daraltması anıldı [G1] |
| GA-17 | orta | işlendi | §4.4.3 "Kurtarma anahtarıyla açılış"; §4.3 tehdit 10, 12; §4.4.5; §4.6.2 `KURTARMA` türü | Yalnız `yonetici` hesabının parolası yenilenir ya da yeni `yonetici` açılır; ayrı iz türü; sahibine ilk girişte bildirim [G1] |
| GA-18 | orta | işlendi | §4.4.2 "Uygulama — iki katman" ve testler; TK13; §12.B `kip_izinleri.py` satırı | Uç katmanı (parametre denetçileri aileden) + servis katmanı tek kapı; hücre başına anlık görüntü testi ve dipnot başına servis testi [G1] |
| GA-19 | orta | işlendi | §12.B AYNEN → UYARLA (`lock_middleware.py`, `recovery_key_document.py`, `kurtarma_anahtari.html`) ve metin kuralları; §2.3.3 elle tarama listesi; §13 D50 | Yeni kilit iletisi ve kurtarma belgesi içeriği yazıldı; "parola iki kişide bulunsun" öğüdü çıkar [G1] |
| GA-20 | orta | işlendi | §4.5 Linux satırı; §4.2 adım 1; §4.3 tehdit 22; §2.3.1 veri dizini notu; §12.B `paths.py`, `main.py`; §13 D52 | `umask 077`, 0700/0600, `postinst` dokunmaz, test, kılavuz notu. Pardus varsayılan izni doğrulanmadı (F1a'da elle) [G1] |
| GA-21 | düşük | işlendi | §4.1 değişmez "Yapılacak"; §12.B `settings.py`; §13 D46 | — [G1] |
| GA-22 | düşük | işlendi | §4.1 değişmez; TK4; §4.3 tehdit 16; §11 B6; §12.B `shared/pdf.py` UYARLA, `evrak.py`; §13 D47 | Yönlendirme hedefi için izinli alan kümesi yazılmadı: güven çapası SHA-256'dır, kurucu çalıştırılmadan önce yeniden doğrulanır (önerinin "gerekirse" kısmı) [G1] |
| GA-23 | düşük | işlendi | §4.4.3 "Ön yüz belleği"; TK14; §4.3 tehdit 3; §12.B `lib/kilit.ts`; §13 D53 | — [G1] |
| GA-24 | düşük | işlendi | §11.1 B20; §11.4 "Giren (aday)" | Numara B20 (B16-B19 §11.2'de dolu; önerideki "B16" çakışırdı). Geçişliler ve lisansları F4'te; B-10 atfı §15'te (aktarım) [G1] |
| KM-1 | yüksek | işlendi | §3.4, §5.2.8, §5.4, §7.1, §8.4, §8.5 | R9: E07 sınıf teslim çizelgesi ve adlı E08 `GeneratedDocument.personal_list`; yalnız `yonetici` basar, dosya hiç saklanmaz (tür, tarih, satır sayısı, sha256 izi), yeniden basılmaz, arşiv paketine girmez (`01-evrak/kisi-listesi-izleri.txt`). §6.2-6 istisnası ve F2/F4 testi aktarımda [G2] |
| KM-2 | yüksek | işlendi | §4.6.2 "Kaydın özeti" kuralı, içerik MAC'i ve "MAC dışı alanlar", F1b testi; §4.6.4; §4.6.5 | Ek: KVKK gereği silinen alanlar (telefon, T.C. kimlik no, istekli iletişimi, veli listesi) içerik MAC'ine de girmez — yoksa anahtara erişen düşük olasılık uzaylı değeri deneyerek geri bulurdu. §5.3, §8.5 payı aktarımda [G1] |
| KM-3 | yüksek | işlendi | §3.4, §5.2.2, §5.2.9, §5.3, §5.4, §7.6 | `crime_bar` + `kinship_bar` → tek açık `participation_bar` (YOK/VAR, sert engel buna bağlı); hangi bentten geldiği şifreli `participation_bar_basis` (`OZEL_NITELIKLI`, erişim günlüklü, arşive girmez, süreç kapanınca boşaltılır). `disqualified_reason` kapalı liste + şifreli not ("adli sicil içeriği yazılmaz" uyarısı). `NITELIK_KAYBI` → `DIGER`. §3.4'e md. 6/1, 6/3, 6/4 değerlendirmesi; şart DOĞRULANMADI → §15 B-16; Kurul kararı BENIOKU §6'ya (aktarım) [G2] |
| KM-4 | yüksek | işlendi | §4.4.2 matris satırı ve dipnot ¹⁰ (BSG md. 5/8 atfı); §4.6.4 | Birleştirmede: §3.4 "e-Okul kaynaklı veri" paragrafı yazıldı; M-13 §15.4'e girdi. R9 sınırları matrise girdi. §3.4 "e-Okul kaynaklı veri" alt başlığı, cetvelin dolaşım düzeni (§7.1, §9.6) ve yeni açık karar **M-13** (T5 adlı cetvel ve BSG md. 5/8) aktarımda [G1] |
| KM-5 | yüksek | işlendi | §5.4, §7.8, §8.5 | Süreli kişisel veri alanları tek sabitte (`SURELI_KISISEL_ALANLAR`); kapanış silmeleri ve arşiv dışlama listesi oradan üretilir, testle kilitlenir. §7.8'de sıra tersine döndü: önce silmeler, sonra arşiv paketi (kapanmış dönemden, yeniden üretilebilir). Arşiv şeması kuralı "süreli kişisel veri alanı pakete girmez — boşaltılmamış olsa da". Telefon alanı zaten kaldırıldı (KM-7). F4 testi aktarımda [G2] |
| KM-6 | orta | işlendi | §3.4, §5.1, §7.1, §7.3, §7.6, §7.7, §8.4 | §3.4 cümlesi düzeltildi (md. 10/1: elde edilme anı; kılavuz yalnız kullanıcıyı bilgilendirir). E04 dört alt metin; `SchoolConfig.data_controller_text` (boşken E04 basılmaz). Ulaştırma noktaları: E07, E48, E50, E46, E58, E21, aktarım ekranı, hesap teslim pusulası. Bankadan gelen bağışçı için kanal yok → okul sitesindeki genel metin, yeterliliği DOĞRULANMADI. §9'daki metin işleri aktarımda [G2] |
| KM-7 | orta | işlendi | §3.4, §5.2.2, §5.3 | §3.4'e işleme envanteri tablosu (kategori · kişi · amaç · hukuki sebep · saklama · aktarım); hukuki sebep sütunu "öneri" (veri sorumlusuna bağlı). `OabPerson.phone` **kaldırıldı** (programda amacı yok: SMS/e-posta yok, hiçbir evrakta yok). Kantin çalışanı ve kiracı belgelerinde md. 6/3 bendi DOĞRULANMADI (işveren kiracı) → B-16. B-7 güncellemesi aktarımda [G2] |
| KM-8 | orta | işlendi | §6 giriş tablosu (okul uygulaması satırları); §6.4.2 `yonetim_kurulu.tek_birlik`, `uyelik.suc_engeli` (v1 `uyelik.suc_engeli_beyani`); §6.4.6 `harcama.alim_komisyonu_uyeleri`; §6.4.8 `kantin.istekli_suc_engeli`; §9.6 E01; §10.3; KE-22 | Birleştirmede: hüküm alanı `OrganMembership.eligibility_bar` (açık var/yok) + şifreli dayanak; düşme türü `DIGER` (KVKK md. 6/1). Hüküm ile yöntem ayrıldı: kurallar yalnız hükmü (görev alamaz, sonradan anlaşılırsa sona erer; tek birlik) taşır, beyan "okul uygulaması" olarak paketin dışında, "tamamlanacaklar" hatırlatması (mevzuat uyarısı değil, gerekçe istemez). Öneriden farkı: beyan pakete `kaynak: okul_uygulamasi` kaydı olarak girmedi; paket yalnız mevzuat atfı taşısın, atıf kilidine istisna türü açılmasın diye §6 girişindeki "okul ayarı / uygulaması" tablosuna kondu. E01 sütunu "Beyan (okul uygulaması)" [G3] |
| KM-9 | orta | işlendi | §3.4 | "Otomatik olmayan işleme istisnasını kaldırır" cümlesi yerine KVKK md. 2 ve 3/1-e (kâğıt kayıt zaten kapsamda) ve md. 16/2 VERBİS sonucu yazıldı; Kurul istisna kararları korpusta yok (DOĞRULANMADI) → BENIOKU §6 "bekliyor" (aktarım); VERBİS sorusu kılavuzdaki açık sorulara [G2] |
| KM-10 | orta | işlendi | §2.3.2 `pre-kapanis-`, `pre-anonim-` F4; §4.4.7 rotasyon ve F4 testi; §12.B `backup.py` | §5.4'teki "saklama fazına kadar kullanılmaz" ifadesi, §14 F4 kalemi ve süreli silmelerin fazı aktarımda [G1] |
| KM-11 | orta | işlendi | §2.3.1 `od-hareket-parmak-izi/v1`; TK12 sayımı; §4.4.4 DEK; §4.3 tehdit 9 kalan risk | `fingerprint` anahtarlı HMAC. `row_no` kaldırma ve §5.3 ilke cümlesi G2'de (aktarım) [G1] |
| KM-12 | orta | işlendi | §5.1, §5.4, §8.4 | İki satır: bağsız `OabPerson` dönem kapanışında silinir; ayrılan ve bağsız `Personnel` ayrılışı izleyen dönem kapanışında silinir (Kütüphane'nin saklama servisi alınmadığı için kural burada). F4 silme testi aktarımda [G2] |
| KM-13 | düşük | işlendi | §9.1-5; §9.6 E56; §6.4.9 `servis.tasimaci_ilani`; §10.5 `ev::test_e56_yalniz_unvan_plaka_guzergah` | Kullanıcı kararı D5 uygulandı: istisna §9.1-5'te açık; ad/unvan, plaka, güzergâh; telefon, adres, T.C. kimlik no yok; ilan süresi bitince kaldırma hatırlatması. Önerideki "iş telefonu" D5 gereği basılmaz. §15 satırı D5 olarak §15.1b'de zaten var [G3] |
| KM-14 | düşük | işlendi | §5.3, §8.3 | Tek kural: T.C. kimlik no **hiçbir dosyaya girmez**; E20'de yalnız "kimlik no kayıtlı: evet/hayır", E18'de "kimlik no kaynağı" sütunu. Maskeli gösterim yalnız ekranda. §9.1-5 ve E20 kabulü aktarımda; B-8 metni zaten uyumlu [G2] |
| KM-15 | düşük | işlendi | §3.4, §5.1, §5.4 | §3.4 cümlesi denetimin önerdiği biçimde (asıl kâğıtta; varsayılan yalnız görüldü ve geçerlilik; tarama şifreli; süre öneri, okul ayarı `scan_retention_years`, kural paketine girmez). İstekli iletişimi için tek süre: seçilmeyenin iletişimi süreç sözleşmeyle ya da iptalle kapandıktan sonraki ilk dönem kapanışında, sözleşme tarafınınki sözleşme bitiminden sonraki ilk dönem kapanışında boşaltılır. Denetimin "kesinleşme + itiraz süresi" önerisi alınmadı: itiraz süresi korpusta yok, sayı uydurulmaz; dönem kapanışı mekanizması yeter. B-5 eşitlemesi aktarımda [G2] |
| KM-16 | düşük | işlendi | §3.5, §5.1, §5.2.2 | Birleştirmede (U2): §6.4.4 ve KE-24 kampüsün kapsamda olmasına göre düzeltildi. `YAYGIN` kaldırıldı (v1 kapsamı dışı; gerekçe md. 4/1-e); `KARMA` yerine çok değerli `levels` (UY-12 ile uyumlu); kampüs okulu kapsama alındı (md. 2/1, 4/1-b) ve `in_campus` alanı `KAMPUS_YONETIMI` satırının koşulu. §6.1 `kosul` sözlüğü aktarımda (G3) [G2] |
| KM-17 | düşük | işlendi | §13 D42; §2.3.1 `.od-yasakli-adlar.txt`; §12.B `.gitignore`, sızıntı kapıları | Yasaklı adlar depo dışı `.gitignore`'lu dosyadan; CI'da depo sırrı (yayın işi). Özet (hash) yolu seçilmedi: firma adının özeti de kısa bir aday listesiyle doğrulanabilirdi [G1] |
| KM-18 | düşük | işlendi | §4.4.6-6 | §8.6 "ihlal dökümü" çıktısı ve kılavuz kontrol listesi aktarımda; matriste satırı var (§4.4.2), erişim günlüğü türü `IHLAL_DOKUMU` [G1] |
| MA-1 | yüksek | işlendi | §6.1 (`dayanak_turu`, `karar`, kullanıcı kararı kuralının yürürlüğü); §6.4.3 `denetleme_kurulu.yk_uyesi_olamaz` (yürürlük 01.12.2023); §6.4.2 `okul_muduru_uye_olamaz`; §10.3 `dk::test_ekim_2026_genel_kurulunda_da_gecerli`; KE-25 | Atıf "kullanıcı kararı A-2 (gerekçe md. 14/4)" biçiminde basılır; hiçbir yerde "Yönetmelik gereği" denmez [G3] |
| MA-2 | yüksek | işlendi | §6.1 `tur` ve `sert_gerekcesi`; §6.4.7-6.4.10 türler; §6.4.11 dağılım; §10.3; KE-23 | Kullanıcı kararı D1: v1'in 23 "hesap parametresi"nden 15'i programın hesapladığı değer olarak sert kaldı, 8'i (ay sayısı, teminat, TÜFE artışı, kiralama usulü, EK-3 puanı, servis ücreti, izin, ihbar) girilen değer olarak uyarı oldu. Hesaplanan değer sertliği gerçek kaydı engellemez: fiilî tutar kaydedilir, fark uyarı (banka hareketi reddedilmez). "Hesap parametresi" ifadesi belgeden kalktı [G3] |
| MA-3 | yüksek | işlendi | §6.4.10 `personel.yillik_izin_gun`, `personel.ihbar_hafta`; §10.3 `pr::*` | Basamaklar lafızdaki gibi (≤5 / 5-15 / ≥15), 18 yaş altı ve 50 yaş üstü en az 20 gün; ikisi `en_az` + uyarı; ihbarda `kosul` belirsiz süreli sözleşme; paragraf atıfları. Personel modelinde yaş ve sözleşme türü alanı aktarımda (sürüm 2) [G3] |
| MA-4 | yüksek | işlendi | §6.4.9 `servis.komisyon_karar_cogunlugu` (S), `servis.komisyon_cekimser_ve_serh` (U); §10.3 | Kimlik bölündü (yayımlanmamıştı); §7.7 etiketi aktarımda [G3] |
| MA-5 | yüksek | işlendi | §6.4.9 `servis.ek3_puanlama` (U); §10.3; §10.4 (AYNEN 30 · UYARLA 39 · ALMA 2) | Kademe dışı puan uyarı + gerekçe (D1); ara kademe (2. kriterde 1, 3. kriterde 3) uyarısız testi eklendi; ikili kriter testi UYARLA'ya geçti [G3] |
| MA-6 | yüksek | işlendi | §6.4.8 `kantin.istekli_belge_sarti`; §10.3 | İki kademeli değer; uyarı iki hâlde; iki test [G3] |
| MA-7 | orta | kısmen | §6.2-2; §6.4.1 `genel_kurul.divan_uye_turleri` → F1c; §6.4.6 `harcama.alim_komisyonu_en_az`, `_uyeleri` → F1c; §6.4.11 DOĞRULANMADI-14; §6.3 son paragraf | (a) ve (c) işlendi: kurallar `r1`'e alındı (davranış fazı ayrı). (b) Genelge 2020/8 metni korpusta var ama çapasız; korpus bu grubun dosyası değil: A-1/a ve A-1/b çapalarının eklenmesi ve BENIOKU notu aktarımda. Çapa gelince `temsilci.kantin_denetim_komisyonu` (F1c) ve `kantin.denetim_aylik` (F5) girer; o zamana kadar sayıma girmedi [G3] |
| MA-8 | orta | işlendi | §6.4.7 `kira.ay_sayisi` (asıl EK-2 md. 4, ek 19/3, 01.12.2023); §6.4.5 `etkinlik.ders_saatleri_disinda` (`kosul: etkinlik.duzenleyen = UCUNCU_KISI`, SEY 5/3 bilgi); §6.4.7 `arz_bedeli.takip_sorumlulari` (yorum); §10.3 | — [G3] |
| MA-9 | orta | işlendi | §6.4.8 `kira.fesih_tazminati` (S, hesaplanan değer), `kira.bakanlik_tahliye_gun` (U); §6.4.4 `temsilci.pay_dagitim_komisyonu` (U, F1c); §10.3 | Fesih tazminatı D1 gereği programın hesapladığı tutar olduğu için sert (hesaplanan değer); fiilî tahsilat farkı uyarı [G3] |
| MA-10 | orta | işlendi | §6.4.9 altı yeni kural; §10.3 `sv::test_belge_ve_yas_sinirlari` parametreleri | Öneriden farkı: `servis.arac_yasi_hesabi` ve `servis.sofor_b_sinifi_sayilan_yil` programın hesap yöntemi olduğu için D1 gereği sert (hesaplanan değer; kayıt engellemez, sonucu uyarı kuralına girer); öteki dördü uyarı [G3] |
| MA-11 | orta | işlendi | §6.4.1 `divan_uye_turleri`; §6.4.2 `yonetim_kurulu.uye_turleri`; §10.3 `yk::test_veli_olan_ogretmen_yk_ye_eklenebilir`, `gk::test_divana_veli_olan_ogretmen_uyarisiz` | Birleştirmede: `OabPerson.is_parent` eklendi; §5.2.2 koltuk uygunluğu bu işarete bağlandı. Uygunluk veli olup olmamaya bakar; `OabPerson` veli işareti aktarımda (G2) [G3] |
| MA-12 | orta | işlendi | §6.1 "Olay tarihi" tablosu ve "Erişim" (`denetlenmedi` durumu); §6.4.11 DOĞRULANMADI-16; §10.3 `kn::test_2023_oncesi_sozlesme_kaydedilir_bilgi_notu` | Bilinmeyen kimlik (fail-closed) ile yürürlük dışı olay (denetim yok, bilgi notu) ayrıldı; uyarı değil bilgi notu [G3] |
| MA-13 | orta | işlendi | §6.1 `madde` alanı; §6.3 D4; §6.4.7-6.4.10 paragraf atıfları; §10.2 `kp::test_cok_fikrali_maddede_fikra_zorunlu` | EK-2 md. 4, 6, 7, 8, 22; 4857 md. 17, 53, 56; 2886 md. 84; md. 24/1 [G3] |
| MA-14 | orta | işlendi | §6.3 D4 (a-c); §10.2 `kp::test_mulga_bende_atif_yakalanir`, `test_yd_bende_atif_yakalanir`, `test_yd_ibareye_atif_yakalanir`, `test_yeniden_duzenlenen_iptal_bent_gecer` | — [G3] |
| MA-15 | orta | işlendi | §10.1 (sınırın iki yanı listesi); §10.3 | (a) eşiklerin uyarısız tarafı; (b) seçim biçimi, beyan (KM-8 ile okul uygulaması hatırlatması olarak), belgesiz çalışan, hısımlık derecesi ve kayın, diploma dönemi; (c) 540 sabit testi [G3] |
| MA-16 | düşük | işlendi | §6.4 ilgili satırların Not sütunu ("yorum"); `genel_kurul.gundem_degisikligi` (sıra değişikliği çıkarıldı, tür U); `uyelik.ayrilan_veli_devam` (kursiyer); `kira.ust_uste_odememe_fesih` (birim adet) | — [G3] |
| MA-17 | düşük | işlendi | §6.1 `yururluk` tanımı ("değerin bugünkü hâli"); §6.4 yürürlük sütunu | 5+5 ve 3+3 kuralları 09.02.2012 (11/1-a, b'nin değişmeyen kısmı), DK görev bölümü ve tek birlik 09.02.2012, VİF'li iki kural 10.10.2024, `alim_komisyonu_uyeleri` 09.02.2012, `secim_bicimi` 09.02.2012 [G3] |
| MA-18 | düşük | işlendi | §10.6 ("`r1`'deki 53 kural"); §6.4.11 dağılımı; §6.4.4 SEY ve RPD satırları | Sayı v1'de 49/50 tartışmasıydı; F0-9 sonrası `r1` = 53 (+divan, +2 alım komisyonu, +pay dağıtım, −kampüs). Müdürün YK'ye girememesi kullanıcı kararı sayımına geçti [G3] |
| MB-1 | yüksek | işlendi | §7.1, §5.2.3 | A-1: `CAGRILDI → ILAN_EDILDI` "ikinci toplantı tarihi en geç 30 gün sonra [U]; olağanda ve olağanüstüde"; `YETER_SAYI_YOK` "olağanüstüde de ikinci toplantı ilanı"; "yeni çağrı önerilir" silindi. E05 kabul ölçütü aktarımda [G2] |
| MB-2 | yüksek | işlendi | §5.2.3 | `AgendaItem`: olağanüstüde gündem dışı madde **uyarı + gerekçe** (`genel_kurul.olaganustu_gundeme_baglilik`; B-13); "sert, hukuken geçersiz karar" ve "eşitlenmeli" silindi [G2] |
| MB-3 | yüksek | işlendi | §9.3 (müdür blokları tablosu); §9.6 giriş ve E05; §10.5 `ev::test_e05_imza_cagirana_gore`, `ev::test_yk_ve_gk_belgelerinde_mudur_yazar_degil` | §4.4.1 `mudur` dayanak sütunu (9/6, 13/8, 25/2) aktarımda (G1) [G3] |
| MB-4 | yüksek | işlendi | §7 okuma kılavuzu, §7.1, §7.2, §7.6, §7.7, §7.8 | Birleştirmede (U1, K2 lafzı): DK görev bölümünü, E02'yi ve denetim planını DK hesabı yazar; `yonetici` yalnız DK yedeğini çağırır (M2). R2: Kim sütunu §4.4.2 matrisine bağlandı. Kantin ve servis Kim hücrelerinden `mudur` çıktı, "kâğıtta Okul Müdürü / Komisyon Başkanı imzalar" notu. Görev bölümü ikiye ayrıldı (YK: sekreter; DK: yonetici kaydı + denetleme_kurulu E02). DK yedeği yonetici, YK kararı gerekmez (md. 14/6). Olağanüstü çağrıya `baskan` (md. 13/8) eklendi. Matris tarafı aktarımda (G1) [G2] |
| MB-5 | yüksek | işlendi | §5.2.9, §7.6, §7.7 | D4: kantinde onaysız kesinleşme **uyarı + gerekçe**, makam ve tarih kaydedilir (dayanak DOĞRULANMADI); serviste **sert** (U-E 4/1, OSAY 8/2). `Tender` satırındaki ortak "(§7.6, §7.7) sert" ibaresi ayrıldı. §9.7 satırı aktarımda [G2] |
| MB-6 | yüksek | kısmen | §5.2.9, §7.6, §7.7 | Birleştirmede (U3): `servis.dosya_geri_alinamaz` kuralı eklenmedi (kural sayımı 157 sabit); §7.7'de başvuru kaydı silinmez, "geri verildi" durumu yoktur, geri isteme gelen evrak + U-E md. 7/2 bilgi notu [B]. D1 ile: md. 21/2 yer teslimi tarihi girilen değer → [U] (`kira.yer_teslimi_gun`). U-E 7/2 "[S — kayıt kilidi]" kaldırıldı: başvuru kaydı silinmez (altın kural 4), dosyanın geri verildiği kaydedilirse [U]; `servis.dosya_geri_alinamaz` (U) kuralı aktarımda (G3) [G2] |
| MB-7 | yüksek | işlendi | §5.2.5, §5.2.9, §7.3, §7.6 | `EMANET` çıkışları üç yol: (a) md. 22/4 ve EK-2 md. 22/2 hâlleri gelir kaydı + tazminat; (b) EK-2 md. 7/4 ödememe feshi mahsup + kalanın iadesi; (c) EK-2 md. 8 sona erme ve md. 21/2 vazgeçmede iade. Emanet giriş/çıkış ayrı yönlü kayıt, TEFBİS'e gelir diye girmez; `OabContract.guarantee_disposition`. md. 22/4 ↔ EK-2 md. 7/4 örtüşmesi, "birliğin alacakları"nın kapsamı ve md. 22/1 / EK-2 md. 15 fesihleri → §15 B-14 [G2] |
| MB-8 | orta | işlendi | §3.4, §5.2.9, §7.6 | `BidderDocument.subject`'e `KIRACI`; "ihale aşamasında istekli belgesi değildir (md. 20/4-5); sözleşmeden sonra kiracının ve çalışanların portör, adli sicil, hijyen belgeleri izlenir (md. 23/4; EK-2 md. 9; HEY 5/1)". §3.4 "işletmeci ve çalışanlar" [G2] |
| MB-9 | orta | işlendi | §5.2.9, §7.6 | Büyükşehir olmayan il merkezinde EK-2 Özel Şartlar md. 2'ye md. 17/1-a-2 pay notu basılır, genel şart 7/2 boşluklarında ilçe "—", genel şart lafzı değişmez; `OabContract.special_terms`. E42 kabul ölçütü ve §15 KE-n aktarımda (G3) [G2] |
| MB-10 | orta | işlendi | §5.2.3, §5.2.4, §7.1, §12.A | `AuditReport.md6_violation_found` (DK açıkça işaretler); `irregularity_found` yalnız rapor bayrağı; md. 14/5 önerisi ve `escalated_assembly` yalnız md. 6 işaretiyle; `GeneralAssembly.call_audit_report`. §7.1 "usulsüzlük tespiti" → "md. 6'daki görev ve yetkilere aykırı faaliyet". Test adı ve §10.4 eşlemesi aktarımda [G2] |
| MB-11 | orta | işlendi | §7.1 | E13: "Yönetmelikte açık bildirim hükmü yok (DOĞRULANMADI); okul uygulaması — dolaylı 13/4, 27/1; hüküm diye sunulmaz". §9.5 dayanak hücresi aktarımda (G3) [G2] |
| MB-12 | orta | işlendi | §9.5-9.6 E63-E79; §9.7; §10.5 | Mevzuatın istediği belgeler yeni kod aldı; değerlendirme tutanağı E54'e, kasa sayımı E37'ye, biten koçan teslimi ve koçan envanteri E22'ye bölüm olarak bağlandı (KE-26). Öneriden farkı: iptal/kayıp yaprak (E67) ve banka imza yetkisi yazısı (E66) ayrı imzalı belge oldukları için kendi kodlarını aldı. §7 ad → kod listesi aktarımda [G3] |
| MB-13 | orta | işlendi | §3.1, §5.2.6, §7.5, §7.8 | §3.1 koçan dayanağı "16/5-7, 23/1-e, 23/6; EK-1". `ReceiptBookRegistry.certified_by/on/no` isteğe bağlı, boşken bilgi; kapanış denetiminde "koçan tasdik kaydı yok" bilgi satırı. Yorum sorusu → §15 B-15. E22 tasdik sütunu aktarımda [G2] |
| MB-14 | orta | işlendi | §3.2, §5.2.9, §7.5, §7.6, §8.6 | Kendi bölümlerindeki beş satır: §3.2 (16/7'deki 1988 atfı; 23/6 tarihsiz); `RentableAsset.full_year` (19/3 + EK-2 md. 4 dokuz ay); §7.5 TKB §4.1 Tablo 4 (`#bolum-4-1`); §7.6 "kiraya veren birliktir; muhammen bedel komisyonu ve ilan MEM, pazarlık md. 20/3 komisyonu"; §8.6 "§4 Tablo 3, §4.1 Tablo 4". §9'daki E03, E27, E36 satırları G3'te [G2] |
| MB-15 | düşük | işlendi | §9.3 tablosu (E37 eklendi; E02, E32, E61'den müdür bloğu kalktı); §9.6 E37 (devralan yeni başkan + yeni muhasip), E56 (imza "Taşımacıyı Tespit Komisyonu"); çapasız atıflar §9.3, §9.4, §9.5 E06, §9.7'de bağlantılı; §9.1-4 RYUE md. 11, 13, 14 | — [G3] |
| UY-1 | yüksek | işlendi | §4.1 değişmez; §4.6.3; §4.4.3 boşta kilit; TK14, TK19; §4.2 | (1) DEK yokken iş verisi yazılmaz, gün işi ertelenir; (2) önerideki `bekleyen-olaylar.json` yerine kilitli kip mühürlü satır (R11); (3) `actor` = `HESAP`/`SISTEM`; (4) uzun iş sayacı tembel kilidi erteler; (5) testler §4.6, §4.2 [G1] |
| UY-2 | yüksek | işlendi | §4.6 | `ComplianceItem.resolved_at` ve `AttendanceCorrection` G2'nin modelleri (aktarım) [G1] |
| UY-3 | yüksek | işlendi | §4.4.4 "Dosya anahtarı"; TK22; TK12 sayımı; §2.3.1 | Önerinin (a) yolu seçildi (sarmal SQLite işlemine girer); test "yenilemeden sonra her `Attachment` açılır" F4 provasında. Fingerprint KM-11 ile [G1] |
| UY-4 | yüksek | işlendi | §5 O2, §5.2.4, §5.2.5, §5.2.8, §7.3, §7.8 | R12: O2'ye beyaz liste (deftere geçirildi, TEFBİS'e girildi, deftere işlendi işaretleri ve `MarkBatch`, yeniden basım, işaretin kapattığı eksik kalemin `resolved_at`'ı); `KESIN` kilidinin tek istisnası bu alanlar. `tefbis_fix_needed` alanı kaldırıldı: "TEFBİS'te düzeltilecek" ters kayıttan hesaplanır, kapanmış kayda yazılmaz [G2] |
| UY-5 | yüksek | işlendi | §5.2.1, §5.2.2, §5.2.3, §5.2.7, §7.1, §7.8 | R12: olağan genel kurul `PLANLANDI` olunca yeni dönem `HAZIRLIK` (tarih aralığı boş, kısıtlar uygulanmaz, mali kayıt yazılmaz); YK/DK adayları, seçilenler ve bütçe ona; divan genel kurulun dönemine; `TUTANAK_TAMAM`'da `ACIK`, eskisi `KAPANISTA`; GK `IPTAL` → `HAZIRLIK` `IPTAL`. "En çok bir KAPANISTA" kısıtı kaldırıldı (kapanmayan dönem yeni dönemi engellemez; SU-6'nın §7.8 tarafı) [G2] |
| UY-6 | yüksek | işlendi | §5.2.5, §7.3, §8.2 | `fingerprint` tekilliği yalnız `void = False` satırlarda (kısmi kısıt); eleme yalnız `void` olmayanlara karşı; önizleme "geri alınmış partiden N satır yeniden alınacak". Ayrıca parmak izi HMAC (KM-11'in §5 tarafı) [G2] |
| UY-7 | yüksek | işlendi | §5.2.5, §5.2.6, §7.3, §7.5 | Yaprak–kayıt bağı `LeafUse` (ETKIN/COZULDU) tablosuna alındı; `LedgerEntry.receipt_leaf` ve `ReceiptLeaf.ledger_entry` kalktı (O6). Ters kayıt eski bağı çözer, düzeltilmiş kayıt aynı yaprağa bağlanır; ters kayıt yaprak istemez. `KULLANILDI → IPTAL` eklendi (bağlı kayıt iptale ya da ters kayda zorlanır) [G2] |
| UY-8 | orta | işlendi | §4.4.5 tek olay tablosu; §4.4.1 kurallar; §4.6.1 iki depo; §4.4.4 DEK yenileme 4-5 | Görev bölümü ve düşme hesabı **askıya alır**, kapanış ve açılış `yonetici`nin; "bütün organ hesapları" → "eski dönemin organ hesapları"; DEK yenilemesi eski hesaplar kapandıktan, yenileri açılmadan önce. §7.2, §7.8 metni aktarımda [G1] |
| UY-9 | orta | işlendi | §5.2.5, §5.2.7, §7.4 | `ExpenseFile.payment_entry` kalktı; ödeme bağı tek yönlü `LedgerEntry.expense_invoice` → `ExpenseInvoice` (1—n). `ODENDI`: faturalara bağlı KESIN gider toplamı = fatura tutarı ve her kayıt bankayla tam eşli ya da KASA (kasa yolu [U]). Kasa yolunda E27 yerine "kasa çıkış tutanağı" (kod bekliyor) [G2] |
| UY-10 | orta | işlendi | §5 O1, §5.2.1, §5.2.2, §5.2.3, §5.2.7, §5.2.9 | `IPTAL` durumu: `OrganMembership`, `OabBudget`, `OabContract`, `OabTerm` (hazırlıkta), `ExpenseInvoice`; `BudgetLine.is_cancelled`, `AgendaItem.removed_by_vote`. `OrganMembership` için iki kısmi tekil kısıt (assembly dolu / boş). Gündem sırası iki adımlı güncelleme [G2] |
| UY-11 | orta | işlendi | §5.2.3, §7.1, §7.4 | A-1 ve B-13 §5 ve §7'de eşitlendi. M-11: §7.4 TALEP "yonetici müdürün kâğıt talebini gelen evrak olarak kaydeder; E25 taslağını hazırlamaz". E25 Üreten satırı (§9.6) aktarımda (G3) [G2] |
| UY-12 | orta | işlendi | §6.1 `kosul` sözlüğü; §6.4.4 (kampüs kuralı çıkarıldı, KE-24); §10.2 `kp::test_kosul_*`; §10.3 `tm::test_karma_okulda_iki_kademenin_satirlari` | Birleştirmede (U2): kampüsteki okul kapsamda, `in_campus` var; md. 13/7 değer taşımadığı için kural yok, E03'te kayıt satırı (KE-24). `SchoolConfig.levels` (çok değerli, KARMA kalkar) aktarımda (G2) [G3] |
| UY-13 | orta | işlendi | §6.2-6; §9.1-2; §9.6 E39; §10.5 `ev::test_yeniden_basim_icerik_ozeti_ayni` | Birleştirmede: `GeneratedDocument.content_json` §5.2.8'e ve §5.4 saklama kuralına girdi. İçerik JSON'u her üretimde saklanır, yeniden basım ondan çizilir; E07/E08 R9 istisnası. `GeneratedDocument.content_json` ve §5.4 saklama kapsamı aktarımda (G2) [G3] |
| UY-14 | orta | işlendi | §14 F1b, F1c, F3 | Sihirbaz F1b'de üç adım; ilk dönem adımı F1c'de; banka ve devreden bakiye adımı F3'te [ana oturum] |
| UY-15 | düşük | işlendi | §6.1 `davranis_fazi`; §6.2-2; §6.3 D6; §10.1 işaretler; §10.2 | `kural_deger` / `kural_davranis` işaretleri, `pyproject` `markers` kaydı. F1c'de girip davranışı sonra gelen kural sayısı 18 [G3] |
| UY-16 | düşük | işlendi | §6.1 `degisiklikler`; §6.2-1, 3a, 5; §6.3 D2; §10.2 | Üçüncü tür "düzeltme"; geçiş ekranında hesabı değişecek kayıtlar zorunlu [G3] |
| UY-17 | düşük | işlendi | §11.1 B10, B12; §11.4; §4.2 çıkış 12; §12.B `pyinstaller/` | Yerel python-docx 1.2.0'da doğrulandı (`docx/api.py` varsayılan şablonu dosya yolundan okur) [G1] |
| UY-18 | düşük | işlendi | §9 giriş; §9.2 (konum cümlesi gövdede, imza bloğunun üstünde); §10.5 `ev::test_docx_pdf_icerik_esdegerligi` | Kanonik metin akışı tanımlandı [G3] |
| UY-19 | düşük | işlendi | §10.6 ("53 kural") | `KD_*` "25 ad" → "24 ad" düzeltmesi §2.3.1'de; aktarımda (ana oturum) [G3] |
| UY-20 | düşük | işlendi | §9.6 E10 (`SECILDI`), E20-E21 (`LedgerEntry.donor_name`), E22 (`OfficialBook`), E46/E58 (`BidderDocument`), E26 (tek kaynak); §9 giriş ve E04 ("KütD-E13"); §9.2 kısa adlar KDT/TFB/DFT; §10.5 test adları | Birleştirmede: `ExpenseFile.commission_members` kaldırıldı; `add_installments` notu ve §2.3.3 negatif örnek yazıldı. §12.A `add_installments` notu, §4.4.5/§12.B "KütD-E18", §2.3.3 kalıntı testinin negatif örneği, `ExpenseFile.commission_members` → `OrganMembership` aktarımda [G3] |
| SU-1 | yüksek | işlendi | §7 okuma kılavuzu, §7.3, §8.1, §8.3 | D2: mali kayıtlar yalnız muhasip; yonetici yalnız "TEFBİS'e girildi". §7.3'e "Aylık iş sırası" tablosu (adım, zaman önerisi, kim, beklediği adım, evrak). Döngüsel atıf kaldırıldı (§7 matrise gönderir). Denetimin "yonetici adına girsin" önerisi D2 nedeniyle alınmadı. İşaret düzeyinde tablo §4.4.2'de (G1, aktarım). Muhasip görüşmesi §14 F3'te zaten var [G2] |
| SU-2 | yüksek | işlendi | §5.2.7, §7.4, §8.2 | R6: `SUREKLI_ODEME` dosyası dönem başı genel karara bağlı tek dosya, çok fatura ve ödeme (`ExpenseInvoice`; durumlar `ALIM → SUREKLI → KAPANDI`); banka masrafı da bu dosyaya. Küçük alım kısa yolu (`path = KISA_YOL`) tek ekran: TALEP, KARAR, ALIM kendiliğinden, gerekçe genel karara toplu bağlı. F4 kapı senaryosu aktarımda [G2] |
| SU-3 | yüksek | işlendi | §5 O3, §5.2.7, §7 okuma kılavuzu, §7.1-§7.4, §7.8 | R5: O3 "uygun · eksik · sapma"; eksik gerekçe istemez, `ComplianceItem(EKSIK)` "tamamlanacaklar"a düşer, kapatıcı geçişte hâlâ duruyorsa gerekçe; toplu gerekçe `ComplianceJustification` (aynı kural + kök neden: defter tasdiki, geçiş sayaç beyanı, genel karar). §6.1 şema alanı ve test aktarımda (G3) [G2] |
| SU-4 | yüksek | işlendi | §5.1, §5.2.1, §5.2.2, §5.2.5, §5.2.6, §5.2.8, §7.8, §7.9 | R7: yeni **§7.9 Geçiş kurulumu** (8 adım): ilk dönem ve `program_start_date`; görevdeki kurul `source = DEVRALINAN` (aynı GK adayı şartı aranmaz); sayaçlar toplu beyan; defterlerin son sıra no/sayfa; açılış bakiyesi dönem başı ya da başlama günü (`pre_program_*` toplamları, kanıt); toplu defter/TEFBİS işareti (`MarkBatch`, `GECIS`); koçanda `GECIS_ONCESI`; süren sözleşmeler. Organ kısmı F1c, mali F3. Açılış günü seçimi → §15 B-18. Kapı senaryoları aktarımda [G2] |
| SU-5 | yüksek | işlendi | §7.10 | R8: yeni **§7.10 Pano ve takvim**: kaynaklar (süre kuralları, `ComplianceItem` TAKVIM ve EKSIK, iş kuyrukları, RH-001 Bölüm 6, kurulum yol haritası), rol başına görünüm, teslim yolu ("bu hafta yapılacaklar", velilere "bu ay sizden beklenenler" ve büyük yazı — R5 karşılığı), fazlar (kabuk F1c, kalemler her fazda) [G2] |
| SU-6 | yüksek | işlendi | §4.4.5 (görev bölümü, dönem kapanışı, MY satırları); §4.4.4 DEK ön koşulu; TK12 | R12: eski organ hesapları görev bölümüyle askıya, hesap geçişinde kapanır; kapanışı `yonetici` yapar; DEK yenilemesi eski kapanınca-yeni açılmadan önce → yeni kurula tek geçici parola. Eski dönemin kalan işi ve kapanmayan dönem (§7.8) G2'de (aktarım) [G1] |
| SU-7 | orta | işlendi | §3.1, §5.2.5, §5.2.8, §7.2, §7.3, §8.3, §8.6 | `MarkBatch` toplu işaret: E17 defter sayfa düzeninde (`OfficialBook.lines_per_page`), "a-b sayfalarına geçirildi" tek işlemi her kaydın sayfasını yazar; TEFBİS toplu işareti E18 sırasıyla; karar sıra no ve sayfası öneriyle dolar. E17 biçimi aktarımda; F7 ölçümü §14'te zaten [G2] |
| SU-8 | orta | işlendi | §5.2.7, §7.3 | `MonthlyReport.cutoff_date`; teslimden sonra o aya düşen kayıt sonraki bildirimin "önceki aylara ait geç kayıtlar" bölümüne; aylık iş sırasında bildirim muhasibin girişinden sonra, ayın son iş günü. E31 kabul ölçütü aktarımda [G2] |
| SU-9 | orta | işlendi | §14 F2, F3, F7; §16 R1, R5, R15 | F7'ye beş ölçülebilir saha ölçütü; F3'ten önce muhasiple görüşme; F2 canlı kullanımı Ekim'deki genel kurulda [ana oturum] |
| SU-10 | orta | kısmen | §9.6 giriş ve E25; §9.3; §6.4.6 `harcama.okul_yazili_talep`; §10.3 `ml::test_gelen_evrak_talebi_yeter` | Birleştirmede: E25 kapsam sorusu §15.2 M-11 satırına "kullanıcıya sorulması önerilen" diye yazıldı. Çelişki giderildi: E25 müdür hesabından (M-11), müdür programı kullanmıyorsa kâğıt talep gelen evrak olarak kaydedilir ve zincir (E27 kontrol listesi) bu kayıttan yürür. **Reddedilen kısım:** M-11'in yalnız E35 ve çağrılarla sınırlanıp E25 taslağının `yonetici`ye verilmesi — `kararlar.md` M-11'i bağlayıcı kullanıcı kararı sayıyor; değiştirmek kullanıcı sorusu ister (aktarımda soru önerisi). §4.4.2 dipnot ² ve ⁴'ün M-11'e eşitlenmesi aktarımda (G1) [G3] |
| SU-11 | orta | işlendi | §3.1, §5.2.4, §7.2, §7.8, §8.5 | `BoardDecision.DEFTERDE_SAKAT`: defterde yazılı ama yeter sayısı olmayan karar iz olarak girilir (defter no, sayfa, gerçek katılım ve oylar, açıklama → SAPMA); geçerli sayılmaz, hiçbir akışı beslemez, DK listesine ve kapanış denetimine düşer. Sert kuralın anlamı "kaydedilemez"den "geçerli sayılmaz"a döndü → §15 B-17 [G2] |
| SU-12 | orta | işlendi | TK10; §4.4.4 yedek başlığı ve DEK yenileme 6-7; §2.3.1 `guvenlik.json`; §12.B `backup_crypto.py`, kurtarma belgesi | Anahtar no + tarih kâğıtta ve başlıkta; geri yüklemede "bu yedek … anahtarla açılır". E37 satırı aktarımda [G1] |
| SU-13 | orta | işlendi | §14 (her kapıda kılavuz bölümü), F7; §9 E63; §16 R5 | Hesap teslim pusulası (E63) ve kılavuzun "yeni kurulun ilk ayı" bölümü [ana oturum] |
| SU-14 | düşük | işlendi | §8.3 | E18'e "kimlik no kaynağı" sütunu (makbuz seri-cilt-sıra · dekont referansı · "kâğıt kaynak yok — bağışçıdan alınmalı"); dekontta kimlik no bulunup bulunmadığı DOĞRULANMADI. E18 kabulü aktarımda [G2] |
| SU-15 | düşük | işlendi | §14 (her kapıda 1366×768), F1a, F3, F7 | Ekran denetimi her kapıda; F7'de 4 GB'lık makinede açılış ve PDF süresi [ana oturum] |
| SU-16 | düşük | işlendi | §4.2 kapanış maddesi; §2.3.1 tarayıcı deposu notu | Birleştirmede: §7 girişine "yarım kalan metin" paragrafı ve §7.10 kaynağı (§4.2) eklendi. İlke ve "tarayıcı deposuna yazılmaz" kuralı §4'te; taslak kaydının model ve ekran ayrıntısı §7'de (aktarım) [G1] |
| EK-1 | yüksek | işlendi | §5.2.3, §7.1 | MB-1 ve MB-2 ile aynı düzeltme (A-1, B-13) [G2] |
| EK-2 | yüksek | işlendi | §4.4.1 müdür ve DK satırları; §4.4.2 matris, dipnot ¹, ⁴, ⁵, ⁶, ⁹ | Birleştirmede (U7): md. 27/3 MEM bildirimi E70 oldu — K2'deki dört müdür yazısından değil, KE-19 kapsamında taslağı `yonetici`, imza Okul Müdürü (§4.4.2 dipnot ⁶, §7.12). M-5 (¹), M-6 (⁵), E25 yalnız `mudur` (⁴; eski dipnot ² "yonetici zaten yazar" kaldırıldı), müdür kantin/serviste iş yapan rol değil (⁹), MEM'e bildirim matristen çıktı: md. 27/3'ün ikinci adımı okulun resmî yazısıdır, programda üretilmez (⁶; K2 lafzı ve KE-19). §7, §9, §10.5 ve M-11 "dört" düzeltmesi aktarımda [G1] |
| EK-3 | yüksek | işlendi | §9.5-9.6 E63-E79; §9.7; §10.5 `ev::test_katalog_kabul`, `ev::test_katalogdaki_her_kodun_testi_var` | Servisin tebliğ ve onaya sunma yazıları (E76, E77) ve öteki yeni servis belgeleri söz dağarcığı testinin kapsamında (E73-E79). §7 ad → kod listesi aktarımda [G3] |
| EK-4 | orta | işlendi | §4.4.2 "Bağlayıcılık" paragrafı; matris (M5 yalnız muhasip, M8'de DK görev bölümü ve planı); §4.4.5 | R2: matris tek bağlayıcı kaynak; §7 ve §9 daraltır, genişletemez; `yonetici` "adına" giremez. §7 Kim ve §9.6 Üreten hizalaması aktarımda [G1] |
| EK-5 | orta | işlendi | §6.4.1 (`gundem_degisikligi` U; `ikinci_toplanti_cogunluk_aranmaz` ve `karar_cogunlugu` S kaldı); §6.4.3 `koltuklar`; §6.4.8 `kira.imzadan_once_teslim_yok` (yeni, U); §6.4.9 komisyon kuralları; §10.3 | Tür tek kaynaktan (§6.4). Yer teslimi için "uyarı" yolu seçildi (D1: teslim tarihi girilen değer). §7.1 [B]→[S], §7.6 yer teslimi [S]→[U], takip sorumluları [B]→[U], §5.2.9 "sert" → uyarı aktarımda (G2) [G3] |
| EK-6 | orta | işlendi | §6.1 sert gerekçelerinin kapalı listesi; §6.4.11 dağılım; CLAUDE.md altın kural 3; §2.1; §15.1b D1 | Birleştirmede: §2.1 F0-b §6.1'in dört gerekçesiyle aynı metne getirildi. "Hesap parametresi" kalktı; A-2, KE-15 ve organ kişi türü listede. CLAUDE.md altın kural 3 ve §2.1 F0-b'nin aynı metne getirilmesi aktarımda (ana oturum; önerilen metin orada) Sert engelin üç hâli (hesap bütünlüğü + hesaplanan değer, hukuken geçersiz işlem, kullanıcı kararı) CLAUDE.md'ye yazıldı; A-2 ve KE-15 CLAUDE.md'de [G3 + ana oturum] |
| EK-7 | orta | işlendi | §14 (giriş ve tablo) | Faz ataması planın §3'üne bağlandı: kantin kira-pay F3, devir-teslim F4, genel kurul raporları F2'de dosya eki; kurulum sihirbazı F1b/F1c/F3'e bölündü [ana oturum] |
| EK-8 | orta | işlendi | §4.6; TK16 "model §4.6"; §2.3.1 "§5 modeli kabul ederse" kalktı; §12.B | — [G1] |
| EK-9 | orta | işlendi | §5.2.7 `SocialEvent`; §7.11; §6.4.5; §9.6 E36; §14 F4; §6.1 `kosul` `etkinlik.duzenleyen`; §6.4.5 etkinlik ve `gelir.proje_protokol_ucret_yasak` (F4); §9.6 E36 | Birleştirmede: `SocialEvent` modeli, `LedgerEntry.event` bağı ve §7.11 akışı eklendi. `SocialEvent` modeli ve `LedgerEntry.event` bağı (§5.2.7), §7 etkinlik akışı (G2) ve F4 kapısına E36 örneği (§14) aktarımda [G3] |
| EK-10 | orta | işlendi | §14 F1b, F1c | F1b kapısına "kapanmış hesap giremez" ve aile güvenlik testleri adıyla; F1c kapısına kılavuzun F1 bölümleri [ana oturum] |
| EK-11 | orta | işlendi | §12.A; §10.4; §12.A | Birleştirmede: §10.4'teki ikili kriter testi (MA-5 ile UYARLA) envanterde AYNEN olduğu için 16. sapmadır; sayım **56 · 289 · 28 = 373**. §10.4 esas alındı; envanterin dosya sayıları ve gerekçe sütunundan test başına çıkarımla 15 sınıf değişikliği listelendi (13 AYNEN→UYARLA, 1 UYARLA→AYNEN, 1 UYARLA→ALMA): **57 · 288 · 28 = 373**. `test_ikili_kriter…` AYNEN (§10.4). §10.4'ün sapma cümlesinin düzeltilmesi aktarımda (G3) [G2] |
| EK-12 | orta | işlendi | §9.6 E02, E04, E08, E14, E25, E26, E46, E58 | Birleştirmede: §5'e `OabTerm` dönem ayarları, `ExpenseFileLine`, `ExpenseQuote`, teslim alanları eklendi; alım komisyonu tek kaynak `OrganMembership(ALIM_KOMISYONU)`. Veri kaynakları düzeltildi; §5'e eklenecek alanlar (veri sorumlusu, YK toplantı günü, DK planı, harcama kalem/teklif/teslim, alım komisyonu tek kaynak) aktarımda [G3] |
| EK-13 | orta | işlendi | §4.3 korunan varlıklar; §4.4.2 hassas okuma listesinden "tam IBAN" çıktı | Kurumsal IBAN açık, maskesiz, günlüksüz. Alıcı IBAN'ı modelde yok; eklenirse kişisel veri alanı olur. E01/E27 ve `ExpenseFile` kararı aktarımda (öneri: alıcı IBAN'ı tutulmaz, E27'de elle) [G1] |
| EK-14 | orta | kısmen | §5.2.7, §7.1, §7.10 | M9 → §7.10. TEFBİS'e genel kurul sonrası yönetim, banka ve bütçe girişi → `ComplianceItem` yükümlülükleri (`TEFBIS_YONETIM_BILGISI`, `TEFBIS_BANKA_BILGISI`, `TEFBIS_BUTCE_GIRISI`; süre yalnız rehberde, kural değil). Kalan üç madde (kiracıya Ba bildirimine yetecek tahsilat belgesi, EBYS için yazı ve ekleri ayrı dosya, tutarın yazıyla okunuşu) §9/§15'in kararıdır → aktarım [G2] |
| EK-15 | orta | işlendi | §2.3.1 dosya HKDF dizgesi; §4.4.7 açık kopya kuralı; §11.3 font atfı §9.1'e; §12.B `letterhead.py` atfı §9.1'e | §9.1'deki üç karar (yazı tipi eşlemesi, PDF/A, birlik antedi) G3'e aktarıldı; antet F1c'nin ön koşulu diye işaretlendi [G1] |
| EK-16 | düşük | işlendi | §12.A | "Ön yüz `modules/okul-aile-birligi/` (S-27): ALMA — ekranlar aile kitiyle yeni; F1c ekranları yeni; gerekirse fazın başında okulapp okuması" satırı. §12.B YENİ tablosu aktarımda [G2] |
| EK-17 | düşük | işlendi | §7.1, §7.6 | (a) E13 dayanağı §7.1'de tek ifadeyle (MB-11). (b) §7.6 `BILDIRILDI`: YK kararı E15'te (konum cümleli taslak), E40 RYUE bildirim yazısı (konum cümlesiz). §9 tarafı (E13 dayanak hücresi, E40'ın KD listesinden çıkması, E41) G3'te [G2] |
| EK-18 | düşük | işlendi | §10.6 (53); §6 giriş tablosu ("F0-e (c)", "F0-e (d)"); §9 giriş ve E04 ("KütD-E13"); §6.1 `dayanak_turu` ve kullanıcı kararı yürürlüğü | `pre-kapanis-` (§2.3.2, §12.B), §5.1/§5.2.5'teki "F0-5" kimlikleri ve §4.4.5/§12.B'deki Kütüphane kodları ana oturumda / aktarımda [G3] |
