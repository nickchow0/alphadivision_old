MAX_POSITION_SIZE = 100      # max dollars per position
MIN_CONFIDENCE = 0.65        # minimum confidence to act on a decision
MAX_DAILY_LOSS = 500         # stop trading for the day if losses exceed this


def position_size(price: float, portfolio_value: float, risk_pct: float = 0.02) -> int:
    max_risk = portfolio_value * risk_pct
    qty = int(min(max_risk, MAX_POSITION_SIZE) / price)
    return max(qty, 1)


def should_act(confidence: float) -> bool:
    return confidence >= MIN_CONFIDENCE
