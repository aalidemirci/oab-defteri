# `docs/mevzuat/` — OAB Defteri mevzuat korpusu

*Kuruluş: 31.10.2026 (F0-1). Bu dizin programın dayandığı mevzuatın kanonik metinlerini tutar. Programın koyduğu
her kural (oran, süre, yeter sayı, sınır) buradaki bir çapaya dayanır; doğrulanamayan hüküm koda, arayüze ve evraka
girmez (CLAUDE.md altın kural 1).*

---

## 1. Kurallar

- **Birebir metin.** Hükümler özetlenmez, düzeltilmez; kaynaktaki yazım biçimleri korunur. Kısmi dosyada alınmayan
  fıkra ve bentler `(…)` ile gösterilir.
- **Şerhler aynen.** `(Değişik:…)`, `(Ek:…)`, `(Mülga:…)` ibareleri kaynaktaki gibi kalır. `(Mülga:…)` görülen hüküm
  **yoktur**; programda kullanılmaz. `(Değişik:…)` hükmün en güncel hâli esastır.
- **Kaynak resmîdir:** mevzuat.gov.tr konsolide metni, Resmî Gazete, mevzuat.meb.gov.tr, Bakanlık birimlerinin
  sitesi. Haber ve paylaşım sitesi metni korpusa giremez.
- **Özelge ve sirküler mevzuat değildir.** Bunlar `bilgi/` alt dizininde "özelge" etiketiyle durur; kural paketine
  giremez, evrakta hüküm diye basılmaz, yalnız bilgi ve uyarı metnine dayanak olur.
- **`.draft-` önekli dosya** doğrulanmamıştır ve hiçbir kuralın dayanağı olamaz.
- **Silme yok.** Yürürlükten kalkan metnin dosyası kalır; frontmatter'a `yururlukte: false` ve
  `yururlukten-kalkma: <tarih>` eklenir. Eski dönemlerin kural sürümü ona atıf yapmaya devam eder.
- **Kişisel ve kurumsal veri yok.** Depo kamuya açılacaktır: okul adı, ilçe yazışması, iç iş numarası, yerel dosya
  yolu ve kişi verisi hiçbir dosyaya girmez (bkz. §5).

## 2. Dosya biçimi ve çapalar

Dosya adlandırma, frontmatter ve çapa biçimi yazarın evrak çalışmasındaki kaynak korpusla aynıdır: kebab-case ASCII
ad (kanunlarda numara önde: `6698-kvkk.md`), YAML frontmatter, her madde `<a id="madde-N"></a>` çapasıyla başlar;
geçici madde `gecici-madde-N`, ekler `ek-1`, `ek-2`. **Çapalar değişmez** — kural paketindeki her kuralın `madde`
alanı `<dosya>#<çapa>` biçiminde buraya bağlanır ve F1 kural testleri çapanın varlığını denetler (atıf kilidi).
Fıkra ve bent, çapadan ayrı alanda tutulur (ör. `meb-okul-aile-birligi-yonetmeligi.md#madde-9`, fıkra 2).

Kaynak korpusun alanlarına ek olarak her dosyada iki alan vardır:

| Alan | Anlamı |
|---|---|
| `oab-kaynak` | Metnin nereden, hangi sürümden, ne zaman alındığı |
| `oab-teyit` | Resmî kaynakla son karşılaştırmanın tarihi ve yöntemi |

## 3. Teyit yöntemi (31.10.2026)

- **mevzuat.gov.tr'deki metinler:** konsolide metin (`MevzuatFihristDetayIframe`) tarayıcıda açıldı; metin
  `MADDE N` / `GEÇİCİ MADDE N` başlıklarından madde madde bölündü, yalnız harf ve rakam bırakılarak normalize edildi,
  sitedeki dipnot imleri (`[n]`) atıldı ve son maddede "yürütür." sonrası (sitedeki Resmî Gazete çizelgesi, korpustaki
  ekler) kesildi. Her maddenin SHA-256 özeti korpus dosyasınınkiyle karşılaştırıldı. Kısmi dosyalarda yalnız alınan
  maddeler karşılaştırıldı ve kısmi dosyadaki madde gövdesinin kaynak tam metinde birebir geçtiği ayrıca denetlendi.
- **Elle aktarılan kısmi metinler** (KDVK, GVK, 2886, OÖEİKY md. 57): her paragrafın resmî sayfada birebir geçtiği
  denetlendi; KDVK'da fıkra ve bent sırası (md. 17 → "4. Diğer İstisnalar" → d bendi) aynı sayfada doğrulandı.
- **mevzuat.gov.tr dışındaki metinler** (MEB genelgeleri, TKB rehberi, Servis Usul ve Esasları, BSG Yönergesi, EK-2)
  bu turda yeniden indirilmedi; `oab-teyit` alanı kaynak korpustaki son teyidi taşır.
- Not: mevzuat.gov.tr ve resmigazete.gov.tr sertifika zinciri nedeniyle komut satırından doğrudan indirilemiyor;
  teyit tarayıcıyla yapılır.

## 4. Dosyalar

