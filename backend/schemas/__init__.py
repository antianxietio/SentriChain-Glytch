"""
Schemas module — Pydantic request/response models.
Designed to match paper Fig. 2 output structure.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date, datetime


# ---------------------------------------------------------------------------
# DB-level schemas
# ---------------------------------------------------------------------------

class SupplierSchema(BaseModel):
    id: int
    supplier_name: str
    country: str
    industry: Optional[str] = None
    reliability_score: float
    average_delivery_time: int
    cost_competitiveness: str

    class Config:
        from_attributes = True


class EquipmentScheduleSchema(BaseModel):
    id: int
    equipment_name: str
    supplier_id: int
    planned_delivery_date: date
    actual_delivery_date: Optional[date]
    equipment_value: float
    status: str

    class Config:
        from_attributes = True


class CountryRiskSchema(BaseModel):
    id: int
    country: str
    risk_score: float
    last_updated: datetime
    headline: str
    source_url: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Analysis response schemas (paper Fig. 2 output)
# ---------------------------------------------------------------------------

class AgentResult(BaseModel):
    """Output from a single risk agent."""
    agent: str
    score: float           # R_ij ∈ [0, 1]
    reasoning: str         # Explainability — supporting evidence


class EnsembleResult(BaseModel):
    """Eq (3) and Eq (4) aggregation output."""
    final_score: float                      # R_i = (1/N) * Σ R_ij
    coefficient_of_variation: float         # CV = std / mean
    high_uncertainty: bool                  # CV > 0.30
    confidence: str                         # 'high' | 'medium' | 'low'
    n_agents: int
    individual_scores: Dict[str, float]


class ScheduleMetrics(BaseModel):
    """Internal EVM and schedule variance metrics."""
    avg_delay_days: float
    delay_percent: float
    risk_level: str                         # 'low' | 'medium' | 'high'
    r_schedule: float                       # Eq (2) value
    spi: float                              # Schedule Performance Index
    sv_days: float                          # Schedule Variance in days
    disruption_threshold_days: float        # T from Eq (2)


class CostImpact(BaseModel):
    currency: str
    estimated_cost: float


class GeoRiskSignal(BaseModel):
    """External geopolitical signal."""
    headline: str
    source_url: Optional[str]
    r_external: float                       # Normalized 0-1 country risk
    risk_score_raw: float                   # Original 0-10 score
    gdelt_event_count: int
    data_source: str                        # 'world_bank_wgi' | 'database' | 'default'


class AlternativeSupplier(BaseModel):
    id: int
    name: str
    country: str
    score: float
    industry: Optional[str] = None
    same_industry: bool = False


class AnalyzeSupplierResponse(BaseModel):
    """Full response from /api/suppliers/{id}/analyze — matches paper Fig. 2."""
    supplier_id: int
    supplier_name: str
    country: str

    # Internal metrics
    schedule: ScheduleMetrics
    costImpact: CostImpact

    # Multi-agent system output (paper §III)
    agent_scores: List[AgentResult]
    ensemble: EnsembleResult

    # External signal grounding
    geoRisk: Optional[GeoRiskSignal]

    # Recommendations
    alternatives: List[AlternativeSupplier]

    # Natural language output
    summary: str
    confidence: str


# Legacy response for POST /api/analyze (global)
class AlternativeSupplierLegacy(BaseModel):
    supplier_name: str
    country: str
    reliability_score: float
    average_delivery_time: int
    cost_competitiveness: str
    reason: str


class RiskAnalysisResponse(BaseModel):
    schedule_risk: str
    delayed_equipment_count: int
    total_equipment_count: int
    cost_impact: float
    high_risk_countries: List[str]
    alternative_suppliers: List[AlternativeSupplierLegacy]
    executive_summary: str


# ---------------------------------------------------------------------------
# Onboarding schemas
# ---------------------------------------------------------------------------

class OnboardRequest(BaseModel):
    company_name: str
    company_type: str
    raw_materials: List[str]         # e.g. ["Semiconductors", "PCBs"]
    preferred_countries: List[str]   # e.g. ["Vietnam", "India"]
    notes: Optional[str] = None


class OnboardResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    company_type: str
    raw_materials: List[str]
    preferred_countries: List[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Country factors schema
# ---------------------------------------------------------------------------

class CountryFactorsSchema(BaseModel):
    country: str
    continent: str
    economy_score: float
    economy_label: str
    gdp_growth_pct: float
    currency: str
    currency_volatility: str
    corporate_tax_pct: float
    import_tariff_pct: float
    vat_gst_pct: float
    tax_complexity: str
    has_fta: bool
    fta_partners: List[str]
    avg_shipping_days: int
    shipping_cost_usd_per_kg: float
    port_efficiency_score: float
    transport_reliability: float
    customs_clearance_days: int
    common_issues: List[str]
    political_stability: float
    infrastructure_score: float
    labor_cost_index: float

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Comprehensive supplier card (for overview table)
# ---------------------------------------------------------------------------

class SupplierCard(BaseModel):
    """All factors for a supplier + its country, used in the overview table."""
    supplier_id: int
    supplier_name: str
    country: str
    continent: str
    industry: Optional[str] = None
    reliability_score: float
    avg_delivery_days: int
    cost_competitiveness: str
    # Delay stats (computed from schedules)
    total_schedules: int
    delayed_count: int
    delay_pct: float
    avg_delay_days: float
    # Country factors (can be None if not seeded)
    country_factors: Optional[CountryFactorsSchema]
    # Country risk
    country_risk_score: Optional[float]
    country_risk_headline: Optional[str]
    # Composite score: lower = better overall option
    composite_score: float


class SupplierOverviewResponse(BaseModel):
    suppliers: List[SupplierCard]
    grouped_by_country: Dict[str, List[SupplierCard]]


# ---------------------------------------------------------------------------
# Recommendation schema
# ---------------------------------------------------------------------------

class SupplierRecommendation(BaseModel):
    rank: int
    supplier_id: int
    supplier_name: str
    country: str
    industry: Optional[str] = None
    match_score: float          # 0-1, higher = better match
    match_reasons: List[str]
    reliability_score: float
    avg_delivery_days: int
    shipping_cost_usd_per_kg: Optional[float]
    avg_shipping_days: Optional[int]
    risk_level: str


class RecommendationResponse(BaseModel):
    raw_materials: List[str]
    preferred_countries: List[str]
    recommendations: List[SupplierRecommendation]
    summary: str


