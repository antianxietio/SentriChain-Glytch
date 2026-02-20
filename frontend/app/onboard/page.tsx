"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { saveOnboardProfile, getOnboardProfile } from "@/lib/api";

// ── Data ─────────────────────────────────────────────────────────────────────

const COMPANY_TYPES = [
  "Manufacturing",
  "Electronics",
  "Automotive",
  "Pharmaceuticals",
  "Aerospace",
  "Energy",
  "Construction",
  "Food & Beverage",
  "Textiles",
  "Chemical",
  "Logistics",
  "Other",
];

// Materials relevant to each industry — shown only when that type is selected
const MATERIALS_BY_TYPE: Record<string, string[]> = {
  Manufacturing: [
    "Steel",
    "Aluminum",
    "Copper",
    "Precision Parts",
    "Hydraulic Parts",
    "Motors",
    "Wiring & Connectors",
    "Plastics & Polymers",
    "Industrial Chemicals",
    "Fasteners & Bearings",
    "Rubber & Seals",
    "Machine Tools",
  ],
  Electronics: [
    "Semiconductors",
    "PCBs",
    "Display Panels",
    "Batteries",
    "Rare Earth Elements",
    "Wiring & Connectors",
    "Sensors & Actuators",
    "Capacitors & Resistors",
    "Microcontrollers",
    "Optical Components",
  ],
  Automotive: [
    "Steel",
    "Aluminum",
    "Hydraulic Parts",
    "Wiring & Connectors",
    "Sensors & Actuators",
    "Precision Parts",
    "Plastics & Polymers",
    "Batteries",
    "Rubber & Seals",
    "Fasteners & Bearings",
    "Glass & Glazing",
    "Paints & Coatings",
  ],
  Pharmaceuticals: [
    "Active Pharmaceutical Ingredients (APIs)",
    "Excipients & Binders",
    "Chemical Solvents",
    "Biologic Raw Materials",
    "Reagents & Buffers",
    "Sterile Packaging",
    "Medical Glass & Vials",
    "Drug Delivery Devices",
    "Laboratory Chemicals",
    "Filtration Membranes",
    "Packaging Materials",
    "Cold-Chain Containers",
  ],
  Aerospace: [
    "Titanium Alloys",
    "Carbon Fiber Composites",
    "Aluminum Alloys",
    "High-Temperature Alloys",
    "Precision Parts",
    "Hydraulic Parts",
    "Avionics Components",
    "Sensors & Actuators",
    "Fasteners & Bearings",
    "Optical Components",
    "Thermal Insulation",
    "Fuel System Components",
  ],
  Energy: [
    "Steel",
    "Copper",
    "Rare Earth Elements",
    "Batteries",
    "Solar Panels",
    "Turbine Components",
    "Industrial Chemicals",
    "Hydraulic Parts",
    "Cables & Conductors",
    "Transformers",
    "Insulation Materials",
    "Pumps & Valves",
  ],
  Construction: [
    "Steel",
    "Aluminum",
    "Copper",
    "Cement & Concrete Additives",
    "Plastics & Polymers",
    "Hydraulic Parts",
    "Wiring & Connectors",
    "Glass & Glazing",
    "Insulation Materials",
    "Fasteners & Bearings",
    "Paints & Coatings",
    "Lumber & Wood Products",
  ],
  "Food & Beverage": [
    "Packaging Materials",
    "Food-Grade Chemicals",
    "Flavoring Agents",
    "Preservatives & Additives",
    "Industrial Equipment",
    "Agricultural Raw Materials",
    "Enzymes & Cultures",
    "Sweeteners",
    "Fats & Oils",
    "Starches & Proteins",
    "Natural Colors & Extracts",
    "Cleaning & Sanitation Agents",
  ],
  Textiles: [
    "Cotton Fiber",
    "Synthetic Fibers (Nylon/Polyester)",
    "Wool & Natural Fibers",
    "Dyes & Pigments",
    "Chemical Treatments",
    "Packaging Materials",
    "Industrial Threads",
    "Elastane & Spandex",
    "Adhesives & Coatings",
    "Knitting & Weaving Machinery Parts",
  ],
  Chemical: [
    "Industrial Chemicals",
    "Solvents",
    "Catalysts",
    "Reagents",
    "Plastics & Polymers",
    "Rare Earth Elements",
    "Acids & Bases",
    "Specialty Gases",
    "Surfactants",
    "Pigments & Dyes",
    "Adhesives & Sealants",
    "Petrochemicals",
  ],
  Logistics: [
    "Packaging Materials",
    "Vehicle Components",
    "Hydraulic Parts",
    "Sensors & Actuators",
    "Wiring & Connectors",
    "Fuel Additives",
    "Lubricants & Oils",
    "Fasteners & Bearings",
    "Conveyor Components",
    "Safety Equipment",
    "Pallets & Load Carriers",
    "Warehouse Equipment",
  ],
  Other: [
    "Semiconductors",
    "PCBs",
    "Steel",
    "Aluminum",
    "Copper",
    "Plastics & Polymers",
    "Industrial Chemicals",
    "Packaging Materials",
    "Precision Parts",
    "Wiring & Connectors",
    "Sensors & Actuators",
    "Batteries",
  ],
};

