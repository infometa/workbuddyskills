# 文档写入

> 创建新文档/页面/文件夹、Markdown/HTML 导入、外部链接导入。**写入失败必须落本地降级**。

---

## 工具概览

- `entry_create_entry` — 创建文档/文件夹
- `entry_import_content` — 导入 Markdown/HTML 创建新文档（⚠️ 仅新建）
- `entry_import_content_to_entry` — 导入内容到已有页面（覆盖/追加）
- `entry_rename_entry` — 重命名条目
- `file_create_hyperlink` — 导入公众号文章等外部链接

---

## 通用写入流程（含强制降级）

```
Step 0: 健康检查（whoami）
  ├─ ✅ 通过 → Step 1
  └─ ❌ 失败 → 直接进入「降级方案」，不执行 Step 1~2

Step 1: 解析用户目标（space_id + parent_entry_id）
  ├─ ✅ 解析成功 → Step 2
  └─ ❌ URL 无效 / 无权限 → 反问用户提供有效链接，**不进降级**（属于输入问题）

Step 2: 调用 entry_import_content
  ├─ ✅ 成功 → 返回 {domain}/pages/{entry_id}
  ├─ ❌ 401/403 → 健康检查已失效，进入「降级方案」并终止重试
  ├─ ❌ 5xx / 超时 → 重试 1 次，仍失败进入「降级方案」
  └─ ❌ 其他错误 → 输出错误 + 进入「降级方案」
```

---

## ❗ 写入降级方案（强制提供，不要等用户问）

写入失败时**立即**执行下面所有动作，不要在末尾用 ⚠️ 一句话带过：

```markdown
❌ 写入乐享知识库失败：[具体错误码 + 简短解释]

✅ 已为你保存到本地，避免内容丢失：
📄 文件路径：~/Desktop/lexiang-fallback/{name}-{timestamp}.md
📋 字数：[N] 字
📋 首段预览：[首 200 字]

恢复连接后可三选一重试：
1. 重新运行原命令（建议先跑 whoami 验证健康）
2. 直接拖拽该 .md 文件到乐享知识库页面手动导入
3. 复制内容到剪贴板：`cat <文件> | pbcopy`，到乐享页面粘贴

诊断建议：
[根据错误类型给出动作，例如 401 → 续期 Token；5xx → 稍后重试；连接异常 → 检查 Trust 状态]
```

### 降级文件落盘要求（必须真实执行）

```python
# 伪代码：失败时必须真的写文件，不要只口头承诺
import os, datetime
fallback_dir = os.path.expanduser("~/Desktop/lexiang-fallback")
os.makedirs(fallback_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
safe_name = name.replace("/", "_")[:60]
path = f"{fallback_dir}/{safe_name}-{timestamp}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
```

> 用户偏好：默认落 Desktop。如果用户在 workspace 中明确要求落 `.workbuddy/` 等其他位置，按用户指定。

---

## 常见操作流程

### 从知识库链接写入文档

```
Step 0: 健康检查
Step 1: 从 URL 提取 space_id
Step 2: space_describe_space(space_id) → 获取 root_entry_id
Step 3: entry_import_content(space_id, parent_id=root_entry_id, name, content, content_type="markdown")
Step 4: 成功 → 返回 {domain}/pages/{entry_id}；失败 → 走降级方案
```

> `space_id` 和 `parent_id` 要同时传；`parent_id` 用 `root_entry_id` 表示写入根目录。

### 创建文档（仅占位文档）

```
entry_create_entry(name="技术文档", parent_entry_id="abc123", entry_type="page")
```

### 导入 Markdown

```
entry_import_content(parent_id="folder123", name="技术文档", content="...", content_type="markdown")
```

### 微信公众号导入

用户提供 `mp.weixin.qq.com` 链接且意图是 "导入/收藏/保存到乐享" 时：

```
file_create_hyperlink(url="...", space_id="...", parent_entry_id="...")
```

> 如果用户只想阅读/总结内容，**不要默认导入**。

---

## 注意事项

1. `entry_import_content` 的 `parent_id` 通常用 `root_entry_id`
2. 支持的 `content_type`：`markdown`、`html`
3. 上传 PDF/Word/图片等二进制文件 → 走 `modules/files.md`
4. 任意失败必须执行降级方案，不允许沉默或仅口头报错
