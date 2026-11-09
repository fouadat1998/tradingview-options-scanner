from datetime import date, timedelta
from scanner.core import rank_contracts
from scanner.telegram_control import keyboard


def test_cost_and_expiry():
    today = date.today()
    item = {'expiration': (today+timedelta(days=3)).isoformat(), 'bid': .35, 'ask': .40,
            'volume': 50, 'open_interest': 100, 'type': 'CALL',
            'timestamp': '2026-11-09T12:00:00+00:00'}
    assert len(rank_contracts([item], as_of=today)) == 1
    assert rank_contracts([{**item, 'ask': 1.00}], as_of=today) == []
    assert rank_contracts([{**item, 'expiration': (today+timedelta(days=8)).isoformat()}], as_of=today) == []


def test_telegram_buttons():
    buttons = str(keyboard())
    assert '🔥 أقوى العقود' in buttons
    assert '🟢 بدء الفحص' in buttons
