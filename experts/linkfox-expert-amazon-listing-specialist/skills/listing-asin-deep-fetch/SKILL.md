---
name: listing-asin-deep-fetch
description: 给定一个或一组 ASIN，并发拉取完整 listing 详情（标题、五点、A+、附图、价格、评分、变体）
  和销售历史，写入 ASINContext。编排 linkfox-amazon-product-detail 与 linkfox-keepa-product-request
  两个原子 Skill 的产出，做字段合并与去重。
  Use when pipeline enters L2 fetch phase. Internal Skill, typically called by playbook.
  NOT for keyword-based product search (use linkfox-amazon-search directly).
---

# Listing · ASIN Deep Fetch

## Claude Code 执行（强制）

每个 ASIN 只跑本专家 `skills/` 下随包提供的 `linkfox-amazon-product-detail` 脚本，禁止 curl / `/tmp`：

```bash
cd <本专家目录>/skills/linkfox-amazon-product-detail
python3 scripts/amazon_product_detail.py '{"asins": "B07JB964VX", "amazonDomain": "amazon.com"}'
```

大响应字段投影用同目录或 benchmark 的 `response_io.py read`，禁止 `python3 -c json.load`。

## Core Concepts

L2 内容拉取层的核心 Skill。Tier 1 已经提供两个数据源：Amazon 前端（实时、含五点/A+/附图）
和 Keepa（销售历史、BSR 趋势、价格曲线）。本 Skill 的职责是**并发调用两者**，把字段合并到
ASINContext 的 target_detail + target_keepa，处理缺失/超时降级，并做 24h 缓存。

## Invoke Schema

```yaml
inputs:
  - name: batch_id
    type: string
    required: true
  - name: row_indices
    type: array<int>
    required: false
    description: "省略则处理 batch 内所有 status='pending' 的行"
  - name: region
    type: string
    required: false
    default: amazon.com
    description: "亚马逊站点，从 rule.context.region 推导"
  - name: fetch_options
    type: object
    required: false
    properties:
      include_bought_together: boolean (default false)
      include_related_products: boolean (default false)
      include_keepa_history: boolean (default true)
      max_keepa_history_days: int (default 90)

outputs:
  - name: fetched_count
    type: int
  - name: failed_rows
    type: array<{row_index: int, asin: string, error: string}>
  - name: cache_hits
    type: int

events:
  - name: fetch_progress
    payload: { batch_id, processed: int, total: int, current_asin: string }
  - name: row_fetched
    payload: { batch_id, row_index, asin, has_detail: bool, has_keepa: bool }

side_effects:
  - write_target_detail_to_asin_context
  - write_target_keepa_to_asin_context
  - update_status_to_'analyzing'
```

## Dependencies

| 原子 Skill | 用途 | 失败影响 |
|---|---|---|
| `linkfox-amazon-product-detail` | 标题、五点、A+、附图、变体、评分 | 必需，失败则该行 fail |
| `linkfox-keepa-product-request` | 销售历史、BSR、价格曲线 | 可选，失败则该行 keepa=null 但继续 |

## Execution Playbook

```
1. 加载待处理行
   contexts = runtime.state_reader.load_batch(batch_id, row_indices)
   targets = [c for c in contexts if c.status == 'pending']
   if empty(targets): return {fetched_count: 0}

2. 按 region 分组（一次只处理同站点的 ASIN）
   regions = group_by(targets, lambda c: c.rule_snapshot.context.region)
   for region, group in regions:
       # 处理同 region 的 group

3. 命中缓存检查
   for ctx in group:
       cached_detail = runtime.cache.get(f"detail:{ctx.asin}:{region}:24h_bucket")
       cached_keepa = runtime.cache.get(f"keepa:{ctx.asin}:{region}:24h_bucket")
       if cached_detail and cached_keepa:
           ctx.target_detail = cached_detail
           ctx.target_keepa = cached_keepa
           cache_hits += 1
           emit row_fetched
       else:
           pending_for_fetch.append(ctx)

4. 拆批调 linkfox-amazon-product-detail
   # 该原子单次支持 40 ASIN，按 40 一批拆
   for chunk in chunks(pending_for_fetch, 40):
       asins = [c.asin for c in chunk]
       detail_result = call_atomic_skill(
           'linkfox-amazon-product-detail',
           {
               asins: ','.join(asins),
               amazonDomain: region,
               returnBoughtTogether: fetch_options.include_bought_together,
               returnRelatedProducts: fetch_options.include_related_products,
           }
       )
       # 把每个 ASIN 的 detail 写回对应 ctx
       for ctx in chunk:
           ctx.target_detail = detail_result.find(c.asin)
           runtime.cache.set(f"detail:{ctx.asin}:{region}:24h_bucket", ctx.target_detail, ttl=24h)

5. 并发调 linkfox-keepa-product-request
   if fetch_options.include_keepa_history:
       # linkfox-keepa-product-request 单次最多支持 5 个 ASIN
       for chunk in chunks(pending_for_fetch, 5):
           asins = [c.asin for c in chunk]
           keepa_result = call_atomic_skill(
               'linkfox-keepa-product-request',
               {
                   asin: ','.join(asins),
                   domain: REGION_TO_DOMAIN_ID[region],
                   stats: 1,    # 含历史数据
               }
           )
           for ctx in chunk:
               ctx.target_keepa = keepa_result.find(c.asin)
               runtime.cache.set(f"keepa:{ctx.asin}:{region}:24h_bucket", ctx.target_keepa, ttl=24h)

6. 字段合并与去重
   # detail 和 keepa 都有 title/price/rating，detail 优先（实时）
   # Keepa 提供 detail 没有的历史字段（90 天 BSR 曲线）
   # 不需要主动合并到单一字段，分别存即可，下游 writer 自己选

7. 状态推进
   for ctx in successful_fetched:
       ctx.status = 'analyzing'
       runtime.state_writer.save(ctx, emit_phase='fetch')

8. 失败处理
   for ctx in failed:
       if ctx.target_detail is None:
           failed_rows.append({
               row_index: ctx.row_index,
               asin: ctx.asin,
               error: 'detail_fetch_failed'
           })
           ctx.status = 'failed'
       elif ctx.target_keepa is None and fetch_options.include_keepa_history:
           # detail 拿到了但 keepa 失败，不算 fail，只 warn
           emit keepa_missing_warning
           ctx.status = 'analyzing'   # 继续推进

9. 返回 stats
```

