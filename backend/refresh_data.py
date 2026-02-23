"""
Real data refresh — pulls live World Bank APIs and builds realistic procurement data.

Sources (all free, no API key required):
  - World Bank WGI  : Political Stability (PV.EST) — https://data.worldbank.org
  - World Bank LPI  : Logistics Performance Index  — https://data.worldbank.org
  - World Bank GDP  : GDP per capita growth        — https://data.worldbank.org
  - GDELT v2        : Geopolitical headlines       — https://api.gdeltproject.org

Run:  python refresh_data.py
"""

import json
import random
import sys
import time
import httpx
from datetime import date, timedelta

# Force UTF-8 output so Unicode symbols (✓ ⚠ →) work on Windows cp1252 terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from database import engine, SessionLocal, Base
from models import Supplier, EquipmentSchedule, CountryRisk, CountryFactors, User, UserCompanyProfile
import bcrypt

random.seed(42)

# ---------------------------------------------------------------------------
# World Bank indicator fetch
# ---------------------------------------------------------------------------

WB_BASE = "https://api.worldbank.org/v2"

COUNTRIES = {
    "China":       "CN",
    "India":       "IN",
    "Vietnam":     "VN",
    "Taiwan":      "TW",
    "South Korea": "KR",
    "Germany":     "DE",
    "Japan":       "JP",
    "USA":         "US",
    "Malaysia":    "MY",
    "Mexico":      "MX",
    "Brazil":      "BR",
    "Bangladesh":  "BD",
    "Indonesia":   "ID",
    "Thailand":    "TH",
}


def wb_fetch(indicator: str, iso: str, years: int = 5) -> float | None:
    """Fetch latest non-null value for a World Bank indicator."""
    url = f"{WB_BASE}/country/{iso}/indicator/{indicator}?format=json&per_page=10&mrv={years}"
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.get(url)
        if r.status_code != 200:
            return None
        data = r.json()
        if len(data) < 2 or not data[1]:
            return None
        for entry in data[1]:
            if entry.get("value") is not None:
                return float(entry["value"])
    except Exception:
        pass
    return None


def fetch_gdelt_headline(country: str) -> tuple[str, str, int]:
    """Returns (headline, source_url, event_count)."""
    try:
        q = f"{country} supply chain trade"
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={q.replace(' ', '%20')}"
            f"&mode=artlist&maxrecords=5&format=json"
        )
        with httpx.Client(timeout=4.0) as c:
            r = c.get(url)
        if r.status_code == 200:
            arts = r.json().get("articles", [])
            if arts:
                top = arts[0]
                return top.get("title", ""), top.get("url", ""), len(arts)
    except Exception:
        pass
    return f"No recent events retrieved for {country}", "", 0


# ---------------------------------------------------------------------------
# Real World Bank data per country
# ---------------------------------------------------------------------------

COUNTRY_META = {
    "China":       {"continent": "Asia",          "currency": "CNY", "has_fta": True,  "fta": ["ASEAN","RCEP","Australia","NZ"]},
    "India":       {"continent": "Asia",          "currency": "INR", "has_fta": True,  "fta": ["ASEAN","Sri Lanka","Japan"]},
    "Vietnam":     {"continent": "Asia",          "currency": "VND", "has_fta": True,  "fta": ["ASEAN","EVFTA","RCEP"]},
    "Taiwan":      {"continent": "Asia",          "currency": "TWD", "has_fta": False, "fta": []},
    "South Korea": {"continent": "Asia",          "currency": "KRW", "has_fta": True,  "fta": ["USA","EU","ASEAN","Japan"]},
    "Germany":     {"continent": "Europe",        "currency": "EUR", "has_fta": True,  "fta": ["EU single market","Japan","Canada","South Korea"]},
    "Japan":       {"continent": "Asia",          "currency": "JPY", "has_fta": True,  "fta": ["CPTPP","EU","USA","ASEAN"]},
    "USA":         {"continent": "North America", "currency": "USD", "has_fta": True,  "fta": ["USMCA","South Korea","Australia","Israel"]},
    "Malaysia":    {"continent": "Asia",          "currency": "MYR", "has_fta": True,  "fta": ["ASEAN","RCEP","Australia","NZ"]},
    "Mexico":      {"continent": "North America", "currency": "MXN", "has_fta": True,  "fta": ["USMCA","EU","Japan"]},
    "Brazil":      {"continent": "South America", "currency": "BRL", "has_fta": False, "fta": ["Mercosur-EU (pending)"]},
    "Bangladesh":  {"continent": "Asia",          "currency": "BDT", "has_fta": False, "fta": []},
    "Indonesia":   {"continent": "Asia",          "currency": "IDR", "has_fta": True,  "fta": ["ASEAN","RCEP","Australia"]},
    "Thailand":    {"continent": "Asia",          "currency": "THB", "has_fta": True,  "fta": ["ASEAN","RCEP","Australia","NZ"]},
}

# Fallback LPI data (World Bank LPI 2023 — published values)
LPI_2023 = {
    "China": 3.68, "India": 3.41, "Vietnam": 3.30, "Taiwan": 3.92,
    "South Korea": 3.97, "Germany": 4.20, "Japan": 4.03, "USA": 3.98,
    "Malaysia": 3.55, "Mexico": 3.02, "Brazil": 2.94, "Bangladesh": 2.68,
    "Indonesia": 3.15, "Thailand": 3.41,
}

