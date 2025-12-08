type Alternative = {
  id: number;
  name: string;
  country: string;
  score: number;
};

type AlternativesCardProps = {
  alternatives: Alternative[];
};

export default function AlternativesCard({
  alternatives,
}: AlternativesCardProps) {
  if (alternatives.length === 0) {
    return (
      <div className="rounded-xl p-4 shadow bg-slate-900/60 border border-slate-700 backdrop-blur-md">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">
          Alternative Suppliers
        </h3>
        <p className="text-slate-400 text-center py-8">
          No better alternatives found
        </p>
      </div>
    );
  }

  const topAlternative = alternatives[0];

  return (
    <div className="rounded-xl p-4 shadow bg-slate-900/60 border border-slate-700 backdrop-blur-md">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">
        Alternative Suppliers
      </h3>

      <div className="space-y-3">
        {alternatives.map((alt, index) => (
          <div
            key={alt.id}
            className={`p-4 rounded-lg border transition-all ${
              index === 0
                ? "bg-blue-500/10 border-blue-500/50 ring-1 ring-blue-500/30"
                : "bg-slate-800/50 border-slate-700"
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-semibold text-slate-100">
                  {alt.name}
                  {index === 0 && (
                    <span className="ml-2 text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
                      Best Choice
                    </span>
                  )}
                </h4>
                <p className="text-sm text-slate-400">{alt.country}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-green-400">
                  {alt.score.toFixed(1)}
                </div>
                <div className="text-xs text-slate-400">Score</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
