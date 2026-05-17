-- db/migrations/003_research_tables.sql
-- Migration 003: Research service tables

CREATE TABLE IF NOT EXISTS strategies (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    hypothesis      TEXT NOT NULL,
    code            TEXT NOT NULL,
    code_hash       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'draft',
    triggered_by    TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id                  SERIAL PRIMARY KEY,
    strategy_id         INTEGER REFERENCES strategies(id),
    symbol              TEXT NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    data_source         TEXT NOT NULL,
    initial_capital     DECIMAL(12,2) NOT NULL DEFAULT 100000,
    max_position_pct    DECIMAL(5,4)  NOT NULL DEFAULT 0.15,
    stop_loss_pct       DECIMAL(5,4)  NOT NULL DEFAULT 0.05,
    max_hold_bars       INTEGER       NOT NULL DEFAULT 20,
    total_return_pct    DECIMAL(8,4),
    sharpe_ratio        DECIMAL(8,4),
    max_drawdown_pct    DECIMAL(8,4),
    win_rate_pct        DECIMAL(8,4),
    trade_count         INTEGER,
    avg_hold_bars       DECIMAL(6,2),
    critique            TEXT,
    ran_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES backtest_runs(id),
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    entry_bar       INTEGER NOT NULL,
    exit_bar        INTEGER,
    entry_price     DECIMAL(10,4),
    exit_price      DECIMAL(10,4),
    position_size   DECIMAL(10,4),
    pnl             DECIMAL(10,4),
    exit_reason     TEXT
);

CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON backtest_runs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_run ON backtest_trades(run_id);
