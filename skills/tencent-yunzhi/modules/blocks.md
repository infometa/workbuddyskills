# 页面编辑（Block 操作）

> 已有页面的 Block 级编辑与排版：创建/更新/删除/移动/批量编辑。

---

## 工具概览

- `block_convert_content_to_blocks` — Markdown/HTML 转 Block 结构
- `block_create_block_descendant` — 创建 Block 结构
- `block_update_block` — 单块更新
- `block_update_blocks` — 批量更新
- `block_move_blocks` — 移动 Block
- `block_delete_block_children` — 删除子节点
- `block_delete_block` — 删除指定 Block（含子孙）
- `block_describe_block` — 获取单个 Block 详情
- `block_list_block_children` — 读取 Block 内容

---

## Block 结构核心规则

### 叶子节点（不能有 children）
h1, h2, h3, h4, h5, code, image, divider, mermaid, plantuml

### 容器节点（必须指定 children）
callout, table, table_cell, column_list, column, toggle

> 详细类型定义见 `references/block-schema.md`

---

## 常见操作

### 创建结构化 Block

```
block_create_block_descendant({
  "entry_id": "doc123",
  "descendant": [
    {"block_id": "h1", "block_type": "h1", "heading1": {"elements": [{"text_run": {"content": "标题"}}]}},
    {"block_id": "tip", "block_type": "callout", "callout": {"color": "#FFF3E0"}, "children": ["tip_p"]},
    {"block_id": "tip_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "提示内容"}}]}}
  ],
  "children": ["h1", "tip"]
})
```

### 读取 Block 内容

```
block_list_block_children(entry_id="abc123", with_descendants=true)
```

### 批量更新

```
block_update_blocks({
  "entry_id": "abc123",
  "updates": {
    "block_id": {
      "update_text_elements": {
        "elements": [{"text_run": {"content": "更新后的内容"}}]
      }
    }
  }
})
```

---

## 注意事项

1. `block_id` 为客户端临时 ID，服务端返回实际 ID 映射
2. 叶子节点不支持 children 字段
3. 容器节点必须指定 children

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/block-schema.md` | Block 类型完整说明 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/block-update.md` | 批量更新方法 |
| `references/content-reorganize.md` | 文档结构重组 |

## 辅助资源

| 资源 | 说明 |
|------|------|
| `assets/lexiang-block-schema.json` | Block Schema JSON |
| `assets/examples/` | Block 结构示例 |
| `assets/themes/` | 主题配置 |
