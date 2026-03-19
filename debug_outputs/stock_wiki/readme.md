生成五张卡的本地结果

``` bash
python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_summary_card.py
python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_entity_info_card.py
python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_timeline_card.py
python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_watch_calendar_card.py
python /Users/hujiawei/Documents/PomeFiDemo/scripts/debug_relationship_card.py
```

让前端只读本地文件

``` bash
POMEFI_LOCAL_FIXTURE_DIR=/Users/hujiawei/Documents/PomeFiDemo/debug_outputs/stock_wiki streamlit run /Users/hujiawei/Documents/PomeFiDemo/app.py
```

建议顺序是：

summary
timeline
entity_info
watch_calendar
relationship

前两个先把 AkShare 数据链路打稳，后面三个主要是 Kimi/Formula 链路。现在 watch_calendar 和 relationship 已经能稳定产出 JSON 文件了，接下来不是修“有没有文件”，而是修“为什么是 ConnectError”。

最稳的 workflow 是：

跑单个脚本
看 debug_outputs/stock_wiki/*.json
我根据这个 JSON 判断是“成功”还是“继续修”
该卡跑通后再接前端 fixture 渲染

先优化 timeline，把事件标进图里
再优化 relationship，把 nodes/edges 画成 map
最后再细修 summary/entity_info/watch_calendar 的视觉排版