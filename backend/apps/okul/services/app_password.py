"""Hesaplı güvenlik çekirdeği — `guvenlik.json` şema 2: ilk hesap, kilit açma, parola, kurtarma.

Tasarım §4.3, §4.4.3-§4.4.4, §4.6.1; plan F1b-1 uygulama kararları. Dosya adı
aileden korunur: "parolayla veri anahtarını (DEK) açma" kavramı sürer, ama parola
artık tek bir yönetici parolası değil, her hesabın kendi parolasıdır (T1).
`shared.crypto` kriptografik ilkelleri (Argon2id türetme, zarf sarmalama, şifreli
alanlar, kör indeks, alt anahtar) sağlar; bu modül BÜTÜN AKIŞI yönetir:

    guvenlik.json (veri dizini, şema 2)        SQLite (db.sqlite3)
    ├── surum: 2, olusturma, kdf               ├── okul_account   (rol, ad-soyad şifreli,
    ├── hesaplar: [{id, tanitici, salt,        │                   durum, tarihler, mühür)
    │              sarmal, turetim,            ├── okul_auditkey  (iz anahtarı, DEK'le şifreli)
    │              hatali, askida}]            └── okul_schoolconfig
    ├── kurtarma: {no, tarih, salt, sarmal,          └── app_password_hash = DEK parmak izi
    │              dogrulandi}
    └── gecis: null | "KURULUM"

**Rol, ad-soyad, organ bağı, durum ve tarihler veritabanındadır** (`Account`);
dosya yalnız sarmalları ve hatalı deneme sayacını taşır. İşlevler hesap kimliğini
açıkça alır. Oturumu (hangi hesabın açık olduğu, boşta kilit) `apps.okul.oturum`
tutar; bu modül onu YALNIZ üç açılış yolunda açar (`unlock`, `unlock_with_recovery`,
`enable`: DEK ve iz anahtarı `OTURUM.ac` içinde, hesapla birlikte belleğe alınır) ve
servis içi yollarda hemen kapatır (`lock`). Parola doğrulaması "oturumdaki hesap"
sorusunu `OTURUM`'a sorar.

**İlk hesap zorunludur ve hesapsız dal YOKTUR** (aile iskeletinin "parolayı kaldır"
akışı ve çözme geçişi sökülmüştü; düz metin şifreleme geçişi de bu adımda kalktı,
tasarım §13 D29: ilk hesap kişi tabloları boşken açılır, şifrelenecek düz satır
yoktur). Kurulum sihirbazının ilk adımı ilk program yöneticisi hesabı + kurtarma
anahtarıdır; hesap kurulmadan kişi yazan uçlar 409 `parola_gerekli` döner
(`apps/okul/permissions.py`, `require_password_set`), şifreli alan anahtarsız
yazmaz (`KeyMissingError`).

**DEK hiçbir yerde açık durmaz**; her hesabın parolasından türetilen anahtarla ve
yazdırılabilir kurtarma anahtarından türetilenle ayrı ayrı sarılır. Her sarmal DEK'i
tek başına verir: şifreli alanlar en zayıf hesap parolası kadar korunur (tasarım
§4.4.6-5). DEK bu adımda değişmez (yenilemesi F4, TK12): parola değişimi ve
kurtarma anahtarının yenilenmesi yalnız ilgili sarmalı yeniler.

**HESAP SARMALI KİMLİĞE BAĞLIDIR** (kullanıcı kararı 02.11.2026; `shared.crypto` modül
başlığı). Sarmalın anahtarı `HKDF(Argon2id(parola, tuz), "od-hesap-sarmali/v1" ‖ kanonik
kimlik)`'tir: `id` alanı metin düzenleyiciyle başka hesabınkine çevrilen sarmal o kimlikle
açılmaz, sonuç yanlış parolayla aynıdır (sayaç ve gecikme dahil). Kimlik yazımda ve okumada
aynı kuraldan geçer (`crypto.canonical_account_id`; yalnız kanonik metin; okumada Argon2id'den
önce, kanonik olmayan kimlikte türetim koşmaz). Bütün yazıcılar
`_account_wrap`'ten (ilk kurulum, hesap açma, parola sıfırlama ve değiştirme, kilit
açılışında yenileme, kurtarma anahtarıyla açılış), bütün okuyucular `_try_unwrap_account`'tan
(kilit açılışı, parola doğrulama ve değiştirme, kurtarma anahtarının yenilenmesi, geri
yükleme) geçer. Bağsız sarmalı kabul eden yol YOKTUR: eski türetime geri düşüş, tembel göç
ya da sürüm alanına bakıp eski türetimi açma yoktur (dosya düz metindir; böyle bir yol açığı
yeniden açardı). Sarmalın `turetim` alanı ("od-hesap-sarmali/v1") YALNIZ RET İÇİNDİR:
türetimi seçmez, okuyucu tek türetimi bilir. Alanı taşımayan sarmal parolayla açılmaz: kilit
açılışı Argon2id koşturmadan, sayaca dokunmadan `UnboundWrap` (409 `iki_depo_tutarsiz`) ile
reddeder. Program bağsız sarmal yazmaz; böyle sarmal ya bağdan önceki (F1b-1) deneme
kurulumundandır (plan F1b-1 "Eski veri": veri dizini silinip yeniden kurulur) ya da etiketi
program dışından silinmiştir. İleti bu yüzden mühür iletisinin kalıbındadır: program dışı
değişikliği anar, Denetleme Kuruluna bildirim ister ve çıkışı söyler (zarfın üçüncü durumu,
kullanıcı kararı 03.11.2026: program yöneticisinin hesabı "Parolamı unuttum" yolundan
kurtarma anahtarıyla açılır, öteki hesapların parolasını program yöneticisi sıfırlar; sözlük
§1 "Hesap"). Teknik olarak kurtarma anahtarıyla açılış ve parola sıfırlaması sarmalı bağlı
biçimde yeniden kurar (`_replace_wrap`). Alanı sonradan eklenen bağsız sarmal yine açılmaz
(anahtar tutmaz); alanı silinen bağlı sarmal yalnız reddedilir. Kurtarma bölümü hesaba bağlı
değildir ve değişmedi. Şema sürümü 2 kalır (`SECURITY_STATE_VERSION`; yedek başlığı yalnız
kurtarma bölümünü taşır ve o değişmedi).
Kalan risk: parolasını bildiği hesabın DEK'ini program dışında türetip başka kimlikle
sarmalayan ya da mühürlü sahte satır üreten biri geçer; bu KOD ister (tehdit 6, 19).

SARMALIN TAZELİĞİ MÜHÜRLÜ SATIRA BAĞLIDIR (kullanıcı kararı 03.11.2026: "Tazelik kapatılır";
`shared.crypto` modül başlığı). Kimlik bağı tazeliği bağlamıyordu: her sarmal değişiminde
`guvenlik.json`'un eski kopyası `guvenlik-arsiv-*.json`'a girer, DEK parola değişiminde
değişmez; aynı hesabın ESKİ sarmalı o kimliğe meşru biçimde bağlıydı ve eski ya da geçici
parolayla açılıyordu (metin düzenleyiciyle geri konarak; kod gerekmeden). Artık hesabın mühürlü
`Account` satırı güncel sarmalın DEK'li özetini taşır (`wrap_digest`; `wrap_digest(...)`,
`crypto.account_wrap_digest`) ve iki aşamalı yazımın bekleyen özetini (`wrap_digest_pending`);
ikisi de mühre girer. Parolayla açılan sarmalın özeti ikisinden birini SABİT SÜREDE tutmalıdır
(`_check_wrap_digest`); ikisi de boşsa hesap parolayla açılmaz (fail-closed). Denetim noktaları:
kilit açılışı (`unlock`; parmak izi, satır ve mühürden sonra, durumdan önce), oturumdaki parola
doğrulaması (`_check_session_password`: parola doğrulama, parola değiştirme, kurtarma
anahtarının yenilenmesi) ve geri yüklemenin parola yolu (`geri_yukleme_yetkisi`, ORM'siz).
Kilit açılışında ve oturumdaki parola doğrulamasında tutmayan sarmal mühür uyuşmazlığı gibi
işlenir (`WrapDigestMismatch`, `AccountSealMismatch`'in alt sınıfı, 409 `hesap_muhru_tutmadi`):
işlem reddedilir, DEK elde olduğu için `BUTUNLUK` satırı düşer (`_muhur_bozuk_izi`, alan adı
`wrap_digest`), satıra dokunulmaz; hatalı deneme sayacı artmaz, gecikme uygulanmaz (parola o
sarmalı açtı: bu bir tahmin değil; sonuç tahminle de değişmez — yanlış parola yine sayılır).
Geri yüklemenin parola yolunda ret `RET_OZET`'tir: o yol ORM'sizdir, iz satırı yazılmaz, ret
yalnız günlüğe düşer ve hiçbir dosya değişmez. İleti bağsız sarmalınkiyle AYNIDIR
(`UNBOUND_WRAP_MESSAGE`). Özet bir PROGRAM kapısıdır: arşivdeki eski sarmal DEK'i sarmaladığı
için eski parolayı bilen biri onu program dışında yine açar (tehdit 6); bunu DEK yenilemesi
kapatır (TK12, F4: yeni DEK eski sarmallarla açılmaz; eski sarmal eski DEK'i ve onunla şifreli
eski yedekleri vermeyi sürdürür).

İKİ AŞAMALI ÖZET (kesinti güvenliği). Kural: her kesinti noktasında hesap `guvenlik.json`'da
O AN duran MEŞRU sarmalın (satırın asıl ya da bekleyen özetini tutan) parolasıyla açılabilir
kalır; yazım başarıyla bitince eski sarmal programda açılmaz (kalan hâller "KALAN RİSKLER"de).
Sarmalı değiştiren her yazıcı (kilit açılışında zorunlu yenileme, parola değiştirme, kurtarma
anahtarıyla açılış, `hesaplar.reset_password`):

1. yeni sarmal bellekte kurulur, özeti hesaplanır; TEK işlemde `wrap_digest` = dosyada ŞU AN
   duran sarmalın özeti (meşruysa: satırın asıl ya da bekleyen özetini tutuyorsa; değilse
   satırınki değişmez — `_kept_digest`), `wrap_digest_pending` = yeni sarmalın özeti, mühür;
   commit (`write_wrap_digests`; iz satırı `HESAP`, sıfırlamada aynı işlemin `PAROLA` satırı);
2. ikinci işlemde satırın asıl yazımı (`PAROLA`/`KURTARMA`/`GIRIS`; sıfırlamada `HESAP`) ile
   `wrap_digest` = yeni özet, `wrap_digest_pending` boş, mühür; işlemin EN SONUNDA, commit'ten
   önce sarmal `guvenlik.json`'a yazılır (arşiv kopyası önce).

Kesinti hâlleri: 1'den önce hiçbir şey değişmez; 1 ile dosya yazımı arasında dosyada eski sarmal
durur ve asıl özet onundur (açılır; bekleyen yeni özet dosyada olmayan sarmalı anlatır); dosya
yazımı ile 2'nin commit'i arasında dosyada yeni sarmal durur ve bekleyen özet onundur (açılır;
sıfırlamada satır zaten `PAROLA_YENILENMELI`dir). Kilit açılışı düzeltir: bekleyenle tutan sarmal
asıla terfi eder, asılla tutan sarmal varken bekleyen temizlenir (`_start_session`, `GIRIS`
satırının yazımında). Yeni hesap (`hesaplar.open_account`) ve ilk hesap (`enable`) tek aşamalıdır:
o kimliğin daha önce sarmalı yoktur, asıl özet doğrudan yazılır (kesinti hâli satırın sarmalsız
kalmasıdır, değişmedi).
KALAN RİSKLER: (a) BEKLEYEN ÖZET PENCERESİ — yalnız sarmal yazımıyla 2. adımın commit'i arasında
süreç ölürse ya da commit düşerse (sarmal yazımından sonra commit dışında düşebilecek adım
yoktur: kapalı hesap temizliği hatasını yutar, okunamayan arşiv atlanır), ilk kilit açılışına
dek eski sarmal da (asıl özet onundur) yeni sarmal da açar; arşivdeki eski sarmalı geri koyan
biri o pencerede eski parolayla açar ve açılış onu asıl bırakır, yeni parola geçersiz kalır
(çıkış parola sıfırlaması). Kesintisiz yazımda pencere yoktur. (b) SATIR GERİ SARMA artık
REDDEDİLİR ("SATIRIN İZİ"): mührü ve özeti tutsa da eski bir kopyadan geri konmuş satır kilit
açılışını, oturumdaki parola doğrulamasını, kurtarma anahtarıyla açılışı, hesap işlemlerini ve
geri yüklemenin parola yolunu açmaz. KALAN — veritabanının BÜTÜNÜYLE (iz dahil) eski bir kopyayla
değiştirilmesi ya da iz kuyruğunun satırla birlikte kesilmesi (satır geri sarılır, ondan sonraki
iz satırları silinir) bu denetimle yakalanmaz: satır kopyanın son iz satırını tutar. Kopyadan
sonraki her kayıt kaybolur. Görünür kılanlar: kilit açılışındaki çapa denetimi (`iz-durumu.json`
çapası kopyadan yeniyse "kuyruk kesik", çapadan sonra açık kipte `KILIT` varsa "çapa bayat",
dosya yoksa "çapa yok" — `BUTUNLUK` kartı; `iz-durumu.json` da kopya anındaki hâliyle geri
konursa program fark etmez), geri yükleme kartının OLMAMASI (veritabanı geri yüklemeyle değil,
program dışından değişmiştir), aylık kâğıt çapası (zincir başı kâğıttakinden geridedir; tasarım
§4.6.3 "Kalan risk"), kopyadan sonra alınmış günlük yedekler (yeni zinciri taşır), hesap
sahiplerinin "Son girişler" kartından düşen girişler ve kopyadan sonra parolası değişen
hesapların parola kaydının özeti (eski sarmallar arşivden de geri konmazsa giriş
`WrapDigestMismatch` ile reddedilir). Çapa denetimi ve geri yükleme kartı bu saldırgana karşı
bağımsız değildir. Geri yükleme notu MAC'siz bir dosyadır: önceki zincir başını çapanın ilerisinde
gösteren sahte bir not çapa denetimini atlatır ve yerine alanları boş bir geri yükleme kartı
çıkarır. Gerçek bir geri yüklemeden sonra not silinip `iz-durumu.json` eski bir kopyasıyla
değiştirilirse kart da çıkmaz. Kalıcı sinyaller aylık kâğıt çapası, günlük yedekler, `db-onceki-*`
dosyası ve onarımın `SISTEM` `HESAP` satırlarıdır. Hesabın yeni iz satırlarını silmek ya da
`model`/`object_id`'lerini değiştirip onları hesabın satırı olmaktan çıkarmak, satır geri sarmayla
birlikte yapılırsa bu denetimden geçer (`satir_izi` modül başlığı "KAPSAMIN SINIRI"). Silinen
satırdan sonrakiler yeniden numaralanırsa kayma zincir başına ulaşır; çapa (`kuyruk_kesik`) ve son
200 satır onu her zaman `BUTUNLUK` bulgusu olarak gösterir. Yeniden numaralamasız silme ve
`model`/`object_id` değişikliği ise yalnız değişen satır kilit açılışının 200 satırlık doğrulama
penceresindeyse (ya da hemen önündeyse) bulgu olur. Bulgu girişi engellemez (altın kural 3).
Pencerenin dışındaysa F1b'de hiçbir yerde görünmez: çapa ve kâğıt çapası yalnız zincir başını
görür, zincirin tam doğrulamasının üretim yolu Denetleme Kurulu modülüyle gelir (F3/F4, plan).
Geri yükleme yollarında (geri yükleme yetkisi ve özet onarımının çapası) kenara alınan
veritabanının zinciri hiç doğrulanmaz; bu varyant orada pencere içinde de görünmez, görünürlüğü
yalnız geri yükleme kartı ve onarım satırlarıdır (çapa kolunu `ozet_onarimi`'nin sıra kuralı
kapatır; geri yükleme yetkisinde, askıya alınmış ya da kapatılmış bir program yöneticisinin geri
sarılmış satırıyla, kalan risktir). Bu bölümü girişte sert engele çevirmek kullanıcı kararını
bekler. DENETİM İLE YAZIM ARASINDAKİ YARIŞ: satırın izi denetlendikten sonra, yazım işleminden
önce satırı değiştiren bir betik (ör. girişin `GIRIS` yazımı satırın o anki hâlinin içerik MAC'ini
yazar) kod ve zamanlama ister; başarısız denemeler `BUTUNLUK` satırı bırakır (tehdit 6/19 çıtası).
Denetimin kendi iki okuması (çağıranın ORM okuması ve iz okuması) beklenen mühürle aynı hâle
bağlıdır ("SATIRIN İZİ"). (c) GERİ YÜKLEME — özet onarımı (`backup_restore` modül başlığı "ÖZET
ONARIMI", `ozet_onarimi`) çapası kullanılamadığında (güncel veritabanı okunamıyor, çapa bayat, ya
da hesabın çapadaki satırının mührü, izi ya da sırası tutmuyor) geri yüklenen satırın özetlerini
ancak güncel `guvenlik.json`'daki sarmal onlardan birini tutuyorsa bırakır, tutmuyorsa boşaltır
(K-a, fail-closed). KALAN: geri yüklemeden ÖNCE `guvenlik.json`'a konmuş yedek günü sarmalı (o
günün parolasını bilen biri, çapayı okunamaz kılıp ya da bir satırın mührünü bozup) geri yüklenen
satırın özetini tutar ve o günün parolasıyla açar; geri yüklemeden SONRA arşivden geri konan yedek
günü sarmalı açmaz. Kapatılmış hesap da bu yoldan döner: kapanıştan önce saklanmış sarmal geri
yüklemeden ÖNCE dosyaya konur ve çapa kullanılamaz kılınırsa (dosyayı kaldırmak ya da o satırın
mührünü bozmak tek bir yazımdır), kapanıştan önceki yedekle hesap `ACIK` olarak eski parolayla
açılır ("çapada `KAPALI` → boşalt" kuralı yalnız kullanılabilen çapada işler). Çapayı okunamaz
kılmak kod istemez; görünürlüğü geri yükleme kartı ve onarımın `SISTEM` `HESAP` satırlarıdır. (d)
Parola sıfırlaması, yalnız `guvenlik.json`'a yazabilen birine karşı eski parolayı ve eski parola
kaydını hemen geçersiz kılar; satırı geri sarılmış hesabı AKLAMAZ (izi tutmayan satır
sıfırlanmaz: `AccountRecordStale`); (b)'nin ve (c)'nin kalan hâllerine karşı kılmaz. DEK
yenilemesi (TK12, F4) eski yedekleri açan sarmalları yine kapatmaz.

SATIRIN İZİ (kullanıcı kararı 03.11.2026 "Girişte reddet"; `services.satir_izi` modül başlığı).
Mühür satırın bir zamanlar program tarafından yazıldığını kanıtlar, BUGÜNKÜ hâli olduğunu
kanıtlamaz. Hesap satırı bu yüzden denetim izindeki SON içerik MAC'li kaydını da tutmalıdır
(tasarım §4.6.2 "içerik MAC'i"; `denetim_izi.hesap_izi_tutuyor` → ORM'siz tek karar işlevi
`satir_izi.hesap_izi_tutuyor`): hesabın iz satırları en yeniden geriye okunur, okunan her satırın
sırası tamsayı türünde ve kendi zincir MAC'i (açık kip, `key_ref`'teki yürürlükteki İA) tutmalıdır,
ilk içerik MAC'li satırın `record_mac`'i satırın bugünkü alanlarından hesaplanana eşit olmalıdır;
içerik MAC'li satır hiç yoksa satır tutmaz (fail-closed; meşru hiçbir hâl böyle doğmaz — her hesap
`HESAP` satırıyla açılır). Satır, iz anahtarları ve iz satırları tek anlık görüntüde okunur;
çağıranın ORM'le okuduğu mühür beklenen mühürdür (ham okumadaki mühür ona eşit olmalı: izi
doğrulanan hâl kararın verildiği hâldir). İlk denetim tutmazsa yanlış alarm ayıklanır
(`_yaristan_sonraki_satir`): arada meşru bir yazım satırı değiştirdiyse denetim yazıcılarla sıralı
bir işlemde yinelenir, doğrulanan GÜNCEL satır döner ve kararlar ondan verilir. Tutmazsa
MÜHÜR UYUŞMAZLIĞIYLA AYNI muamele: işlem reddedilir (`AccountRecordStale`, `AccountSealMismatch`'in
alt sınıfı, 409 `hesap_muhru_tutmadi`, mühür iletisi), `BUTUNLUK` satırı düşer (`SISTEM`, alan
`kayit_mac`; `_muhur_bozuk_izi`), satıra dokunulmaz, hatalı deneme sayacı ve gecikme yok. Denetim
noktaları mühür denetiminin olduğu her yerdir: kilit açılışı (`_open_account_for_login`: parmak
izi → satır → mühür → iz anahtarı → SATIRIN İZİ → özet → durum; sıranın gerekçesi orada),
kurtarma anahtarıyla açılış, oturumdaki parola doğrulaması ve parola değiştirme (`_sealed_account`),
hesap servisleri (işlemi yapan ve işlem gören; `hesaplar` modül başlığı), iki depo karşılaştırması
(izi tutmayan satır `seal_mismatch`'tedir, hiçbir işleme girmez), kapalı hesap sarmalının temizliği
(izi tutmayan `KAPALI` satır sarmal sildiremez) ve geri yüklemenin parola yolu
(`geri_yukleme_yetkisi`, `RET_KAYIT_IZI`). Reddedilen hesabın ÇIKIŞI yedekten geri yüklemedir
(zarfın üçüncü durumu): parola sıfırlaması, askıdan çıkarma ve kapama izi tutmayan satıra
dokunmaz; tek hesaplı roldeki (ör. muhasip) satır `KAPALI` olmadığı için o role yeni hesap da
açılamaz. Kurtarma anahtarıyla geri yükleme rol ve satır izi denetlemez.

YANLIŞ ALARM YOK: her meşru `Account` yazımı aynı işlemde satırın SON hâlinin içerik MAC'ini taşıyan
iz satırını yazar — ilk hesap ve hesap açma `HESAP`, kilit açılışı `GIRIS` (son giriş anı, özet
terfisi ve temizliği aynı yazımda), yenileme ve parola değiştirme `PAROLA`, kurtarma `KURTARMA`,
iki aşamalı özetin 1. adımı ve sıfırlamanın 2. adımı `HESAP` (`write_wrap_digests`), sıfırlama
`PAROLA`, kapama, askıdan çıkarma ve iki depo düzeltmesi `HESAP`, bildirimin kapanması `GUNCELLE`,
geri yüklemenin özet onarımı ORM'siz `SISTEM` `HESAP` (`satir_izi.hesap_satirlarini_izle`). Kilitli
kip satırları (`YEDEK`, `GOC`, `GUN_ISI`, `BUTUNLUK`) `Account` yazmaz. İçerik MAC'ine giren alan
kümesini (`Account.IZ_OZET_ALANLARI` = `satir_izi.HESAP_OZET_ALANLARI`, altın liste) ya da var olan
satırların bu alanlardaki değerini değiştiren her değişiklik (F4'ün DEK yenilemesi dahil) `KAPALI`
olanlar DAHİL BÜTÜN hesap satırlarının izini aynı işlemde yeniden kurmalıdır — her satırı önce eski
hâliyle son kaydına karşı doğrulayıp yalnız tutanlara (`satir_izi.HESAP_OZET_ALANLARI` yorumu);
yoksa açık satırların girişi reddedilir, `KAPALI` satırlar iki depo kartında yanlış alarm verir ve
sarmallarının temizliği durur. Bu adımın bugün yeri yoktur (kullanıcı kararı bekler; `denetim_izi`
modül başlığı "ÖZET ALANLARI VE ŞEMA DEĞİŞİMİ"). Eşzamanlı meşru yazım da alarm doğurmaz:
denetimin okumaları tek anlık görüntüdedir ve ayıklama yazıcılarla sıralı işlemde yinelenir
("SATIRIN İZİ").

İKİ DEPO KURALI (tasarım §4.6.1; `guvenlik.json` ↔ `Account`):

1. **Giriş** (`unlock`): yalnız seçilen hesabın sarmalı denenir (Argon2id bir kez;
   süre hesap sayısıyla büyümez). Sarmal açılınca, DEK belleğe ALINMADAN önce:
   parmak izi bu veritabanınınki mi, `Account` satırı var mı, mührü tutuyor mu, iz
   anahtarı (İA) bu DEK'le çözülüyor mu, satır denetim izindeki son içerik MAC'li kaydını
   tutuyor mu ("SATIRIN İZİ"), açılan sarmalın özeti satırın asıl ya da bekleyen özetini
   tutuyor mu ("SARMALIN TAZELİĞİ"), durumu `ACIK` ya da `PAROLA_YENILENMELI` mi.
   Biri tutmazsa giriş reddedilir ve satıra DOKUNULMAZ (mühür
   tutmazsa yeniden mühürlemek değiştirilmiş rolü meşrulaştırırdı; tehdit 19).
   Ret kodları (`UnlockRefused.code`; kullanıcı metnine çıkmaz): `parola_yanlis`,
   `hesap_askida`, `hesap_muhru_tutmadi`, `iki_depo_tutarsiz`; geçici ya da 180
   günü dolmuş parolada 409 `parola_yenilenmeli` — kilit açma yeni parolayı
   birlikte ister, oturum yeni parolayla açılır.
2. **Açma** (`hesaplar.open_account`): önce veritabanı (`PAROLA_YENILENMELI`, yeni
   sarmalın özeti, mühür), sonra sarmal. Arada kesilirse satır sarmalsız kalır; giriş zaten
   açılmaz, program yöneticisi yeniden geçici parola verir.
3. **Kapama** (`hesaplar.close_account`): önce veritabanı (`KAPALI`, mühür), sonra
   sarmal `guvenlik.json`'dan VE bütün `guvenlik-arsiv-*` kopyalarından silinir
   (TK11). Dosya adımı yarıda kalırsa her kilit açılışında koşan temizlik siler;
   adayları ana dosyayla birlikte bütün arşivlerden toplar (sarmal yalnız arşivde
   kalmış olabilir) ve kesilmiş yazımların `.tmp` artıklarını da siler. Temizlik
   YALNIZ mührü ve izi (denetim izindeki son içerik MAC'li kaydı) tutan `KAPALI` satır
   için koşar: veritabanında durumu program dışından `KAPALI`'ya çevrilmiş satır, meşru
   bir sarmalı sildiremez.
4. **Geri yüklemeden sonra** (`hesaplar.reconcile_two_stores`): fark listelenir;
   sarmalı olmayan açık hesap `PAROLA_YENILENMELI` olur; satırı olmayan ya da
   satırı `KAPALI` olan sarmal yalnız program yöneticisinin onayıyla silinir. Sarmalının
   özeti satırınkini tutmayan hesap (geri yüklemenin özet onarımının özetini boşalttığı ve
   sarmalı dosyada duran hesap dahil; sarmalı yoksa sarmalsız listededir) ayrı listede
   görünür (`digest_mismatch`); çaresi program yöneticisinin parola sıfırlamasıdır (sıfırlama
   özeti yeniden yazar), program yöneticisinin kendi hesabıysa kurtarma anahtarıyla açılış.

**İlk hesap (`enable`) 2. maddeden bilinçli olarak ayrılır** (plan F1b-1): önce
dosya (`gecis: "KURULUM"`), sonra TEK veritabanı işlemi (`Account`, `AuditKey`,
parmak izi), sonra `gecis` kalkar. Ters sıra, dosya yazılmadan kesilirse DEK'i yok
ederdi. Kesinti hâli yarım kurulumdur (`resolve_interrupted_setup`): dosya
`KURULUM` damgalı, parmak izi boş, kişi ve hesap tabloları boş → dosya arşivlenir,
program kuruluma döner (korunacak veri yoktur). Parmak izi doluysa işlem
tamamlanmıştır, yalnız damga kalkar. Damga şartı plan cümlesine eklendi: damgasız
bir dosyanın yanında boş veritabanı (veritabanı silinip yeniden oluşmuş) yarım
kurulum değildir; o dosya hesap parolasıyla yedekten geri yüklemenin (aynı bilgisayar
yolu) anahtarıdır ve arşivlenmez.

HATALI DENEME (tasarım TK15, §15 M-12; plan F1b-1): sayaç hesap başınadır ve
dosyada (`hatali`) durur; DEK istemez, kilitliyken yazılır. Gecikme sayaçtan türer
(0/0/1/2/4 sn, sonra 4). Organ ve müdür hesabında 10. hatada `askida`; program
yöneticisinde askı yoktur (kendi kendine hizmet reddi olurdu; kurtarma anahtarı yolu
kalır). Başarılı giriş, askıdan çıkarma ve parola sıfırlama sayacı sıfırlar.
Kurtarma anahtarı ve geri yükleme denemelerinin gecikmesi hesapsız ve süreç içidir
(aile).

ARŞİV (plan F1b-1): `guvenlik-arsiv-<damga>.json` kopyası YALNIZ yapıyı değiştiren
yazımdan önce alınır — hesap ekleme ve silme, sarmal değişimi, kurtarma bölümünün
yenilenmesi. Hatalı deneme sayacının ve askının yazımı, kurtarma anahtarının
saklandı damgası ve kurulum damgasının kalkması arşivlenmez (her yanlış parola bir
arşiv doğururdu). Kapanan hesabın sarmalı bütün arşivlerden de silinir.

FAIL-CLOSED DURUM SORGUSU (§4.3 tehdit 8): "hesap kurulu mu?" sorusunun cevabı
güvenlik dosyasının VARLIĞI **ya da** DB'deki anahtar parmak izidir. Kilitliyken
`guvenlik.json` silinir ya da yeniden adlandırılırsa program kuruluma dönmez:
parmak izi dolu + dosya yok = **güvenlik dosyası kayıp** kilidi
(`security_file_missing`). Dosya bozulur ya da şema 1 kalırsa da aynı kilide
düşülür (kural tektir: `desktop.backup_crypto.is_usable_security_state`). Bu
durumda yalnız durum uçları ve yedekten geri yükleme açıktır (`lock_middleware`).
Tek istisna: dosya kullanılamıyor AMA parmak izi boş ve şifreli alan taşıyan bütün
tablolar boşsa korunacak veri yoktur; "güvenlik dosyasını sıfırla ve kuruluma dön"
yolu dosyayı arşivleyip ilk açılış hâline döner (`state_reset_available`).

KURTARMA ANAHTARI (tasarım §4.4.3-§4.4.4, §9.7): anahtar sunucuda saklanmaz, hiçbir
günlüğe ve hata iletisine yazılmaz. `kurtarma.no` her yeni anahtarda (yenilemede de)
bir artar, `tarih` üretim günüdür: belge ve yedek başlığı hangi kâğıdın hangi
yedeği açtığını gösterir (TK10). Yalnız program yöneticisi yeniler. Kurtarma
anahtarıyla açılış yalnız VAR OLAN bir program yöneticisi hesabının parolasını
yeniler (yeni yönetici açan kol F4'te, DEK yenilemesiyle); sarmalı yoksa (kurtarma
anahtarıyla geri yüklemeden sonra) sarmalı yeniden kurar. O durumda kilit ekranı
listesi boştur (liste sarmallardan çıkar): hesap kilitliyken açık kurtarma
listesinden (`GET security/recover/`, `hesaplar.recovery_accounts`) ya da
tanıtıcısıyla seçilir (`unlock_with_recovery` kimliği de tanıtıcıyı da alır).
Sahibine ilk girişte "parolanız … tarihinde kurtarma anahtarıyla yenilendi"
bildirimi düşer (`reset_notice_pending`, `reset_kind`).

DENETİM İZİ (tasarım §4.6.2, §4.4.3; plan F1b-1 alt commit c). Her veritabanı yazımı
iz satırıyla AYNI işlemdedir (`apps.okul.denetim_izi`): ilk hesap `HESAP` + ilk kurtarma
anahtarı için `KURTARMA` (+ okul kartına yazılan parmak izi), kilit açılışı `GIRIS`
(geçici ya da süresi dolmuş parola o anda yenilendiyse önce `PAROLA`), kurtarma
anahtarıyla açılış `KURTARMA` + `GIRIS`, kendi parolasını değiştirme `PAROLA`, kurtarma
anahtarının yenilenmesi ve saklandığının doğrulanması `KURTARMA`; sarmalı değiştiren yazımların
iki aşamalı özeti ayrıca `HESAP` satırı yazar ("İKİ AŞAMALI ÖZET"). Bu satırlar o hesabındır:
ilk hesap, kilit açılışı ve
kurtarma oturum açılmadan yazılır, yazar açıkça verilir (`yazar_olarak`). Kilit
açılışında DEK ve İA önce belleğe alınır, satırlar yazılır, oturum SONRA açılır;
yazılamazsa anahtarlar düşer ve oturum açılmaz (iz yazılamazsa yazma yapılamaz). Girişte
hesap mührü, satırın izi ya da sarmal özeti tutmazsa olay `BUTUNLUK` satırı olarak düşer
(`SISTEM`; alan `seal`, `kayit_mac` ya da `wrap_digest`; DEK sarmaldan açıldığı için İA
çözülebilir), satıra dokunulmaz. Hatalı deneme sayacı ve askısı DEK
istemeden, kilitliyken dosyaya yazılır; o an iz yazılamaz (kilitli kip yalnız kişisiz
sistem olaylarını yazar, §4.6.3): askı `guvenlik.json`'da ve kilit ekranında görünür. İzi
KALDIRILIRKEN düşer: sayacı ya da askıyı silen her program yöneticisi işlemi (askıdan
çıkarma, parola sıfırlama, hesabın kapanması, sahipsiz sarmalın silinmesi) ve kapalı hesap
sarmalının temizliği, önceki değerleri `guvenlik.sarmal` bölümünün `HESAP` satırına yazar
(`sarmal_izi`; değer sıfırsa ve sarmal silinmiyorsa satır yok). Başarılı girişin sayacı
sıfırlaması bu kuralın dışındadır: girişin izi `GIRIS` satırıdır.
`guvenlik.json`'u değiştiren ve iz yazan işlemlerde sıra hep aynıdır: önce dosya kilidi,
sonra veritabanı işlemi (`dosya_ve_iz_islemi`); iz satırı dosya yazımından önce eklenir,
dosya yazılamazsa işlem geri sarılır. Kilit açılışında, hesap bütünlüğü denetimlerinden
SONRA, denetim izi kendiliğinden doğrulanır (çapa, kilitli satırlar, son 200 satır; geri
yükleme notu; tasarım §4.6.3) — bulgular `BUTUNLUK` satırı ve kart olur, girişi engellemez
(`apps.okul.iz_dogrulama`, `_start_session`).

Güvenlik dosyasını değiştiren işlemler süreç içi bir kilitle sıralanır: oku-
değiştir-yaz arasına başka bir yazım girip onu ezmesin.

NEDEN GÜVENLİK DOSYASI VERİ DİZİNİNDE, DB'DE DEĞİL?
  * Yedekler (`backups/gunluk-*.odbak`) X25519 + AES-256-GCM kapsayıcılarıdır;
    başlıkları yalnız kurtarma bölümünü taşır (TK10), hesap sarmalı taşımaz.
  * DB'de yalnız anahtarın PARMAK İZİ ve hesapların mührü durur; yanlış eşleşme
    (başka kurulumun güvenlik dosyası) sessizce bozuk çözme yerine açık ret üretir.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import secrets
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any, TypeVar

from desktop.backup import database_snapshot
from desktop.backup_crypto import (
    BACKUP_SUFFIX,
    SECURITY_STATE_VERSION,
    BackupCryptoError,
    config_path,
    encrypt_to_path,
    ensure_public_config,
    is_usable_security_state,
    load_public_key,
    parse_security_state,
    recovery_key_identity,
    recovery_metadata,
)
from django.apps import apps as django_apps
from django.conf import settings
from django.db import DatabaseError, connection, models, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.okul import denetim_izi, iz_dogrulama, masaustu_kanca, rol_izinleri
from apps.okul.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditAction,
    AuditKey,
    Personnel,
    ResetKind,
    SchoolConfig,
    Student,
)
from apps.okul.oturum import (
    IZ_KIP_KILIDI,
    OTURUM,
    OturumHesabi,
    Yazar,
    sistem_olarak,
    yazar_olarak,
)
from apps.okul.services import hesap_kurallari
from shared import crypto, kanonik
from shared.exceptions import PASSWORD_REQUIRED_MESSAGE, RolYetkisiz
from shared.text import tr_lower

logger = logging.getLogger("oab_defteri.guvenlik")

# --- Dosya/dizin çözümü -----------------------------------------------------
STATE_FILE_NAME = "guvenlik.json"
# Testler ve taşınabilir kip için: verilirse güvenlik dosyasının/yedeklerin yeri.
ENV_SECURITY_DIR = "OD_SECURITY_DIR"
ENV_BACKUP_DIR = "OD_BACKUP_DIR"

#: Dosya şeması (tasarım §2.3.1). Tek kaynak masaüstü katmanıdır (kullanılabilirlik kuralı).
STATE_VERSION = SECURITY_STATE_VERSION

#: Kurulum geçişi damgası (`gecis`). Geçiş yokken alan `null`dır; F4'te DEK
#: yenilemesi nesne biçimli bir geçiş (`{"tur": "DEK_YENILEME", …}`) yazar.
TRANSITION_SETUP = "KURULUM"

#: Organ ve müdür hesabını askıya alan ardışık hatalı deneme sayısı (§15 M-12).
SUSPEND_AFTER_FAILURES = 10

#: Kurtarma bölümündeki doğrulama damgası (ISO zaman damgası; tasarım §4.4.4
#: `kurtarma.dogrulandi`). Sarmalla birlikte yaşar: yenilenen kurtarma bölümü
#: damgasız yazılır.
RECOVERY_CONFIRMED_FIELD = "dogrulandi"
#: Kenara alınan güvenlik dosyalarının ad öneki (`guvenlik-arsiv-<damga>.json`);
#: geri yükleme (`backup_restore._ensure_state_file`) ve `recovery_metadata`
#: aynı deseni kullanır.
STATE_ARCHIVE_PREFIX = "guvenlik-arsiv-"

#: Hesap sarmalının türetim etiketi (modül başlığı "HESAP SARMALI KİMLİĞE BAĞLIDIR"). YALNIZ
#: RET İÇİNDİR: değeri tutmayan sarmal açılmadan reddedilir; tutan sarmal yine tek türetimle
#: (`crypto.account_wrapping_key`) açılır. Etiket türetimi SEÇMEZ.
WRAP_DERIVATION_FIELD = "turetim"
WRAP_DERIVATION = crypto.ACCOUNT_WRAP_INFO.decode("ascii")

# Güvenlik dosyasını oku-değiştir-yaz işlemlerinin süreç içi sırası (modül başlığı).
_state_lock = threading.RLock()


@contextmanager
def dosya_ve_iz_islemi() -> Iterator[None]:
    """`guvenlik.json` yazımı ile iz satırı birlikte: önce dosya kilidi, sonra veritabanı işlemi.

    Sıra her yerde aynıdır (kilitlenme olmasın): dosya kilidini tutan iş veritabanının
    yazma kilidini bekleyebilir, tersi olmaz. İçeride iz satırı dosya yazımından ÖNCE
    eklenir; dosya yazımı hata verirse işlem geri sarılır, iz yapılmamış işi anlatmaz.
    """
    with _state_lock, transaction.atomic():
        yield


def sarmal_izi(hesap_id: object, *, silindi: bool = False, her_zaman: bool = False) -> bool:
    """Sarmalın hatalı deneme sayacı ve askısı kalkarken `guvenlik.sarmal` `HESAP` satırı.

    Sayaç ve askı kilitliyken, izsiz yazılır (modül başlığı "DENETİM İZİ"); izleri kalkarken
    düşer. Önceki değerler `values`'a girer: sıfırlanırken `[önceki, 0 | false]`, sarmal
    silinirken `[önceki, null]` ve alan adlarının başında `sarmal`. Değerler sıfırsa satır
    yazılmaz; `her_zaman` doğruysa (silmenin kendisi olaydır: kapalı hesap sarmalının
    temizliği, sahipsiz sarmal) yine yazılır. Yazar çağıranın bağlamıdır. Çağıranın işleminde,
    `_state_lock` altında ve dosya yazımından ÖNCE çağrılır (`dosya_ve_iz_islemi`). Satır
    yazıldıysa True.
    """
    hatali, askida = wrap_failure_state(hesap_id)
    sonra: tuple[int | None, bool | None] = (None, None) if silindi else (0, False)
    degisen = {
        ad: [once, yeni]
        for ad, once, yeni in (("hatali", hatali, sonra[0]), ("askida", askida, sonra[1]))
        if once
    }
    if not degisen and not her_zaman:
        return False
    denetim_izi.olay(
        AuditAction.HESAP,
        model=denetim_izi.HESAP_SARMALI,
        object_id=str(hesap_id),
        changed_fields=(["sarmal"] if silindi else []) + list(degisen),
        values=degisen,
    )
    return True


# Kurtarma anahtarı: 20 rastgele bayt → base32 (32 karakter) → 8 dörtlü grup.
RECOVERY_KEY_BYTES = 20
RECOVERY_GROUP_SIZE = 4
# Base32 alfabesinde 0/1/8/9 yoktur; elle yazımda en sık karışan ikili düzeltilir.
_RECOVERY_FIXUPS = str.maketrans({"0": "O", "1": "I", "8": "B"})
#: Türkçe klavyede büyük harfle yazılan "i" noktalı "İ" (U+0130) olur ve Python'un
#: `upper()`'ı onu "I"ya çevirmez; noktasız "ı" da güvence için eşlenir. Anahtar
#: alfabesi ASCII'dir (A-Z, 2-7): ikisi de "I"dır. Ön yüz aynı eşlemeyi uygular
#: (`frontend/src/modules/guvenlik/kurtarma.ts`).
_RECOVERY_TURKISH_I = str.maketrans({"İ": "I", "ı": "I"})

#: İz anahtarının (İA) uzunluğu; DEK'ten türemez, kurulumda ayrı üretilir (§4.6.3). Tek
#: kaynak denetim izi yazıcısıdır (çözülen anahtarın uzunluğunu o denetler).
AUDIT_KEY_BYTES = denetim_izi.IZ_ANAHTARI_BAYT

# Art arda yanlış denemede uygulanan gecikme (saniye). Son değer tavandır. Hesap
# başına sayaç `guvenlik.json`'dadır; kurtarma ve geri yükleme denemeleri süreç
# içi sayacı (`_failed_attempts`) kullanır (aile).
FAILURE_DELAYS: tuple[float, ...] = (0.0, 0.0, 1.0, 2.0, 4.0)
_failed_attempts = 0

# Kullanıcıya görünen iletiler (sözlük: "parola", "hesap", "program yöneticisi";
# iç kod yok). `PASSWORD_REQUIRED_MESSAGE`'ın tek kaynağı `shared.exceptions`'tır.
SECURITY_FILE_MISSING_MESSAGE = (
    "Güvenlik dosyası (guvenlik.json) bulunamadı ya da okunamıyor. Kayıtlar açılamaz. "
    "Dosyanın sağlam bir kopyasını veri klasörüne geri koyun ya da bir yedekten geri yükleyin."
)
_NOT_SET_MESSAGE = "Program yöneticisi hesabı henüz kurulmadı."
_WRONG_PASSWORD_MESSAGE = "Parola hatalı."  # noqa: S105 — kullanıcı iletisi, parola değil
_WRONG_RECOVERY_MESSAGE = (
    "Kurtarma anahtarı hatalı. Yazdırdığınız kâğıttaki anahtarı olduğu gibi girin."
)
_LOCKED_MESSAGE = "Kayıtlar kilitli. Önce hesabınızla kilidi açın."
_SUSPENDED_MESSAGE = "Hesap askıda — program yöneticisine başvurun."
_SUSPENDED_NOW_MESSAGE = (
    "Parola hatalı. Art arda yanlış parola girildiği için hesap askıya alındı — program "  # noqa: S105
    "yöneticisine başvurun."
)
_RENEWAL_REQUIRED_MESSAGE = (
    "Parolanızı yenilemeniz gerekiyor (geçici parola ya da süresi dolan parola). "
    "Yeni parolanızı belirleyin."
)
_SAME_PASSWORD_MESSAGE = "Yeni parola eskisiyle aynı olamaz."  # noqa: S105
_NO_WRAP_MESSAGE = (
    "Bu hesabın parolası bu bilgisayarın güvenlik dosyasında yok. Program yöneticisine "  # noqa: S105
    "başvurun."
)
#: Program dışından değiştirilmiş görünen parola kaydı (sözlük §1 "Hesap"): bağsız sarmal
#: (`turetim` yok; `UnboundWrap`) ve özeti mühürlü satırınkini tutmayan sarmal
#: (`WrapDigestMismatch`) AYNI iletiyi verir. Program böyle kayıt yazmaz; sahada yalnız program
#: dışı değişiklikle (eski sarmalın geri konması dahil) doğar. Çıkış zarfın üçüncü durumudur
#: (kullanıcı kararı 03.11.2026): program yöneticisinin hesabı kilit ekranının "Parolamı
#: unuttum" yolundan kurtarma anahtarıyla açılır (ya da başka bir program yöneticisi sıfırlar),
#: öteki hesapların parolasını program yöneticisi sıfırlar; Denetleme Kuruluna bildirilir.
UNBOUND_WRAP_MESSAGE = (
    "Bu hesabın parola kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. "
    "Denetleme Kuruluna bildirin. Program yöneticisinin hesabıysa “Parolamı unuttum” yolundan "
    "kurtarma anahtarıyla açılır; öteki hesapların parolasını program yöneticisi sıfırlar."
)
#: Özeti tutmayan sarmalın iletisi bağsız sarmalınkidir (yukarıdaki not).
WRAP_DIGEST_MISMATCH_MESSAGE = UNBOUND_WRAP_MESSAGE
_NO_ROW_MESSAGE = (
    "Hesap kaydı bu veritabanında bulunamadı ya da hesap açık değil. Program "
    "yöneticisine başvurun."
)
_SEAL_MISMATCH_MESSAGE = (
    "Hesap kaydı program dışından değiştirilmiş görünüyor; giriş açılmadı. Program "
    "yöneticisine ve Denetleme Kuruluna bildirin."
)
_FOREIGN_DB_MESSAGE = (
    "Bu güvenlik dosyası bu veritabanına ait değil (anahtar eşleşmiyor). Doğru "
    "guvenlik.json dosyasını veri klasörüne koyup yeniden deneyin ya da bir yedekten geri "
    "yükleyin."
)
_AUDIT_KEY_MESSAGE = (
    "Kayıtların iz anahtarı bu veritabanında okunamadı; iz yazılamayacağı için giriş "
    "açılmadı. Bir yedekten geri yükleyin."
)
_SESSION_ONLY_MESSAGE = "Parola yalnız oturumdaki hesap için doğrulanır."  # noqa: S105
_SESSION_UNKNOWN_MESSAGE = "Oturumdaki hesap bilinmiyor. Kilitleyip hesabınızla yeniden açın."
_RECOVERY_ONLY_ADMIN_MESSAGE = (
    "Kurtarma anahtarıyla yalnız var olan bir program yöneticisi hesabının parolası yenilenir."
)
#: Düzenli kapanış başladıktan sonra gelen kilit açılışı (`ProgramClosing`; sözlük §4.2).
PROGRAM_CLOSING_MESSAGE = "Program kapanıyor; kilit açılmadı."
RESET_NOT_ALLOWED_MESSAGE = (
    "Güvenlik dosyası sıfırlanamaz: bu yol yalnız hiç kişi kaydı girilmemiş ve kayıtların "
    "anahtarı henüz veritabanına işlenmemiş bir kurulumda, güvenlik dosyası okunamıyorken "
    "açıktır. Dosyanın sağlam bir kopyasını veri klasörüne geri koyun ya da bir yedekten "
    "geri yükleyin."
)


class AppPasswordError(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata (view katmanı 400'e çevirir)."""


