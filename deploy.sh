#!/usr/bin/env bash
# Deploy script: pull latest code, update deps, restart bot.
set -euo pipefail
cd /home/ubuntu/aifred
echo "[deploy] fetching latest..."
git fetch --all --quiet
git reset --hard origin/main
echo "[deploy] installing deps..."
pip install -q --break-system-packages -r requirements.txt
echo "[deploy] restarting service..."
sudo systemctl restart claude-bot
sleep 2
systemctl is-active claude-bot
echo "[deploy] done."
