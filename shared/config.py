import os
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]  # pip install tomli

_DEFAULT_CONFIG: dict = {
    "log_level": "INFO",
    "watchlist": ["AAPL", "MSFT", "GOOGL"],
    "paper_balance": 100000.0,
}


def load_config() -> dict:
    """Load configuration from config.toml.

    CONFIG_FILE env var overrides the default path (/app/config.toml).
    Falls back to built-in defaults if the file is not found.
    Secrets (API keys, passwords) must NOT be placed here — use .env instead.
    """
    path = Path(os.environ.get("CONFIG_FILE", "/app/config.toml"))
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return {**_DEFAULT_CONFIG, **data}
    except FileNotFoundError:
        return dict(_DEFAULT_CONFIG)
