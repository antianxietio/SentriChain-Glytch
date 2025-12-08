type SummaryCardProps = {
  summary: string;
  headline?: string;
  sourceUrl?: string;
};

export default function SummaryCard({
  summary,
  headline,
  sourceUrl,
}: SummaryCardProps) {
  return (
    <div className="rounded-xl p-4 shadow bg-slate-900/60 border border-slate-700 backdrop-blur-md">
      <h3 className="text-lg font-semibold text-slate-200 mb-4">
        Executive Summary
      </h3>

      <div className="prose prose-invert max-w-none">
        <p className="text-slate-300 leading-relaxed">{summary}</p>
      </div>

      {headline && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400">
            Latest event: <span className="text-slate-300">{headline}</span>
            {sourceUrl && (
              <>
                {" "}
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  (Source)
                </a>
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
