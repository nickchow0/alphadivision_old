from datetime import date as Date

import psycopg2.extras

from shared.db import get_conn


def get_open_positions() -> list:
    """
    Return open positions: the most recent filled trade per symbol where the
    last action was a buy (i.e. no subsequent filled sell).
    """
    sql = """
        SELECT symbol, qty, price, placed_at
        FROM (
            SELECT DISTINCT ON (symbol)
                symbol, side, qty, price, placed_at
            FROM trades
            WHERE status = 'filled'
            ORDER BY symbol, placed_at DESC
        ) latest
        WHERE side = 'buy'
        ORDER BY placed_at DESC
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return list(cur.fetchall())


def get_total_pnl() -> float:
    """Return cumulative realized P&L across all days."""
    sql = "SELECT SUM(realized_pnl) AS total FROM daily_pnl"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            row = cur.fetchone()
    if row is None or row["total"] is None:
        return 0.0
    return float(row["total"])


def get_daily_pnl_today(today: Date) -> float:
    """Return today's realized P&L, or 0.0 if no row exists yet."""
    sql = "SELECT realized_pnl FROM daily_pnl WHERE date = %s"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (today,))
            row = cur.fetchone()
    if row is None:
        return 0.0
    return float(row["realized_pnl"])


def get_recent_trades(limit: int = 100) -> list:
    """Return the most recent trades, newest first."""
    sql = """
        SELECT id, symbol, side, qty, price, status, placed_at, filled_at
        FROM trades
        ORDER BY placed_at DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return list(cur.fetchall())


def get_recent_decisions(limit: int = 100) -> list:
    """Return the most recent AI decisions, newest first."""
    sql = """
        SELECT id, symbol, decision, confidence, reasoning, model,
               acted_on, skip_reason, decided_at
        FROM decisions
        ORDER BY decided_at DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return list(cur.fetchall())


def get_api_health() -> list:
    """Return the most recent health check result per API."""
    sql = """
        SELECT DISTINCT ON (api_name)
            api_name, status, latency_ms, checked_at, error_message
        FROM api_health
        ORDER BY api_name, checked_at DESC
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return list(cur.fetchall())


def get_watchlist() -> list:
    """Return the most recent AI decision per symbol (the current watchlist state)."""
    sql = """
        SELECT DISTINCT ON (symbol)
            symbol, decision, confidence, decided_at, acted_on
        FROM decisions
        ORDER BY symbol, decided_at DESC
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return list(cur.fetchall())


def get_pnl_history(days: int = 30) -> list:
    """Return daily realized P&L for the last `days` days, oldest first."""
    sql = """
        SELECT date, realized_pnl
        FROM daily_pnl
        WHERE date >= CURRENT_DATE - (%s - 1) * INTERVAL '1 day'
        ORDER BY date ASC
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (days,))
            return list(cur.fetchall())


def get_trade_activity(days: int = 30) -> list:
    """Return count of filled trades per day for the last `days` days, oldest first."""
    sql = """
        SELECT DATE(placed_at AT TIME ZONE 'America/New_York') AS date,
               COUNT(*) AS count
        FROM trades
        WHERE status = 'filled'
          AND placed_at >= NOW() - (%s * INTERVAL '1 day')
        GROUP BY DATE(placed_at AT TIME ZONE 'America/New_York')
        ORDER BY date ASC
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (days,))
            return list(cur.fetchall())


def get_circuit_breaker_status(today: Date) -> bool:
    """Return True if the circuit breaker was triggered today."""
    sql = "SELECT circuit_breaker_triggered FROM daily_pnl WHERE date = %s"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (today,))
            row = cur.fetchone()
    if row is None:
        return False
    return bool(row["circuit_breaker_triggered"])


def get_trade_stats() -> dict:
    """
    Compute aggregate stats for all closed trades (matched buy+sell pairs).

    Each sell is matched with the most recent filled buy for the same symbol
    before that sell's filled_at (LATERAL join). Safe because the bot holds
    at most one open position per symbol at a time.

    Returns a dict with keys:
        total_closed, wins, losses, win_rate_pct,
        avg_pnl, best_trade, worst_trade, avg_holding_hours
    All values are floats (win_rate_pct is 0.0 when total_closed == 0).
    """
    sql = """
        WITH pairs AS (
            SELECT
                (s.price - b.price) * s.qty  AS pnl,
                EXTRACT(EPOCH FROM (s.filled_at - b.filled_at)) / 3600.0
                                              AS holding_hours
            FROM trades s
            JOIN LATERAL (
                SELECT price, filled_at
                FROM trades b
                WHERE b.symbol    = s.symbol
                  AND b.side      = 'buy'
                  AND b.status    = 'filled'
                  AND b.filled_at IS NOT NULL
                  AND b.filled_at < s.filled_at
                ORDER BY b.filled_at DESC
                LIMIT 1
            ) b ON true
            WHERE s.side        = 'sell'
              AND s.status      = 'filled'
              AND s.filled_at   IS NOT NULL
        )
        SELECT
            COUNT(*)                                                              AS total_closed,
            COUNT(*) FILTER (WHERE pnl > 0)                                      AS wins,
            COUNT(*) FILTER (WHERE pnl < 0)                                      AS losses,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE pnl > 0)
                / NULLIF(COUNT(*), 0),
                1
            )                                                                     AS win_rate_pct,
            ROUND(COALESCE(AVG(pnl),            0)::numeric, 2)                  AS avg_pnl,
            ROUND(COALESCE(MAX(pnl),            0)::numeric, 2)                  AS best_trade,
            ROUND(COALESCE(MIN(pnl),            0)::numeric, 2)                  AS worst_trade,
            ROUND(COALESCE(AVG(holding_hours),  0)::numeric, 1)                  AS avg_holding_hours
        FROM pairs
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            row = cur.fetchone()

    def _f(key: str, default: float = 0.0) -> float:
        val = row.get(key)
        return float(val) if val is not None else default

    return {
        "total_closed":      int(row.get("total_closed") or 0),
        "wins":              int(row.get("wins")         or 0),
        "losses":            int(row.get("losses")       or 0),
        "win_rate_pct":      _f("win_rate_pct"),
        "avg_pnl":           _f("avg_pnl"),
        "best_trade":        _f("best_trade"),
        "worst_trade":       _f("worst_trade"),
        "avg_holding_hours": _f("avg_holding_hours"),
    }
