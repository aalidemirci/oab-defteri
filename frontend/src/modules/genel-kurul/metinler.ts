// Genel Kurul ekranının metinleri — tek kaynak (sözlük §1 "Genel Kurul ekranı (F2)", §4.1; plan F2 §6.1).
// Terimler Yönetmeliğinkidir (altın kural 6): "genel kurul", "yönetim kurulu", "Denetleme Kurulu",
// "divan", "ibra", "tahmini bütçe"; "YK", "DK" kullanıcı metninde geçmez. Program karar defterinin ve
// TEFBİS'in yerine geçmez (CLAUDE.md §1). Uyarıların kendi metni ve madde atfı SUNUCUNUNDUR: ekran onları
// olduğu gibi yazar. Evrak kodları (E05…) yüzeye çıkmaz (sözlük §2); belge adları katalogdan gelir.

import type {
  Cagiran,
  GenelKurulDurumu,
  GenelKurulTuru,
  GundemSonucu,
  GundemTuru,
  IbraSonucu,
  KatilimTuru,
  Toplanti,
} from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const GENEL_KURUL_BASLIGI = "Genel Kurul";
export const GENEL_KURUL_ACIKLAMASI =
  "Okul-aile birliğinin olağan ve olağanüstü genel kurulları: planlama, çağrı, ilan ve davet, " +
  "toplantı, tutanak ve genel kuruldan sonraki işler. Kayıt silinmez; yanlış kayıt gerekçeyle " +
  "düzeltilir. Program karar defterinin ve TEFBİS'in yerine geçmez.";

/** Liste ve boş durum. */
export const LISTE_BASLIGI = "Genel Kurullar";
export const GENEL_KURUL_YOK = "Genel kurul kaydı yok";
export const GENEL_KURUL_YOK_ACIKLAMASI =
  "Olağan genel kurul her yıl en geç Ekim ayının sonuna kadar toplanır (md. 9/1). Genel kurulu " +
  "planlayarak başlayın.";
export const GENEL_KURULLAR_OKUNAMADI = "Genel kurullar okunamadı.";
export const GENEL_KURUL_OKUNAMADI = "Genel kurulun kaydı okunamadı.";
export const SUTUN_TUR = "Tür";
export const SUTUN_BIRINCI_TOPLANTI = "Birinci toplantı";
export const SUTUN_DURUM = "Durum";
export const DUGME_PLANLA = "Genel kurulu planla";
export const DUGME_LISTEYE_DON = "Genel kurullara dön";

/** Kural sürümü (U1): açık dönemin sürümü genel kurul kurallarını taşımıyor. */
export const KURAL_SURUMU_GUNCELLENMELI =
  "Açık birlik döneminin kural sürümü genel kurulun kurallarını taşımıyor. Genel kurul planlanmadan " +
  "önce birlik döneminin kural sürümü güncellenir.";
export const KURAL_SURUMU_AC = "Birlik Dönemi → Kural Sürümü Güncellemesi'ni aç";
/** Kural sürümünü güncelleyemeyen planlayıcı (sekreter) için: güncelleme yolu öğütlenmez (sözlük §1
 * "Rol süzmesi"). */
export const KURAL_SURUMU_GUNCELLENMELI_BASVURUN =
  "Açık birlik döneminin kural sürümü genel kurulun kurallarını taşımıyor. Genel kurul, kural sürümü " +
  "güncellendikten sonra planlanır; güncelleme için program yöneticisine başvurun.";

/** Sihirbazın adımları (Stepper). */
export const ADIM_PLANLA = "Planla";
export const ADIM_CAGRI = "Çağrı";
export const ADIM_ILAN = "İlan ve davet";
export const ADIM_TOPLANTI = "Toplantı";
export const ADIM_TUTANAK = "Tutanak";
export const ADIM_SONRASI = "Sonrası";
export const SIHIRBAZ_ADIMLARI = "Genel kurulun adımları";

/** Kaydın özeti. */
export const ALAN_TUR = "Tür";
export const ALAN_DURUM = "Durum";
export const ALAN_BIRINCI_TOPLANTI = "Birinci toplantının günü ve saati";
export const ALAN_IKINCI_TOPLANTI = "İkinci toplantının günü ve saati";
export const ALAN_YER = "Toplantı yeri";
export const ALAN_CAGIRAN = "Çağıran";
export const ALAN_CAGRI_NEDENI = "Çağrı nedeni";
export const ALAN_YETER_SAYI = "Toplantı yeter sayısı";
export const ALAN_OGRENCI_MEVCUDU = "İlandaki öğrenci mevcudu";
export const ALAN_ILAN_GUNU = "İlan günü";
export const ALAN_YAPILDIGI_TOPLANTI = "Yapıldığı toplantı";
export const ALAN_IPTAL_NEDENI = "İptal gerekçesi";
export const BOS_DEGER = "—";
export const BILGILER_BASLIGI = "Bilgi";
export const KURAL_UYARILARI_BASLIGI = "Genel kurulun açık uyarıları";
export const GECIS_UYARILARI_BASLIGI = "Bu kaydın uyarıları";
export const IPTAL_EDILDI_NOTU = "Bu genel kurul iptal edildi; kayıtları salt okunurdur.";
export const TUTANAK_TAMAM_NOTU = "Tutanak tamamlandı; genel kurulun kayıtları salt okunurdur.";

