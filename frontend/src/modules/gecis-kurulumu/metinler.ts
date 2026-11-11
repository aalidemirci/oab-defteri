// Geçiş kurulumu ekranının ve sihirbazın Birlik Dönemi adımının metinleri — tek kaynak (tasarım §7.9;
// plan F1c kararları "Geçiş adımı atlanabilir", 8. adımın kararı ve notları; sözlük §4.1, §4.4).
// Kurulların adları açık yazılır ("yönetim kurulu", "Denetleme Kurulu"); kısaltma kullanıcı metnine
// çıkmaz (sözlük §1 "Organlar"). Program karar defterinin yerine geçmez (CLAUDE.md §1).

import type { GecisAdimi, GecisDurumu } from "../birlik-donemi/api";

/** Sayfanın h1'i (üst çubukla aynı; sözlük §4.1). Gezinmede yoktur: Birlik Dönemi'nden açılır. */
export const GECIS_BASLIGI = "Geçiş Kurulumu";

export const GECIS_ACIKLAMASI =
  "Program okula birlik döneminin ortasında girdiyse programdan önce başlamış birlik dönemi ve " +
  "görevdeki kurul burada programa alınır. Girilen her kayıt denetim izinde geçiş kaydı olarak " +
  "durur; yanlış kayıt değiştirilmez, gerekçeyle iptal edilip yeniden girilir. “Geçiş kurulumu " +
  "tamamlandı” işaretinden sonra geçiş kayıtları salt okunurdur.";

export const GECIS_OKUNAMADI = "Geçiş kurulumunun durumu okunamadı.";

/** Durum (backend `gecis.yol_haritasi_durumu`). */
export const DURUM_ETIKETI = "Durum";
export const GECIS_DURUMU_TR: Record<GecisDurumu, string> = {
  BASLAMADI: "Başlamadı",
  SURUYOR: "Sürüyor",
  TAMAMLANDI: "Tamamlandı",
  GEREKMIYOR: "Gerekmiyor",
};
export const GEREKMIYOR_NOTU =
  "Birlik dönemi genel kurulla açıldığı için geçiş kurulumu gerekmiyor.";
export const ACIK_ADIMLAR_ETIKETI = "Açık adımlar";
export const GECIS_ADIMI_TR: Record<GecisAdimi, string> = {
  donem: "ilk birlik dönemi",
  kurul: "görevdeki kurul",
  sayac_beyani: "programdan önceki seçilme sayıları",
  karar_defteri: "karar defteri",
  tamamla: "“Geçiş kurulumu tamamlandı” işareti",
};

/** 1. adım: ilk birlik dönemi (sihirbazın Birlik Dönemi adımıyla ortak form). */
export const ILK_DONEM_BASLIGI = "İlk Birlik Dönemi";
export const ILK_DONEM_ACIKLAMASI =
  "Birlik dönemi son olağan genel kurulun günüyle başlar. Programa başlama günü dönem başından " +
  "önce olamaz.";
/** Dönem yokken yazamayan rolde (öğütsüz; Birlik Dönemi ekranının boş başlığıyla aynı söz). */
export const ILK_DONEM_BOS = "Birlik dönemi açılmadı.";
export const ALAN_DONEM_ADI = "Birlik döneminin adı";
export const DONEM_ADI_YARDIMI = "Örnek: 2026-2027 birlik dönemi";
export const ALAN_GECIS_DERS_YILI = "Ders yılı";
export const GECIS_DERS_YILI_YARDIMI =
  "Son olağan genel kurulun gününü kapsayan ders yılı. Listede yoksa Ayarlar → Ders Yılları'ndan " +
  "ekleyin; geçmiş ders yılı aktifleştirilmeden eklenir.";
export const ALAN_DONEM_BASI = "Son olağan genel kurulun günü";
export const DONEM_BASI_YARDIMI = "Birlik dönemi bu günle başlar.";
export const ALAN_PROGRAMA_BASLAMA = "Programa başlama günü";
export const PROGRAMA_BASLAMA_YARDIMI = "Boş bırakılırsa bugündür.";
export const DONEM_ADI_ZORUNLU = "Birlik döneminin adı zorunludur.";
export const DERS_YILI_SECIN = "Ders yılını seçin.";
export const DONEM_BASI_ZORUNLU = "Son olağan genel kurulun günü zorunludur.";
export const DUGME_DONEMI_AC = "Birlik dönemini aç";
export const DONEM_ACILDI = "Birlik dönemi açıldı.";
export const DONEM_ACILAMADI = "Birlik dönemi açılamadı.";

