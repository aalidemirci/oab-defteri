// `okul` API katmanı — kapalı gün, kişi ayrılışı/birleştirme, aktarım ve okul kartı uçları;
// okul kartının seçenek adları (`*_TR`, backend enum etiketleriyle birebir).
// Backend `apps/okul/urls.py` ile yol ve gövde hizası burada pinlenir (sessiz 404 /
// yanlış yıl süzgeci yakalanır).

import { afterEach, describe, expect, it, vi } from "vitest";

const apiMock = vi.hoisted(() => ({
  get: vi.fn(() => Promise.resolve([])),
  post: vi.fn(() => Promise.resolve({})),
  put: vi.fn(() => Promise.resolve({})),
  patch: vi.fn(() => Promise.resolve({})),
  del: vi.fn(() => Promise.resolve(undefined)),
  postForm: vi.fn(() => Promise.resolve({})),
  getBlob: vi.fn(() => Promise.resolve(new Blob())),
}));

vi.mock("../../lib/api", () => ({
  api: apiMock,
  ApiError: class ApiError extends Error {},
}));

import {
  CANTEEN_MODE_TR,
  HOLIDAY_KIND_TR,
  MEMBER_KIND_TR,
  SCHOOL_LEVEL_TR,
  SETTLEMENT_TYPE_TR,
  STAFFING_MODE_TR,
  okulApi,
} from "./api";

afterEach(() => vi.clearAllMocks());

describe("okulApi — kapalı günler", () => {
  it("listHolidays yıl verilince ?year= ile, verilmezse süzgeçsiz ister", async () => {
    await okulApi.listHolidays(2027);
    expect(apiMock.get).toHaveBeenLastCalledWith("/holidays/?year=2027");
    await okulApi.listHolidays();
    expect(apiMock.get).toHaveBeenLastCalledWith("/holidays/");
  });

  it("createHoliday → POST /holidays/ (tahmini bayrağı gönderilmez)", async () => {
    const govde = {
      name: "Yarıyıl tatili",
      start_date: "2027-01-25",
      end_date: "2027-02-05",
      kind: "SCHOOL_BREAK" as const,
    };
    await okulApi.createHoliday(govde);
    expect(apiMock.post).toHaveBeenCalledWith("/holidays/", govde);
  });

  it("deleteHoliday → DELETE /holidays/<id>/", async () => {
    await okulApi.deleteHoliday(7);
    expect(apiMock.del).toHaveBeenCalledWith("/holidays/7/");
  });

  it("seedHolidays → POST /holidays/seed/ { year }", async () => {
    await okulApi.seedHolidays(2026);
    expect(apiMock.post).toHaveBeenCalledWith("/holidays/seed/", { year: 2026 });
  });

  it("tür adları sözlüğe uyar: ara tatil “öğrenciye kapalı gün”dür", () => {
    expect(HOLIDAY_KIND_TR.SCHOOL_BREAK).toBe("Öğrenciye kapalı gün");
    expect(HOLIDAY_KIND_TR.OFFICIAL).toBe("Resmî tatil");
    expect(Object.values(HOLIDAY_KIND_TR)).not.toContain("Tatil");
  });
});

describe("okulApi — kişi ayrılışı, birleştirme ve mutabakat seçenekleri", () => {
  it("leaveStudent / leavePersonnel → POST …/<id>/leave/ (gövdesiz)", async () => {
    await okulApi.leaveStudent(3);
    expect(apiMock.post).toHaveBeenLastCalledWith("/students/3/leave/");
    await okulApi.leavePersonnel(4);
    expect(apiMock.post).toHaveBeenLastCalledWith("/personnel/4/leave/");
  });

  it("mergePersonnel → POST /personnel/<kaynak>/merge/ { into_id: hedef }", async () => {
    await okulApi.mergePersonnel(11, 21);
    expect(apiMock.post).toHaveBeenCalledWith("/personnel/11/merge/", { into_id: 21 });
  });

  it("metin yolunda tam liste seçeneği JSON gövdeye yalnız anlamlıysa girer", async () => {
    await okulApi.previewStudentImport({ text: "x" });
    expect(apiMock.post).toHaveBeenLastCalledWith("/imports/students/preview/", { text: "x" });
    await okulApi.commitStudentImport({ text: "x" }, { fullList: true });
    expect(apiMock.post).toHaveBeenLastCalledWith("/imports/students/commit/", {
      text: "x",
      full_list: true,
    });
    // Personelde seçenek yoktur: listede olmayanlar Ayrılış Havuzu'na girer.
    await okulApi.commitPersonnelImport({ text: "x" });
    expect(apiMock.post).toHaveBeenLastCalledWith("/imports/personnel/commit/", { text: "x" });
  });

  it("dosya yolunda seçenek çok parçalı gövdeye eklenir; personelde ayrılış seçimi gitmez", async () => {
    const dosya = new File(["x"], "liste.xls");
    await okulApi.commitPersonnelImport({ file: dosya });
    const [yol, form] = apiMock.postForm.mock.calls.at(-1) as unknown as [string, FormData];
    expect(yol).toBe("/imports/personnel/commit/");
    expect(form.getAll("mark_left_ids")).toEqual([]);
    expect(form.get("file")).toBeInstanceOf(File);

    await okulApi.previewStudentImport({ file: dosya }, { fullList: true });
    const [, ogrenciFormu] = apiMock.postForm.mock.calls.at(-1) as unknown as [string, FormData];
    expect(ogrenciFormu.get("full_list")).toBe("true");
  });

  it("Ayrılış Havuzu: liste, yalnız sayılı özet ve toplu karar uçları", async () => {
    await okulApi.getLeavePool();
    expect(apiMock.get).toHaveBeenLastCalledWith("/leave-pool/");
    await okulApi.getLeavePoolSummary();
    expect(apiMock.get).toHaveBeenLastCalledWith("/leave-pool/?summary=true");
    const govde = { students: { leave: [1, 2], keep: [3] }, personnel: { keep: [9] } };
    await okulApi.resolveLeavePool(govde);
    expect(apiMock.post).toHaveBeenLastCalledWith("/leave-pool/resolve/", govde);
  });

  it("üye türü adları sözlüğe uyar: öğretmen / diğer personel", () => {
    expect(MEMBER_KIND_TR).toEqual({ TEACHER: "Öğretmen", STAFF: "Diğer personel" });
  });
});

