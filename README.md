# PomeFi v0.7.0 Stock Wiki

PomeFi 当前实现为 Router -> Parallel Skills -> Aggregator 的股票百科 MVP。

## Current Phase

- `pomefi.stock_wiki.router`：意图与 A 股标的解析
- `pomefi.stock_wiki.orchestrator`：5 个并行技能调度
- `pomefi.stock_wiki.aggregator`：统一 payload 与 metadata
- `pomefi.stock_wiki.engine`：主执行链路
- `scripts/probe_stock_wiki.py`：Stock Wiki live probe

## Repository Layout

```text
docs/
  PRD_v0.6.4_c_review.md
  Kimi_API_Usage_Guide_v1.md
pomefi/
  agent/
  stock_wiki/
  tools/
  ui/
scripts/
  probe_moonshot_sdk.py
  probe_stock_wiki.py
tests/
```
