// Ayrılış Havuzu (genel tasarım §5.1): e-Okul aktarımı kimseyi ayırmaz; listede bulunmayanlar
// burada karar bekler. Havuz yalnız öğretmen ve diğer personeli taşır (öğrenci bölümü ve yıl
// sonu sınıf süzgeci F1b 5. adımda öğrenci sicili ile söküldü); tek tek ve toplu
// "Ayrıldı olarak işaretle" (onay diyaloğu, kayıt silinmez) ve "Aktif kalsın"
// (onaysız, havuzdan çıkar); "olası aynı kişi" ve onaylı "Birleştir"; bayat seçimde backend
// reddi. Tüm adlar uydurmadır (KVKK).

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { LeavePool } from "../okul/api";

const okulApiMock = vi.hoisted(() => ({
  getLeavePool: vi.fn(),
  resolveLeavePool: vi.fn(),
  mergePersonnel: vi.fn(),
}));

vi.mock("../okul/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../okul/api")>();
  return { ...actual, okulApi: okulApiMock };
});

import AyrilisHavuzu from "./AyrilisHavuzu";

const HAVUZ: LeavePool = {
  personnel_count: 3,
  personnel: [
    {
      id: 11,
      full_name: "AYŞE KARA",
      member_kind: "TEACHER",
      leave_candidate_since: "2026-09-22",
      run: null,
      similar: [
        {
          id: 21,
          full_name: "AYŞE BEYAZ",
          member_kind: "TEACHER",
          created_on: "2026-09-22",
          reason: "ad_ayni_soyad_farkli",
        },
      ],
    },
    {
      id: 12,
      full_name: "MEHMET DEMİR",
      member_kind: "STAFF",
      leave_candidate_since: "2026-09-22",
      run: { id: 6, file_name: "", date: "2026-09-22" },
      similar: [],
    },
    {
      id: 13,
      full_name: "ZEHRA EMEKLİ",
      member_kind: "TEACHER",
      leave_candidate_since: "2026-06-20",
      run: { id: 5, file_name: "OOK01001R1.XLS", date: "2026-06-20" },
      similar: [],
    },
  ],
};

const BOS: LeavePool = { personnel_count: 0, personnel: [] };

function kur(onDegisti = vi.fn(), birlestirebilir = true) {
  render(
    <MemoryRouter>
      <SnackbarProvider>
        <ConfirmProvider>
          <AyrilisHavuzu onDegisti={onDegisti} birlestirebilir={birlestirebilir} />
        </ConfirmProvider>
      </SnackbarProvider>
    </MemoryRouter>,
  );
  return onDegisti;
}

function personelBolumu(): HTMLElement {
  return screen.getByRole("region", { name: /^Öğretmenler ve Diğer Personel/ });
}

/** Hazır olma sinyali: personel bölümünün başlığı (sayısıyla). */
async function hazir(sayi = 3): Promise<void> {
  await screen.findByRole("heading", { name: `Öğretmenler ve Diğer Personel (${sayi})` });
}

