# 业务上下文

## 核心概念澄清

### 三个金额指标的区别

> 在回答用户问题或构造 SQL 时，必须明确以下概念的含义和使用场景。

| 指标 | 字段名 | 含义 | 实际数据关系 | 使用场景 |
|------|--------|------|------------|---------|
| **营业应收** | `recv_money` | 账单原价总额（最大，未减优惠） | recv_money ≥ busi_income ≥ real_income | 用于反映业务规模上限 |
| **实收金额** | `busi_income` | 扣除优惠后的实付金额（次高） | busi_income ≥ real_income | 用于核心营收分析 |
| **纯收金额** | `real_income` | 实收金额再减去服务费等杂项（最小） | real_income ≤ busi_income | 用于计算净利润 |

**三字段关系验证**：
```
recv_money - busi_income = disc_money_total（优惠总金额）
busi_income - real_income ≈ service_free + low_consume + asitem_fix + item_wipe（杂项费用合计）
recv_money - real_income = 优惠合计 + 杂费合计
```

---

### 翻台率的正确理解

> ⚠️ **业界对翻台率定义存在歧义，本 Skill 统一如下**：

| 指标 | 计算公式 | 说明 |
|------|---------|------|
| **开台率** | 总开台数 ÷ Σ(每天的 门店桌数 × 当天市别数) × 100% | 座位被使用的频率 |
| **翻台率** | 开台率 - 1（若结果 < 0 则显示 0） | 相比"一桌换一轮"的超出部分，反映座位复用程度 |

**示例**：
- 周一 50 桌开 2 市别 = 100 桌次
- 周二 50 桌开 3 市别 = 150 桌次
- 总可开台 = 250 桌次
- 若总开台 300，则开台率 = 300÷250×100% = 120%，翻台率 = 20%

**说明**：市别数按「门店×日期」分别统计，每天可能不同（如周一开午市+晚市，周五加开宵夜）

---

### 时间字段说明

| 字段 | 含义 | 备注 |
|------|------|------|
| `settle_biz_date` | 营业日期（北京时间） | 查询时以该字段过滤，非系统时间 |
| 所有时间范围 | 均为闭区间 `>= start AND < end` | 不要用 BETWEEN |

---

### 权限范围说明

用户权限由 OpenClaw 机器人配置层预设（group_code / store_code），查询结果仅返回用户权限范围内的数据。

**但需验证配置的合法性**：

| 配置项 | 验证规则 | 异常处理 |
|--------|---------|---------|
| `group_code` | 必须唯一（或取第一个） | 多集团时默认取第一个，记录警告 |
| `store_code` | 必须属于对应 group_code | 过滤数据库中不存在的门店编码 |

**合法性检查时机**：会话初始化时执行，详见 [rules/security-rules.md](../rules/security-rules.md#检查-1group_code-配置合法性c0-01)。

**禁止事项**：
- ❌ 禁止跨集团查询
- ❌ 禁止查询配置外的数据
- ❌ 禁止绕过权限过滤条件
- ❌ **禁止暴露其他集团的任何信息**（包括 group_code、group_name）
  - 不能说"当前默认集团是 XXX"
  - 不能说"我看到有很多集团"
  - 不能用 group_name 搜索其他集团

---

## Intent 与业务概念对照

| 用户问题 | 对应 Intent | 关键区分 |
|---------|-----------|---------|
| "点外卖" | Intent 8 | sale_type = 外卖 |
| "美团外卖" | Intent 10 | order_source = 美团外卖 |
| "扫码点餐" | Intent 10 | 微信来源 |
| "客单价多少" | Intent 11 | 明确问指标 |
| "最近生意怎么样" | Intent 24 | 看整体经营 |
| "翻台率最高" | Intent 11 | 明确问指标 |
| "看看经营" | Intent 24 | 无限定词 |

---

## 执行入口说明

### read_query
- action: read_query
- 描述: Execute a SELECT query or commands that return a ResultSet. db session already in default db `dm`
- 参数: query:string(必填)，db:unknown
- 必填: query
- 示例命令:
  - `sl starrocks read-query --query 'SELECT 1'`
- 执行前请先结合当前业务场景补全参数，不要直接使用空字符串、0 或 false 作为最终值。

当前 CLI 仅支持 `read-query --query`。多步骤分析需逐条执行 `sl starrocks read-query --query ...`，并遵守单轮最多 10 次查询上限。