/** 2. adım: görevdeki kurul (devralınan kayıtlar). */
export const KURUL_BASLIGI = "Görevdeki Kurul";
export const KURUL_ACIKLAMASI =
  "Görevdeki yönetim kurulu, Denetleme Kurulu ve birlik temsilcileri devralınan kayıt olarak " +
  "girilir; aday kaydı aranmaz. Kişi türü, okul müdürünün yönetim kuruluna girememesi ve aynı " +
  "kişinin iki kurulda bulunmaması yine denetlenir. Kişiler önce Kişiler → Birlik Kişileri'nde " +
  "kaydedilir.";
export const KURUL_BOS = "Görevdeki kurul girilmedi.";
export const DUGME_UYE_EKLE = "Görevdeki üyeyi ekle";
export const UYE_PENCERESI_BASLIGI = "Görevdeki üyeyi ekle";
export const ALAN_KISI = "Kişi";
export const KISI_ARA_YER_TUTUCU = "Ad soyad…";
export const KISI_BULUNAMADI = "Bu adla etkin birlik kişisi yok.";
export const ALAN_KURUL = "Kurul";
export const KURUL_YONETIM = "Yönetim kurulu";
export const KURUL_DENETLEME = "Denetleme Kurulu";
export const KURUL_TEMSILCI = "Birlik temsilcisi";
export const ALAN_KOLTUK = "Koltuk";
export const KOLTUK_ASIL = "Asıl";
export const KOLTUK_YEDEK = "Yedek";
export const ALAN_KOLTUK_GRUBU = "Denetleme Kurulundaki koltuğu";
export const KOLTUK_GRUBU_VELI = "Veli ya da kursiyer";
export const KOLTUK_GRUBU_OGRETMEN = "Öğretmen";
export const ALAN_GOREV = "Görev";
export const ALAN_SECIM_KANALI = "Seçildiği yer";
export const ALAN_TEMSIL = "Temsil edilen kurul ya da komisyon";
export const ALAN_YEDEK_SIRASI = "Yedek sırası";
export const ALAN_SECILDIGI_GUN = "Seçildiği gün";
export const SECILDIGI_GUN_YARDIMI = "Boş bırakılırsa birlik döneminin başıdır.";
export const ALAN_KANIT = "Kanıt";
export const KANIT_YARDIMI =
  "Örnek: seçildiği genel kurulun tarihi, görev bölümü kararının karar defterindeki sıra no'su.";
export const ALAN_MEM_ONAY_NO = "Millî eğitim müdürlüğü onay sayısı";
export const KISI_SECIN = "Kişiyi seçin.";
export const TEMSIL_SECIN = "Temsil edilen kurul ya da komisyonu seçin.";
export const UYE_EKLENDI = "Görevdeki üye eklendi.";
export const UYE_EKLENEMEDI = "Görevdeki üye eklenemedi.";
export const SUTUN_AD_SOYAD = "Ad soyad";
export const SUTUN_KURUL = "Kurul";
export const SUTUN_KOLTUK = "Koltuk";
export const SUTUN_GOREV = "Görev";
export const DUGME_KAYDI_IPTAL = "İptal et";
export const DEVRALINAN_IPTAL_BASLIGI = "Devralınan kayıt iptal edilsin mi?";
export const DEVRALINAN_IPTAL_METNI =
  "Kayıt silinmez, iptal gerekçesiyle kalır; kayda bağlı hesap aynı anda askıya alınır. Doğru " +
  "bilgi yeni kayıtla girilir.";
export const KAYIT_IPTAL_EDILDI = "Kayıt iptal edildi.";
export const KAYIT_IPTAL_EDILEMEDI = "Kayıt iptal edilemedi.";
export const IPTAL_GEREKCESI = "İptal gerekçesi";
export const IPTAL_GEREKCESI_YAZIN = "İptal gerekçesi yazın.";

