import { Supplier, OnboardProfile } from "@/lib/api";

type SupplierSelectorProps = {
  suppliers: Supplier[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  disabled?: boolean;
  profile?: OnboardProfile | null;
};

export default function SupplierSelector({
  suppliers,
  selectedId,
  onSelect,
  disabled = false,
  profile,
}: SupplierSelectorProps) {
  const preferred = profile?.preferred_countries ?? [];
  const preferredSuppliers = preferred.length
    ? suppliers.filter((s) => preferred.includes(s.country))
    : [];
  const otherSuppliers = preferred.length
    ? suppliers.filter((s) => !preferred.includes(s.country))
    : suppliers;

  return (
    <div className="w-full">
      <label
        htmlFor="supplier-select"
        className="block text-sm text-zinc-400 mb-1.5"
      >
        Supplier
        {preferredSuppliers.length > 0 && (
          <span className="ml-2 text-[11px] text-indigo-400">
            — {preferredSuppliers.length} from your preferred countries shown
            first
          </span>
        )}
      </label>
      <select
        id="supplier-select"
        value={selectedId || ""}
        onChange={(e) => onSelect(Number(e.target.value))}
        disabled={disabled}
        className="w-full px-3 py-2.5 rounded-lg bg-zinc-950 border border-zinc-700 text-zinc-100 text-sm
                   focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500
                   disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <option value="">Select a supplier to analyze...</option>
        {preferredSuppliers.length > 0 ? (
          <>
            <optgroup label="★ Your preferred countries">
              {preferredSuppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.supplier_name} — {s.country}
                </option>
              ))}
            </optgroup>
            {otherSuppliers.length > 0 && (
              <optgroup label="Other suppliers">
                {otherSuppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.supplier_name} — {s.country}
                  </option>
                ))}
              </optgroup>
            )}
          </>
        ) : (
          suppliers.map((s) => (
            <option key={s.id} value={s.id}>
              {s.supplier_name} — {s.country}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
