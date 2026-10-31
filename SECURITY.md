# Güvenlik

OAB Defteri okul-aile birliğinin işlerini okulun bilgisayarında yürüten,
çevrimdışı bir masaüstü programıdır. Kayıtlar okulun bilgisayarında kalır.
OAB Defteri ağ servisi sunmaz; yalnız 127.0.0.1'de dinler.

## Açık bildirimi

Bir güvenlik açığı bulduysanız **issue açmayın**; doğrudan
aalidemirci@gmail.com adresine yazın. Şunları yazmanız yeterlidir:

- açığın ne olduğu ve nasıl tetiklendiği,
- etkilediğini düşündüğünüz sürüm,
- varsa ekran görüntüsü ya da günlük — **kişisel veri çıkarılmış olarak**.

Bildirime en geç bir hafta içinde dönüş yapılır. Düzeltme yayımlanana kadar
ayrıntıyı kamuya açık paylaşmamanızı rica ederim.

## Bildirimlere kişisel veri koymayın

Bu program öğrenci ve personel verisi işler. Issue'lara, tartışmalara ve
e-postalara **gerçek ad, okul numarası, kart numarası, veritabanı dosyası,
yedek dosyası (`.odbak`), günlük dosyası ve gerçek veri içeren ekran
görüntüsü koymayın**. Sorunu uydurma veriyle anlatın; gerekiyorsa verinin
biçimini tarif edin.

## Kapsam

- **Kapsam içi:** programın kendisi, kurulum paketleri, yedekleme ve
  şifreleme akışları.
- **Kapsam dışı:** okulun kendi ağ yapılandırması, Windows ya da Pardus
  kurulumu, üçüncü taraf kütüphanelerin kendi açıkları (onları kendi
  projelerine bildirin).

## Bilinen ve kabul edilmiş riskler

Program tek kullanıcılı ve çevrimdışıdır; tehdit modeli ve kabul edilmiş
kalan riskler `docs/teknik-borc.md` ile tasarım belgesinin §4.3 bölümünde
açıkça yazılıdır. Oradaki bir kalemi bildirmeden önce gerekçesini okuyun;
gerekçenin kendisinin yanlış olduğunu düşünüyorsanız yazın.
