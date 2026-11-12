// Organlar ekranının metinleri — tek kaynak (sözlük §1 "Organlar ekranı (F1c)", §4.1 "Organlar", §4.3).
// Kurulların adları açık yazılır ("yönetim kurulu", "Denetleme Kurulu"); kısaltma kullanıcı metnine
// çıkmaz (sözlük §1 "Organlar"). Okul müdürü yönetim kurulu üyesi değildir. Program karar defterinin
// yerine geçmez (CLAUDE.md §1). Madde atıfları korpusla doğrulanmıştır (md. 7/2, 12/3-4, 13/3, 13/6,
// 14/1, 14/3-4, 18/1). Uyarıların kendi metni sunucunundur.

import type { DusmeTuru, EngelDayanagi } from "./api";

/** Sayfanın h1'i ve gezinme etiketi (sözlük §4.1). */
export const ORGANLAR_BASLIGI = "Organlar";
export const ORGANLAR_ACIKLAMASI =
  "Okul-aile birliğinin yönetim kurulu, Denetleme Kurulu ve alım komisyonu: görevdeki üyeler, görev " +
  "bölümü, yedek çağrısı ve düşme. Kayıt silinmez; yanlış kayıt gerekçeyle iptal edilir. Program " +
  "karar defterinin yerine geçmez.";

/** Sekmeler (sözlük §4.3). */
export const SEKME_YK = "Yönetim Kurulu";
export const SEKME_DK = "Denetleme Kurulu";
export const SEKME_ALIM = "Alım Komisyonu";
export const SEKMELER_ETIKETI = "Organlar bölümleri";

/** Birlik dönemi seçimi ve boş durum. */
export const ALAN_BIRLIK_DONEMI = "Birlik dönemi";
export const DONEMLER_OKUNAMADI = "Birlik dönemleri okunamadı.";
export const DONEM_YOK_ORGAN_ACIKLAMASI =
  "Organ kayıtları birlik dönemine yazılır. Birlik dönemini Birlik Dönemi ekranından açın.";
export const DUGME_BIRLIK_DONEMINE_GIT = "Birlik Dönemi ekranını aç";

/** Kadro. */
export const KADRO_OKUNAMADI = "Kurulun kadrosu okunamadı.";
export const KADRO_UYARILARI_BASLIGI = "Kadro uyarıları";
export const ONERILER_BASLIGI = "Öneriler ve hatırlatmalar";
export const BOLUM_ASILLAR = "Görevdeki Asıl Üyeler";
export const BOLUM_YEDEKLER = "Çağrılmamış Yedek Üyeler";
export const BOLUM_KOMISYON = "Komisyon Üyeleri";
export const BOLUM_OTEKI = "Öteki Kayıtlar";
export const OTEKI_ACIKLAMASI = "Aday, düşen ve iptal edilen kayıtlar; kayıt silinmez.";
export const ASIL_YOK = "Görevdeki asıl üye yok.";
export const YEDEK_YOK = "Çağrılmamış yedek üye yok.";
export const KOMISYON_UYESI_YOK = "Komisyon üyesi girilmedi.";
export const YK_SECIM_NOTU =
  "Yönetim kurulunu genel kurul seçer. Programdan önce seçilmiş görevdeki kurul Birlik Dönemi → " +
  "Geçiş Kurulumu'nda girilir.";
export const DK_SECIM_NOTU =
  "Denetleme Kurulunun veli üyesini genel kurul, öğretmen üyelerini öğretmenler kurulu seçer. " +
  "Programdan önce seçilmiş görevdeki kurul Birlik Dönemi → Geçiş Kurulumu'nda girilir.";
export const ALIM_ACIKLAMASI =
  "Mal ve hizmet alımları yönetim kurulu üyelerinden ya da uzmanlık gerektiren işlerde birlik " +
  "üyelerinden oluşan en az üç kişilik komisyonla yapılır (md. 18/1).";

