// Kişiler sayfası testi: sekmeli liste, KVKK gereği TCKN'nin listede
// GÖRÜNMEMESİ, gecikmeli arama, elle ekleme/düzenleme/silme akışı (alan hataları
// backend `fields`'tan), boş/hata durumları ve içe aktarma paneli (önizle → aktar,
// already_imported uyarısı, şablon indirme). Cinsiyet, fotoğraf ve BEP bu
// programda yoktur; geri gelmesinler diye ayrıca sabitlenir. Öğrenciler sekmesi F1b 5.
// adımda öğrenci sicili ile söküldü: onun türden bağımsız sınamaları (liste, form, ayrılış,
// silme, okunamayan alan, 409) personel sekmesi üzerinden yürür. Sekme URL'de tutulur
// (`?tab=personel`), bu yüzden sayfa yönlendirici içinde kurulur.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { saveBlob } from "../../lib/download";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { Personnel, PersonnelImportReport, PersonnelListParams } from "../okul/api";

const okulApiMock = vi.hoisted(() => ({
  listPersonnel: vi.fn(),
  createPersonnel: vi.fn(),
  updatePersonnel: vi.fn(),
  deletePersonnel: vi.fn(),
  leavePersonnel: vi.fn(),
  mergePersonnel: vi.fn(),
  getLeavePool: vi.fn(),
  resolveLeavePool: vi.fn(),
  previewPersonnelImport: vi.fn(),
  commitPersonnelImport: vi.fn(),
  personnelTemplate: vi.fn(),
  getSchoolConfig: vi.fn(),
  getParentRoster: vi.fn(),
  deleteParentRoster: vi.fn(),
  previewParentImport: vi.fn(),
  commitParentImport: vi.fn(),
  parentTemplate: vi.fn(),
}));

// Yalnız `okulApi` taklit edilir; etiket sabitleri + importCounts gerçek kalır
// (sayfa ile api katmanı arasındaki sözleşme sahte veriyle örtülmesin).
vi.mock("../okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../okul/api")>();
  return { ...actual, okulApi: okulApiMock };
});

vi.mock("../../lib/download", () => ({ saveBlob: vi.fn() }));

