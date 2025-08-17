# kai

Local version

## Pre-requisites

- Python 3.13
- Docker

## Environment variables

Look at `.env.example` and create a similar `.env` file:

```
# Get this from Telegram's @BotFather
BOT_TOKEN=

OPENAI_API_KEY=

# Put in your Postgres database URL: postgresql://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL=

# Optional value
# You can get this by printing the `update.message.chat.id` on the webhook
# This is only used if you wanna send out scheduled messages like daily reports, etc, otherwise not needed
CHAT_ID=

# Check out ngrok docs on how to get this token
# ngrok will be used to expose your local server to the internet
NGROK_AUTHTOKEN=

# Set these, they will be read by the docker-compose.yml to setup your local postgres
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
```

## Usage

```shell
docker compose up -d
```

Then go to your telegram channel and submit a message.

## Running the server locally

For debugging or development purposes, you might want to run the FastAPI server not in docker:

### Install dependencies

```shell
uv sync
```

### Run

```shell
# Sync the DB
dbmate up

# Run FastAPI
make run # runs uv run fastapi dev backend/main.py

# Setup ngrok
ngrok http 8000

# Copy the forwarding URL
# It will look like https://<random-id>.ngrok.io
WEBHOOK_URL=https://<random-id>.ngrok.io

# Can also be fetched dynamically
WEBHOOK_URL=$(curl -s -X POST "http://localhost:4040/api/tunnels" | jq -r .tunnels[0].public_url)

# Register the webhook
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
    -F "url=$WEBHOOK_URL" \
    -F "drop_pending_updates=true"
```
