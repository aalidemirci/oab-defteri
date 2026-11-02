// "Son Girişler" kartı (tasarım §4.6.3 "Kâğıt çapası"): oturumdaki hesabın girişleri
// gg.aa.yyyy SS:dd (Europe/Istanbul), ilki bu oturum; altında denetim izinin son kaydı
// "Kayıt no: N · Zincir: XXXX-XXXX" ve kâğıda not etme öğüdü. Kişi adı yok.

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { gorunenMetin } from "../../test/gorunenMetin";
import { SON_GIRISLER_KARTI_BASLIGI } from "./metinler";
import SonGirislerKarti from "./SonGirislerKarti";

function kart(): HTMLElement {
  return screen.getByRole("region", { name: SON_GIRISLER_KARTI_BASLIGI });
}

describe("Son Girişler kartı", () => {
  it("girişleri yerel saatle yazar, ilki bu oturumdur; kâğıt çapası satırı altta", () => {
    render(
      <SonGirislerKarti
        girisler={["2026-11-01T10:15:00+03:00", "2026-10-31T21:30:00Z"]}
        capa={{ kayit_no: 128, zincir: "C3ED-8364" }}
      />,
    );

    const ogeler = within(kart())
      .getAllByRole("listitem")
      .map((li) => li.textContent);
    // 31.10.2026 21:30 UTC → 01.11.2026 00:30 Europe/Istanbul (gün yerel saatten okunur).
    expect(ogeler).toEqual(["01.11.2026 10:15 · bu oturum", "01.11.2026 00:30"]);
    expect(within(kart()).getByText("Denetim izinin son kaydı")).toBeInTheDocument();
    expect(within(kart()).getByText("Kayıt no: 128 · Zincir: C3ED-8364")).toBeInTheDocument();
    expect(
      within(kart()).getByText(/zaman zaman tarihiyle birlikte kâğıda not edin/),
    ).toBeInTheDocument();
    expect(gorunenMetin(kart())).not.toMatch(/GIRIS|[a-z]+_[a-z]+/);
  });

  it("giriş yoksa söyler; zincir boşsa son kayıt satırı yoktur", () => {
    render(<SonGirislerKarti girisler={[]} capa={null} />);

    expect(
      within(kart()).getByText("Bu hesapla henüz kilit ekranından giriş yapılmadı."),
    ).toBeInTheDocument();
    expect(within(kart()).queryByText(/Kayıt no:/)).not.toBeInTheDocument();
    expect(within(kart()).queryByRole("list")).not.toBeInTheDocument();
  });

  it("girişler okunamadıysa “henüz giriş yapılmadı” demez, okunamadı der", () => {
    // Bağımsız denetim bulgusu: backend okunamayan kartı boş listeyle doldurur; kart bunu
    // "hiç giriş yok" diye yazıyor, gerçek girişler ve tanımadığınız giriş öğüdü kayboluyordu.
    render(
      <SonGirislerKarti
        girisler={[]}
        capa={{ kayit_no: 128, zincir: "C3ED-8364" }}
        girislerOkunamadi
      />,
    );

    expect(within(kart()).getByText(/Son girişler okunamadı/)).toBeInTheDocument();
    expect(within(kart()).getByText(/tanımadığınız bir giriş/)).toBeInTheDocument();
    expect(within(kart()).queryByText(/henüz kilit ekranından giriş/)).not.toBeInTheDocument();
    expect(within(kart()).getByText("Kayıt no: 128 · Zincir: C3ED-8364")).toBeInTheDocument();
  });

  it("son kayıt okunamadıysa satır sessizce silinmez, okunamadı der", () => {
    render(<SonGirislerKarti girisler={["2026-11-01T10:15:00+03:00"]} capa={null} capaOkunamadi />);

    expect(within(kart()).getByText("Denetim izinin son kaydı okunamadı.")).toBeInTheDocument();
    expect(within(kart()).queryByText(/Kayıt no:/)).not.toBeInTheDocument();
    expect(within(kart()).getByText("01.11.2026 10:15 · bu oturum")).toBeInTheDocument();
    expect(gorunenMetin(kart())).not.toMatch(/[a-z]+_[a-z]+/);
  });
});
