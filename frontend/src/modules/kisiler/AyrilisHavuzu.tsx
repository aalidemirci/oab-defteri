// Ayrılış Havuzu (Kişiler → `?tab=havuz`) — genel tasarım §5.1 `Personnel`, §8.4.
//
// Aile iskeletinden gelen kullanıcı kararı: e-Okul aktarımı kimseyi ayırmaz ve silmez. Listede
// bulunmayan aktif öğretmen ve diğer personel burada bekler; durumları aktif kalır. Karar
// yöneticinindir, tek tek ya da toplu:
//   - "Ayrıldı olarak işaretle" (onay diyaloğu): okuldan ayrılmış sayılır, kaydı
//     SİLİNMEZ (geçmişi izlenebilsin), "Ayrıldı · gg.aa.yyyy" rozetiyle kalır.
//   - "Aktif kalsın": yalnız havuzdan çıkar; sonraki listede yine yoksa geri gelir.
// Öğrenci bölümü (sınıf süzgeci, mezunların toplu ayrılışı) F1b 5. adımda öğrenci sicili ile
// söküldü (tasarım §5.1 ALMA); veli listesi havuz kullanmaz. "Olası aynı
// kişi" (ör. soyadı değişimi) adayları EŞLEŞME GEREKÇESİYLE gösterilir (§13 D30: aday ad
// benzerliğiyle bulunur, adaş olabilir); "Birleştir" geri alınamadığı için onay
// diyaloğu iki kaydı ayırt eden bilgiyi yazar ve ikinci bir doğrulama kutusu ister.
//
// Karar tek işlemdir: seçilenlerden biri başka pencerede çözülmüşse backend hiçbir
// kararı uygulamaz (400) — liste yenilenir, kullanıcı yeniden seçer. Adlar yalnız bu
// yönetim ekranında görünür.
//
// Rol (plan F1b-2): sekme yalnız `ayrilis_havuzu` yeteneğinde görünür (Kişiler verir); karar
// düğmeleri o yeteneğin ucudur. "Birleştir" ayrıca `kisi_yazma`'ya bağlıdır (`birlestirebilir`);
// yoksa "Olası aynı kişi" sütunu adayları ve gerekçelerini düğmesiz gösterir.

import { useCallback, useEffect, useId, useState } from "react";

import { formatDate, formatNumber } from "../../lib/format";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import EmptyState from "../../ui/EmptyState";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import { MEMBER_KIND_TR, benzerlikGerekcesi, okulApi } from "../okul/api";
import type { LeavePool, LeavePoolPersonnel, LeavePoolRun, LeavePoolSimilar } from "../okul/api";
import { ErrorBand, KisiAdi, hataOku, kisiAdiMetni, kisiKaydiniMetni, kisiOznesi } from "./ortak";
import type { SayfaHatasi } from "./ortak";

const TH = "p-2 text-left text-label-medium text-on-surface-variant";
const TD = "p-2 align-top text-on-surface";

/** Aktarım sütunu: dosya adı; pano yapıştırmasında dosya adı yoktur. */
function aktarimAdi(run: LeavePoolRun | null): string {
  if (run === null) return "—";
  return run.file_name || "Yapıştırılan liste";
}

/** Seçim kümesinden yalnız hâlâ listede olanları bırakır (liste yenilenince). */
function kesisim(secili: Set<number>, kimlikler: number[]): Set<number> {
  const var_ = new Set(kimlikler);
  return new Set([...secili].filter((id) => var_.has(id)));
}