# Tax data (OECD 2024 / country tax authorities)
TAX_DATA = {
    "China":       {"corp": 25.0, "tariff": 7.5,  "vat": 13.0, "complexity": "high"},
    "India":       {"corp": 25.17,"tariff": 13.8, "vat": 18.0, "complexity": "high"},
    "Vietnam":     {"corp": 20.0, "tariff": 9.4,  "vat": 10.0, "complexity": "medium"},
    "Taiwan":      {"corp": 20.0, "tariff": 6.1,  "vat": 5.0,  "complexity": "low"},
    "South Korea": {"corp": 24.0, "tariff": 13.9, "vat": 10.0, "complexity": "medium"},
    "Germany":     {"corp": 29.9, "tariff": 4.2,  "vat": 19.0, "complexity": "medium"},
    "Japan":       {"corp": 29.74,"tariff": 4.0,  "vat": 10.0, "complexity": "medium"},
    "USA":         {"corp": 21.0, "tariff": 3.4,  "vat": 0.0,  "complexity": "low"},
    "Malaysia":    {"corp": 24.0, "tariff": 6.1,  "vat": 8.0,  "complexity": "low"},
    "Mexico":      {"corp": 30.0, "tariff": 7.0,  "vat": 16.0, "complexity": "high"},
    "Brazil":      {"corp": 34.0, "tariff": 13.4, "vat": 17.0, "complexity": "high"},
    "Bangladesh":  {"corp": 27.5, "tariff": 14.8, "vat": 15.0, "complexity": "high"},
    "Indonesia":   {"corp": 22.0, "tariff": 7.1,  "vat": 11.0, "complexity": "medium"},
    "Thailand":    {"corp": 20.0, "tariff": 10.5, "vat": 7.0,  "complexity": "medium"},
}

# Shipping data (UNCTAD / port operator data 2023-24)
SHIPPING_DATA = {
    "China":       {"days": 21, "cost_kg": 2.80, "port_eff": 7.8, "customs_days": 3, "issues": ["port congestion","US tariff risk","lunar new year shutdowns"]},
    "India":       {"days": 25, "cost_kg": 3.10, "port_eff": 5.9, "customs_days": 6, "issues": ["customs delays","infrastructure bottlenecks","monsoon disruption"]},
    "Vietnam":     {"days": 20, "cost_kg": 2.60, "port_eff": 6.1, "customs_days": 4, "issues": ["port capacity limits","typhoon risk","labor shortage"]},
    "Taiwan":      {"days": 18, "cost_kg": 2.50, "port_eff": 7.4, "customs_days": 2, "issues": ["strait tension risk","earthquake risk","semiconductor dependency"]},
    "South Korea": {"days": 17, "cost_kg": 2.40, "port_eff": 8.0, "customs_days": 2, "issues": ["DPRK geopolitical risk","port labor strikes"]},
    "Germany":     {"days": 12, "cost_kg": 3.80, "port_eff": 8.7, "customs_days": 1, "issues": ["high labor costs","Rhine low water risk"]},
    "Japan":       {"days": 16, "cost_kg": 2.90, "port_eff": 8.2, "customs_days": 2, "issues": ["earthquake/tsunami risk","aging workforce"]},
    "USA":         {"days": 8,  "cost_kg": 3.50, "port_eff": 7.2, "customs_days": 2, "issues": ["high labor costs","West Coast port strikes","inland freight costs"]},
    "Malaysia":    {"days": 18, "cost_kg": 2.30, "port_eff": 7.1, "customs_days": 3, "issues": ["flood risk","energy costs"]},
    "Mexico":      {"days": 14, "cost_kg": 2.60, "port_eff": 5.8, "customs_days": 5, "issues": ["security concerns","customs corruption","infrastructure gaps"]},
    "Brazil":      {"days": 22, "cost_kg": 3.20, "port_eff": 5.2, "customs_days": 8, "issues": ["bureaucratic delays","port congestion","political instability"]},
    "Bangladesh":  {"days": 28, "cost_kg": 2.10, "port_eff": 4.8, "customs_days": 9, "issues": ["floods","political unrest","infrastructure"]},
    "Indonesia":   {"days": 22, "cost_kg": 2.70, "port_eff": 5.5, "customs_days": 6, "issues": ["inter-island logistics","customs delays","port congestion"]},
    "Thailand":    {"days": 19, "cost_kg": 2.50, "port_eff": 6.3, "customs_days": 4, "issues": ["political risk","flood risk"]},
}


# ---------------------------------------------------------------------------
# Wikidata SPARQL — live supplier fetch (no API key required)
# ---------------------------------------------------------------------------

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# Wikidata country QIDs for our 14 countries
COUNTRY_QIDS: dict[str, str] = {
    "Q148": "China",
    "Q668": "India",
    "Q881": "Vietnam",
    "Q865": "Taiwan",
    "Q884": "South Korea",
    "Q183": "Germany",
    "Q17":  "Japan",
    "Q30":  "USA",
    "Q833": "Malaysia",
    "Q96":  "Mexico",
    "Q155": "Brazil",
    "Q902": "Bangladesh",
    "Q252": "Indonesia",
    "Q869": "Thailand",
}

# Additional country-name aliases Wikidata may return
_COUNTRY_ALIASES: dict[str, str] = {
    "People's Republic of China": "China",
    "Republic of China": "Taiwan",
    "Republic of Korea": "South Korea",
    "Korea": "South Korea",
    "Federal Republic of Germany": "Germany",
    "United States of America": "USA",
    "United States": "USA",
}

# Cost tier by country (high = cheap supplier, low = expensive)
_COUNTRY_COST_TIER: dict[str, str] = {
    "China": "high", "India": "high", "Vietnam": "high", "Bangladesh": "high",
    "Indonesia": "high", "Thailand": "high", "Mexico": "medium",
    "Malaysia": "medium", "Brazil": "medium",
    "Taiwan": "medium", "South Korea": "medium",
    "Japan": "low", "Germany": "low", "USA": "low",
}

