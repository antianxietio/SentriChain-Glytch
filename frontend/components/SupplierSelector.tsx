import { Supplier } from "@/lib/api";

type SupplierSelectorProps = {
  suppliers: Supplier[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  disabled?: boolean;
};

export default function SupplierSelector({
  suppliers,
  selectedId,
  onSelect,
  disabled = false,
}: SupplierSelectorProps) {
  return (
    <div className="w-full">
      <label
        htmlFor="supplier-select"
        className="block text-sm font-medium text-slate-300 mb-2"
      >
        Select Supplier
      </label>
      <select
        id="supplier-select"
        value={selectedId || ""}
        onChange={(e) => onSelect(Number(e.target.value))}
        disabled={disabled}
        className="w-full px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-700 text-slate-50 
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   disabled:opacity-50 disabled:cursor-not-allowed transition-all backdrop-blur-md"
      >
        <option value="">-- Choose a supplier --</option>
        {suppliers.map((supplier) => (
          <option key={supplier.id} value={supplier.id}>
            {supplier.name} ({supplier.country})
          </option>
        ))}
      </select>
    </div>
  );
}
