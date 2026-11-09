"""Polygon/Massive options snapshot adapter. A paid data entitlement may be required."""
import os
import httpx
from datetime import datetime, timezone

BASE = 'https://api.polygon.io'

async def fetch_option_snapshots(symbol, client=None):
    key = os.getenv('POLYGON_API_KEY')
    if not key:
        raise RuntimeError('NO_MARKET_DATA_PROVIDER: Set POLYGON_API_KEY securely')
    own = client is None
    client = client or httpx.AsyncClient(timeout=20)
    try:
        url = f'{BASE}/v3/snapshot/options/{symbol}'
        results = []
        for _ in range(10):
            response = await client.get(url, params={'apiKey': key, 'limit': 250} if url.startswith(BASE + '/v3/snapshot') else {'apiKey': key})
            response.raise_for_status()
            data = response.json()
            for raw in data.get('results', []):
                details = raw.get('details') or {}
                quote = raw.get('last_quote') or {}
                day = raw.get('day') or {}
                # Explicit timestamp required; reject stale quotes downstream.
                ts = quote.get('last_updated')
                if not ts:
                    continue
                try:
                    stamp = datetime.fromtimestamp(int(ts)/1e9, tz=timezone.utc).isoformat()
                except (ValueError, TypeError, OverflowError):
                    continue
                results.append({'symbol': symbol, 'ticker': details.get('ticker'),
                    'type': str(details.get('contract_type', '')).upper(),
                    'expiration': details.get('expiration_date'),
                    'strike': details.get('strike_price'),
                    'bid': quote.get('bid'), 'ask': quote.get('ask'),
                    'volume': day.get('volume'), 'open_interest': raw.get('open_interest'),
                    'timestamp': stamp})
            nxt = data.get('next_url')
            if not nxt:
                break
            if not nxt.startswith(BASE + '/'):
                raise RuntimeError('Unsafe pagination URL')
            url = nxt
        return results
    finally:
        if own:
            await client.aclose()
