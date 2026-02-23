# SentriChain — Pre-Submission TODO

## Issues to Fix

1. **README is wrong**
   - Still says "Future Integrations: LLM-powered summaries, Real-time data feeds, 3D visualization"
   - Still says "Models: ready for implementation"
   - Judges reading this will think it's an empty template
   - Needs a full rewrite to reflect what's actually built

2. **`/login` page is broken-looking**
   - `frontend/app/login/page.tsx` just instantly redirects to `/onboard` with no UI
   - If a judge navigates to `/login` it looks like a missing page
   - Should either show a proper login form or at least a loading spinner

3. **Gemini LLM key missing**
   - If `GEMINI_API_KEY` is not set in `.env`, the AI Summary in the analysis tab falls back to a heuristic string
   - A real LLM summary would be significantly more impressive for a demo
   - Fix: add a free-tier Gemini API key to `.env`

4. **`supply_tier` not visible in the Overview tab**
   - The Raw Materials / Components / Manufacturing tier data exists in the DB and API
   - It only shows in the SupplierSelector dropdown, not in the Overview table
   - Should surface it as a column or filter in the suppliers overview

5. **Compare Countries tab — verify it shows real data**
   - Not confirmed whether the Compare tab renders actual country comparison data or is empty/broken
   - Needs a visual check before submission
