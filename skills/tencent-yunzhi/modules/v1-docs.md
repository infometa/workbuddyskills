# 1.0 文档管理（REST API）

> 通过 1.0 REST API 进行文档 CRUD：创建/查询/编辑/上传/重新上传/删除。

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
| 创建文档 | POST | `/cgi-bin/v1/docs` | `references/api-create-doc.md` |
| 上传文档 | POST | `/cgi-bin/v1/docs/upload?state={state}` | `references/api-upload-doc.md` |
| 重新上传 | PATCH | `/cgi-bin/v1/docs/{doc_id}/re-upload?state={state}` | `references/api-reupload-doc.md` |
| 编辑文档 | PATCH | `/cgi-bin/v1/docs/{doc_id}` | `references/api-edit-doc.md` |
| 删除文档 | DELETE | `/cgi-bin/v1/docs/{doc_id}` | `references/api-delete-doc.md` |
| 获取文档（原始） | GET | `/cgi-bin/v1/docs/{doc_id}` | `references/api-get-doc.md` |
| **获取解析内容（推荐）** | GET | `/cgi-bin/v1/docs/{doc_id}/parsed-content` | `references/api-get-doc-parsed-content.md` |
| 文档列表 | GET | `/cgi-bin/v1/staffs/x/app-data?module_type=doc&team_id={team_uuid}` | 见下方说明 |

---

## 查询文档列表（按团队空间/目录）

**端点**：`GET /cgi-bin/v1/staffs/x/app-data`

**认证**：使用 Skill 的个人 Token（即 `mcp.json` 中 `lexiang` 服务配置的 `Authorization: Bearer lxmcp_xxx`）。
- Header 方式：`Authorization: Bearer lxmcp_xxx`
- Query 参数方式：`access_token=lxmcp_xxx`

**参数**：

| 参数 | 必填 | 说明 |
|------|------|------|
| `module_type` | ✅ | 固定传 `doc` |
| `team_id` | ✅ | 团队空间 UUID。如果用户给的是团队 code（如 `k100482`），需先转换，见下方 |
| `directory_id` | ❌ | 目录节点 ID（对应 URL 中的 `node` 参数）。**查询目录下文档时必须与 `team_id` 同时传** |
| `page_token` | ❌ | 分页 token（从上一次返回的 `meta.page_token` 获取，为空字符串表示无下一页） |

### 团队 code → UUID 转换

当用户提供的是团队 code（格式为 `k10XXXX`，如 `k100482`）而非 UUID 时，需要先调用以下接口获取 `team_id`：

```
GET https://lxapi.lexiangla.com/cgi-bin/v1/teams/{team_code}?access_token=lxmcp_xxx
```

返回的 `data.id` 即为团队 UUID，用于后续 `team_id` 参数。

**示例**：
```bash
curl -s "https://lxapi.lexiangla.com/cgi-bin/v1/teams/k100482?access_token=lxmcp_xxx"
# 返回 → data.id = "ec5192ac359511ed9b9202a663457286"
```

> ⚠️ **重要**：
> - `team_id` 必须用 **UUID**（如 `ec5192ac359511ed9b9202a663457286`），不能用团队 code（如 `k100482`）
> - 查询特定目录时，`team_id` + `directory_id` **必须同时传**。只传 `directory_id` 会返回异常大范围结果
> - 只传 `team_id` 则返回该团队下所有文档（不按目录过滤）

**返回结构**：

```json
{
  "data": [
    {
      "type": "doc",
      "id": "文档UUID",
      "attributes": {
        "name": "文档名称",
        "read_count": 0,
        "comment_count": 0,
        "created_at": "2026-04-17 17:35:44",
        "edited_at": "2026-04-17 17:35:44",
        "recommended_at": null,
        "is_shelved": true,
        "only_team": null,
        "tags": []
      },
      "links": {
        "platform": "https://csig.lexiangla.com/docs/{doc_id}"
      }
    }
  ],
  "meta": {
    "page_token": "eyJ..."
  }
}
```

**分页**：每次默认返回 20 条，通过 `page_token` 翻页。

---

## 从链接上传文件

### URL 解析

匹配：`/teams/{team_code}(/docs)?`
- `team_code`：路径中 `/teams/` 后的段（如 `k100684`）
- `node`（可选）：查询参数，目标文件夹 ID
- **团队 ID 转换**：`team_describe_team(team_id="k100684")` → 获取 UUID

### 三步上传

**Step 1: 获取 COS 签名**

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs/cos-param" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"filename": "example.pptx", "type": "file"}'
```

返回：`accessUrl`、`authorization`、`securityToken`、`state`

**Step 2: 上传到 COS**

```bash
curl -s -X PUT "${accessUrl}" \
  -H "Authorization: ${authorization}" \
  -H "x-cos-security-token: ${securityToken}" \
  -H "Content-Type: application/octet-stream" \
  -H "Content-Disposition: attachment; filename*=utf-8''${encoded_filename}" \
  --data-binary "@/path/to/file"
```

> Step 2 的 Authorization 是 COS 签名（`q-sign-algorithm=...`），**不是** Bearer Token。

**Step 3: 创建文档实体**

```bash
curl -s -X POST "${API_HOST}/cgi-bin/v1/docs/upload?state=${state}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "doc",
      "attributes": {"name": "文档标题", "downloadable": 1, "privilege_type": 0},
      "relationships": {
        "team": {"data": {"type": "team", "id": "团队UUID"}},
        "directory": {"data": {"type": "directory", "id": "目录节点ID"}}
      }
    }
  }'