/** 3. adım: programdan önceki seçilme sayıları. */
export const SAYAC_BASLIGI = "Programdan Önceki Seçilme Sayıları";
export const SAYAC_ACIKLAMASI =
  "Görevdeki kurulun kişileri için karar defterinden sayılan seçilme sayısını girin; " +
  "sayılamıyorsa “Bilinmiyor” seçin. Beyan görevdeki seçimi de içerir; devralınan kayıt ayrıca " +
  "sayılmaz. “Bilinmiyor” denen bütün kişiler için seçilme sınırı uyarısı tek gerekçeyle kapanır.";
/** Yazılamazken (salt okur rol, işaretten sonra, D7) açıklamanın öğütsüz kısmı. */
export const SAYAC_ACIKLAMASI_BILGI =
  "Beyan görevdeki seçimi de içerir; devralınan kayıt ayrıca sayılmaz. “Bilinmiyor” denen bütün " +
  "kişiler için seçilme sınırı uyarısı tek gerekçeyle kapanır.";
/** Kişi yokken yazabilen rolde; yazılamazken `KURUL_BOS`. */
export const SAYAC_KISI_YOK = "Önce görevdeki kurulu girin.";
export const DUGME_SAYAC_BEYANI = "Seçilme sayılarını beyan et";
export const SAYAC_PENCERESI_BASLIGI = "Seçilme sayılarını beyan et";
export const ALAN_YK_SAYISI = "Yönetim kuruluna seçilme sayısı";
export const ALAN_DK_BASKANLIK_SAYISI = "Denetleme Kurulu başkanlığı sayısı";
export const SAYAC_GIRILMEDI = "Girilmedi";
export const SAYAC_BILINMIYOR = "Bilinmiyor";
export const ALAN_DUZELTME_GEREKCESI = "Düzeltme gerekçesi";
export const DUZELTME_GEREKCESI_YARDIMI =
  "Verilmiş bir sayı değiştiğinde ya da “Bilinmiyor”a döndüğünde gerekçe zorunludur.";
export const DUZELTME_GEREKCESI_YAZIN = "Düzeltme gerekçesi yazın.";
export const SAYAC_KAYDEDILDI = "Seçilme sayıları kaydedildi.";
export const SAYAC_KAYDEDILEMEDI = "Seçilme sayıları kaydedilemedi.";
export const SAYAC_UYUM_BASLIGI = "Seçilme sınırı uyarıları";

/** 4. adım: karar defteri. */
export const DEFTER_BASLIGI = "Karar Defteri";
export const DEFTER_ACIKLAMASI =
  "Program karar defterinin yerine geçmez; programdan önceki son karar sıra no'su ve sayfası " +
  "kaydedilir. Karar defteri noterce tasdik edilir (md. 23/2); tasdik bilgisi girilmezse defter " +
  "için bir gerekçe istenir.";
/** Defter girilmemişken yazılamayan hâlde (salt okur rol, işaretten sonra, D7). */
export const DEFTER_BOS = "Karar defteri girilmedi.";
export const ALAN_SON_SIRA_NO = "Programdan önceki son karar sıra no'su";
export const ALAN_SON_SAYFA = "Programdan önceki son sayfa";
export const ALAN_TASDIK_MAKAMI = "Tasdik eden makam";
export const TASDIK_NOTER = "Noter";
export const TASDIK_MEM = "İl/ilçe millî eğitim müdürlüğü";
export const ALAN_TASDIK_GUNU = "Tasdik günü";
export const ALAN_TASDIK_NO = "Tasdik no";
export const ALAN_SAYFA_SAYISI = "Sayfa sayısı";
export const ALAN_DEFTER_ACILIS = "Defterin açılış günü";
export const SON_SIRA_NO_ZORUNLU = "Son karar sıra no'su zorunludur.";
export const SON_SAYFA_ZORUNLU = "Son sayfa zorunludur.";
export const DUGME_DEFTERI_KAYDET = "Karar defterini kaydet";
export const DEFTER_KAYDEDILDI = "Karar defteri kaydedildi.";
export const DEFTER_KAYDEDILEMEDI = "Karar defteri kaydedilemedi.";
export const DEFTER_IPTAL_BASLIGI = "Karar defteri kaydı iptal edilsin mi?";
export const DEFTER_IPTAL_METNI =
  "Kayıt silinmez, iptal gerekçesiyle kalır; tasdik uyarısı kapanır. Doğru bilgi yeni kayıtla " +
  "girilir.";
