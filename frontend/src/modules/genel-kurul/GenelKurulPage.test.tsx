// Genel Kurul ekranı (plan F2 §6.1; 11b): liste ve boş durum, planlama (yalnız `genel_kurul_yazma`;
// kural sürümü güncellenmeliyse önce Birlik Dönemi'ne götürür — U1), sihirbazın adım geçişleri (durumdan
// süren adım, tamamlanmış adıma dönüş), rol başına görünen ve gizlenen yazma denetimleri (program
// yöneticisi ve sekreter yazar; Denetleme Kurulu ve okul müdürü okur), çağrı penceresinin sunucudan gelen
// seçenekleri (olağanüstüde neden ve gündem; Denetleme Kurulunun yolunda md. 6 işareti zorunlu ve rapor
// aynı istekte), uyarı + gerekçe akışı, ilan, toplantının sayıları, katılım işaretleri (yalnız
// `kisisel_veri_ciktisi`), tutanak, dönem geçişinin onayı (yalnız `donem_gecisi_onayi`; U32), iptal,
// dosya ekleri, belge kartları (üretim sunucunun listesine göre; veli adlı çıktı yalnız program
// yöneticisinde, saklanmaz) ve E12'nin evrak kaydı önerisi. 11b denetiminden: rol kapılarının iki yönü
// (müdürün kendi çağrısındaki toplantı bilgisi, E12'nin evrak kaydı, çağrı yazısının bağı), sihirbazın
// pencerelerinin gövdeleri (toplantı bilgisi, gündem sırası, katılım düzeltmesi, divan ve düzeltmesi,
// gündeme ekleme ve çıkarma, ibra, aday, seçim, tutanağın bilgileri) ve hata yolları (okuma hatası,
// pencerede sert engel ve öteki ret, belge kartında uyum hatası ile sayfa hatası). Veriler UYDURMADIR.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { YETENEK_ADLARI } from "../oturum/api";
import type { YetenekAdi } from "../oturum/api";
import { SALT_OKUR_ILETISI } from "../oturum/RolKapisi";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import type { GenelKurul, GenelKurulListesi, GundemMaddesi, Katalog, KatalogSatiri } from "./api";
import type { EvrakKaydi } from "../gelen-giden-evrak/api";

const gkMock = vi.hoisted(() => ({
  liste: vi.fn(),
  planla: vi.fn(),
  ayrinti: vi.fn(),
  toplantiBilgisi: vi.fn(),
  cagir: vi.fn(),
  mudurCagrisi: vi.fn(),
  dkCagrisi: vi.fn(),
  cagriYazisi: vi.fn(),
  ilan: vi.fn(),
  ikinciIlan: vi.fn(),
  kanit: vi.fn(),
  ilanEki: vi.fn(),
  birinciToplanti: vi.fn(),
  ikinciToplanti: vi.fn(),
  iptalEt: vi.fn(),
  katilimDuzelt: vi.fn(),
  katilimIsaretleri: vi.fn(),
  isaretle: vi.fn(),
  gundemeEkle: vi.fn(),
  gundemSirasi: vi.fn(),
  gundemdenCikar: vi.fn(),
  kararSonucu: vi.fn(),
  secim: vi.fn(),
  secimIptal: vi.fn(),
  ibra: vi.fn(),
  dosyaEki: vi.fn(),
  ekIndir: vi.fn(),
  divan: vi.fn(),
  divanIptal: vi.fn(),
  aday: vi.fn(),
  tutanak: vi.fn(),
  tutanagiTamamla: vi.fn(),
  donemGecisi: vi.fn(),
  donemGecisiniOnayla: vi.fn(),
  katalog: vi.fn(),
  evrakListesi: vi.fn(),
  evrakUret: vi.fn(),
  dkCagriYazisi: vi.fn(),
  adliEvrak: vi.fn(),
  evrakDosyasi: vi.fn(),
}));
vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  genelKurulApi: gkMock,
}));

const gelenGidenMock = vi.hoisted(() => ({
  kayitlar: vi.fn(),
  gidenOnerisi: vi.fn(),
  gidenKaydet: vi.fn(),
}));
vi.mock("../gelen-giden-evrak/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../gelen-giden-evrak/api")>()),
  gelenGidenApi: gelenGidenMock,
}));

const kisiApiMock = vi.hoisted(() => ({ liste: vi.fn() }));
vi.mock("../kisiler/birlikKisileriApi", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../kisiler/birlikKisileriApi")>()),
  birlikKisileriApi: kisiApiMock,
}));

const yarimMetinMock = vi.hoisted(() => ({ oku: vi.fn(), kaydet: vi.fn(), temizle: vi.fn() }));
vi.mock("../uyum/api", () => ({ yarimMetinApi: yarimMetinMock }));

const indirmeMock = vi.hoisted(() => ({ saveBlob: vi.fn() }));
vi.mock("../../lib/download", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/download")>()),
  saveBlob: indirmeMock.saveBlob,
}));

import GenelKurulPage from "./GenelKurulPage";
import {
  ADAY_PENCERESI_BASLIGI,
  ADLI_CIKTI_KAYDEDILDI,
  CAGRI_NEDENI_GEREKLI,
  CAGRI_YAZISI_BASLIGI,
  DIVAN_IPTAL_BASLIGI,
  DIVAN_YOK,
  DONEM_GECISI_OKUNAMADI,
  DUGME_ADAY,
  DUGME_ADLI_EXCEL,
  DUGME_ADLI_WORD,
  DUGME_CAGRI_YAZISI,
  DUGME_DIVAN_IPTAL,
  DUGME_GUNDEM_EKLE,
  DUGME_GUNDEM_SIRASI,
  DUGME_GUNDEMDEN_CIKAR,
  DUGME_IBRA,
  DUGME_KATILIM_DUZELTMESI,
  DUGME_SECIM,
  DUGME_TUTANAK_BILGILERI,
  DUZELTME_GEREKCESI_YAZIN,
  GENEL_KURULLAR_OKUNAMADI,
  GENEL_KURUL_OKUNAMADI,
  GUNDEMDEN_CIKAR_BASLIGI,
  GUNDEM_EKLE_BASLIGI,
  GUNDEM_SIRASI_BASLIGI,
  IBRA_PENCERESI_BASLIGI,
  IPTAL_EDILDI_NOTU,
  KATALOG_OKUNAMADI,
  KATILIM_DUZELTMESI_BASLIGI,
  KISI_SECIN,
  KURAL_SURUMU_GUNCELLENMELI_BASVURUN,
  MADDE_BASLIGI_GEREKLI,
  OYLAR_BIRLIKTE,
  SAYI_GECERSIZ,
  SECIM_PENCERESI_BASLIGI,
  TOPLANTI_BILGISI_BASLIGI,
  TUTANAK_BILGILERI_BASLIGI,
  YENI_DEGER_GEREKLI,
  DIVAN_PENCERESI_BASLIGI,
  DK_CAGRI_GENEL_KURUL_YOK,
  DONEM_GECISI_ONAY_BASLIGI,
  DUGME_ADLI_PDF,
  DUGME_BIRINCI_TOPLANTI,
  DUGME_CAGRI,
  DUGME_DIVAN,
  DUGME_DONEM_GECISI,
  DUGME_EVRAK_KAYDET,
  DUGME_EVRAK_KAYDI,
  DUGME_IKINCI_TOPLANTI,
  DUGME_ILAN,
  DUGME_IPTAL,
  DUGME_KATILIM_ISARETLERI,
  DUGME_PLANLA,
  DUGME_PLANLA_KAYDET,
  DUGME_SONUC,
  DUGME_TOPLANTI_BILGISI,
  DUGME_TUTANAK_TAMAMLA,
  GENEL_KURUL_YOK,
  GENEL_KURUL_YOK_ACIKLAMASI,
  GUNDEM_GEREKLI,
  ISARETLER_KAYDEDILDI,
  KATILIM_ISARETLERI_BASLIGI,
  KURAL_SURUMU_AC,
  KURAL_SURUMU_GUNCELLENMELI,
  MD6_ISARETI_ZORUNLU,
  BIRINCI_TOPLANTI_GEREKLI,
  CAGRI_KAYDEDILDI,
  GIDEN_KAYDEDILDI,
  OLAGANUSTU_DONEM_ACMAZ,
  PLANLANDI,
  SONUC_PENCERESI_BASLIGI,
  TUTANAK_TAMAMLANDI,
  YETER_SAYI_YOK_NOTU,
} from "./metinler";
import DkGenelKurulBolumu from "../organlar/DkGenelKurulBolumu";
import { DUGME_OLUSTUR, DUGME_PDF, EVRAK_OLUSTURULAMADI } from "../evrak/metinler";

// ---------------------------------------------------------------- uydurma veriler

function madde(
  id: number,
  order: number,
  kind: GundemMaddesi["kind"],
  title: string,
): GundemMaddesi {
  return {
    id,
    order,
    kind,
    title,
    notes: "",
    added_by_vote: false,
    removed_by_vote: false,
    change_votes_for: null,
    change_votes_against: null,
    result: "",
    result_text: "",
    votes_for: null,
    votes_against: null,
    present_count: null,
    dosya_eki_belgesi:
      kind === "YK_FAALIYET_RAPORU"
        ? "E34"
        : kind === "DK_RAPORU"
          ? "E33"
          : kind === "TAHMINI_BUTCE"
            ? "E28"
            : "",
    ekler: [],
  };
}

