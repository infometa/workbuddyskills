# COS 向量桶 API 参考

> 官方文档: https://cloud.tencent.com/document/product/436/127755

## create_vector_bucket

创建一个向量桶，用于专门存储和检索向量数据。

### 方法原型

```python
create_vector_bucket(self, Bucket, SseType=None, **kwargs)
```

### 请求参数

| 参数名称 | 描述 | 类型 | 是否必选 |
|----------|------|------|----------|
| Bucket | 向量桶名称，格式为 `BucketName-APPID`。例如 `examplebucket-1250000000`。仅支持小写字母、数字和中划线 `-`，长度 3-63 个字符。 | String | 是 |
| SseType | 加密类型，用于启用服务端加密。当前仅支持 `AES256`。 | String | 否 |

### 返回值

方法返回一个元组 `(resp, data)`：

- **resp (dict)**: 响应头信息
- **data (dict)**: 响应数据，包含向量桶的 Qcs（资源描述符）

### 异常

- **CosServiceError**: 服务端返回的错误（如桶已存在、权限不足、区域不支持等）
- **CosClientError**: 客户端错误（如网络不通、参数格式错误等）

### CosVectorsClient 初始化

向量桶使用专用客户端 `CosVectorsClient`，而非普通的 `CosS3Client`。

```python
from qcloud_cos import CosConfig, CosVectorsClient

config = CosConfig(
    Region='ap-guangzhou',           # 替换为实际区域
    SecretId='your-secret-id',       # 替换为实际密钥 ID
    SecretKey='your-secret-key',     # 替换为实际密钥 Key
    Scheme='http',                   # 协议，默认 http
    Domain='vectors.ap-guangzhou.coslake.com',  # 向量桶专用域名
    Token=None,                      # 永久密钥无需填写
)
client = CosVectorsClient(config)
```

### 域名格式

向量桶使用特殊域名格式：

```
vectors.<Region>.coslake.com
```

例如：
- 广州：`vectors.ap-guangzhou.coslake.com`
- 上海：`vectors.ap-shanghai.coslake.com`
- 北京：`vectors.ap-beijing.coslake.com`

### 示例 1：创建普通向量桶

```python
from qcloud_cos import CosConfig, CosVectorsClient, CosServiceError

config = CosConfig(
    Region='ap-guangzhou',
    SecretId=secret_id,
    SecretKey=secret_key,
    Scheme='http',
    Domain='vectors.ap-guangzhou.coslake.com',
    Token=None,
)
client = CosVectorsClient(config)

try:
    resp, data = client.create_vector_bucket(
        Bucket='examplebucket-1250000000'
    )
    print('向量桶创建成功')
    print('响应头:', resp)
    print('响应数据:', data)
except CosServiceError as e:
    print(f'创建失败: {e}')
```

### 示例 2：创建加密向量桶

```python
try:
    resp, data = client.create_vector_bucket(
        Bucket='examplebucket-1250000000',
        SseType='AES256'
    )
    print('向量桶创建成功（已启用 AES256 加密）')
    print(resp)
except CosServiceError as e:
    print(f'创建失败: {e}')
```

## 注意事项

1. **SDK 版本**：需要 cos-python-sdk-v5 >= 1.9.x，建议使用最新版本
2. **密钥安全**：建议使用子账号密钥，遵循最小权限原则
3. **区域支持**：并非所有区域都支持向量桶，请参考官方文档确认
4. **桶名唯一性**：向量桶名称在全局范围内唯一，创建前确认名称未被占用
