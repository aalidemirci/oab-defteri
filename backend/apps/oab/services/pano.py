"""Genel Bakış'ın pano kalemleri (tasarım §7.10 "Pano ve takvim"; plan F1c 12. adım "pano kabuğu").

KAYNAKLAR: kalemler SAKLANMAZ; her okumada (açılış, gün değişimi, ilgili kayıt yazıldıktan sonraki okuma)
kaynak kayıtlardan hesaplanır (tek kaynak, O6). Hesap okuma işidir: veritabanına hiçbir şey yazmaz,
kilitliyken de yazmaz (§4.6.3; uç kilitliyken 423 döner, hesap hiç koşmaz). Kalem gerekçe istemez:
vadesi geçen kuralın gerekçesi kendi akışındaki kapatıcı geçişte istenir (O3), kalem kayıt kapanınca
kendiliğinden düşer.

KİŞİSİZ: kalemde kişi adı, kişi ya da üyelik kimliği yoktur; yalnız kod, gün, kural paketinin kişisiz
iletisi, madde atfı ve götürdüğü ekran (rota + sekme). Kişi ancak kalemin götürdüğü ekranda, rolün okuma
yetkisi içinde görünür (§7.10; ailenin "bildirimde kişi adı yok" ilkesi, §12.A). Kullanıcı metni
(başlık, açıklama) ön yüzün sözlüğe bağlı metinleridir (`modules/pano/metinler.ts`); burada yalnız kural
paketinin iletisi döner.

F1c KALEMLERİ (§7.10 "Fazlar": pano kabuğu; F2-F6 kaynakları kalem üretmez, yer tutucu da çıkmaz):

* `YK_GOREV_BOLUMU` — yönetim kurulunun görev bölümü süresi (md. 12/3; `yonetim_kurulu.gorev_bolumu_gun`):
  kurulun bugünkü bileşimi oluştuktan sonra görev bölümü yapılmadıysa son gün başlangıç + kural değeri;
* `DK_GOREV_BOLUMU` — Denetleme Kurulunun görev bölümü (md. 14/1; `denetleme_kurulu.gorev_bolumu_gun`);
  başlangıç kurulu seçen genel kuruldur (`gorev_bolumu.dk_secen_genel_kurul_gunu`). İki kalemde de
  başlangıç ve "yapıldı mı" yazmadaki süre denetimiyle aynı kaynaktır
  (`gorev_bolumu.bekleyen_sure_baslangici`). Başlangıç programa başlama gününden önceyse kurul
  programdan önce oluşmuştur (devralınan kurul): geçmiş geriye dönük işletilmez (§7.9 "Ne olmaz"),
  kalem çıkmaz;
* `GECIS_ADIMI` — geçiş kurulumunun açık adımları (`gecis.yol_haritasi_durumu`; §7.9, §7.10);
* `YEDEK_CAGRISI` — yönetim kurulunda görevdeki asıl sayısı kural paketindeki asıl üye sayısının altında
  ve çağrılmamış yedek varken (md. 13/6; ileti `yonetim_kurulu.asil_uye`'nin), Denetleme Kurulunda
  öğretmen üyenin başka kurumdaki görevlendirmesi kural süresini aştıysa
  (`uyelik_gecisleri.oneriler`, `denetleme_kurulu.ogretmen_gorevlendirme_ay`); aynı ileti ve atfı
  taşıyan öneriler tek kalemdir, `ek.sayi` kaç üyede olduğunu söyler (kişisiz sayım, §7.10);
* `KADRO` — kadro okumasının uyarı ve eksikleri (`uyelikler.kadro_uyarilari`: kadro sayıları, görev
  süresi, başkan eksiği); yedek çağrısı önerisine dönen asıl sayısı iletisi ayrıca yazılmaz;
* `HESAP_ONERISI` — program yöneticisinin hesap önerileri (`hesap_baglari.hesap_onerileri`; kişisiz
  kodlar: öneri türü, rol, neden; hesap ve üyelik kimliği dönmez); aynı tür, rol ve nedenli öneriler
  tek kalemdir, `ek.sayi` kaç öneri olduğunu söyler (ör. Denetleme Kurulunun üç asılına hesap
  açılmadıysa tek kalem, `sayi` 3; ilk görülme sırası korunur);
* `YARIM_TASLAK` — oturumdaki hesabın yarım kalan gerekçe metni (§7 "Yarım kalan metin"): yalnız kutunun
  bağlamı (metin okunmaz, şifresi çözülmez); bilinmeyen bağlam kalem üretmez (götüreceği ekran yok);
* `tamamlanacaklar` — açık dönemin açık `ComplianceItem(EKSIK)` satırları (O3), rolün görünümüyle
  (`uyum.uyum_satiri_gorunumu`: görev alma engelinin kimliğini ve atfını yalnız program yöneticisi ve
  yönetim kurulu rolleri görür; kullanıcı kararı 10.11.2026);
* `bilgiler` — kural kopyası doğrulanamayan dönem (D7: kurallı kalemler çıkmaz, uç 503 vermez) ve açık
  birlik dönemi olmaması (hiç açılmadı ya da son dönem iptal edildi).

ROL BAŞINA GÖRÜNÜM (§7.10 tablosu ve §4.4.2; `KALEM_ROLLERI`): program yöneticisi bütün listeyi görür;
sekreter yönetim kurulunun görev bölümü süresini, yedek çağrısı önerisini ve kadrosunu; başkan ve başkan
yardımcısı yönetim kurulunun görev bölümü süresini; Denetleme Kurulu kendi görev bölümü süresini ve
kadrosunu. Geçiş adımları, hesap önerileri ve Denetleme Kurulunun yedek çağrısı (yedeği program yöneticisi
çağırır, md. 14/6) yalnız program yöneticisinindir. Tamamlanacaklar, bilgiler ve kendi yarım taslağı her
roldedir (M2 ve M1'i her rol okur; Organlar ekranının kadro okuması aynı satırları aynı süzmeyle verir).
Veli rollerinde (başkan, başkan yardımcısı, muhasip, sekreter) varsayılan görünüm "bu ay sizden
beklenenler"dir (`gorunum: "ay"`), ötekilerde "bu hafta yapılacaklar" (`"hafta"`); ön yüz rol adıyla
dallanmaz, görünümü buradan okur.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any, Final

from django.utils import timezone

from apps.oab import selectors
from apps.oab.kurallar import (
    BilinmeyenKural,
    KuralPaketiKullanilamaz,
    YururlukteDegerYok,
    kural,
    kural_kaydi,
)
from apps.oab.kurallar.erisim import atif_metni
from apps.oab.kurallar.erisim import denetle as paket_denetle
from apps.oab.models import (
    BoardMeeting,
    ComplianceItem,
    ComplianceKind,
    DraftText,
    OabPerson,
    OabTerm,
    OfficialBook,
    OrganMembership,
    OrganType,
    SeatType,
    TermStatus,
)
from apps.oab.services import (
    donem_kilidi,
    gecis,
    gorev_bolumu,
    hesap_baglari,
    uyelik_gecisleri,
    uyelikler,
    uyum,
)
from apps.okul import denetim_izi, rol_izinleri
from apps.okul.models import AccountRole

# ---------------------------------------------------------------------------
# Kalem kodları ve rolleri (modül başlığı "Rol başına görünüm")
# ---------------------------------------------------------------------------
YK_GOREV_BOLUMU: Final = "YK_GOREV_BOLUMU"
DK_GOREV_BOLUMU: Final = "DK_GOREV_BOLUMU"
GECIS_ADIMI: Final = "GECIS_ADIMI"
YEDEK_CAGRISI_YK: Final = "YEDEK_CAGRISI_YK"
YEDEK_CAGRISI_DK: Final = "YEDEK_CAGRISI_DK"
KADRO_YK: Final = "KADRO_YK"
KADRO_DK: Final = "KADRO_DK"
HESAP_ONERISI: Final = "HESAP_ONERISI"
YARIM_TASLAK: Final = "YARIM_TASLAK"
#: Yanıttaki kod (iki kurulun yedek çağrısı ve kadrosu aynı başlıkla, `ek.organ` ile ayrılır).
_YANIT_KODU: Final[dict[str, str]] = {
    YEDEK_CAGRISI_YK: "YEDEK_CAGRISI",
    YEDEK_CAGRISI_DK: "YEDEK_CAGRISI",
    KADRO_YK: "KADRO",
    KADRO_DK: "KADRO",
}
#: Tamamlanacak satırının kodu (O3 "eksik").
EKSIK: Final = "EKSIK"
#: Bilgi kodları.
KURAL_KOPYASI_DOGRULANAMADI: Final = "KURAL_KOPYASI_DOGRULANAMADI"
DONEM_YOK: Final = "DONEM_YOK"

_YONETICI: Final = rol_izinleri.YONETICI
_SEKRETER: Final = AccountRole.SEKRETER.value
_BASKAN: Final = AccountRole.BASKAN.value
_BASKAN_YARDIMCISI: Final = AccountRole.BASKAN_YARDIMCISI.value
_DK: Final = rol_izinleri.DENETLEME_KURULU

#: Kalemi gören roller (tasarım §7.10 "Rol başına görünüm"; program yöneticisi "bütün liste").
KALEM_ROLLERI: Final[dict[str, frozenset[str]]] = {
    YK_GOREV_BOLUMU: frozenset({_YONETICI, _BASKAN, _BASKAN_YARDIMCISI, _SEKRETER}),
    DK_GOREV_BOLUMU: frozenset({_YONETICI, _DK}),
    GECIS_ADIMI: frozenset({_YONETICI}),
    YEDEK_CAGRISI_YK: frozenset({_YONETICI, _SEKRETER}),
    YEDEK_CAGRISI_DK: frozenset({_YONETICI}),
    KADRO_YK: frozenset({_YONETICI, _SEKRETER}),
    KADRO_DK: frozenset({_YONETICI, _DK}),
    HESAP_ONERISI: frozenset({_YONETICI}),
}
#: Varsayılan görünümü "bu ay sizden beklenenler" olan veli rolleri (§7.10 "Teslim yolu").
AYLIK_GORUNUM_ROLLERI: Final = rol_izinleri.YK_ROLLERI

#: Yarım metin kutusunun bağlamı → götürdüğü ekran (rota, sekme). Bağlamlar ön yüzün kutularıdır
#: (`useUyariGerekce(baglam)`; F1c 11. adım); bu listede olmayan bağlam kalem üretmez. Yedek çağrısı
#: ve düşme pencereleri iki kurulda da açıldığı için bağlamları kurulludur (`.yk` / `.dk`): kalem
#: taslağın yazıldığı kurulun sekmesine götürür.
TASLAK_EKRANLARI: Final[dict[str, tuple[str, str]]] = {
    "gecis.devralinan": ("/birlik-donemi/gecis-kurulumu", ""),
    "gecis.karar_defteri": ("/birlik-donemi/gecis-kurulumu", ""),
    "gecis.sayac_beyani": ("/birlik-donemi/gecis-kurulumu", ""),
    "organlar.yk_gorev_bolumu": ("/organlar", "yk"),
    "organlar.yedek_cagrisi.yk": ("/organlar", "yk"),
    "organlar.yedek_cagrisi.dk": ("/organlar", "dk"),
    "organlar.dusme.yk": ("/organlar", "yk"),
    "organlar.dusme.dk": ("/organlar", "dk"),
    "organlar.dk_gorev_bolumu": ("/organlar", "dk"),
    "organlar.ogretmen_uye": ("/organlar", "dk"),
    "temsilciler.temsilci": ("/temsilciler", ""),
}

#: Kurulun Organlar sekmesi.
_ORGAN_SEKMESI: Final[dict[str, str]] = {
    OrganType.YONETIM_KURULU.value: "yk",
    OrganType.DENETLEME_KURULU.value: "dk",
    OrganType.ALIM_KOMISYONU.value: "alim",
}
_ORGANLAR: Final = "/organlar"
_TEMSILCILER: Final = "/temsilciler"
_BIRLIK_DONEMI: Final = "/birlik-donemi"
_GECIS_KURULUMU: Final = "/birlik-donemi/gecis-kurulumu"
_KULLANICILAR: Final = "/kullanicilar"

#: Paket ya da dönem kopyası okunamayınca kurallı kalem çıkmaz (D1, D7); okuma açık kalır.
_KURAL_OKUNAMADI: Final = (KuralPaketiKullanilamaz, YururlukteDegerYok, BilinmeyenKural)


def bugun() -> date:
    """Kalemlerin günü (Europe/Istanbul); testler gün değişimini bununla sabitler."""
    return timezone.localdate()


def _kalem(
    kod: str,
    *,
    rota: str,
    sekme: str = "",
    vade: date | None = None,
    gun: date | None = None,
    metin: str = "",
    atif: str = "",
    **ek: Any,
) -> dict[str, Any]:
    return {
        "kod": _YANIT_KODU.get(kod, kod),
        "vade": None if vade is None else vade.isoformat(),
        "gecikti": vade is not None and gun is not None and gun > vade,
        "rota": rota,
        "sekme": sekme,
        "metin": metin,
        "atif": atif,
        "ek": ek,
    }


# ---------------------------------------------------------------------------
# Kurallı kalemler (kural paketinden; D7'de çıkmaz)
# ---------------------------------------------------------------------------
_SURE_KURALLARI: Final[dict[str, tuple[str, str]]] = {
    OrganType.YONETIM_KURULU.value: (YK_GOREV_BOLUMU, "yonetim_kurulu.gorev_bolumu_gun"),
    OrganType.DENETLEME_KURULU.value: (DK_GOREV_BOLUMU, "denetleme_kurulu.gorev_bolumu_gun"),
}


def _gorev_bolumu_kalemi(donem: OabTerm, organ: str, gun: date) -> dict[str, Any] | None:
    """Görev bölümü süresi (modül başlığı): son gün = başlangıç + kural değeri (gün; yorum KE-12)."""
    kod, kural_id = _SURE_KURALLARI[organ]
    baslangic = gorev_bolumu.bekleyen_sure_baslangici(donem, organ, gun)
    program_basi = donem.program_start_date or donem.start_date
    if baslangic is None or (program_basi is not None and baslangic < program_basi):
        return None
    kayit = kural_kaydi(kural_id, tarih=baslangic, donem=donem)
    vade = baslangic + timedelta(days=int(kayit["deger"]))
    return _kalem(
        kod,
        rota=_ORGANLAR,
        sekme=_ORGAN_SEKMESI[organ],
        vade=vade,
        gun=gun,
        atif=atif_metni(kayit),
    )


def _yk_yedek_ve_kadro(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Yönetim kurulunun yedek çağrısı önerisi ve kadro kalemleri (modül başlığı)."""
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    organ = OrganType.YONETIM_KURULU.value
    sayilar = selectors.kadro_sayilari(donem, organ)
    yedek_iletisi = ""
    if sayilar[SeatType.ASIL] < int(
        kural("yonetim_kurulu.asil_uye", gun, donem)
    ) and selectors.bekleyen_yedekler(donem, organ):
        sonuc = paket_denetle(
            "yonetim_kurulu.asil_uye", sayilar[SeatType.ASIL], tarih=gun, donem=donem
        )
        if sonuc["durum"] == "uyari":
            yedek_iletisi = sonuc["mesaj"]
            cagri = kural_kaydi("yonetim_kurulu.yedek_cagirma", tarih=gun, donem=donem)
            sonuclar.append(
                (
                    YEDEK_CAGRISI_YK,
                    _kalem(
                        YEDEK_CAGRISI_YK,
                        rota=_ORGANLAR,
                        sekme="yk",
                        metin=yedek_iletisi,
                        atif=atif_metni(cagri),
                        organ=organ,
                    ),
                )
            )
    for sonuc in uyelikler.kadro_uyarilari(donem, organ, tarih=gun):
        if sonuc["mesaj"] == yedek_iletisi:
            continue
        sonuclar.append(
            (
                KADRO_YK,
                _kalem(
                    KADRO_YK,
                    rota=_ORGANLAR,
                    sekme="yk",
                    metin=sonuc["mesaj"],
                    atif=sonuc["atif"],
                    organ=organ,
                    durum=sonuc["durum"],
                ),
            )
        )
    return sonuclar