const GUNDEM: GundemMaddesi[] = [
  madde(11, 1, "ACILIS", "Açılış ve yoklama"),
  madde(12, 2, "DIVAN_SECIMI", "Divan seçimi"),
  madde(13, 3, "YK_FAALIYET_RAPORU", "Yönetim kurulu faaliyet raporunun okunması"),
  madde(14, 4, "DK_RAPORU", "Denetleme Kurulu raporunun okunması"),
  madde(15, 5, "IBRA", "Yönetim kurulu ve Denetleme Kurulunun ibrası"),
  madde(16, 6, "SECIM_YK", "Yönetim kurulu seçimi"),
  madde(17, 7, "DILEK", "Dilek ve temenniler"),
];

function kurul(ek: Partial<GenelKurul> = {}): GenelKurul {
  return {
    id: 5,
    kind: "OLAGAN",
    status: "PLANLANDI",
    term: 3,
    opens_term: 4,
    called_by: "",
    called_by_role: "",
    first_meeting_at: "2026-10-20T10:00:00+03:00",
    second_meeting_at: null,
    venue: "Okul konferans salonu",
    held_at_meeting: "",
    quorum_required: null,
    call_reason: "",
    call_decision: null,
    call_document: null,
    call_audit_report: null,
    cagri_sahibi: null,
    member_application_count: null,
    member_count_declared: null,
    announced_on: null,
    second_announced_on: null,
    student_count_snapshot: null,
    quorum_base: null,
    quorum_multiplier: null,
    first_attendee_count: null,
    second_attendee_count: null,
    attendance_by_kind: {},
    parent_students_count: null,
    observer_count: null,
    discharge_yk: "",
    discharge_dk: "",
    discharge_yk_votes_for: null,
    discharge_yk_votes_against: null,
    discharge_yk_present_count: null,
    discharge_dk_votes_for: null,
    discharge_dk_votes_against: null,
    discharge_dk_present_count: null,
    cancel_reason: "",
    rule_warnings: [],
    gundem: GUNDEM,
    ilanlar: [],
    divan: [],
    adaylar: [],
    tutanak: null,
    katilim_duzeltmeleri: [],
    katilim_isareti_sayilari: { BIRINCI: 0, IKINCI: 0 },
    bilgiler: [],
    oturum: { cagiranlar: [], uretilebilir_belgeler: [] },
    ...ek,
  };
}

const LISTE: GenelKurulListesi = {
  kayitlar: [
    {
      id: 5,
      kind: "OLAGAN",
      status: "PLANLANDI",
      term: 3,
      opens_term: 4,
      called_by: "",
      called_by_role: "",
      first_meeting_at: "2026-10-20T10:00:00+03:00",
      second_meeting_at: null,
      venue: "",
      held_at_meeting: "",
      quorum_required: null,
    },
  ],
  acik_donem: 3,
  kural_surumu_guncellenmeli: false,
  planlama_bilgileri: [
    "Okul kartındaki öğrenci mevcudu 120 (15.09.2026 tarihli). Yeter sayı ilanda bu sayıdan hesaplanır ve dondurulur (md. 9/2); güncel değilse ilandan önce okul kartından güncelleyin.",
  ],
};

function katalogSatiri(kod: string, ad: string, ek: Partial<KatalogSatiri> = {}): KatalogSatiri {
  return {
    kod,
    ad,
    konu: "GENEL_KURUL",
    bicimler: ["PDF", "DOCX"],
    kipler: [],
    adli_bicimler: [],
    toplantili: false,
    muhatapli: false,
    ureten_roller: ["sekreter", "yonetici"],
    okuma_satiri: "M3",
    uretilebilir: true,
    uretilemez_nedeni: "",
    ...ek,
  };
}

const KATALOG: Katalog = {
  belgeler: [
    katalogSatiri("E04", "Kişisel veri aydınlatma metni", { uretilebilir: false }),
    katalogSatiri("E05", "Genel kurul toplantı çağrısı ve gündemi", { toplantili: true }),
    katalogSatiri("E07", "Üyelere elden yazılı davet ve sınıf teslim çizelgesi", {
      kipler: ["KISISIZ", "ADLI"],
      // Sunucunun `DocumentFormat` değerleri (büyük harf); uç küçük harf bekler.
      adli_bicimler: ["PDF", "DOCX", "XLSX"],
    }),
    katalogSatiri("E10", "Genel kurul toplantı tutanağı"),
    katalogSatiri("E12", "İbra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı", {
      muhatapli: true,
      ureten_roller: ["yonetici"],
    }),
    katalogSatiri("E14", "Yıllık iş takvimi", { konu: "DONEM" }),
  ],
  muhatap_onerileri: {
    ILCE: { idare: "ÇANKAYA KAYMAKAMLIĞINA", birim: "İlçe Millî Eğitim Müdürlüğü" },
    IL: { idare: "ANKARA VALİLİĞİNE", birim: "İl Millî Eğitim Müdürlüğü" },
  },
  varsayilan_muhatap: "ILCE",
};

/** Rolün yeteneklerinin kurgusu (sunucunun `rol_izinleri.yetenekler`'iyle aynı küme; uydurma oturum). */
const ROL_YETENEKLERI: Record<string, YetenekAdi[]> = {
  yonetici: [...YETENEK_ADLARI].filter(
    (a) => !["mudur_genel_kurul_yazisi", "dk_genel_kurul_yazma"].includes(a),
  ),
  sekreter: [
    "evrak_kaydi",
    "genel_kurul_cagri",
    "genel_kurul_dosya_eki",
    "genel_kurul_evraki",
    "genel_kurul_yazma",
  ],
  denetleme_kurulu: ["dk_genel_kurul_yazma"],
  mudur: ["genel_kurul_evraki", "mudur_genel_kurul_yazisi"],
};

