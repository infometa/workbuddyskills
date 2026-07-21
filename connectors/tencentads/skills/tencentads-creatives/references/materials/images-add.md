# 上传图片 (images/add)

## 接口信息

- **HTTP方法**: POST
- **接口路径**: `/v3.0/images/add`
- **完整URL**: `https://api.e.qq.com/v3.0/images/add`
- **Content-Type**: multipart/form-data
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限, account_management

## 功能说明

上传图片文件到素材库，支持文件流和 Base64 两种上传方式。

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| upload_type | enum | 上传方式 | `UPLOAD_TYPE_FILE` 或 `UPLOAD_TYPE_BYTES` |
| signature | string | 图片文件 MD5 签名 | 固定 32 字节 |

### 条件必填参数

| 参数名 | 类型 | 触发条件 | 说明 | 限制 |
|--------|------|----------|------|------|
| account_id | integer | - | 广告主账号ID | 与 organization_id 二选一必填 |
| organization_id | integer | - | 业务单元ID | 与 account_id 二选一必填 |
| file | file | upload_type=UPLOAD_TYPE_FILE | 图片文件二进制流 | 见文件限制 |
| bytes | string | upload_type=UPLOAD_TYPE_BYTES | 图片 Base64 编码 | 1-10485760 字节 |

### 可选参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| image_usage | enum | 图片用途 | 见枚举值说明 |
| description | string | 图片文件描述 | 0-255 字节，不支持@等特殊符号 |
| resize_width | integer | 图片宽度（px） | 1-4000 |
| resize_height | integer | 图片高度（px） | 1-4000 |
| resize_file_size | integer | 图片大小（B） | - |

> image_usage、upload_type 枚举值见 [enums.md](../enums.md) > 素材管理枚举

## 文件格式限制

| 限制项 | 要求 |
|--------|------|
| 支持格式 | jpg, png, gif |
| 最大文件大小 | 10MB（1MB = 1024KB = 1048576B） |
| GIF播放时长 | ≤ 5秒 |

## 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 响应码（0表示成功） |
| message | string | 英文错误消息 |
| message_cn | string | 中文错误消息 |
| data.image_id | string | 图片ID |
| data.image_width | integer | 图片宽度（px） |
| data.image_height | integer | 图片高度（px） |
| data.image_file_size | integer | 图片大小（B） |
| data.image_type | enum | 图片类型 |
| data.image_signature | string | 图片文件签名（MD5值） |
| data.outer_image_id | string | 调用方图片ID |
| data.preview_url | string | 预览地址 |
| data.description | string | 图片文件描述 |

## 请求示例

### 基础上传

```bash
node scripts/upload-image.mjs '{"account_id":"123456789","file_path":"/tmp/banner.jpg"}'
```

### 带描述的上传

```bash
node scripts/upload-image.mjs '{"account_id":"123456789","file_path":"/tmp/banner.png","description":"首页横幅"}'
```

### 指定图片用途

```bash
node scripts/upload-image.mjs '{"account_id":"123456789","file_path":"/tmp/pendant.png","image_usage":"IMAGE_USAGE_MARKETING_PENDANT"}'
```

## 响应示例

### 成功响应

```json
{
    "code": 0,
    "message": "",
    "message_cn": "",
    "data": {
        "image_id": "1234567890",
        "image_width": 1280,
        "image_height": 720,
        "image_file_size": 102400,
        "image_type": "TYPE_JPG",
        "image_signature": "f4c8a3bc4deb305fb74cb08ed395b98c",
        "preview_url": "https://example.com/example.jpg"
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

1. **签名计算**: 必须使用原始文件计算 MD5 签名，签名必须为 32 字节小写十六进制字符串
   - Linux: `md5sum file | awk '{print $1}'`
   - macOS: `md5 -q file`

2. **文件大小**: 单个图片文件不能超过 10MB

3. **GIF限制**: GIF 动图播放时长不能超过 5 秒

4. **上传方式选择**: 
   - 小文件建议使用 UPLOAD_TYPE_BYTES
   - 大文件建议使用 UPLOAD_TYPE_FILE

5. **描述限制**: 不支持 @ 等特殊符号

6. **重复上传**: 相同签名的图片会返回已存在的 image_id

## 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查签名是否正确，文件格式是否支持 |
| 5 | 权限不足 | 确认 API Key 有效且有上传权限 |

## 最佳实践

1. **签名验证**: 上传前先本地计算签名，确保文件完整性
2. **错误重试**: 网络错误时可重试，使用相同签名
3. **描述规范**: 使用有意义的描述便于后续管理
4. **格式选择**: 根据用途选择合适的图片格式（JPG适合照片，PNG适合透明图）
