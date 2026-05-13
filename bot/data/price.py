import os
import alpaca_trade_api as tradeapi
import pandas as pd
import pandas_ta as ta

api = tradeapi.REST(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
)


def get_bars(symbol: str, timeframe: str = "1Min", limit: int = 50) -> pd.DataFrame:
    bars = api.get_bars(symbol, timeframe, limit=limit).df
    bars.ta.rsi(append=True)
    bars.ta.sma(length=20, append=True)
    bars.ta.sma(length=50, append=True)
    return bars


def get_current_price(symbol: str) -> float:
    return float(api.get_latest_trade(symbol).price)
