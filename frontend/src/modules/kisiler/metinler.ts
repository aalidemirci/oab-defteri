// Kişiler ekranının personel ve aktarım metinleri — tek kaynak (F1b 5. adım; genel tasarım §5.1
// `Personnel.member_kind`, §8.1 A4, §8.4, TK18). Sözlük testi (`docs/sozluk.md`,
// `test_on_yuz_sozlugu.DOSYALAR`) bu sabitleri kaynaktan okur: dizeler düz yazılır (tek satır ya
// da `"…" + "…"`; şablon dizesi yok).
//
// Ekran adı "Görev türü"dür, "üye türü" değil: diğer personel birliğin üyesi değildir (OAB
// Yönetmeliği md. 4/1-e; plan "F1b-5 uygulama kararları"). Değerlerin adları `okul/api`
// `MEMBER_KIND_TR`'dedir (öğretmen · yönetici · diğer personel).

/** Personel listesinin sütunu, ekleme-düzenleme diyaloğunun alanı, Ayrılış Havuzu'nun sütunu. */
export const GOREV_TURU_ETIKETI = "Görev türü";

/** Görev türü alanının yardımı: unvan ve branş sicilde tutulmaz (tasarım §8.4). */
export const GOREV_TURU_YARDIMI = "Unvan ve branş tutulmaz.";

/** Aktarım panelinin açıklaması (e-Okul OOK01001R1, şablon, CSV, pano). */
export const PERSONEL_AKTARIM_ACIKLAMASI =
  "e-Okul Kurum İşlemleri → Raporlar → OOK01001R1 — Personel Listesi raporunu Excel olarak " +
  "indirip DEĞİŞTİRMEDEN yükleyin. Ad-soyad okunur; “Görevi” sütunu yalnız görev türünü " +
  "(öğretmen, yönetici ya da diğer personel) belirlemek için kullanılır ve saklanmaz; unvan ve " +
  "branş okunmaz; sayaç dipnotu atlanır. Alternatif olarak uygulama şablonu doldurulabilir " +
  "(Excel ya da CSV olarak kaydedilebilir) ya da tablo panoya yapıştırılabilir. Makro içeren " +
  "dosya kabul edilmez.";

/** Dosya seçiminin etiketi. */
export const DOSYA_ALANI_ETIKETI = "Dosya (e-Okul .xls, şablon .xlsx ya da .csv)";

// ---------------------------------------------------------------------------
// Aydınlatma metinleri (KVKK md. 10/1; plan "F1b-5 uygulama kararları"). Metinler kullanıcının
// 08.11.2026'da onayladığı biçimdedir ve BİREBİR kullanılır: tek harf değiştirilmez. Köşeli
// ayraçlı iki parça sabit değildir: "Veri sorumlusu:" satırının değeri Okul Bilgileri'ndeki veri
// sorumlusu bilgisiyle dolar (boşken yerine uyarı ve bağlantı çıkar, aktarım engellenmez); ekran
// notu metnin altında not olarak durur. Personel aktarım ekranı personel metnini, veli listesi
// aktarım ekranı veli metnini aktarımdan önce, dosya seçiminin üstünde gösterir
// (`AydinlatmaMetni`).
// ---------------------------------------------------------------------------

/** Personel aktarım ekranının aydınlatma metni (girişi). */
export const PERSONEL_AYDINLATMA_GIRISI =
  "AKTARMADAN ÖNCE: Bu metin kişisel verisi aktarılan personele okulda duyurulur (KVKK md. 10/1).";

export const PERSONEL_AYDINLATMA_AMACI =
  "Amaç: Okul-aile birliğinin işlerinde öğretmen ve yöneticilerin adının kullanılması: " +
  "Denetleme Kuruluna öğretmen üyelerin seçimi (OAB Yönetmeliği md. 14/1), mal ve hizmet alım " +
  "komisyonu (md. 18/1) ve birlik evrakının imza blokları. Yalnız ad-soyad ve görev türü " +
  "(öğretmen, yönetici, diğer personel) tutulur.";

