// Backend API istemcisi — aile iskeletinden uyarlandı. Program yerel sunucuyla
// konuşur (tasarım §4.1): JWT/Bearer, token yenileme,
// `personnel_inactive`/`password_change_required` oturum kapıları ve
// impersonation yoktur. Kalan: temel `fetch` sarmalayıcı, `ApiError`, backend
// `{code, message, fields}` hata sözleşmesi ve snake_case gövde. Bu üç alanın dışında alan
// taşıyan ret (409 `ek_onayi_gerekli`'nin `rapor`'u) `ApiError.govde`'den okunur. Blob
// yardımcıları (`getBlob`/`postBlob`) dosya indirmeleri (Excel şablonları, kurulum dosyası,
// evrak/PDF) için korunur; şifreli yedek indirilmez, program kaydeder (plan F1b-3). `postDosya`
// dosyayla birlikte sunucunun `Content-Disposition`'daki adını da verir (adı sunucu kuran evrak,
// ör. hesap teslim pusulası, Yedek Raporu; `lib/download.basliktanDosyaAdi`).
// Oturum (tasarım §4.4.3, TK14): kullanıcı etkileşiminden hemen sonra giden isteklere
// `X-OD-Etkinlik: 1` eklenir (oturumun boşta kilit sayacı); yoklamalar eklemez. Kilit
// kapısı: 423 `locked`/`guvenlik_dosyasi_kayip` `lib/kilit.ts`'e verilir — ön yüz
// oturumu açık sanıyorsa pencere yeniden yüklenir (tasarım §13 D53), sanmıyorsa güvenlik
// kapısı durumu yeniden okur. Aile iskeletinin 403 `kip_yetkisiz` dalı görevli kipiyle
// kalktı. Rol reddi (plan F1b-2 "Ön yüz"): `od:rol-yetkisiz` olayı YALNIZ 403 `rol_yetkisiz`'de
// yayınlanır; kilit açmanın 403 `hesap_askida`'sında ve oturum belirteci kapısının 403'ünde
// (`forbidden`, masaüstü `session_guard`) yayınlanmaz. Hatayı (sunucunun iletisi "Bu işlem
// hesabınızın rolüne açık değil.") çağıran ekran gösterir; olay yalnız oturum özetinin
// (yeteneklerin) yeniden okunmasını tetikler (`modules/oturum/yetki.YetkiSaglayici`).

// Boş/tanımsız → göreli "/api/v1": geliştirmede Vite proxy'si (vite.config.ts
// server.proxy) backend'e yönlendirir. Mutlak URL yalnız özel senaryoda gerekir.
import { basliktanDosyaAdi } from "./download";
import { kilitKapisiYaniti } from "./kilit";
import { yenidenBaslatGerekliYayinla } from "./restart";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/** Gövdesinde ileti olmayan hatalı yanıtın iletisi (ekranlar kod eşlemine düşebilsin). */
export const BEKLENMEYEN_HATA_ILETISI = "Beklenmeyen bir hata oluştu.";

/** Backend "yeniden başlat" kapısındayken (geri yükleme sonrası) dönen kod. */
const RESTART_CODE = "restart_required";

/** Rol reddinin kodu (backend `shared/exceptions.ROL_YETKISIZ_KODU`; 403). */
export const ROL_YETKISIZ_KODU = "rol_yetkisiz";
/** 403 `rol_yetkisiz` görülünce yayınlanan olay (dosya başı notu). */
export const ROL_YETKISIZ_OLAYI = "od:rol-yetkisiz";

// --- Kullanıcı etkinliği (tasarım §4.4.3) ------------------------------------
// Oturumun boşta kilit süresi SUNUCUDA dolar ve yalnız kullanıcı eylemi
// taşıyan isteklerle tazelenir. "Kullanıcı eylemi" = son birkaç saniye içinde
// gerçek bir etkileşim (fare/dokunma ya da tuş) olmuş olması. Zamanlayıcıyla
// giden istekler (oturum ve durum sorguları, periyodik yenilemeler) başlığı
// taşımaz; bunun için çağıran `etkinlik: false` verir — aksi hâlde kullanıcının
// son tıklamasından hemen sonra denk gelen bir yoklama da eylem sayılırdı.
// Yerel pencerede yapılan seçim DOM olayı üretmez: tek istisna "Farklı kaydet"tir,
// seçilen yer dönünce ekran `etkilesimKaydet`i kendisi çağırır (zamanlayıcı değil,
// kullanıcının seçimidir; `guvenlik/SifreliYedekleme`).

