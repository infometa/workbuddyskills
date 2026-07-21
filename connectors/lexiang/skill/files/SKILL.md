---
name: lexiang-files
description: "乐享知识库文件上传与下载管理。当用户提到「乐享」「知识库」「lexiang」并包含文件上传/下载意图时使用。典型触发：「上传文件到乐享」「传个 PDF」「把这个文件放到知识库」「上传附件」「同步文件夹」「传文件到乐享」「下载这个文件」「帮我把本地的 Word/Excel/图片上传到乐享」。适用于 PDF、Word、Excel、图片、压缩包等二进制文件的上传和下载场景。支持三步文件上传（申请→PUT上传→确认）、文件详情查询、文件下载。注意：创建 Markdown/HTML 文本文档请使用 writer/SKILL.md。"
---

# 乐享文件上传管理

> **基础知识**：数据模型、URL 规则、写入安全规则见 `base/SKILL.md`。
> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `setup/SKILL.md`。
> **遇到 401 错误**：不要重试，读取 `setup/SKILL.md` 引导用户续期（点击续期按钮即可恢复，无需重新配置）。

---

## ⚠️ 前置检查：确认产品版本

**每次执行文件操作前**，先调用 `whoami()` 检查 `sub_server_type`：
- `v2` → 继续使用本 skill
- `v1` → **停止，提示用户加载 `lexiang-v1-docs`（文件上传）或 `lexiang-v1-assets`（图片上传）**
- `v1v2` → 如果用户明确说了「乐享社区」→ 提示切换对应 v1 skill；否则继续使用本 skill

---

## 工具概览

### 📎 文件管理
- `file_apply_upload` — 申请文件上传（返回 upload_url 和 session_id）
- `file_commit_upload` — 确认上传完成
- `file_describe_file` — 获取文件详情
- `file_download_file` — 下载文件

---

## 文件上传完整流程（三步）

> ⚠️ **必须严格按顺序执行以下三步，缺一不可。**

### Step 1: 申请上传凭证（MCP 调用）

```
MCP Tool: file_apply_upload
Arguments: {
  "parent_entry_id": "<目标目录的 entry_id>",
  "name": "example.pdf",
  "size": 12345,
  "mime_type": "application/pdf",
  "upload_type": "PRE_SIGNED_URL"
}
```

**必填参数说明**：

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| `parent_entry_id` | 目标目录的 entry_id | 从知识库 URL 或 `entry_list_entries` 获取 |
| `name` | 文件名（含扩展名） | 本地文件名 |
| `size` | 文件大小（**字节数，必填**） | 通过 `wc -c <文件>` 或 `stat -f%z <文件>` 获取 |
| `mime_type` | MIME 类型 | 见下方常见类型表 |
| `upload_type` | 固定填 `"PRE_SIGNED_URL"` | — |

**返回值**（关键字段）：
```json
{
  "session": {
    "session_id": "abc123",
    "upload_url": "https://cos.example.com/upload?sign=xxx"
  }
}
```

### Step 2: HTTP PUT 上传文件内容（curl 命令，非 MCP）

> ⚠️ **这一步不是 MCP 调用，必须用 curl 命令执行 HTTP PUT 请求。**

```bash
curl -X PUT \
  -H "Content-Type: <mime_type>" \
  --data-binary "@<本地文件路径>" \
  "<Step 1 返回的 upload_url>"
```

**curl 参数说明**：
- `-X PUT`：必须是 PUT 方法（不是 POST）
- `--data-binary`：必须用 `--data-binary`（不是 `-d` 或 `--data`），保持二进制完整性
- `@文件路径`：`@` 前缀表示读取文件内容，路径必须用绝对路径
- `Content-Type`：必须与 Step 1 中的 `mime_type` 一致

**成功标志**：curl 返回 HTTP 200 或空响应（无报错）

### Step 3: 确认上传完成（MCP 调用）

```
MCP Tool: file_commit_upload
Arguments: {
  "session_id": "<Step 1 返回的 session_id>"
}
```

**返回值**：包含新文件的 `entry_id`，上传完成。按 `base/SKILL.md` 中的**链接生成规则**拼接访问链接返回给用户。

> `{company_from}` 优先从 mcp.json `url` 提取，其次取 `whoami().company.code`。

---

## 常用 MIME 类型速查

| 文件类型 | 扩展名 | mime_type |
|----------|--------|-----------|
| PDF | .pdf | `application/pdf` |
| Word | .docx | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | .xlsx | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPT | .pptx | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| 图片 PNG | .png | `image/png` |
| 图片 JPG | .jpg/.jpeg | `image/jpeg` |
| Markdown | .md | `text/markdown` |
| 文本 | .txt | `text/plain` |
| ZIP | .zip | `application/zip` |
| JSON | .json | `application/json` |

---

## 更新已有文件

更新文件需要额外的 `file_id` 参数，且 `parent_entry_id` 填**文件自身的 entry_id**（不是父目录）。

1. 先获取 file_id：`entry_describe_entry(entry_id=<文件的 entry_id>)` → 返回值中 `target_id` 就是 `file_id`
2. 调用 `file_apply_upload` 时额外传入 `file_id` 参数
3. 同样执行 Step 2（curl PUT）和 Step 3（commit_upload）

---

## ⚠️ 常见错误

| 错误 | 原因 | 修复 |
|------|------|------|
| apply_upload 失败 | 缺少 `size` 参数 | **必须传文件字节数** |
| curl PUT 返回 403 | upload_url 过期或格式错误 | 重新执行 Step 1 获取新 URL |
| curl PUT 上传 0 字节 | 用了 `-d` 而不是 `--data-binary` | 改用 `--data-binary "@文件"` |
| commit 后文件为空 | 跳过了 Step 2 | 必须先 curl PUT 上传文件内容 |
| 更新文件变成新建 | 没传 `file_id` | 更新时必须传 `file_id` |
| 更新时 parent_entry_id 错误 | 填了父目录 ID | 更新时填**文件自身的 entry_id** |