```

> ⚠️ `team.id` 必须用 **UUID**（通过 `team_describe_team` 获取），不能用 URL 中的 code。

---

## 查询文档内容

### ⭐ 推荐方式：解析内容接口（一键拿 Markdown）

**端点**：`GET /cgi-bin/v1/docs/{doc_id}/parsed-content`

```bash
curl -s "${API_HOST}/cgi-bin/v1/docs/{doc_id}/parsed-content" \
  -H "Authorization: Bearer ${TOKEN}"
```

**关键字段**：`data.attributes.parsed_content` → 已解析的 Markdown 纯文本

**优势**：
- 富文本 / PPTX / DOCX / PDF **统一返回 Markdown**，无需区分类型
- 图片自动转换为 `[IMAGE] ... [/IMAGE]` 块，包含图片描述与 OCR 结果
- **一次调用搞定**，不用再下载文件、不用再跑 markitdown
- 详细字段说明见 `references/api-get-doc-parsed-content.md`

**当用户提到"获取/查看/读取文档详细内容/正文/解析内容"且 URL 是 `/teams/.../docs/{doc_id}` 时，直接用此接口。**

### 兜底方式：原始接口（需要 HTML 结构 / 原文件下载时用）

**端点**：`GET /cgi-bin/v1/docs/{doc_id}`

**仅在以下场景使用**：
- 需要保留原始 HTML 结构（block 标签、自定义样式等）
- 需要下载文件二进制（如 pptx 原文件）
- `parsed-content` 接口异常时降级

#### 判断文档类型

通过响应中 `included` 数组的 `type` 字段区分：

| `included` 中包含 | 文档类型 | 内容获取方式 |
|-------------------|---------|-------------|
| `type: "document"` | **富文本** | 直接读取 `attributes.content`（HTML）或 `attributes.md_content`（Markdown） |
| `type: "file"` | **文件** | 通过 `links.download` 下载后解析 |

#### 富文本文档

```bash
curl -s "https://lxapi.lexiangla.com/cgi-bin/v1/docs/{doc_id}?access_token=lxmcp_xxx"
```

**提取内容**：
- 优先使用 `included[type=document].attributes.md_content`（Markdown 格式）
- 如果 md_content 为空，使用 `included[type=document].attributes.content`（HTML 格式，需去标签）

#### 文件类型文档

文件类型的文档正文不在此接口响应中，需要下载文件后本地解析。

**Step 1: 获取下载链接**

```bash
curl -s "https://lxapi.lexiangla.com/cgi-bin/v1/docs/{doc_id}?access_token=lxmcp_xxx"
# 从响应中提取: included[type=file].links.download
# 下载链接有效期 3 分钟，过期需重新查询
```

**Step 2: 下载文件**

```bash
curl -s -o "{filename}.{ext}" "{download_url}"
# 文件扩展名从 download URL 路径中提取（.pptx / .docx / .pdf 等）
```

**Step 3: 解析文件内容**

```bash
# 使用 markitdown 提取文字（支持 pptx / docx / pdf）
python3 -m markitdown "{filename}.{ext}"
```

| 文件格式 | 解析能力 |
|---------|---------|
| `.pptx` | ✅ 可提取全部幻灯片文字和表格 |
| `.docx` | ✅ 可提取全部正文、表格、列表 |
| `.pdf` | ⚠️ 文字型 PDF 可提取；纯图片扫描件 PDF 无法提取 |
| `.xlsx` / `.xls` / `.csv` | ✅ 可提取表格数据 |

> ✅ **已替代**：服务端 `parsed-content` 接口已上线，文件类内容获取应优先走 `GET /cgi-bin/v1/docs/{doc_id}/parsed-content`，本节流程仅作兜底/原始文件下载场景使用。

### 内容获取决策流程

```
用户请求：获取 /teams/k100482/docs/{doc_id} 下文档的内容

✅ 首选：GET /cgi-bin/v1/docs/{doc_id}/parsed-content
        → data.attributes.parsed_content（已解析 Markdown）

🔻 兜底（仅在需要原始 HTML 或下载原文件时）：
        GET /cgi-bin/v1/docs/{doc_id}
        ├─ included[type=document] → 读取 content / md_content
        └─ included[type=file]     → links.download 下载 + markitdown 解析
```

> ⚠️ 不要尝试用 v2 MCP `entry_describe_ai_parse_content` 处理 v1 doc_id，会失败。v1 文档统一走 `parsed-content` 接口。

## 编辑文档

`PATCH /cgi-bin/v1/docs/{doc_id}?target_type={type}`
- 富文本：`target_type=document`（默认）
- 文件：`target_type=file`
- 只传需要修改的字段

## 删除文档

⚠️ 不可恢复，需二次确认。`DELETE /cgi-bin/v1/docs/{doc_id}`

---

## 支持的文件格式

doc/docx/ppt/pptx/xlsx/xls/pdf/csv

---

## 常见错误

| 错误 | 修复 |
|------|------|
| team_id 无效 | 用 UUID，不用 code |
| Step 2 返回 403 | COS 签名过期 → 重新 Step 1 |
| 上传 0 字节 | 用 `--data-binary`，不用 `-d` |
| 格式不支持 | 仅 doc/docx/ppt/pptx/xlsx/xls/pdf/csv |
| 下载链接过期 | 有效期 3 分钟 → 重新查询 |

---

## 辅助脚本

`scripts/docs-v1.py` — 命令行文档管理工具