/** Satır işaretleri. */
export const CIP_ENGEL = "Görev alma engeli";
export const CIP_DEVRALINAN = "Devralınan";
export const CIP_ERTELENDI = "Olağanüstü genel kurula kadar sürer";
export const CIP_UZMANLIK = "Uzmanlık gerektiren iş";

/** Düğmeler. */
export const DUGME_GOREV_BOLUMU = "Görev bölümü";
export const DUGME_DK_GOREV_BOLUMU = "Görev bölümü ve denetim planı";
export const DUGME_OGRETMEN_EKLE = "Öğretmen üye ekle";
export const DUGME_KOMISYON_UYESI_EKLE = "Komisyon üyesi ekle";
export const DUGME_KAYDI_IPTAL = "Kaydı iptal et";
export const DUGME_DAYANAK = "Dayanağı göster";
export const DUGME_ENGEL = "Görev alma engelini düzenle";
export const DUGME_BILGILER = "Bilgileri düzenle";
export const DUGME_YEDEK_CAGIR = "Yedeği çağır";
export const DUGME_DUSUR = "Üyeliği düşür";

/** Aylık toplantı günü (yönetim kurulu; dönem ayarı). */
export const TOPLANTI_GUNU_BASLIGI = "Aylık Toplantı Günü";
export const TOPLANTI_GUNU_ACIKLAMASI =
  "Yönetim kurulu eğitim ve öğretim yılı içinde ayda bir toplanır (md. 13/3); günü kurul belirler. " +
  "Program bu günü görev bölümü karar taslağına yazar, ona bağlı bir kural koymaz.";
export const ALAN_TOPLANTI_GUNU = "Toplantı günü";
export const TOPLANTI_GUNU_YARDIMI = "Örnek: her ayın ilk salısı";
export const GIRILMEDI = "Girilmedi.";
export const TOPLANTI_GUNU_KAYDEDILDI = "Toplantı günü kaydedildi.";
export const TOPLANTI_GUNU_KAYDEDILEMEDI = "Toplantı günü kaydedilemedi.";

/** Üyeliğin penceresi. */
export const UYELIK_PENCERESI_BASLIGI = "Üyelik";
export const ALAN_DURUM = "Durum";
export const ALAN_KAYIT = "Kayıt";
export const KAYIT_DEVRALINAN = "Devralınan (geçiş kurulumu)";
export const KAYIT_PROGRAM = "Programda girildi";
export const ALAN_CAGRI_GUNU = "Yedekten çağrıldığı gün";
export const ALAN_DUSME = "Düşme";
export const ALAN_SUC_BEYANI = "Görev alma engeli beyanı (okul uygulaması)";
export const ALAN_TEK_BIRLIK_BEYANI = "Tek birlik yönetimi beyanı (okul uygulaması)";
export const ALAN_GOREVLENDIRME = "Başka kurumda görevlendirme";
export const ALAN_ENGEL = "Görev alma engeli";
export const ENGEL_YOK = "Yok";
export const ALAN_DAYANAK = "Dayanak";
export const ALAN_YK_SAYAC = "Yönetim kuruluna seçilme sayısı (md. 12/4)";
export const ALAN_DK_SAYAC = "Denetleme Kurulu başkanlığı sayısı (md. 14/3)";
export const UYUM_BASLIGI = "Açık uyarılar";
export const DAYANAK_OKUMA_NOTU = "Bu okuma erişim günlüğüne yazıldı.";
export const DAYANAK_OKUNAMADI = "Dayanak okunamadı.";

/** Üyelik durumları (backend `MembershipStatus`). */
export const DURUM_TR = {
  ADAY: "Aday",
  SECILDI: "Seçildi",
  DUSTU: "Düştü",
  IPTAL: "İptal edildi",
} as const;

