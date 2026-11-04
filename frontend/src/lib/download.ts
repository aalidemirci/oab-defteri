// Blob'u tarayıcıda/pywebview penceresinde dosya olarak indirtir.
// Tüm Excel, PDF, ek ve kurtarma anahtarı indirmelerinin ortak hedefidir.
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // WebView indirme isteğini olay döngüsünün sonunda devralır. URL'yi aynı çağrı
  // yığını içinde bırakmak bazı motorlarda indirmeyi başlamadan iptal edebilir.
  window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
}

/** Dosya adından atılan karakterler: yol ayraçları ve denetim karakterleri (dosya adı yol olmaz). */
// eslint-disable-next-line no-control-regex
const SUNUCU_ADI_YASAK = /[\u0000-\u001f\u007f]/g;

/** Sunucunun verdiği adın son parçası (yol ayracından sonrası), denetim karakterleri atılmış. */
function sunucuAdiniTemizle(ad: string): string | null {
  const parca = (ad.split(/[\\/]/).pop() ?? "").replace(SUNUCU_ADI_YASAK, "").trim();
  return parca === "" || parca === "." || parca === ".." ? null : parca;
}

/** RFC 5987/8187 `ext-value`'nun yüzde kodlu baytlarını verilen karakter kümesiyle çözer. */
function genisletilmisDegeriCoz(kume: string, kodlu: string): string | null {
  const baytlar: number[] = [];
  for (let i = 0; i < kodlu.length; i += 1) {
    const karakter = kodlu[i];
    if (karakter === "%") {
      const ikili = kodlu.slice(i + 1, i + 3);
      if (!/^[0-9a-fA-F]{2}$/.test(ikili)) return null;
      baytlar.push(Number.parseInt(ikili, 16));
      i += 2;
    } else {
      const kod = karakter.charCodeAt(0);
      // `attr-char` yalnız ASCII'dir; kodlanmamış ASCII dışı karakter biçimsizdir.
      if (kod > 0x7e) return null;
      baytlar.push(kod);
    }
  }
  if (kume === "utf-8") {
    try {
      return new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(baytlar));
    } catch {
      return null;
    }
  }
  // ISO-8859-1: her bayt aynı kod noktasıdır.
  return String.fromCharCode(...baytlar);
}

/**
 * Yanıtın `Content-Disposition` başlığındaki dosya adı; yoksa ya da okunamıyorsa null.
 *
 * Sunucunun adı esastır (ör. hesap teslim pusulası: `Hesap-Teslim-Pusulası_Muhasip_03.11.2026.pdf`;
 * ön yüz adı kendisi kurmaz, kurduğu ad yalnız başlık okunamazsa yedektir). Türkçe harfli adı
 * Django `filename*=utf-8''…` biçimiyle verir (RFC 5987/6266); bu biçim düz `filename="…"`'dan
 * önce gelir (RFC 6266 md. 4.3). Karakter kümesi UTF-8 ya da ISO-8859-1 olabilir (büyük-küçük harf
 * fark etmez); biçimsiz kodlama yok sayılır, sıradaki biçime düşülür. Düz biçimde tırnak içindeki
 * ters bölü kaçışı çözülür. Ad yol taşımaz: son yol ayracından sonrası alınır, denetim karakterleri
 * atılır.
 */
export function basliktanDosyaAdi(baslik: string | null | undefined): string | null {
  if (!baslik) return null;
  const yildizli = /(?:^|;)\s*filename\*\s*=\s*([^;]*)/i.exec(baslik);
  if (yildizli) {
    // Bazı sunucular değeri (kurala aykırı olarak) tırnaklar; tırnak atılır.
    const deger = yildizli[1].trim().replace(/^"(.*)"$/, "$1");
    const parcalar = /^([^']*)'[^']*'(.*)$/.exec(deger);
    const kume = parcalar?.[1].toLowerCase();
    if (parcalar && (kume === "utf-8" || kume === "iso-8859-1")) {
      const cozulen = genisletilmisDegeriCoz(kume, parcalar[2]);
      const ad = cozulen === null ? null : sunucuAdiniTemizle(cozulen);
      if (ad !== null) return ad;
    }
  }
  const duz = /(?:^|;)\s*filename\s*=\s*("(?:[^"\\]|\\.)*"|[^;]*)/i.exec(baslik);
  if (duz) {
    let deger = duz[1].trim();
    if (deger.startsWith('"')) deger = deger.slice(1, -1).replace(/\\(.)/g, "$1");
    return sunucuAdiniTemizle(deger);
  }
  return null;
}

/**
 * İndirilen dosyanın adı: belge adı + kapsam + tarih (docs/sozluk.md §3).
 * `dosyaAdi(["Genel Kurul Toplantı Tutanağı", "2026-2027", "16.11.2026"], "pdf")`
 * → `Genel-Kurul-Toplantı-Tutanağı_2026-2027_16.11.2026.pdf`. Kimlik numaralı adlar
 * (`belge_3.pdf`) masaüstünde neye ait olduklarını söylemez.
 * Türkçe harfler korunur; yalnız dosya sistemlerinin yasakladığı karakterler
 * atılır, boşluklar tireye döner, boş parça düşer.
 */
export function dosyaAdi(parts: (string | null | undefined)[], ext: string): string {
  const temiz = parts
    .map((part) =>
      (part ?? "")
        // Windows'un yasakladığı dokuz karakter; ters bölü de dahil (yol ayracıdır).
        .replace(/[\\/:*?"<>|]/g, "")
        .replace(/[.\s]+$/g, "")
        .trim()
        .replace(/\s+/g, "-")
        .replace(/-{2,}/g, "-")
        .replace(/\.-/g, "-"),
    )
    .filter(Boolean);
  const govde = temiz.join("_") || "belge";
  return `${govde}.${ext.replace(/^\./, "")}`;
}