def _dk_yedek_cagrilari(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Denetleme Kurulunun yedek çağrısı önerisi: öğretmen üyenin görevlendirmesi kural süresini aştı.
    Aynı ileti ve atıf tek kalemdir; `sayi` kaç üyede olduğudur (kişisiz; ilk görülme sırası)."""
    organ = OrganType.DENETLEME_KURULU.value
    gruplar: dict[tuple[str, str], int] = {}
    for uyelik in selectors.gorevdeki_asillar(donem, organ):
        sonuc = uyelik_gecisleri.gorevlendirme_denetimi(uyelik)
        if sonuc is not None:
            anahtar = (str(sonuc["mesaj"]), str(sonuc["atif"]))
            gruplar[anahtar] = gruplar.get(anahtar, 0) + 1
    return [
        (
            YEDEK_CAGRISI_DK,
            _kalem(
                YEDEK_CAGRISI_DK,
                rota=_ORGANLAR,
                sekme="dk",
                metin=metin,
                atif=atif,
                organ=organ,
                sayi=sayi,
            ),
        )
        for (metin, atif), sayi in gruplar.items()
    ]


def _dk_kadro(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Denetleme Kurulunun kadro kalemleri."""
    organ = OrganType.DENETLEME_KURULU.value
    return [
        (
            KADRO_DK,
            _kalem(
                KADRO_DK,
                rota=_ORGANLAR,
                sekme="dk",
                metin=sonuc["mesaj"],
                atif=sonuc["atif"],
                organ=organ,
                durum=sonuc["durum"],
            ),
        )
        for sonuc in uyelikler.kadro_uyarilari(donem, organ, tarih=gun)
    ]


def _gorev_bolumu_kalemleri(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for organ, (kod, _) in _SURE_KURALLARI.items():
        kalem = _gorev_bolumu_kalemi(donem, organ, gun)
        if kalem is not None:
            sonuclar.append((kod, kalem))
    return sonuclar


def _kuralli_kalemler(donem: OabTerm, gun: date) -> list[tuple[str, dict[str, Any]]]:
    """Kural paketinden okunan kalemler. Her kaynak ayrı okunur: paket ya da dönem kopyası okunamazsa
    (D1, D7) ya da kuralın olay gününde yürürlükte değeri yoksa o kaynağın kalemi çıkmaz; öteki
    kaynaklar ve kuralsız kalemler çalışır (okuma açık kalır, uç 503 vermez)."""
    sonuclar: list[tuple[str, dict[str, Any]]] = []
    for kaynak in (_gorev_bolumu_kalemleri, _yk_yedek_ve_kadro, _dk_yedek_cagrilari, _dk_kadro):
        try:
            sonuclar.extend(kaynak(donem, gun))
        except _KURAL_OKUNAMADI:
            continue
    return sonuclar


# ---------------------------------------------------------------------------
# Kuralsız kalemler
# ---------------------------------------------------------------------------
def _gecis_kalemleri() -> list[dict[str, Any]]:
    """Geçiş kurulumunun açık adımları (sırasıyla; kişisiz adım anahtarları)."""
    durum = gecis.yol_haritasi_durumu()
    return [_kalem(GECIS_ADIMI, rota=_GECIS_KURULUMU, adim=adim) for adim in durum["open_steps"]]


def _hesap_kalemleri() -> list[dict[str, Any]]:
    """Program yöneticisinin hesap önerileri: yalnız tür, rol, neden ve sayı (kimlik dönmez). Aynı tür,
    rol ve nedenli öneriler tek kalemdir (ilk görülme sırası; aynı adlı bağlantılar yinelenmez)."""
    gruplar: dict[tuple[str, str, str], int] = {}
    for oneri in hesap_baglari.hesap_onerileri():
        anahtar = (str(oneri["tur"]), str(oneri["rol"]), str(oneri.get("neden", "")))
        gruplar[anahtar] = gruplar.get(anahtar, 0) + 1
    return [
        _kalem(HESAP_ONERISI, rota=_KULLANICILAR, tur=tur, rol=rol, neden=neden, sayi=sayi)
        for (tur, rol, neden), sayi in gruplar.items()
    ]


def _taslak_kalemi(hesap_id: str | None) -> dict[str, Any] | None:
    """Oturumdaki hesabın yarım metni: yalnız bağlam okunur (şifreli metin çözülmez)."""
    if hesap_id is None:
        return None
    baglam = DraftText.objects.filter(account_id=hesap_id).values_list("context", flat=True).first()
    if baglam is None or baglam not in TASLAK_EKRANLARI:
        return None
    rota, sekme = TASLAK_EKRANLARI[baglam]
    return _kalem(YARIM_TASLAK, rota=rota, sekme=sekme, baglam=baglam)


# ---------------------------------------------------------------------------
# Tamamlanacaklar (ComplianceItem EKSIK)
# ---------------------------------------------------------------------------
def _sayilar(kimlikler: Iterable[str]) -> list[int]:
    return [int(k) for k in kimlikler if k.isdigit()]


def _konu_organlari(satirlar: list[ComplianceItem]) -> dict[str, dict[str, str]]:
    """Üyelik ve toplantı konulu satırların kurulu (kimlik → organ; ekranın sekmesi için)."""
    uyelik = denetim_izi.model_etiketi(OrganMembership)
    toplanti = denetim_izi.model_etiketi(BoardMeeting)
    uyelikler_ = OrganMembership.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == uyelik)
    ).values_list("pk", "organ")
    toplantilar = BoardMeeting.objects.filter(
        pk__in=_sayilar(s.subject_id for s in satirlar if s.subject_type == toplanti)
    ).values_list("pk", "organ")
    return {
        uyelik: {str(pk): str(organ) for pk, organ in uyelikler_},
        toplanti: {str(pk): str(organ) for pk, organ in toplantilar},
    }


