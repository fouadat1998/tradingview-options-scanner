import json
import os
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title='TradingView Options Scanner - safe skeleton')
ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / 'config' / 'watchlist.json'

class Alert(BaseModel):
    symbol: str = Field(pattern=r'^[A-Za-z0-9.:-]{1,25}$')
    action: str = Field(pattern=r'^(signal|add|remove)$')
    timeframe: str | None = None

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': os.getenv('MODE', 'demo'), 'trading_enabled': False}

@app.post('/webhook/tradingview')
def tradingview(alert: Alert, x_webhook_secret: str | None = Header(default=None)):
    secret = os.getenv('WEBHOOK_SECRET')
    if not secret or x_webhook_secret != secret:
        raise HTTPException(status_code=401, detail='Unauthorized')
    # TradingView webhook cannot always set custom headers; use a trusted gateway
    # to validate a secret in the request body and forward this internal header.
    if alert.action in ('add', 'remove'):
        raise HTTPException(status_code=409, detail='Watchlist changes require explicit sync; alert is not proof of membership')
    return {'accepted': True, 'symbol': alert.symbol.upper(), 'note': 'Signal received; no order placed'}

@app.get('/watchlist')
def watchlist():
    return json.loads(WATCHLIST.read_text(encoding='utf-8'))
