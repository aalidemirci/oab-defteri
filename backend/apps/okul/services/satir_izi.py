"""Hesap satırının izi — ORM'SİZ okuyucu ve geri yükleme onarımının yazıcısı (kullanıcı kararı
03.11.2026 "Girişte reddet").

SORUN. Hesabın `Account` satırı DEK'le mühürlüdür (tasarım §4.6.1) ve güncel parola kaydının
özetini taşır (`app_password` modül başlığı "SARMALIN TAZELİĞİ"). Mühür satırın BİR ZAMANLAR
program tarafından yazıldığını kanıtlar, BUGÜNKÜ hâli olduğunu kanıtlamaz: veritabanına yazabilen
biri (okulda tek bilgisayar; bir SQLite tarayıcısı yeter, kod gerekmez) satırı mührüyle birlikte
eski bir düz kopyadan (kendi aldığı `db.sqlite3` kopyası ya da `db-onceki-*`) geri koyarsa mühür
tutar, özet o günün sarmalını anlatır ve arşivden geri konan o günün sarmalı o günün parolasıyla
açılırdı (Senaryo 1: geçici parolayla sıfırlanan muhasibin satırı, sahibi parolasını yeniledikten
sonra geri sarılır; rolü düşürülmüş ya da kapatılmış hesabın eski hâli de aynı yoldan döner).

KURAL. Satır denetim izindeki SON içerik MAC'li kaydını tutmalıdır (tasarım §4.6.2 "içerik MAC'i";
`denetim_izi.kaydi_dogrula`'nın mantığı): her meşru `Account` yazımı aynı işlemde satırın SON
hâlinin içerik MAC'ini taşıyan bir iz satırı yazar; eski bir kopyadan geri konan satır, ondan sonra
yazılmış iz satırını tutmaz. Tutmazsa satır mühür uyuşmazlığıyla AYNI muameleyi görür (giriş, oturum
işlemi, kurtarma ve hesap işlemi açılmaz; `app_password.AccountRecordStale`, 409
`hesap_muhru_tutmadi`; `BUTUNLUK` satırının alanı `kayit_mac`; geri yüklemenin parola yolunda
`geri_yukleme_yetkisi.RET_KAYIT_IZI`). Çıkış yedekten geri yüklemedir (zarfın üçüncü durumu).

`hesap_izi_karari` (eşleşen iz satırının sırası ya da retin NEDENİ; `hesap_izi_sirasi` ve
`hesap_izi_tutuyor` onun ince sarmalayıcılarıdır) TEK karar işlevidir: kilit açılışında (DEK
belleğe alınmadan, aday DEK'le), oturumdaki parola doğrulamasında,
hesap servislerinde (`denetim_izi.hesap_izi_tutuyor` Django'nun bağlantısını verir), geri
yüklemenin parola yolunda (`geri_yukleme_yetkisi`; salt okunur `sqlite3`) ve özet onarımında
(`ozet_onarimi`) AYNI işlev koşar; iz boşluğu kararı da burada verilir ("İZ BOŞLUĞU"). Adımları:

1. Satırın içerik MAC'ine giren alanlar (`HESAP_OZET_ALANLARI`; `Account.IZ_OZET_ALANLARI` ile
   birebir, altın listeyle sabit) ham sütunlardan okunur ve ORM'in verdiği değerlere çevrilir
   (`hesap_ozet_alanlari`): ad-soyad verilen DEK'le çözülür (çözülemezse `kanonik.bozuk_alan`,
   ORM'in `CorruptField`'ı gibi), zaman saat dilimli UTC, yabancı anahtar tireli kimlik metni,
   bildirim bayrağı `bool`. Sütunlar `CAST(… AS BLOB)` ile okunur: Django bağlantısının sütun
   türü dönüştürücüleri (`detect_types`) ve metin fabrikası devreye girmez; iki bağlantı aynı
   baytları görür. Biçimsiz değer (geçersiz UTF-8, çözülemeyen zaman, 0/1 dışı bayrak) satırı
   tutmaz sayar (fail-closed).
2. Hesabın iz satırları (`model = "okul.Account"`, `object_id` = kanonik kimlik) EN YENİDEN
   geriye okunur. Okunan HER satırın sırası SQLite'ta tamsayı türünde olmalı, satır açık kipte
   olmalı ve kendi zincir MAC'i, `key_ref`'teki iz anahtarıyla (DEK'le çözülür) tutmalıdır; o
   anahtar satırın sırasında YÜRÜRLÜKTEKİ anahtar olmalıdır (geçerli ilk sırası satırınkine eşit
   ya da küçük olanların en yenisi; `denetim_izi.sirayi_muhurleyen_ia`'nın kuralı). Tutmayan satır
   karşılaştırmayı DÜŞÜRÜR (fail-closed). Böylece son satırın `record_mac`'ini boşaltmak,
   `key_ref`'ini başka bir `AuditKey`'e çevirmek ya da kipini değiştirmek denetimi daha eski bir
   satıra kaydıramaz: o satırın kendi MAC'i bozulur; DEK yenilemesinden (F4) kalan eski bir İA'yı
   bilen biri de satırı o anahtarla yeniden mühürleyemez (yürürlükteki anahtar o değildir).
   TÜR ŞARTI (bağımsız denetim bulgusu): `seq` sütunu `bigint unsigned PRIMARY KEY`'dir, rowid
   takma adı değildir; tamsayı yakınlığı (affinity) yalnız tamsayıya benzeyen METNİ ve tam değerli
   REAL'i tamsayıya çevirir, program dışından yazılmış BLOB, sayıya benzemeyen metin, kesirli REAL
   (NOT NULL kısıtı kaldırılmış bir tabloda NULL da) olduğu gibi saklanır. SQLite'ın sıralaması
   NULL < sayılar (INTEGER ve REAL birlikte, DEĞERLERİYLE) < metin < BLOB'dur. Eski eşleşen satırın
   sırası BLOB'a çevrilseydi (`CAST(seq AS BLOB)` aynı baytları, dolayısıyla aynı zincir MAC'ini
   verir) o satır "en yeni" okunur, hesabın yeni satırları hiç okunmazdı. Bu yüzden yürüyüşte her
   satırın `typeof(seq)`'i okunur, tamsayı olmayan ilk satırda karar "tutmuyor"dur (sorguya tür
   süzgeci KONMAZ: süzgeç yeni satırları BLOB'a çevirip gizlemenin yolu olurdu). Metin ve BLOB
   bütün sayılardan büyük sıralandığı için yürüyüş onları ilk okur; kesirli REAL ise tamsayıların
   ARASINA, değerinin yerine sıralanır: hesabın yeni satırı eşleşen satırın gerisine küçük bir REAL
   değerle (S - 0,5) taşınırsa yürüyüş ona hiç varmaz — onu bütün tabloya bakan tür denetimi yakalar
   ("İZ BOŞLUĞU" (b)). Aynı şart iz anahtarı satırlarının `valid_from_seq`'i için de geçerlidir:
   biçimsiz bir anahtar satırı varsa hiçbir hesabın izi doğrulanamaz.
3. İçerik MAC'i boş satır (kilitlenmenin `KILIT`'i, mühür bulgusunun `BUTUNLUK`'u) atlanır; ilk
   içerik MAC'li satır KARŞILAŞTIRMANIN satırıdır: `record_mac`, satırın bugünkü alanlarının o
   satırı mühürleyen İA ile hesaplanan içerik MAC'ine sabit sürede eşit olmalıdır.
4. Hesabın içerik MAC'li iz satırı HİÇ yoksa satır tutmaz (fail-closed). Meşru hiçbir hâl böyle
   doğmaz: ilk hesap (`enable`) ve her yeni hesap (`hesaplar.open_account`) satırla aynı işlemde
   `HESAP` satırını yazar; geri yüklenen veritabanı kendi izini taşır, onarımın değiştirdiği
   satırlar kendi satırını alır (aşağıda). İz anahtarı ya da iz tablosu okunamıyorsa da satır
   doğrulanamaz: veritabanı hatası çağırana yükselir (geri yükleme yetkisinde "okunamıyor"dur).
5. Çağıran satırı kendisi okuyup ona göre karar veriyorsa (ORM'li denetim noktaları, geri
   yüklemenin satır okuyucusu) okuduğu mührü `beklenen_muhur` olarak verir: ham okumadaki mühür ona
   sabit sürede eşit değilse satır tutmaz sayılır. Mühür kararın bütün alanlarını (rol, durum,
   özetler) kapsadığı için böylece çağıranın kararı verdiği hâl ile izi doğrulanan hâl AYNI hâldir
   (iki okuma arasında satırı değiştiren biri denetimi bir hâlde, kararı öbür hâlde geçiremez).
6. Eşleşen satır bulunduktan sonra, aynı anlık görüntüde, izde BOŞLUK aranır ("İZ BOŞLUĞU"):
   eşleşen satırdan sonra silinmiş ya da sırası değiştirilmiş iz satırı varsa satır tutmaz sayılır.

İZ BOŞLUĞU (kullanıcı kararı 03.11.2026 "Boşluğu engelle"). Adım 2-3'ün yürüyüşü yalnız hesabın
KENDİ iz satırlarını okur. Satırı eski bir kopyadan geri koyan biri hesabın daha yeni iz satırlarını
da silerse, sonrakileri bir aşağı kaydırarak (yeniden numaralayarak) silerse ya da onları eşleşen
eski satırın gerisine taşırsa yürüyüş eski satırı en yeni sanardı. Eşleşen satırın sırası S ise:

(a) SİLME: S'den sonraki satırlar zincir başına dek KESİNTİSİZ olmalıdır: `seq > S` aralığında
    `COUNT(*)` = `COUNT(DISTINCT seq)` = `MAX(seq) - S` (sıranın indeksinde aralık sayımı). (b)
    bütün sıraların tamsayı olduğunu, ilk eşitlik her sıranın TEK olduğunu güvenceler; ikisi
    birlikte S+1…MAX'ın her birinin TAM BİR KEZ bulunması demektir. Silinmiş satırın açtığı boşluk
    tutmaz. Tekillik birincil anahtara BIRAKILMAZ (bağımsız denetim bulgusu): SQLite tarayıcısının
    "tabloyu değiştir" işlemi tabloyu birincil anahtarsız yeniden kurabilir (kod gerekmez); o
    zaman silinen satırların yerine S'den sonraki bir satırın BİREBİR kopyası (aynı sıra, aynı MAC;
    hiçbir satırın kendi MAC'i bozulmaz) `COUNT(*)`'u tamamlardı.
(b) TÜR: tabloda sırası tamsayı olmayan HİÇBİR iz satırı olmamalıdır (`typeof(seq) <> 'integer'`;
    program hiç yazmaz). Hesabın yeni satırı S'nin gerisine bir REAL değerle taşınmışsa (yürüyüş
    ona varmaz) ya da S'den sonraki bir REAL değer (a)'nın sayımını şaşırtacaksa böyle yakalanır.
    Bütün tablo, sıranın kapsayan indeksi üzerinden taranır (ölçüm, Docker'da: 20 000 satırda
    ~0,6 ms, 50 000 satırda ~1,4 ms, 200 000 satırda ~6,5 ms; sayım aynı mertebede).
(c) KAYMA (yeniden numaralama): silinen satırdan sonrakiler `seq = seq - d` ile aşağı kaydırılırsa
    boşluk kalmaz. Ama sıra ve önceki MAC zincir MAC'ine girer (`kanonik.iz_mac`: `seq`
    `IZ_SATIRI_ALANLARI`'ndadır, `prev_mac` sona eklenir): kaydırılan her satırın kendi MAC'i bugünkü
    sırasında tutmaz, ESKİ sırasında (`seq + d`) tutar; bağlar (`prev_mac`) birlikte kaydıkları için
    bozulmaz. Bunu DAYANAK SATIRI gösterir: zincir başından aşağı, programın GİRİŞ OLMADAN yazdığı
    satırlar — kilitli kip satırları (açılıştaki günlük yedek, göç, ertelenen gün işi, kilitliyken
    bütünlük) ve açık kipte `BUTUNLUK` satırları (reddedilen girişin ve doğrulamanın satırları) —
    atlanır; S'den sonraki ilk öteki satır (çoğu kez son oturumun `KILIT` satırı) dayanaktır.
    Dayanağın kendi zincir MAC'i bugünkü sırasında tutmuyor ama `seq + d`'de (1 ≤ d ≤
    `KAYMA_SINIRI`) tutuyorsa satır tutmaz. İA, `key_ref`'teki kayıttan YÜRÜRLÜK ŞARTI OLMADAN
    çözülür (`_IzAnahtarlari.dogrudan`; bağımsız denetim bulgusu): yürürlük kuralı (adım 2) eski
    bir anahtarla yeniden mühürlemeye karşıdır, kaymayı saptamak için gerekmez; uygulansaydı
    program dışından `okul_auditkey`'e eklenen tek bir sahte, emekli satır (geçerli ilk sırası
    S+1; iz satırlarına dokunmadan) dayanağın sırasını ve `seq + d`'leri çözülemeyen o anahtara
    bağlar, kayma araması anahtarsız kalırdı. Yürürlüksüz çözüm yalnız DAHA ÇOK kayma bulur:
    meşru satırın MAC'i kendi sırasında tutar.
    Neden yalnız baş satır değil: program, değişiklikten SONRA kimse girmeden de satır yazar
    (açılıştaki günlük yedeğin kilitli satırı; hatta ilk reddedilen denemenin `BUTUNLUK` satırı);
    yalnız başı doğrulamak kaymayı ilk böyle satırda örterdi ("iki kez dene"). Oturum satırı ise
    ancak başarılı bir girişten sonra yazılır ve her giriş bu denetimden geçer: değişiklikten sonra
    hiçbir giriş açılmadıysa dayanak değişiklikten ÖNCE yazılmış bir satırdır ve silinen bölgenin
    ÜSTÜNDEYSE — silinen bölgeden sonra açık kipte, `BUTUNLUK` dışı bir satır kaldıysa —
    kaydırılmıştır. Açık kip satırlar zincir başına dek silinmiş, üstte yalnız girişsiz satırlar
    (kilitli kip, `BUTUNLUK`) kalmışsa dayanak silinen bölgenin altındadır (ya da yoktur),
    kaydırılmamıştır: kayma görünmez. Bu, açık kip satırlar açısından KUYRUK KESMEDİR ((d); çapa,
    varsa, gösterir).
    Dayanak denetimi FAIL-CLOSED DEĞİLDİR: MAC'i hiçbir sırada tutmayan, `key_ref`'teki anahtarı
    bulunamayan ya da biçimsiz dayanak (program dışından eklenmiş ya da değiştirilmiş satır) kayma
    işareti değildir, girişi engellemez — kilit açılışındaki son 200 satırın doğrulaması onu bulgu
    olarak gösterir (altın kural 3; kullanıcı kararı yalnız silme ve sıra değişikliğini engeller).
    Doğrusal yürüyüş YOKTUR: S ile baş arasındaki satırların MAC'i doğrulanmaz (kullanıcı kararı:
    süre kayıt sayısıyla büyür, ilgisiz bozulma girişi kapatır).
(d) KUYRUK: en yeni satırların (kuyruğun) silinmesi boşluk bırakmaz ve yeni baş meşru, MAC'i
    tutan bir satırdır: bu denetim onu engellemez (orkestratör kararı O-2), çapa (`kuyruk_kesik`,
    `capa_bayat`, `capa_yok`) kartta gösterir. Gerekçe: veritabanı ayarı `synchronous=FULL`'dur
    (`config/settings.py`; WAL'da her commit diske senkronlanır): commit edilmiş işlem elektrik
    kesintisinde NORMALDE kaybolmaz. Ama veritabanının çapanın gerisinde kalması program dışı ve
    kötü niyetsiz hâllerde de doğar — yazma önbelleği senkronu onurlandırmayan disk, program
    kapalıyken silinen ya da kaybolan `-wal` dosyası, veri klasörünün elle eski bir kopyayla
    değiştirilmesi — ve çapa ile veritabanı tek işlemde yazılmaz; kuyruğu kesilmiş veritabanının
    ilk açılışında çapanın tohumuyla yazılan kilitli satır da veritabanından doğrulanamaz. Kuyruk
    kesmeyi engellemek böyle bir hâlde herkesi kilitlerdi.
(e) YANLIŞ ALARM YOK: program sırayı boşluksuz yazar — `denetim_izi._ekle` ve onarımın yazıcısı
    (`hesap_satirlarini_izle`) zincir başının +1'ini, işlemin İÇİNDE ve (Django'da) `BEGIN
    IMMEDIATE` işlemde verir; `AUTOINCREMENT` yoktur, geri alınan işlem numara yakmaz (satırı
    kalmaz, sonraki yazım aynı numarayı alır); tetikleyiciler güncellemeyi ve silmeyi keser;
    kilitli kip satırları (`YEDEK`, `GOC`, `GUN_ISI`, `BUTUNLUK`) da `_ekle`'den geçer; kilitli
    yazımın "kesintisi" (tohum ilerledi, satır yazılmadı) sıra boşluğu bırakmaz (satır hiç sıra
    almadı); geri yükleme veritabanını bütünüyle değiştirir (kendi kesintisiz izini taşır).

RET NEDENİ (orkestratör maddesi C-4; `IzRetNedeni`, `IzKarari`). Karar retin nedenini de taşır:
`SATIR_IZI` (satırın kendisi ya da hesabın KENDİ iz satırları tutmuyor: satır yok ya da biçimsiz,
beklenen mühür değil, iz anahtarı tablosu biçimsiz, içerik MAC'li iz satırı yok, satırın zincir MAC'i
ya da içerik MAC'i tutmuyor) ya da İZ BOŞLUĞU'nun üç hâli — `SILME` ((a)), `TUR` ((b); yürüyüşte
okunan tamsayı olmayan sıra da: program yazmaz, BLOB/metin en yeni sıralanır) ve `KAYMA` ((c); hesabın
KENDİ iz satırının zincir MAC'i bugünkü sırasında tutmayıp `seq + d`'de tutuyorsa da — silinen bölgenin
üstündeki satırı aşağı kaydırılmış hesap). Neden kararı DEĞİŞTİRMEZ (ret yine rettir); yalnız
kullanıcının gördüğü iletiyi ve `BUTUNLUK` satırının alan adını seçer: izden ilgisiz bir satır silinince
son kaydı ondan eski hesapların "kaydı değişmiş" değil "denetim izinden kayıt silinmiş ya da sırası
değiştirilmiş" iletisini görmesi için (`app_password.AuditTrailGap`, alan `iz_boslugu`;
`geri_yukleme_yetkisi.RET_IZ_BOSLUGU`). Kendi satırında kayma araması yalnız ret yolunda koşar (en
çok `KAYMA_SINIRI` HMAC; meşru izde maliyet yok). İçerik MAC'i tutmayan kendi satırından sonra izde
boşluk varsa neden boşluktur (`SILME`, `TUR`, `KAYMA`; ör. hesabın KENDİ son kaydı ortadan
silinmiş, satır bir önceki kaydını tutmaz); satır ayrıca geri sarılmış olabilir, karar aynıdır.
Boşluk yoksa (kuyruk kesme dahil) neden `SATIR_IZI`'dir (F1b-2 (c) alt commit'inin bağımsız
denetim bulgusu).

Kayma denetiminin maliyeti meşru izde birkaç satır okuması ve TEK HMAC'tir; dayanak bozuksa en çok
`KAYMA_SINIRI` HMAC — yalnız değiştirilmiş bir izde. Ölçüm (Docker, hesabın son kaydından sonra
25 000 satır; `test_iz_boslugu_denetiminin_suresi_uzun_izde`): kapsam ölçümü kapalıyken meşru izde
kararın tamamı ~7 ms, bozuk dayanakta ~0,15 sn; kapının biçiminde (`--cov`, dal kapsamı) kayma
araması saf Python döngüsü olduğu için bozuk dayanak ~0,4-0,5 sn. Test duvar saatine değil HMAC
sayısına bağlıdır.

TEK ANLIK GÖRÜNTÜ (`okuma_islemi`; bağımsız denetim bulgusu "yanlış alarm"). Satır, iz anahtarları
ve hesabın iz satırları TEK okuma işleminde okunur: bağlantı bir işlemde değilse `BEGIN … COMMIT`
ile sarılır (Django'nun otomatik commit kipindeki bağlantısı da, geri yüklemenin salt okunur
bağlantıları da), işlemdeyse (Django `atomic`'i) o işlemin anlık görüntüsü kullanılır. Ayrı
deyimler WAL kipinde ayrı anlık görüntüler okurdu: satır okunduktan sonra aynı hesaba commit edilen
meşru bir yazım (satır + son hâlin iz satırı) eski satırı yeni iz satırıyla karşılaştırtır, yanlış
"tutmuyor" kararı silinemez bir `BUTUNLUK` satırı doğururdu. Çağıranın ORM okuması ile bu okuma
arasındaki yarış (beklenen mühür değişmiş) ayrıca `app_password.satir_izini_denetle`'de yazıcılarla
sıralı bir işlemde yinelenen denetimle ayrılır.

KAPSAMIN SINIRI (dürüst; `app_password` modül başlığı "KALAN RİSKLER" (b)). Denetim hesabın KENDİ
iz satırlarının MAC'ini, S'den sonrası için yalnız sıraların kesintisizliğini, tekliğini ve türünü
ve dayanak satırının kaymasını doğrular; aradaki satırların MAC'ini doğrulamaz. Zinciri F1b'de
yalnız kilit açılışı doğrular: son 200 satır (`iz_dogrulama.SON_SATIR`) ve çapa; bulgusu girişi
engellemez (altın kural 3). "Boşluğu engelle" bu ilkenin DAR bir istisnasıdır (kullanıcı kararı 03.11.2026):
hesabın son kaydından sonra izde silinmiş ya da sırası değiştirilmiş satır girişi kapatır; öteki
zincir bulguları kapatmaz. Zincirin tamamını doğrulayan Denetleme Kurulu denetiminin üretim yolu
F3/F4'tedir (plan).

ENGELLENENLER: hesabın son kaydından sonra izin ARASINDAN satır SİLMEK (kuyruk değil: (d); hesabın
kendi satırı da, ilgisiz bir satır da; yeniden numaralamasız; birincil anahtarsız yeniden kurulmuş
tabloda yerine birebir kopya konsa da), silinenden sonrakileri AŞAĞI KAYDIRMAK (silinen bölgeden
sonra açık kipte, `BUTUNLUK` dışı bir satır kaldıysa ve o dayanak satırı bozulmadıysa — o zaman,
değişiklikten sonra giriş açılmadıkça dayanak kaydırılmıştır; iz anahtarı tablosuna eklenen sahte
bir anahtar bunu örtmez), bir satırı REAL bir sıraya taşımak ve tabloda tamsayı olmayan herhangi
bir sıra. Kilit açılışı, oturumdaki parola doğrulaması, kurtarma anahtarıyla açılış, hesap
servisleri, iki depo karşılaştırması, kapalı hesap temizliği, geri yükleme yetkisi (güncel
veritabanı ve görüntü) ve özet onarımının çapası (boşluklu çapa → K-a) bu tek işlevden geçtiği için
hepsi aynı kuralı alır. BEDEL (kullanıcı kararıyla kabul edildi): izden
TEK bir satır silinmişse son kaydı ondan eski BÜTÜN hesaplar reddedilir; çıkış, değişiklikten
önceki bir yedeğin kurtarma anahtarıyla geri yüklenmesidir (parola yolu da güncel veritabanındaki
boşluğu görür).

KALANLAR (kalan risk; girişte görünmez):

* veritabanının BÜTÜNÜYLE (iz dahil) eski bir kopyayla değiştirilmesi: satır kopyanın son iz
  satırını tutar, boşluk yoktur;
* iz kuyruğunun satırla birlikte kesilmesi ("İZ BOŞLUĞU" (d)) — açık kip satırların zincir başına
  dek silinip ardından kalan girişsiz satırların (kilitli kip, `BUTUNLUK`) aşağı kaydırılması da:
  çapa (varsa) kartta gösterir;
* hesabın yeni iz satırlarını silmeden başka kayda ÇEVİRMEK (`model`/`object_id` değişikliği) ya da
  içeriğini değiştirmek; iki satırın sırasını TAMSAYI olarak takas etmek, hesabın yeni satırını
  S'nin gerisinde boş bir tamsayıya taşımak ya da silinen satırın yerine başka bir satırı (kuyruktan
  ya da S'nin gerisinden; kopyasını, boşluğun sırasıyla) koymak: boşluk ve tür sorunu kalmaz;
  taşınan ya da değiştirilen satırın KENDİ MAC'i bozulur — kilit açılışının 200 satırlık
  penceresindeyse `BUTUNLUK` kartı olur, dışındaysa yalnız Denetleme Kurulu modülünün tam zincir
  denetiminde görünür;
* dayanağı bozan (`key_ref`'ini ya da içeriğini; tek hücre yeter) ya da zincir başına program
  dışından açık kipte bir satır ekleyen (tek INSERT; hiçbir satır değişmez, eklenen satır dayanak
  olur ve MAC'i hiçbir sırada tutmaz), `KAYMA_SINIRI`'nı aşan ya da oturum açıkken yapılan
  (oturumun sonraki satırı dayanak olur) kaydırma: kayma işareti vermez, yukarıdaki sınıfa düşer
  (kaydırılan satırların MAC'i bozuktur). Kip ya da tür değiştirerek atlatmak (dayanağı `KILITLI`
  ya da `BUTUNLUK` yapmak) yetmez: bir sonraki açık kip, `BUTUNLUK` dışı satır dayanak olur; silinen
  bölgenin üstündeki BÜTÜN böyle satırların değiştirilmesi gerekir. Biçimsiz bir `key_ref` (sayı
  değil ya da `AZAMI_HANE`'den uzun) kararı istisnayla düşürmez: dayanakta kayma işareti değildir,
  hesabın kendi satırında satırı tutmaz kılar.

Hepsi program dışından, veritabanına yazabilen biri içindir (SQLite tarayıcısı yeter, kod
gerekmez).

ONARIMIN İZİ (`hesap_satirlarini_izle`; K-e). Geri yüklemenin özet onarımı (`ozet_onarimi`)
satırları ORM'siz, takastan ÖNCE `.tmp`'de yazar; o veritabanında oturum yoktur. Değiştirdiği her
satır için AYNI `sqlite3` işleminde zincirin sonuna `SISTEM` `HESAP` satırı eklenir: açık kip,
`key_ref` etkin `AuditKey`'in kimliği (İA verilen DEK'le çözülür), içerik MAC'i satırın onarılmış
hâlinden, zincir MAC'i `kanonik.iz_mac` ile — `denetim_izi._ekle`'nin yazdığıyla BİREBİR (sütun
biçimi Django'nunkidir; eşitlik testte ORM'le sabit). Böylece ilk kilit açılışı onarılan satırı
reddetmez; onarım denetim izinde `SISTEM` `HESAP` satırı olarak kalır (değişen alan adlarıyla:
`wrap_digest`, `wrap_digest_pending`, `seal`, yalnız değişenler; değer yok — özet ve mühür izinli
değer değildir; izi okuma ekranı Denetleme Kurulu modülüyle F4'te gelir) ve satırlar zincir
doğrulamasından bulgusuz geçer. Satırın anı geri yüklemenin anıdır. İA çözülemez ya da zincir başı biçimsizse onarım yazılamaz (`IzYazilamadi`): geri yükleme
yarıda kalır, hiçbir dosya değişmez. Zincir başı onarımın satırlarına kayar; geri yükleme notu
KENARA ALINAN veritabanının zincir başını taşır (değişmez), çapa ilk kilit açılışında yenilenir.

Neden geri yükleme notunda MAC'li bir liste değil: not program dışından değiştirilebilen MAC'siz
bir JSON'dur; listeye güvenmek için DEK'ten türeyen ikinci bir anahtar, notu okuyan her denetim
noktasında (geri yüklemenin parola yolu dahil) bir "bekleyen eşitleme" kuralı ve ilk açılışta ayrı
bir yazım gerekirdi. Satır izi veritabanının kendisinde, onu üreten işlemde durunca bekleyen hâl
yoktur.

Modül yalnız standart kitaplığa, `shared.kanonik`'e ve `shared.crypto`'nun saf işlevlerine dayanır
(Django ayarı, uygulama kaydı ve sorgusu gerekmez); konsol geri yüklemesi onu Django kurulmadan da
kullanır.
"""

