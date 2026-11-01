---
name: yj-fin-comparable
description: 可比公司数据看板。输入一家公司，自动找同业可比公司，拉取估值与财务数据，输出单文件 HTML 报告（KPI 速览 + 汇总表 + 按语义分组的 3 类图表 + 文字分析 + 免责声明）。图表按语义分配：规模用横柱、估值用竖柱、质量用圆点、PE×增速双维度用气泡散点。触发词：数据对比、指标对比、同业数据、估值对比、财务数据对比、可比公司、横向对比、peer comparison。
version: 1.0.0
metadata:
  category: research
  domain: finance
  tools_prefix: 
---

# 可比公司分析

## 前置：连接与授权

本技能用到的全部工具都是受保护资源，**调用必须携带用户授权令牌**。用户首次使用时会被自动引导完成一次云极账号授权（登录 + 同意授权），此后令牌自动续期，不再打扰。

技能侧**不需要也绝不应该**要求用户提供 URL、API Key、Token 或环境变量——这些都是不存在的配置项，让用户去找会让对话卡死。

| 被拒情形 | 处置 |
|---|---|
| `UNAUTHORIZED` | 提示"需在连接器里重新完成云极账号授权"，**停止后续调用** |
| `SCOPE_MISSING` | 提示"请重新完成云极账号授权"，**停止后续调用** |
| `QUOTA_EXCEEDED` | **立刻停止全部调用**，用已取到的数据出部分结果并写明缺口 |
| `UPSTREAM_UNAVAILABLE` / `UPSTREAM_TIMEOUT` | 工具返回**错误**（`ok=false`，不返回降级数据）；退避重试一次，仍失败则该项视为缺失、在报告注明缺口；AI 生成类**不得重发**（不可重放，会重复计费） |

配额按**云极账号**累计且跨会话有效，不要建议用户"换个会话再试"。完整说明见技能包 README 第 3 节。

---

## 概览

输入一家公司 → 输出**一个 HTML 文件**：汇总表 + 分组图表 + 分析文字 + 免责声明。

全部数据经自有 MCP 工具取得，**分析文字中不出现任何工具名、接口名、取数过程**。

---

## 工作流

### 第一步：解析目标公司

```
securities_search({ "keyword": "<公司名称>", "top": 5 })
```

取 `security_code` 与 `security_name`。**一次任务只解析一次**，后续全部复用这个 code。

### 第二步：拿可比公司名单

```
sector_search({ "keyword": "<行业关键词>" })            # 拿 sector_id
sector_constituents({ "sector_id": "<板块ID>" })        # 板块成分股名单
# 或按题材：concept_search({ "keyword": "<题材>" }) → concept_securities({ "concept_id": "<ID>" })
# 或按名称：securities_search({ "keyword": "<行业关键词>", "category": "index", "top": 10 })
```

从返回的名单里挑可比公司（**优先取 A 股 3–5 家**，按市值/业务相关性筛选）。`agent_peer_comparison` 在本环境未暴露，**不可调用**；每家可比公司的基本面（营收/净利/ROE/增速/PE/PB/PS/市值）一律按后续步骤自行拉取计算，不要依赖任何预打包结论工具。

**更名/退市兜底**：若 `securities_search` 仅返回一家或空，用 `sector_constituents` 补候选。

### 第三步：补毛利率与净利率（必须）

即使同业对比已给数据，**仍需拉利润表**算毛利率/净利率的绝对值：

```
financial_income({
  "security_code": "<code>", "market": "a",
  "period_type": "accumulated", "period": ["latest"],
  "report_type": ["consolidated"],
  "field_list": ["total_op_rev","total_op_cost","net_profit"]
})
```

对目标公司与每家可比公司各调一次（并发扇出 5）。

- 营业收入 = `total_op_rev`
- 毛利率 = `(total_op_rev - total_op_cost) / total_op_rev × 100`
- 净利率 = `net_profit / total_op_rev × 100`

需要同比增速时，追加拉取**去年同期**报表：`{ "fiscal_year": ["<去年>"], "period": ["<同期枚举，如 q3>"] }`。
报告期枚举是 `q1` / `interim` / `q3` / `annual` / `latest`，**不要写 `2025Q3`**。

