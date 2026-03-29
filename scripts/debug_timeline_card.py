from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

from scripts.debug_skill import default_output_path, write_skill_output, _run_timeline_bundle
from scripts.target_stock import load_target_stock


def _branch_output_path(name: str) -> Path:
    return default_output_path(f"timeline.{name}")


def main() -> int:
    symbol, company_name = load_target_stock()
    payload = asyncio.run(_run_timeline_bundle(symbol, company_name))
    write_skill_output(payload, default_output_path("timeline"))
    branches = dict(payload.get("branches") or {})
    if "akshare" in branches:
        write_skill_output(branches["akshare"], _branch_output_path("akshare"))
    if "kimi" in branches:
        write_skill_output(branches["kimi"], _branch_output_path("kimi"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