export default function AyrilisHavuzu({
  onDegisti,
  birlestirebilir,
}: {
  onDegisti?: () => void;
  /** "Birleştir" düğmeleri (personel birleştirme; `kisi_yazma`). */
  birlestirebilir: boolean;
}) {
  const [havuz, setHavuz] = useState<LeavePool | null>(null);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState<SayfaHatasi | null>(null);
  const [mesgul, setMesgul] = useState(false);
  const [personelSecimi, setPersonelSecimi] = useState<Set<number>>(new Set());
  const [yenile, setYenile] = useState(0);
  const snackbar = useSnackbar();
  const confirm = useConfirm();

  useEffect(() => {
    let iptal = false;
    setYukleniyor(true);
    okulApi
      .getLeavePool()
      .then((veri) => {
        if (iptal) return;
        setHavuz(veri);
        // Seçim listeyle birlikte tazelenir: başka pencerede karar verilmiş kişi seçimde kalmaz.
        setPersonelSecimi((s) =>
          kesisim(
            s,
            veri.personnel.map((p) => p.id),
          ),
        );
      })
      .catch((e: unknown) => {
        if (!iptal) setHata(hataOku(e, "Ayrılış havuzu yüklenemedi."));
      })
      .finally(() => {
        if (!iptal) setYukleniyor(false);
      });
    return () => {
      iptal = true;
    };
  }, [yenile]);

  const tazele = useCallback(() => setYenile((k) => k + 1), []);

  /** Kararı uygular; başarıda listeyi ve seçimi yeniler. */
  const uygula = async (eylem: "leave" | "keep", kimlikler: number[]) => {
    setMesgul(true);
    setHata(null);
    try {
      const sonuc = await okulApi.resolveLeavePool({ personnel: { [eylem]: kimlikler } });
      const sayi = eylem === "leave" ? sonuc.personnel_left : sonuc.personnel_kept;
      snackbar.success(
        eylem === "leave"
          ? `${formatNumber(sayi)} kişi ayrıldı olarak işaretlendi.`
          : `${formatNumber(sayi)} kişi aktif kalacak; havuzdan çıkarıldı.`,
      );
      setPersonelSecimi(new Set());
      onDegisti?.();
    } catch (e) {
      setHata(hataOku(e, "Karar uygulanamadı."));
    } finally {
      setMesgul(false);
      tazele();
    }
  };

  const ayril = async () => {
    const kimlikler = [...personelSecimi];
    if (kimlikler.length === 0) return;
    const ok = await confirm({
      title: `${formatNumber(kimlikler.length)} kişi ayrıldı olarak işaretlensin mi?`,
      message:
        "Seçilen kişiler okuldan ayrılmış sayılır ve seçicilerden düşer. Kayıtları silinmez; sicilde “Ayrıldı · gg.aa.yyyy” rozetiyle kalır. Sonraki bir e-Okul listesinde yeniden görünen kişinin kaydı yeniden aktif olur.",
      confirmLabel: "Ayrıldı olarak işaretle",
    });
    if (!ok) return;
    await uygula("leave", kimlikler);
  };

  const kalsin = async () => {
    const kimlikler = [...personelSecimi];
    if (kimlikler.length === 0) return;
    await uygula("keep", kimlikler);
  };

  // Birleştirme GERİ ALINAMAZ ve aday yalnız ad benzerliğiyle bulunur (§13 D30):
  // diyalog iki kaydı ayırt eden bilgiyi ve eşleşme gerekçesini yazar, onay
  // düğmesi kullanıcı "aynı kişi" kutusunu işaretlemeden açılmaz.
  const birlestir = async (kisi: LeavePoolPersonnel, aday: LeavePoolSimilar) => {
    const ok = await confirm({
      title: "Bu iki kayıt aynı kişi mi?",
      message:
        `Havuzdaki kayıt: ${kisiOznesi(kisi)} — ${MEMBER_KIND_TR[kisi.member_kind]}, havuza giriş ${formatDate(kisi.leave_candidate_since)}. ` +
        `Kalacak kayıt: “${aday.full_name}” — ${MEMBER_KIND_TR[aday.member_kind]}, sicile eklendi ${formatDate(aday.created_on)}. ` +
        `Aday yalnız ad benzerliğiyle bulundu (${benzerlikGerekcesi(aday.reason)}); okula yeni gelen bir adaş da olabilir. ` +
        `Onaylarsanız havuzdaki kaydın bağları kalacak kayda taşınır ve havuzdaki kayıt silinir. Bu işlem geri alınamaz.`,
      confirmLabel: "Birleştir",
      acknowledgeLabel: "Bu iki kaydın aynı kişi olduğunu doğruladım",
    });
    if (!ok) return;
    setMesgul(true);
    setHata(null);
    try {
      await okulApi.mergePersonnel(kisi.id, aday.id);
      snackbar.success("Kayıtlar birleştirildi.");
      onDegisti?.();
    } catch (e) {
      setHata(hataOku(e, "Kayıtlar birleştirilemedi."));
    } finally {
      setMesgul(false);
      tazele();
    }
  };

  const bos = havuz !== null && havuz.personnel_count === 0;

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div>
        <h2 className="text-title-medium text-on-surface">Ayrılış Havuzu</h2>
        <p className="mt-0.5 max-w-3xl text-body-small text-on-surface-variant">
          e-Okul aktarımı kimseyi ayırmaz ve kimsenin kaydını silmez. Listede bulunmayan öğretmen ve
          diğer personel burada bekler; durumları aktif kalır. Okuldan ayrılanlar için “Ayrıldı
          olarak işaretle”yi, okulda kalanlar için “Aktif kalsın”ı seçin. Ayrılan kişinin kaydı
          silinmez.
        </p>
      </div>

      {hata && <ErrorBand hata={hata} />}

      {yukleniyor && havuz === null ? (
        <SkeletonList rows={4} />
      ) : bos ? (
        <EmptyState
          icon="task_alt"
          title="Ayrılış kararı bekleyen kişi yok"
          description="e-Okul aktarımında listede bulunmayan kişiler burada görünür."
        />
      ) : havuz !== null ? (
        <PersonelBolumu
          kisiler={havuz.personnel}
          secim={personelSecimi}
          onSecim={setPersonelSecimi}
          mesgul={mesgul}
          onAyril={() => void ayril()}
          onKalsin={() => void kalsin()}
          onBirlestir={birlestirebilir ? (kisi, aday) => void birlestir(kisi, aday) : undefined}
        />
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ortak parçalar
// ---------------------------------------------------------------------------

function degistir(secim: Set<number>, id: number, secili: boolean): Set<number> {
  const yeni = new Set(secim);
  if (secili) yeni.add(id);
  else yeni.delete(id);
  return yeni;
}

/** Seçim sayısı + iki toplu eylem (seçim yokken kapalı). */
function KararCubugu({
  seciliSayi,
  birim,
  mesgul,
  onAyril,
  onKalsin,
}: {
  seciliSayi: number;
  birim: string;
  mesgul: boolean;
  onAyril: () => void;
  onKalsin: () => void;
}) {
  const kapali = mesgul || seciliSayi === 0;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className="text-body-small text-on-surface-variant" aria-live="polite">
        {seciliSayi === 0
          ? `Karar vermek için ${birim} seçin.`
          : `${formatNumber(seciliSayi)} ${birim} seçili.`}
      </p>
      <div className="flex flex-wrap gap-2">
        <Button variant="tonal" icon="how_to_reg" onClick={onKalsin} disabled={kapali}>
          Aktif kalsın
        </Button>
        <Button icon="logout" onClick={onAyril} disabled={kapali}>
          Ayrıldı olarak işaretle
        </Button>
      </div>
    </div>
  );
}

/** Tablo başlığındaki "görünenlerin tümünü seç" kutusu (kısmi seçimde belirsiz). */
function TumunuSec({
  kimlikler,
  secim,
  onSecim,
  etiket,
}: {
  kimlikler: number[];
  secim: Set<number>;
  onSecim: (s: Set<number>) => void;
  etiket: string;
}) {
  const secilen = kimlikler.filter((id) => secim.has(id)).length;
  const hepsi = kimlikler.length > 0 && secilen === kimlikler.length;
  return (
    <input
      type="checkbox"
      aria-label={etiket}
      checked={hepsi}
      ref={(el) => {
        if (el) el.indeterminate = secilen > 0 && !hepsi;
      }}
      onChange={(e) => {
        const yeni = new Set(secim);
        for (const id of kimlikler) {
          if (e.target.checked) yeni.add(id);
          else yeni.delete(id);
        }
        onSecim(yeni);
      }}
      className="size-5 accent-primary"
    />
  );
}

// ---------------------------------------------------------------------------
// Öğretmenler ve diğer personel
// ---------------------------------------------------------------------------

function PersonelBolumu({
  kisiler,
  secim,
  onSecim,
  mesgul,
  onAyril,
  onKalsin,
  onBirlestir,
}: {
  kisiler: LeavePoolPersonnel[];
  secim: Set<number>;
  onSecim: (s: Set<number>) => void;
  mesgul: boolean;
  onAyril: () => void;
  onKalsin: () => void;
  /** Yoksa "Birleştir" çizilmez (`birlestirebilir`). */
  onBirlestir?: (kisi: LeavePoolPersonnel, aday: LeavePoolSimilar) => void;
}) {
  const baslikId = useId();
  const ciftVar = kisiler.some((k) => k.similar.length > 0);
  return (
    <section aria-labelledby={baslikId}>
      <Card elevation={0} className="space-y-3 p-[var(--od-panel-padding)]">
        <h3 id={baslikId} className="text-title-small text-on-surface">
          Öğretmenler ve Diğer Personel ({formatNumber(kisiler.length)})
        </h3>
        {ciftVar && (
          <p className="flex items-start gap-2 rounded-shape-sm bg-tertiary-container px-3 py-2 text-body-small text-on-tertiary-container">
            <Icon name="info" />
            <span>
              “Olası aynı kişi” sütunundaki kayıt listede yeni adla görünen aynı kişi olabilir (ör.
              soyadı değişimi). Öyleyse ayrıldı diye işaretlemeyin; “Birleştir” ile eski kaydın
              bağlarını yeni kayda taşıyın. Adaylar yalnız ad benzerliğine göre listelenir — her
              satır neden aday olduğunu yazar; okula yeni gelen bir adaş da burada görünebilir.
              Birleştirmeden önce aynı kişi olduğunu doğrulayın; birleştirme geri alınamaz.
            </span>
          </p>
        )}
        <KararCubugu
          seciliSayi={secim.size}
          birim="kişi"
          mesgul={mesgul}
          onAyril={onAyril}
          onKalsin={onKalsin}
        />
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-body-small">
            <caption className="sr-only">
              Ayrılış kararı bekleyen öğretmen ve diğer personel
            </caption>
            <thead>
              <tr className="border-b border-outline-variant">
                <th className={TH}>
                  <TumunuSec
                    kimlikler={kisiler.map((k) => k.id)}
                    secim={secim}
                    onSecim={onSecim}
                    etiket="Bütün kişileri seç"
                  />
                </th>
                <th className={TH}>Ad soyad</th>
                <th className={TH}>Üye türü</th>
                <th className={TH}>Havuza giriş</th>
                <th className={TH}>Aktarım</th>
                <th className={TH}>Olası aynı kişi</th>
              </tr>
            </thead>
            <tbody>
              {kisiler.map((k) => (
                <tr key={k.id} className="border-t border-outline-variant/50">
                  <td className={TD}>
                    <input
                      type="checkbox"
                      aria-label={`${kisiAdiMetni(k)} seç`}
                      checked={secim.has(k.id)}
                      onChange={(e) => onSecim(degistir(secim, k.id, e.target.checked))}
                      className="size-5 accent-primary"
                    />
                  </td>
                  <td className={TD}>
                    <KisiAdi kayit={k} />
                  </td>
                  <td className={TD}>{MEMBER_KIND_TR[k.member_kind]}</td>
                  <td className={TD}>{formatDate(k.leave_candidate_since)}</td>
                  <td className={TD}>{aktarimAdi(k.run)}</td>
                  <td className={TD}>
                    {k.similar.length === 0 ? (
                      "—"
                    ) : (
                      <ul className="space-y-2">
                        {k.similar.map((aday) => (
                          <li key={aday.id} className="space-y-0.5">
                            <div className="flex flex-wrap items-center gap-2">
                              <span>{aday.full_name}</span>
                              {onBirlestir !== undefined && (
                                <Button
                                  variant="text"
                                  icon="merge"
                                  disabled={mesgul}
                                  onClick={() => onBirlestir(k, aday)}
                                  aria-label={`${kisiKaydiniMetni(k)} ${aday.full_name} kaydıyla birleştir`}
                                >
                                  Birleştir
                                </Button>
                              )}
                            </div>
                            {/* Neden aday? Kural adı yeterli sayar; adaş da buraya düşer (§13 D30). */}
                            <p className="text-body-small text-on-surface-variant">
                              Neden aday: {benzerlikGerekcesi(aday.reason)} ·{" "}
                              {MEMBER_KIND_TR[aday.member_kind]}, sicile eklendi{" "}
                              {formatDate(aday.created_on)}
                            </p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}