class UnlockRefused(AppPasswordError):
    """Kilit açma (ya da parola doğrulama) reddi; `code` arayüzün ayırdığı sözleşme kodudur.

    Kod kullanıcı metnine çıkmaz (sözlük §2); ileti Türkçedir. `status_code` görünüm
    katmanının HTTP karşılığıdır.
    """

    code = "parola_yanlis"
    status_code = 400


class WrongPassword(UnlockRefused):
    """Parola sarmalı açmadı (ya da açılan DEK bellekteki anahtar değil)."""

    code = "parola_yanlis"
    status_code = 400


class AccountSuspended(UnlockRefused):
    """Hesap askıda: hatalı deneme askısı (`guvenlik.json`) ya da `Account.status = ASKIDA`."""

    code = "hesap_askida"
    status_code = 403


class AccountSealMismatch(UnlockRefused):
    """`Account` satırının mührü tutmadı; satıra dokunulmaz (tasarım §4.6.1, tehdit 19)."""

    code = "hesap_muhru_tutmadi"
    status_code = 409


class WrapDigestMismatch(AccountSealMismatch):
    """Açılan sarmalın özeti mühürlü satırın asıl ya da bekleyen özetini tutmadı (modül başlığı
    "SARMALIN TAZELİĞİ"): eski ya da program dışından konmuş parola kaydı.

    Mühür uyuşmazlığının alt sınıfıdır ve kodunu taşır (409 `hesap_muhru_tutmadi`; plan F1b-1'in
    kod listesine yeni kod eklenmez). Gerekçe: ikisi de aynı aşamada (DEK sarmaldan açıldıktan,
    parmak izi ve satır doğrulandıktan sonra) mühürlü satırın söylediğiyle çelişen bir kaydı yakalar
    ve aynı yan etkiyi taşır — `BUTUNLUK` satırı (`_muhur_bozuk_izi`), satıra dokunulmaz, hatalı
    deneme sayacı ve gecikme yok. Bağsız sarmalın (`UnboundWrap`) koduna (`iki_depo_tutarsiz`)
    bağlanmadı: o ret DEK açılmadan, iz yazılmadan verilir. İleti ikisinde aynıdır
    (`WRAP_DIGEST_MISMATCH_MESSAGE`); ön yüz kodla davranış seçmez, iletiyi yazar.
    """

    code = "hesap_muhru_tutmadi"
    status_code = 409