function bas(rol: keyof typeof ROL_YETENEKLERI = "yonetici", adres = "/genel-kurul?kurul=5") {
  return render(
    <YetkiDegeri value={hazirYetki(ROL_YETENEKLERI[rol])}>
      <MemoryRouter initialEntries={[adres]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <GenelKurulPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>
    </YetkiDegeri>,
  );
}

function sonuc(k: GenelKurul) {
  return { genel_kurul: k, uyarilar: [], bilgiler: [] };
}

function gerekceGerekli(metin: string) {
  return new ApiError(400, "gerekce_gerekli", `Bu kayıt için gerekçe yazılmalıdır. ${metin}`);
}

/** Organ üyeliğinin kurgusu (divan ve aday satırları; uydurma kişiler). */
function uyelik(ek: Record<string, unknown>): GenelKurul["adaylar"][number] {
  return {
    id: 0,
    term: 3,
    person: 0,
    person_name: null,
    organ: "YK",
    role: "UYE",
    seat_type: "ASIL",
    seat_group: "",
    seat_order: null,
    elected_by: "GENEL_KURUL",
    source: "PROGRAM",
    evidence_note: "",
    representation: "",
    mem_approval_no: "",
    status: "ADAY",
    start_date: null,
    end_date: null,
    votes: null,
    ...ek,
  } as unknown as GenelKurul["adaylar"][number];
}

/** Bildirimler kuyrukla tek tek görünür: öndekiler kapatılarak aranan bildirime ulaşılır. */
async function bildirimiBekle(metin: string) {
  await waitFor(
    () => {
      if (screen.queryByText(metin) !== null) return;
      const kapat = screen.queryAllByRole("button", { name: "Kapat" });
      if (kapat.length > 0) fireEvent.click(kapat[kapat.length - 1]);
      throw new Error(`"${metin}" bildirimi görünmedi`);
    },
    { timeout: 3000 },
  );
}

const YAPILDI = {
  status: "YAPILDI",
  called_by: "YONETIM_KURULU",
  held_at_meeting: "BIRINCI",
} as const;

beforeEach(() => {
  gkMock.liste.mockResolvedValue(LISTE);
  gkMock.ayrinti.mockResolvedValue(kurul());
  gkMock.katalog.mockResolvedValue(KATALOG);
  gkMock.evrakListesi.mockResolvedValue([]);
  gelenGidenMock.kayitlar.mockResolvedValue([]);
  kisiApiMock.liste.mockResolvedValue([
    { id: 31, kind: "VELI", full_name: "Deniz Uydurma", status: "AKTIF" },
    { id: 32, kind: "OGRETMEN", full_name: "Ece Örnekçi", status: "AKTIF" },
  ]);
  yarimMetinMock.oku.mockResolvedValue(null);
  yarimMetinMock.kaydet.mockResolvedValue(undefined);
  yarimMetinMock.temizle.mockResolvedValue(undefined);
  indirmeMock.saveBlob.mockResolvedValue("kaydedildi");
});

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------- liste ve planlama

describe("Genel Kurul — liste ve planlama", () => {
  it("boş listede planlayan role öğüt cümlesi ve düğme; salt okur rolde ikisi de yok", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kayitlar: [] });
    bas("yonetici", "/genel-kurul");
    expect(await screen.findByText(GENEL_KURUL_YOK)).toBeInTheDocument();
    expect(screen.getByText(GENEL_KURUL_YOK_ACIKLAMASI)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_PLANLA })).toBeInTheDocument();
    // Planlamanın bilgi satırı (öğrenci mevcudu; sunucunun metni).
    expect(screen.getByRole("list", { name: "Planlamadan önce" })).toHaveTextContent(
      "öğrenci mevcudu 120",
    );
  });

  it("Denetleme Kurulu okur: planlama yok, salt okur notu yok (kendi yazması var)", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kayitlar: [] });
    bas("denetleme_kurulu", "/genel-kurul");
    expect(await screen.findByText(GENEL_KURUL_YOK)).toBeInTheDocument();
    expect(screen.queryByText(GENEL_KURUL_YOK_ACIKLAMASI)).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_PLANLA })).toBeNull();
  });

  it("yazma yeteneği olmayan rolde salt okur notu", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kayitlar: [] });
    render(
      <YetkiDegeri value={hazirYetki(["son_oturum_onay"])}>
        <MemoryRouter initialEntries={["/genel-kurul"]}>
          <SnackbarProvider>
            <GenelKurulPage />
          </SnackbarProvider>
        </MemoryRouter>
      </YetkiDegeri>,
    );
    expect(await screen.findByText(SALT_OKUR_ILETISI)).toBeInTheDocument();
  });

  it("kural sürümü genel kurul kurallarını taşımıyorsa planlama yerine Birlik Dönemi'ne götürür (U1)", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kural_surumu_guncellenmeli: true });
    bas("yonetici", "/genel-kurul");
    expect(await screen.findByText(KURAL_SURUMU_GUNCELLENMELI)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: KURAL_SURUMU_AC })).toHaveAttribute(
      "href",
      "/birlik-donemi",
    );
    expect(screen.queryByRole("button", { name: DUGME_PLANLA })).toBeNull();
  });

  it("kural sürümünü güncelleyemeyen planlayıcı (sekreter) bölümü olmayan sayfaya yönlendirilmez (U1)", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kural_surumu_guncellenmeli: true });
    bas("sekreter", "/genel-kurul");
    expect(await screen.findByText(KURAL_SURUMU_GUNCELLENMELI_BASVURUN)).toBeInTheDocument();
    expect(screen.queryByText(KURAL_SURUMU_GUNCELLENMELI)).toBeNull();
    expect(screen.queryByRole("link", { name: KURAL_SURUMU_AC })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_PLANLA })).toBeNull();
  });

  it("liste okunamazsa hata bandı", async () => {
    gkMock.liste.mockRejectedValue(new Error("ağ"));
    bas("yonetici", "/genel-kurul");
    expect(await screen.findByRole("alert")).toHaveTextContent(GENEL_KURULLAR_OKUNAMADI);
  });

  it("genel kurulun kaydı okunamazsa hata bandı", async () => {
    gkMock.ayrinti.mockRejectedValue(new Error("ağ"));
    bas("yonetici");
    expect(await screen.findByRole("alert")).toHaveTextContent(GENEL_KURUL_OKUNAMADI);
  });

  it("planlama: birinci toplantı zorunlu; yerel saat +03:00 ile gider, ayrıntı açılır", async () => {
    const user = userEvent.setup();
    gkMock.planla.mockResolvedValue(sonuc(kurul()));
    bas("yonetici", "/genel-kurul");
    await user.click(await screen.findByRole("button", { name: DUGME_PLANLA }));
    const pencere = screen.getByRole("dialog");
    await user.click(within(pencere).getByRole("button", { name: DUGME_PLANLA_KAYDET }));
    expect(within(pencere).getByText(BIRINCI_TOPLANTI_GEREKLI)).toBeInTheDocument();
    expect(gkMock.planla).not.toHaveBeenCalled();
    fireEvent.change(within(pencere).getByLabelText(/Birinci toplantının günü ve saati/), {
      target: { value: "2026-10-20T10:00" },
    });
    await user.click(within(pencere).getByRole("button", { name: DUGME_PLANLA_KAYDET }));
    expect(gkMock.planla).toHaveBeenCalledWith({
      kind: "OLAGAN",
      first_meeting_at: "2026-10-20T10:00:00+03:00",
      venue: "",
    });
    expect(await screen.findByText(PLANLANDI)).toBeInTheDocument();
    expect(await screen.findByText(/Olağan genel kurul · 20\.10\.2026 10:00/)).toBeInTheDocument();
  });

  it("listenin satırı ayrıntıyı açar", async () => {
    const user = userEvent.setup();
    bas("yonetici", "/genel-kurul");
    await user.click(
      await screen.findByRole("button", {
        name: "Olağan genel kurul · 20.10.2026 10:00 kaydını aç",
      }),
    );
    expect(gkMock.ayrinti).toHaveBeenCalledWith(5);
  });
});

// ---------------------------------------------------------------- sihirbaz ve roller