def _eksik_ekrani(satir: ComplianceItem, organlar: dict[str, dict[str, str]]) -> tuple[str, str]:
    """Satırın götürdüğü ekran: konusunun ekranı (organ sekmesi, temsilciler, kişiler, geçiş)."""
    if satir.rule_id.startswith("temsilci."):
        return _TEMSILCILER, ""
    organ = organlar.get(satir.subject_type, {}).get(satir.subject_id)
    if organ is not None:
        if organ == OrganType.TEMSILCI:
            return _TEMSILCILER, ""
        return _ORGANLAR, _ORGAN_SEKMESI.get(organ, "")
    if satir.subject_type == denetim_izi.model_etiketi(OabPerson):
        return "/kisiler", "birlik"
    if satir.subject_type == denetim_izi.model_etiketi(OfficialBook):
        return _GECIS_KURULUMU, ""
    return _BIRLIK_DONEMI, ""


def _uyum_atfi(kural_id: str, donem: OabTerm, gun: date) -> str:
    try:
        return atif_metni(kural_kaydi(kural_id, tarih=gun, donem=donem))
    except _KURAL_OKUNAMADI:
        return ""


def _tamamlanacaklar(donem: OabTerm, rol: str | None, gun: date) -> list[dict[str, Any]]:
    satirlar = list(
        ComplianceItem.objects.filter(
            term=donem, kind=ComplianceKind.EKSIK, resolved_at__isnull=True
        ).order_by("pk")
    )
    organlar = _konu_organlari(satirlar)
    sonuc: list[dict[str, Any]] = []
    for satir in satirlar:
        gorunum = uyum.uyum_satiri_gorunumu(satir, rol)
        rota, sekme = _eksik_ekrani(satir, organlar)
        sonuc.append(
            _kalem(
                EKSIK,
                rota=rota,
                sekme=sekme,
                metin=str(gorunum["message"]),
                atif=_uyum_atfi(str(gorunum["rule_id"]), donem, gun),
            )
        )
    return sonuc


