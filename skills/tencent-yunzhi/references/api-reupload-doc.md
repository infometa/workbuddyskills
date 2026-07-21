# 重新上传文档 API

替换已有文件类型文档的文件（需先通过 Step 1 + Step 2 上传新文件获取 `state`）。

## 请求

```
PATCH /cgi-bin/v1/docs/{doc_id}/re-upload?state={state}
```

```bash
curl -s -X PATCH "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}/re-upload?state=${state}" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 请求参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | URL 路径 | ✅ | 要替换文件的文档 ID |
| `state` | URL 查询参数 | ✅ | 新文件上传后获得的 state |

## 响应

**状态码**: `200 OK`

## 使用流程

1. 执行 Step 1（`cos-param`）获取新文件的上传签名
2. 执行 Step 2 上传新文件到 COS
3. 调用本接口 PATCH，传入 `state` 完成文件替换
