# 编辑文档 API

修改已存在文档的属性或内容。

## 请求

```
PATCH /cgi-bin/v1/docs/{doc_id}?target_type={type}
```

```bash
# 编辑富文本文档
curl -s -X PATCH "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}?target_type=document" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "doc",
      "attributes": {
        "title": "新标题",
        "content": "<p>新的正文内容</p>"
      }
    }
  }'

# 编辑文件类型文档的属性
curl -s -X PATCH "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}?target_type=file" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "doc",
      "attributes": {
        "name": "新文档名",
        "privilege_type": 1
      }
    }
  }'
```

## URL 参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | URL 路径 | ✅ | 文档 ID |
| `target_type` | URL 查询参数 | ❌ | `document`（富文本，默认）或 `file`（文件类型） |

## 富文本类型 (target_type=document) 可修改的属性

| 参数路径 | 类型 | 说明 |
|----------|------|------|
| `data.attributes.title` | string | 文档标题 |
| `data.attributes.content` | string | 正文内容（HTML） |
| `data.attributes.privilege_type` | int | 可见性：`0`=公开，`1`=部分人可见，`2`=仅创建者 |
| `data.attributes.allow_comment` | int | 是否允许评论：`0`=不允许，`1`=允许 |
| `data.attributes.source` | string | `original`=原创，`reship`=转载 |
| `data.attributes.reship_url` | string | 转载来源链接 |
| `data.attributes.signature` | string | 署名 |
| `data.attributes.picture_url` | string | 封面图片 URL |
| `data.attributes.only_team` | int | `0`=发布到公共知识库（需 category.id），`1`=仅团队（需 team.id） |
| `data.attributes.enable_watermark` | int | 页面文字水印：`0`=关，`1`=开 |
| `data.attributes.enable_copy_limit` | int | 禁止复制文字：`0`=关，`1`=开 |
| `data.attributes.enable_image_watermark` | int | 图片水印：`0`=关，`1`=开（文件类型不支持） |
| `data.attributes.tags` | array | 标签列表（最多 5 个） |

## 文件类型 (target_type=file) 可修改的属性

| 参数路径 | 类型 | 说明 |
|----------|------|------|
| `data.attributes.name` | string | 文档名 |
| `data.attributes.downloadable` | int | 是否允许下载：`0`=禁止，`1`=允许 |
| `data.attributes.privilege_type` | int | 可见性（同上） |
| `data.attributes.allow_comment` | int | 是否允许评论 |
| `data.attributes.signature` | string | 署名 |
| `data.attributes.picture_url` | string | 封面图片 URL |
| `data.attributes.only_team` | int | 同上 |
| `data.attributes.tags` | array | 标签列表 |

## 关联关系（两种类型通用）

| 参数路径 | 说明 |
|----------|------|
| `data.relationships.category.data` | 所属分类 `{"type":"category","id":"xxx"}` |
| `data.relationships.team.data` | 所属 K 吧/团队 `{"type":"team","id":"xxx"}` |
| `data.relationships.directory.data` | 所属目录 `{"type":"directory","id":"xxx"}` |
| `data.relationships.privilege.data` | 可见人员/部门列表（privilege_type=1 时使用） |
| `data.relationships.managers.data` | 协管人列表（最多 5 个，如已有则覆盖） |
| `data.relationships.attachments.data` | 附件列表（富文本类型） |

## 响应

**状态码**: `200 OK`，返回更新后的文档对象。

> ⚠️ 只需传入要修改的字段，缺省字段不会变化。`is_markdown` 属性创建后不可修改。
