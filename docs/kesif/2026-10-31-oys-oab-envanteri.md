# OYS Okul-Aile Birliği Modülü Envanteri (F0-6)

> **Tarih:** 31.10.2026 · **Plan kalemi:** [F0-6](../plan/2026-10-31-f0-f1-plani.md) ·
> **Kaynak:** `okulapp` deposunun `origin/main` dalı, commit **8e1687c5** (yerel `main` 159 commit geride
> olduğundan ayrı bir çıkarım üzerinden okundu; `okulapp` deposuna dokunulmadı) ·
> **Kapsam:** `backend/apps/okul_aile_birligi/` (modeller, servisler, seçiciler, izinler, sinyaller, görevler,
> evrak, dosya saklama, uçlar, göçler, 373 test) ve `docs/adr/0028`, `0029`, `0035`.
> **Girdi verdiği yerler:** F0-8 genel tasarım §5 (veri modeli), §6 (kural paketi), §9 (evrak kataloğu),
> §10 (kural testleri), §12 (çıkarım haritası); F1c kural paketi v1.

## Okuma kılavuzu

**Sınıflar**

| Sınıf | Anlamı |
|---|---|
| **AYNEN** | Mantık ve beklenen değerler olduğu gibi alınır; yalnız mekanik değişiklik (import yolu, fabrika, model adı, Türkçe ad çevirisi). |
| **UYARLA** | Mantık alınır, değişiklik yazılır (K1-K9, kural paketi, aile iskeleti, mevzuat düzeltmesi). Ne değiştiği satırda yazılıdır. |
| **ALMA** | Alınmaz; gerekçesi satırdadır. Yerine bir şey gelecekse o da yazılıdır. |

**Olgu ve yorum ayrımı.** Tablolarda "Kaynakta" sütunları koddaki ya da ADR'deki olguyu, "Not / değerlendirme"
sütunları bu belgenin yorumunu taşır. Düz metinde yorumlar **"Yorum:"** ile başlar. Emin olunamayan yerlerde
**DOĞRULANMADI** yazılır.

**Mevzuat karşılaştırması** `../evrakmotoru/mevzuat/` korpusundaki kanonik metinlerle yapıldı (salt okundu):
`meb-okul-aile-birligi-yonetmeligi.md`, `meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md`,
`okul-servisi-calistirma-usul-esaslari.md`, `okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md`,
`okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md`. 6183 sayılı Kanun korpusta yoktur. Bu
metinler aynı gün bu deponun [`docs/mevzuat/`](../mevzuat/BENIOKU.md) korpusuna da alındı (dosya adları ve çapalar aynı).

**Kısaltmalar.** GK genel kurul · YK yönetim kurulu · DK Denetleme Kurulu · **Yön.** MEB Okul-Aile Birliği
Yönetmeliği (RG 09.02.2012/28199; son değişiklik RG 01.12.2023/32386) · **Yön. EK-2** Okullarda Bulunan Kantin
ve Benzeri Yerleri Kiralama Sözleşmesi · **Servis U-E** Okul Servis Araçlarının Çalıştırılmasına İlişkin Usul ve
Esaslar (30.05.2018) · **Servis EK-2 / EK-3** aynı usul ve esasların sözleşme tasarısı / puanlama kriterleri ·
**GNL-OAB-FR-0xx** evrakmotoru genel OAB setindeki form kodu. Dosya yolları `backend/apps/okul_aile_birligi/`
altına görelidir.

**Kapsam dışı kalanlar.** Ön yüz (`frontend/.../modules/okul-aile-birligi/`) çıkarımda yok, envanterlenmedi.
OYS'nin `shared/`, `apps/core`, `apps/denetim`, `apps/bildirim`, `apps/bordro` kodları okunmadı; bu modüllere
olan bağlar yalnız import ve yabancı anahtar düzeyinde çıkarıldı. OYS kodunun atıf yaptığı
`kesif-evrak-analizi.md` (gerçek evrak analizi) çıkarımda yok ve gerçek kişi verisi içerebileceği için buraya
taşınmaz.

---

## 0. Ana bulgular

1. **Boyut.** 29 model, 34 enum, 57 servis fonksiyonu, 44 seçici, 52 görünüm sınıfı, 72 serileştirici, 54 uç,
   21 şablon dosyası (19 belge + 2 parça şablonu) ve kodla üretilen 1 XLSX, 10 göç, 40 test dosyasında
   **373 test**. Modül ADR-0035 ile 11.07.2026'dan beri OYS'de bayrakla **pasif** — kod testli ama sahada bir
   tam yıl çalışmadı.
2. **GK yeter sayısının tabanı hatalı.** Kod, dönemin `OrganMembership` kayıtlarını sayıp (ADAY dâhil, DÜŞTÜ
   hariç) ×4/×2 ile çarpıyor (`services.py:255-261`); Yön. md. 9/2'deki taban organ bileşiminden gelen sabit
   **16** koltuktur (YK 5+5, DK 3+3 → 64 / 32). Olağanüstü GK dönemsiz planlanırsa yeter sayı **0** çıkıyor
   (`services.py:293-302`), oysa md. 9/6 aynı ×4/×2'yi ister.
3. **ADR-0028'de ve ön değerlendirme §7.4'te yazan "30 gün" denetimi kodda yok.** Ekim sonu (md. 9/1), YK
   toplantı yeter sayısı 4 / karar yeter sayısı 3 (md. 13/3), görev bölümü bir hafta (md. 12/3, 14/1), elden
   bağışta 5 iş günü (md. 16/3), makbuz 50 asıl + 50 koçan (md. 16/5) da yok. F1c kural paketi v1'in on dört
   kaleminden altısı OYS'de hiç yok, üçü kısmen var, ikisinin anlamı düzeltilecek; bunlar sıfırdan yazılacak
   ya da düzeltilecek (§4.2).
4. **Dönem sınırı yarım.** Yön. md. 12/4 "Yönetim kurulu başkan **ve üyeleri** en fazla dört defa seçilebilir"
   der; kod yalnız başkanlık sayısını sayıyor (`services.py:122-130, 446-458`).
5. **Servis taşımacı seçimi mevzuata ve ADR-0028'e aykırı varsayılanla kurulmuş.** Kod servis için EK-3
   puanlamayı varsayılan yapıyor, başka yöntemi uyarıyla karşılıyor (`services.py:1065-1075`). Servis U-E md. 8/2
   komisyonun kriter değerlendirmesini esas alır; EK-3 puanlaması md. 8/3'e göre yalnız itiraz ya da yeni açılan
   okulda zorunludur. `EN_DUSUK_TEKLIF` (yürürlükten kalkmış 10.01.2018 metni) enumda duruyor → ALMA.
6. **Kantin tarafı yarım.** OYS kiralama süreci için evrak üretmiyor (uç 400 döner); sözleşme taslağı kira
   sözleşmesini de Servis EK-2'nin 10 maddesiyle basıyor (Yön. EK-2 25 madde). Aylık kira takvimi (Yön. EK-2
   md. 4: ayın 5-15'i, yarıyıl ayında yarım, 9/12 ay) yok. Pay beyanı Yön. EK-2 md. 7'deki "izleyen ayın
   **onuncu** günü" vadesini ve aylık dağıtımı görmüyor. Aynı dönem ve çeyrekte ikinci bir alan için beyan
   tekil kısıt yüzünden açılamıyor (`models/contract.py:247-251`).
7. **`is_metropolitan` alanı yanlış ölçütü modelliyor.** Yön. md. 17/1'deki %20 il payı "büyükşehir statüsünde
   olmayan **il merkezleri**" içindir; alan "büyükşehir mi" sorusunu soruyor, büyükşehir olmayan bir ilin ilçe
   okulunu yanlış sınıflar.
8. **Servis taksitleri birliğin alacağı değil.** Servis EK-2 md. 6'ya göre ücreti veli taşımacıya öder,
   makbuzu taşımacı verir. `ContractInstallment`'ın servis için anlamı sorgulanmalı; birliğin asıl alacak
   takvimi kantin kirasıdır ve OYS'de yoktur.
9. **§7.4 taslağından sapmalar.** `ReceiptBookRegistry` ve `ComplianceEntry` AYNEN değil UYARLA (koçan
   seri-cilt-sıra ve yaprak kaydı yok; uyum kaydı dört ayrı modele dağılıyor); `TefbisImport` yalnız kabuk →
   ALMA; ADR-0028'de sayılan `OabDocumentRecord` (evrak defteri) **hiç yazılmamış**; "21 şablon" 19 belge + 2
   parçadır; `TenderCommissionMember`, `TenderApproval`, `BidderDocument`, `BidderScore` tabloda yoktu (§2.5).
10. **İmza blokları Yönetmelikle çelişiyor.** Davetiye, tahmini bütçe ve gelir-gider çizelgesi "Okul Müdürü"
    imzalı. md. 9/1 çağrıyı YK'ye, md. 13/9 bütçeyi YK'ye, md. 13/4 gelir-gider işlemlerini muhasibe verir;
    proje kuralı 6 (müdür YK üyesi değildir) ile de çelişir.
11. **Servis evrakında "ihale" 7 şablonda 13 kez geçiyor** (görünür metin); "teklif" veri üzerinden basılabiliyor
    (durum etiketi, EK-3 4. kriterin mevzuattaki lafzı). Proje kuralı: servis evrakında "taşımacının tespiti".
12. **OYS çekirdeğine bağlar** (`core.SchoolYear` FK, `BaseModel.created_by`, `BidderDocument.uploaded_by`,
    `linked_user_id`, `shared.*`, `core`/`denetim`/`bildirim`/`bordro` servisleri, Celery) tek tek §2.1'de;
    hepsi çıkar ya da ailenin karşılığıyla değişir.
13. **Testler: 373 = AYNEN 69 · UYARLA 277 · ALMA 27.** AYNEN olanların tamamı saf iş kuralı testidir; API,
    izin ve evrak testlerinin hepsi UYARLA (K2 rolleri, docx, ailenin erişim günlüğü); ALMA'lar TCKN (K9),
    bordro (K3), Celery/bildirim ve modül bayrağıdır. Kural testi niteliğindeki 71 test §6.2'de.
14. **Altın kural 3 ile gerilim.** OYS'de istekli uygunluğu (hısımlık, suç, belge), taksit > 9, mülki amir
    onayı olmadan kesinleştirme, serviste muhammen bedel ve puan sınırları **sert engel**. Proje kuralı sert
    engeli yalnız hesap bütünlüğüne bırakıyor; F0-8'de hangisinin sert kalacağı karara bağlanmalı.
15. **KVKK temizliği gerekiyor.** Üyelikteki şifreli serbest metin beyan notu (özel nitelikli), DK kontrol
    listesindeki "adli sicil kayıtları alınmış mı" maddesi, kantin ilanındaki portör/adli sicil belgeleri
    (md. 20/6 bunları çalışandan ister, istekliden değil) sadeleşmeli. OYS'de bir sabit yorumunda ve bir test
    adında gerçek bir taşımacı firmanın adı geçiyor; taşınırken çıkarılır.

---

## 1. Envanterin boyutu

| Bileşen | Kaynakta | Sınıf (toplu) |
|---|---|---|
| `models/` | 13 dosya, 29 model, 34 enum (`_base.py`), sabitler ve tohum listeleri `_base.py:364-560` | UYARLA (ayrıntı §2) |
| `services.py` | 1813 satır, 57 fonksiyon + 1 dataclass | çoğu UYARLA (§3.1) |
| `selectors.py` | 554 satır, 44 fonksiyon | UYARLA / AYNEN (§3.2) |
| `permissions.py` | 5 sınıf (hepsi ADMIN/MUDUR/MUDUR_YARDIMCISI) | ALMA (§3.3) |
| `signals.py`, `events.md`, `tasks.py` | 5 bildirim sinyali, 2 Celery görevi | ALMA (§3.4) |
| `documents.py` | 20 üretici (19 PDF + 1 XLSX) + 5 yardımcı | UYARLA (§3.5) |
| `file_storage.py` | 8 fonksiyon, yalnız PDF, libmagic | UYARLA (§3.6) |
| `views.py`, `serializers.py`, `urls.py` | 52 görünüm, 72 serileştirici, 54 uç (`/api/v1/oab/`) | UYARLA (§3.7) |
| `admin.py` | 20 kayıt | ALMA |
| `migrations/` | 10 göç (0010: KVKK şifreleme geri doldurma) | ALMA |
| `templates/.../documents/` | 21 dosya | UYARLA (§5) |
| `tests/` | 40 dosya, 373 test, `factories.py` (336 satır) | §6 |

---

## 2. Modeller

### 2.1 OYS çekirdeğine ve kardeş modüllere bağlar

