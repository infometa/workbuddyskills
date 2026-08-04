# 选品 / 市场调研 SOP

目标：从一个类目或关键词出发，产出一份可决策的选品候选清单。

## 流程

### 1. 明确前提（缺了就问用户）

- 目标市场（国家码，如 us / th / id）
- 类目或关键词（如"便携榨汁杯"、"skincare"）
- 可选：价格带、卖家类型偏好（跨境 / 本土 / 品牌）

### 2. 建候选池

用 search(entity=products) 初筛，用 offset 翻页把候选池凑够量。候选池要多大按任务需要定：用户说了规模按用户的来；没说就根据调研深度自己定并在产出里说明，别只拿第一页就下结论。

```
search(entity="products", country="us", keyword="portable blender",
       filters={"min_sold_7d": 100, "seller_type": 1})
```

常用 filters：min_price / max_price（锁价格带）、min_rating（质量底线，建议 ≥4.0）、min_sold_7d 或 min_sold_30d（动销底线）、seller_type（1=海外非品牌 2=本土 3=品牌 4=非品牌）、free_shipping。

初筛就把明显不合格的丢掉：评分 <4.0、近 7 天零动销、价格明显偏离用户预算。

### 3. 深挖头部候选（对前 5–8 个执行）

对每个候选商品做多维画像：

| 调用 | 看什么 |
|---|---|
| get_detail(products, id, country) | 销量趋势（上升期还是衰退期）、价格、SKU 结构、渠道占比 |
| get_related(products, id, "reviews", country) | 差评集中点（质量/物流/与描述不符），差评率是主要风险信号 |
| get_related(products, id, "creators", country) | 带货达人数量和结构：头部垄断（难切入）还是长尾分散（有机会） |
| get_related(products, id, "similar", country) | 竞品密度和价格分布，判断赛道拥挤程度 |

深度评论分析可以用 AI：`ai_generate(type="review_analysis", params={"product_id": id})` → check_task 轮询取报告。

### 4. Amazon 交叉验证（对首推 1–2 个候选做）

TikTok 销量反映内容流量的爆发力，Amazon 评论量和 BSR 反映长期真实需求。两边信号交叉后判读和动作完全不同：

```
amazon(action="search", keyword="<商品英文关键词>", marketplace="us")  # 同类的评论量级、评分水位、价格带
amazon(action="detail", asin="<头部同类的 asin>")                      # BSR、近一月购买量、星级分布、划线价
amazon(action="reviews", asin="...")                                   # 头部评论原声，挖痛点
```

| TikTok | Amazon | 判读 | 动作 |
|---|---|---|---|
| 爆 | 热（评论多/BSR 靠前） | 需求真实且长期，但 Amazon 侧竞争成熟 | 用差评找差异化切入点；Amazon 价格做定价锚——美区用户会比价，TK 定价明显高于 Amazon 会伤转化 |
| 爆 | 冷（搜索稀疏/评论少） | 信息差窗口或昙花一现，必须二次区分（见下） | 确认是真机会后优先级最高：抢先卡位，吃住「TK 看到 → Amazon 搜索」的流量外溢 |
| 冷 | 热 | 反向选品信号：长期需求还没被 TikTok 内容化 | 用 Amazon 评论挖卖点做内容切入，抢内容蓝海（入口见「注意」） |
| 冷 | 冷 | 无信号 | 放弃 |

**「TK 爆 + Amazon 冷」必须二次区分**，两种成因动作相反：

- **内容原生需求（真机会）**：强演示属性 / 冲动消费型产品，靠短视频激发购买，搜索场景天然滞后。佐证信号：TK 销量趋势持续走高（get_detail 趋势）、达人结构是长尾自发扩散（get_related creators 看头部集中度）
- **内容炒作（陷阱）**：单一头部达人带起来、趋势冲高回落（search 结果的 spike 为负）。铺货进去就是库存

限制与成本：

- marketplace 只有 us/uk/de/jp，且是 Amazon 站点码不是 country 码（英国是 uk 不是 gb，勿混用）。东南亚市场（th/id/vn 等）没有对应站点，跳过本环节
- amazon 每次调用计费，只对首推候选做，不要全候选池扫一遍

### 5. 产出

用表格输出候选清单，每行一个商品，列建议：

商品名 | 价格 | 近7天销量 | 30天GMV | 评分 | 带货达人数 | 趋势 | 主要风险

表格后面用几句话给出推荐结论：首推哪 1–2 个、为什么、主要风险是什么。做过 Amazon 验证的候选，把验证结论（落在四象限的哪一格、价格对比、差评痛点）写进推荐理由。数据要注明查询日期和市场。

首推的 1–2 个候选应继续做利润测算（读 profit-model.md）：卖得动 ≠ 赚钱，进货价、头程、佣金、退货算完才能下结论。

## 注意

- 判断"上升期"要看 get_detail 的趋势数据，不要只看 7 天销量绝对值
- 同一商品在不同国家表现差异大，用户要做多市场时对每个市场分别跑
- 先筛后挖：初筛阶段只用 search 返回的列表字段，不要对每个候选都 get_detail，候选池过大时先收窄再深挖，避免上下文爆炸
- 反向选品（从 Amazon 出发）：用户想找「Amazon 已验证但 TikTok 还没人做」的机会时，入口倒过来：amazon search 锁定高评论高评分商品 → reviews 挖卖点 → search(entity=videos/products) 反查 TikTok 侧竞争密度，密度低即内容蓝海；后续深挖仍走本 SOP 第 3 步
