---
name: listing-competitor-cluster
description: 在批量 Listing 任务中，使用宿主本地 Python 或模型能力按已提供的标题、类目和结构特征聚类，为写作阶段生成防雷同 cluster_id。不调用图片相似度或外部 embedding 服务。
---

# Listing Competitor Cluster

仅在批量行数大于 1 时运行。

1. 读取每行已提供的标题、类目、核心属性与可选文本特征。
2. 使用本地 n-gram/Jaccard；宿主若已有 embedding，可额外提供向量，但不是必需依赖。
3. 类目不同的项目强制拆分；相似度达到阈值的项目归入同一 cluster。
4. 为每行写入 `cluster_id`、相似来源和置信度。
5. 下游 writer 在同一 cluster 内切换卖点顺序、句式和场景重点，但不得改变商品事实。

没有足够文本特征时为每行分配 singleton cluster，不阻塞主流程。
