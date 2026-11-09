# TradingView Options Scanner — Telegram alert bot

## Status and limitations
Runnable Telegram alert bot with an optional Polygon/Massive option-snapshot connector. **Not a fully validated live trading signal engine.** No broker execution. No TradingView watchlist sync or TradingView webhook implemented. A paid market-data entitlement may be required. Quote freshness and incomplete data fail closed. Liquidity ranking is **not** a prediction of profitability. Never treat these reports as investment advice.

## Quick start (Python 3.11+)
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
# Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as environment variables in a secure host
python -m scanner.telegram_control
```

Create a bot via @BotFather, message it, and obtain your chat ID using Telegram's getUpdates privately. Never commit tokens or share them in chat. Do not run two polling processes using the same token. `.env.example` documents configuration, but `.env` is NOT auto-loaded. Put environment variables in your host's secret manager. Add `POLYGON_API_KEY` only if your account is authorized to retrieve the required options snapshots. Edit `config/watchlist.json` to change symbols (illustrative defaults only). Ensure your provider supplies real-time quote timestamps and required data fields; otherwise reports are blocked. Estimated fees are placeholders; replace with your broker's actual fees.

## Hosting
Deploy as a persistent **background worker** on a service that supports long-running Python processes. Build command: `pip install -r requirements.txt`; start command: `python -m scanner.telegram_control`. Configure secrets in the host UI. Polling must be single-instance. The local state file is ephemeral on many hosts: use a persistent volume or database for production reliability. This package does not include automatic hosting or webhook exposure.

## Before real-world use
Implement proper market-hours calendar, durable scheduler/state and deduplication, quote freshness testing per data entitlement, provider pagination/limits, trend and backtested scoring, broker fee verification, monitoring, alert retries, TradingView watchlist synchronization and end-to-end tests. Live order execution is intentionally excluded.

## Interactive trade budget
Press **💰 تحديد الميزانية** in Telegram, then send a number in USD (for example `100`). The bot validates and persists the amount in `state.json`; it uses the amount as the **maximum total estimated cost including fees** for each candidate contract. Send `إلغاء` to cancel budget entry. Until a budget is entered, scans do not produce contract suggestions. For persistent hosting, store `state.json` on a durable volume.
