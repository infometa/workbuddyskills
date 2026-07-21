# 场景：内容重组

使用 MoveBlocks 调整文档结构，将块移动到新位置。

## 移动块 API

```
MCP Tool: 云知.block_move_blocks
Arguments: {
  "entry_id": "<entry_id>",
  "block_ids": ["block_1", "block_2", "block_3"],
  "parent_block_id": "<目标父块 ID>",
  "after": "<插入位置，某块之后，可选>"
}
```

**限制**: 单次最多移动 20 个块

---

## 参数说明

| 参数 | 说明 |
|------|------|
| `entry_id` | 文档 entry_id |
| `block_ids` | 要移动的块 ID 数组，按顺序移动 |
| `parent_block_id` | 目标父节点块 ID |
| `after` | 插入到此块之后，为空则插入到开头 |

---

## 使用场景

### 将分散内容整合到同一章节

```
MCP Tool: 云知.block_move_blocks
Arguments: {
  "entry_id": "doc123",
  "block_ids": ["para_1", "para_2", "list_1"],
  "parent_block_id": "section_h2",
  "after": "intro_callout"
}
```

### 调整段落顺序

```
MCP Tool: 云知.block_move_blocks
Arguments: {
  "entry_id": "doc123",
  "block_ids": ["para_3"],
  "parent_block_id": "root_block",
  "after": "para_1"
}
```

---

## 使用辅助工具

```typescript
import { ContentReorganizer } from './scripts/block-helper';

const reorganizer = new ContentReorganizer()
  .move(['para_1', 'para_2'], 'section_h2', 'intro_callout')
  .move(['list_1', 'list_2'], 'section_h2');

const mcpCalls = reorganizer.toMCPCalls(entryId);
// 返回多个 MCP 调用
```

---

## 注意事项

1. **所有块只能移动到同一个目标父节点**
2. **目标父节点不能是叶子节点类型**，包括：
   - h1, h2, h3, h4, h5（标题块）
   - code（代码块）
   - image（图片块）
   - attachment（附件块）
   - video（视频块）
   - divider（分割线）
   - mermaid、plantuml（图表块）
3. 移动操作会保持块的子孙结构
4. 建议移动前先获取文档结构确认 block_id

---

## 获取文档结构

```
MCP Tool: 云知.block_list_block_children
Arguments: {
  "entry_id": "<entry_id>",
  "with_descendants": true
}
```

返回完整的块树结构，包含所有 block_id。
