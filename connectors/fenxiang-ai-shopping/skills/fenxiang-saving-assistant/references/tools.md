# 粉象 MCP 工具参考

## 连接

- 生产：`https://api.fenxianglife.com/njia/mcp`
- 测试环境：`https://k8s-api-test.fenxianglife.com/test2/njia/mcp`（按需替换）
- 协议：MCP Streamable HTTP，JSON-RPC 2.0
- 鉴权：当前服务已关闭 MCP 鉴权，无需 API Key；如后续恢复，支持 `Authorization: Bearer <API Key>` 或 `X-Api-Key: <API Key>`
- 内容类型：`Content-Type: application/json`，`Accept: application/json, text/event-stream`

如果 Qoder 已配置粉象 MCP 连接器，直接调用连接器暴露的工具；工具名可能带前缀，例如 `mcp__fenxiang-compare__goods_search`。没有连接器时用 `scripts/fenxiang_mcp.py`。

## 工具一览

### goods_search

按关键词搜索商品。

```json
{
  "keyword": "iPhone 18",
  "platform": "all",
  "size": 10,
  "sortField": "price",
  "sort": "asc",
  "minPrice": 100,
  "maxPrice": 10000,
  "officialShop": false,
  "withCoupon": true,
  "responseFormat": "json"
}
```

- `platform`：`taobao` / `jd` / `vip` / `all`，默认 `taobao`；拼多多搜索暂不支持。
- `size`：默认 10，最大 20。
- 返回：`goodsList`，每项含 `goodsName`、`goodsPrice`、`couponPrice`、`finalPrice`、`savingAmount`、`priceType`、`shopType`、`itemId`、`goodsUrl`。
- 手机型号搜索会过滤配件和无关品类。

### history_price

查询单个商品历史价格。

```json
{
  "goodsUrl": "https://s.click.taobao.com/OH0jVXi",
  "responseFormat": "json"
}
```

返回：

```json
{
  "points": [{"time": "2026-10-23 12:00:00", "price": 314.0}],
  "couponPrice": 314.0,
  "finalPrice": 310.72,
  "priceType": "no_rebate",
  "itemTitle": "商品标题",
  "shopName": "店铺名",
  "brand": "品牌",
  "spec": "规格",
  "itemPicUrl": "https://..."
}
```

### compare_price

查询同款全网比价。

```json
{
  "goodsUrl": "https://s.click.taobao.com/OH0jVXi",
  "responseFormat": "json"
}
```

返回对象：

```json
{
  "items": [
    {
      "shopType": "淘宝",
      "shopName": "店铺名",
      "couponPrice": 300.0,
      "finalPrice": 297.84,
      "savingAmount": 7.21,
      "priceType": "no_rebate",
      "sameItem": true,
      "itemId": "...",
      "goodsUrl": "https://..."
    }
  ],
  "itemTitle": "商品标题",
  "shopName": "当前商品店铺",
  "brand": "品牌",
  "spec": "规格",
  "itemPicUrl": "https://..."
}
```

无同款数据时返回文本“商品暂无比价数据”，不要换格式重试。

### saving_plan

生成省钱方案，已包含历史价和比价。

```json
{
  "goodsUrl": "https://s.click.taobao.com/OH0jVXi",
  "responseFormat": "json"
}
```

关键字段：`bestPrice`、`bestPlatform`、`bestShop`、`bestGoodsUrl`、`finalPrice`、`estimatedSaving`、`historicalLow`、`steps`、`priceType`。

### buy_advice

完整购买决策，已包含历史价、同款渠道和省钱方案。

```json
{
  "goodsUrl": "https://s.click.taobao.com/OH0jVXi",
  "responseFormat": "json"
}
```

关键字段：

- `recommendation`：`buy_now` / `watch` / `wait`
- `score`、`confidence`、`reasons`、`risks`、`nextAction`
- `finalPrice`、`priceType`、`latestPrice`、`historicalLow`、`average30`
- `compareItems`：同款渠道
- `savingPlan`：省钱方案对象
- 商品摘要：`itemTitle`、`shopName`、`brand`、`spec`、`itemPicUrl`

**单个商品做购买决策时优先调用本工具，不要先调 `history_price`/`compare_price`/`saving_plan`。**

### batch_analyze

一次分析多个商品详情链接，最多 5 个。

```json
{
  "goodsUrls": "https://s.click.taobao.com/OH0jVXi,https://s.click.taobao.com/WR0whPi",
  "responseFormat": "json"
}
```

返回 `items` 数组，每项是 `buy_advice` 结构；单个链接失败不影响其他链接。

## 价格口径

- 单位：元。
- `finalPrice`：到手价（券后价）= 券后价 − 平台优惠；MCP 场景佣金为 0。
- `priceType`：
  - `no_rebate`：不返佣到手价
  - `reference`：参考价
  - `coupon_only`：仅券后价
  - `exact`：精确到手价
- 不返回 `commissionRebate`；不要展示佣金/返现。

## 空结果与错误

- 空结果带 `retryable=false` 和 `suggestedNextAction`。
- 不要对同一关键词/同一链接反复重试，也不要只改 `responseFormat` 重试。
- 当前服务已关闭鉴权；如果服务恢复鉴权后出现 HTTP `401`/`403`/`503`，按鉴权错误处理。
- 超时：降低 `size`、换平台，或稍后重试；不要并发轰炸。

## 示例工作流

1. `goods_search` 找候选商品。
2. 选 1–3 个最相关商品。
3. 对每个商品调 `buy_advice`。
4. 汇总商品、到手价、历史低点、最佳渠道、建议。

多商品比较：

1. 收集最多 5 个商品详情链接。
2. 调 `batch_analyze`。
3. 输出每个商品的结论、到手价、最佳渠道、预计可省。
