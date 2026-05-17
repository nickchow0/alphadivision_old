# AlphaDivision Watchdog

A standalone host-level watchdog that monitors all AlphaDivision Docker services,
auto-restarts failures, and sends Discord + email alerts.

Runs **outside Docker** directly on the VM host. No shared modules required.

---

## How It Works

- Polls Redis heartbeat keys (`heartbeat:{service}`, TTL 90 s) every 2 minutes
- If a service heartbeat TTL ≤ 0, the service is considered **down**
- Attempts `docker compose restart <service>` up to 3 times (tracked in Redis, 1-hour window)
- After 3 failed restarts, escalates to **CRITICAL** Discord + email alert and stops retrying until the window expires
- When a service recovers, sends a **recovery** Discord notification
- Polls the dashboard `/health` endpoint (HTTP); alerts Discord on non-200 or timeout

---

## Prerequisites

- Python 3.8+
- pip3
- Docker (with `docker compose` plugin)
- systemd (standard on Ubuntu/Oracle Linux)

---

## Environment Variables

The watchdog reads `/opt/alphadivision/.env` at startup (same file used by Docker Compose).
Required keys:

```ini
REDIS_URL=redis://localhost:6379
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SENDGRID_API_KEY=SG.xxxx
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=you@yourdomain.com
```

---

## Installation (systemd)

With the repo deployed at `/opt/alphadivision` and `.env` filled in:

```bash
sudo bash /opt/alphadivision/watchdog/install.sh
```

That's it. The script:
1. Checks prerequisites (Python 3, pip3, Docker, systemd)
2. Installs Python dependencies system-wide
3. Copies `alphadivision-watchdog.service` to `/etc/systemd/system/`
4. Enables the service (auto-start on boot)
5. Starts the service and prints its status

### Useful commands after install

```bash
# Live logs
journalctl -u alphadivision-watchdog -f

# Status
sudo systemctl status alphadivision-watchdog

# Restart (e.g. after config change)
sudo systemctl restart alphadivision-watchdog

# Uninstall
sudo bash /opt/alphadivision/watchdog/uninstall.sh
```

---

## Running Manually (testing only)

```bash
python3 /opt/alphadivision/watchdog/watchdog.py
```

---

## Running Tests

```bash
cd /opt/alphadivision
python3 -m pytest watchdog/tests/ -v
```

---

## Failure Modes

| Scenario | Behaviour |
|---|---|
| Redis is down | `redis.from_url` raises at startup; watchdog exits (systemd restarts it after 10 s) |
| Docker compose fails | `restart_service` returns False, logs error, increments restart count |
| Discord webhook fails | Logged as ERROR; watchdog continues — email still attempted |
| SendGrid fails | Logged as ERROR; watchdog continues |
| Exception during a service check | Logged as ERROR; remaining services still checked |
| Dashboard HTTP unreachable | Discord-only alert (no restart attempted) |
| Watchdog itself crashes | systemd restarts it within 10 s |
