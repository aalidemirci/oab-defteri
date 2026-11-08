// Kişiler sayfası (aile iskeleti kalıbı) — öğretmen ve diğer personel sicilinin ekranı.
// Sicil sekmesinde arama + sayfalama, Dialog içinde elle ekleme-düzenleme, "Ayrıldı olarak
// işaretle" (ayrılış yolu; kayıt silinmez) ve silme; altta e-Okul listesinden aktarım paneli
// (önizle → mutabakat → aktar, AktarimPaneli). İkinci sekme "Ayrılış Havuzu" (genel tasarım
// §5.1, §8.4): aktarım kimseyi ayırmaz, listede bulunmayan kişi orada karar bekler
// (AyrilisHavuzu). Üçüncü sekme "Veli Listesi" (T5; genel tasarım §5.1 `ParentRoster`, §8.4):
// okulun şablonundan aktarılan liste, ekranda yalnız sınıf başına sayı (VeliListesi). KVKK: TCKN,
// cinsiyet, fotoğraf, unvan ve branş bu ekranda HİÇ YOKTUR — sicil ad-soyad ve görev türüyle,
// veli listesi veli adı ve öğrencinin sınıfıyla yürür (işleme envanteri genel tasarım §3.4).
// Öğrenciler sekmesi F1b 5. adımda öğrenci sicili ve aktarımıyla söküldü (tasarım §5.1 ALMA).
// Sekme URL'de tutulur (`?tab=personel`, `?tab=havuz`, `?tab=veli`): başka ekranlar doğrudan o
// sekmeye bağlanır.
// Aile iskeletinin kütüphane üyelik sekmeleri ve "Bakanlık sistemi" hatırlatması
// F1a-2'de söküldü.
//
// Rol süzmesi (plan F1b-2 "Bugünkü uçların eşlemi" → Kişiler; kaynak `oturum/yetki`): personeli
// her rol okur. Ayrılış Havuzu sekmesi yalnız `ayrilis_havuzu`'nda, Veli Listesi sekmesi yalnız
// `veli_listesi`'nde (kişisel veri satırı; program yöneticisi) görünür; adresle gelinirse rolün
// ilk sekmesi açılır. Personel sekmesinde "Kişi ekle" ve satırdan
// düzenleme (ayrılış, silme dahil) `kisi_yazma`'ya, e-Okul aktarım paneli (şablon dahil)
// `eokul_aktarimi`'na, "Birleştir" düğmeleri (aktarım raporu ve havuz) `kisi_yazma`'ya bağlıdır.
// Yazamayan rolde liste salt okurdur (başta `SaltOkurNotu`, satır tıklanmaz). Özet yüklenirken
// sekmeler yerine iskelet durur.

import { useCallback, useEffect, useState } from "react";

import { useDebounced } from "../../hooks/useDebounced";
import { useFormErrors } from "../../hooks/useFormErrors";
import { useTabParam } from "../../hooks/useTabParam";
import { formatNumber } from "../../lib/format";
import { emptyPage, geriDusulecekOffset } from "../../lib/pagination";
import type { Paginated } from "../../lib/pagination";
import Button from "../../ui/Button";
import Card from "../../ui/Card";
import { useConfirm } from "../../ui/ConfirmProvider";
import DataTable from "../../ui/DataTable";
import type { Column } from "../../ui/DataTable";
import Dialog from "../../ui/Dialog";
import EmptyState from "../../ui/EmptyState";
import PaginationBar from "../../ui/PaginationBar";
import Select from "../../ui/Select";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import Tabs, { tabPanelProps } from "../../ui/Tabs";
import type { TabItem } from "../../ui/Tabs";
import TextField from "../../ui/TextField";
import { MEMBER_KIND_TR, okulApi } from "../okul/api";
import { SaltOkurNotu } from "../oturum/RolKapisi";
import type { YetenekAdi } from "../oturum/api";
import { useYetki } from "../oturum/yetki";
import type { MemberKind, Personnel, PersonnelWriteBody } from "../okul/api";
import AktarimPaneli from "./AktarimPaneli";
import AyrilisHavuzu from "./AyrilisHavuzu";
import {
  GOREV_TURU_ETIKETI,
  GOREV_TURU_YARDIMI,
  KISI_SILME_ONAY_BASLIGI,
  KISI_SILME_ONAY_METNI,
  VELI_LISTESI_SEKMESI,
} from "./metinler";
import {
  DurumRozeti,
  ErrorBand,
  KisiAdi,
  hataOku,
  kisiKaydiniMetni,
  kisiOznesi,
  okunamadiMi,
} from "./ortak";
import type { SayfaHatasi } from "./ortak";
import VeliListesi from "./VeliListesi";

