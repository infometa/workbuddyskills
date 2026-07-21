# 上传文档 API（三步）

上传文件类型文档到乐享（如 PDF、Word、PPT、Excel、CSV）。

> ⚠️ **必须严格按顺序执行以下三步，缺一不可。**

## 支持的文件格式

| 格式 | 扩展名 |
|------|--------|
| PDF | .pdf |
| Word | .doc / .docx |
| PowerPoint | .ppt / .pptx |
| Excel | .xls / .xlsx |
| CSV | .csv |

## Step 1: 获取资源签名

```
POST /cgi-bin/v1/docs/cos-param
```

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs/cos-param" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"filename": "example.pdf", "type": "file"}'
```

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | string | ✅ | 文件名（含扩展名） |
| `type` | string | ✅ | 固定填 `"file"` |

**返回值**（关键字段）：

```json
{
  "data": {
    "attributes": {
      "accessUrl": "https://xxx.cos.ap-shanghai.myqcloud.com/...",
      "authorization": "q-sign-algorithm=sha1&q-ak=xxx&...",
      "securityToken": "xxx",
      "state": "uuid-state-string"
    }
  }
}
```

**需提取**：`accessUrl`、`authorization`、`securityToken`、`state`

## Step 2: 上传文件到腾讯云 COS

```bash
curl -s -X PUT "${accessUrl}" \
  -H "Authorization: ${authorization}" \
  -H "x-cos-security-token: ${securityToken}" \
  -H "Content-Type: application/octet-stream" \
  -H "Content-Disposition: attachment; filename*=utf-8''${filename}; filename=${filename}" \
  --data-binary "@/path/to/local/file"
```

**重要**：
- 必须使用 `--data-binary`（不是 `-d` 或 `--data`），保持二进制完整性
- Step 2 的 `Authorization` 是 COS 签名（`q-sign-algorithm=...`），**不是** Bearer token
- 成功标志：HTTP 200 + 返回含 `ETag` 的响应头

## Step 3: 创建文档实体

```
POST /cgi-bin/v1/docs/upload?state={state}
```

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs/upload?state=${state}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "doc",
      "attributes": {
        "name": "文档标题",
        "downloadable": 1,
        "privilege_type": 2
      }
    }
  }'
```

**请求参数**：

| 参数路径 | 类型 | 必填 | 说明 |
|----------|------|------|------|
| `state`（URL 参数） | string | ✅ | Step 1 返回的 `state` |
| `data.type` | string | ✅ | 固定填 `"doc"` |
| `data.attributes.name` | string | ✅ | 文档名称 |
| `data.attributes.downloadable` | int | ❌ | `1`=允许下载（默认），`0`=禁止 |
| `data.attributes.privilege_type` | int | ❌ | 可见性：`0`=公开，`1`=部分人，`2`=仅自己 |
| `data.attributes.only_team` | int | ❌ | `0`=公共，`1`=仅团队 |
| `data.attributes.tags` | array | ❌ | 标签列表 |
| `data.relationships.category.data` | object | ❌ | 所属分类 |
| `data.relationships.team.data` | object | ❌ | 所属团队 |
| `data.relationships.directory.data` | object | ❌ | 所属目录 |
| `data.relationships.privilege.data` | array | ❌ | 可见人员/部门列表 |
| `data.relationships.managers.data` | array | ❌ | 协管人列表 |

**响应**: `201 Created`，返回文档对象（含 `data.id`）。