export const PERSONEL_AYDINLATMA_TOPLAMA =
  "Toplama yöntemi ve hukuki sebep: e-Okul personel listesinden okul idaresince elektronik " +
  "ortamda aktarılır. Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi " +
  "(KVKK md. 5/2-ç).";

export const PERSONEL_AYDINLATMA_SAKLAMA =
  "Saklama: Okuldan ayrılan ve birlik kaydına bağı olmayan personelin kaydı, ayrılışı izleyen " +
  "dönem kapanışında silinir.";

/** Veli listesi aktarım ekranının aydınlatma metni (girişi). */
export const VELI_AYDINLATMA_GIRISI =
  "AKTARMADAN ÖNCE: Bu metin velilere duyurulur; genel kurul davetinde kısa paragrafı ve tam " +
  "metnin okunacağı yer (okul panosu, okul sitesi) yer alır (KVKK md. 10/1).";

export const VELI_AYDINLATMA_AMACI =
  "Amaç: Genel kurul toplantısının daveti, katılım cetveli ve toplantı yeter sayısının sayımı " +
  "(OAB Yönetmeliği md. 9/2, 9/3, 10/1-a); birlik organlarına aday olan velinin kaydı. Yalnız " +
  "veli adı-soyadı ve öğrencinin sınıfı tutulur; telefon, adres, T.C. kimlik no ve öğrencinin " +
  "adı tutulmaz.";

export const VELI_AYDINLATMA_TOPLAMA =
  "Toplama yöntemi ve hukuki sebep: Okul idaresinin hazırladığı listeden elektronik ortamda " +
  "aktarılır. Hukuki sebep: veri sorumlusunun hukuki yükümlülüğünü yerine getirmesi " +
  "(KVKK md. 5/2-ç).";

export const VELI_AYDINLATMA_SAKLAMA =
  "Saklama: Liste birlik döneminin kapanışında silinir; genel kuruldan sonra daha önce de " +
  "silinebilir.";

/** İki metnin ortak satırları. */
export const AYDINLATMA_VERI_SORUMLUSU_ETIKETI = "Veri sorumlusu:";

export const AYDINLATMA_AKTARIM =
  "Aktarım: Kişisel veriler kimseye aktarılmaz; program okulun bilgisayarında çalışır, dışarıya " +
  "veri göndermez.";

export const AYDINLATMA_HAKLARINIZ =
  "Haklarınız: KVKK md. 11'deki haklarınızı (verinizin işlenip işlenmediğini öğrenme, bilgi " +
  "isteme, düzeltilmesini ya da silinmesini isteme ve ötekiler) veri sorumlusuna başvurarak " +
  "kullanabilirsiniz.";

/** Metnin altındaki ekran notu. */
export const AYDINLATMA_EKRAN_NOTU =
  "Hukuki sebep öneridir; veri sorumlusu ve hukuki sebep okul müdürlüğünce teyit edilir.";

/** Aydınlatma kutusunun başlığı. */
export const AYDINLATMA_BASLIGI = "Kişisel veri aydınlatma metni";

/** Okul Bilgileri'nde veri sorumlusu boşken "Veri sorumlusu:" satırının yerinde. */
export const VERI_SORUMLUSU_GIRILMEDI =
  "Okul Bilgileri'nde veri sorumlusu bilgisi henüz girilmedi. Metni duyurmadan önce girin; " +
  "aktarım bu bilgi olmadan da yapılabilir.";

/** Uyarının bağlantısı (Ayarlar → Okul Bilgileri). */
export const VERI_SORUMLUSU_BAGLANTISI = "Ayarlar → Okul Bilgileri'ni aç";

/** Okul bilgileri okunamazsa "Veri sorumlusu:" satırının yerinde. */
export const VERI_SORUMLUSU_OKUNAMADI = "Okul Bilgileri'ndeki veri sorumlusu bilgisi okunamadı.";

// ---------------------------------------------------------------------------
// Veli listesi (T5; genel tasarım §5.1 `ParentRoster`, §8.4) — ekranda yalnız SAYI
// ---------------------------------------------------------------------------

