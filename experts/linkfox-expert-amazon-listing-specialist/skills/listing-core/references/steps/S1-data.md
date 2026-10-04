# S1–S2 证据采集

## 输入

- `mode`、`profile`、站点、语言、本品事实、现有 Listing（如有）、主参考 ASIN（如有）。

## 操作

1. rewrite 带 `listingAuditHandoff`：先校验目标 ASIN/站点和 evidence paths。24 小时窗口内的同参 Product Detail、SIF、Reviews List、合规和报表投影直接复用；只补缺失或过期证据。handoff 不匹配时停止复用并按普通 rewrite 取数。
2. create 没有 ASIN：图片下载/上传只是共同前置；图片一旦可访问，必须在**同一条 assistant 消息中同时发出**视觉事实提取与一次 `linkfox-amazon-search-by-image` 两个工具调用，再一起等待结果。不得先等视觉描述完成再发图搜。无图时调用一次 `linkfox-amazon-search`。选择最相关且商品形态一致的成熟 ASIN。找不到时停止并说明无法满足 SIF 底线，不静默走 category seed。下载远程图片使用 Python/现有上传工具，不先尝试运行时未保证安装的 `curl`。
3. rewrite 没有 ASIN（用户只给品牌 + 现有文案）：**禁止用品牌名搜索定位本品**。新品牌、演示品牌和小众品牌大概率未被索引，品牌名搜索属于可预期的无效计费检索，命中失败也不得换词或翻页重试。正确路径：
   - 本品事实直接取自用户提供的现有 Listing 与已确认商品事实，不依赖本品 ASIN；
   - 调用**一次** `linkfox-amazon-search`，关键词用**去品牌化的品类核心词**（现有标题剔除品牌名后的核心短语，如 `whiskey stones gift set 9 pack soapstone`），选 1 个商品形态一致的成熟 ASIN 作参考 ASIN；
   - 用该参考 ASIN 走第 4 条的 Product Detail + SIF 并发；产出中把评论与关键词数据来源明确标注为参考竞品，置 `data_confidence.own_asin_data=unavailable`；
   - 找不到形态一致的参考 ASIN 时停止并说明无法满足 SIF 底线，不静默走 category seed。
   用户提供了本品 ASIN 时不走本分支，直接进第 4 条。
4. 已知主 ASIN 后运行 `run_pipeline.py plan`，由脚本一次查完共享证据缓存并输出 `fetch-plan.json`；仅对 plan 中未命中的请求同轮并发：
   - Product Detail：`returnAuthorsReviews=true`。按用户提供的参考 ASIN 数拉取，与本品合并为一次批量请求（上限 5 个，超出取用户列出的前 5 个并说明取舍）；只有主 ASIN 时拉 1 个。
   - `listing-keyword-matrix-build`：主 ASIN，`top_n=50`，默认 30 天窗口；内部先 SIF，失败才 SellerSprite backup（脚本自带缓存，空结果/失败同样计入缓存）。
5. API 结果落盘后只运行一次 `run_pipeline.py ingest --product-detail <path> --keyword-matrix <path>`。它批量完成字段映射、竞品隔离、最小投影、缓存登记、Top 50 投影和 manifest 推进，输出 `insight-input.json`；禁止再单独跑 project/peek/cache/save/manifest 脚本。SIF 与同次 SellerSprite backup 都失败时，不传空 matrix，改传 `--keyword-unavailable '<真实原因>'`，由脚本标记 `facts_only`。create 的本品事实路径在 plan 阶段通过 `--own-facts` 传入。只校验当前目标事实；竞品字段缺失只标证据弱，不触发第二轮取数。
6. 默认到此为止，不自动拉评论原文。用户主动要求评论明细，或摘要证据弱/任务以评论为核心时，读取 `../review-depth-policy.md` 决定是否提示及调用 `linkfox-amazon-reviews-list`。
7. 只保存原始响应路径与紧凑事实包；竞品字段和本品事实分开，禁止混用。

## 输出

- `product-detail.json`：原始落盘路径/最小投影/缓存信息。
- `product-facts.md`：本品事实、来源、未知项、禁写项。
- SIF matrix artifact 路径。

## 用途

Product Detail 的客户评论是洞察的最低证据；SIF 是关键词计划的最低真实数据源。

- **落盘**：复用 Tier 1 的 `Saved full response`，紧凑投影进入 run data 目录。
- **读取**：用 `response_io.py read` 且带 `--fields`/`--path`，禁止整份响应进上下文。
- **判定**：Product Detail 无商品事实则停止；SIF 已尝试但失败可降级，必须显式标记来源。
