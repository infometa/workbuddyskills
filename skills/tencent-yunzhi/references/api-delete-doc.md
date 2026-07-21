# 删除文档 API

删除指定文档。

## 请求

```
DELETE /cgi-bin/v1/docs/{doc_id}
```

```bash
curl -s -X DELETE "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 请求参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | URL 路径 | ✅ | 要删除的文档 ID |

## 响应

**状态码**: `204 No Content`

> ⚠️ 删除操作不可恢复，调用前应二次确认。