describe("okulApi — kurulum ve başlangıç yol haritası", () => {
  it("markRoadmapItem → POST /setup/roadmap/ { item, done }", async () => {
    await okulApi.markRoadmapItem("kurtarma_zarfi", true);
    expect(apiMock.post).toHaveBeenLastCalledWith("/setup/roadmap/", {
      item: "kurtarma_zarfi",
      done: true,
    });
  });

  it("setRoadmapHidden → POST /setup/roadmap/ { hidden }", async () => {
    await okulApi.setRoadmapHidden(true);
    expect(apiMock.post).toHaveBeenLastCalledWith("/setup/roadmap/", { hidden: true });
  });

  it("updateSchoolConfig → PUT /setup/school-config/ okul kartının yeni alanlarıyla", async () => {
    const govde = {
      institution_code: "123456",
      levels: ["ILKOKUL" as const, "ORTAOKUL" as const],
      student_count: 480,
      student_count_as_of: "2026-10-01",
      settlement_type: "DIGER" as const,
      canteen_mode: "KANTIN_YOK" as const,
      staffing_mode: "HIZMET_ALIMI" as const,
      in_campus: true,
      opened_on: null,
    };
    await okulApi.updateSchoolConfig(govde);
    expect(apiMock.put).toHaveBeenLastCalledWith("/setup/school-config/", govde);
  });

  it("completeSetup → POST /setup/complete/", async () => {
    await okulApi.completeSetup();
    expect(apiMock.post).toHaveBeenLastCalledWith("/setup/complete/");
  });

  it("kademe adları sözlüğe uyar; sıra backend `SchoolLevel` sırasıdır", () => {
    expect(SCHOOL_LEVEL_TR).toEqual({
      OKUL_ONCESI: "Okul öncesi",
      ILKOKUL: "İlkokul",
      ORTAOKUL: "Ortaokul",
      ORTAOGRETIM: "Ortaöğretim (lise)",
    });
    expect(Object.keys(SCHOOL_LEVEL_TR)).toEqual([
      "OKUL_ONCESI",
      "ILKOKUL",
      "ORTAOKUL",
      "ORTAOGRETIM",
    ]);
  });

  it("yerleşim türü, kantin ve personel çalıştırma biçimi adları backend etiketleriyle birebir", () => {
    expect(SETTLEMENT_TYPE_TR).toEqual({
      BUYUKSEHIR: "Büyükşehir statüsündeki il",
      IL_MERKEZI_BUYUKSEHIR_DEGIL: "Büyükşehir statüsünde olmayan il merkezi",
      DIGER: "Büyükşehir statüsünde olmayan ilde, il merkezi dışında",
    });
    expect(CANTEEN_MODE_TR).toEqual({
      KIRAYA_VERILIYOR: "Kiraya veriliyor",
      BIRLIKCE_ISLETILIYOR: "Birlikçe işletiliyor",
      KANTIN_YOK: "Kantin ve benzeri yer yok",
    });
    expect(STAFFING_MODE_TR).toEqual({
      DOGRUDAN_ISVEREN: "Birlik doğrudan işveren",
      HIZMET_ALIMI: "Hizmet alımıyla",
      CALISTIRMIYOR: "Personel çalıştırmıyor",
    });
  });
});
