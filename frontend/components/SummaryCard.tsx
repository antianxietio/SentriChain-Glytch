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
  const getConfidenceColor = (c?: string) => {
    if (c === "high")
      return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    if (c === "medium")
      return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    return "text-red-400 bg-red-500/10 border-red-500/20";
  };

  const getScoreBar = (score: number) => {
    const pct = Math.round(score * 100);
    const color =
      pct < 33 ? "bg-emerald-500" : pct < 67 ? "bg-amber-500" : "bg-red-500";
    return { pct, color };
  };

  const getDataSourceLabel = (source?: string) => {
    if (source === "world_bank_wgi") return "World Bank WGI";
    if (source === "database") return "DB";
    return "Default";
  };

  return (
    <div className="rounded-xl p-5 bg-zinc-900 border border-zinc-800">
      <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-4">
        Executive Summary
      </p>

      {/* Confidence badge */}
      {confidence && (
        <div
          className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-xs font-medium mb-3 ${getConfidenceColor(confidence)}`}
        >
          {confidence.toUpperCase()} confidence
          {cv !== undefined && (
            <span className="opacity-60 font-mono">CV={cv.toFixed(3)}</span>
          )}
        </div>
      )}

      {/* Summary text */}
      <p className="text-zinc-400 leading-relaxed text-sm mb-4">{summary}</p>

      {/* Multi-agent scores (paper §III) */}
      {agents && agents.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-zinc-600 uppercase tracking-wide mb-3">
            Agent Risk Scores
          </p>
          <div className="space-y-3">
            {agents.map((a) => {
              const { pct, color } = getScoreBar(a.score);
              return (
                <div key={a.agent}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-zinc-300">{a.agent}</span>
                    <span className="text-xs font-mono text-zinc-400">
                      {a.score.toFixed(3)}
                    </span>
                  </div>
                  <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${color} rounded-full transition-all duration-700`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="text-xs text-zinc-600 mt-1 leading-tight">
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
        <div className="pt-3 border-t border-zinc-800">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-zinc-600 uppercase tracking-wide">
              Geopolitical Signal
            </span>
            <span className="text-xs text-zinc-600 font-mono">
              {getDataSourceLabel(geoRisk.data_source)}
              {geoRisk.gdelt_event_count > 0 &&
                ` · ${geoRisk.gdelt_event_count} events`}
            </span>
          </div>
          <p className="text-sm text-zinc-300">{geoRisk.headline}</p>
          <div className="flex items-center justify-between mt-1.5">
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
                Source
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
