"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getSuppliers,
  analyzeSupplier,
  getSuppliersOverview,
  getRecommendations,
  getOnboardProfile,
  Supplier,
  AnalyzeResponse,
  SupplierOverview,
  SupplierCard,
  CountryFactors,
  RecommendationResponse,
  OnboardProfile,
} from "@/lib/api";
import { getStoredUser, getToken, clearSession, AuthUser } from "@/lib/auth";
import SupplierSelector from "@/components/SupplierSelector";
import RiskCard from "@/components/RiskCard";
import CostCard from "@/components/CostCard";
import AlternativesCard from "@/components/AlternativesCard";
import SummaryCard from "@/components/SummaryCard";

/* ── History entry stored in localStorage ─────────────────────────── */
interface HistoryEntry {
  id: string;
  supplierId: number;
  supplierName: string;
  country: string;
  ensembleScore: number;
  riskLevel: string;
  timestamp: string;
  data: AnalyzeResponse;
}

const HISTORY_KEY = "sc_history";
const HISTORY_MAX = 5;

/* ── Tabs ─────────────────────────────────────────────────────────── */
type Tab = "overview" | "recommendations" | "analysis" | "compare";

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(entries: HistoryEntry[]) {
  localStorage.setItem(
    HISTORY_KEY,
    JSON.stringify(entries.slice(0, HISTORY_MAX)),
  );
}

function riskColor(score: number) {
  if (score >= 0.7) return "text-red-400 bg-red-500/10 border-red-500/20";
  if (score >= 0.4) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
  return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
}

function riskLabel(score: number) {
  if (score >= 0.7) return "High";
  if (score >= 0.4) return "Medium";
  return "Low";
}
function riskLabelByStr(level: string) {
  if (level === "high")
    return {
      label: "High Risk",
      cls: "text-red-400 bg-red-500/10 border-red-500/20",
    };
  if (level === "medium")
    return {
      label: "Med Risk",
      cls: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    };
  return {
    label: "Low Risk",
    cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  };
}

