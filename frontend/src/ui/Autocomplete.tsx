// M3 stilinde generic combobox/autocomplete bileşeni (Tur 35).
//
// Davranış: kullanıcı yazdıkça `search(query)` çağrılır (300 ms debounce);
// sonuç listesi açılır, klavyeyle (↑↓ Enter Esc) gezilir, seçim yapılınca
// dropdown kapanır ve `onSelect(item)` çağrılır. Mevcut bir değer varsa
// (`selected`) etiketi gösterilen "chip" kart olarak görünür; X'e basınca
// `onClear` ile temizlenir.
//
// KVKK: arama sorguları sunucuya gider; sunucu yetki + KVKK-güvenli serileştirme
// uygular (yalnız id + ad-soyad döner). UI bu garantiyi gösterilemez ama
// sonuçları ekstra alan göstermez.
//
// LİSTE BİLEŞENİN DIŞINA ÇİZİLİR (`createPortal`, `position: fixed`): `absolute` liste en yakın
// kaydırma alanına kırpılıyordu; tek alanlı pencerede (Kişiler → "Personelden ekle") pencere
// gövdesinin kaydırma alanında kalıp yalnız bir satırı görünüyordu (Windows sınaması 12.11.2026).
// Hedef: alan bir `role="dialog"` öğesinin içindeyse o öğe, değilse gövde (`document.body`).
// Pencerede gövdeye değil pencere öğesine çizilmesinin nedeni `aria-modal`: modal pencerenin
// dışındaki içerik yardımcı teknolojide görünmez sayılır, `aria-activedescendant` seçenekleri
// duyurulmazdı; testler de seçenekleri pencerenin içinde arar. Pencere öğesinin `overflow-hidden`'ı
// `fixed` listeyi kırpmaz (kapsayan blok ekrandır). `fixed`, atasında `transform`, `filter` ya da
// `backdrop-filter` varsa o ataya göre konumlanır (Dialog.tsx başındaki not): pencere öğesi bunları
// taşımaz (açılış canlandırmasındaki `scale` yalnız açılışta, liste yazınca açılır); gövdede ata yoktur.
// Konum alanın çerçevesinin `getBoundingClientRect`'inden hesaplanır, açıkken her kaydırmada
// (yakalama evresinde: iç kaydırma alanları da) ve boyut değişiminde yenilenir; altta yer
// yetmiyorsa ve üstte daha çok yer varsa liste üste açılır. Liste kırpılmadığı için alanın kaydırma
// alanlarında görünen parçasına bağlanır; alan görünen yerin tamamen dışına çıkınca liste kapanır
// (`gorunenParca`). Katman z-[52]: gövdedeyken pencerenin
// (z-50) üstünde, bildirim kabının (z-[55]) ve "yeniden açın" ekranının (z-[60]) altında;
// penceredeyken pencerenin katmanı içinde kalır. React ağacı değişmez: pencerenin örtüsü
// (`e.target === e.currentTarget`) listeye basınca kapanmaz, dışarı tıklama denetimi listeyi
// içeri sayar.

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import type { CSSProperties, KeyboardEvent, ReactNode } from "react";
import { createPortal } from "react-dom";

import Icon from "./Icon";

/** Listenin en çok yüksekliği (eski `max-h-72` = 18rem). */
const LISTE_EN_COK = 288;
/** Alanla liste arasındaki aralık (eski `mt-1`). */
const ARALIK = 4;
/** Liste ile ekran kenarı arasında bırakılan pay. */
const KENAR_PAYI = 8;

interface ListeKonumu {
  left: number;
  width: number;
  maxHeight: number;
  top?: number;
  bottom?: number;
}

interface AlanParcasi {
  left: number;
  width: number;
  top: number;
  bottom: number;
}

// İçeriği kırpan `overflow` değerleri (jsdom tanımsız özelliği "" döndürür: kırpmaz sayılır).
const KIRPAN = /^(auto|scroll|hidden|clip|overlay)$/;

