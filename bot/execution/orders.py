import os
import alpaca_trade_api as tradeapi

api = tradeapi.REST(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
)


def get_position(symbol: str):
    try:
        return api.get_position(symbol)
    except Exception:
        return None


def place_order(symbol: str, qty: int, side: str):
    return api.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="market",
        time_in_force="day",
    )


def close_position(symbol: str):
    api.close_position(symbol)
