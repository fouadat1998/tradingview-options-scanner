from datetime import date, datetime, timezone
from decimal import Decimal
from scanner.core import eligible_contract, score_signal


def test_score():
    assert score_signal(20, 20, 20, 20, 20) == (100, 'strong')
    assert score_signal(12, 12, 12, 12, 12) == (60, 'medium')


def test_contract_budget_and_expiry():
    now = datetime.now(timezone.utc)
    c = dict(expiry=date.today().isoformat(), ask='0.60', bid='0.55', quote_at=now.isoformat(), volume=100, open_interest=100)
    assert eligible_contract(c, today=date.today())[0]
    c['ask'] = '0.70'
    assert eligible_contract(c, today=date.today()) == (False, 'over_budget')


def test_missing_quote_rejected():
    assert eligible_contract({}, today=date.today()) == (False, 'missing_or_invalid_quote')