## 并发与限流

- detail 与 keepa **并发跑**（同一批 ASIN 的 detail 和 keepa 同时发请求）
- 单批 40 个 ASIN（detail 上限）+ 100 个（keepa 上限）的请求按 runtime 全局并发池调度
- 受 Tier 1 rate-limit：默认并发 5，detect 429 后降到 1，60s 后恢复
- emit `rate_limit_throttled` 事件让 playbook 调整后续节奏

## Cache Strategy

```
key: detail:{asin}:{region}:{24h_bucket}
value: AmazonProductDetail 完整对象
ttl: 24 小时

key: keepa:{asin}:{region}:{24h_bucket}
value: KeepaProductDetail 完整对象
ttl: 24 小时
```

- 24h_bucket = floor(now() / 24h)，让同一天的多次调用命中同一缓存
- 用户手动触发"刷新此 ASIN"时跳过缓存
- ASIN 检测到下架（detail 返回 404 或 inventory_status='unavailable'）时清除缓存

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| detail_fetch_failed | 单 ASIN detail 返回空 | 该行 fail，继续其他行 |
| keepa_fetch_failed | 单 ASIN keepa 失败 | warn 但不阻塞，target_keepa=null |
| rate_limit_429 | 触发 Tier 1 限流 | 自动降并发 + 等待 60s 重试 |
| atomic_skill_timeout | 单次请求 > 30s | 重试 1 次，仍失败则该 chunk fail |
| batch_all_failed | 整批 detail 全失败 | emit batch_fetch_emergency，提示用户检查 region/ASIN 时效性 |
| asin_not_found | ASIN 在 detail 中返回不存在 | 标记 source.dead_asin=true，跳过 |
| variation_parent_asin | 父 ASIN（不能直接售卖） | 取第一个变体子 ASIN，emit variation_parent_substituted |

## Not Applicable

- 单 ASIN 实时刷新（直接调 `linkfox-amazon-product-detail`）
- 拉评论明细（用 `linkfox-amazon-reviews-list`，计费，先取得用户同意）
- 拉关键词布局（用 `listing-keyword-matrix-build`）
- 价格历史长期趋势（已在 keepa 中包含，但单独要求时也调 `linkfox-keepa-price-history`）

## 输出后下游消费

```
target_detail → 
  - listing-title-writer（参考结构）
  - listing-bullet-writer（参考五点）
  - listing-description-writer（参考长描述/A+）
  - listing-diff-meter（diff baseline）
  - listing-compliance-scan（图片 URL 做专利扫）

target_keepa →
  - listing-title-writer（销量上下文，影响关键词选择）
  - listing-bullet-writer（BSR 上下文影响卖点排序）
```

## 产物与落盘

本 skill **没有专用 save 脚本**。需要把结果留成产物时，统一用通用脚本落盘，
不要 `cat > /tmp/...`、不要用 Write/Edit 直接建 JSON、不要在聊天正文里贴全文：

```bash
echo '<payload JSON>' | node <agent-listing-result-html-skill>/scripts/save-json-artifact.mjs \
  --stdin \
  --slug=linkfox-listing-asin-deep-fetch
```

- 落点：会话目录 `linkfox/<日期>/<session>/reports/linkfox-listing-asin-deep-fetch-<ts>.json`，符合
  `linkfox-<slug>-<数字>.json` 命名规则。
- stdout 打印 `JSON artifact: <绝对路径>`——**不是** `Saved full response:`。
  一次 Bash 输出只允许一行 `Saved full response:`，本 skill 不占用它。
- 载荷形状见本文档上方的 schema 小节。前端没有为它做专用面板，产物按 JSON 文件展示。
- 传输层与命名的完整规则见 `listing-core/references/output-schema.md` §1。

同一 ASIN/站点/窗口只抓一次，下游读这里打印的绝对路径复用，不要为每个 writer 重抓一遍。
