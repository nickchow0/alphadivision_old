import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_prompt(symbol: str, price: float, indicators: dict, news: list[dict], macro: dict) -> str:
    news_text = "\n".join(f"- {a['headline']}: {a['summary']}" for a in news)
    return f"""You are a trading analyst. Based on the data below, respond with a JSON object:
{{"decision": "buy" | "sell" | "hold", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

Symbol: {symbol}
Current price: ${price:.2f}
RSI (14): {indicators.get("rsi", "N/A")}
SMA 20: {indicators.get("sma_20", "N/A")}
SMA 50: {indicators.get("sma_50", "N/A")}

Recent news:
{news_text}

Macro:
Fed funds rate: {macro.get("fed_funds_rate", "N/A")}%
CPI: {macro.get("cpi", "N/A")}

Respond with JSON only."""


def get_decision(symbol: str, price: float, indicators: dict, news: list[dict], macro: dict) -> dict:
    prompt = build_prompt(symbol, price, indicators, news, macro)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    return json.loads(response.content[0].text)