import { YETENEK_ADLARI } from "../oturum/api";
import type { OturumOzeti } from "../oturum/api";
import { OTURUM_SORGU_ANAHTARI } from "../oturum/useOturum";
import { YetkiDegeri, hazirYetki } from "../oturum/yetki";
import { ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import KisilerPage from "./KisilerPage";
import { DOSYA_ALANI_ETIKETI, VELI_LISTESI_SEKMESI } from "./metinler";

const PERSONNEL: Personnel = {
  id: 5,
  first_name: "Mehmet",
  last_name: "Demirci",
  full_name: "Mehmet Demirci",
  member_kind: "OGRETMEN",
  is_active: true,
  left_at: null,
  leave_candidate_since: null,
};

const PREVIEW_REPORT: PersonnelImportReport = {
  file_hash: "abc",
  file_name: "",
  total_rows: 4,
  processed: 3,
  created_personnel: 2,
  updated_personnel: 1,
  unchanged_personnel: 0,
  reactivated_personnel: 0,
  pool_added_personnel: 0,
  pool_removed_personnel: 0,
  similar_pair_count: 0,
  already_imported: false,
  dry_run: true,
  pool_added: [],
  similar_pairs: [],
  warnings: [
    {
      row_number: 3,
      field: "member_kind",
      issue: "Görev türünü denetleyin: görev bilgisi boş ya da tanınmadı.",
      raw_value: "",
    },
  ],
  skipped: [],
};

function page<T>(results: T[], count = results.length) {
  return { count, next: null, previous: null, results };
}

/** `route` derin bağlantıyı sınar: sekme URL'deki `tab` parametresinden okunur. Varsayılan
 *  yetenekler program yöneticisininkidir (bütün yetenekler; süzme `oturum/yetki`'den). */
function renderPage(route = "/kisiler", yetenekler: readonly string[] = YETENEK_ADLARI) {
  // Aktarım paneli yükleme sınırını oturum özetinden okur; özet önbellekte hazırdır.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  queryClient.setQueryData<OturumOzeti>(OTURUM_SORGU_ANAHTARI, {
    durum: "acik",
    hesap: null,
    bosta_dk: 10,
    bosta_kalan_sn: 600,
    kilit_bekliyor: false,
    kurulum_tamam: true,
    yukleme_siniri_mb: 20,
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <YetkiDegeri value={hazirYetki(yetenekler)}>
        <MemoryRouter initialEntries={[route]}>
          <SnackbarProvider>
            <ConfirmProvider>
              <KisilerPage />
            </ConfirmProvider>
          </SnackbarProvider>
        </MemoryRouter>
      </YetkiDegeri>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  // Gerçek `saveBlob` hep sonuç döndürür; sahte de öyle olsun.
  vi.mocked(saveBlob).mockResolvedValue("kaydedildi");
  okulApiMock.listPersonnel.mockResolvedValue(page([PERSONNEL]));
  // Aktarım panellerinin aydınlatma metni veri sorumlusunu okul kartından okur.
  okulApiMock.getSchoolConfig.mockResolvedValue({
    ...ORNEK_OKUL_KARTI,
    data_controller_text: "Örnek Anadolu Lisesi Müdürlüğü",
  });
  okulApiMock.getParentRoster.mockResolvedValue({
    total_rows: 0,
    class_count: 0,
    last_import_at: null,
    classes: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("KisilerPage — öğretmen ve diğer personel listesi", () => {
  it("liste yüklenir: ad + görev türü + durum (unvan, branş ve cinsiyet yok)", async () => {
    renderPage();

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Görev türü" })).toBeInTheDocument();
    expect(screen.getByText("Öğretmen")).toBeInTheDocument();
    expect(screen.getByText("Aktif")).toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /Unvan|Branş|Cinsiyet/ })).toBeNull();
    expect(okulApiMock.listPersonnel).toHaveBeenCalledWith({
      search: "",
      limit: 25,
      offset: 0,
    });
  });

  it("arama gecikmeli olarak sorguya yansır", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.type(screen.getByLabelText("Ara"), "demirci");

    await waitFor(() =>
      expect(okulApiMock.listPersonnel).toHaveBeenLastCalledWith(
        expect.objectContaining({ search: "demirci", offset: 0 }),
      ),
    );
  });

  it("boş liste: yönlendirici boş-durum kartı aktarımı öğütler", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(page<Personnel>([]));
    renderPage();
    expect(await screen.findByText("Gösterilecek kişi yok")).toBeInTheDocument();
    expect(screen.getByText(/e-Okul personel listesini aşağıdaki panelden/)).toBeInTheDocument();
  });

  it("hata: backend Türkçe mesajı hata bandında gösterilir; bant canlı bölgedir", async () => {
    okulApiMock.listPersonnel.mockRejectedValue(
      new ApiError(500, "server_error", "Sicil okunamadı."),
    );
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("Sicil okunamadı.");
  });

  it("ayrılış havuzundaki kişide “Ayrılış kararı bekliyor” rozeti görünür", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(
      page([{ ...PERSONNEL, leave_candidate_since: "2026-09-22" }]),
    );
    renderPage();

    expect(await screen.findByText("Ayrılış kararı bekliyor")).toBeInTheDocument();
    expect(screen.getByText("Aktif")).toBeInTheDocument();
  });
});