const EXPORT_COUNTRIES = [
  { name: "China", flag: "🇨🇳" },
  { name: "India", flag: "🇮🇳" },
  { name: "Vietnam", flag: "🇻🇳" },
  { name: "Taiwan", flag: "🇹🇼" },
  { name: "South Korea", flag: "🇰🇷" },
  { name: "Germany", flag: "🇩🇪" },
  { name: "Japan", flag: "🇯🇵" },
  { name: "USA", flag: "🇺🇸" },
  { name: "Malaysia", flag: "🇲🇾" },
  { name: "Mexico", flag: "🇲🇽" },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function OnboardPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [loadingExisting, setLoadingExisting] = useState(true);

  // Form state
  const [companyName, setCompanyName] = useState("");
  const [companyType, setCompanyType] = useState("");
  const [rawMaterials, setRawMaterials] = useState<string[]>([]);
  const [preferredCountries, setPreferredCountries] = useState<string[]>([]);
  const [notes, setNotes] = useState("");

  // Materials list derived from selected industry — reset selections on change
  const availableMaterials =
    MATERIALS_BY_TYPE[companyType] ?? MATERIALS_BY_TYPE["Other"];
  const prevTypeRef = useState(companyType);
  useEffect(() => {
    if (prevTypeRef[0] === companyType) return;
    // Keep only selections that still exist in the new type's list
    setRawMaterials((prev) =>
      prev.filter((m) => availableMaterials.includes(m)),
    );
    prevTypeRef[1](companyType);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyType]);

  // Load existing profile (for editing)
  useEffect(() => {
    (async () => {
      let token = getToken();
      if (!token) {
        const { ensureSession } = await import("@/lib/auth");
        await ensureSession();
        token = getToken();
      }
      if (!token) {
        setLoadingExisting(false);
        return;
      }
      try {
        const p = await getOnboardProfile(token);
        if (p) {
          setCompanyName(p.company_name ?? "");
          setCompanyType(p.company_type ?? "");
          setRawMaterials(p.raw_materials ?? []);
          setPreferredCountries(p.preferred_countries ?? []);
          setNotes(p.notes ?? "");
        }
      } catch {
        // No profile yet — user will fill in the form
      } finally {
        setLoadingExisting(false);
      }
    })();
  }, []);

  // ── Helpers ────────────────────────────────────────────────────────────────

  function toggleItem(
    list: string[],
    setList: (v: string[]) => void,
    item: string,
  ) {
    setList(
      list.includes(item) ? list.filter((x) => x !== item) : [...list, item],
    );
  }

  async function doSave(token: string) {
    await saveOnboardProfile(
      {
        company_name: companyName,
        company_type: companyType,
        raw_materials: rawMaterials,
        preferred_countries: preferredCountries,
        notes,
      },
      token,
    );
    document.cookie = "sc_onboarded=1; path=/; max-age=2592000; SameSite=Lax";
    router.push("/dashboard");
  }

  async function handleSubmit() {
    const { ensureSession, clearSession } = await import("@/lib/auth");

    // Ensure we have a fresh token before trying
    if (!getToken()) await ensureSession();

    let token = getToken();
    if (!token) {
      setSaveError(
        "Could not reach the backend. Please refresh and try again.",
      );
      return;
    }

    setSaving(true);
    setSaveError(null);
    try {
      await doSave(token);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to save profile.";
      if (
        msg.toLowerCase().includes("session expired") ||
        msg.includes("401")
      ) {
        // Token expired — refresh silently and retry once
        try {
          clearSession();
          await ensureSession();
          token = getToken();
          if (!token) throw new Error("no token after refresh");
          await doSave(token);
        } catch {
          setSaveError(
            "Authentication failed. Please refresh the page and try again.",
          );
        }
      } else {
        setSaveError(msg);
      }
    } finally {
      setSaving(false);
    }
  }

  // ── Step validation ────────────────────────────────────────────────────────

  const canProceed =
    step === 1
      ? companyName.trim().length > 0 && companyType !== ""
      : step === 2
        ? rawMaterials.length > 0
        : step === 3
          ? preferredCountries.length > 0
          : true;

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loadingExisting) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#09090b]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col items-center justify-center px-4 py-12">
      {/* Logo / Title */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            SC
          </div>
          <span className="text-white font-semibold text-lg">SentriChain</span>
        </div>
        <p className="text-zinc-400 text-sm">
          Set up your supply chain profile
        </p>
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-lg mb-6">
        <div className="flex justify-between mb-2">
          {["Company", "Raw Materials", "Countries", "Review"].map(
            (label, i) => (
              <div
                key={label}
                className="flex flex-col items-center gap-1 flex-1"
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all
                ${
                  step > i + 1
                    ? "bg-indigo-500 text-white"
                    : step === i + 1
                      ? "bg-indigo-600 text-white ring-2 ring-indigo-400"
                      : "bg-zinc-800 text-zinc-500"
                }`}
                >
                  {step > i + 1 ? "✓" : i + 1}
                </div>
                <span
                  className={`text-xs ${step === i + 1 ? "text-indigo-400" : "text-zinc-600"}`}
                >
                  {label}
                </span>
              </div>
            ),
          )}
        </div>
        <div className="h-1 bg-zinc-800 rounded-full">
          <div
            className="h-1 bg-indigo-600 rounded-full transition-all duration-500"
            style={{ width: `${((step - 1) / 3) * 100}%` }}
          />
        </div>
      </div>

      {/* Card */}
      {saveError && (
        <div className="w-full max-w-lg mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {saveError}
        </div>
      )}
      <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-xl">
        {/* Step 1: Company Info */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-white mb-1">
              Tell us about your company
            </h2>
            <p className="text-zinc-500 text-sm mb-6">
              This helps us tailor supplier recommendations to your industry.
            </p>

            <label className="block mb-4">
              <span className="text-zinc-400 text-sm font-medium mb-1 block">
                Company Name *
              </span>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Acme Electronics Ltd."
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
              />
            </label>

            <label className="block mb-4">
              <span className="text-zinc-400 text-sm font-medium mb-1 block">
                Industry / Company Type *
              </span>
              <select
                value={companyType}
                onChange={(e) => setCompanyType(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition appearance-none"
              >
                <option value="">Select industry…</option>
                {COMPANY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-zinc-400 text-sm font-medium mb-1 block">
                Additional Notes{" "}
                <span className="text-zinc-600">(optional)</span>
              </span>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Any specific requirements or context…"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none"
              />
            </label>
          </div>
        )}

        {/* Step 2: Raw materials */}
        {step === 2 && (
          <div>
            <h2 className="text-xl font-bold text-white mb-1">
              {companyType
                ? `${companyType} raw materials`
                : "What raw materials do you need?"}
            </h2>
            <p className="text-zinc-500 text-sm mb-6">
              Select all that apply — we&apos;ll match you with the best
              suppliers for your industry.
            </p>
            <div className="flex flex-wrap gap-2">
              {availableMaterials.map((m) => {
                const active = rawMaterials.includes(m);
                return (
                  <button
                    key={m}
                    onClick={() => toggleItem(rawMaterials, setRawMaterials, m)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all
                      ${active ? "bg-indigo-600 border-indigo-500 text-white" : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200"}`}
                  >
                    {m}
                  </button>
                );
              })}
            </div>
            {rawMaterials.length > 0 && (
              <p className="mt-4 text-indigo-400 text-xs">
                {rawMaterials.length} item{rawMaterials.length > 1 ? "s" : ""}{" "}
                selected
              </p>
            )}
          </div>
        )}

        {/* Step 3: Countries */}
        {step === 3 && (
          <div>
            <h2 className="text-xl font-bold text-white mb-1">
              Preferred export countries
            </h2>
            <p className="text-zinc-500 text-sm mb-6">
              Select all countries you can source from. At least one required.
            </p>
            <div className="grid grid-cols-2 gap-3">
              {EXPORT_COUNTRIES.map(({ name, flag }) => {
                const active = preferredCountries.includes(name);
                return (
                  <button
                    key={name}
                    onClick={() =>
                      toggleItem(
                        preferredCountries,
                        setPreferredCountries,
                        name,
                      )
                    }
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-medium transition-all text-left
                      ${active ? "bg-indigo-600/20 border-indigo-500 text-white" : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white"}`}
                  >
                    <span className="text-2xl">{flag}</span>
                    <span>{name}</span>
                    {active && (
                      <span className="ml-auto text-indigo-400">✓</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div>
            <h2 className="text-xl font-bold text-white mb-1">
              Review your profile
            </h2>
            <p className="text-zinc-500 text-sm mb-6">
              Everything look right? You can always update this later from your
              profile settings.
            </p>

            <div className="space-y-4">
              <ReviewRow label="Company" value={companyName} />
              <ReviewRow label="Industry" value={companyType} />
              <div>
                <span className="text-zinc-500 text-xs uppercase tracking-wide block mb-1.5">
                  Raw Materials
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {rawMaterials.map((m) => (
                    <span
                      key={m}
                      className="bg-indigo-900/50 border border-indigo-700 text-indigo-300 px-2.5 py-0.5 rounded-full text-xs"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-zinc-500 text-xs uppercase tracking-wide block mb-1.5">
                  Preferred Countries
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {preferredCountries.map((c) => {
                    const flag =
                      EXPORT_COUNTRIES.find((x) => x.name === c)?.flag ?? "🌍";
                    return (
                      <span
                        key={c}
                        className="bg-zinc-800 border border-zinc-700 text-zinc-300 px-2.5 py-0.5 rounded-full text-xs"
                      >
                        {flag} {c}
                      </span>
                    );
                  })}
                </div>
              </div>
              {notes && <ReviewRow label="Notes" value={notes} />}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
            className="px-4 py-2 rounded-lg text-sm text-zinc-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition"
          >
            ← Back
          </button>

          {step < 4 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canProceed}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition"
            >
              Continue →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition flex items-center gap-2"
            >
              {saving && (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              {saving ? "Saving…" : "Go to Dashboard →"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-zinc-500 text-xs uppercase tracking-wide block mb-0.5">
        {label}
      </span>
      <span className="text-white text-sm">{value}</span>
    </div>
  );
}
