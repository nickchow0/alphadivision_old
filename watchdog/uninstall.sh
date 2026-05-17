#!/usr/bin/env bash
# uninstall.sh — Stop and remove the AlphaDivision Watchdog systemd service.
#
# Usage:
#   sudo bash /opt/alphadivision/watchdog/uninstall.sh

set -euo pipefail

SERVICE_NAME="alphadivision-watchdog"
SYSTEMD_DIR="/etc/systemd/system"

GREEN='\033[0;32m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC}  $*"; }

[[ $EUID -eq 0 ]] || { echo "Run as root: sudo bash $0" >&2; exit 1; }

if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl stop "$SERVICE_NAME"
    info "Service stopped."
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    info "Service disabled."
fi

if [[ -f "$SYSTEMD_DIR/$SERVICE_NAME.service" ]]; then
    rm "$SYSTEMD_DIR/$SERVICE_NAME.service"
    systemctl daemon-reload
    info "Service file removed and daemon reloaded."
fi

info "Uninstall complete."
