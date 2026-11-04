// Güvenlik kapısı testi: kilitliyken içerik GÖRÜNMEZ; kilit ekranından açılış içeriği
// YEREL olarak açmaz, pencereyi yeniden yükler (tasarım §13 D53); kapı okuduğu durumla
// "açık sanma" bayrağını yazar (döngü koruması, `lib/kilit.ts`). Güvenlik dosyası
// kayıpken kilit ekranı yerine AYRI "Güvenlik dosyası bulunamadı" ekranı ve çıkış
// yolları (dosyayı geri koy + yeniden denetle, yedekten geri yükle) gösterilir; durum
// ucu hata verirse kapı FAIL-OPEN davranır (gerçek kapı backend'dedir) ve bayrağı
// kaldırmaz.

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const guvenlik = vi.hoisted(() => ({
  durum: vi.fn(),
  kur: vi.fn(),
  sifirla: vi.fn(),
}));
const oturum = vi.hoisted(() => ({
  hesaplar: vi.fn(),
  ac: vi.fn(),
  kurtar: vi.fn(),
  kurtarmaHesaplari: vi.fn(),
}));

vi.mock("./api", () => ({ guvenlikApi: guvenlik }));
vi.mock("../oturum/api", () => ({ oturumApi: oturum }));
// Geri yükleme kartının kendi davranışı YedektenGeriYukleme.test.tsx'tedir.
vi.mock("./YedektenGeriYukleme", () => ({
  default: ({ kayipKipi }: { kayipKipi?: boolean }) => (
    <p>{kayipKipi ? "geri yükleme kartı (kayıp kipi)" : "geri yükleme kartı"}</p>
  ),
}));

import { ApiError } from "../../lib/api";
import {
  kilitKapisiYaniti,
  oturumAcikSan,
  oturumAcikSaniliyor,
  pencereIcerigi,
} from "../../lib/kilit";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import GuvenlikKapisi, { OKUNAMADI } from "./GuvenlikKapisi";
import type { GuvenlikDurumu } from "./api";

const ACIK: GuvenlikDurumu = {
  ...OKUNAMADI,
  password_set: true,
  recovery_key_confirmed: true,
  protected_fields: ["ad"],
  account_count: 1,
  recovery_key_no: 1,
  recovery_key_date: "2026-11-01",
};
const KILITLI: GuvenlikDurumu = { ...ACIK, locked: true };
const KAYIP: GuvenlikDurumu = { ...ACIK, locked: true, security_file_missing: true };
/** Kişi kaydı hiç girilmemiş kurulumda bozuk dosya: sıfırlama yolu açık. */
const SIFIRLANABILIR: GuvenlikDurumu = { ...KAYIP, reset_available: true };
const KURULUMA_DONDU: GuvenlikDurumu = { ...ACIK, password_set: false, account_count: 0 };

const YONETICI = {
  id: "11111111-1111-4111-8111-111111111111",
  tanitici: "yonetici",
  rol: "yonetici",
  rol_etiketi: "Program yöneticisi",
  secilebilir: true,
  askida_nedeni: null,
};

function icerikliKapi() {
  return render(
    <ConfirmProvider>
      <GuvenlikKapisi>
        <p>Gizli içerik</p>
      </GuvenlikKapisi>
    </ConfirmProvider>,
  );
}

