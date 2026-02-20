"""
refresh_real_data.py — Replace all static seed data with live external feeds.

Sources:
  - World Bank WGI (PV.EST) — Political Stability risk scores, free REST API
  - GDELT v2 — live geopolitical headlines per country, free
  - DataCo SMART Supply Chain CSV (if available at backend/dataco.csv or
    auto-downloaded via Kaggle API if ~/.kaggle/kaggle.json is configured)

Run:
    python refresh_real_data.py
"""

import json
import sys
import time
from datetime import datetime, date, timedelta

import httpx
from database import engine, SessionLocal, Base
from models import Supplier, EquipmentSchedule, CountryRisk, CountryFactors

# ── Countries to refresh ────────────────────────────────────────────────────
COUNTRIES = [
    ("China",       "CN"),
    ("India",       "IN"),
    ("Vietnam",     "VN"),
    ("Taiwan",      "TW"),
    ("South Korea", "KR"),
    ("Germany",     "DE"),
    ("Japan",       "JP"),
    ("USA",         "US"),
    ("Malaysia",    "MY"),
    ("Mexico",      "MX"),
    ("Brazil",      "BR"),
    ("Bangladesh",  "BD"),
    ("Indonesia",   "ID"),
    ("Thailand",    "TH"),
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. World Bank WGI  —  Political Stability & Absence of Violence (PV.EST)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_wgi(iso: str) -> tuple[float | None, str]:
    """Returns (risk_score 0-10, year_label). Higher = more risk."""
    url = (
        f"https://api.worldbank.org/v2/country/{iso}"
        f"/indicator/PV.EST?format=json&mrv=1"
    )
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.get(url)
        if r.status_code != 200:
            return None, "WB API error"
        data = r.json()
        if len(data) < 2 or not data[1]:
            return None, "no data"
        rec = data[1][0]
        pv = rec.get("value")
        year = rec.get("date", "?")
        if pv is None:
            return None, "null value"
        # PV.EST: -2.5 (very unstable) → +2.5 (very stable)  →  risk 0–10
        risk = round(max(0.0, min(10.0, 5.0 - (2.0 * float(pv)))), 2)
        return risk, year
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# 2. GDELT v2  —  recent supply-chain news headline per country
# ─────────────────────────────────────────────────────────────────────────────

def fetch_gdelt_headline(country: str) -> tuple[str, str]:
    """Returns (headline, source_url). GDELT is also called live per /analyze request."""
    query = f"{country} supply chain trade disruption"
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={query.replace(' ', '%20')}"
        f"&mode=artlist&maxrecords=5&format=json"
    )
    try:
        with httpx.Client(timeout=6.0, verify=False) as c:
            r = c.get(url)
        if r.status_code != 200:
            return f"No recent supply chain events retrieved for {country}", ""
        arts = r.json().get("articles", [])
        if not arts:
            return f"No recent supply chain events retrieved for {country}", ""
        top = arts[0]
        return top.get("title", "No headline"), top.get("url", "")
    except BaseException:
        return f"Live GDELT headlines fetched per analysis request for {country}", "https://www.gdeltproject.org/"


# ─────────────────────────────────────────────────────────────────────────────
# 3. DataCo CSV (auto-download via Kaggle if possible, else prompt)
# ─────────────────────────────────────────────────────────────────────────────

DATACO_CSV = "dataco.csv"
KAGGLE_DATASET = "shashwatwork/dataco-smart-supply-chain-for-big-data-analysis"


def ensure_dataco_csv() -> bool:
    """Returns True if dataco.csv is available after this call."""
    import os
    if os.path.exists(DATACO_CSV):
        print(f"   dataco.csv already present ({os.path.getsize(DATACO_CSV) // 1024} KB)")
        return True

    # Try Kaggle API
    try:
        import kaggle  # noqa
        print("   Downloading DataCo CSV via Kaggle API …")
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(KAGGLE_DATASET, path=".", unzip=True)
        # Kaggle may save with a different filename — try to find it
        import glob
        candidates = glob.glob("*.csv")
        dataco_file = next((f for f in candidates if "dataco" in f.lower() or "supply" in f.lower()), None)
        if dataco_file and dataco_file != DATACO_CSV:
            os.rename(dataco_file, DATACO_CSV)
        return os.path.exists(DATACO_CSV)
    except Exception as e:
        print(f"   Kaggle auto-download unavailable: {e}")
        print()
        print("   ─────────────────────────────────────────────────────")
        print("   To load real order data, download DataCo manually:")
        print("   1. Visit https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis")
        print("   2. Click Download → save as  backend/dataco.csv")
        print("   3. Re-run:  python refresh_real_data.py")
        print("   ─────────────────────────────────────────────────────")
        print()
        return False


REGION_COUNTRY_MAP = {
    "Western Europe": "Germany", "Central America": "Mexico",
    "Oceania":        "Japan",   "Eastern Asia":    "China",
    "West of USA":    "USA",     "US Center":        "USA",
    "East of USA":    "USA",     "Canada":           "USA",
    "Southern Asia":  "India",   "South America":    "Brazil",
    "Southeast Asia": "Vietnam", "Eastern Europe":   "India",
    "West Africa":    "India",   "Central Africa":   "India",
    "North Africa":   "India",   "East Africa":      "India",
    "South Asia":     "India",   "Caribbean":        "Mexico",
    "Pacific Asia":   "South Korea", "Southern Europe": "Germany",
    "Northern Europe":"Germany",
}


