#!/data/data/com.termux/files/usr/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="logs"
TOR_LOG="$LOG_DIR/tor.log"

mkdir -p "$LOG_DIR"

echo "[INFO] Killing any existing Tor processes (if any)..."
pkill tor 2>/dev/null || true

echo "[INFO] Starting Tor..."
tor > "$TOR_LOG" 2>&1 &
TOR_PID=$!

echo "[INFO] Tor started with PID $TOR_PID, waiting for bootstrap..."

# Wait for Tor to report Bootstrapped 100%
while true; do
  if ! ps -p "$TOR_PID" > /dev/null 2>&1; then
    echo "[ERROR] Tor process exited early. Check $TOR_LOG for details."
    exit 1
  fi

  if grep -q "Bootstrapped 100%" "$TOR_LOG" 2>/dev/null; then
    echo "[INFO] Tor bootstrapped 100%. Starting Crypto Drip Farm..."
    break
  fi

  sleep 2
done

# Run the farm
python src/farm.py