class AccountRecordStale(AccountSealMismatch):
    """Hesap satırı denetim izindeki son içerik MAC'li kaydını tutmadı (kullanıcı kararı 03.11.2026
    "Girişte reddet"; modül başlığı "SATIRIN İZİ", `satir_izi`): mührü tutan ama eski bir
    kopyadan geri konmuş (ya da izi program dışından değiştirilmiş) satır.

    Mühür uyuşmazlığının alt sınıfıdır ve kodunu, durumunu ve iletisini taşır (409
    `hesap_muhru_tutmadi`; `_SEAL_MISMATCH_MESSAGE`, hesap servislerinde onların iletisi): kullanıcı
    kararı onu mühür uyuşmazlığıyla AYNI muameleye bağlar — işlem reddedilir, `BUTUNLUK` satırı
    düşer (`_muhur_bozuk_izi`, alan adı `kayit_mac`), satıra dokunulmaz, hatalı deneme sayacı ve
    gecikme yok. Ayrı sınıf yalnız günlüğün, testin ve kartın ayırt etmesi içindir; plan F1b-1'in
    kod listesine yeni kod eklenmez.
    """

    code = "hesap_muhru_tutmadi"
    status_code = 409


class TwoStoreMismatch(UnlockRefused):
    """`guvenlik.json` ile veritabanı tutarsız (satır yok, kapalı, başka veritabanı)."""

    code = "iki_depo_tutarsiz"
    status_code = 409


class AuditKeyUnreadable(TwoStoreMismatch):
    """İz anahtarı bu DEK'le çözülemedi: iz yazılamaz, giriş açılmaz (hesap bütünlüğü).

    Plan F1b-1'in kod listesinde ayrı kod yoktur: iz anahtarı veritabanının DEK'e
    bağlı parçasıdır, ret `iki_depo_tutarsiz` koduyla döner.
    """


class UnboundWrap(TwoStoreMismatch):
    """Sarmal kimliğe bağlı türetim etiketini taşımıyor (`turetim` yok): parolayla açılmaz.

    Program bağsız sarmal yazmaz: böyle sarmal ya bağdan önceki deneme kurulumundandır (plan
    F1b-1 "Eski veri": silinip yeniden kurulur) ya da etiketi program dışından silinmiştir.
    İleti bu yüzden program dışı değişikliği anar ve bildirim ister (`UNBOUND_WRAP_MESSAGE`).
    Plan F1b-1'in kod listesine yeni kod eklenmez: ret `iki_depo_tutarsiz` (409) koduyla ve
    kendi iletisiyle döner (ön yüz iletiyi yazar). Argon2id koşmaz, hatalı deneme sayacına
    dokunulmaz: yanıt paroladan bağımsızdır, deneme sayılacak bir şey yoktur. Ret DEK
    açılmadan verilir; yanlış parola reddinde olduğu gibi denetim izine satır yazılmaz.
    """


class PasswordRenewalRequired(UnlockRefused):
    """Geçici ya da 180 günü dolmuş parola: kilit açma yeni parolayı birlikte ister (409)."""

    code = "parola_yenilenmeli"
    status_code = 409


class ProgramClosing(AppPasswordError):
    """Düzenli kapanış başladı: kilit açılışı hiçbir şey yazmadan reddedilir (`_start_session`)."""


class PasswordRequired(crypto.KeyMissingError):
    """İlk hesap kurulmadan kişi yazılmak istendi (409 `parola_gerekli`).

    `KeyMissingError`'ın alt sınıfıdır: hesap yoksa anahtar da yoktur ve
    `shared.exceptions.od_exception_handler` ikisini aynı 409 yanıtına çevirir.
    """

    def __init__(self, message: str = PASSWORD_REQUIRED_MESSAGE) -> None:
        super().__init__(message)


_T = TypeVar("_T")


def _kural(dogrulayici: Callable[[str], _T], deger: str) -> _T:
    """`hesap_kurallari` doğrulayıcısını çağırır; ihlali bu modülün hata türüne çevirir."""
    try:
        return dogrulayici(deger)
    except hesap_kurallari.AccountRuleError as exc:
        raise AppPasswordError(str(exc)) from exc


def validate_password(password: str) -> str:
    """Parola politikası (`hesap_kurallari.validate_password`); ihlalde `AppPasswordError`."""
    return _kural(hesap_kurallari.validate_password, password)


# ---------------------------------------------------------------------------
# Yol yardımcıları
# ---------------------------------------------------------------------------
def _data_dir() -> Path:
    return Path(os.environ.get(ENV_SECURITY_DIR) or settings.DATA_DIR)


def state_path() -> Path:
    """`guvenlik.json` yolu — veri dizininde, db.sqlite3'ün yanında."""
    return _data_dir() / STATE_FILE_NAME


def backup_dir() -> Path:
    """Yedek dizini. Paketlenmiş kipte `<veri kökü>/backups` (desktop/paths.py)."""
    override = os.environ.get(ENV_BACKUP_DIR)
    if override:
        return Path(override)
    # settings.DATA_DIR = <kök>/data → yedekler <kök>/backups (desktop/paths.py yerleşimi).
    return Path(settings.DATA_DIR).parent / "backups"


# ---------------------------------------------------------------------------
# Durum dosyası
# ---------------------------------------------------------------------------
def read_state() -> dict[str, Any] | None:
    """Güvenlik dosyasını okur; yoksa None. Bozuksa Türkçe hata yükseltir.

    Şema denetlenmez (yalnız JSON sözlük mü bakılır); kullanılabilirlik
    `_require_state` ve `security_file_missing`'in işidir.
    """
    path = state_path()
    if not path.is_file():
        return None
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        # Derin iç içe JSON (`[[[[…]]]]`) `json.loads`'ta `RecursionError` yükseltir; o da
        # bozuk dosyadır (aile kuralı: `desktop.backup_crypto.parse_security_state`). Yakalanmasaydı
        # veri dizinine konmuş tek bir zehirli `guvenlik.json` kilit ekranının hesap listesini
        # (`account_wraps`) ve kilit açılışını Türkçe ret yerine 500'e düşürürdü.
        raise AppPasswordError(
            "Güvenlik dosyası (guvenlik.json) okunamadı ya da bozuk. Dosyanın sağlam bir "
            "kopyasını veri klasörüne geri koyun ya da bir yedekten geri yükleyin; dosya "
            "olmadan şifreli alanlar açılamaz."
        ) from exc
    if not isinstance(data, dict):
        raise AppPasswordError("Güvenlik dosyası (guvenlik.json) beklenen biçimde değil.")
    return data


def _require_state() -> dict[str, Any]:
    """Kullanılabilir güvenlik dosyasını okur; yoksa kayıp mı hiç kurulmamış mı söyler."""
    state = read_state()
    if state is None:
        if _stored_fingerprint():
            raise AppPasswordError(SECURITY_FILE_MISSING_MESSAGE)
        raise AppPasswordError(_NOT_SET_MESSAGE)
    if not is_usable_security_state(state):
        # Şema 1 ya da bölümleri eksik dosya: kayıp kilidiyle aynı sınıf (tehdit 8).
        raise AppPasswordError(SECURITY_FILE_MISSING_MESSAGE)
    return state


def _write_state(data: dict[str, Any]) -> None:
    """Dosyayı ATOMİK yazar (önce .tmp, sonra yerine koy) — yarım dosya kalmaz."""
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _archive_target() -> Path:
    """Boş bir `guvenlik-arsiv-<damga>.json` yolu (aynı saniyede ikinci arşiv ezilmez)."""
    yol = state_path()
    damga = timezone.localtime().strftime("%Y-%m-%d-%H%M%S")
    arsiv = yol.with_name(f"{STATE_ARCHIVE_PREFIX}{damga}.json")
    sira = 2
    while arsiv.exists():
        arsiv = yol.with_name(f"{STATE_ARCHIVE_PREFIX}{damga}-{sira}.json")
        sira += 1
    return arsiv


def _copy_state_to_archive() -> Path:
    """Güncel güvenlik dosyasının baytlarını arşive KOPYALAR (asıl dosya yerinde kalır).

    Arşiv de atomik yazılır (.tmp → yerine koy): yarım arşiv dosyası kalmaz.
    """
    arsiv = _archive_target()
    temp = arsiv.with_name(arsiv.name + ".tmp")
    temp.write_bytes(state_path().read_bytes())
    temp.replace(arsiv)
    return arsiv


def _write_structural(data: dict[str, Any]) -> None:
    """Yapıyı değiştiren yazım: önce güncel dosyanın arşiv kopyası, sonra atomik yazım.

    Yapı: hesap ekleme ve silme, sarmal değişimi, kurtarma bölümünün yenilenmesi
    (plan F1b-1; modül başlığı ARŞİV). Dosya yoksa arşivlenecek bir şey yoktur.
    """
    if state_path().is_file():
        _copy_state_to_archive()
    _write_state(data)


def _archive_paths() -> list[Path]:
    """Veri dizinindeki `guvenlik-arsiv-*.json` kopyaları (ada göre sıralı)."""
    dizin = _data_dir()
    if not dizin.is_dir():
        return []
    return sorted(dizin.glob(f"{STATE_ARCHIVE_PREFIX}*.json"))


def _leftover_temp_paths() -> list[Path]:
    """Kesilmiş atomik yazımların artıkları: `guvenlik.json.tmp`, `guvenlik-arsiv-*.json.tmp`.

    Güvenlik dosyası ve arşivleri `_state_lock` altında yazılır (geri yüklemenin
    yazımı da; `backup_restore._ensure_state_file`). Kilit tutulurken diskte duran
    `.tmp` bu yüzden yarıda kalmış bir yazımdır: işlem hata vermiş, asıl dosya ve
    arşivler yerindedir. Artık sarmal taşıyabilir (kapanan hesabınki dahil) ve
    `*.json` desenine girmediği için arşiv temizliği onu görmezdi (TK11).
    """
    dizin = _data_dir()
    if not dizin.is_dir():
        return []
    return sorted(
        [*dizin.glob(f"{STATE_FILE_NAME}.tmp"), *dizin.glob(f"{STATE_ARCHIVE_PREFIX}*.json.tmp")]
    )


