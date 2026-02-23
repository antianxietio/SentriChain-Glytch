import { ScheduleMetrics, EnsembleResult } from "@/lib/api";

type RiskCardProps = {
  schedule: ScheduleMetrics;
  ensemble: EnsembleResult;
};

export default function RiskCard({ schedule, ensemble }: RiskCardProps) {
  const level = schedule.risk_level.toUpperCase();

  const riskConfig = {
    LOW:    { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/25", dot: "bg-emerald-500", bar: "bg-emerald-500" },
    MEDIUM: { text: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/25",   dot: "bg-amber-500",   bar: "bg-amber-500" },
    HIGH:   { text: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/25",     dot: "bg-red-500",     bar: "bg-red-500" },
  }[level] ?? { text: "text-zinc-400", bg: "bg-zinc-800", border: "border-zinc-700", dot: "bg-zinc-500", bar: "bg-zinc-500" };

  const confConfig = {
    high:   { label: "High",   cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" },
    medium: { label: "Medium", cls: "text-amber-400   bg-amber-500/10   border-amber-500/30" },
    low:    { label: "Low",    cls: "text-red-400     bg-red-500/10     border-red-500/30" },
  }[ensemble.confidence] ?? { label: "—", cls: "text-zinc-400 bg-zinc-800 border-zinc-700" };

  const spiPct = Math.round(schedule.spi * 100);
  const rPct   = Math.round(schedule.r_schedule * 100);
  const ensPct = Math.round(ensemble.final_score * 100);

  const spiColor = schedule.spi >= 0.9 ? "text-emerald-400" : schedule.spi >= 0.7 ? "text-amber-400" : "text-red-400";
  const svNeg    = schedule.sv_days <= 0;

  return (
    <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
      {/* Header band */}
      <div className={`px-6 py-4 flex items-center justify-between ${riskConfig.bg} border-b ${riskConfig.border}`}>
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full ${riskConfig.dot} shadow-[0_0_8px_2px] shadow-current opacity-80`} />
          <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">Schedule Risk</span>
        </div>
        <span className={`text-2xl font-bold tracking-tight ${riskConfig.text}`}>
          {level}
        </span>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* EVM grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* SPI */}
          <div className="rounded-xl bg-zinc-950/60 border border-zinc-800 px-4 py-3">
            <div className={`text-2xl font-bold font-mono tracking-tight ${spiColor}`}>
              {schedule.spi.toFixed(3)}
            </div>
            <div className="text-[11px] text-zinc-500 mt-1 uppercase tracking-wide">SPI</div>
            <div className="mt-2 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div className={`h-full bar-fill ${spiColor.replace("text-","bg-").replace("-400","-500")} rounded-full`}
                style={{ width: `${spiPct}%` }} />
            </div>
          </div>
          {/* SV */}
          <div className="rounded-xl bg-zinc-950/60 border border-zinc-800 px-4 py-3">
            <div className={`text-2xl font-bold font-mono tracking-tight ${svNeg ? "text-red-400" : "text-emerald-400"}`}>
              {schedule.sv_days > 0 ? "+" : ""}{schedule.sv_days}d
            </div>
            <div className="text-[11px] text-zinc-500 mt-1 uppercase tracking-wide">Schedule Variance</div>
            <div className="mt-2 text-xs text-zinc-600">
              {svNeg ? "Behind schedule" : "On track"}
            </div>
          </div>
          {/* R_schedule */}
          <div className="rounded-xl bg-zinc-950/60 border border-zinc-800 px-4 py-3">
            <div className="text-2xl font-bold font-mono tracking-tight text-amber-400">
              {schedule.r_schedule.toFixed(3)}
            </div>
            <div className="text-[11px] text-zinc-500 mt-1 uppercase tracking-wide">R_schedule</div>
            <div className="mt-2 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bar-fill bg-amber-500 rounded-full" style={{ width: `${rPct}%` }} />
            </div>
          </div>
          {/* Ensemble */}
          <div className="rounded-xl bg-zinc-950/60 border border-zinc-800 px-4 py-3">
            <div className="text-2xl font-bold font-mono tracking-tight text-indigo-400">
              {ensemble.final_score.toFixed(3)}
            </div>
            <div className="text-[11px] text-zinc-500 mt-1 uppercase tracking-wide">Ensemble R_i</div>
            <div className="mt-2 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bar-fill bg-indigo-500 rounded-full" style={{ width: `${ensPct}%` }} />
            </div>
          </div>
        </div>

        {/* Stats rows */}
        <div className="space-y-3">
          {[
            { label: "Avg Delay",   value: `${schedule.avg_delay_days} days`,             em: schedule.avg_delay_days > 5 },
            { label: "Delay Rate",  value: `${schedule.delay_percent.toFixed(1)}%`,         em: schedule.delay_percent > 20 },
            { label: "Threshold T", value: `${schedule.disruption_threshold_days} days`,   em: false },
          ].map(({ label, value, em }) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-sm text-zinc-500">{label}</span>
              <span className={`text-sm font-mono font-medium ${em ? "text-amber-300" : "text-zinc-200"}`}>{value}</span>
            </div>
          ))}
          <div className="flex items-center justify-between pt-1 border-t border-zinc-800">
            <span className="text-sm text-zinc-500">Agent Confidence</span>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${confConfig.cls}`}>
              {confConfig.label}
            </span>
          </div>
        </div>

        {/* Uncertainty warning */}
        {ensemble.high_uncertainty && (
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-amber-500/8 border border-amber-500/20">
            <span className="text-amber-400 text-base mt-0.5">⚠</span>
            <p className="text-xs text-amber-300 leading-relaxed">
              High agent disagreement (CV={ensemble.coefficient_of_variation.toFixed(3)}) — manual review recommended
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