from __future__ import annotations

import base64
import binascii
import json
import sqlite3
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Final, Protocol

from cryptography.fernet import InvalidToken

from shared import crypto, kanonik

#: Hesap satırının iz satırlarındaki model etiketi (`denetim_izi.model_etiketi(Account)`).
HESAP_MODELI: Final = "okul.Account"

#: İçerik MAC'ine giren `Account` alanları — `Account.IZ_OZET_ALANLARI` ile BİREBİR (sıra dahil;
#: altın liste `test_satir_izi.py`'de). KURAL: bu kümeyi ya da var olan satırların bu alanlardaki
#: değerini değiştiren her değişiklik (F4'ün DEK yenilemesindeki mühür, özet ve ad-soyad yeniden
#: yazımı dahil), `KAPALI` olanlar DAHİL BÜTÜN `Account` satırlarının izini aynı işlemde yeniden
#: kurmalıdır: her satıra, satırın yeni hâlinin içerik MAC'ini taşıyan ve o sırada yürürlükteki iz
#: anahtarıyla mühürlü bir iz satırı yazılır — ama YALNIZ satır önce ESKİ hâliyle (eski alan
#: kümesi, eski anahtar) son içerik MAC'li kaydını tutuyorsa; tutmayana dokunulmaz (doğrulamasız
#: yeniden kurma geri sarılmış satırı aklardı). Yoksa açık satırların girişi reddedilir, `KAPALI`
#: satırlar "kaydı ya da denetim izi program dışından değiştirilmiş görünen hesaplar" listesine
#: (`seal_mismatch`) düşer ve sarmallarının temizliği durur. Bu yolun yeri F4'tür (DEK yenilemesi):
#: satırın izi kilit açılışında, DEK belleğe alınmadan ve her veri göçünden ÖNCE denetlenir; şema
#: göçü kilitliyken iz yazamaz (`denetim_izi` modül başlığı "ÖZET ALANLARI VE ŞEMA DEĞİŞİMİ").
#: F1c 7. adımda küme hesap bağlarıyla (`person`, `membership`, `term`) genişledi, yeniden kurma
#: yazılmadı (plan "F1c uygulama kararları": F1b deneme kurulumları F1c sürümüyle açılmaz).
HESAP_OZET_ALANLARI: Final[tuple[str, ...]] = (
    "login_name",
    "role",
    "display_name",
    "person",
    "membership",
    "term",
    "status",
    "suspend_reason",
    "opened_at",
    "opened_by",
    "closed_at",
    "closed_by",
    "password_changed_at",
    "reset_at",
    "reset_by",
    "reset_kind",
    "reset_notice_pending",
    "last_login_at",
    "wrap_digest",
    "wrap_digest_pending",
    "seal",
)
#: Türlerine göre alanlar (ham değerin ORM değerine çevrilmesi; `hesap_ozet_alanlari`).
_SIFRELI: Final = frozenset({"display_name"})
_ZAMANLAR: Final = frozenset(
    {"opened_at", "closed_at", "password_changed_at", "reset_at", "last_login_at"}
)
_YABANCI_ANAHTARLAR: Final = frozenset({"opened_by", "closed_by", "reset_by"})
#: Hesap bağları (`oab` modellerinin tamsayı kimlikleri; F1c 7. adım): değer kimliğin ondalık metni.
_TAMSAYI_ANAHTARLAR: Final = frozenset({"person", "membership", "term"})
_MANTIKSALLAR: Final = frozenset({"reset_notice_pending"})

