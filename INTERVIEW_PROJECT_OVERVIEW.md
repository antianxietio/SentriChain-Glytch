# SentriChain Project Overview (Interview Prep)

## 1) What this project is
SentriChain is an AI-assisted supply chain risk intelligence platform built for procurement and operations teams. It helps users identify supplier risk, estimate cost impact from delays, and evaluate safer alternatives using both internal operational data and external geopolitical signals.

This repository contains a full-stack implementation with:
- **Frontend:** Next.js 16 + React 19 dashboard
- **Backend:** FastAPI service with JWT authentication
- **Database:** SQLAlchemy models over SQLite (development)
- **Risk Engine:** Multi-agent scoring + ensemble aggregation

---

## 2) Problem it solves
Modern supply chains fail when teams rely only on static supplier scorecards or delayed reporting. SentriChain addresses this by combining:
- Delivery/schedule performance data
- Supplier reliability history
- Country-level risk indicators and live event signals

The output is a practical risk score with confidence and an executive summary, so decisions can be made quickly.

---

## 3) Core architecture
At a high level, the system follows this flow:
1. User authenticates and completes onboarding profile (industry, raw materials, preferred countries).
2. Frontend requests supplier data and analysis from FastAPI endpoints.
3. Backend computes risk using three specialized agents:
   - **ScheduleVarianceAgent** (delay and EVM metrics)
   - **GeopoliticalSignalAgent** (country risk + GDELT event activity)
   - **SupplierReliabilityAgent** (historical performance)
4. Agent outputs are combined by an ensemble function into a final risk score and uncertainty/confidence label.
5. API returns risk details, alternatives, and a manager-friendly summary.

External integrations are wired through utility functions and architecture docs for sources like **World Bank WGI**, **GDELT**, and optional **Gemini** summarization.

---

## 4) Backend highlights (what interviewers usually ask)

### API and auth
- FastAPI app entry point: `backend/main.py`
- JWT auth utilities: `backend/auth.py`
- Auth endpoints: register/login/me/profile update/onboarding in `backend/routers/auth_router.py`

### Main business endpoints
Under `/api` (defined in `backend/routers/__init__.py`), key endpoints include:
- `GET /api/suppliers`
- `GET /api/suppliers/{supplier_id}`
- `GET /api/suppliers-overview` (auth required)
- `GET /api/recommend` (auth + onboarding-aware)
- `GET /api/suppliers/{supplier_id}/analyze` (core multi-agent analysis)
- `POST /api/analyze` (global analysis)
- `POST /api/refresh-risk` (refresh country risk signals)

### Data model
Important entities in `backend/models/__init__.py`:
- `User`, `UserCompanyProfile`
- `Supplier`, `EquipmentSchedule`
- `CountryRisk`, `CountryFactors`

These support identity, onboarding personalization, supplier operations, and country intelligence.

### Risk computation design
In `backend/agents.py`, the risk engine implements:
- Normalized schedule risk
- Agent-level explainable scores
- Ensemble averaging and coefficient-of-variation uncertainty logic
- Optional LLM summary fallback behavior when API keys are absent

This gives both numerical scoring and explainability.

---

## 5) Frontend highlights
The frontend is a Next.js App Router app with major pages such as:
- `app/onboard/page.tsx` — onboarding wizard (industry/material/country preferences)
- `app/dashboard/page.tsx` — core workspace (overview, recommendations, analysis, compare/history)
- `app/profile/page.tsx` — user profile and credential updates

The dashboard UX emphasizes decision support:
- Supplier-level analysis
- Risk cards and summary views
- Personalized recommendations based on onboarding profile
- Local history for quick comparison

---

## 6) Why this is strong for interviews
This project demonstrates:
- **Product thinking:** clear business problem and user workflow
- **Full-stack capability:** frontend + backend + data modeling
- **Applied AI architecture:** multi-agent scoring with confidence handling
- **Security basics:** JWT auth, password hashing, protected endpoints
- **Practical explainability:** combines quantitative scores with natural-language summaries

It is especially strong for roles in backend engineering, applied AI systems, or data-driven product development.

---

## 7) Known talking points / tradeoffs
When discussing honestly in interviews:
- SQLite is suitable for development; production would move to Postgres/Azure SQL.
- Some route definitions in `backend/routers/__init__.py` appear duplicated, indicating refactor debt from rapid iteration.
- External signal quality depends on upstream source availability and refresh cadence.
- LLM summary is optional and should be governed by cost/latency and prompt controls in production.

Calling out tradeoffs proactively usually strengthens technical interviews.

---

## 8) 30-second interview pitch
“SentriChain is a full-stack AI-assisted supply chain risk platform. We ingest supplier performance and schedule data, enrich it with geopolitical and logistics signals, then run a three-agent risk ensemble to produce a final score with confidence and an executive summary. The Next.js dashboard personalizes recommendations using onboarding data, so procurement teams can quickly identify risky suppliers, estimate cost exposure, and choose safer alternatives.”