/**
 * Alanın ekranda görünen parçası: alanın çerçevesi, ekranla ve içeriği kırpan atalarla
 * (`overflow` değeri `auto`, `scroll`, `hidden` ya da `clip`: pencere gövdesi, pencere öğesi,
 * sayfadaki kaydırma alanları) kesiştirilir. Alan görünen yerin tamamen dışındaysa `null`.
 * Soldan sağa genişlik alanın tamamınınkidir (liste alan genişliğinde açılır). `fixed` atanın
 * üstündekiler onu kırpmaz, orada durulur; gövde ve kök öğe atlanır (taşmaları ekrana geçer, ekranla zaten kesişir).
 * Sayfadaki yapışkan üst çubuk (`sticky`) bir kırpma değildir, burada sayılmaz: bugün sayfa
 * içinde (pencere dışında) kullanım yok.
 */
function gorunenParca(alan: HTMLElement): AlanParcasi | null {
  const r = alan.getBoundingClientRect();
  let ust = Math.max(r.top, 0);
  let alt = Math.min(r.bottom, window.innerHeight);
  let sol = Math.max(r.left, 0);
  let sag = Math.min(r.right, window.innerWidth);
  for (
    let ata = alan.parentElement;
    ata !== null && ata !== document.body && ata !== document.documentElement;
    ata = ata.parentElement
  ) {
    const s = window.getComputedStyle(ata);
    if (KIRPAN.test(s.overflowX) || KIRPAN.test(s.overflowY)) {
      const k = ata.getBoundingClientRect();
      ust = Math.max(ust, k.top);
      alt = Math.min(alt, k.bottom);
      sol = Math.max(sol, k.left);
      sag = Math.min(sag, k.right);
    }
    if (s.position === "fixed") break;
  }
  // Kenarı kenara değen (sıfır genişlikli) kesişim de görünür sayılır: jsdom'da her çerçeve
  // sıfırdır, testler buna dayanır; gerçek ekranda bu sınır tek piksellik bir andır.
  if (alt < ust || sag < sol) return null;
  return { left: r.left, width: r.width, top: ust, bottom: alt };
}

interface AutocompleteProps<T> {
  /** Üst etiket — boş geçilirse etiket alanı render edilmez. */
  label: string;
  /** Placeholder metni (henüz seçim yokken). */
  placeholder?: string;
  /** Şu an seçili değer (chip olarak gösterilir); null/undefined ise input açık. */
  selected: T | null | undefined;
  /** Sunucu araması; en az `minChars` karakter sonrası çağrılır. */
  search: (query: string) => Promise<T[]>;
  /** Sonuç bir öğesi seçildiğinde tetiklenir. */
  onSelect: (item: T) => void;
  /** Seçimi temizlemek için (X düğmesi). */
  onClear: () => void;
  /** Liste satırının görsel etiketi. */
  getLabel: (item: T) => string;
  /** Liste satırının alt-etiketi (opsiyonel: sınıf, rol, vb.). */
  getSublabel?: (item: T) => string;
  /** Liste anahtarı (genelde `id`). */
  getKey: (item: T) => string | number;
  /**
   * Öğe seçilemezse NEDENİNİ döndürür (örn. "ayrıldı", "sınır dolu");
   * undefined = seçilebilir. Devre dışı öğe listede görünür ama tıklanamaz/
   * Enter ile seçilemez (Tur 242).
   */
  getDisabled?: (item: T) => string | undefined;
  /** Seçili chip altında gösterilecek yardımcı metin (KVKK uyarısı vb.). */
  helperText?: ReactNode;
  /** Alan-bazlı hata mesajı (kırmızı çerçeve + metin + aria-invalid). TextField/Select ile eşdeğer. */
  error?: string;
  /** Form doğrulaması için zorunluluk işareti (görsel). */
  required?: boolean;
  /** Aramada minimum karakter sayısı (varsayılan 2). */
  minChars?: number;
  /** Debounce süresi ms (varsayılan 300). */
  debounceMs?: number;
  /** Boş sonuçta gösterilecek metin. */
  emptyText?: string;
  /** Hiç sonuç yokken serbest metin kabul edilsin mi (örn. "Diğer" payaşları). */
  allowFreeText?: boolean;
  /** allowFreeText=true ise serbest yazıldıkça çağrılır. */
  onFreeText?: (text: string) => void;
  /** allowFreeText=true ise mevcut serbest metin değeri (input'a yazılır). */
  freeText?: string;
  /** Form etiketleme — useId() ile otomatik üretilir; opsiyonel override. */
  id?: string;
  /**
   * Görsel etiket (`label`) boş geçilen kullanımlarda ekran okuyucu için
   * erişilebilir ad (C16). `label` doluysa yok sayılır (htmlFor bağı yeter).
   */
  ariaLabel?: string;
  disabled?: boolean;
}

