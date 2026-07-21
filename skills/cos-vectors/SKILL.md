---
name: cos-vectors
description: '腾讯云 COS 向量桶全功能管理技能。覆盖向量桶、索引、向量数据的全生命周期管理，包括创建/删除/查询向量桶、创建/管理索引、插入/查询/搜索/删除向量数据、策略管理等 16 个核心能力。Trigger phrases: vector bucket, vector index, vector search, 向量桶, 向量索引, 向量搜索, 向量存储, 插入向量, 相似度搜索,
  COS vector.'
description_zh: 腾讯云 COS 向量桶管理（索引、存储、相似度搜索）
description_en: 腾讯云 COS 向量桶全功能管理技能。覆盖向量桶、索引、向量数据的全生命周期管理，包括创建/删除/查询向量桶、创建/管理索引、插入/查询/搜索/删除向量数据、策...
version: 1.0.1
metadata:
  clawdbot:
    requires:
      env:
      - COS_VECTORS_SECRET_ID
      - COS_VECTORS_SECRET_KEY
    primaryEnv: COS_VECTORS_SECRET_ID
---

# 腾讯云 COS 向量桶全功能管理技能

通过 cos-python-sdk-v5 的 CosVectorsClient 管理腾讯云 COS 向量桶的完整生命周期。

## 能力总览

| 类别 | 能力 | 脚本 |
|------|------|------|
| **向量桶管理** | 创建向量桶 | `create_vector_bucket.py` |
| | 删除向量桶 | `delete_vector_bucket.py` |
| | 查询向量桶信息 | `get_vector_bucket.py` |
| | 列出所有向量桶 | `list_vector_buckets.py` |
| **桶策略管理** | 设置桶策略 | `put_vector_bucket_policy.py` |
| | 获取桶策略 | `get_vector_bucket_policy.py` |
| | 删除桶策略 | `delete_vector_bucket_policy.py` |
| **索引管理** | 创建索引 | `create_index.py` |
| | 查询索引信息 | `get_index.py` |
| | 列出所有索引 | `list_indexes.py` |
| | 删除索引 | `delete_index.py` |
| **向量数据操作** | 插入/更新向量 | `put_vectors.py` |
| | 获取指定向量 | `get_vectors.py` |
| | 列出向量列表 | `list_vectors.py` |
| | 删除向量 | `delete_vectors.py` |
| | 相似度搜索 | `query_vectors.py` |

---

## 首次使用 — 环境检查

### 步骤 1：检查 Python SDK

```bash
python3 -c "from qcloud_cos import CosConfig, CosVectorsClient; print('OK')"
```

如果失败，安装 SDK：

```bash
pip3 install cos-python-sdk-v5 --upgrade
```

### 步骤 2：检查凭证

确认以下环境变量已设置（或准备通过命令行参数传入）：

- `COS_VECTORS_SECRET_ID` — 腾讯云 API 密钥 ID
- `COS_VECTORS_SECRET_KEY` — 腾讯云 API 密钥 Key

如果未设置，引导用户提供凭证：

