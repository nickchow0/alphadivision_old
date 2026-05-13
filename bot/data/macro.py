import os
import requests

FRED_API_KEY = os.getenv("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_series(series_id: str) -> float:
    response = requests.get(
        BASE_URL,
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
    )
    response.raise_for_status()
    return float(response.json()["observations"][0]["value"])


def get_fed_funds_rate() -> float:
    return get_series("FEDFUNDS")


def get_cpi() -> float:
    return get_series("CPIAUCSL")
