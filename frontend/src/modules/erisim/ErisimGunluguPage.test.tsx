// Erişim Günlüğü ekranı (plan F1b-2 "Erişim günlüğü okuma ucu"; tasarım §4.6.4): süzgeçler tarih
// aralığı, tür ve hesap (seçenekler yanıttan; aynı tanıtıcılı hesaplar günleriyle ayrılır),
// sayfalı ve en yeni önce; ad-soyad ve iç kod yok; süzgecin 400 iletisi alanının altında; bugün
// günlüğe yazan okuma olmadığı için süzgeçsiz liste boştur. Veriler uydurmadır.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { gorunenMetin } from "../../test/gorunenMetin";
import type { ErisimGunluguSayfasi, ErisimSatiri } from "./api";

const apiMock = vi.hoisted(() => ({ sayfa: vi.fn() }));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  erisimGunluguApi: apiMock,
}));

import ErisimGunluguPage, { suzgecHatalari } from "./ErisimGunluguPage";
import {
  BOS_ACIKLAMA,
  BOS_BASLIK,
  ERISIM_GUNLUGU_BASLIGI,
  OKUNAMADI,
  SUZGECE_UYAN_YOK,
  TABLO_ADI,
} from "./metinler";

const ESKI_MUHASIP = {
  id: "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f",
  tanitici: "muhasip",
  rol_etiketi: "Muhasip",
  acilis: "2026-09-01",
  kapanis: "2026-10-31",
};
const YENI_MUHASIP = {
  ...ESKI_MUHASIP,
  id: "5b4a3c2d-1e0f-4a9b-8c7d-6e5f4a3b2c1d",
  acilis: "2026-11-01",
  kapanis: null,
};
const TURLER = [
  { tur: "KISI_DOKUMU", tur_adi: "Kişi dökümü" },
  { tur: "VELI_LISTESI_CIKTISI", tur_adi: "Veli listesi çıktısı" },
];

function satir(ek: Partial<ErisimSatiri> = {}): ErisimSatiri {
  return {
    id: 1,
    // UTC 07:15 → Europe/Istanbul 10:15.
    zaman: "2026-11-02T07:15:00Z",
    hesap: YENI_MUHASIP,
    tur: "VELI_LISTESI_CIKTISI",
    tur_adi: "Veli listesi çıktısı",
    model: "okul.Student",
    kayit: "7",
    alan: null,
    belge_ozeti: "cd".repeat(32),
    satir_sayisi: 12,
    ...ek,
  };
}

function sayfa(ek: Partial<ErisimGunluguSayfasi> = {}): ErisimGunluguSayfasi {
  return {
    satirlar: [],
    toplam: 0,
    sayfa: 1,
    sayfa_sayisi: 1,
    sayfa_boyutu: 50,
    turler: TURLER,
    hesaplar: [],
    ...ek,
  };
}

function bas() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ErisimGunluguPage />
    </QueryClientProvider>,
  );
}

/** Son çağrının süzgeci. */
function sonSuzgec(): Record<string, unknown> {
  return apiMock.sayfa.mock.calls.at(-1)?.[0] as Record<string, unknown>;
}

beforeEach(() => {
  vi.clearAllMocks();
  apiMock.sayfa.mockResolvedValue(sayfa());
});