/** Kişiler'in sekmesi. */
export const VELI_LISTESI_SEKMESI = "Veli Listesi";

export const VELI_LISTESI_ACIKLAMASI =
  "Genel kurul daveti, katılım cetveli ve yeter sayının sayımı için velilerin listesi. Bir satır " +
  "bir öğrencidir; iki çocuklu veli iki satırdır. Ekranda adlar listelenmez, yalnız sınıf başına " +
  "satır sayısı görünür.";

export const VELI_LISTESI_BOS = "Veli listesinde satır yok.";

export const VELI_LISTESI_OKUNAMADI = "Veli listesi okunamadı.";

/** Aktarım panelinin başlığı ve açıklaması. */
export const VELI_AKTARIM_BASLIGI = "Okulun Şablonundan Veli Listesi Aktar";

export const VELI_AKTARIM_ACIKLAMASI =
  "Veli listesi şablonunu indirip her öğrenci için bir satır doldurun: velinin adı-soyadı ve " +
  "öğrencinin sınıfı (9-A, 10/B, Hazırlık-A, Anasınıfı-A ya da 5 Yaş-A). Başka sütun okunmaz. " +
  "Dosyadaki sınıflar listedeki aynı sınıfların yerini alır; dosyada olmayan sınıflara " +
  "dokunulmaz. Şablon Excel ya da CSV olarak kaydedilebilir; makro içeren dosya kabul edilmez.";

export const VELI_DOSYA_ALANI_ETIKETI = "Dosya (şablon .xlsx, .xls ya da .csv)";

/** "Veli listesini sil" onayı. */
export const VELI_LISTESINI_SIL = "Veli listesini sil";

export const VELI_SILME_ONAY_BASLIGI = "Veli listesi silinsin mi?";

export const VELI_SILME_ONAY_METNI =
  "Listedeki bütün satırlar kalıcı olarak silinir, geri alınamaz. Denetim izine yalnız silinen " +
  "satır sayısı yazılır; adlar yazılmaz. Gerekirse liste şablondan yeniden aktarılır.";

/** Personelin sicilden silinme onayı; gövdenin başına kişinin adı gelir (`kisiOznesi`). */
export const KISI_SILME_ONAY_BASLIGI = "Kişi sicilden silinsin mi?";

export const KISI_SILME_ONAY_METNI =
  "kalıcı olarak silinir, geri alınamaz. Denetim izine yalnız bir kaydın silindiği yazılır; " +
  "kişinin adı yazılmaz. Yanlış girilmiş kayıtlar içindir; okuldan ayrılan kişi için " +
  "“Ayrıldı olarak işaretle”yi kullanın.";

/** Veli listesi özetinin tablosu (ekran okuyucu başlığı ve sütunlar). */
export const VELI_OZET_TABLO_BASLIGI = "Veli listesinin sınıf başına satır sayısı";

export const VELI_SINIF_SUTUNU = "Sınıf";

export const VELI_SATIR_SUTUNU = "Satır (öğrenci)";

/** Özet satırı: "N satır · M sınıf · son aktarım gg.aa.yyyy SS:dd" (sayılar biçimlenmiş gelir). */
export function veliOzetSatiri(satir: string, sinif: string, sonAktarim: string | null): string {
  const bas = `${satir} satır · ${sinif} sınıf`;
  return sonAktarim === null ? bas : `${bas} · son aktarım ${sonAktarim}`;
}

/** "Veli listesini sil"in sonucu: "Veli listesi silindi (N satır)." */
export function veliSilindi(satir: string): string {
  return `Veli listesi silindi (${satir} satır).`;
}

export const VELI_SILINEMEDI = "Veli listesi silinemedi.";

// Veli listesi aktarım paneli: düğmeler, iletiler, rapor (yalnız sayı; ad ve hücre değeri yok).

export const SABLON_INDIR = "Şablon indir";

export const SABLON_INDIRILEMEDI = "Şablon indirilemedi.";

export const DOSYAYI_KALDIR = "Dosyayı kaldır";

export const ONIZLE = "Önizle";

