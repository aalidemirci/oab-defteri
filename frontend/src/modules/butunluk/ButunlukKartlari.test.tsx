// Denetim izi uyarı kartları (tasarım §4.6.3, §4.6.1 kural 1 ve 4, §4.4.4): görünen metin
// sade Türkçedir, iç kod (`kuyruk_kesik`, `seal`…) ve kişi adı yoktur, tarih gg.aa.yyyy
// SS:dd (Europe/Istanbul). Söyleyecek bir şeyi olmayan kart çizilmez.

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../lib/api";
import { gorunenMetin } from "../../test/gorunenMetin";
import { ConfirmProvider } from "../../ui/ConfirmProvider";
import { SnackbarProvider } from "../../ui/SnackbarProvider";
import { butunlukApi } from "./api";
import type {
  ButunlukBulgusu,
  ButunlukDurumu,
  DenetimKartlari,
  EksikEk,
  GeriYuklemeOzeti,
  HesapOzeti,
} from "./api";
import ButunlukKartlari, {
  DegistirilmisHesapKarti,
  DenetimIziKarti,
  EksikEklerKarti,
  GeriYuklemeKarti,
  geriYuklemeDipCumlesi,
} from "./ButunlukKartlari";
import {
  DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
  DENETIM_DEGISIKLIK_CUMLESI,
  DENETIM_DENETLENEMEDI_CUMLESI,
  DENETIM_DENETLENEMEDI_DIP_CUMLESI,
  DENETIM_IZI_KARTI_BASLIGI,
  EKSIK_EKLER_DIP_CUMLESI,
  EKSIK_EKLER_KARTI_BASLIGI,
  EKSIK_EKLER_OKUNAMADI_METNI,
  GERI_YUKLEME_BILDIRIN,
  GERI_YUKLEME_KARTI_BASLIGI,
  GORDUM_ACIKLAMASI,
  GORDUM_KART_KALKTI,
  GORDUM_KAYDEDILEMEDI,
  IKI_DEPO_KARTI_BASLIGI,
  IZ_BOSLUGU_GIRISI,
  KAYIT_DEGISMIS_GIRISI,
  KULLANICILARI_AC,
  OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI,
  PAROLA_KAYDI_ACIKLAMASI,
  PAROLA_KAYDI_GIRISI,
  ROL_DEGISMIS_OLABILIR,
} from "./metinler";

afterEach(() => vi.restoreAllMocks());

/** UTC 07:15 → Europe/Istanbul 10:15. */
const ZAMAN = "2026-11-01T07:15:00Z";
/** Sunucunun hesap özeti açılış ve kapanış gününü de taşır (`iz_dogrulama._hesap_ozeti`). */
const YONETICI = {
  id: "h-1",
  tanitici: "yonetici",
  rol_etiketi: "Program yöneticisi",
  acilis: "2026-11-01",
  kapanis: null,
};
/** Snake_case iç kodlar ve backend'in mühür alan adı ekrana çıkmaz (sözlük §2). */
const IC_KOD = /[a-z]+_[a-z]+|\bseal\b|SIFIRLAMA|KURTARMA|BUTUNLUK/;

function dogrulama(bulgular: string[], duzey: "uyari" | "bilgi" = "uyari"): ButunlukBulgusu {
  return { seq: 12, zaman: ZAMAN, tur: "dogrulama", duzey, bulgular, hesap: null };
}

/** Hesabın kaydı tutmadı: `BUTUNLUK` satırının alan adı (`seal`, `kayit_mac`…) ve hesabı. */
function hesapBulgusu(kod: string, ek: Partial<HesapOzeti> = {}): ButunlukBulgusu {
  return {
    seq: 20,
    zaman: ZAMAN,
    tur: "muhur",
    duzey: "uyari",
    bulgular: [kod],
    hesap: { id: "h-2", tanitici: "muhasip", rol_etiketi: "Muhasip", ...ek },
  };
}

const BOS: ButunlukDurumu = {
  butunluk: [],
  geri_yukleme: null,
  iki_depo: {
    fark_var: false,
    sarmalsiz_hesaplar: [],
    silinebilir_sarmallar: [],
    muhru_tutmayan: [],
  },
  eksik_ekler: [],
  kagit_capasi: { kayit_no: 7, zincir: "C3ED-8364" },
  son_girisler: [],
  parola_yenilenme: null,
  okunamayan: [],
};

const GERI: GeriYuklemeOzeti = {
  seq: 40,
  zaman: ZAMAN,
  geri_yukleme_ani: "2026-10-31T19:15:00Z",
  hesap: YONETICI,
  yol: "hesap",
  yol_hesap: YONETICI,
  oturum_hesap: null,
  kurtarma_no: null,
  yedek: "gunluk-2026-10-31.odbak",
  onceki_dosya: "db-onceki-2026-11-01-101530.sqlite3",
  onceki_sha256: "ab".repeat(32),
  onceki_kayit_no: 42,
  onceki_zincir: "CDCD-CDCD",
  ayrintisiz: false,
  dosyalar: {},
  onceki_geri_yuklemeler: [],
};

/** Sunucunun `dosyalar`ı (`iz_dogrulama`; yanıtta `kapsam` ve beş sayı birlikte gelir). */
const DOSYALAR = {
  kapsam: "tam",
  yerine_konan: 3,
  yetimden_donen: 0,
  eksik: 1,
  bozuk: 2,
  onayla_suruldu: 2,
} as const;

