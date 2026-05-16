"""
watchdog.py — AlphaDivision host-level service watchdog.

Runs outside Docker on the VM host. Monitors service heartbeats via Redis,
auto-restarts failed services via docker compose, and sends Discord/email alerts.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

import redis
import requests
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVICES = ["data", "analysis", "execution", "alerts", "dashboard"]
DASHBOARD_HEALTH_URL = "http://localhost:8080/health"
MAX_RESTARTS = 3
POLL_INTERVAL = 120       # seconds between watchdog cycles
RESTART_WINDOW = 3600     # TTL for restart count key (1 hour)
ALERT_WINDOW = 3600       # TTL for alert state key (1 hour)

# Path to docker-compose project directory
COMPOSE_DIR = os.environ.get("COMPOSE_DIR", "/opt/alphadivision")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("watchdog")

# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def send_discord(webhook_url: str, message: str) -> None:
    """POST a message to a Discord webhook. Raises on failure."""
    resp = requests.post(webhook_url, json={"content": message}, timeout=10)
    resp.raise_for_status()


def send_email(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    """Send a plain-text email via SendGrid. Raises on failure."""
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )
    sg = SendGridAPIClient(api_key)
    sg.send(message)