describe("KisilerPage — ekleme/düzenleme/silme", () => {
  it("zorunlu alan boşken istek atılmaz, hata alanın altında görünür", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: "Kişi ekle" }));
    const dialog = await screen.findByRole("dialog", { name: "Yeni kişi" });
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    expect(await within(dialog).findByText("Ad zorunludur.")).toBeInTheDocument();
    expect(within(dialog).getByText("Soyad zorunludur.")).toBeInTheDocument();
    expect(okulApiMock.createPersonnel).not.toHaveBeenCalled();
  });

  // docs/sozluk.md "Personelin türü": ekranda "Görev türü" (öğretmen · yönetici · diğer personel;
  // "üye" denmez, md. 4/1-e); "personel" tek başına yalnız e-Okul raporunun adında
  // ("Personel Listesi raporu") geçer.
  it("ekleme diyaloğu görev türü sorar; unvan, branş ve cinsiyet alanı yoktur", async () => {
    okulApiMock.createPersonnel.mockResolvedValue({ ...PERSONNEL, member_kind: "DIGER" });
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Kişi ekle" }));

    const dialog = await screen.findByRole("dialog", { name: "Yeni kişi" });
    expect(within(dialog).queryByLabelText("Unvan")).toBeNull();
    expect(within(dialog).queryByLabelText("Branş")).toBeNull();
    expect(within(dialog).queryByLabelText("Cinsiyet")).toBeNull();
    // Görev türünün yardım metni ödünç sınırından söz etmez (OAB'de ödünç yoktur).
    expect(within(dialog).getByText("Unvan ve branş tutulmaz.")).toBeInTheDocument();
    expect(dialog.textContent).not.toMatch(/ödünç/i);
    const tur = within(dialog).getByLabelText("Görev türü");
    expect(tur).toHaveValue("OGRETMEN");
    expect(
      within(tur)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Öğretmen", "Yönetici", "Diğer personel"]);
    expect(dialog.textContent).not.toMatch(/üye türü/i);
    await user.type(within(dialog).getByLabelText(/^Ad \*$/), "Mehmet");
    await user.type(within(dialog).getByLabelText(/^Soyad \*$/), "Demirci");
    await user.selectOptions(within(dialog).getByLabelText("Görev türü"), "DIGER");
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    await waitFor(() =>
      expect(okulApiMock.createPersonnel).toHaveBeenCalledWith({
        first_name: "Mehmet",
        last_name: "Demirci",
        member_kind: "DIGER",
      }),
    );
    expect(okulApiMock.createPersonnel.mock.calls[0][0]).not.toHaveProperty("gender");
    expect(await screen.findByText("Kayıt eklendi.")).toBeInTheDocument();
    expect(screen.queryByText(/Personel eklendi/)).not.toBeInTheDocument();
    // e-Okul raporunun ADI değişmez.
    expect(screen.getByText(/OOK01001R1 — Personel Listesi raporunu/)).toBeInTheDocument();
  });

  it("düzenlemede değişiklik updatePersonnel'a gider ve liste tazelenir", async () => {
    okulApiMock.updatePersonnel.mockResolvedValue({ ...PERSONNEL, member_kind: "DIGER" });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));
    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    // Satıra tıklama düzenleme formunu açar; alanlar dolu gelir.
    expect(within(dialog).getByLabelText(/^Ad \*$/)).toHaveValue("Mehmet");
    await user.selectOptions(within(dialog).getByLabelText("Görev türü"), "DIGER");
    const onceki = okulApiMock.listPersonnel.mock.calls.length;
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    await waitFor(() =>
      expect(okulApiMock.updatePersonnel).toHaveBeenCalledWith(
        5,
        expect.objectContaining({ member_kind: "DIGER" }),
      ),
    );
    expect(await screen.findByText("Kayıt güncellendi.")).toBeInTheDocument();
    await waitFor(() =>
      expect(okulApiMock.listPersonnel.mock.calls.length).toBeGreaterThan(onceki),
    );
  });

  it("backend alan hatası (fields) ilgili alanın altına yazılır", async () => {
    okulApiMock.createPersonnel.mockRejectedValue(
      new ApiError(400, "validation_error", "Girdiğiniz bilgileri kontrol edin.", {
        member_kind: ["Geçerli bir seçenek seçin."],
      }),
    );
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: "Kişi ekle" }));
    const dialog = await screen.findByRole("dialog", { name: "Yeni kişi" });
    await user.type(within(dialog).getByLabelText(/^Ad \*$/), "Zeynep");
    await user.type(within(dialog).getByLabelText(/^Soyad \*$/), "Kaya");
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    expect(await within(dialog).findByText("Geçerli bir seçenek seçin.")).toBeInTheDocument();
    expect(within(dialog).getByText("Girdiğiniz bilgileri kontrol edin.")).toBeInTheDocument();
  });

  it("409 parola_gerekli: ileti okunaklı gösterilir ve kurulum sihirbazına bağlanır", async () => {
    okulApiMock.createPersonnel.mockRejectedValue(
      new ApiError(
        409,
        "parola_gerekli",
        "Kişi kaydı için önce program yöneticisi hesabını kurun (Kurulum Sihirbazı'nın ilk adımı).",
      ),
    );
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: "Kişi ekle" }));
    const dialog = await screen.findByRole("dialog", { name: "Yeni kişi" });
    await user.type(within(dialog).getByLabelText(/^Ad \*$/), "Zeynep");
    await user.type(within(dialog).getByLabelText(/^Soyad \*$/), "Kaya");
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    const bant = await within(dialog).findByRole("alert");
    expect(within(bant).getByText("Önce program yöneticisi hesabını kurun")).toBeInTheDocument();
    expect(within(bant).getByText(/Kurulum Sihirbazı'nın ilk adımı/)).toBeInTheDocument();
    expect(within(bant).getByRole("link", { name: "Kurulum sihirbazını aç" })).toHaveAttribute(
      "href",
      "/kurulum",
    );
  });

  it("silme onayı başlıklıdır ve kalıcı olduğunu söyler", async () => {
    okulApiMock.deletePersonnel.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));

    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Sil" }));

    // Başlık soru, gövde sonuç; silme KALICIDIR ve ayrılış yolu ayrıca gösterilir.
    const onay = await screen.findByRole("dialog", { name: "Kişi sicilden silinsin mi?" });
    expect(within(onay).getByText(/kalıcı olarak silinir/)).toBeInTheDocument();
    expect(within(onay).getByText(/Ayrıldı olarak işaretle/)).toBeInTheDocument();
    expect(within(onay).queryByText(/gözetmen|görevlendirme|soft delete/)).not.toBeInTheDocument();
    await user.click(within(onay).getByRole("button", { name: "Sil" }));

    await waitFor(() => expect(okulApiMock.deletePersonnel).toHaveBeenCalledWith(5));
    expect(await screen.findByText("Kayıt silindi.")).toBeInTheDocument();
  });

  it("son sayfadaki tek kayıt silinince önceki sayfaya düşer (boş sayfada kilitlenmez)", async () => {
    const SON_KAYIT: Personnel = {
      ...PERSONNEL,
      id: 9,
      first_name: "Zeynep",
      last_name: "Kaya",
      full_name: "Zeynep Kaya",
    };
    // İkinci sayfada tek kayıt var; silinince o sayfa boşalır (count 26 → 25).
    let silindi = false;
    okulApiMock.listPersonnel.mockImplementation((params: PersonnelListParams) =>
      Promise.resolve(
        (params.offset ?? 0) === 0
          ? page([PERSONNEL], silindi ? 25 : 26)
          : silindi
            ? page<Personnel>([], 25)
            : page([SON_KAYIT], 26),
      ),
    );
    okulApiMock.deletePersonnel.mockImplementation(() => {
      silindi = true;
      return Promise.resolve(undefined);
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: /Sonraki/ }));
    await screen.findByText("Zeynep Kaya");

    await user.click(screen.getByRole("button", { name: "Zeynep Kaya kaydını düzenle" }));
    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Sil" }));
    const confirmDialog = await screen.findByRole("dialog", {
      name: "Kişi sicilden silinsin mi?",
    });
    await user.click(within(confirmDialog).getByRole("button", { name: "Sil" }));

    // Önceki sayfa yeniden yüklenir: liste dolu ve sayfalama çubuğu yerinde.
    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.queryByText("Gösterilecek kişi yok")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Önceki/ })).toBeDisabled();
  });
});