describe("Genel Kurul — sihirbaz", () => {
  it("planlanmış kurulda süren adım Çağrı; Planla'ya dönülür ve toplantı bilgisi değişir", async () => {
    const user = userEvent.setup();
    bas("yonetici");
    expect(await screen.findByRole("heading", { name: "Çağrı" })).toBeInTheDocument();
    // Program yöneticisi olağan çağrıyı yazmaz (sunucunun seçenekleri boş): düğme yok, açıklama var.
    expect(screen.queryByRole("button", { name: DUGME_CAGRI })).toBeNull();
    await user.click(screen.getByRole("button", { name: /Planla/ }));
    expect(screen.getByRole("heading", { name: "Planla" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_TOPLANTI_BILGISI })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Gündem" })).toHaveTextContent("Divan seçimi");
  });

  it("sekreter yönetim kurulunun çağrısını yazar; gerekçe istenirse kutu açılır ve gerekçeyle gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        oturum: {
          cagiranlar: [{ called_by: "YONETIM_KURULU", yol: "genel" }],
          uretilebilir_belgeler: [],
        },
      }),
    );
    gkMock.cagir
      .mockRejectedValueOnce(
        gerekceGerekli(
          "Genel kurul çağrısı yönetim kurulu kararına bağlanmadı (kullanıcı kararı S1).",
        ),
      )
      .mockResolvedValueOnce(sonuc(kurul({ status: "CAGRILDI", called_by: "YONETIM_KURULU" })));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_CAGRI }));
    const pencere = screen.getByRole("dialog");
    expect(within(pencere).getByText("Çağıran: Yönetim kurulu")).toBeInTheDocument();
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI }));
    expect(gkMock.cagir).toHaveBeenNthCalledWith(1, 5, { called_by: "" });
    const alan = await within(pencere).findByLabelText(/^Gerekçe/);
    await user.type(alan, "Uydurma: karar F3'te bağlanacak.");
    await user.click(within(pencere).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(gkMock.cagir).toHaveBeenNthCalledWith(2, 5, {
      called_by: "",
      gerekce: "Uydurma: karar F3'te bağlanacak.",
    });
    expect(await screen.findByText(CAGRI_KAYDEDILDI)).toBeInTheDocument();
    // Durum ilerledi: süren adım İlan ve davet.
    expect(await screen.findByRole("heading", { name: "İlan ve davet" })).toBeInTheDocument();
  });

  it("olağanüstü çağrıda neden ve gündem zorunlu; müdür kendi yolundan yazar", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        kind: "OLAGANUSTU",
        opens_term: null,
        gundem: [],
        oturum: {
          cagiranlar: [
            { called_by: "OKUL_MUDURU", yol: "mudur" },
            { called_by: "MUDUR_25_2", yol: "mudur" },
          ],
          uretilebilir_belgeler: [],
        },
      }),
    );
    gkMock.mudurCagrisi.mockResolvedValue(sonuc(kurul({ status: "CAGRILDI", kind: "OLAGANUSTU" })));
    bas("mudur");
    await user.click(await screen.findByRole("button", { name: DUGME_CAGRI }));
    const pencere = screen.getByRole("dialog");
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI }));
    expect(within(pencere).getByText(CAGRI_NEDENI_GEREKLI)).toBeInTheDocument();
    expect(within(pencere).getByText(GUNDEM_GEREKLI)).toBeInTheDocument();
    expect(gkMock.mudurCagrisi).not.toHaveBeenCalled();
    await user.selectOptions(within(pencere).getByLabelText("Çağıran"), "OKUL_MUDURU");
    await user.type(within(pencere).getByLabelText(/Çağrı nedeni/), "Uydurma neden.");
    await user.type(within(pencere).getByLabelText("Gündem maddesi 1"), "Yönetim kurulu seçimi");
    await user.selectOptions(within(pencere).getByLabelText("Tür"), "SECIM_YK");
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI }));
    expect(gkMock.mudurCagrisi).toHaveBeenCalledWith(5, {
      called_by: "OKUL_MUDURU",
      call_reason: "Uydurma neden.",
      gundem: [{ title: "Yönetim kurulu seçimi", kind: "SECIM_YK" }],
    });
    expect(gkMock.cagir).not.toHaveBeenCalled();
  });

  it("müdür ve Denetleme Kurulu sihirbazın yazma denetimlerini görmez (çağrılmış kurul)", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul({ status: "CAGRILDI", called_by: "YONETIM_KURULU" }));
    for (const rol of ["denetleme_kurulu", "mudur"] as const) {
      const { unmount } = bas(rol);
      expect(await screen.findByRole("heading", { name: "İlan ve davet" })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: DUGME_ILAN })).toBeNull();
      expect(screen.queryByRole("button", { name: DUGME_IPTAL })).toBeNull();
      // Sahipsiz çağrının toplantı bilgisi ve gündem sırası genel kurul yazma kapısındadır.
      await user.click(screen.getByRole("button", { name: "Planla adımına dön" }));
      expect(screen.queryByRole("button", { name: DUGME_TOPLANTI_BILGISI })).toBeNull();
      expect(screen.queryByRole("button", { name: DUGME_GUNDEM_SIRASI })).toBeNull();
      unmount();
    }
  });

  it("müdürün kendi çağrısında toplantı bilgisini yalnız müdür değiştirir", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        kind: "OLAGANUSTU",
        opens_term: null,
        status: "CAGRILDI",
        called_by: "OKUL_MUDURU",
        cagri_sahibi: "mudur",
      }),
    );
    const { unmount } = bas("mudur");
    await user.click(await screen.findByRole("button", { name: "Planla adımına dön" }));
    expect(screen.getByRole("button", { name: DUGME_TOPLANTI_BILGISI })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_GUNDEM_SIRASI })).toBeInTheDocument();
    unmount();
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: "Planla adımına dön" }));
    expect(screen.queryByRole("button", { name: DUGME_TOPLANTI_BILGISI })).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_GUNDEM_SIRASI })).toBeNull();
  });

  it("toplantı bilgisi: birinci toplantı zorunlu; gün ve yer gider", async () => {
    const user = userEvent.setup();
    gkMock.toplantiBilgisi.mockResolvedValue(sonuc(kurul({ venue: "Spor salonu" })));
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: "Planla adımına dön" }));
    await user.click(screen.getByRole("button", { name: DUGME_TOPLANTI_BILGISI }));
    const pencere = screen.getByRole("dialog", { name: TOPLANTI_BILGISI_BASLIGI });
    const an = within(pencere).getByLabelText(/Birinci toplantının günü ve saati/);
    fireEvent.change(an, { target: { value: "" } });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText(BIRINCI_TOPLANTI_GEREKLI)).toBeInTheDocument();
    expect(gkMock.toplantiBilgisi).not.toHaveBeenCalled();
    fireEvent.change(an, { target: { value: "2026-10-22T14:30" } });
    const yer = within(pencere).getByLabelText("Toplantı yeri");
    await user.clear(yer);
    await user.type(yer, "Spor salonu");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gkMock.toplantiBilgisi).toHaveBeenCalledWith(5, {
      first_meeting_at: "2026-10-22T14:30:00+03:00",
      venue: "Spor salonu",
    });
  });

  it("gündem sırası: taşınan maddeyle birlikte bütün sıra gider", async () => {
    const user = userEvent.setup();
    gkMock.gundemSirasi.mockResolvedValue(sonuc(kurul()));
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: "Planla adımına dön" }));
    await user.click(screen.getByRole("button", { name: DUGME_GUNDEM_SIRASI }));
    const pencere = screen.getByRole("dialog", { name: GUNDEM_SIRASI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Divan seçimi: Aşağı taşı" }));
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gkMock.gundemSirasi).toHaveBeenCalledWith(5, [11, 13, 12, 14, 15, 16, 17]);
  });

  it("üyelerin başvurusunda çağrı yazısını yalnız program yöneticisi bağlar", async () => {
    const user = userEvent.setup();
    const basvuru = kurul({
      kind: "OLAGANUSTU",
      opens_term: null,
      status: "CAGRILDI",
      called_by: "UYE_BASVURUSU",
      call_document: null,
    });
    gkMock.ayrinti.mockResolvedValue(basvuru);
    const gelen: EvrakKaydi = {
      id: 9,
      book: 2,
      direction: "GELEN",
      year: 2026,
      record_no: 14,
      date: "2026-10-03",
      counterparty: "Uydurma veli grubu",
      subject: "Olağanüstü genel kurul başvurusu",
      external_ref: "",
      generated_document: null,
      term: 3,
      ekler: [],
    };
    gelenGidenMock.kayitlar.mockResolvedValue([gelen]);
    gkMock.cagriYazisi.mockResolvedValue(sonuc({ ...basvuru, call_document: 9 }));
    const { unmount } = bas("sekreter");
    await user.click(await screen.findByRole("button", { name: "Çağrı adımına dön" }));
    expect(screen.queryByRole("button", { name: DUGME_CAGRI_YAZISI })).toBeNull();
    unmount();
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: "Çağrı adımına dön" }));
    await user.click(screen.getByRole("button", { name: DUGME_CAGRI_YAZISI }));
    const pencere = screen.getByRole("dialog", { name: CAGRI_YAZISI_BASLIGI });
    expect(gelenGidenMock.kayitlar).toHaveBeenCalledWith({ direction: "GELEN" });
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI_YAZISI }));
    expect(gkMock.cagriYazisi).not.toHaveBeenCalled();
    await user.selectOptions(
      within(pencere).getByRole("combobox"),
      await within(pencere).findByRole("option", { name: "2026/14 · 03.10.2026" }),
    );
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI_YAZISI }));
    expect(gkMock.cagriYazisi).toHaveBeenCalledWith(5, 9);
  });

  it("ilan: kanalların günleri ve ikinci toplantı gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul({ status: "CAGRILDI", called_by: "YONETIM_KURULU" }));
    gkMock.ilan.mockResolvedValue(sonuc(kurul({ status: "ILAN_EDILDI", quorum_required: 64 })));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_ILAN }));
    const pencere = screen.getByRole("dialog");
    fireEvent.change(within(pencere).getByLabelText("Elden yazılı bildirimin günü"), {
      target: { value: "2026-10-05" },
    });
    fireEvent.change(within(pencere).getByLabelText(/İkinci toplantının günü/), {
      target: { value: "2026-11-05T10:00" },
    });
    await user.click(within(pencere).getByRole("button", { name: DUGME_ILAN }));
    expect(gkMock.ilan).toHaveBeenCalledWith(5, {
      kanallar: {
        distributed_written_on: "2026-10-05",
        posted_board_on: null,
        published_web_on: null,
      },
      second_meeting_at: "2026-11-05T10:00:00+03:00",
    });
  });

  it("birinci toplantının sayıları; yeter sayı yoksa not ve ikinci toplantı düğmesi", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        status: "ILAN_EDILDI",
        called_by: "YONETIM_KURULU",
        quorum_required: 64,
        bilgiler: ["Toplantının açılışını okul müdürü yapar (md. 10/1-b)."],
      }),
    );
    gkMock.birinciToplanti.mockResolvedValue(
      sonuc(
        kurul({ status: "YETER_SAYI_YOK", called_by: "YONETIM_KURULU", first_attendee_count: 10 }),
      ),
    );
    bas("yonetici");
    expect(await screen.findByText("Toplantının açılışını okul müdürü yapar.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_BIRINCI_TOPLANTI }));
    const pencere = screen.getByRole("dialog");
    await user.type(within(pencere).getByLabelText(/^Katılan üye sayısı/), "10");
    await user.type(within(pencere).getByLabelText("Veli ve kursiyer"), "8");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gkMock.birinciToplanti).toHaveBeenCalledWith(5, {
      attendee_count: 10,
      attendance_by_kind: { VELI_KURSIYER: 8 },
      parent_students_count: null,
      observer_count: null,
    });
    expect(await screen.findByText(YETER_SAYI_YOK_NOTU)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_IKINCI_TOPLANTI })).toBeInTheDocument();
  });

  it("katılım işaretleri penceresi yalnız program yöneticisinde; veli adları ve değişiklik gider", async () => {
    const user = userEvent.setup();
    const ilanli = kurul({
      status: "ILAN_EDILDI",
      called_by: "YONETIM_KURULU",
      quorum_required: 64,
    });
    gkMock.ayrinti.mockResolvedValue(ilanli);
    gkMock.katilimIsaretleri.mockResolvedValue({
      toplanti: "BIRINCI",
      siniflar: [
        {
          sinif: "9-A",
          satirlar: [
            {
              id: 101,
              veli: "Ayla Uydurma",
              isaretli: true,
              oteki_toplanti: false,
              baska_isaret: false,
            },
            {
              id: 102,
              veli: "Bora Örnek",
              isaretli: false,
              oteki_toplanti: false,
              baska_isaret: false,
            },
            { id: 103, veli: null, isaretli: false, oteki_toplanti: false, baska_isaret: true },
          ],
        },
      ],
    });
    gkMock.isaretle.mockResolvedValue({ toplanti: "BIRINCI", isaret_sayisi: 1 });
    const { unmount } = bas("sekreter");
    expect(await screen.findByRole("button", { name: DUGME_BIRINCI_TOPLANTI })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_KATILIM_ISARETLERI })).toBeNull();
    unmount();
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: DUGME_KATILIM_ISARETLERI }));
    const pencere = screen.getByRole("dialog", { name: KATILIM_ISARETLERI_BASLIGI });
    expect(await within(pencere).findByText("Ayla Uydurma")).toBeInTheDocument();
    expect(gkMock.katilimIsaretleri).toHaveBeenCalledWith(5, "BIRINCI");
    expect(within(pencere).getByRole("checkbox", { name: /Adı okunamayan satır/ })).toBeDisabled();
    await user.click(within(pencere).getByRole("checkbox", { name: "Ayla Uydurma" }));
    await user.click(within(pencere).getByRole("checkbox", { name: "Bora Örnek" }));
    await user.click(within(pencere).getByRole("button", { name: "İşaretleri kaydet" }));
    expect(gkMock.isaretle).toHaveBeenCalledWith(5, {
      toplanti: "BIRINCI",
      isaretle: [102],
      kaldir: [101],
    });
    expect(await screen.findByText(ISARETLER_KAYDEDILDI)).toBeInTheDocument();
  });

  it("tutanak: divan, oylanan maddenin sonucu ve tutanağın gerekçeyle tamamlanması", async () => {
    const user = userEvent.setup();
    const yapildi = kurul({
      status: "YAPILDI",
      called_by: "YONETIM_KURULU",
      held_at_meeting: "BIRINCI",
    });
    gkMock.ayrinti.mockResolvedValue(yapildi);
    gkMock.divan.mockResolvedValue(sonuc(yapildi));
    gkMock.kararSonucu.mockResolvedValue({ ...sonuc(yapildi), madde: GUNDEM[6] });
    gkMock.tutanagiTamamla
      .mockRejectedValueOnce(gerekceGerekli("İlanın internet kanıtı girilmedi (md. 9/3)."))
      .mockResolvedValueOnce(sonuc(kurul({ status: "TUTANAK_TAMAM", held_at_meeting: "BIRINCI" })));
    gkMock.donemGecisi.mockResolvedValue({
      genel_kurul: 5,
      yeni_donem: { id: 4, name: "2026-2027 birlik dönemi", status: "HAZIRLIK" },
      baslangic: "2026-10-20",
      kapanacak: { id: 3, name: "2025-2026 birlik dönemi", status: "ACIK" },
      kapanacak_bitis: "2026-10-19",
      engeller: [],
    });
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_DIVAN }));
    const divan = screen.getByRole("dialog", { name: DIVAN_PENCERESI_BASLIGI });
    await user.click(within(divan).getByRole("button", { name: DUGME_DIVAN }));
    expect(within(divan).getAllByText("Kişiyi seçin.")).toHaveLength(2);
    expect(gkMock.divan).not.toHaveBeenCalled();
    await user.click(within(divan).getByRole("button", { name: "Vazgeç" }));

    const sonucDugmeleri = screen.getAllByRole("button", { name: DUGME_SONUC });
    await user.click(sonucDugmeleri[sonucDugmeleri.length - 1]);
    const sonucPenceresi = screen.getByRole("dialog", { name: SONUC_PENCERESI_BASLIGI });
    await user.type(within(sonucPenceresi).getByLabelText("Kabul oyu"), "40");
    await user.click(within(sonucPenceresi).getByRole("button", { name: DUGME_SONUC }));
    expect(
      within(sonucPenceresi).getByText("Kabul ve ret oylarını birlikte girin."),
    ).toBeInTheDocument();
    await user.type(within(sonucPenceresi).getByLabelText("Ret oyu"), "3");
    await user.click(within(sonucPenceresi).getByRole("button", { name: DUGME_SONUC }));
    expect(gkMock.kararSonucu).toHaveBeenCalledWith(17, {
      votes_for: 40,
      votes_against: 3,
      present_count: null,
      result_text: "",
    });

    await user.click(await screen.findByRole("button", { name: DUGME_TUTANAK_TAMAMLA }));
    const tamamla = screen.getByRole("dialog");
    await user.click(within(tamamla).getByRole("button", { name: DUGME_TUTANAK_TAMAMLA }));
    const alan = await within(tamamla).findByLabelText(/^Gerekçe/);
    await user.type(alan, "Uydurma: internet sayfası yok.");
    await user.click(within(tamamla).getByRole("button", { name: "Gerekçeyle kaydet" }));
    expect(gkMock.tutanagiTamamla).toHaveBeenLastCalledWith(5, {
      gerekce: "Uydurma: internet sayfası yok.",
    });
    // Bildirimler kuyrukla gösterilir; tamamlanan tutanak sihirbazı Sonrası adımına geçirir.
    await bildirimiBekle(TUTANAK_TAMAMLANDI);
    // Sekreter dönem geçişini onaylamaz (U32): önizleme görünür, düğme yok.
    expect(await screen.findByText("2026-2027 birlik dönemi · Hazırlık")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_DONEM_GECISI })).toBeNull();
  });

  it("dönem geçişini yalnız program yöneticisi onaylar (U32)", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul({ status: "TUTANAK_TAMAM", held_at_meeting: "IKINCI" }));
    const onizleme = {
      genel_kurul: 5,
      yeni_donem: { id: 4, name: "2026-2027 birlik dönemi", status: "HAZIRLIK" },
      baslangic: "2026-11-05",
      kapanacak: { id: 3, name: "2025-2026 birlik dönemi", status: "ACIK" },
      kapanacak_bitis: "2026-11-04",
      engeller: [],
    };
    gkMock.donemGecisi.mockResolvedValue(onizleme);
    gkMock.donemGecisiniOnayla.mockResolvedValue({
      ...onizleme,
      yeni_donem: { ...onizleme.yeni_donem, status: "ACIK" },
    });
    bas("yonetici");
    expect(await screen.findByText("05.11.2026")).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: DUGME_DONEM_GECISI }));
    const onay = screen.getByRole("dialog", { name: DONEM_GECISI_ONAY_BASLIGI });
    await user.click(within(onay).getByRole("button", { name: DUGME_DONEM_GECISI }));
    expect(gkMock.donemGecisiniOnayla).toHaveBeenCalledWith(5);
    expect(
      await screen.findByText("Yeni birlik dönemi açıldı.", { selector: "p" }),
    ).toBeInTheDocument();
  });

  it("olağanüstü genel kurul dönem açmaz: önizleme okunmaz", async () => {
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        status: "TUTANAK_TAMAM",
        kind: "OLAGANUSTU",
        opens_term: null,
        held_at_meeting: "BIRINCI",
      }),
    );
    bas("yonetici");
    expect(await screen.findByText(OLAGANUSTU_DONEM_ACMAZ)).toBeInTheDocument();
    expect(gkMock.donemGecisi).not.toHaveBeenCalled();
  });

  it("iptal yalnız program yöneticisinde ve gerekçeyle", async () => {
    const user = userEvent.setup();
    gkMock.iptalEt.mockResolvedValue(sonuc(kurul({ status: "IPTAL", cancel_reason: "Uydurma." })));
    const { unmount } = bas("sekreter");
    expect(await screen.findByRole("heading", { name: "Çağrı" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_IPTAL })).toBeNull();
    unmount();
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: DUGME_IPTAL }));
    const pencere = screen.getByRole("dialog");
    await user.type(within(pencere).getByLabelText(/İptal gerekçesi/), "Uydurma.");
    await user.click(within(pencere).getByRole("button", { name: "İptal et" }));
    expect(gkMock.iptalEt).toHaveBeenCalledWith(5, "Uydurma.");
    // İptalden sonra kayıt salt okunur: not ve gerekçe görünür, iptal düğmesi kalkar.
    expect(await screen.findByText(IPTAL_EDILDI_NOTU)).toBeInTheDocument();
    expect(screen.getByText("İptal gerekçesi: Uydurma.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_IPTAL })).toBeNull();
  });

  it("dosya ekleri: yönetim kurulu rolleri raporu ekler, Denetleme Kurulu raporunu yalnız Denetleme Kurulu", async () => {
    const user = userEvent.setup();
    gkMock.dosyaEki.mockResolvedValue({ id: 1 });
    bas("sekreter");
    const ekle = await screen.findByLabelText(/Yönetim kurulu faaliyet raporu: Dosya ekle/);
    expect(screen.queryByLabelText(/Denetleme Kurulu raporu: Dosya ekle/)).toBeNull();
    const dosya = new File(["%PDF"], "rapor.pdf", { type: "application/pdf" });
    await user.upload(ekle, dosya);
    const dugmeler = screen.getAllByRole("button", { name: "Dosya ekle" });
    await user.click(dugmeler[0]);
    expect(gkMock.dosyaEki).toHaveBeenCalledWith(13, dosya, false);
  });
});