export const AKTAR = "Aktar";

export const CALISIYOR = "Çalışıyor…";

export const VELI_DOSYA_SECIN = "Önce bir dosya seçin.";

export const ONIZLEME_YAPILAMADI = "Önizleme yapılamadı.";

export const VELI_AKTARILDI = "Veli listesi aktarıldı.";

export const VELI_AKTARILAMADI = "Veli listesi aktarılamadı.";

export const ONIZLEME_BASLIGI = "Önizleme — hiçbir kayıt yazılmadı";

export const VELI_AKTARIM_SONUCU = "Aktarım sonucu";

/** Aynı içerik daha önce aktarıldıysa (personel ve veli raporu). */
export const DAHA_ONCE_AKTARILMIS =
  "Bu içerik daha önce aktarılmış. Güncelleme amaçlı yeniden aktarma engellenmez.";

/** Rapor kutularının etiketleri. */
export const RAPOR_DOSYADAKI_SATIR = "Dosyadaki satır";

export const RAPOR_AKTARILACAK = "Aktarılacak";

export const RAPOR_AKTARILAN = "Aktarılan";

export const RAPOR_AKTARILAMAYAN = "Aktarılamayan";

export const RAPOR_SINIF = "Sınıf";

export const RAPOR_SILINECEK_ESKI_SATIR = "Silinecek eski satır";

export const RAPOR_SILINEN_ESKI_SATIR = "Silinen eski satır";

export const RAPOR_DOKUNULMAYAN_SINIF = "Dokunulmayan sınıf";

export const VELI_YERINE_KOYMA_ONIZLEME =
  "Dosyadaki sınıfların listedeki eski satırları silinir, yerine dosyadakiler yazılır; dosyada " +
  "olmayan sınıflara dokunulmaz.";

export const VELI_YERINE_KOYMA_SONUC =
  "Dosyadaki sınıfların eski satırları silindi, yerine dosyadakiler yazıldı; dosyada olmayan " +
  "sınıflara dokunulmadı.";

/** Raporun sınıf tablosu (ekran okuyucu başlığı). */
export const DOSYADAKI_SINIFLAR = "Dosyadaki sınıflar";

/** "Aktarılamayan satırlar (N)": N satır sayısıdır (bir satırın birden çok sorunu olabilir). */
export function aktarilamayanSatirlar(satir: string): string {
  return `Aktarılamayan satırlar (${satir})`;
}

export const AKTARILAMAYAN_SATIR_YOK = "Aktarılamayan satır yok.";

/** Başlık satırının uyarıları (ör. aynı alana uyan ikinci sütun); satır sayısına girmez. */
export function baslikUyarilari(sayi: string): string {
  return `Başlık uyarıları (${sayi})`;
}

/** Sorun tablolarının sütunları. */
export const SORUN_SATIR_SUTUNU = "Satır";

export const SORUN_ALAN_SUTUNU = "Alan";

export const SORUN_SORUN_SUTUNU = "Sorun";

/** Veli raporundaki alan kodlarının adları (sunucunun `excel_veli.ALAN_ADLARI`'yla aynı). */
export const VELI_ALAN_BASLIK = "Başlık";

export const VELI_ALAN_AD = "Velinin adı-soyadı";

export const VELI_ALAN_SINIF = "Öğrencinin sınıfı";

// ---------------------------------------------------------------------------
// Kaynak dosya hatırlatması (genel tasarım §4.3 tehdit modeli 15. satır: içe aktarılan liste
// diskte kalır; program kendi açık kopyasını bırakmaz, kalanını koruyamaz — "kaynak dosyayı
// silin" hatırlatması). Personel ve veli listesi aktarımı dosyayla başarıyla bitince görünür.
// ---------------------------------------------------------------------------

export const KAYNAK_DOSYA_HATIRLATMASI =
  "Aktarılan dosya bilgisayarda şifresiz durur: artık gerekmiyorsa silin, Geri Dönüşüm " +
  "Kutusu'ndan (Pardus'ta Çöp'ten) de kaldırın.";