/** Planla. */
export const PLANLA_BASLIGI = "Genel kurulu planla";
export const PLANLA_ACIKLAMASI =
  "Olağan genel kurul planlanınca yeni birlik dönemi hazırlık durumunda açılır ve gündem, " +
  "Yönetmeliğin saydığı maddelerle hazırlanır. Olağanüstü genel kurulun gündemi çağrıda girilir.";
export const ALAN_GENEL_KURUL_TURU = "Genel kurulun türü";
export const DUGME_PLANLA_KAYDET = "Planla";
export const PLANLANDI = "Genel kurul planlandı.";
export const PLANLANAMADI = "Genel kurul planlanamadı.";
export const BIRINCI_TOPLANTI_GEREKLI = "Birinci toplantının günü ve saatini girin.";
export const PLANLAMA_BILGILERI_BASLIGI = "Planlamadan önce";
export const DUGME_TOPLANTI_BILGISI = "Toplantı bilgisini değiştir";
export const TOPLANTI_BILGISI_BASLIGI = "Toplantı bilgisini değiştir";
export const TOPLANTI_BILGISI_ACIKLAMASI =
  "Toplantının günü, saati ve yeri ilandan önce değiştirilir; ilandan sonra değişmez.";
export const TOPLANTI_BILGISI_KAYDEDILDI = "Toplantı bilgisi kaydedildi.";
export const TOPLANTI_BILGISI_KAYDEDILEMEDI = "Toplantı bilgisi kaydedilemedi.";

/** Gündem. */
export const GUNDEM_BASLIGI = "Gündem";
export const GUNDEM_BOS = "Gündemde madde yok.";
export const GUNDEMDEN_CIKARILDI = "gündemden çıkarıldı";
export const OYLAMAYLA_EKLENDI = "oylamayla eklendi";
export const DUGME_GUNDEM_SIRASI = "Gündemin sırasını değiştir";
export const GUNDEM_SIRASI_BASLIGI = "Gündemin sırasını değiştir";
export const GUNDEM_SIRASI_ACIKLAMASI =
  "Gündemin sırası ilandan önce ya da toplantıda değişir; genel kurul maddeleri sırasıyla görüşür.";
export const DUGME_YUKARI = "Yukarı taşı";
export const DUGME_ASAGI = "Aşağı taşı";
export const GUNDEM_SIRASI_KAYDEDILDI = "Gündemin sırası kaydedildi.";
export const GUNDEM_SIRASI_KAYDEDILEMEDI = "Gündemin sırası kaydedilemedi.";

/** Çağrı. */
export const CAGRI_BASLIGI = "Çağrı";
export const DUGME_CAGRI = "Çağrıyı kaydet";
export const CAGRI_PENCERESI_BASLIGI = "Genel kurulun çağrısı";
export const CAGRI_OLAGAN_ACIKLAMASI =
  "Olağan genel kurulu yönetim kurulu çağırır; yeni açılan okulda okul müdürü davet eder (md. 9/1).";
export const CAGRI_OLAGANUSTU_ACIKLAMASI =
  "Olağanüstü genel kurulun çağrı nedeni ve gündemi yazılır; genel kurul yalnız bu gündemi görüşür " +
  "(md. 9/6).";
export const CAGRI_SECENEGI_YOK =
  "Bu genel kurulun çağrısı hesabınızın rolüyle yazılmaz; çağrıyı yazacak hesap kaydeder.";
export const ALAN_CAGRI_GUNDEMI = "Gündem maddeleri";
export const ALAN_GUNDEM_MADDESI = "Gündem maddesi";
export const DUGME_MADDE_EKLE = "Madde ekle";
export const DUGME_MADDEYI_KALDIR = "Maddeyi kaldır";
export const ALAN_BASVURAN_SAYISI = "Başvuran üye sayısı";
export const ALAN_UYE_SAYISI = "Birlik üye sayısı";
export const UYE_SAYISI_YARDIMI =
  "Üye sayısı elle girilir; başvuru yazısıyla birlikte saklanır (md. 9/6, üyelerin %10'u).";
export const ALAN_BASVURU_YAZISI = "Başvuru yazısının gelen evrak kaydı";
export const BASVURU_YAZISI_YOK = "Gelen evrak kaydı yok; başvuru yazısı sonra bağlanabilir.";
export const CAGRI_KAYDEDILDI = "Çağrı kaydedildi.";
export const CAGRI_KAYDEDILEMEDI = "Çağrı kaydedilemedi.";
export const CAGRI_NEDENI_GEREKLI = "Çağrı nedenini yazın.";
export const GUNDEM_GEREKLI = "En az bir gündem maddesi girin.";
export const DUGME_CAGRI_YAZISI = "Çağrı yazısını bağla";
export const CAGRI_YAZISI_BASLIGI = "Çağrı yazısının evrak kaydı";
export const CAGRI_YAZISI_ACIKLAMASI =
  "Üyelerin başvurusu ya da Denetleme Kurulunun yazısı gelen-giden evrak defterine kaydedildiyse " +
  "kaydı genel kurula bağlayın.";
export const CAGRI_YAZISI_BAGLANDI = "Çağrı yazısı bağlandı.";
export const CAGRI_YAZISI_BAGLANAMADI = "Çağrı yazısı bağlanamadı.";
export const CAGRI_YAZISI_BAGLI = "Çağrı yazısı bağlı.";
export const CAGRI_YAZISI_BAGSIZ = "Çağrı yazısının evrak kaydı bağlanmadı.";

