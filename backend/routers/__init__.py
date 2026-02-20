"""
API route handlers.

Implements the multi-agent procurement risk pipeline from the paper (Fig. 2):
  Internal data  → ScheduleVarianceAgent     (Eq. 1, 2)
  External data  → GeopoliticalSignalAgent   (R_i^external)
  Historical     → SupplierReliabilityAgent
  Ensemble       → R_i = (1/N) Σ R_ij       (Eq. 3)
  Uncertainty    → CV = std / mean           (Eq. 4)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Supplier, EquipmentSchedule, CountryRisk, User, CountryFactors, UserCompanyProfile
from auth import get_current_user
from schemas import (
    RiskAnalysisResponse,
    AlternativeSupplierLegacy,
    AnalyzeSupplierResponse,
    ScheduleMetrics,
    CostImpact,
    GeoRiskSignal,
    AgentResult,
    EnsembleResult,
    AlternativeSupplier,
    SupplierCard,
    SupplierOverviewResponse,
    CountryFactorsSchema,
    RecommendationResponse,
    SupplierRecommendation,
)
from agents import (
    compute_r_schedule,
    compute_spi,
    compute_sv_days,
    agent_schedule,
    agent_geopolitical,
    agent_supplier_reliability,
    ensemble_aggregate,
    llm_summarize,
    DISRUPTION_THRESHOLD_DAYS,
)
from utils import fetch_gdelt_events, fetch_wgi_risk_score
from datetime import date as date_type

router = APIRouter(prefix="/api", tags=["api"])


# ---------------------------------------------------------------------------
# GET /api/suppliers
# ---------------------------------------------------------------------------

@router.get("/suppliers")
async def get_suppliers(db: Session = Depends(get_db)):
    """Returns all suppliers."""
    suppliers = db.query(Supplier).all()
    return {
        "suppliers": [
            {
                "id": s.id,
                "supplier_name": s.supplier_name,
                "country": s.country,
                "industry": s.industry,
                "reliability_score": s.reliability_score,
                "average_delivery_time": s.average_delivery_time,
                "cost_competitiveness": s.cost_competitiveness,
            }
            for s in suppliers
        ],
        "count": len(suppliers),
    }


# ---------------------------------------------------------------------------
# GET /api/suppliers/{supplier_id}
# ---------------------------------------------------------------------------

@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Returns a specific supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {
        "id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "country": supplier.country,
        "reliability_score": supplier.reliability_score,
        "average_delivery_time": supplier.average_delivery_time,
        "cost_competitiveness": supplier.cost_competitiveness,
    }


# ---------------------------------------------------------------------------
# GET /api/suppliers-overview  — all suppliers + country factors, sorted
# ---------------------------------------------------------------------------

@router.get("/suppliers-overview", response_model=SupplierOverviewResponse)
async def get_suppliers_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all suppliers enriched with country factors and delay stats,
    sorted first by country name then by supplier name. Groups by country.
    """
    import json as _json
    suppliers = db.query(Supplier).order_by(Supplier.country, Supplier.supplier_name).all()
    cf_map = {cf.country: cf for cf in db.query(CountryFactors).all()}
    cr_map = {cr.country: cr for cr in db.query(CountryRisk).all()}
    schedules_all = db.query(EquipmentSchedule).all()

    def _supplier_card(s: Supplier) -> SupplierCard:
        scheds = [sc for sc in schedules_all if sc.supplier_id == s.id]
        total = len(scheds)
        delayed = [sc for sc in scheds if sc.status == "delayed"]
        delayed_count = len(delayed)
        delay_pct = round(delayed_count / total * 100, 1) if total else 0.0

        from datetime import date as _date
        total_delay = 0.0
        for sc in delayed:
            if sc.actual_delivery_date and sc.planned_delivery_date:
                total_delay += (sc.actual_delivery_date - sc.planned_delivery_date).days
            elif not sc.actual_delivery_date and sc.planned_delivery_date:
                overdue = (_date.today() - sc.planned_delivery_date).days
                if overdue > 0:
                    total_delay += overdue
        avg_delay = round(total_delay / delayed_count, 1) if delayed_count else 0.0

        cf = cf_map.get(s.country)
        cr = cr_map.get(s.country)

        cf_schema = None
        if cf:
            cf_schema = CountryFactorsSchema(
                country=cf.country,
                continent=cf.continent,
                economy_score=cf.economy_score,
                economy_label=cf.economy_label,
                gdp_growth_pct=cf.gdp_growth_pct,
                currency=cf.currency,
                currency_volatility=cf.currency_volatility,
                corporate_tax_pct=cf.corporate_tax_pct,
                import_tariff_pct=cf.import_tariff_pct,
                vat_gst_pct=cf.vat_gst_pct,
                tax_complexity=cf.tax_complexity,
                has_fta=cf.has_fta,
                fta_partners=_json.loads(cf.fta_partners or "[]"),
                avg_shipping_days=cf.avg_shipping_days,
                shipping_cost_usd_per_kg=cf.shipping_cost_usd_per_kg,
                port_efficiency_score=cf.port_efficiency_score,
                transport_reliability=cf.transport_reliability,
                customs_clearance_days=cf.customs_clearance_days,
                common_issues=_json.loads(cf.common_issues or "[]"),
                political_stability=cf.political_stability,
                infrastructure_score=cf.infrastructure_score,
                labor_cost_index=cf.labor_cost_index,
            )

        # Composite score: lower = better
        risk_norm = (cr.risk_score / 10.0) if cr else 0.5
        delay_norm = min(1.0, avg_delay / 30.0)
        reliability_norm = 1.0 - (s.reliability_score / 100.0)
        shipping_norm = ((cf.avg_shipping_days / 35.0) if cf else 0.5)
        composite = round((risk_norm * 0.35 + delay_norm * 0.25 + reliability_norm * 0.25 + shipping_norm * 0.15), 4)

        return SupplierCard(
            supplier_id=s.id,
            supplier_name=s.supplier_name,
            country=s.country,
            continent=cf.continent if cf else "Unknown",
            industry=s.industry,
            reliability_score=s.reliability_score,
            avg_delivery_days=s.average_delivery_time,
            cost_competitiveness=s.cost_competitiveness,
            total_schedules=total,
            delayed_count=delayed_count,
            delay_pct=delay_pct,
            avg_delay_days=avg_delay,
            country_factors=cf_schema,
            country_risk_score=cr.risk_score if cr else None,
            country_risk_headline=cr.headline if cr else None,
            composite_score=composite,
        )

    cards = [_supplier_card(s) for s in suppliers]

    grouped: dict = {}
    for c in cards:
        grouped.setdefault(c.country, []).append(c)

    return SupplierOverviewResponse(suppliers=cards, grouped_by_country=grouped)