#: Onarımın iz satırının sabitleri (`AuditActor.SISTEM`, `AuditAction.HESAP`,
#: `AuditKeyMode.ACIK`; modeller ORM istediği için değerler burada metindir, eşitliği test sabitler).
AKTOR_SISTEM: Final = "SISTEM"
TUR_HESAP: Final = "HESAP"
KIP_ACIK: Final = "ACIK"
#: Onarımın değiştirebildiği sütunlar, model sırasıyla (iz satırının `changed_fields`'ı).
ONARIM_ALANLARI: Final[tuple[str, ...]] = ("wrap_digest", "wrap_digest_pending", "seal")

#: İz anahtarının uzunluğu (`denetim_izi.IZ_ANAHTARI_BAYT`; eşitliği test sabitler).
IZ_ANAHTARI_BAYT: Final = 32

#: Kayma denetiminde ("İZ BOŞLUĞU" (c)) denenen en büyük sıra farkı: dayanak satırının MAC'i
#: bugünkü sırasında tutmazsa `seq + 1 … seq + KAYMA_SINIRI` denenir. Maliyet yalnız değiştirilmiş
#: izde doğar (her deneme bir HMAC, ~16 µs; sınırda kapsam ölçümü kapalıyken ~0,15 sn). Daha büyük
#: kaydırma (on binden çok satırın silinip yeniden numaralanması) kayma işareti vermez: kalan risk
#: ("KAPSAMIN SINIRI").
KAYMA_SINIRI: Final = 10_000
#: Programın GİRİŞ OLMADAN da yazdığı açık kip satırının türü (`AuditAction.BUTUNLUK`; reddedilen
#: girişin ve kilit açılışındaki doğrulamanın satırı). Kayma denetiminin dayanağı olamaz.
TUR_BUTUNLUK: Final = "BUTUNLUK"
#: SQLite'ın en büyük tamsayısı (64 bit, işaretli). Zincir başının sırası buna ulaşmışsa (program
#: dışından yazılmış; program bu sıraya hiç varmaz) yeni satır sıra alamaz (`+ 1` taşar,
#: `OverflowError`): yazıcılar Türkçe `IzYazilamadi` verir (`hesap_satirlarini_izle`,
#: `denetim_izi._zincir_basi_satiri`; orkestratör kararı O-3'ün uzantısı).
EN_BUYUK_SIRA: Final = 2**63 - 1
#: SQLite tamsayısının en çok ondalık hanesi (`EN_BUYUK_SIRA` 19 hanedir). Daha uzun rakam dizisi
#: hiçbir kimlik ya da sıra değildir; Python'un `int()`'i 4300 haneden uzun metinde `ValueError`
#: verir (dönüşüm sınırı). Program dışından yazılmış böyle bir hücre kararı istisnayla
#: düşürmesin, biçimsiz sayılsın (son sınama bulgusu: zincir başının `key_ref`'i).
AZAMI_HANE: Final = 19