beforeEach(() => {
  okulApiMock.getLeavePool.mockResolvedValue(HAVUZ);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("AyrilisHavuzu — liste", () => {
  it("personel listelenir; giriş tarihi, aktarım ve sayı görünür; öğrenci bölümü yoktur", async () => {
    kur();
    await hazir();

    const bolum = personelBolumu();
    const satir = within(bolum).getByRole("row", { name: /ZEHRA EMEKLİ/ });
    expect(
      within(satir)
        .getAllByRole("cell")
        .slice(1, 5)
        .map((c) => c.textContent),
    ).toEqual(["ZEHRA EMEKLİ", "Öğretmen", "20.06.2026", "OOK01001R1.XLS"]);
    expect(within(bolum).getByText("Yapıştırılan liste")).toBeInTheDocument();
    expect(within(bolum).getByText("Diğer personel")).toBeInTheDocument();
    expect(screen.getByText(/kimseyi ayırmaz ve kimsenin kaydını silmez/)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /^Öğrenciler/ })).toBeNull();
    expect(screen.queryByLabelText("Sınıf")).toBeNull();
    expect(screen.getByText(/Listede bulunmayan öğretmen ve\s+diğer personel/)).toBeInTheDocument();
  });

  it("havuz boşsa boş durum gösterilir", async () => {
    okulApiMock.getLeavePool.mockResolvedValue(BOS);
    kur();

    expect(await screen.findByText("Ayrılış kararı bekleyen kişi yok")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ayrıldı olarak işaretle" })).toBeNull();
  });

  it("yükleme hatası bantta gösterilir", async () => {
    okulApiMock.getLeavePool.mockRejectedValue(
      new ApiError(500, "error", "Havuz okunamadı; yeniden deneyin."),
    );
    kur();

    expect(await screen.findByText("Havuz okunamadı; yeniden deneyin.")).toBeInTheDocument();
  });
});

describe("AyrilisHavuzu — karar", () => {
  it("seçim yokken eylemler kapalıdır", async () => {
    kur();
    await hazir();

    const bolum = personelBolumu();
    expect(within(bolum).getByText("Karar vermek için kişi seçin.")).toBeInTheDocument();
    expect(within(bolum).getByRole("button", { name: "Ayrıldı olarak işaretle" })).toBeDisabled();
    expect(within(bolum).getByRole("button", { name: "Aktif kalsın" })).toBeDisabled();
  });

  it("toplu seçim onayla ayrılır (kayıt silinmez); liste ve seçim tazelenir", async () => {
    okulApiMock.resolveLeavePool.mockResolvedValue({
      personnel_left: 3,
      personnel_kept: 0,
      personnel_count: 0,
    });
    const user = userEvent.setup();
    const onDegisti = kur();
    await hazir();
    const bolum = personelBolumu();

    await user.click(within(bolum).getByRole("checkbox", { name: "Bütün kişileri seç" }));
    expect(within(bolum).getByText("3 kişi seçili.")).toBeInTheDocument();
    await user.click(within(bolum).getByRole("button", { name: "Ayrıldı olarak işaretle" }));

    const onay = await screen.findByRole("dialog", {
      name: "3 kişi ayrıldı olarak işaretlensin mi?",
    });
    expect(within(onay).getByText(/Kayıtları silinmez/)).toBeInTheDocument();
    await user.click(within(onay).getByRole("button", { name: "Ayrıldı olarak işaretle" }));

    await waitFor(() =>
      expect(okulApiMock.resolveLeavePool).toHaveBeenCalledWith({
        personnel: { leave: [11, 12, 13] },
      }),
    );
    expect(await screen.findByText("3 kişi ayrıldı olarak işaretlendi.")).toBeInTheDocument();
    expect(onDegisti).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(okulApiMock.getLeavePool).toHaveBeenCalledTimes(2));
  });

  it("ayrılış onayından vazgeçilirse istek atılmaz", async () => {
    const user = userEvent.setup();
    kur();
    await hazir();
    const bolum = personelBolumu();

    await user.click(within(bolum).getByRole("checkbox", { name: "ZEHRA EMEKLİ seç" }));
    await user.click(within(bolum).getByRole("button", { name: "Ayrıldı olarak işaretle" }));
    await user.click(
      within(
        await screen.findByRole("dialog", { name: "1 kişi ayrıldı olarak işaretlensin mi?" }),
      ).getByRole("button", { name: "Vazgeç" }),
    );

    expect(okulApiMock.resolveLeavePool).not.toHaveBeenCalled();
  });

  it("tek kişi “Aktif kalsın”: onaysız, yalnız havuzdan çıkar", async () => {
    okulApiMock.resolveLeavePool.mockResolvedValue({
      personnel_left: 0,
      personnel_kept: 1,
      personnel_count: 2,
    });
    const user = userEvent.setup();
    kur();
    await hazir();
    const bolum = personelBolumu();

    await user.click(within(bolum).getByRole("checkbox", { name: "MEHMET DEMİR seç" }));
    await user.click(within(bolum).getByRole("button", { name: "Aktif kalsın" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    await waitFor(() =>
      expect(okulApiMock.resolveLeavePool).toHaveBeenCalledWith({ personnel: { keep: [12] } }),
    );
    expect(
      await screen.findByText("1 kişi aktif kalacak; havuzdan çıkarıldı."),
    ).toBeInTheDocument();
  });

  it("liste yenilenince artık havuzda olmayan kişi seçimden düşer", async () => {
    okulApiMock.resolveLeavePool.mockResolvedValue({
      personnel_left: 0,
      personnel_kept: 1,
      personnel_count: 2,
    });
    const kalan: LeavePool = {
      personnel_count: 2,
      personnel: HAVUZ.personnel.filter((k) => k.id !== 12),
    };
    okulApiMock.getLeavePool.mockResolvedValueOnce(HAVUZ).mockResolvedValue(kalan);
    const user = userEvent.setup();
    kur();
    await hazir();

    await user.click(within(personelBolumu()).getByRole("checkbox", { name: "MEHMET DEMİR seç" }));
    await user.click(within(personelBolumu()).getByRole("button", { name: "Aktif kalsın" }));

    await hazir(2);
    expect(within(personelBolumu()).getByText("Karar vermek için kişi seçin.")).toBeInTheDocument();
  });

  it("bayat seçim: backend reddi bantta gösterilir, liste yenilenir", async () => {
    okulApiMock.resolveLeavePool.mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Seçilen kişilerden bazıları artık ayrılış havuzunda değil. Listeyi yenileyip yeniden seçin; hiçbir karar uygulanmadı.",
      ),
    );
    const user = userEvent.setup();
    kur();
    await hazir();
    const bolum = personelBolumu();

    await user.click(within(bolum).getByRole("checkbox", { name: "ZEHRA EMEKLİ seç" }));
    await user.click(within(bolum).getByRole("button", { name: "Aktif kalsın" }));

    expect(await screen.findByText(/artık ayrılış havuzunda değil/)).toBeInTheDocument();
    await waitFor(() => expect(okulApiMock.getLeavePool).toHaveBeenCalledTimes(2));
  });
});

describe("AyrilisHavuzu — olası aynı kişi", () => {
  it("aday gösterilir; “Birleştir” onaylı çalışır (havuzdaki kayıt kaynak)", async () => {
    okulApiMock.mergePersonnel.mockResolvedValue({});
    const user = userEvent.setup();
    const onDegisti = kur();
    await hazir();

    expect(screen.getByText(/Öyleyse ayrıldı diye işaretlemeyin/)).toBeInTheDocument();
    await user.click(
      within(personelBolumu()).getByRole("button", {
        name: "AYŞE KARA kaydını AYŞE BEYAZ kaydıyla birleştir",
      }),
    );
    const onay = await screen.findByRole("dialog", { name: "Bu iki kayıt aynı kişi mi?" });
    expect(within(onay).getByText(/havuzdaki kayıt silinir/)).toBeInTheDocument();
    // Diyalog iki kaydı ayırt eden bilgiyi ve gerekçeyi yazar (§13 D30).
    expect(within(onay).getByText(/adı aynı, soyadı farklı/)).toBeInTheDocument();
    expect(within(onay).getByText(/sicile eklendi 22\.09\.2026/)).toBeInTheDocument();

    const dugme = within(onay).getByRole("button", { name: "Birleştir" });
    expect(dugme).toBeDisabled();
    await user.click(
      within(onay).getByRole("checkbox", {
        name: "Bu iki kaydın aynı kişi olduğunu doğruladım",
      }),
    );
    expect(dugme).toBeEnabled();
    await user.click(dugme);

    await waitFor(() => expect(okulApiMock.mergePersonnel).toHaveBeenCalledWith(11, 21));
    expect(await screen.findByText("Kayıtlar birleştirildi.")).toBeInTheDocument();
    expect(onDegisti).toHaveBeenCalledTimes(1);
  });

  it("kişi yazma yeteneği yoksa aday gösterilir, “Birleştir” çizilmez", async () => {
    kur(vi.fn(), false);
    await hazir();

    expect(within(personelBolumu()).getByText("AYŞE BEYAZ")).toBeInTheDocument();
    expect(within(personelBolumu()).queryByRole("button", { name: /birleştir/i })).toBeNull();
    // Karar düğmeleri havuzun kendi yeteneğidir (sekme yalnız o yetenekte görünür).
    expect(
      within(personelBolumu()).getByRole("button", { name: /Ayrıldı olarak işaretle/ }),
    ).toBeInTheDocument();
  });

  it("aday satırı neden aday olduğunu yazar (ad benzerliği adaşı da yakalar)", async () => {
    kur();
    await hazir();

    expect(
      within(personelBolumu()).getByText(
        "Neden aday: adı aynı, soyadı farklı · Öğretmen, sicile eklendi 22.09.2026",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/her satır neden aday olduğunu yazar/)).toBeInTheDocument();
  });

  it("doğrulama kutusu işaretlenmeden birleştirme çağrılmaz", async () => {
    const user = userEvent.setup();
    kur();
    await hazir();
    await user.click(
      within(personelBolumu()).getByRole("button", {
        name: "AYŞE KARA kaydını AYŞE BEYAZ kaydıyla birleştir",
      }),
    );

    const onay = await screen.findByRole("dialog", { name: "Bu iki kayıt aynı kişi mi?" });
    await user.click(within(onay).getByRole("button", { name: "Birleştir" }));

    expect(okulApiMock.mergePersonnel).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog", { name: "Bu iki kayıt aynı kişi mi?" })).toBeInTheDocument();
  });
});

// Çözülemeyen şifreli alan (tasarım §13 D48): havuz satırında da boş hücre değil
// "okunamadı" yazar; seçim kutusunun adı kişi adı tahmin etmez.
describe("AyrilisHavuzu — okunamayan şifreli alan", () => {
  it("okunamayan ad “okunamadı” diye görünür; seçim kutusu kişi adı tahmin etmez", async () => {
    okulApiMock.getLeavePool.mockResolvedValue({
      ...BOS,
      personnel_count: 1,
      personnel: [{ ...HAVUZ.personnel[1], full_name: null, bozuk_alanlar: ["first_name"] }],
    });
    kur();

    const personel = await screen.findByRole("region", { name: /^Öğretmenler/ });
    expect(within(personel).getByText("okunamadı")).toBeInTheDocument();
    expect(
      within(personel).getByRole("checkbox", { name: "Adı okunamayan kayıt seç" }),
    ).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/null/);
  });

  it("birleştirme düğmesinin adı okunamayanda “kayıt kaydını” ikilemesi kurmaz", async () => {
    okulApiMock.getLeavePool.mockResolvedValue({
      ...BOS,
      personnel_count: 1,
      personnel: [{ ...HAVUZ.personnel[0], full_name: null, bozuk_alanlar: ["last_name"] }],
    });
    kur();

    expect(
      await within(await screen.findByRole("region", { name: /^Öğretmenler/ })).findByRole(
        "button",
        { name: "Adı okunamayan kaydı AYŞE BEYAZ kaydıyla birleştir" },
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /kayıt kaydını/ })).toBeNull();
  });
});