// ---------------------------------------------------------------- belge kartları

describe("Genel Kurul — belge kartları", () => {
  it("üretim yalnız sunucunun listesindeki belgede; E04 ve E14 burada yok", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        status: "CAGRILDI",
        called_by: "YONETIM_KURULU",
        oturum: { cagiranlar: [], uretilebilir_belgeler: ["E05", "E10"] },
      }),
    );
    gkMock.evrakUret.mockResolvedValue({
      evrak: {
        id: 70,
        kod: "E05",
        ad: "Genel kurul toplantı çağrısı ve gündemi",
        kip: "",
        toplanti: "BIRINCI",
        surum: 1,
        durum: "GECERLI",
        uretim_zamani: "2026-10-01T09:00:00+03:00",
        bicimler: ["PDF", "DOCX"],
        kisi_listesi: false,
        satir_sayisi: null,
      },
      uyarilar: ["Karar tarihi ve sayısı ……… basıldı."],
    });
    bas("sekreter");
    expect(await screen.findByText("Genel kurul toplantı çağrısı ve gündemi")).toBeInTheDocument();
    expect(screen.queryByText("Kişisel veri aydınlatma metni")).toBeNull();
    expect(screen.queryByText("Yıllık iş takvimi")).toBeNull();
    const olustur = screen.getAllByRole("button", { name: DUGME_OLUSTUR });
    // E05 ve E10 üretilir; E07 ve E12 bu rolde üretilmez.
    expect(olustur).toHaveLength(2);
    await user.click(olustur[0]);
    expect(gkMock.evrakUret).toHaveBeenCalledWith(5, "E05", { kip: "", toplanti: "BIRINCI" });
    expect(await screen.findByText("Karar tarihi ve sayısı ……… basıldı.")).toBeInTheDocument();
  });

  it("Denetleme Kurulunun çağrısında çağrı yazısı kendi ucundan", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        kind: "OLAGANUSTU",
        status: "ILAN_EDILDI",
        called_by: "DENETLEME_KURULU",
        cagri_sahibi: "denetleme_kurulu",
        oturum: { cagiranlar: [], uretilebilir_belgeler: ["E05"] },
      }),
    );
    gkMock.dkCagriYazisi.mockResolvedValue({ evrak: { id: 1, kod: "E05" }, uyarilar: [] });
    bas("denetleme_kurulu");
    await user.click(await screen.findByRole("button", { name: DUGME_OLUSTUR }));
    expect(gkMock.dkCagriYazisi).toHaveBeenCalledWith(5, "BIRINCI");
    expect(gkMock.evrakUret).not.toHaveBeenCalled();
  });

  it("veli adlı çıktı yalnız program yöneticisinde; tek istekte iner, saklanmaz", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul({ status: "ILAN_EDILDI", called_by: "YONETIM_KURULU" }));
    const blob = new Blob(["%PDF"]);
    gkMock.adliEvrak.mockResolvedValue({
      blob,
      ad: "Genel-Kurul-Daveti-Sınıf-Teslim-Çizelgesi_05.10.2026.pdf",
    });
    const { unmount } = bas("sekreter");
    expect(
      await screen.findByText("Üyelere elden yazılı davet ve sınıf teslim çizelgesi"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: DUGME_ADLI_PDF })).toBeNull();
    unmount();
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: DUGME_ADLI_PDF }));
    expect(screen.getByRole("button", { name: DUGME_ADLI_WORD })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: DUGME_ADLI_EXCEL })).toBeInTheDocument();
    expect(gkMock.adliEvrak).toHaveBeenCalledWith(5, "E07", "pdf", "");
    expect(indirmeMock.saveBlob).toHaveBeenCalledWith(
      blob,
      "Genel-Kurul-Daveti-Sınıf-Teslim-Çizelgesi_05.10.2026.pdf",
    );
    expect(await screen.findByText(ADLI_CIKTI_KAYDEDILDI)).toBeInTheDocument();
  });

  it("E12: muhatap ilçe varsayılan, il seçilince öneri değişir; kayıt öneriyle onaylanır", async () => {
    const user = userEvent.setup();
    const e12 = {
      id: 80,
      kod: "E12",
      ad: "İbra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı",
      kip: "",
      toplanti: "",
      surum: 1,
      durum: "GECERLI",
      uretim_zamani: "2026-10-21T09:00:00+03:00",
      bicimler: ["PDF", "DOCX"],
      kisi_listesi: false,
      satir_sayisi: null,
    };
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        status: "TUTANAK_TAMAM",
        held_at_meeting: "BIRINCI",
        oturum: { cagiranlar: [], uretilebilir_belgeler: ["E12"] },
      }),
    );
    gkMock.donemGecisi.mockRejectedValue(new Error("ağ"));
    gkMock.evrakListesi.mockResolvedValue([e12]);
    gkMock.evrakUret.mockResolvedValue({ evrak: e12, uyarilar: [] });
    gelenGidenMock.gidenOnerisi.mockResolvedValue({
      evrak: 80,
      kod: "E12",
      kayitli: null,
      direction: "GIDEN",
      tarih: "2026-10-21",
      counterparty: "ÇANKAYA KAYMAKAMLIĞINA (İlçe Millî Eğitim Müdürlüğü)",
      subject: "Genel Kurulda Hesapların İbra Edilmemesi",
      defter: 2,
      onerilen_no: 14,
      gecerli: true,
    });
    gelenGidenMock.gidenKaydet.mockResolvedValue({ kayit: { id: 9 }, uyarilar: [] });
    bas("yonetici");
    // Dönem geçişinin önizlemesi okunamadı: Sonrası'nda hata bandı.
    expect(await screen.findByText(DONEM_GECISI_OKUNAMADI)).toBeInTheDocument();
    const muhatap = await screen.findByLabelText("Muhatap");
    expect(screen.getByLabelText("Muhatap idare")).toHaveValue("ÇANKAYA KAYMAKAMLIĞINA");
    await user.selectOptions(muhatap, "IL");
    expect(screen.getByLabelText("Muhatap idare")).toHaveValue("ANKARA VALİLİĞİNE");
    await user.click(screen.getByRole("button", { name: "Belgeyi yeniden oluştur" }));
    expect(gkMock.evrakUret).toHaveBeenCalledWith(5, "E12", {
      kip: "",
      toplanti: "",
      muhatap_secimi: "IL",
      muhatap_idare: "ANKARA VALİLİĞİNE",
      muhatap_birim: "İl Millî Eğitim Müdürlüğü",
    });
    expect(screen.getByRole("button", { name: DUGME_PDF })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_EVRAK_KAYDI }));
    const pencere = screen.getByRole("dialog");
    const no = await within(pencere).findByLabelText("Kayıt no");
    expect(no).toHaveValue("14");
    // Rakam olmayan numara sıradaki numaraya dönmez: alan hatası, istek gitmez.
    await user.clear(no);
    await user.type(no, "14a");
    await user.click(within(pencere).getByRole("button", { name: DUGME_EVRAK_KAYDET }));
    expect(within(pencere).getByText(SAYI_GECERSIZ)).toBeInTheDocument();
    expect(gelenGidenMock.gidenKaydet).not.toHaveBeenCalled();
    await user.clear(no);
    await user.type(no, "14");
    await user.click(within(pencere).getByRole("button", { name: DUGME_EVRAK_KAYDET }));
    expect(gelenGidenMock.gidenKaydet).toHaveBeenCalledWith(80, {
      tarih: "2026-10-21",
      counterparty: "ÇANKAYA KAYMAKAMLIĞINA (İlçe Millî Eğitim Müdürlüğü)",
      subject: "Genel Kurulda Hesapların İbra Edilmemesi",
      external_ref: "",
      record_no: 14,
    });
    // Pencere kapanır (bildirim kuyrukta, üretimin bildiriminden sonra gelir).
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await bildirimiBekle(GIDEN_KAYDEDILDI);
  });

  it("E12'nin evrak kaydı müdür ve Denetleme Kurulunda çizilmez", async () => {
    gkMock.ayrinti.mockResolvedValue(
      kurul({ status: "TUTANAK_TAMAM", held_at_meeting: "BIRINCI" }),
    );
    gkMock.donemGecisi.mockRejectedValue(new Error("ağ"));
    gkMock.evrakListesi.mockResolvedValue([
      {
        id: 80,
        kod: "E12",
        ad: "İbra edilmediğine dair il/ilçe millî eğitim müdürlüğüne resmî yazı",
        kip: "",
        toplanti: "",
        surum: 1,
        durum: "GECERLI",
        uretim_zamani: "2026-10-21T09:00:00+03:00",
        bicimler: ["PDF", "DOCX"],
        kisi_listesi: false,
        satir_sayisi: null,
      },
    ]);
    for (const rol of ["mudur", "denetleme_kurulu"] as const) {
      const { unmount } = bas(rol);
      expect(await screen.findByRole("button", { name: DUGME_PDF })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: DUGME_EVRAK_KAYDI })).toBeNull();
      unmount();
    }
  });

  it("belge kartı: uyum hatası kendi bandında, öteki hata sayfa bandında; katalog okunamazsa ileti", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({
        status: "CAGRILDI",
        called_by: "YONETIM_KURULU",
        oturum: { cagiranlar: [], uretilebilir_belgeler: ["E05"] },
      }),
    );
    gkMock.evrakUret
      .mockRejectedValueOnce(
        new ApiError(409, "donem_kapali", "Bu birlik dönemi kapandı; kayıt yazılamaz."),
      )
      .mockRejectedValueOnce(new Error("ağ"));
    const { unmount } = bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_OLUSTUR }));
    expect(await screen.findByText("Bu kayıt yazılamaz")).toBeInTheDocument();
    expect(screen.queryByText(EVRAK_OLUSTURULAMADI)).toBeNull();
    await user.click(screen.getByRole("button", { name: DUGME_OLUSTUR }));
    expect(await screen.findByText(EVRAK_OLUSTURULAMADI)).toBeInTheDocument();
    expect(screen.queryByText("Bu kayıt yazılamaz")).toBeNull();
    unmount();
    gkMock.katalog.mockRejectedValue(new Error("ağ"));
    bas("sekreter");
    expect(await screen.findByText(KATALOG_OKUNAMADI)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------- pencerelerin gövdeleri ve hataları

describe("Genel Kurul — pencerelerin gövdeleri", () => {
  it("pencerede sert engel bantla gösterilir; öteki ret hata bandıyla; pencere açık kalır, gerekçe sorulmaz", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(
      kurul({ status: "ILAN_EDILDI", called_by: "YONETIM_KURULU", quorum_required: 64 }),
    );
    gkMock.birinciToplanti
      .mockRejectedValueOnce(
        new ApiError(400, "kural_sert", "Uydurma sert engel: bu toplantının sayısı yazılamaz."),
      )
      .mockRejectedValueOnce(
        new ApiError(409, "cakisma", "Bu toplantının sayıları başka bir oturumda kaydedildi."),
      );
    bas("yonetici");
    await user.click(await screen.findByRole("button", { name: DUGME_BIRINCI_TOPLANTI }));
    const pencere = screen.getByRole("dialog");
    await user.type(within(pencere).getByLabelText(/^Katılan üye sayısı/), "10");
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(await within(pencere).findByText(/Uydurma sert engel/)).toBeInTheDocument();
    expect(within(pencere).queryByLabelText(/^Gerekçe/)).toBeNull();
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(await within(pencere).findByRole("alert")).toHaveTextContent(
      "Bu toplantının sayıları başka bir oturumda kaydedildi.",
    );
    expect(within(pencere).queryByLabelText(/^Gerekçe/)).toBeNull();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(gkMock.birinciToplanti).toHaveBeenCalledTimes(2);
  });

  it("katılım düzeltmesi: sayı, doğru değer ve gerekçe zorunlu; düzeltilen alan gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul({ ...YAPILDI, first_attendee_count: 10 }));
    gkMock.katilimDuzelt.mockResolvedValue(sonuc(kurul({ ...YAPILDI, first_attendee_count: 12 })));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: "Toplantı adımına dön" }));
    await user.click(screen.getByRole("button", { name: DUGME_KATILIM_DUZELTMESI }));
    const pencere = screen.getByRole("dialog", { name: KATILIM_DUZELTMESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(within(pencere).getByText(YENI_DEGER_GEREKLI)).toBeInTheDocument();
    expect(within(pencere).getByText(DUZELTME_GEREKCESI_YAZIN)).toBeInTheDocument();
    expect(gkMock.katilimDuzelt).not.toHaveBeenCalled();
    await user.selectOptions(
      within(pencere).getByLabelText(/Düzeltilen sayı/),
      "first_attendee_count",
    );
    await user.type(within(pencere).getByLabelText(/Doğru değer/), "12");
    await user.type(
      within(pencere).getByLabelText(/Düzeltmenin gerekçesi/),
      "Uydurma: imza listesi yeniden sayıldı.",
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gkMock.katilimDuzelt).toHaveBeenCalledWith(5, {
      toplanti: "BIRINCI",
      degerler: { first_attendee_count: 12 },
      justification: "Uydurma: imza listesi yeniden sayıldı.",
    });
  });

  it("divan: düzeltilen divan listeden düşer, divan yeniden seçilir ve kişiler gider", async () => {
    const user = userEvent.setup();
    const baskan = uyelik({
      id: 61,
      person: 31,
      person_name: "Deniz Uydurma",
      organ: "DIVAN",
      role: "BASKAN",
      status: "SECILDI",
    });
    const katip = uyelik({
      id: 62,
      person: 32,
      person_name: "Ece Örnekçi",
      organ: "DIVAN",
      role: "KATIP",
      status: "SECILDI",
    });
    gkMock.ayrinti.mockResolvedValue(kurul({ ...YAPILDI, divan: [baskan, katip] }));
    // Sunucu düzeltilen divanı göstermese de iptal edilmiş kayıtlar ekranda divan sayılmaz.
    gkMock.divanIptal.mockResolvedValue(
      sonuc(
        kurul({
          ...YAPILDI,
          divan: [
            { ...baskan, status: "IPTAL" },
            { ...katip, status: "IPTAL" },
          ],
        }),
      ),
    );
    gkMock.divan.mockResolvedValue(sonuc(kurul({ ...YAPILDI, divan: [baskan, katip] })));
    bas("sekreter");
    expect(await screen.findByText(/Deniz Uydurma · Divan başkanı/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: DUGME_DIVAN_IPTAL }));
    const iptal = screen.getByRole("dialog", { name: DIVAN_IPTAL_BASLIGI });
    await user.type(within(iptal).getByLabelText(/İptal gerekçesi/), "Uydurma: kâtip yanlış.");
    await user.click(within(iptal).getByRole("button", { name: "İptal et" }));
    expect(gkMock.divanIptal).toHaveBeenCalledWith(5, "Uydurma: kâtip yanlış.");
    expect(await screen.findByText(DIVAN_YOK)).toBeInTheDocument();
    expect(screen.queryByText(/Deniz Uydurma · Divan başkanı/)).toBeNull();
    expect(screen.queryByRole("button", { name: DUGME_DIVAN_IPTAL })).toBeNull();
    await user.click(screen.getByRole("button", { name: DUGME_DIVAN }));
    const divan = screen.getByRole("dialog", { name: DIVAN_PENCERESI_BASLIGI });
    const [baskanAlani, katipAlani] = within(divan).getAllByRole("combobox", { name: /Kişi/ });
    await user.type(baskanAlani, "Deniz");
    await user.click(await within(divan).findByRole("option", { name: /Deniz Uydurma/ }));
    await user.type(katipAlani, "Ece");
    await user.click(await within(divan).findByRole("option", { name: /Ece Örnekçi/ }));
    await user.click(within(divan).getByRole("button", { name: DUGME_DIVAN }));
    expect(gkMock.divan).toHaveBeenCalledWith(5, { baskan: 31, katip: 32 });
    expect(await screen.findByText(/Ece Örnekçi · Kâtip/)).toBeInTheDocument();
  });

  it("gündeme ekleme: başlık zorunlu; sıra ve değişikliğin oyları gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul(YAPILDI));
    gkMock.gundemeEkle.mockResolvedValue(sonuc(kurul(YAPILDI)));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_GUNDEM_EKLE }));
    const pencere = screen.getByRole("dialog", { name: GUNDEM_EKLE_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: DUGME_GUNDEM_EKLE }));
    expect(within(pencere).getByText(MADDE_BASLIGI_GEREKLI)).toBeInTheDocument();
    expect(gkMock.gundemeEkle).not.toHaveBeenCalled();
    await user.type(
      within(pencere).getByLabelText(/Maddenin başlığı/),
      "Okul bahçesinin düzenlenmesi",
    );
    await user.type(within(pencere).getByLabelText("Gündemdeki sırası"), "3");
    await user.type(within(pencere).getByLabelText("Değişikliğe kabul oyu"), "30");
    await user.type(within(pencere).getByLabelText("Değişikliğe ret oyu"), "2");
    await user.click(within(pencere).getByRole("button", { name: DUGME_GUNDEM_EKLE }));
    expect(gkMock.gundemeEkle).toHaveBeenCalledWith(5, {
      title: "Okul bahçesinin düzenlenmesi",
      kind: "DIGER",
      sira: 3,
      change_votes_for: 30,
      change_votes_against: 2,
    });
  });

  it("gündemden çıkarma: değişikliğin oyları gider; geçersiz sayı gitmez", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul(YAPILDI));
    gkMock.gundemdenCikar.mockResolvedValue({ ...sonuc(kurul(YAPILDI)), madde: GUNDEM[6] });
    bas("sekreter");
    const dugmeler = await screen.findAllByRole("button", { name: DUGME_GUNDEMDEN_CIKAR });
    await user.click(dugmeler[dugmeler.length - 1]);
    const pencere = screen.getByRole("dialog", { name: GUNDEMDEN_CIKAR_BASLIGI });
    expect(within(pencere).getByText("Dilek ve temenniler")).toBeInTheDocument();
    await user.type(within(pencere).getByLabelText("Değişikliğe kabul oyu"), "2a");
    await user.click(within(pencere).getByRole("button", { name: DUGME_GUNDEMDEN_CIKAR }));
    expect(within(pencere).getByText(SAYI_GECERSIZ)).toBeInTheDocument();
    expect(gkMock.gundemdenCikar).not.toHaveBeenCalled();
    await user.clear(within(pencere).getByLabelText("Değişikliğe kabul oyu"));
    await user.type(within(pencere).getByLabelText("Değişikliğe kabul oyu"), "25");
    await user.type(within(pencere).getByLabelText("Değişikliğe ret oyu"), "5");
    await user.click(within(pencere).getByRole("button", { name: DUGME_GUNDEMDEN_CIKAR }));
    expect(gkMock.gundemdenCikar).toHaveBeenCalledWith(17, {
      change_votes_for: 25,
      change_votes_against: 5,
    });
  });

  it("ibra: kurulun kabul ve ret oyları birlikte girilir; görüşülmeyen kurul null gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul(YAPILDI));
    gkMock.ibra.mockResolvedValue({ ...sonuc(kurul(YAPILDI)), madde: GUNDEM[4] });
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_IBRA }));
    const pencere = screen.getByRole("dialog", { name: IBRA_PENCERESI_BASLIGI });
    const yk = within(pencere).getByRole("group", { name: "Yönetim kurulu" });
    await user.type(within(yk).getByLabelText("Kabul oyu"), "15");
    await user.click(within(pencere).getByRole("button", { name: DUGME_IBRA }));
    expect(within(yk).getByText(OYLAR_BIRLIKTE)).toBeInTheDocument();
    expect(gkMock.ibra).not.toHaveBeenCalled();
    await user.type(within(yk).getByLabelText("Ret oyu"), "3");
    await user.type(
      within(pencere).getByLabelText(/İbra edilmeyen muhasebe evrakı/),
      "Uydurma: 12 numaralı fatura.",
    );
    await user.click(within(pencere).getByRole("button", { name: DUGME_IBRA }));
    expect(gkMock.ibra).toHaveBeenCalledWith(15, {
      yk: { votes_for: 15, votes_against: 3, present_count: null },
      dk: null,
      unaudited_documents_note: "Uydurma: 12 numaralı fatura.",
    });
  });

  it("aday: kişi zorunlu; Denetleme Kuruluna veli koltuğu gider", async () => {
    const user = userEvent.setup();
    gkMock.ayrinti.mockResolvedValue(kurul(YAPILDI));
    gkMock.aday.mockResolvedValue(uyelik({ id: 70, person: 31 }));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_ADAY }));
    const pencere = screen.getByRole("dialog", { name: ADAY_PENCERESI_BASLIGI });
    await user.click(within(pencere).getByRole("button", { name: DUGME_ADAY }));
    expect(within(pencere).getByText(KISI_SECIN)).toBeInTheDocument();
    expect(gkMock.aday).not.toHaveBeenCalled();
    await user.type(within(pencere).getByRole("combobox", { name: /Kişi/ }), "Deniz");
    await user.click(await within(pencere).findByRole("option", { name: /Deniz Uydurma/ }));
    await user.selectOptions(within(pencere).getByLabelText("Kurul"), "DK");
    await user.click(within(pencere).getByRole("button", { name: DUGME_ADAY }));
    expect(gkMock.aday).toHaveBeenCalledWith(5, {
      person: 31,
      organ: "DK",
      seat_type: "ASIL",
      seat_group: "VELI",
    });
    await waitFor(() => expect(gkMock.ayrinti).toHaveBeenCalledTimes(2));
  });

  it("seçim: oy ve yedek sırası doğrulanır; seçilenler, sıra ve biçim gider", async () => {
    const user = userEvent.setup();
    const adaylar = [
      uyelik({ id: 51, person: 31, person_name: "Deniz Uydurma" }),
      uyelik({ id: 52, person: 32, person_name: "Ece Örnekçi", seat_type: "YEDEK" }),
      // Öteki kurulun adayı bu pencereye girmez.
      uyelik({ id: 53, person: 33, person_name: "Fikret Örnek", organ: "DK" }),
    ];
    gkMock.ayrinti.mockResolvedValue(kurul({ ...YAPILDI, adaylar }));
    gkMock.secim.mockResolvedValue({ ...sonuc(kurul({ ...YAPILDI, adaylar })), madde: GUNDEM[5] });
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_SECIM }));
    const pencere = screen.getByRole("dialog", { name: SECIM_PENCERESI_BASLIGI });
    expect(within(pencere).queryByText(/Fikret Örnek/)).toBeNull();
    const oylar = within(pencere).getAllByLabelText("Oy");
    await user.type(oylar[0], "3o");
    await user.click(within(pencere).getByRole("button", { name: DUGME_SECIM }));
    expect(within(pencere).getByText(SAYI_GECERSIZ)).toBeInTheDocument();
    expect(gkMock.secim).not.toHaveBeenCalled();
    await user.clear(oylar[0]);
    await user.type(oylar[0], "30");
    await user.type(oylar[1], "12");
    await user.click(within(pencere).getAllByRole("checkbox", { name: "Seçildi" })[0]);
    await user.type(within(pencere).getAllByLabelText("Yedek sırası")[1], "2");
    await user.click(within(pencere).getByRole("checkbox", { name: "Açık oyla seçildi" }));
    await user.click(within(pencere).getByRole("button", { name: DUGME_SECIM }));
    expect(gkMock.secim).toHaveBeenCalledWith(16, {
      adaylar: [
        { uyelik: 51, votes: 30, secildi: true, seat_order: null },
        { uyelik: 52, votes: 12, secildi: false, seat_order: 2 },
      ],
      liste: true,
      acik_oy: false,
    });
  });

  it("tutanağın bilgileri: yalnız değişen alan gider", async () => {
    const user = userEvent.setup();
    const tutanakli = kurul({
      ...YAPILDI,
      tutanak: {
        yk_report_reader: { id: 31, ad: "Deniz Uydurma" },
        dk_report_reader: null,
        budget_presenter: null,
        unaudited_documents_note: "",
        handed_to_new_yk_on: null,
      },
    });
    gkMock.ayrinti.mockResolvedValue(tutanakli);
    gkMock.tutanak.mockResolvedValue(sonuc(tutanakli));
    bas("sekreter");
    await user.click(await screen.findByRole("button", { name: DUGME_TUTANAK_BILGILERI }));
    const pencere = screen.getByRole("dialog", { name: TUTANAK_BILGILERI_BASLIGI });
    fireEvent.change(
      within(pencere).getByLabelText("Tutanağın yeni yönetim kuruluna teslim günü"),
      { target: { value: "2026-11-06" } },
    );
    await user.click(within(pencere).getByRole("button", { name: "Kaydet" }));
    expect(gkMock.tutanak).toHaveBeenCalledWith(5, { handed_to_new_yk_on: "2026-11-06" });
  });
});

