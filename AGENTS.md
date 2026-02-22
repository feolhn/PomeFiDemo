# PomeFi AI 理财 App - Agent Guide

> 本文件面向 AI 编程助手，用于快速理解项目结构、技术栈和开发规范。

---

## 项目概述

**PomeFi** 是一款面向个人投资者的 AI 驱动理财分析应用，定位为"金融表达的高级视觉载体"。

- **当前版本**: v0.3.0 (Streamlit Demo 版)
- **核心定位**: 面试展示用的前端展示型 MVP
- **技术形态**: Streamlit 单页应用，部署于 Streamlit Cloud
- **目标用户**: 个人投资者，具备特定投资人格标签

### 版本说明

本版本为**展示型 MVP**，核心目标是证明 "Skill 卡片可以成为金融表达的高级视觉载体"。

**已实现**:
- ✅ Skill 卡片预览功能完整闭环
- ✅ 图表效果达到展示级质量
- ✅ 可部署至 Streamlit Cloud

**未实现**（本版本范围外）:
- ❌ 完整 Skill OS 架构
- ❌ Core 调度层 / Registry / Schema 校验
- ❌ 用户系统 / 社区互动系统
- ❌ 数据库与缓存层

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端框架 | [Streamlit](https://streamlit.io/) | Python 声明式 UI 渲染 |
| 数据源 | [Akshare](https://www.akshare.xyz/) | 中国金融数据抓取 |
| AI 模型 | Kimi API (Moonshot AI) | 结构化分析与文本生成 |
| 可视化 | Plotly / Matplotlib | 交互式图表渲染 |
| 部署平台 | Streamlit Cloud | 免费托管与分享 |

---

## 项目结构

```
PomeFiDemo/
├── docs/                          # 产品文档与设计稿
│   ├── prd_v0.3.0.md              # 产品需求文档 (核心参考)
│   ├── flow_v0.3.0.md             # 架构与数据流说明
│   ├── input_mock.md              # 测试输入数据规范
│   ├── output_mock.md             # 输出内容结构规范
│   └── ui_*.jpg                   # UI 设计稿截图
│
├── app.py                         # 主入口：四栏页面 + Skill 预览
├── skill_engine.py                # 核心模块：数据抓取 + 大模型处理
├── mock_data.py                   # Mock 数据：非核心页面使用
├── utils.py                       # 工具函数：JSON 整理 & 文本处理
├── requirements.txt               # Python 依赖
├── .streamlit/
│   └── secrets.toml               # API Key 配置 (本地/云端)
├── README.md                      # 部署说明
└── AGENTS.md                      # 本文件
```

### 文件职责说明

| 文件 | 职责 | 数据类型 |
|------|------|----------|
| `app.py` | 页面路由、UI 布局、用户交互 | Mock / Real |
| `skill_engine.py` | 唯一真实数据模块：调用 Akshare + Kimi API | Real |
| `mock_data.py` | 其他三页面的静态展示数据 | Mock only |
| `utils.py` | JSON 格式化、文本清洗、辅助函数 | - |

---

## 页面架构

共 **4 个一级页面**，其中仅 Skill Lab 页面有真实逻辑，其余为纯 UI 展示：

```
┌─────────────────────────────────────────────────────────────┐
│  Navigation Bar                                             │
├──────────┬──────────┬──────────┬────────────────────────────┤
│ Message  │ Skill Lab│ Chat     │ Profile                    │
│ (消息流)  │ (实验室) │ (聊天)   │ (个人主页)                  │
├──────────┴──────────┴──────────┴────────────────────────────┤
│                                                             │
│  Message: Mock 数据展示消息流                                │
│  Skill Lab: 真实数据流 + 三种 Skill 卡片                     │
│  Chat: Mock 数据展示聊天界面                                 │
│  Profile: Mock 数据展示个人主页                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Skill 模块详解（核心功能）

Skill 是本应用的核心分析单元，每个 Skill 是一个独立的金融分析场景。

### 当前支持的三种 Skill

| Skill ID | 中文名称 | 测试输入 | 输出图表类型 |
|----------|----------|----------|--------------|
| `trend_follower` | 趋势跟踪 | 股票 300750 (宁德时代) | PE 百分位曲线、价格趋势折线图 |
| `fund_diagnostic` | 基金诊断 | 基金 001410 (嘉实新机遇混合A) | 行业占比饼图、市值风格分布条形图 |
| `stock_diagnostic` | 个股诊断 | 股票列表 (5只) | 行业集中度环形图、市值风格雷达图 |

### 数据流流程

```
用户点击生成按钮
        ↓
app.py 调用 skill_engine.generate_skill_card(skill_type, input_param)
        ↓
Akshare 拉取指定标的数据
        ↓
数据清洗与格式化
        ↓
传入 Kimi API 生成结构化分析
        ↓
接收 JSON 格式响应
        ↓
转化为卡片渲染结构
        ↓
Streamlit 渲染卡片 + Plotly 交互图表
```

### Skill 卡片输出字段规范

每张 Skill 卡片必须包含以下模块（具体字段因 Skill 类型而异）：

1. **基本信息**: Skill ID、分类、创建者
2. **属性标签**: 投资人格标签、MBTI 标签
3. **核心分析**: 因 Skill 类型而异（如上涨原因、行业分布、估值等）
4. **结构风险**: 风险点识别与解读
5. **用户画像匹配度**: 与用户投资风格的匹配分析
6. **元数据**: 数据来源、生成时间、质量状态、免责声明

---

## 视觉设计规范

### 风格关键词

> 冷静、理性、极简、结构化

### 设计原则

- **主色调**: 黑 / 白 / 灰
- **布局**: 大量留白，强层级排版
- **组件**: 圆角卡片，弱边框
- **标签**: 低饱和度配色
- **字体**: 清晰易读，层次分明

### 图表要求

图表是核心视觉锚点，必须达到"出彩"效果：

- ✅ 支持悬停显示明细数据
- ✅ 黑白灰风格适配
- ✅ 字体与图例优化
- ✅ 自适应布局
- ✅ 卡片内视觉居中
- ✅ 响应式设计

---

## 文案风格规范

Skill 卡片内所有分析性文字必须遵循统一的"华尔街分析师"风格。

### 语气基调

- 冷静、克制、理性
- 不煽情、不口号化、不鸡汤化
- 类似投行研究报告的判断口吻
- 允许轻微毒舌或黑色幽默

### 语言风格

- 使用短句增强节奏感
- 避免网络用语
- 先给事实，再给判断
- 先给结构，再给风险

### 禁用表达

- ❌ "强烈推荐"、"必涨" 等绝对化表述
- ❌ 情绪化夸张表达
- ❌ 明显营销语言
- ❌ 投资建议语气（如"建议买入"）

### 风格示例

| ❌ 错误风格 | ✅ 正确风格 |
|-------------|-------------|
| "这只基金超级稳健，强烈推荐！" | "纯正大盘价值，波动率低于市场均值。" |
| "必涨！赶紧上车！" | "估值处于历史中偏高区间。" |
| "太厉害了，收益爆表！" | "你看上去买了一箩筐基金，其实都一样。" |

---

## 开发命令

### 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
echo 'MOONSHOT_API_KEY = "your-api-key-here"' > .streamlit/secrets.toml

# 启动开发服务器
streamlit run app.py
```

### 部署

```bash
# 推送到 GitHub 后，在 Streamlit Cloud 连接仓库即可自动部署
# 需在 Streamlit Cloud 设置中配置 Secrets: MOONSHOT_API_KEY
```

---

## 依赖清单

```
streamlit>=1.28.0
plotly>=5.18.0
akshare>=1.11.0
openai>=1.0.0  # 用于调用 Kimi API
pandas>=2.0.0
numpy>=1.24.0
```

---

## 配置说明

### secrets.toml 格式

```toml
MOONSHOT_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 注意事项

- `secrets.toml` 已添加到 `.gitignore`，切勿提交到版本控制
- Streamlit Cloud 部署时需在 Dashboard 中手动设置 Secrets
- 本地开发时文件位于 `.streamlit/secrets.toml`

---

## 测试规范

### Skill 模块测试输入（固定）

| Skill | 输入参数 | 说明 |
|-------|----------|------|
| trend_follower | `300750` | 宁德时代 |
| fund_diagnostic | `001410` | 嘉实新机遇混合A |
| stock_diagnostic | `[600519, 002594, 600036, 601012, 601318]` | 茅台、比亚迪、招行、隆基、平安 |

### 测试检查清单

- [ ] 三个 Skill 均能正常生成卡片
- [ ] 图表无加载异常，支持悬停交互
- [ ] 输出字段与 `output_mock.md` 一致
- [ ] 文案风格符合规范（冷静、克制、理性）
- [ ] 移动端布局正常
- [ ] 无控制台报错

---

## 目录约定

- 所有代码文件使用 **英文命名**
- 所有文档位于 `docs/` 目录
- 所有 UI 截图以 `ui_` 前缀命名
- 版本号格式：`v0.3.0`（主版本.次版本.修订号）

---

## 参考文档

| 文档 | 用途 |
|------|------|
| `docs/prd_v0.3.0.md` | 产品需求文档，功能定义 |
| `docs/flow_v0.3.0.md` | 架构图与数据流说明 |
| `docs/input_mock.md` | 测试输入数据规范 |
| `docs/output_mock.md` | 输出 JSON 结构规范与文案示例 |

---

## 免责声明

所有 Skill 卡片必须包含以下免责声明：

> 仅为历史数据与公开信息结构展示，不构成投资建议。

---

## 联系与贡献

本项目为个人面试展示作品，暂不开放外部贡献。

---

*最后更新: 2026-02-22*