| Bağ | Nerede | Ne için | OAB Defteri'nde | Karar |
|---|---|---|---|---|
| `core.SchoolYear` FK (PROTECT) | `models/term.py:23` (`OabTerm.school_year`); `services.create_term` aktif ders yılını `core.selectors`'tan çözer | Dönemin başladığı ders yılı | Birlik dönemi kendi ders yılı alanını taşır (ör. "2026-2027"); başlangıç = GK tarihi (T3) | UYARLA |
| `linked_user_id` (FK değil, `PositiveIntegerField`) | `models/person.py:65` | Veli ↔ öğrenci eşleşmesi (md. 7/2) için planlanmıştı, çözüm servisi hiç yazılmadı | Çıkar. Velinin üyeliğinin bitmesi elle "öğrencisi ayrıldı" düşürmesiyle (yedek çağırma önerisiyle) işlenir | ALMA |
| `shared.models.BaseModel` | bütün modeller | `created_by` (kullanıcı FK), zaman damgaları, `deleted_at` yumuşak silme; "canlı kayıt" koşullu tekil kısıtları | Ailenin temel modeli + denetim izi; altın kural 4 (silme yok, ters kayıt) ile yumuşak silmenin ilişkisi F0-8'de | UYARLA |
| `settings.AUTH_USER_MODEL` FK | `models/bidder.py:129` (`BidderDocument.uploaded_by`) | Yükleyen | Yerel kullanıcı (F1b) | UYARLA |
| `shared.fields.EncryptedCharField/TextField` | `OabPerson.tckn/phone`, `OrganMembership.dropped_reason/eligibility_declaration_note`, `Bidder.contact_address` | Fernet alan şifrelemesi (ADR-0005) | Ailenin Fernet alan şifrelemesi (§7.1); TCKN alanı yok (K9) | UYARLA |
| `shared.blind_index` | `OabPerson.save()` → `tckn_hash`, `phone_hash` | Eşitlik araması, TCKN tekilliği | Kişide TCKN yok → `tckn_hash` ve tekil kısıt çıkar; telefon araması gerekmiyorsa `phone_hash` de çıkar | ALMA |
| `shared.roles.Role` | `permissions.py`, `services.oab_reminder_recipients` | ADMIN/MUDUR/MUDUR_YARDIMCISI | K2 rolleri (MY, başkan, muhasip, sekreter yazar; DK ve müdür salt okur) | ALMA |
| `shared.letterhead` + `core.services.get_letterhead_identity` | `documents._letterhead` | Antet: okul adı, ilçe, müdür adı | Okul kartı (F1b) | UYARLA |
| `core.services.list_students_with_responsible_parent` | `documents.build_imza_surkusu_xlsx` | GK katılım cetveline öğrenci + sorumlu veli listesi | Çekirdek yok; boş satırlı katılım cetveli ya da içe aktarılan liste (KVKK: veli verisi en aza) | UYARLA |
| `core.selectors.users_with_role` | `services.oab_reminder_recipients` | Bildirim alıcıları | Bildirim yok | ALMA |
| `core.services.file_serving.serve_protected_file` | `views.BidderDocumentDownloadView` | X-Accel korumalı dosya | Yerel dosya sunumu (yalnız `127.0.0.1`) | UYARLA |
| `apps.denetim.services` (`log_access`, `SENSITIVE_READ`, `AuditAction`) | `views.py` genelinde | Hassas okuma ve yazma günlüğü | Ailenin erişim günlüğü ve denetim izi | UYARLA |
| `apps.bildirim.signals` (5 sinyal) | `services._emit_membership_dropped`, `tasks.py` | Uygulama içi bildirim | Açılış ekranı (pano) + takvim | ALMA |
| `apps.bordro.services.get_period_employer_cost` | `services.suggest_personnel_realized_for_term` | Bütçede personel gideri önerisi | K3: bordro yok | ALMA |
| Ters kenar: bordro ← `services.get_disbursement_signatories` | `services.py:1783` | Banka ödeme listesine başkan + muhasip imza bloğu (md. 18/2) | Ödeme talimatı çıktısında iç kullanım | UYARLA |
| Celery (`shared_task`), `settings.MODULE_OAB_ENABLED` | `tasks.py` | Günlük hatırlatma, modül bayrağı (ADR-0035) | Masaüstünde yok | ALMA |
| `shared.exceptions._client_ip` | `views.py` | Günlüğe IP | Yerel uygulamada anlamsız | ALMA |
| `apps.core.tests.factories.SchoolYearFactory` | `tests/factories.py:15` | Bütün fabrikaların kökü | Yerel fabrika | UYARLA |
| `python-magic` (libmagic) | `file_storage.py:21` | İçerikten MIME | Windows'ta ayrı DLL gerekir (paketleme riski, F0-7); PDF imza baytı denetimi yeterli olabilir | UYARLA |
| `documents/base.html` (proje ortak şablonu) | bütün belge şablonları `extends` eder | Antet ve sayfa düzeni | Ailenin evrak katmanı + docx şablonu | UYARLA |

### 2.2 Model tablosu

**Kişi, dönem, organ**

| Model | Alanlar (özet) | Doğrulama / kısıt | Sınıf | Uyarlama notu |
|---|---|---|---|---|
| `OabPerson` | `kind` (VELI, OGRETMEN, IDARECI, HAYIRSEVER, KURSIYER, DIGER), ad, soyad, `tckn` + `tckn_hash`, `phone` + `phone_hash`, `linked_user_id` | Canlı kayıtta `tckn_hash` tekil (`person.py:83-87`); TCKN 11 hane (`serializers.py:215-218`); TCKN ve telefon isteğe bağlı | UYARLA | **K9:** `tckn`, `tckn_hash`, tekil kısıt, TCKN doğrulaması çıkar (bağışçı TCKN'si F3'te bağış kaydında, ayarla). `linked_user_id` çıkar. Telefon şifreli kalır. F1c türleri (veli · öğretmen · yönetici · hayırsever · kursiyer) ile örtüşür; DIGER isteğe bağlı. "18 yaşını doldurmuş kursiyer" (md. 7/1, 12/1) için yaş ya da beyan alanı yok |
| `OabTerm` | `school_year` FK, `name`, `start_date` (GK seçim tarihi), `end_date`, `is_active` | Ad canlı kayıtta tekil; tek aktif dönem; bitiş ≥ başlangıç | UYARLA | `school_year` FK çıkar (§2.1). Kapanmış dönem kilidi (altın kural 4) ve kural paketi sürümü bağı eklenir (F1c). Görev süresi bir yıl (md. 12/2, 14/2) kodda sınanmıyor |
| `OrganMembership` | `term`, `person`, `organ` (yalnız YK, DK), `role` (BASKAN, BASKAN_YARDIMCISI, MUHASIP, SEKRETER, UYE), `seat_type` (ASIL, YEDEK), `seat_order` (yedek oy sırası), `status` (ADAY → SECILDI → DUSTU), `status_changed_at`, `dropped_reason` (şifreli), `eligibility_declared` + tarih + `eligibility_declaration_note` (şifreli), `compliance_warnings`, `compliance_justification` | Aynı dönem + organ + kişi canlı kayıtta tekil; sayı kuralları modelde değil serviste (uyarı) | UYARLA | Organ türleri genişler: divan, alım komisyonu (en az 3, md. 18/1), temsilciler (F1c). Beyan notu (özel nitelikli serbest metin) yerine yalnız "beyan alındı" + tarih (ön değerlendirme §2.1). Okul müdürü YK'ye eklenemez kuralı yok → eklenir. `kvkk_special_category=True` gerekçesi beyan notu kalkınca yeniden değerlendirilir |

**Genel kurul**