/* ── Download helper ──────────────────────────────────────────────── */
function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════════════════════════════ */
export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<number | null>(
    null,
  );
  const [analysisData, setAnalysisData] = useState<AnalyzeResponse | null>(
    null,
  );
  const [isLoadingSuppliers, setIsLoadingSuppliers] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);

  // Overview state
  const [overview, setOverview] = useState<SupplierOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  // Recommendations state
  const [recs, setRecs] = useState<RecommendationResponse | null>(null);
  const [recsLoading, setRecsLoading] = useState(false);
  const [recsError, setRecsError] = useState<string | null>(null);

  // Onboarding profile (drives personalization throughout the dashboard)
  const [profile, setProfile] = useState<OnboardProfile | null>(null);

  /* Init session + profile */
  useEffect(() => {
    (async () => {
      const { ensureSession } = await import("@/lib/auth");
      await ensureSession();
      const stored = getStoredUser();
      if (stored) setUser(stored);
      setHistory(loadHistory());
      const tok = getToken();
      if (tok) {
        try {
          const p = await getOnboardProfile(tok);
          if (p) setProfile(p);
        } catch { /* No profile yet */ }
      }
    })();
  }, []);

  /* Load suppliers */
  useEffect(() => {
    if (!user) return;
    getSuppliers()
      .then(setSuppliers)
      .catch(() =>
        setError("Failed to load suppliers. Is the backend running?"),
      )
      .finally(() => setIsLoadingSuppliers(false));
  }, [user]);

  /* Load overview when tab selected */
  useEffect(() => {
    if ((tab !== "overview" && tab !== "compare") || overview || !user) return;
    const token = getToken();
    if (!token) return;
    setOverviewLoading(true);
    getSuppliersOverview(token)
      .then(setOverview)
      .catch((e: unknown) =>
        setOverviewError(
          e instanceof Error ? e.message : "Failed to load overview",
        ),
      )
      .finally(() => setOverviewLoading(false));
  }, [tab, user, overview]);

  /* Load recommendations when tab selected */
  useEffect(() => {
    if (tab !== "recommendations" || recs || !user) return;
    const token = getToken();
    if (!token) return;
    setRecsLoading(true);
    getRecommendations(token)
      .then(setRecs)
      .catch((e: unknown) =>
        setRecsError(
          e instanceof Error ? e.message : "Failed to load recommendations",
        ),
      )
      .finally(() => setRecsLoading(false));
  }, [tab, user, recs]);

  // Material → leading-country map (mirrors backend logic)
  const MATERIAL_COUNTRY_MAP: Record<string, string[]> = {
    // Electronics
    "Semiconductors":                   ["Taiwan", "South Korea", "China"],
    "PCBs":                             ["China", "Taiwan", "South Korea"],
    "Display Panels":                   ["South Korea", "China", "Taiwan"],
    "Batteries":                        ["China", "South Korea"],
    "Rare Earth Elements":              ["China"],
    "Sensors & Actuators":              ["Germany", "Japan", "South Korea"],
    "Capacitors & Resistors":           ["Japan", "China", "South Korea"],
    "Microcontrollers":                 ["Taiwan", "South Korea"],
    "Optical Components":               ["Japan", "Germany", "Taiwan"],
    // Manufacturing / Automotive
    "Steel":                            ["India", "China", "Germany"],
    "Aluminum":                         ["China", "India", "Germany"],
    "Aluminum Alloys":                  ["China", "Germany", "Japan"],
    "Copper":                           ["China", "India", "South Korea"],
    "Precision Parts":                  ["Germany", "India", "Taiwan"],
    "Wiring & Connectors":              ["Vietnam", "China", "India"],
    "Hydraulic Parts":                  ["Germany", "India"],
    "Motors":                           ["Germany", "India", "China"],
    "Rubber & Seals":                   ["Malaysia", "Thailand", "Vietnam"],
    "Fasteners & Bearings":             ["China", "India", "Germany"],
    "Plastics & Polymers":              ["China", "Germany", "South Korea"],
    "Glass & Glazing":                  ["China", "Germany", "India"],
    "Paints & Coatings":                ["Germany", "India", "China"],
    "Machine Tools":                    ["Germany", "Japan", "China"],
    // Pharmaceuticals
    "Active Pharmaceutical Ingredients (APIs)": ["India", "China", "Germany"],
    "Excipients & Binders":             ["India", "Germany", "China"],
    "Chemical Solvents":                ["Germany", "China", "India"],
    "Biologic Raw Materials":           ["Germany", "USA", "India"],
    "Reagents & Buffers":               ["Germany", "USA", "Japan"],
    "Sterile Packaging":                ["Germany", "India", "China"],
    "Medical Glass & Vials":            ["Germany", "India"],
    "Drug Delivery Devices":            ["Germany", "India", "USA"],
    "Laboratory Chemicals":             ["Germany", "Japan", "USA"],
    "Filtration Membranes":             ["Germany", "Japan", "India"],
    "Cold-Chain Containers":            ["Germany", "South Korea", "USA"],
    // Aerospace
    "Titanium Alloys":                  ["Japan", "Germany", "China"],
    "Carbon Fiber Composites":          ["Japan", "Germany", "South Korea"],
    "High-Temperature Alloys":          ["Germany", "Japan", "USA"],
    "Avionics Components":              ["USA", "Germany", "Japan"],
    "Thermal Insulation":               ["Germany", "Japan", "China"],
    "Fuel System Components":           ["Germany", "Japan", "USA"],
    // Energy
    "Solar Panels":                     ["China", "South Korea"],
    "Turbine Components":               ["Germany", "India", "China"],
    "Cables & Conductors":              ["China", "Germany", "India"],
    "Transformers":                     ["China", "Germany", "India"],
    "Insulation Materials":             ["China", "Germany"],
    "Pumps & Valves":                   ["Germany", "India", "China"],
    // Construction
    "Cement & Concrete Additives":      ["India", "China", "Vietnam"],
    "Lumber & Wood Products":           ["Vietnam", "Malaysia", "Indonesia"],
    // Food & Beverage
    "Packaging Materials":              ["China", "Vietnam", "India"],
    "Food-Grade Chemicals":             ["Germany", "USA", "China"],
    "Flavoring Agents":                 ["China", "India", "Germany"],
    "Preservatives & Additives":        ["China", "Germany", "India"],
    "Enzymes & Cultures":               ["Germany", "China"],
    "Sweeteners":                       ["China", "India"],
    "Fats & Oils":                      ["Malaysia", "Indonesia", "India"],
    "Starches & Proteins":              ["China", "India", "USA"],
    "Agricultural Raw Materials":       ["India", "Vietnam", "Thailand"],
    "Natural Colors & Extracts":        ["India", "China"],
    "Cleaning & Sanitation Agents":     ["Germany", "China", "India"],
    // Textiles
    "Cotton Fiber":                     ["India", "China", "Bangladesh"],
    "Synthetic Fibers (Nylon/Polyester)": ["China", "India", "Vietnam"],
    "Wool & Natural Fibers":            ["India", "China"],
    "Dyes & Pigments":                  ["India", "China", "Germany"],
    "Chemical Treatments":              ["Germany", "China", "India"],
    "Industrial Threads":               ["China", "India", "Vietnam"],
    "Elastane & Spandex":               ["China", "South Korea"],
    "Adhesives & Coatings":             ["Germany", "China", "India"],
    // Chemical
    "Industrial Chemicals":             ["Germany", "China", "India"],
    "Solvents":                         ["Germany", "China", "India"],
    "Catalysts":                        ["Germany", "Japan", "China"],
    "Reagents":                         ["Germany", "USA", "Japan"],
    "Acids & Bases":                    ["Germany", "China", "India"],
    "Specialty Gases":                  ["Germany", "Japan", "South Korea"],
    "Surfactants":                      ["Germany", "China", "India"],
    "Petrochemicals":                   ["China", "India", "South Korea"],
    // Logistics
    "Vehicle Components":               ["Germany", "Japan", "China"],
    "Fuel Additives":                   ["Germany", "China", "India"],
    "Lubricants & Oils":                ["Germany", "China", "India"],
    "Conveyor Components":              ["Germany", "China", "India"],
    "Safety Equipment":                 ["Germany", "China", "South Korea"],
    "Pallets & Load Carriers":          ["China", "Vietnam", "India"],
    "Warehouse Equipment":              ["China", "Germany", "South Korea"],
  };

  // Suppliers sorted so profile-matching ones appear first
  const sortedSuppliers = useMemo(() => {
    if (!profile) return suppliers;
    const preferred = profile.preferred_countries ?? [];
    const materials = profile.raw_materials ?? [];
    const materialCountries = new Set<string>();
    for (const mat of materials) {
      for (const [key, countries] of Object.entries(MATERIAL_COUNTRY_MAP)) {
        if (
          mat.toLowerCase().includes(key.toLowerCase()) ||
          key.toLowerCase().includes(mat.toLowerCase())
        ) {
          countries.forEach((c) => materialCountries.add(c));
        }
      }
    }
    return [...suppliers].sort((a, b) => {
      const aScore =
        (preferred.includes(a.country) ? 2 : 0) +
        (materialCountries.has(a.country) ? 1 : 0);
      const bScore =
        (preferred.includes(b.country) ? 2 : 0) +
        (materialCountries.has(b.country) ? 1 : 0);
      if (bScore !== aScore) return bScore - aScore;
      return a.supplier_name.localeCompare(b.supplier_name);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suppliers, profile]);

  const selectedSupplier = suppliers.find((s) => s.id === selectedSupplierId);

  /* Persist + run analysis */
  const handleSupplierSelect = useCallback(
    async (id: number) => {
      setSelectedSupplierId(id);
      setIsAnalyzing(true);
      setError(null);
      setAnalysisData(null);
      const token = getToken() ?? undefined;
      try {
        const data = await analyzeSupplier(id, token);
        setAnalysisData(data);

        const sup = suppliers.find((s) => s.id === id);
        if (sup) {
          const entry: HistoryEntry = {
            id: `${Date.now()}`,
            supplierId: id,
            supplierName: sup.supplier_name,
            country: sup.country,
            ensembleScore: data.ensemble.final_score,
            riskLevel: riskLabel(data.ensemble.final_score),
            timestamp: new Date().toLocaleString(),
            data,
          };
          setHistory((prev) => {
            const updated = [
              entry,
              ...prev.filter((h) => h.supplierId !== id),
            ].slice(0, HISTORY_MAX);
            saveHistory(updated);
            return updated;
          });
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Analysis failed.";
        setError(msg);
      } finally {
        setIsAnalyzing(false);
      }
    },
    [suppliers, router],
  );

  /* Restore from history */
  function restoreFromHistory(entry: HistoryEntry) {
    setSelectedSupplierId(entry.supplierId);
    setAnalysisData(entry.data);
    setHistoryOpen(false);
    setTab("analysis");
  }

  /* Export */
  function handleExport() {
    if (!analysisData || !selectedSupplier) return;
    downloadJSON(
      {
        exported_at: new Date().toISOString(),
        supplier: selectedSupplier,
        analysis: analysisData,
      },
      `sentrichain-${selectedSupplier.supplier_name.toLowerCase().replace(/\s+/g, "-")}-${Date.now()}.json`,
    );
  }

  function handleReonboard() {
    clearSession();
    document.cookie = "sc_onboarded=; path=/; max-age=0";
    router.push("/onboard");
  }

  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  async function handleRefreshRisk() {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("sc_token") : null;
      const res = await fetch("http://localhost:8000/api/refresh-risk", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        setRefreshMsg(`✓ Updated ${data.updated} countries`);
      } else {
        setRefreshMsg(`Error: ${data.detail ?? "refresh failed"}`);
      }
    } catch {
      setRefreshMsg("Network error — is the backend running?");
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMsg(null), 4000);
    }
  }

  if (!user)
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      {/* ── Top navigation ─────────────────────────────────────────── */}
      <header className="border-b border-zinc-800 bg-zinc-900/60 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-zinc-100 font-semibold tracking-tight text-sm hover:text-indigo-400 transition-colors"
            >
              SentriChain
            </Link>
            <span className="text-zinc-700 text-xs hidden sm:block">|</span>
            <span className="text-zinc-500 text-xs hidden sm:block">
              Risk Dashboard
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* History toggle */}
            <button
              onClick={() => setHistoryOpen((v) => !v)}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                historyOpen
                  ? "bg-indigo-600/20 border-indigo-500/40 text-indigo-400"
                  : "border-zinc-700 text-zinc-400 hover:text-zinc-100 hover:border-zinc-500"
              }`}
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              History
              {history.length > 0 && (
                <span className="bg-indigo-600 text-white text-[10px] px-1.5 rounded-full font-medium">
                  {history.length}
                </span>
              )}
            </button>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen((v) => !v)}
                className="flex items-center gap-2 text-sm text-zinc-300 hover:text-zinc-100 transition-colors"
              >
                <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-semibold text-white select-none">
                  {user.full_name.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:block text-xs">
                  {user.full_name.split(" ")[0]}
                </span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                    user.role === "admin"
                      ? "bg-amber-500/10 text-amber-400"
                      : "bg-indigo-500/10 text-indigo-400"
                  }`}
                >
                  {user.role}
                </span>
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 top-10 w-44 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl overflow-hidden z-50">
                  <Link
                    href="/profile"
                    className="block px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    Profile &amp; settings
                  </Link>
                  <Link
                    href="/onboard"
                    className="block px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    Update company profile
                  </Link>
                  <button
                    onClick={() => { handleRefreshRisk(); setUserMenuOpen(false); }}
                    disabled={refreshing}
                    className="w-full text-left px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-indigo-400 transition-colors border-t border-zinc-800 disabled:opacity-50"
                  >
                    {refreshing ? "Refreshing…" : "Refresh risk data"}
                  </button>
                  <button
                    onClick={handleReonboard}
                    className="w-full text-left px-4 py-2.5 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-red-400 transition-colors border-t border-zinc-800"
                  >
                    Reset & re-onboard
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tab bar */}
        <div className="max-w-7xl mx-auto px-6 flex gap-1 border-t border-zinc-800/50">
          {(
            [
              { id: "overview", label: "Overview" },
              { id: "recommendations", label: "Best Matches" },
              { id: "analysis", label: "Deep Analysis" },
              { id: "compare", label: "Compare Countries" },
            ] as { id: Tab; label: string }[]
          ).map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === id
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* Refresh risk toast */}
      {refreshMsg && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-lg bg-zinc-800 border border-zinc-700 text-sm text-zinc-100 shadow-xl transition-all">
          {refreshMsg}
        </div>
      )}

      <div className="flex flex-1">
        {/* ── History sidebar ───────────────────────────────────────── */}
        {historyOpen && (
          <aside className="w-72 shrink-0 border-r border-zinc-800 bg-zinc-900/50 p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
                Recent analyses
              </h2>
              <button
                onClick={() => {
                  setHistory([]);
                  saveHistory([]);
                }}
                className="text-[10px] text-zinc-600 hover:text-red-400 transition-colors"
              >
                Clear all
              </button>
            </div>
            {history.length === 0 ? (
              <p className="text-xs text-zinc-600 text-center py-8">
                No analyses yet.
              </p>
            ) : (
              <div className="space-y-2">
                {history.map((entry) => (
                  <button
                    key={entry.id}
                    onClick={() => restoreFromHistory(entry)}
                    className="w-full text-left p-3 rounded-lg bg-zinc-800/60 border border-zinc-700/50 hover:border-zinc-600 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <p className="text-xs font-medium text-zinc-200 group-hover:text-white truncate">
                        {entry.supplierName}
                      </p>
                      <span
                        className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded border font-medium ${riskColor(entry.ensembleScore)}`}
                      >
                        {entry.riskLevel}
                      </span>
                    </div>
                    <p className="text-[10px] text-zinc-500">{entry.country}</p>
                    <p className="text-[10px] text-zinc-600 mt-1">
                      {entry.timestamp}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </aside>
        )}

        {/* ── Main content ────────────────────────────────────────── */}
        <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
          {/* ═══ TAB: OVERVIEW ═══ */}
          {tab === "overview" && (
            <div>
              <div className="mb-4">
                <h1 className="text-xl font-semibold text-zinc-100">
                  {profile?.company_name
                    ? `Suppliers for ${profile.company_name}`
                    : "Supplier Overview"}
                </h1>
                <p className="text-zinc-500 text-sm mt-0.5">
                  {profile?.raw_materials?.length
                    ? `${profile.company_type ? `Filtered to ${profile.company_type} suppliers` : "Showing suppliers"} — materials: ${profile.raw_materials.slice(0, 3).join(", ")}${profile.raw_materials.length > 3 ? ` +${profile.raw_materials.length - 3} more` : ""}`
                    : "All suppliers sorted by country, with logistics and economic factors"}
                </p>
              </div>
              {/* Profile context banner */}
              {profile && (
                <div className="mb-6 flex flex-wrap items-center gap-3 p-3 bg-indigo-600/10 border border-indigo-600/20 rounded-xl text-xs">
                  <span className="text-indigo-400 font-medium">{profile.company_type}</span>
                  {profile.preferred_countries.length > 0 && (
                    <span className="text-zinc-400">
                      Preferred sources:{" "}
                      <span className="text-zinc-200">{profile.preferred_countries.join(", ")}</span>
                    </span>
                  )}
                  {profile.raw_materials.length > 0 && (
                    <span className="text-zinc-400">
                      Materials:{" "}
                      <span className="text-zinc-200">{profile.raw_materials.slice(0, 4).join(", ")}{profile.raw_materials.length > 4 ? ` +${profile.raw_materials.length - 4}` : ""}</span>
                    </span>
                  )}
                  <a href="/onboard" className="ml-auto text-indigo-400 hover:text-indigo-300 transition-colors">Edit profile →</a>
                </div>
              )}
              {overviewLoading && <OverviewSkeleton />}
              {overviewError && <ErrorBanner msg={overviewError} />}
              {overview && (
                <OverviewContent
                  overview={overview}
                  profile={profile}
                  onDeepAnalyze={(id) => {
                    setTab("analysis");
                    handleSupplierSelect(id);
                  }}
                />
              )}
            </div>
          )}

          {/* ═══ TAB: COMPARE ═══ */}
          {tab === "compare" && (
            <div>
              {overviewLoading && <OverviewSkeleton />}
              {overviewError && <ErrorBanner msg={overviewError} />}
              {overview && (
                <CompareContent
                  overview={overview}
                  profile={profile}
                />
              )}
            </div>
          )}

          {/* ═══ TAB: RECOMMENDATIONS ═══ */}
          {tab === "recommendations" && (
            <div>
              <div className="mb-6">
                <h1 className="text-xl font-semibold text-zinc-100">
                  Best Matches for Your Profile
                </h1>
                <p className="text-zinc-500 text-sm mt-0.5">
                  Ranked by raw materials match, preferred countries,
                  reliability and risk
                </p>
              </div>
              {recsLoading && <RecsSkeleton />}
              {recsError && <ErrorBanner msg={recsError} />}
              {recs && (
                <RecsContent
                  recs={recs}
                  onDeepAnalyze={(id) => {
                    setTab("analysis");
                    handleSupplierSelect(id);
                  }}
                />
              )}
            </div>
          )}

          {/* ═══ TAB: DEEP ANALYSIS ═══ */}
          {tab === "analysis" && (
            <div>
              {/* Page heading + export */}
              <div className="mb-8 flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-xl font-semibold text-zinc-100">
                    Deep Analysis
                  </h1>
                  <p className="text-zinc-500 text-sm mt-0.5">
                    Multi-agent supply chain risk analysis — schedule variance,
                    geopolitical signals, ensemble scoring
                  </p>
                </div>
                {analysisData && selectedSupplier && (
                  <button
                    onClick={handleExport}
                    className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-zinc-700 text-zinc-400 hover:text-zinc-100 hover:border-zinc-500 transition-colors shrink-0"
                  >
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Export report
                  </button>
                )}
              </div>

              {/* Error banner */}
              {error && (
                <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                  <svg
                    className="w-4 h-4 mt-0.5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                    />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              {/* Supplier selector */}
              <div className="mb-6 max-w-xl">
                {isLoadingSuppliers ? (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-3 bg-zinc-800 rounded w-24" />
                    <div className="h-10 bg-zinc-800 rounded" />
                  </div>
                ) : (
                  <SupplierSelector
                    suppliers={sortedSuppliers}
                    selectedId={selectedSupplierId}
                    onSelect={handleSupplierSelect}
                    disabled={isAnalyzing}
                    profile={profile}
                  />
                )}
              </div>

              {/* Analyzing spinner */}
              {isAnalyzing && (
                <div className="flex items-center gap-3 py-12 text-zinc-400 text-sm">
                  <div className="w-5 h-5 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
                  <span>
                    Running agent pipeline for{" "}
                    {selectedSupplier?.supplier_name ?? "supplier"}…
                  </span>
                </div>
              )}

              {/* Results */}
              {analysisData && !isAnalyzing && (
                <>
                  {/* Supplier meta strip */}
                  {selectedSupplier && (
                    <div className="mb-6 flex flex-wrap items-center gap-4 p-4 bg-zinc-900 border border-zinc-800 rounded-xl text-sm">
                      <div>
                        <span className="text-zinc-500 text-xs">Supplier</span>
                        <p className="text-zinc-100 font-medium">
                          {selectedSupplier.supplier_name}
                        </p>
                      </div>
                      <div className="w-px h-8 bg-zinc-800" />
                      <div>
                        <span className="text-zinc-500 text-xs">Country</span>
                        <p className="text-zinc-100 font-medium">
                          {selectedSupplier.country}
                        </p>
                      </div>
                      <div className="w-px h-8 bg-zinc-800" />
                      <div>
                        <span className="text-zinc-500 text-xs">
                          Reliability
                        </span>
                        <p className="text-zinc-100 font-mono font-medium">
                          {selectedSupplier.reliability_score.toFixed(0)}%
                        </p>
                      </div>
                      <div className="w-px h-8 bg-zinc-800" />
                      <div>
                        <span className="text-zinc-500 text-xs">
                          Avg Lead Time
                        </span>
                        <p className="text-zinc-100 font-mono font-medium">
                          {selectedSupplier.average_delivery_time}d
                        </p>
                      </div>
                      <div className="w-px h-8 bg-zinc-800" />
                      <div>
                        <span className="text-zinc-500 text-xs">
                          Cost Class
                        </span>
                        <p className="text-zinc-100 font-medium capitalize">
                          {selectedSupplier.cost_competitiveness}
                        </p>
                      </div>
                      <div className="w-px h-8 bg-zinc-800" />
                      <div>
                        <span className="text-zinc-500 text-xs">
                          Ensemble Risk
                        </span>
                        <p
                          className={`font-mono font-semibold text-sm ${
                            analysisData.ensemble.final_score >= 0.7
                              ? "text-red-400"
                              : analysisData.ensemble.final_score >= 0.4
                                ? "text-amber-400"
                                : "text-emerald-400"
                          }`}
                        >
                          {analysisData.ensemble.final_score.toFixed(3)}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Cards grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <RiskCard
                      schedule={analysisData.schedule}
                      ensemble={analysisData.ensemble}
                    />
                    <SummaryCard
                      summary={analysisData.summary}
                      geoRisk={analysisData.geoRisk}
                      agents={analysisData.agent_scores}
                      confidence={analysisData.confidence}
                      cv={analysisData.ensemble.coefficient_of_variation}
                    />
                    <CostCard
                      currency={analysisData.costImpact.currency}
                      estimatedCost={analysisData.costImpact.estimated_cost}
                    />
                    <AlternativesCard
                      alternatives={analysisData.alternatives}
                      currentIndustry={selectedSupplier?.industry}
                    />
                  </div>
                </>
              )}

              {/* Empty state */}
              {!analysisData && !isAnalyzing && !isLoadingSuppliers && (
                <div className="text-center py-20 text-zinc-600">
                  <svg
                    className="w-10 h-10 mx-auto mb-4 text-zinc-800"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="text-sm text-zinc-500 mb-1">
                    Select a supplier to run analysis
                  </p>
                  {history.length > 0 && (
                    <p className="text-xs text-zinc-600">
                      Or{" "}
                      <button
                        onClick={() => setHistoryOpen(true)}
                        className="text-indigo-400 hover:underline"
                      >
                        restore a previous result
                      </button>
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800">
        <div className="max-w-7xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-zinc-600">
          <span>SentriChain &mdash; SRMIST Ramapuram &bull; 2025</span>
          <span className="font-mono">v0.2.0</span>
        </div>
      </footer>
    </div>
  );
}
/* ── Error banner ─────────────────────────────────────────────────── */
function ErrorBanner({ msg }: { msg: string }) {
  return (
    <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
      <svg
        className="w-4 h-4 mt-0.5 shrink-0"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
        />
      </svg>
      <span>{msg}</span>
    </div>
  );
}

/* ── Overview tab ────────────────────────────────────────────────── */
function OverviewSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
        >
          <div className="h-4 bg-zinc-800 rounded w-32 mb-4" />
          <div className="space-y-3">
            {[1, 2].map((j) => (
              <div key={j} className="h-14 bg-zinc-800 rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function OverviewContent({
  overview,
  profile,
  onDeepAnalyze,
}: {
  overview: SupplierOverview;
  profile?: OnboardProfile | null;
  onDeepAnalyze: (id: number) => void;
}) {
  const [showAllIndustries, setShowAllIndustries] = useState(false);
  const countryGroups = overview.grouped_by_country as Record<
    string,
    SupplierCard[]
  >;
  const preferred = profile?.preferred_countries ?? [];
  const companyType = profile?.company_type ?? "";

  // Countries that have at least one supplier matching the user's industry
  const industryMatchCountries = new Set(
    Object.entries(countryGroups)
      .filter(([, sups]) =>
        sups.some(
          (s) =>
            s.industry &&
            companyType &&
            s.industry.toLowerCase() === companyType.toLowerCase(),
        ),
      )
      .map(([c]) => c),
  );

  const hasIndustryFilter = !!companyType && industryMatchCountries.size > 0;

  // When filter is ON: only show countries with matching-industry suppliers
  const filteredCountryKeys = hasIndustryFilter && !showAllIndustries
    ? Object.keys(countryGroups).filter((c) => industryMatchCountries.has(c))
    : Object.keys(countryGroups);

  // Sort: industry+preferred first, then preferred-only, then industry-only, then alpha
  const countries = filteredCountryKeys.sort((a, b) => {
    const aInd = industryMatchCountries.has(a) ? 0 : 1;
    const bInd = industryMatchCountries.has(b) ? 0 : 1;
    const aP = preferred.includes(a) ? 0 : 1;
    const bP = preferred.includes(b) ? 0 : 1;
    const aPriority = aInd * 2 + aP;
    const bPriority = bInd * 2 + bP;
    if (aPriority !== bPriority) return aPriority - bPriority;
    return a.localeCompare(b);
  });

  // When filter ON, only count matching-industry suppliers for stats
  const displayedSuppliers = hasIndustryFilter && !showAllIndustries
    ? overview.suppliers.filter(
        (s) => s.industry?.toLowerCase() === companyType.toLowerCase(),
      )
    : overview.suppliers;

  const avgReliability =
    displayedSuppliers.reduce((s, x) => s + x.reliability_score, 0) /
    (displayedSuppliers.length || 1);
  const avgShipping =
    displayedSuppliers.reduce(
      (s, x) => s + (x.country_factors?.avg_shipping_days ?? 0),
      0,
    ) / (displayedSuppliers.length || 1);

  function scoreToRiskStr(score: number) {
    if (score >= 0.6) return "high";
    if (score >= 0.35) return "medium";
    return "low";
  }

  return (
    <div className="space-y-8">
      {/* Industry filter toggle */}
      {hasIndustryFilter && (
        <div className="mb-4 flex items-center gap-3">
          <button
            onClick={() => setShowAllIndustries((v) => !v)}
            className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors ${
              showAllIndustries
                ? "border-zinc-600 text-zinc-400 hover:border-zinc-500"
                : "bg-emerald-600/20 border-emerald-500/50 text-emerald-400 hover:bg-emerald-600/30"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${ showAllIndustries ? "bg-zinc-600" : "bg-emerald-500" }`} />
            {showAllIndustries
              ? `Showing all industries`
              : `Filtered: ${companyType} suppliers only`}
          </button>
          {showAllIndustries && (
            <span className="text-xs text-zinc-600">{overview.suppliers.length} total suppliers across all industries</span>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Total Suppliers",
            value: String(overview.suppliers.length),
          },
          { label: "Countries", value: String(countries.length) },
          { label: "Avg Reliability", value: `${avgReliability.toFixed(0)}%` },
          { label: "Avg Shipping", value: `${avgShipping.toFixed(0)}d` },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center"
          >
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-zinc-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Per-country sections */}
      {countries.map((country) => {
        // When filter ON, only show matching-industry suppliers within each country
        const rawSups = countryGroups[country];
        const sups = hasIndustryFilter && !showAllIndustries
          ? rawSups.filter((s) => s.industry?.toLowerCase() === companyType.toLowerCase())
          : rawSups;
        if (sups.length === 0) return null;
        const first = sups[0];
        const cf = first.country_factors;
        return (
          <div
            key={country}
            className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
          >
            <div className={`flex flex-wrap items-center gap-3 px-6 py-4 border-b border-zinc-800 ${
              industryMatchCountries.has(country) && preferred.includes(country)
                ? "bg-violet-950/40 border-l-2 border-l-violet-500"
                : industryMatchCountries.has(country)
                  ? "bg-emerald-950/30 border-l-2 border-l-emerald-600"
                  : preferred.includes(country)
                    ? "bg-indigo-950/40 border-l-2 border-l-indigo-500"
                    : "bg-zinc-800/40"
            }`}>
              <h2 className="text-base font-semibold text-white">{country}</h2>
              {preferred.includes(country) && (
                <span className="text-[11px] px-2 py-0.5 rounded border font-medium bg-indigo-500/20 border-indigo-500/40 text-indigo-300">
                  ✓ Your preferred source
                </span>
              )}
              {industryMatchCountries.has(country) && (
                <span className="text-[11px] px-2 py-0.5 rounded border font-medium bg-emerald-500/20 border-emerald-500/40 text-emerald-300">
                  ✓ {companyType} suppliers
                </span>
              )}
              {cf?.economy_label && (
                <span className="text-[11px] px-2 py-0.5 rounded border font-medium bg-indigo-500/10 border-indigo-500/30 text-indigo-400">
                  {cf.economy_label}
                </span>
              )}
              {cf?.has_fta && (
                <span className="text-[11px] px-2 py-0.5 rounded border font-medium bg-emerald-500/10 border-emerald-500/30 text-emerald-400">
                  FTA Available
                </span>
              )}
              <div className="flex flex-wrap gap-4 ml-auto text-xs text-zinc-400">
                {cf?.corporate_tax_pct != null && (
                  <span>
                    💰 Tax:{" "}
                    <strong className="text-zinc-300">
                      {cf.corporate_tax_pct}%
                    </strong>
                  </span>
                )}
                {cf?.avg_shipping_days != null && (
                  <span>
                    🚢 Ship:{" "}
                    <strong className="text-zinc-300">
                      {cf.avg_shipping_days}d
                    </strong>
                  </span>
                )}
                {cf?.shipping_cost_usd_per_kg != null && (
                  <span>
                    📦{" "}
                    <strong className="text-zinc-300">
                      ${cf.shipping_cost_usd_per_kg}/kg
                    </strong>
                  </span>
                )}
                {cf?.customs_clearance_days != null && (
                  <span>
                    ⚡ Customs:{" "}
                    <strong className="text-zinc-300">
                      {cf.customs_clearance_days}d
                    </strong>
                  </span>
                )}
                {cf?.political_stability != null && (
                  <span>
                    🏛 Stability:{" "}
                    <strong className="text-zinc-300">
                      {cf.political_stability}/10
                    </strong>
                  </span>
                )}
              </div>
            </div>
            <div className="divide-y divide-zinc-800/50">
              {sups.map((s) => {
                const riskStr = scoreToRiskStr(s.composite_score);
                const rl = riskLabelByStr(riskStr);
                const score = s.composite_score ?? 0;
                const scoreColor =
                  score >= 0.6
                    ? "text-red-400"
                    : score >= 0.35
                      ? "text-amber-400"
                      : "text-emerald-400";
                return (
                  <div
                    key={s.supplier_id}
                    className="flex flex-wrap items-center gap-4 px-6 py-4 hover:bg-zinc-800/20 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white truncate">
                          {s.supplier_name}
                        </p>
                        {s.industry &&
                          companyType &&
                          s.industry.toLowerCase() ===
                            companyType.toLowerCase() && (
                            <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded font-medium bg-emerald-500/20 border border-emerald-500/40 text-emerald-300">
                              {s.industry}
                            </span>
                          )}
                      </div>
                      <p className="text-xs text-zinc-500 mt-0.5 capitalize">
                        {s.cost_competitiveness} cost · {s.avg_delivery_days}d
                        lead time
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs">
                      <span className="text-zinc-500">
                        Reliability:{" "}
                        <strong className="text-zinc-200">
                          {s.reliability_score.toFixed(0)}%
                        </strong>
                      </span>
                      <span className="text-zinc-500">
                        Delay:{" "}
                        <strong className="text-zinc-200">
                          {s.delay_pct.toFixed(0)}%
                        </strong>
                      </span>
                      <span className="text-zinc-500">
                        Avg delay:{" "}
                        <strong className="text-zinc-200">
                          {s.avg_delay_days.toFixed(1)}d
                        </strong>
                      </span>
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded border font-medium ${rl.cls}`}
                      >
                        {rl.label}
                      </span>
                      <span className="text-zinc-600">
                        Score:{" "}
                        <span className={`font-mono font-bold ${scoreColor}`}>
                          {score.toFixed(2)}
                        </span>
                      </span>
                      <button
                        onClick={() => onDeepAnalyze(s.supplier_id)}
                        className="px-3 py-1 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-600/40 text-indigo-400 rounded-lg text-xs transition-colors"
                      >
                        Deep Analysis →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
            {cf?.common_issues &&
              Array.isArray(cf.common_issues) &&
              cf.common_issues.length > 0 && (
                <div className="px-6 py-3 bg-amber-500/5 border-t border-amber-500/10">
                  <p className="text-xs text-amber-500/80 font-medium mb-1.5">
                    Known Issues
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(cf.common_issues as string[]).map((issue) => (
                      <span
                        key={issue}
                        className="text-[11px] bg-amber-500/10 border border-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full"
                      >
                        {issue}
                      </span>
                    ))}
                  </div>
                </div>
              )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Recommendations tab ─────────────────────────────────────────── */
function RecsSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="h-28 bg-zinc-900 border border-zinc-800 rounded-xl"
        />
      ))}
    </div>
  );
}

function RecsContent({
  recs,
  onDeepAnalyze,
}: {
  recs: RecommendationResponse;
  onDeepAnalyze: (id: number) => void;
}) {
  if (!recs.recommendations || recs.recommendations.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-zinc-500 text-sm">No recommendations yet.</p>
        <p className="text-zinc-600 text-xs mt-1">
          <a href="/onboard" className="text-indigo-400 hover:underline">
            Update your company profile
          </a>{" "}
          to get personalised recommendations.
        </p>
      </div>
    );
  }
  return (
    <div>
      {recs.summary && (
        <div className="mb-6 p-4 bg-indigo-600/10 border border-indigo-600/20 rounded-xl text-sm text-indigo-300">
          <span className="text-indigo-500 font-medium mr-2">Profile:</span>
          {recs.summary}
        </div>
      )}
      <div className="space-y-4">
        {recs.recommendations.map((r) => {
          const rl = riskLabelByStr(r.risk_level ?? "low");
          const rankColor =
            r.rank === 1
              ? "text-amber-400 border-amber-500/50 bg-amber-500/10"
              : r.rank === 2
                ? "text-zinc-300 border-zinc-500/50 bg-zinc-500/10"
                : r.rank === 3
                  ? "text-orange-400 border-orange-500/50 bg-orange-500/10"
                  : "text-zinc-500 border-zinc-700 bg-zinc-800/30";
          return (
            <div
              key={r.supplier_id}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-colors"
            >
              <div className="flex flex-wrap items-start gap-4">
                <div
                  className={`w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0 text-sm font-bold ${rankColor}`}
                >
                  #{r.rank}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <h3 className="text-base font-semibold text-white">
                      {r.supplier_name}
                    </h3>
                    <span className="text-zinc-500 text-sm">· {r.country}</span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded border font-medium ${rl.cls}`}
                    >
                      {rl.label}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-zinc-400 mb-3">
                    <span>
                      Reliability:{" "}
                      <strong className="text-zinc-200">
                        {r.reliability_score?.toFixed(0)}%
                      </strong>
                    </span>
                    <span>
                      Shipping:{" "}
                      <strong className="text-zinc-200">
                        {r.avg_shipping_days ?? "—"}d
                      </strong>
                    </span>
                    <span>
                      Cost/kg:{" "}
                      <strong className="text-zinc-200">
                        ${r.shipping_cost_usd_per_kg ?? "—"}
                      </strong>
                    </span>
                    <span>
                      Match:{" "}
                      <strong className="text-indigo-400">
                        {(r.match_score * 100).toFixed(0)}%
                      </strong>
                    </span>
                  </div>
                  {r.match_reasons && r.match_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {(r.match_reasons as string[]).map((reason) => (
                        <span
                          key={reason}
                          className="text-[11px] bg-indigo-900/30 border border-indigo-700/40 text-indigo-300 px-2.5 py-0.5 rounded-full"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onDeepAnalyze(r.supplier_id)}
                  className="shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors"
                >
                  Analyse →
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Compare Countries tab ───────────────────────────────────────── */
function CompareContent({
  overview,
  profile,
}: {
  overview: SupplierOverview;
  profile?: OnboardProfile | null;
}) {
  const [selected, setSelected] = useState<string[]>([]);

  const countryGroups = overview.grouped_by_country as Record<string, SupplierCard[]>;
  const preferred = profile?.preferred_countries ?? [];
  const companyType = profile?.company_type ?? "";

  const allCountries = Object.keys(countryGroups).sort((a, b) => {
    const aP = preferred.includes(a) ? 0 : 1;
    const bP = preferred.includes(b) ? 0 : 1;
    return aP - bP || a.localeCompare(b);
  });

  function toggleCountry(c: string) {
    setSelected((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : prev.length >= 4 ? prev : [...prev, c],
    );
  }

  type CData = {
    country: string;
    sups: SupplierCard[];
    cf: CountryFactors | null;
    riskScore: number | null;
    riskHeadline: string | null;
    avgReliability: number;
    avgDelay: number;
    industryCount: number;
  };

  function getData(country: string): CData {
    const sups = countryGroups[country] ?? [];
    const first = sups[0];
    const cf = first?.country_factors ?? null;
    const riskScore = first?.country_risk_score ?? null;
    const riskHeadline = first?.country_risk_headline ?? null;
    const avgReliability = sups.length
      ? sups.reduce((s, x) => s + x.reliability_score, 0) / sups.length
      : 0;
    const avgDelay = sups.length
      ? sups.reduce((s, x) => s + x.delay_pct, 0) / sups.length
      : 0;
    const industryCount = companyType
      ? sups.filter((s) => s.industry?.toLowerCase() === companyType.toLowerCase()).length
      : 0;
    return { country, sups, cf, riskScore, riskHeadline, avgReliability, avgDelay, industryCount };
  }

  const cols = selected.map(getData);

  function best<T extends number | null>(
    vals: T[],
    prefer: "min" | "max",
  ): T {
    const nums = vals.filter((v) => v != null) as number[];
    if (!nums.length) return null as T;
    return (prefer === "min" ? Math.min(...nums) : Math.max(...nums)) as T;
  }

  function cellCls(val: number | null, bestVal: number | null, prefer: "min" | "max") {
    if (val == null || bestVal == null) return "text-zinc-400";
    const isBest = prefer === "min" ? val === bestVal : val === bestVal;
    return isBest ? "text-emerald-400 font-bold" : "text-zinc-200";
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-zinc-100">Compare Countries</h1>
        <p className="text-zinc-500 text-sm mt-0.5">
          Select up to 4 countries to compare logistics, risk, and supplier quality side-by-side.
        </p>
      </div>

      {/* Country picker */}
      <div className="mb-8 p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-zinc-500 font-medium uppercase tracking-wide">
            Select countries (up to 4)
          </p>
          {selected.length > 0 && (
            <button
              onClick={() => setSelected([])}
              className="text-xs text-zinc-600 hover:text-red-400 transition-colors"
            >
              Clear all
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {allCountries.map((c) => {
            const isSelected = selected.includes(c);
            const isPref = preferred.includes(c);
            const hasIndustry = companyType
              ? (countryGroups[c] ?? []).some(
                  (s) => s.industry?.toLowerCase() === companyType.toLowerCase(),
                )
              : false;
            const disabled = !isSelected && selected.length >= 4;
            return (
              <button
                key={c}
                onClick={() => toggleCountry(c)}
                disabled={disabled}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                  isSelected
                    ? "bg-indigo-600/30 border-indigo-500 text-indigo-200 shadow-sm shadow-indigo-500/20"
                    : disabled
                      ? "opacity-25 cursor-not-allowed border-zinc-800 text-zinc-600"
                      : hasIndustry
                        ? "border-emerald-700/60 text-emerald-400 hover:bg-emerald-500/10"
                        : isPref
                          ? "border-indigo-700/60 text-indigo-400 hover:bg-indigo-500/10"
                          : "border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200"
                }`}
              >
                {c}
                {isPref && <span className="ml-1 text-indigo-500 opacity-70">★</span>}
                {hasIndustry && <span className="ml-1 text-emerald-500 opacity-70">✓</span>}
              </button>
            );
          })}
        </div>
        {(preferred.length > 0 || companyType) && (
          <p className="text-[11px] text-zinc-600 mt-3">
            {preferred.length > 0 && <><span className="text-indigo-500">★</span> preferred source&nbsp;&nbsp;</>}
            {companyType && <><span className="text-emerald-500">✓</span> has {companyType} suppliers</>}
          </p>
        )}
      </div>

      {selected.length < 2 ? (
        <div className="text-center py-20 text-zinc-600">
          <svg
            className="w-12 h-12 mx-auto mb-4 text-zinc-800"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-sm text-zinc-500">Select at least 2 countries above to compare</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left text-xs text-zinc-600 font-medium pb-4 pr-6 w-44">Metric</th>
                {cols.map((d) => (
                  <th key={d.country} className="pb-4 px-4 text-center min-w-[140px]">
                    <p className="text-base font-bold text-white">{d.country}</p>
                    <div className="flex flex-wrap justify-center gap-1 mt-1">
                      {preferred.includes(d.country) && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">★ Preferred</span>
                      )}
                      {d.industryCount > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
                          {d.industryCount} {companyType}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Suppliers */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Total Suppliers</td>
                {cols.map((d) => (
                  <td key={d.country} className="py-3 px-4 text-center">
                    <span className="font-bold text-white">{d.sups.length}</span>
                  </td>
                ))}
              </tr>
              {/* Industry match */}
              {companyType && (
                <tr className="border-b border-zinc-800/50">
                  <td className="py-3 pr-6 text-xs text-zinc-500">{companyType} Suppliers</td>
                  {cols.map((d) => (
                    <td key={d.country} className="py-3 px-4 text-center">
                      <span className={`font-bold ${d.industryCount > 0 ? "text-emerald-400" : "text-zinc-700"}`}>
                        {d.industryCount}
                      </span>
                    </td>
                  ))}
                </tr>
              )}
              {/* Avg Reliability */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Avg Reliability</td>
                {(() => {
                  const b = best(cols.map((d) => d.avgReliability), "max");
                  return cols.map((d) => (
                    <td key={d.country} className="py-3 px-4 text-center">
                      <span className={cellCls(d.avgReliability, b, "max")}>{d.avgReliability.toFixed(0)}%</span>
                    </td>
                  ));
                })()}
              </tr>
              {/* Avg Delay */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Avg Delay Rate</td>
                {(() => {
                  const b = best(cols.map((d) => d.avgDelay), "min");
                  return cols.map((d) => (
                    <td key={d.country} className="py-3 px-4 text-center">
                      <span className={cellCls(d.avgDelay, b, "min")}>{d.avgDelay.toFixed(1)}%</span>
                    </td>
                  ));
                })()}
              </tr>
              {/* Geopolitical Risk */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Geopolitical Risk</td>
                {(() => {
                  const b = best(cols.map((d) => d.riskScore), "min");
                  return cols.map((d) => {
                    const rs = d.riskScore;
                    const rsCls = rs == null ? "text-zinc-600" : rs === b ? "text-emerald-400 font-bold" : rs >= 7 ? "text-red-400" : rs >= 4 ? "text-amber-400" : "text-emerald-400";
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={rsCls}>{rs?.toFixed(1) ?? "—"}<span className="text-zinc-600 text-xs">/10</span></span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* Shipping Cost */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Shipping Cost/kg</td>
                {(() => {
                  const b = best(cols.map((d) => d.cf?.shipping_cost_usd_per_kg ?? null), "min");
                  return cols.map((d) => {
                    const v = d.cf?.shipping_cost_usd_per_kg ?? null;
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={cellCls(v, b, "min")}>{v != null ? `$${v}` : "—"}</span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* Shipping Days */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Avg Shipping Days</td>
                {(() => {
                  const b = best(cols.map((d) => d.cf?.avg_shipping_days ?? null), "min");
                  return cols.map((d) => {
                    const v = d.cf?.avg_shipping_days ?? null;
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={cellCls(v, b, "min")}>{v != null ? `${v}d` : "—"}</span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* Customs Clearance */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Customs Clearance</td>
                {(() => {
                  const b = best(cols.map((d) => d.cf?.customs_clearance_days ?? null), "min");
                  return cols.map((d) => {
                    const v = d.cf?.customs_clearance_days ?? null;
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={cellCls(v, b, "min")}>{v != null ? `${v}d` : "—"}</span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* Political Stability */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Political Stability</td>
                {(() => {
                  const b = best(cols.map((d) => d.cf?.political_stability ?? null), "max");
                  return cols.map((d) => {
                    const v = d.cf?.political_stability ?? null;
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={cellCls(v, b, "max")}>{v != null ? `${v}/10` : "—"}</span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* FTA */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">FTA Available</td>
                {cols.map((d) => (
                  <td key={d.country} className="py-3 px-4 text-center">
                    {d.cf?.has_fta
                      ? <span className="text-emerald-400 font-bold">Yes</span>
                      : <span className="text-zinc-600">No</span>}
                  </td>
                ))}
              </tr>
              {/* Corporate Tax */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Corporate Tax</td>
                {(() => {
                  const b = best(cols.map((d) => d.cf?.corporate_tax_pct ?? null), "min");
                  return cols.map((d) => {
                    const v = d.cf?.corporate_tax_pct ?? null;
                    return (
                      <td key={d.country} className="py-3 px-4 text-center">
                        <span className={cellCls(v, b, "min")}>{v != null ? `${v}%` : "—"}</span>
                      </td>
                    );
                  });
                })()}
              </tr>
              {/* Economy */}
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 pr-6 text-xs text-zinc-500">Economy</td>
                {cols.map((d) => (
                  <td key={d.country} className="py-3 px-4 text-center">
                    <span className="text-xs text-zinc-400">{d.cf?.economy_label ?? "—"}</span>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>

          {/* Risk headlines */}
          {cols.some((d) => d.riskHeadline) && (
            <div className={["mt-6 grid gap-3", ["grid-cols-1","grid-cols-2","grid-cols-3","grid-cols-4"][cols.length - 1]].join(" ")}>
              {cols.map((d) => (
                <div key={d.country} className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                  <p className="text-[11px] text-zinc-500 mb-1.5 font-medium">{d.country} — Latest signal</p>
                  <p className="text-xs text-zinc-300 leading-relaxed">{d.riskHeadline ?? "No signal data"}</p>
                </div>
              ))}
            </div>
          )}

          {/* Supplier lists per country */}
          <div className={["mt-6 grid gap-4", ["grid-cols-1","grid-cols-2","grid-cols-3","grid-cols-4"][cols.length - 1]].join(" ")}>
            {cols.map((d) => (
              <div key={d.country}>
                <p className="text-[11px] text-zinc-500 font-semibold mb-2 uppercase tracking-wide">
                  {d.country} Suppliers
                </p>
                <div className="space-y-1.5">
                  {d.sups.slice(0, 6).map((s) => {
                    const isMatch = companyType && s.industry?.toLowerCase() === companyType.toLowerCase();
                    return (
                      <div
                        key={s.supplier_id}
                        className={`text-xs px-2.5 py-2 rounded-lg border ${
                          isMatch
                            ? "border-emerald-800/50 bg-emerald-950/30 text-emerald-200"
                            : "border-zinc-800 bg-zinc-900/40 text-zinc-400"
                        }`}
                      >
                        <p className="font-medium truncate">{s.supplier_name}</p>
                        <p className="text-zinc-600 mt-0.5">{s.reliability_score.toFixed(0)}% reliable · {s.avg_delivery_days}d</p>
                      </div>
                    );
                  })}
                  {d.sups.length > 6 && (
                    <p className="text-[11px] text-zinc-600 pl-1">+{d.sups.length - 6} more</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