/** Seçim kanallarının görünen adları (backend `ElectedBy`). */
export const SECIM_KANALI_TR = {
  GENEL_KURUL: "Genel kurul",
  OGRETMENLER_KURULU: "Öğretmenler kurulu",
  MEM_GOREVLENDIRME: "İl/ilçe millî eğitim müdürlüğü görevlendirmesi",
  YK_KARARI: "Yönetim kurulu kararı",
  OKUL_IDARESI: "Okul idaresi",
  KENDILIGINDEN: "Birlik başkanı sıfatıyla",
} as const;

/** Düşme türleri (backend `DropKind`). */
export const DUSME_TURU_TR: Record<DusmeTuru, string> = {
  OGRENCI_AYRILDI: "Öğrencisi okuldan ayrıldı",
  DEVAMSIZLIK: "Devamsızlık",
  ISTIFA: "İstifa",
  BASKA_KURUMDA_GOREV: "Başka kurumda görev",
  OLAGANUSTU_GK_SECIMI: "Olağanüstü genel kurul seçimi",
  DIGER: "Diğer",
};

/** Görev alma engelinin dayanakları (backend `EligibilityBarBasis`; özel nitelikli). */
export const ENGEL_DAYANAGI_TR: Record<EngelDayanagi, string> = {
  SUC_12_5_14_7: "Suç engeli (md. 12/5, 14/7)",
  TEK_BIRLIK_12_4: "Başka birlik yönetiminde görev (md. 12/4)",
};

/** Görev alma engelinin penceresi. */
export const ENGEL_PENCERESI_BASLIGI = "Görev alma engeli";
export const ENGEL_ACIKLAMASI =
  "Dayanak özel nitelikli kişisel veridir: şifreli saklanır, yalnız program yöneticisi ve yönetim " +
  "kurulu rolleri okur. Denetleme Kurulu ve okul müdürü yalnız engelin var olduğunu görür.";
export const ALAN_ENGEL_HUKMU = "Engel";
export const ENGEL_VAR = "Var";
export const ALAN_TESPIT_GUNU = "Tespit günü";
export const ENGEL_DAYANAK_ZORUNLU = "Dayanağı ve tespit gününü girin.";
export const ENGEL_KAYDEDILDI = "Görev alma engeli kaydedildi.";
export const ENGEL_KAYDEDILEMEDI = "Görev alma engeli kaydedilemedi.";

/** Üyeliğin bilgileri (kişisiz ayrıntılar). */
export const BILGI_PENCERESI_BASLIGI = "Üyeliğin bilgileri";
export const BEYAN_YARDIMI = "Okulun beyan uygulamasıdır; Yönetmelik hükmü değildir.";
export const ALAN_GOREVLENDIRME_BASLANGICI = "Görevlendirmenin başlangıcı";
export const ALAN_GOREVLENDIRME_BITISI = "Görevlendirmenin bitişi";
export const GOREVLENDIRME_YARDIMI =
  "Denetleme Kurulunun öğretmen üyesi başka kurumda dört aydan fazla süreli görevlendirilirse " +
  "yerine yedeği çağrılır (md. 14/6).";
export const BILGILER_KAYDEDILDI = "Üyeliğin bilgileri kaydedildi.";
export const BILGILER_KAYDEDILEMEDI = "Üyeliğin bilgileri kaydedilemedi.";

/** Yedek çağrısı. */
export const YEDEK_PENCERESI_BASLIGI = "Yedek üye asıl üyeliğe çağrılsın mı?";
export const YEDEK_METNI_YK =
  "Yedekler aldıkları oy sırasıyla asıl üyeliğe çağrılır (md. 13/6). Sıra dışı çağrı gerekçe " +
  "ister. Yeni bileşimle kurul bir hafta içinde görev dağılımı yapar (md. 12/3).";
export const YEDEK_METNI_DK =
  "Denetleme Kurulunun yedeği yönetim kurulu kararı gerekmeden çağrılır; çağrılan yedek kendi " +
  "koltuğunun asıl yerine geçer.";
export const ALAN_CAGRI_GUNU_GIRIS = "Çağrı günü";
export const ALAN_YEDEK_KARARI = "Yedek çağırma kararı";
export const ALAN_KARAR_BAGLANMASIN = "Bağlanmasın";
export const KARAR_BAGI_YARDIMI =
  "Yalnız kabul edilmiş ya da karar defterine işlenmiş yönetim kurulu kararı bağlanabilir.";
