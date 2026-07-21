# 创建文档 API

创建一个新的富文本文档。

## 请求

```
POST /cgi-bin/v1/docs
```

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "doc",
      "attributes": {
        "title": "文档标题",
        "content": "<h1>正文内容</h1><p>支持 HTML</p>",
        "is_markdown": 0,
        "privilege_type": 1,
        "allow_comment": 1,
        "tags": ["标签1", "标签2"]
      }
    }
  }'
```

## 请求参数

| 参数路径 | 类型 | 必填 | 说明 |
|----------|------|------|------|
| `data.type` | string | ✅ | 固定填 `"doc"` |
| `data.attributes.title` | string | ✅ | 文档标题 |
| `data.attributes.content` | string | ✅ | 正文内容（HTML 或 Markdown） |
| `data.attributes.is_markdown` | int | ❌ | `0`=HTML（默认），`1`=Markdown |
| `data.attributes.privilege_type` | int | ❌ | 可见性：`0`=公开，`1`=部分人可见，`2`=仅创建者（默认） |
| `data.attributes.allow_comment` | int | ❌ | 是否允许评论：`0`=不允许，`1`=允许 |
| `data.attributes.source` | string | ❌ | 来源：`"reship"` 表示转载 |
| `data.attributes.reship_url` | string | ❌ | 转载原始链接 |
| `data.attributes.signature` | string | ❌ | 签名/作者 |
| `data.attributes.picture_url` | string | ❌ | 封面图片 URL |
| `data.attributes.only_team` | int | ❌ | `0`=发布到公共知识库，`1`=仅发到团队（需设置 team.id） |
| `data.attributes.enable_watermark` | int | ❌ | 是否启用水印 |
| `data.attributes.enable_copy_limit` | int | ❌ | 是否限制复制 |
| `data.attributes.tags` | array | ❌ | 标签列表 |
| `data.relationships.category.data` | object | ❌ | 所属分类 `{"type":"category","id":"xxx"}` |
| `data.relationships.team.data` | object | ❌ | 所属团队 `{"type":"team","id":"xxx"}` |
| `data.relationships.directory.data` | object | ❌ | 所属目录 `{"type":"directory","id":"xxx"}` |
| `data.relationships.privilege.data` | array | ❌ | 可见人员/部门列表（privilege_type=1 时使用） |
| `data.relationships.managers.data` | array | ❌ | 协管人列表（最多 5 个） |

## 响应

**状态码**: `201 Created`

返回创建的文档对象，包含 `data.id`（文档 ID）等信息。