class IzRetNedeni(StrEnum):
    """Satırın izi neden tutmadı? (modül başlığı "RET NEDENİ"). Kararı değiştirmez, iletiyi seçer."""

    #: Satır ya da hesabın kendi iz satırları (adım 1-5).
    SATIR_IZI = "satir_izi"
    #: İZ BOŞLUĞU (a): eşleşen (ya da içerik MAC'i tutmayan) kendi satırından sonra silinmiş (ya da
    #: birebir kopyalanmış) satır.
    SILME = "silme"
    #: İZ BOŞLUĞU (b): tamsayı olmayan sıra (yürüyüşte okunan da).
    TUR = "tur"
    #: İZ BOŞLUĞU (c): aşağı kaydırılmış satır (dayanak ya da hesabın kendi satırı).
    KAYMA = "kayma"

    @property
    def bosluk_mu(self) -> bool:
        """Retin nedeni izdeki bir boşluk mu (silme, tür, kayma)?"""
        return self is not IzRetNedeni.SATIR_IZI


@dataclass(frozen=True)
class IzKarari:
    """`hesap_izi_karari`'nın sonucu: tutuyorsa eşleşen iz satırının sırası, tutmuyorsa neden."""

    sira: int | None
    neden: IzRetNedeni | None = None

    @property
    def tutuyor(self) -> bool:
        return self.sira is not None


#: Satırın kendi izinin tutmadığı karar (en sık ret; nedeni `SATIR_IZI`).
_SATIR_TUTMUYOR: Final = IzKarari(None, IzRetNedeni.SATIR_IZI)


class _Bicimsiz(Exception):
    """Ham değer ORM'in verdiği değere çevrilemiyor: satır tutmaz sayılır (fail-closed)."""