### 第四步：组装 `data.json`

```json
{
  "target": "源杰科技",
  "asOf": "2026-09-22",
  "companies": [
    {
      "name": "源杰科技",
      "code": "688498.SH",
      "revenue": 3.55,
      "revenue_growth": 138.5,
      "net_profit": 1.79,
      "net_profit_growth": 3212.6,
      "gross_margin": 77.8,
      "net_margin": 50.5,
      "roe": 8.2,
      "pe": 399.4,
      "market_cap": 142.2
    }
  ],
  "analysis": "## 核心判断\n...\n\n## 估值对比\n...\n\n..."
}
```

| 字段 | 单位 | 取数路径 |
|---|---|---|
| `revenue` | 亿元 | `financial_income` · `total_op_rev` |
| `revenue_growth` | % | 自行计算：拉本期与去年同期 `total_op_rev`，增速 = (本期−去年同期)/去年同期×100。**港股不可得时写 `—`** |
| `net_profit` | 亿元 | `financial_income` · `net_profit`（归母口径） |
| `net_profit_growth` | % | 同上。**港股不可得时写 `—`** |
| `gross_margin` | % | 计算：(收入 − 成本) / 收入 × 100 |
| `net_margin` | % | 计算：净利润 / 收入 × 100 |
| `roe` | % | `financial_balance` 取归属母公司所有者权益合计，配合 `financial_income` 净利润年化计算：ROE = 净利润 / 归母所有者权益 × 100 |
| `pe` | 倍 | `valuation_analysis`(pe_ttm) 或 `earnings_consensus`（仅 A 股，pe 字段），否则 `—` |
| `market_cap` | 亿元 | A 股：`quote_daily` 最新收盘价 × 总股本（来自 `financial_balance`/`financial_income` 股本字段）/ 1e8；港股：`quote_daily_hk` 最新收盘价 × 总股本 / 1e8，**注意币种换算（利润表 CNY、股价 HKD）** |

**缺失数据一律写 `—`**，不要补 0、不要估算后不标注。缺哪个指标就跳过对应图表。

### 第五步：生成 HTML

```
python3 scripts/report_html.py --data <data.json> --title <标题> --out <输出路径.html>
```

---

## `analysis` 字段怎么写

目标：**读者读完后能清晰转述一个核心判断**。五段递进：

1. **核心判断**（1 句定性：估值定位"高/低/合理" + 盈利能力特征 + 竞争位势）
2. **估值定位**（2–3 句：PE 横向对比 + 是否被低基数扭曲 + 预期 PE 收敛路径）
3. **盈利能力**（2–3 句：毛利率/净利率/ROE 横向对比，**用具体数字**）
4. **竞争格局**（2–3 句：时间窗口 + 先发优势 + 潜在供给冲击）
5. **风险提示**（1–2 句：估值消化 + 规模验证）

### 文字禁止事项

- ❌ 任何工具名 / 接口名（"同业分析指出""数据源显示""从某某返回"）
- ❌ 引用取数过程
- ❌ 缩写指标名（营收 → 营业收入，净利 → 净利润）
- ✅ 直接陈述事实，用数据说话

---

## 图表类型分配

按**指标语义**自动选图，不按个人喜好。

| 指标 | 语义类别 | 图表 | 理由 |
|---|---|---|---|
| 营业收入、净利润 | 规模 | 横向柱状图 `hbar` | 绝对值差异大，横柱最直观 |
| 毛利率、净利率、ROE | 质量 | 圆点对比图 `dot` | 线性刻度 + 均值虚线，突显离散度与排名 |
| 总市值、PE(TTM) | 估值 | 垂直柱状图 `vbar` | 跨公司对比，目标公司高亮 |
| PE(TTM) × 营业收入增速 | 综合 | 气泡散点图 `scatter` | X=PE / Y=增速 / 气泡=市值，一图看增长定价匹配度 |

**增速类不单独成图**（跨公司连线无序列关系、缺乏语义依据），只在散点图 X/Y 轴使用。
全部**内嵌 SVG，零外部依赖**。按三组语义分组展示（规模对比 / 盈利质量 / 估值对比），每组带标签。

