"""
One-time script to verify SendGrid email and Discord webhook work end-to-end.
Exercises the exact same send_email() and send_discord() functions used by the
alerts service in production.

Usage:
    python3 /opt/alphadivision/scripts/test_email.py
"""
import os
import sys
from pathlib import Path

# Allow importing notifier.py directly from the alerts service
sys.path.append(str(Path(__file__).resolve().parent.parent / "services" / "alerts"))

from dotenv import load_dotenv

# Load .env — prefer the production path, fall back to local
env_path = Path("/opt/alphadivision/.env")
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

REQUIRED_VARS = ["SENDGRID_API_KEY", "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO", "DISCORD_WEBHOOK_URL"]

missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
    print(f"        Add them to {env_path} and re-run.")
    sys.exit(1)

sg_api_key   = os.environ["SENDGRID_API_KEY"]
email_from   = os.environ["ALERT_EMAIL_FROM"]
email_to     = os.environ["ALERT_EMAIL_TO"]
webhook_url  = os.environ["DISCORD_WEBHOOK_URL"]

from notifier import send_email, send_discord

exit_code = 0

# --- Email ---
try:
    send_email(
        api_key=sg_api_key,
        from_email=email_from,
        to_email=email_to,
        subject="[AlphaDivision] Test alert — email working",
        body="This is a test message sent by scripts/test_email.py to verify the SendGrid integration.",
    )
    print(f"[OK]   Email sent to {email_to}")
except Exception as exc:
    print(f"[FAIL] Email failed: {exc}")
    exit_code = 1

# --- Discord ---
try:
    send_discord(
        webhook_url=webhook_url,
        message="[AlphaDivision] Test alert — Discord webhook working ✓",
    )
    print("[OK]   Discord webhook fired")
except Exception as exc:
    print(f"[FAIL] Discord webhook failed: {exc}")
    exit_code = 1

sys.exit(exit_code)