class IzYazilamadi(Exception):
    """Onarımın iz satırı yazılamadı (İA çözülemiyor, zincir başı biçimsiz): onarım yapılmaz."""


class _Imlec(Protocol):
    def fetchall(self) -> list[Any]: ...

    def fetchone(self) -> Any: ...

    def close(self) -> None: ...


class Baglanti(Protocol):
    """`sqlite3.Connection` biçiminde bağlantı (`execute(sql, parametreler)` → imleç; açık bir
    işlemin içinde mi)."""

    @property
    def in_transaction(self) -> bool: ...

    def execute(self, sql: str, parameters: Sequence[Any] = ..., /) -> _Imlec: ...


@contextmanager
def okuma_islemi(baglanti: Baglanti) -> Iterator[None]:
    """Okumaları TEK bir okuma işleminde (tek anlık görüntü) toplar (modül başlığı "TEK ANLIK
    GÖRÜNTÜ").

    Bağlantı zaten bir işlemdeyse (Django `atomic`'i, çağıranın açtığı işlem) hiçbir şey eklemez:
    okumalar o işlemin anlık görüntüsündedir. Değilse `BEGIN` (ertelenmiş; salt okunur `mode=ro`
    bağlantıda da çalışır) gönderilir ve çıkışta işlem kapatılır — hata yolunda `ROLLBACK`; Django'nun
    otomatik commit kipindeki bağlantısında açık işlem kalmaz. Gövde yalnız okur.
    """
    if baglanti.in_transaction:
        yield
        return
    baglanti.execute("BEGIN")
    try:
        yield
    except BaseException:
        if baglanti.in_transaction:
            with suppress(sqlite3.Error):
                baglanti.execute("ROLLBACK")
        raise
    if baglanti.in_transaction:
        baglanti.execute("COMMIT")


# ---------------------------------------------------------------------------
# Ham değerlerin çevrilmesi
# ---------------------------------------------------------------------------
def _metin(ham: object) -> str:
    """`CAST(… AS BLOB)` baytlarının metni (katı UTF-8); bayt değilse ya da çözülmezse `_Bicimsiz`."""
    if not isinstance(ham, bytes):
        raise _Bicimsiz
    try:
        return ham.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _Bicimsiz from exc


def _metin_ya_da_none(ham: object) -> str | None:
    return None if ham is None else _metin(ham)


def _zaman(ham: object) -> datetime | None:
    """Django'nun saat dilimsiz UTC metni → saat dilimli zaman (ORM'in dönüştürücüsü gibi)."""
    if ham is None:
        return None
    try:
        an = datetime.fromisoformat(_metin(ham))
    except ValueError as exc:
        raise _Bicimsiz from exc
    return an.replace(tzinfo=UTC) if an.tzinfo is None else an


def _kimlik_metni(ham: object) -> str | None:
    """Ham kimlik (tiresiz 32 hane) → tireli UUID metni; boşsa None."""
    if ham is None:
        return None
    try:
        return str(uuid.UUID(_metin(ham)))
    except ValueError as exc:
        raise _Bicimsiz from exc


def _tamsayi_kimlik_metni(ham: object) -> str | None:
    """Ham tamsayı kimlik (`CAST(… AS BLOB)`: ondalık rakamlar) → kimliğin metni; boşsa None.

    ORM'in yabancı anahtar değeri `str(pk)`'dir (`denetim_izi._alan_degeri`): baştaki sıfır, işaret
    ya da rakam dışı karakter taşıyan bayt (program dışından metin ya da BLOB yazılmış) o metne
    eşit olamaz, `_Bicimsiz`'dir (fail-closed)."""
    if ham is None:
        return None
    metin = _metin(ham)
    if (
        not metin.isascii()
        or not metin.isdigit()
        or len(metin) > AZAMI_HANE
        or str(int(metin)) != metin
    ):
        raise _Bicimsiz
    return metin


def _mantiksal(ham: object) -> bool:
    if ham == b"1":
        return True
    if ham == b"0":
        return False
    raise _Bicimsiz


def _tamsayi(ham: object) -> int:
    metin = _metin(ham)
    if not metin.isascii() or not metin.isdigit() or len(metin) > AZAMI_HANE:
        raise _Bicimsiz
    return int(metin)


def _sifreli(ham: object, dek: bytes) -> object:
    """Şifreli alanın ORM değeri: boşsa olduğu gibi, çözülürse metin, çözülmezse bozuk temsil.

    `crypto.EncryptedTextField.from_db_value` ve `denetim_izi._alan_degeri` ile aynı kural
    (kilit açıkken katı kip; `CorruptField` → `kanonik.bozuk_alan(ham)`).
    """
    if ham is None:
        return None
    token = _metin(ham)
    if token == "":
        return ""
    try:
        return crypto.decrypt_with(dek, token).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError):
        return kanonik.bozuk_alan(token)


def hesap_ozet_alanlari(ham: Sequence[Any], dek: bytes) -> dict[str, Any]:
    """`_hesap_satiri`'nın satırını içerik MAC'inin alanlarına çevirir (ORM'in değerleriyle aynı).

    Biçimsiz değer `_Bicimsiz` yükseltir (çağıran "tutmuyor" sayar).
    """
    alanlar: dict[str, Any] = {}
    for alan, deger in zip(HESAP_OZET_ALANLARI, ham, strict=True):
        if alan in _SIFRELI:
            alanlar[alan] = _sifreli(deger, dek)
        elif alan in _ZAMANLAR:
            alanlar[alan] = _zaman(deger)
        elif alan in _YABANCI_ANAHTARLAR:
            alanlar[alan] = _kimlik_metni(deger)
        elif alan in _TAMSAYI_ANAHTARLAR:
            alanlar[alan] = _tamsayi_kimlik_metni(deger)
        elif alan in _MANTIKSALLAR:
            alanlar[alan] = _mantiksal(deger)
        else:
            alanlar[alan] = _metin_ya_da_none(deger)
    return alanlar


#: Hesap bağı sütunları F1c 7. adımda geldi (`okul.0004`); sütunları olmayan eski görüntüde NULL
#: okunur (`hesap_bag_sutunlari_var`).
HESAP_BAG_SUTUNLARI: Final = ("person_id", "membership_id", "term_id")
_HESAP_BAG_SECIMI: Final = (
    "CAST(person_id AS BLOB), CAST(membership_id AS BLOB), CAST(term_id AS BLOB), "
)
_HESAP_BAGSIZ_SECIM: Final = "NULL, NULL, NULL, "


def hesap_bag_sutunlari_var(baglanti: Baglanti) -> bool:
    """`okul_account` hesap bağı sütunlarını taşıyor mu? (`okul.0004`'ten önceki görüntüde yoktur.)

    Üçü birlikte gelir: biri eksikse görüntü biçimsizdir, bağ sütunları yok sayılmaz — sorgu eksik
    sütunda `sqlite3` hatası verir (çağıranın okunamama hâli)."""
    (adet,) = baglanti.execute(
        "SELECT COUNT(*) FROM pragma_table_info('okul_account') "
        "WHERE name IN ('person_id', 'membership_id', 'term_id')"
    ).fetchone()
    return bool(adet)


def _hesap_satiri(baglanti: Baglanti, kimlik: str) -> Sequence[Any] | None:
    """Hesabın ham satırı (`HESAP_OZET_ALANLARI` sırası, `CAST(… AS BLOB)`); yoksa ya da birden
    çoksa None. Sorgu kaynakta sabit metinlerden kurulan bir `SELECT`'tir (izsiz yazım taraması
    salt okuma sayar); sütun sırasını `test_satir_izi.py` `HESAP_OZET_ALANLARI`'yla karşılaştırır.

    Geri yüklenecek görüntü `okul.0004`'ten önce üretilmiş olabilir (plan F1c 7. adım): bağ
    sütunları yoksa NULL okunur. O görüntünün satırları bağsızdır; içerik MAC'leri eski kümeyle
    yazıldığı için satırın izi tutmaz (fail-closed; F1b deneme kurulumları açılmaz, plan "F1c
    uygulama kararları")."""
    bag = _HESAP_BAG_SECIMI if hesap_bag_sutunlari_var(baglanti) else _HESAP_BAGSIZ_SECIM
    satirlar = baglanti.execute(
        "SELECT CAST(login_name AS BLOB), CAST(role AS BLOB), CAST(display_name AS BLOB), "  # noqa: S608 — sabit metinler
        f"{bag}"
        "CAST(status AS BLOB), CAST(suspend_reason AS BLOB), CAST(opened_at AS BLOB), "
        "CAST(opened_by_id AS BLOB), CAST(closed_at AS BLOB), CAST(closed_by_id AS BLOB), "
        "CAST(password_changed_at AS BLOB), CAST(reset_at AS BLOB), CAST(reset_by_id AS BLOB), "
        "CAST(reset_kind AS BLOB), CAST(reset_notice_pending AS BLOB), "
        "CAST(last_login_at AS BLOB), CAST(wrap_digest AS BLOB), "
        "CAST(wrap_digest_pending AS BLOB), CAST(seal AS BLOB) FROM okul_account WHERE id = ?",
        (uuid.UUID(kimlik).hex,),
    ).fetchall()
    return satirlar[0] if len(satirlar) == 1 else None


