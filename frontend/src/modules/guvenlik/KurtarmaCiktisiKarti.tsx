// "Kurtarma anahtarı belgesi" kartı (katalog dışı program belgesi, tasarım §9.7; kart
// başlığı belge adıdır, sözlük §2-§3) — hesap kurulduktan SONRA belgeyi yeniden almak
// için (ör. elle yazılmış kâğıdın temiz kopyası). Anahtar programda saklanmaz: kullanıcı
// elindeki anahtarı yazar, backend onu kurtarma sarmalına karşı doğrular (yanlışsa
// Türkçe ileti + kademeli gecikme) ve yalnız doğruysa PDF üretir. Kaydedilen dosyanın adı
// backend'in Content-Disposition'ıyla aynıdır (`kurtarma.kurtarmaBelgesiDosyaAdi`).
// Güncel anahtarın kimliği (no, üretim tarihi; tasarım TK10) verilirse kartta yazar:
// zarftaki kâğıdın güncel anahtar olup olmadığı buradan karşılaştırılır.
// Ayarlar → Güvenlik'te ve sihirbazın ilk adımında (hesap zaten kuruluysa) durur.

import { useState } from "react";
import type { FormEvent } from "react";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Icon from "../../ui/Icon";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import type { KurtarmaKimligi } from "./api";
import { KURTARMA_BELGESI_ADI, kurtarmaKimligiMetni, useKurtarmaBelgesi } from "./kurtarma";
import { BELGE_YENIDEN_METNI } from "./metinler";

export default function KurtarmaCiktisiKarti({
  kimlik = null,
}: {
  kimlik?: KurtarmaKimligi | null;
}) {
  const snackbar = useSnackbar();
  const [anahtar, setAnahtar] = useState("");
  const { indir, indiriliyor, hata } = useKurtarmaBelgesi();
  const kimlikMetni = kurtarmaKimligiMetni(kimlik);

  async function gonder(e: FormEvent) {
    e.preventDefault();
    if (await indir(anahtar)) {
      // Anahtar işi bitince alanda bekletilmez.
      setAnahtar("");
      snackbar.success("Kurtarma anahtarı belgesi PDF olarak kaydedildi.");
    }
  }

  return (
    <Card className="p-6">
      <div className="mb-2 flex items-center gap-3">
        <Icon name="picture_as_pdf" className="text-primary" />
        <h2 className="text-title-large text-on-surface">{KURTARMA_BELGESI_ADI}</h2>
      </div>
      {kimlikMetni && (
        <p className="mb-2 text-body-medium text-on-surface">
          {kimlikMetni} (bu bilgisayarda geçerli anahtar)
        </p>
      )}
      <p className="text-body-medium text-on-surface-variant">{BELGE_YENIDEN_METNI}</p>
      <form onSubmit={gonder} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-start">
        <TextField
          className="flex-1 font-mono"
          label="Kurtarma anahtarı"
          value={anahtar}
          onChange={(e) => setAnahtar(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          error={hata ?? undefined}
          required
        />
        <Button
          type="submit"
          variant="tonal"
          icon="download"
          className="sm:mt-7"
          disabled={indiriliyor || !anahtar.trim()}
        >
          {indiriliyor ? "Hazırlanıyor…" : "PDF olarak kaydet"}
        </Button>
      </form>
    </Card>
  );
}
