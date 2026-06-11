#!/usr/bin/env bash
# Poll origin/main; if remote is ahead, run deploy. Safe to run on a timer.
set -euo pipefail
cd /home/ubuntu/aifred
git fetch --quiet origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date -Is) new commit $REMOTE detected, deploying..."
  /home/ubuntu/aifred/deploy.sh
else
  echo "$(date -Is) up to date ($LOCAL)"
fi
