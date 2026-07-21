# 文件管理（2.0 MCP）

> 文件三步上传/下载/更新，适用于 PDF、Word、Excel、PPT、图片、压缩包等二进制文件。**上传失败必须落本地降级**。

---

## 工具概览

- `file_apply_upload` — 申请上传凭证
- `file_commit_upload` — 确认上传完成
- `file_describe_file` — 获取文件详情
- `file_download_file` — 下载文件

---

## URL → parent_entry_id 路由

| URL 模式 | 处理方式 |
|----------|---------|
| `/t/{team_id}/spaces` | `space_list_spaces` → 选择知识库 → `space_describe_space` 获取 `root_entry_id` |
| `/spaces/{space_id}` | `space_describe_space` 获取 `root_entry_id` → 作为 `parent_entry_id` |
| `/pages/{entry_id}` | `entry_describe_entry` → folder 类型直接用；page 类型取其 `parent_entry_id` |

---

## 文件上传（三步 + 健康检查 + 降级）

> ⚠️ 必须严格按顺序执行，缺一不可。

### Step 0: 健康检查（whoami）
失败直接进入「上传降级方案」，不执行后续步骤。

### Step 1: 申请上传凭证（MCP）

```
file_apply_upload({
  "parent_entry_id": "<目标目录 entry_id>",
  "name": "example.pdf",
  "size": "12345",
  "mime_type": "application/pdf",
  "upload_type": "PRE_SIGNED_URL"
})
```

**`size` 必填**，通过 `stat -f%z <文件>` 获取字节数。

### Step 2: HTTP PUT 上传（curl，非 MCP）

```bash
curl -X PUT \
  -H "Content-Type: <mime_type>" \
  --data-binary "@<本地文件路径>" \
  "<Step 1 返回的 upload_url>"
```

> 必须用 `--data-binary`（不是 `-d`），保持二进制完整性。

### Step 3: 确认上传（MCP）

```
file_commit_upload({"session_id": "<Step 1 返回的 session_id>"})
```

### 任一步骤失败 → 立即进入「上传降级方案」

---

## ❗ 上传降级方案（强制）

任一步骤失败时立即输出：

```markdown
❌ 上传到乐享失败：[Step N 失败原因 + 错误码]

✅ 原文件保留在原路径：[原始文件路径]
✅ 已复制一份到 fallback 目录便于追溯：
📄 ~/Desktop/lexiang-upload-fallback/{原文件名}-{timestamp}.{ext}
📋 文件大小：[N] KB

恢复连接后三选一：
1. 重新运行上传命令（先跑 whoami 验证健康）
2. 直接拖拽文件到乐享知识库页面手动上传
3. 用 `open ~/Desktop/lexiang-upload-fallback/` 打开目录定位文件

诊断建议：
[Step 1 失败 → 检查 Token 与 parent_entry_id；Step 2 失败 → 检查文件读权限 / 网络；Step 3 失败 → upload_url 过期，重跑 Step 1]
```

### 降级落盘要求（必须真实执行）

```bash
mkdir -p ~/Desktop/lexiang-upload-fallback
cp "<原文件路径>" "~/Desktop/lexiang-upload-fallback/<filename>-<timestamp>.<ext>"
```

---

## 更新已有文件

1. `entry_describe_entry(entry_id)` → 返回 `target_id` 即 `file_id`
2. `file_apply_upload` 时额外传 `file_id`，且 `parent_entry_id` 填**文件自身的 entry_id**
3. 后续同 Step 2 + Step 3

---

## MIME 类型速查

| 类型 | mime_type |
|------|-----------|
| PDF | `application/pdf` |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPT | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| PNG | `image/png` |
| JPG | `image/jpeg` |
| Markdown | `text/markdown` |
| ZIP | `application/zip` |

---

## 常见错误

| 错误 | 修复 |
|------|------|
| apply_upload 失败 | **必须传 `size`（字节数）** |
| curl PUT 返回 403 | upload_url 过期 → 重新 Step 1 |
| 上传 0 字节 | 用了 `-d` → 改 `--data-binary` |
| commit 后文件为空 | 跳过了 Step 2 |
| 更新变成新建 | 没传 `file_id` |
| 任一步骤失败 | **必须执行上传降级方案** |

---

## 辅助脚本

| 脚本 | 说明 |
|------|------|
| `scripts/upload-files.py` | 批量文件上传 |
| `scripts/sync-folder.ts` | 文件夹增量同步 |
