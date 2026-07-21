# IR / Web / Data 顶会术语库（SIGIR / WWW / KDD / CIKM / WSDM / RecSys / VLDB / ICDE）

> 在 general-cs-terms.md + ml-venues.md 之上，补充信息检索 / Web / 数据 / 推荐系统术语。

## 信息检索

| 英文 | 中文（首选） |
|---|---|
| information retrieval (IR) | 信息检索 |
| query | 查询 |
| document | 文档 |
| corpus | 语料 / 文档集合 |
| relevance | 相关性 |
| ranking | 排序 |
| learning-to-rank (LTR) | 学习排序 |
| pointwise / pairwise / listwise | 单点 / 成对 / 列表式 |
| TF-IDF | TF-IDF |
| BM25 | BM25 |
| dense retrieval | 稠密检索 |
| sparse retrieval | 稀疏检索 |
| ANN search | 近似最近邻搜索 / ANN 搜索 |
| inverted index | 倒排索引 |
| reranker / reranking | 重排序器 / 重排 |
| query expansion | 查询扩展 |
| pseudo-relevance feedback | 伪相关反馈 |
| cross-encoder | 交叉编码器 |
| bi-encoder / dual-encoder | 双塔编码器 |

## 评估指标（IR）

| 英文 | 中文（首选） |
|---|---|
| nDCG | nDCG |
| MAP（mean average precision）| 平均精度均值 / MAP |
| MRR (mean reciprocal rank) | 平均倒数排名 |
| precision@k / P@k | 前 k 精确率 |
| recall@k | 前 k 召回率 |
| hit ratio @ k (HR@k) | 命中率@k |

## 推荐系统

| 英文 | 中文（首选） |
|---|---|
| recommender system | 推荐系统 |
| collaborative filtering (CF) | 协同过滤 |
| content-based filtering | 基于内容的过滤 |
| matrix factorization (MF) | 矩阵分解 |
| user-item matrix | 用户-物品矩阵 |
| user embedding / item embedding | 用户嵌入 / 物品嵌入 |
| implicit feedback | 隐式反馈 |
| explicit feedback | 显式反馈 |
| cold start | 冷启动 |
| sequential recommendation | 序列推荐 |
| session-based recommendation | 会话推荐 |
| candidate generation | 候选生成 |
| recall stage / ranking stage | 召回阶段 / 排序阶段 |
| CTR (click-through rate) | 点击率 |
| CVR (conversion rate) | 转化率 |

## Web / 图

| 英文 | 中文（首选） |
|---|---|
| web graph | 网页图 / Web 图 |
| PageRank | PageRank |
| HITS | HITS |
| crawling | 爬取 |
| indexing | 索引 |
| social network | 社交网络 |
| influence maximization | 影响力最大化 |
| community detection | 社区发现 |
| link prediction | 链接预测 |
| knowledge graph (KG) | 知识图谱 |
| knowledge graph embedding (KGE) | 知识图谱嵌入 |
| triple | 三元组 |
| entity | 实体 |
| relation | 关系 |

## 数据挖掘

| 英文 | 中文（首选） |
|---|---|
| data mining | 数据挖掘 |
| frequent pattern mining | 频繁模式挖掘 |
| association rule | 关联规则 |
| clustering | 聚类 |
| anomaly detection | 异常检测 |
| outlier detection | 离群点检测 |
| time-series analysis | 时间序列分析 |
| spatial data | 空间数据 |
| trajectory data | 轨迹数据 |
| streaming data | 流数据 |

## 数据库 / 大数据

| 英文 | 中文（首选） |
|---|---|
| database | 数据库 |
| relational database | 关系数据库 |
| OLAP / OLTP | OLAP / OLTP（保留） |
| query optimization | 查询优化 |
| index | 索引 |
| transaction | 事务 |
| ACID | ACID（保留）|
| NoSQL | NoSQL（保留） |
| MapReduce | MapReduce（保留） |
| sharding | 分片 |
| replication | 复制 |
| eventual consistency | 最终一致性 |
| consensus | 共识 |
| Paxos / Raft | Paxos / Raft（保留） |

## 不译保留（IR/Data 高频）

- SIGIR, WWW (TheWebConf), KDD, CIKM, WSDM, RecSys, VLDB, ICDE, SIGMOD
- BM25, TF-IDF, PageRank, HITS, SimRank
- Spark, Hadoop, Flink, Kafka, Pulsar
- MongoDB, Redis, Elasticsearch, Cassandra
- MS-MARCO, TREC, BEIR, MIRACL
- MovieLens, Amazon-Books, Netflix, Yelp
- Freebase, DBpedia, Wikidata, YAGO
