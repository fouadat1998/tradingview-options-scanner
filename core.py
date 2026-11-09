"""Conservative option candidate filter. Never substitutes fabricated market data."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def rank_contracts(contracts, *, max_cost=65, fees=2.54, as_of=None):
    today = as_of or date.today()
    ranked = []
    for item in contracts:
        try:
            expiry = date.fromisoformat(item['expiration'])
            days = (expiry - today).days
            bid = Decimal(str(item['bid']))
            ask = Decimal(str(item['ask']))
            volume = int(item['volume'])
            oi = int(item['open_interest'])
            kind = str(item['type']).upper()
            stamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            if stamp.tzinfo is None or kind not in ('CALL', 'PUT'):
                continue
            if not (0 <= days <= 7 and 0 < bid <= ask and volume >= 1 and oi >= 1):
                continue
            cost = ask * 100 + Decimal(str(fees))
            if cost > Decimal(str(max_cost)):
                continue
            spread = (ask - bid) / ask
            if spread > Decimal('0.20'):
                continue
            # Liquidity score, not win probability or trade recommendation.
            score = min(volume, 500) / 10 + min(oi, 1000) / 20 - float(spread) * 100
            ranked.append({**item, 'estimated_total_cost': round(float(cost), 2),
                           'spread_pct': round(float(spread) * 100, 2),
                           'liquidity_score': round(score, 2)})
        except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
            continue
    return sorted(ranked, key=lambda x: x['liquidity_score'], reverse=True)
