import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import ModuleHeader from "./ModuleHeader";

function renderAt(initial: string) {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route
          path="/kisiler/kisi"
          element={<ModuleHeader backTo="/kisiler" moduleLabel="Kişiler" title="Kişi Ayrıntısı" />}
        />
        <Route path="/kisiler" element={<div>KİŞİLER ANA SAYFASI</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ModuleHeader", () => {
  it("başlık ve modül adını basar", () => {
    renderAt("/kisiler/kisi");
    expect(screen.getByRole("heading", { name: "Kişi Ayrıntısı" })).toBeInTheDocument();
    expect(screen.getByText("Kişiler")).toBeInTheDocument();
  });

  it("geri butonu modül köküne gider (erişilebilir ad ile)", async () => {
    renderAt("/kisiler/kisi");
    const back = screen.getByRole("link", { name: "Kişiler ana sayfasına dön" });
    await userEvent.click(back);
    expect(screen.getByText("KİŞİLER ANA SAYFASI")).toBeInTheDocument();
  });
});