# Wikidata class QIDs to query per industry (tries each class in order)
# "p31" = instance-of QIDs; "p452" = P452 industry-property QIDs;
# "keywords" = fallback text search on P452 label (most robust, slightly slower)
# "tier" = supply chain position: "Raw Materials" | "Components" | "Manufacturing"
WIKIDATA_INDUSTRIES: list[dict] = [
    # ── Components / Manufacturer tier ──────────────────────────────
    {"industry": "Electronics",     "tier": "Components",    "p31": ["Q1297980", "Q210112"],     "p452": ["Q11650"],    "keywords": ["electronics"],                   "target": 10, "min_sl": 4},
    {"industry": "Manufacturing",   "tier": "Components",    "p31": ["Q216786", "Q13235160"],    "p452": ["Q8205328"],  "keywords": ["manufacturing", "industrial"],   "target": 8,  "min_sl": 4},
    {"industry": "Automotive",      "tier": "Components",    "p31": ["Q190604", "Q786820"],      "p452": ["Q1361984"],  "keywords": ["automotive", "automobile"],      "target": 7,  "min_sl": 4},
    {"industry": "Pharmaceuticals", "tier": "Components",    "p31": [],                           "p452": [],            "keywords": ["pharmaceutical"],               "target": 6,  "min_sl": 3},
    {"industry": "Textiles",        "tier": "Components",    "p31": ["Q190716"],                  "p452": ["Q28823"],    "keywords": ["textile", "apparel"],           "target": 5,  "min_sl": 3},
    {"industry": "Food & Beverage", "tier": "Components",    "p31": ["Q1141470"],                 "p452": ["Q1589726"],  "keywords": ["food", "beverage"],             "target": 5,  "min_sl": 3},
    {"industry": "Chemical",        "tier": "Components",    "p31": ["Q899523", "Q170790"],       "p452": ["Q43004"],    "keywords": ["chemical"],                     "target": 4,  "min_sl": 3},
    {"industry": "Aerospace",       "tier": "Components",    "p31": [],                           "p452": [],            "keywords": ["aerospace", "aviation"],        "target": 4,  "min_sl": 3},
    {"industry": "Energy",          "tier": "Components",    "p31": ["Q1651599", "Q891723"],      "p452": ["Q12748"],    "keywords": ["energy", "renewable"],          "target": 4,  "min_sl": 3},
    # Raw Materials tier uses curated list below (keyword SPARQL too slow on free Wikidata endpoint)
]

# ---------------------------------------------------------------------------
# Curated Raw Materials tier — real upstream feedstock / material companies
# (These are always loaded; avoids slow keyword-based SPARQL queries)
# ---------------------------------------------------------------------------
RAW_MATERIALS_SUPPLIERS = [
    # ── Electronics — Silicon / Semiconductor materials ──────────────
    {"name": "Shin-Etsu Chemical",           "country": "Japan",       "industry": "Electronics",     "tier": "Raw Materials"},
    {"name": "Sumco Corporation",            "country": "Japan",       "industry": "Electronics",     "tier": "Raw Materials"},
    {"name": "Wacker Chemie AG",             "country": "Germany",     "industry": "Electronics",     "tier": "Raw Materials"},
    {"name": "SK Siltron",                   "country": "South Korea", "industry": "Electronics",     "tier": "Raw Materials"},
    {"name": "Siltronic AG",                 "country": "Germany",     "industry": "Electronics",     "tier": "Raw Materials"},
    # ── Textiles — Fiber / Yarn feedstock ────────────────────────────
    {"name": "Indorama Ventures",            "country": "Thailand",    "industry": "Textiles",        "tier": "Raw Materials"},
    {"name": "Toray Industries",             "country": "Japan",       "industry": "Textiles",        "tier": "Raw Materials"},
    {"name": "Teijin Limited",               "country": "Japan",       "industry": "Textiles",        "tier": "Raw Materials"},
    {"name": "Reliance Textiles Division",   "country": "India",       "industry": "Textiles",        "tier": "Raw Materials"},
    {"name": "Zhejiang Hengli Petrochemical","country": "China",       "industry": "Textiles",        "tier": "Raw Materials"},
    # ── Pharmaceuticals — Active Pharmaceutical Ingredients ──────────
    {"name": "BASF Pharma Chemicals",        "country": "Germany",     "industry": "Pharmaceuticals", "tier": "Raw Materials"},
    {"name": "Dr. Reddy's API Division",     "country": "India",       "industry": "Pharmaceuticals", "tier": "Raw Materials"},
    {"name": "Zhejiang Medicine Co.",        "country": "China",       "industry": "Pharmaceuticals", "tier": "Raw Materials"},
    {"name": "Divi's Laboratories",          "country": "India",       "industry": "Pharmaceuticals", "tier": "Raw Materials"},
    # ── Chemical — Petrochemicals / Feedstock ────────────────────────
    {"name": "Sinopec Chemicals",            "country": "China",       "industry": "Chemical",        "tier": "Raw Materials"},
    {"name": "LG Chem Petrochemicals",       "country": "South Korea", "industry": "Chemical",        "tier": "Raw Materials"},
    {"name": "PTT Global Chemical",          "country": "Thailand",    "industry": "Chemical",        "tier": "Raw Materials"},
    {"name": "Reliance Industries",          "country": "India",       "industry": "Chemical",        "tier": "Raw Materials"},
    # ── Manufacturing — Steel / Metals ───────────────────────────────
    {"name": "POSCO",                        "country": "South Korea", "industry": "Manufacturing",   "tier": "Raw Materials"},
    {"name": "Nippon Steel Corporation",     "country": "Japan",       "industry": "Manufacturing",   "tier": "Raw Materials"},
    {"name": "Tata Steel",                   "country": "India",       "industry": "Manufacturing",   "tier": "Raw Materials"},
    {"name": "Baoshan Iron & Steel",         "country": "China",       "industry": "Manufacturing",   "tier": "Raw Materials"},
    {"name": "ThyssenKrupp Materials",       "country": "Germany",     "industry": "Manufacturing",   "tier": "Raw Materials"},
    # ── Aerospace — Specialty Materials ──────────────────────────────
    {"name": "Toray Carbon Fiber",           "country": "Japan",       "industry": "Aerospace",       "tier": "Raw Materials"},
    {"name": "SGL Carbon SE",                "country": "Germany",     "industry": "Aerospace",       "tier": "Raw Materials"},
    {"name": "UACJ Corporation",             "country": "Japan",       "industry": "Aerospace",       "tier": "Raw Materials"},
]


def _normalize_country(label: str) -> str | None:
    """Map a Wikidata country label to our canonical country name."""
    for canonical in COUNTRIES:
        if canonical.lower() == label.lower() or canonical.lower() in label.lower():
            return canonical
    return _COUNTRY_ALIASES.get(label)


