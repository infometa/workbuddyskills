# RAG / 企业知识库 架构模式

> 基于 Excellent 828 API 企业ERP + 1012 API 跨境电商实战蒸馏

## 一、RAG 管道架构

### 自研三层漏斗检索

```
用户查询
    ↓
[第一层] 向量搜索 Top-50
    pgvector + HNSW 索引
    语义相似度匹配
    ↓
[第二层] BM25 重排序
    精准关键词匹配加权
    TF-IDF + 位置权重
    ↓
[第三层] 业务规则过滤
    权限过滤（用户只能看到有权的数据）
    时效过滤（优先最新文档）
    相关性阈值（低于阈值直接丢弃）
    ↓
最终结果 Top-5
```

### 为什么不用 LangChain/LlamaIndex？

- 企业ERP场景下，通用框架的抽象层反而增加调试成本
- 自研可以精确控制每个环节的行为
- 权限感知必须在检索层实现，通用框架难以深度定制
- 性能优化可以针对业务特征做专项优化

## 二、分块策略

### 滑动窗口分块
```python
def sliding_window_chunk(text, window_size=512, overlap=64):
    chunks = []
    for i in range(0, len(text), window_size - overlap):
        chunk = text[i:i + window_size]
        chunks.append(chunk)
    return chunks
```

### 语义断点分块
```python
def semantic_chunk(text, threshold=0.7):
    # 1. 将文本按段落/标题拆分
    # 2. 计算相邻段落的语义相似度
    # 3. 相似度低于阈值处 → 断点
    # 4. 在断点处切分
    chunks = []
    current_chunk = []
    for paragraph in paragraphs:
        if current_chunk:
            similarity = embed_similarity(current_chunk[-1], paragraph)
            if similarity < threshold:
                chunks.append(join(current_chunk))
                current_chunk = []
        current_chunk.append(paragraph)
    return chunks
```

### 混合策略（推荐）
1. 先语义断点粗切（保证语义完整性）
2. 超长段落再用滑动窗口细切（控制最大长度）
3. 每个chunk保留上下文元数据（来源/章节/页码）

## 三、向量存储选型

| 方案 | 适用场景 | 优势 | 劣势 |
|------|----------|------|------|
| pgvector + HNSW | 中小规模(100万以内) | 与业务数据库统一、事务一致 | 大规模检索速度不如专用 |
| Milvus | 大规模(千万级) | 高性能、分布式 | 部署复杂、额外依赖 |
| Qdrant | 中等规模 | Rust高性能、过滤能力强 | 社区较小 |
| Weaviate | 通用场景 | 多模态、内置分块 | 资源占用大 |

**MVP推荐**：pgvector + HNSW（与业务数据库统一，减少运维负担）

## 四、双存储 RAG

### 架构

```
用户查询
    ├── 向量路径：语义搜索 → "找相似"
    │   适用：模糊查询、概念查询
    │   示例："权限管理怎么设计？" → 找到权限设计文档
    │
    └── 关系路径：结构化查询 → "找精确"
        适用：精确查询、数值查询
        示例："2024年Q3的销售额" → 精确匹配报表数据
```

### 交叉验证
- 两种检索结果取交集 → 高置信度
- 取并集 → 高召回率
- 排序融合 → Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(vector_results, relation_results, k=60):
    scores = {}
    for rank, doc in enumerate(vector_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(relation_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

## 五、权限感知 RAG

### 核心原则
- 检索前过滤：根据用户权限预先过滤知识库范围
- 检索后过滤：对检索结果做权限二次校验
- 摘要脱敏：高权限文档被引用时，仅返回当前用户有权看到的部分

### 实现
```sql
-- 向量搜索 + 权限过滤
SELECT doc_id, content, similarity
FROM knowledge_chunks
WHERE doc_id IN (
    SELECT doc_id FROM doc_permissions
    WHERE user_role = ANY(current_user_roles)
)
ORDER BY embedding <=> query_vector
LIMIT 50;
```

## 六、企业知识库架构

### 文档入库流水线
```
原始文档(PDF/Word/HTML/Markdown)
    ↓
文档解析(Python-docx/PyPDF/BeautifulSoup)
    ↓
元数据提取(标题/作者/日期/分类/权限标签)
    ↓
分块(混合策略: 语义断点 + 滑动窗口)
    ↓
向量化(OpenAI/BGE/GLM embedding)
    ↓
存储(pgvector + 关系数据库)
    ↓
索引构建(HNSW + BM25 + 业务索引)
```

### 增量更新
- 文档变更检测：文件hash对比
- 增量向量化：只处理变更的chunk
- 版本管理：保留历史版本，支持回溯

### 知识自演化
```sql
-- 使用效果追踪
CREATE TABLE knowledge_usage (
    chunk_id UUID,
    query_text TEXT,
    relevance_score FLOAT,  -- 用户反馈
    was_useful BOOLEAN,     -- 是否采纳
    created_at TIMESTAMP
);
-- 定期分析：高命中率chunk提升权重，低命中率chunk降权或淘汰
```

## 七、MVP 快速实现方案

### 最小可行 RAG（1天可上线）
1. PostgreSQL + pgvector 扩展
2. OpenAI/BGE embedding API
3. 简单余弦相似度检索 Top-10
4. 前端搜索框 + 结果列表

### 生产级 RAG（1周可上线）
1. 三层漏斗检索
2. 混合分块策略
3. 权限过滤
4. 增量更新机制
5. 使用效果追踪

### 企业级 RAG（持续优化）
1. 双存储交叉验证
2. 知识自演化
3. 多模型路由
4. 审计日志
5. 性能监控
