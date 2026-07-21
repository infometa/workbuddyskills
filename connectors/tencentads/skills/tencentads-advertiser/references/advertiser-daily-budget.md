# 账户日预算查询与修改

## 脚本：get-daily-budget.mjs

查询指定广告主账户的当前日预算及今日可设置的最低日预算。

### 调用方式

```bash
node scripts/get-daily-budget.mjs '{"account_id":"<ACCOUNT_ID>"}'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 广告主账户 ID |

### 返回格式

```json
{
  "account_id": 123456789,
  "daily_budget": 100000,
  "min_daily_budget": 50000
}
```

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账户 ID |
| `daily_budget` | integer | 当前日预算，单位：**分**。0 表示不限预算 |
| `min_daily_budget` | integer | 当前可设置的最低日预算，单位：**分**。基于今日消耗和延迟扣款估算，仅供参考，不保证修改一定成功 |

---

## 脚本：update-daily-budget.mjs

修改指定广告主账户的日预算。

### 调用方式

```bash
node scripts/update-daily-budget.mjs '{"account_id":"<ACCOUNT_ID>","daily_budget":<分>}'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 广告主账户 ID |
| `daily_budget` | integer | **是** | 目标日预算，单位：**分**。传 `0` 表示不限预算 |
| `use_min_daily_budget` | boolean | 否 | 降预算兜底开关，默认 `false`，见下方说明 |

**`daily_budget` 约束**（脚本内部已做前置校验）：

- 非零时范围：`5000` ~ `4000000000`（分），即 50元 ~ 4000万元
- 每次调整幅度至少 5000 分（50元）；微信公众号/小程序账户每次最少提升 50000 分（500元）
- 不得低于今日消耗 × 1.2 + 冻结金额；不得低于今日消耗 + 5000 分

**`use_min_daily_budget` 说明**：

| 值 | 行为 |
|----|------|
| `false`（默认） | 严格执行目标预算，若因今日消耗限制无法降到目标值则报错返回 |
| `true` | 若降预算失败，自动降至系统允许的最低值（可能高于目标值，即"想降反而升"） |

> **Agent 决策规则**：用户明确说"降到尽可能低"、"降到系统允许的最低值"、"用最低值兜底"时传 `true`；用户指定了明确的目标金额时传 `false`（或不传）。

### 返回格式

```json
{
  "success": true,
  "account_id": 123456789,
  "daily_budget": 100000,
  "use_min_daily_budget": false
}
```

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `account_id` | integer | 广告主账户 ID |
| `daily_budget` | integer | 实际设置后的日预算，单位：**分** |
| `use_min_daily_budget` | boolean | 是否触发了最低值兜底。若为 `true` 说明实际设置值高于用户目标值，需告知用户 |

---

## Agent 使用流程

### 场景 A：查询日预算

1. 确认 `account_id`（如未提供，先用 `get-account-list.mjs` 让用户选择）
2. 调用 `get-daily-budget.mjs`
3. 将结果换算为元展示给用户：`daily_budget / 100` 元；0 显示为"不限预算"

### 场景 B：修改日预算

1. 确认 `account_id` 和目标预算金额
2. 将用户表达的元换算为分（如"500元" → `50000`）
3. 根据用户意图决定 `use_min_daily_budget`：
   - 用户说明确金额 → 不传（默认 `false`）
   - 用户说"降到最低"/"尽量低"/"兜底" → 传 `true`
4. 调用 `update-daily-budget.mjs`
5. 若返回 `use_min_daily_budget=true`，说明实际生效值与目标值不同，需告知用户实际生效的预算金额

### 场景 C：先查后改

用户说"把日预算降低一半"等相对表达时：

1. 先调 `get-daily-budget.mjs` 获取当前值
2. 计算目标值（当前值 / 2，取整为分），校验与当前值的差值是否 ≥ 5000 分（50元）；若差值不足则告知用户调整幅度不够，需重新确认目标值
3. 向用户确认目标金额后再调 `update-daily-budget.mjs`
