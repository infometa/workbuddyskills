# 共享证据缓存协议

计费检索（Product Detail、SIF/关键词矩阵、评论明细）的结果**跨会话、跨场景**复用：同一个 ASIN 先跑合规检测、再跑 Alexa 体检、再跑重写，Product Detail 只应真实调用一次。本协议是 CLAUDE.md 规则 9（付费检索预算）的执行细则，不放松它的任何限制。

## 缓存位置与持久性

- 缓存根：`writable_root()/linkfox/.cache/evidence/`（`writable_root` 见 `scripts/linkfox_paths.py`：`$LINKFOX_WORKSPACE` → cwd → tmp）。
- **跨会话持久的前提是 `LINKFOX_WORKSPACE` 指向持久卷**。指向会话级临时目录时，缓存自动退化为会话内复用——行为不变，只是命中率低；不要因此绕过本协议。
- 缓存条目只是索引（key → 落盘响应绝对路径 + 时间戳 + 状态），不复制大响应本体。

## 何时查、何时存

任何计费检索**调用前先 lookup，调用后必 store**（含失败/空结果）：

```bash
# 调用前
python3 skills/listing-core/scripts/evidence_cache.py lookup \
  --type product-detail --key-asin B0XXXXXXX --key-site US --key returnAuthorsReviews=true

# 未命中 → 真实调用 → 用 stdout 的 Saved full response 路径登记
python3 skills/listing-core/scripts/evidence_cache.py store \
  --type product-detail --key-asin B0XXXXXXX --key-site US --key returnAuthorsReviews=true \
  --path /abs/.../saved-response.json --status ok
```

- `lookup` 输出单行 JSON（`hit/path/age_hours/status`）；命中即用 `response_io.py read --fields` 按最小投影读取 `path`，不重新调用。
- 批量 Product Detail 请求按**单 ASIN 粒度**逐个 lookup/store：部分命中时只对未命中的 ASIN 发起批量请求。
- key 必须含齐区分计费参数的维度：ASIN、站点，以及影响响应内容的参数（如 `returnAuthorsReviews`、评论明细的星级/页数、矩阵的窗口）。拿不准就多加 key——宁可少命中，不可错命中。

## TTL

| 类型 | TTL | 理由 |
|---|---|---|
| `product-detail` | 24h | 页面事实/价格/评论摘要日级变化 |
| `keyword-matrix` | 7 天 | SIF 数据本身是 30 天窗口，周级才有意义变化；`build_keyword_matrix.py` 另有自身 24h 缓存，两层各自生效 |
| `reviews-list` | 7 天 | 计费高、变化慢 |
| 负结果（`empty`/`error`） | 统一 24h | 与「失败/空结果也视为已消耗」一致：TTL 内不得静默重试同参检索，继续检索先 AskUserQuestion |

## 诚实约束（不可省略）

- 命中缓存时，产物的 `data_confidence` 必须标注数据时点（如「关键词数据取自 18 小时前的缓存」），交付摘要同步说明；不得把缓存数据表述为本次实时拉取。
- 用户明确要求刷新数据时跳过 lookup 直接调用（正常计费），调用后 store 覆盖旧条目。
- 缓存的 `path` 失效（文件被清理）按未命中处理，不得凭索引编造数据。
