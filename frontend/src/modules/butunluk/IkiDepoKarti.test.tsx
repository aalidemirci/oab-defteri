// "Hesaplar ve Güvenlik Dosyası" kartı (tasarım §4.6.1 kural 4): farkın üç listesi kişisizdir;
// güvenlik dosyasında kalan eski parola kaydı yalnız onay diyaloğundan geçince silinir
// (`POST security/integrity/orphan-wraps/`), kart yanıttaki güncel iki depo kartıyla yenilenir.
// "Sarmal" ve iç kodlar ekrana çıkmaz (sözlük §1 "Denetim izi").

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { gorunenMetin } from "../../test/gorunenMetin";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { butunlukApi } from "./api";
import type { IkiDepoFarki, IkiDepoYaniti } from "./api";
import IkiDepoKarti, {
  SILME_ONAY_BASLIGI,
  eskiKayitlarAciklamasi,
  silDugmesiAdi,
  silmeSonucu,
} from "./IkiDepoKarti";
import { IKI_DEPO_KARTI_BASLIGI } from "./metinler";

const ESKI = "0d6c1f2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f";

const FARK: IkiDepoFarki = {
  fark_var: true,
  sarmalsiz_hesaplar: [{ id: "h-2", tanitici: "muhasip", rol_etiketi: "Muhasip", kapali: false }],
  silinebilir_sarmallar: [
    { id: ESKI, tanitici: "eski-hesap", rol_etiketi: null, kapali: false },
    { id: "h-3", tanitici: "sekreter", rol_etiketi: "Sekreter", kapali: true },
  ],
  muhru_tutmayan: [{ id: "h-4", tanitici: "dk-1", rol_etiketi: "Denetleme Kurulu", kapali: false }],
};

/** Silmeden dönen iki depo kartı (`two-store/` biçimi; mührü tutmayanlar denetim kartında). */
const GUNCEL: IkiDepoYaniti = {
  iki_depo: {
    fark_var: true,
    sarmalsiz_hesaplar: FARK.sarmalsiz_hesaplar,
    silinebilir_sarmallar: FARK.silinebilir_sarmallar.slice(1),
  },
  okunamayan: [],
};

function bas(fark: IkiDepoFarki = FARK, onIkiDepo = vi.fn()) {
  const sonuc = render(
    <SnackbarProvider>
      <ConfirmProvider>
        <IkiDepoKarti fark={fark} onIkiDepo={onIkiDepo} />
      </ConfirmProvider>
    </SnackbarProvider>,
  );
  return { ...sonuc, onIkiDepo };
}

function kart(): HTMLElement {
  return screen.getByRole("region", { name: IKI_DEPO_KARTI_BASLIGI });
}

afterEach(() => vi.restoreAllMocks());

