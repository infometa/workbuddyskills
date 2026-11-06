---
name: fenxiang-saving-assistant
display_name: 粉象网购省钱管家
display_name_en: Fenxiang Online Shopping Saving Assistant
description: 使用粉象 MCP 完成商品搜索、历史价、同款比价、省钱方案、购买建议和批量分析。当用户问某商品值不值得买、历史最低价、全网比价、哪个平台更便宜、怎么买更省，或要搜索淘宝/京东/唯品会商品时使用。
description_zh: 搜索淘宝、京东、唯品会商品，查询历史价格、全网比价，生成省钱方案和购买建议，支持批量分析。
description_en: Search Taobao, JD, and Vipshop products, check price history, compare prices, create saving plans and buying advice, with batch analysis.
examples_zh:
  - "搜索 iPhone 18，按价格从低到高排序"
  - "这个商品历史最低价是多少，现在值得买吗"
  - "帮我比较这几个商品，给出最省钱的购买方案"
examples_en:
  - "Search for iPhone 18 and sort by lowest price"
  - "What is the historical low price of this item, and is it worth buying now?"
  - "Compare these products and recommend the cheapest buying plan"
version: 1.0.0
author: "粉象生活"
---

# 粉象网购省钱管家

## 概述

通过粉象 MCP 的 6 个工具完成“搜商品 → 看价格 → 判断买不买 → 给省钱方案”的完整闭环。默认优先使用已配置的 MCP 工具；没有原生 MCP 连接时，用 `scripts/fenxiang_mcp.py` 直连 HTTP 端点。

## 鉴权模式

- 当前粉象 MCP 服务已关闭鉴权，不需要 Token。
- Skill 不内置 API Key，也不在对话或文件中保存 Key。
- 如果后续服务恢复鉴权，再通过连接器配置页或 `FENXIANG_MCP_API_KEY` 环境变量传入。
- 不要向用户展示 Key，不要把 Key 写入仓库或可分发文件。

## 工具选择

| 用户意图 | 优先工具 | 说明 |
|---|---|---|
| 按关键词搜商品 | `goods_search` | 支持淘宝/京东/唯品会/全平台；默认返回 10 条，最大 20 条 |
| 某个商品值不值得买 | `buy_advice` | **首选**；已包含历史价、同款渠道、省钱方案、评分和建议 |
| 某个商品怎么买最省 | `saving_plan` | 已包含历史价和比价，无需先调 `history_price`/`compare_price` |
| 只看历史价格曲线 | `history_price` | 原始历史价数据 |
| 只看同款全网报价 | `compare_price` | 原始比价数据 |
| 一次比较多个商品 | `batch_analyze` | 一次最多 5 个商品详情链接 |

**减少调用**：对单个商品做购买决策时，直接调 `buy_advice`，不要再串行调用 `history_price`、`compare_price`、`saving_plan`。只有用户明确要“原始历史价”或“原始比价表”时才用对应原始工具。

## 价格与展示规则

- 所有价格单位是**元**。
- `finalPrice` 是**到手价（券后价）**：券后价减去平台优惠，MCP 场景不返佣。
- 响应里不会返回 `commissionRebate`；不要向用户展示“佣金返现”“预估返现”。
- 有 `itemTitle`/`shopName`/`brand`/`spec`/`itemPicUrl` 时，回答里带上商品标题和店铺，避免用户再问“这是哪个店”。
- `priceType=no_rebate` 时统一表述为“到手价（券后价）”。
- 不编造价格；没有数据就明确说“暂无数据”，并给出下一步建议。

## 空结果与错误

- 空结果会带 `retryable=false` 和 `suggestedNextAction`；**不要对同一关键词/同一链接反复重试**，也不要只换 `responseFormat` 重试。
- `compare_price` 返回“商品暂无比价数据”时，直接转 `buy_advice` 或 `saving_plan`，不要继续换关键词搜同款。
- `goods_search` 空结果时，换更具体的品牌+型号关键词，或切换平台；不要重复同一请求。
- 当前服务已关闭鉴权；如果服务恢复鉴权后出现 HTTP `401`/`403`/`503`，如实告知用户，不要伪造结果。

