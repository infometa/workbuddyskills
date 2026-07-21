# 1.0 图片管理（REST API）

> 通过 1.0 REST API 上传和下载图片资源。

---

## 环境

```
API_HOST = https://lxapi.lexiangla.com
Authorization: Bearer lxmcp_xxx
```

---

## 接口总览

| 接口 | 方法 | 路径 | 详细文档 |
|------|------|------|----------|
| 上传图片 | POST | `/cgi-bin/v1/assets` | `references/api-upload-asset.md` |
| 下载图片 | GET | `/cgi-bin/v1/assets/{asset_id}` | `references/api-download-asset.md` |

---

## 上传图片

支持格式：jpg/jpeg/png/gif

```bash
curl -X POST "${API_HOST}/cgi-bin/v1/assets" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "type=image" \
  -F "data=@/path/to/photo.jpg" \
  -F "is_public=1"
```

返回 `asset_id` 和 URL。设 `is_public=1` 获取公共访问地址。

## 下载图片

```bash
curl -s "${API_HOST}/cgi-bin/v1/assets/${asset_id}" \
  -H "Authorization: Bearer ${TOKEN}"
```

返回临时下载链接（有效期 3 分钟）。

## 在文档中插入图片

1. 先上传图片获取 `public_url`（`is_public=1`）
2. 在创建/编辑文档时将 `public_url` 嵌入 HTML content

---

## 注意事项

1. 上传使用 `multipart/form-data`（`-F` 参数）
2. 下载链接有效期仅 3 分钟
3. `is_public=1` 才返回公共 URL

---

## 辅助脚本

`scripts/assets-v1.py` — 命令行图片上传/下载工具