/** `dosya_deposu.eksik_ekler`'in satırı; ad uydurmadır. */
const EKSIK_EK: EksikEk = {
  kayit_turu: "ders yılı",
  kayit_no: "7",
  yukleme_tarihi: "2026-10-01",
  boyut: 4096,
  ozgun_ad: "toplanti-tutanagi.pdf",
};

describe("Denetim İzi Bütünlüğü kartı", () => {
  it("bulgular sade cümleyle ve anıyla yazılır; iç kod yok", () => {
    const { container } = render(
      <DenetimIziKarti
        bulgular={[dogrulama(["kuyruk_kesik", "kilitli_satir_eksik", "zincir_kopuk", "capa_yok"])]}
      />,
    );

    const kart = screen.getByRole("region", { name: DENETIM_IZI_KARTI_BASLIGI });
    expect(
      within(kart).getByText(/son kayıtları silinmiş .* \(geri sarılmış\)/),
    ).toBeInTheDocument();
    expect(within(kart).getByText(/kilitliyken yazılan olaylardan bazıları/)).toBeInTheDocument();
    expect(within(kart).getByText(/zinciri kırık/)).toBeInTheDocument();
    expect(within(kart).getByText(/Kilit işareti bulunamadı/)).toBeInTheDocument();
    expect(within(kart).getByText("01.11.2026 10:15")).toBeInTheDocument();
    expect(within(kart).getByText(/Denetleme Kuruluna bildirin/)).toBeInTheDocument();
    expect(within(kart).getByText(/bir sonraki girişinizde kalkar/)).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("yalnız kesinti varsa bilgi olarak yazılır, bildirim öğüdü yoktur", () => {
    render(<DenetimIziKarti bulgular={[dogrulama(["kesinti"], "bilgi")]} />);

    const kart = screen.getByRole("region", { name: DENETIM_IZI_KARTI_BASLIGI });
    expect(within(kart).getByText(/bir bilgi verdi/)).toBeInTheDocument();
    expect(within(kart).getByText("01.11.2026 10:15 · bilgi")).toBeInTheDocument();
    expect(within(kart).queryByText(/Denetleme Kuruluna bildirin/)).not.toBeInTheDocument();
  });

  it("yalnız denetleyemeyen bulgu varsa değişiklik iddia etmez, geri yüklemeyi öğütlemez", () => {
    // Bağımsız denetim bulgusu: kurulumdan sonra ilk kilitlenmeden önce elektrik kesintisi →
    // "kilit işareti yok" + "işaret yokken yazılmış olaylar". Kart "değişiklik buldu" ve
    // "sağlam bir yedekten geri yüklenir" diyordu.
    render(<DenetimIziKarti bulgular={[dogrulama(["capa_yok", "muhursuz_satir"])]} />);

    const kart = screen.getByRole("region", { name: DENETIM_IZI_KARTI_BASLIGI });
    expect(within(kart).getByText(DENETIM_DENETLENEMEDI_CUMLESI)).toBeInTheDocument();
    expect(within(kart).queryByText(DENETIM_DEGISIKLIK_CUMLESI)).not.toBeInTheDocument();
    expect(within(kart).queryByText(/geri yüklenir/)).not.toBeInTheDocument();
    expect(within(kart).queryByText(/program dışından değiştirilmiş/)).not.toBeInTheDocument();
    expect(within(kart).getByText(DENETIM_DENETLENEMEDI_DIP_CUMLESI)).toBeInTheDocument();
    expect(within(kart).getByText(/Kilit işareti bulunamadı/)).toBeInTheDocument();
  });

  it("denetleyemeyen bulguda kart değişiklik olmadığını da söylemez", () => {
    // Bağımsız denetim bulgusu: "Bu bir değişiklik bulgusu değildir" cümlesi, denetimi
    // düşüren program dışı bir yazımda yanlış bir güvence veriyordu.
    for (const kod of ["capa_yok", "dogrulama_yapilamadi", "muhursuz_satir"]) {
      const { unmount } = render(<DenetimIziKarti bulgular={[dogrulama([kod])]} />);
      const kart = screen.getByRole("region", { name: DENETIM_IZI_KARTI_BASLIGI });
      expect(within(kart).queryByText(/değişiklik bulgusu değildir/)).not.toBeInTheDocument();
      expect(
        within(kart).getByText(/değişiklik olup olmadığı bilinmiyor/),
        kod,
      ).toBeInTheDocument();
      unmount();
    }
  });

  it("doğrulamanın kendi hatası değişiklik iddia etmez, denetlenemedi diye yazılır", () => {
    render(<DenetimIziKarti bulgular={[dogrulama(["dogrulama_yapilamadi"])]} />);
    expect(screen.getByText(DENETIM_DENETLENEMEDI_CUMLESI)).toBeInTheDocument();
    expect(screen.queryByText(/geri yüklenir/)).not.toBeInTheDocument();
  });

  it("anahtarı bulunamayan kayıt değişiklik olarak yazılır, geri yükleme öğütlenir", () => {
    // Bağımsız denetim bulgusu: içeriği değiştirilip anahtar başvurusu bozulan kayıt kartta
    // "denetleyemedi … Bu bir değişiklik bulgusu değildir" diye çıkıyordu.
    const { container } = render(<DenetimIziKarti bulgular={[dogrulama(["anahtar_yok"])]} />);

    const kart = screen.getByRole("region", { name: DENETIM_IZI_KARTI_BASLIGI });
    expect(within(kart).getByText(DENETIM_DEGISIKLIK_CUMLESI)).toBeInTheDocument();
    expect(within(kart).queryByText(DENETIM_DENETLENEMEDI_CUMLESI)).not.toBeInTheDocument();
    expect(within(kart).getByText(/anahtarı bulunamayan kayıt var/)).toBeInTheDocument();
    expect(
      within(kart).getByText(/gerekirse sağlam bir\s+yedekten geri yüklenir/),
    ).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("denetleyemeyen bulgunun yanında değişiklik gösteren bulgu varsa değişiklik der", () => {
    render(
      <DenetimIziKarti
        bulgular={[dogrulama(["capa_yok"]), { ...dogrulama(["mac_tutmadi"]), seq: 14 }]}
      />,
    );
    expect(screen.getByText(DENETIM_DEGISIKLIK_CUMLESI)).toBeInTheDocument();
    expect(screen.getByText(/gerekirse sağlam bir\s+yedekten geri yüklenir/)).toBeInTheDocument();
  });

  it("tanınmayan ya da boş bulgu kodu yazmaz, genel cümleyi yazar", () => {
    const { container } = render(
      <DenetimIziKarti bulgular={[dogrulama(["yeni_bir_bulgu"]), { ...dogrulama([]), seq: 13 }]} />,
    );

    expect(screen.getAllByText("Denetim izinde tanınmayan bir bulgu var.")).toHaveLength(2);
    // Tanınmayan ya da okunamayan bulgu değişiklik sayılır (fail-closed).
    expect(screen.getByText(DENETIM_DEGISIKLIK_CUMLESI)).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("doğrulama bulgusu yoksa kart çizilmez", () => {
    const { container } = render(<DenetimIziKarti bulgular={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Değiştirilmiş Hesap Kaydı kartı", () => {
  it("hesap tanıtıcı ve kaydın söylediği rolle anılır; mühür kodu ve kişi adı yok", () => {
    const { container } = render(
      <DegistirilmisHesapKarti
        bulgular={[
          {
            seq: 9,
            zaman: ZAMAN,
            tur: "muhur",
            duzey: "uyari",
            bulgular: ["seal"],
            hesap: { id: "h-2", tanitici: "muhasip", rol_etiketi: "Sekreter" },
          },
        ]}
      />,
    );

    const kart = screen.getByRole("region", { name: DEGISTIRILMIS_HESAP_KARTI_BASLIGI });
    // Metin nötrdür: olay giriş de olabilir hesap işlemi de (eskiden "giriş açılmadı" diyordu).
    expect(within(kart).getByText(KAYIT_DEGISMIS_GIRISI)).toBeInTheDocument();
    expect(within(kart).queryByText(/giriş açılmadı/)).not.toBeInTheDocument();
    expect(
      within(kart).getByText(
        "Tanıtıcısı “muhasip” olan hesap (kayıtta yazan rol: Sekreter) · 01.11.2026 10:15",
      ),
    ).toBeInTheDocument();
    // Yalnız mühür bulgusunda kayıttaki rolün kendisi değiştirilmiş olabilir.
    expect(within(kart).getByText(ROL_DEGISMIS_OLABILIR)).toBeInTheDocument();
    expect(within(kart).getByText(/Durumu Denetleme Kuruluna bildirin\./)).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("satırın izi tutmayan hesap kaydı değiştirilmiş hesap gibi yazılır; rolü doğrudur", () => {
    render(
      <DegistirilmisHesapKarti
        bulgular={[hesapBulgusu("kayit_mac", { acilis: "2026-11-01", kapanis: null })]}
      />,
    );

    const kart = screen.getByRole("region", { name: DEGISTIRILMIS_HESAP_KARTI_BASLIGI });
    expect(within(kart).getByText(KAYIT_DEGISMIS_GIRISI)).toBeInTheDocument();
    expect(
      within(kart).getByText("Muhasip · tanıtıcı muhasip (açılış 01.11.2026) · 01.11.2026 10:15"),
    ).toBeInTheDocument();
    expect(within(kart).queryByText(ROL_DEGISMIS_OLABILIR)).not.toBeInTheDocument();
    expect(within(kart).queryByText(/kayıtta yazan rol/)).not.toBeInTheDocument();
  });

  it("iz boşluğu değişen denetim izini anar, hesap kaydını suçlamaz", () => {
    const { container } = render(
      <DegistirilmisHesapKarti bulgular={[hesapBulgusu("iz_boslugu")]} />,
    );

    const kart = screen.getByRole("region", { name: DEGISTIRILMIS_HESAP_KARTI_BASLIGI });
    expect(within(kart).getByText(IZ_BOSLUGU_GIRISI)).toBeInTheDocument();
    expect(within(kart).queryByText(KAYIT_DEGISMIS_GIRISI)).not.toBeInTheDocument();
    expect(within(kart).queryByText(ROL_DEGISMIS_OLABILIR)).not.toBeInTheDocument();
    expect(
      within(kart).getByText("Muhasip · tanıtıcı muhasip · 01.11.2026 10:15"),
    ).toBeInTheDocument();
    expect(within(kart).getByText(/Durumu Denetleme Kuruluna bildirin\./)).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("parola kaydı bulgusu ayrı cümleyle yazılır: rol doğrudur, çaresi sıfırlama ya da kurtarma anahtarı", () => {
    const { container } = render(
      <DegistirilmisHesapKarti bulgular={[hesapBulgusu("wrap_digest")]} />,
    );

    const kart = screen.getByRole("region", { name: DEGISTIRILMIS_HESAP_KARTI_BASLIGI });
    expect(within(kart).getByText(PAROLA_KAYDI_GIRISI)).toBeInTheDocument();
    // Aynı bulgu açık oturumdaki parola işleminde de yazılır: kart "giriş açılmadı" demez.
    expect(within(kart).queryByText(/giriş açılmadı/)).not.toBeInTheDocument();
    expect(within(kart).getByText(PAROLA_KAYDI_ACIKLAMASI)).toBeInTheDocument();
    expect(within(kart).getByText(/hesap kaydındaki rol doğrudur/)).toBeInTheDocument();
    expect(within(kart).getByText(/“Parolamı unuttum” yolundan kurtarma/)).toBeInTheDocument();
    // "Rol değiştirilmiş olabilir" yalnız mühür bulgusundadır.
    expect(within(kart).queryByText(ROL_DEGISMIS_OLABILIR)).not.toBeInTheDocument();
    expect(within(kart).queryByText(KAYIT_DEGISMIS_GIRISI)).not.toBeInTheDocument();
    expect(within(kart).getByText(/Durumu Denetleme Kuruluna bildirin\./)).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("türler bir arada olunca her biri kendi cümlesiyle; tanınmayan kod mühür sayılır", () => {
    render(
      <DegistirilmisHesapKarti
        bulgular={[
          { ...hesapBulgusu("yeni_bir_alan"), seq: 21 },
          { ...hesapBulgusu("iz_boslugu"), seq: 22 },
          { ...hesapBulgusu("wrap_digest"), seq: 23 },
        ]}
      />,
    );

    const kart = screen.getByRole("region", { name: DEGISTIRILMIS_HESAP_KARTI_BASLIGI });
    expect(within(kart).getByText(KAYIT_DEGISMIS_GIRISI)).toBeInTheDocument();
    expect(within(kart).getByText(IZ_BOSLUGU_GIRISI)).toBeInTheDocument();
    expect(within(kart).getByText(PAROLA_KAYDI_GIRISI)).toBeInTheDocument();
    // Tanınmayan kodda (fail-closed) rol de değiştirilmiş olabilir.
    expect(within(kart).getByText(ROL_DEGISMIS_OLABILIR)).toBeInTheDocument();
    expect(
      within(kart).getByText(/^Tanıtıcısı “muhasip” olan hesap \(kayıtta yazan rol: Muhasip\)/),
    ).toBeInTheDocument();
    expect(within(kart).getAllByRole("listitem")).toHaveLength(3);
  });

  it("mühür bulgusunda günler de kaydın söylediğidir; okunamayan açılış günü söylenir", () => {
    render(
      <DegistirilmisHesapKarti
        bulgular={[hesapBulgusu("seal", { acilis: null, kapanis: "2026-11-03" })]}
      />,
    );

    expect(
      screen.getByText(
        "Tanıtıcısı “muhasip” olan hesap (kayıtta yazan rol: Muhasip; açılış günü okunamadı, " +
          "kapanış 03.11.2026) · 01.11.2026 10:15",
      ),
    ).toBeInTheDocument();
  });

  it("kaydı okunamayan hesap da anılır; doğrulama bulguları bu kartta değildir", () => {
    render(
      <DegistirilmisHesapKarti
        bulgular={[
          dogrulama(["capa_yok"]),
          { seq: 10, zaman: ZAMAN, tur: "muhur", duzey: "uyari", bulgular: [], hesap: null },
        ]}
      />,
    );

    expect(screen.getByText(/^Kaydı okunamayan bir hesap/)).toBeInTheDocument();
    expect(screen.queryByText(/Kilit işareti/)).not.toBeInTheDocument();
  });
});

describe("Yedekten Geri Yükleme Yapıldı kartı", () => {
  it("yedeğin adını, açan hesabı, önceki veritabanını ve son kaydını yazar", () => {
    const { container } = render(<GeriYuklemeKarti geri={GERI} />);

    const kart = screen.getByRole("region", { name: GERI_YUKLEME_KARTI_BASLIGI });
    expect(within(kart).getByText(/Kayıtlar bir yedekten geri yüklendi/)).toBeInTheDocument();
    // Geri yüklemenin anı (nottan) ile denetim izine yazıldığı an (ilk giriş) ayrı yazılır.
    expect(within(kart).getByText("Geri yükleme anı").nextElementSibling).toHaveTextContent(
      "31.10.2026 22:15",
    );
    expect(
      within(kart).getByText("Denetim izine yazıldığı an").nextElementSibling,
    ).toHaveTextContent("01.11.2026 10:15");
    expect(within(kart).getByText("gunluk-2026-10-31.odbak")).toBeInTheDocument();
    expect(
      within(kart).getByText(
        "Program yöneticisi · tanıtıcı yonetici (açılış 01.11.2026) hesabının parolası",
      ),
    ).toBeInTheDocument();
    expect(within(kart).getByText("db-onceki-2026-11-01-101530.sqlite3")).toBeInTheDocument();
    expect(within(kart).getByText("Kayıt no: 42 · Zincir: CDCD-CDCD")).toBeInTheDocument();
    // "Gördüm" diyemeyen hesap (program yöneticisi): kart kimin kaldırdığını ve DK hesabı yoksa
    // kalacağını söyler; düğme yok.
    expect(
      within(kart).getByText(/Denetleme Kuruluna bildirin. Kart, Denetleme/),
    ).toBeInTheDocument();
    expect(
      within(kart).getByText(/Denetleme Kurulunun açık hesabı yoksa kart kalır/),
    ).toBeInTheDocument();
    expect(within(kart).queryByText(/göstermeyi sürdürür/)).not.toBeInTheDocument();
    expect(within(kart).queryByRole("button")).not.toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("kurtarma anahtarı yolunda anahtar no'sunu, elden getirilen dosyada adın kayda geçmediğini yazar", () => {
    render(
      <GeriYuklemeKarti
        geri={{ ...GERI, yol: "kurtarma", yol_hesap: null, kurtarma_no: 3, yedek: null }}
      />,
    );

    expect(screen.getByText("Kurtarma anahtarı (anahtar no 3)")).toBeInTheDocument();
    expect(screen.getByText("Elden getirilen dosya (adı kayda geçmez)")).toBeInTheDocument();
    // Konsoldan yapılan geri yüklemede oturum yoktur: satır çizilmez.
    expect(screen.queryByText("Başlatan oturum")).not.toBeInTheDocument();
  });

  it("uygulama içinden yapılan geri yüklemeyi başlatan oturumun hesabını yazar (kurtarma yolunda da)", () => {
    render(
      <GeriYuklemeKarti
        geri={{ ...GERI, yol: "kurtarma", yol_hesap: null, kurtarma_no: 3, oturum_hesap: YONETICI }}
      />,
    );

    expect(screen.getByText("Başlatan oturum").nextElementSibling?.textContent).toBe(
      "Program yöneticisi · tanıtıcı yonetici (açılış 01.11.2026)",
    );
  });

  it("yedeğin kapsamını ve eklerin kişisiz sayılarını satır olarak yazar", () => {
    render(<GeriYuklemeKarti geri={{ ...GERI, dosyalar: DOSYALAR }} />);

    expect(screen.getByText("Yedeğin kapsamı").nextElementSibling?.textContent).toBe(
      "kayıtlar, ekler ve üretilen evrak",
    );
    expect(screen.getByText("Ekler").nextElementSibling?.textContent).toBe(
      "3 ek yerine kondu · 1 ek eksik · 2 bozuk ek onayla geride bırakıldı",
    );
  });

  it("yerel yedekte sorunsuz geri yükleme eksik ek olmadığını söyler", () => {
    render(
      <GeriYuklemeKarti
        geri={{
          ...GERI,
          dosyalar: {
            kapsam: "yerel",
            yerine_konan: 0,
            yetimden_donen: 0,
            eksik: 0,
            bozuk: 0,
            onayla_suruldu: 0,
          },
        }}
      />,
    );

    expect(screen.getByText("Yedeğin kapsamı").nextElementSibling?.textContent).toBe(
      "yalnız kayıtlar; ekler bu bilgisayardan alınır",
    );
    expect(screen.getByText("Ekler").nextElementSibling?.textContent).toBe(
      "eksik ya da bozuk ek yok",
    );
  });

  it("dosya bilgisi taşımayan eski satırda kapsam ve ek satırı çizilmez", () => {
    render(<GeriYuklemeKarti geri={GERI} />);

    expect(screen.queryByText("Yedeğin kapsamı")).not.toBeInTheDocument();
    expect(screen.queryByText("Ekler")).not.toBeInTheDocument();
  });

  it("sayının biri satıra girmediyse eksik ek olmadığı söylenmez", () => {
    render(
      <GeriYuklemeKarti
        geri={{ ...GERI, dosyalar: { kapsam: "tam", yerine_konan: 0, eksik: 0, bozuk: 0 } }}
      />,
    );

    expect(screen.getByText("Yedeğin kapsamı")).toBeInTheDocument();
    expect(screen.queryByText("Ekler")).not.toBeInTheDocument();
    expect(screen.queryByText(/ek yok/)).not.toBeInTheDocument();
  });

  it("birden çok geri yüklemede her geri yükleme kendi sayılarını yazar", () => {
    const ilk = { ...GERI, seq: 38, dosyalar: { ...DOSYALAR, yerine_konan: 5 } };
    render(
      <GeriYuklemeKarti geri={{ ...GERI, dosyalar: DOSYALAR, onceki_geri_yuklemeler: [ilk] }} />,
    );

    expect(screen.getByText(/^5 ek yerine kondu/)).toBeInTheDocument();
    expect(screen.getByText(/^3 ek yerine kondu/)).toBeInTheDocument();
  });

  it("dip cümlesi kenara alınan dosyanın 14 gün sonra silindiğini söyler", () => {
    expect(geriYuklemeDipCumlesi([GERI])).toBe(
      "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; kenara alınan önceki " +
        "veritabanında durur. O dosya geri yüklemeden 14 gün sonra silinir.",
    );
    expect(geriYuklemeDipCumlesi([GERI, { ...GERI, seq: 41 }])).toBe(
      "Yedeğin alındığı günden sonra girilen kayıtlar ekrandan kalkmıştır; ilk geri yüklemede " +
        "kenara alınan veritabanında durur. O dosya geri yüklemeden 14 gün sonra silinir.",
    );
    // Yeni bilgisayara taşımada kenara alınan yoktur: silinecek dosya da anılmaz.
    expect(geriYuklemeDipCumlesi([{ ...GERI, onceki_dosya: null, onceki_kayit_no: null }])).toBe(
      "Geri yüklemeden önce bu bilgisayarda kayıt yoktu.",
    );
  });

  it("ayrıntısız geri yüklemede olgu yine yazılır", () => {
    render(
      <GeriYuklemeKarti
        geri={{ ...GERI, ayrintisiz: true, yol: null, yedek: null, onceki_dosya: null }}
      />,
    );

    expect(
      screen.getByText(/ayrıntıları okunamadı; olgu denetim izinde kayıtlıdır/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Yedeği açan")).not.toBeInTheDocument();
  });

  it("aralarında giriş yapılmadan yapılan geri yüklemelerin hepsini sırasıyla yazar", () => {
    // Bağımsız denetim bulgusu: kart yalnız son satırı gösteriyordu; yedekten sonraki kayıtlar
    // İLK geri yüklemenin kenara aldığı veritabanındadır.
    const ilk = {
      ...GERI,
      seq: 38,
      yedek: "gunluk-2026-10-30.odbak",
      onceki_dosya: "db-onceki-2026-11-01-091000.sqlite3",
      onceki_kayit_no: 120,
      onceki_zincir: "AAAA-1111",
    };
    const { container } = render(
      <GeriYuklemeKarti geri={{ ...GERI, onceki_geri_yuklemeler: [ilk] }} />,
    );

    const kart = screen.getByRole("region", { name: GERI_YUKLEME_KARTI_BASLIGI });
    expect(within(kart).getByText(/aralarında giriş yapılmadan 2 kez/)).toBeInTheDocument();
    const basliklar = within(kart)
      .getAllByRole("heading", { level: 3 })
      .map((h) => h.textContent);
    expect(basliklar).toEqual(["1. geri yükleme", "2. geri yükleme (son)"]);
    expect(within(kart).getByText("db-onceki-2026-11-01-091000.sqlite3")).toBeInTheDocument();
    expect(within(kart).getByText("Kayıt no: 120 · Zincir: AAAA-1111")).toBeInTheDocument();
    expect(within(kart).getByText("db-onceki-2026-11-01-101530.sqlite3")).toBeInTheDocument();
    expect(
      within(kart).getByText(/ilk geri yüklemede kenara alınan veritabanında durur/),
    ).toBeInTheDocument();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("bozuk notun ayrıntısız geri yüklemesi önce, okunabilen sonuncusu son yazılır", () => {
    const ayrintisiz = {
      ...GERI,
      seq: 39,
      ayrintisiz: true,
      geri_yukleme_ani: null,
      yol: null,
      yedek: null,
      onceki_dosya: null,
      onceki_kayit_no: null,
      onceki_zincir: null,
    };
    render(<GeriYuklemeKarti geri={{ ...GERI, onceki_geri_yuklemeler: [ayrintisiz] }} />);

    const [birinci, ikinci] = screen.getAllByRole("listitem");
    expect(within(birinci).getByText(/ayrıntıları okunamadı/)).toBeInTheDocument();
    expect(within(ikinci).getByText("gunluk-2026-10-31.odbak")).toBeInTheDocument();
    // Asıl dönüş yolu bilinmiyor: "kayıt yoktu" denmez.
    expect(screen.queryByText(/kayıt yoktu/)).not.toBeInTheDocument();
  });

  it.each([
    ["kenara alınacak veritabanı yoktu", { onceki_dosya: null, onceki_kayit_no: null }],
    ["kenara alınan veritabanının izi boştu", { onceki_kayit_no: 0, onceki_zincir: null }],
  ])("%s: “kayıtlar ekrandan kalktı” demez, önceden kayıt olmadığını söyler", (_ad, degisen) => {
    // Bağımsız denetim bulgusu: yeni bilgisayara taşımada kaybolan kayıt yoktur.
    render(<GeriYuklemeKarti geri={{ ...GERI, ...degisen }} />);

    expect(
      screen.getByText(/Geri yüklemeden önce bu bilgisayarda kayıt yoktu\./),
    ).toBeInTheDocument();
    expect(screen.queryByText(/ekrandan kalkmıştır/)).not.toBeInTheDocument();
    expect(
      screen.getByText(/Denetleme Kurulunun açık hesabı yoksa kart kalır/),
    ).toBeInTheDocument();
  });

  it("geri yükleme yoksa kart çizilmez", () => {
    const { container } = render(<GeriYuklemeKarti geri={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Eksik Ekler kartı", () => {
  it("söyleyecek bir şey yoksa çizilmez", () => {
    const { container } = render(<EksikEklerKarti ekler={[]} okunamadi={false} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("her eki özgün adı, kaydı, tarihi ve boyuyla yazar; iç kod yok", () => {
    const { container } = render(
      <EksikEklerKarti ekler={[EKSIK_EK, { ...EKSIK_EK, kayit_no: "9" }]} okunamadi={false} />,
    );

    const kart = screen.getByRole("region", { name: EKSIK_EKLER_KARTI_BASLIGI });
    expect(
      within(kart).getByText("2 ekin kaydı duruyor ama dosyası bu bilgisayarda bulunamadı:"),
    ).toBeInTheDocument();
    expect(
      within(kart).getByText("toplanti-tutanagi.pdf · ders yılı · no 7 · 01.10.2026 · 4 KB"),
    ).toBeInTheDocument();
    expect(within(kart).getByText(EKSIK_EKLER_DIP_CUMLESI)).toBeInTheDocument();
    expect(within(kart).queryByText(EKSIK_EKLER_OKUNAMADI_METNI)).toBeNull();
    expect(gorunenMetin(container)).not.toMatch(IC_KOD);
  });

  it("uzun liste klavyeyle de kayar: kaydırma kutusu odak alır", () => {
    render(<EksikEklerKarti ekler={[EKSIK_EK]} okunamadi={false} />);

    expect(screen.getByRole("list", { name: EKSIK_EKLER_KARTI_BASLIGI })).toHaveAttribute(
      "tabindex",
      "0",
    );
  });

  it("özgün adı çözülemeyen ek listeden düşmez, adı okunamadı der", () => {
    render(<EksikEklerKarti ekler={[{ ...EKSIK_EK, ozgun_ad: null }]} okunamadi={false} />);

    expect(
      screen.getByText("Adı okunamayan ek · ders yılı · no 7 · 01.10.2026 · 4 KB"),
    ).toBeInTheDocument();
  });

  it("depo okunamadıysa “eksik yok” demez, okunamadığını söyler", () => {
    render(<EksikEklerKarti ekler={[]} okunamadi />);

    const kart = screen.getByRole("region", { name: EKSIK_EKLER_KARTI_BASLIGI });
    expect(within(kart).getByText(EKSIK_EKLER_OKUNAMADI_METNI)).toBeInTheDocument();
    expect(within(kart).queryByRole("list")).toBeNull();
    expect(within(kart).queryByText(EKSIK_EKLER_DIP_CUMLESI)).toBeNull();
  });
});

describe("ButunlukKartlari", () => {
  it("söyleyecek bir şey yoksa hiçbir kart çizilmez", () => {
    const { container } = render(<ButunlukKartlari durum={BOS} onIkiDepo={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("eksik ek varken Eksik Ekler kartı çizilir", () => {
    render(<ButunlukKartlari durum={{ ...BOS, eksik_ekler: [EKSIK_EK] }} onIkiDepo={vi.fn()} />);

    expect(screen.getByRole("region", { name: EKSIK_EKLER_KARTI_BASLIGI })).toBeInTheDocument();
  });

  it("depo okunamadıysa genel uyarı kartı da Eksik Ekler kartı da çizilir", () => {
    render(
      <ButunlukKartlari durum={{ ...BOS, okunamayan: ["eksik_ekler"] }} onIkiDepo={vi.fn()} />,
    );

    expect(
      screen.getByRole("region", { name: OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI }),
    ).toBeInTheDocument();
    expect(screen.getByText(EKSIK_EKLER_OKUNAMADI_METNI)).toBeInTheDocument();
  });

  it("başka bir kart okunamadıysa Eksik Ekler kartı çizilmez", () => {
    render(
      <ButunlukKartlari durum={{ ...BOS, okunamayan: ["geri_yukleme"] }} onIkiDepo={vi.fn()} />,
    );

    expect(screen.queryByRole("region", { name: EKSIK_EKLER_KARTI_BASLIGI })).toBeNull();
  });

  it("iki depo farkı kendiliğinden hesaplanamadıysa (null) kart çizilmez", () => {
    const { container } = render(
      <ButunlukKartlari durum={{ ...BOS, iki_depo: null }} onIkiDepo={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("okunamayan kart varsa uyarı kartı çizilir (uyarı sessizce kaybolmaz)", () => {
    render(
      <ButunlukKartlari durum={{ ...BOS, okunamayan: ["geri_yukleme"] }} onIkiDepo={vi.fn()} />,
    );

    const kart = screen.getByRole("region", { name: OKUNAMAYAN_BUTUNLUK_KARTI_BASLIGI });
    expect(within(kart).getByText(/kartları tam okunamadı/)).toBeInTheDocument();
    // Son Girişler de kapsanır: metin yalnız "uyarı kartları" demez.
    expect(within(kart).getByText(/bir uyarı ya da giriş gösterilemiyor/)).toBeInTheDocument();
    expect(gorunenMetin(kart)).not.toMatch(IC_KOD);
  });

  it("dört kart sırasıyla çizilir", () => {
    render(
      <SnackbarProvider>
        <ConfirmProvider>
          <ButunlukKartlari
            durum={{
              ...BOS,
              butunluk: [
                dogrulama(["kuyruk_kesik"]),
                {
                  seq: 9,
                  zaman: ZAMAN,
                  tur: "muhur",
                  duzey: "uyari",
                  bulgular: ["seal"],
                  hesap: { id: "h-2", tanitici: "muhasip", rol_etiketi: "Muhasip" },
                },
              ],
              geri_yukleme: GERI,
              iki_depo: {
                fark_var: true,
                sarmalsiz_hesaplar: [
                  { id: "h-2", tanitici: "muhasip", rol_etiketi: "Muhasip", kapali: false },
                ],
                silinebilir_sarmallar: [],
                muhru_tutmayan: [],
              },
            }}
            onIkiDepo={vi.fn()}
          />
        </ConfirmProvider>
      </SnackbarProvider>,
    );

    const basliklar = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(basliklar).toEqual([
      DENETIM_IZI_KARTI_BASLIGI,
      DEGISTIRILMIS_HESAP_KARTI_BASLIGI,
      GERI_YUKLEME_KARTI_BASLIGI,
      IKI_DEPO_KARTI_BASLIGI,
    ]);
  });
});

describe("Yedekten Geri Yükleme Yapıldı kartının “Gördüm”ü", () => {
  /** "Gördüm"den dönen güncel denetim kartları: kart kalktı. */
  const KALKTI: DenetimKartlari = {
    butunluk: [],
    geri_yukleme: null,
    muhru_tutmayan: [],
    eksik_ekler: [],
    okunamayan: [],
  };

  function bas(geri: GeriYuklemeOzeti = GERI) {
    const islem = { onDenetim: vi.fn(), onYenile: vi.fn() };
    render(
      <SnackbarProvider>
        <GeriYuklemeKarti geri={geri} gordum={islem} />
      </SnackbarProvider>,
    );
    return islem;
  }

  it("düğme yalnız “Gördüm” verilince çizilir; metin bir üyenin yettiğini söyler", () => {
    bas();

    const kart = screen.getByRole("region", { name: GERI_YUKLEME_KARTI_BASLIGI });
    expect(within(kart).getByRole("button", { name: "Gördüm" })).toBeEnabled();
    expect(within(kart).getByText(new RegExp(GORDUM_ACIKLAMASI))).toBeInTheDocument();
    // "Gördüm" diyen hesaba "Denetleme Kuruluna bildirin" denmez.
    expect(within(kart).queryByText(new RegExp(GERI_YUKLEME_BILDIRIN))).not.toBeInTheDocument();
  });

  it("kartın gösterdiği geri yüklemenin sırası gider; kart kalkınca snackbar söyler", async () => {
    const user = userEvent.setup();
    const gordum = vi.spyOn(butunlukApi, "geriYuklemeyiGordum").mockResolvedValue(KALKTI);
    const islem = bas();

    await user.click(screen.getByRole("button", { name: "Gördüm" }));

    expect(gordum).toHaveBeenCalledWith(GERI.seq);
    await waitFor(() => expect(islem.onDenetim).toHaveBeenCalledWith(KALKTI));
    expect(await screen.findByText(GORDUM_KART_KALKTI)).toBeInTheDocument();
    expect(islem.onYenile).not.toHaveBeenCalled();
  });

  it("kart yanıtta kalıyorsa snackbar “kalktı” demez; kart yanıtla yenilenir", async () => {
    const user = userEvent.setup();
    const kalan: DenetimKartlari = { ...KALKTI, geri_yukleme: { ...GERI, seq: 41 } };
    vi.spyOn(butunlukApi, "geriYuklemeyiGordum").mockResolvedValue(kalan);
    const islem = bas();

    await user.click(screen.getByRole("button", { name: "Gördüm" }));

    await waitFor(() => expect(islem.onDenetim).toHaveBeenCalledWith(kalan));
    expect(screen.queryByText(GORDUM_KART_KALKTI)).not.toBeInTheDocument();
  });

  it("sürerken düğme kapalıdır ve süren işi söyler", async () => {
    const user = userEvent.setup();
    let bitir: (yanit: DenetimKartlari) => void = () => undefined;
    vi.spyOn(butunlukApi, "geriYuklemeyiGordum").mockReturnValue(
      new Promise((resolve) => {
        bitir = resolve;
      }),
    );
    bas();

    await user.click(screen.getByRole("button", { name: "Gördüm" }));

    expect(screen.getByRole("button", { name: "Kaydediliyor…" })).toBeDisabled();
    bitir(KALKTI);
    expect(await screen.findByRole("button", { name: "Gördüm" })).toBeEnabled();
  });

  it("kart artık güncel değilse (409) kartlar yeniden okunur, sunucunun iletisi kalır", async () => {
    const user = userEvent.setup();
    const ileti =
      "Bu geri yükleme kartı artık güncel değil; Genel Bakış'ı yenileyip yeniden deneyin.";
    vi.spyOn(butunlukApi, "geriYuklemeyiGordum").mockRejectedValue(
      new ApiError(409, "geri_yukleme_guncel_degil", ileti),
    );
    const islem = bas();

    await user.click(screen.getByRole("button", { name: "Gördüm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(ileti);
    expect(islem.onYenile).toHaveBeenCalledTimes(1);
    expect(islem.onDenetim).not.toHaveBeenCalled();
  });

  it.each([
    [
      new ApiError(403, "rol_yetkisiz", "Bu işlem hesabınızın rolüne açık değil."),
      /rolüne açık değil/,
    ],
    [new ApiError(409, "hesap_muhru_tutmadi", ""), /program dışından değiştirilmiş/],
    [new TypeError("Failed to fetch"), new RegExp(GORDUM_KAYDEDILEMEDI)],
  ])(
    "öteki retlerde ileti düğmenin altında kalır, kartlar yeniden okunmaz (%#)",
    async (hata, metin) => {
      const user = userEvent.setup();
      vi.spyOn(butunlukApi, "geriYuklemeyiGordum").mockRejectedValue(hata);
      const islem = bas();

      await user.click(screen.getByRole("button", { name: "Gördüm" }));

      expect(await screen.findByRole("alert")).toHaveTextContent(metin);
      expect(islem.onYenile).not.toHaveBeenCalled();
      // Kod ekrana çıkmaz.
      expect(screen.getByRole("alert")).not.toHaveTextContent(/[a-z]+_[a-z]+/);
    },
  );
});

describe("ButunlukKartlari — yeteneğe bağlı denetimler", () => {
  it("“Gördüm” ve Kullanıcılar bağlantısı yalnız verilince çizilir", () => {
    const durum: ButunlukDurumu = {
      ...BOS,
      geri_yukleme: GERI,
      iki_depo: {
        fark_var: true,
        sarmalsiz_hesaplar: [
          { id: "h-2", tanitici: "muhasip", rol_etiketi: "Muhasip", kapali: false },
        ],
        silinebilir_sarmallar: [],
        muhru_tutmayan: [],
      },
    };
    const { unmount } = render(
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <ButunlukKartlari durum={durum} onIkiDepo={vi.fn()} />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>,
    );
    expect(screen.queryByRole("button", { name: "Gördüm" })).toBeNull();
    expect(screen.queryByRole("link", { name: KULLANICILARI_AC })).toBeNull();
    unmount();

    render(
      <MemoryRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <ButunlukKartlari
              durum={durum}
              onIkiDepo={vi.fn()}
              gordum={{ onDenetim: vi.fn(), onYenile: vi.fn() }}
              kullanicilarAcik
            />
          </ConfirmProvider>
        </SnackbarProvider>
      </MemoryRouter>,
    );
    expect(screen.getByRole("button", { name: "Gördüm" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: KULLANICILARI_AC })).toHaveAttribute(
      "href",
      "/kullanicilar",
    );
  });
});
