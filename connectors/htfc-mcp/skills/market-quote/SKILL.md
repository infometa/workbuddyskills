---
name: market-quote
description: 查询期货结构化行情数据。当用户询问某品种或合约的实时价格、最新价、分时、K 线、历史日线行情，或需要比较多个合约行情时使用。
---

# 行情查询（market-quote）

## 用途

查询期货实时、分时、K 线、逐笔与历史日线等结构化行情数据，支持一次查询多个合约。

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `params` | 是 | 查询条件对象，见下表 |
| `action` | 否 | `query`（默认）查实时/分时/K 线/逐笔；`historical` 查历史日线 |

`action` 合法值只有 `query` 和 `historical`，其它值会返回 `invalid_market_action`。

### action=query 时的 params

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `dataset` | 是 | `quote` 实时快照；`kline` K 线；`trend` 分时；`tick` 逐笔 |
| `symbols` | 是 | 合约代码数组，形如 `["AU.SHF"]`；`kline`/`trend`/`tick` 只能传 1 个 |
| `period` | `kline` 必填 | K 线周期，见下方枚举 |
| `market` | 否 | `cn_futures` 期货；`cn_stock` 股票；`index` 指数；`lme` 外盘 |
| `range` | `kline` 建议必填 | 时间范围 `{"from": "...", "to": "..."}`，开区间。不传时 K 线基本只返回当天，要历史区间必须显式传入 |
| `fields` | 否 | 需要返回的字段列表 |
| `limit` / `offset` | 否 | 分页，`limit` 为返回条数 |
| `filters` / `order` | 否 | 过滤条件、排序 |
| `name_like` | 否 | 按品种名模糊匹配 |

### action=historical 时的 params

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `dataset` | 是 | `futday` 期货日线；`futoptday` 期权日线 |
| `symbols` | 是 | 合约代码数组 |

### dataset 合法值总表

| 场景 | 合法值 |
| --- | --- |
| `action=query` | `quote`、`kline`、`trend`、`tick` |
| `action=historical` | `futday`、`futoptday` |

不要使用中文值（如 `实时`、`分时`、`K线`）或 `realtime`、`history` 等别名，都会返回 `invalid_market_dataset`。

### K 线周期（`period`）合法值

`minute`、`minute5`、`minute10`、`minute15`、`minute30`、`minute60`、`minute120`、`day`

不要使用 `1d`、`D`、`daily`、`1m`、`5m`，都会返回 `invalid_market_period`。

## 返回

`content[0].text` 是 JSON 字符串，直接用 `json.loads` 解析。

```json
{"success": true, "requestId": "...", "data": {"table": {"info": {"rank": "row", "rows": 2, "totalRows": 2}, "field": ["Code", "Name"], "data": [["AU.SHF", "沪金主连"]]}}}
```

**关键：`info.rank` 决定 `data` 的布局，不同 dataset 不一样**

| `rank` | 出现在 | `data` 每个元素的含义 |
| --- | --- | --- |
| `row` | `quote` | 一条记录，`data` 长度 = 记录数 |
| `col` | `kline`、`trend`、`tick` | **一个字段的整列**，`data` 长度 = 字段数 |

`col` 布局下绝不能按行解析：`data[0]` 是日期整列、`data[1]` 是开盘价整列……记录数要取 `info.rows`。转成行：

```python
table = result["data"]["table"]
fields, cols, rows = table["field"], table["data"], table["info"]["rows"]
names = [f[0] if isinstance(f, (list, tuple)) else f for f in fields]
records = [dict(zip(names, [col[i] for col in cols])) for i in range(rows)]
```

## 调用示例

实时快照：

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"market_quote","arguments":{"action":"query","params":{"dataset":"quote","market":"cn_futures","symbols":["AU.SHF","RB.SHF"],"limit":10}}}}
```

日 K 线（注意带 `range`）：

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"market_quote","arguments":{"action":"query","params":{"dataset":"kline","symbols":["AU.SHF"],"period":"day","range":{"from":"2026-10-01","to":"2026-11-03"},"limit":20}}}}
```

历史日线：

```json
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"market_quote","arguments":{"action":"historical","params":{"dataset":"futday","symbols":["AU.SHF"],"limit":20}}}}
```

## 注意事项

- `symbols` 必填：漏传或传空数组会被服务端直接拒绝，返回 `isError=true`、`code=missing_symbols`，不会落到"查全市场"。需要按名称查询时改用 `name_like` 或 `filters`。
- `kline`/`trend`/`tick` 一次只能查 1 个合约。
- 合约代码不存在时返回一行除代码外全为 `null` 的记录且不报错，解析时应判定为无效合约，不要当成行情展示。
- `quote` 的 `PercentChange` 以**昨结算价**为基准，不是紧挨着的 `PreClose`（前收价）。两者可能差 0.5 个百分点以上，不要互相验算；行情表不返回昨结算价字段。

## Key 说明

用户在连接器配置里填写一次期赢通 API Key，客户端以 `X-API-KEY` 请求头发送，工具入参中不需要再携带 Key，也不要让用户在对话中提供 Key。

Key 相关错误：`missing_api_key`、`invalid_qiyingtong_api_key`、`qiyingtong_api_key_invalid`，处理方式同连接器配置检查。