> 图表选择决策框架见 `references/chart-selection-principles.md`。

---

## 配色与布局

| 角色 | 颜色 |
|---|---|
| 目标公司 | `#c53030`（朱红） |
| 可比公司 | `#4a6996`（钢蓝） |
| 页面底色 | `#fafbfc` |
| 卡片底色 | `#ffffff` |
| 页面顶部 | `#f7f8fa → #eef1f5 → #e8ecf1` 三层渐变 |
| 目标行底色 | `#fff5f5` |
| 分隔线 | `#e8ecf0` |
| 正文 / 次要文字 | `#1a202c` / `#718096` |
| 强调数字 | `#c53030` |

| 项目 | 规范 |
|---|---|
| 输出 | 单个 HTML 文件，内嵌 CSS + SVG |
| KPI 卡片 | 6 张水平排列，首张左边框朱红高亮；hover 上浮 3px；圆角 12px |
| 汇总表 | 10 列全称标题；目标行朱红底+粗体；末尾可比均值行灰底斜体 |
| 图表卡片 | 白色圆角，padding 18px 22px；散点图跨全行；CSS Grid 对齐 |
| 数值精度 | 保留 1 位小数（PE 保留整数） |
| 缺失数据 | `—` |
| 可比公司数量 | 3–5 家 |
| 响应式 | `@media(max-width:768px)` 适配移动端 |
| SVG id | 必须加类型前缀避免跨图冲突：`hbar_{i}` / `vbar_{i}` |

**同比箭头红涨绿跌**（中国市场惯例）。

---

## 免责声明（强制）

每个报告末尾必须包含，`.footer` 容器，上方细线分隔：

```
以上信息由AI生成，投资有风险，入市需谨慎。数据来源为云极数据服务，仅供参考。
```

第一行 `font-size: 11px`，第二行 `font-size: 10px` + `color: #a0aec0`。

> **来源统一署名「云极数据服务」**：契约 C1 要求对外口径统一，报告里的数据来源一律写这个字面值，不要用占位符、不要写成别家品牌。

---

## 错误处理

| 情形 | 处理 |
|---|---|
| 公司名解析不到 | 提示用户提供完整证券代码 |
| 同业对比失败 | 降级走行业/板块检索挑可比公司，并在报告里注明可比口径 |
| 某指标缺失 | 写 `—`，跳过对应图表 |
| 工具返回 `degraded=true` | 报告里写明缺什么、为什么 |
| `UNAUTHORIZED` / `SCOPE_MISSING` | 提示用户重新完成云极账号授权，**停止调用** |
| `QUOTA_EXCEEDED` | **立刻停止全部调用**，用已取到的数据出部分看板并在免责区上方写明缺口 |

🔴 **可比公司最容易触碰的合规红线（契约 C7）**：因为是横向对比，"哪家便宜/哪家贵"的诱惑很强。只能写**倍数与分位的事实对比**（"PS 最低的是 XXX，2.1×，同业中位 4.3×"），不得写买入/卖出、目标价、仓位建议，也不得把"估值最低"表述成值得投资。

---

## 依赖

- MCP 工具：`securities_search`、`sector_search`/`sector_constituents`（或 `concept_search`/`concept_securities`）取可比名单、`financial_income`、`financial_balance`（ROE 兜底）、`quote_daily`/`quote_daily_hk`（市值兜底）、`valuation_analysis`/`earnings_consensus`（PE/PB/PS 兜底）；**`agent_peer_comparison` 未暴露，不调用**

> **取数铁律**：所有取数一律经 `yj-fin-data` 统一 MCP；可比公司与各项乘数由 `securities_search`+`sector_constituents`/`concept_securities` 取名单、`financial_*`/`quote_*`/`valuation_analysis`/`earnings_consensus` 自行计算，不得凭记忆填空、不得调用未暴露的 `agent_peer_comparison`；遇 `UNAUTHORIZED` 即停并引导用户授权。
- 脚本：`scripts/report_html.py`（仅渲染，不取数）