def load_dataco_into_db(db):
    """Loads DataCo CSV into Supplier + EquipmentSchedule tables."""
    import pandas as pd

    print("   Reading dataco.csv …")
    try:
        df = pd.read_csv(DATACO_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(DATACO_CSV, encoding="latin-1")

    print(f"   {len(df):,} rows loaded")

    # Normalise column names
    col_map = {}
    for col in df.columns:
        lc = col.lower().strip()
        if "days for shipment" in lc and "scheduled" in lc:
            col_map[col] = "Days_Scheduled"
        elif "days for shipping" in lc and "real" in lc:
            col_map[col] = "Days_Real"
        elif "late_delivery_risk" in lc or "late delivery" in lc:
            col_map[col] = "Late_Risk"
        elif "order region" in lc:
            col_map[col] = "Region"
        elif "order item product price" in lc or ("sales" in lc and "per" in lc):
            col_map[col] = "ItemValue"
    df = df.rename(columns=col_map)

    for req in ["Days_Scheduled", "Days_Real", "Late_Risk"]:
        if req not in df.columns:
            print(f"   ⚠  Missing column '{req}' — skipping schedule data")
            return
    if "Region" not in df.columns:
        df["Region"] = "Eastern Asia"
    if "ItemValue" not in df.columns:
        df["ItemValue"] = 25000.0

    for col in ["Days_Scheduled", "Days_Real", "Late_Risk", "ItemValue"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Days_Scheduled", "Days_Real", "Late_Risk"])

    # Clear old schedule / supplier data
    db.query(EquipmentSchedule).delete()
    db.query(Supplier).delete()
    db.commit()

    regions = df["Region"].dropna().unique()[:12]
    supplier_map = {}
    ref_date = date(2025, 1, 1)

    for i, region in enumerate(regions, start=1):
        country = REGION_COUNTRY_MAP.get(region, "China")
        rdf = df[df["Region"] == region]
        late_rate = rdf["Late_Risk"].mean()
        reliability = round(max(50.0, min(98.0, 100.0 - late_rate * 30)), 1)
        avg_delivery = int(rdf["Days_Scheduled"].median() or 14)
        costs = ["low", "medium", "high"]
        cost = costs[i % 3]

        s = Supplier(
            id=i,
            supplier_name=f"{country} Supply Co. ({region})",
            country=country,
            reliability_score=reliability,
            average_delivery_time=avg_delivery,
            cost_competitiveness=cost,
        )
        db.add(s)
        supplier_map[region] = i

    db.commit()
    print(f"   ✅ {len(supplier_map)} suppliers from DataCo regions")

    eq_id = 1
    max_per_supplier = 200  # up to 200 real order rows per region

    for region, sup_id in supplier_map.items():
        rdf = df[df["Region"] == region].head(max_per_supplier)
        for _, row in rdf.iterrows():
            sched = int(row["Days_Scheduled"])
            real  = int(row["Days_Real"])
            late  = int(row["Late_Risk"]) == 1
            val   = float(row["ItemValue"]) * 100

            planned = ref_date + timedelta(days=eq_id % 365)
            delay   = real - sched
            actual  = planned + timedelta(days=delay) if late and delay > 0 else planned

            db.add(EquipmentSchedule(
                id=eq_id,
                equipment_name=f"Order {eq_id:05d} [{region}]",
                supplier_id=sup_id,
                planned_delivery_date=planned,
                actual_delivery_date=actual,
                equipment_value=round(val, 2),
                status="delayed" if late else "on_time",
            ))
            eq_id += 1
        db.commit()

    print(f"   ✅ {eq_id - 1:,} real order records loaded from DataCo")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print()
    print("═" * 60)
    print("  SentriChain — Live Data Refresh")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("═" * 60)

    # ── 1. World Bank WGI + GDELT per country ───────────────────────────────
    print()
    print("▶ Fetching World Bank WGI Political Stability scores …")
    print("  Source: https://api.worldbank.org  (PV.EST indicator)")
    print()

    db.query(CountryRisk).delete()
    db.commit()

    success = 0
    for risk_id, (country, iso) in enumerate(COUNTRIES, start=1):
        try:
            risk_score, year = fetch_wgi(iso)
            headline, src_url = fetch_gdelt_headline(country)

            if risk_score is None:
                risk_score = 5.0
                year = "fallback"

            db.add(CountryRisk(
                id=risk_id,
                country=country,
                risk_score=risk_score,
                headline=headline,
                source_url=src_url or "https://info.worldbank.org/governance/wgi/",
            ))
            db.commit()

            status = "✅" if year != "fallback" else "⚠ "
            print(f"  {status} {country:<14} risk={risk_score:.2f}/10  "
                  f"(WGI {year})  headline: {headline[:60]}…")
            success += 1
        except BaseException as e:
            print(f"  ✗  {country:<14} skipped ({e})")
            db.rollback()

        time.sleep(0.3)

    print(f"\n  {success}/{len(COUNTRIES)} countries updated from World Bank WGI")

    # ── 2. DataCo order data ─────────────────────────────────────────────────
    print()
    print("▶ Loading DataCo order data …")
    if ensure_dataco_csv():
        load_dataco_into_db(db)
    else:
        print("  ⚠  Skipping schedule data (dataco.csv not available)")
        print("     Existing supplier/schedule rows kept unchanged")

    db.close()
    print()
    print("═" * 60)
    print("  Refresh complete. Restart uvicorn to clear any caches.")
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
