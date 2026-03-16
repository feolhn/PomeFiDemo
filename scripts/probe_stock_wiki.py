from __future__ import annotations

import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from app import _load_stock_table
from pomefi.config import print_probe_env_summary, validate_probe_env_or_raise
from pomefi.stock_wiki import run_stock_wiki_analysis

EXIT_OK = 0
EXIT_FAIL = 1


async def main() -> int:
    try:
        config = validate_probe_env_or_raise()
    except Exception as exc:
        print(f"[ENV_CHECK] FAIL - {exc}")
        return EXIT_FAIL

    print_probe_env_summary(config)
    print("[ENV_CHECK] PASS")

    payload = await run_stock_wiki_analysis(
        question="300750 最近有什么关键风险和关系链变化？",
        config=config,
        stock_table_loader=_load_stock_table,
    )
    card = payload["card"]
    data = dict(card.get("data") or {})
    metadata = dict(card.get("metadata") or {})

    required_cards = ("summary", "entity_info", "timeline", "watch_calendar", "relationship")
    missing = [name for name in required_cards if name not in data]
    if missing:
        print(f"[PROBE] FAIL - missing cards: {missing}")
        return EXIT_FAIL

    print("[PROBE] cards=5 PASS")
    print(f"[PROBE] quality_status={card.get('quality_status')}")
    print(f"[PROBE] partial_release={metadata.get('partial_release')}")
    print(f"[PROBE] relationship_pending={metadata.get('relationship_pending')}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
