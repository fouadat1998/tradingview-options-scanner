"""Telegram polling bot: alerts only, never executes orders."""
import asyncio
import json
import logging
import os
import math
from datetime import datetime, timezone
from pathlib import Path
import httpx
from .core import rank_contracts
from .provider import fetch_option_snapshots

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / 'config' / 'watchlist.json'
STATE = ROOT / 'state.json'
LOG = logging.getLogger(__name__)
BUTTONS = [['🟢 بدء الفحص', '🔴 إيقاف الفحص'], ['📊 تقرير الآن', '🔥 أقوى العقود'],
           ['💪 العقود القوية', '💰 تحديد الميزانية'], ['📡 الحالة', '📋 قائمة الأسهم'], ['⚙️ الإعدادات']]


def get_symbols():
    data = json.loads(WATCHLIST.read_text(encoding='utf-8'))
    return [str(s).strip().upper() for s in data['symbols'] if str(s).strip()][:30]


def get_state():
    try:
        data = json.loads(STATE.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Invalid state')
        return data
    except (OSError, ValueError):
        return {'enabled': False}


def update_state(**changes):
    data = get_state()
    data.update(changes)
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temp.replace(STATE)


def set_state(enabled):
    update_state(enabled=enabled)


def get_budget():
    value = get_state().get('budget')
    if value is None:
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) and value > 0 else None
    except (TypeError, ValueError):
        return None


def parse_budget(text):
    try:
        value = float(text.strip())
    except (TypeError, ValueError, AttributeError):
        return None
    if not math.isfinite(value) or not 1 <= value <= 1000000:
        return None
    return round(value, 2)


def keyboard():
    return {'keyboard': [[{'text': s} for s in row] for row in BUTTONS], 'resize_keyboard': True}


async def report():
    budget = get_budget()
    if budget is None:
        return '💰 حدد ميزانية الصفقة أولاً من زر 💰 تحديد الميزانية.'
    if not os.getenv('POLYGON_API_KEY'):
        return '⚠️ بيانات عقود الأوبشن الحية غير متصلة. لا توجد توصيات أو أسعار مؤكدة.'
    found = []
    errors = []
    async with httpx.AsyncClient(timeout=25) as client:
        for symbol in get_symbols():
            try:
                found.extend(await fetch_option_snapshots(symbol, client))
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                LOG.warning('Provider error for %s: %s', symbol, type(exc).__name__)
                errors.append(symbol)
    if errors:
        return '⚠️ تعذر التحقق من بيانات جميع الأسهم: ' + ', '.join(errors) + '. تم حجب التقرير منعًا لعرض نتائج ناقصة.'
    # Reject quotes older than 15 min. Closed-market snapshots will not be called live.
    now = datetime.now(timezone.utc)
    fresh = []
    for c in found:
        try:
            dt = datetime.fromisoformat(c['timestamp'])
            if dt.tzinfo and 0 <= (now-dt).total_seconds() <= 900:
                fresh.append(c)
        except (ValueError, TypeError, KeyError):
            pass
    ranked = rank_contracts(fresh, max_cost=budget,
                            fees=float(os.getenv('ESTIMATED_FEES', '2.54')))
    if not ranked:
        return '📊 لا توجد عقود مستوفية للشروط بأسعار حديثة ومؤكدة. قد يكون السوق مغلقًا.'
    lines = ['🔥 أقوى العقود حسب السيولة (ليست احتمالات نجاح أو أوامر شراء):']
    for c in ranked[:5]:
        lines.append(f"{c['symbol']} {c['type']} {c['strike']} | {c['expiration']} | Ask ${c['ask']} | إجمالي تقريبي ${c['estimated_total_cost']} | سبريد {c['spread_pct']}%")
    lines.append('⚠️ التكاليف تقديرية. تحقق من السعر والسيولة والرسوم لدى الوسيط قبل أي قرار.')
    return '\n'.join(lines)


async def run():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id or not chat_id.lstrip('-').isdigit():
        raise SystemExit('Set TELEGRAM_BOT_TOKEN and numeric TELEGRAM_CHAT_ID in environment')
    base = f'https://api.telegram.org/bot{token}'
    interval = max(5, int(os.getenv('SCAN_INTERVAL_MINUTES', '30'))) * 60
    async with httpx.AsyncClient(timeout=45) as client:
        async def send(message):
            r = await client.post(base+'/sendMessage', json={'chat_id': chat_id, 'text': message,
                                                              'reply_markup': keyboard()})
            r.raise_for_status()
        offset = None
        last_report = asyncio.get_running_loop().time()
        while True:
            try:
                params = {'timeout': 25}
                if offset is not None:
                    params['offset'] = offset
                r = await client.get(base+'/getUpdates', params=params)
                r.raise_for_status()
                for update in r.json().get('result', []):
                    offset = update['update_id'] + 1
                    msg = update.get('message') or {}
                    if str((msg.get('chat') or {}).get('id')) != chat_id:
                        continue
                    cmd = msg.get('text', '')
                    if cmd == '💰 تحديد الميزانية':
                        update_state(awaiting_budget=True)
                        await send('💰 أدخل ميزانية الصفقة بالدولار، مثل 25 أو 50 أو 100. لإلغاء الإدخال أرسل إلغاء.')
                    elif get_state().get('awaiting_budget') and cmd.strip() == 'إلغاء':
                        update_state(awaiting_budget=False)
                        await send('تم إلغاء تعديل الميزانية.')
                    elif get_state().get('awaiting_budget'):
                        amount = parse_budget(cmd)
                        if amount is None:
                            await send('⚠️ أدخل مبلغًا صحيحًا بين 1 و1,000,000 دولار، أو أرسل إلغاء.')
                        else:
                            update_state(budget=amount, awaiting_budget=False)
                            await send(f'✅ تم حفظ ميزانية الصفقة: ${amount:,.2f} شاملة الرسوم التقديرية.')
                    elif cmd == '🟢 بدء الفحص':
                        set_state(True)
                        last_report = asyncio.get_running_loop().time()
                        await send('🟢 تم تفعيل التقارير الدورية. لا يتم تنفيذ صفقات.')
                    elif cmd == '🔴 إيقاف الفحص':
                        set_state(False)
                        await send('🔴 تم إيقاف التقارير الدورية.')
                    elif cmd in ('📊 تقرير الآن', '🔥 أقوى العقود', '💪 العقود القوية'):
                        await send(await report())
                    elif cmd == '📡 الحالة':
                        await send(('🟢 الفحص مفعّل' if get_state().get('enabled') else '🔴 الفحص متوقف') +
                                   (' | مزود البيانات متصل بالمفتاح' if os.getenv('POLYGON_API_KEY') else ' | مزود البيانات غير مهيأ'))
                    elif cmd == '📋 قائمة الأسهم':
                        await send('📋 ' + ', '.join(get_symbols()))
                    elif cmd == '⚙️ الإعدادات':
                        await send(f'⚙️ التكرار {interval//60} دقيقة | الميزانية ' + (f'${get_budget():,.2f}' if get_budget() is not None else 'لم تحدد بعد') + ' | صلاحية 0–7 أيام | تنبيهات فقط')
                    else:
                        await send('مرحبًا! استخدم الأزرار للتحكم بالماسح. لا توجد صفقات آلية.')
                now = asyncio.get_running_loop().time()
                if get_state().get('enabled') and now - last_report >= interval:
                    last_report = now
                    await send(await report())
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                LOG.error('Telegram loop error: %s', type(exc).__name__)
                await asyncio.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
