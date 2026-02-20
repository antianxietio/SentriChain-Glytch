"""
Seed script — populates DB with realistic procurement data.

Data modeled after EPC project procurement patterns. Values reference:
  - DataCo Supply Chain Dataset structure (Kaggle, MIT license)
  - World Bank WGI Political Stability scores (rescaled 0-10)
  - World Bank Logistics Performance Index (LPI) 2023
  - OECD Tax Database 2024
  - UNCTAD Trade & Transport Facilitation data

Run:  python seed_data.py
"""

import json
from datetime import date, datetime
from database import engine, SessionLocal, Base
from models import Supplier, EquipmentSchedule, CountryRisk, CountryFactors, User, UserCompanyProfile
import bcrypt


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clear in FK-safe order
        db.query(UserCompanyProfile).delete()
        db.query(EquipmentSchedule).delete()
        db.query(Supplier).delete()
        db.query(CountryRisk).delete()
        db.query(CountryFactors).delete()
        demo_emails = ["demo@sentrichain.com", "admin@sentrichain.com"]
        for email in demo_emails:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                db.delete(existing)
        db.commit()

        # ── Demo users ────────────────────────────────────────────────────
        demo_users = [
            User(email="demo@sentrichain.com", full_name="Demo Analyst",
                 hashed_password=_hash("Demo@2025"), role="analyst", is_active=True),
            User(email="admin@sentrichain.com", full_name="Admin User",
                 hashed_password=_hash("Admin@2025"), role="admin", is_active=True),
        ]
        db.add_all(demo_users)
        db.commit()

        # ── Suppliers (8, across 6 countries) ─────────────────────────────
        suppliers = [
            Supplier(id=1, supplier_name="Shanghai Electronics Co.",
                     country="China", reliability_score=72.0,
                     average_delivery_time=21, cost_competitiveness="high"),
            Supplier(id=2, supplier_name="Shenzhen Tech Manufacturing",
                     country="China", reliability_score=68.0,
                     average_delivery_time=25, cost_competitiveness="high"),
            Supplier(id=3, supplier_name="Mumbai Industrial Parts",
                     country="India", reliability_score=85.0,
                     average_delivery_time=18, cost_competitiveness="medium"),
            Supplier(id=4, supplier_name="Delhi Precision Components",
                     country="India", reliability_score=88.0,
                     average_delivery_time=16, cost_competitiveness="medium"),
            Supplier(id=5, supplier_name="Hanoi Assembly Solutions",
                     country="Vietnam", reliability_score=91.0,
                     average_delivery_time=14, cost_competitiveness="low"),
            Supplier(id=6, supplier_name="Taiwan Precision Semiconductors",
                     country="Taiwan", reliability_score=95.0,
                     average_delivery_time=12, cost_competitiveness="medium"),
            Supplier(id=7, supplier_name="Seoul Advanced Materials",
                     country="South Korea", reliability_score=93.0,
                     average_delivery_time=13, cost_competitiveness="medium"),
            Supplier(id=8, supplier_name="Berlin Engineering GmbH",
                     country="Germany", reliability_score=97.0,
                     average_delivery_time=10, cost_competitiveness="low"),
        ]
        db.add_all(suppliers)
        db.commit()

        # ── Equipment schedules ───────────────────────────────────────────
        equipment = [
            EquipmentSchedule(id=1,  equipment_name="PCB Assembly Unit A",       supplier_id=1,
                              planned_delivery_date=date(2025,10, 1), actual_delivery_date=date(2025,10,16),
                              equipment_value=45000.00,  status="delayed"),
            EquipmentSchedule(id=2,  equipment_name="Semiconductor Batch X1",    supplier_id=1,
                              planned_delivery_date=date(2025,11, 1), actual_delivery_date=date(2025,11,19),
                              equipment_value=120000.00, status="delayed"),
            EquipmentSchedule(id=3,  equipment_name="Control Module B2",         supplier_id=1,
                              planned_delivery_date=date(2025,11,20), actual_delivery_date=date(2025,11,20),
                              equipment_value=38000.00,  status="on_time"),
            EquipmentSchedule(id=4,  equipment_name="Display Panels Set B",      supplier_id=2,
                              planned_delivery_date=date(2025,10,10), actual_delivery_date=date(2025,11, 4),
                              equipment_value=78000.00,  status="delayed"),
            EquipmentSchedule(id=5,  equipment_name="Battery Modules C",         supplier_id=2,
                              planned_delivery_date=date(2025,11, 1), actual_delivery_date=None,
                              equipment_value=55000.00,  status="delayed"),
            EquipmentSchedule(id=6,  equipment_name="Power Inverter D3",         supplier_id=2,
                              planned_delivery_date=date(2025,11,15), actual_delivery_date=date(2025,12, 5),
                              equipment_value=62000.00,  status="delayed"),
            EquipmentSchedule(id=7,  equipment_name="Steel Frames D",            supplier_id=3,
                              planned_delivery_date=date(2025,10,10), actual_delivery_date=date(2025,10,10),
                              equipment_value=32000.00,  status="on_time"),
            EquipmentSchedule(id=8,  equipment_name="Precision Gears E",         supplier_id=3,
                              planned_delivery_date=date(2025,11, 5), actual_delivery_date=date(2025,11,10),
                              equipment_value=28000.00,  status="delayed"),
            EquipmentSchedule(id=9,  equipment_name="Hydraulic Cylinders F2",    supplier_id=3,
                              planned_delivery_date=date(2025,12, 1), actual_delivery_date=date(2025,12, 1),
                              equipment_value=41000.00,  status="on_time"),
            EquipmentSchedule(id=10, equipment_name="Motor Assembly F",          supplier_id=4,
                              planned_delivery_date=date(2025,10,25), actual_delivery_date=date(2025,10,24),
                              equipment_value=41000.00,  status="on_time"),
            EquipmentSchedule(id=11, equipment_name="Sensor Package G",          supplier_id=4,
                              planned_delivery_date=date(2025,11,20), actual_delivery_date=date(2025,11,20),
                              equipment_value=19000.00,  status="on_time"),
            EquipmentSchedule(id=12, equipment_name="Wiring Harness H",          supplier_id=5,
                              planned_delivery_date=date(2025,10,15), actual_delivery_date=date(2025,10,14),
                              equipment_value=15000.00,  status="on_time"),
            EquipmentSchedule(id=13, equipment_name="Connector Set I",           supplier_id=5,
                              planned_delivery_date=date(2025,11,10), actual_delivery_date=date(2025,11,10),
                              equipment_value=12000.00,  status="on_time"),
            EquipmentSchedule(id=14, equipment_name="MOSFET Wafer Batch T1",     supplier_id=6,
                              planned_delivery_date=date(2025,11, 1), actual_delivery_date=date(2025,11, 1),
                              equipment_value=210000.00, status="on_time"),
            EquipmentSchedule(id=15, equipment_name="DRAM Module Set T2",        supplier_id=6,
                              planned_delivery_date=date(2025,12, 1), actual_delivery_date=date(2025,11,30),
                              equipment_value=175000.00, status="on_time"),
            EquipmentSchedule(id=16, equipment_name="OLED Display Array K1",     supplier_id=7,
                              planned_delivery_date=date(2025,10,20), actual_delivery_date=date(2025,10,20),
                              equipment_value=88000.00,  status="on_time"),
            EquipmentSchedule(id=17, equipment_name="Li-Ion Cell Pack K2",       supplier_id=7,
                              planned_delivery_date=date(2025,11,25), actual_delivery_date=date(2025,12, 3),
                              equipment_value=64000.00,  status="delayed"),
            EquipmentSchedule(id=18, equipment_name="CNC Machined Parts G1",     supplier_id=8,
                              planned_delivery_date=date(2025,10,15), actual_delivery_date=date(2025,10,15),
                              equipment_value=95000.00,  status="on_time"),
            EquipmentSchedule(id=19, equipment_name="Precision Servo Motors G2", supplier_id=8,
                              planned_delivery_date=date(2025,11,10), actual_delivery_date=date(2025,11,10),
                              equipment_value=72000.00,  status="on_time"),
        ]
        db.add_all(equipment)
        db.commit()

        # ── Country risk (World Bank WGI PV.EST rescaled 0-10) ────────────
        country_risks = [
            CountryRisk(id=1, country="China",       risk_score=7.5,
                        headline="Trade tensions escalate; export controls on semiconductor equipment",
                        source_url="https://www.gdeltproject.org/"),
            CountryRisk(id=2, country="India",       risk_score=4.2,
                        headline="Regulatory uncertainty in electronics import; minor logistics delays",
                        source_url="https://www.gdeltproject.org/"),
            CountryRisk(id=3, country="Vietnam",     risk_score=2.1,
                        headline="Stable manufacturing hub; FDI inflows continue as China+1 gains momentum",
                        source_url="https://www.gdeltproject.org/"),
            CountryRisk(id=4, country="Taiwan",      risk_score=5.8,
                        headline="Cross-strait tensions elevated; semiconductor supply chain under geopolitical watch",
                        source_url="https://www.gdeltproject.org/"),
            CountryRisk(id=5, country="South Korea", risk_score=2.8,
                        headline="Strong export performance; minor North Korea-related geopolitical risk",
                        source_url="https://www.gdeltproject.org/"),
            CountryRisk(id=6, country="Germany",     risk_score=1.5,
                        headline="Energy cost pressures persist post-2022; manufacturing PMI stabilising",
                        source_url="https://www.gdeltproject.org/"),
        ]
        db.add_all(country_risks)
        db.commit()

        # ── Country factors (logistics, economy, tax) ─────────────────────
        # Sources: World Bank LPI 2023, OECD Tax DB 2024, IMF WEO 2024
        country_factors = [
            CountryFactors(
                id=1, country="China", continent="Asia",
                economy_score=8.2, economy_label="emerging",
                gdp_growth_pct=4.9, currency="CNY", currency_volatility="medium",
                corporate_tax_pct=25.0, import_tariff_pct=7.5, vat_gst_pct=13.0,
                tax_complexity="high", has_fta=True,
                fta_partners=json.dumps(["ASEAN", "RCEP", "Pakistan", "Chile"]),
                avg_shipping_days=21, shipping_cost_usd_per_kg=0.85,
                port_efficiency_score=7.4, transport_reliability=7.2,
                customs_clearance_days=4,
                common_issues=json.dumps([
                    "Port congestion at Shanghai & Shenzhen during peak season (Oct–Dec)",
                    "Export controls on semiconductors & advanced electronics components",
                    "Typhoon season (Jul–Oct) causes coastal route delays of 3–7 days",
                    "US/EU tariff escalation risk on electronics (15–25% additional)",
                    "Intensive customs documentation; pre-clearance filing mandatory",
                ]),
                political_stability=4.5, infrastructure_score=8.1, labor_cost_index=0.60,
            ),
            CountryFactors(
                id=2, country="India", continent="Asia",
                economy_score=7.1, economy_label="emerging",
                gdp_growth_pct=6.5, currency="INR", currency_volatility="medium",
                corporate_tax_pct=22.0, import_tariff_pct=15.1, vat_gst_pct=18.0,
                tax_complexity="high", has_fta=True,
                fta_partners=json.dumps(["ASEAN", "UAE", "Australia", "South Korea", "Japan"]),
                avg_shipping_days=18, shipping_cost_usd_per_kg=0.92,
                port_efficiency_score=6.2, transport_reliability=6.8,
                customs_clearance_days=6,
                common_issues=json.dumps([
                    "Port congestion at JNPT Mumbai during festive & monsoon seasons",
                    "High import tariff (15–25%) on many industrial categories",
                    "Complex GST structure — 5%, 12%, 18%, 28% slabs add compliance cost",
                    "Inland infrastructure bottlenecks; last-mile adds 2–4 days",
                    "Bureaucratic customs clearance — licensed customs agent strongly advised",
                ]),
                political_stability=5.8, infrastructure_score=6.5, labor_cost_index=0.38,
            ),
            CountryFactors(
                id=3, country="Vietnam", continent="Asia",
                economy_score=6.8, economy_label="developing",
                gdp_growth_pct=5.8, currency="VND", currency_volatility="low",
                corporate_tax_pct=20.0, import_tariff_pct=5.2, vat_gst_pct=10.0,
                tax_complexity="medium", has_fta=True,
                fta_partners=json.dumps(["RCEP", "EU (EVFTA)", "UK", "ASEAN", "CPTPP", "South Korea"]),
                avg_shipping_days=14, shipping_cost_usd_per_kg=0.78,
                port_efficiency_score=7.0, transport_reliability=7.5,
                customs_clearance_days=3,
                common_issues=json.dumps([
                    "Smaller port capacity than China; limited direct routes to some markets",
                    "Seasonal flooding in Mekong Delta disrupts inland logistics (Aug–Nov)",
                    "Limited rail freight; road transport is dominant mode",
                    "Power supply reliability issues in some industrial zones",
                    "Skilled labour shortages in precision electronics manufacturing",
                ]),
                political_stability=7.2, infrastructure_score=6.8, labor_cost_index=0.30,
            ),
            CountryFactors(
                id=4, country="Taiwan", continent="Asia",
                economy_score=8.8, economy_label="advanced",
                gdp_growth_pct=3.1, currency="TWD", currency_volatility="low",
                corporate_tax_pct=20.0, import_tariff_pct=4.2, vat_gst_pct=5.0,
                tax_complexity="medium", has_fta=False,
                fta_partners=json.dumps(["Singapore", "New Zealand", "ECFA (China — limited)"]),
                avg_shipping_days=12, shipping_cost_usd_per_kg=0.72,
                port_efficiency_score=8.5, transport_reliability=8.8,
                customs_clearance_days=2,
                common_issues=json.dumps([
                    "Cross-strait geopolitical tension — contingency planning essential",
                    "Limited FTA access; most trade under WTO MFN rates only",
                    "TSMC ecosystem concentration creates single-point-of-failure risk",
                    "Earthquake & typhoon risk (seismic zone) — BCP protocols required",
                    "Intense talent competition with global semiconductor majors",
                ]),
                political_stability=5.5, infrastructure_score=9.0, labor_cost_index=0.75,
            ),
            CountryFactors(
                id=5, country="South Korea", continent="Asia",
                economy_score=8.5, economy_label="advanced",
                gdp_growth_pct=2.3, currency="KRW", currency_volatility="low",
                corporate_tax_pct=24.0, import_tariff_pct=6.3, vat_gst_pct=10.0,
                tax_complexity="medium", has_fta=True,
                fta_partners=json.dumps(["US (KORUS)", "EU", "China", "ASEAN", "UK", "Australia"]),
                avg_shipping_days=13, shipping_cost_usd_per_kg=0.79,
                port_efficiency_score=8.2, transport_reliability=8.5,
                customs_clearance_days=2,
                common_issues=json.dumps([
                    "DPRK geopolitical risk — low probability, high impact scenario",
                    "Samsung/LG ecosystem dependency for electronics supply chains",
                    "Rising labour costs reduce cost advantage vs Vietnam & India",
                    "Occasional port labour strikes at Busan causing brief congestion",
                    "24% corporate tax on Korean subsidiary profits",
                ]),
                political_stability=7.0, infrastructure_score=9.2, labor_cost_index=0.82,
            ),
            CountryFactors(
                id=6, country="Germany", continent="Europe",
                economy_score=8.0, economy_label="advanced",
                gdp_growth_pct=0.2, currency="EUR", currency_volatility="low",
                corporate_tax_pct=29.9, import_tariff_pct=3.5, vat_gst_pct=19.0,
                tax_complexity="high", has_fta=True,
                fta_partners=json.dumps(["EU Single Market", "UK (TCA)", "Canada (CETA)", "Japan (EPA)", "South Korea"]),
                avg_shipping_days=10, shipping_cost_usd_per_kg=1.15,
                port_efficiency_score=8.9, transport_reliability=9.1,
                customs_clearance_days=1,
                common_issues=json.dumps([
                    "Post-Brexit UK border friction adds documentation overhead",
                    "Energy cost volatility post-2022 impacts manufacturing margins by 8–15%",
                    "Highest labour & logistics costs among all listed countries",
                    "VAT reclaim for non-EU buyers — 4 to 6 week processing",
                    "Slow GDP growth (near-recession 2024) — manufacturer capacity risk",
                ]),
                political_stability=9.2, infrastructure_score=9.5, labor_cost_index=1.85,
            ),
        ]
        db.add_all(country_factors)
        db.commit()

        print("✅ Database seeded successfully!")
        print(f"   {len(suppliers)} suppliers (China×2, India×2, Vietnam×1, Taiwan×1, S.Korea×1, Germany×1)")
        print(f"   {len(equipment)} equipment schedules")
        print(f"   {len(country_risks)} country risk entries")
        print(f"   {len(country_factors)} country factor profiles")
        print(f"   {len(demo_users)} demo users")
        print()
        print("Demo credentials:")
        print("  • Analyst — demo@sentrichain.com  / Demo@2025")
        print("  • Admin   — admin@sentrichain.com / Admin@2025")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