def _read_archive(arsiv: Path) -> dict[str, Any] | None:
    """Arşivi okur; sarmal listesi taşımıyorsa ya da okunamıyorsa None (uyarı günlüğe).

    Okunamama kümesi aileninkidir (`desktop.backup_crypto.parse_security_state`): geçersiz UTF-8
    (`UnicodeDecodeError`, bir `ValueError`), bozuk JSON ve derin iç içe JSON (`[[[[…]]]]`;
    `json.loads` `RecursionError` yükseltir). Yakalanmasaydı veri dizinine konmuş tek bir zehirli
    arşiv her kilit açılışını düşürür ve sarmal yazımından SONRA koşan kapalı hesap temizliğinde
    yeni parolanın satırlarını geri sarardı (bağımsız denetim bulgusu; `_cleanup_closed_wraps`).
    """
    try:
        veri: Any = json.loads(arsiv.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        logger.warning("Güvenlik arşivi okunamadı; sarmal temizliği atlandı: %s", arsiv.name)
        return None
    if not isinstance(veri, dict) or not isinstance(veri.get("hesaplar"), list):
        return None
    return veri


def _archived_wrap_ids() -> set[str]:
    """Bütün arşiv kopyalarındaki hesap sarmallarının kimlikleri (okunamayan arşiv atlanır)."""
    kimlikler: set[str] = set()
    for arsiv in _archive_paths():
        veri = _read_archive(arsiv)
        if veri is not None:
            kimlikler.update(str(h.get("id", "")) for h in _accounts_in(veri))
    return kimlikler


def _remove_leftover_temps() -> int:
    """Güvenlik dosyalarının `.tmp` artıklarını siler (`_leftover_temp_paths`); sayısını döndürür.

    Çağıran `_state_lock`'u tutar. İçerik ayrıştırılmaz: kesilmiş yazımın artığı
    yarım da olabilir; hangi sarmalı taşıdığı bilinemez, asıl dosya ve arşivler zaten
    yerindedir. Silinemeyen artık günlüğe düşer ve ilk `OSError` sonda yükseltilir.
    """
    silinen = 0
    hata: OSError | None = None
    for artik in _leftover_temp_paths():
        try:
            artik.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            logger.warning("Güvenlik dosyası artığı silinemedi: %s", artik.name)
            hata = hata or exc
            continue
        silinen += 1
    if silinen:
        logger.info("Güvenlik dosyasının yarım kalmış yazım artıkları silindi (%d).", silinen)
    if hata is not None:
        raise hata
    return silinen


def _remove_wraps_from_archives(hesap_idler: set[str]) -> int:
    """Verilen hesapların sarmallarını BÜTÜN arşiv kopyalarından siler (TK11).

    Fikirdeştir. Ayrıştırılamayan arşiv olduğu gibi bırakılır ve günlüğe uyarı
    düşer: içinde ne olduğu bilinmeyen dosyayı yeniden yazmak, onu kurtarma
    girişimine yarayacak tek kopyayı bozabilirdi. Yazımı düşen arşiv öteki
    arşivlerin temizliğini durdurmaz; ilk `OSError` hepsi denendikten sonra
    yükseltilir (kalanı kilit açılışındaki temizlik siler). Kesilmiş yazımların
    `.tmp` artıkları da silinir. Değişen arşiv sayısını döndürür.
    """
    degisen = 0
    hata: OSError | None = None
    for arsiv in _archive_paths():
        veri = _read_archive(arsiv)
        if veri is None:
            continue
        kalan = [
            h
            for h in veri["hesaplar"]
            if not (isinstance(h, dict) and str(h.get("id", "")) in hesap_idler)
        ]
        if len(kalan) == len(veri["hesaplar"]):
            continue
        veri["hesaplar"] = kalan
        temp = arsiv.with_name(arsiv.name + ".tmp")
        try:
            temp.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(arsiv)
        except OSError as exc:
            logger.warning("Güvenlik arşivinden sarmal silinemedi: %s", arsiv.name)
            hata = hata or exc
            continue
        degisen += 1
    try:
        _remove_leftover_temps()
    except OSError as exc:
        hata = hata or exc
    if hata is not None:
        raise hata
    return degisen


# ---------------------------------------------------------------------------
# Hesap sarmalları ve kurtarma bölümü
# ---------------------------------------------------------------------------
def _accounts_in(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Durumdaki hesap sarmalları (liste değilse ya da öğe sözlük değilse atlanır)."""
    hesaplar = state.get("hesaplar", [])
    if not isinstance(hesaplar, list):
        return []
    return [h for h in hesaplar if isinstance(h, dict)]


def _find_wrap(state: dict[str, Any], hesap_id: object) -> dict[str, Any] | None:
    """Kimliği verilen hesabın sarmalı (yoksa None)."""
    aranan = str(hesap_id)
    for hesap in _accounts_in(state):
        if str(hesap.get("id", "")) == aranan:
            return hesap
    return None


def _find_wrap_by_login_name(state: dict[str, Any], tanitici: str) -> dict[str, Any] | None:
    """Tanıtıcısı ya da kimliği verilen sarmal (konsol geri yüklemesinin `--hesap`'ı)."""
    aranan = tanitici.strip()
    for hesap in _accounts_in(state):
        if aranan and aranan in (str(hesap.get("tanitici", "")), str(hesap.get("id", ""))):
            return hesap
    return None


@sensitive_variables("password", "data_key")
def _account_wrap(
    data_key: bytes, *, hesap_id: object, tanitici: str, password: str, kdf: crypto.KdfParams
) -> dict[str, Any]:
    """Hesap sarmalı: `{id, tanitici, salt, sarmal, turetim, hatali: 0, askida: false}`.

    TEK hesap sarmalı yazıcısıdır (modül başlığı "HESAP SARMALI KİMLİĞE BAĞLIDIR"): anahtar
    kanonik kimliğe bağlıdır (`crypto.account_wrapping_key`) ve `id` alanına AYNI kanonik
    metin yazılır. Kanonik olmayan kimlikle sarmal yazılmaz (`ValueError`/`TypeError`).
    """
    kimlik = crypto.canonical_account_id(hesap_id)
    tuz = crypto.new_salt()
    return {
        "id": kimlik,
        "tanitici": tanitici,
        "salt": base64.b64encode(tuz).decode("ascii"),
        "sarmal": crypto.wrap_key(
            data_key,
            wrapping_key=crypto.account_wrapping_key(
                password, salt=tuz, account_id=kimlik, params=kdf
            ),
        ),
        WRAP_DERIVATION_FIELD: WRAP_DERIVATION,
        "hatali": 0,
        "askida": False,
    }


@sensitive_variables("recovery_key", "data_key")
def _recovery_section(
    data_key: bytes, *, recovery_key: str, no: int, kdf: crypto.KdfParams
) -> dict[str, Any]:
    """Kurtarma bölümü: `{no, tarih, salt, sarmal, dogrulandi: null}` (tarih üretim günü)."""
    tuz = crypto.new_salt()
    return {
        "no": no,
        "tarih": timezone.localdate().isoformat(),
        "salt": base64.b64encode(tuz).decode("ascii"),
        "sarmal": crypto.wrap_key(
            data_key,
            wrapping_key=crypto.derive_key(
                normalize_recovery_key(recovery_key), salt=tuz, params=kdf
            ),
        ),
        RECOVERY_CONFIRMED_FIELD: None,
    }


@sensitive_variables("password", "recovery_key", "data_key")
def _build_state(
    data_key: bytes,
    *,
    hesap_id: object,
    tanitici: str,
    password: str,
    recovery_key: str,
    gecis: str | None = None,
) -> dict[str, Any]:
    """Tek hesaplı şema 2 durumu (ilk kurulum; testlerin varsayılan ortamı da bunu kurar)."""
    kdf = crypto.DEFAULT_KDF
    return {
        "surum": STATE_VERSION,
        # Dış yedek hatırlatmasının ilk günü (`dis_yedek`): hesap kurulduğu an.
        "olusturma": timezone.localtime().isoformat(timespec="seconds"),
        "kdf": kdf.to_dict(),
        "hesaplar": [
            _account_wrap(
                data_key, hesap_id=hesap_id, tanitici=tanitici, password=password, kdf=kdf
            )
        ],
        "kurtarma": _recovery_section(data_key, recovery_key=recovery_key, no=1, kdf=kdf),
        "gecis": gecis,
    }


def _kdf_of(state: dict[str, Any]) -> crypto.KdfParams:
    kdf = state.get("kdf", {})
    return crypto.KdfParams.from_dict(dict(kdf) if isinstance(kdf, dict) else {})


def _wrap_parts(bolum: dict[str, Any]) -> tuple[bytes, str] | None:
    """Sarmal bölümünün tuzu (çözülmüş) ve sarmalı; biri eksik ya da biçimsizse None."""
    tuz_b64 = str(bolum.get("salt", ""))
    sarmal = str(bolum.get("sarmal", ""))
    if not tuz_b64 or not sarmal:
        return None
    try:
        return base64.b64decode(tuz_b64), sarmal
    except (binascii.Error, ValueError):
        return None


def _unwrap_or_none(sarmal: str, sarmalama: bytes) -> bytes | None:
    try:
        return crypto.unwrap_key(sarmal, wrapping_key=sarmalama)
    except Exception:  # noqa: BLE001 — InvalidToken ve biçim hataları aynı yanıta çıkar
        return None


def wrap_is_bound(bolum: dict[str, Any]) -> bool:
    """Sarmal kimliğe bağlı türetimle mi yazılmış? (`turetim` etiketi; YALNIZ ret içindir)

    Etiket türetimi seçmez (modül başlığı): yanlışsa sarmal açılmadan reddedilir, doğruysa
    yine tek türetimle açılır; sonradan eklenen etiket bağsız bir sarmalı açtırmaz.
    """
    return bolum.get(WRAP_DERIVATION_FIELD) == WRAP_DERIVATION


def _require_bound(bolum: dict[str, Any]) -> None:
    """Bağsız sarmalda Argon2id koşmadan, sayaca dokunmadan `UnboundWrap` (409)."""
    if not wrap_is_bound(bolum):
        raise UnboundWrap(UNBOUND_WRAP_MESSAGE)


@sensitive_variables("password")
def _try_unwrap_account(
    bolum: dict[str, Any], state: dict[str, Any], password: str
) -> bytes | None:
    """HESAP sarmalını parolayla açmayı dener; açılmazsa None (gecikme ve sayaç çağıranındır).

    TEK hesap sarmalı okuyucusudur. Anahtar sarmalın KENDİ `id` alanına bağlıdır
    (`crypto.account_wrapping_key`): alan başka hesabın kimliğine çevrilmişse, kanonik değilse
    ya da etiket (`turetim`) yoksa sarmal açılmaz — yanlış parolayla aynı sonuç. Bağsız
    türetime geri düşen kol YOKTUR (modül başlığı).

    Kimlik okumada da yazımdaki kuraldan geçer (`crypto.canonical_account_id`) ve bu denetim
    Argon2id'den ÖNCE yapılır: kanonik olmayan kimlikte türetim hiç koşmaz. Yakalanan hata
    YALNIZ kimliğinkidir: `kdf` alanı biçimsizse (`KdfParams.from_dict`'in `int(...)`'i) hata
    çağırana çıkar, yanlış parola sayılmaz (sayaç artmaz, hesap askıya düşmez; kurtarma
    yoluyla aynı davranış).
    """
    if not wrap_is_bound(bolum):
        return None
    parcalar = _wrap_parts(bolum)
    if parcalar is None:
        return None
    tuz, sarmal = parcalar
    try:
        kimlik = crypto.canonical_account_id(bolum.get("id"))
    except (TypeError, ValueError):  # kimlik kanonik değil: o sarmal açılmaz
        return None
    sarmalama = crypto.account_wrapping_key(
        password, salt=tuz, account_id=kimlik, params=_kdf_of(state)
    )
    return _unwrap_or_none(sarmal, sarmalama)


# ---------------------------------------------------------------------------
# Sarmal özeti (modül başlığı "SARMALIN TAZELİĞİ" ve "İKİ AŞAMALI ÖZET")
# ---------------------------------------------------------------------------
#: Satırdaki özet yerleri (`_digest_slot`).
DIGEST_SLOT_CURRENT = "asil"
DIGEST_SLOT_PENDING = "bekleyen"


@sensitive_variables("data_key")
def wrap_digest(data_key: bytes, bolum: dict[str, Any]) -> str | None:
    """Sarmalın DEK'li özeti (`crypto.account_wrap_digest`); kimlik kanonik değilse ya da tuz veya
    sarmal eksik/biçimsizse None — hiçbir özeti tutmaz (fail-closed)."""
    parcalar = _wrap_parts(bolum)
    if parcalar is None:
        return None
    tuz, sarmal = parcalar
    try:
        return crypto.account_wrap_digest(
            data_key, account_id=bolum.get("id"), salt=tuz, wrapped=sarmal
        )
    except (TypeError, ValueError):
        return None


@sensitive_variables("data_key")
def _own_wrap_digest(data_key: bytes, bolum: dict[str, Any]) -> str:
    """Programın az önce kurduğu sarmalın özeti (`_account_wrap`'in biçimi; None olamaz)."""
    ozet = wrap_digest(data_key, bolum)
    if ozet is None:  # pragma: no cover — yazıcının kendi sarmalı daima biçimlidir
        raise AppPasswordError("Parola kaydının özeti hesaplanamadı; işlem yapılmadı.")
    return ozet


def _digest_slot(hesap: Account, ozet: str | None) -> str | None:
    """Özetin satırdaki yeri: asıl (`"asil"`), bekleyen (`"bekleyen"`) ya da None.

    İki alan da her çağrıda sabit sürede karşılaştırılır (`kanonik.esit`); boş alan hiçbir özeti
    tutmaz (özeti boş satır parolayla açılmaz).
    """
    if not ozet:
        return None
    asil = bool(hesap.wrap_digest) and kanonik.esit(hesap.wrap_digest, ozet)
    bekleyen = bool(hesap.wrap_digest_pending) and kanonik.esit(hesap.wrap_digest_pending, ozet)
    if asil:
        return DIGEST_SLOT_CURRENT
    return DIGEST_SLOT_PENDING if bekleyen else None


def digest_matches(hesap: Account, ozet: str | None) -> bool:
    """Sarmalın özeti satırın asıl ya da bekleyen özetini tutuyor mu? (iki depo karşılaştırması)"""
    return _digest_slot(hesap, ozet) is not None


def _check_wrap_digest(hesap: Account, ozet: str | None, data_key: bytes) -> str:
    """Açılan sarmalın özeti satırınkini tutmalı; tutanın yerini döndürür (modül başlığı).

    Tutmazsa olay `BUTUNLUK` satırı olarak düşer (DEK elde: İA çözülebilir; `_muhur_bozuk_izi`)
    ve `WrapDigestMismatch` yükselir. Satıra dokunulmaz; hatalı deneme sayacına ve gecikmeye
    dokunulmaz (mühür uyuşmazlığı yoluyla aynı). Çağıran satırın mührünü önceden doğrulamıştır:
    mührü tutmayan satırın özetine güvenilmez.
    """
    yer = _digest_slot(hesap, ozet)
    if yer is None:
        logger.warning(
            "Parola kaydının özeti hesap satırınkini tutmadı; giriş reddedildi, satıra "
            "dokunulmadı (%s).",
            hesap.id,
        )
        _muhur_bozuk_izi(hesap, data_key, alan="wrap_digest")
        raise WrapDigestMismatch(WRAP_DIGEST_MISMATCH_MESSAGE)
    return yer


def _kept_digest(hesap: Account, mevcut: str | None) -> str:
    """İki aşamalı yazımın 1. adımında asıl alanda kalacak özet (modül başlığı).

    Dosyada ŞU AN duran sarmal meşruysa (satırın asıl ya da bekleyen özetini tutuyorsa) onun özeti:
    kesintide o sarmal açılabilir kalmalı. Değilse (yok, eski ya da program dışından konmuş)
    satırın asıl özeti değişmez.
    """
    if mevcut is not None and _digest_slot(hesap, mevcut) is not None:
        return mevcut
    return str(hesap.wrap_digest)


@sensitive_variables("data_key")
def kept_wrap_digest(hesap: Account, data_key: bytes) -> str:
    """`_kept_digest` güncel `guvenlik.json`'daki sarmalla (parolası bilinmeyen hesap: sıfırlama).

    Sarmalın açılması gerekmez: özet DEK'le sarmalın baytlarından hesaplanır. Çağıran dosya
    kilidini (`dosya_kilidi`) tutar.
    """
    mevcut = _find_wrap(_require_state(), hesap.id)
    return _kept_digest(hesap, wrap_digest(data_key, mevcut) if mevcut is not None else None)


def set_wrap_digests(hesap: Account, *, asil: str, bekleyen: str) -> list[str]:
    """Özet alanlarını örneğe yazar (KAYDETMEZ, mühürlemez); değişen alan adlarını döndürür.

    Çağıran mührü yeniler (`compute_seal`) ve alanları kaydeder.
    """
    degisen: list[str] = []
    if hesap.wrap_digest != asil:
        hesap.wrap_digest = asil
        degisen.append("wrap_digest")
    if hesap.wrap_digest_pending != bekleyen:
        hesap.wrap_digest_pending = bekleyen
        degisen.append("wrap_digest_pending")
    return degisen


@sensitive_variables("data_key")
def write_wrap_digests(
    hesap: Account,
    data_key: bytes,
    *,
    asil: str,
    bekleyen: str,
    anahtar: denetim_izi.AcikAnahtar | None = None,
) -> bool:
    """Özetleri yazar, mührü yeniler ve `HESAP` iz satırını ekler; değişiklik yoksa yazmaz.

    Çağıranın işleminde ve yazar bağlamında çağrılır (iki aşamalı yazımın 1. adımı, sıfırlamanın
    2. adımı). Yazdıysa True.
    """
    onceki = denetim_izi.anlik(hesap)
    alanlar = set_wrap_digests(hesap, asil=asil, bekleyen=bekleyen)
    if not alanlar:
        return False
    hesap.seal = hesap.compute_seal(data_key)
    hesap.save(update_fields=[*alanlar, "seal"])
    denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=onceki, anahtar=anahtar)
    return True


@sensitive_variables("data_key", "password")
def new_account_wrap(
    data_key: bytes, *, hesap_id: object, tanitici: str, password: str
) -> dict[str, Any]:
    """Güncel dosyanın KDF'siyle yeni hesap sarmalı (bellekte; yazmaz). Özeti yazımdan önce
    satıra girsin diye sarmal önce kurulur (`_account_wrap`; modül başlığı)."""
    return _account_wrap(
        data_key,
        hesap_id=hesap_id,
        tanitici=tanitici,
        password=password,
        kdf=_kdf_of(_require_state()),
    )


@sensitive_variables("data_key")
def wrap_digests(data_key: bytes) -> dict[str, str | None]:
    """`guvenlik.json`'daki her hesabın İLK sarmalının özeti (kilit açılışı da ilkini dener)."""
    ozetler: dict[str, str | None] = {}
    for bolum in _accounts_in(_require_state()):
        kimlik = str(bolum.get("id", ""))
        if kimlik not in ozetler:
            ozetler[kimlik] = wrap_digest(data_key, bolum)
    return ozetler


@contextmanager
def dosya_kilidi() -> Iterator[None]:
    """Güvenlik dosyasının süreç içi kilidi (oku-değiştir-yaz; hesap servisleri iki aşamalı
    yazımda tutar). Sıra hep dosya kilidi → veritabanı işlemidir (`dosya_ve_iz_islemi`)."""
    with _state_lock:
        yield


@sensitive_variables("recovery_key")
def _try_unwrap_recovery(state: dict[str, Any], recovery_key: str) -> bytes | None:
    """KURTARMA sarmalını (normalleştirilmiş) anahtarla açmayı dener; açılmazsa None.

    Kurtarma bölümü hesaba bağlı değildir: anahtar `crypto.derive_key`'in kendisidir (değişmedi).
    """
    bolum = state.get("kurtarma")
    parcalar = _wrap_parts(bolum) if isinstance(bolum, dict) else None
    if parcalar is None:
        return None
    tuz, sarmal = parcalar
    sarmalama = crypto.derive_key(
        normalize_recovery_key(recovery_key), salt=tuz, params=_kdf_of(state)
    )
    return _unwrap_or_none(sarmal, sarmalama)


@sensitive_variables("password")
def _unwrap_with_account(state: dict[str, Any], hesap: str, password: str) -> bytes:
    """Geri yükleme için: tanıtıcısı (ya da kimliği) verilen hesabın sarmalını açar.

    Yalnız `backup_restore` çağırır: hesap sayacına DOKUNMAZ (geri yükleme denemesinin
    gecikmesi hesapsız ve süreç içidir; plan F1b-1). Yedek başlığında hesap yoktur
    (TK10), bu yol yalnız güncel `guvenlik.json` ile işler. Sarmal kendi `id`'sine bağlı
    açılır (`_try_unwrap_account`): geri yüklemenin yetki denetimi (`geri_yukleme_yetkisi`)
    aynı sarmalın `id`'sini denetler, yani parolanın gerçekten açtığı hesabı. Kimliği
    değiştirilmiş ya da bağsız sarmal yanlış parolayla aynı yanıtı alır.
    """
    bolum = _find_wrap_by_login_name(state, hesap)
    dek = _try_unwrap_account(bolum, state, password) if bolum is not None else None
    if dek is None:
        _delay_after_failure()
        raise WrongPassword(_WRONG_PASSWORD_MESSAGE)
    return dek


@sensitive_variables("recovery_key")
def _unwrap_with_recovery(state: dict[str, Any], recovery_key: str) -> bytes:
    """Kurtarma sarmalını açar; yanlışsa süreç içi gecikme + `AppPasswordError`."""
    dek = _try_unwrap_recovery(state, recovery_key)
    if dek is None:
        _delay_after_failure()
        raise AppPasswordError(_WRONG_RECOVERY_MESSAGE)
    return dek


# ---------------------------------------------------------------------------
# Geçiş öncesi yedek
# ---------------------------------------------------------------------------
def database_file() -> Path | None:
    """Canlı veritabanı dosyasının yolu; dosya tabanlı değilse (testler) None."""
    if connection.vendor != "sqlite":  # pragma: no cover — program yalnız SQLite kullanır
        return None
    ad = str(connection.settings_dict.get("NAME") or "")
    # Django'nun SQLite test veritabanı bellek içidir (`file:...mode=memory...`).
    if not ad or ad == ":memory:" or "mode=memory" in ad:
        return None
    return Path(ad)


def take_transition_backup(label: str) -> Path | None:
    """Geçiş ÖNCESİ tam veritabanı kopyası alır; yolunu döndürür (alınamazsa None).

    Masaüstü kabuğuyla aynı RAM-içi SQLite görüntüsü ve `.odbak` şifreli kapsayıcı
    yordamları kullanılır. Adı rotasyon desenlerine ÇAKIŞMAZ (`pre-parola-*`);
    kabuğun 14 günlük rotasyonu bu dosyalara DOKUNMAZ. Başlık TK10 izdüşümüdür
    (yalnız kurtarma bölümü).

    KOPYA AYRI BİR BAĞLANTIDAN alınır (canlı Django bağlantısından DEĞİL): açık
    bir işlem varken `sqlite3.Connection.backup()` SQLITE_BUSY'de sonsuz döngüye
    girer — testte donma olarak yakalandı. Ayrı bağlantı WAL dosyasını da
    okuduğu için kopya tutarlıdır.

    Bellek-içi veritabanında (testler) yedek ATLANIR ve None döner; çağıranlar
    yedeği zorunlu koşul saymaz, ama gerçek kurulumda daima alınır.
    """
    kaynak = database_file()
    if kaynak is None or not kaynak.exists():
        logger.warning("Veritabanı dosya tabanlı değil; geçiş öncesi yedek atlandı.")
        return None
    hedef_dizin = backup_dir()
    hedef_dizin.mkdir(parents=True, exist_ok=True)
    damga = timezone.localtime().strftime("%Y-%m-%d-%H%M%S")
    hedef = hedef_dizin / f"pre-parola-{label}-{damga}{BACKUP_SUFFIX}"
    try:
        encrypt_to_path(
            database_snapshot(kaynak),
            hedef,
            load_public_key(_data_dir()),
            recovery_header=recovery_metadata(_data_dir()),
        )
    except (sqlite3.Error, OSError, BackupCryptoError):
        logger.exception("Geçiş öncesi yedek alınamadı.")
        raise AppPasswordError(
            "Güvenlik değişikliği öncesi yedek alınamadı; işlem yapılmadı. "
            "Veri klasöründe yer olduğundan emin olup yeniden deneyin."
        ) from None
    logger.info("Geçiş öncesi yedek alındı: %s", hedef.name)
    return hedef


# ---------------------------------------------------------------------------
# Şifreli alan kayıt defteri
# ---------------------------------------------------------------------------
def encrypted_field_map() -> list[tuple[type[models.Model], tuple[str, ...]]]:
    """Şifreli alan taşıyan tüm modeller — elle liste YOK, koddan okunur.

    Yeni bir `EncryptedTextField` eklendiğinde sıfırlama koşulu
    (`_encrypted_rows_exist`) ve "şifrelenen alanlar" listesi onu KENDİLİĞİNDEN
    kapsar.
    """
    sonuc: list[tuple[type[models.Model], tuple[str, ...]]] = []
    for model in django_apps.get_models():
        alanlar = tuple(f.name for f in crypto.encrypted_fields_of(model))
        if alanlar:
            sonuc.append((model, alanlar))
    return sonuc


def protected_field_labels() -> list[str]:
    """Arayüzde "hangi kişisel alanlar korunuyor" listesi (Türkçe, tekilleştirilmiş).

    Kişisel veri taşımayan şifreli alanlar (iz anahtarı;
    `ENCRYPTED_FIELDS_ARE_PERSONAL = False`) listelenmez (tasarım §4.6.5).
    """
    etiketler: list[str] = []
    for model, _ in encrypted_field_map():
        if not getattr(model, "ENCRYPTED_FIELDS_ARE_PERSONAL", True):
            continue
        for alan in crypto.encrypted_fields_of(model):
            etiket = str(getattr(alan, "verbose_name", alan.name))
            if etiket not in etiketler:
                etiketler.append(etiket)
    return etiketler


def _write_fingerprint(value: str) -> None:
    """Parmak izini okul kartına yazar ve iz satırını ekler (çağıranın işleminde; `enable`)."""
    config, olustu = SchoolConfig.objects.get_or_create(pk=SchoolConfig.SINGLETON_PK)
    onceki = None if olustu else denetim_izi.anlik(config)
    config.app_password_hash = value
    config.save(update_fields=["app_password_hash", "updated_at"])
    eylem = AuditAction.OLUSTUR if olustu else AuditAction.GUNCELLE
    denetim_izi.kayit(eylem, config, onceki=onceki)


def _stored_fingerprint() -> str:
    return SchoolConfig.load().app_password_hash


def _persons_exist() -> bool:
    """Kişi ya da hesap tablolarında (silinmişler dahil) satır var mı?"""
    return bool(
        Student.all_objects.exists() or Personnel.all_objects.exists() or Account.objects.exists()
    )


# ---------------------------------------------------------------------------
# Kurtarma anahtarı
# ---------------------------------------------------------------------------
def generate_recovery_key() -> str:
    """Yazdırılabilir kurtarma anahtarı üretir (ör. `A1B2-C3D4-...`, 8 grup)."""
    ham = base64.b32encode(os.urandom(RECOVERY_KEY_BYTES)).decode("ascii").rstrip("=")
    return "-".join(
        ham[i : i + RECOVERY_GROUP_SIZE] for i in range(0, len(ham), RECOVERY_GROUP_SIZE)
    )


def normalize_recovery_key(value: str) -> str:
    """Kullanıcının yazdığı anahtarı normalleştirir (tire/boşluk, küçük harf, İ/ı, 0/1/8).

    Yalnız ASCII harf ve rakam kalır — ön yüzdeki `kurtarmaAnahtariniNormallestir`
    ile birebir aynı kural (iki taraf aynı örnek tablosuyla sınanır).
    """
    buyuk = value.strip().translate(_RECOVERY_TURKISH_I).upper()
    sade = "".join(ch for ch in buyuk if ch.isascii() and ch.isalnum())
    return sade.translate(_RECOVERY_FIXUPS)


def recovery_key_groups(value: str) -> list[str]:
    """Anahtarı dörtlü gruplara ayırır (çıktı ve ekranın ortak biçimi): ['ABCD', …]."""
    sade = normalize_recovery_key(value)
    return [sade[i : i + RECOVERY_GROUP_SIZE] for i in range(0, len(sade), RECOVERY_GROUP_SIZE)]


# ---------------------------------------------------------------------------
# Deneme gecikmesi ve hesap başına sayaç
# ---------------------------------------------------------------------------
def _delay_after_failure() -> None:
    """Süreç içi kademeli gecikme — kurtarma anahtarı ve geri yükleme denemeleri (aile)."""
    global _failed_attempts
    gecikme = FAILURE_DELAYS[min(_failed_attempts, len(FAILURE_DELAYS) - 1)]
    _failed_attempts += 1
    if gecikme:
        time.sleep(gecikme)


def _reset_failures() -> None:
    global _failed_attempts
    _failed_attempts = 0


def _uuid_or_none(deger: object) -> uuid.UUID | None:
    """Hesap kimliği UUID mi? Biçimsizse None (istemciden ya da dosyadan gelir)."""
    try:
        return uuid.UUID(str(deger))
    except ValueError:
        return None


def account_by_id(hesap_id: object) -> Account | None:
    """Kimliği verilen hesap satırı; kimlik UUID değilse ya da satır yoksa None (DEK istemez).

    Kimlik istemciden gelir: biçimsiz değer veritabanı doğrulama hatası yerine
    "hesap yok" sayılır.
    """
    anahtar = _uuid_or_none(hesap_id)
    if anahtar is None:
        return None
    hesap: Account | None = Account.objects.filter(pk=anahtar).first()
    return hesap


def _account_role(hesap_id: object) -> str | None:
    """Hesabın rolü (veritabanından, DEK istemez); satır yoksa None."""
    hesap = account_by_id(hesap_id)
    return hesap.role if hesap is not None else None


def _register_failure(hesap_id: object) -> bool:
    """Hesabın hatalı deneme sayacını artırır ve gecikmeyi uygular; askıya alındıysa True.

    Sayaç `guvenlik.json`'da yazılır (kilitliyken de; arşivlenmez). Gecikme sayacın
    önceki değerinden türer: 0/0/1/2/4 sn, sonra 4. `SUSPEND_AFTER_FAILURES`'a
    ulaşınca program yöneticisi DIŞINDAKİ hesap askıya alınır; rol yalnız o eşikte
    veritabanından okunur (satır yoksa askı uygulanır: rolü kanıtlanamayan hesap
    yönetici sayılmaz).
    """
    with _state_lock:
        state = read_state()
        hesap = _find_wrap(state, hesap_id) if state is not None else None
        if state is None or hesap is None:
            onceki = 0
            askiya = False
        else:
            try:
                onceki = int(hesap.get("hatali", 0))
            except (TypeError, ValueError):
                onceki = 0
            hesap["hatali"] = onceki + 1
            askiya = False
            if hesap["hatali"] >= SUSPEND_AFTER_FAILURES and not hesap.get("askida"):
                askiya = _account_role(hesap_id) != AccountRole.YONETICI
                if askiya:
                    hesap["askida"] = True
            _write_state(state)
    gecikme = FAILURE_DELAYS[min(onceki, len(FAILURE_DELAYS) - 1)]
    if gecikme:
        time.sleep(gecikme)
    if askiya:
        logger.warning("Art arda hatalı deneme: hesap askıya alındı (%s).", hesap_id)
    return askiya


def _clear_failures(hesap_id: object, *, askidan_cikar: bool = False) -> None:
    """Hesabın sayacını (ve istenirse hatalı deneme askısını) sıfırlar; değişiklik yoksa yazmaz."""
    with _state_lock:
        state = read_state()
        hesap = _find_wrap(state, hesap_id) if state is not None else None
        if state is None or hesap is None:
            return
        degisti = bool(hesap.get("hatali"))
        hesap["hatali"] = 0
        if askidan_cikar and hesap.get("askida"):
            hesap["askida"] = False
            degisti = True
        if degisti:
            _write_state(state)


def _failure_outcome(hesap_id: object) -> UnlockRefused:
    """Yanlış parolanın sonucu: sayaç + gecikme; askıya alındıysa askı reddi."""
    if _register_failure(hesap_id):
        return AccountSuspended(_SUSPENDED_NOW_MESSAGE)
    return WrongPassword(_WRONG_PASSWORD_MESSAGE)


# ---------------------------------------------------------------------------
# Durum sorgusu
# ---------------------------------------------------------------------------
def is_password_set() -> bool:
    """İlk hesap kurulu mu? Fail-closed: dosya VAR **ya da** DB parmak izi dolu.

    Dosya varsa DB'ye gidilmez (her istekte çağrılır). Dosya yoksa parmak izi
    sorulur: dolu olması hesabın kurulduğunu, dosyanın ise KAYBOLDUĞUNU gösterir —
    program kuruluma dönmez.
    """
    if state_path().is_file():
        return True
    return bool(_stored_fingerprint())


def _state_file_usable(path: Path) -> bool:
    """Var olan güvenlik dosyası DEK'i açmaya yeter biçimde mi? (tek kural: backup_crypto)"""
    try:
        ham = path.read_bytes()
    except OSError:
        return False
    return parse_security_state(ham) is not None


def security_file_missing() -> bool:
    """Güvenlik dosyası kayıp mı? (kayıp kilidi; tasarım §4.3 tehdit 8)

    İki hâl aynı kilide düşer:

    * dosya yok + DB'de parmak izi dolu (silinmiş ya da yeniden adlandırılmış);
    * dosya VAR ama kullanılamıyor: okunamıyor, boş, bozuk JSON, şema 1 ya da
      sarmal bölümleri eksik (`backup_crypto.is_usable_security_state` — yedek
      başlığının kuralıyla aynıdır). Parmak izinden bağımsızdır (fail-closed:
      dosyanın neyi koruduğu bilinemez) ve DB'ye gitmez.

    Dosya varsa yalnız dosya okunur (her API isteğinde çağrılır; birkaç KB).
    """
    yol = state_path()
    if yol.is_file():
        return not _state_file_usable(yol)
    return bool(_stored_fingerprint())


def _encrypted_rows_exist() -> bool:
    """Şifreli alan taşıyan herhangi bir tabloda (silinmişler dahil) satır var mı?

    Liste elle tutulmaz (`encrypted_field_map`): hesaplar ve iz anahtarı da,
    F1c'den itibaren gelen OAB modellerinin şifreli tabloları da kendiliğinden
    kapsanır.
    """
    for model, _ in encrypted_field_map():
        manager = getattr(model, "all_objects", model._default_manager)
        if manager.exists():
            return True
    return False


#: Hesap kurulurken alınan geçiş yedeğinin adı (`take_transition_backup("acilis")`).
#: `enable()` yalnız kişi tabloları boşken çalıştığı için bu yedek kişi verisi taşımaz.
_TRANSITION_BACKUP_PREFIX = "pre-parola-"
#: Yedek klasöründe veri taşıyabilen dosyalar: şifreli yedek ve (dönüştürülmemiş) eski düz yedek.
_DATA_BACKUP_SUFFIXES = (BACKUP_SUFFIX, ".sqlite3")


def _data_backups_exist() -> bool:
    """Yedek klasöründe kişi verisi taşıyabilecek bir yedek var mı?

    Hesap kurulurken alınan geçiş yedeği (`pre-parola-*`) sayılmaz: o an kişi
    tabloları boştur. Hangi anahtarla şifrelendiğine bakılmaz — yedeğin varlığı
    "korunan veri olabilir" demektir (fail-closed).
    """
    dizin = backup_dir()
    if not dizin.is_dir():
        return False
    return any(
        yol.is_file()
        and yol.suffix in _DATA_BACKUP_SUFFIXES
        and not yol.name.startswith(_TRANSITION_BACKUP_PREFIX)
        for yol in dizin.iterdir()
    )


def state_reset_available() -> bool:
    """ "Güvenlik dosyasını sıfırla ve kuruluma dön" yolu açık mı? (§4.3 tehdit 8)

    DÖRT koşul birden (biri eksikse yol görünmez, uç 409 döner):

    1. güvenlik dosyası VAR ama kullanılamıyor (boş, bozuk, şema 1, bölümleri
       eksik — `security_file_missing` ile aynı kural). Dosya hiç yoksa ve parmak
       izi boşsa zaten "hesap kurulmamış" hâlidir, sıfırlanacak bir şey yoktur;
    2. DB'de anahtar parmak izi BOŞ: ilk hesabın veritabanı işlemi hiç
       tamamlanmamış, yani bu veritabanında o anahtarla şifrelenmiş kalıcı bir
       satır yoktur;
    3. şifreli alan taşıyan bütün tablolar (silinmişler dahil; hesaplar ve iz
       anahtarı dahil) BOŞ;
    4. yedek klasöründe veri taşıyabilen yedek YOK (`_data_backups_exist`).
       Veritabanı kaybolup boş yeniden oluştuğunda 2 ve 3 sağlanır ama eski
       kayıtlar yedeklerde durur; o zaman doğru yol yedekten geri yüklemedir.

    Bu koşullarda bozuk dosya korunacak hiçbir veriyi açmıyordur; kullanıcıyı
    yalnız dosyayı elle silebileceği bir çıkmazda bırakmak yerine dosya
    ARŞİVLENİR (silinmez) ve program ilk açılış hâline döner.
    """
    yol = state_path()
    if not yol.is_file() or _state_file_usable(yol):
        return False
    if _stored_fingerprint():
        return False
    if _encrypted_rows_exist():
        return False
    return not _data_backups_exist()


class StateResetNotAllowed(AppPasswordError):
    """Sıfırlama koşulları sağlanmıyor (görünüm 409 `sifirlama_uygun_degil` döner)."""


def _archive_state_file() -> str:
    """Güvenlik dosyasını ve yedek açık anahtarını arşive TAŞIR; arşiv adını döndürür.

    İlk açılışta ikisi de yoktur; yeni hesap kurulurken yenileri yazılır.
    """
    damga = timezone.localtime().strftime("%Y-%m-%d-%H%M%S")
    arsiv = _archive_target()
    state_path().replace(arsiv)
    yedek_ayari = config_path(_data_dir())
    if yedek_ayari.is_file():
        yedek_ayari.replace(yedek_ayari.with_name(f"yedekleme-arsiv-{damga}.json"))
    OTURUM.kapat()
    _reset_failures()
    return arsiv.name


def reset_unusable_state() -> str:
    """Kullanılamayan güvenlik dosyasını arşivler, programı "hesap kurulmamış" hâline döndürür.

    Yalnız `state_reset_available()` doğruyken çalışır; aksi hâlde
    `StateResetNotAllowed`. Dosya `guvenlik-arsiv-<damga>.json` adıyla kenara
    alınır (geri yüklemenin arşiv adıyla aynı desen); eski yedek açık anahtarı
    (`yedekleme.json`) da `yedekleme-arsiv-<damga>.json` olur. Arşiv adını döndürür.
    """
    if not state_reset_available():
        raise StateResetNotAllowed(RESET_NOT_ALLOWED_MESSAGE)
    with _state_lock:
        ad = _archive_state_file()
    logger.warning("Kullanılamayan güvenlik dosyası arşivlendi (%s); kurulum yeniden başlar.", ad)
    return ad


def resolve_interrupted_setup() -> str | None:
    """Yarım kalmış ilk hesap kurulumunu çözer (plan F1b-1); arşivlendiyse arşiv adını döndürür.

    Yalnız dosya `gecis: "KURULUM"` damgasını taşıyorsa veritabanına bakılır (her
    durum sorgusunda çağrılır; olağan hâlde dosyadan öteye gidilmez):

    * parmak izi dolu: `enable`'ın veritabanı işlemi tamamlanmış, yalnız damga
      kalkmadan kesilmiş → damga kaldırılır (arşivlenmez);
    * parmak izi boş VE kişi ve hesap tabloları boş: yarım kurulum → dosya ve yedek
      açık anahtarı arşivlenir, program kuruluma döner (korunacak veri yoktur);
    * başka her hâl (parmak izi boş ama satır var): dokunulmaz — fail-closed,
      kilit açma `iki_depo_tutarsiz` ile reddeder.

    Bozuk ya da kullanılamaz dosyada hiçbir şey yapılmaz (kayıp kilidinin işidir).
    """
    try:
        state = read_state()
    except AppPasswordError:
        return None
    if state is None or state.get("gecis") != TRANSITION_SETUP:
        return None
    if not is_usable_security_state(state):
        return None
    with _state_lock:
        state = read_state()
        if state is None or state.get("gecis") != TRANSITION_SETUP:
            return None
        if _stored_fingerprint():
            state["gecis"] = None
            _write_state(state)
            logger.info("Kurulum damgası kaldırıldı (veritabanı işlemi tamamlanmıştı).")
            return None
        if _persons_exist():
            return None
        ad = _archive_state_file()
    logger.warning(
        "Yarım kalan kurulum: güvenlik dosyası arşivlendi (%s); kurulum yeniden başlar.", ad
    )
    return ad


def is_locked() -> bool:
    """Hesap kurulu ve oturum açık değil mi? (`OTURUM`; DEK oturumla birlikte bellektedir)"""
    return is_password_set() and not OTURUM.acik_mi()


def require_password_set() -> None:
    """İlk hesap kurulmamışsa `PasswordRequired` (409 `parola_gerekli`) yükseltir.

    Kişi yazan uçların izin sınıfı (`permissions.RequiresAdminPassword`) ve
    kişi yazan servisler savunma derinliği için çağırır.
    """
    if not is_password_set():
        raise PasswordRequired()


def status() -> dict[str, Any]:
    """Arayüzün okuduğu durum özeti (sır ve kişi adı içermez). HİÇ hata yükseltmez.

    Kullanılamayan güvenlik dosyası `security_file_missing` olarak raporlanır
    (arayüz kayıp ekranını ve geri yükleme kartını gösterir); durum ucu 500
    dönseydi arayüz kilit de kayıp da gösteremezdi. Yarım kalmış kurulum burada
    çözülür (`resolve_interrupted_setup`).

    Şema 2 alanları: `account_count` (dosyadaki hesap sarmalı sayısı),
    `recovery_key_no` ve `recovery_key_date` (kurtarma anahtarının kimliği, TK10; ISO
    gün, tek kural `backup_crypto.recovery_key_identity`),
    `corrupt_field_count` (bu süreçte okunan çözülemeyen şifreli alan sayısı, D48).
    `password_set` "ilk hesap kurulu", `transition` kurulum damgasıdır.
    """
    try:
        resolve_interrupted_setup()
    except (DatabaseError, OSError):
        logger.exception("Yarım kurulum denetimi yapılamadı.")
    kayip = security_file_missing()
    state: dict[str, Any] | None = None
    if not kayip:
        try:
            state = read_state()
        except AppPasswordError:  # iki okuma arasında bozulduysa (yarış) — yine kayıp
            kayip = True
    kurulu = state is not None or kayip
    gecis = state.get("gecis") if state else None
    gecis_metni = gecis if isinstance(gecis, str) else ""
    kimlik = recovery_key_identity(state) or {}
    return {
        "password_set": kurulu,
        "locked": kurulu and not OTURUM.acik_mi(),
        "security_file_missing": kayip,
        # Kayıp ekranındaki "sıfırla ve kuruluma dön" yolu (yalnız korunan veri yokken).
        "reset_available": kayip and state_reset_available(),
        "transition_pending": bool(gecis_metni),
        "transition": gecis_metni,
        # Kurtarma anahtarının saklandığı doğrulandı mı? (damga; kurulum kapısı)
        "recovery_key_confirmed": _recovery_confirmed_in(state),
        "protected_fields": protected_field_labels(),
        "account_count": len(_accounts_in(state)) if state else 0,
        "recovery_key_no": kimlik.get("no"),
        "recovery_key_date": kimlik.get("tarih"),
        "corrupt_field_count": crypto.corrupt_read_count(),
    }


def _recovery_confirmed_in(state: dict[str, Any] | None) -> bool:
    """Durumun kurtarma bölümünde doğrulama damgası var mı? Hata yükseltmez."""
    if not isinstance(state, dict):
        return False
    bolum = state.get("kurtarma")
    if not isinstance(bolum, dict):
        return False
    damga = bolum.get(RECOVERY_CONFIRMED_FIELD)
    return isinstance(damga, str) and bool(damga)


def recovery_key_confirmed() -> bool:
    """Kurtarma anahtarının saklandığı doğrulandı mı? HİÇ hata yükseltmez.

    `setup/status/` (sağlık denetimi ucu) ve `setup/complete/` kapısı sorar:
    yalnız güvenlik dosyası okunur, DB'ye gidilmez. Dosya yok, okunamıyor ya da
    damga yoksa yanlış döner (fail-closed: kurulum tamamlanmaz).
    """
    try:
        return _recovery_confirmed_in(read_state())
    except AppPasswordError:
        return False


def account_id_for_login_name(tanitici: str) -> str | None:
    """Tanıtıcısı verilen açık (`KAPALI` olmayan) hesabın kimliği; yoksa None.

    Konsol araçları ve kurtarma anahtarıyla açılış kullanır. Tanıtıcı kayıttaki
    biçimine getirilir (kırpılır, Türkçe küçük harf; `hesap_kurallari.validate_login_name`).
    """
    hesap_id = (
        Account.objects.exclude(status=AccountStatus.KAPALI)
        .filter(login_name=tr_lower(tanitici.strip()))
        .values_list("id", flat=True)
        .first()
    )
    return str(hesap_id) if hesap_id is not None else None


def _recovery_account(hesap: object) -> Account | None:
    """Kurtarma yolunun hesabı: kimliği YA DA tanıtıcısı verilen satır; yoksa None.

    Kurtarma anahtarıyla geri yüklemeden sonra `guvenlik.json`'da sarmal yoktur ve
    kilit ekranı listesi boştur; ön yüz hesabı kurtarma listesinden
    (`hesaplar.recovery_accounts`) ya da kullanıcının yazdığı tanıtıcıdan bulur.
    Tanıtıcı UUID biçiminde olamaz (harfle başlar, en çok 32 karakter): iki yol çakışmaz.
    """
    satir = account_by_id(hesap)
    if satir is None:
        kimlik = account_id_for_login_name(str(hesap))
        satir = account_by_id(kimlik) if kimlik is not None else None
    return satir


# ---------------------------------------------------------------------------
# Kurtarma bölümünün iz satırı
# ---------------------------------------------------------------------------
def _kimlik_degeri(deger: object) -> int | str | None:
    """Kurtarma bölümünün `no`/`tarih` değeri izdeki biçimiyle; başka tür izlenmez (None)."""
    if isinstance(deger, bool) or not isinstance(deger, int | str):
        return None
    return deger


def _kurtarma_izi(eski: object, yeni: dict[str, Any]) -> None:
    """Yeni kurtarma anahtarının `KURTARMA` satırı (çağıranın işleminde; tasarım §4.4.4).

    Satır yalnız anahtarın kimliğini (no, üretim günü; TK10) değer olarak taşır; tuz,
    sarmal ve doğrulama damgası yalnız adlarıyla görünür. Belgenin basımı iz yazmaz
    (plan F1b-1: birlik evrakı değildir, tasarım §9.7).
    """
    onceki = eski if isinstance(eski, dict) else {}
    degisen = sorted(ad for ad in {*onceki, *yeni} if onceki.get(ad) != yeni.get(ad))
    denetim_izi.olay(
        AuditAction.KURTARMA,
        model=denetim_izi.KURTARMA_ANAHTARI,
        object_id=str(_kimlik_degeri(yeni.get("no"))),
        changed_fields=degisen,
        values={
            ad: [_kimlik_degeri(onceki.get(ad)), _kimlik_degeri(yeni.get(ad))]
            for ad in ("no", "tarih")
            if ad in degisen
        },
    )


# ---------------------------------------------------------------------------
# İlk hesap (kurulum sihirbazının 1. adımı)
# ---------------------------------------------------------------------------
def _require_first_setup() -> None:
    """İlk hesabın ön koşulları (§4.4.5): dosya yok, parmak izi boş, kişi ve hesap tabloları boş.

    Biri tutmazsa Türkçe ret (`AppPasswordError`). `enable` bunu iki kez sorar:
    Argon2id'den önce (hızlı ret) ve `_state_lock` altında dosyayı yazmadan hemen
    önce (çift gönderim; aşağıda).
    """
    if read_state() is not None:
        raise AppPasswordError("Program yöneticisi hesabı zaten kurulu.")
    if _stored_fingerprint():
        raise AppPasswordError(
            "Program yöneticisi hesabı daha önce kurulmuş, ancak güvenlik dosyası "
            "(guvenlik.json) bulunamadı. Yeni hesap kurulamaz; dosyanın yedeğini veri "
            "klasörüne geri koyun ya da bir yedekten geri yükleyin."
        )
    if _persons_exist():
        raise AppPasswordError(
            "Kayıtlı öğrenci, öğretmen, diğer personel ya da hesap varken ilk program "
            "yöneticisi hesabı kurulamaz. Hesap, kurulum sihirbazının ilk adımında, kişi "
            "kaydından önce kurulur."
        )


def _state_carries_account(hesap_id: object) -> bool:
    """Diskteki güvenlik dosyası bu hesabın sarmalını taşıyor mu? (okunamazsa hayır)"""
    try:
        state = read_state()
    except AppPasswordError:
        return False
    return state is not None and _find_wrap(state, hesap_id) is not None


@sensitive_variables("password", "veri_anahtari", "iz_anahtari", "kurtarma")
def enable(*, tanitici: str, display_name: str, password: str) -> str:
    """İlk program yöneticisi hesabını kurar; TEK SEFERLİK kurtarma anahtarını döndürür.

    Yalnız ilk kurulumda çalışır (§4.4.5): güvenlik dosyası yokken, DB'de parmak
    izi boşken VE kişi ve hesap tabloları (silinmişler dahil) boşken. Parmak izi
    doluysa ya hesap zaten kurulmuştur ya da güvenlik dosyası kaybolmuştur; ikisinde
    de yeni bir anahtar üretmek eski kayıtları okunamaz bırakırdı. Yarım kalmış bir
    önceki kurulum önce çözülür (`resolve_interrupted_setup`).

    SIRA (plan F1b-1; modül başlığı): (1) `guvenlik.json` `gecis: "KURULUM"` ile;
    yedek açık anahtarı ve `pre-parola` yedeği; (2) TEK veritabanı işlemi: mühürlü
    `Account` (`yonetici`, `ACIK`, dosyadaki sarmalın özeti), DEK'le şifreli ilk iz anahtarı (`AuditKey`; İA
    DEK'ten türemez, ayrı üretilir), parmak izi ve zincirin ilk satırları (`HESAP`,
    ilk kurtarma anahtarı için `KURTARMA`, okul kartının yazımı; yazar bu hesap);
    (3) damga kalkar. Oturum bu
    hesapla açılır (`OTURUM.ac`; DEK ve İA bellekte). Kurulumda boşta kilit yoktur
    (tasarım §13 D15): kurtarma anahtarı ekrandayken oturum kendiliğinden kapanmaz.

    ÇİFT GÖNDERİM (sihirbazda düğmeye iki kez basılması; sunucu birden çok iş
    parçacığında koşar): ön koşullar `_state_lock` altında, dosya yazılmadan hemen
    önce YENİDEN sorulur. İkinci istek ilk kurulumun dosyasını görür ve "zaten
    kurulu" ile döner; o dosyayı ezmez, oturumun DEK'ini değiştirmez. Argon2id
    türetmesi kilit dışındadır, karar kilit içindedir. (1)-(2)'de hata olursa geri
    alma yalnız BU çağrının yazdığı dosyayı siler (dosya bu hesabın sarmalını
    taşımıyorsa dokunulmaz).

    (3) yazılamazsa (`OSError`) kurulum yine tamamdır: veritabanı işlemi bitmiş,
    parmak izi doludur; damgayı ilk durum sorgusu kaldırır (`resolve_interrupted_setup`).
    Oturum yine açılır ve kurtarma anahtarı döner: DEK oturumsuz bellekte kalmaz.

    Dönen kurtarma anahtarı (no 1) hiçbir yerde AÇIK saklanmaz — çağıran onu
    kullanıcıya bir kez gösterir (yazdırma/indirme), sonrasında yalnız sarmalı kalır.
    Tanıtıcının ad-soyadı içerip içermediği uyarısı çağıranındır
    (`hesap_kurallari.login_name_warning`).
    """
    resolve_interrupted_setup()
    _require_first_setup()
    tanitici = _kural(hesap_kurallari.validate_login_name, tanitici)
    ad = _kural(hesap_kurallari.validate_display_name, display_name)
    parola = validate_password(password)

    veri_anahtari = crypto.new_data_key()
    iz_anahtari = secrets.token_bytes(AUDIT_KEY_BYTES)
    kurtarma = generate_recovery_key()
    hesap_id = uuid.uuid4()
    state = _build_state(
        veri_anahtari,
        hesap_id=hesap_id,
        tanitici=tanitici,
        password=parola,
        recovery_key=kurtarma,
        gecis=TRANSITION_SETUP,
    )
    with _state_lock:
        # Çift gönderim: karar kilit altında, dosyayı yazmadan hemen önce (belge dizesi).
        _require_first_setup()
        # (1) Dosya ÖNCE: ters sırada, dosya yazılmadan kesilen kurulum DEK'i yok ederdi.
        _write_state(state)
        yedek_ayar_yolu = config_path(_data_dir())
        onceki_yedek_ayari = yedek_ayar_yolu.read_bytes() if yedek_ayar_yolu.is_file() else None

        def _geri_al() -> None:
            crypto.unload_key()
            if _state_carries_account(hesap_id):
                state_path().unlink(missing_ok=True)
            if onceki_yedek_ayari is None:
                yedek_ayar_yolu.unlink(missing_ok=True)
            else:
                yedek_ayar_yolu.write_bytes(onceki_yedek_ayari)

        try:
            ensure_public_config(_data_dir(), veri_anahtari, replace=True)
            take_transition_backup("acilis")
        except Exception:
            _geri_al()
            raise

        # (2) TEK veritabanı işlemi. Şifreli alanlar (ad-soyad, iz anahtarı) ve içerik
        # MAC'i için DEK ve İA belleğe alınır; işlem düşerse geri bırakılır. İlk iz
        # satırları (zincirin başı) bu hesabındır (plan F1b-1 "Denetim izi").
        crypto.load_key(veri_anahtari, audit_key=iz_anahtari)
        try:
            with (
                yazar_olarak(Yazar(hesap_id=str(hesap_id), rol=AccountRole.YONETICI.value)),
                transaction.atomic(),
            ):
                simdi = timezone.now()
                hesap = Account(
                    id=hesap_id,
                    login_name=tanitici,
                    role=AccountRole.YONETICI,
                    display_name=ad,
                    status=AccountStatus.ACIK,
                    opened_at=simdi,
                    password_changed_at=simdi,
                    # Tek aşamalı: kimliğin önceki sarmalı yoktur, dosyadaki sarmal (1) yazıldı
                    # (modül başlığı "İKİ AŞAMALI ÖZET").
                    wrap_digest=_own_wrap_digest(veri_anahtari, state["hesaplar"][0]),
                )
                hesap.seal = hesap.compute_seal(veri_anahtari)
                hesap.save(force_insert=True)
                AuditKey.objects.create(
                    key=base64.b64encode(iz_anahtari).decode("ascii"),
                    valid_from_seq=1,
                    created_at=simdi,
                )
                denetim_izi.kayit(AuditAction.HESAP, hesap, onceki=None)
                _kurtarma_izi(None, state["kurtarma"])
                _write_fingerprint(crypto.key_fingerprint(veri_anahtari))
        except Exception:
            _geri_al()
            raise

        # (3) Damga kalkar (arşivlenmez). Yazılamazsa ya da burada kesilirse damgayı
        # durum sorgusu kaldırır; oturum yine açılır (belge dizesi).
        state["gecis"] = None
        try:
            _write_state(state)
        except OSError:
            logger.warning(
                "Kurulum damgası kaldırılamadı; ilk durum sorgusu kaldıracak.", exc_info=True
            )
    OTURUM.ac(
        OturumHesabi(id=str(hesap_id), tanitici=tanitici, rol=AccountRole.YONETICI.value),
        veri_anahtari=veri_anahtari,
        iz_anahtari=iz_anahtari,
    )
    _reset_failures()
    logger.info("İlk program yöneticisi hesabı kuruldu.")
    return kurtarma


# ---------------------------------------------------------------------------
# Kilit açma (iki depo kuralı)
# ---------------------------------------------------------------------------
def _password_expired(hesap: Account) -> bool:
    """Parola değişiminin üzerinden 180 günden fazla geçti mi? (TK15; değişim anı yoksa evet)"""
    if hesap.password_changed_at is None:
        return True
    sinir = timedelta(days=hesap_kurallari.PASSWORD_MAX_AGE_DAYS)
    return timezone.now() - hesap.password_changed_at > sinir


def _check_fingerprint(data_key: bytes) -> None:
    """DB parmak izi doluysa DEK'inkine eşit olmalı (başka veritabanının dosyası reddedilir)."""
    kayitli = _stored_fingerprint()
    if kayitli and not kanonik.esit(kayitli, crypto.key_fingerprint(data_key)):
        raise TwoStoreMismatch(_FOREIGN_DB_MESSAGE)


def _muhurlu_satir(hesap_id: object, data_key: bytes, *, giris: bool = False) -> Account:
    """Satırı okur ve mührünü DEK'le doğrular (DEK belleğe alınmadan). Satıra dokunmaz.

    Satır yoksa `TwoStoreMismatch`, mühür tutmazsa `AccountSealMismatch`. Girişte
    (`giris`) mühür tutmazsa olay ayrıca denetim izine `BUTUNLUK` satırı olarak düşer
    (`_muhur_bozuk_izi`; tasarım §4.6.1 kural 1, tehdit 19). Satırın izini SORMAZ: o,
    çağıranın sırasıyla `satir_izini_denetle`'dir (kilit açılışı ve kurtarma önce İA'yı çözer).
    """
    hesap = account_by_id(hesap_id)
    if hesap is None:
        raise TwoStoreMismatch(_NO_ROW_MESSAGE)
    if not hesap.seal_matches(data_key):
        logger.warning("Hesap mührü tutmadı; giriş reddedildi, satıra dokunulmadı (%s).", hesap_id)
        if giris:
            _muhur_bozuk_izi(hesap, data_key)
        raise AccountSealMismatch(_SEAL_MISMATCH_MESSAGE)
    return hesap


def _sealed_account(hesap_id: object, data_key: bytes, *, giris: bool = False) -> Account:
    """Mühürlü ve izi tutan satır: `_muhurlu_satir` + `satir_izini_denetle` (modül başlığı
    "SATIRIN İZİ"). Oturumdaki parola doğrulaması ve parola değiştirme kullanır (İA bellekte).
    Döndürülen satır kararın satırıdır (`satir_izini_denetle`)."""
    hesap = _muhurlu_satir(hesap_id, data_key, giris=giris)
    return satir_izini_denetle(hesap, data_key)


#: Satır izi tutmadığında `BUTUNLUK` satırının alan adı (kart onu mühür ve özetten ayırır).
KAYIT_MAC_ALANI = "kayit_mac"


def satir_izini_denetle(
    hesap: Account, data_key: bytes, *, ileti: str = _SEAL_MISMATCH_MESSAGE
) -> Account:
    """Satır denetim izindeki son içerik MAC'li kaydını tutmalı (modül başlığı "SATIRIN İZİ").

    Karar `denetim_izi.hesap_izi_tutuyor`'dadır (ORM'siz tek işlev `satir_izi.hesap_izi_tutuyor`;
    DEK verilir, kilit açılışında henüz belleğe alınmamıştır). Çağıranın okuduğu mühür beklenen
    mühürdür: izi doğrulanan hâl, kararın verildiği hâlin AYNISIDIR (`satir_izi` adım 5). Tutmazsa
    önce yanlış alarm ayıklanır (`_yaristan_sonraki_satir`); yine tutmazsa mühür uyuşmazlığıyla
    AYNI muamele (kullanıcı kararı 03.11.2026): `BUTUNLUK` satırı (`SISTEM`, alan `kayit_mac`;
    `_muhur_bozuk_izi`) ve `AccountRecordStale` (409 `hesap_muhru_tutmadi`); satıra dokunulmaz,
    hatalı deneme sayacına ve gecikmeye dokunulmaz. Çağıran mührü önceden doğrulamıştır. Hesap
    servisleri kendi iletilerini verir (`ileti`).

    DÖNÜŞ kararın satırıdır: çoğu kez verilen `hesap`; arada meşru bir yazım satırı değiştirdiyse
    yazıcılarla sıralı işlemde yeniden okunup mührü ve izi doğrulanmış GÜNCEL satır. Çağıran sonraki
    kararlarını (özet, durum, rol) dönen satırdan verir.
    """
    if denetim_izi.hesap_izi_tutuyor(hesap.id, veri_anahtari=data_key, beklenen_muhur=hesap.seal):
        return hesap
    guncel = _yaristan_sonraki_satir(hesap, data_key)
    if guncel is not None:
        logger.info(
            "Hesap satırı denetim sırasında programca değişti; karar güncel satırdan verildi (%s).",
            hesap.id,
        )
        return guncel
    logger.warning(
        "Hesap satırı denetim izindeki son kaydını tutmadı; işlem reddedildi, satıra "
        "dokunulmadı (%s).",
        hesap.id,
    )
    _muhur_bozuk_izi(hesap, data_key, alan=KAYIT_MAC_ALANI)
    raise AccountRecordStale(ileti)


def _yaristan_sonraki_satir(hesap: Account, data_key: bytes) -> Account | None:
    """Yanlış alarm ayıklaması (modül başlığı "SATIRIN İZİ"; bağımsız denetim bulgusu): ilk denetim
    işlem dışında koşar ve çağıranın ORM okumasından ayrı bir anlık görüntüdür. Arada aynı hesaba
    commit edilen MEŞRU bir yazım (çift tıklanan giriş ya da askıdan çıkarma) satırın mührünü
    değiştirmişse ilk denetim tutmaz — oysa satır ve izi tutarlıdır; silinemez bir `BUTUNLUK`
    satırı yanlış alarm olurdu.

    Denetim bu yüzden yazıcılarla SIRALI bir işlemde (`atomic`; ayarlarda `BEGIN IMMEDIATE`, arada
    yazım commit edilemez) yinelenir: satır yeniden okunur; var, mührü bu DEK'le tutuyor ve AYNI
    anlık görüntüde izini tutuyorsa (beklenen mühür onun mührü) güncel satır döner — karar ondan
    verilir, alarm yazılmaz. Değilse None (satır program dışından değişmiştir). Dönen satır
    doğrulanmış güncel hâldir: iki hâl arasında satırı gidip getiren biri de kararı ancak doğrulanmış
    hâlden aldırabilir (ör. Senaryo 1'in geçici parolası güncel satırın özetini tutmaz). Çağıran bir
    işlemin içindeyse kayıt noktasıdır ve aynı anlık görüntüyü görür (ayıklama bir şey değiştirmez).
    """
    with transaction.atomic():
        guncel = account_by_id(hesap.id)
        if (
            guncel is None
            or not guncel.seal_matches(data_key)
            or not denetim_izi.hesap_izi_tutuyor(
                guncel.id, veri_anahtari=data_key, beklenen_muhur=guncel.seal
            )
        ):
            return None
    return guncel


def _muhur_bozuk_izi(hesap: Account, data_key: bytes, *, alan: str = "seal") -> None:
    """Mühür (`seal`), sarmal özeti (`wrap_digest`) ya da satırın izi (`kayit_mac`) tutmadı:
    `BUTUNLUK` satırı (`SISTEM`), satıra dokunulmadan (§4.6.1 kural 1; modül başlığı "SARMALIN
    TAZELİĞİ", "SATIRIN İZİ").

    DEK sarmaldan açıldığı için İA çözülebilir; satır oturum açılmadan, o DEK'ten çözülen
    İA ile yazılır (iz bellekteki anahtarı beklemez). Aktör `SISTEM`'dir: mührü, özeti ya da
    izi tutmayan satırın hesabı kanıtlanmış bir yazar değildir. Satır kaydın kimliğini ve
    tutmayan alanın adını taşır; program yöneticisinin panosundaki kart bu satırdan okunur.
    Yazılamazsa (İA çözülemiyor, veritabanı yazılamıyor) giriş yine reddedilir, olay
    günlüğe düşer. Kendi işlemindedir: çağıranın açık bir işlemi geri alınırsa satır da gider
    (hesap servislerinin uçları istek boyu işlem açmamalıdır).
    """
    try:
        anahtar = denetim_izi.anahtari_coz(data_key)
        with sistem_olarak(), transaction.atomic():
            denetim_izi.olay(
                AuditAction.BUTUNLUK,
                model=denetim_izi.model_etiketi(Account),
                object_id=str(hesap.id),
                changed_fields=[alan],
                anahtar=anahtar,
            )
    except Exception:  # noqa: BLE001 — giriş zaten reddediliyor; iz yazılamadığı günlüğe düşer
        logger.exception("Hesap kaydının tutmadığı denetim izine yazılamadı.")


def _open_account_for_login(
    hesap_id: object, data_key: bytes, ozet: str | None
) -> tuple[Account, denetim_izi.AcikAnahtar]:
    """İki depo kuralının veritabanı yarısı: parmak izi, satır, mühür, iz anahtarı, satırın izi,
    sarmal özeti, durum (§4.6.1 kural 1; modül başlığı "İKİ DEPO KURALI" 1). `ozet` açılan
    sarmalınkidir. Satırı ve çözülen iz anahtarını döndürür.

    Sıranın gerekçesi: mühür tutmuyorsa satırın hiçbir değerine güvenilmez; satırın izi tutmuyorsa
    (eski bir kopyadan geri konmuş satır) özetine ve durumuna da güvenilmez — özet ve durum ancak
    güncel olduğu kanıtlanmış satırdan okunur, eski satırın durumu (ör. kapanmadan önceki `ACIK`)
    karar vermez ve her geri sarma `BUTUNLUK` satırıyla izlenir. İz anahtarı satırın izinden ÖNCE
    çözülür: çözülemiyorsa ret `AuditKeyUnreadable`'dır (veritabanının DEK'e bağlı parçası okunamıyor;
    iz yazılamaz), satırın izi suçlanmaz. Meşru satırda durum iletisi değişmez (askı, kapalı hesap).
    """
    _check_fingerprint(data_key)
    hesap = _muhurlu_satir(hesap_id, data_key, giris=True)
    anahtar = _decrypt_audit_key(data_key)
    hesap = satir_izini_denetle(hesap, data_key)
    _check_wrap_digest(hesap, ozet, data_key)
    if hesap.status == AccountStatus.ASKIDA:
        raise AccountSuspended(_SUSPENDED_MESSAGE)
    if hesap.status not in (AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI):
        raise TwoStoreMismatch(_NO_ROW_MESSAGE)
    return hesap, anahtar


def _decrypt_audit_key(data_key: bytes) -> denetim_izi.AcikAnahtar:
    """Etkin iz anahtarını aday DEK'le çözer (DEK belleğe alınmadan; tasarım §4.6.3).

    Çözüm `denetim_izi.anahtari_coz`'dadır (yazıcı aynı kuralla doğrular). İA yoksa ya
    da çözülemezse `AuditKeyUnreadable`: iz yazılamazsa yazma yapılamaz (hesap
    bütünlüğü), giriş açılmaz.
    """
    try:
        return denetim_izi.anahtari_coz(data_key)
    except denetim_izi.IzAnahtariOkunamadi as exc:
        raise AuditKeyUnreadable(_AUDIT_KEY_MESSAGE) from exc


def _replace_wrap(state: dict[str, Any], yeni: dict[str, Any]) -> None:
    """Hesabın sarmalını ÖNCEDEN kurulmuş yeni sarmalla değiştirir (yoksa ekler); sayaç ve askı sıfır.

    Sarmal yazımdan önce kurulur (`_account_wrap`, `new_account_wrap`): özeti iki aşamalı yazımın
    1. adımında satıra girer (modül başlığı "İKİ AŞAMALI ÖZET"); dosyaya giren sarmal o özetin
    sarmalının ta kendisidir. Yeni sarmal aynı kimliği taşıyan İLK sarmalın yerine geçer; aynı
    kimliği taşıyan öteki sarmallar silinir. Program aynı kimliğe ikinci sarmal yazmaz; dosyada
    varsa program dışından eklenmiştir (kilit açılışı ilkini dener). Yeniden kurulumdan sonra
    kalsaydı eski parolanın açtığı bir kopya dosyada sessizce yaşardı. Yapısal yazımdır (arşiv
    kopyası önce). Çağıran `_state_lock`'u tutar.
    """
    kalan: list[dict[str, Any]] = []
    yerlesti = False
    for hesap in _accounts_in(state):
        if str(hesap.get("id", "")) != yeni["id"]:
            kalan.append(hesap)
        elif not yerlesti:
            kalan.append(yeni)
            yerlesti = True
    if not yerlesti:
        kalan.append(yeni)
    state["hesaplar"] = kalan
    _write_structural(state)


def _remove_wraps(hesap_idler: set[str]) -> None:
    """Sarmalları `guvenlik.json`'dan (arşiv kopyası önce) ve bütün arşivlerden siler (TK11).

    Sıra: ana dosya (yapısal yazım: önce güncel dosyanın arşiv kopyası, sonra
    sarmalsız dosya), sonra bütün arşivler (az önce alınan kopya dahil) ve `.tmp`
    artıkları. Arşiv adımı yarıda kalırsa sarmal yalnız arşivlerde kalır; kilit
    açılışındaki temizlik adayları ana dosyayla BİRLİKTE arşivlerden de topladığı
    için onu bulur (`_cleanup_closed_wraps`).
    """
    with _state_lock:
        state = read_state()
        if state is not None:
            hesaplar = _accounts_in(state)
            kalan = [h for h in hesaplar if str(h.get("id", "")) not in hesap_idler]
            if len(kalan) != len(hesaplar):
                state["hesaplar"] = kalan
                _write_structural(state)
        _remove_wraps_from_archives(hesap_idler)


def _cleanup_closed_wraps(data_key: bytes) -> None:
    """ "Kapalı hesabın sarmalı duruyor" temizliği (§4.6.1 kural 3; fikirdeş).

    Her kilit açılışında koşar. Adaylar `guvenlik.json`'daki VE bütün
    `guvenlik-arsiv-*` kopyalarındaki sarmallardır: kapamanın dosya adımı ana
    dosyayı yazıp arşivlerde yarıda kaldıysa ya da kurtarma anahtarıyla geri
    yükleme eski dosyayı arşive taşıdıysa sarmal yalnız arşivde durur (TK11).
    YALNIZ mührü ve izi (denetim izindeki son içerik MAC'li kaydı) tutan `KAPALI` satırın
    sarmalı silinir: durumu program dışından değiştirilmiş satır meşru bir sarmalı
    sildiremez (tehdit 19; plan F1b-1).
    Kesilmiş yazımların `.tmp` artıkları da silinir.

    HİÇBİR HATA girişi durdurmaz (yalnız dosya hatası değil; bağımsız denetim bulgusu): temizlik
    her kilit açılışında yinelenen bir en-iyi-çaba işidir ve sarmal yazımından SONRA koşar
    (`_start_session`). Düşseydi işlem geri sarılır, dosyada yeni parolanın sarmalı durur, satırı
    (`PAROLA`/`KURTARMA`) ve bildirimi geri alınırdı: kesintiyle aynı hâl, ama süreç ölmeden ve
    istenildiği an (zehirli bir arşivle) tekrarlanabilir biçimde. Hata günlüğe düşer, temizlik bir
    sonraki kilit açılışında yinelenir. Bütün gövde kendi kayıt noktasındadır: veritabanı
    hatası da yalnız bu noktayı geri alır, kilit açılışının işlemi kullanılabilir kalır.

    DENETİM İZİ: silinen her sarmal için `guvenlik.sarmal` `HESAP` satırı (`sarmal_izi`;
    sarmal yalnız arşivde kalmışsa da), yazar `SISTEM` (programın kendi düzeltmesi; iki depo
    karşılaştırmasının durum düzeltmesi gibi). Kilit açılışının işleminin EN SONUNDA, bir
    kayıt noktasında (`savepoint`) koşar (`_start_session`): satırlar dosyadan önce eklenir;
    ana dosya yazılamazsa yalnız bu satırlar geri alınır, giriş sürer. Sarmal ana dosyadan
    silinip yalnız bir arşiv kopyası temizlenemediyse satırlar kalır (sarmal artık kilit
    açmaz; kalan kopyayı sonraki açılış siler ve yeniden yazar). Ana dosya yazıldıktan SONRA
    dosya hatası olmayan bir istisna gelirse kayıt noktasının `SISTEM` satırları geri alınır ama
    ana dosya değişmiş kalır (sarmal izsiz silinmiş olur; arşivde kalan kopyayı sonraki açılış
    satırıyla siler); bu, girişin düşmesinden iyidir.
    """
    try:
        with _state_lock, transaction.atomic():
            _kapali_sarmallari_temizle(data_key)
    except Exception:  # noqa: BLE001 — en-iyi-çaba temizlik girişi durdurmaz (belge dizesi)
        logger.warning(
            "Kapalı hesap sarmallarının temizliği tamamlanamadı; bir sonraki kilit "
            "açılışında yinelenecek.",
            exc_info=True,
        )


def _kapali_sarmallari_temizle(data_key: bytes) -> None:
    """`_cleanup_closed_wraps`'ın gövdesi; çağıran `_state_lock`'u ve kayıt noktasını tutar."""
    state = read_state()
    adaylar = {str(h.get("id", "")) for h in _accounts_in(state)} if state else set()
    adaylar |= _archived_wrap_ids()
    idler = [kimlik for kimlik in map(_uuid_or_none, adaylar) if kimlik is not None]
    silinecek = {
        str(hesap.id)
        for hesap in Account.objects.filter(pk__in=idler, status=AccountStatus.KAPALI)
        if hesap.seal_matches(data_key)
        and denetim_izi.hesap_izi_tutuyor(
            hesap.id, veri_anahtari=data_key, beklenen_muhur=hesap.seal
        )
    }
    if not silinecek:
        _remove_leftover_temps()
        return
    with sistem_olarak(), transaction.atomic():
        for kimlik in sorted(silinecek):
            sarmal_izi(kimlik, silindi=True, her_zaman=True)
        try:
            _remove_wraps(silinecek)
        except OSError:
            if silinecek & set(wrap_ids()):
                raise  # ana dosya yazılmadı: satırlar da geri alınır
            logger.warning(
                "Kapalı hesapların sarmalı güvenlik dosyasından silindi; bazı arşiv "
                "kopyaları temizlenemedi, bir sonraki kilit açılışında yinelenecek.",
                exc_info=True,
            )
    logger.info("Kapalı hesapların kalan sarmalı silindi (%d).", len(silinecek))


def _start_session(
    hesap: Account,
    data_key: bytes,
    anahtar: denetim_izi.AcikAnahtar,
    *,
    acilan_ozet: str | None = None,
    ozet_plani: tuple[str, str] | None = None,
    giris_oncesi: Callable[[Account], None] | None = None,
    yeni_sarmal: Callable[[], None] | None = None,
) -> Account:
    """Bütün denetimlerden SONRA: yedek anahtarı, sayaç; iz satırları ve temizlik; sonra oturum.

    Baştan sona `IZ_KIP_KILIDI` tutulur (kilitli kip yazıcısı ve bekleyen bir kilidin satırı ile
    çapası araya girmesin). İz satırları içerik MAC'i için kaydın çözülmüş değerini ister: DEK ve
    İA önce belleğe alınır (`crypto.load_key`). Sonra tasarım §4.4.3 "Kilit açılışında sıra"nın
    kalan adımları:

    1. çapa, kilitli satırlar ve son 200 satır doğrulanır (`iz_dogrulama.hazirla`; yalnız
       okur, girişi ENGELLEMEZ);
    1a. sarmal değişecekse (`ozet_plani = (korunan, yeni)`; kilit açılışında parola yenileme,
       kurtarma anahtarıyla açılış) iki aşamalı özetin 1. adımı AYRI bir işlemde commit edilir:
       asıl özet `korunan` (dosyada şu an duran meşru sarmalınki), bekleyen özet `yeni`, `HESAP`
       satırı (`write_wrap_digests`; modül başlığı "İKİ AŞAMALI ÖZET"). `giris_oncesi` 2. adımda
       asıl özeti `yeni`ye çeker, bekleyeni boşaltır;
    2. TEK işlemde: girişten önceki yazım (`giris_oncesi`: kilit açılışında parola yenileme
       `PAROLA`, kurtarmada `KURTARMA`), bulgu varsa `BUTUNLUK` (`SISTEM`), geri yükleme
       notu varsa `GERI_YUKLEME` + bekleyen sistem olayları + iki depo karşılaştırması
       (`iz_dogrulama.yaz`), son giriş anı ve `GIRIS` satırı — sarmal değişmiyorsa ve açılan
       sarmal bekleyen özetle tuttuysa ya da satırda bekleyen özet kaldıysa özet düzeltmesi
       (`acilan_ozet` asıla, bekleyen boş, mühür) aynı `GIRIS` yazımındadır; yazar bu hesaptır
       (plan F1b-1 "Denetim izi"); işlemin EN SONUNDA, hâlâ işlemin içinde, yeni parolanın sarmalı
       `guvenlik.json`'a yazılır (`yeni_sarmal`; modül başlığı "DENETİM İZİ": iz satırı dosya
       yazımından önce, dosya yazılamazsa işlem geri sarılır) ve kapalı hesapların kalan
       sarmalları `SISTEM` satırlarıyla silinir (`_cleanup_closed_wraps`; kendi kayıt
       noktasında, HİÇBİR hatası girişi durdurmaz: sarmal yazımından sonra commit dışında
       düşebilecek adım yoktur). İkisi de dosyaya yazar: işlemin sonunda olmaları, sonraki bir
       adım düşüp satırlar geri alındığında dosyanın izsiz değişmiş kalmaması içindir;
    3. işlem commit edildikten sonra not silinir, gerekiyorsa çapa yenilenir
       (`iz_dogrulama.tamamla`); oturum EN SONDA açılır (`OTURUM.ac`).

    İşlem düşerse oturum açılmaz ve bu çağrının belleğe aldığı anahtarlar düşer (`OTURUM.kapat`):
    iz yazılamazsa yazma yapılamaz; not yerinde kalır, sonraki açılış yeniden işler. Çağrıdan
    ÖNCE süren bir oturum (açık ya da uçuştakileri bekleyen bir kilit; `OTURUM.suruyor_mu`)
    varsa anahtarlar onundur (aynı DEK ve İA): düşen giriş ona dokunmaz, nesli değiştirmez.
    Bekleyen kilidin `KILIT` satırı ve çapası böylece yazılır, uçuştaki iş de DEK'siz kalmaz
    (`apps.okul.oturum` modül başlığı "KİLİDİN İZİ"). Düzenli kapanış başladıysa
    (`OTURUM.kapaniyor_mu`) açılış hiçbir şey yazmadan reddedilir (`ProgramClosing`): kapanış
    kilidi bu kilidin altında açılan oturumu görmeden süreç bitmesin. Sarmal ancak işlemin bütün
    satırlarından sonra yazıldığı için işlem düşen girişte parola DEĞİŞMEZ (kurtarma anahtarı
    elinde olan biri parolayı izsiz ve bildirimsiz yenileyemez; 1a'nın bekleyen özeti dosyada
    olmayan sarmalı anlatır, eski sarmal asıl özetle açılmayı sürdürür); süreç sarmal yazımıyla
    commit arasında ölürse ya da commit düşerse (arada başka düşebilecek adım yoktur: kapalı
    hesap temizliği hatasını yutar, okunamayan arşiv atlanır) yeni parola bekleyen özetle
    geçerlidir, satır eskide kalır ve ilk kilit açılışı özeti asıla çeker (`change_password` ile aynı kesinti hâli; modül başlığı
    "İKİ AŞAMALI ÖZET"). O ana dek ara katman oturumu kapalı görür; açık olmayan oturumun
    istekleri 423 alır.

    4. ertelenen gün işleri (tasarım §4.4.3 sırasının son adımı, TK19): oturum açılıp
       kilitler BIRAKILDIKTAN sonra masaüstünün gün kapısına "ertelenenleri şimdi dene"
       sinyali verilir (`masaustu_kanca.ertelenen_gun_islerini_dene`). Sinyal engellemez ve
       hata yükseltmez: iş `od-gunluk` iş parçacığında, bakım kapısından geçerek ve bu
       kilitleri kendisi alarak koşar; isteğin iş parçacığında uzun iş koşmaz. Masaüstü
       yoksa (testler, konsol) etkisizdir; tetiklenen iş düşerse saatlik deneme sürer.

    Kilit sırası `_state_lock` → `IZ_KIP_KILIDI` → veritabanı → oturum kilidi: dosya
    kilidi en dışta (modül başlığı "DENETİM İZİ"; `dosya_ve_iz_islemi` ile aynı yön), ters
    yönde alan yol yoktur.
    """
    with _state_lock, IZ_KIP_KILIDI:
        if OTURUM.kapaniyor_mu():
            raise ProgramClosing(PROGRAM_CLOSING_MESSAGE)
        # replace=True: DEK bu noktada DB parmak izine ve hesabın mührüne karşı
        # KANITLANDI — otorite dosya değil anahtardır. Bayat/uyumsuz yedekleme.json
        # (ör. çapraz-DEK geri yükleme artığı) burada sessizce onarılır.
        ensure_public_config(_data_dir(), data_key, replace=True)
        _clear_failures(hesap.id)
        oturum_hesabi = OturumHesabi.hesaptan(hesap)
        sarmali_yazilacak = frozenset({str(hesap.id)}) if yeni_sarmal is not None else frozenset()
        # Süren oturumun (açık ya da kilitlenmekte) anahtarları aynıdır: düşen giriş onlara
        # dokunmaz (belge dizesi). `IZ_KIP_KILIDI` altında okunur: bekleyen kilit satırını ve
        # çapasını bu kilidin altında yazar, arada oturum kapanmaz.
        onceden_suruyordu = OTURUM.suruyor_mu()
        crypto.load_key(data_key, audit_key=anahtar.ia)
        try:
            acilis = iz_dogrulama.hazirla(anahtar)
            if ozet_plani is not None:
                # 1a: bekleyen özet sarmal yazımından ÖNCE commit edilir (belge dizesi).
                korunan, yeni_ozet = ozet_plani
                with yazar_olarak(Yazar.hesaptan(oturum_hesabi)), transaction.atomic():
                    write_wrap_digests(
                        hesap, data_key, asil=korunan, bekleyen=yeni_ozet, anahtar=anahtar
                    )
            with yazar_olarak(Yazar.hesaptan(oturum_hesabi)), transaction.atomic():
                if giris_oncesi is not None:
                    giris_oncesi(hesap)
                iz_dogrulama.yaz(acilis, anahtar=anahtar, sarmali_yazilacak=sarmali_yazilacak)
                onceki = denetim_izi.anlik(hesap)
                # Son giriş mührün dışındadır (§4.6.1); özet düzeltmesi yoksa yalnız bu sütun
                # yazılır. Düzeltme: açılan sarmal asıl özete, bekleyen boşa (belge dizesi).
                hesap.last_login_at = timezone.now()
                alanlar = ["last_login_at"]
                if ozet_plani is None and acilan_ozet is not None:
                    duzeltme = set_wrap_digests(hesap, asil=acilan_ozet, bekleyen="")
                    if duzeltme:
                        hesap.seal = hesap.compute_seal(data_key)
                        alanlar += [*duzeltme, "seal"]
                hesap.save(update_fields=alanlar)
                denetim_izi.kayit(AuditAction.GIRIS, hesap, onceki=onceki, anahtar=anahtar)
                if yeni_sarmal is not None:
                    yeni_sarmal()
                _cleanup_closed_wraps(data_key)
            iz_dogrulama.tamamla(acilis)
            OTURUM.ac(oturum_hesabi, veri_anahtari=data_key, iz_anahtari=anahtar.ia)
        except BaseException:
            if not onceden_suruyordu:
                OTURUM.kapat()
            raise
    _reset_failures()
    masaustu_kanca.ertelenen_gun_islerini_dene()  # (4): kilitlerin DIŞINDA, yalnız sinyal
    return hesap


@sensitive_variables("password", "new_password", "veri_anahtari", "iz_anahtari", "yeni")
def unlock(*, hesap_id: object, password: str, new_password: str | None = None) -> Account:
    """Seçilen hesabın parolasıyla kilidi açar; oturumdaki hesabı döndürür.

    Sıra (modül başlığı, İKİ DEPO KURALI 1): askı → bağsız sarmal (`UnboundWrap`, sayaçsız)
    → yalnız bu hesabın sarmalı, KENDİ kimliğine bağlı (Argon2id bir kez; kimliği
    değiştirilmiş sarmal yanlış parola sayılır) → parmak izi, satır, mühür (tutmazsa
    `BUTUNLUK` satırı), iz anahtarı, satırın izi (tutmazsa `AccountRecordStale` + `BUTUNLUK`
    satırı, sayaçsız; modül başlığı "SATIRIN İZİ"), sarmal özeti (tutmazsa `WrapDigestMismatch` +
    `BUTUNLUK` satırı, sayaçsız; modül başlığı "SARMALIN TAZELİĞİ"), durum → parola yenileme
    gereği → sayaç → tek işlemde son giriş ve `GIRIS` satırı (gerekiyorsa özet düzeltmesiyle),
    sonunda kapalı hesap sarmalı temizliği → oturum açılır (`_start_session`). Herhangi bir
    ret hâlinde DEK belleğe ALINMAZ ve satıra dokunulmaz. Oturum açıkken çağrılırsa
    oturum bu hesaba geçer (parolayla kanıtlanmış "Kilitle + aç"; `apps.okul.oturum`
    modül başlığı).

    Hesap `PAROLA_YENILENMELI` ise ya da parolası 180 günden eskiyse
    `new_password` zorunludur (yoksa `PasswordRenewalRequired`, 409
    `parola_yenilenmeli`); yeni parola politikaya uymalı ve eskisinden farklı
    olmalıdır. Yeni sarmal önce bellekte kurulur; iki aşamalı özetin 1. adımı (asıl: açılan
    sarmalınki, bekleyen: yeninin) ayrı işlemde commit edilir; satır (`ACIK`, değişim anı,
    özet, mühür) ve `PAROLA` satırı `GIRIS` ile aynı işlemde, sarmal (arşiv kopyası önce) o
    işlemin EN SONUNDA yazılır (`_start_session` `yeni_sarmal`): işlem düşerse parola
    değişmez, satır `PAROLA_YENILENMELI` kalır; süreç sarmal yazımıyla commit arasında ölürse
    yeni parola bekleyen özetle geçerlidir ve bir sonraki girişte yenileme yeniden istenir.
    Gerek yokken verilen `new_password` yok sayılır.
    """
    resolve_interrupted_setup()
    state = _require_state()
    sarmal = _find_wrap(state, hesap_id)
    if sarmal is None:
        raise TwoStoreMismatch(_NO_WRAP_MESSAGE)
    if sarmal.get("askida"):
        raise AccountSuspended(_SUSPENDED_MESSAGE)
    _require_bound(sarmal)
    veri_anahtari = _try_unwrap_account(sarmal, state, password)
    if veri_anahtari is None:
        raise _failure_outcome(hesap_id)
    acilan_ozet = wrap_digest(veri_anahtari, sarmal)
    hesap, iz_anahtari = _open_account_for_login(hesap_id, veri_anahtari, acilan_ozet)
    giris_oncesi: Callable[[Account], None] | None = None
    yeni_sarmal: Callable[[], None] | None = None
    ozet_plani: tuple[str, str] | None = None
    if hesap.status == AccountStatus.PAROLA_YENILENMELI or _password_expired(hesap):
        if not new_password:
            raise PasswordRenewalRequired(_RENEWAL_REQUIRED_MESSAGE)
        yeni = validate_password(new_password)
        if yeni == password:
            raise AppPasswordError(_SAME_PASSWORD_MESSAGE)
        # Yeni sarmal önce kurulur: özeti 1a'da bekleyen, 2'de asıl özet olur (`_start_session`).
        yeni_bolum = _account_wrap(
            veri_anahtari,
            hesap_id=hesap.id,
            tanitici=hesap.login_name,
            password=yeni,
            kdf=_kdf_of(state),
        )
        yeni_ozet = _own_wrap_digest(veri_anahtari, yeni_bolum)
        # Açılan sarmal özetle doğrulandı (`_open_account_for_login`): korunan asıl özet onunki.
        ozet_plani = (str(acilan_ozet), yeni_ozet)

        def _parolayi_yenile(satir: Account) -> None:
            """Satır yazımı ve `PAROLA` satırı `GIRIS` ile aynı işlemde (`_start_session`)."""
            onceki = denetim_izi.anlik(satir)
            satir.status = AccountStatus.ACIK
            satir.password_changed_at = timezone.now()
            alanlar = ["status", "password_changed_at"]
            alanlar += set_wrap_digests(satir, asil=yeni_ozet, bekleyen="")
            satir.seal = satir.compute_seal(veri_anahtari)
            satir.save(update_fields=[*alanlar, "seal"])
            denetim_izi.kayit(AuditAction.PAROLA, satir, onceki=onceki, anahtar=iz_anahtari)

        def _sarmali_yaz() -> None:
            """Yeni parolanın sarmalı: işlemin sonunda, satırlardan sonra (`_start_session`)."""
            _replace_wrap(_require_state(), yeni_bolum)
            logger.info("Kilit açılışında parola yenilendi.")

        giris_oncesi, yeni_sarmal = _parolayi_yenile, _sarmali_yaz

    _start_session(
        hesap,
        veri_anahtari,
        iz_anahtari,
        acilan_ozet=acilan_ozet,
        ozet_plani=ozet_plani,
        giris_oncesi=giris_oncesi,
        yeni_sarmal=yeni_sarmal,
    )
    logger.info("Kilit açıldı.")
    return hesap


def _session_account_or_refuse(hesap_id: object) -> str:
    """Parola yalnız oturumdaki hesap için doğrulanır (plan F1b-1); kimliği döndürür."""
    oturum = OTURUM.hesap_id()
    if oturum is None:
        raise AppPasswordError(_SESSION_UNKNOWN_MESSAGE)
    if str(hesap_id) != oturum:
        raise AppPasswordError(_SESSION_ONLY_MESSAGE)
    return oturum


@sensitive_variables("password", "veri_anahtari")
def _check_session_password(
    state: dict[str, Any], hesap_id: object, password: str
) -> tuple[bytes, str]:
    """Oturumdaki hesabın parolasını sarmala, bellekteki anahtara VE mühürlü satıra karşı doğrular.

    DEK'i ve açılan sarmalın özetini döndürür. Başka bir hesabın parolası geçmez; başka kurulumdan
    getirilmiş (parolası bilinen) bir `guvenlik.json` ile de geçilmez (açılan DEK bellektekiyle
    aynı olmalı). Yanlışta hesabın sayacı artar ve gecikme uygulanır (kilit ekranıyla aynı kural).
    Sarmal açıldıktan sonra satır mühürlü olmalı ve sarmalın özeti satırınkini tutmalıdır (modül
    başlığı "SARMALIN TAZELİĞİ"): oturum açıkken dosyaya eski sarmal konduysa eski parola parola
    doğrulamasını, parola değiştirmeyi ve kurtarma anahtarının yenilenmesini geçmez
    (`WrapDigestMismatch`, `BUTUNLUK` satırı; sayaç artmaz).
    """
    aktif = crypto.active_fingerprint()
    if aktif is None:
        raise AppPasswordError(_LOCKED_MESSAGE)
    _session_account_or_refuse(hesap_id)
    sarmal = _find_wrap(state, hesap_id)
    if sarmal is None:
        raise TwoStoreMismatch(_NO_WRAP_MESSAGE)
    if sarmal.get("askida"):
        raise AccountSuspended(_SUSPENDED_MESSAGE)
    _require_bound(sarmal)
    veri_anahtari = _try_unwrap_account(sarmal, state, password)
    if veri_anahtari is None or not kanonik.esit(crypto.key_fingerprint(veri_anahtari), aktif):
        raise _failure_outcome(hesap_id)
    ozet = wrap_digest(veri_anahtari, sarmal)
    _check_wrap_digest(_sealed_account(hesap_id, veri_anahtari), ozet, veri_anahtari)
    _clear_failures(hesap_id)
    return veri_anahtari, str(ozet)


def verify_password(*, hesap_id: object, password: str) -> None:
    """Oturumdaki hesabın parolasını yeniden doğrular (F4'te DEK işlemleri yeniden sorar).

    Yanlışsa `WrongPassword` ("Parola hatalı.") + hesap sayacı ve gecikme. Anahtar
    bellekte değilse (kilitli) doğrulama yapılamaz; çağıran önce kilidi açtırmalıdır.
    """
    _check_session_password(_require_state(), hesap_id, password)


@sensitive_variables("current_password", "new_password", "yeni", "veri_anahtari", "yeni_bolum")
def change_password(*, hesap_id: object, current_password: str, new_password: str) -> None:
    """Oturumdaki hesabın parolasını değiştirir. Veri YENİDEN ŞİFRELENMEZ — yalnız sarmal yenilenir.

    Yalnız açık oturumda ve o hesabın parolasıyla (plan F1b-1; ailede kilitliyken de
    açıktı ve ikinci bir kilit açma yoluydu; uç da artık kilit kapısından muaf
    değildir). Yeni parola politikaya uymalı ve eskisinden farklı olmalıdır. Parola (ve
    açılan sarmalın özeti) doğrulandıktan sonra yeni sarmal bellekte kurulur; iki aşamalı özet
    (modül başlığı "İKİ AŞAMALI ÖZET"): (1) ayrı işlemde asıl özet açılan sarmalınki, bekleyen
    özet yeninin, `HESAP` satırı; (2) TEK veritabanı işleminde satır (`password_changed_at`,
    `PAROLA_YENILENMELI` ise `ACIK`, asıl özet yeninin, bekleyen boş, yeni mühür) ve `PAROLA`
    iz satırı, EN SONDA sarmal (arşiv kopyası önce): dosya yazılamazsa 2'nin satırları geri
    alınır, eski parola açmayı sürdürür; süreç dosya yazımıyla işlemin sonu arasında ölürse
    yeni parola bekleyen özetle geçerlidir, satır eskide kalır, ilk kilit açılışı özeti asıla
    çeker. Mührü tutmayan satıra dokunulmaz. DEK ve oturum değişmez (yeni açılış sayılmaz;
    boşta sayacı da sıfırlanmaz).
    """
    if not OTURUM.acik_mi():
        raise AppPasswordError(_LOCKED_MESSAGE)
    yeni = validate_password(new_password)
    if yeni == current_password:
        raise AppPasswordError(_SAME_PASSWORD_MESSAGE)
    with _state_lock:
        # Parola işlemin DIŞINDA doğrulanır: yanlış parolanın gecikmesi veritabanının yazma
        # kilidini tutmasın. Sıra yine dosya kilidi → veritabanı işlemidir.
        veri_anahtari, acilan_ozet = _check_session_password(
            _require_state(), hesap_id, current_password
        )
        hesap = _sealed_account(hesap_id, veri_anahtari)
        yeni_bolum = new_account_wrap(
            veri_anahtari, hesap_id=hesap.id, tanitici=hesap.login_name, password=yeni
        )
        yeni_ozet = _own_wrap_digest(veri_anahtari, yeni_bolum)
        # (1) Bekleyen özet, sarmal yazımından ÖNCE commit edilir.
        with transaction.atomic():
            write_wrap_digests(hesap, veri_anahtari, asil=acilan_ozet, bekleyen=yeni_ozet)
        # (2) Satır, `PAROLA` satırı, asıl özet; en sonda sarmal.
        with transaction.atomic():
            hesap = _sealed_account(hesap_id, veri_anahtari)
            onceki = denetim_izi.anlik(hesap)
            hesap.password_changed_at = timezone.now()
            alanlar = ["password_changed_at"]
            if hesap.status == AccountStatus.PAROLA_YENILENMELI:
                hesap.status = AccountStatus.ACIK
                alanlar.append("status")
            alanlar += set_wrap_digests(hesap, asil=yeni_ozet, bekleyen="")
            hesap.seal = hesap.compute_seal(veri_anahtari)
            hesap.save(update_fields=[*alanlar, "seal"])
            denetim_izi.kayit(AuditAction.PAROLA, hesap, onceki=onceki)
            # Doğrulama sayacı sıfırlayıp dosyayı yazmış olabilir: güncel hâl yeniden okunur.
            _replace_wrap(_require_state(), yeni_bolum)
    logger.info("Hesap parolası değiştirildi.")


# ---------------------------------------------------------------------------
# Kurtarma anahtarı: doğrulama, saklandı damgası, yenileme, kurtarmayla açılış
# ---------------------------------------------------------------------------
@sensitive_variables("recovery_key", "veri_anahtari")
def _check_recovery_key(state: dict[str, Any], recovery_key: str) -> None:
    """Kurtarma anahtarını verilen duruma VE bellekteki anahtara karşı doğrular."""
    aktif = crypto.active_fingerprint()
    if aktif is None:
        raise AppPasswordError(_LOCKED_MESSAGE)
    veri_anahtari = _unwrap_with_recovery(state, recovery_key)
    if not kanonik.esit(crypto.key_fingerprint(veri_anahtari), aktif):
        _delay_after_failure()
        raise AppPasswordError(_WRONG_RECOVERY_MESSAGE)
    _reset_failures()


@sensitive_variables("recovery_key")
def verify_recovery_key(recovery_key: str) -> list[str]:
    """Kurtarma anahtarını doğrular; anahtarın dörtlü gruplarını döndürür.

    İki denetim: anahtar `guvenlik.json`'daki KURTARMA SARMALINI açmalı (yanlış
    yazılmış anahtarın kâğıda basılmasını önler) VE çıkan DEK bellekteki
    anahtarla aynı olmalı (başka kurulumun dosyasıyla doğrulama yapılamaz).
    Yanlışsa `AppPasswordError` + süreç içi kademeli gecikme. Kilitliyken doğrulama
    yapılmaz (kilit ara katmanı zaten 423 ile keser). Yalnız program yöneticisi
    (`verify_recovery_key_identity`).

    Anahtar hiçbir iletiye, günlüğe ya da istisnaya yazılmaz.
    """
    return verify_recovery_key_identity(recovery_key)[0]


@sensitive_variables("recovery_key")
def verify_recovery_key_identity(recovery_key: str) -> tuple[list[str], dict[str, Any] | None]:
    """`verify_recovery_key` + anahtarın kimliği `{no, tarih}` (kurtarma anahtarı belgesi için).

    Doğrulama ve kimlik AYNI okunmuş durumdan çıkar: arada anahtar yenilenseydi eski
    anahtarın kâğıdına yenisinin no'su basılırdı. Kimlik `backup_crypto.
    recovery_key_identity` kuralıyla okunur; tuz ve sarmal dönmez. Ret
    `verify_recovery_key` ile aynıdır.

    Yalnız program yöneticisi (tasarım §4.4.2 Güvenlik satırı; rol kapısının ardından derin
    savunma): rol isteğin yazarından okunur, değilse `RolYetkisiz` (403) ve anahtar
    denenmez (gecikme sayacına dokunulmaz). Hesap kurulmamışsa önce o söylenir (yan etkisiz
    okuma; kurulumda yazar yoktur).
    """
    state = _require_state()
    rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURTARMA_ANAHTARI)
    _check_recovery_key(state, recovery_key)
    return recovery_key_groups(recovery_key), recovery_key_identity(state)


@sensitive_variables("recovery_key")
def confirm_recovery_key(recovery_key: str) -> None:
    """Anahtarın saklandığını doğrular ve damgayı `guvenlik.json`'a yazar (tasarım §4.4.4).

    Sihirbaz (ve Ayarlar → Güvenlik) iki grubu istemcide denetledikten sonra
    TAM anahtarı gönderir. Doğrulama `verify_recovery_key` ile aynı kuraldır.
    Doğrulama ile yazım AYNI okunmuş durum üzerinde, kilit altında yapılır:
    arada bir yenileme olsaydı eski anahtarın damgası yeni sarmala yazılırdı.
    Damga yapı değildir, arşivlenmez; fikirdeştir (yeniden doğrulamada zaman
    güncellenir).

    Damga oturumdaki hesabın `KURTARMA` satırıdır (anahtarın no'su kimlik; damga yalnız
    alan adıyla, `dogrulandi`): satır dosyadan ÖNCE, aynı işlemde (`dosya_ve_iz_islemi`).
    Yalnız program yöneticisi (`RolYetkisiz`, 403; anahtar denenmez).
    """
    with _state_lock:
        state = _require_state()
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURTARMA_ANAHTARI)
        _check_recovery_key(state, recovery_key)
        bolum = state.get("kurtarma")
        if not isinstance(bolum, dict):  # pragma: no cover — sarmal açıldıysa bölüm vardır
            raise AppPasswordError("Güvenlik dosyasının kurtarma bölümü okunamadı.")
        eski = dict(bolum)
        bolum[RECOVERY_CONFIRMED_FIELD] = timezone.localtime().isoformat(timespec="seconds")
        with dosya_ve_iz_islemi():
            _kurtarma_izi(eski, bolum)
            _write_state(state)
    logger.info("Kurtarma anahtarının saklandığı doğrulandı.")


