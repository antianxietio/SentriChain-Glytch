"use client";

import { useState, useEffect } from "react";
import {
  getSuppliers,
  analyzeSupplier,
  Supplier,
  AnalyzeResponse,
} from "@/lib/api";
import SupplierSelector from "@/components/SupplierSelector";
import RiskCard from "@/components/RiskCard";
import CostCard from "@/components/CostCard";
import AlternativesCard from "@/components/AlternativesCard";
import SummaryCard from "@/components/SummaryCard";
import Globe from "@/components/Globe";

export default function Home() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<number | null>(
    null
  );
  const [analysisData, setAnalysisData] = useState<AnalyzeResponse | null>(
    null
  );
  const [isLoadingSuppliers, setIsLoadingSuppliers] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch suppliers on mount
  useEffect(() => {
    async function fetchSuppliers() {
      try {
        setIsLoadingSuppliers(true);
        setError(null);
        const data = await getSuppliers();
        setSuppliers(data);
      } catch (err) {
        setError("Failed to load suppliers. Please try again.");
        console.error(err);
      } finally {
        setIsLoadingSuppliers(false);
      }
    }

    fetchSuppliers();
  }, []);

  // Handle supplier selection
  const handleSupplierSelect = async (supplierId: number) => {
    setSelectedSupplierId(supplierId);
    setIsAnalyzing(true);
    setError(null);

    try {
      const data = await analyzeSupplier(supplierId);
      setAnalysisData(data);
    } catch (err) {
      setError("Failed to load analysis. Please try again.");
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold bg-linear-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            🌍 Sentrichain
          </h1>
          <p className="text-slate-400 mt-1">
            Intelligent Supply Chain Risk Management Platform
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/50 text-red-400">
            ⚠️ {error}
          </div>
        )}

        {/* Supplier Selector */}
        <div className="mb-8 max-w-2xl">
          {isLoadingSuppliers ? (
            <div className="animate-pulse">
              <div className="h-4 bg-slate-800 rounded w-32 mb-2"></div>
              <div className="h-12 bg-slate-800 rounded"></div>
            </div>
          ) : (
            <SupplierSelector
              suppliers={suppliers}
              selectedId={selectedSupplierId}
              onSelect={handleSupplierSelect}
              disabled={isAnalyzing}
            />
          )}
        </div>

        {/* Loading State */}
        {isAnalyzing && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-slate-400">Analyzing...</p>
          </div>
        )}

        {/* Analysis Results */}
        {analysisData && !isAnalyzing && (
          <div className="space-y-6">
            {/* Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <RiskCard
                avgDelayDays={analysisData.schedule.avg_delay_days}
                delayPercent={analysisData.schedule.delay_percent}
                riskLevel={analysisData.schedule.risk_level}
              />

              <CostCard
                currency={analysisData.costImpact.currency}
                estimatedCost={analysisData.costImpact.estimated_cost}
              />

              <AlternativesCard alternatives={analysisData.alternatives} />

              <SummaryCard
                summary={analysisData.summary}
                headline={analysisData.geoRisk?.headline}
                sourceUrl={analysisData.geoRisk?.source_url}
              />
            </div>

            {/* Globe Section */}
            <div className="mt-6">
              <Globe />
            </div>
          </div>
        )}

        {/* Empty State */}
        {!analysisData && !isAnalyzing && !isLoadingSuppliers && (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-slate-300 mb-2">
              Ready to Analyze
            </h2>
            <p className="text-slate-400">
              Select a supplier above to begin risk analysis
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-16">
        <div className="container mx-auto px-4 py-6 text-center text-slate-500 text-sm">
          Built for VIT Chennai Hackathon 2025 • Sentrichain v0.1.0
        </div>
      </footer>
    </div>
  );
}
