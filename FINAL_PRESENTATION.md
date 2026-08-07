# SentriChain Final Project Presentation (In-Depth)

## 1. Title Slide

**Project:** SentriChain  
**Tagline:** Intelligent Supply Chain Risk Management Platform  
**Team:** [Add team member names]  
**Institution/Event:** [Add college or hackathon name]  
**Date:** April 2026

**One-line pitch:**
SentriChain helps procurement teams predict supplier disruption risk, quantify cost impact, and choose better alternatives using a multi-agent risk engine and real-world country factors.

---

## 2. Agenda

1. Problem and why it matters
2. Our solution
3. Product walkthrough
4. System architecture
5. Multi-agent methodology
6. Data model and APIs
7. Recommendation and personalization engine
8. Security and reliability
9. What we built vs what is next
10. Demo script and Q&A backup

---

## 3. Problem Statement

Global supply chains are increasingly vulnerable to:

- Delivery delays and schedule variance
- Country-level geopolitical and logistics disruptions
- Limited visibility into supplier reliability trends
- Slow decision-making during disruptions

### Pain for businesses

- Late deliveries create project overruns
- Procurement teams react too late
- Alternative sourcing decisions are often ad hoc, not data-driven

### Opportunity

A platform that continuously combines internal schedule data with external country signals can move teams from reactive decisions to proactive risk management.

---

## 4. Solution Overview

SentriChain is a web platform that enables users to:

- Onboard their company profile and sourcing preferences
- Analyze supplier risk with a multi-agent ensemble
- View detailed supplier overview with country factors
- Receive ranked supplier recommendations
- Compare country risk/logistics context
- Export analysis output for downstream reporting

### Core value proposition

- Faster risk visibility
- Explainable scoring (agent-level reasoning)
- Practical alternatives, not just alerts

---

## 5. Product Walkthrough (User Journey)

1. User authenticates and creates company profile
2. User selects company type, raw materials, and preferred countries
3. Dashboard loads suppliers and overview insights
4. User selects a supplier to run analysis
5. System computes schedule, geopolitical, and reliability risk
6. Ensemble score and confidence are generated
7. Alternatives and recommendations are shown
8. User exports analysis JSON for operations or management reporting

---

## 6. System Architecture

## Frontend

- Next.js App Router (TypeScript)
- Dashboard with tabs: Overview, Recommendations, Analysis, Compare
- Client-side history of recent analyses
- Token/session handling for authenticated API calls

## Backend

- FastAPI (Python)
- Modular routers for auth and business APIs
- SQLAlchemy ORM with relational models
- JWT-based auth, onboarding profile, and protected endpoints

## Data Layer

- Supplier master data
- Equipment schedule records
- Country risk and country factor datasets
- User and onboarding preference profiles

## External Intelligence

- GDELT events and country risk enrichment hooks
- Optional Gemini LLM summary generation (fallback supported)

---

## 7. Multi-Agent Risk Methodology

SentriChain uses an ensemble of three specialized agents:

1. **ScheduleVarianceAgent**

- Uses delay and SPI (Schedule Performance Index)
- Captures internal execution variance

2. **GeopoliticalSignalAgent**

- Uses country risk score and event signal amplification
- Captures external disruption pressure

3. **SupplierReliabilityAgent**

- Uses historical supplier reliability and delivery behavior
- Captures vendor consistency over time

### Aggregation approach

- Ensemble final score is the mean of agent scores
- Uncertainty is measured with coefficient of variation (CV)
- Confidence label (high/medium/low) is derived from CV thresholds

### Why this matters

- Better than a single-score heuristic
- Improves robustness by combining independent signals
- Gives transparent, explainable evidence per agent

---

## 8. Risk and Scoring Logic (Technical Depth)

### Schedule normalization

- Delay is normalized against a disruption threshold
- Example concept: higher delay ratio -> higher schedule risk

### Reliability risk

- Converts high reliability percentage to lower risk
- Blends reliability with delay frequency and delay ratio

### Composite recommendation bias

Supplier ranking blends:

- Reliability quality
- Country risk attractiveness
- Shipping efficiency
- Delay behavior
- User preference boosts (country + raw material relevance)

### Explainability output

The API returns:

- Agent-wise scores
- Agent reasoning text
- Ensemble final score
- Confidence and uncertainty flags

---

## 9. Data Model (What We Store)

### Core entities

- User
- UserCompanyProfile (onboarding)
- Supplier
- EquipmentSchedule
- CountryRisk
- CountryFactors

### CountryFactors coverage includes

- Economy indicators
- Tax and tariff indicators
- Logistics and shipping metrics
- Stability and infrastructure indicators

This allows both risk scoring and operationally useful sourcing context.

---