@sensitive_variables("password", "veri_anahtari", "yeni_anahtar")
def renew_recovery_key(*, hesap_id: object, password: str) -> str:
    """Kurtarma anahtarını yeniler; YENİ anahtarı döndürür (yanıtta BİR KEZ gösterilir).

    Yalnız program yöneticisi (tasarım TK9, §4.4.2 Güvenlik satırı; değilse `RolYetkisiz`,
    403, parola denenmez) ve yalnız kilit açıkken: parola
    oturumdaki hesabınkine karşı doğrulanır (başka hesabın parolası geçmez);
    yanlışsa "Parola hatalı." + hesap sayacı ve hiçbir dosya değişmez. Sonra aynı
    DEK YENİ anahtar ve YENİ tuzla sarılır: `kurtarma.no` bir artar, `tarih` bugün,
    doğrulama damgası boş (yeni anahtar yeniden doğrulanana dek kurulum kapısı ve
    Güvenlik ekranı uyarır). Önceki `guvenlik.json` arşive kopyalanır (yapısal yazım).

    DEK değişmez: kayıtlar, kör indeks ve yedek anahtarı aynen kalır, oturum
    etkilenmez. Yenileme ele geçmiş bir anahtara karşı koruma DEĞİLDİR: önceki
    yedekler eski anahtarla açılmaya devam eder (§4.4.6-2; D3'teki zarf imhası F4).
    """
    with _state_lock:
        state = _require_state()
        rol_izinleri.yetki_oturum(rol_izinleri.Eylem.KURTARMA_ANAHTARI)
        # Derin savunma: parolası sorulacak hesabın kayıttaki rolü de program yöneticisi.
        if _account_role(hesap_id) != AccountRole.YONETICI:
            raise RolYetkisiz
        veri_anahtari, _ozet = _check_session_password(state, hesap_id, password)
        # Doğrulama sayacı sıfırlayıp dosyayı yazmış olabilir: güncel hâl yeniden okunur.
        state = _require_state()
        eski = state.get("kurtarma")
        eski_no = eski.get("no") if isinstance(eski, dict) else None
        no = (eski_no if isinstance(eski_no, int) and not isinstance(eski_no, bool) else 0) + 1
        yeni_anahtar = generate_recovery_key()
        state["kurtarma"] = _recovery_section(
            veri_anahtari, recovery_key=yeni_anahtar, no=no, kdf=_kdf_of(state)
        )
        # `KURTARMA` satırı dosyadan ÖNCE, aynı işlemde: dosya yazılamazsa satır geri alınır.
        with dosya_ve_iz_islemi():
            _kurtarma_izi(eski, state["kurtarma"])
            _write_structural(state)
    logger.info("Kurtarma anahtarı yenilendi (no %d).", no)
    return yeni_anahtar


