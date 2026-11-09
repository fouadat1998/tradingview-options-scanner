"""Dry-run only. No API requests and no automatic live sending."""
import json
from pathlib import Path
from scanner.report import build_report


def main():
    path = Path(__file__).resolve().parent.parent / 'config' / 'watchlist.json'
    symbols = json.loads(path.read_text(encoding='utf-8'))['symbols']
    print(build_report(symbols))

if __name__ == '__main__':
    main()