/** Denetleme Kurulunun çağrısı (md. 14/5; ⁵). */
export const DK_CAGRI_BASLIGI = "Olağanüstü genel kurul çağrısı";
export const DK_CAGRI_ACIKLAMASI =
  "Denetleme Kurulu, denetiminde Yönetmeliğin 6. maddesine aykırılık bulursa genel kurulu " +
  "olağanüstü toplantıya çağırır (md. 14/5). Çağrı denetim raporuna bağlanır; rapor çağrıyla " +
  "aynı anda kaydedilir.";
export const DK_CAGRI_BOLUM_BASLIGI = "Olağanüstü Genel Kurul Çağrısı";
export const DK_CAGRI_GENEL_KURUL_YOK =
  "Planlanmış olağanüstü genel kurul yok. Toplantının günü ve yeri program yöneticisince ya da " +
  "sekreterce planlanır; çağrı sonra buradan yazılır.";
export const ALAN_RAPOR_TURU = "Denetim raporunun türü";
export const RAPOR_ARA = "Ara rapor";
export const RAPOR_NIHAI = "Nihai rapor";
export const ALAN_RAPOR_GUNU = "Raporun günü";
export const ALAN_MD6_AYKIRILIK =
  "Denetimde Yönetmeliğin 6. maddesine aykırılık bulundu (md. 14/5)";
export const ALAN_USULSUZLUK = "Denetimde usulsüzlük bulundu";
export const USULSUZLUK_YARDIMI =
  "Usulsüzlük tek başına olağanüstü genel kurul çağrısının dayanağı değildir (md. 14/5). Denetleme " +
  "Kurulu ara raporunu bilgi ve gereği için yönetim kuruluna, nihai raporunu genel kurula sunar " +
  "(md. 14/4).";
export const MD6_ISARETI_ZORUNLU =
  "Çağrı yalnız Yönetmeliğin 6. maddesine aykırılık bulunduğunda yazılır (md. 14/5).";
export const RAPOR_GUNU_GEREKLI = "Raporun gününü girin.";
export const DK_RAPORU_EKI_BASLIGI = "Denetleme Kurulu Raporunun Eki";
export const DK_RAPORU_EKI_ACIKLAMASI =
  "Denetleme Kurulunun nihai raporu genel kurulun gündemindeki rapor maddesine dosya olarak " +
  "eklenir (md. 14/4). Rapor programda üretilmez.";
export const DK_RAPORU_MADDESI_YOK =
  "Gündeminde Denetleme Kurulu raporu maddesi olan, tutanağı tamamlanmamış genel kurul yok.";

/** İlan ve davet. */
export const ILAN_BASLIGI = "İlan ve davet";
export const DUGME_ILAN = "İlanı kaydet";
export const ILAN_PENCERESI_BASLIGI = "Genel kurulun ilanı";
export const ILAN_ACIKLAMASI =
  "Toplantının yeri, zamanı ve gündemi üyelere en az on beş gün önce elden yazılı olarak " +
  "bildirilir, okulun ilan panosunda ve internet sayfasında duyurulur (md. 9/3). İlanla toplantı " +
  "yeter sayısı o günkü öğrenci mevcudundan hesaplanır ve değişmez.";
export const ALAN_ELDEN_YAZILI = "Elden yazılı bildirimin günü";
export const ALAN_ILAN_PANOSU = "İlan panosuna asıldığı gün";
export const ALAN_INTERNET = "İnternet sayfasında yayımlandığı gün";
export const KANAL_YARDIMI = "Henüz yapılmadıysa boş bırakın; sonra girilir.";
export const IKINCI_TOPLANTI_YARDIMI =
  "Birinci toplantıda yeter sayı sağlanamazsa ikinci toplantı en geç otuz gün içinde yapılır " +
  "(md. 9/2). Davette önerilir; boş bırakılabilir.";
export const ILAN_KAYDEDILDI = "İlan kaydedildi.";
export const ILAN_KAYDEDILEMEDI = "İlan kaydedilemedi.";
export const ILANLAR_BASLIGI = "İlanlar";
export const ILAN_YOK = "İlan kaydı yok.";
export const DUGME_KANIT = "Kanıt günlerini gir";
export const KANIT_PENCERESI_BASLIGI = "İlanın kanıt günleri";
export const KANIT_KAYDEDILDI = "Kanıt günleri kaydedildi.";
export const KANIT_KAYDEDILEMEDI = "Kanıt günleri kaydedilemedi.";
export const DUGME_IKINCI_ILAN = "İkinci toplantıyı ilan et";
export const IKINCI_ILAN_BASLIGI = "İkinci toplantının ilanı";
export const IKINCI_ILAN_ACIKLAMASI =
  "Birinci toplantıda yeter sayı sağlanamadı. İkinci toplantı en geç otuz gün içinde yapılır; " +
  "ikinci toplantıda çoğunluk aranmaz (md. 9/2).";
export const IKINCI_TOPLANTI_GEREKLI = "İkinci toplantının günü ve saatini girin.";
export const KANIT_EKLERI = "Kanıt dosyaları";
export const KANIT_EKI_YARDIMI =
  "İlan panosunun fotoğrafı, internet sayfasının görüntüsü ya da teslim kaydı (PDF, JPEG, PNG). " +
  "Veli adı taşıyan çizelge eklenmez.";

/** Toplantı. */
export const TOPLANTI_BASLIGI = "Toplantı";
export const DUGME_BIRINCI_TOPLANTI = "Birinci toplantıyı kaydet";
export const DUGME_IKINCI_TOPLANTI = "İkinci toplantıyı kaydet";
export const BIRINCI_TOPLANTI_BASLIGI = "Birinci toplantının sayıları";
export const IKINCI_TOPLANTI_BASLIGI = "İkinci toplantının sayıları";
export const TOPLANTI_ACIKLAMASI =
  "Katılan üye sayısı imzalayan üyelerdir. Yeter sayının sağlanıp sağlanmadığını program " +
  "hesaplar; gözlemci öğrenci katılan sayısına girmez (md. 9/5).";
