import anthropic

MODEL_HAIKU = "claude-haiku-4-5"
MODEL_SONNET = "claude-sonnet-4-5"

_MAX_TOKENS = 2048

# Forced tool use — Claude always calls this tool, guaranteeing structured output.
_DECISION_TOOL = {
    "name": "record_decision",
    "description": "Record the swing trading decision for this symbol.",
    "input_schema": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["buy", "sell", "hold"],
            },
            "confidence": {
                "type": "number",
                "description": "Confidence level between 0.0 and 1.0",
            },
            "reasoning": {
                "type": "string",
                "description": "1-2 sentence explanation",
            },
        },
        "required": ["decision", "confidence", "reasoning"],
    },
}


def build_prompt(snapshot: dict) -> str:
    """
    Build the analysis prompt from a market snapshot dict.

    Includes current price, technical indicators, recent news headlines
    (up to 5), and macro context. Asks for a structured JSON response
    with keys: decision, confidence, reasoning.
    """
    symbol = snapshot.get("symbol", "UNKNOWN")
    price = snapshot.get("price", 0)
    rsi = snapshot.get("rsi", 0)
    sma20 = snapshot.get("sma20", 0)
    sma50 = snapshot.get("sma50", 0)
    news = snapshot.get("news", [])
    macro = snapshot.get("macro", {})

    if news:
        news_lines = "\n".join(
            f"- {a.get('headline', 'No headline')}" for a in news[:5]
        )
    else:
        news_lines = "No recent news."

    macro_text = (
        f"Fed funds rate: {macro.get('fed_funds_rate', 'N/A')}%\n"
        f"CPI index: {macro.get('cpi', 'N/A')}"
    )

    return f"""You are a swing trading analyst for US equities. Analyze the following market data for {symbol} and make a trading decision.

Technical Indicators:
- Current price: ${price:.2f}
- RSI (14): {rsi:.1f}
- SMA (20): {sma20:.2f}
- SMA (50): {sma50:.2f}

Recent News Headlines (last 24 hours):
{news_lines}

Macro Context:
{macro_text}

Based on this data, provide a swing trading recommendation. Keep reasoning to 1-2 sentences."""


def call_claude(snapshot: dict, api_key: str, model: str = MODEL_HAIKU) -> dict:
    """
    Call Claude with the market snapshot and return a parsed decision dict.

    Parameters:
        snapshot: market snapshot dict (from stream:market_snapshot)
        api_key: Anthropic API key
        model: Claude model ID (default: MODEL_HAIKU)

    Returns a dict with keys: decision (str), confidence (float),
        reasoning (str), model (str).

    Raises ValueError if response is missing required fields or has invalid values.
    """
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(snapshot)

    message = client.messages.create(
        model=model,
        max_tokens=_MAX_TOKENS,
        tools=[_DECISION_TOOL],
        tool_choice={"type": "tool", "name": "record_decision"},
        messages=[{"role": "user", "content": prompt}],
        timeout=30.0,
    )

    # tool_choice forces content[0] to always be a ToolUseBlock; input is already a dict
    parsed = message.content[0].input

    for field in ("decision", "confidence", "reasoning"):
        if field not in parsed:
            raise ValueError(f"Claude response missing field '{field}': {parsed}")

    if parsed["decision"] not in ("buy", "sell", "hold"):
        raise ValueError(f"Invalid decision value '{parsed['decision']}' — must be buy, sell, or hold")

    parsed["confidence"] = float(parsed["confidence"])
    if not (0.0 <= parsed["confidence"] <= 1.0):
        raise ValueError(f"Confidence {parsed['confidence']} out of range [0.0, 1.0]")

    parsed["model"] = model
    return parsed