@sensitive_variables(
    "recovery_key", "new_password", "parola", "veri_anahtari", "iz_anahtari", "yeni_bolum"
)
def unlock_with_recovery(*, recovery_key: str, hesap_id: object, new_password: str) -> Account:
    """Kurtarma anahtarıyla açar ve program yöneticisi hesabının parolasını yeniler.

    Yalnız VAR OLAN, `KAPALI` olmayan bir program yöneticisi hesabı için (tasarım
    §4.4.3; yeni yönetici açan kol F4'te). Hesap kimliğiyle ya da tanıtıcısıyla
    verilir (`_recovery_account`). Denetimler `unlock`'unkiyle aynıdır
    (parmak izi, mühür, iz anahtarı; DEK ancak hepsinden sonra belleğe alınır).
    Hesabın sarmalı yeni parolayla yeniden kurulur; sarmalı yoksa (kurtarma
    anahtarıyla geri yüklemeden sonra `hesaplar` boştur) yeniden EKLENİR. Hatalı
    deneme sayacı ve askısı sıfırlanır. Satıra yenilenme izi düşer: `reset_at`,
    `reset_kind = KURTARMA`, `reset_notice_pending` — sahibi ilk girişinde görür
    (tehdit 12 deseni). Kurtarma sarmalı DEĞİŞMEZ: elindeki kâğıt geçerli kalır.

    Kurtarma anahtarının yanlış denemeleri süreç içi gecikmeye tabidir (aile).

    DENETİM İZİ (tasarım §4.4.3 "hangi hesap, yeni mi"): satır yazımı `KURTARMA` satırıdır
    (kayıt kimliği hangi hesap olduğunu; değerler `reset_kind`, durum ve tarihleri; var
    olan hesapta açılış alanları değişmez, yeni hesabı açan kol F4'te `OLUSTUR` değerleri
    taşır), ardından aynı işlemde `GIRIS` (`_start_session`). İkisi de o hesabındır.
    Mühür tutmazsa `BUTUNLUK` satırı düşer, giriş açılmaz.

    SIRA (modül başlığı "DENETİM İZİ"): yeni parolanın sarmalı `KURTARMA` ve `GIRIS`
    satırlarından SONRA, aynı işlemin en sonunda yazılır (`_start_session` `yeni_sarmal`).
    İşlem düşerse (iz yazılamadı, veritabanı kilitli, disk dolu) parola DEĞİŞMEZ: eski parola
    açmayı sürdürür, kurtarma anahtarını elinde tutan biri parolayı izsiz ve bildirimsiz
    yenileyemez (tasarım §4.3 tehdit 10 ve 12). Süreç sarmal yazımıyla commit arasında
    ölürse yeni parola bekleyen özetle geçerlidir, satır eskide kalır (`change_password` ile
    aynı kesinti). İki aşamalı özetin 1. adımı (`_start_session` 1a) `KURTARMA`'dan önce ayrı
    işlemde commit edilir; korunan asıl özet dosyada şu an duran sarmalınkidir — yalnız meşruysa
    (modül başlığı "İKİ AŞAMALI ÖZET"). Kurtarma, özeti tutmayan (eski ya da program dışından
    konmuş) sarmalı olan program yöneticisinin çıkışıdır (zarfın üçüncü durumu).
    """
    resolve_interrupted_setup()
    parola = validate_password(new_password)
    hesap = _recovery_account(hesap_id)
    if hesap is None or hesap.role != AccountRole.YONETICI:
        raise AppPasswordError(_RECOVERY_ONLY_ADMIN_MESSAGE)
    if hesap.status not in (AccountStatus.ACIK, AccountStatus.PAROLA_YENILENMELI):
        raise AppPasswordError(_RECOVERY_ONLY_ADMIN_MESSAGE)
    with _state_lock:
        state = _require_state()
        veri_anahtari = _unwrap_with_recovery(state, recovery_key)
        _check_fingerprint(veri_anahtari)
        hesap = _muhurlu_satir(hesap.id, veri_anahtari, giris=True)
        iz_anahtari = _decrypt_audit_key(veri_anahtari)
        # Satırın izi (modül başlığı "SATIRIN İZİ"): eski bir kopyadan geri konmuş satırın
        # parolası kurtarma anahtarıyla da yenilenmez; çıkış yedekten geri yüklemedir. Rol ve
        # durum doğrulanmış (dönen) satırda yeniden sorulur: yukarıdaki ön denetim mühürsüz okumadır.
        hesap = satir_izini_denetle(hesap, veri_anahtari)
        if hesap.role != AccountRole.YONETICI or hesap.status not in (
            AccountStatus.ACIK,
            AccountStatus.PAROLA_YENILENMELI,
        ):
            raise AppPasswordError(_RECOVERY_ONLY_ADMIN_MESSAGE)
        # İki aşamalı özet (modül başlığı): dosyada şu an duran sarmal meşruysa (özeti satırınkini
        # tutuyorsa) kesintide açılabilir kalır; yoksa ya da tutmuyorsa asıl özet değişmez.
        mevcut = _find_wrap(state, hesap.id)
        korunan = _kept_digest(
            hesap, wrap_digest(veri_anahtari, mevcut) if mevcut is not None else None
        )
        yeni_bolum = _account_wrap(
            veri_anahtari,
            hesap_id=hesap.id,
            tanitici=hesap.login_name,
            password=parola,
            kdf=_kdf_of(state),
        )
        yeni_ozet = _own_wrap_digest(veri_anahtari, yeni_bolum)

    def _sarmali_yaz() -> None:
        """Yeni parolanın sarmalı (yoksa eklenir): işlemin sonunda, satırlardan sonra.

        Durum yeniden okunur: `_start_session` sayacı sıfırlamış olabilir; eski okunmuş durum
        onu geri yazardı. Kapalı hesap sarmallarının temizliği bundan SONRA koşar.
        """
        _replace_wrap(_require_state(), yeni_bolum)

    def _kurtarma_yaz(satir: Account) -> None:
        """Satır yazımı ve `KURTARMA` satırı `GIRIS` ile aynı işlemde (`_start_session`)."""
        onceki = denetim_izi.anlik(satir)
        simdi = timezone.now()
        satir.status = AccountStatus.ACIK
        satir.password_changed_at = simdi
        satir.reset_at = simdi
        satir.reset_by = None
        satir.reset_kind = ResetKind.KURTARMA
        satir.reset_notice_pending = True
        ozet_alanlari = set_wrap_digests(satir, asil=yeni_ozet, bekleyen="")
        satir.seal = satir.compute_seal(veri_anahtari)
        satir.save(
            update_fields=[
                "status",
                "password_changed_at",
                "reset_at",
                "reset_by",
                "reset_kind",
                "reset_notice_pending",
                *ozet_alanlari,
                "seal",
            ]
        )
        denetim_izi.kayit(AuditAction.KURTARMA, satir, onceki=onceki, anahtar=iz_anahtari)

    _start_session(
        hesap,
        veri_anahtari,
        iz_anahtari,
        ozet_plani=(korunan, yeni_ozet),
        giris_oncesi=_kurtarma_yaz,
        yeni_sarmal=_sarmali_yaz,
    )
    logger.info("Kurtarma anahtarıyla giriş yapıldı; program yöneticisinin parolası yenilendi.")
    return hesap


