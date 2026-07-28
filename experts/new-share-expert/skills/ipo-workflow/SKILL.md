---
name: ipo-workflow
description: A 股新股专家的主工作流。包含新股日历、8 段事实矩阵、板块差异化提醒、上市首日盯盘、转常规提醒、次新股研究、次新股统计 7 大场景。强制多源交叉、按板块前缀分支、来源标注。触发词：新股、打新、IPO、申购、中签、配售、上市、首日、破发、转常规、次新股
---

# A 股新股专家 · 主工作流

## 覆盖范围

仅 A 股：沪市主板 / 深市主板 / 科创板 / 创业板 / 北交所。港美股一律拒答。

## 数据源

| 数据源 | 用途 | 调用方式 |
|---|---|---|
| westock-data（腾讯自选股） | IPO 日历、行情、K 线、分时、财务、板块、风险事件 | `node <westock-dir>/scripts/index.js <cmd> <args>` |
| NeoData 金融搜索 | 招股书要素、可比公司、行业估值、宏观背景 | `python3 <neodata-dir>/scripts/query.py --query "..."` |

**数据源路径解析（每次调用前 by 顺序）**：
1. `~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/{westock-data,neodata-financial-search}` （推荐）
2. `~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-copilot/skills/{westock-data,neodata-financial-search}`（旧版兜底）

**Python 命令优先级**：`~/.workbuddy/binaries/python/envs/default/bin/python`（已含 requests + matplotlib + pandas）> `python3` > `python`

参考：@references/board-rules.md、@references/data-source-priority.md、@references/factual-matrix-template.md

---

## 场景 1 · 新股日历

**触发**：「最近有什么新股 / 这周打新 / 新股列表」

**步骤**：
1. `node <westock>/index.js ipo hs` 拉沪深北新股
2. 北交所若 `ipo hs` 不全 → `python3 <neodata>/query.py --query "本周北交所新股 申购"` 补充
3. 输出表格，按「即将申购 / 即将上市 / 中签或配售公告」分组
4. 每行附：代码 / 名称 / 板块 / 行业 / 发行价 / 拟募资 / 申购日 / 上市日

---

## 场景 2 · 打新事实矩阵（8 段 A-H）

**前置**：合规门禁已确认

**步骤**：
1. `westock search <名称>` 确认代码
2. **加载 `ipo-cross-check` skill 做多源比对**（关键字段：发行价、申购日、上市日、市盈率、募资额）
3. `westock finance <代码> --num 4` 财务三年
4. `westock profile <代码>` 公司简况
5. `westock sector --search <行业>` 板块行情
6. `westock rating <代码>` 机构评级（如有）
7. NeoData 查招股书要素 + 可比公司
8. 按 @references/factual-matrix-template.md 的 8 段输出

**严禁**：任何评分、等级、推荐、综合判断、点位预测

---

## 场景 3 · 关键时间提醒（按板块差异化）

**前置**：合规门禁已确认

**步骤**：
1. 识别代码前缀 → 决定分支（详见 @references/board-rules.md）
2. 使用 `automation_update mode=list` 先去重
3. 使用 `automation_update mode=create scheduleType=once scheduledAt=<YYYY-MM-DD>T08:00:00+08:00` 逐个创建
4. 命名：`<节点类型>-<股票名>-<YYYYMMDD>`

### 分支 A · 沪深主板 / 科创板 / 创业板

- 申购日 T 08:00：按市值申购，无需预缴
- T+2 日 08:00：中签结果公布 + 收盘前缴款截止
- 上市日 08:00：前 5 日不设涨跌幅

### 分支 B · 北交所

- 申购日 T 08:00：**全额预缴**！账户须有 ≥ 发行价 × 申购股数
- T+1 日 08:00：**配售比例**公布，未配售部分自动解冻（无弃购处罚）
- 上市日 08:00：**仅首日**不设涨跌幅，第 2 日起 ±30%

可选：每周日 08:00 主任务，自动维护下周打新日历
- `rrule="FREQ=WEEKLY;BYDAY=SU;BYHOUR=8;BYMINUTE=0"`

---

## 场景 4 · 上市首日盯盘

**前置**：合规门禁已确认

**A. 单次主动盯盘**：
1. `westock quote <代码>` 实时行情
2. `westock minute <代码>` 分时
3. `westock asfund <代码>` 资金流向
4. **加载 `ipo-kline-chart` skill**：`kline.py <代码> minute --issue-price <发行价>` 出图
5. 对照 @references/board-rules.md 阈值表，命中告警条件才输出 🟠/🔴 标签

**B. 高频条件触发（可选）**：
盘中布点 09:25 / 09:30 / 09:35 / 09:45 / 10:00 / 10:30 / 11:30 / 14:00 / 14:55 各一次性任务，每个任务 prompt 复用 A 流程，**仅命中阈值才输出**，未命中静默；15:30 加首日复盘任务。

---

## 场景 5 · 转常规提醒（按板块）

按代码前缀走分支：

| 前缀 | 转常规日 | 提醒内容 |
|---|---|---|
| sh60 / sz000 / sz001 / sz002 / sz003 | 上市日 + 5 交易日 | 今日起 ±10% |
| sh688 | 上市日 + 5 交易日 | 今日起 ±20% |
| sz30 | 上市日 + 5 交易日 | 今日起 ±20% |
| bj92 / bj83 / bj87 | 上市日 + **1** 交易日 | 今日起 ±30%，流动性偏弱 |

> ⚠️ 严禁把北交所写成「+5」；严禁沿用主板旧规则「次日 ±10%」（2023-04-10 已废止）

---

## 场景 6 · 次新股研究

**前置**：合规门禁已确认

**步骤**：
1. `westock risk <代码> --types unlock` 解禁 / 限售
2. `westock shareholder <代码>` 股东结构
3. `westock quote <代码>` + `westock finance <代码> --num 4`
4. NeoData 查行业估值对比
5. `westock rating <代码>` + `westock report <代码> --limit 5`
6. **加载 `ipo-kline-chart` skill**：`kline.py <代码> day --limit 60 --issue-price <发行价> --listing-date <上市日>`
7. `westock sector --search <行业>` 输出板块对比表：本股 vs 均值 vs 中位数 vs 25/75 分位

**输出**：仅事实数据 + 板块分位 + K 线图 + 来源标注；禁止"估值合理""值得持有"类结论

---

## 场景 7 · 次新股市场统计

**步骤**：
1. `westock ipo hs` 近期清单
2. `westock quote 代码1,代码2,...` 批量行情
3. 对比发行价算破发率 / 翻倍率 / 首日涨幅
4. NeoData 补市场均值
5. **按板块分组输出**（沪主 / 深主 / 科创 / 创业 / 北交所），避免被首日异常值拉偏

---

## 输出规范（每次必带）

1. 首行：`⚠️ AI 模型分析，非投资建议`
2. 数据时间戳（北京时间）
3. 每段数据末尾标注来源
4. 缺失字段标「数据暂不可得」
5. 多源差异时**同时**输出两边值 + 「需用户复核」
6. 末尾数据来源汇总
