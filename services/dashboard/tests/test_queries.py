import unittest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from datetime import date, datetime, timezone

import psycopg2.extras

from queries import (
    get_open_positions,
    get_total_pnl,
    get_daily_pnl_today,
    get_recent_trades,
    get_recent_decisions,
    get_api_health,
    get_watchlist,
    get_circuit_breaker_status,
    get_pnl_history,
    get_trade_activity,
    get_trade_stats,
    get_analysis_stats,
)


def _make_mock_conn(rows, fetchone_row=None):
    """Helper: mock psycopg2 connection whose cursor returns rows."""
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = rows
    mock_cur.fetchone.return_value = fetchone_row
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


@contextmanager
def _make_mock_cm(mock_conn):
    yield mock_conn


class TestGetOpenPositions(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_empty_when_no_open_positions(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_open_positions()
        self.assertEqual(result, [])

    @patch("queries.get_conn")
    def test_returns_positions_list(self, mock_get_conn):
        rows = [
            {"symbol": "AAPL", "qty": 10, "price": "150.0000", "placed_at": datetime(2026, 5, 15, 9, 30, tzinfo=timezone.utc)},
            {"symbol": "MSFT", "qty": 5,  "price": "300.0000", "placed_at": datetime(2026, 5, 15, 9, 31, tzinfo=timezone.utc)},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_open_positions()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["symbol"], "AAPL")

    @patch("queries.get_conn")
    def test_uses_realdict_cursor(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_open_positions()
        call_kwargs = mock_conn.cursor.call_args[1]
        self.assertEqual(call_kwargs["cursor_factory"], psycopg2.extras.RealDictCursor)


class TestGetTotalPnl(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_zero_when_no_rows(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={"total": None})
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_total_pnl()
        self.assertEqual(result, 0.0)

    @patch("queries.get_conn")
    def test_returns_sum(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={"total": "1234.56"})
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_total_pnl()
        self.assertAlmostEqual(result, 1234.56)


class TestGetDailyPnlToday(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_zero_when_no_row(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=None)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_daily_pnl_today(date(2026, 5, 15))
        self.assertEqual(result, 0.0)

    @patch("queries.get_conn")
    def test_returns_todays_pnl(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn(
            [], fetchone_row={"realized_pnl": "250.00", "circuit_breaker_triggered": False}
        )
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_daily_pnl_today(date(2026, 5, 15))
        self.assertAlmostEqual(result, 250.0)


class TestGetRecentTrades(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_list_of_dicts(self, mock_get_conn):
        rows = [
            {"id": 1, "symbol": "AAPL", "side": "buy", "qty": 10, "price": "150.0000",
             "status": "filled", "placed_at": datetime(2026, 5, 15, 9, 30, tzinfo=timezone.utc),
             "filled_at": datetime(2026, 5, 15, 9, 30, 5, tzinfo=timezone.utc)},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_recent_trades()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "AAPL")

    @patch("queries.get_conn")
    def test_passes_limit_to_query(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_recent_trades(limit=50)
        params = mock_cur.execute.call_args[0][1]
        self.assertIn(50, params)


class TestGetRecentDecisions(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_list_of_dicts(self, mock_get_conn):
        rows = [
            {"id": 1, "symbol": "AAPL", "decision": "buy", "confidence": "0.820",
             "reasoning": "Strong uptrend", "model": "claude-haiku",
             "acted_on": True, "skip_reason": None,
             "decided_at": datetime(2026, 5, 15, 9, 29, tzinfo=timezone.utc)},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_recent_decisions()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "AAPL")

    @patch("queries.get_conn")
    def test_passes_limit_to_query(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_recent_decisions(limit=25)
        params = mock_cur.execute.call_args[0][1]
        self.assertIn(25, params)


class TestGetApiHealth(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_list_of_health_rows(self, mock_get_conn):
        rows = [
            {"api_name": "alpaca", "status": "ok", "latency_ms": 45,
             "checked_at": datetime(2026, 5, 15, 9, 0, tzinfo=timezone.utc), "error_message": None},
            {"api_name": "finnhub", "status": "warning", "latency_ms": 800,
             "checked_at": datetime(2026, 5, 15, 9, 0, tzinfo=timezone.utc), "error_message": "slow"},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_api_health()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["api_name"], "alpaca")

    @patch("queries.get_conn")
    def test_returns_empty_list_when_no_rows(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_api_health()
        self.assertEqual(result, [])


class TestGetWatchlist(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_latest_decision_per_symbol(self, mock_get_conn):
        rows = [
            {"symbol": "AAPL", "decision": "buy", "confidence": "0.820",
             "decided_at": datetime(2026, 5, 15, 9, 29, tzinfo=timezone.utc), "acted_on": True},
            {"symbol": "TSLA", "decision": "hold", "confidence": "0.550",
             "decided_at": datetime(2026, 5, 15, 9, 29, tzinfo=timezone.utc), "acted_on": False},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_watchlist()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["symbol"], "AAPL")

    @patch("queries.get_conn")
    def test_returns_empty_list_when_no_decisions(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_watchlist()
        self.assertEqual(result, [])


class TestGetCircuitBreakerStatus(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_false_when_no_row(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=None)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_circuit_breaker_status(date(2026, 5, 15))
        self.assertFalse(result)

    @patch("queries.get_conn")
    def test_returns_true_when_triggered(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={"circuit_breaker_triggered": True})
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_circuit_breaker_status(date(2026, 5, 15))
        self.assertTrue(result)

    @patch("queries.get_conn")
    def test_returns_false_when_not_triggered(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={"circuit_breaker_triggered": False})
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_circuit_breaker_status(date(2026, 5, 15))
        self.assertFalse(result)


class TestGetPnlHistory(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_empty_list_when_no_rows(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_pnl_history(30)
        self.assertEqual(result, [])

    @patch("queries.get_conn")
    def test_returns_rows_with_correct_keys(self, mock_get_conn):
        rows = [
            {"date": date(2026, 5, 14), "realized_pnl": "123.45"},
            {"date": date(2026, 5, 15), "realized_pnl": "-50.00"},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_pnl_history(30)
        self.assertEqual(len(result), 2)
        self.assertIn("date", result[0])
        self.assertIn("realized_pnl", result[0])
        self.assertEqual(result[0]["date"], date(2026, 5, 14))

    @patch("queries.get_conn")
    def test_passes_days_parameter_to_query(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_pnl_history(days=7)
        params = mock_cur.execute.call_args[0][1]
        self.assertIn(7, params)


class TestGetTradeActivity(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_empty_list_when_no_rows(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_activity(30)
        self.assertEqual(result, [])

    @patch("queries.get_conn")
    def test_returns_rows_with_correct_keys(self, mock_get_conn):
        rows = [
            {"date": date(2026, 5, 14), "count": 5},
            {"date": date(2026, 5, 15), "count": 12},
        ]
        mock_conn, mock_cur = _make_mock_conn(rows)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_activity(30)
        self.assertEqual(len(result), 2)
        self.assertIn("date", result[0])
        self.assertIn("count", result[0])
        self.assertEqual(result[1]["count"], 12)

    @patch("queries.get_conn")
    def test_passes_days_parameter_to_query(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([])
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_trade_activity(days=14)
        params = mock_cur.execute.call_args[0][1]
        self.assertIn(14, params)


class TestGetTradeStats(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_zeros_when_no_closed_trades(self, mock_get_conn):
        row = {
            "total_closed": 0, "wins": 0, "losses": 0,
            "win_rate_pct": None,
            "avg_pnl": "0.00", "best_trade": "0.00",
            "worst_trade": "0.00", "avg_holding_hours": "0.0",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_stats()
        self.assertEqual(result["total_closed"], 0)
        self.assertEqual(result["wins"], 0)
        self.assertAlmostEqual(result["win_rate_pct"], 0.0)
        self.assertAlmostEqual(result["avg_pnl"], 0.0)

    @patch("queries.get_conn")
    def test_win_rate_pct_is_float(self, mock_get_conn):
        row = {
            "total_closed": 4, "wins": 3, "losses": 1,
            "win_rate_pct": "75.0",
            "avg_pnl": "42.50", "best_trade": "120.00",
            "worst_trade": "-30.00", "avg_holding_hours": "18.5",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_stats()
        self.assertAlmostEqual(result["win_rate_pct"], 75.0)
        self.assertIsInstance(result["win_rate_pct"], float)

    @patch("queries.get_conn")
    def test_all_keys_present(self, mock_get_conn):
        row = {
            "total_closed": 1, "wins": 1, "losses": 0,
            "win_rate_pct": "100.0",
            "avg_pnl": "55.00", "best_trade": "55.00",
            "worst_trade": "55.00", "avg_holding_hours": "24.0",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_stats()
        expected_keys = {
            "total_closed", "wins", "losses", "win_rate_pct",
            "avg_pnl", "best_trade", "worst_trade", "avg_holding_hours",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    @patch("queries.get_conn")
    def test_negative_values_preserved(self, mock_get_conn):
        row = {
            "total_closed": 2, "wins": 0, "losses": 2,
            "win_rate_pct": "0.0",
            "avg_pnl": "-75.00", "best_trade": "-50.00",
            "worst_trade": "-100.00", "avg_holding_hours": "6.0",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_stats()
        self.assertAlmostEqual(result["worst_trade"], -100.0)
        self.assertAlmostEqual(result["avg_pnl"], -75.0)
        self.assertAlmostEqual(result["win_rate_pct"], 0.0)

    @patch("queries.get_conn")
    def test_uses_realdict_cursor(self, mock_get_conn):
        row = {
            "total_closed": 0, "wins": 0, "losses": 0,
            "win_rate_pct": None,
            "avg_pnl": "0.00", "best_trade": "0.00",
            "worst_trade": "0.00", "avg_holding_hours": "0.0",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        get_trade_stats()
        call_kwargs = mock_conn.cursor.call_args[1]
        self.assertEqual(call_kwargs["cursor_factory"], psycopg2.extras.RealDictCursor)

    @patch("queries.get_conn")
    def test_break_even_trade_not_counted_as_loss(self, mock_get_conn):
        # A trade where sell_price == buy_price has pnl == 0
        # It must not be counted as a loss (pnl < 0 is the loss filter)
        row = {
            "total_closed": 1, "wins": 0, "losses": 0,
            "win_rate_pct": "0.0",
            "avg_pnl": "0.00", "best_trade": "0.00",
            "worst_trade": "0.00", "avg_holding_hours": "8.0",
        }
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row=row)
        mock_get_conn.return_value = _make_mock_cm(mock_conn)

        result = get_trade_stats()
        self.assertEqual(result["total_closed"], 1)
        self.assertEqual(result["wins"], 0)
        self.assertEqual(result["losses"], 0)   # break-even ≠ loss
        self.assertAlmostEqual(result["win_rate_pct"], 0.0)


class TestGetAnalysisStats(unittest.TestCase):
    @patch("queries.get_conn")
    def test_returns_zeros_when_no_decisions(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 0,
            "median_confidence": None,
            "pct_above_threshold": None,
            "pct_acted_on": None,
            "haiku_count": 0,
            "sonnet_count": 0,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        result = get_analysis_stats()
        self.assertEqual(result["total_decisions"], 0)
        self.assertEqual(result["median_confidence"], 0.0)
        self.assertEqual(result["pct_above_threshold"], 0.0)
        self.assertEqual(result["pct_acted_on"], 0.0)

    @patch("queries.get_conn")
    def test_all_keys_present(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 50,
            "median_confidence": "0.72",
            "pct_above_threshold": "68.0",
            "pct_acted_on": "45.0",
            "haiku_count": 40,
            "sonnet_count": 10,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        result = get_analysis_stats()
        self.assertEqual(
            set(result.keys()),
            {"total_decisions", "median_confidence", "pct_above_threshold",
             "pct_acted_on", "haiku_count", "sonnet_count"}
        )

    @patch("queries.get_conn")
    def test_median_confidence_is_float(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 10,
            "median_confidence": "0.71",
            "pct_above_threshold": "70.0",
            "pct_acted_on": "50.0",
            "haiku_count": 8,
            "sonnet_count": 2,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        result = get_analysis_stats()
        self.assertIsInstance(result["median_confidence"], float)

    @patch("queries.get_conn")
    def test_passes_days_param_when_provided(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 0, "median_confidence": None,
            "pct_above_threshold": None, "pct_acted_on": None,
            "haiku_count": 0, "sonnet_count": 0,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        get_analysis_stats(days=30)
        params = mock_cur.execute.call_args[0][1]
        self.assertIn(30, params)

    @patch("queries.get_conn")
    def test_no_params_when_days_is_none(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 0, "median_confidence": None,
            "pct_above_threshold": None, "pct_acted_on": None,
            "haiku_count": 0, "sonnet_count": 0,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        get_analysis_stats(days=None)
        params = mock_cur.execute.call_args[0][1]
        self.assertEqual(params, ())

    @patch("queries.get_conn")
    def test_haiku_and_sonnet_counts_are_ints(self, mock_get_conn):
        mock_conn, mock_cur = _make_mock_conn([], fetchone_row={
            "total_decisions": 10,
            "median_confidence": "0.71",
            "pct_above_threshold": "70.0",
            "pct_acted_on": "50.0",
            "haiku_count": 8,
            "sonnet_count": 2,
        })
        mock_get_conn.return_value = _make_mock_cm(mock_conn)
        result = get_analysis_stats()
        self.assertIsInstance(result["haiku_count"], int)
        self.assertIsInstance(result["sonnet_count"], int)


if __name__ == "__main__":
    unittest.main()
