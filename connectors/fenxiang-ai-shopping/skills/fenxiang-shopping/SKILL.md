---
name: fenxiang-shopping
description: 粉象省钱管家商品工具，用于搜索商品、查历史价、全网比价、生成省钱方案和购买建议。当用户询问商品价格、历史最低价、跨平台比价、是否值得买时使用。
---

# 粉象省钱管家

通过 MCP 工具查询淘宝、京东、唯品会、拼多多的商品价格与购买建议。拼多多关键词搜索暂不支持，但历史价和比价可用。

## 工具

### goods_search

按关键词搜索商品。

参数：
- `keyword`（必填）：搜索关键词。
- `platform`（可选）：`taobao`、`jd`、`vip`、`all`，默认 `taobao`；`pdd` 搜索暂不支持。
- `sortField`（可选）：`price` 或 `sales`。
- `sort`（可选）：`asc` 或 `desc`。
- `minPrice` / `maxPrice`（可选）：价格区间，单位元。
- `responseFormat`（可选）：`markdown`（默认）或 `json`。

返回商品名称、价格、平台、itemId 和购买链接。链接为转链后的联盟链接。

### history_price

根据商品链接查询历史价格。

参数：
- `goodsUrl`（必填）：淘宝/京东/拼多多/唯品会商品链接或淘口令。
- `responseFormat`（可选）：`markdown`（默认）或 `json`。

返回最近历史价格点，最多 100 个。可用于判断当前价格是否处于历史低位。

### compare_price

根据商品链接做全网比价。

参数：
- `goodsUrl`（必填）。
- `responseFormat`（可选）。

返回最多 4 个渠道的平台、店铺、价格和购买链接，按价格升序。

### saving_plan

生成省钱购买方案。

参数：
- `goodsUrl`（必填）。
- `responseFormat`（可选）。

返回最低价渠道、参考价、预计节省、历史低点和下单步骤。转链失败时链接回退为平台商品页。

### buy_advice

给出购买建议。

参数：
- `goodsUrl`（必填）。
- `responseFormat`（可选）。

返回：
- `recommendation`：`buy_now`（值得入手）、`watch`（建议观察）、`wait`（建议再等等）。
- `pricePosition`：`below_low`、`near_low`、`normal`、`high`、`unknown_history`。
- 理由、历史低点、30 天均价、最高价和最优渠道链接。

## 使用示例

- “搜一下 iPhone 16，按价格从低到高排序” → `goods_search(keyword="iPhone 16", sortField="price", sort="asc")`
- “这个淘宝商品历史最低价是多少” → `history_price(goodsUrl="...")`
- “帮我对比这个京东商品在全网的价格” → `compare_price(goodsUrl="...")`
- “生成这个商品的省钱购买方案” → `saving_plan(goodsUrl="...")`
- “现在这个价格值得买吗” → `buy_advice(goodsUrl="...")`

## 注意事项

- 工具结果默认 Markdown，需要程序化处理时传 `responseFormat=json`。
- 价格单位为元；历史价可能因商品较新而只有少量数据点。
- 比价数据可能为空，此时 `saving_plan` 和 `buy_advice` 会主要依据历史价判断。
- 链接为转链后的联盟购买链接；转链失败会回退为平台商品页。
- 商品链接需要是完整链接或可解析的淘口令；无法识别时返回“商品信息获取失败”。
- 不要编造价格、历史低点或购买建议，必须以工具返回结果为准。