describe("KisilerPage — ayrılış", () => {
  it("ayrıldı olarak işaretleme onaylı yapılır; kaydın silinmediği söylenir", async () => {
    okulApiMock.leavePersonnel.mockResolvedValue({
      ...PERSONNEL,
      is_active: false,
      left_at: "2026-09-22",
    });
    const user = userEvent.setup();
    renderPage("/kisiler?tab=personel");
    await user.click(await screen.findByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));

    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Ayrıldı olarak işaretle" }));
    const onay = await screen.findByRole("dialog", {
      name: "Kişi ayrıldı olarak işaretlensin mi?",
    });
    expect(within(onay).getByText(/Kaydı silinmez/)).toBeInTheDocument();
    expect(within(onay).queryByText(/hemen silinir/)).toBeNull();
    await user.click(within(onay).getByRole("button", { name: "Ayrıldı olarak işaretle" }));

    await waitFor(() => expect(okulApiMock.leavePersonnel).toHaveBeenCalledWith(5));
    expect(await screen.findByText("Kişi ayrıldı olarak işaretlendi.")).toBeInTheDocument();
    expect(screen.queryByText(/kaydı silindi/)).toBeNull();
  });

  it("ayrılış onayından vazgeçilirse istek atılmaz", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));

    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Ayrıldı olarak işaretle" }));
    const onay = await screen.findByRole("dialog", {
      name: "Kişi ayrıldı olarak işaretlensin mi?",
    });
    await user.click(within(onay).getByRole("button", { name: "Vazgeç" }));

    expect(okulApiMock.leavePersonnel).not.toHaveBeenCalled();
  });

  it("ayrılış hatası diyalogda gösterilir", async () => {
    okulApiMock.leavePersonnel.mockRejectedValue(
      new ApiError(400, "validation_error", "Bu kişi zaten ayrıldı olarak işaretli."),
    );
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));

    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Ayrıldı olarak işaretle" }));
    const onay = await screen.findByRole("dialog", {
      name: "Kişi ayrıldı olarak işaretlensin mi?",
    });
    await user.click(within(onay).getByRole("button", { name: "Ayrıldı olarak işaretle" }));

    expect(
      await within(dialog).findByText("Bu kişi zaten ayrıldı olarak işaretli."),
    ).toBeInTheDocument();
  });

  it("ayrılmış kişide rozet görünür, ayrılış eylemi sunulmaz", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(
      page([{ ...PERSONNEL, is_active: false, left_at: "2026-06-20" }]),
    );
    const user = userEvent.setup();
    renderPage("/kisiler?tab=personel");

    expect(await screen.findByText("Ayrıldı · 20.06.2026")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Mehmet Demirci kaydını düzenle" }));
    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    expect(
      within(dialog).queryByRole("button", { name: "Ayrıldı olarak işaretle" }),
    ).not.toBeInTheDocument();
    expect(within(dialog).getByText("Ayrıldı · 20.06.2026")).toBeInTheDocument();
  });
});

