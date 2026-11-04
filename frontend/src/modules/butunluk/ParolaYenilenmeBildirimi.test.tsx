// Parola yenilenme bildirimi (tasarım §4.4.3, §4.3 tehdit 12): bildirim bekleyen hesabın
// sahibine pencere olarak çıkar — "Parolanız gg.aa.yyyy tarihinde sıfırlandı." ya da "…
// kurtarma anahtarıyla yenilendi." ve o tarihten bu yana yalnız bu hesabın girişleri; iç kod
// yok. "Gördüm" izli uca POST eder ve pencereyi kapatır; Esc yalnız pencereyi kapatır.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { gorunenMetin } from "../../test/gorunenMetin";
import { butunlukApi } from "./api";
import type { ParolaYenilenme } from "./api";
import { PAROLA_BILDIRIMI_BASLIGI } from "./metinler";
import ParolaYenilenmeBildirimi, { bildirimiOku } from "./ParolaYenilenmeBildirimi";

const SIFIRLAMA: ParolaYenilenme = {
  tur: "SIFIRLAMA",
  zaman: "2026-10-30T16:00:00+03:00",
  girisler: ["2026-11-01T09:05:00+03:00", "2026-10-31T08:40:00+03:00"],
};

afterEach(() => vi.restoreAllMocks());

function bildirimVar(bildirim: ParolaYenilenme | null) {
  return vi.spyOn(butunlukApi, "parolaBildirimi").mockResolvedValue({ parola_yenilenme: bildirim });
}

describe("Parola yenilenme bildirimi", () => {
  it("sıfırlamayı tarihle ve o tarihten sonraki girişlerle söyler; iç kod yok", async () => {
    bildirimVar(SIFIRLAMA);
    render(<ParolaYenilenmeBildirimi />);

    const pencere = await screen.findByRole("dialog", { name: PAROLA_BILDIRIMI_BASLIGI });
    expect(
      within(pencere).getByText("Parolanız 30.10.2026 tarihinde sıfırlandı."),
    ).toBeInTheDocument();
    expect(
      within(pencere).getByText("O tarihten bu yana hesabınızla yapılan girişler:"),
    ).toBeInTheDocument();
    const girisler = within(pencere)
      .getAllByRole("listitem")
      .map((li) => li.textContent);
    expect(girisler).toEqual(["01.11.2026 09:05 · bu oturum", "31.10.2026 08:40"]);
    expect(within(pencere).getByText(/sıfırlanmasını siz istemediyseniz/)).toBeInTheDocument();
    expect(within(pencere).getByText(/Son Girişler kartında da görünür/)).toBeInTheDocument();
    expect(gorunenMetin(pencere)).not.toMatch(/SIFIRLAMA|KURTARMA|[a-z]+_[a-z]+/);
  });

  it("kurtarma anahtarıyla yenilemeyi ve zarfın açıldığını söyler", async () => {
    bildirimVar({ ...SIFIRLAMA, tur: "KURTARMA" });
    render(<ParolaYenilenmeBildirimi />);

    const pencere = await screen.findByRole("dialog", { name: PAROLA_BILDIRIMI_BASLIGI });
    expect(
      within(pencere).getByText("Parolanız 30.10.2026 tarihinde kurtarma anahtarıyla yenilendi."),
    ).toBeInTheDocument();
    expect(within(pencere).getByText(/okul müdürlüğüne ve Denetleme Kuruluna/)).toBeInTheDocument();
  });

  it("“Gördüm” izli uca POST eder ve pencereyi kapatır", async () => {
    const user = userEvent.setup();
    bildirimVar(SIFIRLAMA);
    const gordum = vi
      .spyOn(butunlukApi, "parolaBildiriminiGordum")
      .mockResolvedValue({ parola_yenilenme: null });
    render(<ParolaYenilenmeBildirimi />);

    await user.click(await screen.findByRole("button", { name: "Gördüm" }));

    expect(gordum).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("Esc pencereyi kapatır ama bildirimi kaydetmez", async () => {
    const user = userEvent.setup();
    bildirimVar(SIFIRLAMA);
    const gordum = vi.spyOn(butunlukApi, "parolaBildiriminiGordum");
    render(<ParolaYenilenmeBildirimi />);
    await screen.findByRole("dialog", { name: PAROLA_BILDIRIMI_BASLIGI });

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(gordum).not.toHaveBeenCalled();
  });

  it("kaydedilemezse pencere kalır ve hata görünür", async () => {
    const user = userEvent.setup();
    bildirimVar({ ...SIFIRLAMA, girisler: [] });
    vi.spyOn(butunlukApi, "parolaBildiriminiGordum").mockRejectedValue(
      new ApiError(500, "sunucu_hatasi", "Sunucu hatası."),
    );
    render(<ParolaYenilenmeBildirimi />);

    await user.click(await screen.findByRole("button", { name: "Gördüm" }));

    const pencere = screen.getByRole("dialog", { name: PAROLA_BILDIRIMI_BASLIGI });
    expect(await within(pencere).findByRole("alert")).toHaveTextContent("Sunucu hatası.");
    expect(within(pencere).queryByRole("list")).not.toBeInTheDocument();
  });

  it("beklenmeyen biçimli yanıt pencere açmaz; girişsiz bildirim boş listeyle okunur", () => {
    expect(bildirimiOku(undefined)).toBeNull();
    expect(bildirimiOku({})).toBeNull();
    expect(bildirimiOku({ parola_yenilenme: { tur: "SIFIRLAMA" } })).toBeNull();
    expect(bildirimiOku({ parola_yenilenme: { tur: "KURTARMA", zaman: SIFIRLAMA.zaman } })).toEqual(
      { tur: "KURTARMA", zaman: SIFIRLAMA.zaman, girisler: [] },
    );
  });

  it("bildirim yoksa ya da okunamazsa hiçbir şey göstermez", async () => {
    const sorgu = bildirimVar(null);
    const ilk = render(<ParolaYenilenmeBildirimi />);
    await waitFor(() => expect(sorgu).toHaveBeenCalledTimes(1));
    expect(ilk.container).toBeEmptyDOMElement();
    ilk.unmount();

    sorgu.mockRejectedValueOnce(new ApiError(423, "locked", "Kayıtlar kilitli."));
    const ikinci = render(<ParolaYenilenmeBildirimi />);
    await waitFor(() => expect(sorgu).toHaveBeenCalledTimes(2));
    expect(ikinci.container).toBeEmptyDOMElement();
  });
});
