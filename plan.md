# PomeFi v0.3.0 修订版任务方案（按评审意见收敛）

## Summary
本版已按 `plan_review_comments.md` 收敛为“最小可实现 MVP”路线：  
- 删除治理型/过度工程化内容  
- 保留最小接口冻结、最小降级机制、可验证 DoD  
- 目标周期：2-5 天完成可展示、可部署、可扩展的单体 Streamlit Demo

## 修订后的目标与边界

### Objective
交付一个单体应用：`Streamlit UI + 3个Skill + Akshare + Kimi + Plotly 图表 + Cloud 部署`，证明 Skill 卡片展示闭环。

### Out of Scope
- 不做 Skill OS / registry
- 不做数据库、用户系统、社区逻辑
- 不做独立 schema 文件体系
- 不做缓存、熔断、性能 SLA
- 不做治理型 Annotation 机制（仅保留轻量评审）

## Definition of Done（必须全部满足）
1. 本地 `streamlit run app.py` 0 error  
2. Streamlit Cloud 可访问  
3. 三个 skill 主路径全部成功  
4. 卡片字段完整可渲染  
5. 图表 hover 正常  
6. 异常情况下页面不崩溃（有降级）

## Public APIs / Interfaces / Types（最小冻结）

### 核心函数
```python
# /Users/hujiawei/Documents/PomeFiDemo/skill_engine.py
def generate_skill_card(skill_type: str, input_param) -> dict
```

### 返回结构（统一）
```python
{
  "data": {...},
  "metadata": {
    "generated_at": "ISO8601 string",
    "data_source": "string"
  },
  "quality_status": "valid" | "degraded" | "error"
}
```

### Normalize 规则（强制）
1. LLM 非法 JSON -> `quality_status="degraded"`  
2. 缺失字段 -> 自动填 `"N/A"`  
3. API 失败 -> 返回“可渲染最小结构”  
4. UI 层只消费 normalize 后结果，不接触原始 LLM 输出

## 执行阶段（5阶段）

### 阶段1：搭骨架
- 创建 `app.py` / `skill_engine.py` / `mock_data.py` / `utils.py` / `requirements.txt` / `.streamlit/secrets.toml.example` / `README.md`
- 四页导航可启动
- Message/Chat/Profile 用 mock 渲染  
完成标准：`app.py` 可运行

### 阶段2：锁接口
- 实现 `generate_skill_card`
- 返回最小统一结构（先用假数据）
- UI 先按固定 JSON 渲染  
完成标准：Skill Lab 能稳定渲染假数据卡片

### 阶段3：接入真实数据
- 接入 Akshare（3 skill 最小所需数据）
- 接入 Kimi（结构化文本）
- 加 normalize + 降级  
完成标准：3 skill 主路径可跑通

### 阶段4：图表完善
- `trend_follower`: 2条 trace（价格+估值相关），hover 正常，黑白灰配色（禁默认蓝）
- `fund_diagnostic`: 饼图+条形图，图例与 hover 正常
- `stock_diagnostic`: 环图或雷达图，展示稳定  
完成标准：图表满足展示要求

### 阶段5：部署
- 完整依赖与 secrets 示例
- Streamlit Cloud 配置并上线  
完成标准：外网可访问并演示三条主路径

## Checklist（提交级别，15-60分钟/项）

### P0（必须）
1. 项目骨架文件创建完成  
2. 四页导航启动成功  
3. `generate_skill_card` 路由完成  
4. normalize 降级机制完成  
5. 三个 skill 主路径成功  
6. 三类图表均可正常展示  
7. Cloud 成功部署可访问

### P1（重要）
1. UI 黑白灰风格统一  
2. 免责声明自动注入  
3. 异常提示可读且不打断流程

### P2（优化）
1. 视觉微调（间距/字体/层次）  
2. 加载态优化  
3. 图表交互细节优化（tooltip 文案、legend 排序）

## 测试场景与验收
1. 固定输入回归：`300750`、`001410`、`[600519,002594,600036,601012,601318]`
2. 字段完整性：每个 skill 输出字段与 `docs/output_mock.md` 对齐（缺失补 N/A）
3. 异常场景：
- Akshare 失败 -> degraded + 可渲染
- Kimi 失败/格式异常 -> degraded + 可渲染
4. 文案规则：无“强烈推荐/必涨”等禁用表达
5. 每张卡片存在免责声明

## 轻量评审循环（替代治理式 Annotation）
- 保留 1-2 轮人工批注即可，不作为流程门禁  
- 每轮只允许改三类内容：假设纠偏、范围变更、验收条款修订  
- 不再采用 1-6 轮强制循环

## Assumptions & Defaults
1. 当前代码从零搭建（仓库现状以文档为主）  
2. 技术栈固定 Streamlit + Akshare + Kimi + Plotly  
3. 优先稳定闭环，不引入额外抽象层  
4. 扩展能力通过“统一返回结构+解耦边界”保留，不提前实现复杂架构

## 解耦原则

当前结构：

`app.py` → 仅负责 UI  
`skill_engine.py` → 唯一真实逻辑  
`mock_data.py` → 非核心页面  
`utils.py` → 文本处理  

UI 不调用外部 API。

已具备未来扩展能力：

可新增第 4 个 skill  
可替换 Kimi  
可替换 Akshare  
可单独重构 UI  

当前解耦程度：适合 MVP。