export const ALAN_KATILAN = "Katılan üye sayısı";
export const ALAN_VELISI_KATILAN = "Velisi katılan öğrenci sayısı";
export const ALAN_GOZLEMCI = "Gözlemci öğrenci sayısı";
export const DAGILIM_BASLIGI = "Katılanların türe göre dağılımı";
export const DAGILIM_YARDIMI = "Girilen sayıların toplamı katılan üye sayısını tutmalıdır.";
export const KATILAN_GEREKLI = "Katılan üye sayısını girin.";
export const TOPLANTI_KAYDEDILDI = "Toplantının sayıları kaydedildi.";
export const TOPLANTI_KAYDEDILEMEDI = "Toplantının sayıları kaydedilemedi.";
export const YETER_SAYI_YOK_NOTU =
  "Birinci toplantıda yeter sayı sağlanamadı; ikinci toplantı yapılır (md. 9/2).";
export const DUGME_KATILIM_DUZELTMESI = "Katılımı düzelt";
export const KATILIM_DUZELTMESI_BASLIGI = "Katılım düzeltmesi";
export const KATILIM_DUZELTMESI_ACIKLAMASI =
  "Yanlış girilmiş sayı düzeltilir; önceki değer silinmez, düzeltme gerekçesiyle kayda geçer. " +
  "İlanda hesaplanan yeter sayı düzeltilemez.";
export const ALAN_TOPLANTI = "Toplantı";
export const ALAN_DUZELTILEN_SAYI = "Düzeltilen sayı";
export const ALAN_YENI_DEGER = "Doğru değer";
export const ALAN_DUZELTME_GEREKCESI = "Düzeltmenin gerekçesi";
export const DUZELTME_GEREKCESI_YAZIN = "Düzeltmenin gerekçesini yazın.";
export const YENI_DEGER_GEREKLI = "Doğru değeri girin.";
export const DUZELTME_KAYDEDILDI = "Katılım düzeltmesi kaydedildi.";
export const DUZELTME_KAYDEDILEMEDI = "Katılım düzeltmesi kaydedilemedi.";
export const DUZELTMELER_BASLIGI = "Katılım düzeltmeleri";

/** Katılım işaretleri (U33; yalnız program yöneticisi, erişim günlüğü). */
export const DUGME_KATILIM_ISARETLERI = "Katılım işaretleri";
export const KATILIM_ISARETLERI_BASLIGI = "Katılım işaretleri";
export const KATILIM_ISARETLERI_ACIKLAMASI =
  "Sayımı kolaylaştırmak için veli satırlarına katılım işareti konur. Pencerede veli adları " +
  "görünür; açılması erişim günlüğüne yazılır. İşaretlerin sayısı katılan sayısına öneridir; " +
  "toplantının sayısı elle girilir.";
export const ISARETLER_OKUNAMADI = "Katılım işaretleri okunamadı.";
export const ISARET_LISTESI_BOS = "Veli listesinde satır yok.";
export const ISARET_OTEKI_TOPLANTI = "öteki toplantıda işaretli";
export const ISARET_BASKA_GENEL_KURUL = "başka genel kurulda işaretli";
export const ADI_OKUNAMADI = "Adı okunamayan satır";
export const ISARETLER_KAYDEDILDI = "Katılım işaretleri kaydedildi.";
export const ISARETLER_KAYDEDILEMEDI = "Katılım işaretleri kaydedilemedi.";
export const DUGME_ISARETLERI_KAYDET = "İşaretleri kaydet";

/** Tutanak: divan, gündem sonuçları, ibra, aday ve seçim. */
export const TUTANAK_BASLIGI = "Tutanak";
export const DIVAN_BASLIGI = "Divan";
export const DIVAN_YOK = "Divan seçilmedi.";
export const DUGME_DIVAN = "Divanı kaydet";
export const DIVAN_PENCERESI_BASLIGI = "Divan";
export const DIVAN_ACIKLAMASI =
  "Genel kurul toplantıyı yönetmek için bir başkan ve bir kâtipten oluşan divan seçer " +
  "(md. 10/1-c). Divan başkanı ve kâtip ayrı kişilerdir.";
export const ALAN_DIVAN_BASKANI = "Divan başkanı";
export const ALAN_KATIP = "Kâtip";
export const KISI_SECIN = "Kişiyi seçin.";
export const DIVAN_KAYDEDILDI = "Divan kaydedildi.";
export const DIVAN_KAYDEDILEMEDI = "Divan kaydedilemedi.";
export const DUGME_DIVAN_IPTAL = "Divanı düzelt";
export const DIVAN_IPTAL_BASLIGI = "Divanın kaydı iptal edilsin mi?";
export const DIVAN_IPTAL_METNI =
  "Yanlış girilen divan iptal edilir: kayıt silinmez, iptal gerekçesiyle kalır. Sonra doğru divan " +
  "kaydedilir.";
export const DIVAN_IPTAL_EDILDI = "Divanın kaydı iptal edildi.";
export const DIVAN_IPTAL_EDILEMEDI = "Divanın kaydı iptal edilemedi.";
export const GUNDEM_SONUCLARI_BASLIGI = "Gündem sonuçları";
export const DUGME_SONUC = "Sonucu gir";
export const SONUC_PENCERESI_BASLIGI = "Gündem maddesinin sonucu";
export const SONUC_ACIKLAMASI =
  "Oylanan maddede sonucu program oylardan hesaplar: kabul oyu katılanların yarısından fazla " +
  "olmalıdır. Oylanmayan madde görüşüldü olarak kaydedilir.";
