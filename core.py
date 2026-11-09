from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any


def eligible_contract(contract: dict[str, Any], *, today: date, budget: Decimal = Decimal('65'), buy_fees: Decimal = Decimal('2.54'), max_days: int = 7) -> tuple[bool, str]:
    """Never treat missing, stale or invalid options quotes as tradeable."""
    try:
        expiry = date.fromisoformat(contract['expiry'])
        ask = Decimal(str(contract['ask']))
        bid = Decimal(str(contract['bid']))
        quote_at = datetime.fromisoformat(contract['quote_at'].replace('Z', '+00:00'))
        volume = int(contract['volume'])
        oi = int(contract['open_interest'])
    except (KeyError, ValueError, TypeError, ArithmeticError):
        return False, 'missing_or_invalid_quote'
    if quote_at.tzinfo is None or (datetime.now(timezone.utc) - quote_at.astimezone(timezone.utc)).total_seconds() > 900:
        return False, 'stale_quote'
    if not 0 <= (expiry - today).days <= max_days:
        return False, 'expiry_out_of_range'
    if ask <= 0 or bid < 0 or bid > ask:
        return False, 'invalid_bid_ask'
    if ask * 100 + buy_fees > budget:
        return False, 'over_budget'
    if volume < 10 or oi < 50 or (ask - bid) / ask > Decimal('0.25'):
        return False, 'low_liquidity'
    return True, 'eligible'


def score_signal(trend: int, momentum: int, volume: int, liquidity: int, risk: int) -> tuple[int, str]:
    """Five validated 0..20 components; scores rank candidates, not win probabilities."""
    values = (trend, momentum, volume, liquidity, risk)
    if any(not isinstance(v, int) or not 0 <= v <= 20 for v in values):
        raise ValueError('Each component must be an integer between 0 and 20')
    score = sum(values)
    return score, 'strong' if score >= 80 else 'medium' if score >= 60 else 'weak'
