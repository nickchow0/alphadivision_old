import os
import requests

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"


def get_news(symbol: str, limit: int = 5) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/company-news",
        params={"symbol": symbol, "token": FINNHUB_API_KEY},
    )
    response.raise_for_status()
    articles = response.json()[:limit]
    return [{"headline": a["headline"], "summary": a["summary"]} for a in articles]
