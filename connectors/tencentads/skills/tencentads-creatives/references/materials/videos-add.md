# 上传视频 (videos/add)

## 接口信息

- **HTTP方法**: POST
- **接口路径**: `/v3.0/videos/add`
- **完整URL**: `https://api.e.qq.com/v3.0/videos/add`
- **Content-Type**: multipart/form-data
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限

## 功能说明

上传视频文件到素材库。

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| video_file | file | 被上传的视频文件二进制流 | 支持 mp4, mov, avi；最大 100MB |
| signature | string | 视频文件 MD5 签名 | 固定 32 字节 |

### 条件必填参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID（与 organization_id 二选一必填） |
| organization_id | integer | 业务单元ID（与 account_id 二选一必填） |

### 可选参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| description | string | 视频文件描述 | 0-255 字节，不支持@等特殊符号 |
| adcreative_template_id | integer | 创意形式ID | 仅可上传微信规格时需要 |

## 文件格式限制

| 限制项 | 要求 |
|--------|------|
| 支持格式 | mp4, mov, avi |
| 最大文件大小 | 100MB |
| 微信广告 | 扫描类型(scan_type)必须为 Progressive |

## 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 响应码（0表示成功） |
| message | string | 英文错误消息 |
| message_cn | string | 中文错误消息 |
| data.video_id | integer | 视频ID |
| data.cover_image_id | integer | 视频封面图ID |

## 请求示例

### 基础上传

```bash
node scripts/upload-video.mjs '{"account_id":"123456789","file_path":"/tmp/ad.mp4"}'
```

### 带描述的上传

```bash
node scripts/upload-video.mjs '{"account_id":"123456789","file_path":"/tmp/ad.mp4","description":"产品宣传视频"}'
```

> 上传成功后返回 `video_id` 和自动生成的 `cover_image_id`。
> 视频需要转码，可用 `get-videos.mjs` 轮询 `system_status` 确认转码完成（`MEDIA_STATUS_VALID`）后再使用。

## 响应示例

### 成功响应

```json
{
    "code": 0,
    "message": "",
    "message_cn": "",
    "data": {
        "video_id": 1234567890,
        "cover_image_id": 9876543210
    }
}
```

### 错误响应

```json
{
    "code": 3,
    "message": "Parameter error",
    "message_cn": "参数错误：签名不匹配",
    "data": {}
}
```

## 注意事项

1. **签名计算**: 必须使用原始文件计算 MD5 签名
   - Linux: `md5sum file | awk '{print $1}'`
   - macOS: `md5 -q file`

2. **文件大小**: 单个视频文件不能超过 100MB

3. **微信广告限制**: 
   - 扫描类型(scan_type)必须为 Progressive 类型
   - 需要指定 adcreative_template_id

4. **描述限制**: 不支持 @ 等特殊符号

5. **转码处理**: 视频上传后需要转码，可通过 videos/get 查询转码状态

6. **封面图**: 成功上传后会自动生成封面图 cover_image_id

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查签名是否正确，文件格式是否支持 |
| 5 | 权限不足 | 确认 API Key 有效且有上传权限 |

## 最佳实践

1. **签名验证**: 上传前先本地计算签名，确保文件完整性
2. **格式选择**: 推荐使用 mp4 格式，兼容性最好
3. **编码规范**: 视频编码推荐使用 H.264，音频编码推荐使用 AAC
4. **错误重试**: 网络错误时可重试，使用相同签名
5. **转码监控**: 上传后定期查询转码状态，确认视频可用