## 10. API Surface (Key Endpoints)

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `POST /auth/onboard`
- `GET /auth/onboard`

### Supply Chain Intelligence

- `GET /api/suppliers`
- `GET /api/suppliers/{supplier_id}`
- `GET /api/suppliers-overview`
- `GET /api/recommend`
- `GET /api/suppliers/{supplier_id}/analyze`

### Platform Health

- `GET /`
- `GET /health`

---

## 11. Personalization Strategy

SentriChain is not a generic dashboard.
Recommendations are personalized using:

- Company type
- Raw materials needed
- Preferred source countries

### Impact

- Improves recommendation relevance
- Supports practical procurement decisions
- Reduces decision latency during disruptions

---

## 12. Security and Operational Readiness

### Security controls

- Password hashing
- JWT access tokens
- Authenticated access for protected routes
- Profile-bound recommendation and analysis context

### Reliability controls

- Session refresh flow on token expiry
- API health checks
- Graceful fallback when LLM key is unavailable

### Production readiness note

- Development uses SQLite
- Architecture is portable to PostgreSQL/Azure SQL

---

## 13. What We Built vs Roadmap

## Delivered now

- End-to-end auth + onboarding
- Supplier overview and country context
- Multi-agent risk analysis with confidence
- Personalized recommendations
- Exportable analysis artifacts
- Compare-country intelligence view in dashboard

## Next milestones

- Real-time event stream ingestion
- Alerting channels (email/WhatsApp)
- Scenario simulation (what-if procurement planning)
- Model calibration with historical outcomes
- Role-based enterprise controls and audit trail

---

## 14. Demo Script (5-7 Minutes)

1. **Login/Onboard (45 sec)**

- Show company profile setup and sourcing preferences

2. **Overview tab (60 sec)**

- Show supplier list, country factors, and sorting rationale

3. **Run supplier analysis (90 sec)**

- Select one supplier
- Explain agent scores + ensemble confidence
- Show cost impact and summary output

4. **Recommendations tab (60 sec)**

- Show top ranked alternatives and reasons
- Highlight personalization effect

5. **Compare tab (45 sec)**

- Compare country-level sourcing characteristics

6. **Export + close (30 sec)**

- Export analysis JSON
- Reiterate business value and next steps

---

## 15. Judge-Focused Talking Points

- We solve a real procurement risk problem with a practical workflow, not only a prediction score.
- Our model is explainable: each agent gives interpretable reasoning.
- We combine internal operational metrics with external geopolitical/logistics signals.
- Recommendations are personalized to the buyer profile, making outputs actionable.
- The stack is production-oriented and extensible.

---

## 16. Potential Questions and Strong Answers

### Q1: Why multi-agent instead of one model?

A: Different risk sources behave differently. Specialized agents improve explainability and resilience, then ensemble aggregation stabilizes the final score.

### Q2: How do you handle uncertainty?

A: We compute coefficient of variation across agent scores and convert it to confidence labels. High disagreement is explicitly flagged.

### Q3: Is this deployable beyond hackathon scope?

A: Yes. The API/data architecture is modular. SQLite can be swapped for PostgreSQL/Azure SQL, and external signal ingestion can be scaled.

### Q4: What if LLM integration fails?

A: Summaries gracefully fall back to deterministic heuristic text so core decision support continues.

---

## 17. Business Impact Framing

If adopted by procurement teams, SentriChain can help:

- Reduce disruption response time
- Improve sourcing diversification quality
- Increase transparency in supplier decision-making
- Support data-backed executive communication

Use this wording carefully in presentation:
"Expected impact" or "potential impact" unless validated by production KPI studies.

---

## 18. Closing Slide

**SentriChain:** From supply chain uncertainty to actionable intelligence.

Thank you.  
Questions?

---

## Appendix A: 60-Second Elevator Pitch

SentriChain is an intelligent supply chain risk platform that helps teams detect supplier disruption risk early and act quickly. It combines three specialized agents for schedule, geopolitical, and reliability risk, then produces an explainable ensemble score with confidence. On top of that, it personalizes supplier recommendations using company type, raw materials, and preferred sourcing countries. The result is faster, better procurement decisions with clear operational context.

---

## Appendix B: Slide Design Suggestions

- Keep each section above as one slide
- Use architecture diagram with 4 lanes: UI, API, Data, Intelligence
- Show one real supplier analysis screenshot for credibility
- Use one chart for agent scores and one gauge for ensemble confidence
- Keep text minimal on slides; use this file as speaker notes

---

## Appendix C: Presenter Checklist

- Backend running on port 8000
- Frontend running on port 3000
- Seed/demo data present
- At least one user account ready
- At least one analyzed supplier in history for backup
- Internet available if external signals are live
- Optional: GEMINI_API_KEY configured for AI summary demo
