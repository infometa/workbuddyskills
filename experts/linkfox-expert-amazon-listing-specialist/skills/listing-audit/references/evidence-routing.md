# Audit evidence routing

## Core run

输入包含 `run-manifest.json` 时，先解析 artifacts：

- facts：product-facts、Product Detail；
- insight：buyer questions、keywords、评论证据；
- write：listing-final、check-report、ai-readiness；
- 已有 scorer/audit 产物。

同 ASIN、站点且数据仍在 24 小时复用窗口时，不重新调用 Product Detail、SIF 或 Reviews List。缺某一证据只补该证据，不重跑完整 Core。

## Live ASIN

1. Product Detail 获取现状、评论摘要、图片/A+、变体和可见属性。
2. 只有需要评价搜索匹配且无有效 keyword matrix 时才调用 SIF matrix。
3. 评论摘要正常时不拉明细；按 Core 的 review-depth-policy 判断升级。
4. 合规和 AI readiness 优先复用已有结果；standard 才补一次对应内检。

## Provided text

直接标准化 Listing 字段。没有商品事实时，事实可信度 N/A；没有关键词矩阵时，语义可发现性 N/A；没有图片时，视觉诊断 N/A，不因缺图扣文案分。

## Confidence

每条 finding 记录 `source_path|source_tool`、ASIN/字段、采集时间和 `verified|partial|unavailable`。外部数值必须能回到真实产物；推导结论不得伪装为平台数据。

## Incremental supplement

用户后续提供评论、后台属性或卖家报表时，只重算受影响视角和 `auditHandoff`。Canonical score 只有评分证据发生变化时才重新运行。
