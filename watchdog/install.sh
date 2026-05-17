#!/usr/bin/env bash
# install.sh — Install and start the AlphaDivision Watchdog as a systemd service.
#
# Usage (run as root or with sudo on the Oracle VM):
#   sudo bash /opt/alphadivision/watchdog/install.sh
#
# What it does:
#   1. Checks prerequisites (Python 3, pip3, systemd, Docker)
#   2. Installs Python dependencies system-wide
#   3. Installs the systemd service file
#   4. Enables the service (auto-start on boot)
#   5. Starts the service and prints its status

set -euo pipefail

SERVICE_NAME="alphadivision-watchdog"
SERVICE_FILE="$(dirname "$0")/alphadivision-watchdog.service"
INSTALL_DIR="/opt/alphadivision"
SYSTEMD_DIR="/etc/systemd/system"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 1. Preflight checks ────────────────────────────────────────────────────────

[[ $EUID -eq 0 ]] || error "Run this script as root: sudo bash $0"

command -v python3 >/dev/null || error "python3 not found — install it first"
command -v pip3    >/dev/null || error "pip3 not found — install it first"
command -v docker  >/dev/null || error "docker not found — install Docker first"
command -v systemctl >/dev/null || error "systemctl not found — this script requires systemd"

[[ -f "$SERVICE_FILE" ]] || error "Service file not found: $SERVICE_FILE"
[[ -f "$INSTALL_DIR/watchdog/watchdog.py" ]] || \
    error "watchdog.py not found at $INSTALL_DIR/watchdog/watchdog.py — deploy the repo first"
[[ -f "$INSTALL_DIR/.env" ]] || \
    error ".env not found at $INSTALL_DIR/.env — copy .env.example and fill in your secrets"

info "Preflight checks passed."

# ── 2. Python dependencies ─────────────────────────────────────────────────────

info "Installing Python dependencies..."
pip3 install --quiet \
    "redis==5.0.4" \
    "requests==2.31.0" \
    "sendgrid==6.11.0" \
    "python-dotenv==1.0.1"
info "Python dependencies installed."

# ── 3. Install service file ────────────────────────────────────────────────────

info "Installing systemd service file to $SYSTEMD_DIR/$SERVICE_NAME.service ..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_NAME.service"
chmod 644 "$SYSTEMD_DIR/$SERVICE_NAME.service"

systemctl daemon-reload
info "systemd daemon reloaded."

# ── 4. Enable + start ─────────────────────────────────────────────────────────

if systemctl is-active --quiet "$SERVICE_NAME"; then
    warn "Service is already running — restarting to pick up any changes..."
    systemctl restart "$SERVICE_NAME"
else
    systemctl enable "$SERVICE_NAME"
    systemctl start  "$SERVICE_NAME"
fi

# ── 5. Status ─────────────────────────────────────────────────────────────────

echo ""
systemctl status "$SERVICE_NAME" --no-pager --lines=10
echo ""
info "Done. Useful commands:"
echo "  View logs:    journalctl -u $SERVICE_NAME -f"
echo "  Stop:         sudo systemctl stop $SERVICE_NAME"
echo "  Disable:      sudo bash $(dirname "$0")/uninstall.sh"
