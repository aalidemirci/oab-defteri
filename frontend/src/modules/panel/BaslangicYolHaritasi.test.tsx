// Başlangıç Yol Haritası kartı: maddeler (sözlük), kendiliğinden tespit edilen
// maddeler (setup/status sayıları ve okul kartının tamamlığı), her maddenin ilgili sayfaya
// bağlanması.

import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { KURULU_DURUM } from "../../test/kurulumDurumu";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import type { SetupStatus } from "../okul/api";
import {
  OKUL_KARTI_YOL_HARITASI_ACIKLAMASI,
  OKUL_KARTI_YOL_HARITASI_BASLIGI,
} from "../okul/metinler";
import BaslangicYolHaritasi, { YOL_HARITASI_MADDELERI, maddeTamamMi } from "./BaslangicYolHaritasi";

function bas(durum: SetupStatus = KURULU_DURUM) {
  return render(
    <MemoryRouter>
      <SnackbarProvider>
        <BaslangicYolHaritasi durum={durum} onIsaretle={vi.fn()} onGizle={vi.fn()} />
      </SnackbarProvider>
    </MemoryRouter>,
  );
}

function madde(metin: RegExp): HTMLElement {
  const li = screen.getByText(metin).closest("li");
  if (!li) throw new Error("madde bulunamadı");
  return li;
}

