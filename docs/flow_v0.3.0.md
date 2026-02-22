# 产品PRD_v0.3.0_Diagram
> 版本定位：Streamlit MVP Demo 架构（极简可运行版）
> 原则：只做展示 + 1 个真实 Skill 数据流
> 目标：可直接部署 Streamlit Cloud

---

# 一、目录结构（极简版）

```
/pomefi_streamlit_mvp  
│  
├── app.py # 主入口（四栏页面 + Skill预览）  
├── skill_engine.py # Akshare + Kimi API 调用封装  
├── mock_data.py # 其他页面的Mock数据  
├── utils.py # JSON格式整理函数  
│  
├── requirements.txt # 依赖  
├── .streamlit/  
│ └── secrets.toml # API Key  
│  
└── README.md # 部署说明
```

原则：

- ❌ 不再区分 frontend/core/api/registry
- ❌ 不使用复杂分层架构
- ❌ 不做 Schema 校验
- ❌ 不构建 Skill OS
- ✅ 单进程 Streamlit App
- ✅ 一个真实数据流模块

---

# 二、系统架构图（极简 MVP）
```
┌──────────────────────────────┐
│            User              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        Streamlit App         │
│                              │
│  ┌────────────────────────┐  │
│  │ 1. 消息 (Mock)         │  │
│  │ 2. Skill实验室 (真实)  │  │
│  │ 3. 聊天 (Mock)         │  │
│  │ 4. 主页 (Mock)         │  │
│  └────────────────────────┘  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        skill_engine.py       │
│                              │
│  Akshare 获取数据            │
│  ↓                           │
│  传入 Kimi API               │
│  ↓                           │
│  返回结构化文本              │
│  ↓                           │
│  整理为 JSON                 │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    Skill Card UI Render      │
└──────────────────────────────┘
```

核心说明：

- Streamlit = UI + 控制层
- skill_engine = 唯一真实逻辑模块
- 不存在独立 API 层
- 不存在 Core 调度层
- 不存在 Registry
- 不存在 Protocol

---

# 三、边界图（Boundary Diagram）

```
              ┌────────────────────┐
              │      Streamlit     │
              │    UI + 控制层     │
              │                    │
              │ - 页面切换         │
              │ - 用户输入         │
              │ - 按钮触发         │
              │ - JSON展示         │
              └─────────┬──────────┘
                        │
                        │ 调用函数
                        ▼
              ┌────────────────────┐
              │    skill_engine    │
              │                    │
              │ - 调用 Akshare     │
              │ - 调用 Kimi API    │
              │ - 整理为 JSON      │
              └─────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │   External Services │
             │                     │
             │ - Akshare           │
             │ - Kimi API          │
             └─────────────────────┘
```

边界原则：

Streamlit 负责：
- 页面结构
- 卡片展示
- Loading 状态
- JSON 原文展示

skill_engine 负责：
- 数据抓取
- 模型调用
- JSON格式化

外部服务：
- 仅 Akshare
- 仅 Kimi API

---

# 四、数据流（单向极简）
```
用户输入股票代码  
↓  
点击生成按钮  
↓  
Streamlit 调用 skill_engine  
↓  
Akshare 抓取数据  
↓  
Kimi 生成结构化文本  
↓  
整理为 JSON  
↓  
返回 UI  
↓  
渲染 Skill 卡片
```

无缓存
无数据库
无状态管理
无多用户隔离
无持久层

---

# 五、页面结构（UI层）
```
Sidebar:  
- 消息  
- Skill实验室  
- 聊天  
- 主页

消息:  
- 展示 3~5 张 mock Skill 卡片

Skill实验室:  
- 股票代码输入框  
- 生成按钮  
- Loading 状态  
- Skill 卡片  
- JSON 展开区

聊天:  
- 模拟聊天内容  
- 折叠 Skill 卡片样式

主页:  
- 用户画像  
- 投资人格标签  
- 小组件式 Skill 卡片
```
 
---

# 六、部署结构（Streamlit Cloud）
```
GitHub Repo  
↓  
Streamlit Cloud  
↓  
自动安装 requirements.txt  
↓  
加载 secrets.toml  
↓  
启动 app.py
```

---

# 七、MVP 原则总结

v0.3.0 是：

- 极简
- 可运行
- 可演示
- 无复杂分层
- 无 Skill OS

它只是：

> 一个“结构表达 Demo”

不是：

- 完整系统
- 可扩展架构
- 多人平台

---

# 八、最终目标

用最少代码实现：

- 4 页面结构
- 1 个真实 Skill 数据流
- 结构化 JSON 输出
- 黑白灰卡片 UI
- 可公开访问链接

完成即可进入面试展示阶段。
