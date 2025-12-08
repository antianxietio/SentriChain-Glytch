type RiskCardProps = {
  avgDelayDays: number;
  delayPercent: number;
  riskLevel: string;
};

export default function RiskCard({
  avgDelayDays,
  delayPercent,
  riskLevel,
}: RiskCardProps) {
  const getRiskColor = (level: string) => {
    const levelUpper = level.toUpperCase();
    if (levelUpper === "LOW") return "text-green-400";
    if (levelUpper === "MEDIUM") return "text-yellow-400";
    if (levelUpper === "HIGH") return "text-red-400";
    return "text-slate-400";
  };

  const getRiskBg = (level: string) => {
    const levelUpper = level.toUpperCase();
    if (levelUpper === "LOW") return "bg-green-500/10 border-green-500/30";
    if (levelUpper === "MEDIUM") return "bg-yellow-500/10 border-yellow-500/30";
    if (levelUpper === "HIGH") return "bg-red-500/10 border-red-500/30";
    return "bg-slate-500/10 border-slate-500/30";
  };

  return (
    <div className="rounded-xl p-4 shadow bg-slate-900/60 border border-slate-700 backdrop-blur-md">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">
        Schedule Risk
      </h3>

      <div className={`rounded-lg p-4 mb-4 border ${getRiskBg(riskLevel)}`}>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Risk Level</span>
          <span className={`text-2xl font-bold ${getRiskColor(riskLevel)}`}>
            {riskLevel.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-400">Average Delay</span>
          <span className="text-lg font-semibold text-slate-100">
            {avgDelayDays} days
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-400">Delay Percentage</span>
          <span className="text-lg font-semibold text-slate-100">
            {(delayPercent * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}
