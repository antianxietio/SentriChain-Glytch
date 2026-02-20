type CostCardProps = {
  currency: string;
  estimatedCost: number;
};

export default function CostCard({ currency, estimatedCost }: CostCardProps) {
  const formatCurrency = (amount: number, curr: string) => {
    const symbols: { [key: string]: string } = {
      USD: "$",
      INR: "₹",
      EUR: "€",
      GBP: "£",
    };

    const symbol = symbols[curr] || curr;
    return `${symbol}${amount.toLocaleString()}`;
  };

  return (
    <div className="rounded-xl p-5 bg-zinc-900 border border-zinc-800">
      <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-4">
        Cost Impact
      </p>

      <div className="flex items-end gap-2 mb-1">
        <span className="text-3xl font-semibold font-mono text-zinc-100">
          {formatCurrency(estimatedCost, currency)}
        </span>
      </div>
      <p className="text-sm text-zinc-500 mb-5">
        Estimated additional cost due to schedule delays
      </p>

      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className="h-full bg-amber-500 rounded-full transition-all duration-1000 w-3/4" />
      </div>
      <p className="text-xs text-zinc-600 mt-2">
        Based on {currency} cost model
      </p>
    </div>
  );
}
