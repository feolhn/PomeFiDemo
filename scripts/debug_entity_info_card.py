from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from scripts.debug_skill import default_output_path, write_skill_output, _run_skill
from scripts.target_stock import load_target_stock


def main() -> int:
    symbol, company_name = load_target_stock()
    had_error = False
    try:
        payload = asyncio.run(_run_skill("entity_info", symbol, company_name))
    except Exception as exc:  # pragma: no cover - debug fallback
        from scripts.debug_skill import build_error_payload

        payload = build_error_payload("entity_info", symbol, company_name, exc)
        had_error = True
    write_skill_output(payload, default_output_path("entity_info"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