export const KARAR_YOK =
  "Bağlanabilecek kabul edilmiş yönetim kurulu kararı yok; karar bağı olmadan kayıt gerekçe ister.";
export const YEDEK_CAGRILDI = "Yedek üye asıl üyeliğe çağrıldı.";
export const YEDEK_CAGRILAMADI = "Yedek üye çağrılamadı.";

/** Düşme. */
export const DUSME_PENCERESI_BASLIGI = "Üyelik düşürülsün mü?";
export const DUSME_METNI =
  "Kayıt silinmez; düşen üyelik kurulun geçmişinde kalır. Üyeliğe bağlı hesap aynı anda askıya " +
  "alınır.";
export const ALAN_DUSME_TURU = "Düşme türü";
export const ALAN_DUSME_GUNU = "Düşme günü";
export const ALAN_DUSME_ACIKLAMASI = "Açıklama";
export const DUSME_ACIKLAMASI_YARDIMI = "İsteğe bağlı; şifreli saklanır.";
export const ALAN_ERTELE = "Olağanüstü genel kurula kadar sürsün";
export const ERTELE_YARDIMI =
  "Yönetim kurulunun üye sayısı toplantı yeter sayısının altına düşecekse öğrencisi ayrılan velinin " +
  "üyeliği olağanüstü genel kurula kadar devam eder (md. 7/2).";
export const DUSME_TURU_SECIN = "Düşme türünü seçin.";
export const UYELIK_DUSURULDU = "Üyelik düşürüldü.";
export const UYELIK_ERTELENDI = "Üyelik olağanüstü genel kurula kadar devam edecek.";
export const UYELIK_DUSURULEMEDI = "Üyelik düşürülemedi.";

/** İptal. */
export const UYELIK_IPTAL_BASLIGI = "Üyelik kaydı iptal edilsin mi?";
export const UYELIK_IPTAL_METNI =
  "Yanlış girilmiş kayıt iptal edilir: kayıt silinmez, iptal gerekçesiyle kalır; kayda bağlı hesap " +
  "aynı anda askıya alınır. Doğru bilgi yeni kayıtla girilir.";

/** Görev bölümü (iki kurul). */
export const YK_GOREV_BOLUMU_BASLIGI = "Yönetim kurulunun görev bölümü";
export const YK_GOREV_BOLUMU_ACIKLAMASI =
  "Kurul, görevdeki asıl üyeleri arasından başkan, başkan yardımcısı, muhasip ve sekreter seçer " +
  "(md. 12/3). Yalnız verilen görevleri seçin; görevin önceki sahibi üye olur. Kayıt bir görev " +
  "bölümü toplantısı ve karar taslağı açar; görevi değişen üyenin hesabı askıya alınır.";
export const DK_GOREV_BOLUMU_BASLIGI = "Denetleme Kurulunun görev bölümü ve denetim planı";
export const DK_GOREV_BOLUMU_ACIKLAMASI =
  "Asıl üyeler genel kuruldan sonraki ilk hafta içinde toplanır ve aralarından bir başkan seçer " +
  "(md. 14/1). Denetim planına yönetim kurulunun faaliyetlerinin inceleneceği günler yazılır; kurul " +
  "bu incelemeyi yılda en az iki defa yapar (md. 14/4).";
