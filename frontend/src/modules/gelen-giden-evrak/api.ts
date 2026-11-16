// Gelen-Giden Evrak ekranının API istemcisi — backend `apps/oab/views_genel_kurul.py`
// (`DocumentBookListView`, `DocumentRecordListView`, `DocumentRecordAttachmentsView`,
// `DocumentOutgoingRecordView`) ile BİREBİR (plan F2 §6.1 M10; tasarım §5.2.8). Gövde ve yanıt
// anahtarları sunucununkidir. Karşı taraf ve konu şifreli saklanır; çözülemezse `null` gelir.
// Numara tekilliği serttir (hesap bütünlüğü), sıra atlama uyarı + gerekçedir (400 `gerekce_gerekli`).

import { api } from "../../lib/api";
import type { Ek, GerekceEki } from "../genel-kurul/api";

export type EvrakYonu = "GELEN" | "GIDEN";
export type TasdikMakami = "NOTER" | "IL_ILCE_MEM";

/** Gelen-giden evrak defteri. */
export interface EvrakDefteri {
  id: number;
  status: "KULLANIMDA" | "DOLDU" | "ARSIVDE" | "IPTAL";
  certified_by: TasdikMakami | "";
  certified_on: string | null;
  certification_no: string;
  page_count: number | null;
  opened_on: string | null;
  last_no_before_program: number | null;
  /** Bu yılın sıradaki numarası. */
  siradaki_no: number;
}

export interface DefterListesi {
  defterler: EvrakDefteri[];
  /** Kullanımdaki en yeni defter (yoksa null). */
  varsayilan: number | null;
}

export interface DefterGovdesi {
  certified_by?: TasdikMakami | "";
  certified_on?: string | null;
  certification_no?: string;
  page_count?: number | null;
  last_no_before_program?: number | null;
  opened_on?: string | null;
}

/** Evrak kaydı (kişisiz alanlar; karşı taraf ve konu şifreli). */
export interface EvrakKaydi {
  id: number;
  book: number;
  direction: EvrakYonu;
  year: number;
  record_no: number;
  date: string | null;
  counterparty: string | null;
  subject: string | null;
  external_ref: string;
  /** Programın ürettiği yazının kaydı (E12, müdür yazısı); elle kayıtta null. */
  generated_document: number | null;
  term: number;
  ekler: Ek[];
}

export interface EvrakKaydiGovdesi extends GerekceEki {
  direction: EvrakYonu;
  tarih: string;
  counterparty?: string;
  subject?: string;
  external_ref?: string;
  record_no?: number | null;
  defter?: number | null;
}

export interface EvrakKaydiSonucu {
  kayit: EvrakKaydi;
  uyarilar: { kural: string; atif: string; mesaj: string; durum: string }[];
}

/** Programın ürettiği giden yazının (E12) kaydı önerisi (`genel_kurul_evraki.giden_kayit_onerisi`). */
export interface GidenKayitOnerisi {
  evrak: number;
  kod: string;
  kayitli: { id: number; yil: number; kayit_no: number } | null;
  direction: "GIDEN";
  tarih: string;
  counterparty: string;
  subject: string;
  /** Kullanımdaki defter (yoksa null: öneri numarasızdır). */
  defter: number | null;
  onerilen_no: number | null;
  /** Kayıt yazının geçerli sürümü mü? (Yerini almış sürüm kaydedilmez.) */
  gecerli: boolean;
}

export interface GidenKayitGovdesi extends GerekceEki {
  tarih: string;
  counterparty?: string;
  subject?: string;
  external_ref?: string;
  record_no?: number | null;
}

export const gelenGidenApi = {
  defterler: (): Promise<DefterListesi> => api.get<DefterListesi>("/oab/document-books/"),
  defterKaydet: (govde: DefterGovdesi): Promise<EvrakDefteri> =>
    api.post<EvrakDefteri>("/oab/document-books/", govde),
  kayitlar: (suzgec: {
    book?: number | null;
    year?: number | null;
    direction?: EvrakYonu | "";
  }): Promise<EvrakKaydi[]> => {
    const p = new URLSearchParams();
    if (suzgec.book) p.set("book", String(suzgec.book));
    if (suzgec.year) p.set("year", String(suzgec.year));
    if (suzgec.direction) p.set("direction", suzgec.direction);
    const sorgu = p.toString();
    return api.get<EvrakKaydi[]>(`/oab/document-records/${sorgu ? `?${sorgu}` : ""}`);
  },
  kaydet: (govde: EvrakKaydiGovdesi): Promise<EvrakKaydiSonucu> =>
    api.post<EvrakKaydiSonucu>("/oab/document-records/", govde),
  ekEkle: (kayit: number, dosya: File): Promise<Ek> => {
    const form = new FormData();
    form.append("file", dosya);
    return api.postForm<Ek>(`/oab/document-records/${kayit}/attachments/`, form);
  },
  gidenOnerisi: (evrak: number): Promise<GidenKayitOnerisi> =>
    api.get<GidenKayitOnerisi>(`/oab/documents/${evrak}/outgoing-record/`),
  gidenKaydet: (evrak: number, govde: GidenKayitGovdesi): Promise<EvrakKaydiSonucu> =>
    api.post<EvrakKaydiSonucu>(`/oab/documents/${evrak}/outgoing-record/`, govde),
};