> 请提供腾讯云凭证来连接 COS 向量存储服务：
> 1. **SecretId** — 腾讯云 API 密钥 ID
> 2. **SecretKey** — 腾讯云 API 密钥 Key
> 3. **Region** — 存储桶区域（如 ap-guangzhou）
> 4. **Bucket** — 向量桶名称（格式 BucketName-APPID，如 examplebucket-1250000000）
>
> 密钥获取：[腾讯云控制台 > 访问管理 > API密钥管理](https://console.cloud.tencent.com/cam/capi)

### 公共参数

所有脚本都支持以下公共参数：

| 参数 | 必需 | 说明 |
|------|:---:|------|
| `--secret-id` | ✅ | 腾讯云 SecretId（或环境变量 `COS_VECTORS_SECRET_ID`） |
| `--secret-key` | ✅ | 腾讯云 SecretKey（或环境变量 `COS_VECTORS_SECRET_KEY`） |
| `--region` | ✅ | 地域，如 `ap-guangzhou` |
| `--bucket` | ✅ | 向量桶名称，格式 `BucketName-APPID` |
| `--scheme` | ❌ | 协议，`http`（默认）或 `https` |

---

## 一、向量桶管理

### 1. 创建向量桶

```bash
python3 {baseDir}/scripts/create_vector_bucket.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  [--sse-type AES256]
```

| 专有参数 | 说明 |
|----------|------|
| `--sse-type` | 可选，加密类型，当前仅支持 `AES256` |

### 2. 删除向量桶

```bash
python3 {baseDir}/scripts/delete_vector_bucket.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>"
```

### 3. 查询向量桶信息

```bash
python3 {baseDir}/scripts/get_vector_bucket.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>"
```

### 4. 列出所有向量桶

```bash
python3 {baseDir}/scripts/list_vector_buckets.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  [--max-results 10] \
  [--prefix "my-"]
```

| 专有参数 | 说明 |
|----------|------|
| `--max-results` | 可选，最大返回数量 |
| `--prefix` | 可选，桶名前缀过滤 |

---

## 二、桶策略管理

### 5. 设置桶策略

```bash
python3 {baseDir}/scripts/put_vector_bucket_policy.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --policy '{"Statement": [...]}'
```

| 专有参数 | 说明 |
|----------|------|
| `--policy` | 必需，策略 JSON 字符串 |

### 6. 获取桶策略

```bash
python3 {baseDir}/scripts/get_vector_bucket_policy.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>"
```

### 7. 删除桶策略

```bash
python3 {baseDir}/scripts/delete_vector_bucket_policy.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>"
```

---

## 三、索引管理

### 8. 创建索引

```bash
python3 {baseDir}/scripts/create_index.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --dimension <Dimension> \
  [--data-type float32] \
  [--distance-metric cosine] \
  [--non-filterable-keys key1,key2]
```

| 专有参数 | 必需 | 说明 |
|----------|:---:|------|
| `--index` | ✅ | 索引名称 |
| `--dimension` | ✅ | 向量维度，范围 1-4096 |
| `--data-type` | ❌ | 数据类型，默认 `float32` |
| `--distance-metric` | ❌ | 距离度量，`cosine`（默认）或 `euclidean` |
| `--non-filterable-keys` | ❌ | 非过滤元数据键，逗号分隔 |

### 9. 查询索引信息

```bash
python3 {baseDir}/scripts/get_index.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>"
```

### 10. 列出所有索引

```bash
python3 {baseDir}/scripts/list_indexes.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  [--max-results 10] \
  [--prefix "demo-"]
```

### 11. 删除索引

```bash
python3 {baseDir}/scripts/delete_index.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>"
```

---

## 四、向量数据操作

### 12. 插入/更新向量

```bash
# 方式 1：直接传 JSON
python3 {baseDir}/scripts/put_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --vectors '[{"key":"doc-001","data":{"float32":[0.1,0.2,...]},"metadata":{"title":"标题"}}]'

# 方式 2：通过文件传入
python3 {baseDir}/scripts/put_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --vectors-file vectors.json
```

| 专有参数 | 说明 |
|----------|------|
| `--index` | 必需，索引名称 |
| `--vectors` | 向量数据 JSON 字符串 |
| `--vectors-file` | 向量数据 JSON 文件路径（与 --vectors 二选一） |

**向量 JSON 格式**：
```json
[
  {
    "key": "doc-001",
    "data": {"float32": [0.1, 0.2, 0.3, "..."]},
    "metadata": {"title": "文档标题", "category": "分类"}
  }
]
```

### 13. 获取指定向量

```bash
python3 {baseDir}/scripts/get_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --keys "doc-001,doc-002" \
  [--return-data] \
  [--return-metadata]
```

| 专有参数 | 说明 |
|----------|------|
| `--index` | 必需，索引名称 |
| `--keys` | 必需，向量键列表，逗号分隔 |
| `--return-data` | 可选，返回向量数据 |
| `--return-metadata` | 可选，返回元数据 |

### 14. 列出向量列表

```bash
python3 {baseDir}/scripts/list_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  [--max-results 10] \
  [--return-data] \
  [--return-metadata]
```

| 专有参数 | 说明 |
|----------|------|
| `--index` | 必需，索引名称 |
| `--max-results` | 可选，最大返回数量 |
| `--return-data` | 可选，返回向量数据 |
| `--return-metadata` | 可选，返回元数据 |
| `--segment-count` | 可选，分段总数 |
| `--segment-index` | 可选，分段索引（从0开始） |

### 15. 删除向量

```bash
python3 {baseDir}/scripts/delete_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --keys "doc-001,doc-002"
```

### 16. 相似度搜索（query_vectors）

```bash
# 方式 1：直接传查询向量
python3 {baseDir}/scripts/query_vectors.py \
  --secret-id "<SecretId>" \
  --secret-key "<SecretKey>" \
  --region "<Region>" \
  --bucket "<BucketName-APPID>" \
  --index "<IndexName>" \
  --query-vector '[0.1, 0.2, ...]' \
  --top-k 5 \
  [--filter '{"category": {"$eq": "AI"}}'] \
  [--return-distance] \
  [--return-metadata]

# 方式 2：通过文件传入查询向量
python3 {baseDir}/scripts/query_vectors.py \
  ... \
  --query-vector-file query.json \
  --top-k 5
```

| 专有参数 | 必需 | 说明 |
|----------|:---:|------|
| `--index` | ✅ | 索引名称 |
| `--query-vector` | ✅* | 查询向量 JSON 数组 |
| `--query-vector-file` | ✅* | 查询向量文件（与 --query-vector 二选一） |
| `--top-k` | ✅ | 返回最相似的 K 个结果 |
| `--filter` | ❌ | 过滤条件 JSON，如 `{"category": {"$eq": "AI"}}` |
| `--return-distance` | ❌ | 返回距离/相似度值 |
| `--return-metadata` | ❌ | 返回元数据 |

---

## 关键技术细节

1. **CosVectorsClient**：向量桶专用客户端，不同于普通的 CosS3Client
2. **Endpoint 配置**：使用 `Endpoint` 参数（`vectors.<Region>.coslake.com`），SDK 会自动拼接 bucket 前缀
3. **协议**：默认使用 `http` 协议
4. **桶名格式**：必须为 `BucketName-APPID` 格式，如 `examplebucket-1250000000`
5. **桶名规则**：仅支持小写字母、数字和中划线 `-`，长度 3-63 个字符
6. **向量维度**：范围 1-4096
7. **数据类型**：当前支持 `float32`
8. **距离度量**：支持 `cosine`（余弦相似度）和 `euclidean`（欧氏距离）
9. **加密类型**：可选 `AES256` 服务端加密

## 公共模块

所有脚本共享 `common.py` 公共模块，提供：
- `base_parser()` — 创建包含凭证参数的基础解析器
- `create_client()` — 初始化 CosVectorsClient
- `success_output()` — 统一的成功输出格式（JSON）
- `fail()` — 统一的错误输出格式并退出
- `handle_error()` — 统一的异常处理（CosServiceError / CosClientError）
- `run()` — 包装主函数并捕获异常

## 错误处理

- **CosServiceError**：服务端错误（如桶已存在、权限不足等）
- **CosClientError**：客户端错误（如网络问题、参数错误等）

所有脚本输出统一 JSON 格式：
```json
{"success": true, "action": "...", ...}   // 成功
{"success": false, "error": "..."}        // 失败
```

调用失败时先检查：
1. 凭证是否正确
2. Region 是否正确
3. Bucket 名称格式是否符合要求
4. 网络是否连通

## API 参考

详细 API 参数定义见 `references/api_reference.md`。
