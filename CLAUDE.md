# CLAUDE.md — OAB Defteri

> Her oturumda otomatik yüklenir. Amaç: projeyi ilk kez gören bir ajanın işi doğru
> okuması ve **kasıtlı kararları kusur sanmaması**. Şu an proje **planlama**
> aşamasındadır; kod yoktur. Ana belgeler:
> [`docs/kesif/2026-10-31-on-degerlendirme.md`](docs/kesif/2026-10-31-on-degerlendirme.md)
> (neden, ne, kararlar) ve [`docs/plan/2026-10-31-f0-f1-plani.md`](docs/plan/2026-10-31-f0-f1-plani.md)
> (ilk iki fazın işleri ve kapıları). F0'da yazılacak genel tasarım belgesi
> (`docs/tasarim/`) gelince ana referans o olur.
>
> Depo dili **Türkçe**: yorumlar, commit mesajları, testler, belgeler ve kullanıcıya
> görünen bütün metinler. Tanımlayıcılar (sınıf, alan, uç adları) İngilizcedir; OYS'den
> gelen model ve API yüzeyi korunur. Tarih `gg.aa.yyyy`, saat dilimi `Europe/Istanbul`.

---

## 1. Altmış saniyede proje

OAB Defteri, okul-aile birliğinin işlerini okulun bilgisayarında yürüten **çevrimdışı
bir masaüstü programıdır** (Windows 10/11 + Pardus 21/23/25). Organlar ve toplantılar,
genel kurul, işlem düzeyinde gelir-gider ve banka mutabakatı, harcama zinciri, bütçe ve
duyurular, denetleme kurulu, kantin ve servis, devir-teslim.

**Konum (bağlayıcı):** program **karar defterinin ve TEFBİS'in yerine geçmez.** Karar
defterine kararlar el ile yazılır ve defter noter tasdiklidir (OAB Yön. md. 13/5, 23/2);
birliğin gelir-gider kayıtlarını TEFBİS'e okul idaresi girer (md. 23/5). Program bunlara
girilecek metni ve listeyi hazırlar, tutarlılığı denetler. Bu cümle arayüzü, kılavuzu,
siteyi ve evrakı kapsar.

**Köken:**
- Masaüstü, paketleme, güvenlik, okul çekirdeği ve ön yüz kiti: **Kütüphane Defteri**
  (`../kutuphane`) — ailenin en güncel iskeleti (PySide6, lisans dizini, saha kabulü).
  Tepsi, ağ kataloğu, Ağ Doktoru, barkod **alınmaz**. Kelebek Sınav (`../kelebek-sinav`)
  ortak atadır.
- İş mantığı: OYS'nin (`../okulapp`) `backend/apps/okul_aile_birligi` modülü (ADR-0028),
  uyarlanarak. OYS bu cihazda bayat olabilir: bakmadan önce `git -C ../okulapp fetch` ve
  `origin/main` teyidi.
- Evrak birikimi ve mevzuat korpusu: `../evrakmotoru` (`mevzuat/*.md`, İŞ 12 OAB seti,
  İŞ 4 servis, İŞ 5 kantin). **O depodan kişisel veri içeren dosya (`_kaynak/`, gerçek
  adlı belgeler) buraya taşınmaz;** yalnız kamuya açık mevzuat ve şablon mantığı.
- AYNEN / UYARLA / ALMA haritası F0'daki genel tasarımda yazılır; haritaya uymayan
  "iyileştirme" yapılmaz.

## 2. Altın kurallar

1. **Mevzuat doğruluğu.** Programın koyduğu her kural (oran, süre, yeter sayı, sınır)
   madde numarasıyla `docs/mevzuat/` kanonik metnine dayanır. Doğrulanamayan hüküm koda,
   arayüze ve evraka girmez; kullanıcıya sorulur. `(Mülga:…)` hüküm yoktur; `(Değişik:…)`
   en güncel hâli esastır. **Özelge ve sirküler mevzuat değildir** — vergi konularında
   yalnız bilgi/uyarı metni olur, hüküm diye basılmaz.
2. **Kural paketi.** Oranlar, süreler, çarpanlar ve sınırlar kodda sabit değil, sürümlü
   kural dosyasındadır; her birlik dönemi kendi kural sürümüyle hesaplanır.
3. **Uyarı + gerekçe, sert engel değil** (OYS kullanıcı kararı 4): program doğrusunu
   gösterir, sapma gerekçesiyle kayda geçer. Sert engel yalnız hesap bütünlüğünde
   (toplamlar, numara tekilliği, kapanmış dönem, yeter sayı hesabı).
4. **Kayıt silinmez, ters kayıtla düzeltilir;** kapanan dönem kilitlenir; her değişiklik
   denetim izine yazılır.
5. **KVKK.** T.C. kimlik numarası varsayılan kapalı (K9); veli verisi en aza; duyuru ve
   ilan çıktılarında kişi adı yok; gerçek veri, banka özeti, TEFBİS çıktısı, e-Okul
   listesi depoya girmez (`.gitignore` önler, sızıntı denetimi F1'de kapıya girer).
6. **Terimler Yönetmeliğinkidir:** "Denetleme Kurulu" (Denetim Kurulu değil), "muhasip",
   "birlik", "genel kurul", "tahmini bütçe". Servis evrakında "ihale/teklif/eksiltme"
   yazılmaz — "taşımacının tespiti" (İŞ 4 dersi). Okul müdürü yönetim kurulu üyesi
   değildir, kurula başkanlık etmez.
7. **Test ve lint yalnız Docker'da** (aile kuralı); faz, kod kapısı geçilmeden kapanmaz.
8. **Yayın işleri** (GitHub deposu, etiket, push, site, indirme alanı) dışa açıktır,
   kullanıcı onaylı adımlardır.

## 3. Kararlar (31.10.2026, ön değerlendirme §9)

| # | Karar |
|---|---|
| K1 | Gelir-gider **işlem düzeyinde** (banka hareketiyle eşlenir) |
| K2 | Okulda **tek bilgisayar**, rol bazlı yerel hesaplar (MY, başkan, muhasip, sekreter; DK ve müdür salt okur) |
| K3 | Bordro **yok**; personel için özlük, yıllık izin kaydı, kıdem karşılığı (sürüm 2) |
| K4 | **Kantin ve servis ilk sürümde** (birliğin ve okulun evrakı ve takibi; komisyon kararının yerine geçmez) |
| K5 | Makbuz **basılmaz**; ciltli koçan envanteri ve yaprak kaydı |
| K6 | TEFBİS: giriş listesi + Excel çıktısıyla mutabakat; **otomatik giriş yok** (öneri; sorulmadı) |
| K7 | Lisans **PolyForm Noncommercial 1.0.0**; kamuya "kaynağı açık" diye tanıtılır |
| K8 | Ad **OAB Defteri**; site `okulapp.org/oab-defteri` |
| K9 | Bağışçının T.C. kimlik no'su **varsayılan kapalı**, ayardan açılır (şifreli, maskeli) |

Açık: birlik personelinin doğrudan mı firma üzerinden mi çalıştığı (K3'ün kapsamını belirler).

## 4. Faz durumu

| Faz | Durum |
|---|---|
| F0 Keşif tamamlama + genel tasarım + mevzuat | başlamadı |
| F1 İskelet + çekirdek + organlar + kural paketi | başlamadı |

Sapmalar ve tasarımda yazmayan kararlar faz bittikçe "F<n> ekleri (tarih)" satırıyla
plan/tasarım belgesine işlenir.