/** Etkileşimden sonra giden isteğin kullanıcı eylemi sayıldığı pencere. */
export const ETKINLIK_PENCERESI_MS = 5_000;
/** Backend `apps/okul/oturum.ETKINLIK_BASLIGI` ile aynı. */
export const ETKINLIK_BASLIGI = "X-OD-Etkinlik";

let sonEtkilesim = Number.NEGATIVE_INFINITY;
let sonEtkinlikGonderimi = Number.NEGATIVE_INFINITY;

/** Kullanıcı etkileşimini kaydeder: DOM dinleyicileri ve yerel pencereden dönen seçim. */
export function etkilesimKaydet(): void {
  sonEtkilesim = Date.now();
}

// Yakalama evresinde dinlenir: bir tıklamanın kendi işleyicisi isteği
// başlatmadan ÖNCE etkileşim kaydedilmiş olur.
if (typeof window !== "undefined") {
  window.addEventListener("pointerdown", etkilesimKaydet, { capture: true, passive: true });
  window.addEventListener("keydown", etkilesimKaydet, { capture: true, passive: true });
}

/** Son etkileşimin anı (`Date.now()`); hiç yoksa -Infinity. */
export function sonEtkilesimAni(): number {
  return sonEtkilesim;
}

/** `X-OD-Etkinlik` taşıyan son isteğin gönderildiği an; hiç yoksa -Infinity. */
export function sonEtkinlikGonderimiAni(): number {
  return sonEtkinlikGonderimi;
}

/** Yalnız testler için: modül düzeyindeki etkinlik saatlerini sıfırlar. */
export function etkinlikSaatleriniSifirla(): void {
  sonEtkilesim = Number.NEGATIVE_INFINITY;
  sonEtkinlikGonderimi = Number.NEGATIVE_INFINITY;
}

export interface IstekSecenekleri {
  /**
   * `false`: `X-OD-Etkinlik` hiçbir koşulda gönderilmez (oturum/durum/pano
   * sorguları, periyodik yenilemeler). Verilmezse son etkileşime bakılır.
   */
  etkinlik?: boolean;
}

function etkinlikBasligiEkle(headers: Record<string, string>, etkinlik?: boolean): void {
  if (etkinlik === false) return;
  const simdi = Date.now();
  if (simdi - sonEtkilesim > ETKINLIK_PENCERESI_MS) return;
  headers[ETKINLIK_BASLIGI] = "1";
  sonEtkinlikGonderimi = simdi;
}

/** Hata koduna göre uygulama çapı tepkiler (yeniden başlat, kilit kapısı). */
function hataOlayiYayinla(status: number, code: string): void {
  // Geri yükleme sonrası kapı: HANGİ çağrı olursa olsun tam ekran
  // "yeniden başlatın" yönlendirmesi tetiklenir (sayfa yenilense bile).
  if (code === RESTART_CODE) yenidenBaslatGerekliYayinla();
  // Kilit kapısı: oturum arayüzün haberi olmadan kilitlendi (boşta süre doldu) ya da
  // güvenlik dosyası kayboldu. Yeniden yükleme ve döngü koruması `lib/kilit.ts`'tedir.
  if (status === 423) kilitKapisiYaniti(code);
  // Rol reddi: yalnız 403 `rol_yetkisiz` (dosya başı notu). Aynı durumun öteki 403'leri
  // (`hesap_askida`, belirteç kapısı) ve başka durumdaki aynı kod olay doğurmaz.
  if (status === 403 && code === ROL_YETKISIZ_KODU) {
    window.dispatchEvent(new CustomEvent(ROL_YETKISIZ_OLAYI));
  }
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields: Record<string, unknown>;
  /** Yanıt gövdesinin bütünü: `{code, message, fields}`'in dışında alan taşıyan ret için. */
  govde: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    fields: Record<string, unknown> = {},
    govde: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.govde = govde;
  }
}