export const ALAN_SONUC_TURU = "Sonucun türü";
export const SONUC_OYLANDI = "Oylandı";
export const ALAN_KABUL = "Kabul oyu";
export const ALAN_RET = "Ret oyu";
export const ALAN_SALONDAKI = "Oylamada salonda bulunan";
export const SALONDAKI_YARDIMI = "Boş bırakılırsa toplantının katılan sayısı esas alınır.";
export const ALAN_SONUC_METNI = "Sonucun metni";
export const SONUC_KAYDEDILDI = "Sonuç kaydedildi.";
export const SONUC_KAYDEDILEMEDI = "Sonuç kaydedilemedi.";
export const DUGME_GUNDEM_EKLE = "Gündeme madde ekle";
export const GUNDEM_EKLE_BASLIGI = "Gündeme madde ekle";
export const GUNDEM_EKLE_ACIKLAMASI =
  "Toplantıda gündeme madde eklenmesi oylanır (md. 9/4). Olağanüstü genel kurul yalnız çağrıdaki " +
  "gündemi görüşür (md. 9/6).";
export const ALAN_MADDE_BASLIGI = "Maddenin başlığı";
export const ALAN_SIRA = "Gündemdeki sırası";
export const ALAN_DEGISIKLIK_KABUL = "Değişikliğe kabul oyu";
export const ALAN_DEGISIKLIK_RET = "Değişikliğe ret oyu";
export const MADDE_BASLIGI_GEREKLI = "Maddenin başlığını yazın.";
export const GUNDEM_EKLENDI = "Madde gündeme eklendi.";
export const GUNDEM_EKLENEMEDI = "Madde gündeme eklenemedi.";
export const DUGME_GUNDEMDEN_CIKAR = "Gündemden çıkar";
export const GUNDEMDEN_CIKAR_BASLIGI = "Gündemden çıkarma";
export const GUNDEMDEN_CIKAR_ACIKLAMASI =
  "Gündemden madde çıkarılması oylanır (md. 9/4); madde silinmez, çıkarıldığı yazılır.";
export const GUNDEMDEN_CIKARILDI_BILDIRIMI = "Madde gündemden çıkarıldı.";
export const GUNDEMDEN_CIKARILAMADI = "Madde gündemden çıkarılamadı.";
export const IBRA_BASLIGI = "İbra";
export const DUGME_IBRA = "İbrayı gir";
export const IBRA_PENCERESI_BASLIGI = "İbra";
export const IBRA_ACIKLAMASI =
  "Yönetim kurulunun ve Denetleme Kurulunun hesapları ayrı ayrı oylanır (md. 11/1-c). Sonucu " +
  "program oylardan hesaplar. Görüşülmeyen kurulun satırı boş bırakılır.";
export const IBRA_YK = "Yönetim kurulu";
export const IBRA_DK = "Denetleme Kurulu";
export const ALAN_IBRA_EDILMEYEN_EVRAK = "İbra edilmeyen muhasebe evrakı";
export const IBRA_EDILMEYEN_EVRAK_YARDIMI =
  "Yönetim kurulu ibra edilmezse ibra edilmeyen muhasebe evrakı tutanağa yazılır (md. 11/1-ç).";
export const IBRA_KAYDEDILDI = "İbra kaydedildi.";
export const IBRA_KAYDEDILEMEDI = "İbra kaydedilemedi.";
export const OYLAR_BIRLIKTE = "Kabul ve ret oylarını birlikte girin.";
export const ADAYLAR_BASLIGI = "Adaylar ve seçim";
export const ADAY_YOK = "Aday kaydı yok.";
export const DUGME_ADAY = "Aday ekle";
export const ADAY_PENCERESI_BASLIGI = "Aday";
export const ADAY_ACIKLAMASI =
  "Genel kurul yönetim kurulunun asıl ve yedek üyelerini ve Denetleme Kurulunun veli üyesini seçer " +
  "(md. 11/1-a, b). Aday toplantıda da kaydedilebilir.";
export const ALAN_KURUL = "Kurul";
export const ALAN_KOLTUK = "Koltuk";
export const KOLTUK_ASIL = "Asıl";
export const KOLTUK_YEDEK = "Yedek";
export const ADAY_KAYDEDILDI = "Aday kaydedildi.";
export const ADAY_KAYDEDILEMEDI = "Aday kaydedilemedi.";
export const DUGME_SECIM = "Seçim sonucunu gir";
export const SECIM_PENCERESI_BASLIGI = "Seçimin sonucu";
export const SECIM_ACIKLAMASI =
  "Adayların oyları ve seçilenler girilir. Yedek üyelerin sırası oydan hesaplanır; eşit oyda sıra " +
  "elle girilir.";
