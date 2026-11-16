// Etiketli onay kutusu (Genel Kurul pencereleri ve kural sürümü güncellemesinin onayı): yardım ve
// alan hatası isteğe bağlıdır; hata `role="alert"` ile okunur.

/** Onay kutusu (etiketli; isteğe bağlı yardım ve alan hatası). */
export default function OnayKutusu({
  etiket,
  secili,
  onDegis,
  yardim,
  hata,
}: {
  etiket: string;
  secili: boolean;
  onDegis: (deger: boolean) => void;
  yardim?: string;
  hata?: string;
}) {
  return (
    <div>
      <label className="flex items-start gap-2 text-body-medium text-on-surface">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 shrink-0"
          checked={secili}
          onChange={(e) => onDegis(e.target.checked)}
        />
        <span>{etiket}</span>
      </label>
      {yardim && <p className="mt-1 pl-6 text-body-small text-on-surface-variant">{yardim}</p>}
      {hata && (
        <p role="alert" className="mt-1 pl-6 text-body-small text-error">
          {hata}
        </p>
      )}
    </div>
  );
}