/** Sayfa başına kayıt (liste uçları limit/offset ile sayfalanır, varsayılan 25). */
const PAGE_SIZE = 25;

// TAB_KEYS[0] varsayılan sekmedir (useTabParam fallback) — başa yeni anahtar EKLEME.
const TAB_KEYS = ["personel", "havuz", "veli"] as const;
type TabKey = (typeof TAB_KEYS)[number];

// Sözlük: "personel" tek başına öğretmen anlamında kullanılmaz; görev türleri
// "öğretmen", "yönetici" ve "diğer personel"dir. Sekme hepsini taşır.
const TABS: TabItem[] = [
  { key: "personel", label: "Öğretmenler ve Diğer Personel", icon: "badge" },
  { key: "havuz", label: "Ayrılış Havuzu", icon: "pending_actions" },
  { key: "veli", label: VELI_LISTESI_SEKMESI, icon: "family_restroom" },
];

/** Sekmenin yeteneği (verilmeyen sekme her role açık; dosya başı "Rol süzmesi"). */
const SEKME_YETENEGI: Partial<Record<TabKey, YetenekAdi>> = {
  havuz: "ayrilis_havuzu",
  veli: "veli_listesi",
};

/** Sayfanın açıklaması: yazabilen rolde ve salt okur rolde (sözlük §4.1). */
export const KISILER_ACIKLAMASI =
  "Öğretmen ve diğer personel sicili ve veli listesi. Personel e-Okul listesinden toplu " +
  "aktarılabilir ya da tek tek girilebilir. Aktarım kimseyi ayırmaz: listede bulunmayanlar " +
  "Ayrılış Havuzu'nda karar bekler. Veliden yalnız adı-soyadı ve öğrencinin sınıfı alınır; " +
  "TCKN, unvan ve branş bu programda tutulmaz.";
export const KISILER_SALT_OKUR_ACIKLAMASI =
  "Öğretmen ve diğer personel sicili. TCKN, unvan ve branş bu programda tutulmaz.";

/** Ayrılış onayının ortak sonucu cümlesi (ayrılış yolu kaydı silmez). */
const AYRILIS_SONUCU = "Kaydı silinmez; sicilde “Ayrıldı · gg.aa.yyyy” rozetiyle kalır.";

/**
 * Düzenleme penceresinde çözülemeyen şifreli alanın yardım metni (tasarım §13 D48). Ad ve
 * soyad zorunludur: okunamayan değer ancak yeniden yazılarak kaydedilir.
 */
const OKUNAMAYAN_AD_YARDIMI = "Kayıtlı değer okunamadı; kaydetmek için yeniden yazın.";