def _derive_metrics(country: str) -> tuple[float, int, str]:
    """Derive reliability %, delivery days, cost tier from World Bank LPI data."""
    lpi = LPI_2023.get(country, 3.0)
    # LPI 2.5-4.3 → roughly 62-97% reliability
    base_rel = 40.0 + (lpi * 14.0)
    reliability = round(min(99.0, max(58.0, base_rel + random.uniform(-7.0, 5.0))), 1)
    base_days = SHIPPING_DATA.get(country, {}).get("days", 20)
    delivery = max(7, base_days + random.randint(-3, 6))
    cost = _COUNTRY_COST_TIER.get(country, "medium")
    return reliability, delivery, cost


def fetch_wikidata_suppliers() -> list[dict]:
    """
    Query Wikidata SPARQL for real-world companies grouped by industry.
    Derives reliability/delivery/cost metrics from World Bank LPI data.
    Returns [] on failure (caller should fall back to FALLBACK_SUPPLIERS).
    """
    country_filter = ", ".join(f"wd:{q}" for q in COUNTRY_QIDS)
    results: list[dict] = []
    seen: set[str] = set()

    print("\n  Querying Wikidata SPARQL for live supplier companies...")

    for cfg in WIKIDATA_INDUSTRIES:
        industry = cfg["industry"]
        tier = cfg["tier"]
        target = cfg["target"]
        min_sl = cfg["min_sl"]
        found: list[dict] = []

        # Build query variants: (predicate, QID) pairs to try in order,
        # followed by a keyword-based text search as final fallback
        query_variants: list[tuple[str, str]] = []
        for qid in cfg.get("p31", []):
            query_variants.append(("wdt:P31", qid))
        for qid in cfg.get("p452", []):
            query_variants.append(("wdt:P452", qid))

        for pred, qid in query_variants:
            if len(found) >= target:
                break

            sparql = (
                "SELECT DISTINCT ?companyLabel ?countryLabel WHERE {\n"
                f"  ?company {pred} wd:{qid} ;\n"
                f"           wdt:P17 ?country .\n"
                f"  FILTER(?country IN ({country_filter}))\n"
                "  ?company wikibase:sitelinks ?sl .\n"
                f"  FILTER(?sl > {min_sl})\n"
                "  SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" . }\n"
                "}\n"
                "ORDER BY DESC(?sl) ?companyLabel\n"
                "LIMIT 100\n"
            )

            try:
                with httpx.Client(
                    timeout=30.0,
                    headers={
                        "User-Agent": "SentriChain-RiskTool/1.0 (supply-chain-risk; https://github.com/sentrichain) httpx/0.27",
                        "Accept": "application/sparql-results+json",
                    },
                ) as c:
                    r = c.post(
                        WIKIDATA_ENDPOINT,
                        data={"query": sparql},
                    )
                if r.status_code != 200:
                    print(f"    ⚠ HTTP {r.status_code} for {industry}/{qid}")
                    continue
                rows = r.json().get("results", {}).get("bindings", [])
            except Exception as exc:
                print(f"    ⚠ {industry}/{qid}: {exc}")
                continue

            for row in rows:
                if len(found) >= target:
                    break
                name = row.get("companyLabel", {}).get("value", "")
                country_label = row.get("countryLabel", {}).get("value", "")
                if not name or (name.startswith("Q") and name[1:].isdigit()):
                    continue
                if name in seen:
                    continue
                country = _normalize_country(country_label)
                if not country or country not in COUNTRIES:
                    continue
                reliability, delivery, cost = _derive_metrics(country)
                found.append({"name": name, "country": country, "industry": industry, "tier": tier,
                              "reliability": reliability, "delivery": delivery, "cost": cost})
                seen.add(name)

        # Keyword fallback: search by P452 label text (catches industries where QID enumeration fails)
        if len(found) < target:
            for kw in cfg.get("keywords", []):
                if len(found) >= target:
                    break
                kw_filter = " || ".join(
                    f'CONTAINS(LCASE(?indLabel), "{k}")' for k in [kw]
                )
                sparql = (
                    "SELECT DISTINCT ?companyLabel ?countryLabel WHERE {\n"
                    "  ?company wdt:P17 ?country ;\n"
                    "           wdt:P452 ?ind .\n"
                    f"  FILTER(?country IN ({country_filter}))\n"
                    "  ?ind rdfs:label ?indLabel .\n"
                    "  FILTER(LANG(?indLabel) = \"en\")\n"
                    f"  FILTER({kw_filter})\n"
                    "  ?company wikibase:sitelinks ?sl .\n"
                    f"  FILTER(?sl > {min_sl})\n"
                    "  SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" . }\n"
                    "}\n"
                    "ORDER BY DESC(?sl) ?companyLabel\n"
                    "LIMIT 100\n"
                )
                try:
                    with httpx.Client(
                        timeout=35.0,
                        headers={
                            "User-Agent": "SentriChain-RiskTool/1.0 (supply-chain-risk; https://github.com/sentrichain) httpx/0.27",
                            "Accept": "application/sparql-results+json",
                        },
                    ) as c:
                        r = c.post(WIKIDATA_ENDPOINT, data={"query": sparql})
                    if r.status_code != 200:
                        continue
                    rows = r.json().get("results", {}).get("bindings", [])
                except BaseException:
                    continue
                for row in rows:
                    if len(found) >= target:
                        break
                    name = row.get("companyLabel", {}).get("value", "")
                    country_label = row.get("countryLabel", {}).get("value", "")
                    if not name or (name.startswith("Q") and name[1:].isdigit()):
                        continue
                    if name in seen:
                        continue
                    country = _normalize_country(country_label)
                    if not country or country not in COUNTRIES:
                        continue
                    reliability, delivery, cost = _derive_metrics(country)
                    found.append({"name": name, "country": country, "industry": industry, "tier": tier,
                                  "reliability": reliability, "delivery": delivery, "cost": cost})
                    seen.add(name)

        print(f"    {industry}: {len(found)} suppliers")
        results.extend(found)
        time.sleep(0.8)  # be polite to Wikidata rate limiter

    if len(results) < 25:
        print(f"  ⚠ Only {len(results)} live results — will use fallback list")
        return []

    print(f"  ✓ {len(results)} suppliers fetched from Wikidata")
    return results


# ---------------------------------------------------------------------------
# Fallback supplier data (used when Wikidata is unreachable)
# ---------------------------------------------------------------------------

