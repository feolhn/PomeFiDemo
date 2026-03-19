# PomeFi

PomeFi 是一个 A 股单标的 Stock Wiki MVP。当前页面包含 5 张卡：

- `summary`
- `entity_info`
- `timeline`
- `watch_calendar`
- `relationship`

## 先安装

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 环境变量

项目默认从根目录 `.env` 读取配置。最少需要：

```env
KIMI_API_KEY="..."
KIMI_BASE_URL="https://api.moonshot.cn/v1"
KIMI_MODEL="kimi-k2.5"
```

## 启动前端

```bash
source venv/bin/activate
streamlit run app.py
```

页面里可以开启“使用本地 Fixture 调试”：

- 开启后，前端直接读取 `debug_outputs/stock_wiki/*.json`
- 适合修 UI，不受 live timeout 干扰

## 单卡调试

每张卡都可以单独跑，并把结果写到 `debug_outputs/stock_wiki/`：

```bash
python scripts/debug_summary_card.py
python scripts/debug_entity_info_card.py
python scripts/debug_timeline_card.py
python scripts/debug_watch_calendar_card.py
python scripts/debug_relationship_card.py
```

说明：

- 前端默认读取合并后的 `timeline.json`
- `timeline.akshare.json` 和 `timeline.kimi.json` 只是调试拆分文件

## Live Probe

验证整条主链路：

```bash
python scripts/probe_stock_wiki.py
python scripts/probe_moonshot_sdk.py
```

验证 AkShare 最小链路：

```bash
python scripts/mvp_akshare_300750.py
python scripts/probe_akshare_spot_mvp.py --symbol 300750
```

## 测试

```bash
pytest -q
```

## 文档

- [PRD_v0.6.4_c_review.md](/Users/hujiawei/Documents/PomeFiDemo/docs/PRD_v0.6.4_c_review.md)
- [Kimi_API_Usage_Guide_v1.md](/Users/hujiawei/Documents/PomeFiDemo/docs/Kimi_API_Usage_Guide_v1.md)
- [stock.md](/Users/hujiawei/Documents/PomeFiDemo/docs/stock.md)
