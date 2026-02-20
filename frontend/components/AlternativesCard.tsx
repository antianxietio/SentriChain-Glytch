type Alternative = {
  id: number;
  name: string;
  country: string;
  score: number;
  industry?: string;
  same_industry?: boolean;
};

type AlternativesCardProps = {
  alternatives: Alternative[];
  currentIndustry?: string;
};

export default function AlternativesCard({
  alternatives,
  currentIndustry,
}: AlternativesCardProps) {
  if (alternatives.length === 0) {
    return (
      <div className="rounded-xl p-5 bg-zinc-900 border border-zinc-800">
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide mb-4">
          Alternative Suppliers
        </p>
        <p className="text-zinc-500 text-sm text-center py-8">
          No better alternatives found
        </p>
      </div>
    );
  }

  const sameIndustryAlts = alternatives.filter((a) => a.same_industry);
  const crossIndustryAlts = alternatives.filter((a) => !a.same_industry);

  return (
    <div className="rounded-xl p-5 bg-zinc-900 border border-zinc-800">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
          Alternative Suppliers
        </p>
        {currentIndustry && (
          <span className="text-[10px] px-2 py-0.5 rounded border font-medium bg-emerald-500/10 border-emerald-500/30 text-emerald-400">
            {currentIndustry}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {/* Same-industry alternatives first */}
        {sameIndustryAlts.length > 0 && (
          <>
            {sameIndustryAlts.map((alt, index) => (
              <div
                key={alt.id}
                className={`p-3 rounded-lg border transition-all ${
                  index === 0 && crossIndustryAlts.length === 0
                    ? "bg-emerald-500/5 border-emerald-500/30"
                    : index === 0
                      ? "bg-emerald-500/5 border-emerald-500/30"
                      : "bg-zinc-950/50 border-zinc-800"
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="min-w-0 flex-1 mr-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-medium text-zinc-100 truncate">
                        {alt.name}
                      </span>
                      {index === 0 && (
                        <span className="shrink-0 text-[10px] bg-indigo-600 text-white px-1.5 py-0.5 rounded font-medium">
                          Best
                        </span>
                      )}
                      {alt.industry && (
                        <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded border font-medium bg-emerald-500/15 border-emerald-700/40 text-emerald-400">
                          {alt.industry}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5">{alt.country}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-base font-semibold font-mono text-emerald-400">
                      {alt.score.toFixed(1)}
                    </div>
                    <div className="text-xs text-zinc-600">reliability</div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}

        {/* Cross-industry fallbacks — visually separated */}
        {crossIndustryAlts.length > 0 && (
          <>
            {sameIndustryAlts.length > 0 && (
              <p className="text-[10px] text-zinc-600 pt-1 pl-1">Other high-reliability options</p>
            )}
            {crossIndustryAlts.map((alt) => (
              <div
                key={alt.id}
                className="p-3 rounded-lg border bg-zinc-950/50 border-zinc-800 opacity-60"
              >
                <div className="flex justify-between items-center">
                  <div className="min-w-0 flex-1 mr-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-medium text-zinc-300 truncate">
                        {alt.name}
                      </span>
                      {alt.industry && (
                        <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded border font-medium bg-zinc-800 border-zinc-700 text-zinc-500">
                          {alt.industry}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-600 mt-0.5">{alt.country} · different industry</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-base font-semibold font-mono text-zinc-400">
                      {alt.score.toFixed(1)}
                    </div>
                    <div className="text-xs text-zinc-700">reliability</div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

