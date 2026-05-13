# AlphaDivision

Algorithmic trading bot powered by Claude AI.

## Setup

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run: `python bot/main.py`

## Architecture

- `bot/data/` — price, news, and macro data fetching
- `bot/analysis/` — Claude AI decision making
- `bot/strategy/` — risk management and position sizing
- `bot/execution/` — order placement via Alpaca