"MG" = 31.10.2026'da mevzuat.gov.tr konsolide metniyle madde madde karşılaştırıldı, fark yok.

| Dosya | Kapsam | Teyit | Programdaki yeri |
|---|---|---|---|
| `meb-okul-aile-birligi-yonetmeligi.md` | tam (32 madde + 4 geçici) | MG; son değişiklik RG 01.12.2023/32386 | her şey; kural paketi v1 `OAB-2023.12` |
| `meb-okul-aile-birligi-yonetmeligi-ek-1-bagis-alindi-belgesi.md` | EK-1 | ek dosyası 25.09.2026; MD5 31.10.2026 | makbuz koçanı envanteri (seri, cilt, sıra) — K5, K9 |
| `meb-okul-aile-birligi-yonetmeligi-ek-2-kantin-kiralama-sozlesmesi.md` | EK-2 | 25.09.2026 | kantin sözleşmesi, arz bedeli ve pay (F5) |
| `okul-aile-birligi-yonetmeligi-degisikligi-genelgesi-2024-35.md` | tam | 25.09.2026 | kantin: yirmi yıl hesabı, pazarlık |
| `ogrenci-kayit-kabullerinde-bagis-alinmamasi-genelgesi-2011-40.md` | tam | 18.08.2026 | kayıt döneminde bağış uyarısı |
| `okul-aile-birlikleri-denetim-rehberi.md` | tam (TKB E.4, 2026-10) | 19.10.2026 | kabul ölçütü; denetim dosyası, Tablo 1-4 |
| `okul-servis-araclari-yonetmeligi.md` | tam | MG (md. 15'te yalnız dipnot imi yeri farklı); son değişiklik RG 19.08.2025/32991 | servis belge takibi (F6) |
| `okul-servisi-calistirma-usul-esaslari.md` | tam + EK-1/2/3 | 17.08.2026 | taşımacının tespiti, sözleşme (F6) |
| `okul-kantinlerinde-gida-ve-hijyen-denetimi-genelgesi-2020-8.md` | tam | 14.09.2026 | kantin denetim komisyonu, belge süreleri |
| `okul-kantinlerine-dair-ozel-hijyen-kurallari-yonetmeligi.md` | tam | MG | kantin belge süreleri |
| `hijyen-egitimi-yonetmeligi.md` | tam | MG | kantin çalışanı hijyen belgesi |
| `tasinir-mal-yonetmeligi.md` | tam | MG | OAB Yön. md. 18/3 taşınır bağı (eski TMY atfının güncel karşılığı, md. 41/2) |
| `devlet-arsiv-hizmetleri-hakkinda-yonetmelik.md` | tam + EK-1…5 | MG (ek formlar karşılaştırılmadı) | saklama; OAB Yön. md. 16/7 ve 23/6'daki 1988 atfı — 1988 yönetmeliği bu yönetmeliğin md. 32'siyle yürürlükten kalktı |
| `resmi-yazismalarda-uygulanacak-usul-ve-esaslar-hakkinda-yonetmelik.md` | tam | MG | yazı biçimi, evrak düzeni |
| `6698-kvkk.md` | tam | MG | KVKK: veri en aza, saklama, aydınlatma |
| `meb-bilgi-ve-sistem-guvenligi-yonergesi.md` | tam | 18.08.2026 | güvenlik çekirdeği, parola, yedek |
| `5510-sosyal-sigortalar-ve-genel-saglik-sigortasi-kanunu.md` | kısmi: md. 11, 12, 86 | MG | birlik işveren sayılır; SGK belgeleri on yıl saklanır (personel, sürüm 2) |
| `4857-is-kanunu.md` | kısmi: md. 2, 17, 53-60, 120 | MG | yıllık izin kaydı, ihbar ve kıdem karşılığı (personel, sürüm 2) |
| `is-sagligi-ve-guvenligi-kanunu-6331.md` | kısmi: md. 2-4 | MG | birlik personel çalıştırırsa işveren yükümlülüğü |
| `ortaogretim-kurumlari-yonetmeligi.md` | kısmi: md. 25, 78, 105, 185, 186 | MG | temsilciler: kontenjan komisyonu (25), ödül ve disiplin kurulu (185-186); müdürün OAB sorumluluğu (78/4-ü); kantin (105) |
| `meb-okul-oncesi-egitim-ve-ilkogretim-kurumlari-yonetmeligi.md` | kısmi: md. 57 | 31.10.2026, doğrudan aktarım | temsilciler: ortaokulda öğrenci davranışlarını değerlendirme kurulu |
| `meb-egitim-kurumlari-sosyal-etkinlikler-yonetmeligi.md` | kısmi: md. 5, 6 | MG | etkinlik gelir-gideri birlikçe yürütülür (5/8); sosyal etkinlikler kurulunda veli (6/1) |
| `meb-rehberlik-ve-psikolojik-danisma-hizmetleri-yonetmeligi.md` | kısmi: md. 16 | MG | temsilciler: RPD yürütme komisyonu (16/2-e) |
| `3065-katma-deger-vergisi-kanunu.md` | kısmi: md. 17/4-d | 31.10.2026, doğrudan aktarım | kantin kirasında KDV hesaplanmaz |
| `193-gelir-vergisi-kanunu.md` | kısmi: md. 89/1-4-5, 94 (bentler) | 31.10.2026, doğrudan aktarım | **yalnız bilgi metni:** bağışçıya vergi indirimi, tevkifat sorumluluğu |
| `2886-devlet-ihale-kanunu.md` | kısmi: md. 51/g, 75, 83, 84 | 31.10.2026, doğrudan aktarım | kantin kiralamasında pazarlık usulü, tahliye, yasaklama (OAB Yön. md. 20/2, 22) |

## 5. Kaynak korpustan alırken yapılan ayıklamalar

Kaynak korpus (yazarın evrak çalışması, `evrakmotoru/mevzuat`, commit `d5b9806`) okulun kendi işleri için tutulur.
Mevzuat metinlerine dokunulmadan yalnız şu korpus notları değiştirildi:

| Dosya | Değişiklik |
|---|---|
| EK-2 | İç iş numarası çıkarıldı; okula özel doldurulmuş sözleşme nüshasına ve üretici betiğe yapılan atıf silindi |
| Genelge 2024/35 | Kaynak PDF'in yerel dosya yolu silindi (indirme adresi `kaynak` alanında) |
| Okul Servis Araçları Yön. | Şoför yaş sınırı geçici düzenlemesinin ilçe yazışma zincirine ve korpustaki dosyasına yapılan atıf, "korpusa alınmadı" notuyla değiştirildi |
| Genelge 2011/40 | "korpustaki" → "kaynak korpustaki" (atıf yapılan denetim rehberleri bu korpusta yok) |

Kısmi dosyalar kaynak tam metinden betikle kesildi; frontmatter'ları yeniden yazıldı, madde gövdeleri birebirdir.

## 6. Alınmayanlar ve bekleyenler

| Metin | Durum |
|---|---|
| KV Sirküleri No. 11, kantin kirası ve iktisadi işletme özelgeleri, gider pusulası ve tevkifat özelgeleri | **Bekliyor** → `bilgi/` (kantin fazı F5'ten önce; gib.gov.tr tam metinleri) |
| Okul servis aracı şoför yaş sınırı geçici düzenlemesi (İçişleri Bakanlığı, 02.01.2026; 31.12.2026'ya kadar) | Alınmadı: süreli düzenleme, kaynak dosya kurum yazışma zinciri içeriyor. F6'da güncel durum yeniden araştırılır |
| 1475 sayılı Kanun md. 14 (kıdem tazminatı) | Personel modülüyle (sürüm 2, F8+) |
| TEFBİS'e ilişkin SGB yazıları (31.12.2010/7729, 11.03.2016/2866395, 02.12.2019/23883563) | Metinleri bulunamadı (ön değerlendirme §2.5); bulunursa `bilgi/` |
| Okul kantini satış listesi (Bilim Kurulu tutanağı), Okul Gıdası Tebliği | Programın kapsamında değil; gerekirse F5'te |
| Genelge 2020/8'de A-1/a ve A-1/b için `<a id>` çapaları | **Bekliyor** (F1c'den önce): metin korpusta var, çapası yok; eklenince kantin denetim komisyonundaki birlik temsilcisine dair iki kural pakete girer (genel tasarım §6.4, denetim MA-7) |
| KVKK Kurulu kararları: VERBİS kayıt istisnası (2018/32, 2018/87, 2023/1154, 2025/1572) ve özel nitelikli veride "yeterli önlemler" (KVKK md. 6/4) | **Bekliyor** → `bilgi/` (kvkk.gov.tr tam metinleri; genel tasarım §3.4, denetim KM-3, KM-9) |
| 01.12.2023 öncesi EK-2 kira sözleşmesi metni | İsteğe bağlı: o tarihten önce imzalanmış kantin sözleşmeleri için (genel tasarım §6.4, DOĞRULANMADI-16) |

## 7. Kaynak korpusta görülen kusurlar (bilgi için)

- Sosyal Etkinlikler Yön.: md. 5/A'nın çapası `madde-5` ile mükerrer (kısmi dosyaya yalnız md. 5 alındı).
- RPD Yön.: md. 16'nın başlığı önceki maddenin son satırına yapışık; kısmi dosyada başlık ayrı satıra alındı.
- Okul Servis Araçları Yön.: md. 15'teki dipnot imi yalın "1" olarak kalmış, dipnot metni md. 17'nin sonuna karışmış
  (madde metinleri resmî metinle aynı).

## 8. Eşitleme

Mevzuat değişince ya da kaynak korpus güncellenince: dosya yeniden alınır, §5'teki ayıklamalar tekrarlanır,
`oab-kaynak` ve `oab-teyit` yenilenir, §3'teki yöntemle resmî metinle karşılaştırılır. Değişen bir madde kural
paketine dayanak oluyorsa yeni kural sürümü açılır; kapanmış dönemlerin hesabı eski sürümle kalır (CLAUDE.md altın
kural 2).