# ---------------------------------------------------------------------------
# İz satırı ve iz anahtarı
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _IzSatiri:
    seq: int
    alanlar: dict[str, Any]
    record_mac: str
    key_mode: str
    key_ref: str
    prev_mac: str
    mac: str


#: `_iz_satirlari`'nın sütunları (`_iz_satiri`'nın sırası; baştaki sütun "sıra tamsayı mı?").
_IZ_SUTUNLARI: Final = (
    "typeof(seq) = 'integer', "
    'CAST(seq AS BLOB), CAST("at" AS BLOB), CAST(actor AS BLOB), '
    "CAST(account_id AS BLOB), CAST(role AS BLOB), CAST(action AS BLOB), "
    "CAST(model AS BLOB), CAST(object_id AS BLOB), CAST(changed_fields AS BLOB), "
    'CAST("values" AS BLOB), CAST(record_mac AS BLOB), CAST(label AS BLOB), '
    "CAST(key_mode AS BLOB), CAST(key_ref AS BLOB), CAST(prev_mac AS BLOB), CAST(mac AS BLOB)"
)
#: Dönem ve uyum bağı sütunları F1c-3'te geldi (`okul.0002`); yoksa NULL okunur.
_IZ_BAG_SUTUNLARI: Final = ", CAST(term_id AS BLOB), CAST(compliance_item_id AS BLOB)"
_IZ_BAGSIZ_SUTUNLAR: Final = ", NULL, NULL"


def _iz_satirlari(baglanti: Baglanti, kosul: str, degerler: Sequence[Any]) -> Any:
    """Denetim izi satırları, en yeniden geriye (`_iz_satiri`'nın okuduğu biçim; salt okuma).

    `kosul` bu modüldeki iki sabittir. Geri yüklenecek görüntü `okul.0002`'den önce üretilmiş
    olabilir (plan F1c-7): sütunları o yüzden önce sorulur.
    """
    (bag_sutunu,) = baglanti.execute(
        "SELECT COUNT(*) FROM pragma_table_info('okul_audittrail') "
        "WHERE name IN ('term_id', 'compliance_item_id')"
    ).fetchone()
    bag = _IZ_BAG_SUTUNLARI if bag_sutunu == 2 else _IZ_BAGSIZ_SUTUNLAR
    return baglanti.execute(
        f"SELECT {_IZ_SUTUNLARI}{bag} FROM okul_audittrail "  # noqa: S608 — sabit metinler
        f"WHERE {kosul} ORDER BY seq DESC",
        degerler,
    )


def _iz_satiri(ham: Sequence[Any]) -> _IzSatiri:
    """`hesap_izi_sirasi`'nın iz sorgusunun satırı (tür sütunu hariç) → zincir MAC'inin alanları
    (`denetim_izi.satir_alanlari` ile aynı).

    `term` ve `compliance_item` F1c-3'te geldi: sorgunun son iki sütunudur (`_iz_satirlari`);
    sütunları olmayan eski görüntüde ikisi de None'dır. `denetim_izi.satir_alanlari` ile birlikte
    değişir.
    """
    (
        seq_ham,
        an_ham,
        aktor,
        hesap,
        rol,
        tur,
        model,
        kimlik,
        degisen,
        degerler,
        record_mac,
        etiket,
        kip,
        key_ref,
        prev_mac,
        mac,
        donem,
        uyum_satiri,
    ) = ham
    seq = _tamsayi(seq_ham)
    an = _zaman(an_ham)
    if an is None:
        raise _Bicimsiz
    try:
        degisen_alanlar = json.loads(_metin(degisen))
        deger_sozlugu = json.loads(_metin(degerler))
    except (ValueError, RecursionError) as exc:
        raise _Bicimsiz from exc
    alanlar = {
        "seq": seq,
        "at": an,
        "actor": _metin(aktor),
        "account": _kimlik_metni(hesap),
        "role": _metin(rol),
        "action": _metin(tur),
        "model": _metin(model),
        "object_id": _metin(kimlik),
        "term": _metin_ya_da_none(donem),
        "changed_fields": degisen_alanlar,
        "values": deger_sozlugu,
        "record_mac": _metin(record_mac),
        "compliance_item": _metin_ya_da_none(uyum_satiri),
        "label": _metin(etiket),
        "key_mode": _metin(kip),
        "key_ref": _metin(key_ref),
    }
    return _IzSatiri(
        seq=seq,
        alanlar=alanlar,
        record_mac=alanlar["record_mac"],
        key_mode=alanlar["key_mode"],
        key_ref=alanlar["key_ref"],
        prev_mac=_metin(prev_mac),
        mac=_metin(mac),
    )


def _ia_coz(token: str, dek: bytes) -> bytes | None:
    """`AuditKey.key` belirtecini DEK'le çözer (`denetim_izi._token_coz` ile aynı); olmazsa None."""
    try:
        ia = base64.b64decode(crypto.decrypt_with(dek, token), validate=True)
    except (InvalidToken, UnicodeEncodeError, binascii.Error, ValueError):
        return None
    return ia if len(ia) == IZ_ANAHTARI_BAYT else None


class _IzAnahtarlari:
    """`AuditKey` satırları (küçük tablo; bir kez okunur) ve çözülmüş İA'lar (önbellekte).

    Kimliği ya da geçerli ilk sırası SQLite'ta tamsayı türünde olmayan (program dışından BLOB ya da
    metin yazılmış) ya da çevrilemeyen bir satır varsa `bozuk`'tur: yürürlük kuralı güvenilir
    değildir, hiçbir hesabın izi doğrulanmaz (fail-closed; modül başlığı adım 2, "TÜR ŞARTI").
    """

    def __init__(self, baglanti: Baglanti, dek: bytes) -> None:
        self._dek = dek
        self.bozuk = False
        self._kayitlar: dict[int, tuple[bytes | None, int]] = {}
        for tamsayi_mi, ham_id, ham_key, ham_gecerli in baglanti.execute(
            "SELECT typeof(id) = 'integer' AND typeof(valid_from_seq) = 'integer', "
            "CAST(id AS BLOB), CAST(key AS BLOB), CAST(valid_from_seq AS BLOB) FROM okul_auditkey"
        ).fetchall():
            try:
                if tamsayi_mi != 1:
                    raise _Bicimsiz
                kayit_id = _tamsayi(ham_id)
                gecerli = _tamsayi(ham_gecerli)
            except _Bicimsiz:
                self.bozuk = True
                continue
            self._kayitlar[kayit_id] = (ham_key if isinstance(ham_key, bytes) else None, gecerli)
        self._cozulen: dict[int, bytes | None] = {}

    def _yururlukteki(self, seq: int) -> int | None:
        """`seq` satırını mühürlemesi gereken anahtar: geçerli ilk sırası `seq`'e eşit ya da küçük
        olanların EN YENİSİ (`denetim_izi.sirayi_muhurleyen_ia` ile aynı kural)."""
        adaylar = [
            (gecerli, kayit_id)
            for kayit_id, (_, gecerli) in self._kayitlar.items()
            if gecerli <= seq
        ]
        return max(adaylar)[1] if adaylar else None

    def satirin(self, key_ref: str, seq: int) -> bytes | None:
        """Açık kip satırını mühürleyen İA: `key_ref` ASCII ondalık kimlik, kayıt var, DEK'le
        çözülüyor ve satırın sırasında YÜRÜRLÜKTEKİ anahtar odur; değilse None.

        Yürürlük şartı `denetim_izi._acik_zincir_anahtarlari`'nın "satır anahtarın geçerli ilk
        sırasından önce olamaz" kuralından katıdır: DEK yenilemesinden (TK12, F4) kalan eski bir
        İA'yı bilen biri, yenilemeden sonraki bir satırı o anahtarla yeniden mühürleyip (`key_ref`,
        `record_mac` ve `mac` birlikte) eski bir hâli aklatamasın. Program her satırı yürürlükteki
        (etkin) anahtarla yazar.
        """
        kayit_id = _anahtar_kimligi(key_ref)
        if kayit_id is None or self._yururlukteki(seq) != kayit_id:
            return None
        return self._coz(kayit_id)

    def dogrudan(self, key_ref: str) -> bytes | None:
        """`key_ref`'teki kaydın İA'sı, YÜRÜRLÜK ŞARTI OLMADAN; kayıt yoksa ya da çözülmüyorsa None.

        Yalnız kayma araması içindir (modül başlığı "İZ BOŞLUĞU" (c)): yürürlük kuralı eski bir
        anahtarla yeniden mühürlemeye karşıdır, kaymayı saptamak için gerekmez. Uygulansaydı program
        dışından eklenen tek bir sahte, emekli `AuditKey` satırı (geçerli ilk sırası S+1) dayanağın
        sırasını ve `seq + d`'leri o anahtara bağlar, arama anahtarsız kalırdı (bağımsız denetim
        bulgusu). Bu çözüm yalnız DAHA ÇOK kayma bulur: meşru satırın MAC'i kendi sırasında tutar.
        """
        kayit_id = _anahtar_kimligi(key_ref)
        return None if kayit_id is None else self._coz(kayit_id)

    def _coz(self, kayit_id: int) -> bytes | None:
        """Kaydın İA'sı (önbellekte); kayıt yoksa ya da DEK'le çözülmüyorsa None."""
        kayit = self._kayitlar.get(kayit_id)
        if kayit is None:
            return None
        if kayit_id not in self._cozulen:
            ia: bytes | None = None
            if kayit[0] is not None:
                try:
                    ia = _ia_coz(_metin(kayit[0]), self._dek)
                except _Bicimsiz:
                    ia = None
            self._cozulen[kayit_id] = ia
        return self._cozulen[kayit_id]


