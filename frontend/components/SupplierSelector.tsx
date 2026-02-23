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
      <div className="flex items-baseline justify-between mb-2">
        <label
          htmlFor="supplier-select"
          className="text-sm font-medium text-zinc-300"
        >
          Select supplier
        </label>
        {preferredSuppliers.length > 0 && (
          <span className="text-xs text-indigo-400">
            {preferredSuppliers.length} from your preferred regions
          </span>
        )}
      </div>
      <div className="relative">
        <select
          id="supplier-select"
          value={selectedId ?? ""}
          onChange={(e) => onSelect(Number(e.target.value))}
          disabled={disabled}
          className="w-full px-4 py-3.5 pr-10 rounded-xl bg-zinc-900 border border-zinc-700
                     text-zinc-100 text-sm appearance-none cursor-pointer
                     focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500
                     hover:border-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all"
        >
          <option value="">— Choose a supplier to analyse —</option>
          {preferredSuppliers.length > 0 ? (
            <>
              <optgroup label="★ Preferred regions">
                {preferredSuppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.supplier_name} · {s.country}
                    {s.industry ? ` · ${s.industry}` : ""}
                    {s.supply_tier ? ` [${s.supply_tier}]` : ""}
                  </option>
                ))}
              </optgroup>
              {otherSuppliers.length > 0 && (
                <optgroup label="Other suppliers">
                  {otherSuppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.supplier_name} · {s.country}
                      {s.industry ? ` · ${s.industry}` : ""}
                      {s.supply_tier ? ` [${s.supply_tier}]` : ""}
                    </option>
                  ))}
                </optgroup>
              )}
            </>
          ) : (
            suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.supplier_name} · {s.country}
                {s.industry ? ` · ${s.industry}` : ""}
                {s.supply_tier ? ` [${s.supply_tier}]` : ""}
              </option>
            ))
          )}
        </select>
        {/* chevron icon */}
        <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
          <svg
            className="w-4 h-4 text-zinc-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>
      {selectedId &&
        (() => {
          const s = suppliers.find((x) => x.id === selectedId);
          const tierColor =
            s?.supply_tier === "Raw Materials"
              ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
              : s?.supply_tier === "Manufacturing"
                ? "text-violet-400 bg-violet-500/10 border-violet-500/30"
                : "text-sky-400 bg-sky-500/10 border-sky-500/30";
          return s ? (
            <div className="mt-2 flex items-center flex-wrap gap-2 text-xs text-zinc-500">
              <span className="text-zinc-400 font-medium">
                {s.supplier_name}
              </span>
              <span>·</span>
              <span>{s.country}</span>
              {s.industry && (
                <>
                  <span>·</span>
                  <span>{s.industry}</span>
                </>
              )}
              {s.supply_tier && (
                <span
                  className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${tierColor}`}
                >
                  {s.supply_tier}
                </span>
              )}
              <span>·</span>
              <span className="text-emerald-400">
                {s.reliability_score.toFixed(0)}% reliability
              </span>
            </div>
          ) : null;
        })()}
    </div>
  );
}
