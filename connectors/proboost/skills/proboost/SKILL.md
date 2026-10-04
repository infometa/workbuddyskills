---
name: proboost
description: 跨境电商数据查询。用于 Amazon 选品/市场/关键词/竞品/ASIN 详情、TikTok 商品/达人/视频/店铺分析、全球专利检索。用户提到亚马逊、TikTok Shop、达人、选品、专利时使用。
version: 1.0.0
author: OpenBoost（小数汇智）
license: UNLICENSED
homepage: https://open.microdata-inc.com/
trigger:
  - "帮我做亚马逊选品分析"
  - "用 OpenBoost 查这个 ASIN"
  - "分析这个 TikTok 达人"
  - "用 OpenBoost 查专利侵权风险"
  - "分析这个亚马逊类目的市场"
  - "挖亚马逊关键词"
  - "找 TikTok Shop 爆款商品"
permission:
  - 网络访问
agent_created: true
category: research
tags:
  - Amazon
  - TikTok
  - 专利
  - 选品
  - MCP
---

# OpenBoost 跨境数据

通过已启用的 OpenBoost MCP 连接器查询 Amazon、TikTok Shop、全球专利数据。不要编造数据；所有数字、排名、销量、专利结果必须来自工具返回。

详细工具清单见 `references/tools.md`。Amazon 站点 ID 见 `references/sites.md`。

## 使用前

1. 确认 MCP 连接器 `proboost-tiktok-amazon-patent-mcp` 已连接（OAuth 授权成功，状态为绿色）。
2. 未授权时，引导用户完成 OpenBoost 登录授权；不要向用户索要或回显 secret-key。
3. 未订阅、套餐过期或额度用尽时，提示用户前往 https://open.microdata-inc.com/ 开通或续费。
4. 调用失败（401 / 业务码 -1）时，按顺序排查：未授权 → 套餐过期 → 额度用尽 → 参数错误。

## 能力边界

能做：

- Amazon：商品详情、类目、选品、选市场、关键词、ABA、流量词、竞品、评论、榜单、销量预估
- TikTok Shop：商品选品、达人、视频、店铺、品类大盘、口碑
- 专利：检索式/语义/图像检索、著录项目、法律状态、同族、全文与翻译

不能做：

- 代用户下单、改广告、改 Listing、登录第三方后台
- 在没有工具结果时编造销量、排名、专利结论
- 引导用户离开 WorkBuddy 去完成可在对话内完成的任务（OAuth / 开通套餐除外）

## 执行原则

1. 先判断任务属于 Amazon / TikTok / 专利哪一类，再选最少必要的工具。
2. Amazon 查询默认美国站（`webSiteId=1`），用户指定站点时再切换；站点 ID 查 `references/sites.md`。
3. 缺关键参数时先问：站点、类目、ASIN、国家/地区、时间范围、专利检索式。
4. 多步任务按流水线调用，每步用上一步结果，不要一次堆很多无关工具。
5. 结果用中文归纳：结论先行，再给关键数字、来源字段、下一步建议。
6. 列表类结果默认取 Top 10～20，并说明筛选条件。

## 典型工作流

### Amazon 选品 / 选市场

1. 用类目树确认类目 ID 或路径（`amz_category_query_v2` 或 `amz_hot_amz_hot_cat_tree`）。
2. 看市场容量与竞争（`amz_market_research` / `amz_market_statistics`）。
3. 看价格带、品牌、卖家结构（`amz_market_price` / `amz_market_brand` / `amz_market_seller`）。
4. 筛潜力款（`amz_product_selection` 或 `amz_market_goods` / `amz_hot_amz_hot_list_v2`）。
5. 对候选 ASIN 做详情与销量（`amz_sku_query` / `amz_sales_query`）。

### Amazon 关键词

1. 种子词挖掘：`amz_keyword_miner`
2. 选词与趋势：`amz_keyword_research` / `amz_research_monthly` / `amz_aba_research_trends`
3. 流量结构：`amz_traffic_keyword` / `amz_traffic_source`

### TikTok 找品 / 找达人

1. 类目：`tt_commodity_get_commodity_cat_tree`
2. 商品列表或详情：`tt_commodity_info_list` / `tt_commodity_detail` / `tt_commodity_sales_trend`
3. 达人：`tt_expert_info_list` / `tt_expert_detail` / `tt_expert_fans_portrait`
4. 视频脚本与口播：`tt_video_info_list` / `tt_video_detail` / `tt_video_content` / `tt_video_new_video_summary`
5. 大盘：`tt_commodity_statistics_get_total_statistics` / `tt_commodity_statistics_get_category_statistics`

### 专利预检

1. 先检索：文本用 `patent_query_search` 或 `patent_semantic_search`；外观用 `patent_image_search_single`
2. 看件数：`patent_query_count`
3. 对命中专利取著录/法律状态/同族：`patent_bibliography` / `patent_legal_status` / `patent_family`
4. 需要权利要求或说明书时再调全文/翻译工具
5. 结论必须区分「检索到相似专利」与「构成侵权」，后者需要专业律师判断，技能只做数据辅助。

## 输出格式

- 标题：一句话结论
- 关键数据：表格或要点（含站点、时间范围、类目）
- 依据：列出调用过的工具名
- 建议：下一步可继续查什么
- 风险：数据延迟、样本偏差、专利结论需人工复核

## 异常处理

- MCP 未连接 → 「请先在连接器中启用 OpenBoost，并完成 OAuth 授权。」
- 401 / 未授权 → 「当前授权无效或已过期，请重新授权；如未订阅请到 https://open.microdata-inc.com/ 开通。」
- 参数缺失 → 明确列出还缺哪些字段，不要空跑工具
- 无结果 → 说明筛选条件，建议放宽站点、类目或关键词后再查
- 工具超时 → 缩小时间范围或分页后再试

## 隐私说明

本技能通过远程 MCP 查询 OpenBoost（小数汇智）数据服务，请求会发送至中国大陆区域的 HTTPS 端点。不在本地保存用户密钥。隐私政策：https://www.microdata-inc.com/privacy
