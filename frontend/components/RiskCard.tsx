import { ScheduleMetrics, EnsembleResult } from "@/lib/api";

type RiskCardProps = {
  schedule: ScheduleMetrics;
  ensemble: EnsembleResult;
};

export default function RiskCard({ schedule, ensemble }: RiskCardProps) {
  const getRiskColor = (level: string) => {
    const l = level.toUpperCase();
    if (l === "LOW") return "text-emerald-400";
    if (l === "MEDIUM") return "text-amber-400";
    if (l === "HIGH") return "text-red-400";
    return "text-zinc-400";
  };

  const getRiskBg = (level: string) => {
    const l = level.toUpperCase();
    if (l === "LOW") return "bg-emerald-500/10 border-emerald-500/30";
    if (l === "MEDIUM") return "bg-amber-500/10 border-amber-500/30";
    if (l === "HIGH") return "bg-red-500/10 border-red-500/30";
    return "bg-zinc-800/50 border-zinc-700";
  };

  const getConfidenceColor = (c: string) => {
    if (c === "high") return "text-emerald-400";
    if (c === "medium") return "text-amber-400";
    return "text-red-400";
  };

  const spiColor =
    schedule.spi >= 0.9
      ? "text-emerald-400"
      : schedule.spi >= 0.7
        ? "text-amber-400"
        : "text-red-400";

  return (
    <div className="rounded-xl p-5 bg-zinc-900 border border-zinc-800">
      <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-4">
        Schedule Risk
      </p>

      {/* Risk level banner */}
      <div
        className={`rounded-lg p-3 mb-4 border ${getRiskBg(schedule.risk_level)}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-500 uppercase tracking-wide">
            Risk Level
          </span>
          <span
            className={`text-xl font-semibold font-mono ${getRiskColor(schedule.risk_level)}`}
          >
            {schedule.risk_level.toUpperCase()}
          </span>
        </div>
      </div>

      {/* EVM metrics grid */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-zinc-950/70 rounded-lg p-3 text-center border border-zinc-800">
          <div className={`text-xl font-semibold font-mono ${spiColor}`}>
            {schedule.spi.toFixed(3)}
          </div>
          <div className="text-xs text-zinc-500 mt-1">SPI</div>
        </div>
        <div className="bg-zinc-950/70 rounded-lg p-3 text-center border border-zinc-800">
          <div
            className={`text-xl font-semibold font-mono ${schedule.sv_days <= 0 ? "text-red-400" : "text-emerald-400"}`}
          >
            {schedule.sv_days > 0 ? "+" : ""}
            {schedule.sv_days}d
          </div>
          <div className="text-xs text-zinc-500 mt-1">SV (days)</div>
        </div>
        <div className="bg-zinc-950/70 rounded-lg p-3 text-center border border-zinc-800">
          <div className="text-xl font-semibold font-mono text-amber-400">
            {schedule.r_schedule.toFixed(3)}
          </div>
          <div className="text-xs text-zinc-500 mt-1">R_schedule</div>
        </div>
        <div className="bg-zinc-950/70 rounded-lg p-3 text-center border border-zinc-800">
          <div className="text-xl font-semibold font-mono text-indigo-400">
            {ensemble.final_score.toFixed(3)}
          </div>
          <div className="text-xs text-zinc-500 mt-1">Ensemble R_i</div>
        </div>
      </div>

      {/* Stats */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-zinc-500">Avg Delay</span>
          <span className="font-mono text-zinc-200">
            {schedule.avg_delay_days} days
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-zinc-500">Delay Rate</span>
          <span className="font-mono text-zinc-200">
            {schedule.delay_percent.toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-zinc-500">Threshold T</span>
          <span className="font-mono text-zinc-400">
            {schedule.disruption_threshold_days}d
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-zinc-500">Agent Confidence</span>
          <span
            className={`font-medium ${getConfidenceColor(ensemble.confidence)}`}
          >
            {ensemble.confidence.toUpperCase()}
          </span>
        </div>
        {ensemble.high_uncertainty && (
          <div className="mt-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
            High agent disagreement (CV=
            {ensemble.coefficient_of_variation.toFixed(3)}) — manual review
            recommended
          </div>
        )}
      </div>
    </div>
  );
}