describe("Hesaplar ve Güvenlik Dosyası kartı", () => {
  it("üç listeyi rol etiketi ve tanıtıcıyla yazar; iç kod ve “sarmal” yok", () => {
    const { container } = bas();

    expect(within(kart()).getByText("Giriş yapamayan hesaplar")).toBeInTheDocument();
    expect(within(kart()).getByText("Muhasip · tanıtıcı muhasip")).toBeInTheDocument();
    expect(
      within(kart()).getByText("tanıtıcı eski-hesap · veritabanında kaydı yok"),
    ).toBeInTheDocument();
    expect(
      within(kart()).getByText("Sekreter · tanıtıcı sekreter · hesap kapalı"),
    ).toBeInTheDocument();
    expect(within(kart()).getByText("Kaydı değiştirilmiş görünen hesaplar")).toBeInTheDocument();
    expect(within(kart()).getByText("Denetleme Kurulu · tanıtıcı dk-1")).toBeInTheDocument();
    expect(
      within(kart()).getAllByRole("button", { name: /güvenlik dosyasından sil$/i }),
    ).toHaveLength(2);
    expect(gorunenMetin(container)).not.toMatch(/sarmal|[a-z]+_[a-z]+/i);
  });

  it("her satırın silme düğmesi hangi hesabın kaydını sildiğini söyler (erişilebilir ad)", () => {
    bas();

    const eski = within(kart()).getByRole("button", {
      name: "“eski-hesap” tanıtıcılı hesabın parola kaydını güvenlik dosyasından sil",
    });
    const sekreter = within(kart()).getByRole("button", {
      name: "“sekreter” tanıtıcılı hesabın parola kaydını güvenlik dosyasından sil",
    });
    // Görünür metin aynı kalır ve erişilebilir adın içindedir (WCAG 2.5.3).
    expect(eski).toHaveTextContent("Güvenlik dosyasından sil");
    expect(sekreter).toHaveTextContent("Güvenlik dosyasından sil");
    expect(silDugmesiAdi({ id: "x", tanitici: null, rol_etiketi: null, kapali: false })).toBe(
      "Bu hesabın parola kaydını güvenlik dosyasından sil",
    );
  });

  it("onaylanınca yalnız o kayıt silinir, kart güncel durumla yenilenir", async () => {
    const user = userEvent.setup();
    const sil = vi.spyOn(butunlukApi, "sahipsizSarmallariSil").mockResolvedValue({
      ...GUNCEL,
      silinen: [ESKI],
    });
    const { onIkiDepo } = bas();

    await user.click(
      within(kart()).getByRole("button", { name: silDugmesiAdi(FARK.silinebilir_sarmallar[0]) }),
    );
    const diyalog = await screen.findByRole("dialog", { name: SILME_ONAY_BASLIGI });
    expect(
      within(diyalog).getByText(/“eski-hesap” tanıtıcılı hesabın parola kaydı/),
    ).toBeInTheDocument();
    expect(within(diyalog).getByText(/denetim izine yazılır ve geri alınamaz/)).toBeInTheDocument();
    await user.click(within(diyalog).getByRole("button", { name: "Sil" }));

    await waitFor(() => expect(sil).toHaveBeenCalledWith([ESKI]));
    await waitFor(() => expect(onIkiDepo).toHaveBeenCalledWith({ ...GUNCEL, silinen: [ESKI] }));
    expect(
      await screen.findByText("Parola kaydı güvenlik dosyasından silindi."),
    ).toBeInTheDocument();
  });

  it("Vazgeç'te hiçbir şey silinmez", async () => {
    const user = userEvent.setup();
    const sil = vi.spyOn(butunlukApi, "sahipsizSarmallariSil");
    const { onIkiDepo } = bas();

    await user.click(
      within(kart()).getByRole("button", { name: silDugmesiAdi(FARK.silinebilir_sarmallar[1]) }),
    );
    const diyalog = await screen.findByRole("dialog", { name: SILME_ONAY_BASLIGI });
    await user.click(within(diyalog).getByRole("button", { name: "Vazgeç" }));

    expect(sil).not.toHaveBeenCalled();
    expect(onIkiDepo).not.toHaveBeenCalled();
  });

  it("silme reddedilirse sunucunun iletisi kartta görünür", async () => {
    const user = userEvent.setup();
    vi.spyOn(butunlukApi, "sahipsizSarmallariSil").mockRejectedValue(
      new ApiError(
        400,
        "validation_error",
        "Bu parola kaydı artık güvenlik dosyasından silinebilecek durumda değil; Genel Bakış'ı yenileyip yeniden deneyin.",
      ),
    );
    const { onIkiDepo } = bas();

    await user.click(
      within(kart()).getByRole("button", { name: silDugmesiAdi(FARK.silinebilir_sarmallar[0]) }),
    );
    await user.click(
      within(await screen.findByRole("dialog", { name: SILME_ONAY_BASLIGI })).getByRole("button", {
        name: "Sil",
      }),
    );

    expect(await within(kart()).findByRole("alert")).toHaveTextContent(
      /silinebilecek durumda değil/,
    );
    expect(onIkiDepo).not.toHaveBeenCalled();
  });

  it("kapalı hesabın kaydını programın kendisinin sildiğini, kaydı olmayanınkini silmediğini söyler", () => {
    // Bağımsız denetim bulgusu: metin "program onları kendiliğinden silmez" diyordu; kapalı
    // hesabın parola kaydını program her kilit açılışında kendisi siler (§4.6.1 kural 3).
    bas();
    const aciklama = within(kart()).getByText(/^Kapalı hesapların parola kaydını program/);
    expect(aciklama).toHaveTextContent(/her kilit açılışında kendisi siler/);
    expect(aciklama).toHaveTextContent(/bir sonraki kilit açılışında yinelenir/);
    expect(aciklama).toHaveTextContent(
      /Veritabanında kaydı olmayan hesapların parola kaydını program kendiliğinden silmez\./,
    );
    expect(aciklama).toHaveTextContent(/Program yöneticisi onaylarsa hemen silinir\.$/);

    const kapali = { id: "k", tanitici: "sekreter", rol_etiketi: "Sekreter", kapali: true };
    const kayitsiz = { id: "y", tanitici: "eski", rol_etiketi: null, kapali: false };
    expect(eskiKayitlarAciklamasi([kapali])).not.toMatch(/kendiliğinden silmez/);
    expect(eskiKayitlarAciklamasi([kayitsiz])).toBe(
      "Veritabanında kaydı olmayan hesapların parola kaydını program kendiliğinden silmez. " +
        "Program yöneticisi onaylarsa hemen silinir.",
    );
  });

  it("fark yoksa kart çizilmez; tanıtıcısı okunamayan kayıt da sonuç cümlesini bozmaz", () => {
    const { container } = bas({ ...FARK, fark_var: false });
    expect(container).toBeEmptyDOMElement();
    expect(silmeSonucu({ id: "x", tanitici: null, rol_etiketi: null, kapali: false })).toMatch(
      /^Bu hesabın parola kaydı/,
    );
  });
});
