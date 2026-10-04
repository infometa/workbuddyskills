# 乐享评论

> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `references/setup.md`。
> **触发场景**：用户想查看某个知识页面的评论、讨论内容时使用。当前仅支持读取评论，不支持通过 MCP 发布评论。

---

## 工具概览

| 工具 | 说明 |
|------|------|
| `comment_list_comments` | 获取知识条目的评论列表 |
| `comment_describe_comment` | 获取评论详情（含评论内容） |

---

## 使用流程

### 查看页面评论

```
Step 1: 获取 entry_id
  - 从用户提供的页面链接中提取：{domain}/pages/{entry_id}
  - 或通过 search_kb_search 搜索后获取

Step 2: comment_list_comments(
  target_type="kb_entry",
  target_id=<entry_id>
)
→ 返回评论列表（评论 ID、作者、时间等元信息）

Step 3（可选，获取评论正文）: comment_describe_comment(
  target_type="kb_entry",
  target_id=<entry_id>
)
→ 返回评论详情，含content 字段
```

---

## ⚠️ 注意事项

1. **`content` 字段格式特殊**：评论的 `content` 不是普通 HTML，需要特别注意解析，不能直接当普通文本展示
2. **`target_type` 固定值**：当前只支持 `"kb_entry"`（页面评论）
3. **只读能力**：当前 MCP 只支持读取评论，无法通过 MCP 发布新评论或回复
4. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准
