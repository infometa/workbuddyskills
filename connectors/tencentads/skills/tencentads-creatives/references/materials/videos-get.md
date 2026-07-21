# 查询视频列表 (videos/get)

## 接口信息

- **HTTP方法**: GET
- **接口路径**: `/v3.0/videos/get`
- **完整URL**: `https://api.e.qq.com/v3.0/videos/get`
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限

## 功能说明

获取素材库中的视频列表，支持过滤条件、分页查询。

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID（与 organization_id 二选一必填，不支持代理商ID） |
| organization_id | integer | 业务单元ID（与 account_id 二选一必填） |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 | 限制 |
|--------|------|--------|------|------|
| filtering | struct[] | - | 过滤条件数组 | 1-4 个元素 |
| page | integer | 1 | 页码 | 1-99999 |
| page_size | integer | 10 | 每页数量 | 1-100 |
| label_id | integer | - | 标签ID | - |
| business_scenario | integer | - | 业务场景 | 1=内容素材包，2=投放素材包 |

## filtering 过滤条件

每个 filtering 元素包含：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| field | string | 是 | 过滤字段（长度1-32字节） |
| operator | enum | 是 | 操作符 |
| values | string[] | 是 | 字段值数组 |

### 支持的过滤字段

| 过滤字段 | 可选操作符 | values 说明 |
|---------|----------|-----------|
| video_id | EQUALS, CONTAINS | - |
| media_id | EQUALS, IN | EQUALS时数组长度1；IN时数组长度1-100 |
| media_signature | EQUALS, CONTAINS | 数组长度1 |
| media_width | EQUALS | 数组长度1，取值0-3840 |
| media_height | EQUALS | 数组长度1，取值0-2160 |
| created_time | EQUALS, LESS_EQUALS, LESS, GREATER_EQUALS, GREATER | 支持 `YYYY-MM-DD HH:mm:ss` 格式（脚本自动转为时间戳），数组长度1 |
| last_modified_time | EQUALS, LESS_EQUALS, LESS, GREATER_EQUALS, GREATER | 支持 `YYYY-MM-DD HH:mm:ss` 格式（脚本自动转为时间戳），数组长度1 |
| source_type | EQUALS | 见枚举值说明 |
| status | EQUALS, CONTAINS | ADSTATUS_NORMAL, ADSTATUS_DELETED |
| media_description | EQUALS, CONTAINS | 数组长度1，长度1-100字节；CONTAINS 可按素材名称/描述模糊查 |
| sample_aspect_ratio | EQUALS, CONTAINS | 宽高比，数组长度1 |
| owner_account_id | EQUALS, CONTAINS | 数组长度1，长度1-100字节 |
| product_catalog_id | EQUALS, CONTAINS | 数组长度1，长度1-100字节 |
| product_outer_id | EQUALS, CONTAINS | 商品ID，数组长度1，长度1-100字节 |
| first_publication_status | EQUALS | 首发状态 |
| quality_status | - | 质量状态 |
| file_size | LESS_EQUALS | 文件大小（B） |
| height | GREATER_EQUALS, LESS_EQUALS | 视频高度 |
| width | GREATER_EQUALS, LESS_EQUALS | 视频宽度 |
| ratio | EQUALS | 宽高比 |
| video_duration_millisecond | GREATER_EQUALS, LESS_EQUALS | 视频时长（毫秒） |
| aigc_flag | EQUALS | AIGC 标识（数组长度1） |

> 枚举值完整定义见 [enums.md](../enums.md) > 素材管理枚举（source_type、status、similarity_status、first_publication_status、quality_status、aigc_flag、filtering 操作符）

## 响应字段

### 主要响应结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 响应码（0表示成功） |
| message | string | 英文错误消息 |
| message_cn | string | 中文错误消息 |
| data.list | struct[] | 视频信息列表 |
| data.page_info | struct | 分页信息 |

