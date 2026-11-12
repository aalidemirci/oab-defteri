// Okul kartının ortak form alanları (sihirbazın 2. adımı ve Ayarlar → Okul Bilgileri) ve salt
// okur listesi: etiketler, kademe çoklu seçimi (backend sırasıyla), radyo grupları, kantin
// birlikçe işletilince md. 23/3 bilgisi, mevcudun tarihinin varsayılanı, alan hataları ve salt
// okur değer yazımı. Veriler uydurmadır.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { todayIso } from "../../lib/format";
import { BOS_OKUL_KARTI, KANTIN_ISLETME_BILGISI, ORNEK_OKUL_KARTI } from "../../test/okulKarti";
import OkulKartiAlanlari, { OkulKartiListesi, mevcutYazimi } from "./OkulKartiAlanlari";
import { KAMPUS_ETIKETI, OKUL_ADI_YARDIMI, VERI_SORUMLUSU_YARDIMI } from "./metinler";
import { bosOkulFormu } from "./okulBilgileri";
import type { OkulFormu } from "./okulBilgileri";

const kantinBilgisi = vi.hoisted(() => ({ useKantinIsletmeBilgisi: vi.fn() }));
vi.mock("./kuralBilgileri", () => kantinBilgisi);

beforeEach(async () => {
  const { ORNEK_KANTIN_BILGISI } = await import("../../test/okulKarti");
  kantinBilgisi.useKantinIsletmeBilgisi.mockReturnValue(ORNEK_KANTIN_BILGISI);
});

/** Durumlu sarmalayıcı: her değişiklik forma işlenir ve dışarı bildirilir. */
function Sarmal({
  ilk,
  errors = {},
  onForm,
}: {
  ilk: OkulFormu;
  errors?: Partial<Record<string, string>>;
  onForm?: (f: OkulFormu) => void;
}) {
  const [form, setForm] = useState(ilk);
  return (
    <OkulKartiAlanlari
      form={form}
      errors={errors}
      onChange={(d) => {
        const yeni = { ...form, ...d };
        setForm(yeni);
        onForm?.(yeni);
      }}
    />
  );
}

function bas(ilk: OkulFormu = bosOkulFormu(), errors?: Partial<Record<string, string>>) {
  const onForm = vi.fn<(f: OkulFormu) => void>();
  render(<Sarmal ilk={ilk} errors={errors} onForm={onForm} />);
  return { onForm, son: () => onForm.mock.calls.at(-1)?.[0] };
}