export const ALAN_OY = "Oy";
export const ALAN_SECILDI = "Seçildi";
export const ALAN_YEDEK_SIRASI = "Yedek sırası";
export const ALAN_LISTE = "Liste hâlinde seçildi";
export const ALAN_ACIK_OY = "Açık oyla seçildi";
export const SECIM_ADAYI_YOK = "Bu kurulun aday kaydı yok; önce aday ekleyin.";
export const SECIM_KAYDEDILDI = "Seçimin sonucu kaydedildi.";
export const SECIM_KAYDEDILEMEDI = "Seçimin sonucu kaydedilemedi.";
export const DUGME_SECIM_IPTAL = "Seçimi düzelt";
export const SECIM_IPTAL_BASLIGI = "Seçimin sonucu iptal edilsin mi?";
export const SECIM_IPTAL_METNI =
  "Yanlış girilen seçim sonucu iptal edilir: seçilenlerin kaydı silinmez, iptal gerekçesiyle kalır. " +
  "Sonra doğru sonuç girilir.";
export const SECIM_IPTAL_EDILDI = "Seçimin sonucu iptal edildi.";
export const SECIM_IPTAL_EDILEMEDI = "Seçimin sonucu iptal edilemedi.";
export const TUTANAK_BILGILERI_BASLIGI = "Tutanağın bilgileri";
export const DUGME_TUTANAK_BILGILERI = "Tutanağın bilgilerini gir";
export const ALAN_YK_RAPORU_OKUYAN = "Yönetim kurulu raporunu okuyan";
export const ALAN_DK_RAPORU_OKUYAN = "Denetleme Kurulu raporunu okuyan";
export const ALAN_BUTCEYI_SUNAN = "Tahmini bütçeyi sunan";
export const ALAN_TESLIM_GUNU = "Tutanağın yeni yönetim kuruluna teslim günü";
export const TESLIM_GUNU_YARDIMI =
  "Genel kurul tutanağı ve ekleri yeni yönetim kuruluna teslim edilir (md. 10/1-ç).";
export const TUTANAK_BILGILERI_KAYDEDILDI = "Tutanağın bilgileri kaydedildi.";
export const TUTANAK_BILGILERI_KAYDEDILEMEDI = "Tutanağın bilgileri kaydedilemedi.";
export const DUGME_TUTANAK_TAMAMLA = "Tutanağı tamamla";
export const TUTANAK_TAMAMLA_BASLIGI = "Tutanak tamamlansın mı?";
export const TUTANAK_TAMAMLA_METNI =
  "Tutanak tamamlanınca genel kurulun kayıtları değişmez. Açık eksikler gerekçesiyle kayda geçer. " +
  "Olağan genel kurulda yeni birlik dönemi program yöneticisinin onayıyla açılır.";
export const TUTANAK_TAMAMLANDI = "Tutanak tamamlandı.";
export const TUTANAK_TAMAMLANAMADI = "Tutanak tamamlanamadı.";

/** Sonrası: dönem geçişi (U32), görev bölümü, TEFBİS. */
export const SONRASI_BASLIGI = "Sonrası";
export const DONEM_GECISI_BASLIGI = "Yeni Birlik Döneminin Açılışı";
export const DONEM_GECISI_ACIKLAMASI =
  "Tutanak tamamlanınca yeni birlik dönemi kendiliğinden açılmaz; program yöneticisi onaylar. Yeni " +
  "birlik dönemi genel kurulun yapıldığı gün başlar, önceki birlik dönemi kapanışa geçer.";
export const DONEM_GECISI_OKUNAMADI = "Birlik döneminin geçişi okunamadı.";
export const ALAN_YENI_DONEM = "Yeni birlik dönemi";
export const ALAN_DONEM_BASLANGICI = "Başlangıç";
export const ALAN_KAPANACAK_DONEM = "Kapanışa geçecek birlik dönemi";
export const ALAN_KAPANACAK_BITIS = "Bitiş";
export const DONEM_GECISI_ENGELLERI = "Onaydan önce";
export const DUGME_DONEM_GECISI = "Yeni birlik dönemini aç";
export const DONEM_GECISI_ONAY_BASLIGI = "Yeni birlik dönemi açılsın mı?";
export const DONEM_GECISI_ONAY_METNI =
  "Yeni birlik dönemi açılır, önceki birlik dönemi kapanışa geçer. Bu işlem geri alınmaz.";
export const DONEM_GECISI_ONAYLANDI = "Yeni birlik dönemi açıldı.";
export const DONEM_GECISI_ONAYLANAMADI = "Yeni birlik dönemi açılamadı.";
export const DONEM_ACIK_NOTU = "Yeni birlik dönemi açıldı.";
export const OLAGANUSTU_DONEM_ACMAZ =
  "Olağanüstü genel kurul birlik dönemi açmaz; seçilen kurul görevdeki birlik döneminde görev yapar.";
export const GOREV_BOLUMU_BASLIGI = "Görev Bölümü";
export const GOREV_BOLUMU_ACIKLAMASI =
  "Yönetim kurulu ve Denetleme Kurulunun asıl üyeleri genel kuruldan sonraki ilk hafta içinde " +
  "toplanır ve görev bölümü yapar (md. 12/3, 14/1).";
export const YK_GOREV_BOLUMU_AC = "Organlar → Yönetim Kurulu'nu aç";
export const DK_GOREV_BOLUMU_AC = "Organlar → Denetleme Kurulu'nu aç";
export const TEFBIS_BASLIGI = "TEFBİS";
export const TEFBIS_ACIKLAMASI =
  "Olağan genel kuruldan sonra yeni birlik döneminin yönetim, banka ve bütçe bilgilerinin " +
  "TEFBİS'e girişi takvim satırı olarak kayda geçer; girişi okul idaresi yapar (md. 23/5).";

