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
    <div className="rounded-xl p-4 shadow bg-slate-900/60 border border-slate-700 backdrop-blur-md">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">Cost Impact</h3>

      <div className="text-center py-6">
        <div className="text-4xl font-bold text-orange-400 mb-2">
          {formatCurrency(estimatedCost, currency)}
        </div>
        <p className="text-sm text-slate-400">
          Estimated Additional Cost Due to Delays
        </p>
      </div>

      <div className="mt-4 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full transition-all duration-1000 w-3/4" />
      </div>
    </div>
  );
}