describe("KisilerPage — sekmeler", () => {
  it("sekmeler: personel sicili, Ayrılış Havuzu ve Veli Listesi (öğrenci, BEP ve fotoğraf yok)", async () => {
    renderPage();
    await screen.findByText("Mehmet Demirci");

    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      expect.stringContaining("Öğretmenler ve Diğer Personel"),
      expect.stringContaining("Ayrılış Havuzu"),
      expect.stringContaining(VELI_LISTESI_SEKMESI),
    ]);
    expect(screen.queryByRole("tab", { name: /Öğrenci|BEP/ })).toBeNull();
    expect(screen.queryByText(/fotoğraf/i)).toBeNull();
    // Sayfanın açıklaması öğrenci sicilinden söz etmez; veli listesini anar ("veli bilgisi
    // tutulmaz" ibaresi T5 ile kalktı).
    expect(
      screen.getByText(/^Öğretmen ve diğer personel sicili ve veli listesi\. Personel/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/veli bilgisi/)).toBeNull();
  });

  it("derin bağlantı: /kisiler?tab=veli Veli Listesi sekmesini açar (ad yok, sayı var)", async () => {
    okulApiMock.getParentRoster.mockResolvedValue({
      total_rows: 3,
      class_count: 2,
      last_import_at: "2026-11-08T10:00:00+03:00",
      classes: [
        { student_class: "9-A", rows: 2 },
        { student_class: "10-B", rows: 1 },
      ],
    });
    renderPage("/kisiler?tab=veli");

    expect(await screen.findByRole("cell", { name: "9-A" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: new RegExp(VELI_LISTESI_SEKMESI) })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(okulApiMock.listPersonnel).not.toHaveBeenCalled();
  });

  it("derin bağlantı: /kisiler?tab=havuz Ayrılış Havuzu sekmesini açar", async () => {
    okulApiMock.getLeavePool.mockResolvedValue({ personnel_count: 0, personnel: [] });
    renderPage("/kisiler?tab=havuz");

    expect(await screen.findByText("Ayrılış kararı bekleyen kişi yok")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Ayrılış Havuzu/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(okulApiMock.listPersonnel).not.toHaveBeenCalled();
  });

  it("derin bağlantı: /kisiler?tab=personel doğrudan Öğretmenler sekmesini açar", async () => {
    renderPage("/kisiler?tab=personel");

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Öğretmenler/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("geçersiz ya da kaldırılmış sekme parametresi sessizce personel sekmesine düşer", async () => {
    for (const eski of ["bep", "ogrenciler"]) {
      const { unmount } = renderPage(`/kisiler?tab=${eski}`);

      expect(await screen.findByText("Öğretmen ve Diğer Personel Sicili")).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /Öğretmenler/ })).toHaveAttribute(
        "aria-selected",
        "true",
      );
      unmount();
    }
  });
});