// ---------------------------------------------------------------- Organlar → Denetleme Kurulu

describe("Organlar → Denetleme Kurulu: olağanüstü çağrı ve raporun eki", () => {
  function basDk() {
    return render(
      <YetkiDegeri value={hazirYetki(["dk_genel_kurul_yazma"])}>
        <MemoryRouter>
          <SnackbarProvider>
            <DkGenelKurulBolumu />
          </SnackbarProvider>
        </MemoryRouter>
      </YetkiDegeri>,
    );
  }

  it("planlanmış olağanüstü genel kurul yoksa yalnız açıklama", async () => {
    gkMock.liste.mockResolvedValue({ ...LISTE, kayitlar: [] });
    basDk();
    expect(await screen.findByText(DK_CAGRI_GENEL_KURUL_YOK)).toBeInTheDocument();
  });

  it("md. 6 işareti olmadan çağrı gitmez; rapor aynı istekte", async () => {
    const user = userEvent.setup();
    const olaganustu = kurul({
      id: 8,
      kind: "OLAGANUSTU",
      opens_term: null,
      gundem: [madde(41, 1, "DK_RAPORU", "Denetleme Kurulu raporu")],
      oturum: {
        cagiranlar: [{ called_by: "DENETLEME_KURULU", yol: "dk" }],
        uretilebilir_belgeler: [],
      },
    });
    gkMock.liste.mockResolvedValue({
      ...LISTE,
      kayitlar: [{ ...LISTE.kayitlar[0], id: 8, kind: "OLAGANUSTU" }],
    });
    gkMock.ayrinti.mockResolvedValue(olaganustu);
    gkMock.dkCagrisi.mockResolvedValue(sonuc({ ...olaganustu, status: "CAGRILDI" }));
    basDk();
    await user.click(await screen.findByRole("button", { name: "Olağanüstü genel kurul çağrısı" }));
    const pencere = screen.getByRole("dialog");
    await user.type(within(pencere).getByLabelText(/Çağrı nedeni/), "Uydurma aykırılık.");
    await user.type(within(pencere).getByLabelText("Gündem maddesi 1"), "Yönetim kurulu seçimi");
    fireEvent.change(within(pencere).getByLabelText(/Raporun günü/), {
      target: { value: "2026-11-20" },
    });
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI }));
    expect(within(pencere).getByText(MD6_ISARETI_ZORUNLU)).toBeInTheDocument();
    expect(gkMock.dkCagrisi).not.toHaveBeenCalled();
    await user.click(within(pencere).getByRole("checkbox", { name: /6\. maddesine aykırılık/ }));
    await user.click(within(pencere).getByRole("button", { name: DUGME_CAGRI }));
    expect(gkMock.dkCagrisi).toHaveBeenCalledWith(8, {
      call_reason: "Uydurma aykırılık.",
      gundem: [{ title: "Yönetim kurulu seçimi", kind: "DIGER" }],
      rapor: {
        kind: "ARA",
        report_date: "2026-11-20",
        md6_violation_found: true,
        irregularity_found: false,
      },
    });
    await waitFor(() => expect(gkMock.liste).toHaveBeenCalledTimes(2));
    // Raporun eki Denetleme Kurulunun ucundan.
    expect(screen.getByLabelText(/Dosya ekle/)).toBeInTheDocument();
  });
});
