type CostCardProps = {
  currency: string;
  estimatedCost: number;
};

export default function CostCard({ currency, estimatedCost }: CostCardProps) {
  const symbols: Record<string, string> = {
    USD: "$",
    INR: "₹",
    EUR: "€",
    GBP: "£",
  };
  const symbol = symbols[currency] ?? currency;

  // Determine severity of cost impact
  const severity =
    estimatedCost > 100000 ? "high" : estimatedCost > 40000 ? "medium" : "low";

  const colors = {
    high: {
      val: "text-red-300",
      bar: "bg-gradient-to-r from-amber-500 to-red-500",
      badge: "text-red-400 bg-red-500/10 border-red-500/25",
    },
    medium: {
      val: "text-amber-300",
      bar: "bg-gradient-to-r from-emerald-500 to-amber-500",
      badge: "text-amber-400 bg-amber-500/10 border-amber-500/25",
    },
    low: {
      val: "text-emerald-300",
      bar: "bg-emerald-500",
      badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/25",
    },
  }[severity];

  // Rough bar fill: cap at $200k = 100%
  const barPct = Math.min(100, Math.round((estimatedCost / 200000) * 100));

  // Format with abbreviation for large numbers
  function fmt(n: number) {
    if (n >= 1_000_000) return `${symbol}${(n / 1_000_000).toFixed(2)}M`;
    if (n >= 1_000) return `${symbol}${(n / 1_000).toFixed(1)}K`;
    return `${symbol}${n.toLocaleString()}`;
  }

  return (
    <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-800/30">
        <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Cost Impact
        </span>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border capitalize ${colors.badge}`}
        >
          {severity} impact
        </span>
      </div>

      <div className="px-6 py-6">
        {/* Big number */}
        <div className="mb-1">
          <span
            className={`text-5xl font-bold font-mono tracking-tight count-in ${colors.val}`}
          >
            {fmt(estimatedCost)}
          </span>
        </div>
        <p className="text-sm text-zinc-500 mb-6">
          Estimated additional cost due to schedule delays
        </p>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full bar-fill ${colors.bar} rounded-full`}
              style={{ width: `${barPct}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-600">
            <span>$0</span>
            <span className="text-zinc-500">{barPct}% of threshold</span>
            <span>$200K</span>
          </div>
        </div>

        {/* Currency note */}
        <p className="text-xs text-zinc-700 mt-4">
          Calculated on {currency} cost model
        </p>
      </div>
    </div>
  );
}
