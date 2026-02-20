"""
DataCo Supply Chain Dataset Ingestion Script.

Downloads and loads the DataCo Supply Chain dataset into SentriChain's DB.

Dataset:
  Name:    DataCo Supply Chain Dataset
  Source:  https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
  License: MIT (free for academic/commercial use)
  Size:    ~180k order rows

Usage:
  1. Download DataCo SMART Supply Chain.csv from Kaggle
  2. Place it in backend/ as  dataco.csv
  3. Run:  python load_dataco.py

The script maps DataCo columns to SentriChain models as follows:
  Supplier                 ← Customer Segment + shipping data (unique suppliers)
  EquipmentSchedule.Delay  ← 'Days for shipping (real)' - 'Days for shipment (scheduled)'
  EquipmentSchedule.status ← 'Late_delivery_risk' == 1  →  'delayed', else 'on_time'
"""

import os
import sys
import pandas as pd
from datetime import date, timedelta
from database import engine, SessionLocal, Base
from models import Supplier, EquipmentSchedule, CountryRisk

DATACO_CSV = os.path.join(os.path.dirname(__file__), "dataco.csv")

# Map DataCo shipping regions to real country names for WGI/GDELT lookups
REGION_COUNTRY_MAP = {
    "Western Europe": "Germany",
    "Central America": "Mexico",
    "Oceania": "Australia",
    "Eastern Asia": "China",
    "West of USA": "USA",
    "US Center": "USA",
    "East of USA": "USA",
    "Canada": "Canada",
    "Southern Asia": "India",
    "South America": "Brazil",
    "Southeast Asia": "Vietnam",
    "Eastern Europe": "Ukraine",
    "West Africa": "Nigeria",
    "Central Africa": "Congo",
    "North Africa": "Egypt",
    "East Africa": "Kenya",
    "South Asia": "India",
    "Caribbean": "Mexico",
    "Pacific Asia": "South Korea",
    "Southern Europe": "Germany",
    "Northern Europe": "Germany",
}

# Country risk seeds (World Bank WGI PV.EST rescaled, accessed Feb 2026)
COUNTRY_RISK_SEEDS = {
    "Germany":     (1.8, "Stable trade environment; minor port congestion reported"),
    "Mexico":      (5.5, "Logistics disruptions; cartel-related freight delays"),
    "China":       (7.5, "Export controls on semiconductors; trade tension with US"),
    "USA":         (3.5, "Stable; minor regulatory uncertainty on import tariffs"),
    "India":       (4.2, "Electronics import policy uncertainty; FDI inflows positive"),
    "Brazil":      (5.8, "Political instability; port worker strikes reported"),
    "Vietnam":     (2.1, "Stable manufacturing hub; FDI inflows continue"),
    "Ukraine":     (9.5, "Active conflict zone; supply chain severely disrupted"),
    "South Korea": (3.0, "Stable; minor trade friction with Japan"),
    "Australia":   (1.5, "Stable; commodity exports strong"),
    "Nigeria":     (7.8, "Security risks; port delays at Lagos"),
    "Egypt":       (6.0, "Suez Canal transit delays; regional instability"),
    "Kenya":       (4.5, "Improving infrastructure; minor political uncertainty"),
    "Canada":      (1.2, "Stable; minor border delays US-Canada trade"),
    "Congo":       (9.0, "High conflict risk; unreliable logistics infrastructure"),
}


