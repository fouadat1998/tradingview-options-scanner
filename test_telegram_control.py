from scanner.telegram_control import keyboard, response_for

def test_keyboard_has_eight_actions():
    assert {b['callback_data'] for row in keyboard()['inline_keyboard'] for b in row} == {'start','stop','report','status','watchlist','settings','top_contracts','strong_contracts'}

def test_start_stop_changes_only_scanner_state():
    state = {'enabled': False, 'interval_minutes': 30, 'live_data': False}
    msg, changed = response_for('start', state, ['TSLA'])
    assert changed and state['enabled'] and state['live_data'] is False
    msg, changed = response_for('stop', state, ['TSLA'])
    assert changed and not state['enabled']

def test_report_is_demo():
    msg, changed = response_for('report', {'enabled': False}, ['AAPL'])
    assert 'DEMO' in msg and not changed


def test_strong_contracts_require_live_data():
    for action in ("top_contracts", "strong_contracts"):
        message, changed = response_for(action, {"enabled": False}, ["TSLA"])
        assert "لا تتوفر" in message and not changed
