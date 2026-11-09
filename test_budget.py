from scanner import telegram_control as bot


def test_budget_entry_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, 'STATE', tmp_path / 'state.json')
    assert bot.get_budget() is None
    assert bot.parse_budget('100') == 100
    assert bot.parse_budget('25.50') == 25.5
    for invalid in ('', 'abc', '-1', '0', 'nan', 'inf', '1000001'):
        assert bot.parse_budget(invalid) is None
    bot.update_state(enabled=True, awaiting_budget=True)
    bot.update_state(budget=bot.parse_budget('100'), awaiting_budget=False)
    assert bot.get_budget() == 100
    assert bot.get_state()['enabled'] is True
    assert bot.get_state()['awaiting_budget'] is False


def test_budget_button():
    assert '💰 تحديد الميزانية' in str(bot.keyboard())
