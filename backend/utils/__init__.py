"""
Utils module — external data fetchers.

GDELT:      Free, no registration. Fetches geopolitical events per country.
World Bank WGI: Free REST API. Fetches Political Stability indicator (PV.EST).
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional

# Country ISO code mapping for World Bank API
COUNTRY_ISO = {
    "China": "CN",
    "India": "IN",
    "Vietnam": "VN",
    "Germany": "DE",
    "USA": "US",
    "United States": "US",
    "Japan": "JP",
    "South Korea": "KR",
    "Taiwan": "TW",
    "Mexico": "MX",
    "Brazil": "BR",
    "Bangladesh": "BD",
    "Indonesia": "ID",
    "Thailand": "TH",
    "Malaysia": "MY",
    "Singapore": "SG",
    "Russia": "RU",
    "Ukraine": "UA",
}


def fetch_gdelt_events(country: str, max_records: int = 10) -> dict:
    """
    Fetches recent geopolitical events mentioning a country from GDELT v2 REST API.
    No API key required. Free academic use.
    Returns: {events: [...], count: int, headline: str, source_url: str}
    Source: https://www.gdeltproject.org/
    """
    try:
        query = f"{country} supply chain trade disruption"
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={query.replace(' ', '%20')}"
            f"&mode=artlist&maxrecords={max_records}&format=json"
        )

        with httpx.Client(timeout=8.0) as client:
            response = client.get(url)

        if response.status_code != 200:
            return _gdelt_fallback(country)

        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            return _gdelt_fallback(country)

        top = articles[0]
        return {
            "events": [
                {"title": a.get("title", ""), "url": a.get("url", "")}
                for a in articles[:5]
            ],
            "count": len(articles),
            "headline": top.get("title", f"No recent events for {country}"),
            "source_url": top.get("url", ""),
        }

    except Exception:
        return _gdelt_fallback(country)


def _gdelt_fallback(country: str) -> dict:
    """Static fallback when GDELT is unreachable."""
    return {
        "events": [],
        "count": 0,
        "headline": f"No recent GDELT events retrieved for {country}",
        "source_url": "https://www.gdeltproject.org/",
    }


def fetch_wgi_risk_score(country: str) -> Optional[float]:
    """
    Fetches Political Stability & Absence of Violence (PV.EST) from World Bank WGI.
    Score range: roughly -2.5 (very unstable) to +2.5 (very stable).
    Normalized to 0–10 risk scale: risk = 5 - (2 * PV.EST), clamped [0, 10].
    Source: https://info.worldbank.org/governance/wgi/
    """
    iso = COUNTRY_ISO.get(country)
    if not iso:
        return None

    try:
        url = (
            f"https://api.worldbank.org/v2/country/{iso}"
            f"/indicator/PV.EST?format=json&mrv=1"
        )
        with httpx.Client(timeout=8.0) as client:
            response = client.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        # World Bank returns [{metadata}, [{value records}]]
        if len(data) < 2 or not data[1]:
            return None

        pv_est = data[1][0].get("value")
        if pv_est is None:
            return None

        # Convert PV.EST (-2.5 to +2.5) → risk (0 to 10)
        risk = max(0.0, min(10.0, 5.0 - (2.0 * float(pv_est))))
        return round(risk, 2)

    except Exception:
        return None

