# PomeFi v0.6.4 Rebuild

PomeFi is being rebuilt from scratch on top of the Moonshot/Kimi tool loop prototype in `scripts/probe_moonshot_sdk.py`.

## Current Phase

Step 3 is complete when the core loop is no longer trapped inside `scripts/probe_moonshot_sdk.py`:

- `pomefi.config` owns config resolution and probe validation
- `pomefi.tools.formula` owns Formula tool loading and fiber execution
- `pomefi.agent.loop` owns the reusable Kimi tool loop
- `scripts/probe_moonshot_sdk.py` is now a thin live-probe entrypoint

## Planned Shape

- Single-agent financial analysis engine
- Streamlit single-page "Finance Garden" card UI
- Formula-backed `date` and `web_search`
- Single custom `akshare_tool` for numeric finance data

## Repository Layout

```text
docs/
  PRD_v0.6.4_c_review.md
  Kimi_API_Usage_Guide_v1.md
pomefi/
  agent/
  tools/
  ui/
scripts/
  probe_moonshot_sdk.py
tests/
```
