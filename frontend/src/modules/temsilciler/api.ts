// Temsilciler ekranının API istemcisi — backend `apps/oab/views.RepresentativeListCreateView` ile BİREBİR
// (tasarım §6.4.4 "Temsil türleri"; plan F1c 6. adım; ekranı 11. adımda). Çizelge E03'ün tek kaynağıdır:
// satırlar okul kartındaki kademe ve kantin koşulundan, kampüs satırı okul kartından gelir; pay dağıtım
// komisyonu ve "diğer" yalnız kayıt varsa görünür. Satırın durumu ve atıflı iletisi kural paketinindir
// (kaydedilmez, gerekçe istemez); RPD satırının notu kuralın yorumudur. Temsilcinin iptali genel üyelik
// iptal ucundandır (`organlar/api`).

import { api } from "../../lib/api";
import type { KoltukTuru, TemsilTuru } from "../gecis-kurulumu/api";
import type { Uyelik } from "../organlar/api";

/** Çizelgenin satırı (`_cizelge_satiri`). */
export interface CizelgeSatiri {
  representation: TemsilTuru;
  ad: string;
  kural: string | null;
  /** Kural paketinin sonucu: `uygun`, `uyari`, `eksik`; kuralsız satırda null. */
  durum: string | null;
  /** Uyarı ya da eksiklik varsa atıflı ileti; yoksa boş. */
  metin: string;
  notlar: string[];
  uyeler: Uyelik[];
}

/** Temsilci kaydı (`TemsilciCreateSerializer`). */
export interface TemsilciGovdesi {
  term: number;
  person: number;
  representation: TemsilTuru;
  seat_type: KoltukTuru;
  start_date: string | null;
  representative_decision: number | null;
  gerekce?: string;
}

export const temsilcilerApi = {
  cizelge: (donem: number): Promise<CizelgeSatiri[]> =>
    api.get<CizelgeSatiri[]>(`/oab/representatives/?term=${donem}`),

  ekle: (govde: TemsilciGovdesi): Promise<Uyelik> =>
    api.post<Uyelik>("/oab/representatives/", govde),
};
