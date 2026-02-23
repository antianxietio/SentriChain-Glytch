import { AgentResult, GeoRiskSignal } from "@/lib/api";

type SummaryCardProps = {
  summary: string;
  geoRisk?: GeoRiskSignal;
  agents?: AgentResult[];
  confidence?: string;
  cv?: number;
};

export default function SummaryCard({
  summary,
  geoRisk,
  agents,
  confidence,
  cv,
}: SummaryCardProps) {
  const confConfig = {
    high: {
      label: "High confidence",
      cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
    medium: {
      label: "Medium confidence",
      cls: "text-amber-400   bg-amber-500/10   border-amber-500/30",
    },
    low: {
      label: "Low confidence",
      cls: "text-red-400     bg-red-500/10     border-red-500/30",
    },
  }[confidence ?? ""] ?? {
    label: "—",
    cls: "text-zinc-400 bg-zinc-800 border-zinc-700",
  };

  function barColor(score: number) {
    if (score < 0.33) return "bg-emerald-500";
    if (score < 0.67) return "bg-amber-500";
    return "bg-red-500";
  }

  function agentShortName(name: string) {
    return name
      .replace("Agent", "")
      .replace(/([A-Z])/g, " $1")
      .trim();
  }

  const dataSourceLabel = (src?: string) =>
    src === "world_bank_wgi"
      ? "World Bank WGI"
      : src === "database"
        ? "DB"
        : "Default";

  return (
    <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-800/30 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Executive Summary
        </span>
        {confidence && (
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${confConfig.cls}`}
          >
            {confConfig.label}
            {cv !== undefined && (
              <span className="ml-1.5 opacity-60 font-mono text-[11px]">
                CV={cv.toFixed(3)}
              </span>
            )}
          </span>
        )}
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Summary text */}
        <p className="text-zinc-300 leading-relaxed text-[0.9375rem]">
          {summary}
        </p>

        {/* Multi-agent scores */}
        {agents && agents.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-3">
              Agent Risk Scores
            </p>
            <div className="space-y-4">
              {agents.map((a) => {
                const pct = Math.round(a.score * 100);
                const color = barColor(a.score);
                const scoreColor =
                  a.score < 0.33
                    ? "text-emerald-400"
                    : a.score < 0.67
                      ? "text-amber-400"
                      : "text-red-400";
                return (
                  <div
                    key={a.agent}
                    className="rounded-xl bg-zinc-950/50 border border-zinc-800 px-4 py-3"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-zinc-200">
                        {agentShortName(a.agent)}
                      </span>
                      <span
                        className={`text-base font-bold font-mono ${scoreColor}`}
                      >
                        {a.score.toFixed(3)}
                      </span>
                    </div>
                    <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-2">
                      <div
                        className={`h-full bar-fill ${color} rounded-full`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <p className="text-xs text-zinc-600 leading-relaxed">
                      {a.reasoning}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Geopolitical signal */}
        {geoRisk && (
          <div className="rounded-xl bg-zinc-950/50 border border-zinc-800 px-4 py-3.5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
                Geopolitical Signal
              </span>
              <span className="text-xs text-zinc-600 font-mono">
                {dataSourceLabel(geoRisk.data_source)}
                {geoRisk.gdelt_event_count > 0 &&
                  ` · ${geoRisk.gdelt_event_count} events`}
              </span>
            </div>
            <p className="text-sm text-zinc-200 leading-relaxed mb-2">
              {geoRisk.headline}
            </p>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-zinc-500">
                R_ext={geoRisk.r_external.toFixed(3)} (
                {geoRisk.risk_score_raw.toFixed(1)}/10)
              </span>
              {geoRisk.source_url && (
                <a
                  href={geoRisk.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Source ↗
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