describe("OkulKartiAlanlari — form", () => {
  it("bütün alanlar sözleşmedeki etiketlerle durur; kısa ad ve hazırlık sınıfı yoktur", () => {
    bas();
    for (const etiket of [
      /^Okul adı/,
      /^Kurum kodu/,
      /^Okul müdürü/,
      /^İl \*$/,
      /^İlçe/,
      /^Öğrenci mevcudu/,
      /^Mevcudun tarihi/,
      /^Okulun açılış tarihi/,
    ]) {
      expect(screen.getByLabelText(etiket)).toBeInTheDocument();
    }
    for (const grup of [
      /^Kademe/,
      /^Yerleşim türü/,
      /^Kantin işletme biçimi/,
      /^Personel çalıştırma biçimi/,
    ]) {
      expect(screen.getByRole("group", { name: grup })).toBeInTheDocument();
    }
    expect(screen.getByRole("checkbox", { name: new RegExp(KAMPUS_ETIKETI) })).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: /Bu bilgisayar okul demirbaşıdır/ }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/Kısa ad/)).toBeNull();
    expect(screen.queryByText(/Hazırlık/)).toBeNull();
  });

  it("zorunlu alanlar yıldızlıdır; müdür ve açılış tarihi isteğe bağlıdır", () => {
    bas();
    expect(screen.getByLabelText(/^Kurum kodu/)).toBeRequired();
    expect(screen.getByLabelText(/^İl \*$/)).toBeRequired();
    expect(screen.getByLabelText(/^Öğrenci mevcudu/)).toBeRequired();
    expect(screen.getByRole("group", { name: "Kademe *" })).toBeInTheDocument();
    expect(screen.getByLabelText(/^Okul müdürü/)).not.toBeRequired();
    expect(screen.getByLabelText(/^Okulun açılış tarihi/)).not.toBeRequired();
    expect(screen.getByLabelText(/^Veri sorumlusu/)).not.toBeRequired();
  });

  it("veri sorumlusu isteğe bağlı serbest metindir; yardımı uydurma örneklidir", async () => {
    const user = userEvent.setup();
    const { son } = bas();
    const alan = screen.getByLabelText(/^Veri sorumlusu/);
    expect(alan).toHaveAccessibleDescription(VERI_SORUMLUSU_YARDIMI);
    expect(VERI_SORUMLUSU_YARDIMI).toContain("Okul müdürlüğünce belirlenir");
    expect(VERI_SORUMLUSU_YARDIMI).toContain("Örnek Anadolu Lisesi Müdürlüğü");
    await user.type(alan, "Örnek Ortaokulu Müdürlüğü");
    expect(son()?.veriSorumlusu).toBe("Örnek Ortaokulu Müdürlüğü");
  });

  it("kademe çoklu seçilir; liste backend sırasıyla tutulur, işaret kaldırılabilir", async () => {
    const user = userEvent.setup();
    const { son } = bas();
    const grup = screen.getByRole("group", { name: /^Kademe/ });
    expect(
      within(grup)
        .getAllByRole("checkbox")
        .map((k) => k.getAttribute("name")),
    ).toHaveLength(4);
    expect(
      within(grup)
        .getAllByRole("checkbox")
        .map((k) => (k.closest("label") as HTMLElement).textContent),
    ).toEqual(["Okul öncesi", "İlkokul", "Ortaokul", "Ortaöğretim (lise)"]);

    await user.click(within(grup).getByRole("checkbox", { name: "Ortaokul" }));
    await user.click(within(grup).getByRole("checkbox", { name: "İlkokul" }));
    expect(son()?.kademeler).toEqual(["ILKOKUL", "ORTAOKUL"]);
    expect(within(grup).getByRole("checkbox", { name: "İlkokul" })).toBeChecked();

    await user.click(within(grup).getByRole("checkbox", { name: "Ortaokul" }));
    expect(son()?.kademeler).toEqual(["ILKOKUL"]);
  });

  it("yerleşim, kantin ve personel tek seçimlidir; seçenekler backend etiketleriyle", async () => {
    const user = userEvent.setup();
    const { son } = bas();
    const yerlesim = screen.getByRole("group", { name: /^Yerleşim türü/ });
    expect(within(yerlesim).getAllByRole("radio")).toHaveLength(3);
    await user.click(
      within(yerlesim).getByRole("radio", {
        name: "Büyükşehir statüsünde olmayan ilde, il merkezi dışında",
      }),
    );
    expect(son()?.yerlesim).toBe("DIGER");
    await user.click(within(yerlesim).getByRole("radio", { name: "Büyükşehir statüsündeki il" }));
    expect(son()?.yerlesim).toBe("BUYUKSEHIR");
    expect(
      within(yerlesim).getByRole("radio", {
        name: "Büyükşehir statüsünde olmayan ilde, il merkezi dışında",
      }),
    ).not.toBeChecked();

    await user.click(screen.getByRole("radio", { name: "Kantin ve benzeri yer yok" }));
    expect(son()?.kantin).toBe("KANTIN_YOK");
    await user.click(screen.getByRole("radio", { name: "Hizmet alımıyla" }));
    expect(son()?.personel).toBe("HIZMET_ALIMI");
  });

  it("kantin birlikçe işletilince md. 23/3 bilgisi görünür; başka seçimde kalkar", async () => {
    const user = userEvent.setup();
    bas();
    // Canlı bölge seçimden ÖNCE de DOM'dadır (içeriğiyle doğan bölge duyurulmaz; denetim F1b-4).
    const bolge = screen.getByRole("status");
    expect(bolge).toBeEmptyDOMElement();
    expect(screen.queryByText(KANTIN_ISLETME_BILGISI)).toBeNull();

    await user.click(screen.getByRole("radio", { name: "Birlikçe işletiliyor" }));
    expect(screen.getByRole("status")).toBe(bolge);
    expect(bolge).toHaveTextContent(KANTIN_ISLETME_BILGISI);

    await user.click(screen.getByRole("radio", { name: "Kiraya veriliyor" }));
    expect(screen.queryByText(KANTIN_ISLETME_BILGISI)).toBeNull();
    expect(bolge).toBeEmptyDOMElement();
  });

  it("kural paketi okunamazsa bilgi çıkmaz, form çalışır", async () => {
    kantinBilgisi.useKantinIsletmeBilgisi.mockReturnValue(null);
    const user = userEvent.setup();
    bas();
    await user.click(screen.getByRole("radio", { name: "Birlikçe işletiliyor" }));
    expect(screen.getByRole("status")).toBeEmptyDOMElement();
  });

  it("künye alanları sözlükteki sırayla durur: okul adı, il, ilçe, müdür, kurum kodu", () => {
    bas();
    const sira = [/^Okul adı/, /^İl \*$/, /^İlçe/, /^Okul müdürü/, /^Kurum kodu/].map((e) =>
      screen.getByLabelText(e),
    );
    for (let i = 1; i < sira.length; i++) {
      expect(
        sira[i - 1].compareDocumentPosition(sira[i]) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    }
    expect(screen.getByText(OKUL_ADI_YARDIMI)).toBeInTheDocument();
  });

  it("kurum kodunda uzunluk sınırı yoktur: boşlukla yapıştırılan kod kırpılmadan önce kesilmez", async () => {
    const user = userEvent.setup();
    const { son } = bas();
    const alan = screen.getByLabelText(/^Kurum kodu/);
    expect(alan).not.toHaveAttribute("maxlength");
    await user.click(alan);
    await user.paste(" 123456");
    expect(son()?.kurumKodu).toBe(" 123456");
  });

  it("mevcudun tarihinin varsayılanı bugündür ve bugünden sonrası seçtirilmez", () => {
    bas();
    const tarih = screen.getByLabelText(/^Mevcudun tarihi/);
    expect(tarih).toHaveValue(todayIso());
    expect(tarih).toHaveAttribute("max", todayIso());
  });

  it("kayıtlı değerler forma dolar; açılış tarihi boşaltılabilir", async () => {
    const user = userEvent.setup();
    const { son } = bas({
      ...bosOkulFormu(),
      kurumKodu: "123456",
      kademeler: ["ILKOKUL", "ORTAOKUL"],
      mevcut: "480",
      kantin: "BIRLIKCE_ISLETILIYOR",
      kampus: true,
      acilis: "2025-09-08",
    });
    expect(screen.getByLabelText(/^Kurum kodu/)).toHaveValue("123456");
    expect(screen.getByRole("checkbox", { name: "İlkokul" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Ortaöğretim (lise)" })).not.toBeChecked();
    expect(screen.getByLabelText(/^Öğrenci mevcudu/)).toHaveValue("480");
    expect(screen.getByRole("radio", { name: "Birlikçe işletiliyor" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: new RegExp(KAMPUS_ETIKETI) })).toBeChecked();

    await user.clear(screen.getByLabelText(/^Okulun açılış tarihi/));
    expect(son()?.acilis).toBe("");
  });

  it("alan hataları ilgili alanın ya da grubun altına yazılır", () => {
    bas(bosOkulFormu(), {
      institution_code: "Kurum kodu altı haneli bir sayıdır.",
      levels: "En az bir kademe seçin.",
      canteen_mode: "Kantin işletme biçimini seçin.",
    });
    expect(screen.getByLabelText(/^Kurum kodu/)).toHaveAccessibleDescription(
      "Kurum kodu altı haneli bir sayıdır.",
    );
    expect(screen.getByRole("group", { name: /^Kademe/ })).toHaveAccessibleDescription(
      "En az bir kademe seçin.",
    );
    expect(screen.getByRole("group", { name: /^Kantin/ })).toHaveAccessibleDescription(
      "Kantin işletme biçimini seçin.",
    );
    expect(screen.getByRole("checkbox", { name: "İlkokul" })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  it("yardım metinleri madde numarasını söyler; oran ya da eşik yazmaz", () => {
    const { container } = render(<Sarmal ilk={bosOkulFormu()} />);
    expect(
      screen.getByText(/toplantı yeter sayısının hesabına girer \(md\. 9\/2\)/),
    ).toBeInTheDocument();
    expect(screen.getByText(/pay dağılımı buna göre yapılır \(md\. 17\/1\)/)).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/%|yüzde/i);
  });
});

describe("OkulKartiListesi — salt okur", () => {
  it("değerler formun etiketleriyle yazılır; mevcut tarihiyle, kampüs Evet/Hayır, boş açılış —", () => {
    render(<OkulKartiListesi kayit={{ ...ORNEK_OKUL_KARTI, levels: ["ORTAOKUL", "ILKOKUL"] }} />);
    const deger = (etiket: string) =>
      (screen.getByText(etiket, { selector: "dt" }).nextElementSibling as HTMLElement).textContent;
    expect(
      Array.from(document.querySelectorAll("dt"))
        .slice(0, 5)
        .map((dt) => dt.textContent),
    ).toEqual(["Okul adı", "İl", "İlçe", "Okul müdürü", "Kurum kodu"]);
    expect(deger("Okul adı")).toBe("Örnek Anadolu Lisesi");
    expect(deger("Kurum kodu")).toBe("123456");
    expect(deger("Kademe")).toBe("İlkokul, Ortaokul");
    expect(deger("Öğrenci mevcudu")).toBe("1.234 · 01.10.2026 itibarıyla");
    expect(deger("Yerleşim türü")).toBe("Büyükşehir statüsündeki il");
    expect(deger("Kantin işletme biçimi")).toBe("Kiraya veriliyor");
    expect(deger("Personel çalıştırma biçimi")).toBe("Personel çalıştırmıyor");
    expect(deger(KAMPUS_ETIKETI)).toBe("Hayır");
    expect(deger("Okulun açılış tarihi")).toBe("—");
    expect(deger("Okul müdürü")).toBe("—");
    expect(deger("Veri sorumlusu")).toBe("—");
    expect(screen.getByText("Bu bilgisayar okul demirbaşıdır.")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByText(KANTIN_ISLETME_BILGISI)).toBeNull();
  });

  it("kampüsteki, birlikçe işletilen kantinli yeni okulda bilgi ve tarihler görünür", () => {
    render(
      <OkulKartiListesi
        kayit={{
          ...ORNEK_OKUL_KARTI,
          canteen_mode: "BIRLIKCE_ISLETILIYOR",
          in_campus: true,
          opened_on: "2025-09-08",
        }}
      />,
    );
    const deger = (etiket: string) =>
      (screen.getByText(etiket, { selector: "dt" }).nextElementSibling as HTMLElement).textContent;
    expect(deger(KAMPUS_ETIKETI)).toBe("Evet");
    expect(deger("Okulun açılış tarihi")).toBe("08.09.2025");
    expect(screen.getByText(KANTIN_ISLETME_BILGISI)).toBeInTheDocument();
  });

  it("boş kartta her değer — yazılır, demirbaş cümlesi çıkmaz", () => {
    render(<OkulKartiListesi kayit={BOS_OKUL_KARTI} />);
    const tanimlar = screen.getAllByRole("definition").map((d) => d.textContent);
    expect(tanimlar.filter((t) => t !== "Hayır").every((t) => t === "—")).toBe(true);
    expect(screen.queryByText("Bu bilgisayar okul demirbaşıdır.")).toBeNull();
  });

  it("mevcutYazimi: tarihli, tarihsiz ve boş", () => {
    expect(mevcutYazimi(1234, "2026-10-01")).toBe("1.234 · 01.10.2026 itibarıyla");
    expect(mevcutYazimi(480, null)).toBe("480");
    expect(mevcutYazimi(null, null)).toBe("");
  });
});