FALLBACK_SUPPLIERS = [
    # ── Electronics ─────────────────────────────────────────────────
    {"name": "Foxconn Industrial Internet (Shenzhen)", "country": "China",       "industry": "Electronics", "reliability": 74.0, "delivery": 22, "cost": "high"},
    {"name": "BYD Electronic Components",              "country": "China",       "industry": "Electronics", "reliability": 71.0, "delivery": 24, "cost": "high"},
    {"name": "Longhua Precision Manufacturing",        "country": "China",       "industry": "Manufacturing", "reliability": 69.0, "delivery": 26, "cost": "high"},
    {"name": "Taiwan Semiconductor Supply Chain",      "country": "Taiwan",      "industry": "Electronics", "reliability": 94.0, "delivery": 13, "cost": "medium"},
    {"name": "Delta Electronics Components",           "country": "Taiwan",      "industry": "Electronics", "reliability": 92.0, "delivery": 14, "cost": "medium"},
    {"name": "Samsung Electro-Mechanics",              "country": "South Korea", "industry": "Electronics", "reliability": 93.0, "delivery": 13, "cost": "medium"},
    {"name": "LG Innotek Industrial",                  "country": "South Korea", "industry": "Electronics", "reliability": 91.0, "delivery": 14, "cost": "medium"},
    {"name": "Murata Manufacturing Supply",            "country": "Japan",       "industry": "Electronics", "reliability": 95.0, "delivery": 14, "cost": "medium"},
    {"name": "Penang Advanced Electronics",            "country": "Malaysia",    "industry": "Electronics", "reliability": 86.0, "delivery": 17, "cost": "low"},
    {"name": "Saigon Hi-Tech Electronics",             "country": "Vietnam",     "industry": "Electronics", "reliability": 88.0, "delivery": 15, "cost": "low"},
    # ── Manufacturing / Automotive ───────────────────────────────────
    {"name": "Bosch Industrial Sensors GmbH",          "country": "Germany",     "industry": "Manufacturing", "reliability": 97.0, "delivery": 10, "cost": "low"},
    {"name": "Siemens Component Supply AG",            "country": "Germany",     "industry": "Manufacturing", "reliability": 96.0, "delivery": 11, "cost": "low"},
    {"name": "Bharat Forge Industrial Division",       "country": "India",       "industry": "Automotive", "reliability": 87.0, "delivery": 17, "cost": "medium"},
    {"name": "Motherson Sumi Wiring Systems",          "country": "India",       "industry": "Automotive", "reliability": 81.0, "delivery": 20, "cost": "medium"},
    {"name": "Monterrey Precision Manufacturing",      "country": "Mexico",      "industry": "Automotive", "reliability": 78.0, "delivery": 15, "cost": "medium"},
    {"name": "Tijuana Industrial Components SA",       "country": "Mexico",      "industry": "Automotive", "reliability": 76.0, "delivery": 16, "cost": "medium"},
    {"name": "Kyocera Industrial Components",          "country": "Japan",       "industry": "Manufacturing", "reliability": 94.0, "delivery": 15, "cost": "medium"},
    {"name": "Kulim Hi-Tech Industrial Park",          "country": "Malaysia",    "industry": "Manufacturing", "reliability": 84.0, "delivery": 18, "cost": "low"},
    # ── Pharmaceuticals ─────────────────────────────────────────────
    {"name": "Sun Pharma API Division",                "country": "India",       "industry": "Pharmaceuticals", "reliability": 89.0, "delivery": 18, "cost": "low"},
    {"name": "Aurobindo Pharma Ingredients",           "country": "India",       "industry": "Pharmaceuticals", "reliability": 86.0, "delivery": 21, "cost": "low"},
    {"name": "CSPC Pharmaceutical Supply",             "country": "China",       "industry": "Pharmaceuticals", "reliability": 78.0, "delivery": 23, "cost": "medium"},
    {"name": "Evonik Pharma Excipients GmbH",          "country": "Germany",     "industry": "Pharmaceuticals", "reliability": 97.0, "delivery": 10, "cost": "medium"},
    {"name": "Merck KGaA Lab Materials",               "country": "Germany",     "industry": "Pharmaceuticals", "reliability": 96.0, "delivery": 11, "cost": "medium"},
    # ── Textiles ────────────────────────────────────────────────────
    {"name": "Arvind Textiles Export",                 "country": "India",       "industry": "Textiles", "reliability": 84.0, "delivery": 22, "cost": "low"},
    {"name": "Welspun Synthetic Fibers",               "country": "India",       "industry": "Textiles", "reliability": 82.0, "delivery": 24, "cost": "low"},
    {"name": "DBL Group Textiles",                     "country": "Bangladesh",  "industry": "Textiles", "reliability": 71.0, "delivery": 30, "cost": "low"},
    {"name": "Ha Nam Silk & Fiber Co.",                "country": "Vietnam",     "industry": "Textiles", "reliability": 80.0, "delivery": 20, "cost": "low"},
    {"name": "Toray Advanced Fibers",                  "country": "Japan",       "industry": "Textiles", "reliability": 95.0, "delivery": 16, "cost": "medium"},
    {"name": "Indorama Synthetics",                    "country": "Indonesia",   "industry": "Textiles", "reliability": 77.0, "delivery": 25, "cost": "low"},
    # ── Food & Beverage ─────────────────────────────────────────────
    {"name": "ITC Agri & Food Division",               "country": "India",       "industry": "Food & Beverage", "reliability": 85.0, "delivery": 19, "cost": "low"},
    {"name": "Wilmar Food Ingredients",                "country": "Malaysia",    "industry": "Food & Beverage", "reliability": 83.0, "delivery": 17, "cost": "low"},
    {"name": "Thai Agro Exchange",                     "country": "Thailand",    "industry": "Food & Beverage", "reliability": 80.0, "delivery": 20, "cost": "low"},
    {"name": "Chr. Hansen Germany GmbH",               "country": "Germany",     "industry": "Food & Beverage", "reliability": 96.0, "delivery": 11, "cost": "medium"},
    # ── Chemical ────────────────────────────────────────────────────
    {"name": "BASF Chemical Intermediates",            "country": "Germany",     "industry": "Chemical", "reliability": 97.0, "delivery": 10, "cost": "medium"},
    {"name": "Sinopec Chemical Supply",                "country": "China",       "industry": "Chemical", "reliability": 76.0, "delivery": 23, "cost": "medium"},
    {"name": "Tata Chemicals Industrial",              "country": "India",       "industry": "Chemical", "reliability": 85.0, "delivery": 19, "cost": "low"},
    # ── Aerospace ───────────────────────────────────────────────────
    {"name": "Mitsubishi Aerospace Materials",         "country": "Japan",       "industry": "Aerospace", "reliability": 96.0, "delivery": 18, "cost": "high"},
    {"name": "Premium Aerotec GmbH",                   "country": "Germany",     "industry": "Aerospace", "reliability": 97.0, "delivery": 12, "cost": "high"},
    # ── Energy ──────────────────────────────────────────────────────
    {"name": "Longi Solar Components",                 "country": "China",       "industry": "Energy", "reliability": 80.0, "delivery": 22, "cost": "medium"},
    {"name": "Siemens Energy Supply",                  "country": "Germany",     "industry": "Energy", "reliability": 96.0, "delivery": 11, "cost": "high"},
    {"name": "Suzlon Wind Components",                 "country": "India",       "industry": "Energy", "reliability": 82.0, "delivery": 20, "cost": "low"},
]

