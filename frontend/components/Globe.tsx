"use client";

import { SupplierOverview, SupplierCard } from "@/lib/api";

interface Props {
  overview: SupplierOverview;
}

const RISK_CONFIG = {
  high: {
    label: "High",
    barCls: "bg-red-500",
    textCls: "text-red-400",
    borderCls: "border-red-500/30",
    bgCls: "bg-red-500/8",
  },
  medium: {
    label: "Medium",
    barCls: "bg-amber-500",
    textCls: "text-amber-400",
    borderCls: "border-amber-500/30",
    bgCls: "bg-amber-500/8",
  },
  low: {
    label: "Low",
    barCls: "bg-emerald-500",
    textCls: "text-emerald-400",
    borderCls: "border-emerald-500/30",
    bgCls: "bg-emerald-500/8",
  },
};

function riskBand(score: number | null): "high" | "medium" | "low" {
  if (score === null) return "low";
  if (score >= 6.5) return "high";
  if (score >= 4.0) return "medium";
  return "low";
}

export default function Globe({ overview }: Props) {
  const grouped = overview.grouped_by_country as Record<string, SupplierCard[]>;

  // Build per-country summary rows
  const rows = Object.entries(grouped)
    .map(([country, sups]) => {
      const riskScore = sups[0]?.country_risk_score ?? null;
      const avgComposite =
        sups.reduce((a, s) => a + s.composite_score, 0) / sups.length;
      const avgDelay = sups.reduce((a, s) => a + s.delay_pct, 0) / sups.length;
      const avgReliability =
        sups.reduce((a, s) => a + s.reliability_score, 0) / sups.length;
      const headline = sups[0]?.country_risk_headline ?? null;
      const band = riskBand(riskScore);
      return {
        country,
        sups,
        riskScore,
        avgComposite,
        avgDelay,
        avgReliability,
        headline,
        band,
      };
    })
    .sort((a, b) => (b.riskScore ?? 0) - (a.riskScore ?? 0));

  // Totals
  const highRisk = rows.filter((r) => r.band === "high").length;
  const medRisk = rows.filter((r) => r.band === "medium").length;
  const lowRisk = rows.filter((r) => r.band === "low").length;
  const totalSups = rows.reduce((a, r) => a + r.sups.length, 0);

  return (
    <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-zinc-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-zinc-100">
            Country Risk Heatmap
          </h2>
          <p className="text-zinc-500 text-sm mt-0.5">
            {rows.length} countries · {totalSups} suppliers — sorted by
            geopolitical risk score
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-red-400">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            High ({highRisk})
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Medium ({medRisk})
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Low ({lowRisk})
          </span>
        </div>
      </div>

      {/* Country rows */}
      <div className="divide-y divide-zinc-800/60">
        {rows.map(
          ({
            country,
            sups,
            riskScore,
            avgComposite,
            avgDelay,
            avgReliability,
            headline,
            band,
          }) => {
            const cfg = RISK_CONFIG[band];
            const barPct =
              riskScore !== null ? Math.min(100, (riskScore / 10) * 100) : 0;
            return (
              <div
                key={country}
                className={`px-6 py-4 flex flex-col sm:flex-row sm:items-center gap-4 ${cfg.bgCls}`}
              >
                {/* Country + headline */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold text-zinc-100">
                      {country}
                    </span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${cfg.textCls} ${cfg.borderCls}`}
                    >
                      {cfg.label}
                    </span>
                    <span className="text-xs text-zinc-600">
                      {sups.length} supplier{sups.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  {headline && (
                    <p className="text-xs text-zinc-500 truncate">{headline}</p>
                  )}
                </div>

                {/* Metrics */}
                <div className="flex items-center gap-6 text-xs shrink-0">
                  <div className="text-center">
                    <p className="text-zinc-500 mb-0.5">Geo Risk</p>
                    <p className={`font-mono font-semibold ${cfg.textCls}`}>
                      {riskScore !== null ? riskScore.toFixed(1) : "—"}
                      <span className="text-zinc-700">/10</span>
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-zinc-500 mb-0.5">Composite</p>
                    <p className="font-mono font-semibold text-zinc-300">
                      {avgComposite.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-zinc-500 mb-0.5">Avg Delay</p>
                    <p
                      className={`font-mono font-semibold ${avgDelay > 30 ? "text-red-400" : avgDelay > 15 ? "text-amber-400" : "text-emerald-400"}`}
                    >
                      {avgDelay.toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-zinc-500 mb-0.5">Reliability</p>
                    <p className="font-mono font-semibold text-zinc-300">
                      {avgReliability.toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Risk bar */}
                <div className="sm:w-28 shrink-0">
                  <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${cfg.barCls} rounded-full transition-all duration-700`}
                      style={{ width: `${barPct}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          },
        )}
      </div>
    </div>
  );
}
