# 获取文档解析后的纯文本内容 API（v1，推荐）

获取 1.0 文档的「已解析正文」。无论是富文本文档还是 PPTX/DOCX/PDF 等文件类型文档，**都直接返回服务端解析好的 Markdown 文本**，包含图片描述与 OCR 结果，无需再走「下载文件 → 本地 markitdown 解析」流程。

> 🎯 **触发场景**：当用户提到「获取文档详细内容 / 解析内容 / 查看正文 / 读取文档内容 / 提取文字」且 URL 形如 `https://{prefix}.lexiangla.com/teams/{team_code}/docs/{doc_id}` 时，**默认且优先**用此接口。

> ⚠️ **不适用 v2 pages 文档**。若 URL 形如 `/pages/{entry_id}`，请使用 MCP 工具 `entry_describe_ai_parse_content(entry_id)`，详见 `modules/search.md`。

---

## 请求

```
GET /cgi-bin/v1/docs/{doc_id}/parsed-content
```

```bash
curl -s -X GET "${API_HOST}/cgi-bin/v1/docs/${DOC_ID}/parsed-content" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 请求参数

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | URL 路径 | ✅ | 文档 ID（32 位十六进制） |

ID 提取规则：从 `https://{prefix}.lexiangla.com/teams/{team_code}/docs/{doc_id}` 用正则 `/docs/([a-f0-9]{32})` 提取。

## 响应结构

```json
{
  "data": {
    "type": "doc",
    "id": "0ca8feca37de11f1a6ca123436be13c9",
    "attributes": {
      "name": "AI问答痛点场景",
      "created_at": "2026-04-14 16:43:45",
      "updated_at": "2026-04-14 16:43:45",
      "parsed_content": "# 标题\n\n正文 Markdown ...\n\n[IMAGE]\n图片链接：/assets/xxx\n图片标题：xxx\n图片描述：xxx\n图片OCR结果：xxx\n[/IMAGE]"
    },
    "links": {
      "platform": "https://csig.lexiangla.com/teams/k100684/docs/xxx"
    },
    "relationships": {
      "target": { "data": { "type": "file", "id": "xxx" } },
      "team":   { "data": { "type": "team", "id": "xxx" } }
    }
  },
  "included": [
    { "type": "file", "id": "xxx", "attributes": { "name": "xxx", "file_type": "pptx" } },
    { "type": "team", "id": "xxx", "attributes": { "code": "k100684", "name": "xxx" } }
  ]
}
```

**关键字段**：

| 字段 | 说明 |
|------|------|
| `data.attributes.parsed_content` | **主结果**：解析后的 Markdown 纯文本 |
| `data.attributes.name` | 文档标题 |
| `data.attributes.created_at` / `updated_at` | 时间信息 |
| `data.links.platform` | 文档在乐享上的访问链接 |
| `included[type=file].attributes.file_type` | 原始文件类型（pptx/docx/pdf/...） |
| `included[type=team].attributes.code` | 团队 code（如 k100684） |

## parsed_content 中的图片块格式

图片会被服务端解析并包裹为：

```
[IMAGE]
图片链接：/assets/{asset_id}
图片标题：xxx
图片描述：xxx（多模态视觉描述，便于理解图表/截图含义）
图片OCR结果：xxx（图中文字识别结果，含表格、坐标数据等）
[/IMAGE]
```

需要原图时，把 `图片链接` 拼成完整 URL：`https://{domain}{path}`，或调用 `references/api-download-asset.md` 下载。

## 与旧接口对比

| 场景 | 旧方式（GET /docs/{id}） | 新方式（推荐） |
|------|--------------------------|----------------|
| 富文本文档 | `included[type=document].md_content` | `data.attributes.parsed_content` |
| PPTX/DOCX/PDF | 拿 `links.download` 下载 → markitdown 解析 | 直接拿 `parsed_content` |
| 图片说明 | 仅 `<img>` 标签或 alt | 含图片描述 + OCR 结果 |
| 调用次数 | 1 次 API + 1 次下载 + 本地解析 | **1 次 API** |

**优先使用本接口**。仅当：
- 需要原始 HTML（保留 block 结构、自定义样式）→ 用 `GET /docs/{id}` 取 `content`
- 需要原始文件下载（pptx 二进制本身）→ 用 `GET /docs/{id}` 取 `links.download`
- 本接口异常时 → 降级到 `GET /docs/{id}` + markitdown

## 端到端示例

```bash
# 从 ~/.workbuddy/mcp.json 中读取 token
TOKEN=$(cat ~/.workbuddy/mcp.json | python3 -c "import json,sys; print(json.load(sys.stdin)['mcpServers']['lexiang']['headers']['Authorization'].replace('Bearer ',''))")

DOC_ID=0ca8feca37de11f1a6ca123436be13c9
curl -sS "https://lxapi.lexiangla.com/cgi-bin/v1/docs/${DOC_ID}/parsed-content" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['attributes']['parsed_content'])"
```

## 批量获取示例

```python
import json, urllib.request, urllib.parse

TOKEN = open('/path/to/token').read().strip()
DOC_IDS = ['0ca8feca37de11f1a6ca123436be13c9', '...']
API = 'https://lxapi.lexiangla.com'

results = []
for did in DOC_IDS:
    req = urllib.request.Request(
        f'{API}/cgi-bin/v1/docs/{did}/parsed-content',
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    results.append({
        'id': did,
        'name': data['data']['attributes']['name'],
        'content': data['data']['attributes']['parsed_content'],
    })

with open('all-docs.md', 'w') as f:
    for r in results:
        f.write(f"# {r['name']}\n\n{r['content']}\n\n---\n\n")
```

## 错误码

| 状态 | 处理 |
|------|------|
| 401 | Token 过期 → 引导访问 `https://lexiangla.com/mcp?company_from=CSIG` 续期 |
| 404 | 文档不存在 / 无权限 / 误用 v2 entry_id |
| 200 但 `parsed_content` 为空 | 文档刚上传尚未解析完成（异步任务），稍后重试或降级到 `GET /docs/{id}` |