# Equipment categories, keyed by industry
EQUIPMENT_CATEGORIES_BY_INDUSTRY: dict[str, list[dict]] = {
    "Electronics": [
        {"name": "PCB Assembly",          "base_cost": 45000,  "base_lead": 45},
        {"name": "Semiconductor Module",  "base_cost": 120000, "base_lead": 60},
        {"name": "Display Panel",         "base_cost": 55000,  "base_lead": 42},
        {"name": "Battery Module",        "base_cost": 95000,  "base_lead": 58},
        {"name": "Sensor Package",        "base_cost": 32000,  "base_lead": 35},
        {"name": "Microcontroller Unit",  "base_cost": 28000,  "base_lead": 30},
    ],
    "Manufacturing": [
        {"name": "Precision Casting",     "base_cost": 28000,  "base_lead": 30},
        {"name": "Industrial Motor",      "base_cost": 85000,  "base_lead": 55},
        {"name": "Hydraulic Assembly",    "base_cost": 65000,  "base_lead": 50},
        {"name": "Machine Tool Component","base_cost": 42000,  "base_lead": 38},
        {"name": "Structural Casting",    "base_cost": 22000,  "base_lead": 28},
        {"name": "Wiring Harness",        "base_cost": 18000,  "base_lead": 25},
    ],
    "Automotive": [
        {"name": "Brake Assembly",        "base_cost": 35000,  "base_lead": 35},
        {"name": "Wiring Harness",        "base_cost": 18000,  "base_lead": 25},
        {"name": "Aluminum Casting",      "base_cost": 26000,  "base_lead": 30},
        {"name": "Hydraulic Actuator",    "base_cost": 48000,  "base_lead": 40},
        {"name": "Rubber Seals Batch",    "base_cost": 12000,  "base_lead": 20},
        {"name": "ECU Sensor Module",     "base_cost": 52000,  "base_lead": 45},
    ],
    "Pharmaceuticals": [
        {"name": "Active Pharmaceutical Ingredient (API) Batch",  "base_cost": 180000, "base_lead": 60},
        {"name": "Excipient Supply",       "base_cost": 45000,  "base_lead": 30},
        {"name": "Sterile Vial Set",       "base_cost": 28000,  "base_lead": 25},
        {"name": "Lab Reagent Kit",        "base_cost": 15000,  "base_lead": 20},
        {"name": "Filtration Membrane",    "base_cost": 22000,  "base_lead": 22},
        {"name": "Biologic Raw Material",  "base_cost": 220000, "base_lead": 70},
    ],
    "Textiles": [
        {"name": "Synthetic Fiber Bale",   "base_cost": 14000,  "base_lead": 25},
        {"name": "Cotton Fiber Bale",      "base_cost": 12000,  "base_lead": 22},
        {"name": "Dye & Chemical Batch",   "base_cost": 8000,   "base_lead": 18},
        {"name": "Industrial Thread Spool","base_cost": 6000,   "base_lead": 15},
        {"name": "Elastane Yarn Batch",    "base_cost": 18000,  "base_lead": 28},
        {"name": "Fabric Finishing Chemical","base_cost":10000, "base_lead": 20},
    ],
    "Food & Beverage": [
        {"name": "Agricultural Commodity Batch","base_cost": 25000, "base_lead": 20},
        {"name": "Flavoring Agent Supply", "base_cost": 18000,  "base_lead": 18},
        {"name": "Enzyme Culture Kit",     "base_cost": 32000,  "base_lead": 22},
        {"name": "Food-Grade Packaging",   "base_cost": 12000,  "base_lead": 16},
        {"name": "Preservative Batch",     "base_cost": 9000,   "base_lead": 15},
        {"name": "Edible Oil Supply",      "base_cost": 21000,  "base_lead": 18},
    ],
    "Chemical": [
        {"name": "Industrial Solvent Drum", "base_cost": 22000,  "base_lead": 25},
        {"name": "Catalyst Batch",         "base_cost": 85000,  "base_lead": 40},
        {"name": "Specialty Gas Cylinder", "base_cost": 15000,  "base_lead": 20},
        {"name": "Petrochemical Feedstock","base_cost": 55000,  "base_lead": 30},
        {"name": "Surfactant Batch",       "base_cost": 18000,  "base_lead": 22},
        {"name": "Lab Reagent Supply",     "base_cost": 12000,  "base_lead": 18},
    ],
    "Aerospace": [
        {"name": "Titanium Alloy Sheet",   "base_cost": 280000, "base_lead": 80},
        {"name": "Carbon Fiber Panel",     "base_cost": 220000, "base_lead": 70},
        {"name": "Precision Fastener Set", "base_cost": 45000,  "base_lead": 40},
        {"name": "Avionics Sub-assembly",  "base_cost": 380000, "base_lead": 90},
        {"name": "Thermal Barrier Coating","base_cost": 65000,  "base_lead": 50},
        {"name": "High-Temp Alloy Forging","base_cost": 195000, "base_lead": 75},
    ],
    "Energy": [
        {"name": "Solar Module Batch",     "base_cost": 120000, "base_lead": 45},
        {"name": "Turbine Blade",          "base_cost": 250000, "base_lead": 75},
        {"name": "Cable Drum",             "base_cost": 38000,  "base_lead": 30},
        {"name": "Transformer Unit",       "base_cost": 180000, "base_lead": 60},
        {"name": "Pump Assembly",          "base_cost": 55000,  "base_lead": 40},
        {"name": "Insulation Panel",       "base_cost": 22000,  "base_lead": 25},
    ],
}
# Fallback for any unlisted industry
EQUIPMENT_CATEGORIES_BY_INDUSTRY["Other"] = EQUIPMENT_CATEGORIES_BY_INDUSTRY["Manufacturing"]
EQUIPMENT_CATEGORIES_BY_INDUSTRY["Logistics"] = EQUIPMENT_CATEGORIES_BY_INDUSTRY["Manufacturing"]
EQUIPMENT_CATEGORIES_BY_INDUSTRY["Construction"] = EQUIPMENT_CATEGORIES_BY_INDUSTRY["Manufacturing"]