describe("KisilerPage — içe aktarma paneli", () => {
  it("yapıştırılan metin: önizleme raporu gösterilir, Aktar önizlemeden önce kapalıdır", async () => {
    okulApiMock.previewPersonnelImport.mockResolvedValue(PREVIEW_REPORT);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    expect(screen.getByRole("button", { name: "Aktar" })).toBeDisabled();

    await user.type(screen.getByLabelText("Ya da tabloyu yapıştırın"), "ad\tsoyad");
    await user.click(screen.getByRole("button", { name: /Önizle/ }));

    await waitFor(() =>
      expect(okulApiMock.previewPersonnelImport).toHaveBeenCalledWith({ text: "ad\tsoyad" }),
    );
    expect(await screen.findByText("Önizleme — hiçbir kayıt yazılmadı")).toBeInTheDocument();
    expect(screen.getByText("Uyarılar (1)")).toBeInTheDocument();
    expect(
      screen.getByText("Görev türünü denetleyin: görev bilgisi boş ya da tanınmadı."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aktar" })).toBeEnabled();
  });

  it("aktar: commit sonrası liste tazelenir ve already_imported uyarısı görünür", async () => {
    okulApiMock.previewPersonnelImport.mockResolvedValue(PREVIEW_REPORT);
    okulApiMock.commitPersonnelImport.mockResolvedValue({
      ...PREVIEW_REPORT,
      dry_run: false,
      already_imported: true,
      warnings: [],
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.type(screen.getByLabelText("Ya da tabloyu yapıştırın"), "ad\tsoyad");
    await user.click(screen.getByRole("button", { name: /Önizle/ }));
    await screen.findByText("Önizleme — hiçbir kayıt yazılmadı");

    const callsBefore = okulApiMock.listPersonnel.mock.calls.length;
    await user.click(screen.getByRole("button", { name: "Aktar" }));

    await waitFor(() =>
      expect(okulApiMock.commitPersonnelImport).toHaveBeenCalledWith({ text: "ad\tsoyad" }),
    );
    expect(await screen.findByText("İçe aktarma sonucu")).toBeInTheDocument();
    expect(await screen.findByText(/daha önce aktarılmış/)).toBeInTheDocument();
    await waitFor(() =>
      expect(okulApiMock.listPersonnel.mock.calls.length).toBeGreaterThan(callsBefore),
    );
    expect(screen.queryByText(/zümre/i)).toBeNull();
    expect(screen.queryByRole("link", { name: /Zümreler/ })).toBeNull();
  });

  it("aktarım paneli öğrenci aktarımından söz etmez; tam liste onayı yoktur", async () => {
    renderPage();
    await screen.findByText("Mehmet Demirci");
    expect(screen.queryByText(/OOG01001R020|Öğrenci Aktar|Cinsiyet ve pansiyon/)).toBeNull();
    expect(screen.queryByLabelText(/Bu dosya okulun tam listesidir/)).toBeNull();
    expect(screen.queryByText(/ayrışma/)).toBeNull();
  });

  it("önizleme hatası: backend mesajı bantta görünür, Aktar kapalı kalır", async () => {
    okulApiMock.previewPersonnelImport.mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Dosya (file) veya metin (text) alanlarından biri gerekli.",
      ),
    );
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.type(screen.getByLabelText("Ya da tabloyu yapıştırın"), "x");
    await user.click(screen.getByRole("button", { name: /Önizle/ }));

    expect(
      await screen.findByText("Dosya (file) veya metin (text) alanlarından biri gerekli."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aktar" })).toBeDisabled();
  });

  it("dosya seçimi kaldırılınca yapıştırma alanı yeniden etkinleşir", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    const dosyaAlani = screen.getByLabelText(DOSYA_ALANI_ETIKETI) as HTMLInputElement;
    // e-Okul ihracı BÜYÜK harfli .XLS uzantısıyla iner — seçici onu da kabul etmeli.
    expect(dosyaAlani.accept).toContain(".xls");
    await user.upload(dosyaAlani, new File(["x"], "OOK01001R1_826.XLS"));
    expect(screen.getByLabelText("Ya da tabloyu yapıştırın")).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /Dosyayı kaldır/ }));

    expect(screen.getByLabelText("Ya da tabloyu yapıştırın")).toBeEnabled();
    expect(dosyaAlani.files?.length ?? 0).toBe(0);
  });

  it("şablon indir: blob dosya olarak kaydedilir", async () => {
    const blob = new Blob(["x"]);
    okulApiMock.personnelTemplate.mockResolvedValue(blob);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText("Mehmet Demirci");

    await user.click(screen.getByRole("button", { name: "Şablon indir" }));

    await waitFor(() => expect(saveBlob).toHaveBeenCalledWith(blob, "sablon-personel.xlsx"));
  });
});

