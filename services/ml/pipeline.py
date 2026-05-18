"""services/ml/pipeline.py — ML strategy discovery pipeline entrypoint.

Runs a nightly batch job at 2am. Exposes GET /health on port 8082 for the
existing watchdog. All pipeline logic is orchestrated from run_pipeline().
"""
import logging
import os
import threading
import time

import schedule
from flask import Flask, jsonify

from shared.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("ml")

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


def run_pipeline() -> None:
    """Orchestrate all 5 pipeline phases. Called by cron and on first boot."""
    log.info("Pipeline started")
    start = time.time()
    try:
        _run_phases()
    except Exception as exc:  # noqa: BLE001
        log.error("Pipeline failed: %s", exc, exc_info=True)
        _send_discord_alert(f"ML pipeline failed: {exc}")
    finally:
        log.info("Pipeline finished in %.1fs", time.time() - start)


def _run_phases() -> None:
    """Placeholder — implemented in Task 7."""
    log.info("No phases implemented yet")


def _send_discord_alert(message: str) -> None:
    """Send a Discord alert via webhook if configured."""
    import requests as req
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    try:
        req.post(url, json={"content": message}, timeout=10)
    except Exception as exc:  # noqa: BLE001
        log.warning("Discord alert failed: %s", exc)


def _start_health_server() -> None:
    """Run Flask health server in background thread on port 8082."""
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8082, use_reloader=False),
        daemon=True,
        name="health",
    ).start()
    log.info("Health server started on :8082")


def main() -> None:
    cfg = load_config().get("ml", {})
    cron = cfg.get("cron_schedule", "0 2 * * *")

    _start_health_server()

    # Parse cron: "0 2 * * *" → run at 02:00 daily
    hour = int(cron.split()[1])
    minute = int(cron.split()[0])
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_pipeline)
    log.info("Scheduled pipeline at %02d:%02d UTC nightly", hour, minute)

    # Run once immediately on startup so the first nightly run isn't skipped
    run_pipeline()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