export const ALAN_TOPLANTI_ZAMANI = "Toplantının günü ve saati";
export const ALAN_YER = "Yer";
export const GOREV_DEGISMESIN = "Verilmesin";
export const KATILIM_BASLIGI = "Katılım";
export const KATILDI = "Katıldı";
export const OZURLU = "Özürlü";
export const OZURSUZ = "Özürsüz";
export const DENETIM_PLANI_BASLIGI = "Denetim planı";
export const DUGME_INCELEME_GUNU_EKLE = "İnceleme günü ekle";
export const DUGME_KALDIR = "Kaldır";
export const TOPLANTI_ZAMANI_ZORUNLU = "Toplantının günü ve saatini girin.";
export const GOREV_SECIN = "En az bir görev seçin.";
export const TEK_GOREV = "Bir üyeye tek görev verilir.";
export const BASKAN_SECIN = "Başkanı seçin.";
export const ASIL_UYE_YOK_GOREV_BOLUMU = "Görevdeki asıl üye yok; görev bölümü yapılamaz.";
export const GOREV_BOLUMU_KAYDEDILDI = "Görev bölümü kaydedildi.";
export const GOREV_BOLUMU_KAYDEDILEMEDI = "Görev bölümü kaydedilemedi.";

/** Denetleme Kuruluna öğretmen üye. */
export const OGRETMEN_PENCERESI_BASLIGI = "Denetleme Kuruluna öğretmen üye";
export const OGRETMEN_ACIKLAMASI =
  "Denetleme Kurulunun öğretmen üyelerini öğretmenler kurulu seçer; okulda yeteri kadar öğretmen " +
  "yoksa il/ilçe millî eğitim müdürü onayıyla başka okulların öğretmenleri arasından görevlendirme " +
  "yapılır (md. 14/1).";
export const UYE_EKLENDI = "Üye eklendi.";
export const UYE_EKLENEMEDI = "Üye eklenemedi.";

/** Alım komisyonu üyesi. */
export const KOMISYON_PENCERESI_BASLIGI = "Alım komisyonu üyesi";
export const ALAN_UZMANLIK = "Uzmanlık gerektiren iş için";
export const UZMANLIK_YARDIMI =
  "Yönetim kurulu üyesi olmayan birlik üyesi yalnız uzmanlık gerektiren işlerde komisyona girer.";
export const ALAN_BASLANGIC_GUNU = "Başlangıç günü";

/** Bağlanabilir kararın seçenek adı: "Sıra no 12 · 15.10.2026" (sıra no girilmediyse yalnız gün). */
export function kararSecenegi(no: number | null, gun: string): string {
  return no === null ? gun : `Sıra no ${no} · ${gun}`;
}

/** "Asıl üye: 5 · Yedek üye: 4" */
export function kadroOzeti(asil: number, yedek: number): string {
  return `Asıl üye: ${asil} · Yedek üye: ${yedek}`;
}

/** "Komisyon üyesi: 3" */
export function komisyonOzeti(sayi: number): string {
  return `Komisyon üyesi: ${sayi}`;
}

/** "Yedekten çağrıldı · 15.10.2026" */
export function yedektenCagrildiMetni(gun: string): string {
  return `Yedekten çağrıldı · ${gun}`;
}

/** "2 açık uyarı" */
export function acikUyariMetni(sayi: number): string {
  return `${sayi} açık uyarı`;
}

/** "Var · tespit günü 14.10.2026" */
export function engelVarMetni(gun: string): string {
  return `Var · tespit günü ${gun}`;
}

/** Seçilme sayacı: "3 (programda 1, programdan önce 2)" ya da beyan bilinmiyorsa "Programda 1; …". */
export function sayacMetni(program: number, beyan: number | null): string {
  if (beyan === null) return `Programda ${program}; programdan önceki sayı bilinmiyor`;
  return `${program + beyan} (programda ${program}, programdan önce ${beyan})`;
}

/** "Ad Soyad kaydını aç" */
export function satirEtiketi(ad: string): string {
  return `${ad} kaydını aç`;
}

/** "N. inceleme günü" */
export function incelemeGunuEtiketi(sira: number): string {
  return `${sira}. inceleme günü`;
}

/** Denetim planı satırının "Kaldır" düğmesinin erişilebilir adı: "N. inceleme günü: Kaldır". */
export function kaldirEtiketi(sira: number): string {
  return `${incelemeGunuEtiketi(sira)}: ${DUGME_KALDIR}`;
}
