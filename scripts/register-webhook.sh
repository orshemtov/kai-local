#!/bin/sh

# Simple webhook registration script
set -e

echo "[webhook] Starting webhook registration..."

# Check BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo "[webhook] ERROR: BOT_TOKEN not set"
    exit 1
fi

echo "[webhook] Waiting for ngrok tunnel..."

# Wait for ngrok and get URL
attempt=1
while [ $attempt -le 60 ]; do
    echo "[webhook] Attempt $attempt/60 - checking ngrok..."
    
    NGROK_URL=$(curl -s http://ngrok:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[]? | select(.proto=="https") | .public_url' 2>/dev/null || echo "")
    
    if [ -n "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
        echo "[webhook] Found ngrok URL: $NGROK_URL"
        break
    fi
    
    sleep 3
    attempt=$((attempt + 1))
done

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "[webhook] ERROR: Could not get ngrok URL"
    exit 1
fi

# Register webhook
WEBHOOK_URL="$NGROK_URL/telegram/webhook"
echo "[webhook] Registering webhook: $WEBHOOK_URL"

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
    -F "url=$WEBHOOK_URL" \
    -F "drop_pending_updates=true")

echo "[webhook] Response: $RESPONSE"

if echo "$RESPONSE" | jq -e '.ok == true' >/dev/null 2>&1; then
    echo "[webhook] SUCCESS!"
    exit 0
else
    echo "[webhook] FAILED!"
    exit 1
fi
