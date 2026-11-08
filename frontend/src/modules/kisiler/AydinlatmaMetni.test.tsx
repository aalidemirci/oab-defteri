// Aktarım ekranlarının aydınlatma metni (KVKK md. 10/1; plan "F1b-5 uygulama kararları"):
// kullanıcının onayladığı metin BİREBİR görünür (sabitler `metinler.ts`'te; sözlükteki
// birebirliği backend `test_on_yuz_sozlugu` sınar), personel ve veli metinleri ayrıdır, "Veri
// sorumlusu:" satırı okul kartından dolar; boşken uyarı ve Ayarlar → Okul Bilgileri bağlantısı
// çıkar. Veriler uydurmadır.

import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import * as metinler from "./metinler";

const okulApiMock = vi.hoisted(() => ({ getSchoolConfig: vi.fn() }));

vi.mock("../okul/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../okul/api")>()),
  okulApi: okulApiMock,
}));

import AydinlatmaMetni, { OKUL_BILGILERI_ADRESI } from "./AydinlatmaMetni";
import type { AydinlatmaTuru } from "./AydinlatmaMetni";

const VERI_SORUMLUSU = "Örnek Anadolu Lisesi Müdürlüğü, Örnek Mah. Örnek Sok. No: 1, Örnek İlçe";

function kur(tur: AydinlatmaTuru, veriSorumlusu: string | Error = VERI_SORUMLUSU) {
  if (veriSorumlusu instanceof Error) okulApiMock.getSchoolConfig.mockRejectedValue(veriSorumlusu);
  else
    okulApiMock.getSchoolConfig.mockResolvedValue({
      ...ORNEK_OKUL_KARTI,
      data_controller_text: veriSorumlusu,
    });
  render(
    <MemoryRouter>
      <AydinlatmaMetni tur={tur} />
    </MemoryRouter>,
  );
  return screen.getByRole("region", { name: metinler.AYDINLATMA_BASLIGI });
}

/** Paragrafların metinleri (başlık kalın yazılır; metin birleşince birebir olmalıdır). */
function paragraflar(bolge: HTMLElement): string[] {
  return Array.from(bolge.querySelectorAll("p")).map((p) => p.textContent ?? "");
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("AydinlatmaMetni", () => {
  it("personel metni birebir ve sırasıyla görünür; veri sorumlusu okul kartından dolar", async () => {
    const bolge = kur("personel");

    await waitFor(() =>
      expect(paragraflar(bolge)).toContain(
        `${metinler.AYDINLATMA_VERI_SORUMLUSU_ETIKETI} ${VERI_SORUMLUSU}`,
      ),
    );
    expect(within(bolge).getByRole("heading", { name: metinler.AYDINLATMA_BASLIGI })).toBeVisible();
    expect(paragraflar(bolge)).toEqual([
      metinler.PERSONEL_AYDINLATMA_GIRISI,
      `${metinler.AYDINLATMA_VERI_SORUMLUSU_ETIKETI} ${VERI_SORUMLUSU}`,
      metinler.PERSONEL_AYDINLATMA_AMACI,
      metinler.AYDINLATMA_AKTARIM,
      metinler.PERSONEL_AYDINLATMA_TOPLAMA,
      metinler.PERSONEL_AYDINLATMA_SAKLAMA,
      metinler.AYDINLATMA_HAKLARINIZ,
      metinler.AYDINLATMA_EKRAN_NOTU,
    ]);
    // Köşeli ayraçlı yer tutucu ve "Ekran notu" öneki ekranda yoktur.
    expect(bolge).not.toHaveTextContent(/\[|\]|Ekran notu/);
    expect(within(bolge).queryByRole("link")).toBeNull();
  });

  it("veli metni personel metninden ayrıdır", async () => {
    const bolge = kur("veli");

    await waitFor(() => expect(bolge).toHaveTextContent(VERI_SORUMLUSU));
    const metin = paragraflar(bolge);
    expect(metin).toContain(metinler.VELI_AYDINLATMA_GIRISI);
    expect(metin).toContain(metinler.VELI_AYDINLATMA_AMACI);
    expect(metin).toContain(metinler.VELI_AYDINLATMA_TOPLAMA);
    expect(metin).toContain(metinler.VELI_AYDINLATMA_SAKLAMA);
    expect(metin).not.toContain(metinler.PERSONEL_AYDINLATMA_AMACI);
  });

  it("onaylı metnin anahtar sözleri değişmemiştir", () => {
    // Birebirlik sözlükte sınanır; burada metnin hukuki dayanakları sabitlenir.
    expect(metinler.PERSONEL_AYDINLATMA_GIRISI).toBe(
      "AKTARMADAN ÖNCE: Bu metin kişisel verisi aktarılan personele okulda duyurulur (KVKK md. 10/1).",
    );
    expect(metinler.PERSONEL_AYDINLATMA_TOPLAMA).toContain("(KVKK md. 5/2-ç)");
    expect(metinler.VELI_AYDINLATMA_AMACI).toContain("(OAB Yönetmeliği md. 9/2, 9/3, 10/1-a)");
    expect(metinler.VELI_AYDINLATMA_SAKLAMA).toBe(
      "Saklama: Liste birlik döneminin kapanışında silinir; genel kuruldan sonra daha önce de silinebilir.",
    );
    expect(metinler.AYDINLATMA_HAKLARINIZ).toContain("KVKK md. 11'deki haklarınızı");
  });

  it("veri sorumlusu boşken uyarı ve Okul Bilgileri bağlantısı çıkar", async () => {
    const bolge = kur("veli", "   ");

    const baglanti = await within(bolge).findByRole("link", {
      name: metinler.VERI_SORUMLUSU_BAGLANTISI,
    });
    expect(baglanti).toHaveAttribute("href", OKUL_BILGILERI_ADRESI);
    expect(bolge).toHaveTextContent(metinler.VERI_SORUMLUSU_GIRILMEDI);
    // Metnin geri kalanı yine görünür (aktarım engellenmez).
    expect(paragraflar(bolge)).toContain(metinler.VELI_AYDINLATMA_AMACI);
  });

  it("okul bilgileri okunamazsa bunu söyler", async () => {
    const bolge = kur("personel", new Error("ağ"));

    await waitFor(() => expect(bolge).toHaveTextContent(metinler.VERI_SORUMLUSU_OKUNAMADI));
    expect(within(bolge).queryByRole("link")).toBeNull();
  });
});