def _anahtar_kimligi(key_ref: str) -> int | None:
    """Açık kip satırının `key_ref`'i ASCII ondalık bir kimlikse (en çok `AZAMI_HANE` hane) o
    kimlik; değilse None."""
    if not key_ref or not (key_ref.isascii() and key_ref.isdigit()) or len(key_ref) > AZAMI_HANE:
        return None
    return int(key_ref)


def _mac_tutuyor(
    ia: bytes, satir: _IzSatiri, *, seq: int | None = None, zincir: bytes | None = None
) -> bool:
    """Satırın zincir MAC'i İA'nın zincir anahtarıyla yeniden hesaplanınca tutuyor mu?

    `seq` verilirse MAC satırın o sırada yazıldığı varsayılarak hesaplanır (kayma denetimi;
    "İZ BOŞLUĞU" (c)); verilmezse satırın bugünkü sırası. `zincir` İA'nın önceden türetilmiş
    zincir anahtarıdır (kayma denetiminin döngüsünde her denemede yeniden türetilmesin).
    """
    alanlar = satir.alanlar if seq is None else {**satir.alanlar, "seq": seq}
    anahtar = crypto.audit_chain_key(ia) if zincir is None else zincir
    try:
        beklenen = kanonik.iz_mac(anahtar, alanlar, satir.prev_mac)
    except kanonik.KanonikHata:
        return False
    return kanonik.esit(satir.mac, beklenen)


# ---------------------------------------------------------------------------
# Karar
# ---------------------------------------------------------------------------
def kanonik_kimlik(hesap_id: object) -> str | None:
    """Hesap kimliğinin tireli metni (iz satırının `object_id`'si); UUID değilse None."""
    try:
        return str(hesap_id if isinstance(hesap_id, uuid.UUID) else uuid.UUID(str(hesap_id)))
    except ValueError:
        return None


def hesap_izi_tutuyor(
    baglanti: Baglanti, hesap_id: object, dek: bytes, *, beklenen_muhur: str | None = None
) -> bool:
    """Hesap satırı denetim izindeki son içerik MAC'li kaydını tutuyor mu? (modül başlığı)

    `hesap_izi_karari(...).tutuyor`; ayrıntılar orada.
    """
    return hesap_izi_karari(baglanti, hesap_id, dek, beklenen_muhur=beklenen_muhur).tutuyor


def hesap_izi_sirasi(
    baglanti: Baglanti, hesap_id: object, dek: bytes, *, beklenen_muhur: str | None = None
) -> int | None:
    """Satırın tuttuğu (eşleştiği) iz satırının sırası; tutmuyorsa None (`hesap_izi_karari`).

    Sıra, geri yüklemenin özet onarımında çapanın soyunu sınar (`ozet_onarimi` modül başlığı
    "SIRA KURALI").
    """
    return hesap_izi_karari(baglanti, hesap_id, dek, beklenen_muhur=beklenen_muhur).sira


def hesap_izi_karari(
    baglanti: Baglanti, hesap_id: object, dek: bytes, *, beklenen_muhur: str | None = None
) -> IzKarari:
    """TEK karar (modül başlığı): satırın tuttuğu iz satırının sırası ya da retin nedeni.

    Satır yoksa, biçimsizse, mührü verilen `beklenen_muhur`'a eşit değilse (adım 5), hesabın okunan
    bir iz satırının zincir MAC'i tutmuyorsa, iz anahtarı tablosunda biçimsiz satır varsa ya da
    içerik MAC'li iz satırı yoksa ret, neden `SATIR_IZI`; hesabın okunan bir iz satırının sırası
    tamsayı değilse ya da eşleşen satırdan sonra izde boşluk varsa (adım 6, "İZ BOŞLUĞU") ret, neden
    boşluğun türü (`SILME`, `TUR`, `KAYMA`; zincir MAC'i tutmayan kendi satırı aşağı kaydırılmışsa
    da `KAYMA`); içerik MAC'i tutmayan kendi satırından sonra izde boşluk varsa da neden boşluğun
    türüdür ("RET NEDENİ"). Fail-closed: her şüphede ret. Bütün okumalar tek anlık görüntüdedir
    (`okuma_islemi`). Hiçbir şey yazmaz. Veritabanı hatası (tablo yok, dosya kilitli) çağırana
    yükselir.
    """
    kimlik = kanonik_kimlik(hesap_id)
    if kimlik is None:
        return _SATIR_TUTMUYOR
    with okuma_islemi(baglanti):
        return _karar(baglanti, kimlik, dek, beklenen_muhur)


def _karar(baglanti: Baglanti, kimlik: str, dek: bytes, beklenen_muhur: str | None) -> IzKarari:
    """`hesap_izi_karari`'nın gövdesi; çağıran okuma işlemini açmıştır."""
    ham = _hesap_satiri(baglanti, kimlik)
    if ham is None:
        return _SATIR_TUTMUYOR
    try:
        alanlar = hesap_ozet_alanlari(ham, dek)
    except _Bicimsiz:
        return _SATIR_TUTMUYOR
    if beklenen_muhur is not None and not kanonik.esit(alanlar["seal"], beklenen_muhur):
        return _SATIR_TUTMUYOR  # çağıranın kararı verdiği hâl bu hâl değil (adım 5)
    anahtarlar = _IzAnahtarlari(baglanti, dek)
    if anahtarlar.bozuk:
        return _SATIR_TUTMUYOR
    imlec = _iz_satirlari(baglanti, "model = ? AND object_id = ?", (HESAP_MODELI, kimlik))
    eslesen: int
    try:
        while True:
            satir_ham = imlec.fetchone()
            if satir_ham is None:
                return _SATIR_TUTMUYOR  # içerik MAC'li iz satırı yok (adım 4)
            if satir_ham[0] != 1:
                # Sırası tamsayı değil: metin/BLOB en yeni sıralanır (adım 2). Program yazmaz;
                # "İZ BOŞLUĞU" (b)'nin tablo taramasıyla aynı hâl.
                return IzKarari(None, IzRetNedeni.TUR)
            try:
                satir = _iz_satiri(satir_ham[1:])
            except _Bicimsiz:
                return _SATIR_TUTMUYOR
            ia = anahtarlar.satirin(satir.key_ref, satir.seq)
            if satir.key_mode != KIP_ACIK or ia is None or not _mac_tutuyor(ia, satir):
                # Hesabın satırı program dışından değişmiş (adım 2) — ya da aşağı kaydırılmış:
                # zincir MAC'i eski sırasında tutuyorsa neden kaymadır ("RET NEDENİ").
                if satir.key_mode == KIP_ACIK and _kaymis_mi(anahtarlar, satir):
                    return IzKarari(None, IzRetNedeni.KAYMA)
                return _SATIR_TUTMUYOR
            if not satir.record_mac:
                continue
            try:
                guncel = kanonik.kayit_mac(
                    crypto.record_summary_key(ia), HESAP_MODELI, kimlik, alanlar
                )
            except kanonik.KanonikHata:
                return _SATIR_TUTMUYOR
            if not kanonik.esit(satir.record_mac, guncel):
                # Satır bu kaydı tutmuyor. Ondan sonra izde boşluk varsa (ör. hesabın KENDİ son
                # kaydı ortadan silinmiş) değişen denetim izidir: neden boşluğun türüdür ("RET
                # NEDENİ"; orkestratör maddesi C-4). Yalnız ret yolunda koşar; karar aynıdır.
                bosluk = _iz_boslugu_nedeni(baglanti, anahtarlar, satir.seq)
                return _SATIR_TUTMUYOR if bosluk is None else IzKarari(None, bosluk)
            eslesen = satir.seq
            break
    finally:
        imlec.close()
    neden = _iz_boslugu_nedeni(baglanti, anahtarlar, eslesen)
    return IzKarari(eslesen) if neden is None else IzKarari(None, neden)


def _iz_boslugu_nedeni(
    baglanti: Baglanti, anahtarlar: _IzAnahtarlari, sira: int
) -> IzRetNedeni | None:
    """Eşleşen satırdan (`sira`) sonra izde boşluk varsa türü, yoksa None (modül başlığı "İZ
    BOŞLUĞU").

    (b) tür, (a) silme, (c) kayma; sıra (b) → (a) → (c)'dir: (a)'nın sayımı ancak bütün sıralar
    tamsayıysa kesintisizliği kanıtlar. Çağıranın okuma işlemindedir (tek anlık görüntü).
    """
    (bicimsiz_var,) = baglanti.execute(
        "SELECT EXISTS (SELECT 1 FROM okul_audittrail WHERE typeof(seq) <> 'integer')"
    ).fetchone()
    if bicimsiz_var != 0:
        return IzRetNedeni.TUR  # (b) tamsayı olmayan sıra: program yazmaz
    adet, farkli, en_buyuk = baglanti.execute(
        "SELECT COUNT(*), COUNT(DISTINCT seq), MAX(seq) FROM okul_audittrail WHERE seq > ?",
        (sira,),
    ).fetchone()
    beklenen = 0 if en_buyuk is None else en_buyuk - sira
    if not all(isinstance(sayi, int) for sayi in (adet, farkli, beklenen)):
        return IzRetNedeni.TUR  # sayım tamsayı değil: (b)'den sonra olmaz, savunma
    if not adet == farkli == beklenen:
        return IzRetNedeni.SILME  # (a) S'den sonra silinmiş satır (ya da yerine konmuş kopya)
    return IzRetNedeni.KAYMA if _dayanak_kaymis(baglanti, anahtarlar, sira) else None