/** Dosya ekleri (U23). */
export const DOSYA_EKLERI_BASLIGI = "Dosya Ekleri";
export const DOSYA_EKLERI_ACIKLAMASI =
  "Yönetim kurulunun faaliyet raporu ve kesin hesabı, tahmini bütçe ve Denetleme Kurulunun raporu " +
  "gündemdeki maddelerine dosya olarak eklenir (PDF, JPEG, PNG). Bu belgeler bu sürümde programda " +
  "üretilmez.";
export const EK_YOK = "Ek yok.";
export const DUGME_DOSYA_EKLE = "Dosya ekle";
export const DUGME_EKI_KAYDET = "Kaydet";
export const EK_EKLENDI = "Dosya eklendi.";
export const EK_EKLENEMEDI = "Dosya eklenemedi.";
export const EK_KAYDEDILDI = "Ek kaydedildi.";
export const EK_KAYDEDILEMEDI = "Ek kaydedilemedi.";
export const EK_ADI_OKUNAMADI = "Adı okunamayan ek";
export const DOSYA_SECIN = "Dosyayı seçin.";

/** İptal. */
export const DUGME_IPTAL = "Genel kurulu iptal et";
export const IPTAL_BASLIGI = "Genel kurul iptal edilsin mi?";
export const IPTAL_METNI =
  "Genel kurul iptal edilir: kayıt silinmez, iptal gerekçesiyle kalır. Olağan genel kurulda " +
  "hazırlıktaki birlik dönemi de iptal edilir.";
export const IPTAL_EDILDI = "Genel kurul iptal edildi.";
export const IPTAL_EDILEMEDI = "Genel kurul iptal edilemedi.";

/** Belge kartları. */
export const BELGELER_BASLIGI = "Genel Kurulun Belgeleri";
export const BELGELER_ACIKLAMASI =
  "Belgeler genel kurulun kayıtlarından üretilir; yeniden üretim yeni sürümdür. Veli adı taşıyan " +
  "çıktı saklanmaz, her basımda yeniden üretilir ve erişim günlüğüne yazılır.";
export const KATALOG_OKUNAMADI = "Belgelerin listesi okunamadı.";
export const ALAN_KIP = "Biçim";
export const KIP_KISISIZ = "Kişisiz";
export const KIP_ADLI = "Veli adlı";
export const ALAN_BELGE_TOPLANTISI = "Toplantı";
export const ALAN_MUHATAP = "Muhatap";
export const MUHATAP_ILCE = "İlçe millî eğitim müdürlüğü";
export const MUHATAP_IL = "İl millî eğitim müdürlüğü";
export const ALAN_MUHATAP_IDARE = "Muhatap idare";
export const ALAN_MUHATAP_BIRIM = "Muhatap birim";
export const MUHATAP_YARDIMI =
  "Önerilen muhatap okul bilgilerindeki il ve ilçeden kurulur; basımdan önce düzenlenebilir.";
export const DUGME_WEB = "Web sayfası olarak kaydet";
export const WEB_KAYDEDILDI = "Belge web sayfası olarak kaydedildi.";
export const ADLI_CIKTI_BASLIGI = "Veli adlı çıktı";
export const ADLI_CIKTI_ACIKLAMASI =
  "Veli adı taşır: program saklamaz, basım erişim günlüğüne yazılır. Asılmaz, okul dışına verilmez.";
export const DUGME_ADLI_PDF = "Veli adlı PDF";
export const DUGME_ADLI_WORD = "Veli adlı Word";
export const DUGME_ADLI_EXCEL = "Veli adlı Excel";
export const ADLI_CIKTI_KAYDEDILDI = "Veli adlı çıktı kaydedildi.";
export const ADLI_CIKTI_YAZILAMADI = "Veli adlı çıktı üretilemedi.";
export const DUGME_EVRAK_KAYDI = "Gelen-giden evrak defterine kaydet";
export const EVRAK_KAYDI_BASLIGI = "Giden evrak kaydı";
export const EVRAK_KAYDI_ACIKLAMASI =
  "Programın hazırladığı resmî yazı kendiliğinden kaydedilmez. Önerilen kaydı denetleyip onaylayın; " +
  "bir yazı bir kez kaydedilir.";
export const EVRAK_KAYDI_OKUNAMADI = "Kaydın önerisi okunamadı.";
export const GIDEN_KAYDEDILDI = "Yazı gelen-giden evrak defterine kaydedildi.";
export const GIDEN_KAYDEDILEMEDI = "Yazı kaydedilemedi.";
export const DUGME_EVRAK_KAYDET = "Kaydı onayla";

/** Ortak. */
export const DUGME_VAZGEC = "Vazgeç";
export const DUGME_KAYDET = "Kaydet";
export const DUGME_KAPAT = "Kapat";
export const KAYDEDILIYOR = "Kaydediliyor…";
export const YUKLENIYOR = "Okunuyor…";
export const SECIN = "Seçin";
export const SAYI_GECERSIZ = "Sıfır ya da pozitif tam sayı girin.";

/** Durumların görünen adları (backend `AssemblyStatus`). */
export const DURUM_TR: Record<GenelKurulDurumu, string> = {
  PLANLANDI: "Planlandı",
  CAGRILDI: "Çağrıldı",
  ILAN_EDILDI: "İlan edildi",
  YETER_SAYI_YOK: "Yeter sayı sağlanamadı",
  YAPILDI: "Yapıldı",
  TUTANAK_TAMAM: "Tutanak tamamlandı",
  IPTAL: "İptal edildi",
};

export const TUR_TR: Record<GenelKurulTuru, string> = {
  OLAGAN: "Olağan",
  OLAGANUSTU: "Olağanüstü",
};

