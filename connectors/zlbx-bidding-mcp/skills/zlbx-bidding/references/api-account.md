# 账户查询类工具 API 详情

账户查询凭当前调用所用的 API Key 自动识别用户，只做鉴权，不限流、不计费、不扣除额度。不要向用户索要或输出 API Key；从环境变量 `ZLBX_API_KEY` 或 Agent 配置文件读取即可。

## 余额查询：get_account_balance

用于回答用户「当前余额」「剩余积分」「还能查多少次」「累计充值/消费」等账户状态问题。

### MCP 调用

优先复用 MCP 服务中已注册的账户工具：

```text
get_account_balance
```

无需传参，凭 MCP 调用上下文中的 API Key 自动识别当前账户。

### REST API 调用

```http
GET https://mcp-server.zhiliaobiaoxun.com/api_v2/account/balance
X-API-Key: $ZLBX_API_KEY
```

### CLI 调用

```bash
zlbx balance
```

### 返回字段

统一响应外层仍为 MCPResponse 结构，余额信息在 `data` 中：

| 字段 | 说明 |
|---|---|
| `balance` | 剩余可用积分/调用次数 |
| `total_charged` | 累计充值积分 |
| `total_consumed` | 累计消费积分 |

### 回答要求

- 余额查询本身免费、不扣额度，可以直接查询后回答。
- 只展示余额、累计充值、累计消费等账户状态；不要展示 API Key。
- 如果返回认证失败，提示用户检查 `ZLBX_API_KEY` 或 Agent 配置，不要让用户把密钥发到对话里。
- 如果用户询问充值入口，统一引导到 `https://ai.zhiliaobiaoxun.com/?ch=s01` 手机号登录后充值。

---

## 每日消耗查询：get_daily_consumption

用于回答「这几天用了多少」「哪天用得最多」「最近消耗趋势」等问题。

### MCP 调用

```
get_daily_consumption
```

### REST API 调用

```
GET https://mcp-server.zhiliaobiaoxun.com/api_v2/account/daily_consumption
```

### 参数

| 参数 | 说明 |
|---|---|
| `start_date` / `end_date` | 绝对日期 `YYYY-MM-DD`，**闭区间**；不传则按 `days` 取最近 N 天 |
| `days` | 不传区间时生效，默认 15（以今天为结束日往前推） |

### 返回字段

| 字段 | 说明 |
|---|---|
| `start_date` / `end_date` | 实际统计区间 |
| `total_consumed` | 区间总消耗积分 |
| `total_calls` | 区间总调用次数 |
| `daily` | 逐日列表 `{date, consumed, calls}`，**无消耗的日期补 0**，返回连续日序列 |

### 回答要求

- 本查询免费、不扣额度，可直接调用后回答。
- `daily` 已补零成连续日序列，画趋势或算日均可直接用，不要自己再补日期。
- 用户问「还能用多久」时，可用近 7 日均值配合 `get_account_balance` 的 `balance` 估算，
  并说明这是按近期速率的估算值。