# Delay probability and magnitude per country (based on World Bank LPI + Sourcemap data)
DELAY_PROFILE = {
    "China":       {"delay_prob": 0.38, "avg_delay": 8,  "max_delay": 35},
    "India":       {"delay_prob": 0.42, "avg_delay": 10, "max_delay": 40},
    "Vietnam":     {"delay_prob": 0.30, "avg_delay": 7,  "max_delay": 28},
    "Taiwan":      {"delay_prob": 0.18, "avg_delay": 4,  "max_delay": 18},
    "South Korea": {"delay_prob": 0.20, "avg_delay": 4,  "max_delay": 20},
    "Germany":     {"delay_prob": 0.10, "avg_delay": 2,  "max_delay": 10},
    "Japan":       {"delay_prob": 0.14, "avg_delay": 3,  "max_delay": 14},
    "USA":         {"delay_prob": 0.22, "avg_delay": 4,  "max_delay": 20},
    "Malaysia":    {"delay_prob": 0.28, "avg_delay": 6,  "max_delay": 22},
    "Mexico":      {"delay_prob": 0.36, "avg_delay": 9,  "max_delay": 32},
    "Brazil":      {"delay_prob": 0.45, "avg_delay": 12, "max_delay": 45},
    "Bangladesh":  {"delay_prob": 0.50, "avg_delay": 15, "max_delay": 55},
    "Indonesia":   {"delay_prob": 0.40, "avg_delay": 10, "max_delay": 38},
    "Thailand":    {"delay_prob": 0.32, "avg_delay": 7,  "max_delay": 26},
}


