import time
import logging
from data.price import get_bars, get_current_price
from data.news import get_news
from data.macro import get_fed_funds_rate, get_cpi
from analysis.claude import get_decision
from execution.orders import get_position, place_order
from strategy.risk import position_size, should_act

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SYMBOLS = ["AAPL", "MSFT"]
POLL_INTERVAL = 3600  # seconds (1 hour)


def run_once(symbol: str):
    price = get_current_price(symbol)
    bars = get_bars(symbol)
    indicators = {
        "rsi": round(bars["RSI_14"].iloc[-1], 2),
        "sma_20": round(bars["SMA_20"].iloc[-1], 2),
        "sma_50": round(bars["SMA_50"].iloc[-1], 2),
    }
    news = get_news(symbol)
    macro = {
        "fed_funds_rate": get_fed_funds_rate(),
        "cpi": get_cpi(),
    }

    result = get_decision(symbol, price, indicators, news, macro)
    log.info(f"{symbol} decision: {result}")

    if not should_act(result["confidence"]):
        log.info(f"{symbol} confidence too low ({result['confidence']}), skipping")
        return

    position = get_position(symbol)
    decision = result["decision"]

    if decision == "buy" and not position:
        qty = position_size(price, portfolio_value=10000)
        place_order(symbol, qty, "buy")
        log.info(f"Bought {qty} shares of {symbol} at ${price}")

    elif decision == "sell" and position:
        place_order(symbol, int(float(position.qty)), "sell")
        log.info(f"Sold {symbol} position")

    else:
        log.info(f"{symbol} holding, no action taken")


def main():
    log.info("AlphaDivision bot starting")
    while True:
        for symbol in SYMBOLS:
            try:
                run_once(symbol)
            except Exception as e:
                log.error(f"Error processing {symbol}: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