interface RequestOptions extends IstekSecenekleri {
  method?: string;
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, etkinlik } = options;
  const isForm = body instanceof FormData;
  const headers: Record<string, string> = {};
  // FormData'da Content-Type'ı tarayıcı (boundary ile) kendisi koyar.
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  etkinlikBasligiEkle(headers, etkinlik);

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
  });

  if (resp.status === 204) return undefined as T;

  let data: unknown = null;
  try {
    data = await resp.json();
  } catch {
    /* boş gövde */
  }

  if (!resp.ok) {
    const d = (data ?? {}) as { code?: string; message?: string; fields?: Record<string, unknown> };
    const code = d.code ?? String(resp.status);
    hataOlayiYayinla(resp.status, code);
    throw new ApiError(resp.status, code, d.message ?? BEKLENMEYEN_HATA_ILETISI, d.fields ?? {}, d);
  }
  return data as T;
}

/**
 * İndirilen dosya ve sunucunun verdiği adı (`Content-Disposition`; `lib/download.basliktanDosyaAdi`).
 * Başlık yoksa ya da okunamıyorsa `ad` null'dır: çağıran yedek adı kendisi kurar.
 */
export interface IndirilenDosya {
  blob: Blob;
  ad: string | null;
}

/** İkili (dosya) indirme — şablon, kurulum dosyası ve evrak/PDF için. */
async function requestBlob(path: string, options: RequestOptions = {}): Promise<Blob> {
  return (await blobYaniti(path, options)).blob();
}

/** Dosya indirme + sunucunun dosya adı (evrak/PDF; adı sunucu kurar). */
async function requestDosya(path: string, options: RequestOptions = {}): Promise<IndirilenDosya> {
  const resp = await blobYaniti(path, options);
  return {
    blob: await resp.blob(),
    ad: basliktanDosyaAdi(resp.headers?.get("Content-Disposition")),
  };
}

/** Dosya yanıtının ortak yolu: hatalı yanıt `ApiError`'a çevrilir, başarılı yanıt döner. */
async function blobYaniti(path: string, options: RequestOptions): Promise<Response> {
  const { method = "GET", body, etkinlik } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  etkinlikBasligiEkle(headers, etkinlik);
  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!resp.ok) {
    // Hatalı yanıt genelde JSON; gövdeyi okuyup ApiError'a aktar.
    let code = String(resp.status);
    let message = BEKLENMEYEN_HATA_ILETISI;
    let fields: Record<string, unknown> = {};
    try {
      const d = (await resp.json()) as {
        code?: string;
        message?: string;
        fields?: Record<string, unknown>;
      };
      code = d.code ?? code;
      message = d.message ?? message;
      fields = d.fields ?? {};
    } catch {
      /* boş gövde */
    }
    hataOlayiYayinla(resp.status, code);
    throw new ApiError(resp.status, code, message, fields);
  }
  return resp;
}

export const api = {
  get: <T>(path: string, secenekler?: IstekSecenekleri) =>
    request<T>(path, { ...secenekler, method: "GET" }),
  post: <T>(path: string, body?: unknown, secenekler?: IstekSecenekleri) =>
    request<T>(path, { ...secenekler, method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  /** Çok parçalı (dosya) gönderim — Content-Type tarayıcıya bırakılır. */
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
  putForm: <T>(path: string, form: FormData) => request<T>(path, { method: "PUT", body: form }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  /** Dosya indirme (evrak/PDF). */
  getBlob: (path: string, secenekler?: IstekSecenekleri) =>
    requestBlob(path, { ...secenekler, method: "GET" }),
  /** JSON body ile POST + dosya yanıtı. */
  postBlob: (path: string, body?: unknown, secenekler?: IstekSecenekleri) =>
    requestBlob(path, { ...secenekler, method: "POST", body }),
  /** JSON body ile POST + dosya yanıtı ve sunucunun dosya adı (`IndirilenDosya`). */
  postDosya: (path: string, body?: unknown, secenekler?: IstekSecenekleri) =>
    requestDosya(path, { ...secenekler, method: "POST", body }),
};

export { API_BASE };
