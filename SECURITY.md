# Güvenlik

OAB Defteri okul-aile birliğinin işlerini okulun bilgisayarında yürüten,
çevrimdışı bir masaüstü programıdır. Kayıtlar okulun bilgisayarında kalır.
Program ağ servisi sunmaz: yönetim sunucusu yalnız `127.0.0.1`'de, rastgele portta
ve oturum belirteciyle dinler; hiçbir port okul ağına açılmaz. Dış istek yalnız
kullanıcının başlattığı güncelleme denetiminden çıkar.

## Açık bildirimi

Bir güvenlik açığı bulduysanız **issue açmayın**; doğrudan
aalidemirci@gmail.com adresine yazın. Şunları yazmanız yeterlidir:

- açığın ne olduğu ve nasıl tetiklendiği,
- etkilediğini düşündüğünüz sürüm,
- varsa ekran görüntüsü ya da günlük — **kişisel veri çıkarılmış olarak**.

Bildirime en geç bir hafta içinde dönüş yapılır. Düzeltme yayımlanana kadar
ayrıntıyı kamuya açık paylaşmamanızı rica ederim.

## Bildirimlere kişisel veri koymayın

Bu program okul-aile birliğinin kayıtlarını işler: veli adı ve öğrencinin
sınıfı, birlik organlarındaki ve personeldeki kişilerin adı ve görevi, birliğin
mali kayıtları. Issue'lara, tartışmalara ve e-postalara **gerçek veli, öğrenci
ya da personel adı, sınıf listesi, banka hesap özeti ya da hesap numarası,
TEFBİS ya da e-Okul çıktısı, veritabanı dosyası, yedek dosyası (`.odbak`),
günlük dosyası ve gerçek veri içeren ekran görüntüsü koymayın**. Sorunu uydurma veriyle anlatın; gerekiyorsa verinin
biçimini tarif edin.

## Kapsam

- **Kapsam içi:** programın kendisi, kurulum paketleri, yedekleme ve
  şifreleme akışları.
- **Kapsam dışı:** okulun kendi ağ yapılandırması, Windows ya da Pardus
  kurulumu, üçüncü taraf kütüphanelerin kendi açıkları (onları kendi
  projelerine bildirin).

## Bilinen ve kabul edilmiş riskler

Program okulun tek bilgisayarında çalışan, çevrimdışı bir programdır; tehdit
modeli ve kabul edilmiş kalan riskler genel tasarım belgesinin
(`docs/tasarim/2026-10-31-genel-tasarim.md`) §4.3 "Tehdit modeli" ve §13
"Devralınan kusurlar" bölümlerinde açıkça yazılıdır. Oradaki bir kalemi
bildirmeden önce gerekçesini okuyun; gerekçenin kendisinin yanlış olduğunu
düşünüyorsanız yazın.