describe("GuvenlikKapisi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    oturum.hesaplar.mockResolvedValue([YONETICI]);
  });

  it("kilitliyken içerik yerine kilit ekranını gösterir; ön yüz oturumu açık sanmaz", async () => {
    oturumAcikSan(true);
    guvenlik.durum.mockResolvedValue(KILITLI);
    icerikliKapi();
    expect(await screen.findByText("Kayıtlar kilitli")).toBeInTheDocument();
    expect(screen.queryByText("Gizli içerik")).toBeNull();
    expect(oturumAcikSaniliyor()).toBe(false);
  });

  it("kilit açılınca içeriği yerelde açmaz, pencereyi yeniden yükler (D53)", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(KILITLI);
    oturum.ac.mockResolvedValue({ durum: "acik" });
    icerikliKapi();

    await kullanici.type(await screen.findByLabelText(/^Parola/), "Deneme-Parola-1");
    await kullanici.click(screen.getByRole("button", { name: "Aç" }));

    await waitFor(() => expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1));
    expect(oturum.ac).toHaveBeenCalledWith({ hesap: YONETICI.id, parola: "Deneme-Parola-1" });
    // Yükleme olana dek içerik görünmez; form kapalı kalır.
    expect(screen.queryByText("Gizli içerik")).toBeNull();
    expect(screen.getByRole("button", { name: "Açılıyor…" })).toBeDisabled();
  });

  it("oturum açıksa içeriği gösterir ve ön yüz oturumu açık sanar", async () => {
    guvenlik.durum.mockResolvedValue(ACIK);
    icerikliKapi();
    expect(await screen.findByText("Gizli içerik")).toBeInTheDocument();
    expect(oturumAcikSaniliyor()).toBe(true);
  });

  it("hesap kurulu değilse doğrudan içeriği gösterir (sihirbaza içteki kapı götürür)", async () => {
    guvenlik.durum.mockResolvedValue(KURULUMA_DONDU);
    icerikliKapi();
    expect(await screen.findByText("Gizli içerik")).toBeInTheDocument();
    expect(oturumAcikSaniliyor()).toBe(false);
  });

  it("durum ucu hata verirse fail-open davranır ama oturumu açık sanmaz", async () => {
    guvenlik.durum.mockRejectedValue(new Error("bağlantı yok"));
    icerikliKapi();
    expect(await screen.findByText("Gizli içerik")).toBeInTheDocument();
    // Okunamayan durum + 423 sonsuz yüklemeye dönmesin (döngü koruması).
    expect(oturumAcikSaniliyor()).toBe(false);
  });

  it("güvenlik dosyası kayıpken kilit ekranı yerine ayrı ekranı ve çıkış yollarını gösterir", async () => {
    guvenlik.durum.mockResolvedValue(KAYIP);
    icerikliKapi();

    expect(
      await screen.findByRole("heading", { name: "Güvenlik dosyası bulunamadı ya da okunamıyor" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Gizli içerik")).toBeNull();
    // Parola ve hesap sorulmaz: dosya yokken hiçbir parola kabul edilmezdi.
    expect(screen.queryByText("Kayıtlar kilitli")).toBeNull();
    expect(screen.queryByLabelText(/parola/i)).toBeNull();
    expect(oturum.hesaplar).not.toHaveBeenCalled();
    // Ne olduğu ve ne yapılacağı anlaşılır dille söylenir.
    expect(screen.getByText(/guvenlik\.json\) veri klasöründe bulunamadı/)).toBeInTheDocument();
    expect(screen.getByText(/veri klasörüne geri koyun/)).toBeInTheDocument();
    expect(screen.getByText(/bir yedeği geri yükleyin/)).toBeInTheDocument();
    expect(screen.getByText("geri yükleme kartı (kayıp kipi)")).toBeInTheDocument();
    // İç kodlar kullanıcı metnine girmez.
    expect(screen.queryByText(/GA-2|guvenlik_dosyasi_kayip/)).toBeNull();
    expect(oturumAcikSaniliyor()).toBe(false);
  });

  it("sıfırlama yolu koşul sağlanmadıkça görünmez", async () => {
    guvenlik.durum.mockResolvedValue(KAYIP);
    icerikliKapi();
    await screen.findByRole("heading", { name: "Güvenlik dosyası bulunamadı ya da okunamıyor" });
    expect(
      screen.queryByRole("button", { name: "Güvenlik dosyasını sıfırla ve kuruluma dön" }),
    ).toBeNull();
  });

  it("korunan veri yokken sıfırlama onayla çalışır ve kuruluma döner", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValueOnce(SIFIRLANABILIR).mockResolvedValueOnce(KURULUMA_DONDU);
    guvenlik.sifirla.mockResolvedValue({ ...KURULUMA_DONDU, archived_as: "guvenlik-arsiv-x.json" });
    icerikliKapi();

    await kullanici.click(
      await screen.findByRole("button", { name: "Güvenlik dosyasını sıfırla ve kuruluma dön" }),
    );
    // Onay diyaloğu: başlık soru, gövde sonuç (docs/sozluk.md §3).
    const diyalog = await screen.findByRole("dialog", { name: "Güvenlik dosyası sıfırlansın mı?" });
    expect(diyalog).toHaveTextContent(/arşivlenir/);
    await kullanici.click(screen.getByRole("button", { name: "Sıfırla ve kuruluma dön" }));

    await waitFor(() => expect(guvenlik.sifirla).toHaveBeenCalledTimes(1));
    // Hesap kurulmamış duruma dönüldü: içerik (içteki kurulum kapısı sihirbaza götürür).
    expect(await screen.findByText("Gizli içerik")).toBeInTheDocument();
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });

  it("sıfırlamadan vazgeçilirse istek atılmaz", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(SIFIRLANABILIR);
    icerikliKapi();

    await kullanici.click(
      await screen.findByRole("button", { name: "Güvenlik dosyasını sıfırla ve kuruluma dön" }),
    );
    await kullanici.click(await screen.findByRole("button", { name: "Vazgeç" }));
    expect(guvenlik.sifirla).not.toHaveBeenCalled();
  });

  it("sıfırlama reddedilirse backend iletisini gösterir", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValue(SIFIRLANABILIR);
    guvenlik.sifirla.mockRejectedValue(
      new ApiError(409, "sifirlama_uygun_degil", "Güvenlik dosyası sıfırlanamaz.", {}),
    );
    icerikliKapi();

    await kullanici.click(
      await screen.findByRole("button", { name: "Güvenlik dosyasını sıfırla ve kuruluma dön" }),
    );
    await kullanici.click(await screen.findByRole("button", { name: "Sıfırla ve kuruluma dön" }));
    expect(await screen.findByText("Güvenlik dosyası sıfırlanamaz.")).toBeInTheDocument();
  });

  it("dosya geri konunca “Yeniden denetle” olağan kilit ekranına geçer", async () => {
    const kullanici = userEvent.setup();
    guvenlik.durum.mockResolvedValueOnce(KAYIP).mockResolvedValueOnce(KILITLI);
    icerikliKapi();

    await kullanici.click(await screen.findByRole("button", { name: "Yeniden denetle" }));

    expect(await screen.findByText("Kayıtlar kilitli")).toBeInTheDocument();
    expect(guvenlik.durum).toHaveBeenCalledTimes(2);
  });

  it("açık oturumda gelen 423 içeriği yerelde gizlemez, pencereyi yeniden yükler", async () => {
    guvenlik.durum.mockResolvedValue(ACIK);
    icerikliKapi();
    expect(await screen.findByText("Gizli içerik")).toBeInTheDocument();

    act(() => kilitKapisiYaniti("locked"));

    expect(pencereIcerigi.yenidenYukle).toHaveBeenCalledTimes(1);
    // Durum bu pencerede yeniden okunmaz: yeni pencere okur.
    expect(guvenlik.durum).toHaveBeenCalledTimes(1);
  });

  it("kilit ekranı açıkken gelen 423 (dosya kayboldu) durumu yeniden okur, yüklemez", async () => {
    guvenlik.durum.mockResolvedValueOnce(KILITLI).mockResolvedValueOnce(KAYIP);
    icerikliKapi();
    expect(await screen.findByText("Kayıtlar kilitli")).toBeInTheDocument();

    act(() => kilitKapisiYaniti("guvenlik_dosyasi_kayip"));

    expect(
      await screen.findByRole("heading", { name: "Güvenlik dosyası bulunamadı ya da okunamıyor" }),
    ).toBeInTheDocument();
    expect(guvenlik.durum).toHaveBeenCalledTimes(2);
    expect(pencereIcerigi.yenidenYukle).not.toHaveBeenCalled();
  });
});
