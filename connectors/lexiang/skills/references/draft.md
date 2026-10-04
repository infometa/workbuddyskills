# 乐享Markdown 草稿

> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `references/setup.md`。
> **触发场景**：用户需要先保存草稿再发布，或查看/管理某个页面的未发布草稿时使用。

---

## 工具概览

| 工具 | 说明 |
|------|------|
| `draft_save_markdown_draft` | 保存草稿（创建或更新） |
| `draft_describe_markdown_draft` | 获取草稿内容和版本信息 |
| `draft_publish_markdown_draft` | 发布草稿为正式版本 |
| `draft_delete_markdown_draft` | 删除草稿，放弃未发布的修改 |

---

## 标准草稿工作流

### 新建草稿并发布

```
Step 1: 获取当前版本 revision_id
  entry_describe_entry(entry_id=<entry_id>)
  → 取返回值中的 revision_id

Step 2: 保存草稿
  draft_save_markdown_draft(
    entry_id=<entry_id>,
    revision_id=<revision_id>,
    content=<markdown内容>,
    seq=0← 首次创建传0
  )
  → 返回草稿信息，包含 seq

Step 3: 查看草稿（可选确认）
  draft_describe_markdown_draft(entry_id=<entry_id>)
  → 返回草稿内容，空表示无草稿

Step 4: 发布
  draft_publish_markdown_draft(
    entry_id=<entry_id>,
    revision_id=<revision_id>,
    content=<可选，传入则覆盖草稿内容>
  )
```

### 更新已有草稿

```
Step 1: 查看当前草稿
  draft_describe_markdown_draft(entry_id=<entry_id>)
  → 取返回值中的 seq

Step 2: 更新草稿
  draft_save_markdown_draft(
    entry_id=<entry_id>,
    revision_id=<revision_id>,
    content=<新内容>,
    seq=<当前seq>← 乐观锁校验，防止并发冲突
  )
```

### 放弃草稿

```
draft_delete_markdown_draft(entry_id=<entry_id>)
→ 删除未发布草稿，页面内容恢复到上次发布状态
```

---

## ⚠️ 注意事项

1. **`seq` 参数是乐观锁**：首次创建传 `0`，更新时必须传当前草稿的 `seq` 值，防止并发冲突
2. **草稿与正式版本独立**：草稿不影响页面当前的正式内容，发布后才生效
3. **`draft_describe_markdown_draft` 返回空**：表示该页面当前没有未发布的草稿，属于正常状态
4. **`draft_publish_markdown_draft` 的 `content` 参数**：可选传入，用于在发布时覆盖草稿内容；不传则直接发布当前草稿
5. **`force_publish=true`**：跳过版本冲突检测，强制发布，谨慎使用
6.参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准
