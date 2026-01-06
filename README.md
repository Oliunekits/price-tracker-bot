# Price Tracker Telegram Bot (crypto + FX)

Portfolio-ready Telegram bot that tracks **crypto** (CoinGecko) and **FX rates** (Frankfurter) and sends alerts when a price crosses your target.

## Features
- Track **crypto** prices (CoinGecko): `BTC/USD`, `ETH/UAH`, etc.
- Track **FX rates** (Frankfurter): `USD/UAH`, `EUR/USD`, etc.
- Alerts on crossing thresholds: `>= target` or `<= target`
- Inline menus and tracker management (pause/resume/delete)
- PostgreSQL + SQLAlchemy (async) + APScheduler (async)

## Tech stack
- Python 3.11
- aiogram 3
- PostgreSQL (asyncpg)
- SQLAlchemy 2 (async)
- APScheduler
- aiohttp
- Docker + docker-compose

---

## Quick start (Docker)
1) Create `.env` from `.env.example`
2) Put your Telegram bot token into `BOT_TOKEN`
3) Run:

```bash
docker compose up --build
```

The bot will:
- wait for Postgres to be ready
- create DB tables automatically (MVP-friendly)
- start scheduler + polling

## Quick start (local)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt

# start Postgres locally or use docker only for db:
docker compose up -d db

copy .env.example .env  # Windows: copy
# edit .env

python -m app.main
```

---

## Bot commands
- `/start` — open menu
- `/add` — add a tracker
- `/trackers` — list/manage your trackers
- `/help` — help
