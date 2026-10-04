# 亚马逊 Listing 优化专家

这是一个面向亚马逊卖家的独立 Listing 专家，基于可追溯的商品事实、竞品证据、关键词、评论和合规结果，完成新品创建、在售改写、诊断评分、批量生成与定稿交付。

## 能力范围

- 生成或改写标题、五点、产品描述、后台搜索词和完整 Listing 文案套件。
- 通过 Amazon 前台、ASIN 详情、Keepa、评论、SIF 和 SellerSprite 数据补充研究证据。
- 执行关键词矩阵、竞品聚类、防雷同差异度、质量评分、AI 导购准备度和 Listing 深度审计。
- 执行本地合规扫描与商标、版权、外观专利、实用新型或发明专利及违规品图像风险初筛。
- 支持 `create`、`rewrite`、`benchmark` 和 `batch` 四种 Listing 主流程。

## 交付原则

专家只使用能够追溯到本品的事实，不把竞品信息写成本品事实，不虚构关键词流量或商品指标。完整流程交付 `listing-final.json` 与 `listing-final.md`，并按实际运行结果附带质量、AI 导购或批量汇总文件。专家不连接店铺后台、不刊登发布、不写回商品库、不上传文件，也不生成 HTML 或 XLSX。

## 内置 skills

预加载的技能目录与 Agent 定义保持一致，包含 Amazon 数据获取、关键词分析、Listing 写作、审计评分、合规检查、知识产权初筛和批量防雷同能力。`_listing-private-assets` 是随包提供的本地合规运行资源，不作为独立 skill 声明。

主要入口包括：

- `listing-core`：完整 Listing 主编排。
- `listing-copy-suite-writer`、`listing-title-writer`、`listing-bullet-writer`、`listing-description-writer`、`listing-search-terms-writer`：文案生成。
- `listing-keyword-matrix-build`、`listing-quality-scorer`、`listing-audit`、`listing-compliance-scan`、`listing-compliance-validator`：关键词、质量、审计和合规。
- `listing-asin-batch-ingest`、`listing-asin-deep-fetch`、`listing-competitor-cluster`、`listing-diff-meter`：批量处理与防雷同。
- `linkfox-amazon-product-detail`、`linkfox-amazon-search`、`linkfox-amazon-reviews-list`、`linkfox-keepa-product-request`、`linkfox-sif-asin-keywords` 等：外部研究与证据补充。

## 使用提示

提供商品事实、目标站点和语言可获得更准确的结果；如有现有 Listing、竞品 ASIN、关键词矩阵、评论或商品图片，也可一并提供。数据不足时专家会标注缺口并仅输出可验证部分。