| Model | Alanlar (özet) | Doğrulama / kısıt | Sınıf | Uyarlama notu |
|---|---|---|---|---|
| `GeneralAssembly` | `term` (boş olabilir), `kind` (OLAGAN, OLAGANUSTU), `trigger_reason` (YK, okul müdürü, DK, üyelerin %10'u), `announced_at`, `scheduled_at`, `venue`, `second_meeting_at`, `student_count_snapshot`, `quorum_required`, `attendee_count`, `follows_failed_assembly` (öz FK), `compliance_warnings/justification`, `status` (PLANLANDI, YAPILDI, IPTAL), `minutes_note`; `notice_days`, `quorum_met` özellikleri | Kısıt yok; denetimler serviste | UYARLA | Yeter sayı tabanı kural paketinden (§4 satır 1). 30 gün ve Ekim sonu uyarıları eklenir. Olağanüstüde çağrı nedeni zorunlu (ön değerlendirme §2.1). İbra sonucu (edildi / edilmedi, md. 11/1-c, ç) ve "edilmedi" akışı eklenir. `venue`, `second_meeting_at` API'den yazılamıyor (yalnız admin) → yazılabilir olur. Öğrenci mevcudu okul kartından |
| `AgendaItem` | `assembly`, `order`, `title`, `notes` | GK + sıra canlı kayıtta tekil | AYNEN | Ekleme, çıkarma, sıralama ucu yok (md. 9/4 oy çokluğu); tohum içeriği GNL-OAB-FR-002'den tazelenir |
| `AssemblyMinutes` | GK'ye bire bir; divan başkanı, kâtip, YK raporunu okuyan, DK raporunu okuyan, bütçeyi sunan (serbest metin adlar), `authorization_note` | — | UYARLA | Divan başkanı ve kâtip veliler/kursiyerler arasından (md. 10/1-c) → kişi kaydına bağlanabilir, türü uymazsa uyarı. Seçilen üyeler tek kaynaktan (`OrganMembership`) gelme ilkesi AYNEN |

**Kurul toplantıları ve denetleme**

| Model | Alanlar (özet) | Doğrulama / kısıt | Sınıf | Uyarlama notu |
|---|---|---|---|---|
| `BoardMeeting` | `term`, `organ`, `meeting_date`, `meeting_no`, `notes` | — | UYARLA | Toplantı yeter sayısı 4 ve aylık toplantı (md. 13/3) eklenir |
| `BoardMeetingAttendance` | `meeting`, `membership`, `present`, `excused` | Toplantı + üyelik canlı kayıtta tekil | AYNEN | Üst üste 3 özürsüz devamsızlık mantığı bu tablodan |
| `BoardDecision` | `meeting`, `decision_no`, `decision_date`, `text`, `is_draft` (varsayılan True) | — | UYARLA | Defter sıra no, sayfa, "deftere işlendi" işareti, oy sayıları (karar yeter sayısı 3), bağlı işlemler (§7.3). `is_draft`'ı False yapan servis yok |
| `AuditReport` | `term`, `kind` (ARA, NIHAI), `report_date`, `checklist` (JSON: no, item, finding, note), `irregularity_found` (bir UYGUNSUZ varsa True), `escalation_note` | — | UYARLA | 18 maddelik liste "[İKİNCİL]" sentezdir; GNL-OAB-FR-012 (22 kalem) ve TKB E.4 ile tazelenir. "Yılda en az iki" (md. 14/4) sayılmıyor. Yazma yetkisi K2'de açık (§8 S-10) |

**Bütçe, uyum, makbuz, endeks, TEFBİS**

| Model | Alanlar (özet) | Doğrulama / kısıt | Sınıf | Uyarlama notu |
|---|---|---|---|---|
| `BudgetCategory` | `code`, `name`, `kind` (GELIR, GIDER), `order`, `is_active` | Kod canlı kayıtta tekil; tohum `_base.py:390-405` (5 gelir + 8 gider) | UYARLA | Hesap planı + TEFBİS işlem tipi eşlemesine dönüşür (K6, §7.3 TEFBİSEşleme) |
| `OabBudget` | `term`, `status` (TASLAK, ONAYLANDI), `approved_at`, `opening_balance` (devir), `notes` | Dönem başına tek canlı bütçe | UYARLA | **K1:** devir "Devreden" kaydına (banka, kasa, TEFBİS) taşınır. ONAYLANDI'ya geçiren servis yok. Yönetmelik "görüşür" der (md. 11/1-d, 13/9); "onaylandı" etiketi yeniden adlandırılır |
| `BudgetLine` | `budget`, `category`, `estimated_amount`, `realized_amount` (kategori bazlı dönem özeti), `realized_from_payroll`, `notes` | Bütçe + kategori tekil; tutarlar ≥ 0 | UYARLA | **K1:** gerçekleşen artık elle girilmez, gelir-gider işlem kayıtlarından hesaplanır. **K3:** `realized_from_payroll` çıkar |
| `ComplianceEntry` | `term`, `kind` (TEFBIS, PANO_WEB_ILAN md. 13/10, MUDURE_BILDIRIM md. 18/5, ARZ_BEDELI_ODEME), `period_label`, `due_date`, `done`, `done_date`, `responsible` (serbest metin ad), `notes` | `done` + `due_date` dizini | UYARLA | Tek çatı bölünür: TEFBİS → mutabakat modülü (K6); pano/web ilanı → İlan (§7.3); müdüre bildirim → AylıkBildirim (otomatik taslak); arz bedeli → pay beyanıyla çift kayıt, kalkar. Kalan takvim maddeleri → UyumKaydı (gerekçe, kanıt). `responsible` serbest metin yerine kullanıcı/rol |
| `ReceiptBookRegistry` | `term`, `book_no`, `serial_start`, `serial_end`, `received_date`, `status` (AKTIF, BITTI, IPTAL), `notes` | Dönem + cilt no tekil | UYARLA | Md. 16/5'teki seri, cilt, sıra; 50 asıl + 50 koçan; mühür tarihi; karar defteri kaydı; kullanılan/iptal yaprak kaydı yok (§7.3 MakbuzKoçanı). Koçan dönemle değil birlikle yaşar (dönemler arası devir) |
| `IndexRate` | `kind` (TUFE, UFE), `year`, `month`, `value`, `source_note` | Tür + yıl + ay tekil; ay 1-12 | AYNEN | Tek not: `value` "aylık endeks ya da yıllık %" diye belirsiz (`compliance.py:124-130`); md. 21/3'e göre "TÜFE on iki aylık ortalamalara göre yüzde değişim" diye sabitlenir |
| `TefbisImport` | `term`, `period_label`, `status` (BEKLIYOR, ISLENDI), `raw_summary` (JSON), `notes` | — | ALMA | Kabuk: servis, uç, admin, test yok. K6'ya göre yeni TEFBİS Excel mutabakat modeli tasarlanır |

**Kantin ve servis (K4 — sürüm 1)**

| Model | Alanlar (özet) | Doğrulama / kısıt | Sınıf | Uyarlama notu |
|---|---|---|---|---|
| `RentableAsset` | `name`, `asset_kind` (KANTIN, SPOR_SALONU, KONFERANS_SALONU, OTOPARK, SERVIS_GUZERGAHI, DIGER), `description`, `location_note`, `is_active` | Ad canlı kayıtta tekil | UYARLA | SERVIS_GUZERGAHI kiralanan alan değildir → çıkar. Tam yıl / 9 ay işletme (md. 19/3) ve kısa süreli kullandırma bedelleri (md. 19/4) eklenir |
| `Tender` | `asset`, `term`, `kind` (SERVIS, KIRALAMA), `evaluation_method` (PUANLAMA, PAZARLIK, EN_DUSUK_TEKLIF), `title`, `status` (TASLAK → MUHAMMEN_TESPIT → ILAN → TEKLIF_TOPLAMA → DEGERLENDIRME → KARAR → ONAY → KESINLESTI / IPTAL), ilan, dosya teslim ve ihale tarihleri, `estimated_price`, `guarantee_amount`, `single_bidder`, `winner` (tek istekli FK), `winning_reason`, uyarı + gerekçe | KESINLESTI silinemez (`tender.py:140-144`) | UYARLA | İki ayrı sürece bölünür: **kantin kiralaması** ("ihale", md. 20) ve **servis taşımacısının tespiti** (ihale/teklif yok). EN_DUSUK_TEKLIF çıkar; servis için "komisyon değerlendirmesi" (md. 8/2) varsayılan, EK-3 yalnız itiraz/yeni okul. Serviste birden çok taşımacı seçilebilmeli (Servis U-E md. 10/3 çoğul) — DOĞRULANMADI. Teminat serviste kalktı (30.05.2018) |
| `TenderCommissionMember` | `tender`, `commission_kind` (MUHAMMEN_TESPIT, IHALE), `role` (12 seçenek), `person` ya da dış temsilci adı + unvanı, `seat_type`, `is_chair` | İhale + komisyon türü + kişi tekil | UYARLA | Bileşim şablonları kural paketine. Servis komisyonunda yedekler (md. 3/1-e) ve "varsa" vakıf temsilcisi |
| `TenderApproval` | `tender`, `order`, `authority` (mülki amir, kaymakam, valilik, ilçe/il MEB), `decision` (BEKLIYOR, UYGUN_GORUS, OLUR, RED), evrak no ve tarihi | İhale + sıra tekil | UYARLA | Servis: mülki amir 5 iş günü (md. 8/5), tebliğ 5 iş günü (md. 8/6). Kantin onay zinciri DOĞRULANMADI |
| `Bidder` | `tender`, `person`, `bidder_type` (GERCEK, TUZEL), `legal_name`, `tax_number`, `trade_registry_no`, `contact_address` (şifreli), `contact_email`, `bid_amount`, `is_disqualified` + gerekçe | İhale + kişi tekil | UYARLA | Gerçek kişide vergi no = TCKN; K9 çizgisinde basılmaz (OYS de basmıyor). `bid_amount` yalnız kantin |
| `BidderDocument` | `bidder`, `document_type` (21 tür; adli sicil, portör, sağlık raporları özel nitelikli), dosya yolu, ad, MIME, boyut, sha256, `is_present` (Mevcut/Eksik), `uploaded_by`, `notes` | sha256 dizini | UYARLA | Yön. md. 23/4 kantin çalışanlarının portör ve adli sicil belgelerinin **birlikçe muhafazasını** ister → saklama gerekli; dosyada şifreleme, erişim günlüğü ve saklama süresi eklenir. Yıllık yenileme (md. 20/7) için belge süresi alanı (§7.3 BelgeSüresi) |
| `ScoringCriterion` | `code`, `name`, `tender_kind`, `max_points` (5), `order`, `is_binary`, `scale` (JSON kademeler), `is_active` | Kod tekil; tohum `_base.py:458-513` | AYNEN | Tohum kural paketine taşınır (EK-3 sürümlü). Kademeler EK-3 ile birebir |
| `BidderScore` | `bidder`, `criterion`, `awarded_points`, `selected_tier`, `note` | İstekli + kriter tekil; toplam saklanmaz | AYNEN | — |
| `OabContract` | `kind`, `tender`, `contractor`, `asset`, `term`, `renewal_of` (öz FK, 20 yıl zinciri), `status` (TASLAK, IMZALANDI, YURURLUKTE, FESIH, SONA_ERDI), `title`, karar tebliğ, imza, başlangıç, bitiş tarihleri, `duration_terms`, `base_amount`, `current_annual_amount`, yer teslimi (yapıldı, tarih), uyarı + gerekçe | İhale başına bir canlı (feshedilmemiş) sözleşme | UYARLA | Durum geçişleri, yer teslimi kaydı servisi yok. Kantin: Yön. EK-2 (25 madde + özel şartlar), kesin teminat, millî emlak'a örnek (md. 21/5), %25 öğrenci değişimi (md. 21/3), 20 yıl için Genelge 2024/35 III hesabı. Kesinleşme kilidi yalnız `Tender`'da; sözleşmeye de gelir (altın kural 4) |
| `ContractInstallment` | `contract`, `installment_no` (1-9, DB kısıtı `contract.py:164-168`), `period_label`, `due_date` (ayın 15'i), `amount`, `status` (BEKLIYOR, ODENDI, IADE), `paid_at`, `refunded_amount`, `notes` | Sözleşme + no tekil | UYARLA | Servis ücretini veli taşımacıya öder (Servis EK-2 md. 6/b); birlik için anlamı sorgulanmalı (§8 S-6). Asıl gereken kantin aylık kira takvimi (Yön. EK-2 md. 4); kira taksidi banka hareketiyle eşlenir (K1). ODENDI/IADE'ye geçiren servis yok |
| `ShareStatement` | `term`, `contract`, `asset`, `mode` (KIRAYA_VERME, ISLETME), `payer` (moddan türer), `year`, `period` (Q1-Q4 takvim çeyreği), `is_metropolitan`, `gross_amount`, oran ve tutarlar (arz bedeli, işletme giderleri, net, birlik, ilçe, il payları), `due_date`, `paid_at`, gecikme zammı oranı ve tutarı | Dönem + mod + yıl + çeyrek tekil (`contract.py:247-251`) | UYARLA | Tekil kısıta alan/sözleşme eklenir. `is_metropolitan` → okul kartındaki yerleşim türü ("büyükşehir olmayan il merkezi"). Vade 20'si / 10'u kararı (§4 satır 29). Yön. EK-2 md. 7: kiracı payları ayın 5-15'inde doğrudan yatırır → aylık izleme (GNL-OAB-FR-021). K1: ödemeler banka hareketiyle eşlenir |
| `InspectionRecord` | `term`, `subject` (BIRLIK_MEM_DENETIMI md. 26, BIRLIK_MALI, KANTIN Genelge 2020/8, SERVIS), `asset`, planlı ve gerçekleşen tarih, `result` (UYGUN, UYGUNSUZ, KISMEN), `inspector` (serbest metin), rapor no ve tarihi, `findings`, `follow_up_due`, `done`, `notes` | `done` + `planned_date` dizini | AYNEN | Vade sinyali yerine pano. `follow_up_due` yardım metnindeki "3 iş günü / aynı gün" Genelge 2020/8'de ilçe ekibinin müdahale süresidir, düzeltme termini değildir (§4 satır 52) |

### 2.3 Enum'lar (34)

Hepsi `_base.py`'dedir. Değerler Türkçe etiketleriyle birlikte büyük ölçüde AYNEN alınabilir; değişenler:

| Enum | Değişiklik | Gerekçe |
|---|---|---|
| `OrganType` (YK, DK) | Divan, alım komisyonu, temsilci görevleri eklenir | F1c organlar |
| `EvaluationMethod` | `EN_DUSUK_TEKLIF` çıkar; servis için `KOMISYON_DEGERLENDIRME` eklenir | Servis U-E md. 8/2-3; ADR-0028 |
| `TenderKind`, `TenderStatus`, `CommissionKind` | Servis tarafında "ihale", "teklif toplama" etiketleri değişir ("taşımacının tespiti", "başvuru toplama") | Proje kuralı 6 |
| `RentableAssetKind` | `SERVIS_GUZERGAHI` çıkar | Servis güzergâhı kiralanan alan değildir |
| `ComplianceKind` | Dağılır (§2.2) | §7.3 modelleri |
| `TefbisImportStatus` | Çıkar | `TefbisImport` ALMA |
| `OabBudgetStatus.ONAYLANDI` | "Genel kurulda görüşüldü" | md. 11/1-d, 13/9 |
| `SharePeriod` | Takvim çeyreği varsayımı doğrulanmalı | Yön. "üçer aylık dönemler" der, başlangıcı yazmaz — DOĞRULANMADI |
| `BidderDocumentType` | Kantinde portör/adli sicil "çalışan belgesi" olarak ayrılır | md. 20/6, 23/4 |

### 2.4 OYS'de olmayan, OAB Defteri'nde gereken modeller

Ön değerlendirme §7.3'teki çekirdekten OYS'de **karşılığı olmayanlar**: BankaHesabı, BankaHareketi, Eşleme, GelirKaydı,
GiderKaydı (harcama zinciri: talep → karar → komisyon → belge → ödeme, md. 18/1), MakbuzKoçanı yaprak kaydı,
TEFBİSEşleme, Devreden, İlan, AylıkBildirim, Evrak (gelen/giden/üretilen + sha256 — ADR-0028'de
`OabDocumentRecord` adıyla planlanmış ama **yazılmamış**), UyumKaydı, KuralPaketi, Okul (kart), roller ve
kullanıcılar, temsilcilikler, kantin aylık kira takvimi, BelgeSüresi. Yorum: OYS modülü mali çekirdeği bilinçli
olarak dışarıda bırakmıştı (ADR-0028 "muhasebe DEĞİL"); K1 ile bu katman tamamen yeni yazılacak.

### 2.5 Ön değerlendirme §7.4 taslağıyla karşılaştırma

| §7.4'te | §7.4 kararı | Bu envanterin bulgusu | Düzeltme |
|---|---|---|---|
| `OabPerson`, `OabTerm`, `OrganMembership` ("YK 5+5, DK 1+2 doğrulamaları; dönem sınırları") | UYARLA | Doğru. Ancak DK bileşimi 1 veli + 2 öğretmen **asıl** ve aynı sayıda yedek (3+3); dönem sınırı yalnız başkan için sayılıyor (md. 12/4 üyeleri de kapsar); DK veli koltuğuna hayırsever de sayılıyor (md. 14/1 saymaz); `core.SchoolYear` FK ve şifreli beyan notu da çıkar | UYARLA (notlar genişler) |
| `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes` ("nisap ×4/×2; 15 gün ve 30 gün denetimi") | UYARLA | **30 gün denetimi kodda yok** (yalnız ADR'de); nisap tabanı kayıt sayısından hesaplanıyor; olağanüstü dönemsiz GK'de yeter sayı 0; ibra sonucu alanı yok | UYARLA (eksikler yazıldı) |
| `BoardMeeting`, `BoardMeetingAttendance`, `BoardDecision` | UYARLA | Doğru. Ek olarak YK toplantı yeter sayısı 4, karar yeter sayısı 3, aylık toplantı, yedek çağırma, görev bölümü bir hafta kodda yok | UYARLA |
| `AuditReport` (18 madde) | UYARLA | Doğru; 18 madde "[İKİNCİL]" sentez; GNL-OAB-FR-012 22 kalem; KVKK'lı bir madde var | UYARLA |
| `BudgetCategory`, `OabBudget`, `BudgetLine` | UYARLA | Doğru; bordro önerisi (K3) de çıkar | UYARLA |
| `ReceiptBookRegistry`, `ComplianceEntry`, `IndexRate` | **AYNEN** | `ReceiptBookRegistry` yalnız cilt no + seri aralığı tutuyor (md. 16/5 ve §7.3 MakbuzKoçanı alanları yok); `ComplianceEntry` dört farklı modele dağılıyor; `IndexRate` neredeyse aynen | **`ReceiptBookRegistry` UYARLA · `ComplianceEntry` UYARLA · `IndexRate` AYNEN** |
| `TefbisImport` | UYARLA | Kabuk: alan analizi, servis, uç yok | **ALMA** (K6'ya göre yeni model) |
| `RentableAsset`, `Tender`, `Bidder`, `ScoringCriterion`, `OabContract`, `ContractInstallment`, `ShareStatement`, `InspectionRecord` | UYARLA — sürüm 1 | Doğru, ama liste eksik: `TenderCommissionMember`, `TenderApproval`, `BidderDocument`, `BidderScore` de var. `ScoringCriterion`, `BidderScore`, `InspectionRecord` AYNEN alınabilir. Servis varsayılan yöntemi, kantin evrak seti, aylık kira, pay vadesi ve tekil kısıt sorunları §0'da | Liste tamamlanır; üçü AYNEN |
| 21 evrak şablonu (HTML/WeasyPrint) | UYARLA | 19 belge + 2 parça şablonu; ayrıca kodla üretilen XLSX katılım cetveli. Servis setinin 9 belgesi kiralama için üretilmiyor | UYARLA (§5) |
| Celery beat hatırlatmaları | ALMA | Doğru. Vade seçicileri (`due_*`) pano için UYARLA | ALMA + seçiciler UYARLA |
| `bordro` modülü | ALMA (şimdilik) | Doğru; OAB içindeki bordro bağları (`suggest_personnel_realized_for_term`, `apply_personnel_realized`, `realized_from_payroll`) da çıkar | ALMA |
| Çok kullanıcılı OYS rol sistemi | ALMA | Doğru (`permissions.py` ALMA) | ALMA |
| — (tabloda yok) | — | `OabDocumentRecord` ADR'de var, kodda yok; `file_storage.py`, `documents.py`, uçlar, göçler, `get_disbursement_signatories` tabloda yoktu | Eklendi (§3) |

---

## 3. Servisler, seçiciler, izinler, sinyaller, görevler, evrak, dosya saklama

### 3.1 `services.py`

| Fonksiyon | Satır | Kaynakta | Sınıf | Not |
|---|---|---|---|---|
| `_q` | 95 | Kuruş, ROUND_HALF_UP | AYNEN | — |
| `create_term`, `update_term` | 140, 184 | Ders yılını `core`'dan çözer; tek aktif dönem | UYARLA | §2.1; kapanmış dönem kilidi |
| `create_person`, `update_person` | 204, 234 | TCKN/telefon şifreli + kör indeks; TCKN tekilliği | UYARLA | K9, `linked_user` çıkar |
| `compute_assembly_quorum` | 251 | Dönemin DÜŞTÜ olmayan üyelik kayıtları × (mevcut < 100 ise 2, değilse 4); 2. toplantıda 0 | UYARLA | Taban kural paketinden sabit (YK 5+5 + DK 3+3) |
| `schedule_general_assembly` | 264 | 15 gün uyarısı + gerekçe; yeter sayıyı dondurur; gündem tohumu | UYARLA | 30 gün, Ekim sonu, olağanüstüde çağrı nedeni ve yeter sayı |
| `create_default_agenda` | 323 | 11 maddelik tohum | AYNEN | İçerik GNL-OAB-FR-002 ile tazelenir |
| `record_assembly_outcome` | 333 | Katılım sayısı + durum | UYARLA | İbra sonucu; yeter sayı yoksa 2. toplantı önerisi |
| `set_assembly_minutes` | 364 | Serbest metin adlar | UYARLA | Kişi bağı + md. 10/1-c uyarısı |
| `validate_membership_composition` | 399 | YK 5+5, DK veli 1+1, öğretmen 2+2 — uyarı | UYARLA | Kural paketi; YK kişi türü; müdür yasağı; DK'de hayırsever; yeni organlar |
| `count_prior_baskan_terms`, `promote_membership` | 446, 461 | Başkanlık sayacı (YK 4, DK 3) → uyarı + gerekçe | UYARLA | md. 12/4: YK'de bütün üyelikler sayılır; geçmiş eksikse uyarı |
| `oab_reminder_recipients`, `_emit_membership_dropped` | 495, 507 | Bildirim alıcısı ve yayını | ALMA | Pano |
| `drop_membership` | 535 | SECILDI → DUSTU, gerekçe zorunlu | UYARLA | Yedek çağırma önerisi (oy sırası), bir hafta görev bölümü, md. 13/8 olağanüstü GK uyarısı |
| `assign_membership` | 553 | ADAY olarak ekler; beyan tarihi | UYARLA | Beyan notu sadeleşir |
| `record_board_meeting` | 596 | Kayıt | UYARLA | Yeter sayı 4, aylık |
| `record_attendance`, `_maybe_auto_drop_for_absences` | 617, 647 | YK'de üyeliğin son 3 katılım kaydı mazeretsiz devamsızsa düşürür | AYNEN | Sayım toplantıya değil kayda dayanır; toplu katılım girişi bunu kapatır |
| `record_board_decision` | 657 | Taslak karar | UYARLA | Defter sıra no, sayfa, işlendi, oylar |
| `create_audit_report`, `update_audit_report` | 679, 709 | Varsayılan 18 madde; bir UYGUNSUZ → usulsüzlük | UYARLA / AYNEN | Liste tazelenir; bayrak mantığı AYNEN |
| `ensure_default_budget_categories`, `create_budget`, `set_budget_line` | 735, 751, 771 | Kategori tohumu, satırlar, elle tahmini/gerçekleşen | UYARLA | K1 |
| `_iter_year_months`, `suggest_personnel_realized_for_term`, `apply_personnel_realized` | 796, 809, 825 | Bordrodan personel gideri önerisi | ALMA | K3 |
| `BudgetFinancialSummary`, `budget_financial_summary` | 848, 866 | Devir + gerçekleşen gelir − gider | UYARLA | K1: işlem kayıtlarından; Devreden |
| `record_compliance`, `mark_compliance_done` | 894, 916 | Uyum kalemi aç / yapıldı | UYARLA | Takvim + kanıt |
| `create_index_rate` | 926 | Elle endeks | AYNEN | — |
| `create_receipt_book` | 951 | Koçan kaydı | UYARLA | §2.2 |
| `_persist_tender_warnings`, `set_commission` | 988, 1170 | Uyarı + gerekçe deseni | AYNEN | Altın kural 3'ün doğrudan karşılığı |
| `ensure_ek3_scoring_criteria` | 1002 | EK-3 tohumu | UYARLA | Kural paketinden |
| `create_rentable_asset`, `set_estimated_price` | 1026, 1094 | Alan; muhammen bedel yalnız kiralamada (serviste sert engel) | AYNEN | — |
| `create_tender` | 1050 | Varsayılan yöntem SERVIS → PUANLAMA | UYARLA | §0 madde 5 |
| `validate_commission` | 1114 | Servis md. 3/1-e, muhammen bedel md. 19/1, kiralama md. 20/3 bileşimleri | UYARLA | Şablonlar kural paketine |
| `register_bidder` | 1210 | İstekli | UYARLA | K9 |
| `check_bidder_eligibility` | 1238 | Suç, hısımlık, belge → sert engel | UYARLA | Atıf 20/11; md. 20/5; altın kural 3 |
| `score_bidder`, `compute_bidder_total` | 1268, 1304 | Puan sınırları, toplam | AYNEN | — |
| `determine_winner` | 1309 | Puan / en yüksek / en düşük; eşitlikte gerekçe | UYARLA | En düşük çıkar; komisyon değerlendirmesi |
| `record_approval`, `finalize_tender` | 1365, 1398 | Onay zinciri; OLUR olmadan sert engel; ilan < 7 gün uyarısı | UYARLA | 7 gün ilan anında; 5 iş günü |
| `add_bidder_document` | 1440 | Korumalı dosya | UYARLA | §3.6 |
| `create_contract` | 1478 | Servis 1-3 dönem, kiralama alanı, ≤ 5 / ≤ 20 yıl, imza 10 gün → uyarı | UYARLA | Genelge 2024/35; artık yıl; durum geçişleri |
| `add_installments` | 1562 | ≤ 9 taksit sert engel, vade 15'i, atlanan aylar | UYARLA | Kantin aylık kira takvimine genişler |
| `_share_due_date`, `record_share_statement`, `mark_share_paid` | 1614, 1626, 1689 | Çeyrek vadesi 20'si; %3/%1 ve 80/10/10; gecikme zammı ay = ⌈gün/30⌉ | UYARLA | §4 satır 28-30 |
| `apply_tufe_increase` | 1710 | 2. yıldan `IndexRate.value` % artış | UYARLA | Yıl dönümü, 12 aylık ortalama |
| `record_inspection` | 1744 | Denetim kaydı | AYNEN | — |
| `get_disbursement_signatories` | 1783 | Başkan (yoksa başkan yardımcısı) + muhasip imza bloğu | UYARLA | Ödeme talimatı (md. 18/2) |

### 3.2 `selectors.py` (45)

| Grup | Fonksiyonlar | Sınıf | Not |
|---|---|---|---|
| Tek kaynak listeleri | `organ_members`, `elected_roster`, `candidate_roster`, `agenda_items`, `list_memberships` | AYNEN | Evrakların tutarlılık ilkesinin dayanağı |
| Tek kayıt getiriciler | `get_person`, `get_assembly`, `get_membership`, `get_budget`, `get_budget_category`, `get_compliance_entry`, `get_audit_report`, `get_tender`, `get_bidder`, `get_bidder_document`, `get_term`, `get_active_term`, `get_board_meeting`, `get_rentable_asset`, `get_scoring_criterion`, `get_share_statement`, `get_contract`, `get_tender_detail`, `get_tender_for_documents`, `board_decisions` | UYARLA | Model değişikliklerine göre |
| Vade taramaları | `due_compliance_entries`, `due_contract_installments`, `due_share_statements`, `due_inspections` | UYARLA | Celery yerine açılış ekranındaki "yaklaşan işler" |
| Endeks | `latest_index_rate` | AYNEN | — |
| Liste uçları | `list_persons`, `list_terms`, `list_assemblies`, `list_board_meetings`, `list_audit_reports`, `list_budgets`, `list_compliance_entries`, `list_receipt_books`, `list_index_rates`, `list_tenders`, `list_rentable_assets`, `list_scoring_criteria`, `list_contracts`, `list_inspections` | UYARLA | Geçersiz filtreyi yok sayma ve PII'siz liste deseni korunur |

### 3.3 `permissions.py`

| Sınıf | Kaynakta | Sınıf | OAB Defteri'nde |
|---|---|---|---|
| `HasAnyRole`, `CanViewOabPersonDetail`, `CanManageOab`, `CanViewOab`, `CanAccessBidderDocument` | Beşi de ADMIN, MUDUR, MUDUR_YARDIMCISI; MEMUR ve öğretmen giremez (ADR-0028 "operatör V1'de okul idaresi") | ALMA | **K2** rol matrisi: MY, başkan, muhasip, sekreter yazar; DK ve müdür salt okur. "Okuma ≠ yönetme ≠ hassas detay" ayrımı ve hassas okumada günlük deseni korunur |

### 3.4 Sinyaller ve görevler

| Öğe | Kaynakta | Sınıf | Yerine |
|---|---|---|---|
| `oab_uyum_hatirlatma` | `ComplianceEntry.due_date`'e 7/3/1/0 gün kala, günlük 07:30 | ALMA | Açılış ekranında son tarihe göre sıralı iş listesi + takvim |
| `oab_uye_dusme_uyarisi` | `drop_membership` sonrası (commit sonrası) | ALMA | Panoda "yedek çağır, görev bölümü yap" işi |
| `oab_odeme_vadesi_yaklasti`, `oab_arz_bedeli_vadesi`, `oab_denetim_zamani` | Günlük 07:35 tarama | ALMA | Pano + takvim |
| `student_enrollment_changed` dinleyicisi | PLANLI, yazılmamış | ALMA | Elle düşürme (§2.1) |
| `tasks.scan_compliance_reminders`, `tasks.scan_contract_reminders`, `REMINDER_DAYS` | Celery beat, bayrak denetimi | ALMA | — |
| Kontrat ilkesi: bildirim gövdesinde kişi adı yok | `events.md` | AYNEN (ilke) | Pano metinlerinde de kişi adı yerine görev ve konu |

Yorum: OYS'nin "yer teslimi, imza vadesi ve TÜFE yıl dönümü hatırlatması bilinçli olarak yazılmadı" notu
(`events.md`) OAB Defteri panosunda doğal olarak kapanır; bu üç vade panoya eklenmeli.

### 3.5 `documents.py`

| Fonksiyon | Kaynakta | Sınıf | Not |
|---|---|---|---|
| `render_pdf` | WeasyPrint, tembel import | UYARLA | Aile WeasyPrint kullanıyor; OAB'de docx (python-docx) + PDF birlikte (§7.1) |
| `_letterhead` | `core` antet kimliği | UYARLA | Okul kartı |
| `render_davetiye`, `render_gundem`, `render_tutanak`, `render_yeter_sayi_yok`, `render_aday_listeleri` | GK seti | UYARLA | §5 |
| `render_yk_faaliyet_raporu`, `render_gelir_gider_cizelgesi`, `render_tahmini_butce`, `render_dk_faaliyet_raporu` | Mali set | UYARLA | K1 |
| `_ihale_commission` | Yalnız IHALE komisyonu, başkan başta | AYNEN | — |
| `_tender_ctx` | Ortak bağlam + mevzuat atfı | UYARLA | Kantin ve servis ayrı atıf |
| `render_ihale_ilani` … `render_tek_katilimci_tutanagi` (9) | Servis seti | UYARLA | Söz dağarcığı; kantin seti ayrıca |
| `render_sozlesme_taslagi` | Sözleşme türünden bağımsız `SERVIS_CONTRACT_ARTICLES` | UYARLA | Kantinde Yön. EK-2 tam metni (korpusta var) |
| `build_imza_surkusu_xlsx` | `core` öğrenci + veli listesi | UYARLA | §2.1 |

Yorum: OYS'nin en değerli evrak ilkesi **"tek kaynak"** (seçilen üyeler, tarihler, puanlar tek kayıttan; tutanak,
aday listesi ve faaliyet raporu birbiriyle çelişemez) AYNEN alınmalıdır.

### 3.6 `file_storage.py`

| Fonksiyon | Kaynakta | Sınıf | Not |
|---|---|---|---|
| `compute_sha256`, `generate_uuid_filename`, `max_upload_bytes` | Bütünlük, tahmin edilemez ad, boyut sınırı | AYNEN | — |
| `detect_mime`, `validate_upload` | libmagic; yalnız PDF | UYARLA | Paketleme (§2.1); tarama görüntüsü (JPEG) gerekebilir — karar F0-8 |
| `save_attachment`, `absolute_path`, `_bidder_dir` | `MEDIA_ROOT/bidder_docs/bidder_<id>/<uuid>.pdf`, 0o750/0o640 | UYARLA | Kullanıcı veri dizini, dosya şifrelemesi (özel nitelikli veri), yedekle birlikte |
| `FileValidationError`, `StoredFile` | — | AYNEN | — |

### 3.7 Uçlar, serileştiriciler, admin, göçler

| Bileşen | Kaynakta | Sınıf | Not |
|---|---|---|---|
| `views.py` (52), `urls.py` (54 uç) | İnce görünüm, servis çağrısı; yazmada denetim kaydı; hassas okumada günlük; liste uçları PII'siz | UYARLA | Aile DRF kullanıyor (§7.1); rol ve günlük katmanı değişir. Desen değerli |
| `serializers.py` (72) | Liste/detay ayrımı (TCKN, adres, vergi no listede yok) | UYARLA | K9 ile TCKN alanları zaten kalkar |
| `admin.py` (20 kayıt) | Django admin | ALMA | Masaüstünde admin yüzü yok |
| `migrations/` (10) | 0010 KVKK geri doldurma (ADR-0058) | ALMA | Şema sıfırdan |
| `apps.py`, `signals.py`, `events.md` | — | ALMA | — |

---

## 4. Kural sabitleri envanteri

Durum sütunu: **UYUMLU** (kanonik metinle aynı) · **ÇELİŞKİ** (kanonik metinden farklı) · **KISMİ** (değer doğru,
kapsam ya da anlam eksik) · **EKSİK** (hüküm var, kodda yok) · **ATIFSIZ** (kodda madde atfı yok) ·
**DOĞRULANMADI** (kanonik metin elde değil). F1c'de sürümlü kural paketine yalnız UYUMLU ya da düzeltilmiş
değerler girer (altın kural 1).

### 4.1 Tablo

| # | Kural | Değer | Kod konumu | Koddaki atıf | Kanonik dayanak | Durum |
|---|---|---|---|---|---|---|
| 1 | GK yeter sayısı tabanı | Dönemin DÜŞTÜ olmayan üyelik kayıt sayısı (ADAY dâhil) | `services.py:255-259` | "madde 9/2" | Yön. md. 9/2: YK ve DK asıl + yedek üye sayısı = 16 | **ÇELİŞKİ** |
| 2 | GK yeter sayısı çarpanı | ×4 | `services.py:260` | "madde 9/2" | md. 9/2, 9/6 | UYUMLU |
| 3 | Küçük okul çarpanı | ×2 | `services.py:260` | "madde 9/2" | md. 9/2, 9/6 | UYUMLU |
| 4 | Küçük okul eşiği | mevcut < 100 | `services.py:260` | "madde 9/2" | md. 9/2 "yüzün altında" | UYUMLU (mevcut elle giriliyor) |
| 5 | 2. toplantı yeter sayısı | 0 | `services.py:253-254` | "madde 9/2" | md. 9/2 | UYUMLU (olağanüstüde uygulanabilirliği §8 S-3) |
| 6 | Olağanüstü GK, dönemsiz | yeter sayı 0 | `services.py:293-302` | — | md. 9/6: ×4/×2 | **ÇELİŞKİ** |
| 7 | 2. toplantı süresi | — | yok (yalnız ADR-0028) | — | md. 9/2 "en geç otuz gün" | **EKSİK** |
| 8 | GK son günü | — | yok | — | md. 9/1 Ekim sonu; yeni okulda 2 ay | **EKSİK** |
| 9 | İlan süresi | ≥ 15 gün | `services.py:284` | "madde 9/3" | md. 9/3, 9/6 | UYUMLU |
| 10 | Olağanüstü GK üye başvurusu | %10 | `_base.py:93` (yalnız etiket) | "yüzde onu" | md. 9/6 | ATIFSIZ, denetim yok |
| 11 | YK bileşimi | 5 asıl + 5 yedek | `services.py:412-415` | "madde 12/1" | md. 12/1, 11/1-a | KISMİ (kişi türü denetlenmiyor) |
| 12 | DK veli koltuğu | 1 asıl + 1 yedek; veli, kursiyer **ve hayırsever** | `services.py:120, 427-433` | "madde 14/1" | md. 14/1, 11/1-b: veli ya da 18 yaşını doldurmuş kursiyer | **ÇELİŞKİ** (hayırsever) |
| 13 | DK öğretmen koltuğu | 2 asıl + 2 yedek | `services.py:435-441` | "madde 14/1" | md. 14/1, 11/1-b | UYUMLU |
| 14 | YK dönem sınırı | Başkan ≤ 4 | `services.py:124` | "madde 12/4" | md. 12/4 "başkan ve üyeleri en fazla dört defa" | **KISMİ** (üyeler sayılmıyor) |
| 15 | DK başkanı dönem sınırı | ≤ 3 | `services.py:125` | "madde 14/3" | md. 14/3 | UYUMLU |
| 16 | Aynı anda birden fazla birlik yönetimi | — | yok | — | md. 12/4 2. cümle | EKSİK (beyan) |
| 17 | Özürsüz devamsızlık | üst üste 3 → düşer (yalnız YK) | `services.py:651-654` | "madde 13/6" | md. 13/6 | UYUMLU (yedek çağırma yok) |
| 18 | YK toplantı ve karar yeter sayısı | — | yok | — | md. 13/3: en az 4 üye, karar 3, ayda bir | **EKSİK** |
| 19 | Görev bölümü süresi | — | yok | — | md. 12/3 (yedek çağrılınca da), 14/1: bir hafta | **EKSİK** |
| 20 | YK karar yeter sayısının altına düşme | — | yok | — | md. 13/8: bir ay içinde olağanüstü GK; md. 7/2 | EKSİK |
| 21 | DK incelemesi | — | yalnız yorum/etiket (`models/inspection.py` belge başı) | "md.14/4" | md. 14/4: yılda en az iki | EKSİK (sayılmıyor) |
| 22 | DK öğretmeninin başka kurumda görevi | — | yok | — | md. 14/6: 4 aydan fazla → yedek | EKSİK |
| 23 | Elden bağış | — | yok | — | md. 16/3: en geç 5 iş günü | **EKSİK** |
| 24 | Makbuz koçanı | — | yok (yalnız cilt no + seri aralığı) | "madde 16/5-7" | md. 16/5: seri, cilt, sıra; 50 asıl + 50 koçan; mühür; karar defterine kayıt | **EKSİK** |
| 25 | Arz bedeli, kiraya verme | %3 | `_base.py:367` | "md.17/1-a-1" | md. 17/1-a-1; Yön. EK-2 md. 7 | UYUMLU |
| 26 | Arz bedeli, birlikçe işletme | %1 | `_base.py:368` | "md.17/1-b-1" | md. 17/1-b-1 | UYUMLU |
| 27 | Net dağıtım | %80 birlik / %10 ilçe / %10 il | `_base.py:370-372` (il payı kodda kalan olarak, `services.py:1660`) | "md.17/1-a-2, b-2" | md. 17/1-a-2, b-2; Yön. EK-2 md. 7 | UYUMLU |
| 28 | İl merkezi istisnası | ilçe 0, il %20 | `services.py:1661-1663`; alan `models/contract.py:208` | yardım metni "büyükşehir olmayan il merkezi" | md. 17/1-a, b son cümle: "Büyükşehir statüsünde olmayan **il merkezlerindeki** birlikler" | **ÇELİŞKİ** (alan "büyükşehir mi" diye soruyor) |
| 29 | Arz bedeli vadesi | çeyreği izleyen ayın **20**'si; takvim çeyrekleri | `services.py:1614-1623` | "md.17/1-a-1" | Yön. md. 17/1-a-1, b-1: "takip eden ayın yirmisine kadar"; **Yön. EK-2 md. 7: "dönemi takip eden ayın onuncu günü sonuna kadar"** | **ÇELİŞKİ** (Yönetmelik ile EK-2 arasında; kod EK-2'yi görmüyor). Çeyreklerin başlangıcı DOĞRULANMADI |
| 30 | Gecikme zammı | ay = ⌈gün/30⌉ × oran × arz bedeli; oran elle | `services.py:1700-1704` | "6183/51" (`tasks.py:118`) | md. 17/1-b-6 → 6183 md. 51 | DOĞRULANMADI (6183 korpusta yok; ay kesirlerinin hesabı teyit edilmeli) |
| 31 | Kira sözleşmesi tek süre | ≤ 5 yıl (5 × 365 gün) | `_base.py:380`; `services.py:1517` | "md.21" | md. 21/3 | UYUMLU (değer); artık yılda sınırda yanlış uyarı riski |
| 32 | Toplam kira süresi | ≤ 20 yıl, zincirdeki en eski başlangıçtan | `_base.py:381`; `services.py:1520-1529` | "md.21" | md. 21/4; **Genelge 2024/35 III**: 31.05.2005 tabanı, rekabetçi ihalede yeni başlangıç, dondurulan süre ve 540 gün ilavesi | **KISMİ** (Genelge hesabı yok) |
| 33 | Yer teslimi | imzadan 15 gün | `_base.py:382` | yorum "imzadan 15 gün" | md. 21/2 (+ kiracının 15 gün içinde 10 günlük noter ihtarı) | UYUMLU ama **kullanılmıyor** |
| 34 | TÜFE artışı | 2. yıldan, `IndexRate.value` % | `services.py:1728, 1737` | "md.21" | md. 21/3: TÜFE on iki aylık ortalamalara göre % değişim | KISMİ (değerin anlamı belirsiz) |
| 35 | Öğrenci mevcudunda %25 değişim | — | yok | — | md. 21/3: muhammen bedel yeniden tespit | EKSİK |
| 36 | Hısımlık | 2. derece kan ve kayın; yalnız kiralama; sert engel | `services.py:1253-1256` | "madde 20/8" | md. 20/8 | UYUMLU |
| 37 | Kantin belge şartı | tek mantıksal alan; sert engel | `services.py:1258-1259` | "madde 20/4" | md. 20/4 (+ md. 20/5 esnaf odası belgesi) | KISMİ (md. 20/5 yok) |
| 38 | İstekli suç engeli | sert engel | `services.py:1251-1252` | "madde 12/5" | İstekli için md. 20/11 (12/5'teki suçlara gönderir) | **ÇELİŞKİ** (atıf) |
| 39 | Kantin ilanında istenen belgeler | 5 madde (portör, adli sicil dâhil) | `_base.py:538-544` | "md.20 (TASLAK)" | md. 20/4-5 istekliden; portör ve adli sicil md. 20/6'ya göre **çalışandan** | **ÇELİŞKİ** |
| 40 | Sözleşme fesih bildirimi | 15 gün | `sozlesme_taslagi.html` madde 7 metni | yok | Yön. md. 22/1-e (kantin); Servis EK-2 md. 7 DOĞRULANMADI | ATIFSIZ |
| 41 | Servis ilanı | ≥ 7 gün | `services.py:1411-1420` | "md.5/3" | Servis U-E md. 5/3 | UYUMLU (yalnız kesinleştirmede denetleniyor) |
| 42 | Servis komisyonu | müdür başkan + birlik başkanı + 1 öğretmen + 2 veli | `services.py:1137-1148` | "usul-esaslar md.3" | Servis U-E md. 3/1-e (asıl + yedek; varsa vakıf temsilcisi) | UYUMLU (yedekler sayılmıyor) |
| 43 | Muhammen bedel komisyonu | MEM temsilcisi başkan + okul müdürü/MY + birlik başkanı + millî emlak + meslek odası | `services.py:1149-1158` | "md.19" | md. 19/1 | UYUMLU |
| 44 | Kiralama ihale komisyonu | MEM temsilcisi başkan + birlik başkanı + defterdarlık | `services.py:1159-1166` | "md.20" | md. 20/3 | UYUMLU |
| 45 | Servis sözleşme süresi | 1-3 "eğitim-öğretim dönemi" | `_base.py:375-376` | "md.8" | Servis U-E md. 8/4 | UYUMLU (değer); şablon "eğitim-öğretim **yılı**" basıyor — anlam DOĞRULANMADI |
| 46 | Sözleşme imzası | tebliğden 10 gün | `_base.py:377` | "md.8" | Servis U-E md. 8/6 | UYUMLU |
| 47 | Mülki amir onayı ve tebliğ | — | yok | — | Servis U-E md. 8/5-6: 5 iş günü + 5 iş günü | EKSİK |
| 48 | Servis taksidi | ≤ 9 (+ DB kısıtı 1-9) | `_base.py:374`; `models/contract.py:164-168` | "EK-2 md.6" | Servis EK-2 md. 6/a | UYUMLU |
| 49 | Taksit vadesi | ayın 15'i | `_base.py:378` | "EK-2 md.6" | Servis EK-2 md. 6/b "1 ile 15'i arası" | UYUMLU (yorum: son gün) |
| 50 | EK-3 puanlama | 5 kriter × 5 = 25; kademeler | `_base.py:458-513` | "EK-3" | Servis U-E EK-3 | UYUMLU |
| 51 | Servis değerlendirme yöntemi | varsayılan PUANLAMA, aksi uyarı | `services.py:1065-1073` | "usul-esaslar" | Servis U-E md. 8/2 (komisyon değerlendirmesi), 8/3 (EK-3 yalnız itiraz/yeni okul) | **ÇELİŞKİ** |
| 52 | En düşük teklif | enum değeri | `_base.py:199` | "yürürlükten kalkan 10.01.2018 metni" | Yürürlükte değil | ALMA |
| 53 | Kantin hijyen denetimi | yılda ≥ 1; büyük uygunsuzluk aynı gün, küçük 3 iş günü | `_base.py:352`; `models/inspection.py:55-60` | "Genelge 2020/8" | Genelge 2020/8 (ilçe ekibinin müdahale süreleri) | KISMİ (anlam: düzeltme termini değil) |
| 54 | MEM denetimi | yılda ≥ 1 | `_base.py:350` (etiket) | "md.26" | md. 26/1 | UYUMLU (denetim yok) |
| 55 | Hatırlatma eşikleri | 7/3/1/0 gün | `tasks.py:24` | — | mevzuat değil | ATIFSIZ → ALMA |
| 56 | DK kontrol listesi | 18 madde | `_base.py:431-450` | "[İKİNCİL]" | GNL-OAB-FR-012 (22 kalem), TKB E.4 | ATIFSIZ (madde 6 KVKK'lı) |
| 57 | Standart gündem | 11 madde | `_base.py:412-424` | "madde 10-11" | md. 10, 11 | KISMİ (md. 11/1-e yetkilendirme ve 11/1-f öneriler maddesi yok) |
| 58 | Bütçe kategorileri | 5 gelir + 8 gider | `_base.py:390-405` | yorumda "4 gelir + 12 gider" | TEFBİS işlem tipleri (2009 kılavuzu EK-A) | ATIFSIZ (yorumla sayı da tutmuyor) |
| 59 | Kuruş artığı | il MEM payına | `services.py:1660` | — | Yönetmelik sessiz | ATIFSIZ (F0-8 kararı) |
| 60 | Dosya | yalnız PDF; boyut `settings.MAX_UPLOAD_SIZE_MB` | `file_storage.py:25, 44-46` | — | teknik | ATIFSIZ (teknik) |
| 61 | TCKN | 11 hane | `models/person.py:47`; `serializers.py:215-218` | — | teknik | ALMA (K9) |
| 62 | Kantin aylık kirası | — | yok | — | Yön. EK-2 md. 4 (ayın 5-15'i, yarıyıl ayında yarım, 9 ya da 12 ay); md. 19/3 | **EKSİK** |
| 63 | Ceza, tazminat, kısa süreli kullanım bedellerinde arz | — | yok | — | md. 17/1-b-4: %3 | EKSİK |
| 64 | İhaleden yasaklama | — | yok | — | md. 22/5: bir yıl | EKSİK (bilgi) |

### 4.2 F1c kural paketi v1 listesiyle eşleme

| F1c kalemi | OYS'de | Konum | Durum |
|---|---|---|---|
| Yeter sayı çarpanları ve 100 eşiği | Var | §4.1 satır 1-6 | Taban düzeltilir |
| İlan 15 gün | Var | satır 9 | Aynen |
| İkinci toplantı 30 gün | **Yok** | satır 7 | Yeni |
| Görev bölümü 1 hafta | **Yok** | satır 19 | Yeni |
| Organ bileşimleri | Kısmen | satır 11-13, 42-44 | Divan, alım komisyonu (en az 3, md. 18/1), temsilciler yeni |
| Dönem sınırları | Kısmen | satır 14-15 | YK üyeleri eklenir |
| YK toplantı yeter sayısı 4, karar 3 | **Yok** | satır 18 | Yeni |
| Devamsızlık 3 | Var | satır 17 | Aynen + yedek çağırma |
| Elden bağış 5 iş günü | **Yok** | satır 23 | Yeni (iş günü takvimi gerekir) |
| Arz %3 / %1 | Var | satır 25-26 | Aynen |
| Pay %80/%10/%10, il merkezinde il %20 | Var | satır 27-28 | Alan anlamı düzeltilir |
| Arz vadesi 20'si (EK-2 md. 7: 10'u) | Yalnız 20'si | satır 29 | Karar gerekir (§8 S-5) |
| Makbuz 50 asıl + 50 koçan | **Yok** | satır 24 | Yeni |
| SGK saklama 10 yıl | OAB modülünde yok (bordro modülünde, ADR-0029) | — | Yeni (K3 personel) |

Kantin ve servis kuralları (satır 31-53) F1c'de değil, F5-F6'da kural paketine girer.

### 4.3 İşaretli değerlerin özeti

- **Yönetmelikle çelişen:** satır 1 (yeter sayı tabanı), 6 (olağanüstü dönemsiz GK), 12 (DK'de hayırsever), 28
  (il merkezi istisnası), 29 (vade: Yönetmelik 20'si ↔ EK-2 10'u), 38 (suç engeli atfı), 39 (kantin ilanı
  belgeleri), 51 (servis değerlendirme yöntemi).
- **Kapsamı eksik:** satır 11, 14, 32, 34, 37, 53, 57.
- **Atıfsız:** satır 10, 40, 55, 56, 58, 59, 60.
- **Doğrulanmadı:** satır 29 (çeyrek başlangıcı), 30 (6183/51), 45 (dönem ↔ yıl).

---

## 5. Evrak şablonları (21 dosya)

"İhale" sütunu görünür metindeki "ihale" sayısıdır (şablon yorumları hariç). Hiçbir şablonda "eksiltme" yok;
"teklif" şablon metninde yok ama veriyle basılabilir: `komisyon_karari` durum etiketini (`TEKLIF_TOPLAMA` =
"Teklif toplama"), `ihale_ilani` değerlendirme yöntemi etiketini ("En düşük teklif …"), `puanlama_cetveli`
kriter adını (EK-3'ün 4. kriteri mevzuat lafzında "aynı okula teklif vermesi") basar.

| # | Dosya | Belge | Kullandığı veri | Dayanak (kod → doğrulanmış) | İhale | Sınıf | GNL karşılığı | Not |
|---|---|---|---|---|---|---|---|---|
| 1 | `davetiye.html` | GK toplantı davetiyesi | `GeneralAssembly` (tür, çağrı nedeni, ilan, 1. ve 2. toplantı, yer, yeter sayı, ilan günü), müdür adı | md. 9/3 (+9/2) | 0 | UYARLA | FR-002 | İmza "Okul Müdürü": md. 9/1 çağrıyı YK'ye verir (yeni okulda müdür) → başkan |
| 2 | `gundem.html` | GK gündemi | `GeneralAssembly`, `AgendaItem` | md. 9/4 | 0 | UYARLA | FR-002 | Tohum md. 11/1-e, f içermiyor |
| 3 | `tutanak.html` | GK toplantı tutanağı | `GeneralAssembly`, `AgendaItem`, `AssemblyMinutes`, `OrganMembership` (SECILDI) | md. 10 | 0 | UYARLA | FR-004 | İbra sonucu ve oy sonuçları yok; divan başkanı + kâtip imzası doğru |
| 4 | `yeter_sayi_yok.html` | Yeter sayı bulunamadığına dair tutanak | `GeneralAssembly` (yeter sayı, katılan, 2. toplantı) | md. 9/2 | 0 | UYARLA | FR-003 | 30 gün sınırı basılmıyor; imza birlik başkanı + okul müdürü |
| 5 | `aday_listeleri.html` | YK ve DK aday listeleri | `OrganMembership` (ADAY), kişi türü | "madde 11" → md. 10/1-d, 11/1-a, b | 0 | UYARLA | FR-004 (kısmen; DOĞRULANMADI) | DK öğretmen koltukları GK'da oylanmaz (öğretmenler kurulu seçer) → ayrılmalı |
| 6 | `yk_faaliyet_raporu.html` | YK faaliyet raporu ("003") | `OabBudget`, `BudgetLine` (gerçekleşen), YK asıl üyeleri | md. 11/1-c | 0 | UYARLA (K1) | FR-023 | Tutarlar işlem kayıtlarından; imza YK asıl üyeleri |
| 7 | `gelir_gider_cizelgesi.html` | Gelir-gider çizelgesi ("004") | `OabBudget`, `BudgetLine` | md. 11/1-c, 13/10 | 0 | UYARLA (K1) | FR-010, FR-023 | İmza "Okul Müdürü" → muhasip + başkan (md. 13/4) |
| 8 | `tahmini_butce.html` | Tahmini bütçe ("006") | `OabBudget`, `BudgetLine` (tahmini) | md. 11/1-d, 13/9 | 0 | UYARLA | FR-010 | İmza "Okul Müdürü" → YK (md. 13/9); "onaylandı" → "görüşüldü" |
| 9 | `dk_faaliyet_raporu.html` | DK ara / nihai raporu ("005") | `AuditReport`, DK asıl üyeleri | md. 14/4-5 | 0 | UYARLA | FR-012 (ara), FR-013 (nihai) | Liste FR-012 ile tazelenir; usulsüzlükte olağanüstü GK çağrısı (md. 14/5) metni |
| 10 | `ihale_ilani.html` | Servis çalıştırma işi ilanı | `Tender`, komisyon başkanı, belge listesi | Servis U-E md. 5/3-4, 6/1 | 3 | UYARLA | — | Başlık hep "servis"; kiralama için uç 400 döndüğünden üretilmiyor |
| 11 | `ilan_asma_tutanagi.html` | İlan asma tutanağı | `Tender`, komisyon | md. 5/3 | 1 | UYARLA | — | — |
| 12 | `ilan_indirme_tutanagi.html` | İlan indirme tutanağı | `Tender`, komisyon | md. 5/3 | 1 | UYARLA | — | İndirme tarihi = dosya teslim son günü varsayımı |
| 13 | `sartname_teslim_tutanagi.html` | Tip şartname teslim tutanağı | `Tender`, `Bidder` | md. 5/1 | 0 | UYARLA | — | — |
| 14 | `evrak_teslim_tutanagi.html` | Başvuru evrakı teslim tutanağı | `Tender`, `Bidder` | md. 7 | 2 | UYARLA | — | — |
| 15 | `evrak_kontrol_cetveli.html` | Evrak kontrol ve tespit tutanağı | `Bidder`, `BidderDocument` (Mevcut/Eksik) | md. 8/1 | 1 | UYARLA | — | — |
| 16 | `puanlama_cetveli.html` | EK-3 puanlama cetveli | `Bidder`, `BidderScore`, `ScoringCriterion` | md. 8/3, EK-3 | 0 | UYARLA | — | Yalnız itiraz / yeni okul hâlinde |
| 17 | `komisyon_karari.html` | Taşımacıyı tespit komisyon kararı | `Tender.winner`, toplam puan, `TenderApproval` | md. 8/2, 8/5, 4/1 | 4 | UYARLA | — | "Oy birliği ile" sabit basılıyor (md. 4/1 çoğunluk, muhalif şerhi); karar no "OAB-İhale-{pk}" |
| 18 | `tek_katilimci_tutanagi.html` | Tek katılımcı tutanağı | `Tender`, tek `Bidder` | kod "md. 8/7" → md. 8/7 başvuru olmaması / uygun görülmemesi hâlidir; tek istekli metinde yok | 1 | UYARLA | — | Atıf düzeltilir ya da saha belgesi diye işaretlenir |
| 19 | `sozlesme_taslagi.html` | Servis / kira sözleşmesi taslağı | `OabContract`, `Bidder`, `ContractInstallment`, komisyon, 10 madde başlığı | Servis U-E md. 10, Servis EK-2 | 0 | UYARLA (servis) | — (kantin izleme FR-021) | Kirada da servis maddelerini ve "Taşımacı" tarafını basıyor; kantinde Yön. EK-2 (25 madde) tam metni korpusta var, "[şablon]" boşlukları doldurulur |
| 20 | `_commission_signatures.html` | Parça: komisyon imza ızgarası | `TenderCommissionMember` | md. 3/1-e | 0 | UYARLA | — | Yalnız ad + görev (TCKN yok) — ilke AYNEN |
| 21 | `_compliance_warnings.html` | Parça: mevzuat uyarıları kutusu | `Tender.compliance_warnings/justification` | uyarı + gerekçe deseni | 0 | UYARLA | — | Yorum: resmî evraka uyarı kutusu basmak yerine gerekçe iç kayıtta kalmalı; karar F0-8 |
| — | `documents.build_imza_surkusu_xlsx` (kod) | GK katılımcı imza cetveli | `core` öğrenci + sorumlu veli | md. 10/1-a | 0 | UYARLA | FR-003 | §2.1 |

**Genel OAB setinde olup OYS'de karşılığı olmayanlar:** FR-001 (işlem dosyası kapak ve kontrol listesi), FR-005
(sonuç bildirimi ve devir-teslim), **FR-006** (YK görev bölümü ve imza yetkisi), FR-007 (YK aylık toplantı ve
karar tutanağı), FR-008 (toplantı ve katılım izleme), FR-009 (müdüre aylık bildirim), **FR-011** (DK görev
bölümü), FR-014 (bağış), FR-015 (defter, makbuz tasdik-kayıt), FR-016 (harcama talebi), FR-017 (alım komisyonu),
FR-018 (harcama belgesi ve ödeme onayı), FR-019 (personel), FR-020 (etkinlik/kampanya), FR-021 (kantin kira, arz
ve pay izleme), **FR-022** (temsilci görevlendirme) ve RH-001 (rehber). F1c'nin ilk üç evrakının (FR-006,
FR-011, FR-022) **hiçbiri OYS'de yok**; evrak hattı GNL docx'lerinden kurulur.

---

## 6. Testler (373)

### 6.1 Dosya bazında

Bütün testler `factories.py` üzerinden `core.SchoolYearFactory`'ye bağlıdır; AYNEN testlerde de fabrika ve
import yolları mekanik olarak değişir. API testleri OYS rollerini (öğretmen/memur 403, anonim 401) ve
`apps.denetim` günlüğünü sınadığından hepsi UYARLA'dır (K2, ailenin günlüğü).

| Dosya | Test | Ne sınıyor | AYNEN | UYARLA | ALMA | Gerekçe |
|---|---|---|---|---|---|---|
| `test_assembly.py` | 8 | Yeter sayı ×4/×2/0, 15 gün uyarı + gerekçe, 2. toplantı bağı, gündem tohumu | 6 | 2 | 0 | İki yeter sayı testi taban sabitlenince sadeleşir (beklenen 64/32 aynı) |
| `test_assembly_write.py` | 9 | GK planlama, sonuç, tutanak uçları | 0 | 9 | 0 | API, roller |
| `test_audit.py` | 3 | 18 madde tohumu, usulsüzlük bayrağı | 2 | 1 | 0 | 18 → yeni liste |
| `test_audit_write.py` | 9 | DK raporu uçları | 0 | 9 | 0 | API; DK yazma yetkisi K2'de açık |
| `test_bidder.py` | 10 | Suç, hısımlık, belge engelleri; puan, pazarlık, en düşük, tek katılımcı, eşitlik | 6 | 3 | 1 | Atıf 20/11; servis yöntemi; en düşük teklif ALMA |
| `test_bidder_document_views.py` | 6 | Dosya yükleme/indirme, MIME, hassas okuma günlüğü | 0 | 6 | 0 | Yerel şifreli saklama, roller |
| `test_bidder_write.py` | 11 | İstekli ve puan uçları | 0 | 11 | 0 | API; gerçek kişi K9 |
| `test_board.py` | 6 | Katılım, 3 mazeretsiz devamsızlık, seri bozulması, DK'de düşme yok, taslak karar | 5 | 1 | 0 | Karar defteri alanları |
| `test_board_write.py` | 12 | Toplantı, toplu katılım, karar uçları | 0 | 12 | 0 | API |
| `test_budget.py` | 11 | Kategori tohumu, satır, bordro önerisi, uyum, tek bütçe, KVKK bayrakları | 1 | 5 | 5 | K1; K3 (5 bordro testi) |
| `test_budget_write.py` | 8 | Bütçe ve satır uçları | 0 | 8 | 0 | API; K1 (gerçekleşen elle girilmez) |
| `test_commission_write.py` | 7 | Komisyon ucu, bileşim uyarısı | 0 | 7 | 0 | API |
| `test_compliance_write.py` | 12 | Uyum, endeks, makbuz koçanı uçları | 0 | 12 | 0 | API; koçan genişler |
| `test_contract.py` | 5 | Servis süresi, kiralama alanı, ≤ 9 taksit, yarıyıl, kirada taksit engeli | 4 | 1 | 0 | Kirada aylık takvim gelir |
| `test_contract_reminders.py` | 6 | Vade seçicileri (3), beat taraması (3) | 0 | 3 | 3 | Seçiciler pano için; Celery ALMA |
| `test_contract_write.py` | 12 | Sözleşme ve taksit uçları | 0 | 12 | 0 | API |
| `test_document_views.py` | 9 | GK evrak uçları, imza cetveli günlüğü | 0 | 9 | 0 | API, docx, `core` yok |
| `test_documents.py` | 9 | GK PDF'leri, XLSX, tutanak servisleri | 2 | 7 | 0 | Biçim docx + PDF; tek kaynak ilkesi korunur |
| `test_financial_documents.py` | 10 | Mali özet, 4 mali PDF, günlük | 0 | 10 | 0 | K1, imza blokları |
| `test_inspection.py` | 3 | 4 konu, kapanış, KVKK bayrağı | 2 | 1 | 0 | KVKK bayrağı ailenin mekanizmasına bağlı |
| `test_kimlik_write.py` | 14 | Dönem ve kişi uçları; TCKN şifreleme ve tekilliği | 0 | 10 | 4 | K9 (4 TCKN testi); ders yılı `core`'dan değil |
| `test_membership_lifecycle.py` | 10 | YK/DK bileşim uyarıları, başkan sınırı, düşürme | 7 | 3 | 0 | DK'de hayırsever; md. 12/4 kapsamı |
| `test_membership_write.py` | 9 | Üyelik uçları | 0 | 9 | 0 | API |
| `test_models.py` | 24 | Kişi kör indeksi ve TCKN tekilliği (6), ad, dönem kısıtları (5), üyelik şeması (8), KVKK bayrakları (3), puan tekilliği (1) | 14 | 4 | 6 | K9 (6 TCKN testi); beyan alanı sadeleşir |
| `test_module_flag_guard.py` | 2 | ADR-0035 bayrağı | 0 | 0 | 2 | Bayrak yok |
| `test_notifications.py` | 6 | Uyum hatırlatması (4), üye düşme bildirimi (2) | 0 | 0 | 6 | Celery/bildirim yok; pano testleri yeni yazılır |
| `test_read_assembly.py` | 12 | GK, toplantı, rapor okuma uçları | 0 | 12 | 0 | API |
| `test_read_budget.py` | 12 | Bütçe, uyum, koçan, endeks okuma | 0 | 12 | 0 | API, K1 |
| `test_read_contract.py` | 9 | Sözleşme ve denetim okuma | 0 | 9 | 0 | API |
| `test_read_kimlik.py` | 15 | Kişi, dönem, kadro okuma; PII dışlama | 0 | 15 | 0 | API, K9 |
| `test_read_tender.py` | 9 | İhale, alan, kriter okuma | 0 | 9 | 0 | API |
| `test_scoring.py` | 5 | EK-3 tohumu, 25 tavan, gerçek evrak örneği 23, ikili kriter | 4 | 1 | 0 | Örnek testin adı ve verisi gerçek bir firma adı taşıyor → uydurma adla yeniden yazılır |
| `test_share.py` | 6 | %3/%1, 80/10/10, il %20, kuruş korunumu, vade, gecikme zammı | 3 | 3 | 0 | Yerleşim türü, vade kararı, 6183 hesabı |
| `test_share_inspection_write.py` | 12 | Pay, TÜFE, denetim uçları | 0 | 12 | 0 | API |
| `test_tender.py` | 10 | Yöntem varsayılanı, muhammen bedel, silme kilidi, komisyon, onay, kesinleştirme, ret | 9 | 1 | 0 | Servis varsayılan yöntemi değişir |
| `test_tender_decision_write.py` | 12 | Kazanan, onay, kesinleştirme uçları | 0 | 12 | 0 | API |
| `test_tender_documents.py` | 18 | Servis seti 9 PDF + sözleşme + uçlar; kirada 400 | 0 | 18 | 0 | Docx, söz dağarcığı, kantin seti eklenince 400 değişir |
| `test_tender_write.py` | 13 | Alan, ihale, muhammen bedel uçları | 0 | 13 | 0 | API |
| `test_tufe.py` | 5 | İlk yıl artış yok, 2. yıl, oran yoksa hata, serviste engel, son endeks | 4 | 1 | 0 | Endeks değerinin anlamı |
| `test_views.py` | 4 | Kişi detay ucu, günlük, yetki | 0 | 4 | 0 | TCKN kalkar; telefon detayında günlük |
| **Toplam** | **373** | | **69** | **277** | **27** | |

| Özet | Test | Oran |
|---|---|---|
| AYNEN | 69 | %18,5 |
| UYARLA | 277 | %74,3 |
| ALMA | 27 | %7,2 |
| ALMA gerekçe dağılımı | TCKN (K9) 10 · bordro (K3) 5 · Celery/bildirim 9 · modül bayrağı 2 · yürürlükten kalkan usul 1 | |

Yorum: "Testler OYS'den" beklentisi (ön değerlendirme §10 risk 7) iş kuralı düzeyinde karşılanır (69 test +
mantığı korunan UYARLA'lar); API ve evrak testleri yeniden yazılacak sayılmalıdır.

### 6.2 Kural testleri (F0-8 "mevzuat hükmü → test eşlemesi"ne girdi)

"Durum" sütunu, testin sınadığı kodun kanonik metinle ilişkisidir (§4).

| Test (dosya :: ad) | Hüküm | Madde | Durum |
|---|---|---|---|
| `test_assembly` :: `test_compute_assembly_quorum_100_ustu_ogrenci` | Yeter sayı ×4 (16 → 64) | Yön. 9/2 | Test tam kadroyla kurulduğundan taban hatasını yakalamaz |
| `test_assembly` :: `test_compute_assembly_quorum_100_alti_ogrenci` | Mevcut < 100 → ×2 (32) | 9/2 | Aynı not |
| `test_assembly` :: `test_compute_assembly_quorum_ikinci_toplanti_cogunluksuz` | 2. toplantıda çoğunluk aranmaz | 9/2 | UYUMLU |
| `test_assembly` :: `test_schedule_general_assembly_yeterli_ilan_suresi_uyarisiz` | İlan ≥ 15 gün | 9/3 | UYUMLU |
| `test_assembly` :: `test_schedule_general_assembly_13_gun_gerekcesiz_reddedilir` | < 15 gün → gerekçe zorunlu | 9/3 + altın kural 3 | UYUMLU |
| `test_assembly` :: `test_schedule_general_assembly_13_gun_gerekceyle_gecer` | Gerekçeyle geçer | 9/3 + altın kural 3 | UYUMLU |
| `test_assembly` :: `test_schedule_general_assembly_ikinci_toplanti_baglantisi` | 2. toplantı ilk toplantıya bağlı | 9/2 | 30 gün sınanmıyor |
| `test_assembly_write` :: `test_schedule_13_gun_gerekcesiz_400`, `test_schedule_13_gun_gerekceyle_201` | 15 gün (uç) | 9/3 | UYUMLU |
| `test_audit` :: `test_create_audit_report_uygunsuz_madde_usulsuzluk_bayragi_kaldirir`, `test_create_audit_report_tumu_uygun_usulsuzluk_yok` | Uygunsuzluk → usulsüzlük | 14/5 | UYUMLU (olağanüstü GK çağrısı akışı yok) |
| `test_audit_write` :: `test_update_uygunsuz_bulgu_irregularity_true`, `test_update_hepsi_uygun_irregularity_false` | Aynı (uç) | 14/5 | UYUMLU |
| `test_bidder` :: `test_suc_engeli_sert` | Suç engeli | 20/11 (kod 12/5 der) | Atıf ÇELİŞKİ |
| `test_bidder` :: `test_kiralama_hisimlik_engeli` | 2. derece hısımlık | 20/8 | UYUMLU |
| `test_bidder` :: `test_servis_hisimlik_engeli_uygulanmaz` | Serviste hısımlık engeli yok | Servis U-E'de hüküm bulunmadı | DOĞRULANMADI |
| `test_bidder` :: `test_kiralama_belge_eksik_engeli` | Kantin belge şartı | 20/4 | KISMİ |
| `test_bidder` :: `test_puanlama_kazanan_en_yuksek`, `test_puanlama_esitlik_gerekce_ister` | EK-3 en yüksek puan | Servis U-E 8/3, EK-3 | Yalnız itiraz/yeni okul |
| `test_bidder` :: `test_pazarlik_kazanan_en_yuksek_teklif` | Kirada pazarlık, en yüksek | 20/2 (2886 md. 51/g) | UYUMLU |
| `test_bidder` :: `test_en_dusuk_teklif_kazanan` | En düşük teklif | yürürlükten kalkan 10.01.2018 metni | ALMA |
| `test_board` :: `test_ust_uste_3_mazeretsiz_devamsizlik_dusurur`, `test_mazeretli_devamsizlik_dusurmez`, `test_araya_bir_katilim_girerse_seri_bozulur` | Üst üste 3 özürsüz devamsızlık | 13/6 | UYUMLU |
| `test_board` :: `test_dk_toplantisinda_otomatik_dusme_yok` | Kural yalnız YK | 13/6 (DK'de karşılığı yok) | UYUMLU |
| `test_board` :: `test_record_board_decision_taslak_varsayilan` | Karar el ile deftere yazılır, program taslak üretir | 13/5 | UYUMLU |
| `test_board_write` :: `test_attendance_ucuncu_mazeretsiz_devamsizlik_dusurur` | 13/6 (uç) | 13/6 | UYUMLU |
| `test_contract` :: `test_create_contract_servis_sure_uyarisi` | Servis 1-3 dönem | Servis U-E 8/4 | UYUMLU (dönem ↔ yıl) |
| `test_contract` :: `test_add_installments_9_gecer_10_engel` | ≤ 9 taksit | Servis EK-2 6/a | UYUMLU |
| `test_contract` :: `test_add_installments_yariyil_atlar` | Yarıyılda ücret yok | Servis EK-2 6/c | UYUMLU |
| `test_contract` :: `test_create_contract_kiralama_alan_uyarisi` | Kira sözleşmesinde alan | 21/1 (yorum) | UYUMLU |
| `test_contract_write` :: `test_create_contract_servis_sure_disi_gerekce_ister_400`, `test_add_installments_ondan_fazla_400` | 8/4, EK-2 6/a (uç) | — | UYUMLU |
| `test_membership_lifecycle` :: `test_validate_membership_composition_yk_eksik_uyari_uretir`, `..._yk_tam_uyarisiz` | YK 5+5 | 12/1, 11/1-a | UYUMLU (kişi türü yok) |
| `test_membership_lifecycle` :: `test_validate_membership_composition_dk_veli_ogretmen_ayrimi` | DK 1 veli + 2 öğretmen | 14/1 | Hayırsever ÇELİŞKİ |
| `test_membership_lifecycle` :: `test_dustu_koltuk_kompozisyon_sayimina_girmez` | Düşen koltuk sayılmaz | 13/6 (yorum) | UYUMLU |
| `test_membership_lifecycle` :: `test_promote_membership_baskan_5_kez_gerekcesiz_reddedilir`, `..._gerekceyle_gecer` | YK başkanı ≤ 4 | 12/4 | KISMİ (üyeler) |
| `test_membership_lifecycle` :: `test_promote_membership_dk_baskan_3_sinir_farkli_organda_etkilemez` | DK başkanı ≤ 3, organ bazında | 14/3 | UYUMLU |
| `test_membership_lifecycle` :: `test_drop_membership_gerekcesiz_reddedilir` | Düşürmede gerekçe | 7/2, 12/5, 13/6 | UYUMLU |
| `test_membership_write` :: `test_promote_baskan_donem_siniri_gerekce` | 12/4 (uç) | 12/4 | KISMİ |
| `test_models` :: `test_membership_dustu_gerekcesi`, `test_membership_yedek_sirasi` | Düşme gerekçesi; yedek oy sırası | 13/6 | UYUMLU |
| `test_models` :: `test_membership_uygunluk_beyani_alanlari` | Suç engeli beyanı | 12/5, 14/7 | UYUMLU (KVKK sadeleşmesi) |
| `test_models` :: `test_membership_ayni_kisi_farkli_organda_serbesttir` | Aynı kişi YK ve DK'de | Yasak bulunmadı | DOĞRULANMADI (§8 S-14) |
| `test_scoring` :: `test_ek3_seed_idempotent_ve_maks_25`, `test_tam_puan_25`, `test_puan_azamiyi_asamaz_sert_engel`, `test_ikili_kriter_yalniz_0_veya_max`, gerçek evrak örneği (23 puan) | EK-3 tablo | Servis U-E EK-3 | UYUMLU |
| `test_share` :: `test_kiraya_verme_yuzde_3_ve_dagitim` | %3 + 80/10/10 | 17/1-a; Yön. EK-2 md. 7 | UYUMLU |
| `test_share` :: `test_isletme_yuzde_1_ve_gider_dususu` | %1 + giderler düşülür | 17/1-b | UYUMLU |
| `test_share` :: `test_non_metropolitan_ilce_yok_il_yirmi` | İl %20 | 17/1 son cümleler | Alan anlamı ÇELİŞKİ |
| `test_share` :: `test_due_date_ceyrekten_turer` | Vade 20'si | 17/1-a-1 ↔ Yön. EK-2 md. 7 (10'u) | ÇELİŞKİ |
| `test_share` :: `test_gecikme_zammi` | 6183 gecikme zammı | 17/1-b-6 | DOĞRULANMADI |
| `test_tender` :: `test_create_tender_servis_varsayilan_puanlama` | Serviste puanlama varsayılan | Servis U-E 8/2-3 | ÇELİŞKİ |
| `test_tender` :: `test_create_tender_kiralama_pazarlik_ve_alan_uyarisi` | Kirada pazarlık | 20/2 | UYUMLU |
| `test_tender` :: `test_servis_muhammen_bedel_sert_engel`, `test_kiralama_muhammen_bedel_yazilir` | Muhammen bedel yalnız kirada | 19; Servis U-E 10/2 | UYUMLU |
| `test_tender` :: `test_servis_komisyon_uygun_gerekce_gerektirmez`, `test_servis_komisyon_baskan_sapmasi_uyari_gerekce` | Servis komisyonu bileşimi, birlik başkanı zorunlu | Servis U-E 3/1-e | UYUMLU |
| `test_tender` :: `test_finalize_onaysiz_sert_engel`, `test_onay_kesinlestirme_akisi`, `test_red_ihaleyi_iptal_eder` | Mülki amir onayı | Servis U-E 4/1, 8/5 | UYUMLU (5 iş günü yok) |
| `test_tender_decision_write` :: `test_finalize_olursuz_sert_engel_400` | 4/1 (uç) | — | UYUMLU |
| `test_tender_write` :: `test_estimated_price_servis_400`, `test_create_tender_kiralama_alansiz_gerekce_ister_400` | Muhammen bedel; kirada alan | 19; 17 | UYUMLU |
| `test_tufe` :: `test_ilk_yil_artis_yok`, `test_ikinci_yil_tufe_uygular` | İlk yıl ihale bedeli, sonra TÜFE | 21/3 | KISMİ (endeks anlamı) |
| `test_tufe` :: `test_tufe_servis_sert_engel` | TÜFE yalnız kirada | 21 | UYUMLU |

Toplam 71 test (bazı satırlar birden çok testi kapsar; `_write` dosyalarındakiler servis testlerinin uç aynasıdır,
`test_en_dusuk_teklif_kazanan` ALMA'dır).

**Testi olmayan, kural paketine girecek hükümler** (F0-8 eşlemesinde yeni test gerekir): 30 gün (9/2), Ekim sonu
(9/1), olağanüstü GK'de yeter sayı (9/6), YK üyeleri dönem sınırı (12/4), YK kişi türü ve müdür yasağı (12/1),
görev bölümü bir hafta (12/3, 14/1), YK toplantı 4 / karar 3 (13/3), md. 13/8, DK yılda iki inceleme (14/4),
elden bağış 5 iş günü (16/3), makbuz 50 + 50 (16/5), şartlı bağış (16/4), harcama zinciri ve en az 3 kişilik alım
komisyonu (18/1), müşterek imza (18/2), aylık bildirim (18/5), Yön. EK-2 md. 4 aylık kira, Yön. EK-2 md. 7 vadesi,
Genelge 2024/35 yirmi yıl hesabı, %25 öğrenci değişimi (21/3), yer teslimi 15 gün (21/2), huzur hakkı yasağı
(25/1), servis mülki amir onayı ve tebliğ 5 iş günü (8/5-6).

---

## 7. ADR-0028, ADR-0029, ADR-0035'ten değişen kararlar

| ADR / konu | ADR'de | OAB Defteri'nde | Gerekçe |
|---|---|---|---|
| 0028 · Modül yapısı | OYS'nin 15. modülü; ADR-0002 modül sınırları; yalnız public servis ve sinyalle konuşur | Bağımsız masaüstü program; modüller arası servis kenarları ve sinyaller kalkar | K2, K8; aile iskeleti |
| 0028 · Operatör | V1'de okul idaresi (ADMIN/MUDUR/MUDUR_YARDIMCISI); başkan ve muhasip veli olduğu için giriş yapmaz | **Rol bazlı yerel hesaplar:** MY, başkan, muhasip, sekreter yazar; DK ve müdür salt okur | **K2**; proje kuralı 6 (müdür YK üyesi değildir) |
| 0028 · Veli bağı | `linked_user` isteğe bağlı, `core` servisiyle çözülür | Çıkar; öğrencinin ayrılması elle işlenir | Çekirdek yok; KVKK veri en aza |
| 0028 · Gerçekleşen gelir-gider | Kategori bazlı dönem özeti (`BudgetLine.realized_amount`); "muhasebe DEĞİL" | **İşlem düzeyi**; özet işlem kayıtlarından hesaplanır; banka hareketiyle eşleme | **K1** |
| 0028 · TEFBİS | PDF içe aktarma; "manuel işaret YOK"; şema örnek PDF gelince | "TEFBİS'e girilecekler" listesi + "girildi" işareti + TEFBİS Excel çıktısıyla mutabakat; otomatik giriş yok | **K6** (sorulmadı; öneriyle ilerleniyor) |
| 0028 · Uyum hatırlatmaları | Celery beat + bildirim (pano ilanı, müdüre bildirim, arz vadesi) | Açılış ekranı + takvim; aynı yükümlülükler uyum kaydı ve ilgili modellerde | F0-6 planı; çevrimdışı tek bilgisayar |
| 0028 · Mevzuat kuralları | Uyarı + gerekçeli geçiş; sert engel değil | Aynı; sert engel yalnız hesap bütünlüğünde | Altın kural 3. OYS'deki istekli uygunluğu, taksit, onay engelleri yeniden sınıflanır (§8 S-12) |
| 0028 · Kantin işletme modu | Kiraya verme esas; %1 işletme pasif seçenek | Kurulumda "kiraya veriyor / kendisi işletiyor" seçimi; işletmede vergi ve VUK uyarısı | Ön değerlendirme §2.5 |
| 0028 · Servis değerlendirme | `KOMISYON_DEGERLENDIRME` (md. 8/2) varsayılan / `PUANLAMA` (EK-3) | ADR doğru, **kod ADR'ye uymuyor** (PUANLAMA varsayılan, komisyon değerlendirmesi enumu yok) → ADR'deki karar uygulanır; söz dağarcığı "taşımacının tespiti" | Servis U-E md. 8/2-3; proje kuralı 6 |
| 0028 · Resmî defterler | Yalnız ıslak imzaya hazır taslak; e-imza yok | Aynı + konum cümlesi; karar defteri sıra no, sayfa, "deftere işlendi" | Konum (bağlayıcı); md. 13/5, 23/2 |
| 0028 · Rol | Yeni global rol eklenmez | Dört yazar rol + iki salt okur rol | K2 |
| 0028 · Kişisel veri | TCKN ve telefon şifreli + kör indeks; sabıka uygunluk beyanı özel nitelikli belge eki | Kişide TCKN yok; telefon şifreli; beyan yalnız "alındı" işareti; bağışçı TCKN'si varsayılan kapalı, ayarla açılır | **K9**; ön değerlendirme §2.1 |
| 0028 · Veri modeli | ~24 varlık; `OabDocumentRecord` (evrak defteri) dâhil | Evrak defteri yeni yazılır (M10); `OabDocumentRecord` OYS'de hiç yazılmamış | Kodla ADR farkı |
| 0028 · Bütçe personel satırı | Bordro public servisinden öneri | Kalkar; personel özlük, izin, kıdem karşılığı sürüm 2 | **K3** |
| 0028 · Sinyaller | 5 sinyal; `student_enrollment_changed` dinleme planı | Hiçbiri | Bildirim altyapısı yok |
| 0028 · Evrak üretimi | WeasyPrint + openpyxl; gerçek evrakla birebir kabul | docx + PDF + xlsx; GNL-OAB-FR seti ile birleşir; kabul ölçütü aynı | Ön değerlendirme §7.1 |
| 0028 · Kesinleşme kilidi | `Tender` ve `OabContract` için kesinleşme kilidi riski | Genelleşir: kayıt silinmez, ters kayıt; kapanmış dönem kilitli | Altın kural 4 |
| 0028 · Mevzuat taslakları | 7 taslak kullanıcı teyidi bekliyor; teyitsiz değer koda gömülmez | `docs/mevzuat/` kanonik korpus + madde atfı kilidi; kural paketinde her değer madde taşır | Altın kural 1-2 |
| 0029 · Bordro modülü | OAB'nin kardeşi; parametrik motor, SGK/GİB XML; OAB doğrudan işveren | **Alınmaz** | **K3**. Not: ADR-0029 (07.2026) birliği doğrudan işveren yazıyor, pilot okulun dönem başı kayıtları (10.2026) hizmet alımı gösteriyor — K3'ün kapsamı açık |
| 0029 · Ters servis kenarı | `get_disbursement_signatories` → bordro banka listesi | Ödeme talimatı çıktısında aynı imza bloğu (md. 18/2) | İş kuralı değerli |
| 0029 · Saklama | Bordro belgeleri 10 yıl | Personel/SGK belgelerinde 10 yıl saklama kilidi (5510 md. 86) | Ön değerlendirme §2.5 |
| 0035 · Bayrakla pasifleştirme | `MODULE_OAB_ENABLED`; ara katman 404; beat sökümü; görev guard'ları; arayüz bayrağı | **Alınmaz**; program bağımsız | Konu dışı. Yorum: modül 11.07.2026'dan beri pasif olduğu için sahada bir tam yıl çalışmadı; "testler yeşil" saha kanıtı değildir |
| 0035 · OAB ↔ bordro arayüz bağı | OAB ön yüzü bordro ucuna bağımlı | Yok | K3 |

---

## 8. Açık sorular ve riskler

Her madde kimliklidir (S-n). "Öneri" bu belgenin yorumudur; karar F0-8 genel tasarımda ya da kullanıcıdadır.

### 8.1 Mevzuatla çelişkiler (koddan)

- **S-1 · GK yeter sayısı tabanı.** Kod kayıt sayıyor; Yönetmelik sabit 16'dan hesaplatıyor. Öneri: taban kural
  paketinden (YK 5+5 + DK 3+3), kayıtlara bakılmaz.
- **S-2 · Olağanüstü GK, dönemsiz.** Yeter sayı 0 çıkıyor (md. 9/6'ya aykırı); çağrı nedeni zorunlu değil.
  Öneri: olağanüstüde de ×4/×2; çağrı nedeni ve gerekçe zorunlu (ön değerlendirme §2.1 "sert (gerekçe)").
- **S-3 · Olağanüstü GK'de ikinci toplantı.** md. 9/2'deki "30 gün içinde çoğunluk aranmaksızın" hükmü md. 9/6'da
  tekrarlanmıyor; kod her GK için 2. toplantıda yeter sayıyı 0 yapıyor. DOĞRULANMADI — kullanıcıya sorulmalı.
- **S-4 · md. 12/4 kapsamı.** YK üyeleri de en fazla dört defa seçilebilir; kod yalnız başkanlığı sayıyor.
- **S-5 · Arz bedeli vadesi.** Yönetmelik md. 17/1 "izleyen ayın yirmisine kadar", Yön. EK-2 md. 7 "izleyen ayın
  onuncu günü sonuna kadar". Sözleşme kiracıyı bağlar, Yönetmelik birliği. Öneri: vade EK-2'deki 10'u (kiracı
  yükümlülüğü), 20'si (Hazine'ye son gün) ayrı uyarı; kullanıcıya sorulmalı.
- **S-6 · Servis taksitleri.** Servis EK-2 md. 6'ya göre ücreti veli taşımacıya öder; birliğin defterine girmez.
  OYS'nin sözleşme başına taksit takibi birliğin hangi işine yarıyor? Öneri: serviste taksit takibi çıkar ya
  da yalnız bilgi; aynı yapı kantin aylık kira takvimine dönüşür.
- **S-7 · Servis değerlendirme yöntemi.** Varsayılan md. 8/2 komisyon değerlendirmesi; EK-3 yalnız itiraz/yeni
  okul. Komisyon kararı şablonu "oy birliği ile" sabit basıyor (md. 4/1 çoğunluk, muhalif şerhi zorunlu) →
  oylama alanı gerekir.
- **S-8 · Atıf hataları.** İstekli suç engeli md. 20/11 (kod 12/5); tek katılımcı tutanağı md. 8/7'ye dayanmıyor;
  kantin ilanında portör/adli sicil istekliden isteniyor (md. 20/6 çalışandan ister); DK'de hayırsever (md. 14/1).
- **S-9 · İmza blokları.** Davetiye, tahmini bütçe, gelir-gider çizelgesi müdür imzalı → YK başkanı / muhasip.
  Aday listesinde DK öğretmen koltukları GK oylamasına girmemeli (md. 11/1-b).

### 8.2 Eksik akışlar

- **S-10 · Rol boşlukları (K2).** DK "salt okur" ama DK raporunu (md. 14/4) ve görev bölümünü DK hazırlar; kim
  girer? Müdür "salt okur" ama yeni okulda GK'yi müdür çağırır (md. 9/1), GK'yi müdür açar (md. 10/1-b), md. 27
  sorumluluğu müdürdedir; yeter sayı yok tutanağını OYS'de müdür imzalıyor. Kullanıcıya sorulmalı.
- **S-11 · Durum geçişleri yazılmamış.** Bütçeyi "görüşüldü" yapan; sözleşmeyi imzalandı / yürürlükte / fesih /
  sona erdi yapan; taksidi ödendi / iade yapan; kararı "deftere işlendi" yapan; yer teslimini kaydeden; GK yeri
  ve 2. toplantı zamanını yazan; gündemi düzenleyen servis ya da uç yok. OAB Defteri'nde hepsi sıfırdan.
- **S-12 · Yedek çağırma ve görev bölümü.** Düşen üyenin yerine oy sırasıyla yedek (md. 13/6), bir hafta içinde
  görev bölümü (md. 12/3), yedeklerle karar yeter sayısının altına düşülürse bir ay içinde olağanüstü GK
  (md. 13/8) — hiçbiri yok.
- **S-13 · İbra.** GK tutanağında ibra sonucu ve "ibra edilmedi" akışı (divan tutanağı, MEM'e yazı, md. 11/1-ç)
  yok.
- **S-14 · Kantin seti.** Kiralama için ilan, komisyon, karar evrakı yok (OYS 400 döndürüyor); kira sözleşmesi
  servis maddeleriyle basılıyor; aylık kira takvimi, kesin teminat, millî emlak'a sözleşme örneği (md. 21/5),
  yıllık faaliyet belgesi ve çalışan adli sicil yenilemesi (md. 20/7), %25 değişim (md. 21/3), Genelge 2024/35
  yirmi yıl hesabı, kısa süreli kullandırma (md. 19/4), tahliye cezası ve tazminatta %3 (md. 17/1-b-4) yok.
- **S-15 · Mali çekirdek.** K1 ile gereken banka, işlem, eşleme, harcama zinciri, makbuz yaprağı, devreden,
  ilan, aylık bildirim katmanının OYS'de karşılığı yok (§2.4); F3-F4'ün büyük kısmı yeni kod.

### 8.3 Taşıma tuzakları

- **S-16 · Tekil kısıtlar.** Pay beyanı (dönem + mod + yıl + çeyrek) alanı içermiyor → iki kantinli okulda ikinci
  beyan açılamaz. Sözleşme ihale başına tek (feshedilmemiş) → serviste birden çok taşımacıyla sözleşme
  yapılamaz; `Tender.winner` tek istekli. Servis U-E md. 10/3 "taşımacıların" diyor — sahada tek mi çok mu,
  DOĞRULANMADI.
- **S-17 · `is_metropolitan`.** Alan "büyükşehir mi" diye soruyor; Yönetmelik "büyükşehir olmayan il merkezi"
  diyor. Okul kartında yerleşim türü üçlü olmalı (büyükşehir · büyükşehir olmayan il merkezi · diğer).
- **S-18 · Tarih hesapları.** 5 yıl = 5 × 365 gün (artık yılda yanlış uyarı); gecikme zammında ay = ⌈gün/30⌉
  (6183/51 doğrulanmalı); çeyrekler takvim çeyreği (Yönetmelik başlangıcı söylemiyor). İş günü takvimi (5 iş
  günü kuralları) için resmî tatil verisi gerekir.
- **S-19 · Devamsızlık sayımı.** Üyeliğin son üç katılım **kaydına** bakıyor, son üç **toplantıya** değil; kayıt
  girilmeyen toplantı seriyi bozmuyor. Toplu katılım girişi zorunlu olmalı.
- **S-20 · KVKK.** Beyan notu (şifreli serbest metin) ve DK listesindeki "adli sicil kayıtları alınmış mı"
  maddesi çıkar (md. 12/5 beyan ister, kayıt toplamayı değil). Kantin çalışan belgeleri md. 23/4 gereği saklanır
  → dosya şifrelemesi, erişim günlüğü, saklama süresi tasarlanmalı. GK katılım cetveli için öğrenci + veli
  listesi nereden gelecek (e-Okul içe aktarımı mı, boş cetvel mi)?
- **S-21 · Gerçek ad sızıntısı.** OYS'de `_base.py` EK-3 yorumunda ve `test_scoring.py`'de bir test adında ve
  verisinde gerçek bir taşımacı firmanın adı var; OYS kodu ayrıca gerçek evrak analizine (`kesif-evrak-analizi.md`)
  ve gerçek evrak tarih farklarına atıf yapıyor. Taşınırken uydurma adla yeniden yazılır; sızıntı denetimi (F1)
  bu adları da aramalı.
- **S-22 · Yumuşak silme ↔ altın kural 4.** OYS bütün modellerde `deleted_at` ve "canlı kayıt" koşullu tekil
  kısıtları kullanıyor. Mali kayıtlarda ters kayıt, organ ve kişi kayıtlarında yumuşak silme mi kalacak — F0-8.
- **S-23 · Altın kural 3 ↔ OYS sert engelleri.** Sert: istekli suç/hısımlık/belge, taksit > 9, serviste muhammen
  bedel, OLUR olmadan kesinleştirme, puan > azami, ikili kriter, TÜFE yalnız kira, taksit yalnız servis. Proje
  kuralı sert engeli hesap bütünlüğüne bırakıyor; yasal katılım engelleri için istisna gerekip gerekmediği F0-8.
- **S-24 · Evraka uyarı basmak.** OYS ihale belgelerine "MEVZUAT UYARILARI" kutusu basıyor. Resmî dosyaya
  girecek evrakta bu kutunun yeri tartışmalı; gerekçe iç kayıtta tutulup evraka basılmayabilir — kullanıcıya
  sorulmalı.
- **S-25 · Söz dağarcığı.** Servis tarafında model, enum ve şablonlarda "ihale", "teklif toplama", "ihale komisyonu"
  geçiyor (7 şablonda 13 görünür "ihale"). EK-3'ün 4. kriteri mevzuat lafzında "teklif vermesi" diyor; alıntı
  lafzı korunacak mı, proje kuralı alıntıyı da kapsıyor mu — kullanıcıya sorulmalı.
- **S-26 · Paketleme.** `python-magic` Windows'ta libmagic DLL ister (F0-7 bağımlılık kesim listesine).
- **S-27 · Kapsam dışı kalan kaynak.** Ön yüz (`modules/okul-aile-birligi/`) envanterlenmedi; ekran akışları ve
  ön yüz testleri için ayrı bir okuma gerekirse `okulapp` `origin/main`'den yapılmalı.
- **S-28 · Aynı kişi YK ve DK'de.** OYS buna izin veriyor (test "mevzuatta engel yok" diyor). DK YK'yi denetler;
  açık bir yasak bulunamadı (DOĞRULANMADI). Öneri: uyarı + gerekçe.
- **S-29 · Saha kanıtı yok.** Modül 11.07.2026'dan beri pasif; ikinci toplantı, kantin pay dağılımı ve servis
  tespiti hiç gerçek yılla sınanmadı. Ön değerlendirme §7.4'teki "gerçek yılla sınanır" notu bütün kantin ve
  servis akışlarına genişletilmeli (F5-F6 kabul ölçütü).