export default function KisilerPage() {
  const yetki = useYetki();
  // Rolün sekmeleri; ilki (personel) varsayılandır. Yetkisiz sekmenin adresi varsayılana düşer
  // (`useTabParam`).
  const sekmeler = TAB_KEYS.filter((k) => {
    const yetenek = SEKME_YETENEGI[k];
    return yetenek === undefined || yetki.acik(yetenek);
  });
  const [active, setActive] = useTabParam<TabKey>("tab", sekmeler, sekmeler[0]);
  const birlestirebilir = yetki.acik("kisi_yazma");

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="od-page-header">
        <div>
          <h1 className="od-page-title">Kişiler</h1>
          <p className="od-page-description">
            {yetki.acik("kisi_yazma") ? KISILER_ACIKLAMASI : KISILER_SALT_OKUR_ACIKLAMASI}
          </p>
        </div>
      </div>

      {yetki.durum === "yukleniyor" ? (
        <SkeletonList rows={5} />
      ) : (
        <>
          <Tabs
            items={TABS.filter((t) => (sekmeler as readonly string[]).includes(t.key))}
            active={active}
            onChange={(key) => setActive(key as TabKey)}
            ariaLabel="Kişiler bölümleri"
            idBase="kisiler"
          />

          <div {...tabPanelProps("kisiler", active)}>
            {active === "personel" && (
              <PersonelSekmesi
                yazabilir={yetki.acik("kisi_yazma")}
                aktarabilir={yetki.acik("eokul_aktarimi")}
              />
            )}
            {active === "havuz" && <AyrilisHavuzu birlestirebilir={birlestirebilir} />}
            {active === "veli" && <VeliListesi />}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Öğretmenler ve diğer personel sekmesi
// ---------------------------------------------------------------------------

function PersonelSekmesi({
  yazabilir,
  aktarabilir,
}: {
  /** "Kişi ekle" ve satırdan düzenleme (`kisi_yazma`). */
  yazabilir: boolean;
  /** e-Okul aktarım paneli (`eokul_aktarimi`). */
  aktarabilir: boolean;
}) {
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput);
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<Paginated<Personnel>>(emptyPage<Personnel>());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<SayfaHatasi | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [editing, setEditing] = useState<Personnel | null>(null);
  const [creating, setCreating] = useState(false);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    let geriDusuluyor = false;
    setLoading(true);
    okulApi
      .listPersonnel({ search, limit: PAGE_SIZE, offset })
      .then((result) => {
        if (cancelled) return;
        const geri = geriDusulecekOffset(result, offset, PAGE_SIZE);
        if (geri !== null) {
          geriDusuluyor = true;
          setOffset(geri);
          return;
        }
        setPage(result);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(hataOku(e, "Öğretmen ve diğer personel listesi yüklenemedi."));
      })
      .finally(() => {
        if (!cancelled && !geriDusuluyor) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [search, offset, reloadKey]);

  const columns: Column<Personnel>[] = [
    { header: "Ad soyad", cell: (p) => <KisiAdi kayit={p} /> },
    { header: GOREV_TURU_ETIKETI, cell: (p) => MEMBER_KIND_TR[p.member_kind] },
    {
      header: "Durum",
      cell: (p) => (
        <DurumRozeti
          aktif={p.is_active}
          leftAt={p.left_at}
          havuzda={p.leave_candidate_since !== null}
        />
      ),
    },
  ];

  return (
    <div className="space-y-[var(--od-page-gap)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-title-medium text-on-surface">Öğretmen ve Diğer Personel Sicili</p>
          {!loading && (
            <p className="text-body-small text-on-surface-variant">
              {formatNumber(page.count)} kayıt
            </p>
          )}
        </div>
        {yazabilir && (
          <Button icon="person_add" onClick={() => setCreating(true)}>
            Kişi ekle
          </Button>
        )}
      </div>

      {!yazabilir && <SaltOkurNotu />}

      <Card
        elevation={0}
        className="grid items-end gap-3 bg-surface-container-lowest p-[var(--od-panel-padding)] sm:grid-cols-2"
      >
        <TextField
          className="min-w-60 flex-1"
          label="Ara"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value);
            setOffset(0);
          }}
          placeholder="Ad soyad…"
        />
      </Card>

      {error && <ErrorBand hata={error} />}

      {loading ? (
        <SkeletonList rows={5} />
      ) : page.results.length === 0 ? (
        <EmptyState
          icon="badge"
          title="Gösterilecek kişi yok"
          description={
            aktarabilir
              ? "Aramayı değiştirin ya da e-Okul personel listesini aşağıdaki panelden içe aktarın."
              : undefined
          }
        />
      ) : (
        <>
          {/* Salt okurda satır tıklanmaz: düzenleme penceresinin her eylemi bir yazmadır;
              listenin sütunları kaydın okunabilen bütün alanlarını zaten gösterir. */}
          <DataTable<Personnel>
            columns={columns}
            rows={page.results}
            onRowClick={yazabilir ? (p) => setEditing(p) : undefined}
            rowLabel={yazabilir ? (p) => `${kisiKaydiniMetni(p)} düzenle` : undefined}
          />
          <PaginationBar
            count={page.count}
            offset={offset}
            pageSize={PAGE_SIZE}
            onOffset={setOffset}
          />
        </>
      )}

      {aktarabilir && (
        <AktarimPaneli kind="personnel" onImported={reload} birlestirebilir={yazabilir} />
      )}

      {yazabilir && (creating || editing !== null) && (
        <PersonelFormDialog
          personnel={editing}
          onClose={() => {
            setCreating(false);
            setEditing(null);
          }}
          onSaved={() => {
            setCreating(false);
            setEditing(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

const MEMBER_KIND_OPTIONS = (Object.entries(MEMBER_KIND_TR) as [MemberKind, string][]).map(
  ([value, label]) => ({ value, label }),
);

function PersonelFormDialog({
  personnel,
  onClose,
  onSaved,
}: {
  personnel: Personnel | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [firstName, setFirstName] = useState(personnel?.first_name ?? "");
  const [lastName, setLastName] = useState(personnel?.last_name ?? "");
  const [memberKind, setMemberKind] = useState<MemberKind>(personnel?.member_kind ?? "OGRETMEN");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<SayfaHatasi | null>(null);
  const { errors, setFieldError, clearErrors, applyApiError } = useFormErrors();
  const snackbar = useSnackbar();
  const confirm = useConfirm();
  const aktif = personnel === null || personnel.is_active;
  const adBozuk = personnel !== null && okunamadiMi(personnel, "first_name");
  const soyadBozuk = personnel !== null && okunamadiMi(personnel, "last_name");

  const submit = async () => {
    clearErrors();
    setError(null);
    if (!firstName.trim() || !lastName.trim()) {
      if (!firstName.trim()) setFieldError("first_name", "Ad zorunludur.");
      if (!lastName.trim()) setFieldError("last_name", "Soyad zorunludur.");
      return;
    }
    const body: PersonnelWriteBody = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      member_kind: memberKind,
    };
    setBusy(true);
    try {
      if (personnel) await okulApi.updatePersonnel(personnel.id, body);
      else await okulApi.createPersonnel(body);
      snackbar.success(personnel ? "Kayıt güncellendi." : "Kayıt eklendi.");
      onSaved();
    } catch (e) {
      applyApiError(e);
      setError(hataOku(e, "Kayıt kaydedilemedi."));
      setBusy(false);
    }
  };

  const leave = async () => {
    if (!personnel) return;
    const ok = await confirm({
      title: "Kişi ayrıldı olarak işaretlensin mi?",
      message: `${kisiOznesi(personnel)} okuldan ayrılmış sayılır ve seçicilerden düşer. ${AYRILIS_SONUCU}`,
      confirmLabel: "Ayrıldı olarak işaretle",
    });
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      await okulApi.leavePersonnel(personnel.id);
      snackbar.success("Kişi ayrıldı olarak işaretlendi.");
      onSaved();
    } catch (e) {
      setError(hataOku(e, "Kişi ayrıldı olarak işaretlenemedi."));
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!personnel) return;
    const ok = await confirm({
      title: KISI_SILME_ONAY_BASLIGI,
      message: `${kisiOznesi(personnel, true)} ${KISI_SILME_ONAY_METNI}`,
      confirmLabel: "Sil",
    });
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      await okulApi.deletePersonnel(personnel.id);
      snackbar.success("Kayıt silindi.");
      onSaved();
    } catch (e) {
      setError(hataOku(e, "Kayıt silinemedi."));
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onClose}
      title={personnel ? "Kişiyi düzenle" : "Yeni kişi"}
      actions={
        <>
          {personnel && (
            <Button variant="text" icon="delete" onClick={remove} disabled={busy}>
              Sil
            </Button>
          )}
          {personnel && aktif && (
            <Button variant="text" icon="logout" onClick={leave} disabled={busy}>
              Ayrıldı olarak işaretle
            </Button>
          )}
          <Button variant="text" onClick={onClose} disabled={busy}>
            Vazgeç
          </Button>
          <Button icon="check" onClick={submit} disabled={busy}>
            {busy ? "Kaydediliyor…" : "Kaydet"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <ErrorBand hata={error} />}
        {personnel && (!aktif || personnel.leave_candidate_since !== null) && (
          <p className="text-body-medium text-on-surface-variant">
            Durum:{" "}
            <DurumRozeti
              aktif={aktif}
              leftAt={personnel.left_at}
              havuzda={personnel.leave_candidate_since !== null}
            />
          </p>
        )}
        <TextField
          label="Ad"
          required
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          error={errors.first_name}
          helperText={adBozuk ? OKUNAMAYAN_AD_YARDIMI : undefined}
        />
        <TextField
          label="Soyad"
          required
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          error={errors.last_name}
          helperText={soyadBozuk ? OKUNAMAYAN_AD_YARDIMI : undefined}
        />
        <Select
          label={GOREV_TURU_ETIKETI}
          value={memberKind}
          onChange={(e) => setMemberKind(e.target.value as MemberKind)}
          options={MEMBER_KIND_OPTIONS}
          error={errors.member_kind}
          helperText={GOREV_TURU_YARDIMI}
        />
      </div>
    </Dialog>
  );
}
