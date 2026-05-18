-- db/migrations/004_ml_tables.sql
-- Migration 004: ML discovery pipeline tables

CREATE TABLE IF NOT EXISTS ml_bars (
    id          SERIAL PRIMARY KEY,
    symbol      TEXT NOT NULL,
    bar_date    DATE NOT NULL,
    open        FLOAT,
    high        FLOAT,
    low         FLOAT,
    close       FLOAT,
    volume      BIGINT,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, bar_date)
);

CREATE TABLE IF NOT EXISTS ml_runs (
    id                    SERIAL PRIMARY KEY,
    ran_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbols_processed     INTEGER,
    patterns_found        INTEGER,
    strategies_generated  INTEGER,
    candidates_promoted   INTEGER,
    duration_seconds      FLOAT,
    error                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_ml_bars_symbol_date ON ml_bars(symbol, bar_date);