# ---------------------------------------------------------------------------
# GET /api/recommend  — best suppliers for user's raw material profile
# ---------------------------------------------------------------------------

@router.get("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uses the user's onboarding profile (raw materials + preferred countries)
    to score and rank suppliers. Returns top recommendations.
    """
    import json as _json
    from datetime import date as _date

    profile = db.query(UserCompanyProfile).filter(UserCompanyProfile.user_id == current_user.id).first()
    raw_materials = _json.loads(profile.raw_materials) if profile else []
    preferred = _json.loads(profile.preferred_countries or "[]") if profile else []

    suppliers = db.query(Supplier).all()
    cf_map = {cf.country: cf for cf in db.query(CountryFactors).all()}
    cr_map = {cr.country: cr for cr in db.query(CountryRisk).all()}
    schedules_all = db.query(EquipmentSchedule).all()

    # Keywords that map raw material categories to leading supplier countries
    MATERIAL_COUNTRY_MAP = {
        # Electronics
        "semiconductors":             ["Taiwan", "South Korea", "China"],
        "pcbs":                       ["China", "Taiwan", "South Korea"],
        "display panels":             ["South Korea", "China", "Taiwan"],
        "batteries":                  ["China", "South Korea"],
        "rare earth":                 ["China"],
        "sensors":                    ["Germany", "Japan", "South Korea"],
        "capacitor":                  ["Japan", "China", "South Korea"],
        "microcontroller":            ["Taiwan", "South Korea"],
        "optical":                    ["Japan", "Germany", "Taiwan"],
        # Manufacturing / Automotive
        "steel":                      ["India", "China", "Germany"],
        "aluminum":                   ["China", "India", "Germany"],
        "copper":                     ["China", "India", "South Korea"],
        "precision parts":            ["Germany", "India", "Taiwan"],
        "wiring":                     ["Vietnam", "China", "India"],
        "hydraulic":                  ["Germany", "India"],
        "motors":                     ["Germany", "India", "China"],
        "rubber":                     ["Malaysia", "Thailand", "Vietnam"],
        "fastener":                   ["China", "India", "Germany"],
        "plastics":                   ["China", "Germany", "South Korea"],
        "glass":                      ["China", "Germany", "India"],
        "paints":                     ["Germany", "India", "China"],
        # Pharmaceuticals
        "active pharmaceutical":      ["India", "China", "Germany"],
        "api":                        ["India", "China", "Germany"],
        "excipients":                 ["India", "Germany", "China"],
        "chemical solvents":          ["Germany", "China", "India"],
        "biologic":                   ["Germany", "USA", "India"],
        "reagents":                   ["Germany", "USA", "Japan"],
        "sterile packaging":          ["Germany", "India", "China"],
        "medical glass":              ["Germany", "India"],
        "drug delivery":              ["Germany", "India", "USA"],
        "laboratory":                 ["Germany", "Japan", "USA"],
        "filtration":                 ["Germany", "Japan", "India"],
        "cold-chain":                 ["Germany", "South Korea", "USA"],
        # Aerospace
        "titanium":                   ["Japan", "Germany", "China"],
        "carbon fiber":               ["Japan", "Germany", "South Korea"],
        "avionics":                   ["USA", "Germany", "Japan"],
        "thermal insulation":         ["Germany", "Japan", "China"],
        "fuel system":                ["Germany", "Japan", "USA"],
        # Energy
        "solar":                      ["China", "South Korea"],
        "turbine":                    ["Germany", "India", "China"],
        "cables":                     ["China", "Germany", "India"],
        "transformer":                ["China", "Germany", "India"],
        "insulation":                 ["China", "Germany"],
        "pumps":                      ["Germany", "India", "China"],
        # Construction
        "cement":                     ["India", "China", "Vietnam"],
        "lumber":                     ["Vietnam", "Malaysia", "Indonesia"],
        # Food & Beverage
        "packaging materials":        ["China", "Vietnam", "India"],
        "food-grade":                 ["Germany", "USA", "China"],
        "flavoring":                  ["China", "India", "Germany"],
        "preservatives":              ["China", "Germany", "India"],
        "enzymes":                    ["Germany", "China", "Denmark"],
        "sweeteners":                 ["China", "India"],
        "fats":                       ["Malaysia", "Indonesia", "India"],
        "starches":                   ["China", "India", "USA"],
        "agricultural":               ["India", "Vietnam", "Thailand"],
        # Textiles
        "cotton":                     ["India", "China", "Bangladesh"],
        "synthetic fibers":           ["China", "India", "Vietnam"],
        "dyes":                       ["India", "China", "Germany"],
        "elastane":                   ["China", "South Korea"],
        # Chemical
        "solvents":                   ["Germany", "China", "India"],
        "catalysts":                  ["Germany", "Japan", "China"],
        "surfactants":                ["Germany", "China", "India"],
        "petrochemicals":             ["China", "India", "South Korea"],
        "specialty gases":            ["Germany", "Japan", "South Korea"],
        # Logistics
        "lubricants":                 ["Germany", "China", "India"],
        "conveyor":                   ["Germany", "China", "India"],
        "warehouse":                  ["China", "Germany", "South Korea"],
        "pallets":                    ["China", "Vietnam", "India"],
    }

    scored = []
    for s in suppliers:
        scheds = [sc for sc in schedules_all if sc.supplier_id == s.id]
        total = len(scheds)
        delayed_count = sum(1 for sc in scheds if sc.status == "delayed")
        delay_pct = (delayed_count / total * 100) if total else 0.0

        cf = cf_map.get(s.country)
        cr = cr_map.get(s.country)

        risk_score = cr.risk_score if cr else 5.0
        shipping_days = cf.avg_shipping_days if cf else 20
        shipping_cost = cf.shipping_cost_usd_per_kg if cf else 1.0

        # Base score: higher = better preferred supplier
        score = (s.reliability_score / 100.0) * 0.35
        score += (1.0 - min(1.0, risk_score / 10.0)) * 0.25
        score += (1.0 - min(1.0, shipping_days / 30.0)) * 0.20
        score += (1.0 - min(1.0, delay_pct / 100.0)) * 0.20

        reasons = []

        # Boost for preferred countries
        country_boost = 0.0
        if preferred and s.country in preferred:
            country_boost = 0.15
            reasons.append(f"Matches your preferred source country ({s.country})")

        # Boost for material relevance
        material_boost = 0.0
        for mat in raw_materials:
            mat_lower = mat.lower()
            for key, countries in MATERIAL_COUNTRY_MAP.items():
                if key in mat_lower and s.country in countries:
                    material_boost = max(material_boost, 0.10)
                    reasons.append(f"{s.country} is a leading source for {mat}")
                    break

        # Industry match boost
        industry_boost = 0.0
        if profile and s.industry and profile.company_type and s.industry.lower() == profile.company_type.lower():
            industry_boost = 0.20
            reasons.append(f"Serves the {s.industry} industry — matches your company type")

        score = min(1.0, score + country_boost + material_boost + industry_boost)

        if s.reliability_score >= 90:
            reasons.append(f"High reliability ({s.reliability_score:.0f}%)")
        if shipping_days <= 14:
            reasons.append(f"Fast shipping: ~{shipping_days} days")
        if cf and cf.has_fta:
            reasons.append("Free Trade Agreement in place — lower tariff burden")
        if risk_score <= 3.0:
            reasons.append(f"Low geopolitical risk ({risk_score}/10)")
        elif risk_score >= 7.0:
            reasons.append(f"⚠ High geopolitical risk ({risk_score}/10) — consider diversification")

        if risk_score >= 7:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"
        else:
            risk_level = "low"

        scored.append({
            "supplier": s,
            "score": score,
            "reasons": list(dict.fromkeys(reasons)),  # deduplicate
            "risk_level": risk_level,
            "shipping_cost": cf.shipping_cost_usd_per_kg if cf else None,
            "shipping_days": cf.avg_shipping_days if cf else None,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:5]

    recommendations = [
        SupplierRecommendation(
            rank=i + 1,
            supplier_id=item["supplier"].id,
            supplier_name=item["supplier"].supplier_name,
            country=item["supplier"].country,
            industry=item["supplier"].industry,
            match_score=round(item["score"], 3),
            match_reasons=item["reasons"] or ["Competitive overall supplier profile"],
            reliability_score=item["supplier"].reliability_score,
            avg_delivery_days=item["supplier"].average_delivery_time,
            shipping_cost_usd_per_kg=item["shipping_cost"],
            avg_shipping_days=item["shipping_days"],
            risk_level=item["risk_level"],
        )
        for i, item in enumerate(top)
    ]

    mat_str = ", ".join(raw_materials) if raw_materials else "your specified materials"
    summary = (
        f"Based on your raw material needs ({mat_str}) and "
        + (f"preferred source countries ({', '.join(preferred)}), " if preferred else "")
        + f"we recommend {len(recommendations)} suppliers. "
        f"Top pick: {recommendations[0].supplier_name} ({recommendations[0].country}) "
        f"with a match score of {recommendations[0].match_score:.2f}."
        if recommendations else "No supplier recommendations available yet."
    )

    return RecommendationResponse(
        raw_materials=raw_materials,
        preferred_countries=preferred,
        recommendations=recommendations,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# GET /api/suppliers/{supplier_id}/analyze   — CORE ENDPOINT (paper Fig. 2)
# ---------------------------------------------------------------------------

@router.get("/suppliers/{supplier_id}/analyze", response_model=AnalyzeSupplierResponse)
async def analyze_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Multi-agent procurement risk analysis for a specific supplier.

    Pipeline (paper §III, Fig. 2):
      1. Collect internal schedules → compute Delay_i (Eq. 1), SPI, SV
      2. Compute R_i^schedule (Eq. 2)
      3. Fetch external signals → GDELT + World Bank WGI → R_i^external
      4. Run 3 independent agents
      5. Ensemble aggregate → R_i = (1/N) Σ R_ij  (Eq. 3)
      6. Compute CV for uncertainty flagging      (Eq. 4)
      7. Generate LLM summary (if GEMINI_API_KEY set) or heuristic fallback
    """

    # -- Fetch supplier -------------------------------------------------------
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # -- Internal data: equipment schedules -----------------------------------
    supplier_schedules = db.query(EquipmentSchedule).filter(
        EquipmentSchedule.supplier_id == supplier_id
    ).all()

    if not supplier_schedules:
        # No data — return minimal safe response
        empty_agents = [
            agent_schedule(0, 1.0, 0.0),
            agent_geopolitical(5.0, "No data", 0.5),
            agent_supplier_reliability(supplier.reliability_score, supplier.average_delivery_time, 0, 0),
        ]
        ens = ensemble_aggregate(empty_agents)
        return AnalyzeSupplierResponse(
            supplier_id=supplier.id,
            supplier_name=supplier.supplier_name,
            country=supplier.country,
            schedule=ScheduleMetrics(
                avg_delay_days=0, delay_percent=0, risk_level="low",
                r_schedule=0, spi=1.0, sv_days=0,
                disruption_threshold_days=DISRUPTION_THRESHOLD_DAYS,
            ),
            costImpact=CostImpact(currency="USD", estimated_cost=0),
            agent_scores=[AgentResult(**a) for a in empty_agents],
            ensemble=EnsembleResult(**ens),
            geoRisk=None,
            alternatives=[],
            summary=f"No equipment schedule data available for {supplier.supplier_name}.",
            confidence="low",
        )

    # -- Eq (1): Delay_i = ForecastDate_i - PlannedDate_i --------------------
    total_count = len(supplier_schedules)
    delayed_schedules = [s for s in supplier_schedules if s.status == "delayed"]
    delayed_count = len(delayed_schedules)
    delay_percent = round((delayed_count / total_count * 100) if total_count > 0 else 0, 1)

    total_delay_days = 0.0
    for s in delayed_schedules:
        if s.actual_delivery_date and s.planned_delivery_date:
            # Eq (1): Delay_i = ForecastDate_i - PlannedDate_i
            total_delay_days += (s.actual_delivery_date - s.planned_delivery_date).days
        elif not s.actual_delivery_date and s.planned_delivery_date:
            overdue = (date_type.today() - s.planned_delivery_date).days
            if overdue > 0:
                total_delay_days += overdue

    avg_delay_days = round(total_delay_days / delayed_count if delayed_count > 0 else 0, 1)

    # -- Eq (2): R_i^schedule = min(1, Delay_i / T) --------------------------
    r_schedule = compute_r_schedule(avg_delay_days)
    spi = compute_spi(avg_delay_days, supplier.average_delivery_time)
    sv_days = compute_sv_days(avg_delay_days)

    # Risk level label
    if r_schedule >= 0.67:
        risk_level = "high"
    elif r_schedule >= 0.33:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Cost impact
    cost_impact = sum(s.equipment_value for s in delayed_schedules)

    # -- External data: World Bank WGI + GDELT + DB ---------------------------
    # Try World Bank WGI first (most citable for report)
    wgi_score = fetch_wgi_risk_score(supplier.country)

    # Fall back to DB value if WGI unavailable
    country_risk_db = db.query(CountryRisk).filter(
        CountryRisk.country.ilike(supplier.country)
    ).first()

    if wgi_score is not None:
        country_risk_score = wgi_score
        data_source = "world_bank_wgi"
    elif country_risk_db:
        country_risk_score = country_risk_db.risk_score
        data_source = "database"
    else:
        country_risk_score = 5.0  # neutral default
        data_source = "default"

    r_external = round(min(1.0, max(0.0, country_risk_score / 10.0)), 4)

    # GDELT — live geopolitical event headlines
    gdelt_data = fetch_gdelt_events(supplier.country)

    # Determine headline: prefer fresh GDELT, fallback to DB
    if gdelt_data["headline"] and not gdelt_data["headline"].startswith("No recent"):
        headline = gdelt_data["headline"]
        source_url = gdelt_data["source_url"]
    elif country_risk_db:
        headline = country_risk_db.headline
        source_url = country_risk_db.source_url or ""
    else:
        headline = f"No recent risk events recorded for {supplier.country}"
        source_url = "https://www.gdeltproject.org/"

    geo_risk = GeoRiskSignal(
        headline=headline,
        source_url=source_url,
        r_external=r_external,
        risk_score_raw=country_risk_score,
        gdelt_event_count=gdelt_data["count"],
        data_source=data_source,
    )

    # -- Multi-agent risk assessment (paper §III) -----------------------------
    a1 = agent_schedule(avg_delay_days, spi, r_schedule)
    a2 = agent_geopolitical(country_risk_score, headline, r_external, gdelt_data["count"])
    a3 = agent_supplier_reliability(
        supplier.reliability_score,
        supplier.average_delivery_time,
        avg_delay_days,
        delay_percent,
    )
    all_agents = [a1, a2, a3]

    # -- Eq (3) + Eq (4): Ensemble aggregate ----------------------------------
    ens = ensemble_aggregate(all_agents)

    # -- Summary: LLM if key present, heuristic fallback ----------------------
    llm_text = llm_summarize(supplier.supplier_name, supplier.country, all_agents, ens)

    if llm_text:
        summary = llm_text
    else:
        summary = (
            f"Analysis of {supplier.supplier_name} ({supplier.country}): "
            f"{delayed_count}/{total_count} equipment items delayed ({delay_percent}%), "
            f"avg delay {avg_delay_days} days. "
            f"Ensemble risk score {ens['final_score']:.3f} "
            f"(confidence: {ens['confidence']}, CV={ens['coefficient_of_variation']:.3f}). "
            f"Cost impact: ${cost_impact:,.2f}. "
            f"Country risk {country_risk_score:.1f}/10 [{data_source}]. "
            + (f"⚠ High agent disagreement — review manually." if ens["high_uncertainty"] else "Agents in agreement.")
        )

    # -- Alternative supplier recommendations ----------------------------------
    # Prefer same-industry alternatives; pad with best overall if not enough
    same_industry_alts = []
    if supplier.industry:
        same_industry_alts = (
            db.query(Supplier)
            .filter(
                Supplier.id != supplier_id,
                Supplier.industry == supplier.industry,
                Supplier.reliability_score >= supplier.reliability_score - 5,
            )
            .order_by(Supplier.reliability_score.desc())
            .limit(3)
            .all()
        )

    already_ids = {s.id for s in same_industry_alts}
    if len(same_industry_alts) < 3:
        remaining = 3 - len(same_industry_alts)
        fallback_alts = (
            db.query(Supplier)
            .filter(
                Supplier.id != supplier_id,
                Supplier.reliability_score > supplier.reliability_score,
                ~Supplier.id.in_(already_ids),
            )
            .order_by(Supplier.reliability_score.desc())
            .limit(remaining)
            .all()
        )
    else:
        fallback_alts = []

    alt_data = same_industry_alts + fallback_alts

    alternatives = [
        AlternativeSupplier(
            id=s.id,
            name=s.supplier_name,
            country=s.country,
            score=s.reliability_score,
            industry=s.industry,
            same_industry=(s.id in already_ids),
        )
        for s in alt_data
    ]

    return AnalyzeSupplierResponse(
        supplier_id=supplier.id,
        supplier_name=supplier.supplier_name,
        country=supplier.country,
        schedule=ScheduleMetrics(
            avg_delay_days=avg_delay_days,
            delay_percent=delay_percent,
            risk_level=risk_level,
            r_schedule=r_schedule,
            spi=spi,
            sv_days=sv_days,
            disruption_threshold_days=DISRUPTION_THRESHOLD_DAYS,
        ),
        costImpact=CostImpact(currency="USD", estimated_cost=cost_impact),
        agent_scores=[AgentResult(**a) for a in all_agents],
        ensemble=EnsembleResult(**ens),
        geoRisk=geo_risk,
        alternatives=alternatives,
        summary=summary,
        confidence=ens["confidence"],
    )


# ---------------------------------------------------------------------------
# POST /api/analyze  — global analysis across all suppliers
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_supply_chain(db: Session = Depends(get_db)):
    """Global supply chain risk analysis across all suppliers."""
    all_schedules = db.query(EquipmentSchedule).all()
    total_equipment_count = len(all_schedules)

    delayed_schedules = [s for s in all_schedules if s.status == "delayed"]
    delayed_count = len(delayed_schedules)
    cost_impact = sum(s.equipment_value for s in delayed_schedules)

    if delayed_count == 0:
        schedule_risk = "low"
    elif delayed_count / total_equipment_count < 0.3:
        schedule_risk = "medium"
    else:
        schedule_risk = "high"

    high_risk_countries_data = db.query(CountryRisk).filter(CountryRisk.risk_score >= 7.0).all()
    high_risk_countries = [r.country for r in high_risk_countries_data]

    delayed_supplier_ids = list(set(s.supplier_id for s in delayed_schedules))

    alt_data = db.query(Supplier).filter(
        Supplier.reliability_score >= 80.0,
        ~Supplier.country.in_(high_risk_countries),
        ~Supplier.id.in_(delayed_supplier_ids),
    ).order_by(Supplier.reliability_score.desc()).limit(3).all()

    alternative_suppliers = [
        AlternativeSupplierLegacy(
            supplier_name=s.supplier_name,
            country=s.country,
            reliability_score=s.reliability_score,
            average_delivery_time=s.average_delivery_time,
            cost_competitiveness=s.cost_competitiveness,
            reason=(
                f"High reliability ({s.reliability_score}%), "
                f"{s.average_delivery_time}-day delivery, located in {s.country}"
            ),
        )
        for s in alt_data
    ]

    executive_summary = (
        f"Global supply chain analysis: {schedule_risk.upper()} risk. "
        f"{delayed_count}/{total_equipment_count} items delayed, "
        f"cost impact ${cost_impact:,.2f}. "
    )
    if high_risk_countries:
        executive_summary += f"High-risk countries: {', '.join(high_risk_countries)}. "
    if alternative_suppliers:
        avg_rel = sum(s.reliability_score for s in alt_data) / len(alt_data)
        executive_summary += (
            f"{len(alternative_suppliers)} alternative suppliers available "
            f"(avg reliability {avg_rel:.1f}%)."
        )

    return RiskAnalysisResponse(
        schedule_risk=schedule_risk,
        delayed_equipment_count=delayed_count,
        total_equipment_count=total_equipment_count,
        cost_impact=cost_impact,
        high_risk_countries=high_risk_countries,
        alternative_suppliers=alternative_suppliers,
        executive_summary=executive_summary,
    )


# ---------------------------------------------------------------------------
# Read-only data endpoints
# ---------------------------------------------------------------------------

@router.get("/equipment-schedule")
async def get_equipment_schedule(db: Session = Depends(get_db)):
    schedules = db.query(EquipmentSchedule).all()
    return {
        "equipment_schedules": [
            {
                "id": e.id,
                "equipment_name": e.equipment_name,
                "supplier_id": e.supplier_id,
                "planned_delivery_date": e.planned_delivery_date.isoformat() if e.planned_delivery_date else None,
                "actual_delivery_date": e.actual_delivery_date.isoformat() if e.actual_delivery_date else None,
                "equipment_value": e.equipment_value,
                "status": e.status,
            }
            for e in schedules
        ],
        "count": len(schedules),
    }


@router.get("/country-risk")
async def get_country_risks(db: Session = Depends(get_db)):
    risks = db.query(CountryRisk).all()
    return {
        "country_risks": [
            {
                "id": r.id,
                "country": r.country,
                "risk_score": r.risk_score,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "headline": r.headline,
                "source_url": r.source_url,
            }
            for r in risks
        ],
        "count": len(risks),
    }


@router.get("/country-risk/{country}")
async def get_country_risk(country: str, db: Session = Depends(get_db)):
    risk = db.query(CountryRisk).filter(CountryRisk.country.ilike(country)).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Country risk not found")
    return {
        "id": risk.id,
        "country": risk.country,
        "risk_score": risk.risk_score,
        "last_updated": risk.last_updated.isoformat() if risk.last_updated else None,
        "headline": risk.headline,
        "source_url": risk.source_url,
    }



@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_supply_chain(db: Session = Depends(get_db)):
    """
    POST /api/analyze - Comprehensive supply chain risk analysis
    
    Analyzes:
    - Schedule risks based on delayed equipment
    - Cost impact from delays
    - Country-level risks
    - Alternative supplier recommendations
    """
    
    # Get all equipment schedules
    all_schedules = db.query(EquipmentSchedule).all()
    total_equipment_count = len(all_schedules)
    
    # Identify delayed equipment
    delayed_schedules = [s for s in all_schedules if s.status == "delayed"]
    delayed_count = len(delayed_schedules)
    
    # Calculate cost impact (sum of delayed equipment values)
    cost_impact = sum(s.equipment_value for s in delayed_schedules)
    
    # Determine schedule risk level
    if delayed_count == 0:
        schedule_risk = "low"
    elif delayed_count / total_equipment_count < 0.3:
        schedule_risk = "medium"
    else:
        schedule_risk = "high"
    
    # Get high-risk countries (risk_score >= 7)
    high_risk_countries_data = db.query(CountryRisk).filter(CountryRisk.risk_score >= 7.0).all()
    high_risk_countries = [r.country for r in high_risk_countries_data]
    
    # Get suppliers from delayed equipment
    delayed_supplier_ids = list(set(s.supplier_id for s in delayed_schedules))
    
    # Find alternative suppliers (high reliability, not in high-risk countries, not currently delayed)
    alternative_suppliers_data = db.query(Supplier).filter(
        Supplier.reliability_score >= 80.0,
        ~Supplier.country.in_(high_risk_countries),
        ~Supplier.id.in_(delayed_supplier_ids)
    ).order_by(Supplier.reliability_score.desc()).limit(3).all()
    
    alternative_suppliers = [
        AlternativeSupplier(
            supplier_name=s.supplier_name,
            country=s.country,
            reliability_score=s.reliability_score,
            average_delivery_time=s.average_delivery_time,
            cost_competitiveness=s.cost_competitiveness,
            reason=f"High reliability ({s.reliability_score}%), {s.average_delivery_time}-day delivery, located in {s.country}"
        )
        for s in alternative_suppliers_data
    ]
    
    # Generate executive summary
    executive_summary = (
        f"Supply chain analysis reveals {schedule_risk.upper()} risk level. "
        f"{delayed_count} out of {total_equipment_count} equipment items are delayed, "
        f"resulting in ${cost_impact:,.2f} in potential cost impact. "
    )
    
    if high_risk_countries:
        executive_summary += f"High-risk countries identified: {', '.join(high_risk_countries)}. "
    
    if alternative_suppliers:
        executive_summary += (
            f"Recommended diversification to {len(alternative_suppliers)} alternative suppliers "
            f"with average reliability score of {sum(s.reliability_score for s in alternative_suppliers_data) / len(alternative_suppliers_data):.1f}%."
        )
    else:
        executive_summary += "No alternative suppliers currently available meeting criteria."
    
    return RiskAnalysisResponse(
        schedule_risk=schedule_risk,
        delayed_equipment_count=delayed_count,
        total_equipment_count=total_equipment_count,
        cost_impact=cost_impact,
        high_risk_countries=high_risk_countries,
        alternative_suppliers=alternative_suppliers,
        executive_summary=executive_summary
    )


@router.get("/suppliers")
async def get_suppliers(db: Session = Depends(get_db)):
    """
    GET /api/suppliers - Returns all suppliers with their details
    """
    suppliers = db.query(Supplier).all()
    return {
        "suppliers": [
            {
                "id": s.id,
                "supplier_name": s.supplier_name,
                "country": s.country,
                "reliability_score": s.reliability_score,
                "average_delivery_time": s.average_delivery_time,
                "cost_competitiveness": s.cost_competitiveness
            }
            for s in suppliers
        ],
        "count": len(suppliers)
    }


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """
    GET /api/suppliers/{id} - Returns a specific supplier
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {
        "id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "country": supplier.country,
        "reliability_score": supplier.reliability_score,
        "average_delivery_time": supplier.average_delivery_time,
        "cost_competitiveness": supplier.cost_competitiveness
    }


# Duplicate route removed — auth-gated version is defined above
@router.get("/suppliers/{supplier_id}/analyze-legacy-disabled", include_in_schema=False)
async def _disabled_legacy_analyze(supplier_id: int):
    raise HTTPException(status_code=404, detail="Not found")

def _unused_placeholder():
    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get all equipment schedules for this supplier
    supplier_schedules = db.query(EquipmentSchedule).filter(
        EquipmentSchedule.supplier_id == supplier_id
    ).all()
    
    if not supplier_schedules:
        # No equipment data for this supplier
        return {
            "schedule": {
                "avg_delay_days": 0,
                "delay_percent": 0,
                "risk_level": "low"
            },
            "costImpact": {
                "currency": "USD",
                "estimated_cost": 0
            },
            "alternatives": [],
            "summary": f"No equipment data available for {supplier.supplier_name}.",
            "geoRisk": None
        }
    
    # Calculate delay statistics
    delayed_schedules = [s for s in supplier_schedules if s.status == "delayed"]
    total_count = len(supplier_schedules)
    delayed_count = len(delayed_schedules)
    delay_percent = (delayed_count / total_count * 100) if total_count > 0 else 0
    
    # Calculate average delay in days
    total_delay_days = 0
    for schedule in delayed_schedules:
        if schedule.actual_delivery_date and schedule.planned_delivery_date:
            delay_days = (schedule.actual_delivery_date - schedule.planned_delivery_date).days
            total_delay_days += delay_days
        elif not schedule.actual_delivery_date:
            # For items not yet delivered, estimate delay based on today's date
            from datetime import date as date_type
            estimated_delay = (date_type.today() - schedule.planned_delivery_date).days
            if estimated_delay > 0:
                total_delay_days += estimated_delay
    
    avg_delay_days = total_delay_days / delayed_count if delayed_count > 0 else 0
    
    # Determine risk level
    if delay_percent >= 50:
        risk_level = "high"
    elif delay_percent >= 20:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Calculate cost impact
    cost_impact = sum(s.equipment_value for s in delayed_schedules)
    
    # Get country risk for supplier's country
    country_risk = db.query(CountryRisk).filter(
        CountryRisk.country.ilike(supplier.country)
    ).first()
    
    geo_risk = None
    if country_risk:
        geo_risk = {
            "headline": country_risk.headline,
            "source_url": country_risk.source_url
        }
    
    # Find alternative suppliers (better reliability, different country, not the current one)
    alternative_suppliers_data = db.query(Supplier).filter(
        Supplier.id != supplier_id,
        Supplier.reliability_score > supplier.reliability_score,
    ).order_by(Supplier.reliability_score.desc()).limit(3).all()
    
    alternatives = [
        {
            "id": s.id,
            "name": s.supplier_name,
            "country": s.country,
            "score": s.reliability_score
        }
        for s in alternative_suppliers_data
    ]
    
    # Generate summary
    summary = (
        f"Analysis of {supplier.supplier_name} ({supplier.country}): "
        f"{delayed_count} of {total_count} equipment items are delayed "
        f"({delay_percent:.1f}%), with an average delay of {avg_delay_days:.1f} days. "
        f"Total cost impact: ${cost_impact:,.2f}. "
    )
    
    if country_risk and country_risk.risk_score >= 7.0:
        summary += f"Country risk is HIGH ({country_risk.risk_score}/10). "
    
    if alternatives:
        summary += f"Found {len(alternatives)} alternative suppliers with better reliability scores."
    else:
        summary += "No better alternatives found at this time."
    
    return {
        "schedule": {
            "avg_delay_days": round(avg_delay_days, 1),
            "delay_percent": round(delay_percent, 1),
            "risk_level": risk_level
        },
        "costImpact": {
            "currency": "USD",
            "estimated_cost": cost_impact
        },
        "alternatives": alternatives,
        "summary": summary,
        "geoRisk": geo_risk
    }



@router.get("/equipment-schedule")
async def get_equipment_schedule(db: Session = Depends(get_db)):
    """
    GET /api/equipment-schedule - Returns all equipment schedules
    """
    schedules = db.query(EquipmentSchedule).all()
    return {
        "equipment_schedules": [
            {
                "id": e.id,
                "equipment_name": e.equipment_name,
                "supplier_id": e.supplier_id,
                "planned_delivery_date": e.planned_delivery_date.isoformat() if e.planned_delivery_date else None,
                "actual_delivery_date": e.actual_delivery_date.isoformat() if e.actual_delivery_date else None,
                "equipment_value": e.equipment_value,
                "status": e.status
            }
            for e in schedules
        ],
        "count": len(schedules)
    }


@router.get("/country-risk")
async def get_country_risks(db: Session = Depends(get_db)):
    """
    GET /api/country-risk - Returns all country risk assessments
    """
    risks = db.query(CountryRisk).all()
    return {
        "country_risks": [
            {
                "id": r.id,
                "country": r.country,
                "risk_score": r.risk_score,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "headline": r.headline,
                "source_url": r.source_url
            }
            for r in risks
        ],
        "count": len(risks)
    }


@router.get("/country-risk/{country}")
async def get_country_risk(country: str, db: Session = Depends(get_db)):
    """
    GET /api/country-risk/{country} - Returns risk for a specific country
    """
    risk = db.query(CountryRisk).filter(CountryRisk.country.ilike(country)).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Country risk not found")
    return {
        "id": risk.id,
        "country": risk.country,
        "risk_score": risk.risk_score,
        "last_updated": risk.last_updated.isoformat() if risk.last_updated else None,
        "headline": risk.headline,
        "source_url": risk.source_url
    }

# ---------------------------------------------------------------------------
# POST /api/refresh-risk
# ---------------------------------------------------------------------------

@router.post("/refresh-risk")
async def refresh_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    POST /api/refresh-risk - Live-refreshes CountryRisk from World Bank WGI + GDELT.
    Requires authentication. Returns per-country update summary.
    """
    from datetime import datetime

    risks = db.query(CountryRisk).all()
    if not risks:
        raise HTTPException(status_code=404, detail="No country risk records found. Run refresh_data.py first.")

    updated = []
    skipped = []

    for risk in risks:
        country = risk.country

        # --- World Bank WGI political stability ---
        new_score = fetch_wgi_risk_score(country)
        if new_score is None:
            skipped.append({"country": country, "reason": "WGI fetch failed"})
            continue

        # --- GDELT headline ---
        gdelt = fetch_gdelt_events(country, max_records=5)
        headline = gdelt.get("headline", risk.headline or "")
        source_url = gdelt.get("source_url", risk.source_url or "")

        risk.risk_score = new_score
        risk.headline = headline
        risk.source_url = source_url
        risk.last_updated = datetime.utcnow()

        updated.append({
            "country": country,
            "risk_score": new_score,
            "headline": headline[:120] if headline else "",
        })

    db.commit()

    return {
        "status": "ok",
        "updated": len(updated),
        "skipped": len(skipped),
        "results": updated,
        "skipped_details": skipped,
    }