describe("Erişim Günlüğü", () => {
  it("süzgeçsiz boş günlük bugün yazan okuma olmadığını söyler", async () => {
    bas();

    expect(
      screen.getByRole("heading", { level: 1, name: ERISIM_GUNLUGU_BASLIGI }),
    ).toBeInTheDocument();
    expect(await screen.findByText(BOS_BASLIK)).toBeInTheDocument();
    expect(screen.getByText(BOS_ACIKLAMA)).toBeInTheDocument();
    expect(sonSuzgec()).toEqual({ baslangic: "", bitis: "", tur: "", hesap: "", sayfa: 1 });
    // Temizlenecek süzgeç yok.
    expect(screen.getByRole("button", { name: "Süzgeçleri temizle" })).toBeDisabled();
  });

  it("satırlar kişisizdir: hesap rol etiketi, tanıtıcı ve günlerle; iç kod yazılmaz", async () => {
    apiMock.sayfa.mockResolvedValue(
      sayfa({
        satirlar: [
          satir(),
          satir({
            id: 2,
            hesap: ESKI_MUHASIP,
            tur: "MASKESIZ_TCKN",
            tur_adi: "Maskesiz T.C. kimlik numarası",
            alan: "tckn",
            belge_ozeti: null,
            satir_sayisi: null,
          }),
        ],
        toplam: 2,
        hesaplar: [ESKI_MUHASIP, YENI_MUHASIP],
      }),
    );
    const { container } = bas();

    const tablo = await screen.findByRole("table", { name: TABLO_ADI });
    const basliklar = within(tablo)
      .getAllByRole("columnheader")
      .map((h) => h.textContent);
    expect(basliklar).toEqual(["Zaman", "Hesap", "Tür", "Okunan kayıt", "Çıktı"]);
    const [, ilk, ikinci] = within(tablo).getAllByRole("row");
    expect(within(ilk).getByText("02.11.2026 10:15")).toBeInTheDocument();
    expect(
      within(ilk).getByText("Muhasip · tanıtıcı muhasip (açılış 01.11.2026)"),
    ).toBeInTheDocument();
    expect(within(ilk).getByText("Veli listesi çıktısı")).toBeInTheDocument();
    expect(within(ilk).getByText("Bilinmeyen kayıt türü · kimlik 7")).toBeInTheDocument();
    expect(within(ilk).getByText("12 satır")).toBeInTheDocument();
    expect(
      within(ikinci).getByText(
        "Muhasip · tanıtıcı muhasip (açılış 01.09.2026, kapanış 31.10.2026)",
      ),
    ).toBeInTheDocument();
    expect(
      within(ikinci).getByText("Bilinmeyen kayıt türü · kimlik 7 · bilinmeyen alan"),
    ).toBeInTheDocument();
    expect(gorunenMetin(tablo)).not.toMatch(/okul\.Student|MASKESIZ_TCKN|VELI_LISTESI|tckn|cdcdcd/);
    expect(gorunenMetin(container)).not.toMatch(/[A-Z]+_[A-Z]+/);
  });

  it("tür ve hesap seçenekleri yanıttandır; seçim ilk sayfadan okunur", async () => {
    const user = userEvent.setup();
    apiMock.sayfa.mockResolvedValue(
      sayfa({ satirlar: [satir()], toplam: 1, hesaplar: [ESKI_MUHASIP, YENI_MUHASIP] }),
    );
    bas();
    await screen.findByRole("table", { name: TABLO_ADI });

    const tur = screen.getByLabelText("Tür");
    expect(
      within(tur)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Bütün türler", "Kişi dökümü", "Veli listesi çıktısı"]);
    const hesap = screen.getByLabelText("Hesap");
    // Aynı tanıtıcılı eski ve yeni hesap günleriyle ayrılır.
    expect(
      within(hesap)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual([
      "Bütün hesaplar",
      "Muhasip · tanıtıcı muhasip (açılış 01.09.2026, kapanış 31.10.2026)",
      "Muhasip · tanıtıcı muhasip (açılış 01.11.2026)",
    ]);

    await user.selectOptions(tur, "KISI_DOKUMU");
    await waitFor(() => expect(sonSuzgec()).toMatchObject({ tur: "KISI_DOKUMU", sayfa: 1 }));
    await user.selectOptions(hesap, ESKI_MUHASIP.id);
    await waitFor(() =>
      expect(sonSuzgec()).toMatchObject({ tur: "KISI_DOKUMU", hesap: ESKI_MUHASIP.id }),
    );
  });

  it("tarih aralığı uca ISO gün olarak gider; temizle süzgeçleri kaldırır", async () => {
    const user = userEvent.setup();
    bas();
    await screen.findByText(BOS_BASLIK);

    fireEvent.change(screen.getByLabelText("Başlangıç"), { target: { value: "2026-11-01" } });
    fireEvent.change(screen.getByLabelText("Bitiş"), { target: { value: "2026-11-03" } });

    await waitFor(() =>
      expect(sonSuzgec()).toMatchObject({ baslangic: "2026-11-01", bitis: "2026-11-03" }),
    );
    // Süzgeçli boş liste süzgeçleri anar.
    expect(await screen.findByText(SUZGECE_UYAN_YOK)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Süzgeçleri temizle" }));
    await waitFor(() =>
      expect(sonSuzgec()).toEqual({ baslangic: "", bitis: "", tur: "", hesap: "", sayfa: 1 }),
    );
    expect(await screen.findByText(BOS_BASLIK)).toBeInTheDocument();
  });

  it.each([
    ["bitis", "Bitiş", "Tarih geçersiz."],
    ["bitis", "Bitiş", "Bitiş tarihi başlangıç tarihinden önce olamaz."],
    ["baslangic", "Başlangıç", "Tarih geçersiz."],
  ])(
    "takvim ucunda ve ters aralıkta sunucunun iletisi alanın altındadır (%s: %s)",
    async (alan, etiket, ileti) => {
      bas();
      await screen.findByText(BOS_BASLIK);
      apiMock.sayfa.mockRejectedValue(
        new ApiError(400, "validation_error", ileti, { [alan]: [ileti] }),
      );

      fireEvent.change(screen.getByLabelText(etiket), { target: { value: "9999-12-31" } });

      const girdi = screen.getByLabelText(etiket);
      await waitFor(() => expect(girdi).toHaveAttribute("aria-invalid", "true"));
      expect(girdi).toHaveAccessibleDescription(ileti);
      // Alana bağlı ret hata bandına ikinci kez yazılmaz; seçenekler silinmez.
      expect(screen.getAllByRole("alert")).toHaveLength(1);
      expect(within(screen.getByLabelText("Tür")).getAllByRole("option")).toHaveLength(3);
    },
  );

  it.each([
    [
      "sayfa numarası",
      new ApiError(400, "validation_error", "Sayfa numarası geçersiz.", {
        sayfa: ["Sayfa numarası geçersiz."],
      }),
      "Sayfa numarası geçersiz.",
    ],
    [
      "rol reddi",
      new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."),
      "Bu işlem hesabınızın rolüne açık değil.",
    ],
    ["ağ", new TypeError("Failed to fetch"), OKUNAMADI],
  ])("alana bağlanamayan ret (%s) hata bandındadır", async (_ad, hata, ileti) => {
    apiMock.sayfa.mockRejectedValue(hata);
    bas();

    expect(await screen.findByRole("alert")).toHaveTextContent(ileti);
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.queryByText(BOS_BASLIK)).toBeNull();
  });

  it("sayfalıdır: sonraki sayfa okunur, süzgeç değişince ilk sayfaya dönülür", async () => {
    const user = userEvent.setup();
    apiMock.sayfa.mockImplementation((s: { sayfa: number }) =>
      Promise.resolve(
        sayfa({
          satirlar: [satir({ id: s.sayfa })],
          toplam: 120,
          sayfa: s.sayfa,
          sayfa_sayisi: 3,
        }),
      ),
    );
    bas();
    await screen.findByRole("table", { name: TABLO_ADI });
    expect(screen.getByText("1–50 / 120 kayıt")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Önceki" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Sonraki" }));
    await waitFor(() => expect(sonSuzgec()).toMatchObject({ sayfa: 2 }));
    expect(await screen.findByText("51–100 / 120 kayıt")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Tür"), "KISI_DOKUMU");
    await waitFor(() => expect(sonSuzgec()).toMatchObject({ tur: "KISI_DOKUMU", sayfa: 1 }));
  });

  it("son sayfadan büyük bir sayfada kalınırsa son sayfaya dönülür", async () => {
    const user = userEvent.setup();
    apiMock.sayfa.mockImplementation((s: { sayfa: number }) =>
      Promise.resolve(
        s.sayfa === 1
          ? sayfa({ satirlar: [satir()], toplam: 60, sayfa: 1, sayfa_sayisi: 2 })
          : // Kayıtlar bu arada azaldı: ikinci sayfa artık yok.
            sayfa({ satirlar: [], toplam: 40, sayfa: s.sayfa, sayfa_sayisi: 1 }),
      ),
    );
    bas();
    await screen.findByRole("table", { name: TABLO_ADI });

    await user.click(screen.getByRole("button", { name: "Sonraki" }));

    await waitFor(() => expect(sonSuzgec()).toMatchObject({ sayfa: 1 }));
    expect(apiMock.sayfa.mock.calls.map((c) => (c[0] as { sayfa: number }).sayfa)).toEqual([
      1, 2, 1,
    ]);
  });
});

describe("suzgecHatalari", () => {
  it("süzgeç alanlarına bağlı iletiler alanlara, ötekiler banda", () => {
    expect(suzgecHatalari(null)).toEqual({ alanlar: {}, genel: null });
    expect(
      suzgecHatalari(
        new ApiError(400, "validation_error", "Geçerli bir tür seçin.", {
          tur: ["Geçerli bir tür seçin."],
        }),
      ),
    ).toEqual({ alanlar: { tur: "Geçerli bir tür seçin." }, genel: null });
    // Alansız 400 (eski sunucu) ve bilinmeyen alan bandadır.
    expect(suzgecHatalari(new ApiError(400, "validation_error", "Tarih geçersiz."))).toEqual({
      alanlar: {},
      genel: "Tarih geçersiz.",
    });
    expect(
      suzgecHatalari(
        new ApiError(400, "validation_error", "Tarih geçersiz. Başka.", {
          bitis: ["Tarih geçersiz."],
          non_field_errors: ["Başka."],
        }),
      ),
    ).toEqual({ alanlar: { bitis: "Tarih geçersiz." }, genel: "Tarih geçersiz. Başka." });
  });
});