// Çözülemeyen şifreli alan (tasarım TK8 (3), §13 D48): API'de alan `null` gelir ve
// kaydın `bozuk_alanlar` listesinde durur; ekran boş hücre değil "okunamadı" yazar.
describe("KisilerPage — okunamayan şifreli alan", () => {
  const BOZUK_PERSONEL: Personnel = {
    ...PERSONNEL,
    id: 2,
    last_name: null,
    full_name: null,
    bozuk_alanlar: ["last_name"],
  };

  it("listede ad “okunamadı” görünür; satırın adı kişi adı tahmin etmez", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(page([PERSONNEL, BOZUK_PERSONEL]));
    renderPage();
    await screen.findByText("Mehmet Demirci");

    expect(screen.getAllByText("okunamadı")).toHaveLength(1);
    expect(document.body.textContent).not.toMatch(/null/);
    expect(
      screen.getByRole("button", { name: "Adı okunamayan kaydı düzenle" }),
    ).toBeInTheDocument();
  });

  it("düzenlemede okunamayan alan boş açılır ve yardım metni söyler", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(page([BOZUK_PERSONEL]));
    okulApiMock.updatePersonnel.mockResolvedValue({ ...BOZUK_PERSONEL });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Adı okunamayan kaydı düzenle" }));
    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    expect(within(dialog).getByLabelText(/^Soyad \*$/)).toHaveValue("");
    expect(
      within(dialog).getByText("Kayıtlı değer okunamadı; kaydetmek için yeniden yazın."),
    ).toBeInTheDocument();

    // Soyad zorunludur: okunamayan değer ancak yeniden yazılarak kaydedilir.
    await user.type(within(dialog).getByLabelText(/^Soyad \*$/), "Kaya");
    await user.click(within(dialog).getByRole("button", { name: "Kaydet" }));

    await waitFor(() => expect(okulApiMock.updatePersonnel).toHaveBeenCalledTimes(1));
    const govde = okulApiMock.updatePersonnel.mock.calls[0][1] as Record<string, unknown>;
    expect(govde.last_name).toBe("Kaya");
  });

  it("silme onayı adı okunamayan kaydı adsız anar", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(page([BOZUK_PERSONEL]));
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Adı okunamayan kaydı düzenle" }));
    const dialog = await screen.findByRole("dialog", { name: "Kişiyi düzenle" });
    await user.click(within(dialog).getByRole("button", { name: "Sil" }));
    const onay = await screen.findByRole("dialog", { name: "Kişi sicilden silinsin mi?" });
    expect(onay).toHaveTextContent("Adı okunamayan bu kayıt kalıcı olarak silinir");
    expect(onay).not.toHaveTextContent("null");
  });
});

