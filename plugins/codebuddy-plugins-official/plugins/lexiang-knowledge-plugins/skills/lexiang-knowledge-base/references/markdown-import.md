# 场景：Markdown 导入知识库

将 Markdown 文件导入到云知知识库。

## 导入策略

### 方式一：文件上传（推荐）

- **优点**: 保留文件版本历史，后续更新只需上传新版本
- **适用**: 需要版本管理的文档
- **后续更新**: 使用 `file_id` 上传新版本

### 方式二：转换为 Block

- **优点**: 内容直接转换为可编辑的 Block 结构
- **缺点**: 后续更新需要操作 Block，较复杂
- **适用**: 需要在云知中直接编辑的文档

---

## 文件上传流程 (3步)

### Step 1: 申请上传凭证

```
MCP Tool: 云知.file_apply_upload
Arguments: {
  "parent_entry_id": "<父节点 entry_id>",
  "name": "document.md",
  "mime_type": "text/markdown",
  "size": 1234,
  "upload_type": "PRE_SIGNED_URL"
}
返回: { "session": { "session_id": "xxx", "upload_url": "https://..." } }
```

### Step 2: HTTP PUT 上传

```bash
curl -X PUT -H "Content-Type: text/markdown" \
  --data-binary @document.md \
  "$upload_url"
```

### Step 3: 确认上传

```
MCP Tool: 云知.file_commit_upload
Arguments: { "session_id": "xxx" }
返回: { "entry": { "id": "new_entry_id", ... } }
```

---

## 更新已有文件

更新时需要提供 `file_id`：

```
MCP Tool: 云知.file_apply_upload
Arguments: {
  "parent_entry_id": "<当前文件的 entry_id>",  // 注意：更新时填自己的 entry_id
  "name": "document.md",
  "mime_type": "text/markdown",
  "size": 5678,
  "file_id": "<describe_entry 返回的 target_id>",  // 必填
  "upload_type": "PRE_SIGNED_URL"
}
```

### 获取 file_id

```
MCP Tool: 云知.entry_describe_entry
Arguments: { "entry_id": "<文件条目 entry_id>" }
返回: { "entry": { "target_id": "<这就是 file_id>", ... } }
```

---

## 使用 import_content 转换为 Block

```
MCP Tool: 云知.entry_import_content
Arguments: {
  "parent_id": "<父节点 entry_id>",
  "name": "文档标题",
  "content": "# 标题\n\n正文内容...",
  "content_type": "markdown"
}
```

---

## 辅助脚本

```bash
# 单文件上传
python scripts/upload-files.py --files doc.md --entry-id <parent_entry_id>

# 文件夹批量上传（并行）
python scripts/upload-files.py --folder ./docs --entry-id <parent_entry_id> --parallel 5

# 生成上传计划
python scripts/upload-files.py --folder ./docs --entry-id <entry_id> --output plan.json --dry-run
```