def lock() -> None:
    """Oturumu HEMEN kapatır; DEK ve iz anahtarı bellekten düşer (`OTURUM.kapat`).

    Servis içi yollar içindir (geri yükleme sonrası, testler): beklemez, ertelenmez.
    Kullanıcının Kilitle'si ve boşta kilit `OTURUM.kilitle`'dir (uçuştaki istekleri
    bekler, uzun işte ertelenir; `apps.okul.oturum`).
    """
    OTURUM.kapat()


# ---------------------------------------------------------------------------
# Hesap servislerinin dosya ayağı (`services.hesaplar` çağırır)
# ---------------------------------------------------------------------------
@sensitive_variables("password", "data_key", "sarmal")
def write_account_wrap(
    *,
    data_key: bytes,
    hesap_id: object,
    tanitici: str,
    password: str | None = None,
    sarmal: dict[str, Any] | None = None,
) -> None:
    """Hesabın sarmalını dosyaya yazar ya da değiştirir (hesap açma, parola sıfırlama; arşiv önce).

    Hesap servisleri sarmalı ÖNCEDEN kurar (`new_account_wrap`) ve `sarmal` olarak verir: özeti
    yazımdan önce satıra girmiştir (modül başlığı "İKİ AŞAMALI ÖZET"). `sarmal` verilmezse sarmal
    burada `password`'la kurulur — satırı olmayan ya da özeti satıra yazılmayan sarmal (satırı
    olmayan sarmal: iki depo farkı; testler). Verilen sarmalın kimliği `hesap_id`'nin kanonik
    metni olmalıdır.
    """
    if sarmal is None:
        if password is None:
            raise ValueError("Parola ya da kurulmuş sarmal verilmelidir.")
        sarmal = new_account_wrap(data_key, hesap_id=hesap_id, tanitici=tanitici, password=password)
    elif sarmal.get("id") != crypto.canonical_account_id(hesap_id):
        raise ValueError("Sarmalın kimliği hesabınki değil.")
    with _state_lock:
        _replace_wrap(_require_state(), sarmal)


