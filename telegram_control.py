"""Telegram inline keyboard control. Explicit opt-in to start polling; no broker orders."""
import json
import os
import time
from pathlib import Path

import httpx
from scanner.report import build_report

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / 'config' / 'bot_state.json'
WATCHLIST = ROOT / 'config' / 'watchlist.json'


def read_state():
    if not STATE.exists():
        return {'enabled': False, 'interval_minutes': 30, 'live_data': False}
    return json.loads(STATE.read_text(encoding='utf-8'))


def save_state(state):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(STATE)


def keyboard():
    return {'inline_keyboard': [
        [{'text': '🟢 تشغيل الفحص', 'callback_data': 'start'}, {'text': '🔴 إيقاف الفحص', 'callback_data': 'stop'}],
        [{'text': '🔥 أقوى العقود', 'callback_data': 'top_contracts'}, {'text': '💪 العقود القوية', 'callback_data': 'strong_contracts'}],
        [{'text': '📊 تقرير الآن', 'callback_data': 'report'}, {'text': '📡 حالة النظام', 'callback_data': 'status'}],
        [{'text': '📋 قائمة الأسهم', 'callback_data': 'watchlist'}, {'text': '⚙️ الإعدادات', 'callback_data': 'settings'}],
    ]}


def response_for(action, state, symbols):
    if action == 'start':
        state['enabled'] = True
        return '🟢 تم تشغيل الفحص التجريبي كل 30 دقيقة. لا توجد توصيات حقيقية أو صفقات.', True
    if action == 'stop':
        state['enabled'] = False
        return '🔴 تم إيقاف الفحص والتقارير المجدولة.', True
    if action in ('top_contracts', 'strong_contracts'):
        label = '🔥 أقوى العقود' if action == 'top_contracts' else '💪 العقود القوية'
        return f'{label}\n🧪 لا تتوفر حاليًا بيانات عقود أوبشن حقيقية موثقة. لا توجد ترشيحات حتى يتم ربط مزود البيانات والتحقق من السيولة والميزانية.', False
    if action == 'report':
        return '📊 ' + build_report(symbols, demo=True), False
    if action == 'status':
        return f"📡 الحالة: {'🟢 يعمل' if state['enabled'] else '🔴 متوقف'}\n⏱ الفاصل: 30 دقيقة\n🧪 بيانات السوق: غير متصلة\n🚫 التداول الآلي: معطل", False
    if action == 'watchlist':
        return '📋 الأسهم: ' + (', '.join(symbols) or 'القائمة فارغة'), False
    if action == 'settings':
        return '⚙️ الميزانية: $65 شاملة رسوم الشراء\n📅 الانتهاء: 0–7 أيام\n⏱ التحديث: 30 دقيقة\n🔐 التحكم: محصور في Chat ID المصرح به', False
    return 'استخدم الأزرار المتاحة.', False


def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    allowed = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not allowed:
        raise SystemExit('Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. No polling started.')
    base = f'https://api.telegram.org/bot{token}'
    offset = None
    last_report = time.monotonic()
    print('Telegram control ready; demo only, no broker integration.', flush=True)
    with httpx.Client(timeout=40) as client:
        def api(method, data):
            res = client.post(f'{base}/{method}', json=data)
            res.raise_for_status()
            result = res.json()
            if not result.get('ok'):
                raise RuntimeError('Telegram API request failed')
            return result['result']
        while True:
            try:
                updates = api('getUpdates', {'offset': offset, 'timeout': 25, 'allowed_updates': ['message', 'callback_query']})
                for update in updates:
                    offset = update['update_id'] + 1
                    callback = update.get('callback_query')
                    message = (callback or {}).get('message') if callback else update.get('message')
                    if not message:
                        continue
                    chat_id = str(message['chat']['id'])
                    if chat_id != allowed:
                        if callback:
                            api('answerCallbackQuery', {'callback_query_id': callback['id'], 'text': 'غير مصرح', 'show_alert': True})
                        continue
                    state = read_state()
                    symbols = json.loads(WATCHLIST.read_text(encoding='utf-8')).get('symbols', [])
                    action = callback['data'] if callback else 'menu'
                    if callback:
                        api('answerCallbackQuery', {'callback_query_id': callback['id']})
                    if action == 'menu':
                        text = '📊 لوحة تحكم Options Scanner\n🧪 وضع تجريبي — لا توجد بيانات سوق مباشرة.'
                    else:
                        text, changed = response_for(action, state, symbols)
                        if changed:
                            save_state(state)
                            last_report = time.monotonic()
                    api('sendMessage', {'chat_id': allowed, 'text': text, 'reply_markup': keyboard()})
                state = read_state()
                if state['enabled'] and time.monotonic() - last_report >= state['interval_minutes'] * 60:
                    symbols = json.loads(WATCHLIST.read_text(encoding='utf-8')).get('symbols', [])
                    api('sendMessage', {'chat_id': allowed, 'text': '⏱ تقرير دوري\n' + build_report(symbols, demo=True), 'reply_markup': keyboard()})
                    last_report = time.monotonic()
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError) as exc:
                print(f'Telegram polling error: {type(exc).__name__}', flush=True)
                time.sleep(5)


if __name__ == '__main__':
    main()
