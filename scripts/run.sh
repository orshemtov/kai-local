#!/usr/bin/env bash
set -Eeuo pipefail

# --- Config ---
PORT="${PORT:-8000}"                 # change if your app isn't on 8000
NGROK_API="http://localhost:4040"    # ngrok local API
SECRET_TOKEN="${SECRET_TOKEN:-}"     # optional: set to a random string to verify Telegram requests

# --- Preflight checks ---
for cmd in ngrok curl jq; do
  command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd"; exit 1; }
done

# Load env with BOT_TOKEN
source .env
: "${BOT_TOKEN:?BOT_TOKEN is required in .env}"

# --- Cleanup handler ---
NGROK_PID=""
cleanup() {
  echo -e "\n[cleanup] Removing Telegram webhook and stopping ngrok..."
  # Remove webhook (ignore errors during cleanup)
  curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" -d "url=" >/dev/null || true
  # Stop ngrok if still running
  if [[ -n "${NGROK_PID}" ]] && ps -p "${NGROK_PID}" >/dev/null 2>&1; then
    kill "${NGROK_PID}" 2>/dev/null || true
    wait "${NGROK_PID}" 2>/dev/null || true
  fi
  echo "[cleanup] Done."
}
trap cleanup INT TERM EXIT

# --- Start ngrok in background ---
echo "[ngrok] Starting tunnel on :${PORT} ..."
ngrok http "${PORT}" >/dev/null 2>&1 &
NGROK_PID=$!

# --- Wait for ngrok URL ---
echo "[ngrok] Waiting for public URL..."
NGROK_URL=""
for i in {1..30}; do
  NGROK_URL="$(curl -sf "${NGROK_API}/api/tunnels" \
    | jq -r '.tunnels[] | select(.proto=="https") | .public_url' || true)"
  if [[ -n "${NGROK_URL}" && "${NGROK_URL}" != "null" ]]; then
    break
  fi
  sleep 1
done
if [[ -z "${NGROK_URL}" || "${NGROK_URL}" == "null" ]]; then
  echo "[error] Could not get ngrok URL from ${NGROK_API}. Exiting."
  exit 1
fi
echo "[ngrok] Public URL: ${NGROK_URL}"

# --- Telegram webhook: drop backlog, then set fresh ---
echo "[tg] Deleting webhook and DROPPING pending updates..."
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook" \
  -d "drop_pending_updates=true" >/dev/null

WEBHOOK_URL="${NGROK_URL}/telegram/webhook"
echo "[tg] Setting new webhook -> ${WEBHOOK_URL} (drop pending updates on set)"
SET_ARGS=( -d "url=${WEBHOOK_URL}" -d "drop_pending_updates=true" )
if [[ -n "${SECRET_TOKEN}" ]]; then
  SET_ARGS+=( -d "secret_token=${SECRET_TOKEN}" )
fi

set +e
SET_RESP=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" "${SET_ARGS[@]}")
set -e
echo "[tg] setWebhook response: ${SET_RESP}"

echo "[tg] Current webhook info:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq

echo ""
echo "✅ Ready. Press Ctrl+C to stop and clean up."

# --- Keep process alive until user stops it ---
# (when you press Ctrl+C, trap will run cleanup)
wait "${NGROK_PID}"
