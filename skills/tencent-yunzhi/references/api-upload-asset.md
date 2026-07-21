# 上传图片 API

将图片文件上传到乐享服务器，获取资源 ID 和访问 URL。

## 请求

```
POST /cgi-bin/v1/assets
```

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/assets" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "type=image" \
  -F "file=@/path/to/image.jpg" \
  -F "is_public=1"
```

> ⚠️ 注意：此接口使用 `multipart/form-data` 格式上传，不是 JSON。

## 支持的图片格式

| 格式 | 扩展名 | MIME Type |
|------|--------|-----------|
| JPEG | .jpg / .jpeg | `image/jpeg` |
| PNG | .png | `image/png` |
| GIF | .gif | `image/gif` |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 资源类型，上传图片填 `"image"`（也支持 `"audio"`） |
| `file` | file | ✅ | 要上传的图片文件 |
| `is_public` | int | ❌ | 是否获取公共地址：`0`=不需要（默认），`1`=需要 |

## 响应

**状态码**: `200 OK`

```json
{
  "asset_id": "68975160a41211ebbcc38ead0db1c463",
  "url": "https://lexiangla.com/assets/68975160a41211ebbcc38ead0db1c463",
  "public_url": "https://image-pub.lexiang-asset.com/company_xxx/assets/2021/04/xxx.jpg"
}
```

**返回字段**：

| 字段 | 说明 |
|------|------|
| `asset_id` | 资源 ID（32 位十六进制字符串） |
| `url` | 乐享平台内部访问地址（格式：`https://lexiangla.com/assets/{asset_id}`） |
| `public_url` | 公共访问地址（仅 `is_public=1` 时返回，可用于外部引用） |

## 使用场景

上传图片后，可以在创建富文本文档时引用：

```bash
# 1. 上传图片
RESULT=$(curl -s -X POST "${API_HOST}/cgi-bin/v1/assets" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "type=image" \
  -F "file=@photo.jpg" \
  -F "is_public=1")

PUBLIC_URL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['public_url'])")

# 2. 在创建文档时引用图片
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"data\": {
      \"type\": \"doc\",
      \"attributes\": {
        \"title\": \"带图片的文档\",
        \"content\": \"<p>正文内容</p><img src='${PUBLIC_URL}' />\",
        \"is_markdown\": 0,
        \"privilege_type\": 2
      }
    }
  }"
```