def _kaymis_mi(anahtarlar: _IzAnahtarlari, satir: _IzSatiri) -> bool:
    """Açık kip satırın zincir MAC'i bugünkü sırasında tutmayıp `seq + d`'de (1 ≤ d ≤
    `KAYMA_SINIRI`) tutuyor mu? (modül başlığı "İZ BOŞLUĞU" (c), "RET NEDENİ")

    İA `key_ref`'teki kayıttan yürürlük şartı OLMADAN çözülür (`_IzAnahtarlari.dogrudan`): sahte,
    emekli bir anahtar satırı aramayı anahtarsız bırakamaz. Anahtar bulunamıyor ya da çözülmüyorsa,
    MAC bugünkü sırasında tutuyorsa ya da hiçbir sırada tutmuyorsa kayma YOKTUR.
    """
    ia = anahtarlar.dogrudan(satir.key_ref)
    if ia is None:
        return False  # anahtarı bulunamıyor: kayma işareti değil
    zincir = crypto.audit_chain_key(ia)
    if _mac_tutuyor(ia, satir, zincir=zincir):
        return False
    return any(
        _mac_tutuyor(ia, satir, seq=satir.seq + kayma, zincir=zincir)
        for kayma in range(1, KAYMA_SINIRI + 1)
    )


def _dayanak_kaymis(baglanti: Baglanti, anahtarlar: _IzAnahtarlari, sira: int) -> bool:
    """Dayanak satırı aşağı kaydırılmış mı? (modül başlığı "İZ BOŞLUĞU" (c))

    Zincir başından aşağı, `sira`'dan sonraki satırlar okunur; programın giriş olmadan yazdığı
    satırlar (kilitli kip ya da açık kipte `BUTUNLUK`) atlanır. İlk öteki satır dayanaktır: açık
    kipteyse ve MAC'i bugünkü sırasında tutmayıp `seq + d`'de (1 ≤ d ≤ `KAYMA_SINIRI`) tutuyorsa
    kaymıştır. İA `key_ref`'teki kayıttan yürürlük şartı OLMADAN çözülür
    (`_IzAnahtarlari.dogrudan`): sahte, emekli bir anahtar satırı aramayı anahtarsız bırakamaz.
    Dayanak yoksa, biçimsizse, `key_ref`'teki anahtar bulunamıyor ya da çözülmüyorsa ya da MAC'i
    hiçbir sırada tutmuyorsa kayma işareti YOKTUR (fail-closed değildir: bozuk satır girişi
    kapatmaz).
    """
    imlec = _iz_satirlari(baglanti, "seq > ?", (sira,))
    acik = KIP_ACIK.encode("ascii")
    butunluk = TUR_BUTUNLUK.encode("ascii")
    dayanak_ham: Sequence[Any] | None = None
    try:
        while dayanak_ham is None:
            satir_ham = imlec.fetchone()
            if satir_ham is None:
                return False  # S'den sonra yalnız girişsiz satırlar var
            # Sütunlar: 0 tür, 6 action, 13 key_mode (`_iz_satiri`'nın sırası, bir kaydırmalı).
            if satir_ham[13] == acik and satir_ham[6] != butunluk:
                dayanak_ham = satir_ham
    finally:
        imlec.close()
    try:
        dayanak = _iz_satiri(dayanak_ham[1:])
    except _Bicimsiz:
        return False
    return _kaymis_mi(anahtarlar, dayanak)


# ---------------------------------------------------------------------------
# Onarımın izi (yazıcı; modül başlığı "ONARIMIN İZİ")
# ---------------------------------------------------------------------------
def _etkin_anahtar(baglanti: Baglanti, dek: bytes) -> tuple[int, bytes]:
    """Etkin (emekli olmamış, en yeni) iz anahtarı: (kimlik, İA); `denetim_izi._etkin_kayit` gibi."""
    kayit = baglanti.execute(
        "SELECT CAST(id AS BLOB), CAST(key AS BLOB) FROM okul_auditkey "
        "WHERE retired_at IS NULL ORDER BY valid_from_seq DESC LIMIT 1"
    ).fetchone()
    if kayit is None:
        raise IzYazilamadi("Geri yüklenen veritabanında etkin iz anahtarı yok.")
    try:
        kayit_id = _tamsayi(kayit[0])
        ia = _ia_coz(_metin(kayit[1]), dek)
    except _Bicimsiz as exc:
        raise IzYazilamadi("Geri yüklenen veritabanının iz anahtarı biçimsiz.") from exc
    if ia is None:
        raise IzYazilamadi("Geri yüklenen veritabanının iz anahtarı bu DEK'le çözülemedi.")
    return kayit_id, ia


def django_zamani(an: datetime) -> str:
    """Django'nun SQLite'a yazdığı zaman metni: saat dilimsiz UTC, `str(datetime)`."""
    return str(an.astimezone(UTC).replace(tzinfo=None))


def hesap_satirlarini_izle(
    baglanti: Baglanti,
    degisenler: Mapping[str, Sequence[str]],
    dek: bytes,
    *,
    an: datetime,
) -> list[int]:
    """Onarılan her hesap satırı için zincirin sonuna `SISTEM` `HESAP` satırı ekler.

    `degisenler`: {kanonik kimlik: değişen alan adları (model sırasıyla)}. Çağıranın açık
    `sqlite3` işleminde ve satırlar YAZILDIKTAN sonra çağrılır: içerik MAC'i satırın onarılmış
    hâlinden okunur. Commit çağıranındır. Eklenen satırların sıralarını döndürür. İA çözülemez,
    zincir başı ya da satır biçimsizse `IzYazilamadi` (hiçbir satır eklenmeden önce de olabilir;
    çağıran işlemi geri alır).
    """
    if not degisenler:
        return []
    kayit_id, ia = _etkin_anahtar(baglanti, dek)
    bas = baglanti.execute(
        "SELECT typeof(seq) = 'integer', CAST(seq AS BLOB), CAST(mac AS BLOB) "
        "FROM okul_audittrail ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    try:
        if bas is None:
            seq, prev_mac = 0, ""
        elif bas[0] != 1:
            raise _Bicimsiz
        else:
            seq, prev_mac = _tamsayi(bas[1]), _metin(bas[2])
        if seq > EN_BUYUK_SIRA - len(degisenler):
            raise _Bicimsiz  # yeni satırların sırası SQLite tamsayısını aşardı
    except _Bicimsiz as exc:
        raise IzYazilamadi("Geri yüklenen veritabanının zincir başı biçimsiz.") from exc
    zincir = crypto.audit_chain_key(ia)
    ozet = crypto.record_summary_key(ia)
    eklenen: list[int] = []
    for kimlik in sorted(degisenler):
        ham = _hesap_satiri(baglanti, kimlik)
        if ham is None:
            raise IzYazilamadi("Onarılan hesap satırı okunamadı.")
        try:
            record_mac = kanonik.kayit_mac(
                ozet, HESAP_MODELI, kimlik, hesap_ozet_alanlari(ham, dek)
            )
        except (_Bicimsiz, kanonik.KanonikHata) as exc:
            raise IzYazilamadi("Onarılan hesap satırının içerik MAC'i hesaplanamadı.") from exc
        seq += 1
        satir: dict[str, Any] = {
            "seq": seq,
            "at": an,
            "actor": AKTOR_SISTEM,
            "account": None,
            "role": "",
            "action": TUR_HESAP,
            "model": HESAP_MODELI,
            "object_id": kimlik,
            "term": None,
            "changed_fields": list(degisenler[kimlik]),
            "values": {},
            "record_mac": record_mac,
            "compliance_item": None,
            "label": "",
            "key_mode": KIP_ACIK,
            "key_ref": str(kayit_id),
        }
        try:
            mac = kanonik.iz_mac(zincir, satir, prev_mac)
        except kanonik.KanonikHata as exc:
            raise IzYazilamadi("Geri yüklenen veritabanının zincir başı biçimsiz.") from exc
        baglanti.execute(
            'INSERT INTO okul_audittrail (seq, "at", actor, account_id, role, action, model, '
            'object_id, changed_fields, "values", record_mac, label, key_mode, key_ref, '
            "prev_mac, mac) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seq,
                django_zamani(an),
                AKTOR_SISTEM,
                "",
                TUR_HESAP,
                HESAP_MODELI,
                kimlik,
                json.dumps(satir["changed_fields"]),
                json.dumps(satir["values"]),
                record_mac,
                "",
                KIP_ACIK,
                str(kayit_id),
                prev_mac,
                mac,
            ),
        )
        eklenen.append(seq)
        prev_mac = mac
    return eklenen