def generate_schedules(supplier_id: int, country: str, industry: str, n: int = 25) -> list[dict]:
    """Generate realistic schedule records based on country delay statistics and industry."""
    profile = DELAY_PROFILE.get(country, {"delay_prob": 0.30, "avg_delay": 7, "max_delay": 30})
    categories = EQUIPMENT_CATEGORIES_BY_INDUSTRY.get(industry, EQUIPMENT_CATEGORIES_BY_INDUSTRY["Manufacturing"])
    schedules = []
    today = date.today()

    for i in range(n):
        cat = random.choice(categories)
        lead_days = cat["base_lead"] + random.randint(-5, 10)
        planned = today - timedelta(days=random.randint(14, 400)) + timedelta(days=lead_days)

        is_delayed = random.random() < profile["delay_prob"]
        is_future = planned > today

        if is_future and not is_delayed:
            status = "on_time"
            actual = None
        elif is_delayed:
            delay_d = int(random.expovariate(1.0 / profile["avg_delay"]))
            delay_d = max(1, min(delay_d, profile["max_delay"]))
            actual_dt = planned + timedelta(days=delay_d)
            if actual_dt <= today:
                status = "delayed"
                actual = actual_dt
            else:
                status = "delayed"
                actual = None  # still incoming but already late
        else:
            status = "on_time"
            jitter = random.randint(-2, 2)
            actual = planned + timedelta(days=jitter)

        cost_var = random.uniform(0.88, 1.18)
        schedules.append({
            "supplier_id": supplier_id,
            "equipment_name": cat["name"],
            "planned_delivery_date": planned,
            "actual_delivery_date": actual,
            "status": status,
            "equipment_value": round(cat["base_cost"] * cost_var, 2),
        })

    return schedules


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=" * 60)
    print("SentriChain Real Data Refresh")
    print("=" * 60)

    # ── 1. CountryRisk: pull live WGI + GDELT ──────────────────────
    print("\n[1/4] Fetching World Bank WGI Political Stability...")
    db.query(CountryRisk).delete()
    db.commit()

    for country, iso in COUNTRIES.items():
        # WGI PV.EST: political stability score -2.5 to +2.5
        pv = wb_fetch("PV.EST", iso, years=5)
        if pv is not None:
            risk_score = round(max(0.0, min(10.0, 5.0 - (2.0 * pv))), 2)
        else:
            risk_score = 5.0  # neutral fallback

        # GDELT headline (best effort)
        pv_str = f"{pv:.3f}" if pv is not None else "N/A"
        print(f"  {country}: WGI={pv_str} → risk={risk_score}  fetching GDELT...", end=" ")
        headline, source_url, event_count = fetch_gdelt_headline(country)
        print(f"events={event_count}")

        db.add(CountryRisk(
            country=country,
            risk_score=risk_score,
            headline=headline[:500] if headline else f"WGI Political Stability score: {risk_score:.1f}/10",
            source_url=source_url or f"https://data.worldbank.org/indicator/PV.EST?locations={iso}",
        ))

    db.commit()
    print("  ✓ Country risk data updated")

    # ── 2. CountryFactors: World Bank LPI + real tax/shipping data ──
    print("\n[2/4] Fetching World Bank LPI & building country factors...")
    db.query(CountryFactors).delete()
    db.commit()

    for country, iso in COUNTRIES.items():
        meta = COUNTRY_META[country]
        tax = TAX_DATA[country]
        ship = SHIPPING_DATA[country]

        # Live LPI overall score
        lpi = wb_fetch("LP.LPI.OVRL.XQ", iso, years=5) or LPI_2023.get(country, 3.0)
        # GDP growth
        gdp_g = wb_fetch("NY.GDP.PCAP.KD.ZG", iso, years=3) or 2.0
        # Infrastructure (road, port quality proxy via LPI infrastructure sub-index fallback)
        infra = wb_fetch("LP.LPI.INFR.XQ", iso, years=5) or (lpi * 0.9)
        # Labour cost index (GNI per capita PPP normalised, inverted to cost index)
        gni = wb_fetch("NY.GNP.PCAP.PP.CD", iso, years=3)
        if gni:
            labor_idx = round(min(100.0, max(5.0, gni / 1200.0)), 1)
        else:
            labor_idx = 40.0

        # Economy score from LPI (scale 1-5 → 0-10)
        economy_score = round((lpi / 5.0) * 10.0, 2)
        if economy_score >= 7.5:
            economy_label = "advanced"
        elif economy_score >= 5.5:
            economy_label = "emerging"
        else:
            economy_label = "developing"

        # Currency volatility heuristic
        if country in ("Germany", "USA", "Japan", "South Korea", "Taiwan"):
            cv = "low"
        elif country in ("China", "Malaysia", "Thailand", "Vietnam"):
            cv = "medium"
        else:
            cv = "high"

        transport_reliability = round(min(1.0, lpi / 5.0), 3)

        print(f"  {country}: LPI={lpi:.2f}, gdp_g={gdp_g:.1f}%, infra={infra:.2f}")

        db.add(CountryFactors(
            country=country,
            continent=meta["continent"],
            economy_score=economy_score,
            economy_label=economy_label,
            gdp_growth_pct=round(gdp_g, 2),
            currency=meta["currency"],
            currency_volatility=cv,
            corporate_tax_pct=tax["corp"],
            import_tariff_pct=tax["tariff"],
            vat_gst_pct=tax["vat"],
            tax_complexity=tax["complexity"],
            has_fta=meta["has_fta"],
            fta_partners=json.dumps(meta["fta"]),
            avg_shipping_days=ship["days"],
            shipping_cost_usd_per_kg=ship["cost_kg"],
            port_efficiency_score=ship["port_eff"],
            transport_reliability=transport_reliability,
            customs_clearance_days=ship["customs_days"],
            common_issues=json.dumps(ship["issues"]),
            political_stability=round(10.0 - (db.query(CountryRisk).filter_by(country=country).first().risk_score if db.query(CountryRisk).filter_by(country=country).first() else 5.0), 2),
            infrastructure_score=round(min(10.0, infra * 2.0), 2),
            labor_cost_index=labor_idx,
        ))

    db.commit()
    print("  ✓ Country factors updated (14 countries)")

    # ── 3. Suppliers + Schedules ────────────────────────────────────
    print("\n[3/4] Fetching live supplier data (Wikidata) + generating schedules...")
    # Migrate: add industry and supply_tier columns if they don't exist
    from sqlalchemy import text as _text
    try:
        db.execute(_text("ALTER TABLE suppliers ADD COLUMN industry VARCHAR"))
        db.commit()
    except Exception:
        pass  # Already exists
    try:
        db.execute(_text("ALTER TABLE suppliers ADD COLUMN supply_tier VARCHAR"))
        db.commit()
    except Exception:
        pass  # Already exists

    # Fetch BEFORE clearing DB so a crash/interrupt never leaves it empty
    try:
        live = fetch_wikidata_suppliers()
    except BaseException as exc:
        print(f"  ⚠ Wikidata fetch interrupted ({type(exc).__name__}): {exc}")
        live = []
    suppliers_to_load = live if live else FALLBACK_SUPPLIERS

    # Always append curated Raw Materials suppliers (with derived LPI-based metrics)
    raw_mats = []
    for s in RAW_MATERIALS_SUPPLIERS:
        rel, ddays, cost = _derive_metrics(s["country"])
        raw_mats.append({
            "name": s["name"], "country": s["country"],
            "industry": s["industry"], "tier": s["tier"],
            "reliability": rel, "delivery": ddays, "cost": cost,
        })
    suppliers_to_load = suppliers_to_load + raw_mats

    # Clear existing only after we have data ready to insert
    db.query(EquipmentSchedule).delete()
    db.query(Supplier).delete()
    db.commit()
    source_label = "Wikidata (live)" if live else "fallback list"
    print(f"  Using {source_label}: {len(suppliers_to_load)} suppliers")

    for i, s in enumerate(suppliers_to_load, start=1):
        sup = Supplier(
            id=i,
            supplier_name=s["name"],
            country=s["country"],
            industry=s["industry"],
            supply_tier=s.get("tier", "Components"),
            reliability_score=s["reliability"],
            average_delivery_time=s["delivery"],
            cost_competitiveness=s["cost"],
        )
        db.add(sup)
        db.flush()

        schedules = generate_schedules(i, s["country"], s["industry"], n=30)
        for sc in schedules:
            db.add(EquipmentSchedule(
                supplier_id=sc["supplier_id"],
                equipment_name=sc["equipment_name"],
                planned_delivery_date=sc["planned_delivery_date"],
                actual_delivery_date=sc["actual_delivery_date"],
                status=sc["status"],
                equipment_value=sc["equipment_value"],
            ))

    db.commit()
    print(f"  ✓ {len(suppliers_to_load)} suppliers ({source_label}), {len(suppliers_to_load) * 30} schedule records")

    # ── 4. Demo users ───────────────────────────────────────────────
    print("\n[4/4] Ensuring demo users exist...")
    for email, name, role, pw in [
        ("demo@sentrichain.com",  "Demo Analyst", "analyst", "Demo@2025"),
        ("admin@sentrichain.com", "Admin User",   "admin",   "Admin@2025"),
    ]:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            db.add(User(email=email, full_name=name, hashed_password=hashed, role=role, is_active=True))
    db.commit()
    print("  ✓ Demo users ready")

    db.close()
    print("\n" + "=" * 60)
    print("Refresh complete.")
    print("=" * 60)


if __name__ == "__main__":
    run()