export default function Autocomplete<T>({
  label,
  placeholder = "Yazmaya başlayın…",
  selected,
  search,
  onSelect,
  onClear,
  getLabel,
  getSublabel,
  getKey,
  getDisabled,
  helperText,
  error,
  required,
  minChars = 2,
  debounceMs = 300,
  emptyText = "Sonuç bulunamadı.",
  allowFreeText = false,
  onFreeText,
  freeText = "",
  id,
  ariaLabel,
  disabled,
}: AutocompleteProps<T>) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const listId = `${inputId}-listbox`;
  const descId = error || helperText ? `${inputId}-desc` : undefined;

  const [query, setQuery] = useState(freeText);
  const [results, setResults] = useState<T[]>([]);
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // Girişin çerçevesi: liste bunun altına (ya da üstüne), bunun genişliğinde açılır.
  const fieldRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  // Listenin çizileceği öğe (pencere öğesi ya da gövde); liste açılırken belirlenir.
  const [listHost, setListHost] = useState<HTMLElement | null>(null);
  const [konum, setKonum] = useState<ListeKonumu | null>(null);
  const listeAcik = !selected && open;

  // freeText prop'u dışarıdan değişirse input'u sıfırla (form reset senaryosu).
  useEffect(() => {
    if (!selected && freeText !== query) {
      setQuery(freeText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [freeText, selected]);

  // Debounce'lu arama
  useEffect(() => {
    if (selected) return; // seçim varsa arama yok
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    if (query.trim().length < minChars) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = window.setTimeout(() => {
      setLoading(true);
      search(query.trim())
        .then((items) => {
          setResults(items);
          setHighlighted(0);
          setOpen(true);
        })
        .catch(() => setResults([]))
        .finally(() => setLoading(false));
    }, debounceMs);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [query, minChars, debounceMs, search, selected]);

  // Dışarı tıklayınca kapansın. Liste bileşenin dışına çizildiği için (dosya başındaki not)
  // ona basmak (boşluğu, kaydırma çubuğu) da içeri sayılır.
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      const hedef = e.target as Node;
      if (listRef.current?.contains(hedef)) return;
      if (containerRef.current && !containerRef.current.contains(hedef)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  // Listenin ekrandaki yeri: alanın altı, yer yetmiyorsa ve üstte daha çok yer varsa üstü.
  // Liste kırpılmadığından alanın kaydırma alanlarında GÖRÜNEN parçasına bağlanır; alan görünen
  // yerin tamamen dışına çıkınca (başlığın ya da eylem şeridinin arkasına) liste kapanır, yoksa
  // başlığın, şeridin, hatta pencerenin dışında asılı kalırdı (bağımsız denetim 12.11.2026).
  // Sonuçlar kalır: alan geri gelince ↓ ya da odak listeyi yeniden açar.
  const konumla = useCallback(() => {
    const alan = fieldRef.current;
    if (alan === null) return;
    const r = gorunenParca(alan);
    if (r === null) {
      setOpen(false);
      return;
    }
    const ekran = window.innerHeight;
    const altta = ekran - r.bottom - ARALIK - KENAR_PAYI;
    const ustte = r.top - ARALIK - KENAR_PAYI;
    const gereken = Math.min(LISTE_EN_COK, listRef.current?.scrollHeight ?? 0);
    const yeni: ListeKonumu =
      altta >= gereken || altta >= ustte
        ? {
            left: r.left,
            width: r.width,
            top: r.bottom + ARALIK,
            maxHeight: Math.max(0, Math.min(LISTE_EN_COK, altta)),
          }
        : {
            left: r.left,
            width: r.width,
            bottom: ekran - r.top + ARALIK,
            maxHeight: Math.min(LISTE_EN_COK, ustte),
          };
    setKonum((eski) =>
      eski !== null &&
      eski.left === yeni.left &&
      eski.width === yeni.width &&
      eski.top === yeni.top &&
      eski.bottom === yeni.bottom &&
      eski.maxHeight === yeni.maxHeight
        ? eski
        : yeni,
    );
  }, []);

  // Liste açılırken çizileceği öğe belirlenir; kapanınca konum unutulur.
  useLayoutEffect(() => {
    if (!listeAcik) {
      setKonum(null);
      return;
    }
    setListHost(fieldRef.current?.closest<HTMLElement>('[role="dialog"]') ?? document.body);
  }, [listeAcik]);

  // Liste çizildikten sonra, boyamadan önce konumlanır (içerik değişince yüksekliği de değişir).
  useLayoutEffect(() => {
    if (!listeAcik || listHost === null) return;
    konumla();
  }, [listeAcik, listHost, results, loading, konumla]);

  // Açıkken kaydırma (yakalama evresi: pencere gövdesi gibi iç kaydırma alanları da) ve boyut
  // değişimi konumu yeniler.
  useEffect(() => {
    if (!listeAcik) return;
    window.addEventListener("scroll", konumla, true);
    window.addEventListener("resize", konumla);
    return () => {
      window.removeEventListener("scroll", konumla, true);
      window.removeEventListener("resize", konumla);
    };
  }, [listeAcik, konumla]);

  const listeStili: CSSProperties =
    konum === null
      ? { position: "fixed", left: 0, top: 0, visibility: "hidden" }
      : {
          position: "fixed",
          left: konum.left,
          width: konum.width,
          top: konum.top,
          bottom: konum.bottom,
          maxHeight: konum.maxHeight,
        };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!open && (e.key === "ArrowDown" || e.key === "ArrowUp") && results.length) {
      setOpen(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      if (open && results[highlighted]) {
        e.preventDefault();
        pick(results[highlighted]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const pick = (item: T) => {
    if (getDisabled?.(item)) return; // seçilemez öğe — görünür ama tıklanamaz
    onSelect(item);
    setOpen(false);
    setResults([]);
    setQuery(getLabel(item));
  };

  // Eşleşen alt-metni vurgulamak için basit highlight
  const highlight = (text: string): ReactNode => {
    if (!query.trim()) return text;
    const idx = text.toLocaleLowerCase("tr").indexOf(query.trim().toLocaleLowerCase("tr"));
    if (idx < 0) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark className="bg-tertiary-container text-on-tertiary-container">
          {text.slice(idx, idx + query.trim().length)}
        </mark>
        {text.slice(idx + query.trim().length)}
      </>
    );
  };

  // --- Render ---

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label htmlFor={inputId} className="mb-1 block text-label-large text-on-surface-variant">
          {label}
          {required && <span className="text-error"> *</span>}
        </label>
      )}

      {selected ? (
        // Seçili chip görünümü
        <div className="flex items-center justify-between gap-3 rounded-shape-md bg-secondary-container px-4 py-2 text-body-medium text-on-secondary-container">
          <div className="min-w-0">
            <p className="truncate font-medium">{getLabel(selected)}</p>
            {getSublabel && getSublabel(selected) && (
              <p className="truncate text-label-small opacity-80">{getSublabel(selected)}</p>
            )}
          </div>
          {!disabled && (
            <button
              type="button"
              onClick={() => {
                onClear();
                setQuery("");
                setResults([]);
                setTimeout(() => inputRef.current?.focus(), 0);
              }}
              className="-my-2 -mr-2 flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded-full hover:bg-on-secondary-container/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label="Seçimi temizle"
            >
              <Icon name="close" size="base" />
            </button>
          )}
        </div>
      ) : (
        // Arama input'u. ARIA 1.2 combobox deseni: rol ve durum öznitelikleri
        // SARMALAYICIDA değil, odağı alan INPUT'tadır (1.1'deki sarmalayıcı deseni
        // ekran okuyucularda "açılır liste" duyurusunu düşürüyordu — odak input'ta,
        // rol div'deydi). `aria-controls` yalnız liste DOM'dayken verilir: kapalıyken
        // var olmayan bir kimliğe işaret etmesin.
        <div
          ref={fieldRef}
          className={`flex h-14 items-center rounded-shape-xs border bg-surface px-4 ${
            error
              ? "border-error focus-within:border-error focus-within:ring-2 focus-within:ring-error"
              : "border-outline focus-within:border-primary focus-within:ring-2 focus-within:ring-primary"
          }`}
        >
          <Icon name="search" size="base" className="mr-2 text-on-surface-variant" />
          <input
            ref={inputRef}
            id={inputId}
            type="text"
            role="combobox"
            aria-haspopup="listbox"
            aria-expanded={open}
            aria-controls={open ? listId : undefined}
            autoComplete="off"
            disabled={disabled}
            required={required && !allowFreeText}
            aria-invalid={error ? true : undefined}
            aria-label={!label ? ariaLabel : undefined}
            aria-describedby={descId}
            value={query}
            placeholder={placeholder}
            onChange={(e) => {
              const v = e.target.value;
              setQuery(v);
              if (allowFreeText) onFreeText?.(v);
            }}
            onFocus={() => {
              if (results.length > 0) setOpen(true);
            }}
            onKeyDown={handleKey}
            aria-autocomplete="list"
            aria-activedescendant={
              open && results[highlighted] ? `${listId}-opt-${highlighted}` : undefined
            }
            className="w-full bg-transparent text-body-large text-on-surface outline-none placeholder:text-on-surface-variant/60 disabled:opacity-50"
          />
          {loading && (
            <span className="ml-2 text-label-small text-on-surface-variant">aranıyor…</span>
          )}
          {!loading && query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setResults([]);
                setOpen(false);
                if (allowFreeText) onFreeText?.("");
              }}
              className="-mr-2 ml-1 flex min-h-12 min-w-12 items-center justify-center rounded-full text-on-surface-variant hover:bg-on-surface/10"
              aria-label="Temizle"
              tabIndex={-1}
            >
              <Icon name="close" size="base" />
            </button>
          )}
        </div>
      )}

      {/* Sonuç listesi: bileşenin dışına, pencere öğesine ya da gövdeye çizilir (dosya başındaki not). */}
      {listeAcik &&
        listHost !== null &&
        createPortal(
          <ul
            ref={listRef}
            id={listId}
            role="listbox"
            style={listeStili}
            className="z-[52] overflow-y-auto rounded-shape-sm border border-outline-variant bg-surface-container-high shadow-elevation-2"
          >
            {results.length === 0 && !loading ? (
              <li className="px-4 py-3 text-body-medium text-on-surface-variant">
                {emptyText}
                {allowFreeText && query.trim() && (
                  <span className="ml-2 text-label-small">
                    (“{query.trim()}” serbest metin olarak kalır)
                  </span>
                )}
              </li>
            ) : (
              results.map((item, i) => {
                const disabledReason = getDisabled?.(item);
                return (
                  <li
                    key={getKey(item)}
                    id={`${listId}-opt-${i}`}
                    role="option"
                    aria-selected={i === highlighted}
                    aria-disabled={disabledReason ? true : undefined}
                    onMouseEnter={() => setHighlighted(i)}
                    onMouseDown={(e) => {
                      // mousedown: input'tan focus düşmeden seçimi tamamla
                      e.preventDefault();
                      pick(item);
                    }}
                    className={`px-4 py-2 text-body-medium ${
                      disabledReason
                        ? "cursor-not-allowed opacity-50"
                        : i === highlighted
                          ? "cursor-pointer bg-secondary-container text-on-secondary-container"
                          : "cursor-pointer text-on-surface hover:bg-surface-container-low"
                    }`}
                  >
                    <p className="truncate">{highlight(getLabel(item))}</p>
                    {(disabledReason || (getSublabel && getSublabel(item))) && (
                      <p className="truncate text-label-small opacity-75">
                        {getSublabel?.(item)}
                        {disabledReason && <span className="text-error"> — {disabledReason}</span>}
                      </p>
                    )}
                  </li>
                );
              })
            )}
          </ul>,
          listHost,
        )}

      {(error || helperText) && (
        <p
          id={descId}
          className={`mt-1 text-body-small ${error ? "text-error" : "text-on-surface-variant"}`}
        >
          {error || helperText}
        </p>
      )}
    </div>
  );
}
