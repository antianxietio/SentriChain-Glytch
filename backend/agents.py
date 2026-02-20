"""
Multi-agent risk assessment module.

Implements the multi-agent ensemble architecture from the paper:
  - N independent agents each produce R_ij ∈ [0, 1]
  - Ensemble: R_i = (1/N) * Σ R_ij   ... Eq (3)
  - Uncertainty: CV = std(R_ij) / mean(R_ij)  ... Eq (4)

Agents:
  1. ScheduleVarianceAgent  — internal EVM metrics, Eq (1)(2)
  2. GeopoliticalSignalAgent — external country risk, R_i^external
  3. SupplierReliabilityAgent — historical delivery performance
"""

import os
import statistics
from typing import Optional

# Disruption threshold T in days (configurable via .env)
DISRUPTION_THRESHOLD_DAYS = float(os.getenv("DISRUPTION_THRESHOLD_DAYS", "30"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# Eq (1): Delay_i = ForecastDate_i - PlannedDate_i  (computed upstream)
# Eq (2): R_i^schedule = min(1, Delay_i / T)
# ---------------------------------------------------------------------------

def compute_r_schedule(delay_days: float, threshold: float = DISRUPTION_THRESHOLD_DAYS) -> float:
    """Paper Eq (2): normalized schedule risk score ∈ [0, 1]."""
    return round(min(1.0, max(0.0, delay_days / threshold)), 4)


def compute_spi(delay_days: float, planned_duration_days: int) -> float:
    """
    Schedule Performance Index (EVM).
    SPI = PlannedDuration / (PlannedDuration + max(0, Delay))
    SPI < 1.0 means behind schedule.
    """
    if planned_duration_days <= 0:
        return 1.0
    return round(planned_duration_days / (planned_duration_days + max(0.0, delay_days)), 4)


def compute_sv_days(delay_days: float) -> float:
    """Schedule Variance in days (negative = behind schedule)."""
    return round(-delay_days, 2)


# ---------------------------------------------------------------------------
# Agent 1: Schedule Variance Agent
# ---------------------------------------------------------------------------

def agent_schedule(delay_days: float, spi: float, r_schedule: float) -> dict:
    """
    Agent 1 — ScheduleVarianceAgent.
    Uses internal EVM data: Delay_i and SPI.
    Score = 0.7 * R_schedule + 0.3 * SPI_risk
    """
    spi_risk = round(max(0.0, min(1.0, 1.0 - spi)), 4)
    score = round((r_schedule * 0.7) + (spi_risk * 0.3), 4)

    if delay_days <= 0:
        reasoning = (
            f"No delay detected. R_schedule=0.000 (T={DISRUPTION_THRESHOLD_DAYS:.0f}d). "
            f"SPI={spi:.3f} — on schedule."
        )
    else:
        reasoning = (
            f"Delay of {delay_days:.1f} days → R_schedule={r_schedule:.3f} "
            f"(T={DISRUPTION_THRESHOLD_DAYS:.0f}d). SPI={spi:.3f} "
            f"→ SPI-risk={spi_risk:.3f}. Weighted score={score:.3f}."
        )

    return {
        "agent": "ScheduleVarianceAgent",
        "score": score,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Agent 2: Geopolitical Signal Agent
# ---------------------------------------------------------------------------

def agent_geopolitical(
    country_risk_score: float,
    headline: str,
    r_external: float,
    gdelt_event_count: int = 0,
) -> dict:
    """
    Agent 2 — GeopoliticalSignalAgent.
    Uses external country risk + GDELT event signal.
    R_i^external ∈ [0, 1] from World Bank WGI / GDELT.
    """
    # GDELT amplifier: more recent events → slightly higher risk
    gdelt_boost = min(0.1, gdelt_event_count * 0.01)
    score = round(min(1.0, r_external + gdelt_boost), 4)

    short_headline = headline[:100] + "..." if len(headline) > 100 else headline
    reasoning = (
        f"Country risk score {country_risk_score:.1f}/10 → R_external={r_external:.3f}. "
        f"GDELT recent events: {gdelt_event_count} → boost +{gdelt_boost:.3f}. "
        f"Latest signal: '{short_headline}'"
    )

    return {
        "agent": "GeopoliticalSignalAgent",
        "score": score,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Agent 3: Supplier Reliability Agent
# ---------------------------------------------------------------------------

def agent_supplier_reliability(
    reliability_score: float,
    avg_delivery_time: int,
    delay_days: float,
    delay_percent: float,
) -> dict:
    """
    Agent 3 — SupplierReliabilityAgent.
    Uses historical supplier performance metrics.
    """
    reliability_risk = round(1.0 - (reliability_score / 100.0), 4)
    delivery_ratio = round(
        min(1.0, delay_days / avg_delivery_time) if avg_delivery_time > 0 else 0.0, 4
    )
    delay_freq_risk = round(min(1.0, delay_percent / 100.0), 4)

    score = round(
        (reliability_risk * 0.4) + (delivery_ratio * 0.3) + (delay_freq_risk * 0.3), 4
    )

    reasoning = (
        f"Reliability {reliability_score:.1f}% → reliability-risk={reliability_risk:.3f}. "
        f"Delay/avg_delivery_time ratio={delivery_ratio:.3f}. "
        f"Delay frequency {delay_percent:.1f}% → freq-risk={delay_freq_risk:.3f}. "
        f"Weighted score={score:.3f}."
    )

    return {
        "agent": "SupplierReliabilityAgent",
        "score": score,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Ensemble Aggregation — Eq (3) and Eq (4)
# ---------------------------------------------------------------------------

def ensemble_aggregate(agents: list[dict]) -> dict:
    """
    Paper Eq (3): R_i = (1/N) * Σ R_ij
    Paper Eq (4): CV = std(R_ij) / mean(R_ij)  — flags uncertainty
    """
    scores = [a["score"] for a in agents]
    n = len(scores)

    r_i = round(sum(scores) / n, 4)                                # Eq (3)
    cv = round(statistics.stdev(scores) / r_i, 4) if n > 1 and r_i > 0 else 0.0  # Eq (4)
    high_uncertainty = cv > 0.30  # Flag when agents disagree >30%

    # Derive confidence label from CV
    if cv <= 0.15:
        confidence = "high"
    elif cv <= 0.30:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "final_score": r_i,
        "coefficient_of_variation": cv,
        "high_uncertainty": high_uncertainty,
        "confidence": confidence,
        "n_agents": n,
        "individual_scores": {a["agent"]: a["score"] for a in agents},
    }


# ---------------------------------------------------------------------------
# Optional: LLM-powered summary via Gemini
# ---------------------------------------------------------------------------

def llm_summarize(supplier_name: str, country: str, agents: list[dict], ensemble: dict) -> Optional[str]:
    """
    Calls Gemini API to generate a natural language procurement risk summary.
    Falls back to None if GEMINI_API_KEY not set (heuristic summary used instead).
    """
    if not GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        agent_text = "\n".join(
            f"- {a['agent']} (score={a['score']:.3f}): {a['reasoning']}"
            for a in agents
        )

        prompt = f"""You are a procurement risk analyst. Summarize the following multi-agent risk assessment 
for supplier '{supplier_name}' from {country} in 2-3 concise sentences for a procurement manager.
Focus on the most critical risks and actionable recommendations.

Agent assessments:
{agent_text}

Ensemble risk score: {ensemble['final_score']:.3f} (confidence: {ensemble['confidence']}, CV={ensemble['coefficient_of_variation']:.3f})

Write a plain English executive summary:"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return None