describe("BaslangicYolHaritasi", () => {
  it("maddeler bu sırayla durur; parola paylaşımı maddesi yoktur", () => {
    expect(YOL_HARITASI_MADDELERI.map((m) => m.anahtar)).toEqual([
      "okul_karti",
      "ogrenci_aktarimi",
      "personel_aktarimi",
      "kapali_gunler",
      "kurtarma_zarfi",
    ]);
  });

  it("parolanın paylaşılmasını öğütleyen madde ya da metin yoktur", () => {
    const { container } = bas();
    expect(container.textContent).not.toMatch(/paylaş/i);
    expect(container.textContent).not.toMatch(/görevlendirilmiş kişi|masadaki görevli/i);
  });

  it("kendiliğinden tespit edilen maddeler sayılardan, diğerleri işaretten okunur", () => {
    const durum: SetupStatus = {
      ...KURULU_DURUM,
      student_count: 3,
      personnel_count: 0,
      school_break_count: 1,
      roadmap: { marks: {}, hidden: false },
    };
    expect(maddeTamamMi("okul_karti", durum)).toBe(true);
    expect(maddeTamamMi("okul_karti", { ...durum, school_info_complete: false })).toBe(false);
    expect(maddeTamamMi("ogrenci_aktarimi", durum)).toBe(true);
    expect(maddeTamamMi("personel_aktarimi", durum)).toBe(false);
    expect(maddeTamamMi("kapali_gunler", durum)).toBe(true);
    expect(maddeTamamMi("kurtarma_zarfi", durum)).toBe(false);
    expect(
      maddeTamamMi("kurtarma_zarfi", {
        ...durum,
        roadmap: { marks: { kurtarma_zarfi: "2026-09-22" }, hidden: false },
      }),
    ).toBe(true);
  });

  it("okul kartı maddesi ilk sıradadır; başlık ve açıklama okul metinlerindendir", () => {
    bas({ ...KURULU_DURUM, school_info_complete: false });
    const ilk = screen.getAllByRole("listitem")[0];
    expect(ilk).toHaveTextContent(OKUL_KARTI_YOL_HARITASI_BASLIGI);
    expect(ilk).toHaveTextContent(OKUL_KARTI_YOL_HARITASI_ACIKLAMASI);
    expect(ilk).toHaveTextContent("(yapılacak)");
    expect(within(ilk).getByText("Yapıldığında kendiliğinden işaretlenir.")).toBeInTheDocument();
    expect(within(ilk).queryByRole("checkbox")).toBeNull();
    expect(within(ilk).getByRole("link", { name: /Okul Bilgileri/ })).toHaveAttribute(
      "href",
      "/ayarlar?tab=okul",
    );
  });

  it("okul kartının zorunlu alanları tamamsa madde tamamlandı görünür", () => {
    bas();
    expect(madde(/Okul bilgilerini tamamlayın/)).toHaveTextContent("(tamamlandı)");
  });

  it("kapalı günler maddesi iş günü hesabını anlatır, iade tarihinden söz etmez", () => {
    bas();
    const kapali = madde(/Öğrenciye kapalı günleri girin/);
    expect(kapali).toHaveTextContent(/iş günüyle verilen süreler/);
    expect(kapali.textContent).not.toMatch(/iade/i);
  });

  it("kurtarma anahtarı doğrulanmamışsa uyarı ve Güvenlik bağlantısı gösterilir", () => {
    bas({ ...KURULU_DURUM, recovery_key_confirmed: false });
    const uyari = screen.getByText(/Kurtarma anahtarı doğrulanmadı/).closest("div");
    expect(uyari).not.toBeNull();
    expect(
      within(uyari as HTMLElement).getByRole("link", { name: /Ayarlar → Güvenlik'i aç/ }),
    ).toHaveAttribute("href", "/ayarlar?tab=guvenlik");
  });

  it("anahtar doğrulanmışsa uyarı çıkmaz", () => {
    bas();
    expect(screen.queryByText(/Kurtarma anahtarı doğrulanmadı/)).toBeNull();
  });

  it("her madde ilgili sayfaya bağlanır", () => {
    bas();
    const bag = (metin: RegExp) => within(madde(metin)).getByRole("link");
    expect(bag(/Okul bilgilerini tamamlayın/)).toHaveAttribute("href", "/ayarlar?tab=okul");
    expect(bag(/e-Okul öğrenci listesini aktarın/)).toHaveAttribute("href", "/kisiler");
    expect(bag(/Öğretmen ve diğer personel listesini aktarın/)).toHaveAttribute(
      "href",
      "/kisiler?tab=personel",
    );
    expect(bag(/Öğrenciye kapalı günleri girin/)).toHaveAttribute(
      "href",
      "/ayarlar?tab=kapali-gunler",
    );
    expect(bag(/Kurtarma anahtarını müdürlükte kapalı zarfta saklayın/)).toHaveAttribute(
      "href",
      "/ayarlar?tab=guvenlik",
    );
    expect(screen.queryByRole("button", { name: /Şablonu indir/ })).toBeNull();
  });

  it("kendiliğinden tespit edilen maddelerde işaret kutusu yoktur", () => {
    bas();
    expect(within(madde(/e-Okul öğrenci listesini aktarın/)).queryByRole("checkbox")).toBeNull();
    expect(
      within(madde(/e-Okul öğrenci listesini aktarın/)).getByText(
        "Yapıldığında kendiliğinden işaretlenir.",
      ),
    ).toBeInTheDocument();
    // Elle işaretlenen tek madde: kurtarma anahtarı zarfı.
    expect(screen.getAllByRole("checkbox")).toHaveLength(1);
  });

  it("aktarımlar yapılınca maddeler tamamlandı olarak görünür", () => {
    bas({ ...KURULU_DURUM, student_count: 480, personnel_count: 36 });
    expect(
      within(madde(/e-Okul öğrenci listesini aktarın/)).getByText(/tamamlandı/),
    ).toBeInTheDocument();
    // İki aktarım + okul kartı (KURULU_DURUM'da tamam).
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
  });

  it("iç kodlar kullanıcı metnine girmez; yerel araç dili korunur", () => {
    const { container } = bas();
    expect(container.textContent).not.toMatch(/\b(F1|U10|E14|T5|KM-|OPAC)\b/);
    expect(container.textContent).not.toMatch(/otomasyon sistemi/i);
  });
});