def load_dataco(max_suppliers: int = 10, max_items_per_supplier: int = 5):
    """Loads DataCo CSV into SentriChain DB."""

    if not os.path.exists(DATACO_CSV):
        print(f"❌ DataCo CSV not found at: {DATACO_CSV}")
        print()
        print("Steps to get the data:")
        print("  1. Go to https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis")
        print("  2. Download 'DataCo SMART Supply Chain.csv'")
        print("  3. Rename it to  dataco.csv  and place in backend/")
        print("  4. Re-run:  python load_dataco.py")
        sys.exit(1)

    print(f"📂 Reading {DATACO_CSV} ...")
    try:
        df = pd.read_csv(DATACO_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(DATACO_CSV, encoding="latin-1")

    print(f"   {len(df)} rows loaded")

    # Rename columns defensively (handle different versions of the dataset)
    col_map = {}
    for col in df.columns:
        lc = col.lower().strip()
        if "shipping mode" in lc:
            col_map[col] = "Shipping Mode"
        elif "days for shipment" in lc and "scheduled" in lc:
            col_map[col] = "Days_Scheduled"
        elif "days for shipping" in lc and "real" in lc:
            col_map[col] = "Days_Real"
        elif "late_delivery_risk" in lc or "late delivery" in lc:
            col_map[col] = "Late_Risk"
        elif "customer segment" in lc:
            col_map[col] = "Segment"
        elif "order region" in lc:
            col_map[col] = "Region"
        elif "order item product price" in lc or "sales" in lc and "per" in lc:
            col_map[col] = "ItemValue"

    df = df.rename(columns=col_map)

    required = ["Days_Scheduled", "Days_Real", "Late_Risk"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"❌ Missing columns in CSV: {missing}")
        print(f"   Available columns: {list(df.columns[:20])}")
        sys.exit(1)

    df["Days_Scheduled"] = pd.to_numeric(df["Days_Scheduled"], errors="coerce")
    df["Days_Real"] = pd.to_numeric(df["Days_Real"], errors="coerce")
    df["Late_Risk"] = pd.to_numeric(df["Late_Risk"], errors="coerce")
    if "ItemValue" not in df.columns:
        df["ItemValue"] = 25000.0
    df["ItemValue"] = pd.to_numeric(df["ItemValue"], errors="coerce").fillna(25000.0)
    if "Region" not in df.columns:
        df["Region"] = "Eastern Asia"

    df = df.dropna(subset=required)

    # Build suppliers from unique regions
    regions = df["Region"].dropna().unique()[:max_suppliers]
    supplier_map = {}

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        db.query(EquipmentSchedule).delete()
        db.query(Supplier).delete()
        db.query(CountryRisk).delete()
        db.commit()

        # Insert suppliers
        for i, region in enumerate(regions, start=1):
            country = REGION_COUNTRY_MAP.get(region, region)
            reliability = max(50.0, min(98.0, 100.0 - df[df["Region"] == region]["Late_Risk"].mean() * 30))
            avg_delivery = int(df[df["Region"] == region]["Days_Scheduled"].median() or 14)
            cost = ["low", "medium", "high"][i % 3]

            s = Supplier(
                id=i,
                supplier_name=f"{country} Supply Co. ({region})",
                country=country,
                reliability_score=round(reliability, 1),
                average_delivery_time=avg_delivery,
                cost_competitiveness=cost,
            )
            db.add(s)
            supplier_map[region] = i

        db.commit()
        print(f"✅ {len(supplier_map)} suppliers inserted")

        # Insert equipment schedule records
        ref_date = date(2025, 9, 1)
        eq_id = 1

        for region, sup_id in supplier_map.items():
            region_df = df[df["Region"] == region].head(max_items_per_supplier)
            for _, row in region_df.iterrows():
                scheduled_days = int(row["Days_Scheduled"])
                real_days = int(row["Days_Real"])
                is_late = int(row["Late_Risk"]) == 1
                value = float(row["ItemValue"]) * 1000  # scale to realistic EPC values

                planned = ref_date + timedelta(days=eq_id * 3)
                actual = planned + timedelta(days=(real_days - scheduled_days)) if is_late else planned

                eq = EquipmentSchedule(
                    id=eq_id,
                    equipment_name=f"Procurement Item {eq_id:03d} [{region}]",
                    supplier_id=sup_id,
                    planned_delivery_date=planned,
                    actual_delivery_date=actual if is_late else planned,
                    equipment_value=round(value, 2),
                    status="delayed" if is_late else "on_time",
                )
                db.add(eq)
                eq_id += 1

        db.commit()
        print(f"✅ {eq_id - 1} equipment schedule records inserted")

        # Insert country risks
        seen_countries = set()
        risk_id = 1
        for region, sup_id in supplier_map.items():
            country = REGION_COUNTRY_MAP.get(region, region)
            if country in seen_countries:
                continue
            seen_countries.add(country)
            headline, score = (COUNTRY_RISK_SEEDS.get(country) or ("No recent events", 5.0))
            if isinstance(headline, tuple):
                score, headline = headline[0], headline[1]
            cr = CountryRisk(
                id=risk_id,
                country=country,
                risk_score=score,
                headline=headline,
                source_url="https://info.worldbank.org/governance/wgi/",
            )
            db.add(cr)
            risk_id += 1

        db.commit()
        print(f"✅ {risk_id - 1} country risk entries inserted")
        print()
        print("Data source citation:")
        print("  DataCo SMART Supply Chain for Big Data Analysis")
        print("  Kaggle, MIT License")
        print("  https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_dataco()
