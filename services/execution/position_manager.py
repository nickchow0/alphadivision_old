from shared.logger import get_logger

log = get_logger("execution")


def get_positions(api) -> dict:
    """
    Query Alpaca for all currently open positions.

    Called before every order to get fresh state — never uses a cached
    in-memory dict. This ensures the service doesn't place duplicate orders
    after a restart (startup reconciliation is implicit: just call this).

    Returns {symbol: qty} for each open position (e.g. {"AAPL": 5, "MSFT": 3}).
    """
    positions = api.list_positions()
    return {p.symbol: int(p.qty) for p in positions}


def get_portfolio_value(api) -> float:
    """
    Returns the total portfolio equity from Alpaca's account endpoint.

    Used for the 2% position sizing calculation. In paper trading mode,
    this reflects the paper account balance.
    """
    account = api.get_account()
    return float(account.equity)


def get_last_price(api, symbol: str) -> float:
    """
    Returns the most recent closing price for `symbol` from Alpaca.

    Uses a 1-minute bar with limit=1 to get the latest available price.
    Used for position sizing (buy) and realized P&L estimation (sell).

    Raises ValueError if no price data is available for the symbol.
    """
    bars_resp = api.get_bars(symbol, "1Min", limit=1)
    df = bars_resp.df
    if df.empty:
        raise ValueError(f"No price data available for {symbol}")
    return float(df["close"].iloc[-1])
