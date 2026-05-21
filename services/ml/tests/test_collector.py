"""Unit tests for collector.py — all external I/O is mocked."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure shared is on path
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from collector import collect_bars, _fetch_yfinance


def _make_df(n=10, start="2024-01-01"):
    """Build a minimal OHLCV DataFrame mimicking yfinance output."""
    idx = pd.date_range(start=start, periods=n, freq="B")
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(n)],
            "High": [102.0 + i for i in range(n)],
            "Low":  [98.0 + i for i in range(n)],
            "Close":[101.0 + i for i in range(n)],
            "Volume":[1_000_000 + i * 1000 for i in range(n)],
        },
        index=idx,
    )


def test_fetch_yfinance_returns_list_of_dicts():
    df = _make_df(5)
    with patch("collector.yf.download", return_value=df):
        bars = _fetch_yfinance("AAPL", date(2024, 1, 1), date(2024, 1, 10))
    assert len(bars) == 5
    assert "date" in bars[0]
    assert "open" in bars[0]
    assert "close" in bars[0]
    assert "volume" in bars[0]


def test_fetch_yfinance_empty_returns_empty():
    with patch("collector.yf.download", return_value=pd.DataFrame()):
        bars = _fetch_yfinance("AAPL", date(2024, 1, 1), date(2024, 1, 2))
    assert bars == []


def test_collect_bars_uses_cache():
    """collect_bars returns DB-cached bars without calling yfinance for covered dates."""
    today = date.today()
    cached_bars = [
        {"date": today - timedelta(days=i), "open": 100.0, "high": 102.0,
         "low": 98.0, "close": 101.0, "volume": 1_000_000}
        for i in range(400, 0, -1)  # 400 days of cached bars
    ]

    with patch("collector.get_cached_bars", return_value=cached_bars) as mock_cache, \
         patch("collector.save_bars") as mock_save, \
         patch("collector.yf.download") as mock_yf:
        result = collect_bars(["AAPL"], lookback_days=365)

    mock_yf.assert_not_called()   # full cache hit → no yfinance call
    assert "AAPL" in result
    assert len(result["AAPL"]) == 400


def test_collect_bars_fetches_missing_dates():
    """collect_bars fetches only the gap between cached data and today."""
    today = date.today()
    # Cache only has bars up to 10 days ago — gap of 10 days
    cached_bars = [
        {"date": today - timedelta(days=i), "open": 100.0, "high": 102.0,
         "low": 98.0, "close": 101.0, "volume": 1_000_000}
        for i in range(20, 10, -1)  # days 11–20 ago
    ]
    new_bars_df = _make_df(10)

    with patch("collector.get_cached_bars", return_value=cached_bars), \
         patch("collector.save_bars") as mock_save, \
         patch("collector.yf.download", return_value=new_bars_df) as mock_yf:
        result = collect_bars(["AAPL"], lookback_days=30)

    mock_yf.assert_called_once()
    mock_save.assert_called_once()  # saves the newly fetched bars


def test_collect_bars_parallel_handles_multiple_symbols():
    new_df = _make_df(5)
    with patch("collector.get_cached_bars", return_value=[]), \
         patch("collector.save_bars"), \
         patch("collector.yf.download", return_value=new_df):
        result = collect_bars(["AAPL", "MSFT"], lookback_days=30)
    assert "AAPL" in result
    assert "MSFT" in result


def test_fetch_yfinance_returns_empty_on_key_error():
    """KeyError raised inside yf.download (yfinance batch-mode bug) returns []."""
    with patch("collector.yf.download", side_effect=KeyError("SITM")):
        bars = _fetch_yfinance("SITM", date(2024, 1, 1), date(2024, 1, 10))
    assert bars == []


def test_collect_bars_omits_symbol_on_key_error():
    """collect_bars silently drops a symbol when yfinance raises KeyError."""
    with patch("collector.get_cached_bars", return_value=[]), \
         patch("collector.save_bars"), \
         patch("collector.yf.download", side_effect=KeyError("SITM")):
        result = collect_bars(["SITM"], lookback_days=30)
    assert result == {}
