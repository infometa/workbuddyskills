# 场景：文件夹同步到知识库

将本地文件夹（如项目文档目录）增量同步到云知知识库，保持目录结构。

## 使用脚本

```bash
npx ts-node scripts/sync-folder.ts --local ./docs --entry-id <parent_entry_id> [--dry-run]
```

## 同步流程

1. **扫描本地目录**: 递归扫描文件和目录，计算文件 hash
2. **加载同步状态**: 从 `.yunzhi-sync-state.json` 读取上次同步状态
3. **计算差异**: 比对本地和远程，确定创建/更新操作
4. **生成 MCP 调用**: 输出需要执行的 MCP 调用序列

## 增量同步逻辑

| 场景 | 操作 |
|------|------|
| 新文件 | `apply_upload` + HTTP PUT + `commit_upload` |
| 文件内容变更 | 使用 `file_id` 更新文件版本 |
| 新目录 | `create_entry` (type=folder) |
| 文件删除 | 暂不自动删除，需手动处理 |

## 同步状态文件

位置: `.yunzhi-sync-state.json`

```json
{
  "version": "1.0.0",
  "lastSyncAt": "2026-01-22T10:00:00Z",
  "files": {
    "docs/readme.md": {
      "localPath": "docs/readme.md",
      "entryId": "abc123",
      "fileId": "file_xyz",
      "contentHash": "d41d8cd98f00b204e9800998ecf8427e",
      "lastModified": "2026-01-22T10:00:00Z",
      "syncedAt": "2026-01-22T10:00:00Z"
    }
  }
}
```

## MCP 调用示例

### 创建文件夹

```
MCP Tool: 云知.entry_create_entry
Arguments: {
  "parent_entry_id": "<父节点 entry_id>",
  "name": "子目录名",
  "entry_type": "folder"
}
```

### 上传文件 (3步)

```
Step 1: 云知.file_apply_upload
Arguments: {
  "parent_entry_id": "<父节点 entry_id>",
  "name": "document.md",
  "mime_type": "text/markdown",
  "size": 1234,
  "upload_type": "PRE_SIGNED_URL"
}

Step 2: HTTP PUT 上传到 upload_url

Step 3: 云知.file_commit_upload
Arguments: { "session_id": "xxx" }
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--local` | 本地目录路径 |
| `--entry-id` | 目标父节点 entry_id |
| `--space-id` | 知识库 ID（可选） |
| `--state-file` | 同步状态文件路径 |
| `--dry-run` | 仅生成计划不执行 |
