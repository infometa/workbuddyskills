# 获取妙思版权音频列表 (muse_audios/get)

## 接口信息

- **HTTP方法**: POST
- **接口路径**: `/v3.0/muse_audios/get`
- **完整URL**: `https://api.e.qq.com/v3.0/muse_audios/get`
- **Content-Type**: application/json
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限

## 功能说明

获取妙思平台提供的版权音频列表，用于视频创意制作。

## 请求Body参数（JSON格式）

### 必填参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| fields | string[] | 需要返回的字段列表 | 数组长度1-1024，字段长度1-64字节 |

### 可选参数

| 参数名 | 类型 | 默认值 | 说明 | 限制 |
|--------|------|--------|------|------|
| page | integer | 1 | 页码 | 1-99999 |
| page_size | integer | 10 | 每页数量 | 1-100 |

### fields 可选字段

| 字段名 | 说明 |
|--------|------|
| audio_id | 音频ID |
| audio_name | 音频文件名称 |
| cover_image_url | 音频封面图地址 |
| author | 音频作者 |
| duration | 音频时长（秒） |
| expire_time | 音频版权过期时间戳 |
| feel_tags | 音频情感标签列表 |
| genre_tags | 音频流派标签列表 |

## 响应字段

### 主要响应结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 响应码（0表示成功） |
| message | string | 英文错误消息 |
| message_cn | string | 中文错误消息 |
| data.list | struct[] | 音频信息列表 |
| data.page_info | struct | 分页信息 |

### list 数组元素字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| audio_id | string | 音频ID |
| audio_name | string | 音频文件名称 |
| cover_image_url | string | 音频封面图地址 |
| author | string | 音频作者 |
| duration | float | 音频时长（秒） |
| expire_time | integer | 音频版权过期时间戳 |
| feel_tags | string[] | 音频情感标签列表 |
| genre_tags | string[] | 音频流派标签列表 |

### page_info 分页信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total_number | integer | 总记录数 |
| total_page | integer | 总页数 |

## 请求示例

### 基础查询（返回全部字段）

```bash
node scripts/get-audios.mjs '{"account_id":"123456789"}'
```

### 指定返回字段

```bash
node scripts/get-audios.mjs '{"account_id":"123456789","fields":["audio_id","audio_name","author","duration","feel_tags"]}'
```

### 分页查询

```bash
node scripts/get-audios.mjs '{"account_id":"123456789","page":2,"page_size":20}'
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
                "audio_id": "88",
                "audio_name": "8-bit",
                "cover_image_url": "https://example.com/cover.jpg",
                "author": "Cassiopeia",
                "duration": 51.36,
                "expire_time": 1760025599,
                "feel_tags": [
                    "复古",
                    "可爱/童真"
                ],
                "genre_tags": [
                    "电子"
                ]
            },
            {
                "audio_id": "89",
                "audio_name": "Summer Vibes",
                "cover_image_url": "https://example.com/cover2.jpg",
                "author": "MusicMaker",
                "duration": 120.5,
                "expire_time": 1760025599,
                "feel_tags": [
                    "欢快",
                    "活力"
                ],
                "genre_tags": [
                    "流行",
                    "电子"
                ]
            }
        ],
        "page_info": {
            "page": 1,
            "page_size": 10,
            "total_number": 100,
            "total_page": 10
        }
    }
}
```

### 错误响应

```json
{
    "code": 3,
    "message": "Parameter error",
    "message_cn": "参数错误：fields 不能为空",
    "data": {}
}
```

## 常见标签说明

### 情感标签 (feel_tags)

常见的情感标签包括：
- 欢快
- 活力
- 复古
- 可爱/童真
- 温馨
- 励志
- 浪漫
- 紧张
- 悲伤

### 流派标签 (genre_tags)

常见的流派标签包括：
- 电子
- 流行
- 摇滚
- 古典
- 嘻哈
- 民谣
- 爵士

## 注意事项

1. **fields 必填**: 必须指定需要返回的字段列表

2. **版权有效期**: 注意检查 expire_time，确保音频版权在使用时仍然有效

3. **分页限制**: 
   - page_size 最大值为 100
   - page 最大值为 99999

4. **用途说明**: 妙思音频主要用于视频创意制作，需配合视频编辑工具使用

5. **标签筛选**: 可根据 feel_tags 和 genre_tags 选择适合的背景音乐

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查 fields 参数是否正确 |
| 5 | 权限不足 | 确认 API Key 有效且有查询权限 |

## 最佳实践

1. **按需获取字段**: 只请求需要的字段，减少数据传输
2. **分页遍历**: 使用分页获取完整音频列表
3. **标签匹配**: 根据视频内容选择匹配的情感和流派标签
4. **版权检查**: 使用前检查音频版权是否在有效期内
5. **缓存列表**: 音频列表相对稳定，可适当缓存减少请求
