// Birlik kişileri API istemcisi — backend `apps/oab/views.py` (`PersonListCreateView`,
// `PersonDetailView`, `PersonFromPersonnelView`, `PersonFromParentView`) ile BİREBİR (tasarım §5.2.2;
// plan F1c-4, ekranı F1c-11). KVKK: T.C. kimlik no ve telefon YOKTUR (K9; tasarım §5.2.2); veli
// listesinden yalnız yazılan adın kör indeksle bulunduğu satır kopyalanır, liste dökülmez (§8.4).
// Silme yoktur: kayıt PASİF olur. "Olası aynı kişi" (D30) 409 `olasi_ayni_kisi` döner; kullanıcı aynı
// kişi olmadığını onaylayınca istek `ayni_kisi_degil: true` ile yinelenir.

import { api } from "../../lib/api";

/** Birlik kişisinin türü (backend `PersonKind`). */
export type BirlikKisiTuru = "VELI" | "OGRETMEN" | "IDARECI" | "HAYIRSEVER" | "KURSIYER" | "DIGER";

/** Türlerin görünen adları; `IDARECI` "İdareci"dir ("Program yöneticisi" ile karışmasın; plan F1c kararları). */
export const BIRLIK_KISI_TURU_TR: Record<BirlikKisiTuru, string> = {
  VELI: "Veli",
  OGRETMEN: "Öğretmen",
  IDARECI: "İdareci",
  HAYIRSEVER: "Hayırsever",
  KURSIYER: "Kursiyer",
  DIGER: "Diğer",
};

export type BirlikKisiDurumu = "AKTIF" | "PASIF";

/** Birlik kişisi (`OabPersonSerializer`). Çözülemeyen ad `null` gelir, `bozuk_alanlar`'da durur. */
export interface BirlikKisisi {
  id: number;
  kind: BirlikKisiTuru;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  is_parent: boolean;
  adult_declared: boolean;
  is_principal: boolean;
  /** Bağlı personel kaydı (personelden eklendiyse). */
  personnel: number | null;
  /** Programdan önceki seçilme sayıları; null "beyan yok ya da bilinmiyor"dur (geçiş kurulumu). */
  external_yk_terms: number | null;
  external_dk_chair_terms: number | null;
  status: BirlikKisiDurumu;
  bozuk_alanlar?: string[];
}

export interface BirlikKisiGovdesi {
  kind: BirlikKisiTuru;
  first_name: string;
  last_name: string;
  is_parent?: boolean;
  adult_declared?: boolean;
  ayni_kisi_degil?: boolean;
}

export interface BirlikKisiDegisikligi {
  kind?: BirlikKisiTuru;
  first_name?: string;
  last_name?: string;
  is_parent?: boolean;
  adult_declared?: boolean;
  is_principal?: boolean;
  status?: BirlikKisiDurumu;
  ayni_kisi_degil?: boolean;
}

/** "Olası aynı kişi" sorusunun kodu (backend `OlasiAyniKisi`). */
export const OLASI_AYNI_KISI_KODU = "olasi_ayni_kisi";

export const birlikKisileriApi = {
  liste: (params: { search?: string; onlyActive?: boolean } = {}): Promise<BirlikKisisi[]> => {
    const q = new URLSearchParams();
    if (params.search) q.set("search", params.search);
    if (params.onlyActive) q.set("only_active", "true");
    const sorgu = q.toString();
    return api.get<BirlikKisisi[]>(`/oab/persons/${sorgu ? `?${sorgu}` : ""}`);
  },

  ekle: (govde: BirlikKisiGovdesi): Promise<BirlikKisisi> =>
    api.post<BirlikKisisi>("/oab/persons/", govde),

  guncelle: (id: number, govde: BirlikKisiDegisikligi): Promise<BirlikKisisi> =>
    api.patch<BirlikKisisi>(`/oab/persons/${id}/`, govde),

  personeldenEkle: (personnel: number, ayniKisiDegil = false): Promise<BirlikKisisi> =>
    api.post<BirlikKisisi>("/oab/persons/from-personnel/", {
      personnel,
      ayni_kisi_degil: ayniKisiDegil,
    }),

  veliListesindenEkle: (fullName: string, ayniKisiDegil = false): Promise<BirlikKisisi> =>
    api.post<BirlikKisisi>("/oab/persons/from-parent/", {
      full_name: fullName,
      ayni_kisi_degil: ayniKisiDegil,
    }),
};
