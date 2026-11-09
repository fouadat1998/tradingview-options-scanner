# TradingView Options Scanner — safe starter project

**Status: scaffold / DEMO ONLY.** Not a live scanner. No broker execution. No API keys are bundled. The scheduler, market-data connectors, options-data connectors, secure public webhook gateway, persistent alert store and Telegram live integration are **not deployed**. The sample watchlist is illustrative and **not** your actual TradingView watchlist.

## Approved requirements
- Watchlist chosen in TradingView; must be synced through a supported workflow.
- Reports every 30 minutes around the clock (once deployment and scheduler are configured).
- CALL/PUT options with 0–7 calendar days to expiration.
- Maximum total cost **$65 including estimated buy fees**; default fees $2.54 are only a placeholder, replace with broker-specific fees.
- Daily trend, ranked strong/medium candidates, candidate stocks and stale-price warnings.
- Alerts only; never place orders.

## Local smoke test (Windows PowerShell)
```powershell
cd tradingview_options_scanner
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python -m scanner.runner
uvicorn scanner.app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/health` and `/watchlist`. No secrets are needed for these tests. Do not expose this local server to the internet.

## TradingView integration
1. In TradingView, create/choose your watchlist and configure Watchlist Alerts where your plan supports them.
2. Alerts are *events*, not a guaranteed API for reading the full private watchlist. For initial sync, export the list or enter symbols into `config/watchlist.json` manually; verify changes after adding/removing symbols.
3. Before production, put an HTTPS gateway in front of `/webhook/tradingview` that checks a random secret in the alert JSON body and forwards a private `X-Webhook-Secret` header. TradingView may not allow custom headers. Never put Telegram tokens or brokerage secrets in TradingView alert messages.
4. Webhook alerts alone are insufficient for scanning every symbol at a fixed interval: connect a licensed historical/intraday market data API and options-chain API.

## Telegram integration
1. Open `@BotFather` in Telegram, use `/newbot` and save the token privately.
2. Start a chat with the bot; get your chat ID using Telegram Bot API `getUpdates` in a secure local environment.
3. Put `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in local environment variables (never commit them).
4. Use `scanner.report.send_telegram` only after a manual approval/test. No automatic messages are sent by this starter project.

## Next engineering tasks (not yet implemented)
- Integrate provider adapters for market candles, current quote timestamps, and option chains.
- Build indicator calculation and backtested scoring with configurable signal thresholds.
- Store signal history, deduplicate alerts, handle closed markets and holidays.
- Add APScheduler interval job at 30 minutes with persistent state, health monitoring and rate limits.
- Implement Telegram report delivery with retries, redaction and observability.
- Validate full watchlist sync, live quote freshness, bid/ask, spread, OI, volume, fees and 0–7-day expiries before enabling live reports.
- Deploy to an always-on server only after explicit approval.

## Safety
Never fabricate options quotes, Greeks, liquidity, prices, profit targets, or probability of success. Reject missing/stale data. Candidate scores are rankings, not statistical success probabilities. Do not store credentials in source files.

## Telegram control panel (new)

The Telegram panel has six Arabic-labeled emoji buttons: 🟢 Start scan, 🔴 Stop scan, 📊 Report now, 📡 Status, 📋 Watchlist, ⚙️ Settings. Telegram inline keyboards support emoji icons; they do not support custom button background colors. Only the configured TELEGRAM_CHAT_ID can control the bot.

1. Create a Telegram bot with @BotFather. Keep its token private.
2. Send `/start` to the bot. Obtain your numeric chat ID using a trusted local method (e.g. call `getUpdates` with the bot token on your own machine); never paste the token into chat.
3. In your local `.env` or environment, configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (the starter does **not** auto-load `.env`; set environment variables in the shell or use your own secret manager).
4. Test with `python -m pytest -q` before running anything connected.
5. After credentials are configured and you explicitly approve Telegram testing, run `python -m scanner.telegram_control` from the project root. This begins Telegram long-polling; send `/start` to display the buttons.
6. The Start button enables **demo-only** reports every 30 minutes while the process is running; Stop disables them. Reports explicitly state that no verified live market/option data is connected. Restarting the process does not automatically enable a stopped bot. A previously enabled state is persisted; stop it from Telegram before shutting down if desired.

Security and limitations: Telegram bot messages are not an execution or broker interface. Do not expose the bot token. Only one polling process should run per bot token. This version does not connect to TradingView Plus, a market-data provider, or an options-chain API, and does not auto-start or deploy. To run 24/7 later, deploy a supervised process after successful integration tests. Telegram button colors are represented with colored emoji rather than actual button background styling.


## Mobile update — strong contracts buttons
- Replaced the proposed **medium contracts** button with **🔥 أقوى العقود** (top-ranked strong contracts).
- Also retained **💪 العقود القوية** as a separate category. Both explicitly report that verified options-chain data is not connected, rather than fabricating candidates.
- For GitHub on mobile, upload extracted project files and preserve the `scanner/`, `config/`, and `tests/` paths. GitHub's browser uploader may not preserve folders when selecting individual files; a Git client or desktop-mode folder upload may be necessary. Do not commit `.env` or credentials.
- Render deployment is NOT enabled. The Background Worker may be paid; review pricing before creation. Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in Render Environment only, then run tests before approving deployment.