## 标准工作流

### 1. 关键词找商品

1. 调 `goods_search`，参数：`keyword`，可选 `platform`（taobao/jd/vip/all）、`size`、`sortField`/`sort`、`minPrice`/`maxPrice`、`officialShop`、`responseFormat=json`。
2. 从 `goodsList` 里选 1–3 个最相关商品，记录 `itemTitle`、`goodsPrice`、`finalPrice`、`shopType`、`goodsUrl`、`itemId`。
3. 用户没指定平台时，优先 `platform=all`；手机型号搜索会过滤配件和无关商品。

**候选筛选：**

- 优先品牌/型号完整、旗舰店/自营、价格在合理区间的商品。
- 手机搜索忽略“游戏机/直播机/无卡槽/展示机/资源机”等非零售机；结果不理想时用 `officialShop=true` 或 `platform=jd` 再搜一次。
- 搜索结果价格与 `buy_advice.finalPrice` 差异过大时，用 `itemTitle`/`shopName` 核对是否同一商品；标题和店铺一致时以 `buy_advice.finalPrice` 为准，不输出搜索页的异常低价（可能是占位价/定金）。

### 2. 单个商品购买决策

1. 直接调 `buy_advice`，传商品详情链接，`responseFormat=json`。
2. 回答结构：
   - 商品：`itemTitle` / `shopName` / `brand` / `spec`
   - 结论：值得入手 / 建议观察 / 建议再等等（`recommendation`）
   - 到手价：`finalPrice`，价格口径：到手价（券后价）
   - 历史低点、近 30 天均价、历史分位
   - 同款渠道：`compareItems` 里的平台、店铺、到手价
   - 省钱方案：`savingPlan.bestPlatform`、`bestShop`、`estimatedSaving`、`steps`
   - 风险与下一步：`risks`、`nextAction`
3. 如果 `buy_advice` 返回空，按 `suggestedNextAction` 处理，不要自行编造。

### 3. 省钱方案

1. 调 `saving_plan`，传商品链接。
2. 输出最低渠道、到手价、预计节省、历史低点和执行步骤。
3. `saving_plan` 已经包含历史价和比价，**不要**先调 `history_price`/`compare_price`。

### 4. 批量比较

1. 调 `batch_analyze`，`goodsUrls` 用逗号或换行分隔，最多 5 个。
2. 对每个商品输出：标题、到手价、历史低点、最佳渠道、预计可省、建议。
3. 单个链接失败不影响其他链接；空项直接展示失败原因。

## 使用脚本（无原生 MCP 连接时）

```bash
# 当前服务已关闭鉴权，不需要 API Key
# 生产默认地址；测试环境用 --url 覆盖
python3 scripts/fenxiang_mcp.py goods_search '{"keyword":"iPhone 18","platform":"all","size":5,"responseFormat":"json"}'
python3 scripts/fenxiang_mcp.py buy_advice '{"goodsUrl":"https://s.click.taobao.com/OH0jVXi","responseFormat":"json"}'
python3 scripts/fenxiang_mcp.py batch_analyze '{"goodsUrls":"https://s.click.taobao.com/OH0jVXi,https://s.click.taobao.com/WR0whPi","responseFormat":"json"}'
```

- `FENXIANG_MCP_URL` 默认 `https://api.fenxianglife.com/njia/mcp`
- TLS 默认严格校验证书；只有内网自签名测试环境才显式加 `--insecure`，生产环境不要使用
- 如果后续服务恢复鉴权，再通过 `FENXIANG_MCP_API_KEY` 或 `--api-key-file` 传入；不要把 Key 写进 skill 或提交到仓库
- 脚本只输出 MCP 结果文本；加 `--pretty` 会尝试格式化 JSON

## 验证

```bash
python3 scripts/verify.py
```

验证内容：`tools/list` 6 个工具、搜索、历史价、比价、省钱方案、购买建议、批量分析，以及响应不含 `commissionRebate`。

## 资源

- `scripts/fenxiang_mcp.py`：MCP Streamable HTTP 客户端
- `scripts/verify.py`：全链路验证脚本
- `references/tools.md`：6 个工具的入参/出参与示例
