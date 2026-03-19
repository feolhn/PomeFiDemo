from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_STOCK_PATH = PROJECT_ROOT / "config" / "target_stock.json"


def load_target_stock() -> tuple[str, str]:
    payload = json.loads(TARGET_STOCK_PATH.read_text(encoding="utf-8"))
    symbol = str(payload.get("symbol") or "").strip()
    company_name = str(payload.get("company_name") or "").strip()
    if not symbol or not company_name:
        raise RuntimeError(f"target_stock config invalid: {TARGET_STOCK_PATH}")
    return symbol, company_name
