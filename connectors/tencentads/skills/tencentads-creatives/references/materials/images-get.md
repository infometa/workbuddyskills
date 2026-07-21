# 查询图片列表 (images/get)

## 接口信息

- **HTTP方法**: GET
- **接口路径**: `/v3.0/images/get`
- **完整URL**: `https://api.e.qq.com/v3.0/images/get`
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限, account_management

## 功能说明

获取素材库中的图片列表，支持过滤条件、分页查询。

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID（与 organization_id 二选一必填） |
| organization_id | integer | 业务单元ID（与 account_id 二选一必填） |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 | 限制 |
|--------|------|--------|------|------|
| filtering | struct[] | - | 过滤条件数组 | 1-4 个元素 |
| page | integer | 1 | 页码 | 1-99999 |
| page_size | integer | 10 | 每页数量 | 1-100 |
| label_id | integer | - | 标签ID | - |
| business_scenario | integer | - | 业务场景 | 1=内容素材包，2=投放素材包 |

> **注意**: 若不传 created_time 过滤条件，默认查询半年内数据。

## filtering 过滤条件

每个 filtering 元素包含：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| field | string | 是 | 过滤字段 |
| operator | enum | 是 | 操作符 |
| values | string[] | 是 | 字段值数组 |

### 支持的过滤字段

| 过滤字段 | 可选操作符 | values 说明 |
|---------|----------|-----------|
| image_id | EQUALS, CONTAINS, IN | IN时数组长度1-100；字段长度1-48字节 |
| image_signature | EQUALS, CONTAINS | 数组长度1，字段长度1-32字节 |
| image_width | EQUALS | 数组长度1，取值0-2000 |
| image_height | EQUALS | 数组长度1，取值0-2000 |
| created_time | EQUALS, LESS_EQUALS, LESS, GREATER_EQUALS, GREATER | 支持 `YYYY-MM-DD HH:mm:ss` 格式（脚本自动转为时间戳），数组长度1 |
| last_modified_time | EQUALS, LESS_EQUALS, LESS, GREATER_EQUALS, GREATER | 支持 `YYYY-MM-DD HH:mm:ss` 格式（脚本自动转为时间戳），数组长度1 |
| source_type | EQUALS | 见枚举值说明 |
| status | EQUALS, CONTAINS | ADSTATUS_NORMAL, ADSTATUS_DELETED |
| image_description | EQUALS, CONTAINS | 数组长度1，字段长度1-256字节；CONTAINS 可按素材名称/描述模糊查 |
| sample_aspect_ratio | EQUALS, CONTAINS | 宽高比，数组长度1 |
| owner_account_id | EQUALS, CONTAINS | 数组长度1；10字节 |
| product_catalog_id | EQUALS, CONTAINS | 商品库ID；数组长度1 |
| product_outer_id | EQUALS, CONTAINS | 商品ID，字段长度1-256字节 |
| first_publication_status | EQUALS | 首发状态 |
| quality_status | EQUALS | 质量状态 |
| file_size | LESS_EQUALS | 文件大小（B） |
| height | GREATER_EQUALS, LESS_EQUALS | 图片高度 |
| width | GREATER_EQUALS, LESS_EQUALS | 图片宽度 |
| ratio | EQUALS | 宽高比 |
| aigc_flag | EQUALS | AIGC 标识（数组长度1） |

> 枚举值完整定义见 [enums.md](../enums.md) > 素材管理枚举（source_type、status、similarity_status、first_publication_status、quality_status、aigc_flag、filtering 操作符）

## 响应字段

### 主要响应结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 响应码（0表示成功） |
| message | string | 英文错误消息 |
| message_cn | string | 中文错误消息 |
| data.list | struct[] | 图片信息列表 |
| data.page_info | struct | 分页信息 |