# ---------------------------------------------------------------------------
# Bilgiler ve toplu okuma
# ---------------------------------------------------------------------------
def _acik_donem() -> OabTerm | None:
    donem: OabTerm | None = (
        OabTerm.objects.select_related("rule_package").filter(status=TermStatus.ACIK).first()
    )
    return donem


def _bilgiler(donem: OabTerm | None) -> list[dict[str, Any]]:
    if donem is None:
        son = OabTerm.objects.order_by("-pk").values_list("status", flat=True).first()
        return [
            _kalem(
                DONEM_YOK,
                rota=_BIRLIK_DONEMI,
                son_durum=str(son) if son == TermStatus.IPTAL else "",
            )
        ]
    if not donem_kilidi.kural_kopyasi_tutuyor(donem):
        return [_kalem(KURAL_KOPYASI_DOGRULANAMADI, rota=_BIRLIK_DONEMI)]
    return []


def kalemler(rol: str | None, hesap_id: str | None, *, gun: date | None = None) -> dict[str, Any]:
    """Oturumdaki rolün pano kalemleri (modül başlığı). Yazmaz; rolü bilinmeyen oturum yalnız rol
    süzmesi gerekmeyen kalemleri (bilgiler, tamamlanacaklar, kendi taslağı) görür.

    Dönüş: `{bugun, gorunum, bilgiler, isler, tamamlanacaklar}`. `isler` vadeli kalemler önde (son güne
    göre), vadesizler ardından; tamamlanacaklar satır sırasıyla.
    """
    gun = gun or bugun()
    donem = _acik_donem()
    adaylar: list[tuple[str, dict[str, Any]]] = []
    if donem is not None:
        adaylar.extend(_kuralli_kalemler(donem, gun))
    if rol == _YONETICI:
        adaylar.extend((GECIS_ADIMI, k) for k in _gecis_kalemleri())
        adaylar.extend((HESAP_ONERISI, k) for k in _hesap_kalemleri())
    isler = [k for kod, k in adaylar if rol is not None and rol in KALEM_ROLLERI[kod]]
    taslak = _taslak_kalemi(hesap_id)
    if taslak is not None:
        isler.append(taslak)
    isler.sort(key=lambda k: (k["vade"] is None, k["vade"] or ""))
    return {
        "bugun": gun.isoformat(),
        "gorunum": "ay" if rol in AYLIK_GORUNUM_ROLLERI else "hafta",
        "bilgiler": _bilgiler(donem),
        "isler": isler,
        "tamamlanacaklar": [] if donem is None else _tamamlanacaklar(donem, rol, gun),
    }