/** Çağıranların görünen adları (backend `AssemblyCaller`; madde atfıyla). */
export const CAGIRAN_TR: Record<Cagiran, string> = {
  YONETIM_KURULU: "Yönetim kurulu",
  OKUL_MUDURU: "Okul müdürü (md. 9/6)",
  MUDUR_YENI_OKUL: "Okul müdürü (yeni açılan okul; md. 9/1)",
  DENETLEME_KURULU: "Denetleme Kurulu (md. 14/5)",
  UYE_BASVURUSU: "Üyelerin yazılı başvurusu (md. 9/6)",
  BASKAN_VEYA_MUDUR_13_8: "Birlik başkanı ya da okul müdürü (md. 13/8)",
  MUDUR_25_2: "Okul müdürü (md. 25/2)",
};

export const TOPLANTI_TR: Record<Toplanti, string> = {
  BIRINCI: "Birinci toplantı",
  IKINCI: "İkinci toplantı",
};

export const GUNDEM_TURU_TR: Record<GundemTuru, string> = {
  ACILIS: "Açılış",
  DIVAN_SECIMI: "Divan seçimi",
  YK_FAALIYET_RAPORU: "Yönetim kurulu faaliyet raporu",
  DK_RAPORU: "Denetleme Kurulu raporu",
  IBRA: "İbra",
  TAHMINI_BUTCE: "Tahmini bütçe",
  YETKILENDIRME: "Yetkilendirme",
  SECIM_YK: "Yönetim kurulu seçimi",
  SECIM_DK: "Denetleme Kurulu seçimi",
  ONERILER: "Öneriler",
  DILEK: "Dilek ve temenniler",
  KAPANIS: "Kapanış",
  DIGER: "Diğer",
};

export const SONUC_TR: Record<GundemSonucu, string> = {
  KABUL: "Kabul edildi",
  RET: "Reddedildi",
  GORUSULDU: "Görüşüldü",
};

export const IBRA_TR: Record<IbraSonucu, string> = {
  EDILDI: "İbra edildi",
  EDILMEDI: "İbra edilmedi",
  GORUSULMEDI: "Görüşülmedi",
};

/** Aday kaydının durumu (backend `MembershipStatus`). */
export const UYELIK_DURUMU_TR: Record<"ADAY" | "SECILDI" | "DUSTU" | "IPTAL", string> = {
  ADAY: "Aday",
  SECILDI: "Seçildi",
  DUSTU: "Düştü",
  IPTAL: "İptal edildi",
};

export const KATILIM_TURU_TR: Record<KatilimTuru, string> = {
  VELI_KURSIYER: "Veli ve kursiyer",
  OGRETMEN: "Öğretmen",
  IDARECI: "İdareci",
  HAYIRSEVER: "Hayırsever",
  DIGER: "Diğer",
};

/** Katılım düzeltmesinde düzeltilebilen sayıların adları (backend `DUZELTILEBILIR_ALANLAR`). */
export const DUZELTME_ALANI_TR: Record<string, string> = {
  first_attendee_count: "Birinci toplantıda katılan üye sayısı",
  second_attendee_count: "İkinci toplantıda katılan üye sayısı",
  parent_students_count: "Velisi katılan öğrenci sayısı",
  observer_count: "Gözlemci öğrenci sayısı",
  "attendance_by_kind.VELI_KURSIYER": "Katılan veli ve kursiyer",
  "attendance_by_kind.OGRETMEN": "Katılan öğretmen",
  "attendance_by_kind.IDARECI": "Katılan idareci",
  "attendance_by_kind.HAYIRSEVER": "Katılan hayırsever",
  "attendance_by_kind.DIGER": "Katılan diğer",
};

/** "Olağan genel kurul · 20.10.2026 10:00" */
export function genelKurulAdi(tur: GenelKurulTuru, an: string): string {
  return `${TUR_TR[tur]} genel kurul · ${an}`;
}

/** "Yeter sayı 64 (16 × 4)" */
export function yeterSayiMetni(sayi: number, taban: number | null, carpan: number | null): string {
  return taban !== null && carpan !== null ? `${sayi} (${taban} × ${carpan})` : String(sayi);
}

/** "Katılım işaretleri: 12 satır işaretli (öneri)" */
export function isaretOnerisi(sayi: number): string {
  return `Katılım işaretleri: ${sayi} satır işaretli (öneri)`;
}

/** "42 oy" */
export function oySayisi(oy: number): string {
  return `${oy} oy`;
}

/** "Kabul 40 · Ret 3 · Salonda 50" */
export function oyMetni(kabul: number | null, ret: number | null, salonda: number | null): string {
  const parcalar = [`Kabul ${kabul ?? "—"}`, `Ret ${ret ?? "—"}`];
  if (salonda !== null) parcalar.push(`Salonda ${salonda}`);
  return parcalar.join(" · ");
}

/** "Birinci toplantı · Katılan üye sayısı: 10 → 12 · 21.10.2026 09:30" */
export function duzeltmeMetni(toplanti: string, alan: string, eski: string, yeni: string): string {
  return `${toplanti} · ${alan}: ${eski} → ${yeni}`;
}

/** "Bu yazı 2026/14 numarayla kaydedildi." */
export function kayitliMetni(yil: number, no: number): string {
  return `Bu yazı ${yil}/${no} numarayla kaydedildi.`;
}

/** "Veli adlı · 120 satır · 21.10.2026 09:30" */
export function adliKayitMetni(an: string, satir: number | null): string {
  return `Son veli adlı basım: ${an}${satir !== null ? ` · ${satir} satır` : ""}`;
}
