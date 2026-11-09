import os
import httpx


def build_report(symbols: list[str], *, demo: bool = True) -> str:
    heading = '🧪 DEMO / NOT LIVE' if demo else 'Market report'
    return (f'{heading}\nTradingView Options Scanner\n'
            f'Watchlist: {", ".join(symbols)}\n'
            'No verified quotes or options chain connected.\n'
            'No trade recommendations generated.')


def send_telegram(message: str) -> dict:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise RuntimeError('Telegram credentials not configured; message not sent')
    response = httpx.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat_id, 'text': message}, timeout=15)
    response.raise_for_status()
    data = response.json()
    if not data.get('ok'):
        raise RuntimeError('Telegram rejected message')
    return {'ok': True}