describe("KisilerPage — rol süzmesi (personeli her rol okur)", () => {
  it("yazma yeteneği olmayan rolde yalnız personel sekmesi açılır; liste salt okurdur", async () => {
    // Denetleme Kurulunun yetenekleri (sunucudan gelir gibi): Kişiler'de yazma yok.
    renderPage("/kisiler", ["butunluk_denetim", "erisim_gunlugu", "geri_yukleme_gordum"]);

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    const sekmeler = screen.getAllByRole("tab");
    expect(sekmeler).toHaveLength(1);
    expect(sekmeler[0]).toHaveAccessibleName(/Öğretmenler ve Diğer Personel/);
    expect(okulApiMock.getLeavePool).not.toHaveBeenCalled();
    expect(screen.getByRole("note")).toHaveTextContent(
      "Bu bölüm hesabınızın rolüne yalnız okuma için açık.",
    );
    expect(screen.queryByRole("button", { name: "Kişi ekle" })).toBeNull();
    // Satır tıklanmaz: düzenleme penceresinin her eylemi yazmadır.
    expect(screen.queryByRole("button", { name: /düzenle/ })).toBeNull();
    // e-Okul aktarım paneli ve şablon yok; aydınlatma metni de yok (aktarım yok).
    expect(screen.queryByText(/Öğretmen ve Diğer Personeli Aktar/)).toBeNull();
    expect(screen.queryByRole("button", { name: /Önizle|Aktar|şablon/i })).toBeNull();
    expect(screen.queryByRole("region", { name: /aydınlatma/i })).toBeNull();
    expect(okulApiMock.getParentRoster).not.toHaveBeenCalled();
    expect(screen.getByText(/^Öğretmen ve diğer personel sicili\. TCKN/)).toBeInTheDocument();
  });

  it("veli listesi yeteneği olmayan rolde Veli Listesi sekmesi yoktur; adresi ilk sekmeye düşer", async () => {
    renderPage(
      "/kisiler?tab=veli",
      YETENEK_ADLARI.filter((ad) => ad !== "veli_listesi"),
    );

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: new RegExp(VELI_LISTESI_SEKMESI) })).toBeNull();
    expect(okulApiMock.getParentRoster).not.toHaveBeenCalled();
  });

  it("yetkisiz sekmenin adresi rolün ilk sekmesine düşer (havuz ucu çağrılmaz)", async () => {
    renderPage("/kisiler?tab=havuz", []);

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Öğretmenler/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(okulApiMock.getLeavePool).not.toHaveBeenCalled();
  });

  it("boş listede salt okur rol aktarımı öğütlemez", async () => {
    okulApiMock.listPersonnel.mockResolvedValue(page([]));
    renderPage("/kisiler", []);

    expect(await screen.findByText("Gösterilecek kişi yok")).toBeInTheDocument();
    expect(screen.queryByText(/içe aktarın/)).toBeNull();
  });

  it("program yöneticisinde üç sekme ve yazma denetimleri durur", async () => {
    const user = userEvent.setup();
    renderPage("/kisiler?tab=personel");

    expect(await screen.findByText("Mehmet Demirci")).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Kişi ekle" })).toBeInTheDocument();
    expect(screen.queryByRole("note")).toBeNull();
    await user.click(screen.getByRole("button", { name: /Mehmet Demirci.*düzenle/ }));
    expect(await screen.findByRole("dialog", { name: "Kişiyi düzenle" })).toBeInTheDocument();
  });

  it("özet yüklenirken sekme ve liste çizilmez (yanlış sekme bir an açılmaz)", async () => {
    render(
      <MemoryRouter initialEntries={["/kisiler"]}>
        <SnackbarProvider>
          <ConfirmProvider>
            <KisilerPage />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { level: 1, name: "Kişiler" })).toBeInTheDocument();
    expect(screen.queryByRole("tab")).toBeNull();
    expect(okulApiMock.listPersonnel).not.toHaveBeenCalled();
  });
});
