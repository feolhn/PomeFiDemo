```markdown
# 产品PRD_v0.3.0_Diagram
> Streamlit Demo MVP 架构图
> 原则：极简 / 单文件驱动 / 单进程运行 / 仅验证 Skill 卡片展示闭环

---

# 一、目录结构（Tree）

pomefi_streamlit_mvp/
│
├── app.py                 # 主入口（四栏页面 + Skill预览）
├── skill_engine.py        # Akshare + Kimi API 调用封装（唯一真实数据流）
├── mock_data.py           # 其他页面 Mock 数据
├── utils.py               # JSON 整理 & 文本处理函数
│
├── requirements.txt       # 依赖
├── .streamlit/
│   └── secrets.toml       # API Key
└── README.md              # 部署说明

说明：
- 不再区分 frontend / core / api / registry
- 不拆 skills / services / components 目录
- 不做 Schema 校验
- 不构建 Skill OS
- 单体 Streamlit 应用（Monolith）

---

# 二、极简架构图（Architecture Diagram）

                ┌────────────────────────┐
                │        app.py          │
                │  页面渲染 + 交互入口     │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │     skill_engine.py    │
                │  数据抓取 + 大模型处理   │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │      External APIs     │
                │  - Akshare             │
                │  - Kimi API            │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │     JSON Structured    │
                │        Result          │
                └───────────┬────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │   Streamlit Card UI    │
                │  + Plotly Interactive  │
                └────────────────────────┘

核心特征：
- 单进程
- 单真实数据模块
- 无额外抽象层
- 所有调用链清晰可见

---

# 三、边界图（Boundary Diagram）

                         ┌────────────────────┐
                         │    Streamlit UI    │
                         │  页面 + 卡片展示    │
                         └──────────┬─────────┘
                                    │
                                    │ 调用本地函数
                                    ▼
                         ┌────────────────────┐
                         │   skill_engine.py   │
                         │  数据抓取 + JSON拼装 │
                         └──────────┬─────────┘
                                    │
                                    │ 外部数据请求
                                    ▼
                 ┌──────────────────────────────┐
                 │        External APIs         │
                 │  - Akshare                   │
                 │  - Kimi API                  │
                 └──────────────────────────────┘

边界原则：
- UI 层只负责展示
- skill_engine.py 是唯一真实逻辑模块
- utils.py 只做辅助函数
- mock_data.py 仅用于非核心页面
- 不引入中间层

---

# 四、运行流程（Data Flow）

用户点击按钮
        ↓
app.py 调用 skill_engine
        ↓
Akshare 拉取数据
        ↓
Kimi 生成结构化文本
        ↓
整理为 JSON
        ↓
Streamlit 渲染卡片
        ↓
Plotly 输出交互图表

---

# 五、MVP 原则

1. 只跑通三个 Skill
2. 只支持固定测试输入
3. 仅一个真实数据流模块
4. 无数据库
5. 无缓存系统
6. 无扩展性设计
7. 可直接部署至 Streamlit Cloud

---

# 六、目标状态

部署平台：Streamlit Cloud

要求：
- 打开即用
- 无报错
- 图表正常
- secrets.toml 可安全读取 API Key

---

# 总结

v0.3.0_Diagram 的核心理念：

> 用最少的文件、最短的数据路径，跑通一个高质感 Skill 卡片展示闭环。

复杂架构不在本版本目标内。
```