def remove_account_wraps(hesap_idler: set[str]) -> None:
    """Hesapların sarmallarını `guvenlik.json`'dan ve bütün arşivlerden siler (TK11)."""
    _remove_wraps({str(h) for h in hesap_idler})


def clear_failed_attempts(hesap_id: object) -> None:
    """Hatalı deneme sayacını ve askısını kaldırır (askıdan çıkarma; arşivlenmez)."""
    _clear_failures(hesap_id, askidan_cikar=True)


def wrap_ids() -> list[str]:
    """`guvenlik.json`'daki hesap sarmallarının kimlikleri (dosya sırasıyla)."""
    state = _require_state()
    return [str(h.get("id", "")) for h in _accounts_in(state)]


def account_wraps() -> list[dict[str, Any]]:
    """Sarmalların sırsız izdüşümü `[{id, tanitici, askida}]` (dosya sırasıyla; kilit ekranı).

    Tuz ve sarmal dönmez. Dosya yoksa ya da okunamıyorsa boş liste (hata yükseltmez:
    kilit ekranı kayıp ekranına durum ucundan geçer).
    """
    try:
        state = read_state()
    except AppPasswordError:
        return []
    if state is None:
        return []
    return [
        {
            "id": str(h.get("id", "")),
            "tanitici": str(h.get("tanitici", "")),
            "askida": bool(h.get("askida")),
        }
        for h in _accounts_in(state)
    ]


def wrap_is_suspended(hesap_id: object) -> bool:
    """Hesabın sarmalında hatalı deneme askısı var mı? (dosya yoksa ya da sarmal yoksa hayır)"""
    return wrap_failure_state(hesap_id)[1]


def wrap_failure_state(hesap_id: object) -> tuple[int, bool]:
    """Sarmalın hatalı deneme sayacı ve askısı: `(hatali, askida)`; dosya ya da sarmal yoksa (0, False).

    Sayacı ve askıyı kaldıran işlemlerin iz satırı önceki değerleri buradan alır (`sarmal_izi`).
    """
    try:
        state = read_state()
    except AppPasswordError:
        return 0, False
    sarmal = _find_wrap(state, hesap_id) if state is not None else None
    if not sarmal:
        return 0, False
    try:
        hatali = int(sarmal.get("hatali", 0))
    except (TypeError, ValueError):
        hatali = 0
    return hatali, bool(sarmal.get("askida"))
