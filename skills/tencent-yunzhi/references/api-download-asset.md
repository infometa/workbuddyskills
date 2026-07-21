# 下载图片 API

获取指定图片资源的临时下载链接。

## 请求

```
GET /cgi-bin/v1/assets/{asset_id}
```

```bash
curl -s -X GET "${API_HOST}/cgi-bin/v1/assets/${ASSET_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 请求参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `asset_id` | URL 路径 | ✅ | 资源 ID |

## asset_id 提取

从乐享平台的图片 URL 中提取 `asset_id`：

```
https://lexiangla.com/assets/68975160a41211ebbcc38ead0db1c463
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                              这部分就是 asset_id
```

也可以从上传接口的返回值中直接获取 `asset_id`。

## 响应

**状态码**: `200 OK`

```json
{
  "url": "https://file.lexiang-asset.com/xxxx/assets/2021/06/xxx.jpg?sign=SIGN",
  "mime_type": "image/jpeg"
}
```

**返回字段**：

| 字段 | 说明 |
|------|------|
| `url` | 带临时签名的下载链接（**有效期 3 分钟**） |
| `mime_type` | MIME 类型（如 `image/jpeg`、`image/png`） |

> ⚠️ **重要**：下载链接有效期仅 3 分钟！请获取后立即下载，切勿将此链接用于前端展示。

## 下载到本地

```bash
# 获取下载链接
RESULT=$(curl -s -X GET "${API_HOST}/cgi-bin/v1/assets/${ASSET_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

DOWNLOAD_URL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

# 下载文件
curl -s -o "image.jpg" "${DOWNLOAD_URL}"
echo "✅ 图片已下载: image.jpg"
```
