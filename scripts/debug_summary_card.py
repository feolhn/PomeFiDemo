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


def main() -> int:
    payload = asyncio.run(_run_skill("summary", "300750", "宁德时代"))
    write_skill_output(payload, default_output_path("summary"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