### list 数组元素字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| video_id | integer | 视频ID |
| width | integer | 视频宽度（px） |
| height | integer | 视频高度（px） |
| video_frames | integer | 视频帧数 |
| video_fps | float | 视频帧率 |
| video_codec | string | 视频编码格式（如 H264） |
| video_bit_rate | integer | 视频码率（b/s） |
| audio_codec | string | 音频编码格式（如 AAC） |
| audio_bit_rate | integer | 音频码率（b/s） |
| file_size | integer | 视频文件大小（B） |
| type | enum | 视频类型，见枚举值说明 |
| signature | string | 视频文件签名（MD5值） |
| system_status | enum | 转码状态 |
| description | string | 视频文件描述 |
| preview_url | string | 视频预览地址 |
| key_frame_image_url | string | 视频首帧缩略图地址 |
| created_time | integer | 创建时间（时间戳） |
| last_modified_time | integer | 最后修改时间（时间戳） |
| video_profile_name | string | 视频格式类型 |
| audio_sample_rate | integer | 音频采样率（hz） |
| max_keyframe_interval | integer | 关键帧最大间隔帧数 |
| min_keyframe_interval | integer | 关键帧最小间隔帧数 |
| sample_aspect_ratio | string | 采样纵横比 |
| audio_profile_name | string | 音频格式类型 |
| scan_type | string | 扫描类型 |
| image_duration_millisecond | integer | 画面时长（ms） |
| audio_duration_millisecond | integer | 音频时长（ms） |
| source_type | enum | 视频来源 |
| product_outer_id | string | 商品ID |
| source_reference_id | string | 素材来源关联ID |
| owner_account_id | string | 素材拥有者ID |
| status | enum | 视频状态 |
| similarity_status | enum | 相似度检测状态，见枚举值说明 |

> type（视频格式）、similarity_status、system_status 枚举值见 [enums.md](../enums.md) > 素材管理枚举

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
node scripts/get-videos.mjs '{"account_id":"123456789"}'
```

### 按视频 ID 查询（确认转码状态）

```bash
node scripts/get-videos.mjs '{"account_id":"123456789","filtering":[{"field":"video_id","operator":"EQUALS","values":["123456"]}]}'
```

### 按尺寸查询

```bash
node scripts/get-videos.mjs '{"account_id":"123456789","filtering":[{"field":"media_width","operator":"EQUALS","values":["1280"]},{"field":"media_height","operator":"EQUALS","values":["720"]}]}'
```

### 按来源类型查询

```bash
node scripts/get-videos.mjs '{"account_id":"123456789","filtering":[{"field":"source_type","operator":"EQUALS","values":["SOURCE_TYPE_API"]}]}'
```

### 按视频时长查询（30秒以内）

```bash
node scripts/get-videos.mjs '{"account_id":"123456789","filtering":[{"field":"video_duration_millisecond","operator":"LESS_EQUALS","values":["30000"]}]}'
```

### 批量查询视频 ID

```bash
node scripts/get-videos.mjs '{"account_id":"123456789","filtering":[{"field":"media_id","operator":"IN","values":["111222","333444"]}]}'
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
                "video_id": 1234567890,
                "width": 1280,
                "height": 720,
                "video_frames": 750,
                "video_fps": 25.0,
                "video_codec": "H264",
                "video_bit_rate": 2000000,
                "audio_codec": "AAC",
                "audio_bit_rate": 128000,
                "file_size": 10485760,
                "type": "TYPE_MP4",
                "signature": "19efcaeda3c30e1cf28170d86ecbf5e0",
                "system_status": "MEDIA_STATUS_VALID",
                "description": "产品宣传视频",
                "preview_url": "https://example.com/video.mp4",
                "key_frame_image_url": "https://example.com/thumbnail.jpg",
                "created_time": 1704038400,
                "last_modified_time": 1704124800,
                "source_type": "SOURCE_TYPE_API",
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

1. **微信广告主限制**: 微信广告主调用此接口仅返回以下字段：
   - video_id
   - width
   - height
   - file_size

2. **过滤条件数量**: 最多支持 4 个过滤条件

3. **分页限制**: 
   - page_size 最大值为 100
   - page 最大值为 99999

4. **账户标识**: account_id 不支持代理商ID，与 organization_id 二选一必填

5. **转码状态**: 新上传的视频需要转码，只有 system_status 为 MEDIA_STATUS_VALID 时才可使用

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查account_id是否正确，filtering格式是否正确 |
| 5 | 权限不足 | 确认 API Key 有效且有查询权限 |

## 最佳实践

1. **转码检查**: 查询视频时检查 system_status，确认视频已转码完成
2. **分页查询**: 首次查询使用小的 page_size，确认数据量后再调整
3. **时间过滤**: 建议指定 created_time 过滤条件，避免返回过多数据
4. **批量查询**: 使用 IN 操作符可一次查询多个视频ID（最多100个）
