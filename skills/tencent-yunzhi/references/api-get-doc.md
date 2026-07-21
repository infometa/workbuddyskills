# 获取单个文档 API

查询指定文档的详细信息（原始字段）。

> 💡 **若只是想拿到正文内容**（无论富文本还是 PPTX/DOCX/PDF），**请优先使用 `references/api-get-doc-parsed-content.md`**（`GET /cgi-bin/v1/docs/{doc_id}/parsed-content`），一次调用直接返回已解析的 Markdown，无需再下载文件本地解析。本接口仅在需要原始 HTML 结构 / 下载原始文件二进制时使用。

## 请求

```
GET /cgi-bin/v1/docs/{doc_id}
```

```bash
curl -s -X GET "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 请求参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | URL 路径 | ✅ | 文档 ID（32 位十六进制字符串） |

## 链接识别与 ID 提取

当用户发送乐享文档链接时，自动提取文档 ID：

| 格式 | 示例 | ID 提取规则 |
|------|------|-------------|
| 标准链接 | `https://lexiangla.com/docs/54907cb434ae11f1858b42a2dae6d1f7` | `docs/` 后面的字符串 |
| 团队链接 | `https://lexiangla.com/teams/k101145/docs/9a723982349211f1bb626ee3ab4b9e54` | `docs/` 后面的字符串 |
| 带查询参数 | `https://lexiangla.com/docs/xxx?company_from=yyy` | `docs/` 到 `?` 之间的字符串 |
| 带域名前缀 | `https://{prefix}.lexiangla.com/docs/xxx` | 同上 |

**ID 提取正则**：

```
/docs/([a-f0-9]{32})
```

## 响应结构

### 判断文档类型

通过 `included` 数组中的对象类型判断：

| `included` 中包含 | 文档类型 | 处理方式 |
|-------------------|---------|---------| 
| `type: "document"` | 富文本文档 | 直接读取 `content` 字段 |
| `type: "file"` | 文件类型文档 | 通过 `links.download` 下载 |

### 富文本文档响应

```json
{
  "data": {
    "type": "doc",
    "id": "7c6cca86484411ec922f960346af4b7a",
    "attributes": {
      "name": "文档标题",
      "privilege_type": 1,
      "read_count": 2,
      "comment_count": 1,
      "created_at": "2021-11-18 15:52:32",
      "updated_at": "2021-11-18 15:52:39",
      "tags": ["标签1"]
    }
  },
  "included": [
    {
      "type": "document",
      "attributes": {
        "content": "<p>HTML 正文</p>",
        "md_content": "Markdown 正文（如果有）"
      }
    }
  ]
}
```

**关键字段**：
- `included[type=document].attributes.content` → HTML 内容
- `included[type=document].attributes.md_content` → Markdown 内容（优先使用）

### 文件类型文档响应

```json
{
  "data": {
    "type": "doc",
    "id": "xxx",
    "attributes": { "name": "报告.pdf" }
  },
  "included": [
    {
      "type": "file",
      "attributes": {
        "name": "report.pdf",
        "size": 1048576,
        "mime_type": "application/pdf"
      },
      "links": {
        "download": "https://xxx.cos.ap-shanghai.myqcloud.com/path/to/file?sign=xxx"
      }
    }
  ]
}
```

**关键字段**：
- `included[type=file].links.download` → 下载链接（**有效期 3 分钟**）
- `included[type=file].attributes.name` → 文件名
- `included[type=file].attributes.size` → 文件大小（字节）