export const DEFTER_UYUM_BASLIGI = "Karar defterinin tasdik uyarısı";

/** 5. adım: "Geçiş kurulumu tamamlandı" işareti. */
export const TAMAMLA_BASLIGI = "Tamamlama";
export const TAMAMLA_ACIKLAMASI =
  "İşaret konunca geçiş kayıtları kilitlenir: eklenemez, düzeltilemez, iptal edilemez. Adımlar " +
  "eksik bırakılabilir; işaretten önce bütün kayıtları gözden geçirin.";
export const DUGME_TAMAMLA = "Geçiş kurulumunu tamamla";
export const TAMAMLA_ONAY_BASLIGI = "Geçiş kurulumu tamamlansın mı?";
export const TAMAMLA_ONAY_METNI =
  "Geçiş kayıtları kilitlenir; sonra eklenemez, düzeltilemez ve iptal edilemez.";
export const DUGME_TAMAMLANDI_ISARETLE = "Tamamlandı olarak işaretle";
export const GECIS_TAMAMLANDI = "Geçiş kurulumu tamamlandı.";
export const GECIS_TAMAMLANAMADI = "Geçiş kurulumu tamamlanamadı.";

/** "Geçiş kurulumu dd.mm.yyyy günü tamamlandı; …" */
export function tamamlandiNotu(gun: string): string {
  return `Geçiş kurulumu ${gun} günü tamamlandı; geçiş kayıtları salt okunurdur.`;
}

/** Onay diyaloğunda eksik adımların cümlesi. */
export function acikAdimlarCumlesi(adimlar: readonly GecisAdimi[]): string {
  const eksik = adimlar.filter((a) => a !== "tamamla").map((a) => GECIS_ADIMI_TR[a]);
  return eksik.length === 0 ? "" : `Eksik adımlar: ${eksik.join(", ")}.`;
}

/** Sihirbazın Birlik Dönemi adımı (atlanabilir; sözlük §4.4). */
export const SIHIRBAZ_ADIM_ADI = "Birlik Dönemi";
export const SIHIRBAZ_ADIM_ACIKLAMASI =
  "Program okula birlik döneminin ortasında giriyorsa birlik dönemini burada açın. Bu adım " +
  "atlanabilir: okulda daha önce genel kurul yapılmadıysa adımı atlayın. Eksik kalan adım Genel " +
  "Bakış'taki yol haritasında görünür.";
export const SIHIRBAZ_DEVAM_NOTU =
  "Geçiş kurulumunun öteki adımları (görevdeki kurul, seçilme sayıları, karar defteri) kurulumdan " +
  "sonra Birlik Dönemi → Geçiş Kurulumu'ndadır.";

/** Görevlerin görünen adları (sözlük §1 "Yönetim kurulunun görevleri"). */
export const GOREV_TR = {
  BASKAN: "Başkan",
  BASKAN_YARDIMCISI: "Başkan yardımcısı",
  MUHASIP: "Muhasip",
  SEKRETER: "Sekreter",
  KATIP: "Kâtip",
  UYE: "Üye",
} as const;

/** Seçim kanallarının görünen adları (backend `ElectedBy`). */
export const SECIM_KANALI_OGRETMENLER_KURULU = "Öğretmenler kurulu";
export const SECIM_KANALI_MEM = "İl/ilçe millî eğitim müdürlüğü görevlendirmesi";

/** "Yedek (2. sıra)" */
export function koltukMetni(koltuk: "ASIL" | "YEDEK", sira: number | null): string {
  if (koltuk === "ASIL") return KOLTUK_ASIL;
  return sira === null ? KOLTUK_YEDEK : `${KOLTUK_YEDEK} (${sira}. sıra)`;
}