### list 数组元素字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| image_id | string | 图片ID |
| width | integer | 图片宽度（px） |
| height | integer | 图片高度（px） |
| file_size | integer | 图片大小（B） |
| type | enum | 图片类型，见枚举值说明 |
| signature | string | 图片文件签名（MD5值） |
| source_signature | string | 图片源文件签名（裁剪前源文件的MD5值） |
| preview_url | string | 预览地址 |
| source_type | enum | 图片来源 |
| image_usage | enum | 图片用途 |
| created_time | integer | 创建时间（时间戳） |
| last_modified_time | integer | 最后修改时间（时间戳） |
| product_catalog_id | integer | 商品库ID |
| product_outer_id | string | 商品ID |
| source_reference_id | string | 素材来源关联ID |
| owner_account_id | string | 素材拥有者ID |
| status | enum | 状态 |
| sample_aspect_ratio | string | 图片宽高比 |
| similarity_status | enum | 相似度检测状态，见枚举值说明 |

> type（图片格式）、image_usage、similarity_status 枚举值见 [enums.md](../enums.md) > 素材管理枚举

### page_info 分页信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total_number | integer | 总记录数 |
| total_page | integer | 总页数 |

## 请求示例

### 基础查询（最近半年）

```bash
node scripts/get-images.mjs '{"account_id":"123456789"}'
```

### 按尺寸查询

```bash
node scripts/get-images.mjs '{"account_id":"123456789","filtering":[{"field":"image_width","operator":"EQUALS","values":["1280"]},{"field":"image_height","operator":"EQUALS","values":["720"]}]}'
```

### 按图片 ID 批量查询

```bash
node scripts/get-images.mjs '{"account_id":"123456789","filtering":[{"field":"image_id","operator":"IN","values":["111222","333444"]}]}'
```

### 按签名查询

```bash
node scripts/get-images.mjs '{"account_id":"123456789","filtering":[{"field":"image_signature","operator":"EQUALS","values":["f4c8a3bc4deb305fb74cb08ed395b98c"]}]}'
```

### 按来源类型查询

```bash
node scripts/get-images.mjs '{"account_id":"123456789","filtering":[{"field":"source_type","operator":"EQUALS","values":["SOURCE_TYPE_API"]}]}'
```

## 响应示例

### 成功响应

```json
{
    "code": 0,
    "message": "",
    "message_cn": "",
    "data": {
        "list": [
            {
                "image_id": "1234567890",
                "width": 1280,
                "height": 720,
                "file_size": 102400,
                "type": "TYPE_JPG",
                "signature": "f4c8a3bc4deb305fb74cb08ed395b98c",
                "source_signature": "83a447d55c02dd4efe8776e369915eb7",
                "preview_url": "https://example.com/example.jpg",
                "source_type": "SOURCE_TYPE_API",
                "created_time": 1704038400,
                "last_modified_time": 1704124800,
                "status": "ADSTATUS_NORMAL"
            }
        ],
        "page_info": {
            "page": 1,
            "page_size": 10,
            "total_number": 1,
            "total_page": 1
        }
    }
}
```

### 错误响应

```json
{
    "code": 3,
    "message": "Parameter error",
    "message_cn": "参数错误",
    "data": {}
}
```

## 注意事项

1. **默认时间范围**: 若不指定 created_time 过滤条件，默认只查询半年内数据

2. **过滤条件数量**: 最多支持 4 个过滤条件

3. **分页限制**: 
   - page_size 最大值为 100
   - page 最大值为 99999

4. **账户标识**: account_id 和 organization_id 二选一必填

5. **图片来源**: source_type 可用于区分不同来源的图片

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查account_id是否正确，filtering格式是否正确 |
| 5 | 权限不足 | 确认 API Key 有效且有查询权限 |

## 最佳实践

1. **分页查询**: 首次查询使用小的 page_size（如 10-20），确认数据量后再调整
2. **时间过滤**: 建议指定 created_time 过滤条件，避免返回过多数据
3. **批量查询**: 使用 IN 操作符可一次查询多个图片ID（最多100个）
4. **字段筛选**: 根据需要使用过滤条件减少返回数据量
